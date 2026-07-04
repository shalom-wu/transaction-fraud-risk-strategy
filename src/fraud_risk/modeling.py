"""Model training and evaluation for imbalanced fraud detection."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import numpy as np
import pandas as pd
from sklearn.ensemble import ExtraTreesClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    average_precision_score,
    f1_score,
    precision_recall_curve,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from fraud_risk.data import PCA_FEATURES


FEATURE_COLUMNS = ["Time", *PCA_FEATURES, "Amount"]


@dataclass
class ModelResult:
    name: str
    estimator: object
    scores: np.ndarray
    metrics: dict[str, float]


def train_test_frame(
    df: pd.DataFrame,
    test_size: float = 0.25,
    random_state: int = 42,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series, pd.Series, pd.Series]:
    """Create a stratified train/test split and keep amount for cost analysis."""
    X = df[FEATURE_COLUMNS].copy()
    y = df["Class"].astype(int)
    amounts = df["Amount"].astype(float)
    return train_test_split(
        X,
        y,
        amounts,
        test_size=test_size,
        stratify=y,
        random_state=random_state,
    )


def random_oversample_minority(
    X: pd.DataFrame,
    y: pd.Series,
    target_minority_rate: float = 0.08,
    random_state: int = 42,
) -> tuple[pd.DataFrame, pd.Series]:
    """Oversample fraud rows to a bounded minority share.

    This is intentionally conservative: it helps the tree model see more fraud
    examples without creating a 50/50 training set that no longer resembles the
    real operating base rate.
    """
    if not 0 < target_minority_rate < 0.5:
        raise ValueError("target_minority_rate must be between 0 and 0.5")

    y = y.astype(int)
    minority_idx = y[y == 1].index.to_numpy()
    majority_idx = y[y == 0].index.to_numpy()
    if len(minority_idx) < 2:
        raise ValueError("Need at least two minority examples for resampling")

    current_rate = len(minority_idx) / len(y)
    if current_rate >= target_minority_rate:
        return X.copy(), y.copy()

    target_minority_count = int(
        np.ceil((target_minority_rate / (1 - target_minority_rate)) * len(majority_idx))
    )
    additional_needed = max(0, target_minority_count - len(minority_idx))

    rng = np.random.default_rng(random_state)
    sampled_idx = rng.choice(minority_idx, size=additional_needed, replace=True)
    combined_idx = np.concatenate([majority_idx, minority_idx, sampled_idx])
    rng.shuffle(combined_idx)

    return X.loc[combined_idx].reset_index(drop=True), y.loc[combined_idx].reset_index(drop=True)


def smote_or_random_resample(
    X: pd.DataFrame,
    y: pd.Series,
    target_minority_rate: float = 0.08,
    random_state: int = 42,
) -> tuple[pd.DataFrame, pd.Series, str]:
    """Use SMOTE when installed, otherwise fall back to random oversampling."""
    sampling_strategy = target_minority_rate / (1 - target_minority_rate)
    minority_count = int((y == 1).sum())
    try:
        from imblearn.over_sampling import SMOTE

        k_neighbors = max(1, min(5, minority_count - 1))
        sampler = SMOTE(
            sampling_strategy=sampling_strategy,
            k_neighbors=k_neighbors,
            random_state=random_state,
        )
        X_resampled, y_resampled = sampler.fit_resample(X, y)
        return pd.DataFrame(X_resampled, columns=X.columns), pd.Series(y_resampled), "SMOTE"
    except Exception:
        X_resampled, y_resampled = random_oversample_minority(
            X, y, target_minority_rate=target_minority_rate, random_state=random_state
        )
        return X_resampled, y_resampled, "Random oversampling fallback"


def fit_logistic_baseline(X_train: pd.DataFrame, y_train: pd.Series) -> Pipeline:
    """Fit a class-weighted logistic regression baseline."""
    model = Pipeline(
        steps=[
            ("scaler", StandardScaler()),
            (
                "classifier",
                LogisticRegression(
                    class_weight="balanced",
                    max_iter=2000,
                    solver="lbfgs",
                    random_state=42,
                ),
            ),
        ]
    )
    model.fit(X_train, y_train)
    return model


def fit_tree_model(
    X_train: pd.DataFrame,
    y_train: pd.Series,
    random_state: int = 42,
) -> tuple[object, str]:
    """Fit a resampled tree-based model for the minority fraud class."""
    X_resampled, y_resampled, resampling_method = smote_or_random_resample(
        X_train, y_train, target_minority_rate=0.08, random_state=random_state
    )
    model = ExtraTreesClassifier(
        n_estimators=140,
        min_samples_leaf=4,
        max_features="sqrt",
        n_jobs=1,
        random_state=random_state,
    )
    model.fit(X_resampled, y_resampled)
    return model, resampling_method


def predict_scores(model: object, X: pd.DataFrame) -> np.ndarray:
    """Return positive-class scores from a fitted classifier."""
    if hasattr(model, "predict_proba"):
        return np.asarray(model.predict_proba(X)[:, 1], dtype=float)
    if hasattr(model, "decision_function"):
        decision = np.asarray(model.decision_function(X), dtype=float)
        return 1 / (1 + np.exp(-decision))
    raise TypeError("Model must expose predict_proba or decision_function")


def classification_metrics(y_true: Iterable[int], scores: Iterable[float]) -> dict[str, float]:
    """Evaluate PR-AUC, ROC-AUC, and default-threshold classification metrics."""
    y = np.asarray(list(y_true), dtype=int)
    score_arr = np.asarray(list(scores), dtype=float)
    pred = score_arr >= 0.5
    return {
        "average_precision_pr_auc": float(average_precision_score(y, score_arr)),
        "roc_auc": float(roc_auc_score(y, score_arr)),
        "precision_at_0_50": float(precision_score(y, pred, zero_division=0)),
        "recall_at_0_50": float(recall_score(y, pred, zero_division=0)),
        "f1_at_0_50": float(f1_score(y, pred, zero_division=0)),
        "alert_rate_at_0_50": float(pred.mean()),
    }


def train_candidate_models(
    X_train: pd.DataFrame,
    y_train: pd.Series,
    X_test: pd.DataFrame,
    y_test: pd.Series,
    random_state: int = 42,
) -> tuple[list[ModelResult], str]:
    """Train baseline and tree model, returning holdout scores and metrics."""
    logistic = fit_logistic_baseline(X_train, y_train)
    logistic_scores = predict_scores(logistic, X_test)

    tree, resampling_method = fit_tree_model(X_train, y_train, random_state=random_state)
    tree_scores = predict_scores(tree, X_test)

    results = [
        ModelResult(
            name="Class-weighted logistic regression",
            estimator=logistic,
            scores=logistic_scores,
            metrics=classification_metrics(y_test, logistic_scores),
        ),
        ModelResult(
            name=f"Tree model with {resampling_method}",
            estimator=tree,
            scores=tree_scores,
            metrics=classification_metrics(y_test, tree_scores),
        ),
    ]
    return results, resampling_method


def model_metrics_frame(results: list[ModelResult]) -> pd.DataFrame:
    """Convert model metrics to a tidy DataFrame."""
    rows = []
    for result in results:
        rows.append({"model": result.name, **result.metrics})
    return pd.DataFrame(rows).sort_values("average_precision_pr_auc", ascending=False)


def choose_best_model(results: list[ModelResult]) -> ModelResult:
    """Choose the model with the best PR-AUC on the holdout set."""
    return max(results, key=lambda result: result.metrics["average_precision_pr_auc"])


def precision_recall_points(y_true: Iterable[int], scores: Iterable[float]) -> pd.DataFrame:
    """Return precision-recall curve points for plotting."""
    precision, recall, thresholds = precision_recall_curve(y_true, scores)
    threshold_series = np.append(thresholds, 1.0)
    return pd.DataFrame(
        {
            "precision": precision,
            "recall": recall,
            "threshold": threshold_series,
        }
    )


def threshold_candidates(scores: Iterable[float]) -> np.ndarray:
    """Business-readable thresholds based on alert-rate quantiles plus 0.5."""
    score_arr = np.asarray(list(scores), dtype=float)
    alert_rates = np.array(
        [0.0005, 0.001, 0.002, 0.005, 0.01, 0.015, 0.02, 0.03, 0.05, 0.08, 0.10]
    )
    quantile_thresholds = np.quantile(score_arr, 1 - alert_rates)
    fixed_thresholds = np.array([0.05, 0.10, 0.25, 0.50, 0.75, 0.90])
    return np.unique(np.clip(np.concatenate([quantile_thresholds, fixed_thresholds]), 0, 1))
