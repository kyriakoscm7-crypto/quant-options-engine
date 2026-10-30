"""Test event-date matching and publication-time classification."""

from app.intelligence.event_news import news_near_event


def article(published, url="https://example.com/story"):
    return {
        "title": "Company announcement",
        "publisher": "Test publisher",
        "published": published,
        "url": url,
    }


def test_before_market_open():
    result = news_near_event(
        [article("2026-10-30T12:00:00+00:00")],
        "2026-10-30",
    )
    assert result[0]["event_timing"] == "Published before event opening"


def test_after_market_open():
    result = news_near_event(
        [article("2026-10-30T15:00:00+00:00")],
        "2026-10-30",
    )
    assert result[0]["event_timing"] == "Published at or after event opening"


def test_previous_day_is_included():
    assert len(
        news_near_event(
            [article("2026-10-29T18:00:00+00:00")],
            "2026-10-30",
        )
    ) == 1


def test_distant_news_is_excluded():
    assert news_near_event(
        [article("2026-10-01T18:00:00+00:00")],
        "2026-10-30",
    ) == []


def test_invalid_urls_are_excluded():
    assert news_near_event(
        [article("2026-10-30T12:00:00+00:00", "javascript:alert(1)")],
        "2026-10-30",
    ) == []


def test_missing_timezone_is_excluded():
    assert news_near_event(
        [article("2026-10-30T12:00:00")],
        "2026-10-30",
    ) == []


def test_results_are_newest_first():
    results = news_near_event(
        [
            article("2026-10-29T12:00:00+00:00"),
            article("2026-10-30T12:00:00+00:00"),
        ],
        "2026-10-30",
    )
    assert results[0]["published"].startswith("2026-10-30")
