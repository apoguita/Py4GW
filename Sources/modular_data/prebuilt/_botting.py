"""Shared helpers for prebuilt modular BottingTree recipes."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Sequence

from Py4GWCoreLib.BottingTree import BottingTree
from Py4GWCoreLib.modular import compile_recipe_steps_to_named_planner_steps
from Py4GWCoreLib.modular import load_recipe


@dataclass(frozen=True)
class RecipeSpec:
    kind: str
    key: str
    title: str


def specs_from_campaign_rows(rows: Sequence[tuple[str, str, str, str]]) -> list[RecipeSpec]:
    return [RecipeSpec(kind=str(kind), key=str(key), title=str(title)) for _region, kind, key, title in rows]


def recipe_path(spec: RecipeSpec) -> Path:
    folder_by_kind = {
        "dungeon": "dungeons",
        "farm": "farms",
        "mission": "missions",
        "quest": "quests",
        "route": "routes",
    }
    folder = folder_by_kind.get(spec.kind, spec.kind)
    return Path(folder) / f"{spec.key}.json"


def create_modular_botting_tree(
    *,
    name: str,
    specs: Sequence[RecipeSpec],
    start_index: int = 0,
    loop: bool = False,
    debug_hook: Callable[[str], None] | None = None,
) -> BottingTree:
    selected_specs = list(specs)[max(0, int(start_index)) :]
    planner_steps = []
    for offset, spec in enumerate(selected_specs, start=max(0, int(start_index))):
        path = recipe_path(spec)
        recipe_name = f"{spec.kind.title()}: {spec.title}"
        if debug_hook is not None:
            debug_hook(f"Compiling phase {offset + 1}/{len(specs)} {spec.kind}:{spec.key} from {path}.")
        recipe = load_recipe(path)
        planner_steps.extend(
            compile_recipe_steps_to_named_planner_steps(
                recipe,
                recipe_name=recipe_name,
                planner_prefix=f"{offset + 1:02d}.",
            )
        )

    botting_tree = BottingTree(
        bot_name=name,
        pause_on_combat=False,
        isolation_enabled=False,
    )
    botting_tree.SetCurrentNamedPlannerSteps(
        planner_steps,
        name=name,
        auto_start=False,
        reset=True,
        repeat=bool(loop),
    )
    return botting_tree
