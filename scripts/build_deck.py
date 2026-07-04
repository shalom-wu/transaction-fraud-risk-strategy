"""Generate a markdown strategy deck from saved analysis outputs."""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from fraud_risk.config import OUTPUTS_DIR, REPORTS_DIR  # noqa: E402
from fraud_risk.reporting import format_currency, format_number, format_pct, read_json  # noqa: E402


def _scenario_lines(scenarios: pd.DataFrame) -> str:
    rows = []
    for _, row in scenarios.iterrows():
        rows.append(
            f"- **{row['scenario']}**: threshold {row['threshold']:.3f}, "
            f"flags {format_pct(row['alert_rate'], 2)} of transactions, "
            f"precision {format_pct(row['precision'], 1)}, recall {format_pct(row['recall'], 1)}, "
            f"net savings {format_currency(row['net_savings_per_100k'], 0)} per 100k scored."
        )
    return "\n".join(rows)


def build_strategy_deck() -> str:
    profile = read_json(OUTPUTS_DIR / "data_profile.json")
    metrics = pd.read_csv(OUTPUTS_DIR / "model_metrics.csv")
    scenarios = pd.read_csv(OUTPUTS_DIR / "deployment_scenarios.csv")
    amounts = pd.read_csv(OUTPUTS_DIR / "amount_by_class.csv")
    metadata = read_json(OUTPUTS_DIR / "model_run_metadata.json")

    best_metrics = metrics.iloc[0]
    recommended = scenarios.loc[scenarios["scenario"].eq("Cost-balanced default")].iloc[0]
    fraud_amount = amounts.loc[amounts["class"].eq(1), "total_amount"].iloc[0]

    return f"""# Transaction Fraud Detection & Risk Strategy

Source: Kaggle/ULB credit card fraud dataset. Features V1-V28 are
PCA-anonymized, so this project emphasizes threshold economics rather than
overstated feature-level explanations.

---

## 1. Problem framing: the tradeoff is not "catch everything"

- The dataset contains **{profile['row_count']:,} transactions** and **{profile['fraud_transactions']:,} frauds**.
- Fraud rate is **{format_pct(profile['fraud_rate'], 3)}**, so plain accuracy is not decision-useful.
- The business problem is a cost tradeoff: missed fraud creates direct loss, but false positives create review cost, blocked legitimate transactions, customer friction, and possible churn.

![Class imbalance](figures/class_imbalance.png)

---

## 2. Key descriptive findings

- Fraud transactions total **{format_currency(fraud_amount, 0)}** in this public sample window.
- Fraud has a higher mean amount than legitimate transactions, but lower median amount. That implies a tail-risk problem, not a simple "high amount equals fraud" rule.
- The derived hour pattern is only relative elapsed time. The dataset does not expose real customer local time, merchant, cardholder, or geography fields.

![Amount distribution](figures/amount_distribution.png)

---

## 3. Model performance: optimize for PR-AUC and operating threshold

- Selected model: **{metadata['selected_model']}**.
- Holdout PR-AUC: **{best_metrics['average_precision_pr_auc']:.3f}**.
- Holdout ROC-AUC: **{best_metrics['roc_auc']:.3f}**, reported only as supporting context.
- At the default 0.50 threshold, precision is **{format_pct(best_metrics['precision_at_0_50'], 1)}** and recall is **{format_pct(best_metrics['recall_at_0_50'], 1)}**. The better decision is to tune the threshold against cost.

![Precision recall curve](figures/precision_recall_curve.png)

---

## 4. Cost comparison: current-state assumption vs model-assisted decisioning

- Current-state assumption: no model-assisted intervention in the scored population, so fraud in the holdout sample is not blocked by this project.
- Default model-assisted cost includes missed fraud, manual review, and false-positive customer friction.
- Recommended threshold improves economics by **{format_currency(recommended['net_savings_per_100k'], 0)} per 100,000 scored transactions**.
- This is normalized per 100k transactions so it can be scaled to a card issuer's actual volume.

![Cost curve](figures/cost_curve.png)

---

## 5. Deployment scenarios

{_scenario_lines(scenarios)}

![Threshold tradeoff](figures/threshold_tradeoff.png)

---

## 6. Recommended approach

Use a **tiered risk policy** rather than one blunt block/allow threshold:

1. Auto-decline only the highest-risk band where precision is strong and the expected fraud loss exceeds customer-friction cost.
2. Send the middle-risk band to manual review or step-up authentication.
3. Allow low-risk transactions, but keep monitoring for drift and new fraud patterns.

The cost-balanced threshold is the starting point, not a permanent rule. Review
capacity, false-decline harm, regulatory tolerance, and fraud drift should
drive the final threshold.

---

## 7. Appendix: methodology, imbalance handling, and limitations

- Data: public Kaggle/ULB anonymized European card transactions.
- Features: `Time`, `Amount`, and PCA-anonymized `V1` through `V28`.
- Modeling: class-weighted logistic regression baseline plus a tree model with resampling for the fraud minority class.
- Evaluation: PR-AUC, precision, recall, threshold tables, and cost per 100k scored transactions.
- Limitation: anonymized features prevent credible feature-level "why" explanations. The strongest original contribution is the false-positive cost framing and threshold/deployment reasoning.

---

## Assumptions to confirm before finalizing a public deck

- What false-positive cost should represent for the target audience: manual review only, customer friction, churn, or all of the above.
- Whether the current-state benchmark should assume no model intervention, an existing rules engine detection rate, or a known fraud operations baseline.
- Review capacity per 100k transactions and acceptable customer-friction tolerance.
- Whether to annualize results using a specific card issuer transaction volume, or keep all figures normalized per 100k scored transactions.
"""


def build_summary() -> str:
    profile = read_json(OUTPUTS_DIR / "data_profile.json")
    metrics = pd.read_csv(OUTPUTS_DIR / "model_metrics.csv")
    scenarios = pd.read_csv(OUTPUTS_DIR / "deployment_scenarios.csv")
    metadata = read_json(OUTPUTS_DIR / "model_run_metadata.json")
    recommended = scenarios.loc[scenarios["scenario"].eq("Cost-balanced default")].iloc[0]
    best_metrics = metrics.iloc[0]

    return f"""# Strategy Summary

This project treats fraud detection as a risk strategy problem, not just a
classification exercise. In the Kaggle/ULB sample, fraud is only
{format_pct(profile['fraud_rate'], 3)} of transactions ({profile['fraud_transactions']:,}
frauds out of {profile['row_count']:,}), which makes accuracy misleading.

The selected model is **{metadata['selected_model']}** with holdout PR-AUC
{best_metrics['average_precision_pr_auc']:.3f}. Under the default cost model,
the cost-balanced threshold flags {format_pct(recommended['alert_rate'], 2)}
of transactions and produces {format_currency(recommended['net_savings_per_100k'], 0)}
in net savings per 100,000 scored transactions.

The recommended deployment is tiered: auto-decline only the highest-risk band,
route the middle-risk band to review or step-up authentication, and monitor
the rest for drift. The headline numbers should be re-cut with issuer-specific
false-positive costs, review capacity, and current fraud controls before a
production decision.
"""


def main() -> None:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    (REPORTS_DIR / "strategy_deck.md").write_text(build_strategy_deck(), encoding="utf-8")
    (REPORTS_DIR / "summary.md").write_text(build_summary(), encoding="utf-8")
    print(f"Wrote {REPORTS_DIR / 'strategy_deck.md'}")
    print(f"Wrote {REPORTS_DIR / 'summary.md'}")


if __name__ == "__main__":
    main()

