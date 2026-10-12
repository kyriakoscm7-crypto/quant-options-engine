# Quant Options Engine

A Python-based quantitative finance application for pricing options, calculating risk sensitivities, estimating implied volatility, and visualizing volatility patterns using real market data.

Built with a modular architecture featuring a pricing engine, market-data integration, REST API, interactive visualizations, automated testing, and Docker containerization.

## Features

### Options Pricing
- Black-Scholes-Merton pricing for European call and put options.
- Support for continuous dividend yields.
- Analytical option Greeks for risk sensitivity analysis.
- Input validation and handling of important pricing edge cases.

### Implied Volatility
- Numerical implied volatility estimation from observed option prices.
- Arbitrage-bound validation and numerical safeguards.

### Market Data
- Yahoo Finance integration for retrieving SPY option-chain data.
- Bid-ask quote filtering to reduce the impact of poor-quality observations.
- Multiple-expiration option-chain retrieval.
- Implied volatility calculations across strikes and maturities.

### Interactive Visualizations
- 2D implied volatility smile using Plotly.
- Interactive 3D implied volatility scatter visualization across moneyness and time to expiration.

### API
- FastAPI REST endpoints for option pricing, Greeks, implied volatility, and market-data retrieval.
- Interactive Swagger API documentation.

### Engineering
- Modular Python project structure.
- 61 automated tests using pytest.
- Dockerized FastAPI application.
- GitHub Actions continuous integration for automated testing and Docker builds.

## Technology Stack

| Category | Technologies |
|---|---|
| Programming | Python 3.11 |
| Numerical Computing | NumPy, SciPy |
| Data Processing | pandas |
| Market Data | yfinance |
| API | FastAPI, Uvicorn |
| Visualization | Plotly |
| Testing | pytest |
| Containerization | Docker |
| Continuous Integration | GitHub Actions |

## Project Structure

```text
quant-options-engine/
├── app/
│   ├── api/
│   │   └── main.py
│   ├── market_data/
│   │   ├── yahoo_client.py
│   │   └── multi_expiration.py
│   ├── pricing/
│   │   ├── black_scholes.py
│   │   └── implied_volatility.py
│   └── visualization/
│       ├── volatility_smile.py
│       └── volatility_surface_3d.py
├── tests/
├── .github/
│   └── workflows/
│       └── ci.yml
├── Dockerfile
├── requirements.txt
└── README.md
```

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/kyriakoscm7-crypto/quant-options-engine.git
cd quant-options-engine
```

### 2. Create a virtual environment

```bash
python3.11 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

## Running the API

Start the FastAPI application:

```bash
uvicorn app.api.main:app --reload
```

Open the interactive API documentation:

`http://127.0.0.1:8000/docs`

## Running with Docker

Build the Docker image:

```bash
docker build -t quant-options-engine .
```

Start the container:

```bash
docker run --rm -p 8000:8000 quant-options-engine
```

The API documentation will be available at:

`http://127.0.0.1:8000/docs`

## Example: Black-Scholes Pricing

For a European option with:

| Parameter | Value |
|---|---|
| Underlying price | 100 |
| Strike price | 100 |
| Time to expiration | 1 year |
| Risk-free rate | 5% |
| Volatility | 20% |
| Dividend yield | 0% |

The Black-Scholes-Merton model produces approximately:

| Output | Value |
|---|---|
| Call price | 10.4506 |
| Put price | 5.5735 |
| Call delta | 0.6368 |
| Put delta | -0.3632 |

## Running Tests

Run the automated test suite:

```bash
python -m pytest tests/ -q
```

The project currently contains 61 passing tests.

GitHub Actions automatically executes the test suite and verifies the Docker build when code is pushed to the repository.

## Model Assumptions and Limitations

- Black-Scholes-Merton assumes lognormally distributed underlying prices and constant volatility and interest rates.
- The analytical pricing model is designed for European-style options.
- SPY options are American-style, so Black-Scholes-Merton values and implied volatilities are approximations, particularly when early exercise is relevant.
- Market-data retrieval uses Yahoo Finance through the unofficial `yfinance` interface.
- Historical trade timestamps and underlying price timestamps do not establish real-time quote freshness.
- The current market-data workflow assumes a zero continuous dividend yield when estimating implied volatility.
- The 3D visualization displays observed implied volatility points rather than an interpolated, arbitrage-free volatility surface.

## Future Improvements

- Incorporate dividend-yield estimates into market-data implied volatility calculations.
- Add American-style option pricing methods.
- Improve volatility outlier detection and quote-quality controls.
- Introduce volatility-surface interpolation and calibration.
- Deploy the API to a cloud platform.
- Add monitoring, structured logging, and performance benchmarks.

## Disclaimer

This project is intended for educational, research, and portfolio demonstration purposes. It is not financial advice or a production trading system.