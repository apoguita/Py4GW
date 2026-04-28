"""
actions_party module

This module is part of the modular runtime surface.
"""
from __future__ import annotations

from Py4GWCoreLib.routines_src.behaviourtrees_src.botting_party import (
    add_drop_bundle_state,
    add_flag_heroes_state,
    add_force_hero_state,
    add_unflag_heroes_state,
    add_wait_all_accounts_same_map_state,
)
from Py4GWCoreLib.routines_src.behaviourtrees_src.botting_multibox import (
    add_abandon_quest_state,
    add_broadcast_summoning_stone_state,
    add_flag_all_accounts_state,
    add_unflag_all_accounts_state,
)

from .combat_engine import (
    ENGINE_HERO_AI,
    flag_all_accounts as engine_flag_all_accounts,
    resolve_engine_for_bot,
    set_auto_combat as engine_set_auto_combat,
    set_auto_following as engine_set_auto_following,
    set_auto_looting as engine_set_auto_looting,
    unflag_all_accounts as engine_unflag_all_accounts,
)
from .step_context import StepContext
from .step_registration import modular_step
from .step_utils import debug_log_recipe, log_recipe, parse_step_bool, parse_step_int, parse_step_point, wait_after_step
from .actions_party_consumables import (
    handle_use_all_consumables,
    handle_use_armor_of_salvation,
    handle_use_conset,
    handle_use_consumables,
    handle_use_essence_of_celerity,
    handle_use_grail_of_might,
    handle_use_pcons,
    handle_upkeep_consumables,
)
from .actions_party_load import handle_load_party


def _default_summoning_stone_models() -> list[int]:
    from Py4GWCoreLib import ModelID

    return [
        int(ModelID.Legionnaire_Summoning_Crystal.value),
        int(ModelID.Igneous_Summoning_Stone.value),
        int(ModelID.Tengu_Summon.value),
    ]


def _resolve_summoning_stone_models(raw_value) -> list[int]:
    from Py4GWCoreLib import ModelID

    if raw_value is None:
        return _default_summoning_stone_models()
    raw_items = list(raw_value) if isinstance(raw_value, list) else [raw_value]

    resolved: list[int] = []
    for entry in raw_items:
        mid = parse_step_int(entry, 0)
        if mid <= 0 and isinstance(entry, str):
            token = entry.strip()
            if token.lower().startswith("modelid."):
                token = token.split(".", 1)[1]
            model_obj = getattr(ModelID, token, None)
            mid = int(getattr(model_obj, "value", model_obj) or 0) if model_obj is not None else 0
        if mid > 0 and mid not in resolved:
            resolved.append(mid)
    return resolved


def handle_set_title(ctx: StepContext) -> None:
    ctx.bot.Player.SetTitle(ctx.step["id"])
    wait_after_step(ctx.bot, ctx.step)


def handle_drop_bundle(ctx: StepContext) -> None:
    add_drop_bundle_state(ctx.bot, str(ctx.step.get("name", "Drop Bundle") or "Drop Bundle"))
    wait_after_step(ctx.bot, ctx.step)


def handle_force_hero_state(ctx: StepContext) -> None:
    raw_state = str(ctx.step.get("state", "")).strip().lower()
    behavior_map = {
        "fight": 0,
        "guard": 1,
        "avoid": 2,
    }

    if "behavior" in ctx.step:
        try:
            behavior = int(ctx.step["behavior"])
        except (TypeError, ValueError):
            behavior = -1
    else:
        behavior = behavior_map.get(raw_state, -1)

    if behavior not in (0, 1, 2):
        debug_log_recipe(
            ctx,
            f"Invalid force_hero_state at index {ctx.step_idx}: state={raw_state!r}, behavior={ctx.step.get('behavior')!r}",
        )
        return

    state_name = ctx.step.get("name", f"Force Hero State ({raw_state or behavior})")
    add_force_hero_state(ctx.bot, behavior, name=str(state_name))
    wait_after_step(ctx.bot, ctx.step)


def handle_flag_heroes(ctx: StepContext) -> None:
    coords = parse_step_point(ctx.step)
    if coords is None:
        debug_log_recipe(ctx, f"flag_heroes invalid coordinates at index {ctx.step_idx}: expected point [x, y].")
        return
    x, y = coords
    add_flag_heroes_state(
        ctx.bot,
        x,
        y,
        name=str(ctx.step.get("name", "Flag Heroes")),
        log=lambda message: debug_log_recipe(ctx, message),
    )
    wait_after_step(ctx.bot, ctx.step)


def handle_flag_all_accounts(ctx: StepContext) -> None:
    coords = parse_step_point(ctx.step)
    if coords is None:
        debug_log_recipe(
            ctx,
            f"flag_all_accounts invalid coordinates at index {ctx.step_idx}: expected point [x, y].",
        )
        return
    x, y = coords

    def _flagger(flag_x: float, flag_y: float) -> int:
        engine = resolve_engine_for_bot(ctx.bot)
        changed = 0
        try:
            # HeroAI is the only supported modular combat backend.
            changed += int(engine_flag_all_accounts(flag_x, flag_y, preferred_engine=engine, bot=ctx.bot))
            if engine != ENGINE_HERO_AI:
                changed += int(engine_flag_all_accounts(flag_x, flag_y, preferred_engine=ENGINE_HERO_AI, bot=ctx.bot))
        except Exception as exc:
            debug_log_recipe(ctx, f"flag_all_accounts failed at index {ctx.step_idx}: {exc}")
            return 0
        return changed

    add_flag_all_accounts_state(
        ctx.bot,
        x=x,
        y=y,
        flagger=_flagger,
        name=str(ctx.step.get("name", "Flag All Accounts")),
        log=lambda message: debug_log_recipe(ctx, message),
    )
    wait_after_step(ctx.bot, ctx.step)


def handle_unflag_heroes(ctx: StepContext) -> None:
    add_unflag_heroes_state(ctx.bot, str(ctx.step.get("name", "Unflag Heroes")))
    wait_after_step(ctx.bot, ctx.step)


def handle_unflag_all_accounts(ctx: StepContext) -> None:
    def _unflagger() -> int:
        engine = resolve_engine_for_bot(ctx.bot)
        changed = int(engine_unflag_all_accounts(preferred_engine=engine, bot=ctx.bot))
        if engine != ENGINE_HERO_AI:
            changed += int(engine_unflag_all_accounts(preferred_engine=ENGINE_HERO_AI, bot=ctx.bot))
        return changed

    add_unflag_all_accounts_state(
        ctx.bot,
        unflagger=_unflagger,
        name=str(ctx.step.get("name", "Unflag All Accounts")),
        log=lambda message: debug_log_recipe(ctx, message),
    )
    wait_after_step(ctx.bot, ctx.step)


def handle_resign(ctx: StepContext) -> None:
    ctx.bot.Multibox.ResignParty()
    wait_after_step(ctx.bot, ctx.step)


def handle_summon_all_accounts(ctx: StepContext) -> None:
    ctx.bot.Multibox.SummonAllAccounts()
    wait_after_step(ctx.bot, ctx.step)


def handle_wait_all_accounts_same_map(ctx: StepContext) -> None:
    timeout_ms = max(0, parse_step_int(ctx.step.get("timeout_ms", 60000), 60000))
    poll_ms = max(100, parse_step_int(ctx.step.get("poll_ms", 500), 500))
    include_self = parse_step_bool(ctx.step.get("include_self", False), False)
    exact = parse_step_bool(ctx.step.get("require_same_district", False), False)
    add_wait_all_accounts_same_map_state(
        ctx.bot,
        timeout_ms=timeout_ms,
        poll_ms=poll_ms,
        include_self=include_self,
        require_same_district=exact,
        name=str(ctx.step.get("name", "Wait All Accounts Same Map")),
        log=lambda message: debug_log_recipe(ctx, message),
    )


def handle_invite_all_accounts(ctx: StepContext) -> None:
    ctx.bot.Multibox.InviteAllAccounts()
    wait_after_step(ctx.bot, ctx.step)


def handle_abandon_quest(ctx: StepContext) -> None:
    quest_id = parse_step_int(ctx.step.get("quest_id", ctx.step.get("id", 0)), 0)
    multibox = parse_step_bool(ctx.step.get("multibox", False), False)
    skip_leader = parse_step_bool(ctx.step.get("skip_leader", False), False)

    if quest_id <= 0:
        debug_log_recipe(ctx, f"abandon_quest requires valid quest_id at index {ctx.step_idx}.")
        return

    add_abandon_quest_state(
        ctx.bot,
        quest_id=quest_id,
        multibox=multibox,
        skip_leader=skip_leader,
        name=str(ctx.step.get("name", f"Abandon Quest {quest_id}")),
    )
    wait_after_step(ctx.bot, ctx.step)


def handle_broadcast_summoning_stone(ctx: StepContext) -> None:
    raw_models = ctx.step.get("models", ctx.step.get("summon_models", _default_summoning_stone_models()))
    effect_id = max(0, parse_step_int(ctx.step.get("effect_id", 2886), 2886))
    repeat = max(1, parse_step_int(ctx.step.get("repeat", 1), 1))
    per_message_wait_ms = max(0, parse_step_int(ctx.step.get("per_message_wait_ms", 250), 250))
    model_ids = _resolve_summoning_stone_models(raw_models)
    if not model_ids:
        debug_log_recipe(ctx, "broadcast_summoning_stone skipped: no valid model IDs resolved.")
        return

    add_broadcast_summoning_stone_state(
        ctx.bot,
        model_ids=model_ids,
        effect_id=effect_id,
        repeat=repeat,
        per_message_wait_ms=per_message_wait_ms,
        name=str(ctx.step.get("name", "Broadcast Summoning Stone")),
        log=lambda message: debug_log_recipe(ctx, message),
    )
    wait_after_step(ctx.bot, ctx.step)


def handle_set_anchor(ctx: StepContext) -> None:
    target = str(ctx.step.get("phase", ctx.step.get("target", ctx.step.get("name", ""))) or "").strip()
    owner = getattr(ctx.bot, "_modular_owner", None)
    if owner is None or not hasattr(owner, "set_anchor"):
        debug_log_recipe(ctx, f"set_anchor requires ModularBot owner; step index {ctx.step_idx}")
        return
    if not target:
        current_state = ctx.bot.config.FSM.current_state
        target = str(getattr(current_state, "name", "") or "").strip()
    if not owner.set_anchor(target):
        debug_log_recipe(ctx, f"set_anchor could not resolve target at index {ctx.step_idx}: {target!r}")
        return
    wait_after_step(ctx.bot, ctx.step)


def handle_set_hard_mode(ctx: StepContext) -> None:
    enabled = parse_step_bool(ctx.step.get("enabled", True), True)
    ctx.bot.Party.SetHardMode(enabled)
    wait_after_step(ctx.bot, ctx.step)


def handle_set_combat_engine(ctx: StepContext) -> None:
    from .combat_engine import ENGINE_HERO_AI, ENGINE_NONE

    raw_engine = str(ctx.step.get("engine", ctx.step.get("value", "")) or "").strip().lower()
    aliases = {
        "heroai": ENGINE_HERO_AI,
        "hero_ai": ENGINE_HERO_AI,
        "none": ENGINE_NONE,
    }
    normalized_engine = raw_engine.replace("_", "")
    if normalized_engine in ("custombehaviors", "cb"):
        debug_log_recipe(
            ctx,
            f"set_combat_engine unsupported engine at index {ctx.step_idx}: {raw_engine!r}; use 'hero_ai' or 'none'.",
        )
        return
    engine = aliases.get(raw_engine, raw_engine)
    if engine not in (ENGINE_HERO_AI, ENGINE_NONE):
        debug_log_recipe(
            ctx,
            f"set_combat_engine invalid engine at index {ctx.step_idx}: {raw_engine!r}",
        )
        return

    def _set_engine() -> None:
        setattr(ctx.bot.config, "_modular_start_engine", engine)
        if engine == ENGINE_NONE:
            engine_set_auto_combat(False, preferred_engine=ENGINE_HERO_AI, bot=ctx.bot)
            engine_set_auto_looting(False, preferred_engine=ENGINE_HERO_AI, bot=ctx.bot)
            engine_set_auto_following(False, preferred_engine=ENGINE_HERO_AI, bot=ctx.bot)

        # Optional runtime property sync for local bot flags.
        # Intentionally do NOT touch hero_ai active state here; this step pins
        # modular routing policy and should not flip external widgets.
        if ctx.bot.Properties.exists("auto_combat") and engine == ENGINE_HERO_AI:
            ctx.bot.Properties.ApplyNow("auto_combat", "active", False)
        debug_log_recipe(ctx, f"set_combat_engine pinned engine={engine!r}.")

    ctx.bot.States.AddCustomState(_set_engine, ctx.step.get("name", f"Set Combat Engine ({engine})"))
    wait_after_step(ctx.bot, ctx.step)


def handle_heroes_use_skill(ctx: StepContext) -> None:
    from Py4GWCoreLib import Party

    try:
        slot = parse_step_int(ctx.step.get("slot", 0), 0)
    except Exception:
        slot = 0
    if slot < 1 or slot > 8:
        debug_log_recipe(ctx, f"heroes_use_skill invalid slot at index {ctx.step_idx}: {ctx.step.get('slot')!r}")
        return

    target_id = parse_step_int(ctx.step.get("target_id", 0), 0)

    def _heroes_use_skill() -> None:
        heroes = Party.GetHeroes() or []
        used = 0
        for hero in heroes:
            hero_agent_id = int(getattr(hero, "agent_id", 0) or 0)
            if hero_agent_id <= 0:
                continue
            Party.Heroes.UseSkill(hero_agent_id, int(slot), int(target_id))
            used += 1
        if used == 0:
            debug_log_recipe(ctx, "heroes_use_skill skipped: no heroes available.")

    ctx.bot.States.AddCustomState(_heroes_use_skill, ctx.step.get("name", f"Heroes Use Skill {slot}"))
    wait_after_step(ctx.bot, ctx.step)


def handle_set_party_member_hooks(ctx: StepContext) -> None:
    enabled = parse_step_bool(ctx.step.get("enabled", True), True)
    owner = getattr(ctx.bot, "_modular_owner", None)
    if owner is None or not hasattr(owner, "set_party_member_hooks_enabled"):
        debug_log_recipe(ctx, f"set_party_member_hooks requires ModularBot owner; step index {ctx.step_idx}")
        return

    def _set_party_member_hooks() -> None:
        owner.set_party_member_hooks_enabled(enabled)

    label = str(ctx.step.get("name", f"{'Enable' if enabled else 'Disable'} Party Member Hooks") or "").strip()
    ctx.bot.States.AddCustomState(_set_party_member_hooks, label or "Set Party Member Hooks")
    wait_after_step(ctx.bot, ctx.step)


def handle_disable_party_member_hooks(ctx: StepContext) -> None:
    step = dict(ctx.step)
    step["enabled"] = False
    proxy_ctx = StepContext(
        bot=ctx.bot,
        step=step,
        step_idx=ctx.step_idx,
        recipe_name=ctx.recipe_name,
        step_type=ctx.step_type,
        step_display=ctx.step_display,
    )
    handle_set_party_member_hooks(proxy_ctx)


def handle_enable_party_member_hooks(ctx: StepContext) -> None:
    step = dict(ctx.step)
    step["enabled"] = True
    proxy_ctx = StepContext(
        bot=ctx.bot,
        step=step,
        step_idx=ctx.step_idx,
        recipe_name=ctx.recipe_name,
        step_type=ctx.step_type,
        step_display=ctx.step_display,
    )
    handle_set_party_member_hooks(proxy_ctx)


def handle_suppress_recovery(ctx: StepContext) -> None:
    owner = getattr(ctx.bot, "_modular_owner", None)
    if owner is None or not hasattr(owner, "suppress_recovery_for"):
        debug_log_recipe(ctx, f"suppress_recovery requires ModularBot owner; step index {ctx.step_idx}")
        return

    ms = max(0, parse_step_int(ctx.step.get("ms", 45_000), 45_000))
    max_events = max(0, parse_step_int(ctx.step.get("max_events", 20), 20))
    until_outpost = parse_step_bool(ctx.step.get("until_outpost", False), False)

    def _suppress() -> None:
        owner.suppress_recovery_for(ms=ms, max_events=max_events, until_outpost=until_outpost)
        debug_log_recipe(
            ctx,
            f"suppress_recovery active for {ms} ms, max_events={max_events}, until_outpost={until_outpost}.",
        )

    ctx.bot.States.AddCustomState(_suppress, ctx.step.get("name", "Suppress Recovery"))
    wait_after_step(ctx.bot, ctx.step)


modular_step(
    step_type="abandon_quest",
    category="party",
    allowed_params=("multibox", "name", "quest_id", "skip_leader"),
    node_class_name="AbandonQuestNode",
)(handle_abandon_quest)
modular_step(
    step_type="broadcast_summoning_stone",
    category="party",
    allowed_params=(
        "effect_id",
        "model_id",
        "model_ids",
        "models",
        "name",
        "per_message_wait_ms",
        "repeat",
        "repeat_delay_ms",
        "skip_leader",
        "summon_models",
    ),
    node_class_name="BroadcastSummoningStoneNode",
)(handle_broadcast_summoning_stone)
modular_step(
    step_type="disable_party_member_hooks",
    category="party",
    allowed_params=("name",),
    node_class_name="DisablePartyMemberHooksNode",
)(handle_disable_party_member_hooks)
modular_step(
    step_type="drop_bundle",
    category="party",
    allowed_params=("name",),
    node_class_name="DropBundleNode",
)(handle_drop_bundle)
modular_step(
    step_type="enable_party_member_hooks",
    category="party",
    allowed_params=("name",),
    node_class_name="EnablePartyMemberHooksNode",
)(handle_enable_party_member_hooks)
modular_step(
    step_type="flag_all_accounts",
    category="party",
    allowed_params=("engine", "name", "point"),
    node_class_name="FlagAllAccountsNode",
)(handle_flag_all_accounts)
modular_step(
    step_type="flag_heroes",
    category="party",
    allowed_params=("name", "point"),
    node_class_name="FlagHeroesNode",
)(handle_flag_heroes)
modular_step(
    step_type="force_hero_state",
    category="party",
    allowed_params=("behavior", "name", "state"),
    node_class_name="ForceHeroStateNode",
)(handle_force_hero_state)
modular_step(
    step_type="heroes_use_skill",
    category="party",
    allowed_params=("name", "slot", "target_id"),
    node_class_name="HeroesUseSkillNode",
)(handle_heroes_use_skill)
modular_step(
    step_type="load_party",
    category="party",
    allowed_params=(
        "add_delay_ms",
        "apply_templates",
        "clear_existing",
        "fill_with_henchmen",
        "henchmen",
        "henchman_ids",
        "hero_team",
        "max_heroes",
        "minionless",
        "name",
        "required_hero",
        "team",
        "team_mode",
        "team_selection",
        "use_priority",
        "wait_poll_ms",
        "wait_timeout_ms",
    ),
    node_class_name="LoadPartyNode",
)(handle_load_party)
modular_step(
    step_type="resign",
    category="party",
    allowed_params=("name", "skip_leader"),
    node_class_name="ResignNode",
)(handle_resign)
modular_step(
    step_type="set_anchor",
    category="party",
    allowed_params=("name", "phase", "target"),
    node_class_name="SetAnchorNode",
)(handle_set_anchor)
modular_step(
    step_type="set_combat_engine",
    category="party",
    allowed_params=("engine", "name", "value"),
    node_class_name="SetCombatEngineNode",
)(handle_set_combat_engine)
modular_step(
    step_type="set_hard_mode",
    category="party",
    allowed_params=("enabled", "name"),
    node_class_name="SetHardModeNode",
)(handle_set_hard_mode)
modular_step(
    step_type="set_party_member_hooks",
    category="party",
    allowed_params=("enabled", "name"),
    node_class_name="SetPartyMemberHooksNode",
)(handle_set_party_member_hooks)
modular_step(
    step_type="set_title",
    category="party",
    allowed_params=("id", "name"),
    node_class_name="SetTitleNode",
)(handle_set_title)
modular_step(
    step_type="summon_all_accounts",
    category="party",
    allowed_params=("ms", "name"),
    node_class_name="SummonAllAccountsNode",
)(handle_summon_all_accounts)
modular_step(
    step_type="invite_all_accounts",
    category="party",
    allowed_params=("ms", "name"),
    node_class_name="InviteAllAccountsNode",
)(handle_invite_all_accounts)
modular_step(
    step_type="suppress_recovery",
    category="party",
    allowed_params=("max_events", "ms", "name", "until_outpost"),
    node_class_name="SuppressRecoveryNode",
)(handle_suppress_recovery)
modular_step(
    step_type="wait_all_accounts_same_map",
    category="party",
    allowed_params=("include_self", "name", "poll_ms", "require_same_district", "timeout_ms"),
    node_class_name="WaitAllAccountsSameMapNode",
)(handle_wait_all_accounts_same_map)
modular_step(
    step_type="unflag_all_accounts",
    category="party",
    allowed_params=("engine", "name"),
    node_class_name="UnflagAllAccountsNode",
)(handle_unflag_all_accounts)
modular_step(
    step_type="unflag_heroes",
    category="party",
    allowed_params=("name",),
    node_class_name="UnflagHeroesNode",
)(handle_unflag_heroes)
modular_step(
    step_type="use_all_consumables",
    category="party",
    allowed_params=("leader_only", "multibox", "name"),
    node_class_name="UseAllConsumablesNode",
)(handle_use_all_consumables)
modular_step(
    step_type="use_consumables",
    category="party",
    allowed_params=("leader_only", "mode", "multibox", "name", "selector"),
    node_class_name="UseConsumablesNode",
)(handle_use_consumables)
modular_step(
    step_type="upkeep_consumables",
    category="party",
    allowed_params=("interval_ms", "mode", "ms", "multibox", "name", "poll_ms", "selector"),
    node_class_name="UpkeepConsumablesNode",
)(handle_upkeep_consumables)
modular_step(
    step_type="upkeep_cons",
    category="party",
    allowed_params=("interval_ms", "mode", "ms", "multibox", "name", "poll_ms", "selector"),
    node_class_name="UpkeepConsNode",
)(handle_upkeep_consumables)
modular_step(
    step_type="upkeep_pcons",
    category="party",
    allowed_params=("interval_ms", "mode", "ms", "multibox", "name", "poll_ms", "selector"),
    node_class_name="UpkeepPconsNode",
)(handle_upkeep_consumables)
