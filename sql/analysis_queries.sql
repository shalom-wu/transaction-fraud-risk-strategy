-- ============================================================================
-- analysis_queries.sql — the questions a fraud-strategy team would ask.
-- Standalone; run after create_tables.sql and kpi_views.sql.
-- ============================================================================

-- Q1. Exposure at a glance (and which data basis this run used)
SELECT * FROM v_class_balance;

-- Q2. Does "large amount" mean "fraud"? (tail-heavy, not threshold-simple)
SELECT * FROM v_amount_by_class ORDER BY class;

-- Q3. Fraud concentration by amount band — where the dollars actually sit
SELECT * FROM v_amount_band_risk ORDER BY amount_band;

-- Q4. When does fraud cluster? (hour-of-day exposure for review staffing)
SELECT * FROM v_fraud_by_hour ORDER BY fraud_rate DESC LIMIT 8;

-- Q5. The threshold economics: top 10 operating points by net savings
SELECT * FROM v_threshold_ranking WHERE savings_rank <= 10 ORDER BY savings_rank;

-- Q6. The three deployment scenarios, ranked by savings per 100K txns
SELECT * FROM v_scenario_comparison;

-- Q7. Model comparison (from the committed Python outputs)
SELECT model, ROUND(average_precision_pr_auc, 3) AS pr_auc,
       ROUND(roc_auc, 3) AS roc_auc,
       ROUND(precision_at_0_50, 3) AS precision_at_050,
       ROUND(recall_at_0_50, 3) AS recall_at_050
FROM model_metrics ORDER BY pr_auc DESC;

-- Q8. Claim check: recompute the README's headline numbers
SELECT * FROM v_validation_headlines;
