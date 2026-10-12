"""
Benchmark the vectorized Black-Scholes pricing engine.

Compare the original scalar implementation against NumPy
vectorization using identical option parameters.

Run from the project root:

    python -m benchmarks.benchmark_vectorized
"""

import csv
import gc
import statistics
import time
from pathlib import Path

import numpy as np

from app.pricing.black_scholes import BlackScholes
from app.pricing.vectorized_black_scholes import price_options_vectorized
from benchmarks.benchmark_black_scholes import generate_option_parameters

WORKLOADS = [1_000, 10_000, 100_000]
REPEATS = 5

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RESULTS_FILE = (
    PROJECT_ROOT / "benchmarks" / "results" / "vectorized_comparison.csv"
)


def benchmark_scalar(parameters):
    """
    Price every option using the original BlackScholes class.

    Both call and put prices are calculated for each option.
    """

    checksum = 0.0

    start = time.perf_counter()

    for option in parameters:
        engine = BlackScholes(*option)

        checksum += engine.call_price()
        checksum += engine.put_price()

    elapsed = time.perf_counter() - start

    if not np.isfinite(checksum):
        raise RuntimeError("Invalid scalar benchmark result.")

    return elapsed, checksum


def benchmark_vectorized(parameters):
    """
    Price all options in one NumPy batch.

    Input conversion is included in the timed section.
    """

    start = time.perf_counter()

    data = np.asarray(parameters, dtype=float)

    calls, puts = price_options_vectorized(
        S=data[:, 0],
        K=data[:, 1],
        T=data[:, 2],
        r=data[:, 3],
        sigma=data[:, 4],
        q=data[:, 5],
    )

    checksum = float(np.sum(calls) + np.sum(puts))

    elapsed = time.perf_counter() - start

    if not np.isfinite(checksum):
        raise RuntimeError("Invalid vectorized benchmark result.")

    return elapsed, checksum


def median_benchmark(function, parameters):
    """
    Warm up the function, then measure five repetitions.
    """

    function(parameters[:100])

    times = []
    checksums = []

    for _ in range(REPEATS):
        gc.collect()

        elapsed, checksum = function(parameters)

        times.append(elapsed)
        checksums.append(checksum)

    return statistics.median(times), checksums


def save_results(results):
    """Save benchmark results to a CSV file."""

    RESULTS_FILE.parent.mkdir(parents=True, exist_ok=True)

    with RESULTS_FILE.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=[
                "options",
                "scalar_seconds",
                "vectorized_seconds",
                "speedup",
                "scalar_options_per_second",
                "vectorized_options_per_second",
            ],
        )

        writer.writeheader()
        writer.writerows(results)


def main():
    """Run the complete scalar-versus-vectorized comparison."""

    print()
    print("=" * 72)
    print("BLACK-SCHOLES: SCALAR VS VECTORIZED")
    print("=" * 72)

    results = []

    for workload in WORKLOADS:
        print(f"\nBenchmarking {workload:,} options...")

        parameters = generate_option_parameters(workload)

        scalar_time, scalar_checksums = median_benchmark(
            benchmark_scalar,
            parameters,
        )

        vector_time, vector_checksums = median_benchmark(
            benchmark_vectorized,
            parameters,
        )

        # Verify both implementations produce equivalent prices.
        for scalar_sum, vector_sum in zip(
            scalar_checksums,
            vector_checksums,
        ):
            if not np.isclose(
                scalar_sum,
                vector_sum,
                rtol=1e-10,
                atol=1e-8,
            ):
                raise RuntimeError(
                    "Scalar and vectorized prices do not match."
                )

        speedup = scalar_time / vector_time

        scalar_throughput = workload / scalar_time
        vector_throughput = workload / vector_time

        result = {
            "options": workload,
            "scalar_seconds": round(scalar_time, 6),
            "vectorized_seconds": round(vector_time, 6),
            "speedup": round(speedup, 2),
            "scalar_options_per_second": round(scalar_throughput),
            "vectorized_options_per_second": round(vector_throughput),
        }

        results.append(result)

        print(f"Original engine:   {scalar_time:.6f} seconds")
        print(f"Vectorized engine: {vector_time:.6f} seconds")
        print(f"Speedup:           {speedup:,.2f}x")
        print(f"Original:          {scalar_throughput:,.0f} options/sec")
        print(f"Vectorized:        {vector_throughput:,.0f} options/sec")

    save_results(results)

    print()
    print("=" * 72)
    print("BENCHMARK COMPLETE")
    print("=" * 72)
    print(f"Results saved to: {RESULTS_FILE}")


if __name__ == "__main__":
    main()