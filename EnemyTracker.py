import os

import PyImGui

from Py4GWCoreLib import Py4GW
from Py4GWCoreLib.AgentArray import AgentArray
from Py4GWCoreLib.Agent import Agent
from Py4GWCoreLib.ImGui import ImGui
from Py4GWCoreLib.IniManager import IniManager
from Py4GWCoreLib.Player import Player
from Py4GWCoreLib.py4gwcorelib_src.Color import ColorPalette
from Py4GWCoreLib.py4gwcorelib_src.Utils import Utils
from dataclasses import dataclass, field

@dataclass
class FloatingIconVars:
    MODULE_NAME: str = "Enemy Tracker"
    INI_PATH: str = "Widgets/Automation/Helpers/EnemyTracker"
    MAIN_INI_FILENAME: str = "EnemyTracker.ini"
    FLOATING_INI_FILENAME: str = "EnemyTrackerFloating.ini"

    MAIN_INI_KEY: str = ""
    FLOATING_INI_KEY: str = ""
    INI_INIT: bool = False
    ICON_PATH: str = os.path.join(Py4GW.Console.get_projects_path(), "crossed swords.png")
    GAME_UI_TEXTURE_BASE_PATH: str = os.path.join(Py4GW.Console.get_projects_path(), "Textures", "Game UI") + os.sep
    
@dataclass
class EnemyTrackerVars:
    enemy_array: list[int] = field(default_factory=list)


class EnemyTracker:
    def __init__(self) -> None:
        self.floating_button = ImGui.FloatingIcon(
            icon_path=FloatingIconVars.ICON_PATH,
            window_id="##floating_icon_enemy_tracker_button",
            window_name="Enemy Tracker Toggle",
            tooltip_visible="Hide window",
            tooltip_hidden="Show window",
            toggle_ini_key=FloatingIconVars.FLOATING_INI_KEY,
            toggle_var_name="show_main_window",
            toggle_default=True,
            draw_callback=self.draw_window,
        )
        
        self.vars = EnemyTrackerVars()

    def _get_enemy_name(self, agent_id: int) -> str:
        name = Agent.GetNameByID(agent_id)
        if name:
            return name
        return f"Agent {agent_id}"

    def _get_health_caption(self, agent_id: int, health: float, max_health: int) -> str:
        current_hp = int(health * max_health)
        health_pips = Agent.GetHealthPips(agent_id)
        if health_pips > 0:
            pips_str = ">" * health_pips
        elif health_pips < 0:
            pips_str = "<" * abs(health_pips)
        else:
            pips_str = ""
        return f"{current_hp}/{max_health} {pips_str}".strip()

    def _get_health_color(self, agent_id: int) -> tuple[float, float, float, float]:
        color = ColorPalette.GetColor("firebrick").to_tuple_normalized()
        if Agent.IsDegenHexed(agent_id):
            color = ColorPalette.GetColor("dark_magenta").to_tuple_normalized()
        if Agent.IsPoisoned(agent_id):
            color = ColorPalette.GetColor("olive").to_tuple_normalized()
        if Agent.IsBleeding(agent_id):
            color = ColorPalette.GetColor("light_coral").to_tuple_normalized()
        return color

    def _draw_effect_icons(self, agent_id: int) -> None:
        bar_start_pos = PyImGui.get_cursor_pos()
        bar_height = 20
        cur_x, cur_y = bar_start_pos
        icon_y = cur_y + (bar_height - 16) * 0.5
        x = cur_x + 4

        if Agent.IsHexed(agent_id):
            PyImGui.set_cursor_pos(x, icon_y)
            ImGui.DrawTextureExtended(
                texture_path=FloatingIconVars.GAME_UI_TEXTURE_BASE_PATH + "ui_skill_identifier.png",
                size=(16, 16),
                uv0=(0.125, 0.5),
                uv1=(0.25, 0.75),
                tint=(255, 255, 255, 255),
                border_color=(255, 255, 255, 0),
            )
            x += 18

        if Agent.IsConditioned(agent_id):
            PyImGui.set_cursor_pos(x, icon_y)
            ImGui.DrawTextureExtended(
                texture_path=FloatingIconVars.GAME_UI_TEXTURE_BASE_PATH + "ui_skill_identifier.png",
                size=(16, 16),
                uv0=(0.125, 0.5),
                uv1=(0.25, 0.75),
                tint=(255, 255, 255, 125),
                border_color=(255, 255, 255, 0),
            )
            x += 18

        if Agent.IsEnchanted(agent_id):
            PyImGui.set_cursor_pos(x, icon_y)
            ImGui.DrawTextureExtended(
                texture_path=FloatingIconVars.GAME_UI_TEXTURE_BASE_PATH + "ui_skill_identifier.png",
                size=(16, 16),
                uv0=(0.625, 0.0),
                uv1=(0.75, 0.25),
                tint=(255, 255, 255, 255),
                border_color=(255, 255, 255, 0),
            )
            x += 18

        if Agent.IsWeaponSpelled(agent_id):
            PyImGui.set_cursor_pos(x, icon_y - 2)
            ImGui.DrawTextureExtended(
                texture_path=FloatingIconVars.GAME_UI_TEXTURE_BASE_PATH + "ui_skill_identifier.png",
                size=(20, 20),
                uv0=(0.35, 0.5),
                uv1=(0.5, 0.8),
                tint=(255, 255, 255, 255),
                border_color=(255, 255, 255, 0),
            )

    def _get_status_text(self, agent_id: int) -> str:
        statuses: list[str] = []
        if Agent.IsDead(agent_id):
            statuses.append("Dead")
        if Agent.IsHexed(agent_id):
            statuses.append("Hexed")
        if Agent.IsConditioned(agent_id):
            statuses.append("Conditioned")
        if Agent.IsEnchanted(agent_id):
            statuses.append("Enchanted")
        if Agent.IsWeaponSpelled(agent_id):
            statuses.append("Weapon Spell")
        if Agent.IsBleeding(agent_id):
            statuses.append("Bleeding")
        if Agent.IsPoisoned(agent_id):
            statuses.append("Poisoned")
        if Agent.IsCrippled(agent_id):
            statuses.append("Crippled")
        if Agent.IsDeepWounded(agent_id):
            statuses.append("Deep Wound")
        return ", ".join(statuses) if statuses else "No tracked statuses"

    def _draw_enemy_row(self, agent_id: int, player_xy: tuple[float, float]) -> None:
        enemy_name = self._get_enemy_name(agent_id)
        enc_name = Agent.GetEncNameStrByID(agent_id)
        health = Agent.GetHealth(agent_id)
        max_health = Agent.GetMaxHealth(agent_id)
        level = Agent.GetLevel(agent_id)
        distance = Utils.Distance(player_xy, Agent.GetXY(agent_id))
        status_text = self._get_status_text(agent_id)

        PyImGui.text(f"{enemy_name}  Lv {level}  ID {agent_id}  Dist {int(distance)}")
        avail_width = PyImGui.get_content_region_avail()[0]
        PyImGui.push_style_color(PyImGui.ImGuiCol.PlotHistogram, self._get_health_color(agent_id))
        PyImGui.progress_bar(health, avail_width, self._get_health_caption(agent_id, health, max_health))
        PyImGui.pop_style_color(1)
        self._draw_effect_icons(agent_id)
        PyImGui.text(status_text)
        if enc_name:
            PyImGui.text(f"Enc: {enc_name}")
        PyImGui.separator()

    #region Draw
    def draw_window(self) -> None:
        expanded, open_ = ImGui.BeginWithClose(
            ini_key=FloatingIconVars.MAIN_INI_KEY,
            name=FloatingIconVars.MODULE_NAME,
            p_open=self.floating_button.visible,
            flags=PyImGui.WindowFlags.NoCollapse,
        )
        self.floating_button.sync_begin_with_close(open_)

        if expanded:
            player_xy = Player.GetXY()
            self.vars.enemy_array = AgentArray.Sort.ByDistance(AgentArray.GetEnemyArray(), player_xy)
            PyImGui.text(f"Enemy Count: {len(self.vars.enemy_array)}")
            PyImGui.separator()
            for agent_id in self.vars.enemy_array:
                if not Agent.IsDead(agent_id):
                    self._draw_enemy_row(agent_id, player_xy)

        ImGui.End(FloatingIconVars.MAIN_INI_KEY)


FloatingButton: EnemyTracker | None = None


def _ensure_ini() -> bool:
    if FloatingIconVars.INI_INIT:
        return True

    FloatingIconVars.MAIN_INI_KEY = IniManager().ensure_key(FloatingIconVars.INI_PATH, FloatingIconVars.MAIN_INI_FILENAME)
    FloatingIconVars.FLOATING_INI_KEY = IniManager().ensure_key(FloatingIconVars.INI_PATH, FloatingIconVars.FLOATING_INI_FILENAME)
    if not FloatingIconVars.MAIN_INI_KEY or not FloatingIconVars.FLOATING_INI_KEY:
        return False

    IniManager().load_once(FloatingIconVars.MAIN_INI_KEY)
    IniManager().load_once(FloatingIconVars.FLOATING_INI_KEY)

    FloatingIconVars.INI_INIT = True
    return True


def _ensure_state() -> EnemyTracker:
    global FloatingButton
    if FloatingButton is None:
        FloatingButton = EnemyTracker()
        FloatingButton.floating_button.load_visibility()
    return FloatingButton


def main():
    try:
        if not _ensure_ini():
            return

        state = _ensure_state()
        state.floating_button.draw(FloatingIconVars.FLOATING_INI_KEY)
    except Exception as exc:
        Py4GW.Console.Log(FloatingIconVars.MODULE_NAME, f"Error: {exc}", Py4GW.Console.MessageType.Error)
        raise


if __name__ == "__main__":
    main()
