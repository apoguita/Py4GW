"""PyImGui controls for modular hero team setup."""
from __future__ import annotations

import PyImGui

from .hero_setup_model import (
    DEFAULT_HERO_PRIORITY,
    HERO_ID_TO_NAME,
    load_hero_priority,
    normalize_priority,
    save_hero_priority,
)


_ui_priority: list[int] = []
_ui_loaded = False
_ui_status = ""
_ui_setup_visible_by_id: dict[str, bool] = {}
_ui_priority_drag_from: int | None = None
_ui_priority_drag_to: int | None = None


def _ensure_loaded() -> None:
    global _ui_priority, _ui_loaded
    if _ui_loaded:
        return
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


def draw_setup_tab() -> None:
    draw_priority_tab()


def show_team_configuration_window(ui_id: str = "default") -> None:
    _ui_setup_visible_by_id[ui_id] = True


def toggle_team_configuration_window(ui_id: str = "default") -> bool:
    next_visible = not bool(_ui_setup_visible_by_id.get(ui_id, False))
    _ui_setup_visible_by_id[ui_id] = next_visible
    return next_visible


def is_team_configuration_window_visible(ui_id: str = "default") -> bool:
    return bool(_ui_setup_visible_by_id.get(ui_id, False))


def draw_team_configuration_window(ui_id: str = "default", title: str = "Team Configuration") -> None:
    if not is_team_configuration_window_visible(ui_id):
        return
    _ensure_loaded()

    PyImGui.set_next_window_size((760, 720), PyImGui.ImGuiCond.FirstUseEver)
    if not PyImGui.begin(f"{title}##team_config_window_{ui_id}"):
        PyImGui.end()
        return

    if PyImGui.button(f"Close##team_config_close_top_{ui_id}"):
        _ui_setup_visible_by_id[ui_id] = False
        PyImGui.end()
        return
    PyImGui.separator()
    draw_priority_tab()

    PyImGui.end()


def draw_configure_teams_section(ui_id: str = "default", button_label: str = "Configure Priority") -> None:
    visible = bool(_ui_setup_visible_by_id.get(ui_id, False))
    if PyImGui.button(f"{button_label}##team_setup_btn_{ui_id}"):
        visible = not visible
        _ui_setup_visible_by_id[ui_id] = visible
    if visible:
        draw_team_configuration_window(ui_id=ui_id, title="Team Configuration")
