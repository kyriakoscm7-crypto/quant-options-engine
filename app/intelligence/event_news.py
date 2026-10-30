"""Match dated news to historical market events without inferring causation."""

from datetime import date, datetime, time
from urllib.parse import urlsplit
from zoneinfo import ZoneInfo

EASTERN = ZoneInfo("America/New_York")


def news_near_event(
    articles: list[dict],
    event_date: str | date,
    before_days: int = 5,
    after_days: int = 2,
) -> list[dict]:
    """Return source-linked articles near the event opening, newest first."""
    day = date.fromisoformat(str(event_date)[:10])
    opening = datetime.combine(day, time(9, 30), tzinfo=EASTERN)
    matched = []

    for article in articles:
        if not isinstance(article, dict):
            continue

        url = str(article.get("url") or "")
        parsed_url = urlsplit(url)

        if parsed_url.scheme not in ("http", "https") or not parsed_url.netloc:
            continue

        try:
            published = datetime.fromisoformat(
                str(article["published"]).replace("Z", "+00:00")
            )
        except (KeyError, TypeError, ValueError):
            continue

        if published.tzinfo is None:
            continue

        eastern_time = published.astimezone(EASTERN)
        difference = (eastern_time.date() - day).days

        if not -before_days <= difference <= after_days:
            continue

        timing = (
            "Published before event opening"
            if eastern_time < opening
            else "Published at or after event opening"
        )

        matched.append(
            (
                published,
                {
                    **article,
                    "event_timing": timing,
                    "published_eastern": eastern_time.strftime(
                        "%b %d, %Y at %I:%M %p ET"
                    ),
                },
            )
        )

    matched.sort(key=lambda item: item[0], reverse=True)
    return [article for _, article in matched]
