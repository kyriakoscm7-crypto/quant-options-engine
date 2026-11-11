"""Regression tests for the beginner-first Learn curriculum and navigation."""
from pathlib import Path

from streamlit.testing.v1 import AppTest

from app.education.catalog import PATHWAYS, READY_LESSONS
from dashboard.learn_foundations import DESCRIPTIONS, RELATED, TITLES


def _app():
    return AppTest.from_string(
        "from dashboard.learn_foundations import render_foundations_lesson\n"
        "render_foundations_lesson()"
    ).run()


def test_foundations_registered_first_and_has_eight_ordered_chapters():
    assert PATHWAYS[0]["id"] == "foundations"
    assert "foundations" in READY_LESSONS
    assert len(TITLES) == len(DESCRIPTIONS) == 8
    assert "money" in TITLES[0].lower()
    assert "research" in TITLES[-1].lower()


def test_foundations_intro_and_all_chapters_navigate_without_sliders():
    app = _app()
    assert not app.exception
    assert app.session_state["qi_foundations_chapter"] == 0
    assert app.button(key="qi_foundations_next")
    app.button(key="qi_foundations_next").click().run()
    assert app.session_state["qi_foundations_chapter"] == 1
    assert app.button(key="qi_foundations_previous").label == "← Course overview"
    assert len(app.slider) == 0
    app.button(key="qi_foundations_previous").click().run()
    assert app.session_state["qi_foundations_chapter"] == 0
    for chapter in range(1, 9):
        app.button(key="qi_foundations_next").click().run()
        assert not app.exception
        assert app.session_state["qi_foundations_chapter"] == chapter
        assert len(app.slider) == 0
    assert app.button(key="qi_foundations_previous")
    assert app.session_state["qi_learn_scroll_serial"] >= 9


def test_existing_labs_are_related_to_appropriate_chapters():
    ready = {(p["id"], lesson) for p in PATHWAYS for lesson, _ in p["lessons"]
             if lesson in READY_LESSONS}
    assert set(RELATED) == set(range(1, 9))
    for items in RELATED.values():
        assert items
        for _, path, lesson in items:
            assert (path, lesson) in ready


def test_source_has_no_live_quoting_or_unverified_yield_promises():
    course = Path("dashboard/learn_foundations.py").read_text()
    assert "yfinance" not in course
    assert "fetch_option_chain" not in course
    assert "guarantee" in course.lower()
    assert "theoretical_option" not in course
    assert "st.slider(" not in course
    assert "lesson_journey(TITLES, DESCRIPTIONS)" in course


def test_learn_home_prefers_first_principles_over_advanced_options():
    page = Path("dashboard/learn_page.py").read_text()
    assert 'key="qi_learn_start_foundations"' in page
    assert 'optional_paths = [path for path in PATHWAYS' in page
    assert page.index("lesson_journey(FOUNDATION_TITLES") < page.index("featured_lesson()")


def test_options_scroll_request_called_from_next_chapter_callback():
    course = Path("dashboard/options_premium_lesson.py").read_text()
    assert "request_top()" in course
    assert "st.slider(" not in course
    assert "st.radio(" not in course
    assert 'st.table([' in course
