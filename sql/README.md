# SQL Layer — Validation, Exposure Cuts & Threshold Ranking

DuckDB scripts covering everything that is counting, exposure and ranking:
data-quality checks, fraud-concentration views (by class, amount band,
hour), and rankings over the Python model's committed decision tables
(threshold economics, deployment scenarios). The classifier itself stays in
`src/fraud_risk` — SQL doesn't pretend to do machine learning; it validates
the data going in and organizes the decisions coming out.

## Files (run in this order)

| File | What it does |
|---|---|
| `create_tables.sql` | Loads transactions (full raw file if present locally, else the included sample — and records which) + the committed model outputs |
| `data_quality_checks.sql` | 6 checks: missing values, label domain, negative amounts, the 1,081 duplicate rows (documented, not dropped), capture-window bounds |
| `kpi_views.sql` | Class balance, amount stats by class, fraud by hour-of-day, amount-band risk, threshold ranking, scenario comparison, README claim-check |
| `analysis_queries.sql` | 8 questions ending with the claim check |

## How to run

```bash
pip install duckdb
python scripts/run_sql.py     # runs everything + writes data/powerbi/ inputs
```

## Full file vs included sample

The full ULB file (284,807 rows, ~150MB) exceeds GitHub's file-size limit,
so the repo includes a **stratified sample** (`data/sample/`): every one of
the 492 fraud rows plus a seeded 20,000 legitimate rows. Rates on the
sample are inflated by construction — every output carries a `data_basis`
label, and the claim-check view says which basis it ran on. The committed
`data/powerbi/` exports were generated from the **full** file so they match
the README's numbers.
