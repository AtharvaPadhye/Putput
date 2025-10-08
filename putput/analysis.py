"""Analytical helpers for estimating cash-secured put premiums."""

from __future__ import annotations

import math
from dataclasses import dataclass
from statistics import mean, median
from typing import Dict, Iterable, List, Optional

TRADING_DAYS_PER_YEAR = 252


@dataclass
class PremiumConfig:
    """Parameters controlling the premium estimation."""

    days_to_expiration: int = 30
    strike_distance: float = 0.05  # 5% below spot


def _rolling_std(values: Iterable[float], window: int) -> List[Optional[float]]:
    """Compute a simple rolling standard deviation."""

    buffer: List[float] = []
    results: List[Optional[float]] = []
    values_list = list(values)

    for value in values_list:
        buffer.append(value)
        if len(buffer) > window:
            buffer.pop(0)

        if len(buffer) < window:
            results.append(None)
            continue

        avg = sum(buffer) / len(buffer)
        if len(buffer) == 1:
            variance = 0.0
        else:
            variance = sum((x - avg) ** 2 for x in buffer) / (len(buffer) - 1)
        results.append(math.sqrt(variance))

    return results


def annualized_volatility(returns: Iterable[float], window: int = 21) -> List[Optional[float]]:
    """Compute annualized volatility from daily returns."""

    rolling = _rolling_std(returns, window=window)
    return [value * math.sqrt(TRADING_DAYS_PER_YEAR) if value is not None else None for value in rolling]


def _norm_cdf(x: float) -> float:
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def black_scholes_put(
    spot: float,
    strike: float,
    time: float,
    rate: float,
    volatility: float,
) -> float:
    """Black-Scholes price for a European put option."""

    if spot <= 0 or strike <= 0 or time <= 0 or volatility <= 0:
        return math.nan

    sqrt_time = math.sqrt(time)
    d1 = (math.log(spot / strike) + (rate + 0.5 * volatility**2) * time) / (volatility * sqrt_time)
    d2 = d1 - volatility * sqrt_time

    return strike * math.exp(-rate * time) * _norm_cdf(-d2) - spot * _norm_cdf(-d1)


def estimate_put_premiums(
    rows: List[Dict[str, object]],
    config: Optional[PremiumConfig] = None,
) -> List[Dict[str, object]]:
    """Estimate put premiums and derived yields for each observation."""

    config = config or PremiumConfig()
    time = config.days_to_expiration / TRADING_DAYS_PER_YEAR
    returns = [row["return"] for row in rows]
    volatilities = annualized_volatility(returns, window=21)

    enriched: List[Dict[str, object]] = []
    for row, vol in zip(rows, volatilities):
        if vol is None or vol <= 0:
            continue

        strike = row["close"] * (1 - config.strike_distance)
        premium = black_scholes_put(
            spot=row["close"],
            strike=strike,
            time=time,
            rate=row["risk_free_rate"],
            volatility=vol,
        )

        if math.isnan(premium):
            continue

        premium_yield = premium / strike
        annualized_yield = premium_yield * (TRADING_DAYS_PER_YEAR / config.days_to_expiration)

        enriched_row = dict(row)
        enriched_row.update(
            {
                "volatility": vol,
                "estimated_premium": premium,
                "premium_yield": premium_yield,
                "annualized_premium_yield": annualized_yield,
                "strike": strike,
                "days_to_expiration": config.days_to_expiration,
            }
        )
        enriched.append(enriched_row)

    return enriched


def summarize_yields(rows: Iterable[Dict[str, object]]) -> Dict[str, float]:
    """Compute summary statistics for annualized yields."""

    values = [row["annualized_premium_yield"] for row in rows if not math.isnan(row["annualized_premium_yield"])]
    if not values:
        return {"mean": math.nan, "median": math.nan}
    return {"mean": mean(values), "median": median(values)}

