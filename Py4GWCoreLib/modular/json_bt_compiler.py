"""BT-native compiler for modular JSON recipes."""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from Py4GWCoreLib.py4gwcorelib_src.BehaviorTree import BehaviorTree
from Py4GWCoreLib.routines_src.BehaviourTrees import BT


CANONICAL_STEP_TYPES: tuple[str, ...] = (
    "behavior",
    "interact",
    "inventory",
    "map",
    "party",
    "route",
    "wait",
)

DEFAULT_ROUTE_TOLERANCE = 300.0

LEGACY_STEP_TYPES: tuple[str, ...] = (
    "abandon_quest",
    "add_enemy_blacklist",
    "automatic_dialog",
    "auto_path",
    "auto_path_delayed",
    "auto_path_till_timeout",
    "broadcast_summoning_stone",
    "dialog",
    "dialog_multibox",
    "dialog_with_model",
    "dialogs",
    "disable_party_member_hooks",
    "drop_bundle",
    "emote",
    "enable_party_member_hooks",
    "enemy_blacklist",
    "enter_challenge",
    "exit_map",
    "flag_all_accounts",
    "flag_heroes",
    "follow_model",
    "force_hero_state",
    "interact_gadget",
    "interact_gadget_at_xy",
    "interact_item",
    "interact_nearest_npc",
    "interact_npc",
    "interact_quest_npc",
    "inventory_cleanup",
    "key_press",
    "load_party",
    "loot_chest",
    "move",
    "nudge_move",
    "party_member_hooks",
    "path",
    "path_to_target",
    "quest",
    "remove_enemy_blacklist",
    "resign",
    "set_anchor",
    "set_auto_behavior",
    "set_auto_combat",
    "set_auto_following",
    "set_auto_looting",
    "set_combat_engine",
    "skip_cutscene",
    "suppress_recovery",
    "travel",
    "unflag_all_accounts",
    "unflag_heroes",
    "use_all_consumables",
    "use_consumables",
    "wait_for_map_load",
    "wait_map_change",
    "wait_map_load",
    "wait_model_has_quest",
)

DEFAULT_INTERACT_DELAY_MS = 250
DEFAULT_DIALOG_DELAY_MS = 250


class RecipeCompileError(ValueError):
    """Raised when a modular JSON recipe cannot be compiled."""


class UnknownRecipeStepType(RecipeCompileError):
    """Raised when a step type is missing, unknown, or migration-only."""


@dataclass(frozen=True)
class JsonBTCompilerContext:
    recipe_name: str
    required_hero: Any = None
    metadata: dict[str, Any] | None = None


@dataclass(frozen=True)
class VocabularyIssue:
    index: int
    step_type: str
    reason: str


@dataclass(frozen=True)
class VocabularyAudit:
    recipe_name: str
    steps: int
    issues: tuple[VocabularyIssue, ...]

    @property
    def has_issues(self) -> bool:
        return bool(self.issues)


@dataclass(frozen=True)
class RecipeStepMetadata:
    index: int
    title: str
    step_type: str
    anchor: bool = False


@dataclass(frozen=True)
class CompiledRecipeStep:
    metadata: RecipeStepMetadata
    tree: BehaviorTree
    source_step: dict[str, Any]
    context: JsonBTCompilerContext


StepBuilder = Callable[[dict[str, Any], JsonBTCompilerContext], BehaviorTree]


def get_json_bt_step_types() -> tuple[str, ...]:
    return tuple(sorted(CANONICAL_STEP_TYPES))


def load_recipe(path_or_name: str | Path) -> dict[str, Any]:
    path = Path(path_or_name)
    if not path.suffix:
        path = path.with_suffix(".json")
    if not path.is_absolute():
        from .paths import modular_data_root

        path = Path(modular_data_root()) / path
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(data, dict):
        raise RecipeCompileError(f"Recipe {path} must be a JSON object.")
    return data


def compile_file_to_bt(path: str | Path, *, recipe_name: str | None = None) -> BehaviorTree:
    recipe = load_recipe(path)
    return compile_recipe_to_bt(recipe, recipe_name=recipe_name or str(recipe.get("name") or Path(path).stem))


def compile_recipe_to_bt(recipe: dict[str, Any], *, recipe_name: str) -> BehaviorTree:
    compiled_steps = compile_recipe_steps_to_bt(recipe, recipe_name=recipe_name)
    if not compiled_steps:
        return BehaviorTree(BehaviorTree.SucceederNode(name=f"{recipe_name or 'Recipe'}::NoOp"))
    metadata = tuple(compiled.metadata for compiled in compiled_steps)
    children = [
        _as_subtree(
            compiled.metadata.title,
            compiled.tree,
            step_metadata=compiled.metadata,
        )
        for compiled in compiled_steps
    ]
    root = BehaviorTree.SequenceNode(name=recipe_name or "JSON Recipe", children=children)
    root.modular_step_metadata = metadata
    return BehaviorTree(root)


def compile_recipe_steps_to_bt(recipe: dict[str, Any], *, recipe_name: str) -> tuple[CompiledRecipeStep, ...]:
    if not isinstance(recipe, dict):
        raise RecipeCompileError("Recipe must be a JSON object.")

    steps = _recipe_steps(recipe, recipe_name)
    audit = audit_recipe_vocabulary(recipe, recipe_name=recipe_name)
    if audit.has_issues:
        first = audit.issues[0]
        raise UnknownRecipeStepType(
            f"Recipe {recipe_name!r} step {first.index + 1} uses {first.step_type!r}: {first.reason}."
        )

    context = JsonBTCompilerContext(
        recipe_name=recipe_name,
        required_hero=recipe.get("required_hero"),
        metadata={"required_hero": recipe.get("required_hero")},
    )
    expanded_steps = _expand_steps(steps)
    metadata = _step_metadata(expanded_steps)
    return tuple(
        CompiledRecipeStep(
            metadata=metadata[index],
            tree=compile_recipe_step_to_bt(step, context),
            source_step=dict(step),
            context=context,
        )
        for index, step in enumerate(expanded_steps)
    )


def recipe_step_metadata(recipe: dict[str, Any], *, recipe_name: str | None = None) -> tuple[RecipeStepMetadata, ...]:
    name = str(recipe_name or recipe.get("name") or "Recipe") if isinstance(recipe, dict) else "Recipe"
    steps = _recipe_steps(recipe, name) if isinstance(recipe, dict) else []
    return _step_metadata(_expand_steps(steps))


def compile_step_to_bt(step: dict[str, Any], context: JsonBTCompilerContext) -> BehaviorTree:
    if not isinstance(step, dict):
        raise RecipeCompileError("Step must be a JSON object.")
    step_type = _validate_step_type(step.get("type"), recipe_name=context.recipe_name, step_idx=0)
    return _BUILDERS[step_type](step, context)


def compile_recipe_step_to_bt(step: dict[str, Any], context: JsonBTCompilerContext) -> BehaviorTree:
    return _with_post_wait(compile_step_to_bt(step, context), step)


def audit_recipe_vocabulary(recipe: dict[str, Any], *, recipe_name: str | None = None) -> VocabularyAudit:
    name = str(recipe_name or recipe.get("name") or "Recipe") if isinstance(recipe, dict) else "Recipe"
    steps = _recipe_steps(recipe, name) if isinstance(recipe, dict) else []
    issues: list[VocabularyIssue] = []
    for index, step in enumerate(steps):
        if not isinstance(step, dict):
            issues.append(VocabularyIssue(index=index, step_type="<non-object-step>", reason="step must be an object"))
            continue
        step_type = _normalize_step_type(step.get("type"))
        if not step_type:
            issues.append(VocabularyIssue(index=index, step_type="<missing>", reason="missing type"))
        elif step_type in LEGACY_STEP_TYPES:
            issues.append(VocabularyIssue(index=index, step_type=step_type, reason="legacy type pending migration"))
        elif step_type not in CANONICAL_STEP_TYPES:
            issues.append(VocabularyIssue(index=index, step_type=step_type, reason="unknown type"))
    return VocabularyAudit(recipe_name=name, steps=len(steps), issues=tuple(issues))


def _build_route(step: dict[str, Any], _context: JsonBTCompilerContext) -> BehaviorTree:
    mode = _choice(step, "mode", "move")
    log = _bool(step.get("log", step.get("debug")), False)
    pause_on_combat = _route_pause_on_combat(step, mode)
    if mode == "exit":
        point = _require_point(step)
        return BT.Movement.MoveAndExitMap(
            x=point[0],
            y=point[1],
            target_map_id=_int(step.get("target_map_id", step.get("map_id")), 0),
            target_map_name=_text(step, "target_map_name", ""),
            move_tolerance=_float(step.get("tolerance", step.get("move_tolerance")), DEFAULT_ROUTE_TOLERANCE),
            pause_on_combat=pause_on_combat,
            log=log,
        )
    if mode == "nudge":
        point = _require_point(step)
        return _nudge_tree(
            x=point[0],
            y=point[1],
            pulses=max(1, _int(step.get("pulses"), 1)),
            pulse_ms=max(0, _int(step.get("pulse_ms"), 150)),
        )
    if mode == "target":
        return _route_to_target_tree(step, _context)
    points = _points(step)
    if mode == "kill":
        return BT.Movement.MoveAndKillPath(
            pos=points,
            clear_area_radius=_float(step.get("clear_area_radius", step.get("range")), 2500.0),
            pause_on_combat=pause_on_combat,
        )
    return BT.Movement.MovePath(
        pos=points,
        pause_on_combat=pause_on_combat,
        tolerance=_float(step.get("tolerance"), DEFAULT_ROUTE_TOLERANCE),
        log=log,
    )


def _route_pause_on_combat(step: dict[str, Any], mode: str) -> bool:
    default = mode == "kill"
    return _bool(step.get("pause_on_combat"), default)


def _build_interact(step: dict[str, Any], context: JsonBTCompilerContext) -> BehaviorTree:
    action = _choice(step, "action", "target")
    log = _bool(step.get("log"), False)
    if action == "dialog":
        ids = _dialog_ids(step)
        if not ids:
            raise RecipeCompileError(f"Recipe {context.recipe_name!r} interact dialog requires id.")
        interval_ms = max(0, _int(step.get("interval_ms"), 0))
        trees: list[BehaviorTree] = []
        for dialog_id in ids:
            if _has_selector(step):
                trees.append(_interact_and_dialog_tree(step, context, dialog_id))
            else:
                trees.append(BT.Player.SendDialog(dialog_id=dialog_id, log=_bool(step.get("log"), False)))
            if interval_ms:
                trees.append(BT.Player.Wait(interval_ms, log=False))
        return _sequence("InteractDialog", trees)
    if action == "auto_dialog":
        button = _int(step.get("button", step.get("button_number")), 0)
        return BT.Player.SendAutomaticDialog(button_number=button, log=log)
    if action == "drop_bundle":
        return BT.Party.DropBundle(log=log)
    if action == "target":
        target = _choice(step, "target", _choice(step, "kind", "npc"))
        if target in {"npc", "gadget", "item"}:
            return _interact_tree(step, context, target)
        raise RecipeCompileError(f"Recipe {context.recipe_name!r} has unsupported interact target {target!r}.")
    raise RecipeCompileError(f"Recipe {context.recipe_name!r} has unsupported interact action {action!r}.")


def _build_map(step: dict[str, Any], context: JsonBTCompilerContext) -> BehaviorTree:
    action = _choice(step, "action", "travel")
    if action == "travel":
        log = _bool(step.get("log"), False)
        return _sequence(
            "MapTravel",
            [
                BT.Party.LeaveParty(log=log),
                BT.Map.TravelToOutpost(
                    outpost_id=_int(step.get("target_map_id", step.get("map_id")), 0),
                    outpost_name=_text(step, "target_map_name", ""),
                    log=log,
                    timeout=_int(step.get("timeout_ms", step.get("timeout")), 10000),
                ),
            ],
        )
    if action == "enter_challenge":
        return BT.Map.EnterChallenge(
            target_map_id=_int(step.get("target_map_id", step.get("map_id")), 0),
            target_map_name=_text(step, "target_map_name", ""),
            delay_ms=_int(step.get("delay_ms"), 3000),
            timeout=_int(step.get("timeout_ms", step.get("timeout")), 30000),
            log=_bool(step.get("log"), False),
        )
    if action == "wait_for_map_load":
        return BT.Map.WaitforMapLoad(
            map_id=_int(step.get("target_map_id", step.get("map_id")), 0),
            map_name=_text(step, "target_map_name", ""),
            timeout=_int(step.get("timeout_ms", step.get("timeout", step.get("ms"))), 10000),
            log=_bool(step.get("log"), False),
        )
    raise RecipeCompileError(f"Recipe {context.recipe_name!r} has unsupported map action {action!r}.")


def _build_party(step: dict[str, Any], context: JsonBTCompilerContext) -> BehaviorTree:
    action = _choice(step, "action", "")
    log = _bool(step.get("log"), False)
    if action == "load":
        return BT.Party.LoadParty(
            hero_ids=_party_hero_ids(step, context),
            henchman_ids=_int_list(step.get("henchman_ids", step.get("henchmen"))),
            clear_existing=_bool(step.get("clear_existing"), False),
            log=log,
        )
    if action == "flag_heroes":
        point = _require_point(step)
        return BT.Party.FlagAllHeroes(point[0], point[1], log=log)
    if action == "unflag_heroes":
        return BT.Party.UnflagAllHeroes(log=log)
    if action == "force_hero_state":
        return BT.Party.ForceHeroState(_hero_state(step.get("state", step.get("behavior"))), log=log)
    if action == "resign":
        return BT.Party.Resign(log=log)
    if action == "abandon_quest":
        return BT.Party.AbandonQuest(_int(step.get("quest_id", step.get("id")), 0), log=log)
    raise RecipeCompileError(f"Recipe {context.recipe_name!r} has unsupported party action {action!r}.")


def _build_behavior(step: dict[str, Any], context: JsonBTCompilerContext) -> BehaviorTree:
    action = _choice(step, "action", "enemy_blacklist")
    if action == "enemy_blacklist":
        return _action_tree(f"Behavior::{action}", lambda: _behavior_action(step, action))
    raise RecipeCompileError(f"Recipe {context.recipe_name!r} has unsupported behavior action {action!r}.")


def _build_inventory(step: dict[str, Any], context: JsonBTCompilerContext) -> BehaviorTree:
    action = _choice(step, "action", "use_consumables")
    if action == "use_consumables":
        return _action_tree("UseConsumables", lambda: _use_consumables(step))
    if action == "broadcast_summoning_stone":
        from Py4GWCoreLib.enums_src.Multiboxing_enums import SharedCommandType

        return BT.Shared.SendAndWait(
            SharedCommandType.UseSummoningStone,
            include_self=True,
            refs_blackboard_key="summoning_stone_refs",
            timeout_ms=_int(step.get("timeout_ms"), 5000),
            log=_bool(step.get("log"), False),
        )
    raise RecipeCompileError(f"Recipe {context.recipe_name!r} has unsupported inventory action {action!r}.")


def _build_wait(step: dict[str, Any], _context: JsonBTCompilerContext) -> BehaviorTree:
    action = _choice(step, "action", "wait")
    if action == "emote":
        command = _text(step, "command", "")
        if not command:
            raise RecipeCompileError("wait action emote requires command.")
        return BT.Player.SendChatCommand(command.lstrip("/"), log=_bool(step.get("log"), False))
    return BT.Player.Wait(_int(step.get("ms", step.get("duration_ms")), 0), log=_bool(step.get("log"), False))


_BUILDERS: dict[str, StepBuilder] = {
    "behavior": _build_behavior,
    "interact": _build_interact,
    "inventory": _build_inventory,
    "map": _build_map,
    "party": _build_party,
    "route": _build_route,
    "wait": _build_wait,
}


def _recipe_steps(recipe: dict[str, Any], recipe_name: str) -> list[dict[str, Any]]:
    steps = recipe.get("steps", [])
    if steps is None:
        return []
    if not isinstance(steps, list):
        raise RecipeCompileError(f"Recipe {recipe_name!r} must define steps as a list.")
    return steps


def _validate_step_type(value: Any, *, recipe_name: str, step_idx: int) -> str:
    step_type = _normalize_step_type(value)
    if not step_type:
        raise UnknownRecipeStepType(f"Recipe {recipe_name!r} step {step_idx + 1} is missing type.")
    if step_type in LEGACY_STEP_TYPES:
        raise UnknownRecipeStepType(
            f"Recipe {recipe_name!r} step {step_idx + 1} uses legacy type {step_type!r}; migrate it."
        )
    if step_type not in CANONICAL_STEP_TYPES:
        raise UnknownRecipeStepType(
            f"Recipe {recipe_name!r} step {step_idx + 1} has unknown type {step_type!r}."
        )
    return step_type


def _expand_steps(steps: list[dict[str, Any]]) -> list[dict[str, Any]]:
    expanded: list[dict[str, Any]] = []
    for step in steps:
        repeat = max(1, _int(step.get("repeat"), 1))
        for _ in range(repeat):
            expanded.append(step)
    return expanded


def _step_metadata(steps: list[dict[str, Any]]) -> tuple[RecipeStepMetadata, ...]:
    return tuple(
        RecipeStepMetadata(
            index=index + 1,
            title=_step_title(step, index),
            step_type=_normalize_step_type(step.get("type")),
            anchor=_bool(step.get("anchor"), False),
        )
        for index, step in enumerate(steps)
    )


def _step_title(step: dict[str, Any], index: int) -> str:
    name = _text(step, "name", "")
    if name:
        return name
    step_type = _normalize_step_type(step.get("type")) or "step"
    action = _text(step, "action", _text(step, "mode", ""))
    suffix = f"::{action}" if action else ""
    return f"{index + 1}. {step_type}{suffix}"


def _as_subtree(
    name: str,
    tree: BehaviorTree,
    *,
    step_metadata: RecipeStepMetadata | None = None,
) -> BehaviorTree.SubtreeNode:
    subtree = BehaviorTree.SubtreeNode(name=name, subtree_fn=lambda _node, _tree=tree: _tree)
    if step_metadata is not None:
        subtree.modular_step_index = step_metadata.index
        subtree.modular_step_name = step_metadata.title
        subtree.modular_step_type = step_metadata.step_type
        subtree.modular_anchor = step_metadata.anchor
    return subtree


def _with_post_wait(tree: BehaviorTree, step: dict[str, Any]) -> BehaviorTree:
    wait_ms = _int(step.get("ms"), 0)
    if wait_ms <= 0 or _normalize_step_type(step.get("type")) == "wait":
        return tree
    return _sequence("StepWithPostWait", [tree, BT.Player.Wait(wait_ms, log=False)])


def _sequence(name: str, trees: list[BehaviorTree]) -> BehaviorTree:
    if not trees:
        return BehaviorTree(BehaviorTree.SucceederNode(name=f"{name}::NoOp"))
    return BT.Composite.Sequence(*trees, name=name)


def _action_tree(name: str, action: Callable[[], BehaviorTree.NodeState | None]) -> BehaviorTree:
    def _run() -> BehaviorTree.NodeState:
        result = action()
        return result if isinstance(result, BehaviorTree.NodeState) else BehaviorTree.NodeState.SUCCESS

    return BehaviorTree(BehaviorTree.ActionNode(name=name, action_fn=_run))


def _interact_tree(step: dict[str, Any], context: JsonBTCompilerContext, target: str) -> BehaviorTree:
    log = _bool(step.get("log"), False)
    point = _point(step)
    if target == "item":
        model_id = _int(step.get("model_id", step.get("id")), 0)
        if model_id:
            return _optional_item_by_model_interact_tree(step, point, log=log)
    if point is not None:
        return BT.Composite.Sequence(
            _move_to_point_tree(step, point, log=log),
            _interact_delay_tree(step),
            _target_tree(step, context, target),
            BT.Player.InteractTarget(log=log),
            name=f"Interact{target.title()}AtPoint",
        )
    return BT.Composite.Sequence(
        _target_tree(step, context, target),
        _move_to_selected_target_tree(step, log=log),
        _interact_delay_tree(step),
        _target_tree(step, context, target),
        BT.Player.InteractTarget(log=log),
        name=f"Interact{target.title()}",
    )


def _route_to_target_tree(step: dict[str, Any], context: JsonBTCompilerContext) -> BehaviorTree:
    log = _bool(step.get("log"), False)
    target = _choice(step, "target", _choice(step, "kind", "enemy"))
    return BT.Composite.Sequence(
        _target_tree(step, context, target),
        _move_to_selected_target_tree(step, log=log),
        name=f"RouteTo{target.title()}Target",
    )


def _interact_and_dialog_tree(step: dict[str, Any], context: JsonBTCompilerContext, dialog_id: str | int) -> BehaviorTree:
    log = _bool(step.get("log"), False)
    target = _choice(step, "target", _choice(step, "kind", "npc"))
    if "gadget" in step and "target" not in step and "kind" not in step:
        target = "gadget"
    point = _point(step)
    move_tree = (
        _move_to_point_tree(step, point, log=log)
        if point is not None
        else BT.Composite.Sequence(
            _target_tree(step, context, target),
            _move_to_selected_target_tree(step, log=log),
            name="MoveToResolvedDialogTarget",
        )
    )
    return BT.Composite.Sequence(
        move_tree,
        _interact_delay_tree(step),
        _target_tree(step, context, target),
        BT.Player.InteractTarget(log=log),
        _dialog_delay_tree(step),
        BT.Player.SendDialog(dialog_id=dialog_id, log=log),
        name="InteractDialog",
    )


def _move_to_point_tree(step: dict[str, Any], point: tuple[float, float], *, log: bool) -> BehaviorTree:
    return BT.Movement.Move(
        x=point[0],
        y=point[1],
        tolerance=_float(step.get("move_tolerance", step.get("tolerance")), 150.0),
        pause_on_combat=_bool(step.get("pause_on_combat"), True),
        log=log,
    )


def _move_to_selected_target_tree(step: dict[str, Any], *, log: bool) -> BehaviorTree:
    tolerance = _float(step.get("move_tolerance", step.get("tolerance")), 150.0)
    pause_on_combat = _bool(step.get("pause_on_combat"), True)

    def _move_to_selected_target(_node: BehaviorTree.Node) -> BehaviorTree:
        from Py4GWCoreLib import Agent, Player

        target_id = int(Player.GetTargetID() or 0)
        if target_id <= 0 or not Agent.IsValid(target_id):
            return BehaviorTree(BehaviorTree.FailerNode(name="MoveToSelectedTargetMissingTarget"))
        x, y = Agent.GetXY(target_id)
        return BT.Movement.Move(
            x=float(x),
            y=float(y),
            tolerance=tolerance,
            pause_on_combat=pause_on_combat,
            log=log,
        )

    return BehaviorTree(BehaviorTree.SubtreeNode(name="MoveToSelectedTarget", subtree_fn=_move_to_selected_target))


def _interact_delay_tree(step: dict[str, Any]) -> BehaviorTree:
    delay_ms = max(0, _int(step.get("interact_delay_ms", step.get("settle_ms")), DEFAULT_INTERACT_DELAY_MS))
    return BT.Player.Wait(delay_ms, log=False) if delay_ms > 0 else BehaviorTree(BehaviorTree.SucceederNode(name="NoInteractDelay"))


def _dialog_delay_tree(step: dict[str, Any]) -> BehaviorTree:
    delay_ms = max(0, _int(step.get("dialog_delay_ms"), DEFAULT_DIALOG_DELAY_MS))
    return BT.Player.Wait(delay_ms, log=False) if delay_ms > 0 else BehaviorTree(BehaviorTree.SucceederNode(name="NoDialogDelay"))


def _target_tree(step: dict[str, Any], context: JsonBTCompilerContext, target: str) -> BehaviorTree:
    log = _bool(step.get("log"), False)
    point = _point(step)
    max_dist = _float(step.get("max_dist"), 4500.0)
    model_id = _int(step.get("model_id"), 0)
    if target == "item":
        model_id = _int(step.get("model_id", step.get("id")), 0)
        if model_id:
            return _target_item_by_model(model_id, max_dist=max_dist)
        if point is not None:
            return BT.Agents.TargetNearestItemXY(point[0], point[1], max_dist, log=log)
        return BT.Agents.TargetNearestItem(distance=max_dist, log=log)
    if model_id:
        return BT.Agents.TargetAgentByModelID(model_id, log=log)
    named_key = _selector_key(step, target)
    if named_key:
        return _target_named_agent(target, named_key, max_dist=max_dist)
    if point is not None and target == "npc":
        return BT.Agents.TargetNearestNPCXY(point[0], point[1], max_dist, log=log)
    if point is not None and target == "gadget":
        return BT.Agents.TargetNearestGadgetXY(point[0], point[1], max_dist, log=log)
    if target == "npc" and _bool(step.get("nearest"), False):
        return BT.Agents.TargetNearestNPC(distance=max_dist, log=log)
    if target == "gadget" and _bool(step.get("nearest"), False):
        return _target_nearest_gadget(max_dist, log=log)
    raise RecipeCompileError(
        f"Recipe {context.recipe_name!r} cannot target {target!r} without point, model_id, named selector, or nearest=true."
    )


def _target_named_agent(kind: str, key: str, *, max_dist: float) -> BehaviorTree:
    from .domain.target_registry import get_named_agent_target

    definition = get_named_agent_target(kind, key)
    if definition is None:
        raise RecipeCompileError(f"Unknown {kind} selector {key!r}.")

    def _target() -> BehaviorTree.NodeState:
        from Py4GWCoreLib import AgentArray, Player

        px, py = Player.GetXY()
        agents = _agents_for_kind(kind)
        agents = AgentArray.Filter.ByDistance(agents, (px, py), max_dist)
        agents = AgentArray.Sort.ByDistance(agents, (px, py))
        for agent_id in agents:
            if _agent_matches_definition(int(agent_id), definition):
                Player.ChangeTarget(int(agent_id))
                return BehaviorTree.NodeState.SUCCESS
        return BehaviorTree.NodeState.FAILURE

    return _action_tree(f"Target{kind.title()}::{key}", _target)


def _agents_for_kind(kind: str) -> list[int]:
    from Py4GWCoreLib import AgentArray

    if kind == "gadget":
        return list(AgentArray.GetGadgetArray())
    if kind == "enemy":
        return list(AgentArray.GetEnemyArray())
    return list(AgentArray.GetNPCMinipetArray())


def _agent_matches_definition(agent_id: int, definition: Any) -> bool:
    model_id = int(getattr(definition, "model_id", 0) or 0)
    if model_id:
        try:
            from Py4GWCoreLib import Agent

            return int(Agent.GetModelID(agent_id)) == model_id
        except Exception:
            return False

    encoded_name = _agent_encoded_name(agent_id)
    if encoded_name and encoded_name in getattr(definition, "encoded_names", ()):
        return True

    display_name = str(getattr(definition, "display_name", "") or "").strip()
    if display_name:
        try:
            from .domain.target_registry import normalize_target_key
            from Py4GWCoreLib import Agent

            return normalize_target_key(Agent.GetNameByID(agent_id)) == normalize_target_key(display_name)
        except Exception:
            return False
    return False


def _agent_encoded_name(agent_id: int) -> tuple[int, ...]:
    try:
        from PyAgent import PyAgent

        return tuple(int(value) for value in PyAgent.GetAgentEncName(agent_id))
    except Exception:
        return ()


def _target_nearest_gadget(max_dist: float, *, log: bool = False) -> BehaviorTree:
    def _target() -> BehaviorTree.NodeState:
        from Py4GWCoreLib import Agent, AgentArray, Player

        px, py = Player.GetXY()
        gadgets = AgentArray.GetGadgetArray()
        gadgets = AgentArray.Filter.ByDistance(gadgets, (px, py), max_dist)
        gadgets = AgentArray.Sort.ByDistance(gadgets, (px, py))
        if not gadgets:
            return BehaviorTree.NodeState.FAILURE
        Player.ChangeTarget(int(gadgets[0]))
        return BehaviorTree.NodeState.SUCCESS

    return _action_tree("TargetNearestGadget", _target)


def _optional_item_by_model_interact_tree(step: dict[str, Any], point: tuple[float, float] | None, *, log: bool) -> BehaviorTree:
    model_id = _int(step.get("model_id", step.get("id")), 0)
    max_dist = _float(step.get("max_dist"), 4500.0)
    state: dict[str, bool | int] = {"found": False, "missing_logged": False}

    def _target_optional_item() -> BehaviorTree.NodeState:
        from Py4GWCoreLib import Player

        agent_id = _find_item_agent_by_model(model_id, max_dist)
        if agent_id <= 0:
            state["found"] = False
            if not bool(state.get("missing_logged", False)):
                _log_optional_item_missing(model_id, max_dist)
                state["missing_logged"] = True
            return BehaviorTree.NodeState.SUCCESS
        state["found"] = True
        state["agent_id"] = int(agent_id)
        Player.ChangeTarget(int(agent_id))
        return BehaviorTree.NodeState.SUCCESS

    def _move_if_found(_node: BehaviorTree.Node) -> BehaviorTree:
        if not bool(state.get("found", False)):
            return BehaviorTree(BehaviorTree.SucceederNode(name="OptionalItemMissingSkipMove"))
        return _move_to_selected_target_tree(step, log=log)

    def _interact_if_found(_node: BehaviorTree.Node) -> BehaviorTree:
        if not bool(state.get("found", False)):
            return BehaviorTree(BehaviorTree.SucceederNode(name="OptionalItemMissingSkipInteract"))
        return BT.Player.InteractTarget(log=log)

    if point is not None:
        return BT.Composite.Sequence(
            _move_to_point_tree(step, point, log=log),
            _interact_delay_tree(step),
            _action_tree(f"OptionalTargetItemByModel::{model_id}", _target_optional_item),
            BehaviorTree(BehaviorTree.SubtreeNode(name="OptionalInteractItemByModel", subtree_fn=_interact_if_found)),
            name=f"OptionalInteractItemByModel::{model_id}",
        )
    return BT.Composite.Sequence(
        _action_tree(f"OptionalTargetItemByModel::{model_id}", _target_optional_item),
        BehaviorTree(BehaviorTree.SubtreeNode(name="OptionalMoveToItemByModel", subtree_fn=_move_if_found)),
        _interact_delay_tree(step),
        _action_tree(f"OptionalRetargetItemByModel::{model_id}", _target_optional_item),
        BehaviorTree(BehaviorTree.SubtreeNode(name="OptionalInteractItemByModel", subtree_fn=_interact_if_found)),
        name=f"OptionalInteractItemByModel::{model_id}",
    )


def _target_item_by_model(model_id: int, *, max_dist: float) -> BehaviorTree:
    return _action_tree(f"TargetItemByModel::{model_id}", lambda: _target_item_by_model_action(model_id, max_dist))


def _target_item_by_model_action(model_id: int, max_dist: float) -> BehaviorTree.NodeState:
    agent_id = _find_item_agent_by_model(model_id, max_dist)
    if agent_id <= 0:
        return BehaviorTree.NodeState.FAILURE
    from Py4GWCoreLib import Player

    Player.ChangeTarget(int(agent_id))
    return BehaviorTree.NodeState.SUCCESS


def _find_item_agent_by_model(model_id: int, max_dist: float) -> int:
    from Py4GWCoreLib import Agent
    from Py4GWCoreLib import AgentArray
    from Py4GWCoreLib import Item
    from Py4GWCoreLib import Player

    px, py = Player.GetXY()
    items = AgentArray.GetItemArray()
    items = AgentArray.Filter.ByDistance(items, (px, py), max_dist)
    items = AgentArray.Sort.ByDistance(items, (px, py))
    for agent_id in items:
        try:
            item_id = int(Agent.GetItemAgentItemID(int(agent_id)) or 0)
            if item_id <= 0 or int(Item.GetModelID(item_id) or 0) != int(model_id):
                continue
        except Exception:
            continue
        return int(agent_id)
    return 0


def _log_optional_item_missing(model_id: int, max_dist: float) -> None:
    try:
        from Py4GWCoreLib import Console
        from Py4GWCoreLib import ConsoleLog

        ConsoleLog(
            "Modular",
            f"Optional item model_id {int(model_id)} not found within {float(max_dist):.0f}; continuing.",
            Console.MessageType.Warning,
        )
    except Exception:
        pass


def _nudge_tree(x: float, y: float, *, pulses: int, pulse_ms: int) -> BehaviorTree:
    trees: list[BehaviorTree] = []
    for _ in range(pulses):
        trees.append(_action_tree("NudgeMove", lambda _x=x, _y=y: _player_move(_x, _y)))
        if pulse_ms:
            trees.append(BT.Player.Wait(pulse_ms, log=False))
    return _sequence("NudgeMove", trees)


def _player_move(x: float, y: float) -> BehaviorTree.NodeState:
    from Py4GWCoreLib import Player

    Player.Move(float(x), float(y))
    return BehaviorTree.NodeState.SUCCESS


def _behavior_action(step: dict[str, Any], action: str) -> BehaviorTree.NodeState:
    if action == "enemy_blacklist":
        from Py4GWCoreLib.EnemyBlacklist import EnemyBlacklist

        enemy = _text(step, "enemy", "")
        if not enemy:
            return BehaviorTree.NodeState.FAILURE
        if _choice(step, "mode", "add") == "remove":
            EnemyBlacklist().remove_name(enemy)
        else:
            EnemyBlacklist().add_name(enemy)
    return BehaviorTree.NodeState.SUCCESS


def _use_consumables(step: dict[str, Any]) -> BehaviorTree.NodeState:
    from Py4GWCoreLib import GLOBAL_CACHE
    from Py4GWCoreLib.routines_src.behaviourtrees_src.botting_consumables import consumable_specs
    from Py4GWCoreLib.routines_src.behaviourtrees_src.botting_consumables import normalize_consumable_mode
    from Py4GWCoreLib.routines_src.behaviourtrees_src.botting_consumables import send_consumable_to_accounts
    from Py4GWCoreLib.routines_src.behaviourtrees_src.botting_consumables import should_skip_local_consumable_for_non_leader
    from Py4GWCoreLib.routines_src.behaviourtrees_src.botting_consumables import use_local_consumable

    mode = normalize_consumable_mode(step.get("mode"), default="all")
    if not mode:
        return BehaviorTree.NodeState.FAILURE

    multibox = _bool(step.get("multibox"), False)
    leader_only = _bool(step.get("leader_only"), True)
    skip_local = should_skip_local_consumable_for_non_leader(leader_only=leader_only)
    for model_id, effect_name in consumable_specs(mode):
        effect_id = int(GLOBAL_CACHE.Skill.GetID(effect_name) or 0)
        if not skip_local:
            use_local_consumable(int(model_id), effect_id)
        if multibox:
            send_consumable_to_accounts(int(model_id), effect_id)
    return BehaviorTree.NodeState.SUCCESS


def _hero_state(value: Any) -> int:
    aliases = {"fight": 0, "guard": 1, "avoid": 2}
    text = str(value or "").strip().lower()
    return aliases.get(text, _int(value, 0))


def _party_hero_ids(step: dict[str, Any], context: JsonBTCompilerContext) -> list[int]:
    explicit = _int_list(step.get("hero_ids", step.get("heroes")))
    if explicit:
        return explicit

    from .hero_setup_model import get_team_by_priority
    from .hero_setup_model import resolve_hero_ids

    required_source = step.get("required_hero", context.required_hero)
    required = resolve_hero_ids(required_source)
    if required_source and not required:
        raise RecipeCompileError(f"Recipe {context.recipe_name!r} has unresolved required_hero {required_source!r}.")

    max_heroes = max(1, _int(step.get("max_heroes"), 7))
    hero_ids = get_team_by_priority(max_heroes=max_heroes, required_hero_ids=required)
    if max_heroes > 1 and not hero_ids:
        raise RecipeCompileError(f"Recipe {context.recipe_name!r} party load resolved to an empty hero list.")
    return hero_ids


def _has_selector(step: dict[str, Any]) -> bool:
    target = _choice(step, "target", "npc")
    return (
        _point(step) is not None
        or _int(step.get("model_id"), 0) > 0
        or bool(_selector_key(step, target))
        or bool(_selector_key(step, "npc"))
        or bool(_selector_key(step, "gadget"))
        or bool(_selector_key(step, "enemy"))
        or _bool(step.get("nearest"), False)
    )


def _dialog_ids(step: dict[str, Any]) -> list[str | int]:
    raw = step.get("ids", step.get("id", step.get("dialog_id")))
    if isinstance(raw, list):
        return [value for value in raw if value is not None]
    if raw is None:
        return []
    return [raw]


def _selector_key(step: dict[str, Any], target: str) -> str:
    for key in (target, "selector"):
        value = step.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def _points(step: dict[str, Any]) -> list[tuple[float, float]]:
    raw_points = step.get("points")
    if isinstance(raw_points, list):
        points = [_coerce_point(value) for value in raw_points]
        points = [point for point in points if point is not None]
        if points:
            return points
    point = _point(step)
    if point is None:
        raise RecipeCompileError("route step requires point or points.")
    return [point]


def _require_point(step: dict[str, Any]) -> tuple[float, float]:
    point = _point(step)
    if point is None:
        raise RecipeCompileError(f"{_normalize_step_type(step.get('type')) or 'step'} requires point [x, y].")
    return point


def _point(step: dict[str, Any]) -> tuple[float, float] | None:
    point = _coerce_point(step.get("point"))
    if point is not None:
        return point
    if "x" in step and "y" in step:
        return _coerce_point((step.get("x"), step.get("y")))
    return None


def _coerce_point(value: Any) -> tuple[float, float] | None:
    if not isinstance(value, (list, tuple)) or len(value) < 2:
        return None
    try:
        return float(value[0]), float(value[1])
    except (TypeError, ValueError):
        return None


def _int_list(value: Any) -> list[int]:
    if not isinstance(value, list):
        return []
    parsed: list[int] = []
    for item in value:
        number = _int(item, 0)
        if number > 0:
            parsed.append(number)
    return parsed


def _int(value: Any, default: int) -> int:
    try:
        if isinstance(value, str):
            return int(value, 0)
        return int(value)
    except (TypeError, ValueError):
        return default


def _float(value: Any, default: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _bool(value: Any, default: bool) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"1", "true", "yes", "on"}:
            return True
        if normalized in {"0", "false", "no", "off"}:
            return False
    return default


def _choice(step: dict[str, Any], key: str, default: str) -> str:
    return _text(step, key, default).lower()


def _text(step: dict[str, Any], key: str, default: str) -> str:
    value = step.get(key, default)
    return str(value if value is not None else default).strip()


def _normalize_step_type(value: Any) -> str:
    return str(value or "").strip().lower()


def _optional_str(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None
