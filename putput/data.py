"""Data acquisition utilities for SPY option analysis.

This module avoids external data sources so that the package can operate in
restricted environments (e.g. offline continuous integration).  It generates a
deterministic synthetic price history and risk-free rate series that resemble
realistic market dynamics.  The synthetic data is sufficient for exercising the
analytical pipeline end-to-end without relying on third-party APIs or
heavy-weight dependencies.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
import math
from typing import Dict, List, Sequence


TRADING_DAYS_PER_YEAR = 252


@dataclass(frozen=True)
class MarketDataPoint:
    """Synthetic daily market data for SPY."""

    date: date
    close: float


@dataclass(frozen=True)
class MarketDataConfig:
    """Configuration for generating market data."""

    spy_period: str = "10y"
    risk_free_period: str | None = None


def _parse_period(period: str) -> int:
    """Convert a period string like ``"1y"`` into trading days."""

    period = period.strip().lower()
    if not period.endswith("y"):
        raise ValueError(f"Unsupported period format: {period}")

    try:
        years = float(period[:-1])
    except ValueError as exc:  # pragma: no cover - defensive programming
        raise ValueError(f"Invalid year component in period: {period}") from exc

    return max(1, int(round(years * TRADING_DAYS_PER_YEAR)))


def _generate_trading_days(days: int) -> List[date]:
    """Generate a list of trading days ending on today."""

    results: List[date] = []
    current = date.today()
    while len(results) < days:
        if current.weekday() < 5:  # Monday-Friday
            results.append(current)
        current -= timedelta(days=1)
    results.reverse()
    return results


def _generate_price_path(dates: Sequence[date]) -> List[MarketDataPoint]:
    """Generate a deterministic yet realistic looking price path."""

    price_points: List[MarketDataPoint] = []
    price = 400.0
    for idx, current_date in enumerate(dates):
        if idx == 0:
            price_points.append(MarketDataPoint(date=current_date, close=round(price, 2)))
            continue

        drift = 0.0003
        seasonal = 0.012 * math.sin(idx / 18.0)
        medium_cycle = 0.008 * math.cos(idx / 6.0)
        high_freq = 0.01 * math.sin(idx / 2.3)
        log_return = drift + seasonal + medium_cycle + high_freq
        price *= math.exp(log_return)
        price_points.append(MarketDataPoint(date=current_date, close=round(price, 2)))
    return price_points


def _generate_risk_free_rates(dates: Sequence[date]) -> Dict[date, float]:
    """Create a smooth series of synthetic risk-free rates."""

    rates: Dict[date, float] = {}
    base_rate = 0.02
    for idx, current_date in enumerate(dates):
        seasonal = 0.0025 * math.sin(idx / 45.0)
        trend = 0.00005 * idx
        rate = max(0.0001, base_rate + seasonal + trend)
        rates[current_date] = round(rate, 6)
    return rates


def fetch_spy_history(config: MarketDataConfig | None = None) -> List[MarketDataPoint]:
    """Return synthetic SPY price history data."""

    config = config or MarketDataConfig()
    days = _parse_period(config.spy_period)
    dates = _generate_trading_days(days)
    return _generate_price_path(dates)


def fetch_risk_free_rate(config: MarketDataConfig | None = None) -> Dict[date, float]:
    """Return a synthetic risk-free rate series keyed by date."""

    config = config or MarketDataConfig()
    period = config.risk_free_period or config.spy_period
    days = _parse_period(period)
    dates = _generate_trading_days(days)
    return _generate_risk_free_rates(dates)


def prepare_analysis_frame(
    price_history: Sequence[MarketDataPoint],
    risk_free_rate: Dict[date, float],
) -> List[Dict[str, object]]:
    """Combine price and risk-free data into a list of observations."""

    results: List[Dict[str, object]] = []
    previous_close: float | None = None
    last_rate: float | None = None

    for point in price_history:
        rate = risk_free_rate.get(point.date, last_rate)
        if rate is None:
            continue

        if previous_close is None:
            previous_close = point.close
            last_rate = rate
            continue

        log_return = math.log(point.close / previous_close)
        results.append(
            {
                "date": point.date,
                "close": point.close,
                "return": log_return,
                "risk_free_rate": rate,
            }
        )
        previous_close = point.close
        last_rate = rate

    return results

