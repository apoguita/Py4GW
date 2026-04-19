from __future__ import annotations

import math
from dataclasses import dataclass

from Py4GWCoreLib import Agent, Range, ThrottledTimer, Utils
from Py4GWCoreLib.AgentArray import AgentArray
from Py4GWCoreLib.IniManager import IniManager
from Py4GWCoreLib.Player import Player


@dataclass(slots=True)
class FollowMovementConfig:
    slot_recovery_distance: float = float(Range.Nearby.value)
    ally_repulsion_radius: float = float(Range.Adjacent.value)
    ally_repulsion_weight: float = 0.65
    enemy_repulsion_radius: float = float(Range.Nearby.value)
    enemy_repulsion_weight: float = 0.45
    local_move_clamp: float = float(Range.Area.value)
    min_move_threshold: float = 15.0


_FOLLOW_RUNTIME_KEY = ""
_FOLLOW_MOVEMENT_VARS_REGISTERED = False
_FOLLOW_MOVEMENT_CACHE: FollowMovementConfig | None = None
_FOLLOW_MOVEMENT_CACHE_TIMER = ThrottledTimer(1000)


def _ensure_follow_runtime_key() -> str:
    global _FOLLOW_RUNTIME_KEY
    if not _FOLLOW_RUNTIME_KEY:
        _FOLLOW_RUNTIME_KEY = IniManager().ensure_global_key("HeroAI", "FollowRuntime.ini")
    return _FOLLOW_RUNTIME_KEY


def _ensure_follow_movement_vars() -> str:
    global _FOLLOW_MOVEMENT_VARS_REGISTERED
    key = _ensure_follow_runtime_key()
    if not key:
        return ""

    if not _FOLLOW_MOVEMENT_VARS_REGISTERED:
        im = IniManager()
        im.add_float(
            key,
            "slot_recovery_distance",
            "FollowRuntime",
            "slot_recovery_distance",
            float(Range.Nearby.value),
        )
        im.add_float(
            key,
            "ally_repulsion_radius",
            "FollowRuntime",
            "ally_repulsion_radius",
            float(Range.Adjacent.value),
        )
        im.add_float(
            key,
            "ally_repulsion_weight",
            "FollowRuntime",
            "ally_repulsion_weight",
            0.65,
        )
        im.add_float(
            key,
            "enemy_repulsion_radius",
            "FollowRuntime",
            "enemy_repulsion_radius",
            float(Range.Nearby.value),
        )
        im.add_float(
            key,
            "enemy_repulsion_weight",
            "FollowRuntime",
            "enemy_repulsion_weight",
            0.45,
        )
        im.add_float(
            key,
            "local_move_clamp",
            "FollowRuntime",
            "local_move_clamp",
            float(Range.Area.value),
        )
        im.add_float(
            key,
            "min_move_threshold",
            "FollowRuntime",
            "min_move_threshold",
            15.0,
        )
        _FOLLOW_MOVEMENT_VARS_REGISTERED = True

    IniManager().load_once(key)
    return key


def load_follow_movement_config(force_reload: bool = False) -> FollowMovementConfig:
    global _FOLLOW_MOVEMENT_CACHE

    key = _ensure_follow_movement_vars()
    if not key:
        return FollowMovementConfig()

    if (
        not force_reload
        and _FOLLOW_MOVEMENT_CACHE is not None
        and not _FOLLOW_MOVEMENT_CACHE_TIMER.IsExpired()
    ):
        return _FOLLOW_MOVEMENT_CACHE

    im = IniManager()
    if force_reload:
        try:
            im.reload(key)
        except Exception:
            pass

    _FOLLOW_MOVEMENT_CACHE = FollowMovementConfig(
        slot_recovery_distance=max(
            1.0,
            float(im.getFloat(key, "slot_recovery_distance", float(Range.Nearby.value), section="FollowRuntime")),
        ),
        ally_repulsion_radius=max(
            0.0,
            float(im.getFloat(key, "ally_repulsion_radius", float(Range.Adjacent.value), section="FollowRuntime")),
        ),
        ally_repulsion_weight=max(
            0.0,
            float(im.getFloat(key, "ally_repulsion_weight", 0.65, section="FollowRuntime")),
        ),
        enemy_repulsion_radius=max(
            0.0,
            float(im.getFloat(key, "enemy_repulsion_radius", float(Range.Nearby.value), section="FollowRuntime")),
        ),
        enemy_repulsion_weight=max(
            0.0,
            float(im.getFloat(key, "enemy_repulsion_weight", 0.45, section="FollowRuntime")),
        ),
        local_move_clamp=max(
            1.0,
            float(im.getFloat(key, "local_move_clamp", float(Range.Area.value), section="FollowRuntime")),
        ),
        min_move_threshold=max(
            0.0,
            float(im.getFloat(key, "min_move_threshold", 15.0, section="FollowRuntime")),
        ),
    )
    _FOLLOW_MOVEMENT_CACHE_TIMER.Reset()
    return _FOLLOW_MOVEMENT_CACHE


def save_follow_movement_config(config: FollowMovementConfig) -> None:
    global _FOLLOW_MOVEMENT_CACHE

    key = _ensure_follow_movement_vars()
    if not key:
        return

    im = IniManager()
    im.set(key, "slot_recovery_distance", float(config.slot_recovery_distance), section="FollowRuntime")
    im.set(key, "ally_repulsion_radius", float(config.ally_repulsion_radius), section="FollowRuntime")
    im.set(key, "ally_repulsion_weight", float(config.ally_repulsion_weight), section="FollowRuntime")
    im.set(key, "enemy_repulsion_radius", float(config.enemy_repulsion_radius), section="FollowRuntime")
    im.set(key, "enemy_repulsion_weight", float(config.enemy_repulsion_weight), section="FollowRuntime")
    im.set(key, "local_move_clamp", float(config.local_move_clamp), section="FollowRuntime")
    im.set(key, "min_move_threshold", float(config.min_move_threshold), section="FollowRuntime")
    im.save_vars(key)
    _FOLLOW_MOVEMENT_CACHE = FollowMovementConfig(
        slot_recovery_distance=float(config.slot_recovery_distance),
        ally_repulsion_radius=float(config.ally_repulsion_radius),
        ally_repulsion_weight=float(config.ally_repulsion_weight),
        enemy_repulsion_radius=float(config.enemy_repulsion_radius),
        enemy_repulsion_weight=float(config.enemy_repulsion_weight),
        local_move_clamp=float(config.local_move_clamp),
        min_move_threshold=float(config.min_move_threshold),
    )
    _FOLLOW_MOVEMENT_CACHE_TIMER.Reset()


def _normalize(dx: float, dy: float) -> tuple[float, float, float]:
    magnitude = math.sqrt((dx * dx) + (dy * dy))
    if magnitude <= 0.001:
        return (0.0, 0.0, 0.0)
    return (dx / magnitude, dy / magnitude, magnitude)


def _accumulate_repulsion(
    current_pos: tuple[float, float],
    positions: list[tuple[float, float]],
    radius: float,
    weight: float,
) -> tuple[float, float]:
    if radius <= 0.0 or weight <= 0.0:
        return (0.0, 0.0)

    result_x = 0.0
    result_y = 0.0
    for pos_x, pos_y in positions:
        dx = current_pos[0] - pos_x
        dy = current_pos[1] - pos_y
        norm_x, norm_y, distance = _normalize(dx, dy)
        if distance <= 0.001 or distance >= radius:
            continue
        force = ((radius - distance) / radius) * radius * weight
        result_x += norm_x * force
        result_y += norm_y * force

    return (result_x, result_y)


def _collect_nearby_allies() -> list[tuple[float, float]]:
    my_agent_id = Player.GetAgentID()
    positions: list[tuple[float, float]] = []
    for agent_id in AgentArray.GetAllyArray():
        if agent_id == my_agent_id or not Agent.IsValid(agent_id) or not Agent.IsAlive(agent_id):
            continue
        positions.append(Agent.GetXY(agent_id))

    for agent_id in AgentArray.GetSpiritPetArray():
        if not Agent.IsValid(agent_id) or not Agent.IsAlive(agent_id):
            continue
        positions.append(Agent.GetXY(agent_id))

    return positions


def _collect_nearby_enemies() -> list[tuple[float, float]]:
    positions: list[tuple[float, float]] = []
    for agent_id in AgentArray.GetEnemyArray():
        if not Agent.IsValid(agent_id) or not Agent.IsAlive(agent_id):
            continue
        positions.append(Agent.GetXY(agent_id))
    return positions


def _clamp_point_to_radius(
    point: tuple[float, float],
    center: tuple[float, float],
    radius: float,
) -> tuple[float, float]:
    if radius <= 0.0:
        return center

    dx = point[0] - center[0]
    dy = point[1] - center[1]
    norm_x, norm_y, distance = _normalize(dx, dy)
    if distance <= radius:
        return point
    return (center[0] + (norm_x * radius), center[1] + (norm_y * radius))


def compute_mixed_follow_target(
    current_pos: tuple[float, float],
    assigned_pos: tuple[float, float],
    follow_distance: float,
    in_combat: bool,
    config: FollowMovementConfig | None = None,
) -> tuple[float, float] | None:
    cfg = config or load_follow_movement_config()

    slot_dx = assigned_pos[0] - current_pos[0]
    slot_dy = assigned_pos[1] - current_pos[1]
    slot_norm_x, slot_norm_y, slot_distance = _normalize(slot_dx, slot_dy)

    if slot_distance <= max(0.0, follow_distance) and not in_combat:
        return None

    if slot_distance > cfg.slot_recovery_distance:
        move_amount = min(slot_distance, cfg.local_move_clamp)
        if move_amount < cfg.min_move_threshold:
            return None
        return (
            current_pos[0] + (slot_norm_x * move_amount),
            current_pos[1] + (slot_norm_y * move_amount),
        )

    result_x = 0.0
    result_y = 0.0

    if slot_distance > follow_distance:
        attraction_amount = slot_distance - follow_distance
        result_x += slot_norm_x * attraction_amount
        result_y += slot_norm_y * attraction_amount

    if in_combat:
        ally_repulsion_x, ally_repulsion_y = _accumulate_repulsion(
            current_pos,
            _collect_nearby_allies(),
            cfg.ally_repulsion_radius,
            cfg.ally_repulsion_weight,
        )
        enemy_repulsion_x, enemy_repulsion_y = _accumulate_repulsion(
            current_pos,
            _collect_nearby_enemies(),
            cfg.enemy_repulsion_radius,
            cfg.enemy_repulsion_weight,
        )
        result_x += ally_repulsion_x + enemy_repulsion_x
        result_y += ally_repulsion_y + enemy_repulsion_y

    move_norm_x, move_norm_y, move_distance = _normalize(result_x, result_y)
    if move_distance < cfg.min_move_threshold:
        return None

    if move_distance > cfg.local_move_clamp:
        result_x = move_norm_x * cfg.local_move_clamp
        result_y = move_norm_y * cfg.local_move_clamp

    candidate = (
        current_pos[0] + result_x,
        current_pos[1] + result_y,
    )

    if slot_distance <= follow_distance:
        candidate = _clamp_point_to_radius(candidate, assigned_pos, max(follow_distance, cfg.min_move_threshold))

    if Utils.Distance(candidate, current_pos) < cfg.min_move_threshold:
        return None

    return candidate
