# DAX Measures

```DAX
Transactions = SUM(kpi_class_balance[transactions])

Fraud Transactions = SUM(kpi_class_balance[fraud_transactions])

Fraud Rate = DIVIDE([Fraud Transactions], [Transactions])

Best Net Savings per 100K =
MAX(threshold_cost_table[net_savings_per_100k])

Recommended Alerts =
CALCULATE(
    MAX(threshold_cost_table[alerts]),
    TOPN(1, threshold_cost_table, threshold_cost_table[net_savings_per_100k], DESC)
)

Average Precision PR AUC =
MAX(model_metrics[average_precision_pr_auc])
```

Use percentage formatting for fraud rate, precision, recall, alert rate, and false-positive rate. Cost values are estimated from documented assumptions.
