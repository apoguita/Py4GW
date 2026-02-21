"""
Shared hero team setup for modular bot recipes and UIs.

Provides:
- Persistent team config (save/load JSON)
- Team lookup by party size
- Reusable Setup tab UI renderer
"""

from __future__ import annotations

import json
import os
import re
from typing import Any, Dict, List

import PyImGui
from Py4GWCoreLib import Player


TEAM_SLOT_COUNTS: Dict[str, int] = {
    "party_4": 3,
    "party_6": 5,
    "party_6_no_spirits_minions": 5,
    "party_8": 7,
}

TEAM_LABELS: Dict[str, str] = {
    "party_4": "4man (Player + 3 Heroes)",
    "party_6": "6man (Player + 5 Heroes)",
    "party_6_no_spirits_minions": "6man NO SPIRITS/MINIONS (Player + 5 Heroes)",
    "party_8": "8man (Player + 7 Heroes)",
}

DEFAULT_HERO_TEAMS: Dict[str, List[int]] = {
    "party_4": [24, 27, 21],
    "party_6": [24, 27, 21, 26, 25],
    "party_6_no_spirits_minions": [24, 27, 21, 4, 37],
    "party_8": [24, 27, 21, 26, 25, 4, 37],
}


_HERO_CATALOG = [
    (0, "Empty"),
    (1, "Norgu"),
    (2, "Goren"),
    (3, "Tahlkora"),
    (4, "Master Of Whispers"),
    (5, "Acolyte Jin"),
    (6, "Koss"),
    (7, "Dunkoro"),
    (8, "Acolyte Sousuke"),
    (9, "Melonni"),
    (10, "Zhed Shadowhoof"),
    (11, "General Morgahn"),
    (12, "Magrid The Sly"),
    (13, "Zenmai"),
    (14, "Olias"),
    (15, "Razah"),
    (16, "MOX"),
    (17, "Keiran Thackeray"),
    (18, "Jora"),
    (19, "Pyre Fierceshot"),
    (20, "Anton"),
    (21, "Livia"),
    (22, "Hayda"),
    (23, "Kahmu"),
    (24, "Gwen"),
    (25, "Xandra"),
    (26, "Vekk"),
    (27, "Ogden"),
    (28, "Mercenary Hero 1"),
    (29, "Mercenary Hero 2"),
    (30, "Mercenary Hero 3"),
    (31, "Mercenary Hero 4"),
    (32, "Mercenary Hero 5"),
    (33, "Mercenary Hero 6"),
    (34, "Mercenary Hero 7"),
    (35, "Mercenary Hero 8"),
    (36, "Miku"),
    (37, "Zei Ri"),
]


_HERO_OPTIONS = sorted(
    _HERO_CATALOG,
    key=lambda x: x[0],
)
_HERO_IDS = [hero_id for hero_id, _ in _HERO_OPTIONS]
_HERO_LABELS = [f"{name} ({hero_id})" for hero_id, name in _HERO_OPTIONS]
_HERO_ID_TO_INDEX = {hero_id: idx for idx, hero_id in enumerate(_HERO_IDS)}


def _config_path() -> str:
    base_dir = os.path.dirname(__file__)
    configs_dir = os.path.join(base_dir, "configs")
    os.makedirs(configs_dir, exist_ok=True)

    safe_account_dir = _get_safe_account_key()
    return os.path.join(configs_dir, f"{safe_account_dir}.json")


def _default_config_path() -> str:
    base_dir = os.path.dirname(__file__)
    configs_dir = os.path.join(base_dir, "configs")
    os.makedirs(configs_dir, exist_ok=True)
    return os.path.join(configs_dir, "default.json")


def _get_safe_account_key() -> str:
    try:
        account_email = str(Player.GetAccountEmail() or "").strip()
    except Exception:
        account_email = ""

    # Fallback when account email is not available yet (e.g., loading screens).
    if not account_email:
        account_email = "default"

    safe_account_dir = re.sub(r'[<>:"/\\|?*]+', "_", account_email).strip(" .")
    if not safe_account_dir:
        safe_account_dir = "default"
    return safe_account_dir


def _legacy_config_path_root() -> str:
    return os.path.join(os.path.dirname(__file__), "hero_teams.json")


def _legacy_config_path_account_folder() -> str:
    base_dir = os.path.dirname(__file__)
    try:
        account_email = str(Player.GetAccountEmail() or "").strip()
    except Exception:
        account_email = ""
    if not account_email:
        account_email = "default"
    safe_account_dir = re.sub(r'[<>:"/\\|?*]+', "_", account_email).strip(" .")
    if not safe_account_dir:
        safe_account_dir = "default"
    return os.path.join(base_dir, safe_account_dir, "hero_teams.json")


def _normalize_teams(raw: Dict[str, Any]) -> Dict[str, List[int]]:
    teams: Dict[str, List[int]] = {}
    for team_key, slot_count in TEAM_SLOT_COUNTS.items():
        values = raw.get(team_key, DEFAULT_HERO_TEAMS[team_key])
        if not isinstance(values, list):
            values = DEFAULT_HERO_TEAMS[team_key]

        cleaned: List[int] = []
        for value in values[:slot_count]:
            try:
                cleaned.append(int(value))
            except (TypeError, ValueError):
                cleaned.append(0)

        while len(cleaned) < slot_count:
            cleaned.append(0)

        teams[team_key] = cleaned

    return teams


def load_hero_teams() -> Dict[str, List[int]]:
    filepath = _config_path()
    candidate_paths = [filepath]

    default_path = _default_config_path()
    if os.path.normcase(filepath) != os.path.normcase(default_path):
        candidate_paths.append(default_path)

    for candidate in candidate_paths:
        if os.path.isfile(candidate):
            try:
                with open(candidate, "r", encoding="utf-8") as f:
                    raw = json.load(f)
                if isinstance(raw, dict):
                    # New format: account config with hero_teams payload
                    if isinstance(raw.get("hero_teams"), dict):
                        return _normalize_teams(raw["hero_teams"])
                    # Backward-compatible: file only contains hero teams dict
                    return _normalize_teams(raw)
            except Exception:
                pass

    for legacy_path in (_legacy_config_path_account_folder(), _legacy_config_path_root()):
        if os.path.isfile(legacy_path):
            try:
                with open(legacy_path, "r", encoding="utf-8") as f:
                    raw_legacy = json.load(f)
                if isinstance(raw_legacy, dict):
                    normalized = _normalize_teams(raw_legacy)
                    # Migrate legacy file layout to account config file on first successful read.
                    if not os.path.isfile(filepath):
                        try:
                            with open(filepath, "w", encoding="utf-8") as out_f:
                                json.dump({"hero_teams": normalized}, out_f, indent=4)
                        except Exception:
                            pass
                    return normalized
            except Exception:
                pass

    return _normalize_teams(DEFAULT_HERO_TEAMS)


def save_hero_teams(teams: Dict[str, List[int]]) -> None:
    filepath = _config_path()
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    normalized = _normalize_teams(teams)
    config: Dict[str, Any] = {}
    if os.path.isfile(filepath):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                raw = json.load(f)
            if isinstance(raw, dict):
                config = raw
        except Exception:
            config = {}

    config["hero_teams"] = normalized
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=4)


def get_team_for_size(max_heroes: int, team_key: str = "") -> List[int]:
    teams = load_hero_teams()

    if team_key in teams:
        return [hero_id for hero_id in teams[team_key] if hero_id > 0]

    if max_heroes == 4:
        key = "party_4"
    elif max_heroes == 6:
        key = "party_6"
    elif max_heroes == 8:
        key = "party_8"
    else:
        return []

    return [hero_id for hero_id in teams.get(key, []) if hero_id > 0]


_ui_teams: Dict[str, List[int]] = {}
_ui_loaded = False
_ui_status = ""


def draw_setup_tab() -> None:
    global _ui_teams, _ui_loaded, _ui_status

    if not _ui_loaded:
        _ui_teams = load_hero_teams()
        _ui_loaded = True

    PyImGui.text("Hero Team Setup")
    PyImGui.text("Set hero IDs for each team. Use 0 to leave a slot empty.")

    for team_key in ("party_4", "party_6", "party_6_no_spirits_minions", "party_8"):
        PyImGui.separator()
        PyImGui.text(TEAM_LABELS[team_key])

        slots = TEAM_SLOT_COUNTS[team_key]
        if team_key not in _ui_teams:
            _ui_teams[team_key] = list(DEFAULT_HERO_TEAMS[team_key])

        for idx in range(slots):
            label = f"Hero {idx + 1}##{team_key}_{idx}"
            hero_id = _ui_teams[team_key][idx] if idx < len(_ui_teams[team_key]) else 0
            selected_index = _HERO_ID_TO_INDEX.get(int(hero_id), 0)
            selected_index = PyImGui.combo(label, selected_index, _HERO_LABELS)
            selected_index = max(0, min(selected_index, len(_HERO_IDS) - 1))
            _ui_teams[team_key][idx] = int(_HERO_IDS[selected_index])

    PyImGui.separator()
    if PyImGui.button("Save Setup"):
        save_hero_teams(_ui_teams)
        _ui_status = "Saved."

    if PyImGui.button("Reload Saved Setup"):
        _ui_teams = load_hero_teams()
        _ui_status = "Reloaded."

    if PyImGui.button("Reset Defaults"):
        _ui_teams = _normalize_teams(DEFAULT_HERO_TEAMS)
        _ui_status = "Reset to defaults (not saved yet)."

    if _ui_status:
        PyImGui.text(_ui_status)
