from Py4GWCoreLib import *
from . import state
from .handler import handler
from .settings_io import save_account_settings, save_global_settings

def draw_centered_checkbox(label: str, value: bool) -> bool:
    width = PyImGui.calc_text_size(label)[0] + 20
    center_x = (PyImGui.get_content_region_avail()[0] - width) * 0.5
    PyImGui.set_cursor_pos_x(PyImGui.get_cursor_pos_x() + center_x)
    return PyImGui.checkbox(label, value)

def draw_labeled_slider(label: str, id: str, value: int, min_val: int, max_val: int) -> int:
    x, y = PyImGui.get_cursor_pos()
    PyImGui.set_cursor_pos(x, y + 5)
    PyImGui.text(label)
    PyImGui.same_line(0, -1)
    PyImGui.set_cursor_pos(x + 160, y)
    PyImGui.set_next_item_width(PyImGui.get_content_region_avail()[0])
    return PyImGui.slider_int(id, value, min_val, max_val)

def draw_account_widget_config():
    PyImGui.text("Widget Settings")
    PyImGui.spacing()     
    save_label = "Save to Account Settings"
    save_width = PyImGui.calc_text_size(save_label)[0] + 20
    center = (PyImGui.get_content_region_avail()[0] - save_width) * 0.5
    PyImGui.set_cursor_pos_x(PyImGui.get_cursor_pos_x() + center)
    if PyImGui.button(save_label, save_width, 0):
        save_account_settings()
    PyImGui.same_line(0,-1)
    save_label = "Save to Global Settings"
    if PyImGui.button(save_label, save_width, 0):
        save_global_settings()
    
    widget_names = list(handler.widgets.keys())
    selected_index = widget_names.index(state.selected_widget) if state.selected_widget in widget_names else 0
    label = "Select Widget:"
    x, y = PyImGui.get_cursor_pos()
    PyImGui.set_cursor_pos(x, y + 5)
    PyImGui.text(label)
    PyImGui.same_line(0, -1)
    PyImGui.set_cursor_pos(x + 160, y)
    PyImGui.set_next_item_width(PyImGui.get_content_region_avail()[0])
    selected_index = PyImGui.combo("##selwidg", selected_index, widget_names)
    state.selected_widget = widget_names[selected_index]

    info = handler.widgets[state.selected_widget]
    data = handler.widget_data_cache.get(state.selected_widget, {})
    enabled = info.get("enabled", False)
    category = data.get("category", "Miscellaneous")
    subcategory = data.get("subcategory", "General")
    icon = data.get("icon", "ICON_CIRCLE")

    PyImGui.spacing()
    updated_enabled = PyImGui.checkbox("Enabled", enabled)
    if updated_enabled != enabled:
        info["enabled"] = updated_enabled
        handler._save_widget_state(state.selected_widget)

    PyImGui.spacing()
    label = "Widget Category:"
    x, y = PyImGui.get_cursor_pos()
    PyImGui.set_cursor_pos(x, y + 5)
    PyImGui.text(label)
    PyImGui.same_line(0, -1)
    PyImGui.set_cursor_pos(x + 160, y)
    PyImGui.set_next_item_width(PyImGui.get_content_region_avail()[0])
    new_category = PyImGui.input_text("##cat", category, 100)

    PyImGui.spacing()
    label = "Widget Subcategory:"
    x, y = PyImGui.get_cursor_pos()
    PyImGui.set_cursor_pos(x, y + 5)
    PyImGui.text(label)
    PyImGui.same_line(0, -1)
    PyImGui.set_cursor_pos(x + 160, y)
    PyImGui.set_next_item_width(PyImGui.get_content_region_avail()[0])
    new_sub = PyImGui.input_text("##subcat", subcategory, 100)

    PyImGui.spacing()
    icon_names = [name for name in dir(IconsFontAwesome5) if name.startswith("ICON_")]
    current_index = icon_names.index(icon) if icon in icon_names else 0
    label = "Widget Icon:"
    x, y = PyImGui.get_cursor_pos()
    PyImGui.set_cursor_pos(x, y + 5)
    PyImGui.text(label)
    PyImGui.same_line(0, -1)
    PyImGui.set_cursor_pos(x + 160, y)
    PyImGui.set_next_item_width(PyImGui.get_content_region_avail()[0])
    new_index = PyImGui.combo("##icon_combo", current_index, icon_names)
    icon_value = getattr(IconsFontAwesome5, icon_names[current_index], "?")
    x, y = PyImGui.get_cursor_pos()
    PyImGui.set_cursor_pos(x, y + 5)
    PyImGui.text("Widget Icon Preview:")
    PyImGui.same_line(0, -1)
    PyImGui.set_cursor_pos(x + 160, y)
    PyImGui.text(f"{icon_value}")
    
    if new_index != current_index:
        data["icon"] = icon_names[new_index]
        handler._save_widget_state(state.selected_widget)

    if new_category != category or new_sub != subcategory:
        data["category"] = new_category
        data["subcategory"] = new_sub
        handler._save_widget_state(state.selected_widget)
        
def reset_quick_dock():
    state.quick_dock_color[:] = [0.6, 0.8, 1.0, 1.0]
    state.buttons_per_row = 8
    state.quick_dock_width = 10
    state.quick_dock_height = 50        

def draw_quick_dock_config():
    #config options go here        
    PyImGui.text("Quick Dock Settings")
    PyImGui.spacing()
    
    label = "Quick Dock Enabled" if state.enable_quick_dock else "Quick Dock Disabled"
    state.enable_quick_dock = draw_centered_checkbox(label, state.enable_quick_dock)
    ImGui.show_tooltip("Enable or Disbale the Widget Dock on the edge of the screen")
    
    PyImGui.spacing()
    label = "Quick Dock Color:"
    x, y = PyImGui.get_cursor_pos()
    PyImGui.set_cursor_pos(x, y + 5)
    PyImGui.text(label)
    PyImGui.set_cursor_pos(x + 160, y)
    full_width = PyImGui.get_content_region_avail()[0]
    slider_width = full_width
    PyImGui.set_next_item_width(slider_width)
    new_color = PyImGui.color_edit4("##rcolor", (state.quick_dock_color[0], state.quick_dock_color[1], state.quick_dock_color[2], state.quick_dock_color[3]))
    if list(new_color) != state.quick_dock_color:
        state.quick_dock_color[:] = new_color
     
    PyImGui.spacing()
    state.quick_dock_width = draw_labeled_slider("Quick Dock Width:", "##rwidth", state.quick_dock_width, 4, 50)
    state.quick_dock_height = draw_labeled_slider("Quick Dock Height:", "##rheight", state.quick_dock_height, 20, 150)
    state.buttons_per_row = draw_labeled_slider("Buttons Per Row:", "##bpr", state.buttons_per_row, 1, 16)
    
    PyImGui.spacing()
    label = "Lock Quick Dock location" if state.quick_dock_unlocked else "Unlock Quick Dock location"
    state.quick_dock_unlocked = PyImGui.checkbox(label, state.quick_dock_unlocked)
    ImGui.show_tooltip("You can also Unlock and Lock it by Middle-Clicking the Quick Dock")
    
    PyImGui.spacing()
    label = "Reset Quick Dock Settings"
    width = PyImGui.calc_text_size(label)[0] + 20
    center_x = (PyImGui.get_content_region_avail()[0] - width) * 0.5
    PyImGui.set_cursor_pos_x(PyImGui.get_cursor_pos_x() + center_x)
    PyImGui.push_style_color(PyImGui.ImGuiCol.Button, (0.0, 0.2, 0.4, 1.0))
    PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonHovered, (0.2, 0.4, 0.6, 1.0))
    PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonActive, (0.1, 0.3, 0.5, 1.0))
    if PyImGui.button(label, width, 0):
        reset_quick_dock()
    PyImGui.pop_style_color(3)

    PyImGui.spacing()
    PyImGui.text("Per-Widget QuickDock Settings")
    PyImGui.spacing()

    if PyImGui.begin_child("QuickDockWidgetList", (0.0, 150.0), True, 0):
        for idx, (name, widget) in enumerate(handler.widgets.items()):
            data = handler.widget_data_cache.get(name, {})
            if data.get("hidden", False) and not state.show_hidden_widgets:
                continue
            dock_enabled = data.get("quickdock", False)
            icon_name = data.get("icon", "ICON_CIRCLE")
            icon_char = getattr(IconsFontAwesome5, icon_name, "?")

            PyImGui.text(f"{icon_char} {name}")
            PyImGui.same_line(300, -1)

            new_dock_enabled = PyImGui.checkbox(f"##dock_{idx}", dock_enabled)
            if new_dock_enabled != dock_enabled:
                data["quickdock"] = new_dock_enabled
                handler._save_widget_state(name)
        PyImGui.end_child()
