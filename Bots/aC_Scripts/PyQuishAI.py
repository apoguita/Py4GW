import Py4GW
import os
projects_base_path = Py4GW.Console.get_projects_path()
ac_folder_path = os.path.join(projects_base_path, "Bots", "aC_Scripts")
os.chdir(ac_folder_path)
#Py4GW.Console.change_working_directory(ac_folder_path)

from Py4GWCoreLib import *
from Widgets.Blessed import Get_Blessed
from aC_api import *
from HeroAI.cache_data import *
import time
import math
import importlib.util
from aC_api.Blessing_Core import get_blessing_npc
from aC_api.Titles import (
    display_title_track, display_faction, display_title_progress,
    vanguard_tiers, norn_tiers, asura_tiers, deldrimor_tiers,
    sunspear_tiers, lightbringer_tiers, kurzick_tiers, luxon_tiers,
    luxon_regions, kurzick_regions, nightfall_regions, eotn_region_titles
)

module_name = "PyQuishAI "
cache_data = CacheData()

RECHECK_INTERVAL_MS = 500 # Used for followpathandaggro 
ARRIVAL_TOLERANCE = 250  # Used for path point arrival

#NEW: Auto-load selected map script
MAPS_DIR = "PyQuishAI_maps"


# Default placeholders (used if no dynamic script is selected)
OUTPOST_ID = 389
MAP_ID = 200
outpost_path = []
map_path = []

combat_handler = SkillManager.Autocombat()

class FSMVars:
    def __init__(self):
        self.global_combat_fsm = FSM("Global Combat Monitor")
        self.global_combat_handler = FSM("Interruptible Combat")
        self.state_machine = FSM("MainStateMachine")
        self.movement_handler = Routines.Movement.FollowXY()
        self.exact_movement_handler = Routines.Movement.FollowXY(tolerance=500)
        self.outpost_pathing = Routines.Movement.PathHandler(outpost_path)
        self.explorable_pathing = Routines.Movement.PathHandler(map_path)
        self.path_and_aggro = FollowPathAndAggro(self.explorable_pathing, self.movement_handler, aggro_range=2500, log_actions=True)
        self.chest_found_pathing = None
        self.loot_chest = FSM("LootChestStateMachine")
        self.sell_to_vendor = FSM("VendorStateMachine")
        self._current_path_point = None
        self.non_movement_timer = Timer()
        self.auto_stuck_command_timer = Timer()
        self.old_player_x = 0
        self.old_player_y = 0
        self.stuck_count = 0
        self.in_waiting_routine = False
        self.in_killing_routine = False
        self.last_skill_time = 0
        self.current_skill = 1
        self.blessing_timer = Timer()
        self.has_blessing = False
        self.in_blessing_dialog = False
        self.get_blessing_delay_start = None
        self.blessing_points = []
        self.blessing_triggered = set()
        self.blessing_timers = {}

class BotVars:
    def __init__(self):
        self.window_module = ImGui.WindowModule(
            module_name,
            window_name="MQVQ Bot",
            window_size=(300, 300),
            window_flags=PyImGui.WindowFlags.AlwaysAutoResize
        )
        self.is_running = False
        self.is_paused = False
        self.starting_map = OUTPOST_ID
        self.combat_started = False
        self.pause_combat_fsm = False
        self.global_timer = Timer()
        self.lap_timer = Timer()
        self.lap_history = []
        self.min_time = 0
        self.max_time = 0
        self.avg_time = 0.0
        self.runs_attempted = 0
        self.runs_completed = 0
        self.success_rate = 0.0
        self.selected_region = ""
        self.selected_map = ""
        self.map_data = {}

def trigger_blessing_at(point):
    if point in FSM_vars.blessing_triggered:
        return

    if point not in FSM_vars.blessing_timers:
        FSM_vars.blessing_timers[point] = time.time()
        return

    if time.time() - FSM_vars.blessing_timers[point] < 5.0:
        return

    ConsoleLog("Blessing", f"Triggering blessing at {point}", Console.MessageType.Info)
    Get_Blessed()
    FSM_vars.blessing_triggered.add(point)

class FollowPathAndAggro:
    def __init__(self, path_handler, follow_handler, aggro_range=2500, log_actions=False):
        self.path_handler       = path_handler
        self.follow_handler     = follow_handler
        self.aggro_range        = aggro_range
        self.log_actions        = log_actions
        self._last_scanned_enemy = None
        # ── THROTTLING STATE ───────────────────────────────────────────
        # only re-scan if we've moved this far (¾ of aggro_range)
        self._scan_move_thresh   = aggro_range * 0.75
        # track the last position we scanned at
        self._last_scan_pos      = Player.GetXY()
        # also still guard by time interval (ms)
        self._scan_interval_ms   = 500
        self._enemy_scan_timer   = Timer()
        # for ChangeTarget/Move dedupe
        self._last_target_id     = None
        self._last_move_target   = None
        # instrumentation counters & timer
        self._stats_start_time      = time.time()
        self.enemy_array_fetches    = 0
        self.change_target_calls    = 0
        self.move_calls             = 0
        self._stats_interval_secs   = 30.0

        self._last_enemy_check      = Timer()
        self._current_target_enemy  = None
        self._mode                  = 'path'
        self._current_path_point    = None
        self.status_message         = "Waiting to begin..."

    def _throttled_scan(self):
        curr_pos   = Player.GetXY()
        dist_moved = Utils.Distance(curr_pos, self._last_scan_pos)

        if (dist_moved >= self._scan_move_thresh
                or self._enemy_scan_timer.HasElapsed(self._scan_interval_ms)):
            # re-do the heavy call
            self._last_scanned_enemy = self._find_nearest_enemy()
            self._last_scan_pos      = curr_pos
            self._enemy_scan_timer.Reset()

        return self._last_scanned_enemy

    def _find_nearest_enemy(self):
        # instrumentation
        self.enemy_array_fetches += 1

        my_pos = Player.GetXY()
        enemies = [
            e for e in AgentArray.GetEnemyArray()
            if Agent.IsAlive(e) and Utils.Distance(my_pos, Agent.GetXY(e)) <= self.aggro_range
        ]
        if not enemies:
            return None
        return AgentArray.Sort.ByDistance(enemies, my_pos)[0]

    def _approach_enemy(self):
        if not self._current_target_enemy or not Agent.IsAlive(self._current_target_enemy):
            self._current_target_enemy = self._find_nearest_enemy()
            if not self._current_target_enemy:
                self._mode = 'path'
                self.status_message = "No enemies nearby."
                return

        if self._enemy_scan_timer.HasElapsed(self._scan_interval_ms):
            new_enemy = self._find_nearest_enemy()
            if new_enemy:
                self._current_target_enemy = new_enemy
            self._enemy_scan_timer.Reset()

        if not self._current_target_enemy:
            self._mode = 'path'
            self.status_message = "Returning to path mode."
            return

        try:
            tx, ty = Agent.GetXY(self._current_target_enemy)
        except Exception:
            self._mode = 'path'
            self.status_message = "Error getting target position."
            return

        # ── target only if it’s a new one ───────────────────────────
        if self._current_target_enemy != self._last_target_id:
            Player.ChangeTarget(self._current_target_enemy)
            self.change_target_calls += 1
            self._last_target_id = self._current_target_enemy

        # ── move only if the coords differ ──────────────────────────
        new_move = (int(tx), int(ty))
        if new_move != self._last_move_target:
            Player.Move(*new_move)
            self.move_calls += 1
            self._last_move_target = new_move

        self.status_message = f"Approaching target at ({int(tx)}, {int(ty)})"
        my_pos = Player.GetXY()
        if Utils.Distance(my_pos, (tx, ty)) <= Range.Area.value:
            self.status_message = "In combat range."

    def _advance_to_next_point(self):
        if not self.follow_handler.is_following():
            next_point = self.path_handler.advance()
            if not next_point:
                # SAFETY: No next point found
                self.status_message = "No valid next waypoint! Stopping pathing."
                if self.log_actions:
                    ConsoleLog("FollowPathAndAggro", "PathHandler returned None – halting movement.", Console.MessageType.Warning)
                
                # Optional fallback: reset to start or nearest point
                if hasattr(self.path_handler, "reset"):
                    self.path_handler.reset()  # resets to first node
                    retry_point = self.path_handler.advance()
                    if retry_point:
                        self._current_path_point = retry_point
                        self.follow_handler.move_to_waypoint(*retry_point)
                        self.status_message = f"Path reset → moving to {retry_point}"
                        ConsoleLog("FollowPathAndAggro", f"Path reset after failure, moving to {retry_point}", Console.MessageType.Warning)
                return  # do nothing else this tick
            
            # If we got a valid next_point
            self._current_path_point = next_point
            self.follow_handler.move_to_waypoint(*next_point)
            self.status_message = f"Moving to {next_point}"
            if self.log_actions:
                ConsoleLog("FollowPathAndAggro", f"Moving to {next_point}", Console.MessageType.Info)
        else:
            # SAFETY: make sure _current_path_point is valid
            if not self._current_path_point:
                self.status_message = "Lost current path point, hang on a second"
                if self.log_actions:
                    pass
                self.follow_handler._following = False
                return
            
            px, py = Player.GetXY()
            tx, ty = self._current_path_point
            if Utils.Distance((px, py), (tx, ty)) <= ARRIVAL_TOLERANCE:
                self.follow_handler._following = False
                self.follow_handler.arrived    = True
                self.status_message            = "Arrived at waypoint."

    def _maybe_log_stats(self):
        elapsed = time.time() - self._stats_start_time
        if elapsed >= self._stats_interval_secs:
            ConsoleLog(
                "FollowPathAndAggro",
                f"[Stats over {int(elapsed)}s] fetches={self.enemy_array_fetches}, "
                f"changeTarget={self.change_target_calls}, move={self.move_calls}",
                Console.MessageType.Info
            )
            # reset
            self._stats_start_time     = time.time()
            self.enemy_array_fetches   = 0
            self.change_target_calls   = 0
            self.move_calls            = 0

    def update(self):
        # periodically emit stats
        self._maybe_log_stats()

        if CacheData().in_looting_routine:
            self.status_message = "Waiting for looting to finish..."
            self.follow_handler.update()
            return

        # Mid-map blessing trigger
        if FSM_vars.blessing_points:
            px, py = Player.GetXY()
            for point in FSM_vars.blessing_points:
                if point in FSM_vars.blessing_triggered:
                    continue
                if Utils.Distance((px, py), point) < 1000:
                    self.status_message = f"Near blessing point {point}"
                    trigger_blessing_at(point)
                    break

        if self._mode == 'path':
            target = self._throttled_scan()
            if target:
                self._current_target_enemy = target
                self._last_enemy_check.Reset()
                self._mode = 'combat'
                self.status_message = "Switching to combat mode."
                if self.log_actions:
                    ConsoleLog("FollowPathAndAggro", "Switching to COMBAT mode", Console.MessageType.Warning)
            else:
                self._advance_to_next_point()

        elif self._mode == 'combat':
            if not self._current_target_enemy or not Agent.IsAlive(self._current_target_enemy):
                self._mode                  = 'path'
                self._current_target_enemy  = None
                self.status_message         = "Combat done. Switching to path mode."
                return

            # ── unified, throttled scan ──────────────────────────────
            self._current_target_enemy = self._throttled_scan()
            if not self._current_target_enemy:
                self._mode = 'path'
                self.status_message = "No enemies (throttled)—returning to path."
                return

            try:
                tx, ty = Agent.GetXY(self._current_target_enemy)
            except Exception:
                self._mode                 = 'path'
                self._current_target_enemy = None
                self.status_message        = "Enemy fetch failed. Returning to path."
                return

            # ── target only if it’s a new one ───────────────────────────
            if self._current_target_enemy != self._last_target_id:
                Player.ChangeTarget(self._current_target_enemy)
                self.change_target_calls += 1
                self._last_target_id = self._current_target_enemy

            # ── move only if the coords differ ──────────────────────────
            new_move = (int(tx), int(ty))
            if new_move != self._last_move_target:
                Player.Move(*new_move)
                self.move_calls += 1
                self._last_move_target = new_move

            self.status_message = f"Closing in on enemy at ({int(tx)}, {int(ty)})"

        # always let follow-handler tick
        self.follow_handler.update()

def load_map_script():
    region_path = os.path.join(MAPS_DIR, bot_vars.selected_region)
    map_file = os.path.join(region_path, f"{bot_vars.selected_map}.py")
    if not os.path.exists(map_file):
        ConsoleLog(module_name, f"[ERROR] Map script not found: {map_file}", Console.MessageType.Error)
        return

    spec = importlib.util.spec_from_file_location(bot_vars.selected_map, map_file)
    if spec is None or spec.loader is None:
        ConsoleLog(module_name, f"[ERROR] Failed to load map script: {map_file}", Console.MessageType.Error)
        return
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    data = getattr(mod, bot_vars.selected_map, [])
    outpost = getattr(mod, f"{bot_vars.selected_map}_outpost_path", [])
    ids = getattr(mod, f"{bot_vars.selected_map}_ids", {})

    # Blessing points detection
    bless_points = []
    if isinstance(data, list):
        for segment in data:
            if isinstance(segment, dict) and "bless" in segment:
                bless_points.append(segment["bless"])

    bot_vars.map_data = {
        "map_path": data,
        "outpost_path": outpost,
        "outpost_id": ids.get("outpost_id", OUTPOST_ID),
        "map_id": ids.get("map_id", MAP_ID)
    }

    FSM_vars.blessing_points = bless_points
    FSM_vars.outpost_pathing = Routines.Movement.PathHandler(bot_vars.map_data["outpost_path"])
    FSM_vars.explorable_pathing = Routines.Movement.PathHandler(merge_map_segments(bot_vars.map_data["map_path"]))
    FSM_vars.path_and_aggro = FollowPathAndAggro(FSM_vars.explorable_pathing, FSM_vars.movement_handler, aggro_range=2500, log_actions=True)
    bot_vars.starting_map = bot_vars.map_data["outpost_id"]

def merge_map_segments(data):
    if isinstance(data, list) and all(isinstance(x, dict) for x in data):
        all_coords = []
        for segment in data:
            all_coords.extend(segment.get("path", []))
        return all_coords
    elif isinstance(data, list):
        return data
    return []

# Add combat control functions



def check_combat():
    return Routines.Checks.Agents.InDanger(Range.Area)

def start_combat(): 
    bot_vars.combat_started = True

def stop_combat(): 
    bot_vars.combat_started = False

def pause_all(debug: bool = False):
    if not check_combat():
        return
    if not FSM_vars.state_machine.is_paused():
        if debug: ConsoleLog("FSM", "[DEBUG] Pausing Main FSM", Console.MessageType.Warning)
        FSM_vars.state_machine.pause()
    FSM_vars.movement_handler.pause()

def resume_all(debug: bool = False):
    if check_combat():
        return
    if FSM_vars.state_machine.is_paused():
        if debug:
            ConsoleLog("FSM", "[DEBUG] Resuming Main FSM", Console.MessageType.Warning)
        FSM_vars.state_machine.resume()

    FSM_vars.movement_handler.resume()

# Modify InitializeStateMachine
def InitializeStateMachine():
    # Combat FSM setup
    FSM_vars.global_combat_fsm.SetLogBehavior(False)
    FSM_vars.global_combat_fsm.AddState(
        name="Check: In Danger",
        execute_fn=lambda: pause_all(),
        exit_condition=check_combat,
        run_once=False)
    FSM_vars.global_combat_fsm.AddSubroutine(
        name="Combat: Execute Global",
        condition_fn=lambda: check_combat(),
        sub_fsm=FSM_vars.global_combat_handler)
    FSM_vars.global_combat_fsm.AddState(
        name="Resume: Main FSM",
        execute_fn=lambda: resume_all(),
        exit_condition=lambda: not check_combat(),
        run_once=False)

    FSM_vars.global_combat_handler.SetLogBehavior(False)
    FSM_vars.global_combat_handler.AddState(
        name="Combat: Wait Safe",
        execute_fn=lambda: None,
        exit_condition=lambda: not check_combat(),
        run_once=False)
    FSM_vars.global_combat_handler.AddState(
        name="Combat: Stop",
        execute_fn=lambda: stop_combat(),
        exit_condition=lambda: True)

    # Primary flow states
    FSM_vars.state_machine.AddState(
        name="Check Current Map",
        execute_fn= lambda: Routines.Transition.TravelToOutpost(bot_vars.starting_map),
        exit_condition= lambda: Routines.Transition.HasArrivedToOutpost(bot_vars.starting_map),
        transition_delay_ms=1000
    )
    FSM_vars.state_machine.AddState(
        name="Wait For Map Load",
        exit_condition=lambda: not Map.IsMapLoading(),
        transition_delay_ms=1000
    )
    FSM_vars.state_machine.AddState(
        name="Navigate Outpost",
        execute_fn=lambda: Routines.Movement.FollowPath(
            FSM_vars.outpost_pathing, FSM_vars.movement_handler
        ),
        exit_condition=lambda: (
            Routines.Movement.IsFollowPathFinished(FSM_vars.outpost_pathing, FSM_vars.movement_handler)
            or Map.IsExplorable()
        ),
        run_once=False
    )
    FSM_vars.state_machine.AddState(
        name="Wait For Explorable Load",
        exit_condition=lambda: not Map.IsMapLoading() and Map.IsExplorable(),
        transition_delay_ms=1000
    )
    FSM_vars.state_machine.AddState(
        name="Initial Auto-Blessing",
        execute_fn=lambda: Get_Blessed(),
        exit_condition=lambda: has_any_blessing(Player.GetAgentID()) or Map.IsMapLoading() or (get_blessing_npc()[0] is None),
        transition_delay_ms=5000,
        run_once=True
    )
    FSM_vars.state_machine.AddState(
        name="Combat and Movement",
        execute_fn=lambda: FSM_vars.path_and_aggro.update(),
        exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.explorable_pathing, FSM_vars.movement_handler),
        run_once=False
    )

def ResetEnvironment():
    FSM_vars.outpost_pathing.reset()
    FSM_vars.explorable_pathing.reset()
    FSM_vars.blessing_triggered.clear()
    FSM_vars.blessing_timers.clear()
    FSM_vars.movement_handler.reset()
    if bot_vars.combat_started:
        stop_combat()
    # Remove the combat_handler.reset_all() call as it doesn't exist

# --------------------------------------------------------------------------------------------------
# NEW THEME COLORS (rename to English‐friendly names)
# --------------------------------------------------------------------------------------------------

# 1) Window & Frame backgrounds (dark charcoal, slightly translucent)
window_bg_color       = Color(28,  28,  28, 230).to_tuple_normalized()
frame_bg_color        = Color(48,  48,  48, 230).to_tuple_normalized()
frame_hover_color     = Color(68,  68,  68, 230).to_tuple_normalized()
frame_active_color    = Color(58,  58,  58, 230).to_tuple_normalized()

# 2) Body text (off‐white for maximum readability)
body_text_color       = Color(139, 131, 99, 255).to_tuple_normalized()

# 3) Disabled text (mid‐gray for grayed‐out buttons)
disabled_text_color   = Color(140, 140, 140, 255).to_tuple_normalized()

# 4) Separator lines (medium‐gray)
separator_color       = Color(90,  90,  90, 255).to_tuple_normalized()

# 5) Header text (use the same bright off‐white as body, or tweak to slightly brighter)
header_color          = Color(136, 117, 44, 255).to_tuple_normalized()  # “Statistics:” style: pale gold
#    You can change (251,241,166) to any off‐white / pale‐yellow RGB you like.

# 6) Icon accent color (a more “exciting” golden‐teal that fits the palette)
icon_color            = Color(177, 152, 55, 255).to_tuple_normalized()

# 7) Neutral button colors (light gray → slightly brighter on hover → slightly darker on active)
neutral_button        = Color(33, 51, 58, 255).to_tuple_normalized()  # default button
neutral_button_hover  = Color(140, 140, 140, 255).to_tuple_normalized()  # hovered
neutral_button_active = Color( 90,  90,  90, 255).to_tuple_normalized()  # pressed

# 8) Combo‐box header (still a dark green tint, if you prefer; otherwise gray)
header_bg_color       = Color(33, 51, 58, 255).to_tuple_normalized()
header_hover_color    = Color(33, 51, 58, 255).to_tuple_normalized()
header_active_color   = Color(95, 145,  95, 255).to_tuple_normalized()


# --------------------------------------------------------------------------------------------------
# UPDATED DrawWindow() WITH EVERY ICON & HEADING COLORED
# --------------------------------------------------------------------------------------------------

def DrawWindow():
    """Renders a single, themed ImGui window using our new neutral‐gray buttons,
    pale‐gold headings, off‐white body text, and punchy icon color."""
    # 1) Begin the window
    if not PyImGui.begin(module_name, PyImGui.WindowFlags.AlwaysAutoResize):
        PyImGui.end()
        return

    # 2) Push “global” style colors: WindowBg, FrameBg, FrameBgHovered, FrameBgActive, Text, Separator
    PyImGui.push_style_color(PyImGui.ImGuiCol.WindowBg,       window_bg_color)   # push #1
    PyImGui.push_style_color(PyImGui.ImGuiCol.FrameBg,        frame_bg_color)    # push #2
    PyImGui.push_style_color(PyImGui.ImGuiCol.FrameBgHovered, frame_hover_color) # push #3
    PyImGui.push_style_color(PyImGui.ImGuiCol.FrameBgActive,  frame_active_color)# push #4
    PyImGui.push_style_color(PyImGui.ImGuiCol.Text,           body_text_color)   # push #5
    PyImGui.push_style_color(PyImGui.ImGuiCol.Separator,      separator_color)   # push #6

    # 3) Push “combo header” colors (if you still want a greenish tint for dropdowns):
    PyImGui.push_style_color(PyImGui.ImGuiCol.Header,         header_bg_color)   # push #7
    PyImGui.push_style_color(PyImGui.ImGuiCol.HeaderHovered,  header_hover_color)# push #8
    PyImGui.push_style_color(PyImGui.ImGuiCol.HeaderActive,   header_active_color)# push #9

    # 4) Push “button accent” colors (now neutral grays)
    PyImGui.push_style_color(PyImGui.ImGuiCol.Button,         neutral_button)         # push #10
    PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonHovered,  neutral_button_hover)   # push #11
    PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonActive,   neutral_button_active)  # push #12

    # --------------------------------
    # BEGIN DRAWING ALL WIDGETS
    # --------------------------------

    # ---- Start / Stop Button ----
    #   Renders in neutral gray by default; changes on hover/press.
    btn_label = (
        "Start bot " + IconsFontAwesome5.ICON_PLAY_CIRCLE
        if not bot_vars.is_running
        else "Stop bot  " + IconsFontAwesome5.ICON_STOP_CIRCLE
    )
    if PyImGui.button(btn_label, width=140):
        if not bot_vars.is_running:
            StartBot()
        else:
            StopBot()

    # ---- Pause / Resume Button (same line) ----
    PyImGui.same_line(0, 5)
    if not bot_vars.is_running:
        # Bot not running → render “Pause bot” in disabled gray
        PyImGui.push_style_color(PyImGui.ImGuiCol.Text, disabled_text_color)  # push #13
        PyImGui.button("Pause bot  " + IconsFontAwesome5.ICON_PAUSE_CIRCLE, width=140)
        PyImGui.pop_style_color(1)  # pop that single “Text” change
    else:
        pause_label = "Pause bot  " + IconsFontAwesome5.ICON_PAUSE_CIRCLE
        if PyImGui.button(pause_label, width=140):
            TogglePause()

    PyImGui.separator()

    # ---- Select Region (Icon + Heading) ----
    #   Icon in punchy accent color:
    PyImGui.push_style_color(PyImGui.ImGuiCol.Text, icon_color)       # push #14
    PyImGui.text(IconsFontAwesome5.ICON_GLOBE_EUROPE)
    PyImGui.pop_style_color(1)

    #   Heading “Select Region:” in pale‐gold
    PyImGui.same_line(0, 3)
    PyImGui.push_style_color(PyImGui.ImGuiCol.Text, header_color)     # push #15
    PyImGui.text("Select Region:")
    PyImGui.pop_style_color(1)

    #   Combo itself uses frame_bg_color + body_text_color (already pushed)

    regions = sorted([d for d in os.listdir(MAPS_DIR) if os.path.isdir(os.path.join(MAPS_DIR, d))])
    if bot_vars.selected_region in regions:
        region_index = regions.index(bot_vars.selected_region)
    else:
        region_index = 0

    region_index = PyImGui.combo("##Region", region_index, regions)
    if region_index < len(regions):
        new_region = regions[region_index]
        if bot_vars.selected_region != new_region:
            bot_vars.selected_region = new_region
            bot_vars.selected_map = ""

    # ---- Select Map (Icon + Heading) ----
    if bot_vars.selected_region:
        # Icon in punchy accent:
        PyImGui.push_style_color(PyImGui.ImGuiCol.Text, icon_color)   # push #16
        PyImGui.text(IconsFontAwesome5.ICON_MAP)
        PyImGui.pop_style_color(1)

        # Heading “Select Map:” in pale‐gold
        PyImGui.same_line(0, 3)
        PyImGui.push_style_color(PyImGui.ImGuiCol.Text, header_color) # push #17
        PyImGui.text("Select Map:")
        PyImGui.pop_style_color(1)

        maps = sorted([
            f[:-3] for f in os.listdir(os.path.join(MAPS_DIR, bot_vars.selected_region))
            if f.endswith(".py")
        ])
        if bot_vars.selected_map in maps:
            map_index = maps.index(bot_vars.selected_map)
        else:
            map_index = 0

        map_index = PyImGui.combo("##Map", map_index, maps)
        if map_index < len(maps):
            new_map = maps[map_index]
            if bot_vars.selected_map != new_map:
                bot_vars.selected_map = new_map
                load_map_script()

    PyImGui.separator()

    # ---- Current State (Heading Only) ----
    PyImGui.push_style_color(PyImGui.ImGuiCol.Text, header_color)      # push #18
    PyImGui.text("Current State:")
    PyImGui.pop_style_color(1)

    current_state = FSM_vars.state_machine.get_current_step_name()
    PyImGui.text(f"{current_state}")
    if current_state == "Combat and Movement":
        PyImGui.text(f"> {FSM_vars.path_and_aggro.status_message}")

    PyImGui.separator()

    # ---- Statistics (Icon + Heading) ----
    PyImGui.push_style_color(PyImGui.ImGuiCol.Text, icon_color)         # push #19
    PyImGui.text(IconsFontAwesome5.ICON_LIST_ALT)
    PyImGui.pop_style_color(1)

    PyImGui.same_line(0, 3)
    PyImGui.push_style_color(PyImGui.ImGuiCol.Text, header_color)      # push #20
    PyImGui.text("Statistics:")
    PyImGui.pop_style_color(1)

    if bot_vars.is_running:
        PyImGui.text(f"Total Time: {FormatTime(bot_vars.global_timer.GetElapsedTime(), 'hh:mm:ss')}")
        PyImGui.text(f"Current Run: {FormatTime(bot_vars.lap_timer.GetElapsedTime(), 'mm:ss')}")
        draw_vanquish_status("Vanquish Progress")

    if bot_vars.runs_attempted > 0:
        PyImGui.text(f"Runs Attempted: {bot_vars.runs_attempted}")
        PyImGui.text(f"Runs Completed: {bot_vars.runs_completed}")
        PyImGui.text(f"Success Rate: {bot_vars.success_rate * 100:.1f}%")
        if bot_vars.lap_history:
            PyImGui.text(f"Best Time: {FormatTime(bot_vars.min_time, 'mm:ss')}")
            PyImGui.text(f"Worst Time: {FormatTime(bot_vars.max_time, 'mm:ss')}")
            PyImGui.text(f"Average Time: {FormatTime(bot_vars.avg_time, 'mm:ss')}")

    PyImGui.separator()

    # ---- Title / Allegiance (Icon + Heading) ----
    PyImGui.push_style_color(PyImGui.ImGuiCol.Text, icon_color)         # push #21
    PyImGui.text(IconsFontAwesome5.ICON_TROPHY)
    PyImGui.pop_style_color(1)

    PyImGui.same_line(0, 5)
    PyImGui.push_style_color(PyImGui.ImGuiCol.Text, header_color)      # push #22
    PyImGui.text("Title / Allegiance:")
    PyImGui.pop_style_color(1)

    # Now use display_title_progress(...) as before
    region = bot_vars.selected_region
    if region in kurzick_regions:
        display_faction("Kurzick", 5, Player.GetKurzickData, kurzick_tiers)
    elif region in luxon_regions:
        display_faction("Luxon", 6, Player.GetLuxonData, luxon_tiers)
    elif region in nightfall_regions:
        display_title_progress("Sunspear Title", 17, sunspear_tiers)
        display_title_progress("Lightbringer Title", 20, lightbringer_tiers)
    elif region in eotn_region_titles:
        for title_id, title_name, tier_data in eotn_region_titles[region]:
            display_title_progress(title_name, title_id, tier_data)

    PyImGui.separator()

    # --------------------------------
    # POP ALL THE STYLE COLORS WE PUSHED (in reverse order)
    # --------------------------------
    # We pushed 22 times (counts 1..22). Pop in reverse groups:
    PyImGui.pop_style_color(3)   # unwinds neutral_button, neutral_button_hover, neutral_button_active (#10,#11,#12)
    PyImGui.pop_style_color(3)   # unwinds header_bg_color, header_hover_color, header_active_color (#7,#8,#9)
    PyImGui.pop_style_color(6)   # unwinds window_bg_color, frame_bg_color, frame_hover_color, frame_active_color, body_text_color, separator_color (#1..#6)
    # (Note: the 13–22 pushes were popped inline, so no need to pop them here.)

    PyImGui.end()



def main():
    try:
        DrawWindow()
        
        if not bot_vars.is_running or bot_vars.is_paused:
            return
        
        if Map.IsMapLoading():
            FSM_vars.movement_handler.reset()
            return
        
        if FSM_vars.global_combat_fsm.is_finished():
            FSM_vars.global_combat_fsm.reset()
            return
        
        if Map.IsExplorable():
            if bot_vars.combat_started:
                combat_handler.HandleCombat()

        ActionQueueManager().ProcessAll()
        
        if not bot_vars.pause_combat_fsm:
            FSM_vars.global_combat_fsm.update()
        FSM_vars.state_machine.update()
        
    except Exception as e:
        ConsoleLog(module_name, f"Error in main: {str(e)}", Console.MessageType.Error)
        raise

def StartBot():
    global bot_vars, FSM_vars
    
    # First initialize state machines if needed
    if FSM_vars.state_machine.get_state_count() == 0:
        InitializeStateMachine()
    
    # Then reset all variables and states
    FSM_vars.has_blessing = False
    FSM_vars.in_blessing_dialog = False
    FSM_vars.blessing_timer.Stop()
    FSM_vars.movement_handler.reset()
    FSM_vars.outpost_pathing.reset()
    FSM_vars.explorable_pathing.reset()
    
    # Force return to outpost if not already there
    if Map.GetMapID() != bot_vars.starting_map:
        Routines.Transition.TravelToOutpost(bot_vars.starting_map)
    
    # Reset state machines after initialization
    FSM_vars.state_machine.reset()
    FSM_vars.global_combat_fsm.reset()
    FSM_vars.global_combat_handler.reset()
    
    bot_vars.is_running = True
    bot_vars.combat_started = False
    bot_vars.global_timer.Start()
    bot_vars.lap_timer.Start()
    
    # Start the state machines
    FSM_vars.state_machine.start()
    FSM_vars.global_combat_fsm.start()

# Add new Pause control functions
def TogglePause():
    if bot_vars.is_paused:
        ResumeBotExecution()
    else:
        PauseBotExecution()

def PauseBotExecution():
    if not bot_vars.is_running:
        return
    
    bot_vars.is_paused = True
    FSM_vars.state_machine.pause()
    FSM_vars.global_combat_fsm.pause()
    FSM_vars.movement_handler.pause()
    ConsoleLog(module_name, "Bot Paused", Console.MessageType.Info)

def ResumeBotExecution():
    if not bot_vars.is_running:
        return
    
    bot_vars.is_paused = False
    FSM_vars.state_machine.resume()
    FSM_vars.global_combat_fsm.resume()
    FSM_vars.movement_handler.resume()
    ConsoleLog(module_name, "Bot Resumed", Console.MessageType.Info)

def StopBot():
    global bot_vars, FSM_vars
    bot_vars.is_running = False
    bot_vars.is_paused = False  # Reset pause state when stopping
    bot_vars.global_timer.Stop()
    bot_vars.lap_timer.Stop()
    FSM_vars.state_machine.stop()
    FSM_vars.global_combat_fsm.stop()
    if bot_vars.combat_started:
        stop_combat()
    ResetEnvironment()

# Initialize the global instances
FSM_vars = FSMVars()
bot_vars = BotVars()
