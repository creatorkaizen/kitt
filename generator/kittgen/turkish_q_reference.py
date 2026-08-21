"""Loader for the *real* Windows Turkish Q keyboard driver's tables.

Why this module exists
----------------------

Kitt is a Ukrainian mnemonic layout designed to sit on top of a Turkish Q
physical keyboard. Earlier versions of the generator built the Windows
KBDTABLES from scratch: they emitted a row for every Ukrainian letter Kitt
maps, plus a hand-curated list of "extra" keys somebody remembered to add
(digits, then space, then the arrow keys, then Insert/Delete/Home/End...).

That approach is structurally wrong. A keyboard-layout DLL's tables are the
*only* source of truth Windows consults: a VK with no row in any
`aVkToWchars*` table produces nothing at all, and a shift state that no
`aModification[]` entry maps to a Modification Number is simply dead. So
every key or modifier combination nobody thought to add by hand silently
stopped working — which is exactly what real-machine testing kept turning
up, one forgotten key at a time (AltGr, Ctrl+Alt, `"`, `é`, the dead-key
accents...).

The fix is to invert the default. Instead of "start empty, add what we
remember", Kitt now starts from the *complete* table set of the real
Windows-shipped Turkish Q driver and overrides only the handful of keys
Kitt actually intends to change. Anything Kitt does not deliberately remap
keeps behaving exactly as it does on a stock Turkish Q keyboard, including
shift states Kitt itself has no opinion about.

Where the data comes from
-------------------------

`kbdtuq_reference.json` at the repo root is a programmatic dump of
`C:\\Windows\\System32\\KBDTUQ.DLL`, produced by loading it with
`LoadLibraryExW(..., DONT_RESOLVE_DLL_REFERENCES)`, calling its exported
`KbdLayerDescriptor()`, and walking the returned `KBDTABLES` struct. It is
the actual shipping driver's data, not a transcription of documentation, so
it is authoritative for every question of the form "what does the real
Turkish Q layout do here?".

This module only parses and models that dump. It makes no Kitt-specific
decisions; `windows.py` applies Kitt's overrides on top of the model this
module returns.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

# `wch[]` sentinel values from kbd.h. Kept as distinct Python singletons
# rather than as their raw 0xF000/0xF001 integers so that a sentinel can
# never be confused with an ordinary code point during override logic, and
# so the C renderer can emit the symbolic name (WCH_NONE / WCH_DEAD) that a
# human reading the generated table expects to see.
WCH_NONE = "WCH_NONE"
WCH_DEAD = "WCH_DEAD"

WCH_SENTINELS: frozenset[str] = frozenset({WCH_NONE, WCH_DEAD})

# kbd.h: "Special values for VirtualKey: -1 - This entry contains dead
# chars for the previous entry". The JSON dump renders that -1 row as the
# string "DEADCHARS" rather than a number.
DEADCHARS_VK = "DEADCHARS"

# kbd.h: SHFT_INVALID (0x0F) means "no characters produced with this shift
# state" — the mechanism that keeps Ctrl+<letter> a shortcut instead of a
# character (KITT_ARCHITECTURE.md section 7, "Safety invariants").
SHFT_INVALID = 0x0F

DEFAULT_REFERENCE_FILENAME = "kbdtuq_reference.json"


@dataclass(frozen=True)
class VkToBit:
    """One `aVkToBits[]` row: a modifier VK and the bit it contributes."""

    vk: int
    mod_bits: int


@dataclass(frozen=True)
class VscToVk:
    """One scan-code -> virtual-key association."""

    vsc: int
    vk: int


@dataclass(frozen=True)
class WcharRow:
    """One `VK_TO_WCHARS<n>` row.

    `vk` is either an integer virtual-key code or `DEADCHARS_VK` for the
    kbd.h "-1" row that carries the dead characters of the row above it.

    `wch` holds exactly `nModifications` entries, each either an `int` code
    point or one of the `WCH_NONE` / `WCH_DEAD` sentinel strings.
    """

    vk: int | str
    attr: int
    wch: tuple[int | str, ...]

    @property
    def is_deadchars(self) -> bool:
        return self.vk == DEADCHARS_VK


@dataclass(frozen=True)
class WcharGroup:
    """One `VK_TO_WCHAR_TABLE` entry: all rows sharing a shift-state count."""

    n_modifications: int
    rows: tuple[WcharRow, ...] = ()


@dataclass(frozen=True)
class DeadKeyEntry:
    """One `DEADTRANS(...)` row from the driver's `aDeadKey[]` table."""

    ch: int
    accent: int
    composed: int
    flags: int


@dataclass(frozen=True)
class TurkishQReference:
    """The complete KBDTABLES content of the real Turkish Q driver."""

    vk_to_bits: tuple[VkToBit, ...]
    max_mod_bits: int
    modification_numbers: tuple[int, ...]
    vsc_to_vk: tuple[VscToVk, ...]
    vsc_to_vk_e0: tuple[VscToVk, ...]
    vsc_to_vk_e1: tuple[VscToVk, ...]
    wchar_groups: tuple[WcharGroup, ...]
    dead_keys: tuple[DeadKeyEntry, ...]
    locale_flags: int
    dw_type: int
    dw_sub_type: int

    # --- derived lookups ---------------------------------------------------

    def find_row(self, vk: int) -> tuple[WcharGroup, WcharRow] | None:
        """Locate the `(group, row)` describing `vk`'s character outputs.

        Returns `None` if this VK produces no characters at all in the real
        Turkish Q layout (e.g. it is a pure navigation key).
        """
        for group in self.wchar_groups:
            for row in group.rows:
                if row.vk == vk:
                    return group, row
        return None

    def deadchars_row_for(self, vk: int) -> WcharRow | None:
        """Return the DEADCHARS row belonging to `vk`'s row, if it has one.

        Per kbd.h, a row containing `WCH_DEAD` is immediately followed by a
        `VirtualKey == -1` row holding the dead-key identity characters for
        each shift state.
        """
        for group in self.wchar_groups:
            for index, row in enumerate(group.rows):
                if row.vk != vk:
                    continue
                following = group.rows[index + 1] if index + 1 < len(group.rows) else None
                if following is not None and following.is_deadchars:
                    return following
                return None
        return None

    def modifier_index_for_modification_number(self, mod_number: int) -> int | None:
        """Reverse `aModification[]`: which (CTRL,ALT,SHIFT) bit combination
        selects `mod_number`.

        Used only for diagnostics/tests; the generated tables carry the
        forward mapping.
        """
        for index, value in enumerate(self.modification_numbers):
            if value == mod_number:
                return index
        return None


def _parse_wch(value: object) -> int | str:
    """Normalize one `wch[]` element from JSON into an int or a sentinel."""
    if isinstance(value, str):
        if value not in WCH_SENTINELS:
            raise ValueError(
                f"unknown wch sentinel {value!r} in reference data; expected "
                f"one of {sorted(WCH_SENTINELS)} or an integer code point"
            )
        return value
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"wch element must be an int or sentinel string, got {value!r}")
    return value


def _parse_wchar_row(raw: dict) -> WcharRow:
    vk_raw = raw["vk"]
    if isinstance(vk_raw, str):
        if vk_raw != DEADCHARS_VK:
            raise ValueError(
                f"unknown virtual-key sentinel {vk_raw!r}; expected an integer "
                f"or {DEADCHARS_VK!r}"
            )
        vk: int | str = DEADCHARS_VK
    else:
        vk = int(vk_raw)
    return WcharRow(
        vk=vk,
        attr=int(raw["attr"]),
        wch=tuple(_parse_wch(value) for value in raw["wch"]),
    )


def _parse_wchar_group(raw: dict) -> WcharGroup:
    n_modifications = int(raw["nModifications"])
    rows = tuple(_parse_wchar_row(row) for row in raw["rows"])
    for row in rows:
        if len(row.wch) != n_modifications:
            raise ValueError(
                f"row for VK {row.vk!r} has {len(row.wch)} wch entries but its "
                f"group declares nModifications={n_modifications}"
            )
    return WcharGroup(n_modifications=n_modifications, rows=rows)


def parse_reference(data: dict) -> TurkishQReference:
    """Build a `TurkishQReference` from an already-loaded JSON dict."""
    return TurkishQReference(
        vk_to_bits=tuple(
            VkToBit(vk=int(entry["vk"]), mod_bits=int(entry["modBits"]))
            for entry in data["vkToBits"]
        ),
        max_mod_bits=int(data["wMaxModBits"]),
        modification_numbers=tuple(int(value) for value in data["modNumber"]),
        vsc_to_vk=tuple(
            VscToVk(vsc=int(e["vsc"]), vk=int(e["vk"])) for e in data["vscToVk"]
        ),
        vsc_to_vk_e0=tuple(
            VscToVk(vsc=int(e["vsc"]), vk=int(e["vk"])) for e in data["vscToVkE0"]
        ),
        vsc_to_vk_e1=tuple(
            VscToVk(vsc=int(e["vsc"]), vk=int(e["vk"])) for e in data["vscToVkE1"]
        ),
        wchar_groups=tuple(_parse_wchar_group(g) for g in data["vkToWchars"]),
        dead_keys=tuple(
            DeadKeyEntry(
                ch=int(e["ch"]),
                accent=int(e["accent"]),
                composed=int(e["composed"]),
                flags=int(e["flags"]),
            )
            for e in data["deadKeys"]
        ),
        locale_flags=int(data["fLocaleFlags"]),
        dw_type=int(data["dwType"]),
        dw_sub_type=int(data["dwSubType"]),
    )


def find_reference_path(start: Path | None = None) -> Path:
    """Locate `kbdtuq_reference.json` by walking up from `start`.

    Defaults to searching upward from this module, so the generator works
    both when run from the repo root and when the package is installed in
    editable mode from a different working directory.
    """
    origin = (start or Path(__file__)).resolve()
    for candidate_dir in (origin, *origin.parents):
        candidate = candidate_dir / DEFAULT_REFERENCE_FILENAME
        if candidate.is_file():
            return candidate
    raise FileNotFoundError(
        f"could not find {DEFAULT_REFERENCE_FILENAME} in any parent directory "
        f"of {origin}. This file is the dump of the real Windows Turkish Q "
        "driver and is required to generate Kitt's tables."
    )


def load_reference(path: Path | str | None = None) -> TurkishQReference:
    """Load and parse the Turkish Q reference dump."""
    resolved = Path(path) if path is not None else find_reference_path()
    with Path(resolved).open(encoding="utf-8") as handle:
        return parse_reference(json.load(handle))
