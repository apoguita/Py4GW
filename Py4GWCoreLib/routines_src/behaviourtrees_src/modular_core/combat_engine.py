"""
combat_engine module

This module is part of the modular runtime surface.
"""
from __future__ import annotations

from typing import Iterable

from Py4GWCoreLib import ActionQueueManager, GLOBAL_CACHE, Key, Keystroke, Player, SharedCommandType
from Py4GWCoreLib.GlobalCache.shared_memory_src.Globals import SHMEM_MAX_NUMBER_OF_SKILLS

ENGINE_NONE = "none"
ENGINE_HERO_AI = "hero_ai"


def resolve_active_engine() -> str:
    """Detect active combat engine based on enabled widgets."""
    from Py4GWCoreLib.py4gwcorelib_src.WidgetManager import get_widget_handler

    widget_handler = get_widget_handler()
    hero_ai_enabled = bool(widget_handler.is_widget_enabled("HeroAI"))

    if hero_ai_enabled:
        return ENGINE_HERO_AI
    return ENGINE_NONE


def resolve_engine_for_bot(bot=None, preferred_engine: str | None = None) -> str:
    """
    Resolve combat engine using explicit preference first, then bot-pinned startup
    engine, then live widget detection.
    """
    explicit = str(preferred_engine or "").strip().lower()
    if explicit in (ENGINE_HERO_AI, ENGINE_NONE):
        return explicit

    cfg = getattr(bot, "config", None) if bot is not None else None
    pinned = str(getattr(cfg, "_modular_start_engine", "") or "").strip().lower()
    if pinned in (ENGINE_HERO_AI, ENGINE_NONE):
        return pinned

    return resolve_active_engine()


def _iter_same_party_accounts(include_self: bool = False) -> list:
    my_email = Player.GetAccountEmail()
    me = GLOBAL_CACHE.ShMem.GetAccountDataFromEmail(my_email)
    if me is None:
        return []
    my_party_id = int(getattr(me.AgentPartyData, "PartyID", 0) or 0)
    if my_party_id <= 0:
        return []

    accounts: list = []
    for account in GLOBAL_CACHE.ShMem.GetAllAccountData():
        if not include_self and account.AccountEmail == my_email:
            continue

        same_party = int(account.AgentPartyData.PartyID) == my_party_id
        same_map = (
            int(account.AgentData.Map.MapID) == int(me.AgentData.Map.MapID)
            and int(account.AgentData.Map.Region) == int(me.AgentData.Map.Region)
            and int(account.AgentData.Map.District) == int(me.AgentData.Map.District)
            and int(account.AgentData.Map.Language) == int(me.AgentData.Map.Language)
        )
        if same_party and same_map:
            accounts.append(account)
    return accounts


def _iter_same_party_accounts_any_map(include_self: bool = False) -> list:
    my_email = Player.GetAccountEmail()
    me = GLOBAL_CACHE.ShMem.GetAccountDataFromEmail(my_email)
    if me is None:
        return []
    my_party_id = int(getattr(me.AgentPartyData, "PartyID", 0) or 0)
    if my_party_id <= 0:
        return []

    accounts: list = []
    for account in GLOBAL_CACHE.ShMem.GetAllAccountData():
        if not include_self and account.AccountEmail == my_email:
            continue
        if int(getattr(account.AgentPartyData, "PartyID", 0) or 0) != my_party_id:
            continue
        accounts.append(account)
    return accounts


def _iter_same_isolation_group_accounts(include_self: bool = False) -> list:
    my_email = Player.GetAccountEmail()
    me = GLOBAL_CACHE.ShMem.GetAccountDataFromEmail(my_email)
    if me is None:
        return []
    my_group_id = int(getattr(me, "IsolationGroupID", 0) or 0)
    if my_group_id <= 0:
        return []

    accounts: list = []
    for account in GLOBAL_CACHE.ShMem.GetAllAccountData():
        if not include_self and account.AccountEmail == my_email:
            continue
        if int(getattr(account, "IsolationGroupID", 0) or 0) != my_group_id:
            continue
        accounts.append(account)
    return accounts


def _iter_toggle_target_accounts(include_self: bool = False) -> tuple[list, str]:
    # Toggle fan-out is resilient to map transitions:
    # 1) same-party across maps, 2) same isolation group fallback.
    party_accounts = _iter_same_party_accounts_any_map(include_self=include_self)
    if party_accounts:
        return party_accounts, "party"

    group_accounts = _iter_same_isolation_group_accounts(include_self=include_self)
    if group_accounts:
        return group_accounts, "group_fallback"

    return [], "none"


def is_party_looting_enabled(bot=None, preferred_engine: str | None = None) -> bool:
    """
    Return whether looting is currently enabled for the active combat backend.
    """
    engine = resolve_engine_for_bot(bot, preferred_engine)
    if engine == ENGINE_HERO_AI:
        try:
            my_email = Player.GetAccountEmail()
            options = GLOBAL_CACHE.ShMem.GetHeroAIOptionsFromEmail(my_email)
            return bool(getattr(options, "Looting", False)) if options is not None else False
        except Exception:
            return False

    return False


def party_loot_wait_required(
    search_range: float | None = None,
    *,
    bot=None,
    preferred_engine: str | None = None,
) -> bool:
    """
    Check whether party-shared loot is still pending near the player.
    Mirrors CB utility logic used by WaitIfPartyMemberNeedsToLootUtility.
    """
    if not is_party_looting_enabled(bot=bot, preferred_engine=preferred_engine):
        return False

    try:
        from Py4GWCoreLib import Range
        from Py4GWCoreLib.Py4GWcorelib import LootConfig

        loot_range = float(search_range) if search_range is not None else float(Range.Spellcast.value)
        loot_array = LootConfig().GetfilteredLootArray(
            loot_range,
            multibox_loot=True,
            allow_unasigned_loot=True,
        )
        return len(loot_array) > 1
    except Exception:
        return False


def _apply_hero_ai_toggle_option(options, option_name: str, value) -> bool:
    changed = False
    bool_value = bool(value)

    if hasattr(options, option_name):
        current_value = getattr(options, option_name)
        if bool(current_value) != bool_value:
            changed = True
        setattr(options, option_name, bool_value)

    if option_name == "Combat":
        for linked_option in ("Targeting", "Avoidance"):
            if hasattr(options, linked_option):
                current_value = getattr(options, linked_option)
                if bool(current_value) != bool_value:
                    changed = True
                setattr(options, linked_option, bool_value)

        skills = getattr(options, "Skills", None)
        if skills is not None:
            for skill_index in range(SHMEM_MAX_NUMBER_OF_SKILLS):
                if bool(skills[skill_index]) != bool_value:
                    changed = True
                skills[skill_index] = bool_value

    return changed


def _set_hero_ai_option_for_toggle_targets(option_name: str, value) -> dict[str, int | str]:
    changed = 0
    targeted = 0
    accounts, selector = _iter_toggle_target_accounts(include_self=True)
    for account in accounts:
        account_email = str(getattr(account, "AccountEmail", "") or "").strip()
        if not account_email:
            continue
        options = GLOBAL_CACHE.ShMem.GetHeroAIOptionsFromEmail(account.AccountEmail)
        if options is None or not hasattr(options, option_name):
            continue
        targeted += 1
        if _apply_hero_ai_toggle_option(options, option_name, value):
            changed += 1
        GLOBAL_CACHE.ShMem.SetHeroAIOptionsByEmail(account_email, options)
    return {
        "selector": selector,
        "targeted": int(targeted),
        "updated": int(changed),
    }


def set_auto_combat(enabled: bool, preferred_engine: str | None = None, bot=None) -> dict[str, int | str]:
    engine = resolve_engine_for_bot(bot, preferred_engine)
    if engine == ENGINE_HERO_AI:
        result = _set_hero_ai_option_for_toggle_targets("Combat", bool(enabled))
        result["backend"] = ENGINE_HERO_AI
        return result

    return {
        "backend": engine,
        "selector": "none",
        "targeted": 0,
        "updated": 0,
    }


def set_auto_looting(enabled: bool, preferred_engine: str | None = None, bot=None) -> dict[str, int | str]:
    engine = resolve_engine_for_bot(bot, preferred_engine)
    if engine == ENGINE_HERO_AI:
        result = _set_hero_ai_option_for_toggle_targets("Looting", bool(enabled))
        result["backend"] = ENGINE_HERO_AI
        return result

    return {
        "backend": engine,
        "selector": "none",
        "targeted": 0,
        "updated": 0,
    }


def set_auto_following(enabled: bool, preferred_engine: str | None = None, bot=None) -> dict[str, int | str]:
    engine = resolve_engine_for_bot(bot, preferred_engine)
    if engine == ENGINE_HERO_AI:
        result = _set_hero_ai_option_for_toggle_targets("Following", bool(enabled))
        result["backend"] = ENGINE_HERO_AI
        return result

    return {
        "backend": engine,
        "selector": "none",
        "targeted": 0,
        "updated": 0,
    }


def set_party_target(target_agent_id: int, preferred_engine: str | None = None, bot=None) -> None:
    engine = resolve_engine_for_bot(bot, preferred_engine)
    if engine == ENGINE_HERO_AI:
        # HeroAI follows GW's called target; emulate Ctrl+Space on current target.
        ActionQueueManager().AddAction("ACTION", Keystroke.PressAndReleaseCombo, [Key.Ctrl.value, Key.Space.value])


def flag_all_accounts(x: float, y: float, preferred_engine: str | None = None, bot=None) -> int:
    engine = resolve_engine_for_bot(bot, preferred_engine)
    if engine == ENGINE_HERO_AI:
        # HeroAI backend: use PixelStack command instead of HeroAI flag fields.
        # This mirrors the desired "stack alts to coordinates" behavior for FoW.
        sender_email = Player.GetAccountEmail()
        changed = 0
        for account in _iter_same_party_accounts(include_self=False):
            receiver_email = str(getattr(account, "AccountEmail", "") or "").strip()
            if not receiver_email:
                continue
            message_index = GLOBAL_CACHE.ShMem.SendMessage(
                sender_email,
                receiver_email,
                SharedCommandType.PixelStack,
                (float(x), float(y), 0.0, 0.0),
            )
            if int(message_index) >= 0:
                changed += 1
        return changed

    return 0


def unflag_all_accounts(preferred_engine: str | None = None, bot=None) -> int:
    engine = resolve_engine_for_bot(bot, preferred_engine)
    if engine == ENGINE_HERO_AI:
        changed = 0
        for account in _iter_same_party_accounts(include_self=True):
            options = GLOBAL_CACHE.ShMem.GetHeroAIOptionsFromEmail(account.AccountEmail)
            if options is None:
                continue
            options.IsFlagged = False
            options.FlagPos.x = 0.0
            options.FlagPos.y = 0.0
            options.AllFlag.x = 0.0
            options.AllFlag.y = 0.0
            options.FlagFacingAngle = 0.0
            changed += 1
        return changed

    return 0


def send_multibox_command(
    command: SharedCommandType,
    params: tuple[float, float, float, float] = (0.0, 0.0, 0.0, 0.0),
    extra_data: tuple[str, str, str, str] = ("", "", "", ""),
    recipients: Iterable[str] | None = None,
) -> list[tuple[str, int]]:
    sender_email = Player.GetAccountEmail()
    refs: list[tuple[str, int]] = []

    if recipients is None:
        recipients = [
            str(getattr(account, "AccountEmail", "") or "")
            for account in GLOBAL_CACHE.ShMem.GetAllAccountData()
            if str(getattr(account, "AccountEmail", "") or "") != sender_email
        ]

    for account_email in recipients:
        if not account_email or account_email == sender_email:
            continue
        message_index = GLOBAL_CACHE.ShMem.SendMessage(
            sender_email,
            account_email,
            command,
            params,
            extra_data,
        )
        refs.append((account_email, int(message_index)))
    return refs


def outbound_messages_done(refs: list[tuple[str, int]], command: SharedCommandType) -> bool:
    if not refs:
        return True

    sender_email = Player.GetAccountEmail()
    for account_email, message_index in refs:
        if message_index < 0:
            continue
        message = GLOBAL_CACHE.ShMem.GetInbox(message_index)
        is_same_message = (
            bool(getattr(message, "Active", False))
            and str(getattr(message, "ReceiverEmail", "") or "") == account_email
            and str(getattr(message, "SenderEmail", "") or "") == sender_email
            and int(getattr(message, "Command", -1)) == int(command)
        )
        if is_same_message:
            return False
    return True
