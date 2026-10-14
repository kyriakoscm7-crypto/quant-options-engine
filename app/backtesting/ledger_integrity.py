"""Independent consistency checks for historical transaction ledgers."""

import math

import pandas as pd

REQUIRED_LEDGER_COLUMNS = {
    "Date",
    "Ticker",
    "Action",
    "Shares",
    "Execution Price",
    "Trade Value",
    "Transaction Fee",
    "Cash Before",
    "Cash After",
}

REQUIRED_RANKING_COLUMNS = {
    "Selection Date",
    "Rank",
    "Ticker",
}


def audit_ledger(
    ledger: pd.DataFrame,
    rankings: pd.DataFrame,
    transaction_cost: float = 0.001,
    tolerance: float = 1e-5,
) -> pd.DataFrame:
    """Return an issue report; an empty report means all checks passed.

    Assumes the supplied ledger is complete, chronologically ordered,
    and uses the same execution and fee conventions as the simulator.
    """
    missing_ledger = REQUIRED_LEDGER_COLUMNS - set(ledger.columns)
    missing_rankings = REQUIRED_RANKING_COLUMNS - set(rankings.columns)

    if missing_ledger:
        raise ValueError(
            f"Missing ledger columns: {sorted(missing_ledger)}"
        )

    if missing_rankings:
        raise ValueError(
            f"Missing ranking columns: {sorted(missing_rankings)}"
        )

    if not 0 <= transaction_cost < 1:
        raise ValueError("transaction_cost must be between 0 and 1.")

    if tolerance <= 0:
        raise ValueError("tolerance must be positive.")

    issues = []

    def report(row_number, issue, details):
        issues.append(
            {
                "Row": row_number,
                "Issue": issue,
                "Details": str(details),
            }
        )

    decisions = rankings.copy()
    decisions["Selection Date"] = pd.to_datetime(
        decisions["Selection Date"],
        errors="coerce",
    )

    if decisions["Selection Date"].isna().any():
        raise ValueError("Rankings contain invalid selection dates.")

    decisions["Rank"] = pd.to_numeric(
        decisions["Rank"],
        errors="coerce",
    )

    if (
        decisions["Rank"].isna().any()
        or (decisions["Rank"] < 1).any()
    ):
        raise ValueError("Rankings contain invalid ranks.")

    decisions = decisions.sort_values(
        ["Selection Date", "Rank"]
    )

    decision_dates = sorted(
        decisions["Selection Date"].unique()
    )

    allowed_by_date = {
        date: set(
            decisions.loc[
                (decisions["Selection Date"] == date)
                & (decisions["Rank"] <= 10),
                "Ticker",
            ]
        )
        for date in decision_dates
    }

    trades = ledger.copy()
    trades["Date"] = pd.to_datetime(
        trades["Date"],
        errors="coerce",
    )

    if trades["Date"].isna().any():
        raise ValueError("Ledger contains invalid trade dates.")

    if not trades["Date"].is_monotonic_increasing:
        raise ValueError("Ledger must be chronologically ordered.")

    shares_held = {}
    previous_cash_after = None

    numeric_columns = [
        "Shares",
        "Execution Price",
        "Trade Value",
        "Transaction Fee",
        "Cash Before",
        "Cash After",
    ]

    for row_number, row in enumerate(
        trades.to_dict("records"),
        start=1,
    ):
        date = row["Date"]
        ticker = str(row["Ticker"])
        action = str(row["Action"])

        values = {}

        for column in numeric_columns:
            try:
                value = float(row[column])
            except (TypeError, ValueError):
                value = float("nan")

            values[column] = value

        if not all(
            math.isfinite(value)
            for value in values.values()
        ):
            report(row_number, "INVALID_NUMBER", ticker)
            continue

        shares = values["Shares"]
        price = values["Execution Price"]
        trade_value = values["Trade Value"]
        fee = values["Transaction Fee"]
        cash_before = values["Cash Before"]
        cash_after = values["Cash After"]

        if action not in {"BUY", "SELL"}:
            report(row_number, "INVALID_ACTION", action)
            continue

        if shares <= 0 or price <= 0 or trade_value <= 0:
            report(row_number, "INVALID_TRADE", ticker)
            continue

        if fee < 0:
            report(row_number, "NEGATIVE_FEE", ticker)

        if not math.isclose(
            trade_value,
            shares * price,
            rel_tol=1e-9,
            abs_tol=tolerance,
        ):
            report(row_number, "TRADE_VALUE_MISMATCH", ticker)

        if not math.isclose(
            fee,
            trade_value * transaction_cost,
            rel_tol=1e-9,
            abs_tol=tolerance,
        ):
            report(row_number, "FEE_MISMATCH", ticker)

        if previous_cash_after is not None and not math.isclose(
            cash_before,
            previous_cash_after,
            rel_tol=1e-9,
            abs_tol=tolerance,
        ):
            report(row_number, "CASH_DISCONTINUITY", ticker)

        if action == "BUY":
            eligible_dates = [
                decision_date
                for decision_date in decision_dates
                if decision_date < date
            ]

            if not eligible_dates:
                report(
                    row_number,
                    "NO_PRIOR_RANKING",
                    ticker,
                )
            else:
                latest_date = eligible_dates[-1]

                if ticker not in allowed_by_date[latest_date]:
                    report(
                        row_number,
                        "UNAUTHORIZED_BUY",
                        f"{ticker} on {date.date()}",
                    )

            expected_cash = cash_before - trade_value - fee

            shares_held[ticker] = (
                shares_held.get(ticker, 0.0) + shares
            )

        else:
            held = shares_held.get(ticker, 0.0)

            if shares > held + 1e-8:
                report(
                    row_number,
                    "SELL_EXCEEDS_HOLDINGS",
                    f"{ticker}: sold {shares}, held {held}",
                )

            shares_held[ticker] = held - shares

            expected_cash = cash_before + trade_value - fee

        if not math.isclose(
            cash_after,
            expected_cash,
            rel_tol=1e-9,
            abs_tol=tolerance,
        ):
            report(row_number, "CASH_MISMATCH", ticker)

        if cash_after < -tolerance:
            report(row_number, "NEGATIVE_CASH", ticker)

        previous_cash_after = cash_after

    return pd.DataFrame(
        issues,
        columns=["Row", "Issue", "Details"],
    )
