"""
Automated tests for the interactive volatility smile visualization.

These tests verify that:
- Valid market data produces a Plotly figure.
- Strike prices and implied volatilities are plotted correctly.
- Unsorted market data is sorted before plotting.
- The underlying stock price is displayed.
- Bid, ask, and expiration data are included in tooltips.
- Input parameters are forwarded to the market-data client.
- Empty market data raises an appropriate error.

All Yahoo Finance data is mocked, so no internet connection is needed.
"""

from unittest.mock import patch

import pandas as pd
import plotly.graph_objects as go
import pytest

from app.visualization.volatility_smile import create_volatility_smile

# ============================================================
# TEST HELPERS
# ============================================================


def make_mock_option_data():
    """
    Create a small, realistic options dataset.

    The strike prices are deliberately unsorted so that
    we can verify the visualization sorts them correctly.
    """

    return pd.DataFrame(
        [
            {
                "Strike": 510.0,
                "ImpliedVolatility": 22.0,
                "UnderlyingPrice": 500.0,
                "Bid": 15.0,
                "Ask": 16.0,
                "Expiration": "2027-01-15",
            },
            {
                "Strike": 490.0,
                "ImpliedVolatility": 24.0,
                "UnderlyingPrice": 500.0,
                "Bid": 20.0,
                "Ask": 21.0,
                "Expiration": "2027-01-15",
            },
            {
                "Strike": 500.0,
                "ImpliedVolatility": 20.0,
                "UnderlyingPrice": 500.0,
                "Bid": 18.0,
                "Ask": 19.0,
                "Expiration": "2027-01-15",
            },
        ]
    )


# ============================================================
# BASIC FIGURE TESTS
# ============================================================


def test_create_volatility_smile_returns_plotly_figure():
    """
    Valid option data should produce a Plotly Figure.
    """

    with patch(
        "app.visualization.volatility_smile.fetch_option_chain",
        return_value=make_mock_option_data(),
    ):
        figure = create_volatility_smile()

    assert isinstance(figure, go.Figure)


def test_volatility_smile_contains_one_trace():
    """
    The volatility smile should contain one scatter trace.
    """

    with patch(
        "app.visualization.volatility_smile.fetch_option_chain",
        return_value=make_mock_option_data(),
    ):
        figure = create_volatility_smile()

    assert len(figure.data) == 1

    assert isinstance(figure.data[0], go.Scatter)


def test_volatility_smile_sorts_strikes():
    """
    Strike prices should appear in ascending order.
    """

    with patch(
        "app.visualization.volatility_smile.fetch_option_chain",
        return_value=make_mock_option_data(),
    ):
        figure = create_volatility_smile()

    assert list(figure.data[0].x) == [
        490.0,
        500.0,
        510.0,
    ]


def test_volatility_smile_plots_correct_volatilities():
    """
    Implied volatilities must match their sorted strikes.
    """

    with patch(
        "app.visualization.volatility_smile.fetch_option_chain",
        return_value=make_mock_option_data(),
    ):
        figure = create_volatility_smile()

    assert list(figure.data[0].y) == [
        24.0,
        20.0,
        22.0,
    ]


def test_volatility_smile_uses_lines_and_markers():
    """
    The chart should display both lines and data markers.
    """

    with patch(
        "app.visualization.volatility_smile.fetch_option_chain",
        return_value=make_mock_option_data(),
    ):
        figure = create_volatility_smile()

    assert figure.data[0].mode == "lines+markers"


def test_volatility_smile_trace_name():
    """
    Verify the chart uses the expected legend label.
    """

    with patch(
        "app.visualization.volatility_smile.fetch_option_chain",
        return_value=make_mock_option_data(),
    ):
        figure = create_volatility_smile()

    assert figure.data[0].name == "Call Implied Volatility"


# ============================================================
# FINANCIAL DATA TESTS
# ============================================================


def test_volatility_smile_stock_price_reference_line():
    """
    The chart should display a vertical reference line
    at the current underlying stock price.
    """

    with patch(
        "app.visualization.volatility_smile.fetch_option_chain",
        return_value=make_mock_option_data(),
    ):
        figure = create_volatility_smile()

    assert len(figure.layout.shapes) >= 1

    reference_line = figure.layout.shapes[0]

    assert reference_line.x0 == 500.0
    assert reference_line.x1 == 500.0


def test_volatility_smile_contains_bid_ask_tooltips():
    """
    Verify that each plotted option contains bid, ask,
    and expiration data for interactive tooltips.
    """

    with patch(
        "app.visualization.volatility_smile.fetch_option_chain",
        return_value=make_mock_option_data(),
    ):
        figure = create_volatility_smile()

    custom_data = figure.data[0].customdata

    assert len(custom_data) == 3

    # First row corresponds to the lowest strike ($490).
    assert custom_data[0][0] == 20.0
    assert custom_data[0][1] == 21.0
    assert custom_data[0][2] == "2027-01-15"


def test_volatility_smile_hovertemplate():
    """
    The hover tooltip should describe important
    financial information.
    """

    with patch(
        "app.visualization.volatility_smile.fetch_option_chain",
        return_value=make_mock_option_data(),
    ):
        figure = create_volatility_smile()

    hovertemplate = figure.data[0].hovertemplate

    assert "Strike" in hovertemplate
    assert "Implied Volatility" in hovertemplate
    assert "Bid" in hovertemplate
    assert "Ask" in hovertemplate
    assert "Expiration" in hovertemplate


# ============================================================
# CHART APPEARANCE TESTS
# ============================================================


def test_volatility_smile_chart_title():
    """
    The chart title should contain the ticker symbol.
    """

    with patch(
        "app.visualization.volatility_smile.fetch_option_chain",
        return_value=make_mock_option_data(),
    ):
        figure = create_volatility_smile(
            ticker_symbol="QQQ"
        )

    assert "QQQ" in figure.layout.title.text

    assert "Implied Volatility by Strike" in figure.layout.title.text


def test_volatility_smile_axis_labels():
    """
    Both axes should have appropriate financial labels.
    """

    with patch(
        "app.visualization.volatility_smile.fetch_option_chain",
        return_value=make_mock_option_data(),
    ):
        figure = create_volatility_smile()

    assert figure.layout.xaxis.title.text == "Strike Price ($)"

    assert figure.layout.yaxis.title.text == "Implied Volatility (%)"


def test_volatility_smile_dark_theme():
    """
    The chart should use Plotly's dark theme.
    """

    with patch(
        "app.visualization.volatility_smile.fetch_option_chain",
        return_value=make_mock_option_data(),
    ):
        figure = create_volatility_smile()

    assert figure.layout.template is not None

    assert figure.layout.height == 650


# ============================================================
# PARAMETER FORWARDING TESTS
# ============================================================


def test_volatility_smile_forwards_parameters():
    """
    Verify that user-supplied parameters are forwarded
    to the market-data function correctly.
    """

    with patch(
        "app.visualization.volatility_smile.fetch_option_chain",
        return_value=make_mock_option_data(),
    ) as mock_fetch:
        create_volatility_smile(
            ticker_symbol="QQQ",
            risk_free_rate=0.05,
            dividend_yield=0.01,
            minimum_days_to_expiry=14,
        )

    mock_fetch.assert_called_once_with(
        ticker_symbol="QQQ",
        risk_free_rate=0.05,
        dividend_yield=0.01,
        minimum_days_to_expiry=14,
    )


# ============================================================
# ERROR HANDLING TESTS
# ============================================================


def test_volatility_smile_rejects_empty_data():
    """
    Empty market data should raise a clear error.
    """

    with (
        patch(
            "app.visualization.volatility_smile.fetch_option_chain",
            return_value=pd.DataFrame(),
        ),
        pytest.raises(
            RuntimeError,
            match="No valid option quotes available for visualization",
        ),
    ):
        create_volatility_smile()


def test_volatility_smile_handles_single_option():
    """
    The chart should still work when only one
    valid option quote is available.
    """

    single_option = make_mock_option_data().iloc[[0]]

    with patch(
        "app.visualization.volatility_smile.fetch_option_chain",
        return_value=single_option,
    ):
        figure = create_volatility_smile()

    assert len(figure.data[0].x) == 1
    assert len(figure.data[0].y) == 1


def test_volatility_smile_does_not_modify_input_dataframe():
    """
    The visualization should not change the original
    DataFrame returned by the market-data client.
    """

    original_data = make_mock_option_data()

    original_strikes = original_data["Strike"].tolist()

    with patch(
        "app.visualization.volatility_smile.fetch_option_chain",
        return_value=original_data,
    ):
        create_volatility_smile()

    assert original_data["Strike"].tolist() == original_strikes
    