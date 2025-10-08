"""Visualization utilities for SPY cash-secured put analysis."""

from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime
import math
from pathlib import Path
from statistics import mean
from typing import Iterable, Mapping, MutableMapping, Optional, Sequence, Tuple


try:  # pragma: no cover - optional dependency
    import matplotlib.dates as mdates
    import matplotlib.pyplot as plt
    from matplotlib.ticker import FuncFormatter
except Exception:  # pragma: no cover - matplotlib is optional
    mdates = None  # type: ignore[assignment]
    plt = None  # type: ignore[assignment]
    FuncFormatter = None  # type: ignore[assignment]
    HAS_MATPLOTLIB = False
else:  # pragma: no cover - simple flag assignment
    HAS_MATPLOTLIB = True


DEFAULT_STYLE = "seaborn-v0_8"


class MatplotlibUnavailableError(RuntimeError):
    """Raised when matplotlib is required but not installed."""


def _require_matplotlib() -> None:
    if not HAS_MATPLOTLIB:
        raise MatplotlibUnavailableError(
            "matplotlib is required for visualization features. "
            "Install it with `pip install matplotlib` to enable plotting support."
        )


def _setup_style(style: str = DEFAULT_STYLE) -> None:
    _require_matplotlib()
    assert plt is not None
    plt.style.use(style)


def _ensure_records(data: Iterable[Mapping[str, object]]) -> Sequence[Mapping[str, object]]:
    records = list(data)
    if not records:
        return []
    for record in records:
        if not isinstance(record, Mapping):
            raise TypeError("Records must be mappings containing 'date' and yield fields.")
    return records


def _coerce_date(value: object) -> datetime:
    if isinstance(value, datetime):
        return value
    if isinstance(value, date):
        return datetime.combine(value, datetime.min.time())
    if isinstance(value, str):
        return datetime.fromisoformat(value)
    raise TypeError(f"Unsupported date value: {value!r}")


def plot_premium_yield_timeseries(
    data: Iterable[Mapping[str, object]],
    output_path: Optional[Path] = None,
    title: str = "Estimated SPY Put Premium Yield",
) -> "plt.Figure":
    """Plot the estimated premium yield through time."""

    records = _ensure_records(data)
    if not records:
        raise ValueError("No data provided for plotting.")

    _setup_style()
    assert plt is not None
    assert mdates is not None
    assert FuncFormatter is not None

    dates = [_coerce_date(record["date"]) for record in records]
    yields = [float(record["annualized_premium_yield"]) for record in records]

    fig, ax = plt.subplots(figsize=(12, 6))
    ax.plot(dates, yields, color="#1f77b4", lw=1.5)
    ax.set_title(title)
    ax.set_ylabel("Annualized Yield (Black-Scholes Estimate)")
    ax.set_xlabel("Date")
    ax.grid(True, alpha=0.3)
    ax.yaxis.set_major_formatter(FuncFormatter(lambda x, _pos: f"{x:.0%}"))
    ax.xaxis.set_major_locator(mdates.YearLocator(base=1))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    fig.autofmt_xdate()

    if output_path:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(output_path, bbox_inches="tight")
    return fig


def _group_by_month_weekday(records: Sequence[Mapping[str, object]]) -> Tuple[Sequence[str], Sequence[str], list[list[float]]]:
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
    weekday_labels = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]

    grouped: MutableMapping[Tuple[int, int], list[float]] = defaultdict(list)
    for record in records:
        dt = _coerce_date(record["date"])
        yield_value = float(record["annualized_premium_yield"])
        grouped[(dt.month, dt.weekday())].append(yield_value)

    matrix: list[list[float]] = []
    for month in range(1, 13):
        row: list[float] = []
        for weekday in range(5):
            values = grouped.get((month, weekday))
            row.append(mean(values) if values else float("nan"))
        matrix.append(row)
    return month_labels, weekday_labels, matrix


def plot_seasonality_heatmap(
    data: Iterable[Mapping[str, object]],
    output_path: Optional[Path] = None,
    title: str = "Seasonality of SPY Put Premium Yields",
) -> "plt.Figure":
    """Plot average yield by month and weekday to highlight seasonal patterns."""

    records = _ensure_records(data)
    if not records:
        raise ValueError("No data provided for plotting.")

    _setup_style()
    assert plt is not None

    month_labels, weekday_labels, matrix = _group_by_month_weekday(records)

    fig, ax = plt.subplots(figsize=(10, 6))
    cax = ax.imshow(matrix, aspect="auto", cmap="YlGnBu")
    ax.set_title(title)
    ax.set_xlabel("Weekday")
    ax.set_ylabel("Month")
    ax.set_xticks(range(len(weekday_labels)))
    ax.set_xticklabels(weekday_labels)
    ax.set_yticks(range(len(month_labels)))
    ax.set_yticklabels(month_labels)

    for i, row in enumerate(matrix):
        for j, value in enumerate(row):
            if not math.isnan(value):  # type: ignore[name-defined]
                ax.text(j, i, f"{value:.0%}", ha="center", va="center", color="black")

    fig.colorbar(cax, ax=ax, format=lambda x, _: f"{x:.0%}")

    if output_path:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(output_path, bbox_inches="tight")

    return fig

