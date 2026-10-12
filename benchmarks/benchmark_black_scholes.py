"""
Black-Scholes Performance Benchmark
===================================

This script measures the performance of our Black-Scholes-Merton
options pricing engine.

We benchmark three operations:

1. European call option pricing
2. European put option pricing
3. Full valuation (call, put, and Greeks)

Workloads:
- 1,000 option valuations
- 10,000 option valuations
- 100,000 option valuations

Each benchmark is repeated multiple times to reduce the effect
of random system performance fluctuations.

Results include:
- Median execution time
- Options valued per second

Run from the project root:

    python -m benchmarks.benchmark_black_scholes
"""

import csv
import gc
import statistics
import time
from pathlib import Path

from app.pricing.black_scholes import BlackScholes

# ============================================================
# BENCHMARK CONFIGURATION
# ============================================================

# Number of options to value in each benchmark.
WORKLOADS = [1_000, 10_000, 100_000]

# Number of times each benchmark is repeated.
REPEATS = 3

# Project root directory.
PROJECT_ROOT = Path(__file__).resolve().parents[1]

# Directory where benchmark results will be saved.
RESULTS_DIRECTORY = PROJECT_ROOT / "benchmarks" / "results"

# Output CSV file.
RESULTS_FILE = RESULTS_DIRECTORY / "black_scholes_benchmark.csv"


# ============================================================
# GENERATE OPTION PARAMETERS
# ============================================================


def generate_option_parameters(count: int) -> list[tuple]:
    """
    Generate deterministic option-pricing inputs.

    We vary strike prices, expiration times, and volatility
    to simulate a range of European option contracts.

    The parameters are generated outside the timed section
    so input generation does not affect pricing measurements.
    """

    parameters = []

    for index in range(count):

        # Underlying stock price remains fixed at $100.
        stock_price = 100.0

        # Strike prices vary from $80 to $120.
        strike_price = 80.0 + (index % 41)

        # Expirations range from 30 to 390 days.
        days_to_expiry = 30 + (index % 13) * 30

        time_to_expiry = days_to_expiry / 365.0

        # Annualized volatility ranges from 15% to 34%.
        volatility = 0.15 + (index % 20) * 0.01

        # Fixed annual risk-free interest rate.
        risk_free_rate = 0.045

        # Fixed annual dividend yield.
        dividend_yield = 0.01

        parameters.append(
            (
                stock_price,
                strike_price,
                time_to_expiry,
                risk_free_rate,
                volatility,
                dividend_yield,
            )
        )

    return parameters


# ============================================================
# RUN A SINGLE BENCHMARK
# ============================================================


def run_single_benchmark(
    parameters: list[tuple],
    operation: str,
) -> float:
    """
    Time one complete batch of option valuations.

    Returns the elapsed time in seconds.

    The timer starts immediately before pricing begins
    and stops immediately after all options are valued.
    """

    # Use a high-resolution timer suitable for benchmarking.
    start_time = time.perf_counter()

    # Prevent the results from being completely unused.
    checksum = 0.0

    for option_parameters in parameters:

        # Create a pricing engine for this option.
        engine = BlackScholes(*option_parameters)

        if operation == "call":

            # Calculate the European call price.
            checksum += engine.call_price()

        elif operation == "put":

            # Calculate the European put price.
            checksum += engine.put_price()

        elif operation == "greeks":

            # Calculate both option prices and all Greeks.
            results = engine.greeks()

            checksum += results["call_price"]
            checksum += results["put_price"]

        else:
            raise ValueError(f"Unknown benchmark operation: {operation}")

    # Stop the timer after the full batch completes.
    end_time = time.perf_counter()

    # Check that pricing produced a valid numerical result.
    if not (checksum > 0):
        raise RuntimeError("Benchmark produced an invalid result.")

    return end_time - start_time


# ============================================================
# REPEAT BENCHMARK AND CALCULATE STATISTICS
# ============================================================


def benchmark_operation(
    parameters: list[tuple],
    operation: str,
) -> dict:
    """
    Run an operation several times and calculate
    its median execution time and throughput.

    Median time is used because it is less sensitive
    to occasional slow runs caused by other processes.
    """

    execution_times = []

    # Warm up the code before collecting measurements.
    warmup_parameters = parameters[:100]

    run_single_benchmark(warmup_parameters, operation)

    for _ in range(REPEATS):

        # Collect garbage before the timed run.
        gc.collect()

        # Measure one full batch.
        elapsed_time = run_single_benchmark(
            parameters,
            operation,
        )

        execution_times.append(elapsed_time)

    # Calculate the median execution time.
    median_time = statistics.median(execution_times)

    # Number of option valuations completed per second.
    options_per_second = len(parameters) / median_time

    return {
        "operation": operation,
        "options": len(parameters),
        "median_seconds": median_time,
        "options_per_second": options_per_second,
    }


# ============================================================
# SAVE RESULTS TO CSV
# ============================================================


def save_results(results: list[dict]) -> None:
    """
    Save benchmark measurements to a CSV file.

    This allows us to document performance results
    in the project's README.
    """

    RESULTS_DIRECTORY.mkdir(
        parents=True,
        exist_ok=True,
    )

    with RESULTS_FILE.open(
        mode="w",
        newline="",
        encoding="utf-8",
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=[
                "operation",
                "options",
                "median_seconds",
                "options_per_second",
            ],
        )

        writer.writeheader()

        writer.writerows(results)


# ============================================================
# MAIN BENCHMARK EXECUTION
# ============================================================


def main() -> None:
    """
    Run every benchmark and print the results.
    """

    print()
    print("=" * 72)
    print("BLACK-SCHOLES PERFORMANCE BENCHMARK")
    print("=" * 72)

    print(f"Repeats per benchmark: {REPEATS}")
    print(f"Workloads: {WORKLOADS}")

    print()

    all_results = []

    for workload in WORKLOADS:

        print(f"\nBenchmarking {workload:,} options...")
        print("-" * 72)

        # Generate inputs once for the current workload.
        parameters = generate_option_parameters(workload)

        for operation in ["call", "put", "greeks"]:

            result = benchmark_operation(
                parameters,
                operation,
            )

            all_results.append(result)

            print(
                f"{operation.upper():8s} | "
                f"Median: {result['median_seconds']:.4f} s | "
                f"Throughput: "
                f"{result['options_per_second']:,.0f} options/sec"
            )

    # Save all nine benchmark results to a CSV file.
    save_results(all_results)

    print()
    print("=" * 72)
    print("BENCHMARK COMPLETE")
    print("=" * 72)

    print(f"Results saved to: {RESULTS_FILE}")

    print()


if __name__ == "__main__":
    main()