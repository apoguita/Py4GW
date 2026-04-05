from Py4GWCoreLib import Botting, Routines, GLOBAL_CACHE, ModelID, Map, Agent, ConsoleLog, Player, AgentArray, Map
from Py4GWCoreLib import *
import Py4GW
import os
import PyImGui
import importlib.util
projects_base_path = Py4GW.Console.get_projects_path()
BOUNTIES_DIR = os.path.join(projects_base_path,"Sources","ZaishenBounty")

MODULE_NAME = "Zaishen Bounty"
MODULE_ICON = "Textures\\Module_Icons\\ZaishenBounty.png"

class BotSettings:
    BOT_NAME = "Zaishen Bounty"
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
# region BOUNTY QUEUE DATA
# =============================================================================
class QueuedBounty:
    """Stores all data needed to execute a single bounty."""
    def __init__(self, bounty_name, display,
                 outpost_id, explorable_id,
                 outpost_path, bounty_path,
                 transit_explorables, transit_paths):
        self.bounty_name = bounty_name
        self.display = display
        self.outpost_id = outpost_id
        self.explorable_id = explorable_id
        self.outpost_path = outpost_path
        self.bounty_path = bounty_path
        self.transit_explorables = transit_explorables
        self.transit_paths = transit_paths

_queued_bounties: list[QueuedBounty] = []
_queue_version: int = 0
_current_bounty_index: int = 0
_bounty_header_names: list[str] = []
_current_section_header: tuple = ("", 0.0, 0.0)  # (header_name, first_x, first_y)
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

    # Determine format by inspecting first element
    first = path[0]

    if isinstance(first, dict):
        # Format 2: list of dicts
        for entry in path:
            for key, value in entry.items():
                _handle_keyword(bot, key, value)

    elif isinstance(first, list):
        # Format 3: list of lists-of-tuples (allows duplicate keys)
        for segment in path:
            for key, value in segment:
                _handle_keyword(bot, key, value)

    else:
        # Format 1: simple path [(x,y), ...]
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


# endregion

# =============================================================================
# region BOT ROUTINE
# =============================================================================
def bot_routine(bot: Botting) -> None:
    global _current_bounty_index, _bounty_header_names

    if not _queued_bounties:
        ConsoleLog(BotSettings.BOT_NAME, "No bounties queued!", Py4GW.Console.MessageType.Error)
        return

    # Events
    condition = lambda: OnPartyWipe(bot)
    bot.Events.OnPartyWipeCallback(condition)

    # Main header
    bot.States.AddHeader(BotSettings.BOT_NAME)  # header counter = 1
    bot.Multibox.ApplyWidgetPolicy(enable_widgets=BotSettings.WIDGETS_TO_ENABLE)
    bot.Templates.Multibox_Aggressive()

    # Pre-calculate bounty header names for OnWipe outpost fallback.
    # Headers per bounty:
    #   1. Bounty_{idx}_{name}
    #   2. Prepare For Farm (inside PrepareForFarm)
    #   3. Transit_{idx}_0 (if transit exists)
    #   ... Transit_{idx}_N
    #   4. BountyPath_{idx}
    #   5. Bounty Completed_{idx}
    # Number of headers varies per bounty depending on transit count.
    _bounty_header_names = []
    _section_headers = {}  # b_idx → list of full header names for each section
    header_counter = 1  # starts at 1 (main header)
    for b_idx, bounty in enumerate(_queued_bounties):
        header_counter += 1  # Bounty_{idx}_{name}
        _bounty_header_names.append(f"[H]Bounty_{b_idx}_{bounty.bounty_name}_{header_counter}")
        header_counter += 1  # Prepare For Farm
        transit_count = len(bounty.transit_explorables)
        has_outpost_path = bool(bounty.outpost_path)
        has_explorable = bool(bounty.explorable_id)
        sections = []
        if transit_count > 0 and (has_outpost_path or not has_explorable):
            for t_i in range(transit_count):
                header_counter += 1
                sections.append(f"[H]Transit_{b_idx}_{t_i}_{header_counter}")
        header_counter += 1  # BountyPath_{idx}
        sections.append(f"[H]BountyPath_{b_idx}_{header_counter}")
        _section_headers[b_idx] = sections
        header_counter += 1  # Bounty Completed_{idx}

    # Pre-calculate the first bounty header name for looping.
    first_bounty_header = _bounty_header_names[0]

    # -------------------------------------------------------------------------
    # Build FSM states for each bounty
    # -------------------------------------------------------------------------

    for b_idx, bounty in enumerate(_queued_bounties):
        is_last = (b_idx == len(_queued_bounties) - 1)

        # -- Header for this bounty --
        bot.States.AddHeader(f"Bounty_{b_idx}_{bounty.bounty_name}")

        # -- Update current bounty index --
        def _set_current_index(idx=b_idx):
            global _current_bounty_index
            _current_bounty_index = idx
            yield
        bot.States.AddCustomState(lambda idx=b_idx: _set_current_index(idx),
                                  f"SetBountyIndex_{b_idx}")

        # -- Prepare for farm --
        bot.Templates.Routines.PrepareForFarm(map_id_to_travel=bounty.outpost_id)
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
        has_outpost_path = bool(bounty.outpost_path)
        has_explorable = bool(bounty.explorable_id)
        transit_count = len(bounty.transit_explorables)

        if has_outpost_path and has_explorable:
            if transit_count > 0:
                bot.Move.FollowPathAndExitMap(bounty.outpost_path, target_map_id=bounty.transit_explorables[0])
                for i in range(transit_count):
                    next_map = bounty.transit_explorables[i + 1] if i + 1 < transit_count else bounty.explorable_id
                    t_coord = _get_first_path_coord(bounty.transit_paths[i])
                    bot.States.AddCustomState(lambda bi=b_idx, ti=i, tc=t_coord: _set_section_header(_section_headers[bi][ti], tc[0], tc[1]),
                                              f"SetSection_Transit_{b_idx}_{i}")
                    if _restock_pcons:
                        bot.Multibox.UsePcons()
                    _register_path(bot, bounty.transit_paths[i], header_name=f"Transit_{b_idx}_{i}")
                    bot.Wait.ForMapToChange(next_map)
            else:
                bot.Move.FollowPathAndExitMap(bounty.outpost_path, target_map_id=bounty.explorable_id)
        elif not has_outpost_path and not has_explorable:
            bot.UI.PrintMessageToConsole(BotSettings.BOT_NAME, f"No outpost exit path. Executing transit paths from outpost.")
            for i in range(transit_count):
                t_coord = _get_first_path_coord(bounty.transit_paths[i])
                bot.States.AddCustomState(lambda bi=b_idx, ti=i, tc=t_coord: _set_section_header(_section_headers[bi][ti], tc[0], tc[1]),
                                          f"SetSection_Transit_{b_idx}_{i}")
                _register_path(bot, bounty.transit_paths[i], header_name=f"Transit_{b_idx}_{i}")
        elif has_outpost_path and not has_explorable:
            bot.UI.PrintMessageToConsole(BotSettings.BOT_NAME, f"Following outpost path, then transit paths.")
            if transit_count > 0:
                _register_path(bot, bounty.outpost_path)
                for i in range(transit_count):
                    _register_path(bot, bounty.transit_paths[i], header_name=f"Transit_{b_idx}_{i}")
            else:
                _register_path(bot, bounty.outpost_path)

        # -- Bounty Path --
        bp_coord = _get_first_path_coord(bounty.bounty_path)
        bot.States.AddCustomState(lambda bi=b_idx, bc=bp_coord: _set_section_header(_section_headers[bi][-1], bc[0], bc[1]),
                                  f"SetSection_BountyPath_{b_idx}")
        if _restock_pcons:
            bot.Multibox.UsePcons()
        _register_path(bot, bounty.bounty_path, header_name=f"BountyPath_{b_idx}")
        bot.UI.PrintMessageToConsole(BotSettings.BOT_NAME, f"Starting Bounty: {bounty.display}")
        bot.Wait.UntilOutOfCombat()

        # -- Bounty Completed --
        bot.States.AddHeader(f"Bounty Completed_{b_idx}")
        if is_last:
            bot.UI.PrintMessageToConsole(BotSettings.BOT_NAME, f"Bounty SUCCESS: {bounty.display}.")
            bot.States.AddCustomState(lambda: _check_loop_or_stop(bot),
                                      f"CheckLoopOrStop")
            bot.Multibox.ResignParty()
            bot.Wait.ForTime(1000)
            bot.Wait.UntilOnOutpost()
            bot.States.AddCustomState(lambda h=first_bounty_header: _do_loop_jump(bot, h),
                                      f"DoLoopJump")
        else:
            bot.UI.PrintMessageToConsole(BotSettings.BOT_NAME, f"Bounty SUCCESS: {bounty.display}. Moving to next Bounty.")
            bot.Multibox.ResignParty()
            bot.Wait.ForTime(1000)
            bot.Wait.UntilOnOutpost()

    # All bounties finished
    bot.States.AddHeader("All Bounties Finished")
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


def _do_loop_jump(bot: "Botting", first_bounty_header: str):
    """CustomState coroutine: increment loop count and jump back to first bounty."""
    global _loop_count
    _loop_count += 1
    ConsoleLog(BotSettings.BOT_NAME,
               f"Back at outpost. Starting loop #{_loop_count}. Jumping to: {first_bounty_header}",
               Py4GW.Console.MessageType.Info, True)
    bot.config.FSM.jump_to_state_by_name(first_bounty_header)
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
        target = _bounty_header_names[_current_bounty_index]
        ConsoleLog("on_party_wipe",
                   f"Resurrected in outpost. Re-executing bounty. Jumping to: {target}")
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
         In this case, transit paths handle their own map changes via 'map' keyword.
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

def _load_bounty_data(bounty_name):
    """Load a bounty module and return a QueuedBounty with all its data."""
    bounty_file = os.path.join(BOUNTIES_DIR, bounty_name) + ".py"
    spec = importlib.util.spec_from_file_location(bounty_name, bounty_file)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    ids = getattr(mod, f"{bounty_name}_ids", {})
    outpost_id = ids.get("outpost_id", 0)
    explorable_id = ids.get("map_id", 0)
    outpost_path = getattr(mod, f"{bounty_name}_outpost_path", [])
    bounty_path = getattr(mod, bounty_name, [])
    transit_explorables, transit_paths = _load_transit_data(mod, bounty_name)

    display = bounty_name

    return QueuedBounty(
        bounty_name=bounty_name,
        display=display,
        outpost_id=outpost_id,
        explorable_id=explorable_id,
        outpost_path=outpost_path,
        bounty_path=bounty_path,
        transit_explorables=transit_explorables,
        transit_paths=transit_paths,
    )
# endregion

# =============================================================================
# region UI
# =============================================================================
bounty_index = 0
_prev_queue_version: int = -1

def _draw_settings():
    global bounty_index, _queue_version, _prev_queue_version

    # --- Bounty combo ---
    PyImGui.text("Bounty Selection")
    PyImGui.separator()
    bounties = sorted([
        f[:-3] for f in os.listdir(BOUNTIES_DIR)
        if f.endswith(".py")
    ])
    bounty_index = PyImGui.combo("##Bounty", bounty_index, bounties)
    if bounty_index >= len(bounties):
        bounty_index = 0

    # --- Add Bounty / Clear buttons ---
    if PyImGui.button("Add Bounty", 120, 25):
        qb = _load_bounty_data(bounties[bounty_index])
        _queued_bounties.append(qb)
        _queue_version += 1

    PyImGui.same_line(0, 10)
    if PyImGui.button("Clear Bounties", 120, 25):
        _queued_bounties.clear()
        _queue_version += 1

    # --- Queue display ---
    PyImGui.separator()
    PyImGui.text(f"Queued bounties: {len(_queued_bounties)}")
    to_remove = None
    for i, qb in enumerate(_queued_bounties):
        marker = " <-- CURRENT" if i == _current_bounty_index and bot.config.initialized else ""
        PyImGui.text(f"  {i + 1}. {qb.display}{marker}")
        PyImGui.same_line(0, 10)
        if PyImGui.button(f"X##{i}", 20, 20):
            to_remove = i
    if to_remove is not None:
        _queued_bounties.pop(to_remove)
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
        if PyImGui.button("Move to Bounty signpost", 250, 30):
            Player.Move(-557.00, -3333.00)

    _draw_settings_consumables()
    #_draw_settings_debug()

def _draw_settings_consumables():
    global _loop_queue

    PyImGui.separator()
    PyImGui.text("Consumables Selection")
    PyImGui.separator()

    use_conset = bot.Properties.Get("armor_of_salvation", "active")
    use_conset = PyImGui.checkbox("Restock & use Conset", use_conset)
    bot.Properties.ApplyNow("armor_of_salvation", "active", use_conset)
    bot.Properties.ApplyNow("essence_of_celerity", "active", use_conset)
    bot.Properties.ApplyNow("grail_of_might", "active", use_conset)

    global _restock_pcons
    _restock_pcons = PyImGui.checkbox("Restock & use Pcons (Multibox)", _restock_pcons)

    use_honeycomb = bot.Properties.Get("honeycomb", "active")
    use_honeycomb = PyImGui.checkbox("Restock & use Honeycomb", use_honeycomb)
    bot.Properties.ApplyNow("honeycomb", "active", use_honeycomb)

    global _restock_res_scroll
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
    PyImGui.text(f"_current_bounty_index: {_current_bounty_index}")
    PyImGui.text(f"_queued_bounties: {len(_queued_bounties)}")
    PyImGui.text(f"_bounty_header_names: {_bounty_header_names}")
    PyImGui.text(f"_loop_queue: {_loop_queue}")
    PyImGui.text(f"_loop_count: {_loop_count}")
    for i, qb in enumerate(_queued_bounties):
        marker = " <-- CURRENT" if i == _current_bounty_index else ""
        PyImGui.text(f"  {i+1}. {qb.display} (outpost={qb.outpost_id}, expl={qb.explorable_id}){marker}")

def _draw_help():
    PyImGui.text("Developed by: Aura")
    PyImGui.text("Bounties credits to: Simfoniya")
# endregion

# =============================================================================
# region MAIN
# =============================================================================
bot.SetMainRoutine(bot_routine)

TEXTURE = os.path.join(Py4GW.Console.get_projects_path(), "Textures", "Module_Icons", "ZaishenBounty.png")
bot.UI.override_draw_config(lambda: _draw_settings())
bot.UI.override_draw_help(lambda: _draw_help())

def main():
    if not Routines.Checks.Map.MapValid():
        return
    
    bot.UI.draw_window(icon_path=TEXTURE)

    if _queued_bounties:
        bot.Update()

if __name__ == "__main__":
    main()
# endregion
