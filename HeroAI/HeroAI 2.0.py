import PyImGui
import math
import random
from Py4GWCoreLib.py4gwcorelib_src.BehaviorTree import BehaviorTree
from Py4GWCoreLib.Routines import Routines
from Py4GWCoreLib.Agent import Agent
from Py4GWCoreLib.Player import Player
from Py4GWCoreLib.Map import Map
from Py4GWCoreLib.GlobalCache import GLOBAL_CACHE
from Py4GWCoreLib.py4gwcorelib_src.Timer import ThrottledTimer
from Py4GWCoreLib.py4gwcorelib_src.VectorFields import BumperCarVectorFields
from Py4GWCoreLib import ActionQueueManager, Range, Utils


#region PreChecker
def IsUserInterrupting() -> bool:
    from Py4GWCoreLib.enums_src.IO_enums import Key
    io = PyImGui.get_io()
    
    if io.want_capture_keyboard or io.want_capture_mouse:
        return False
    
    movement_keys = [
        Key.W.value, Key.A.value, Key.S.value, Key.D.value,
        Key.Q.value, Key.E.value, Key.Z.value, Key.R.value,
        Key.UpArrow.value, Key.DownArrow.value, 
        Key.LeftArrow.value, Key.RightArrow.value
    ]
    
    for vk in movement_keys:
        if PyImGui.is_key_down(vk):
            return True

    if (PyImGui.is_mouse_down(0) and PyImGui.is_mouse_down(1)) or PyImGui.is_mouse_down(2):
        return True

    return False

#region PreChecker
def PreCheckerSubtree(_node) -> BehaviorTree:
    return BehaviorTree(BehaviorTree.SequenceNode(
        name="PreChecker",
        children=[
            BehaviorTree.ConditionNode(
                name="IsMapValid",
                condition_fn=lambda: Routines.Checks.Map.MapValid()
            ),
            BehaviorTree.ConditionNode(
                name="IsInExplorableMap",
                condition_fn=lambda: Map.IsExplorable()
            ),
            BehaviorTree.ConditionNode(
                name="IsPartyLoaded",
                condition_fn=lambda: GLOBAL_CACHE.Party.IsPartyLoaded()
            ),
            BehaviorTree.ConditionNode(
                name="IsNotInCimenatic",
                condition_fn=lambda: not Map.IsInCinematic()
            ),
            BehaviorTree.ConditionNode(
                name="IsAlive",
                condition_fn=lambda: Agent.IsAlive(Player.GetAgentID())
            ),
            BehaviorTree.ConditionNode(
                name="IsNotKnockedDown",
                condition_fn=lambda: not Agent.IsKnockedDown(Player.GetAgentID())
            ),
            BehaviorTree.ConditionNode(
                name="IsNotUserInterrupting",
                condition_fn=lambda: not IsUserInterrupting()
            ),
        ]
    ))



last_follow_move_point: tuple[float, float] | None = None
follow_map_entry_signature: tuple[int, int, int, int] | None = None
follow_require_front_after_map_entry = False
follow_throttle_timer = ThrottledTimer(300)
follow_throttle_timer.Start()

def _combat_bumper_follow_target(raw_target_position: tuple[float, float]) -> tuple[float, float]:
    probe_position = Player.GetXY()
    to_target = (
        float(raw_target_position[0]) - float(probe_position[0]),
        float(raw_target_position[1]) - float(probe_position[1]),
    )
    distance_to_target = math.hypot(to_target[0], to_target[1])
    if distance_to_target <= 0.001:
        return raw_target_position

    solver = BumperCarVectorFields(
        probe_position=probe_position,
        target_position=raw_target_position,
        probe_radius=Range.Touch.value * 0.5,
        probe_velocity=(0.0, 0.0),
        time_horizon=0.35,
        target_weight=1.0,
        collision_weight=2.5,
        tangent_weight=0.35,
        arrival_radius=1.0,
    )

    nearby_radius = float(Range.Earshot.value)
    nearby_agent_ids: set[int] = set()

    for agent_id in Routines.Agents.GetFilteredAllyArray(probe_position[0], probe_position[1], nearby_radius, other_ally=True):
        nearby_agent_ids.add(int(agent_id))

    for agent_id in Routines.Agents.GetFilteredEnemyArray(probe_position[0], probe_position[1], nearby_radius):
        nearby_agent_ids.add(int(agent_id))

    for agent_id in Routines.Agents.GetFilteredSpiritArray(probe_position[0], probe_position[1], nearby_radius):
        nearby_agent_ids.add(int(agent_id))

    for agent_id in nearby_agent_ids:
        if agent_id <= 0 or agent_id == Player.GetAgentID() or not Agent.IsLiving(agent_id):
            continue
        solver.add_body(
            position=Agent.GetXY(agent_id),
            radius=Range.Touch.value * 0.5,
            velocity=(0.0, 0.0),
            weight=1.0,
            body_id=agent_id,
        )

    step_distance = min(distance_to_target, max(1.0, float(Range.Touch.value)))
    return solver.compute_next_position(step_distance)

def _is_in_aggro() -> bool:
    return bool(Routines.Checks.Agents.InAggro(Range.Earshot.value))

def Follow() -> BehaviorTree.NodeState:
    global last_follow_move_point, follow_map_entry_signature, follow_require_front_after_map_entry

    options = GLOBAL_CACHE.ShMem.GetHeroAIOptionsFromEmail(Player.GetAccountEmail())
    if not options or not options.Following:
        return BehaviorTree.NodeState.FAILURE

    if not bool(getattr(options, "LeaderFollowReady", False)):
        return BehaviorTree.NodeState.FAILURE

    if not follow_throttle_timer.IsExpired():
        return BehaviorTree.NodeState.FAILURE

    if Player.GetAgentID() == GLOBAL_CACHE.Party.GetPartyLeaderID():
        follow_throttle_timer.Reset()
        return BehaviorTree.NodeState.FAILURE

    map_sig = (
        int(Map.GetMapID()),
        int(Map.GetRegion()[0]),
        int(Map.GetDistrict()),
        int(Map.GetLanguage()[0]),
    )
    if follow_map_entry_signature != map_sig:
        follow_map_entry_signature = map_sig
        follow_require_front_after_map_entry = True
        last_follow_move_point = None

    follow_x = float(options.FollowPos.x)
    follow_y = float(options.FollowPos.y)
    follow_z = int(float(getattr(options.FollowPos, "z", 0.0)))
    in_aggro = _is_in_aggro()
    if in_aggro:
        combat_threshold_raw = float(getattr(options, "FollowMoveThresholdCombat", -1.0))
        if combat_threshold_raw >= 0.0:
            follow_distance = max(0.0, combat_threshold_raw)
        else:
            follow_distance = max(0.0, float(getattr(options, "FollowMoveThreshold", 0.0)))
    else:
        follow_distance = max(0.0, float(getattr(options, "FollowMoveThreshold", 0.0)))
    if Utils.Distance((follow_x, follow_y), Player.GetXY()) <= follow_distance:
        return BehaviorTree.NodeState.FAILURE

    if follow_require_front_after_map_entry:
        px, py = Player.GetXY()
        dx = follow_x - px
        dy = follow_y - py
        if abs(dx) > 0.001 or abs(dy) > 0.001:
            facing = Agent.GetRotationAngle(Player.GetAgentID())
            if ((dx * math.cos(facing)) + (dy * math.sin(facing))) <= 0.0:
                return BehaviorTree.NodeState.FAILURE

    xx = follow_x
    yy = follow_y
    if in_aggro and follow_z == 0:
        xx, yy = _combat_bumper_follow_target((follow_x, follow_y))

    if last_follow_move_point is not None:
        last_x, last_y = last_follow_move_point
        if abs(xx - last_x) <= 0.0001 and abs(yy - last_y) <= 0.0001:
            xx += random.uniform(-5.0, 5.0)
            yy += random.uniform(-5.0, 5.0)

    ActionQueueManager().ResetQueue("ACTION")
    if follow_z == 0:
        #Player.Move(xx, yy, follow_z)
        Player.Move(xx, yy)
    else:
        from Py4GWCoreLib.UIManager import UIManager
        from Py4GWCoreLib.enums_src.UI_enums import ControlAction
        ActionQueueManager().AddAction("ACTION",UIManager.Keypress,ControlAction.ControlAction_TargetPartyMember1.value, 0)
        ActionQueueManager().AddAction("ACTION",UIManager.Keypress,ControlAction.ControlAction_Follow.value, 0)



    last_follow_move_point = (xx, yy)
    follow_require_front_after_map_entry = False
    follow_throttle_timer.Reset()
    if in_aggro:
        return BehaviorTree.NodeState.SUCCESS
    return BehaviorTree.NodeState.FAILURE


def MovementBrain(_node) -> BehaviorTree:
    return BehaviorTree(BehaviorTree.SelectorNode(
        name="MovementBrain",
        children=[
            BehaviorTree.ActionNode(
                name="Follow",
                action_fn=Follow
            ),
            BehaviorTree.SucceederNode(name="NoFollowDecision")
        ]
    ))


def CombatBrain(_node) -> BehaviorTree:
    return BehaviorTree(BehaviorTree.SelectorNode(
        name="CombatBrain",
        children=[
            BehaviorTree.ActionNode(
                name="EmergencyCombat",
                action_fn=lambda: BehaviorTree.NodeState.FAILURE
            ),
            BehaviorTree.ActionNode(
                name="TargetSelection",
                action_fn=lambda: BehaviorTree.NodeState.FAILURE
            ),
            BehaviorTree.ActionNode(
                name="SkillSelection",
                action_fn=lambda: BehaviorTree.NodeState.FAILURE
            ),
            BehaviorTree.ActionNode(
                name="AutoAttackFallback",
                action_fn=lambda: BehaviorTree.NodeState.FAILURE
            ),
            BehaviorTree.SucceederNode(name="NoCombatDecision")
        ]
    ))

def ExternalInputBrain(_node) -> BehaviorTree:
    return BehaviorTree(BehaviorTree.SelectorNode(
        name="ExternalInputBrain",
        children=[
            BehaviorTree.ActionNode(
                name="HandlePlayerOverride",
                action_fn=lambda: BehaviorTree.NodeState.FAILURE
            ),
            BehaviorTree.ActionNode(
                name="HandlePartyCommands",
                action_fn=lambda: BehaviorTree.NodeState.FAILURE
            ),
            BehaviorTree.SucceederNode(name="NoExternalInput")
        ]
    ))


HeroAI_Tree: BehaviorTree = BehaviorTree(BehaviorTree.SequenceNode(
    name="HeroAI_Tree",
    children=[
        BehaviorTree.SubtreeNode(name="PreCheckerSubtree", subtree_fn=PreCheckerSubtree),
        BehaviorTree.ParallelNode(
            name="BrainLayer",
            children=[
                BehaviorTree.SubtreeNode(name="ExternalInputSubtree", subtree_fn=ExternalInputBrain),
                BehaviorTree.SubtreeNode(name="MovementSubtree", subtree_fn=MovementBrain),
                BehaviorTree.SubtreeNode(name="CombatSubtree", subtree_fn=CombatBrain),
            ]
        ),
    ]
))



def draw():
    if PyImGui.begin ("Immediate Window Reference"):
        if PyImGui.button("Toggle UI Window"):
            pass
    PyImGui.end()

def main():
    HeroAI_Tree.tick()

    


if __name__ == "__main__":
    main()
