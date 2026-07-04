# Explain It To Me: Fraud Detection and Risk Strategy

## 1. Plain-English walkthrough

Fraud detection sounds like it should be simple: catch the bad transactions and
let the good ones through. The catch is that the bad transactions are extremely
rare. In this dataset, fewer than 2 out of every 1,000 transactions are fraud.

That means a model can be "accurate" by saying everything is legitimate. It
would be useless, but it would still be more than 99% accurate. So the real
question is not accuracy. The real question is: **which transactions should we
interrupt, and how much business cost are we willing to create to stop fraud?**

This project builds three things:

1. A data analysis showing the imbalance, amount patterns, and relative time
   patterns in the transaction data.
2. A fraud model that gives each transaction a risk score.
3. A cost model that converts different score thresholds into business tradeoffs.

The key idea is that false positives matter. If a card issuer wrongly blocks a
real customer, the issuer may pay manual review costs, frustrate the customer,
lose trust, or even lose future spend. So "catch more fraud" is not always the
best answer. The best answer is a risk policy that uses the model carefully.

## 2. Explanation versions

### 30-second version

I built a fraud detection project using the public Kaggle/ULB credit card fraud
dataset. Because fraud is only about 0.17% of transactions, accuracy is
misleading. I evaluate precision, recall, PR-AUC, and then connect thresholds to
a cost model that includes both missed fraud and false-positive customer
friction. The recommended strategy is tiered risk scoring, not a single blunt
block rule.

### 2-minute version

The dataset contains anonymized European card transactions. Almost all rows are
legitimate and only a tiny fraction are fraud. That severe imbalance changes
both the modeling and the business framing.

First, I profile the data: class balance, amount distribution, and relative
hour patterns. Then I train a class-weighted logistic regression baseline and a
tree-based model with resampling for the rare fraud class. I evaluate using
PR-AUC, precision, and recall because those metrics directly show the tradeoff:
when recall goes up, the model catches more fraud, but precision may fall and
create more false positives.

Finally, I score different thresholds with a cost model. The model includes
missed fraud loss, chargeback/admin fees, review cost, and false-positive
friction. That lets me recommend a deployment approach: auto-decline only the
highest-risk band, send the middle band to review or step-up authentication,
and allow low-risk transactions while monitoring drift.

### 5-minute version

This project is designed like a risk strategy memo rather than a model demo.
The data comes from the well-known Kaggle/ULB credit card fraud dataset. It has
`Time`, `Amount`, and 28 anonymized PCA features named `V1` through `V28`, plus
the fraud label.

The first important finding is imbalance. Fraud is rare enough that a naive
model can get a high accuracy score by doing nothing useful. So I avoid making
accuracy the headline. Instead, I use PR-AUC, precision, and recall.

Precision answers: "Of the transactions I flagged, how many were actually
fraud?" Recall answers: "Of all real frauds, how many did I catch?" They move
against each other when the threshold changes. A lower threshold catches more
fraud but flags more good customers. A higher threshold bothers fewer customers
but lets more fraud through.

The cost model is the bridge from machine learning to business strategy. It
estimates the cost of missed fraud and the cost of false positives. That is the
piece many beginner projects skip. The final deck compares threshold scenarios
and recommends tiered deployment instead of a one-size-fits-all threshold.

## 3. How the code actually works

### What each file and folder does

- `data-sources.md`: documents the dataset source, setup, and limitations.
- `src/fraud_risk/data.py`: loads the CSV, validates columns, and derives
  fields like relative hour and log amount.
- `src/fraud_risk/costs.py`: calculates missed fraud cost, false-positive cost,
  threshold cost, and deployment scenarios.
- `src/fraud_risk/modeling.py`: trains the logistic baseline and tree model,
  handles class imbalance, and produces PR-AUC/precision/recall metrics.
- `src/fraud_risk/viz.py`: creates the charts used in the reports and deck.
- `scripts/run_eda.py`: runs the descriptive analysis and saves figures.
- `scripts/run_modeling.py`: trains models and creates threshold-cost outputs.
- `scripts/build_deck.py`: turns the saved outputs into `reports/strategy_deck.md`.
- `notebooks/fraud_risk_analysis.ipynb`: a readable walkthrough of the generated outputs.
- `tests/`: checks data validation and the cost model logic.

Read order:

1. `README.md`
2. `data-sources.md`
3. `src/fraud_risk/costs.py`
4. `src/fraud_risk/modeling.py`
5. `scripts/run_modeling.py`
6. `reports/strategy_deck.md`

### Key functions in plain terms

- `clean_transactions`: checks that the dataset has the expected columns, then
  adds helper columns like `relative_hour` and `amount_log1p`.
- `random_oversample_minority`: copies fraud rows in the training set so the
  tree model has more rare examples to learn from.
- `smote_or_random_resample`: uses SMOTE if the library is installed; otherwise
  uses random oversampling.
- `threshold_cost_table`: tries many thresholds and calculates precision,
  recall, false positives, missed fraud, total cost, and net savings.
- `choose_deployment_scenarios`: picks aggressive, cost-balanced, and
  conservative threshold scenarios from the threshold table.

### How imbalance handling works conceptually

The training data has very few fraud examples. Logistic regression handles this
with `class_weight="balanced"`, which makes fraud mistakes matter more during
training. The tree model uses resampling: it increases the number of fraud
examples in the training data so the model has more chances to learn fraud-like
patterns.

The code does not oversample the test set. That matters. The test set keeps the
real imbalance so evaluation still reflects the real operating problem.

### How to run the project end to end

```bash
python scripts/download_data.py --archive path/to/archive.zip
python scripts/run_eda.py
python scripts/run_modeling.py
python scripts/build_deck.py
python scripts/make_notebook.py
pytest
```

### What I would point to first in a technical interview

I would start with `src/fraud_risk/costs.py`, because it shows the project is
not only a model exercise. Then I would show `scripts/run_modeling.py`, because
it ties together the train/test split, PR-AUC model selection, threshold table,
cost model, and deployment scenarios.

## 4. Anticipated questions and spoken-language answers

### Why precision and recall instead of accuracy?

Because fraud is extremely rare. If the model called every transaction
legitimate, it would be more than 99% accurate and still catch zero fraud.
Precision and recall show the actual operating tradeoff.

### Why does false-positive cost matter as much as fraud loss?

A false positive means a real customer gets interrupted. That can mean review
cost, failed purchase, support contact, frustration, or churn. If a threshold
stops a little more fraud but creates a lot more customer friction, it may be a
bad business decision.

### What would you do with non-anonymized features?

I would build more interpretable features around merchant category, cardholder
history, device, geography, velocity, transaction channel, and customer tenure.
Then I would explain risk patterns in business language instead of pointing at
anonymous PCA columns.

### How confident are you in the dollar numbers?

Confident in the calculation logic, but the default assumptions need business
calibration. The model can show the tradeoff structure; a real issuer should
replace the default costs with its own chargeback recovery, review cost,
false-decline impact, and current controls.

### Biggest limitation?

The anonymized features. They make the dataset safe to publish, but they limit
interpretability and prevent strong explanations about why fraud happens.

### Walk me through the threshold cost function.

For each threshold, the function marks transactions above the threshold as
alerts. It counts true positives, false positives, and false negatives. Then it
adds missed fraud cost, false-positive friction cost, and review cost. Finally,
it compares that total with the current-state baseline.

## Glossary

- **Accuracy:** Share of all predictions that are correct. Misleading here
  because fraud is rare.
- **Class imbalance:** One class is much more common than the other. Here,
  legitimate transactions massively outnumber fraud.
- **False positive:** A legitimate transaction incorrectly flagged as fraud.
- **False negative:** A fraud transaction that the model misses.
- **Precision:** Of the transactions flagged as fraud, the share that are
  actually fraud.
- **Recall:** Of all actual fraud transactions, the share the model catches.
- **PR-AUC:** Area under the precision-recall curve. Useful when the positive
  class is rare.
- **ROC-AUC:** Area under the receiver operating characteristic curve. Useful
  for ranking, but it can look overly optimistic when fraud is extremely rare.
- **SMOTE:** A technique that creates synthetic minority-class examples during
  training.
- **Threshold:** The score cutoff where the model changes from "allow" to
  "flag."
- **Tiered risk scoring:** A deployment policy with different actions for low,
  medium, and high risk rather than one simple cutoff.

