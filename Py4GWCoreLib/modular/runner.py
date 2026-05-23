"""BottingTree-backed runner wrapper for modular JSON recipe groups."""
from __future__ import annotations

import traceback
from dataclasses import dataclass
from pathlib import Path
from typing import Callable
from typing import Sequence

from Py4GWCoreLib.BottingTree import BottingTree
from Py4GWCoreLib.py4gwcorelib_src.BehaviorTree import BehaviorTree

from .json_bt_compiler import CompiledRecipeStep
from .json_bt_compiler import RecipeStepMetadata
from .json_bt_compiler import compile_recipe_step_to_bt
from .json_bt_compiler import compile_recipe_steps_to_bt
from .json_bt_compiler import load_recipe


@dataclass(frozen=True)
class RecipeSpec:
    kind: str
    key: str
    title: str


@dataclass(frozen=True)
class RecipePhaseView:
    name: str


@dataclass(frozen=True)
class CompiledRecipe:
    spec: RecipeSpec
    steps: tuple[CompiledRecipeStep, ...]


@dataclass(frozen=True)
class RuntimeStepView:
    planner_step_name: str
    spec: RecipeSpec
    phase_index: int
    recipe_title: str
    step_index: int
    step_total: int
    metadata: RecipeStepMetadata
    compiled_step: CompiledRecipeStep


class BTRecipeRunner:
    def __init__(
        self,
        name: str,
        specs: Sequence[RecipeSpec],
        *,
        start_index: int = 0,
        start_step_index: int = 0,
        loop: bool = False,
        debug_hook: Callable[[str], None] | None = None,
    ) -> None:
        self.name = str(name)
        self._specs = list(specs)
        self._start_index = max(0, min(int(start_index), max(0, len(self._specs) - 1)))
        self._start_step_index = max(0, int(start_step_index))
        self._loop = bool(loop)
        self._debug_hook = debug_hook
        self._last_state: BehaviorTree.NodeState | None = None
        self._last_debug_phase_index: int | None = None
        self._last_debug_step_index: int | None = None
        self._last_debug_state: str | None = None
        self._last_active_step_name = ""
        self._phases = [
            RecipePhaseView(name=f"{index + 1:02d}. {spec.kind.title()}: {spec.title}")
            for index, spec in enumerate(self._specs)
        ]
        self._recipes = self._compile_recipes()
        self._runtime_steps = self._build_runtime_steps()
        self._step_by_name = {step.planner_step_name: step for step in self._runtime_steps}
        self._botting_tree = BottingTree(
            bot_name=self.name,
            pause_on_combat=False,
            isolation_enabled=False,
        )
        self._install_planner_steps(reset=True)
        self._debug(
            f"Initialized runner specs={len(self._specs)} compiled={len(self._recipes)} "
            f"runtime_steps={len(self._runtime_steps)} "
            f"start_index={self._start_index + 1 if self._specs else 0}/{len(self._specs)} "
            f"start_step_index={self._start_step_index + 1 if self._start_step_index else 1} loop={self._loop}."
        )

    def start(self) -> None:
        self.reset()
        self._botting_tree.Start()
        self._debug("Started.")

    def stop(self) -> None:
        if self.is_running() or self.is_paused():
            self._debug(f"Stopped by user. {self.debug_snapshot()}")
        self._botting_tree.Stop()

    def pause(self) -> None:
        if not self.is_running():
            return
        self._botting_tree.Pause(True)
        self._debug(f"Paused. {self.debug_snapshot()}")

    def resume(self) -> None:
        if not self.is_paused():
            return
        self._botting_tree.Pause(False)
        self._debug(f"Resumed. {self.debug_snapshot()}")

    def reset(self) -> None:
        if self._botting_tree.IsStarted():
            self._botting_tree.Stop()
        else:
            self._botting_tree.Reset()
        self._last_state = None
        self._last_debug_phase_index = None
        self._last_debug_step_index = None
        self._last_debug_state = None
        self._last_active_step_name = ""
        self._install_planner_steps(reset=True)

    def is_running(self) -> bool:
        return self._botting_tree.IsStarted() and not self._botting_tree.IsPaused()

    def is_paused(self) -> bool:
        return self._botting_tree.IsPaused()

    def update(self) -> None:
        if not self._botting_tree.IsStarted():
            return
        self._debug_progress()
        try:
            self._last_state = self._botting_tree.tick()
        except Exception as exc:
            self._debug(f"Tick exception: {type(exc).__name__}: {exc}. {self.debug_snapshot()}")
            self._debug(traceback.format_exc())
            self._botting_tree.Stop()
            raise
        self._debug_progress()
        self._debug_state()
        if not self._botting_tree.IsStarted():
            status = str(self._botting_tree.GetBlackboardValue("PLANNER_STATUS", "") or "")
            if status == "PLANNER: Failed":
                self._debug(f"Planner failed. {self.debug_snapshot()}")
            elif status == "PLANNER: Completed":
                self._debug("Completed all recipes.")

    def get_current_step_name(self) -> str:
        _index, _total, _recipe_title, step_title = self.get_step_progress()
        return step_title or self.name

    def get_current_step_metadata(self) -> RecipeStepMetadata | None:
        view = self._active_step_view()
        return view.metadata if view is not None else None

    def get_phase_title(self, index: int) -> str:
        if 0 <= int(index) < len(self._phases):
            return self._phases[int(index)].name
        return f"Phase {int(index) + 1}"

    def get_phase_progress(self) -> tuple[int, int, str]:
        total = len(self._specs)
        view = self._active_step_view()
        if view is None:
            return 0, total, ""
        return view.phase_index + 1, total, view.spec.title

    def get_step_progress(self) -> tuple[int, int, str, str]:
        view = self._active_step_view()
        if view is None:
            return 0, 0, "", ""
        return view.step_index, view.step_total, view.recipe_title, view.metadata.title

    def get_runtime_blackboard(self) -> dict:
        return dict(self._botting_tree.blackboard)

    def debug_snapshot(self) -> str:
        phase_current, phase_total, phase_title = self.get_phase_progress()
        step_current, step_total, recipe_title, step_title = self.get_step_progress()
        metadata = self.get_current_step_metadata()
        anchor = bool(metadata.anchor) if metadata is not None else False
        state = self._last_state.name if isinstance(self._last_state, BehaviorTree.NodeState) else str(self._last_state)
        return (
            f"runner={self.name!r} running={self.is_running()} state={state} "
            f"phase={phase_current}/{phase_total} {phase_title!r} "
            f"recipe={recipe_title!r} step={step_current}/{step_total} {step_title!r} anchor={anchor}"
        )

    def _compile_recipes(self) -> list[CompiledRecipe]:
        recipes: list[CompiledRecipe] = []
        for absolute_index, spec in enumerate(self._specs[self._start_index :], start=self._start_index):
            path = _recipe_path(spec)
            recipe_name = f"{spec.kind.title()}: {spec.title}"
            self._debug(f"Compiling phase {absolute_index + 1}/{len(self._specs)} {spec.kind}:{spec.key} from {path}.")
            try:
                recipe = load_recipe(path)
                steps = compile_recipe_steps_to_bt(recipe, recipe_name=recipe_name)
                recipes.append(
                    CompiledRecipe(
                        spec=spec,
                        steps=steps,
                    )
                )
                self._debug(f"Compiled {spec.kind}:{spec.key} title={recipe_name!r} steps={len(steps)}.")
            except Exception as exc:
                self._debug(f"Compile failed for {spec.kind}:{spec.key} path={path}: {type(exc).__name__}: {exc}")
                self._debug(traceback.format_exc())
                raise
        return recipes

    def _build_runtime_steps(self) -> list[RuntimeStepView]:
        runtime_steps: list[RuntimeStepView] = []
        for recipe_offset, recipe in enumerate(self._recipes):
            phase_index = self._start_index + recipe_offset
            step_total = len(recipe.steps)
            first_step_index = 0
            if recipe_offset == 0 and step_total > 0:
                first_step_index = min(self._start_step_index, step_total - 1)
            for step_offset, compiled_step in enumerate(recipe.steps[first_step_index:], start=first_step_index):
                step_index = step_offset + 1
                title = compiled_step.metadata.title
                planner_step_name = f"{phase_index + 1:02d}.{step_index:03d} {title}"
                runtime_steps.append(
                    RuntimeStepView(
                        planner_step_name=planner_step_name,
                        spec=recipe.spec,
                        phase_index=phase_index,
                        recipe_title=recipe.spec.title,
                        step_index=step_index,
                        step_total=step_total,
                        metadata=compiled_step.metadata,
                        compiled_step=compiled_step,
                    )
                )
        return runtime_steps

    def _install_planner_steps(self, *, reset: bool) -> None:
        planner_steps: list[tuple[str, Callable[[], object]]] = [
            (step.planner_step_name, self._make_step_builder(step))
            for step in self._runtime_steps
        ]
        self._botting_tree.SetCurrentNamedPlannerSteps(
            planner_steps,
            name="ModularRecipeRunner",
            auto_start=False,
            reset=reset,
            repeat=self._loop,
        )

    def _make_step_builder(self, step: RuntimeStepView) -> Callable[[], BehaviorTree]:
        def _build_step_tree(step: RuntimeStepView = step) -> BehaviorTree:
            return compile_recipe_step_to_bt(
                dict(step.compiled_step.source_step),
                step.compiled_step.context,
            )

        return _build_step_tree

    def _active_step_view(self) -> RuntimeStepView | None:
        current_step_name = str(self._botting_tree.GetBlackboardValue("current_step_name", "") or "")
        if current_step_name in self._step_by_name:
            self._last_active_step_name = current_step_name
            return self._step_by_name[current_step_name]
        if self._last_active_step_name in self._step_by_name:
            return self._step_by_name[self._last_active_step_name]
        if self._runtime_steps:
            return self._runtime_steps[0]
        return None

    def _debug_progress(self) -> None:
        view = self._active_step_view()
        if view is None:
            return
        if (
            self._last_debug_phase_index == view.phase_index + 1
            and self._last_debug_step_index == view.step_index
        ):
            return
        self._last_debug_phase_index = view.phase_index + 1
        self._last_debug_step_index = view.step_index
        anchor_label = " anchor=true" if bool(view.metadata.anchor) else ""
        self._debug(
            f"Progress phase={view.phase_index + 1}/{len(self._specs)} {view.spec.kind}:{view.spec.key} "
            f"step={view.step_index}/{view.step_total} {view.metadata.title!r}{anchor_label}."
        )

    def _debug_state(self) -> None:
        status = str(self._botting_tree.GetBlackboardValue("PLANNER_STATUS", "") or "")
        if status == self._last_debug_state:
            return
        self._last_debug_state = status
        if status:
            self._debug(f"Planner status={status}.")

    def _debug(self, message: str) -> None:
        if self._debug_hook is None:
            return
        try:
            self._debug_hook(str(message))
        except Exception:
            pass


def specs_from_campaign_rows(rows: Sequence[tuple[str, str, str, str]]) -> list[RecipeSpec]:
    return [RecipeSpec(kind=str(kind), key=str(key), title=str(title)) for _region, kind, key, title in rows]


def _recipe_path(spec: RecipeSpec) -> Path:
    folder_by_kind = {
        "dungeon": "dungeons",
        "farm": "farms",
        "mission": "missions",
        "quest": "quests",
        "route": "routes",
    }
    folder = folder_by_kind.get(spec.kind, spec.kind)
    return Path(folder) / f"{spec.key}.json"
