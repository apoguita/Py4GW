"""
HeroAI Following Module — Leader-Driven Follow Logic

The leader calculates formation positions for all followers and writes them
to shared memory (HeroAIOptionStruct.FollowPos).  Each follower simply reads
its own assigned position and moves there.

Also contains the leader-only config window with per-follower angle control,
formation canvas preview, and 3D overlay visualization.
"""

import math
import Py4GW
import PyImGui

from Py4GWCoreLib import (
    GLOBAL_CACHE, Agent, Player, Map, Range, Utils,
    ActionQueueManager, Routines,
)
from Py4GWCoreLib.Overlay import Overlay
from Py4GWCoreLib.ImGui import ImGui
from Py4GWCoreLib.IniManager import IniManager
from Py4GWCoreLib.py4gwcorelib_src.Color import Color, ColorPalette
from Py4GWCoreLib.py4gwcorelib_src.Console import ConsoleLog
from Py4GWCoreLib.native_src.internals.types import Vec2f

from HeroAI.cache_data import CacheData
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
MAX_FOLLOWERS = 12

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
    def __init__(self, angle_deg: float = 0.0, radius: float = -1.0, color: Color = None):
        self.angle_deg = angle_deg
        self.radius = radius  # -1 means use global formation_radius
        self.color: Color = color or ColorPalette.GetColor("white")

    def get_radius(self, global_radius: float) -> float:
        """Return this follower's radius, falling back to global if -1."""
        return self.radius if self.radius >= 0 else global_radius


# ─────────────────────────────────────────────
# Module-level settings
# ─────────────────────────────────────────────
class FollowModuleSettings:
    """All leader-configurable follow settings."""

    # Default formation angles (same layout as the old hero_formation)
    DEFAULT_ANGLES = [0.0, 45.0, -45.0, 90.0, -90.0, 135.0, -135.0, 180.0,
                      -180.0, 225.0, -225.0, 270.0]

    def __init__(self):
        # Formation
        self.formation_radius: float = Range.Touch.value  # distance from leader
        self.follow_distance_ooc: float = FOLLOW_DISTANCE_OUT_OF_COMBAT
        self.follow_distance_combat: float = MELEE_RANGE_VALUE
        self.confirm_follow_point: bool = False

        # Per-follower angle configs (index = party slot)
        self.follower_configs: list[FollowerConfig] = []
        for i, angle in enumerate(self.DEFAULT_ANGLES):
            palette_colors = ["gw_blue", "firebrick", "gold", "gw_purple",
                              "gw_green", "gw_assassin", "blue", "white",
                              "gw_blue", "firebrick", "gold", "gw_purple"]
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
        self.show_config_window: bool = True


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

    # Per-follower angles
    for i, fc in enumerate(settings.follower_configs):
        ini.write_key(_ini_key, "Followers", f"Angle_{i}", fc.angle_deg)
        ini.write_key(_ini_key, "Followers", f"Radius_{i}", fc.radius)

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

    for i, fc in enumerate(settings.follower_configs):
        fc.angle_deg = ini.read_float(_ini_key, "Followers", f"Angle_{i}", fc.angle_deg)
        fc.radius = ini.read_float(_ini_key, "Followers", f"Radius_{i}", fc.radius)

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
    if not _map_quads:
        _map_quads = Map.Pathing.GetMapQuads()
    for quad in _map_quads:
        if Map.Pathing._point_in_quad(x, y, quad):
            return True
    return False


def reset_map_quads():
    """Call when map changes to clear cached pathing data."""
    global _map_quads
    _map_quads.clear()


# ─────────────────────────────────────────────
# LEADER UPDATE — calculates & writes follow positions
# ─────────────────────────────────────────────
def LeaderUpdate(cached_data: CacheData):
    """
    Run on the leader's client each tick.
    Calculates formation positions for every follower and writes
    them to shared memory via HeroAIOptionStruct.FollowPos.
    """
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
            if follower_grid_pos < len(settings.follower_configs):
                angle_deg = settings.follower_configs[follower_grid_pos].angle_deg
            else:
                angle_deg = 0.0

            # Convert angle to local offset (0°=forward)
            angle_rad = Utils.DegToRad(angle_deg)
            fc = settings.follower_configs[follower_grid_pos] if follower_grid_pos < len(settings.follower_configs) else None
            effective_radius = fc.get_radius(settings.formation_radius) if fc else settings.formation_radius
            local_x = effective_radius * math.sin(angle_rad)
            local_y = effective_radius * math.cos(angle_rad)

            # Rotate into world using leader facing (same as reference)
            rot_angle = follow_angle - math.pi / 2
            rot_cos = -math.cos(rot_angle)
            rot_sin = -math.sin(rot_angle)
            rot_x = (local_x * rot_cos) - (local_y * rot_sin)
            rot_y = (local_x * rot_sin) + (local_y * rot_cos)
            xx = follow_x + rot_x
            yy = follow_y + rot_y

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

def Follow(cached_data: CacheData) -> bool:
    """
    BT ActionNode — runs on each follower.
    Reads the leader-assigned FollowPos from shared memory and moves there.
    Returns True if a move was issued, False otherwise.
    """
    global following_flag

    options = cached_data.account_options
    if not options or not options.Following:
        return False

    if not cached_data.follow_throttle_timer.IsExpired():
        return False

    # Leader doesn't follow
    if Player.GetAgentID() == GLOBAL_CACHE.Party.GetPartyLeaderID():
        cached_data.follow_throttle_timer.Reset()
        return False

    # Read assigned position from shared memory
    follow_pos = options.FollowPos
    target_x = follow_pos.x
    target_y = follow_pos.y

    # (0,0) means leader says: no move needed (close enough or no valid pos)
    point_zero = (0.0, 0.0)
    if Utils.Distance((target_x, target_y), point_zero) <= 5:
        return False

    if not Agent.IsValid(GLOBAL_CACHE.Party.GetPartyLeaderID()):
        return False

    following_flag = options.IsFlagged

    # Minimal jitter threshold — the leader already did the real distance gating
    my_x, my_y = Agent.GetXY(Player.GetAgentID())
    distance = Utils.Distance((target_x, target_y), (my_x, my_y))
    if distance < 50:
        return False  # already practically there

    # Issue move command
    ActionQueueManager().ResetQueue("ACTION")
    Player.Move(target_x, target_y)
    return True


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
        "Follow Module — Leader Config", settings.show_config_window, 0
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
    child_flags = (
        PyImGui.WindowFlags.NoTitleBar |
        PyImGui.WindowFlags.NoResize |
        PyImGui.WindowFlags.NoMove
    )

    if PyImGui.begin_child("FollowCanvas", settings.canvas_size, True, child_flags):
        canvas_pos = PyImGui.get_cursor_screen_pos()
        cx = canvas_pos[0] + settings.canvas_size[0] / 2
        cy = canvas_pos[1] + settings.canvas_size[1] / 2

        # Grid
        grid_color = ColorPalette.GetColor("gray").copy()
        grid_color.set_a(80)
        grid_step = (Range.Touch.value / 2) * settings.scale

        canvas_x, canvas_y = canvas_pos
        canvas_w, canvas_h = settings.canvas_size
        left, right = canvas_x, canvas_x + canvas_w
        top, bottom = canvas_y, canvas_y + canvas_h

        x = cx
        while x <= right:
            PyImGui.draw_list_add_line(x, top, x, bottom, grid_color.to_color(), 1)
            x += grid_step
        x = cx - grid_step
        while x >= left:
            PyImGui.draw_list_add_line(x, top, x, bottom, grid_color.to_color(), 1)
            x -= grid_step
        y = cy
        while y <= bottom:
            PyImGui.draw_list_add_line(left, y, right, y, grid_color.to_color(), 1)
            y += grid_step
        y = cy - grid_step
        while y >= top:
            PyImGui.draw_list_add_line(left, y, right, y, grid_color.to_color(), 1)
            y -= grid_step

        # Center marker (leader position)
        touch_color = settings.area_rings[0].color.copy()
        touch_color.set_a(100)
        touch_radius = settings.area_rings[0].radius * settings.scale
        PyImGui.draw_list_add_circle_filled(cx, cy, touch_radius, touch_color.to_color(), 64)

        # Area rings
        if settings.draw_area_rings:
            for ring in settings.area_rings:
                if ring.show:
                    PyImGui.draw_list_add_circle(
                        cx, cy,
                        ring.radius * settings.scale,
                        ring.color.to_color(), 32, ring.thickness
                    )

        # Follower formation points (real-time, rotated by player heading)
        leader_angle = 0.0
        try:
            leader_angle = Agent.GetRotationAngle(Player.GetAgentID())
        except Exception:
            pass

        rot_angle = leader_angle - math.pi / 2
        rot_cos = -math.cos(rot_angle)
        rot_sin = -math.sin(rot_angle)

        follower_radius_px = (Range.Touch.value / 2) * settings.scale

        for i, fc in enumerate(settings.follower_configs):
            if i >= MAX_FOLLOWERS:
                break
            # Convert angle to local offset (0°=forward)
            angle_rad = Utils.DegToRad(fc.angle_deg)
            effective_radius = fc.get_radius(settings.formation_radius)
            local_x = effective_radius * math.sin(angle_rad)
            local_y = effective_radius * math.cos(angle_rad)

            # Rotate into world (same matrix as 3D overlay)
            rot_x = (local_x * rot_cos) - (local_y * rot_sin)
            rot_y = (local_x * rot_sin) + (local_y * rot_cos)

            # Map to canvas: flip both axes for correct game-to-screen mapping
            draw_x = cx + (rot_x * settings.scale)
            draw_y = cy + (-rot_y * settings.scale)

            color_fill = fc.color.copy()
            color_fill.set_a(120)

            PyImGui.draw_list_add_circle_filled(
                draw_x, draw_y, follower_radius_px,
                color_fill.to_color(), 32
            )
            PyImGui.draw_list_add_circle(
                draw_x, draw_y, follower_radius_px,
                fc.color.to_color(), 32, 2
            )

        PyImGui.end_child()


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
            v_angles = [30, -30, 60, -60, 90, -90, 120, -120, 150, -150, 180, -180]
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
            cluster = [0, 15, -15, 30, -30, 10, -10, 5, -5, 20, -20, 25]
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

        if PyImGui.begin_table("CustomFormationTable", 4, table_flags):
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
        # Convert angle to local offset (0°=forward)
        angle_rad = Utils.DegToRad(fc.angle_deg)
        effective_radius = fc.get_radius(settings.formation_radius)
        local_x = effective_radius * math.sin(angle_rad)
        local_y = effective_radius * math.cos(angle_rad)

        # Rotate into world using leader facing (same as reference)
        rot_angle = leader_angle - math.pi / 2
        rot_cos = -math.cos(rot_angle)
        rot_sin = -math.sin(rot_angle)
        rot_x = (local_x * rot_cos) - (local_y * rot_sin)
        rot_y = (local_x * rot_sin) + (local_y * rot_cos)
        world_x = player_x + rot_x
        world_y = player_y + rot_y

        overlay.DrawPoly3D(
            world_x, world_y, player_z,
            radius_3d, fc.color.to_color(), 32, 2
        )

    overlay.EndDraw()
