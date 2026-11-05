"""Typed boundary for future licensed earnings and analyst integrations.

No vendor is admitted by default. A key or environment attestation is insufficient:
reviewed source contracts must be registered in code in a separate integration PR.
"""
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Protocol
from urllib.parse import urlsplit
from zoneinfo import ZoneInfo


def safe_source_url(value):
    try:
        parsed = urlsplit(value)
        return (parsed.scheme == "https" and bool(parsed.hostname)
                and not parsed.username and not parsed.password
                and not any(c.isspace() for c in value))
    except (TypeError, ValueError):
        return False


@dataclass(frozen=True)
class SourceGrant:
    provider: str
    owner: str  # Underlying dataset owner; syndication does not add independence.
    contract_reference: str
    expires: date
    datasets: frozenset[str]
    display: bool
    derived: bool


# Deliberately empty until provider-specific rights, geography/users, retention,
# timestamps and attribution have been reviewed and tested.
APPROVED_SOURCES: dict[str, SourceGrant] = {}


@dataclass(frozen=True)
class Evidence:
    cik: str
    field: str  # earnings or analyst_sentiment
    value: str  # earnings ISO date, or provider's attributed rating label
    provider: str
    url: str
    as_of: datetime
    timezone: str = "America/New_York"
    scheduled_at: datetime | None = None
    confirmed: bool = False
    sample_size: int | None = None


class LicensedProvider(Protocol):
    def evidence(self, cik: str) -> list[Evidence]: ...


def corroborate(items, cik, field, *, now, grants=None):
    """Reconcile current, licensed, independently owned observations.

    This reports evidence agreement, never a probability of investment success.
    Different analyst methodologies remain attributed rather than averaged.
    """
    grants = APPROVED_SOURCES if grants is None else grants
    if now.tzinfo is None:
        raise ValueError("An aware current time is required")
    accepted, rejected = [], 0
    max_age = timedelta(days=2 if field == "earnings" else 30)
    for item in items:
        grant = grants.get(item.provider)
        if (item.cik != cik or item.field != field or not grant or not grant.owner
                or not grant.contract_reference or not grant.display or not grant.derived
                or field not in grant.datasets or grant.expires < now.date()
                or not safe_source_url(item.url) or item.as_of.tzinfo is None
                or not timedelta(0) <= now - item.as_of <= max_age):
            rejected += 1
            continue
        try:
            ZoneInfo(item.timezone)
            if field == "earnings":
                day = date.fromisoformat(item.value)
                if day < now.astimezone(ZoneInfo(item.timezone)).date():
                    raise ValueError("Past earnings date")
                if item.scheduled_at and (item.scheduled_at.tzinfo is None
                        or item.scheduled_at.astimezone(ZoneInfo(item.timezone)).date() != day
                        or item.scheduled_at < now):
                    raise ValueError("Invalid event timestamp")
            elif field != "analyst_sentiment" or not item.value.strip() or not item.sample_size or item.sample_size < 1:
                raise ValueError("Invalid analyst evidence")
        except (ValueError, KeyError):
            rejected += 1
            continue
        accepted.append(item)
    owners = {grants[x.provider].owner for x in accepted}
    values = {(x.value, x.timezone, x.scheduled_at) if field == "earnings" else (x.provider, x.value) for x in accepted}
    # Date-only and timed records can corroborate a date, but disagreement about
    # exact timestamps is surfaced separately and cannot produce a confirmed time.
    days = {x.value for x in accepted}
    times = {x.scheduled_at for x in accepted if x.scheduled_at}
    zones = {x.timezone for x in accepted if not x.scheduled_at}
    conflict = len(days) > 1 or (field == "earnings" and (len(times) > 1 or len(zones) > 1))
    if field == "analyst_sentiment":
        conflict = len({x.value.casefold() for x in accepted}) > 1
    status = ("unavailable" if not accepted else "conflict" if conflict else
              "corroborated" if len(owners) >= 2 else "single source")
    return {"status": status, "evidence": accepted, "independent_owners": len(owners),
            "rejected": rejected, "distinct_observations": len(values)}


def earnings_label(item, *, now, viewer_timezone="America/Toronto"):
    """Calendar-day proximity, explicitly localized; never invent midnight time."""
    if now.tzinfo is None:
        raise ValueError("An aware current time is required")
    zone = ZoneInfo(viewer_timezone if item.scheduled_at else item.timezone)
    event_day = (item.scheduled_at.astimezone(zone).date() if item.scheduled_at
                 else date.fromisoformat(item.value))
    days = (event_day - now.astimezone(zone).date()).days
    proximity = "past" if days < 0 else "today" if days == 0 else f"{days}d"
    timing = (item.scheduled_at.astimezone(zone).strftime("%Y-%m-%d %H:%M %Z")
              if item.scheduled_at else f"{event_day.isoformat()} · time unannounced · {item.timezone}")
    return f"{proximity} · {timing} · {'confirmed by source' if item.confirmed else 'estimated'}"
