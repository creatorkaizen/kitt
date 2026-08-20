from __future__ import annotations

from kittgen.docs import generate_mapping_doc
from kittgen.model import (
    Behavior,
    DeadKeyCombination,
    DeadKeySpec,
    KeyOutputs,
    LayoutSpec,
    Metadata,
    PhysicalLayout,
    Punctuation,
)


def _spec_with_dead_keys() -> LayoutSpec:
    keys = {
        "KeyA": KeyOutputs(physical_key="KeyA", by_modifier={"base": "а", "shift": "А"}),
        "KeyB": KeyOutputs(physical_key="KeyB", by_modifier={"base": "б", "shift": "Б"}),
    }
    dead_keys = {
        "Y": DeadKeySpec(
            dead_key="Y",
            alone=KeyOutputs(physical_key="Y", by_modifier={"base": "й", "shift": "Й"}),
            combinations={
                "KeyA": DeadKeyCombination(
                    dead_key="Y",
                    following_physical_key="KeyA",
                    by_modifier={"base": "я", "shift": "Я"},
                )
            },
        )
    }
    return LayoutSpec(
        schema_version=1,
        metadata=Metadata(
            id="kitt-uk-ua",
            name="Kitt",
            description="Ukrainian mnemonic keyboard layout",
            language="uk-UA",
            version="0.1.0",
        ),
        physical_layout=PhysicalLayout(family="ansi-qwerty"),
        modifiers=("base", "shift"),
        keys=keys,
        dead_keys=dead_keys,
        punctuation=Punctuation(preserve_qwerty_where_possible=True),
        behavior=Behavior(caps_lock="letters_only", normalize_unicode="NFC"),
    )


def test_generate_mapping_doc_returns_string():
    doc = generate_mapping_doc(_spec_with_dead_keys())
    assert isinstance(doc, str)
    assert doc.endswith("\n")


def test_generate_mapping_doc_includes_metadata_header():
    doc = generate_mapping_doc(_spec_with_dead_keys())
    assert "# Kitt — Mapping Reference" in doc
    assert "kitt-uk-ua" in doc
    assert "uk-UA" in doc
    assert "0.1.0" in doc
    assert "ansi-qwerty" in doc


def test_generate_mapping_doc_includes_every_physical_key_row():
    spec = _spec_with_dead_keys()
    doc = generate_mapping_doc(spec)
    for physical_key in spec.keys:
        assert f"`{physical_key}`" in doc


def test_generate_mapping_doc_includes_key_outputs():
    doc = generate_mapping_doc(_spec_with_dead_keys())
    assert "`а`" in doc
    assert "`А`" in doc
    assert "`б`" in doc
    assert "`Б`" in doc


def test_generate_mapping_doc_includes_dead_key_section():
    doc = generate_mapping_doc(_spec_with_dead_keys())
    assert "## Dead Keys" in doc
    assert "`Y` (dead key)" in doc
    assert "`й`" in doc
    assert "`Й`" in doc
    assert "`я`" in doc
    assert "`Я`" in doc


def test_generate_mapping_doc_omits_dead_key_section_when_absent():
    spec = _spec_with_dead_keys()
    spec_no_dead_keys = LayoutSpec(
        schema_version=spec.schema_version,
        metadata=spec.metadata,
        physical_layout=spec.physical_layout,
        modifiers=spec.modifiers,
        keys=spec.keys,
        dead_keys={},
        punctuation=spec.punctuation,
        behavior=spec.behavior,
    )
    doc = generate_mapping_doc(spec_no_dead_keys)
    assert "## Dead Keys" not in doc


def test_generate_mapping_doc_includes_behavior_section():
    doc = generate_mapping_doc(_spec_with_dead_keys())
    assert "## Behavior" in doc
    assert "letters_only" in doc
    assert "NFC" in doc
    assert "preserves QWERTY punctuation where possible" in doc


def test_generate_mapping_doc_reflects_punctuation_disabled():
    spec = _spec_with_dead_keys()
    spec_no_preserve = LayoutSpec(
        schema_version=spec.schema_version,
        metadata=spec.metadata,
        physical_layout=spec.physical_layout,
        modifiers=spec.modifiers,
        keys=spec.keys,
        dead_keys=spec.dead_keys,
        punctuation=Punctuation(preserve_qwerty_where_possible=False),
        behavior=spec.behavior,
    )
    doc = generate_mapping_doc(spec_no_preserve)
    assert "does not preserve QWERTY punctuation" in doc


def test_generate_mapping_doc_from_real_layout(layout_spec):
    doc = generate_mapping_doc(layout_spec)
    for physical_key in layout_spec.keys:
        assert f"`{physical_key}`" in doc
    for dead_key_name in layout_spec.dead_keys:
        assert f"`{dead_key_name}` (dead key)" in doc
