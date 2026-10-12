"""
Benchmark individual versus batch FastAPI Greeks requests.

This benchmark compares:

1. POST /api/v1/options/greeks
   One HTTP-style request per option contract.

2. POST /api/v1/options/batch-greeks
   One HTTP-style request containing all contracts.

Each endpoint calculates ten outputs:
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

Methodology:
- Generate deterministic option contracts.
- Test 100, 1,000, and 10,000 contracts.
- Warm up both endpoints.
- Measure each approach five times.
- Compare median execution times.
- Verify numerical consistency.
- Save results to CSV.

Run from the project root:

    python -m benchmarks.benchmark_batch_greeks_api

Important:
    FastAPI TestClient runs requests inside the Python process.

    Results include request validation, routing, calculation,
    response serialization, and TestClient overhead.

    Results do not measure real network latency or concurrency.
"""

import csv
import math
import statistics
import time
from pathlib import Path

import numpy as np
from fastapi.testclient import TestClient

from app.api.main import app

# ============================================================
# BENCHMARK CONFIGURATION
# ============================================================

WORKLOAD_SIZES = (
    100,
    1_000,
    10_000,
)

REPEATS = 5

RANDOM_SEED = 42

SINGLE_ENDPOINT = "/api/v1/options/greeks"

BATCH_ENDPOINT = "/api/v1/options/batch-greeks"

RESULTS_PATH = (
    Path(__file__).resolve().parent
    / "results"
    / "batch_greeks_api_comparison.csv"
)

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

def generate_option_contracts(count: int) -> list[dict]:
    """
    Generate valid, reproducible option contracts.

    The same contracts are sent to both endpoints to
    ensure a fair comparison.
    """

    rng = np.random.default_rng(RANDOM_SEED)

    stock_prices = rng.uniform(
        50.0,
        250.0,
        size=count,
    )

    strikes = stock_prices * rng.uniform(
        0.80,
        1.20,
        size=count,
    )

    expirations = rng.uniform(
        1.0 / 12.0,
        2.0,
        size=count,
    )

    interest_rates = rng.uniform(
        0.0,
        0.07,
        size=count,
    )

    volatilities = rng.uniform(
        0.10,
        0.60,
        size=count,
    )

    dividend_yields = rng.uniform(
        0.0,
        0.05,
        size=count,
    )

    contracts = []

    for index in range(count):

        contract = {
            "S": float(stock_prices[index]),
            "K": float(strikes[index]),
            "T": float(expirations[index]),
            "r": float(interest_rates[index]),
            "sigma": float(volatilities[index]),
            "q": float(dividend_yields[index]),
        }

        contracts.append(contract)

    return contracts


# ============================================================
# INDIVIDUAL API REQUESTS
# ============================================================

def calculate_individual_requests(
    client: TestClient,
    contracts: list[dict],
) -> list[dict]:
    """
    Calculate Greeks using one request per contract.

    Every request passes through FastAPI independently.

    This includes:
    - Request handling
    - Pydantic validation
    - Scalar Black-Scholes calculation
    - JSON response generation
    """

    results = []

    for contract in contracts:

        response = client.post(
            SINGLE_ENDPOINT,
            json=contract,
        )

        if response.status_code != 200:
            raise RuntimeError(
                "Individual Greeks request failed: "
                f"HTTP {response.status_code}: {response.text}"
            )

        results.append(response.json())

    return results


# ============================================================
# BATCH API REQUEST
# ============================================================

def calculate_batch_request(
    client: TestClient,
    contracts: list[dict],
) -> list[dict]:
    """
    Calculate Greeks using one batch request.

    The complete contract list is submitted to FastAPI.

    The endpoint uses vectorized NumPy calculations.
    """

    response = client.post(
        BATCH_ENDPOINT,
        json={"options": contracts},
    )

    if response.status_code != 200:
        raise RuntimeError(
            "Batch Greeks request failed: "
            f"HTTP {response.status_code}: {response.text}"
        )

    data = response.json()

    if data["count"] != len(contracts):
        raise AssertionError(
            "Batch endpoint returned an incorrect contract count."
        )

    if len(data["results"]) != len(contracts):
        raise AssertionError(
            "Batch endpoint returned an incorrect number of results."
        )

    return data["results"]


# ============================================================
# VERIFY NUMERICAL CONSISTENCY
# ============================================================

def verify_results(
    individual_results: list[dict],
    batch_results: list[dict],
) -> None:
    """
    Verify that both API approaches return matching values.

    Both endpoints round their outputs to four decimals.

    A small absolute tolerance accounts for possible
    floating-point rounding differences.
    """

    if len(individual_results) != len(batch_results):
        raise AssertionError(
            "Individual and batch result counts do not match."
        )

    for index, (individual, batch) in enumerate(
        zip(
            individual_results,
            batch_results,
            strict=True,
        )
    ):

        for field in OUTPUT_FIELDS:

            individual_value = individual[field]
            batch_value = batch[field]

            # Handle undefined Greeks consistently.
            if individual_value is None or batch_value is None:

                if individual_value is not None or batch_value is not None:
                    raise AssertionError(
                        f"Undefined Greek mismatch at contract {index}, "
                        f"field {field}."
                    )

                continue

            # Both values must be finite.
            if not math.isfinite(individual_value):
                raise AssertionError(
                    f"Non-finite individual value: {field}"
                )

            if not math.isfinite(batch_value):
                raise AssertionError(
                    f"Non-finite batch value: {field}"
                )

            if not math.isclose(
                individual_value,
                batch_value,
                rel_tol=0.0,
                abs_tol=0.0001,
            ):
                raise AssertionError(
                    f"Numerical mismatch at contract {index}, "
                    f"field {field}: "
                    f"individual={individual_value}, "
                    f"batch={batch_value}"
                )


# ============================================================
# TIMING UTILITIES
# ============================================================

def measure_execution_time(
    calculation_function,
    client: TestClient,
    contracts: list[dict],
) -> float:
    """
    Measure the total time required for an API workload.
    """

    start = time.perf_counter()

    calculation_function(
        client,
        contracts,
    )

    end = time.perf_counter()

    return end - start


def benchmark_implementation(
    calculation_function,
    client: TestClient,
    contracts: list[dict],
) -> float:
    """
    Run repeated measurements and return the median.

    A warm-up request is performed before measurements.
    """

    calculation_function(
        client,
        contracts[:1],
    )

    measurements = []

    for _ in range(REPEATS):

        elapsed = measure_execution_time(
            calculation_function,
            client,
            contracts,
        )

        measurements.append(elapsed)

    return statistics.median(measurements)


# ============================================================
# BENCHMARK ONE WORKLOAD
# ============================================================

def benchmark_workload(
    client: TestClient,
    count: int,
) -> dict:
    """
    Compare individual and batch API performance.
    """

    print()
    print("=" * 70)
    print(f"BENCHMARKING {count:,} OPTION CONTRACTS")
    print("=" * 70)

    contracts = generate_option_contracts(count)

    # Verify numerical agreement before timing.
    individual_results = calculate_individual_requests(
        client,
        contracts,
    )

    batch_results = calculate_batch_request(
        client,
        contracts,
    )

    verify_results(
        individual_results,
        batch_results,
    )

    print("Numerical verification: PASSED")

    # Benchmark sequential individual requests.
    individual_time = benchmark_implementation(
        calculate_individual_requests,
        client,
        contracts,
    )

    # Benchmark one vectorized batch request.
    batch_time = benchmark_implementation(
        calculate_batch_request,
        client,
        contracts,
    )

    if individual_time <= 0 or batch_time <= 0:
        raise RuntimeError(
            "Benchmark produced an invalid execution time."
        )

    speedup = individual_time / batch_time

    individual_throughput = count / individual_time

    batch_throughput = count / batch_time

    values = (
        individual_time,
        batch_time,
        speedup,
        individual_throughput,
        batch_throughput,
    )

    if not all(math.isfinite(value) for value in values):
        raise RuntimeError(
            "Benchmark produced non-finite statistics."
        )

    print(f"Individual requests:       {individual_time:.6f} seconds")
    print(f"Single batch request:      {batch_time:.6f} seconds")
    print(f"Speedup:                   {speedup:.2f}x")
    print()
    print(f"Individual throughput:     {individual_throughput:,.0f} options/sec")
    print(f"Batch throughput:          {batch_throughput:,.0f} options/sec")

    return {
        "contracts": count,
        "individual_seconds": individual_time,
        "batch_seconds": batch_time,
        "speedup": speedup,
        "individual_options_per_second": individual_throughput,
        "batch_options_per_second": batch_throughput,
    }


# ============================================================
# SAVE BENCHMARK RESULTS
# ============================================================

def save_results(results: list[dict]) -> None:
    """
    Export benchmark results to CSV.
    """

    RESULTS_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    fieldnames = (
        "contracts",
        "individual_seconds",
        "batch_seconds",
        "speedup",
        "individual_options_per_second",
        "batch_options_per_second",
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
        writer.writerows(results)

    print()
    print(f"Results saved to: {RESULTS_PATH}")


# ============================================================
# MAIN
# ============================================================

def main() -> None:
    """
    Run all workloads and export the results.
    """

    print()
    print("=" * 70)
    print("FASTAPI BATCH GREEKS PERFORMANCE BENCHMARK")
    print("=" * 70)

    print(f"Repeated measurements: {REPEATS}")
    print(f"Random seed: {RANDOM_SEED}")

    results = []

    # Use one TestClient for the entire benchmark.
    with TestClient(app) as client:

        for count in WORKLOAD_SIZES:

            result = benchmark_workload(
                client,
                count,
            )

            results.append(result)

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
            f"Individual: {result['individual_seconds']:.6f}s | "
            f"Batch: {result['batch_seconds']:.6f}s | "
            f"Speedup: {result['speedup']:.2f}x"
        )


if __name__ == "__main__":
    main()