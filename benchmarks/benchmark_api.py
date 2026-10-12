"""
Benchmark individual FastAPI pricing requests against batch pricing.

This benchmark compares two workflows:

1. Sending one HTTP request per option contract.
2. Sending one HTTP request containing multiple contracts.

Both workflows use FastAPI's TestClient.

TestClient executes the application directly in the Python process,
so no separate Uvicorn server or network connection is required.

IMPORTANT:

This measures in-process HTTP-style request handling.

It includes:
- FastAPI routing.
- Request validation.
- Pricing calculations.
- Response construction.
- JSON serialization.

It does not measure:
- Real network latency.
- External server deployment.
- Concurrent production traffic.
- Load balancing.
- Production throughput.

Run:

    python -m benchmarks.benchmark_api
"""

import csv
import statistics
import time
from pathlib import Path

import numpy as np
from fastapi.testclient import TestClient

from app.api.main import app

# ============================================================
# BENCHMARK CONFIGURATION
# ============================================================

# Number of option contracts in each benchmark workload.
WORKLOADS = (100, 1_000, 10_000)

# Number of times each workload is measured.
REPEATS = 5

# Existing API endpoints.
SINGLE_ENDPOINT = "/api/v1/options/price"
BATCH_ENDPOINT = "/api/v1/options/batch-price"

# Directory where benchmark results will be saved.
RESULTS_DIRECTORY = Path("benchmarks/results")

# CSV output filename.
RESULTS_FILE = RESULTS_DIRECTORY / "api_comparison.csv"


# ============================================================
# GENERATE DETERMINISTIC OPTION CONTRACTS
# ============================================================

def generate_options(count: int) -> list[dict]:
    """
    Generate a reproducible collection of option contracts.

    A fixed random seed ensures that the same workload
    produces the same input parameters across benchmark runs.

    This makes performance comparisons more meaningful.
    """

    # Create NumPy's modern random number generator.
    rng = np.random.default_rng(seed=42)

    # Generate plausible underlying prices.
    stock_prices = rng.uniform(
        low=80.0,
        high=120.0,
        size=count,
    )

    # Generate strike prices.
    strikes = rng.uniform(
        low=70.0,
        high=130.0,
        size=count,
    )

    # Generate time to expiration in years.
    expirations = rng.uniform(
        low=0.05,
        high=2.0,
        size=count,
    )

    # Generate risk-free interest rates.
    interest_rates = rng.uniform(
        low=0.01,
        high=0.06,
        size=count,
    )

    # Generate annualized volatility.
    volatilities = rng.uniform(
        low=0.10,
        high=0.60,
        size=count,
    )

    # Generate continuous dividend yields.
    dividend_yields = rng.uniform(
        low=0.0,
        high=0.04,
        size=count,
    )

    # Convert each parameter set into a JSON-compatible dictionary.
    #
    # Python's float() converts NumPy scalar values into
    # standard Python floats that can be serialized to JSON.
    options = []

    for index in range(count):

        option = {
            "S": float(stock_prices[index]),
            "K": float(strikes[index]),
            "T": float(expirations[index]),
            "r": float(interest_rates[index]),
            "sigma": float(volatilities[index]),
            "q": float(dividend_yields[index]),
        }

        options.append(option)

    return options


# ============================================================
# INDIVIDUAL REQUEST WORKFLOW
# ============================================================

def benchmark_individual_requests(
    client: TestClient,
    options: list[dict],
) -> tuple[float, list[dict]]:
    """
    Price every option using a separate API request.

    Returns:
        elapsed_seconds:
            Total execution time.

        results:
            Call and put prices for every contract.
    """

    results = []

    # Start the performance timer.
    start = time.perf_counter()

    # Send one request for each option.
    for option in options:

        response = client.post(
            SINGLE_ENDPOINT,
            json=option,
        )

        # Stop immediately if the API returns an error.
        response.raise_for_status()

        # Save the returned call and put prices.
        results.append(response.json())

    # Measure the total elapsed time.
    elapsed_seconds = time.perf_counter() - start

    return elapsed_seconds, results


# ============================================================
# VECTORIZED BATCH REQUEST WORKFLOW
# ============================================================

def benchmark_batch_request(
    client: TestClient,
    options: list[dict],
) -> tuple[float, list[dict]]:
    """
    Price all contracts using one batch API request.

    Returns:
        elapsed_seconds:
            Total execution time.

        results:
            Call and put prices for every contract.
    """

    # Start the performance timer.
    start = time.perf_counter()

    # Submit every contract in one request.
    response = client.post(
        BATCH_ENDPOINT,
        json={"options": options},
    )

    # Raise an error if the API rejects the request.
    response.raise_for_status()

    # Decode the response.
    data = response.json()

    # Stop the timer after response processing.
    elapsed_seconds = time.perf_counter() - start

    # Verify that the API returned the expected number of results.
    if data["count"] != len(options):

        raise RuntimeError(
            "Batch API returned an unexpected number of contracts."
        )

    return elapsed_seconds, data["results"]


# ============================================================
# NUMERICAL CORRECTNESS VERIFICATION
# ============================================================

def verify_results(
    individual_results: list[dict],
    batch_results: list[dict],
) -> None:
    """
    Verify that both API workflows produce matching prices.

    Both endpoints round prices to four decimal places.

    Small differences of 0.0001 may occur near rounding
    boundaries due to floating-point arithmetic.
    """

    if len(individual_results) != len(batch_results):

        raise AssertionError(
            "Individual and batch result counts do not match."
        )

    for index, (individual, batch) in enumerate(
        zip(individual_results, batch_results, strict=True)
    ):

        for price_type in ("call_price", "put_price"):

            difference = abs(
                individual[price_type] - batch[price_type]
            )

            if difference > 0.0001 + 1e-10:

                raise AssertionError(
                    f"Pricing mismatch at contract {index}: "
                    f"{price_type} differs by {difference}."
                )


# ============================================================
# RUN ONE BENCHMARK WORKLOAD
# ============================================================

def run_workload(
    client: TestClient,
    count: int,
) -> dict:
    """
    Benchmark both API workflows for one workload size.

    Each workflow is measured multiple times.

    The median is used to reduce sensitivity to
    occasional operating-system scheduling delays.
    """

    # Generate identical inputs for both approaches.
    options = generate_options(count)

    individual_times = []
    batch_times = []

    # Warm up both endpoints before timing.
    #
    # This avoids measuring some one-time initialization costs.
    benchmark_individual_requests(client, options[:1])
    benchmark_batch_request(client, options[:1])

    # Repeat the benchmark several times.
    for repeat in range(REPEATS):

        print(
            f"  Repeat {repeat + 1}/{REPEATS}",
            flush=True,
        )

        # Measure individual API requests.
        individual_time, individual_results = (
            benchmark_individual_requests(
                client,
                options,
            )
        )

        # Measure one vectorized batch request.
        batch_time, batch_results = benchmark_batch_request(
            client,
            options,
        )

        # Verify that both approaches return consistent prices.
        verify_results(
            individual_results,
            batch_results,
        )

        # Save the measured times.
        individual_times.append(individual_time)
        batch_times.append(batch_time)

    # Calculate median execution times.
    individual_median = statistics.median(individual_times)
    batch_median = statistics.median(batch_times)

    # Calculate the measured performance improvement.
    speedup = individual_median / batch_median

    # Calculate throughput for both workflows.
    individual_throughput = count / individual_median
    batch_throughput = count / batch_median

    return {
        "options": count,
        "individual_seconds": individual_median,
        "batch_seconds": batch_median,
        "speedup": speedup,
        "individual_options_per_second": individual_throughput,
        "batch_options_per_second": batch_throughput,
    }


# ============================================================
# SAVE RESULTS TO CSV
# ============================================================

def save_results(results: list[dict]) -> None:
    """
    Save benchmark results to a CSV file.

    The CSV can later be used for:
    - Performance comparisons.
    - Charts.
    - README documentation.
    - Portfolio demonstrations.
    """

    # Create the results directory if necessary.
    RESULTS_DIRECTORY.mkdir(
        parents=True,
        exist_ok=True,
    )

    # Determine the CSV columns.
    fieldnames = [
        "options",
        "individual_seconds",
        "batch_seconds",
        "speedup",
        "individual_options_per_second",
        "batch_options_per_second",
    ]

    # Open the CSV file for writing.
    with RESULTS_FILE.open(
        mode="w",
        newline="",
        encoding="utf-8",
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames,
        )

        writer.writeheader()
        writer.writerows(results)


# ============================================================
# MAIN BENCHMARK EXECUTION
# ============================================================

def main() -> None:
    """
    Run all configured API benchmark workloads.
    """

    print()
    print("=" * 65)
    print("QUANT OPTIONS ENGINE — API PERFORMANCE BENCHMARK")
    print("=" * 65)

    print()
    print("Comparing:")
    print("  1. Individual option-pricing API requests")
    print("  2. One vectorized batch-pricing API request")

    print()
    print(f"Repeats per workload: {REPEATS}")
    print(f"Workloads: {WORKLOADS}")

    results = []

    # TestClient executes FastAPI directly in the current process.
    #
    # We reuse one client so both workflows run in the
    # same application environment.
    with TestClient(app) as client:

        for count in WORKLOADS:

            print()
            print("-" * 65)
            print(f"Benchmarking {count:,} option contracts")
            print("-" * 65)

            result = run_workload(
                client,
                count,
            )

            results.append(result)

            print()
            print(
                f"Individual requests: "
                f"{result['individual_seconds']:.6f} seconds"
            )

            print(
                f"Batch request:       "
                f"{result['batch_seconds']:.6f} seconds"
            )

            print(
                f"Measured speedup:    "
                f"{result['speedup']:.2f}x"
            )

            print(
                f"Individual throughput: "
                f"{result['individual_options_per_second']:,.0f} options/sec"
            )

            print(
                f"Batch throughput:      "
                f"{result['batch_options_per_second']:,.0f} options/sec"
            )

    # Save the completed benchmark results.
    save_results(results)

    print()
    print("=" * 65)
    print("BENCHMARK COMPLETE")
    print("=" * 65)

    print()
    print(f"Results saved to: {RESULTS_FILE}")
    print()


# Only run the benchmark when this file is executed directly.
#
# Importing this module from a test file will not
# automatically start the performance measurements.
if __name__ == "__main__":
    main()