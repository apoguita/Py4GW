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
              upkeep_honeycomb_restock=25,
              upkeep_auto_loot_active=True,
              upkeep_armor_of_salvation_active=True,
              upkeep_essence_of_celerity_active=True,
              upkeep_grail_of_might_active=True,
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
_vq_header_names: list[str] = []
_section_headers: dict = {}
_current_section_header: tuple = ("", 0.0, 0.0)
_restock_pcons: bool = True
_restock_res_scroll: bool = True
_loop_queue: bool = False
_loop_count: int = 0
# endregion

# =============================================================================
# region HELPERS
# =============================================================================
def _register_path(bot, path, header_name=None):
    """Register FSM states for a path (simple or complex with bless/gadget/etc.).

    Supports three path formats:
      1. Simple path: [(x1,y1), (x2,y2), ...]
      2. Dict-based complex path (no duplicate keys per segment):
         [{"bless": (x,y), "path": [...]}, {"path": [...]}]
      3. Tuple-list complex path (allows duplicate keys per segment):
         [[("path", [...]), ("bless", (x,y)), ("path", [...])], ...]
    """
    if header_name:
        bot.States.AddHeader(header_name)

    if not path:
        return

    first = path[0]

    if isinstance(first, dict):
        for entry in path:
            for key, value in entry.items():
                _handle_keyword(bot, key, value)

    elif isinstance(first, list):
        for segment in path:
            for key, value in segment:
                _handle_keyword(bot, key, value)

    else:
        bot.Move.FollowAutoPath(path)


def _handle_keyword(bot, key, value):
    """Process a single keyword action from a complex path segment."""
    if key == "bless":
        bot.UI.PrintMessageToConsole(BotSettings.BOT_NAME, f"Interacting with Blessing.")
        bot.Move.XY(*value)
        bot.Wait.ForTime(1500)
        bot.Move.XYAndInteractNPC(*value)
        bot.Multibox.SendDialogToTarget(0x84)
        bot.Multibox.SendDialogToTarget(0x85)
    elif key == "gadget":
        bot.UI.PrintMessageToConsole(BotSettings.BOT_NAME, f"Interacting with Gadget.")
        bot.Move.XY(*value)
        bot.Wait.ForTime(1500)
        bot.Move.XYAndInteractGadget(*value)
    elif key == "npc":
        bot.UI.PrintMessageToConsole(BotSettings.BOT_NAME, f"Interacting with NPC.")
        bot.Move.XY(*value)
        bot.Wait.ForTime(1500)
        bot.Move.XYAndInteractNPC(*value)
    elif key == "dialog":
        bot.UI.PrintMessageToConsole(BotSettings.BOT_NAME, f"Sending dialog target.")
        bot.Wait.ForTime(500)
        bot.Multibox.SendDialogToTarget(value)
    elif key == "wait":
        bot.UI.PrintMessageToConsole(BotSettings.BOT_NAME, f"Waiting...")
        bot.Wait.ForTime(value)
    elif key == "map":
        bot.Wait.ForMapToChange(value)
    elif key == "path":
        bot.Move.FollowAutoPath(value)


def _get_first_path_coord(path):
    """Extract the first (x,y) coordinate from any path format."""
    if not path:
        return (0.0, 0.0)
    first = path[0]
    if isinstance(first, dict):
        for entry in path:
            for key, value in entry.items():
                if key == "path" and value:
                    return (value[0][0], value[0][1])
        return (0.0, 0.0)
    elif isinstance(first, list):
        for segment in path:
            for key, value in segment:
                if key == "path" and value:
                    return (value[0][0], value[0][1])
        return (0.0, 0.0)
    else:
        return (first[0], first[1])


def _set_section_header(header_name, first_x, first_y):
    """Update the current section header and first waypoint for OnWipe recovery."""
    global _current_section_header
    _current_section_header = (header_name, first_x, first_y)
    yield


def _build_reversed_path(vanquish_path):
    """Build a reversed version of vanquish_path, handling both simple and dict formats."""
    if not vanquish_path:
        return []
    first = vanquish_path[0]
    if isinstance(first, dict):
        reversed_list = []
        for entry in reversed(vanquish_path):
            reversed_keys = list(entry.keys())[::-1]
            reversed_entry = {}
            for key in reversed_keys:
                value = entry[key]
                if isinstance(value, list):
                    reversed_entry[key] = value[::-1]
                else:
                    reversed_entry[key] = value
            reversed_list.append(reversed_entry)
        return reversed_list
    elif isinstance(first, list):
        reversed_list = []
        for segment in reversed(vanquish_path):
            reversed_segment = []
            for key, value in reversed(segment):
                if isinstance(value, list):
                    reversed_segment.append((key, value[::-1]))
                else:
                    reversed_segment.append((key, value))
            reversed_list.append(reversed_segment)
        return reversed_list
    else:
        return list(reversed(vanquish_path))
# endregion

# =============================================================================
# region BOT ROUTINE
# =============================================================================
def Radar(bot: "Botting", radar_range: int = 3500):
    ConsoleLog("Radar", f"Radar coroutine started (range={radar_range}).", Py4GW.Console.MessageType.Debug, True)
    while True:
        player_x, player_y = Player.GetXY()
        enemy_array = AgentArray.GetEnemyArray()
        enemy_array = AgentArray.Filter.ByDistance(enemy_array, Player.GetXY(), radar_range)
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


def bot_routine(bot: Botting) -> None:
    global _current_vq_index, _vq_header_names

    if not _queued_vanquishes:
        ConsoleLog(BotSettings.BOT_NAME, "No vanquishes queued!", Py4GW.Console.MessageType.Error)
        return

    # Events
    condition = lambda: OnPartyWipe(bot)
    bot.Events.OnPartyWipeCallback(condition)

    # Main header
    bot.States.AddHeader(BotSettings.BOT_NAME)  # header counter = 1
    bot.Templates.Multibox_Aggressive()
    bot.Multibox.ApplyWidgetPolicy(enable_widgets=BotSettings.WIDGETS_TO_ENABLE)

    # -------------------------------------------------------------------------
    # Pre-calculate header names for OnWipe jumps.
    # Headers per VQ (variable):
    #   1. VQ_{idx}_{name}
    #   2. Prepare For Farm (inside PrepareForFarm)
    #   N. Transit_{idx}_0 ... Transit_{idx}_N (if transits)
    #   M. VanquishPath_{idx}
    #   M+1. ReversePath3500_{idx}
    #   M+2. ReversePath5000_{idx}
    #   M+3. Vanquish Failed_{idx}
    #   M+4. Vanquish Completed_{idx}
    # -------------------------------------------------------------------------
    _vq_header_names = []
    _completed_header_names = []
    _section_headers.clear()
    header_counter = 1  # main header

    for vq_idx, vq in enumerate(_queued_vanquishes):
        header_counter += 1  # VQ_{idx}_{name}
        _vq_header_names.append(f"[H]VQ_{vq_idx}_{vq.map_name}_{header_counter}")
        header_counter += 1  # Prepare For Farm

        transit_count = len(vq.transit_explorables)
        sections = []

        # Transit headers
        if transit_count > 0:
            for t_i in range(transit_count):
                header_counter += 1
                sections.append(f"[H]Transit_{vq_idx}_{t_i}_{header_counter}")

        # VanquishPath header
        header_counter += 1
        sections.append(f"[H]VanquishPath_{vq_idx}_{header_counter}")

        # ReversePath3500 header
        header_counter += 1
        sections.append(f"[H]ReversePath3500_{vq_idx}_{header_counter}")

        # ReversePath5000 header
        header_counter += 1
        sections.append(f"[H]ReversePath5000_{vq_idx}_{header_counter}")

        _section_headers[vq_idx] = sections

        # Vanquish Failed
        header_counter += 1

        # Vanquish Completed
        header_counter += 1
        _completed_header_names.append(f"[H]Vanquish Completed_{vq_idx}_{header_counter}")

    # Pre-calculate first VQ header for looping
    first_vq_header = _vq_header_names[0]

    # -------------------------------------------------------------------------
    # Build FSM states for each vanquish
    # -------------------------------------------------------------------------
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
        bot.Items.Restock.Honeycomb()
        if _restock_pcons:
            bot.Multibox.RestockAllPcons(10)
        if _restock_res_scroll:
            bot.Multibox.RestockResurrectionScroll(25)

        # -- Travel to explorable --
        transit_count = len(vq.transit_explorables)
        section_idx = 0  # track position within _section_headers[vq_idx]

        if transit_count > 0:
            bot.Move.FollowPathAndExitMap(vq.outpost_path, target_map_id=vq.transit_explorables[0])
            for i in range(transit_count):
                next_map = vq.transit_explorables[i + 1] if i + 1 < transit_count else vq.explorable_id
                t_coord = _get_first_path_coord(vq.transit_paths[i])
                bot.States.AddCustomState(lambda vi=vq_idx, si=section_idx, tc=t_coord: _set_section_header(_section_headers[vi][si], tc[0], tc[1]),
                                          f"SetSection_Transit_{vq_idx}_{i}")
                if _restock_pcons:
                        bot.Multibox.UsePcons()
                _register_path(bot, vq.transit_paths[i], header_name=f"Transit_{vq_idx}_{i}")
                bot.Wait.ForMapToChange(next_map)
                section_idx += 1
        else:
            bot.Move.FollowPathAndExitMap(vq.outpost_path, target_map_id=vq.explorable_id)

        # -- Vanquish Path --
        vp_coord = _get_first_path_coord(vq.vanquish_path)
        bot.States.AddCustomState(lambda vi=vq_idx, si=section_idx, vc=vp_coord: _set_section_header(_section_headers[vi][si], vc[0], vc[1]),
                                  f"SetSection_VanquishPath_{vq_idx}")
        if _restock_pcons:
            bot.Multibox.UsePcons()
        _register_path(bot, vq.vanquish_path, header_name=f"VanquishPath_{vq_idx}")
        bot.UI.PrintMessageToConsole(BotSettings.BOT_NAME, f"Starting Vanquish: {vq.display}")
        target_header = _completed_header_names[vq_idx]
        bot.States.AddManagedCoroutine("VanquishWatchdog",
            lambda h=target_header: VanquishWatchdog(bot, h))
        bot.Wait.UntilOutOfCombat()
        section_idx += 1

        # -- Reverse Path with Radar (range=3500) --
        reversed_path = _build_reversed_path(vq.vanquish_path)
        rp_coord = _get_first_path_coord(reversed_path)
        bot.States.AddCustomState(lambda vi=vq_idx, si=section_idx, rc=rp_coord: _set_section_header(_section_headers[vi][si], rc[0], rc[1]),
                                  f"SetSection_ReversePath3500_{vq_idx}")
        bot.States.AddHeader(f"ReversePath3500_{vq_idx}")
        bot.UI.PrintMessageToConsole(BotSettings.BOT_NAME, f"Starting Reverse Path with Radar (range=3500).")
        bot.States.AddManagedCoroutine("Radar", lambda: Radar(bot, radar_range=3500))
        _register_path(bot, reversed_path)
        bot.Wait.UntilOutOfCombat()
        bot.States.RemoveManagedCoroutine("Radar")
        section_idx += 1

        # -- Reverse Path with Radar (range=5000) --
        rp5_coord = _get_first_path_coord(reversed_path)  # same reversed path
        bot.States.AddCustomState(lambda vi=vq_idx, si=section_idx, rc=rp5_coord: _set_section_header(_section_headers[vi][si], rc[0], rc[1]),
                                  f"SetSection_ReversePath5000_{vq_idx}")
        bot.States.AddHeader(f"ReversePath5000_{vq_idx}")
        bot.UI.PrintMessageToConsole(BotSettings.BOT_NAME, f"Starting Reverse Path with Extended Radar (range=5000).")
        bot.States.AddManagedCoroutine("Radar", lambda: Radar(bot, radar_range=5000))
        _register_path(bot, reversed_path)
        bot.Wait.UntilOutOfCombat()
        section_idx += 1

        # -- Vanquish FAILED --
        bot.States.AddHeader(f"Vanquish Failed_{vq_idx}")
        bot.States.RemoveManagedCoroutine("Radar")
        bot.States.RemoveManagedCoroutine("VanquishWatchdog")
        bot.UI.PrintMessageToConsole(BotSettings.BOT_NAME, f"Vanquish FAILED. Stopping bot. Report on Discord.")
        bot.States.AddCustomState(lambda: _stop_bot(), f"StopBot_{vq_idx}")

        # -- Vanquish Completed --
        bot.States.AddHeader(f"Vanquish Completed_{vq_idx}")
        bot.States.RemoveManagedCoroutine("Radar")
        bot.States.RemoveManagedCoroutine("VanquishWatchdog")
        if is_last:
            bot.UI.PrintMessageToConsole(BotSettings.BOT_NAME, f"Vanquish queue SUCCESS: {vq.display}.")
            bot.States.AddCustomState(lambda: _check_loop_or_stop(bot),
                                      f"CheckLoopOrStop")
            bot.Multibox.ResignParty()
            bot.Wait.ForTime(1000)
            bot.Wait.UntilOnOutpost()
            bot.States.AddCustomState(lambda h=first_vq_header: _do_loop_jump(bot, h),
                                      f"DoLoopJump")
        else:
            bot.UI.PrintMessageToConsole(BotSettings.BOT_NAME, f"Vanquish SUCCESS: {vq.display}. Moving to next Vanquish.")
            bot.Multibox.ResignParty()
            bot.Wait.ForTime(1000)
            bot.Wait.UntilOnOutpost()

    # All vanquishes finished
    bot.States.AddHeader("All Vanquishes Finished")
    bot.States.AddCustomState(lambda: _stop_bot(), "StopBotFinal")

def _stop_bot():
    bot.Stop()
    yield

def _check_loop_or_stop(bot: "Botting"):
    """CustomState coroutine: if loop OFF → stop bot. If loop ON → continue to resign states."""
    if _loop_queue:
        ConsoleLog(BotSettings.BOT_NAME,
                   f"Loop Queue enabled. Resigning party for next loop.",
                   Py4GW.Console.MessageType.Info, True)
    else:
        ConsoleLog(BotSettings.BOT_NAME,
                   "Loop Queue disabled. Staying in map. Stopping bot.",
                   Py4GW.Console.MessageType.Info, True)
        bot.Stop()
    yield


def _do_loop_jump(bot: "Botting", first_vq_header: str):
    """CustomState coroutine: increment loop count and jump back to first vanquish."""
    global _loop_count
    _loop_count += 1
    ConsoleLog(BotSettings.BOT_NAME,
               f"Back at outpost. Starting loop #{_loop_count}. Jumping to: {first_vq_header}",
               Py4GW.Console.MessageType.Info, True)
    bot.config.FSM.jump_to_state_by_name(first_vq_header)
    yield
# endregion

# =============================================================================
# region EVENTS
# =============================================================================
def _on_party_wipe(bot: "Botting"):
    from Py4GWCoreLib.Pathing import AutoPathing

    # Wait until player is no longer dead
    while Agent.IsDead(Player.GetAgentID()):
        yield from bot.Wait._coro_for_time(1000)

    # Wait for map to stabilize (loading screen after defeat/shrine teleport)
    yield from Routines.Yield.wait(2000)
    while not Routines.Checks.Map.MapValid():
        yield from Routines.Yield.wait(500)

    # Check if we ended up in outpost (defeat at -60% DP, or widget)
    if Map.IsOutpost():
        target = _vq_header_names[_current_vq_index]
        ConsoleLog("on_party_wipe",
                   f"Resurrected in outpost. Re-executing vanquish. Jumping to: {target}")
        bot.config.FSM.jump_to_state_by_name(target)
        bot.config.FSM.resume()
        return

    # Still in explorable (shrine resurrection) — navigate to section start
    section_header, goal_x, goal_y = _current_section_header
    shrine_x, shrine_y = Player.GetXY()
    ConsoleLog("on_party_wipe",
               f"Revived at shrine ({shrine_x:.0f}, {shrine_y:.0f}). "
               f"Navigating to section start ({goal_x:.0f}, {goal_y:.0f})")

    start = (shrine_x, shrine_y, 0)
    goal = (goal_x, goal_y, 0)
    path_back = yield from AutoPathing().get_path(start, goal)
    if path_back:
        yield from Routines.Yield.Movement.FollowPath(
            path_points=[(p[0], p[1]) for p in path_back],
            tolerance=200,
            custom_pause_fn=bot.config.pause_on_danger_fn,
        )

    # Jump to the current section header to re-execute the section path
    ConsoleLog("on_party_wipe",
               f"Jumping to section: {section_header}")
    bot.config.FSM.jump_to_state_by_name(section_header)
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
    """Dynamically loads N transit_id / transit_path pairs from the map module.

    Supports two modes:
      1. Standard: transit_id keys in _ids dict paired with transit_path attributes.
      2. Path-only: no transit_id keys, but transit_path attributes exist.
    """
    ids = getattr(mod, f"{map_selected}_ids", {})
    transit_explorables = []
    transit_paths = []

    i = 1
    while True:
        key = "transit_id" if i == 1 else f"transit_id{i}"
        path_attr = f"{map_selected}_transit_path" if i == 1 else f"{map_selected}_transit_path{i}"

        transit_id = ids.get(key, 0)
        path_data = getattr(mod, path_attr, None)

        if not transit_id and path_data is None:
            break

        if transit_id:
            transit_explorables.append(transit_id)
        else:
            transit_explorables.append(0)

        if path_data is not None:
            transit_paths.append(path_data)
        else:
            transit_paths.append([(0, 0)])

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
    global _loop_queue, _restock_pcons, _restock_res_scroll

    PyImGui.separator()
    PyImGui.text("Consumables Selection")
    PyImGui.separator()

    use_conset = bot.Properties.Get("armor_of_salvation", "active")
    use_conset = PyImGui.checkbox("Restock & use Conset", use_conset)
    bot.Properties.ApplyNow("armor_of_salvation", "active", use_conset)
    bot.Properties.ApplyNow("essence_of_celerity", "active", use_conset)
    bot.Properties.ApplyNow("grail_of_might", "active", use_conset)
    _restock_pcons = PyImGui.checkbox("Restock & use Pcons (Multibox)", _restock_pcons)

    use_honeycomb = bot.Properties.Get("honeycomb", "active")
    use_honeycomb = PyImGui.checkbox("Restock & use Honeycomb", use_honeycomb)
    bot.Properties.ApplyNow("honeycomb", "active", use_honeycomb)

    _restock_res_scroll = PyImGui.checkbox("Restock Resurrection Scroll (Multibox)", _restock_res_scroll)

    PyImGui.separator()
    _loop_queue = PyImGui.checkbox("Loop Queue", _loop_queue)
    if _loop_queue and _loop_count > 0:
        PyImGui.same_line(0, 10)
        PyImGui.text(f"(loop #{_loop_count})")

def _draw_settings_debug():
    PyImGui.separator()
    PyImGui.text("DEBUG DATA")
    PyImGui.separator()
    PyImGui.text(f"_queue_version: {_queue_version}")
    PyImGui.text(f"_current_vq_index: {_current_vq_index}")
    PyImGui.text(f"_queued_vanquishes: {len(_queued_vanquishes)}")
    PyImGui.text(f"_vq_header_names: {_vq_header_names}")
    PyImGui.text(f"_section_headers: {_section_headers}")
    PyImGui.text(f"_current_section_header: {_current_section_header}")
    PyImGui.text(f"_loop_queue: {_loop_queue}")
    PyImGui.text(f"_loop_count: {_loop_count}")

def _draw_help():
    PyImGui.text("Developed by: Aura")
    PyImGui.text("Vanquish paths credits to: aC, Aura, AH & Simfoniya")
# endregion

# =============================================================================
# region MAIN
# =============================================================================
bot.SetMainRoutine(bot_routine)

TEXTURE = os.path.join(Py4GW.Console.get_projects_path(), "Sources", "ApoSource", "textures", "VQ_Helmet.png")
bot.UI.override_draw_config(lambda: _draw_settings())
bot.UI.override_draw_help(lambda: _draw_help())

def main():
    if not Routines.Checks.Map.MapValid():
        return
    
    bot.UI.draw_window(icon_path=TEXTURE)

    if _queued_vanquishes:
        bot.Update()

if __name__ == "__main__":
    main()
# endregion
