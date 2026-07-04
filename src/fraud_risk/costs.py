"""Cost model for fraud losses and false-positive customer friction."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Iterable

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class CostAssumptions:
    """Default operating assumptions for threshold analysis.

    Amount is treated as the transaction currency in the dataset. The Kaggle
    page describes European card transactions, but does not expose enough
    business context to know card issuer recovery rates or interchange impact.
    These defaults are intentionally simple and should be replaced by issuer
    economics before production use.
    """

    fraud_loss_multiplier: float = 1.0
    chargeback_fee: float = 15.0
    review_cost_per_alert: float = 3.0
    false_positive_fixed_cost: float = 5.0
    false_positive_amount_rate: float = 0.025
    current_state_detection_rate: float = 0.0

    def to_dict(self) -> dict[str, float]:
        return asdict(self)


def fraud_loss(amounts: Iterable[float], assumptions: CostAssumptions) -> float:
    """Direct cost of fraud that is not stopped."""
    arr = np.asarray(list(amounts), dtype=float)
    return float(arr.sum() * assumptions.fraud_loss_multiplier + len(arr) * assumptions.chargeback_fee)


def false_positive_cost(amounts: Iterable[float], assumptions: CostAssumptions) -> float:
    """Cost of wrongly flagging legitimate transactions."""
    arr = np.asarray(list(amounts), dtype=float)
    return float(
        len(arr) * assumptions.false_positive_fixed_cost
        + arr.sum() * assumptions.false_positive_amount_rate
    )


def current_state_cost(
    y_true: Iterable[int], amounts: Iterable[float], assumptions: CostAssumptions
) -> float:
    """Cost if no model-assisted decisioning is used in the scored population."""
    y = np.asarray(list(y_true), dtype=int)
    amount_arr = np.asarray(list(amounts), dtype=float)
    total_fraud_cost = fraud_loss(amount_arr[y == 1], assumptions)
    stopped_share = assumptions.current_state_detection_rate
    return float(total_fraud_cost * (1 - stopped_share))


def threshold_cost_table(
    y_true: Iterable[int],
    y_score: Iterable[float],
    amounts: Iterable[float],
    thresholds: Iterable[float],
    assumptions: CostAssumptions | None = None,
    normalize_per_transactions: int = 100_000,
) -> pd.DataFrame:
    """Evaluate precision, recall, alert volume, and costs by threshold."""
    assumptions = assumptions or CostAssumptions()
    y = np.asarray(list(y_true), dtype=int)
    scores = np.asarray(list(y_score), dtype=float)
    amount_arr = np.asarray(list(amounts), dtype=float)
    baseline_cost = current_state_cost(y, amount_arr, assumptions)
    scale = normalize_per_transactions / len(y) if len(y) else 1.0

    rows = []
    for threshold in sorted(set(float(t) for t in thresholds), reverse=True):
        predicted = scores >= threshold
        tp = int(((predicted) & (y == 1)).sum())
        fp = int(((predicted) & (y == 0)).sum())
        fn = int(((~predicted) & (y == 1)).sum())
        tn = int(((~predicted) & (y == 0)).sum())
        alerts = tp + fp

        uncaught_fraud_cost = fraud_loss(amount_arr[(~predicted) & (y == 1)], assumptions)
        false_positive_friction = false_positive_cost(
            amount_arr[(predicted) & (y == 0)], assumptions
        )
        review_cost = alerts * assumptions.review_cost_per_alert
        total_cost = uncaught_fraud_cost + false_positive_friction + review_cost
        fraud_cost_caught = fraud_loss(amount_arr[(predicted) & (y == 1)], assumptions)

        precision = tp / alerts if alerts else 0.0
        recall = tp / (tp + fn) if tp + fn else 0.0
        fpr = fp / (fp + tn) if fp + tn else 0.0

        rows.append(
            {
                "threshold": threshold,
                "alerts": alerts,
                "alert_rate": alerts / len(y) if len(y) else 0.0,
                "true_positives": tp,
                "false_positives": fp,
                "false_negatives": fn,
                "true_negatives": tn,
                "precision": precision,
                "recall": recall,
                "false_positive_rate": fpr,
                "baseline_cost": baseline_cost,
                "model_assisted_cost": total_cost,
                "fraud_loss_uncaught": uncaught_fraud_cost,
                "fraud_loss_caught": fraud_cost_caught,
                "false_positive_friction_cost": false_positive_friction,
                "review_operations_cost": review_cost,
                "net_savings": baseline_cost - total_cost,
                "baseline_cost_per_100k": baseline_cost * scale,
                "model_cost_per_100k": total_cost * scale,
                "net_savings_per_100k": (baseline_cost - total_cost) * scale,
            }
        )

    return pd.DataFrame(rows)


def choose_deployment_scenarios(threshold_table: pd.DataFrame) -> pd.DataFrame:
    """Pick three stakeholder-readable threshold scenarios from a cost table."""
    if threshold_table.empty:
        raise ValueError("threshold_table is empty")

    positive_savings = threshold_table[threshold_table["net_savings"] > 0]
    candidate_pool = positive_savings if not positive_savings.empty else threshold_table

    balanced = candidate_pool.sort_values("net_savings", ascending=False).iloc[0]

    aggressive_pool = candidate_pool.copy()
    aggressive_pool = aggressive_pool.sort_values(
        ["recall", "net_savings"], ascending=[False, False]
    )
    aggressive = aggressive_pool.iloc[0]

    conservative_pool = candidate_pool[candidate_pool["precision"] >= 0.75]
    if conservative_pool.empty:
        conservative_pool = candidate_pool[candidate_pool["precision"] >= 0.50]
    if conservative_pool.empty:
        conservative_pool = candidate_pool.sort_values("precision", ascending=False).head(10)
    conservative = conservative_pool.sort_values(
        ["precision", "net_savings"], ascending=[False, False]
    ).iloc[0]

    def choose_distinct(row: pd.Series, ordered: pd.DataFrame, used: set[float]) -> pd.Series:
        if float(row["threshold"]) not in used:
            return row
        for _, candidate in ordered.iterrows():
            if float(candidate["threshold"]) not in used:
                return candidate
        return row

    rows = []
    scenario_specs = [
        (
            "Aggressive review",
            aggressive,
            aggressive_pool,
            "Maximize fraud capture when review capacity and customer messaging can absorb more alerts.",
        ),
        (
            "Cost-balanced default",
            balanced,
            candidate_pool.sort_values("net_savings", ascending=False),
            "Use as the recommended operating point under the default cost assumptions.",
        ),
        (
            "Conservative flagging",
            conservative,
            conservative_pool.sort_values(["precision", "net_savings"], ascending=[False, False]),
            "Prioritize customer experience by flagging fewer legitimate transactions.",
        ),
    ]

    used_thresholds: set[float] = set()
    for label, row, ordered, use_case in scenario_specs:
        row = choose_distinct(row, ordered, used_thresholds)
        used_thresholds.add(float(row["threshold"]))
        scenario = row.to_dict()
        scenario["scenario"] = label
        scenario["use_case"] = use_case
        rows.append(scenario)

    cols = [
        "scenario",
        "use_case",
        "threshold",
        "alert_rate",
        "precision",
        "recall",
        "false_positive_rate",
        "alerts",
        "net_savings_per_100k",
        "model_cost_per_100k",
        "baseline_cost_per_100k",
    ]
    return pd.DataFrame(rows)[cols]
