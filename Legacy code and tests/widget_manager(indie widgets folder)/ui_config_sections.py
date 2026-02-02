from Py4GWCoreLib import PyImGui, ImGui, IconsFontAwesome5
from . import state
from .handler import handler
from .config_scope import use_account_settings, character_select
from .settings_io import load_account_settings, load_global_settings, save_all_settings, restore_global_defaults

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

def draw_floating_menu_config():
    char_select = character_select
    if char_select:
        PyImGui.spacing()
        PyImGui.text("Floating Widget Menu Settings available in game")
        PyImGui.spacing()
        PyImGui.separator()
    else:
        PyImGui.spacing()
        PyImGui.text("Floating Widget Menu Settings")
        PyImGui.spacing()
        PyImGui.separator()
        PyImGui.spacing()
        lock_text = "Lock Floating Button"
        new_locked = draw_centered_checkbox(lock_text, state.floating_drag_locked)
        if new_locked != state.floating_drag_locked:
            state.floating_drag_locked = new_locked
            handler._write_setting("FloatingMenu", "floating_drag_locked", str(new_locked))
        ImGui.show_tooltip("Prevents the floating button from being dragged")        
        PyImGui.spacing()
        PyImGui.separator()
        PyImGui.spacing()
        label = "Use Custom Floating Button Colors"
        prev_enabled = draw_centered_checkbox(label, state.floating_custom_colors_enabled)
        ImGui.show_tooltip("Overrides default floating button colors with custom values")
        if prev_enabled != state.floating_custom_colors_enabled:
            state.floating_custom_colors_enabled = prev_enabled
            handler._write_setting("FloatingMenu", "use_custom_colors", str(state.floating_custom_colors_enabled), to_account=use_account_settings())
        
        if state.floating_custom_colors_enabled:
            for label, key in [("Base", "base"), ("Hover", "hover"), ("Active", "active"), ("Border", "border")]:
                PyImGui.spacing()
                PyImGui.text(f"{label} Color")
                PyImGui.same_line(150, -1)
                new_col = PyImGui.color_edit4(f"##floatcol_{key}", state.floating_custom_colors[key])
                if list(new_col) != state.floating_custom_colors[key]:
                    state.floating_custom_colors[key] = new_col
                    for i, ch in zip("rgba", new_col):
                        handler._write_setting("FloatingMenu", f"{key}_{i}", ch, to_account=use_account_settings())

def draw_account_widget_config():
    from . import config_scope
    PyImGui.spacing()
    PyImGui.text("Widget Settings")
    PyImGui.separator()

    PyImGui.spacing()
    label = "Use settings from:"
    x, y = PyImGui.get_cursor_pos()
    PyImGui.set_cursor_pos(x, y + 5)
    PyImGui.text(label)
    PyImGui.same_line(0, -1)
    PyImGui.set_cursor_pos(x + 160, y)
    PyImGui.set_next_item_width(PyImGui.get_content_region_avail()[0])
    prev_scope = config_scope.selected_settings_scope
    config_scope.selected_settings_scope = PyImGui.combo(
        "##settings_scope",
        config_scope.selected_settings_scope,
        state.settings_scope_options
    )

    if config_scope.selected_settings_scope != prev_scope:
        handler._write_account_setting("WidgetManager", "use_account_settings", str(use_account_settings()))
        if use_account_settings():
            load_account_settings()
        else:
            load_global_settings()
        handler.discover_widgets()
    
    ImGui.show_tooltip("Determines whether to load and save settings globally or per account")

    PyImGui.spacing()
    PyImGui.text("Save Current Widget Settings:")
    
    
    
    PyImGui.spacing()
    label = "Save Settings:"
    x, y = PyImGui.get_cursor_pos()
    PyImGui.set_cursor_pos(x, y + 5)
    PyImGui.text(label)
    PyImGui.same_line(0, -1)
    PyImGui.set_cursor_pos(x + 160, y)
    save_label = "  Save to Global Settings "
    save_width = PyImGui.calc_text_size(save_label)[0] + 20
    # center = (PyImGui.get_content_region_avail()[0] - save_width) * 0.5
    PyImGui.set_cursor_pos_x(PyImGui.get_cursor_pos_x())
    PyImGui.push_style_color(PyImGui.ImGuiCol.Button, (0.0, 0.2, 0.4, 1.0))
    PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonHovered, (0.2, 0.4, 0.6, 1.0))
    PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonActive, (0.1, 0.3, 0.5, 1.0))
    if PyImGui.button(save_label, save_width, 0):
        save_all_settings(to_account=False)
    PyImGui.pop_style_color(3)
    
    PyImGui.same_line(0,-1)
    
    PyImGui.spacing()
    label = ""
    x, y = PyImGui.get_cursor_pos()
    PyImGui.set_cursor_pos(x, y + 5)
    PyImGui.text(label)
    PyImGui.same_line(0, -1)
    PyImGui.set_cursor_pos(x + 160, y)
    save_label = "Save to Account Settings"
    save_width = PyImGui.calc_text_size(save_label)[0] + 20
    # center = (PyImGui.get_content_region_avail()[0] - save_width) * 0.5
    PyImGui.set_cursor_pos_x(PyImGui.get_cursor_pos_x())
    PyImGui.push_style_color(PyImGui.ImGuiCol.Button, (0.0, 0.2, 0.4, 1.0))
    PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonHovered, (0.2, 0.4, 0.6, 1.0))
    PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonActive, (0.1, 0.3, 0.5, 1.0))
    if PyImGui.button(save_label, save_width, 0):
        save_all_settings(to_account=True)
    PyImGui.pop_style_color(3)
    
    PyImGui.spacing()
    label = "Restore Settings:"
    x, y = PyImGui.get_cursor_pos()
    PyImGui.set_cursor_pos(x, y + 5)
    PyImGui.text(label)
    PyImGui.same_line(0, -1)
    PyImGui.set_cursor_pos(x + 160, y)
    the_label = "Restore Default Global Settings "
    the_width = PyImGui.calc_text_size(the_label)[0] + 20
    # center = (PyImGui.get_content_region_avail()[0] - save_width) * 0.5
    PyImGui.set_cursor_pos_x(PyImGui.get_cursor_pos_x())
    PyImGui.push_style_color(PyImGui.ImGuiCol.Button, (0.0, 0.2, 0.4, 1.0))
    PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonHovered, (0.2, 0.4, 0.6, 1.0))
    PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonActive, (0.1, 0.3, 0.5, 1.0))
    if PyImGui.button(the_label, the_width, 0):
        restore_global_defaults()
        load_global_settings()
        from . import config_scope
        config_scope.selected_settings_scope = 0
        handler.discover_widgets()
    PyImGui.pop_style_color(3)

        
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
    enable_qd = draw_centered_checkbox(label, state.enable_quick_dock)
    if enable_qd != state.enable_quick_dock:
        state.enable_quick_dock = enable_qd
        handler._write_setting("QuickDock", "enable_quick_dock", str(enable_qd), to_account=use_account_settings())
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
    new_color = PyImGui.color_edit3("##rcolor", (state.quick_dock_color[0], state.quick_dock_color[1], state.quick_dock_color[2]))
    if list(new_color[:3]) != state.quick_dock_color[:3]:
        state.quick_dock_color[0:3] = new_color[0:3]
        for i, key in enumerate(("r", "g", "b")):
            handler._write_setting("QuickDockColor", key, f"{state.quick_dock_color[i]}", to_account=use_account_settings())
     
    PyImGui.spacing() 
    label = "Quick Dock Transparency:"
    x, y = PyImGui.get_cursor_pos()
    PyImGui.set_cursor_pos(x, y + 5)
    PyImGui.text(label)
    PyImGui.same_line(0, -1)
    PyImGui.set_cursor_pos(x + 160, y)
    PyImGui.set_next_item_width(PyImGui.get_content_region_avail()[0])
    alpha = PyImGui.slider_float("Quick Dock Transparency", state.quick_dock_color[3], 0.0, 1.0)
    if alpha != state.quick_dock_color[3]:
        state.quick_dock_color[3] = alpha
        handler._write_setting("QuickDockColor", "a", f"{alpha}", to_account=use_account_settings())
    
    PyImGui.spacing()
    new_width = draw_labeled_slider("Quick Dock Width:", "##rwidth", state.quick_dock_width, 4, 50)
    if new_width != state.quick_dock_width:
        state.quick_dock_width = new_width
        handler._write_setting("QuickDock", "width", str(state.quick_dock_width), to_account=use_account_settings())

    PyImGui.spacing()
    new_height = draw_labeled_slider("Quick Dock Height:", "##rheight", state.quick_dock_height, 20, 150)
    if new_height != state.quick_dock_height:
        state.quick_dock_height = new_height
        handler._write_setting("QuickDock", "height", str(state.quick_dock_height), to_account=use_account_settings())

    PyImGui.spacing()
    new_bpr = draw_labeled_slider("Buttons Per Row:", "##bpr", state.buttons_per_row, 1, 16)
    if new_bpr != state.buttons_per_row:
        state.buttons_per_row = new_bpr
        handler._write_setting("QuickDock", "buttons_per_row", str(state.buttons_per_row), to_account=use_account_settings())
    
    PyImGui.spacing()
    label = "Quick Dock is Unlocked" if state.quick_dock_unlocked else "Quick Dock is Locked"
    qd_unlocked = PyImGui.checkbox(label, state.quick_dock_unlocked)
    if qd_unlocked != state.quick_dock_unlocked:
        state.quick_dock_unlocked = qd_unlocked
        handler._write_setting("QuickDock", "unlocked", str(qd_unlocked), to_account=use_account_settings())
    ImGui.show_tooltip("Click to lock" if state.quick_dock_unlocked else "Click to unlock")
    
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

    PyImGui.begin_child("QuickDockWidgetList", (0.0, 150.0), True, 0)
    for idx, (name, widget) in enumerate(handler.widgets.items()):
        data = handler.widget_data_cache.get(name, {})
        if data.get("hidden", False) and not state.show_hidden_widgets:
            continue
        dock_enabled = data.get("quickdock", False)
        icon_name = data.get("icon", "ICON_CIRCLE")
        icon_char = getattr(IconsFontAwesome5, icon_name, "?")

        PyImGui.text(f"{icon_char} {name}")
        PyImGui.same_line(200, -1)

        new_dock_enabled = PyImGui.checkbox(f"##dock_{idx}", bool(dock_enabled))
        if new_dock_enabled != dock_enabled:
            data["quickdock"] = new_dock_enabled
            handler._write_setting(name, "quickdock", str(new_dock_enabled), to_account=use_account_settings())
    PyImGui.end_child()

def draw_debug_config():
    PyImGui.text("Debug Widget Settings")
    PyImGui.spacing()  
    state.show_hidden_widgets = PyImGui.checkbox("Show Hidden Widgets", state.show_hidden_widgets)
    PyImGui.show_tooltip("Toggle visibility of hidden/internal widgets in menus")
    PyImGui.spacing()
    if PyImGui.collapsing_header("Edit Specific Widget Data"):
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
            handler._write_setting(state.selected_widget, "enabled", str(updated_enabled), to_account=use_account_settings())

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
            handler._write_setting(state.selected_widget, "icon", icon_names[new_index], to_account=use_account_settings())

        if new_category != category:
            data["category"] = new_category
            handler._write_setting(state.selected_widget, "category", new_category, to_account=use_account_settings())

        if new_sub != subcategory:
            data["subcategory"] = new_sub
            handler._write_setting(state.selected_widget, "subcategory", new_sub, to_account=use_account_settings())