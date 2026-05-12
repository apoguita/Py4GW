import math

import HeroAI.globals as hero_globals
import PyImGui

from Py4GWCoreLib import GLOBAL_CACHE, Agent, IconsFontAwesome5, ImGui, Map, Overlay, Range, Utils, WindowFrames, Color, ColorPalette, ConsoleLog, SharedCommandType
from Py4GWCoreLib import Key, Keystroke, ThrottledTimer, UIManager
from Py4GWCoreLib.GlobalCache.SharedMemory import AccountStruct, HeroAIOptionStruct
from Py4GWCoreLib.IniManager import IniManager
from Py4GWCoreLib.Player import Player

from HeroAI.cache_data import CacheData
from HeroAI.constants import NUMBER_OF_SKILLS
from HeroAI.follow.vector_fields import load_follow_movement_config, save_follow_movement_config
from HeroAI.utils import DrawFlagAll, DrawHeroFlag, IsHeroFlagged
from HeroAI.windows import HeroAI_FloatingWindows, HeroAI_Windows
from .constants import MAX_NUM_PLAYERS, NUMBER_OF_SKILLS

from HeroAI.constants import (FOLLOW_DISTANCE_OUT_OF_COMBAT, MAX_NUM_PLAYERS, MELEE_RANGE_VALUE, PARTY_WINDOW_FRAME_EXPLORABLE_OFFSETS,
                              PARTY_WINDOW_FRAME_OUTPOST_OFFSETS, PARTY_WINDOW_HASH, RANGED_RANGE_VALUE)


_SKILL_NAME_SUFFIXES: dict[str, str] = {
    "Summon_Spirits_kurzick": "(Kurzick)",
    "Summon_Spirits_luxon": "(Luxon)",
    "Save_Yourselves_kurzick": "(Kurzick)",
    "Save_Yourselves_luxon": "(Luxon)",
}
_skill_name_suffix_cache: dict[int, str] | None = None


def _get_skill_name_suffix(skill_id: int) -> str:
    global _skill_name_suffix_cache
    if _skill_name_suffix_cache is None:
        _skill_name_suffix_cache = {}
        for skill_key, suffix in _SKILL_NAME_SUFFIXES.items():
            resolved_id = GLOBAL_CACHE.Skill.GetID(skill_key)
            if resolved_id:
                _skill_name_suffix_cache[resolved_id] = suffix
    return _skill_name_suffix_cache.get(skill_id, "")


class HeroAI_BaseUI:
    show_debug = False
    outline_color: Color = Color(255, 255, 255, 255)
    color_tick = 0
    show_build_match_window = False
    show_follow_formations_quick_window = False
    show_follow_formations_editor_window = False
    HeroFlags: list[bool] = [False, False, False, False, False, False, False, False, False]
    AllFlag = False
    ClearFlags = False
    one_time_set_flag = False
    capture_hero_index = -1
    capture_hero_flag = False
    capture_flag_all = False
    follow_formations_ini_key = ""
    follow_formations_settings_key = ""
    follow_runtime_ini_key = ""
    follow_window_ini_vars_registered = False
    follow_window_ini_vars_registered_key = ""
    follow_formations_names: list[str] = []
    follow_formations_ids: list[str] = []
    follow_formations_selected_index = 0
    follow_move_threshold_default = float(Range.Area.value)
    follow_move_threshold_combat = float(Range.Touch.value)
    follow_move_threshold_flagged = 0.0
    follow_move_threshold_default_mode = "Area"
    follow_move_threshold_combat_mode = "Touch"
    follow_move_threshold_flagged_mode = "Zero"
    _build_match_timer = ThrottledTimer(750)
    _build_match_rows: list[tuple[int, str, int, int, str, str, str]] = []
    _build_match_signature_cache: dict[int, tuple[tuple[int, int, tuple[int, ...]], tuple[int, str, int, int, str, str, str]]] = {}
    _build_registry = None
    _supported_build_selected_key = ""
    _supported_build_selected_skill_id = 0
    _supported_build_last_detail_key = ""
    _supported_builds_cache: dict[str, dict[str, object]] = {}
    _team_viewer_anonymize = False
    _team_viewer_timer = ThrottledTimer(750)
    _team_viewer_rows: list[tuple[int, str, str, int, int, dict, tuple[int, ...], str]] = []
    _team_viewer_parse_cache: dict[str, tuple[str, tuple[int, int, dict, list]]] = {}
    _team_viewer_aliases: tuple[str, ...] = (
        "Gaile Gray",
        "Regina Buenaobra",
        "Emily Diehl",
        "Andrew Patrick",
        "Linsey Murdock",
        "Joe Kimmes",
        "Michael Gills",
        "Isaiah Cartwright",
    )
    _flag_map_signature = None
    _profession_palette_names = {
        1: "GW_Warrior",
        2: "GW_Ranger",
        3: "GW_Monk",
        4: "GW_Necromancer",
        5: "GW_Mesmer",
        6: "GW_Elementalist",
        7: "GW_Assassin",
        8: "GW_Ritualist",
        9: "GW_Paragon",
        10: "GW_Dervish",
    }

    class ButtonColor:
        def __init__(self, button_color: Color, hovered_color: Color, active_color: Color, texture_path: str = ""):
            self.button_color = button_color
            self.hovered_color = hovered_color
            self.active_color = active_color
            self.texture_path = texture_path

    ButtonColors = {
        "Resign": ButtonColor(button_color=Color(90, 0, 10, 255), hovered_color=Color(160, 0, 15, 255), active_color=Color(210, 0, 20, 255)),
        "PixelStack": ButtonColor(button_color=Color(90, 0, 10, 255), hovered_color=Color(160, 0, 15, 255), active_color=Color(190, 0, 20, 255)),
        "Flag": ButtonColor(button_color=Color(90, 0, 10, 255), hovered_color=Color(160, 0, 15, 255), active_color=Color(190, 0, 20, 255)),
        "ClearFlags": ButtonColor(button_color=Color(90, 0, 10, 255), hovered_color=Color(160, 0, 15, 255), active_color=Color(190, 0, 20, 255)),
        "Celerity": ButtonColor(button_color=Color(129, 33, 188, 255), hovered_color=Color(165, 100, 200, 255), active_color=Color(135, 225, 230, 255), texture_path="Textures\\Consumables\\Trimmed\\Essence_of_Celerity.png"),
        "GrailOfMight": ButtonColor(button_color=Color(70, 0, 10, 255), hovered_color=Color(160, 0, 15, 255), active_color=Color(252, 225, 115, 255), texture_path="Textures\\Consumables\\Trimmed\\Grail_of_Might.png"),
        "ArmorOfSalvation": ButtonColor(button_color=Color(96, 60, 15, 255), hovered_color=Color(187, 149, 38, 255), active_color=Color(225, 150, 0, 255), texture_path="Textures\\Consumables\\Trimmed\\Armor_of_Salvation.png"),
        "CandyCane": ButtonColor(button_color=Color(63, 91, 54, 255), hovered_color=Color(149, 72, 34, 255), active_color=Color(96, 172, 28, 255), texture_path="Textures\\Consumables\\Trimmed\\Rainbow_Candy_Cane.png"),
        "BirthdayCupcake": ButtonColor(button_color=Color(138, 54, 80, 255), hovered_color=Color(255, 186, 198, 255), active_color=Color(205, 94, 215, 255), texture_path="Textures\\Consumables\\Trimmed\\Birthday_Cupcake.png"),
        "GoldenEgg": ButtonColor(button_color=Color(245, 227, 143, 255), hovered_color=Color(253, 248, 234, 255), active_color=Color(129, 82, 35, 255), texture_path="Textures\\Consumables\\Trimmed\\Golden_Egg.png"),
        "CandyCorn": ButtonColor(button_color=Color(239, 174, 33, 255), hovered_color=Color(206, 178, 148, 255), active_color=Color(239, 77, 16, 255), texture_path="Textures\\Consumables\\Trimmed\\Candy_Corn.png"),
        "CandyApple": ButtonColor(button_color=Color(75, 26, 28, 255), hovered_color=Color(202, 60, 88, 255), active_color=Color(179, 0, 39, 255), texture_path="Textures\\Consumables\\Trimmed\\Candy_Apple.png"),
        "PumpkinPie": ButtonColor(button_color=Color(224, 176, 126, 255), hovered_color=Color(226, 209, 210, 255), active_color=Color(129, 87, 54, 255), texture_path="Textures\\Consumables\\Trimmed\\Slice_of_Pumpkin_Pie.png"),
        "DrakeKabob": ButtonColor(button_color=Color(28, 28, 28, 255), hovered_color=Color(190, 187, 184, 255), active_color=Color(94, 26, 13, 255), texture_path="Textures\\Consumables\\Trimmed\\Drake_Kabob.png"),
        "SkalefinSoup": ButtonColor(button_color=Color(68, 85, 142, 255), hovered_color=Color(255, 255, 107, 255), active_color=Color(106, 139, 51, 255), texture_path="Textures\\Consumables\\Trimmed\\Bowl_of_Skalefin_Soup.png"),
        "PahnaiSalad": ButtonColor(button_color=Color(113, 43, 25, 255), hovered_color=Color(185, 157, 90, 255), active_color=Color(137, 175, 10, 255), texture_path="Textures\\Consumables\\Trimmed\\Pahnai_Salad.png"),
        "WarSupplies": ButtonColor(button_color=Color(51, 26, 13, 255), hovered_color=Color(113, 43, 25, 255), active_color=Color(202, 115, 77, 255), texture_path="Textures\\Consumables\\Trimmed\\War_Supplies.png"),
        "Alcohol": ButtonColor(button_color=Color(58, 41, 50, 255), hovered_color=Color(169, 145, 111, 255), active_color=Color(173, 173, 156, 255), texture_path="Textures\\Consumables\\Trimmed\\Dwarven_Ale.png"),
        "Blank": ButtonColor(button_color=Color(0, 0, 0, 0), hovered_color=Color(0, 0, 0, 0), active_color=Color(0, 0, 0, 0)),
    }

    @staticmethod
    def _reset_flag_capture_state() -> None:
        HeroAI_BaseUI.ClearFlags = False
        HeroAI_BaseUI.one_time_set_flag = False
        HeroAI_BaseUI.capture_hero_index = -1
        HeroAI_BaseUI.capture_hero_flag = False
        HeroAI_BaseUI.capture_flag_all = False
        hero_globals.capture_mouse_timer.Stop()

    @staticmethod
    def _get_flag_option_pairs() -> tuple[list[HeroAIOptionStruct | None], list[AccountStruct | None], HeroAIOptionStruct | None]:
        active_account_option_pairs: list[tuple[AccountStruct, HeroAIOptionStruct]] = GLOBAL_CACHE.ShMem.GetAllActiveAccountHeroAIPairs(sort_results=False)
        options_by_party: list[HeroAIOptionStruct | None] = [None] * MAX_NUM_PLAYERS
        accounts_by_party: list[AccountStruct | None] = [None] * MAX_NUM_PLAYERS

        for account, options in active_account_option_pairs:
            party_index = int(account.AgentPartyData.PartyPosition)
            if 0 <= party_index < MAX_NUM_PLAYERS:
                accounts_by_party[party_index] = account
                options_by_party[party_index] = options

        return options_by_party, accounts_by_party, options_by_party[0]

    @staticmethod
    def _clear_all_flags(options_by_party: list[HeroAIOptionStruct | None] | None = None) -> None:
        party_heroes = GLOBAL_CACHE.Party.Heroes
        if options_by_party is None:
            options_by_party, _, _ = HeroAI_BaseUI._get_flag_option_pairs()

        for i in range(MAX_NUM_PLAYERS):
            options = options_by_party[i]
            if options is not None:
                options.IsFlagged = False
                options.FlagPos.x = 0.0
                options.FlagPos.y = 0.0
                options.AllFlag.x = 0.0
                options.AllFlag.y = 0.0
                options.FlagFacingAngle = 0.0

            party_heroes.UnflagHero(i)

        party_heroes.UnflagAllHeroes()
        HeroAI_BaseUI._reset_flag_capture_state()

    @staticmethod
    def _process_flagging_runtime(cached_data: CacheData) -> None:
        if not Map.IsMapReady():
            return

        is_leader = Player.GetAgentID() == GLOBAL_CACHE.Party.GetPartyLeaderID()
        if not is_leader:
            HeroAI_BaseUI._reset_flag_capture_state()
            HeroAI_BaseUI._flag_map_signature = None
            return

        options_by_party, accounts_by_party, leader_options = HeroAI_BaseUI._get_flag_option_pairs()

        if not Map.IsExplorable():
            if HeroAI_BaseUI._flag_map_signature is not None:
                HeroAI_BaseUI._clear_all_flags(options_by_party)
            HeroAI_BaseUI._flag_map_signature = None
            hero_globals.show_flagging_window = False
            return

        map_signature = (
            int(Map.GetMapID()),
            int(Map.GetRegion()[0]),
            int(Map.GetDistrict()),
            int(Map.GetLanguage()[0]),
            int(GLOBAL_CACHE.Party.GetPartyID()),
        )
        if HeroAI_BaseUI._flag_map_signature is not None and HeroAI_BaseUI._flag_map_signature != map_signature:
            HeroAI_BaseUI._clear_all_flags(options_by_party)
            options_by_party, accounts_by_party, leader_options = HeroAI_BaseUI._get_flag_option_pairs()
        HeroAI_BaseUI._flag_map_signature = map_signature

        if HeroAI_BaseUI.capture_hero_flag:
            x, y, _ = Overlay().GetMouseWorldPos()
            if HeroAI_BaseUI.capture_flag_all:
                DrawFlagAll(x, y)
            else:
                DrawHeroFlag(x, y)

            mouse_clicked = PyImGui.is_mouse_clicked(0)
            if mouse_clicked and HeroAI_BaseUI.one_time_set_flag:
                HeroAI_BaseUI.one_time_set_flag = False
                return

            if mouse_clicked:
                capture_index = HeroAI_BaseUI.capture_hero_index
                hero_count = GLOBAL_CACHE.Party.GetHeroCount()

                if 0 < capture_index <= hero_count and not HeroAI_BaseUI.capture_flag_all:
                    agent_id = GLOBAL_CACHE.Party.Heroes.GetHeroAgentIDByPartyPosition(capture_index)
                    GLOBAL_CACHE.Party.Heroes.FlagHero(agent_id, x, y)
                    HeroAI_BaseUI.one_time_set_flag = True
                else:
                    if capture_index == 0:
                        hero_ai_index = 0
                        GLOBAL_CACHE.Party.Heroes.FlagAllHeroes(x, y)
                    else:
                        hero_ai_index = capture_index - hero_count

                    options = options_by_party[hero_ai_index] if 0 <= hero_ai_index < MAX_NUM_PLAYERS else None
                    if options is not None:
                        if capture_index == 0:
                            options.AllFlag.x = x
                            options.AllFlag.y = y
                        else:
                            options.FlagPos.x = x
                            options.FlagPos.y = y
                        options.IsFlagged = True
                        options.FlagFacingAngle = Agent.GetRotationAngle(GLOBAL_CACHE.Party.GetPartyLeaderID())
                    HeroAI_BaseUI.one_time_set_flag = True

                HeroAI_BaseUI.capture_flag_all = False
                HeroAI_BaseUI.capture_hero_flag = False
                HeroAI_BaseUI.one_time_set_flag = False
                hero_globals.capture_mouse_timer.Stop()

        if leader_options and leader_options.IsFlagged:
            DrawFlagAll(leader_options.AllFlag.x, leader_options.AllFlag.y)

        for i in range(1, MAX_NUM_PLAYERS):
            options = options_by_party[i]
            account = accounts_by_party[i]
            if options is None or not options.IsFlagged or account is None:
                continue
            DrawHeroFlag(options.FlagPos.x, options.FlagPos.y)

        if hero_globals.show_broadcast_follow_positions or hero_globals.show_broadcast_follow_threshold_rings:
            segments = 24
            Overlay().BeginDraw()
            for i in range(1, MAX_NUM_PLAYERS):
                options = options_by_party[i]
                account = accounts_by_party[i]
                if options is None or account is None or not account.IsSlotActive:
                    continue

                fx = float(options.FollowPos.x)
                fy = float(options.FollowPos.y)
                if abs(fx) < 0.001 and abs(fy) < 0.001:
                    continue

                fz = Overlay().FindZ(fx, fy, 0)
                if hero_globals.show_broadcast_follow_positions:
                    Overlay().DrawPoly3D(
                        fx, fy, fz,
                        radius=Range.Touch.value / 3,
                        color=Utils.RGBToColor(0, 255, 255, 140),
                        numsegments=segments,
                        thickness=2.0,
                    )
                    Overlay().DrawText3D(
                        fx, fy, fz - 110,
                        f"F{i}",
                        color=Utils.RGBToColor(0, 255, 255, 220),
                        autoZ=False,
                        centered=True,
                        scale=1.8,
                    )
                if hero_globals.show_broadcast_follow_threshold_rings:
                    thr = max(0.0, float(getattr(options, "FollowMoveThreshold", 0.0)))
                    if thr > 0.0:
                        Overlay().DrawPoly3D(
                            fx, fy, fz,
                            radius=thr,
                            color=Utils.RGBToColor(255, 215, 0, 110),
                            numsegments=max(24, segments),
                            thickness=2.0,
                        )
            Overlay().EndDraw()

        if HeroAI_BaseUI.ClearFlags:
            HeroAI_BaseUI._clear_all_flags(options_by_party)

    @staticmethod
    def DrawPanelButtons(identifier: str, source_game_option: HeroAIOptionStruct, set_global: bool = False):
        style = ImGui.get_style()

        def set_global_option(game_option: HeroAIOptionStruct, option_name: str = "", skill_index: int = -1):
            cached_data: CacheData = CacheData()
            accounts = cached_data.party.accounts.values()

            if not accounts:
                ConsoleLog("HeroAI", "No accounts found in shared memory.")
                return

            for account in accounts:
                if not account or not account.IsSlotActive or account.IsHero or account.AgentPartyData.PartyID != GLOBAL_CACHE.Party.GetPartyID():
                    continue

                account_options = GLOBAL_CACHE.ShMem.GetHeroAIOptionsFromEmail(account.AccountEmail)
                if not account_options:
                    continue

                match option_name:
                    case "Following" | "Avoidance" | "Looting" | "Targeting" | "Combat":
                        value = getattr(game_option, option_name)
                        ConsoleLog("HeroAI", f"Setting {option_name} to {value} for account {account.AccountEmail}")
                        setattr(account_options, option_name, value)
                    case "Skills":
                        if 0 <= skill_index < NUMBER_OF_SKILLS:
                            ConsoleLog("HeroAI", f"Setting Skills[{skill_index}] to {game_option.Skills[skill_index]} for account {account.AccountEmail}")
                            account_options.Skills[skill_index] = game_option.Skills[skill_index]

        avail_x, _avail_y = PyImGui.get_content_region_avail()
        table_width = avail_x
        btn_size = (table_width / 5) - 4
        skill_size = (table_width / NUMBER_OF_SKILLS) - 4

        style.ItemSpacing.push_style_var(0, 0)
        style.CellPadding.push_style_var(2, 2)

        if PyImGui.begin_table(f"GameOptionTable##{identifier}", 5, 0, table_width, btn_size + 2):
            PyImGui.table_next_row()
            PyImGui.table_next_column()
            following = ImGui.toggle_button(IconsFontAwesome5.ICON_RUNNING + "##Following" + identifier, source_game_option.Following, btn_size, btn_size)
            if following != source_game_option.Following:
                source_game_option.Following = following
                if set_global:
                    set_global_option(source_game_option, "Following")
            ImGui.show_tooltip("Following")

            PyImGui.table_next_column()
            avoidance = ImGui.toggle_button(IconsFontAwesome5.ICON_PODCAST + "##Avoidance" + identifier, source_game_option.Avoidance, btn_size, btn_size)
            if avoidance != source_game_option.Avoidance:
                source_game_option.Avoidance = avoidance
                if set_global:
                    set_global_option(source_game_option, "Avoidance")
            ImGui.show_tooltip("Avoidance")

            PyImGui.table_next_column()
            looting = ImGui.toggle_button(IconsFontAwesome5.ICON_COINS + "##Looting" + identifier, source_game_option.Looting, btn_size, btn_size)
            if looting != source_game_option.Looting:
                source_game_option.Looting = looting
                if set_global:
                    set_global_option(source_game_option, "Looting")
            ImGui.show_tooltip("Looting")

            PyImGui.table_next_column()
            targeting = ImGui.toggle_button(IconsFontAwesome5.ICON_BULLSEYE + "##Targeting" + identifier, source_game_option.Targeting, btn_size, btn_size)
            if targeting != source_game_option.Targeting:
                source_game_option.Targeting = targeting
                if set_global:
                    ConsoleLog("HeroAI", f"Setting Targeting to {targeting} for all heroes in party.")
                    set_global_option(source_game_option, "Targeting")
            ImGui.show_tooltip("Targeting")

            PyImGui.table_next_column()
            combat = ImGui.toggle_button(IconsFontAwesome5.ICON_SKULL_CROSSBONES + "##Combat" + identifier, source_game_option.Combat, btn_size, btn_size)
            if combat != source_game_option.Combat:
                source_game_option.Combat = combat
                if set_global:
                    set_global_option(source_game_option, "Combat")
            ImGui.show_tooltip("Combat")
            PyImGui.end_table()

        style.ButtonPadding.push_style_var(5 if style.Theme not in ImGui.Textured_Themes else 0, 3 if style.Theme not in ImGui.Textured_Themes else 2)
        if PyImGui.begin_table("SkillsTable", NUMBER_OF_SKILLS, 0, table_width, (btn_size / 3)):
            PyImGui.table_next_row()
            for i in range(NUMBER_OF_SKILLS):
                PyImGui.table_next_column()
                skill_active = ImGui.toggle_button(f"{i + 1}##Skill{i}" + identifier, source_game_option.Skills[i], skill_size, skill_size)
                if skill_active != source_game_option.Skills[i]:
                    source_game_option.Skills[i] = skill_active
                    if set_global:
                        set_global_option(source_game_option, "Skills", i)
                ImGui.show_tooltip(f"Skill {i + 1}")
            PyImGui.end_table()
        style.ButtonPadding.pop_style_var()

        style.ItemSpacing.pop_style_var()
        style.CellPadding.pop_style_var()

    @staticmethod
    def DrawButtonBar(cached_data: CacheData):
        btn_size = 23
        ImGui.push_font("Regular", 10)
        if PyImGui.begin_child("ControlPanelChild", (215, 0), False, PyImGui.WindowFlags.AlwaysAutoResize):
            if PyImGui.begin_table("MessagingTable", 5):
                PyImGui.table_next_row()
                PyImGui.table_next_column()
                if ImGui.colored_button(
                    f"{IconsFontAwesome5.ICON_SKULL}##commands_resign",
                    HeroAI_BaseUI.ButtonColors["Resign"].button_color,
                    HeroAI_BaseUI.ButtonColors["Resign"].hovered_color,
                    HeroAI_BaseUI.ButtonColors["Resign"].active_color,
                    btn_size,
                    btn_size,
                ):
                    accounts = cached_data.party.accounts.values()
                    sender_email = cached_data.account_email
                    for account in accounts:
                        ConsoleLog("Messaging", "Resigning account: " + account.AccountEmail)
                        GLOBAL_CACHE.ShMem.SendMessage(sender_email, account.AccountEmail, SharedCommandType.Resign, (0, 0, 0, 0))
                ImGui.pop_font()
                ImGui.show_tooltip("Resign Party")
                ImGui.push_font("Regular", 10)
                PyImGui.same_line(0, -1)
                PyImGui.text("|")
                PyImGui.same_line(0, -1)

                if PyImGui.button(f"{IconsFontAwesome5.ICON_COMPRESS_ARROWS_ALT}##commands_pixelstack", btn_size, btn_size):
                    self_account = GLOBAL_CACHE.ShMem.GetAccountDataFromEmail(cached_data.account_email)
                    if not self_account:
                        return
                    accounts = cached_data.party.accounts.values()
                    sender_email = cached_data.account_email
                    for account in accounts:
                        if self_account.AccountEmail == account.AccountEmail:
                            continue
                        ConsoleLog("Messaging", "Pixelstacking account: " + account.AccountEmail)
                        GLOBAL_CACHE.ShMem.SendMessage(sender_email, account.AccountEmail, SharedCommandType.PixelStack, (self_account.AgentData.Pos.x, self_account.AgentData.Pos.y, 0, 0))
                ImGui.pop_font()
                ImGui.show_tooltip("Pixel Stack (Carto Helper)")
                ImGui.push_font("Regular", 10)
                PyImGui.same_line(0, -1)

                if PyImGui.button(f"{IconsFontAwesome5.ICON_HAND_POINT_RIGHT}##commands_InteractTarget", btn_size, btn_size):
                    target = Player.GetTargetID()
                    if target == 0:
                        ConsoleLog("Messaging", "No target to interact with.")
                        return
                    self_account = GLOBAL_CACHE.ShMem.GetAccountDataFromEmail(cached_data.account_email)
                    if not self_account:
                        return
                    accounts = cached_data.party.accounts.values()
                    sender_email = cached_data.account_email
                    for account in accounts:
                        if self_account.AccountEmail == account.AccountEmail:
                            continue
                        ConsoleLog("Messaging", f"Ordering {account.AccountEmail} to interact with target: {target}")
                        GLOBAL_CACHE.ShMem.SendMessage(sender_email, account.AccountEmail, SharedCommandType.InteractWithTarget, (target, 0, 0, 0))
                ImGui.pop_font()
                ImGui.show_tooltip("Interact with Target")
                ImGui.push_font("Regular", 10)
                PyImGui.same_line(0, -1)

                if PyImGui.button(f"{IconsFontAwesome5.ICON_COMMENT_DOTS}##commands_takedialog", btn_size, btn_size):
                    target = Player.GetTargetID()
                    if target == 0:
                        ConsoleLog("Messaging", "No target to interact with.")
                        return
                    if not UIManager.IsNPCDialogVisible():
                        ConsoleLog("Messaging", "No dialog is open.")
                        return
                    self_account = GLOBAL_CACHE.ShMem.GetAccountDataFromEmail(cached_data.account_email)
                    if not self_account:
                        return
                    accounts = cached_data.party.accounts.values()
                    sender_email = cached_data.account_email
                    for account in accounts:
                        if self_account.AccountEmail == account.AccountEmail:
                            continue
                        ConsoleLog("Messaging", f"Ordering {account.AccountEmail} to interact with target: {target}")
                        GLOBAL_CACHE.ShMem.SendMessage(sender_email, account.AccountEmail, SharedCommandType.TakeDialogWithTarget, (target, 0, 0, 0))
                ImGui.pop_font()
                ImGui.show_tooltip("Get Dialog")
                ImGui.push_font("Regular", 10)
                PyImGui.same_line(0, -1)

                if PyImGui.button(f"{IconsFontAwesome5.ICON_KEY}##unlock_chest", btn_size, btn_size):
                    sender_email = Player.GetAccountEmail()
                    target_id = Player.GetTargetID()
                    account_data = GLOBAL_CACHE.ShMem.GetAccountDataFromEmail(sender_email)
                    if account_data is None:
                        return

                    party_id = account_data.AgentPartyData.PartyID
                    map_id = account_data.AgentData.Map.MapID
                    map_region = account_data.AgentData.Map.Region
                    map_district = account_data.AgentData.Map.District
                    map_language = account_data.AgentData.Map.Language

                    def on_same_map_and_party(account: AccountStruct) -> bool:
                        return (
                            account.AgentPartyData.PartyID == party_id
                            and account.AgentData.Map.MapID == map_id
                            and account.AgentData.Map.Region == map_region
                            and account.AgentData.Map.District == map_district
                            and account.AgentData.Map.Language == map_language
                        )

                    all_accounts = [account for account in cached_data.party.accounts.values()]
                    lowest_party_index_account = min(all_accounts, key=lambda account: account.AgentPartyData.PartyPosition, default=None)
                    if lowest_party_index_account is None:
                        return

                    GLOBAL_CACHE.ShMem.SendMessage(sender_email, lowest_party_index_account.AccountEmail, SharedCommandType.OpenChest, (target_id, 1, 0, 0))
                ImGui.pop_font()
                ImGui.show_tooltip("Open Chest")
                ImGui.push_font("Regular", 10)
                PyImGui.same_line(0, -1)

                if PyImGui.button(f"{IconsFontAwesome5.ICON_COINS}##pickup_loot", btn_size, btn_size):
                    sender_email = Player.GetAccountEmail()
                    accounts = GLOBAL_CACHE.ShMem.GetAllAccountData()
                    for account in accounts:
                        GLOBAL_CACHE.ShMem.SendMessage(sender_email, account.AccountEmail, SharedCommandType.PickUpLoot, (0, 0, 0, 0))
                ImGui.pop_font()
                ImGui.show_tooltip("Pick up Loot")
                ImGui.push_font("Regular", 10)
                PyImGui.end_table()

            PyImGui.separator()
            if PyImGui.begin_table("MessagingTable_Row2", 1):
                PyImGui.table_next_row()
                PyImGui.table_next_column()

                from HeroAI import ui

                v = ui.is_base_configure_consumables_window_open()
                new_v = ImGui.toggle_button(
                    label=f"{IconsFontAwesome5.ICON_CANDY_CANE}##consumables",
                    v=v,
                    width=btn_size,
                    height=btn_size,
                )
                if new_v != v:
                    ui.show_base_configure_consumables_window()
                ImGui.pop_font()
                ImGui.show_tooltip("Consumables")
                ImGui.push_font("Regular", 10)
                PyImGui.same_line(0, -1)

                fv = HeroAI_BaseUI.show_follow_formations_quick_window
                new_fv = ImGui.toggle_button(
                    label=f"{IconsFontAwesome5.ICON_PERSON_WALKING_ARROW_RIGHT}##follow_formations_quick",
                    v=fv,
                    width=btn_size,
                    height=btn_size,
                )
                if new_fv != fv:
                    HeroAI_BaseUI.show_follow_formations_quick_window = new_fv
                ImGui.pop_font()
                ImGui.show_tooltip("Follow Formations")
                ImGui.push_font("Regular", 10)
                PyImGui.same_line(0, -1)

                fv = ui.is_party_window_open()
                new_fv = ImGui.toggle_button(
                    label=f"{IconsFontAwesome5.ICON_PEOPLE_GROUP}##open_party_window",
                    v=fv,
                    width=btn_size,
                    height=btn_size,
                )
                if new_fv != fv:
                    Keystroke.PressAndRelease(Key.P.value)
                ImGui.pop_font()
                ImGui.show_tooltip("Open Party Window")
                ImGui.push_font("Regular", 10)
                PyImGui.same_line(0, -1)

                bv = HeroAI_BaseUI.show_build_match_window
                new_bv = ImGui.toggle_button(
                    label="Builds##open_build_matches",
                    v=bv,
                    width=60,
                    height=btn_size,
                )
                if new_bv != bv:
                    HeroAI_BaseUI.show_build_match_window = new_bv
                ImGui.show_tooltip("Show each party account's build resolved from shared-memory skillbars")
                PyImGui.end_table()
            PyImGui.end_child()
        ImGui.pop_font()

    @staticmethod
    def _get_build_registry():
        if HeroAI_BaseUI._build_registry is None:
            from Py4GWCoreLib.BuildMgr import BuildRegistry

            HeroAI_BaseUI._build_registry = BuildRegistry(default_fallback_name="HeroAI")
        return HeroAI_BaseUI._build_registry

    @staticmethod
    def _profession_label(profession_value: int) -> str:
        from Py4GWCoreLib import Profession

        if profession_value == 0:
            return ""
        try:
            return Profession(int(profession_value)).name
        except Exception:
            return str(profession_value)

    @staticmethod
    def _profession_color(profession_value: int) -> Color:
        palette_name = HeroAI_BaseUI._profession_palette_names.get(int(profession_value))
        if not palette_name:
            return ColorPalette.GetColor("white")
        return ColorPalette.GetColor(palette_name)

    @staticmethod
    def _get_build_signature(account) -> tuple[int, int, tuple[int, ...]]:
        primary_value = int(account.AgentData.Profession[0])
        secondary_value = int(account.AgentData.Profession[1])
        skill_ids = tuple(int(skill.Id) for skill in account.AgentData.Skillbar.Skills if int(skill.Id) != 0)
        return primary_value, secondary_value, skill_ids

    @staticmethod
    def _build_match_row_from_account(account, registry, fallback_name: str):
        from Py4GWCoreLib import Profession

        primary_value, secondary_value, skill_ids = HeroAI_BaseUI._get_build_signature(account)
        primary_label = HeroAI_BaseUI._profession_label(primary_value)
        secondary_label = HeroAI_BaseUI._profession_label(secondary_value)
        profession_label = f"{primary_label}{('/' + secondary_label) if secondary_label else ''}"

        primary_prof = Profession(primary_value)
        secondary_prof = Profession(secondary_value)
        best_score = -1
        for build in registry._iter_matchable_builds(match_only=True):
            score = build.ScoreMatch(
                current_primary=primary_prof,
                current_secondary=secondary_prof,
                current_skills=list(skill_ids),
            )
            if score > best_score:
                best_score = score

        resolved_build = registry.ResolveBuild(
            current_primary=primary_prof,
            current_secondary=secondary_prof,
            current_skills=list(skill_ids),
            fallback_name=fallback_name,
        )

        if resolved_build is not None and best_score > 0 and not resolved_build.is_fallback_candidate:
            build_name = str(getattr(resolved_build, "build_name", "") or resolved_build.__class__.__name__)
            source_label = "Matched"
        else:
            build_name = fallback_name
            source_label = "Fallback"
        return (
            int(account.AgentPartyData.PartyPosition),
            str(account.AgentData.CharacterName),
            primary_value,
            secondary_value,
            profession_label,
            build_name,
            source_label,
        )

    @staticmethod
    def _refresh_build_match_rows(cached_data: CacheData) -> None:
        if not HeroAI_BaseUI._build_match_timer.IsExpired() and HeroAI_BaseUI._build_match_rows:
            return

        rows: list[tuple[int, str, int, int, str, str, str]] = []
        registry = HeroAI_BaseUI._get_build_registry()
        sorted_accounts = sorted(cached_data.party.accounts.values(), key=lambda acc: acc.AgentPartyData.PartyPosition)
        active_slot_keys: set[int] = set()
        fallback_name = "HeroAI"

        for account in sorted_accounts:
            if not account or not account.IsSlotActive:
                continue
            if account.AgentPartyData.PartyID != GLOBAL_CACHE.Party.GetPartyID():
                continue
            if account.IsPet or account.IsNPC:
                continue

            slot_key = int(account.AgentPartyData.PartyPosition)
            active_slot_keys.add(slot_key)
            signature = HeroAI_BaseUI._get_build_signature(account)
            cached_entry = HeroAI_BaseUI._build_match_signature_cache.get(slot_key)

            if cached_entry is not None and cached_entry[0] == signature:
                row = cached_entry[1]
            else:
                row = HeroAI_BaseUI._build_match_row_from_account(account, registry, fallback_name)
                HeroAI_BaseUI._build_match_signature_cache[slot_key] = (signature, row)

            rows.append(row)

        stale_slot_keys = [slot_key for slot_key in HeroAI_BaseUI._build_match_signature_cache if slot_key not in active_slot_keys]
        for stale_slot_key in stale_slot_keys:
            HeroAI_BaseUI._build_match_signature_cache.pop(stale_slot_key, None)

        HeroAI_BaseUI._build_match_rows = rows
        HeroAI_BaseUI._build_match_timer.Reset()

    @staticmethod
    def _dump_build_match_debug(cached_data: CacheData) -> None:
        from Py4GWCoreLib import Profession

        registry = HeroAI_BaseUI._get_build_registry()
        sorted_accounts = sorted(cached_data.party.accounts.values(), key=lambda acc: acc.AgentPartyData.PartyPosition)

        ConsoleLog("HeroAI", "=== Build Match Debug Dump ===")
        build_types = registry.GetBuildTypes()
        ConsoleLog("HeroAI", f"[BuildDebug] Scanned build type count={len(build_types)}")
        for build_type in build_types:
            try:
                build = registry._instantiate_build(build_type)
                if build is None:
                    ConsoleLog("HeroAI", f"[BuildDebug] Instantiate returned None for class={build_type.__name__}")
                    continue

                ConsoleLog(
                    "HeroAI",
                    f"[BuildDebug] Instantiated class={build_type.__name__} "
                    f"build_name={getattr(build, 'build_name', '')!r} "
                    f"template_only={getattr(build, 'is_template_only', False)} "
                    f"fallback={getattr(build, 'is_fallback_candidate', False)} "
                    f"fixed={getattr(build, 'IsFixedBuild', False)} "
                    f"compatible={getattr(build, 'is_combat_automator_compatible', True)}",
                )
            except Exception as exc:
                ConsoleLog("HeroAI", f"[BuildDebug] Instantiate exception for class={build_type.__name__}: {exc!r}")

        for account in sorted_accounts:
            if not account or not account.IsSlotActive:
                continue
            if account.AgentPartyData.PartyID != GLOBAL_CACHE.Party.GetPartyID():
                continue
            if account.IsPet or account.IsNPC:
                continue

            primary_value = int(account.AgentData.Profession[0])
            secondary_value = int(account.AgentData.Profession[1])
            primary_prof = Profession(primary_value)
            secondary_prof = Profession(secondary_value)
            skill_ids = [int(skill.Id) for skill in account.AgentData.Skillbar.Skills if int(skill.Id) != 0]
            fallback_name = "HeroAI"
            best_score = -1
            for build in registry._iter_matchable_builds(match_only=True):
                score = build.ScoreMatch(
                    current_primary=primary_prof,
                    current_secondary=secondary_prof,
                    current_skills=skill_ids,
                )
                if score > best_score:
                    best_score = score

            resolved_build = registry.ResolveBuild(
                current_primary=primary_prof,
                current_secondary=secondary_prof,
                current_skills=skill_ids,
                fallback_name=fallback_name,
            )

            resolved_class = resolved_build.__class__.__name__ if resolved_build is not None else "None"
            if resolved_build is not None and best_score > 0 and not resolved_build.is_fallback_candidate:
                resolved_name = str(getattr(resolved_build, "build_name", "") or resolved_class)
                resolved_source = "Matched"
            else:
                resolved_name = fallback_name
                resolved_source = "Fallback"

            ConsoleLog(
                "HeroAI",
                f"[BuildDebug] Pos={int(account.AgentPartyData.PartyPosition) + 1} "
                f"Name={account.AgentData.CharacterName} "
                f"Prof={primary_prof.name}/{secondary_prof.name} "
                f"Skills={skill_ids}",
            )
            ConsoleLog("HeroAI", f"[BuildDebug] Resolved class={resolved_class} build_name={resolved_name!r} source={resolved_source}")

            all_matchables = registry._iter_matchable_builds()
            ConsoleLog("HeroAI", f"[BuildDebug] Matchable build count={len(all_matchables)}")

            scored_candidates: list[tuple[int, str, str]] = []
            for build in all_matchables:
                score = build.ScoreMatch(
                    current_primary=primary_prof,
                    current_secondary=secondary_prof,
                    current_skills=skill_ids,
                )
                ConsoleLog(
                    "HeroAI",
                    f"[BuildDebug] Build class={build.__class__.__name__} "
                    f"build_name={getattr(build, 'build_name', '')!r} "
                    f"required_primary={getattr(build.required_primary, 'name', build.required_primary)} "
                    f"required_secondary={getattr(build.required_secondary, 'name', build.required_secondary)} "
                    f"required_skills={list(getattr(build, 'required_skills', []))} "
                    f"optional_skills={list(getattr(build, 'optional_skills', []))} "
                    f"score={score}",
                )
                if score >= 0:
                    scored_candidates.append((score, build.__class__.__name__, str(getattr(build, "build_name", ""))))

            scored_candidates.sort(key=lambda item: item[0], reverse=True)
            if not scored_candidates:
                ConsoleLog("HeroAI", "[BuildDebug] No matchable build qualified.")
            else:
                for score, class_name, build_name in scored_candidates:
                    ConsoleLog("HeroAI", f"[BuildDebug] Candidate score={score} class={class_name} build_name={build_name!r}")

            fallback_candidates = registry._iter_fallback_builds()
            for build in fallback_candidates:
                ConsoleLog("HeroAI", f"[BuildDebug] Fallback class={build.__class__.__name__} build_name={getattr(build, 'build_name', '')!r}")
        ConsoleLog("HeroAI", "=== End Build Match Debug Dump ===")

    @staticmethod
    def _get_supported_build_groups(registry) -> list[tuple[str, list[tuple[str, list[str]]]]]:
        grouped_builds: dict[str, dict[str, list[str]]] = {}

        for build in registry._iter_matchable_builds(match_only=True):
            module_parts = build.__class__.__module__.split(".")
            profession_group = module_parts[2] if len(module_parts) > 2 else "Other"
            combo_group = module_parts[3] if len(module_parts) > 3 else "General"
            build_name = str(getattr(build, "build_name", "") or build.__class__.__name__)

            profession_entry = grouped_builds.setdefault(profession_group, {})
            combo_entry = profession_entry.setdefault(combo_group, [])
            if build_name not in combo_entry:
                combo_entry.append(build_name)

        supported_groups: list[tuple[str, list[tuple[str, list[str]]]]] = []
        for profession_group in sorted(grouped_builds):
            combo_groups: list[tuple[str, list[str]]] = []
            for combo_group in sorted(grouped_builds[profession_group]):
                combo_groups.append((combo_group, sorted(grouped_builds[profession_group][combo_group])))
            supported_groups.append((profession_group, combo_groups))
        return supported_groups

    @staticmethod
    def _draw_build_matches_tab() -> None:
        if not HeroAI_BaseUI._build_match_rows:
            PyImGui.text("No party accounts available.")
            return

        for party_pos, character_name, primary_value, secondary_value, profession_label, build_name, source_label in HeroAI_BaseUI._build_match_rows:
            PyImGui.text(f"{party_pos + 1}. {character_name}")
            if profession_label:
                PyImGui.same_line(220, 0)
                primary_prof = HeroAI_BaseUI._profession_label(primary_value)
                secondary_prof = HeroAI_BaseUI._profession_label(secondary_value)
                if secondary_prof:
                    PyImGui.text_colored(primary_prof, HeroAI_BaseUI._profession_color(primary_value).to_tuple_normalized())
                    PyImGui.same_line(0, 0)
                    PyImGui.text("/")
                    PyImGui.same_line(0, 0)
                    PyImGui.text_colored(secondary_prof, HeroAI_BaseUI._profession_color(secondary_value).to_tuple_normalized())
                else:
                    PyImGui.text_colored(primary_prof, HeroAI_BaseUI._profession_color(primary_value).to_tuple_normalized())
            build_color = ColorPalette.GetColor("dodger_blue") if source_label == "Matched" else ColorPalette.GetColor("gw_gold")
            PyImGui.text("Build:")
            PyImGui.same_line(220, 0)
            PyImGui.text_colored(build_name, build_color.to_tuple_normalized())
            PyImGui.same_line(0, 14)
            status_color = ColorPalette.GetColor("dodger_blue") if source_label == "Matched" else ColorPalette.GetColor("gw_gold")
            PyImGui.text_colored(source_label, status_color.to_tuple_normalized())
            PyImGui.separator()

    @staticmethod
    def _build_browser_catalog(registry) -> list[dict[str, object]]:
        grouped_builds: dict[str, dict[str, list[dict[str, object]]]] = {}
        build_catalog: dict[str, dict[str, object]] = {}

        for build in registry._iter_matchable_builds(match_only=True):
            module_parts = build.__class__.__module__.split(".")
            profession_group = module_parts[2] if len(module_parts) > 2 else "Other"
            combo_group = module_parts[3] if len(module_parts) > 3 else "General"
            build_name = str(getattr(build, "build_name", "") or build.__class__.__name__)
            build_key = f"{build.__class__.__module__}.{build.__class__.__name__}"
            required_skills = [int(skill_id) for skill_id in getattr(build, "required_skills", []) if int(skill_id) != 0]
            optional_skills = [int(skill_id) for skill_id in getattr(build, "optional_skills", []) if int(skill_id) != 0]
            supported_skills = [int(skill_id) for skill_id in build.GetSupportedSkills() if int(skill_id) != 0]

            build_info = {
                "key": build_key,
                "name": build_name,
                "class_name": build.__class__.__name__,
                "template_code": str(getattr(build, "template_code", "") or ""),
                "required_primary": int(getattr(build.required_primary, "value", 0)),
                "required_secondary": int(getattr(build.required_secondary, "value", 0)),
                "required_skills": required_skills,
                "optional_skills": optional_skills,
                "supported_skills": supported_skills,
                "profession_group": profession_group,
                "combo_group": combo_group,
            }
            build_catalog[build_key] = build_info

            profession_entry = grouped_builds.setdefault(profession_group, {})
            combo_entry = profession_entry.setdefault(combo_group, [])
            combo_entry.append(build_info)

        if not HeroAI_BaseUI._supported_build_selected_key and build_catalog:
            HeroAI_BaseUI._supported_build_selected_key = next(iter(build_catalog.keys()))
        elif HeroAI_BaseUI._supported_build_selected_key not in build_catalog:
            HeroAI_BaseUI._supported_build_selected_key = next(iter(build_catalog.keys()), "")

        HeroAI_BaseUI._supported_builds_cache = build_catalog

        supported_groups: list[dict[str, object]] = []
        for profession_group in sorted(grouped_builds):
            combo_groups: list[dict[str, object]] = []
            profession_count = 0
            for combo_group in sorted(grouped_builds[profession_group]):
                builds = sorted(grouped_builds[profession_group][combo_group], key=lambda item: str(item["name"]))
                profession_count += len(builds)
                combo_groups.append({
                    "name": combo_group,
                    "count": len(builds),
                    "builds": builds,
                })
            supported_groups.append({
                "name": profession_group,
                "count": profession_count,
                "combo_groups": combo_groups,
            })
        return supported_groups

    @staticmethod
    def _copy_build_template_to_clipboard(template_code: str) -> None:
        if template_code:
            PyImGui.set_clipboard_text(template_code)

    @staticmethod
    def _get_selected_supported_skill(skill_ids: list[int]) -> int:
        normalized_skill_ids = [int(skill_id) for skill_id in skill_ids if int(skill_id) != 0]
        if not normalized_skill_ids:
            HeroAI_BaseUI._supported_build_selected_skill_id = 0
            return 0
        if HeroAI_BaseUI._supported_build_selected_skill_id not in normalized_skill_ids:
            HeroAI_BaseUI._supported_build_selected_skill_id = normalized_skill_ids[0]
        return HeroAI_BaseUI._supported_build_selected_skill_id

    @staticmethod
    def _draw_skill_info_card(skill_id: int, compact: bool = False, tooltip: bool = False) -> None:
        if int(skill_id) == 0:
            return

        texture_path = GLOBAL_CACHE.Skill.ExtraData.GetTexturePath(skill_id)
        skill_name = GLOBAL_CACHE.Skill.GetNameFromWiki(skill_id) or GLOBAL_CACHE.Skill.GetName(skill_id) or str(skill_id)
        suffix = _get_skill_name_suffix(skill_id)
        if suffix:
            skill_name = f"{skill_name} {suffix}"
        profession_value, profession_name = GLOBAL_CACHE.Skill.GetProfession(skill_id)
        _skill_type_value, skill_type_name = GLOBAL_CACHE.Skill.GetType(skill_id)
        energy_cost = int(GLOBAL_CACHE.Skill.Data.GetEnergyCost(skill_id))
        adrenaline_cost = int(GLOBAL_CACHE.Skill.Data.GetAdrenaline(skill_id))
        health_cost = int(GLOBAL_CACHE.Skill.Data.GetHealthCost(skill_id))
        overcast_cost = int(GLOBAL_CACHE.Skill.Data.GetOvercast(skill_id))
        activation_time = float(GLOBAL_CACHE.Skill.Data.GetActivation(skill_id))
        aftercast_time = float(GLOBAL_CACHE.Skill.Data.GetAftercast(skill_id))
        recharge_time = int(GLOBAL_CACHE.Skill.Data.GetRecharge(skill_id))
        is_elite = bool(GLOBAL_CACHE.Skill.Flags.IsElite(skill_id))
        campaign_name = GLOBAL_CACHE.Skill.GetCampaign(skill_id)[1]
        concise_description = GLOBAL_CACHE.Skill.GetConciseDescription(skill_id) or GLOBAL_CACHE.Skill.GetDescription(skill_id) or ""

        accent = HeroAI_BaseUI._profession_color(int(profession_value))
        title_color = ColorPalette.GetColor("gw_gold") if is_elite else ColorPalette.GetColor("white")
        icon_size = 56 if compact else 72
        wrap_width = 360 if compact or tooltip else 520

        PyImGui.begin_group()
        ImGui.DrawTexture(texture_path, icon_size, icon_size)
        PyImGui.same_line(0, 12)
        PyImGui.begin_group()
        ImGui.push_font("Bold", 16 if compact else 18)
        PyImGui.text_colored(skill_name, title_color.to_tuple_normalized())
        ImGui.pop_font()
        PyImGui.text_colored(f"{profession_name} | {skill_type_name}", accent.to_tuple_normalized())
        PyImGui.text_colored(campaign_name, ColorPalette.GetColor("gray").to_tuple_normalized())

        meta_parts: list[str] = []
        if health_cost > 0:
            meta_parts.append(f"HP {health_cost}%")
        if overcast_cost > 0:
            meta_parts.append(f"OC {overcast_cost}")
        if energy_cost > 0:
            meta_parts.append(f"E {energy_cost}")
        if adrenaline_cost > 0:
            meta_parts.append(f"A {adrenaline_cost}")
        if activation_time > 0:
            meta_parts.append(f"Cast {activation_time:.2f}s")
        if aftercast_time > 0 and not compact:
            meta_parts.append(f"After {aftercast_time:.2f}s")
        if recharge_time > 0:
            meta_parts.append(f"Recharge {recharge_time}s")
        if not meta_parts:
            meta_parts.append(skill_type_name)
        PyImGui.text(" | ".join(meta_parts))
        PyImGui.push_text_wrap_pos(wrap_width)
        PyImGui.text_wrapped(concise_description)
        PyImGui.pop_text_wrap_pos()
        PyImGui.end_group()
        PyImGui.end_group()

    @staticmethod
    def _draw_skill_icon_grid(skill_ids: list[int], section_name: str) -> None:
        PyImGui.text(f"{section_name} ({len(skill_ids)})")
        if not skill_ids:
            PyImGui.text_colored("None", ColorPalette.GetColor("gray").to_tuple_normalized())
            return

        cards_per_row = 8
        for index, skill_id in enumerate(skill_ids):
            is_selected = HeroAI_BaseUI._supported_build_selected_skill_id == int(skill_id)
            if ImGui.image_toggle_button(f"{section_name}_{index}_{skill_id}", GLOBAL_CACHE.Skill.ExtraData.GetTexturePath(skill_id), is_selected, 42, 42):
                HeroAI_BaseUI._supported_build_selected_skill_id = int(skill_id)

            if PyImGui.is_item_hovered():
                if PyImGui.begin_tooltip():
                    HeroAI_BaseUI._draw_skill_info_card(int(skill_id), compact=True, tooltip=True)
                    PyImGui.end_tooltip()

            if (index + 1) % cards_per_row != 0 and index + 1 < len(skill_ids):
                PyImGui.same_line(0, 8)

    @staticmethod
    def _draw_supported_build_details(selected_build: dict[str, object] | None) -> None:
        if not selected_build:
            PyImGui.text("Select a build from the tree to inspect its details.")
            return

        build_name = str(selected_build["name"])
        build_key = str(selected_build["key"])
        class_name = str(selected_build["class_name"])
        template_code = str(selected_build["template_code"])
        required_primary = int(selected_build["required_primary"])
        required_secondary = int(selected_build["required_secondary"])
        required_skills = list(selected_build["required_skills"])
        optional_skills = list(selected_build["optional_skills"])
        supported_skills = list(selected_build["supported_skills"])
        all_detail_skills = list(dict.fromkeys([*required_skills, *optional_skills, *supported_skills]))

        if HeroAI_BaseUI._supported_build_last_detail_key != build_key:
            HeroAI_BaseUI._supported_build_last_detail_key = build_key
            HeroAI_BaseUI._supported_build_selected_skill_id = int(all_detail_skills[0]) if all_detail_skills else 0

        selected_skill_id = HeroAI_BaseUI._get_selected_supported_skill(all_detail_skills)

        ImGui.push_font("Bold", 18)
        PyImGui.text(build_name)
        ImGui.pop_font()
        PyImGui.text_colored(class_name, ColorPalette.GetColor("gray").to_tuple_normalized())
        PyImGui.separator()

        PyImGui.text("Professions")
        primary_label = HeroAI_BaseUI._profession_label(required_primary) or "Any"
        secondary_label = HeroAI_BaseUI._profession_label(required_secondary) or "Any"
        PyImGui.text_colored(primary_label, HeroAI_BaseUI._profession_color(required_primary).to_tuple_normalized())
        PyImGui.same_line(0, 8)
        PyImGui.text("/")
        PyImGui.same_line(0, 8)
        PyImGui.text_colored(secondary_label, HeroAI_BaseUI._profession_color(required_secondary).to_tuple_normalized())
        PyImGui.separator()

        PyImGui.text("Template")
        if template_code:
            PyImGui.text_wrapped(template_code)
            if PyImGui.button("Copy Template##copy_supported_build_template"):
                HeroAI_BaseUI._copy_build_template_to_clipboard(template_code)
        else:
            PyImGui.text_colored("No template code.", ColorPalette.GetColor("gray").to_tuple_normalized())
        PyImGui.separator()

        HeroAI_BaseUI._draw_skill_icon_grid(required_skills, "Required Skills")
        PyImGui.separator()
        HeroAI_BaseUI._draw_skill_icon_grid(optional_skills, "Supported Extras")
        PyImGui.separator()
        HeroAI_BaseUI._draw_skill_icon_grid(supported_skills, "All Supported Skills")
        PyImGui.separator()
        PyImGui.text("Selected Skill")
        if PyImGui.begin_child("SupportedBuildSelectedSkillPane", (0, 220), True, PyImGui.WindowFlags.NoFlag):
            if selected_skill_id:
                HeroAI_BaseUI._draw_skill_info_card(selected_skill_id, compact=False)
            else:
                PyImGui.text("Select a skill icon to inspect it here.")
            PyImGui.end_child()

    @staticmethod
    def _draw_supported_builds_tab(registry) -> None:
        supported_groups = HeroAI_BaseUI._build_browser_catalog(registry)
        if not supported_groups:
            PyImGui.text("No supported matchable builds discovered.")
            return

        PyImGui.text("Browse supported builds and inspect what the matcher can inherit from.")
        PyImGui.separator()

        avail_x, _avail_y = PyImGui.get_content_region_avail()
        tree_width = min(320.0, max(250.0, avail_x * 0.34))
        details_width = max(260.0, avail_x - tree_width - 16.0)

        if PyImGui.begin_child("SupportedBuildTreePane", (tree_width, 0), True, PyImGui.WindowFlags.NoFlag):
            for profession_group in supported_groups:
                profession_name = str(profession_group["name"])
                profession_count = int(profession_group["count"])
                if not PyImGui.tree_node(f"{profession_name} ({profession_count})##supported_{profession_name}"):
                    continue

                for combo_group in profession_group["combo_groups"]:
                    combo_name = str(combo_group["name"])
                    combo_count = int(combo_group["count"])
                    if not PyImGui.tree_node(f"{combo_name} ({combo_count})##supported_{profession_name}_{combo_name}"):
                        continue

                    for build_info in combo_group["builds"]:
                        build_key = str(build_info["key"])
                        build_name = str(build_info["name"])
                        is_selected = HeroAI_BaseUI._supported_build_selected_key == build_key
                        if ImGui.selectable(f"{build_name}##supported_build_{build_key}", is_selected, PyImGui.SelectableFlags.NoFlag, (0, 0)):
                            HeroAI_BaseUI._supported_build_selected_key = build_key

                    PyImGui.tree_pop()

                PyImGui.tree_pop()
            PyImGui.end_child()

        PyImGui.same_line(0, 12)

        if PyImGui.begin_child("SupportedBuildDetailsPane", (details_width, 0), True, PyImGui.WindowFlags.NoFlag):
            selected_build = HeroAI_BaseUI._supported_builds_cache.get(HeroAI_BaseUI._supported_build_selected_key)
            HeroAI_BaseUI._draw_supported_build_details(selected_build)
            PyImGui.end_child()

    @staticmethod
    def _get_team_viewer_display_name(party_pos: int, character_name: str) -> str:
        if not HeroAI_BaseUI._team_viewer_anonymize:
            return character_name
        aliases = HeroAI_BaseUI._team_viewer_aliases
        if 0 <= party_pos < len(aliases):
            return aliases[party_pos]
        return character_name

    @staticmethod
    def _refresh_team_viewer_rows(cached_data: CacheData) -> None:
        if not HeroAI_BaseUI._team_viewer_timer.IsExpired() and HeroAI_BaseUI._team_viewer_rows:
            return

        from HeroAI import team_viewer_broadcast

        rows: list[tuple[int, str, str, int, int, dict, tuple[int, ...], str]] = []
        sorted_accounts = sorted(
            cached_data.party.accounts.values(),
            key=lambda acc: acc.AgentPartyData.PartyPosition,
        )
        active_emails: set[str] = set()
        seen_positions: set[int] = set()

        current_party_id = int(GLOBAL_CACHE.Party.GetPartyID() or 0)
        try:
            current_email = str(Player.GetAccountEmail() or "")
        except Exception:
            current_email = ""

        for account in sorted_accounts:
            if not account or not account.IsSlotActive:
                continue
            if account.IsPet or account.IsNPC:
                continue

            account_party_id = int(account.AgentPartyData.PartyID)
            email = str(getattr(account, "AccountEmail", "") or "")
            is_self = bool(email) and email == current_email

            if is_self:
                if current_party_id > 0 and account_party_id != current_party_id:
                    continue
            else:
                if account_party_id == 0 or account_party_id != current_party_id:
                    continue

            party_pos = int(account.AgentPartyData.PartyPosition)
            if party_pos in seen_positions:
                continue
            seen_positions.add(party_pos)

            active_emails.add(email)
            character_name = str(account.AgentData.CharacterName)

            template_code = team_viewer_broadcast.get_template_for_email(email) or ""
            parsed: tuple[int, int, dict, list] | None = None
            if template_code:
                cached = HeroAI_BaseUI._team_viewer_parse_cache.get(email)
                if cached is not None and cached[0] == template_code:
                    parsed = cached[1]
                else:
                    try:
                        parsed = Utils.ParseSkillbarTemplate(template_code)
                        HeroAI_BaseUI._team_viewer_parse_cache[email] = (template_code, parsed)
                    except Exception:
                        parsed = None

            if parsed is not None:
                primary_value = int(parsed[0])
                secondary_value = int(parsed[1])
                attributes: dict = dict(parsed[2] or {})
                raw_skills = list(parsed[3] or [])
            else:
                primary_value = int(account.AgentData.Profession[0])
                secondary_value = int(account.AgentData.Profession[1])
                attributes = {}
                raw_skills = [int(skill.Id) for skill in account.AgentData.Skillbar.Skills]

            skills = [int(s) for s in raw_skills[:8]]
            while len(skills) < 8:
                skills.append(0)

            rows.append((
                party_pos,
                character_name,
                email,
                primary_value,
                secondary_value,
                attributes,
                tuple(skills),
                template_code,
            ))

        stale_emails = [e for e in HeroAI_BaseUI._team_viewer_parse_cache if e not in active_emails]
        for stale_email in stale_emails:
            HeroAI_BaseUI._team_viewer_parse_cache.pop(stale_email, None)

        HeroAI_BaseUI._team_viewer_rows = rows
        HeroAI_BaseUI._team_viewer_timer.Reset()

    @staticmethod
    def _apply_team_viewer_template(target_email: str, template_code: str) -> None:
        if not target_email or not template_code:
            return
        try:
            from Py4GWCoreLib.Player import Player

            sender_email = Player.GetAccountEmail() or ""
            chunk_size = 29
            chunks = [template_code[i:i + chunk_size] for i in range(0, len(template_code), chunk_size)]
            while len(chunks) < 4:
                chunks.append("")
            GLOBAL_CACHE.ShMem.SendMessage(
                sender_email,
                target_email,
                SharedCommandType.LoadSkillTemplate,
                (0.0, 0.0, 0.0, 0.0),
                (chunks[0], chunks[1], chunks[2], chunks[3]),
            )
        except Exception as exc:
            ConsoleLog("HeroAI", f"Team Viewer apply failed: {exc!r}")

    @staticmethod
    def _format_team_viewer_attributes(attributes: dict) -> str:
        from Py4GWCoreLib.enums_src.GameData_enums import Attribute, AttributeNames

        if not attributes:
            return "No attributes"
        parts: list[str] = []
        for attr_id, level in attributes.items():
            if not level:
                continue
            try:
                name = AttributeNames.get(Attribute(int(attr_id)), f"Attr {attr_id}")
            except Exception:
                name = f"Attr {attr_id}"
            parts.append(f"{name} {int(level)}")
        return " | ".join(parts) if parts else "No attributes"

    @staticmethod
    def _draw_team_viewer_tab(cached_data: CacheData) -> None:
        toggle_label = "Anonymize Names: ON" if HeroAI_BaseUI._team_viewer_anonymize else "Anonymize Names: OFF"
        if PyImGui.button(f"{toggle_label}##team_viewer_anonymize"):
            HeroAI_BaseUI._team_viewer_anonymize = not HeroAI_BaseUI._team_viewer_anonymize
        PyImGui.separator()

        if not HeroAI_BaseUI._team_viewer_rows:
            PyImGui.text("No party accounts available.")
            return

        skill_icon_size = 50
        name_box_width = 150
        row_height = 140

        for party_pos, character_name, email, primary_value, secondary_value, attributes, skills_tuple, template_code in HeroAI_BaseUI._team_viewer_rows:
            display_name = HeroAI_BaseUI._get_team_viewer_display_name(party_pos, character_name)
            skills = list(skills_tuple)
            primary_label = HeroAI_BaseUI._profession_label(primary_value)
            secondary_label = HeroAI_BaseUI._profession_label(secondary_value)

            if PyImGui.begin_child(f"TVName_{party_pos}", (name_box_width, row_height), True, PyImGui.WindowFlags.NoFlag):
                name_inner_y = PyImGui.get_cursor_pos_y()
                PyImGui.set_cursor_pos_y(name_inner_y + max(0, (row_height - 40) // 2))
                ImGui.push_font("Bold", 16)
                PyImGui.text(f"{party_pos + 1}. {display_name}")
                ImGui.pop_font()
            PyImGui.end_child()

            PyImGui.same_line(0, 6)

            if PyImGui.begin_child(f"TVDetails_{party_pos}", (0, row_height), True, PyImGui.WindowFlags.NoFlag):
                PyImGui.text_colored(primary_label, HeroAI_BaseUI._profession_color(primary_value).to_tuple_normalized())
                if secondary_label:
                    PyImGui.same_line(0, 8)
                    PyImGui.text("/")
                    PyImGui.same_line(0, 8)
                    PyImGui.text_colored(secondary_label, HeroAI_BaseUI._profession_color(secondary_value).to_tuple_normalized())

                PyImGui.text("Attributes:")
                PyImGui.same_line(0, 8)
                attr_text = HeroAI_BaseUI._format_team_viewer_attributes(attributes)
                attr_color = ColorPalette.GetColor("white") if attributes else ColorPalette.GetColor("gray")
                PyImGui.text_colored(attr_text, attr_color.to_tuple_normalized())

                PyImGui.text("Template:")
                PyImGui.same_line(0, 8)
                if template_code:
                    PyImGui.text_colored(template_code, ColorPalette.GetColor("white").to_tuple_normalized())
                else:
                    PyImGui.text_colored("(unavailable)", ColorPalette.GetColor("gray").to_tuple_normalized())

                skill_row_y = PyImGui.get_cursor_pos_y()
                for skill_index, skill_id in enumerate(skills[:8]):
                    skill_id_int = int(skill_id)
                    slot_label = skill_index + 1
                    if skill_id_int != 0:
                        texture_path = GLOBAL_CACHE.Skill.ExtraData.GetTexturePath(skill_id_int)
                        if texture_path:
                            ImGui.DrawTexture(texture_path, skill_icon_size, skill_icon_size)
                        else:
                            PyImGui.button(f"?##tv_skill_{party_pos}_{skill_index}", skill_icon_size, skill_icon_size)
                        if PyImGui.is_item_hovered():
                            PyImGui.begin_tooltip()
                            HeroAI_BaseUI._draw_skill_info_card(skill_id_int, tooltip=True)
                            PyImGui.end_tooltip()
                    else:
                        PyImGui.button(f"Empty##tv_empty_{party_pos}_{skill_index}", skill_icon_size, skill_icon_size)
                        if PyImGui.is_item_hovered():
                            PyImGui.begin_tooltip()
                            PyImGui.text(f"Slot {slot_label}: Empty")
                            PyImGui.end_tooltip()
                    PyImGui.same_line(0, 5)

                button_y_offset = max(0, (skill_icon_size - 24) // 2)
                PyImGui.set_cursor_pos_y(skill_row_y + button_y_offset)
                copy_disabled = not template_code
                PyImGui.begin_disabled(copy_disabled)
                if PyImGui.button(f"Copy Template##tv_copy_{party_pos}"):
                    PyImGui.set_clipboard_text(template_code)
                PyImGui.end_disabled()
            PyImGui.end_child()

    @staticmethod
    def DrawBuildMatchesWindow(cached_data: CacheData):
        if not HeroAI_BaseUI.show_build_match_window:
            return

        HeroAI_BaseUI._refresh_build_match_rows(cached_data)
        HeroAI_BaseUI._refresh_team_viewer_rows(cached_data)
        registry = HeroAI_BaseUI._get_build_registry()
        PyImGui.set_next_window_size((980, 720), PyImGui.ImGuiCond.FirstUseEver)

        if ImGui.Begin(ini_key=cached_data.ini_key, name="HeroAI Build Matches", p_open=True, flags=PyImGui.WindowFlags.NoFlag):
            if PyImGui.begin_tab_bar("HeroAIBuildMatchTabs"):
                if PyImGui.begin_tab_item("Matches"):
                    PyImGui.text("Resolved from each account's shared-memory profession pair and skillbar.")
                    PyImGui.same_line(0, 12)
                    if PyImGui.button("Debug##build_match_debug"):
                        HeroAI_BaseUI._dump_build_match_debug(cached_data)
                    PyImGui.separator()
                    HeroAI_BaseUI._draw_build_matches_tab()
                    PyImGui.end_tab_item()

                if PyImGui.begin_tab_item("Supported Builds"):
                    HeroAI_BaseUI._draw_supported_builds_tab(registry)
                    PyImGui.end_tab_item()

                if PyImGui.begin_tab_item("Team Viewer"):
                    HeroAI_BaseUI._draw_team_viewer_tab(cached_data)
                    PyImGui.end_tab_item()

                if PyImGui.begin_tab_item("Hex Removal"):
                    from HeroAI.hex_removal_src.hex_removal_ui import draw_tab as _draw_hex_removal_tab
                    _draw_hex_removal_tab()
                    PyImGui.end_tab_item()

                PyImGui.end_tab_bar()

        ImGui.End(cached_data.ini_key)

    @staticmethod
    def _follow_threshold_presets() -> list[tuple[str, float | None]]:
        return [
            ("Manual", None),
            ("Zero", 0.0),
            (Range.Touch.name, float(Range.Touch.value)),
            (Range.Adjacent.name, float(Range.Adjacent.value)),
            (Range.Nearby.name, float(Range.Nearby.value)),
            (Range.Area.name, float(Range.Area.value)),
            (Range.Earshot.name, float(Range.Earshot.value)),
            (Range.Spellcast.name, float(Range.Spellcast.value)),
        ]

    @staticmethod
    def _threshold_mode_index(mode_name: str) -> int:
        presets = HeroAI_BaseUI._follow_threshold_presets()
        for i, (name, _) in enumerate(presets):
            if name == mode_name:
                return i
        return 0

    @staticmethod
    def _ensure_follow_module_ini_keys():
        im = IniManager()
        if not HeroAI_BaseUI.follow_formations_ini_key:
            HeroAI_BaseUI.follow_formations_ini_key = im.ensure_global_key("HeroAI", "FollowModule_Formations.ini")
        if not HeroAI_BaseUI.follow_formations_settings_key:
            HeroAI_BaseUI.follow_formations_settings_key = im.ensure_global_key("HeroAI", "FollowModule_Settings.ini")
        if not HeroAI_BaseUI.follow_runtime_ini_key:
            HeroAI_BaseUI.follow_runtime_ini_key = im.ensure_global_key("HeroAI", "FollowRuntime.ini")
        return bool(
            HeroAI_BaseUI.follow_formations_ini_key
            and HeroAI_BaseUI.follow_formations_settings_key
            and HeroAI_BaseUI.follow_runtime_ini_key
        )

    @staticmethod
    def _ensure_follow_window_ini_vars(ini_key: str):
        if not HeroAI_BaseUI._ensure_follow_module_ini_keys():
            return
        ini_key = HeroAI_BaseUI.follow_runtime_ini_key
        im = IniManager()
        if (
            not HeroAI_BaseUI.follow_window_ini_vars_registered
            or HeroAI_BaseUI.follow_window_ini_vars_registered_key != ini_key
        ):
            im.add_bool(ini_key, "show_broadcast_follow_positions", "FollowRuntime", "show_broadcast_follow_positions", True)
            im.add_bool(ini_key, "show_broadcast_follow_threshold_rings", "FollowRuntime", "show_broadcast_follow_threshold_rings", True)
            im.add_bool(ini_key, "show_flagging_window", "FollowRuntime", "show_flagging_window", False)
            im.add_float(ini_key, "follow_move_threshold_default", "FollowRuntime", "follow_move_threshold_default", float(Range.Area.value))
            im.add_float(ini_key, "follow_move_threshold_combat", "FollowRuntime", "follow_move_threshold_combat", float(Range.Touch.value))
            im.add_float(ini_key, "follow_move_threshold_flagged", "FollowRuntime", "follow_move_threshold_flagged", 0.0)
            im.add_str(ini_key, "follow_move_threshold_default_mode", "FollowRuntime", "follow_move_threshold_default_mode", "Area")
            im.add_str(ini_key, "follow_move_threshold_combat_mode", "FollowRuntime", "follow_move_threshold_combat_mode", "Touch")
            im.add_str(ini_key, "follow_move_threshold_flagged_mode", "FollowRuntime", "follow_move_threshold_flagged_mode", "Zero")
            HeroAI_BaseUI.follow_window_ini_vars_registered = True
            HeroAI_BaseUI.follow_window_ini_vars_registered_key = ini_key
        im.load_once(ini_key)

    @staticmethod
    def _load_follow_runtime_config(ini_key: str):
        if not HeroAI_BaseUI._ensure_follow_module_ini_keys():
            return
        ini_key = HeroAI_BaseUI.follow_runtime_ini_key
        HeroAI_BaseUI._ensure_follow_window_ini_vars(ini_key)
        im = IniManager()
        hero_globals.show_broadcast_follow_positions = bool(im.getBool(ini_key, "show_broadcast_follow_positions", True, section="FollowRuntime"))
        hero_globals.show_broadcast_follow_threshold_rings = bool(im.getBool(ini_key, "show_broadcast_follow_threshold_rings", True, section="FollowRuntime"))
        hero_globals.show_flagging_window = bool(im.getBool(ini_key, "show_flagging_window", False, section="FollowRuntime"))
        HeroAI_BaseUI.follow_move_threshold_default = max(0.0, float(im.getFloat(ini_key, "follow_move_threshold_default", float(Range.Area.value), section="FollowRuntime")))
        HeroAI_BaseUI.follow_move_threshold_combat = max(0.0, float(im.getFloat(ini_key, "follow_move_threshold_combat", float(Range.Touch.value), section="FollowRuntime")))
        HeroAI_BaseUI.follow_move_threshold_flagged = max(0.0, float(im.getFloat(ini_key, "follow_move_threshold_flagged", 0.0, section="FollowRuntime")))
        HeroAI_BaseUI.follow_move_threshold_default_mode = str(im.getStr(ini_key, "follow_move_threshold_default_mode", "Area", section="FollowRuntime"))
        HeroAI_BaseUI.follow_move_threshold_combat_mode = str(im.getStr(ini_key, "follow_move_threshold_combat_mode", "Touch", section="FollowRuntime"))
        HeroAI_BaseUI.follow_move_threshold_flagged_mode = str(im.getStr(ini_key, "follow_move_threshold_flagged_mode", "Zero", section="FollowRuntime"))

    @staticmethod
    def _write_follow_runtime_value(im: IniManager, ini_key: str, name: str, value) -> None:
        section = "FollowRuntime"
        im.write_key(ini_key, section, name, value)
        node = im._get_node(ini_key)
        if node:
            text_value = str(value)
            node.ini_handler.write_key(section, name, text_value)
            node.cached_values[(section, name)] = text_value
            node.pending_writes.pop((section, name), None)
            node.needs_flush = bool(node.pending_writes)

    @staticmethod
    def _save_follow_runtime_config(ini_key: str):
        if not HeroAI_BaseUI._ensure_follow_module_ini_keys():
            return
        ini_key = HeroAI_BaseUI.follow_runtime_ini_key
        im = IniManager()
        HeroAI_BaseUI._ensure_follow_window_ini_vars(ini_key)
        im.set(ini_key, "show_broadcast_follow_positions", bool(hero_globals.show_broadcast_follow_positions), section="FollowRuntime")
        im.set(ini_key, "show_broadcast_follow_threshold_rings", bool(hero_globals.show_broadcast_follow_threshold_rings), section="FollowRuntime")
        im.set(ini_key, "show_flagging_window", bool(hero_globals.show_flagging_window), section="FollowRuntime")
        im.set(ini_key, "follow_move_threshold_default", float(HeroAI_BaseUI.follow_move_threshold_default), section="FollowRuntime")
        im.set(ini_key, "follow_move_threshold_combat", float(HeroAI_BaseUI.follow_move_threshold_combat), section="FollowRuntime")
        im.set(ini_key, "follow_move_threshold_flagged", float(HeroAI_BaseUI.follow_move_threshold_flagged), section="FollowRuntime")
        im.set(ini_key, "follow_move_threshold_default_mode", str(HeroAI_BaseUI.follow_move_threshold_default_mode), section="FollowRuntime")
        im.set(ini_key, "follow_move_threshold_combat_mode", str(HeroAI_BaseUI.follow_move_threshold_combat_mode), section="FollowRuntime")
        im.set(ini_key, "follow_move_threshold_flagged_mode", str(HeroAI_BaseUI.follow_move_threshold_flagged_mode), section="FollowRuntime")
        im.save_vars(ini_key)
        HeroAI_BaseUI._write_follow_runtime_value(im, ini_key, "show_broadcast_follow_positions", bool(hero_globals.show_broadcast_follow_positions))
        HeroAI_BaseUI._write_follow_runtime_value(im, ini_key, "show_broadcast_follow_threshold_rings", bool(hero_globals.show_broadcast_follow_threshold_rings))
        HeroAI_BaseUI._write_follow_runtime_value(im, ini_key, "show_flagging_window", bool(hero_globals.show_flagging_window))
        HeroAI_BaseUI._write_follow_runtime_value(im, ini_key, "follow_move_threshold_default", float(HeroAI_BaseUI.follow_move_threshold_default))
        HeroAI_BaseUI._write_follow_runtime_value(im, ini_key, "follow_move_threshold_combat", float(HeroAI_BaseUI.follow_move_threshold_combat))
        HeroAI_BaseUI._write_follow_runtime_value(im, ini_key, "follow_move_threshold_flagged", float(HeroAI_BaseUI.follow_move_threshold_flagged))
        HeroAI_BaseUI._write_follow_runtime_value(im, ini_key, "follow_move_threshold_default_mode", str(HeroAI_BaseUI.follow_move_threshold_default_mode))
        HeroAI_BaseUI._write_follow_runtime_value(im, ini_key, "follow_move_threshold_combat_mode", str(HeroAI_BaseUI.follow_move_threshold_combat_mode))
        HeroAI_BaseUI._write_follow_runtime_value(im, ini_key, "follow_move_threshold_flagged_mode", str(HeroAI_BaseUI.follow_move_threshold_flagged_mode))

    @staticmethod
    def _load_follow_formations_quick_data():
        if not HeroAI_BaseUI._ensure_follow_module_ini_keys():
            HeroAI_BaseUI.follow_formations_names = []
            HeroAI_BaseUI.follow_formations_ids = []
            HeroAI_BaseUI.follow_formations_selected_index = 0
            return
        im = IniManager()
        try:
            im.reload(HeroAI_BaseUI.follow_formations_ini_key)
            im.reload(HeroAI_BaseUI.follow_formations_settings_key)
        except Exception:
            pass

        count = max(0, im.read_int(HeroAI_BaseUI.follow_formations_ini_key, "Formations", "count", 0))
        names: list[str] = []
        ids: list[str] = []
        for i in range(count):
            fid = str(im.read_key(HeroAI_BaseUI.follow_formations_ini_key, "Formations", f"id_{i}", "") or "").strip()
            name = str(im.read_key(HeroAI_BaseUI.follow_formations_ini_key, "Formations", f"name_{i}", "") or "").strip()
            if not fid or not name:
                continue
            ids.append(fid)
            names.append(name)

        selected_id = str(im.read_key(HeroAI_BaseUI.follow_formations_settings_key, "Formations", "selected_id", "") or "").strip()
        selected_index = 0
        if selected_id and ids:
            try:
                selected_index = ids.index(selected_id)
            except ValueError:
                selected_index = 0

        HeroAI_BaseUI.follow_formations_names = names
        HeroAI_BaseUI.follow_formations_ids = ids
        HeroAI_BaseUI.follow_formations_selected_index = selected_index

    @staticmethod
    def _set_selected_follow_formation(index: int):
        if not HeroAI_BaseUI._ensure_follow_module_ini_keys():
            return
        if index < 0 or index >= len(HeroAI_BaseUI.follow_formations_ids):
            return
        HeroAI_BaseUI.follow_formations_selected_index = index
        selected_id = HeroAI_BaseUI.follow_formations_ids[index]
        selected_name = HeroAI_BaseUI.follow_formations_names[index]

        im = IniManager()
        key = HeroAI_BaseUI.follow_formations_settings_key
        try:
            node = im._get_node(key)
            if node:
                node.ini_handler.write_key("Formations", "selected_id", selected_id)
                node.ini_handler.write_key("Formations", "selected", selected_name)
                if hasattr(node, "cached_values") and node.cached_values is not None:
                    node.cached_values[("Formations", "selected_id")] = str(selected_id)
                    node.cached_values[("Formations", "selected")] = str(selected_name)
                if hasattr(node, "pending_writes") and node.pending_writes is not None:
                    node.pending_writes.pop(("Formations", "selected_id"), None)
                    node.pending_writes.pop(("Formations", "selected"), None)
                return
        except Exception:
            pass
        im.write_key(key, "Formations", "selected_id", selected_id)
        im.write_key(key, "Formations", "selected", selected_name)

    @staticmethod
    def _set_party_follow_option(cached_data: CacheData, option_name: str, value: bool) -> None:
        if cached_data.global_options is not None and hasattr(cached_data.global_options, option_name):
            setattr(cached_data.global_options, option_name, bool(value))

        for account in cached_data.party.accounts.values():
            if (
                not account
                or not account.IsSlotActive
                or account.IsHero
                or account.AgentPartyData.PartyID != GLOBAL_CACHE.Party.GetPartyID()
            ):
                continue

            account_options = GLOBAL_CACHE.ShMem.GetHeroAIOptionsFromEmail(account.AccountEmail)
            if account_options is not None and hasattr(account_options, option_name):
                setattr(account_options, option_name, bool(value))

    @staticmethod
    def _refresh_follow_publisher_live(cached_data: CacheData, *, reload_ini: bool = False) -> None:
        try:
            publisher = getattr(GLOBAL_CACHE.ShMem, "follow_publisher", None)
            if publisher is None:
                return
            if reload_ini and hasattr(publisher, "refresh_from_ini"):
                publisher.refresh_from_ini()
            publisher.publish(force=True)
        except Exception:
            pass

    @staticmethod
    def _apply_follow_thresholds_to_party(cached_data: CacheData) -> None:
        leader_options = GLOBAL_CACHE.ShMem.GetHeroAIOptionsByPartyNumber(0)
        leader_all_flag_active = (
            leader_options is not None
            and bool(getattr(leader_options, "IsFlagged", False))
            and (
                abs(float(getattr(leader_options.AllFlag, "x", 0.0))) > 0.001
                or abs(float(getattr(leader_options.AllFlag, "y", 0.0))) > 0.001
            )
        )

        for account in cached_data.party.accounts.values():
            if (
                not account
                or not account.IsSlotActive
                or account.IsHero
                or account.AgentPartyData.PartyID != GLOBAL_CACHE.Party.GetPartyID()
            ):
                continue

            options = GLOBAL_CACHE.ShMem.GetHeroAIOptionsFromEmail(account.AccountEmail)
            if options is None:
                continue

            personal_flag_active = (
                bool(getattr(options, "IsFlagged", False))
                and (
                    abs(float(getattr(options.FlagPos, "x", 0.0))) > 0.001
                    or abs(float(getattr(options.FlagPos, "y", 0.0))) > 0.001
                )
            )

            if personal_flag_active or leader_all_flag_active:
                options.FollowMoveThreshold = float(HeroAI_BaseUI.follow_move_threshold_flagged)
                options.FollowMoveThresholdCombat = float(HeroAI_BaseUI.follow_move_threshold_flagged)
            else:
                options.FollowMoveThreshold = float(HeroAI_BaseUI.follow_move_threshold_default)
                options.FollowMoveThresholdCombat = float(HeroAI_BaseUI.follow_move_threshold_combat)

    @staticmethod
    def DrawFlaggingWindow(cached_data: CacheData):
        party_size = GLOBAL_CACHE.Party.GetPartySize()
        if party_size == 1:
            PyImGui.text("No Follower or Heroes to Flag.")
            return

        if PyImGui.button("Pin Down Flag Position"):
            leader_x, leader_y = Agent.GetXY(GLOBAL_CACHE.Party.GetPartyLeaderID())
            leader_options = GLOBAL_CACHE.ShMem.GetHeroAIOptionsByPartyNumber(0)
            if leader_options:
                leader_options.AllFlag.x = leader_x
                leader_options.AllFlag.y = leader_y
                leader_options.IsFlagged = True
                leader_options.FlagFacingAngle = Agent.GetRotationAngle(GLOBAL_CACHE.Party.GetPartyLeaderID())
            GLOBAL_CACHE.Party.Heroes.FlagAllHeroes(leader_x, leader_y)
            HeroAI_BaseUI.AllFlag = True
            HeroAI_BaseUI.capture_hero_flag = False
            HeroAI_BaseUI.capture_flag_all = False
            HeroAI_BaseUI.capture_hero_index = 0
            HeroAI_BaseUI.one_time_set_flag = False
            hero_globals.capture_mouse_timer.Stop()

        if PyImGui.begin_table("Flags", 3):
            PyImGui.table_next_row()
            PyImGui.table_next_column()
            if party_size >= 2:
                HeroAI_BaseUI.HeroFlags[0] = ImGui.toggle_button("1", IsHeroFlagged(1), 30, 30)
            PyImGui.table_next_column()
            if party_size >= 3:
                HeroAI_BaseUI.HeroFlags[1] = ImGui.toggle_button("2", IsHeroFlagged(2), 30, 30)
            PyImGui.table_next_column()
            if party_size >= 4:
                HeroAI_BaseUI.HeroFlags[2] = ImGui.toggle_button("3", IsHeroFlagged(3), 30, 30)
            PyImGui.table_next_row()
            PyImGui.table_next_column()
            if party_size >= 5:
                HeroAI_BaseUI.HeroFlags[3] = ImGui.toggle_button("4", IsHeroFlagged(4), 30, 30)
            PyImGui.table_next_column()
            HeroAI_BaseUI.AllFlag = ImGui.toggle_button("All", IsHeroFlagged(0), 30, 30)
            PyImGui.table_next_column()
            if party_size >= 6:
                HeroAI_BaseUI.HeroFlags[4] = ImGui.toggle_button("5", IsHeroFlagged(5), 30, 30)
            PyImGui.table_next_row()
            PyImGui.table_next_column()
            if party_size >= 7:
                HeroAI_BaseUI.HeroFlags[5] = ImGui.toggle_button("6", IsHeroFlagged(6), 30, 30)
            PyImGui.table_next_column()
            if party_size >= 8:
                HeroAI_BaseUI.HeroFlags[6] = ImGui.toggle_button("7", IsHeroFlagged(7), 30, 30)
            PyImGui.table_next_column()
            HeroAI_BaseUI.ClearFlags = ImGui.toggle_button("X", HeroAI_BaseUI.ClearFlags, 30, 30)
            PyImGui.end_table()

        if HeroAI_BaseUI.AllFlag != IsHeroFlagged(0):
            HeroAI_BaseUI.capture_hero_flag = True
            HeroAI_BaseUI.capture_flag_all = True
            HeroAI_BaseUI.capture_hero_index = 0
            HeroAI_BaseUI.one_time_set_flag = False
            hero_globals.capture_mouse_timer.Start()

        for i in range(1, party_size):
            if HeroAI_BaseUI.HeroFlags[i - 1] != IsHeroFlagged(i):
                HeroAI_BaseUI.capture_hero_flag = True
                HeroAI_BaseUI.capture_flag_all = False
                HeroAI_BaseUI.capture_hero_index = i
                HeroAI_BaseUI.one_time_set_flag = False
                hero_globals.capture_mouse_timer.Start()

    @staticmethod
    def DrawFollowFormationsQuickWindow(cached_data: CacheData):
        if not HeroAI_BaseUI.show_follow_formations_quick_window:
            return

        if ImGui.Begin(ini_key=cached_data.formation_window_ini_key, name="Follow Formations Quick Settings", p_open=True, flags=PyImGui.WindowFlags.AlwaysAutoResize):
            HeroAI_BaseUI._load_follow_formations_quick_data()
            HeroAI_BaseUI._load_follow_runtime_config(cached_data.formation_window_ini_key)
            if PyImGui.button("Refresh Formations"):
                HeroAI_BaseUI._load_follow_formations_quick_data()
                HeroAI_BaseUI._load_follow_runtime_config(cached_data.formation_window_ini_key)
            PyImGui.same_line(0, 6)
            editor_label = "Close Editor" if HeroAI_BaseUI.show_follow_formations_editor_window else "Open Editor"
            if PyImGui.button(editor_label):
                HeroAI_BaseUI.show_follow_formations_editor_window = not HeroAI_BaseUI.show_follow_formations_editor_window
                if HeroAI_BaseUI.show_follow_formations_editor_window:
                    from HeroAI.follow.editor import open_editor
                    open_editor()

            if HeroAI_BaseUI.follow_formations_names:
                idx = PyImGui.combo("Formation", HeroAI_BaseUI.follow_formations_selected_index, HeroAI_BaseUI.follow_formations_names)
                if idx != HeroAI_BaseUI.follow_formations_selected_index:
                    HeroAI_BaseUI._set_selected_follow_formation(idx)
                    HeroAI_BaseUI._refresh_follow_publisher_live(cached_data, reload_ini=True)
            else:
                PyImGui.text_disabled("No saved follow formations found.")

            dirty_runtime_cfg = False

            PyImGui.separator()
            PyImGui.text("Follower Behavior")

            if cached_data.global_options is not None:
                new_following = PyImGui.checkbox("Enable Following", bool(cached_data.global_options.Following))
                if new_following != bool(cached_data.global_options.Following):
                    HeroAI_BaseUI._set_party_follow_option(cached_data, "Following", new_following)
                    HeroAI_BaseUI._refresh_follow_publisher_live(cached_data)

                new_avoidance = PyImGui.checkbox("Enable Combat Avoidance Mix", bool(cached_data.global_options.Avoidance))
                if new_avoidance != bool(cached_data.global_options.Avoidance):
                    HeroAI_BaseUI._set_party_follow_option(cached_data, "Avoidance", new_avoidance)
                    HeroAI_BaseUI._refresh_follow_publisher_live(cached_data)

            PyImGui.separator()
            PyImGui.text("Follow Publish")

            new_show_broadcast_follow_positions = PyImGui.checkbox("Draw Followers FollowPos (3D)", hero_globals.show_broadcast_follow_positions)
            if new_show_broadcast_follow_positions != hero_globals.show_broadcast_follow_positions:
                hero_globals.show_broadcast_follow_positions = new_show_broadcast_follow_positions
                dirty_runtime_cfg = True

            new_show_broadcast_follow_threshold_rings = PyImGui.checkbox("Draw Followers Threshold Rings (3D)", hero_globals.show_broadcast_follow_threshold_rings)
            if new_show_broadcast_follow_threshold_rings != hero_globals.show_broadcast_follow_threshold_rings:
                hero_globals.show_broadcast_follow_threshold_rings = new_show_broadcast_follow_threshold_rings
                dirty_runtime_cfg = True
            presets = HeroAI_BaseUI._follow_threshold_presets()
            preset_names = [name for name, _ in presets]

            d_idx = PyImGui.combo("Follow Threshold Preset", HeroAI_BaseUI._threshold_mode_index(HeroAI_BaseUI.follow_move_threshold_default_mode), preset_names)
            d_name, d_val = presets[d_idx]
            if d_name != HeroAI_BaseUI.follow_move_threshold_default_mode:
                HeroAI_BaseUI.follow_move_threshold_default_mode = d_name
                if d_val is not None:
                    HeroAI_BaseUI.follow_move_threshold_default = float(d_val)
                dirty_runtime_cfg = True
            new_default_thr = max(0.0, float(PyImGui.input_float("Follow Threshold", float(HeroAI_BaseUI.follow_move_threshold_default))))
            if abs(new_default_thr - HeroAI_BaseUI.follow_move_threshold_default) > 0.0001:
                HeroAI_BaseUI.follow_move_threshold_default = new_default_thr
                if HeroAI_BaseUI.follow_move_threshold_default_mode != "Manual":
                    HeroAI_BaseUI.follow_move_threshold_default_mode = "Manual"
                dirty_runtime_cfg = True

            c_idx = PyImGui.combo("Combat Threshold Preset", HeroAI_BaseUI._threshold_mode_index(HeroAI_BaseUI.follow_move_threshold_combat_mode), preset_names)
            c_name, c_val = presets[c_idx]
            if c_name != HeroAI_BaseUI.follow_move_threshold_combat_mode:
                HeroAI_BaseUI.follow_move_threshold_combat_mode = c_name
                if c_val is not None:
                    HeroAI_BaseUI.follow_move_threshold_combat = float(c_val)
                dirty_runtime_cfg = True
            new_combat_thr = max(0.0, float(PyImGui.input_float("Combat Follow Threshold", float(HeroAI_BaseUI.follow_move_threshold_combat))))
            if abs(new_combat_thr - HeroAI_BaseUI.follow_move_threshold_combat) > 0.0001:
                HeroAI_BaseUI.follow_move_threshold_combat = new_combat_thr
                if HeroAI_BaseUI.follow_move_threshold_combat_mode != "Manual":
                    HeroAI_BaseUI.follow_move_threshold_combat_mode = "Manual"
                dirty_runtime_cfg = True

            f_idx = PyImGui.combo("Flag Threshold Preset", HeroAI_BaseUI._threshold_mode_index(HeroAI_BaseUI.follow_move_threshold_flagged_mode), preset_names)
            f_name, f_val = presets[f_idx]
            if f_name != HeroAI_BaseUI.follow_move_threshold_flagged_mode:
                HeroAI_BaseUI.follow_move_threshold_flagged_mode = f_name
                if f_val is not None:
                    HeroAI_BaseUI.follow_move_threshold_flagged = float(f_val)
                dirty_runtime_cfg = True
            new_flagged_thr = max(0.0, float(PyImGui.input_float("Flag Threshold", float(HeroAI_BaseUI.follow_move_threshold_flagged))))
            if abs(new_flagged_thr - HeroAI_BaseUI.follow_move_threshold_flagged) > 0.0001:
                HeroAI_BaseUI.follow_move_threshold_flagged = new_flagged_thr
                if HeroAI_BaseUI.follow_move_threshold_flagged_mode != "Manual":
                    HeroAI_BaseUI.follow_move_threshold_flagged_mode = "Manual"
                dirty_runtime_cfg = True

            movement_cfg = load_follow_movement_config()
            PyImGui.separator()
            PyImGui.text("Combat Movement Mix")

            new_recovery_distance = max(1.0, float(PyImGui.input_float("Slot Recovery Distance", float(movement_cfg.slot_recovery_distance))))
            if abs(new_recovery_distance - movement_cfg.slot_recovery_distance) > 0.0001:
                movement_cfg.slot_recovery_distance = new_recovery_distance
                save_follow_movement_config(movement_cfg)
                HeroAI_BaseUI._refresh_follow_publisher_live(cached_data, reload_ini=True)

            new_ally_radius = max(0.0, float(PyImGui.input_float("Ally Repulsion Radius", float(movement_cfg.ally_repulsion_radius))))
            if abs(new_ally_radius - movement_cfg.ally_repulsion_radius) > 0.0001:
                movement_cfg.ally_repulsion_radius = new_ally_radius
                save_follow_movement_config(movement_cfg)
                HeroAI_BaseUI._refresh_follow_publisher_live(cached_data, reload_ini=True)

            new_ally_weight = max(0.0, float(PyImGui.input_float("Ally Repulsion Weight", float(movement_cfg.ally_repulsion_weight))))
            if abs(new_ally_weight - movement_cfg.ally_repulsion_weight) > 0.0001:
                movement_cfg.ally_repulsion_weight = new_ally_weight
                save_follow_movement_config(movement_cfg)
                HeroAI_BaseUI._refresh_follow_publisher_live(cached_data, reload_ini=True)

            new_enemy_radius = max(0.0, float(PyImGui.input_float("Enemy Repulsion Radius", float(movement_cfg.enemy_repulsion_radius))))
            if abs(new_enemy_radius - movement_cfg.enemy_repulsion_radius) > 0.0001:
                movement_cfg.enemy_repulsion_radius = new_enemy_radius
                save_follow_movement_config(movement_cfg)
                HeroAI_BaseUI._refresh_follow_publisher_live(cached_data, reload_ini=True)

            new_enemy_weight = max(0.0, float(PyImGui.input_float("Enemy Repulsion Weight", float(movement_cfg.enemy_repulsion_weight))))
            if abs(new_enemy_weight - movement_cfg.enemy_repulsion_weight) > 0.0001:
                movement_cfg.enemy_repulsion_weight = new_enemy_weight
                save_follow_movement_config(movement_cfg)
                HeroAI_BaseUI._refresh_follow_publisher_live(cached_data, reload_ini=True)

            new_move_clamp = max(1.0, float(PyImGui.input_float("Local Move Clamp", float(movement_cfg.local_move_clamp))))
            if abs(new_move_clamp - movement_cfg.local_move_clamp) > 0.0001:
                movement_cfg.local_move_clamp = new_move_clamp
                save_follow_movement_config(movement_cfg)
                HeroAI_BaseUI._refresh_follow_publisher_live(cached_data, reload_ini=True)

            new_min_move = max(0.0, float(PyImGui.input_float("Local Min Move Threshold", float(movement_cfg.min_move_threshold))))
            if abs(new_min_move - movement_cfg.min_move_threshold) > 0.0001:
                movement_cfg.min_move_threshold = new_min_move
                save_follow_movement_config(movement_cfg)
                HeroAI_BaseUI._refresh_follow_publisher_live(cached_data, reload_ini=True)

            if dirty_runtime_cfg:
                HeroAI_BaseUI._save_follow_runtime_config(cached_data.formation_window_ini_key)
                HeroAI_BaseUI._apply_follow_thresholds_to_party(cached_data)
                HeroAI_BaseUI._refresh_follow_publisher_live(cached_data, reload_ini=True)

            if Map.IsExplorable() and Player.GetAgentID() == GLOBAL_CACHE.Party.GetPartyLeaderID():
                new_show_flagging_window = PyImGui.checkbox("Show Flagging Window", hero_globals.show_flagging_window)
                if new_show_flagging_window != hero_globals.show_flagging_window:
                    hero_globals.show_flagging_window = new_show_flagging_window
                    HeroAI_BaseUI._save_follow_runtime_config(cached_data.formation_window_ini_key)
                    HeroAI_BaseUI._refresh_follow_publisher_live(cached_data, reload_ini=True)

        ImGui.End(ini_key=cached_data.formation_window_ini_key)

        if HeroAI_BaseUI.show_follow_formations_editor_window:
            import Py4GW
            try:
                from HeroAI.follow.editor import main as draw_follow_formations_editor
                HeroAI_BaseUI.show_follow_formations_editor_window = bool(draw_follow_formations_editor())
            except Exception as e:
                Py4GW.Console.Log("HeroAI", f"Follow formations editor failed: {e}", Py4GW.Console.MessageType.Error)
                HeroAI_BaseUI.show_follow_formations_editor_window = False

        if hero_globals.show_flagging_window and Map.IsExplorable() and Player.GetAgentID() == GLOBAL_CACHE.Party.GetPartyLeaderID():
            if ImGui.Begin(ini_key=cached_data.flagging_window_ini_key, name="Flagging Window", p_open=True, flags=PyImGui.WindowFlags.AlwaysAutoResize):
                HeroAI_BaseUI.DrawFlaggingWindow(cached_data)
            ImGui.End(ini_key=cached_data.flagging_window_ini_key)
            
    @staticmethod
    def DrawFramedContent(cached_data: CacheData, content_frame_id):
        from Py4GWCoreLib import Utils
        
        if  HeroAI_FloatingWindows.selected_tab == HeroAI_FloatingWindows.TabType.party:
            return

        child_left, child_top, child_right, child_bottom = UIManager.GetFrameCoords(content_frame_id)
        width = child_right - child_left
        height = child_bottom - child_top

        UIManager().DrawFrame(content_frame_id, Utils.RGBToColor(0, 0, 0, 255))

        flags = PyImGui.WindowFlags.NoCollapse | PyImGui.WindowFlags.NoTitleBar | PyImGui.WindowFlags.NoResize
        PyImGui.push_style_var(ImGui.ImGuiStyleVar.WindowRounding, 0.0)
        PyImGui.set_next_window_pos(child_left, child_top)
        PyImGui.set_next_window_size(width, height)

        def control_panel_case(cached_data : CacheData):
            from HeroAI.ui_base import HeroAI_BaseUI

            own_party_number = GLOBAL_CACHE.Party.GetOwnPartyNumber()
            
            if own_party_number == 0:
                # leader control panel
                
                HeroAI_BaseUI.DrawPanelButtons("global", cached_data.global_options, set_global=True)
                
                if PyImGui.collapsing_header("Player Control"):
                    for index in range(MAX_NUM_PLAYERS):
                        account = GLOBAL_CACHE.ShMem.GetAccountDataFromPartyNumber(index)
                        options = GLOBAL_CACHE.ShMem.GetHeroAIOptionsByPartyNumber(index)
                        
                        if account and not account.IsHero:                            
                            if PyImGui.tree_node(f"{account.AgentData.CharacterName}##ControlPlayer{index}"):
                                if options is not None:
                                    HeroAI_BaseUI.DrawPanelButtons(account.AccountEmail, options)
                                
                                PyImGui.tree_pop()
            else:
                # follower control panel
                options = GLOBAL_CACHE.ShMem.GetHeroAIOptionsFromEmail(cached_data.account_email)
                
                if options is not None:
                    HeroAI_BaseUI.DrawPanelButtons(cached_data.account_email, options)

        if PyImGui.begin("##heroai_framed_content", True, flags):
            match HeroAI_FloatingWindows.selected_tab:
                case HeroAI_FloatingWindows.TabType.control_panel:
                    control_panel_case(cached_data)
                case HeroAI_FloatingWindows.TabType.candidates:
                    HeroAI_BaseUI.DrawCandidateWindow(cached_data)
                case HeroAI_FloatingWindows.TabType.flagging:
                    HeroAI_BaseUI.DrawFlaggingWindow(cached_data)
                case HeroAI_FloatingWindows.TabType.config:
                    HeroAI_Windows.DrawOptions(cached_data)
                case HeroAI_FloatingWindows.TabType.messaging:
                    # Placeholder for messaging tab
                    HeroAI_Windows.DrawMessagingOptions(cached_data)

        PyImGui.end()
        PyImGui.pop_style_var(1)

    @staticmethod
    def DrawEmbeddedWindow(cached_data: CacheData):         
        if not HeroAI_FloatingWindows.settings.ShowPartyPanelUI:        
             return
         
        parent_frame_id = UIManager.GetFrameIDByHash(PARTY_WINDOW_HASH)
        outpost_content_frame_id = UIManager.GetChildFrameID(PARTY_WINDOW_HASH, PARTY_WINDOW_FRAME_OUTPOST_OFFSETS)
        explorable_content_frame_id = UIManager.GetChildFrameID(PARTY_WINDOW_HASH, PARTY_WINDOW_FRAME_EXPLORABLE_OFFSETS)

        if Map.IsMapReady() and Map.IsExplorable():
            content_frame_id = explorable_content_frame_id
        else:
            content_frame_id = outpost_content_frame_id

        left, top, right, _bottom = UIManager.GetFrameCoords(parent_frame_id)
        frame_offset = 5
        width = right - left - frame_offset

        flags = ImGui.PushTransparentWindow()

        PyImGui.set_next_window_pos(left, top - 35)
        PyImGui.set_next_window_size(width, 35)
        if PyImGui.begin("embedded contorl panel", True, flags):
            if PyImGui.begin_tab_bar("HeroAITabs"):
                if PyImGui.begin_tab_item(IconsFontAwesome5.ICON_USERS + "Party##PartyTab"):
                    HeroAI_FloatingWindows.selected_tab = HeroAI_FloatingWindows.TabType.party
                    PyImGui.end_tab_item()
                ImGui.show_tooltip("Party")
                if PyImGui.begin_tab_item(IconsFontAwesome5.ICON_RUNNING + "HeroAI##controlpanelTab"):
                    HeroAI_FloatingWindows.selected_tab = HeroAI_FloatingWindows.TabType.control_panel
                    PyImGui.end_tab_item()
                ImGui.show_tooltip("HeroAI Control Panel")
                if PyImGui.begin_tab_item(IconsFontAwesome5.ICON_BULLHORN + "##messagingTab"):
                    HeroAI_FloatingWindows.selected_tab = HeroAI_FloatingWindows.TabType.messaging
                    PyImGui.end_tab_item()
                ImGui.show_tooltip("Messaging")
                if Map.IsOutpost():
                    if PyImGui.begin_tab_item(IconsFontAwesome5.ICON_USER_PLUS + "##candidatesTab"):
                        HeroAI_FloatingWindows.selected_tab = HeroAI_FloatingWindows.TabType.candidates
                        PyImGui.end_tab_item()
                    ImGui.show_tooltip("Candidates")
                else:
                    if PyImGui.begin_tab_item(IconsFontAwesome5.ICON_FLAG + "##flaggingTab"):
                        HeroAI_FloatingWindows.selected_tab = HeroAI_FloatingWindows.TabType.flagging
                        PyImGui.end_tab_item()
                    ImGui.show_tooltip("Flagging")
                if PyImGui.begin_tab_item(IconsFontAwesome5.ICON_COGS + "##configTab"):
                    HeroAI_FloatingWindows.selected_tab = HeroAI_FloatingWindows.TabType.config
                    PyImGui.end_tab_item()
                ImGui.show_tooltip("Config")
                PyImGui.end_tab_bar()
        PyImGui.end()

        ImGui.PopTransparentWindow()
            
        HeroAI_BaseUI.DrawFramedContent(cached_data, content_frame_id)

    @staticmethod
    def DrawFollowerUI(cached_data: CacheData):
        own_party_number = GLOBAL_CACHE.Party.GetOwnPartyNumber()
        if own_party_number <= 0:
            return

        party_window_frame = WindowFrames["PartyWindow"]

        def advance_rainbow_color(tick: int) -> tuple[int, Color]:
            tick += 2
            r = int((math.sin(tick * 0.05) * 0.5 + 0.5) * 255)
            g = int((math.sin(tick * 0.05 + 2.0) * 0.5 + 0.5) * 255)
            b = int((math.sin(tick * 0.05 + 4.0) * 0.5 + 0.5) * 255)
            return tick, Color(r, g, b, 255).copy()

        HeroAI_BaseUI.color_tick, HeroAI_BaseUI.outline_color = advance_rainbow_color(HeroAI_BaseUI.color_tick)
        party_window_frame.DrawFrameOutline(HeroAI_BaseUI.outline_color.to_color(), 3)

        left, top, right, _bottom = party_window_frame.GetCoords()
        width = right - left - 5

        flags = ImGui.PushTransparentWindow()
        PyImGui.set_next_window_pos(left, top - 35)
        PyImGui.set_next_window_size(width, 35)
        if PyImGui.begin("embedded contorl panel", True, flags):
            if PyImGui.begin_tab_bar("HeroAITabs"):
                if PyImGui.begin_tab_item(IconsFontAwesome5.ICON_USERS + "HeroAI##HeroAITab"):
                    PyImGui.end_tab_item()
                ImGui.show_tooltip("HeroAI is Active. \nRefer to Leaders control panel for options.")
                PyImGui.end_tab_bar()
        PyImGui.end()
        ImGui.PopTransparentWindow()

        HeroAI_BaseUI.DrawFramedContent(cached_data, party_window_frame.GetFrameID())

    @staticmethod
    def DrawControlPanelWindow(cached_data: CacheData):
        if not HeroAI_FloatingWindows.settings.ShowControlPanelWindow:
            return
        if GLOBAL_CACHE.Party.GetOwnPartyNumber() != 0:
            return

        def _close_spacing():
            PyImGui.dummy(0, 5)
            PyImGui.separator()
            PyImGui.dummy(0, 5)

        if ImGui.Begin(ini_key=cached_data.ini_key, name="HeroAI Control Panel", p_open=True, flags=PyImGui.WindowFlags.AlwaysAutoResize):
            if PyImGui.begin_child("ControlPanelChild", (200, 138), False, PyImGui.WindowFlags.AlwaysAutoResize):
                style = ImGui.get_style()
                style.ItemSpacing.push_style_var(2, 2)
                style.CellPadding.push_style_var(2, 2)

                HeroAI_BaseUI.DrawPanelButtons(cached_data.account_email, cached_data.global_options, set_global=True)
                _close_spacing()
                HeroAI_BaseUI.DrawButtonBar(cached_data)

                style.CellPadding.pop_style_var()
                style.ItemSpacing.pop_style_var()
                PyImGui.end_child()

            PyImGui.separator()
            if PyImGui.tree_node("Players"):
                style = ImGui.get_style()
                style.ItemSpacing.push_style_var(2, 2)
                style.CellPadding.push_style_var(2, 2)
                sorted_by_party_position = sorted(cached_data.party.accounts.values(), key=lambda acc: acc.AgentPartyData.PartyPosition)
                index = 0

                for account in sorted_by_party_position:
                    if account and account.IsSlotActive and not account.IsHero and account.AgentPartyData.PartyID == GLOBAL_CACHE.Party.GetPartyID():
                        index += 1
                        original_game_option = cached_data.party.options.get(account.AgentData.AgentID)
                        if PyImGui.tree_node(f"{index}. {account.AgentData.CharacterName}##ControlPlayer{index}"):
                            if original_game_option is not None:
                                HeroAI_BaseUI.DrawPanelButtons(account.AccountEmail, original_game_option)
                            PyImGui.new_line()
                            PyImGui.tree_pop()

                PyImGui.tree_pop()
                style.CellPadding.pop_style_var()
                style.ItemSpacing.pop_style_var()

        ImGui.End(cached_data.ini_key)

    @staticmethod
    def draw_debug_window(heroai_bt=None):
        visible, HeroAI_BaseUI.show_debug = PyImGui.begin_with_close("HeroAI Debug", HeroAI_BaseUI.show_debug, 0)
        if visible and heroai_bt is not None:
            heroai_bt.draw()
        PyImGui.end()
        
    @staticmethod
    def DrawCandidateWindow(cached_data:CacheData):
        def _OnSameMap(self_account, candidate):
            if (candidate.MapID == self_account.MapID and
                candidate.MapRegion == self_account.MapRegion and
                candidate.MapDistrict == self_account.MapDistrict):
                return True
            return False
        
        def _OnSameParty(self_account, candidate):
            if self_account.PartyID == candidate.PartyID:
                return True
            return False
            
        table_flags = PyImGui.TableFlags.Sortable | PyImGui.TableFlags.Borders | PyImGui.TableFlags.RowBg
        if PyImGui.begin_table("CandidateTable", 2, table_flags):
            # Setup columns
            PyImGui.table_setup_column("Command", PyImGui.TableColumnFlags.NoSort)
            PyImGui.table_setup_column("Candidate", PyImGui.TableColumnFlags.NoFlag)
            PyImGui.table_headers_row()

            account_email = Player.GetAccountEmail()
            self_account = GLOBAL_CACHE.ShMem.GetAccountDataFromEmail(account_email)
            if not self_account:
                PyImGui.text("No account data found.")
                PyImGui.end_table()
                return
            
            accounts = cached_data.party.accounts.values()
            
            for account in accounts:
                if account.AccountEmail == account_email:
                    continue
                
                if _OnSameMap(self_account, account) and not _OnSameParty(self_account, account):
                    PyImGui.table_next_row()
                    PyImGui.table_next_column()
                    if PyImGui.button(f"Invite##invite_{account.AgentData.AgentID}"):
                        GLOBAL_CACHE.Party.Players.InvitePlayer(account.AgentData.CharacterName)
                        GLOBAL_CACHE.ShMem.SendMessage(account_email, account.AccountEmail,SharedCommandType.InviteToParty, (self_account.AgentData.AgentID,0,0,0))
                    PyImGui.table_next_column()
                    PyImGui.text(f"{account.AgentData.CharacterName}")
                else:
                    if not _OnSameMap(self_account, account):
                        PyImGui.table_next_row()
                        PyImGui.table_next_column()
                        if PyImGui.button(f"Summon##summon_{account.AgentData.AgentID}"):
                            GLOBAL_CACHE.ShMem.SendMessage(account_email, account.AccountEmail,SharedCommandType.TravelToMap, (self_account.AgentData.Map.MapID,self_account.AgentData.Map.Region,self_account.AgentData.Map.District,0))
                        PyImGui.table_next_column()
                        PyImGui.text(f"{account.AgentData.CharacterName}")
            PyImGui.end_table()

    @staticmethod
    def DrawMultiboxTools(cached_data:CacheData):
        global MAX_NUM_PLAYERS
        cached_data.HeroAI_windows.tools_window.initialize()

        if cached_data.HeroAI_windows.tools_window.begin():
            if Map.IsOutpost() and Player.GetAgentID() == GLOBAL_CACHE.Party.GetPartyLeaderID():
                if PyImGui.collapsing_header("Party Setup",PyImGui.TreeNodeFlags.DefaultOpen):
                    HeroAI_BaseUI.DrawCandidateWindow(cached_data)
            if Map.IsExplorable() and Player.GetAgentID() == GLOBAL_CACHE.Party.GetPartyLeaderID():
                if PyImGui.collapsing_header("Flagging"):
                    HeroAI_BaseUI.DrawFlaggingWindow(cached_data)

            if PyImGui.collapsing_header("Debug Options"):
                HeroAI_BaseUI.draw_debug_window(cached_data)
    
        cached_data.HeroAI_windows.tools_window.process_window()
        cached_data.HeroAI_windows.tools_window.end()            
        
    


        
