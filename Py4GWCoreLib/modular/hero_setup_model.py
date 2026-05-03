"""Account-scoped hero team setup model for modular party loading."""
from __future__ import annotations

import json
import os
import re
from typing import Any

from Py4GWCoreLib import Player

from .paths import modular_settings_root


TEAM_KEY_ALIASES: dict[str, str] = {
    "party_4": "heroes_3",
    "party_6": "heroes_5",
    "party_6_no_spirits_minions": "heroes_5_minionless",
    "party_8": "heroes_7",
    "party_8_minionless": "heroes_7_minionless",
}

TEAM_SLOT_COUNTS: dict[str, int] = {
    "heroes_3": 3,
    "heroes_3_minionless": 3,
    "heroes_5": 5,
    "heroes_5_minionless": 5,
    "heroes_7": 7,
    "heroes_7_minionless": 7,
}

TEAM_LABELS: dict[str, str] = {
    "heroes_3": "3 Heroes",
    "heroes_3_minionless": "3 Heroes (minionless)",
    "heroes_5": "5 Heroes",
    "heroes_5_minionless": "5 Heroes (minionless)",
    "heroes_7": "7 Heroes",
    "heroes_7_minionless": "7 Heroes (minionless)",
}

DEFAULT_HERO_TEAMS: dict[str, list[int]] = {
    "heroes_3": [24, 27, 21],
    "heroes_3_minionless": [24, 27, 21],
    "heroes_5": [24, 27, 21, 26, 25],
    "heroes_5_minionless": [24, 27, 21, 4, 37],
    "heroes_7": [24, 27, 21, 26, 25, 4, 37],
    "heroes_7_minionless": [24, 27, 21, 4, 37, 3, 7],
}

HERO_CATALOG = [
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

HERO_OPTIONS = (
    [(0, "Empty")]
    + sorted(
        [(hero_id, hero_name) for hero_id, hero_name in HERO_CATALOG if int(hero_id) > 0],
        key=lambda x: str(x[1]).lower(),
    )
)
HERO_IDS = [hero_id for hero_id, _ in HERO_OPTIONS]
HERO_LABELS = [f"{name} ({hero_id})" for hero_id, name in HERO_OPTIONS]
HERO_ID_TO_INDEX = {hero_id: idx for idx, hero_id in enumerate(HERO_IDS)}
HERO_TEMPLATE_IDS = [hero_id for hero_id, _ in HERO_OPTIONS if int(hero_id) > 0]
HERO_ID_TO_NAME = {int(hero_id): str(name) for hero_id, name in HERO_CATALOG}


def _normalize_hero_name(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", str(value or "").strip().lower())


HERO_NAME_TO_ID: dict[str, int] = {}
for _hero_id, _hero_name in HERO_CATALOG:
    _key = _normalize_hero_name(_hero_name)
    if _key:
        HERO_NAME_TO_ID[_key] = int(_hero_id)

HERO_NAME_TO_ID.setdefault(_normalize_hero_name("Master of Whispers"), 4)
HERO_NAME_TO_ID.setdefault(_normalize_hero_name("Margrid the Sly"), 12)
HERO_NAME_TO_ID.setdefault(_normalize_hero_name("Magrid the Sly"), 12)


def _build_default_hero_priority() -> list[int]:
    seeded = list(DEFAULT_HERO_TEAMS["heroes_7"])
    for hero_id, _name in HERO_CATALOG:
        hid = int(hero_id)
        if hid > 0 and hid not in seeded:
            seeded.append(hid)
    return seeded


DEFAULT_HERO_PRIORITY = _build_default_hero_priority()


def safe_account_key() -> str:
    try:
        account_email = str(Player.GetAccountEmail() or "").strip()
    except Exception:
        account_email = ""
    if not account_email:
        account_email = "default"
    safe_key = re.sub(r'[<>:"/\\|?*]+', "_", account_email).strip(" .")
    return safe_key or "default"


def hero_config_path(account_key: str | None = None) -> str:
    configs_dir = os.path.join(modular_settings_root(), "configs")
    os.makedirs(configs_dir, exist_ok=True)
    return os.path.join(configs_dir, f"{account_key or safe_account_key()}.json")


def default_hero_config_path() -> str:
    return hero_config_path("default")


def normalize_team_key(team_key: str, *, minionless: bool = False) -> str:
    key = str(team_key or "").strip()
    key = TEAM_KEY_ALIASES.get(key, key)
    if minionless:
        if key == "heroes_3":
            return "heroes_3_minionless"
        if key == "heroes_5":
            return "heroes_5_minionless"
        if key == "heroes_7":
            return "heroes_7_minionless"
    return key


def team_key_for_party_size(max_party_size: int, *, minionless: bool = False) -> str:
    size = int(max_party_size or 0)
    if size >= 8:
        return "heroes_7_minionless" if minionless else "heroes_7"
    if size >= 6:
        return "heroes_5_minionless" if minionless else "heroes_5"
    return "heroes_3_minionless" if minionless else "heroes_3"


def max_party_size_for_team_key(team_key: str) -> int:
    key = normalize_team_key(team_key)
    slots = int(TEAM_SLOT_COUNTS.get(key, 5))
    return slots + 1


def normalize_teams(raw: dict[str, Any] | None) -> dict[str, list[int]]:
    source = raw if isinstance(raw, dict) else {}
    teams: dict[str, list[int]] = {}

    for alias, canonical in TEAM_KEY_ALIASES.items():
        if alias in source and canonical not in source:
            source[canonical] = source.get(alias)

    for team_key, slot_count in TEAM_SLOT_COUNTS.items():
        values = source.get(team_key, DEFAULT_HERO_TEAMS[team_key])
        if not isinstance(values, list):
            values = DEFAULT_HERO_TEAMS[team_key]
        cleaned: list[int] = []
        for value in values[:slot_count]:
            try:
                cleaned.append(int(value))
            except (TypeError, ValueError):
                cleaned.append(0)
        while len(cleaned) < slot_count:
            cleaned.append(0)
        teams[team_key] = cleaned
    return teams


def normalize_templates(raw: dict[str, Any] | None) -> dict[str, str]:
    templates = {str(hero_id): "" for hero_id in HERO_TEMPLATE_IDS}
    if not isinstance(raw, dict):
        return templates
    for hero_id in HERO_TEMPLATE_IDS:
        key = str(hero_id)
        value = raw.get(key, "")
        templates[key] = "" if value is None else str(value)
    return templates


def normalize_priority(raw: Any) -> list[int]:
    values = raw if isinstance(raw, list) else []
    cleaned: list[int] = []
    valid_ids = {int(hero_id) for hero_id in HERO_TEMPLATE_IDS}
    for value in values:
        try:
            hero_id = int(value)
        except (TypeError, ValueError):
            continue
        if hero_id <= 0 or hero_id not in valid_ids or hero_id in cleaned:
            continue
        cleaned.append(hero_id)
    for hero_id in DEFAULT_HERO_PRIORITY:
        if hero_id not in cleaned:
            cleaned.append(int(hero_id))
    return cleaned


def default_hero_config() -> dict[str, Any]:
    return {
        "version": 1,
        "teams": normalize_teams(DEFAULT_HERO_TEAMS),
        "templates": normalize_templates({}),
        "priority": normalize_priority(DEFAULT_HERO_PRIORITY),
    }


def normalize_hero_config(raw: dict[str, Any] | None) -> dict[str, Any]:
    source = raw if isinstance(raw, dict) else {}
    teams_source = source.get("teams", source.get("hero_teams", source))
    templates_source = source.get("templates", source.get("hero_templates", {}))
    priority_source = source.get("priority", source.get("hero_priority", []))
    return {
        "version": 1,
        "teams": normalize_teams(teams_source),
        "templates": normalize_templates(templates_source),
        "priority": normalize_priority(priority_source),
    }


def _load_hero_config_file(path: str) -> dict[str, Any] | None:
    try:
        with open(path, "r", encoding="utf-8") as handle:
            loaded = json.load(handle)
        return normalize_hero_config(loaded if isinstance(loaded, dict) else {})
    except Exception:
        return None


def _write_hero_config_file(path: str, config: dict[str, Any]) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    normalized = normalize_hero_config(config)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(normalized, handle, indent=2, sort_keys=True)
        handle.write("\n")


def load_hero_config() -> dict[str, Any]:
    path = hero_config_path()
    default_path = default_hero_config_path()

    config = _load_hero_config_file(path) if os.path.isfile(path) else None
    if config is not None:
        return config

    config = _load_hero_config_file(default_path) if os.path.isfile(default_path) else None
    if config is None:
        config = default_hero_config()

    _write_hero_config_file(path, config)
    return config


def save_hero_config(config: dict[str, Any]) -> None:
    _write_hero_config_file(hero_config_path(), config)


def load_hero_teams() -> dict[str, list[int]]:
    return normalize_teams(load_hero_config().get("teams", {}))


def save_hero_teams(teams: dict[str, list[int]]) -> None:
    config = load_hero_config()
    config["teams"] = normalize_teams(teams)
    save_hero_config(config)


def load_hero_templates() -> dict[str, str]:
    return normalize_templates(load_hero_config().get("templates", {}))


def save_hero_templates(templates: dict[str, str]) -> None:
    config = load_hero_config()
    config["templates"] = normalize_templates(templates)
    save_hero_config(config)


def load_hero_priority() -> list[int]:
    return normalize_priority(load_hero_config().get("priority", []))


def save_hero_priority(priority: list[int]) -> None:
    config = load_hero_config()
    config["priority"] = normalize_priority(priority)
    save_hero_config(config)


def get_team_for_size(max_heroes: int, team_key: str = "", *, minionless: bool = False) -> list[int]:
    key = normalize_team_key(team_key, minionless=minionless)
    if not key:
        key = team_key_for_party_size(int(max_heroes or 0), minionless=minionless)
    teams = load_hero_teams()
    return [hero_id for hero_id in teams.get(key, []) if int(hero_id) > 0]


def get_hero_priority() -> list[int]:
    return normalize_priority(load_hero_priority())


def get_team_by_priority(max_heroes: int, required_hero_ids: list[int] | None = None) -> list[int]:
    slots = max(0, int(max_heroes) - 1)
    if slots <= 0:
        return []
    required = [int(h) for h in (required_hero_ids or []) if int(h) > 0]
    team: list[int] = []
    for hero_id in required + get_hero_priority():
        if hero_id not in team:
            team.append(hero_id)
    return team[:slots]


def hero_id_from_name(hero_name: str) -> int | None:
    key = _normalize_hero_name(hero_name)
    if not key:
        return None
    hero_id = HERO_NAME_TO_ID.get(key)
    return int(hero_id) if hero_id and int(hero_id) > 0 else None


def resolve_hero_ids(value: Any) -> list[int]:
    if value is None:
        names: list[str] = []
    elif isinstance(value, str):
        names = [value]
    elif isinstance(value, list):
        names = [str(v) for v in value if isinstance(v, str) and str(v).strip()]
    else:
        names = []

    resolved: list[int] = []
    for name in names:
        hero_id = hero_id_from_name(name)
        if hero_id is not None and hero_id not in resolved:
            resolved.append(hero_id)
    return resolved
