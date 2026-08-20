"""Exception types raised by kittgen.

Every error carries a stable error code (see KITT_ARCHITECTURE.md, section 15,
"Logging and Diagnostics") and a human-readable message that names the source
key/path the problem came from. Stable codes let tests and CI logs assert on
specific failure classes instead of matching free-text messages.

Code ranges (informal, extend as needed):
    KITT0xx  file / parsing errors
    KITT1xx  structural / duplicate-mapping errors
    KITT2xx  content errors (invalid Unicode, missing alphabet coverage, ...)
    KITT3xx  modifier / schema errors
"""

from __future__ import annotations


class KittError(Exception):
    """Base class for all kittgen errors.

    Attributes:
        code: Stable error code, e.g. "KITT101".
        message: Human-readable description, should name the offending
            source key/path.
    """

    code: str = "KITT000"

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(f"{self.code}: {message}")


class LayoutFileError(KittError):
    """The layout YAML file could not be read or parsed."""

    code = "KITT001"


class SchemaError(KittError):
    """The layout document does not match the expected structural schema."""

    code = "KITT002"


class DuplicateMappingError(KittError):
    """The same physical key / modifier output was assigned more than once."""

    code = "KITT101"


class UnknownPhysicalKeyError(KittError):
    """A physical key identifier is referenced but not recognized."""

    code = "KITT102"


class InvalidUnicodeOutputError(KittError):
    """An output value is not a single valid Unicode scalar (or allowed short
    sequence), contains a control character, or fails NFC normalization."""

    code = "KITT201"


class UnsupportedSchemaVersionError(KittError):
    """schema_version in the layout file is not supported by this generator."""

    code = "KITT202"


class MissingAlphabetCoverageError(KittError):
    """One or more required Ukrainian letters are not reachable through
    `keys` or `dead_keys.combinations`."""

    code = "KITT203"


class InvalidMetadataError(KittError):
    """layout.id, layout.version, or layout.language is invalid."""

    code = "KITT204"


class UnsupportedModifierError(KittError):
    """A modifier name is not one of the recognized modifier names."""

    code = "KITT301"
