# Putput

Tools for analyzing cash-secured put (short put) opportunities on $SPY. The
project ships with a deterministic synthetic data generator so the full
analytics pipeline can run in offline or network-restricted environments. The
CLI estimates theoretical option premiums with a Black–Scholes model and
produces artifacts that highlight periods with attractive yields.

## Features

- Deterministic generation of SPY-like price history and risk-free rate series
  suitable for testing and CI environments.
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

2. Execute the analysis CLI (synthetic market data is generated on the fly):

   ```bash
   python -m putput.cli --spy-period 5y --days-to-expiration 30 --strike-distance 0.05
   ```

   Available options:

   | Flag | Description |
   | ---- | ----------- |
   | `--spy-period` | Lookback period expressed in years (e.g. `1y`, `5y`, `10y`). |
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
- The bundled synthetic data is tuned for testing workflows and does not
  represent actual market data. For production use, adapt the data module to
  source live prices and rates that match your brokerage.
- Consider adjusting the strike distance and expiration inputs to match your
  personal risk tolerance and preferred option selling cadence.

## License

This project is provided without warranty and for educational purposes only.
