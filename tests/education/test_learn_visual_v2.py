"""Learn 2.0: preserve existing curriculum and test the guided options route."""
from pathlib import Path

from streamlit.testing.v1 import AppTest

from app.education.catalog import LESSON_SUMMARIES, PATHWAYS, READY_LESSONS


def test_featured_lesson_is_searchable_and_ready():
    advanced = next(p for p in PATHWAYS if p["id"] == "advanced")
    assert ("options_premium", "Why do option premiums change?") in advanced["lessons"]
    assert "options_premium" in READY_LESSONS
    assert "options_premium" in LESSON_SUMMARIES


def test_reusable_theme_does_not_fetch_external_fonts_or_run_scripts():
    source = Path("dashboard/learn_design.py").read_text()
    assert "https://" not in source
    assert "<script" not in source
    for marker in ("#ff78b7", "#80a8f5", "pair-grid", "progress-track",
                   "chapter-top", "large-example", "force-icon", "insight"):
        assert marker in source.lower()


def test_full_guided_lesson_has_eight_chapters_before_any_quiz():
    app = AppTest.from_string(
        "from dashboard.options_premium_lesson import render_options_premium_lesson\n"
        "render_options_premium_lesson()"
    ).run()
    assert not app.exception
    assert app.session_state["qi_options_premium_chapter_v2"] == 0
    assert app.button(key="qi_opt_course_start_hero")
    assert app.button(key="qi_opt_course_start_hero").label == "Start learning — Chapter 1 →"
    assert not any(button.label == "← Previous chapter" for button in app.button)

    # The large hero start button and the bottom start action both lead to chapter 1.
    app.button(key="qi_opt_course_start_hero").click().run()
    assert not app.exception
    assert app.session_state["qi_options_premium_chapter_v2"] == 1
    assert app.button(key="qi_opt_course_previous_v2").label == "← Back to lesson overview"
    app.button(key="qi_opt_course_previous_v2").click().run()
    assert app.session_state["qi_options_premium_chapter_v2"] == 0

    for expected in range(1, 9):
        app.button(key="qi_opt_course_next_v2").click().run()
        assert not app.exception
        assert app.session_state["qi_options_premium_chapter_v2"] == expected

    assert app.button(key="qi_opt_course_previous_v2")
    app.button(key="qi_opt_course_previous_v2").click().run()
    assert not app.exception
    assert app.session_state["qi_options_premium_chapter_v2"] == 7


def test_interactive_option_value_changes_without_market_feed(monkeypatch):
    import app.market_data.yahoo_client as yahoo

    def forbidden(*args, **kwargs):
        raise AssertionError("Learn attempted live option chain request")

    monkeypatch.setattr(yahoo, "fetch_option_chain", forbidden)

    app = AppTest.from_string(
        "import streamlit as st\n"
        "st.session_state['qi_options_premium_chapter_v2'] = 4\n"
        "from dashboard.options_premium_lesson import render_options_premium_lesson\n"
        "render_options_premium_lesson()"
    ).run()
    assert not app.exception
    assert app.slider(key="qi_opt_course_stock_v2").value == 100
    assert app.slider(key="qi_opt_course_vol_v2").value == 30
    app.slider(key="qi_opt_course_stock_v2").set_value(110).run()
    assert not app.exception
    app.radio(key="qi_opt_course_kind_v2").set_value("Put").run()
    assert not app.exception


def test_learn_home_and_existing_lesson_links_remain_available():
    app = AppTest.from_string(
        "from dashboard.learn_page import render_learn_page\n"
        "render_learn_page()"
    ).run()
    assert not app.exception
    assert app.button(key="qi_learn_featured_masterclass_v2")

    source = Path("dashboard/learn_page.py").read_text()
    assert 'if lesson_id == "options_premium":' in source
    assert 'LESSON_RENDERERS[lesson_id]()' in source
    assert 'for i in range(0, len(PATHWAYS), 2)' in source



def test_currency_is_escaped_in_real_markdown_components():
    """Reproduce screenshots where paired $ symbols turned prose into LaTeX."""
    app = AppTest.from_string(
        "import streamlit as st\n"
        "st.session_state['qi_options_premium_chapter_v2'] = 1\n"
        "from dashboard.options_premium_lesson import render_options_premium_lesson\n"
        "render_options_premium_lesson()"
    ).run()
    assert not app.exception
    rendered = [element.value for element in app.markdown]
    assert any(r"\$100" in value and r"\$10,000" in value for value in rendered)
    assert any(r"\$3.50" in value and r"\$350" in value for value in rendered)

    app.button(key="qi_opt_course_next_v2").click().run()
    assert not app.exception
    assert app.session_state["qi_options_premium_chapter_v2"] == 2
    rendered = [element.value for element in app.markdown]
    assert any(r"\$100" in value and r"\$105" in value for value in rendered)
    assert any(r"\$8" in value and r"\$3" in value for value in rendered)


def test_overview_is_compact_and_all_chapters_have_optional_depth():
    design = Path("dashboard/learn_design.py").read_text()
    course = Path("dashboard/options_premium_lesson.py").read_text()
    depth = Path("dashboard/options_premium_depth.py").read_text()
    assert 'class="journey-map"' in design
    assert 'grid-template-columns:repeat(2,minmax(0,1fr))' in design
    assert 'key="qi_opt_course_start_hero"' in course
    assert "lesson_journey(CHAPTER_TITLES, CHAPTER_DESCRIPTIONS)" in course
    assert "render_chapter_depth(page)" in course
    assert "r\"\\$\"" in depth
    for concept in (
        "Exercise cost", "Intrinsic is not profit", "Bid–ask spread",
        "Change one input", "Theta isn't a fixed daily fee",
        "Implied volatility", "Greek estimate", "full contract",
    ):
        assert concept in depth
