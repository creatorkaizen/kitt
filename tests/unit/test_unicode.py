from __future__ import annotations

import unicodedata

import pytest

from kittgen.unicode import (
    UnicodeCheckResult,
    check_output,
    is_control_character,
    is_nfc,
    to_nfc,
)


@pytest.mark.parametrize("value", ["а", "А", "ї", "Ї", "z", "'"])
def test_check_output_accepts_valid_single_scalar(value):
    result = check_output(value)
    assert isinstance(result, UnicodeCheckResult)
    assert result.ok is True
    assert result.reason is None
    assert result.value == value


def test_check_output_rejects_empty_string():
    result = check_output("")
    assert result.ok is False
    assert "empty" in result.reason


@pytest.mark.parametrize("value", ["\x00", "\x01", "\x1b", "\x7f", "a\x01"])
def test_check_output_rejects_control_characters(value):
    result = check_output(value)
    assert result.ok is False
    assert "control character" in result.reason


@pytest.mark.parametrize("value", ["ab", "яЯ", "abc"])
def test_check_output_rejects_multi_scalar_output(value):
    result = check_output(value)
    assert result.ok is False
    assert "code points" in result.reason


def test_check_output_rejects_non_nfc_input():
    decomposed = unicodedata.normalize("NFD", "ї")
    assert decomposed != "ї"
    result = check_output(decomposed)
    assert result.ok is False
    assert "NFC" in result.reason


def test_check_output_accepts_already_nfc_input():
    composed = unicodedata.normalize("NFC", "ї")
    result = check_output(composed)
    assert result.ok is True


def test_is_control_character_true_for_control():
    assert is_control_character("\x01") is True
    assert is_control_character("\x00") is True


def test_is_control_character_false_for_letter():
    assert is_control_character("a") is False
    assert is_control_character("я") is False


def test_to_nfc_normalizes_decomposed_form():
    decomposed = unicodedata.normalize("NFD", "ї")
    assert to_nfc(decomposed) == unicodedata.normalize("NFC", "ї")


def test_is_nfc_true_for_composed_form():
    assert is_nfc(unicodedata.normalize("NFC", "ї")) is True


def test_is_nfc_false_for_decomposed_form():
    decomposed = unicodedata.normalize("NFD", "ї")
    assert is_nfc(decomposed) is False
