"""
actions_party module

This module is part of the modular runtime surface.
"""
from __future__ import annotations

from time import monotonic

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


def _account_map_tuple(account) -> tuple[int, int, int, int]:
    map_obj = getattr(getattr(account, "AgentData", None), "Map", None)
    return (
        int(getattr(account, "MapID", 0) or getattr(map_obj, "MapID", 0) or 0),
        int(getattr(account, "MapRegion", 0) or getattr(map_obj, "Region", 0) or 0),
        int(getattr(account, "MapDistrict", 0) or getattr(map_obj, "District", 0) or 0),
        int(getattr(account, "MapLanguage", 0) or getattr(map_obj, "Language", 0) or 0),
    )


def _current_map_tuple() -> tuple[int, int, int, int]:
    from Py4GWCoreLib import Map

    return (
        int(Map.GetMapID() or 0),
        int(Map.GetRegion()[0] or 0),
        int(Map.GetDistrict() or 0),
        int(Map.GetLanguage()[0] or 0),
    )


def _same_map(actual: tuple[int, int, int, int], expected: tuple[int, int, int, int], exact: bool) -> bool:
    if actual[0] <= 0 or actual[0] != expected[0]:
        return False
    return not exact or actual[1:] == expected[1:]


def handle_set_title(ctx: StepContext) -> None:
    ctx.bot.Player.SetTitle(ctx.step["id"])
    wait_after_step(ctx.bot, ctx.step)


def handle_drop_bundle(ctx: StepContext) -> None:
    from Py4GWCoreLib import Key, Keystroke

    ctx.bot.States.AddCustomState(lambda: Keystroke.PressAndRelease(getattr(Key, "F2").value), "F2 Drop Bundle")
    ctx.bot.Wait.ForTime(200)
    ctx.bot.States.AddCustomState(lambda: Keystroke.PressAndRelease(getattr(Key, "F1").value), "F1 Drop Bundle")
    ctx.bot.Wait.ForTime(200)
    wait_after_step(ctx.bot, ctx.step)


def handle_force_hero_state(ctx: StepContext) -> None:
    from Py4GWCoreLib import Party

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

    def _set_hero_behavior_all(behavior_value: int = behavior) -> None:
        for hero in Party.GetHeroes():
            hero_agent_id = getattr(hero, "agent_id", 0)
            if hero_agent_id:
                Party.Heroes.SetHeroBehavior(hero_agent_id, behavior_value)

    ctx.bot.States.AddCustomState(_set_hero_behavior_all, state_name)
    wait_after_step(ctx.bot, ctx.step)


def handle_flag_heroes(ctx: StepContext) -> None:
    from Py4GWCoreLib import Map, Party

    def _flag_heroes() -> None:
        if not Map.IsExplorable():
            debug_log_recipe(ctx, "flag_heroes skipped: map is not explorable.")
            return

        hero_count = int(Party.GetHeroCount() or 0)
        if hero_count <= 0:
            debug_log_recipe(ctx, "flag_heroes skipped: no heroes in party.")
            return

        coords = parse_step_point(ctx.step)
        if coords is None:
            debug_log_recipe(ctx, f"flag_heroes invalid coordinates at index {ctx.step_idx}: expected point [x, y].")
            return
        x, y = coords

        Party.Heroes.FlagAllHeroes(x, y)

    ctx.bot.States.AddCustomState(_flag_heroes, ctx.step.get("name", "Flag Heroes"))
    wait_after_step(ctx.bot, ctx.step)


def handle_flag_all_accounts(ctx: StepContext) -> None:
    def _flag_all_accounts() -> None:
        coords = parse_step_point(ctx.step)
        if coords is None:
            debug_log_recipe(
                ctx,
                f"flag_all_accounts invalid coordinates at index {ctx.step_idx}: expected point [x, y].",
            )
            return
        x, y = coords
        engine = resolve_engine_for_bot(ctx.bot)
        changed = 0
        try:
            # HeroAI is the only supported modular combat backend.
            changed += int(engine_flag_all_accounts(x, y, preferred_engine=engine, bot=ctx.bot))
            if engine != ENGINE_HERO_AI:
                changed += int(engine_flag_all_accounts(x, y, preferred_engine=ENGINE_HERO_AI, bot=ctx.bot))
        except Exception as exc:
            debug_log_recipe(ctx, f"flag_all_accounts failed at index {ctx.step_idx}: {exc}")
            return

        if changed:
            debug_log_recipe(ctx, f"flag_all_accounts applied to {changed} account(s).")
        else:
            debug_log_recipe(ctx, "flag_all_accounts had no eligible accounts.")

    ctx.bot.States.AddCustomState(
        _flag_all_accounts,
        ctx.step.get("name", "Flag All Accounts"),
    )
    wait_after_step(ctx.bot, ctx.step)


def handle_unflag_heroes(ctx: StepContext) -> None:
    from Py4GWCoreLib import Party

    def _unflag_heroes() -> None:
        Party.Heroes.UnflagAllHeroes()

    ctx.bot.States.AddCustomState(_unflag_heroes, ctx.step.get("name", "Unflag Heroes"))
    wait_after_step(ctx.bot, ctx.step)


def handle_unflag_all_accounts(ctx: StepContext) -> None:
    def _unflag_all_accounts() -> None:
        engine = resolve_engine_for_bot(ctx.bot)
        changed = int(engine_unflag_all_accounts(preferred_engine=engine, bot=ctx.bot))
        if engine != ENGINE_HERO_AI:
            changed += int(engine_unflag_all_accounts(preferred_engine=ENGINE_HERO_AI, bot=ctx.bot))
        debug_log_recipe(ctx, f"unflag_all_accounts cleared flags for {changed} account(s).")

    ctx.bot.States.AddCustomState(
        _unflag_all_accounts,
        ctx.step.get("name", "Unflag All Accounts"),
    )
    wait_after_step(ctx.bot, ctx.step)


def handle_resign(ctx: StepContext) -> None:
    ctx.bot.Multibox.ResignParty()
    wait_after_step(ctx.bot, ctx.step)


def handle_summon_all_accounts(ctx: StepContext) -> None:
    ctx.bot.Multibox.SummonAllAccounts()
    wait_after_step(ctx.bot, ctx.step)


def handle_wait_all_accounts_same_map(ctx: StepContext) -> None:
    from Py4GWCoreLib import GLOBAL_CACHE, Player

    timeout_ms = max(0, parse_step_int(ctx.step.get("timeout_ms", 60000), 60000))
    poll_ms = max(100, parse_step_int(ctx.step.get("poll_ms", 500), 500))
    include_self = parse_step_bool(ctx.step.get("include_self", False), False)
    exact = parse_step_bool(ctx.step.get("require_same_district", False), False)

    def _account_emails() -> list[str]:
        my_email = str(Player.GetAccountEmail() or "").strip()
        emails: list[str] = []
        for account in GLOBAL_CACHE.ShMem.GetAllAccountData():
            email = str(getattr(account, "AccountEmail", "") or "").strip()
            if not email or (email == my_email and not include_self):
                continue
            if email not in emails:
                emails.append(email)
        return emails

    def _wait_all_accounts_same_map():
        expected = _current_map_tuple()
        recipients = _account_emails()
        deadline = monotonic() + (timeout_ms / 1000.0)
        if not recipients:
            debug_log_recipe(ctx, "wait_all_accounts_same_map: no accounts to verify.")
            return
        while True:
            expected = _current_map_tuple() or expected
            missing = [
                email
                for email in recipients
                if not _same_map(
                    _account_map_tuple(GLOBAL_CACHE.ShMem.GetAccountDataFromEmail(email)),
                    expected,
                    exact,
                )
            ]
            if not missing:
                debug_log_recipe(ctx, f"wait_all_accounts_same_map: all {len(recipients)} account(s) arrived.")
                return
            if timeout_ms <= 0 or monotonic() >= deadline:
                debug_log_recipe(ctx, "wait_all_accounts_same_map timed out; missing=" + ", ".join(missing))
                return
            yield from ctx.bot.Wait._coro_for_time(poll_ms)

    ctx.bot.States.AddCustomState(
        _wait_all_accounts_same_map,
        ctx.step.get("name", "Wait All Accounts Same Map"),
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

    def _abandon_quest():
        if multibox:
            yield from ctx.bot.helpers.Multibox._abandon_quest_message(quest_id, skip_leader=skip_leader)
            return
        ctx.bot.Quest.AbandonQuest(quest_id)
        yield

    ctx.bot.States.AddCustomState(_abandon_quest, ctx.step.get("name", f"Abandon Quest {quest_id}"))
    wait_after_step(ctx.bot, ctx.step)


def handle_broadcast_summoning_stone(ctx: StepContext) -> None:
    from Py4GWCoreLib import GLOBAL_CACHE, Map, ModelID, Player, SharedCommandType

    default_models = [
        int(ModelID.Legionnaire_Summoning_Crystal.value),
        int(ModelID.Igneous_Summoning_Stone.value),
        int(ModelID.Tengu_Summon.value),
    ]
    raw_models = ctx.step.get("models", ctx.step.get("summon_models", default_models))
    effect_id = max(0, parse_step_int(ctx.step.get("effect_id", 2886), 2886))
    repeat = max(1, parse_step_int(ctx.step.get("repeat", 1), 1))
    per_message_wait_ms = max(0, parse_step_int(ctx.step.get("per_message_wait_ms", 250), 250))

    def _resolve_models(raw_value) -> list[int]:
        if raw_value is None:
            return list(default_models)
        if not isinstance(raw_value, list):
            raw_items = [raw_value]
        else:
            raw_items = list(raw_value)

        resolved: list[int] = []
        for entry in raw_items:
            mid = parse_step_int(entry, 0)
            if mid > 0:
                if mid not in resolved:
                    resolved.append(mid)
                continue

            if isinstance(entry, str):
                token = entry.strip()
                if token.lower().startswith("modelid."):
                    token = token.split(".", 1)[1]
                model_obj = getattr(ModelID, token, None)
                if model_obj is not None:
                    mid = int(getattr(model_obj, "value", model_obj))
                    if mid > 0 and mid not in resolved:
                        resolved.append(mid)

        return resolved

    model_ids = _resolve_models(raw_models)
    if not model_ids:
        debug_log_recipe(ctx, "broadcast_summoning_stone skipped: no valid model IDs resolved.")
        return

    def _broadcast_summoning_stone():
        sender_email = str(Player.GetAccountEmail() or "")
        sender_data = GLOBAL_CACHE.ShMem.GetAccountDataFromEmail(sender_email)
        sender_party_id = int(getattr(getattr(sender_data, "AgentPartyData", None), "PartyID", 0) or 0)
        map_id = int(Map.GetMapID() or 0)
        map_region = int(Map.GetRegion()[0] or 0)
        map_district = int(Map.GetDistrict() or 0)
        map_language = int(Map.GetLanguage()[0] or 0)

        def _account_map_tuple(account) -> tuple[int, int, int, int]:
            map_obj = getattr(getattr(account, "AgentData", None), "Map", None)
            acc_map_id = int(
                getattr(account, "MapID", 0)
                or getattr(map_obj, "MapID", 0)
                or 0
            )
            acc_region = int(
                getattr(account, "MapRegion", 0)
                or getattr(map_obj, "Region", 0)
                or 0
            )
            acc_district = int(
                getattr(account, "MapDistrict", 0)
                or getattr(map_obj, "District", 0)
                or 0
            )
            acc_language = int(
                getattr(account, "MapLanguage", 0)
                or getattr(map_obj, "Language", 0)
                or 0
            )
            return acc_map_id, acc_region, acc_district, acc_language

        recipients = []
        for account in GLOBAL_CACHE.ShMem.GetAllAccountData():
            account_email = str(getattr(account, "AccountEmail", "") or "")
            if not account_email or account_email == sender_email:
                continue
            acc_map_id, acc_region, acc_district, acc_language = _account_map_tuple(account)
            if acc_map_id != map_id:
                continue
            if acc_region != map_region:
                continue
            if acc_district != map_district:
                continue
            if acc_language != map_language:
                continue
            account_party_id = int(getattr(getattr(account, "AgentPartyData", None), "PartyID", 0) or 0)
            if sender_party_id and account_party_id and account_party_id != sender_party_id:
                continue
            recipients.append(account_email)

        if not recipients:
            debug_log_recipe(ctx, "broadcast_summoning_stone: no eligible recipients.")
            return

        for account_email in recipients:
            for model_id in model_ids:
                GLOBAL_CACHE.ShMem.SendMessage(
                    sender_email,
                    account_email,
                    SharedCommandType.UseItem,
                    (int(model_id), int(repeat), int(effect_id), 0),
                    ("modular_summoning_broadcast", "", "", ""),
                )
                if per_message_wait_ms > 0:
                    yield from ctx.bot.Wait._coro_for_time(per_message_wait_ms)

        debug_log_recipe(
            ctx,
            (
                "broadcast_summoning_stone sent "
                f"{len(model_ids)} model request(s) to {len(recipients)} account(s); "
                f"effect_id={effect_id}, repeat={repeat}."
            ),
        )

    ctx.bot.States.AddCustomState(_broadcast_summoning_stone, ctx.step.get("name", "Broadcast Summoning Stone"))
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
