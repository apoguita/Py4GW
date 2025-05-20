from Py4GWCoreLib import PyImGui, ImGui, Utils, ConsoleLog, IconsFontAwesome5, Py4GW
from .handler import handler
from .config_scope import use_account_settings
from . import state

CAT_COLOR = Utils.RGBToNormal(200, 255, 150, 255)

_cached_popup_state = {
    "version": None,
    "show_hidden": None,
    "render_list": [],
    "grouped": None
}

def draw_widget_popup_menus():
    current_version = id(handler.widgets)
    show_hidden = state.show_hidden_widgets

    if (_cached_popup_state["version"] != current_version or
        _cached_popup_state["show_hidden"] != show_hidden):

        render_list = []
        grouped = {}

        from collections import defaultdict
        grouped = defaultdict(lambda: defaultdict(list))

        for name, info in handler.widgets.items():
            data = handler.widget_data_cache.get(name, {})
            if data.get("hidden", False) and not show_hidden:
                continue

            cat = data.get("category", "Miscellaneous")
            sub = data.get("subcategory") or "General"

            item = {
                "name": name,
                "cat": cat,
                "sub": sub,
                "configure_id": IconsFontAwesome5.ICON_COG + f"##Configure{name}",
                "info": info
            }
            render_list.append(item)
            grouped[cat][sub].append(item)

        _cached_popup_state.update({
            "version": current_version,
            "show_hidden": show_hidden,
            "render_list": render_list,
            "grouped": grouped
        })

    grouped = _cached_popup_state["grouped"]
    written_this_frame = set()

    for cat, subs in grouped.items():
        if not PyImGui.begin_menu(cat):
            continue
        if PyImGui.is_window_collapsed():
            PyImGui.end_menu()
            continue

        for sub, widgets in subs.items():
            if not widgets or not PyImGui.begin_menu(sub):
                continue

            if not PyImGui.begin_table(f"Widgets_{cat}_{sub}", 2, PyImGui.TableFlags.Borders):
                PyImGui.end_menu()
                continue

            for item in widgets:
                PyImGui.table_next_row()
                PyImGui.table_set_column_index(0)

                enabled = item["info"].get("enabled", False)
                new_enabled = PyImGui.checkbox(item["name"], enabled)

                if new_enabled != enabled and (item["name"], "enabled") not in written_this_frame:
                    item["info"]["enabled"] = new_enabled
                    handler._write_setting(item["name"], "enabled", str(new_enabled), to_account=use_account_settings())
                    written_this_frame.add((item["name"], "enabled"))
                    state.reopen_floating_menu = True

                PyImGui.table_set_column_index(1)
                if new_enabled:
                    PyImGui.push_style_color(PyImGui.ImGuiCol.Text, CAT_COLOR)

                item["info"]["configuring"] = ImGui.toggle_button(item["configure_id"], item["info"]["configuring"])

                if new_enabled:
                    PyImGui.pop_style_color(1)

            PyImGui.end_table()
            PyImGui.end_menu()
        PyImGui.end_menu()
