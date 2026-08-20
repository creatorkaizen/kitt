"""Semantic validation of a parsed LayoutSpec.

Implements the checks required by KITT_ARCHITECTURE.md section 7
("Validation Layer"):

  - schema_version is supported;
  - layout id/version/language are valid;
  - no physical key is declared twice;
  - every output is valid Unicode (via unicode.py);
  - all 66 required Ukrainian letters (33 upper + 33 lower) are reachable
    through either `keys` or `dead_keys.combinations`;
  - modifier names are recognized.

`validate_layout` runs every check and returns a `ValidationReport` rather
than raising on the first problem, so `kittgen validate` can print a full
list of issues in one pass instead of a whack-a-mole one-error-at-a-time
loop. Callers that want fail-fast behavior can inspect `report.errors` and
raise themselves.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from .errors import (
    DuplicateMappingError,
    InvalidMetadataError,
    InvalidUnicodeOutputError,
    KittError,
    MissingAlphabetCoverageError,
    UnsupportedModifierError,
    UnsupportedSchemaVersionError,
)
from .model import KNOWN_MODIFIERS, SUPPORTED_SCHEMA_VERSIONS, LayoutSpec
from .unicode import check_output

REQUIRED_LOCALE = "uk-UA"

# 33 Ukrainian uppercase letters, in alphabetical order.
UKRAINIAN_UPPERCASE_LETTERS: tuple[str, ...] = tuple(
    "АБВГҐДЕЄЖЗИІЇЙКЛМНОПРСТУФХЦЧШЩЬЮЯ"
)
# Matching lowercase letters, same order.
UKRAINIAN_LOWERCASE_LETTERS: tuple[str, ...] = tuple(
    "абвгґдеєжзиіїйклмнопрстуфхцчшщьюя"
)

assert len(UKRAINIAN_UPPERCASE_LETTERS) == 33
assert len(UKRAINIAN_LOWERCASE_LETTERS) == 33

REQUIRED_UKRAINIAN_LETTERS: frozenset[str] = frozenset(
    UKRAINIAN_UPPERCASE_LETTERS + UKRAINIAN_LOWERCASE_LETTERS
)

_SEMVER_RE = re.compile(
    r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)"
    r"(?:-[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?"
    r"(?:\+[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?$"
)
_LAYOUT_ID_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")


@dataclass
class ValidationReport:
    """Accumulated result of validating a LayoutSpec."""

    errors: list[KittError] = field(default_factory=list)
    duplicate_count: int = 0
    invalid_unicode_count: int = 0
    reachable_letter_count: int = 0

    @property
    def ok(self) -> bool:
        return not self.errors

    def add(self, error: KittError) -> None:
        self.errors.append(error)


def validate_layout(spec: LayoutSpec) -> ValidationReport:
    """Run every semantic validation check against `spec` and return a report."""
    report = ValidationReport()

    _validate_schema_version(spec, report)
    _validate_metadata(spec, report)
    _validate_modifiers_declared(spec, report)
    _validate_no_duplicate_physical_keys(spec, report)
    _validate_no_duplicate_outputs(spec, report)
    _validate_modifier_names_used(spec, report)
    _validate_unicode_outputs(spec, report)
    _validate_alphabet_coverage(spec, report)

    return report


# --- individual checks ------------------------------------------------------


def _validate_schema_version(spec: LayoutSpec, report: ValidationReport) -> None:
    if spec.schema_version not in SUPPORTED_SCHEMA_VERSIONS:
        report.add(
            UnsupportedSchemaVersionError(
                f"schema_version {spec.schema_version} is not supported "
                f"(supported: {', '.join(str(v) for v in SUPPORTED_SCHEMA_VERSIONS)})"
            )
        )


def _validate_metadata(spec: LayoutSpec, report: ValidationReport) -> None:
    meta = spec.metadata

    if not _LAYOUT_ID_RE.match(meta.id):
        report.add(
            InvalidMetadataError(
                f"layout.id {meta.id!r} is not a valid stable identifier "
                "(expected lowercase alphanumeric segments separated by hyphens, "
                "e.g. 'kitt-uk-ua')"
            )
        )

    if not _SEMVER_RE.match(meta.version):
        report.add(
            InvalidMetadataError(
                f"layout.version {meta.version!r} is not valid semantic versioning "
                "(expected MAJOR.MINOR.PATCH, e.g. '0.1.0')"
            )
        )

    if meta.language != REQUIRED_LOCALE:
        report.add(
            InvalidMetadataError(
                f"layout.language {meta.language!r} does not match required "
                f"locale {REQUIRED_LOCALE!r}"
            )
        )


def _validate_modifiers_declared(spec: LayoutSpec, report: ValidationReport) -> None:
    for modifier in spec.modifiers:
        if modifier not in KNOWN_MODIFIERS:
            report.add(
                UnsupportedModifierError(
                    f"modifiers: unsupported modifier name {modifier!r} "
                    f"(recognized: {', '.join(KNOWN_MODIFIERS)})"
                )
            )


def _validate_no_duplicate_physical_keys(
    spec: LayoutSpec, report: ValidationReport
) -> None:
    # Literal duplicate YAML mapping keys (e.g. `KeyA:` declared twice under
    # `keys`) are already rejected at parse time by parser.py's
    # duplicate-key-checking loader. What remains to check here is a
    # physical key being claimed by more than one *source*: a plain `keys`
    # entry that names the same physical key as a dead key's own trigger
    # identifier. A bare `keys` physical key and a `dead_keys.<Key>` name
    # occupy the same namespace of "what happens when this physical key is
    # pressed with no active dead key", so a collision there is a real
    # duplicate mapping.
    dead_key_names = set(spec.dead_keys.keys())
    for physical_key in spec.keys:
        if physical_key in dead_key_names:
            report.duplicate_count += 1
            report.add(
                DuplicateMappingError(
                    f"{physical_key} is declared both in 'keys' and as a "
                    f"'dead_keys' entry name — a physical key cannot be both "
                    f"a normal key and a dead key trigger"
                )
            )


def _validate_no_duplicate_outputs(spec: LayoutSpec, report: ValidationReport) -> None:
    # Two different (physical key, modifier) sources producing the exact
    # same character is almost always an authoring mistake — see
    # KITT_ARCHITECTURE.md section 15's own example:
    #   "KeyG.altgr duplicates output already assigned to KeyH.altgr"
    # Compare within the same modifier only: e.g. KeyA.base == "а" and a
    # dead-key alone output of "а" under a different modifier are unrelated
    # concerns, but two "base" outputs both producing "а" would make one of
    # them a dead assignment.
    seen: dict[tuple[str, str], str] = {}
    for source_path, modifier, char in spec.all_key_outputs():
        dedup_key = (modifier, char)
        if dedup_key in seen:
            report.duplicate_count += 1
            report.add(
                DuplicateMappingError(
                    f"{source_path} duplicates output already assigned to "
                    f"{seen[dedup_key]} ({char!r} under modifier {modifier!r})"
                )
            )
        else:
            seen[dedup_key] = source_path


def _validate_modifier_names_used(spec: LayoutSpec, report: ValidationReport) -> None:
    for source_path, modifier, _char in spec.all_key_outputs():
        if modifier not in KNOWN_MODIFIERS:
            report.add(
                UnsupportedModifierError(
                    f"{source_path}: unsupported modifier name {modifier!r} "
                    f"(recognized: {', '.join(KNOWN_MODIFIERS)})"
                )
            )


def _validate_unicode_outputs(spec: LayoutSpec, report: ValidationReport) -> None:
    for source_path, _modifier, char in spec.all_key_outputs():
        result = check_output(char)
        if not result.ok:
            report.invalid_unicode_count += 1
            report.add(
                InvalidUnicodeOutputError(f"{source_path}: {result.reason} ({char!r})")
            )


def _validate_alphabet_coverage(spec: LayoutSpec, report: ValidationReport) -> None:
    reachable: set[str] = set()

    for outputs in spec.keys.values():
        reachable.update(outputs.by_modifier.values())

    for dead_spec in spec.dead_keys.values():
        for combo in dead_spec.combinations.values():
            reachable.update(combo.by_modifier.values())
        # Note: `alone` output (e.g. Y -> й) is also a legitimate way to
        # reach a required letter and should count as reachable.
        reachable.update(dead_spec.alone.by_modifier.values())

    report.reachable_letter_count = len(REQUIRED_UKRAINIAN_LETTERS & reachable)

    missing = REQUIRED_UKRAINIAN_LETTERS - reachable
    if missing:
        missing_sorted = sorted(missing)
        report.add(
            MissingAlphabetCoverageError(
                "required Ukrainian character(s) unreachable via 'keys' or "
                "'dead_keys.combinations': " + ", ".join(missing_sorted)
            )
        )
