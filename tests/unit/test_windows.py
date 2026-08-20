"""Tests for kittgen.windows: YAML LayoutSpec -> Windows KBDTABLES C source.

These tests check string/structural properties of the generated C source
(the right struct names appear, every mapped output shows up as a WCHAR
literal, dead keys use WCH_DEAD, the file is marked as generated, etc). They
do not compile the C — an actual MSVC/WDK compile is a separate follow-up
step outside this generator's scope.
"""

from __future__ import annotations

import re

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
from kittgen.windows import (
    PHYSICAL_KEY_TO_VK,
    STANDARD_SCANCODE_TO_VK,
    generate_kbdtables_source,
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
        physical_layout=PhysicalLayout(family="iso-turkish-q"),
        modifiers=("base", "shift"),
        keys=keys,
        dead_keys=dead_keys,
        punctuation=Punctuation(preserve_qwerty_where_possible=True),
        behavior=Behavior(caps_lock="letters_only", normalize_unicode="NFC"),
    )


def _spec_without_dead_keys() -> LayoutSpec:
    spec = _spec_with_dead_keys()
    return LayoutSpec(
        schema_version=spec.schema_version,
        metadata=spec.metadata,
        physical_layout=spec.physical_layout,
        modifiers=spec.modifiers,
        keys=spec.keys,
        dead_keys={},
        punctuation=spec.punctuation,
        behavior=spec.behavior,
    )


# --- basic shape -------------------------------------------------------


def test_generate_kbdtables_source_returns_string():
    source = generate_kbdtables_source(_spec_with_dead_keys())
    assert isinstance(source, str)
    assert source.endswith("\n")


def test_generated_source_is_marked_as_generated():
    source = generate_kbdtables_source(_spec_with_dead_keys())
    assert "GENERATED FILE" in source
    assert "DO NOT EDIT" in source
    assert "kitt.uk-UA.yaml" in source


def test_generated_source_includes_layout_metadata():
    source = generate_kbdtables_source(_spec_with_dead_keys())
    assert "kitt-uk-ua" in source
    assert "0.1.0" in source
    assert "uk-UA" in source


def test_generated_source_includes_required_headers():
    source = generate_kbdtables_source(_spec_with_dead_keys())
    assert "#include <windows.h>" in source
    assert '#include "kbd.h"' in source


# --- KBDTABLES / core struct wiring -------------------------------------


def test_generated_source_defines_kbdtables_struct():
    source = generate_kbdtables_source(_spec_with_dead_keys())
    assert "KBDTABLES" in source
    assert "static KBDTABLES kitt_KbdTables" in source


def test_generated_source_exports_kbdlayerdescriptor():
    source = generate_kbdtables_source(_spec_with_dead_keys())
    assert "KbdLayerDescriptor" in source
    assert "__declspec(dllexport)" in source
    assert "PKBDTABLES" in source
    assert "return &kitt_KbdTables;" in source


def test_generated_source_defines_modifiers_table():
    source = generate_kbdtables_source(_spec_with_dead_keys())
    assert "MODIFIERS" in source
    assert "VK_TO_BIT" in source
    assert "VK_SHIFT" in source
    assert "KBDSHIFT" in source


def test_generated_source_marks_ctrl_combinations_invalid():
    # Safety invariant (KITT_ARCHITECTURE.md section 7): Ctrl shortcuts must
    # not unexpectedly emit letters. CTRL and CTRL+ALT modification-bit
    # states must be SHFT_INVALID, not a valid shift-state index.
    source = generate_kbdtables_source(_spec_with_dead_keys())
    assert "SHFT_INVALID" in source
    # At least the pure-CTRL (index 4) and CTRL+ALT (index 6) entries must
    # be invalid — every modification-number line that isn't 0 (base) or 1
    # (shift) should be SHFT_INVALID given Kitt defines no AltGr.
    invalid_count = source.count("SHFT_INVALID,")
    assert invalid_count >= 5


def test_generated_source_defines_vk_to_wchars_table():
    source = generate_kbdtables_source(_spec_with_dead_keys())
    assert "VK_TO_WCHARS2" in source
    assert "VK_TO_WCHAR_TABLE" in source


def test_generated_source_terminates_vk_to_wchar_table_with_null():
    source = generate_kbdtables_source(_spec_with_dead_keys())
    assert "{ NULL, 0, 0 }" in source


# --- character output correctness ---------------------------------------


def test_every_key_output_appears_as_wchar_literal():
    spec = _spec_with_dead_keys()
    source = generate_kbdtables_source(spec)
    for outputs in spec.keys.values():
        for char in outputs.by_modifier.values():
            literal = f"0x{ord(char):04X}"
            assert literal in source, f"missing literal for {char!r} ({literal})"


def test_every_dead_key_combination_output_appears_as_wchar_literal():
    spec = _spec_with_dead_keys()
    source = generate_kbdtables_source(spec)
    for dead_spec in spec.dead_keys.values():
        for combo in dead_spec.combinations.values():
            for char in combo.by_modifier.values():
                literal = f"0x{ord(char):04X}"
                assert literal in source, f"missing literal for {char!r} ({literal})"


def test_mapped_vk_appears_in_vk_to_wchars_rows():
    # winuser.h does not #define VK_A..VK_Z / VK_0..VK_9 (they are documented
    # as numerically equal to their ASCII codes), so the generator must emit
    # a character literal ('A') for these, not the bare name "VK_A" — using
    # the bare name fails to compile with MSVC (confirmed empirically).
    source = generate_kbdtables_source(_spec_with_dead_keys())
    assert "'A'," in source
    assert "'B'," in source


def test_dead_key_trigger_uses_wch_dead():
    source = generate_kbdtables_source(_spec_with_dead_keys())
    assert "WCH_DEAD" in source
    # The Y row should use WCH_DEAD for both base and shift. Y has no
    # PHYSICAL_KEY_TO_VK override, so it renders as the character literal 'Y'.
    dead_row = re.search(r"'Y',\s*\w+,\s*\{\s*(\S+),\s*(\S+)\s*\}", source)
    assert dead_row is not None, "could not find Y's row in generated source"
    assert dead_row.group(1) == "WCH_DEAD"
    assert dead_row.group(2) == "WCH_DEAD"


def test_no_dead_key_row_omits_wch_dead_row_but_keeps_none_semantics():
    # VK_Y still legitimately appears in the standard scan-code table (Kitt
    # does not remap physical key positions), but with no dead key defined
    # it must not appear as a row in the VK_TO_WCHARS2 output table.
    source = generate_kbdtables_source(_spec_without_dead_keys())
    wchars_table = re.search(
        r"kitt_VkToWchars2\[\] = \{(.*?)\n\};", source, re.DOTALL
    )
    assert wchars_table is not None
    assert "VK_Y," not in wchars_table.group(1)


# --- DEADKEY / DEADTRANS table -------------------------------------------


def test_generated_source_includes_deadkey_table_when_dead_keys_present():
    source = generate_kbdtables_source(_spec_with_dead_keys())
    assert "DEADKEY" in source
    assert "DEADTRANS(" in source


def test_deadkey_table_omitted_when_no_dead_keys():
    source = generate_kbdtables_source(_spec_without_dead_keys())
    assert "DEADTRANS(" not in source
    assert "pDeadKey" in source  # field comment still present in KBDTABLES
    # pDeadKey field value should be NULL when there are no dead keys.
    assert re.search(r"NULL,\s*//\s*pDeadKey", source)


def test_deadtrans_rows_use_alone_base_as_accent_identity():
    # Y's alone.base is 'й'; every DEADTRANS row for Y should carry that
    # accent literal (0x0439) as the second argument.
    spec = _spec_with_dead_keys()
    source = generate_kbdtables_source(spec)
    accent_literal = f"0x{ord('й'):04X}"
    rows = re.findall(r"DEADTRANS\(([^,]+), ([^,]+), ([^,]+), DKF_DEAD\)", source)
    assert rows, "expected at least one DEADTRANS row"
    for _following, accent, _composed in rows:
        assert accent == accent_literal


def test_deadtrans_row_composes_expected_characters():
    # Y + KeyA: following='а' (KeyA.base), accent='й' (Y.alone.base),
    # composed='я' (the combination's base output).
    spec = _spec_with_dead_keys()
    source = generate_kbdtables_source(spec)
    following = f"0x{ord('а'):04X}"
    accent = f"0x{ord('й'):04X}"
    composed = f"0x{ord('я'):04X}"
    assert f"DEADTRANS({following}, {accent}, {composed}, DKF_DEAD)" in source


# --- scan-code table ------------------------------------------------------


def test_generated_source_defines_scancode_to_vk_table():
    source = generate_kbdtables_source(_spec_with_dead_keys())
    assert "kitt_VscToVk" in source
    assert "pusVSCtoVK" in source


def test_standard_scancode_table_maps_key_a_position_to_vk_a():
    # Scan code 0x1E is the standard "A" key position on a PC/AT-101
    # keyboard; Kitt must not remap physical positions, only outputs.
    table = dict(STANDARD_SCANCODE_TO_VK)
    assert table[0x1E] == "VK_A"
    assert table[0x10] == "VK_Q"
    assert table[0x39] == "VK_SPACE"
    assert table[0x1C] == "VK_RETURN"


def test_generated_source_from_real_layout_includes_scancode_rows_for_every_letter():
    from kittgen.parser import parse_layout_file
    from pathlib import Path

    layout_path = Path(__file__).resolve().parent.parent.parent / "layout" / "kitt.uk-UA.yaml"
    spec = parse_layout_file(layout_path)
    source = generate_kbdtables_source(spec)
    # Every plain KeyX (single Latin letter) physical key must resolve to a
    # VK_X constant that appears somewhere in the generated source.
    for physical_key in spec.keys:
        if physical_key.startswith("Key") and len(physical_key) == 4:
            letter = physical_key[-1]
            # VK_A..VK_Z have no #define in winuser.h, so the generator emits
            # the character literal ('A') rather than the bare name.
            assert f"'{letter}'," in source


# --- Turkish-Q-specific VK mapping (flagged for manual verification) ------


def test_turkish_specific_physical_keys_have_a_vk_oem_guess():
    for physical_key in ("KeyCCedilla", "KeyGBreve", "KeyISlash", "KeySCedilla"):
        assert physical_key in PHYSICAL_KEY_TO_VK
        assert PHYSICAL_KEY_TO_VK[physical_key].startswith("VK_OEM_")


def test_turkish_specific_vk_values_match_real_kbdtuq_driver():
    # These four VK_OEM_* assignments were confirmed empirically against the
    # real Windows-shipped Turkish Q driver (KBDTUQ.DLL) rather than guessed:
    #   VK_OEM_1 -> s,/S with cedilla ; VK_OEM_4 -> g-breve ; VK_OEM_5 -> c-cedilla ; VK_OEM_7 -> dotted I
    assert PHYSICAL_KEY_TO_VK["KeySCedilla"] == "VK_OEM_1"
    assert PHYSICAL_KEY_TO_VK["KeyGBreve"] == "VK_OEM_4"
    assert PHYSICAL_KEY_TO_VK["KeyCCedilla"] == "VK_OEM_5"
    assert PHYSICAL_KEY_TO_VK["KeyISlash"] == "VK_OEM_7"


def test_generated_source_from_real_layout_resolves_turkish_specific_keys():
    from kittgen.parser import parse_layout_file
    from pathlib import Path

    layout_path = Path(__file__).resolve().parent.parent.parent / "layout" / "kitt.uk-UA.yaml"
    spec = parse_layout_file(layout_path)
    source = generate_kbdtables_source(spec)
    for physical_key in ("KeyCCedilla", "KeyGBreve", "KeyISlash", "KeySCedilla"):
        if physical_key in spec.keys or physical_key in spec.dead_keys:
            vk = PHYSICAL_KEY_TO_VK[physical_key]
            assert f"{vk}," in source


# --- real layout end-to-end ------------------------------------------------


def test_generate_kbdtables_source_from_real_layout(layout_spec):
    source = generate_kbdtables_source(layout_spec)
    assert "KBDTABLES" in source
    assert "KbdLayerDescriptor" in source
    assert "WCH_DEAD" in source  # Y dead key
    # Every Ukrainian letter reachable via plain keys must show up as a
    # WCHAR literal in the source.
    for outputs in layout_spec.keys.values():
        for char in outputs.by_modifier.values():
            literal = f"0x{ord(char):04X}"
            assert literal in source


def test_generate_kbdtables_source_from_real_layout_is_deterministic(layout_spec):
    source_a = generate_kbdtables_source(layout_spec)
    source_b = generate_kbdtables_source(layout_spec)
    assert source_a == source_b
