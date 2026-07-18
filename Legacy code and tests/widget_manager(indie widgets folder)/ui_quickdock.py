from Py4GWCoreLib import UIManager, Overlay, PyImGui, ImGui, IconsFontAwesome5
from . import state
from .handler import handler
from .config_scope import use_account_settings

button_flags = (
    PyImGui.WindowFlags.NoTitleBar |
    PyImGui.WindowFlags.AlwaysAutoResize |
    PyImGui.WindowFlags.NoMove |
    PyImGui.WindowFlags.NoScrollbar
)

def quick_dock_menu():
    io = PyImGui.get_io()
    left, top = 0, 0
    right = io.display_size_x
    bottom = io.display_size_y
    
    mouse_x, mouse_y = Overlay().GetMouseCoords()
    if state.quick_dock_unlocked and PyImGui.is_mouse_dragging(0, -1.0) and state.quick_dock_hovering_button:
        edge_threshold = 30
        new_edge = None
        if mouse_y < top + edge_threshold:
            new_edge = "top"
        elif mouse_y > bottom - edge_threshold:
            new_edge = "bottom"
        elif mouse_x < left + edge_threshold:
            new_edge = "left"
        elif mouse_x > right - edge_threshold:
            new_edge = "right"

        if new_edge and new_edge != state.quick_dock_edge[0]:
            state.quick_dock_edge[0] = new_edge

            if new_edge != state.last_written_quick_dock_edge:
                handler._write_setting("QuickDock", "edge", new_edge, to_account=use_account_settings())
                state.last_written_quick_dock_edge = new_edge

    if state.quick_dock_edge[0] == "left":
        quick_dock_x = left - 10
        quick_dock_y = max(top + 5, min(bottom - state.quick_dock_height - 5, state.quick_dock_offset_y))
    elif state.quick_dock_edge[0] == "right":
        quick_dock_x = right - state.quick_dock_width - 10
        quick_dock_y = max(top + 5, min(bottom - state.quick_dock_height - 5, state.quick_dock_offset_y))
    elif state.quick_dock_edge[0] == "top":
        quick_dock_x = max(left + 5, min(right - state.quick_dock_width - 5, state.quick_dock_offset_y))
        quick_dock_y = top - 10
    elif state.quick_dock_edge[0] == "bottom":
        quick_dock_x = max(left + 5, min(right - state.quick_dock_width - 5, state.quick_dock_offset_y))
        quick_dock_y = bottom - 20
    else:
        quick_dock_x = right - state.quick_dock_width - 5
        quick_dock_y = state.quick_dock_offset_y

    if state.quick_dock_edge[0] in ("top", "bottom"):
        quick_dock_w = state.quick_dock_height
        quick_dock_h = state.quick_dock_width
    else:
        quick_dock_w = state.quick_dock_width
        quick_dock_h = state.quick_dock_height

    PyImGui.set_next_window_pos(quick_dock_x, quick_dock_y)
    PyImGui.set_next_window_size(quick_dock_w, quick_dock_h)

    PyImGui.push_style_color(PyImGui.ImGuiCol.Button, (state.quick_dock_color[0], state.quick_dock_color[1], state.quick_dock_color[2], state.quick_dock_color[3]))

    if PyImGui.begin("##quick_dock_toggle", PyImGui.WindowFlags.NoTitleBar | PyImGui.WindowFlags.NoResize | PyImGui.WindowFlags.NoScrollbar | PyImGui.WindowFlags.NoBackground):
        PyImGui.push_style_var(ImGui.ImGuiStyleVar.FrameRounding, 0)
        PyImGui.push_style_var(ImGui.ImGuiStyleVar.WindowRounding, 0)
        state.quick_dock_hovering_button = False
        if PyImGui.button("##toggle_ribbon", quick_dock_w, quick_dock_h):
            state.show_quick_dock_popup = not state.show_quick_dock_popup
        # PyImGui.show_tooltip("Middle Click to Lock" if state.quick_dock_unlocked else "Middle Click to Unlock")
        if PyImGui.is_item_hovered():
            ImGui.show_tooltip("Middle-click to Lock/Unlock")
            if PyImGui.is_mouse_clicked(2):
                state.quick_dock_unlocked = not state.quick_dock_unlocked
        state.quick_dock_hovering_button = PyImGui.is_item_active()
        
        if state.quick_dock_unlocked and PyImGui.is_item_active():
            if state.quick_dock_edge[0] in ("left", "right"):
                state.quick_dock_offset_y = max(top, min(bottom - state.quick_dock_height, mouse_y - state.quick_dock_height // 2))
            else:
                state.quick_dock_offset_y = max(left, min(right - state.quick_dock_width, mouse_x - state.quick_dock_width // 2))

            if state.quick_dock_offset_y != state.last_written_offset_y:
                handler._write_setting("QuickDock", "offset_y", str(state.quick_dock_offset_y), to_account=use_account_settings())
                state.last_written_offset_y = state.quick_dock_offset_y
        PyImGui.end()

        PyImGui.pop_style_color(1)
        PyImGui.pop_style_var(2)

    if state.show_quick_dock_popup:
        popup_w, popup_h = state.last_popup_size
        if state.quick_dock_edge[0] == "right":
            panel_x = quick_dock_x - popup_w + 12
            panel_y = max(top + 5, min(bottom - popup_h - 5, quick_dock_y))
        elif state.quick_dock_edge[0] == "left":
            panel_x = quick_dock_x + quick_dock_w + 12
            panel_y = max(top + 5, min(bottom - popup_h - 5, quick_dock_y))
        elif state.quick_dock_edge[0] == "top":
            panel_x = max(left + 5, min(right - popup_w - 5, quick_dock_x))
            panel_y = quick_dock_y + quick_dock_h + 12
        elif state.quick_dock_edge[0] == "bottom":
            panel_x = max(left + 5, min(right - popup_w - 5, quick_dock_x))
            panel_y = quick_dock_y - popup_h + 12
        else:
            panel_x = quick_dock_x + quick_dock_w
            panel_y = quick_dock_y

        PyImGui.set_next_window_pos(panel_x, panel_y)
        PyImGui.push_style_var(ImGui.ImGuiStyleVar.FramePadding, 0.0)
        PyImGui.push_style_var(ImGui.ImGuiStyleVar.ItemSpacing, 0.0)
        PyImGui.push_style_var(ImGui.ImGuiStyleVar.WindowPadding, 0.0)

        if PyImGui.begin("##quick_dock_expanded", button_flags):
            state.last_popup_size[0], state.last_popup_size[1] = PyImGui.get_window_size()

            current_id = id(handler.widget_data_cache)
            if current_id != state.last_quickdock_cache_id:
                state.cached_quickdock_widgets = []
                for name, data in handler.widget_data_cache.items():
                    if not data.get("quickdock", False):
                        continue

                    icon_name = data.get("icon", "ICON_CIRCLE")
                    icon = getattr(IconsFontAwesome5, icon_name, "?")
                    widget = handler.widgets.get(name)
                    if not widget:
                        continue

                    label = f"{icon}##dock_toggle_{name}"
                    state.cached_quickdock_widgets.append((name, label, widget))

                state.last_quickdock_cache_id = current_id

            color_enabled = (0.2, 0.6, 0.3, 1.0)
            color_disabled = (0.3, 0.3, 0.3, 1.0)
            dockable_widgets = state.cached_quickdock_widgets
            written_this_frame = set()
            button_size = (32, 32)
            for i, (name, label, widget) in enumerate(dockable_widgets):
                enabled = widget.get("enabled", False)
                color = color_enabled if enabled else color_disabled

                PyImGui.push_style_color(PyImGui.ImGuiCol.Button, color)
                
                if PyImGui.button(label, *button_size):
                    widget["enabled"] = not enabled
                    if name not in written_this_frame:
                        handler._write_setting(name, "enabled", str(widget["enabled"]), to_account=use_account_settings())
                        written_this_frame.add(name)

                if PyImGui.is_item_hovered():
                    PyImGui.begin_tooltip()
                    PyImGui.text(f"{name} [{'Enabled' if enabled else 'Disabled'}]")
                    PyImGui.end_tooltip()
                    if PyImGui.is_mouse_clicked(2):
                        widget["configuring"] = not widget.get("configuring", False)

                PyImGui.pop_style_color(1)

                if (i + 1) % state.buttons_per_row != 0:
                    PyImGui.same_line(0, 5)

        PyImGui.end()
        PyImGui.pop_style_var(3)
