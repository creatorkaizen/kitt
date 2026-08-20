from __future__ import annotations

from kittgen.model import Punctuation


def test_punctuation_section_parses_into_punctuation_model(layout_spec):
    assert isinstance(layout_spec.punctuation, Punctuation)


def test_preserve_qwerty_where_possible_is_true(layout_spec):
    assert layout_spec.punctuation.preserve_qwerty_where_possible is True


def test_preserve_qwerty_where_possible_is_bool_typed(layout_spec):
    assert isinstance(layout_spec.punctuation.preserve_qwerty_where_possible, bool)
