import pandas as pd

from fraud_risk.costs import (
    CostAssumptions,
    choose_deployment_scenarios,
    current_state_cost,
    false_positive_cost,
    fraud_loss,
    threshold_cost_table,
)


def test_fraud_loss_includes_amount_and_fee():
    assumptions = CostAssumptions(fraud_loss_multiplier=1.0, chargeback_fee=15.0)

    assert fraud_loss([100.0, 50.0], assumptions) == 180.0


def test_false_positive_cost_includes_fixed_and_amount_linked_cost():
    assumptions = CostAssumptions(false_positive_fixed_cost=5.0, false_positive_amount_rate=0.10)

    assert false_positive_cost([100.0, 50.0], assumptions) == 25.0


def test_threshold_cost_table_rewards_catching_fraud_when_scores_separate():
    y = [0, 0, 1, 1]
    scores = [0.01, 0.02, 0.95, 0.99]
    amounts = [100.0, 100.0, 200.0, 300.0]
    assumptions = CostAssumptions(
        chargeback_fee=0.0,
        review_cost_per_alert=1.0,
        false_positive_fixed_cost=1.0,
        false_positive_amount_rate=0.0,
    )

    table = threshold_cost_table(y, scores, amounts, [0.5, 0.98], assumptions)
    good_threshold = table.loc[table["threshold"].eq(0.5)].iloc[0]
    high_threshold = table.loc[table["threshold"].eq(0.98)].iloc[0]

    assert current_state_cost(y, amounts, assumptions) == 500.0
    assert good_threshold["recall"] == 1.0
    assert good_threshold["net_savings"] > high_threshold["net_savings"]


def test_choose_deployment_scenarios_returns_three_named_rows():
    table = pd.DataFrame(
        {
            "threshold": [0.9, 0.5, 0.1],
            "alert_rate": [0.01, 0.03, 0.08],
            "precision": [0.9, 0.7, 0.4],
            "recall": [0.3, 0.8, 0.9],
            "false_positive_rate": [0.001, 0.02, 0.07],
            "alerts": [10, 30, 80],
            "net_savings": [100.0, 200.0, 150.0],
            "net_savings_per_100k": [1000.0, 2000.0, 1500.0],
            "model_cost_per_100k": [900.0, 800.0, 850.0],
            "baseline_cost_per_100k": [2000.0, 2000.0, 2000.0],
        }
    )

    scenarios = choose_deployment_scenarios(table)

    assert list(scenarios["scenario"]) == [
        "Aggressive review",
        "Cost-balanced default",
        "Conservative flagging",
    ]

