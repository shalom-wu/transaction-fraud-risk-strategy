# Manual Build Instructions

1. Run `python scripts/run_sql.py`.
2. Open Power BI Desktop.
3. Load all CSV files from `data/powerbi/`.
4. Create the measures in `dax_measures.md`.
5. Build three pages:
   - Executive KPI: transactions, fraud rate, PR-AUC, recommended threshold, net savings per 100K.
   - Diagnostic Analysis: fraud by hour, amount-band risk, amount by class, precision-recall curve.
   - Decision Support: threshold ranking table and scenario comparison.
6. Add footer text: `Source: Kaggle/ULB credit-card fraud benchmark; features are PCA-anonymized; cost outputs use documented assumptions.`
7. Save as `power-bi/fraud_risk_strategy.pbix`.

The screenshots are mockups generated from the included data.
