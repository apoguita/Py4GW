import sys


def _viewer_runtime_module(viewer):
    try:
        return sys.modules.get(viewer.__class__.__module__)
    except (TypeError, ValueError, RuntimeError, AttributeError):
        return None


def _runtime_attr(viewer, name: str, fallback=None):
    module = _viewer_runtime_module(viewer)
    if module is not None and hasattr(module, name):
        return getattr(module, name)
    return fallback


def _build_item_hover_tooltip_text(viewer, row, fallback_item_name: str = "") -> str:
    fallback_name = viewer._clean_item_name(fallback_item_name)
    if row is not None:
        stats_text = viewer._ensure_text(viewer._get_row_stats_text(row)).strip()
        if stats_text:
            return stats_text
        parsed = viewer._parse_drop_row(row)
        if parsed is not None:
            parsed_name = viewer._clean_item_name(getattr(parsed, "item_name", ""))
            if parsed_name:
                fallback_name = parsed_name
    if fallback_name:
        return f"{fallback_name}\nNo stats available yet."
    return "No stats available yet."


def draw_aggregated(viewer, filtered_rows, materials_only: bool = False) -> None:
    pyimgui = _runtime_attr(viewer, "PyImGui")
    imgui = _runtime_attr(viewer, "ImGui")
    c = viewer._ui_colors()
    filtered_agg, total_filtered_qty = viewer._get_filtered_aggregated(filtered_rows)
    if materials_only:
        filtered_agg = {
            (name, rarity): data
            for (name, rarity), data in filtered_agg.items()
            if viewer._ensure_text(rarity).strip() == "Material"
        }
    else:
        filtered_agg = {
            (name, rarity): data
            for (name, rarity), data in filtered_agg.items()
            if viewer._ensure_text(rarity).strip() != "Material"
        }
    total_filtered_qty = sum(data["Quantity"] for data in filtered_agg.values())
    total_filtered_events = sum(data["Count"] for data in filtered_agg.values())
    total_items_without_gold = total_filtered_qty - sum(
        data["Quantity"] for (name, _), data in filtered_agg.items() if name == "Gold"
    )
    total_events_without_gold = total_filtered_events - sum(
        data["Count"] for (name, _), data in filtered_agg.items() if name == "Gold"
    )

    if materials_only:
        pyimgui.text_colored(
            f"Total Materials (filtered): {max(0, total_items_without_gold)} | Events: {max(0, total_events_without_gold)}",
            c["muted"],
        )
    else:
        pyimgui.text_colored(
            f"Total Items (filtered): {max(0, total_items_without_gold)} | Events: {max(0, total_events_without_gold)}",
            c["muted"],
        )
        pyimgui.same_line(0.0, 12.0)
        viewer._draw_inline_rarity_filter_buttons()
    if not filtered_agg:
        pyimgui.separator()
        if materials_only:
            pyimgui.text_colored("No material drops match your current filters.", c["muted"])
            pyimgui.text("Try clearing filters or switching to Stats/Log tab.")
        else:
            pyimgui.text_colored("No drops match your current filters.", c["muted"])
            pyimgui.text("Try clearing filters or switching to Log tab.")
        return

    pyimgui.push_style_color(pyimgui.ImGuiCol.TableHeaderBg, (0.16, 0.20, 0.27, 0.95))
    if pyimgui.begin_table(
        f"AggTable##{int(viewer._agg_table_reset_nonce)}",
        5,
        pyimgui.TableFlags.Borders | pyimgui.TableFlags.RowBg | pyimgui.TableFlags.Resizable | pyimgui.TableFlags.Sortable | pyimgui.TableFlags.ScrollY,
        0.0,
        360.0,
    ):
        pyimgui.table_setup_column("Item Name")
        pyimgui.table_setup_column("Quantity")
        pyimgui.table_setup_column("%")
        pyimgui.table_setup_column("Rarity")
        pyimgui.table_setup_column("Count")
        pyimgui.table_headers_row()

        display_items = list(filtered_agg.items())
        sorted_items = sorted(display_items, key=lambda x: (x[0][0], x[0][1]))

        for idx, ((item_name, rarity), data) in enumerate(sorted_items):
            pyimgui.table_next_row()
            qty = data["Quantity"]
            if item_name == "Gold":
                pct_str = "---"
            else:
                pct = (qty / total_items_without_gold * 100) if total_items_without_gold > 0 else 0
                pct_str = f"{pct:.2f}%"

            r, g, b, a = viewer._get_rarity_color(rarity)
            row_key = (item_name, rarity)

            pyimgui.table_set_column_index(0)
            pyimgui.push_style_color(pyimgui.ImGuiCol.Text, (r, g, b, a))
            if pyimgui.selectable(
                f"{item_name}##agg_{idx}",
                viewer.selected_item_key == row_key,
                pyimgui.SelectableFlags.NoFlag,
                (0.0, 0.0),
            ):
                viewer.selected_item_key = row_key
                viewer.selected_log_row = viewer._find_best_row_for_item(item_name, rarity, filtered_rows)
            if pyimgui.is_item_clicked(1):
                pyimgui.open_popup(f"DropAggRowMenu##{idx}")
            if pyimgui.begin_popup(f"DropAggRowMenu##{idx}"):
                target_row = viewer._find_best_row_for_item(item_name, rarity, filtered_rows)
                if target_row is None:
                    pyimgui.text("No concrete row available")
                else:
                    viewer.selected_item_key = row_key
                    viewer.selected_log_row = target_row
                    if pyimgui.menu_item("Identify item"):
                        viewer._identify_item_for_all_characters(item_name, rarity)
                pyimgui.end_popup()
            if pyimgui.is_item_hovered():
                hover_row = viewer._find_best_row_for_item(item_name, rarity, filtered_rows)
                viewer._set_hover_item_preview(
                    row_key,
                    hover_row,
                )
                imgui.show_tooltip(_build_item_hover_tooltip_text(viewer, hover_row, item_name))
            pyimgui.pop_style_color(1)

            pyimgui.table_set_column_index(1)
            pyimgui.text(str(qty))

            pyimgui.table_set_column_index(2)
            pyimgui.text(pct_str)

            pyimgui.table_set_column_index(3)
            pyimgui.text_colored(rarity, (r, g, b, a))

            pyimgui.table_set_column_index(4)
            pyimgui.text(str(data["Count"]))

        if viewer._request_agg_scroll_bottom:
            pyimgui.set_scroll_here_y(1.0)
            viewer._request_agg_scroll_bottom = False

        pyimgui.end_table()
    pyimgui.pop_style_color(1)
    viewer._draw_selected_item_details()


def draw_log(viewer, filtered_rows) -> None:
    pyimgui = _runtime_attr(viewer, "PyImGui")
    imgui = _runtime_attr(viewer, "ImGui")
    c = viewer._ui_colors()
    viewer._draw_inline_rarity_filter_buttons()
    pyimgui.separator()
    if not filtered_rows:
        pyimgui.text_colored("No log entries to show.", c["muted"])
        pyimgui.text("Drops will appear here as they are tracked.")
        return

    pyimgui.push_style_color(pyimgui.ImGuiCol.TableHeaderBg, (0.16, 0.20, 0.27, 0.95))
    if pyimgui.begin_table(
        f"DropsLogTable##{int(viewer._log_table_reset_nonce)}",
        8,
        pyimgui.TableFlags.Borders | pyimgui.TableFlags.RowBg | pyimgui.TableFlags.Resizable | pyimgui.TableFlags.ScrollY,
        0.0,
        0.0,
    ):
        pyimgui.table_setup_column("Timestamp")
        pyimgui.table_setup_column("Logger")
        pyimgui.table_setup_column("MapID")
        pyimgui.table_setup_column("MapName")
        pyimgui.table_setup_column("Player")
        pyimgui.table_setup_column("Item")
        pyimgui.table_setup_column("Qty")
        pyimgui.table_setup_column("Rarity")
        pyimgui.table_headers_row()

        for row_idx, row in enumerate(filtered_rows):
            pyimgui.table_next_row()
            parsed = viewer._parse_drop_row(row)
            if parsed is None:
                continue
            rarity = viewer._ensure_text(parsed.rarity).strip() or "Unknown"
            r, g, b, a = viewer._get_rarity_color(rarity)
            selected_key = (
                viewer._canonical_agg_item_name(parsed.item_name, rarity, viewer.aggregated_drops),
                viewer._ensure_text(rarity).strip() or "Unknown",
            )

            for i, col in enumerate(row):
                if i >= 8:
                    break
                pyimgui.table_set_column_index(i)

                if i == 5:
                    pyimgui.push_style_color(pyimgui.ImGuiCol.Text, (r, g, b, a))
                    if pyimgui.selectable(
                        f"{str(col)}##log_item_{row_idx}",
                        viewer.selected_item_key == selected_key,
                        pyimgui.SelectableFlags.NoFlag,
                        (0.0, 0.0),
                    ):
                        viewer.selected_item_key = selected_key
                        viewer.selected_log_row = row
                    if pyimgui.is_item_clicked(1):
                        pyimgui.open_popup(f"DropLogRowMenu##{row_idx}")
                    if pyimgui.begin_popup(f"DropLogRowMenu##{row_idx}"):
                        if pyimgui.menu_item("Identify item"):
                            viewer._identify_item_for_all_characters(parsed.item_name, rarity)
                        pyimgui.end_popup()
                    if pyimgui.is_item_hovered():
                        viewer._set_hover_item_preview(selected_key, row)
                        imgui.show_tooltip(_build_item_hover_tooltip_text(viewer, row, parsed.item_name))
                    pyimgui.pop_style_color(1)
                elif i == 7:
                    pyimgui.text_colored(str(col), (r, g, b, a))
                elif i == 4:
                    pyimgui.text(
                        viewer._display_player_name(
                            viewer._ensure_text(parsed.player_name).strip(),
                            viewer._extract_row_sender_email(row),
                        )
                    )
                else:
                    pyimgui.text(str(col))

        log_scroll_to_bottom = False
        current_total = int(viewer.total_drops)
        if not viewer._log_autoscroll_initialized:
            viewer._log_autoscroll_initialized = True
        elif viewer.auto_scroll and current_total > int(viewer._last_log_autoscroll_total_drops):
            log_scroll_to_bottom = True
        viewer._last_log_autoscroll_total_drops = current_total

        if viewer._request_log_scroll_bottom:
            log_scroll_to_bottom = True
            viewer._request_log_scroll_bottom = False

        if log_scroll_to_bottom:
            pyimgui.set_scroll_here_y(1.0)

        pyimgui.end_table()
    pyimgui.pop_style_color(1)
    viewer._draw_selected_item_details()
