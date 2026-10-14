"""Tests for independent transaction-ledger auditing."""

import pandas as pd

from app.backtesting.ledger_integrity import audit_ledger


def rankings():
    return pd.DataFrame(
        [
            {
                "Selection Date": "2024-01-02",
                "Rank": 1,
                "Ticker": "AAA",
            },
        ]
    )


def valid_ledger():
    return pd.DataFrame(
        [
            {
                "Date": "2024-01-03",
                "Ticker": "AAA",
                "Action": "BUY",
                "Shares": 10.0,
                "Execution Price": 100.0,
                "Trade Value": 1000.0,
                "Transaction Fee": 1.0,
                "Cash Before": 10000.0,
                "Cash After": 8999.0,
            },
            {
                "Date": "2024-02-01",
                "Ticker": "AAA",
                "Action": "SELL",
                "Shares": 10.0,
                "Execution Price": 110.0,
                "Trade Value": 1100.0,
                "Transaction Fee": 1.1,
                "Cash Before": 8999.0,
                "Cash After": 10097.9,
            },
        ]
    )


def test_valid_ledger_passes():
    result = audit_ledger(valid_ledger(), rankings())
    assert result.empty


def test_unauthorized_purchase_detected():
    ledger = valid_ledger()
    ledger.loc[0, "Ticker"] = "BBB"

    result = audit_ledger(ledger, rankings())

    assert "UNAUTHORIZED_BUY" in result["Issue"].tolist()


def test_trade_value_mismatch_detected():
    ledger = valid_ledger()
    ledger.loc[0, "Trade Value"] = 900.0

    result = audit_ledger(ledger, rankings())

    assert "TRADE_VALUE_MISMATCH" in result["Issue"].tolist()


def test_fee_mismatch_detected():
    ledger = valid_ledger()
    ledger.loc[0, "Transaction Fee"] = 10.0

    result = audit_ledger(ledger, rankings())

    assert "FEE_MISMATCH" in result["Issue"].tolist()


def test_cash_mismatch_detected():
    ledger = valid_ledger()
    ledger.loc[0, "Cash After"] = 5000.0

    result = audit_ledger(ledger, rankings())

    assert "CASH_MISMATCH" in result["Issue"].tolist()


def test_overselling_detected():
    ledger = valid_ledger()
    ledger.loc[1, "Shares"] = 20.0

    result = audit_ledger(ledger, rankings())

    assert "SELL_EXCEEDS_HOLDINGS" in result["Issue"].tolist()


def test_purchase_before_ranking_detected():
    ledger = valid_ledger()
    ledger.loc[0, "Date"] = "2024-01-01"

    result = audit_ledger(ledger, rankings())

    assert "NO_PRIOR_RANKING" in result["Issue"].tolist()
