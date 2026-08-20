from __future__ import annotations

from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
LAYOUT_PATH = REPO_ROOT / "layout" / "kitt.uk-UA.yaml"


@pytest.fixture(scope="session")
def layout_path() -> Path:
    return LAYOUT_PATH


@pytest.fixture(scope="session")
def layout_spec():
    from kittgen.parser import parse_layout_file

    return parse_layout_file(LAYOUT_PATH)
