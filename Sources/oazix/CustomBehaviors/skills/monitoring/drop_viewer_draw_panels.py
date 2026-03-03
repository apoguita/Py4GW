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


def draw_selected_item_details(viewer):
    pyimgui = _runtime_attr(viewer, "PyImGui")
    imgui = _runtime_attr(viewer, "ImGui")

    preview_item_key = viewer.hover_preview_item_key
    preview_log_row = viewer.hover_preview_log_row
    active_item_key = preview_item_key if preview_item_key else viewer.selected_item_key
    active_log_row = preview_log_row if preview_log_row else viewer.selected_log_row
    preview_mode = bool(preview_item_key and preview_log_row)

    stats = viewer._collect_selected_item_stats(active_item_key)
    if not stats:
        return

    pyimgui.separator()
    pyimgui.text("Selected Item Stats")
    pyimgui.text_colored(
        f"{stats['name']} ({stats['rarity']})",
        viewer._get_rarity_color(stats["rarity"]),
    )
    pyimgui.text(f"Total Quantity: {stats['quantity']}")
    pyimgui.text(f"Drop Count: {stats['count']}")
    if preview_mode:
        pyimgui.text_colored("Previewing hovered row", (0.78, 0.78, 0.78, 1.0))

    selected_rows = viewer._get_selected_item_rows(item_key=active_item_key)
    if selected_rows and not preview_mode:
        selected_idx = viewer._get_selected_row_index(selected_rows)
        selected_idx = max(0, min(selected_idx, len(selected_rows) - 1))
        if viewer.selected_log_row is None or not viewer._row_matches_selected_item(viewer.selected_log_row):
            viewer.selected_log_row = selected_rows[selected_idx]

        if pyimgui.button("Prev Item"):
            selected_idx = (selected_idx - 1) % len(selected_rows)
            viewer.selected_log_row = selected_rows[selected_idx]
        pyimgui.same_line(0.0, 8.0)
        if pyimgui.button("Next Item"):
            selected_idx = (selected_idx + 1) % len(selected_rows)
            viewer.selected_log_row = selected_rows[selected_idx]
        pyimgui.same_line(0.0, 12.0)
        pyimgui.text_colored(
            f"Showing Item {selected_idx + 1}/{len(selected_rows)}",
            (0.78, 0.78, 0.78, 1.0),
        )

    if active_log_row and viewer._row_matches_selected_item(active_log_row, active_item_key):
        selected_parsed = viewer._parse_drop_row(active_log_row)
        selected_char = viewer._ensure_text(selected_parsed.player_name if selected_parsed else "").strip() or "Unknown"
        selected_map = viewer._ensure_text(selected_parsed.map_name if selected_parsed else "").strip() or "Unknown"
        selected_ts = viewer._ensure_text(selected_parsed.timestamp if selected_parsed else "").strip() or "Unknown"
        selected_qty = int(selected_parsed.quantity) if selected_parsed is not None else 1
        if selected_qty < 1:
            selected_qty = 1
        selected_rarity = (
            viewer._ensure_text(selected_parsed.rarity if selected_parsed else "").strip()
            or viewer._ensure_text(stats.get("rarity", "Unknown")).strip()
            or "Unknown"
        )
        rarity_color = viewer._get_rarity_color(selected_rarity)
        pyimgui.text_colored(f"Selected Entry: {selected_char} | {selected_map} | {selected_ts}", rarity_color)
        pyimgui.text_colored(f"Selected Qty: {selected_qty}", rarity_color)
        stats_text = viewer._get_row_stats_text(active_log_row)
        if stats_text:
            pyimgui.separator()
            pyimgui.text_colored("Item Mods / Stats", rarity_color)
            for line in stats_text.splitlines():
                line_txt = viewer._ensure_text(line).strip()
                if line_txt:
                    pyimgui.text_colored(line_txt, rarity_color)
        else:
            pyimgui.text_colored("No detailed mod stats available for this row.", (0.78, 0.78, 0.78, 1.0))
        if viewer.debug_item_stats_panel:
            debug_lines = viewer._build_selected_row_debug_lines(active_log_row)
            pyimgui.separator()
            pyimgui.text_colored("Debug Item Pipeline", (0.95, 0.78, 0.38, 1.0))
            if viewer._styled_button("Copy Debug", "secondary", tooltip="Copy debug pipeline text to clipboard."):
                try:
                    pyimgui.set_clipboard_text("\n".join(debug_lines))
                    viewer.set_status("Debug pipeline copied to clipboard")
                except EXPECTED_RUNTIME_ERRORS as e:
                    viewer.set_status(f"Clipboard copy failed: {e}")
            if pyimgui.begin_child(
                "DropTrackerItemDebugPanel",
                size=(0.0, float(viewer.debug_item_stats_panel_height)),
                border=True,
                flags=pyimgui.WindowFlags.HorizontalScrollbar,
            ):
                for line in debug_lines:
                    pyimgui.text(viewer._ensure_text(line))
            pyimgui.end_child()

    flags = pyimgui.TableFlags.Borders | pyimgui.TableFlags.RowBg | pyimgui.TableFlags.SizingStretchProp
    if pyimgui.begin_table("DropTrackerSelectedItemCharacters", 3, flags, 0.0, 150.0):
        pyimgui.table_setup_column("Character")
        pyimgui.table_setup_column("Qty")
        pyimgui.table_setup_column("Drops")
        pyimgui.table_headers_row()

        selected_char_name = ""
        if active_log_row and viewer._row_matches_selected_item(active_log_row, active_item_key):
            selected_parsed = viewer._parse_drop_row(active_log_row)
            selected_char_name = viewer._ensure_text(selected_parsed.player_name if selected_parsed else "").strip().lower()

        for char_idx, (character, char_stats) in enumerate(stats["characters"]):
            pyimgui.table_next_row()
            pyimgui.table_set_column_index(0)
            row_is_selected = bool(selected_char_name and selected_char_name == viewer._ensure_text(character).strip().lower())
            if pyimgui.selectable(
                f"{character}##char_pick_{char_idx}",
                row_is_selected,
                pyimgui.SelectableFlags.NoFlag,
                (0.0, 0.0),
            ):
                target_row = viewer._find_best_row_for_item_and_character(stats["name"], stats["rarity"], character)
                if target_row is not None:
                    viewer.selected_log_row = target_row
            if pyimgui.is_item_hovered():
                imgui.show_tooltip("Click to view this character's item stats.")
            pyimgui.table_set_column_index(1)
            pyimgui.text(str(char_stats["Quantity"]))
            pyimgui.table_set_column_index(2)
            pyimgui.text(str(char_stats["Count"]))
        pyimgui.end_table()


def collect_live_status_snapshot(viewer):
    player_api = _runtime_attr(viewer, "Player")
    party_api = _runtime_attr(viewer, "Party")
    global_cache = _runtime_attr(viewer, "GLOBAL_CACHE")
    map_api = _runtime_attr(viewer, "Map")

    is_leader = False
    party_size = 0
    map_id = 0
    map_name = "Unknown"

    try:
        is_leader = bool(player_api.GetAgentID() == party_api.GetPartyLeaderID())
    except EXPECTED_RUNTIME_ERRORS:
        is_leader = False

    try:
        party_size = max(0, int(global_cache.Party.GetPartySize()))
    except EXPECTED_RUNTIME_ERRORS:
        party_size = 0
    if party_size <= 0:
        try:
            players = global_cache.Party.GetPlayers() or []
            heroes = global_cache.Party.GetHeroes() or []
            henchmen = global_cache.Party.GetHenchmen() or []
            party_size = max(0, len(players) + len(heroes) + len(henchmen))
        except EXPECTED_RUNTIME_ERRORS:
            party_size = 0

    try:
        map_id = max(0, int(map_api.GetMapID()))
    except EXPECTED_RUNTIME_ERRORS:
        map_id = 0
    try:
        if map_id > 0:
            map_name = viewer._ensure_text(map_api.GetMapName(map_id)).strip() or "Unknown"
    except EXPECTED_RUNTIME_ERRORS:
        map_name = "Unknown"

    display_map_name = map_name
    if len(display_map_name) > 20:
        display_map_name = f"{display_map_name[:17]}..."

    return {
        "is_leader": bool(is_leader),
        "party_size": int(party_size),
        "map_id": int(map_id),
        "map_name": map_name,
        "display_map_name": display_map_name,
    }


def draw_top_control_strip(viewer):
    pyimgui = _runtime_attr(viewer, "PyImGui")
    c = viewer._ui_colors()
    viewer._draw_section_header("Quick Control")
    pyimgui.push_style_color(pyimgui.ImGuiCol.ChildBg, c["panel_bg"])
    pyimgui.push_style_color(pyimgui.ImGuiCol.Border, (0.28, 0.35, 0.43, 0.72))
    if pyimgui.begin_child("DropTrackerQuickControlStrip", size=(0, 66), border=True, flags=pyimgui.WindowFlags.NoScrollbar):
        action_gap = 8.0
        action_h = 32.0
        action_row_w = max(180.0, float(pyimgui.get_content_region_avail()[0]))
        action_w = max(110.0, (action_row_w - (action_gap * 2.0)) / 3.0)
        inline = action_w >= 118.0
        button_w = action_w if inline else action_row_w

        if viewer._styled_button(
            "Resign + Outpost",
            "danger",
            width=button_w,
            height=action_h,
            tooltip="Resign all party clients and return to outpost.",
        ):
            viewer._trigger_party_resign_to_outpost()
        if inline:
            pyimgui.same_line(0.0, action_gap)

        if viewer._styled_button(
            "Join Followers",
            "warning",
            width=button_w,
            height=action_h,
            tooltip="Invite all eligible followers in the current map.",
        ):
            viewer._trigger_party_invite_all_followers()
        if inline:
            pyimgui.same_line(0.0, action_gap)

        if viewer._styled_button(
            "Resume Tracking" if viewer.paused else "Pause Tracking",
            "success" if viewer.paused else "warning",
            width=button_w,
            height=action_h,
            tooltip="Pause or resume local drop tracking updates.",
        ):
            viewer._set_paused(not viewer.paused)
    pyimgui.end_child()
    pyimgui.pop_style_color(2)


def draw_live_status_chips(viewer):
    pyimgui = _runtime_attr(viewer, "PyImGui")
    c = viewer._ui_colors()
    snapshot = collect_live_status_snapshot(viewer)
    chips = [
        (f"Role: {'Leader' if snapshot['is_leader'] else 'Follower'}", "success" if snapshot["is_leader"] else "secondary", "Leader can broadcast actions to followers."),
        (f"Map: {snapshot['map_id']} {snapshot['display_map_name']}", "primary", f"Current map: {snapshot['map_name']} ({snapshot['map_id']})"),
        (f"Party: {snapshot['party_size']}", "secondary", "Current full party size (players + heroes + henchmen)."),
        (f"Auto ID: {'ON' if viewer.auto_id_enabled else 'OFF'}", "success" if viewer.auto_id_enabled else "secondary", "Auto ID loop status."),
        (f"Auto Salv: {'ON' if viewer.auto_salvage_enabled else 'OFF'}", "success" if viewer.auto_salvage_enabled else "secondary", "Auto Salvage loop status."),
        (f"Auto Kits: {'ON' if viewer.auto_buy_kits_enabled else 'OFF'}", "success" if viewer.auto_buy_kits_enabled else "secondary", "Auto buy kits loop status."),
        (f"Inv Sort: {'ON' if viewer.auto_buy_kits_sort_to_front_enabled else 'OFF'}", "success" if viewer.auto_buy_kits_sort_to_front_enabled else "secondary", "Outpost-entry inventory reorder status."),
        (f"Auto Gold: {'ON' if viewer.auto_gold_balance_enabled else 'OFF'}", "success" if viewer.auto_gold_balance_enabled else "secondary", f"Auto keep {int(viewer.auto_gold_balance_target)}g on character in outpost."),
    ]

    viewer._draw_section_header("Live Status")
    pyimgui.push_style_color(pyimgui.ImGuiCol.ChildBg, c["panel_bg"])
    pyimgui.push_style_color(pyimgui.ImGuiCol.Border, (0.28, 0.35, 0.43, 0.72))
    if pyimgui.begin_child("DropTrackerLiveStatusStrip", size=(0, 70), border=True, flags=pyimgui.WindowFlags.NoScrollbar):
        for idx, (label, variant, tooltip) in enumerate(chips):
            viewer._draw_status_chip(label, variant, tooltip=tooltip)
            if idx < (len(chips) - 1):
                remaining_w = max(0.0, float(pyimgui.get_content_region_avail()[0]))
                if remaining_w > 130.0:
                    pyimgui.same_line(0.0, 6.0)
    pyimgui.end_child()
    pyimgui.pop_style_color(2)


def format_elapsed_since(viewer, timestamp_value: float) -> str:
    ts = float(timestamp_value or 0.0)
    if ts <= 0:
        return "never"
    elapsed = max(0, int(time.time() - ts))
    if elapsed < 60:
        return f"{elapsed}s ago"
    if elapsed < 3600:
        mins = elapsed // 60
        secs = elapsed % 60
        return f"{mins}m {secs:02d}s"
    hours = elapsed // 3600
    mins = (elapsed % 3600) // 60
    return f"{hours}h {mins:02d}m"


def draw_auto_inventory_activity(viewer):
    pyimgui = _runtime_attr(viewer, "PyImGui")
    imgui = _runtime_attr(viewer, "ImGui")
    c = viewer._ui_colors()
    viewer._refresh_auto_inventory_pending_counts()
    viewer._draw_section_header("Queue Activity")
    pyimgui.push_style_color(pyimgui.ImGuiCol.ChildBg, c["panel_bg"])
    pyimgui.push_style_color(pyimgui.ImGuiCol.Border, (0.28, 0.35, 0.43, 0.72))
    if pyimgui.begin_child("DropTrackerAutoQueueActivity", size=(0, 106), border=True, flags=pyimgui.WindowFlags.NoScrollbar):
        width = max(110.0, float(pyimgui.get_content_region_avail()[0]))
        cap = max(1, int(viewer.auto_queue_progress_cap))
        id_pending = max(0, int(viewer.auto_id_pending_jobs))
        salvage_pending = max(0, int(viewer.auto_salvage_pending_jobs))
        id_progress = min(1.0, float(id_pending) / float(cap))
        salvage_progress = min(1.0, float(salvage_pending) / float(cap))

        pyimgui.text_colored(
            f"ID: pending {id_pending}, last run {format_elapsed_since(viewer, viewer.auto_id_last_run_ts)}",
            c["muted"],
        )
        pyimgui.progress_bar(id_progress, width, f"{id_pending} queued")
        if pyimgui.is_item_hovered():
            imgui.show_tooltip(
                f"Last queued: {int(viewer.auto_id_last_queued)}\n"
                f"Total queued this session: {int(viewer.auto_id_total_queued)}"
            )

        pyimgui.text_colored(
            f"Salvage: pending {salvage_pending}, last run {format_elapsed_since(viewer, viewer.auto_salvage_last_run_ts)}",
            c["muted"],
        )
        pyimgui.progress_bar(salvage_progress, width, f"{salvage_pending} queued")
        if pyimgui.is_item_hovered():
            imgui.show_tooltip(
                f"Last queued: {int(viewer.auto_salvage_last_queued)}\n"
                f"Total queued this session: {int(viewer.auto_salvage_total_queued)}"
            )
    pyimgui.end_child()
    pyimgui.pop_style_color(2)


def draw_view_and_theme_controls(viewer):
    pyimgui = _runtime_attr(viewer, "PyImGui")
    c = viewer._ui_colors()
    viewer._draw_section_header("View")
    pyimgui.push_style_color(pyimgui.ImGuiCol.ChildBg, c["panel_bg"])
    pyimgui.push_style_color(pyimgui.ImGuiCol.Border, (0.28, 0.35, 0.43, 0.72))
    if pyimgui.begin_child("DropTrackerViewCard", size=(0, 98), border=True, flags=pyimgui.WindowFlags.NoScrollbar):
        width = max(120.0, float(pyimgui.get_content_region_avail()[0]))
        if viewer._styled_button(
            f"Compact Mode: {'ON' if viewer.compact_mode else 'OFF'}",
            "success" if viewer.compact_mode else "secondary",
            width=width,
            height=28.0,
            tooltip="Hide advanced settings and show only core controls in the left panel.",
        ):
            viewer.compact_mode = not viewer.compact_mode
            if viewer.compact_mode:
                viewer.show_runtime_panel = False
            viewer.runtime_config_dirty = True

        pyimgui.text_colored("Theme Preset", c["muted"])
        theme_names = viewer._theme_names()
        current_theme_idx = 0
        try:
            current_theme_idx = max(0, theme_names.index(viewer.ui_theme_name))
        except EXPECTED_RUNTIME_ERRORS:
            current_theme_idx = 0
        next_theme_idx = int(pyimgui.combo("##DropTrackerThemePreset", current_theme_idx, theme_names))
        if 0 <= next_theme_idx < len(theme_names) and next_theme_idx != current_theme_idx:
            viewer.ui_theme_name = theme_names[next_theme_idx]
            viewer.runtime_config_dirty = True
    pyimgui.end_child()
    pyimgui.pop_style_color(2)


def draw_inventory_action_cards(viewer):
    pyimgui = _runtime_attr(viewer, "PyImGui")
    c = viewer._ui_colors()
    pyimgui.push_style_color(pyimgui.ImGuiCol.ChildBg, c["panel_bg"])
    pyimgui.push_style_color(pyimgui.ImGuiCol.Border, (0.28, 0.35, 0.43, 0.72))
    if pyimgui.begin_child("DropTrackerInventoryActionCards", size=(0, 224), border=True, flags=pyimgui.WindowFlags.NoScrollbar):
        cards = [
            {"label": f"[ID] Auto {'ON' if viewer.auto_id_enabled else 'OFF'}", "variant": "success" if viewer.auto_id_enabled else "secondary", "tooltip": "Auto ID Loop: enable/disable periodic identify using ID settings.", "action": "toggle_auto_id"},
            {"label": f"[SV] Auto {'ON' if viewer.auto_salvage_enabled else 'OFF'}", "variant": "success" if viewer.auto_salvage_enabled else "secondary", "tooltip": "Auto Salvage Loop: enable/disable periodic salvage using Salvage settings.", "action": "toggle_auto_salvage"},
            {"label": f"[ST] Outpost {'ON' if viewer.auto_outpost_store_enabled else 'OFF'}", "variant": "success" if viewer.auto_outpost_store_enabled else "secondary", "tooltip": "Auto Store in Outpost: deposit Materials + Tomes (including Elite Tomes) on outpost entry.", "action": "toggle_auto_outpost_store"},
            {"label": "[CFG] Sync", "variant": "secondary", "tooltip": "Sync Config -> Followers: push auto ID/salvage/outpost-store settings.", "action": "sync_config"},
            {"label": f"[CH] Chest {'ON' if viewer._get_party_chesting_enabled() else 'OFF'}", "variant": "success" if viewer._get_party_chesting_enabled() else "secondary", "tooltip": "Party chesting toggle (leader): enable/disable chesting for all members including leader.", "action": "toggle_party_chesting"},
            {"label": "[IT] Interact Leader Target", "variant": "primary", "tooltip": "Ask all party members (including leader) to interact with the leader-selected target.", "action": "interact_leader_target"},
            {"label": f"[KT] Auto {'ON' if viewer.auto_buy_kits_enabled else 'OFF'}", "variant": "success" if viewer.auto_buy_kits_enabled else "secondary", "tooltip": "Auto Buy Kits: while in outpost, periodically buy kits if uses are below threshold.", "action": "toggle_auto_buy_kits"},
            {"label": f"[KS] Sort {'ON' if viewer.auto_buy_kits_sort_to_front_enabled else 'OFF'}", "variant": "success" if viewer.auto_buy_kits_sort_to_front_enabled else "secondary", "tooltip": "Outpost entry: kits to front, then followers reorder non-kits by rarity/type priority.", "action": "toggle_auto_buy_kits_sort"},
            {"label": f"[GD] Auto {'ON' if viewer.auto_gold_balance_enabled else 'OFF'}", "variant": "success" if viewer.auto_gold_balance_enabled else "secondary", "tooltip": f"Auto Gold Balance: keep {int(viewer.auto_gold_balance_target)} gold on character in outpost.", "action": "toggle_auto_gold_balance"},
            {"label": "[DBG] Merch Dump", "variant": "secondary", "tooltip": "Temporary debug: dump full merchant scan report to file and clipboard.", "action": "dump_merchant_debug"},
        ]

        gap = 8.0
        avail_w = max(140.0, float(pyimgui.get_content_region_avail()[0]))
        half_w = max(110.0, (avail_w - gap) * 0.5)

        def _run_card_action(action_code: str):
            if action_code == "toggle_auto_id":
                next_id_enabled = not viewer.auto_id_enabled
                id_payload = viewer._encode_auto_action_payload(next_id_enabled, viewer._get_selected_id_rarities())
                viewer._trigger_inventory_action("cfg_auto_id", id_payload)
            elif action_code == "toggle_auto_salvage":
                next_salvage_enabled = not viewer.auto_salvage_enabled
                salvage_payload = viewer._encode_auto_action_payload(next_salvage_enabled, viewer._get_selected_salvage_rarities())
                viewer._trigger_inventory_action("cfg_auto_salvage", salvage_payload)
            elif action_code == "toggle_auto_outpost_store":
                next_store_enabled = not viewer.auto_outpost_store_enabled
                store_payload = "1" if next_store_enabled else "0"
                viewer._trigger_inventory_action("cfg_auto_outpost_store", store_payload)
            elif action_code == "toggle_auto_buy_kits":
                next_kits_enabled = not viewer.auto_buy_kits_enabled
                kits_payload = "1" if next_kits_enabled else "0"
                viewer._trigger_inventory_action("cfg_auto_buy_kits", kits_payload)
            elif action_code == "toggle_auto_buy_kits_sort":
                next_sort_enabled = not viewer.auto_buy_kits_sort_to_front_enabled
                sort_payload = "1" if next_sort_enabled else "0"
                viewer._trigger_inventory_action("cfg_auto_buy_kits_sort", sort_payload)
            elif action_code == "toggle_auto_gold_balance":
                next_gold_enabled = not viewer.auto_gold_balance_enabled
                gold_payload = "1" if next_gold_enabled else "0"
                viewer._trigger_inventory_action("cfg_auto_gold_balance", gold_payload)
            elif action_code == "sync_config":
                viewer._sync_auto_inventory_config_to_followers()
            elif action_code == "toggle_party_chesting":
                viewer._toggle_party_chesting()
            elif action_code == "interact_leader_target":
                viewer._trigger_party_interact_leader_target()
            elif action_code == "run_id_now":
                viewer._trigger_inventory_action("id_selected", viewer._encode_rarities(viewer._get_selected_id_rarities()))
            elif action_code == "run_salvage_now":
                viewer._trigger_inventory_action("salvage_selected", viewer._encode_rarities(viewer._get_selected_salvage_rarities()))
            elif action_code == "dump_merchant_debug":
                viewer._dump_auto_buy_kits_merchant_debug_report()

        for row_idx in range(0, len(cards), 2):
            left_card = cards[row_idx]
            right_card = cards[row_idx + 1] if (row_idx + 1) < len(cards) else None

            if viewer._styled_button(left_card["label"], left_card["variant"], width=half_w, height=30.0, tooltip=left_card["tooltip"]):
                _run_card_action(left_card["action"])
            if right_card is not None:
                pyimgui.same_line(0.0, gap)
                if viewer._styled_button(right_card["label"], right_card["variant"], width=half_w, height=30.0, tooltip=right_card["tooltip"]):
                    _run_card_action(right_card["action"])
    pyimgui.end_child()
    pyimgui.pop_style_color(2)


def status_color(viewer, msg: str):
    txt = viewer._ensure_text(msg).lower()
    if "fail" in txt or "error" in txt:
        return (1.0, 0.46, 0.42, 1.0)
    if "warn" in txt:
        return (1.0, 0.80, 0.34, 1.0)
    return (0.40, 0.95, 0.56, 1.0)


def draw_status_toast(viewer, message: str):
    pyimgui = _runtime_attr(viewer, "PyImGui")
    msg = viewer._ensure_text(message).strip()
    if not msg:
        return
    col = status_color(viewer, msg)
    pyimgui.push_style_color(pyimgui.ImGuiCol.ChildBg, (col[0] * 0.22, col[1] * 0.22, col[2] * 0.22, 0.96))
    pyimgui.push_style_color(pyimgui.ImGuiCol.Border, (col[0], col[1], col[2], 0.95))
    if pyimgui.begin_child("DropTrackerStatusToast", size=(0, 28), border=True, flags=pyimgui.WindowFlags.NoScrollbar):
        pyimgui.text_colored(msg, col)
    pyimgui.end_child()
    pyimgui.pop_style_color(2)


def draw_rarity_chips(viewer, prefix: str, rarities: list[str]):
    pyimgui = _runtime_attr(viewer, "PyImGui")
    c = viewer._ui_colors()
    pyimgui.text_colored(prefix, c["muted"])
    if not rarities:
        pyimgui.same_line(0.0, 6.0)
        pyimgui.text_colored("[None]", c["muted"])
        return
    for idx, rarity in enumerate(rarities):
        pyimgui.same_line(0.0, 6.0)
        r, g, b, a = viewer._get_rarity_color(rarity)
        pyimgui.text_colored(f"[{rarity}]", (r, g, b, a))
        if idx >= 6:
            pyimgui.same_line(0.0, 6.0)
            pyimgui.text_colored("...", c["muted"])
            break


def draw_metric_card(viewer, card_id, title, value, accent_color):
    pyimgui = _runtime_attr(viewer, "PyImGui")
    c = viewer._ui_colors()
    pyimgui.push_style_color(pyimgui.ImGuiCol.ChildBg, c["panel_bg"])
    pyimgui.push_style_color(pyimgui.ImGuiCol.Border, (0.28, 0.35, 0.43, 0.72))
    if pyimgui.begin_child(card_id, size=(0, 52), border=True, flags=pyimgui.WindowFlags.NoFlag):
        pyimgui.text_colored(title, accent_color)
        pyimgui.text_colored(value, (0.94, 0.96, 1.0, 1.0))
    pyimgui.end_child()
    pyimgui.pop_style_color(2)


def draw_summary_bar(viewer, filtered_rows):
    pyimgui = _runtime_attr(viewer, "PyImGui")
    total_qty_without_gold = 0
    rare_count = 0
    gold_qty = 0
    for row in filtered_rows:
        parsed = viewer._parse_drop_row(row)
        if parsed is None:
            continue
        qty = int(parsed.quantity)
        rarity = viewer._ensure_text(parsed.rarity).strip() or "Unknown"
        if viewer._is_rare_rarity(rarity):
            rare_count += 1
        if viewer._is_gold_row(row):
            gold_qty += qty
        elif rarity == "Material":
            continue
        else:
            total_qty_without_gold += qty

    session_time = viewer._get_session_duration_text()
    c = viewer._ui_colors()
    pyimgui.text_colored("Session Snapshot", c["accent"])
    flags = pyimgui.TableFlags.SizingStretchSame
    if pyimgui.begin_table("DropViewerSummary", 4, flags):
        pyimgui.table_next_row()
        pyimgui.table_set_column_index(0)
        draw_metric_card(viewer, "CardSession", "Session", session_time, (0.55, 0.85, 1.0, 1.0))
        pyimgui.table_set_column_index(1)
        draw_metric_card(viewer, "CardDrops", "Total Drops", str(total_qty_without_gold), (0.8, 0.9, 1.0, 1.0))
        pyimgui.table_set_column_index(2)
        draw_metric_card(viewer, "CardGold", "Gold Value", f"{gold_qty:,}", (0.72, 0.72, 0.72, 1.0))
        pyimgui.table_set_column_index(3)
        draw_metric_card(viewer, "CardRare", "Rare Drops", str(rare_count), (1.0, 0.84, 0.0, 1.0))
        pyimgui.end_table()
