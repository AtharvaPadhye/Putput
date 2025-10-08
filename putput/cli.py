"""Command-line interface for generating SPY put-sell analytics."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from . import analysis, data, visualization


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--spy-period",
        default="10y",
        help="Historical lookback period to request from Yahoo Finance (e.g. '5y', '1y').",
    )
    parser.add_argument(
        "--days-to-expiration",
        type=int,
        default=30,
        help="Days to expiration used for the theoretical option pricing.",
    )
    parser.add_argument(
        "--strike-distance",
        type=float,
        default=0.05,
        help="Fractional distance below the spot price for the strike (0.05 == 5% OTM).",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("artifacts"),
        help="Directory where plots and tables will be saved.",
    )
    return parser


def run(args: argparse.Namespace) -> None:
    cfg = data.MarketDataConfig(spy_period=args.spy_period)
    price_history = data.fetch_spy_history(cfg)
    risk_free = data.fetch_risk_free_rate(cfg)
    frame = data.prepare_analysis_frame(price_history, risk_free)

    premium_cfg = analysis.PremiumConfig(
        days_to_expiration=args.days_to_expiration,
        strike_distance=args.strike_distance,
    )
    enriched = analysis.estimate_put_premiums(frame, premium_cfg)

    output_dir: Path = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    visualization.plot_premium_yield_timeseries(
        enriched,
        output_path=output_dir / "premium_yield_timeseries.png",
    )
    visualization.plot_seasonality_heatmap(
        enriched,
        output_path=output_dir / "premium_seasonality_heatmap.png",
    )

    top_opportunities = (
        enriched.sort_values("annualized_premium_yield", ascending=False)
        .head(25)
        .loc[:, [
            "close",
            "strike",
            "estimated_premium",
            "premium_yield",
            "annualized_premium_yield",
            "volatility",
        ]]
    )
    top_path = output_dir / "top_put_sell_windows.csv"
    top_opportunities.to_csv(top_path, float_format="%.6f")

    def _to_float(value: float) -> float:
        if isinstance(value, (np.floating, np.integer)):
            return float(value)
        return float(value)

    summary = {
        "observations": len(enriched),
        "mean_annualized_yield": float(enriched["annualized_premium_yield"].mean()),
        "median_annualized_yield": float(enriched["annualized_premium_yield"].median()),
        "figures": {
            "timeseries": str(output_dir / "premium_yield_timeseries.png"),
            "seasonality": str(output_dir / "premium_seasonality_heatmap.png"),
        },
        "top_table": str(top_path),
    }
    if not top_opportunities.empty:
        summary["top_window"] = {
            key: _to_float(value)
            for key, value in top_opportunities.iloc[0].to_dict().items()
        }

    summary_path = output_dir / "summary.json"
    summary_path.write_text(json.dumps(summary, indent=2))

    print("Artifacts written to", output_dir.resolve())
    print(summary_path.read_text())


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    run(args)


if __name__ == "__main__":
    main()
