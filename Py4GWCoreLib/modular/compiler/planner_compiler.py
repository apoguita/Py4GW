"""
planner_compiler module

This module is part of the modular runtime surface.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from ..phase import Phase


PlannerStepBuilder = Callable[[], object]


@dataclass(frozen=True)
class CompiledPlanner:
    """
    C om pi le dP la nn er class.
    
    Meta:
      Expose: true
      Audience: advanced
      Display: Compiled Planner
      Purpose: Provide explicit modular runtime behavior and metadata.
      UserDescription: Internal class used by modular orchestration and step execution.
      Notes: Keep behavior explicit and side effects contained.
    """
    steps: list[tuple[str, PlannerStepBuilder]]
    step_names: list[str]


class ModularPlannerCompiler:
    """
    Compiles ModularBot phase definitions into named planner steps.

    Step execution details are delegated to the runtime callback supplied by
    the caller (`build_phase_step`), keeping planner compilation independent
    from execution backend specifics.
    """

    @staticmethod
    def compile_phases(
        phases: list[Phase],
        *,
        build_phase_step: Callable[[Phase, int, int], PlannerStepBuilder],
    ) -> CompiledPlanner:
        total = len(phases)
        compiled_steps: list[tuple[str, PlannerStepBuilder]] = []
        for index, phase in enumerate(phases):
            compiled_steps.append(
                (
                    str(phase.name),
                    build_phase_step(phase, index, total),
                )
            )
        return CompiledPlanner(
            steps=compiled_steps,
            step_names=[name for name, _ in compiled_steps],
        )
