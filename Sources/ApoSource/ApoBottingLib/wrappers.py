from collections.abc import Callable
from collections.abc import Mapping
from collections.abc import Sequence as SequenceABC
from typing import cast

from .helpers import _capture_current_target
from .helpers import _coerce_vanquish_step
from .helpers import _final_point
from .helpers import _movement_with_runtime_pause
from .helpers import _pause_heroai_for_action
from .helpers import _POST_MOVEMENT_SETTLE_MS
from .helpers import _send_multibox_auto_dialog
from .helpers import _send_multibox_get_blessing_with_target
from .helpers import _send_multibox_dialog_to_target
from .helpers import _send_multibox_manual_dialog
from .helpers import _send_multibox_take_dialog_with_target
from .helpers import _wait_special
from .helpers import _wait_until_player_stops_moving
from Py4GWCoreLib.BottingTree import BottingTree
from Py4GWCoreLib.py4gwcorelib_src.BehaviorTree import BehaviorTree
from Py4GWCoreLib.routines_src.BehaviourTrees import BT as RoutinesBT
from Py4GWCoreLib.routines_src.behaviourtrees_src.player import BT

def Node(tree_or_node) -> BehaviorTree.Node:
    return BehaviorTree.Node._coerce_node(tree_or_node)

from Py4GWCoreLib.native_src.internals.types import PointPath
from Py4GWCoreLib.native_src.internals.types import PointOrPath
from Py4GWCoreLib.enums import PlayerStatus
from Py4GWCoreLib.enums import Range
from Py4GWCoreLib.enums_src.Multiboxing_enums import SharedCommandType
from Py4GWCoreLib.enums_src.IO_enums import Key
from Py4GWCoreLib.enums_src.UI_enums import ControlAction
#region nodes

def Sequence(name: str, 
             map_id_or_name: int | str = 0,
             map_prep: BehaviorTree | BehaviorTree.Node | None = None,
             children: SequenceABC[BehaviorTree | BehaviorTree.Node] | None = None,
             random_travel: bool = False,
             region_pool: str = "eu",
             hard_mode: bool | None = None,
             ) -> BehaviorTree:
    """
    Build a sequence wrapper with an optional leading map-travel step.

    Parameters
    ----------
    name
        Name assigned to the underlying `BehaviorTree.SequenceNode`.
    map_id_or_name
        Optional outpost destination to prepend before `children`.
        Pass `0` or `""` to skip travel.
        Pass an `int` to travel by map id.
        Pass a `str` to travel by map name.
    map_prep
        Optional node or tree to run immediately after the optional travel step
        and before `children`.
    children
        Child nodes run after the optional travel step.
        If omitted, a single `SucceederNode` is used so the wrapper still
        produces a valid sequence.
    random_travel
        When `True`, use random-district travel for the prepended travel step.
    region_pool
        Region pool forwarded to random travel.
    hard_mode
        Optional party difficulty applied after the prepended travel step.
        Pass `True` for hard mode, `False` for normal mode, or `None` to skip.

    Returns
    -------
    BehaviorTree
        A sequence tree containing the optional travel node first, then
        `map_prep` when provided, followed by the provided `children`.
    """
    resolved_children = list(children) if children is not None else [Succeeder()]

    travel_child = [Travel(target_map_id=map_id_or_name if isinstance(map_id_or_name, int) else 0,
                           target_map_name=map_id_or_name if isinstance(map_id_or_name, str) else "",
                           random_travel=random_travel,
                           region_pool=region_pool,
                           hard_mode=hard_mode,
                          )] if map_id_or_name else []

    prep_child = [BehaviorTree(Node(map_prep))] if map_prep is not None else []

    resolved_children = travel_child + prep_child + resolved_children
    
    return BehaviorTree(
        BehaviorTree.SequenceNode(
            name=name,
            children=resolved_children,
        )
    )
    

def Repeater(
    name: str,
    repeat_count: int = 1,
    children: SequenceABC[BehaviorTree | BehaviorTree.Node] | None = None,
) -> BehaviorTree:
    """
    Build a repeater wrapper that always repeats a sequence of children.

    Parameters
    ----------
    name
        Base name assigned to the repeater and its inner sequence.
    repeat_count
        Number of times to repeat the child sequence.
    children
        Child nodes run in order for each repetition. If omitted, a single
        `Succeeder` is used so the wrapper still produces a valid repeater.
    """
    sequence = Sequence(
        name=f'{name}Cycle',
        children=children,
    )
    return BehaviorTree(
        BehaviorTree.RepeaterNode(
            name=name,
            repeat_count=repeat_count,
            child=Node(sequence),
        )
    )

def Subtree(name: str, subtree_fn: Callable[[BehaviorTree.Node], BehaviorTree]) -> BehaviorTree:
    """
    Build a subtree wrapper that resolves its child at runtime.

    Parameters
    ----------
    name
        Name assigned to the subtree node.
    subtree_fn
        Function that takes the subtree node as an argument and returns the
        child tree or node to run.

    Returns
    -------
    BehaviorTree
        A subtree that runs the tree or node returned by `subtree_fn`.
    """
    return BehaviorTree(
        BehaviorTree.SubtreeNode(
            name=name,
            subtree_fn=subtree_fn,
        )
    )


def Succeeder(name: str = "Succeeder") -> BehaviorTree:
    return BehaviorTree(
        BehaviorTree.SucceederNode(name=name)
    )
    
def Failer(name: str = "Failer") -> BehaviorTree:
    return BehaviorTree(
        BehaviorTree.FailerNode(name=name)
    )


def ActivateWidget(widget_name: str, name: str | None = None) -> BehaviorTree:
    return BottingTree.ActivateWidgetTree(widget_name, name=name)


def DeactivateWidget(widget_name: str, name: str | None = None) -> BehaviorTree:
    return BottingTree.DeactivateWidgetTree(widget_name, name=name)


def SetWidgetActive(widget_name: str, enabled: bool, name: str | None = None) -> BehaviorTree:
    return BottingTree.GetWidgetSetEnabledTree(widget_name, enabled, name=name)


def EnableAutoInventoryHandler(name: str | None = None) -> BehaviorTree:
    return BottingTree.EnableAutoInventoryHandlerTree() if name is None else BottingTree.GetAutoInventoryHandlerSetEnabledTree(True, name=name)


def DisableAutoInventoryHandler(name: str | None = None) -> BehaviorTree:
    return BottingTree.DisableAutoInventoryHandlerTree() if name is None else BottingTree.GetAutoInventoryHandlerSetEnabledTree(False, name=name)


def SetAutoInventoryHandlerActive(enabled: bool, name: str | None = None) -> BehaviorTree:
    return BottingTree.GetAutoInventoryHandlerSetEnabledTree(enabled, name=name)

def GetNodeByProfession(
    WarriorNode: BehaviorTree | BehaviorTree.Node | None = None,
    RangerNode: BehaviorTree | BehaviorTree.Node | None = None,
    MonkNode: BehaviorTree | BehaviorTree.Node | None = None,
    NecromancerNode: BehaviorTree | BehaviorTree.Node | None = None,
    MesmerNode: BehaviorTree | BehaviorTree.Node | None = None,
    ElementalistNode: BehaviorTree | BehaviorTree.Node | None = None,
    AssassinNode: BehaviorTree | BehaviorTree.Node | None = None,
    RitualistNode: BehaviorTree | BehaviorTree.Node | None = None,
    ParagonNode: BehaviorTree | BehaviorTree.Node | None = None,
    DervishNode: BehaviorTree | BehaviorTree.Node | None = None,
) -> BehaviorTree:
    """
    Select a profession-specific node at runtime from the blackboard.

    This helper reads `player_primary_profession_name` from the blackboard and
    returns the node mapped to that profession.

    Parameters
    ----------
    WarriorNode, RangerNode, MonkNode, NecromancerNode, MesmerNode,
    ElementalistNode, AssassinNode, RitualistNode, ParagonNode, DervishNode
        Optional node or tree to use for each primary profession.

    Returns
    -------
    BehaviorTree
        A wrapper sequence that resolves the matching node at tick time.

    Notes
    -----
    If the current profession has no supplied node, the helper returns a
    `Failer`.
    """
    def _profession_specific_node(node: BehaviorTree.Node) -> BehaviorTree:
        primary_profession = str(node.blackboard.get("player_primary_profession_name", "Warrior") or "Warrior")
        profession_nodes: dict[str, BehaviorTree | BehaviorTree.Node | None] = {
            "Warrior": WarriorNode,
            "Ranger": RangerNode,
            "Monk": MonkNode,
            "Necromancer": NecromancerNode,
            "Mesmer": MesmerNode,
            "Elementalist": ElementalistNode,
            "Assassin": AssassinNode,
            "Ritualist": RitualistNode,
            "Paragon": ParagonNode,
            "Dervish": DervishNode,
        }
        selected_node = profession_nodes.get(primary_profession)

        if selected_node is None:
            return Failer(name=f"GetNodeByProfession<{primary_profession}>")

        return BehaviorTree(Node(selected_node))

    return Sequence(
            name="GetNodeByProfession",
            children=[
                Subtree(
                    name="GetNodeByProfessionSubtree",
                    subtree_fn=_profession_specific_node,
                ),
            ],
        )

def SkipNodeByProfession(profession_name: str, NodeToRun: BehaviorTree) -> BehaviorTree:
    return Subtree(
        name=f"Skip {profession_name} Profession Specific Quests",
        subtree_fn=lambda node: Sequence(
            name=f"{profession_name} Profession Skip Decision",
            children=[
                NodeToRun
                if node.blackboard.get("player_primary_profession_name") != profession_name
                else Succeeder(name=f"Skip{profession_name}ProfessionSpecificQuests")
            ],
        ),
    )
    
def ExecuteIfProfession(profession_name: str, NodeToRun: BehaviorTree) -> BehaviorTree:
    return Subtree(
        name=f"ExecuteIf {profession_name} Profession Specific Quests",
        subtree_fn=lambda node: Sequence(
            name=f"{profession_name} Profession Execution Decision",
            children=[
                NodeToRun
                if node.blackboard.get("player_primary_profession_name") == profession_name
                else Succeeder(name=f"SkipNon{profession_name}ProfessionSpecificQuests")
            ],
        ),
    )
    

def GetValuesByProfession(
    profession_values: Mapping[str, object],
    target_key: str = "profession_value",
    fallback_profession: str = "Warrior",
) -> BehaviorTree:
    """
    Resolve a profession-specific value and store it on the blackboard.

    This helper reads `player_primary_profession_name`, looks up the value in
    `profession_values`, and writes the resolved value to `target_key`.

    Parameters
    ----------
    profession_values
        Mapping of profession name to value. Values are stored as-is on the
        blackboard and can be any object needed by later subtree nodes.
    target_key
        Blackboard key that will receive the resolved value.
    fallback_profession
        Fallback profession name used when the current profession is missing
        from `profession_values`.

    Returns
    -------
    BehaviorTree
        A wrapper sequence that writes the resolved value to the blackboard.

    Notes
    -----
    The helper fails if neither the current profession nor
    `fallback_profession` exists in `profession_values`.
    """
    def _store_profession_value(node: BehaviorTree.Node) -> BehaviorTree.NodeState:
        primary_profession = str(node.blackboard.get("player_primary_profession_name", fallback_profession) or fallback_profession)
        selected_value = profession_values.get(primary_profession, profession_values.get(fallback_profession))

        if selected_value is None:
            return BehaviorTree.NodeState.FAILURE

        node.blackboard[target_key] = selected_value
        return BehaviorTree.NodeState.SUCCESS

    return Sequence(
            name="GetValuesByProfession",
            children=[
                BehaviorTree.ActionNode(
                    name="GetValuesByProfessionAction",
                    action_fn=_store_profession_value,
                ),
            ],
        )


def BuyMaterialsByProfession(
    profession_materials: Mapping[str, list[tuple[int, int]]],
    *,
    rare_trader: bool = False,
    fallback_profession: str = "Warrior",
    log: bool = False,
    aftercast_ms: int = 125,
) -> BehaviorTree:
    def _buy_for_profession(node: BehaviorTree.Node) -> BehaviorTree:
        materials = cast(list[tuple[int, int]], node.blackboard["profession_buy_materials"])
        return BuyMaterialsFromList(
            materials=materials,
            rare_trader=rare_trader,
            log=log,
            aftercast_ms=aftercast_ms,
        )

    return Sequence(
        name="BuyMaterialsByProfession",
        children=[
            GetValuesByProfession(
                profession_values=profession_materials,
                target_key="profession_buy_materials",
                fallback_profession=fallback_profession,
            ),
            Subtree(
                name="BuyMaterialsByProfessionSubtree",
                subtree_fn=_buy_for_profession,
            ),
        ],
    )


def CraftItemsByProfession(
    profession_craft_steps: Mapping[str, list[tuple[int, int, list[int], list[int]]]],
    *,
    fallback_profession: str = "Warrior",
    equip_items: bool = True,
    craft_aftercast_ms: int = 350,
    equip_aftercast_ms: int = 250,
    equip_log: bool = False,
) -> BehaviorTree:
    def _craft_for_profession(node: BehaviorTree.Node) -> BehaviorTree:
        craft_steps = cast(list[tuple[int, int, list[int], list[int]]], node.blackboard["profession_craft_steps"])
        children: list[BehaviorTree | BehaviorTree.Node] = []

        for item_id, cost, trade_model_ids, quantity_list in craft_steps:
            children.append(
                CraftItem(
                    output_model_id=item_id,
                    cost=cost,
                    trade_model_ids=trade_model_ids,
                    quantity_list=quantity_list,
                    aftercast_ms=craft_aftercast_ms,
                )
            )
            if equip_items:
                children.append(
                    EquipItemByModelID(
                        item_id,
                        aftercast_ms=equip_aftercast_ms,
                        log=equip_log,
                    )
                )

        return Sequence(
            name="CraftItemsByProfessionSequence",
            children=children,
        )

    return Sequence(
        name="CraftItemsByProfession",
        children=[
            GetValuesByProfession(
                profession_values=profession_craft_steps,
                target_key="profession_craft_steps",
                fallback_profession=fallback_profession,
            ),
            Subtree(
                name="CraftItemsByProfessionSubtree",
                subtree_fn=_craft_for_profession,
            ),
        ],
    )
#region LOGGING

def LogMessage(message: str, 
               module_name: str = "ApobottingLib", 
               print_to_console: bool = True, 
               print_to_blackboard: bool = True) -> BehaviorTree:
    return RoutinesBT.Player.LogMessage(
        source=module_name,
        to_console=print_to_console,
        to_blackboard=print_to_blackboard,
        message=message,
    )
    
#region dialogs
def TargetNearest(x: float, y: float, target_distance: float = Range.Nearby.value, log: bool = False) -> BehaviorTree:
    return RoutinesBT.Agents.TargetNearestNPCXY(x=x,y=y,distance=target_distance,log=log)

def TargetNearestGadget(x: float, y: float, target_distance: float = Range.Nearby.value, log: bool = False) -> BehaviorTree:
    return RoutinesBT.Agents.TargetNearestGadgetXY(x=x,y=y,distance=target_distance,log=log)

def TargetAgentByModelID(modelID_or_encStr: int | str, log: bool = False) -> BehaviorTree:
    return RoutinesBT.Agents.TargetAgentByModelID(modelID_or_encStr=modelID_or_encStr, log=log)

def InteractTarget(log: bool = False) -> BehaviorTree:
    return _pause_heroai_for_action(RoutinesBT.Player.InteractTarget(log=log))

def AutoDialog(buttons: int | list[int] = 0, log: bool = False, aftercast_ms: int = 200, multi_account: bool = False) -> BehaviorTree:
    if isinstance(buttons, int):
        buttons = [buttons]
    else:
        buttons = list(buttons)

    if multi_account:
        return _pause_heroai_for_action(
            RoutinesBT.Composite.Sequence(
                *[
                    RoutinesBT.Composite.Sequence(
                        RoutinesBT.Player.SendAutomaticDialog(
                            button_number=int(button),
                            log=log,
                            aftercast_ms=aftercast_ms,
                        ),
                        _send_multibox_auto_dialog(
                            button_number=int(button),
                            log=log,
                            aftercast_ms=aftercast_ms,
                        ),
                        name=f"AutoDialogMultiboxStep_{int(button)}",
                    )
                    for button in buttons
                ],
                name="AutoDialogSequence",
            )
        )

    if len(buttons) == 1:
        return _pause_heroai_for_action(
            RoutinesBT.Player.SendAutomaticDialog(
                button_number=buttons[0],
                log=log,
                aftercast_ms=aftercast_ms,
            )
        )

    return _pause_heroai_for_action(
        RoutinesBT.Composite.Sequence(
            *[
                RoutinesBT.Player.SendAutomaticDialog(
                    button_number=int(button),
                    log=log,
                    aftercast_ms=aftercast_ms,
                )
                for button in buttons
            ],
            name="AutoDialogSequence",
        )
    )


def InteractTargetAndAutoDialog(
    buttons: int | list[int] = 0,
    log: bool = False,
    aftercast_ms: int = 250,
    multi_account: bool = False,
) -> BehaviorTree:
    if isinstance(buttons, int):
        buttons = [buttons]
    else:
        buttons = list(buttons)

    if multi_account:
        steps: list[BehaviorTree | BehaviorTree.Node] = [
            RoutinesBT.Player.InteractTarget(log=log),
            _capture_current_target(),
        ]
        for idx, button in enumerate(buttons):
            local_step = RoutinesBT.Player.SendAutomaticDialog(
                button_number=int(button),
                log=log,
                aftercast_ms=aftercast_ms,
            )
            remote_step = (
                _send_multibox_take_dialog_with_target(
                    button_number=int(button),
                    log=log,
                    aftercast_ms=aftercast_ms,
                )
                if idx == 0
                else _send_multibox_auto_dialog(
                    button_number=int(button),
                    log=log,
                    aftercast_ms=aftercast_ms,
                )
            )
            steps.append(
                RoutinesBT.Composite.Sequence(
                    local_step,
                    remote_step,
                    name=f"InteractTargetAndAutoDialogStep_{idx}",
                )
            )
        return _pause_heroai_for_action(
            RoutinesBT.Composite.Sequence(
                *steps,
                name="InteractTargetAndAutoDialogSequence",
            )
        )

    return _pause_heroai_for_action(
        RoutinesBT.Composite.Sequence(
            RoutinesBT.Player.InteractTarget(log=log),
            *[
                RoutinesBT.Player.SendAutomaticDialog(
                    button_number=int(button),
                    log=log,
                    aftercast_ms=aftercast_ms,
                )
                for button in buttons
            ],
            name="InteractTargetAndAutoDialogSequence",
        )
    )


def InteractTargetAndSendDialog(dialog_id: int | str, log: bool = False, multi_account: bool = False) -> BehaviorTree:
    if multi_account:
        return _pause_heroai_for_action(
            RoutinesBT.Composite.Sequence(
                RoutinesBT.Player.InteractTarget(log=log),
                _capture_current_target(),
                RoutinesBT.Player.SendDialog(dialog_id=dialog_id, log=log),
                _send_multibox_dialog_to_target(dialog_id=dialog_id, log=log),
                name="InteractTargetAndSendDialogSequence",
            )
        )

    return _pause_heroai_for_action(
        RoutinesBT.Composite.Sequence(
            RoutinesBT.Player.InteractTarget(log=log),
            RoutinesBT.Player.SendDialog(dialog_id=dialog_id, log=log),
            name="InteractTargetAndSendDialogSequence",
        )
    )


def TargetNearestAndInteract(
    pos: PointOrPath,
    target_distance: float = Range.Nearby.value,
    log: bool = False,
) -> BehaviorTree:
    point = _final_point(pos)
    return _pause_heroai_for_action(
        RoutinesBT.Composite.Sequence(
            RoutinesBT.Agents.TargetNearestNPCXY(x=point.x, y=point.y, distance=target_distance, log=log),
            RoutinesBT.Player.InteractTarget(log=log),
            name="TargetNearestAndInteractSequence",
        )
    )


def TargetNearestAndAutoDialog(
    pos: PointOrPath,
    buttons: int | list[int] = 0,
    target_distance: float = Range.Nearby.value,
    log: bool = False,
    aftercast_ms: int = 250,
    multi_account: bool = False,
) -> BehaviorTree:
    point = _final_point(pos)
    if isinstance(buttons, int):
        buttons = [buttons]
    else:
        buttons = list(buttons)

    if multi_account:
        steps: list[BehaviorTree | BehaviorTree.Node] = [
            RoutinesBT.Agents.TargetNearestNPCXY(x=point.x, y=point.y, distance=target_distance, log=log),
            RoutinesBT.Player.InteractTarget(log=log),
            _capture_current_target(),
        ]
        for idx, button in enumerate(buttons):
            local_step = RoutinesBT.Player.SendAutomaticDialog(
                button_number=int(button),
                log=log,
                aftercast_ms=aftercast_ms,
            )
            remote_step = (
                _send_multibox_take_dialog_with_target(
                    button_number=int(button),
                    log=log,
                    aftercast_ms=aftercast_ms,
                )
                if idx == 0
                else _send_multibox_auto_dialog(
                    button_number=int(button),
                    log=log,
                    aftercast_ms=aftercast_ms,
                )
            )
            steps.append(
                RoutinesBT.Composite.Sequence(
                    local_step,
                    remote_step,
                    name=f"TargetNearestAndAutoDialogStep_{idx}",
                )
            )
        return _pause_heroai_for_action(
            RoutinesBT.Composite.Sequence(
                *steps,
                name="TargetNearestAndAutoDialogSequence",
            )
        )

    return _pause_heroai_for_action(
        RoutinesBT.Composite.Sequence(
            RoutinesBT.Agents.TargetNearestNPCXY(x=point.x, y=point.y, distance=target_distance, log=log),
            RoutinesBT.Player.InteractTarget(log=log),
            *[
                RoutinesBT.Player.SendAutomaticDialog(
                    button_number=int(button),
                    log=log,
                    aftercast_ms=aftercast_ms,
                )
                for button in buttons
            ],
            name="TargetNearestAndAutoDialogSequence",
        )
    )


def TargetNearestAndSendDialog(
    pos: PointOrPath,
    dialog_id: int | str,
    target_distance: float = Range.Nearby.value,
    log: bool = False,
    multi_account: bool = False,
) -> BehaviorTree:
    point = _final_point(pos)
    if multi_account:
        return _pause_heroai_for_action(
            RoutinesBT.Composite.Sequence(
                RoutinesBT.Agents.TargetNearestNPCXY(x=point.x, y=point.y, distance=target_distance, log=log),
                RoutinesBT.Player.InteractTarget(log=log),
                _capture_current_target(),
                RoutinesBT.Player.SendDialog(dialog_id=dialog_id, log=log),
                _send_multibox_dialog_to_target(dialog_id=dialog_id, log=log),
                name="TargetNearestAndSendDialogSequence",
            )
        )

    return _pause_heroai_for_action(
        RoutinesBT.Composite.Sequence(
            RoutinesBT.Agents.TargetNearestNPCXY(x=point.x, y=point.y, distance=target_distance, log=log),
            RoutinesBT.Player.InteractTarget(log=log),
            RoutinesBT.Player.SendDialog(dialog_id=dialog_id, log=log),
            name="TargetNearestAndSendDialogSequence",
        )
    )


def TargetNearestGadgetAndInteract(
    pos: PointOrPath,
    target_distance: float = Range.Nearby.value,
    log: bool = False,
) -> BehaviorTree:
    point = _final_point(pos)
    return _pause_heroai_for_action(
        RoutinesBT.Composite.Sequence(
            RoutinesBT.Agents.TargetNearestGadgetXY(x=point.x, y=point.y, distance=target_distance, log=log),
            RoutinesBT.Player.InteractTarget(log=log),
            name="TargetNearestGadgetAndInteractSequence",
        )
    )


def TargetAgentByModelIDAndInteract(modelID_or_encStr: int | str, log: bool = False) -> BehaviorTree:
    return _pause_heroai_for_action(
        RoutinesBT.Composite.Sequence(
            RoutinesBT.Agents.TargetAgentByModelID(modelID_or_encStr=modelID_or_encStr, log=log),
            RoutinesBT.Player.InteractTarget(log=log),
            name="TargetAgentByModelIDAndInteractSequence",
        )
    )


def TargetAgentByModelIDAndAutoDialog(
    modelID_or_encStr: int | str,
    buttons: int | list[int] = 0,
    log: bool = False,
    aftercast_ms: int = 250,
    multi_account: bool = False,
) -> BehaviorTree:
    if isinstance(buttons, int):
        buttons = [buttons]
    else:
        buttons = list(buttons)

    if multi_account:
        steps: list[BehaviorTree | BehaviorTree.Node] = [
            RoutinesBT.Agents.TargetAgentByModelID(modelID_or_encStr=modelID_or_encStr, log=log),
            RoutinesBT.Player.InteractTarget(log=log),
            _capture_current_target(),
        ]
        for idx, button in enumerate(buttons):
            local_step = RoutinesBT.Player.SendAutomaticDialog(
                button_number=int(button),
                log=log,
                aftercast_ms=aftercast_ms,
            )
            remote_step = (
                _send_multibox_take_dialog_with_target(
                    button_number=int(button),
                    log=log,
                    aftercast_ms=aftercast_ms,
                )
                if idx == 0
                else _send_multibox_auto_dialog(
                    button_number=int(button),
                    log=log,
                    aftercast_ms=aftercast_ms,
                )
            )
            steps.append(
                RoutinesBT.Composite.Sequence(
                    local_step,
                    remote_step,
                    name=f"TargetAgentByModelIDAndAutoDialogStep_{idx}",
                )
            )
        return _pause_heroai_for_action(
            RoutinesBT.Composite.Sequence(
                *steps,
                name="TargetAgentByModelIDAndAutoDialogSequence",
            )
        )

    return _pause_heroai_for_action(
        RoutinesBT.Composite.Sequence(
            RoutinesBT.Agents.TargetAgentByModelID(modelID_or_encStr=modelID_or_encStr, log=log),
            RoutinesBT.Player.InteractTarget(log=log),
            *[
                RoutinesBT.Player.SendAutomaticDialog(
                    button_number=int(button),
                    log=log,
                    aftercast_ms=aftercast_ms,
                )
                for button in buttons
            ],
            name="TargetAgentByModelIDAndAutoDialogSequence",
        )
    )


def TargetAgentByModelIDAndSendDialog(
    modelID_or_encStr: int | str,
    dialog_id: int | str,
    log: bool = False,
    multi_account: bool = False,
) -> BehaviorTree:
    if multi_account:
        return _pause_heroai_for_action(
            RoutinesBT.Composite.Sequence(
                RoutinesBT.Agents.TargetAgentByModelID(modelID_or_encStr=modelID_or_encStr, log=log),
                RoutinesBT.Player.InteractTarget(log=log),
                _capture_current_target(),
                RoutinesBT.Player.SendDialog(dialog_id=dialog_id, log=log),
                _send_multibox_dialog_to_target(dialog_id=dialog_id, log=log),
                name="TargetAgentByModelIDAndSendDialogSequence",
            )
        )

    return _pause_heroai_for_action(
        RoutinesBT.Composite.Sequence(
            RoutinesBT.Agents.TargetAgentByModelID(modelID_or_encStr=modelID_or_encStr, log=log),
            RoutinesBT.Player.InteractTarget(log=log),
            RoutinesBT.Player.SendDialog(dialog_id=dialog_id, log=log),
            name="TargetAgentByModelIDAndSendDialogSequence",
        )
    )

def SendDialog(dialog_id: int | str, log: bool = False, multi_account: bool = False) -> BehaviorTree:
    if multi_account:
        return _pause_heroai_for_action(
            RoutinesBT.Composite.Sequence(
                RoutinesBT.Player.SendDialog(dialog_id=dialog_id, log=log),
                _send_multibox_manual_dialog(dialog_id=dialog_id, log=log),
                name="SendDialogMultibox",
            )
        )
    return _pause_heroai_for_action(RoutinesBT.Player.SendDialog(dialog_id=dialog_id, log=log))

def DialogAtXY(
    pos: PointOrPath,
    dialog_id: int | str,
    target_distance: float = 200.0,
    log: bool = False,
    multi_account: bool = False,
) -> BehaviorTree:
    return TargetNearestAndSendDialog(
        pos=pos,
        dialog_id=dialog_id,
        target_distance=target_distance,
        log=log,
        multi_account=multi_account,
    )
    
def InteractWithGadgetAtXY(pos: PointOrPath, target_distance: float = 200.0) -> BehaviorTree:
    return TargetNearestGadgetAndInteract(pos=pos, target_distance=target_distance, log=False)
    
def TargetAndDialogByModelID(
    modelID_or_encStr: int | str,
    dialog_id: int | str,
    log: bool = False,
    multi_account: bool = False,
) -> BehaviorTree:
    return TargetAgentByModelIDAndSendDialog(
        modelID_or_encStr=modelID_or_encStr,
        dialog_id=dialog_id,
        log=log,
        multi_account=multi_account,
    )


#region faction
def StoreFactionData(
    luxon_key: str = 'current_luxon_faction',
    kurzick_key: str = 'current_kurzick_faction',
    log: bool = False,
) -> BehaviorTree:
    from Py4GWCoreLib.Player import Player

    def _store(node: BehaviorTree.Node) -> BehaviorTree.NodeState:
        current_luxon = int(Player.GetLuxonData()[0] or 0)
        current_kurzick = int(Player.GetKurzickData()[0] or 0)
        node.blackboard[luxon_key] = current_luxon
        node.blackboard[kurzick_key] = current_kurzick
        return BehaviorTree.NodeState.SUCCESS

    return BehaviorTree(
        BehaviorTree.ActionNode(
            name='StoreFactionData',
            action_fn=_store,
        )
    )


def TakeBlessing(
    pos: PointOrPath,
    faction: str | None = None,
    buttons: int | SequenceABC[int] = 0,
    blessing_dialog_id: int | str = 0x86,
    bribe_dialog_id: int | str = 0x84,
    multi_account: bool = False,
    log: bool = False,
    pre_dialog_wait_ms: int = 125,
    post_dialog_wait_ms: int = 125,
) -> BehaviorTree:
    faction_name = str(faction or '').strip().lower()
    if faction_name and faction_name not in {'luxon', 'kurzick'}:
        raise ValueError("faction must be 'luxon', 'kurzick', or empty.")

    if faction_name:
        bribe_key = f'{faction_name}_blessing_bribe_priest'

        def _set_bribe_flag(node: BehaviorTree.Node) -> BehaviorTree.NodeState:
            current_luxon = int(node.blackboard.get('current_luxon_faction', 0) or 0)
            current_kurzick = int(node.blackboard.get('current_kurzick_faction', 0) or 0)
            node.blackboard[bribe_key] = (
                current_kurzick >= current_luxon if faction_name == 'luxon' else current_luxon >= current_kurzick
            )
            return BehaviorTree.NodeState.SUCCESS

        def _maybe_bribe(node: BehaviorTree.Node) -> BehaviorTree:
            if bool(node.blackboard.get(bribe_key, False)):
                return InteractTargetAndSendDialog(
                    dialog_id=bribe_dialog_id,
                    log=log,
                    multi_account=multi_account,
                )
            return Succeeder(name=f'Skip{faction_name.title()}BlessingBribe')

        return Sequence(
            name=f'Take {faction_name.title()} Blessing',
            children=[
                StoreFactionData(log=log),
                BehaviorTree(
                    BehaviorTree.ActionNode(
                        name=f'Set{faction_name.title()}BlessingBribeFlag',
                        action_fn=_set_bribe_flag,
                    )
                ),
                MoveAndInteract(pos=pos, log=log),
                LogMessage(message=f"Obtaining {faction_name.title()} blessing"),
                Wait(pre_dialog_wait_ms, log=log),
                Subtree(name=f'MaybeBribe{faction_name.title()}Priest', subtree_fn=_maybe_bribe),
                InteractTargetAndSendDialog(
                    dialog_id=blessing_dialog_id,
                    log=log,
                    multi_account=multi_account,
                ),
                Wait(post_dialog_wait_ms, log=log),
            ],
        )

    return Sequence(
        name='Take Blessing',
        children=[
            MoveAndInteract(pos=pos, log=log),
            LogMessage(message='Obtaining blessing'),
            Wait(pre_dialog_wait_ms, log=log),
            *(
                [
                    _capture_current_target(),
                    RoutinesBT.Composite.Sequence(
                        *[
                            RoutinesBT.Player.SendAutomaticDialog(
                                button_number=int(button),
                                log=log,
                            )
                            for button in ([buttons] if isinstance(buttons, int) else list(buttons))
                        ],
                        _send_multibox_get_blessing_with_target(
                            buttons=[buttons] if isinstance(buttons, int) else list(buttons),
                            log=log,
                        ),
                        name='TakeBlessingMultiboxSequence',
                    ),
                ]
                if multi_account
                else [
                    *[
                        RoutinesBT.Player.SendAutomaticDialog(
                            button_number=int(button),
                            log=log,
                        )
                        for button in ([buttons] if isinstance(buttons, int) else list(buttons))
                    ]
                ]
            ),
            Wait(post_dialog_wait_ms, log=log),
        ],
    )

def DonateFaction(
    faction: str = 'luxon',
    threshold: int = 10000,
    travel_map_id: int = 0,
    random_travel: bool = False,
    region_pool: str = 'eu',
    multi_account: bool = False,
    summon_accounts: bool = True,
    timeout_ms: int = 90000,
    poll_interval_ms: int = 100,
    log: bool = False,
) -> BehaviorTree:
    faction_name = str(faction or 'luxon').strip().lower()
    if faction_name not in {'luxon', 'kurzick'}:
        raise ValueError("faction must be 'luxon' or 'kurzick'.")
    donate_children: list[BehaviorTree | BehaviorTree.Node] = []
    if multi_account and summon_accounts:
        donate_children.append(
            RoutinesBT.Multibox.SummonAllAccounts(
                timeout_ms=15000,
                poll_interval_ms=poll_interval_ms,
                log=log,
            )
        )
        donate_children.append(Wait(duration_ms=1000, log=log))

    donate_children.append(
        RoutinesBT.Multibox.DonateFaction(
            faction=faction_name,
            threshold=threshold,
            refs_blackboard_key=f'{faction_name}_donation_message_refs',
            timeout_ms=timeout_ms,
            poll_interval_ms=poll_interval_ms,
            log=log,
        )
    )

    donate_sequence = Sequence(
        name=f'Donate{faction_name.title()}FactionSequence',
        map_id_or_name=int(travel_map_id) if travel_map_id else 0,
        random_travel=random_travel,
        region_pool=region_pool,
        children=donate_children,
    )

    if travel_map_id:
        return Sequence(
            name=f'Donate {faction_name.title()} Faction',
            children=[
                LeaveParty(),
                donate_sequence,
            ],
        )

    return donate_sequence

   

#region travel
def SetHardMode(hard_mode: bool = True, log: bool = False) -> BehaviorTree:
    return RoutinesBT.Map.SetHardMode(hard_mode=hard_mode, log=log)


def Travel(
    target_map_id: int = 0,
    target_map_name: str = "",
    random_travel: bool = False,
    region_pool: str = "eu",
    hard_mode: bool | None = None,
    log: bool = False,
) -> BehaviorTree:
    travel_tree = (
        RoutinesBT.Map.TravelToRandomDistrict(
            target_map_id=target_map_id,
            target_map_name=target_map_name,
            region_pool=region_pool,
            log=log,
        )
        if random_travel
        else RoutinesBT.Map.TravelToOutpost(
            outpost_id=target_map_id,
            outpost_name=target_map_name,
            log=log,
        )
    )

    if hard_mode is None:
        return travel_tree

    return RoutinesBT.Composite.Sequence(
        travel_tree,
        SetHardMode(hard_mode=hard_mode, log=log),
        name="TravelAndSetHardMode",
    )

def TravelGH() -> BehaviorTree:
    return RoutinesBT.Map.TravelGH()

def LeaveGH() -> BehaviorTree:
    return RoutinesBT.Map.LeaveGH()

def TravelToRegion(
    outpost_id: int,
    region: int,
    district: int,
    language: int = 0,
    log: bool = False,
    timeout_ms: int = 10000,
) -> BehaviorTree:
    return RoutinesBT.Map.TravelToRegion(
        outpost_id=outpost_id,
        region=region,
        district=district,
        language=language,
        log=log,
        timeout=timeout_ms,
    )

def EnterChallenge(
    delay_ms: int = 3000,
    target_map_id: int = 0,
    target_map_name: str = "",
    confirm_extra: bool = False,
) -> BehaviorTree:
    return RoutinesBT.Map.EnterChallenge(
        target_map_id=target_map_id,
        target_map_name=target_map_name,
        delay_ms=delay_ms,
        confirm_extra=confirm_extra,
    )

#region Waits
def Wait(duration_ms: int, log: bool = False, emote: bool | str = False, announce_delay: bool = False) -> BehaviorTree:
    
    emote_str = str(emote) if isinstance(emote, str) else None
    wait_tree = _wait_special(emote=emote_str, duration_ms=duration_ms, log=log) if emote else RoutinesBT.Player.Wait(duration_ms=duration_ms, log=log)
    if not announce_delay:
        return wait_tree

    wait_seconds = max(0.0, float(duration_ms) / 1000.0)
    return RoutinesBT.Composite.Sequence(
        LogMessage(
            message=f"Waiting for {wait_seconds:.1f}s",
            module_name="ApobottingLib",
            print_to_console=True,
            print_to_blackboard=True,
        ),
        wait_tree,
        name="WaitAnnounced",
    )

def WaitUntilOnExplorable(timeout_ms: int = 15000) -> BehaviorTree:
    return RoutinesBT.Map.WaitUntilOnExplorable(timeout_ms=timeout_ms,)

def WaitUntilOnOutpost(timeout_ms: int = 15000) -> BehaviorTree:
    return RoutinesBT.Map.WaitUntilOnOutpost(timeout_ms=timeout_ms,)


def WaitUntilOutOfCombat(range: float = Range.Earshot.value, timeout_ms: int = 60000) -> BehaviorTree:
    return RoutinesBT.Agents.WaitUntilOutOfCombat(range=range,timeout_ms=timeout_ms)

def WaitUntilOnCombat(range: float = Range.Earshot.value, timeout_ms: int = 60000) -> BehaviorTree:
    return RoutinesBT.Agents.WaitUntilOnCombat(range=range,timeout_ms=timeout_ms,)
    
def WaitForMapLoad(map_id: int = 0, timeout_ms: int = 30000, map_name: str = "") -> BehaviorTree:
    return RoutinesBT.Map.WaitforMapLoad(map_id=map_id, timeout=timeout_ms, map_name=map_name,
                                         player_instance_uptime_ms=500,
                                         throttle_interval_ms=250,
                                         post_arrival_wait_ms=0,
                                         log=bool(map_id or map_name),
    )

def WaitForMapToChange(map_id: int, timeout_ms: int = 30000, map_name: str = "") -> BehaviorTree:
    return WaitForMapLoad(map_id=map_id, timeout_ms=timeout_ms, map_name=map_name)

def WaitUntilCharacterSelect(timeout_ms: int = 45000) -> BehaviorTree:
    return RoutinesBT.Player.WaitUntilCharacterSelect(timeout_ms=timeout_ms,)

#region Movement
def Move(pos: PointOrPath,pause_on_combat: bool | None = None,tolerance: float = 200.0,flag_heroes_to_waypoint: bool = False,log: bool = False,) -> BehaviorTree:
    return _movement_with_runtime_pause(
        "Move",
        lambda resolved_pause: RoutinesBT.Movement.MovePath(
            pos=pos,
            pause_on_combat=resolved_pause,
            tolerance=tolerance,
            flag_heroes_to_waypoint=flag_heroes_to_waypoint,
            log=log,
        ),
        pause_on_combat=pause_on_combat,
    )

def MoveDirect(
    pos: PointOrPath,
    pause_on_combat: bool | None = None,
    flag_heroes_to_waypoint: bool = False,
    log: bool = False,
    timeout_ms: int = 15000,
    tolerance: float = 50.0,
) -> BehaviorTree:
    return _movement_with_runtime_pause(
        "MoveDirect",
        lambda resolved_pause: RoutinesBT.Movement.MoveDirect(
            PointPath.as_path(pos),
            pause_on_combat=resolved_pause,
            flag_heroes_to_waypoint=flag_heroes_to_waypoint,
            log=log,
            timeout_ms=timeout_ms,
            tolerance=tolerance,
        ),
        pause_on_combat=pause_on_combat,
    )

def MoveAndExitMap(pos: PointOrPath, target_map_id: int = 0, target_map_name: str = "", flag_heroes_to_waypoint: bool = False, log: bool = False) -> BehaviorTree:
    return RoutinesBT.Composite.Sequence(
            LogMessage("Exiting map..."),
            Move(pos=pos, tolerance=150.0, flag_heroes_to_waypoint=flag_heroes_to_waypoint, log=log),
            WaitForMapLoad(map_id=target_map_id, map_name=target_map_name),
    )

def MoveAndKill(
    pos: PointOrPath,
    clear_area_radius: float = Range.Spirit.value,
    pause_on_combat: bool | None = None,
    flag_heroes_to_waypoint: bool = False,
    timeout_ms: int = 15000,
) -> BehaviorTree:
    return _movement_with_runtime_pause(
        "MoveAndKill",
        lambda resolved_pause: RoutinesBT.Movement.MoveAndKillPath(
            pos=pos,
            clear_area_radius=clear_area_radius,
            pause_on_combat=resolved_pause,
            flag_heroes_to_waypoint=flag_heroes_to_waypoint,
            timeout_ms=timeout_ms,
        ),
        pause_on_combat=pause_on_combat,
    )


def VanquishNode(
    steps: SequenceABC[object],
    clear_area_radius: float = Range.Spirit.value,
    pause_on_combat: bool | None = None,
    flag_heroes_to_waypoint: bool = False,
    name: str = 'VanquishNode',
    timeout_ms: int = 15000,
) -> BehaviorTree:
    resolved_children: list[BehaviorTree | BehaviorTree.Node] = []

    for step in steps:
        resolved_pos, step_clear_area_radius, step_pause_on_combat, step_flag_heroes_to_waypoint = _coerce_vanquish_step(
            step=step,
            clear_area_radius=clear_area_radius,
            pause_on_combat=pause_on_combat,
            flag_heroes_to_waypoint=flag_heroes_to_waypoint,
        )

        resolved_children.append(
            MoveAndKill(
                pos=resolved_pos,
                clear_area_radius=step_clear_area_radius,
                pause_on_combat=step_pause_on_combat,
                flag_heroes_to_waypoint=step_flag_heroes_to_waypoint,
                timeout_ms=timeout_ms,
            )
        )

    if not resolved_children:
        return Succeeder(name=f'{name}Empty')

    return Sequence(
        name=name,
        children=resolved_children,
    )

def MoveAndTarget(
    pos: PointOrPath,
    target_distance: float = Range.Adjacent.value,
    move_tolerance: float = 150.0,
    pause_on_combat: bool | None = None,
    flag_heroes_to_waypoint: bool = False,
    log: bool = False,
) -> BehaviorTree:
    return _movement_with_runtime_pause(
        "MoveAndTarget",
        lambda resolved_pause: RoutinesBT.Movement.MoveAndTargetPath(
            pos=pos,
            target_distance=target_distance,
            move_tolerance=move_tolerance,
            pause_on_combat=resolved_pause,
            flag_heroes_to_waypoint=flag_heroes_to_waypoint,
            log=log,
        ),
        pause_on_combat=pause_on_combat,
    )

def MoveAndInteract(
    pos: PointOrPath,
    target_distance: float = Range.Area.value,
    move_tolerance: float = 150.0,
    pause_on_combat: bool | None = None,
    flag_heroes_to_waypoint: bool = False,
    log: bool = False,
) -> BehaviorTree:
    return RoutinesBT.Composite.Sequence(
        Move(pos=pos, tolerance=move_tolerance, pause_on_combat=pause_on_combat, flag_heroes_to_waypoint=flag_heroes_to_waypoint, log=log),
        _wait_until_player_stops_moving(log=log),
        Wait(_POST_MOVEMENT_SETTLE_MS, log=log),
        TargetNearestAndInteract(pos=pos, target_distance=target_distance, log=log),
        name="MoveAndInteract",
    )

def MoveAndInteractWithGadget(
    pos: PointOrPath,
    target_distance: float = Range.Area.value,
    move_tolerance: float = 150.0,
    pause_on_combat: bool | None = None,
    flag_heroes_to_waypoint: bool = False,
    log: bool = False,
) -> BehaviorTree:
    return _movement_with_runtime_pause(
        "MoveAndInteractWithGadget",
        lambda resolved_pause: RoutinesBT.Composite.Sequence(
            RoutinesBT.Movement.MovePath(
                pos=pos,
                pause_on_combat=resolved_pause,
                tolerance=move_tolerance,
                flag_heroes_to_waypoint=flag_heroes_to_waypoint,
                log=log,
            ),
            _wait_until_player_stops_moving(log=log),
            Wait(_POST_MOVEMENT_SETTLE_MS, log=log),
            TargetNearestGadgetAndInteract(pos=pos, target_distance=target_distance, log=log),
            name="MoveAndInteractWithGadget",
        ),
        pause_on_combat=pause_on_combat,
    )
        
def MoveAndAutoDialog(
    pos: PointOrPath,
    buttons: int | list[int] = 0,
    target_distance: float = Range.Nearby.value,
    move_tolerance: float = 150.0,
    pause_on_combat: bool | None = None,
    flag_heroes_to_waypoint: bool = False,
    log: bool = False,
    multi_account: bool = False,
) -> BehaviorTree:
    return RoutinesBT.Composite.Sequence(
        Move(pos=pos, tolerance=move_tolerance, pause_on_combat=pause_on_combat, flag_heroes_to_waypoint=flag_heroes_to_waypoint, log=log),
        _wait_until_player_stops_moving(log=log),
        Wait(_POST_MOVEMENT_SETTLE_MS, log=log),
        TargetNearestAndAutoDialog(pos=pos, buttons=buttons, target_distance=target_distance, log=log, multi_account=multi_account),
        name="MoveAndAutoDialog",
    )

def MoveAndDialog(
    pos: PointOrPath,
    dialog_id: int | str,
    target_distance: float = Range.Nearby.value,
    move_tolerance: float = 150.0,
    pause_on_combat: bool | None = None,
    flag_heroes_to_waypoint: bool = False,
    log: bool = False,
    multi_account: bool = False,
) -> BehaviorTree:
    return RoutinesBT.Composite.Sequence(
        Move(pos=pos, tolerance=move_tolerance, pause_on_combat=pause_on_combat, flag_heroes_to_waypoint=flag_heroes_to_waypoint, log=log),
        _wait_until_player_stops_moving(log=log),
        Wait(_POST_MOVEMENT_SETTLE_MS, log=log),
        TargetNearestAndSendDialog(pos=pos, dialog_id=dialog_id, target_distance=target_distance, log=log, multi_account=multi_account),
        name="MoveAndDialog",
    )
    
def MoveAndTargetByModelID(
    modelID_or_encStr: int | str,
    pause_on_combat: bool | None = None,
    flag_heroes_to_waypoint: bool = False,
    log: bool = False,
) -> BehaviorTree:
    return _movement_with_runtime_pause(
        "MoveAndTargetByModelID",
        lambda resolved_pause: RoutinesBT.Movement.MoveAndTargetByModelID(
            modelID_or_encStr=modelID_or_encStr,
            pause_on_combat=resolved_pause,
            flag_heroes_to_waypoint=flag_heroes_to_waypoint,
            log=log,
        ),
        pause_on_combat=pause_on_combat,
    )


def MoveToModelID(
    modelID_or_encStr: int | str,
    pause_on_combat: bool | None = None,
    flag_heroes_to_waypoint: bool = False,
    log: bool = False,
) -> BehaviorTree:
    return _movement_with_runtime_pause(
        "MoveToModelID",
        lambda resolved_pause: RoutinesBT.Movement._move_to_model_id(
            modelID_or_encStr=modelID_or_encStr,
            pause_on_combat=resolved_pause,
            flag_heroes_to_waypoint=flag_heroes_to_waypoint,
            log=log,
        ),
        pause_on_combat=pause_on_combat,
    )
    
def MoveAndAutoDialogByModelID(modelID_or_encStr: int | str, button_number: int = 0, flag_heroes_to_waypoint: bool = False, log: bool = False, multi_account: bool = False) -> BehaviorTree:
    return RoutinesBT.Composite.Sequence(
        MoveToModelID(modelID_or_encStr=modelID_or_encStr, flag_heroes_to_waypoint=flag_heroes_to_waypoint, log=log),
        _wait_until_player_stops_moving(log=log),
        Wait(_POST_MOVEMENT_SETTLE_MS, log=log),
        TargetAgentByModelIDAndAutoDialog(modelID_or_encStr=modelID_or_encStr, buttons=button_number, log=log, multi_account=multi_account),
        name="MoveAndAutoDialogByModelID",
    )

def MoveAndDialogByModelID(modelID_or_encStr: int | str, dialog_id: int | str, flag_heroes_to_waypoint: bool = False, log: bool = False, multi_account: bool = False) -> BehaviorTree:
    return RoutinesBT.Composite.Sequence(
        MoveToModelID(modelID_or_encStr=modelID_or_encStr, flag_heroes_to_waypoint=flag_heroes_to_waypoint, log=log),
        _wait_until_player_stops_moving(log=log),
        Wait(_POST_MOVEMENT_SETTLE_MS, log=log),
        TargetAgentByModelIDAndSendDialog(modelID_or_encStr=modelID_or_encStr, dialog_id=dialog_id, log=log, multi_account=multi_account),
        name="MoveAndDialogByModelID",
    )

def MoveAndInteractByModelID(modelID_or_encStr: int | str, target_distance: float = Range.Nearby.value, flag_heroes_to_waypoint: bool = False, log: bool = False) -> BehaviorTree:
    return RoutinesBT.Composite.Sequence(
        MoveToModelID(modelID_or_encStr=modelID_or_encStr, flag_heroes_to_waypoint=flag_heroes_to_waypoint, log=log),
        _wait_until_player_stops_moving(log=log),
        Wait(_POST_MOVEMENT_SETTLE_MS, log=log),
        TargetAgentByModelIDAndInteract(modelID_or_encStr=modelID_or_encStr, log=log),
        name="MoveAndInteractByModelID",
    )
    


def FollowModel(
    modelID_or_encStr: int | str,
    follow_range: float = Range.Area.value,
    timeout_ms: int = 30000,
    repath_interval_ms: int = 500,
    repath_distance: float = 200.0,
    exit_condition: Callable[[], bool] | None = None,
    exit_by_area: tuple[tuple[float, float], float] | None = None,
    log: bool = False,
) -> BehaviorTree:
    from Py4GWCoreLib.AgentArray import AgentArray
    from Py4GWCoreLib.Agent import Agent
    from Py4GWCoreLib.Player import Player
    from Py4GWCoreLib.Py4GWcorelib import Console
    from Py4GWCoreLib.Py4GWcorelib import ConsoleLog
    from Py4GWCoreLib.Py4GWcorelib import Utils
    from Py4GWCoreLib.routines_src.Checks import Checks

    state = {
        "started_ms": None,
        "approach_started_ms": None,
        "last_move_ms": 0,
        "last_target_xy": None,
        "last_status": "",
    }

    def _trace(message: str, message_type=Console.MessageType.Info, log: bool = False) -> None:
        ConsoleLog("FollowModel", message, message_type, log=log)

    def _resolve_agent_id() -> int:
        if isinstance(modelID_or_encStr, str):
            for aid in AgentArray.GetAgentArray():
                if Agent.GetEncNameStrByID(aid, literal=True) == modelID_or_encStr:
                    return int(aid)
            return 0

        model_id = int(modelID_or_encStr)
        for aid in AgentArray.GetAgentArray():
            if Agent.GetModelID(aid) == model_id:
                return int(aid)
        return 0

    def _follow(node: BehaviorTree.Node) -> BehaviorTree.NodeState:
        now = int(Utils.GetBaseTimestamp())
        if state["started_ms"] is None:
            state["started_ms"] = now
            _trace(
                f"Starting follow for model {modelID_or_encStr} with range={float(follow_range):.1f}, timeout_ms={int(timeout_ms)}.",
                log=log
            )

        if exit_condition is not None and exit_condition():
            if state["last_status"] != "exit":
                _trace("Exit condition satisfied.", log=log)
                state["last_status"] = "exit"
            return BehaviorTree.NodeState.SUCCESS

        if exit_by_area is not None:
            exit_point, exit_range = exit_by_area
            player_xy = Player.GetXY()
            exit_distance = float(Utils.Distance(player_xy, exit_point))
            if exit_distance <= float(exit_range):
                if state["last_status"] != "exit_area":
                    _trace(
                        f"Exit-by-area satisfied at distance {exit_distance:.1f} from {exit_point} within range {float(exit_range):.1f}.",
                        log=log,
                    )
                    state["last_status"] = "exit_area"
                return BehaviorTree.NodeState.SUCCESS

        if not Checks.Map.MapValid():
            if state["last_status"] != "invalid_map":
                _trace("Map became invalid while following target.", Console.MessageType.Warning, log=True)
                state["last_status"] = "invalid_map"
            return BehaviorTree.NodeState.FAILURE

        if Checks.Player.IsCasting():
            if state["last_status"] != "casting":
                _trace("Pausing follow while player is casting.", log=log)
                state["last_status"] = "casting"
            return BehaviorTree.NodeState.RUNNING

        if Checks.Player.IsDead():
            if state["last_status"] != "dead":
                _trace("Pausing follow while player is dead.", log=log)
                state["last_status"] = "dead"
            return BehaviorTree.NodeState.RUNNING

        agent_id = _resolve_agent_id()
        if agent_id == 0:
            if state["last_status"] != "waiting_agent":
                _trace(f"Waiting for model {modelID_or_encStr} to resolve via AgentArray.GetAgentArray().", log=log)
                state["last_status"] = "waiting_agent"
            return BehaviorTree.NodeState.RUNNING

        target_xy = Agent.GetXY(agent_id)
        player_xy = Player.GetXY()
        distance = float(Utils.Distance(player_xy, target_xy))
        node.blackboard["follow_model_last_agent_id"] = agent_id
        node.blackboard["follow_model_last_distance"] = distance
        node.blackboard["follow_model_last_xy"] = target_xy

        if distance <= float(follow_range):
            if state["approach_started_ms"] is not None:
                state["approach_started_ms"] = None
                state["last_target_xy"] = None
                state["last_move_ms"] = 0
            if state["last_status"] != "within_range":
                _trace(
                    f"Tracking agent {agent_id} at distance {distance:.1f}; within follow range, waiting for movement.",
                    log=log
                )
                state["last_status"] = "within_range"
            return BehaviorTree.NodeState.RUNNING

        if timeout_ms > 0 and state["approach_started_ms"] is not None and now - int(state["approach_started_ms"]) >= int(timeout_ms):
            if state["last_status"] != "timeout":
                _trace("Timed out during current approach step.", Console.MessageType.Warning, log=True)
                state["last_status"] = "timeout"
            return BehaviorTree.NodeState.FAILURE

        last_target_xy = state["last_target_xy"]
        target_moved = (
            last_target_xy is None
            or float(Utils.Distance(last_target_xy, target_xy)) >= float(repath_distance)
        )
        repath_due = now - int(state["last_move_ms"]) >= int(max(50, repath_interval_ms))

        if target_moved or repath_due:
            if state["approach_started_ms"] is None:
                state["approach_started_ms"] = now
                _trace(
                    f"Starting new approach to agent {agent_id} at distance {distance:.1f}.",
                    log=log,
                )
            Player.Move(float(target_xy[0]), float(target_xy[1]))
            state["last_move_ms"] = now
            state["last_target_xy"] = target_xy
            _trace(f"Chasing agent {agent_id} at {target_xy}; distance={distance:.1f}.", log=log)
            state["last_status"] = "chasing"

        return BehaviorTree.NodeState.RUNNING

    return BehaviorTree(
        BehaviorTree.ActionNode(
            name=f"FollowModel({modelID_or_encStr})",
            action_fn=_follow,
        )
    )
    
def MoveAndCraftItem(pos: PointOrPath, output_model_id: int,cost: int,trade_model_ids: list[int],quantity_list: list[int]) -> BehaviorTree:
    return RoutinesBT.Composite.Sequence(
        MoveAndInteract(pos=pos),
        _pause_heroai_for_action(
            RoutinesBT.Items.CraftItem(output_model_id=output_model_id,cost=cost,trade_model_ids=trade_model_ids,quantity_list=quantity_list,)
         ),
        name="MoveAndCraftItem",
     )
    
def MoveAndBuyMaterials(pos: PointOrPath, model_id: int, batches:int = 1, log: bool = False, aftercast_ms: int = 350) -> BehaviorTree:
    return RoutinesBT.Composite.Sequence(
        MoveAndInteract(pos=pos),
        _pause_heroai_for_action(
            RoutinesBT.Items.BuyMaterials(model_id=model_id, batches=batches, log=log, aftercast_ms=aftercast_ms)
        ),
        name="MoveAndBuyMaterials",
    )

def MoveAndBuyMerchantItem(pos: PointOrPath, model_id: int, quantity: int = 1, log: bool = False, aftercast_ms: int = 350) -> BehaviorTree:
    return RoutinesBT.Composite.Sequence(
        MoveAndInteract(pos=pos),
        _pause_heroai_for_action(
            RoutinesBT.Items.BuyMerchantItem(model_id=model_id, quantity=quantity, log=log, aftercast_ms=aftercast_ms)
        ),
        name="MoveAndBuyMerchantItem",
    )


#region ClearEnemies
def ClearEnemiesInArea(pos: PointOrPath, radius: float = Range.Spirit.value, allowed_alive_enemies: int = 0) -> BehaviorTree:
    point = _final_point(pos)
    return RoutinesBT.Agents.ClearEnemiesInArea(x=point.x,y=point.y,radius=radius,allowed_alive_enemies=allowed_alive_enemies,)

def WaitForClearEnemiesInArea(pos: PointOrPath, radius: float = Range.Spirit.value, allowed_alive_enemies: int = 0) -> BehaviorTree:
    point = _final_point(pos)
    return RoutinesBT.Agents.WaitForClearEnemiesInArea(x=point.x,y=point.y,radius=radius,allowed_alive_enemies=allowed_alive_enemies,)
     
#region Items
def IsItemInInventoryBags(modelID_or_encStr: int | str) -> BehaviorTree:
    return RoutinesBT.Items.IsItemInInventoryBags(modelID_or_encStr=modelID_or_encStr)

def IsItemEquipped(modelID_or_encStr: int | str) -> BehaviorTree:
    return RoutinesBT.Items.IsItemEquipped(modelID_or_encStr=modelID_or_encStr)

def EquipItemByModelID(modelID_or_encStr: int | str, aftercast_ms: int = 250, log: bool = False) -> BehaviorTree:
    from Py4GWCoreLib.Agent import Agent
    from Py4GWCoreLib import GLOBAL_CACHE
    from Py4GWCoreLib.py4gwcorelib_src.Console import Console
    from Py4GWCoreLib.py4gwcorelib_src.Console import ConsoleLog
    verify_aftercast_ms = max(250, int(aftercast_ms))

    def _is_item_equipped() -> BehaviorTree.NodeState:
        resolved_model_id = (
            Agent.GetModelIDByEncString(modelID_or_encStr)
            if isinstance(modelID_or_encStr, str)
            else int(modelID_or_encStr)
        )
        equipped_count = GLOBAL_CACHE.Inventory.GetModelCountInEquipped(resolved_model_id)
        inventory_count = GLOBAL_CACHE.Inventory.GetModelCount(resolved_model_id)
        ConsoleLog(
            "EquipItemByModelID",
            (
                f"Verify model {resolved_model_id}: "
                f"inventory_count={inventory_count}, equipped_count={equipped_count}."
            ),
            Console.MessageType.Info,
            log=log,
        )
        return (
            BehaviorTree.NodeState.SUCCESS
            if GLOBAL_CACHE.Inventory.GetModelCountInEquipped(resolved_model_id) > 0
            else BehaviorTree.NodeState.RUNNING
        )

    return BehaviorTree(
        BehaviorTree.SelectorNode(
            name=f"Equip Weapon {modelID_or_encStr}",
            children=[
                IsItemEquipped(modelID_or_encStr),
                BehaviorTree.SequenceNode(
                    name=f"EquipAndVerify {modelID_or_encStr}",
                    children=[
                        RoutinesBT.Items.EquipItemByModelID(
                            modelID_or_encStr=modelID_or_encStr,
                            aftercast_ms=aftercast_ms,
                            log=log,
                        ),
                        BehaviorTree.WaitUntilNode(
                            name=f"WaitUntilEquipped({modelID_or_encStr})",
                            condition_fn=_is_item_equipped,
                            throttle_interval_ms=100,
                            timeout_ms=verify_aftercast_ms + 1250,
                        ),
                    ],
                ),
            ],
        )
    )

def EquipInventoryBag(modelID_or_encStr: int | str,target_bag: int,timeout_ms: int = 2500,poll_interval_ms: int = 125,log: bool = False,) -> BehaviorTree:
    return RoutinesBT.Items.EquipInventoryBag(modelID_or_encStr=modelID_or_encStr,target_bag=target_bag,timeout_ms=timeout_ms,poll_interval_ms=poll_interval_ms,log=log,)

def DestroyItems(model_ids: list[int], log: bool = False, aftercast_ms: int = 75) -> BehaviorTree:
    return RoutinesBT.Items.DestroyItems(model_ids=model_ids,log=log,aftercast_ms=aftercast_ms,)
    
def DestroyBonusItems(exclude_list: list[int] = [], log: bool = False, aftercast_ms: int = 75) -> BehaviorTree:
    return RoutinesBT.Items.DestroyBonusItems(exclude_list=exclude_list,log=log,aftercast_ms=aftercast_ms,)
    
def SpawnBonusItems(log: bool = False, spawn_settle_ms: int = 50) -> BehaviorTree:
    return RoutinesBT.Items.SpawnBonusItems(log=log, aftercast_ms=spawn_settle_ms)

def SpawnAndDestroyBonusItems(exclude_list: list[int] = [], log: bool = False) -> BehaviorTree:
    return RoutinesBT.Items.SpawnAndDestroyBonusItems(exclude_list=exclude_list,log=log,)

def AddModelToLootWhitelist(model_id: int) -> BehaviorTree:
    return RoutinesBT.Items.AddModelToLootWhitelist(model_id=model_id,)

def LootItems(distance: float = Range.Earshot.value, timeout_ms: int = 10000) -> BehaviorTree:
    return RoutinesBT.Items.LootItems(distance=distance,timeout_ms=timeout_ms,)

def RestockItems(model_id: int, desired_quantity: int, allow_missing: bool = False) -> BehaviorTree:
    return RoutinesBT.Items.RestockItems(
        model_id=model_id,
        desired_quantity=desired_quantity,
        allow_missing=allow_missing,
    )

def RestockItemsFromList(items: SequenceABC[tuple[int, int]], allow_missing: bool = False) -> BehaviorTree:
    return RoutinesBT.Items.RestockItemsFromList(
        items=items,
        allow_missing=allow_missing,
    )

def HasItemQuantity(model_id: int, quantity: int) -> BehaviorTree:
    return RoutinesBT.Items.HasItemQuantity(model_id=model_id, quantity=quantity)

def DepositModelToStorage(model_id: int, aftercast_ms: int = 150) -> BehaviorTree:
    return RoutinesBT.Items.DepositModelToStorage(model_id=model_id,aftercast_ms=aftercast_ms,)

def DepositGoldKeep(gold_amount_to_leave_on_character: int = 0, aftercast_ms: int = 150) -> BehaviorTree:
    return RoutinesBT.Items.DepositGoldKeep(gold_amount_to_leave_on_character=gold_amount_to_leave_on_character,aftercast_ms=aftercast_ms,)

def EqualizeGold(target_gold: int, deposit_all: bool = True, log: bool = False, aftercast_ms: int = 150) -> BehaviorTree:
    return RoutinesBT.Items.EqualizeGold(
        target_gold=target_gold,
        deposit_all=deposit_all,
        log=log,
        aftercast_ms=aftercast_ms,
    )

def BuyMaterial(model_id: int, rare_trader: bool = False, log: bool = False, aftercast_ms: int = 125) -> BehaviorTree:
    return _pause_heroai_for_action(
        RoutinesBT.Items.BuyMaterial(
            model_id=model_id,
            rare_trader=rare_trader,
            log=log,
            aftercast_ms=aftercast_ms,
        )
    )

def BuyMaterials(
    model_id: int,
    batches: int = 1,
    rare_trader: bool = False,
    log: bool = False,
    aftercast_ms: int = 125,
) -> BehaviorTree:
    return _pause_heroai_for_action(
        RoutinesBT.Items.BuyMaterials(
            model_id=model_id,
            batches=batches,
            rare_trader=rare_trader,
            log=log,
            aftercast_ms=aftercast_ms,
        )
    )

def BuyMaterialsFromList(
    materials: list[tuple[int, int]],
    rare_trader: bool = False,
    log: bool = False,
    aftercast_ms: int = 125,
) -> BehaviorTree:
    return _pause_heroai_for_action(
        RoutinesBT.Items.BuyMaterialsFromList(
            materials=materials,
            rare_trader=rare_trader,
            log=log,
            aftercast_ms=aftercast_ms,
        )
    )

def BuyMerchantItem(model_id: int, quantity: int = 1, log: bool = False, aftercast_ms: int = 350) -> BehaviorTree:
    return _pause_heroai_for_action(
        RoutinesBT.Items.BuyMerchantItem(
            model_id=model_id,
            quantity=quantity,
            log=log,
            aftercast_ms=aftercast_ms,
        )
    )

def ExchangeCollectorItem(output_model_id: int,trade_model_ids: list[int],quantity_list: list[int],cost: int = 0,aftercast_ms: int = 150,) -> BehaviorTree:
    return _pause_heroai_for_action(
        RoutinesBT.Items.ExchangeCollectorItem(output_model_id=output_model_id,trade_model_ids=trade_model_ids,quantity_list=quantity_list,cost=cost,aftercast_ms=aftercast_ms,)    
    )

def CraftItem(output_model_id: int,cost: int,trade_model_ids: list[int],quantity_list: list[int],aftercast_ms: int = 350,) -> BehaviorTree:
    return _pause_heroai_for_action(
        RoutinesBT.Items.CraftItem(output_model_id=output_model_id,cost=cost,trade_model_ids=trade_model_ids,quantity_list=quantity_list,aftercast_ms=aftercast_ms,)
    )
     
def NeedsInventoryCleanup(exclude_models: list[int] | None = None) -> BehaviorTree:
    return RoutinesBT.Items.NeedsInventoryCleanup(exclude_models=exclude_models)

def SellInventoryItems(exclude_models: list[int] | None = None,log: bool = False,) -> BehaviorTree:
    return _pause_heroai_for_action(
        RoutinesBT.Items.SellInventoryItems(exclude_models=exclude_models,log=log,)
    ) 
    
def DestroyZeroValueItems(exclude_models: list[int] | None = None,log: bool = False,aftercast_ms: int = 100,) -> BehaviorTree:
    return RoutinesBT.Items.DestroyZeroValueItems(exclude_models=exclude_models,log=log,aftercast_ms=aftercast_ms,)

def CustomizeWeapon(
        frame_label: str = "Merchant.CustomizeWeaponButton",
        aftercast_ms: int = 500,
    ) -> BehaviorTree:
    return _pause_heroai_for_action(
        RoutinesBT.Items.CustomizeWeapon(frame_label=frame_label,aftercast_ms=aftercast_ms,)
    )

#region skills
def LoadSkillbar(template: str, log: bool = False) -> BehaviorTree:
    return RoutinesBT.Skills.LoadSkillbar(template=template,log=log,)

def LoadSkillbarFromMap(
    profession_level_skillbars: Mapping[str, SequenceABC[tuple[int | None, str]]],
    default_template: str = "",
    log: bool = False,
) -> BehaviorTree:
    return RoutinesBT.Skills.LoadSkillbarFromMap(
        profession_level_skillbars=profession_level_skillbars,
        default_template=default_template,
        log=log,
    )

def LoadHeroSkillbar(hero_index: int, template: str, log: bool = False) -> BehaviorTree:
    return RoutinesBT.Skills.LoadHeroSkillbar(hero_index=hero_index,template=template,log=log,)

def CastSkillID(skill_id: int,
                target_agent_id: int = 0,
                extra_condition: bool = True,
                aftercast_delay_ms: int = 50,
                log: bool = False
) -> BehaviorTree:
    return RoutinesBT.Skills.CastSkillID(
        skill_id=skill_id,
        target_agent_id=target_agent_id,
        extra_condition=extra_condition,
        aftercast_delay=aftercast_delay_ms,
        log=log,
    )
RoutinesBT.Skills.CastSkillID

#region Party
def ToggleHeroPanel() -> BehaviorTree:
    return PressKeybind(Key.H.value)

def ToggleSkillsAndAttributes() -> BehaviorTree:
    return PressKeybind(ControlAction.ControlAction_OpenSkillsAndAttributes.value)

def PressEsc() -> BehaviorTree:
    return BehaviorTree(
        BehaviorTree.SequenceNode(
            name="PressEsc",
            children=[
                Wait(duration_ms=250, log=False),
                PressKeybind(Key.Escape.value),
            ],
        )
    )


def LeaveParty() -> BehaviorTree:
    def _log_disbanding_if_needed(_node: BehaviorTree.Node) -> BehaviorTree:
        from Py4GWCoreLib import Party

        if Party.IsPartyLoaded() and int(Party.GetPlayerCount() or 0) > 1:
            return LogMessage(message="disbanding")
        return BehaviorTree(
            BehaviorTree.SucceederNode(name="SkipDisbandingLog")
        )

    return RoutinesBT.Composite.Sequence(
        BehaviorTree.SubtreeNode(
            name="LogDisbandingIfNeeded",
            subtree_fn=_log_disbanding_if_needed,
        ),
        RoutinesBT.Multibox.KickAllAccounts(
            timeout_ms=15000,
            poll_interval_ms=100,
            log=False,
            aftercast_ms=250,
        ),
        RoutinesBT.Party.LeaveParty(aftercast_ms=600,),
        name="LeaveParty",
    )


def Resign(
    wait_for_map_load: bool = False,
    target_map_id: int | None = None,
    target_map_name: str | None = None,
    multi_account: bool = False,
    timeout_ms: int = 30000,
    poll_interval_ms: int = 100,
    aftercast_ms: int = 250,
    log: bool = False,
) -> BehaviorTree:
    def _set_wipe_recovery_suppressed(value: bool) -> BehaviorTree:
        def _set(node: BehaviorTree.Node) -> BehaviorTree.NodeState:
            node.blackboard['party_wipe_recovery_suppressed'] = bool(value)
            return BehaviorTree.NodeState.SUCCESS

        return BehaviorTree(
            BehaviorTree.ActionNode(
                name='SuppressPartyWipeRecovery' if value else 'UnsuppressPartyWipeRecovery',
                action_fn=_set,
                aftercast_ms=0,
            )
        )

    children: list[BehaviorTree | BehaviorTree.Node] = []
    children.append(LogMessage(message="Resign initiated"))
    children.append(_set_wipe_recovery_suppressed(True))
    if multi_account:
        children.append(
            RoutinesBT.Multibox.ResignAllAccounts(
                refs_blackboard_key='__resign_message_refs',
                timeout_ms=timeout_ms,
                poll_interval_ms=poll_interval_ms,
                log=log,
                aftercast_ms=aftercast_ms,
            )
        )
    children.append(
        RoutinesBT.Shared.SendAndWait(
            command=SharedCommandType.Resign,
            include_self=True,
            refs_blackboard_key='__self_resign_message_refs',
            timeout_ms=timeout_ms,
            poll_interval_ms=poll_interval_ms,
            log=log,
            aftercast_ms=aftercast_ms,
        )
    )
    if wait_for_map_load:
        children.append(
            WaitForMapLoad(
                map_id=0 if target_map_id is None else int(target_map_id),
                timeout_ms=timeout_ms,
                map_name='' if target_map_name is None else str(target_map_name),
            )
        )
    children.append(_set_wipe_recovery_suppressed(False))
    children.append(LogMessage(message="Resign completed"))

    return Sequence(
        name="Resign",
        children=children,
    )

def _flag_heroai_accounts_by_party_position(
    party_positions: list[int] | None,
    x: float,
    y: float,
    *,
    flag_all: bool = False,
    aftercast_ms: int = 125,
) -> BehaviorTree:
    resolved_positions = [int(pos) for pos in (party_positions or []) if int(pos) >= 0]

    def _apply_flag(_node: BehaviorTree.Node) -> BehaviorTree.NodeState:
        from Py4GWCoreLib import GLOBAL_CACHE, Agent, Party

        party_id = int(GLOBAL_CACHE.Party.GetPartyID() or 0)
        leader_id = int(GLOBAL_CACHE.Party.GetPartyLeaderID() or 0)
        facing_angle = float(Agent.GetRotationAngle(leader_id) if leader_id > 0 else 0.0)

        if flag_all:
            leader_options = GLOBAL_CACHE.ShMem.GetHeroAIOptionsByPartyNumber(0)
            if leader_options is not None:
                leader_options.AllFlag.x = float(x)
                leader_options.AllFlag.y = float(y)
                leader_options.IsFlagged = True
                leader_options.FlagFacingAngle = facing_angle
            return BehaviorTree.NodeState.SUCCESS

        target_positions = set(resolved_positions)
        if not target_positions:
            return BehaviorTree.NodeState.SUCCESS

        for account, options in GLOBAL_CACHE.ShMem.GetAllActiveAccountHeroAIPairs(sort_results=False):
            if (
                not account
                or options is None
                or not account.IsSlotActive
                or account.IsHero
                or int(account.AgentPartyData.PartyID or 0) != party_id
            ):
                continue

            party_position = int(account.AgentPartyData.PartyPosition or -1)
            if party_position not in target_positions:
                continue

            options.FlagPos.x = float(x)
            options.FlagPos.y = float(y)
            options.IsFlagged = True
            options.FlagFacingAngle = facing_angle

        return BehaviorTree.NodeState.SUCCESS

    return BehaviorTree(
        BehaviorTree.ActionNode(
            name="FlagHeroAIAccounts",
            action_fn=_apply_flag,
            aftercast_ms=max(0, int(aftercast_ms)),
        )
    )


def _unflag_heroai_accounts(*, aftercast_ms: int = 125) -> BehaviorTree:
    def _clear_flags(_node: BehaviorTree.Node) -> BehaviorTree.NodeState:
        from Py4GWCoreLib import GLOBAL_CACHE

        party_id = int(GLOBAL_CACHE.Party.GetPartyID() or 0)
        for account, options in GLOBAL_CACHE.ShMem.GetAllActiveAccountHeroAIPairs(sort_results=False):
            if (
                not account
                or options is None
                or not account.IsSlotActive
                or int(account.AgentPartyData.PartyID or 0) != party_id
            ):
                continue

            options.IsFlagged = False
            options.FlagPos.x = 0.0
            options.FlagPos.y = 0.0
            options.AllFlag.x = 0.0
            options.AllFlag.y = 0.0
            options.FlagFacingAngle = 0.0

        return BehaviorTree.NodeState.SUCCESS

    return BehaviorTree(
        BehaviorTree.ActionNode(
            name="UnflagHeroAIAccounts",
            action_fn=_clear_flags,
            aftercast_ms=max(0, int(aftercast_ms)),
        )
    )


def FlagHero(hero_position: int, x: float, y: float) -> BehaviorTree:
    resolved_position = int(hero_position)

    def _subtree(_node: BehaviorTree.Node) -> BehaviorTree:
        from Py4GWCoreLib import GLOBAL_CACHE

        hero_count = int(GLOBAL_CACHE.Party.GetHeroCount() or 0)
        if 0 < resolved_position <= hero_count:
            return RoutinesBT.Party.FlagHero(hero_position=resolved_position, x=x, y=y)
        return _flag_heroai_accounts_by_party_position([resolved_position], x, y)

    return BehaviorTree(
        BehaviorTree.SubtreeNode(
            name="FlagHeroOrAccount",
            subtree_fn=_subtree,
        )
    )


def FlagAllHeroes(x: float, y: float) -> BehaviorTree:
    return RoutinesBT.Composite.Sequence(
        RoutinesBT.Party.FlagAllHeroes(x=x, y=y),
        _flag_heroai_accounts_by_party_position(None, x, y, flag_all=True),
        name="FlagAllHeroes",
    )


def FlagHeroesFromList(hero_positions: list[int | str] | None, x: float, y: float, flag_all: bool = False) -> BehaviorTree:
    if flag_all:
        return FlagAllHeroes(x=x, y=y)

    raw_positions = list(hero_positions or [])

    def _subtree(_node: BehaviorTree.Node) -> BehaviorTree:
        from Py4GWCoreLib import GLOBAL_CACHE

        hero_count = int(GLOBAL_CACHE.Party.GetHeroCount() or 0)
        resolved_positions: list[int] = []
        for value in raw_positions:
            try:
                resolved = int(value)
            except Exception:
                continue
            if resolved > 0 and resolved not in resolved_positions:
                resolved_positions.append(resolved)

        hero_positions_only = [pos for pos in resolved_positions if pos <= hero_count]
        account_positions_only = [pos for pos in resolved_positions if pos > hero_count]

        children: list[BehaviorTree | BehaviorTree.Node] = [
            RoutinesBT.Party.FlagHero(hero_position=pos, x=x, y=y)
            for pos in hero_positions_only
        ]
        if account_positions_only:
            children.append(_flag_heroai_accounts_by_party_position(account_positions_only, x, y))

        if not children:
            return BehaviorTree(BehaviorTree.SucceederNode(name="FlagHeroesFromListEmpty"))

        return RoutinesBT.Composite.Sequence(
            *children,
            name="FlagHeroesFromList",
        )

    return BehaviorTree(
        BehaviorTree.SubtreeNode(
            name="FlagHeroesOrAccountsFromList",
            subtree_fn=_subtree,
        )
    )


def UnflagAllHeroes(log: bool = False, aftercast_ms: int = 125) -> BehaviorTree:
    return RoutinesBT.Composite.Sequence(
        RoutinesBT.Party.UnflagAllHeroes(log=log, aftercast_ms=aftercast_ms),
        _unflag_heroai_accounts(aftercast_ms=aftercast_ms),
        name="UnflagAllHeroes",
    )

def DropBundle(log: bool = False) -> BehaviorTree:
    return RoutinesBT.Party.DropBundle(log=log)

def WaitForActiveQuest(quest_id: int, timeout_ms: int = 1500, throttle_interval_ms: int = 150) -> BehaviorTree:
    return RoutinesBT.Party.WaitForActiveQuest(quest_id=quest_id,timeout_ms=timeout_ms,throttle_interval_ms=throttle_interval_ms,)

def WaitForQuestCleared(quest_id: int, timeout_ms: int = 1500, throttle_interval_ms: int = 150) -> BehaviorTree:
    return RoutinesBT.Party.WaitForActiveQuestCleared(quest_id=quest_id,timeout_ms=timeout_ms,throttle_interval_ms=throttle_interval_ms,)

def LogoutToCharacterSelect() -> BehaviorTree:
    return RoutinesBT.Player.LogoutToCharacterSelect()


def SummonAccountByEmail(
    account_email: str,
    timeout_ms: int = 15000,
    poll_interval_ms: int = 100,
    log: bool = False,
) -> BehaviorTree:
    return RoutinesBT.Multibox.SummonAccountByEmail(
        account_email=account_email,
        timeout_ms=timeout_ms,
        poll_interval_ms=poll_interval_ms,
        log=log,
    )


def InviteAccountByEmail(
    account_email: str,
    timeout_ms: int = 15000,
    poll_interval_ms: int = 100,
    log: bool = False,
) -> BehaviorTree:
    return RoutinesBT.Multibox.InviteAccountByEmail(
        account_email=account_email,
        timeout_ms=timeout_ms,
        poll_interval_ms=poll_interval_ms,
        log=log,
    )



def CreateParty(
    hero_ids: list[int] | None = None,
    henchman_ids: list[int] | None = None,
    multibox_invite: bool = False,
    timeout_ms: int = 15000,
    poll_interval_ms: int = 100,
    aftercast_ms: int = 250,
    log: bool = False,
) -> BehaviorTree:
    hero_ids = list(hero_ids or [])
    henchman_ids = list(henchman_ids or [])

    def _conditional_log_subtree(
        name: str,
        message: str,
        predicate: Callable[[], bool],
    ) -> BehaviorTree.Node:
        def _subtree(_node: BehaviorTree.Node) -> BehaviorTree:
            if predicate():
                return LogMessage(message=message)
            return BehaviorTree(BehaviorTree.SucceederNode(name=f"Skip{name}"))

        return BehaviorTree.SubtreeNode(
            name=name,
            subtree_fn=_subtree,
        )

    def _conditional_tree_subtree(
        name: str,
        predicate: Callable[[], bool],
        tree_factory: Callable[[], BehaviorTree | BehaviorTree.Node],
    ) -> BehaviorTree.Node:
        def _subtree(_node: BehaviorTree.Node) -> BehaviorTree:
            if predicate():
                return BehaviorTree(Node(tree_factory()))
            return BehaviorTree(BehaviorTree.SucceederNode(name=f"Skip{name}"))

        return BehaviorTree.SubtreeNode(
            name=name,
            subtree_fn=_subtree,
        )

    def _need_summon_accounts() -> bool:
        from Py4GWCoreLib.routines_src.behaviourtrees_src.shared import _account_emails_not_on_same_map_as_local
        return len(_account_emails_not_on_same_map_as_local()) > 0

    def _need_invite_accounts() -> bool:
        from Py4GWCoreLib.routines_src.behaviourtrees_src.shared import _account_emails_on_same_map_as_local
        return len(_account_emails_on_same_map_as_local(include_self=True)) > 1

    children: list[BehaviorTree | BehaviorTree.Node] = [LeaveParty()]
    if multibox_invite:
        children.append(_conditional_log_subtree("LogSummoningAccountsIfNeeded", "summoning accounts", _need_summon_accounts))
        children.append(_conditional_tree_subtree(
            "SummonAllAccountsIfNeeded",
            _need_summon_accounts,
            lambda: RoutinesBT.Multibox.SummonAllAccounts(
                timeout_ms=timeout_ms,
                poll_interval_ms=poll_interval_ms,
                log=log,
            ),
        ))
        children.append(_conditional_tree_subtree(
            "WaitAfterSummonIfNeeded",
            _need_summon_accounts,
            lambda: RoutinesBT.Player.Wait(duration_ms=1000, log=log),
        ))
        children.append(_conditional_log_subtree("LogInvitingAccountsIfNeeded", "invitng accoutns", _need_invite_accounts))
        children.append(_conditional_tree_subtree(
            "InviteAllAccountsIfNeeded",
            _need_invite_accounts,
            lambda: RoutinesBT.Multibox.InviteAllAccounts(
                timeout_ms=timeout_ms,
                poll_interval_ms=poll_interval_ms,
                log=log,
                aftercast_ms=aftercast_ms,
            ),
        ))
    if hero_ids or henchman_ids:
        children.append(LogMessage(
            message=f"loading party heroes={hero_ids}, henchmen={henchman_ids}"
        ))
        children.append(RoutinesBT.Party.LoadParty(
            hero_ids=hero_ids,
            henchman_ids=henchman_ids,
            log=log,
            aftercast_ms=aftercast_ms,
        ))

    if not children:
        return Succeeder(name="CreatePartyEmpty",)

    return RoutinesBT.Composite.Sequence(
        *children,
        name="CreateParty",
    )

    
#region blackboard

def StoreProfessionNames() -> BehaviorTree:
    return RoutinesBT.Player.StoreProfessionNames()

def SaveBlackboardValue(key: str, value, log: bool = False) -> BehaviorTree:
    return RoutinesBT.Player.SaveBlackboardValue(
        key=key,
        value=value,
        log=log,
    )

def LoadBlackboardValue(
    source_key: str,
    target_key: str = "result",
    fail_if_missing: bool = True,
    log: bool = False,
) -> BehaviorTree:
    return RoutinesBT.Player.LoadBlackboardValue(
        source_key=source_key,
        target_key=target_key,
        fail_if_missing=fail_if_missing,
        log=log,
    )

def HasBlackboardValue(key: str, log: bool = False) -> BehaviorTree:
    return RoutinesBT.Player.HasBlackboardValue(
        key=key,
        log=log,
    )

def BlackboardValueEquals(key: str, value, log: bool = False) -> BehaviorTree:
    return RoutinesBT.Player.BlackboardValueEquals(
        key=key,
        value=value,
        log=log,
    )

def ClearBlackboardValue(key: str, log: bool = False) -> BehaviorTree:
    return RoutinesBT.Player.ClearBlackboardValue(
        key=key,
        log=log,
    )

def StoreRerollContext(
        character_name_key: str = "reroll_character_name",
        profession_key: str = "reroll_primary_profession",
        campaign_key: str = "reroll_campaign",
        campaign_name: str = "Nightfall",
        fallback_profession: str = "Warrior",
    ) -> BehaviorTree:
    return RoutinesBT.Player.StoreRerollContext(
        character_name_key=character_name_key,
        profession_key=profession_key,
        campaign_key=campaign_key,
        campaign_name=campaign_name,
        fallback_profession=fallback_profession,
    )


#region misc
#helpers
def PressKeybind(keybind_index: int, duration_ms: int = 75, log: bool = False) -> BehaviorTree:
    return RoutinesBT.Keybinds.PressKeybind(
        keybind_index=keybind_index,
        duration_ms=duration_ms,
        log=log,
    )
    
def SendChatMessage(message: str, channel: str = "say", log: bool = False) -> BehaviorTree:
    return RoutinesBT.Player.SendChatMessage(message=message, channel=channel, log=log,)

def SendChatCommand(command: str, log: bool = False) -> BehaviorTree:
    return RoutinesBT.Player.SendChatCommand(command=command, log=log,)

def SetPlayerStatus(
    status: PlayerStatus | int | str,
    log: bool = False,
    aftercast_ms: int = 250,
    verify: bool = True,
    timeout_ms: int = 3000,
) -> BehaviorTree:
    return RoutinesBT.Player.SetPlayerStatus(
        status=status,
        log=log,
        aftercast_ms=aftercast_ms,
        verify=verify,
        timeout_ms=timeout_ms,
    )

def ClickWindowFrame(frame_name: str, aftercast_ms: int = 250) -> BehaviorTree:
    return RoutinesBT.Player.ClickWindowFrame(frame_name=frame_name,aftercast_ms=aftercast_ms,)

def CancelSkillRewardWindow() -> BehaviorTree:
    return RoutinesBT.Player.CancelSkillRewardWindow(aftercast_ms=1000,)

def ResetActionQueues() -> BehaviorTree:
    return RoutinesBT.Player.ResetActionQueues()

def TypeTextFromBlackboard(key: str,delay_ms: int = 50,name: str = "TypeTextFromBlackboard",) -> BehaviorTree:
    return RoutinesBT.Player.TypeTextFromBlackboard(key=key,delay_ms=delay_ms,name=name,)

def PasteTextFromBlackboard(key: str,name: str = "PasteTextFromBlackboard",) -> BehaviorTree:
    return RoutinesBT.Player.PasteTextFromBlackboard(key=key,name=name,)

def PressRightArrowTimes(count_key: str,delay_ms: int = 500,name: str = "PressRightArrowTimes",) -> BehaviorTree:
    return RoutinesBT.Player.PressRightArrowTimes(count_key=count_key,delay_ms=delay_ms,name=name,)

def StoreCampaignArrowCount(campaign_key: str = "reroll_campaign",count_key: str = "reroll_campaign_arrow_count",) -> BehaviorTree:
    return RoutinesBT.Player.StoreCampaignArrowCount(campaign_key=campaign_key,count_key=count_key,)

def StoreProfessionArrowCount(profession_key: str = "reroll_primary_profession",count_key: str = "reroll_profession_arrow_count",) -> BehaviorTree:
    return RoutinesBT.Player.StoreProfessionArrowCount(profession_key=profession_key,count_key=count_key,)

def ResolveRerollNewCharacterName(character_name_key: str = "reroll_character_name",new_character_name_key: str = "reroll_character_name",) -> BehaviorTree:
    return RoutinesBT.Player.ResolveRerollNewCharacterName(character_name_key=character_name_key,new_character_name_key=new_character_name_key,)

def DeleteCharacterFromBlackboard(character_name_key: str = "reroll_character_name",timeout_ms: int = 45000,) -> BehaviorTree:
    return RoutinesBT.Player.DeleteCharacterFromBlackboard(character_name_key=character_name_key,timeout_ms=timeout_ms,)

def CreateCharacterFromBlackboard(character_name_key: str = "reroll_new_character_name",campaign_key: str = "reroll_campaign",profession_key: str = "reroll_primary_profession",timeout_ms: int = 60000,) -> BehaviorTree:
    return RoutinesBT.Player.CreateCharacterFromBlackboard(character_name_key=character_name_key,campaign_key=campaign_key,profession_key=profession_key,timeout_ms=timeout_ms,)


#region compositeRoutines

class Questmode():
    Accept = "accept"
    Complete = "complete"
    Step = "step"
    Skip = "skip"


def HandleAutoQuest(
    pos: PointOrPath | None,
    buttons: int | list[int] = 0,
    use_npc_model_or_enc_str: int | str | None = None,
    require_quest_marker: bool = False,
    log: bool = False,
) -> BehaviorTree:
    import Py4GW
    from Py4GWCoreLib.Agent import Agent
    from Py4GWCoreLib.routines_src.Agents import Agents as RoutinesAgents
    from typing import cast

    module_name = "HandleAutoQuest"
    resolved_pos: PointOrPath | None = pos if pos is not None else None

    def _resolve_npc_id() -> int:
        nonlocal resolved_pos

        if use_npc_model_or_enc_str is not None:
            return int(RoutinesAgents.GetAgentIDByModelOrEncStr(use_npc_model_or_enc_str) or 0)

        if resolved_pos is not None:
            final_point = PointPath.final_point(resolved_pos)
            if final_point is not None:
                return int(RoutinesAgents.GetNearestNPCXY(final_point.x, final_point.y, 200.0) or 0)
        return 0

    def _pre_checks(node: BehaviorTree.Node) -> BehaviorTree.NodeState:
        nonlocal resolved_pos

        if resolved_pos is None:
            if use_npc_model_or_enc_str is None:
                Py4GW.Console.Log(
                    module_name,
                    "HandleAutoQuest failed: no position or NPC model provided.",
                    Py4GW.Console.MessageType.Warning,
                )
                return BehaviorTree.NodeState.FAILURE

            agent_id = _resolve_npc_id()
            if agent_id == 0:
                if require_quest_marker:
                    return BehaviorTree.NodeState.RUNNING
                Py4GW.Console.Log(
                    module_name,
                    f"HandleAutoQuest failed: could not resolve NPC model {use_npc_model_or_enc_str}.",
                    Py4GW.Console.MessageType.Warning,
                )
                return BehaviorTree.NodeState.FAILURE
            agent_x, agent_y = Agent.GetXY(agent_id)
            resolved_pos = (agent_x, agent_y)

        if log:
            Py4GW.Console.Log(
                module_name,
                f"HandleAutoQuest start: pos={resolved_pos} buttons={buttons} npc={use_npc_model_or_enc_str}",
                Py4GW.Console.MessageType.Info,
            )
        return BehaviorTree.NodeState.SUCCESS

    def _single_button_number() -> int:
        if isinstance(buttons, int):
            return int(buttons)
        return int(buttons[0]) if buttons else 0

    def _mid_checks() -> BehaviorTree:
        if not require_quest_marker:
            return BehaviorTree(
                BehaviorTree.ActionNode(
                    name="HandleAutoQuestMidChecksNoop",
                    action_fn=lambda: BehaviorTree.NodeState.SUCCESS,
                )
            )

        def _wait_for_quest_marker() -> BehaviorTree.NodeState:
            npc_id = _resolve_npc_id()
            if npc_id != 0 and Agent.HasQuest(npc_id):
                return BehaviorTree.NodeState.SUCCESS
            return BehaviorTree.NodeState.RUNNING

        return BehaviorTree(
            BehaviorTree.WaitUntilNode(
                name="HandleAutoQuestWaitForQuestMarker",
                condition_fn=_wait_for_quest_marker,
                throttle_interval_ms=150,
                timeout_ms=30000,
            )
        )

    def _move_dialog_node() -> BehaviorTree:
        nonlocal resolved_pos
        move_pos = resolved_pos
        if move_pos is None:
            raise ValueError("HandleAutoQuest requires a resolved position before movement.")
        if use_npc_model_or_enc_str is None:
            if isinstance(buttons, int):
                return MoveAndAutoDialog(
                    pos=cast(PointOrPath, move_pos),
                    buttons=_single_button_number(),
                    log=log,
                )
            return RoutinesBT.Composite.Sequence(
                Move(pos=cast(PointOrPath, move_pos), tolerance=150.0, log=log),
                _wait_until_player_stops_moving(log=log),
                Wait(_POST_MOVEMENT_SETTLE_MS, log=log),
                TargetNearestAndAutoDialog(pos=cast(PointOrPath, move_pos), buttons=buttons, target_distance=Range.Nearby.value, log=log),
                name="MoveAndAutoDialogSequence",
            )
        if isinstance(buttons, int):
            return MoveAndAutoDialogByModelID(
                modelID_or_encStr=use_npc_model_or_enc_str,
                button_number=_single_button_number(),
                log=log,
            )
        return RoutinesBT.Composite.Sequence(
            MoveToModelID(modelID_or_encStr=use_npc_model_or_enc_str, log=log),
            _wait_until_player_stops_moving(log=log),
            Wait(_POST_MOVEMENT_SETTLE_MS, log=log),
            TargetAgentByModelIDAndAutoDialog(modelID_or_encStr=use_npc_model_or_enc_str, buttons=buttons, log=log),
            name="MoveAndAutoDialogByModelIDSequence",
        )

    def _post_checks() -> BehaviorTree:
        return Wait(150, log=log)

    return BehaviorTree(
        BehaviorTree.SequenceNode(
            name="HandleAutoQuest",
            children=[
                BehaviorTree.ActionNode(name="HandleAutoQuestPreChecks", action_fn=_pre_checks),
                _mid_checks(),
                Subtree(
                    name="HandleAutoQuestMoveDialogSubtree",
                    subtree_fn=lambda node: _move_dialog_node(),
                ),
                _post_checks(),
            ],
        )
    )



def HandleQuest(
    quest_id: int,
    pos: PointOrPath | None,
    dialog_id: int,
    mode: str = Questmode.Accept,
    multi_dialog_id: int = 0,
    use_npc_model_or_enc_str: int | str | None = None,
    require_quest_marker: bool = False,
    success_map_id: int = 0,
    cancel_skill_reward_window: bool = False,
    log: bool = False,
) -> BehaviorTree:
    import Py4GW
    from Py4GWCoreLib.Map import Map
    from Py4GWCoreLib.Quest import Quest
    from Py4GWCoreLib.Agent import Agent
    from Py4GWCoreLib.routines_src.Agents import Agents as RoutinesAgents
    from typing import cast
    
    MODULE_NAME = "HandleQuest"
    
    blackboard_map_key = f"handlequest_initial_map_id_{quest_id}_{mode}"
    blackboard_active_quest_key = f"handlequest_initial_active_quest_id_{quest_id}_{mode}"
    blackboard_completion_key = f"handlequest_initial_completed_{quest_id}_{mode}"
    resolved_pos: PointOrPath | None = pos if pos is not None else None
    post_check_timeout_ms = 10000
    post_check_throttle_ms = 150

    def _quest_in_log() -> bool:
        return int(quest_id) in [int(qid) for qid in (Quest.GetQuestLogIds() or [])]

    def _quest_completed() -> bool:
        try:
            return bool(Quest.IsQuestCompleted(int(quest_id)))
        except Exception:
            return False

    def _current_active_quest_id() -> int:
        try:
            return int(Quest.GetActiveQuest() or 0)
        except Exception:
            return 0

    def _npc_has_quest_marker() -> bool:
        npc_id = 0
        if use_npc_model_or_enc_str is not None:
            npc_id = int(RoutinesAgents.GetAgentIDByModelOrEncStr(use_npc_model_or_enc_str) or 0)
        elif resolved_pos is not None:
            final_point = PointPath.final_point(resolved_pos)
            if final_point is not None:
                npc_id = int(RoutinesAgents.GetNearestNPCXY(final_point.x, final_point.y, 200.0) or 0)
        return bool(npc_id != 0 and Agent.HasQuest(npc_id))

    def _pre_checks(node: BehaviorTree.Node) -> BehaviorTree.NodeState:
        nonlocal resolved_pos
        if resolved_pos is None:
            if use_npc_model_or_enc_str is None:
                Py4GW.Console.Log(MODULE_NAME, f"HandleQuest failed: no position or NPC model provided for quest {quest_id} in mode {mode}.", Py4GW.Console.MessageType.Warning)
                return BehaviorTree.NodeState.FAILURE

            agent_id = int(RoutinesAgents.GetAgentIDByModelOrEncStr(use_npc_model_or_enc_str) or 0)
            if agent_id == 0:
                Py4GW.Console.Log(MODULE_NAME, f"HandleQuest failed: could not resolve NPC model {use_npc_model_or_enc_str} for quest {quest_id}.", Py4GW.Console.MessageType.Warning)
                return BehaviorTree.NodeState.FAILURE
            agent_x, agent_y = Agent.GetXY(agent_id)
            resolved_pos = (agent_x, agent_y)

        node.blackboard[blackboard_map_key] = int(Map.GetMapID() or 0)
        node.blackboard[blackboard_active_quest_key] = _current_active_quest_id()
        node.blackboard[blackboard_completion_key] = _quest_completed()
        Quest.RequestQuestInfo(int(quest_id), update_marker=True)
        if log:
            Py4GW.Console.Log(
                MODULE_NAME,
                f"HandleQuest start: quest={quest_id} mode={mode} pos={resolved_pos} dialog={dialog_id} npc={use_npc_model_or_enc_str}",
                Py4GW.Console.MessageType.Info,
            )
        if mode == Questmode.Accept and _quest_in_log():
            Py4GW.Console.Log(MODULE_NAME, f"HandleQuest accept failed: quest {quest_id} already in log.", Py4GW.Console.MessageType.Warning)
            return BehaviorTree.NodeState.FAILURE
        if mode in (Questmode.Complete, Questmode.Step) and not _quest_in_log():
            Py4GW.Console.Log(MODULE_NAME, f"HandleQuest {mode} failed: quest {quest_id} not in log.", Py4GW.Console.MessageType.Warning)
            return BehaviorTree.NodeState.FAILURE
        return BehaviorTree.NodeState.SUCCESS
    
    def _mid_checks() -> BehaviorTree:
        if not require_quest_marker:
            return BehaviorTree(
                BehaviorTree.ActionNode(
                    name="HandleQuestMidChecksNoop",
                    action_fn=lambda: BehaviorTree.NodeState.SUCCESS,
                )
            )

        def _wait_for_quest_marker() -> BehaviorTree.NodeState:
            nonlocal resolved_pos

            npc_id = 0
            if use_npc_model_or_enc_str is not None:
                npc_id = int(RoutinesAgents.GetAgentIDByModelOrEncStr(use_npc_model_or_enc_str) or 0)
            elif resolved_pos is not None:
                final_point = PointPath.final_point(resolved_pos)
                if final_point is not None:
                    npc_id = int(RoutinesAgents.GetNearestNPCXY(final_point.x, final_point.y, 200.0) or 0)

            if npc_id != 0 and Agent.HasQuest(npc_id):
                return BehaviorTree.NodeState.SUCCESS
            return BehaviorTree.NodeState.RUNNING

        return BehaviorTree(
            BehaviorTree.WaitUntilNode(
                name="HandleQuestWaitForQuestMarker",
                condition_fn=_wait_for_quest_marker,
                throttle_interval_ms=150,
                timeout_ms=30000,
            )
        )
    

    def _post_checks() -> BehaviorTree:
        def _wait_for_result(node: BehaviorTree.Node) -> BehaviorTree.NodeState:
            current_map_id = int(Map.GetMapID() or 0)
            initial_map_id = int(node.blackboard.get(blackboard_map_key, 0) or 0)

            if success_map_id != 0 and current_map_id == int(success_map_id):
                return BehaviorTree.NodeState.SUCCESS

            if mode == Questmode.Accept:
                return (
                    BehaviorTree.NodeState.SUCCESS
                    if _quest_in_log()
                    else BehaviorTree.NodeState.RUNNING
                )

            if mode == Questmode.Complete:
                initial_active_quest_id = int(node.blackboard.get(blackboard_active_quest_key, 0) or 0)
                initial_completed = bool(node.blackboard.get(blackboard_completion_key, False))
                if current_map_id != initial_map_id:
                    return BehaviorTree.NodeState.SUCCESS
                if _quest_completed() and not initial_completed:
                    return BehaviorTree.NodeState.SUCCESS
                if initial_active_quest_id == int(quest_id) and _current_active_quest_id() != int(quest_id):
                    return BehaviorTree.NodeState.SUCCESS
                if (
                    require_quest_marker
                    and initial_active_quest_id == int(quest_id)
                    and _current_active_quest_id() != int(quest_id)
                    and _npc_has_quest_marker()
                ):
                    return BehaviorTree.NodeState.SUCCESS
                return (
                    BehaviorTree.NodeState.SUCCESS
                    if not _quest_in_log()
                    else BehaviorTree.NodeState.RUNNING
                )

            if mode == Questmode.Step:
                if current_map_id != initial_map_id:
                    return BehaviorTree.NodeState.SUCCESS

                npc_id = 0
                if use_npc_model_or_enc_str is not None:
                    npc_id = int(RoutinesAgents.GetAgentIDByModelOrEncStr(use_npc_model_or_enc_str) or 0)
                elif resolved_pos is not None:
                    final_point = PointPath.final_point(resolved_pos)
                    if final_point is not None:
                        npc_id = int(RoutinesAgents.GetNearestNPCXY(final_point.x, final_point.y, 200.0) or 0)

                if npc_id != 0 and not Agent.HasQuest(npc_id):
                    return BehaviorTree.NodeState.SUCCESS
                return BehaviorTree.NodeState.RUNNING
            
            return BehaviorTree.NodeState.SUCCESS

        return BehaviorTree(
            BehaviorTree.WaitUntilNode(
                name="HandleQuestPostChecks",
                condition_fn=_wait_for_result,
                throttle_interval_ms=post_check_throttle_ms,
                timeout_ms=post_check_timeout_ms,
            )
        )
    
    def _move_node() -> BehaviorTree:
        nonlocal resolved_pos
        if resolved_pos is None:
            raise ValueError("HandleQuest requires a resolved position before movement.")
        return BehaviorTree(
                BehaviorTree.SequenceNode(
                    name="HandleQuestMove",
                    children=[
                        Move(pos=cast(PointOrPath, resolved_pos), log=log),
                        Wait(_POST_MOVEMENT_SETTLE_MS, log=log),
                    ]
                )
        )

    def _move_dialog_node() -> BehaviorTree:
        nonlocal resolved_pos
        move_pos = resolved_pos
        if move_pos is None:
            raise ValueError("HandleQuest requires a resolved position before movement.")
        if use_npc_model_or_enc_str is None:
            return MoveAndDialog(pos=move_pos, dialog_id=dialog_id, log=log)
        else:
            return BehaviorTree(
                BehaviorTree.SequenceNode(
                    name="Move And Dialog With Model Check",
                    children=[
                        MoveAndDialogByModelID(modelID_or_encStr=use_npc_model_or_enc_str, dialog_id=dialog_id, log=log),
                    ]
                 )
             )

    def _move_subtree() -> BehaviorTree:
        return Subtree(
            name="HandleQuestMoveSubtree",
            subtree_fn=lambda node: (
                _move_node()
                if require_quest_marker
                else BehaviorTree(
                    BehaviorTree.ActionNode(
                        name="HandleQuestMoveNoop",
                        action_fn=lambda: BehaviorTree.NodeState.SUCCESS,
                    )
                )
            ),
        )

    def _move_dialog_subtree() -> BehaviorTree:
        return Subtree(
            name="HandleQuestMoveDialogSubtree",
            subtree_fn=lambda node: _move_dialog_node(),
        )

    def _cancel_skill_reward_window_node() -> BehaviorTree:
        if not cancel_skill_reward_window:
            return BehaviorTree(
                BehaviorTree.ActionNode(
                    name="HandleQuestCancelSkillRewardWindowNoop",
                    action_fn=lambda: BehaviorTree.NodeState.SUCCESS,
                )
            )
        return BehaviorTree(
                BehaviorTree.SequenceNode(
                    name="Move And Dialog With Model Check",
                    children=[
                        Wait(250, log=log),
                        CancelSkillRewardWindow()]
                )
            )
    
    def _extra_dialog_node() -> BehaviorTree:
        if multi_dialog_id == 0:
            return BehaviorTree(
                BehaviorTree.ActionNode(
                    name="HandleQuestNoMultiDialog",
                    action_fn=lambda: BehaviorTree.NodeState.SUCCESS,
                )
            )
        else:
            return BehaviorTree(
                BehaviorTree.SequenceNode(
                    name="HandleQuestMultiDialog",
                    children=[
                        SendDialog(dialog_id=multi_dialog_id, log=log),
                    ]
                )
            )
        
    return BehaviorTree(
        BehaviorTree.SequenceNode(
            name="Quest Handler",
            children=[
                BehaviorTree.ActionNode(name="HandleQuestPreChecks",action_fn=_pre_checks,),
                _move_subtree(),
                _mid_checks(),
                _move_dialog_subtree(),
                _post_checks(),
                _cancel_skill_reward_window_node(),
                _extra_dialog_node(),
            ]
        )
    )    

