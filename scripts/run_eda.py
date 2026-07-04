"""Run data validation and exploratory analysis."""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from fraud_risk.config import FIGURES_DIR, OUTPUTS_DIR, RAW_DATA_PATH  # noqa: E402
from fraud_risk.data import (  # noqa: E402
    amount_summary_by_class,
    class_balance_table,
    clean_transactions,
    data_quality_summary,
    hourly_fraud_summary,
    load_transactions,
)
from fraud_risk.reporting import dataframe_to_markdown, format_currency, format_pct, write_json  # noqa: E402
from fraud_risk.viz import (  # noqa: E402
    save_amount_distribution_chart,
    save_class_imbalance_chart,
    save_hourly_pattern_chart,
)


def _display_amounts(amounts: pd.DataFrame) -> pd.DataFrame:
    display = amounts.copy()
    for col in ["mean_amount", "median_amount", "total_amount", "max_amount"]:
        display[col] = display[col].map(lambda value: format_currency(float(value), 2))
    return display


def build_data_quality_report(profile: dict, balance: pd.DataFrame, amounts: pd.DataFrame) -> str:
    fraud_rate = profile["fraud_rate"]
    amount_display = _display_amounts(amounts)
    balance_display = balance.copy()
    balance_display["share"] = balance_display["share"].map(lambda value: format_pct(float(value), 3))

    return f"""# Data Quality and Exploratory Notes

## Source file

- Path: `data/raw/creditcard.csv`
- Rows: {profile["row_count"]:,}
- Columns: {profile["column_count"]:,}
- Missing cells: {profile["missing_cells"]:,}
- Exact duplicate rows: {profile["duplicate_rows"]:,}
- Dataset time span: {profile["dataset_days"]:.2f} elapsed days

## Class imbalance

Fraud accounts for **{format_pct(fraud_rate, 3)}** of transactions. This is the
central modeling and business issue: a classifier can be more than 99% accurate
while catching no fraud at all, and a threshold that catches more fraud can
still be economically bad if it blocks too many legitimate customers.

{dataframe_to_markdown(balance_display)}

## Amount distribution

The fraud class has a different amount profile, but amount alone is not enough
to explain the model. The V1-V28 columns are PCA-anonymized, so feature-level
interpretation is intentionally limited.

{dataframe_to_markdown(amount_display)}

## Time pattern caveat

`Time` is seconds elapsed since the first transaction in the dataset. The
project derives `relative_hour = floor(Time / 3600) mod 24`, but this is a
relative elapsed-hour pattern, not an actual customer local time-of-day.
"""


def main() -> None:
    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)

    raw = load_transactions(RAW_DATA_PATH)
    df = clean_transactions(raw)

    profile = data_quality_summary(raw)
    balance = class_balance_table(df)
    amounts = amount_summary_by_class(df)
    hourly = hourly_fraud_summary(df)

    write_json(OUTPUTS_DIR / "data_profile.json", profile)
    balance.to_csv(OUTPUTS_DIR / "class_balance.csv", index=False)
    amounts.to_csv(OUTPUTS_DIR / "amount_by_class.csv", index=False)
    hourly.to_csv(OUTPUTS_DIR / "hourly_fraud_patterns.csv", index=False)

    report = build_data_quality_report(profile, balance, amounts)
    (OUTPUTS_DIR / "data_quality_report.md").write_text(report, encoding="utf-8")

    save_class_imbalance_chart(balance, FIGURES_DIR / "class_imbalance.png")
    save_amount_distribution_chart(df, FIGURES_DIR / "amount_distribution.png")
    save_hourly_pattern_chart(hourly, FIGURES_DIR / "relative_hour_fraud_rate.png")

    print("EDA complete")
    print(f"Wrote outputs to {OUTPUTS_DIR}")
    print(f"Wrote figures to {FIGURES_DIR}")


if __name__ == "__main__":
    main()

