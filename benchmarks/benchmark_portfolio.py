"""
Benchmark portfolio valuation, aggregate Greeks, and scenario analysis.

This benchmark measures the performance of the Quant Options Engine
portfolio analytics modules using reproducible synthetic option positions.

Benchmarks included:
1. Portfolio valuation and aggregate Greeks:
   - 100 positions
   - 1,000 positions
   - 10,000 positions

2. Portfolio scenario analysis:
   - 100 positions x 10 scenarios
   - 1,000 positions x 50 scenarios
   - 10,000 positions x 100 scenarios

Methodology:
- Deterministic synthetic inputs.
- One untimed warm-up execution.
- Five timed repetitions.
- Median execution time.
- Correctness checks outside timed sections.
- Results saved automatically to CSV.

Important:
These are local, in-process Python benchmarks.

They do not measure network latency, concurrent API throughput,
or real-world trading execution performance.
"""

import csv
import math
import statistics
import time
from pathlib import Path

import numpy as np

from app.pricing.portfolio import OptionPosition, PortfolioAnalytics
from app.pricing.scenario_analysis import (
    MarketScenario,
    PortfolioScenarioAnalysis,
)

# ============================================================
# BENCHMARK CONFIGURATION
# ============================================================

# Use a fixed seed so repeated runs generate identical inputs.
RANDOM_SEED = 42

# Number of timed repetitions per benchmark.
REPETITIONS = 5

# Portfolio sizes to benchmark.
PORTFOLIO_SIZES = (100, 1_000, 10_000)

# Portfolio/scenario combinations to benchmark.
SCENARIO_CONFIGURATIONS = (
    (100, 10),
    (1_000, 50),
    (10_000, 100),
)

# Store results alongside the project's existing benchmarks.
RESULTS_DIRECTORY = Path(__file__).resolve().parent / "results"

VALUATION_RESULTS_FILE = (
    RESULTS_DIRECTORY / "portfolio_valuation_comparison.csv"
)

SCENARIO_RESULTS_FILE = (
    RESULTS_DIRECTORY / "portfolio_scenario_comparison.csv"
)


# ============================================================
# GENERATE REPRODUCIBLE OPTION POSITIONS
# ============================================================

def generate_positions(count: int) -> list[OptionPosition]:
    """
    Generate a deterministic portfolio containing call and put options.

    All positions share the same underlying stock price because
    the current portfolio engine supports one underlying asset.

    Positions vary by:
    - Option type.
    - Long/short quantity.
    - Strike price.
    - Time to expiration.
    - Interest rate.
    - Volatility.
    - Dividend yield.

    The random generator is reset using the same seed each time,
    making benchmark inputs reproducible.
    """

    if count <= 0:
        raise ValueError("count must be positive.")

    rng = np.random.default_rng(RANDOM_SEED)

    # Shared underlying stock price.
    underlying_price = 100.0

    # Generate option parameters using NumPy.
    strikes = rng.uniform(70.0, 130.0, count)

    expirations = rng.uniform(0.10, 2.0, count)

    interest_rates = rng.uniform(0.01, 0.07, count)

    volatilities = rng.uniform(0.15, 0.60, count)

    dividend_yields = rng.uniform(0.0, 0.04, count)

    # Generate quantities from -10 to +10.
    quantities = rng.integers(-10, 11, count)

    # Replace zero quantities with one contract.
    quantities[quantities == 0] = 1

    # Alternate between calls and puts.
    option_types = (
        "call",
        "put",
    )

    positions = []

    for index in range(count):

        position = OptionPosition(
            option_type=option_types[index % 2],
            quantity=int(quantities[index]),
            S=underlying_price,
            K=float(strikes[index]),
            T=float(expirations[index]),
            r=float(interest_rates[index]),
            sigma=float(volatilities[index]),
            q=float(dividend_yields[index]),
            multiplier=100,
        )

        positions.append(position)

    return positions


# ============================================================
# GENERATE REPRODUCIBLE MARKET SCENARIOS
# ============================================================

def generate_scenarios(count: int) -> list[MarketScenario]:
    """
    Generate deterministic hypothetical market scenarios.

    Each scenario modifies:
    - Underlying stock price.
    - Annualized volatility.
    - Calendar time.

    Volatility shocks are restricted to a safe range so
    the resulting volatility remains nonnegative for
    every generated option position.
    """

    if count <= 0:
        raise ValueError("count must be positive.")

    rng = np.random.default_rng(RANDOM_SEED + 1)

    price_changes = rng.uniform(-20.0, 20.0, count)

    volatility_changes = rng.uniform(-0.10, 0.15, count)

    days_forward = rng.uniform(0.0, 30.0, count)

    scenarios = []

    for index in range(count):

        scenario = MarketScenario(
            name=f"Scenario {index + 1}",
            price_change_pct=float(price_changes[index]),
            volatility_change=float(volatility_changes[index]),
            days_forward=float(days_forward[index]),
        )

        scenarios.append(scenario)

    return scenarios


# ============================================================
# BENCHMARK TIMING HELPER
# ============================================================

def measure_median_execution_time(function) -> float:
    """
    Measure execution time using perf_counter().

    Procedure:
    1. Execute the function once without timing.
    2. Execute it five times while measuring elapsed time.
    3. Return the median elapsed time in seconds.

    The median reduces the effect of unusually slow runs.
    """

    # Warm up the Python interpreter and NumPy functions.
    function()

    execution_times = []

    for _ in range(REPETITIONS):

        start_time = time.perf_counter()

        function()

        elapsed_time = time.perf_counter() - start_time

        execution_times.append(elapsed_time)

    return statistics.median(execution_times)


# ============================================================
# VERIFY PORTFOLIO VALUATION RESULTS
# ============================================================

def verify_portfolio_report(
    report: dict,
    expected_position_count: int,
) -> None:
    """
    Verify the portfolio engine returned structurally valid results.

    Also verify that position-level values sum to
    the aggregate theoretical portfolio value.
    """

    assert report["position_count"] == expected_position_count

    assert len(report["positions"]) == expected_position_count

    # All reported portfolio risk metrics should be finite
    # for the generated non-expired, positive-volatility options.
    aggregate_fields = (
        "portfolio_value",
        "portfolio_delta",
        "portfolio_gamma",
        "portfolio_vega",
        "portfolio_theta",
        "portfolio_rho",
    )

    for field in aggregate_fields:

        assert math.isfinite(report[field]), (
            f"Non-finite portfolio result: {field}"
        )

    # Independently sum the position values.
    position_value_sum = math.fsum(
        position["position_value"]
        for position in report["positions"]
    )

    assert math.isclose(
        report["portfolio_value"],
        position_value_sum,
        rel_tol=1e-10,
        abs_tol=1e-6,
    ), "Portfolio value does not match position-level values."


# ============================================================
# VERIFY SCENARIO ANALYSIS RESULTS
# ============================================================

def verify_scenario_report(
    report: dict,
    expected_position_count: int,
    expected_scenario_count: int,
) -> None:
    """
    Verify scenario-analysis output consistency.

    Checks:
    - Correct number of scenarios.
    - Correct number of positions per scenario.
    - Finite theoretical values and P&L.
    - Scenario P&L equals shocked value minus original value.
    - Position-level P&L sums to portfolio-level scenario P&L.
    """

    assert report["position_count"] == expected_position_count

    assert report["scenario_count"] == expected_scenario_count

    assert len(report["scenarios"]) == expected_scenario_count

    original_value = report["original_portfolio_value"]

    assert math.isfinite(original_value)

    for scenario in report["scenarios"]:

        assert len(scenario["positions"]) == expected_position_count

        scenario_value = scenario["scenario_portfolio_value"]

        scenario_pnl = scenario["scenario_pnl"]

        assert math.isfinite(scenario_value)

        assert math.isfinite(scenario_pnl)

        assert math.isclose(
            scenario_pnl,
            scenario_value - original_value,
            rel_tol=1e-10,
            abs_tol=1e-6,
        ), "Scenario P&L does not match the value change."

        # Independently aggregate all position-level P&L.
        position_pnl_sum = math.fsum(
            position["position_pnl"]
            for position in scenario["positions"]
        )

        assert math.isclose(
            scenario_pnl,
            position_pnl_sum,
            rel_tol=1e-10,
            abs_tol=1e-6,
        ), "Scenario P&L does not match position-level P&L."


# ============================================================
# BENCHMARK 1: PORTFOLIO VALUATION AND GREEKS
# ============================================================

def benchmark_portfolio_valuation() -> list[dict]:
    """
    Benchmark complete portfolio valuation and aggregate Greeks.

    Each timed execution includes:
    - Vectorized Black-Scholes pricing.
    - Vectorized Greeks calculations.
    - Long/short exposure aggregation.
    - Construction of the complete position-level report.

    Portfolio construction is excluded from the timed section.
    """

    print()
    print("=" * 76)
    print("PORTFOLIO VALUATION AND GREEKS BENCHMARK")
    print("=" * 76)

    results = []

    for position_count in PORTFOLIO_SIZES:

        # Generate inputs outside the timed region.
        positions = generate_positions(position_count)

        portfolio = PortfolioAnalytics(positions)

        # Verify correctness before timing.
        report = portfolio.calculate()

        verify_portfolio_report(
            report=report,
            expected_position_count=position_count,
        )

        # Measure the complete analytics operation.
        median_seconds = measure_median_execution_time(
            portfolio.calculate
        )

        positions_per_second = (
            position_count / median_seconds
            if median_seconds > 0
            else float("inf")
        )

        result = {
            "position_count": position_count,
            "repetitions": REPETITIONS,
            "median_seconds": median_seconds,
            "positions_per_second": positions_per_second,
        }

        results.append(result)

        print(
            f"{position_count:>7,} positions | "
            f"{median_seconds:>10.6f} seconds | "
            f"{positions_per_second:>12,.0f} positions/sec"
        )

    return results


# ============================================================
# BENCHMARK 2: PORTFOLIO SCENARIO ANALYSIS
# ============================================================

def benchmark_portfolio_scenarios() -> list[dict]:
    """
    Benchmark portfolio repricing under multiple market scenarios.

    Each timed execution includes:
    - Scenario parameter construction.
    - Vectorized repricing of all scenario-position combinations.
    - Portfolio-level P&L calculations.
    - Position-level P&L reporting.

    Portfolio and scenario object construction is excluded.
    """

    print()
    print("=" * 76)
    print("PORTFOLIO SCENARIO ANALYSIS BENCHMARK")
    print("=" * 76)

    results = []

    for position_count, scenario_count in SCENARIO_CONFIGURATIONS:

        positions = generate_positions(position_count)

        portfolio = PortfolioAnalytics(positions)

        scenarios = generate_scenarios(scenario_count)

        analysis = PortfolioScenarioAnalysis(
            portfolio=portfolio,
            scenarios=scenarios,
        )

        # Verify the result before timing.
        report = analysis.calculate()

        verify_scenario_report(
            report=report,
            expected_position_count=position_count,
            expected_scenario_count=scenario_count,
        )

        # Measure scenario calculation and report generation.
        median_seconds = measure_median_execution_time(
            analysis.calculate
        )

        # One scenario-position combination represents
        # one hypothetical option repricing.
        combination_count = position_count * scenario_count

        combinations_per_second = (
            combination_count / median_seconds
            if median_seconds > 0
            else float("inf")
        )

        result = {
            "position_count": position_count,
            "scenario_count": scenario_count,
            "scenario_position_combinations": combination_count,
            "repetitions": REPETITIONS,
            "median_seconds": median_seconds,
            "combinations_per_second": combinations_per_second,
        }

        results.append(result)

        print(
            f"{position_count:>7,} positions x "
            f"{scenario_count:>3,} scenarios | "
            f"{median_seconds:>10.6f} seconds | "
            f"{combinations_per_second:>12,.0f} combinations/sec"
        )

    return results


# ============================================================
# SAVE RESULTS TO CSV
# ============================================================

def save_results_to_csv(
    results: list[dict],
    output_path: Path,
) -> None:
    """
    Save benchmark measurements in a CSV file.

    CSV files allow benchmark results to be:
    - Tracked in Git.
    - Compared across future engine versions.
    - Imported into pandas or Excel.
    - Referenced in the project's README.
    """

    if not results:
        raise ValueError("Cannot save empty benchmark results.")

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with output_path.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as csv_file:

        writer = csv.DictWriter(
            csv_file,
            fieldnames=list(results[0].keys()),
        )

        writer.writeheader()

        writer.writerows(results)


# ============================================================
# MAIN BENCHMARK EXECUTION
# ============================================================

def main() -> None:
    """
    Run all portfolio benchmarks and save their results.
    """

    print("=" * 76)
    print("QUANT OPTIONS ENGINE - PORTFOLIO BENCHMARKS")
    print("=" * 76)

    print(f"Random seed: {RANDOM_SEED}")
    print(f"Timed repetitions: {REPETITIONS}")

    # Benchmark portfolio pricing and risk aggregation.
    valuation_results = benchmark_portfolio_valuation()

    save_results_to_csv(
        results=valuation_results,
        output_path=VALUATION_RESULTS_FILE,
    )

    # Benchmark scenario analysis.
    scenario_results = benchmark_portfolio_scenarios()

    save_results_to_csv(
        results=scenario_results,
        output_path=SCENARIO_RESULTS_FILE,
    )

    print()
    print("=" * 76)
    print("BENCHMARK COMPLETE")
    print("=" * 76)

    print()
    print("Saved valuation results to:")
    print(VALUATION_RESULTS_FILE)

    print()
    print("Saved scenario results to:")
    print(SCENARIO_RESULTS_FILE)


if __name__ == "__main__":
    main()