"""
actions_targeting module

This module is part of the modular runtime surface.
"""
from __future__ import annotations

from .combat_engine import (
    ENGINE_HERO_AI,
    set_party_target as engine_set_party_target,
)
from .step_context import StepContext
from .step_registration import modular_step
from .step_selectors import resolve_enemy_agent_id_from_step
from .step_utils import log_recipe, recipe_debug_logging_enabled
from .step_utils import parse_step_bool, parse_step_float, parse_step_int, wait_after_step


def handle_target_enemy(ctx: StepContext) -> None:
    from Py4GWCoreLib import Player

    set_party_target = parse_step_bool(ctx.step.get("set_party_target", False), False)
    step_name = ctx.step.get("name", "Target Enemy")

    def _target_enemy() -> None:
        target_agent_id = resolve_enemy_agent_id_from_step(
            ctx.step,
            recipe_name=ctx.recipe_name,
            step_idx=ctx.step_idx,
        )
        if target_agent_id is None:
            return
        Player.ChangeTarget(target_agent_id)
        if set_party_target:
            try:
                engine_set_party_target(target_agent_id, preferred_engine=ENGINE_HERO_AI, bot=ctx.bot)
            except Exception:
                return

    ctx.bot.States.AddCustomState(_target_enemy, step_name)
    wait_after_step(ctx.bot, ctx.step)


def handle_debug_nearby_enemies(ctx: StepContext) -> None:
    from Py4GWCoreLib import Agent, AgentArray, ConsoleLog, Player, Utils

    max_dist = parse_step_float(ctx.step.get("max_dist", 5000.0), 5000.0)
    if max_dist <= 0:
        max_dist = 5000.0

    limit = parse_step_int(ctx.step.get("limit", 25), 25)
    if limit <= 0:
        limit = 25

    include_dead = parse_step_bool(ctx.step.get("include_dead", False), False)

    def _debug_nearby_enemies() -> None:
        if not recipe_debug_logging_enabled(ctx):
            return
        px, py = Player.GetXY()
        enemies = AgentArray.GetEnemyArray()
        enemies = AgentArray.Filter.ByDistance(enemies, (px, py), max_dist)
        enemies = AgentArray.Filter.ByCondition(
            enemies,
            lambda agent_id: Agent.IsSpawned(agent_id) and (include_dead or Agent.IsAlive(agent_id)),
        )
        enemies = AgentArray.Sort.ByDistance(enemies, (px, py))

        ConsoleLog(
            f"Recipe:{ctx.recipe_name}",
            f"debug_nearby_enemies found {len(enemies)} enemies within {max_dist:.0f}",
        )

        for idx, agent_id in enumerate(enemies[:limit]):
            ax, ay = Agent.GetXY(agent_id)
            distance = Utils.Distance((px, py), (ax, ay))
            ConsoleLog(
                f"Recipe:{ctx.recipe_name}",
                (
                    f"[{idx + 1}] agent_id={int(agent_id)} "
                    f"model_id={int(Agent.GetModelID(agent_id))} "
                    f"distance={distance:.0f} "
                    f"alive={Agent.IsAlive(agent_id)} "
                    f"name={Agent.GetNameByID(agent_id)!r}"
                ),
            )

    ctx.bot.States.AddCustomState(_debug_nearby_enemies, ctx.step.get("name", "Debug Nearby Enemies"))
    wait_after_step(ctx.bot, ctx.step)


def handle_debug_nearby_agents(ctx: StepContext) -> None:
    from Py4GWCoreLib import Agent, AgentArray, ConsoleLog, Player, Utils

    max_dist = parse_step_float(ctx.step.get("max_dist", 5000.0), 5000.0)
    if max_dist <= 0:
        max_dist = 5000.0

    limit = parse_step_int(ctx.step.get("limit", 25), 25)
    if limit <= 0:
        limit = 25

    include_dead = parse_step_bool(ctx.step.get("include_dead", True), True)

    def _debug_nearby_agents() -> None:
        if not recipe_debug_logging_enabled(ctx): return
        px, py = Player.GetXY()
        agents = AgentArray.GetAgentArray()
        agents = AgentArray.Filter.ByDistance(agents, (px, py), max_dist)
        agents = AgentArray.Filter.ByCondition(
            agents,
            lambda agent_id: Agent.IsValid(agent_id) and (include_dead or Agent.IsAlive(agent_id)),
        )
        agents = AgentArray.Sort.ByDistance(agents, (px, py))

        ConsoleLog(
            f"Recipe:{ctx.recipe_name}",
            f"debug_nearby_agents found {len(agents)} agents within {max_dist:.0f}",
        )

        for idx, agent_id in enumerate(agents[:limit]):
            ax, ay = Agent.GetXY(agent_id)
            distance = Utils.Distance((px, py), (ax, ay))
            ConsoleLog(
                f"Recipe:{ctx.recipe_name}",
                (
                    f"[{idx + 1}] agent_id={int(agent_id)} "
                    f"model_id={int(Agent.GetModelID(agent_id))} "
                    f"distance={distance:.0f} "
                    f"alive={Agent.IsAlive(agent_id)} "
                    f"spawned={Agent.IsSpawned(agent_id)} "
                    f"living={Agent.IsLiving(agent_id)} "
                    f"item={Agent.IsItem(agent_id)} "
                    f"gadget={Agent.IsGadget(agent_id)} "
                    f"allegiance={Agent.GetAllegiance(agent_id)[1]!r} "
                    f"name={Agent.GetNameByID(agent_id)!r}"
                ),
            )

    ctx.bot.States.AddCustomState(_debug_nearby_agents, ctx.step.get("name", "Debug Nearby Agents"))
    wait_after_step(ctx.bot, ctx.step)


def handle_wait_model_has_quest(ctx: StepContext) -> None:
    model_id = int(str(ctx.step["model_id"]), 0)
    ctx.bot.Wait.UntilModelHasQuest(model_id)
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
