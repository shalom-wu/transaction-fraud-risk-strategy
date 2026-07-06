-- ============================================================================
-- create_tables.sql — load transactions + the model's decision tables
-- Run from the repo root (scripts/run_sql.py does this). Uses the full raw
-- file when present locally, otherwise the included stratified sample —
-- and records which one, because rates differ by construction.
-- ============================================================================

-- scripts/run_sql.py substitutes the path + label before execution
CREATE OR REPLACE TABLE transactions AS
SELECT * FROM read_csv_auto('{DATA_PATH}', header = true);

CREATE OR REPLACE TABLE meta AS
SELECT '{DATA_LABEL}' AS data_basis;

-- The Python pipeline's decision outputs (outputs/ is committed) — SQL
-- queries these to rank thresholds and scenarios without re-running models.
CREATE OR REPLACE TABLE threshold_costs AS
SELECT * FROM read_csv_auto('outputs/threshold_cost_table.csv', header = true);

CREATE OR REPLACE TABLE deployment_scenarios AS
SELECT * FROM read_csv_auto('outputs/deployment_scenarios.csv', header = true);

CREATE OR REPLACE TABLE model_metrics AS
SELECT * FROM read_csv_auto('outputs/model_metrics.csv', header = true);
