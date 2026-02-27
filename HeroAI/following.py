"""
HeroAI Following Module — Leader-Driven Follow Logic

The leader calculates formation positions for all followers and writes them
to shared memory (HeroAIOptionStruct.FollowPos).  Each follower simply reads
its own assigned position and moves there.

Also contains the leader-only config window with per-follower angle control,
formation canvas preview, and 3D overlay visualization.
"""

import Py4GW
import PyImGui
import math
import random
import time

from Py4GWCoreLib.ImGui import ImGui
from Py4GWCoreLib.Agent import Agent
from Py4GWCoreLib.Player import Player
from Py4GWCoreLib.enums_src.GameData_enums import Range
from Py4GWCoreLib.py4gwcorelib_src.Color import Color, ColorPalette
from Py4GWCoreLib.Overlay import Overlay
from Py4GWCoreLib.IniManager import IniManager
from Py4GWCoreLib.Pathing import AutoPathing, AStar, NavMesh
from Py4GWCoreLib import ActionQueueManager
from Py4GWCoreLib import Utils
from Py4GWCoreLib import GLOBAL_CACHE
from Py4GWCoreLib.native_src.internals.types import Vec2f

from HeroAI.cache_data import CacheData
from HeroAI.settings import Settings
from HeroAI.constants import (
    MODULE_NAME,
    MELEE_RANGE_VALUE,
    RANGED_RANGE_VALUE,
    FOLLOW_DISTANCE_OUT_OF_COMBAT,
)

# ─────────────────────────────────────────────
# Constants
# ─────────────────────────────────────────────
FOLLOW_COMBAT_DISTANCE = 25.0  # body-block close range when flagged
MAX_FOLLOWERS = 8

# ─────────────────────────────────────────────
# INI persistence
# ─────────────────────────────────────────────
INI_DIR = "HeroAI"
INI_FILENAME = "FollowModule.ini"
_ini_key = ""

# ─────────────────────────────────────────────
# Ring config (merged from FollowingModule.py)
# ─────────────────────────────────────────────
class RingConfig:
    def __init__(self, radius, color: Color, thickness, show=True):
        if isinstance(radius, Range):
            self.caption = radius.name
            self.radius = radius.value
        else:
            self.caption = f"{radius:.0f}"
            self.radius = float(radius)
        self.show = show
        self.color: Color = color
        self.thickness = thickness


# ─────────────────────────────────────────────
# Per-follower config
# ─────────────────────────────────────────────
class FollowerConfig:
    """Per-follower formation settings controlled by the leader."""
    def __init__(self, angle_deg: float = 0.0, radius: float = -1.0, color: Color = None, enabled: bool = True):
        self.angle_deg = angle_deg
        self.radius = radius  # -1 means use global formation_radius
        self.color: Color = color or ColorPalette.GetColor("white")
        self.enabled = enabled

    def get_radius(self, global_radius: float) -> float:
        """Return this follower's radius, falling back to global if -1."""
        return self.radius if self.radius >= 0 else global_radius


# ─────────────────────────────────────────────
# Module-level settings
# ─────────────────────────────────────────────
class FollowModuleSettings:
    """All leader-configurable follow settings."""

    # Default formation angles (same layout as the old hero_formation)
    DEFAULT_ANGLES = [0.0, 45.0, -45.0, 90.0, -90.0, 135.0, -135.0, 180.0]

    def __init__(self):
        # Formation
        self.formation_radius: float = Range.Touch.value  # distance from leader
        self.follow_distance_ooc: float = FOLLOW_DISTANCE_OUT_OF_COMBAT
        self.follow_distance_combat: float = MELEE_RANGE_VALUE
        self.confirm_follow_point: bool = False
        self.follow_enabled: bool = True

        # Per-follower angle configs (index = party slot)
        self.follower_configs: list[FollowerConfig] = []
        for i, angle in enumerate(self.DEFAULT_ANGLES):
            palette_colors = ["gw_blue", "firebrick", "gold", "gw_purple",
                              "gw_green", "gw_assassin", "blue", "white"]
            color = ColorPalette.GetColor(palette_colors[i % len(palette_colors)])
            self.follower_configs.append(FollowerConfig(angle, color=color))

        # Canvas / visualization
        self.show_canvas: bool = True
        self.canvas_size: tuple = (400, 400)
        self.scale: float = 0.3
        self.draw_area_rings: bool = True
        self.draw_3d_overlay: bool = True
        self.area_rings: list[RingConfig] = [
            RingConfig(Range.Touch.value / 2, ColorPalette.GetColor("gw_green"), 2),
            RingConfig(Range.Touch, ColorPalette.GetColor("gw_assassin"), 2, False),
            RingConfig(Range.Adjacent, ColorPalette.GetColor("gw_blue"), 2),
            RingConfig(Range.Nearby, ColorPalette.GetColor("blue"), 2),
            RingConfig(Range.Area, ColorPalette.GetColor("firebrick"), 2),
            RingConfig(Range.Earshot, ColorPalette.GetColor("gw_purple"), 2, False),
            RingConfig(Range.Spellcast, ColorPalette.GetColor("gold"), 2, False),
        ]

        # UI state
        self.show_config_window: bool = False


settings = FollowModuleSettings()

# Map pathing quads cache (populated once per map)
_map_quads: list = []


# ─────────────────────────────────────────────
# INI Persistence helpers
# ─────────────────────────────────────────────
def _ensure_ini():
    global _ini_key
    if not _ini_key:
        _ini_key = IniManager().AddIniHandler(INI_DIR, INI_FILENAME)
        if _ini_key:
            _load_settings()


def _save_settings():
    if not _ini_key:
        return
    ini = IniManager()
    ini.write_key(_ini_key, "Formation", "Radius", settings.formation_radius)
    ini.write_key(_ini_key, "Formation", "DistanceOOC", settings.follow_distance_ooc)
    ini.write_key(_ini_key, "Formation", "DistanceCombat", settings.follow_distance_combat)
    ini.write_key(_ini_key, "Formation", "ConfirmFollowPoint", settings.confirm_follow_point)

    ini.write_key(_ini_key, "Formation", "FollowEnabled", settings.follow_enabled)
    
    # Per-follower angles
    for i, fc in enumerate(settings.follower_configs):
        ini.write_key(_ini_key, "Followers", f"Angle_{i}", fc.angle_deg)
        ini.write_key(_ini_key, "Followers", f"Radius_{i}", fc.radius)
        ini.write_key(_ini_key, "Followers", f"Enabled_{i}", fc.enabled)

    # Canvas settings
    ini.write_key(_ini_key, "Canvas", "Show", settings.show_canvas)
    ini.write_key(_ini_key, "Canvas", "Scale", settings.scale)
    ini.write_key(_ini_key, "Canvas", "Draw3D", settings.draw_3d_overlay)
    ini.write_key(_ini_key, "Canvas", "DrawRings", settings.draw_area_rings)


def _load_settings():
    if not _ini_key:
        return
    ini = IniManager()

    settings.formation_radius = ini.read_float(_ini_key, "Formation", "Radius", Range.Touch.value)
    settings.follow_distance_ooc = ini.read_float(_ini_key, "Formation", "DistanceOOC", FOLLOW_DISTANCE_OUT_OF_COMBAT)
    settings.follow_distance_combat = ini.read_float(_ini_key, "Formation", "DistanceCombat", MELEE_RANGE_VALUE)
    settings.confirm_follow_point = ini.read_bool(_ini_key, "Formation", "ConfirmFollowPoint", False)
    settings.follow_enabled = ini.read_bool(_ini_key, "Formation", "FollowEnabled", True)
    
    for i, fc in enumerate(settings.follower_configs):
        fc.angle_deg = ini.read_float(_ini_key, "Followers", f"Angle_{i}", fc.angle_deg)
        fc.radius = ini.read_float(_ini_key, "Followers", f"Radius_{i}", fc.radius)
        fc.enabled = ini.read_bool(_ini_key, "Followers", f"Enabled_{i}", fc.enabled)

    settings.show_canvas = ini.read_bool(_ini_key, "Canvas", "Show", True)
    settings.scale = ini.read_float(_ini_key, "Canvas", "Scale", 0.3)
    settings.draw_3d_overlay = ini.read_bool(_ini_key, "Canvas", "Draw3D", True)
    settings.draw_area_rings = ini.read_bool(_ini_key, "Canvas", "DrawRings", True)


# ─────────────────────────────────────────────
# Map pathing validation
# ─────────────────────────────────────────────
def _is_position_on_map(x: float, y: float) -> bool:
    """Check if a position is on a walkable map quad."""
    global _map_quads
    if not settings.confirm_follow_point:
        return True
    
    # Global Toggle Check
    if not Settings().advanced_pathing_enabled:
        return True

    if not _map_quads:
        _map_quads = Map.Pathing.GetMapQuads()
    for quad in _map_quads:
        if Map.Pathing._point_in_quad(x, y, quad):
            return True
    return False


def reset_map_quads():
    """Call when map changes to clear cached pathing data."""
    global _map_quads, follower_states
    _map_quads = []
    if 'follower_states' in globals():
        follower_states.clear()


# ─────────────────────────────────────────────
# LEADER UPDATE — calculates & writes follow positions
# ─────────────────────────────────────────────
def LeaderUpdate(cached_data: CacheData):
    """
    Run on the leader's client each tick.
    them to shared memory via HeroAIOptionStruct.FollowPos.
    """
    _ensure_ini()
    
    if not settings.follow_enabled:
        return

    leader_id = GLOBAL_CACHE.Party.GetPartyLeaderID()
    if Player.GetAgentID() != leader_id:
        return  # not leader
    
    leader_x, leader_y = Agent.GetXY(leader_id)
    leader_angle = Agent.GetRotationAngle(leader_id)

    # Validate leader position
    point_zero = (0.0, 0.0)
    if Utils.Distance((leader_x, leader_y), point_zero) <= 5:
        return  # leader at origin, skip

    leader_options = GLOBAL_CACHE.ShMem.GetGerHeroAIOptionsByPartyNumber(0)
    
    # Broadcast targeting mode to all followers via leader's FollowPos.x
    if leader_options:
        leader_options.FollowPos.x = float(Settings().targeting_mode.value)

    # Iterate over all party accounts
    for acc in cached_data.party:
        if not acc.IsSlotActive:
            continue
        if acc.PlayerID == leader_id:
            continue  # skip self (leader)

        # Get this follower's HeroAI options from shared memory
        follower_options = GLOBAL_CACHE.ShMem.GetHeroAIOptions(acc.AccountEmail)
        if follower_options is None:
            continue

        if not follower_options.Following:
            continue  # following disabled for this follower

        # Determine follow target
        follow_x = 0.0
        follow_y = 0.0
        follow_angle = leader_angle
        is_following_flag = False

        if follower_options.IsFlagged:
            # Follower's own flag takes priority
            follow_x = follower_options.FlagPosX
            follow_y = follower_options.FlagPosY
            follow_angle = follower_options.FlagFacingAngle
            is_following_flag = True
        elif leader_options and leader_options.IsFlagged:
            # Leader's flag
            follow_x = leader_options.FlagPosX
            follow_y = leader_options.FlagPosY
            follow_angle = leader_options.FlagFacingAngle
        else:
            # Follow leader directly
            follow_x = leader_x
            follow_y = leader_y
            follow_angle = leader_angle

        # Calculate formation offset position
        if is_following_flag:
            # Go directly to flag position
            xx = follow_x
            yy = follow_y
        else:
            # Get per-follower angle config
            follower_grid_pos = acc.PartyPosition + GLOBAL_CACHE.Party.GetHeroCount() + GLOBAL_CACHE.Party.GetHenchmanCount()
            angle_deg = 0.0
            fc = None
            if follower_grid_pos < len(settings.follower_configs):
                fc = settings.follower_configs[follower_grid_pos]
                if not fc.enabled:
                    xx = follow_x
                    yy = follow_y
                    # Skip calculation if disabled, just follow directly
                else:
                    angle_deg = fc.angle_deg
            
            if fc and fc.enabled:
                # Convert to radians and add to leader's facing
                # 0 degrees = Forward
                angle_rad = Utils.DegToRad(angle_deg)
                world_angle = follow_angle + angle_rad
                
                radius = fc.get_radius(settings.formation_radius)
                
                # Standard rotation mapping (0=East, pi/2=North)
                rot_x = radius * math.cos(world_angle)
                rot_y = radius * math.sin(world_angle)
                
                xx = follow_x + rot_x
                yy = follow_y + rot_y
            else:
                xx = follow_x
                yy = follow_y

            # Validate against map pathing
            if not _is_position_on_map(xx, yy):
                # Fallback to direct follow position
                xx = follow_x
                yy = follow_y

        # Write calculated position to shared memory
        # Leader-side distance gating: only update FollowPos if the follower
        # is far enough from the target that they need to move
        follower_x = acc.PlayerPosX
        follower_y = acc.PlayerPosY
        dist_to_target = Utils.Distance((xx, yy), (follower_x, follower_y))

        # Determine appropriate follow distance threshold
        if is_following_flag:
            threshold = 0.0  # always move to flag
        elif cached_data.data.in_aggro:
            if Agent.IsMelee(acc.PlayerID):
                threshold = MELEE_RANGE_VALUE
            else:
                threshold = RANGED_RANGE_VALUE
        else:
            threshold = settings.follow_distance_ooc

        if dist_to_target > threshold:
            follower_options.FollowPos = Vec2f(xx, yy)
        else:
            follower_options.FollowPos = Vec2f(0.0, 0.0)  # signal: no move needed


# ─────────────────────────────────────────────
# FOLLOW — follower reads assigned position and moves
# ─────────────────────────────────────────────
following_flag = False

class FollowerState:
    def __init__(self):
        self.last_pos = (0.0, 0.0)
        self.last_move_time = 0.0
        self.stuck_start_time = 0.0
        self.is_stuck = False
        self.path = []
        self.path_index = 0
        self.last_path_calc_time = 0.0
        self.last_target_pos = (0.0, 0.0)
        self.unstuck_target = None
        self.unstuck_timestamp = 0.0
        self.unstuck_attempt_count = 0
        self.last_unstuck_time = 0.0 # Track when we last successfully unstuck

follower_states = {}  # agent_id -> FollowerState

def Follow(cached_data: CacheData) -> bool:
    """
    BT ActionNode — runs on each follower.
    Reads the leader-assigned FollowPos from shared memory and moves there.
    Handles obstacle avoidance via local NavMesh A* and unstuck logic.
    Returns True if a move was issued, False otherwise.
    """
    global following_flag, follower_states

    options = cached_data.account_options
    if not options or not options.Following:
        return False
        
    my_agent_id = Player.GetAgentID()
    if my_agent_id == GLOBAL_CACHE.Party.GetPartyLeaderID():
        # Leader logic handled elsewhere or skipped
        cached_data.follow_throttle_timer.Reset()
        return False

    if not cached_data.follow_throttle_timer.IsExpired():
        return False

    # Check for global setting updates (e.g. toggle enabled/disabled)
    Settings().check_for_updates()

    # Initialize state if needed
    if my_agent_id not in follower_states:
        follower_states[my_agent_id] = FollowerState()
        follower_states[my_agent_id].last_update_time = 0.0
        
    state = follower_states[my_agent_id]
    
    current_time = time.time()
    
    # Check for resumption after pause (e.g. toggle off/on)
    # Check for resumption after pause (e.g. toggle off/on)
    # Increased to 5.0s to avoid resetting on normal 1.0s throttle intervals
    if (current_time - getattr(state, 'last_update_time', 0.0)) > 5.0:
        # Reset stuck state
        if state.stuck_start_time != 0.0:
            Py4GW.Console.Log("HeroAI", f"Follower {my_agent_id}: Stuck State RESET due to inactivity/pause > 5.0s", Py4GW.Console.MessageType.Info)
        state.is_stuck = False
        state.stuck_start_time = 0.0
        state.unstuck_target = None
        state.unstuck_attempt_count = 0
        state.path = []
        
    state.last_update_time = current_time
     
    # Read assigned position from shared memory
    follow_pos = options.FollowPos
    target_x = follow_pos.x
    target_y = follow_pos.y

    # (0,0) signal check
    if Utils.Distance((target_x, target_y), (0.0, 0.0)) <= 5:
        state.path = [] # Clear path if stopped
        return False

    if not Agent.IsValid(GLOBAL_CACHE.Party.GetPartyLeaderID()):
        return False

    following_flag = options.IsFlagged
    my_x, my_y = Agent.GetXY(my_agent_id)
    my_z = Agent.GetZPlane(my_agent_id) # Z needed for pathing sometimes? mostly 2D here
    
    # --- STRICT DEACTIVATION FALLBACK ---
    # If the module is off, bypass all custom pathing/unstuck logic and do "normal" follow.
    if not Settings().advanced_pathing_enabled:
        state.path = [] # Clear cached path data
        state.is_stuck = False
        state.stuck_start_time = 0.0
        state.unstuck_target = None
        state.unstuck_attempt_count = 0
        
        dist_to_target = Utils.Distance((target_x, target_y), (my_x, my_y))
        if dist_to_target < 50:
            return False
            
        ActionQueueManager().ResetQueue("ACTION")
        Player.Move(target_x, target_y)
        return True

    current_time = time.time()

    # --- 0.5. VALIDATE TARGET ON NAVMESH ---
    # Check if target is valid on NavMesh to prevent "Invalid start or goal trapezoid" and stuck loops
    if Settings().advanced_pathing_enabled:
        navmesh = AutoPathing().get_navmesh()
        if navmesh:
            target_id = navmesh.find_trapezoid_id_by_coord((target_x, target_y))
            if not target_id:
                # Target is off-mesh (wall/obstacle). Pull towards leader until valid.
                leader_id = GLOBAL_CACHE.Party.GetPartyLeaderID()
                if Agent.IsValid(leader_id):
                    lx, ly = Agent.GetXY(leader_id)
                    found_valid = False
                    # Try 5 steps from target to leader
                    for i in range(1, 6):
                        factor = i / 5.0
                        check_x = target_x + (lx - target_x) * factor
                        check_y = target_y + (ly - target_y) * factor
                        if navmesh.find_trapezoid_id_by_coord((check_x, check_y)):
                            target_x, target_y = check_x, check_y
                            found_valid = True
                            # Py4GW.Console.Log("HeroAI", f"Adjusted off-mesh target to valid point ({target_x:.1f}, {target_y:.1f})", Py4GW.Console.MessageType.Info)
                            break
                    
                    if not found_valid:
                         # worst case, go to leader
                         target_x, target_y = lx, ly

    # --- 1. UNSTUCK LOGIC ---
    # Detect if we should be moving but aren't
    dist_to_target = Utils.Distance((target_x, target_y), (my_x, my_y))
    
    # If we are far enough to move
    if dist_to_target > 50:
        # Check if we moved significantly since last check
        dist_moved = Utils.Distance((my_x, my_y), state.last_pos)
        
        # Hypersensitive Mode: If we were stuck recently (<10s), check faster!
        # Normal: Check every 0.75s, Stuck after 1.5s
        # Hyper: Check every 0.3s, Stuck after 0.5s
        if Settings().advanced_pathing_enabled:
            recidivism_memory = Settings().recidivism_memory
            hypersensitive_speed = Settings().hypersensitive_speed
        else:
            recidivism_memory = 0.0 # Standard mode only
            hypersensitive_speed = 0.75 # Standard speed
        
        is_recidivist = (current_time - state.last_unstuck_time) < recidivism_memory
        check_interval = hypersensitive_speed if is_recidivist else 0.75
        stuck_threshold = 0.5 if is_recidivist else 1.5

        # If we haven't moved much in a while AND we tried to move
        if dist_moved < 10 and (current_time - state.last_move_time) > check_interval:
            if state.stuck_start_time == 0.0:
                 state.stuck_start_time = current_time
                 # Only log info if not spamming hyper mode
                 if not is_recidivist:
                     Py4GW.Console.Log("HeroAI", f"Follower {my_agent_id}: Possible stuck. Moved {dist_moved:.2f} (<10) in {(current_time - state.last_move_time):.2f}s. DistToTarget: {dist_to_target:.1f}", Py4GW.Console.MessageType.Info)
            
            elif (current_time - state.stuck_start_time) > stuck_threshold: 
                 if not state.is_stuck:
                    Py4GW.Console.Log("HeroAI", f"Follower {my_agent_id} CONFIRMED STUCK at ({my_x:.1f}, {my_y:.1f}). Initiating smart unstuck sequence.", Py4GW.Console.MessageType.Warning)
                    
                    # Recidivism Check: If we were stuck recently (<RecidivismMemory), resume strategy instead of resetting
                    if (current_time - state.last_unstuck_time) > recidivism_memory:
                         state.unstuck_attempt_count = 0 # New incident, start from 0
                    else:
                         Py4GW.Console.Log("HeroAI", f"Follower {my_agent_id}: Recidivism detected (<{recidivism_memory}s). Resuming sequence at Attempt {state.unstuck_attempt_count}.", Py4GW.Console.MessageType.Warning)
                         
                 state.is_stuck = True
        else:
             if state.stuck_start_time != 0.0:
                  Py4GW.Console.Log("HeroAI", f"Follower {my_agent_id}: Stuck State RESET. Moved {dist_moved:.1f} units.", Py4GW.Console.MessageType.Info)
             
             state.stuck_start_time = 0.0 # Reset if moving
             if dist_moved >= 10:
                 if state.is_stuck:
                    Py4GW.Console.Log("HeroAI", f"Follower {my_agent_id} unstuck successfully. Resuming pathing.", Py4GW.Console.MessageType.Info)
                    state.last_unstuck_time = current_time # Record success time
                 
                 state.is_stuck = False # Clear stuck status if we engaged movement
                 state.unstuck_target = None
                 
                 # Only reset attempt count if we've been free for > RecidivismMemory (Recidivism check)
                 if (current_time - state.last_unstuck_time) > recidivism_memory:
                     state.unstuck_attempt_count = 0
        
        # LOGIC FIX: Only update last_pos and last_move_time if we actually moved significantly!
        # Otherwise, we accumulate time until we trigger the stuck threshold.
        if dist_moved >= 10:
             state.last_pos = (my_x, my_y)
             state.last_move_time = current_time
        
        # Log movement for debug (uncomment if needed, effectively "show coords")
        if dist_moved > 0:
             leader_id = GLOBAL_CACHE.Party.GetPartyLeaderID()
             lx, ly = Agent.GetXY(leader_id)
             Py4GW.Console.Log("HeroAI", f"Pos:({my_x:.0f},{my_y:.0f}) Target:({target_x:.0f},{target_y:.0f}) Leader:({lx:.0f},{ly:.0f}) DistT:{dist_to_target:.0f}", Py4GW.Console.MessageType.Info)

        if state.stuck_start_time == 0.0:
             pass
    else:
        # We are close to target, so not "stuck" in a bad way, just arrived?
        # Only reset if we were previously stuck to clear the flag
        if state.stuck_start_time != 0.0:
             Py4GW.Console.Log("HeroAI", f"Follower {my_agent_id}: Stuck State RESET. Reached target range (Dist: {dist_to_target:.1f}).", Py4GW.Console.MessageType.Info)
        
        if state.is_stuck:
             Py4GW.Console.Log("HeroAI", f"Follower {my_agent_id} reached target range. Clearing stuck status.", Py4GW.Console.MessageType.Info)
        state.stuck_start_time = 0.0
        state.is_stuck = False
        state.unstuck_target = None
        
        # Only reset attempt count if we've been free for > RecidivismMemory (Recidivism check)
        recidivism_memory = Settings().recidivism_memory
        if (current_time - state.last_unstuck_time) > recidivism_memory:
            state.unstuck_attempt_count = 0

    # Execute Unstuck Maneuver
    if state.is_stuck:
        # If we don't have a target or it's been too long, pick a new one
        # Reduced retarget interval from 2.0s to 1.0s for punchier actions
        if state.unstuck_target is None or (current_time - state.unstuck_timestamp) > 1.0:
            # Determine strategy based on attempt count
            dx = target_x - my_x
            dy = target_y - my_y
            dist = math.sqrt(dx*dx + dy*dy)
            if dist > 0.1:
                dx /= dist
                dy /= dist
            else:
                dx, dy = 1.0, 0.0 # Default forward
            
            strategy = "Unknown"
            radius = Settings().unstuck_radius  
            
            # Attempt 0: Backtrack/Reverse
            if state.unstuck_attempt_count == 0:
                ux = my_x - dx * radius
                uy = my_y - dy * radius
                strategy = "Backtrack"
            # Attempt 1: Backtrack + Strafe Right (Diagonal Back-Right)
            elif state.unstuck_attempt_count == 1:
                ux = my_x - dx * radius + dy * radius
                uy = my_y - dy * radius - dx * radius
                strategy = "Backtrack + Right"
            # Attempt 2: Backtrack + Strafe Left (Diagonal Back-Left)
            elif state.unstuck_attempt_count == 2:
                ux = my_x - dx * radius - dy * radius
                uy = my_y - dy * radius + dx * radius
                strategy = "Backtrack + Left"
            # Attempt 3: Strafe Right (Pure)
            elif state.unstuck_attempt_count == 3:
                ux = my_x + dy * radius
                uy = my_y - dx * radius
                strategy = "Strafe Right"
                # Attempt 4: Strafe Left (Pure)
            elif state.unstuck_attempt_count == 4:
                ux = my_x - dy * radius
                uy = my_y + dx * radius
                strategy = "Strafe Left"
            # Attempt 3+: Random Wiggle
            else:
                angle = random.uniform(0, 2 * math.pi)
                ux = my_x + math.cos(angle) * radius
                uy = my_y + math.sin(angle) * radius
                strategy = "Random Wiggle"

            state.unstuck_target = (ux, uy)
            state.unstuck_timestamp = current_time
            state.unstuck_attempt_count += 1
            Py4GW.Console.Log("HeroAI", f"Unstuck Attempt {state.unstuck_attempt_count}: {strategy} to ({ux:.1f}, {uy:.1f})", Py4GW.Console.MessageType.Info)
        
        # Move to unstuck target
        ux, uy = state.unstuck_target
        ActionQueueManager().ResetQueue("ACTION")
        Player.Move(ux, uy)
        
        # Reset stuck flag after a periodic attempt to verify if it worked
        # Increased reset timeout from 3.0s to 8.0s to allow Backtrack/Wiggle attempts
        if (current_time - state.stuck_start_time) > 8.0:
            state.stuck_start_time = 0.0 # Data reset to try again or resume normal
            state.is_stuck = False
            state.unstuck_target = None
            Py4GW.Console.Log("HeroAI", f"Unstuck: Resetting stuck state to retry normal pathing/movement.", Py4GW.Console.MessageType.Info)
            
        return True

    # --- 2. PATHING LOGIC ---
    
    # Check if we are close enough to just stop
    if dist_to_target < 50:
        return False

    # Get NavMesh for current map
    navmesh = AutoPathing().get_navmesh()
    
    # If no navmesh, fallback to direct line interact
    if not navmesh:
        ActionQueueManager().ResetQueue("ACTION")
        Py4GW.Console.Log("HeroAI", f"No NavMesh. Direct move to {target_x:.1f}, {target_y:.1f}", Py4GW.Console.MessageType.Info)
        Player.Move(target_x, target_y)
        return True

    # Check Line of Sight to target
    has_los = navmesh.has_line_of_sight((my_x, my_y), (target_x, target_y))

    if has_los:
        # Clear path if we can go direct
        state.path = []
        ActionQueueManager().ResetQueue("ACTION")
        # Log direct LOS movement
        Py4GW.Console.Log("HeroAI", f"Direct Move (LOS) to ({target_x:.1f}, {target_y:.1f}) Dist: {dist_to_target:.1f}", Py4GW.Console.MessageType.Info)
        Player.Move(target_x, target_y)
        return True
    else:
        # We need a path
        # Recompute path if:
        # 1. No path
        # 2. Target moved significantly
        # 3. Path is stale (optional time check)
        
        dist_target_moved = Utils.Distance((target_x, target_y), state.last_target_pos)
        
        if not state.path or dist_target_moved > 100 or state.path_index >= len(state.path):
            # Calculate A*
            astar = AStar(navmesh)
            # AStar search is synchronous here
            t_start = time.time()
            success = astar.search((my_x, my_y), (target_x, target_y))
            t_end = time.time()
            t_dur = t_end - t_start
            
            if t_dur > 0.1:
                 Py4GW.Console.Log("HeroAI", f"A* Pathfinding took {t_dur:.3f}s. Start:({my_x:.1f},{my_y:.1f}) End:({target_x:.1f},{target_y:.1f})", Py4GW.Console.MessageType.Warning)
            
            if success:
                raw_path = astar.get_path()
                path_str = " -> ".join([f"({p[0]:.0f},{p[1]:.0f})" for p in raw_path[:5]])
                Py4GW.Console.Log("HeroAI", f"Path found! Len:{len(raw_path)} Nodes: [{path_str} ...]", Py4GW.Console.MessageType.Info)
                
                # Sanity Check: If first REAL step is super far, log warning and FALLBACK
                # raw_path[0] is start_pos (me), so we need to check raw_path[1]
                if len(raw_path) > 1:
                    d1 = Utils.Distance((my_x, my_y), raw_path[1])
                    if d1 > Settings().sanity_check_distance:
                         Py4GW.Console.Log("HeroAI", f"WARNING: First Step (Node 1) is {d1:.1f} units away! Path rejected (Ghost Wall/Mesh Error). Forcing Direct Move.", Py4GW.Console.MessageType.Warning)
                         # Fallback to direct move
                         ActionQueueManager().ResetQueue("ACTION")
                         Player.Move(target_x, target_y)
                         return True

                # Smooth path
                # ... (rest of smoothing logic)
                state.path = raw_path # Simplified assignment for now, smoothing can be added back if needed
                state.path_index = 0
                state.last_target_pos = (target_x, target_y)
                state.last_path_calc_time = current_time
            else:
                # Fallback if pathfinding fails (e.g. goal off mesh)
                Py4GW.Console.Log("HeroAI", f"Pathfinding failed after {t_dur:.3f}s to {(target_x, target_y)}, falling back to direct move.", Py4GW.Console.MessageType.Warning)
                ActionQueueManager().ResetQueue("ACTION")
                Player.Move(target_x, target_y)
                return True
        
        # Follow the path
        if state.path and state.path_index < len(state.path):
            # Get next waypoint
            wp = state.path[state.path_index]
            dist_to_wp = Utils.Distance((my_x, my_y), wp)
            
            # If close to waypoint, advance
            if dist_to_wp < 80:
                state.path_index += 1
                if state.path_index < len(state.path):
                    wp = state.path[state.path_index]
                else:
                    # Reached end of path
                    ActionQueueManager().ResetQueue("ACTION")
                    Player.Move(target_x, target_y)
                    return True
            
            # Move to waypoint
            ActionQueueManager().ResetQueue("ACTION")
            # Log normal path movement
            Py4GW.Console.Log("HeroAI", f"Moving to Path WP: ({wp[0]:.1f}, {wp[1]:.1f})", Py4GW.Console.MessageType.Info)
            Player.Move(wp[0], wp[1])
            return True
            
    return False

    return False


def draw_embedded_config(cached_data: CacheData):
    """
    Renders the follow configuration UI logic without creating a new window.
    Designed to be embedded within the main Control Panel.
    """
    _ensure_ini()
    
    # Master Toggle handled by caller (windows.py), but we enable inner logic here
    
    if settings.show_canvas:
        # If canvas is shown, we might need a child window or just columns if space permits.
        # Given it's inside a tree node, columns are best.
        
        # Calculate available width to decide layout? 
        # For now, simplistic column approach similar to standalone.
        table_flags = (
            PyImGui.TableFlags.Borders |
            PyImGui.TableFlags.SizingStretchProp
        )
        
        if PyImGui.begin_table("EmbeddedFollowTable", 2, table_flags):
            PyImGui.table_setup_column("Canvas", PyImGui.TableColumnFlags.WidthFixed, settings.canvas_size[0] + 20)
            PyImGui.table_setup_column("Settings", PyImGui.TableColumnFlags.WidthStretch)
            
            PyImGui.table_next_row()
            PyImGui.table_next_column()
            _draw_canvas(cached_data)
            
            PyImGui.table_next_column()
            _draw_formation_settings()
            _draw_custom_formation(cached_data)
            _draw_canvas_settings()
            _draw_ring_settings()
            
            PyImGui.end_table()
    else:
        # No canvas, just settings list
        _draw_formation_settings()
        _draw_custom_formation(cached_data)
        _draw_canvas_settings()
        _draw_ring_settings()


# ─────────────────────────────────────────────
# LEADER CONFIG WINDOW — UI (leader-only)
# ─────────────────────────────────────────────
def draw_follow_config(cached_data: CacheData):
    """
    Leader-only config window with formation settings,
    per-follower angle control, and canvas preview.
    """
    _ensure_ini()

    if not settings.show_config_window:
        return

    # Only show on leader client
    if Player.GetAgentID() != GLOBAL_CACHE.Party.GetPartyLeaderID():
        return

    canvas_w, canvas_h = settings.canvas_size
    settings_width = 420
    window_w = canvas_w + settings_width if settings.show_canvas else settings_width
    window_h = canvas_h + 80

    PyImGui.set_next_window_size(
        (window_w, window_h),
        PyImGui.ImGuiCond.FirstUseEver
    )

    visible, settings.show_config_window = PyImGui.begin_with_close(
        "Follow Module - Leader Config", settings.show_config_window, 0
    )

    if visible:
        table_flags = (
            PyImGui.TableFlags.Borders |
            PyImGui.TableFlags.SizingStretchProp
        )

        column_count = 2 if settings.show_canvas else 1

        if PyImGui.begin_table("FollowMainTable", column_count, table_flags):
            if settings.show_canvas:
                PyImGui.table_setup_column(
                    "Canvas",
                    PyImGui.TableColumnFlags.WidthFixed,
                    settings.canvas_size[0] + 20
                )

            PyImGui.table_setup_column(
                "Settings",
                PyImGui.TableColumnFlags.WidthStretch)

            if settings.show_canvas:
                PyImGui.table_next_row()
                PyImGui.table_next_column()
                _draw_canvas(cached_data)
                PyImGui.table_next_column()
            else:
                PyImGui.table_next_row()
                PyImGui.table_next_column()

            # ── Settings panel ──
            _draw_formation_settings()
            _draw_custom_formation(cached_data)
            _draw_canvas_settings()
            _draw_ring_settings()

            PyImGui.end_table()

        # 3D overlay
        if settings.draw_3d_overlay:
            _draw_3d_overlay(cached_data)

    PyImGui.end()


# ─────────────────────────────────────────────
# Canvas drawing
# ─────────────────────────────────────────────
def _draw_canvas(cached_data: CacheData):
    """Draw the 2D radar-style canvas with area rings and follower positions."""
    # Manual setup
    canvas_w, canvas_h = settings.canvas_size
    canvas_pos = PyImGui.get_cursor_screen_pos()
    
    # ── Manual Canvas Setup ──
    # Note: PyImGui static methods draw to the current window's draw list.
    # We cannot clip manually as push_clip_rect is not exposed.
    
    # Background
    PyImGui.draw_list_add_rect_filled(canvas_pos[0], canvas_pos[1], canvas_pos[0]+canvas_w, canvas_pos[1]+canvas_h, Color(0,0,0,100).to_color(), 0.0, 0)
    # Border
    PyImGui.draw_list_add_rect(canvas_pos[0], canvas_pos[1], canvas_pos[0]+canvas_w, canvas_pos[1]+canvas_h, Color(255,255,255,100).to_color(), 0.0, 0, 1.0)
    
    cx = canvas_pos[0] + canvas_w / 2
    cy = canvas_pos[1] + canvas_h / 2

    # Grid
    grid_color = ColorPalette.GetColor("gray").copy()
    grid_color.set_a(80)
    grid_step = (Range.Touch.value / 2) * settings.scale

    canvas_x, canvas_y = canvas_pos
    left, right = canvas_x, canvas_x + canvas_w
    top, bottom = canvas_y, canvas_y + canvas_h

    x = cx
    while x <= right:
        PyImGui.draw_list_add_line(x, top, x, bottom, grid_color.to_color(), 1.0)
        x += grid_step
    x = cx - grid_step
    while x >= left:
        PyImGui.draw_list_add_line(x, top, x, bottom, grid_color.to_color(), 1.0)
        x -= grid_step
    y = cy
    while y <= bottom:
        PyImGui.draw_list_add_line(left, y, right, y, grid_color.to_color(), 1.0)
        y += grid_step
    y = cy - grid_step
    while y >= top:
        PyImGui.draw_list_add_line(left, y, right, y, grid_color.to_color(), 1.0)
        y -= grid_step

        # Cardinal Directions (N, S, E, W)
    # Cardinal Directions (N, S, E, W)
    text_color = ColorPalette.GetColor("gold").to_color()
    PyImGui.draw_list_add_text(cx - 5, top + 15, text_color, "N")
    PyImGui.draw_list_add_text(cx - 5, bottom - 30, text_color, "S")
    PyImGui.draw_list_add_text(right - 30, cy - 7, text_color, "E")
    PyImGui.draw_list_add_text(left + 20, cy - 7, text_color, "W")

    # Center marker (leader position)
    touch_color = settings.area_rings[0].color.copy()
    touch_color.set_a(100)
    touch_radius = settings.area_rings[0].radius * settings.scale
    PyImGui.draw_list_add_circle_filled(cx, cy, touch_radius, touch_color.to_color(), 64)

    # Facing Arrow for Leader
    leader_angle = 0.0
    try:
        leader_angle = Agent.GetRotationAngle(Player.GetAgentID())
    except Exception:
        pass
    
    arrow_len = touch_radius * 1.5
    tip_x = cx + (math.cos(leader_angle) * arrow_len)
    tip_y = cy - (math.sin(leader_angle) * arrow_len)
    
    base_angle_offset = 0.5 
    base_len = touch_radius * 0.8
    base_L_x = cx + (math.cos(leader_angle - math.pi + base_angle_offset) * base_len)
    base_L_y = cy - (math.sin(leader_angle - math.pi + base_angle_offset) * base_len)
    base_R_x = cx + (math.cos(leader_angle - math.pi - base_angle_offset) * base_len)
    base_R_y = cy - (math.sin(leader_angle - math.pi - base_angle_offset) * base_len)
    
    arrow_color = ColorPalette.GetColor("white").to_color()
    PyImGui.draw_list_add_triangle_filled(tip_x, tip_y, base_L_x, base_L_y, base_R_x, base_R_y, arrow_color)
    PyImGui.draw_list_add_triangle(tip_x, tip_y, base_L_x, base_L_y, base_R_x, base_R_y, ColorPalette.GetColor("black").to_color(), 1.0)

    # Area rings
    if settings.draw_area_rings:
        for ring in settings.area_rings:
            if ring.show:
                PyImGui.draw_list_add_circle(
                    cx, cy,
                    ring.radius * settings.scale,
                    ring.color.to_color(), 32, float(ring.thickness)
                )

    # Follower formation points
    follower_radius_px = (Range.Touch.value / 2) * settings.scale

    for i, fc in enumerate(settings.follower_configs):
        if i >= MAX_FOLLOWERS:
            break
        
        if not fc.enabled:
            continue
        
        angle_rad = Utils.DegToRad(fc.angle_deg)
        world_angle = leader_angle + angle_rad
        effective_radius = fc.get_radius(settings.formation_radius)

        rot_x = effective_radius * math.cos(world_angle)
        rot_y = effective_radius * math.sin(world_angle)

        draw_x = cx + (rot_x * settings.scale)
        draw_y = cy - (rot_y * settings.scale)

        color_fill = fc.color.copy()
        color_fill.set_a(120)

        PyImGui.draw_list_add_circle_filled(
            draw_x, draw_y, follower_radius_px,
            color_fill.to_color(), 32
        )
        PyImGui.draw_list_add_circle(
            draw_x, draw_y, follower_radius_px,
            fc.color.to_color(), 32, 2.0
        )

    # Advance cursor to reserve the space we just drew on
    PyImGui.dummy(settings.canvas_size[0], settings.canvas_size[1])


# ─────────────────────────────────────────────
# Settings sub-panels
# ─────────────────────────────────────────────
def _draw_formation_settings():
    """Formation parameters section."""
    if PyImGui.collapsing_header("Formation", PyImGui.TreeNodeFlags.DefaultOpen):
        changed = False

        new_radius = PyImGui.slider_float(
            "Formation Radius", settings.formation_radius,
            50.0, Range.Spellcast.value
        )
        if new_radius != settings.formation_radius:
            settings.formation_radius = new_radius
            changed = True

        new_ooc = PyImGui.slider_float(
            "Follow Distance (OOC)", settings.follow_distance_ooc,
            0.0, Range.Spellcast.value
        )
        if new_ooc != settings.follow_distance_ooc:
            settings.follow_distance_ooc = new_ooc
            changed = True

        new_combat = PyImGui.slider_float(
            "Follow Distance (Combat)", settings.follow_distance_combat,
            0.0, Range.Spellcast.value
        )
        if new_combat != settings.follow_distance_combat:
            settings.follow_distance_combat = new_combat
            changed = True

        new_confirm = PyImGui.checkbox(
            "Confirm Follow Point (Map Pathing)", settings.confirm_follow_point
        )
        if new_confirm != settings.confirm_follow_point:
            settings.confirm_follow_point = new_confirm
            changed = True

        if changed:
            _save_settings()


def _draw_custom_formation(cached_data: CacheData):
    """Per-follower custom formation: angle, radius, and color per slot."""
    if PyImGui.collapsing_header("Custom Formation", PyImGui.TreeNodeFlags.DefaultOpen):

        # Build lookup: grid_pos → character name
        leader_id = GLOBAL_CACHE.Party.GetPartyLeaderID()
        hero_count = GLOBAL_CACHE.Party.GetHeroCount()
        hench_count = GLOBAL_CACHE.Party.GetHenchmanCount()
        grid_names: dict[int, str] = {}
        for acc in cached_data.party:
            if not acc.IsSlotActive or acc.PlayerID == leader_id:
                continue
            grid_pos = acc.PartyPosition + hero_count + hench_count
            name = acc.CharacterName if acc.CharacterName else f"Slot {grid_pos + 1}"
            grid_names[grid_pos] = name

        # ── Angle presets ──
        n = min(len(settings.follower_configs), MAX_FOLLOWERS)
        preset_changed = False

        PyImGui.text("Presets:")
        PyImGui.same_line(0.0, 10.0)
        if PyImGui.button("Even Spread"):
            for i in range(n):
                settings.follower_configs[i].angle_deg = (360.0 / n) * i
            preset_changed = True
        PyImGui.same_line(0.0, 5.0)
        if PyImGui.button("V-Shape"):
            v_angles = [30, -30, 60, -60, 90, -90, 120, -120]
            for i in range(n):
                settings.follower_configs[i].angle_deg = float(v_angles[i % len(v_angles)])
            preset_changed = True
        PyImGui.same_line(0.0, 5.0)
        if PyImGui.button("Line"):
            for i in range(n):
                settings.follower_configs[i].angle_deg = 180.0
            preset_changed = True
        PyImGui.same_line(0.0, 5.0)
        if PyImGui.button("Cluster"):
            cluster = [0, 15, -15, 30, -30, 10, -10, 5]
            for i in range(n):
                settings.follower_configs[i].angle_deg = float(cluster[i % len(cluster)])
            preset_changed = True
        PyImGui.same_line(0.0, 5.0)
        if PyImGui.button("Semi-Circle"):
            for i in range(n):
                settings.follower_configs[i].angle_deg = -90.0 + (180.0 / max(n - 1, 1)) * i
            preset_changed = True
        PyImGui.same_line(0.0, 5.0)
        if PyImGui.button("Reset Radius"):
            for i in range(n):
                settings.follower_configs[i].radius = -1.0
            preset_changed = True

        if preset_changed:
            _save_settings()

        PyImGui.separator()

        # ── Per-follower table ──
        table_flags = (
            PyImGui.TableFlags.Borders |
            PyImGui.TableFlags.RowBg |
            PyImGui.TableFlags.SizingStretchProp
        )

        if PyImGui.begin_table("CustomFormationTable", 5, table_flags):
            PyImGui.table_setup_column("Slot", PyImGui.TableColumnFlags.WidthFixed, 50)
            PyImGui.table_setup_column("Follower", PyImGui.TableColumnFlags.WidthFixed, 100)
            PyImGui.table_setup_column("Angle (°)", PyImGui.TableColumnFlags.WidthStretch)
            PyImGui.table_setup_column("Radius", PyImGui.TableColumnFlags.WidthFixed, 160)
            PyImGui.table_setup_column("Color", PyImGui.TableColumnFlags.WidthFixed, 50)
            PyImGui.table_headers_row()

            changed = False

            for i, fc in enumerate(settings.follower_configs):
                if i >= MAX_FOLLOWERS:
                    break

                PyImGui.table_next_row()

                # Slot / Enable
                PyImGui.table_next_column()
                new_enabled = PyImGui.checkbox(f"#{i+1}", fc.enabled)
                if new_enabled != fc.enabled:
                    fc.enabled = new_enabled
                    changed = True

                # Follower name
                PyImGui.table_next_column()
                display_name = grid_names.get(i, f"Slot {i + 1}")
                PyImGui.text(display_name)

                # Angle: slider then input on same line
                PyImGui.table_next_column()
                PyImGui.set_next_item_width(120)
                new_angle = PyImGui.slider_float(
                    f"##AngleS_{i}", fc.angle_deg, -360.0, 360.0
                )
                if new_angle != fc.angle_deg:
                    fc.angle_deg = new_angle
                    changed = True
                PyImGui.same_line(0.0, 4.0)
                PyImGui.set_next_item_width(60)
                typed_angle = PyImGui.input_float(f"##AngleI_{i}", fc.angle_deg)
                if typed_angle != fc.angle_deg:
                    fc.angle_deg = typed_angle
                    changed = True

                # Radius: slider then input on same line (-1 = use global)
                PyImGui.table_next_column()
                display_radius = fc.radius if fc.radius >= 0 else -1.0
                PyImGui.set_next_item_width(80)
                new_radius = PyImGui.slider_float(
                    f"##RadS_{i}", display_radius, -1.0, Range.Spellcast.value
                )
                if new_radius != display_radius:
                    fc.radius = new_radius
                    changed = True
                PyImGui.same_line(0.0, 4.0)
                PyImGui.set_next_item_width(60)
                typed_radius = PyImGui.input_float(f"##RadI_{i}", display_radius)
                if typed_radius != display_radius:
                    fc.radius = typed_radius
                    changed = True

                # Color picker
                PyImGui.table_next_column()
                old_color = fc.color.to_tuple_normalized()
                flags = (
                    PyImGui.ColorEditFlags.NoInputs |
                    PyImGui.ColorEditFlags.NoTooltip |
                    PyImGui.ColorEditFlags.NoLabel |
                    PyImGui.ColorEditFlags.NoDragDrop |
                    PyImGui.ColorEditFlags.AlphaPreview
                )
                new_color = PyImGui.color_edit4(
                    f"##FColor_{i}", old_color,
                    PyImGui.ColorEditFlags(flags)
                )
                if new_color != old_color:
                    fc.color = Color.from_tuple_normalized(new_color)

            PyImGui.end_table()

            # Help text
            PyImGui.text_disabled("Radius: -1 = use global Formation Radius")

            if changed:
                _save_settings()


def _draw_canvas_settings():
    """Canvas display settings."""
    if PyImGui.collapsing_header("Canvas", PyImGui.TreeNodeFlags.DefaultOpen):
        settings.show_canvas = PyImGui.checkbox("Show Canvas", settings.show_canvas)
        settings.scale = PyImGui.slider_float("Scale", settings.scale, 0.05, 1.0)
        settings.draw_3d_overlay = PyImGui.checkbox("Draw 3D Overlay", settings.draw_3d_overlay)
        settings.draw_area_rings = PyImGui.checkbox("Draw Area Rings", settings.draw_area_rings)


def _draw_ring_settings():
    """Area ring configuration."""
    if not settings.draw_area_rings:
        return

    if PyImGui.collapsing_header("Area Rings"):
        table_flags = (
            PyImGui.TableFlags.Borders |
            PyImGui.TableFlags.RowBg |
            PyImGui.TableFlags.SizingStretchProp
        )

        if PyImGui.begin_table("FollowRingsTable", 4, table_flags):
            PyImGui.table_setup_column("Show", PyImGui.TableColumnFlags.WidthFixed, 80)
            PyImGui.table_setup_column("Radius", PyImGui.TableColumnFlags.WidthFixed, 70)
            PyImGui.table_setup_column("Thickness", PyImGui.TableColumnFlags.WidthFixed, 40)
            PyImGui.table_setup_column("Color", PyImGui.TableColumnFlags.WidthStretch)
            PyImGui.table_headers_row()

            for i, ring in enumerate(settings.area_rings):
                PyImGui.table_next_row()
                PyImGui.table_next_column()
                ring.show = PyImGui.checkbox(f"{ring.caption}##FRing{i}", ring.show)
                PyImGui.table_next_column()
                ring.radius = PyImGui.input_float(f"##FRingR{i}", ring.radius)
                PyImGui.table_next_column()
                ring.thickness = int(PyImGui.input_text(f"##FRingT{i}", str(ring.thickness)))
                PyImGui.table_next_column()

                old_color = ring.color.to_tuple_normalized()
                flags = (
                    PyImGui.ColorEditFlags.NoInputs |
                    PyImGui.ColorEditFlags.NoTooltip |
                    PyImGui.ColorEditFlags.NoLabel |
                    PyImGui.ColorEditFlags.NoDragDrop |
                    PyImGui.ColorEditFlags.AlphaPreview
                )
                new_color = PyImGui.color_edit4(
                    f"##FRingC{i}", old_color,
                    PyImGui.ColorEditFlags(flags)
                )
                if new_color != old_color:
                    ring.color = Color.from_tuple_normalized(new_color)

            PyImGui.end_table()


# ─────────────────────────────────────────────
# 3D Overlay
# ─────────────────────────────────────────────
def _draw_3d_overlay(cached_data: CacheData):
    """Draw 3D area rings and follower formation points in the game world."""
    overlay = Overlay()
    overlay.BeginDraw()

    player_id = Player.GetAgentID()
    player_x, player_y, player_z = Agent.GetXYZ(player_id)
    leader_angle = Agent.GetRotationAngle(player_id)

    # Area rings
    if settings.draw_area_rings:
        for ring in settings.area_rings:
            if ring.show:
                overlay.DrawPoly3D(
                    player_x, player_y, player_z,
                    ring.radius, ring.color.to_color(), 64,
                    ring.thickness * 2
                )

    # Follower formation points (3D rotated)
    radius_3d = Range.Touch.value / 2

    for i, fc in enumerate(settings.follower_configs):
        if i >= MAX_FOLLOWERS:
            break
        
        if not fc.enabled:
            continue
            
        # Convert angle to local offset (0°=forward)
        angle_rad = Utils.DegToRad(fc.angle_deg)
        world_angle = leader_angle + angle_rad
        effective_radius = fc.get_radius(settings.formation_radius)

        # Rotate into world
        rot_x = effective_radius * math.cos(world_angle)
        rot_y = effective_radius * math.sin(world_angle)
        
        world_x = player_x + rot_x
        world_y = player_y + rot_y

        overlay.DrawPoly3D(
            world_x, world_y, player_z,
            radius_3d, fc.color.to_color(), 32, 2
        )

    overlay.EndDraw()
