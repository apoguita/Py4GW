import os
import random
import math
from typing import Optional

import PyImGui

from HeroAI.cache_data import CacheData, INI_DIR
from HeroAI.utils import IsHeroFlagged
from HeroAI.constants import NUMBER_OF_SKILLS
from HeroAI.commands import HeroAICommands
from Py4GWCoreLib import Py4GW
from Py4GWCoreLib import Agent, Color, GLOBAL_CACHE, ConsoleLog, ManagedWindowSpec, Player, SharedCommandType, Utils, WindowFactory, WindowVarSpec
from Py4GWCoreLib.Map import Map
from Py4GWCoreLib.ImGui import ImGui
from Py4GWCoreLib.ImGui_src.IconsFontAwesome5 import IconsFontAwesome5
from Py4GWCoreLib.ImGui_src.Textures import TextureState, ThemeTexture, ThemeTextures
from Py4GWCoreLib.ImGui_src.types import ImGuiStyleVar, StyleTheme
from Py4GWCoreLib.IniManager import IniManager
from Py4GWCoreLib.enums import ImguiFonts
from Py4GWCoreLib.enums_src.GameData_enums import Allegiance, Profession, ProfessionShort
from Py4GWCoreLib.py4gwcorelib_src.Timer import Timer
from dataclasses import dataclass

PANEL_BASE_WIDTH = 200
PANEL_BASE_HEIGHT = 90
PANEL_MIN_SCALE = 0.65
PANEL_MAX_SCALE = 4.0
RICH_PANEL_WIDTH = 319
RICH_BAR_HEIGHT = 28

MODULE_NAME = "HeroAI"
MODULE_ICON = "Textures/Module_Icons/HeroAI.png"

@dataclass
class HeroAIFloatingIcon:
    MODULE_NAME: str = MODULE_NAME
    INI_PATH: str = f"{INI_DIR}/"
    MAIN_INI_FILENAME: str = "heroai_ui_window.ini"
    FLOATING_INI_FILENAME: str = "heroai_ui_floating.ini"
    CONFIG_INI_FILENAME: str = "heroai_ui_config_window.ini"

    MAIN_INI_KEY: str = ""
    FLOATING_INI_KEY: str = ""
    CONFIG_INI_KEY: str = ""
    INI_INIT: bool = False
    ICON_PATH: str = os.path.join(Py4GW.Console.get_projects_path(), "Textures", "Module_Icons", "HeroAI.png")


window_factory = WindowFactory(HeroAIFloatingIcon.INI_PATH)
window_factory.register_window(
    ManagedWindowSpec(
        identifier="main",
        filename=HeroAIFloatingIcon.MAIN_INI_FILENAME,
        title=HeroAIFloatingIcon.MODULE_NAME,
        flags=PyImGui.WindowFlags.AlwaysAutoResize,
    )
)
window_factory.register_window(
    ManagedWindowSpec(
        identifier="floating",
        filename=HeroAIFloatingIcon.FLOATING_INI_FILENAME,
        title="HeroAI Floating",
        open_var_name="show_main_window",
        open_default=True,
    )
)
window_factory.register_window(
    ManagedWindowSpec(
        identifier="appearance",
        filename=HeroAIFloatingIcon.CONFIG_INI_FILENAME,
        title="HeroAI Appearance Settings",
        flags=PyImGui.WindowFlags.AlwaysAutoResize,
        open_var_name="show_appearance_window",
        open_default=False,
        vars=[
            WindowVarSpec("float", "panel_table_scale", "Appearance", "panel_table_scale", 1.0),
            WindowVarSpec("bool", "show_main_skill_toggles", "Appearance", "show_main_skill_toggles", True),
            WindowVarSpec("bool", "show_players", "Appearance", "show_players", True),
            WindowVarSpec("bool", "show_player_skill_toggles", "Appearance", "show_player_skill_toggles", True),
            WindowVarSpec("bool", "use_rich_player_panels", "Appearance", "use_rich_player_panels", False),
            WindowVarSpec("bool", "show_players_in_individual_windows", "Appearance", "show_players_in_individual_windows", False),
            WindowVarSpec("bool", "obfuscate_player_names", "Appearance", "obfuscate_player_names", False),
        ],
    )
)
window_factory.register_window(
    ManagedWindowSpec(
        identifier="players",
        filename="heroai_ui_players_window.ini",
        title="HeroAI Players",
        flags=PyImGui.WindowFlags.AlwaysAutoResize,
        open_var_name="show_player_window",
        open_default=True,
    )
)


def get_panel_dimensions(scale: float) -> tuple[int, int]:
    return int(round(PANEL_BASE_WIDTH * scale)), int(round(PANEL_BASE_HEIGHT * scale))


class CachedSkillInfo:
    def __init__(self, skill_id: int):
        self.skill_id = skill_id
        self.name = GLOBAL_CACHE.Skill.GetNameFromWiki(skill_id) or GLOBAL_CACHE.Skill.GetName(skill_id) or str(skill_id)
        self.description = GLOBAL_CACHE.Skill.GetDescription(skill_id) or ""
        self.texture_path = GLOBAL_CACHE.Skill.ExtraData.GetTexturePath(skill_id)

        if not self.texture_path or not os.path.exists(self.texture_path):
            self.texture_path = ThemeTexture.PlaceHolderTexture.texture if skill_id != 0 else ""

        self.is_elite = GLOBAL_CACHE.Skill.Flags.IsElite(skill_id)
        self.is_hex = GLOBAL_CACHE.Skill.Flags.IsHex(skill_id)
        self.is_title = GLOBAL_CACHE.Skill.Flags.IsTitle(skill_id)
        self.is_enchantment = GLOBAL_CACHE.Skill.Flags.IsEnchantment(skill_id)
        self.is_shout = GLOBAL_CACHE.Skill.Flags.IsShout(skill_id)
        self.is_skill = GLOBAL_CACHE.Skill.Flags.IsSkill(skill_id)
        self.is_condition = GLOBAL_CACHE.Skill.Flags.IsCondition(skill_id)
        self.adrenaline_cost = GLOBAL_CACHE.Skill.Data.GetAdrenaline(skill_id)
        self.recharge_time = GLOBAL_CACHE.Skill.Data.GetRecharge(skill_id)
        self.frame_texture, self.texture_state, self.progress_color = get_frame_texture_for_effect(skill_id)


class HealthState:
    Normal = Color(204, 0, 0, 255)
    Poisoned = Color(116, 116, 48, 255)
    Bleeding = Color(224, 119, 119, 255)
    DegenHexed = Color(196, 56, 150, 255)
    Disconnected = Color(54, 54, 54, 255)


def get_frame_texture_for_effect(skill_id: int):
    is_elite = GLOBAL_CACHE.Skill.Flags.IsElite(skill_id)
    texture_state = TextureState.Normal if not is_elite else TextureState.Active
    theme = ImGui.get_style().Theme if ImGui.get_style().Theme in ImGui.Textured_Themes else StyleTheme.Guild_Wars

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


class HeroAI_PlayerPanelRenderer:
    title_names: dict[str, str] = {}

    def __init__(self, appearance_window: "HeroAI_AppearanceWindow") -> None:
        self.appearance_window = appearance_window
        self.rich_renderer = HeroAI_RichPlayerPanelRenderer(appearance_window)

    def get_display_name(self, account) -> str:
        name = account.AgentData.CharacterName
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
            "the Legendary",
        ]

        if name not in self.title_names:
            self.title_names[name] = "Robin " + random.choice(titles)

        return self.title_names[name] if self.appearance_window.get_obfuscate_player_names() else name

    def get_window_title(self, account) -> str:
        display_name = self.get_display_name(account)
        primary_prof = ProfessionShort(account.AgentData.Profession[0]).name if account.AgentData.Profession[0] != 0 else ""
        secondary_prof = ProfessionShort(account.AgentData.Profession[1]).name if account.AgentData.Profession[1] != 0 else ""
        return f"{primary_prof}{('/' if secondary_prof else '')}{secondary_prof}{account.AgentData.Level} {display_name}"

    def draw_simple_panel(self, identifier: str, game_option) -> None:
        if game_option is None:
            return

        style = ImGui.get_style()
        table_width, _ = get_panel_dimensions(self.appearance_window.get_panel_scale())
        btn_size = (table_width / 5) - 4
        skill_size = (table_width / NUMBER_OF_SKILLS) - 8

        style.ItemSpacing.push_style_var(0, 0)
        style.CellPadding.push_style_var(2, 2)

        if PyImGui.begin_table(f"FollowerGameOptionTable##{identifier}", 3, 0, 0, btn_size + 2):
            PyImGui.table_next_row()
            PyImGui.table_next_column()
            following = ImGui.toggle_button(IconsFontAwesome5.ICON_RUNNING + f"##Following{identifier}", game_option.Following, btn_size * 1.45, btn_size)
            if following != game_option.Following:
                game_option.Following = following
            ImGui.show_tooltip("Follow / Avoidance")

            PyImGui.table_next_column()
            looting = ImGui.toggle_button(IconsFontAwesome5.ICON_COINS + f"##Looting{identifier}", game_option.Looting, btn_size * 1.45, btn_size)
            if looting != game_option.Looting:
                game_option.Looting = looting
            ImGui.show_tooltip("Looting")

            PyImGui.table_next_column()
            combat = ImGui.toggle_button(IconsFontAwesome5.ICON_SKULL_CROSSBONES + f"##Combat{identifier}", game_option.Combat, btn_size * 1.45, btn_size)
            if combat != game_option.Combat:
                game_option.Combat = combat
            ImGui.show_tooltip("Combat")
            PyImGui.end_table()

        if self.appearance_window.get_show_player_skill_toggles():
            style.ButtonPadding.push_style_var(5 if style.Theme not in ImGui.Textured_Themes else 0, 3 if style.Theme not in ImGui.Textured_Themes else 2)
            if PyImGui.begin_table(f"FollowerSkillsTable##{identifier}", NUMBER_OF_SKILLS, 0, 0, (btn_size / 3)):
                PyImGui.table_next_row()
                for i in range(NUMBER_OF_SKILLS):
                    PyImGui.table_next_column()
                    skill_active = ImGui.toggle_button(f"{i + 1}##Skill{i}{identifier}", game_option.Skills[i], skill_size, skill_size)
                    if skill_active != game_option.Skills[i]:
                        game_option.Skills[i] = skill_active
                    ImGui.show_tooltip(f"Skill {i + 1}")
                PyImGui.end_table()
            style.ButtonPadding.pop_style_var()

        style.ItemSpacing.pop_style_var()
        style.CellPadding.pop_style_var()

    def draw_rich_panel(self, account, cached_data: CacheData, messages: list) -> None:
        self.rich_renderer.draw_panel(account, cached_data, messages)


class HeroAI_RichPlayerPanelRenderer:
    skill_cache: dict[int, CachedSkillInfo] = {}
    message_cache: dict[str, dict[SharedCommandType, dict[int, tuple]]] = {}
    template_popup_open: bool = False
    template_account: str = ""
    template_code: str = ""
    casting_animation_timer = Timer()
    commands = HeroAICommands()

    def __init__(self, appearance_window: "HeroAI_AppearanceWindow") -> None:
        self.appearance_window = appearance_window
        if not self.casting_animation_timer.IsRunning():
            self.casting_animation_timer.Start()

    def _scale(self, value: float) -> float:
        return value * self.appearance_window.get_panel_scale()

    def _bar_font_scale(self, height: float) -> float:
        return max(height / 13.0, 1.0)

    def _get_conditioned(self, account) -> tuple[Color, bool, bool, bool, bool, bool]:
        buff_ids = [buff.SkillId for buff in account.AgentData.Buffs.Buffs]
        same_map = Map.GetMapID() == account.AgentData.Map.MapID and Map.GetRegion()[0] == account.AgentData.Map.Region and Map.GetDistrict() == account.AgentData.Map.District

        deep_wounded = 482 in buff_ids
        poisoned = 484 in buff_ids or 483 in buff_ids
        enchanted = Agent.IsEnchanted(account.AgentData.AgentID) if same_map else False
        conditioned = Agent.IsConditioned(account.AgentData.AgentID) if same_map else False
        hexed = Agent.IsHexed(account.AgentData.AgentID) if same_map else False
        has_weaponspell = Agent.IsWeaponSpelled(account.AgentData.AgentID) if same_map else False

        if poisoned:
            return HealthState.Poisoned, deep_wounded, enchanted, conditioned, hexed, has_weaponspell

        bleeding = 478 in buff_ids
        if bleeding:
            return HealthState.Bleeding, deep_wounded, enchanted, conditioned, hexed, has_weaponspell

        if Agent.IsDegenHexed(account.AgentData.AgentID) if same_map else False:
            return HealthState.DegenHexed, deep_wounded, enchanted, conditioned, hexed, has_weaponspell

        return HealthState.Normal, deep_wounded, enchanted, conditioned, hexed, has_weaponspell

    def _draw_health_bar_local(
        self,
        width: float,
        height: float,
        max_health: float,
        current_health: float,
        regen: float,
        state,
        deep_wound: bool = False,
        enchanted: bool = False,
        conditioned: bool = False,
        hexed: bool = False,
        has_weaponspell: bool = False,
    ) -> bool:
        style = ImGui.get_style()
        draw_textures = style.Theme in ImGui.Textured_Themes
        pips = Utils.calculate_health_pips(max_health, regen)

        if not draw_textures:
            xpos, ypos = PyImGui.get_cursor_pos()
            style.PlotHistogram.push_color(state.rgb_tuple)
            style.FrameRounding.push_style_var(0)
            ImGui.progress_bar(current_health, width, height)
            style.FrameRounding.pop_style_var()
            style.PlotHistogram.pop_color()
            PyImGui.set_cursor_pos(xpos, ypos)

        ImGui.dummy(width, height)
        fraction = (max(0.0, min(1.0, current_health)) if max_health > 0 else 0.0)
        item_rect_min, item_rect_max, item_rect_size = ImGui.get_item_rect()
        width = item_rect_max[0] - item_rect_min[0]
        height = item_rect_max[1] - item_rect_min[1]
        item_rect = (item_rect_min[0] + 1, item_rect_min[1], width - 2, height)
        width = item_rect[2]
        progress_rect = (item_rect[0] + 1, item_rect[1] + 1, (width - 2) * fraction, height - 2)
        background_rect = (item_rect[0] + 1, item_rect[1] + 1, width - 2, height - 2)
        cursor_rect = (item_rect[0] - 2 + (width - 2) * fraction, item_rect[1] + 1, 4, height - 2) if fraction > 0 else (item_rect[0] + (width - 2) * fraction, item_rect[1] + 1, 4, height - 2)

        if draw_textures:
            match state:
                case HealthState.Poisoned:
                    empty_texture = ThemeTextures.HealthBarPoisonedEmpty
                    fill_texture = ThemeTextures.HealthBarPoisonedFill
                    cursor_texture = ThemeTextures.HealthBarPoisonedCursor
                case HealthState.Bleeding:
                    empty_texture = ThemeTextures.HealthBarBleedingEmpty
                    fill_texture = ThemeTextures.HealthBarBleedingFill
                    cursor_texture = ThemeTextures.HealthBarBleedingCursor
                case HealthState.DegenHexed:
                    empty_texture = ThemeTextures.HealthBarHexedEmpty
                    fill_texture = ThemeTextures.HealthBarHexedFill
                    cursor_texture = ThemeTextures.HealthBarHexedCursor
                case HealthState.Disconnected:
                    empty_texture = ThemeTextures.HealthBarDisconnectedEmpty
                    fill_texture = ThemeTextures.HealthBarDisconnectedFill
                    cursor_texture = ThemeTextures.HealthBarDisconnectedCursor
                case _:
                    empty_texture = ThemeTextures.HealthBarEmpty
                    fill_texture = ThemeTextures.HealthBarFill
                    cursor_texture = ThemeTextures.HealthBarCursor

            empty_texture.value.get_texture().draw_in_drawlist(background_rect[:2], background_rect[2:])
            fill_texture.value.get_texture().draw_in_drawlist(progress_rect[:2], progress_rect[2:])
            if current_health * max_health != max_health:
                cursor_texture.value.get_texture().draw_in_drawlist(cursor_rect[:2], cursor_rect[2:])

        if deep_wound:
            deep_wound_rect = (item_rect[0] + (width * 0.8), item_rect[1] + 1, (width * 0.2) + 1, height - 2)
            ThemeTextures.HealthBarDeepWound.value.get_texture().draw_in_drawlist(deep_wound_rect[:2], deep_wound_rect[2:])
            ThemeTextures.HealthBarDeepWoundCursor.value.get_texture().draw_in_drawlist(deep_wound_rect[:2], (2, deep_wound_rect[3]))

        indicators = (enchanted, conditioned, hexed, has_weaponspell)
        if any(indicators) and draw_textures:
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
                        indicator_texture.value.get_texture().draw_in_drawlist((item_rect[0] + item_rect[2] - x_offset, item_rect[1]), (height, height))
                    x_offset += height + 2

        display_label = str(int(current_health * max_health))
        bar_font_scale = self._bar_font_scale(height)
        PyImGui.push_font_scaled(ImguiFonts.Regular_14.value, bar_font_scale)
        textsize = PyImGui.calc_text_size(display_label)
        text_rect = (item_rect[0] + ((width - textsize[0]) / 2), item_rect[1] + ((height - textsize[1]) / 2) + self._scale(3), textsize[0], textsize[1])
        PyImGui.draw_list_add_text(
            text_rect[0],
            text_rect[1],
            style.Text.color_int,
            display_label,
        )
        PyImGui.pop_font_scaled()
        if draw_textures:
            pip_texture = ThemeTextures.Pip_Regen if pips > 0 else ThemeTextures.Pip_Degen
            pip_size = (10 * (height / 16), height)
            pip_y = item_rect[1] + ((height - pip_size[1]) / 2)
            pip_step = 8 * (height / 16)
            if pips > 0:
                pip_pos = text_rect[0] + text_rect[2] + 5
                for i in range(int(pips)):
                    pip_texture.value.get_texture().draw_in_drawlist((pip_pos + (i * pip_step), pip_y), pip_size)
            elif pips < 0:
                pip_pos = text_rect[0] - 5 - pip_size[0]
                for i in range(abs(int(pips))):
                    pip_texture.value.get_texture().draw_in_drawlist((pip_pos - (i * pip_step), pip_y), pip_size)
            PyImGui.draw_list_add_rect(item_rect_min[0], item_rect_min[1], item_rect_min[0] + item_rect_size[0], item_rect_min[1] + item_rect_size[1], style.Border.color_int, 0, 0, 1)
        else:
            pip_char = IconsFontAwesome5.ICON_ANGLE_RIGHT if pips > 0 else IconsFontAwesome5.ICON_ANGLE_LEFT
            pip_string = "".join([pip_char for _ in range(abs(int(pips)))])
            PyImGui.push_font_scaled(ImguiFonts.Regular_14.value, max((8.0 / 14.0) * bar_font_scale, 8.0 / 14.0))
            pip_text_size = PyImGui.calc_text_size(pip_string)
            pip_y = item_rect[1] + ((height - pip_text_size[1]) / 2)
            if pips > 0:
                PyImGui.draw_list_add_text(text_rect[0] + text_rect[2] + 5, pip_y, style.Text.color_int, pip_string)
            elif pips < 0:
                PyImGui.draw_list_add_text(text_rect[0] - 5 - pip_text_size[0], pip_y, style.Text.color_int, pip_string)
            PyImGui.pop_font_scaled()
        return PyImGui.is_item_clicked(0)

    def _draw_energy_bar_local(
        self,
        width: float,
        height: float,
        max_energy: float,
        current_energy: float,
        regen: float,
    ) -> bool:
        style = ImGui.get_style()
        pips = Utils.calculate_energy_pips(max_energy, regen)
        draw_textures = style.Theme in ImGui.Textured_Themes

        if not draw_textures:
            xpos, ypos = PyImGui.get_cursor_pos()
            style.PlotHistogram.push_color((30, 94, 153, 255))
            style.FrameRounding.push_style_var(0)
            ImGui.progress_bar(current_energy, width, height)
            style.FrameRounding.pop_style_var()
            style.PlotHistogram.pop_color()
            PyImGui.set_cursor_pos(xpos, ypos)

        ImGui.dummy(width, height)

        fraction = (max(0.0, min(1.0, current_energy)) if max_energy > 0 else 0.0)
        item_rect_min, item_rect_max, item_rect_size = ImGui.get_item_rect()
        width = item_rect_max[0] - item_rect_min[0]
        height = item_rect_max[1] - item_rect_min[1]
        item_rect = (item_rect_min[0], item_rect_min[1], width, height)
        progress_rect = (item_rect[0] + 1, item_rect[1] + 1, (width - 2) * fraction, height - 2)
        background_rect = (item_rect[0] + 1, item_rect[1] + 1, width - 2, height - 2)
        cursor_rect = (item_rect[0] - 2 + (width - 2) * fraction, item_rect[1] + 1, 4, height - 2) if fraction > 0 else (item_rect[0] + (width - 2) * fraction, item_rect[1] + 1, 4, height - 2)

        if draw_textures:
            ThemeTextures.EnergyBarEmpty.value.get_texture().draw_in_drawlist(background_rect[:2], background_rect[2:])
            ThemeTextures.EnergyBarFill.value.get_texture().draw_in_drawlist(progress_rect[:2], progress_rect[2:])
            if current_energy * max_energy != max_energy:
                ThemeTextures.EnergyBarCursor.value.get_texture().draw_in_drawlist(cursor_rect[:2], cursor_rect[2:])

        display_label = str(int(current_energy * max_energy))
        bar_font_scale = self._bar_font_scale(height)
        PyImGui.push_font_scaled(ImguiFonts.Regular_14.value, bar_font_scale)
        text_size = PyImGui.calc_text_size(display_label)
        text_rect = (item_rect[0] + ((width - text_size[0]) / 2), item_rect[1] + ((height - text_size[1]) / 2) + self._scale(3), text_size[0], text_size[1])
        PyImGui.draw_list_add_text(
            text_rect[0],
            text_rect[1],
            style.Text.color_int,
            display_label,
        )
        PyImGui.pop_font_scaled()
        if draw_textures:
            pip_texture = ThemeTextures.Pip_Regen if pips > 0 else ThemeTextures.Pip_Degen
            pip_size = (10 * (height / 16), height)
            pip_y = item_rect[1] + ((height - pip_size[1]) / 2)
            pip_step = 8 * (height / 16)
            if pips > 0:
                pip_pos = text_rect[0] + text_rect[2] + 5
                for i in range(int(pips)):
                    pip_texture.value.get_texture().draw_in_drawlist((pip_pos + (i * pip_step), pip_y), pip_size)
            elif pips < 0:
                pip_pos = text_rect[0] - 5 - pip_size[0]
                for i in range(abs(int(pips))):
                    pip_texture.value.get_texture().draw_in_drawlist((pip_pos - (i * pip_step), pip_y), pip_size)
            PyImGui.draw_list_add_rect(item_rect_min[0], item_rect_min[1], item_rect_min[0] + item_rect_size[0], item_rect_min[1] + item_rect_size[1], style.Border.color_int, 0, 0, 1)
        else:
            pip_char = IconsFontAwesome5.ICON_ANGLE_RIGHT if pips > 0 else IconsFontAwesome5.ICON_ANGLE_LEFT
            pip_string = "".join([pip_char for _ in range(abs(int(pips)))])
            PyImGui.push_font_scaled(ImguiFonts.Regular_14.value, max((8.0 / 14.0) * bar_font_scale, 8.0 / 14.0))
            pip_text_size = PyImGui.calc_text_size(pip_string)
            pip_y = item_rect[1] + ((height - pip_text_size[1]) / 2)
            if pips > 0:
                PyImGui.draw_list_add_text(text_rect[0] + text_rect[2] + 5, pip_y, style.Text.color_int, pip_string)
            elif pips < 0:
                PyImGui.draw_list_add_text(text_rect[0] - 5 - pip_text_size[0], pip_y, style.Text.color_int, pip_string)
            PyImGui.pop_font_scaled()
        return PyImGui.is_item_clicked(0)

    def _draw_square_cooldown_ex(self, button_pos, button_size, progress, tint=0.1):
        if isinstance(button_size, (int, float)):
            button_size = (button_size, button_size)
        if progress <= 0 or progress >= 1.0:
            return
        center_x = button_pos[0] + button_size[0] / 2.0
        center_y = button_pos[1] + button_size[1] / 2.0
        half_w = button_size[0] / 2.0
        half_h = button_size[1] / 2.0
        color = (int(255 * tint) << 24)
        start_angle = -math.pi / 2.0
        end_angle = start_angle - 2.0 * math.pi * progress
        segments = max(32, min(64, int(64 + 128 * (1 - progress))))
        points = [(center_x, center_y)]

        def intersection(angle):
            dx, dy = math.cos(angle), math.sin(angle)
            tx = half_w / abs(dx) if dx != 0 else float("inf")
            ty = half_h / abs(dy) if dy != 0 else float("inf")
            t = min(tx, ty)
            return (center_x + dx * t, center_y + dy * t)

        corner_angles = [-math.pi / 4, -3 * math.pi / 4, -5 * math.pi / 4, -7 * math.pi / 4, -math.pi / 4 - 2 * math.pi]
        a = start_angle
        for corner in corner_angles:
            if end_angle < corner < a or end_angle >= corner >= a:
                points.append(intersection(corner))
        for i in range(segments + 1):
            angle = start_angle + (end_angle - start_angle) * (i / segments)
            points.append(intersection(angle))
        unique_points = []
        for p in points:
            if not unique_points or (abs(unique_points[-1][0] - p[0]) > 0.1 or abs(unique_points[-1][1] - p[1]) > 0.1):
                unique_points.append(p)
        for i in range(1, len(unique_points) - 1):
            x1, y1 = unique_points[0]
            x2, y2 = unique_points[i]
            x3, y3 = unique_points[i + 1]
            PyImGui.draw_list_add_triangle_filled(x1, y1, x2, y2, x3, y3, color)

    def _draw_casting_animation(self, pos: tuple[float, float], size: tuple[float, float], min_alpha: int = 40):
        t = self.casting_animation_timer.GetElapsedTime() / 1000.0
        num_circles = 3
        cycle_duration = 1.25
        max_radius = max(size) * 0.75
        min_radius = max(size) * 0.05
        center_x = pos[0] + size[0] / 2
        center_y = pos[1] + size[1] / 2
        min_alpha = max(0, min(255, min_alpha))
        for i in range(num_circles):
            offset = i / num_circles
            progress = (t / cycle_duration + offset) % 1.0
            radius = max_radius - (max_radius - min_radius) * progress
            alpha = int(min_alpha + (255 - min_alpha) * (1.0 - progress) ** 1.5)
            alpha = max(0, min(255, alpha))
            swirl_angle = math.sin((t + i) * 2.0) * 0.1
            cx = center_x + math.cos(swirl_angle) * 0.0
            cy = center_y + math.sin(swirl_angle) * 0.0
            color = Color.from_tuple((0, 0, 0, alpha / 255.0))
            PyImGui.push_clip_rect(pos[0], pos[1], pos[0] + size[0], pos[1] + size[1], True)
            PyImGui.draw_list_add_circle(cx, cy, radius, color.color_int, 36, 6.0)
            PyImGui.pop_clip_rect()

    def _get_skill_texture(self, skill_id: int) -> str:
        texture = GLOBAL_CACHE.Skill.ExtraData.GetTexturePath(skill_id)
        return texture if texture and os.path.exists(texture) else ""

    def _show_skill_tooltip(self, skill: CachedSkillInfo, show_usage=True) -> None:
        if not skill or not skill.skill_id:
            return
        PyImGui.set_next_window_size((300, 0), PyImGui.ImGuiCond.Always)
        if ImGui.begin_tooltip():
            ImGui.push_font("Regular", 14)
            ImGui.text_colored(f"{skill.name} (ID: {skill.skill_id})", Color(227, 211, 165, 255).color_tuple)
            ImGui.pop_font()
            ImGui.separator()
            if skill.description:
                ImGui.text_wrapped(skill.description)
            if show_usage:
                PyImGui.spacing()
                gray_color = Color(150, 150, 150, 255)
                ImGui.push_font("Regular", 12)
                ImGui.text_colored("Click to use on current target", gray_color.color_tuple)
                PyImGui.set_cursor_pos_y(PyImGui.get_cursor_pos_y() - 2)
                ImGui.text_colored("Ctrl + Click to use on self", gray_color.color_tuple)
                PyImGui.set_cursor_pos_y(PyImGui.get_cursor_pos_y() - 2)
                ImGui.text_colored("Shift + Click to toggle active/inactive", gray_color.color_tuple)
                ImGui.pop_font()
            ImGui.end_tooltip()

    def _get_skill_target(self, account, cached_skill: CachedSkillInfo) -> int | None:
        if not cached_skill or cached_skill.skill_id == 0:
            return None
        target_id = Player.GetTargetID()
        is_gadget = Agent.IsGadget(target_id)
        is_item = Agent.IsItem(target_id)
        if cached_skill.is_enchantment or cached_skill.is_shout:
            allegiance, _ = Agent.GetAllegiance(target_id) if target_id != 0 else (Allegiance.Neutral, None)
            if allegiance in [Allegiance.Ally, Allegiance.Minion, Allegiance.SpiritPet]:
                return target_id
            return Player.GetAgentID() if PyImGui.get_io().key_ctrl else account.AgentData.AgentID
        return Player.GetAgentID() if PyImGui.get_io().key_ctrl else target_id if not is_item and not is_gadget and target_id else account.AgentData.AgentID

    def _draw_rich_skill_bar(self, account, options) -> None:
        skill_size = self._scale(float(RICH_BAR_HEIGHT))
        style = ImGui.get_style()
        draw_textures = style.Theme in ImGui.Textured_Themes
        texture_theme = style.Theme if draw_textures else StyleTheme.Guild_Wars
        for slot, skill_info in enumerate(account.AgentData.Skillbar.Skills):
            skill_id = int(skill_info.Id)
            if skill_id not in self.skill_cache:
                self.skill_cache[skill_id] = CachedSkillInfo(skill_id)
            skill = self.skill_cache[skill_id]
            if skill.texture_path:
                ImGui.image(skill.texture_path, (skill_size, skill_size), uv0=(0.0625, 0.0625) if draw_textures else (0, 0), uv1=(0.9375, 0.9375) if draw_textures else (1, 1))
                if PyImGui.is_item_hovered():
                    self._show_skill_tooltip(skill)
            else:
                ImGui.dummy(skill_size, skill_size)
                item_rect_min = PyImGui.get_item_rect_min()
                PyImGui.draw_list_add_rect(item_rect_min[0], item_rect_min[1], item_rect_min[0] + skill_size, item_rect_min[1] + skill_size, Color(50, 50, 50, 255).color_int, 0, 0, 2)
                if slot < NUMBER_OF_SKILLS - 1:
                    PyImGui.same_line(0, 0)
                continue

            item_rect_min = PyImGui.get_item_rect_min()
            skill_recharge = int(skill_info.Recharge)
            adrenaline = int(skill_info.Adrenaline)
            enough_adrenaline = adrenaline >= skill.adrenaline_cost
            casting_skill = account.AgentData.Skillbar.CastingSkillID

            if skill_recharge > 0 and skill.recharge_time > 0:
                self._draw_square_cooldown_ex((item_rect_min[0], item_rect_min[1]), skill_size, skill_recharge / (skill.recharge_time * 1000.0), tint=0.6)
                recharge_seconds = f"{int(skill_recharge / 1000)}"
                text_size = PyImGui.calc_text_size(recharge_seconds)
                PyImGui.draw_list_add_text(
                    item_rect_min[0] + ((skill_size - text_size[0]) / 2),
                    item_rect_min[1] + ((skill_size - text_size[1]) / 2),
                    ImGui.get_style().Text.color_int,
                    recharge_seconds,
                )
            elif casting_skill == skill.skill_id:
                self._draw_casting_animation(item_rect_min, (skill_size, skill_size))

            if not enough_adrenaline:
                adrenaline_fraction = adrenaline / skill.adrenaline_cost if skill.adrenaline_cost > 0 else 0.0
                adrenaline_fraction = max(0.0, min(adrenaline_fraction, 1.0))
                fill_rect = (item_rect_min[0], item_rect_min[1], skill_size, skill_size - (skill_size * adrenaline_fraction))
                PyImGui.draw_list_add_rect_filled(fill_rect[0], fill_rect[1], fill_rect[0] + fill_rect[2], fill_rect[1] + fill_rect[3], Color(0, 0, 0, 150).color_int, 0, 0)
                PyImGui.draw_list_add_line(fill_rect[0], fill_rect[1] + fill_rect[3], fill_rect[0] + fill_rect[2], fill_rect[1] + fill_rect[3], Color(0, 0, 0, 255).color_int, 1)

            if not options.Skills[slot]:
                if draw_textures:
                    hovered = PyImGui.is_item_hovered()
                    ThemeTextures.Cancel.value.get_texture(texture_theme).draw_in_drawlist(PyImGui.get_item_rect_min(), (skill_size, skill_size), state=TextureState.Hovered if hovered else TextureState.Normal)
                else:
                    PyImGui.draw_list_add_rect_filled(item_rect_min[0], item_rect_min[1], item_rect_min[0] + skill_size, item_rect_min[1] + skill_size, Color(89, 0, 0, 120).color_int, 0, 0)

            account_email = Player.GetAccountEmail()
            queued_skill_messages = self.message_cache.get(account_email, {}).get(SharedCommandType.UseSkill, {})
            if queued_skill_messages:
                queued_skill_usage = {
                    index: msg for index, msg in GLOBAL_CACHE.ShMem.GetAllMessages()
                    if msg.Command == SharedCommandType.UseSkill and msg.ReceiverEmail == account_email and msg.Params[1] == float(skill.skill_id) and index in queued_skill_messages
                }
                if queued_skill_usage and draw_textures:
                    hovered = PyImGui.is_item_hovered()
                    ThemeTextures.Check.value.get_texture(texture_theme).draw_in_drawlist(PyImGui.get_item_rect_min(), (skill_size, skill_size), state=TextureState.Hovered if hovered else TextureState.Normal)
                else:
                    indices_to_delete = [index for index, msg in queued_skill_messages.items() if msg[1] == skill.skill_id]
                    for index in indices_to_delete:
                        del queued_skill_messages[index]

            if PyImGui.is_item_clicked(0) and enough_adrenaline:
                if PyImGui.get_io().key_shift:
                    if options:
                        options.Skills[slot] = not options.Skills[slot]
                else:
                    target_id = self._get_skill_target(account, skill)
                    if target_id is not None and skill_id != 0:
                        message_index = GLOBAL_CACHE.ShMem.SendMessage(Player.GetAccountEmail(), account.AccountEmail, SharedCommandType.UseSkill, (target_id, skill_id))
                        if account.AccountEmail not in self.message_cache:
                            self.message_cache[account.AccountEmail] = {}
                        if SharedCommandType.UseSkill not in self.message_cache[account.AccountEmail]:
                            self.message_cache[account.AccountEmail][SharedCommandType.UseSkill] = {}
                        self.message_cache[account.AccountEmail][SharedCommandType.UseSkill][message_index] = (target_id, skill.skill_id)

            if draw_textures:
                texture_state = TextureState.Normal if not skill.is_elite else TextureState.Active
                ThemeTextures.Skill_Frame.value.get_texture(texture_theme).draw_in_drawlist(item_rect_min[:2], (skill_size, skill_size), state=texture_state)

            if slot < NUMBER_OF_SKILLS - 1:
                PyImGui.same_line(0, 0)

    def _enter_skill_template_code(self, account) -> None:
        if not self.template_popup_open:
            return
        PyImGui.open_popup("Enter Skill Template Code")
        PyImGui.set_window_pos(500, 100, PyImGui.ImGuiCond.Always)
        if PyImGui.begin_popup("Enter Skill Template Code"):
            self.template_code = ImGui.input_text("##template_code", self.template_code)
            if ImGui.button("Load"):
                GLOBAL_CACHE.ShMem.SendMessage(Player.GetAccountEmail(), account.AccountEmail, SharedCommandType.LoadSkillTemplate, ExtraData=(self.template_code, 0, 0, 0))
                self.template_popup_open = False
                PyImGui.close_current_popup()
            PyImGui.same_line(0, 10)
            if ImGui.button("Cancel"):
                PyImGui.close_current_popup()
                self.template_popup_open = False
            if PyImGui.is_mouse_clicked(0) and not PyImGui.is_any_item_hovered():
                PyImGui.close_current_popup()
                self.template_popup_open = False
            PyImGui.end_popup()

    def _draw_buffs_and_upkeeps(self, account, skill_size: float = 28):
        style = ImGui.get_style()
        hard_mode_effect_id = 1912
        effects = [effect for effect in account.AgentData.Buffs.Buffs if effect.Type == 2]
        upkeeps = [effect for effect in account.AgentData.Buffs.Buffs if effect.Type == 1]

        def draw_buff(effect: CachedSkillInfo, duration: float, remaining: float, draw_effect_frame: bool = True, size: float = skill_size):
            if not effect.texture_path:
                ImGui.dummy(size, size)
            else:
                ImGui.image(effect.texture_path, (size, size), uv0=(0.125, 0.125) if not draw_effect_frame else (0.0625, 0.0625), uv1=(0.875, 0.875) if not draw_effect_frame else (0.9375, 0.9375))

            item_rect_min = PyImGui.get_item_rect_min()
            item_rect_max = PyImGui.get_item_rect_max()

            if draw_effect_frame:
                effect.frame_texture.draw_in_drawlist(item_rect_min[:2], (size, size), state=effect.texture_state)

            if duration > 0 and remaining:
                progress_background_rect = (item_rect_min[0] + 2, item_rect_max[1] - 4, item_rect_max[0] - 2, item_rect_max[1] - 1)
                PyImGui.draw_list_add_rect_filled(progress_background_rect[0], progress_background_rect[1], progress_background_rect[2], progress_background_rect[3], Color(0, 0, 0, 255).color_int, 0, 0)
                progress_rect = (progress_background_rect[0] + 1, progress_background_rect[1] + 1, progress_background_rect[2] - 2, progress_background_rect[3] - 1)
                fraction = remaining / (duration * 1000.0)
                progress_width = (progress_rect[2] - progress_rect[0]) * fraction
                PyImGui.draw_list_add_rect_filled(progress_rect[0], progress_rect[1], progress_rect[0] + progress_width, progress_rect[3], effect.progress_color, 0, 0)
                remaining_text = f"{remaining/1000:.0f}" if remaining >= 1000 else f"{remaining/1000:.1f}".lstrip("0")
                text_size = PyImGui.calc_text_size(remaining_text)
                offset_x = (size - text_size[0]) / 2
                offset_y = (size - text_size[1]) / 2
                PyImGui.draw_list_add_rect_filled(item_rect_min[0] + offset_x - 1, item_rect_min[1] + offset_y - 1, item_rect_min[0] + offset_x + text_size[0] + 1, item_rect_min[1] + offset_y + text_size[1] + 1, Color(0, 0, 0, 150).color_int, 2, 0)
                PyImGui.draw_list_add_text(item_rect_min[0] + offset_x, item_rect_min[1] + offset_y, style.Text.color_int, remaining_text)

            if PyImGui.is_item_hovered():
                self._show_skill_tooltip(effect, show_usage=False)

        def draw_morale(morale: int, size: float = skill_size):
            morale_display = f"{('+' if morale > 100 else '-')}{abs(100 - morale)}%"
            texture = ThemeTextures.DeathPenalty.value.get_texture() if morale < 100 else ThemeTextures.MoraleBoost.value.get_texture()
            ImGui.push_font("Regular", 11)
            ImGui.dummy(size, size)
            item_rect_min = PyImGui.get_item_rect_min()
            item_rect_max = PyImGui.get_item_rect_max()
            item_rect = (item_rect_min[0], item_rect_min[1], item_rect_max[0] - item_rect_min[0], item_rect_max[1] - item_rect_min[1])
            texture.draw_in_drawlist(item_rect[:2], (size, size))
            text_size = PyImGui.calc_text_size(morale_display)
            offset_x = (size - text_size[0]) / 2
            offset_y = (size - text_size[1])
            PyImGui.draw_list_add_text(item_rect[0] + offset_x, item_rect[1] + offset_y, Color(201, 188, 145, 255).color_int, morale_display)
            ImGui.pop_font()
            PyImGui.table_next_column()

        def draw_hardmode():
            if any(effect.SkillId == hard_mode_effect_id for effect in effects):
                to_kill = Map.GetFoesToKill()
                texture = ThemeTextures.HardMode.value.get_texture(StyleTheme.Guild_Wars) if to_kill > 0 else ThemeTextures.HardModeCompleted.value.get_texture(StyleTheme.Guild_Wars)
                ImGui.dummy(skill_size + 1, skill_size + 1)
                item_rect_min, _item_rect_max, _item_rect_size = ImGui.get_item_rect()
                texture.draw_in_drawlist(item_rect_min[:2], (skill_size + 1, skill_size + 1))
                PyImGui.table_next_column()

        if any(upkeeps):
            upkeep_size = self._scale(24)
            ImGui.dummy(0, upkeep_size)
            PyImGui.same_line(0, 0)
            for upkeep in upkeeps:
                if upkeep.SkillId == 0:
                    continue
                if upkeep.SkillId not in self.skill_cache:
                    self.skill_cache[upkeep.SkillId] = CachedSkillInfo(upkeep.SkillId)
                effect = self.skill_cache[upkeep.SkillId]
                draw_buff(effect, upkeep.Duration, upkeep.Remaining, False, upkeep_size)
            if any(effects):
                PyImGui.new_line()
                PyImGui.set_cursor_pos_y(PyImGui.get_cursor_pos_y() - self._scale(4))

        avail = PyImGui.get_content_region_avail()[0]
        style.CellPadding.push_style_var(0, 0)
        if ImGui.begin_table("##effects_table" + account.AccountEmail, max(1, round(avail / skill_size)), PyImGui.TableFlags.SizingFixedFit):
            PyImGui.table_next_row()
            PyImGui.table_next_column()
            if account.AgentData.Morale not in [0, 100]:
                draw_morale(account.AgentData.Morale, skill_size)
            draw_hardmode()
            player_effects = {}
            for effect in effects:
                remaining = effect.Remaining
                duration = effect.Duration
                effect_id = effect.SkillId
                if not effect_id or effect_id == hard_mode_effect_id:
                    continue
                if effect_id not in self.skill_cache:
                    self.skill_cache[effect_id] = CachedSkillInfo(effect_id)
                if effect_id not in player_effects or remaining > player_effects[effect_id][1]:
                    player_effects[effect_id] = (self.skill_cache[effect_id], remaining, duration)
            for _effect_id, (effect, remaining, duration) in player_effects.items():
                draw_buff(effect, duration, remaining, True, 28)
                PyImGui.table_next_column()
            ImGui.end_table()
        style.CellPadding.pop_style_var()
        PyImGui.new_line()

    def _draw_buffs_bar(self, account):
        style = ImGui.get_style()
        PyImGui.push_style_var(ImGuiStyleVar.WindowRounding, 0.0)
        PyImGui.push_style_var(ImGuiStyleVar.WindowPadding, 0.0)
        PyImGui.push_style_var(ImGuiStyleVar.WindowBorderSize, 0.0)
        PyImGui.push_style_var2(ImGuiStyleVar.WindowPadding, 0.0, 0.0)
        flags = (
            PyImGui.WindowFlags.NoCollapse |
            PyImGui.WindowFlags.NoTitleBar |
            PyImGui.WindowFlags.NoScrollbar |
            PyImGui.WindowFlags.AlwaysAutoResize |
            PyImGui.WindowFlags.NoScrollWithMouse |
            PyImGui.WindowFlags.NoBringToFrontOnFocus |
            PyImGui.WindowFlags.NoResize |
            PyImGui.WindowFlags.NoBackground
        )
        win_pos = PyImGui.get_window_pos()
        win_size = PyImGui.get_window_size()
        PyImGui.set_next_window_pos((win_pos[0], win_pos[1] + win_size[1] + (13 if style.Theme == StyleTheme.Guild_Wars else 4)), PyImGui.ImGuiCond.Always)
        PyImGui.set_next_window_size((win_size[0], 0), PyImGui.ImGuiCond.Always)
        opened = PyImGui.begin("##Buffs Bar" + account.AccountEmail, True, flags)
        PyImGui.pop_style_var(4)
        if opened:
            self._draw_buffs_and_upkeeps(account, self._scale(28))
        PyImGui.end()

    def draw_panel(self, account, cached_data: CacheData, messages: list) -> None:
        options = cached_data.party.options.get(account.AgentData.AgentID)
        if options is None:
            return

        panel_width = self._scale(225)
        bar_height = self._scale(13)
        row_overlap = self._scale(4)
        skill_bar_height = self._scale(RICH_BAR_HEIGHT)
        height = self._scale(28)
        height += skill_bar_height if self.appearance_window.get_show_player_skill_toggles() else 0
        height += row_overlap if self.appearance_window.get_show_player_skill_toggles() else 0

        if height > 0:
            if ImGui.begin_child("##bars" + account.AccountEmail, (panel_width, height)):
                curr_avail = PyImGui.get_content_region_avail()
                health_state, deep_wounded, enchanted, conditioned, hexed, has_weaponspell = self._get_conditioned(account)
                health_clicked = self._draw_health_bar_local(
                    curr_avail[0],
                    bar_height,
                    account.AgentData.Health.Max,
                    account.AgentData.Health.Current,
                    account.AgentData.Health.Regen,
                    health_state,
                    deep_wounded,
                    enchanted,
                    conditioned,
                    hexed,
                        has_weaponspell,
                )
                PyImGui.set_cursor_pos_y(PyImGui.get_cursor_pos_y() - row_overlap)
                energy_clicked = self._draw_energy_bar_local(
                    curr_avail[0],
                    bar_height,
                    account.AgentData.Energy.Max,
                    account.AgentData.Energy.Current,
                    account.AgentData.Energy.Regen,
                )
                if health_clicked or energy_clicked:
                    if Map.GetMapID() == account.AgentData.Map.MapID:
                        Player.ChangeTarget(account.AgentData.AgentID)

                if self.appearance_window.get_show_player_skill_toggles():
                    PyImGui.set_cursor_pos_y(PyImGui.get_cursor_pos_y() - row_overlap)
                    self._draw_rich_skill_bar(account, options)

            ImGui.end_child()

        #if self.appearance_window.get_show_player_skill_toggles():
        #    PyImGui.same_line(0, 2)


        opt_dict = {
            "Following": options.Following,
            "Looting": options.Looting,
            "Combat": options.Combat,
        }

        PyImGui.set_cursor_pos_y(PyImGui.get_cursor_pos_y() - self._scale(2))
        control_row_width = panel_width
        for name, value in opt_dict.items():
            ImGui.push_font("Regular", 10)
            active = ImGui.toggle_button(name + f"##{account.AccountEmail}", value, control_row_width / len(opt_dict) - self._scale(3), self._scale(20))
            ImGui.pop_font()
            if active != value:
                setattr(options, name, active)
            PyImGui.same_line(0, 2)

        self._draw_buffs_bar(account)


class HeroAI_AppearanceWindow:
    def is_open(self) -> bool:
        return window_factory.is_open("appearance")

    def set_open(self, value: bool) -> None:
        window_factory.set_open("appearance", value)

    def get_panel_scale(self) -> float:
        scale = IniManager().getFloat(window_factory.key("appearance"), "panel_table_scale", 1.0, section="Appearance")
        return max(PANEL_MIN_SCALE, min(PANEL_MAX_SCALE, scale))

    def set_panel_scale(self, scale: float) -> None:
        clamped_scale = max(PANEL_MIN_SCALE, min(PANEL_MAX_SCALE, scale))
        IniManager().set(window_factory.key("appearance"), "panel_table_scale", float(clamped_scale), section="Appearance")
        IniManager().set(window_factory.key("appearance"), "panel_table_width", int(round(PANEL_BASE_WIDTH * clamped_scale)), section="Appearance")
        IniManager().set(window_factory.key("appearance"), "panel_table_height", int(round(PANEL_BASE_HEIGHT * clamped_scale)), section="Appearance")
        IniManager().save_vars(window_factory.key("appearance"))

    def get_show_main_skill_toggles(self) -> bool:
        return IniManager().getBool(window_factory.key("appearance"), "show_main_skill_toggles", True, section="Appearance")

    def set_show_main_skill_toggles(self, value: bool) -> None:
        IniManager().set(window_factory.key("appearance"), "show_main_skill_toggles", bool(value), section="Appearance")
        IniManager().save_vars(window_factory.key("appearance"))

    def get_show_player_skill_toggles(self) -> bool:
        return IniManager().getBool(window_factory.key("appearance"), "show_player_skill_toggles", True, section="Appearance")

    def set_show_player_skill_toggles(self, value: bool) -> None:
        IniManager().set(window_factory.key("appearance"), "show_player_skill_toggles", bool(value), section="Appearance")
        IniManager().save_vars(window_factory.key("appearance"))

    def get_show_players(self) -> bool:
        return IniManager().getBool(window_factory.key("appearance"), "show_players", True, section="Appearance")

    def set_show_players(self, value: bool) -> None:
        IniManager().set(window_factory.key("appearance"), "show_players", bool(value), section="Appearance")
        IniManager().save_vars(window_factory.key("appearance"))

    def get_show_players_in_separate_window(self) -> bool:
        return window_factory.is_open("players")

    def set_show_players_in_separate_window(self, value: bool) -> None:
        window_factory.set_open("players", value)

    def get_show_players_in_individual_windows(self) -> bool:
        return IniManager().getBool(window_factory.key("appearance"), "show_players_in_individual_windows", False, section="Appearance")

    def set_show_players_in_individual_windows(self, value: bool) -> None:
        IniManager().set(window_factory.key("appearance"), "show_players_in_individual_windows", bool(value), section="Appearance")
        IniManager().save_vars(window_factory.key("appearance"))

    def get_use_rich_player_panels(self) -> bool:
        return IniManager().getBool(window_factory.key("appearance"), "use_rich_player_panels", False, section="Appearance")

    def set_use_rich_player_panels(self, value: bool) -> None:
        IniManager().set(window_factory.key("appearance"), "use_rich_player_panels", bool(value), section="Appearance")
        IniManager().save_vars(window_factory.key("appearance"))

    def get_obfuscate_player_names(self) -> bool:
        return IniManager().getBool(window_factory.key("appearance"), "obfuscate_player_names", False, section="Appearance")

    def set_obfuscate_player_names(self, value: bool) -> None:
        IniManager().set(window_factory.key("appearance"), "obfuscate_player_names", bool(value), section="Appearance")
        IniManager().save_vars(window_factory.key("appearance"))

    def draw_window(self) -> None:
        if not self.is_open():
            return

        expanded, open_ = window_factory.begin("appearance", self.is_open())
        self.set_open(open_)

        if expanded:
            PyImGui.text("Main Panel")
            PyImGui.separator()
            
            PyImGui.text("Scale:")       
            PyImGui.same_line(0,-1)     
            
            
            current_scale = self.get_panel_scale()
            scale_percent = int(round(current_scale * 100.0))
            new_scale_percent = PyImGui.slider_int("##panel_scale", scale_percent, int(PANEL_MIN_SCALE * 100), int(PANEL_MAX_SCALE * 100))
            if new_scale_percent != scale_percent:
                self.set_panel_scale(float(new_scale_percent) / 100.0)
                
            show_main_skill_toggles = self.get_show_main_skill_toggles()
            new_show_main_skill_toggles = PyImGui.checkbox("Show Main Skill Toggles", show_main_skill_toggles)
            if new_show_main_skill_toggles != show_main_skill_toggles:
                self.set_show_main_skill_toggles(new_show_main_skill_toggles)

            PyImGui.spacing()
            PyImGui.text("Players")
            PyImGui.separator()

            show_players = self.get_show_players()
            new_show_players = PyImGui.checkbox("Show Players", show_players)
            if new_show_players != show_players:
                self.set_show_players(new_show_players)

            #todo add achecks box to obfuscate player names in the player list for streamers who want privacy but still want to use the UI
            #the floating window ui in the heroai has aliases we can use

            if show_players:
                show_players_in_separate_window = self.get_show_players_in_separate_window()
                PyImGui.indent(20)
                obfuscate_player_names = self.get_obfuscate_player_names()
                new_obfuscate_player_names = PyImGui.checkbox("Obfuscate Player Names", obfuscate_player_names)
                if new_obfuscate_player_names != obfuscate_player_names:
                    self.set_obfuscate_player_names(new_obfuscate_player_names)

                use_rich_player_panels = self.get_use_rich_player_panels()
                new_use_rich_player_panels = PyImGui.checkbox("Use Rich Player Panels", use_rich_player_panels)
                if new_use_rich_player_panels != use_rich_player_panels:
                    self.set_use_rich_player_panels(new_use_rich_player_panels)

                new_show_players_in_separate_window = PyImGui.checkbox("Show Players In Separate Window", show_players_in_separate_window)
                if new_show_players_in_separate_window != show_players_in_separate_window:
                    self.set_show_players_in_separate_window(new_show_players_in_separate_window)

                if show_players_in_separate_window:
                    PyImGui.indent(20)
                    show_players_in_individual_windows = self.get_show_players_in_individual_windows()
                    new_show_players_in_individual_windows = PyImGui.checkbox("Pop Up Each Player In A Separate Window", show_players_in_individual_windows)
                    if new_show_players_in_individual_windows != show_players_in_individual_windows:
                        self.set_show_players_in_individual_windows(new_show_players_in_individual_windows)
                    PyImGui.unindent(20)

                show_player_skill_toggles = self.get_show_player_skill_toggles()
                new_show_player_skill_toggles = PyImGui.checkbox("Show Player Skill Toggles", show_player_skill_toggles)
                if new_show_player_skill_toggles != show_player_skill_toggles:
                    self.set_show_player_skill_toggles(new_show_player_skill_toggles)

                PyImGui.unindent(20)

        ImGui.End(window_factory.key("appearance"))


class HeroAI_MainWindow:
    def __init__(self, appearance_window: HeroAI_AppearanceWindow) -> None:
        self.appearance_window = appearance_window
        self.player_renderer = HeroAI_PlayerPanelRenderer(appearance_window)
        self.floating_button = ImGui.FloatingIcon(
            icon_path=HeroAIFloatingIcon.ICON_PATH,
            window_id="##floating_icon_example_button",
            window_name="Floating Icon Example Toggle",
            tooltip_visible="Hide window",
            tooltip_hidden="Show window",
            toggle_ini_key=window_factory.key("floating"),
            toggle_var_name="show_main_window",
            toggle_default=True,
            draw_callback=self.draw_window,
        )

    def draw_window(self) -> None:
        expanded, open_ = window_factory.begin("main", self.floating_button.visible)
        self.floating_button.sync_begin_with_close(open_)

        if expanded:
            self.DrawPanelButtons()

        ImGui.End(window_factory.key("main"))

    def DrawPanelButtons(self):
        global cached_data
        if cached_data is None:
            return

        def set_global_option(option_name="", skill_index=-1):
            global cached_data
            if cached_data is None:
                return

            accounts = cached_data.party.accounts.values()
            if not accounts:
                ConsoleLog("HeroAI", "No accounts found in shared memory.")
                return

            for account in accounts:
                if not account or not account.IsSlotActive or account.IsHero or account.IsPet or account.AgentPartyData.PartyID != GLOBAL_CACHE.Party.GetPartyID():
                    continue

                account_options = GLOBAL_CACHE.ShMem.GetHeroAIOptionsFromEmail(account.AccountEmail)
                if not account_options:
                    continue

                match option_name:
                    case "Following" | "Avoidance" | "Looting" | "Targeting" | "Combat":
                        value = getattr(cached_data.global_options, option_name)
                        setattr(account_options, option_name, value)
                    case "Skills":
                        if 0 <= skill_index < NUMBER_OF_SKILLS:
                            account_options.Skills[skill_index] = cached_data.global_options.Skills[skill_index]

        style = ImGui.get_style()
        table_width, _ = get_panel_dimensions(self.appearance_window.get_panel_scale())
        btn_size = (table_width / 5) - 4
        skill_size = (table_width / NUMBER_OF_SKILLS) - 8

        style.ItemSpacing.push_style_var(0, 0)
        style.CellPadding.push_style_var(2, 2)

        if PyImGui.begin_table(f"GameOptionTable##{"Global"}", 5, 0, 0, btn_size + 2):
            PyImGui.table_next_row()
            PyImGui.table_next_column()
            following = ImGui.toggle_button(IconsFontAwesome5.ICON_RUNNING + "##Following" + "Global", cached_data.global_options.Following, btn_size, btn_size)
            if following != cached_data.global_options.Following:
                cached_data.global_options.Following = following
                set_global_option("Following")
            ImGui.show_tooltip("Follow / Avoidance")

            PyImGui.table_next_column()
            looting = ImGui.toggle_button(IconsFontAwesome5.ICON_COINS + "##Looting" + "Global", cached_data.global_options.Looting, btn_size, btn_size)
            if looting != cached_data.global_options.Looting:
                cached_data.global_options.Looting = looting
                set_global_option("Looting")
            ImGui.show_tooltip("Looting")

            PyImGui.table_next_column()

            combat = ImGui.toggle_button(IconsFontAwesome5.ICON_SKULL_CROSSBONES + "##Combat" + "Global", cached_data.global_options.Combat, btn_size, btn_size)
            if combat != cached_data.global_options.Combat:
                cached_data.global_options.Combat = combat
                set_global_option("Combat")
            ImGui.show_tooltip("Combat")

            PyImGui.table_next_column()
            PyImGui.text("|")

            PyImGui.table_next_column()
            show_appearance = self.appearance_window.is_open()
            new_show_appearance = ImGui.toggle_button(IconsFontAwesome5.ICON_COG + "##Appearance" + "Global", show_appearance, btn_size, btn_size)
            if new_show_appearance != show_appearance:
                self.appearance_window.set_open(new_show_appearance)
            ImGui.show_tooltip("Appearance")
            PyImGui.end_table()

        if self.appearance_window.get_show_main_skill_toggles():
            style.ButtonPadding.push_style_var(5 if style.Theme not in ImGui.Textured_Themes else 0, 3 if style.Theme not in ImGui.Textured_Themes else 2)
            if PyImGui.begin_table(f"SkillsTable##{"Global"}", NUMBER_OF_SKILLS, 0, 0, (btn_size / 3)):
                PyImGui.table_next_row()
                for i in range(NUMBER_OF_SKILLS):
                    PyImGui.table_next_column()
                    skill_active = ImGui.toggle_button(f"{i + 1}##Skill{i}" + "Global", cached_data.global_options.Skills[i], skill_size, skill_size)
                    if skill_active != cached_data.global_options.Skills[i]:
                        cached_data.global_options.Skills[i] = skill_active
                        set_global_option("Skills", i)
                    ImGui.show_tooltip(f"Skill {i + 1}")
                PyImGui.end_table()
            style.ButtonPadding.pop_style_var()

        if self.appearance_window.get_show_players() and not self.appearance_window.get_show_players_in_separate_window():
            PyImGui.dummy(0, 10)
            PyImGui.separator()

            if PyImGui.collapsing_header("Players##EmbeddedPlayers"):
                sorted_accounts = sorted(cached_data.party.accounts.values(), key=lambda acc: acc.AgentPartyData.PartyPosition)
                player_index = 0
                for account in sorted_accounts:
                    if not account or not account.IsSlotActive or account.IsHero or account.IsPet or account.AgentPartyData.PartyID != GLOBAL_CACHE.Party.GetPartyID():
                        continue

                    player_index += 1
                    account_options = cached_data.party.options.get(account.AgentData.AgentID)
                    if account_options is None:
                        continue

                    display_name = (
                        self.player_renderer.get_window_title(account)
                        if self.appearance_window.get_use_rich_player_panels()
                        else self.player_renderer.get_display_name(account)
                    )
                    header_label = f"{player_index}. {display_name}##ControlPlayer{player_index}"
                    if PyImGui.collapsing_header(header_label):
                        if self.appearance_window.get_use_rich_player_panels():
                            self.player_renderer.draw_rich_panel(
                                account,
                                cached_data,
                                [],
                            )
                        else:
                            self.player_renderer.draw_simple_panel(account.AccountEmail, account_options)
                    PyImGui.spacing()

        style.ItemSpacing.pop_style_var()
        style.CellPadding.pop_style_var()

    def draw_follower_panel_buttons(self, identifier: str, game_option) -> None:
        if game_option is None:
            return

        style = ImGui.get_style()
        table_width, _ = get_panel_dimensions(self.appearance_window.get_panel_scale())
        btn_size = (table_width / 5) - 4
        skill_size = (table_width / NUMBER_OF_SKILLS) - 8

        style.ItemSpacing.push_style_var(0, 0)
        style.CellPadding.push_style_var(2, 2)

        if PyImGui.begin_table(f"FollowerGameOptionTable##{identifier}", 3, 0, 0, btn_size + 2):
            PyImGui.table_next_row()
            PyImGui.table_next_column()
            following = ImGui.toggle_button(IconsFontAwesome5.ICON_RUNNING + f"##Following{identifier}", game_option.Following, btn_size * 1.45, btn_size)
            if following != game_option.Following:
                game_option.Following = following
            ImGui.show_tooltip("Follow / Avoidance")

            PyImGui.table_next_column()
            looting = ImGui.toggle_button(IconsFontAwesome5.ICON_COINS + f"##Looting{identifier}", game_option.Looting, btn_size* 1.45, btn_size)
            if looting != game_option.Looting:
                game_option.Looting = looting
            ImGui.show_tooltip("Looting")

            PyImGui.table_next_column()
            combat = ImGui.toggle_button(IconsFontAwesome5.ICON_SKULL_CROSSBONES + f"##Combat{identifier}", game_option.Combat, btn_size* 1.45, btn_size)
            if combat != game_option.Combat:
                game_option.Combat = combat
            ImGui.show_tooltip("Combat")
            PyImGui.end_table()

        if self.appearance_window.get_show_player_skill_toggles():
            style.ButtonPadding.push_style_var(5 if style.Theme not in ImGui.Textured_Themes else 0, 3 if style.Theme not in ImGui.Textured_Themes else 2)
            if PyImGui.begin_table(f"FollowerSkillsTable##{identifier}", NUMBER_OF_SKILLS, 0, 0, (btn_size / 3)):
                PyImGui.table_next_row()
                for i in range(NUMBER_OF_SKILLS):
                    PyImGui.table_next_column()
                    skill_active = ImGui.toggle_button(f"{i + 1}##Skill{i}{identifier}", game_option.Skills[i], skill_size, skill_size)
                    if skill_active != game_option.Skills[i]:
                        game_option.Skills[i] = skill_active
                    ImGui.show_tooltip(f"Skill {i + 1}")
                PyImGui.end_table()
            style.ButtonPadding.pop_style_var()

        style.ItemSpacing.pop_style_var()
        style.CellPadding.pop_style_var()

class HeroAI_PlayersWindow:
    def __init__(self, appearance_window: HeroAI_AppearanceWindow) -> None:
        self.appearance_window = appearance_window
        self.player_renderer = HeroAI_PlayerPanelRenderer(appearance_window)

    def draw_window(self) -> None:
        global cached_data
        if (
            cached_data is None
            or not self.appearance_window.get_show_players()
            or not self.appearance_window.get_show_players_in_separate_window()
        ):
            return

        sorted_accounts = sorted(cached_data.party.accounts.values(), key=lambda acc: acc.AgentPartyData.PartyPosition)
        player_accounts = []
        for account in sorted_accounts:
            if not account or not account.IsSlotActive or account.IsHero or account.IsPet or account.AgentPartyData.PartyID != GLOBAL_CACHE.Party.GetPartyID():
                continue
            player_accounts.append(account)
            if len(player_accounts) >= 16:
                break

        if self.appearance_window.get_show_players_in_individual_windows():
            player_index = 0
            for account in player_accounts:
                player_index += 1
                account_options = cached_data.party.options.get(account.AgentData.AgentID)
                if account_options is None:
                    continue

                display_name = (
                    self.player_renderer.get_window_title(account)
                    if self.appearance_window.get_use_rich_player_panels()
                    else self.player_renderer.get_display_name(account)
                )
                window_title = f"{player_index}. {display_name}##HeroAIPlayerWindow{player_index}"
                if PyImGui.begin(window_title, PyImGui.WindowFlags.AlwaysAutoResize):
                    if self.appearance_window.get_use_rich_player_panels():
                        self.player_renderer.draw_rich_panel(
                            account,
                            cached_data,
                            [],
                        )
                    else:
                        self.player_renderer.draw_simple_panel(account.AccountEmail, account_options)
                PyImGui.end()
            return

        expanded, open_ = window_factory.begin("players", self.appearance_window.get_show_players_in_separate_window())
        self.appearance_window.set_show_players_in_separate_window(open_)

        if expanded:
            player_index = 0
            for account in player_accounts:
                player_index += 1
                account_options = cached_data.party.options.get(account.AgentData.AgentID)
                if account_options is None:
                    continue

                display_name = (
                    self.player_renderer.get_window_title(account)
                    if self.appearance_window.get_use_rich_player_panels()
                    else self.player_renderer.get_display_name(account)
                )
                header_label = f"{player_index}. {display_name}##ControlPlayer{player_index}"
                if PyImGui.collapsing_header(header_label):
                    if self.appearance_window.get_use_rich_player_panels():
                        self.player_renderer.draw_rich_panel(
                            account,
                            cached_data,
                            [],
                        )
                    else:
                        self.player_renderer.draw_simple_panel(account.AccountEmail, account_options)
                PyImGui.spacing()

        ImGui.End(window_factory.key("players"))

FloatingButton: HeroAI_MainWindow | None = None
AppearanceWindow: HeroAI_AppearanceWindow | None = None
PlayersWindow: HeroAI_PlayersWindow | None = None
cached_data: CacheData | None = None


def _ensure_ini() -> bool:
    if HeroAIFloatingIcon.INI_INIT:
        return True

    if not window_factory.ensure_ini():
        return False

    HeroAIFloatingIcon.MAIN_INI_KEY = window_factory.key("main")
    HeroAIFloatingIcon.FLOATING_INI_KEY = window_factory.key("floating")
    HeroAIFloatingIcon.CONFIG_INI_KEY = window_factory.key("appearance")

    HeroAIFloatingIcon.INI_INIT = True
    return True


def _ensure_state() -> HeroAI_MainWindow:
    global AppearanceWindow, FloatingButton, PlayersWindow, cached_data
    if FloatingButton is None:
        cached_data = CacheData()
        AppearanceWindow = HeroAI_AppearanceWindow()
        FloatingButton = HeroAI_MainWindow(AppearanceWindow)
        PlayersWindow = HeroAI_PlayersWindow(AppearanceWindow)
        FloatingButton.floating_button.load_visibility()
    return FloatingButton


def main():
    global AppearanceWindow, PlayersWindow, cached_data
    try:
        if not _ensure_ini():
            return

        state = _ensure_state()
        if cached_data is not None:
            cached_data.Update()
        state.floating_button.draw(HeroAIFloatingIcon.FLOATING_INI_KEY)
        if AppearanceWindow is not None:
            AppearanceWindow.draw_window()
        if PlayersWindow is not None:
            PlayersWindow.draw_window()
    except Exception as exc:
        Py4GW.Console.Log(HeroAIFloatingIcon.MODULE_NAME, f"Error: {exc}", Py4GW.Console.MessageType.Error)
        raise


def configure():
    if not _ensure_ini():
        return
    if AppearanceWindow is None:
        _ensure_state()
    if AppearanceWindow is not None:
        AppearanceWindow.set_open(not AppearanceWindow.is_open())


def tooltip():
    import PyImGui
    from Py4GWCoreLib.py4gwcorelib_src.Color import Color
    from Py4GWCoreLib.ImGui import ImGui
    PyImGui.begin_tooltip()

    # Title
    title_color = Color(255, 200, 100, 255)
    ImGui.push_font("Regular", 20)
    PyImGui.text_colored("HeroAI: Multibox Combat Engine", title_color.to_tuple_normalized())
    ImGui.pop_font()
    PyImGui.spacing()
    PyImGui.separator()

    # Description
    PyImGui.text("An advanced multi-account synchronization and combat AI system.")
    PyImGui.text("This widget transforms extra game instances into intelligent,")
    PyImGui.text("automated party members that behave like high-performance heroes.")
    PyImGui.spacing()

    # Features
    PyImGui.text_colored("Features:", title_color.to_tuple_normalized())
    PyImGui.bullet_text("Multibox Logic: Synchronizes actions across multiple game clients")
    PyImGui.bullet_text("Advanced AI: Replaces standard hero behavior with custom combat routines")
    PyImGui.bullet_text("Formation Control: Dynamic follower distancing and tactical positioning")
    PyImGui.bullet_text("Automation Suite: Integrated auto-looting, salvaging, and cutscene skipping")
    PyImGui.bullet_text("Behavior Trees: Complex decision-making for combat and out-of-combat states")
    PyImGui.bullet_text("Shared Memory: Seamless data exchange via the Shared Memory Manager (SMM)")

    PyImGui.spacing()
    PyImGui.separator()
    PyImGui.spacing()

    # Credits
    PyImGui.text_colored("Credits:", title_color.to_tuple_normalized())
    PyImGui.bullet_text("Developed by Apo")
    PyImGui.bullet_text("Contributors: Mark, frenkey, Dharmantrix, aC, Greg-76, ")
    PyImGui.bullet_text("Wick-Divinus, LLYANL, Zilvereyes, valkogw")

    PyImGui.end_tooltip()


if __name__ == "__main__":
    main()


__all__ = ["main", "configure", "tooltip"]
