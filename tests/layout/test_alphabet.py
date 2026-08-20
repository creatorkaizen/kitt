from __future__ import annotations

import pytest

from kittgen.validation import (
    REQUIRED_UKRAINIAN_LETTERS,
    UKRAINIAN_LOWERCASE_LETTERS,
    UKRAINIAN_UPPERCASE_LETTERS,
    validate_layout,
)


def _reachable_outputs(spec) -> set[str]:
    reachable: set[str] = set()
    for outputs in spec.keys.values():
        reachable.update(outputs.by_modifier.values())
    for dead_spec in spec.dead_keys.values():
        reachable.update(dead_spec.alone.by_modifier.values())
        for combo in dead_spec.combinations.values():
            reachable.update(combo.by_modifier.values())
    return reachable


def test_required_alphabet_constant_has_66_letters():
    assert len(UKRAINIAN_UPPERCASE_LETTERS) == 33
    assert len(UKRAINIAN_LOWERCASE_LETTERS) == 33
    assert len(REQUIRED_UKRAINIAN_LETTERS) == 66


def test_real_layout_validates_ok(layout_spec):
    report = validate_layout(layout_spec)
    assert report.ok, [f"{e.code}: {e.message}" for e in report.errors]


def test_real_layout_reaches_all_66_required_letters(layout_spec):
    report = validate_layout(layout_spec)
    assert report.reachable_letter_count == 66


@pytest.mark.parametrize("letter", sorted(UKRAINIAN_UPPERCASE_LETTERS))
def test_each_uppercase_letter_is_reachable(layout_spec, letter):
    reachable = _reachable_outputs(layout_spec)
    assert letter in reachable, f"uppercase letter {letter!r} is not reachable"


@pytest.mark.parametrize("letter", sorted(UKRAINIAN_LOWERCASE_LETTERS))
def test_each_lowercase_letter_is_reachable(layout_spec, letter):
    reachable = _reachable_outputs(layout_spec)
    assert letter in reachable, f"lowercase letter {letter!r} is not reachable"


def test_no_required_letter_missing(layout_spec):
    reachable = _reachable_outputs(layout_spec)
    missing = REQUIRED_UKRAINIAN_LETTERS - reachable
    assert missing == set(), f"missing required Ukrainian letters: {sorted(missing)}"
