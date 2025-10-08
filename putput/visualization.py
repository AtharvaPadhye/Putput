"""Visualization utilities for SPY cash-secured put analysis."""
from __future__ import annotations

from pathlib import Path
from typing import Optional

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
import numpy as np
import pandas as pd


DEFAULT_STYLE = "seaborn-v0_8"


def _setup_style(style: str = DEFAULT_STYLE) -> None:
    plt.style.use(style)


def plot_premium_yield_timeseries(
    df: pd.DataFrame,
    output_path: Optional[Path] = None,
    title: str = "Estimated SPY Put Premium Yield",
) -> plt.Figure:
    """Plot the estimated premium yield through time."""

    _setup_style()
    fig, ax = plt.subplots(figsize=(12, 6))
    df["annualized_premium_yield"].plot(ax=ax, color="#1f77b4", lw=1.5)
    ax.set_title(title)
    ax.set_ylabel("Annualized Yield (Black-Scholes Estimate)")
    ax.set_xlabel("Date")
    ax.grid(True, alpha=0.3)
    ax.yaxis.set_major_formatter(FuncFormatter(lambda x, pos: f"{x:.0%}"))
    ax.xaxis.set_major_locator(mdates.YearLocator(base=1))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    fig.autofmt_xdate()

    if output_path:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(output_path, bbox_inches="tight")
    return fig


def plot_seasonality_heatmap(
    df: pd.DataFrame,
    output_path: Optional[Path] = None,
    title: str = "Seasonality of SPY Put Premium Yields",
) -> plt.Figure:
    """Plot average yield by month and weekday to highlight seasonal patterns."""

    _setup_style()
    seasonality = (
        df.assign(
            month=lambda x: x.index.month,
            weekday=lambda x: x.index.day_name(),
        )
        .groupby(["month", "weekday"])  # type: ignore[arg-type]
        ["annualized_premium_yield"]
        .mean()
        .unstack()
        .reindex(columns=["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"])
        .reindex(index=range(1, 13))
    )
    month_labels = [
        "Jan",
        "Feb",
        "Mar",
        "Apr",
        "May",
        "Jun",
        "Jul",
        "Aug",
        "Sep",
        "Oct",
        "Nov",
        "Dec",
    ]

    fig, ax = plt.subplots(figsize=(10, 6))
    cax = ax.imshow(seasonality, aspect="auto", cmap="YlGnBu")
    ax.set_title(title)
    ax.set_xlabel("Weekday")
    ax.set_ylabel("Month")
    ax.set_xticks(range(len(seasonality.columns)))
    ax.set_xticklabels(seasonality.columns)
    ax.set_yticks(range(len(seasonality.index)))
    ax.set_yticklabels([month_labels[m - 1] for m in seasonality.index])

    for (i, j), val in np.ndenumerate(seasonality.values):
        ax.text(j, i, f"{val:.0%}", ha="center", va="center", color="black")

    fig.colorbar(cax, ax=ax, format=lambda x, _: f"{x:.0%}")

    if output_path:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(output_path, bbox_inches="tight")

    return fig
