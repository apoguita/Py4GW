import re
import time
from typing import Any

from Py4GWCoreLib import Agent, AgentArray, Item, Player, Py4GW
from Sources.oazix.CustomBehaviors.skills.monitoring.drop_tracker_inventory_runtime import (
    coerce_consistent_item_identity,
)

EXPECTED_RUNTIME_ERRORS = (TypeError, ValueError, RuntimeError, AttributeError, IndexError, KeyError, OSError)


def _normalize_world_item_rarity(item_id: int, clean_name: str, rarity: str) -> str:
    resolved = str(rarity or "Unknown")
    if Item.Type.IsTome(item_id):
        return "Tomes"
    if "Dye" in clean_name or "Vial of Dye" in clean_name:
        return "Dyes"
    if "Key" in clean_name:
        return "Keys"
    if Item.Type.IsMaterial(item_id) or Item.Type.IsRareMaterial(item_id):
        return "Material"
    return resolved


def prune_recent_world_item_disappearances(sender, now_ts: float | None = None) -> None:
    now = float(now_ts if now_ts is not None else time.time())
    ttl_s = max(1.0, float(getattr(sender, "world_item_disappearance_ttl_seconds", 5.0)))
    kept = []
    for entry in list(getattr(sender, "recent_world_item_disappearances", []) or []):
        if not isinstance(entry, dict):
            continue
        disappeared_at = float(entry.get("disappeared_at", now))
        if (now - disappeared_at) <= ttl_s:
            kept.append(entry)
    sender.recent_world_item_disappearances = kept


def build_world_item_state(sender, agent_id: int) -> dict[str, Any] | None:
    try:
        world_agent_id = int(agent_id)
        if world_agent_id <= 0 or not Agent.IsValid(world_agent_id):
            return None
        item_id = int(Agent.GetItemAgentItemID(world_agent_id) or 0)
        if item_id <= 0:
            return None
        player_agent_id = int(Player.GetAgentID() or 0)
        owner_agent_id = int(Agent.GetItemAgentOwnerID(world_agent_id) or 0)
        if player_agent_id > 0 and owner_agent_id not in (0, player_agent_id):
            return None
        model_id = int(Item.GetModelID(item_id) or 0)
        qty = max(1, int(Item.Properties.GetQuantity(item_id) or 1))
        rarity = "Unknown"
        try:
            rarity = str(Item.Rarity.GetRarity(item_id)[1] or "Unknown")
        except EXPECTED_RUNTIME_ERRORS:
            rarity = "Unknown"
        name = ""
        try:
            if Item.IsNameReady(item_id):
                raw_name = Item.GetName(item_id) or ""
                strip_tags = getattr(sender, "_strip_tags", lambda text: text)
                name = re.sub(r"^[\d,]+\s+", "", str(strip_tags(str(raw_name))).strip()).strip()
            else:
                Item.RequestName(item_id)
        except EXPECTED_RUNTIME_ERRORS:
            name = ""
        if not name:
            name = f"Model#{model_id}" if model_id > 0 else "Unknown Item"
        name, rarity, requested_refresh = coerce_consistent_item_identity(item_id, model_id, name, rarity)
        if requested_refresh:
            try:
                Item.RequestName(item_id)
            except EXPECTED_RUNTIME_ERRORS:
                pass
        if not name:
            name = f"Model#{model_id}" if model_id > 0 else "Unknown Item"
        rarity = _normalize_world_item_rarity(item_id, name, rarity)
        return {
            "agent_id": world_agent_id,
            "item_id": item_id,
            "model_id": model_id,
            "qty": qty,
            "rarity": rarity,
            "name": name,
            "owner_agent_id": owner_agent_id,
        }
    except EXPECTED_RUNTIME_ERRORS:
        return None


def poll_world_item_disappearances(sender) -> None:
    now_ts = time.time()
    prune_recent_world_item_disappearances(sender, now_ts)
    try:
        current_agent_ids = [int(v) for v in list(AgentArray.GetItemArray() or []) if int(v) > 0]
    except EXPECTED_RUNTIME_ERRORS:
        return

    next_world_items: dict[int, dict[str, Any]] = {}
    saw_world_items = False
    for agent_id in current_agent_ids:
        entry = build_world_item_state(sender, agent_id)
        if not isinstance(entry, dict):
            continue
        previous_entry = sender.current_world_item_agents.get(agent_id)
        if isinstance(previous_entry, dict):
            previous_name = str(previous_entry.get("name", "") or "").strip()
            current_name = str(entry.get("name", "") or "").strip()
            if previous_name and not previous_name.startswith("Model#") and current_name.startswith("Model#"):
                entry["name"] = previous_name
        next_world_items[agent_id] = entry
        saw_world_items = True

    for agent_id, previous_entry in list(sender.current_world_item_agents.items()):
        if agent_id in next_world_items:
            continue
        if not isinstance(previous_entry, dict):
            continue
        disappearance = dict(previous_entry)
        disappearance["disappeared_at"] = now_ts
        sender.recent_world_item_disappearances.append(disappearance)
        if sender.debug_pipeline_logs:
            Py4GW.Console.Log(
                "DropTrackerSender",
                (
                    f"WORLD item disappeared item='{str(disappearance.get('name', 'Unknown Item'))}' "
                    f"qty={int(disappearance.get('qty', 1))} rarity={str(disappearance.get('rarity', 'Unknown'))} "
                    f"agent_id={int(disappearance.get('agent_id', 0))} item_id={int(disappearance.get('item_id', 0))} "
                    f"model_id={int(disappearance.get('model_id', 0))}"
                ),
                Py4GW.Console.MessageType.Info,
            )

    sender.current_world_item_agents = next_world_items
    sender.last_world_item_scan_count = len(next_world_items)
    if saw_world_items:
        sender.world_item_seen_since_reset = True
    prune_recent_world_item_disappearances(sender, now_ts)


def world_item_names_compatible(world_name: str, event_name: str) -> bool:
    left = str(world_name or "").strip()
    right = str(event_name or "").strip()
    left_ready = bool(left and not left.startswith("Model#") and left != "Unknown Item")
    right_ready = bool(right and not right.startswith("Model#") and right != "Unknown Item")
    if not left_ready or not right_ready:
        return True
    if left == right:
        return True
    return _normalize_world_name_for_compare(left) == _normalize_world_name_for_compare(right)


def _normalize_world_name_for_compare(name: str) -> str:
    normalized_tokens: list[str] = []
    for token in str(name or "").strip().lower().split():
        if token.endswith("ies") and len(token) > 3:
            normalized_tokens.append(token[:-3] + "y")
            continue
        if token.endswith("s") and len(token) > 1 and not token.endswith("ss"):
            normalized_tokens.append(token[:-1])
            continue
        normalized_tokens.append(token)
    return " ".join(normalized_tokens)


def _world_item_match_score(candidate: dict[str, Any], event: dict[str, Any]) -> tuple[int, int, int] | None:
    if not isinstance(candidate, dict):
        return None
    event_item_id = int(event.get("item_id", 0))
    event_model_id = int(event.get("model_id", 0))
    event_qty = max(1, int(event.get("qty", 1)))
    event_rarity = str(event.get("rarity", "Unknown") or "Unknown")
    event_name = str(event.get("name", "") or "").strip()
    event_reason = str(event.get("reason", "") or "").strip()

    candidate_model_id = int(candidate.get("model_id", 0))
    candidate_qty = max(1, int(candidate.get("qty", 1)))
    if event_model_id > 0 and candidate_model_id > 0 and candidate_model_id != event_model_id:
        return None
    qty_matches = candidate_qty == event_qty
    if event_reason == "stack_increase":
        qty_matches = candidate_qty >= event_qty
    if not qty_matches:
        return None
    candidate_rarity = str(candidate.get("rarity", "Unknown") or "Unknown")
    if (
        event_rarity != "Unknown"
        and candidate_rarity != "Unknown"
        and candidate_rarity != event_rarity
    ):
        return None
    if not world_item_names_compatible(str(candidate.get("name", "") or ""), event_name):
        return None
    return (
        1 if int(candidate.get("item_id", 0)) == event_item_id and event_item_id > 0 else 0,
        1 if candidate_rarity == event_rarity and event_rarity != "Unknown" else 0,
        1 if world_item_names_compatible(str(candidate.get("name", "") or ""), event_name) else 0,
    )


def _consume_matching_recent_disappearance(sender, event: dict[str, Any]) -> dict[str, Any] | None:
    best_index = -1
    best_score: tuple[int, int, int] = (-1, -1, -1)
    for idx, candidate in enumerate(list(sender.recent_world_item_disappearances)):
        score = _world_item_match_score(candidate, event)
        if score is None:
            continue
        if score > best_score:
            best_score = score
            best_index = idx
    if best_index < 0:
        return None
    return sender.recent_world_item_disappearances.pop(best_index)


def _consume_matching_live_world_item(sender, event: dict[str, Any]) -> dict[str, Any] | None:
    best_agent_id = 0
    best_score: tuple[int, int, int] = (-1, -1, -1)
    for agent_id, candidate in list(getattr(sender, "current_world_item_agents", {}).items()):
        score = _world_item_match_score(candidate, event)
        if score is None:
            continue
        if score > best_score:
            best_score = score
            best_agent_id = int(agent_id)
    if best_agent_id <= 0:
        return None
    return getattr(sender, "current_world_item_agents", {}).pop(best_agent_id, None)


def consume_recent_world_item_confirmation(sender, event: dict[str, Any]) -> bool:
    if not bool(getattr(sender, "require_world_item_confirmation", True)):
        return True
    now_ts = time.time()
    prune_recent_world_item_disappearances(sender, now_ts)
    matched = _consume_matching_recent_disappearance(sender, event)
    if matched is None:
        matched = _consume_matching_live_world_item(sender, event)
    if matched is None:
        return False

    event_item_id = int(event.get("item_id", 0))
    event_model_id = int(event.get("model_id", 0))
    event_qty = max(1, int(event.get("qty", 1)))
    event_rarity = str(event.get("rarity", "Unknown") or "Unknown")
    event_name = str(event.get("name", "") or "").strip()
    if sender.debug_pipeline_logs:
        Py4GW.Console.Log(
            "DropTrackerSender",
            (
                f"WORLD matched candidate item='{event_name or 'Unknown Item'}' "
                f"qty={event_qty} rarity={event_rarity} item_id={event_item_id} model_id={event_model_id} "
                f"world_agent_id={int(matched.get('agent_id', 0))} world_item_id={int(matched.get('item_id', 0))}"
            ),
            Py4GW.Console.MessageType.Info,
        )
    return True
