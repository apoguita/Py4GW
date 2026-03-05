import PyImGui
import Py4GW.UI as UI


PROFESSIONS = [
    "Warrior",
    "Ranger",
    "Monk",
    "Necromancer",
    "Mesmer",
    "Elementalist",
    "Assassin",
    "Ritualist",
    "Paragon",
    "Dervish",
]

ui_window = None
GRID_ROWS = 16

# Immediate-mode state for the PyImGui benchmark window.
imgui_state = {
    "show_window": True,
    "enabled": False,
    "name": "Apo",
    "level": 20,
    "speed": 1.5,
    "volume": 35,
    "scale": 1.0,
    "profession_idx": 0,
    "opt_a": True,
    "opt_b": False,
    "opt_c": True,
    "radio_idx": 1,
    "select_a": False,
    "select_b": True,
    "progress": 0.42,
    "color_rgba": (0.20, 0.70, 0.90, 1.00),
    "clipboard_text": "Py4GW UI stress clipboard",
    "grid_checks": [i % 2 == 0 for i in range(GRID_ROWS)],
    "grid_values": [10 + (i * 5) for i in range(GRID_ROWS)],
    "grid_last_click": -1,
}


def _seed_ui_vars(window: UI.UI) -> None:
    window.set_var("show_window", True)
    window.set_var("enabled", False)
    window.set_var("name", "Apo")
    window.set_var("level", 20)
    window.set_var("speed", 1.5)
    window.set_var("volume", 35)
    window.set_var("scale", 1.0)
    window.set_var("profession_idx", 0)
    window.set_var("opt_a", True)
    window.set_var("opt_b", False)
    window.set_var("opt_c", True)
    window.set_var("radio_idx", 1)
    window.set_var("select_a", False)
    window.set_var("select_b", True)
    window.set_var("progress", 0.42)
    window.set_var("color_rgba", (0.20, 0.70, 0.90, 1.00))
    window.set_var("button_clicked", False)
    window.set_var("small_clicked", False)
    window.set_var("invisible_clicked", False)
    window.set_var("hovered_last", False)
    window.set_var("collapsed", False)
    window.set_var("text_w", 0.0)
    window.set_var("text_h", 0.0)
    window.set_var("avail_w", 0.0)
    window.set_var("avail_h", 0.0)
    window.set_var("win_x", 0.0)
    window.set_var("win_y", 0.0)
    window.set_var("win_w", 0.0)
    window.set_var("win_h", 0.0)
    window.set_var("clip_text", "")
    window.set_var("grid_last_click", -1)
    for i in range(GRID_ROWS):
        window.set_var(f"grid_check_{i}", i % 2 == 0)
        window.set_var(f"grid_value_{i}", 10 + (i * 5))
        window.set_var(f"grid_btn_{i}", False)


def _record_ui(window: UI.UI) -> None:
    window.clear_ui()

    # Window/layout setup
    window.set_next_window_size(1080, 760)
    window.begin("Stress Test: UI Class", "show_window", 0)
    window.text_colored("Py4GW.UI Cached Command Stress Window", (0.90, 0.95, 0.40, 1.0))
    window.text_wrapped("This window intentionally packs many widgets and containers for benchmark coverage.")
    window.separator()

    # Top controls row
    window.button("Big Button", "button_clicked", 120, 28)
    window.same_line()
    window.small_button("Small", "small_clicked")
    window.same_line()
    window.invisible_button("##inv_btn", 100, 22, "invisible_clicked")
    window.same_line()
    window.text_disabled("Invisible button area on left")
    window.separator()

    # Tabs + dense table layout
    window.begin_tab_bar("StressTabs")

    window.begin_tab_item("Controls")
    window.begin_table("ControlsTable", 4, 0)
    window.table_setup_column("Column A", 0, 220.0)
    window.table_setup_column("Column B", 0, 280.0)
    window.table_setup_column("Column C", 0, 280.0)
    window.table_setup_column("Column D", 0, 300.0)
    window.table_headers_row()
    window.table_next_row()

    # Column A
    window.table_set_column_index(0)
    window.checkbox("Enabled", "enabled")
    window.checkbox("Opt A", "opt_a")
    window.checkbox("Opt B", "opt_b")
    window.checkbox("Opt C", "opt_c")
    window.input_text("Name", "name")
    window.input_int("Level", "level")
    window.input_float("Speed", "speed")
    window.slider_int("Volume", "volume", 0, 100)
    window.slider_float("Scale", "scale", 0.25, 3.0)
    window.combo("Profession", "profession_idx", PROFESSIONS)
    window.radio_button("Radio 0", "radio_idx", 0)
    window.radio_button("Radio 1", "radio_idx", 1)
    window.radio_button("Radio 2", "radio_idx", 2)
    window.color_edit4("Color", "color_rgba")
    window.selectable("Selectable A", "select_a")
    window.selectable("Selectable B", "select_b")

    # Column B
    window.table_set_column_index(1)
    window.text("Progress")
    window.progress_bar(0.42, 220.0, "42%")
    window.progress_bar_ex(0.68, 220.0, 18.0, "68%")
    window.spacing()
    window.push_style_color(0, (0.85, 0.35, 0.35, 1.0))
    window.text_colored("Styled text sample", (0.70, 1.00, 0.75, 1.0))
    window.pop_style_color()
    window.new_line()
    window.bullet_text("Bullet item one")
    window.bullet_text("Bullet item two")
    window.bullet_text("Bullet item three")
    window.separator()
    window.begin_group()
    window.text("Indent Group")
    window.indent(12.0)
    window.text("Indented line A")
    window.text("Indented line B")
    window.unindent(12.0)
    window.end_group()
    window.separator()
    window.text("Child region:")
    window.begin_child("StressChild", 300.0, 170.0, True, 0)
    window.text("Child text line 1")
    window.text("Child text line 2")
    window.text("Child text line 3")
    window.end_child()

    # Column C
    window.table_set_column_index(2)
    window.text("Queries / Metrics")
    window.calc_text_size("Py4GW.UI", "text_w", "text_h")
    window.get_content_region_avail("avail_w", "avail_h")
    window.is_item_hovered("hovered_last")
    window.is_window_collapsed("collapsed")
    window.get_window_pos("win_x", "win_y")
    window.get_window_size("win_w", "win_h")
    window.get_clipboard_text("clip_text")
    window.text(f"text_size=({float(window.vars('text_w')):.1f},{float(window.vars('text_h')):.1f})")
    window.text(f"avail=({float(window.vars('avail_w')):.1f},{float(window.vars('avail_h')):.1f})")
    window.text(f"win_pos=({float(window.vars('win_x')):.1f},{float(window.vars('win_y')):.1f})")
    window.text(f"win_size=({float(window.vars('win_w')):.1f},{float(window.vars('win_h')):.1f})")
    window.text(f"hovered_last={bool(window.vars('hovered_last'))}")
    window.text(f"collapsed={bool(window.vars('collapsed'))}")
    window.show_tooltip("Hover this metrics area.")
    window.text_disabled("Tooltip APIs")
    window.set_tooltip("Persistent tooltip sample")

    # Column D
    window.table_set_column_index(3)
    window.text("Dense list")
    for i in range(20):
        window.bullet_text(f"Row {i:02d} sample text")
    window.separator()
    window.text_wrapped("This column is intentionally dense to increase widget count per frame.")

    window.end_table()
    window.end_tab_item()

    window.begin_tab_item("Grid")
    window.text("4-column grid with repeated controls")
    window.begin_table("GridTableUI", 4, 0)
    window.table_setup_column("ID", 0, 80.0)
    window.table_setup_column("Toggle", 0, 140.0)
    window.table_setup_column("Value", 0, 220.0)
    window.table_setup_column("Action", 0, 220.0)
    window.table_headers_row()
    for i in range(GRID_ROWS):
        window.table_next_row()
        window.table_set_column_index(0)
        window.text(f"Item {i:02d}")
        window.table_set_column_index(1)
        window.checkbox(f"##grid_check_{i}", f"grid_check_{i}")
        window.same_line()
        window.text(f"Enabled {i:02d}")
        window.table_set_column_index(2)
        window.slider_int(f"##grid_value_{i}", f"grid_value_{i}", 0, 100)
        window.table_set_column_index(3)
        window.button(f"Run {i:02d}", f"grid_btn_{i}", 120, 24)
    window.end_table()
    window.end_tab_item()

    window.begin_tab_item("Popups")
    window.text("Popup examples")
    window.button("Open Popup", "button_clicked", 120, 26)
    window.open_popup("SamplePopup")
    window.begin_popup("SamplePopup", 0)
    window.text("Inside popup")
    window.menu_item("Menu Item", "small_clicked")
    window.close_current_popup()
    window.end_popup()
    window.end_tab_item()

    window.end_tab_bar()
    window.end()


def _ensure_ui() -> None:
    global ui_window
    if ui_window is None:
        ui_window = UI.UI()
        _seed_ui_vars(ui_window)


def update():
    _ensure_ui()
    if ui_window is not None:
        _record_ui(ui_window)


def draw():
    if ui_window is not None:
        ui_window.render()


def main():
    update()

    # Immediate-mode reference window with dense object count + multi-column table.
    show = imgui_state["show_window"]
    visible, show = PyImGui.begin_with_close("Stress Test: PyImGui", show, 0)
    imgui_state["show_window"] = show
    if visible:
        PyImGui.text_colored("PyImGui Immediate Window", (0.95, 0.95, 0.35, 1.0))
        PyImGui.text_wrapped("Dense widget layout for side-by-side visual benchmark.")
        PyImGui.separator()

        PyImGui.button("Big Button", 120, 28)
        PyImGui.same_line(0, -1)
        PyImGui.small_button("Small")
        PyImGui.same_line(0, -1)
        PyImGui.invisible_button("##inv_btn_imgui", 100, 22)
        PyImGui.same_line(0, -1)
        PyImGui.text_disabled("Invisible button area on left")
        PyImGui.separator()

        if PyImGui.begin_tab_bar("StressTabsImGui"):
            if PyImGui.begin_tab_item("Controls"):
                if PyImGui.begin_table("ControlsTableImGui", 4, PyImGui.TableFlags.NoFlag):
                    PyImGui.table_setup_column("Column A", PyImGui.TableColumnFlags.NoFlag, 220.0)
                    PyImGui.table_setup_column("Column B", PyImGui.TableColumnFlags.NoFlag, 280.0)
                    PyImGui.table_setup_column("Column C", PyImGui.TableColumnFlags.NoFlag, 280.0)
                    PyImGui.table_setup_column("Column D", PyImGui.TableColumnFlags.NoFlag, 300.0)
                    PyImGui.table_headers_row()
                    PyImGui.table_next_row()

                    PyImGui.table_set_column_index(0)
                    imgui_state["enabled"] = PyImGui.checkbox("Enabled", imgui_state["enabled"])
                    imgui_state["opt_a"] = PyImGui.checkbox("Opt A", imgui_state["opt_a"])
                    imgui_state["opt_b"] = PyImGui.checkbox("Opt B", imgui_state["opt_b"])
                    imgui_state["opt_c"] = PyImGui.checkbox("Opt C", imgui_state["opt_c"])
                    imgui_state["name"] = PyImGui.input_text("Name", imgui_state["name"])
                    imgui_state["level"] = PyImGui.input_int("Level", int(imgui_state["level"]))
                    imgui_state["speed"] = PyImGui.input_float("Speed", float(imgui_state["speed"]))
                    imgui_state["volume"] = PyImGui.slider_int("Volume", int(imgui_state["volume"]), 0, 100)
                    imgui_state["scale"] = PyImGui.slider_float("Scale", float(imgui_state["scale"]), 0.25, 3.0)
                    imgui_state["profession_idx"] = PyImGui.combo("Profession", int(imgui_state["profession_idx"]), PROFESSIONS)
                    imgui_state["radio_idx"] = PyImGui.radio_button("Radio 0", int(imgui_state["radio_idx"]), 0)
                    imgui_state["radio_idx"] = PyImGui.radio_button("Radio 1", int(imgui_state["radio_idx"]), 1)
                    imgui_state["radio_idx"] = PyImGui.radio_button("Radio 2", int(imgui_state["radio_idx"]), 2)
                    imgui_state["color_rgba"] = PyImGui.color_edit4("Color", imgui_state["color_rgba"])
                    imgui_state["select_a"] = PyImGui.selectable("Selectable A", imgui_state["select_a"], 0, (0.0, 0.0))
                    imgui_state["select_b"] = PyImGui.selectable("Selectable B", imgui_state["select_b"], 0, (0.0, 0.0))

                    PyImGui.table_set_column_index(1)
                    PyImGui.text("Progress")
                    PyImGui.progress_bar(0.42, 220.0, "42%")
                    PyImGui.progress_bar(0.68, 220.0, 18.0, "68%")
                    PyImGui.spacing()
                    PyImGui.text_colored("Styled text sample", (0.70, 1.00, 0.75, 1.0))
                    PyImGui.new_line()
                    PyImGui.bullet_text("Bullet item one")
                    PyImGui.bullet_text("Bullet item two")
                    PyImGui.bullet_text("Bullet item three")
                    PyImGui.separator()
                    PyImGui.begin_group()
                    PyImGui.text("Indent Group")
                    PyImGui.indent(12.0)
                    PyImGui.text("Indented line A")
                    PyImGui.text("Indented line B")
                    PyImGui.unindent(12.0)
                    PyImGui.end_group()
                    PyImGui.separator()
                    PyImGui.text("Child region:")
                    if PyImGui.begin_child("StressChildImGui", (300.0, 170.0), True, 0):
                        PyImGui.text("Child text line 1")
                        PyImGui.text("Child text line 2")
                        PyImGui.text("Child text line 3")
                    PyImGui.end_child()

                    PyImGui.table_set_column_index(2)
                    PyImGui.text("Queries / Metrics")
                    tw, th = PyImGui.calc_text_size("PyImGui")
                    aw, ah = PyImGui.get_content_region_avail()
                    wposx, wposy = PyImGui.get_window_pos()
                    wsizex, wsizey = PyImGui.get_window_size()
                    imgui_state["hovered_last"] = PyImGui.is_item_hovered()
                    imgui_state["collapsed"] = PyImGui.is_window_collapsed()
                    PyImGui.text(f"text_size=({tw:.1f},{th:.1f})")
                    PyImGui.text(f"avail=({aw:.1f},{ah:.1f})")
                    PyImGui.text(f"win_pos=({wposx:.1f},{wposy:.1f})")
                    PyImGui.text(f"win_size=({wsizex:.1f},{wsizey:.1f})")
                    if PyImGui.is_item_hovered():
                        PyImGui.show_tooltip("Hovered metrics text")
                    PyImGui.set_tooltip("Persistent tooltip sample")

                    PyImGui.table_set_column_index(3)
                    PyImGui.text("Dense list")
                    for i in range(20):
                        PyImGui.bullet_text(f"Row {i:02d} sample text")
                    PyImGui.separator()
                    PyImGui.text_wrapped("This column is intentionally dense to increase widget count per frame.")

                    PyImGui.end_table()
                PyImGui.end_tab_item()

            if PyImGui.begin_tab_item("Grid"):
                PyImGui.text("4-column grid with repeated controls")
                if PyImGui.begin_table("GridTableImGui", 4, PyImGui.TableFlags.NoFlag):
                    PyImGui.table_setup_column("ID", PyImGui.TableColumnFlags.NoFlag, 80.0)
                    PyImGui.table_setup_column("Toggle", PyImGui.TableColumnFlags.NoFlag, 140.0)
                    PyImGui.table_setup_column("Value", PyImGui.TableColumnFlags.NoFlag, 220.0)
                    PyImGui.table_setup_column("Action", PyImGui.TableColumnFlags.NoFlag, 220.0)
                    PyImGui.table_headers_row()
                    for i in range(GRID_ROWS):
                        PyImGui.table_next_row()
                        PyImGui.table_set_column_index(0)
                        PyImGui.text(f"Item {i:02d}")
                        PyImGui.table_set_column_index(1)
                        imgui_state["grid_checks"][i] = PyImGui.checkbox(f"##grid_check_imgui_{i}", imgui_state["grid_checks"][i])
                        PyImGui.same_line(0, -1)
                        PyImGui.text(f"Enabled {i:02d}")
                        PyImGui.table_set_column_index(2)
                        imgui_state["grid_values"][i] = PyImGui.slider_int(
                            f"##grid_value_imgui_{i}", int(imgui_state["grid_values"][i]), 0, 100
                        )
                        PyImGui.table_set_column_index(3)
                        if PyImGui.button(f"Run {i:02d}", 120, 24):
                            imgui_state["grid_last_click"] = i
                    PyImGui.end_table()
                PyImGui.text(f"Last clicked row: {imgui_state['grid_last_click']}")
                PyImGui.end_tab_item()

            if PyImGui.begin_tab_item("Popups"):
                PyImGui.text("Popup examples")
                if PyImGui.button("Open Popup"):
                    PyImGui.open_popup("SamplePopupImGui")
                if PyImGui.begin_popup("SamplePopupImGui"):
                    PyImGui.text("Inside popup")
                    PyImGui.menu_item("Menu Item")
                    PyImGui.close_current_popup()
                    PyImGui.end_popup()
                PyImGui.end_tab_item()

            PyImGui.end_tab_bar()

    PyImGui.end()


if __name__ == "__main__":
    main()
