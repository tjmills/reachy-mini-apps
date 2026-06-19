"""Tests for emotion selection and iteration."""

from itertools import islice

from hello_emotion.main import emotion_sequence, parse_names, select_moves


def test_parse_names_ignores_empty_items_and_whitespace() -> None:
    assert parse_names(" curious1, ,welcoming1 ") == ("curious1", "welcoming1")


def test_select_moves_preserves_requested_order() -> None:
    assert select_moves(
        ("welcoming1", "missing", "curious1"),
        ("curious1", "welcoming1"),
    ) == ("welcoming1", "curious1")


def test_looping_sequence_repeats() -> None:
    values = tuple(islice(emotion_sequence(("a", "b"), loop=True), 5))
    assert values == ("a", "b", "a", "b", "a")
