"""PyImGui controls for modular hero team setup."""
from __future__ import annotations

import PyImGui

from .hero_setup_model import (
    DEFAULT_HERO_PRIORITY,
    DEFAULT_HERO_TEAMS,
    HERO_ID_TO_INDEX,
    HERO_ID_TO_NAME,
    HERO_IDS,
    HERO_LABELS,
    HERO_TEMPLATE_IDS,
    TEAM_LABELS,
    TEAM_SLOT_COUNTS,
    load_hero_priority,
    load_hero_teams,
    load_hero_templates,
    normalize_priority,
    normalize_teams,
    normalize_templates,
    save_hero_priority,
    save_hero_teams,
    save_hero_templates,
)


_ui_teams: dict[str, list[int]] = {}
_ui_templates: dict[str, str] = {}
_ui_priority: list[int] = []
_ui_loaded = False
_ui_status = ""
_ui_setup_visible_by_id: dict[str, bool] = {}
_ui_active_section_by_id: dict[str, str] = {}
_ui_priority_drag_from: int | None = None
_ui_priority_drag_to: int | None = None


def _ensure_loaded() -> None:
    global _ui_teams, _ui_templates, _ui_priority, _ui_loaded
    if _ui_loaded:
        return
    _ui_teams = load_hero_teams()
    _ui_templates = load_hero_templates()
    _ui_priority = load_hero_priority()
    _ui_loaded = True


def _ui_input_text(label: str, value: str, max_len: int = 256) -> str:
    try:
        result = PyImGui.input_text(label, str(value), 0)
    except Exception:
        result = PyImGui.input_text(label, str(value))
    text = str(result[1]) if isinstance(result, tuple) and len(result) == 2 else str(result)
    return text[: int(max_len)] if int(max_len) > 0 else text


def _begin_child(child_id: str, height: int = 290, border: bool = True) -> bool:
    try:
        h = int(height)
        size = (0, 0) if h <= 0 else (0, h)
        return bool(PyImGui.begin_child(child_id, size, bool(border), PyImGui.WindowFlags.NoFlag))
    except Exception:
        try:
            h = int(height)
            return bool(PyImGui.begin_child(child_id, 0, h, bool(border)))
        except Exception:
            return False


def _content_region_avail() -> tuple[float, float]:
    try:
        avail = PyImGui.get_content_region_avail()
        if isinstance(avail, tuple) and len(avail) >= 2:
            return float(avail[0]), float(avail[1])
    except Exception:
        pass
    return (700.0, 360.0)


def draw_priority_tab() -> None:
    global _ui_priority, _ui_status, _ui_priority_drag_from, _ui_priority_drag_to
    _ensure_loaded()

    PyImGui.text("Global Hero Priority")
    PyImGui.text("Required heroes are added first, then this order fills remaining slots.")
    PyImGui.text("Drag a row and release over another row to reorder.")
    PyImGui.text(f"Priority entries loaded: {len(_ui_priority)}")

    _ui_priority = normalize_priority(_ui_priority) or normalize_priority(DEFAULT_HERO_PRIORITY)
    if PyImGui.button("Save Priority"):
        save_hero_priority(_ui_priority)
        _ui_status = "Priority saved."
    PyImGui.same_line(0, 8)
    if PyImGui.button("Reload Priority"):
        _ui_priority = load_hero_priority()
        _ui_status = "Priority reloaded."
    PyImGui.same_line(0, 8)
    if PyImGui.button("Populate All Heroes"):
        _ui_priority = normalize_priority(DEFAULT_HERO_PRIORITY)
        _ui_status = "Priority list populated with all heroes (not saved yet)."
    PyImGui.same_line(0, 8)
    if PyImGui.button("Reset Priority Defaults"):
        _ui_priority = normalize_priority(DEFAULT_HERO_PRIORITY)
        _ui_status = "Priority reset to defaults (not saved yet)."

    avail_x, _avail_y = _content_region_avail()
    row_width = float(max(120, avail_x - 120))
    if _begin_child("hero_priority_list", height=0, border=True):
        for idx, hero_id in enumerate(list(_ui_priority)):
            hero_name = HERO_ID_TO_NAME.get(int(hero_id), f"Hero {hero_id}")
            is_source = _ui_priority_drag_from == idx
            is_target = _ui_priority_drag_to == idx
            prefix = ">> " if is_source else "   "
            marker = " <DROP>" if is_target else ""
            row_label = f"{prefix}[::] {idx + 1:02d}. {hero_name} ({hero_id}){marker}##hero_priority_row_{idx}"
            try:
                PyImGui.selectable(row_label, False, PyImGui.SelectableFlags.NoFlag, (row_width, 0))
            except Exception:
                PyImGui.selectable(row_label, False)
            try:
                if PyImGui.is_item_active() and PyImGui.is_mouse_dragging(0, 0.0):
                    _ui_priority_drag_from = idx
                if _ui_priority_drag_from is not None and PyImGui.is_item_hovered():
                    _ui_priority_drag_to = idx
            except Exception:
                pass

            PyImGui.same_line(0, 10)
            if PyImGui.button(f"Top##hero_priority_top_{idx}") and idx > 0:
                _ui_priority.insert(0, _ui_priority.pop(idx))
                _ui_priority_drag_from = _ui_priority_drag_to = None
            PyImGui.same_line(0, 4)
            if PyImGui.button(f"Up##hero_priority_up_{idx}") and idx > 0:
                _ui_priority[idx - 1], _ui_priority[idx] = _ui_priority[idx], _ui_priority[idx - 1]
                _ui_priority_drag_from = _ui_priority_drag_to = None
            PyImGui.same_line(0, 4)
            if PyImGui.button(f"Dn##hero_priority_dn_{idx}") and idx < len(_ui_priority) - 1:
                _ui_priority[idx + 1], _ui_priority[idx] = _ui_priority[idx], _ui_priority[idx + 1]
                _ui_priority_drag_from = _ui_priority_drag_to = None
            PyImGui.same_line(0, 4)
            if PyImGui.button(f"Bottom##hero_priority_bottom_{idx}") and idx < len(_ui_priority) - 1:
                _ui_priority.append(_ui_priority.pop(idx))
                _ui_priority_drag_from = _ui_priority_drag_to = None

        try:
            mouse_down = bool(PyImGui.is_mouse_down(0))
        except Exception:
            mouse_down = False
        if not mouse_down and _ui_priority_drag_from is not None:
            src = int(_ui_priority_drag_from)
            dst = int(_ui_priority_drag_to) if _ui_priority_drag_to is not None else src
            if 0 <= src < len(_ui_priority) and 0 <= dst < len(_ui_priority) and src != dst:
                moved = _ui_priority.pop(src)
                if dst > src:
                    dst -= 1
                _ui_priority.insert(dst, moved)
                _ui_status = f"Moved {HERO_ID_TO_NAME.get(int(moved), moved)} to position {dst + 1}."
            _ui_priority_drag_from = _ui_priority_drag_to = None
        PyImGui.end_child()


def draw_exact_tab() -> None:
    global _ui_teams, _ui_status
    _ensure_loaded()
    PyImGui.text("Exact Team Setup")
    PyImGui.text("Set exact hero IDs for static team profiles. Use 0 to leave a slot empty.")

    for team_key in TEAM_SLOT_COUNTS:
        PyImGui.separator()
        PyImGui.text(TEAM_LABELS[team_key])
        _ui_teams.setdefault(team_key, list(DEFAULT_HERO_TEAMS[team_key]))
        slots = TEAM_SLOT_COUNTS[team_key]
        while len(_ui_teams[team_key]) < slots:
            _ui_teams[team_key].append(0)
        for idx in range(slots):
            selected = HERO_ID_TO_INDEX.get(int(_ui_teams[team_key][idx]), 0)
            selected = PyImGui.combo(f"Hero {idx + 1}##{team_key}_{idx}", selected, HERO_LABELS)
            selected = max(0, min(selected, len(HERO_IDS) - 1))
            _ui_teams[team_key][idx] = int(HERO_IDS[selected])

    PyImGui.separator()
    if PyImGui.button("Save Exact Setup"):
        save_hero_teams(_ui_teams)
        _ui_status = "Exact setup saved."
    if PyImGui.button("Reload Exact Setup"):
        _ui_teams = load_hero_teams()
        _ui_status = "Exact setup reloaded."
    if PyImGui.button("Reset Exact Defaults"):
        _ui_teams = normalize_teams(DEFAULT_HERO_TEAMS)
        _ui_status = "Exact setup reset to defaults (not saved yet)."
    if _ui_status:
        PyImGui.text(_ui_status)


def _draw_templates_tab(ui_id: str = "default") -> None:
    global _ui_templates
    _ensure_loaded()
    PyImGui.text("Hero Templates")
    PyImGui.text("Set optional template code per hero. Leave empty to skip.")
    PyImGui.separator()
    for row_idx, hero_id in enumerate(HERO_TEMPLATE_IDS):
        color = (0.90, 0.90, 0.90, 1.0) if (row_idx % 2) == 0 else (0.72, 0.86, 0.98, 1.0)
        hero_name = HERO_ID_TO_NAME.get(int(hero_id), f"Hero {hero_id}")
        key = str(hero_id)
        PyImGui.text_colored(f"{hero_name} ({hero_id})", color)
        PyImGui.same_line(260, 8)
        _ui_templates[key] = _ui_input_text(f"##hero_template_{ui_id}_{hero_id}", _ui_templates.get(key, ""), 512)


def draw_setup_tab() -> None:
    draw_priority_tab()
    PyImGui.separator()
    draw_exact_tab()


def show_team_configuration_window(ui_id: str = "default") -> None:
    _ui_setup_visible_by_id[ui_id] = True


def toggle_team_configuration_window(ui_id: str = "default") -> bool:
    next_visible = not bool(_ui_setup_visible_by_id.get(ui_id, False))
    _ui_setup_visible_by_id[ui_id] = next_visible
    return next_visible


def is_team_configuration_window_visible(ui_id: str = "default") -> bool:
    return bool(_ui_setup_visible_by_id.get(ui_id, False))


def draw_team_configuration_window(ui_id: str = "default", title: str = "Team Configuration") -> None:
    global _ui_templates, _ui_status
    if not is_team_configuration_window_visible(ui_id):
        return
    _ensure_loaded()

    PyImGui.set_next_window_size((760, 720), PyImGui.ImGuiCond.FirstUseEver)
    if not PyImGui.begin(f"{title}##team_config_window_{ui_id}"):
        PyImGui.end()
        return

    active = str(_ui_active_section_by_id.get(ui_id, "priority") or "priority").strip().lower()
    if active not in ("priority", "exact", "templates"):
        active = "priority"

    if PyImGui.button(f"Close##team_config_close_top_{ui_id}"):
        _ui_setup_visible_by_id[ui_id] = False
        PyImGui.end()
        return
    PyImGui.same_line(0, 12)
    if PyImGui.button(f"Priority##team_config_priority_{ui_id}"):
        active = "priority"
    PyImGui.same_line(0, 6)
    if PyImGui.button(f"Exact##team_config_exact_{ui_id}"):
        active = "exact"
    PyImGui.same_line(0, 6)
    if PyImGui.button(f"Templates##team_config_templates_{ui_id}"):
        active = "templates"
    _ui_active_section_by_id[ui_id] = active
    PyImGui.separator()

    if active == "priority":
        draw_priority_tab()
    elif active == "exact":
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
            _ui_templates = normalize_templates({})
            _ui_status = "Templates cleared (not saved yet)."
        if _ui_status:
            PyImGui.text(_ui_status)

    PyImGui.end()


def draw_configure_teams_section(ui_id: str = "default", button_label: str = "Configure Teams") -> None:
    visible = bool(_ui_setup_visible_by_id.get(ui_id, False))
    if PyImGui.button(f"{button_label}##team_setup_btn_{ui_id}"):
        visible = not visible
        _ui_setup_visible_by_id[ui_id] = visible
    if visible:
        draw_team_configuration_window(ui_id=ui_id, title="Team Configuration")
