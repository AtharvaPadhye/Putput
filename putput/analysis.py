"""Analytical helpers for estimating cash-secured put premiums."""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Optional

import pandas as pd
from scipy.stats import norm


TRADING_DAYS_PER_YEAR = 252


@dataclass
class PremiumConfig:
    """Parameters controlling the premium estimation."""

    days_to_expiration: int = 30
    strike_distance: float = 0.05  # 5% below spot


def annualized_volatility(returns: pd.Series, window: int = 21) -> pd.Series:
    """Compute annualized volatility from daily returns."""

    daily_vol = returns.rolling(window=window).std()
    return daily_vol * math.sqrt(TRADING_DAYS_PER_YEAR)


def black_scholes_put(
    spot: float,
    strike: float,
    time: float,
    rate: float,
    volatility: float,
) -> float:
    """Black-Scholes price for a European put option."""

    if spot <= 0 or strike <= 0 or time <= 0 or volatility <= 0:
        return float("nan")

    d1 = (math.log(spot / strike) + (rate + 0.5 * volatility**2) * time) / (
        volatility * math.sqrt(time)
    )
    d2 = d1 - volatility * math.sqrt(time)

    return strike * math.exp(-rate * time) * norm.cdf(-d2) - spot * norm.cdf(-d1)


def estimate_put_premiums(
    df: pd.DataFrame,
    config: Optional[PremiumConfig] = None,
) -> pd.DataFrame:
    """Estimate put premiums and derived yields for each row in ``df``."""

    config = config or PremiumConfig()
    data = df.copy()
    data["volatility"] = annualized_volatility(data["return"], window=21)

    time = config.days_to_expiration / TRADING_DAYS_PER_YEAR
    strikes = data["close"] * (1 - config.strike_distance)

    premiums = []
    for date, row in data.iterrows():
        spot = row["close"]
        strike = strikes.loc[date]
        rate = row["risk_free_rate"]
        vol = row["volatility"]
        premium = black_scholes_put(spot, strike, time, rate, vol) if pd.notna(vol) else float("nan")
        premiums.append(premium)

    data["estimated_premium"] = premiums
    data["premium_yield"] = data["estimated_premium"] / strikes
    data["annualized_premium_yield"] = data["premium_yield"] * (TRADING_DAYS_PER_YEAR / config.days_to_expiration)
    data["strike"] = strikes
    data["days_to_expiration"] = config.days_to_expiration
    return data.dropna(subset=["estimated_premium"])
