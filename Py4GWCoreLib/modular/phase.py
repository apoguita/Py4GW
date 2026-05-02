"""Native modular runtime phase model.

Build phases through native recipe factories:

    from Py4GWCoreLib.modular.recipes import Mission, Quest, Route
    from Py4GWCoreLib.modular.recipes.modular_block import (
        ModularBlock,
        build_inline_modular_phase,
    )

    phases = [
        Mission("prophecies/fort_ranik", anchor=True),
        Quest("prophecies/ruins_of_surmia", anchor=True),
        Route("la_to_beacons"),
        ModularBlock("custom/block", kind="farms"),
        build_inline_modular_phase(display_name="Inline", steps=[{"type": "wait", "ms": 1000}]),
    ]
"""

from __future__ import annotations

from typing import Any, Callable, Optional


class Phase:
    """
    A named native modular runtime phase.

    Args:
        name: Display name used as the native planner step and recovery target.
        runtime_spec: Native execution payload created by modular recipe factories.
        condition: Optional callable returning bool.  When provided, the phase is
                   wrapped in a runtime check - if it returns ``False`` the phase
                   is skipped entirely.
        template:  Optional template name to apply at the start of this phase.
                   One of ``"aggressive"``, ``"pacifist"``, ``"multibox_aggressive"``.
        anchor:    If ``True``, sets runtime recovery anchor to this phase when entered.
    """

    __slots__ = ("name", "condition", "template", "anchor", "runtime_spec")

    def __init__(
        self,
        name: str,
        *,
        runtime_spec: Any,
        condition: Optional[Callable[[], bool]] = None,
        template: Optional[str] = None,
        anchor: bool = False,
    ) -> None:
        if runtime_spec is None:
            raise ValueError("Phase requires a native runtime_spec; use modular recipe factories to build phases.")
        self.name = name
        self.condition = condition
        self.template = template
        self.anchor = anchor
        self.runtime_spec = runtime_spec

    def __repr__(self) -> str:
        parts = [f"Phase({self.name!r}"]
        if self.condition is not None:
            parts.append("conditional")
        if self.template is not None:
            parts.append(f"template={self.template!r}")
        if self.anchor:
            parts.append("anchor=True")
        return ", ".join(parts) + ")"
