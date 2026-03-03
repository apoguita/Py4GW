from Py4GWCoreLib import Map


def get_selected_id_rarities(viewer):
    rarities = []
    if viewer.id_sel_white:
        rarities.append("White")
    if viewer.id_sel_blue:
        rarities.append("Blue")
    if viewer.id_sel_green:
        rarities.append("Green")
    if viewer.id_sel_purple:
        rarities.append("Purple")
    if viewer.id_sel_gold:
        rarities.append("Gold")
    return rarities


def get_selected_salvage_rarities(viewer):
    rarities = []
    if viewer.salvage_sel_white:
        rarities.append("White")
    if viewer.salvage_sel_blue:
        rarities.append("Blue")
    if viewer.salvage_sel_green:
        rarities.append("Green")
    if viewer.salvage_sel_purple:
        rarities.append("Purple")
    if viewer.salvage_sel_gold:
        rarities.append("Gold")
    return rarities


def encode_rarities(viewer, rarities):
    return ",".join(
        viewer._ensure_text(r).strip()
        for r in list(rarities or [])
        if viewer._ensure_text(r).strip()
    )


def decode_rarities(viewer, payload):
    return [part.strip() for part in viewer._ensure_text(payload).split(",") if part.strip()]


def apply_selected_id_rarities(viewer, rarities):
    selected = set(decode_rarities(viewer, encode_rarities(viewer, rarities)))
    viewer.id_sel_white = "White" in selected
    viewer.id_sel_blue = "Blue" in selected
    viewer.id_sel_green = "Green" in selected
    viewer.id_sel_purple = "Purple" in selected
    viewer.id_sel_gold = "Gold" in selected


def apply_selected_salvage_rarities(viewer, rarities):
    selected = set(decode_rarities(viewer, encode_rarities(viewer, rarities)))
    viewer.salvage_sel_white = "White" in selected
    viewer.salvage_sel_blue = "Blue" in selected
    viewer.salvage_sel_green = "Green" in selected
    viewer.salvage_sel_purple = "Purple" in selected
    viewer.salvage_sel_gold = "Gold" in selected


def rarities_to_bitmask(viewer, rarities):
    bitmask = 0
    order = ["White", "Blue", "Green", "Purple", "Gold"]
    selected = set(decode_rarities(viewer, encode_rarities(viewer, rarities)))
    for idx, rarity in enumerate(order):
        if rarity in selected:
            bitmask |= 1 << idx
    return bitmask


def bitmask_to_rarities(_viewer, mask):
    order = ["White", "Blue", "Green", "Purple", "Gold"]
    resolved = []
    for idx, rarity in enumerate(order):
        if int(mask) & (1 << idx):
            resolved.append(rarity)
    return resolved


def encode_auto_action_payload(viewer, enabled: bool, rarities):
    return f"{1 if bool(enabled) else 0}:{rarities_to_bitmask(viewer, rarities)}"


def decode_auto_action_payload(viewer, payload, default_enabled: bool, default_rarities):
    text = viewer._ensure_text(payload).strip()
    enabled = bool(default_enabled)
    rarities = list(default_rarities or [])
    if not text:
        return enabled, rarities
    if ":" not in text:
        decoded_rarities = decode_rarities(viewer, text)
        return enabled, decoded_rarities if decoded_rarities else rarities
    left, right = text.split(":", 1)
    left_txt = left.strip()
    if left_txt in ("0", "1"):
        enabled = left_txt == "1"
    try:
        mask = int(right.strip())
    except (TypeError, ValueError, RuntimeError, AttributeError):
        mask = -1
    if mask >= 0:
        rarities = bitmask_to_rarities(viewer, mask)
    return enabled, rarities


def parse_toggle_payload(viewer, payload: str, fallback: bool = False) -> bool:
    txt = viewer._ensure_text(payload).strip().lower()
    if txt in ("1", "true", "on", "yes", "y", "enable", "enabled"):
        return True
    if txt in ("0", "false", "off", "no", "n", "disable", "disabled"):
        return False
    return bool(fallback)


def apply_auto_id_config_payload(viewer, payload):
    enabled, rarities = decode_auto_action_payload(
        viewer,
        payload,
        viewer.auto_id_enabled,
        get_selected_id_rarities(viewer),
    )
    viewer.auto_id_enabled = bool(enabled)
    apply_selected_id_rarities(viewer, rarities)
    viewer.runtime_config_dirty = True


def apply_auto_salvage_config_payload(viewer, payload):
    enabled, rarities = decode_auto_action_payload(
        viewer,
        payload,
        viewer.auto_salvage_enabled,
        get_selected_salvage_rarities(viewer),
    )
    viewer.auto_salvage_enabled = bool(enabled)
    apply_selected_salvage_rarities(viewer, rarities)
    viewer.runtime_config_dirty = True


def apply_auto_outpost_store_config_payload(viewer, payload: str):
    next_enabled = parse_toggle_payload(viewer, payload, viewer.auto_outpost_store_enabled)
    changed = bool(next_enabled) != bool(viewer.auto_outpost_store_enabled)
    viewer.auto_outpost_store_enabled = bool(next_enabled)
    if changed and viewer.auto_outpost_store_enabled:
        viewer.auto_outpost_store_handled_entry_key = ""
    viewer.runtime_config_dirty = True


def apply_auto_buy_kits_config_payload(viewer, payload: str):
    next_enabled = parse_toggle_payload(viewer, payload, viewer.auto_buy_kits_enabled)
    previous = bool(viewer.auto_buy_kits_enabled)
    viewer.auto_buy_kits_enabled = bool(next_enabled)
    if previous and (not viewer.auto_buy_kits_enabled):
        viewer.auto_buy_kits_abort_requested = True
        if viewer.auto_buy_kits_job_running:
            viewer._trace_auto_buy_kits("job: abort requested (feature toggled OFF)")
            viewer.set_status("Auto Buy Kits: abort requested")
    if (not previous) and viewer.auto_buy_kits_enabled:
        viewer.auto_buy_kits_abort_requested = False
    if (not previous) and viewer.auto_buy_kits_enabled and bool(Map.IsOutpost()):
        viewer.auto_buy_kits_handled_entry_key = ""
        viewer._run_auto_buy_kits_once_on_outpost_entry_tick()
    viewer.runtime_config_dirty = True


def apply_auto_buy_kits_sort_config_payload(viewer, payload: str):
    next_enabled = parse_toggle_payload(viewer, payload, viewer.auto_buy_kits_sort_to_front_enabled)
    previous = bool(viewer.auto_buy_kits_sort_to_front_enabled)
    viewer.auto_buy_kits_sort_to_front_enabled = bool(next_enabled)
    if (not previous) and viewer.auto_buy_kits_sort_to_front_enabled:
        viewer.auto_inventory_reorder_handled_entry_key = ""
    viewer.runtime_config_dirty = True


def apply_auto_gold_balance_config_payload(viewer, payload: str):
    txt = viewer._ensure_text(payload).strip()
    if not txt:
        return
    if ":" in txt:
        enabled_txt, target_txt = txt.split(":", 1)
        viewer.auto_gold_balance_enabled = parse_toggle_payload(
            viewer,
            enabled_txt,
            viewer.auto_gold_balance_enabled,
        )
        try:
            viewer.auto_gold_balance_target = max(0, int(target_txt.strip()))
        except (TypeError, ValueError, RuntimeError, AttributeError):
            pass
    else:
        viewer.auto_gold_balance_enabled = parse_toggle_payload(
            viewer,
            txt,
            viewer.auto_gold_balance_enabled,
        )
    viewer.runtime_config_dirty = True
