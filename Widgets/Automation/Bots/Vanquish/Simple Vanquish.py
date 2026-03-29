from Py4GWCoreLib import Botting, Routines, GLOBAL_CACHE, ModelID, Map, Agent, ConsoleLog, Player, AgentArray, Map
from Py4GWCoreLib import *
import Py4GW
import os
import PyImGui
import importlib.util
projects_base_path = Py4GW.Console.get_projects_path()
ac_folder_path = os.path.join(projects_base_path, "Sources", "aC_Scripts")
from Sources.aC_Scripts.aC_api import *
MAPS_DIR = os.path.join(ac_folder_path,"PyQuishAI_maps")

MODULE_NAME = "Simple Vanquish"
MODULE_ICON = "Textures\\Module_Icons\\PyQuishAI.png"

class BotSettings:
    BOT_NAME = "Simple Vanquish"
    OUTPOST_TO_TRAVEL = 0
    EXPLORABLE_TO_TRAVEL = 0
    TRANSIT_EXPLORABLES = []       # lista escalable de transit map IDs
    TRANSIT_PATHS = []             # lista escalable de transit paths
    COORD_TO_EXIT_MAP = []
    VANQUISH_PATH = []
    WIDGETS_TO_ENABLE: tuple[str, ...] = (
        "Titles",
    )

bot = Botting(BotSettings.BOT_NAME,
              upkeep_armor_of_salvation_restock=5,
              upkeep_essence_of_celerity_restock=5,
              upkeep_grail_of_might_restock=5,
              upkeep_war_supplies_restock=5,
              upkeep_honeycomb_restock=25,
              upkeep_auto_loot_active=True,
              upkeep_armor_of_salvation_active=True,
              upkeep_essence_of_celerity_active=True,
              upkeep_grail_of_might_active=True,
              upkeep_war_supplies_active=True,
              upkeep_honeycomb_active=True,
              config_draw_path=True)

def bot_routine(bot: Botting) -> None:
    # Widgets    
    bot.Multibox.ApplyWidgetPolicy(enable_widgets=BotSettings.WIDGETS_TO_ENABLE)

    # events
    condition = lambda: OnPartyWipe(bot)
    bot.Events.OnPartyWipeCallback(condition)

    # Combat preparations
    bot.States.AddHeader(BotSettings.BOT_NAME) # 1
    bot.Templates.Multibox_Aggressive()
    bot.Templates.Routines.PrepareForFarm(map_id_to_travel=BotSettings.OUTPOST_TO_TRAVEL) # 2
    bot.Party.SetHardMode(True)
    PrepareForBattle(bot)

    # Travel
    bot.States.AddHeader("Travelling to Explorable") # 3
    transit_count = len(BotSettings.TRANSIT_EXPLORABLES)
    if transit_count > 0:
        # Exit to first transit explorable
        bot.Move.FollowPathAndExitMap(BotSettings.COORD_TO_EXIT_MAP, target_map_id=BotSettings.TRANSIT_EXPLORABLES[0])
        for i in range(transit_count):
            bot.Move.FollowAutoPath(BotSettings.TRANSIT_PATHS[i])
            # Determine which map we expect after following this transit path
            next_map = BotSettings.TRANSIT_EXPLORABLES[i + 1] if i + 1 < transit_count else BotSettings.EXPLORABLE_TO_TRAVEL
            bot.Wait.ForMapToChange(next_map)
    else:
        bot.Move.FollowPathAndExitMap(BotSettings.COORD_TO_EXIT_MAP, target_map_id=BotSettings.EXPLORABLE_TO_TRAVEL)

    # Vanquish Path
    bot.States.AddHeader("Vanquish Path") # 4
    bot.UI.PrintMessageToConsole(BotSettings.BOT_NAME, f"Starting Vanquish Path.")
    bot.States.AddManagedCoroutine("VanquishWatchdog", lambda: VanquishWatchdog(bot))
    if "bless" in BotSettings.VANQUISH_PATH[0]:
        for i, entry in enumerate(BotSettings.VANQUISH_PATH):
            for key, value in entry.items():
                if key == "bless":
                    bot.UI.PrintMessageToConsole(BotSettings.BOT_NAME, f"Taking Blessing.")
                    bot.Move.XY(*value)
                    bot.Wait.ForTime(1500)
                    bot.Move.XYAndInteractNPC(*value)
                    bot.Multibox.SendDialogToTarget(0x84) # eotn blessings
                    bot.Multibox.SendDialogToTarget(0x85) # NF blessings
                elif key == "junundu":
                    bot.UI.PrintMessageToConsole(BotSettings.BOT_NAME, f"Taking Junundu.")
                    bot.Move.XY(*value)
                    bot.Wait.ForTime(1500)
                    bot.Move.XYAndInteractGadget(*value)
                elif key == "path":
                    bot.Move.FollowAutoPath(value)
    else:
        bot.Move.FollowAutoPath(BotSettings.VANQUISH_PATH)
    bot.Wait.UntilOutOfCombat()
   
    # Reverse Path with Radar
    bot.States.AddHeader("Reverse Path with Radar") # 5
    bot.UI.PrintMessageToConsole(BotSettings.BOT_NAME, f"Starting Reverse Path with Radar.")
    bot.States.AddManagedCoroutine("Radar", lambda: Radar(bot))
    if "bless" in BotSettings.VANQUISH_PATH[0]:
        reversed_list = []
        for entry in reversed(BotSettings.VANQUISH_PATH):
            reversed_keys = list(entry.keys())[::-1]
            reversed_entry = {}
            for key in reversed_keys:
                value = entry[key]
                if isinstance(value, list):
                    reversed_entry[key] = value[::-1]
                else:
                        reversed_entry[key] = value
            reversed_list.append(reversed_entry)
        BotSettings.VANQUISH_PATH = reversed_list

        for i, entry in enumerate(BotSettings.VANQUISH_PATH):
            for key, value in entry.items():
                if key == "bless":
                    bot.UI.PrintMessageToConsole(BotSettings.BOT_NAME, f"Taking Blessing.")
                    bot.Move.XY(*value)
                    bot.Wait.ForTime(1500)
                    bot.Move.XYAndInteractNPC(*value)
                    bot.Multibox.SendDialogToTarget(0x84) # eotn blessings
                    bot.Multibox.SendDialogToTarget(0x85) # NF blessings
                elif key == "junundu":
                    bot.UI.PrintMessageToConsole(BotSettings.BOT_NAME, f"Taking Junundu.")
                    bot.Move.XY(*value)
                    bot.Wait.ForTime(1500)
                    bot.Move.XYAndInteractGadget(*value)
                elif key == "path":
                    bot.Move.FollowAutoPath(value)
    else:
        BotSettings.VANQUISH_PATH = list(reversed(BotSettings.VANQUISH_PATH))
        bot.Move.FollowAutoPath(BotSettings.VANQUISH_PATH)
    bot.Wait.UntilOutOfCombat()

    # Vanquish Finished
    bot.States.AddHeader("Vanquish Finished") # 6
    bot.UI.PrintMessageToConsole(BotSettings.BOT_NAME, f"Bot Stopped.")
    bot.States.AddCustomState(lambda: _stop_bot(), "StopBot")

def PrepareForBattle(bot: Botting):                  
    bot.Items.Restock.ArmorOfSalvation()
    bot.Items.Restock.EssenceOfCelerity()
    bot.Items.Restock.GrailOfMight()
    bot.Items.Restock.WarSupplies()
    bot.Items.Restock.Honeycomb()

def Radar(bot: "Botting"):
    ConsoleLog("Radar", f"Radar coroutine started.", Py4GW.Console.MessageType.Debug, True)
    while True:
        player_x, player_y = Player.GetXY()                
        enemy_array = AgentArray.GetEnemyArray()
        enemy_array = AgentArray.Filter.ByDistance(enemy_array, Player.GetXY(), 3000)
        enemy_array = AgentArray.Sort.ByDistance(enemy_array, (player_x,player_y))
        enemy_array = AgentArray.Filter.ByCondition(enemy_array, lambda a: Agent.IsAlive(a))
        closest_enemy = next(iter(enemy_array), 0)
       
        if closest_enemy != 0:
            closest_enemy_coord = Agent.GetXY(closest_enemy)
            ConsoleLog("Radar", f"Enemy detected at {closest_enemy_coord}.", Py4GW.Console.MessageType.Debug, True)
            bot.config.FSM.pause()
            Player.Move(closest_enemy_coord[0], closest_enemy_coord[1])
            yield from Routines.Yield.wait(500)
        else:
            bot.config.FSM.resume()
            yield from Routines.Yield.wait(500)
        yield from Routines.Yield.wait(500)

def VanquishWatchdog(bot: "Botting"):
    while True:
        if Map.IsVanquishCompleted():
            ConsoleLog("VanquishWatchdog", f"Vanquish trigger activated.", Py4GW.Console.MessageType.Debug, True)
            bot.config.FSM.pause()
            bot.config.FSM.jump_to_state_by_name("[H]Vanquish Finished_6")
            bot.config.FSM.resume()
            return
        yield from Routines.Yield.wait(500)

def _stop_bot():
    bot.Stop()
    yield
   
region_index = 0
map_index = 0
_farm_configured = [False]
prev_map_id = 0

def _load_transit_data(mod, map_selected):
    """
    Dynamically loads N transit_id / transit_path pairs from the map module.
    Looks for keys: transit_id, transit_id2, transit_id3, ... in the _ids dict
    and variables: {map_selected}_transit_path, _transit_path2, _transit_path3, ...
    Returns (transit_explorables_list, transit_paths_list)
    """
    ids = getattr(mod, f"{map_selected}_ids", {})
    transit_explorables = []
    transit_paths = []

    # The first transit uses the key "transit_id" and suffix "_transit_path"
    # Subsequent ones use "transit_id2", "transit_id3", ... and "_transit_path2", "_transit_path3", ...
    i = 1
    while True:
        key = "transit_id" if i == 1 else f"transit_id{i}"
        path_attr = f"{map_selected}_transit_path" if i == 1 else f"{map_selected}_transit_path{i}"

        transit_id = ids.get(key, 0)
        if not transit_id:
            break

        transit_explorables.append(transit_id)
        path_data = getattr(mod, path_attr, [(0, 0)])
        transit_paths.append(path_data)
        i += 1

    return transit_explorables, transit_paths

def _draw_settings():
    global region_index
    global map_index
    global prev_map_id    

    #Region combo
    PyImGui.text("Region & Map Selection")
    PyImGui.separator()
    regions = sorted([d for d in os.listdir(MAPS_DIR) if os.path.isdir(os.path.join(MAPS_DIR, d))])
    region_index = PyImGui.combo("##Region", region_index, regions)
    REGION_DIR = os.path.join(MAPS_DIR, regions[region_index])
 
    #Map combo
    maps = sorted([
        f[:-3] for f in os.listdir(REGION_DIR)
        if f.endswith(".py")
    ])
    map_index = PyImGui.combo("##Map", map_index, maps)
    if map_index >= len(maps):
        map_index = 0
    map_file = os.path.join(REGION_DIR, maps[map_index])+".py"
    map_selected = maps[map_index]

    spec = importlib.util.spec_from_file_location(map_selected, map_file)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    BotSettings.VANQUISH_PATH = getattr(mod, map_selected, [])  
    ids = getattr(mod, f"{map_selected}_ids", {})
    BotSettings.OUTPOST_TO_TRAVEL = ids.get("outpost_id")
    BotSettings.EXPLORABLE_TO_TRAVEL = ids.get("map_id")
    BotSettings.COORD_TO_EXIT_MAP = getattr(mod, f"{map_selected}_outpost_path", [])

    # Load N transit explorables and paths dynamically
    BotSettings.TRANSIT_EXPLORABLES, BotSettings.TRANSIT_PATHS = _load_transit_data(mod, map_selected)
   
    if prev_map_id != BotSettings.EXPLORABLE_TO_TRAVEL :
        bot.Stop()
        bot.config.FSM = FSM(BotSettings.BOT_NAME)
        bot.config.counters.clear_all()
        bot.config.initialized = False
        prev_map_id = BotSettings.EXPLORABLE_TO_TRAVEL
        _farm_configured[0] = True      

    PyImGui.separator()  
    if Map.GetMapID() != 857:
        if PyImGui.button("Travel to Embark Beach", 250, 30):
            Map.Travel(857)
    else:
        if PyImGui.button("Move to Vanquish signpost", 250, 30):  
            Player.Move(-428.00, -3439.00)

    _draw_settings_consumables()
    #_draw_settings_debug()

def _draw_settings_consumables():
    PyImGui.separator()
    PyImGui.text("Consumables Selection")
    PyImGui.separator()

    # Conset controls
    use_conset = bot.Properties.Get("armor_of_salvation", "active")
    use_conset = PyImGui.checkbox("Restock & use Conset", use_conset)
    bot.Properties.ApplyNow("armor_of_salvation", "active", use_conset)
    bot.Properties.ApplyNow("essence_of_celerity", "active", use_conset)
    bot.Properties.ApplyNow("grail_of_might", "active", use_conset)

    # War Supplies controls
    use_war_supplies = bot.Properties.Get("war_supplies", "active")
    use_war_supplies = PyImGui.checkbox("Restock & use War Supplies", use_war_supplies)
    bot.Properties.ApplyNow("war_supplies", "active", use_war_supplies)
                         
    # Honeycomb controls
    use_honeycomb = bot.Properties.Get("honeycomb", "active")
    use_honeycomb = PyImGui.checkbox("Restock & use Honeycomb", use_honeycomb)
    bot.Properties.ApplyNow("honeycomb", "active", use_honeycomb)
    hc_restock_qty = bot.Properties.Get("honeycomb", "restock_quantity")
    hc_restock_qty = PyImGui.input_int("Honeycomb Restock Quantity", hc_restock_qty)
    bot.Properties.ApplyNow("honeycomb", "restock_quantity", hc_restock_qty)

def _draw_settings_debug():
    PyImGui.separator()
    PyImGui.text("DEBUG DATA")
    PyImGui.separator()
    PyImGui.text(f"_farm_configured: {_farm_configured[0]}")
    PyImGui.text(f"BotSettings.OUTPOST_TO_TRAVEL: {BotSettings.OUTPOST_TO_TRAVEL}")
    PyImGui.text(f"BotSettings.EXPLORABLE_TO_TRAVEL: {BotSettings.EXPLORABLE_TO_TRAVEL}")
    PyImGui.text(f"BotSettings.COORD_TO_EXIT_MAP: {BotSettings.COORD_TO_EXIT_MAP[-1] if BotSettings.COORD_TO_EXIT_MAP else 'empty'}")
    PyImGui.text(f"BotSettings.VANQUISH_PATH: {BotSettings.VANQUISH_PATH[-1] if BotSettings.VANQUISH_PATH else 'empty'}")
    PyImGui.text(f"Transit count: {len(BotSettings.TRANSIT_EXPLORABLES)}")
    for i in range(len(BotSettings.TRANSIT_EXPLORABLES)):
        suffix = "" if i == 0 else str(i + 1)
        tid = BotSettings.TRANSIT_EXPLORABLES[i]
        tpath = BotSettings.TRANSIT_PATHS[i] if i < len(BotSettings.TRANSIT_PATHS) else []
        PyImGui.text(f"  TRANSIT_EXPLORABLE{suffix}: {tid}")
        PyImGui.text(f"  TRANSIT_PATH{suffix}[-1]: {tpath[-1] if tpath else 'empty'}")

def _draw_help():
    PyImGui.text("Developed by: Aura")
    PyImGui.text("Map credits to: aC, Aura, AH and Simfoniya")
             
def _on_party_wipe(bot: "Botting"):
    while Agent.IsDead(Player.GetAgentID()):
        yield from bot.Wait._coro_for_time(1000)
        if not Routines.Checks.Map.MapValid():
            # Map invalid → release FSM and exit
            bot.config.FSM.resume()
            return

    # Player revived on same map → jump to recovery step
    bot.States.JumpToStepName("[H]Start Combat_4")
    bot.config.FSM.resume()
   
def OnPartyWipe(bot: "Botting"):
    ConsoleLog("on_party_wipe", "event triggered")
    fsm = bot.config.FSM
    fsm.pause()
    fsm.AddManagedCoroutine("OnWipe_OPD", lambda: _on_party_wipe(bot))

bot.SetMainRoutine(bot_routine)

TEXTURE = os.path.join(Py4GW.Console.get_projects_path(), "Sources", "ApoSource", "textures", "VQ_Helmet.png")
#Override UI window
bot.UI.override_draw_config(lambda: _draw_settings())
bot.UI.override_draw_help(lambda: _draw_help())

def main():
    bot.UI.draw_window(icon_path=TEXTURE)

    if  _farm_configured[0]:
        bot.Update()

if __name__ == "__main__":
    main()
