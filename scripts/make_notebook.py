"""Create a readable Jupyter notebook companion for the project."""

from __future__ import annotations

import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
NOTEBOOK_PATH = PROJECT_ROOT / "notebooks" / "fraud_risk_analysis.ipynb"


def markdown_cell(source: str) -> dict:
    return {"cell_type": "markdown", "metadata": {}, "source": source.splitlines(True)}


def code_cell(source: str) -> dict:
    return {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": source.splitlines(True),
    }


def build_notebook() -> dict:
    cells = [
        markdown_cell(
            "# Transaction Fraud Detection and Risk Strategy\n"
            "\n"
            "This notebook is the reader-facing companion to the scripts in `scripts/`. "
            "It walks through the data profile, severe class imbalance, model evaluation, "
            "and threshold-cost tradeoff."
        ),
        markdown_cell(
            "## tl;dr\n"
            "\n"
            "Run the project scripts first to generate the CSV outputs and chart assets. "
            "The core finding is not just which model has the highest score, but which "
            "decision threshold balances fraud loss against false-positive customer friction."
        ),
        code_cell(
            "from pathlib import Path\n"
            "import sys\n"
            "import pandas as pd\n"
            "\n"
            "PROJECT_ROOT = Path.cwd().parent if Path.cwd().name == 'notebooks' else Path.cwd()\n"
            "sys.path.insert(0, str(PROJECT_ROOT / 'src'))\n"
            "\n"
            "from fraud_risk.config import OUTPUTS_DIR\n"
        ),
        markdown_cell("## Context and methods"),
        code_cell(
            "profile = pd.read_json(OUTPUTS_DIR / 'data_profile.json', typ='series')\n"
            "balance = pd.read_csv(OUTPUTS_DIR / 'class_balance.csv')\n"
            "amounts = pd.read_csv(OUTPUTS_DIR / 'amount_by_class.csv')\n"
            "metrics = pd.read_csv(OUTPUTS_DIR / 'model_metrics.csv')\n"
            "thresholds = pd.read_csv(OUTPUTS_DIR / 'threshold_cost_table.csv')\n"
            "scenarios = pd.read_csv(OUTPUTS_DIR / 'deployment_scenarios.csv')\n"
        ),
        markdown_cell("## Data"),
        code_cell(
            "print(f\"Rows: {int(profile['row_count']):,}\")\n"
            "print(f\"Fraud rate: {profile['fraud_rate']:.3%}\")\n"
            "balance\n"
        ),
        code_cell("amounts"),
        markdown_cell("## Results"),
        code_cell("metrics"),
        code_cell(
            "scenarios[['scenario', 'threshold', 'alert_rate', 'precision', 'recall', 'net_savings_per_100k']]"
        ),
        markdown_cell(
            "## Takeaways\n"
            "\n"
            "- PR-AUC, precision, and recall are more useful than accuracy because fraud is extremely rare.\n"
            "- The threshold should be selected against an explicit cost model, not a generic 0.50 cutoff.\n"
            "- Because V1-V28 are PCA-anonymized, the project should not over-claim feature-level explanations."
        ),
    ]
    return {
        "cells": cells,
        "metadata": {
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3",
            },
            "language_info": {"name": "python", "pygments_lexer": "ipython3"},
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }


def main() -> None:
    NOTEBOOK_PATH.parent.mkdir(parents=True, exist_ok=True)
    NOTEBOOK_PATH.write_text(json.dumps(build_notebook(), indent=2), encoding="utf-8")
    print(f"Wrote {NOTEBOOK_PATH}")


if __name__ == "__main__":
    main()

