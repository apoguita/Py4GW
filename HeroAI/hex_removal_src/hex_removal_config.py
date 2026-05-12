"""Per-character JSONC persistence for hex-removal priority overrides.

File: <projects>/Settings/<account_email>/HeroAI/Hex removal/<character_name>/hex_removal_config.json

Each character on the account has an independent config. The GUI at
HeroAI Control Panel -> Builds -> Hex Removal edits this file; hand
edits are also supported via JSONC (// line and /* */ block comments).
Hand-edits are picked up next time HeroAI loads.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field

import Py4GW

from Py4GWCoreLib.enums_src.GameData_enums import Profession, Profession_Names
from Py4GWCoreLib.GlobalCache.HexRemovalPriority import (
    HexRemovalEntry,
    HexRemovalPriority,
    _HEX_DEFAULTS,
)


# ============================================================================
# Constants
# ============================================================================

SCHEMA_ID = "py4gw_hex_removal_v1"
CONFIG_FILENAME = "hex_removal_config.json"
# Folder under Settings/<email>/HeroAI/ that holds per-character configs.
CONFIG_SUBDIR = "Hex removal"

_PRIORITY_BY_NAME: dict[str, HexRemovalPriority] = {
    "NONE": HexRemovalPriority.NONE,
    "LOW":  HexRemovalPriority.LOW,
    "MED":  HexRemovalPriority.MEDIUM,
    "HIGH": HexRemovalPriority.HIGH,
}
_NAME_BY_PRIORITY: dict[HexRemovalPriority, str] = {
    v: k for k, v in _PRIORITY_BY_NAME.items()
}

_PROFESSION_BY_NAME: dict[str, int] = {
    Profession_Names[p]: int(p)
    for p in Profession if p != Profession._None
}
_NAME_BY_PROFESSION_ID: dict[int, str] = {
    v: k for k, v in _PROFESSION_BY_NAME.items()
}

_PROFESSION_ORDER: list[int] = [
    int(Profession.Warrior), int(Profession.Ranger), int(Profession.Monk),
    int(Profession.Necromancer), int(Profession.Mesmer), int(Profession.Elementalist),
    int(Profession.Assassin), int(Profession.Ritualist), int(Profession.Paragon),
    int(Profession.Dervish),
]


# ============================================================================
# In-memory state
# ============================================================================

@dataclass
class HexEntryState:
    entry: HexRemovalEntry


@dataclass
class ConfigState:
    debug_hex_removal: bool = True
    debug_hex_removal_locks: bool = False
    hexes: dict[str, HexEntryState] = field(default_factory=dict)


# Cache key is (email, character_name); reloads when the active
# character changes mid-session (multibox / character switch).
_cache_key: tuple[str, str] = ("", "")
_cache_state: ConfigState | None = None


# ============================================================================
# Logging + path helpers
# ============================================================================

def _log(msg: str) -> None:
    try:
        from Py4GWCoreLib import ConsoleLog
        ConsoleLog("HexRemoval", msg, Py4GW.Console.MessageType.Info)
    except Exception:
        pass


def _projects_settings_root() -> str:
    return os.path.join(Py4GW.Console.get_projects_path(), "Settings")


def _path_for(email: str, character_name: str) -> str:
    return os.path.join(
        _projects_settings_root(),
        email,
        "HeroAI",
        CONFIG_SUBDIR,
        character_name,
        CONFIG_FILENAME,
    )


def _active_account_key() -> tuple[str, str]:
    """Returns (email, character_name). Either may be empty if not ready."""
    try:
        from Py4GWCoreLib.Player import Player
        email = (Player.GetAccountEmail() or "").strip()
        char = (Player.GetName() or "").strip()
        return email, char
    except Exception:
        return "", ""


def _desktop_path() -> str:
    return os.path.join(os.path.expanduser("~"), "Desktop", CONFIG_FILENAME)


# ============================================================================
# JSONC strip
# ============================================================================

def _strip_jsonc(text: str) -> str:
    """Remove // and /* */ comments while preserving them inside strings."""
    out: list[str] = []
    i, n = 0, len(text)
    while i < n:
        c = text[i]
        if c == '"':
            j = i + 1
            while j < n:
                if text[j] == '\\' and j + 1 < n:
                    j += 2
                    continue
                if text[j] == '"':
                    j += 1
                    break
                j += 1
            out.append(text[i:j])
            i = j
            continue
        if c == '/' and i + 1 < n and text[i + 1] == '/':
            nl = text.find('\n', i)
            i = n if nl == -1 else nl
            continue
        if c == '/' and i + 1 < n and text[i + 1] == '*':
            end = text.find('*/', i + 2)
            i = n if end == -1 else end + 2
            continue
        out.append(c)
        i += 1
    return ''.join(out)


# ============================================================================
# Parsing
# ============================================================================

def _parse_priority(value: object) -> HexRemovalPriority | None:
    if not isinstance(value, str):
        return None
    return _PRIORITY_BY_NAME.get(value.strip().upper())


def _parse_profession_id(value: object) -> int | None:
    if not isinstance(value, str):
        return None
    return _PROFESSION_BY_NAME.get(value.strip())


def _parse_entry(name: str, blob: object) -> HexEntryState | None:
    if not isinstance(blob, dict):
        _log(f"config: skipping '{name}' - not an object")
        return None
    caster = _parse_priority(blob.get("caster"))
    ranged = _parse_priority(blob.get("ranged_martial"))
    melee = _parse_priority(blob.get("melee"))
    if caster is None or ranged is None or melee is None:
        _log(f"config: skipping '{name}' - invalid role priority")
        return None
    by_prof_blob = blob.get("by_profession", {}) or {}
    by_prof: dict[int, HexRemovalPriority] = {}
    if isinstance(by_prof_blob, dict):
        for prof_name, prio_name in by_prof_blob.items():
            pid = _parse_profession_id(prof_name)
            prio = _parse_priority(prio_name)
            if pid is None:
                _log(f"config: '{name}' - unknown profession '{prof_name}', dropped")
                continue
            if prio is None:
                _log(f"config: '{name}' - invalid priority for '{prof_name}', dropped")
                continue
            by_prof[pid] = prio
    # "modified" field in older files is intentionally ignored (legacy).
    return HexEntryState(
        entry=HexRemovalEntry(
            caster=caster,
            ranged_martial=ranged,
            melee=melee,
            by_profession=by_prof,
        ),
    )


def _parse_file(text: str) -> ConfigState | None:
    try:
        stripped = _strip_jsonc(text)
        if not stripped.strip():
            return None
        data = json.loads(stripped)
    except Exception as exc:
        _log(f"config: parse error - {exc!r}")
        return None
    if not isinstance(data, dict) or data.get("schema") != SCHEMA_ID:
        _log(f"config: unrecognized schema (expected '{SCHEMA_ID}')")
        return None

    state = ConfigState()
    debug_blob = data.get("debug", {}) or {}
    if isinstance(debug_blob, dict):
        state.debug_hex_removal = bool(debug_blob.get("hex_removal", True))
        state.debug_hex_removal_locks = bool(debug_blob.get("hex_removal_locks", False))

    hexes_blob = data.get("hexes", {}) or {}
    if isinstance(hexes_blob, dict):
        for name, blob in hexes_blob.items():
            if not isinstance(name, str):
                continue
            parsed = _parse_entry(name, blob)
            if parsed is not None:
                state.hexes[name] = parsed
    return state


# ============================================================================
# Serialization
# ============================================================================

def _profession_for_hex(name: str) -> int:
    try:
        from Py4GWCoreLib import GLOBAL_CACHE
        sid = GLOBAL_CACHE.Skill.GetID(name)
        if sid <= 0:
            return 0
        prof_value, _prof_name = GLOBAL_CACHE.Skill.GetProfession(sid)
        return int(prof_value or 0)
    except Exception:
        return 0


def _serialize_entry_object(entry: HexRemovalEntry) -> str:
    parts = [
        f'"caster": "{_NAME_BY_PRIORITY[entry.caster]}"',
        f'"ranged_martial": "{_NAME_BY_PRIORITY[entry.ranged_martial]}"',
        f'"melee": "{_NAME_BY_PRIORITY[entry.melee]}"',
    ]
    if entry.by_profession:
        bp_pairs: list[str] = []
        for pid in _PROFESSION_ORDER:
            if pid in entry.by_profession:
                pname = _NAME_BY_PROFESSION_ID[pid]
                vname = _NAME_BY_PRIORITY[entry.by_profession[pid]]
                bp_pairs.append(f'"{pname}": "{vname}"')
        parts.append('"by_profession": { ' + ', '.join(bp_pairs) + ' }')
    else:
        parts.append('"by_profession": {}')
    return '{ ' + ', '.join(parts) + ' }'


_FILE_HEADER = (
    "// HeroAI Hex Removal Configuration\n"
    "//\n"
    "// Each hex has a removal priority for three target roles:\n"
    "//   caster         - Mesmer, Necromancer, Elementalist, Monk, Ritualist\n"
    "//   ranged_martial - Ranger, Paragon\n"
    "//   melee          - Warrior, Assassin, Dervish\n"
    "//\n"
    "// Priorities: NONE | LOW | MED | HIGH\n"
    "//   NONE = never remove on this role\n"
    "//   LOW  = remove if nothing better to do\n"
    "//   MED  = standard cleanup\n"
    "//   HIGH = urgent removal\n"
    "//\n"
    "// by_profession overrides the role priority for a specific\n"
    "// primary profession (e.g. \"Paragon\": \"HIGH\"). Empty {} = none.\n"
    "//\n"
    "// This config is per-character. Each character on the account\n"
    "// has its own folder under Settings/<email>/HeroAI/Hex removal/.\n"
    "// Edit via the GUI: HeroAI Control Panel -> Builds -> Hex Removal\n"
    "// -> Settings tab. Or hand-edit this file; changes take effect\n"
    "// when HeroAI reloads.\n"
    "\n"
)


def _serialize_jsonc(state: ConfigState) -> str:
    grouped: dict[int, list[str]] = {}
    unknown: list[str] = []
    known_prof_ids = set(_PROFESSION_BY_NAME.values())
    for name in state.hexes.keys():
        pid = _profession_for_hex(name)
        if pid in known_prof_ids:
            grouped.setdefault(pid, []).append(name)
        else:
            unknown.append(name)

    sections: list[tuple[str, list[str]]] = []
    for pid in _PROFESSION_ORDER:
        names = sorted(grouped.get(pid, []))
        if names:
            sections.append((_NAME_BY_PROFESSION_ID[pid], names))
    if unknown:
        sections.append(("Other / Unresolved", sorted(unknown)))

    total = sum(len(names) for _, names in sections)

    buf: list[str] = [_FILE_HEADER, "{\n"]
    buf.append(f'  "schema": "{SCHEMA_ID}",\n')
    buf.append('  "debug": {\n')
    buf.append(f'    "hex_removal": {str(state.debug_hex_removal).lower()},\n')
    buf.append(f'    "hex_removal_locks": {str(state.debug_hex_removal_locks).lower()}\n')
    buf.append('  },\n')
    buf.append('  "hexes": {\n')

    written = 0
    for section_idx, (section_name, names) in enumerate(sections):
        if section_idx > 0:
            buf.append('\n')
        buf.append(f'    // --- {section_name} ---\n')
        for name in names:
            written += 1
            hs = state.hexes[name]
            obj = _serialize_entry_object(hs.entry)
            sep = '' if written == total else ','
            buf.append(f'    "{name}": {obj}{sep}\n')

    buf.append('  }\n')
    buf.append('}\n')
    return ''.join(buf)


# ============================================================================
# Load logic - migration only (no auto-detect / propagation)
# ============================================================================

def _build_initial_state() -> ConfigState:
    state = ConfigState()
    for name, entry in _HEX_DEFAULTS.items():
        state.hexes[name] = HexEntryState(entry=entry)
    return state


def _normalize_loaded(parsed: ConfigState) -> tuple[ConfigState, bool]:
    """Apply migration only. Parsed entries are taken at face value."""
    dirty = False
    state = ConfigState(
        debug_hex_removal=parsed.debug_hex_removal,
        debug_hex_removal_locks=parsed.debug_hex_removal_locks,
    )

    for name, parsed_state in parsed.hexes.items():
        if name not in _HEX_DEFAULTS:
            _log(
                f"config: '{name}' is not in the default table - "
                f"kept in JSON, ignored at runtime"
            )
        state.hexes[name] = parsed_state

    for name, default_entry in _HEX_DEFAULTS.items():
        if name not in state.hexes:
            state.hexes[name] = HexEntryState(entry=default_entry)
            dirty = True

    return state, dirty


# ============================================================================
# Disk IO
# ============================================================================

def _load_from_disk(email: str, character_name: str) -> ConfigState:
    if not email or not character_name:
        return _build_initial_state()

    path = _path_for(email, character_name)
    if not os.path.exists(path):
        state = _build_initial_state()
        _save_to_disk(email, character_name, state)
        return state

    try:
        with open(path, "r", encoding="utf-8") as f:
            text = f.read()
    except Exception as exc:
        _log(f"config: read error '{path}' - {exc!r}")
        return _build_initial_state()

    parsed = _parse_file(text)
    if parsed is None:
        state = _build_initial_state()
        _save_to_disk(email, character_name, state)
        return state

    state, dirty = _normalize_loaded(parsed)
    if dirty:
        _save_to_disk(email, character_name, state)
    return state


def _save_to_disk(email: str, character_name: str, state: ConfigState) -> bool:
    if not email or not character_name:
        return False
    path = _path_for(email, character_name)
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        text = _serialize_jsonc(state)
        with open(path, "w", encoding="utf-8") as f:
            f.write(text)
        return True
    except Exception as exc:
        _log(f"config: write error '{path}' - {exc!r}")
        return False


def _save_active(state: ConfigState) -> bool:
    """Save state to the active (email, character_name) location."""
    email, char = _active_account_key()
    return _save_to_disk(email, char, state)


# ============================================================================
# Runtime debug-flag application
# ============================================================================

def _apply_debug_flags_to_runtime(state: ConfigState) -> None:
    try:
        from Py4GWCoreLib.GlobalCache import HexRemovalPriority as hp
        hp.HEX_REMOVAL_DEBUG = bool(state.debug_hex_removal)
    except Exception:
        pass
    try:
        from Py4GWCoreLib.GlobalCache.shared_memory_src import AllAccounts as wb
        from Py4GWCoreLib.enums_src.Whiteboard_enums import WhiteboardLockKind
        kind = int(WhiteboardLockKind.HEX_REMOVAL_TARGET)
        if hasattr(wb, "WHITEBOARD_DEBUG_KINDS"):
            wb.WHITEBOARD_DEBUG_KINDS[kind] = bool(state.debug_hex_removal_locks)
    except Exception:
        pass


def _invalidate_priority() -> None:
    try:
        from Py4GWCoreLib.GlobalCache import HexRemovalPriority as hp
        if hasattr(hp, "invalidate_hex_removal_priority"):
            hp.invalidate_hex_removal_priority()
        else:
            hp._HEX_REMOVAL_PRIORITY_BUILT = False
            hp.HEX_REMOVAL_PRIORITY.clear()
    except Exception:
        pass


# ============================================================================
# Public API
# ============================================================================

def _get_state() -> ConfigState:
    """Return cached ConfigState for the active character. Reloads when the
    active (email, character_name) pair changes (e.g. character switch)."""
    global _cache_key, _cache_state
    key = _active_account_key()
    if key != _cache_key or _cache_state is None:
        _cache_state = _load_from_disk(*key)
        _cache_key = key
        _apply_debug_flags_to_runtime(_cache_state)
    return _cache_state


def load_active_overrides() -> dict[str, HexRemovalEntry]:
    state = _get_state()
    return {name: hs.entry for name, hs in state.hexes.items()}


def has_override(name: str) -> bool:
    """Legacy stub. Modified-tracking removed; always returns False."""
    return False


def set_override(name: str, entry: HexRemovalEntry) -> None:
    """Save a hex's entry. Logging is performed by the GUI per change."""
    state = _get_state()
    state.hexes[name] = HexEntryState(entry=entry)
    _save_active(state)
    _invalidate_priority()


def clear_override(name: str) -> None:
    """Reset a hex to its current default. Logging by the GUI."""
    state = _get_state()
    if name not in _HEX_DEFAULTS:
        state.hexes.pop(name, None)
    else:
        state.hexes[name] = HexEntryState(entry=_HEX_DEFAULTS[name])
    _save_active(state)
    _invalidate_priority()


def hard_reset_all_to_none() -> None:
    """Set every default-table hex to NONE on every role with no overrides.

    Single batched save + single priority invalidation regardless of count.
    Irreversible - caller is responsible for confirming with the user.
    """
    state = _get_state()
    none_entry = HexRemovalEntry(
        caster=HexRemovalPriority.NONE,
        ranged_martial=HexRemovalPriority.NONE,
        melee=HexRemovalPriority.NONE,
        by_profession={},
    )
    for name in list(state.hexes.keys()):
        if name in _HEX_DEFAULTS:
            state.hexes[name] = HexEntryState(entry=none_entry)
    _save_active(state)
    _invalidate_priority()


def get_debug_flags() -> tuple[bool, bool]:
    state = _get_state()
    return state.debug_hex_removal, state.debug_hex_removal_locks


def set_debug_flags(hex_removal: bool, hex_removal_locks: bool) -> None:
    state = _get_state()
    state.debug_hex_removal = bool(hex_removal)
    state.debug_hex_removal_locks = bool(hex_removal_locks)
    _save_active(state)
    _apply_debug_flags_to_runtime(state)
    _log(
        f"debug toggles updated: hex_removal={hex_removal}, "
        f"hex_removal_locks={hex_removal_locks}"
    )


# ----- Import / Export -------------------------------------------------------

def export_to_desktop() -> tuple[bool, str]:
    state = _get_state()
    text = _serialize_jsonc(state)
    path = _desktop_path()
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(text)
        return True, path
    except Exception as exc:
        return False, str(exc)


def import_from_text(payload: str) -> tuple[bool, str, ConfigState | None]:
    if not payload or not payload.strip():
        return False, "Empty payload.", None
    parsed = _parse_file(payload)
    if parsed is None:
        return False, "Failed to parse payload (schema/JSON error).", None
    if not parsed.hexes:
        return False, "No hex entries found in payload.", None
    return True, f"OK - {len(parsed.hexes)} entries.", parsed


def commit_imported(parsed: ConfigState) -> bool:
    if parsed is None:
        return False
    state, _dirty = _normalize_loaded(parsed)
    global _cache_state, _cache_key
    _cache_state = state
    _cache_key = _active_account_key()
    if not _save_active(state):
        return False
    _apply_debug_flags_to_runtime(state)
    _invalidate_priority()
    return True
