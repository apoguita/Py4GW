"""Selector helpers kept for BT-oriented modular recipes and MerchantRules."""
from __future__ import annotations

from typing import Any

import PyAgent
from Py4GWCoreLib import Range

from .domain.target_registry import get_named_agent_target


COMPASS_RANGE = float(Range.Compass.value)


def resolve_agent_xy_from_step(
    step: dict[str, Any],
    *,
    recipe_name: str,
    step_idx: int,
    agent_kind: str,
    default_max_dist: float | None = None,
    log_failures: bool = True,
) -> tuple[float, float] | None:
    from Py4GWCoreLib import Agent, AgentArray, Player

    if default_max_dist is None:
        default_max_dist = COMPASS_RANGE

    explicit_point = _parse_point(step)
    if explicit_point is not None:
        return explicit_point

    max_dist = _parse_float(step.get("max_dist", default_max_dist), default_max_dist)
    if max_dist <= 0:
        max_dist = default_max_dist

    named_target_key = str(step.get(agent_kind, "") or "").strip()
    named_target = get_named_agent_target(agent_kind, named_target_key) if named_target_key else None
    target_name = str(
        step.get("target", step.get("name_contains", step.get("agent_name", step.get("enemy_name", "")))) or ""
    ).strip()
    model_id_raw = step.get("model_id", None)
    model_id = _parse_int(model_id_raw, 0) if model_id_raw is not None else None
    if model_id is None and named_target is not None and named_target.model_id is not None:
        model_id = int(named_target.model_id)
    encoded_names = named_target.encoded_names if named_target is not None else ()
    if not target_name and named_target is not None and not encoded_names and model_id is None:
        target_name = str(named_target.display_name or "").strip()
    exact_name = _parse_bool(step.get("exact_name", False), False)
    nearest = _parse_bool(step.get("nearest", False), False)

    if agent_kind == "npc":
        agent_array = AgentArray.GetNPCMinipetArray()
    elif agent_kind == "gadget":
        agent_array = AgentArray.GetGadgetArray()
    else:
        _log_recipe(recipe_name, f"Unsupported agent resolver kind: {agent_kind!r}")
        return None

    px, py = Player.GetXY()
    agent_array = AgentArray.Filter.ByDistance(agent_array, (px, py), max_dist)
    agent_array = AgentArray.Sort.ByDistance(agent_array, (px, py))

    if nearest and not target_name and model_id is None and not encoded_names:
        if agent_array:
            return Agent.GetXY(int(agent_array[0]))
        if log_failures:
            _log_recipe(recipe_name, f"No nearest {agent_kind} found within {max_dist:.0f} at index {step_idx}")
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
            return agent_name_l == target_name_l if exact_name else target_name_l in agent_name_l
        return model_id is not None or bool(encoded_names)

    if target_name or model_id is not None or encoded_names:
        matches = AgentArray.Filter.ByCondition(agent_array, _matches)
        matches = AgentArray.Sort.ByDistance(matches, (px, py))
        if matches:
            return Agent.GetXY(int(matches[0]))

    if log_failures:
        _log_recipe(recipe_name, f"Could not resolve {agent_kind} within {max_dist:.0f} at index {step_idx}")
    return None


def _matches_encoded_name(agent_id: int, encoded_names: tuple[tuple[int, ...], ...]) -> bool:
    if not encoded_names:
        return False
    agent_enc_name = PyAgent.PyAgent.GetAgentEncName(agent_id)
    if not agent_enc_name:
        return False
    agent_enc_tuple = tuple(int(value) for value in agent_enc_name)
    return any(agent_enc_tuple == tuple(encoded_name) for encoded_name in encoded_names)


def _parse_point(step: dict[str, Any]) -> tuple[float, float] | None:
    point = step.get("point")
    if isinstance(point, (list, tuple)) and len(point) >= 2:
        try:
            return float(point[0]), float(point[1])
        except (TypeError, ValueError):
            return None
    if "x" in step and "y" in step:
        try:
            return float(step["x"]), float(step["y"])
        except (TypeError, ValueError):
            return None
    return None


def _parse_int(value: Any, default: int) -> int:
    try:
        if isinstance(value, str):
            return int(value, 0)
        return int(value)
    except (TypeError, ValueError):
        return default


def _parse_float(value: Any, default: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _parse_bool(value: Any, default: bool) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"1", "true", "yes", "on"}:
            return True
        if normalized in {"0", "false", "no", "off"}:
            return False
    return default


def _log_recipe(recipe_name: str, message: str) -> None:
    from Py4GWCoreLib import ConsoleLog

    ConsoleLog(f"Recipe:{recipe_name}", message)
