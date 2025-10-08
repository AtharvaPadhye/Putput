"""Command-line interface for generating SPY put-sell analytics."""
from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path

from . import analysis, data, visualization


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--spy-period",
        default="10y",
        help="Historical lookback period expressed as a year string (e.g. '5y', '1y').",
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

    figures: dict[str, str | None] = {}
    if visualization.HAS_MATPLOTLIB:
        timeseries_path = output_dir / "premium_yield_timeseries.png"
        visualization.plot_premium_yield_timeseries(
            enriched,
            output_path=timeseries_path,
        )
        seasonality_path = output_dir / "premium_seasonality_heatmap.png"
        visualization.plot_seasonality_heatmap(
            enriched,
            output_path=seasonality_path,
        )
        figures = {
            "timeseries": str(timeseries_path),
            "seasonality": str(seasonality_path),
        }
    else:
        print(
            "matplotlib is not available; skipping generation of visualization "
            "artifacts."
        )

    sorted_rows = sorted(
        enriched,
        key=lambda row: row["annualized_premium_yield"],
        reverse=True,
    )
    top_opportunities = sorted_rows[:25]
    top_path = output_dir / "top_put_sell_windows.csv"
    if top_opportunities:
        fieldnames = [
            "close",
            "strike",
            "estimated_premium",
            "premium_yield",
            "annualized_premium_yield",
            "volatility",
        ]
        with top_path.open("w", newline="") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for row in top_opportunities:
                writer.writerow({
                    key: f"{row[key]:.6f}" if isinstance(row[key], float) else row[key]
                    for key in fieldnames
                })
    else:
        top_path.write_text("close,strike,estimated_premium,premium_yield,annualized_premium_yield,volatility\n")

    yield_summary = analysis.summarize_yields(enriched)

    def _clean_float(value: float | None) -> float | None:
        if value is None or (isinstance(value, float) and math.isnan(value)):
            return None
        return value

    summary = {
        "observations": len(enriched),
        "mean_annualized_yield": _clean_float(yield_summary.get("mean")),
        "median_annualized_yield": _clean_float(yield_summary.get("median")),
        "figures": figures,
        "top_table": str(top_path),
    }
    if top_opportunities:
        summary["top_window"] = {
            key: float(top_opportunities[0][key])
            for key in [
                "close",
                "strike",
                "estimated_premium",
                "premium_yield",
                "annualized_premium_yield",
                "volatility",
            ]
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
