from Py4GWCoreLib import Botting, Routines, GLOBAL_CACHE, ModelID, Map, Agent, ConsoleLog, Player, AgentArray, Map
from Py4GWCoreLib import *
import Py4GW
import os
import PyImGui
import importlib.util
import time
import random
from Py4GWCoreLib.enums_src.Region_enums import District

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
              upkeep_honeycomb_restock=25,
              upkeep_auto_loot_active=True,
              upkeep_honeycomb_active=True,
              config_draw_path=True)

_RANDOM_DISTRICTS = [
    District.EuropeItalian.value,
    District.EuropeSpanish.value,
    District.EuropePolish.value,
    District.EuropeRussian.value,
    District.AsiaKorean.value,
    District.AsiaChinese.value,
    District.AsiaJapanese.value,
]

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
_restock_conset: bool = True
_restock_pcons: bool = True
_restock_res_scroll: bool = True
_restock_use_summoning_stones: bool = True
_loop_queue: bool = False
_loop_count: int = 0
_reverse_detections: dict = {}  # {map_name: {"reverse1": [(x,y)], "reverse2": [(x,y)]}}
_vq_timers: dict = {}        # {vq_idx: {"start": float, "elapsed": float, "done": bool}}
_bot_start_time: float = 0.0  # time.time() when first VQ starts
_bot_total_elapsed: float = 0.0  # frozen total when bot stops
_prev_build_settings: tuple = (True, True, True, True, True, False, 2500, 3500, 5000)
_aggro_range_forward: int = 2500
_aggro_range_reverse1: int = 3500
_aggro_range_reverse2: int = 5000
# endregion

# =============================================================================
# region HELPERS

def _format_time(seconds: float) -> str:
    """Format seconds as 00h 00m 00s."""
    s = int(seconds)
    h = s // 3600
    m = (s % 3600) // 60
    sec = s % 60
    return f"{h:02d}h {m:02d}m {sec:02d}s"

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
        bot.Multibox.SendDialogToTarget(0x84) # EOTN Blessing
        bot.Multibox.SendDialogToTarget(0x85) # NF Blessing
        bot.Multibox.SendDialogToTarget(0x86) # Factions Blessing
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
    elif key == "dropbundle":
        bot.UI.PrintMessageToConsole(BotSettings.BOT_NAME, f"Dropping bundle.")
        bot.UI.Keybinds.DropBundle()
    elif key == "interacttarget":
        bot.UI.PrintMessageToConsole(BotSettings.BOT_NAME, f"Interacting with target {value}.")
        Player.ChangeTarget(value)
        bot.Wait.ForTime(500)
        bot.Multibox.InteractWithTarget()
        bot.Wait.ForTime(5000)
    elif key == "followmodel":
        model_id, follow_range, time_ms = value
        _start = [None]
        def _timeout(t=time_ms):
            if _start[0] is None:
                _start[0] = time.time()
            return (time.time() - _start[0]) * 1000 >= t
        bot.UI.PrintMessageToConsole(BotSettings.BOT_NAME, f"Following model {model_id} for {time_ms}ms.")
        bot.Move.FollowModel(model_id, follow_range, _timeout)
    elif key == "path":
        bot.Move.FollowAutoPath(value)


def _register_aggro_path(bot, path, header_name=None, detection_radius=2500.0, clear_radius=2500.0, on_enemy_detected=None):
    """Register FSM states for an aggro path (movement + enemy engagement).

    Supports the same 3 formats as _register_path. For dict/tuple segments
    the keyword 'path' is replaced by FollowAutoPathAggro.
    If on_enemy_detected is provided, it is passed to FollowAutoPathAggro.
    """
    if header_name:
        bot.States.AddHeader(header_name)

    if not path:
        return

    first = path[0]

    def _handle_aggro_keyword(key, value):
        if key == "path":
            bot.Move.FollowAutoPathAggro(value, detection_radius, clear_radius, on_enemy_detected=on_enemy_detected)
        else:
            _handle_keyword(bot, key, value)

    if isinstance(first, dict):
        for entry in path:
            for key, value in entry.items():
                _handle_aggro_keyword(key, value)

    elif isinstance(first, list):
        for segment in path:
            for key, value in segment:
                _handle_aggro_keyword(key, value)

    else:
        bot.Move.FollowAutoPathAggro(path, detection_radius, clear_radius, on_enemy_detected=on_enemy_detected)


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


def VanquishWatchdog(bot: "Botting", completed_header_name: str):
    ConsoleLog("VanquishWatchdog", "Vanquish Watchdog Coroutine Started", Py4GW.Console.MessageType.Debug, True)
    while True:
        if Map.IsVanquishCompleted():
            ConsoleLog("VanquishWatchdog", f"Vanquish trigger activated. Jumping to: {completed_header_name}", Py4GW.Console.MessageType.Debug, True)
            bot.Events.OnPartyWipeCallback(None)
            # Freeze timer for completed vanquish
            if _current_vq_index in _vq_timers and not _vq_timers[_current_vq_index]["done"]:
                _vq_timers[_current_vq_index]["elapsed"] = time.time() - _vq_timers[_current_vq_index]["start"]
                _vq_timers[_current_vq_index]["done"] = True
            bot.config.FSM.pause()
            # Reset current state to detach any SelfManagedYieldState coroutine
            if bot.config.FSM.current_state:
                bot.config.FSM.current_state.reset()
            bot.config.FSM.RemoveManagedCoroutine("ConsetUpkeep")
            bot.config.FSM.RemoveManagedCoroutine("PconsUpkeep")
            bot.config.FSM.jump_to_state_by_name(completed_header_name)
            bot.config.FSM.resume()
            return
        yield from Routines.Yield.wait(500)


def bot_routine(bot: Botting) -> None:
    global _current_vq_index, _vq_header_names

    bot.config.counters.clear_all()

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
    # Headers per VQ:
    #   1. VQ_{idx}_{name}
    #   2. Prepare For Farm (inside PrepareForFarm)
    #   N. Transit_{idx}_0 ... Transit_{idx}_N (if transits)
    #   M. VanquishPath_{idx}
    #   M+1. ReverseAggro1_{idx}
    #   M+2. ReverseAggro2_{idx}
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

        # ReverseAggro1 header
        header_counter += 1
        sections.append(f"[H]ReverseAggro1_{vq_idx}_{header_counter}")

        # ReverseAggro2 header
        header_counter += 1
        sections.append(f"[H]ReverseAggro2_{vq_idx}_{header_counter}")

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
            global _current_vq_index, _vq_timers, _bot_start_time, _bot_total_elapsed
            _current_vq_index = idx
            _vq_timers[idx] = {"start": time.time(), "elapsed": 0.0, "done": False}
            if _bot_start_time == 0.0:
                _bot_start_time = time.time()
                _bot_total_elapsed = 0.0
            bot.Events.OnPartyWipeCallback(lambda: OnPartyWipe(bot))
            yield
        bot.States.AddCustomState(lambda idx=vq_idx: _set_current_index(idx), f"SetVQIndex_{vq_idx}")

        # -- Prepare for farm --
        bot.Templates.Routines.PrepareForFarm(map_id_to_travel=vq.outpost_id)
        bot.Party.SetHardMode(True)
        bot.Items.Restock.Honeycomb()
        if _restock_conset:
            bot.Multibox.RestockConset(10)
        if _restock_pcons:
            bot.Multibox.RestockAllPcons(10)
        if _restock_res_scroll:
            bot.Multibox.RestockResurrectionScroll(25)
        if _restock_use_summoning_stones:
            bot.Multibox.RestockSummoningStones(10)
        bot.Multibox.WithdrawGold()

        # -- Travel to explorable --
        has_outpost_path = bool(vq.outpost_path)
        has_explorable = bool(vq.explorable_id)
        transit_count = len(vq.transit_explorables)
        section_idx = 0  # track position within _section_headers[vq_idx]

        if has_outpost_path and has_explorable:
            if transit_count > 0:
                bot.Move.FollowPathAndExitMap(vq.outpost_path, target_map_id=vq.transit_explorables[0])
                for i in range(transit_count):
                    next_map = vq.transit_explorables[i + 1] if i + 1 < transit_count else vq.explorable_id
                    t_coord = _get_first_path_coord(vq.transit_paths[i])
                    bot.States.AddCustomState(lambda vi=vq_idx, si=section_idx, tc=t_coord: _set_section_header(_section_headers[vi][si], tc[0], tc[1]), f"SetSection_Transit_{vq_idx}_{i}")
                    bot.UI.PrintMessageToConsole(BotSettings.BOT_NAME, f"Navigating Transit path.")
                    bot.config.FSM.RemoveManagedCoroutine("ConsetUpkeep")
                    bot.config.FSM.RemoveManagedCoroutine("PconsUpkeep")
                    if _restock_conset:
                        bot.States.AddManagedCoroutine("ConsetUpkeep", lambda: _conset_upkeep(bot))
                    if _restock_pcons:
                        bot.States.AddManagedCoroutine("PconsUpkeep", lambda: _pcons_upkeep(bot))
                    _register_path(bot, vq.transit_paths[i], header_name=f"Transit_{vq_idx}_{i}")
                    bot.Wait.ForMapToChange(next_map)
                    section_idx += 1
            else:
                bot.Move.FollowPathAndExitMap(vq.outpost_path, target_map_id=vq.explorable_id)
        elif not has_outpost_path and not has_explorable:
            bot.UI.PrintMessageToConsole(BotSettings.BOT_NAME, f"No outpost exit path. Starting Vanquish from outpost.")
            for i in range(transit_count):
                t_coord = _get_first_path_coord(vq.transit_paths[i])
                bot.States.AddCustomState(lambda vi=vq_idx, si=section_idx, tc=t_coord: _set_section_header(_section_headers[vi][si], tc[0], tc[1]), f"SetSection_Transit_{vq_idx}_{i}")
                _register_path(bot, vq.transit_paths[i], header_name=f"Transit_{vq_idx}_{i}")
                section_idx += 1

        # -- Vanquish Path (Aggro: detect=2500, clear=2500) --
        bot.UI.PrintMessageToConsole(BotSettings.BOT_NAME, f"Starting Vanquish (Aggro): {vq.display}")
        vp_coord = _get_first_path_coord(vq.vanquish_path)
        bot.States.AddCustomState(lambda vi=vq_idx, si=section_idx, vc=vp_coord: _set_section_header(_section_headers[vi][si], vc[0], vc[1]), f"SetSection_VanquishPath_{vq_idx}")
        bot.config.FSM.RemoveManagedCoroutine("ConsetUpkeep")
        bot.config.FSM.RemoveManagedCoroutine("PconsUpkeep")
        if _restock_conset:
            bot.States.AddManagedCoroutine("ConsetUpkeep", lambda: _conset_upkeep(bot))
        if _restock_pcons:
            bot.States.AddManagedCoroutine("PconsUpkeep",
                lambda: _pcons_upkeep(bot))
        if _restock_use_summoning_stones:
            bot.Multibox.UseSummoningStone()
        target_header = _completed_header_names[vq_idx]  
        bot.States.AddManagedCoroutine("VanquishWatchdog", lambda h=target_header: VanquishWatchdog(bot, h))    
        _register_aggro_path(bot, vq.vanquish_path,
                             header_name=f"VanquishPath_{vq_idx}",
                             detection_radius=float(_aggro_range_forward),
                             clear_radius=float(_aggro_range_forward))
        bot.Wait.UntilOutOfCombat()
        section_idx += 1

        # -- Reverse Path (Aggro: ReverseAggro1) --
        bot.UI.PrintMessageToConsole(BotSettings.BOT_NAME, f"Starting Reverse Aggro Path 1 (range={_aggro_range_reverse1}).")
        reversed_path = _build_reversed_path(vq.vanquish_path)
        rp_coord = _get_first_path_coord(reversed_path)
        bot.States.AddCustomState(lambda vi=vq_idx, si=section_idx, rc=rp_coord: _set_section_header(_section_headers[vi][si], rc[0], rc[1]), f"SetSection_ReverseAggro1_{vq_idx}")
        def _log_reverse1(x, y, mn=vq.map_name):
            _reverse_detections.setdefault(mn, {}).setdefault("reverse1", []).append((round(x), round(y)))
        _register_aggro_path(bot, reversed_path,
                             header_name=f"ReverseAggro1_{vq_idx}",
                             detection_radius=float(_aggro_range_reverse1),
                             clear_radius=float(_aggro_range_reverse1),
                             on_enemy_detected=_log_reverse1)
        bot.Wait.UntilOutOfCombat()
        section_idx += 1

        # -- Reverse Path (Aggro: ReverseAggro2) --
        bot.UI.PrintMessageToConsole(BotSettings.BOT_NAME, f"Starting Reverse Aggro Path 2 (range={_aggro_range_reverse2}).")
        reversed_path = _build_reversed_path(vq.vanquish_path)
        rp5_coord = _get_first_path_coord(reversed_path)
        bot.States.AddCustomState(lambda vi=vq_idx, si=section_idx, rc=rp5_coord: _set_section_header(_section_headers[vi][si], rc[0], rc[1]), f"SetSection_ReverseAggro2_{vq_idx}")
        def _log_reverse2(x, y, mn=vq.map_name):
            _reverse_detections.setdefault(mn, {}).setdefault("reverse2", []).append((round(x), round(y)))
        _register_aggro_path(bot, reversed_path,
                             header_name=f"ReverseAggro2_{vq_idx}",
                             detection_radius=float(_aggro_range_reverse2),
                             clear_radius=float(_aggro_range_reverse2),
                             on_enemy_detected=_log_reverse2)
        bot.Wait.UntilOutOfCombat()
        section_idx += 1

        # -- Vanquish FAILED --
        bot.States.AddHeader(f"Vanquish Failed_{vq_idx}")
        bot.States.RemoveManagedCoroutine("VanquishWatchdog")
        bot.States.RemoveManagedCoroutine("ConsetUpkeep")
        bot.States.RemoveManagedCoroutine("PconsUpkeep")
        bot.UI.PrintMessageToConsole(BotSettings.BOT_NAME, f"Vanquish FAILED. Stopping bot. Report on Discord.")
        bot.States.AddCustomState(lambda: _stop_bot(), f"StopBot_{vq_idx}")

        # -- Vanquish Completed --
        bot.States.AddHeader(f"Vanquish Completed_{vq_idx}")
        bot.States.RemoveManagedCoroutine("VanquishWatchdog")
        bot.States.RemoveManagedCoroutine("ConsetUpkeep")
        bot.States.RemoveManagedCoroutine("PconsUpkeep")
        if is_last:
            bot.UI.PrintMessageToConsole(BotSettings.BOT_NAME, f"Vanquish queue SUCCESS: {vq.display}.")
            if _loop_queue:
                bot.Multibox.ResignParty()
                bot.Wait.ForTime(1000)
                bot.Wait.UntilOnOutpost()
                bot.States.AddCustomState(lambda h=first_vq_header: _do_loop_jump(bot, h), f"DoLoopJump")
        else:
            bot.UI.PrintMessageToConsole(BotSettings.BOT_NAME, f"Vanquish SUCCESS: {vq.display}. Moving to next Vanquish.")
            bot.Multibox.ResignParty()
            bot.Wait.ForTime(1000)
            bot.Wait.UntilOnOutpost()

    # All vanquishes finished
    bot.States.AddHeader("All Vanquishes Finished")
    bot.States.AddCustomState(lambda: _stop_bot(), "StopBotFinal")


def _stop_bot():
    global _reverse_detections, _vq_timers, _bot_start_time, _bot_total_elapsed
    # Print reverse detection summary for source file improvements
    if _reverse_detections:
        ConsoleLog(BotSettings.BOT_NAME, "=" * 60, Py4GW.Console.MessageType.Info, True)
        ConsoleLog(BotSettings.BOT_NAME, "REVERSE PASS ENEMY DETECTIONS (for source file updates):", Py4GW.Console.MessageType.Info, True)
        ConsoleLog(BotSettings.BOT_NAME, "=" * 60, Py4GW.Console.MessageType.Info, True)
        for map_name, phases in _reverse_detections.items():
            ConsoleLog(BotSettings.BOT_NAME, f"Map: {map_name}", Py4GW.Console.MessageType.Info, True)
            for phase, coords in sorted(phases.items()):
                if coords:
                    ConsoleLog(BotSettings.BOT_NAME, f"  Reverse {phase}:", Py4GW.Console.MessageType.Info, True)
                    # Deduplicate nearby coords (within 200 units)
                    unique = []
                    for cx, cy in coords:
                        is_dup = False
                        for ux, uy in unique:
                            if ((cx - ux)**2 + (cy - uy)**2) < 200**2:
                                is_dup = True
                                break
                        if not is_dup:
                            unique.append((cx, cy))
                    for cx, cy in unique:
                        ConsoleLog(BotSettings.BOT_NAME, f"    ({cx}, {cy})", Py4GW.Console.MessageType.Info, True)
                    ConsoleLog(BotSettings.BOT_NAME, f"  Total: {len(coords)} detections, {len(unique)} unique positions", Py4GW.Console.MessageType.Info, True)
        ConsoleLog(BotSettings.BOT_NAME, "=" * 60, Py4GW.Console.MessageType.Info, True)
    # Freeze any running timer on bot stop
    for _ti_key, _ti_val in _vq_timers.items():
        if not _ti_val["done"] and _ti_val["start"] > 0:
            _ti_val["elapsed"] = time.time() - _ti_val["start"]
            _ti_val["start"] = 0
    # Freeze total timer
    if _bot_start_time > 0.0:
        _bot_total_elapsed = time.time() - _bot_start_time
        _bot_start_time = 0.0
    bot.Stop()
    yield

def _do_loop_jump(bot: "Botting", first_vq_header: str):
    """CustomState coroutine: increment loop count and jump back to first vanquish."""
    global _loop_count
    _loop_count += 1
    ConsoleLog(BotSettings.BOT_NAME, f"Back at outpost. Starting loop #{_loop_count}. Jumping to: {first_vq_header}", Py4GW.Console.MessageType.Info, True)
    if bot.config.FSM.current_state:
        bot.config.FSM.current_state.reset()
    bot.config.FSM.jump_to_state_by_name(first_vq_header)
    yield
# endregion
# =============================================================================
# region EVENTS
def _conset_upkeep(bot):
    """Background coroutine: applies conset immediately, then re-checks every 30s."""
    ConsoleLog("ConsetUpkeep", "Conset Upkeep Coroutine Started", Py4GW.Console.MessageType.Debug, True)
    while True:
        if not _restock_conset or Map.IsOutpost():
            yield from Routines.Yield.wait(30000)
            continue
        essence_params = (ModelID.Essence_Of_Celerity.value, GLOBAL_CACHE.Skill.GetID("Essence_of_Celerity_item_effect"), 0, 0)
        grail_params = (ModelID.Grail_Of_Might.value, GLOBAL_CACHE.Skill.GetID("Grail_of_Might_item_effect"), 0, 0)
        armor_params = (ModelID.Armor_Of_Salvation.value, GLOBAL_CACHE.Skill.GetID("Armor_of_Salvation_item_effect"), 0, 0)
        for params in (essence_params, grail_params, armor_params):
            yield from bot.helpers.Multibox._use_consumable_message(params)
        yield from Routines.Yield.wait(30000)

def _pcons_upkeep(bot):
    """Background coroutine: applies pcons immediately, then re-checks every 30s."""
    ConsoleLog("PconsUpkeep", "Pcons Upkeep Coroutine Started", Py4GW.Console.MessageType.Debug, True)
    while True:
        if not _restock_pcons or Map.IsOutpost():
            yield from Routines.Yield.wait(30000)
            continue
        pcon_params = [
            (ModelID.Birthday_Cupcake.value, GLOBAL_CACHE.Skill.GetID("Birthday_Cupcake_skill"), 0, 0),
            (ModelID.Golden_Egg.value, GLOBAL_CACHE.Skill.GetID("Golden_Egg_skill"), 0, 0),
            (ModelID.Candy_Corn.value, GLOBAL_CACHE.Skill.GetID("Candy_Corn_skill"), 0, 0),
            (ModelID.Candy_Apple.value, GLOBAL_CACHE.Skill.GetID("Candy_Apple_skill"), 0, 0),
            (ModelID.Slice_Of_Pumpkin_Pie.value, GLOBAL_CACHE.Skill.GetID("Pie_Induced_Ecstasy"), 0, 0),
            (ModelID.Drake_Kabob.value, GLOBAL_CACHE.Skill.GetID("Drake_Skin"), 0, 0),
            (ModelID.Bowl_Of_Skalefin_Soup.value, GLOBAL_CACHE.Skill.GetID("Skale_Vigor"), 0, 0),
            (ModelID.Pahnai_Salad.value, GLOBAL_CACHE.Skill.GetID("Pahnai_Salad_item_effect"), 0, 0),
            (ModelID.War_Supplies.value, GLOBAL_CACHE.Skill.GetID("Well_Supplied"), 0, 0),
        ]
        for params in pcon_params:
            yield from bot.helpers.Multibox._use_consumable_message(params)
        yield from Routines.Yield.wait(30000)


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
        if bot.config.FSM.current_state:
            bot.config.FSM.current_state.reset()
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

    # Re-register managed coroutines if needed
    if _restock_conset:
        bot.config.FSM.AddManagedCoroutine("ConsetUpkeep", lambda: _conset_upkeep(bot))
    if _restock_pcons:
        bot.config.FSM.AddManagedCoroutine("PconsUpkeep", lambda: _pcons_upkeep(bot))

    # Jump to the current section header to re-execute the section path
    ConsoleLog("on_party_wipe", f"Jumping to section: {section_header}")
    if bot.config.FSM.current_state:
        bot.config.FSM.current_state.reset()
    bot.config.FSM.jump_to_state_by_name(section_header)
    bot.config.FSM.resume()


def OnPartyWipe(bot: "Botting"):
    ConsoleLog("on_party_wipe", "event triggered")
    fsm = bot.config.FSM
    # Reset current state to detach any SelfManagedYieldState coroutine
    if fsm.current_state:
        fsm.current_state.reset()
    fsm.pause()
    fsm.RemoveManagedCoroutine("ConsetUpkeep")
    fsm.RemoveManagedCoroutine("PconsUpkeep")
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
    global region_index, map_index, _queue_version, _prev_queue_version, _vq_timers, _bot_start_time, _bot_total_elapsed

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
    _bot_is_running = bot.config.fsm_running
    for qi, qv in enumerate(_queued_vanquishes):
        timer_info = _vq_timers.get(qi, None)
        if timer_info and timer_info["done"]:
            # Completed
            PyImGui.text_colored("[+]", (0.0, 1.0, 0.0, 1.0))
            PyImGui.same_line(0, 5)
            PyImGui.text(f"{qi + 1}. {qv.display}  {_format_time(timer_info['elapsed'])}")
        elif timer_info and timer_info["start"] > 0 and _bot_is_running:
            # Running (live timer)
            elapsed = time.time() - timer_info["start"]
            PyImGui.text_colored("[>]", (0.3, 0.6, 1.0, 1.0))
            PyImGui.same_line(0, 5)
            PyImGui.text(f"{qi + 1}. {qv.display}  {_format_time(elapsed)}")
        elif timer_info and timer_info["start"] > 0 and not _bot_is_running:
            # Bot stopped but timer was never frozen — auto-freeze now
            timer_info["elapsed"] = time.time() - timer_info["start"]
            timer_info["start"] = 0
            PyImGui.text_colored("[>]", (0.3, 0.6, 1.0, 1.0))
            PyImGui.same_line(0, 5)
            PyImGui.text(f"{qi + 1}. {qv.display}  {_format_time(timer_info['elapsed'])}")
        elif timer_info and timer_info["elapsed"] > 0:
            # Frozen timer (already frozen by _stop_bot or auto-freeze)
            PyImGui.text_colored("[>]", (0.3, 0.6, 1.0, 1.0))
            PyImGui.same_line(0, 5)
            PyImGui.text(f"{qi + 1}. {qv.display}  {_format_time(timer_info['elapsed'])}")
        else:
            # Not started
            PyImGui.text_colored("[-]", (0.5, 0.5, 0.5, 1.0))
            PyImGui.same_line(0, 5)
            PyImGui.text(f"{qi + 1}. {qv.display}")
        PyImGui.same_line(0, 10)
        if PyImGui.button(f"X##{qi}", 20, 20):
            to_remove = qi
    if to_remove is not None:
        _queued_vanquishes.pop(to_remove)
        if to_remove in _vq_timers:
            del _vq_timers[to_remove]
        _queue_version += 1
    if _bot_start_time > 0.0 and _bot_is_running:
        total_secs = time.time() - _bot_start_time
        PyImGui.text(f"  Total timer: {_format_time(total_secs)}")
    elif _bot_start_time > 0.0 and not _bot_is_running:
        # Auto-freeze total timer
        _bot_total_elapsed = time.time() - _bot_start_time
        _bot_start_time = 0.0
        PyImGui.text(f"  Total timer: {_format_time(_bot_total_elapsed)}")
    elif _bot_total_elapsed > 0.0:
        PyImGui.text(f"  Total timer: {_format_time(_bot_total_elapsed)}")

    # --- Rebuild FSM when queue changes ---
    if _queue_version != _prev_queue_version:
        bot.Stop()
        bot.config.FSM = FSM(BotSettings.BOT_NAME)
        bot.config.counters.clear_all()
        bot.config.initialized = False
        bot.UI._FSM_FILTER_START = 0
        bot.UI._FSM_FILTER_END = 0
        _prev_queue_version = _queue_version

    PyImGui.separator()
    if Map.GetMapID() != 857:
        if PyImGui.button("Travel to Embark Beach", 250, 30):
            Map.TravelToDistrict(857, random.choice(_RANDOM_DISTRICTS))
    else:
        if PyImGui.button("Move to Vanquish signpost", 250, 30):
            Player.Move(-428.00, -3439.00)

    _draw_settings_consumables()
    #_draw_settings_debug()

def _draw_settings_consumables():
    global _loop_queue, _restock_pcons, _restock_res_scroll, _restock_use_summoning_stones
    global _queue_version, _prev_build_settings

    PyImGui.separator()
    PyImGui.text("Consumables Selection")
    PyImGui.separator()

    global _restock_conset
    _restock_conset = PyImGui.checkbox("Restock & use Conset (Multibox)", _restock_conset)
    _restock_pcons = PyImGui.checkbox("Restock & use Pcons (Multibox)", _restock_pcons)

    use_honeycomb = bot.Properties.Get("honeycomb", "active")
    use_honeycomb = PyImGui.checkbox("Restock & use Honeycomb", use_honeycomb)
    bot.Properties.ApplyNow("honeycomb", "active", use_honeycomb)

    _restock_res_scroll = PyImGui.checkbox("Restock Resurrection Scroll (Multibox)", _restock_res_scroll)
    _restock_use_summoning_stones = PyImGui.checkbox("Restock & use Summoning Stones (Multibox)", _restock_use_summoning_stones)

    PyImGui.separator()
    PyImGui.text("Aggro Range Settings")
    PyImGui.separator()
    global _aggro_range_forward, _aggro_range_reverse1, _aggro_range_reverse2
    _aggro_range_forward = PyImGui.input_int("Forward pass range", _aggro_range_forward)
    _aggro_range_forward = max(1200, min(5000, _aggro_range_forward))
    _aggro_range_reverse1 = PyImGui.input_int("Reverse pass 1 range", _aggro_range_reverse1)
    _aggro_range_reverse1 = max(1200, min(5000, _aggro_range_reverse1))
    _aggro_range_reverse2 = PyImGui.input_int("Reverse pass 2 range", _aggro_range_reverse2)
    _aggro_range_reverse2 = max(1200, min(5000, _aggro_range_reverse2))

    PyImGui.separator()
    _loop_queue = PyImGui.checkbox("Loop Queue", _loop_queue)
    if _loop_queue and _loop_count > 0:
        PyImGui.same_line(0, 10)
        PyImGui.text(f"(loop #{_loop_count})")

    # Rebuild FSM if any build-time setting changed
    current_build_settings = (_restock_conset, _restock_pcons, use_honeycomb, _restock_res_scroll, _restock_use_summoning_stones, _loop_queue, _aggro_range_forward, _aggro_range_reverse1, _aggro_range_reverse2)
    if current_build_settings != _prev_build_settings:
        _prev_build_settings = current_build_settings
        _queue_version += 1

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
    if Map.IsMapLoading():
        return
    
    bot.UI.draw_window(icon_path=TEXTURE)

    if _queued_vanquishes:
        bot.Update()

if __name__ == "__main__":
    main()
# endregion
