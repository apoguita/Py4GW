"""
Phase — A named group of bot steps.

A Phase wraps a function that registers FSM states on a Botting instance.
Phases can optionally be conditional (skipped at runtime if condition returns False)
and can switch templates at the start.

Usage:
    from modular_bot import Phase

    def my_combat_phase(bot: Botting):
        bot.Move.FollowAutoPath(KILL_PATH, "Kill Route")
        bot.Wait.UntilOutOfCombat()

    Phase("Combat", my_combat_phase)
    Phase("Optional Quest", quest_fn, condition=lambda: Settings.do_quest)
    Phase("Pacifist Run", run_fn, template="pacifist")
"""

from __future__ import annotations

from typing import Callable, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from Py4GWCoreLib import Botting


class Phase:
    """
    A named group of bot steps.

    Args:
        name:      Display name (used as FSM header and for loop/recovery targets).
        fn:        Function ``(bot: Botting) -> None`` that registers FSM states.
        condition: Optional callable returning bool.  When provided, the phase is
                   wrapped in a runtime check — if it returns ``False`` the phase
                   is skipped entirely.
        template:  Optional template name to apply at the start of this phase.
                   One of ``"aggressive"``, ``"pacifist"``, ``"multibox_aggressive"``.
    """

    __slots__ = ("name", "fn", "condition", "template")

    def __init__(
        self,
        name: str,
        fn: Callable[["Botting"], None],
        *,
        condition: Optional[Callable[[], bool]] = None,
        template: Optional[str] = None,
    ) -> None:
        self.name = name
        self.fn = fn
        self.condition = condition
        self.template = template

    def __repr__(self) -> str:
        parts = [f"Phase({self.name!r}"]
        if self.condition is not None:
            parts.append("conditional")
        if self.template is not None:
            parts.append(f"template={self.template!r}")
        return ", ".join(parts) + ")"

