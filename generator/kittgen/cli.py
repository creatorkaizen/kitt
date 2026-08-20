"""Command-line entry point for kittgen.

Usage:
    python -m kittgen validate layout/kitt.uk-UA.yaml
    python -m kittgen generate [--layout layout/kitt.uk-UA.yaml] [--out docs/mapping.md]

This is a build/development-time tool only (KITT_ARCHITECTURE.md section
2.3); it never ships as part of the installed Windows layout.
"""

from __future__ import annotations

import argparse
import io
import sys
from pathlib import Path

from .docs import generate_mapping_doc
from .errors import KittError
from .parser import parse_layout_file
from .validation import (
    REQUIRED_UKRAINIAN_LETTERS,
    ValidationReport,
    validate_layout,
)

DEFAULT_LAYOUT_PATH = "layout/kitt.uk-UA.yaml"
DEFAULT_DOCS_PATH = "docs/mapping.md"


def _ensure_utf8_stdio() -> None:
    """Make sure stdout/stderr can print Ukrainian (Cyrillic) output.

    Some Windows console codepages (e.g. cp1254 on a Turkish-locale system)
    cannot encode Cyrillic characters, which would otherwise crash any
    command that prints a Ukrainian letter (which is most of them, by
    design). Reconfigure to UTF-8 with a non-strict fallback rather than
    letting a display-only concern crash a build/validation tool.
    """
    for stream_name in ("stdout", "stderr"):
        stream = getattr(sys, stream_name)
        if isinstance(stream, io.TextIOWrapper):
            try:
                stream.reconfigure(encoding="utf-8", errors="replace")
            except (AttributeError, ValueError):
                pass


def main(argv: list[str] | None = None) -> int:
    _ensure_utf8_stdio()
    parser = _build_arg_parser()
    args = parser.parse_args(argv)

    if args.command == "validate":
        return _run_validate(args.layout)
    if args.command == "generate":
        return _run_generate(args.layout, args.out)

    parser.print_help()
    return 1


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="kittgen", description=__doc__)
    subparsers = parser.add_subparsers(dest="command")

    validate_parser = subparsers.add_parser(
        "validate", help="validate a Kitt layout YAML file"
    )
    validate_parser.add_argument(
        "layout",
        nargs="?",
        default=DEFAULT_LAYOUT_PATH,
        help=f"path to the layout YAML file (default: {DEFAULT_LAYOUT_PATH})",
    )

    generate_parser = subparsers.add_parser(
        "generate", help="generate docs/mapping.md from the layout YAML file"
    )
    generate_parser.add_argument(
        "--layout",
        default=DEFAULT_LAYOUT_PATH,
        help=f"path to the layout YAML file (default: {DEFAULT_LAYOUT_PATH})",
    )
    generate_parser.add_argument(
        "--out",
        default=DEFAULT_DOCS_PATH,
        help=f"path to write the generated Markdown to (default: {DEFAULT_DOCS_PATH})",
    )

    return parser


def _run_validate(layout_path: str) -> int:
    try:
        spec = parse_layout_file(layout_path)
    except KittError as exc:
        print(f"ERROR {exc.code}: {exc.message}")
        return 1

    report = validate_layout(spec)
    _print_report(report)

    if not report.ok:
        return 1

    print("Kitt layout valid.")
    print(f"{report.reachable_letter_count} of {len(REQUIRED_UKRAINIAN_LETTERS)} "
          "Ukrainian letters reachable.")
    print(f"{report.duplicate_count} duplicate mappings.")
    print(f"{report.invalid_unicode_count} invalid Unicode outputs.")
    return 0


def _run_generate(layout_path: str, out_path: str) -> int:
    try:
        spec = parse_layout_file(layout_path)
    except KittError as exc:
        print(f"ERROR {exc.code}: {exc.message}")
        return 1

    report = validate_layout(spec)
    if not report.ok:
        print("Refusing to generate docs from an invalid layout:")
        _print_report(report)
        return 1

    markdown = generate_mapping_doc(spec)
    out_file = Path(out_path)
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(markdown, encoding="utf-8")
    print(f"Generated {out_file}")
    return 0


def _print_report(report: ValidationReport) -> None:
    for error in report.errors:
        print(f"ERROR {error.code}: {error.message}")


if __name__ == "__main__":
    sys.exit(main())
