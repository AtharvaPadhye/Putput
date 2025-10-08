# Putput

Tools for analyzing cash-secured put (short put) opportunities on $SPY. The
project downloads historical pricing data, estimates theoretical option
premiums with a Black–Scholes model, and produces visual artifacts that help you
identify when premium yields have been most attractive.

## Features

- Automated download of SPY price history and the 13-week Treasury bill rate
  (used as the risk-free rate) via [Yahoo! Finance](https://finance.yahoo.com).
- Rolling volatility estimation and Black–Scholes pricing for 30-day, 5% OTM
  cash-secured puts (configurable).
- Visualization of the annualized premium yield over time as well as
  seasonality trends by month and weekday.
- Export of the top historical premium windows to CSV along with a JSON
  summary report of the analysis run.

## Getting Started

1. Create a virtual environment and install the dependencies:

   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

2. Execute the analysis CLI (this will download market data on first run):

   ```bash
   python -m putput.cli --spy-period 5y --days-to-expiration 30 --strike-distance 0.05
   ```

   Available options:

   | Flag | Description |
   | ---- | ----------- |
   | `--spy-period` | Lookback period passed to Yahoo Finance (e.g. `1y`, `5y`, `max`). |
   | `--days-to-expiration` | Days until expiration assumed when estimating the premium. |
   | `--strike-distance` | Fractional distance below spot for the strike (0.05 = 5% OTM). |
   | `--output-dir` | Folder where plots, tables, and the summary JSON will be saved. |

3. Inspect the generated artifacts in the specified `--output-dir` (defaults to
   `artifacts/`):

   - `premium_yield_timeseries.png`: Annualized premium yield over time.
   - `premium_seasonality_heatmap.png`: Average yield by month and weekday.
   - `top_put_sell_windows.csv`: Top 25 historical opportunities sorted by
     annualized yield.
   - `summary.json`: Machine-readable summary containing aggregate metrics and
     file paths to generated outputs.

## Notes & Caveats

- The premium estimates rely on a simplified Black–Scholes model using
  historical volatility; real option prices will differ.
- Yahoo Finance data can occasionally be rate limited or unavailable. Re-run the
  CLI if you encounter transient download failures.
- Consider adjusting the strike distance and expiration inputs to match your
  personal risk tolerance and preferred option selling cadence.

## License

This project is provided without warranty and for educational purposes only.
