from __future__ import annotations

import json
from pathlib import Path

SNAPSHOT_PATH = Path(__file__).resolve().parent.parent / "snapshots" / "expected_mapping.json"


def _build_normalized_mapping(spec) -> dict:
    return {
        "schema_version": spec.schema_version,
        "metadata": {
            "id": spec.metadata.id,
            "name": spec.metadata.name,
            "language": spec.metadata.language,
            "version": spec.metadata.version,
        },
        "keys": {
            pk: dict(sorted(outputs.by_modifier.items()))
            for pk, outputs in sorted(spec.keys.items())
        },
        "dead_keys": {
            dk_name: {
                "alone": dict(sorted(dk.alone.by_modifier.items())),
                "combinations": {
                    ck: dict(sorted(combo.by_modifier.items()))
                    for ck, combo in sorted(dk.combinations.items())
                },
            }
            for dk_name, dk in sorted(spec.dead_keys.items())
        },
    }


def test_snapshot_file_exists():
    assert SNAPSHOT_PATH.exists(), f"snapshot file missing: {SNAPSHOT_PATH}"


def test_snapshot_file_is_valid_json():
    with SNAPSHOT_PATH.open(encoding="utf-8") as f:
        data = json.load(f)
    assert isinstance(data, dict)
    assert "keys" in data
    assert "dead_keys" in data


def test_real_layout_matches_snapshot(layout_spec):
    with SNAPSHOT_PATH.open(encoding="utf-8") as f:
        expected = json.load(f)

    actual = _build_normalized_mapping(layout_spec)

    assert actual == expected, (
        "Generated mapping no longer matches tests/snapshots/expected_mapping.json. "
        "If this change is intentional, regenerate the snapshot and review the diff."
    )


def test_snapshot_contains_all_physical_keys(layout_spec):
    with SNAPSHOT_PATH.open(encoding="utf-8") as f:
        expected = json.load(f)

    assert set(expected["keys"].keys()) == set(layout_spec.keys.keys())


def test_snapshot_contains_all_dead_keys(layout_spec):
    with SNAPSHOT_PATH.open(encoding="utf-8") as f:
        expected = json.load(f)

    assert set(expected["dead_keys"].keys()) == set(layout_spec.dead_keys.keys())
