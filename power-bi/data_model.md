# Data Model

Load these files from `data/powerbi/`:

| Table | File | Grain |
|---|---|---|
| `kpi_class_balance` | `kpi_class_balance.csv` | One-row dataset summary. |
| `kpi_amount_by_class` | `kpi_amount_by_class.csv` | One row per class. |
| `kpi_fraud_by_hour` | `kpi_fraud_by_hour.csv` | One row per elapsed-hour bucket. |
| `kpi_amount_band_risk` | `kpi_amount_band_risk.csv` | One row per amount band. |
| `threshold_cost_table` | `threshold_cost_table.csv` | One row per evaluated threshold. |
| `scenario_comparison` | `scenario_comparison.csv` | One row per operating scenario. |
| `deployment_scenarios` | `deployment_scenarios.csv` | One row per recommended deployment scenario. |
| `model_metrics` | `model_metrics.csv` | One row per model. |
| `precision_recall_curve` | `precision_recall_curve.csv` | One row per curve point. |
| `cost_assumptions` | `cost_assumptions.csv` | One-row assumption table. |

Relationships are optional. Most pages can use the pre-aggregated tables directly. Keep assumption tables visibly separate from observed data.
