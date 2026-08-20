"""YAML -> model.LayoutSpec parsing.

This module only converts the raw YAML document into the typed model in
model.py. It performs the minimal structural checks needed to build that
model safely (missing sections, wrong types) and raises SchemaError /
LayoutFileError with a source path in the message when it cannot. Deeper
semantic validation (duplicate mappings, Unicode correctness, alphabet
coverage, ...) is validation.py's job, not this module's.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from .errors import LayoutFileError, SchemaError

# yaml.SafeLoader silently lets a later duplicate mapping key overwrite an
# earlier one (last-one-wins), which would hide a real authoring mistake such
# as declaring KeyA twice under `keys`. Kitt should catch that at parse time
# with a clear source location instead of silently dropping a mapping, so
# construct_mapping is overridden to raise on a repeated key.


class _DuplicateKeyCheckingLoader(yaml.SafeLoader):
    pass


def _construct_mapping_no_duplicates(
    loader: yaml.SafeLoader, node: yaml.MappingNode, deep: bool = False
) -> dict[Any, Any]:
    mapping: dict[Any, Any] = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if key in mapping:
            raise SchemaError(
                f"duplicate YAML mapping key {key!r} at line {key_node.start_mark.line + 1}"
            )
        mapping[key] = loader.construct_object(value_node, deep=deep)
    return mapping


_DuplicateKeyCheckingLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _construct_mapping_no_duplicates
)
from .model import (
    Behavior,
    DeadKeyCombination,
    DeadKeySpec,
    KeyOutputs,
    LayoutSpec,
    Metadata,
    PhysicalLayout,
    Punctuation,
)

REQUIRED_TOP_LEVEL_KEYS = (
    "schema_version",
    "layout",
    "physical_layout",
    "modifiers",
    "keys",
    "punctuation",
    "behavior",
)


def parse_layout_file(path: str | Path) -> LayoutSpec:
    """Read and parse a Kitt layout YAML file from disk into a LayoutSpec."""
    file_path = Path(path)
    try:
        text = file_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise LayoutFileError(f"could not read layout file {file_path}: {exc}") from exc

    try:
        document = yaml.load(text, Loader=_DuplicateKeyCheckingLoader)
    except SchemaError as exc:
        raise SchemaError(f"{file_path}: {exc.message}") from exc
    except yaml.YAMLError as exc:
        raise LayoutFileError(f"could not parse YAML in {file_path}: {exc}") from exc

    return parse_layout_document(document, source=str(file_path))


def parse_layout_document(document: Any, *, source: str) -> LayoutSpec:
    """Parse an already-loaded YAML document (dict) into a LayoutSpec."""
    if not isinstance(document, dict):
        raise SchemaError(f"{source}: top-level YAML document must be a mapping")

    for key in REQUIRED_TOP_LEVEL_KEYS:
        if key not in document:
            raise SchemaError(f"{source}: missing required top-level key '{key}'")

    schema_version = _require_int(document, "schema_version", source)
    metadata = _parse_metadata(document["layout"], source)
    physical_layout = _parse_physical_layout(document["physical_layout"], source)
    modifiers = _parse_modifiers(document["modifiers"], source)
    keys = _parse_keys(document["keys"], source)
    dead_keys = _parse_dead_keys(document.get("dead_keys", {}), source)
    punctuation = _parse_punctuation(document["punctuation"], source)
    behavior = _parse_behavior(document["behavior"], source)

    return LayoutSpec(
        schema_version=schema_version,
        metadata=metadata,
        physical_layout=physical_layout,
        modifiers=modifiers,
        keys=keys,
        dead_keys=dead_keys,
        punctuation=punctuation,
        behavior=behavior,
    )


# --- section parsers -------------------------------------------------------


def _parse_metadata(raw: Any, source: str) -> Metadata:
    path = f"{source}:layout"
    if not isinstance(raw, dict):
        raise SchemaError(f"{path}: 'layout' section must be a mapping")
    return Metadata(
        id=_require_str(raw, "id", path),
        name=_require_str(raw, "name", path),
        description=_require_str(raw, "description", path),
        language=_require_str(raw, "language", path),
        version=_require_str(raw, "version", path),
    )


def _parse_physical_layout(raw: Any, source: str) -> PhysicalLayout:
    path = f"{source}:physical_layout"
    if not isinstance(raw, dict):
        raise SchemaError(f"{path}: 'physical_layout' section must be a mapping")
    return PhysicalLayout(family=_require_str(raw, "family", path))


def _parse_modifiers(raw: Any, source: str) -> tuple[str, ...]:
    path = f"{source}:modifiers"
    if not isinstance(raw, list) or not all(isinstance(item, str) for item in raw):
        raise SchemaError(f"{path}: 'modifiers' must be a list of strings")
    return tuple(raw)


def _parse_keys(raw: Any, source: str) -> dict[str, KeyOutputs]:
    path = f"{source}:keys"
    if not isinstance(raw, dict):
        raise SchemaError(f"{path}: 'keys' section must be a mapping")

    keys: dict[str, KeyOutputs] = {}
    for physical_key, outputs_raw in raw.items():
        key_path = f"{path}.{physical_key}"
        if not isinstance(physical_key, str):
            raise SchemaError(f"{path}: physical key names must be strings, got {physical_key!r}")
        by_modifier = _parse_modifier_outputs(outputs_raw, key_path)
        keys[physical_key] = KeyOutputs(physical_key=physical_key, by_modifier=by_modifier)
    return keys


def _parse_dead_keys(raw: Any, source: str) -> dict[str, DeadKeySpec]:
    path = f"{source}:dead_keys"
    if raw in (None, {}):
        return {}
    if not isinstance(raw, dict):
        raise SchemaError(f"{path}: 'dead_keys' section must be a mapping")

    dead_keys: dict[str, DeadKeySpec] = {}
    for dead_key_name, spec_raw in raw.items():
        dk_path = f"{path}.{dead_key_name}"
        if not isinstance(spec_raw, dict):
            raise SchemaError(f"{dk_path}: dead key entry must be a mapping")
        if "alone" not in spec_raw:
            raise SchemaError(f"{dk_path}: dead key entry missing required 'alone' section")

        alone_by_modifier = _parse_modifier_outputs(spec_raw["alone"], f"{dk_path}.alone")
        alone = KeyOutputs(physical_key=dead_key_name, by_modifier=alone_by_modifier)

        combinations: dict[str, DeadKeyCombination] = {}
        combos_raw = spec_raw.get("combinations", {})
        if not isinstance(combos_raw, dict):
            raise SchemaError(f"{dk_path}.combinations: must be a mapping")
        for combo_key, combo_outputs_raw in combos_raw.items():
            combo_path = f"{dk_path}.combinations.{combo_key}"
            by_modifier = _parse_modifier_outputs(combo_outputs_raw, combo_path)
            combinations[combo_key] = DeadKeyCombination(
                dead_key=dead_key_name,
                following_physical_key=combo_key,
                by_modifier=by_modifier,
            )

        dead_keys[dead_key_name] = DeadKeySpec(
            dead_key=dead_key_name, alone=alone, combinations=combinations
        )

    return dead_keys


def _parse_modifier_outputs(raw: Any, path: str) -> dict[str, str]:
    if not isinstance(raw, dict):
        raise SchemaError(f"{path}: expected a mapping of modifier -> output string")
    by_modifier: dict[str, str] = {}
    for modifier, value in raw.items():
        if not isinstance(modifier, str):
            raise SchemaError(f"{path}: modifier name must be a string, got {modifier!r}")
        if not isinstance(value, str):
            raise SchemaError(f"{path}.{modifier}: output must be a string, got {value!r}")
        by_modifier[modifier] = value
    return by_modifier


def _parse_punctuation(raw: Any, source: str) -> Punctuation:
    path = f"{source}:punctuation"
    if not isinstance(raw, dict):
        raise SchemaError(f"{path}: 'punctuation' section must be a mapping")
    preserve = raw.get("preserve_qwerty_where_possible", False)
    if not isinstance(preserve, bool):
        raise SchemaError(
            f"{path}.preserve_qwerty_where_possible: must be a boolean"
        )
    return Punctuation(preserve_qwerty_where_possible=preserve)


def _parse_behavior(raw: Any, source: str) -> Behavior:
    path = f"{source}:behavior"
    if not isinstance(raw, dict):
        raise SchemaError(f"{path}: 'behavior' section must be a mapping")
    return Behavior(
        caps_lock=_require_str(raw, "caps_lock", path),
        normalize_unicode=_require_str(raw, "normalize_unicode", path),
    )


# --- small typed getters ----------------------------------------------------


def _require_str(raw: dict[str, Any], key: str, path: str) -> str:
    if key not in raw:
        raise SchemaError(f"{path}: missing required key '{key}'")
    value = raw[key]
    if not isinstance(value, str):
        raise SchemaError(f"{path}.{key}: expected a string, got {value!r}")
    return value


def _require_int(raw: dict[str, Any], key: str, source: str) -> int:
    if key not in raw:
        raise SchemaError(f"{source}: missing required key '{key}'")
    value = raw[key]
    if isinstance(value, bool) or not isinstance(value, int):
        raise SchemaError(f"{source}.{key}: expected an integer, got {value!r}")
    return value
