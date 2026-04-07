from Py4GWCoreLib.py4gwcorelib_src.BehaviorTree import BehaviorTree
from Py4GWCoreLib.routines_src.BehaviourTrees import BT as RoutinesBT, Routines
from Py4GWCoreLib.native_src.internals.types import Vec2f
from Py4GWCoreLib.enums import Range

PointOrPath = Vec2f | list[Vec2f]


def _as_path(pos: PointOrPath) -> list[Vec2f]:
    return pos if isinstance(pos, list) else [pos]


def _sequence_from_points(
    name: str,
    points: list[Vec2f],
    leaf_builder,
) -> BehaviorTree:
    if not points:
        return BehaviorTree(
            BehaviorTree.SucceederNode(
                name=f"{name}EmptyPath",
            )
        )

    if len(points) == 1:
        return leaf_builder(points[0])

    return BehaviorTree(
        BehaviorTree.SequenceNode(
            name=name,
            children=[leaf_builder(point) for point in points],
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
    

  
#region Player  
def AutoDialog(button_number: int = 0) -> BehaviorTree:
    return RoutinesBT.Player.SendAutomaticDialog(button_number=button_number)

def Wait(duration_ms: int, log: bool = False) -> BehaviorTree:
    return RoutinesBT.Player.Wait(duration_ms=duration_ms, log=log)

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

def ClearBlackboardValue(key: str, log: bool = False) -> BehaviorTree:
    return RoutinesBT.Player.ClearBlackboardValue(
        key=key,
        log=log,
    )

#region Map
def WaitForMapLoad(map_id: int) -> BehaviorTree:
    return RoutinesBT.Map.WaitforMapLoad(map_id=map_id)


def TravelToOutpost(outpost_id: int) -> BehaviorTree:
    return RoutinesBT.Map.TravelToOutpost(outpost_id=outpost_id)

#region Movement
def Move(pos: PointOrPath, pause_on_combat: bool = True) -> BehaviorTree:
    return _sequence_from_points(
        "MovePath",
        _as_path(pos),
        lambda point: RoutinesBT.Player.Move(x=point.x, y=point.y, pause_on_combat=pause_on_combat, log=False),
    )

def MoveDirect(list_of_positions: list[Vec2f], pause_on_combat: bool = True) -> BehaviorTree:
    return RoutinesBT.Player.MoveDirect(list_of_positions, pause_on_combat=pause_on_combat, log=False)

def MoveAndKill(pos: PointOrPath, clear_area_radius: float = Range.Spirit.value) -> BehaviorTree:
    return _sequence_from_points(
        "MoveAndKillPath",
        _as_path(pos),
        lambda point: RoutinesBT.Player.MoveAndKill(
            coords=point,
            clear_area_radius=clear_area_radius,
        ),
    )

def MoveAndTarget(
    pos: PointOrPath,
    target_distance: float = Range.Adjacent.value,
    log: bool = False,
) -> BehaviorTree:
    points = _as_path(pos)
    if len(points) <= 1:
        point = points[0]
        return RoutinesBT.Agents.MoveAndTarget(
            x=point.x,
            y=point.y,
            target_distance=target_distance,
            log=log,
        )

    return BehaviorTree(
        BehaviorTree.SequenceNode(
            name="MoveAndTargetPath",
            children=[
                *[RoutinesBT.Player.Move(x=point.x, y=point.y, log=False) for point in points[:-1]],
                RoutinesBT.Agents.MoveAndTarget(
                    x=points[-1].x,
                    y=points[-1].y,
                    target_distance=target_distance,
                    log=log,
                ),
            ],
        )
    )

def MoveAndInteract(pos: PointOrPath, target_distance: float = Range.Area.value) -> BehaviorTree:
    points = _as_path(pos)
    if len(points) <= 1:
        point = points[0]
        return RoutinesBT.Agents.MoveTargetAndInteract(
            x=point.x,
            y=point.y,
            target_distance=target_distance,
        )

    return BehaviorTree(
        BehaviorTree.SequenceNode(
            name="MoveAndInteractPath",
            children=[
                *[RoutinesBT.Player.Move(x=point.x, y=point.y, log=False) for point in points[:-1]],
                RoutinesBT.Agents.MoveTargetAndInteract(
                    x=points[-1].x,
                    y=points[-1].y,
                    target_distance=target_distance,
                ),
            ],
        )
    )

def MoveAndAutoDialog(pos: PointOrPath, button_number: int = 0, target_distance: float = Range.Nearby.value) -> BehaviorTree:
    points = _as_path(pos)
    if len(points) <= 1:
        point = points[0]
        return RoutinesBT.Agents.MoveTargetInteractAndAutomaticDialog(
            x=point.x,
            y=point.y,
            button_number=button_number,
            target_distance=target_distance,
            log=False,
        )

    return BehaviorTree(
        BehaviorTree.SequenceNode(
            name="MoveAndAutoDialogPath",
            children=[
                *[RoutinesBT.Player.Move(x=point.x, y=point.y, log=False) for point in points[:-1]],
                RoutinesBT.Agents.MoveTargetInteractAndAutomaticDialog(
                    x=points[-1].x,
                    y=points[-1].y,
                    button_number=button_number,
                    target_distance=target_distance,
                    log=False,
                ),
            ],
        )
    )
    
def MoveAndAutoDialogByModelID(modelID_or_encStr: int | str, button_number: int = 0) -> BehaviorTree:
    return RoutinesBT.Agents.MoveTargetInteractAndAutomaticDialogByModelID(
        modelID_or_encStr=modelID_or_encStr,
        button_number=button_number,
        log=False,
    )

def MoveAndTargetByModelID(modelID_or_encStr: int | str, log: bool = False) -> BehaviorTree:
    return RoutinesBT.Agents.MoveAndTargetByModelID(
        modelID_or_encStr=modelID_or_encStr,
        log=log
    )
    
def MoveAndInteractByModelID(modelID_or_encStr: int | str, target_distance: float = Range.Nearby.value) -> BehaviorTree:
    return RoutinesBT.Agents.MoveTargetAndInteractByModelID(
        modelID_or_encStr=modelID_or_encStr,
    )

#region Agents
def ClearEnemiesInArea(pos: Vec2f, radius: float = Range.Spirit.value, allowed_alive_enemies: int = 0) -> BehaviorTree:
    return RoutinesBT.Agents.ClearEnemiesInArea(
        x=pos.x,
        y=pos.y,
        radius=radius,
        allowed_alive_enemies=allowed_alive_enemies,
    )

def WaitForClearEnemiesInArea(pos: Vec2f, radius: float = Range.Spirit.value, allowed_alive_enemies: int = 0) -> BehaviorTree:
    return RoutinesBT.Agents.WaitForClearEnemiesInArea(
        x=pos.x,
        y=pos.y,
        radius=radius,
        allowed_alive_enemies=allowed_alive_enemies,
    )
     
#region Items

def IsItemInInventoryBags(modelID_or_encStr: int | str) -> BehaviorTree:
    return RoutinesBT.Items.IsItemInInventoryBags(modelID_or_encStr=modelID_or_encStr)

def IsItemEquipped(modelID_or_encStr: int | str) -> BehaviorTree:
    return RoutinesBT.Items.IsItemEquipped(modelID_or_encStr=modelID_or_encStr)

def EquipItemByModelID(modelID_or_encStr: int | str, aftercast_ms: int = 250) -> BehaviorTree:
    return RoutinesBT.Items.EquipItemByModelID(
        modelID_or_encStr=modelID_or_encStr,
        aftercast_ms=aftercast_ms,
    )

def EquipInventoryBag(
        modelID_or_encStr: int | str,
        target_bag: int,
        timeout_ms: int = 2500,
        poll_interval_ms: int = 125,
        log: bool = False,
    ) -> BehaviorTree:
    return RoutinesBT.Items.EquipInventoryBag(
        modelID_or_encStr=modelID_or_encStr,
        target_bag=target_bag,
        timeout_ms=timeout_ms,
        poll_interval_ms=poll_interval_ms,
        log=log,
    )

def DestroyItems(model_ids: list[int], log: bool = False, aftercast_ms: int = 75) -> BehaviorTree:
    return RoutinesBT.Items.DestroyItems(
        model_ids=model_ids,
        log=log,
        aftercast_ms=aftercast_ms,
    )
    
def DestroyBonusItems(exclude_list: list[int] = [], log: bool = False, aftercast_ms: int = 75) -> BehaviorTree:
    return RoutinesBT.Items.DestroyBonusItems(
        exclude_list=exclude_list,
        log=log,
        aftercast_ms=aftercast_ms,
    )
    
def SpawnBonusItems(log: bool = False, spawn_settle_ms: int = 50) -> BehaviorTree:
    return RoutinesBT.Items.SpawnBonusItems(log=log, aftercast_ms=spawn_settle_ms)

def HasItemQuantity(model_id: int, quantity: int) -> BehaviorTree:
    return RoutinesBT.Items.HasItemQuantity(model_id=model_id, quantity=quantity)

def ExchangeCollectorItem(
        output_model_id: int,
        trade_model_ids: list[int],
        quantity_list: list[int],
        cost: int = 0,
        aftercast_ms: int = 500,
    ) -> BehaviorTree:
    return RoutinesBT.Items.ExchangeCollectorItem(
        output_model_id=output_model_id,
        trade_model_ids=trade_model_ids,
        quantity_list=quantity_list,
        cost=cost,
        aftercast_ms=aftercast_ms,
    )
    
def NeedsInventoryCleanup(exclude_models: list[int] | None = None) -> BehaviorTree:
    return RoutinesBT.Items.NeedsInventoryCleanup(exclude_models=exclude_models)

def SellInventoryItems(
        exclude_models: list[int] | None = None,
        log: bool = False,
    ) -> BehaviorTree:
    return RoutinesBT.Items.SellInventoryItems(
        exclude_models=exclude_models,
        log=log,
    ) 
    
def DestroyZeroValueItems(
        exclude_models: list[int] | None = None,
        log: bool = False,
        aftercast_ms: int = 100,
    ) -> BehaviorTree:
    return RoutinesBT.Items.DestroyZeroValueItems(
        exclude_models=exclude_models,
        log=log,
        aftercast_ms=aftercast_ms,
    )

def CustomizeWeapon(
        frame_label: str = "Merchant.CustomizeWeaponButton",
        aftercast_ms: int = 500,
    ) -> BehaviorTree:
    return RoutinesBT.Items.CustomizeWeapon(
        frame_label=frame_label,
        aftercast_ms=aftercast_ms,
    )

#region skills
def LoadSkillbar(template: str, log: bool = False) -> BehaviorTree:
    return RoutinesBT.Skills.LoadSkillbar(
        template=template,
        log=log,
    )

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
