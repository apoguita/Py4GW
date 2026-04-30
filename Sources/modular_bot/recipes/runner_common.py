from __future__ import annotations

from typing import Any, Callable, Dict, List


def count_expanded_steps(steps: List[Dict[str, Any]]) -> int:
    total = 0
    for step in steps:
        repeat_raw = step.get("repeat", 1)
        try:
            repeat = int(repeat_raw)
        except (TypeError, ValueError):
            repeat = 1
        if repeat > 0:
            total += repeat
    return total


def register_recipe_context(bot, display_name: str, total_steps: int = 0) -> None:
    bot.States.AddCustomState(
        lambda _t=display_name: setattr(bot.config, "modular_recipe_title", str(_t)),
        f"Set Recipe Title: {display_name}",
    )
    bot.States.AddCustomState(
        lambda: setattr(bot.config, "modular_step_title", ""),
        "Reset Step Title",
    )
    bot.States.AddCustomState(
        lambda _total=max(0, int(total_steps)): setattr(bot.config, "modular_step_total", _total),
        f"Set Total Steps: {display_name}",
    )
    bot.States.AddCustomState(
        lambda: setattr(bot.config, "modular_step_index", 0),
        "Reset Step Index",
    )


def register_repeated_steps(
    bot,
    *,
    recipe_name: str,
    steps: List[Dict[str, Any]],
    register_step: Callable[[Any, Dict[str, Any], int], None],
) -> int:
    from Py4GWCoreLib import ConsoleLog

    total_registered_steps = 0
    for source_idx, step in enumerate(steps):
        repeat_raw = step.get("repeat", 1)
        try:
            repeat = int(repeat_raw)
        except (TypeError, ValueError):
            ConsoleLog(
                f"Recipe:{recipe_name}",
                f"Invalid repeat at source step {source_idx}: {repeat_raw!r}. Using 1.",
            )
            repeat = 1

        if repeat <= 0:
            ConsoleLog(
                f"Recipe:{recipe_name}",
                f"Skipping source step {source_idx} because repeat={repeat}.",
            )
            continue

        for rep_idx in range(repeat):
            step_to_register = step
            if repeat > 1 and "name" in step:
                step_to_register = dict(step)
                step_to_register["name"] = f"{step['name']} [{rep_idx + 1}/{repeat}]"

            register_step(bot, step_to_register, total_registered_steps)
            total_registered_steps += 1

    return total_registered_steps
