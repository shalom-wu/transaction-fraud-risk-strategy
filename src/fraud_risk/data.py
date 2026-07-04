"""Data loading, validation, and descriptive summaries."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from fraud_risk.config import RAW_DATA_PATH


PCA_FEATURES = [f"V{i}" for i in range(1, 29)]
EXPECTED_COLUMNS = ["Time", *PCA_FEATURES, "Amount", "Class"]


class DatasetSchemaError(ValueError):
    """Raised when the fraud dataset does not match the expected schema."""


def load_transactions(path: str | Path = RAW_DATA_PATH) -> pd.DataFrame:
    """Load the Kaggle/ULB credit card fraud dataset."""
    data_path = Path(path)
    if not data_path.exists():
        raise FileNotFoundError(
            f"Dataset not found at {data_path}. Download Kaggle dataset "
            "mlg-ulb/creditcardfraud and place creditcard.csv in data/raw/."
        )
    return pd.read_csv(data_path)


def validate_schema(df: pd.DataFrame) -> None:
    """Validate required columns, label values, and basic numeric usability."""
    missing = [col for col in EXPECTED_COLUMNS if col not in df.columns]
    if missing:
        raise DatasetSchemaError(f"Missing required columns: {missing}")

    unexpected_labels = sorted(set(df["Class"].dropna().unique()) - {0, 1})
    if unexpected_labels:
        raise DatasetSchemaError(
            f"Class must be binary with 0=legitimate and 1=fraud. "
            f"Unexpected labels: {unexpected_labels}"
        )

    numeric_cols = EXPECTED_COLUMNS
    non_numeric = [
        col for col in numeric_cols if not pd.api.types.is_numeric_dtype(df[col])
    ]
    if non_numeric:
        raise DatasetSchemaError(f"Expected numeric columns: {non_numeric}")


def clean_transactions(df: pd.DataFrame) -> pd.DataFrame:
    """Return a validated copy with derived time and amount features.

    The Kaggle dataset stores Time as seconds elapsed from the first
    transaction, not an absolute timestamp. The derived hour is therefore a
    relative hour within the dataset window, not a real local hour of day.
    """
    cleaned = df.copy()
    cleaned.columns = [col.strip() for col in cleaned.columns]
    validate_schema(cleaned)

    for col in EXPECTED_COLUMNS:
        cleaned[col] = pd.to_numeric(cleaned[col], errors="raise")

    cleaned["Class"] = cleaned["Class"].astype(int)
    cleaned["is_fraud"] = cleaned["Class"].eq(1)
    cleaned["elapsed_hours"] = cleaned["Time"] / 3600
    cleaned["elapsed_day"] = (cleaned["Time"] // 86400).astype(int) + 1
    cleaned["relative_hour"] = ((cleaned["Time"] // 3600) % 24).astype(int)
    cleaned["amount_log1p"] = np.log1p(cleaned["Amount"])
    return cleaned


def data_quality_summary(df: pd.DataFrame) -> dict[str, Any]:
    """Summarize rows, missingness, duplicates, class balance, and time span."""
    validate_schema(df)
    label_counts = df["Class"].value_counts().sort_index()
    row_count = int(len(df))
    fraud_count = int(label_counts.get(1, 0))
    legitimate_count = int(label_counts.get(0, 0))
    return {
        "row_count": row_count,
        "column_count": int(df.shape[1]),
        "missing_cells": int(df.isna().sum().sum()),
        "duplicate_rows": int(df.duplicated().sum()),
        "legitimate_transactions": legitimate_count,
        "fraud_transactions": fraud_count,
        "fraud_rate": fraud_count / row_count if row_count else 0.0,
        "time_min_seconds": float(df["Time"].min()),
        "time_max_seconds": float(df["Time"].max()),
        "dataset_days": float((df["Time"].max() - df["Time"].min()) / 86400),
    }


def class_balance_table(df: pd.DataFrame) -> pd.DataFrame:
    """Return class counts and shares."""
    counts = df["Class"].value_counts().sort_index().rename("transactions")
    result = counts.reset_index().rename(columns={"Class": "class"})
    result["label"] = result["class"].map({0: "Legitimate", 1: "Fraud"})
    result["share"] = result["transactions"] / result["transactions"].sum()
    return result[["class", "label", "transactions", "share"]]


def amount_summary_by_class(df: pd.DataFrame) -> pd.DataFrame:
    """Summarize transaction amounts by fraud label."""
    summary = (
        df.groupby("Class")["Amount"]
        .agg(["count", "mean", "median", "sum", "max"])
        .reset_index()
        .rename(
            columns={
                "Class": "class",
                "count": "transactions",
                "mean": "mean_amount",
                "median": "median_amount",
                "sum": "total_amount",
                "max": "max_amount",
            }
        )
    )
    summary["label"] = summary["class"].map({0: "Legitimate", 1: "Fraud"})
    return summary[
        [
            "class",
            "label",
            "transactions",
            "mean_amount",
            "median_amount",
            "total_amount",
            "max_amount",
        ]
    ]


def hourly_fraud_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate transaction and fraud behavior by relative hour in day."""
    grouped = (
        df.groupby("relative_hour")
        .agg(
            transactions=("Class", "size"),
            fraud_transactions=("Class", "sum"),
            total_amount=("Amount", "sum"),
            fraud_amount=("Amount", lambda s: s[df.loc[s.index, "Class"].eq(1)].sum()),
        )
        .reset_index()
    )
    grouped["fraud_rate"] = grouped["fraud_transactions"] / grouped["transactions"]
    return grouped

