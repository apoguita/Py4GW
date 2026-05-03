"""
Unified modular recipe runner.

Canonical JSON format is steps-only:

{
  "name": "Any Block",
  "steps": [{...}]
}
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from Py4GWCoreLib import Botting

from ..compiler.source_loader import BlockSourceLoader
from ..compiler.execution_plan import CompiledExecutionPlan, build_execution_plan
from ..domain.contracts import ModularPhaseRuntimeSpec
from ..phase import Phase


def _load_block_data(block_name: str, kind: Optional[str] = None) -> Dict[str, Any]:
    loaded = BlockSourceLoader.load(block_name, kind=kind)
    return loaded.data


def list_available_blocks(kind: Optional[str] = None) -> List[str]:
    return BlockSourceLoader.list_available(kind=kind)




ModularBlockExecutionPlan = CompiledExecutionPlan


def build_modular_block_execution_plan(
    block_name: str,
    *,
    kind: Optional[str] = None,
    recipe_name: str = "ModularBlock",
    load_party_overrides: Optional[Dict[str, Any]] = None,
) -> ModularBlockExecutionPlan:
    return build_execution_plan(
        block_name,
        kind=kind,
        recipe_name=recipe_name,
        load_party_overrides=load_party_overrides,
    )


def build_modular_block_phase(
    block_name: str,
    *,
    name: Optional[str] = None,
    kind: Optional[str] = None,
    recipe_name: str = "ModularBlock",
    anchor: bool = False,
    load_party_overrides: Optional[Dict[str, Any]] = None,
    pre_run_hook: Optional[Callable[["Botting"], None]] = None,
    pre_run_name: str = "Pre Block Hook",
    post_run_hook: Optional[Callable[["Botting"], None]] = None,
    post_run_name: str = "Post Block Hook",
) -> Phase:
    spec = ModularPhaseRuntimeSpec(
        block_name=str(block_name),
        kind=str(kind or ""),
        recipe_name=str(recipe_name),
        load_party_overrides=dict(load_party_overrides or {}),
        inline_plan=None,
        pre_run_hook=pre_run_hook,
        pre_run_name=str(pre_run_name or "Pre Block Hook"),
        post_run_hook=post_run_hook,
        post_run_name=str(post_run_name or "Post Block Hook"),
    )
    phase_name = str(name or "").strip()
    if not phase_name:
        try:
            data = _load_block_data(block_name, kind=kind)
            phase_name = str(data.get("name", block_name))
        except FileNotFoundError:
            phase_name = f"{recipe_name}: {block_name}"
    return Phase(phase_name, anchor=anchor, runtime_spec=spec)


def build_inline_modular_phase(
    *,
    display_name: str,
    steps: list[dict[str, Any]],
    recipe_name: str = "ModularInline",
    name: Optional[str] = None,
    anchor: bool = False,
    inventory_guard_source: Optional[Dict[str, Any]] = None,
    pre_run_hook: Optional[Callable[["Botting"], None]] = None,
    pre_run_name: str = "Pre Inline Hook",
    post_run_hook: Optional[Callable[["Botting"], None]] = None,
    post_run_name: str = "Post Inline Hook",
) -> Phase:
    source_data = dict(inventory_guard_source or {})
    inline_plan = {
        "display_name": str(display_name or "Inline Plan"),
        "steps": [dict(step) if isinstance(step, dict) else step for step in (steps or [])],
        "source_data": source_data,
    }
    spec = ModularPhaseRuntimeSpec(
        block_name="",
        kind="",
        recipe_name=str(recipe_name or "ModularInline"),
        load_party_overrides={},
        inline_plan=inline_plan,
        pre_run_hook=pre_run_hook,
        pre_run_name=str(pre_run_name or "Pre Inline Hook"),
        post_run_hook=post_run_hook,
        post_run_name=str(post_run_name or "Post Inline Hook"),
    )
    return Phase(
        str(name or display_name or "Inline Plan"),
        anchor=anchor,
        runtime_spec=spec,
    )


def ModularBlock(
    block_name: str,
    name: Optional[str] = None,
    *,
    kind: Optional[str] = None,
    anchor: bool = False,
) -> Phase:
    if name is None:
        try:
            data = _load_block_data(block_name, kind=kind)
            name = str(data.get("name", block_name))
        except FileNotFoundError:
            name = f"ModularBlock: {block_name}"
    spec = ModularPhaseRuntimeSpec(
        block_name=str(block_name),
        kind=str(kind or ""),
        recipe_name="ModularBlock",
    )
    return Phase(name, anchor=anchor, runtime_spec=spec)


# Typed phase factories.
def list_available_missions() -> List[str]:
    return list_available_blocks(kind="missions")


def list_available_quests() -> List[str]:
    return list_available_blocks(kind="quests")


def list_available_routes() -> List[str]:
    return list_available_blocks(kind="routes")


def list_available_farms() -> List[str]:
    return list_available_blocks(kind="farms")


def list_available_dungeons() -> List[str]:
    return list_available_blocks(kind="dungeons")


def list_available_vanquishes() -> List[str]:
    return list_available_blocks(kind="vanquishes")


def list_available_bounties() -> List[str]:
    return list_available_blocks(kind="bounties")


def Mission(mission_name: str, name: Optional[str] = None, anchor: bool = False) -> Phase:
    return ModularBlock(mission_name, name=name, kind="missions", anchor=anchor)


def Quest(quest_name: str, name: Optional[str] = None, anchor: bool = False) -> Phase:
    return ModularBlock(quest_name, name=name, kind="quests", anchor=anchor)


def Route(route_name: str, name: Optional[str] = None, anchor: bool = False) -> Phase:
    return ModularBlock(route_name, name=name, kind="routes", anchor=anchor)


def Farm(farm_name: str, name: Optional[str] = None, anchor: bool = False) -> Phase:
    return ModularBlock(farm_name, name=name, kind="farms", anchor=anchor)


def Dungeon(dungeon_name: str, name: Optional[str] = None, anchor: bool = False) -> Phase:
    return ModularBlock(dungeon_name, name=name, kind="dungeons", anchor=anchor)


def Vanquish(vanquish_name: str, name: Optional[str] = None, anchor: bool = False) -> Phase:
    return ModularBlock(vanquish_name, name=name, kind="vanquishes", anchor=anchor)


def Bounty(bounty_name: str, name: Optional[str] = None, anchor: bool = False) -> Phase:
    return ModularBlock(bounty_name, name=name, kind="bounties", anchor=anchor)
