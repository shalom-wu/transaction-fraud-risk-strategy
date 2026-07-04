# Model Card and Threshold Cost Notes

## Model choice

The selected model is **Tree model with Random oversampling fallback**, chosen by holdout PR-AUC. ROC-AUC
is reported for completeness, but PR-AUC, precision, recall, and threshold
cost are more relevant under a fraud base rate below 1%.

| model | average_precision_pr_auc | roc_auc | precision_at_0_50 | recall_at_0_50 | f1_at_0_50 | alert_rate_at_0_50 |
| --- | --- | --- | --- | --- | --- | --- |
| Tree model with Random oversampling fallback | 0.845 | 0.975 | 0.862 | 0.813 | 0.837 | 0.002 |
| Class-weighted logistic regression | 0.704 | 0.973 | 0.062 | 0.886 | 0.117 | 0.024 |

## Recommended operating point under default assumptions

The cost-balanced threshold flags **0.19%**
of transactions, reaches **85.4% recall**
and **78.4% precision**, and improves
cost by **$14,543 per
100,000 scored transactions** against the current-state assumption.

## Deployment scenarios

| scenario | use_case | threshold | alert_rate | precision | recall | false_positive_rate | alerts | net_savings_per_100k | model_cost_per_100k | baseline_cost_per_100k |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Aggressive review | Maximize fraud capture when review capacity and customer messaging can absorb more alerts. | 0.050 | 0.005 | 0.304 | 0.878 | 0.003 | 355.0 | $10,298 | $10,930 | $21,227 |
| Cost-balanced default | Use as the recommended operating point under the default cost assumptions. | 0.250 | 0.002 | 0.784 | 0.854 | 0.000 | 134.0 | $14,543 | $6,684 | $21,227 |
| Conservative flagging | Prioritize customer experience by flagging fewer legitimate transactions. | 0.987 | 0.001 | 1.000 | 0.293 | 0.000 | 36.0 | $4,557 | $16,670 | $21,227 |

## Cost assumptions

- Missed fraud loss: transaction amount x 1.00
- Chargeback/admin fee on missed fraud: $15.00 per fraud
- Manual review operations cost: $3.00 per alert
- False-positive fixed friction cost: $5.00 per legitimate alert
- False-positive amount-linked friction: 2.50% of legitimate transaction amount
- Current-state detection rate assumption: 0.0%

These are portfolio-planning assumptions, not issuer-specific economics. A real
deployment should replace them with chargeback recovery, review capacity,
interchange/revenue impact, false-decline churn impact, and current rule-stack
detection rates.
