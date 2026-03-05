import os
import sys
import time


EXPECTED_RUNTIME_ERRORS = (TypeError, ValueError, RuntimeError, AttributeError, IndexError, KeyError, OSError)


def _viewer_runtime_module(viewer):
    try:
        return sys.modules.get(viewer.__class__.__module__)
    except EXPECTED_RUNTIME_ERRORS:
        return None


def _runtime_attr(viewer, name: str, fallback=None):
    module = _viewer_runtime_module(viewer)
    if module is not None and hasattr(module, name):
        return getattr(module, name)
    return fallback


def _mouse_in_rect(viewer, rect) -> bool:
    pyimgui = _runtime_attr(viewer, "PyImGui")
    if pyimgui is None:
        return False
    try:
        io = pyimgui.get_io()
        mx = float(getattr(io, "mouse_pos_x", -1.0))
        my = float(getattr(io, "mouse_pos_y", -1.0))
        rx, ry, rw, rh = rect
        return (mx >= rx) and (mx <= (rx + rw)) and (my >= ry) and (my <= (ry + rh))
    except EXPECTED_RUNTIME_ERRORS:
        return False


def _item_rect(pyimgui):
    try:
        rect_min = pyimgui.get_item_rect_min()
        rect_max = pyimgui.get_item_rect_max()
        return (
            float(rect_min[0]),
            float(rect_min[1]),
            max(0.0, float(rect_max[0]) - float(rect_min[0])),
            max(0.0, float(rect_max[1]) - float(rect_min[1])),
        )
    except EXPECTED_RUNTIME_ERRORS:
        return None


def _draw_main_gui(viewer, pyimgui, imgui, map_api, player_api, py4gw_api):
    hovered = False
    if not viewer.viewer_window_initialized:
        if viewer.saved_viewer_window_pos is not None:
            sw, sh = viewer.saved_viewer_window_size if viewer.saved_viewer_window_size is not None else (760.0, 520.0)
            sw, sh = viewer._clamp_size(sw, sh)
            px, py = viewer._clamp_pos(viewer.saved_viewer_window_pos[0], viewer.saved_viewer_window_pos[1], sw, sh)
            pyimgui.set_next_window_pos(px, py)
        if viewer.saved_viewer_window_size is not None:
            sw, sh = viewer._clamp_size(viewer.saved_viewer_window_size[0], viewer.saved_viewer_window_size[1])
            pyimgui.set_next_window_size(sw, sh)

    if pyimgui.begin(viewer.window_name):
        viewer.viewer_window_initialized = True
        current_window_pos = pyimgui.get_window_pos()
        current_window_size = pyimgui.get_window_size()
        top_section_rect = None
        left_rail_rect = None
        data_panel_header_rect = None
        data_panel_item_hovered = False
        try:
            viewer.last_main_window_rect = (
                float(current_window_pos[0]),
                float(current_window_pos[1]),
                float(current_window_size[0]),
                float(current_window_size[1]),
            )
        except EXPECTED_RUNTIME_ERRORS:
            pass

        viewer._persist_layout_value("drop_viewer_window_pos", current_window_pos)
        viewer._persist_layout_value("drop_viewer_window_size", current_window_size)
        hovered = bool(viewer._mouse_in_current_window_rect() or pyimgui.is_window_hovered())
        try:
            window_is_collapsed = bool(pyimgui.is_window_collapsed())
        except EXPECTED_RUNTIME_ERRORS:
            window_is_collapsed = False

        try:
            top_section_start_y = float(current_window_pos[1])
            top_section_x = float(current_window_pos[0])
            top_section_w = float(current_window_size[0])
        except EXPECTED_RUNTIME_ERRORS:
            top_section_start_y = 0.0
            top_section_x = 0.0
            top_section_w = 0.0
        if viewer._styled_button("Refresh (Live)" if viewer.paused else "Refresh", "primary", tooltip="Reload from current live session file."):
            viewer._set_paused(False)
            viewer.last_read_time = 0
            viewer.load_drops()

        pyimgui.same_line(0.0, 10.0)

        if viewer._styled_button("Save", "secondary", tooltip="Save current session log snapshot"):
            viewer.show_save_popup = not viewer.show_save_popup

        if viewer.show_save_popup:
            pyimgui.same_line(0.0, 10.0)
            pyimgui.push_item_width(100)
            viewer.save_filename = pyimgui.input_text("", viewer.save_filename)
            pyimgui.pop_item_width()
            pyimgui.same_line(0.0, 10.0)
            if viewer._styled_button("OK", "primary"):
                viewer.save_run()

        pyimgui.same_line(0.0, 10.0)

        if viewer._styled_button("Load/Merge..", "secondary", tooltip="Load or merge a saved log file"):
            pyimgui.open_popup("LoadMergePopup")

        if pyimgui.begin_popup("LoadMergePopup"):
            if os.path.exists(viewer.saved_logs_dir):
                files = [f for f in os.listdir(viewer.saved_logs_dir) if f.endswith(".csv")]
                if not files:
                    pyimgui.text("No saved logs")
                else:
                    for filename in files:
                        if pyimgui.begin_menu(filename):
                            if pyimgui.menu_item("Load"):
                                viewer.load_run(filename)
                            if pyimgui.menu_item("Merge"):
                                viewer.merge_run(filename)
                            pyimgui.end_menu()
            else:
                pyimgui.text("Directory not found")
            pyimgui.end_popup()

        pyimgui.same_line(0.0, 10.0)
        if viewer._styled_button("Follower Inventory", "secondary", tooltip="Toggle follower inventory viewer."):
            viewer._toggle_follower_inventory_viewer()

        pyimgui.same_line(0.0, 10.0)
        if viewer._styled_button("Sell Gold (No Runes)", "danger", tooltip="Manually sell all Gold-rarity inventory items except anything named Rune."):
            pyimgui.open_popup("ConfirmSellGoldNoRunes")

        if pyimgui.begin_popup_modal("ConfirmSellGoldNoRunes", True, pyimgui.WindowFlags.AlwaysAutoResize):
            pyimgui.text("Sell all GOLD-rarity inventory items?")
            pyimgui.text("Runes will NOT be sold.")
            pyimgui.separator()
            if viewer._styled_button("Yes, Sell", "danger"):
                viewer._trigger_inventory_action("sell_gold_no_runes")
                pyimgui.close_current_popup()
            pyimgui.same_line(0.0, 10.0)
            if viewer._styled_button("Cancel", "secondary"):
                pyimgui.close_current_popup()
            pyimgui.end_popup_modal()

        if viewer.unknown_mod_popup_pending:
            pyimgui.open_popup("UnknownModAlert")
            viewer.unknown_mod_popup_pending = False
        if pyimgui.begin_popup_modal("UnknownModAlert", True, pyimgui.WindowFlags.AlwaysAutoResize):
            pyimgui.text_colored("New Unknown Mod Detected", (1.0, 0.86, 0.40, 1.0))
            pyimgui.separator()
            popup_msg = viewer._ensure_text(getattr(viewer, "unknown_mod_popup_message", "")).strip()
            if popup_msg:
                pyimgui.text_wrapped(popup_msg)
            pyimgui.separator()
            if viewer._styled_button("OK", "primary"):
                pyimgui.close_current_popup()
            pyimgui.end_popup_modal()

        pyimgui.same_line(0.0, 40.0)
        if viewer._styled_button("Clear/Reset", "danger", tooltip="Clear live file and in-memory drop stats"):
            try:
                current_map_id = max(0, viewer._safe_int(map_api.GetMapID(), 0))
                current_instance_uptime_ms = max(0, viewer._safe_int(map_api.GetInstanceUptime(), 0))
                viewer._reset_sender_tracking_session(current_map_id, current_instance_uptime_ms)
                viewer._reset_live_session()
                viewer.last_chat_index = -1
                if player_api.IsChatHistoryReady():
                    viewer.last_chat_index = len(player_api.GetChatHistory())
                viewer.set_status("Log Cleared")
            except EXPECTED_RUNTIME_ERRORS as e:
                if py4gw_api is not None:
                    py4gw_api.Console.Log("DropViewer", f"Clear failed: {e}", py4gw_api.Console.MessageType.Error)

        filtered_rows = viewer._get_filtered_rows()
        viewer._clear_hover_item_preview()
        table_rows = filtered_rows
        viewer._draw_summary_bar(filtered_rows)
        viewer._draw_top_control_strip()
        viewer._draw_live_status_chips()

        if time.time() - viewer.status_time < 5:
            viewer._draw_status_toast(viewer.status_message)

        if not window_is_collapsed:
            try:
                separator_pos = pyimgui.get_cursor_screen_pos()
                top_section_end_y = float(separator_pos[1])
            except EXPECTED_RUNTIME_ERRORS:
                top_section_end_y = top_section_start_y
            if top_section_end_y > top_section_start_y:
                top_section_rect = (
                    top_section_x,
                    top_section_start_y,
                    top_section_w,
                    top_section_end_y - top_section_start_y,
                )

        pyimgui.separator()

        total_w = max(520.0, float(current_window_size[0]) if isinstance(current_window_size, (list, tuple)) and len(current_window_size) >= 2 else 760.0)
        left_w = max(320.0, min(390.0, total_w * 0.46))
        if (total_w - left_w) < 260.0:
            left_w = max(280.0, total_w - 260.0)
        if pyimgui.begin_child("DropViewerLeftRail", size=(left_w, 0), border=True, flags=pyimgui.WindowFlags.NoFlag):
            viewer._draw_view_and_theme_controls()

            if viewer.compact_mode:
                viewer._draw_section_header("Core Actions")
                viewer._draw_inventory_action_cards()
                viewer._draw_auto_inventory_activity()
                viewer._draw_rarity_chips("ID:", viewer._get_selected_id_rarities())
                viewer._draw_rarity_chips("Salvage:", viewer._get_selected_salvage_rarities())
                pyimgui.text_colored("Compact mode hides filters, tabs, and runtime controls.", viewer._ui_colors()["muted"])
            else:
                viewer._draw_section_header("Filters")
                if pyimgui.collapsing_header("Filter Settings"):
                    viewer.search_text = pyimgui.input_text("Search", viewer.search_text)
                    viewer.filter_player = pyimgui.input_text("Player", viewer.filter_player)
                    viewer.filter_map = pyimgui.input_text("Map", viewer.filter_map)
                    viewer.only_rare = pyimgui.checkbox("Only Rare", viewer.only_rare)
                    viewer.hide_gold = pyimgui.checkbox("Hide Gold", viewer.hide_gold)
                    viewer.min_qty = max(1, int(pyimgui.input_int("Min Qty", int(viewer.min_qty))))
                    viewer.auto_scroll = pyimgui.checkbox("Auto Scroll", viewer.auto_scroll)
                    pyimgui.text_colored("Rarity filter moved to the table header.", viewer._ui_colors()["muted"])
                    if viewer._styled_button("Table Top", "secondary", tooltip="Jump table scroll to the top"):
                        viewer._log_table_reset_nonce += 1
                        viewer._agg_table_reset_nonce += 1
                    pyimgui.same_line(0.0, 8.0)
                    if viewer._styled_button("Table Bottom", "secondary", tooltip="Jump table scroll to the bottom"):
                        viewer._request_log_scroll_bottom = True
                        viewer._request_agg_scroll_bottom = True
                    prev_hover_mode = viewer.hover_handle_mode
                    viewer.hover_handle_mode = pyimgui.checkbox("Hover Handle Mode", viewer.hover_handle_mode)
                    if viewer.hover_handle_mode != prev_hover_mode:
                        viewer.runtime_config_dirty = True
                    if pyimgui.is_item_hovered():
                        imgui.show_tooltip("Show as hoverable floating handle instead of always-open window.")
                    if viewer.hover_handle_mode:
                        prev_hover_pin_open = viewer.hover_pin_open
                        viewer.hover_pin_open = pyimgui.checkbox("Pin Open", viewer.hover_pin_open)
                        if viewer.hover_pin_open != prev_hover_pin_open:
                            viewer.runtime_config_dirty = True
                    if viewer.hover_handle_mode and not prev_hover_mode:
                        viewer.hover_is_visible = True
                        viewer.hover_hide_deadline = time.time() + viewer.hover_hide_delay_s

                    if viewer._styled_button("Quick: Rare Only", "primary", tooltip="Enable Rare-only filters quickly"):
                        viewer.only_rare = True
                        viewer.hide_gold = True
                        viewer.filter_rarity_idx = 0
                    if viewer._styled_button("Clear Filters", "secondary", tooltip="Reset all filter fields"):
                        viewer.search_text = ""
                        viewer.filter_player = ""
                        viewer.filter_map = ""
                        viewer.filter_rarity_idx = 0
                        viewer.only_rare = False
                        viewer.hide_gold = False
                        viewer.min_qty = 1

                viewer._draw_conset_controls()
                viewer._draw_section_header("Inventory Actions")
                viewer._draw_inventory_action_cards()
                viewer._draw_auto_inventory_activity()
                viewer._draw_rarity_chips("ID:", viewer._get_selected_id_rarities())
                viewer._draw_rarity_chips("Salvage:", viewer._get_selected_salvage_rarities())

                if pyimgui.begin_tab_bar("DropTrackerInventoryTabs"):
                    if pyimgui.begin_tab_item("ID/Salvage Settings"):
                        if pyimgui.collapsing_header("ID Settings"):
                            old_id = (viewer.id_sel_white, viewer.id_sel_blue, viewer.id_sel_green, viewer.id_sel_purple, viewer.id_sel_gold)
                            viewer.id_sel_white = pyimgui.checkbox("ID White", viewer.id_sel_white)
                            viewer.id_sel_blue = pyimgui.checkbox("ID Blue", viewer.id_sel_blue)
                            viewer.id_sel_green = pyimgui.checkbox("ID Green", viewer.id_sel_green)
                            viewer.id_sel_purple = pyimgui.checkbox("ID Purple", viewer.id_sel_purple)
                            viewer.id_sel_gold = pyimgui.checkbox("ID Gold", viewer.id_sel_gold)
                            if old_id != (viewer.id_sel_white, viewer.id_sel_blue, viewer.id_sel_green, viewer.id_sel_purple, viewer.id_sel_gold):
                                viewer.runtime_config_dirty = True
                                id_payload = viewer._encode_auto_action_payload(viewer.auto_id_enabled, viewer._get_selected_id_rarities())
                                viewer._trigger_inventory_action("cfg_auto_id", id_payload)

                        if pyimgui.collapsing_header("Salvage Settings"):
                            old_salvage = (viewer.salvage_sel_white, viewer.salvage_sel_blue, viewer.salvage_sel_green, viewer.salvage_sel_purple, viewer.salvage_sel_gold)
                            viewer.salvage_sel_white = pyimgui.checkbox("Salvage White", viewer.salvage_sel_white)
                            viewer.salvage_sel_blue = pyimgui.checkbox("Salvage Blue", viewer.salvage_sel_blue)
                            viewer.salvage_sel_green = pyimgui.checkbox("Salvage Green", viewer.salvage_sel_green)
                            viewer.salvage_sel_purple = pyimgui.checkbox("Salvage Purple", viewer.salvage_sel_purple)
                            viewer.salvage_sel_gold = pyimgui.checkbox("Salvage Gold", viewer.salvage_sel_gold)
                            if old_salvage != (viewer.salvage_sel_white, viewer.salvage_sel_blue, viewer.salvage_sel_green, viewer.salvage_sel_purple, viewer.salvage_sel_gold):
                                viewer.runtime_config_dirty = True
                                salvage_payload = viewer._encode_auto_action_payload(viewer.auto_salvage_enabled, viewer._get_selected_salvage_rarities())
                                viewer._trigger_inventory_action("cfg_auto_salvage", salvage_payload)

                        pyimgui.end_tab_item()

                    if pyimgui.begin_tab_item("Inventory Kits"):
                        viewer._draw_inventory_kit_stats_tab()
                        pyimgui.end_tab_item()
                    pyimgui.end_tab_bar()

                viewer._draw_section_header("Advanced")
                viewer.show_runtime_panel = pyimgui.checkbox("Advanced Runtime Controls", viewer.show_runtime_panel)
                runtime_btn_w = max(120.0, float(pyimgui.get_content_region_avail()[0]))
                if viewer._styled_button(
                    "Close Runtime Window" if viewer.runtime_controls_popout else "Open Runtime Window",
                    "secondary",
                    width=runtime_btn_w,
                    height=28.0,
                    tooltip="Open runtime controls in a separate window.",
                ):
                    viewer.runtime_controls_popout = not viewer.runtime_controls_popout
                    if viewer.runtime_controls_popout:
                        viewer.runtime_popout_initialized = False
                    viewer.runtime_config_dirty = True
                if viewer.show_runtime_panel:
                    if viewer.runtime_controls_popout:
                        pyimgui.text_colored("Runtime controls opened in popout window.", viewer._ui_colors()["muted"])
                    else:
                        viewer._draw_runtime_controls()
            try:
                viewer.left_rail_scroll_y = max(0.0, float(pyimgui.get_scroll_y()))
            except EXPECTED_RUNTIME_ERRORS:
                viewer.left_rail_scroll_y = 0.0
        pyimgui.end_child()
        if not window_is_collapsed:
            left_rail_rect = _item_rect(pyimgui)

        pyimgui.same_line(0.0, 10.0)

        if pyimgui.begin_child("DropViewerDataPanel", size=(0, 0), border=False, flags=pyimgui.WindowFlags.NoFlag):
            try:
                data_panel_pos = pyimgui.get_window_pos()
            except EXPECTED_RUNTIME_ERRORS:
                data_panel_pos = None
            if viewer._styled_button("Stats", "success" if viewer.view_mode == "Aggregated" else "secondary", width=116.0, height=30.0, tooltip="Aggregated drops (materials excluded)."):
                viewer.view_mode = "Aggregated"
            pyimgui.same_line(0.0, 8.0)
            if viewer._styled_button("Materials", "success" if viewer.view_mode == "Materials" else "secondary", width=116.0, height=30.0, tooltip="Material-only aggregated drops."):
                viewer.view_mode = "Materials"
            pyimgui.same_line(0.0, 8.0)
            if viewer._styled_button("Log", "success" if viewer.view_mode == "Log" else "secondary", width=116.0, height=30.0, tooltip="Raw drop event log."):
                viewer.view_mode = "Log"
            pyimgui.separator()
            if not window_is_collapsed and data_panel_pos is not None:
                try:
                    after_header_pos = pyimgui.get_cursor_screen_pos()
                    data_panel_size = pyimgui.get_window_size()
                    data_panel_header_rect = (
                        float(data_panel_pos[0]),
                        float(data_panel_pos[1]),
                        float(data_panel_size[0]),
                        max(0.0, float(after_header_pos[1]) - float(data_panel_pos[1])),
                    )
                except EXPECTED_RUNTIME_ERRORS:
                    data_panel_header_rect = None

            if viewer.view_mode == "Log":
                viewer._draw_log(table_rows)
            elif viewer.view_mode == "Materials":
                viewer._draw_aggregated(table_rows, materials_only=True)
            else:
                viewer._draw_aggregated(table_rows, materials_only=False)
            if not window_is_collapsed:
                try:
                    data_panel_item_hovered = bool(pyimgui.is_any_item_hovered())
                except EXPECTED_RUNTIME_ERRORS:
                    data_panel_item_hovered = False
        pyimgui.end_child()

        if not window_is_collapsed:
            hovered = False
            if top_section_rect is not None and _mouse_in_rect(viewer, top_section_rect):
                hovered = True
            if left_rail_rect is not None and _mouse_in_rect(viewer, left_rail_rect):
                hovered = True
            if data_panel_header_rect is not None and _mouse_in_rect(viewer, data_panel_header_rect):
                hovered = True
            if data_panel_item_hovered:
                hovered = True

    pyimgui.end()
    return hovered


def draw_window(viewer):
    pyimgui = _runtime_attr(viewer, "PyImGui")
    imgui = _runtime_attr(viewer, "ImGui")
    map_api = _runtime_attr(viewer, "Map")
    player_api = _runtime_attr(viewer, "Player")
    py4gw_api = _runtime_attr(viewer, "Py4GW")

    now = time.time()
    handle_hovered = False
    main_window_hovered = False

    if viewer.hover_handle_mode:
        handle_hovered = viewer._draw_hover_handle()
        if handle_hovered:
            viewer.hover_is_visible = True
            viewer.hover_hide_deadline = now + viewer.hover_hide_delay_s
        if viewer.hover_pin_open:
            viewer.hover_is_visible = True

        if viewer.hover_is_visible or viewer.hover_pin_open:
            main_window_hovered = bool(_draw_main_gui(viewer, pyimgui, imgui, map_api, player_api, py4gw_api))
            if not main_window_hovered:
                try:
                    main_window_hovered = bool(_mouse_in_rect(viewer, viewer.last_main_window_rect))
                except EXPECTED_RUNTIME_ERRORS:
                    main_window_hovered = False
    else:
        viewer.hover_is_visible = True
        main_window_hovered = bool(_draw_main_gui(viewer, pyimgui, imgui, map_api, player_api, py4gw_api))

    if viewer.hover_handle_mode:
        if main_window_hovered:
            viewer.hover_is_visible = True
            viewer.hover_hide_deadline = now + viewer.hover_hide_delay_s
        if not viewer.hover_pin_open and not handle_hovered and not main_window_hovered and now >= viewer.hover_hide_deadline:
            viewer.hover_is_visible = False

    if viewer.runtime_controls_popout:
        viewer._draw_runtime_controls_popout()
    viewer._flush_runtime_config_if_dirty()
    viewer._flush_unknown_mod_catalog_if_dirty()
