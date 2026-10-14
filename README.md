# Quant Intelligence — Quant Options Engine

[![Quant Options Engine CI](https://github.com/kyriakoscm7-crypto/quant-options-engine/actions/workflows/ci.yml/badge.svg)](https://github.com/kyriakoscm7-crypto/quant-options-engine/actions/workflows/ci.yml)

**A Python-based quantitative options analytics platform featuring Black-Scholes-Merton pricing, analytical Greeks, implied volatility estimation, real market-data integration, high-performance NumPy vectorization, portfolio risk analytics, and market scenario analysis.**

Built with a modular architecture, a FastAPI REST API, interactive Plotly volatility visualizations, automated testing, Docker, and GitHub Actions continuous integration.

The project emphasizes numerical correctness, reproducible performance measurements, and automated software quality assurance.

## Project Highlights

| Metric | Verified Local Result |
|---|---|
| Standalone Vectorized Pricing Throughput | **3.62 million options/second** |
| Standalone Pricing Speedup | **262.89× faster** |
| FastAPI Batch Pricing Throughput | **100,637 options/second** |
| FastAPI Batch Pricing Speedup | **50.19× faster** |
| Standalone Vectorized Greeks Throughput | **3.87 million options/second** |
| Standalone Pricing + Greeks Speedup | **944.76× faster** |
| FastAPI Batch Greeks Throughput | **42,463 options/second** |
| FastAPI Batch Greeks Speedup | **27.48× faster** |
| Portfolio Valuation Throughput | **297,201 positions/second** |
| Scenario Analysis Throughput | **1,408,945 scenario-position combinations/second** |
| Largest Scenario Benchmark | **1,000,000 combinations in 0.710 seconds** |
| Automated Tests | **638 passing** |
| Overall Code Coverage | **93%** |
| FastAPI Coverage | **99%** |
| Vectorized Pricing and Greeks Module Coverage | **100%** |
| Portfolio Analytics Coverage | **100%** |
| Scenario Analysis Coverage | **98%** |
| REST API Endpoints | **10** |
| Maximum Batch API Size | **10,000 contracts/request** |
| Continuous Integration | **GitHub Actions** |
| Containerization | **Docker** |
| API Framework | **FastAPI** |

Performance measurements were performed locally on an Apple Silicon MacBook Pro using Python 3.11.

The performance benchmarks measure different workflows:

1. Standalone scalar versus vectorized option pricing.
2. Individual versus batch FastAPI pricing requests.
3. Standalone scalar versus vectorized option pricing and Greeks.
4. Individual versus batch FastAPI Greeks requests.
5. Portfolio valuation and aggregate Greeks across different portfolio sizes.
6. Portfolio scenario analysis across different scenario-position workloads.

**These benchmarks measure different operations and overhead. Their speedup figures should not be interpreted as equivalent performance measurements.**

---


## Quant Intelligence — Interactive Research Dashboard

Quant Intelligence expands the original options-pricing engine into
an interactive stock, options, and quantitative research platform.

### Dashboard Features

**Stock Explorer**
- Historical and intraday stock charts.
- Technical indicators and momentum analysis.
- SPY market benchmarking.
- Financial news and potential catalysts.
- Company and ticker search.

**Risk Intelligence**
- Annualized historical volatility.
- Maximum drawdown.
- Historical Sharpe ratio.
- Beta relative to SPY.
- Market correlation.
- Contextual risk explanations.

**Strategy Research**
- Existing strategy research and analysis tools.

**Quant Discovery**
- SQLite company database.
- Mega-, large-, mid-, small-, micro-, and nano-cap classifications.
- Penny-stock classification.
- Company and ticker search.
- Experimental 5-day, 1-month, and 1-year research rankings.
- Exchange-listed symbol-directory ingestion.
- Resumable bulk company importer.
- Batch historical price downloads.
- Liquidity and data-quality eligibility checks.
- Precomputed ranking storage in SQLite.

### Development Snapshot — October 2026

| Component | Status |
|---|---|
| Stock Explorer | Implemented |
| Risk Intelligence | Implemented |
| Strategy Research | Implemented |
| Quant Discovery interface | Implemented |
| Company universe importer | Implemented |
| Resumable bulk importer | Implemented |
| Batch ranking pipeline | Implemented |
| Cached rankings connected to dashboard | Planned |
| Automated ranking refresh | Planned |
| Public deployment | Planned |

The local development database contained 359 company records,
with 237 companies ranked by the batch pipeline.

These are historical development counts, not live market totals.

The SQLite database is local and excluded from Git.

### Run the Dashboard

Activate your Python environment and start Streamlit:

    python -m streamlit run dashboard/main.py --server.port 8503

### Quant Discovery Backend

Import additional companies:

    python -m app.discovery.bulk_import --limit 250 --delay 1.0

Calculate technical research rankings:

    python -m app.discovery.ranking_pipeline --batch-size 40

The batch-ranking pipeline is implemented, but its cached results
have not yet been connected to the dashboard interface.

### Development Roadmap

1. Connect cached rankings to Quant Discovery.
2. Improve security-type classification and data validation.
3. Expand the supported company universe.
4. Add historical backtesting and ranking evaluation.
5. Automate ranking refreshes.
6. Prepare public cloud deployment.

**Disclaimer:** Research scores are experimental indicators,
not investment recommendations or validated return predictions.

---

## Features

### 1. Black-Scholes-Merton Options Pricing

Implements analytical pricing for European call and put options.

Features include:

- European call and put pricing.
- Continuous dividend yield support.
- Risk-free interest rate modeling.
- Input validation for invalid or non-finite parameters.
- Expiration and zero-volatility handling.
- Analytical option Greeks.
- Numerical consistency testing.

The original implementation provides a readable, object-oriented reference pricing engine.

### 2. High-Performance Vectorized Pricing

Implements a second Black-Scholes-Merton pricing engine using NumPy and SciPy.

Unlike the original implementation, which constructs a separate Python object for each option, the vectorized engine processes arrays of option parameters in batches.

Capabilities include:

- Batch European call and put pricing.
- NumPy broadcasting across input arrays.
- Support for varying underlying prices, strikes, maturities, volatilities, and interest rates.
- Continuous dividend yields.
- Expired-option handling.
- Zero-volatility handling.
- Input validation across entire arrays.
- Numerical comparison against the original pricing engine.
- Integration with the FastAPI batch-pricing endpoint.

The vectorized implementation achieved a measured **262.89× speedup** when pricing 100,000 European option contracts in the standalone benchmark.

The optimized pricing engine is also accessible through the REST API.

### 3. Vectorized Analytical Option Greeks

The project supports analytical option Greeks through both its original scalar pricing engine and its optimized NumPy implementation.

The following risk sensitivities are calculated:

| Greek | Description |
|---|---|
| Delta | Sensitivity to changes in the underlying asset price |
| Gamma | Sensitivity of delta to changes in the underlying price |
| Vega | Sensitivity to changes in volatility |
| Theta | Sensitivity to the passage of time |
| Rho | Sensitivity to changes in the risk-free interest rate |

The implementation uses the following conventions:

- Delta and gamma are expressed relative to changes in the underlying price.
- Vega measures sensitivity to a 1-percentage-point volatility change.
- Theta represents calendar-day time decay.
- Rho measures sensitivity to a 1-percentage-point interest rate change.

The vectorized Greeks engine calculates ten outputs for each option contract:

1. Call price.
2. Put price.
3. Call delta.
4. Put delta.
5. Gamma.
6. Vega.
7. Call theta.
8. Put theta.
9. Call rho.
10. Put rho.

The optimized implementation supports:

- NumPy array broadcasting.
- Multiple contracts with different financial parameters.
- Continuous dividend yields.
- Expired options.
- Zero-volatility options.
- Validation of invalid or non-finite inputs.
- Numerical consistency with the scalar Black-Scholes engine.

Undefined analytical Greeks are represented internally using NumPy `NaN` values.

When accessed through FastAPI, undefined Greeks are converted into JSON `null`.

The standalone vectorized Greeks benchmark achieved a measured **944.76× speedup** when calculating prices and Greeks for 100,000 European option contracts.

This represents approximately a **99.89% reduction in execution time** for the measured workflow.

### 4. Implied Volatility Estimation

Provides numerical implied volatility estimation from observed option prices.

Features include:

- Numerical root-finding.
- Pricing-bound validation.
- Numerical safeguards.
- Market-data-derived implied volatility estimates.
- Support for analyzing volatility across strikes and maturities.

### 5. Yahoo Finance Market Data

Integrates with Yahoo Finance through `yfinance` to retrieve option-chain observations.

Features include:

- SPY option-chain retrieval.
- Bid-ask quote filtering.
- Multiple-expiration data collection.
- Underlying-price observations.
- Option last-trade timestamps.
- Implied volatility estimation from filtered market observations.
- Preparation of datasets for volatility visualizations.

The market-data layer separates external data retrieval from the pricing and visualization components.

### 6. FastAPI REST API

Exposes quantitative pricing and market-data functionality through a REST API.

The application provides ten endpoints:

| Method | Endpoint | Description |
|---|---|---|
| GET | `/health` | Application health monitoring |
| POST | `/api/v1/options/price` | Single-contract European call and put pricing |
| POST | `/api/v1/options/greeks` | Analytical option Greeks |
| POST | `/api/v1/options/implied-volatility` | Numerical implied volatility estimation |
| GET | `/api/v1/market/options/{ticker}` | Yahoo Finance option-chain market data |
| POST | `/api/v1/options/batch-price` | Vectorized pricing for up to 10,000 contracts |
| POST | `/api/v1/options/batch-greeks` | Vectorized prices and Greeks for up to 10,000 contracts |
| POST | `/api/v1/portfolio/value` | Portfolio theoretical valuation and position breakdown |
| POST | `/api/v1/portfolio/greeks` | Portfolio valuation, aggregate Greeks, and position exposures |
| POST | `/api/v1/portfolio/scenarios` | Hypothetical portfolio repricing and scenario P&L |

Additional features include:

- JSON request and response handling.
- Automatic input validation using Pydantic.
- Interactive Swagger documentation.
- Automated endpoint tests.
- Numerical validation of batch results.
- Request-size restrictions.
- Structured error responses.

#### Vectorized Batch Pricing API

The batch-pricing endpoint accepts between **1 and 10,000 European option contracts** in a single request.

Each contract is validated using the same financial input rules as the original single-option pricing endpoint.

After validation, the application converts the input parameters into NumPy arrays and performs vectorized call and put pricing.

The endpoint:

- Processes multiple contracts in one request.
- Supports different stock prices, strikes, maturities, rates, volatilities, and dividend yields.
- Preserves the original contract order.
- Returns European call and put prices rounded to four decimal places.
- Rejects empty batches and batches exceeding 10,000 contracts.
- Rejects invalid financial parameters with HTTP 422.
- Uses the existing vectorized pricing engine without duplicating its mathematical implementation.

A local benchmark demonstrated a **50.19× speedup** for 10,000 contracts compared with sending 10,000 individual requests through FastAPI's TestClient.

This improvement reflects the combined benefits of batching requests and using vectorized calculations.

#### Vectorized Batch Greeks API

The batch Greeks endpoint accepts between **1 and 10,000 European option contracts** in a single request.

**Endpoint:**

`POST /api/v1/options/batch-greeks`

The endpoint uses the same validated request model as the existing batch-pricing endpoint.

After validation, the application converts the contract parameters into NumPy arrays and performs one vectorized calculation.

Each result includes:

- Call price.
- Put price.
- Call delta.
- Put delta.
- Gamma.
- Vega.
- Call theta.
- Put theta.
- Call rho.
- Put rho.

The endpoint:

- Processes multiple contracts in one request.
- Preserves the original contract order.
- Returns all ten outputs for each contract.
- Rounds numerical results to four decimal places.
- Converts undefined Greeks into JSON `null`.
- Supports expired and zero-volatility contracts.
- Rejects invalid parameters with HTTP 422.
- Rejects batches containing more than 10,000 contracts.
- Uses the vectorized Greeks engine without duplicating the financial calculations.

A local benchmark demonstrated a **27.48× speedup** for 10,000 contracts compared with sending 10,000 individual Greeks requests through FastAPI's TestClient.

This represents approximately a **96.36% reduction in execution time** for the measured API workflow.

### 7. Portfolio Valuation and Aggregate Greeks

The portfolio analytics engine evaluates collections of European call and put positions using the existing vectorized Black-Scholes-Merton implementation.

Each position specifies:

- Call or put option type.
- Signed contract quantity: positive for long, negative for short.
- Underlying asset price.
- Strike price.
- Time to expiration.
- Risk-free interest rate.
- Annualized volatility.
- Continuous dividend yield.
- Contract multiplier, defaulting to 100.

The current implementation supports portfolios containing options on a single underlying asset. All positions must use the same current underlying price.

The engine calculates:

- Theoretical portfolio value.
- Total absolute contract count.
- Net signed contract count.
- Aggregate portfolio delta.
- Aggregate portfolio gamma.
- Aggregate portfolio vega.
- Aggregate portfolio theta.
- Aggregate portfolio rho.
- Individual option prices, position values, and Greek contributions.

Position values and Greek exposures account for signed quantities and contract multipliers.

The implementation uses vectorized calculations instead of creating a separate scalar pricing engine for every position.

Undefined analytical Greeks are represented as JSON `null` in API responses.

#### Portfolio API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/v1/portfolio/value` | Theoretical portfolio valuation and individual position values |
| POST | `/api/v1/portfolio/greeks` | Complete portfolio valuation and aggregate Greek exposures |

Both endpoints accept between 1 and 10,000 option positions.

### 8. Portfolio Market Scenario Analysis

The scenario analysis engine reprices an options portfolio under hypothetical market conditions.

Each scenario supports three independent changes:

| Scenario Input | Meaning | Example |
|---|---|---|
| `price_change_pct` | Percentage change in the underlying price | `-5.0` means a 5% decline |
| `volatility_change` | Absolute change in annualized volatility | `0.05` means an increase of 5 percentage points |
| `days_forward` | Calendar days elapsed | `7` advances time by one week |

For each scenario, the engine:

1. Adjusts the underlying price.
2. Adjusts the volatility of each option position.
3. Reduces time to expiration, without allowing negative remaining maturity.
4. Reprices the portfolio using vectorized calculations.
5. Calculates the new theoretical portfolio value.
6. Calculates scenario P&L relative to the original theoretical value.
7. Reports position-level theoretical value changes.

Scenario percentage returns are normalized using the absolute original portfolio value when that value is nonzero.

The API accepts between 1 and 100 scenarios per request.

**Endpoint:** `POST /api/v1/portfolio/scenarios`

The maximum supported request contains 10,000 positions and 100 scenarios, representing 1,000,000 scenario-position combinations.

These scenarios are hypothetical model repricings. They are not forecasts, probability-weighted risk measures, or realized trading P&L.

### 9. Interactive Volatility Visualizations

Uses Plotly to visualize implied volatility across option strikes and expiration dates.

Includes:

- A 2D implied volatility smile.
- A 3D visualization of implied volatility across moneyness and maturity.
- Interactive tooltips.
- Market-data-derived observations.
- Multiple viewing perspectives.

---

## Performance Benchmarking

The project includes four complementary performance benchmarks:

1. **Standalone pricing benchmark:** Compares scalar and vectorized Python pricing workflows.
2. **FastAPI batch pricing benchmark:** Compares repeated single-option API requests against one batch-pricing request.
3. **Standalone Greeks benchmark:** Compares scalar and vectorized pricing and Greeks calculations.
4. **FastAPI batch Greeks benchmark:** Compares repeated single-option Greeks requests against one batch Greeks request.

All four benchmarks verify numerical consistency between the compared implementations.

### Benchmark 1: Standalone Pricing Engine

The original implementation calculates option prices individually using Python objects and scalar SciPy operations.

The optimized implementation uses NumPy arrays and vectorized mathematical operations to process large batches.

#### Methodology

Both implementations were evaluated using identical, deterministically generated option parameters.

The benchmark measures the complete workflow required to calculate both European call and put prices.

Three workloads were evaluated:

- 1,000 option contracts.
- 10,000 option contracts.
- 100,000 option contracts.

Each workload was repeated five times, with the median execution time used for comparison.

The benchmark also checks numerical consistency between the aggregate pricing results of both implementations.

The original implementation includes per-option object construction, while the vectorized implementation includes conversion of the generated input parameters into NumPy arrays.

This comparison represents two different end-to-end pricing workflows rather than an isolated comparison of mathematical functions.

#### Standalone Benchmark Results

| Options Priced | Original Engine | Vectorized Engine | Speedup |
|---|---:|---:|---:|
| 1,000 | 73.469 ms | 0.511 ms | **143.90×** |
| 10,000 | 731.115 ms | 3.087 ms | **236.80×** |
| 100,000 | 7,266.352 ms | 27.640 ms | **262.89×** |

#### Standalone Pricing Throughput

| Workload | Original Engine | Vectorized Engine |
|---|---:|---:|
| 1,000 options | 13,611 options/sec | 1,958,703 options/sec |
| 10,000 options | 13,678 options/sec | 3,238,955 options/sec |
| 100,000 options | 13,762 options/sec | **3,617,956 options/sec** |

#### Key Standalone Result

For 100,000 European option contracts:

**Original implementation:**

- Execution time: 7.266 seconds.
- Throughput: 13,762 options per second.

**Vectorized implementation:**

- Execution time: 0.02764 seconds.
- Throughput: 3,617,956 options per second.

**Measured improvement: 262.89× faster.**

This corresponds to an approximately **99.62% reduction in execution time** for the benchmarked workload.

These measurements apply to batch call-and-put pricing, not analytical Greeks, implied volatility estimation, or the complete market-data workflow.

---

### Benchmark 2: FastAPI Batch Pricing Performance

The second benchmark evaluates whether vectorized pricing provides a measurable performance improvement when accessed through the REST API.

Rather than comparing only mathematical functions, this benchmark compares two complete API workflows.

#### Workflow A: Individual API Requests

Each option contract is submitted separately to:

```text
POST /api/v1/options/price
```

For 10,000 contracts, the application processes 10,000 individual requests.

Each request includes:

- FastAPI request handling.
- Pydantic input validation.
- Scalar option pricing.
- Response construction.
- JSON serialization and decoding.

#### Workflow B: Vectorized Batch API Request

All option contracts are submitted together to:

```text
POST /api/v1/options/batch-price
```

For 10,000 contracts, the application processes one batch request.

The workflow includes:

- FastAPI request handling.
- Pydantic validation of all contracts.
- Conversion of contract parameters into NumPy arrays.
- Vectorized call and put pricing.
- Response construction.
- JSON serialization and decoding.

#### API Benchmark Methodology

The benchmark uses FastAPI's `TestClient` to execute the application directly within the Python process.

No separate Uvicorn server is required.

The benchmark:

1. Generates deterministic option parameters using a fixed random seed.
2. Uses identical contracts for both API workflows.
3. Warms up the endpoints before measuring performance.
4. Measures the elapsed time for each workflow.
5. Repeats each workload five times.
6. Uses median execution times to reduce sensitivity to timing fluctuations.
7. Verifies that individual and batch pricing results agree within the configured numerical tolerance.
8. Calculates speedup and option-pricing throughput.
9. Saves the measurements to a CSV file.

The workloads are:

- 100 contracts.
- 1,000 contracts.
- 10,000 contracts.

The benchmark uses sequential requests for the individual workflow.

It does not simulate concurrent clients or network traffic.

#### API Benchmark Results

| Options Priced | Individual API Requests | Single Batch API Request | Speedup |
|---|---:|---:|---:|
| 100 | 46.449 ms | 1.590 ms | **29.22×** |
| 1,000 | 457.218 ms | 10.029 ms | **45.59×** |
| 10,000 | 4,987.507 ms | 99.367 ms | **50.19×** |

#### API Pricing Throughput

| Workload | Individual API Requests | Batch API Request |
|---|---:|---:|
| 100 options | 2,153 options/sec | 62,905 options/sec |
| 1,000 options | 2,187 options/sec | 99,710 options/sec |
| 10,000 options | 2,005 options/sec | **100,637 options/sec** |

#### Key API Performance Result

For 10,000 European option contracts:

**Individual API requests:**

- Number of requests: 10,000.
- Execution time: 4.988 seconds.
- Throughput: 2,005 options per second.

**Vectorized batch API:**

- Number of requests: 1.
- Execution time: 0.099 seconds.
- Throughput: 100,637 options per second.

**Measured improvement: 50.19× faster.**

This represents an approximately **98.01% reduction in execution time** for the measured workflow.

The benchmark demonstrates that the batch API can process substantially more contracts per second than repeated sequential individual requests under the tested conditions.

---

### Benchmark 3: Standalone Vectorized Greeks Performance

The third benchmark evaluates the performance improvement from vectorizing analytical option Greeks.

The original implementation uses the scalar `BlackScholes.greeks()` method.

The optimized implementation uses `greeks_options_vectorized()` to process complete NumPy arrays.

Both implementations calculate:

- Call price.
- Put price.
- Call delta.
- Put delta.
- Gamma.
- Vega.
- Call theta.
- Put theta.
- Call rho.
- Put rho.

#### Greeks Benchmark Methodology

The benchmark:

1. Generates deterministic option parameters.
2. Uses identical contracts for both implementations.
3. Calculates all ten outputs for every contract.
4. Verifies numerical consistency.
5. Warms up both implementations.
6. Repeats each workload five times.
7. Uses median execution times.
8. Calculates throughput and speedup.
9. Saves the results to a CSV file.

Three workloads were evaluated:

- 1,000 option contracts.
- 10,000 option contracts.
- 100,000 option contracts.

The scalar implementation processes each contract individually.

The vectorized implementation processes entire arrays of financial parameters.

#### Standalone Greeks Benchmark Results

| Contracts | Scalar Engine | Vectorized Engine | Speedup |
|---|---:|---:|---:|
| 1,000 | 0.244534 s | 0.000579 s | **422.06×** |
| 10,000 | 2.452822 s | 0.003051 s | **803.94×** |
| 100,000 | 24.421484 s | 0.025850 s | **944.76×** |

#### Standalone Greeks Throughput

| Workload | Scalar Engine | Vectorized Engine |
|---|---:|---:|
| 1,000 options | 4,089 options/sec | 1,725,998 options/sec |
| 10,000 options | 4,077 options/sec | 3,277,614 options/sec |
| 100,000 options | 4,095 options/sec | **3,868,541 options/sec** |

#### Key Standalone Greeks Result

For 100,000 European option contracts:

**Original scalar implementation:**

- Execution time: 24.421484 seconds.
- Throughput: 4,095 options per second.

**Vectorized implementation:**

- Execution time: 0.025850 seconds.
- Throughput: 3,868,541 options per second.

**Measured improvement: 944.76× faster.**

This represents an approximately **99.89% reduction in execution time** for the measured workload.

Numerical verification passed for all three workloads.

The scalar implementation includes Python object construction and four-decimal rounding.

The vectorized implementation preserves full floating-point precision.

The benchmark measures complete local calculation workflows rather than isolating the execution time of individual mathematical formulas.

---

### Benchmark 4: FastAPI Batch Greeks Performance

The fourth benchmark evaluates the performance of the new Batch Greeks API.

It compares sending individual Greeks requests against submitting the same contracts in one vectorized batch request.

#### Workflow A: Individual Greeks Requests

Each contract is submitted separately to:

```text
POST /api/v1/options/greeks
```

For 10,000 contracts, the application processes 10,000 individual requests.

Each request performs:

- FastAPI request handling.
- Pydantic validation.
- Scalar Black-Scholes calculations.
- Analytical Greeks calculations.
- JSON response construction.
- Response serialization and decoding.

#### Workflow B: Vectorized Batch Greeks Request

All contracts are submitted together to:

```text
POST /api/v1/options/batch-greeks
```

For 10,000 contracts, the application processes one request.

The workflow includes:

- FastAPI request handling.
- Pydantic validation of all contracts.
- Conversion into NumPy arrays.
- Vectorized pricing and Greeks calculations.
- JSON response construction.
- Response serialization and decoding.

#### Batch Greeks API Benchmark Methodology

The benchmark uses FastAPI's `TestClient` to execute requests directly against the application.

The benchmark:

1. Generates deterministic option contracts.
2. Uses identical contracts for both workflows.
3. Verifies numerical consistency across all ten output fields.
4. Warms up both endpoints.
5. Repeats each workload five times.
6. Uses median execution times.
7. Calculates throughput and speedup.
8. Saves the results to a CSV file.

The workloads are:

- 100 contracts.
- 1,000 contracts.
- 10,000 contracts.

Individual requests are executed sequentially.

The benchmark does not measure network latency or concurrent users.

#### Batch Greeks API Benchmark Results

| Contracts | Individual Requests | Single Batch Request | Speedup |
|---|---:|---:|---:|
| 100 | 0.066370 s | 0.002973 s | **22.32×** |
| 1,000 | 0.646701 s | 0.024437 s | **26.46×** |
| 10,000 | 6.471921 s | 0.235500 s | **27.48×** |

#### Batch Greeks API Throughput

| Workload | Individual Requests | Batch Request |
|---|---:|---:|
| 100 options | 1,507 options/sec | 33,636 options/sec |
| 1,000 options | 1,546 options/sec | 40,921 options/sec |
| 10,000 options | 1,545 options/sec | **42,463 options/sec** |

#### Key Batch Greeks API Result

For 10,000 European option contracts:

**Individual API requests:**

- Number of requests: 10,000.
- Execution time: 6.471921 seconds.
- Throughput: 1,545 options per second.

**Vectorized batch API:**

- Number of requests: 1.
- Execution time: 0.235500 seconds.
- Throughput: 42,463 options per second.

**Measured improvement: 27.48× faster.**

This represents an approximately **96.36% reduction in execution time** for the measured workflow.

Numerical verification passed for every workload.

---

### Benchmark 5: Portfolio Valuation and Aggregate Greeks

This benchmark measures the complete portfolio analytics calculation, including theoretical valuation, aggregate Greeks, and position-level reporting.

Portfolios contain deterministic synthetic European call and put positions with varying strikes, maturities, rates, volatilities, dividend yields, and signed quantities.

Portfolio construction is excluded from the timed section.

Each workload is warmed up once and timed five times. The median execution time is reported.

| Portfolio Size | Median Execution Time | Throughput |
|---|---:|---:|
| 100 positions | 0.000637 s | 156,996 positions/sec |
| 1,000 positions | 0.003739 s | 267,445 positions/sec |
| **10,000 positions** | **0.033647 s** | **297,201 positions/sec** |

**Key result:** The engine valued and calculated aggregate Greeks for 10,000 positions in approximately **33.6 milliseconds**.

The benchmark verifies that individual position values reconcile with the reported portfolio value.

### Benchmark 6: Portfolio Scenario Analysis

This benchmark measures hypothetical portfolio repricing across multiple market scenarios.

Each timed execution includes vectorized scenario calculations and construction of detailed scenario-level and position-level reports.

Portfolio and scenario object construction is excluded from the timed section.

| Portfolio Size | Scenarios | Combinations | Median Execution Time | Throughput |
|---|---:|---:|---:|---:|
| 100 positions | 10 | 1,000 | 0.000875 s | 1,142,802 combinations/sec |
| 1,000 positions | 50 | 50,000 | 0.031888 s | 1,568,004 combinations/sec |
| **10,000 positions** | **100** | **1,000,000** | **0.709751 s** | **1,408,945 combinations/sec** |

**Key result:** The engine processed **1 million scenario-position combinations in approximately 0.71 seconds**.

The benchmark verifies that:

- Scenario P&L equals the difference between shocked and original theoretical portfolio values.
- Position-level scenario P&L reconciles with portfolio-level scenario P&L.
- Reported numerical results are finite for the generated test inputs.

The benchmark measures local Python execution, including detailed result construction. It does not measure HTTP network throughput or concurrent requests.

---

### Why the Benchmark Speedups Differ

The pricing and Greeks comparison benchmarks measure different operations and application overhead. The portfolio benchmarks additionally measure aggregate risk calculations and hypothetical scenario repricing.

The standalone pricing benchmark calculates two prices per contract.

The standalone Greeks benchmark calculates ten outputs per contract.

The API benchmarks include additional processing:

- Request routing.
- Pydantic validation.
- JSON serialization and decoding.
- Response construction.
- TestClient overhead.

The Batch Greeks API also returns more data per contract than the Batch Pricing API.

Additionally, the API benchmarks compare one batch request against many individual requests, so the speedup reflects both request consolidation and vectorized calculations.

**These benchmarks do not isolate NumPy's performance contribution from all other overhead.**

### Benchmark Limitations

The benchmarks were executed locally on an Apple Silicon MacBook Pro using Python 3.11.

Results may vary depending on:

- Processor performance.
- Python version.
- Installed dependencies.
- System load.
- Memory availability.

The API benchmarks use FastAPI's in-process `TestClient`.

They do not include:

- Real network latency.
- Production Uvicorn server performance.
- Concurrent user traffic.
- Reverse proxies or load balancers.
- Cloud infrastructure.
- External market-data retrieval.
- Database operations.
- Production monitoring overhead.

The reported API throughput is therefore **in-process benchmark throughput**, not a claim about production HTTP server capacity.

---

### Reproduce the Benchmarks

Run the original pricing benchmark:

```bash
python -m benchmarks.benchmark_black_scholes
```

Run the scalar-versus-vectorized pricing benchmark:

```bash
python -m benchmarks.benchmark_vectorized
```

Run the FastAPI batch-pricing benchmark:

```bash
python -m benchmarks.benchmark_api
```

Run the scalar-versus-vectorized Greeks benchmark:

```bash
python -m benchmarks.benchmark_vectorized_greeks
```

Run the FastAPI Batch Greeks benchmark:

```bash
python -m benchmarks.benchmark_batch_greeks_api
```

Run the portfolio valuation and scenario analysis benchmarks:

```bash
python -m benchmarks.benchmark_portfolio
```

The API benchmarks run directly against the FastAPI application using `TestClient`.

A separate server is not required.

The benchmarks may take several minutes because they perform repeated scalar calculations and individual API requests.

#### Benchmark Output Files

Results are saved to:

```text
benchmarks/results/
├── black_scholes_benchmark.csv
├── vectorized_comparison.csv
├── api_comparison.csv
├── vectorized_greeks_comparison.csv
├── batch_greeks_api_comparison.csv
├── portfolio_valuation_comparison.csv
└── portfolio_scenario_comparison.csv
```

The original benchmark measures call pricing, put pricing, and full valuation with analytical Greeks separately.

The vectorized pricing comparison measures both call and put pricing together.

The vectorized Greeks comparison measures prices and all analytical Greeks.

The two API comparisons measure complete in-process request workflows.

---

## Visualizations

### 2D Implied Volatility Smile

The volatility smile displays implied volatility across option strikes using filtered SPY market-data observations.

This visualization helps illustrate how implied volatility varies across strike prices for a selected expiration.

![SPY Implied Volatility Smile](docs/images/volatility_smile.png)

### 3D Implied Volatility Visualization

The interactive 3D visualization displays observed implied volatility across:

- **Moneyness:** Strike price relative to the underlying price.
- **Time to expiration:** Remaining days until option expiration.
- **Implied volatility:** Volatility estimated from observed option prices.

Unlike an interpolated volatility surface, this visualization represents individual market-data observations.

The screenshots below show the visualization from different viewing angles.

**View 1 — Implied Volatility Across Moneyness and Maturity**

![SPY Implied Volatility - 3D View 1](docs/images/volatility_surface_3d.png)

**View 2 — Alternative Perspective**

![SPY Implied Volatility - 3D View 2](docs/images/volatility_surface_3d_2.png)

---

## Technology Stack

| Category | Technologies |
|---|---|
| Programming Language | Python 3.11 |
| Numerical Computing | NumPy, SciPy |
| Data Processing | pandas |
| Market Data | yfinance |
| REST API | FastAPI, Uvicorn |
| Data Validation | Pydantic |
| Visualization | Plotly |
| Automated Testing | pytest, pytest-cov |
| Code Quality | Ruff |
| Dependency Security | pip-audit |
| Containerization | Docker |
| Version Control | Git, GitHub |
| Continuous Integration | GitHub Actions |

---

## Project Architecture

The application follows a modular architecture that separates financial calculations, market-data retrieval, API functionality, and visualization.

### Pricing Layer

Responsible for:

- Scalar Black-Scholes-Merton pricing.
- Analytical Greeks.
- Implied volatility estimation.
- Vectorized batch pricing.
- Vectorized analytical Greeks.
- Portfolio theoretical valuation and aggregate Greeks.
- Vectorized portfolio market scenario analysis.
- Numerical validation of financial calculations.

### Market-Data Layer

Responsible for:

- Yahoo Finance option-chain retrieval.
- Quote validation and filtering.
- Multiple-expiration data collection.
- Preparing market observations for analysis.

### API Layer

Responsible for:

- Exposing quantitative functionality through FastAPI.
- Validating incoming requests.
- Supporting single-contract pricing and Greeks.
- Supporting vectorized batch pricing.
- Supporting vectorized batch Greeks.
- Exposing portfolio valuation, risk, and scenario endpoints.
- Enforcing batch request-size limits.
- Returning structured JSON responses.
- Providing application health monitoring.

### Visualization Layer

Responsible for:

- Generating implied volatility smiles.
- Visualizing volatility across moneyness and maturity.
- Producing interactive Plotly figures.

### Benchmarking Layer

Responsible for:

- Measuring scalar pricing performance.
- Measuring vectorized pricing performance.
- Measuring scalar and vectorized Greeks performance.
- Comparing individual and batch API workflows.
- Measuring portfolio valuation and scenario analysis throughput.
- Verifying numerical consistency during performance comparisons.
- Saving reproducible benchmark results.

### Testing and Infrastructure

Responsible for:

- Automated unit and integration-style tests.
- Numerical correctness checks.
- Batch API validation and response testing.
- Code coverage measurement.
- Static code-quality checks.
- Dependency vulnerability scanning.
- Docker image builds.
- Container smoke testing.
- Continuous integration.

---

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
│   │   ├── implied_volatility.py
│   │   ├── portfolio.py
│   │   ├── scenario_analysis.py
│   │   └── vectorized_black_scholes.py
│   │
│   └── visualization/
│       ├── __init__.py
│       ├── volatility_smile.py
│       └── volatility_surface_3d.py
│
├── benchmarks/
│   ├── benchmark_api.py
│   ├── benchmark_batch_greeks_api.py
│   ├── benchmark_black_scholes.py
│   ├── benchmark_vectorized.py
│   ├── benchmark_vectorized_greeks.py
│   ├── benchmark_portfolio.py
│   └── results/
│       ├── api_comparison.csv
│       ├── batch_greeks_api_comparison.csv
│       ├── black_scholes_benchmark.csv
│       ├── vectorized_comparison.csv
│       ├── vectorized_greeks_comparison.csv
│       ├── portfolio_valuation_comparison.csv
│       └── portfolio_scenario_comparison.csv
│
├── docs/
│   └── images/
│       ├── volatility_smile.png
│       ├── volatility_surface_3d.png
│       └── volatility_surface_3d_2.png
│
├── tests/
│   ├── test_api.py
│   ├── test_batch_greeks_api.py
│   ├── test_batch_pricing_api.py
│   ├── test_black_scholes.py
│   ├── test_implied_volatility.py
│   ├── test_market_data.py
│   ├── test_multi_expiration.py
│   ├── test_multi_expiration_extended.py
│   ├── test_portfolio.py
│   ├── test_portfolio_api.py
│   ├── test_scenario_analysis.py
│   ├── test_vectorized_black_scholes.py
│   ├── test_vectorized_greeks.py
│   ├── test_volatility_smile.py
│   ├── test_volatility_surface.py
│   └── test_yahoo_client_extended.py
│
├── .dockerignore
├── .gitignore
├── Dockerfile
├── README.md
├── requirements.txt
├── ruff.toml
└── volatility_surface.py
```

---

## Installation

### Prerequisites

- Python 3.11.
- Git.
- Docker (optional).

### 1. Clone the Repository

```bash
git clone https://github.com/kyriakoscm7-crypto/quant-options-engine.git
cd quant-options-engine
```

### 2. Create a Virtual Environment

**macOS or Linux:**

```bash
python3.11 -m venv .venv
source .venv/bin/activate
```

**Windows:**

```powershell
py -3.11 -m venv .venv
.venv\Scripts\Activate.ps1
```

### 3. Install Dependencies

```bash
python -m pip install -r requirements.txt
```

---

## Running the API

Start the FastAPI application:

```bash
python -m uvicorn app.api.main:app --reload
```

Open the interactive API documentation:

**http://127.0.0.1:8000/docs**

The Swagger interface allows users to explore available endpoints, submit requests, and inspect responses.

If port 8000 is already in use, start the application on another port:

```bash
python -m uvicorn app.api.main:app --reload --port 8001
```

Then open:

**http://127.0.0.1:8001/docs**

---

## Running with Docker

The application can also run inside a Docker container without requiring a local Python installation.

### 1. Build the Docker Image

```bash
docker build -t quant-options-engine .
```

### 2. Start the Container

```bash
docker run --rm -p 8080:8080 quant-options-engine
```

### 3. Access the API

Open:

**http://127.0.0.1:8080/docs**

To stop the container, press `Ctrl + C` in the terminal.

---

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

Submit the following JSON to:

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

### Example: Vectorized Pricing in Python

The vectorized engine can price multiple contracts in a single operation.

```python
from app.pricing.vectorized_black_scholes import (
    price_options_vectorized,
)

strikes = [90, 95, 100, 105, 110]

calls, puts = price_options_vectorized(
    S=100,
    K=strikes,
    T=0.5,
    r=0.045,
    sigma=0.20,
    q=0.01,
)

print("Call prices:", calls)
print("Put prices:", puts)
```

NumPy broadcasting allows a single stock price, interest rate, or volatility value to be combined with arrays of strike prices and expiration times.

### Example: Vectorized Greeks in Python

The optimized engine can calculate prices and analytical Greeks for multiple contracts simultaneously.

```python
from app.pricing.vectorized_black_scholes import (
    greeks_options_vectorized,
)

results = greeks_options_vectorized(
    S=100,
    K=[90, 100, 110],
    T=1.0,
    r=0.05,
    sigma=0.20,
    q=0.0,
)

print("Call prices:", results["call_price"])
print("Call deltas:", results["call_delta"])
print("Vega:", results["vega"])
```

The function returns a dictionary containing ten NumPy arrays.

Each array contains one result for every option contract.

---

## Example: Vectorized Batch Pricing Through FastAPI

**Endpoint:**

```text
POST /api/v1/options/batch-price
```

The endpoint accepts between 1 and 10,000 contracts per request.

### Example Request

```json
{
  "options": [
    {
      "S": 100,
      "K": 90,
      "T": 1,
      "r": 0.05,
      "sigma": 0.2,
      "q": 0
    },
    {
      "S": 100,
      "K": 100,
      "T": 1,
      "r": 0.05,
      "sigma": 0.2,
      "q": 0
    },
    {
      "S": 100,
      "K": 110,
      "T": 1,
      "r": 0.05,
      "sigma": 0.2,
      "q": 0
    }
  ]
}
```

### Example Response

```json
{
  "count": 3,
  "results": [
    {
      "call_price": 16.6994,
      "put_price": 2.3101
    },
    {
      "call_price": 10.4506,
      "put_price": 5.5735
    },
    {
      "call_price": 6.0401,
      "put_price": 10.6753
    }
  ]
}
```

The example was verified locally using FastAPI's Swagger interface.

The API returned HTTP 200 with three option-pricing results.

Each result corresponds to the contract at the same position in the request.

---

## Example: Vectorized Batch Greeks Through FastAPI

**Endpoint:**

```text
POST /api/v1/options/batch-greeks
```

The endpoint accepts between 1 and 10,000 contracts per request.

### Example Request

```json
{
  "options": [
    {
      "S": 100,
      "K": 100,
      "T": 1,
      "r": 0.05,
      "sigma": 0.2,
      "q": 0
    },
    {
      "S": 110,
      "K": 100,
      "T": 0,
      "r": 0.05,
      "sigma": 0.2,
      "q": 0
    }
  ]
}
```

### Example Response

```json
{
  "count": 2,
  "results": [
    {
      "call_price": 10.4506,
      "put_price": 5.5735,
      "call_delta": 0.6368,
      "put_delta": -0.3632,
      "gamma": 0.0188,
      "vega": 0.3752,
      "call_theta": -0.0176,
      "put_theta": -0.0045,
      "call_rho": 0.5323,
      "put_rho": -0.4189
    },
    {
      "call_price": 10.0,
      "put_price": 0.0,
      "call_delta": null,
      "put_delta": null,
      "gamma": null,
      "vega": null,
      "call_theta": null,
      "put_theta": null,
      "call_rho": null,
      "put_rho": null
    }
  ]
}
```

The first contract demonstrates a standard Black-Scholes-Merton valuation.

The second contract has expired.

Its option prices equal their intrinsic values, while the analytical Greeks are undefined and returned as JSON `null`.

### Batch API Request Validation

Both batch endpoints return HTTP 422 when:

- The options list is empty.
- More than 10,000 contracts are submitted.
- A required contract parameter is missing.
- A stock price or strike price is nonpositive.
- Time to expiration or volatility is negative.
- A parameter is invalid or non-finite.
- Unexpected request fields are supplied.

Each contract is validated before the vectorized calculation begins.

---

## Example: Portfolio Risk Analytics Through FastAPI

### Portfolio Valuation and Greeks

**Endpoint:** `POST /api/v1/portfolio/greeks`

Example request:

```json
{
  "positions": [
    {
      "option_type": "call",
      "quantity": 2,
      "S": 100,
      "K": 100,
      "T": 1,
      "r": 0.05,
      "sigma": 0.2,
      "q": 0,
      "multiplier": 100
    },
    {
      "option_type": "put",
      "quantity": -1,
      "S": 100,
      "K": 95,
      "T": 0.5,
      "r": 0.05,
      "sigma": 0.25,
      "q": 0,
      "multiplier": 100
    }
  ]
}
```

The response contains the portfolio's theoretical value, aggregate Greeks, and a detailed breakdown of each position's contribution.

Positive quantities represent long option positions; negative quantities represent short option positions.

To retrieve theoretical valuation without aggregate Greeks, submit the same request to:

`POST /api/v1/portfolio/value`

### Portfolio Scenario Analysis

**Endpoint:** `POST /api/v1/portfolio/scenarios`

Example request:

```json
{
  "positions": [
    {
      "option_type": "call",
      "quantity": 2,
      "S": 100,
      "K": 100,
      "T": 1,
      "r": 0.05,
      "sigma": 0.2
    },
    {
      "option_type": "put",
      "quantity": -1,
      "S": 100,
      "K": 95,
      "T": 0.5,
      "r": 0.05,
      "sigma": 0.25
    }
  ],
  "scenarios": [
    {
      "name": "No Change"
    },
    {
      "name": "Market Decline",
      "price_change_pct": -5,
      "volatility_change": 0.05,
      "days_forward": 7
    },
    {
      "name": "Market Rally",
      "price_change_pct": 5,
      "volatility_change": -0.03,
      "days_forward": 7
    }
  ]
}
```

The response includes:

- Original theoretical portfolio value.
- Scenario names and market shocks.
- Repriced theoretical portfolio value for each scenario.
- Scenario theoretical P&L.
- Scenario percentage return, when defined.
- Position-level original and shocked values.
- Position-level theoretical P&L.

A scenario that decreases an option's volatility below zero is rejected with HTTP 422.

Invalid request fields, non-finite financial inputs, duplicate scenario names, and inconsistent underlying prices are also rejected.

---

## Automated Testing

The project includes **638 automated tests** covering quantitative calculations, market-data processing, API behavior, and visualizations.

Recent milestones introduced:

- 43 tests for vectorized Greeks calculations.
- 47 tests for the Batch Greeks API.
- 113 tests for portfolio valuation and aggregate Greeks.
- 118 tests for portfolio scenario analysis.
- 108 tests for the portfolio API endpoints.

### Test Coverage

Latest verified local results:

| Component | Coverage |
|---|---:|
| FastAPI | **99%** |
| Yahoo Finance Client | 95% |
| Multiple-Expiration Processing | 90% |
| Original Black-Scholes Engine | 90% |
| Vectorized Black-Scholes Engine | **100%** |
| Portfolio Analytics | **100%** |
| Portfolio Scenario Analysis | **98%** |
| Implied Volatility Solver | 78% |
| Volatility Smile | 79% |
| 3D Volatility Visualization | 63% |
| **Overall** | **93%** |

The test suite covers:

- European call and put pricing.
- Analytical Greeks.
- Numerical pricing edge cases.
- Implied volatility estimation.
- Input validation and error handling.
- FastAPI endpoint behavior.
- Market-data processing and quote filtering.
- Multiple-expiration data retrieval.
- Volatility visualization generation.
- Vectorized batch pricing.
- Vectorized analytical Greeks.
- NumPy broadcasting.
- Expired and zero-volatility options.
- Numerical agreement between scalar and vectorized implementations.
- Batch API request validation.
- Batch API response formatting.
- Preservation of contract order.
- Maximum batch-size enforcement.
- Consistency between single-contract and batch endpoints.
- Undefined Greeks represented as JSON `null`.
- Portfolio valuation and aggregate Greek exposure calculations.
- Long and short option positions with contract multipliers.
- Portfolio scenario repricing and P&L reconciliation.
- Scenario input validation and HTTP 422 responses.
- Portfolio API response structures and financial consistency.

### Run Tests Locally

```bash
python -m pytest tests/ -q --cov=app --cov-report=term-missing
```

Latest verified local result:

```text
638 passed, 1 warning in 5.08s
TOTAL 850 56 93%
```

The warning originates from a Starlette dependency deprecation notice and does not indicate a failed test.

Code coverage measures which statements are executed during testing. It does not independently guarantee numerical correctness or complete financial-model validation.

---

## Code Quality and Security

The project uses automated checks to maintain code quality and identify dependency vulnerabilities.

### Ruff

Ruff performs static analysis and enforces consistent Python coding practices.

Run locally:

```bash
python -m ruff check app/ tests/ benchmarks/
```

Latest verified result:

```text
All checks passed!
```

### Dependency Security Scanning

The GitHub Actions workflow includes dependency vulnerability scanning using `pip-audit`.

This helps identify known security vulnerabilities in installed Python dependencies.

Security scanning does not guarantee that the application or its dependencies are free from vulnerabilities.

---

## Continuous Integration

The project uses GitHub Actions to automatically validate changes.

Workflow configuration:

```text
.github/workflows/ci.yml
```

Every push and pull request triggers two jobs.

### Python Quality, Tests, and Security

The workflow:

1. Checks out the repository.
2. Configures Python 3.11.
3. Installs project dependencies.
4. Runs Ruff code-quality checks.
5. Executes automated pytest tests.
6. Generates code coverage results.
7. Scans dependencies for known vulnerabilities.

### Docker Build and Smoke Test

The workflow:

1. Checks out the repository.
2. Builds the application's Docker image.
3. Starts the container.
4. Checks the application's `/health` endpoint.
5. Verifies that the containerized API responds successfully.

Both jobs have been successfully executed through GitHub Actions for previous milestones.

The new portfolio analytics and scenario analysis changes will be verified through CI after they are committed and pushed.

The workflow status is displayed at the top of this README.

---

## Quantitative Finance Concepts

### Black-Scholes-Merton Model

The Black-Scholes-Merton framework estimates theoretical European option prices using:

- Underlying asset price.
- Strike price.
- Time to expiration.
- Risk-free interest rate.
- Volatility.
- Continuous dividend yield.

The model assumes a particular stochastic process for the underlying asset and provides analytical European option pricing formulas.

### Option Greeks

Option Greeks quantify how theoretical option values respond to changes in market inputs.

They are useful for analyzing risk exposure and understanding the behavior of derivative prices.

### Implied Volatility

Implied volatility is the volatility parameter that makes a model's theoretical price equal an observed option price.

Because implied volatility generally cannot be isolated algebraically in the Black-Scholes-Merton formula, numerical root-finding methods are used.

### Volatility Smile

A volatility smile describes how implied volatility varies across strike prices for options sharing the same expiration.

### Volatility Across Maturities

Examining implied volatility across different expiration dates helps illustrate the term structure of implied volatility.

The project's 3D visualization combines strike-relative moneyness, time to expiration, and implied volatility into an interactive chart.

### Portfolio Risk Aggregation

Portfolio Greeks combine position-level option sensitivities after accounting for contract quantities and multipliers.

Long and short positions contribute signed exposures. Aggregate Greeks describe local sensitivity to changes in model inputs, not guaranteed future profit or loss.

### Scenario Analysis

Scenario analysis evaluates how a portfolio's theoretical value changes under specified hypothetical market shocks.

The engine adjusts the underlying price, volatility, and remaining time to expiration before repricing each position.

Scenario P&L is the difference between shocked and original theoretical portfolio values. It is not a probability estimate or realized trading result.

### Numerical Vectorization

Vectorization replaces repeated scalar Python operations with array-based numerical computations.

NumPy and SciPy perform many array operations using optimized numerical routines, reducing Python-level execution overhead.

In this project, vectorization substantially improves throughput for:

- European call and put pricing.
- Analytical option Greeks.
- Batch pricing API requests.
- Batch Greeks API requests.

The optimized calculations can be accessed directly through Python or through the FastAPI endpoints.

---

## Model Assumptions and Limitations

This project demonstrates quantitative modeling and software engineering techniques. Several limitations should be considered when interpreting its results.

### Black-Scholes-Merton Assumptions

- The underlying asset follows geometric Brownian motion.
- Volatility and the risk-free interest rate are assumed constant over the option's life.
- The model assumes continuous trading and frictionless markets.
- Analytical pricing formulas are designed for European-style exercise.

### American-Style SPY Options

SPY options are American-style and may be exercised before expiration.

The current implementation uses European Black-Scholes-Merton formulas when estimating prices and implied volatility.

Consequently, these estimates are approximations, particularly when early exercise is economically relevant.

### Dividend Yield

The pricing engines support continuous dividend yields.

The market-data implied volatility workflow may use a zero dividend yield unless a nonzero value is explicitly supplied.

This can introduce differences between theoretical model estimates and observed SPY option prices.

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

### Portfolio Analytics Limitations

- The portfolio engine currently supports one underlying asset per portfolio.
- Portfolio positions are limited to European call and put options.
- Position values are theoretical model valuations, not executable market quotes.
- Portfolio Greeks describe local model sensitivities and may change substantially under large market moves.
- Scenario analysis uses deterministic hypothetical shocks, not probability-weighted forecasts.
- The scenario model holds interest rates and dividend yields constant while changing price, volatility, and time.
- Portfolio scenario analysis does not model transaction costs, liquidity, margin requirements, or execution risk.
- Large scenario requests can require substantial memory because detailed position-level results are returned.

### Performance Benchmark Limitations

- Measurements were performed on a local Apple Silicon MacBook Pro.
- Results may vary with hardware, software versions, and system load.
- Benchmarks use generated option parameters rather than live trading workloads.
- The vectorized implementation calculates both prices and analytical Greeks.
- Standalone pricing throughput excludes market-data retrieval, API overhead, and network latency.
- API benchmark throughput includes in-process request handling but excludes real network latency.
- API benchmarks use sequential individual requests rather than concurrent clients.
- The scalar and vectorized implementations have different execution and memory-allocation characteristics.
- The scalar Greeks implementation rounds outputs, while the vectorized implementation preserves floating-point precision.
- The batch API supports a maximum of 10,000 contracts per request.
- Portfolio endpoints support a maximum of 10,000 positions.
- Scenario requests support a maximum of 100 scenarios.
- Portfolio benchmark throughput includes local calculation and report construction, not HTTP networking.
- Performance results should not be interpreted as production trading-system throughput.

---

## Future Improvements

Potential future enhancements include:

- Implementing Monte Carlo option pricing with statistical convergence analysis.
- Implementing American-style option pricing using binomial trees.
- Adding finite-difference pricing methods.
- Extending portfolio risk analytics to multiple underlying assets.
- Adding historical and probability-based portfolio risk measures such as Value at Risk.
- Incorporating estimated dividend yields into market-data implied volatility calculations.
- Improving quote-quality filters and volatility outlier detection.
- Developing interpolated and calibrated volatility surfaces.
- Adding additional underlying assets and option types.
- Benchmarking performance under real HTTP traffic and concurrent workloads.
- Building an interactive web dashboard.
- Deploying the FastAPI application to a cloud platform.
- Adding structured logging and application monitoring.
- Introducing additional numerical performance optimizations.
- Implementing more advanced derivatives pricing models.

---

## Disclaimer

This project is intended for educational, research, and software engineering portfolio purposes.

It is not financial advice, an investment recommendation, or a production trading system.

Theoretical model outputs and market-data-derived estimates should not be relied upon for live trading decisions.