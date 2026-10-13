"""NYSE trading-session detection and market-data freshness utilities."""

from dataclasses import dataclass
from datetime import timedelta

import exchange_calendars as xcals
import pandas as pd

NYSE = xcals.get_calendar("XNYS")
DATA_FINALIZATION_DELAY = timedelta(minutes=30)


@dataclass(frozen=True)
class MarketSessionStatus:
    session_date: str
    market_close: pd.Timestamp
    checked_at: pd.Timestamp
    is_completed: bool
    is_current_session: bool
    status: str


def get_market_session_status(
    session_date: str | pd.Timestamp,
    checked_at: pd.Timestamp | None = None,
) -> MarketSessionStatus:
    """Classify a NYSE session using the official exchange calendar.

    A session is treated as completed only after its scheduled close
    plus a conservative data-finalization delay.

    This does not guarantee that the data provider has finalized its
    daily candle.
    """

    now = (
        pd.Timestamp.now(tz="UTC")
        if checked_at is None
        else pd.Timestamp(checked_at)
    )

    if now.tzinfo is None:
        raise ValueError("checked_at must be timezone-aware.")

    now = now.tz_convert("UTC")

    # A daily candle's Date is a trading-date label, not a
    # moment in time. Preserve its calendar date when removing
    # timezone information to avoid shifting UTC midnight
    # into the previous New York trading day.
    date = pd.Timestamp(session_date)

    if date.tzinfo is not None:
        date = date.tz_localize(None)

    date = date.normalize()

    if not NYSE.is_session(date):
        raise ValueError(
            f"{date.date()} is not an NYSE trading session."
        )

    close = NYSE.session_close(date)
    finalization_time = close + DATA_FINALIZATION_DELAY

    completed = now >= finalization_time

    local_today = now.tz_convert("America/New_York").date()
    current_session = date.date() == local_today

    if completed:
        status = "Completed"
    elif now < close:
        status = "In Progress / Not Yet Closed"
    else:
        status = "Awaiting Data Finalization"

    return MarketSessionStatus(
        session_date=date.date().isoformat(),
        market_close=close,
        checked_at=now,
        is_completed=completed,
        is_current_session=current_session,
        status=status,
    )
