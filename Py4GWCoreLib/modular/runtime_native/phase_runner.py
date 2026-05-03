"""
phase_runner module

This module is part of the modular runtime surface.
"""
from __future__ import annotations

import traceback
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Callable, Optional

from Py4GWCoreLib import Console, ConsoleLog
from Py4GWCoreLib.py4gwcorelib_src.BehaviorTree import BehaviorTree
from Py4GWCoreLib.routines_src.behaviourtrees_src.modular_core import (
    StepNodeRequest,
    build_action_step_tree,
    expand_steps as expand_action_steps,
)
from Py4GWCoreLib.routines_src.behaviourtrees_src.modular_core.step_utils import step_display_name

from Py4GWCoreLib.modular.actions.registry import get_action_node_metadata
from Py4GWCoreLib.modular.domain.contracts import ModularPhaseRuntimeSpec
from Py4GWCoreLib.modular.phase import Phase
from Py4GWCoreLib.modular.recipes.modular_block import build_modular_block_execution_plan

from .helpers import apply_template


if TYPE_CHECKING:
    from Py4GWCoreLib.modular.bot import ModularBot


@dataclass
class PendingRecovery:
    """
    P en di ng Re co ve ry class.
    
    Meta:
      Expose: true
      Audience: advanced
      Display: Pending Recovery
      Purpose: Provide explicit modular runtime behavior and metadata.
      UserDescription: Internal class used by modular orchestration and step execution.
      Notes: Keep behavior explicit and side effects contained.
    """
    phase_name: str
    state_name: str
    reason: str
    requested_at: float


@dataclass(frozen=True)
class NativeBlockSpec:
    """
    N at iv eB lo ck Sp ec class.
    
    Meta:
      Expose: true
      Audience: advanced
      Display: Native Block Spec
      Purpose: Provide explicit modular runtime behavior and metadata.
      UserDescription: Internal class used by modular orchestration and step execution.
      Notes: Keep behavior explicit and side effects contained.
    """
    block_name: str
    kind: str
    recipe_name: str
    load_party_overrides: dict[str, Any]
    inline_plan: Optional[dict[str, Any]]
    pre_run_hook: Optional[Callable[[Any], None]]
    pre_run_name: str
    post_run_hook: Optional[Callable[[Any], None]]
    post_run_name: str


def extract_native_block_spec(phase: Phase) -> Optional[NativeBlockSpec]:
    raw = getattr(phase, "runtime_spec", None)
    if not isinstance(raw, ModularPhaseRuntimeSpec):
        return None
    block_name = str(raw.block_name or "").strip()
    kind = str(raw.kind or "").strip()
    recipe_name = str(raw.recipe_name or "ModularBlock")
    overrides = dict(raw.load_party_overrides or {})
    inline_raw = raw.inline_plan
    inline_plan: Optional[dict[str, Any]] = None
    if isinstance(inline_raw, dict):
        inline_steps = inline_raw.get("steps", [])
        if not isinstance(inline_steps, list):
            inline_steps = []
        inline_plan = {
            "display_name": str(inline_raw.get("display_name", "") or "").strip(),
            "steps": [dict(step) if isinstance(step, dict) else step for step in inline_steps],
            "source_data": dict(inline_raw.get("source_data", {}) or {}),
        }
    if not block_name and inline_plan is None:
        return None
    pre_run_hook = raw.pre_run_hook if callable(raw.pre_run_hook) else None
    pre_run_name = str(raw.pre_run_name or "").strip()
    post_run_hook = raw.post_run_hook if callable(raw.post_run_hook) else None
    post_run_name = str(raw.post_run_name or "").strip()
    return NativeBlockSpec(
        block_name=block_name,
        kind=kind,
        recipe_name=recipe_name,
        load_party_overrides=overrides,
        inline_plan=inline_plan,
        pre_run_hook=pre_run_hook,
        pre_run_name=pre_run_name,
        post_run_hook=post_run_hook,
        post_run_name=post_run_name,
    )


class _NativeStepRunner:
    """
    Executes a single modular action step through the BT-native action node registry.
    """

    def __init__(
        self,
        owner: "ModularBot",
        *,
        phase_name: str,
        recipe_name: str,
        step: dict[str, Any],
        step_index: int,
        restart_state: str = "",
    ) -> None:
        self.owner = owner
        self.phase_name = str(phase_name)
        self.recipe_name = str(recipe_name)
        self.step = dict(step)
        self.step_index = int(step_index)
        self.restart_state = str(restart_state or "")
        self.started = False
        self.done = False
        self._step_type = str(self.step.get("type", "") or "")
        self._step_display = step_display_name(self.step, self._step_type, self.step_index)
        self._step_tree: Optional[BehaviorTree] = None

    def _start_runtime(self) -> BehaviorTree.NodeState:
        request = StepNodeRequest(
            owner=self.owner,
            bot=self.owner.bot,
            phase_name=self.phase_name,
            recipe_name=self.recipe_name,
            step=dict(self.step),
            step_idx=int(self.step_index),
            step_total=int(getattr(self.owner.bot.config, "modular_step_total", 0) or 0),
            step_type=self._step_type,
            step_display=self._step_display,
            restart_state=str(self.restart_state or ""),
        )
        self._step_tree = build_action_step_tree(request)
        self.started = True
        self.owner.record_diagnostics_event(
            "step_registered",
            phase=self.phase_name,
            step_index=int(self.step_index + 1),
            step_type=self._step_type,
            message=f"Registered step node type={self._step_type!r} for phase={self.phase_name!r}.",
        )
        return BehaviorTree.NodeState.RUNNING

    def tick(self) -> BehaviorTree.NodeState:
        if self.done:
            return BehaviorTree.NodeState.SUCCESS

        if not self.started:
            start_state = self._start_runtime()
            if start_state != BehaviorTree.NodeState.RUNNING:
                return start_state

        if self._step_tree is None:
            self.done = True
            return BehaviorTree.NodeState.FAILURE

        try:
            step_state = BehaviorTree.Node._normalize_state(self._step_tree.tick())
            if step_state is None:
                raise TypeError("Step tree returned non-NodeState result.")
        except Exception as exc:
            ConsoleLog(
                "ModularBot",
                (
                    f"Step node tick failed for phase={self.phase_name!r}, "
                    f"idx={self.step_index + 1}, type={self._step_type!r}: {exc}"
                ),
                Console.MessageType.Error,
            )
            self.owner.record_diagnostics_event(
                "exception",
                phase=self.phase_name,
                step_index=int(self.step_index + 1),
                step_type=self._step_type,
                message=f"Step node tick failed: {exc}",
                traceback_text=traceback.format_exc(),
            )
            self.done = True
            return BehaviorTree.NodeState.FAILURE

        if step_state == BehaviorTree.NodeState.RUNNING:
            return BehaviorTree.NodeState.RUNNING

        self.done = True
        if step_state == BehaviorTree.NodeState.SUCCESS:
            self.done = True
            return BehaviorTree.NodeState.SUCCESS
        return BehaviorTree.NodeState.FAILURE


class NativeBlockPhaseRunner:
    """
    Executes a modular JSON block phase as a BT-native sequence of action steps.

    Each expanded step is executed via `_NativeStepRunner` through the native
    step node registry while planner orchestration remains native.
    """

    def __init__(
        self,
        owner: "ModularBot",
        phase: Phase,
        phase_index: int,
        total_phases: int,
        spec: NativeBlockSpec,
    ) -> None:
        self.owner = owner
        self.phase = phase
        self.phase_index = phase_index
        self.total_phases = total_phases
        self.spec = spec
        self.started = False
        self.done = False
        self.death_pause_logged = False
        self.recipe_title = ""
        self.expanded_steps: list[dict[str, Any]] = []
        self._restart_state_index_map: dict[str, int] = {}
        self.current_step_index = 0
        self.current_step_runner: Optional[_NativeStepRunner] = None
        self._initial_restart_state = ""
        self._pre_hook_done = False
        self._post_hook_done = False

    def _enumerate_step_state_names(self, step: dict[str, Any], step_index: int) -> list[str]:
        step_type = str(step.get("type", "") or "").strip()
        spec = get_action_node_metadata(step_type)
        if spec is None or not callable(spec.state_name_probe):
            return []
        try:
            request = StepNodeRequest(
                owner=self.owner,
                bot=self.owner.bot,
                phase_name=str(self.phase.name),
                recipe_name=self.spec.recipe_name,
                step=dict(step),
                step_idx=int(step_index),
                step_total=int(len(self.expanded_steps)),
                step_type=step_type,
                step_display=step_display_name(step, step_type, step_index),
                restart_state="",
            )
            names = list(spec.state_name_probe(request) or [])
        except Exception:
            names = []
        return [str(name) for name in names if str(name or "").strip()]

    def _build_restart_state_index_map(self) -> None:
        mapping: dict[str, int] = {}
        for idx, step in enumerate(self.expanded_steps):
            if not isinstance(step, dict):
                continue
            step_name = str(step.get("name", "") or "").strip()
            if step_name:
                key = step_name.lower()
                if key not in mapping:
                    mapping[key] = idx

            state_names = self._enumerate_step_state_names(step, idx)
            for state_name in state_names:
                key = state_name.strip().lower()
                if key and key not in mapping:
                    mapping[key] = idx

        self.owner._reset_step_fsm()
        self._restart_state_index_map = mapping

    def _resolve_restart_step_index(self, restart_state: str) -> int:
        needle = str(restart_state or "").strip().lower()
        if not needle:
            return 0

        if needle in self._restart_state_index_map:
            return int(self._restart_state_index_map[needle])

        contains_matches = [
            (state_name, idx)
            for state_name, idx in self._restart_state_index_map.items()
            if needle in state_name or state_name in needle
        ]
        if contains_matches:
            contains_matches.sort(key=lambda item: (item[1], len(item[0])))
            return int(contains_matches[0][1])

        matches: list[tuple[int, int]] = []
        for idx, step in enumerate(self.expanded_steps):
            if not isinstance(step, dict):
                continue
            step_name = str(step.get("name", "") or "").strip().lower()
            if not step_name:
                continue
            if needle == step_name:
                matches.append((0, idx))
            elif needle in step_name or step_name in needle:
                matches.append((1, idx))

        if matches:
            best_rank = min(rank for rank, _ in matches)
            return min(idx for rank, idx in matches if rank == best_rank)
        return 0

    def _start_runtime(self) -> BehaviorTree.NodeState:
        cfg = self.owner.bot.config
        phase_name = str(self.phase.name)
        self.owner._active_phase_name = phase_name
        self.owner.record_diagnostics_event(
            "phase_started",
            phase=phase_name,
            message=f"Phase started: {phase_name}",
        )

        setattr(cfg, "modular_phase_index", int(self.phase_index + 1))
        setattr(cfg, "modular_phase_total", int(self.total_phases))
        setattr(cfg, "modular_phase_title", phase_name)
        setattr(cfg, "modular_recipe_title", "")
        setattr(cfg, "modular_step_title", "")
        setattr(cfg, "modular_step_index", 0)
        setattr(cfg, "modular_step_total", 0)

        if self.phase.anchor:
            self.owner._set_runtime_anchor(phase_name=phase_name, state_name="")

        if self.phase.template is not None:
            try:
                apply_template(self.owner.bot, self.phase.template)
            except Exception as exc:
                ConsoleLog(
                    "ModularBot",
                    f"Template switch failed for phase {phase_name!r}: {exc}",
                    Console.MessageType.Warning,
                )

        if self.phase.condition is not None:
            should_run = False
            try:
                should_run = bool(self.phase.condition())
            except Exception as exc:
                ConsoleLog(
                    "ModularBot",
                    f"Phase condition failed for {phase_name!r}: {exc}",
                    Console.MessageType.Error,
                )
                self.owner.record_diagnostics_event(
                    "exception",
                    phase=phase_name,
                    message=f"Phase condition failed: {exc}",
                    traceback_text=traceback.format_exc(),
                )
                self.owner.record_diagnostics_event(
                    "phase_finished",
                    phase=phase_name,
                    message=f"Phase failed during condition check: {phase_name}",
                )
                self.done = True
                self.owner._active_phase_name = None
                return self.owner._phase_failure_state()
            if not should_run:
                self.owner._debug_log(f"Skipping phase (condition=false): {phase_name}")
                self.owner.record_diagnostics_event(
                    "phase_finished",
                    phase=phase_name,
                    message=f"Phase skipped (condition=false): {phase_name}",
                )
                self.done = True
                return BehaviorTree.NodeState.SUCCESS

        if callable(self.spec.pre_run_hook) and not self._pre_hook_done:
            try:
                self.spec.pre_run_hook(self.owner.bot)
            except Exception as exc:
                ConsoleLog(
                    "ModularBot",
                    (
                        f"Native pre-run hook failed for phase={self.phase.name!r} "
                        f"({self.spec.pre_run_name or 'Pre Block Hook'}): {exc}"
                    ),
                    Console.MessageType.Error,
                )
                self.done = True
                self.owner._active_phase_name = None
                self.owner.record_diagnostics_event(
                    "exception",
                    phase=phase_name,
                    message=f"Pre-run hook failed: {exc}",
                    traceback_text=traceback.format_exc(),
                )
                self.owner.record_diagnostics_event(
                    "phase_finished",
                    phase=phase_name,
                    message=f"Phase failed during pre-run hook: {phase_name}",
                )
                return self.owner._phase_failure_state()
            self._pre_hook_done = True

        if isinstance(self.spec.inline_plan, dict):
            inline_plan = self.spec.inline_plan
            self.recipe_title = str(inline_plan.get("display_name", "") or phase_name)
            inline_steps = inline_plan.get("steps", [])
            if not isinstance(inline_steps, list):
                inline_steps = []
            source_data = inline_plan.get("source_data", {})
            source_data = dict(source_data) if isinstance(source_data, dict) else {}
            self.expanded_steps = expand_action_steps(
                steps=[dict(step) if isinstance(step, dict) else step for step in inline_steps],
                inventory_guard_source=source_data,
            )
        else:
            try:
                plan = build_modular_block_execution_plan(
                    self.spec.block_name,
                    kind=self.spec.kind or None,
                    recipe_name=self.spec.recipe_name,
                    load_party_overrides=self.spec.load_party_overrides or None,
                )
            except Exception as exc:
                ConsoleLog(
                    "ModularBot",
                    f"Native block plan load failed for phase {phase_name!r}: {exc}",
                    Console.MessageType.Error,
                )
                self.owner.record_diagnostics_event(
                    "exception",
                    phase=phase_name,
                    message=f"Native block plan load failed: {exc}",
                    traceback_text=traceback.format_exc(),
                )
                self.owner.record_diagnostics_event(
                    "phase_finished",
                    phase=phase_name,
                    message=f"Phase failed during block plan load: {phase_name}",
                )
                self.done = True
                return self.owner._phase_failure_state()

            self.recipe_title = str(plan.display_name)
            self.expanded_steps = expand_action_steps(
                steps=[dict(step) if isinstance(step, dict) else step for step in plan.steps],
                inventory_guard_source=plan.source_data,
            )

        self._build_restart_state_index_map()
        setattr(cfg, "modular_recipe_title", self.recipe_title)
        setattr(cfg, "modular_step_title", "")
        setattr(cfg, "modular_step_total", int(len(self.expanded_steps)))
        setattr(cfg, "modular_step_index", 0)

        if not self.expanded_steps:
            self.owner._debug_log(f"Phase {phase_name!r} compiled to 0 steps; skipping.")
            self.owner.record_diagnostics_event(
                "phase_finished",
                phase=phase_name,
                message=f"Phase produced zero steps and was skipped: {phase_name}",
            )
            self.done = True
            self.owner._active_phase_name = None
            return BehaviorTree.NodeState.SUCCESS

        self._initial_restart_state = self.owner._consume_phase_restart_state(phase_name)
        self.current_step_index = self._resolve_restart_step_index(self._initial_restart_state)
        self.current_step_runner = None
        self.started = True
        return BehaviorTree.NodeState.RUNNING

    def _build_current_step_runner(self) -> _NativeStepRunner:
        step = self.expanded_steps[self.current_step_index]
        restart_state = ""
        if self._initial_restart_state:
            restart_state = self._initial_restart_state
            self._initial_restart_state = ""
        return _NativeStepRunner(
            self.owner,
            phase_name=str(self.phase.name),
            recipe_name=self.spec.recipe_name,
            step=step,
            step_index=self.current_step_index,
            restart_state=restart_state,
        )

    def tick(self) -> BehaviorTree.NodeState:
        if self.done:
            return BehaviorTree.NodeState.SUCCESS

        if not self.started:
            start_state = self._start_runtime()
            if start_state != BehaviorTree.NodeState.RUNNING:
                return start_state

        if self.owner._pending_recovery is not None:
            return BehaviorTree.NodeState.RUNNING

        if self.owner._on_death is None and self.owner._is_player_dead():
            if not self.death_pause_logged:
                self.owner._debug_log("[Player death] Pausing phase execution until revive.")
                self.death_pause_logged = True
            return BehaviorTree.NodeState.RUNNING
        self.death_pause_logged = False

        if self.current_step_runner is None:
            self.current_step_runner = self._build_current_step_runner()

        step_result = self.current_step_runner.tick()
        if step_result == BehaviorTree.NodeState.RUNNING:
            return BehaviorTree.NodeState.RUNNING

        if step_result == BehaviorTree.NodeState.FAILURE:
            self.done = True
            self.owner._active_phase_name = None
            self.owner.record_diagnostics_event(
                "phase_finished",
                phase=str(self.phase.name),
                message=f"Phase failed: {self.phase.name}",
            )
            return step_result

        self.current_step_index += 1
        self.current_step_runner = None
        if self.current_step_index >= len(self.expanded_steps):
            if callable(self.spec.post_run_hook) and not self._post_hook_done:
                try:
                    self.spec.post_run_hook(self.owner.bot)
                except Exception as exc:
                    ConsoleLog(
                        "ModularBot",
                        (
                            f"Native post-run hook failed for phase={self.phase.name!r} "
                            f"({self.spec.post_run_name or 'Post Block Hook'}): {exc}"
                        ),
                        Console.MessageType.Error,
                    )
                    self.done = True
                    self.owner._active_phase_name = None
                    self.owner.record_diagnostics_event(
                        "exception",
                        phase=str(self.phase.name),
                        message=f"Post-run hook failed: {exc}",
                        traceback_text=traceback.format_exc(),
                    )
                    self.owner.record_diagnostics_event(
                        "phase_finished",
                        phase=str(self.phase.name),
                        message=f"Phase failed during post-run hook: {self.phase.name}",
                    )
                    return self.owner._phase_failure_state()
                self._post_hook_done = True
            self.done = True
            self.owner._active_phase_name = None
            self.owner.record_diagnostics_event(
                "phase_finished",
                phase=str(self.phase.name),
                message=f"Phase finished: {self.phase.name}",
            )
            return BehaviorTree.NodeState.SUCCESS

        return BehaviorTree.NodeState.RUNNING
