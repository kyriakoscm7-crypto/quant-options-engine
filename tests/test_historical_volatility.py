"""Historical volatility computation uses uploaded prices, never live feeds."""
from datetime import date, timedelta

import numpy as np
import pandas as pd
import pytest

from app.visualization.historical_volatility import (
    historical_volatility_from_csv,
    latest_hv,
)


def sample_csv(n=100):
    days = pd.bdate_range("2026-01-01", periods=n)
    # Deterministic alternating returns give a nonzero realized volatility.
    price = 100 * np.exp(np.cumsum(np.where(np.arange(n) % 2, 0.012, -0.009)))
    frame = pd.DataFrame({"Date": days.strftime("%Y-%m-%d"), "Close": price})
    return frame.to_csv(index=False).encode()


def test_rolling_hv_from_explicit_adjusted_price_csv():
    frame = historical_volatility_from_csv(sample_csv())
    assert len(frame) == 100
    assert frame["HV20"].iloc[:20].isna().all()
    assert frame["HV60"].iloc[:60].isna().all()
    assert 0 < latest_hv(frame, 20) < 100
    assert 0 < latest_hv(frame, 60) < 100
    assert frame["Date"].iloc[-1].year == 2026


def test_insufficient_history_reports_unavailable_sixty_day():
    frame = historical_volatility_from_csv(sample_csv(25))
    assert latest_hv(frame, 20) is not None
    assert latest_hv(frame, 60) is None


@pytest.mark.parametrize("contents", [
    b"", b"Ticker,Price\\nAAPL,100", b"Date,Close\\n2026-01-01,0",
    b"Date,Close\\n2026-01-01,-10", b"Date,Close\\n2026-01-01,nonsense",
    b"x" * 2000001,
])
def test_rejects_invalid_csv(contents):
    with pytest.raises(ValueError):
        historical_volatility_from_csv(contents)


def test_duplicate_and_out_of_order_dates_rejected():
    frame = pd.read_csv(pd.io.common.BytesIO(sample_csv()))
    frame.loc[20, "Date"] = frame.loc[19, "Date"]
    with pytest.raises(ValueError, match="Duplicate"):
        historical_volatility_from_csv(frame.to_csv(index=False).encode())
    frame = pd.read_csv(pd.io.common.BytesIO(sample_csv()))
    frame.loc[20, "Date"] = "2025-12-30"
    with pytest.raises(ValueError, match="Sort"):
        historical_volatility_from_csv(frame.to_csv(index=False).encode())
