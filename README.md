# Quant Options Engine

[![Quant Options Engine CI](https://github.com/kyriakoscm7-crypto/quant-options-engine/actions/workflows/ci.yml/badge.svg)](https://github.com/kyriakoscm7-crypto/quant-options-engine/actions/workflows/ci.yml)

A Python-based quantitative finance application for pricing options, calculating risk sensitivities, estimating implied volatility, and visualizing volatility patterns using real market data.

Built with a modular architecture featuring a pricing engine, market-data integration, REST API, interactive visualizations, automated testing, Docker containerization, and continuous integration.

## Features

### Options Pricing

- Black-Scholes-Merton pricing for European call and put options.
- Support for continuous dividend yields.
- Analytical option Greeks for risk sensitivity analysis.
- Input validation and handling of important pricing edge cases.

### Implied Volatility

- Numerical implied volatility estimation from observed option prices.
- Arbitrage-bound validation and numerical safeguards.
- Implied volatility calculations using filtered market-data observations.

### Market Data

- Yahoo Finance integration for retrieving SPY option-chain data.
- Bid-ask quote filtering to reduce the impact of poor-quality observations.
- Multiple-expiration option-chain retrieval.
- Implied volatility calculations across strikes and maturities.
- Tracking of underlying-price and option-trade timestamps.

### REST API

- FastAPI endpoints for option pricing, Greeks, implied volatility, and market-data retrieval.
- Interactive Swagger API documentation.
- JSON request and response handling.
- Automated API endpoint testing.

### Software Engineering

- Modular Python project architecture.
- 61 automated tests using pytest.
- Dockerized FastAPI application.
- GitHub Actions continuous integration.
- Automated testing and Docker image builds on every push and pull request.

## Visualizations

### 2D Implied Volatility Smile

The volatility smile displays implied volatility across option strikes using filtered SPY market-data observations.

This visualization helps illustrate how implied volatility varies across different strike prices for a selected expiration.

![SPY Implied Volatility Smile](docs/images/volatility_smile.png)

### 3D Implied Volatility Visualization

The interactive 3D visualization displays observed implied volatility across:

- **Moneyness:** Strike price relative to the underlying price.
- **Time to expiration:** Remaining days until option expiration.
- **Implied volatility:** Volatility estimated from observed option prices.

Unlike an interpolated volatility surface, this visualization represents individual market-data observations.

The two screenshots below show the same type of visualization from different viewing angles.

**View 1 — Implied Volatility Across Moneyness and Maturity**

![SPY Implied Volatility - 3D View 1](docs/images/volatility_surface_3d.png)

**View 2 — Alternative Perspective**

![SPY Implied Volatility - 3D View 2](docs/images/volatility_surface_3d_2.png)

## Technology Stack

| Category | Technologies |
|---|---|
| Programming Language | Python 3.11 |
| Numerical Computing | NumPy, SciPy |
| Data Processing | pandas |
| Market Data | yfinance |
| REST API | FastAPI, Uvicorn |
| Visualization | Plotly |
| Automated Testing | pytest |
| Containerization | Docker |
| Version Control | Git, GitHub |
| Continuous Integration | GitHub Actions |

## Project Architecture

The application is organized into independent components:

1. **Pricing Engine:** Implements Black-Scholes-Merton pricing, analytical Greeks, and implied volatility estimation.
2. **Market-Data Layer:** Retrieves option-chain data, validates quotes, and prepares observations for analysis.
3. **API Layer:** Exposes pricing, Greeks, implied volatility, and market-data functionality through FastAPI.
4. **Visualization Layer:** Generates interactive Plotly visualizations of implied volatility.
5. **Testing and Infrastructure:** Provides automated tests, Docker containerization, and GitHub Actions CI.

## Project Structure

```text
quant-options-engine/
├── .github/
│   └── workflows/
│       └── ci.yml
│
├── app/
│   ├── __init__.py
│   │
│   ├── api/
│   │   ├── __init__.py
│   │   └── main.py
│   │
│   ├── market_data/
│   │   ├── __init__.py
│   │   ├── yahoo_client.py
│   │   └── multi_expiration.py
│   │
│   ├── pricing/
│   │   ├── __init__.py
│   │   ├── black_scholes.py
│   │   └── implied_volatility.py
│   │
│   └── visualization/
│       ├── __init__.py
│       ├── volatility_smile.py
│       └── volatility_surface_3d.py
│
├── docs/
│   └── images/
│       ├── volatility_smile.png
│       ├── volatility_surface_3d.png
│       └── volatility_surface_3d_2.png
│
├── tests/
│   ├── test_api.py
│   ├── test_black_scholes.py
│   ├── test_implied_volatility.py
│   ├── test_market_data.py
│   ├── test_multi_expiration.py
│   └── test_volatility_surface.py
│
├── .dockerignore
├── .gitignore
├── Dockerfile
├── README.md
├── requirements.txt
└── volatility_surface.py
```

## Installation

### Prerequisites

- Python 3.11
- Git
- Docker (optional, for containerized execution)

### 1. Clone the Repository

```bash
git clone https://github.com/kyriakoscm7-crypto/quant-options-engine.git
cd quant-options-engine
```

### 2. Create a Virtual Environment

On macOS or Linux:

```bash
python3.11 -m venv .venv
source .venv/bin/activate
```

On Windows:

```powershell
py -3.11 -m venv .venv
.venv\Scripts\Activate.ps1
```

### 3. Install Dependencies

```bash
python -m pip install -r requirements.txt
```

## Running the API

Start the FastAPI application:

```bash
uvicorn app.api.main:app --reload
```

Open the interactive API documentation:

`http://127.0.0.1:8000/docs`

The Swagger interface allows users to explore available endpoints, submit requests, and inspect responses.

## Running with Docker

The application can also run inside a Docker container without requiring a local Python installation.

### 1. Build the Docker Image

```bash
docker build -t quant-options-engine .
```

### 2. Start the Container

```bash
docker run --rm -p 8000:8000 quant-options-engine
```

### 3. Access the API

Open:

`http://127.0.0.1:8000/docs`

The FastAPI application is now running inside the Docker container.

To stop the container, press `Ctrl + C` in the terminal.

## Example: Black-Scholes-Merton Pricing

Consider a European option with the following parameters:

| Parameter | Symbol | Value |
|---|---|---|
| Underlying price | S | 100 |
| Strike price | K | 100 |
| Time to expiration | T | 1 year |
| Risk-free interest rate | r | 5% |
| Volatility | σ | 20% |
| Continuous dividend yield | q | 0% |

The Black-Scholes-Merton model produces approximately:

| Output | Value |
|---|---|
| European call price | 10.4506 |
| European put price | 5.5735 |
| Call delta | 0.6368 |
| Put delta | -0.3632 |

### Example API Request

Using the interactive Swagger documentation, submit the following JSON to the Greeks endpoint:

**POST `/api/v1/options/greeks`**

```json
{
  "S": 100,
  "K": 100,
  "T": 1,
  "r": 0.05,
  "sigma": 0.2,
  "q": 0
}
```

The API returns calculated option prices and risk sensitivities.

## Automated Testing

The project includes 61 automated tests covering the application's major components.

The test suite checks:

- Black-Scholes-Merton pricing calculations.
- Analytical Greeks and numerical edge cases.
- Implied volatility estimation.
- Input validation and error handling.
- FastAPI endpoints.
- Market-data processing and filtering.
- Multiple-expiration data retrieval.
- Volatility visualization data preparation.

### Run Tests Locally

```bash
python -m pytest tests/ -q
```

Latest verified local result:

```text
61 passed, 1 warning
```

The warning originates from a dependency deprecation notice and does not indicate a failed test.

## Continuous Integration

The project uses GitHub Actions to automatically validate code changes.

The workflow is defined in:

```text
.github/workflows/ci.yml
```

Every push and pull request triggers two jobs.

### Python Tests

1. Check out the repository.
2. Configure Python 3.11.
3. Install project dependencies.
4. Execute the automated pytest suite.

### Docker Build

1. Check out the repository.
2. Build the application's Docker image.
3. Verify that the container image can be constructed successfully.

Both jobs have been successfully executed through GitHub Actions.

The workflow status is displayed at the top of this README.

## Quantitative Finance Concepts

This project demonstrates several concepts commonly used in derivatives pricing and quantitative finance.

### Black-Scholes-Merton Model

The Black-Scholes-Merton framework estimates theoretical European option prices using the underlying price, strike price, time to expiration, risk-free interest rate, volatility, and dividend yield.

### Option Greeks

Option Greeks measure how an option's theoretical value changes when market inputs change.

- **Delta:** Sensitivity to changes in the underlying price.
- **Gamma:** Sensitivity of delta to changes in the underlying price.
- **Vega:** Sensitivity to changes in implied volatility.
- **Theta:** Sensitivity to the passage of time.
- **Rho:** Sensitivity to changes in the risk-free interest rate.

### Implied Volatility

Implied volatility is the volatility parameter that makes a pricing model's theoretical value match an observed option price.

Because implied volatility generally cannot be isolated algebraically in the Black-Scholes-Merton formula, numerical root-finding methods are used.

### Volatility Smile

A volatility smile describes how implied volatility varies across strike prices for options sharing the same expiration.

### Volatility Across Maturities

Examining implied volatility across different expiration dates helps illustrate the term structure of implied volatility.

The project's 3D visualization combines strike-relative moneyness, time to expiration, and implied volatility into a single interactive chart.

## Model Assumptions and Limitations

This project is intended to demonstrate quantitative modeling and software engineering techniques. Several limitations should be considered when interpreting its results.

### Black-Scholes-Merton Assumptions

- The underlying asset follows a geometric Brownian motion.
- Volatility and the risk-free interest rate are assumed constant over the option's life.
- The model assumes continuous trading and frictionless markets.
- The analytical formulas are designed for European-style exercise.

### American-Style SPY Options

SPY options are American-style and may be exercised before expiration.

The current implementation uses European Black-Scholes-Merton formulas when estimating prices and implied volatility.

Consequently, these estimates are approximations, especially when early exercise is economically relevant.

### Dividend Yield

The pricing engine supports continuous dividend yields.

However, the current market-data implied volatility workflow assumes a zero continuous dividend yield.

This can introduce differences between model estimates and observed SPY option prices.

### Market-Data Quality

- Yahoo Finance data is retrieved using the unofficial `yfinance` interface.
- Option quotes may be delayed, stale, incomplete, or inconsistent.
- Bid-ask filtering improves quote selection but does not guarantee data quality.
- Option last-trade timestamps and underlying daily-price timestamps do not establish quote freshness.
- Market-data availability depends on the external provider.

### Volatility Visualization

The 3D chart displays observed implied volatility estimates as individual points.

It is not a calibrated, interpolated, or arbitrage-free volatility surface.

Observed volatility patterns may contain outliers caused by market-data limitations or pricing-model assumptions.

## Future Improvements

Potential future enhancements include:

- Incorporating estimated dividend yields into market-data implied volatility calculations.
- Implementing American-style option pricing models.
- Improving quote-quality filters and volatility outlier detection.
- Developing interpolated and calibrated volatility surfaces.
- Adding additional underlying assets and option types.
- Deploying the FastAPI application to a cloud platform.
- Adding structured logging and application monitoring.
- Implementing performance benchmarks and numerical optimization.
- Introducing more advanced derivatives pricing models.

## Disclaimer

This project is intended for educational, research, and software engineering portfolio purposes.

It is not financial advice, an investment recommendation, or a production trading system.

Theoretical model outputs and market-data-derived estimates should not be relied upon for live trading decisions.