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
    WIDGETS_TO_ENABLE: tuple[str, ...] = (
        "Titles",
        "Return to outpost on defeat",
        "ResurrectionScroll",
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

# =============================================================================
# region VANQUISH QUEUE DATA
# =============================================================================
class QueuedVanquish:
    """Stores all data needed to execute a single vanquish."""
    def __init__(self, region, map_name, display,
                 outpost_id, explorable_id,
                 outpost_path, vanquish_path,
                 transit_explorables, transit_paths):
        self.region = region
        self.map_name = map_name
        self.display = display
        self.outpost_id = outpost_id
        self.explorable_id = explorable_id
        self.outpost_path = outpost_path
        self.vanquish_path = vanquish_path
        self.transit_explorables = transit_explorables
        self.transit_paths = transit_paths

_queued_vanquishes: list[QueuedVanquish] = []
_queue_version: int = 0
_current_vq_index: int = 0
_start_combat_header_names: list[str] = []
# endregion

# =============================================================================
# region BOT ROUTINE
# =============================================================================
def bot_routine(bot: Botting) -> None:
    global _current_vq_index, _start_combat_header_names

    if not _queued_vanquishes:
        ConsoleLog(BotSettings.BOT_NAME, "No vanquishes queued!", Py4GW.Console.MessageType.Error)
        return

    # Events
    #condition = lambda: OnPartyWipe(bot)
    #bot.Events.OnPartyWipeCallback(condition)

    # Main header
    bot.States.AddHeader(BotSettings.BOT_NAME)  # header counter = 1
    bot.Templates.Multibox_Aggressive()
    bot.Multibox.ApplyWidgetPolicy(enable_widgets=BotSettings.WIDGETS_TO_ENABLE)

    # Pre-calculate header names.
    # Each VQ generates exactly 5 headers:
    #   1. VQ_{idx}_{name}
    #   2. Prepare For Farm (inside PrepareForFarm)
    #   3. Start Combat
    #   4. Vanquish Failed_{idx}
    #   5. Vanquish Completed_{idx}
    # The initial header (BOT_NAME) uses counter=1.
    # So Start Combat_{N} gets counter = 4 + N*5
    # And Completed_{N} gets counter = 6 + N*5
    _start_combat_header_names = []
    completed_header_names = []
    for vq_idx in range(len(_queued_vanquishes)):
        sc_counter = 4 + vq_idx * 5
        _start_combat_header_names.append(f"[H]Start Combat_{sc_counter}")
        comp_counter = 6 + vq_idx * 5
        completed_header_names.append(f"[H]Vanquish Completed_{vq_idx}_{comp_counter}")

    for vq_idx, vq in enumerate(_queued_vanquishes):
        is_last = (vq_idx == len(_queued_vanquishes) - 1)

        # -- Header for this vanquish --
        bot.States.AddHeader(f"VQ_{vq_idx}_{vq.map_name}")

        # -- Update current vanquish index --
        def _set_current_index(idx=vq_idx):
            global _current_vq_index
            _current_vq_index = idx
            yield
        bot.States.AddCustomState(lambda idx=vq_idx: _set_current_index(idx),
                                  f"SetVQIndex_{vq_idx}")

        # -- Prepare for farm --
        bot.Templates.Routines.PrepareForFarm(map_id_to_travel=vq.outpost_id)
        bot.Party.SetHardMode(True)
        bot.Items.Restock.ArmorOfSalvation()
        bot.Items.Restock.EssenceOfCelerity()
        bot.Items.Restock.GrailOfMight()
        bot.Items.Restock.WarSupplies()
        bot.Items.Restock.Honeycomb()

        # -- Travel to explorable --
        transit_count = len(vq.transit_explorables)
        if transit_count > 0:
            bot.Move.FollowPathAndExitMap(vq.outpost_path, target_map_id=vq.transit_explorables[0])
            for i in range(transit_count):
                bot.Move.FollowAutoPath(vq.transit_paths[i])
                next_map = vq.transit_explorables[i + 1] if i + 1 < transit_count else vq.explorable_id
                bot.Wait.ForMapToChange(next_map)
        else:
            bot.Move.FollowPathAndExitMap(vq.outpost_path, target_map_id=vq.explorable_id)

        # -- Vanquish Path (with Watchdog using pre-calculated header name) --
        bot.States.AddHeader("Start Combat")
        bot.UI.PrintMessageToConsole(BotSettings.BOT_NAME, f"Starting Vanquish: {vq.display}")
        target_header = completed_header_names[vq_idx]
        bot.States.AddManagedCoroutine("VanquishWatchdog",
            lambda h=target_header: VanquishWatchdog(bot, h))
        if vq.vanquish_path and isinstance(vq.vanquish_path[0], dict):
            for i, entry in enumerate(vq.vanquish_path):
                for key, value in entry.items():
                    if key == "bless":
                        bot.UI.PrintMessageToConsole(BotSettings.BOT_NAME, f"Taking Blessing.")
                        bot.Move.XY(*value)
                        bot.Wait.ForTime(1500)
                        bot.Move.XYAndInteractNPC(*value)
                        bot.Multibox.SendDialogToTarget(0x84)
                        bot.Multibox.SendDialogToTarget(0x85)
                    elif key == "junundu":
                        bot.UI.PrintMessageToConsole(BotSettings.BOT_NAME, f"Taking Junundu.")
                        bot.Move.XY(*value)
                        bot.Wait.ForTime(1500)
                        bot.Move.XYAndInteractGadget(*value)
                    elif key == "path":
                        bot.Move.FollowAutoPath(value)
        else:
            bot.Move.FollowAutoPath(vq.vanquish_path)
        bot.Wait.UntilOutOfCombat()

        # -- Reverse Path with Radar --
        bot.UI.PrintMessageToConsole(BotSettings.BOT_NAME, f"Starting Reverse Path with Radar.")
        bot.States.AddManagedCoroutine("Radar", lambda: Radar(bot))
        if vq.vanquish_path and isinstance(vq.vanquish_path[0], dict):
            reversed_list = []
            for entry in reversed(vq.vanquish_path):
                reversed_keys = list(entry.keys())[::-1]
                reversed_entry = {}
                for key in reversed_keys:
                    value = entry[key]
                    if isinstance(value, list):
                        reversed_entry[key] = value[::-1]
                    else:
                        reversed_entry[key] = value
                reversed_list.append(reversed_entry)

            for i, entry in enumerate(reversed_list):
                for key, value in entry.items():
                    if key == "bless":
                        bot.UI.PrintMessageToConsole(BotSettings.BOT_NAME, f"Taking Blessing.")
                        bot.Move.XY(*value)
                        bot.Wait.ForTime(1500)
                        bot.Move.XYAndInteractNPC(*value)
                        bot.Multibox.SendDialogToTarget(0x84)
                        bot.Multibox.SendDialogToTarget(0x85)
                    elif key == "junundu":
                        bot.UI.PrintMessageToConsole(BotSettings.BOT_NAME, f"Taking Junundu.")
                        bot.Move.XY(*value)
                        bot.Wait.ForTime(1500)
                        bot.Move.XYAndInteractGadget(*value)
                    elif key == "path":
                        bot.Move.FollowAutoPath(value)
        else:
            reversed_path = list(reversed(vq.vanquish_path))
            bot.Move.FollowAutoPath(reversed_path)
        bot.Wait.UntilOutOfCombat()

        # -- Vanquish FAILED (path ended, VQ not completed - stay in map & stop) --
        bot.States.AddHeader(f"Vanquish Failed_{vq_idx}")
        bot.States.RemoveManagedCoroutine("Radar")
        bot.States.RemoveManagedCoroutine("VanquishWatchdog")
        bot.UI.PrintMessageToConsole(BotSettings.BOT_NAME, f"Vanquish FAILED. Stopping bot. Report on Discord.")
        bot.States.AddCustomState(lambda: _stop_bot(), f"StopBot_{vq_idx}")

        # -- Vanquish Completed (VQ completed) --
        bot.States.AddHeader(f"Vanquish Completed_{vq_idx}")
        bot.States.RemoveManagedCoroutine("Radar")
        bot.States.RemoveManagedCoroutine("VanquishWatchdog")
        if is_last:
            # Last VQ: stay in map, no resign
            bot.UI.PrintMessageToConsole(BotSettings.BOT_NAME, f"Vanquish queue SUCCESS. Stopping bot. Staying in map.")
            #bot.States.AddCustomState(lambda: _stop_bot(), f"StopBotLastVQ_{vq_idx}")
        else:
            # Not last VQ: resign, go to outpost, continue to next VQ
            bot.UI.PrintMessageToConsole(BotSettings.BOT_NAME, f"Vanquish SUCCESS: {vq.display}. Moving to next Vanquish.")
            bot.Multibox.ResignParty()
            bot.Wait.ForTime(1000)
            bot.Wait.UntilOnOutpost()

    # All vanquishes finished
    bot.States.AddHeader("All Vanquishes Finished")
    #bot.UI.PrintMessageToConsole(BotSettings.BOT_NAME, "All vanquishes finished. Bot Stopped.")
    bot.States.AddCustomState(lambda: _stop_bot(), "StopBotFinal")

def _stop_bot():
    bot.Stop()
    yield
# endregion

# =============================================================================
# region COROUTINES
# =============================================================================
def Radar(bot: "Botting"):
    ConsoleLog("Radar", f"Radar coroutine started.", Py4GW.Console.MessageType.Debug, True)
    while True:
        player_x, player_y = Player.GetXY()
        enemy_array = AgentArray.GetEnemyArray()
        enemy_array = AgentArray.Filter.ByDistance(enemy_array, Player.GetXY(), 4000)
        enemy_array = AgentArray.Sort.ByDistance(enemy_array, (player_x, player_y))
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

def VanquishWatchdog(bot: "Botting", completed_header_name: str):
    while True:
        if Map.IsVanquishCompleted():
            ConsoleLog("VanquishWatchdog", f"Vanquish trigger activated. Jumping to: {completed_header_name}", Py4GW.Console.MessageType.Debug, True)
            bot.config.FSM.pause()
            bot.config.FSM.jump_to_state_by_name(completed_header_name)
            bot.config.FSM.resume()
            return
        yield from Routines.Yield.wait(500)
# endregion

# =============================================================================
# region EVENTS
# =============================================================================
def _on_party_wipe(bot: "Botting"):
    while Agent.IsDead(Player.GetAgentID()):
        yield from bot.Wait._coro_for_time(1000)
        if not Routines.Checks.Map.MapValid():
            bot.config.FSM.resume()
            return

    # Jump to the Start Combat header of the CURRENT vanquish
    target = _start_combat_header_names[_current_vq_index]
    ConsoleLog("on_party_wipe", f"Revived. Jumping to: {target}")
    bot.config.FSM.jump_to_state_by_name(target)
    bot.config.FSM.resume()

def OnPartyWipe(bot: "Botting"):
    ConsoleLog("on_party_wipe", "event triggered")
    fsm = bot.config.FSM
    fsm.pause()
    fsm.AddManagedCoroutine("OnWipe_OPD", lambda: _on_party_wipe(bot))
# endregion

# =============================================================================
# region DATA LOADING
# =============================================================================
def _load_transit_data(mod, map_selected):
    """Dynamically loads N transit_id / transit_path pairs from the map module."""
    ids = getattr(mod, f"{map_selected}_ids", {})
    transit_explorables = []
    transit_paths = []

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

def _load_vanquish_data(region_dir, map_name):
    """Load a map module and return a QueuedVanquish with all its data."""
    map_file = os.path.join(region_dir, map_name) + ".py"
    spec = importlib.util.spec_from_file_location(map_name, map_file)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    ids = getattr(mod, f"{map_name}_ids", {})
    outpost_id = ids.get("outpost_id", 0)
    explorable_id = ids.get("map_id", 0)
    outpost_path = getattr(mod, f"{map_name}_outpost_path", [])
    vanquish_path = getattr(mod, map_name, [])
    transit_explorables, transit_paths = _load_transit_data(mod, map_name)

    region_name = os.path.basename(region_dir)
    display = f"[{region_name}] {map_name}"

    return QueuedVanquish(
        region=region_name,
        map_name=map_name,
        display=display,
        outpost_id=outpost_id,
        explorable_id=explorable_id,
        outpost_path=outpost_path,
        vanquish_path=vanquish_path,
        transit_explorables=transit_explorables,
        transit_paths=transit_paths,
    )
# endregion

# =============================================================================
# region UI
# =============================================================================
region_index = 0
map_index = 0
_prev_queue_version: int = -1

def _draw_settings():
    global region_index, map_index, _queue_version, _prev_queue_version

    # --- Region combo ---
    PyImGui.text("Region & Map Selection")
    PyImGui.separator()
    regions = sorted([d for d in os.listdir(MAPS_DIR) if os.path.isdir(os.path.join(MAPS_DIR, d))])
    region_index = PyImGui.combo("##Region", region_index, regions)
    REGION_DIR = os.path.join(MAPS_DIR, regions[region_index])

    # --- Map combo ---
    maps = sorted([
        f[:-3] for f in os.listdir(REGION_DIR)
        if f.endswith(".py")
    ])
    map_index = PyImGui.combo("##Map", map_index, maps)
    if map_index >= len(maps):
        map_index = 0

    # --- Add Region / Add Map / Clear buttons ---
    if PyImGui.button("Add Region", 120, 25):
        for mn in maps:
            qv = _load_vanquish_data(REGION_DIR, mn)
            _queued_vanquishes.append(qv)
        _queue_version += 1

    PyImGui.same_line(0, 10)
    if PyImGui.button("Add Map", 120, 25):
        qv = _load_vanquish_data(REGION_DIR, maps[map_index])
        _queued_vanquishes.append(qv)
        _queue_version += 1

    PyImGui.same_line(0, 10)
    if PyImGui.button("Clear Maps", 120, 25):
        _queued_vanquishes.clear()
        _queue_version += 1

    # --- Queue display ---
    PyImGui.separator()
    PyImGui.text(f"Queued vanquishes: {len(_queued_vanquishes)}")
    to_remove = None
    for i, qv in enumerate(_queued_vanquishes):
        marker = " <-- CURRENT" if i == _current_vq_index and bot.config.initialized else ""
        PyImGui.text(f"  {i + 1}. {qv.display}{marker}")
        PyImGui.same_line(0, 10)
        if PyImGui.button(f"X##{i}", 20, 20):
            to_remove = i
    if to_remove is not None:
        _queued_vanquishes.pop(to_remove)
        _queue_version += 1

    # --- Rebuild FSM when queue changes ---
    if _queue_version != _prev_queue_version:
        bot.Stop()
        bot.config.FSM = FSM(BotSettings.BOT_NAME)
        bot.config.counters.clear_all()
        bot.config.initialized = False
        _prev_queue_version = _queue_version

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

    use_conset = bot.Properties.Get("armor_of_salvation", "active")
    use_conset = PyImGui.checkbox("Restock & use Conset", use_conset)
    bot.Properties.ApplyNow("armor_of_salvation", "active", use_conset)
    bot.Properties.ApplyNow("essence_of_celerity", "active", use_conset)
    bot.Properties.ApplyNow("grail_of_might", "active", use_conset)

    use_war_supplies = bot.Properties.Get("war_supplies", "active")
    use_war_supplies = PyImGui.checkbox("Restock & use War Supplies", use_war_supplies)
    bot.Properties.ApplyNow("war_supplies", "active", use_war_supplies)

    use_honeycomb = bot.Properties.Get("honeycomb", "active")
    use_honeycomb = PyImGui.checkbox("Restock & use Honeycomb", use_honeycomb)
    bot.Properties.ApplyNow("honeycomb", "active", use_honeycomb)
    #hc_restock_qty = bot.Properties.Get("honeycomb", "restock_quantity")
    #hc_restock_qty = PyImGui.input_int("Honeycomb Restock Quantity", hc_restock_qty)
    #bot.Properties.ApplyNow("honeycomb", "restock_quantity", hc_restock_qty)

def _draw_settings_debug():
    PyImGui.separator()
    PyImGui.text("DEBUG DATA")
    PyImGui.separator()
    PyImGui.text(f"_queue_version: {_queue_version}")
    PyImGui.text(f"_current_vq_index: {_current_vq_index}")
    PyImGui.text(f"_queued_vanquishes: {len(_queued_vanquishes)}")
    PyImGui.text(f"_start_combat_header_names: {_start_combat_header_names}")
    for i, qv in enumerate(_queued_vanquishes):
        marker = " <-- CURRENT" if i == _current_vq_index else ""
        PyImGui.text(f"  {i+1}. {qv.display} (outpost={qv.outpost_id}, expl={qv.explorable_id}){marker}")

def _draw_help():
    PyImGui.text("Developed by: Aura")
    PyImGui.text("Map credits to: aC, Aura, AH and Simfoniya")
# endregion

# =============================================================================
# region MAIN
# =============================================================================
bot.SetMainRoutine(bot_routine)

TEXTURE = os.path.join(Py4GW.Console.get_projects_path(), "Sources", "ApoSource", "textures", "VQ_Helmet.png")
bot.UI.override_draw_config(lambda: _draw_settings())
bot.UI.override_draw_help(lambda: _draw_help())

def main():
    bot.UI.draw_window(icon_path=TEXTURE)

    if _queued_vanquishes:
        bot.Update()

if __name__ == "__main__":
    main()
# endregion