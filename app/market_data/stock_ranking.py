"""
Transparent cross-sectional stock-ranking engine.

Ranks stocks using historical quantitative metrics produced by
the Quant Intelligence Market Scanner.

The ranking is descriptive, not predictive.

Important:
    - Scores depend on the selected stock universe.
    - Scores are not probabilities of future returns.
    - Weights are research assumptions, not optimized parameters.
    - Missing data makes a stock ineligible for ranking.
"""

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class RankingFactor:
    """Configuration for one quantitative ranking factor."""

    column: str
    weight: float
    higher_is_better: bool


DEFAULT_RANKING_FACTORS = (
    RankingFactor(
        column="1M Momentum (%)",
        weight=0.20,
        higher_is_better=True,
    ),
    RankingFactor(
        column="3M Momentum (%)",
        weight=0.25,
        higher_is_better=True,
    ),
    RankingFactor(
        column="Relative to SPY (%)",
        weight=0.25,
        higher_is_better=True,
    ),
    RankingFactor(
        column="Annualized Volatility (%)",
        weight=0.15,
        higher_is_better=False,
    ),
    RankingFactor(
        column="Maximum Drawdown (%)",
        weight=0.15,
        higher_is_better=True,
    ),
)

SCORE_COLUMN = "Quant Score"
RANK_COLUMN = "Quant Rank"
RANKING_STATUS_COLUMN = "Ranking Status"


def validate_ranking_factors(
    factors: tuple[RankingFactor, ...],
) -> None:
    """
    Validate factor definitions.

    Requirements:
        - At least one factor.
        - Unique column names.
        - Finite, strictly positive weights.
        - Weights sum to 1.
        - Valid higher_is_better flags.
    """

    if not isinstance(factors, tuple) or not factors:
        raise ValueError(
            "Ranking factors must be a non-empty tuple."
        )

    columns = []
    weights = []

    for factor in factors:
        if not isinstance(factor, RankingFactor):
            raise ValueError(
                "Each factor must be a RankingFactor."
            )

        if (
            not isinstance(factor.column, str)
            or not factor.column.strip()
        ):
            raise ValueError(
                "Factor column names must be non-empty strings."
            )

        if not isinstance(factor.higher_is_better, bool):
            raise ValueError(
                "higher_is_better must be a boolean."
            )

        if (
            isinstance(factor.weight, bool)
            or not isinstance(factor.weight, (int, float))
            or not np.isfinite(factor.weight)
            or factor.weight <= 0
        ):
            raise ValueError(
                "Factor weights must be finite positive numbers."
            )

        columns.append(factor.column)
        weights.append(float(factor.weight))

    if len(columns) != len(set(columns)):
        raise ValueError(
            "Ranking factor columns must be unique."
        )

    if not np.isclose(
        sum(weights),
        1.0,
        rtol=0,
        atol=1e-9,
    ):
        raise ValueError(
            "Ranking factor weights must sum to 1.0."
        )


def calculate_factor_scores(
    values: pd.Series,
    higher_is_better: bool = True,
) -> pd.Series:
    """
    Convert historical metric values into 0-100 factor scores.

    Uses average ranks for ties.

    Lowest rank -> 0.
    Highest rank -> 100.

    If only one valid value exists, its score is 50.

    Missing and non-finite values receive NaN.
    """

    if not isinstance(values, pd.Series):
        raise ValueError(
            "Values must be a pandas Series."
        )

    if not isinstance(higher_is_better, bool):
        raise ValueError(
            "higher_is_better must be a boolean."
        )

    numeric = pd.to_numeric(
        values,
        errors="coerce",
    )

    numeric = numeric.replace(
        [np.inf, -np.inf],
        np.nan,
    )

    valid = numeric.dropna()

    scores = pd.Series(
        np.nan,
        index=values.index,
        dtype=float,
    )

    count = len(valid)

    if count == 0:
        return scores

    if count == 1:
        scores.loc[valid.index] = 50.0
        return scores

    ranks = valid.rank(
        method="average",
        ascending=higher_is_better,
    )

    # With ascending=True, the largest metric receives
    # the highest rank and therefore the highest score.
    #
    # With ascending=False, the smallest metric receives
    # the highest rank and therefore the highest score.
    scores.loc[valid.index] = (
        (ranks - 1.0)
        / (count - 1.0)
        * 100.0
    )

    return scores


def rank_stocks(
    scan_results: pd.DataFrame,
    factors: tuple[RankingFactor, ...] = DEFAULT_RANKING_FACTORS,
) -> pd.DataFrame:
    """
    Rank stocks using weighted cross-sectional factor scores.

    Only rows with:
        - Status == "OK"
        - Valid observations for every configured factor

    are eligible for ranking.

    Ineligible rows remain in the output but receive:
        - Quant Score = NaN
        - Quant Rank = missing
        - Ranking Status explaining the issue

    Eligible stocks are sorted by descending Quant Score.
    Ticker breaks score ties alphabetically for display.

    Returns a new DataFrame without modifying the input.
    """

    if not isinstance(scan_results, pd.DataFrame):
        raise ValueError(
            "Scan results must be a pandas DataFrame."
        )

    validate_ranking_factors(factors)

    required_columns = {
        "Ticker",
        "Status",
        *(factor.column for factor in factors),
    }

    missing_columns = required_columns.difference(
        scan_results.columns
    )

    if missing_columns:
        raise ValueError(
            "Scan results are missing required columns: "
            f"{sorted(missing_columns)}"
        )

    result = scan_results.copy(deep=True)

    factor_columns = [
        factor.column
        for factor in factors
    ]

    # Convert metrics to numeric values in a separate
    # DataFrame so the original displayed data is preserved.
    metrics = result[
        factor_columns
    ].apply(
        pd.to_numeric,
        errors="coerce",
    )

    metrics = metrics.replace(
        [np.inf, -np.inf],
        np.nan,
    )

    valid_status = result["Status"].eq("OK")

    complete_metrics = metrics.notna().all(
        axis=1
    )

    eligible = (
        valid_status
        & complete_metrics
    )

    result[SCORE_COLUMN] = np.nan

    result[RANK_COLUMN] = pd.Series(
        pd.NA,
        index=result.index,
        dtype="Int64",
    )

    result[RANKING_STATUS_COLUMN] = (
        "Missing required metrics"
    )

    result.loc[
        ~valid_status,
        RANKING_STATUS_COLUMN,
    ] = "Scan unavailable"

    result.loc[
        eligible,
        RANKING_STATUS_COLUMN,
    ] = "Ranked"

    if eligible.any():
        eligible_metrics = metrics.loc[
            eligible
        ]

        weighted_score = pd.Series(
            0.0,
            index=eligible_metrics.index,
        )

        for factor in factors:
            factor_scores = calculate_factor_scores(
                eligible_metrics[factor.column],
                higher_is_better=factor.higher_is_better,
            )

            weighted_score = (
                weighted_score
                + factor_scores * factor.weight
            )

        result.loc[
            eligible,
            SCORE_COLUMN,
        ] = weighted_score.round(4)

        # Rank scores descending; equal scores share
        # the same numerical rank.
        ranks = weighted_score.rank(
            method="min",
            ascending=False,
        ).astype("Int64")

        result.loc[
            eligible,
            RANK_COLUMN,
        ] = ranks

    # Ranked stocks first, unranked stocks afterward.
    # Alphabetical ticker ordering makes ties deterministic.
    result = result.sort_values(
        by=[
            SCORE_COLUMN,
            "Ticker",
        ],
        ascending=[
            False,
            True,
        ],
        na_position="last",
        kind="stable",
    )

    return result.reset_index(
        drop=True
    )