"""
Quest Auto-Runner (Simple)
Author: raffaeloguido
Description: Minimal quest runner that reads the active quest, converts its marker,
computes a navmesh path, and walks to the marker while pausing for combat/looting.
Start the bot on the correct quest map/outpost.
"""

from __future__ import annotations
import time
import os
from Py4GWCoreLib import Botting, Quest, Map, Player, ConsoleLog, Console, Routines, IniHandler, Timer, ImGui
from Py4GWCoreLib import GLOBAL_CACHE
from Py4GWCoreLib.Pathing import AutoPathing
from Py4GWCoreLib.Agent import Agent
from Py4GWCoreLib.enums import SharedCommandType
import PyImGui


def LootingRoutineActive() -> bool:
    """Check if a looting command is currently active in shared memory."""
    account_email = Player.GetAccountEmail()
    index, message = GLOBAL_CACHE.ShMem.PreviewNextMessage(account_email)

    if index == -1 or message is None:
        return False

    if message.Command != SharedCommandType.PickUpLoot:
        return False
    return True

BOT_NAME = "Quest Auto-Runner (Simple)"
MARKER_UPDATE_TIMEOUT_S = 20.0
MARKER_POLL_INTERVAL_S = 1.0

# Configuration
script_directory = os.path.dirname(os.path.abspath(__file__))
root_directory = os.path.normpath(os.path.join(script_directory, ".."))
ini_file_location = os.path.join(root_directory, "Widgets/Config/Quest Auto-Runner.ini")

ini_handler = IniHandler(ini_file_location)
sync_timer = Timer()
sync_timer.Start()
sync_interval = 1000

class Config:
    def __init__(self):
        """Read configuration values from INI file"""
        self.debug_logging = ini_handler.read_bool(BOT_NAME, "debug_logging", False)

    def save(self):
        """Save the current configuration to the INI file."""
        if sync_timer.HasElapsed(sync_interval):
            ini_handler.write_key(BOT_NAME, "debug_logging", str(self.debug_logging))
            sync_timer.Start()

bot_config = Config()

# Configuration window
config_module = ImGui.WindowModule(
    f"{BOT_NAME} Config",
    window_name=f"{BOT_NAME} Settings##{BOT_NAME}",
    window_size=(300, 150),
    window_flags=PyImGui.WindowFlags.AlwaysAutoResize
)
window_x = ini_handler.read_int(BOT_NAME + " Config", "config_x", 300)
window_y = ini_handler.read_int(BOT_NAME + " Config", "config_y", 300)
config_module.window_pos = (window_x, window_y)

def DebugLog(module_name: str, message: str, message_type=Console.MessageType.Info):
    """Wrapper for ConsoleLog that respects debug_logging setting"""
    if bot_config.debug_logging:
        ConsoleLog(module_name, message, message_type)

# Create bot instance
bot = Botting(BOT_NAME)

# Configure combat properties - uses simple auto_combat
properties = bot.Properties
properties.Enable("pause_on_danger")   # Pause when enemies near
properties.Enable("auto_combat")       # AutoCombat handles fighting
properties.Disable("hero_ai")          # Don't use HeroAI
properties.Enable("auto_loot")         # Enable looting
properties.Disable("auto_inventory_management")  # No salvaging/ID
properties.Disable("halt_on_death")    # Don't stop on death
properties.Set("movement_timeout", value=-1)  # No timeout

DebugLog(BOT_NAME, "Combat config: pause_on_danger + auto_combat + auto_loot enabled", Console.MessageType.Info)

# Wait for lagging or dead party members before continuing.
bot.Events.OnPartyMemberBehindCallback(
    lambda: bot.Templates.Routines.OnPartyMemberBehind()
)
bot.Events.OnPartyMemberDeadBehindCallback(
    lambda: bot.Templates.Routines.OnPartyMemberDeathBehind()
)

# Quest data storage
quest_info = {
    "quest_data": None,
    "marker_x": 0,
    "marker_y": 0,
    "is_valid": False
}

def GetQuestData():
    """Get and validate the active quest data."""
    active_quest_id = Quest.GetActiveQuest()

    if active_quest_id == 0:
        DebugLog(BOT_NAME, "ERROR: No active quest found!", Console.MessageType.Error)
        DebugLog(BOT_NAME, "Please click a quest in your in-game quest log to make it active.", Console.MessageType.Info)
        raise Exception("No active quest")

    quest_data = Quest.GetQuestData(active_quest_id)

    if quest_data.is_completed:
        DebugLog(BOT_NAME, f"WARNING: Quest '{quest_data.name}' is already completed. Navigating to its marker anyway.", Console.MessageType.Warning)

    quest_name_display = quest_data.name if quest_data.name else f"Quest #{active_quest_id}"
    DebugLog(BOT_NAME, f"Active Quest: {quest_name_display} (ID: {active_quest_id})", Console.MessageType.Info)

    target_map_name = Map.GetMapName(quest_data.map_to)
    DebugLog(BOT_NAME, f"Target Map: {target_map_name} (ID: {quest_data.map_to})", Console.MessageType.Info)
    DebugLog(BOT_NAME, f"Quest Marker: ({quest_data.marker_x:.0f}, {quest_data.marker_y:.0f})", Console.MessageType.Info)

    return quest_data

def ConvertQuestMarkerCoordinates(quest_data) -> tuple[float, float] | None:
    """Convert quest marker coordinates from unsigned to signed if needed.

    Returns None if coordinates are invalid, otherwise returns (x, y) as floats.
    """
    marker_x = quest_data.marker_x
    marker_y = quest_data.marker_y

    # Check for sentinel values
    if marker_x == 2147483648 or marker_y == 2147483648:
        return None
    if marker_x == 0 and marker_y == 0:
        return None

    # Convert unsigned to signed
    if marker_y > 2147483647:
        marker_y = marker_y - 4294967296
    if marker_x > 2147483647:
        marker_x = marker_x - 4294967296

    return float(marker_x), float(marker_y)

def bot_routine(bot: Botting) -> None:
    """Main bot routine using Botting framework."""

    DebugLog(BOT_NAME, "=== Bot routine starting ===", Console.MessageType.Info)

    # Step 1: Load quest data and get coordinates
    bot.States.AddHeader("Load Quest Data")

    def load_and_setup():
        DebugLog(BOT_NAME, "Loading quest data...", Console.MessageType.Info)
        try:
            quest_info["quest_data"] = GetQuestData()
            quest_data = quest_info["quest_data"]

            # Convert coordinates immediately
            coords = ConvertQuestMarkerCoordinates(quest_data)

            if coords is None:
                DebugLog(BOT_NAME, "ERROR: Quest has no valid marker coordinates!", Console.MessageType.Error)
                bot.Stop()
                return

            marker_x, marker_y = coords
            quest_info["marker_x"] = marker_x
            quest_info["marker_y"] = marker_y
            quest_info["is_valid"] = True

            DebugLog(BOT_NAME, f"Quest marker: ({marker_x:.0f}, {marker_y:.0f})", Console.MessageType.Info)

        except Exception as e:
            DebugLog(BOT_NAME, f"Failed to load quest: {str(e)}", Console.MessageType.Error)
            quest_info["is_valid"] = False
            bot.Stop()
            # Let FSM exit cleanly
            return
        yield

    bot.States.AddCustomState(load_and_setup, "Load Quest Data")

    # Step 2: (Travel removed) assume user is on/near the quest map
    target_map_id = quest_info["quest_data"].map_to if quest_info.get("quest_data") else None
    if target_map_id is not None and Map.GetMapID() != target_map_id:
        DebugLog(BOT_NAME, "Travel step skipped — start the bot on the quest map/outpost.", Console.MessageType.Warning)
    # Step 3: Navigate to quest marker
    bot.States.AddHeader("Navigate to Quest Marker")

    def setup_navigation():
        """Set up navigation states using bot.Move."""
        if not quest_info.get("is_valid"):
            DebugLog(BOT_NAME, "Quest data invalid, cannot navigate", Console.MessageType.Error)
            bot.Stop()
            return

        marker_x = quest_info["marker_x"]
        marker_y = quest_info["marker_y"]
        if marker_x is None or marker_y is None:
            DebugLog(BOT_NAME, "Quest marker coordinates missing; cannot navigate", Console.MessageType.Error)
            bot.Stop()
            return

        # Cast to float to satisfy pathing typing
        marker_x = float(marker_x)
        marker_y = float(marker_y)
        start_map_id = Map.GetMapID()

        DebugLog(BOT_NAME, f"Setting up navigation to ({marker_x:.0f}, {marker_y:.0f})", Console.MessageType.Info)

        # Pause following while looting or in combat
        loot_hold_until = [0.0]
        combat_hold_until = [0.0]

        def should_pause():
            """Check if movement should pause for combat, looting, or party issues."""
            now = time.time()

            try:
                # PRIORITY 1: Check if FSM is paused (handles party member death/behind events)
                if bot.config.FSM.is_paused():
                    return True

                # PRIORITY 2: Check if there's a dead party member
                dead_player = Routines.Party.GetDeadPartyMemberID()
                if dead_player != 0:
                    return True

                # Check for active looting (uses shared memory - more reliable)
                if LootingRoutineActive():
                    loot_hold_until[0] = now + 0.5  # Short cooldown, we'll re-check actual state
                    return True

                # Check for combat
                player_id = Player.GetAgentID()
                in_combat = Agent.IsInCombatStance(player_id)
                in_danger = Routines.Checks.Agents.InDanger()

                if in_combat or in_danger:
                    combat_hold_until[0] = now + 2.0
                    return True

                # Check cooldown timers
                if loot_hold_until[0] > now or combat_hold_until[0] > now:
                    return True

                return False

            except Exception as e:
                DebugLog(BOT_NAME, f"Error in should_pause: {e}", Console.MessageType.Warning)
                return False  # Don't pause on error - let movement continue

        def refresh_marker_from_quest():
            quest_info["quest_data"] = GetQuestData()
            qd = quest_info["quest_data"]
            return ConvertQuestMarkerCoordinates(qd)

        def wait_for_next_marker(current_marker):
            DebugLog(BOT_NAME, f"Waiting up to {MARKER_UPDATE_TIMEOUT_S:.0f}s for next quest marker...", Console.MessageType.Info)
            start_time = time.time()
            while time.time() - start_time < MARKER_UPDATE_TIMEOUT_S:
                try:
                    qd = Quest.GetQuestData(Quest.GetActiveQuest())
                    if qd.is_completed:
                        DebugLog(BOT_NAME, "Quest completed; no further markers expected.", Console.MessageType.Success)
                        return None
                    next_marker = ConvertQuestMarkerCoordinates(qd)
                except Exception as e:
                    DebugLog(BOT_NAME, f"Failed to refresh quest marker: {e}", Console.MessageType.Warning)
                    next_marker = None

                if next_marker is not None and next_marker != current_marker:
                    return next_marker

                yield from Routines.Yield.wait(int(MARKER_POLL_INTERVAL_S * 1000))
            return None

        # Use AutoPathing to detour around obstacles/navmesh gaps
        while True:
            attempt = 0
            reached = False
            while attempt < 3 and not reached:
                attempt += 1

                # If we changed maps (portal/zone), refresh quest data and marker
                current_map_id = Map.GetMapID()
                if current_map_id != start_map_id:
                    try:
                        refreshed_marker = refresh_marker_from_quest()
                        if refreshed_marker is None:
                            DebugLog(BOT_NAME, "Quest marker coordinates missing after map change; stopping", Console.MessageType.Error)
                            return
                        marker_x, marker_y = refreshed_marker
                        quest_info["marker_x"] = marker_x
                        quest_info["marker_y"] = marker_y
                        DebugLog(BOT_NAME, f"Map changed to {Map.GetMapName(current_map_id)}; refreshed quest marker to ({marker_x:.0f}, {marker_y:.0f})", Console.MessageType.Info)
                        start_map_id = current_map_id
                    except Exception as e:
                        DebugLog(BOT_NAME, f"Failed to refresh quest data after map change: {e}", Console.MessageType.Error)
                        return

                try:
                    path = yield from AutoPathing().get_path_to(marker_x, marker_y)
                except Exception as e:
                    DebugLog(BOT_NAME, f"Pathfinding failed (attempt {attempt}/3): {e}", Console.MessageType.Warning)
                    path = []

                if not path:
                    DebugLog(BOT_NAME, f"No path returned from AutoPathing (attempt {attempt}/3)", Console.MessageType.Warning)
                    yield from Routines.Yield.wait(1000)
                    continue

                DebugLog(BOT_NAME, f"Following path with {len(path)} waypoints (attempt {attempt}/3)", Console.MessageType.Info)
                success = yield from Routines.Yield.Movement.FollowPath(
                    path_points=path,
                    tolerance=200,
                    timeout=120000,
                    custom_pause_fn=should_pause
                )

                if success:
                    reached = True
                    break

                # Path failed (e.g., map change/portal). Wait briefly and retry with fresh navmesh.
                DebugLog(BOT_NAME, f"Path interrupted; retrying navigation ({attempt}/3)", Console.MessageType.Warning)
                yield from Routines.Yield.wait(2000)

            if not reached:
                DebugLog(BOT_NAME, "Failed to reach quest marker after retries; stopping navigation", Console.MessageType.Error)
                return

            next_marker = yield from wait_for_next_marker((marker_x, marker_y))
            if next_marker is None:
                break

            marker_x, marker_y = next_marker
            quest_info["marker_x"] = marker_x
            quest_info["marker_y"] = marker_y
            DebugLog(BOT_NAME, f"New quest marker detected: ({marker_x:.0f}, {marker_y:.0f})", Console.MessageType.Info)

        yield

    bot.States.AddCustomState(setup_navigation, "Setup Navigation")

    # Add wait for combat after movement
    bot.Wait.UntilOutOfCombat()

    # Step 4: Completion
    bot.States.AddHeader("Quest Marker Reached")

    def completion():
        DebugLog(BOT_NAME, "=== Arrived at quest marker! ===", Console.MessageType.Success)
        DebugLog(BOT_NAME, "Handle quest objectives manually or restart for next quest.", Console.MessageType.Info)
        yield

    bot.States.AddCustomState(completion, "Completion")

# Set the main routine
bot.SetMainRoutine(bot_routine)

def draw_window():
    """Draw the bot UI."""
    from Py4GWCoreLib import Color
    from Py4GWCoreLib.ImGui import ImGui
    from Py4GWCoreLib.ImGui_src.IconsFontAwesome5 import IconsFontAwesome5

    # Try to load quest data for display
    quest_name = "No quest loaded"
    quest_map = "Unknown"

    try:
        active_id = Quest.GetActiveQuest()
        if active_id != 0:
            quest_data = Quest.GetQuestData(active_id)
            if quest_data and not quest_data.is_completed:
                quest_name = quest_data.name if quest_data.name else f"Quest #{active_id}"
                target_map_name = Map.GetMapName(quest_data.map_to)
                quest_map = target_map_name if target_map_name != "Unknown Map ID" else f"Map {quest_data.map_to}"
    except:
        pass

    if not PyImGui.begin(BOT_NAME, PyImGui.WindowFlags.AlwaysAutoResize):
        PyImGui.end()
        return

    # Title
    PyImGui.dummy(0, 3)
    ImGui.push_font("Regular", 22)
    PyImGui.push_style_color(PyImGui.ImGuiCol.Text, Color(255, 255, 0, 255).to_tuple_normalized())
    PyImGui.text(BOT_NAME)
    PyImGui.pop_style_color(1)
    ImGui.pop_font()

    # Quest info
    ImGui.push_font("Bold", 16)
    PyImGui.push_style_color(PyImGui.ImGuiCol.Text, Color(100, 200, 255, 255).to_tuple_normalized())
    PyImGui.text(quest_name)
    PyImGui.pop_style_color(1)
    ImGui.pop_font()

    PyImGui.text(f"Target: {quest_map}")

    PyImGui.separator()

    # Status (reflect FSM state)
    fsm = bot.config.FSM
    if fsm.is_started():
        if getattr(fsm, "is_paused", lambda: False)():
            status_label = "Status: Paused"
        elif getattr(fsm, "is_finished", lambda: False)():
            status_label = "Status: Finished"
        else:
            status_label = "Status: Running"
        ImGui.push_font("Bold", 14)
        PyImGui.text(status_label)
        ImGui.pop_font()

        # Current state
        current_state = bot.config.FSM.get_current_step_name()
        if current_state:
            # Clean up state name for better display
            import re
            clean_state = re.sub(r'_\d+$', '', current_state)

            # Map technical state names to user-friendly names
            state_display_names = {
                "pause on danger ENABLE": "Initializing",
                "Load Quest Data": "Loading Quest Data",
                "Travel to Quest Map": "Traveling to Quest Map",
                "Setup Navigation": "Setting up Navigation",
                "GetPathTo": "Calculating Path",
                "XY": "Moving to Quest Marker",
                "FollowPath": "Following Path",
                "UntilOutOfCombat": "Waiting for Combat to End",
                "Completion": "Quest Marker Reached",
            }

            # Check for exact matches first
            display_state = None
            for key, value in state_display_names.items():
                if key.lower() in clean_state.lower():
                    display_state = value
                    break

            # If no match, just clean up the name
            if display_state is None:
                display_state = clean_state.replace('_', ' ').title()

            PyImGui.text(f"State: {display_state}")

        # Check for combat/looting
        from Py4GWCoreLib.Routines import Routines as Rout
        if Rout.Checks.Agents.InDanger():
            PyImGui.push_style_color(PyImGui.ImGuiCol.Text, Color(255, 100, 100, 255).to_tuple_normalized())
            PyImGui.text("Combat active!")
            PyImGui.pop_style_color(1)
        elif bot.config.FSM.is_paused():
            PyImGui.push_style_color(PyImGui.ImGuiCol.Text, Color(255, 200, 100, 255).to_tuple_normalized())
            PyImGui.text("Paused (looting/combat)")
            PyImGui.pop_style_color(1)
    else:
        PyImGui.text("Status: Idle")

    # Start/Stop button
    is_running = bot.config.FSM.is_started()
    icon = IconsFontAwesome5.ICON_STOP_CIRCLE if is_running else IconsFontAwesome5.ICON_PLAY_CIRCLE
    legend = "  Stop Bot" if is_running else "  Start Bot"

    if PyImGui.button(icon + legend + "##BotToggle"):
        if is_running:
            bot.Stop()
        else:
            bot.Start()

    PyImGui.end()

def configure():
    """Draw configuration window for the bot."""
    global bot_config, config_module, ini_handler

    if config_module.first_run:
        PyImGui.set_next_window_size(config_module.window_size[0], config_module.window_size[1])
        PyImGui.set_next_window_pos(config_module.window_pos[0], config_module.window_pos[1])
        config_module.first_run = False

    end_pos = config_module.window_pos
    if PyImGui.begin(config_module.window_name, config_module.window_flags):
        PyImGui.text_wrapped(f"{BOT_NAME} Settings")
        PyImGui.separator()
        PyImGui.dummy(0, 5)

        # Debug logging toggle
        PyImGui.text("Debug Logging:")
        bot_config.debug_logging = PyImGui.checkbox("##debug_logging", bot_config.debug_logging)
        if PyImGui.is_item_hovered():
            PyImGui.set_tooltip("Enable/disable console log messages from this bot")

        PyImGui.dummy(0, 5)
        PyImGui.separator()
        PyImGui.text_wrapped("When enabled, the bot will print status messages to the console.")

        bot_config.save()
        end_pos = PyImGui.get_window_pos()

    PyImGui.end()

    if end_pos[0] != config_module.window_pos[0] or end_pos[1] != config_module.window_pos[1]:
        config_module.window_pos = (int(end_pos[0]), int(end_pos[1]))
        ini_handler.write_key(BOT_NAME + " Config", "config_x", str(int(end_pos[0])))
        ini_handler.write_key(BOT_NAME + " Config", "config_y", str(int(end_pos[1])))

def main():
    """Main entry point called every frame."""
    # Update bot framework
    bot.Update()

    # Draw UI
    draw_window()

if __name__ == "__main__":
    main()
