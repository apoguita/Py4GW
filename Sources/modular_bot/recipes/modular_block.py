"""
Unified modular recipe runner.

Canonical JSON format is steps-only:

{
  "name": "Any Block",
  "steps": [{...}]
}

Legacy mission/quest/route top-level keys are still accepted and translated
into equivalent pre-steps so existing files keep working during migration.
"""

from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from Py4GWCoreLib import Botting

from ..phase import Phase
from .inventory_recipe import build_auto_inventory_guard_step
from .modular_actions import register_step as _register_shared_step
from .runner_common import count_expanded_steps, register_recipe_context, register_repeated_steps


_BLOCK_DIRS: dict[str, str] = {
    "missions": "missions",
    "quests": "quests",
    "routes": "routes",
    "farms": "farms",
}


def _modular_root_dir() -> str:
    return os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))


def _normalize_block_name(block_name: str) -> str:
    name = str(block_name or "").strip().replace("\\", "/")
    if name.endswith(".json"):
        name = name[:-5]
    return name.strip("/")


def _resolve_block_path(block_name: str, kind: Optional[str] = None) -> str:
    normalized = _normalize_block_name(block_name)
    if not normalized:
        raise FileNotFoundError("Empty modular block name.")

    root = _modular_root_dir()
    if os.path.isabs(normalized):
        absolute = normalized if normalized.endswith(".json") else f"{normalized}.json"
        if os.path.isfile(absolute):
            return absolute
        raise FileNotFoundError(f"Modular block not found: {absolute}")

    candidates: list[str] = []
    direct_candidate = os.path.join(root, f"{normalized}.json")
    candidates.append(direct_candidate)

    search_kinds: list[str]
    if kind:
        kind_norm = str(kind).strip().lower()
        if kind_norm not in _BLOCK_DIRS:
            raise FileNotFoundError(f"Unknown block kind: {kind!r}")
        search_kinds = [kind_norm]
    else:
        search_kinds = list(_BLOCK_DIRS.keys())

    for block_kind in search_kinds:
        base_dir = os.path.join(root, _BLOCK_DIRS[block_kind])
        if normalized.startswith(f"{_BLOCK_DIRS[block_kind]}/"):
            rel_name = normalized[len(_BLOCK_DIRS[block_kind]) + 1:]
        else:
            rel_name = normalized
        candidates.append(os.path.join(base_dir, f"{rel_name}.json"))

    for candidate in candidates:
        candidate_norm = os.path.normpath(candidate)
        if os.path.isfile(candidate_norm):
            return candidate_norm

    available = list_available_blocks(kind=kind)
    raise FileNotFoundError(
        f"Modular block not found: {block_name!r}\n"
        f"Checked: {candidates}\n"
        f"Available ({kind or 'all'}): {available}"
    )


def _load_block_data(block_name: str, kind: Optional[str] = None) -> Dict[str, Any]:
    filepath = _resolve_block_path(block_name, kind=kind)
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def _list_json_files(base_dir: str) -> list[str]:
    if not os.path.isdir(base_dir):
        return []

    names: list[str] = []
    for root, _, files in os.walk(base_dir):
        for filename in files:
            if not filename.endswith(".json"):
                continue
            relative = os.path.relpath(os.path.join(root, filename), base_dir).replace("\\", "/")
            names.append(relative[:-5])
    return sorted(names)


def list_available_blocks(kind: Optional[str] = None) -> List[str]:
    root = _modular_root_dir()
    if kind:
        kind_norm = str(kind).strip().lower()
        if kind_norm not in _BLOCK_DIRS:
            return []
        return _list_json_files(os.path.join(root, _BLOCK_DIRS[kind_norm]))

    merged: list[str] = []
    for block_kind, dirname in _BLOCK_DIRS.items():
        for rel in _list_json_files(os.path.join(root, dirname)):
            merged.append(f"{block_kind}/{rel}")
    return sorted(merged)


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(str(value), 0)
    except (TypeError, ValueError):
        return int(default)


def _coerce_required_heroes(raw: Any) -> list[str]:
    if raw is None:
        return []
    if isinstance(raw, str):
        value = raw.strip()
        return [value] if value else []
    if isinstance(raw, list):
        result: list[str] = []
        for item in raw:
            if not isinstance(item, str):
                continue
            value = item.strip()
            if value and value not in result:
                result.append(value)
        return result
    return []


def _inject_required_heroes_into_load_party_steps(steps: list[dict], required_heroes: list[str]) -> list[dict]:
    if not required_heroes:
        return steps

    injected: list[dict] = []
    for step in steps:
        if not isinstance(step, dict):
            injected.append(step)
            continue

        if str(step.get("type", "")).strip().lower() != "load_party":
            injected.append(step)
            continue

        updated_step = dict(step)
        step_required = _coerce_required_heroes(updated_step.get("required_hero"))
        merged_required: list[str] = []
        for hero_name in required_heroes + step_required:
            if hero_name not in merged_required:
                merged_required.append(hero_name)
        updated_step["required_hero"] = merged_required
        injected.append(updated_step)

    return injected


def _inject_load_party_overrides_into_steps(steps: list[dict], overrides: dict[str, Any]) -> list[dict]:
    if not overrides:
        return steps

    injected: list[dict] = []
    for step in steps:
        if not isinstance(step, dict):
            injected.append(step)
            continue
        if str(step.get("type", "")).strip().lower() != "load_party":
            injected.append(step)
            continue
        updated_step = dict(step)
        for key, value in overrides.items():
            updated_step[str(key)] = value
        injected.append(updated_step)
    return injected


def _legacy_pre_steps(data: Dict[str, Any]) -> list[dict]:
    steps: list[dict] = []

    outpost_id = _safe_int(data.get("outpost_id"), 0)
    take_quest = data.get("take_quest") if isinstance(data.get("take_quest"), dict) else None
    take_quest_outpost_id = _safe_int((take_quest or {}).get("outpost_id"), 0)
    travel_outpost_id = take_quest_outpost_id or outpost_id

    max_heroes = _safe_int(data.get("max_heroes"), 0)
    hero_team = str(data.get("hero_team", "") or "").strip()
    entry = data.get("entry") if isinstance(data.get("entry"), dict) else None

    if travel_outpost_id > 0:
        steps.append({"type": "leave_party", "name": "Leave Party (Legacy)"})
        steps.append({"type": "travel", "name": "Travel to Outpost (Legacy)", "target_map_id": travel_outpost_id})

    if max_heroes > 0 or hero_team:
        load_party_step: dict[str, Any] = {"type": "load_party", "name": "Load Party (Legacy)"}
        if max_heroes > 0:
            load_party_step["max_heroes"] = int(max_heroes)
        if hero_team:
            load_party_step["team"] = hero_team
            if hero_team == "party_6_no_spirits_minions":
                load_party_step["minionless"] = True
        steps.append(load_party_step)

    if entry:
        entry_type = str(entry.get("type", "") or "").strip().lower()
        if entry_type == "enter_challenge":
            enter_step: dict[str, Any] = {"type": "enter_challenge", "name": "Enter Mission (Legacy)"}
            target_map_id = _safe_int(entry.get("target_map_id"), 0)
            if target_map_id > 0:
                enter_step["target_map_id"] = target_map_id
            delay_value = _safe_int(entry.get("delay", entry.get("delay_ms", 2000)), 2000)
            if delay_value > 0:
                enter_step["delay_ms"] = delay_value
            steps.append(enter_step)
        elif entry_type == "dialog":
            dialog_step: dict[str, Any] = {"type": "dialog", "name": "Enter Mission (Legacy)"}
            if "x" in entry and "y" in entry:
                dialog_step["x"] = entry["x"]
                dialog_step["y"] = entry["y"]
            if "id" in entry:
                dialog_step["id"] = entry["id"]
            steps.append(dialog_step)

    if take_quest:
        npc_location = take_quest.get("quest_npc_location")
        dialog_id_raw = take_quest.get("dialog_id")
        wait_ms = max(0, _safe_int(take_quest.get("wait_ms", 1000), 1000))
        step_name = str(take_quest.get("name", "Take Quest") or "Take Quest").strip()

        if isinstance(npc_location, list) and len(npc_location) == 2:
            steps.append(
                {
                    "type": "interact_npc",
                    "name": f"{step_name} - Reach NPC (Legacy)",
                    "x": npc_location[0],
                    "y": npc_location[1],
                    "ms": wait_ms,
                }
            )

        if dialog_id_raw is not None:
            dialog_ids = dialog_id_raw if isinstance(dialog_id_raw, (list, tuple)) else [dialog_id_raw]
            if len(dialog_ids) == 1:
                step = {"type": "dialog", "name": step_name, "id": dialog_ids[0]}
                if isinstance(npc_location, list) and len(npc_location) == 2:
                    step["x"] = npc_location[0]
                    step["y"] = npc_location[1]
                if wait_ms > 0:
                    step["ms"] = wait_ms
                steps.append(step)
            else:
                step = {"type": "dialogs", "name": step_name, "id": list(dialog_ids)}
                if isinstance(npc_location, list) and len(npc_location) == 2:
                    step["x"] = npc_location[0]
                    step["y"] = npc_location[1]
                if wait_ms > 0:
                    step["ms"] = wait_ms
                steps.append(step)

    return steps


def modular_block_run(
    bot: "Botting",
    block_name: str,
    *,
    kind: Optional[str] = None,
    recipe_name: str = "ModularBlock",
    load_party_overrides: Optional[Dict[str, Any]] = None,
) -> None:
    from Py4GWCoreLib import ConsoleLog

    data = _load_block_data(block_name, kind=kind)
    display_name = str(data.get("name", block_name) or block_name)
    body_steps = data.get("steps", [])
    if not isinstance(body_steps, list):
        body_steps = []

    pre_steps = _legacy_pre_steps(data)
    steps = [*pre_steps, *body_steps]

    required_heroes = _coerce_required_heroes(data.get("required_hero"))
    if not required_heroes:
        required_heroes = _coerce_required_heroes(data.get("required_heroes"))
    if required_heroes:
        steps = _inject_required_heroes_into_load_party_steps(steps, required_heroes)
    if load_party_overrides:
        steps = _inject_load_party_overrides_into_steps(steps, dict(load_party_overrides))

    inventory_guard_step = build_auto_inventory_guard_step("modular_block", data)
    total_steps = count_expanded_steps(steps) + (
        1 if inventory_guard_step and inventory_guard_step.get("check_on_start", True) else 0
    )
    register_recipe_context(bot, display_name, total_steps=total_steps)

    if inventory_guard_step and inventory_guard_step.get("check_on_start", True):
        _register_shared_step(bot, inventory_guard_step, 0, recipe_name=recipe_name)

    total_registered_steps = register_repeated_steps(
        bot,
        recipe_name=recipe_name,
        steps=steps,
        register_step=lambda _bot, step, idx: _register_shared_step(_bot, step, idx, recipe_name=recipe_name),
    )

    ConsoleLog(
        f"Recipe:{recipe_name}",
        (
            f"Registered block: {display_name} "
            f"({total_registered_steps} expanded steps from {len(steps)} source steps, "
            f"legacy_pre_steps={len(pre_steps)})"
        ),
    )


def ModularBlock(
    block_name: str,
    name: Optional[str] = None,
    *,
    kind: Optional[str] = None,
    anchor: bool = False,
) -> Phase:
    if name is None:
        try:
            data = _load_block_data(block_name, kind=kind)
            name = str(data.get("name", block_name))
        except FileNotFoundError:
            name = f"ModularBlock: {block_name}"
    return Phase(name, lambda bot: modular_block_run(bot, block_name, kind=kind), anchor=anchor)


# Backward-compatible public API aliases.
def list_available_missions() -> List[str]:
    return list_available_blocks(kind="missions")


def list_available_quests() -> List[str]:
    return list_available_blocks(kind="quests")


def list_available_routes() -> List[str]:
    return list_available_blocks(kind="routes")


def list_available_farms() -> List[str]:
    return list_available_blocks(kind="farms")


def mission_run(bot: "Botting", mission_name: str) -> None:
    modular_block_run(bot, mission_name, kind="missions", recipe_name="Mission")


def quest_run(bot: "Botting", quest_name: str) -> None:
    modular_block_run(bot, quest_name, kind="quests", recipe_name="Quest")


def route_run(bot: "Botting", route_name: str) -> None:
    modular_block_run(bot, route_name, kind="routes", recipe_name="Route")


def farm_run(bot: "Botting", farm_name: str) -> None:
    modular_block_run(bot, farm_name, kind="farms", recipe_name="Farm")


def Mission(mission_name: str, name: Optional[str] = None, anchor: bool = False) -> Phase:
    return ModularBlock(mission_name, name=name, kind="missions", anchor=anchor)


def Quest(quest_name: str, name: Optional[str] = None, anchor: bool = False) -> Phase:
    return ModularBlock(quest_name, name=name, kind="quests", anchor=anchor)


def Route(route_name: str, name: Optional[str] = None, anchor: bool = False) -> Phase:
    return ModularBlock(route_name, name=name, kind="routes", anchor=anchor)


def Farm(farm_name: str, name: Optional[str] = None, anchor: bool = False) -> Phase:
    return ModularBlock(farm_name, name=name, kind="farms", anchor=anchor)

