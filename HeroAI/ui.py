from collections.abc import Callable
import ctypes
from enum import Enum
import math
import os
import random
from typing import Optional
from Py4GW import Console
import PyImGui
from HeroAI import windows
from HeroAI.cache_data import CacheData
from HeroAI.commands import HeroAICommands
from HeroAI.constants import NUMBER_OF_SKILLS, PARTY_WINDOW_HASH, SKILLBAR_WINDOW_HASH
from HeroAI.settings import Settings
from HeroAI.types import Docked, GameOptionStruct, FramePosition
from HeroAI.utils import IsHeroFlagged, SameMapAsAccount
from HeroAI.windows import CompareAndSubmitGameOptions
from Py4GWCoreLib import ImGui
from Py4GWCoreLib.GlobalCache import GLOBAL_CACHE
from Py4GWCoreLib.GlobalCache.SharedMemory import AccountData, SharedMessage
from Py4GWCoreLib.ImGui_src.IconsFontAwesome5 import IconsFontAwesome5
from Py4GWCoreLib.ImGui_src.Style import Style
from Py4GWCoreLib.ImGui_src.Textures import GameTexture, GameTexture, TextureState, ThemeTexture, ThemeTextures
from Py4GWCoreLib.ImGui_src.WindowModule import WindowModule
from Py4GWCoreLib.ImGui_src.types import Alignment, HorizontalAlignment, ImGuiStyleVar, StyleTheme, VerticalAlignment
from Py4GWCoreLib.Overlay import Overlay
from Py4GWCoreLib.Player import Player
from Py4GWCoreLib.UIManager import UIManager
from Py4GWCoreLib.enums_src.GameData_enums import Allegiance, Profession, ProfessionShort, Range
from Py4GWCoreLib.enums_src.IO_enums import Key
from Py4GWCoreLib.enums_src.Model_enums import ModelID
from Py4GWCoreLib.enums_src.Multiboxing_enums import SharedCommandType
from Py4GWCoreLib.py4gwcorelib_src.Color import Color
from Py4GWCoreLib.py4gwcorelib_src.Console import ConsoleLog
from Py4GWCoreLib.py4gwcorelib_src.Timer import ThrottledTimer, Timer
from Py4GWCoreLib.py4gwcorelib_src.Utils import Utils
from Py4GW_widget_manager import WidgetHandler

class CachedSkillInfo:
    def __init__(self, skill_id: int):
        self.skill_id = skill_id
        self.name = GLOBAL_CACHE.Skill.GetNameFromWiki(skill_id)
        self.description = GLOBAL_CACHE.Skill.GetDescription(skill_id)
        self.texture_path = GLOBAL_CACHE.Skill.ExtraData.GetTexturePath(skill_id)
        
        if not os.path.exists(self.texture_path):
            self.texture_path = ""
        
        if not self.texture_path and self.skill_id != 0:
            self.texture_path = ThemeTexture.PlaceHolderTexture.texture
            
        self.is_elite = GLOBAL_CACHE.Skill.Flags.IsElite(skill_id)
        self.is_hex = GLOBAL_CACHE.Skill.Flags.IsHex(skill_id)
        self.is_title = GLOBAL_CACHE.Skill.Flags.IsTitle(skill_id)
        self.is_enchantment = GLOBAL_CACHE.Skill.Flags.IsEnchantment(skill_id)
        self.is_shout = GLOBAL_CACHE.Skill.Flags.IsShout(skill_id)
        self.is_skill = GLOBAL_CACHE.Skill.Flags.IsSkill(skill_id)
        self.is_condition = GLOBAL_CACHE.Skill.Flags.IsCondition(skill_id)
        
        self.adrenaline_cost = GLOBAL_CACHE.Skill.Data.GetAdrenaline(skill_id)

        frame_texture, texture_state, progress_color = get_frame_texture_for_effect(
            skill_id)
        self.frame_texture = frame_texture
        self.texture_state = texture_state
        self.progress_color = progress_color

        self.recharge_time = GLOBAL_CACHE.Skill.Data.GetRecharge(skill_id)


skill_cache: dict[int, CachedSkillInfo] = {}
message_cache : dict[str, dict[SharedCommandType, dict[int, tuple]]] = {}
template_popup_open: bool = False
template_account: str = ""
template_code = ""
configure_consumables_window_open: bool = False

widget_handler = WidgetHandler()
module_info = None

settings = Settings()
casting_animation_timer = Timer()
casting_animation_timer.Start()

dialog_throttle = ThrottledTimer(500)
party_throttle = ThrottledTimer(500)
party_search_throttle = ThrottledTimer(500)
party_member_frames : list[FramePosition] = []

commands = HeroAICommands()
gray_color = Color(150, 150, 150, 255)
MAX_CHILD_FRAMES = 50

class HealthState(Enum):
    Normal = Color(204, 0, 0, 255)
    Poisoned = Color(116, 116, 48, 255)
    Bleeding = Color(224, 119, 119, 255)
    DegenHexed = Color(196, 56, 150, 255)
    Disconnected = Color(54, 54, 54, 255)

def show_configure_consumables_window():
    global configure_consumables_window_open
    configure_consumables_window_open = True
          
def get_frame_texture_for_effect(skill_id: int) -> tuple[(GameTexture), TextureState, int]:
    is_elite = GLOBAL_CACHE.Skill.Flags.IsElite(skill_id)
    texture_state = TextureState.Normal if not is_elite else TextureState.Active

    theme = ImGui.get_style().Theme if ImGui.get_style().Theme in ImGui.Textured_Themes else StyleTheme.Guild_Wars
    
    if not theme in ImGui.Textured_Themes:
        theme = StyleTheme.Guild_Wars

    if GLOBAL_CACHE.Skill.Flags.IsHex(skill_id):
        frame_texture = ThemeTextures.Effect_Frame_Hex.value.get_texture(theme)
        progress_color = Color(215, 31, 158, 255).color_int

    elif GLOBAL_CACHE.Skill.Flags.IsTitle(skill_id):
        frame_texture = ThemeTextures.Effect_Frame_Skill.value.get_texture(theme)
        progress_color = Color(75, 139, 69, 255).color_int

    elif GLOBAL_CACHE.Skill.Flags.IsEnchantment(skill_id):
        frame_texture = ThemeTextures.Effect_Frame_Enchantment.value.get_texture(theme)
        progress_color = Color(178, 225, 47, 255).color_int

        profession, _ = GLOBAL_CACHE.Skill.GetProfession(skill_id)
        if profession == Profession.Dervish:
            frame_texture = ThemeTextures.Effect_Frame_Blue.value.get_texture()
            progress_color = Color(74, 163, 193, 255).color_int

    elif GLOBAL_CACHE.Skill.Flags.IsCondition(skill_id):
        frame_texture = ThemeTextures.Effect_Frame_Condition.value.get_texture(theme)
        progress_color = Color(221, 175, 52, 255).color_int

    else:
        frame_texture = ThemeTextures.Effect_Frame_Skill.value.get_texture(theme)
        progress_color = Color(75, 139, 69, 255).color_int

    return frame_texture, texture_state, progress_color

def draw_health_bar(width: float, height: float, max_health: float, current_health: float, regen: float, state: HealthState = HealthState.Normal, deep_wound : bool = False, enchanted: bool = False, conditioned: bool = False, hexed: bool = False, has_weaponspell: bool = False) -> bool:
    style = ImGui.get_style()
    draw_textures = style.Theme in ImGui.Textured_Themes
    pips = Utils.calculate_health_pips(max_health, regen)

    if not draw_textures:
        color = state.value
        style.PlotHistogram.push_color(color.rgb_tuple)
        style.FrameRounding.push_style_var(0)
        ImGui.progress_bar(current_health, width, height)
        style.FrameRounding.pop_style_var()
        style.PlotHistogram.pop_color()            
    else:
        ImGui.dummy(width, height)

    fraction = (max(0.0, min(1.0, current_health))
                if max_health > 0 else 0.0)
    
    item_rect_min, item_rect_max, item_rect_size = ImGui.get_item_rect()

    width = item_rect_max[0] - item_rect_min[0]
    height = item_rect_max[1] - item_rect_min[1]
    item_rect = (item_rect_min[0], item_rect_min[1], width, height)

    progress_rect = (item_rect[0] + 1, item_rect[1] + 1,
                     (width - 2) * fraction, height - 2)
    background_rect = (
        item_rect[0] + 1, item_rect[1] + 1, width - 2, height - 2)
    cursor_rect = (item_rect[0] - 2 + (width - 2) * fraction, item_rect[1] + 1, 4, height -
                   2) if fraction > 0 else (item_rect[0] + (width - 2) * fraction, item_rect[1] + 1, 4, height - 2)

    if draw_textures:
        match state:
            case HealthState.Poisoned:
                health_bar_empty_texture = ThemeTextures.HealthBarPoisonedEmpty
                health_bar_fill_texture = ThemeTextures.HealthBarPoisonedFill
                health_bar_cursor_texture = ThemeTextures.HealthBarPoisonedCursor
            case HealthState.Bleeding:
                health_bar_empty_texture = ThemeTextures.HealthBarBleedingEmpty
                health_bar_fill_texture = ThemeTextures.HealthBarBleedingFill
                health_bar_cursor_texture = ThemeTextures.HealthBarBleedingCursor
            case HealthState.DegenHexed:        
                health_bar_empty_texture = ThemeTextures.HealthBarHexedEmpty
                health_bar_fill_texture = ThemeTextures.HealthBarHexedFill
                health_bar_cursor_texture = ThemeTextures.HealthBarHexedCursor
            case HealthState.Disconnected:
                health_bar_empty_texture = ThemeTextures.HealthBarDisconnectedEmpty
                health_bar_fill_texture = ThemeTextures.HealthBarDisconnectedFill
                health_bar_cursor_texture = ThemeTextures.HealthBarDisconnectedCursor
            case _:                
                health_bar_empty_texture = ThemeTextures.HealthBarEmpty
                health_bar_fill_texture = ThemeTextures.HealthBarFill
                health_bar_cursor_texture = ThemeTextures.HealthBarCursor
        
        health_bar_empty_texture.value.get_texture().draw_in_drawlist(
            background_rect[:2],
            background_rect[2:],
        )

        health_bar_fill_texture.value.get_texture().draw_in_drawlist(
            progress_rect[:2],
            progress_rect[2:],
        )

        if current_health * max_health != max_health:
            health_bar_cursor_texture.value.get_texture().draw_in_drawlist(
                cursor_rect[:2],
                cursor_rect[2:],
            )

    if deep_wound:
        deep_wound_rect = (
            item_rect[0] + (width * 0.8), item_rect[1] + 1, (width * 0.2) + 1, height - 2)
        
        ThemeTextures.HealthBarDeepWound.value.get_texture().draw_in_drawlist(
            deep_wound_rect[:2],
            deep_wound_rect[2:],
        )
        
        ThemeTextures.HealthBarDeepWoundCursor.value.get_texture().draw_in_drawlist(
            deep_wound_rect[:2],
            (2, deep_wound_rect[3]),
        )
        pass
    
    indicators = (enchanted, conditioned, hexed, has_weaponspell)
    if any(indicators):
        #weapon_spell, hexed, conditioned, enchanted
        x_offset = height + 2
        
        for i, indicator in enumerate(indicators):
            if indicator:
                indicator_texture = None
                match i:
                    case 0:
                        indicator_texture = ThemeTextures.HealthIdenticator_Enchanted
                    case 1:
                        indicator_texture = ThemeTextures.HealthIdenticator_Conditioned
                    case 2:
                        indicator_texture = ThemeTextures.HealthIdenticator_Hexed
                    case 3:
                        indicator_texture = ThemeTextures.HealthIdenticator_WeaponSpell
                        
                if indicator_texture:
                    indicator_texture.value.get_texture().draw_in_drawlist(
                        (item_rect[0] + item_rect[2] - x_offset, item_rect[1]),
                        (height, height),
                    )
                    
                x_offset += height + 2
        
        
    display_label = str(int(current_health * max_health))
    textsize = PyImGui.calc_text_size(display_label)
    text_rect = (item_rect[0] + ((width - textsize[0]) / 2), item_rect[1] +
                 ((height - textsize[1]) / 2) + 3, textsize[0], textsize[1])

    ImGui.push_font("Regular", 12)
    PyImGui.draw_list_add_text(
        text_rect[0],
        text_rect[1],
        style.Text.color_int,
        display_label,
    )
    ImGui.pop_font()

    if draw_textures:
        pip_texture = ThemeTextures.Pip_Regen if pips > 0 else ThemeTextures.Pip_Degen

        if pips > 0:
            pip_pos = text_rect[0] + text_rect[2] + 5

            for i in range(int(pips)):
                pip_texture.value.get_texture().draw_in_drawlist(
                    (pip_pos + (i * 8), item_rect[1]),
                    (10 * (height / 16), height),
                )

        elif pips < 0:
            pip_pos = text_rect[0] - 5 - 10

            for i in range(abs(int(pips))):
                pip_texture.value.get_texture().draw_in_drawlist(
                    (pip_pos - (i * 8), item_rect[1]),
                    (10 * (height / 16), height),
                )

        PyImGui.draw_list_add_rect(
            item_rect_min[0], item_rect_min[1], item_rect_min[0] + item_rect_size[0], item_rect_min[1] + item_rect_size[1], style.Border.color_int, 0, 0, 1
        )
        
    else:
        pip_char = IconsFontAwesome5.ICON_ANGLE_RIGHT if pips > 0 else IconsFontAwesome5.ICON_ANGLE_LEFT
        pip_string = "".join([pip_char for _ in range(abs(int(pips)))])

        ImGui.push_font("Regular", 8)
        if pips > 0:
            PyImGui.draw_list_add_text(
                text_rect[0] + text_rect[2] + 5,
                item_rect[1] + 3,
                style.Text.color_int,
                pip_string
            )
        elif pips < 0:
            text_size = PyImGui.calc_text_size(pip_string)
            PyImGui.draw_list_add_text(
                text_rect[0] - 5 - text_size[0],
                item_rect[1] + 3,
                style.Text.color_int,
                pip_string
            )
        ImGui.pop_font()
        
    return PyImGui.is_item_clicked(0)

def draw_energy_bar(width: float, height: float, max_energy: float, current_energy: float, regen: float) -> bool:
    style = ImGui.get_style()
    pips = Utils.calculate_energy_pips(max_energy, regen)

    draw_textures = style.Theme in ImGui.Textured_Themes

    if not draw_textures:
        style.PlotHistogram.push_color((30, 94, 153, 255))
        style.FrameRounding.push_style_var(0)
        ImGui.progress_bar(current_energy, width, height)
        style.FrameRounding.pop_style_var()
        style.PlotHistogram.pop_color()
    else:
        ImGui.dummy(width, height)

    fraction = (max(0.0, min(1.0, current_energy))
                if max_energy > 0 else 0.0)
    
    item_rect_min, item_rect_max, item_rect_size = ImGui.get_item_rect()

    width = item_rect_max[0] - item_rect_min[0]
    height = item_rect_max[1] - item_rect_min[1]
    item_rect = (item_rect_min[0], item_rect_min[1], width, height)

    progress_rect = (item_rect[0] + 1, item_rect[1] + 1,
                     (width - 2) * fraction, height - 2)
    background_rect = (
        item_rect[0] + 1, item_rect[1] + 1, width - 2, height - 2)
    cursor_rect = (item_rect[0] - 2 + (width - 2) * fraction, item_rect[1] + 1, 4, height -
                   2) if fraction > 0 else (item_rect[0] + (width - 2) * fraction, item_rect[1] + 1, 4, height - 2)

    if draw_textures:
        ThemeTextures.EnergyBarEmpty.value.get_texture().draw_in_drawlist(
            background_rect[:2],
            background_rect[2:],
        )

        ThemeTextures.EnergyBarFill.value.get_texture().draw_in_drawlist(
            progress_rect[:2],
            progress_rect[2:],
        )

        if current_energy * max_energy != max_energy:
            ThemeTextures.EnergyBarCursor.value.get_texture().draw_in_drawlist(
                cursor_rect[:2],
                cursor_rect[2:],
            )

    display_label = str(int(current_energy * max_energy))
    textsize = PyImGui.calc_text_size(display_label)
    text_rect = (item_rect[0] + ((width - textsize[0]) / 2), item_rect[1] +
                 ((height - textsize[1]) / 2) + 3, textsize[0], textsize[1])

    ImGui.push_font("Regular", 12)
    PyImGui.draw_list_add_text(
        text_rect[0],
        text_rect[1],
        style.Text.color_int,
        display_label,
    )
    ImGui.pop_font()

    if draw_textures:
        pip_texture = ThemeTextures.Pip_Regen if pips > 0 else ThemeTextures.Pip_Degen

        if pips > 0:
            pip_pos = text_rect[0] + text_rect[2] + 5

            for i in range(int(pips)):
                pip_texture.value.get_texture().draw_in_drawlist(
                    (pip_pos + (i * 8), item_rect[1]),
                    (10 * (height / 16), height),
                )

        elif pips < 0:
            pip_pos = text_rect[0] - 5 - 10

            for i in range(abs(int(pips))):
                pip_texture.value.get_texture().draw_in_drawlist(
                    (pip_pos - (i * 8), item_rect[1]),
                    (10 * (height / 16), height),
                )

        PyImGui.draw_list_add_rect(
            item_rect_min[0], item_rect_min[1], item_rect_min[0] + item_rect_size[0], item_rect_min[1] + item_rect_size[1], style.Border.color_int, 0, 0, 1
        )
    else:
        pip_char = IconsFontAwesome5.ICON_ANGLE_RIGHT if pips > 0 else IconsFontAwesome5.ICON_ANGLE_LEFT
        pip_string = "".join([pip_char for _ in range(abs(int(pips)))])

        ImGui.push_font("Regular", 8)
        if pips > 0:
            PyImGui.draw_list_add_text(
                text_rect[0] + text_rect[2] + 5,
                item_rect[1] + 3,
                style.Text.color_int,
                pip_string
            )
        elif pips < 0:
            text_size = PyImGui.calc_text_size(pip_string)
            PyImGui.draw_list_add_text(
                text_rect[0] - 5 - text_size[0],
                item_rect[1] + 3,
                style.Text.color_int,
                pip_string
            )
        ImGui.pop_font()

    return PyImGui.is_item_clicked(0)

def DrawSquareCooldownEx(button_pos, button_size, progress, tint=0.1):
    """Smooth, non-overlapping, counter-clockwise square cooldown effect."""
    if isinstance(button_size, (int, float)):
        button_size = (button_size, button_size)

    if progress <= 0 or progress >= 1.0:
        return

    center_x = button_pos[0] + button_size[0] / 2.0
    center_y = button_pos[1] + button_size[1] / 2.0
    half_w = button_size[0] / 2.0
    half_h = button_size[1] / 2.0
    color = (int(255 * tint) << 24)

    # Angles
    start_angle = -math.pi / 2.0  # top center
    end_angle = start_angle - 2.0 * math.pi * progress

    # Pre-calculate points
    segments = max(32, min(64, int(64 + 128 * (1 - progress))))
    points = [(center_x, center_y)]

    # Function to compute intersection with square boundary
    def intersection(angle):
        dx, dy = math.cos(angle), math.sin(angle)
        tx = half_w / abs(dx) if dx != 0 else float("inf")
        ty = half_h / abs(dy) if dy != 0 else float("inf")
        t = min(tx, ty)
        return (center_x + dx * t, center_y + dy * t)

    # Always include corners at boundary crossings to prevent overlap
    # Define corner angles in CCW order (starting from top-right)
    corner_angles = [
        -math.pi / 4,     # top-right
        -3 * math.pi / 4,  # bottom-right
        -5 * math.pi / 4,  # bottom-left
        -7 * math.pi / 4,  # top-left
        -math.pi / 4 - 2 * math.pi  # wrap
    ]

    # Generate wedge path
    a = start_angle
    for corner in corner_angles:
        if end_angle < corner < a:
            points.append(intersection(corner))
        elif end_angle >= corner >= a:
            points.append(intersection(corner))
    # Uniform segment sampling for smoothness
    for i in range(segments + 1):
        angle = start_angle + (end_angle - start_angle) * (i / segments)
        points.append(intersection(angle))

    # Remove potential duplicates to prevent triangle overlap
    unique_points = []
    for p in points:
        if not unique_points or (abs(unique_points[-1][0] - p[0]) > 0.1 or abs(unique_points[-1][1] - p[1]) > 0.1):
            unique_points.append(p)

    # Draw filled triangle fan (no overlaps)
    for i in range(1, len(unique_points) - 1):
        x1, y1 = unique_points[0]
        x2, y2 = unique_points[i]
        x3, y3 = unique_points[i + 1]
        PyImGui.draw_list_add_triangle_filled(x1, y1, x2, y2, x3, y3, color)

def get_skill_target(account_data: AccountData, cached_skill: CachedSkillInfo) -> int | None:
    py_io = PyImGui.get_io()
    
    if not cached_skill or cached_skill.skill_id == 0:
        return None
    
    target_id = GLOBAL_CACHE.Player.GetTargetID()
    is_gadget = GLOBAL_CACHE.Agent.IsGadget(target_id)
    is_item = GLOBAL_CACHE.Agent.IsItem(target_id)
    
    if cached_skill.is_enchantment or cached_skill.is_shout:
        allegiance, _ = GLOBAL_CACHE.Agent.GetAllegiance(target_id) if target_id != 0 else (Allegiance.Neutral, None)
        
        if allegiance in [Allegiance.Ally, Allegiance.Minion, Allegiance.SpiritPet]:
            return target_id
        else:
            return GLOBAL_CACHE.Player.GetAgentID() if py_io.key_ctrl else account_data.PlayerID
    else:
        return GLOBAL_CACHE.Player.GetAgentID() if py_io.key_ctrl else target_id if not is_item and target_id else account_data.PlayerID

def draw_casting_animation(
    pos: tuple[float, float],
    size: tuple[float, float],
    min_alpha: int = 40
):
    """Draws lightweight concentric circles moving from outside toward the center (casting animation)."""
    global casting_animation_timer

    # Get elapsed time (ms → s)
    t = casting_animation_timer.GetElapsedTime() / 1000.0

    # Animation parameters
    num_circles = 3               # number of simultaneous circles
    cycle_duration = 1.25         # seconds per full travel (outside → center)
    max_radius = max(size) * 0.75 # start slightly outside item bounds
    min_radius = max(size) * 0.05 # small inner limit (center end)
    center_x = pos[0] + size[0] / 2
    center_y = pos[1] + size[1] / 2

    # Clamp the minimum alpha to valid range
    min_alpha = max(0, min(255, min_alpha))

    for i in range(num_circles):
        # Each circle’s start offset — evenly staggered
        offset = i / num_circles

        # Normalized progress (0 → 1), wraps every cycle
        progress = (t / cycle_duration + offset) % 1.0

        # Radius interpolates from max_radius → min_radius
        radius = max_radius - (max_radius - min_radius) * progress

        # Alpha goes from 255 → min_alpha (instead of fading to zero)
        alpha = int(min_alpha + (255 - min_alpha) * (1.0 - progress) ** 1.5)
        alpha = max(0, min(255, alpha))  # safety clamp

        # Optional subtle rotation effect
        swirl_angle = math.sin((t + i) * 2.0) * 0.1
        cx = center_x + math.cos(swirl_angle) * 0.0
        cy = center_y + math.sin(swirl_angle) * 0.0

        color = Color.from_tuple((0, 0, 0, alpha / 255.0))

        PyImGui.push_clip_rect(pos[0], pos[1], pos[0] + size[0], pos[1] + size[1], True)
        PyImGui.draw_list_add_circle(cx, cy, radius, color.color_int, 36, 6.0)
        PyImGui.pop_clip_rect()

def draw_skill_bar(height: float, account_data: AccountData, cached_data: CacheData, message_queue: list[tuple[int, SharedMessage]]):
    global skill_cache, messages
    style = ImGui.get_style()
    draw_textures = style.Theme in ImGui.Textured_Themes
    texture_theme = style.Theme if draw_textures else StyleTheme.Guild_Wars

    for slot, skill_info in enumerate(account_data.PlayerData.SkillbarData.Skills):
        
        if skill_info.Id not in skill_cache:
            skill_cache[skill_info.Id] = CachedSkillInfo(skill_info.Id)

        skill = skill_cache[skill_info.Id]
        skill_texture = skill.texture_path

        if not skill_texture:
            ImGui.dummy(height, height)
            item_rect_min = PyImGui.get_item_rect_min()

            PyImGui.draw_list_add_rect(
                item_rect_min[0],
                item_rect_min[1],
                item_rect_min[0] + height,
                item_rect_min[1] + height,
                Color(50, 50, 50, 255).color_int,
                0,
                0,
                2
            )
            PyImGui.same_line(0, 0)
            continue

        skill_recharge = skill_info.Recharge
        adrenaline = skill_info.Adrenaline
        enough_adrenaline = adrenaline >= skill.adrenaline_cost
        
        ImGui.image(skill_texture, (height, height), uv0=(
            0.0625, 0.0625) if draw_textures else (0, 0), uv1=(0.9375, 0.9375) if draw_textures else (1, 1))

        if PyImGui.is_item_hovered():
            show_skill_tooltip(skill)

        item_rect_min = PyImGui.get_item_rect_min()
        casting_skill = account_data.PlayerData.SkillbarData.CastingSkillID
        
        if skill_recharge > 0 and skill.recharge_time > 0:
                DrawSquareCooldownEx(
                    (item_rect_min[0], item_rect_min[1]),
                    height,
                    skill_recharge / (skill.recharge_time * 1000.0),
                    tint=0.6
                )

                text_size = PyImGui.calc_text_size(
                    f"{int(skill_recharge/1000)}")
                offset_x = (height - text_size[0]) / 2
                offset_y = (height - text_size[1]) / 2

                PyImGui.draw_list_add_text(
                    item_rect_min[0] + offset_x,
                    item_rect_min[1] + offset_y,
                    ImGui.get_style().Text.color_int,
                    f"{int(skill_recharge/1000)}"
                )
        elif casting_skill == skill.skill_id:
            draw_casting_animation(item_rect_min, (height, height))
        
        if not enough_adrenaline:             
            adrenaline_fraction = adrenaline / skill.adrenaline_cost if skill.adrenaline_cost > 0 else 0.0
            adrenaline_fraction = max(0.0, min(adrenaline_fraction, 1.0))  # Clamp between 0–1       
                   
            fill_rect = (item_rect_min[0], item_rect_min[1], height, height - (height * adrenaline_fraction))
            
            PyImGui.draw_list_add_rect_filled(
                fill_rect[0],
                fill_rect[1],
                fill_rect[0] + fill_rect[2],
                fill_rect[1] + fill_rect[3],
                Color(0, 0, 0, 150).color_int,
                0,
                0
            )
            
            PyImGui.draw_list_add_line(
                fill_rect[0],
                fill_rect[1] + fill_rect[3],
                fill_rect[0] + fill_rect[2],
                fill_rect[1] + fill_rect[3],
                Color(0, 0, 0, 255).color_int,
                1
            )
                
        hero_options = cached_data.HeroAI_vars.all_game_option_struct[account_data.PartyPosition]
        if not hero_options.Skills[slot].Active:
            hovered = PyImGui.is_item_hovered()
            ThemeTextures.Cancel.value.get_texture(texture_theme).draw_in_drawlist(
                PyImGui.get_item_rect_min(),
                (height, height),
                state=TextureState.Hovered if hovered else TextureState.Normal
            )

        account_email = GLOBAL_CACHE.Player.GetAccountEmail()
        queued_skill_messages = message_cache.get(account_email, {}).get(SharedCommandType.UseSkill, {})
        if queued_skill_messages:
            queued_skill_usage = {index: msg for index, msg in message_queue if msg.Command == SharedCommandType.UseSkill and msg.ReceiverEmail == account_email and msg.Params[1] == float(skill.skill_id) and index in queued_skill_messages}
                    
            if queued_skill_usage:
                hovered = PyImGui.is_item_hovered()
                ThemeTextures.Check.value.get_texture(texture_theme).draw_in_drawlist(
                    PyImGui.get_item_rect_min(),
                    (height, height),
                    state=TextureState.Hovered if hovered else TextureState.Normal
                )
            else:
                #delete all queued messages for this skill that were not found in new messages (probably failed)
                indices_to_delete = [index for index, msg in queued_skill_messages.items() if msg[1] == skill.skill_id]
                for index in indices_to_delete:
                    del queued_skill_messages[index]

        if PyImGui.is_item_clicked(0) and enough_adrenaline:
            io = PyImGui.get_io()
            if io.key_shift:
                hero_ai_data = GLOBAL_CACHE.ShMem.GetGerHeroAIOptionsByPartyNumber(
                    account_data.PartyPosition)
                if hero_ai_data:
                    hero_ai_data.Skills[slot] = not hero_options.Skills[slot].Active

            else:
                target_id = get_skill_target(account_data, skill)
                
                if target_id is not None:
                    message_index = GLOBAL_CACHE.ShMem.SendMessage(GLOBAL_CACHE.Player.GetAccountEmail(
                    ), account_data.AccountEmail, SharedCommandType.UseSkill, (target_id, int(skill.skill_id)))

                    if account_data.AccountEmail not in message_cache:
                        message_cache[account_data.AccountEmail] = {}
                        
                    if SharedCommandType.UseSkill not in message_cache[account_data.AccountEmail]:
                        message_cache[account_data.AccountEmail][SharedCommandType.UseSkill] = {}

                    message_cache[account_data.AccountEmail][SharedCommandType.UseSkill][message_index] = (target_id, skill.skill_id)

        if draw_textures:
            texture_state = TextureState.Normal if not skill.is_elite else TextureState.Active

            ThemeTextures.Skill_Frame.value.get_texture(texture_theme).draw_in_drawlist(
                item_rect_min[:2],
                (height, height),
                state=texture_state
            )

        PyImGui.same_line(0, 0)

    pass 

def show_skill_tooltip(skill, show_usage=True):
    PyImGui.set_next_window_size((300, 0), PyImGui.ImGuiCond.Always)
    if ImGui.begin_tooltip():
        ImGui.push_font("Regular", 14)
        ImGui.text_colored(
                    f"{skill.name} (ID: {skill.skill_id})",
                    Color(227, 211, 165, 255).color_tuple                    
                )
        ImGui.pop_font()

        ImGui.separator()
        if skill.description:
            ImGui.text_wrapped(skill.description)
        
        if show_usage:
            PyImGui.spacing()
                    
            gray_color = Color(150, 150, 150, 255)
                    
            ImGui.push_font("Regular", 12)
            ImGui.text_colored(
                        "Click to use on current target",
                        gray_color.color_tuple                  
                    )
            PyImGui.set_cursor_pos_y(PyImGui.get_cursor_pos_y() - 2)
                    
            ImGui.text_colored(
                        "Ctrl + Click to use on self",
                        gray_color.color_tuple                
                    )
            PyImGui.set_cursor_pos_y(PyImGui.get_cursor_pos_y() - 2)
                    
            ImGui.text_colored(
                        "Shift + Click to toggle active/inactive",
                        gray_color.color_tuple              
                    )
            ImGui.pop_font()

        ImGui.end_tooltip() # Implementation of skill bar drawing logic goes here

def draw_buffs_bar(account_data: AccountData, win_pos: tuple, win_size: tuple, message_queue: list[tuple[int, SharedMessage]], skill_size: float = 28):
    if not settings.ShowHeroEffects and not settings.ShowHeroUpkeeps:
        return

    style = ImGui.get_style()

    PyImGui.push_style_var(ImGuiStyleVar.WindowRounding,0.0)
    PyImGui.push_style_var(ImGuiStyleVar.WindowPadding,0.0)
    PyImGui.push_style_var(ImGuiStyleVar.WindowBorderSize,0.0)
    PyImGui.push_style_var2(ImGuiStyleVar.WindowPadding,0.0,0.0)
    
    flags=( PyImGui.WindowFlags.NoCollapse | 
                PyImGui.WindowFlags.NoTitleBar |
                PyImGui.WindowFlags.NoScrollbar |
                PyImGui.WindowFlags.AlwaysAutoResize |
                PyImGui.WindowFlags.NoScrollWithMouse |
                PyImGui.WindowFlags.NoBringToFrontOnFocus |
                PyImGui.WindowFlags.NoResize |
                PyImGui.WindowFlags.NoBackground 
            ) 
    
    PyImGui.set_next_window_pos(
        (win_pos[0], win_pos[1] + win_size[1] + (13 if style.Theme == StyleTheme.Guild_Wars else 4)), PyImGui.ImGuiCond.Always)
    PyImGui.set_next_window_size((win_size[0], 0), PyImGui.ImGuiCond.Always)
    open = PyImGui.begin("##Buffs Bar" + account_data.AccountEmail, True, flags)
    PyImGui.pop_style_var(4)

    if open:
        draw_buffs_and_upkeeps(account_data, skill_size)
        
    PyImGui.end()
    pass  # Implementation of buffs bar drawing logic goes here

def draw_buffs_and_upkeeps(account_data: AccountData, skill_size: float = 28):
    style = ImGui.get_style()
    HARD_MODE_EFFECT_ID = 1912 
    
    effects = [effect for effect in account_data.PlayerBuffs if effect.Type == 2]
    upkeeps = [effect for effect in account_data.PlayerBuffs if effect.Type == 1]
    
    def draw_buff(effect: CachedSkillInfo, duration: float, remaining: float, draw_effect_frame: bool = True, skill_size: float = skill_size):
        if not effect.texture_path:
            ImGui.dummy(skill_size, skill_size)
        else:
            ImGui.image(effect.texture_path, (skill_size, skill_size), uv0=(0.125, 0.125) if not draw_effect_frame else (
                0.0625, 0.0625), uv1=(0.875, 0.875) if not draw_effect_frame else (0.9375, 0.9375))
            
        item_rect_min = PyImGui.get_item_rect_min()
        item_rect_max = PyImGui.get_item_rect_max()

        if draw_effect_frame:
            frame_texture, texture_state = effect.frame_texture, effect.texture_state
            frame_texture.draw_in_drawlist(
                item_rect_min[:2],
                (skill_size, skill_size),
                state=texture_state
            )

        if settings.ShowEffectDurations or settings.ShowShortEffectDurations:
            if duration > 0 and remaining and (not settings.ShowShortEffectDurations or remaining < 60000):
                progress_background_rect = (
                    item_rect_min[0] + 2, item_rect_max[1] - 4, item_rect_max[0] - 2, item_rect_max[1] - 1)

                PyImGui.draw_list_add_rect_filled(
                    progress_background_rect[0],
                    progress_background_rect[1],
                    progress_background_rect[2],
                    progress_background_rect[3],
                    Color(0, 0, 0, 255).color_int,
                    0,
                    0
                )

                progress_rect = (
                    progress_background_rect[0] + 1,
                    progress_background_rect[1] + 1,
                    progress_background_rect[2] - 2,
                    progress_background_rect[3] - 1
                )

                fraction = remaining / (duration * 1000.0)
                progress_width = (
                    progress_rect[2] - progress_rect[0]) * fraction
                PyImGui.draw_list_add_rect_filled(
                    progress_rect[0],
                    progress_rect[1],
                    progress_rect[0] + progress_width,
                    progress_rect[3],
                    effect.progress_color,
                    0,
                    0
                )

                remaining_text = f"{remaining/1000:.0f}" if remaining >= 1000 else f"{remaining/1000:.1f}".lstrip("0")
                    
                text_size = PyImGui.calc_text_size(remaining_text)
                offset_x = (skill_size - text_size[0]) / 2
                offset_y = (skill_size - text_size[1]) / 2

                PyImGui.draw_list_add_rect_filled(
                    item_rect_min[0] + offset_x - 1,
                    item_rect_min[1] + offset_y - 1,
                    item_rect_min[0] + offset_x + text_size[0] + 1,
                    item_rect_min[1] + offset_y + text_size[1] + 1,
                    Color(0, 0, 0, 150).color_int,
                    2,
                    0
                )
                PyImGui.draw_list_add_text(
                    item_rect_min[0] + offset_x,
                    item_rect_min[1] + offset_y,
                    style.Text.color_int,
                    remaining_text
                )


        if PyImGui.is_item_hovered():
            show_skill_tooltip(effect, show_usage=False)
    
    def draw_morale(morale : int, skill_size: float = skill_size):
        morale_display = f"{("+" if morale > 100 else "-")}{abs(100 - morale)}%"
        texture = ThemeTextures.DeathPenalty.value.get_texture() if morale < 100 else ThemeTextures.MoraleBoost.value.get_texture()
        ImGui.push_font("Regular", 11)            
        ImGui.dummy(skill_size, skill_size)
        item_rect_min = PyImGui.get_item_rect_min()
        item_rect_max = PyImGui.get_item_rect_max()
        
        item_rect = (item_rect_min[0], item_rect_min[1], item_rect_max[0] - item_rect_min[0], item_rect_max[1] - item_rect_min[1])
        texture.draw_in_drawlist(
            item_rect[:2],
            (skill_size, skill_size),
        )
        text_size = PyImGui.calc_text_size(morale_display)
        offset_x = (skill_size - text_size[0]) / 2
        offset_y = (skill_size - text_size[1])
        PyImGui.draw_list_add_text(
            item_rect[0] + offset_x,
            item_rect[1] + offset_y,
            Color(201, 188, 145, 255).color_int,
            morale_display
        )

        ImGui.pop_font()
        PyImGui.table_next_column()
    
    def draw_hardmode():
        # hardmode completed 1912
        if any(effect.SkillId == HARD_MODE_EFFECT_ID for effect in effects):
            if not HARD_MODE_EFFECT_ID in skill_cache:
                skill_cache[HARD_MODE_EFFECT_ID] = CachedSkillInfo(HARD_MODE_EFFECT_ID)

            to_kill = GLOBAL_CACHE.Map.GetFoesToKill()
            
            if to_kill > 0:
                texture = ThemeTextures.HardMode.value.get_texture(StyleTheme.Guild_Wars)
                pass
            else:
                texture = ThemeTextures.HardModeCompleted.value.get_texture(StyleTheme.Guild_Wars)
        
            ImGui.dummy(skill_size + 1, skill_size + 1)
            item_rect_min, item_rect_max, item_rect_size = ImGui.get_item_rect()
            texture.draw_in_drawlist(
                item_rect_min[:2],
                (skill_size + 1, skill_size + 1),
            )
                
            PyImGui.table_next_column()
        pass
    
    if settings.ShowHeroUpkeeps:
        ImGui.dummy(0, 24)
        PyImGui.same_line(0, 0)
        
        for index, upkeep in enumerate(upkeeps):
            if upkeep.SkillId == 0:
                continue

            if not upkeep.SkillId in skill_cache:
                skill_cache[upkeep.SkillId] = CachedSkillInfo(upkeep.SkillId)

            effect = skill_cache[upkeep.SkillId]
            duration = upkeep.Duration
            remaining = upkeep.Remaining

            draw_buff(effect, duration, remaining, False, 24)

        if any(upkeeps) and any(effects) and settings.ShowHeroEffects:
            PyImGui.new_line()
            PyImGui.set_cursor_pos_y(PyImGui.get_cursor_pos_y() - 4)

    if settings.ShowHeroEffects:     
        avail = PyImGui.get_content_region_avail()[0]
        style.CellPadding.push_style_var(0, 0)
        if ImGui.begin_table("##effects_table" + account_data.AccountEmail, max(1, round(avail / skill_size)), PyImGui.TableFlags.SizingFixedFit):
            PyImGui.table_next_row()
            PyImGui.table_next_column()
            
            if account_data.PlayerMorale != 100 and account_data.PlayerMorale != 0:
                draw_morale(account_data.PlayerMorale, skill_size)
                            
            draw_hardmode()
            
            #get each effect with unique id and take the longest duration for that id
            player_effects = {}
            
            for index, effect in enumerate(effects):
                remaining = effect.Remaining
                duration = effect.Duration
                effect_id = effect.SkillId
                
                if not effect_id or effect_id == HARD_MODE_EFFECT_ID:
                    continue
                
                if not effect_id in skill_cache:
                    skill_cache[effect_id] = CachedSkillInfo(effect_id)
                    
                if not effect_id in player_effects:
                    player_effects[effect_id] = (skill_cache[effect_id], remaining, duration)
                
                else:
                    cached_effect, existing_remaining, existing_duration = player_effects[effect_id]
                    
                    if remaining > existing_remaining:
                        player_effects[effect_id] = (cached_effect, remaining, duration)
                        
            for effect_id, (effect, remaining, duration) in player_effects.items():
                row = PyImGui.table_get_row_index()
                if row > settings.MaxEffectRows - 1:
                    break
                
                draw_buff(effect, duration, remaining, True, 28)
                PyImGui.table_next_column()
            
            ImGui.end_table() 
        style.CellPadding.pop_style_var()
            
        PyImGui.new_line()

def enter_skill_template_code(account_data : AccountData):
    global template_popup_open, template_code, template_account
    
    if not template_popup_open:
        return
    
    if template_popup_open:
        PyImGui.open_popup("Enter Skill Template Code")
    
    # PyImGui.set_next_window_size((300, 100), PyImGui.ImGuiCond.Always)
    PyImGui.set_window_pos(500 , 100, PyImGui.ImGuiCond.Always)
    if PyImGui.begin_popup("Enter Skill Template Code"):
        template_code = ImGui.input_text("##template_code", template_code)

        if ImGui.button("Load"):
            GLOBAL_CACHE.ShMem.SendMessage(
                GLOBAL_CACHE.Player.GetAccountEmail(),
                account_data.AccountEmail,           
                SharedCommandType.LoadSkillTemplate,
                ExtraData=(template_code, 0, 0, 0)
            )
            
            template_popup_open = False
            PyImGui.close_current_popup() 
            
        PyImGui.same_line(0, 10)
        if ImGui.button("Cancel"):
            PyImGui.close_current_popup()             
            template_popup_open = False

        if PyImGui.is_mouse_clicked(0) and not PyImGui.is_any_item_hovered():
            PyImGui.close_current_popup()             
            template_popup_open = False
            
        PyImGui.end_popup()
        
def draw_buttons(account_data: AccountData, cached_data: CacheData, message_queue: list[tuple[int, SharedMessage]], btn_size: float = 28):
    global message_cache
    style = ImGui.get_style()
    draw_textures = style.Theme in ImGui.Textured_Themes
    
    global template_popup_open, template_account
    is_explorable = GLOBAL_CACHE.Map.IsExplorable()
    if not ImGui.begin_child("##buttons" + account_data.AccountEmail, (84, 58), False,
                             PyImGui.WindowFlags.NoScrollbar | PyImGui.WindowFlags.NoScrollWithMouse):
        ImGui.end_child()
        return

    style = ImGui.get_style()
    same_map = GLOBAL_CACHE.Map.GetMapID() == account_data.MapID and GLOBAL_CACHE.Map.GetRegion()[0] == account_data.MapRegion and GLOBAL_CACHE.Map.GetDistrict() == account_data.MapDistrict
    player_email = GLOBAL_CACHE.Player.GetAccountEmail()
    account_email = account_data.AccountEmail

    btn_size = btn_size if draw_textures else btn_size - 1

    def is_queued(command: SharedCommandType, clear: bool = False) -> bool:
        cached_commands = message_cache.get(account_email, {}).get(command, {})

        if cached_commands:
            queued_commands = {index: msg for index, msg in message_queue if msg.Command == command and msg.ReceiverEmail == account_email and index in cached_commands} 
            if not queued_commands:
                if clear:
                    cached_commands.clear()
                           
            return len(queued_commands) > 0
        
        return False
            
    def draw_button(id_suffix: str, icon: str, tooltip: str, command: SharedCommandType, send_message: Callable[[], int] = lambda: False, get_status: Callable[[], bool] = lambda: False, new_line: bool = False):        
        """Reusable button creation logic with hover, icon, and tooltip."""
        btn_id = f"##{id_suffix}{account_email}"
        status = get_status()
        is_command_queued = is_queued(command, clear=True)
        
        if (draw_textures and PyImGui.invisible_button(btn_id, btn_size, btn_size)) or (not draw_textures and ImGui.button(btn_id, btn_size, btn_size)):
            if is_command_queued:
                return               
            
            message_index = send_message()            
            if message_index > -1:
                if account_data.AccountEmail not in message_cache:
                    message_cache[account_data.AccountEmail] = {}
                    
                if command not in message_cache[account_data.AccountEmail]:
                    message_cache[account_data.AccountEmail][command] = {}
                
                message_cache[account_data.AccountEmail][command][message_index] = ()


        hovered = PyImGui.is_item_hovered()
        item_rect_min = PyImGui.get_item_rect_min()
        if draw_textures:
            ThemeTextures.HeroPanelButtonBase.value.get_texture().draw_in_drawlist(
                item_rect_min, (btn_size, btn_size),
                state=TextureState.Active if status else TextureState.Normal,
                tint=(255, 255, 255, 255) if hovered else (200, 200, 200, 255)
            )

        ImGui.push_font("Regular", 10)
        text_size = PyImGui.calc_text_size(icon)
        PyImGui.draw_list_add_text(
            item_rect_min[0] + (btn_size - text_size[0]) / 2,
            item_rect_min[1] + (btn_size - text_size[1]) / 2,
            style.Text.color_int,
            icon
        )
        ImGui.pop_font()
        
        if hovered:
            ImGui.show_tooltip(tooltip)
        
        if not new_line:
            PyImGui.same_line(0, 0 if draw_textures else 1)
        else:
            PyImGui.set_cursor_pos_y(PyImGui.get_cursor_pos_y() - 4)

    if not is_explorable:
        player_x, player_y = GLOBAL_CACHE.Player.GetXY()
        target_id = Player.GetTargetID() or Player.GetAgentID()

        def invite_player():            
            if same_map:
                GLOBAL_CACHE.Party.Players.InvitePlayer(account_data.CharacterName)
                
            return GLOBAL_CACHE.ShMem.SendMessage(
                player_email,
                account_email,
                SharedCommandType.InviteToParty if same_map else SharedCommandType.TravelToMap,
                (account_data.PlayerID, 0, 0, 0) if same_map else (
                    GLOBAL_CACHE.Map.GetMapID(),
                    GLOBAL_CACHE.Map.GetRegion()[0],
                    GLOBAL_CACHE.Map.GetDistrict(),
                    GLOBAL_CACHE.Map.GetLanguage()[0],
                )
            )
        
        def load_template():
            global template_popup_open, template_code, template_account
            template_popup_open = True  
            template_code = ""
            template_account = account_data.AccountEmail
            
            return -1       
            
        buttons = [
            (
                "pixel_stack",
                commands.PixelStack.icon,
                commands.PixelStack.name,
                SharedCommandType.PixelStack,
                lambda: GLOBAL_CACHE.ShMem.SendMessage(player_email, account_email, SharedCommandType.PixelStack, (player_x, player_y, 0, 0)),
                lambda: is_queued(SharedCommandType.PixelStack),
            ),
            (
                "interact",
                IconsFontAwesome5.ICON_HAND_POINT_RIGHT,
                "Interact with Target",
                SharedCommandType.InteractWithTarget,
                lambda: GLOBAL_CACHE.ShMem.SendMessage(player_email, account_email, SharedCommandType.InteractWithTarget, (target_id, 0, 0, 0)),
                lambda: is_queued(SharedCommandType.InteractWithTarget),
            ),
            (
                "dialog",
                IconsFontAwesome5.ICON_COMMENT_DOTS,
                "Dialog with Target",
                SharedCommandType.TakeDialogWithTarget,
                lambda: GLOBAL_CACHE.ShMem.SendMessage(player_email, account_email, SharedCommandType.TakeDialogWithTarget, (target_id, 1, 0, 0)),
                lambda: is_queued(SharedCommandType.TakeDialogWithTarget),
                True,
            ),
            (
                "load_template",
                IconsFontAwesome5.ICON_FILE_IMPORT,
                "Load Skill Template",
                SharedCommandType.LoadSkillTemplate,
                load_template,
                lambda: is_queued(SharedCommandType.LoadSkillTemplate),
            ),
            (
                "invite_summon",
                IconsFontAwesome5.ICON_USER_PLUS,
                "Invite" if same_map else "Summon",
                SharedCommandType.InviteToParty if same_map else SharedCommandType.TravelToMap,
                invite_player,
                lambda: is_queued(SharedCommandType.InviteToParty) if same_map else is_queued(SharedCommandType.TravelToMap),
            ),
            (
                "focus_client",
                IconsFontAwesome5.ICON_DESKTOP,
                "Focus client",
                SharedCommandType.SetWindowActive,
                lambda: GLOBAL_CACHE.ShMem.SendMessage(
                    player_email,
                    account_email,
                    SharedCommandType.SetWindowActive,
                    (0, 0, 0, 0),
                ),
                lambda: is_queued(SharedCommandType.SetWindowActive),
            ),
        ]


        for btn in buttons:
            draw_button(*btn)
        
        if template_account == account_data.AccountEmail and template_account:    
            enter_skill_template_code(account_data)  

    else:        
        player_x, player_y = GLOBAL_CACHE.Player.GetXY()
        target_id = Player.GetTargetID() or Player.GetAgentID()
        
        def flag_hero_account():
            windows.capture_flag_all = False
            windows.capture_hero_flag = True
            windows.capture_hero_index = account_data.PartyPosition  
            return -1
        
        def clear_hero_flag():
            cached_data.HeroAI_vars.shared_memory_handler.set_player_property(account_data.PartyPosition, "IsFlagged", False)
            cached_data.HeroAI_vars.shared_memory_handler.set_player_property(account_data.PartyPosition, "FlagPosX", 0.0)
            cached_data.HeroAI_vars.shared_memory_handler.set_player_property(account_data.PartyPosition, "FlagPosY", 0.0)
            cached_data.HeroAI_vars.shared_memory_handler.set_player_property(account_data.PartyPosition, "FollowAngle", 0.0)
            return -1
        
        buttons = [
            # (id_suffix, icon, tooltip, command, args)
            ("pixel_stack", IconsFontAwesome5.ICON_COMPRESS_ARROWS_ALT, "Pixel Stack",
             SharedCommandType.PixelStack, lambda: GLOBAL_CACHE.ShMem.SendMessage(player_email, account_email, SharedCommandType.PixelStack, (player_x, player_y, 0, 0)), lambda: is_queued(SharedCommandType.PixelStack)),

            ("interact", IconsFontAwesome5.ICON_HAND_POINT_RIGHT, "Interact with Target",
             SharedCommandType.InteractWithTarget, lambda: GLOBAL_CACHE.ShMem.SendMessage(player_email, account_email, SharedCommandType.InteractWithTarget, (target_id, 0, 0, 0)), lambda: is_queued(SharedCommandType.InteractWithTarget)),

            ("dialog", IconsFontAwesome5.ICON_COMMENT_DOTS, "Dialog with Target",
             SharedCommandType.TakeDialogWithTarget, lambda: GLOBAL_CACHE.ShMem.SendMessage(player_email, account_email, SharedCommandType.TakeDialogWithTarget, (target_id, 1, 0, 0)), lambda: is_queued(SharedCommandType.TakeDialogWithTarget), True),

            ("flag", IconsFontAwesome5.ICON_FLAG, "Flag Target",
             SharedCommandType.NoCommand, flag_hero_account, lambda: IsHeroFlagged(cached_data, account_data.PartyPosition)),

            ("clear flag", IconsFontAwesome5.ICON_CIRCLE_XMARK, "Clear Flag",
             SharedCommandType.NoCommand, clear_hero_flag, lambda: False),
            
            ("focus client",
             IconsFontAwesome5.ICON_DESKTOP,
             "Focus client",
             SharedCommandType.SetWindowActive, lambda: GLOBAL_CACHE.ShMem.SendMessage(
                player_email,
                account_email,
                SharedCommandType.SetWindowActive,
                (0, 0, 0, 0),
             )),
        ]
        
        for btn in buttons:
            draw_button(*btn)
                        
    ImGui.end_child()

title_names: dict[str, str] = {}

def get_display_name(account_data: AccountData) -> str:    
    name = account_data.CharacterName        
    titles = [
        "the Brave",
        "the Mighty",
        "the Swift",
        "the Cunning",
        "the Wise",
        "the Fearless",
        "the Valiant",
        "the Bold",
        "the Fierce",
        "the Gallant",
        "the Noble",
        "the Daring",
        "the Resolute",
        "the Stalwart",
        "the Intrepid",
        "the Dauntless",
        "the Adventurous",
        "the Courageous",
        "the Heroic",
        "the Legendary"
    ]
    
    if not name in title_names:
        title_names[name] = "Robin " + random.choice(titles)
        
    name = title_names[name]
    return name if settings.Anonymous_PanelNames else account_data.CharacterName

def get_conditioned(account_data: AccountData) -> tuple[HealthState, bool, bool, bool, bool, bool]:
    buff_ids = [buff.SkillId for buff in account_data.PlayerBuffs]
    same_map = GLOBAL_CACHE.Map.GetMapID() == account_data.MapID and GLOBAL_CACHE.Map.GetRegion()[0] == account_data.MapRegion and GLOBAL_CACHE.Map.GetDistrict() == account_data.MapDistrict
    
    deep_wounded = 482 in buff_ids
    poisoned = 484 in buff_ids or 483 in buff_ids
    
    enchanted = GLOBAL_CACHE.Agent.IsEnchanted(account_data.PlayerID) if same_map else False
    conditioned = GLOBAL_CACHE.Agent.IsConditioned(account_data.PlayerID) if same_map else False
    hexed = GLOBAL_CACHE.Agent.IsHexed(account_data.PlayerID) if same_map else False
    has_weaponspell = GLOBAL_CACHE.Agent.IsWeaponSpelled(account_data.PlayerID) if same_map else False
        
    if poisoned:
        return HealthState.Poisoned, deep_wounded, enchanted, conditioned, hexed, has_weaponspell
    
    bleeding = 478 in buff_ids
    if bleeding:
        return HealthState.Bleeding, deep_wounded, enchanted, conditioned, hexed, has_weaponspell
    
    degen_hexed = GLOBAL_CACHE.Agent.IsDegenHexed(account_data.PlayerID) if same_map else False
    if degen_hexed:
        return HealthState.DegenHexed, deep_wounded, enchanted, conditioned, hexed, has_weaponspell
    
    return HealthState.Normal, deep_wounded, enchanted, conditioned, hexed, has_weaponspell

def draw_combined_hero_panel(account_data: AccountData, cached_data: CacheData, messages: list[tuple[int, SharedMessage]], open: bool = True):
    window_info = settings.HeroPanelPositions.get(account_data.AccountEmail, None)
    if not window_info or not window_info.open:
        return
    
    name = get_display_name(account_data)
    
    style = ImGui.get_style()
    ImGui.dummy(PyImGui.get_content_region_avail()[0], 22)
    
    item_rect_min = PyImGui.get_item_rect_min()
    item_rect_max = PyImGui.get_item_rect_max()
    item_rect = (item_rect_min[0], item_rect_min[1] + 5, item_rect_max[0] - item_rect_min[0], item_rect_max[1] - item_rect_min[1])
    
    ThemeTextures.HeaderLabelBackground.value.get_texture().draw_in_drawlist(
        item_rect[:2],
        item_rect[2:],
        tint=(225, 225, 225, 200) if style.Theme is StyleTheme.Guild_Wars else (255, 255, 255, 255)
    )
    
    text_size = PyImGui.calc_text_size(name)
    text_pos = (item_rect[0] + (item_rect[2] - text_size[0]) / 2, item_rect[1] + 2 + (item_rect[3] - text_size[1]) / 2)
    ImGui.push_font("Regular", 14)
    PyImGui.draw_list_add_text(
        text_pos[0],
        text_pos[1],
        style.Text.color_int,
        name
    )
    ImGui.pop_font()
    
    height = 28 if settings.ShowHeroSkills else 0
    height += 28 if settings.ShowHeroBars else 0
    height += 4 if settings.ShowHeroBars and settings.ShowHeroSkills else 0

    if height > 0:
        if ImGui.begin_child("##bars" + account_data.AccountEmail, (225, height)):
            curr_avail = PyImGui.get_content_region_avail()
            if settings.ShowHeroBars:
                health_state, deep_wounded, enchanted, conditioned, hexed, has_weaponspell = get_conditioned(account_data)
                
                health_clicked = draw_health_bar(curr_avail[0], 13, account_data.PlayerMaxHP,
                                account_data.PlayerHP, account_data.PlayerHealthRegen, health_state, deep_wounded, enchanted, conditioned, hexed, has_weaponspell)   
                                     
                PyImGui.set_cursor_pos_y(PyImGui.get_cursor_pos_y() - 4)
                
                energy_clicked = draw_energy_bar(curr_avail[0], 13, account_data.PlayerMaxEnergy,
                                account_data.PlayerEnergy, account_data.PlayerEnergyRegen)
                
                if health_clicked or energy_clicked:
                            if GLOBAL_CACHE.Map.GetMapID() == account_data.MapID:
                                GLOBAL_CACHE.Player.ChangeTarget(account_data.PlayerID)
                                
            if settings.ShowHeroSkills:
                if settings.ShowHeroBars:
                    PyImGui.set_cursor_pos_y(PyImGui.get_cursor_pos_y() - 4)
                
                draw_skill_bar(28, account_data, cached_data, messages)

        ImGui.end_child()

    if (settings.ShowHeroBars or settings.ShowHeroSkills) and settings.ShowHeroButtons:
        PyImGui.same_line(0, 2)
        
    if settings.ShowHeroButtons:
        draw_buttons(account_data, cached_data, messages, 28)

    draw_buffs_and_upkeeps(account_data, 28)    

def draw_hero_panel(window: WindowModule, account_data: AccountData, cached_data: CacheData, messages: list[tuple[int, SharedMessage]]):   
    window_info = settings.HeroPanelPositions.get(account_data.AccountEmail, None)
    if not window_info or not window_info.open:
        return
    
    window.open = window_info.open
    window.collapse = window_info.collapsed
    
    global title_names
    style = ImGui.get_style()
    style.WindowPadding.push_style_var(4, 1)
    
    collapsed = window.collapse
    player_pos = GLOBAL_CACHE.Player.GetXY()
    hero_pos = (account_data.PlayerPosX, account_data.PlayerPosY)
    outside_compass_range = Utils.Distance(player_pos, hero_pos) > Range.Compass.value + 10
    
    if outside_compass_range:
        style.TitleBg.push_color((100, 0, 0, 150))
        style.WindowBg.push_color((100, 0, 0, 150))
    PyImGui.set_next_window_size(319, 69 if style.Theme is StyleTheme.Guild_Wars else 86)
    open = window.begin(None, PyImGui.WindowFlags.NoResize)
    # ConsoleLog("HeroAI", f"{window.window_size}")
    if outside_compass_range:
        style.WindowBg.pop_color()
        style.TitleBg.pop_color()
    style.WindowPadding.pop_style_var()

    prof_primary, prof_secondary = "", ""
    prof_primary = ProfessionShort(
        account_data.PlayerProfession[0]).name if account_data.PlayerProfession[0] != 0 else ""
    prof_secondary = ProfessionShort(
        account_data.PlayerProfession[1]).name if account_data.PlayerProfession[1] != 0 else ""
    win_size = PyImGui.get_window_size()
    win_pos = PyImGui.get_window_pos()

    text_pos = (win_pos[0] + 25, win_pos[1] - 23 +
                7) if style.Theme == StyleTheme.Guild_Wars else (win_pos[0] + 25, win_pos[1] + 7)

    PyImGui.push_clip_rect(
        win_pos[0], win_pos[1] - 20, win_size[0] - 30, 50, False)
    ImGui.push_font("Regular", 13)
        
    name = get_display_name(account_data)

    PyImGui.draw_list_add_text(text_pos[0], text_pos[1], style.Text.color_int,
                               f"{prof_primary}{("/" if prof_secondary else "")}{prof_secondary}{account_data.PlayerLevel} {name}")
    ImGui.pop_font()
    PyImGui.pop_clip_rect()

    pos = window.window_pos
    collapsed = window.collapse
    
    if open and window.open and not window.collapse:
        if style.Theme == StyleTheme.Guild_Wars:
            PyImGui.spacing()

        avail = PyImGui.get_content_region_avail()

        height = 28 if settings.ShowHeroSkills else 0
        height += 28 if settings.ShowHeroBars else 0
        height += 4 if settings.ShowHeroBars and settings.ShowHeroSkills else 0

        if height > 0:
            if ImGui.begin_child("##bars" + account_data.AccountEmail, (225, height)):
                curr_avail = PyImGui.get_content_region_avail()
                if settings.ShowHeroBars:
                    health_state, deep_wounded, enchanted, conditioned, hexed, has_weaponspell  = get_conditioned(account_data)
                    
                    health_clicked = draw_health_bar(curr_avail[0], 13, account_data.PlayerMaxHP,
                                    account_data.PlayerHP, account_data.PlayerHealthRegen, health_state, deep_wounded, enchanted, conditioned, hexed, has_weaponspell )
                    PyImGui.set_cursor_pos_y(PyImGui.get_cursor_pos_y() - 4)
                    energy_clicked = draw_energy_bar(curr_avail[0], 13, account_data.PlayerMaxEnergy,
                                                       account_data.PlayerEnergy, account_data.PlayerEnergyRegen)
                    if health_clicked or energy_clicked:
                        if GLOBAL_CACHE.Map.GetMapID() == account_data.MapID:
                            GLOBAL_CACHE.Player.ChangeTarget(account_data.PlayerID)
                            
                if settings.ShowHeroSkills:
                    if settings.ShowHeroBars:
                        PyImGui.set_cursor_pos_y(PyImGui.get_cursor_pos_y() - 4)
                    
                    draw_skill_bar(28, account_data, cached_data, messages)

            ImGui.end_child()

        if (settings.ShowHeroBars or settings.ShowHeroSkills) and settings.ShowHeroButtons:
            PyImGui.same_line(0, 2)
            
        if settings.ShowHeroButtons:
            draw_buttons(account_data, cached_data, messages, 28)

        draw_buffs_bar(account_data, win_pos, win_size, messages, 28)
        window.process_window()
    
    collapsed = PyImGui.is_window_collapsed()
    
    window.process_window()
    window.collapse = collapsed if style.Theme != StyleTheme.Guild_Wars else window.collapse
    
    if window.collapse != window_info.collapsed or window.changed or window.open != window_info.open:            
        if Console.is_window_active():
            window_info.open = window.open
            window_info.collapsed = window.collapse
            window_info.x = round(window.window_pos[0])
            window_info.y = round(window.window_pos[1])
            
            settings.save_settings()
        
    window.end()
            
        
    pass  # Implementation of hero panel drawing logic goes here

def draw_button(id_suffix: str, icon: str, w : float = 0, h : float = 0, active : bool = False, enabled : bool = True) -> bool:       
    style = ImGui.get_style()
    draw_textures = style.Theme in ImGui.Textured_Themes    
    btn_id = f"##{id_suffix}"    
    clicked = (draw_textures and PyImGui.invisible_button(btn_id, w, h)) or (not draw_textures and ImGui.button(btn_id, w, h))


    hovered = PyImGui.is_item_hovered()
    mouse_down = PyImGui.is_mouse_down(0)
    item_rect_min = PyImGui.get_item_rect_min()
    if draw_textures:
        ThemeTextures.HeroPanelButtonBase.value.get_texture().draw_in_drawlist(
            item_rect_min, (w, h),
            state=TextureState.Active if active else TextureState.Normal,
            tint=(255, 255, 255, 85) if not enabled else (255, 255, 255, 255) if hovered and mouse_down else (200, 200, 200, 255) if hovered else (175, 175, 175, 255)
        )

    ImGui.push_font("Regular", 10)
    text_size = PyImGui.calc_text_size(icon)
    PyImGui.draw_list_add_text(
        item_rect_min[0] + (w - text_size[0]) / 2,
        item_rect_min[1] + (h - text_size[1]) / 2,
        style.Text.color_int if enabled else Color(115, 115, 115, 255).color_int,
        icon
    )
    ImGui.pop_font()   
    return clicked and enabled

def send_command_to_all_heroes(accounts: list[AccountData], command: SharedCommandType, param: tuple = (), extra_data: tuple = (), include_self: bool = False):
    account_mail = GLOBAL_CACHE.Player.GetAccountEmail()
    for account in accounts:
        if not include_self and account.AccountEmail == account_mail:
            continue
        
        GLOBAL_CACHE.ShMem.SendMessage(
            account_mail,
            account.AccountEmail,
            command,
            param,
            ExtraData=extra_data
        )

consumables = [
    (ModelID.Essence_Of_Celerity, ("Textures\\Consumables\\Trimmed\\Essence_of_Celerity.png", (ModelID.Essence_Of_Celerity.value, GLOBAL_CACHE.Skill.GetID("Essence_of_Celerity_item_effect"), 0, 0))),
    (ModelID.Grail_Of_Might, ("Textures\\Consumables\\Trimmed\\Grail_of_Might.png", (ModelID.Grail_Of_Might.value, GLOBAL_CACHE.Skill.GetID("Grail_of_Might_item_effect"), 0, 0))),
    (ModelID.Armor_Of_Salvation, ("Textures\\Consumables\\Trimmed\\Armor_of_Salvation.png", (ModelID.Armor_Of_Salvation.value, GLOBAL_CACHE.Skill.GetID("Armor_of_Salvation_item_effect"), 0, 0))),
    
    (0, ("", (0, 0, 0, 0))),  # Empty slot
    (0, ("", (0, 0, 0, 0))),  # Empty slot
    (ModelID.Rainbow_Candy_Cane, ("Textures\\Consumables\\Trimmed\\Rainbow_Candy_Cane.png", (ModelID.Rainbow_Candy_Cane.value, 0, ModelID.Honeycomb.value, 0))),
    
    (ModelID.Birthday_Cupcake, ("Textures\\Consumables\\Trimmed\\Birthday_Cupcake.png", (ModelID.Birthday_Cupcake.value, GLOBAL_CACHE.Skill.GetID("Birthday_Cupcake_skill"), 0, 0))),
    (ModelID.Candy_Apple, ("Textures\\Consumables\\Trimmed\\Candy_Apple.png", (ModelID.Candy_Apple.value, GLOBAL_CACHE.Skill.GetID("Candy_Apple_skill"), 0, 0))),
    (ModelID.Candy_Corn, ("Textures\\Consumables\\Trimmed\\Candy_Corn.png", (ModelID.Candy_Corn.value, GLOBAL_CACHE.Skill.GetID("Candy_Corn_skill"), 0, 0))),
    (ModelID.Golden_Egg, ("Textures\\Consumables\\Trimmed\\Golden_Egg.png", (ModelID.Golden_Egg.value, GLOBAL_CACHE.Skill.GetID("Golden_Egg_skill"), 0, 0))),
    (ModelID.Slice_Of_Pumpkin_Pie, ("Textures\\Consumables\\Trimmed\\Slice_of_Pumpkin_Pie.png", (ModelID.Slice_Of_Pumpkin_Pie.value, GLOBAL_CACHE.Skill.GetID("Pie_Induced_Ecstasy"), 0, 0))),
    (ModelID.War_Supplies, ("Textures\\Consumables\\Trimmed\\War_Supplies.png", (ModelID.War_Supplies.value, GLOBAL_CACHE.Skill.GetID("Well_Supplied"), 0, 0))),
    
    (ModelID.Drake_Kabob, ("Textures\\Consumables\\Trimmed\\Drake_Kabob.png", (ModelID.Drake_Kabob.value, GLOBAL_CACHE.Skill.GetID("Drake_Skin"), 0, 0))),
    (ModelID.Bowl_Of_Skalefin_Soup, ("Textures\\Consumables\\Trimmed\\Bowl_of_Skalefin_Soup.png", (ModelID.Bowl_Of_Skalefin_Soup.value, GLOBAL_CACHE.Skill.GetID("Skale_Vigor"), 0, 0))),
    (ModelID.Pahnai_Salad, ("Textures\\Consumables\\Trimmed\\Pahnai_Salad.png", (ModelID.Pahnai_Salad.value, GLOBAL_CACHE.Skill.GetID("Pahnai_Salad_item_effect"), 0, 0))),
    # (ModelID.Dwarven_Ale, ("Textures\\Consumables\\Trimmed\\Dwarven_Ale.png", (ModelID.Dwarven_Ale.value, GLOBAL_CACHE.Skill.GetID("Dwarven_Ale_item_effect"), 0, 0))),
]

def _post_pcon_message(params, cached_data: CacheData):
    self_account = GLOBAL_CACHE.ShMem.GetAccountDataFromEmail(cached_data.account_email)
    if not self_account:
        return
    
    accounts = GLOBAL_CACHE.ShMem.GetAllAccountData()
    sender_email = cached_data.account_email
    for account in accounts:        
        GLOBAL_CACHE.ShMem.SendMessage(sender_email, account.AccountEmail, SharedCommandType.PCon, params)

#_post_pcon_message((ModelID.Essence_Of_Celerity.value, GLOBAL_CACHE.Skill.GetID("Essence_of_Celerity_item_effect"), 0, 0))
def draw_consumables_window(cached_data: CacheData):
    global configure_consumables_window_open
    style = ImGui.get_style()
    draw_textures = style.Theme in ImGui.Textured_Themes
    
    if not configure_consumables_window_open:
        return
    
    
    PyImGui.open_popup("Configure Consumables")
    
    if PyImGui.begin_popup("Configure Consumables"):        
        if PyImGui.is_window_appearing():
            io = PyImGui.get_io()
            mouse_x, mouse_y = io.mouse_pos_x, io.mouse_pos_y
            PyImGui.set_window_pos(mouse_x, mouse_y - 170, PyImGui.ImGuiCond.Always)
            
        ImGui.text("Consumable configuration window")
        btn_size = 32
        style.CellPadding.push_style_var(2, 2)
        if ImGui.begin_table("##ConTable", 6, PyImGui.TableFlags.SizingStretchProp):
            PyImGui.table_next_column()
            
            for model_id, (texture_path, params) in consumables:        
                if model_id == 0:
                    PyImGui.table_next_column()
                    continue
                PyImGui.push_style_color(PyImGui.ImGuiCol.Button, (0, 0, 0, 0))
                PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonHovered, (0, 0, 0, 0))
                PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonActive, (0, 0, 0, 0))
                PyImGui.push_style_color(PyImGui.ImGuiCol.Text, (0, 0, 0, 0))
                if PyImGui.button(f"##ConConfig {model_id}", btn_size, btn_size):
                    _post_pcon_message(params, cached_data) 
                PyImGui.pop_style_color(4)
                
                x,y = PyImGui.get_item_rect_min()
                ThemeTextures.Inventory_Slots.value.get_texture().draw_in_drawlist((x, y), (btn_size, btn_size))
                ImGui.DrawTextureInDrawList((x + 2, y + 2), (btn_size - 4, btn_size - 4), texture_path)
                    
                ImGui.show_tooltip(f"Use {model_id.name.replace('_', ' ')}")
                PyImGui.table_next_column()
                        
            ImGui.end_table()
            
        style.CellPadding.pop_style_var()
                
        if PyImGui.is_mouse_clicked(0) and not PyImGui.is_any_item_hovered() and not PyImGui.is_window_hovered():
            configure_consumables_window_open = False
            PyImGui.close_current_popup()
            
        PyImGui.end_popup()
        
    
    pass  # Implementation of consumables window drawing logic goes here

def draw_command_panel(window: WindowModule, accounts : list[AccountData], cached_data: CacheData):
    style = ImGui.get_style()

    size = window.window_size
    style.WindowPadding.push_style_var(5, 5)
    
    info = settings.HeroPanelPositions.get(window.window_name, None)
    # if info:
    #     PyImGui.set_next_window_pos((info.x, info.y), PyImGui.ImGuiCond.Always)
        
    if window.begin():
        source_game_option = cached_data.HeroAI_vars.global_control_game_struct
        game_options = GameOptionStruct()
        
        avail = PyImGui.get_content_region_avail()
        avail_x = avail[0]
        btn_size = 32
        table_width = btn_size * 5 + 30
        if ImGui.begin_child("##GlobalHeroOptionsChild",( table_width, (btn_size  * 2) - 6), False, PyImGui.WindowFlags.NoScrollbar | PyImGui.WindowFlags.NoScrollWithMouse):
            style.ItemSpacing.push_style_var(0, 0)
            style.CellPadding.push_style_var(2, 2)
            if PyImGui.begin_table("GameOptionTable", 5, 0, table_width, btn_size + 2):                 
                PyImGui.table_next_row()
                PyImGui.table_next_column()
                
                game_options.Following = ImGui.toggle_icon_button(IconsFontAwesome5.ICON_RUNNING + "##Following", source_game_option.Following, btn_size, btn_size)
                ImGui.show_tooltip("Following")
                PyImGui.table_next_column()
                game_options.Avoidance = ImGui.toggle_icon_button(IconsFontAwesome5.ICON_PODCAST + "##Avoidance", source_game_option.Avoidance, btn_size, btn_size)
                ImGui.show_tooltip("Avoidance")
                PyImGui.table_next_column()
                game_options.Looting = ImGui.toggle_icon_button(IconsFontAwesome5.ICON_COINS + "##Looting", source_game_option.Looting, btn_size, btn_size)
                ImGui.show_tooltip("Looting")
                PyImGui.table_next_column()
                game_options.Targeting = ImGui.toggle_icon_button(IconsFontAwesome5.ICON_BULLSEYE + "##Targeting", source_game_option.Targeting, btn_size, btn_size)
                ImGui.show_tooltip("Targeting")
                PyImGui.table_next_column()
                game_options.Combat = ImGui.toggle_icon_button(IconsFontAwesome5.ICON_SKULL_CROSSBONES + "##Combat", source_game_option.Combat, btn_size, btn_size)
                ImGui.show_tooltip("Combat")        
                
                PyImGui.end_table()


            style.ButtonPadding.push_style_var(5 if style.Theme not in ImGui.Textured_Themes else 0, 3 if style.Theme not in ImGui.Textured_Themes else 2)
            if PyImGui.begin_table("SkillsTable", NUMBER_OF_SKILLS, 0, table_width, (btn_size / 3)):
                PyImGui.table_next_row()
                PyImGui.table_next_column()
                skill_size = table_width / NUMBER_OF_SKILLS - 6
                
                for i in range(NUMBER_OF_SKILLS):
                    game_options.Skills[i].Active = ImGui.toggle_button(f"{i + 1}##Skill{i}", source_game_option.Skills[i].Active, skill_size, skill_size)
                    ImGui.show_tooltip(f"Skill {i + 1}")
                    PyImGui.table_next_column()
                        
                PyImGui.end_table()
            style.ButtonPadding.pop_style_var()
                    
            style.ButtonPadding.pop_style_var()
            style.ItemSpacing.pop_style_var()
            style.CellPadding.pop_style_var()

        ImGui.end_child()
                
        # is_window_active = Console.is_window_active()
        # if is_window_active:
        CompareAndSubmitGameOptions(cached_data, game_options)

        window.process_window()
        
        if window.changed:                
            if Console.is_window_active():                
                window_info = settings.HeroPanelPositions.get(window.window_name, Settings.HeroPanelInfo())
                
                if window_info:
                    if not window_info in settings.HeroPanelPositions.values():
                        settings.HeroPanelPositions[window.window_name] = window_info
                        
                    window_info.x = round(window.window_pos[0])
                    window_info.y = round(window.window_pos[1])
                    window_info.collapsed = window.collapse
                    window_info.open = window.open                    
                    settings.save_settings()
            
    window.end()
    style.WindowPadding.pop_style_var()
    
    pass  # Implementation of command panel drawing logic goes here

hotbars : dict[str, WindowModule] = {}
configure_hotbar = None
assign_command_slot = None

# Offsets for different UI themes and hotbar positions
hotbar_offsets : dict[StyleTheme, dict[str, dict]] = {
    StyleTheme.Guild_Wars: {
        "PartyWindow": {
            HorizontalAlignment.LeftOf.name: -8,
            HorizontalAlignment.Left.name: 0,
            HorizontalAlignment.Center.name: 2,
            HorizontalAlignment.Right.name: 0,
            HorizontalAlignment.RightOf.name: 10,
            
            VerticalAlignment.Above.name: -4,
            VerticalAlignment.Below.name: 2,
            },
        "Skillbar": {
            HorizontalAlignment.LeftOf.name: -17,
            HorizontalAlignment.Left.name: -6,
            HorizontalAlignment.Center.name: 2,
            HorizontalAlignment.Right.name: 11,
            HorizontalAlignment.RightOf.name: 19,
            
            VerticalAlignment.Above.name: 5,
            VerticalAlignment.Top.name: 0,
            VerticalAlignment.Bottom.name: 8,
            VerticalAlignment.Below.name: 8,
            },
    },
    StyleTheme.ImGui: {
        "PartyWindow": {
            HorizontalAlignment.LeftOf.name: -8,
            HorizontalAlignment.Left.name: 0,
            HorizontalAlignment.Center.name: 2,
            HorizontalAlignment.Right.name: 0,
            HorizontalAlignment.RightOf.name: 10,
            
            VerticalAlignment.Above.name: -4,
            VerticalAlignment.Below.name: 2,
            },
        "Skillbar": {
            HorizontalAlignment.LeftOf.name: -17,
            HorizontalAlignment.Left.name: -6,
            HorizontalAlignment.Center.name: 2,
            HorizontalAlignment.Right.name: 11,
            HorizontalAlignment.RightOf.name: 19,
            
            VerticalAlignment.Above.name: 5,
            VerticalAlignment.Top.name: 0,
            VerticalAlignment.Bottom.name: 8,
            VerticalAlignment.Below.name: 8,
            },
    },
    StyleTheme.Minimalus: {
        "PartyWindow": {
            HorizontalAlignment.LeftOf.name: -8,
            HorizontalAlignment.Left.name: 6,
            HorizontalAlignment.Center.name: 1,
            HorizontalAlignment.Right.name: -3,
            HorizontalAlignment.RightOf.name: 10,
            
            VerticalAlignment.Above.name: -1,
            VerticalAlignment.Top.name: -2,
            VerticalAlignment.Bottom.name: -10,
            VerticalAlignment.Below.name: -11,
            },
        "Skillbar": {
            HorizontalAlignment.LeftOf.name: 1,
            HorizontalAlignment.Left.name: 0,
            HorizontalAlignment.Center.name: 2,
            HorizontalAlignment.Right.name: 1,
            HorizontalAlignment.RightOf.name: 1,
            
            VerticalAlignment.Above.name: 1,
            VerticalAlignment.Top.name: 0,
            VerticalAlignment.Bottom.name: 1,
            VerticalAlignment.Below.name: 0,
            },
    },
}
    
def draw_hotbar(hotbar: Settings.CommandHotBar, accounts: list[AccountData]):
    global configure_hotbar
    style = ImGui.get_style()
    window = hotbars.get(hotbar.identifier, None)
    
    btn_size = hotbar.button_size
    rows = len(hotbar.commands)
    cols = max(1, max(len(row) for _, row in hotbar.commands.items()) if rows > 0 else 0)
    cell_spacing = (1, 1)
    
    style.CellPadding.push_style_var(cell_spacing[0], cell_spacing[1])

    height = max(btn_size, rows * (btn_size + cell_spacing[1]))
    width = max(btn_size, cols * (btn_size + cell_spacing[0]) - 1)
    
    if not window:
        window = WindowModule(hotbar.identifier, hotbar.identifier, window_pos=(hotbar.position[0], hotbar.position[1]), window_flags=PyImGui.WindowFlags(PyImGui.WindowFlags.NoTitleBar | PyImGui.WindowFlags.AlwaysAutoResize), can_close=False)
        hotbars[hotbar.identifier] = window
        
    if hotbar.docked is not Docked.Freely:
        window_width = window.window_size[0]
        window_height = window.window_size[1]
        
        window_half_size = (window_width / 2, window_height / 2)
        
        match hotbar.docked:
            case Docked.PartyWindow:
                fid = UIManager.GetFrameIDByHash(PARTY_WINDOW_HASH)
                party_window = UIManager.GetFrameCoords(fid) if fid != 0 and UIManager.FrameExists(fid) else None
                
                if party_window:
                    left, top, right, bottom = party_window
                    
                    offsets = hotbar_offsets.get(style.Theme, hotbar_offsets.get(StyleTheme.ImGui, {})).get("PartyWindow", {})                    
                    x_offset = offsets.get(hotbar.alignment.horizontal.name, 0)
                    y_offset = offsets.get(hotbar.alignment.vertical.name, 0)
                    
                    x , y = ImGui.get_position_aligned(
                        hotbar.alignment,
                        (left, top),
                        (right - left, bottom - top),
                        (window_width, window_height),
                        (x_offset, y_offset))
                    
                    hotbar.position = (int(x), int(y))
                
            case Docked.Skillbar:
                fid = UIManager.GetFrameIDByHash(SKILLBAR_WINDOW_HASH)
                skillbar_window = UIManager.GetFrameCoords(fid) if fid != 0 and UIManager.FrameExists(fid) else None
                if skillbar_window:
                    left, top, right, bottom = skillbar_window
                    
                    offsets = hotbar_offsets.get(style.Theme, hotbar_offsets.get(StyleTheme.ImGui, {})).get("Skillbar", {})       
                    x_offset = offsets.get(hotbar.alignment.horizontal.name, 0)
                    y_offset = offsets.get(hotbar.alignment.vertical.name, 0)
                    
                    x , y = ImGui.get_position_aligned(
                        hotbar.alignment,
                        (left, top),
                        (right - left, bottom - top),
                        (window_width, window_height),
                        (x_offset, y_offset))
                    
                    hotbar.position = (int(x), int(y))
        
        PyImGui.set_next_window_pos(hotbar.position, PyImGui.ImGuiCond.Always)
           

    size = window.window_size
    style.WindowPadding.push_style_var(5, 5)
    draw_textures = style.Theme in ImGui.Textured_Themes
    
    if window.begin():
        explorable = GLOBAL_CACHE.Map.IsExplorable()
        
        is_window_active = Console.is_window_active()

        if ImGui.begin_child("##HotbarCommandsChild" + hotbar.identifier, (width, height), False, PyImGui.WindowFlags.NoScrollbar | PyImGui.WindowFlags.NoScrollWithMouse):
            if PyImGui.is_rect_visible(width, height):
                if ImGui.begin_table("##HotbarTable" + hotbar.identifier, cols, PyImGui.TableFlags.NoFlag, width=width, height=height):
                    PyImGui.table_next_row()
                    PyImGui.table_next_column()
                    
                    def draw_cmnd_tooltip(tooltip: str):
                        if PyImGui.is_item_hovered():
                            PyImGui.set_next_window_size((250, 0), PyImGui.ImGuiCond.Always)
                            if ImGui.begin_tooltip():
                                ImGui.text_wrapped(tooltip)
                                
                                ImGui.text_colored(
                                    "Shift + Left Click to configure hotbar",
                                    gray_color.color_tuple     ,
                                    12               
                                )
                                
                                ImGui.text_colored(
                                    "Ctrl + Left Click to assign command",
                                    gray_color.color_tuple      ,
                                    12               
                                )
                            
                                ImGui.end_tooltip()

                    for row, cmd_row in hotbar.commands.items():
                        for col, cmd_name in cmd_row.items():
                            cmd = commands.Commands.get(cmd_name, None)
                            if not cmd:
                                ImGui.dummy(btn_size, btn_size)
                                ImGui.push_font("Regular", 24)
                                text_size = PyImGui.calc_text_size("?")
                                item_rect_min = PyImGui.get_item_rect_min()
                                
                                text_x = item_rect_min[0] + (btn_size - text_size[0]) / 2
                                text_y = item_rect_min[1] + (btn_size - text_size[1]) / 2 + 2
                                PyImGui.draw_list_add_text(text_x, text_y, style.Text.color_int, "?")
                                ImGui.pop_font()
                                if draw_textures:
                                    ThemeTextures.Skill_Slot_Empty.value.get_texture().draw_in_drawlist(
                                        (item_rect_min[0] + 1, item_rect_min[1] + 1),
                                        (btn_size - 2, btn_size - 2),
                                        tint=(255, 255, 255, 255) if PyImGui.is_item_hovered() else (200, 200, 200, 255)
                                    )
                                else:
                                    PyImGui.draw_list_add_rect_filled(
                                        item_rect_min[0] + 1, 
                                        item_rect_min[1] + 1,
                                        item_rect_min[0] + btn_size - 2, 
                                        item_rect_min[1] + btn_size - 2,
                                        style.Button.opacify(0.3).color_int,
                                        style.FrameRounding.value1,
                                        0,
                                    )
                                    PyImGui.draw_list_add_rect(
                                        item_rect_min[0] + 1, 
                                        item_rect_min[1] + 1,
                                        item_rect_min[0] + btn_size - 2, 
                                        item_rect_min[1] + btn_size - 2,
                                        style.Button.color_int,
                                        style.FrameRounding.value1,
                                        0,
                                        1
                                    )

                            elif cmd.is_separator:
                                ImGui.dummy(btn_size, btn_size)
                                item_rect_min = PyImGui.get_item_rect_min()
                                if draw_textures:
                                    ThemeTextures.Skill_Slot_Empty.value.get_texture().draw_in_drawlist(
                                        (item_rect_min[0] + 1, item_rect_min[1] + 1),
                                        (btn_size - 2, btn_size - 2),
                                        tint=(255, 255, 255, 255) if PyImGui.is_item_hovered() else (200, 200, 200, 255)
                                    )
                                else:
                                    PyImGui.draw_list_add_rect_filled(
                                        item_rect_min[0] + 1, 
                                        item_rect_min[1] + 1,
                                        item_rect_min[0] + btn_size - 2, 
                                        item_rect_min[1] + btn_size - 2,
                                        style.Button.opacify(0.3).color_int,
                                        style.FrameRounding.value1,
                                        0,
                                    )
                                    PyImGui.draw_list_add_rect(
                                        item_rect_min[0] + 1, 
                                        item_rect_min[1] + 1,
                                        item_rect_min[0] + btn_size - 2, 
                                        item_rect_min[1] + btn_size - 2,
                                        style.Button.color_int,
                                        style.FrameRounding.value1,
                                        0,
                                        1
                                    )
                            else:
                                valid_map_type = True
                                if cmd.map_types and explorable:
                                    valid_map_type = "Explorable" in cmd.map_types
                                    
                                elif cmd.map_types and not explorable:
                                    valid_map_type = "Outpost" in cmd.map_types
                                    
                                if draw_button(cmd.name, cmd.icon, btn_size, btn_size, False, valid_map_type):
                                    cmd(accounts)
                                

                            if PyImGui.is_item_clicked(0) and PyImGui.get_io().key_shift:
                                configure_hotbar = hotbar
                            
                            elif PyImGui.is_item_clicked(0) and PyImGui.get_io().key_ctrl:
                                global assign_command_slot
                                assign_command_slot = (hotbar.identifier, row, col)
                                
                            draw_cmnd_tooltip(cmd.tooltip if cmd else f"Unknown command '{cmd_name}'")
                            PyImGui.table_next_column()
                            
                    ImGui.end_table()
                
        ImGui.end_child()
        style.CellPadding.pop_style_var()


        pos = PyImGui.get_window_pos()
        
        if window.changed:
            if is_window_active and hotbar.identifier in settings.CommandHotBars and hotbar.docked is Docked.Freely:
                settings.CommandHotBars[hotbar.identifier].position = (int(pos[0]), int(pos[1]))
                settings.save_settings()
            
    window.end()
    style.WindowPadding.pop_style_var()
    
def draw_command_select_popup():
    global assign_command_slot
    
    if assign_command_slot is None:
        return        
    
    style = ImGui.get_style()
    PyImGui.open_popup("Assign Command")
    PyImGui.set_next_window_size((250, 300), PyImGui.ImGuiCond.Always)
    
    if PyImGui.begin_popup("Assign Command"):
        is_appearing = PyImGui.is_window_appearing()
        if is_appearing:
            io = PyImGui.get_io()
            mouse_x, mouse_y = io.mouse_pos_x, io.mouse_pos_y
            PyImGui.set_window_pos(mouse_x, mouse_y - 170, PyImGui.ImGuiCond.Always)

        identifier, row, col = assign_command_slot[0], assign_command_slot[1], assign_command_slot[2]
        
        hotbar = settings.CommandHotBars.get(identifier, None)
        if not hotbar:
            assign_command_slot = None
            PyImGui.close_current_popup()
            return

        ImGui.text(f"Command Slot [{assign_command_slot[1]}|{assign_command_slot[2]}]")

        if ImGui.begin_child("##CommandSelectChild", (0, 0), True):
            for cmd_name, cmd in commands.Commands.items():
                PyImGui.begin_group()
                draw_button(cmd.name, cmd.icon, 32, 32)
                PyImGui.same_line(0, 5)
                ImGui.text_aligned(cmd_name, 0, 32, Alignment.MidLeft, 14)
                PyImGui.end_group()

                if PyImGui.is_item_clicked(0):
                    hotbar.commands[row][col] = cmd.name
                    settings.save_settings()
                    
                    assign_command_slot = None
                    PyImGui.close_current_popup()
                    
                ImGui.show_tooltip(cmd.description or cmd.tooltip)
            
        ImGui.end_child()
                    
        if not is_appearing and PyImGui.is_mouse_clicked(0) and not PyImGui.is_any_item_hovered() and not PyImGui.is_window_hovered():
            assign_command_slot = None
            PyImGui.close_current_popup()
            
        PyImGui.end_popup()

def draw_configure_hotbar():
    global configure_hotbar
    
    if configure_hotbar is None:
        return        
    
    style = ImGui.get_style()
    PyImGui.open_popup("Configure Hotbar")

    if PyImGui.begin_popup("Configure Hotbar"):
        is_appearing = PyImGui.is_window_appearing()
        if is_appearing:
            io = PyImGui.get_io()
            mouse_x, mouse_y = io.mouse_pos_x, io.mouse_pos_y
            PyImGui.set_window_pos(mouse_x, mouse_y - 80, PyImGui.ImGuiCond.Always)

        ImGui.text(f"Configure '{configure_hotbar.identifier}'")
        rows = len(configure_hotbar.commands)
        cols = max(1, max(len(row) for _, row in configure_hotbar.commands.items()) if rows > 0 else 0)
        
        button_size = ImGui.input_int("Button Size", configure_hotbar.button_size)
        if button_size != configure_hotbar.button_size and button_size >= 10 and button_size <= 256:
            configure_hotbar.button_size = button_size
            settings.save_settings()
        ImGui.show_tooltip("Size of each command button in pixels (10-256)")
            
        desired_rows = ImGui.input_int("Rows", rows)
        desired_cols = ImGui.input_int("Columns", cols)
        
        if desired_rows != rows or desired_cols != cols:
            new_commands = {}
            
            for r in range(desired_rows):
                new_commands[r] = {}
                for c in range(desired_cols):
                    if r in configure_hotbar.commands and c in configure_hotbar.commands[r]:
                        new_commands[r][c] = configure_hotbar.commands[r][c]
                    else:
                        new_commands[r][c] = "Empty"
                        
            configure_hotbar.commands = new_commands
            settings.save_settings()
                
        if not is_appearing and PyImGui.is_mouse_clicked(0) and not PyImGui.is_any_item_hovered() and not PyImGui.is_window_hovered():
            configure_hotbar = None
            PyImGui.close_current_popup()
            
        PyImGui.end_popup()

def draw_hotbars(accounts: list[AccountData], cached_data: CacheData):
    for _, hotbar in settings.CommandHotBars.items():
        if hotbar.visible:
            draw_hotbar(hotbar, accounts)
            
    
    draw_configure_hotbar()
    draw_command_select_popup()
    draw_consumables_window(cached_data)

dialog_open : bool = False
frame_coords : list[tuple[int, tuple[int, int, int, int]]] = []
dialog_coords : tuple[int, int, int, int] = (0, 0, 0, 0)
overlay = Overlay()

# Load user32.dll
user32 = ctypes.windll.user32

# Virtual-key code for left mouse button
VK_LBUTTON = 0x01

def is_left_pressed() -> bool:    
    return bool(user32.GetAsyncKeyState(VK_LBUTTON) & 0x8000)

_left_was_pressed = False

def is_left_mouse_clicked() -> bool:
    """
    Returns True exactly once per full click (press → release).
    False at all other times.
    """
    global _left_was_pressed
    
    # Is button physically down now?
    pressed = bool(user32.GetAsyncKeyState(VK_LBUTTON) & 0x8000)
    
    # Detect release event (was pressed, now not pressed)
    clicked = _left_was_pressed and not pressed

    # Update state for next call
    _left_was_pressed = pressed

    return clicked
    
def draw_dialog_overlay(accounts: list[AccountData], cached_data: CacheData, messages: list[tuple[int, SharedMessage]]):
    global frame_coords, dialog_open, dialog_coords
    if not settings.ShowDialogOverlay:
        return
    
    own_data = GLOBAL_CACHE.ShMem.GetAccountDataFromEmail(cached_data.account_email)
    if own_data is None or not own_data.PlayerIsPartyLeader:
        return
    
    if dialog_throttle.IsExpired():
        dialog_throttle.Reset()
        dialog_open = UIManager.IsNPCDialogVisible()        
        frame_coords = UIManager.GetDialogButtonFrames() if dialog_open else []
            
    if not frame_coords or not dialog_open:
        return
    
    pyimgui_io = PyImGui.get_io()
    mouse_pos = (pyimgui_io.mouse_pos_x, pyimgui_io.mouse_pos_y)
    
    if Console.is_window_active(): 
        sorted_frames = sorted(frame_coords, key=lambda x: (x[1][1], x[1][0]))  # Sort by Y, then X
               
        for i, (frame_id, frame) in enumerate(sorted_frames):                
            if ImGui.is_mouse_in_rect((frame[0], frame[1], frame[2] - frame[0], frame[3] - frame[1]), mouse_pos):                                
                if is_left_mouse_clicked() and pyimgui_io.key_ctrl:
                    accounts = [acc for acc in accounts if acc.AccountEmail != cached_data.account_email]
                    commands.send_dialog(accounts, i + 1)
                    return
                else:
                    ImGui.begin_tooltip()
                    ImGui.text_colored(f"Ctrl + Click to select on all accounts.", gray_color.color_tuple, 12)
                    ImGui.end_tooltip()

    pass

def draw_skip_cutscene_overlay():
    in_cutscene = GLOBAL_CACHE.Map.IsInCinematic()
    
    if in_cutscene:
        pyimgui_io = PyImGui.get_io()
        mouse = (pyimgui_io.mouse_pos_x, pyimgui_io.mouse_pos_y)
        skip_cutscene_hash = 140452905
        button_offsets = [6,1,0]
        skip_cutscene_id = UIManager.GetChildFrameID(skip_cutscene_hash, button_offsets)
        
        frame_exists = UIManager.FrameExists(skip_cutscene_id)
        if frame_exists:          
            frame = UIManager.GetFrameCoords(skip_cutscene_id)
            
            if ImGui.is_mouse_in_rect((frame[0], frame[1], frame[2] - frame[0], frame[3] - frame[1]), mouse):                            
                if is_left_mouse_clicked() and pyimgui_io.key_ctrl:
                    current_account = GLOBAL_CACHE.Player.GetAccountEmail()
                    
                    if current_account:                
                        for account in GLOBAL_CACHE.ShMem.GetAllAccountData():
                            if account.AccountEmail != current_account:
                                
                                GLOBAL_CACHE.ShMem.SendMessage(
                                    current_account,
                                    account.AccountEmail,
                                    SharedCommandType.SkipCutscene,
                                    (0, 0, 0, 0),
                        )
                    
                else:
                    ImGui.begin_tooltip()
                    ImGui.text_colored(f"Ctrl + Click to skip cutscene on all accounts.", gray_color.color_tuple, 12)
                    ImGui.end_tooltip()                          

def draw_party_overlay(accounts: list[AccountData], hero_windows : dict[str, WindowModule]):
    global party_member_frames
    
    main_account = GLOBAL_CACHE.ShMem.GetAccountDataFromEmail(GLOBAL_CACHE.Player.GetAccountEmail())
    if not main_account or not main_account.PlayerIsPartyLeader:
        return
    
    if party_throttle.IsExpired():
        party_throttle.Reset()
        # 3332025202,1,8,0,0,0,0,12,0
        party_members_hash = 3332025202 if GLOBAL_CACHE.Map.IsOutpost() else 3332025202
        offsets = [1,8,0,0,0,0] if GLOBAL_CACHE.Map.IsOutpost() else [0,0,0,0]
        
        party_member_frames = []    
        fid = UIManager.GetChildFrameID(party_members_hash, offsets)
        if fid == 0 or not UIManager.FrameExists(fid):
            return
                
        for i in range(1, MAX_CHILD_FRAMES):
            fid = UIManager.GetChildFrameID(party_members_hash, [1,8,0,0,0,0,i,0] if GLOBAL_CACHE.Map.IsOutpost() else [0,0,0,0,i,0])
            if fid == 0 or not UIManager.FrameExists(fid):
                continue
            
            party_member_frames.append(FramePosition(fid))
            
        ## sort frames by Y
        party_member_frames.sort(key=lambda x: (x.position.top_on_screen, x.position.left_on_screen))  # Sort by Y, then X
    
    style = ImGui.get_style()
    texture = ThemeTextures.Hero_Panel_Toggle_Base.value.get_texture()
    
    if not party_member_frames:
        return
    
    for i, frame_info in enumerate(party_member_frames, start=1):      
        account = next((acc for acc in accounts if acc.PartyPosition == i - 1), None)
        
        if account and account.AccountEmail != GLOBAL_CACHE.Player.GetAccountEmail():
            if account.PartyID != main_account.PartyID or not SameMapAsAccount(account):
                continue
            
            window_info = settings.HeroPanelPositions.get(account.AccountEmail, None)
            
            if window_info:        
                is_minimalus = style.Theme is StyleTheme.Minimalus  
                button_size = frame_info.position.bottom_on_screen - frame_info.position.top_on_screen + (0 if is_minimalus else -4)   
                button_rect = (
                    frame_info.position.right_on_screen - button_size + (0 if is_minimalus else 0), 
                    frame_info.position.bottom_on_screen - button_size + (-1 if is_minimalus else -2),
                    frame_info.position.right_on_screen,
                    frame_info.position.bottom_on_screen + (-3 if is_minimalus else 0)
                    )
                                            
                PyImGui.set_next_window_pos((frame_info.position.left_on_screen - 10, frame_info.position.top_on_screen - 10), PyImGui.ImGuiCond.Always)
                PyImGui.set_next_window_size((frame_info.position.right_on_screen - frame_info.position.left_on_screen + 20 , frame_info.position.bottom_on_screen - frame_info.position.top_on_screen +20), PyImGui.ImGuiCond.Always)
                flags = PyImGui.WindowFlags.NoTitleBar | PyImGui.WindowFlags.NoResize | PyImGui.WindowFlags.NoMove | PyImGui.WindowFlags.NoScrollbar | PyImGui.WindowFlags.NoSavedSettings | PyImGui.WindowFlags.NoFocusOnAppearing | PyImGui.WindowFlags.NoBackground
                
                if not ImGui.is_mouse_in_rect((*button_rect[:2], button_size, button_size)):
                    flags |= PyImGui.WindowFlags.NoMouseInputs
                    
                PyImGui.begin(f"##HeroAIPartyOverlay{i}", False, flags )
                
                draw_panel_toggle(i, account, button_rect, style, texture, window_info, is_minimalus, button_size)
                
                PyImGui.end()
                                    
            
    pass

def draw_panel_toggle(i, account : AccountData, button_rect : tuple[float, float, float, float], style : Style, texture : GameTexture, window_info : Settings.HeroPanelInfo | None, is_minimalus : bool, button_size : float, show_tooltip: bool = True):
    if not window_info:
        return
    
    bg_rect = (
                button_rect[0] + (2 if is_minimalus else 0),
                button_rect[1] + (2 if is_minimalus else 0),
                button_rect[2],
                button_rect[3] + (2 if is_minimalus else 0)
                )
                
    if is_minimalus:
        PyImGui.draw_list_add_rect_filled(
                        *bg_rect,
                        Color(0, 0, 0, 255).color_int,
                        style.FrameRounding.value1,
                        0
                        )
                
    hovered = ImGui.is_mouse_in_rect((*button_rect[:2], button_size, button_size))
    texture.draw_in_drawlist(
                    button_rect[:2],
                    (button_size, button_size),
                    state=TextureState.Active if window_info.open else TextureState.Normal,
                    tint=(255, 255, 255, 255) if hovered else (200, 200, 200, 255)
                    )
                
    text = str(i)
    text_size = PyImGui.calc_text_size(text)
                ## center align horizontally and vertically
    text_pos = (
                    button_rect[0] - 2 + (button_size - text_size[0]) / 2 + 2,
                    button_rect[1] + (button_size - text_size[1]) / 2 + 2
                    )
                
    PyImGui.draw_list_add_text(
                    text_pos[0],
                    text_pos[1],
                    style.Text.color_int,
                    text
                    )

    if hovered:
        if show_tooltip:
            ImGui.begin_tooltip()
            name = get_display_name(account)
            ImGui.text(f"{name}", 13)
            ImGui.text_colored(f"{account.AccountEmail if name == account.CharacterName else f'{name.lower().replace(' ', '')}@mail.com'}", gray_color.color_tuple, 12)
            
            PyImGui.separator()
            ImGui.text_colored(f"Click to {"Hide" if window_info.open else "Show"} the hero panel", gray_color.color_tuple, 11)
            ImGui.end_tooltip()
        
        if PyImGui.is_mouse_clicked(0):  
            window_info.open = not window_info.open
            settings.save_settings()

show_accounts_in_party_search : bool = False
last_active_tab : int = -1
selected_account : str = ""

party_search : Optional[FramePosition] = None
player_tab : Optional[FramePosition] = None
hero_tab : Optional[FramePosition] = None
henchmen_tab : Optional[FramePosition] = None
active_tab : Optional[FramePosition] = None
active_tab_id : int = -1
is_player_tab : bool = True

def draw_tab_control(rect : tuple[float, float, float, float], label: str = "Accounts##PartySearchTab"):
    global show_accounts_in_party_search
    
    PyImGui.push_clip_rect(
        *rect,
        False
    )
    
    style = ImGui.get_style()
    #NON THEMED
    if style.Theme not in ImGui.Textured_Themes:
        ## Draw button/tab item frame and text
        
        pass
        
        
    #THEMED
        
    
    (ThemeTextures.Tab_Active if show_accounts_in_party_search else ThemeTextures.Tab_Inactive).value.get_texture().draw_in_drawlist(
        rect[:2],
        rect[2:],
    )

    display_label = ImGui.trim_text_to_width(label.split("##")[0], rect[2] - 2)        
    final_size = PyImGui.calc_text_size(display_label)
    final_w, final_h = final_size

    text_x = rect[0] + (rect[2] - final_w) / 2
    text_y = rect[1] + (rect[3] - final_h + (5 if show_accounts_in_party_search else 7)) / 2
    text_rect = (text_x, text_y, rect[2], rect[3])

    PyImGui.push_clip_rect(
        *text_rect,
        True
    )

    PyImGui.draw_list_add_text(
        text_x,
        text_y,
        style.Text.color_int,
        display_label,
    )

    PyImGui.pop_clip_rect()  
    
    if ImGui.is_mouse_in_rect(rect):
        if PyImGui.is_mouse_clicked(0):
            show_accounts_in_party_search = not show_accounts_in_party_search
            
    
    PyImGui.pop_clip_rect()
    return show_accounts_in_party_search

def draw_party_search_overlay(accounts: list[AccountData], cached_data: CacheData):
    global show_accounts_in_party_search, last_active_tab, selected_account
    global party_search, player_tab, hero_tab, henchmen_tab, active_tab, is_player_tab
    
    if party_search_throttle.IsExpired():
        party_search_throttle.Reset()
            
        party_search_id = UIManager.GetChildFrameID(3199024334, [14])
        if party_search_id == 0 or not UIManager.FrameExists(party_search_id):
            party_search = None
            party_search_throttle.SetThrottleTime(500)
            return
        
        party_search = FramePosition(party_search_id)
        
        players_tab_id = UIManager.GetChildFrameID(3199024334, [14, 4294967295])    
        player_tab = FramePosition(players_tab_id)
            
        heroes_tab_id = UIManager.GetChildFrameID(3199024334, [14, 4294967294])
        hero_tab = FramePosition(heroes_tab_id)
        
        henchmen_tab_id = UIManager.GetChildFrameID(3199024334, [14, 4294967293])
        henchmen_tab = FramePosition(henchmen_tab_id)
            
        active_tab = next((tab for tab in [player_tab, hero_tab, henchmen_tab] if tab.position.content_top == max(
            player_tab.position.content_top,
            hero_tab.position.content_top,
            henchmen_tab.position.content_top
        )), player_tab)
        
        is_player_tab = (active_tab == player_tab)
               
    
    if not party_search or not player_tab or not hero_tab or not henchmen_tab or not active_tab:
        return
    
    party_search_throttle.SetThrottleTime(0)
    style = ImGui.get_style()
    style.WindowPadding.push_style_var(20, 20)
    style.HeaderHovered.push_color((200, 200, 200, 30))
    style.HeaderActive.push_color((200, 200, 200, 100))
    style.Header.push_color((200, 200, 200, 100))
    
    PyImGui.set_next_window_pos((party_search.position.left_on_screen, active_tab.position.bottom_on_screen + (8 if is_player_tab else 10)), PyImGui.ImGuiCond.Always)
    PyImGui.set_next_window_size((party_search.position.width_on_screen + 3, party_search.position.height_on_screen - (38 if is_player_tab else 40)), PyImGui.ImGuiCond.Always)
    flags = PyImGui.WindowFlags.NoTitleBar | PyImGui.WindowFlags.NoResize | PyImGui.WindowFlags.NoMove | PyImGui.WindowFlags.NoScrollbar | PyImGui.WindowFlags.NoSavedSettings | PyImGui.WindowFlags.NoFocusOnAppearing | PyImGui.WindowFlags.NoBackground
    
    if not show_accounts_in_party_search:
        flags |= PyImGui.WindowFlags.NoMouseInputs 
        
    open = PyImGui.begin("##PartySearchOverlay", show_accounts_in_party_search, flags)
    style.WindowPadding.pop_style_var()
    
    ImGui.push_font("Regular", 14)
    text_size = ImGui.calc_text_size("Accounts")
    
    tab_rect = (
        henchmen_tab.position.right_on_screen,
        henchmen_tab.position.top_on_screen + 2,
        text_size[0] + 25,
        (active_tab.position.height_on_screen) + (0 if show_accounts_in_party_search else -2)
    )
    
    if active_tab:
        if last_active_tab != active_tab.frame_id:
            show_accounts_in_party_search = False
            
        elif not ImGui.is_mouse_in_rect(tab_rect):
            if PyImGui.is_mouse_clicked(0):
                for tab in [player_tab, hero_tab, henchmen_tab]:
                    if tab and ImGui.is_mouse_in_rect((
                        tab.position.left_on_screen,
                        tab.position.top_on_screen,
                        tab.position.width_on_screen,
                        tab.position.height_on_screen
                    )):
                        active_tab_id = tab
                        show_accounts_in_party_search = False
                        break
            
        last_active_tab = active_tab.frame_id
    
    tab_open = draw_tab_control(tab_rect)
    
    
    ImGui.pop_font()
    
    if tab_open:
        PyImGui.draw_list_add_rect_filled(
            party_search.position.left_on_screen,
            party_search.position.top_on_screen,
            party_search.position.right_on_screen,
            party_search.position.bottom_on_screen,
            Color(0, 0, 0, 255).color_int,
            style.FrameRounding.value1,
            0,
        )
        
        sorted_by_profession = sorted(accounts, key=lambda acc: (acc.PlayerProfession[0], get_display_name(acc)), reverse=False)
        button_size  = 20
        texture = ThemeTextures.Hero_Panel_Toggle_Base.value.get_texture()
        mapid = GLOBAL_CACHE.Map.GetMapID()
        
        for i, account in enumerate(sorted_by_profession):
            window_info = settings.HeroPanelPositions.get(account.AccountEmail, None)
            
            if not window_info:
                continue
            
            name = get_display_name(account)
            prof_primary = ProfessionShort(
                account.PlayerProfession[0]).name if account.PlayerProfession[0] != 0 else ""
            prof_secondary = ProfessionShort(
                account.PlayerProfession[1]).name if account.PlayerProfession[1] != 0 else ""
            display_text = f"{prof_primary}{("/" if prof_secondary else "")}{prof_secondary}{account.PlayerLevel} {name} {f"[{GLOBAL_CACHE.Map.GetMapName(account.MapID)}]" if account.MapID != 0 and account.MapID != mapid else ''}"
            
            ImGui.dummy(button_size, button_size)
            draw_panel_toggle(
                i,
                account,
                (
                    PyImGui.get_item_rect_min()[0] - 2,
                    PyImGui.get_item_rect_min()[1] - 2,
                    PyImGui.get_item_rect_min()[0] + button_size,
                    PyImGui.get_item_rect_min()[1] + button_size
                ),
                style,
                texture,
                window_info,
                style.Theme is StyleTheme.Minimalus,
                button_size,
                # account.AccountEmail != cached_data.account_email
            )
            
            PyImGui.same_line(0, 5)            
            is_party_member = GLOBAL_CACHE.Party.IsPartyMember(account.PlayerID)
            selected = selected_account == account.AccountEmail
            
            if is_party_member:
                style.Text.push_color((200, 200, 200, 180))
            elif selected:
                style.Text.push_color((255, 238, 187, 255))
                
            
            _ = ImGui.selectable(f"{display_text}##PartySearchAccount_{account.AccountEmail}", selected_account == account.AccountEmail)
                        
            if is_party_member or selected:
                style.Text.pop_color()
            
            if account.AccountEmail != cached_data.account_email:
                ImGui.show_tooltip(f"Double Click to {'Kick from' if is_party_member else 'Invite to'} party\nSingle Click to select account for travel/invite")
                
            if PyImGui.is_item_clicked(0):
                if PyImGui.is_mouse_double_clicked(0):
                    sender_email = cached_data.account_email or ""
                        
                    if account.AccountEmail == sender_email:
                        continue
                    
                    same_map = GLOBAL_CACHE.Map.GetMapID() == account.MapID and GLOBAL_CACHE.Map.GetRegion()[0] == account.MapRegion and GLOBAL_CACHE.Map.GetDistrict() == account.MapDistrict and GLOBAL_CACHE.Map.GetLanguage()[0] == account.MapLanguage
                    
                    if same_map:
                        if not is_party_member:
                            Player.SendChatCommand("invite " + account.CharacterName)
                            GLOBAL_CACHE.ShMem.SendMessage(
                                sender_email,
                                account.AccountEmail,
                                SharedCommandType.InviteToParty,
                                (GLOBAL_CACHE.Player.GetAgentID(), 0, 0, 0)
                            )
                            
                        else:
                            Player.SendChatCommand("kick " +  account.CharacterName)
                            
                    
                    else:
                        GLOBAL_CACHE.ShMem.SendMessage(
                            sender_email,
                            account.AccountEmail,
                            SharedCommandType.TravelToMap,
                            (
                                GLOBAL_CACHE.Map.GetMapID(),
                                GLOBAL_CACHE.Map.GetRegion()[0],
                                GLOBAL_CACHE.Map.GetDistrict(),
                                GLOBAL_CACHE.Map.GetLanguage()[0],
                            )
                        ) 
                    
                else:
                    selected_account = account.AccountEmail
        pass
    
    PyImGui.end()
    
    style.Header.pop_color()
    style.HeaderActive.pop_color()
    style.HeaderHovered.pop_color()
    
    pass

def draw_configure_window(module_name : str, configure_window : WindowModule):
    
    global module_info
    
    if not module_info:
        module_info = widget_handler.get_widget_info(module_name)
        
    configure_window.open = module_info.configuring if module_info else False
    
    if configure_window.begin():
        if ImGui.begin_tab_bar("##HeroAIConfigTabs"):
            if ImGui.begin_tab_item("General"):
                if ImGui.begin_child("##GeneralSettingsChild", (0, 0)):
                    show_party_panel_ui = ImGui.checkbox("Show Party Panel UI", settings.ShowPartyPanelUI)
                    if show_party_panel_ui != settings.ShowPartyPanelUI:
                        settings.ShowPartyPanelUI = show_party_panel_ui
                        settings.save_settings()
                        
                    show_floating_targets = ImGui.checkbox("Show Floating Target Buttons", settings.ShowFloatingTargets)
                    if show_floating_targets != settings.ShowFloatingTargets:
                        settings.ShowFloatingTargets = show_floating_targets
                        settings.save_settings()

                    disable_automation = ImGui.checkbox("Disable Leader Automation", settings.DisableAutomationOnLeaderAccount)
                    if disable_automation != settings.DisableAutomationOnLeaderAccount:
                        settings.DisableAutomationOnLeaderAccount = disable_automation
                        settings.save_settings()

                    show_command_panel = ImGui.checkbox("Show Global Config Panel", settings.ShowCommandPanel)
                    if show_command_panel != settings.ShowCommandPanel:
                        settings.ShowCommandPanel = show_command_panel
                        settings.save_settings()
                        
                    show_dialog_overlay = ImGui.checkbox("Show Dialog Overlay", settings.ShowDialogOverlay)
                    if show_dialog_overlay != settings.ShowDialogOverlay:
                        settings.ShowDialogOverlay = show_dialog_overlay
                        settings.save_settings()
                    ImGui.show_tooltip("Overlay buttons on NPC dialog with an invisible button for quick selection on all accounts by holding CTRL.\nOnly available to the party leader.\n\nThis is quite expensive due to UI queries, so only enable if needed.")
                        
                    confirm_follow_point = ImGui.checkbox("Confirm Follow Point", settings.ConfirmFollowPoint)
                    if confirm_follow_point != settings.ConfirmFollowPoint:
                        settings.ConfirmFollowPoint = confirm_follow_point
                        settings.save_settings()
                    ImGui.show_tooltip("Reevalutes the follow point when following is enabled. This is beeing tested right now and can impact the performance a lot.")
                        
                ImGui.end_child()
                ImGui.end_tab_item()
                
            if ImGui.begin_tab_item("Hero Panels"):      
                if ImGui.begin_child("##HeroPanelSettingsChild", (0, 0)):   
                    show_hero_panels = ImGui.checkbox("Show Hero Panels", settings.ShowHeroPanels)
                    if show_hero_panels != settings.ShowHeroPanels:
                        settings.ShowHeroPanels = show_hero_panels
                        settings.save_settings()
                                       
                    show_party_overlay = ImGui.checkbox("Show Party Overlay", settings.ShowPartyOverlay)
                    if show_party_overlay != settings.ShowPartyOverlay:
                        settings.ShowPartyOverlay = show_party_overlay
                        settings.save_settings()
                                       
                    show_party_search_overlay = ImGui.checkbox("Show Party Search Overlay", settings.ShowPartySearchOverlay)
                    if show_party_search_overlay != settings.ShowPartySearchOverlay:
                        settings.ShowPartySearchOverlay = show_party_search_overlay
                        settings.save_settings()
                                       
                    show_on_leader = ImGui.checkbox("Show only on Leader", settings.ShowPanelOnlyOnLeaderAccount)
                    if show_on_leader != settings.ShowPanelOnlyOnLeaderAccount:
                        settings.ShowPanelOnlyOnLeaderAccount = show_on_leader
                        settings.save_settings()
                    
                    show_leader_panel = ImGui.checkbox("Show Leader's Panel", settings.ShowLeaderPanel)
                    if show_leader_panel != settings.ShowLeaderPanel:
                        settings.ShowLeaderPanel = show_leader_panel
                        settings.save_settings()
                    
                    combine_panels = ImGui.checkbox("Combine Hero Panels", settings.CombinePanels)
                    if combine_panels != settings.CombinePanels:
                        settings.CombinePanels = combine_panels
                        settings.save_settings()
                        
                    anonymous_panel_names = ImGui.checkbox("Anonymous Panel Names", settings.Anonymous_PanelNames)
                    if anonymous_panel_names != settings.Anonymous_PanelNames:
                        settings.Anonymous_PanelNames = anonymous_panel_names
                        settings.save_settings()
                        
                    show_hero_buttons = ImGui.checkbox("Show Hero Buttons", settings.ShowHeroButtons)
                    if show_hero_buttons != settings.ShowHeroButtons:
                        settings.ShowHeroButtons = show_hero_buttons
                        settings.save_settings()
                        
                    show_hero_bars = ImGui.checkbox("Show Health and Energy", settings.ShowHeroBars)
                    if show_hero_bars != settings.ShowHeroBars:
                        settings.ShowHeroBars = show_hero_bars
                        settings.save_settings()
                            
                    show_hero_skills = ImGui.checkbox("Show Hero Skills", settings.ShowHeroSkills)
                    if show_hero_skills != settings.ShowHeroSkills:
                        settings.ShowHeroSkills = show_hero_skills
                        settings.save_settings()
                        
                    show_hero_upkeeps = ImGui.checkbox("Show Hero Upkeeps", settings.ShowHeroUpkeeps)
                    if show_hero_upkeeps != settings.ShowHeroUpkeeps:
                        settings.ShowHeroUpkeeps = show_hero_upkeeps
                        settings.save_settings()
                        
                    show_hero_effects = ImGui.checkbox("Show Hero Effects", settings.ShowHeroEffects)
                    if show_hero_effects != settings.ShowHeroEffects:
                        settings.ShowHeroEffects = show_hero_effects
                        settings.save_settings()
                        
                    max_effect_rows = ImGui.slider_int("Max Effect Rows", settings.MaxEffectRows, 1, 10)
                    if max_effect_rows != settings.MaxEffectRows and max_effect_rows >= 1 and max_effect_rows <= 10:
                        settings.MaxEffectRows = max_effect_rows
                        settings.save_settings()
                        
                    radio_value = 0 if not settings.ShowEffectDurations and not settings.ShowShortEffectDurations else (1 if settings.ShowShortEffectDurations else 2)

                    radio_value = ImGui.radio_button("Show no durations", radio_value, 0)
                    radio_value = ImGui.radio_button("Show short durations", radio_value, 1)
                    radio_value = ImGui.radio_button("Show all durations", radio_value, 2)

                    if radio_value == 0:
                        if settings.ShowEffectDurations or settings.ShowShortEffectDurations:
                            settings.ShowEffectDurations = False
                            settings.ShowShortEffectDurations = False
                            settings.save_settings()

                    elif radio_value == 1:
                        if settings.ShowEffectDurations or not settings.ShowShortEffectDurations:
                            settings.ShowEffectDurations = False
                            settings.ShowShortEffectDurations = True
                            settings.save_settings()

                    elif radio_value == 2:
                        if not settings.ShowEffectDurations or settings.ShowShortEffectDurations:
                            settings.ShowEffectDurations = True
                            settings.ShowShortEffectDurations = False
                            settings.save_settings()
            
                ImGui.end_child()
                ImGui.end_tab_item()                
                    
            if ImGui.begin_tab_item("Hotbars"):
                if ImGui.begin_child("##HotbarSettingsChild", (0, 0)):
                    x_avail, y_avail = PyImGui.get_content_region_avail()
                    
                    if ImGui.button("Add Hotbar", x_avail - 4):
                        identifier = f"Hotbar_{len(settings.CommandHotBars) + 1}"
                        settings.CommandHotBars[identifier] = Settings.CommandHotBar(identifier)
                        settings.save_settings()
                    
                    if ImGui.begin_child("##HotbarListChild", (0, 0), True):
                        for key, hotbar in settings.CommandHotBars.items():
                            if ImGui.collapsing_header(f"{hotbar.name}"):
                                if ImGui.begin_child(f"##HotbarConfigChild_{key}", (0, 0), True):
                                    x_avail, y_avail = PyImGui.get_content_region_avail()
                    
                                    name = ImGui.input_text(f"##hotbar name{key}", hotbar.name)
                                    if name != hotbar.name:
                                        if PyImGui.is_key_down(Key.Enter.value):
                                            hotbar.name = name
                                            settings.save_settings()
                                    ImGui.show_tooltip("Name of the hotbar. Press Enter to confirm changes.")

                                        
                                    PyImGui.same_line(x_avail - 24 - 32, 0)

                                    visible = ImGui.toggle_icon_button(f"{(IconsFontAwesome5.ICON_EYE if hotbar.visible else IconsFontAwesome5.ICON_EYE_SLASH)}##{key}", hotbar.visible, 32, 20)
                                    if visible != hotbar.visible:
                                        hotbar.visible = visible
                                        settings.save_settings()                    
                                    ImGui.show_tooltip(f"{'Hide' if hotbar.visible else 'Show'} Hotbar '{key}'")
                                    
                                    PyImGui.same_line(x_avail - 20, 0)
                                    
                                    if ImGui.icon_button(f"{IconsFontAwesome5.ICON_TRASH}##{key}", 32, 20):
                                        settings.delete_hotbar(key)
                                        break
                                    ImGui.show_tooltip(f"Delete Hotbar '{key}'")
                                    
                                    positioning = ImGui.combo(f"Docked##positioning {key}", hotbar.docked.value, [Utils.humanize_string(pos.name) for pos in Docked])
                                    if positioning != hotbar.docked.value:
                                        hotbar.docked = Docked(positioning)
                                        settings.save_settings()
                                    ImGui.show_tooltip("Positioning preset for the hotbar. Custom allows free movement.")
                                    
                                    alignment_names = [f"{Utils.humanize_string(pos.name)}" for pos in Alignment]
                                    current_alignment = f"{Utils.humanize_string(hotbar.alignment.name)}"
                                    current_alignment_index = alignment_names.index(current_alignment) if current_alignment in alignment_names else 0
                                    
                                    alignment = ImGui.combo(f"Alignment##positioning {key}", current_alignment_index, alignment_names)
                                    if alignment != current_alignment_index:
                                        hotbar.alignment = Alignment[list(Alignment)[alignment].name]
                                        settings.save_settings()
                                        
                                    ImGui.show_tooltip("Positioning preset for the hotbar. Custom allows free movement.")
                                    
                                    btn_size = ImGui.input_int(f"Button Size##{key}", hotbar.button_size)
                                    if btn_size != hotbar.button_size and btn_size >= 10 and btn_size <= 256:
                                        hotbar.button_size = btn_size
                                        settings.save_settings()
                                        
                                    rows = ImGui.input_int(f"Rows##{key}", len(hotbar.commands))
                                    if rows != len(hotbar.commands):
                                        new_commands = {}
                                        
                                        for r in range(rows):
                                            new_commands[r] = {}
                                            for c in range(max(1, max(len(row) for _, row in hotbar.commands.items()) if len(hotbar.commands) > 0 else 0)):
                                                if r in hotbar.commands and c in hotbar.commands[r]:
                                                    new_commands[r][c] = hotbar.commands[r][c]
                                                else:
                                                    new_commands[r][c] = "Empty"
                                                    
                                        hotbar.commands = new_commands
                                        settings.save_settings()
                                        
                                    cols = ImGui.input_int(f"Columns##{key}", max(1, max(len(row) for _, row in hotbar.commands.items()) if len(hotbar.commands) > 0 else 0))
                                    if cols != max(1, max(len(row) for _, row in hotbar.commands.items()) if len(hotbar.commands) > 0 else 0):
                                        new_commands = {}
                                        
                                        for r in range(len(hotbar.commands)):
                                            new_commands[r] = {}
                                            for c in range(cols):
                                                if r in hotbar.commands and c in hotbar.commands[r]:
                                                    new_commands[r][c] = hotbar.commands[r][c]
                                                else:
                                                    new_commands[r][c] = "Empty"
                                                    
                                        hotbar.commands = new_commands
                                        settings.save_settings()
                                
                    ImGui.end_child()
                        
                ImGui.end_child()
                ImGui.end_tab_item()
                
            ImGui.end_tab_bar()
            
                
                            
    
    configure_window.end()  
    
    if not configure_window.open:
        WidgetHandler().set_widget_configuring(module_name, False)
          
    pass
