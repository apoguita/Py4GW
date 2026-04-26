"""
Party toggle actions and desired-state reconciliation.
"""
from __future__ import annotations

import time

from Py4GWCoreLib import Console, ConsoleLog

from .combat_engine import (
    ENGINE_HERO_AI,
    resolve_engine_for_bot,
    set_auto_combat as engine_set_auto_combat,
    set_auto_following as engine_set_auto_following,
    set_auto_looting as engine_set_auto_looting,
)
from .step_context import StepContext
from .step_registration import modular_step
from .step_utils import log_recipe, parse_step_bool, wait_after_step


_DESIRED_AUTO_COMBAT_KEY = "_modular_desired_auto_combat"
_DESIRED_AUTO_LOOTING_KEY = "_modular_desired_auto_looting"
_DESIRED_AUTO_FOLLOWING_KEY = "_modular_desired_auto_following"
_TOGGLE_RECONCILE_AT_KEY = "_modular_last_toggle_reconcile_at"


def _set_desired_toggle(bot, key: str, enabled: bool) -> None:
    cfg = getattr(bot, "config", None)
    if cfg is not None:
        setattr(cfg, key, bool(enabled))


def _get_desired_toggle(bot, key: str, default: bool = True) -> bool:
    cfg = getattr(bot, "config", None)
    if cfg is None or not hasattr(cfg, key):
        return bool(default)
    return bool(getattr(cfg, key))


def current_auto_combat_enabled(bot) -> bool:
    cfg = getattr(bot, "config", None)
    if cfg is not None and hasattr(cfg, _DESIRED_AUTO_COMBAT_KEY):
        return bool(getattr(cfg, _DESIRED_AUTO_COMBAT_KEY))

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
    if cfg is not None and hasattr(cfg, _DESIRED_AUTO_LOOTING_KEY):
        return bool(getattr(cfg, _DESIRED_AUTO_LOOTING_KEY))

    engine = resolve_engine_for_bot(bot)
    if engine == ENGINE_HERO_AI:
        try:
            from .combat_engine import is_party_looting_enabled

            return bool(is_party_looting_enabled(bot=bot, preferred_engine=engine))
        except Exception:
            return False

    if bot.Properties.exists("auto_loot"):
        return bool(bot.Properties.IsActive("auto_loot"))
    return False


def _normalize_backend_toggle_result(raw_result, backend: str) -> dict[str, str | int]:
    if isinstance(raw_result, dict):
        return {
            "backend": str(raw_result.get("backend", backend) or backend),
            "selector": str(raw_result.get("selector", "none") or "none"),
            "targeted": int(raw_result.get("targeted", 0) or 0),
            "updated": int(raw_result.get("updated", 0) or 0),
        }
    return {"backend": str(backend), "selector": "none", "targeted": 0, "updated": 0}


def _build_toggle_summary(toggle: str, enabled: bool, results: list[dict[str, str | int]]) -> dict:
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


def _hero_ai_result(summary: dict) -> dict[str, str | int]:
    for result in list(summary.get("results", []) or []):
        if str(result.get("backend", "")) == ENGINE_HERO_AI:
            return {
                "selector": str(result.get("selector", "none") or "none"),
                "targeted": int(result.get("targeted", 0) or 0),
                "updated": int(result.get("updated", 0) or 0),
            }
    return {"selector": "none", "targeted": 0, "updated": 0}


def _record_toggle_warning(owner, summary: dict, *, reason: str, hero_ai: dict[str, str | int]) -> None:
    toggle_name = str(summary.get("toggle", "") or "")
    enabled = bool(summary.get("enabled", False))
    if bool(getattr(owner, "is_debug_logging_enabled", lambda: False)()):
        ConsoleLog(
            "ModularBot",
            (
                f"toggle_warning: {toggle_name} enabled={enabled} had zero HeroAI recipients "
                f"(selector={hero_ai.get('selector', 'none')})."
            ),
            Console.MessageType.Warning,
        )
    owner.record_diagnostics_event(
        "toggle_warning",
        step_type=f"set_auto_{toggle_name}" if toggle_name else "set_auto_toggle",
        message=(
            f"toggle {toggle_name} applied enabled={enabled} but HeroAI had zero recipients "
            f"(selector={hero_ai.get('selector', 'none')})."
        ),
        extra=_toggle_diag_extra(summary, reason=reason),
    )


def _record_toggle_reconciled(owner, summary: dict) -> None:
    toggle_name = str(summary.get("toggle", "") or "")
    enabled = bool(summary.get("enabled", False))
    targeted = int(summary.get("targeted", 0) or 0)
    updated = int(summary.get("updated", 0) or 0)
    if bool(getattr(owner, "is_debug_logging_enabled", lambda: False)()):
        ConsoleLog(
            "ModularBot",
            f"toggle_reconciled: {toggle_name} enabled={enabled} updated={updated} targeted={targeted}.",
            Console.MessageType.Info,
        )
    owner.record_diagnostics_event(
        "toggle_reconciled",
        step_type=f"set_auto_{toggle_name}" if toggle_name else "set_auto_toggle",
        message=f"reconciled toggle {toggle_name} enabled={enabled}; updated={updated} targeted={targeted}.",
        extra=_toggle_diag_extra(summary, reason="reconcile"),
    )


def _toggle_diag_extra(summary: dict, *, reason: str) -> dict:
    return {
        "toggle": str(summary.get("toggle", "") or ""),
        "enabled": bool(summary.get("enabled", False)),
        "reason": str(reason),
        "targeted": int(summary.get("targeted", 0) or 0),
        "updated": int(summary.get("updated", 0) or 0),
        "results": list(summary.get("results", []) or []),
    }


def _record_toggle_diagnostics(bot, summary: dict, *, reason: str) -> None:
    owner = getattr(bot, "_modular_owner", None)
    if owner is None or not hasattr(owner, "record_diagnostics_event"):
        return
    hero_ai = _hero_ai_result(summary)
    if bool(summary.get("zero_targets", False)):
        _record_toggle_warning(owner, summary, reason=reason, hero_ai=hero_ai)
    if str(reason) == "reconcile" and int(summary.get("updated", 0) or 0) > 0:
        _record_toggle_reconciled(owner, summary)


def _backend_error_result(backend: str) -> dict[str, str | int]:
    return {"backend": str(backend), "selector": "error", "targeted": 0, "updated": 0}


def apply_auto_combat_state(bot, enabled: bool, *, reason: str = "step") -> dict:
    e = bool(enabled)
    _set_desired_toggle(bot, _DESIRED_AUTO_COMBAT_KEY, e)
    if bot.Properties.exists("pause_on_danger"):
        bot.Properties.ApplyNow("pause_on_danger", "active", e)

    backend_results: list[dict[str, str | int]] = []
    try:
        backend_results.append(_normalize_backend_toggle_result(engine_set_auto_combat(e, preferred_engine=ENGINE_HERO_AI, bot=bot), ENGINE_HERO_AI))
    except Exception:
        backend_results.append(_backend_error_result(ENGINE_HERO_AI))

    if bot.Properties.exists("auto_combat"):
        bot.Properties.ApplyNow("auto_combat", "active", e)

    try:
        owner = getattr(bot, "_modular_owner", None)
        if owner is not None and hasattr(owner, "_apply_party_member_hooks"):
            owner._apply_party_member_hooks(bot, force=True)
    except Exception:
        pass

    summary = _build_toggle_summary("combat", e, backend_results)
    _record_toggle_diagnostics(bot, summary, reason=reason)
    return summary


def apply_auto_looting_state(bot, enabled: bool, *, reason: str = "step") -> dict:
    e = bool(enabled)
    _set_desired_toggle(bot, _DESIRED_AUTO_LOOTING_KEY, e)
    backend_results: list[dict[str, str | int]] = []
    try:
        backend_results.append(_normalize_backend_toggle_result(engine_set_auto_looting(e, preferred_engine=ENGINE_HERO_AI, bot=bot), ENGINE_HERO_AI))
    except Exception:
        backend_results.append(_backend_error_result(ENGINE_HERO_AI))

    if bot.Properties.exists("auto_loot"):
        bot.Properties.ApplyNow("auto_loot", "active", e)

    summary = _build_toggle_summary("looting", e, backend_results)
    _record_toggle_diagnostics(bot, summary, reason=reason)
    return summary


def apply_auto_following_state(bot, enabled: bool, *, reason: str = "step") -> dict:
    e = bool(enabled)
    _set_desired_toggle(bot, _DESIRED_AUTO_FOLLOWING_KEY, e)
    backend_results: list[dict[str, str | int]] = []
    try:
        backend_results.append(_normalize_backend_toggle_result(engine_set_auto_following(e, preferred_engine=ENGINE_HERO_AI, bot=bot), ENGINE_HERO_AI))
    except Exception:
        backend_results.append(_backend_error_result(ENGINE_HERO_AI))

    summary = _build_toggle_summary("following", e, backend_results)
    _record_toggle_diagnostics(bot, summary, reason=reason)
    return summary


def initialize_desired_auto_state_defaults(
    bot,
    *,
    combat: bool = True,
    looting: bool = True,
    following: bool = True,
) -> dict[str, bool]:
    _set_desired_toggle(bot, _DESIRED_AUTO_COMBAT_KEY, bool(combat))
    _set_desired_toggle(bot, _DESIRED_AUTO_LOOTING_KEY, bool(looting))
    _set_desired_toggle(bot, _DESIRED_AUTO_FOLLOWING_KEY, bool(following))
    return {"combat": bool(combat), "looting": bool(looting), "following": bool(following)}


def apply_desired_auto_state_defaults(bot, *, reason: str = "startup") -> dict[str, dict]:
    defaults = initialize_desired_auto_state_defaults(bot, combat=True, looting=True, following=True)
    return {
        "combat": apply_auto_combat_state(bot, bool(defaults["combat"]), reason=reason),
        "looting": apply_auto_looting_state(bot, bool(defaults["looting"]), reason=reason),
        "following": apply_auto_following_state(bot, bool(defaults["following"]), reason=reason),
    }


def reconcile_desired_auto_states(bot, *, throttle_seconds: float = 1.0) -> dict[str, dict] | None:
    cfg = getattr(bot, "config", None)
    if cfg is None:
        return None
    now = time.monotonic()
    last_reconcile = float(getattr(cfg, _TOGGLE_RECONCILE_AT_KEY, 0.0) or 0.0)
    if (now - last_reconcile) < max(0.1, float(throttle_seconds)):
        return None
    setattr(cfg, _TOGGLE_RECONCILE_AT_KEY, now)
    return {
        "combat": apply_auto_combat_state(bot, _get_desired_toggle(bot, _DESIRED_AUTO_COMBAT_KEY, True), reason="reconcile"),
        "looting": apply_auto_looting_state(bot, _get_desired_toggle(bot, _DESIRED_AUTO_LOOTING_KEY, True), reason="reconcile"),
        "following": apply_auto_following_state(bot, _get_desired_toggle(bot, _DESIRED_AUTO_FOLLOWING_KEY, True), reason="reconcile"),
    }


def _record_step_toggle_applied(ctx: StepContext, step_type: str, enabled: bool, active_engine: str, summary: dict, targets: list[str]) -> None:
    owner = getattr(ctx.bot, "_modular_owner", None)
    if owner is not None and hasattr(owner, "record_diagnostics_event"):
        owner.record_diagnostics_event(
            "toggle_applied",
            step_index=int(ctx.step_idx + 1),
            step_type=step_type,
            message=f"{step_type} global enabled={bool(enabled)} active_engine={active_engine} targets={targets}",
            extra={"enabled": bool(enabled), "active_engine": str(active_engine), "global_targets": list(targets), "summary": summary},
        )


def _record_step_toggle_failed(ctx: StepContext, step_type: str, enabled: bool, active_engine: str, exc: Exception) -> None:
    owner = getattr(ctx.bot, "_modular_owner", None)
    if owner is not None and hasattr(owner, "record_diagnostics_event"):
        owner.record_diagnostics_event(
            "toggle_failed",
            step_index=int(ctx.step_idx + 1),
            step_type=step_type,
            message=f"{step_type} failed enabled={bool(enabled)} active_engine={active_engine}: {exc}",
        )


def _log_step_toggle(ctx: StepContext, step_type: str, enabled: bool, active_engine: str, summary: dict, targets: str) -> None:
    hero_ai = _hero_ai_result(summary)
    log_recipe(
        ctx,
        (
            f"{step_type} applied globally: enabled={bool(enabled)} active_engine={active_engine} "
            f"targets={targets} hero_ai_selector={hero_ai.get('selector', 'none')} "
            f"hero_ai_targeted={hero_ai.get('targeted', 0)} hero_ai_updated={hero_ai.get('updated', 0)}"
        ),
    )


def _handle_toggle_step(ctx: StepContext, *, step_type: str, title: str, apply_fn, targets: list[str]) -> None:
    enabled = parse_step_bool(ctx.step.get("enabled", True), True)

    def _set_toggle_runtime(e: bool = enabled) -> None:
        active_engine = resolve_engine_for_bot(ctx.bot)
        try:
            summary = apply_fn(ctx.bot, e)
            _log_step_toggle(ctx, step_type, e, active_engine, summary, targets=str(targets))
            _record_step_toggle_applied(ctx, step_type, e, active_engine, summary, targets)
        except Exception as exc:
            log_recipe(ctx, f"{step_type} failed: enabled={bool(e)} active_engine={active_engine} error={exc}")
            _record_step_toggle_failed(ctx, step_type, e, active_engine, exc)
            raise

    ctx.bot.States.AddCustomState(_set_toggle_runtime, f"Set {title} {'On' if enabled else 'Off'}")
    wait_after_step(ctx.bot, ctx.step)


def handle_set_auto_combat(ctx: StepContext) -> None:
    _handle_toggle_step(
        ctx,
        step_type="set_auto_combat",
        title="Combat",
        apply_fn=apply_auto_combat_state,
        targets=["native", "hero_ai"],
    )


def handle_set_auto_looting(ctx: StepContext) -> None:
    _handle_toggle_step(
        ctx,
        step_type="set_auto_looting",
        title="Looting",
        apply_fn=apply_auto_looting_state,
        targets=["native", "hero_ai"],
    )


def handle_set_auto_following(ctx: StepContext) -> None:
    _handle_toggle_step(
        ctx,
        step_type="set_auto_following",
        title="Following",
        apply_fn=apply_auto_following_state,
        targets=["hero_ai"],
    )


modular_step(
    step_type="set_auto_combat",
    category="party",
    allowed_params=("enabled", "ms", "name"),
    node_class_name="SetAutoCombatNode",
)(handle_set_auto_combat)
modular_step(
    step_type="set_auto_looting",
    category="party",
    allowed_params=("enabled", "ms", "name"),
    node_class_name="SetAutoLootingNode",
)(handle_set_auto_looting)
modular_step(
    step_type="set_auto_following",
    category="party",
    allowed_params=("enabled", "ms", "name"),
    node_class_name="SetAutoFollowingNode",
)(handle_set_auto_following)
