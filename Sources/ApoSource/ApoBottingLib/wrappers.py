from Py4GWCoreLib.py4gwcorelib_src.BehaviorTree import BehaviorTree
from Py4GWCoreLib.routines_src.BehaviourTrees import BT as RoutinesBT
from Py4GWCoreLib.native_src.internals.types import Vec2f
from Py4GWCoreLib.enums import Range

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

#region Map
def WaitForMapLoad(map_id: int) -> BehaviorTree:
    return RoutinesBT.Map.WaitforMapLoad(map_id=map_id)


def TravelToOutpost(outpost_id: int) -> BehaviorTree:
    return RoutinesBT.Map.TravelToOutpost(outpost_id=outpost_id)

#region Movement
def Move(pos: Vec2f) -> BehaviorTree:
    return RoutinesBT.Player.Move(x=pos.x, y=pos.y)

def MoveDirect(list_of_positions: list[Vec2f]) -> BehaviorTree:
    return RoutinesBT.Player.MoveDirect(list_of_positions)

def MoveAndInteract(pos: Vec2f, target_distance: float = Range.Area.value) -> BehaviorTree:
    return RoutinesBT.Agents.MoveTargetAndInteract(
        x=pos.x,
        y=pos.y,
        target_distance=target_distance,
    )

def MoveAndAutoDialog(pos: Vec2f, button_number: int = 0, target_distance: float = Range.Nearby.value) -> BehaviorTree:
    return RoutinesBT.Agents.MoveTargetInteractAndAutomaticDialog(
        x=pos.x,
        y=pos.y,
        button_number=button_number,
        target_distance=target_distance,
    )
    
def MoveAndAutoDialogByModelID(model_id: int, button_number: int = 0) -> BehaviorTree:
    return RoutinesBT.Agents.MoveTargetInteractAndAutomaticDialogByModelID(
        model_id=model_id,
        button_number=button_number,
    )

def MoveAndTargetByModelID(model_id: int, log: bool = False) -> BehaviorTree:
    return RoutinesBT.Agents.MoveAndTargetByModelID(
        model_id=model_id,
        log=log
    )
    
#region Agents
def ClearEnemiesInArea(pos: Vec2f, radius: float = Range.Spirit.value) -> BehaviorTree:
    return RoutinesBT.Agents.ClearEnemiesInArea(
        x=pos.x,
        y=pos.y,
        radius=radius,
    )
    
#region Items
def DestroyItems(model_ids: list[int], log: bool = False, aftercast_ms: int = 50) -> BehaviorTree:
    return RoutinesBT.Items.DestroyItems(
        model_ids=model_ids,
        log=log,
        aftercast_ms=aftercast_ms,
    )
    
#region skills
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