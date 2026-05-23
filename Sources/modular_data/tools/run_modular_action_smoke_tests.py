"""Runtime smoke runner for canonical modular JSON actions.

This is intended for injected/PyGW runtime use. It builds tiny recipes on the
fly, compiles them through the same JSON-to-BT compiler used by Modular Tester,
and reports PASS/SKIP/FAIL per action.
"""
from __future__ import annotations

import argparse
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from typing import Callable

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


StepFactory = Callable[["RuntimeContext"], tuple[dict[str, Any] | None, str]]


@dataclass(frozen=True)
class RuntimeContext:
    include_risky: bool
    include_party: bool
    include_consumables: bool
    include_combat: bool
    dialog_id: str
    dialog_button: int
    timeout_ms: int
    route_offset: int


@dataclass(frozen=True)
class SmokeCase:
    name: str
    step_type: str
    action: str
    factory: StepFactory
    detection: str


@dataclass(frozen=True)
class SmokeResult:
    name: str
    status: str
    detail: str
    detection: str


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case", action="append", default=[], help="Run only a named case. Can be passed more than once.")
    parser.add_argument("--list", action="store_true", help="List available smoke cases and exit.")
    parser.add_argument("--dry-run", action="store_true", help="Compile generated steps without ticking behavior trees.")
    parser.add_argument("--include-risky", action="store_true", help="Enable travel, enter_challenge, resign, abandon_quest.")
    parser.add_argument("--include-party", action="store_true", help="Enable party-load smoke test.")
    parser.add_argument("--include-consumables", action="store_true", help="Enable consumable and summoning-stone smoke tests.")
    parser.add_argument("--include-combat", action="store_true", help="Enable route kill smoke tests.")
    parser.add_argument("--dialog-id", default="", help="Dialog id for interact.dialog, for example 0x86.")
    parser.add_argument("--dialog-button", type=int, default=0, help="Button number for interact.auto_dialog.")
    parser.add_argument("--timeout-ms", type=int, default=8000, help="Per-case runtime timeout.")
    parser.add_argument("--route-offset", type=int, default=25, help="Small XY offset used by route move/nudge tests.")
    args = parser.parse_args(argv)

    cases = _cases()
    selected = {str(name).strip() for name in args.case if str(name).strip()}
    if args.list:
        for case in cases:
            print(f"{case.name}: {case.step_type}.{case.action} [{case.detection}]")
        return 0

    context = RuntimeContext(
        include_risky=bool(args.include_risky),
        include_party=bool(args.include_party),
        include_consumables=bool(args.include_consumables),
        include_combat=bool(args.include_combat),
        dialog_id=str(args.dialog_id or "").strip(),
        dialog_button=int(args.dialog_button or 0),
        timeout_ms=max(250, int(args.timeout_ms or 8000)),
        route_offset=max(1, int(args.route_offset or 25)),
    )

    wanted = [case for case in cases if not selected or case.name in selected]
    if not wanted:
        print("No smoke cases selected.")
        return 1

    try:
        from Py4GWCoreLib.modular.json_bt_compiler import compile_recipe_to_bt
        from Py4GWCoreLib.py4gwcorelib_src.BehaviorTree import BehaviorTree
    except ModuleNotFoundError as exc:
        print(f"Cannot import PyGW runtime bindings: {exc}")
        return 2

    results: list[SmokeResult] = []
    for case in wanted:
        step, reason = case.factory(context)
        if step is None:
            results.append(SmokeResult(case.name, "SKIP", reason, case.detection))
            continue
        recipe = {"name": f"Smoke: {case.name}", "steps": [step]}
        try:
            tree = compile_recipe_to_bt(recipe, recipe_name=str(recipe["name"]))
        except Exception as exc:
            results.append(SmokeResult(case.name, "FAIL", f"compile failed: {type(exc).__name__}: {exc}", "compile"))
            continue
        if args.dry_run:
            results.append(SmokeResult(case.name, "PASS", "compiled", "compile"))
            continue
        results.append(_tick_case(case, tree, BehaviorTree, context.timeout_ms))

    _print_results(results)
    return 1 if any(result.status == "FAIL" for result in results) else 0


def _tick_case(case: SmokeCase, tree: Any, behavior_tree_cls: Any, timeout_ms: int) -> SmokeResult:
    deadline = time.monotonic() + (timeout_ms / 1000.0)
    last_state = None
    try:
        tree.reset()
        while time.monotonic() < deadline:
            last_state = tree.tick()
            if last_state == behavior_tree_cls.NodeState.RUNNING:
                time.sleep(0.05)
                continue
            if last_state == behavior_tree_cls.NodeState.SUCCESS:
                return SmokeResult(case.name, "PASS", "BT returned SUCCESS", case.detection)
            return SmokeResult(case.name, "FAIL", f"BT returned {last_state}", case.detection)
        return SmokeResult(case.name, "FAIL", f"timed out after {timeout_ms} ms; last_state={last_state}", case.detection)
    except Exception as exc:
        return SmokeResult(case.name, "FAIL", f"runtime exception: {type(exc).__name__}: {exc}", case.detection)


def _print_results(results: list[SmokeResult]) -> None:
    width = max([len(result.name) for result in results] + [4])
    for result in results:
        print(f"{result.status:<4} {result.name:<{width}} {result.detail} ({result.detection})")
    counts: dict[str, int] = {}
    for result in results:
        counts[result.status] = counts.get(result.status, 0) + 1
    summary = ", ".join(f"{key.lower()}={counts[key]}" for key in sorted(counts))
    print(f"Summary: {summary}")


def _cases() -> list[SmokeCase]:
    return [
        SmokeCase("route.move", "route", "move", _route_move, "BT success after movement reaches tiny offset"),
        SmokeCase("route.nudge", "route", "nudge", _route_nudge, "BT success after move pulses dispatch"),
        SmokeCase("route.exit", "route", "exit", _route_exit, "risky/manual; requires portal target"),
        SmokeCase("route.kill", "route", "kill", _route_kill, "combat/manual; BT success if path clear completes"),
        SmokeCase("interact.npc", "interact", "npc", _interact_npc, "BT success after target/interact; needs NPC target"),
        SmokeCase("interact.gadget", "interact", "gadget", _interact_gadget, "BT success after target/interact; needs gadget target"),
        SmokeCase("interact.item", "interact", "item", _interact_item, "BT success after item interaction; needs item target"),
        SmokeCase("interact.dialog", "interact", "dialog", _interact_dialog, "BT success after interact/send dialog; needs target and --dialog-id"),
        SmokeCase("interact.auto_dialog", "interact", "auto_dialog", _interact_auto_dialog, "BT success after automatic dialog send"),
        SmokeCase("interact.drop_bundle", "interact", "drop_bundle", _interact_drop_bundle, "BT success after drop command"),
        SmokeCase("map.travel", "map", "travel", _map_travel, "risky/manual; leaves party then travels"),
        SmokeCase("map.enter_challenge", "map", "enter_challenge", _map_enter_challenge, "risky/manual; enters challenge"),
        SmokeCase("map.wait_for_map_load", "map", "wait_for_map_load", _map_wait_for_map_load, "BT success when current map is loaded"),
        SmokeCase("party.load", "party", "load", _party_load, "party/manual; BT success after party load dispatch"),
        SmokeCase("party.flag_heroes", "party", "flag_heroes", _party_flag_heroes, "BT success after flag dispatch"),
        SmokeCase("party.unflag_heroes", "party", "unflag_heroes", _party_unflag_heroes, "BT success after unflag dispatch"),
        SmokeCase("party.force_hero_state", "party", "force_hero_state", _party_force_hero_state, "BT success after behavior dispatch"),
        SmokeCase("party.resign", "party", "resign", _party_resign, "risky/manual; sends /resign"),
        SmokeCase("party.abandon_quest", "party", "abandon_quest", _party_abandon_quest, "risky/manual; abandons quest id"),
        SmokeCase("behavior.enemy_blacklist.add", "behavior", "enemy_blacklist", _blacklist_add, "BT success after blacklist add"),
        SmokeCase("behavior.enemy_blacklist.remove", "behavior", "enemy_blacklist", _blacklist_remove, "BT success after blacklist remove"),
        SmokeCase("inventory.use_consumables", "inventory", "use_consumables", _inventory_use_consumables, "consumable/manual"),
        SmokeCase(
            "inventory.broadcast_summoning_stone",
            "inventory",
            "broadcast_summoning_stone",
            _inventory_broadcast_summoning_stone,
            "consumable/multibox manual",
        ),
        SmokeCase("wait.wait", "wait", "wait", _wait_wait, "BT success after wait duration"),
        SmokeCase("wait.emote", "wait", "emote", _wait_emote, "BT success after chat command dispatch"),
    ]


def _player_xy() -> tuple[int, int]:
    from Py4GWCoreLib import Player

    x, y = Player.GetXY()
    return int(x), int(y)


def _current_map_id() -> int:
    from Py4GWCoreLib import Map

    return int(Map.GetMapID() or 0)


def _target_id() -> int:
    from Py4GWCoreLib import Player

    return int(Player.GetTargetID() or 0)


def _target_point() -> list[int] | None:
    from Py4GWCoreLib import Agent

    target_id = _target_id()
    if target_id <= 0 or not Agent.IsValid(target_id):
        return None
    x, y = Agent.GetXY(target_id)
    return [int(x), int(y)]


def _target_model_id() -> int:
    from Py4GWCoreLib import Agent
    from Py4GWCoreLib import Item

    target_id = _target_id()
    if target_id <= 0 or not Agent.IsValid(target_id) or not Agent.IsItem(target_id):
        return 0
    item_id = int(Agent.GetItemAgentItemID(target_id) or 0)
    return int(Item.GetModelID(item_id) or 0) if item_id > 0 else 0


def _is_npc_target() -> bool:
    from Py4GWCoreLib import Agent
    from Py4GWCoreLib import AgentArray

    target_id = _target_id()
    return target_id > 0 and Agent.IsValid(target_id) and not Agent.IsItem(target_id) and not Agent.IsGadget(target_id) and target_id not in AgentArray.GetEnemyArray()


def _is_gadget_target() -> bool:
    from Py4GWCoreLib import Agent

    target_id = _target_id()
    return target_id > 0 and Agent.IsValid(target_id) and Agent.IsGadget(target_id)


def _is_item_target() -> bool:
    from Py4GWCoreLib import Agent

    target_id = _target_id()
    return target_id > 0 and Agent.IsValid(target_id) and Agent.IsItem(target_id)


def _is_enemy_target() -> bool:
    from Py4GWCoreLib import Agent
    from Py4GWCoreLib import AgentArray

    target_id = _target_id()
    return target_id > 0 and Agent.IsValid(target_id) and target_id in AgentArray.GetEnemyArray()


def _target_name(default: str = "TARGET") -> str:
    from Py4GWCoreLib import Agent

    target_id = _target_id()
    if target_id <= 0 or not Agent.IsValid(target_id):
        return default
    name = str(Agent.GetNameByID(target_id) or "").strip()
    return name or default


def _route_move(ctx: RuntimeContext) -> tuple[dict[str, Any], str]:
    x, y = _player_xy()
    return {"type": "route", "name": "Smoke route.move", "mode": "move", "points": [[x + ctx.route_offset, y]]}, ""


def _route_nudge(ctx: RuntimeContext) -> tuple[dict[str, Any], str]:
    x, y = _player_xy()
    return {"type": "route", "name": "Smoke route.nudge", "mode": "nudge", "point": [x + ctx.route_offset, y], "pulses": 1}, ""


def _route_exit(ctx: RuntimeContext) -> tuple[dict[str, Any] | None, str]:
    if not ctx.include_risky:
        return None, "requires --include-risky and a real portal/target_map_id edit"
    x, y = _player_xy()
    return {"type": "route", "name": "Smoke route.exit", "mode": "exit", "point": [x, y], "target_map_id": _current_map_id()}, ""


def _route_kill(ctx: RuntimeContext) -> tuple[dict[str, Any] | None, str]:
    if not ctx.include_combat:
        return None, "requires --include-combat"
    x, y = _player_xy()
    return {"type": "route", "name": "Smoke route.kill", "mode": "kill", "points": [[x, y], [x + ctx.route_offset, y]]}, ""


def _interact_dialog(ctx: RuntimeContext) -> tuple[dict[str, Any] | None, str]:
    if not ctx.dialog_id:
        return None, "requires --dialog-id, for example --dialog-id 0x86"
    if not _is_npc_target() and not _is_gadget_target():
        return None, "requires targeted NPC or gadget"
    point = _target_point()
    step: dict[str, Any] = {"type": "interact", "name": "Smoke interact.dialog", "action": "dialog", "id": ctx.dialog_id}
    if _is_gadget_target():
        step.update({"gadget": _target_name("GADGET"), "point": point})
    else:
        step.update({"npc": _target_name("NPC"), "point": point})
    return step, ""


def _interact_auto_dialog(ctx: RuntimeContext) -> tuple[dict[str, Any] | None, str]:
    if ctx.dialog_button <= 0:
        return None, "requires --dialog-button"
    return {"type": "interact", "name": "Smoke interact.auto_dialog", "action": "auto_dialog", "button": ctx.dialog_button}, ""


def _interact_npc(_ctx: RuntimeContext) -> tuple[dict[str, Any] | None, str]:
    if not _is_npc_target():
        return None, "requires targeted NPC"
    return {"type": "interact", "name": "Smoke interact.npc", "target": "npc", "point": _target_point()}, ""


def _interact_gadget(_ctx: RuntimeContext) -> tuple[dict[str, Any] | None, str]:
    if not _is_gadget_target():
        return None, "requires targeted gadget"
    return {"type": "interact", "name": "Smoke interact.gadget", "target": "gadget", "point": _target_point()}, ""


def _interact_item(_ctx: RuntimeContext) -> tuple[dict[str, Any] | None, str]:
    if not _is_item_target():
        return None, "requires targeted item"
    model_id = _target_model_id()
    if model_id <= 0:
        return None, "targeted item has no model_id"
    return {"type": "interact", "name": "Smoke interact.item", "target": "item", "model_id": model_id}, ""


def _interact_drop_bundle(_ctx: RuntimeContext) -> tuple[dict[str, Any], str]:
    return {"type": "interact", "name": "Smoke interact.drop_bundle", "action": "drop_bundle"}, ""


def _map_travel(ctx: RuntimeContext) -> tuple[dict[str, Any] | None, str]:
    if not ctx.include_risky:
        return None, "requires --include-risky and target_map_id edit"
    return {"type": "map", "name": "Smoke map.travel", "action": "travel", "target_map_id": _current_map_id()}, ""


def _map_enter_challenge(ctx: RuntimeContext) -> tuple[dict[str, Any] | None, str]:
    if not ctx.include_risky:
        return None, "requires --include-risky in a challenge outpost"
    return {"type": "map", "name": "Smoke map.enter_challenge", "action": "enter_challenge", "target_map_id": 0}, ""


def _map_wait_for_map_load(_ctx: RuntimeContext) -> tuple[dict[str, Any], str]:
    return {"type": "map", "name": "Smoke map.wait_for_map_load", "action": "wait_for_map_load", "map_id": _current_map_id()}, ""


def _party_load(ctx: RuntimeContext) -> tuple[dict[str, Any] | None, str]:
    if not ctx.include_party:
        return None, "requires --include-party"
    from Py4GWCoreLib import Map

    if not Map.IsOutpost():
        return None, "requires outpost"
    party_size = int(Map.GetMaxPartySize() or 8)
    return {"type": "party", "name": "Smoke party.load", "action": "load", "max_heroes": party_size}, ""


def _party_flag_heroes(_ctx: RuntimeContext) -> tuple[dict[str, Any], str]:
    x, y = _player_xy()
    return {"type": "party", "name": "Smoke party.flag_heroes", "action": "flag_heroes", "point": [x, y]}, ""


def _party_unflag_heroes(_ctx: RuntimeContext) -> tuple[dict[str, Any], str]:
    return {"type": "party", "name": "Smoke party.unflag_heroes", "action": "unflag_heroes"}, ""


def _party_force_hero_state(_ctx: RuntimeContext) -> tuple[dict[str, Any], str]:
    return {"type": "party", "name": "Smoke party.force_hero_state", "action": "force_hero_state", "state": "guard"}, ""


def _party_resign(ctx: RuntimeContext) -> tuple[dict[str, Any] | None, str]:
    if not ctx.include_risky:
        return None, "requires --include-risky"
    return {"type": "party", "name": "Smoke party.resign", "action": "resign"}, ""


def _party_abandon_quest(ctx: RuntimeContext) -> tuple[dict[str, Any] | None, str]:
    if not ctx.include_risky:
        return None, "requires --include-risky and quest_id edit"
    return {"type": "party", "name": "Smoke party.abandon_quest", "action": "abandon_quest", "quest_id": 0}, ""


def _blacklist_add(_ctx: RuntimeContext) -> tuple[dict[str, Any] | None, str]:
    if not _is_enemy_target():
        return None, "requires targeted enemy"
    return {"type": "behavior", "name": "Smoke behavior.enemy_blacklist.add", "action": "enemy_blacklist", "mode": "add", "enemy": _target_name("ENEMY")}, ""


def _blacklist_remove(_ctx: RuntimeContext) -> tuple[dict[str, Any] | None, str]:
    if not _is_enemy_target():
        return None, "requires targeted enemy"
    return {"type": "behavior", "name": "Smoke behavior.enemy_blacklist.remove", "action": "enemy_blacklist", "mode": "remove", "enemy": _target_name("ENEMY")}, ""


def _inventory_use_consumables(ctx: RuntimeContext) -> tuple[dict[str, Any] | None, str]:
    if not ctx.include_consumables:
        return None, "requires --include-consumables"
    return {"type": "inventory", "name": "Smoke inventory.use_consumables", "action": "use_consumables", "mode": "pcons"}, ""


def _inventory_broadcast_summoning_stone(ctx: RuntimeContext) -> tuple[dict[str, Any] | None, str]:
    if not ctx.include_consumables:
        return None, "requires --include-consumables"
    return {"type": "inventory", "name": "Smoke inventory.broadcast_summoning_stone", "action": "broadcast_summoning_stone"}, ""


def _wait_wait(_ctx: RuntimeContext) -> tuple[dict[str, Any], str]:
    return {"type": "wait", "name": "Smoke wait.wait", "action": "wait", "ms": 250}, ""


def _wait_emote(_ctx: RuntimeContext) -> tuple[dict[str, Any], str]:
    return {"type": "wait", "name": "Smoke wait.emote", "action": "emote", "command": "dance"}, ""


if __name__ == "__main__":
    raise SystemExit(main())
