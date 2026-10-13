"""Ensure research exports validation predictions only."""

from unittest.mock import patch

import numpy as np
import pandas as pd

from app.forecasting.research_data import ResearchDataResult
from app.forecasting.research_runner import run_research
from app.forecasting.research_universe import ResearchStock


def test_research_preserves_only_validation_predictions():
    prices = pd.Series(
        np.linspace(100, 200, 1200),
        index=pd.bdate_range("2020-01-01", periods=1200),
    )

    data = ResearchDataResult(
        ticker="TEST",
        close=prices,
        status="Valid",
        observations=len(prices),
        start_date="2020-01-01",
        end_date="2024-08-06",
        missing_prices=0,
        duplicate_dates=0,
        invalid_prices=0,
        error=None,
    )

    predictions = pd.DataFrame(
        {
            "Forecast Index": [400, 405, 410],
            "Horizon": [5, 5, 5],
            "Research Period": [
                "Training",
                "Validation",
                "Test",
            ],
            "Actual Up": [1, 0, 1],
            "Historical Probability": [0.5, 0.4, 0.9],
            "ML Probability": [0.5, 0.3, 0.9],
        }
    )

    with (
        patch(
            "app.forecasting.research_runner.download_research_prices",
            return_value=data,
        ),
        patch(
            "app.forecasting.research_runner.ml_walk_forward_predictions",
            return_value=predictions,
        ),
    ):
        result = run_research(
            (ResearchStock("TEST", "Technology"),)
        )

    assert result.predictions is not None
    assert len(result.predictions) == 1

    row = result.predictions.iloc[0]

    assert row["Stock"] == "TEST"
    assert row["Sector"] == "Technology"
    assert row["Forecast Index"] == 405
    assert row["Research Period"] == "Validation"
    assert row["Actual Up"] == 0
    assert row["ML Probability"] == 0.3
    assert "Ensemble Probability" in result.predictions
