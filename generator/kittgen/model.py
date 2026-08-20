"""Typed in-memory representation of a Kitt layout specification.

These dataclasses are what `parser.py` builds from the YAML source and what
`validation.py`, `docs.py`, and (later) the native table generator consume.
They intentionally mirror KITT_ARCHITECTURE.md section 6 ("Internal Data
Model"): explicit, typed structures instead of passing raw dicts around, and
no magic sentinel strings such as "NONE"/"DEAD"/"PASS" — a key either has a
`KeyOutputs` mapping (a normal key) or is the subject of a `DeadKeySpec`
(handled separately), and there is no third "special behavior" string to
smuggle through the model.

All classes are frozen dataclasses: a `LayoutSpec` is a value produced once
from YAML and then only read, never mutated in place (see
KITT_ARCHITECTURE.md section 32: "no global mutable state").
"""

from __future__ import annotations

from dataclasses import dataclass, field

# Recognized modifier names. Kept as a concrete tuple (not a free-form set of
# strings pulled from wherever) so validation has one place to check against.
BASE = "base"
SHIFT = "shift"
ALTGR = "altgr"
SHIFT_ALTGR = "shift_altgr"

KNOWN_MODIFIERS: tuple[str, ...] = (BASE, SHIFT, ALTGR, SHIFT_ALTGR)

SUPPORTED_SCHEMA_VERSIONS: tuple[int, ...] = (1,)


@dataclass(frozen=True)
class Metadata:
    """`layout:` section of the YAML spec."""

    id: str
    name: str
    description: str
    language: str
    version: str


@dataclass(frozen=True)
class PhysicalLayout:
    """`physical_layout:` section of the YAML spec."""

    family: str


@dataclass(frozen=True)
class KeyOutputs:
    """The set of modifier -> output-character mappings for one physical key.

    Only modifiers actually present in the YAML are populated; absent
    modifiers are simply missing from `by_modifier` rather than being filled
    in with a sentinel like "NONE". A missing modifier means "this key does
    not produce anything distinct under that modifier" and callers that care
    should treat that as "not defined", not as a magic value.
    """

    physical_key: str
    by_modifier: dict[str, str] = field(default_factory=dict)

    def get(self, modifier: str) -> str | None:
        return self.by_modifier.get(modifier)


@dataclass(frozen=True)
class DeadKeyCombination:
    """One combination entry under a dead key, e.g. Y + KeyA -> я / Я."""

    dead_key: str
    following_physical_key: str
    by_modifier: dict[str, str] = field(default_factory=dict)

    def get(self, modifier: str) -> str | None:
        return self.by_modifier.get(modifier)


@dataclass(frozen=True)
class DeadKeySpec:
    """One dead key definition, e.g. the `Y` dead key.

    `alone` is what the dead key emits if released without a matching
    combination (see kitt.uk-UA.yaml's comment on this). `combinations` maps
    a following physical key identifier to its resulting output.
    """

    dead_key: str
    alone: KeyOutputs
    combinations: dict[str, DeadKeyCombination] = field(default_factory=dict)


@dataclass(frozen=True)
class Punctuation:
    """`punctuation:` section of the YAML spec."""

    preserve_qwerty_where_possible: bool


@dataclass(frozen=True)
class Behavior:
    """`behavior:` section of the YAML spec."""

    caps_lock: str
    normalize_unicode: str


@dataclass(frozen=True)
class LayoutSpec:
    """Root object: the fully parsed contents of kitt.uk-UA.yaml."""

    schema_version: int
    metadata: Metadata
    physical_layout: PhysicalLayout
    modifiers: tuple[str, ...]
    keys: dict[str, KeyOutputs]
    dead_keys: dict[str, DeadKeySpec]
    punctuation: Punctuation
    behavior: Behavior

    def all_key_outputs(self) -> list[tuple[str, str, str]]:
        """Every (source_path, modifier, output) triple produced by this
        layout, across both `keys` and `dead_keys.combinations`.

        `source_path` is a human-readable origin string suitable for error
        messages, e.g. "KeyA.shift" or "dead_keys.Y.combinations.KeyA.shift".
        """
        results: list[tuple[str, str, str]] = []

        for physical_key, outputs in self.keys.items():
            for modifier, char in outputs.by_modifier.items():
                results.append((f"{physical_key}.{modifier}", modifier, char))

        for dead_key_name, dead_spec in self.dead_keys.items():
            for modifier, char in dead_spec.alone.by_modifier.items():
                results.append(
                    (f"dead_keys.{dead_key_name}.alone.{modifier}", modifier, char)
                )
            for combo_key, combo in dead_spec.combinations.items():
                for modifier, char in combo.by_modifier.items():
                    results.append(
                        (
                            f"dead_keys.{dead_key_name}.combinations.{combo_key}.{modifier}",
                            modifier,
                            char,
                        )
                    )

        return results
