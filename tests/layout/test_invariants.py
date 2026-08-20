from __future__ import annotations

import re
import unicodedata

from kittgen.unicode import check_output

_PHYSICAL_KEY_RE = re.compile(r"^[A-Za-z][A-Za-z0-9]*$")


def test_no_key_output_is_empty(layout_spec):
    for source_path, _modifier, char in layout_spec.all_key_outputs():
        assert char != "", f"{source_path} produced an empty output"


def test_no_key_output_contains_control_characters(layout_spec):
    for source_path, _modifier, char in layout_spec.all_key_outputs():
        for ch in char:
            assert unicodedata.category(ch) != "Cc", (
                f"{source_path} produced a control character in {char!r}"
            )


def test_no_key_output_is_whitespace_only(layout_spec):
    for source_path, _modifier, char in layout_spec.all_key_outputs():
        assert char.strip() != "", f"{source_path} produced a whitespace-only output"


def test_every_key_output_passes_unicode_check(layout_spec):
    for source_path, _modifier, char in layout_spec.all_key_outputs():
        result = check_output(char)
        assert result.ok, f"{source_path}: {result.reason} ({char!r})"


def test_every_physical_key_name_is_valid_identifier(layout_spec):
    for physical_key in layout_spec.keys:
        assert _PHYSICAL_KEY_RE.match(physical_key), (
            f"physical key name {physical_key!r} is not a valid identifier"
        )
    for dead_key_name, dead_spec in layout_spec.dead_keys.items():
        assert _PHYSICAL_KEY_RE.match(dead_key_name), (
            f"dead key name {dead_key_name!r} is not a valid identifier"
        )
        for combo_key in dead_spec.combinations:
            assert _PHYSICAL_KEY_RE.match(combo_key), (
                f"dead key combination physical key {combo_key!r} is not a valid identifier"
            )


def test_no_physical_key_declared_in_both_keys_and_dead_keys(layout_spec):
    overlap = set(layout_spec.keys) & set(layout_spec.dead_keys)
    assert overlap == set(), f"physical keys declared as both normal and dead key: {overlap}"


def test_only_known_modifiers_used(layout_spec):
    from kittgen.model import KNOWN_MODIFIERS

    for source_path, modifier, _char in layout_spec.all_key_outputs():
        assert modifier in KNOWN_MODIFIERS, f"{source_path} uses unknown modifier {modifier!r}"


def test_schema_version_is_supported(layout_spec):
    from kittgen.model import SUPPORTED_SCHEMA_VERSIONS

    assert layout_spec.schema_version in SUPPORTED_SCHEMA_VERSIONS


def test_no_duplicate_output_within_same_modifier(layout_spec):
    seen: dict[tuple[str, str], str] = {}
    duplicates = []
    for source_path, modifier, char in layout_spec.all_key_outputs():
        dedup_key = (modifier, char)
        if dedup_key in seen:
            duplicates.append((source_path, seen[dedup_key], modifier, char))
        else:
            seen[dedup_key] = source_path
    assert duplicates == [], f"duplicate outputs found: {duplicates}"


def test_all_key_outputs_returns_non_empty_list(layout_spec):
    outputs = layout_spec.all_key_outputs()
    assert isinstance(outputs, list)
    assert len(outputs) > 0


def test_dead_key_alone_output_differs_by_modifier(layout_spec):
    for dead_key_name, dead_spec in layout_spec.dead_keys.items():
        base = dead_spec.alone.get("base")
        shift = dead_spec.alone.get("shift")
        assert base != shift, f"dead key {dead_key_name}: base and shift alone outputs match"
