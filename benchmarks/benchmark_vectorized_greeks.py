"""
Benchmark scalar versus vectorized Black-Scholes-Merton Greeks.

This benchmark compares:

1. The original scalar BlackScholes.greeks() method.
2. The NumPy-based greeks_options_vectorized() function.

Both implementations calculate:

- Call price
- Put price
- Call delta
- Put delta
- Gamma
- Vega
- Call theta
- Put theta
- Call rho
- Put rho

Benchmark workloads:
- 1,000 option contracts
- 10,000 option contracts
- 100,000 option contracts

Methodology:
- Generate deterministic option parameters.
- Warm up both implementations.
- Run each workload five times.
- Use median execution times to reduce timing noise.
- Verify numerical consistency.
- Calculate throughput and speedup.
- Export benchmark results to CSV.

Run from the project root:

    python -m benchmarks.benchmark_vectorized_greeks

Notes
-----
This benchmark measures local Python execution time.

It does not measure:
- HTTP request latency
- FastAPI performance
- Network communication
- Concurrent request throughput
"""

import csv
import math
import statistics
import time
from pathlib import Path

import numpy as np

from app.pricing.black_scholes import BlackScholes
from app.pricing.vectorized_black_scholes import greeks_options_vectorized

# ============================================================
# BENCHMARK CONFIGURATION
# ============================================================

# Number of contracts in each benchmark workload.
WORKLOAD_SIZES = (
    1_000,
    10_000,
    100_000,
)

# Number of repeated measurements per workload.
REPEATS = 5

# Fixed random seed ensures repeatable input generation.
RANDOM_SEED = 42

# CSV output location.
RESULTS_PATH = (
    Path(__file__).resolve().parent
    / "results"
    / "vectorized_greeks_comparison.csv"
)

# Every output calculated by both engines.
OUTPUT_FIELDS = (
    "call_price",
    "put_price",
    "call_delta",
    "put_delta",
    "gamma",
    "vega",
    "call_theta",
    "put_theta",
    "call_rho",
    "put_rho",
)


# ============================================================
# GENERATE DETERMINISTIC OPTION CONTRACTS
# ============================================================

def generate_option_parameters(count: int) -> dict:
    """
    Generate reproducible option parameters.

    Each contract receives its own:

    - Underlying stock price
    - Strike price
    - Time to expiration
    - Risk-free interest rate
    - Volatility
    - Dividend yield

    Parameters are intentionally restricted to valid,
    non-expired, positive-volatility contracts.

    This allows us to compare analytical Greeks directly
    without encountering undefined edge cases.
    """

    rng = np.random.default_rng(RANDOM_SEED)

    # Underlying stock prices between $50 and $250.
    stock_prices = rng.uniform(
        50.0,
        250.0,
        size=count,
    )

    # Strike prices relative to each underlying price.
    #
    # A multiplier below 1 produces lower strikes.
    # A multiplier above 1 produces higher strikes.
    strikes = stock_prices * rng.uniform(
        0.80,
        1.20,
        size=count,
    )

    # Expiration times between approximately
    # one month and two years.
    expirations = rng.uniform(
        1.0 / 12.0,
        2.0,
        size=count,
    )

    # Annual risk-free interest rates between 0% and 7%.
    rates = rng.uniform(
        0.00,
        0.07,
        size=count,
    )

    # Annualized volatilities between 10% and 60%.
    volatilities = rng.uniform(
        0.10,
        0.60,
        size=count,
    )

    # Annual dividend yields between 0% and 5%.
    dividends = rng.uniform(
        0.00,
        0.05,
        size=count,
    )

    return {
        "S": stock_prices,
        "K": strikes,
        "T": expirations,
        "r": rates,
        "sigma": volatilities,
        "q": dividends,
    }


# ============================================================
# SCALAR BLACK-SCHOLES IMPLEMENTATION
# ============================================================

def calculate_scalar_greeks(parameters: dict) -> dict:
    """
    Calculate Greeks using one BlackScholes object per option.

    This represents the original non-vectorized workflow.

    Each contract requires:
    1. Extracting its individual parameters.
    2. Constructing a BlackScholes object.
    3. Calling its greeks() method.
    4. Storing the resulting values.

    Returns
    -------
    dict
        NumPy arrays containing every output field.
    """

    count = len(parameters["S"])

    # Allocate storage for all ten output fields.
    results = {
        name: np.empty(count, dtype=float)
        for name in OUTPUT_FIELDS
    }

    # Process contracts individually.
    for index in range(count):

        engine = BlackScholes(
            S=parameters["S"][index],
            K=parameters["K"][index],
            T=parameters["T"][index],
            r=parameters["r"][index],
            sigma=parameters["sigma"][index],
            q=parameters["q"][index],
        )

        # The original engine returns rounded results.
        contract_results = engine.greeks()

        # Store every output in its corresponding array.
        for name in OUTPUT_FIELDS:
            results[name][index] = contract_results[name]

    return results


# ============================================================
# VECTORIZED BLACK-SCHOLES IMPLEMENTATION
# ============================================================

def calculate_vectorized_greeks(parameters: dict) -> dict:
    """
    Calculate all Greeks in a single vectorized operation.

    The function receives complete NumPy arrays rather
    than processing one contract at a time.
    """

    return greeks_options_vectorized(
        S=parameters["S"],
        K=parameters["K"],
        T=parameters["T"],
        r=parameters["r"],
        sigma=parameters["sigma"],
        q=parameters["q"],
    )


# ============================================================
# NUMERICAL VERIFICATION
# ============================================================

def verify_numerical_consistency(
    scalar_results: dict,
    vectorized_results: dict,
) -> None:
    """
    Verify that scalar and vectorized calculations agree.

    The original scalar engine rounds results to four
    decimal places.

    The vectorized engine preserves full floating-point
    precision.

    We therefore compare results using an absolute
    tolerance of 0.0001.

    This avoids incorrectly rejecting small differences
    caused by rounding.
    """

    for name in OUTPUT_FIELDS:

        scalar_values = scalar_results[name]
        vectorized_values = vectorized_results[name]

        # Reject non-finite results.
        if not np.all(np.isfinite(scalar_values)):
            raise AssertionError(
                f"Non-finite scalar values detected: {name}"
            )

        if not np.all(np.isfinite(vectorized_values)):
            raise AssertionError(
                f"Non-finite vectorized values detected: {name}"
            )

        # Compare every contract's result.
        #
        # The tolerance accounts for the scalar engine's
        # four-decimal rounding.
        np.testing.assert_allclose(
            scalar_values,
            vectorized_values,
            rtol=0.0,
            atol=0.0001,
            err_msg=f"Mismatch detected in {name}",
        )


# ============================================================
# TIMING UTILITIES
# ============================================================

def measure_execution_time(
    calculation_function,
    parameters: dict,
) -> float:
    """
    Measure one complete calculation using a monotonic timer.

    perf_counter() provides a high-resolution timer
    suitable for performance measurements.
    """

    start = time.perf_counter()

    calculation_function(parameters)

    end = time.perf_counter()

    return end - start


def benchmark_implementation(
    calculation_function,
    parameters: dict,
) -> float:
    """
    Benchmark an implementation using repeated measurements.

    Steps:
    1. Execute one warm-up calculation.
    2. Measure the function REPEATS times.
    3. Return the median execution time.

    Median timing is less sensitive to occasional
    operating-system scheduling interruptions.
    """

    # Warm up the implementation.
    calculation_function(parameters)

    measurements = []

    for _ in range(REPEATS):

        elapsed = measure_execution_time(
            calculation_function,
            parameters,
        )

        measurements.append(elapsed)

    return statistics.median(measurements)


# ============================================================
# BENCHMARK ONE WORKLOAD
# ============================================================

def benchmark_workload(count: int) -> dict:
    """
    Compare scalar and vectorized Greeks for one workload.

    Returns timing, throughput, and speedup statistics.
    """

    print()
    print("=" * 70)
    print(f"BENCHMARKING {count:,} OPTION CONTRACTS")
    print("=" * 70)

    # Generate the same contracts for both implementations.
    parameters = generate_option_parameters(count)

    # Calculate one result from each implementation
    # before benchmarking.
    scalar_results = calculate_scalar_greeks(parameters)

    vectorized_results = calculate_vectorized_greeks(parameters)

    # Confirm mathematical agreement.
    verify_numerical_consistency(
        scalar_results,
        vectorized_results,
    )

    print("Numerical verification: PASSED")

    # Measure original scalar implementation.
    scalar_time = benchmark_implementation(
        calculate_scalar_greeks,
        parameters,
    )

    # Measure optimized vectorized implementation.
    vectorized_time = benchmark_implementation(
        calculate_vectorized_greeks,
        parameters,
    )

    # Avoid division by zero if an extremely short
    # measurement produces a zero duration.
    if scalar_time <= 0 or vectorized_time <= 0:
        raise RuntimeError(
            "Benchmark produced an invalid execution time."
        )

    # Calculate relative speedup.
    speedup = scalar_time / vectorized_time

    # Calculate how many contracts each implementation
    # processes per second.
    scalar_throughput = count / scalar_time

    vectorized_throughput = count / vectorized_time

    print(f"Scalar execution time:     {scalar_time:.6f} seconds")
    print(f"Vectorized execution time: {vectorized_time:.6f} seconds")
    print(f"Speedup:                   {speedup:.2f}x")
    print()
    print(f"Scalar throughput:         {scalar_throughput:,.0f} options/sec")
    print(f"Vectorized throughput:     {vectorized_throughput:,.0f} options/sec")

    # Confirm calculated statistics are finite.
    statistics_values = (
        scalar_time,
        vectorized_time,
        speedup,
        scalar_throughput,
        vectorized_throughput,
    )

    if not all(math.isfinite(value) for value in statistics_values):
        raise RuntimeError(
            "Benchmark produced non-finite statistics."
        )

    return {
        "contracts": count,
        "scalar_seconds": scalar_time,
        "vectorized_seconds": vectorized_time,
        "speedup": speedup,
        "scalar_options_per_second": scalar_throughput,
        "vectorized_options_per_second": vectorized_throughput,
    }


# ============================================================
# SAVE BENCHMARK RESULTS
# ============================================================

def save_results(results: list[dict]) -> None:
    """
    Save benchmark measurements to a CSV file.

    The results directory is created automatically
    if it does not already exist.
    """

    RESULTS_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    fieldnames = (
        "contracts",
        "scalar_seconds",
        "vectorized_seconds",
        "speedup",
        "scalar_options_per_second",
        "vectorized_options_per_second",
    )

    with RESULTS_PATH.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames,
        )

        writer.writeheader()

        for result in results:
            writer.writerow(result)

    print()
    print(f"Results saved to: {RESULTS_PATH}")


# ============================================================
# MAIN BENCHMARK EXECUTION
# ============================================================

def main() -> None:
    """
    Run every benchmark workload and save the results.
    """

    print()
    print("=" * 70)
    print("VECTORIZED BLACK-SCHOLES GREEKS BENCHMARK")
    print("=" * 70)

    print(f"Repeated measurements: {REPEATS}")
    print(f"Random seed: {RANDOM_SEED}")

    results = []

    # Run each workload independently.
    for count in WORKLOAD_SIZES:

        result = benchmark_workload(count)

        results.append(result)

    # Export the complete benchmark table.
    save_results(results)

    print()
    print("=" * 70)
    print("BENCHMARK COMPLETE")
    print("=" * 70)

    print()
    print("Summary:")

    for result in results:

        print(
            f"{result['contracts']:>8,} options | "
            f"Scalar: {result['scalar_seconds']:.6f}s | "
            f"Vectorized: {result['vectorized_seconds']:.6f}s | "
            f"Speedup: {result['speedup']:.2f}x"
        )


if __name__ == "__main__":
    main()