-- ============================================================================
-- kpi_views.sql — fraud exposure KPIs + rankings over the model's
-- decision tables. The classifier itself lives in Python (src/fraud_risk);
-- SQL owns the counting, the exposure cuts, and the ranking of the
-- already-computed threshold economics.
-- ============================================================================

CREATE OR REPLACE VIEW v_class_balance AS
SELECT (SELECT data_basis FROM meta)              AS data_basis,
       COUNT(*)                                   AS transactions,
       SUM(Class)                                 AS fraud_transactions,
       ROUND(AVG(Class), 6)                       AS fraud_rate,
       ROUND(SUM(Amount), 2)                      AS total_amount,
       ROUND(SUM(Amount * Class), 2)              AS fraud_amount
FROM transactions;

CREATE OR REPLACE VIEW v_amount_by_class AS
SELECT CASE Class WHEN 1 THEN 'Fraud' ELSE 'Legitimate' END AS class,
       COUNT(*)                       AS transactions,
       ROUND(AVG(Amount), 2)          AS mean_amount,
       ROUND(MEDIAN(Amount), 2)       AS median_amount,
       ROUND(MAX(Amount), 2)          AS max_amount,
       ROUND(SUM(Amount), 2)          AS total_amount
FROM transactions GROUP BY Class;

-- fraud concentration by hour of day (Time = seconds since first txn;
-- the capture window is two days, so hour-of-day folds both days together)
CREATE OR REPLACE VIEW v_fraud_by_hour AS
SELECT CAST(FLOOR(Time / 3600) AS INTEGER) % 24   AS hour_of_day,
       COUNT(*)                                   AS transactions,
       SUM(Class)                                 AS fraud_transactions,
       ROUND(AVG(Class), 6)                       AS fraud_rate,
       ROUND(SUM(Amount * Class), 2)              AS fraud_amount
FROM transactions
GROUP BY 1;

-- does "big transaction" mean "fraud"? (the README's tail-heavy point)
CREATE OR REPLACE VIEW v_amount_band_risk AS
SELECT CASE
           WHEN Amount = 0 THEN 'a. $0'
           WHEN Amount < 10 THEN 'b. $0-10'
           WHEN Amount < 50 THEN 'c. $10-50'
           WHEN Amount < 100 THEN 'd. $50-100'
           WHEN Amount < 500 THEN 'e. $100-500'
           ELSE 'f. $500+'
       END                                        AS amount_band,
       COUNT(*)                                   AS transactions,
       SUM(Class)                                 AS fraud_transactions,
       ROUND(AVG(Class), 6)                       AS fraud_rate,
       ROUND(SUM(Amount * Class), 2)              AS fraud_amount
FROM transactions
GROUP BY 1;

-- ----------------------------------------------------------------------------
-- Rankings over the Python model's committed outputs
-- ----------------------------------------------------------------------------
CREATE OR REPLACE VIEW v_threshold_ranking AS
SELECT threshold, alerts, alert_rate, precision, recall,
       false_positive_rate, model_assisted_cost, net_savings,
       net_savings_per_100k,
       RANK() OVER (ORDER BY net_savings DESC) AS savings_rank
FROM threshold_costs;

CREATE OR REPLACE VIEW v_scenario_comparison AS
SELECT scenario, threshold, alerts, precision, recall,
       false_positive_rate, net_savings_per_100k, use_case
FROM deployment_scenarios
ORDER BY net_savings_per_100k DESC;

-- claim check: recompute the README's headline numbers (meaningful on the
-- full file; the sample's fraud share is inflated by construction)
CREATE OR REPLACE VIEW v_validation_headlines AS
SELECT 'data basis' AS claim, (SELECT data_basis FROM meta) AS sql_value
UNION ALL
SELECT 'fraud share (README: 0.173% on full file)',
       ROUND(100 * AVG(Class), 4)::VARCHAR || '%' FROM transactions
UNION ALL
SELECT 'fraud transactions (README: 492 on full file)',
       SUM(Class)::VARCHAR FROM transactions
UNION ALL
SELECT 'fraud amount total (README: $60.1K on full file)',
       ROUND(SUM(Amount * Class), 0)::VARCHAR FROM transactions
UNION ALL
SELECT 'fraud mean vs legit mean (README: $122.21 vs $88.29)',
       ROUND(AVG(Amount) FILTER (WHERE Class = 1), 2)::VARCHAR || ' vs ' ||
       ROUND(AVG(Amount) FILTER (WHERE Class = 0), 2)::VARCHAR FROM transactions
UNION ALL
SELECT 'fraud median vs legit median (README: $9.25 vs $22.00)',
       ROUND(MEDIAN(Amount) FILTER (WHERE Class = 1), 2)::VARCHAR || ' vs ' ||
       ROUND(MEDIAN(Amount) FILTER (WHERE Class = 0), 2)::VARCHAR FROM transactions
UNION ALL
SELECT 'best PR-AUC (README: 0.845)',
       ROUND(MAX(average_precision_pr_auc), 3)::VARCHAR FROM model_metrics;
