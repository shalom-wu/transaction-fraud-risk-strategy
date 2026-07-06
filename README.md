# Transaction Fraud Detection & Risk Strategy

This repository builds a fraud scoring workflow on the public Kaggle/ULB credit card fraud dataset. The focus is threshold selection: fraud captured, false positives, review volume, customer friction, and expected cost.

**Dataset:** public [Credit Card Fraud Detection](https://www.kaggle.com/datasets/mlg-ulb/creditcardfraud) dataset from the Machine Learning Group at Universite Libre de Bruxelles. Features `V1` through `V28` are PCA-anonymized, so the project does not make merchant-, device-, or geography-level driver claims.

## Key findings- **Fraud is only 0.173% of transactions**: 492 frauds out of 284,807 rows.
  There are no missing cells; the file contains 1,081 exact duplicate rows,
  which are documented rather than silently dropped because repeated
  transaction-looking records can be business-real in payments data.
- **Fraud amount risk is tail-heavy**: fraud transactions total $60.1K in the
  sample. Fraud has a higher mean amount than legitimate transactions
  ($122.21 vs. $88.29), but a lower median ($9.25 vs. $22.00), so a simple
  "large amount equals fraud" rule is not enough.
- **Best holdout model:** tree model with random oversampling fallback,
  PR-AUC **0.845** and ROC-AUC **0.975**. The class-weighted logistic baseline
  is useful for comparison (PR-AUC 0.704), but the tree model gives a better
  precision/recall operating surface on this run.
- **Recommended cost-balanced threshold:** score cutoff **0.25**, flagging
  **0.19%** of transactions with **78.4% precision** and **85.4% recall**.
  Under the default assumptions, this improves economics by **$14.5K per
  100,000 scored transactions** versus the no-model current-state benchmark.
- **Deployment should be tiered**: aggressive review catches slightly more
  fraud (87.8% recall) but precision falls to 30.4%; conservative flagging
  keeps precision at 100.0% in the holdout but catches only 29.3% of fraud.
  The practical recommendation is high-risk auto-decline, middle-risk review
  or step-up authentication, and low-risk allow/monitor.

Read these generated artifacts first:

- `reports/summary.md` for the one-page business readout
- `reports/strategy_deck.md` for the 7-slide strategy deck
- `outputs/model_card.md` for model metrics, threshold scenarios, and cost assumptions

![Threshold tradeoff](reports/figures/threshold_tradeoff.png)

## Operating decision

Fraud projects often stop after a classification metric. That misses the
actual operating decision. Under severe imbalance, a model can look good on
accuracy while failing the business, and an aggressive threshold can catch more
fraud while creating too many false positives. This repo makes the tradeoff
explicit by scoring thresholds with:

- missed-fraud loss
- chargeback/admin fees
- manual review cost
- false-positive customer friction
- normalized net savings per 100,000 scored transactions

## Repository structure

```text
data-sources.md                 # dataset attribution, caveats, setup
notebooks/fraud_risk_analysis.ipynb
outputs/                        # generated tables, metrics, and notes
reports/
  figures/                      # generated presentation-ready charts
  strategy_deck.md              # markdown strategy deck
  summary.md                    # one-page business summary
scripts/
  download_data.py              # extract Kaggle archive.zip
  run_eda.py                    # class balance, amount/time analysis, charts
  run_modeling.py               # models, PR-AUC, thresholds, cost table
  build_deck.py                 # generated strategy deck and summary
  make_notebook.py              # notebook companion
src/fraud_risk/                 # reusable data, model, cost, viz code
tests/                          # unit tests for data and cost behavior
```

## Methodology

1. **Clean and profile the data.** Validate the expected Kaggle schema,
   document missingness, duplicate rows, class imbalance, transaction amount
   distributions, and relative elapsed-hour patterns.
2. **Frame the economics.** Direct fraud loss is only one side of the problem.
   The cost model also includes review operations and false-positive friction.
3. **Model for imbalance.** Train a class-weighted logistic regression baseline
   and a tree-based model using SMOTE when available, with a conservative
   random-oversampling fallback. The local run used the fallback because
   `imbalanced-learn` was not installed in the available package folder.
4. **Evaluate the right metrics.** Use PR-AUC, precision, recall, and threshold
   tables. ROC-AUC is reported only as supporting context because it can look
   strong even when precision is operationally weak.
5. **Choose deployment policy.** Compare aggressive review, cost-balanced, and
   conservative flagging scenarios, then recommend a tiered risk-scoring
   approach.

## Reproducing the analysis

Requires Python 3.11+.

```bash
git clone https://github.com/shalom-wu/transaction-fraud-risk-strategy.git
cd transaction-fraud-risk-strategy
python -m venv .venv
.venv\Scripts\activate      # Windows
pip install -r requirements.txt
pip install -e .

python scripts/run_all.py
python scripts/run_sql.py
pytest
```

On macOS/Linux, activate with `source .venv/bin/activate`.

The full raw file and a smaller stratified sample are included in `data/`.
`scripts/download_data.py` remains available only if you want to rebuild from a
fresh Kaggle archive.

## SQL and Power BI layer

The [sql/](sql) folder is the reproducible validation and KPI layer. It checks
the included transaction data, computes class balance, amount-band risk,
fraud-by-hour cuts, threshold economics, and scenario comparisons.

```bash
python scripts/run_sql.py
```

The runner uses the full raw file when present and exports dashboard-ready data
to `data/powerbi/`: class balance, amount by class, fraud by hour, amount-band
risk, threshold cost table, model metrics, precision-recall curve, deployment
scenarios, and cost assumptions. The [power-bi/](power-bi) folder contains a
dashboard brief, data model, DAX, refresh steps, manual build instructions, and
mockups. No `.pbix` is included yet; I did not create a placeholder.

## Limitations

- **Interpretability is limited.** PCA-anonymized `V1`-`V28` features prevent
  business-readable feature explanations like merchant category, device risk,
  customer tenure, or geography.
- **The dataset is a public benchmark.** This is useful for a portfolio project,
  but a production fraud system needs fresher data, customer/merchant features,
  and time-based validation against fraud drift.
- **Costs are assumptions.** The default values are transparent and editable,
  but a real card issuer should replace them with actual chargeback recovery,
  review capacity, interchange/revenue impact, and false-decline churn.
- **`Time` is relative.** The project derives elapsed-hour patterns, not true
  time-of-day behavior.

## Author

Shalom Wu

MIT License.
