"""Manually researched schedule facts, not a redistributed vendor calendar.

Only dates/times and identifiers are recorded; no article text or estimates.
See docs/ISSUER_CALENDAR.md for source review and update procedure.
"""
from datetime import date, timedelta

REVIEWED = date(2026, 11, 6)
EVENTS = (
    dict(symbol="TTD", company="The Trade Desk", day="2026-11-09", release="After US market close", call="5:00 p.m. ET", source="https://www.thetradedesk.com/press-room/the-trade-desk-announces-date-of-third-quarter-2026-financial-results-and-conference-call"),
    dict(symbol="CRWV", company="CoreWeave", day="2026-11-10", release="Release timing not specified", call="5:00 p.m. ET", source="https://investors.coreweave.com/news/news-details/2026/CoreWeave-Announces-Date-of-Third-Quarter-2026-Financial-Results-and-Conference-Call/default.aspx"),
    dict(symbol="AMAT", company="Applied Materials", day="2026-11-12", release="Release timing not specified", call="Time not recorded in reviewed source", source="https://investor.appliedmaterials.com/events"),
    dict(symbol="DIS", company="Walt Disney", day="2026-11-17", release="Release timing not specified", call="8:30 a.m. ET", source="https://investors.thewaltdisneycompany.com/events-and-presentations/event-details/2026/Disneys-Q4-FY26-Earnings-Results-Webcast-2026-r7J4pl6coY/default.aspx"),
    dict(symbol="HD", company="The Home Depot", day="2026-11-17", release="Release timing not specified", call="9:00 a.m. ET", source="https://ir.homedepot.com/events-and-presentations"),
    dict(symbol="TGT", company="Target", day="2026-11-18", release="Release timing not specified", call="8:00 a.m. ET", source="https://corporate.target.com/investors/events-presentations"),
    dict(symbol="HPQ", company="HP Inc.", day="2026-11-24", release="Release timing not specified", call="5:00 p.m. ET", source="https://investor.hp.com/news-events/news/news-details/2026/HP-Inc--to-Announce-Fourth-Quarter-Fiscal-2026-Earnings-on-November-24-2026-and-to-Attend-Upcoming-Investor-Conferences/default.aspx"),
)


def select_events(today, window="Next 30 days", query=""):
    """Inclusive Toronto-local date windows; past events never appear upcoming.

    Withhold the snapshot after 30 days rather than serving old confirmations.
    """
    if today < REVIEWED or today > REVIEWED + timedelta(days=30):
        return ()
    monday = today - timedelta(days=today.weekday())
    start, end = {
        "Next 30 days": (today, today + timedelta(days=29)),
        "This week": (today, monday + timedelta(days=6)),
        "Next week": (monday + timedelta(days=7), monday + timedelta(days=13)),
    }[window]
    query = query.strip().casefold()
    return tuple(e for e in EVENTS if start <= date.fromisoformat(e["day"]) <= end
                 and query in f"{e['symbol']} {e['company']}".casefold())
