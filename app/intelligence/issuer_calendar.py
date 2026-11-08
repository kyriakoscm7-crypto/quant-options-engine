"""Manually researched schedule facts, not a redistributed vendor calendar.

Only dates/times and identifiers are recorded; no article text or estimates.
See docs/ISSUER_CALENDAR.md for source review and update procedure.
"""
from datetime import date, timedelta

REVIEWED = date(2026, 11, 6)
RELEASE_REVIEWED = date(2026, 11, 8)
EVENTS = (
    dict(symbol="FERG", company="Ferguson Enterprises", day="2026-11-09", release="6:45 a.m. ET", release_session="Before market", call="8:30 a.m. ET", source="https://www.corporate.ferguson.com/pressroom/news-releases/news-details/2026/Ferguson-to-Issue-Third-Quarter-Results-And-Host-Conference-Call-on-November-9-2026/default.aspx"),
    dict(release_session="After market", symbol="TTD", company="The Trade Desk", day="2026-11-09", release="After US market close", call="5:00 p.m. ET", source="https://www.thetradedesk.com/press-room/the-trade-desk-announces-date-of-third-quarter-2026-financial-results-and-conference-call"),
    dict(symbol="TTWO", company="Take-Two Interactive", day="2026-11-09", release="After US market close", release_session="After market", call="4:30 p.m. ET", source="https://ir.take2games.com/node/32631/pdf"),
    dict(symbol="CRWV", company="CoreWeave", day="2026-11-10", release="Release timing not specified", call="5:00 p.m. ET", source="https://investors.coreweave.com/news/news-details/2026/CoreWeave-Announces-Date-of-Third-Quarter-2026-Financial-Results-and-Conference-Call/default.aspx"),
    dict(symbol="TDG", company="TransDigm Group", day="2026-11-10", release="Before US market open", release_session="Before market", call="10:00 a.m. ET", source="https://transdigmgroupinc.gcs-web.com/news-releases/news-release-details/transdigm-fourth-quarter-earnings-report-and-conference-call-16"),
    dict(symbol="AMAT", company="Applied Materials", day="2026-11-12", release="Release timing not specified", call="Time not recorded in reviewed source", source="https://investor.appliedmaterials.com/events"),
    dict(symbol="CSCO", company="Cisco Systems", day="2026-11-12", release="After US market close", release_session="After market", call="4:30 p.m. ET", source="https://newsroom.cisco.com/c/r/newsroom/en/us/a/y2026/m11/cisco-schedules-conference-call-for-q1-fiscal-year-2027-financial-results.html"),
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
    return tuple(e for e in sorted(EVENTS, key=lambda e: (e["day"], e["symbol"])) if start <= date.fromisoformat(e["day"]) <= end
                 and query in f"{e['symbol']} {e['company']}".casefold())


def reconcile_provider_events(events, start, today, announcements=None):
    """Prefer reviewed issuer release facts, never infer a release from a call.

    Pure presentation-time reconciliation also fixes already-cached snapshots.
    Facts expire after 30 days and apply only to their explicit reporting week.
    Original provider data and quota ledger are unchanged. No network requests.
    """
    from app.intelligence.earnings_api_provider import EarningsEvent

    rows = tuple(events)
    sources = {}
    corrections = 0
    if not RELEASE_REVIEWED <= today <= RELEASE_REVIEWED + timedelta(days=30):
        return rows, sources, corrections
    for fact in EVENTS if announcements is None else announcements:
        day = date.fromisoformat(fact['day'])
        # Call-only entries do not establish the results-release date/session.
        if not (start <= day <= start + timedelta(days=6)
                and fact.get('release_session') in {'Before market', 'After market'}
                and fact['source'].startswith('https://')):
            continue
        original = tuple(e for e in rows if e.symbol == fact['symbol'])
        replacement = EarningsEvent(fact['symbol'], fact['company'], day, fact['release_session'])
        corrections += int(any(e.day != day or e.session != replacement.session for e in original))
        rows = tuple(e for e in rows if e.symbol != fact['symbol']) + (replacement,)
        sources[(day, fact['symbol'])] = fact
    return tuple(sorted(rows, key=lambda e: (e.day, e.symbol))), sources, corrections
