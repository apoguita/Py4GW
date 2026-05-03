"""
widget_runtime module

This module is part of the modular runtime surface.
"""
from __future__ import annotations

from typing import Any, Callable, Optional
import time
import traceback

from Py4GWCoreLib import Console, ConsoleLog

from .diagnostics import ModularRunDiagnostics


_LAST_MAIN_EXCEPTION_AT: dict[str, float] = {}


def _emit_exception_to_bot(bot: Any, widget_name: str, message: str, traceback_text: str) -> bool:
    if bot is None:
        return False

    record_event = getattr(bot, "record_diagnostics_event", None)
    if not callable(record_event):
        return False

    try:
        record_event(
            "exception",
            message=f"{widget_name}: {message}",
            traceback_text=traceback_text,
        )
        return True
    except Exception:
        return False


def guarded_widget_main(
    widget_name: str,
    run_fn: Callable[[], None],
    *,
    get_bot: Optional[Callable[[], Any]] = None,
    throttle_seconds: float = 2.0,
) -> None:
    try:
        run_fn()
    except Exception as exc:
        now = time.monotonic()
        last_at = float(_LAST_MAIN_EXCEPTION_AT.get(widget_name, 0.0))
        if (now - last_at) < float(throttle_seconds):
            return
        _LAST_MAIN_EXCEPTION_AT[widget_name] = now

        tb = traceback.format_exc()
        message = f"Widget main failed: {exc}"
        ConsoleLog(widget_name, message, Console.MessageType.Error)
        ConsoleLog(widget_name, tb, Console.MessageType.Error)

        bot = None
        if callable(get_bot):
            try:
                bot = get_bot()
            except Exception:
                bot = None

        if _emit_exception_to_bot(bot, widget_name, message, tb):
            return

        # Fallback: write one-off diagnostics session to disk.
        diag = ModularRunDiagnostics.start_run(widget=widget_name, bot_name=widget_name)
        diag.write_event(
            event="exception",
            message=message,
            traceback_text=tb,
        )
        diag.finalize(reason="widget_main_exception")


def start_widget_bot(
    widget_name: str,
    build_bot_fn: Callable[[], Any],
    *,
    post_build_fn: Optional[Callable[[Any], None]] = None,
) -> Any | None:
    diag = ModularRunDiagnostics.start_run(widget=widget_name, bot_name=widget_name)
    diag.write_event(event="start_clicked", message="Widget start button clicked.")
    diag.write_event(event="build_started", message="Building widget bot instance.")

    try:
        bot = build_bot_fn()
        if bot is None:
            raise RuntimeError("Widget bot builder returned None.")

        bind_session = getattr(bot, "bind_diagnostics_session", None)
        if callable(bind_session):
            bind_session(diag)

        if callable(post_build_fn):
            post_build_fn(bot)

        diag.write_event(event="build_succeeded", message="Widget bot instance built successfully.")
        bot.start()
        return bot
    except Exception as exc:
        tb = traceback.format_exc()
        diag.write_event(
            event="build_failed",
            message=f"{exc}",
            traceback_text=tb,
        )
        diag.write_event(
            event="exception",
            message=f"Widget start failed: {exc}",
            traceback_text=tb,
        )
        diag.finalize(reason="widget_start_failed")
        ConsoleLog(widget_name, f"Failed to start widget bot: {exc}", Console.MessageType.Error)
        ConsoleLog(widget_name, tb, Console.MessageType.Error)
        return None
