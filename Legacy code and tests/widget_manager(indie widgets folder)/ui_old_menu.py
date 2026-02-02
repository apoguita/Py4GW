from Py4GWCoreLib import PyImGui, ImGui, IconsFontAwesome5, ConsoleLog, Py4GW, Utils, ThrottledTimer
from .handler import handler
from .config_scope import use_account_settings
from . import state
    
timer = ThrottledTimer(400)
def draw_old_widget_ui():
    global timer
    is_enabled = state.enable_all
    
    if state.window_module.first_run:
            PyImGui.set_next_window_size(*state.window_module.window_size)
            PyImGui.set_next_window_pos(*state.window_module.window_pos)
            PyImGui.set_next_window_collapsed(state.window_module.collapse, 0)
            state.window_module.first_run = False
            
    if PyImGui.begin(state.window_module.window_name, state.window_module.window_flags):
        current_pos = PyImGui.get_window_pos()
        if (current_pos != state.old_menu_window_pos) and timer.IsExpired():
            state.old_menu_window_pos = tuple(current_pos)
            handler._write_setting("WidgetManager", "omx", str(int(current_pos[0])), to_account=use_account_settings())
            handler._write_setting("WidgetManager", "omy", str(int(current_pos[1])), to_account=use_account_settings())
            timer.Reset()


        collapsed = PyImGui.is_window_collapsed()
        if collapsed != state.old_menu_window_collapsed:
            state.old_menu_window_collapsed = collapsed
            handler._write_setting("WidgetManager", "collapsed", str(collapsed), to_account=use_account_settings())
        if PyImGui.button(IconsFontAwesome5.ICON_RETWEET + "##Reload Widgets"):
            ConsoleLog(state.module_name, "Reloading Widgets...", Py4GW.Console.MessageType.Info)
            handler.discover_widgets()
        ImGui.show_tooltip("Reloads all widgets")
        PyImGui.same_line(0.0, 10)
        
        toggle_label = IconsFontAwesome5.ICON_TOGGLE_ON if state.enable_all else IconsFontAwesome5.ICON_TOGGLE_OFF
        if is_enabled:
            PyImGui.push_style_color(PyImGui.ImGuiCol.Button, (0.153, 0.318, 0.929, 1.0))
            PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonHovered, (0.6, 0.6, 0.9, 1.0))
            PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonActive, (0.6, 0.6, 0.6, 1.0))
        if PyImGui.button(toggle_label + "##widget_disable"):
            state.enable_all = not state.enable_all
            handler._write_global_setting(state.module_name, "enable_all", str(state.enable_all))
        if is_enabled:
            PyImGui.pop_style_color(3)
        ImGui.show_tooltip("Toggle all widgets")
        PyImGui.separator()
        draw_widget_contents_old()
    PyImGui.end()

def draw_widget_contents_old():
    categorized_widgets = {}
    for name, info in handler.widgets.items():
        data = handler.widget_data_cache.get(name, {})
        if data.get("hidden", False) and not state.show_hidden_widgets:
            continue
        cat = data.get("category", "Miscellaneous")
        sub = data.get("subcategory", "")
        categorized_widgets.setdefault(cat, {}).setdefault(sub, []).append(name)

    sub_color = Utils.RGBToNormal(255, 200, 100, 255)
    cat_color = Utils.RGBToNormal(200, 255, 150, 255)

    for cat, subs in categorized_widgets.items():
        if not PyImGui.collapsing_header(cat):
            continue
        for sub, names in subs.items():
            if not sub:
                continue
            PyImGui.push_style_color(PyImGui.ImGuiCol.Text, sub_color)
            if not PyImGui.tree_node(sub):
                PyImGui.pop_style_color(1)
                continue
            PyImGui.pop_style_color(1)
            
            if not PyImGui.begin_table(f"Widgets {cat}{sub}", 2, PyImGui.TableFlags.Borders):
                PyImGui.tree_pop()
                continue
            
            for name in names:
                info = handler.widgets[name]
                PyImGui.table_next_row()
                PyImGui.table_set_column_index(0)
                new_enabled = PyImGui.checkbox(name, bool(info["enabled"]))
                if new_enabled != info["enabled"]:
                    info["enabled"] = new_enabled
                    handler._write_setting(name, "enabled", str(new_enabled), to_account=use_account_settings())
                    
                PyImGui.table_set_column_index(1)
                if info["enabled"]:
                    PyImGui.push_style_color(PyImGui.ImGuiCol.Text, cat_color)
                info["configuring"] = ImGui.toggle_button(IconsFontAwesome5.ICON_COG + f"##Configure{name}", info["configuring"])
                if info["enabled"]:
                    PyImGui.pop_style_color(1)

            PyImGui.end_table()
            PyImGui.tree_pop()