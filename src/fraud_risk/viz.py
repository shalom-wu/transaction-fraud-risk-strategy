"""Presentation-quality chart helpers."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
import pandas as pd
import seaborn as sns
from sklearn.metrics import precision_recall_curve


TOKENS = {
    "surface": "#FCFCFD",
    "panel": "#FFFFFF",
    "ink": "#1F2430",
    "muted": "#6F768A",
    "grid": "#E6E8F0",
    "axis": "#D7DBE7",
}

COLORS = {
    "blue": "#A3BEFA",
    "blue_dark": "#2E4780",
    "gold": "#FFE15B",
    "gold_dark": "#736422",
    "orange": "#F0986E",
    "orange_dark": "#804126",
    "olive": "#A3D576",
    "olive_dark": "#386411",
    "pink": "#F390CA",
    "pink_dark": "#8A3A6F",
    "neutral": "#C5CAD3",
    "neutral_dark": "#464C55",
}


def use_chart_theme() -> None:
    sns.set_theme(
        style="whitegrid",
        rc={
            "figure.facecolor": TOKENS["surface"],
            "axes.facecolor": TOKENS["panel"],
            "axes.edgecolor": TOKENS["axis"],
            "axes.labelcolor": TOKENS["ink"],
            "grid.color": TOKENS["grid"],
            "grid.linewidth": 0.8,
            "font.family": "sans-serif",
            "font.sans-serif": ["Aptos", "Inter", "Segoe UI", "DejaVu Sans", "Arial"],
        },
    )


def _finish(fig: plt.Figure, path: str | Path) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(output, dpi=180, bbox_inches="tight", facecolor=TOKENS["surface"])
    plt.close(fig)


def save_class_imbalance_chart(balance: pd.DataFrame, path: str | Path) -> None:
    use_chart_theme()
    fig, ax = plt.subplots(figsize=(8, 4.8))
    palette = {"Legitimate": COLORS["blue"], "Fraud": COLORS["orange"]}
    sns.barplot(data=balance, x="label", y="transactions", hue="label", palette=palette, legend=False, ax=ax)
    ax.set_yscale("log")
    ax.set_xlabel("")
    ax.set_ylabel("Transactions, log scale")
    ax.set_title(
        "Severe class imbalance\nFraud is a tiny share of transactions, so accuracy would reward doing almost nothing.",
        loc="left",
        fontsize=12,
        weight="semibold",
        pad=14,
    )
    for patch, (_, row) in zip(ax.patches, balance.iterrows()):
        ax.text(
            patch.get_x() + patch.get_width() / 2,
            patch.get_height(),
            f"{row['transactions']:,.0f}\n{row['share']:.3%}",
            ha="center",
            va="bottom",
            fontsize=9,
            color=TOKENS["ink"],
        )
    _finish(fig, path)


def save_amount_distribution_chart(df: pd.DataFrame, path: str | Path) -> None:
    use_chart_theme()
    fig, ax = plt.subplots(figsize=(8.5, 5.0))
    plot_df = df.copy()
    plot_df["label"] = np.where(plot_df["Class"].eq(1), "Fraud", "Legitimate")
    if len(plot_df) > 50_000:
        legitimate = plot_df[plot_df["Class"].eq(0)].sample(40_000, random_state=42)
        fraud = plot_df[plot_df["Class"].eq(1)]
        plot_df = pd.concat([legitimate, fraud], ignore_index=True)
    palette = {"Legitimate": COLORS["blue"], "Fraud": COLORS["orange"]}
    sns.boxplot(
        data=plot_df,
        x="label",
        y="amount_log1p",
        hue="label",
        palette=palette,
        legend=False,
        ax=ax,
        showfliers=False,
    )
    ax.set_xlabel("")
    ax.set_ylabel("Log(Amount + 1)")
    ax.set_title(
        "Fraud and legitimate transactions have different amount profiles\nLog scale reduces the influence of extreme amounts while preserving distribution shape.",
        loc="left",
        fontsize=12,
        weight="semibold",
        pad=14,
    )
    _finish(fig, path)


def save_hourly_pattern_chart(hourly: pd.DataFrame, path: str | Path) -> None:
    use_chart_theme()
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.bar(
        hourly["relative_hour"],
        hourly["fraud_rate"],
        color=COLORS["gold"],
        edgecolor=COLORS["gold_dark"],
        linewidth=0.8,
    )
    ax.yaxis.set_major_formatter(mticker.PercentFormatter(1))
    ax.set_xlabel("Relative hour within the dataset day")
    ax.set_ylabel("Fraud rate")
    ax.set_title(
        "Fraud rate by relative hour\nElapsed-hour pattern only: Time is seconds from the first transaction.",
        loc="left",
        fontsize=12,
        weight="semibold",
        pad=14,
    )
    ax.set_xticks(range(0, 24, 2))
    _finish(fig, path)


def save_precision_recall_curve(y_true, scores, path: str | Path) -> None:
    use_chart_theme()
    precision, recall, _ = precision_recall_curve(y_true, scores)
    fig, ax = plt.subplots(figsize=(7.5, 5))
    ax.plot(recall, precision, color=COLORS["blue_dark"], linewidth=1.6)
    ax.set_xlabel("Recall")
    ax.set_ylabel("Precision")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.set_title(
        "Precision-recall curve\nPR-AUC is the main ranking metric because fraud is less than 1% of the data.",
        loc="left",
        fontsize=12,
        weight="semibold",
        pad=14,
    )
    _finish(fig, path)


def save_threshold_tradeoff_chart(thresholds: pd.DataFrame, path: str | Path) -> None:
    use_chart_theme()
    plot_df = thresholds.sort_values("alert_rate")
    fig, ax = plt.subplots(figsize=(8.5, 5))
    ax.plot(plot_df["alert_rate"], plot_df["precision"], marker="o", color=COLORS["blue_dark"], label="Precision")
    ax.plot(plot_df["alert_rate"], plot_df["recall"], marker="o", color=COLORS["orange_dark"], label="Recall")
    ax.xaxis.set_major_formatter(mticker.PercentFormatter(1))
    ax.yaxis.set_major_formatter(mticker.PercentFormatter(1))
    ax.set_xlabel("Share of transactions flagged")
    ax.set_ylabel("Metric value")
    ax.set_title(
        "Decision threshold moves precision and recall in opposite directions\nLower thresholds catch more fraud but create more false-positive customer friction.",
        loc="left",
        fontsize=12,
        weight="semibold",
        pad=14,
    )
    ax.legend(loc="center right", frameon=False)
    _finish(fig, path)


def save_cost_curve_chart(thresholds: pd.DataFrame, path: str | Path) -> None:
    use_chart_theme()
    plot_df = thresholds.sort_values("alert_rate")
    fig, ax = plt.subplots(figsize=(8.5, 5))
    colors = np.where(plot_df["net_savings_per_100k"] >= 0, COLORS["olive"], COLORS["orange"])
    ax.bar(
        plot_df["alert_rate"],
        plot_df["net_savings_per_100k"],
        width=0.003,
        color=colors,
        edgecolor=COLORS["neutral_dark"],
        linewidth=0.5,
    )
    ax.axhline(0, color=TOKENS["ink"], linewidth=1)
    ax.xaxis.set_major_formatter(mticker.PercentFormatter(1))
    ax.yaxis.set_major_formatter(mticker.StrMethodFormatter("${x:,.0f}"))
    ax.set_xlabel("Share of transactions flagged")
    ax.set_ylabel("Net savings per 100k transactions")
    ax.set_title(
        "The best threshold is an economic decision\nCost combines missed fraud, manual review, and false-positive friction under stated assumptions.",
        loc="left",
        fontsize=12,
        weight="semibold",
        pad=14,
    )
    _finish(fig, path)
