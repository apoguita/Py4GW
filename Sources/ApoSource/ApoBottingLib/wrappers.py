import random
from collections.abc import Callable
from collections.abc import Mapping
from collections.abc import Sequence as SequenceABC

from Py4GWCoreLib.py4gwcorelib_src.BehaviorTree import BehaviorTree
from Py4GWCoreLib.routines_src.BehaviourTrees import BT as RoutinesBT
from Py4GWCoreLib.routines_src.behaviourtrees_src.player import BT

def Node(tree_or_node) -> BehaviorTree.Node:
    return BehaviorTree.Node._coerce_node(tree_or_node)
from Py4GWCoreLib.native_src.internals.types import PointPath
from Py4GWCoreLib.native_src.internals.types import PointOrPath
from Py4GWCoreLib.native_src.internals.types import Vec2f
from Py4GWCoreLib.py4gwcorelib_src.ActionQueue import ActionQueueManager
from Py4GWCoreLib.botting_tree_src.enums import HeroAIStatus
from Py4GWCoreLib.enums import Range
from Py4GWCoreLib.enums_src.IO_enums import Key
from Py4GWCoreLib.enums_src.UI_enums import ControlAction

_HEROAI_GUARD_KEY = "__apobottinglib_restore_headless_heroai"
_heroai_pause_counter = 0

_POST_MOVEMENT_SETTLE_MS = 400
_WAITSPECIAL_EMOTES: tuple[str, ...] = (
    "attention",
    "bowhead",
    "catchbreath",
    "dancenew",
    "drums",
    "excited",
    "fame",
    "flex",
    "flute",
    "guitar",
    "jump",
    "kneel",
    "paper",
    "rock",
    "salute",
    "scissors",
    "sit",
    "violin",
)
#region nodes

def Sequence(name: str, 
             map_id_or_name: int | str = 0,
             children: list[BehaviorTree | BehaviorTree.Node] | None = None,
             random_travel: bool = False,
             region_pool: str = "eu"
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
    children
        Child nodes run after the optional travel step.
        If omitted, a single `SucceederNode` is used so the wrapper still
        produces a valid sequence.
    random_travel
        When `True`, use random-district travel for the prepended travel step.
    region_pool
        Region pool forwarded to random travel.

    Returns
    -------
    BehaviorTree
        A sequence tree containing the optional travel node first, followed by
        the provided `children`.
    """
    resolved_children = children if children is not None else [BehaviorTree.SucceederNode()]

    travel_child = [Travel(target_map_id=map_id_or_name if isinstance(map_id_or_name, int) else 0,
                           target_map_name=map_id_or_name if isinstance(map_id_or_name, str) else "",
                           random_travel=random_travel,
                           region_pool=region_pool,
                          )] if map_id_or_name else []

    resolved_children = travel_child + resolved_children
    
    return BehaviorTree(
        BehaviorTree.SequenceNode(
            name=name,
            children=resolved_children,
        )
    )
    

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

    This helper first stores the current player profession names into the
    blackboard, then reads `player_primary_profession_name`, and finally returns
    the node mapped to that profession.

    Parameters
    ----------
    WarriorNode, RangerNode, MonkNode, NecromancerNode, MesmerNode,
    ElementalistNode, AssassinNode, RitualistNode, ParagonNode, DervishNode
        Optional node or tree to use for each primary profession.

    Returns
    -------
    BehaviorTree
        A wrapper sequence that stores profession names and resolves the
        matching node at tick time.

    Notes
    -----
    If the current profession has no supplied node, the helper returns a
    `FailerNode`.
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
            return BehaviorTree(BehaviorTree.FailerNode(name=f"GetNodeByProfession<{primary_profession}>"))

        return BehaviorTree(Node(selected_node))

    return Sequence(
            name="GetNodeByProfession",
            children=[
                StoreProfessionNames(),
                BehaviorTree.SubtreeNode(
                    name="GetNodeByProfessionSubtree",
                    subtree_fn=_profession_specific_node,
                ),
            ],
        )


def GetValuesByProfession(
    profession_values: Mapping[str, object],
    target_key: str = "profession_value",
    fallback_profession: str = "Warrior",
) -> BehaviorTree:
    """
    Resolve a profession-specific value and store it on the blackboard.

    This helper first stores the current player profession names into the
    blackboard, then reads `player_primary_profession_name`, looks up the value
    in `profession_values`, and writes the resolved value to `target_key`.

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
        A wrapper sequence that stores profession names and writes the resolved
        value to the blackboard.

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
                StoreProfessionNames(),
                BehaviorTree.ActionNode(
                    name="GetValuesByProfessionAction",
                    action_fn=_store_profession_value,
                ),
            ],
        )


#helpers
def PressKeybind(keybind_index: int, duration_ms: int = 75, log: bool = False) -> BehaviorTree:
    return RoutinesBT.Keybinds.PressKeybind(
        keybind_index=keybind_index,
        duration_ms=duration_ms,
        log=log,
    )


#region HeroAI helpers
def _save_headless_heroai_state() -> BehaviorTree:
    started = {"value": False}

    def _save(node: BehaviorTree.Node) -> BehaviorTree.NodeState:
        if not started["value"]:
            node.blackboard[_HEROAI_GUARD_KEY] = bool(node.blackboard.get("headless_heroai_enabled", True))
            node.blackboard["headless_heroai_enabled_request"] = False
            node.blackboard["headless_heroai_reset_runtime_request"] = True
            ActionQueueManager().ResetAllQueues()
            started["value"] = True

        if bool(node.blackboard.get("headless_heroai_enabled", True)):
            return BehaviorTree.NodeState.RUNNING
        if node.blackboard.get("HEROAI_STATUS", "") != HeroAIStatus.DISABLED.value:
            return BehaviorTree.NodeState.RUNNING
        if bool(node.blackboard.get("COMBAT_ACTIVE", False)):
            return BehaviorTree.NodeState.RUNNING
        if bool(node.blackboard.get("LOOTING_ACTIVE", False)):
            return BehaviorTree.NodeState.RUNNING
        if bool(node.blackboard.get("USER_INTERRUPT_ACTIVE", False)):
            return BehaviorTree.NodeState.RUNNING
        if bool(node.blackboard.get("PAUSE_MOVEMENT", False)):
            return BehaviorTree.NodeState.RUNNING

        started["value"] = False
        return BehaviorTree.NodeState.SUCCESS

    return BehaviorTree(BehaviorTree.ActionNode(name="PauseHeadlessHeroAIUntilReady", action_fn=_save))


def _restore_headless_heroai_state() -> BehaviorTree:
    def _restore(node: BehaviorTree.Node) -> BehaviorTree.NodeState:
        restore_enabled = bool(node.blackboard.pop(_HEROAI_GUARD_KEY, node.blackboard.get("headless_heroai_enabled", True)))
        node.blackboard["headless_heroai_enabled_request"] = restore_enabled
        node.blackboard["headless_heroai_reset_runtime_request"] = True
        return BehaviorTree.NodeState.SUCCESS

    return BehaviorTree(BehaviorTree.ActionNode(name="RestoreHeadlessHeroAIState", action_fn=_restore))


def _pause_heroai_for_action(action_tree: BehaviorTree) -> BehaviorTree:
    global _heroai_pause_counter
    _heroai_pause_counter += 1
    name = f"HeroAIPausedAction_{_heroai_pause_counter}"

    guarded_action = RoutinesBT.Composite.Sequence(
        _save_headless_heroai_state(),
        action_tree,
        _restore_headless_heroai_state(),
        name=name,
    )
    restore_after_failure = RoutinesBT.Composite.Sequence(
        _restore_headless_heroai_state(),
        BehaviorTree(BehaviorTree.FailerNode(name=f"{name}Failed")),
        name=f"{name}RestoreAfterFailure",
    )
    return BehaviorTree(
        BehaviorTree.SelectorNode(
            name=name,
            children=[
                BehaviorTree.SubtreeNode(
                    name=f"{name}Run",
                    subtree_fn=lambda node: guarded_action,
                ),
                BehaviorTree.SubtreeNode(
                    name=f"{name}Restore",
                    subtree_fn=lambda node: restore_after_failure,
                ),
            ],
        )
    )


def _movement_with_runtime_pause(
    name: str,
    builder: Callable[[bool], BehaviorTree],
    pause_on_combat: bool | None = None,
) -> BehaviorTree:
    def _subtree(node: BehaviorTree.Node) -> BehaviorTree:
        resolved_pause = bool(node.blackboard.get("pause_on_combat", True)) if pause_on_combat is None else bool(pause_on_combat)
        return builder(resolved_pause)

    return BehaviorTree(
        BehaviorTree.SubtreeNode(
            name=name,
            subtree_fn=_subtree,
        )
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

def AutoDialog(buttons: int | list[int] = 0, log: bool = False, aftercast_ms: int = 250) -> BehaviorTree:
    if isinstance(buttons, int):
        buttons = [buttons]
    else:
        buttons = list(buttons)

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

def SendDialog(dialog_id: int | str, log: bool = False) -> BehaviorTree:
    return _pause_heroai_for_action(RoutinesBT.Player.SendDialog(dialog_id=dialog_id, log=log))

def _final_point(pos: PointOrPath) -> Vec2f:
    point = PointPath.final_point(pos)
    if point is None:
        raise ValueError("PointPath cannot be empty.")
    return point

def DialogAtXY(pos: PointOrPath, dialog_id: int | str, target_distance: float = 200.0, log: bool = False) -> BehaviorTree:
    point = _final_point(pos)
    return RoutinesBT.Composite.Sequence(
        TargetNearest(x=point.x, y=point.y, target_distance=target_distance, log=log),
        InteractTarget(log=log),
        SendDialog(dialog_id=dialog_id, log=log),
        name="DialogAtXY",
    )
    
def InteractWithGadgetAtXY(pos: PointOrPath, target_distance: float = 200.0) -> BehaviorTree:
    point = _final_point(pos)
    return RoutinesBT.Composite.Sequence(
        TargetNearestGadget(x=point.x, y=point.y, target_distance=target_distance, log=False),
        InteractTarget(log=False),
        name="InteractWithGadgetAtXY",
    )
    
def TargetAndDialogByModelID(modelID_or_encStr: int | str, dialog_id: int | str, log: bool = False) -> BehaviorTree:
    return RoutinesBT.Composite.Sequence(
        TargetAgentByModelID(modelID_or_encStr=modelID_or_encStr,log=log,),
        InteractTarget(log=log),
        SendDialog(dialog_id=dialog_id, log=log),
        name="TargetAndDialogByModelID",
    )

   

#region travel
def Travel(target_map_id: int = 0, target_map_name: str = "", random_travel: bool = False, region_pool: str = "eu") -> BehaviorTree:
    if random_travel:
        return RoutinesBT.Map.TravelToRandomDistrict(target_map_id=target_map_id,target_map_name=target_map_name,region_pool=region_pool,)
    return RoutinesBT.Map.TravelToOutpost(outpost_id=target_map_id, outpost_name=target_map_name)

def TravelGH() -> BehaviorTree:
    return RoutinesBT.Map.TravelGH()

def LeaveGH() -> BehaviorTree:
    return RoutinesBT.Map.LeaveGH()

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
    wait_tree = WaitSpecial(emote=emote_str, duration_ms=duration_ms, log=log) if emote else RoutinesBT.Player.Wait(duration_ms=duration_ms, log=log)
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

def WaitSpecial(emote: str | None = None, duration_ms: int = 0, log: bool = False) -> BehaviorTree:
    """Randomly performs a safe emote command, then waits for the requested duration."""
    def _pick_emote(node: BehaviorTree.Node) -> BehaviorTree.NodeState:
        node.blackboard["waitspecial_emote"] = emote or random.choice(_WAITSPECIAL_EMOTES)
        return BehaviorTree.NodeState.SUCCESS

    return RoutinesBT.Composite.Sequence(
        BehaviorTree(
            BehaviorTree.ActionNode(
                name="WaitSpecialPickEmote",
                action_fn=_pick_emote,
            )
        ),
        BehaviorTree(
            BehaviorTree.SubtreeNode(
                name="WaitSpecialSendEmote",
                subtree_fn=lambda node: SendChatCommand(
                    command=str(node.blackboard.get("waitspecial_emote", "dance")),
                    log=log,
                ),
            )
        ),
        RoutinesBT.Player.Wait(duration_ms=duration_ms, log=log),
        name="WaitSpecial",
    ) 

def WaitUntilOnExplorable(timeout_ms: int = 15000) -> BehaviorTree:
    return RoutinesBT.Map.WaitUntilOnExplorable(timeout_ms=timeout_ms,)

def WaitUntilOutOfCombat(range: float = Range.Earshot.value, timeout_ms: int = 60000) -> BehaviorTree:
    return RoutinesBT.Agents.WaitUntilOutOfCombat(range=range,timeout_ms=timeout_ms)

def WaitUntilOnCombat(range: float = Range.Earshot.value, timeout_ms: int = 60000) -> BehaviorTree:
    return RoutinesBT.Agents.WaitUntilOnCombat(range=range,timeout_ms=timeout_ms,)
    
def WaitForMapLoad(map_id: int = 0, timeout_ms: int = 30000, map_name: str = "") -> BehaviorTree:
    return RoutinesBT.Map.WaitforMapLoad(map_id=map_id, timeout=timeout_ms, map_name=map_name,
                                         player_instance_uptime_ms=500,
                                         throttle_interval_ms=250,
                                         post_arrival_wait_ms=0,)

def WaitForMapToChange(map_id: int, timeout_ms: int = 30000, map_name: str = "") -> BehaviorTree:
    return WaitForMapLoad(map_id=map_id, timeout_ms=timeout_ms, map_name=map_name)

def WaitUntilCharacterSelect(timeout_ms: int = 45000) -> BehaviorTree:
    return RoutinesBT.Player.WaitUntilCharacterSelect(timeout_ms=timeout_ms,)


#region Movement
def Move(pos: PointOrPath,pause_on_combat: bool | None = None,tolerance: float = 150.0,log: bool = False,) -> BehaviorTree:
    return _movement_with_runtime_pause(
        "Move",
        lambda resolved_pause: RoutinesBT.Movement.MovePath(
            pos=pos,
            pause_on_combat=resolved_pause,
            tolerance=tolerance,
            log=log,
        ),
        pause_on_combat=pause_on_combat,
    )

def MoveDirect(pos: PointOrPath, pause_on_combat: bool | None = None, log: bool = False) -> BehaviorTree:
    return _movement_with_runtime_pause(
        "MoveDirect",
        lambda resolved_pause: RoutinesBT.Movement.MoveDirect(
            PointPath.as_path(pos),
            pause_on_combat=resolved_pause,
            log=log,
        ),
        pause_on_combat=pause_on_combat,
    )

def MoveAndExitMap(pos: PointOrPath, target_map_id: int = 0, target_map_name: str = "", log: bool = False) -> BehaviorTree:
    return RoutinesBT.Composite.Sequence(
            Move(pos=pos, tolerance=150.0, log=log),
            WaitForMapLoad(map_id=target_map_id, map_name=target_map_name),
    )

def MoveAndKill(
    pos: PointOrPath,
    clear_area_radius: float = Range.Spirit.value,
    pause_on_combat: bool | None = None,
) -> BehaviorTree:
    return _movement_with_runtime_pause(
        "MoveAndKill",
        lambda resolved_pause: RoutinesBT.Movement.MoveAndKillPath(
            pos=pos,
            clear_area_radius=clear_area_radius,
            pause_on_combat=resolved_pause,
        ),
        pause_on_combat=pause_on_combat,
    )

def MoveAndTarget(
    pos: PointOrPath,
    target_distance: float = Range.Adjacent.value,
    move_tolerance: float = 150.0,
    pause_on_combat: bool | None = None,
    log: bool = False,
) -> BehaviorTree:
    return _movement_with_runtime_pause(
        "MoveAndTarget",
        lambda resolved_pause: RoutinesBT.Movement.MoveAndTargetPath(
            pos=pos,
            target_distance=target_distance,
            move_tolerance=move_tolerance,
            pause_on_combat=resolved_pause,
            log=log,
        ),
        pause_on_combat=pause_on_combat,
    )

def MoveAndInteract(
    pos: PointOrPath,
    target_distance: float = Range.Area.value,
    move_tolerance: float = 150.0,
    pause_on_combat: bool | None = None,
    log: bool = False,
) -> BehaviorTree:
    return RoutinesBT.Composite.Sequence(
        MoveAndTarget(pos=pos,target_distance=target_distance,move_tolerance=move_tolerance,pause_on_combat=pause_on_combat,log=log,),
        Wait(_POST_MOVEMENT_SETTLE_MS, log=log),
        InteractTarget(log=log),
        name="MoveAndInteract",
    )

def MoveAndInteractWithGadget(
    pos: PointOrPath,
    target_distance: float = Range.Area.value,
    move_tolerance: float = 150.0,
    pause_on_combat: bool | None = None,
    log: bool = False,
) -> BehaviorTree:
    return _movement_with_runtime_pause(
        "MoveAndInteractWithGadget",
        lambda resolved_pause: RoutinesBT.Composite.Sequence(
            RoutinesBT.Movement.MoveAndTargetGadgetPath(
                pos=pos,
                target_distance=target_distance,
                move_tolerance=move_tolerance,
                pause_on_combat=resolved_pause,
                log=log,
            ),
            Wait(_POST_MOVEMENT_SETTLE_MS, log=log),
            InteractTarget(log=log),
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
    log: bool = False,
) -> BehaviorTree:
    return RoutinesBT.Composite.Sequence(
        MoveAndTarget(pos=pos,target_distance=target_distance,move_tolerance=move_tolerance,pause_on_combat=pause_on_combat,log=log,),
        Wait(_POST_MOVEMENT_SETTLE_MS, log=log),
        InteractTarget(log=log),
        AutoDialog(buttons=buttons, log=log),
        name="MoveAndAutoDialog",
    )

def MoveAndDialog(
    pos: PointOrPath,
    dialog_id: int | str,
    target_distance: float = Range.Nearby.value,
    move_tolerance: float = 150.0,
    pause_on_combat: bool | None = None,
    log: bool = False,
) -> BehaviorTree:
    return RoutinesBT.Composite.Sequence(
        MoveAndTarget(pos=pos,target_distance=target_distance,move_tolerance=move_tolerance,pause_on_combat=pause_on_combat,log=log,),
        Wait(_POST_MOVEMENT_SETTLE_MS, log=log),
        InteractTarget(log=log),
        SendDialog(dialog_id=dialog_id, log=log),
        name="MoveAndDialog",
    )
    
def MoveAndTargetByModelID(
    modelID_or_encStr: int | str,
    pause_on_combat: bool | None = None,
    log: bool = False,
) -> BehaviorTree:
    return _movement_with_runtime_pause(
        "MoveAndTargetByModelID",
        lambda resolved_pause: RoutinesBT.Movement.MoveAndTargetByModelID(
            modelID_or_encStr=modelID_or_encStr,
            pause_on_combat=resolved_pause,
            log=log,
        ),
        pause_on_combat=pause_on_combat,
    )
    
def MoveAndAutoDialogByModelID(modelID_or_encStr: int | str, button_number: int = 0, log: bool = False) -> BehaviorTree:
    return RoutinesBT.Composite.Sequence(
        MoveAndTargetByModelID(modelID_or_encStr=modelID_or_encStr, log=log),
        Wait(_POST_MOVEMENT_SETTLE_MS, log=log),
        InteractTarget(log=log),
        AutoDialog(buttons=button_number, log=log),
        name="MoveAndAutoDialogByModelID",
    )

def MoveAndDialogByModelID(modelID_or_encStr: int | str, dialog_id: int | str, log: bool = False) -> BehaviorTree:
    return RoutinesBT.Composite.Sequence(
        MoveAndTargetByModelID(modelID_or_encStr=modelID_or_encStr, log=log),
        Wait(_POST_MOVEMENT_SETTLE_MS, log=log),
        InteractTarget(log=log),
        SendDialog(dialog_id=dialog_id, log=log),
        name="MoveAndDialogByModelID",
    )

def MoveAndInteractByModelID(modelID_or_encStr: int | str, target_distance: float = Range.Nearby.value, log: bool = False) -> BehaviorTree:
    return RoutinesBT.Composite.Sequence(
        MoveAndTargetByModelID(modelID_or_encStr=modelID_or_encStr, log=log),
        Wait(_POST_MOVEMENT_SETTLE_MS, log=log),
        InteractTarget(log=log),
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

def BuyMaterial(model_id: int, log: bool = False, aftercast_ms: int = 125) -> BehaviorTree:
    return _pause_heroai_for_action(
        RoutinesBT.Items.BuyMaterial(
            model_id=model_id,
            log=log,
            aftercast_ms=aftercast_ms,
        )
    )

def BuyMaterials(model_id: int, batches: int = 1, log: bool = False, aftercast_ms: int = 125) -> BehaviorTree:
    return _pause_heroai_for_action(
        RoutinesBT.Items.BuyMaterials(
            model_id=model_id,
            batches=batches,
            log=log,
            aftercast_ms=aftercast_ms,
        )
    )

def BuyMaterialsFromList(materials: list[tuple[int, int]], log: bool = False, aftercast_ms: int = 125) -> BehaviorTree:
    return _pause_heroai_for_action(
        RoutinesBT.Items.BuyMaterialsFromList(
            materials=materials,
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
    return RoutinesBT.Party.LeaveParty(aftercast_ms=600,)

def AddHero(hero_id: int) -> BehaviorTree:
    return RoutinesBT.Party.LoadParty(hero_ids=[hero_id],)

def AddHeroList(hero_ids: list[int]) -> BehaviorTree:
    return RoutinesBT.Party.LoadParty(hero_ids=hero_ids,)

def AddHenchman(henchman_id: int) -> BehaviorTree:
    return RoutinesBT.Party.LoadParty(henchman_ids=[henchman_id],)

def AddHenchmanList(henchman_ids: list[int]) -> BehaviorTree:
    return RoutinesBT.Party.LoadParty(henchman_ids=henchman_ids,)

def WaitForActiveQuest(quest_id: int, timeout_ms: int = 1500, throttle_interval_ms: int = 150) -> BehaviorTree:
    return RoutinesBT.Party.WaitForActiveQuest(quest_id=quest_id,timeout_ms=timeout_ms,throttle_interval_ms=throttle_interval_ms,)

def WaitForQuestCleared(quest_id: int, timeout_ms: int = 1500, throttle_interval_ms: int = 150) -> BehaviorTree:
    return RoutinesBT.Party.WaitForActiveQuestCleared(quest_id=quest_id,timeout_ms=timeout_ms,throttle_interval_ms=throttle_interval_ms,)

def LogoutToCharacterSelect() -> BehaviorTree:
    return RoutinesBT.Player.LogoutToCharacterSelect()
    
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
def SendChatMessage(message: str, channel: str = "say", log: bool = False) -> BehaviorTree:
    return RoutinesBT.Player.SendChatMessage(message=message, channel=channel, log=log,)

def SendChatCommand(command: str, log: bool = False) -> BehaviorTree:
    return RoutinesBT.Player.SendChatCommand(command=command, log=log,)

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
                MoveAndTarget(pos=cast(PointOrPath, move_pos), target_distance=Range.Nearby.value, move_tolerance=150.0, log=log),
                Wait(_POST_MOVEMENT_SETTLE_MS, log=log),
                InteractTarget(log=log),
                AutoDialog(buttons=buttons, log=log),
                name="MoveAndAutoDialogSequence",
            )
        if isinstance(buttons, int):
            return MoveAndAutoDialogByModelID(
                modelID_or_encStr=use_npc_model_or_enc_str,
                button_number=_single_button_number(),
                log=log,
            )
        return RoutinesBT.Composite.Sequence(
            MoveAndTargetByModelID(modelID_or_encStr=use_npc_model_or_enc_str, log=log),
            Wait(_POST_MOVEMENT_SETTLE_MS, log=log),
            InteractTarget(log=log),
            AutoDialog(buttons=buttons, log=log),
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
                BehaviorTree.SubtreeNode(
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

    def _move_subtree() -> BehaviorTree.Node:
        return BehaviorTree.SubtreeNode(
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

    def _move_dialog_subtree() -> BehaviorTree.Node:
        return BehaviorTree.SubtreeNode(
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

