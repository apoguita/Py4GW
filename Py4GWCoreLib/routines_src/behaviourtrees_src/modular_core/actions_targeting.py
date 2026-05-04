"""
actions_targeting module

This module is part of the modular runtime surface.
"""
from __future__ import annotations

from Py4GWCoreLib.routines_src.behaviourtrees_src.botting_interaction import (
    add_debug_nearby_agents_state,
    add_debug_nearby_enemies_state,
    add_target_enemy_state,
    add_wait_model_has_quest_state,
)

from .combat_engine import (
    ENGINE_HERO_AI,
    set_party_target as engine_set_party_target,
)
from .step_context import StepContext
from .step_registration import modular_step
from .step_selectors import resolve_enemy_agent_id_from_step
from .step_utils import log_recipe, recipe_debug_logging_enabled
from .step_utils import parse_step_bool, parse_step_float, parse_step_int, wait_after_step


def _recipe_log(recipe_name: str, message: str) -> None:
    from Py4GWCoreLib import ConsoleLog

    ConsoleLog(f"Recipe:{recipe_name}", message)


def handle_target_enemy(ctx: StepContext) -> None:
    set_party_target = parse_step_bool(ctx.step.get("set_party_target", False), False)
    step_name = ctx.step.get("name", "Target Enemy")

    def _resolve_enemy() -> int | None:
        return resolve_enemy_agent_id_from_step(
            ctx.step,
            recipe_name=ctx.recipe_name,
            step_idx=ctx.step_idx,
        )

    def _set_party_target(target_agent_id: int) -> None:
        try:
            engine_set_party_target(target_agent_id, preferred_engine=ENGINE_HERO_AI, bot=ctx.bot)
        except Exception:
            return

    add_target_enemy_state(
        ctx.bot,
        enemy_resolver=_resolve_enemy,
        set_party_target=set_party_target,
        party_target_setter=_set_party_target,
        name=str(step_name),
    )
    wait_after_step(ctx.bot, ctx.step)


def handle_debug_nearby_enemies(ctx: StepContext) -> None:
    max_dist = parse_step_float(ctx.step.get("max_dist", 5000.0), 5000.0)
    if max_dist <= 0:
        max_dist = 5000.0

    limit = parse_step_int(ctx.step.get("limit", 25), 25)
    if limit <= 0:
        limit = 25

    include_dead = parse_step_bool(ctx.step.get("include_dead", False), False)
    add_debug_nearby_enemies_state(
        ctx.bot,
        max_dist=max_dist,
        limit=limit,
        include_dead=include_dead,
        enabled=lambda: recipe_debug_logging_enabled(ctx),
        name=str(ctx.step.get("name", "Debug Nearby Enemies")),
        log=lambda message: _recipe_log(ctx.recipe_name, message),
    )
    wait_after_step(ctx.bot, ctx.step)


def handle_debug_nearby_agents(ctx: StepContext) -> None:
    max_dist = parse_step_float(ctx.step.get("max_dist", 5000.0), 5000.0)
    if max_dist <= 0:
        max_dist = 5000.0

    limit = parse_step_int(ctx.step.get("limit", 25), 25)
    if limit <= 0:
        limit = 25

    include_dead = parse_step_bool(ctx.step.get("include_dead", True), True)
    add_debug_nearby_agents_state(
        ctx.bot,
        max_dist=max_dist,
        limit=limit,
        include_dead=include_dead,
        enabled=lambda: recipe_debug_logging_enabled(ctx),
        name=str(ctx.step.get("name", "Debug Nearby Agents")),
        log=lambda message: _recipe_log(ctx.recipe_name, message),
    )
    wait_after_step(ctx.bot, ctx.step)


def handle_wait_model_has_quest(ctx: StepContext) -> None:
    model_id = int(str(ctx.step["model_id"]), 0)
    add_wait_model_has_quest_state(ctx.bot, model_id=model_id)
    wait_after_step(ctx.bot, ctx.step)


def handle_add_enemy_blacklist(ctx: StepContext) -> None:
    from Py4GWCoreLib.EnemyBlacklist import EnemyBlacklist

    enemy_name = str(ctx.step.get("enemy_name", "")).strip()
    if not enemy_name:
        log_recipe(ctx, "add_enemy_blacklist requires non-empty 'enemy_name'.")
        return

    ctx.bot.States.AddCustomState(
        lambda name=enemy_name: EnemyBlacklist().add_name(name),
        ctx.step.get("name", f"Add Enemy Blacklist: {enemy_name}"),
    )
    wait_after_step(ctx.bot, ctx.step)


def handle_remove_enemy_blacklist(ctx: StepContext) -> None:
    from Py4GWCoreLib.EnemyBlacklist import EnemyBlacklist

    enemy_name = str(ctx.step.get("enemy_name", "")).strip()
    if not enemy_name:
        log_recipe(ctx, "remove_enemy_blacklist requires non-empty 'enemy_name'.")
        return

    ctx.bot.States.AddCustomState(
        lambda name=enemy_name: EnemyBlacklist().remove_name(name),
        ctx.step.get("name", f"Remove Enemy Blacklist: {enemy_name}"),
    )
    wait_after_step(ctx.bot, ctx.step)


modular_step(
    step_type="add_enemy_blacklist",
    category="targeting",
    allowed_params=("enemy_name", "name"),
    node_class_name="AddEnemyBlacklistNode",
)(handle_add_enemy_blacklist)
modular_step(
    step_type="debug_nearby_agents",
    category="targeting",
    allowed_params=("include_dead", "limit", "max_dist", "name"),
    node_class_name="DebugNearbyAgentsNode",
)(handle_debug_nearby_agents)
modular_step(
    step_type="debug_nearby_enemies",
    category="targeting",
    allowed_params=("include_dead", "limit", "max_dist", "name"),
    node_class_name="DebugNearbyEnemiesNode",
)(handle_debug_nearby_enemies)
modular_step(
    step_type="remove_enemy_blacklist",
    category="targeting",
    allowed_params=("enemy_name", "name"),
    node_class_name="RemoveEnemyBlacklistNode",
)(handle_remove_enemy_blacklist)
modular_step(
    step_type="target_enemy",
    category="targeting",
    allowed_params=(
        "exact_name",
        "include_dead",
        "max_dist",
        "model_id",
        "name",
        "nearest",
        "set_party_target",
        "target_name",
    ),
    node_class_name="TargetEnemyNode",
)(handle_target_enemy)
modular_step(
    step_type="wait_model_has_quest",
    category="targeting",
    allowed_params=("model_id", "name"),
    node_class_name="WaitModelHasQuestNode",
)(handle_wait_model_has_quest)
