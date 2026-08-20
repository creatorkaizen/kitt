from __future__ import annotations

import pytest

from kittgen.errors import (
    DuplicateMappingError,
    InvalidMetadataError,
    InvalidUnicodeOutputError,
    MissingAlphabetCoverageError,
    UnsupportedModifierError,
    UnsupportedSchemaVersionError,
)
from kittgen.model import (
    Behavior,
    DeadKeyCombination,
    DeadKeySpec,
    KeyOutputs,
    LayoutSpec,
    Metadata,
    PhysicalLayout,
    Punctuation,
)
from kittgen.validation import (
    REQUIRED_UKRAINIAN_LETTERS,
    UKRAINIAN_LOWERCASE_LETTERS,
    UKRAINIAN_UPPERCASE_LETTERS,
    validate_layout,
)


def _metadata(**overrides) -> Metadata:
    fields = dict(
        id="kitt-uk-ua",
        name="Kitt",
        description="Ukrainian mnemonic keyboard layout",
        language="uk-UA",
        version="0.1.0",
    )
    fields.update(overrides)
    return Metadata(**fields)


def _full_alphabet_keys() -> dict[str, KeyOutputs]:
    keys: dict[str, KeyOutputs] = {}
    for index, (upper, lower) in enumerate(
        zip(UKRAINIAN_UPPERCASE_LETTERS, UKRAINIAN_LOWERCASE_LETTERS)
    ):
        physical_key = f"Key{index}"
        keys[physical_key] = KeyOutputs(
            physical_key=physical_key, by_modifier={"base": lower, "shift": upper}
        )
    return keys


def _make_spec(
    *,
    schema_version: int = 1,
    metadata: Metadata | None = None,
    modifiers: tuple[str, ...] = ("base", "shift"),
    keys: dict[str, KeyOutputs] | None = None,
    dead_keys: dict[str, DeadKeySpec] | None = None,
) -> LayoutSpec:
    return LayoutSpec(
        schema_version=schema_version,
        metadata=metadata or _metadata(),
        physical_layout=PhysicalLayout(family="ansi-qwerty"),
        modifiers=modifiers,
        keys=keys if keys is not None else _full_alphabet_keys(),
        dead_keys=dead_keys or {},
        punctuation=Punctuation(preserve_qwerty_where_possible=True),
        behavior=Behavior(caps_lock="letters_only", normalize_unicode="NFC"),
    )


def _has_error(report, error_type) -> bool:
    return any(isinstance(e, error_type) for e in report.errors)


# --- schema version ----------------------------------------------------


def test_valid_schema_version_passes():
    report = validate_layout(_make_spec(schema_version=1))
    assert not _has_error(report, UnsupportedSchemaVersionError)


def test_unsupported_schema_version_fails():
    report = validate_layout(_make_spec(schema_version=2))
    assert _has_error(report, UnsupportedSchemaVersionError)
    assert not report.ok


# --- metadata: layout id -------------------------------------------------


@pytest.mark.parametrize("layout_id", ["kitt-uk-ua", "kitt", "a1-b2-c3"])
def test_valid_layout_id_passes(layout_id):
    report = validate_layout(_make_spec(metadata=_metadata(id=layout_id)))
    assert not _has_error(report, InvalidMetadataError)


@pytest.mark.parametrize("layout_id", ["Kitt-UK", "kitt_uk_ua", "-kitt", "kitt-", "", "kitt--ua"])
def test_invalid_layout_id_fails(layout_id):
    report = validate_layout(_make_spec(metadata=_metadata(id=layout_id)))
    assert _has_error(report, InvalidMetadataError)


# --- metadata: semver ------------------------------------------------------


@pytest.mark.parametrize("version", ["0.1.0", "1.0.0", "1.2.3-beta", "1.2.3+build.5"])
def test_valid_semver_passes(version):
    report = validate_layout(_make_spec(metadata=_metadata(version=version)))
    assert not _has_error(report, InvalidMetadataError)


@pytest.mark.parametrize("version", ["1.0", "v1.0.0", "1.0.0.0", "01.0.0", "not-a-version"])
def test_invalid_semver_fails(version):
    report = validate_layout(_make_spec(metadata=_metadata(version=version)))
    assert _has_error(report, InvalidMetadataError)


# --- metadata: locale -------------------------------------------------


def test_required_locale_passes():
    report = validate_layout(_make_spec(metadata=_metadata(language="uk-UA")))
    assert not _has_error(report, InvalidMetadataError)


@pytest.mark.parametrize("language", ["en-US", "uk", "UK-ua", ""])
def test_wrong_locale_fails(language):
    report = validate_layout(_make_spec(metadata=_metadata(language=language)))
    assert _has_error(report, InvalidMetadataError)


# --- modifiers declared -----------------------------------------------


def test_known_modifiers_declared_passes():
    report = validate_layout(_make_spec(modifiers=("base", "shift", "altgr", "shift_altgr")))
    assert not _has_error(report, UnsupportedModifierError)


def test_unknown_modifier_declared_fails():
    report = validate_layout(_make_spec(modifiers=("base", "ctrl_shift_magic")))
    assert _has_error(report, UnsupportedModifierError)


def test_unknown_modifier_used_on_key_fails():
    keys = _full_alphabet_keys()
    keys["KeyExtra"] = KeyOutputs(
        physical_key="KeyExtra", by_modifier={"ctrl_shift_magic": "x"}
    )
    report = validate_layout(_make_spec(keys=keys))
    assert _has_error(report, UnsupportedModifierError)


# --- duplicate physical key (keys vs dead_keys namespace clash) --------


def test_no_duplicate_physical_key_passes():
    # Use a dead-key "alone" output that is not already one of the 66
    # required letters assigned to a plain key, so this only exercises the
    # keys-vs-dead_keys namespace-clash check, not the duplicate-output check.
    dead_keys = {
        "Y": DeadKeySpec(
            dead_key="Y",
            alone=KeyOutputs(physical_key="Y", by_modifier={"base": "'", "shift": "'"}),
            combinations={},
        )
    }
    report = validate_layout(_make_spec(dead_keys=dead_keys))
    assert not _has_error(report, DuplicateMappingError)
    assert report.duplicate_count == 0


def test_duplicate_physical_key_between_keys_and_dead_keys_fails():
    keys = _full_alphabet_keys()
    keys["Y"] = KeyOutputs(physical_key="Y", by_modifier={"base": "z"})
    dead_keys = {
        "Y": DeadKeySpec(
            dead_key="Y",
            alone=KeyOutputs(physical_key="Y", by_modifier={"base": "й"}),
            combinations={},
        )
    }
    report = validate_layout(_make_spec(keys=keys, dead_keys=dead_keys))
    assert _has_error(report, DuplicateMappingError)
    assert report.duplicate_count >= 1


# --- duplicate outputs ---------------------------------------------------


def test_no_duplicate_outputs_passes():
    report = validate_layout(_make_spec())
    assert not _has_error(report, DuplicateMappingError)


def test_duplicate_output_within_same_modifier_fails():
    keys = _full_alphabet_keys()
    # Force a collision: two different physical keys emit "а" under "base".
    keys["KeyExtraDup"] = KeyOutputs(physical_key="KeyExtraDup", by_modifier={"base": "а"})
    report = validate_layout(_make_spec(keys=keys))
    assert _has_error(report, DuplicateMappingError)
    assert report.duplicate_count >= 1


def test_same_output_under_different_modifiers_is_not_a_duplicate():
    keys = _full_alphabet_keys()
    keys["KeyExtraSame"] = KeyOutputs(physical_key="KeyExtraSame", by_modifier={"altgr": "а"})
    report = validate_layout(_make_spec(keys=keys, modifiers=("base", "shift", "altgr")))
    assert not _has_error(report, DuplicateMappingError)


# --- unicode validity ---------------------------------------------------


def test_valid_unicode_outputs_pass():
    report = validate_layout(_make_spec())
    assert not _has_error(report, InvalidUnicodeOutputError)
    assert report.invalid_unicode_count == 0


def test_control_character_output_fails():
    keys = _full_alphabet_keys()
    keys["KeyBad"] = KeyOutputs(physical_key="KeyBad", by_modifier={"base": "\x01"})
    report = validate_layout(_make_spec(keys=keys))
    assert _has_error(report, InvalidUnicodeOutputError)
    assert report.invalid_unicode_count >= 1


def test_multi_scalar_output_fails():
    keys = _full_alphabet_keys()
    keys["KeyBad"] = KeyOutputs(physical_key="KeyBad", by_modifier={"base": "ab"})
    report = validate_layout(_make_spec(keys=keys))
    assert _has_error(report, InvalidUnicodeOutputError)


def test_empty_output_fails():
    keys = _full_alphabet_keys()
    keys["KeyBad"] = KeyOutputs(physical_key="KeyBad", by_modifier={"base": ""})
    report = validate_layout(_make_spec(keys=keys))
    assert _has_error(report, InvalidUnicodeOutputError)


# --- alphabet coverage ---------------------------------------------------


def test_full_alphabet_coverage_passes():
    report = validate_layout(_make_spec())
    assert not _has_error(report, MissingAlphabetCoverageError)
    assert report.reachable_letter_count == len(REQUIRED_UKRAINIAN_LETTERS)


def test_missing_letter_fails_alphabet_coverage():
    keys = _full_alphabet_keys()
    # Drop the key that provides Ukrainian "я" (last upper/lower pair).
    last_key = f"Key{len(UKRAINIAN_UPPERCASE_LETTERS) - 1}"
    del keys[last_key]
    report = validate_layout(_make_spec(keys=keys))
    assert _has_error(report, MissingAlphabetCoverageError)
    assert report.reachable_letter_count < len(REQUIRED_UKRAINIAN_LETTERS)


def test_dead_key_combinations_count_toward_alphabet_coverage():
    keys = _full_alphabet_keys()
    last_key = f"Key{len(UKRAINIAN_UPPERCASE_LETTERS) - 1}"
    missing_lower = keys[last_key].get("base")
    missing_upper = keys[last_key].get("shift")
    del keys[last_key]

    dead_keys = {
        "Y": DeadKeySpec(
            dead_key="Y",
            alone=KeyOutputs(physical_key="Y", by_modifier={"base": "й", "shift": "Й"}),
            combinations={
                "KeyA": DeadKeyCombination(
                    dead_key="Y",
                    following_physical_key="KeyA",
                    by_modifier={"base": missing_lower, "shift": missing_upper},
                )
            },
        )
    }
    report = validate_layout(_make_spec(keys=keys, dead_keys=dead_keys))
    assert not _has_error(report, MissingAlphabetCoverageError)
    assert report.reachable_letter_count == len(REQUIRED_UKRAINIAN_LETTERS)


def test_report_ok_true_when_no_errors():
    report = validate_layout(_make_spec())
    assert report.ok is True


def test_report_ok_false_when_errors_present():
    report = validate_layout(_make_spec(schema_version=99))
    assert report.ok is False
