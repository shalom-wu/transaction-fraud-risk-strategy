# Data Manifest

This repo includes the full Kaggle/ULB transaction file, a smaller stratified sample, SQL outputs, model outputs, and Power BI-ready tables.

| File | Type | Shape / size | Used by | Notes |
|---|---|---:|---|---|
| `raw/creditcard.csv` | Real public benchmark data | 284,807 x 31, 143.8 MB | Python, SQL, tests | Kaggle metadata checked 2026-07-06; license `DbCL-1.0`; source is ULB/Machine Learning Group via Kaggle. |
| `sample/creditcard_sample.csv` | Real sample/extract | 20,492 x 31, 10.4 MB | Fast review, fallback SQL | Stratified sample: all fraud rows plus a legitimate sample. |
| `powerbi/kpi_class_balance.csv` | Derived aggregate | 1 x 6, <1 KB | Power BI | Data basis, transaction count, fraud count/rate, total and fraud amount. |
| `powerbi/kpi_amount_by_class.csv` | Derived aggregate | 2 x 6, <1 KB | Power BI | Amount distribution by fraud label. |
| `powerbi/kpi_fraud_by_hour.csv` | Derived aggregate | 24 x 5, <1 KB | Power BI | Fraud rate by elapsed-hour bucket. |
| `powerbi/kpi_amount_band_risk.csv` | Derived aggregate | 6 x 5, <1 KB | Power BI | Fraud rate and fraud amount by transaction amount band. |
| `powerbi/threshold_cost_table.csv` | Derived + assumed | 17 x 20, 4.7 KB | Power BI | Threshold economics from the Python cost model. |
| `powerbi/scenario_comparison.csv` | Derived + assumed | 3 x 8, <1 KB | Power BI | Cost-balanced, aggressive, and conservative operating points. |
| `powerbi/deployment_scenarios.csv` | Derived + assumed | 3 x 11, <1 KB | Power BI | Recommended review scenarios. |
| `powerbi/model_metrics.csv` | Derived model output | 2 x 7, <1 KB | Power BI | PR-AUC, ROC-AUC, and threshold metrics. |
| `powerbi/precision_recall_curve.csv` | Derived model output | 4,218 x 3, 248.4 KB | Power BI | Precision-recall curve points. |
| `powerbi/cost_assumptions.csv` | Assumed | 1 x 6, <1 KB | Power BI | Fraud loss, review cost, and false-positive cost assumptions. |

`V1`-`V28` are PCA-anonymized features. The project can discuss risk ranking and operating thresholds, but it should not claim merchant-, device-, geography-, or customer-level driver insight.
