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


def _build_default_hero_priority() -> List[int]:
    # Seed with current 8-man defaults, then append remaining heroes
    # in catalog order for deterministic fallback behavior.
    seeded: List[int] = list(DEFAULT_HERO_TEAMS.get("party_8", []))
    for hero_id, _ in _HERO_CATALOG:
        hid = int(hero_id)
        if hid <= 0:
            continue
        if hid not in seeded:
            seeded.append(hid)
    return seeded


DEFAULT_HERO_PRIORITY: List[int] = _build_default_hero_priority()


_HERO_OPTIONS = (
    [(0, "Empty")]
    + sorted(
        [(hero_id, hero_name) for hero_id, hero_name in _HERO_CATALOG if int(hero_id) > 0],
        key=lambda x: str(x[1]).lower(),
    )
)
_HERO_IDS = [hero_id for hero_id, _ in _HERO_OPTIONS]
_HERO_LABELS = [f"{name} ({hero_id})" for hero_id, name in _HERO_OPTIONS]
_HERO_ID_TO_INDEX = {hero_id: idx for idx, hero_id in enumerate(_HERO_IDS)}
_HERO_TEMPLATE_IDS = [hero_id for hero_id, _ in _HERO_OPTIONS if int(hero_id) > 0]
_HERO_ID_TO_NAME = {int(hero_id): str(name) for hero_id, name in _HERO_CATALOG}


def _normalize_hero_name(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", str(value or "").strip().lower())


_HERO_NAME_TO_ID: Dict[str, int] = {}
for _hero_id, _hero_name in _HERO_CATALOG:
    _key = _normalize_hero_name(_hero_name)
    if _key:
        _HERO_NAME_TO_ID[_key] = int(_hero_id)

# Keep compatibility with common naming variants/typos in recipe data.
_HERO_NAME_TO_ID.setdefault(_normalize_hero_name("Master of Whispers"), 4)
_HERO_NAME_TO_ID.setdefault(_normalize_hero_name("Margrid the Sly"), 12)
_HERO_NAME_TO_ID.setdefault(_normalize_hero_name("Magrid the Sly"), 12)


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


def _normalize_templates(raw: Dict[str, Any]) -> Dict[str, str]:
    templates: Dict[str, str] = {str(hero_id): "" for hero_id in _HERO_TEMPLATE_IDS}
    if not isinstance(raw, dict):
        return templates

    for hero_id in _HERO_TEMPLATE_IDS:
        key = str(hero_id)
        value = raw.get(key, "")
        if value is None:
            value = ""
        templates[key] = str(value)

    return templates


def _normalize_priority(raw: Any) -> List[int]:
    if isinstance(raw, list):
        values = raw
    else:
        values = []
    cleaned: List[int] = []
    valid_ids = {int(hero_id) for hero_id in _HERO_TEMPLATE_IDS}
    for value in values:
        try:
            hero_id = int(value)
        except (TypeError, ValueError):
            continue
        if hero_id <= 0 or hero_id not in valid_ids:
            continue
        if hero_id in cleaned:
            continue
        cleaned.append(hero_id)

    # Append any missing heroes to keep full ordered roster.
    for hero_id in DEFAULT_HERO_PRIORITY:
        if hero_id not in cleaned:
            cleaned.append(int(hero_id))

    return cleaned


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


def load_hero_templates() -> Dict[str, str]:
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
                    return _normalize_templates(raw.get("hero_templates", {}))
            except Exception:
                pass

    return _normalize_templates({})


def load_hero_priority() -> List[int]:
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
                    return _normalize_priority(raw.get("hero_priority", []))
            except Exception:
                pass

    return _normalize_priority(DEFAULT_HERO_PRIORITY)


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


def save_hero_templates(templates: Dict[str, str]) -> None:
    filepath = _config_path()
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    normalized = _normalize_templates(templates)

    config: Dict[str, Any] = {}
    if os.path.isfile(filepath):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                raw = json.load(f)
            if isinstance(raw, dict):
                config = raw
        except Exception:
            config = {}

    config["hero_templates"] = normalized
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=4)


def save_hero_priority(priority: List[int]) -> None:
    filepath = _config_path()
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    normalized = _normalize_priority(priority)

    config: Dict[str, Any] = {}
    if os.path.isfile(filepath):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                raw = json.load(f)
            if isinstance(raw, dict):
                config = raw
        except Exception:
            config = {}

    config["hero_priority"] = normalized
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


def get_hero_priority() -> List[int]:
    return _normalize_priority(load_hero_priority())


def get_team_by_priority(max_heroes: int, required_hero_ids: List[int] | None = None) -> List[int]:
    slots = max(0, int(max_heroes) - 1)
    if slots <= 0:
        return []

    priority = get_hero_priority()
    required = [int(h) for h in (required_hero_ids or []) if int(h) > 0]

    team: List[int] = []
    for hero_id in required:
        if hero_id not in team:
            team.append(hero_id)
    for hero_id in priority:
        if hero_id not in team:
            team.append(hero_id)

    return team[:slots]


def hero_id_from_name(hero_name: str) -> int | None:
    key = _normalize_hero_name(hero_name)
    if not key:
        return None
    hero_id = _HERO_NAME_TO_ID.get(key)
    return int(hero_id) if hero_id and int(hero_id) > 0 else None


def resolve_hero_ids(value: Any) -> List[int]:
    names: List[str]
    if value is None:
        names = []
    elif isinstance(value, str):
        names = [value]
    elif isinstance(value, list):
        names = [str(v) for v in value if isinstance(v, str) and str(v).strip()]
    else:
        names = []

    resolved: List[int] = []
    for name in names:
        hero_id = hero_id_from_name(name)
        if hero_id is None or hero_id in resolved:
            continue
        resolved.append(hero_id)
    return resolved


_ui_teams: Dict[str, List[int]] = {}
_ui_templates: Dict[str, str] = {}
_ui_priority: List[int] = []
_ui_loaded = False
_ui_status = ""
_ui_setup_visible_by_id: Dict[str, bool] = {}
_ui_active_section_by_id: Dict[str, str] = {}
_ui_priority_drag_from: int | None = None
_ui_priority_drag_to: int | None = None


def _ui_input_text(label: str, value: str, max_len: int = 256) -> str:
    try:
        # In this binding the 3rd arg is flags, not max_len.
        result = PyImGui.input_text(label, str(value), 0)
    except Exception:
        # Fallback for builds that expose only the 2-arg signature.
        result = PyImGui.input_text(label, str(value))
    if isinstance(result, tuple) and len(result) == 2:
        text = str(result[1])
    else:
        text = str(result)
    if int(max_len) > 0 and len(text) > int(max_len):
        text = text[: int(max_len)]
    return text


def _begin_child_compat(child_id: str, height: int = 290, border: bool = True) -> bool:
    """Open an ImGui child using whichever signature this PyImGui build exposes."""
    try:
        # Most modules in this repo use tuple-based size signature.
        h = int(height)
        if h <= 0:
            return bool(PyImGui.begin_child(child_id, (0, 0), bool(border), PyImGui.WindowFlags.NoFlag))
        return bool(PyImGui.begin_child(child_id, (0, h), bool(border), PyImGui.WindowFlags.NoFlag))
    except Exception:
        try:
            # Fallback for alternate binding variants.
            h = int(height)
            if h <= 0:
                return bool(PyImGui.begin_child(child_id, (0, 0), bool(border), PyImGui.WindowFlags.NoFlag))
            return bool(PyImGui.begin_child(child_id, 0, h, bool(border)))
        except Exception:
            return False


def _content_region_avail_compat() -> tuple[float, float]:
    try:
        avail = PyImGui.get_content_region_avail()
        if isinstance(avail, tuple) and len(avail) >= 2:
            return float(avail[0]), float(avail[1])
    except Exception:
        pass
    return (700.0, 360.0)


def draw_priority_tab() -> None:
    global _ui_teams, _ui_templates, _ui_priority, _ui_loaded, _ui_status
    global _ui_priority_drag_from, _ui_priority_drag_to

    if not _ui_loaded:
        _ui_teams = load_hero_teams()
        _ui_templates = load_hero_templates()
        _ui_priority = load_hero_priority()
        _ui_loaded = True

    PyImGui.text("Global Hero Priority (used by load_party dynamic picker)")
    PyImGui.text("Required heroes are added first, then this order fills remaining slots.")
    PyImGui.text("Drag a row and release over another row to reorder.")
    PyImGui.text(f"Priority entries loaded: {len(_ui_priority)}")

    _ui_priority = _normalize_priority(_ui_priority)
    if not _ui_priority:
        _ui_priority = _normalize_priority(DEFAULT_HERO_PRIORITY)

    if PyImGui.button("Save Priority"):
        save_hero_priority(_ui_priority)
        _ui_status = "Priority saved."
    PyImGui.same_line(0, 8)
    if PyImGui.button("Reload Priority"):
        _ui_priority = load_hero_priority()
        _ui_status = "Priority reloaded."
    PyImGui.same_line(0, 8)
    if PyImGui.button("Populate All Heroes"):
        _ui_priority = _normalize_priority(DEFAULT_HERO_PRIORITY)
        _ui_status = "Priority list populated with all heroes (not saved yet)."
    PyImGui.same_line(0, 8)
    if PyImGui.button("Reset Priority Defaults"):
        _ui_priority = _normalize_priority(DEFAULT_HERO_PRIORITY)
        _ui_status = "Priority reset to defaults (not saved yet)."

    avail_x, _avail_y = _content_region_avail_compat()
    child_height = 0  # Fill all remaining vertical space.
    row_width = float(max(120, avail_x - 120))

    if _begin_child_compat("hero_priority_list", height=child_height, border=True):
        for idx in range(len(_ui_priority)):
            hero_id = int(_ui_priority[idx])
            hero_name = _HERO_ID_TO_NAME.get(hero_id, f"Hero {hero_id}")
            is_drag_source = (_ui_priority_drag_from is not None and int(_ui_priority_drag_from) == idx)
            is_drop_target = (_ui_priority_drag_to is not None and int(_ui_priority_drag_to) == idx)
            prefix = ">> " if is_drag_source else "   "
            handle = "[::]"
            drop_marker = " <DROP>" if is_drop_target else ""
            row_label = f"{prefix}{handle} {idx + 1:02d}. {hero_name} ({hero_id}){drop_marker}##hero_priority_row_{idx}"
            if is_drop_target:
                try:
                    PyImGui.push_style_color(PyImGui.ImGuiCol.Header, (0.18, 0.40, 0.18, 0.95))
                    PyImGui.push_style_color(PyImGui.ImGuiCol.HeaderHovered, (0.22, 0.52, 0.22, 1.0))
                    PyImGui.push_style_color(PyImGui.ImGuiCol.HeaderActive, (0.16, 0.34, 0.16, 1.0))
                except Exception:
                    pass
            try:
                PyImGui.selectable(row_label, False, PyImGui.SelectableFlags.NoFlag, (row_width, 0))
            except Exception:
                PyImGui.selectable(row_label, False)
            if is_drop_target:
                try:
                    PyImGui.pop_style_color(3)
                except Exception:
                    pass

            try:
                if PyImGui.is_item_active() and PyImGui.is_mouse_dragging(0, 0.0):
                    _ui_priority_drag_from = idx
            except Exception:
                pass

            try:
                if PyImGui.is_item_hovered():
                    PyImGui.set_tooltip("Click and drag this row to reorder priority.")
            except Exception:
                pass

            try:
                if _ui_priority_drag_from is not None and PyImGui.is_item_hovered():
                    _ui_priority_drag_to = idx
            except Exception:
                pass

            PyImGui.same_line(0, 10)
            if PyImGui.button(f"Top##hero_priority_top_{idx}") and idx > 0:
                moved = _ui_priority.pop(idx)
                _ui_priority.insert(0, moved)
                _ui_priority_drag_from = None
                _ui_priority_drag_to = None
            PyImGui.same_line(0, 4)
            if PyImGui.button(f"Up##hero_priority_up_{idx}") and idx > 0:
                _ui_priority[idx - 1], _ui_priority[idx] = _ui_priority[idx], _ui_priority[idx - 1]
                # Keep drag indexes coherent after button reorder.
                _ui_priority_drag_from = None
                _ui_priority_drag_to = None
            PyImGui.same_line(0, 4)
            if PyImGui.button(f"Dn##hero_priority_dn_{idx}") and idx < (len(_ui_priority) - 1):
                _ui_priority[idx + 1], _ui_priority[idx] = _ui_priority[idx], _ui_priority[idx + 1]
                _ui_priority_drag_from = None
                _ui_priority_drag_to = None
            PyImGui.same_line(0, 4)
            if PyImGui.button(f"Bottom##hero_priority_bottom_{idx}") and idx < (len(_ui_priority) - 1):
                moved = _ui_priority.pop(idx)
                _ui_priority.append(moved)
                _ui_priority_drag_from = None
                _ui_priority_drag_to = None

        # Apply drag-drop reorder when mouse is released.
        try:
            mouse_down = bool(PyImGui.is_mouse_down(0))
        except Exception:
            mouse_down = False
        if (not mouse_down) and _ui_priority_drag_from is not None:
            src = int(_ui_priority_drag_from)
            dst = int(_ui_priority_drag_to) if _ui_priority_drag_to is not None else src
            if 0 <= src < len(_ui_priority) and 0 <= dst < len(_ui_priority) and src != dst:
                moved = _ui_priority.pop(src)
                if dst > src:
                    dst -= 1
                _ui_priority.insert(dst, moved)
                _ui_status = f"Moved {_HERO_ID_TO_NAME.get(int(moved), moved)} to position {dst + 1} (not saved yet)."
            _ui_priority_drag_from = None
            _ui_priority_drag_to = None
        PyImGui.end_child()


def draw_exact_tab() -> None:
    global _ui_teams, _ui_templates, _ui_priority, _ui_loaded, _ui_status

    if not _ui_loaded:
        _ui_teams = load_hero_teams()
        _ui_templates = load_hero_templates()
        _ui_priority = load_hero_priority()
        _ui_loaded = True

    PyImGui.text("Exact Team Setup")
    PyImGui.text("Set exact hero IDs for legacy team profiles. Use 0 to leave a slot empty.")

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
    if PyImGui.button("Save Exact Setup"):
        save_hero_teams(_ui_teams)
        _ui_status = "Exact setup saved."

    if PyImGui.button("Reload Exact Setup"):
        _ui_teams = load_hero_teams()
        _ui_status = "Exact setup reloaded."

    if PyImGui.button("Reset Exact Defaults"):
        _ui_teams = _normalize_teams(DEFAULT_HERO_TEAMS)
        _ui_status = "Exact setup reset to defaults (not saved yet)."

    if _ui_status:
        PyImGui.text(_ui_status)


def draw_setup_tab() -> None:
    """
    Backward-compatible composite view used by older widgets/tools.
    """
    draw_priority_tab()
    PyImGui.separator()
    draw_exact_tab()


def _draw_templates_tab(ui_id: str = "default") -> None:
    global _ui_templates
    if not _ui_templates:
        _ui_templates = load_hero_templates()

    PyImGui.text("Hero Templates")
    PyImGui.text("Set optional template code per hero. Leave empty to skip.")
    PyImGui.separator()

    row_color_a = (0.90, 0.90, 0.90, 1.0)
    row_color_b = (0.72, 0.86, 0.98, 1.0)
    for row_idx, hero_id in enumerate(_HERO_TEMPLATE_IDS):
        hero_name = _HERO_ID_TO_NAME.get(int(hero_id), f"Hero {hero_id}")
        key = str(hero_id)
        current_value = str(_ui_templates.get(key, ""))
        label_color = row_color_a if (row_idx % 2) == 0 else row_color_b
        PyImGui.text_colored(f"{hero_name} ({hero_id})", label_color)
        PyImGui.same_line(260, 8)
        _ui_templates[key] = _ui_input_text(f"##hero_template_{ui_id}_{hero_id}", current_value, 512)


def show_team_configuration_window(ui_id: str = "default") -> None:
    _ui_setup_visible_by_id[ui_id] = True


def toggle_team_configuration_window(ui_id: str = "default") -> bool:
    next_visible = not bool(_ui_setup_visible_by_id.get(ui_id, False))
    _ui_setup_visible_by_id[ui_id] = next_visible
    return next_visible


def is_team_configuration_window_visible(ui_id: str = "default") -> bool:
    return bool(_ui_setup_visible_by_id.get(ui_id, False))


def draw_team_configuration_window(
    ui_id: str = "default",
    title: str = "Team Configuration",
) -> None:
    global _ui_teams, _ui_templates, _ui_loaded, _ui_status
    if not is_team_configuration_window_visible(ui_id):
        return

    if not _ui_loaded:
        _ui_teams = load_hero_teams()
        _ui_templates = load_hero_templates()
        _ui_loaded = True

    PyImGui.set_next_window_size((760, 720), PyImGui.ImGuiCond.FirstUseEver)
    if not PyImGui.begin(f"{title}##team_config_window_{ui_id}"):
        PyImGui.end()
        return

    active_section = str(_ui_active_section_by_id.get(ui_id, "priority") or "priority").strip().lower()
    if active_section not in ("priority", "exact", "templates"):
        active_section = "priority"

    if PyImGui.button(f"Close##team_config_close_top_{ui_id}"):
        _ui_setup_visible_by_id[ui_id] = False
        PyImGui.end()
        return
    PyImGui.same_line(0, 12)
    if PyImGui.button(f"Priority##team_config_priority_{ui_id}"):
        active_section = "priority"
    PyImGui.same_line(0, 6)
    if PyImGui.button(f"Exact##team_config_exact_{ui_id}"):
        active_section = "exact"
    PyImGui.same_line(0, 6)
    if PyImGui.button(f"Templates##team_config_templates_{ui_id}"):
        active_section = "templates"
    _ui_active_section_by_id[ui_id] = active_section
    PyImGui.separator()

    if active_section == "priority":
        draw_priority_tab()
    elif active_section == "exact":
        draw_exact_tab()
    else:
        _draw_templates_tab(ui_id=ui_id)
        PyImGui.separator()
        if PyImGui.button(f"Save Templates##{ui_id}"):
            save_hero_templates(_ui_templates)
            _ui_status = "Templates saved."
        PyImGui.same_line(0, -1)
        if PyImGui.button(f"Reload Templates##{ui_id}"):
            _ui_templates = load_hero_templates()
            _ui_status = "Templates reloaded."
        PyImGui.same_line(0, -1)
        if PyImGui.button(f"Clear Templates##{ui_id}"):
            _ui_templates = _normalize_templates({})
            _ui_status = "Templates cleared (not saved yet)."
        if _ui_status:
            PyImGui.text(_ui_status)

    PyImGui.end()


def draw_configure_teams_section(
    ui_id: str = "default",
    button_label: str = "Configure Teams",
) -> None:
    """
    Reusable compact entry-point for team setup in any ModularBot app.
    Renders a toggle button and, when open, the standard team setup UI.
    """
    visible = bool(_ui_setup_visible_by_id.get(ui_id, False))
    if PyImGui.button(f"{button_label}##team_setup_btn_{ui_id}"):
        visible = not visible
        _ui_setup_visible_by_id[ui_id] = visible

    if visible:
        draw_team_configuration_window(ui_id=ui_id, title="Team Configuration")
