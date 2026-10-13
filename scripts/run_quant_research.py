"""Command-line interface for reproducible validation research."""

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path

from app.forecasting.research_reliability import analyze_research_reliability
from app.forecasting.research_runner import run_research
from app.forecasting.research_universe import (
    ResearchStock,
    get_research_universe,
)


def main():
    parser = argparse.ArgumentParser(
        description="Run Quant Intelligence validation research."
    )

    parser.add_argument(
        "--stocks",
        nargs="+",
        default=["AAPL"],
        help="Stock tickers to evaluate.",
    )

    parser.add_argument(
        "--years",
        type=int,
        default=15,
    )

    parser.add_argument(
        "--step",
        type=int,
        default=5,
    )

    parser.add_argument(
        "--output",
        default="research_results",
    )

    args = parser.parse_args()

    if args.years < 1:
        parser.error("--years must be positive")

    if args.step < 1:
        parser.error("--step must be positive")

    universe = {
        stock.ticker: stock
        for stock in get_research_universe()
    }

    requested = [ticker.upper() for ticker in args.stocks]

    if len(requested) != len(set(requested)):
        parser.error("Duplicate tickers are not allowed")

    stocks = tuple(
        universe.get(ticker, ResearchStock(ticker, "Other"))
        for ticker in requested
    )

    print("\nQUANT INTELLIGENCE — AUTOMATED RESEARCH")
    print("=" * 50)
    print("Stocks:", ", ".join(requested))
    print("Years:", args.years)
    print("Step:", args.step)
    print("Research period: VALIDATION ONLY")
    print("=" * 50)

    result = run_research(
        stocks=stocks,
        years=args.years,
        step=args.step,
    )

    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=True)

    scores_path = output / "validation_scores.csv"
    quality_path = output / "data_quality.csv"
    metadata_path = output / "experiment_metadata.json"

    if result.predictions is None:
        raise ValueError("Research runner did not return predictions.")

    validation = result.predictions.copy()

    if not validation.empty:
        if "Research Period" not in validation.columns:
            raise ValueError("Missing research-period labels.")

        if not validation["Research Period"].eq("Validation").all():
            raise ValueError("Non-validation predictions cannot be exported.")

    reliability = analyze_research_reliability(
        validation,
        step_days=args.step,
        bootstrap_samples=2000,
        random_seed=42,
    ) if not validation.empty else None

    predictions_path = output / "validation_predictions.csv"
    reliability_path = output / "statistical_reliability.csv"

    result.scores.to_csv(scores_path, index=False)
    result.data_quality.to_csv(quality_path, index=False)
    validation.to_csv(predictions_path, index=False)

    if reliability is not None:
        reliability.to_csv(reliability_path, index=False)

    metadata = {
        "project": "Quant Intelligence",
        "created_utc": datetime.now(UTC).isoformat(),
        "stocks": requested,
        "years": args.years,
        "step": args.step,
        "horizons": [1, 5, 20, 60],
        "ml_weight": 0.25,
        "research_period": "Validation",
        "reserved_test_evaluated": False,
        "score_rows": len(result.scores),
    }

    metadata_path.write_text(
        json.dumps(metadata, indent=2) + "\n"
    )

    print("\nRESEARCH COMPLETE")
    print("=" * 50)

    if result.scores.empty:
        print("No validation scores were produced.")
    else:
        print(
            result.scores.sort_values(
                ["Stock", "Horizon", "Brier"]
            ).to_string(index=False)
        )

    print("\nDATA QUALITY")
    print(
        result.data_quality.to_string(index=False)
    )

    print("\nSaved reports:")
    print(scores_path)
    print(quality_path)
    print(predictions_path)

    if reliability is not None:
        print(reliability_path)

    print(metadata_path)


if __name__ == "__main__":
    main()
