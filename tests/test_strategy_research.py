"""Offline strategy research engine must be deterministic and avoid lookahead."""

import numpy as np
import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest

from dashboard.demo_showcase import synthetic_history
from dashboard.strategy_research import (
    backtest_stats,
    run_strategy_backtest,
)


def test_strategy_is_reproducible_and_self_consistent():
    history = synthetic_history("ORION")
    first = run_strategy_backtest(history, 20, 100, 5)
    second = run_strategy_backtest(history, 20, 100, 5)
    pd.testing.assert_frame_equal(first, second)
    assert len(first) == len(history) - 100
    assert first["Position"].isin([0.0, 1.0]).all()
    assert np.isfinite(first.select_dtypes("number").to_numpy()).all()
    assert (first[["Strategy value", "Buy-and-hold value"]] > 0).all().all()


def test_strategy_signal_uses_prior_day_only():
    frame = synthetic_history("CEDAR")
    initial = run_strategy_backtest(frame, 10, 90)
    changed = frame.copy()
    # Changing the most recent day's close must not change the position
    # used for the most recent day's return.
    changed.iloc[-1, changed.columns.get_loc("Close")] *= 3
    changed_result = run_strategy_backtest(changed, 10, 90)
    assert changed_result["Position"].iloc[-1] == initial["Position"].iloc[-1]


def test_more_fees_cannot_increase_strategy_value():
    history = synthetic_history("QUARTZ")
    cheap = run_strategy_backtest(history, 15, 110, 0)
    costly = run_strategy_backtest(history, 15, 110, 25)
    assert costly["Strategy value"].iloc[-1] <= cheap["Strategy value"].iloc[-1]
    assert backtest_stats(cheap)["max_drawdown_pct"] <= 0
    assert backtest_stats(cheap)["time_in_market_pct"] >= 0


@pytest.mark.parametrize("fast,slow,fee", [
    (0, 100, 5), (100, 100, 5), (110, 100, 5),
    (20, 300, 5), (20, 100, float("nan")),
    (20, 100, -1),
])
def test_strategy_rejects_invalid_controls(fast, slow, fee):
    with pytest.raises(ValueError):
        run_strategy_backtest(synthetic_history("ORION"), fast, slow, fee)


def test_strategy_page_renders_without_market_provider_calls(monkeypatch):
    import app.market_data.stock_history as stock_history
    monkeypatch.setattr(
        stock_history, "fetch_stock_history",
        lambda *a, **kw: (_ for _ in ()).throw(
            AssertionError("No market data fetch permitted")
        ),
    )
    app = AppTest.from_string(
        "from dashboard.strategy_research import render_strategy_research\n"
        "render_strategy_research()\n"
    ).run(timeout=45)
    assert not app.exception, [str(e.message) for e in app.exception]
    assert any("Synthetic market experiment" in i.value for i in app.info)
