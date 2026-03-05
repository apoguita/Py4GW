from Sources.oazix.CustomBehaviors.skills.monitoring.drop_tracker_runtime_store import (
    rebuild_aggregates_from_runtime_rows,
)


def rebuild_aggregates_from_raw_drops(viewer) -> None:
    temp_agg, total = rebuild_aggregates_from_runtime_rows(
        raw_drops=viewer.raw_drops,
        parse_runtime_row_fn=viewer._parse_drop_row,
        canonical_name_fn=viewer._canonical_agg_item_name,
        safe_int_fn=viewer._safe_int,
        ensure_text_fn=viewer._ensure_text,
    )
    viewer.aggregated_drops = temp_agg
    viewer.total_drops = int(total)


def is_rare_rarity(_viewer, rarity):
    return rarity == "Gold"


def passes_filters(viewer, row):
    parsed = viewer._parse_drop_row(row)
    if parsed is None:
        return False

    player_name = viewer._display_player_name(parsed.player_name, getattr(parsed, "sender_email", ""))
    item_name = viewer._ensure_text(parsed.item_name)
    qty = int(parsed.quantity)
    rarity = viewer._ensure_text(parsed.rarity).strip() or "Unknown"
    map_name = viewer._ensure_text(parsed.map_name)

    if qty < max(1, int(viewer.min_qty)):
        return False
    if viewer.only_rare and not viewer._is_rare_rarity(rarity):
        return False
    if viewer.hide_gold and viewer._clean_item_name(item_name) == "Gold":
        return False
    if viewer.filter_rarity_idx > 0:
        wanted = viewer.filter_rarity_options[viewer.filter_rarity_idx]
        if wanted == "Unknown":
            if "Unknown" not in rarity:
                return False
        elif rarity != wanted:
            return False

    search = viewer.search_text.strip().lower()
    if search:
        haystack = f"{item_name} {player_name} {map_name} {rarity}".lower()
        if search not in haystack:
            return False

    fp = viewer.filter_player.strip().lower()
    if fp and fp not in player_name.lower():
        return False

    fm = viewer.filter_map.strip().lower()
    if fm and fm not in map_name.lower():
        return False

    return True


def get_filtered_rows(viewer):
    return [row for row in viewer.raw_drops if viewer._passes_filters(row)]


def is_gold_row(viewer, row):
    parsed = viewer._parse_drop_row(row)
    if parsed is None:
        return False
    return viewer._clean_item_name(parsed.item_name) == "Gold"


def get_filtered_aggregated(viewer, filtered_rows):
    agg = {}
    total_qty = 0
    for row in filtered_rows:
        parsed = viewer._parse_drop_row(row)
        if parsed is None:
            continue
        item_name = parsed.item_name
        rarity = parsed.rarity
        qty = int(parsed.quantity)
        total_qty += qty
        canonical_name = viewer._canonical_agg_item_name(item_name, rarity, agg)
        key = (canonical_name, rarity)
        if key not in agg:
            agg[key] = {"Quantity": 0, "Count": 0}
        agg[key]["Quantity"] += qty
        agg[key]["Count"] += 1
    return agg, total_qty
