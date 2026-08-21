"""Tests for kittgen.windows: YAML LayoutSpec -> Windows KBDTABLES C source.

Kitt generates its Windows tables by taking the *complete* table set of the
real Windows-shipped Turkish Q driver (dumped to kbdtuq_reference.json) and
overriding only the base/Shift outputs of the keys Kitt actually remaps.
These tests therefore check two distinct properties:

  1. Kitt's overrides land where they should (the right VK, the right two
     shift states, the right characters, dead keys marked WCH_DEAD with a
     DEADCHARS identity row).
  2. Everything Kitt does *not* claim survives untouched — AltGr and
     Ctrl+Alt columns, Attributes/CAPLOK flags, the Turkish accent dead
     keys, all three scan-code tables, and fLocaleFlags' KLLF_ALTGR bit.

Property (2) is the reason this module was rewritten: the previous
generator built tables bottom-up from a hand-curated key list, so every key
nobody remembered to add silently produced nothing on a real machine.

These tests check the generated C source as text/structure. An actual
compile-and-load check of the resulting DLL lives outside pytest (it needs
MSVC and a Windows loader); see tools/build.ps1.
"""

from __future__ import annotations

import re

import pytest

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
from kittgen.turkish_q_reference import (
    WCH_DEAD,
    WCH_NONE,
    TurkishQReference,
    load_reference,
)
from kittgen.windows import (
    PHYSICAL_KEY_TO_VK,
    LayoutGenerationError,
    generate_kbdtables_source,
)


@pytest.fixture(scope="module")
def reference() -> TurkishQReference:
    return load_reference()


def _spec_with_dead_keys() -> LayoutSpec:
    keys = {
        "KeyA": KeyOutputs(physical_key="KeyA", by_modifier={"base": "а", "shift": "А"}),
        "KeyB": KeyOutputs(physical_key="KeyB", by_modifier={"base": "б", "shift": "Б"}),
        "KeyU": KeyOutputs(physical_key="KeyU", by_modifier={"base": "у", "shift": "У"}),
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


def _wchars_group(source: str, n: int) -> str:
    """Return the body of the generated VK_TO_WCHARS<n> table."""
    match = re.search(
        rf"static VK_TO_WCHARS{n} kitt_VkToWchars{n}\[\] = \{{(.*?)\n\}};",
        source,
        re.DOTALL,
    )
    assert match is not None, f"no VK_TO_WCHARS{n} table in generated source"
    return match.group(1)


def _row_for(source: str, n: int, vk_expr: str) -> list[str]:
    """Return the wch[] entries of the row for `vk_expr` in group `n`."""
    body = _wchars_group(source, n)
    match = re.search(
        rf"^\s*\{{\s*{re.escape(vk_expr)},\s*([^,]+),\s*\{{([^}}]*)\}}\s*\}},",
        body,
        re.MULTILINE,
    )
    assert match is not None, f"no row for {vk_expr} in VK_TO_WCHARS{n}"
    return [value.strip() for value in match.group(2).split(",")]


def _attr_for(source: str, n: int, vk_expr: str) -> str:
    body = _wchars_group(source, n)
    match = re.search(
        rf"^\s*\{{\s*{re.escape(vk_expr)},\s*([^,]+),\s*\{{",
        body,
        re.MULTILINE,
    )
    assert match is not None, f"no row for {vk_expr} in VK_TO_WCHARS{n}"
    return match.group(1).strip()


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


def test_generated_source_credits_the_turkish_q_reference():
    source = generate_kbdtables_source(_spec_with_dead_keys())
    assert "KBDTUQ" in source


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


def test_generated_source_terminates_vk_to_wchar_table_with_null():
    source = generate_kbdtables_source(_spec_with_dead_keys())
    assert "{ NULL, 0, 0 }" in source


# --- reference tables are copied faithfully ------------------------------


def test_all_reference_wchar_groups_are_emitted(reference):
    # The real Turkish Q driver has six groups (1..6 shift states). Every one
    # must reach the generated source: dropping a group silently deletes
    # every key in it.
    source = generate_kbdtables_source(_spec_with_dead_keys(), reference)
    for group in reference.wchar_groups:
        n = group.n_modifications
        assert f"static VK_TO_WCHARS{n} kitt_VkToWchars{n}[]" in source
        assert f"kitt_VkToWchars{n}, {n}, sizeof(VK_TO_WCHARS{n})" in source


def test_every_reference_vk_has_a_row(reference):
    # Row count per group must match the reference exactly, except for the
    # one group where Kitt's dead key adds a DEADCHARS row.
    source = generate_kbdtables_source(_spec_with_dead_keys(), reference)
    for group in reference.wchar_groups:
        body = _wchars_group(source, group.n_modifications)
        emitted = len(re.findall(r"^\s*\{", body, re.MULTILINE)) - 1  # terminator
        expected = len(group.rows)
        if group.n_modifications == 2:
            expected += 1  # Kitt's Y dead key gains a DEADCHARS row
        assert emitted == expected, (
            f"group n={group.n_modifications}: emitted {emitted} rows, "
            f"reference has {len(group.rows)}"
        )


def test_modification_numbers_copied_from_reference(reference):
    source = generate_kbdtables_source(_spec_with_dead_keys(), reference)
    rendered = re.findall(r"^\s+(SHFT_INVALID|\d+),\s+// \d{3} ", source, re.MULTILINE)
    expected = [
        "SHFT_INVALID" if value == 0x0F else str(value)
        for value in reference.modification_numbers
    ]
    assert rendered == expected


def test_scancode_table_copied_from_reference(reference):
    source = generate_kbdtables_source(_spec_with_dead_keys(), reference)
    # pusVSCtoVK is indexed directly by scan code, so entry N must be scan
    # code N's VK. An earlier off-by-one here shifted every key by one
    # position; keep it pinned.
    rows = re.findall(r"/\* 0x([0-9A-F]{2}) \*/ (.+),", source)
    by_index = {int(code, 16): value for code, value in rows}
    for entry in reference.vsc_to_vk:
        expected = (
            f"'{chr(entry.vk)}'"
            if ("A" <= chr(entry.vk) <= "Z") or ("0" <= chr(entry.vk) <= "9")
            else f"0x{entry.vk:02X}"
        )
        assert by_index[entry.vsc] == expected, f"scan 0x{entry.vsc:02X}"


def test_extended_scancode_tables_copied_from_reference(reference):
    source = generate_kbdtables_source(_spec_with_dead_keys(), reference)
    e0_body = re.search(
        r"kitt_VscToVk_E0\[\] = \{(.*?)\n\};", source, re.DOTALL
    ).group(1)
    assert len(re.findall(r"\{ 0x", e0_body)) == len(reference.vsc_to_vk_e0)
    e1_body = re.search(
        r"kitt_VscToVk_E1\[\] = \{(.*?)\n\};", source, re.DOTALL
    ).group(1)
    assert len(re.findall(r"\{ 0x", e1_body)) == len(reference.vsc_to_vk_e1)


def test_extended_scancode_table_keeps_navigation_keys(reference):
    # Arrow keys, Insert/Delete, and right Alt live only in the E0 table.
    # Leaving it empty made every one of them stop working on a real
    # machine, so pin the specific entries that regression touched.
    source = generate_kbdtables_source(_spec_with_dead_keys(), reference)
    e0_body = re.search(
        r"kitt_VscToVk_E0\[\] = \{(.*?)\n\};", source, re.DOTALL
    ).group(1)
    for vsc, vk in ((0x48, 0x26), (0x50, 0x28), (0x53, 0x2E), (0x38, 0xA5)):
        assert f"{{ 0x{vsc:02X}, 0x{vk:02X} }}" in e0_body


def test_locale_flags_preserve_altgr(reference):
    # KLLF_ALTGR must survive: without it Windows does not treat right-Alt
    # as AltGr at all, making every AltGr column unreachable.
    assert reference.locale_flags & 0x0001
    source = generate_kbdtables_source(_spec_with_dead_keys(), reference)
    assert "MAKELONG(KLLF_ALTGR, KBD_VERSION)" in source


def test_reference_dead_key_entries_are_all_preserved(reference):
    # The real Turkish Q driver's own DEADKEY rows all carry flags=0 (not
    # DKF_DEAD) in KBDTUQ.DLL — confirmed directly from kbdtuq_reference.json,
    # every entry has "flags": 0. _render_dead_keys renders whatever flags
    # value the reference row actually has, so the expected literal must
    # match that, not assume DKF_DEAD unconditionally.
    source = generate_kbdtables_source(_spec_with_dead_keys(), reference)
    for entry in reference.dead_keys:
        flags_literal = "DKF_DEAD" if entry.flags & 1 else f"0x{entry.flags:04X}"
        literal = (
            f"DEADTRANS(0x{entry.ch:04X}, 0x{entry.accent:04X}, "
            f"0x{entry.composed:04X}, {flags_literal})"
        )
        assert literal in source, f"lost Turkish Q dead key {literal}"


def test_reference_deadchars_rows_are_preserved(reference):
    # The Turkish Q accent dead keys (circumflex, acute, diaeresis, grave,
    # tilde) each live in a WCH_DEAD row followed by a DEADCHARS row holding
    # the accent character. Kitt must not drop those rows.
    source = generate_kbdtables_source(_spec_with_dead_keys(), reference)
    for accent in (0x005E, 0x00B4, 0x00A8, 0x0060, 0x007E):
        assert f"0x{accent:04X}" in source, f"lost accent U+{accent:04X}"


# --- Kitt's overrides land correctly ------------------------------------


def test_override_replaces_only_base_and_shift(reference):
    # VK_A lives in the 6-shift-state group of the real driver, with
    # wch = {a, A, ae, WCH_NONE, WCH_NONE, AE}. Kitt replaces columns 0/1
    # with Cyrillic and must leave columns 2..5 exactly as they were.
    source = generate_kbdtables_source(_spec_with_dead_keys(), reference)
    _group, ref_row = reference.find_row(ord("A"))
    values = _row_for(source, 6, "'A'")
    assert values[0] == f"0x{ord('а'):04X}"
    assert values[1] == f"0x{ord('А'):04X}"
    for index in range(2, len(ref_row.wch)):
        original = ref_row.wch[index]
        expected = original if isinstance(original, str) else f"0x{original:04X}"
        assert values[index] == expected, f"VK_A column {index} was modified"


def test_override_preserves_attributes(reference):
    # VK_A carries CAPLOK|CAPLOKALTGR (0x05) in the real driver. Dropping
    # CAPLOKALTGR would change Caps Lock behavior in the AltGr layer.
    _group, ref_row = reference.find_row(ord("A"))
    assert ref_row.attr == 0x05
    source = generate_kbdtables_source(_spec_with_dead_keys(), reference)
    assert _attr_for(source, 6, "'A'") == "CAPLOK | CAPLOKALTGR"


def test_unmapped_keys_keep_reference_output(reference):
    # VK_OEM_3 (0xC0) is the '"' key: base '"', Shift 'é', Ctrl+Alt '<'.
    # Kitt has no opinion about it, so all three must pass through. This is
    # the key whose missing 'é' prompted the reference-driven rewrite.
    source = generate_kbdtables_source(_spec_with_dead_keys(), reference)
    values = _row_for(source, 3, "0xC0")
    assert values == ["0x0022", "0x00E9", "0x003C"]


def test_digit_two_keeps_real_turkish_q_shift_output(reference):
    # Shift+2 on a real Turkish Q keyboard is an apostrophe (U+0027), and
    # Ctrl+Alt+2 is a pound sign — not something Kitt should invent.
    source = generate_kbdtables_source(_spec_with_dead_keys(), reference)
    values = _row_for(source, 5, "'2'")
    assert values[0] == "0x0032"
    assert values[1] == "0x0027"
    assert values[2] == "0x00A3"


def test_override_of_a_key_with_a_dead_altgr_layer_keeps_it(reference):
    # VK_OEM_1 (Ş) has an AltGr acute-accent dead key in the real driver.
    # Kitt overrides its base/Shift to ш/Ш; the dead layer must remain.
    spec = _spec_with_dead_keys()
    keys = dict(spec.keys)
    keys["KeySCedilla"] = KeyOutputs(
        physical_key="KeySCedilla", by_modifier={"base": "ш", "shift": "Ш"}
    )
    spec = LayoutSpec(
        schema_version=spec.schema_version,
        metadata=spec.metadata,
        physical_layout=spec.physical_layout,
        modifiers=spec.modifiers,
        keys=keys,
        dead_keys=spec.dead_keys,
        punctuation=spec.punctuation,
        behavior=spec.behavior,
    )
    source = generate_kbdtables_source(spec, reference)
    values = _row_for(source, 3, "VK_OEM_1")
    assert values == [f"0x{ord('ш'):04X}", f"0x{ord('Ш'):04X}", WCH_DEAD]
    # ...and its DEADCHARS row (acute, U+00B4) must still follow it.
    body = _wchars_group(source, 3)
    match = re.search(
        r"VK_OEM_1,[^\n]*\n\s*\{ 0xFF, [^,]+, \{([^}]*)\}", body
    )
    assert match is not None, "VK_OEM_1 lost its DEADCHARS row"
    assert "0x00B4" in match.group(1)


def test_mapped_vk_uses_character_literal():
    # winuser.h does not #define VK_A..VK_Z / VK_0..VK_9 (they are documented
    # as numerically equal to their ASCII codes), so the generator must emit
    # a character literal ('A'), not the bare name "VK_A" — using the bare
    # name fails to compile with MSVC (confirmed empirically).
    source = generate_kbdtables_source(_spec_with_dead_keys())
    assert "{ 'A'," in source
    assert "{ 'B'," in source
    assert "VK_A," not in source


# --- dead keys ------------------------------------------------------------


def test_dead_key_trigger_uses_wch_dead():
    source = generate_kbdtables_source(_spec_with_dead_keys())
    values = _row_for(source, 2, "'Y'")
    assert values == [WCH_DEAD, WCH_DEAD]


def test_dead_key_emits_deadchars_identity_row():
    # Without a DEADCHARS row, Windows has no identity character for the
    # dead key and the DEADTRANS lookups can never match — the dead key is
    # simply inert. An earlier revision omitted this row entirely.
    source = generate_kbdtables_source(_spec_with_dead_keys())
    body = _wchars_group(source, 2)
    match = re.search(r"'Y',[^\n]*\n\s*\{ 0xFF, [^,]+, \{([^}]*)\}", body)
    assert match is not None, "Y has no DEADCHARS row"
    values = [v.strip() for v in match.group(1).split(",")]
    assert values == [f"0x{ord('й'):04X}", f"0x{ord('Й'):04X}"]


def test_deadtrans_uses_per_shift_state_identity():
    # Y's identity is 'й' unshifted and 'Й' shifted. A shifted combination
    # must compose against the shifted identity, otherwise Shift+Y then
    # Shift+A never matches at runtime.
    source = generate_kbdtables_source(_spec_with_dead_keys())
    assert (
        f"DEADTRANS(0x{ord('а'):04X}, 0x{ord('й'):04X}, "
        f"0x{ord('я'):04X}, DKF_DEAD)" in source
    )
    assert (
        f"DEADTRANS(0x{ord('А'):04X}, 0x{ord('Й'):04X}, "
        f"0x{ord('Я'):04X}, DKF_DEAD)" in source
    )


def test_deadkey_table_still_present_without_kitt_dead_keys(reference):
    # Even with no Kitt dead key, the Turkish Q accent table must survive:
    # pDeadKey must point at it rather than being NULL.
    source = generate_kbdtables_source(_spec_without_dead_keys(), reference)
    assert "kitt_DeadKey,                        // pDeadKey" in source
    assert "DEADTRANS(" in source
    # ...but none of Kitt's own combinations should appear.
    assert f"0x{ord('я'):04X}, DKF_DEAD" not in source


def test_no_dead_key_leaves_vk_y_as_a_normal_letter(reference):
    source = generate_kbdtables_source(_spec_without_dead_keys(), reference)
    values = _row_for(source, 2, "'Y'")
    assert values == ["0x0079", "0x0059"]  # plain Latin y/Y from KBDTUQ


# --- error handling -------------------------------------------------------


def test_unknown_physical_key_is_rejected():
    spec = _spec_with_dead_keys()
    keys = dict(spec.keys)
    keys["KeyNonexistent"] = KeyOutputs(
        physical_key="KeyNonexistent", by_modifier={"base": "ж"}
    )
    spec = LayoutSpec(
        schema_version=spec.schema_version,
        metadata=spec.metadata,
        physical_layout=spec.physical_layout,
        modifiers=spec.modifiers,
        keys=keys,
        dead_keys=spec.dead_keys,
        punctuation=spec.punctuation,
        behavior=spec.behavior,
    )
    with pytest.raises(LayoutGenerationError, match="no known VK"):
        generate_kbdtables_source(spec)


def test_key_with_no_reference_row_is_rejected(reference):
    # VK_W exists in the reference, so use a key that resolves to a VK with
    # no character row at all. F13 (VK 0x7C) has none.
    spec = _spec_with_dead_keys()
    keys = dict(spec.keys)
    keys["KeyW"] = KeyOutputs(physical_key="KeyW", by_modifier={"base": "ю"})
    spec = LayoutSpec(
        schema_version=spec.schema_version,
        metadata=spec.metadata,
        physical_layout=spec.physical_layout,
        modifiers=spec.modifiers,
        keys=keys,
        dead_keys=spec.dead_keys,
        punctuation=spec.punctuation,
        behavior=spec.behavior,
    )
    # VK_W does have a row, so this should succeed rather than raise.
    source = generate_kbdtables_source(spec, reference)
    assert _row_for(source, 2, "'W'")[0] == f"0x{ord('ю'):04X}"


# --- Turkish-Q-specific VK mapping ---------------------------------------


def test_turkish_specific_physical_keys_map_to_vk_oem():
    for physical_key in ("KeyCCedilla", "KeyGBreve", "KeyISlash", "KeySCedilla"):
        assert physical_key in PHYSICAL_KEY_TO_VK
        assert PHYSICAL_KEY_TO_VK[physical_key].startswith("VK_OEM_")


def test_turkish_specific_vk_values_match_real_kbdtuq_driver(reference):
    # These four VK_OEM_* assignments are confirmed against the real driver
    # dump: each VK is the row that actually produces that Turkish letter.
    expected = {
        "KeySCedilla": ("VK_OEM_1", 0xBA, 0x015F, 0x015E),
        "KeyGBreve": ("VK_OEM_4", 0xDB, 0x011F, 0x011E),
        "KeyCCedilla": ("VK_OEM_5", 0xDC, 0x00E7, 0x00C7),
        "KeyISlash": ("VK_OEM_7", 0xDE, 0x0069, 0x0130),
    }
    for physical_key, (vk_name, vk, lower, upper) in expected.items():
        assert PHYSICAL_KEY_TO_VK[physical_key] == vk_name
        hit = reference.find_row(vk)
        assert hit is not None, f"{vk_name} missing from reference"
        _group, row = hit
        assert row.wch[0] == lower
        assert row.wch[1] == upper


# --- real layout end-to-end ------------------------------------------------


def test_generate_kbdtables_source_from_real_layout(layout_spec):
    source = generate_kbdtables_source(layout_spec)
    assert "KBDTABLES" in source
    assert "KbdLayerDescriptor" in source
    assert WCH_DEAD in source  # Y dead key
    for outputs in layout_spec.keys.values():
        for char in outputs.by_modifier.values():
            assert f"0x{ord(char):04X}" in source


def test_real_layout_overrides_every_mapped_key(layout_spec, reference):
    # Every key in the YAML must actually reach a row in the generated
    # tables. Silent omission is the exact failure mode this architecture
    # exists to prevent, so assert it directly rather than trusting that
    # generation "probably" covered everything.
    source = generate_kbdtables_source(layout_spec, reference)
    name_to_vk = {"KeyCCedilla": 0xDC, "KeyGBreve": 0xDB, "KeyISlash": 0xDE,
                  "KeySCedilla": 0xBA}
    for physical_key, outputs in layout_spec.keys.items():
        vk = name_to_vk.get(physical_key)
        if vk is None:
            vk = ord(physical_key[3])
        group, _row = reference.find_row(vk)
        vk_expr = (
            f"'{chr(vk)}'"
            if ("A" <= chr(vk) <= "Z")
            else f"VK_OEM_{ {0xBA: 1, 0xDB: 4, 0xDC: 5, 0xDE: 7}[vk] }"
        )
        values = _row_for(source, group.n_modifications, vk_expr)
        assert values[0] == f"0x{ord(outputs.by_modifier['base']):04X}", physical_key
        assert values[1] == f"0x{ord(outputs.by_modifier['shift']):04X}", physical_key


def test_real_layout_keeps_ctrl_shortcuts_safe(layout_spec):
    # Safety invariant (KITT_ARCHITECTURE.md section 7): Ctrl+<letter> must
    # not emit a letter. The reference aModification[] already marks the
    # pure-CTRL (index 4) and SHIFT+CTRL (index 5) states SHFT_INVALID.
    source = generate_kbdtables_source(layout_spec)
    assert re.search(r"SHFT_INVALID,\s+// 100 CTRL", source)
    assert re.search(r"SHFT_INVALID,\s+// 101 SHIFT CTRL", source)


def test_real_layout_produces_all_eight_kitt_deadtrans_rows(layout_spec):
    source = generate_kbdtables_source(layout_spec)
    kitt_rows = re.findall(r"DEADTRANS\([^)]*\),\s*// Kitt:", source)
    assert len(kitt_rows) == 8, "expected я/Я/ю/Ю/є/Є/ї/Ї"


def test_generate_kbdtables_source_from_real_layout_is_deterministic(layout_spec):
    source_a = generate_kbdtables_source(layout_spec)
    source_b = generate_kbdtables_source(layout_spec)
    assert source_a == source_b


def test_generated_source_stays_a_reasonable_size(layout_spec):
    # The reference tables are a few hundred rows; a multi-megabyte result
    # would mean something duplicated a table in a loop.
    source = generate_kbdtables_source(layout_spec)
    assert 10_000 < len(source) < 200_000, len(source)


def test_wch_none_sentinel_is_emitted_symbolically(layout_spec):
    # WCH_NONE must reach the C source as the kbd.h name, not as 0xF000:
    # a bare 0xF000 would still compile but reads as a real code point.
    source = generate_kbdtables_source(layout_spec)
    assert WCH_NONE in source
    assert "0xF000" not in source
