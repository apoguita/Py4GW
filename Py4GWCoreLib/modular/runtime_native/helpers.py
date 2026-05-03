"""
helpers module

This module is part of the modular runtime surface.
"""
from __future__ import annotations

import re
from typing import Any

from Py4GWCoreLib import Botting, BottingTree

TEMPLATE_MAP: dict[str, str] = {
    "aggressive": "Aggressive",
    "pacifist": "Pacifist",
    "multibox_aggressive": "Multibox_Aggressive",
    "preserve": "",
}


def resolve_botting_tree_ctor():
    """
    Resolve BottingTree constructor across runtime export shapes.

    Depending on Py4GWCoreLib packaging, `BottingTree` may be exported either
    as the class itself or as the `Py4GWCoreLib.BottingTree` module.
    """
    candidate = BottingTree

    ctor = getattr(candidate, "BottingTree", None)
    if callable(ctor):
        return ctor

    if callable(candidate):
        return candidate

    try:
        from Py4GWCoreLib.BottingTree import BottingTree as explicit_ctor

        if callable(explicit_ctor):
            return explicit_ctor
    except Exception:
        pass

    raise TypeError(
        "Unable to resolve BottingTree constructor. Expected callable class or module with BottingTree attribute."
    )


def modular_planner_compiler():
    from Py4GWCoreLib.modular.compiler.planner_compiler import ModularPlannerCompiler

    return ModularPlannerCompiler


def sanitize_bot_name(name: str) -> str:
    safe = re.sub(r'[<>:"/\\|?*]+', "_", name).strip(" .")
    return safe or "Bot"


def apply_template(bot: Botting, template_name: str) -> None:
    if str(template_name or "").strip().lower() == "preserve":
        return
    method_name = TEMPLATE_MAP.get(str(template_name or "").strip())
    if method_name is None:
        raise ValueError(
            f"Unknown template {template_name!r}. "
            f"Choose from: {list(TEMPLATE_MAP.keys())}"
        )
    getattr(bot.Templates, method_name)()


def is_hero_ai_runtime_active(bot: Botting) -> bool:
    try:
        if bot.Properties.exists("hero_ai") and bool(bot.Properties.IsActive("hero_ai")):
            return True
    except Exception:
        pass

    try:
        from Py4GWCoreLib.py4gwcorelib_src.WidgetManager import get_widget_handler

        return bool(get_widget_handler().is_widget_enabled("HeroAI"))
    except Exception:
        return False


def is_widget_enabled(widget_name: str) -> bool:
    name = str(widget_name)
    try:
        from Py4GW_widget_manager import get_widget_handler

        handler = get_widget_handler()
        if bool(handler.is_widget_enabled(name)):
            return True
    except Exception:
        pass
    try:
        from Py4GWCoreLib.py4gwcorelib_src.WidgetManager import get_widget_handler

        handler = get_widget_handler()
        if bool(handler.is_widget_enabled(name)):
            return True
    except Exception:
        pass
    return False


def set_widget_enabled(widget_name: str, enabled: bool) -> bool:
    name = str(widget_name)
    changed = False
    for module_path in ("Py4GW_widget_manager", "Py4GWCoreLib.py4gwcorelib_src.WidgetManager"):
        try:
            if module_path == "Py4GW_widget_manager":
                from Py4GW_widget_manager import get_widget_handler
            else:
                from Py4GWCoreLib.py4gwcorelib_src.WidgetManager import get_widget_handler

            handler = get_widget_handler()
            fn_name = "enable_widget" if bool(enabled) else "disable_widget"
            fn = getattr(handler, fn_name, None)
            if callable(fn):
                fn(name)
                changed = True
        except Exception:
            continue
    return changed
