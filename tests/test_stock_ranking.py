"""
Deterministic tests for the quantitative stock-ranking engine.

These tests verify factor scoring, weighted rankings,
missing-data handling, and input validation.

No internet connection or live market data is required.
"""

import numpy as np
import pandas as pd
import pytest

from app.market_data.stock_ranking import (
    DEFAULT_RANKING_FACTORS,
    RANK_COLUMN,
    RANKING_STATUS_COLUMN,
    SCORE_COLUMN,
    RankingFactor,
    calculate_factor_scores,
    rank_stocks,
    validate_ranking_factors,
)


def make_scan_results() -> pd.DataFrame:
    """Create a small, deterministic market scan."""

    return pd.DataFrame(
        {
            "Ticker": ["AAPL", "MSFT", "NVDA"],
            "Status": ["OK", "OK", "OK"],
            "1M Momentum (%)": [10.0, 5.0, 0.0],
            "3M Momentum (%)": [20.0, 10.0, 0.0],
            "Relative to SPY (%)": [15.0, 5.0, -5.0],
            "Annualized Volatility (%)": [20.0, 30.0, 40.0],
            "Maximum Drawdown (%)": [-10.0, -20.0, -30.0],
        }
    )


# ============================================================
# FACTOR CONFIGURATION
# ============================================================


def test_default_weights_sum_to_one():
    total = sum(
        factor.weight
        for factor in DEFAULT_RANKING_FACTORS
    )

    assert total == pytest.approx(1.0)


def test_default_factors_are_valid():
    validate_ranking_factors(DEFAULT_RANKING_FACTORS)


def test_rejects_empty_factors():
    with pytest.raises(ValueError):
        validate_ranking_factors(())


def test_rejects_list_instead_of_tuple():
    with pytest.raises(ValueError):
        validate_ranking_factors(
            [RankingFactor("Metric", 1.0, True)]
        )


def test_rejects_duplicate_factor_columns():
    factors = (
        RankingFactor("Metric", 0.5, True),
        RankingFactor("Metric", 0.5, False),
    )

    with pytest.raises(ValueError):
        validate_ranking_factors(factors)


@pytest.mark.parametrize(
    "weight",
    [
        0.0,
        -0.1,
        float("nan"),
        float("inf"),
        True,
    ],
)
def test_rejects_invalid_weights(weight):
    factors = (
        RankingFactor("Metric", weight, True),
    )

    with pytest.raises(ValueError):
        validate_ranking_factors(factors)


def test_rejects_weights_not_summing_to_one():
    factors = (
        RankingFactor("Metric A", 0.4, True),
        RankingFactor("Metric B", 0.4, True),
    )

    with pytest.raises(ValueError):
        validate_ranking_factors(factors)


def test_rejects_empty_factor_column():
    factors = (
        RankingFactor("", 1.0, True),
    )

    with pytest.raises(ValueError):
        validate_ranking_factors(factors)


def test_rejects_invalid_direction():
    factors = (
        RankingFactor("Metric", 1.0, "yes"),
    )

    with pytest.raises(ValueError):
        validate_ranking_factors(factors)


# ============================================================
# INDIVIDUAL FACTOR SCORES
# ============================================================


def test_higher_is_better():
    values = pd.Series([10.0, 20.0, 30.0])

    scores = calculate_factor_scores(
        values,
        higher_is_better=True,
    )

    assert scores.tolist() == [0.0, 50.0, 100.0]


def test_lower_is_better():
    values = pd.Series([10.0, 20.0, 30.0])

    scores = calculate_factor_scores(
        values,
        higher_is_better=False,
    )

    assert scores.tolist() == [100.0, 50.0, 0.0]


def test_negative_drawdowns():
    values = pd.Series([-30.0, -20.0, -10.0])

    scores = calculate_factor_scores(
        values,
        higher_is_better=True,
    )

    assert scores.tolist() == [0.0, 50.0, 100.0]


def test_factor_scores_with_ties():
    values = pd.Series([10.0, 10.0, 20.0])

    scores = calculate_factor_scores(values)

    assert scores.tolist() == [25.0, 25.0, 100.0]


def test_single_stock_receives_neutral_score():
    values = pd.Series([25.0])

    scores = calculate_factor_scores(values)

    assert scores.tolist() == [50.0]


def test_all_identical_values_receive_equal_scores():
    values = pd.Series([10.0, 10.0, 10.0])

    scores = calculate_factor_scores(values)

    assert scores.tolist() == [50.0, 50.0, 50.0]


def test_missing_values_remain_missing():
    values = pd.Series([10.0, np.nan, 30.0])

    scores = calculate_factor_scores(values)

    assert scores.iloc[0] == 0.0
    assert pd.isna(scores.iloc[1])
    assert scores.iloc[2] == 100.0


def test_infinite_values_remain_missing():
    values = pd.Series([10.0, np.inf, 30.0])

    scores = calculate_factor_scores(values)

    assert scores.iloc[0] == 0.0
    assert pd.isna(scores.iloc[1])
    assert scores.iloc[2] == 100.0


def test_all_missing_values():
    values = pd.Series([np.nan, np.nan])

    scores = calculate_factor_scores(values)

    assert scores.isna().all()


def test_factor_scores_preserve_index():
    values = pd.Series(
        [10.0, 20.0],
        index=["AAPL", "MSFT"],
    )

    scores = calculate_factor_scores(values)

    assert scores.index.tolist() == ["AAPL", "MSFT"]


def test_factor_scores_reject_non_series():
    with pytest.raises(ValueError):
        calculate_factor_scores([10.0, 20.0])


def test_factor_scores_reject_invalid_direction():
    with pytest.raises(ValueError):
        calculate_factor_scores(
            pd.Series([10.0, 20.0]),
            higher_is_better="yes",
        )


# ============================================================
# COMPLETE STOCK RANKINGS
# ============================================================


def test_rank_stocks_orders_best_to_worst():
    results = rank_stocks(make_scan_results())

    assert results["Ticker"].tolist() == [
        "AAPL",
        "MSFT",
        "NVDA",
    ]


def test_rank_stocks_expected_scores():
    results = rank_stocks(make_scan_results())

    assert results[SCORE_COLUMN].tolist() == [
        100.0,
        50.0,
        0.0,
    ]


def test_rank_stocks_expected_ranks():
    results = rank_stocks(make_scan_results())

    assert results[RANK_COLUMN].tolist() == [
        1,
        2,
        3,
    ]


def test_rank_stocks_statuses():
    results = rank_stocks(make_scan_results())

    assert results[RANKING_STATUS_COLUMN].tolist() == [
        "Ranked",
        "Ranked",
        "Ranked",
    ]


def test_rank_stocks_does_not_modify_input():
    original = make_scan_results()
    snapshot = original.copy(deep=True)

    rank_stocks(original)

    pd.testing.assert_frame_equal(
        original,
        snapshot,
    )


def test_rank_stocks_excludes_failed_scans():
    scan = make_scan_results()

    scan.loc[1, "Status"] = "ERROR: Download failed"

    results = rank_stocks(scan)

    failed = results.loc[
        results["Ticker"] == "MSFT"
    ].iloc[0]

    assert pd.isna(failed[SCORE_COLUMN])
    assert pd.isna(failed[RANK_COLUMN])
    assert failed[RANKING_STATUS_COLUMN] == "Scan unavailable"


def test_rank_stocks_excludes_missing_metrics():
    scan = make_scan_results()

    scan.loc[1, "3M Momentum (%)"] = np.nan

    results = rank_stocks(scan)

    missing = results.loc[
        results["Ticker"] == "MSFT"
    ].iloc[0]

    assert pd.isna(missing[SCORE_COLUMN])
    assert missing[RANKING_STATUS_COLUMN] == "Missing required metrics"


def test_rank_stocks_excludes_infinite_metrics():
    scan = make_scan_results()

    scan.loc[1, "Annualized Volatility (%)"] = np.inf

    results = rank_stocks(scan)

    missing = results.loc[
        results["Ticker"] == "MSFT"
    ].iloc[0]

    assert pd.isna(missing[SCORE_COLUMN])


def test_rank_stocks_unranked_rows_appear_last():
    scan = make_scan_results()

    scan.loc[0, "Status"] = "ERROR"

    results = rank_stocks(scan)

    assert results["Ticker"].iloc[-1] == "AAPL"


def test_rank_stocks_single_eligible_stock():
    scan = make_scan_results().iloc[[0]].copy()

    results = rank_stocks(scan)

    assert results.loc[0, SCORE_COLUMN] == 50.0
    assert results.loc[0, RANK_COLUMN] == 1


def test_rank_stocks_all_failed():
    scan = make_scan_results()

    scan["Status"] = "ERROR"

    results = rank_stocks(scan)

    assert results[SCORE_COLUMN].isna().all()
    assert results[RANK_COLUMN].isna().all()


def test_rank_stocks_tied_scores_share_rank():
    scan = make_scan_results()

    scan.loc[1, scan.columns.difference(["Ticker"])] = (
        scan.loc[0, scan.columns.difference(["Ticker"])].to_numpy()
    )

    results = rank_stocks(scan)

    aapl = results.loc[
        results["Ticker"] == "AAPL"
    ].iloc[0]

    msft = results.loc[
        results["Ticker"] == "MSFT"
    ].iloc[0]

    assert aapl[SCORE_COLUMN] == msft[SCORE_COLUMN]
    assert aapl[RANK_COLUMN] == msft[RANK_COLUMN]


def test_rank_stocks_ties_sort_alphabetically():
    scan = make_scan_results()

    scan.loc[1, scan.columns.difference(["Ticker"])] = (
        scan.loc[0, scan.columns.difference(["Ticker"])].to_numpy()
    )

    results = rank_stocks(scan)

    assert results["Ticker"].tolist()[:2] == [
        "AAPL",
        "MSFT",
    ]


def test_rank_stocks_custom_factors():
    scan = make_scan_results()

    factors = (
        RankingFactor(
            column="1M Momentum (%)",
            weight=1.0,
            higher_is_better=True,
        ),
    )

    results = rank_stocks(
        scan,
        factors=factors,
    )

    assert results[SCORE_COLUMN].tolist() == [
        100.0,
        50.0,
        0.0,
    ]


def test_rank_stocks_custom_lower_is_better():
    scan = make_scan_results()

    factors = (
        RankingFactor(
            column="Annualized Volatility (%)",
            weight=1.0,
            higher_is_better=False,
        ),
    )

    results = rank_stocks(
        scan,
        factors=factors,
    )

    assert results["Ticker"].tolist() == [
        "AAPL",
        "MSFT",
        "NVDA",
    ]


def test_rank_stocks_rejects_missing_columns():
    scan = make_scan_results().drop(
        columns=["3M Momentum (%)"]
    )

    with pytest.raises(ValueError):
        rank_stocks(scan)


def test_rank_stocks_rejects_non_dataframe():
    with pytest.raises(ValueError):
        rank_stocks([])


def test_rank_stocks_empty_dataframe():
    scan = make_scan_results().iloc[0:0].copy()

    results = rank_stocks(scan)

    assert results.empty
    assert SCORE_COLUMN in results.columns
    assert RANK_COLUMN in results.columns
    assert RANKING_STATUS_COLUMN in results.columns


def test_rank_stocks_preserves_original_columns():
    scan = make_scan_results()

    scan["Extra Information"] = ["A", "B", "C"]

    results = rank_stocks(scan)

    assert "Extra Information" in results.columns


def test_rank_stocks_scores_within_bounds():
    results = rank_stocks(make_scan_results())

    scores = results[SCORE_COLUMN].dropna()

    assert scores.between(0.0, 100.0).all()
    