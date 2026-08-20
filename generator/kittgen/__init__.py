"""kittgen — build-time YAML-to-native-layout generator/validator for Kitt.

This package is a development/build-time tool only. It never runs as part of
the installed Windows keyboard layout (see KITT_ARCHITECTURE.md, sections 2.3
and 15). It parses the canonical layout/kitt.uk-UA.yaml specification,
validates it, and (later milestones) generates native Windows tables and
human-readable documentation from the same source of truth.
"""

__version__ = "0.1.0"

__all__ = ["__version__"]
