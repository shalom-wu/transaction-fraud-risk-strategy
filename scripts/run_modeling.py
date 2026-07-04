"""Train imbalanced fraud models and evaluate threshold economics."""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from fraud_risk.config import FIGURES_DIR, OUTPUTS_DIR, RANDOM_STATE, RAW_DATA_PATH  # noqa: E402
from fraud_risk.costs import CostAssumptions, choose_deployment_scenarios, threshold_cost_table  # noqa: E402
from fraud_risk.data import clean_transactions, load_transactions  # noqa: E402
from fraud_risk.modeling import (  # noqa: E402
    choose_best_model,
    model_metrics_frame,
    precision_recall_points,
    threshold_candidates,
    train_candidate_models,
    train_test_frame,
)
from fraud_risk.reporting import dataframe_to_markdown, format_currency, format_pct, write_json  # noqa: E402
from fraud_risk.viz import save_cost_curve_chart, save_precision_recall_curve, save_threshold_tradeoff_chart  # noqa: E402


def _format_metrics(metrics: pd.DataFrame) -> pd.DataFrame:
    display = metrics.copy()
    for col in [
        "average_precision_pr_auc",
        "roc_auc",
        "precision_at_0_50",
        "recall_at_0_50",
        "f1_at_0_50",
        "alert_rate_at_0_50",
    ]:
        display[col] = display[col].map(lambda value: f"{float(value):.3f}")
    return display


def _format_scenarios(scenarios: pd.DataFrame) -> pd.DataFrame:
    display = scenarios.copy()
    for col in ["threshold", "precision", "recall", "false_positive_rate", "alert_rate"]:
        display[col] = display[col].map(lambda value: f"{float(value):.3f}")
    for col in ["net_savings_per_100k", "model_cost_per_100k", "baseline_cost_per_100k"]:
        display[col] = display[col].map(lambda value: format_currency(float(value), 0))
    return display


def build_model_card(
    best_model_name: str,
    metrics: pd.DataFrame,
    scenarios: pd.DataFrame,
    assumptions: CostAssumptions,
) -> str:
    scenario_display = _format_scenarios(scenarios)
    metric_display = _format_metrics(metrics)
    recommended = scenarios.loc[scenarios["scenario"].eq("Cost-balanced default")].iloc[0]

    return f"""# Model Card and Threshold Cost Notes

## Model choice

The selected model is **{best_model_name}**, chosen by holdout PR-AUC. ROC-AUC
is reported for completeness, but PR-AUC, precision, recall, and threshold
cost are more relevant under a fraud base rate below 1%.

{dataframe_to_markdown(metric_display)}

## Recommended operating point under default assumptions

The cost-balanced threshold flags **{format_pct(float(recommended["alert_rate"]), 2)}**
of transactions, reaches **{format_pct(float(recommended["recall"]), 1)} recall**
and **{format_pct(float(recommended["precision"]), 1)} precision**, and improves
cost by **{format_currency(float(recommended["net_savings_per_100k"]), 0)} per
100,000 scored transactions** against the current-state assumption.

## Deployment scenarios

{dataframe_to_markdown(scenario_display)}

## Cost assumptions

- Missed fraud loss: transaction amount x {assumptions.fraud_loss_multiplier:.2f}
- Chargeback/admin fee on missed fraud: {format_currency(assumptions.chargeback_fee, 2)} per fraud
- Manual review operations cost: {format_currency(assumptions.review_cost_per_alert, 2)} per alert
- False-positive fixed friction cost: {format_currency(assumptions.false_positive_fixed_cost, 2)} per legitimate alert
- False-positive amount-linked friction: {format_pct(assumptions.false_positive_amount_rate, 2)} of legitimate transaction amount
- Current-state detection rate assumption: {format_pct(assumptions.current_state_detection_rate, 1)}

These are portfolio-planning assumptions, not issuer-specific economics. A real
deployment should replace them with chargeback recovery, review capacity,
interchange/revenue impact, false-decline churn impact, and current rule-stack
detection rates.
"""


def main() -> None:
    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)

    df = clean_transactions(load_transactions(RAW_DATA_PATH))
    X_train, X_test, y_train, y_test, _, amount_test = train_test_frame(
        df, random_state=RANDOM_STATE
    )

    results, resampling_method = train_candidate_models(
        X_train, y_train, X_test, y_test, random_state=RANDOM_STATE
    )
    metrics = model_metrics_frame(results)
    best = choose_best_model(results)

    assumptions = CostAssumptions()
    thresholds = threshold_candidates(best.scores)
    threshold_table = threshold_cost_table(y_test, best.scores, amount_test, thresholds, assumptions)
    scenarios = choose_deployment_scenarios(threshold_table)
    pr_points = precision_recall_points(y_test, best.scores)

    metrics.to_csv(OUTPUTS_DIR / "model_metrics.csv", index=False)
    threshold_table.to_csv(OUTPUTS_DIR / "threshold_cost_table.csv", index=False)
    scenarios.to_csv(OUTPUTS_DIR / "deployment_scenarios.csv", index=False)
    pr_points.to_csv(OUTPUTS_DIR / "precision_recall_curve.csv", index=False)
    pd.DataFrame([assumptions.to_dict()]).to_csv(OUTPUTS_DIR / "cost_assumptions.csv", index=False)
    write_json(
        OUTPUTS_DIR / "model_run_metadata.json",
        {
            "selected_model": best.name,
            "resampling_method": resampling_method,
            "test_rows": int(len(y_test)),
            "test_fraud_rows": int(y_test.sum()),
            "random_state": RANDOM_STATE,
        },
    )

    model_card = build_model_card(best.name, metrics, scenarios, assumptions)
    (OUTPUTS_DIR / "model_card.md").write_text(model_card, encoding="utf-8")

    save_precision_recall_curve(y_test, best.scores, FIGURES_DIR / "precision_recall_curve.png")
    save_threshold_tradeoff_chart(threshold_table, FIGURES_DIR / "threshold_tradeoff.png")
    save_cost_curve_chart(threshold_table, FIGURES_DIR / "cost_curve.png")

    print("Modeling complete")
    print(f"Selected model: {best.name}")
    print(f"Resampling method: {resampling_method}")
    print(f"PR-AUC: {best.metrics['average_precision_pr_auc']:.3f}")


if __name__ == "__main__":
    main()

