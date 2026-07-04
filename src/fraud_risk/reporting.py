"""Small formatting helpers for generated markdown artifacts."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd


def format_pct(value: float, digits: int = 1) -> str:
    return f"{value * 100:.{digits}f}%"


def format_currency(value: float, digits: int = 0) -> str:
    return f"${value:,.{digits}f}"


def format_number(value: float, digits: int = 0) -> str:
    return f"{value:,.{digits}f}"


def dataframe_to_markdown(df: pd.DataFrame, max_rows: int | None = None) -> str:
    """Render a compact markdown table without requiring tabulate."""
    shown = df.head(max_rows) if max_rows else df
    columns = [str(col) for col in shown.columns]
    lines = [
        "| " + " | ".join(columns) + " |",
        "| " + " | ".join(["---"] * len(columns)) + " |",
    ]
    for _, row in shown.iterrows():
        values = [str(row[col]) for col in shown.columns]
        lines.append("| " + " | ".join(values) + " |")
    return "\n".join(lines)


def write_json(path: str | Path, payload: dict[str, Any]) -> None:
    Path(path).write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def read_json(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))

