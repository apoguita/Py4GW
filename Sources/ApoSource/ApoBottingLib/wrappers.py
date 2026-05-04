from collections.abc import Mapping
from collections.abc import Sequence

from Py4GWCoreLib.py4gwcorelib_src.BehaviorTree import BehaviorTree
from Py4GWCoreLib.routines_src.BehaviourTrees import BT as RoutinesBT

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

_POST_MOVEMENT_SETTLE_MS = 500

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

def AutoDialog(button_number: int = 0, log: bool = False) -> BehaviorTree:
    return _pause_heroai_for_action(RoutinesBT.Player.SendAutomaticDialog(button_number=button_number, log=log))

def SendDialog(dialog_id: int | str, log: bool = False) -> BehaviorTree:
    return _pause_heroai_for_action(RoutinesBT.Player.SendDialog(dialog_id=dialog_id, log=log))

def _final_point(pos: PointOrPath) -> Vec2f:
    point = PointPath.final_point(pos)
    if point is None:
        raise ValueError("PointPath cannot be empty.")
    return point

def DialogAtXY(pos: PointOrPath, dialog_id: int | str, target_distance: float = 200.0) -> BehaviorTree:
    point = _final_point(pos)
    return RoutinesBT.Composite.Sequence(
        TargetNearest(x=point.x, y=point.y, target_distance=target_distance, log=False),
        InteractTarget(log=False),
        SendDialog(dialog_id=dialog_id, log=False),
        name="DialogAtXY",
    )
    
def InteractWithGadgetAtXY(pos: PointOrPath, target_distance: float = 200.0) -> BehaviorTree:
    point = _final_point(pos)
    return RoutinesBT.Composite.Sequence(
        TargetNearestGadget(x=point.x, y=point.y, target_distance=target_distance, log=False),
        InteractTarget(log=False),
        name="InteractWithGadgetAtXY",
    )
    
def TargetAndDialogByModelID(modelID_or_encStr: int | str, dialog_id: int | str) -> BehaviorTree:
    return RoutinesBT.Composite.Sequence(
        TargetAgentByModelID(modelID_or_encStr=modelID_or_encStr,log=False,),
        InteractTarget(log=False),
        SendDialog(dialog_id=dialog_id, log=False),
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

#region Waits
def Wait(duration_ms: int, log: bool = False) -> BehaviorTree:
    return RoutinesBT.Player.Wait(duration_ms=duration_ms, log=log)

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
def Move(pos: PointOrPath,pause_on_combat: bool = True,tolerance: float = 150.0,) -> BehaviorTree:
    return RoutinesBT.Movement.MovePath(pos=pos,pause_on_combat=pause_on_combat,tolerance=tolerance,log=False,)

def MoveDirect(pos: PointOrPath, pause_on_combat: bool = True) -> BehaviorTree:
    return RoutinesBT.Movement.MoveDirect(PointPath.as_path(pos), pause_on_combat=pause_on_combat, log=False)

def MoveAndExitMap(pos: PointOrPath, target_map_id: int = 0, target_map_name: str = "") -> BehaviorTree:
    return RoutinesBT.Composite.Sequence(
            Move(pos=pos, pause_on_combat=False, tolerance=150.0),
            WaitForMapLoad(map_id=target_map_id, map_name=target_map_name),
    )

def MoveAndKill(pos: PointOrPath, clear_area_radius: float = Range.Spirit.value) -> BehaviorTree:
    return RoutinesBT.Movement.MoveAndKillPath(pos=pos,clear_area_radius=clear_area_radius,)

def MoveAndTarget(pos: PointOrPath,target_distance: float = Range.Adjacent.value,move_tolerance: float = 150.0,log: bool = False,) -> BehaviorTree:
    return RoutinesBT.Movement.MoveAndTargetPath(pos=pos,target_distance=target_distance,move_tolerance=move_tolerance,log=log,)

def MoveAndInteract(pos: PointOrPath,target_distance: float = Range.Area.value,move_tolerance: float = 150.0,) -> BehaviorTree:
    return RoutinesBT.Composite.Sequence(
        MoveAndTarget(pos=pos,target_distance=target_distance,move_tolerance=move_tolerance,log=False,),
        Wait(_POST_MOVEMENT_SETTLE_MS, log=False),
        InteractTarget(log=False),
        name="MoveAndInteract",
    )
        
def MoveAndAutoDialog(pos: PointOrPath,button_number: int = 0,target_distance: float = Range.Nearby.value,move_tolerance: float = 150.0,) -> BehaviorTree:
    return RoutinesBT.Composite.Sequence(
        MoveAndTarget(pos=pos,target_distance=target_distance,move_tolerance=move_tolerance,log=False,),
        Wait(_POST_MOVEMENT_SETTLE_MS, log=False),
        InteractTarget(log=False),
        AutoDialog(button_number=button_number, log=False),
        name="MoveAndAutoDialog",
    )

def MoveAndDialog(pos: PointOrPath,dialog_id: int | str,target_distance: float = Range.Nearby.value,move_tolerance: float = 150.0,) -> BehaviorTree:
    return RoutinesBT.Composite.Sequence(
        MoveAndTarget(pos=pos,target_distance=target_distance,move_tolerance=move_tolerance,log=False,),
        Wait(_POST_MOVEMENT_SETTLE_MS, log=False),
        InteractTarget(log=False),
        SendDialog(dialog_id=dialog_id, log=False),
        name="MoveAndDialog",
    )
    
def MoveAndTargetByModelID(modelID_or_encStr: int | str, log: bool = False) -> BehaviorTree:
    return RoutinesBT.Agents.MoveAndTargetByModelID( modelID_or_encStr=modelID_or_encStr,log=log)
    
def MoveAndAutoDialogByModelID(modelID_or_encStr: int | str, button_number: int = 0) -> BehaviorTree:
    return RoutinesBT.Composite.Sequence(
        MoveAndTargetByModelID(modelID_or_encStr=modelID_or_encStr, log=False),
        Wait(_POST_MOVEMENT_SETTLE_MS, log=False),
        InteractTarget(log=False),
        AutoDialog(button_number=button_number, log=False),
        name="MoveAndAutoDialogByModelID",
    )

def MoveAndDialogByModelID(modelID_or_encStr: int | str, dialog_id: int | str) -> BehaviorTree:
    return RoutinesBT.Composite.Sequence(
        MoveAndTargetByModelID(modelID_or_encStr=modelID_or_encStr, log=False),
        Wait(_POST_MOVEMENT_SETTLE_MS, log=False),
        InteractTarget(log=False),
        SendDialog(dialog_id=dialog_id, log=False),
        name="MoveAndDialogByModelID",
    )

def MoveAndInteractByModelID(modelID_or_encStr: int | str, target_distance: float = Range.Nearby.value) -> BehaviorTree:
    return RoutinesBT.Composite.Sequence(
        MoveAndTargetByModelID(modelID_or_encStr=modelID_or_encStr, log=False),
        Wait(_POST_MOVEMENT_SETTLE_MS, log=False),
        InteractTarget(log=False),
        name="MoveAndInteractByModelID",
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

def EquipItemByModelID(modelID_or_encStr: int | str, aftercast_ms: int = 150) -> BehaviorTree:
    return RoutinesBT.Items.EquipItemByModelID(modelID_or_encStr=modelID_or_encStr,aftercast_ms=aftercast_ms,)

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

def BuyMerchantItem(model_id: int, quantity: int = 1, log: bool = False, aftercast_ms: int = 250) -> BehaviorTree:
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
    profession_level_skillbars: Mapping[str, Sequence[tuple[int | None, str]]],
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

def LeaveParty() -> BehaviorTree:
    return RoutinesBT.Party.LeaveParty(aftercast_ms=250,)

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
    return RoutinesBT.Party.WaitForQuestCleared(quest_id=quest_id,timeout_ms=timeout_ms,throttle_interval_ms=throttle_interval_ms,)

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
