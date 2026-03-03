from __future__ import annotations

from typing import Any, Dict

import PyAgent
from Py4GWCoreLib import Range

from .target_enums import get_named_agent_target, get_named_item_target
from .step_utils import parse_step_bool, parse_step_float, parse_step_int

COMPASS_RANGE = float(Range.Compass.value)


def _matches_encoded_name(agent_id: int, encoded_names: tuple[tuple[int, ...], ...]) -> bool:
    if not encoded_names:
        return False

    agent_enc_name = PyAgent.PyAgent.GetAgentEncName(agent_id)
    if not agent_enc_name:
        return False

    agent_enc_tuple = tuple(int(value) for value in agent_enc_name)
    return any(agent_enc_tuple == tuple(encoded_name) for encoded_name in encoded_names)


def resolve_agent_xy_from_step(
    step: Dict[str, Any],
    *,
    recipe_name: str,
    step_idx: int,
    agent_kind: str,
    default_max_dist: float | None = None,
) -> tuple[float, float] | None:
    from Py4GWCoreLib import Agent, AgentArray, ConsoleLog, Player

    if default_max_dist is None:
        default_max_dist = COMPASS_RANGE

    if "x" in step and "y" in step:
        return float(step["x"]), float(step["y"])

    max_dist = parse_step_float(step.get("max_dist", default_max_dist), default_max_dist)
    if max_dist <= 0:
        max_dist = default_max_dist

    named_target_key = str(step.get(agent_kind, "") or "").strip()
    named_target = get_named_agent_target(agent_kind, named_target_key) if named_target_key else None
    target_name = str(
        step.get("target", step.get("name_contains", step.get("agent_name", step.get("enemy_name", "")))) or ""
    ).strip()
    model_id_raw = step.get("model_id", None)
    model_id = parse_step_int(model_id_raw, 0) if model_id_raw is not None else None
    if model_id is None and named_target is not None and named_target.model_id is not None:
        model_id = int(named_target.model_id)
    encoded_names = named_target.encoded_names if named_target is not None else ()
    exact_name = parse_step_bool(step.get("exact_name", False), False)
    nearest = parse_step_bool(step.get("nearest", False), False)

    if agent_kind == "npc":
        agent_array = AgentArray.GetNPCMinipetArray()
    elif agent_kind == "gadget":
        agent_array = AgentArray.GetGadgetArray()
    else:
        ConsoleLog(f"Recipe:{recipe_name}", f"Unsupported agent resolver kind: {agent_kind!r}")
        return None

    px, py = Player.GetXY()
    agent_array = AgentArray.Filter.ByDistance(agent_array, (px, py), max_dist)
    agent_array = AgentArray.Sort.ByDistance(agent_array, (px, py))

    if nearest and not target_name and model_id is None and not encoded_names:
        if agent_array:
            return Agent.GetXY(int(agent_array[0]))
        ConsoleLog(
            f"Recipe:{recipe_name}",
            f"No nearest {agent_kind} found within {max_dist:.0f} at index {step_idx}",
        )
        return None

    target_name_l = target_name.lower()

    def _matches(agent_id: int) -> bool:
        if model_id is not None and Agent.GetModelID(agent_id) != model_id:
            return False

        if encoded_names and not _matches_encoded_name(agent_id, encoded_names):
            return False

        if target_name:
            agent_name = Agent.GetNameByID(agent_id).strip()
            if not agent_name:
                return False
            agent_name_l = agent_name.lower()
            if exact_name:
                return agent_name_l == target_name_l
            return target_name_l in agent_name_l

        return model_id is not None or bool(encoded_names)

    if target_name or model_id is not None or encoded_names:
        matches = AgentArray.Filter.ByCondition(agent_array, _matches)
        matches = AgentArray.Sort.ByDistance(matches, (px, py))
        if matches:
            return Agent.GetXY(int(matches[0]))

    descriptor_parts: list[str] = []
    if named_target_key:
        descriptor_parts.append(f"{agent_kind}={named_target_key!r}")
    if target_name:
        descriptor_parts.append(f"name={target_name!r}")
    if model_id is not None:
        descriptor_parts.append(f"model_id={model_id}")
    if encoded_names:
        descriptor_parts.append("encoded_name=true")
    if nearest:
        descriptor_parts.append("nearest=true")
    descriptor = ", ".join(descriptor_parts) or "no selector"
    ConsoleLog(
        f"Recipe:{recipe_name}",
        f"Could not resolve {agent_kind} using {descriptor} within {max_dist:.0f} at index {step_idx}",
    )
    return None


def resolve_enemy_agent_id_from_step(
    step: Dict[str, Any],
    *,
    recipe_name: str,
    step_idx: int,
    default_max_dist: float | None = None,
) -> int | None:
    from Py4GWCoreLib import Agent, AgentArray, ConsoleLog, Player

    if default_max_dist is None:
        default_max_dist = COMPASS_RANGE

    agent_id_raw = step.get("agent_id", step.get("id", None))
    if agent_id_raw is not None:
        agent_id = parse_step_int(agent_id_raw, 0)
        if agent_id > 0 and Agent.IsValid(agent_id):
            return agent_id
        ConsoleLog(
            f"Recipe:{recipe_name}",
            f"Invalid enemy agent_id at index {step_idx}: {agent_id_raw!r}",
        )
        return None

    max_dist = parse_step_float(step.get("max_dist", default_max_dist), default_max_dist)
    if max_dist <= 0:
        max_dist = default_max_dist

    named_target_key = str(step.get("enemy", "") or "").strip()
    named_target = get_named_agent_target("enemy", named_target_key) if named_target_key else None
    target_name = str(step.get("target", step.get("name_contains", step.get("enemy_name", ""))) or "").strip()
    model_id_raw = step.get("model_id", None)
    model_id = parse_step_int(model_id_raw, 0) if model_id_raw is not None else None
    if model_id is None and named_target is not None and named_target.model_id is not None:
        model_id = int(named_target.model_id)
    encoded_names = named_target.encoded_names if named_target is not None else ()
    exact_name = parse_step_bool(step.get("exact_name", False), False)
    nearest = parse_step_bool(step.get("nearest", False), False)

    px, py = Player.GetXY()
    enemy_array = AgentArray.GetEnemyArray()
    enemy_array = AgentArray.Filter.ByDistance(enemy_array, (px, py), max_dist)
    enemy_array = AgentArray.Filter.ByCondition(enemy_array, lambda eid: Agent.IsAlive(eid))
    enemy_array = AgentArray.Sort.ByDistance(enemy_array, (px, py))

    if nearest and not target_name and model_id is None and not encoded_names:
        return int(enemy_array[0]) if enemy_array else None

    target_name_l = target_name.lower()

    def _matches(enemy_id: int) -> bool:
        if model_id is not None and Agent.GetModelID(enemy_id) != model_id:
            return False

        if encoded_names and not _matches_encoded_name(enemy_id, encoded_names):
            return False

        if target_name:
            enemy_name = Agent.GetNameByID(enemy_id).strip()
            if not enemy_name:
                return False
            enemy_name_l = enemy_name.lower()
            if exact_name:
                return enemy_name_l == target_name_l
            return target_name_l in enemy_name_l

        return model_id is not None or bool(encoded_names)

    if target_name or model_id is not None or encoded_names:
        enemy_array = AgentArray.Filter.ByCondition(enemy_array, _matches)
        enemy_array = AgentArray.Sort.ByDistance(enemy_array, (px, py))
        if enemy_array:
            return int(enemy_array[0])

    descriptor_parts: list[str] = []
    if named_target_key:
        descriptor_parts.append(f"enemy={named_target_key!r}")
    if target_name:
        descriptor_parts.append(f"name={target_name!r}")
    if model_id is not None:
        descriptor_parts.append(f"model_id={model_id}")
    if encoded_names:
        descriptor_parts.append("encoded_name=true")
    if nearest:
        descriptor_parts.append("nearest=true")
    descriptor = ", ".join(descriptor_parts) or "no selector"
    ConsoleLog(
        f"Recipe:{recipe_name}",
        f"Could not resolve enemy using {descriptor} within {max_dist:.0f} at index {step_idx}",
    )
    return None


def resolve_item_model_id_from_step(
    step: Dict[str, Any],
    *,
    recipe_name: str,
    step_idx: int,
) -> int | None:
    from Py4GWCoreLib import ConsoleLog

    named_item_key = str(step.get("item", "") or "").strip()
    named_item = get_named_item_target(named_item_key) if named_item_key else None
    model_id_raw = step.get("model_id", None)

    if model_id_raw is None and named_item is not None:
        model_id = named_item.model_id
        if model_id is not None:
            return int(model_id)

    if model_id_raw is None:
        if named_item_key:
            ConsoleLog(
                f"Recipe:{recipe_name}",
                f"Unknown item selector at index {step_idx}: {named_item_key!r}",
            )
        return None

    try:
        return int(str(model_id_raw), 0)
    except (TypeError, ValueError):
        ConsoleLog(
            f"Recipe:{recipe_name}",
            f"Invalid item selector at index {step_idx}: model_id={model_id_raw!r}, item={named_item_key!r}",
        )
        return None
