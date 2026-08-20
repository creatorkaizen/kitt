from __future__ import annotations

import pytest

EXPECTED_BASE_KEYS = {
    "KeyA": ("а", "А"),
    "KeyB": ("б", "Б"),
    "KeyD": ("д", "Д"),
    "KeyE": ("е", "Е"),
    "KeyF": ("ф", "Ф"),
    "KeyK": ("к", "К"),
    "KeyL": ("л", "Л"),
    "KeyM": ("м", "М"),
    "KeyN": ("н", "Н"),
    "KeyO": ("о", "О"),
    "KeyP": ("п", "П"),
    "KeyR": ("р", "Р"),
    "KeyS": ("с", "С"),
    "KeyT": ("т", "Т"),
    "KeyU": ("у", "У"),
    "KeyV": ("в", "В"),
    "KeyZ": ("з", "З"),
    "KeyC": ("ц", "Ц"),
    "KeyCCedilla": ("ч", "Ч"),
    "KeyG": ("ґ", "Ґ"),
    "KeyGBreve": ("г", "Г"),
    "KeyH": ("х", "Х"),
    "KeyI": ("и", "И"),
    "KeyISlash": ("і", "І"),
    "KeyJ": ("ж", "Ж"),
    "KeyQ": ("щ", "Щ"),
    "KeySCedilla": ("ш", "Ш"),
    "KeyX": ("ь", "Ь"),
}


@pytest.mark.parametrize(("physical_key", "expected"), sorted(EXPECTED_BASE_KEYS.items()))
def test_key_base_and_shift_outputs(layout_spec, physical_key, expected):
    expected_base, expected_shift = expected
    outputs = layout_spec.keys[physical_key]
    assert outputs.get("base") == expected_base
    assert outputs.get("shift") == expected_shift


def test_every_key_has_base_and_shift_defined(layout_spec):
    for physical_key, outputs in layout_spec.keys.items():
        assert outputs.get("base") is not None, f"{physical_key} missing base output"
        assert outputs.get("shift") is not None, f"{physical_key} missing shift output"


def test_shift_output_is_uppercase_of_base_output(layout_spec):
    for physical_key, outputs in layout_spec.keys.items():
        base = outputs.get("base")
        shift = outputs.get("shift")
        assert shift == base.upper(), (
            f"{physical_key}: shift output {shift!r} is not the uppercase form "
            f"of base output {base!r}"
        )


def test_base_output_is_lowercase_of_shift_output(layout_spec):
    for physical_key, outputs in layout_spec.keys.items():
        base = outputs.get("base")
        shift = outputs.get("shift")
        assert base == shift.lower(), (
            f"{physical_key}: base output {base!r} is not the lowercase form "
            f"of shift output {shift!r}"
        )


def test_only_base_and_shift_modifiers_declared(layout_spec):
    assert layout_spec.modifiers == ("base", "shift")


def test_dead_key_y_present(layout_spec):
    assert "Y" in layout_spec.dead_keys


def test_dead_key_y_alone_produces_i_korotke(layout_spec):
    dead_spec = layout_spec.dead_keys["Y"]
    assert dead_spec.alone.get("base") == "й"
    assert dead_spec.alone.get("shift") == "Й"


@pytest.mark.parametrize(
    ("following_key", "expected_base", "expected_shift"),
    [
        ("KeyA", "я", "Я"),
        ("KeyU", "ю", "Ю"),
        ("KeyE", "є", "Є"),
        ("KeyISlash", "ї", "Ї"),
    ],
)
def test_dead_key_y_combinations(layout_spec, following_key, expected_base, expected_shift):
    dead_spec = layout_spec.dead_keys["Y"]
    combo = dead_spec.combinations[following_key]
    assert combo.get("base") == expected_base
    assert combo.get("shift") == expected_shift


def test_dead_key_y_has_exactly_four_combinations(layout_spec):
    dead_spec = layout_spec.dead_keys["Y"]
    assert set(dead_spec.combinations.keys()) == {"KeyA", "KeyU", "KeyE", "KeyISlash"}


def test_dead_key_combination_outputs_are_uppercase_consistent(layout_spec):
    dead_spec = layout_spec.dead_keys["Y"]
    for combo_key, combo in dead_spec.combinations.items():
        base = combo.get("base")
        shift = combo.get("shift")
        assert shift == base.upper(), f"Y+{combo_key}: {shift!r} != upper({base!r})"
