import datetime
import sys

from Sources.oazix.CustomBehaviors.skills.monitoring.drop_tracker_ui_panels import (
    default_ui_colors,
    draw_runtime_controls_panel,
)

EXPECTED_RUNTIME_ERRORS = (TypeError, ValueError, RuntimeError, AttributeError, IndexError, KeyError, OSError)


def _runtime_module(viewer):
    try:
        return sys.modules.get(viewer.__class__.__module__)
    except EXPECTED_RUNTIME_ERRORS:
        return None


def _runtime_attr(viewer, name: str, default=None):
    module = _runtime_module(viewer)
    if module is not None and hasattr(module, name):
        return getattr(module, name)
    return default


def get_session_duration_text(viewer):
    if len(viewer.raw_drops) < 2:
        return "00:00"
    try:
        fmt = "%Y-%m-%d %H:%M:%S"
        first_row = viewer._parse_drop_row(viewer.raw_drops[0]) if viewer.raw_drops else None
        last_row = viewer._parse_drop_row(viewer.raw_drops[-1]) if viewer.raw_drops else None
        if first_row is None or last_row is None:
            return "--:--"
        first_ts = datetime.datetime.strptime(first_row.timestamp, fmt)
        last_ts = datetime.datetime.strptime(last_row.timestamp, fmt)
        total_seconds = max(0, int((last_ts - first_ts).total_seconds()))
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        return f"{minutes:02d}:{seconds:02d}"
    except EXPECTED_RUNTIME_ERRORS:
        return "--:--"


def ui_colors(viewer):
    palette = dict(default_ui_colors())
    theme_name = viewer._ensure_text(getattr(viewer, "ui_theme_name", "Midnight")).strip()
    palette.update(viewer._theme_presets().get(theme_name, {}))
    return palette


def theme_presets(_viewer):
    return {
        "Midnight": {},
        "High Contrast": {
            "accent": (0.52, 0.88, 1.0, 1.0),
            "muted": (0.79, 0.84, 0.92, 1.0),
            "panel_bg": (0.06, 0.08, 0.11, 0.96),
            "primary_btn": (0.08, 0.56, 0.96, 0.98),
            "primary_hover": (0.18, 0.66, 1.0, 1.0),
            "primary_active": (0.05, 0.48, 0.84, 1.0),
            "secondary_btn": (0.17, 0.21, 0.29, 0.98),
            "secondary_hover": (0.24, 0.30, 0.40, 1.0),
            "secondary_active": (0.14, 0.18, 0.25, 1.0),
            "success_btn": (0.10, 0.63, 0.36, 0.98),
            "success_hover": (0.15, 0.75, 0.43, 1.0),
            "success_active": (0.08, 0.52, 0.31, 1.0),
            "warn_btn": (0.72, 0.49, 0.14, 0.98),
            "warn_hover": (0.84, 0.58, 0.18, 1.0),
            "warn_active": (0.62, 0.42, 0.11, 1.0),
            "danger_btn": (0.70, 0.18, 0.18, 0.98),
            "danger_hover": (0.82, 0.24, 0.24, 1.0),
            "danger_active": (0.58, 0.14, 0.14, 1.0),
        },
    }


def theme_names(viewer):
    return list(viewer._theme_presets().keys())


def push_button_style(viewer, variant: str = "secondary"):
    pyimgui = _runtime_attr(viewer, "PyImGui")
    c = viewer._ui_colors()
    palette = {
        "primary": (c.get("primary_btn"), c.get("primary_hover"), c.get("primary_active")),
        "secondary": (c.get("secondary_btn"), c.get("secondary_hover"), c.get("secondary_active")),
        "success": (c.get("success_btn"), c.get("success_hover"), c.get("success_active")),
        "warn": (c.get("warn_btn"), c.get("warn_hover"), c.get("warn_active")),
        "danger": (c.get("danger_btn"), c.get("danger_hover"), c.get("danger_active")),
    }
    btn, hover, active = palette.get(variant, palette["secondary"])
    pyimgui.push_style_color(pyimgui.ImGuiCol.Button, btn)
    pyimgui.push_style_color(pyimgui.ImGuiCol.ButtonHovered, hover)
    pyimgui.push_style_color(pyimgui.ImGuiCol.ButtonActive, active)
    pyimgui.push_style_color(pyimgui.ImGuiCol.Text, c.get("text", (1.0, 1.0, 1.0, 1.0)))


def styled_button(viewer, label: str, variant: str = "secondary", width: float = 0.0, height: float = 0.0, tooltip: str = ""):
    pyimgui = _runtime_attr(viewer, "PyImGui")
    imgui = _runtime_attr(viewer, "ImGui")
    viewer._push_button_style(variant)
    pressed = pyimgui.button(label, width, height)
    pyimgui.pop_style_color(4)
    if tooltip and pyimgui.is_item_hovered():
        imgui.show_tooltip(tooltip)
    return pressed


def set_filter_rarity_label(viewer, rarity_label: str) -> None:
    label = viewer._ensure_text(rarity_label).strip() or "All"
    options = list(getattr(viewer, "filter_rarity_options", []) or [])
    if not options:
        viewer.filter_rarity_idx = 0
        return
    try:
        viewer.filter_rarity_idx = options.index(label)
    except ValueError:
        viewer.filter_rarity_idx = 0


def draw_inline_rarity_filter_buttons(viewer) -> None:
    pyimgui = _runtime_attr(viewer, "PyImGui")
    imgui = _runtime_attr(viewer, "ImGui")
    labels = ["All", "White", "Blue", "Purple", "Gold", "Green"]
    selected_idx = int(getattr(viewer, "filter_rarity_idx", 0) or 0)
    options = list(getattr(viewer, "filter_rarity_options", []) or [])
    for idx, label in enumerate(labels):
        if idx > 0:
            pyimgui.same_line(0.0, 6.0)
        option_idx = options.index(label) if label in options else 0
        is_selected = selected_idx == option_idx
        variant = "primary" if is_selected else "secondary"
        if viewer._styled_button(f"{label}##rarity_filter", variant, 58.0, 24.0):
            viewer._set_filter_rarity_label(label)
        if pyimgui.is_item_hovered():
            imgui.show_tooltip(f"Filter table to {label.lower()} items." if label != "All" else "Show all item rarities.")


def draw_section_header(viewer, title: str):
    pyimgui = _runtime_attr(viewer, "PyImGui")
    c = viewer._ui_colors()
    pyimgui.text_colored(title, c["accent"])
    pyimgui.separator()


def draw_status_chip(viewer, label: str, variant: str = "secondary", tooltip: str = ""):
    pyimgui = _runtime_attr(viewer, "PyImGui")
    imgui = _runtime_attr(viewer, "ImGui")
    chip_label = viewer._ensure_text(label).strip()
    if not chip_label:
        return
    viewer._push_button_style(variant)
    pyimgui.button(chip_label)
    pyimgui.pop_style_color(4)
    if tooltip and pyimgui.is_item_hovered():
        imgui.show_tooltip(tooltip)


def draw_runtime_controls(viewer):
    pyimgui = _runtime_attr(viewer, "PyImGui")
    draw_runtime_controls_panel(viewer, pyimgui)


def draw_runtime_controls_popout(viewer):
    pyimgui = _runtime_attr(viewer, "PyImGui")
    if not viewer.runtime_controls_popout:
        return
    if not viewer.runtime_popout_initialized:
        try:
            display_w, display_h = viewer._get_display_size()
            pop_w = min(760.0, max(560.0, display_w * 0.45))
            pop_h = min(680.0, max(460.0, display_h * 0.58))
            pop_x = max(20.0, (display_w - pop_w) * 0.5)
            pop_y = max(20.0, (display_h - pop_h) * 0.16)
            pyimgui.set_next_window_pos(pop_x, pop_y)
            pyimgui.set_next_window_size(pop_w, pop_h)
            pyimgui.set_next_window_focus()
        except EXPECTED_RUNTIME_ERRORS:
            pass
        viewer.runtime_popout_initialized = True
    if pyimgui.begin("Drop Tracker Runtime Controls"):
        pyimgui.text_colored("Advanced Runtime Controls", viewer._ui_colors()["accent"])
        pyimgui.same_line(0.0, 10.0)
        if viewer._styled_button("Close Popout", "secondary"):
            viewer.runtime_controls_popout = False
            viewer.runtime_config_dirty = True
        pyimgui.separator()
        viewer._draw_runtime_controls()
    pyimgui.end()
