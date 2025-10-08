"""Data acquisition utilities for SPY option analysis."""

from dataclasses import dataclass
from typing import Optional

import numpy as np
import pandas as pd
import yfinance as yf


@dataclass
class MarketDataConfig:
    """Configuration for downloading market data."""

    spy_period: str = "10y"
    spy_interval: str = "1d"
    risk_free_symbol: str = "^IRX"  # 13-week treasury bill yield
    risk_free_period: str = "10y"
    risk_free_interval: str = "1d"


def fetch_spy_history(config: Optional[MarketDataConfig] = None) -> pd.DataFrame:
    """Download historical SPY price data using *yfinance*."""

    config = config or MarketDataConfig()
    spy = yf.Ticker("SPY")
    history = spy.history(period=config.spy_period, interval=config.spy_interval)
    if history.empty:
        raise RuntimeError("Failed to download SPY historical data.")
    history.index = pd.to_datetime(history.index)
    return history


def fetch_risk_free_rate(config: Optional[MarketDataConfig] = None) -> pd.Series:
    """Fetch the risk-free rate series from the 13-week T-bill yield."""

    config = config or MarketDataConfig()
    irx = yf.download(
        config.risk_free_symbol,
        period=config.risk_free_period,
        interval=config.risk_free_interval,
        progress=False,
    )
    if irx.empty:
        raise RuntimeError("Failed to download risk-free rate data.")

    rate = irx["Adj Close"].rename("risk_free_rate")
    rate.index = pd.to_datetime(rate.index)
    # Convert quoted yield (in percent) to decimal risk-free rate.
    rate = rate / 100.0
    return rate


def prepare_analysis_frame(
    price_history: pd.DataFrame,
    risk_free_rate: pd.Series,
) -> pd.DataFrame:
    """Combine price and risk-free data into a single analysis-ready frame."""

    df = price_history[["Close"]].rename(columns={"Close": "close"}).copy()
    df["return"] = np.log(df["close"]).diff()
    df["risk_free_rate"] = risk_free_rate.reindex(df.index).ffill()
    return df.dropna(subset=["risk_free_rate"]).dropna()
