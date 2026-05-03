"""
Reusable combat-toggle helpers for Botting-style runtimes.
"""
from __future__ import annotations

import time

from Py4GWCoreLib import GLOBAL_CACHE, Player
from Py4GWCoreLib.GlobalCache.shared_memory_src.Globals import SHMEM_MAX_NUMBER_OF_SKILLS


ENGINE_NONE = "none"
ENGINE_HERO_AI = "hero_ai"


DESIRED_AUTO_COMBAT_KEY = "_modular_desired_auto_combat"
DESIRED_AUTO_LOOTING_KEY = "_modular_desired_auto_looting"
DESIRED_AUTO_FOLLOWING_KEY = "_modular_desired_auto_following"
TOGGLE_RECONCILE_AT_KEY = "_modular_last_toggle_reconcile_at"


def resolve_active_engine() -> str:
    from Py4GWCoreLib.py4gwcorelib_src.WidgetManager import get_widget_handler

    return ENGINE_HERO_AI if bool(get_widget_handler().is_widget_enabled("HeroAI")) else ENGINE_NONE


def resolve_engine_for_bot(bot=None, preferred_engine: str | None = None) -> str:
    explicit = str(preferred_engine or "").strip().lower()
    if explicit in (ENGINE_HERO_AI, ENGINE_NONE):
        return explicit
    cfg = getattr(bot, "config", None) if bot is not None else None
    pinned = str(getattr(cfg, "_modular_start_engine", "") or "").strip().lower()
    if pinned in (ENGINE_HERO_AI, ENGINE_NONE):
        return pinned
    return resolve_active_engine()


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
        if int(getattr(account.AgentPartyData, "PartyID", 0) or 0) == my_party_id:
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
        if int(getattr(account, "IsolationGroupID", 0) or 0) == my_group_id:
            accounts.append(account)
    return accounts


def _iter_toggle_target_accounts(include_self: bool = False) -> tuple[list, str]:
    party_accounts = _iter_same_party_accounts_any_map(include_self=include_self)
    if party_accounts:
        return party_accounts, "party"
    group_accounts = _iter_same_isolation_group_accounts(include_self=include_self)
    if group_accounts:
        return group_accounts, "group_fallback"
    return [], "none"


def is_party_looting_enabled(bot=None, preferred_engine: str | None = None) -> bool:
    engine = resolve_engine_for_bot(bot, preferred_engine)
    if engine == ENGINE_HERO_AI:
        try:
            options = GLOBAL_CACHE.ShMem.GetHeroAIOptionsFromEmail(Player.GetAccountEmail())
            return bool(getattr(options, "Looting", False)) if options is not None else False
        except Exception:
            return False
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
    return {"selector": selector, "targeted": int(targeted), "updated": int(changed)}


def set_auto_combat(enabled: bool, preferred_engine: str | None = None, bot=None) -> dict[str, int | str]:
    engine = resolve_engine_for_bot(bot, preferred_engine)
    if engine == ENGINE_HERO_AI:
        result = _set_hero_ai_option_for_toggle_targets("Combat", bool(enabled))
        result["backend"] = ENGINE_HERO_AI
        return result
    return {"backend": engine, "selector": "none", "targeted": 0, "updated": 0}


def set_auto_looting(enabled: bool, preferred_engine: str | None = None, bot=None) -> dict[str, int | str]:
    engine = resolve_engine_for_bot(bot, preferred_engine)
    if engine == ENGINE_HERO_AI:
        result = _set_hero_ai_option_for_toggle_targets("Looting", bool(enabled))
        result["backend"] = ENGINE_HERO_AI
        return result
    return {"backend": engine, "selector": "none", "targeted": 0, "updated": 0}


def set_auto_following(enabled: bool, preferred_engine: str | None = None, bot=None) -> dict[str, int | str]:
    engine = resolve_engine_for_bot(bot, preferred_engine)
    if engine == ENGINE_HERO_AI:
        result = _set_hero_ai_option_for_toggle_targets("Following", bool(enabled))
        result["backend"] = ENGINE_HERO_AI
        return result
    return {"backend": engine, "selector": "none", "targeted": 0, "updated": 0}


def set_desired_toggle(bot, key: str, enabled: bool) -> None:
    cfg = getattr(bot, "config", None)
    if cfg is not None:
        setattr(cfg, key, bool(enabled))


def get_desired_toggle(bot, key: str, default: bool = True) -> bool:
    cfg = getattr(bot, "config", None)
    if cfg is None or not hasattr(cfg, key):
        return bool(default)
    return bool(getattr(cfg, key))


def current_auto_combat_enabled(bot) -> bool:
    cfg = getattr(bot, "config", None)
    if cfg is not None and hasattr(cfg, DESIRED_AUTO_COMBAT_KEY):
        return bool(getattr(cfg, DESIRED_AUTO_COMBAT_KEY))
    engine = resolve_engine_for_bot(bot)
    if engine == ENGINE_HERO_AI:
        try:
            from Py4GWCoreLib import GLOBAL_CACHE, Player

            options = GLOBAL_CACHE.ShMem.GetHeroAIOptionsFromEmail(Player.GetAccountEmail())
            if options is not None:
                return bool(getattr(options, "Combat", False))
        except Exception:
            pass
        if bot.Properties.exists("hero_ai"):
            return bool(bot.Properties.IsActive("hero_ai"))
        return False
    if bot.Properties.exists("auto_combat"):
        return bool(bot.Properties.IsActive("auto_combat"))
    if bot.Properties.exists("hero_ai"):
        return bool(bot.Properties.IsActive("hero_ai"))
    return False


def current_auto_looting_enabled(bot) -> bool:
    cfg = getattr(bot, "config", None)
    if cfg is not None and hasattr(cfg, DESIRED_AUTO_LOOTING_KEY):
        return bool(getattr(cfg, DESIRED_AUTO_LOOTING_KEY))
    engine = resolve_engine_for_bot(bot)
    if engine == ENGINE_HERO_AI:
        try:
            return bool(is_party_looting_enabled(bot=bot, preferred_engine=engine))
        except Exception:
            return False
    if bot.Properties.exists("auto_loot"):
        return bool(bot.Properties.IsActive("auto_loot"))
    return False


def normalize_backend_toggle_result(raw_result, backend: str) -> dict[str, str | int]:
    if isinstance(raw_result, dict):
        return {
            "backend": str(raw_result.get("backend", backend) or backend),
            "selector": str(raw_result.get("selector", "none") or "none"),
            "targeted": int(raw_result.get("targeted", 0) or 0),
            "updated": int(raw_result.get("updated", 0) or 0),
        }
    return {"backend": str(backend), "selector": "none", "targeted": 0, "updated": 0}


def build_toggle_summary(toggle: str, enabled: bool, results: list[dict[str, str | int]]) -> dict:
    targeted = int(sum(int(entry.get("targeted", 0) or 0) for entry in results))
    updated = int(sum(int(entry.get("updated", 0) or 0) for entry in results))
    zero_targets = any(
        str(entry.get("backend", "")) == ENGINE_HERO_AI and int(entry.get("targeted", 0) or 0) == 0
        for entry in results
    )
    return {
        "toggle": str(toggle),
        "enabled": bool(enabled),
        "results": list(results),
        "targeted": targeted,
        "updated": updated,
        "zero_targets": bool(zero_targets),
    }


def backend_error_result(backend: str) -> dict[str, str | int]:
    return {"backend": str(backend), "selector": "error", "targeted": 0, "updated": 0}


def apply_auto_combat_state(bot, enabled: bool) -> dict:
    enabled_bool = bool(enabled)
    set_desired_toggle(bot, DESIRED_AUTO_COMBAT_KEY, enabled_bool)
    if bot.Properties.exists("pause_on_danger"):
        bot.Properties.ApplyNow("pause_on_danger", "active", enabled_bool)
    backend_results: list[dict[str, str | int]] = []
    try:
        backend_results.append(
            normalize_backend_toggle_result(
                set_auto_combat(enabled_bool, preferred_engine=ENGINE_HERO_AI, bot=bot),
                ENGINE_HERO_AI,
            )
        )
    except Exception:
        backend_results.append(backend_error_result(ENGINE_HERO_AI))
    if bot.Properties.exists("auto_combat"):
        bot.Properties.ApplyNow("auto_combat", "active", enabled_bool)
    return build_toggle_summary("combat", enabled_bool, backend_results)


def apply_auto_looting_state(bot, enabled: bool) -> dict:
    enabled_bool = bool(enabled)
    set_desired_toggle(bot, DESIRED_AUTO_LOOTING_KEY, enabled_bool)
    backend_results: list[dict[str, str | int]] = []
    try:
        backend_results.append(
            normalize_backend_toggle_result(
                set_auto_looting(enabled_bool, preferred_engine=ENGINE_HERO_AI, bot=bot),
                ENGINE_HERO_AI,
            )
        )
    except Exception:
        backend_results.append(backend_error_result(ENGINE_HERO_AI))
    if bot.Properties.exists("auto_loot"):
        bot.Properties.ApplyNow("auto_loot", "active", enabled_bool)
    return build_toggle_summary("looting", enabled_bool, backend_results)


def apply_auto_following_state(bot, enabled: bool) -> dict:
    enabled_bool = bool(enabled)
    set_desired_toggle(bot, DESIRED_AUTO_FOLLOWING_KEY, enabled_bool)
    backend_results: list[dict[str, str | int]] = []
    try:
        backend_results.append(
            normalize_backend_toggle_result(
                set_auto_following(enabled_bool, preferred_engine=ENGINE_HERO_AI, bot=bot),
                ENGINE_HERO_AI,
            )
        )
    except Exception:
        backend_results.append(backend_error_result(ENGINE_HERO_AI))
    return build_toggle_summary("following", enabled_bool, backend_results)


def initialize_desired_auto_state_defaults(bot, *, combat: bool = True, looting: bool = True, following: bool = True) -> dict[str, bool]:
    set_desired_toggle(bot, DESIRED_AUTO_COMBAT_KEY, bool(combat))
    set_desired_toggle(bot, DESIRED_AUTO_LOOTING_KEY, bool(looting))
    set_desired_toggle(bot, DESIRED_AUTO_FOLLOWING_KEY, bool(following))
    return {"combat": bool(combat), "looting": bool(looting), "following": bool(following)}


def reconcile_desired_auto_states(bot, *, throttle_seconds: float = 1.0) -> dict[str, dict] | None:
    cfg = getattr(bot, "config", None)
    if cfg is None:
        return None
    now = time.monotonic()
    last_reconcile = float(getattr(cfg, TOGGLE_RECONCILE_AT_KEY, 0.0) or 0.0)
    if (now - last_reconcile) < max(0.1, float(throttle_seconds)):
        return None
    setattr(cfg, TOGGLE_RECONCILE_AT_KEY, now)
    return {
        "combat": apply_auto_combat_state(bot, get_desired_toggle(bot, DESIRED_AUTO_COMBAT_KEY, True)),
        "looting": apply_auto_looting_state(bot, get_desired_toggle(bot, DESIRED_AUTO_LOOTING_KEY, True)),
        "following": apply_auto_following_state(bot, get_desired_toggle(bot, DESIRED_AUTO_FOLLOWING_KEY, True)),
    }
