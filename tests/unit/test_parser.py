from __future__ import annotations

import pytest

from kittgen.errors import LayoutFileError, SchemaError
from kittgen.model import Behavior, KeyOutputs, LayoutSpec, Metadata, PhysicalLayout, Punctuation
from kittgen.parser import parse_layout_document, parse_layout_file

MINIMAL_YAML = """
schema_version: 1

layout:
  id: kitt-test
  name: Test
  description: Test layout
  language: uk-UA
  version: 0.1.0

physical_layout:
  family: ansi-qwerty

modifiers:
  - base
  - shift

keys:
  KeyA:
    base: "а"
    shift: "А"

punctuation:
  preserve_qwerty_where_possible: true

behavior:
  caps_lock: letters_only
  normalize_unicode: NFC
"""


def test_parses_minimal_layout_into_layout_spec(tmp_path):
    layout_file = tmp_path / "minimal.yaml"
    layout_file.write_text(MINIMAL_YAML, encoding="utf-8")

    spec = parse_layout_file(layout_file)

    assert isinstance(spec, LayoutSpec)
    assert spec.schema_version == 1
    assert isinstance(spec.metadata, Metadata)
    assert spec.metadata.id == "kitt-test"
    assert spec.metadata.language == "uk-UA"
    assert isinstance(spec.physical_layout, PhysicalLayout)
    assert spec.physical_layout.family == "ansi-qwerty"
    assert spec.modifiers == ("base", "shift")
    assert isinstance(spec.keys["KeyA"], KeyOutputs)
    assert spec.keys["KeyA"].get("base") == "а"
    assert spec.keys["KeyA"].get("shift") == "А"
    assert spec.dead_keys == {}
    assert isinstance(spec.punctuation, Punctuation)
    assert spec.punctuation.preserve_qwerty_where_possible is True
    assert isinstance(spec.behavior, Behavior)
    assert spec.behavior.caps_lock == "letters_only"
    assert spec.behavior.normalize_unicode == "NFC"


def test_parses_dead_keys_section(tmp_path):
    yaml_text = MINIMAL_YAML.replace(
        "keys:\n  KeyA:",
        "dead_keys:\n  Y:\n    alone:\n      base: \"й\"\n      shift: \"Й\"\n"
        "    combinations:\n      KeyA:\n        base: \"я\"\n        shift: \"Я\"\n"
        "keys:\n  KeyA:",
    )
    layout_file = tmp_path / "with_dead_keys.yaml"
    layout_file.write_text(yaml_text, encoding="utf-8")

    spec = parse_layout_file(layout_file)

    assert "Y" in spec.dead_keys
    dead_spec = spec.dead_keys["Y"]
    assert dead_spec.alone.get("base") == "й"
    assert dead_spec.alone.get("shift") == "Й"
    assert dead_spec.combinations["KeyA"].get("base") == "я"
    assert dead_spec.combinations["KeyA"].get("shift") == "Я"


def test_missing_file_raises_layout_file_error(tmp_path):
    missing = tmp_path / "does_not_exist.yaml"
    with pytest.raises(LayoutFileError):
        parse_layout_file(missing)


def test_malformed_yaml_syntax_raises_layout_file_error(tmp_path):
    layout_file = tmp_path / "broken.yaml"
    layout_file.write_text("schema_version: 1\n  layout:\n  bad indent: [", encoding="utf-8")

    with pytest.raises(LayoutFileError):
        parse_layout_file(layout_file)


def test_duplicate_yaml_key_raises_schema_error(tmp_path):
    yaml_text = MINIMAL_YAML + "\nlayout:\n  id: duplicate-top-level\n"
    layout_file = tmp_path / "dup_top.yaml"
    layout_file.write_text(yaml_text, encoding="utf-8")

    with pytest.raises(SchemaError):
        parse_layout_file(layout_file)


def test_duplicate_key_under_keys_section_raises_schema_error(tmp_path):
    yaml_text = MINIMAL_YAML.replace(
        'keys:\n  KeyA:\n    base: "а"\n    shift: "А"\n',
        'keys:\n  KeyA:\n    base: "а"\n    shift: "А"\n  KeyA:\n    base: "б"\n    shift: "Б"\n',
    )
    layout_file = tmp_path / "dup_key.yaml"
    layout_file.write_text(yaml_text, encoding="utf-8")

    with pytest.raises(SchemaError):
        parse_layout_file(layout_file)


@pytest.mark.parametrize("missing_key", [
    "schema_version",
    "layout",
    "physical_layout",
    "modifiers",
    "keys",
    "punctuation",
    "behavior",
])
def test_missing_required_top_level_key_raises_schema_error(missing_key):
    document = {
        "schema_version": 1,
        "layout": {
            "id": "kitt-test",
            "name": "Test",
            "description": "Test layout",
            "language": "uk-UA",
            "version": "0.1.0",
        },
        "physical_layout": {"family": "ansi-qwerty"},
        "modifiers": ["base", "shift"],
        "keys": {"KeyA": {"base": "а", "shift": "А"}},
        "punctuation": {"preserve_qwerty_where_possible": True},
        "behavior": {"caps_lock": "letters_only", "normalize_unicode": "NFC"},
    }
    del document[missing_key]

    with pytest.raises(SchemaError):
        parse_layout_document(document, source="test")


def test_top_level_document_must_be_mapping():
    with pytest.raises(SchemaError):
        parse_layout_document(["not", "a", "mapping"], source="test")


def test_schema_version_must_be_int():
    document = {
        "schema_version": "1",
        "layout": {
            "id": "kitt-test",
            "name": "Test",
            "description": "Test layout",
            "language": "uk-UA",
            "version": "0.1.0",
        },
        "physical_layout": {"family": "ansi-qwerty"},
        "modifiers": ["base", "shift"],
        "keys": {"KeyA": {"base": "а", "shift": "А"}},
        "punctuation": {"preserve_qwerty_where_possible": True},
        "behavior": {"caps_lock": "letters_only", "normalize_unicode": "NFC"},
    }
    with pytest.raises(SchemaError):
        parse_layout_document(document, source="test")


def test_keys_section_must_be_mapping():
    document = {
        "schema_version": 1,
        "layout": {
            "id": "kitt-test",
            "name": "Test",
            "description": "Test layout",
            "language": "uk-UA",
            "version": "0.1.0",
        },
        "physical_layout": {"family": "ansi-qwerty"},
        "modifiers": ["base", "shift"],
        "keys": ["KeyA"],
        "punctuation": {"preserve_qwerty_where_possible": True},
        "behavior": {"caps_lock": "letters_only", "normalize_unicode": "NFC"},
    }
    with pytest.raises(SchemaError):
        parse_layout_document(document, source="test")


def test_real_layout_file_parses_without_error(layout_path):
    spec = parse_layout_file(layout_path)
    assert isinstance(spec, LayoutSpec)
    assert spec.metadata.language == "uk-UA"
