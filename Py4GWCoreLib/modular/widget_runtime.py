"""Small widget helpers for BT-native modular tools."""
from __future__ import annotations

import time
import traceback
from typing import Any, Callable

from Py4GWCoreLib import Console
from Py4GWCoreLib import ConsoleLog


_LAST_MAIN_EXCEPTION_AT: dict[str, float] = {}


def guarded_widget_main(
    widget_name: str,
    run_fn: Callable[[], None],
    *,
    get_bot: Callable[[], Any] | None = None,
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
        ConsoleLog(widget_name, f"Widget main failed: {exc}", Console.MessageType.Error)
        ConsoleLog(widget_name, traceback.format_exc(), Console.MessageType.Error)


def start_widget_bot(
    widget_name: str,
    build_bot_fn: Callable[[], Any],
    *,
    post_build_fn: Callable[[Any], None] | None = None,
) -> Any | None:
    try:
        tree_or_bot = build_bot_fn()
        if callable(post_build_fn):
            post_build_fn(tree_or_bot)
        start = getattr(tree_or_bot, "start", None)
        if callable(start):
            start()
        return tree_or_bot
    except Exception as exc:
        ConsoleLog(widget_name, f"Failed to start modular BT widget: {exc}", Console.MessageType.Error)
        ConsoleLog(widget_name, traceback.format_exc(), Console.MessageType.Error)
        return None
