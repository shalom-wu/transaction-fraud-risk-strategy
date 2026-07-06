"""Run the SQL layer and write the Power BI-ready tables.

Uses the full raw file when present (matches the README numbers), else the
included stratified sample (labeled). Run from the repo root.
"""

import os
import re
import shutil
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw" / "creditcard.csv"
SAMPLE = ROOT / "data" / "sample" / "creditcard_sample.csv"

FILES = ["create_tables.sql", "data_quality_checks.sql",
         "kpi_views.sql", "analysis_queries.sql"]
SHOW = {"data_quality_checks.sql", "analysis_queries.sql"}

SQL_EXPORTS = {
    "v_class_balance": "kpi_class_balance.csv",
    "v_amount_by_class": "kpi_amount_by_class.csv",
    "v_fraud_by_hour": "kpi_fraud_by_hour.csv",
    "v_amount_band_risk": "kpi_amount_band_risk.csv",
    "v_scenario_comparison": "scenario_comparison.csv",
}
# model outputs copied verbatim so Power BI reads one documented folder
OUTPUT_COPIES = ["threshold_cost_table.csv", "deployment_scenarios.csv",
                 "model_metrics.csv", "precision_recall_curve.csv",
                 "cost_assumptions.csv"]


def main() -> None:
    os.chdir(ROOT)
    if RAW.exists():
        data_path, label = RAW, "full raw file (284,807 rows)"
    else:
        data_path, label = SAMPLE, "included stratified sample (492 frauds + 20,000 legit)"
    print(f"data basis: {label}")

    con = duckdb.connect()
    for name in FILES:
        print(f"\n=== {name} ===")
        sql = (ROOT / "sql" / name).read_text()
        sql = sql.replace("{DATA_PATH}", data_path.as_posix())
        sql = sql.replace("{DATA_LABEL}", label)
        for stmt in [s.strip() for s in re.split(r";\s*(?:\n|$)", sql) if s.strip()]:
            result = con.execute(stmt)
            body = re.sub(r"^\s*(--[^\n]*\n)*", "", stmt).lstrip().upper()
            if name in SHOW and body.startswith(("SELECT", "WITH")):
                print(result.df().to_string(index=False, max_rows=25))
                print()

    out = ROOT / "data" / "powerbi"
    out.mkdir(parents=True, exist_ok=True)
    print("=== exports for Power BI ===")
    for view, fname in SQL_EXPORTS.items():
        target = out / fname
        try:
            if target.exists():
                target.unlink()
            con.execute(f"COPY (SELECT * FROM {view}) TO '{target.as_posix()}' "
                        f"(HEADER, DELIMITER ',')")
        except (PermissionError, duckdb.IOException):
            n = con.execute(f"SELECT COUNT(*) FROM {view}").fetchone()[0]
            print(f"  {fname}: kept existing locked file; expected {n:,} rows")
            continue
        n = con.execute(f"SELECT COUNT(*) FROM {view}").fetchone()[0]
        print(f"  {fname}: {n:,} rows")
    for fname in OUTPUT_COPIES:
        target = out / fname
        try:
            if target.exists():
                target.unlink()
            shutil.copy2(ROOT / "outputs" / fname, target)
        except PermissionError:
            print(f"  {fname}: kept existing locked file; source outputs/{fname}")
            continue
        print(f"  {fname}: copied from outputs/")


if __name__ == "__main__":
    main()
