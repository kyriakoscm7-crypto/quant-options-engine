"""Tests for the Quant Learn curriculum catalog."""

from app.education.catalog import LESSON_SUMMARIES, PATHWAYS, READY_LESSONS


def test_nine_unique_learning_pathways_including_beginner_course():
    assert len(PATHWAYS) == 9
    ids = [p["id"] for p in PATHWAYS]
    assert len(ids) == len(set(ids))


def test_lesson_ids_are_unique():
    ids = [
        lesson_id
        for pathway in PATHWAYS
        for lesson_id, _ in pathway["lessons"]
    ]
    assert len(ids) == len(set(ids))
    assert len(ids) >= 25


def test_ready_lessons_have_valid_metadata():
    all_ids = {
        lesson_id
        for pathway in PATHWAYS
        for lesson_id, _ in pathway["lessons"]
    }
    assert READY_LESSONS <= all_ids
    assert set(LESSON_SUMMARIES) == set(READY_LESSONS)


def test_every_pathway_has_description_and_lessons():
    for pathway in PATHWAYS:
        assert pathway["title"]
        assert pathway["description"]
        assert pathway["icon"]
        assert pathway["lessons"]
