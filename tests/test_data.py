import pandas as pd
import pytest

from fraud_risk.data import DatasetSchemaError, clean_transactions, validate_schema


def make_minimal_frame():
    row = {"Time": 3600, "Amount": 10.0, "Class": 0}
    for i in range(1, 29):
        row[f"V{i}"] = 0.1 * i
    return pd.DataFrame([row])


def test_clean_transactions_adds_relative_features():
    cleaned = clean_transactions(make_minimal_frame())

    assert cleaned.loc[0, "relative_hour"] == 1
    assert cleaned.loc[0, "elapsed_day"] == 1
    assert bool(cleaned.loc[0, "is_fraud"]) is False
    assert "amount_log1p" in cleaned.columns


def test_validate_schema_rejects_missing_columns():
    df = make_minimal_frame().drop(columns=["V3"])

    with pytest.raises(DatasetSchemaError):
        validate_schema(df)


def test_validate_schema_rejects_bad_labels():
    df = make_minimal_frame()
    df.loc[0, "Class"] = 7

    with pytest.raises(DatasetSchemaError):
        validate_schema(df)
