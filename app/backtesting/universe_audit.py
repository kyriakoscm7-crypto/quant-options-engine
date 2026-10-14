"""Audit historical price coverage and stock eligibility.

Price coverage is not proof of historical exchange listing or
membership in a historically reconstructed investment universe.
"""

import pandas as pd


def audit_universe(
    histories: dict[str, pd.DataFrame],
    as_of: pd.Timestamp,
    minimum_observations: int = 252,
) -> pd.DataFrame:
    """Summarize price-history availability at a historical decision date."""
    if minimum_observations < 1:
        raise ValueError("minimum_observations must be positive.")

    as_of = pd.Timestamp(as_of)

    if pd.isna(as_of):
        raise ValueError("as_of must be a valid date.")

    records = []

    for ticker, history in sorted(histories.items()):
        if "Close" not in history.columns:
            records.append(
                {
                    "Ticker": ticker,
                    "First Price Date": pd.NaT,
                    "Last Price Date": pd.NaT,
                    "Observations By Date": 0,
                    "Has Prior Price": False,
                    "Sufficient History": False,
                }
            )
            continue

        dates = pd.to_datetime(history.index)

        closes = pd.to_numeric(
            history["Close"],
            errors="coerce",
        )

        valid = (
            pd.Series(dates <= as_of, index=history.index)
            & closes.notna()
            & (closes > 0)
        )

        available_dates = dates[valid.to_numpy()]

        count = len(available_dates)

        records.append(
            {
                "Ticker": ticker,
                "First Price Date": (
                    available_dates.min() if count else pd.NaT
                ),
                "Last Price Date": (
                    available_dates.max() if count else pd.NaT
                ),
                "Observations By Date": count,
                "Has Prior Price": count > 0,
                "Sufficient History": (
                    count >= minimum_observations
                ),
            }
        )

    return pd.DataFrame(records)
