from __future__ import annotations

from typing import Iterable

from Py4GWCoreLib import ActionQueueManager, Agent, GLOBAL_CACHE, Key, Keystroke, Player, SharedCommandType
from Py4GWCoreLib.py4gwcorelib_src.WidgetManager import get_widget_handler

ENGINE_NONE = "none"
ENGINE_CUSTOM_BEHAVIORS = "custom_behaviors"
ENGINE_HERO_AI = "hero_ai"


def resolve_active_engine() -> str:
    """Detect active combat engine based on enabled widgets."""
    widget_handler = get_widget_handler()
    cb_enabled = bool(widget_handler.is_widget_enabled("CustomBehaviors"))
    hero_ai_enabled = bool(widget_handler.is_widget_enabled("HeroAI"))

    if cb_enabled:
        return ENGINE_CUSTOM_BEHAVIORS
    if hero_ai_enabled:
        return ENGINE_HERO_AI
    return ENGINE_NONE


def _iter_same_party_accounts(include_self: bool = False) -> list:
    my_email = Player.GetAccountEmail()
    me = GLOBAL_CACHE.ShMem.GetAccountDataFromEmail(my_email)
    if me is None:
        return []

    accounts: list = []
    for account in GLOBAL_CACHE.ShMem.GetAllAccountData():
        if not include_self and account.AccountEmail == my_email:
            continue

        same_party = int(account.AgentPartyData.PartyID) == int(me.AgentPartyData.PartyID)
        same_map = (
            int(account.AgentData.Map.MapID) == int(me.AgentData.Map.MapID)
            and int(account.AgentData.Map.Region) == int(me.AgentData.Map.Region)
            and int(account.AgentData.Map.District) == int(me.AgentData.Map.District)
            and int(account.AgentData.Map.Language) == int(me.AgentData.Map.Language)
        )
        if same_party and same_map:
            accounts.append(account)
    return accounts


def is_party_looting_enabled() -> bool:
    """
    Return whether looting is currently enabled for the active combat backend.
    """
    engine = resolve_active_engine()
    if engine == ENGINE_CUSTOM_BEHAVIORS:
        try:
            from Sources.oazix.CustomBehaviors.primitives.parties.custom_behavior_party import (
                CustomBehaviorParty,
            )

            return bool(CustomBehaviorParty().get_party_is_looting_enabled())
        except Exception:
            return False

    if engine == ENGINE_HERO_AI:
        try:
            my_email = Player.GetAccountEmail()
            options = GLOBAL_CACHE.ShMem.GetHeroAIOptionsFromEmail(my_email)
            return bool(getattr(options, "Looting", False)) if options is not None else False
        except Exception:
            return False

    return False


def party_loot_wait_required(search_range: float | None = None) -> bool:
    """
    Check whether party-shared loot is still pending near the player.
    Mirrors CB utility logic used by WaitIfPartyMemberNeedsToLootUtility.
    """
    if not is_party_looting_enabled():
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


def _set_hero_ai_option_for_same_party(option_name: str, value) -> int:
    changed = 0
    for account in _iter_same_party_accounts(include_self=True):
        options = GLOBAL_CACHE.ShMem.GetHeroAIOptionsFromEmail(account.AccountEmail)
        if options is None or not hasattr(options, option_name):
            continue
        setattr(options, option_name, value)
        changed += 1
    return changed


def set_auto_combat(enabled: bool) -> None:
    engine = resolve_active_engine()
    if engine == ENGINE_CUSTOM_BEHAVIORS:
        from Sources.oazix.CustomBehaviors.primitives.parties.custom_behavior_party import (
            CustomBehaviorParty,
        )

        CustomBehaviorParty().set_party_is_combat_enabled(bool(enabled))
        return

    if engine == ENGINE_HERO_AI:
        _set_hero_ai_option_for_same_party("Combat", bool(enabled))


def set_auto_looting(enabled: bool) -> None:
    engine = resolve_active_engine()
    if engine == ENGINE_CUSTOM_BEHAVIORS:
        from Sources.oazix.CustomBehaviors.primitives.parties.custom_behavior_party import (
            CustomBehaviorParty,
        )

        CustomBehaviorParty().set_party_is_looting_enabled(bool(enabled))
        return

    if engine == ENGINE_HERO_AI:
        _set_hero_ai_option_for_same_party("Looting", bool(enabled))


def set_party_target(target_agent_id: int) -> None:
    engine = resolve_active_engine()
    if engine == ENGINE_CUSTOM_BEHAVIORS:
        from Sources.oazix.CustomBehaviors.primitives.parties.custom_behavior_party import (
            CustomBehaviorParty,
        )

        CustomBehaviorParty().set_party_custom_target(int(target_agent_id))
        return

    if engine == ENGINE_HERO_AI:
        # HeroAI follows GW's called target; emulate Ctrl+Space on current target.
        ActionQueueManager().AddAction("ACTION", Keystroke.PressAndReleaseCombo, [Key.Ctrl.value, Key.Space.value])


def flag_all_accounts(x: float, y: float) -> int:
    engine = resolve_active_engine()
    if engine == ENGINE_CUSTOM_BEHAVIORS:
        from Sources.oazix.CustomBehaviors.primitives.parties.custom_behavior_party import (
            CustomBehaviorParty,
        )

        party = CustomBehaviorParty()
        manager = party.party_flagging_manager
        manager.auto_assign_emails_if_none_assigned()

        changed = 0
        for flag_index in range(12):
            account_email = str(manager.get_flag_account_email(flag_index) or "")
            if not account_email:
                continue
            manager.set_flag_position(flag_index, float(x), float(y))
            changed += 1
        return changed

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


def unflag_all_accounts() -> int:
    engine = resolve_active_engine()
    if engine == ENGINE_CUSTOM_BEHAVIORS:
        from Sources.oazix.CustomBehaviors.primitives.parties.custom_behavior_party import (
            CustomBehaviorParty,
        )

        CustomBehaviorParty().party_flagging_manager.clear_all_flag_positions()
        return 1

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
