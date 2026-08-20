"""Unicode validation helpers built on the standard library `unicodedata`.

Used by validation.py to check that every output value in the layout is
either a single valid Unicode scalar (the overwhelmingly common case, e.g.
"а") or an explicitly allowed short combining/multi-codepoint sequence (e.g.
an apostrophe-adjacent combining mark), never a control character, and always
already normalized to NFC as required by behavior.normalize_unicode in the
YAML spec.
"""

from __future__ import annotations

import unicodedata

# Outputs longer than a single code point are rejected unless they appear
# here. Kept intentionally tiny and explicit rather than a general "N
# characters is fine" rule, per KITT_ARCHITECTURE.md section 7's requirement
# to reject accidental multi-character/control sequences. Empty for now: the
# current kitt.uk-UA.yaml only uses single-scalar outputs. Extend deliberately
# if a future mapping needs a real short sequence (e.g. a combining mark
# pair), not to silence a validation failure.
ALLOWED_MULTI_SCALAR_OUTPUTS: frozenset[str] = frozenset()


class UnicodeCheckResult:
    """Outcome of validating a single output string."""

    __slots__ = ("value", "ok", "reason")

    def __init__(self, value: str, ok: bool, reason: str | None) -> None:
        self.value = value
        self.ok = ok
        self.reason = reason


def is_control_character(ch: str) -> bool:
    """True if `ch` is a C0/C1 control character (Unicode category Cc)."""
    return unicodedata.category(ch) == "Cc"


def to_nfc(value: str) -> str:
    """Return `value` normalized to Unicode Normalization Form C."""
    return unicodedata.normalize("NFC", value)


def is_nfc(value: str) -> bool:
    """True if `value` is already in NFC (i.e. normalizing it is a no-op)."""
    return unicodedata.is_normalized("NFC", value)


def check_output(value: str) -> UnicodeCheckResult:
    """Validate a single mapping output string.

    Rules enforced:
      - must not be empty;
      - must not contain any control character;
      - must already be in NFC;
      - must be a single Unicode scalar value (one code point after NFC),
        unless it is explicitly present in ALLOWED_MULTI_SCALAR_OUTPUTS.
    """
    if value == "":
        return UnicodeCheckResult(value, False, "output is empty")

    for ch in value:
        if is_control_character(ch):
            name = unicodedata.name(ch, f"U+{ord(ch):04X}")
            return UnicodeCheckResult(
                value, False, f"output contains control character {name}"
            )

    if not is_nfc(value):
        return UnicodeCheckResult(
            value, False, f"output is not NFC-normalized (NFC form is {to_nfc(value)!r})"
        )

    if len(value) > 1 and value not in ALLOWED_MULTI_SCALAR_OUTPUTS:
        return UnicodeCheckResult(
            value,
            False,
            f"output has {len(value)} code points; expected exactly 1 "
            "unless explicitly allow-listed in ALLOWED_MULTI_SCALAR_OUTPUTS",
        )

    return UnicodeCheckResult(value, True, None)
