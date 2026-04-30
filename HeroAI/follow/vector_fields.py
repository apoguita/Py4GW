from __future__ import annotations

import math
from dataclasses import dataclass

from Py4GWCoreLib import Agent, Range, ThrottledTimer, Utils
from Py4GWCoreLib.AgentArray import AgentArray
from Py4GWCoreLib.IniManager import IniManager
from Py4GWCoreLib.Player import Player
from Py4GWCoreLib.Py4GWcorelib import VectorFields


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
_FOLLOW_RUNTIME_SECTION = "FollowRuntime"


def _write_follow_movement_value(im: IniManager, key: str, name: str, value: float) -> None:
    im.write_key(key, _FOLLOW_RUNTIME_SECTION, name, float(value))
    node = im._get_node(key)
    if node:
        text_value = str(float(value))
        node.ini_handler.write_key(_FOLLOW_RUNTIME_SECTION, name, text_value)
        node.cached_values[(_FOLLOW_RUNTIME_SECTION, name)] = text_value
        node.pending_writes.pop((_FOLLOW_RUNTIME_SECTION, name), None)
        node.needs_flush = bool(node.pending_writes)


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
    if force_reload or _FOLLOW_MOVEMENT_CACHE_TIMER.IsExpired():
        try:
            im.reload(key)
        except Exception:
            pass

    _FOLLOW_MOVEMENT_CACHE = FollowMovementConfig(
        slot_recovery_distance=max(
            1.0,
            float(im.read_float(key, _FOLLOW_RUNTIME_SECTION, "slot_recovery_distance", float(Range.Nearby.value))),
        ),
        ally_repulsion_radius=max(
            0.0,
            float(im.read_float(key, _FOLLOW_RUNTIME_SECTION, "ally_repulsion_radius", float(Range.Adjacent.value))),
        ),
        ally_repulsion_weight=max(
            0.0,
            float(im.read_float(key, _FOLLOW_RUNTIME_SECTION, "ally_repulsion_weight", 0.65)),
        ),
        enemy_repulsion_radius=max(
            0.0,
            float(im.read_float(key, _FOLLOW_RUNTIME_SECTION, "enemy_repulsion_radius", float(Range.Nearby.value))),
        ),
        enemy_repulsion_weight=max(
            0.0,
            float(im.read_float(key, _FOLLOW_RUNTIME_SECTION, "enemy_repulsion_weight", 0.45)),
        ),
        local_move_clamp=max(
            1.0,
            float(im.read_float(key, _FOLLOW_RUNTIME_SECTION, "local_move_clamp", float(Range.Area.value))),
        ),
        min_move_threshold=max(
            0.0,
            float(im.read_float(key, _FOLLOW_RUNTIME_SECTION, "min_move_threshold", 15.0)),
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
    im.set(key, "slot_recovery_distance", float(config.slot_recovery_distance), section=_FOLLOW_RUNTIME_SECTION)
    im.set(key, "ally_repulsion_radius", float(config.ally_repulsion_radius), section=_FOLLOW_RUNTIME_SECTION)
    im.set(key, "ally_repulsion_weight", float(config.ally_repulsion_weight), section=_FOLLOW_RUNTIME_SECTION)
    im.set(key, "enemy_repulsion_radius", float(config.enemy_repulsion_radius), section=_FOLLOW_RUNTIME_SECTION)
    im.set(key, "enemy_repulsion_weight", float(config.enemy_repulsion_weight), section=_FOLLOW_RUNTIME_SECTION)
    im.set(key, "local_move_clamp", float(config.local_move_clamp), section=_FOLLOW_RUNTIME_SECTION)
    im.set(key, "min_move_threshold", float(config.min_move_threshold), section=_FOLLOW_RUNTIME_SECTION)
    im.save_vars(key)
    _write_follow_movement_value(im, key, "slot_recovery_distance", config.slot_recovery_distance)
    _write_follow_movement_value(im, key, "ally_repulsion_radius", config.ally_repulsion_radius)
    _write_follow_movement_value(im, key, "ally_repulsion_weight", config.ally_repulsion_weight)
    _write_follow_movement_value(im, key, "enemy_repulsion_radius", config.enemy_repulsion_radius)
    _write_follow_movement_value(im, key, "enemy_repulsion_weight", config.enemy_repulsion_weight)
    _write_follow_movement_value(im, key, "local_move_clamp", config.local_move_clamp)
    _write_follow_movement_value(im, key, "min_move_threshold", config.min_move_threshold)
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
    ally_positions: list[tuple[float, float]] | None = None,
    enemy_positions: list[tuple[float, float]] | None = None,
) -> tuple[float, float] | None:
    cfg = config or load_follow_movement_config()
    target_tolerance = max(0.0, follow_distance)

    slot_distance = Utils.Distance(current_pos, assigned_pos)
    attraction_active = slot_distance > target_tolerance

    if slot_distance <= target_tolerance and not in_combat:
        return None

    repulsion_positions: list[tuple[float, float]] = []
    active_ally_count = 0
    active_enemy_count = 0

    ally_positions = ally_positions if ally_positions is not None else _collect_nearby_allies()
    for ally_pos in ally_positions:
        if cfg.ally_repulsion_radius <= 0.0:
            break
        if Utils.Distance(current_pos, ally_pos) < cfg.ally_repulsion_radius:
            repulsion_positions.append(ally_pos)
            active_ally_count += 1

    enemy_positions = enemy_positions if enemy_positions is not None else _collect_nearby_enemies()
    for enemy_pos in enemy_positions:
        if cfg.enemy_repulsion_radius <= 0.0:
            break
        if Utils.Distance(current_pos, enemy_pos) < cfg.enemy_repulsion_radius:
            repulsion_positions.append(enemy_pos)
            active_enemy_count += 1

    if not attraction_active and not repulsion_positions:
        return None

    max_repulsion_radius = max(cfg.ally_repulsion_radius, cfg.enemy_repulsion_radius, 1.0)
    max_attraction_radius = max(1500.0, slot_distance + 1.0)
    vf = VectorFields(
        current_pos,
        custom_repulsion_radius=int(max_repulsion_radius),
        custom_attraction_radius=int(max_attraction_radius),
    )

    for repulsion_pos in repulsion_positions:
        vf.add_custom_repulsion_position(repulsion_pos)

    if attraction_active:
        vf.add_custom_attraction_position(assigned_pos)

    result_x, result_y = vf.compute_combined_vector()
    move_norm_x, move_norm_y, move_distance = _normalize(result_x, result_y)
    if move_distance <= 0.001:
        return None

    movement_scale = 50.0
    if attraction_active:
        distance_error = max(0.0, slot_distance - target_tolerance)
        if slot_distance > cfg.slot_recovery_distance:
            movement_scale = max(
                movement_scale,
                min(distance_error, cfg.local_move_clamp),
            )
        else:
            attraction_weight_factor = min(max(distance_error / 200.0, 1.0), 5.0)
            movement_scale *= attraction_weight_factor

    if active_ally_count > 0:
        movement_scale *= max(cfg.ally_repulsion_weight, 0.1)

    if active_enemy_count > 0:
        movement_scale *= max(cfg.enemy_repulsion_weight, 0.1)

    movement_scale = max(movement_scale, cfg.min_move_threshold)
    movement_scale = min(movement_scale, cfg.local_move_clamp)
    result_x = move_norm_x * movement_scale
    result_y = move_norm_y * movement_scale

    candidate = (
        current_pos[0] + result_x,
        current_pos[1] + result_y,
    )

    if slot_distance <= target_tolerance:
        candidate = _clamp_point_to_radius(candidate, assigned_pos, max(target_tolerance, cfg.min_move_threshold))

    if Utils.Distance(candidate, current_pos) < cfg.min_move_threshold:
        return None

    return candidate
