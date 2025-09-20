import Py4GW
from Py4GWCoreLib import (Routines,Botting,ActionQueueManager, ConsoleLog, GLOBAL_CACHE, Utils)
from Py4GWCoreLib.enums import ModelID, Range, TitleID
from Py4GWCoreLib.BuildMgr import BuildMgr
from Py4GWCoreLib.Builds import SF_Mes_vaettir
from Py4GWCoreLib.Builds import SF_Ass_vaettir
from typing import List, Tuple

bot = Botting("YAVB 2.0", upkeep_birthday_cupcake_restock=1)

stuck_counter = 0
stuck_able = False

def create_bot_routine(bot: Botting) -> None:
    TownRoutines(bot)
    TraverseBjoraMarches(bot)
    JagaMoraineFarmRoutine(bot)
    ResetFarmLoop(bot)
    
def TownRoutines(bot: Botting) -> None:
    bot.States.AddHeader("Town Routines")
    bot.Map.Travel(target_map_name="Longeyes Ledge")
    InitializeBot(bot)
    bot.States.AddCustomState(lambda: EquipSkillBar(bot), "Equip SkillBar")
    HandleInventory(bot)
    bot.States.AddHeader("Exit to Bjora Marches")
    bot.Party.SetHardMode(True) #set hard mode on
    bot.Move.XYAndExitMap(-26375, 16180, target_map_name="Bjora Marches")
    
def TraverseBjoraMarches(bot: Botting) -> None:
    bot.States.AddHeader("Traverse Bjora Marches")
    bot.Player.SetTitle(TitleID.Norn.value)
    path_points_to_traverse_bjora_marches: List[Tuple[float, float]] = [
    (16694.98, -17901.03), (14849, -15312),(13776, -14882), (13249, -14642),(12235, -14086),(11274, -13450),
    (10839, -13065),(10412, -12036),(10125, -10918), (10029, -10348),(9599, -9327)  ,(9121, -9009)  ,
    (8215, -8289)  ,(7339, -7542)  ,(6587, -6666)  , (6210, -6226)  ,(5457, -5349)  ,(4703, -4470)  ,
    (4379, -3990)  ,(3773, -3031)  ,(3117, -2070)  , (2678, -1703)  ,(1541, -1614)  ,(388, -1491)   ,
    (-187, -1419)  ,(-1343, -1440) ,(-2496, -1472) , (-3073, -1535) ,(-4214, -1712) ,(-5278, -1492) ,
    (-5754, -1164) ,(-6632, -419)  ,(-7770, -306)  , (-8352, -286)  ,(-9504, -226)  ,(-10665, -215) ,
    (-11247, -242) ,(-12400, -247) ,(-13529, -53)  , (-13944, 341)  ,(-14727, 1181) ,(-15539, 2010) ,
    (-15963, 2380) , (-19196, 4986),(-20300, 5600)
    ]
    bot.Move.FollowPathAndExitMap(path_points_to_traverse_bjora_marches, target_map_name="Jaga Moraine")
    
def set_stuck_detection(value: bool):
    global stuck_able
    stuck_able = value
    yield

def JagaMoraineFarmRoutine(bot: Botting) -> None:
    bot.States.AddHeader("Jaga Moraine Farm Routine")
    InitializeBot(bot)
    bot.States.AddCustomState(lambda: set_stuck_detection(True), "Enable Stuck Detection")
    bot.States.AddCustomState(lambda: AssignBuild(bot), "Assign Build")
    bot.Move.XY(13372.44, -20758.50)
    bot.Dialogs.AtXY(13367, -20771,0x84)
    path_points_to_farming_route1: List[Tuple[float, float]] = [
    (11375, -22761), (10925, -23466), (10917, -24311), (10280, -24620), (9640, -23175),
    (7815, -23200), (7765, -22940), (8213, -22829), (8740, -22475), (8880, -21384),
    (8684, -20833), (8982, -20576),
    ]
    bot.Move.FollowPath(path_points_to_farming_route1)
    bot.States.AddHeader("Wait for Left Aggro Ball")
    bot.States.AddCustomState(lambda: WaitForAggroBall(bot), "Wait for Left Aggro Ball")
    path_points_to_farming_route2: List[Tuple[float, float]] = [
    (10196, -20124), (10123, -19529),(10049, -18933), (9976, -18338), (11316, -18056),
    (10392, -17512), (10114, -16948),(10729, -16273), (10505, -14750),(10815, -14790),
    (11090, -15345), (11670, -15457),(12604, -15320), (12450, -14800),(12725, -14850),
    (12476, -16157),]
    bot.Move.FollowPath(path_points_to_farming_route2)
    bot.States.AddHeader("Wait for Right Aggro Ball")
    bot.States.AddCustomState(lambda: WaitForAggroBall(bot), "Wait for Right Aggro Ball")
    bot.States.AddCustomState(lambda: set_stuck_detection(False), "Disable Stuck Detection")
    bot.Properties.Set("movement_tolerance",value=25)
    path_points_to_killing_spot: List[Tuple[float, float]] = [
        (13070, -16911), (12938, -17081), (12790, -17201), (12747, -17220), (12703, -17239),
        (12684, -17184),]
    bot.Move.FollowPath(path_points_to_killing_spot)
    bot.Properties.Set("movement_tolerance",value=150)
    bot.States.AddHeader("Kill Enemies")
    bot.States.AddCustomState(lambda: KillEnemies(bot), "Kill Enemies")
    bot.Properties.Disable("auto_combat")
    bot.States.AddHeader("Loot Items")
    bot.Items.LootItems()
    bot.Items.AutoIDAndSalvageItems()
    bot.States.AddCustomState(lambda: NeedsInventoryManagement(bot), "Needs Inventory Management")
    bot.Move.XYAndExitMap(15850,-20550, target_map_name="Bjora Marches")
    
def ResetFarmLoop(bot: Botting) -> None:
    bot.States.AddHeader("Reset Farm Loop")
    bot.Move.XYAndExitMap(-20300, 5600 , target_map_name="Jaga Moraine")
    bot.States.JumpToStepName("[H]Jaga Moraine Farm Routine_6")
            
#region Helpers   
def InitializeBot(bot: Botting) -> None:
    bot.Events.OnDeathCallback(lambda: on_death(bot))
    bot.Events.OnStuckCallback(lambda: on_stuck(bot))
    bot.Events.SetStuckRoutineEnabled(True)
    bot.States.AddHeader("Initialize Bot")
    bot.Properties.Disable("auto_inventory_management")
    bot.Properties.Disable("auto_loot")
    bot.Properties.Disable("hero_ai")
    bot.Properties.Enable("auto_combat")
    bot.Properties.Disable("pause_on_danger")
    bot.Properties.Enable("halt_on_death")
    bot.Properties.Set("movement_timeout",value=-1)
    bot.Properties.Enable("birthday_cupcake")
    bot.Properties.Enable("identify_kits")
    bot.Properties.Enable("salvage_kits")

def AssignBuild(bot: Botting):
    profession, _ = GLOBAL_CACHE.Agent.GetProfessionNames(GLOBAL_CACHE.Player.GetAgentID())
    match profession:
        case "Assassin":
            bot.OverrideBuild(SF_Ass_vaettir())
        case "Mesmer":
            bot.OverrideBuild(SF_Mes_vaettir())  # Placeholder for Mesmer build 
        case _:
            ConsoleLog("Unsupported Profession", f"The profession '{profession}' is not supported by this bot.", Py4GW.Console.MessageType.Error)
            bot.Stop()
            return
    yield
    
def EquipSkillBar(bot: Botting):
    yield from AssignBuild(bot)
    yield from bot.config.build_handler.LoadSkillBar()
    
def HandleInventory(bot: Botting) -> None:
    bot.States.AddHeader("Inventory Handling")
    bot.Items.AutoIDAndSalvageAndDepositItems() #sort bags, auto id, salvage, deposit to bank
    bot.Move.XYAndInteractNPC(-23110, 14942) # Merchant in Longeyes Ledge
    bot.Wait.ForTime(500)
    bot.Merchant.SellMaterialsToMerchant() # Sell materials to merchant, make space in inventory
    bot.Merchant.Restock.IdentifyKits() #restock identify kits
    bot.Merchant.Restock.SalvageKits() #restock salvage kits
    bot.Items.AutoIDAndSalvageAndDepositItems() #sort bags again to make sure everything is deposited
    bot.Merchant.SellMaterialsToMerchant() #Sell remaining materials again to make sure inventory is clear
    bot.Merchant.Restock.IdentifyKits() #restock identify kits
    bot.Merchant.Restock.SalvageKits() #restock salvage kits
    bot.Items.Restock.BirthdayCupcake() #restock birthday cupcake
    
def NeedsInventoryManagement(bot: Botting):
    free_slots_in_inventory = GLOBAL_CACHE.Inventory.GetFreeSlotCount()
    leave_empty_slots = bot.Properties.Get("leave_empty_inventory_slots", "value")

    count_of_id_kits = GLOBAL_CACHE.Inventory.GetModelCount(ModelID.Superior_Identification_Kit.value)
    count_of_salvage_kits = GLOBAL_CACHE.Inventory.GetModelCount(ModelID.Salvage_Kit.value)

    if (
        free_slots_in_inventory < leave_empty_slots
        or count_of_id_kits == 0
        or count_of_salvage_kits == 0
    ):
        bot.States.JumpToStepName("[H]Town Routines_1")
    yield
    
import time

def WaitForAggroBall(bot: Botting):
    ConsoleLog("Waiting for Aggro Ball", "Waiting for enemies to ball up.", Py4GW.Console.MessageType.Info, False)
    event = bot.Events._events.on_stuck
    event.set_in_waiting_routine(True)

    build = bot.config.build_handler
    elapsed = 0
    max_ticks = 150  # 150 * 100ms = 15s max

    start_time = time.time()  # <-- hard time check baseline
    max_seconds = 15          # <-- hard timeout threshold

    while elapsed < max_ticks:
        yield from Routines.Yield.wait(100)
        elapsed += 1

        # Extra hard timeout based on real time
        #this was added explicitely for preventing a very rare ocurring bug where the routine would get stuck here forever
        #do not remove this check unless you have a better solution
        if time.time() - start_time >= max_seconds:
            break

        px, py = GLOBAL_CACHE.Player.GetXY()
        enemies_ids = Routines.Agents.GetFilteredEnemyArray(px, py, Range.Earshot.value)

        if not enemies_ids:
            continue

        all_in_adjacent = True
        for enemy_id in enemies_ids:
            enemy = GLOBAL_CACHE.Agent.GetAgent(enemy_id)
            if enemy is None:
                all_in_adjacent = False
                continue
            dx, dy = enemy.x - px, enemy.y - py
            if dx * dx + dy * dy > (Range.Adjacent.value ** 2):
                all_in_adjacent = False
                break

        if all_in_adjacent:
            break  # success before timeout

    event.set_in_waiting_routine(False)

    # Always proceed after success or timeout
    if isinstance(build, (SF_Ass_vaettir, SF_Mes_vaettir)):
        yield from build.CastHeartOfShadow()

def KillEnemies(bot: Botting):
    build = bot.config.build_handler
    event = bot.Events._events.on_stuck
    event.set_in_killing_routine(True)
    
    if isinstance(build, SF_Ass_vaettir) or isinstance(build, SF_Mes_vaettir):
        build.SetKillingRoutine(True)
        
    player_pos = GLOBAL_CACHE.Player.GetXY()
    enemy_array = Routines.Agents.GetFilteredEnemyArray(player_pos[0],player_pos[1],Range.Spellcast.value)
    
    start_time = Utils.GetBaseTimestamp()
    timeout = 120000
    
    while len(enemy_array) > 0: #sometimes not all enemies are killed
        current_time = Utils.GetBaseTimestamp()
        delta = current_time - start_time
        if delta > timeout and timeout > 0:
            ConsoleLog("Killing Routine", "Timeout reached, restarting.", Py4GW.Console.MessageType.Error)
            fsm = bot.config.FSM
            fsm.jump_to_state_by_name("[H]Town Routines_1") 
            return
  
        if GLOBAL_CACHE.Agent.IsDead(GLOBAL_CACHE.Player.GetAgentID()):
            ConsoleLog("Killing Routine", "Player is dead, restarting.", Py4GW.Console.MessageType.Warning)
            fsm = bot.config.FSM
            fsm.jump_to_state_by_name("[H]Town Routines_1")   
        yield from Routines.Yield.wait(1000)
        enemy_array = Routines.Agents.GetFilteredEnemyArray(player_pos[0],player_pos[1],Range.Spellcast.value)
    
    event.set_in_killing_routine(False)
    event.set_finished_routine(True)
    if isinstance(build, SF_Ass_vaettir) or isinstance(build, SF_Mes_vaettir):
        build.SetKillingRoutine(False)
        build.SetRoutineFinished(True)
    ConsoleLog("Killing Routine", "Finished Killing Routine", Py4GW.Console.MessageType.Info)
    yield from Routines.Yield.wait(1000)  # Wait a bit to ensure the enemies are dead
      
#region Events  
def _restart(bot: "Botting"):
    bot.Events.SetStuckRoutineEnabled(True)
    GLOBAL_CACHE.Player.SendChatCommand("resign")
    yield from Routines.Yield.wait(8000)
    fsm = bot.config.FSM
    fsm.jump_to_state_by_name("[H]Town Routines_1") 
    fsm.resume()                           
    yield  
    
def on_death(bot: "Botting"):
    ConsoleLog("Death detected", "Run Failed, Restarting...", Py4GW.Console.MessageType.Notice)
    ActionQueueManager().ResetAllQueues()
    fsm = bot.config.FSM
    fsm.pause()
    fsm.AddManagedCoroutine("OnDeath", _restart(bot))

previous_stuck_pos = (0,0)
def on_stuck(bot: Botting):
    global stuck_counter, stuck_able, previous_stuck_pos
    
    if not stuck_able:
        return
    
    current_pos = GLOBAL_CACHE.Player.GetXY()
    if current_pos != previous_stuck_pos:
        previous_stuck_pos = current_pos
        stuck_counter = 0
        return

    ConsoleLog("Stuck Detected", "Emitting stuck signal.", Py4GW.Console.MessageType.Info, False)
    build: BuildMgr = bot.config.build_handler
    stuck_counter += 1
    
    if isinstance(build, (SF_Ass_vaettir, SF_Mes_vaettir)):
        build.SetStuckSignal(stuck_counter)

    if stuck_counter >= 10:
        ConsoleLog("Stuck Detection", "Unrecoverable stuck detected, resetting.", Py4GW.Console.MessageType.Error)
        stuck_counter = 0
        ActionQueueManager().ResetAllQueues()
        fsm = bot.config.FSM
        fsm.pause()
        fsm.AddManagedCoroutine("OnStuck", _restart(bot))

bot.SetMainRoutine(create_bot_routine)

def configure():
    global bot
    bot.UI.draw_configure_window()
    
        
def main():

    bot.Update()

    projects_path = Py4GW.Console.get_projects_path()
    widgets_path = projects_path + "\\Widgets\\Config\\textures\\"
    bot.UI.draw_window(icon_path=widgets_path + "YAVB 2.0 mascot.png")


if __name__ == "__main__":
    main()
