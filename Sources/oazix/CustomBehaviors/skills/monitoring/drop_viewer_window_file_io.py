import os
import shutil
import sys

from Py4GWCoreLib.Item import Item
from Py4GWCoreLib.ItemArray import ItemArray
from Sources.oazix.CustomBehaviors.skills.monitoring.drop_tracker_log_store import parse_drop_log_file
from Sources.oazix.CustomBehaviors.skills.monitoring.drop_tracker_runtime_store import merge_parsed_rows_into_state

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


def mouse_in_current_window_rect(viewer):
    pyimgui = _runtime_attr(viewer, "PyImGui")
    try:
        io = pyimgui.get_io()
        mx = float(getattr(io, "mouse_pos_x", -1.0))
        my = float(getattr(io, "mouse_pos_y", -1.0))
        wx, wy = pyimgui.get_window_pos()
        ww, wh = pyimgui.get_window_size()
        return (mx >= wx) and (mx <= (wx + ww)) and (my >= wy) and (my <= (wy + wh))
    except EXPECTED_RUNTIME_ERRORS:
        return False


def get_display_size(viewer):
    pyimgui = _runtime_attr(viewer, "PyImGui")
    io = pyimgui.get_io()
    w = float(getattr(io, "display_size_x", 1920.0) or 1920.0)
    h = float(getattr(io, "display_size_y", 1080.0) or 1080.0)
    return max(320.0, w), max(240.0, h)


def clamp_pos(viewer, x, y, w, h, margin=4.0):
    display_w, display_h = viewer._get_display_size()
    x = max(float(margin), min(float(x), max(float(margin), display_w - float(w) - float(margin))))
    y = max(float(margin), min(float(y), max(float(margin), display_h - float(h) - float(margin))))
    return x, y


def clamp_size(viewer, w, h, min_w=420.0, min_h=280.0, margin=20.0):
    display_w, display_h = viewer._get_display_size()
    width = max(float(min_w), min(float(w), max(float(min_w), display_w - float(margin))))
    height = max(float(min_h), min(float(h), max(float(min_h), display_h - float(margin))))
    return width, height


def _resolve_hover_icon_path(viewer):
    icon_path = viewer._ensure_text(getattr(viewer, "hover_icon_path", "")).strip()
    if icon_path and os.path.exists(icon_path):
        return icon_path
    path_locator = _runtime_attr(viewer, "PathLocator")
    if path_locator is not None:
        try:
            fallback_path = path_locator.get_custom_behaviors_root_directory() + "\\gui\\textures\\Loot.png"
            if os.path.exists(fallback_path):
                return fallback_path
            return path_locator.get_texture_fallback()
        except EXPECTED_RUNTIME_ERRORS:
            pass
    return ""


def _mouse_in_rect(viewer, rect):
    pyimgui = _runtime_attr(viewer, "PyImGui")
    try:
        io = pyimgui.get_io()
        mx = float(getattr(io, "mouse_pos_x", -1.0))
        my = float(getattr(io, "mouse_pos_y", -1.0))
        rx, ry, rw, rh = rect
        return (mx >= rx) and (mx <= (rx + rw)) and (my >= ry) and (my <= (ry + rh))
    except EXPECTED_RUNTIME_ERRORS:
        return False


def _draw_themed_hover_button(viewer, button_rect):
    pyimgui = _runtime_attr(viewer, "PyImGui")
    imgui = _runtime_attr(viewer, "ImGui")
    style_api = _runtime_attr(viewer, "Style")
    theme_textures = _runtime_attr(viewer, "ThemeTextures")
    utils_api = _runtime_attr(viewer, "Utils")
    hovered = imgui.is_mouse_in_rect(button_rect)
    try:
        if style_api is not None and theme_textures is not None and getattr(imgui.get_style(), "Theme", None) == style_api.StyleTheme.Guild_Wars:
            theme_textures.Button_Background.value.get_texture().draw_in_drawlist(
                button_rect[:2],
                button_rect[2:],
                tint=(255, 255, 255, 255) if hovered else (200, 200, 200, 255),
            )
            theme_textures.Button_Frame.value.get_texture().draw_in_drawlist(
                button_rect[:2],
                button_rect[2:],
                tint=(255, 255, 255, 255) if hovered else (200, 200, 200, 255),
            )
            return
    except EXPECTED_RUNTIME_ERRORS:
        pass
    if utils_api is None:
        return
    try:
        pyimgui.draw_list_add_rect_filled(
            button_rect[0] + 1,
            button_rect[1] + 1,
            button_rect[0] + button_rect[2] - 1,
            button_rect[1] + button_rect[3] - 1,
            utils_api.RGBToColor(51, 76, 102, 255) if hovered else utils_api.RGBToColor(26, 38, 51, 255),
            4,
            0,
        )
        pyimgui.draw_list_add_rect(
            button_rect[0] + 1,
            button_rect[1] + 1,
            button_rect[0] + button_rect[2] - 1,
            button_rect[1] + button_rect[3] - 1,
            utils_api.RGBToColor(204, 204, 212, 50),
            4,
            0,
            1,
        )
    except EXPECTED_RUNTIME_ERRORS:
        return


def draw_hover_handle(viewer):
    pyimgui = _runtime_attr(viewer, "PyImGui")
    imgui = _runtime_attr(viewer, "ImGui")
    utils_api = _runtime_attr(viewer, "Utils")
    icon_path = _resolve_hover_icon_path(viewer)
    display_w, _display_h = viewer._get_display_size()
    btn_w = 48.0 if icon_path else 120.0
    btn_h = 48.0 if icon_path else 30.0
    win_w = btn_w + 4.0 if icon_path else btn_w
    win_h = btn_h + 4.0 if icon_path else btn_h
    default_x = max(8.0, (display_w * 0.5) - (btn_w * 0.5)) if icon_path else 30.0
    default_y = 4.0 if icon_path else 30.0
    x, y = viewer.saved_hover_handle_pos if viewer.saved_hover_handle_pos is not None else (default_x, default_y)
    x, y = viewer._clamp_pos(x, y, btn_w, btn_h)
    viewer.saved_hover_handle_pos = (x, y)
    button_rect = (x, y, btn_w, btn_h)
    pyimgui.set_next_window_pos(x, y)
    pyimgui.set_next_window_size(win_w, win_h)
    pyimgui.push_style_var2(imgui.ImGuiStyleVar.WindowPadding, 0.0, 0.0)
    flags = (
        pyimgui.WindowFlags.NoTitleBar
        | pyimgui.WindowFlags.NoResize
        | pyimgui.WindowFlags.NoMove
        | pyimgui.WindowFlags.NoScrollbar
        | pyimgui.WindowFlags.NoScrollWithMouse
        | pyimgui.WindowFlags.NoCollapse
        | pyimgui.WindowFlags.NoBackground
    )
    hovered = False
    if pyimgui.begin("Drop Tracker##HoverHandle", flags):
        if icon_path:
            _draw_themed_hover_button(viewer, button_rect)
            if utils_api is not None:
                frame_col = (
                    utils_api.RGBToColor(76, 235, 89, 255)
                    if viewer.hover_pin_open
                    else utils_api.RGBToColor(242, 71, 56, 255)
                )
                pyimgui.draw_list_add_rect(
                    button_rect[0] + 1,
                    button_rect[1] + 1,
                    button_rect[0] + button_rect[2] - 1,
                    button_rect[1] + button_rect[3] - 1,
                    frame_col,
                    4,
                    0,
                    3,
                )
            icon_rect = (button_rect[0] + 8.0, button_rect[1] + 8.0, 32.0, 32.0)
            imgui.DrawTextureInDrawList(
                icon_rect[:2],
                icon_rect[2:],
                icon_path,
                tint=(255, 255, 255, 255) if imgui.is_mouse_in_rect(button_rect) else (210, 210, 210, 255),
            )
            clicked = pyimgui.invisible_button("##DropTrackerHoverHandleBtn", btn_w, btn_h)
            if not clicked and pyimgui.is_item_active():
                delta = pyimgui.get_mouse_drag_delta(0, 0.0)
                pyimgui.reset_mouse_drag_delta(0)
                nx, ny = viewer._clamp_pos(x + float(delta[0]), y + float(delta[1]), btn_w, btn_h)
                viewer.saved_hover_handle_pos = (nx, ny)
                viewer.runtime_config_dirty = True
        else:
            clicked = viewer._styled_button("Drop Tracker", "primary", btn_w, btn_h)
        if clicked:
            viewer.hover_pin_open = not viewer.hover_pin_open
            viewer.hover_is_visible = True
            viewer.runtime_config_dirty = True
        if pyimgui.is_item_hovered():
            tip = "Drop Tracker (click to pin open)" if not viewer.hover_pin_open else "Drop Tracker (click to unpin)"
            imgui.show_tooltip(tip)
        hovered = imgui.is_mouse_in_rect(button_rect)
    pyimgui.end()
    pyimgui.pop_style_var(1)
    if viewer.saved_hover_handle_pos is not None:
        viewer._persist_layout_value("drop_viewer_handle_pos", viewer.saved_hover_handle_pos)
    return hovered


def save_run(viewer):
    if not os.path.exists(viewer.saved_logs_dir):
        os.makedirs(viewer.saved_logs_dir)
    target = os.path.join(viewer.saved_logs_dir, f"{viewer.save_filename}.csv")
    try:
        shutil.copy2(viewer.log_path, target)
        viewer.set_status(f"Saved to {viewer.save_filename}.csv")
        viewer.show_save_popup = False
    except EXPECTED_RUNTIME_ERRORS as e:
        viewer.set_status(f"Save failed: {e}")


def load_run(viewer, filename):
    filepath = os.path.join(viewer.saved_logs_dir, filename)
    try:
        viewer._parse_log_file(filepath)
        viewer.set_status(f"Loaded {filename}")
    except EXPECTED_RUNTIME_ERRORS as e:
        viewer.set_status(f"Load failed: {e}")


def merge_run(viewer, filename):
    map_api = _runtime_attr(viewer, "Map")
    filepath = os.path.join(viewer.saved_logs_dir, filename)
    try:
        parsed_rows = parse_drop_log_file(filepath, map_name_resolver=map_api.GetMapName)
        merge_parsed_rows_into_state(
            parsed_rows=parsed_rows,
            raw_drops=viewer.raw_drops,
            aggregated_drops=viewer.aggregated_drops,
            ensure_text_fn=viewer._ensure_text,
            canonical_name_fn=viewer._canonical_agg_item_name,
        )
        viewer.total_drops = len(viewer.raw_drops)
        viewer.set_status(f"Merged {filename}")
    except EXPECTED_RUNTIME_ERRORS as e:
        viewer.set_status(f"Merge failed: {e}")


def get_inventory_snapshot(viewer):
    snapshot = {}
    try:
        bags = ItemArray.CreateBagList(1, 2, 3, 4, 5, 6, 7, 8, 9, 10)
        items = ItemArray.GetItemArray(bags)
    except EXPECTED_RUNTIME_ERRORS:
        items = []
    for item_id in list(items or []):
        try:
            name = viewer._ensure_text(Item.GetName(item_id))
        except EXPECTED_RUNTIME_ERRORS:
            name = ""
        if not name:
            try:
                Item.RequestName(item_id)
            except EXPECTED_RUNTIME_ERRORS:
                pass
            continue
        clean_name = viewer._clean_item_name(name)
        if not clean_name:
            continue
        try:
            rarity = viewer._ensure_text(Item.Rarity.GetRarity(item_id)[1]).strip() or "Unknown"
        except EXPECTED_RUNTIME_ERRORS:
            rarity = "Unknown"
        try:
            quantity = max(1, int(Item.Properties.GetQuantity(item_id)))
        except EXPECTED_RUNTIME_ERRORS:
            quantity = 1
        snapshot[int(item_id)] = {
            "name": clean_name,
            "rarity": rarity,
            "quantity": quantity,
        }
    return snapshot
