from operator import index
from Py4GWCoreLib import GLOBAL_CACHE, Map,IconsFontAwesome5, ImGui, Utils, Overlay, Range, SharedCommandType, ConsoleLog, Color
from Py4GWCoreLib import UIManager, ModelID, GLOBAL_CACHE, WindowFrames
from Py4GWCoreLib import Agent
from Py4GWCoreLib import (Routines, ActionQueueManager,Key, Keystroke, ThrottledTimer)
from HeroAI.constants import (FOLLOW_DISTANCE_OUT_OF_COMBAT, MAX_NUM_PLAYERS, MELEE_RANGE_VALUE, PARTY_WINDOW_FRAME_EXPLORABLE_OFFSETS,
                              PARTY_WINDOW_FRAME_OUTPOST_OFFSETS, PARTY_WINDOW_HASH, RANGED_RANGE_VALUE)
from Py4GWCoreLib.ImGui_src.WindowModule import WindowModule
from Py4GWCoreLib.GlobalCache.SharedMemory import SharedMessage
from Py4GW_widget_manager import WidgetHandler

from .constants import MAX_NUM_PLAYERS, NUMBER_OF_SKILLS
from .types import SkillType, SkillNature, Skilltarget, GameOptionStruct
from .globals import capture_mouse_timer, show_area_rings, show_hero_follow_grid, show_distance_on_followers, hero_formation, capture_hero_flag, capture_flag_all, capture_hero_index
from .utils import IsHeroFlagged, DrawFlagAll, DrawHeroFlag, DistanceFromWaypoint
from HeroAI.settings import Settings

from HeroAI.ui import (draw_combined_hero_panel, draw_command_panel, draw_configure_window, draw_dialog_overlay, 
                       draw_hero_panel, draw_hotbars, draw_party_overlay, draw_party_search_overlay, draw_skip_cutscene_overlay)

from .cache_data import CacheData
from enum import Enum

import math
import PyImGui

#region FloatingWindows

class HeroAI_FloatingWindows():
    # TabType
    class TabType(Enum):
        party = 1
        control_panel = 2
        candidates = 3
        flagging = 4
        config = 5
        debug = 6
        messaging = 7
        
    selected_tab: TabType = TabType.party
    settings : Settings = Settings()
    SETTINGS_THROTTLE = ThrottledTimer(50)
    ACCOUNT_THROTTLE = ThrottledTimer(500)
    hero_windows : dict[str, WindowModule] = {}
    messages : list[tuple[int, SharedMessage]] = []
    widget_handler = WidgetHandler()
    init_success:bool  = False
    module_info = None
    accounts = GLOBAL_CACHE.ShMem.GetAllAccountData()
    
    configure_window : WindowModule = WindowModule(
        module_name="HeroAI Configuration",
        window_name="HeroAI Configuration",
        window_size=(400, 300),
        window_pos=(200, 200),
        can_close=True,
    )
    command_panel_window : WindowModule = WindowModule(
        module_name="HeroAI Command Panel",
        window_name="heroai_command_panel",
        window_size=(400, 300),
        window_pos=(200, 200),
        can_close=False,
        window_flags=PyImGui.WindowFlags(PyImGui.WindowFlags.NoTitleBar | PyImGui.WindowFlags.AlwaysAutoResize),
    )
    
    @staticmethod
    def draw_Targeting_floating_buttons(cached_data: CacheData):
        if not HeroAI_FloatingWindows.settings.ShowFloatingTargets:
            return
        
        if not cached_data.option_show_floating_targets:
            return
        if not Map.IsExplorable():
            return
        player_pos = GLOBAL_CACHE.Player.GetXY()
        enemy_array = Routines.Agents.GetFilteredEnemyArray(player_pos[0], player_pos[1], Range.SafeCompass.value)

        if len(enemy_array) == 0:
            return

        Overlay().BeginDraw()
        for agent_id in enemy_array:
            x, y, z = Agent.GetXYZ(agent_id)
            screen_x, screen_y = Overlay.WorldToScreen(x, y, z + 25)
            if ImGui.floating_button(
                f"{IconsFontAwesome5.ICON_CROSSHAIRS}", name=agent_id, x=screen_x - 12, y=screen_y - 12, width=25, height=25
            ):
                GLOBAL_CACHE.Player.ChangeTarget(agent_id)
                GLOBAL_CACHE.Player.Interact(agent_id, True)
                ActionQueueManager().AddAction("ACTION", Keystroke.PressAndReleaseCombo, [Key.Ctrl.value, Key.Space.value])
        Overlay().EndDraw()

    @staticmethod
    def DrawFramedContent(cached_data: CacheData, content_frame_id):
        
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

        def control_panel_case(cached_data):
            own_party_number = GLOBAL_CACHE.Party.GetOwnPartyNumber()
            hero_ai_vars = cached_data.HeroAI_vars
            if own_party_number == 0:
                # leader control panel
                game_option = HeroAI_Windows.DrawPanelButtons(hero_ai_vars.global_control_game_struct)
                HeroAI_Windows.CompareAndSubmitGameOptions(cached_data, game_option)

                if PyImGui.collapsing_header("Player Control"):
                    for index in range(MAX_NUM_PLAYERS):
                        curr_hero = hero_ai_vars.all_player_struct[index]
                        if curr_hero.IsActive and not curr_hero.IsHero:
                            original_game_option = hero_ai_vars.all_game_option_struct[index]
                            login_number = GLOBAL_CACHE.Party.Players.GetLoginNumberByAgentID(curr_hero.PlayerID)
                            player_name = GLOBAL_CACHE.Party.Players.GetPlayerNameByLoginNumber(login_number)
                            if PyImGui.tree_node(f"{player_name}##ControlPlayer{index}"):
                                game_option = HeroAI_Windows.DrawPanelButtons(original_game_option)
                                HeroAI_Windows.SubmitGameOptions(cached_data, index, game_option, original_game_option)
                                PyImGui.tree_pop()
            else:
                # follower control panel
                original_game_option = hero_ai_vars.all_game_option_struct[own_party_number]
                game_option = HeroAI_Windows.DrawPanelButtons(original_game_option)
                HeroAI_Windows.SubmitGameOptions(cached_data, own_party_number, game_option, original_game_option)

        if PyImGui.begin("##heroai_framed_content", True, flags):
            match HeroAI_FloatingWindows.selected_tab:
                case HeroAI_FloatingWindows.TabType.control_panel:
                    control_panel_case(cached_data)
                case HeroAI_FloatingWindows.TabType.candidates:
                    HeroAI_Windows.DrawCandidateWindow(cached_data)
                case HeroAI_FloatingWindows.TabType.flagging:
                    HeroAI_Windows.DrawFlaggingWindow(cached_data)
                case HeroAI_FloatingWindows.TabType.config:
                    HeroAI_Windows.DrawOptions(cached_data)
                case HeroAI_FloatingWindows.TabType.messaging:
                    # Placeholder for messaging tab
                    HeroAI_Windows.DrawMessagingOptions(cached_data)

        PyImGui.end()
        PyImGui.pop_style_var(1)

    @staticmethod
    def DrawEmbeddedWindow(cached_data: CacheData):
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
        HeroAI_FloatingWindows.DrawFramedContent(cached_data, content_frame_id)

    @staticmethod
    def DistanceToDestination(cached_data: CacheData):
        account = GLOBAL_CACHE.ShMem.GetAccountDataFromEmail(cached_data.account_email)
        if not account:
            return 0.0
        
        is_flagged = IsHeroFlagged(cached_data, account.PartyPosition)
        player_structs = cached_data.HeroAI_vars.all_player_struct
        data = player_structs[account.PartyPosition] if player_structs and len(player_structs) > account.PartyPosition else None
        
        if not data:
            return 0.0 
        
        destination = (data.FlagPosX, data.FlagPosY) if is_flagged else Agent.GetXY(GLOBAL_CACHE.Party.GetPartyLeaderID())
        return Utils.Distance(destination, Agent.GetXY(GLOBAL_CACHE.Player.GetAgentID()))

    @staticmethod
    def _handle_settings():
        if HeroAI_FloatingWindows.SETTINGS_THROTTLE.IsExpired():
            HeroAI_FloatingWindows.SETTINGS_THROTTLE.Reset()
                            
            if not HeroAI_FloatingWindows.settings.ensure_initialized(): 
                HeroAI_FloatingWindows.SETTINGS_THROTTLE.SetThrottleTime(50)                              
                HeroAI_FloatingWindows.hero_windows.clear()
                info = HeroAI_FloatingWindows.settings.HeroPanelPositions.get(HeroAI_FloatingWindows.command_panel_window.window_name, Settings.HeroPanelInfo())                
                HeroAI_FloatingWindows.command_panel_window.window_pos = (info.x, info.y)
                HeroAI_FloatingWindows.command_panel_window.first_run = True             
                return
            
            elif HeroAI_FloatingWindows.SETTINGS_THROTTLE.throttle_time != 1000:
                HeroAI_FloatingWindows.SETTINGS_THROTTLE.SetThrottleTime(1000)
            
            HeroAI_FloatingWindows.settings.write_settings()
            
    @staticmethod
    def combined_hero_panel(own_data, cached_data: CacheData):
        identifier = "combined_hero_panel"
        accounts = GLOBAL_CACHE.ShMem.GetAllAccountData()
        if not HeroAI_FloatingWindows.settings.ShowPanelOnlyOnLeaderAccount or own_data.PlayerIsPartyLeader:
            if HeroAI_FloatingWindows.settings.ShowHeroPanels:
                messages = GLOBAL_CACHE.ShMem.GetAllMessages()
            
                if HeroAI_FloatingWindows.settings.CombinePanels:            
                    if not identifier in HeroAI_FloatingWindows.hero_windows:
                        info = HeroAI_FloatingWindows.settings.HeroPanelPositions.get(identifier, Settings.HeroPanelInfo())
                        HeroAI_FloatingWindows.hero_windows[identifier] = WindowModule(
                            module_name=f"HeroAI - {identifier}",
                            window_name=f"Heroes##HeroAI - {identifier}",
                            window_pos=(info.x, info.y),
                            collapse=info.collapsed,
                            can_close=True,
                        )
                        HeroAI_FloatingWindows.settings.HeroPanelPositions[identifier] = info
                        
                    open = HeroAI_FloatingWindows.hero_windows[identifier].begin(True, PyImGui.WindowFlags.AlwaysAutoResize)
                
                for account in accounts:
                    if not account.AccountEmail:
                        continue
                
                    if account.AccountEmail == GLOBAL_CACHE.Player.GetAccountEmail() and not HeroAI_FloatingWindows.settings.ShowLeaderPanel:
                        continue
                    
                    if not HeroAI_FloatingWindows.settings.CombinePanels:
                        if not account.AccountEmail in HeroAI_FloatingWindows.hero_windows:
                            info = HeroAI_FloatingWindows.settings.HeroPanelPositions.get(account.AccountEmail.lower(), Settings.HeroPanelInfo())
                            HeroAI_FloatingWindows.hero_windows[account.AccountEmail] = WindowModule(
                                module_name=f"HeroAI - {account.AccountEmail}",
                                window_name=f"##HeroAI - {account.AccountEmail}",
                                window_pos=(info.x, info.y),
                                collapse=info.collapsed,
                                can_close=True,
                            )
                            HeroAI_FloatingWindows.settings.HeroPanelPositions[account.AccountEmail] = info
                            
                        draw_hero_panel(HeroAI_FloatingWindows.hero_windows[account.AccountEmail], account, cached_data, messages)
                    else:                    
                        draw_combined_hero_panel(account, cached_data, messages)
                        
                if HeroAI_FloatingWindows.settings.CombinePanels:
                    HeroAI_FloatingWindows.hero_windows[identifier].end()
                    
                    if HeroAI_FloatingWindows.hero_windows[identifier].changed:
                        info = HeroAI_FloatingWindows.settings.HeroPanelPositions.get(identifier, Settings.HeroPanelInfo())
                        info.x = round(HeroAI_FloatingWindows.hero_windows[identifier].window_pos[0])
                        info.y = round(HeroAI_FloatingWindows.hero_windows[identifier].window_pos[1])
                        info.collapsed = HeroAI_FloatingWindows.hero_windows[identifier].collapse
                        info.open = HeroAI_FloatingWindows.hero_windows[identifier].open
                        HeroAI_FloatingWindows.settings.HeroPanelPositions[identifier] = info
                        HeroAI_FloatingWindows.settings.save_settings()
        
    @staticmethod
    def show_ui(cached_data: CacheData):
        show_ui = not UIManager.IsWorldMapShowing() and not Map.IsMapLoading() and not Map.IsInCinematic() and not GLOBAL_CACHE.Player.InCharacterSelectScreen()
        if show_ui:  
            own_data = GLOBAL_CACHE.ShMem.GetAccountDataFromEmail(cached_data.account_email)
            if not own_data:
                return
            HeroAI_FloatingWindows.accounts = GLOBAL_CACHE.ShMem.GetAllAccountData()
            HeroAI_FloatingWindows.combined_hero_panel(own_data , cached_data)

            if HeroAI_FloatingWindows.settings.ShowPartyOverlay:
                draw_party_overlay(HeroAI_FloatingWindows.accounts, HeroAI_FloatingWindows.hero_windows)
                
            if HeroAI_FloatingWindows.settings.ShowPartySearchOverlay:
                draw_party_search_overlay(HeroAI_FloatingWindows.accounts, cached_data)
            
            if (HeroAI_FloatingWindows.settings.ShowCommandPanel and (own_data.PlayerIsPartyLeader or not HeroAI_FloatingWindows.settings.ShowCommandPanelOnlyOnLeaderAccount) 
                ):
                draw_command_panel(HeroAI_FloatingWindows.command_panel_window, HeroAI_FloatingWindows.accounts, cached_data)
            
            if HeroAI_FloatingWindows.settings.CommandHotBars:
                draw_hotbars(HeroAI_FloatingWindows.accounts, cached_data)
                
            draw_dialog_overlay(HeroAI_FloatingWindows.accounts, cached_data, HeroAI_FloatingWindows.messages)
 
    @staticmethod
    def disable_main_automation(cached_data: CacheData):
        own_data = GLOBAL_CACHE.ShMem.GetAccountDataFromEmail(cached_data.account_email)
        if own_data and own_data.PlayerIsPartyLeader and HeroAI_FloatingWindows.settings.DisableAutomationOnLeaderAccount:        
            hero_ai_data = GLOBAL_CACHE.ShMem.GetGerHeroAIOptionsByPartyNumber(own_data.PartyPosition)
                    
            if hero_ai_data is not None:
                hero_ai_data.Following = False
                hero_ai_data.Avoidance = False
                hero_ai_data.Looting = False
                hero_ai_data.Targeting = False
                hero_ai_data.Combat = False
                GLOBAL_CACHE.ShMem.SetHeroAIOptions(own_data.AccountEmail, hero_ai_data)
                return True
        return False

    
    @staticmethod
    def update():
        import Py4GW
        HeroAI_FloatingWindows._handle_settings()
        if not HeroAI_FloatingWindows.settings._initialized:
            return
        else:
            if not HeroAI_FloatingWindows.init_success:
                HeroAI_FloatingWindows.init_success = True
                Py4GW.Console.Log("HeroAI", "HeroAI initialized successfully.", Py4GW.Console.MessageType.Info)
        
            
                   
#region Windows
class HeroAI_Windows():
    skill_slot = 0
    HeroFlags: list[bool] = [False, False, False, False, False, False, False, False, False]
    AllFlag = False
    ClearFlags = False
    one_time_set_flag = False
    slot_to_write = 0
    draw_fake_flag = True
    
    outline_color:Color = Color(255, 255, 255, 255)
    color_tick = 0
    
    class ButtonColor:
        def __init__(self, button_color:Color, hovered_color:Color, active_color:Color, texture_path=""):
            self.button_color = button_color
            self.hovered_color = hovered_color
            self.active_color = active_color
            self.texture_path = texture_path
        

    ButtonColors = {
        "Resign": ButtonColor(button_color=Color(90,0,10,255), hovered_color=Color(160,0,15,255), active_color=Color(210,0,20,255)),  
        "PixelStack": ButtonColor(button_color=Color(90,0,10,255), hovered_color=Color(160,0,15,255), active_color=Color(190,0,20,255)),
        "Flag": ButtonColor(button_color=Color(90,0,10,255), hovered_color=Color(160,0,15,255), active_color=Color(190,0,20,255)),
        "ClearFlags": ButtonColor(button_color=Color(90,0,10,255), hovered_color=Color(160,0,15,255), active_color=Color(190,0,20,255)),
        "Celerity": ButtonColor(button_color = Color(129, 33, 188, 255), hovered_color = Color(165, 100, 200, 255), active_color = Color(135, 225, 230, 255),texture_path="Textures\\Consumables\\Trimmed\\Essence_of_Celerity.png"),  
        "GrailOfMight": ButtonColor(button_color=Color(70,0,10,255), hovered_color=Color(160,0,15,255), active_color=Color(252,225,115,255), texture_path="Textures\\Consumables\\Trimmed\\Grail_of_Might.png"),
        "ArmorOfSalvation": ButtonColor(button_color = Color(96, 60, 15, 255),hovered_color = Color(187, 149, 38, 255),active_color = Color(225, 150, 0, 255), texture_path="Textures\\Consumables\\Trimmed\\Armor_of_Salvation.png"),
        "CandyCane": ButtonColor(button_color = Color(63, 91, 54, 255),hovered_color = Color(149, 72, 34, 255),active_color = Color(96, 172, 28, 255), texture_path="Textures\\Consumables\\Trimmed\\Rainbow_Candy_Cane.png"),
        "BirthdayCupcake": ButtonColor(button_color = Color(138, 54, 80, 255),hovered_color = Color(255, 186, 198, 255),active_color = Color(205, 94, 215, 255), texture_path="Textures\\Consumables\\Trimmed\\Birthday_Cupcake.png"),
        "GoldenEgg": ButtonColor(button_color = Color(245, 227, 143, 255),hovered_color = Color(253, 248, 234, 255),active_color = Color(129, 82, 35, 255), texture_path="Textures\\Consumables\\Trimmed\\Golden_Egg.png"),
        "CandyCorn": ButtonColor(button_color = Color(239, 174, 33, 255),hovered_color = Color(206, 178, 148, 255),active_color = Color(239, 77, 16, 255), texture_path="Textures\\Consumables\\Trimmed\\Candy_Corn.png"),
        "CandyApple": ButtonColor(button_color = Color(75, 26, 28, 255),hovered_color = Color(202, 60, 88, 255),active_color = Color(179, 0, 39, 255), texture_path="Textures\\Consumables\\Trimmed\\Candy_Apple.png"),
        "PumpkinPie": ButtonColor(button_color = Color(224, 176, 126, 255),hovered_color = Color(226, 209, 210, 255),active_color = Color(129, 87, 54, 255), texture_path="Textures\\Consumables\\Trimmed\\Slice_of_Pumpkin_Pie.png"),
        "DrakeKabob": ButtonColor(button_color = Color(28, 28, 28, 255),hovered_color = Color(190, 187, 184, 255),active_color = Color(94, 26, 13, 255), texture_path="Textures\\Consumables\\Trimmed\\Drake_Kabob.png"),
        "SkalefinSoup": ButtonColor(button_color = Color(68, 85, 142, 255),hovered_color = Color(255, 255, 107, 255),active_color = Color(106, 139, 51, 255), texture_path="Textures\\Consumables\\Trimmed\\Bowl_of_Skalefin_Soup.png"),
        "PahnaiSalad": ButtonColor(button_color = Color(113, 43, 25, 255),hovered_color = Color(185, 157, 90, 255),active_color = Color(137, 175, 10, 255), texture_path="Textures\\Consumables\\Trimmed\\Pahnai_Salad.png"),
        "WarSupplies": ButtonColor(button_color = Color(51, 26, 13, 255),hovered_color = Color(113, 43, 25, 255),active_color = Color(202, 115, 77, 255), texture_path="Textures\\Consumables\\Trimmed\\War_Supplies.png"),
        "Alcohol": ButtonColor(button_color = Color(58, 41, 50, 255),hovered_color = Color(169, 145, 111, 255),active_color = Color(173, 173, 156, 255), texture_path="Textures\\Consumables\\Trimmed\\Dwarven_Ale.png"),
        "Blank": ButtonColor(button_color= Color(0, 0, 0, 0), hovered_color=Color(0, 0, 0, 0), active_color=Color(0, 0, 0, 0)),
    }

    show_confirm_dialog = False
    dialog_options = []
    target_id = 0
        
    @staticmethod
    def DrawBuffWindow(cached_data:CacheData):
        global MAX_NUM_PLAYERS
        if not Map.IsExplorable():
            return

        for index in range(MAX_NUM_PLAYERS):
            player_struct = cached_data.HeroAI_vars.all_player_struct[index]
            if player_struct.IsActive:
                if Agent.IsPlayer(player_struct.PlayerID):
                    player_name = Agent.GetNameByID(player_struct.PlayerID)
                else:
                    player_name = GLOBAL_CACHE.Party.Heroes.GetNameByAgentID(player_struct.PlayerID)

                if PyImGui.tree_node(f"{player_name}##DebugBuffsPlayer{index}"):
                    # Retrieve buffs for the player
                    player_buffs = cached_data.HeroAI_vars.shared_memory_handler.get_agent_buffs(player_struct.PlayerID)
                    headers = ["Skill ID", "Skill Name"]
                    data = [(skill_id, GLOBAL_CACHE.Skill.GetName(skill_id)) for skill_id in player_buffs]
                    ImGui.table(f"{player_name} Buffs", headers, data)
                    PyImGui.tree_pop()

    @staticmethod
    def DrawPrioritizedSkills(cached_data:CacheData):
        PyImGui.text(f"skill pointer: : {cached_data.combat_handler.skill_pointer}")
        in_casting_routine = cached_data.combat_handler.InCastingRoutine()
        PyImGui.text_colored(f"InCastingRoutine: {in_casting_routine}",Utils.TrueFalseColor(not in_casting_routine))
        PyImGui.text(f"aftercast_timer: {cached_data.combat_handler.aftercast_timer.GetElapsedTime()}")

        if PyImGui.begin_tab_bar("OrderedSkills"):
            skills = cached_data.combat_handler.GetSkills()
            for i in range(len(skills)):
                slot = i
                skill = skills[i]
            
                if PyImGui.begin_tab_item(GLOBAL_CACHE.Skill.GetName(skill.skill_id)):
                    if PyImGui.tree_node(f"Custom Properties"):
                        # Display skill properties
                        PyImGui.text(f"Skill ID: {skill.skill_id}")
                        PyImGui.text(f"Skill Type: {SkillType(skill.custom_skill_data.SkillType).name}")
                        PyImGui.text(f"Skill Nature: {SkillNature(skill.custom_skill_data.Nature).name}")
                        PyImGui.text(f"Skill Target: {Skilltarget(skill.custom_skill_data.TargetAllegiance).name}")

                        PyImGui.separator()
                        PyImGui.text("Cast Conditions:")

                        # Dynamically display attributes of CastConditions
                        conditions = skill.custom_skill_data.Conditions
                        for attr_name, attr_value in vars(conditions).items():
                            # Check if the attribute is a non-empty list or True for non-list attributes
                            if isinstance(attr_value, list) and attr_value:  # Non-empty list
                                PyImGui.text(f"{attr_name}: {', '.join(map(str, attr_value))}")
                            elif isinstance(attr_value, bool) and attr_value:  # True boolean
                                PyImGui.text(f"{attr_name}: True")
                            elif isinstance(attr_value, (int, float)) and attr_value != 0:  # Non-zero numbers
                                PyImGui.text(f"{attr_name}: {attr_value}")
                        PyImGui.tree_pop()

                    
                    if PyImGui.tree_node(f"Combat debug"):
                    
                        is_skill_ready = cached_data.combat_handler.IsSkillReady(slot)
                        is_ooc_skill = cached_data.combat_handler.IsOOCSkill(slot)  
                        is_ready_to_cast, v_target = cached_data.combat_handler.IsReadyToCast(HeroAI_Windows.skill_slot)

                        self_id = GLOBAL_CACHE.Player.GetAgentID()

                        pet_id = GLOBAL_CACHE.Party.Pets.GetPetID(GLOBAL_CACHE.Player.GetAgentID())

                        headers = ["Self", "Nearest Enemy", "Nearest Ally", "Nearest Item", "Nearest Spirit", "Nearest Minion", "Nearest Corpse", "Pet"]

                        data = [
                            (self_id, pet_id)
                        ]

                        ImGui.table("Target Debug Table", headers, data)

                        PyImGui.text(f"Target to Cast: {v_target}")

                        PyImGui.separator()
                        
                        PyImGui.text(f"InAggro: {cached_data.data.in_aggro}")
                        PyImGui.text(f"stayt_alert_timer: {cached_data.stay_alert_timer.GetElapsedTime()}")
                        
                        PyImGui.separator()

                        PyImGui.text_colored(f"IsSkillReady: {is_skill_ready}",Utils.TrueFalseColor(is_skill_ready))
                        
                        PyImGui.text_colored(f"IsReadyToCast: {is_ready_to_cast}", Utils.TrueFalseColor(is_ready_to_cast))
                        if PyImGui.tree_node(f"IsReadyToCast: {is_ready_to_cast}"): 
                            is_casting = Agent.IsCasting(GLOBAL_CACHE.Player.GetAgentID())
                            casting_skill = Agent.GetCastingSkill(GLOBAL_CACHE.Player.GetAgentID())
                            skillbar_casting = GLOBAL_CACHE.SkillBar.GetCasting()
                            skillbar_recharge = cached_data.combat_handler.skills[HeroAI_Windows.skill_slot].skillbar_data.recharge
                            player_agent_id = GLOBAL_CACHE.Player.GetAgentID()
                            current_energy = Agent.GetEnergy(player_agent_id) * Agent.GetMaxEnergy(player_agent_id)
                            ordered_skill = cached_data.combat_handler.GetOrderedSkill(HeroAI_Windows.skill_slot)
                            if ordered_skill:                        
                                energy_cost = GLOBAL_CACHE.Skill.Data.GetEnergyCost(ordered_skill.skill_id)
                                current_hp = Agent.GetHealth(GLOBAL_CACHE.Player.GetAgentID())
                                target_hp = ordered_skill.custom_skill_data.Conditions.SacrificeHealth
                                health_cost = GLOBAL_CACHE.Skill.Data.GetHealthCost(ordered_skill.skill_id)

                                adrenaline_required = GLOBAL_CACHE.Skill.Data.GetAdrenaline(ordered_skill.skill_id)
                                adrenaline_a = ordered_skill.skillbar_data.adrenaline_a

                                current_overcast = Agent.GetOvercast(GLOBAL_CACHE.Player.GetAgentID())
                                overcast_target = ordered_skill.custom_skill_data.Conditions.Overcast
                                skill_overcast = GLOBAL_CACHE.Skill.Data.GetOvercast(ordered_skill.skill_id)

                                are_cast_conditions_met = cached_data.combat_handler.AreCastConditionsMet(HeroAI_Windows.skill_slot,v_target)
                                spirit_buff_exists = cached_data.combat_handler.SpiritBuffExists(ordered_skill.skill_id)
                                has_effect = cached_data.combat_handler.HasEffect(v_target, ordered_skill.skill_id)

                                PyImGui.text_colored(f"IsCasting: {is_casting}", Utils.TrueFalseColor(not is_casting))
                                PyImGui.text_colored(f"CastingSkill: {casting_skill}", Utils.TrueFalseColor(not casting_skill != 0))
                                PyImGui.text_colored(f"SkillBar Casting: {skillbar_casting}", Utils.TrueFalseColor(not skillbar_casting != 0))
                                PyImGui.text_colored(f"SkillBar recharge: {skillbar_recharge}", Utils.TrueFalseColor(skillbar_recharge == 0))  
                                PyImGui.text_colored(f"Energy: {current_energy} / Cost {energy_cost}", Utils.TrueFalseColor(current_energy >= energy_cost))
                                PyImGui.text_colored(f"Current HP: {current_hp} / Target HP: {target_hp} / Health Cost: {health_cost}", Utils.TrueFalseColor(health_cost == 0 or current_hp >= health_cost))
                                PyImGui.text_colored(f"Adrenaline Required: {adrenaline_required}", Utils.TrueFalseColor(adrenaline_required == 0 or (adrenaline_a >= adrenaline_required)))
                                PyImGui.text_colored(f"Current Overcast: {current_overcast} / Overcast Target: {overcast_target} / Skill Overcast: {skill_overcast}", Utils.TrueFalseColor(current_overcast >= overcast_target or skill_overcast == 0))
                            
                                PyImGui.text_colored(f"AreCastConditionsMet: {are_cast_conditions_met}", Utils.TrueFalseColor(are_cast_conditions_met))
                                PyImGui.text_colored(f"SpiritBuffExists: {spirit_buff_exists}", Utils.TrueFalseColor(not spirit_buff_exists))
                                PyImGui.text_colored(f"HasEffect: {has_effect}", Utils.TrueFalseColor(not has_effect))
                            PyImGui.tree_pop()

                        PyImGui.tree_pop()

                        PyImGui.text_colored(f"IsOOCSkill: {is_ooc_skill}", Utils.TrueFalseColor(is_ooc_skill))
                    
                    PyImGui.end_tab_item()
            PyImGui.end_tab_bar()

    @staticmethod
    def DrawFlags(cached_data:CacheData):
        global capture_flag_all, capture_hero_flag, capture_hero_index
        global one_time_set_flag
        
        if capture_hero_flag:        
            x, y, _ = Overlay().GetMouseWorldPos()
            if capture_flag_all:
                DrawFlagAll(x, y)
                pass
            else:
                DrawHeroFlag(x, y)
                
            if PyImGui.is_mouse_clicked(0) and one_time_set_flag:
                one_time_set_flag = False
                return

            if PyImGui.is_mouse_clicked(0) and not one_time_set_flag:
                if capture_hero_index > 0 and capture_hero_index <= GLOBAL_CACHE.Party.GetHeroCount():
                    if not capture_flag_all:   
                        agent_id = GLOBAL_CACHE.Party.Heroes.GetHeroAgentIDByPartyPosition(capture_hero_index)
                        GLOBAL_CACHE.Party.Heroes.FlagHero(agent_id, x, y)
                        one_time_set_flag = True
                else:
                    if capture_hero_index == 0:
                        hero_ai_index = 0
                        GLOBAL_CACHE.Party.Heroes.FlagAllHeroes(x, y)
                    else:
                        hero_ai_index = capture_hero_index - GLOBAL_CACHE.Party.GetHeroCount()
                    cached_data.HeroAI_vars.shared_memory_handler.set_player_property(hero_ai_index, "IsFlagged", True)
                    cached_data.HeroAI_vars.shared_memory_handler.set_player_property(hero_ai_index, "FlagPosX", x)
                    cached_data.HeroAI_vars.shared_memory_handler.set_player_property(hero_ai_index, "FlagPosY", y)
                    cached_data.HeroAI_vars.shared_memory_handler.set_player_property(hero_ai_index, "FollowAngle", Agent.GetRotationAngle(GLOBAL_CACHE.Party.GetPartyLeaderID()))
                    
                    one_time_set_flag = True

                capture_flag_all = False
                capture_hero_flag = False
                one_time_set_flag = False
                capture_mouse_timer.Stop()

        #All flag is handled by the game even with no heroes
        if cached_data.HeroAI_vars.all_player_struct[0].IsFlagged:
            DrawFlagAll(cached_data.HeroAI_vars.all_player_struct[0].FlagPosX, cached_data.HeroAI_vars.all_player_struct[0].FlagPosY)
            
        for i in range(1, MAX_NUM_PLAYERS):
            if cached_data.HeroAI_vars.all_player_struct[i].IsFlagged and cached_data.HeroAI_vars.all_player_struct[i].IsActive and not cached_data.HeroAI_vars.all_player_struct[i].IsHero:
                DrawHeroFlag(cached_data.HeroAI_vars.all_player_struct[i].FlagPosX,cached_data.HeroAI_vars.all_player_struct[i].FlagPosY)

        if HeroAI_Windows.ClearFlags:
            for i in range(MAX_NUM_PLAYERS):
                cached_data.HeroAI_vars.shared_memory_handler.set_player_property(i, "IsFlagged", False)
                cached_data.HeroAI_vars.shared_memory_handler.set_player_property(i, "FlagPosX", 0.0)
                cached_data.HeroAI_vars.shared_memory_handler.set_player_property(i, "FlagPosY", 0.0)
                cached_data.HeroAI_vars.shared_memory_handler.set_player_property(i, "FollowAngle", 0.0)
                GLOBAL_CACHE.Party.Heroes.UnflagHero(i)
            GLOBAL_CACHE.Party.Heroes.UnflagAllHeroes()
            HeroAI_Windows.ClearFlags = False
                
        
    @staticmethod
    def DrawFlaggingWindow(cached_data:CacheData):
        global AllFlag, capture_flag_all, capture_hero_flag, capture_hero_index, one_time_set_flag

        party_size = GLOBAL_CACHE.Party.GetPartySize()
        if party_size == 1:
            PyImGui.text("No Follower or Heroes to Flag.")
            return

        if PyImGui.collapsing_header("Flagging"):
            if PyImGui.begin_table("Flags",3):
                PyImGui.table_next_row()
                PyImGui.table_next_column()
                if party_size >= 2:
                    HeroAI_Windows.HeroFlags[0] = ImGui.toggle_button("1", IsHeroFlagged(cached_data,1), 30, 30)
                PyImGui.table_next_column()
                if party_size >= 3:
                    HeroAI_Windows.HeroFlags[1] = ImGui.toggle_button("2", IsHeroFlagged(cached_data,2),30,30)
                PyImGui.table_next_column()
                if party_size >= 4:
                    HeroAI_Windows.HeroFlags[2] = ImGui.toggle_button("3", IsHeroFlagged(cached_data,3),30,30)
                PyImGui.table_next_row()
                PyImGui.table_next_column()
                if party_size >= 5:
                    HeroAI_Windows.HeroFlags[3] = ImGui.toggle_button("4", IsHeroFlagged(cached_data,4),30,30)
                PyImGui.table_next_column()
                AllFlag = ImGui.toggle_button("All", IsHeroFlagged(cached_data,0), 30, 30)
                PyImGui.table_next_column()
                if party_size >= 6:
                    HeroAI_Windows.HeroFlags[4] = ImGui.toggle_button("5", IsHeroFlagged(cached_data,5),30,30)
                PyImGui.table_next_row()
                PyImGui.table_next_column()
                if party_size >= 7:
                    HeroAI_Windows.HeroFlags[5] = ImGui.toggle_button("6", IsHeroFlagged(cached_data,6),30,30)
                PyImGui.table_next_column()
                if party_size >= 8:
                    HeroAI_Windows.HeroFlags[6] = ImGui.toggle_button("7", IsHeroFlagged(cached_data,7), 30, 30)
                PyImGui.table_next_column()
                HeroAI_Windows.ClearFlags = ImGui.toggle_button("X", HeroAI_Windows.HeroFlags[7],30,30)
                PyImGui.end_table()
                    
                    
        if AllFlag != IsHeroFlagged(cached_data,0):
            capture_hero_flag = True
            capture_flag_all = True
            capture_hero_index = 0
            one_time_set_flag = False
            capture_mouse_timer.Start()

        for i in range(1, party_size):
            if HeroAI_Windows.HeroFlags[i-1] != IsHeroFlagged(cached_data,i):
                capture_hero_flag = True
                capture_flag_all = False
                capture_hero_index = i
                one_time_set_flag = False
                capture_mouse_timer.Start()
            
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

            account_email = GLOBAL_CACHE.Player.GetAccountEmail()
            self_account = GLOBAL_CACHE.ShMem.GetAccountDataFromEmail(account_email)
            if not self_account:
                PyImGui.text("No account data found.")
                PyImGui.end_table()
                return
            accounts = GLOBAL_CACHE.ShMem.GetAllAccountData()
            
            for account in accounts:
                if account.AccountEmail == account_email:
                    continue
                
                if _OnSameMap(self_account, account) and not _OnSameParty(self_account, account):
                    PyImGui.table_next_row()
                    PyImGui.table_next_column()
                    if PyImGui.button(f"Invite##invite_{account.PlayerID}"):
                        GLOBAL_CACHE.Party.Players.InvitePlayer(account.CharacterName)
                        GLOBAL_CACHE.ShMem.SendMessage(account_email, account.AccountEmail,SharedCommandType.InviteToParty, (self_account.PlayerID,0,0,0))
                    PyImGui.table_next_column()
                    PyImGui.text(f"{account.CharacterName}")
                else:
                    if not _OnSameMap(self_account, account):
                        PyImGui.table_next_row()
                        PyImGui.table_next_column()
                        if PyImGui.button(f"Summon##summon_{account.PlayerID}"):
                            GLOBAL_CACHE.ShMem.SendMessage(account_email, account.AccountEmail,SharedCommandType.TravelToMap, (self_account.MapID,self_account.MapRegion,self_account.MapDistrict,0))
                        PyImGui.table_next_column()
                        PyImGui.text(f"{account.CharacterName}")
            PyImGui.end_table()

    @staticmethod
    def DrawPlayersDebug(cached_data:CacheData):
        global MAX_NUM_PLAYERS

        own_party_number = GLOBAL_CACHE.Party.GetOwnPartyNumber()
        PyImGui.text(f"Own Party Number: {own_party_number}")
        HeroAI_Windows.slot_to_write = PyImGui.input_int("Slot to write", HeroAI_Windows.slot_to_write)

        if PyImGui.button("Submit"):
            self_id = GLOBAL_CACHE.Player.GetAgentID()

            cached_data.HeroAI_vars.shared_memory_handler.set_player_property(HeroAI_Windows.slot_to_write, "PlayerID", self_id)
            player_id = GLOBAL_CACHE.Player.GetAgentID()
            cached_data.HeroAI_vars.shared_memory_handler.set_player_property(HeroAI_Windows.slot_to_write, "Energy_Regen", Agent.GetEnergyRegen(player_id))
            cached_data.HeroAI_vars.shared_memory_handler.set_player_property(HeroAI_Windows.slot_to_write, "Energy", Agent.GetEnergy(player_id))
            cached_data.HeroAI_vars.shared_memory_handler.set_player_property(HeroAI_Windows.slot_to_write, "IsActive", True)
            cached_data.HeroAI_vars.shared_memory_handler.set_player_property(HeroAI_Windows.slot_to_write, "IsHero", False)
            cached_data.HeroAI_vars.shared_memory_handler.set_player_property(HeroAI_Windows.slot_to_write, "IsFlagged", False)
            cached_data.HeroAI_vars.shared_memory_handler.set_player_property(HeroAI_Windows.slot_to_write, "FlagPosX", 0.0)
            cached_data.HeroAI_vars.shared_memory_handler.set_player_property(HeroAI_Windows.slot_to_write, "FlagPosY", 0.0)


        headers = ["Slot","PlayerID", "EnergyRegen", "Energy","IsActive", "IsHero", "IsFlagged", "FlagPosX", "FlagPosY", "LastUpdated"]

        data = []
        for i in range(MAX_NUM_PLAYERS):
            player = cached_data.HeroAI_vars.all_player_struct[i]
            data.append((
                i,  # Slot index
                player.PlayerID,
                f"{player.Energy_Regen:.4f}", 
                f"{player.Energy:.4f}",       
                player.IsActive,
                player.IsHero,
                player.IsFlagged,
                f"{player.FlagPosX:.4f}",     
                f"{player.FlagPosY:.4f}",     
                player.LastUpdated
            ))

        ImGui.table("Players Debug Table", headers, data)

    @staticmethod
    def DrawHeroesDebug(cached_data:CacheData): 
        global MAX_NUM_PLAYERS
        headers = ["Slot", "agent_id", "owner_player_id", "hero_id", "hero_name"]
        data = []

        heroes = GLOBAL_CACHE.Party.GetHeroes()
        for index, hero in enumerate(heroes):
            data.append((
                index,  # Slot index
                hero.agent_id,
                hero.owner_player_id,
                hero.hero_id.GetID(),
                hero.hero_id.GetName(),
            ))
        ImGui.table("Heroes Debug Table", headers, data)

    @staticmethod
    def DrawGameOptionsDebug(cached_data:CacheData):
        global MAX_NUM_PLAYERS

        data = []
        PyImGui.text("Remote Control Variables")
        PyImGui.text(f"own_party_number: {GLOBAL_CACHE.Party.GetOwnPartyNumber()}")
        headers = ["Control", "Following", "Avoidance", "Looting", "Targeting", "Combat"]
        headers += [f"Skill {j + 1}" for j in range(NUMBER_OF_SKILLS)]
        row = [
            "Remote",  
            cached_data.HeroAI_vars.global_control_game_struct.Following,
            cached_data.HeroAI_vars.global_control_game_struct.Avoidance,
            cached_data.HeroAI_vars.global_control_game_struct.Looting,
            cached_data.HeroAI_vars.global_control_game_struct.Targeting,
            cached_data.HeroAI_vars.global_control_game_struct.Combat,
            cached_data.HeroAI_vars.global_control_game_struct.WindowVisible
        ]

        row += [
            cached_data.HeroAI_vars.global_control_game_struct.Skills[j].Active for j in range(NUMBER_OF_SKILLS)
        ]
        data.append(tuple(row))
        ImGui.table("Control Debug Table", headers, data)

        headers = ["Slot", "Following", "Avoidance", "Looting", "Targeting", "Combat", "WindowVisible"]
        headers += [f"Skill {j + 1}" for j in range(NUMBER_OF_SKILLS)] 

        data = []
        for i in range(MAX_NUM_PLAYERS):
            row = [
                i,  
                cached_data.HeroAI_vars.all_game_option_struct[i].Following,
                cached_data.HeroAI_vars.all_game_option_struct[i].Avoidance,
                cached_data.HeroAI_vars.all_game_option_struct[i].Looting,
                cached_data.HeroAI_vars.all_game_option_struct[i].Targeting,
                cached_data.HeroAI_vars.all_game_option_struct[i].Combat,
                cached_data.HeroAI_vars.all_game_option_struct[i].WindowVisible
            ]

            row += [
                cached_data.HeroAI_vars.all_game_option_struct[i].Skills[j].Active for j in range(NUMBER_OF_SKILLS)
            ]

            data.append(tuple(row))

        ImGui.table("Game Options Debug Table", headers, data)

    @staticmethod
    def DrawFlagDebug(cached_data:CacheData):
        global capture_flag_all, capture_hero_flag
        global MAX_NUM_PLAYERS
        
        PyImGui.text("Flag Debug")
        PyImGui.text(f"capture_flag_all: {capture_flag_all}")
        PyImGui.text(f"capture_hero_flag: {capture_hero_flag}")
        if PyImGui.button("Toggle Flags"):
            capture_flag_all = not capture_flag_all
            capture_hero_flag = not capture_hero_flag

        PyImGui.separator()

        x, y, z = Overlay().GetMouseWorldPos()

        PyImGui.text(f"Mouse Position: {x:.2f}, {y:.2f}, {z:.2f}")
        PyImGui.text_colored("Having GetMouseWorldPos active will crash your client on map change",(1, 0.5, 0.05, 1))
        mouse_x, mouse_y = Overlay().GetMouseCoords()
        PyImGui.text(f"Mouse Coords: {mouse_x}, {mouse_y}")
        PyImGui.text(f"Player Position: {Agent.GetXYZ(GLOBAL_CACHE.Player.GetAgentID())}")
        HeroAI_Windows.draw_fake_flag = PyImGui.checkbox("Draw Fake Flag", HeroAI_Windows.draw_fake_flag)

        if HeroAI_Windows.draw_fake_flag:
            DrawFlagAll(x, y)

        PyImGui.separator()

        PyImGui.text(f"AllFlag: {AllFlag}")
        PyImGui.text(f"capture_hero_index: {capture_hero_index}")

        for i in range(MAX_NUM_PLAYERS):
            if HeroAI_Windows.HeroFlags[i]:
                PyImGui.text(f"Hero {i + 1} is flagged")

    @staticmethod
    def DrawFollowDebug(cached_data:CacheData):
        global show_area_rings, show_hero_follow_grid, show_distance_on_followers
        global MAX_NUM_PLAYERS


        if PyImGui.button("reset overlay"):
            Overlay().RefreshDrawList()
        show_area_rings = PyImGui.checkbox("Show Area Rings", show_area_rings)
        show_hero_follow_grid = PyImGui.checkbox("Show Hero Follow Grid", show_hero_follow_grid)
        show_distance_on_followers = PyImGui.checkbox("Show Distance on Followers", show_distance_on_followers)
        PyImGui.separator()
        PyImGui.text(f"InAggro: {cached_data.data.in_aggro}")
        PyImGui.text(f"IsMelee: {Agent.IsMelee(GLOBAL_CACHE.Player.GetAgentID())}")
        PyImGui.text(f"stay_alert_timer: {cached_data.stay_alert_timer.GetElapsedTime()}")
        PyImGui.text(f"Leader Rotation Angle: {Agent.GetRotationAngle(GLOBAL_CACHE.Party.GetPartyLeaderID())}")
        PyImGui.text(f"old_leader_rotation_angle: {cached_data.data.old_angle}")
        PyImGui.text(f"Angle_changed: {cached_data.data.angle_changed}")

        segments = 32
        Overlay().BeginDraw()
        if show_area_rings:
            player_x, player_y, player_z = Agent.GetXYZ(GLOBAL_CACHE.Player.GetAgentID()) #cached_data.data.player_xyz # needs to be live

            Overlay().DrawPoly3D(player_x, player_y, player_z, Range.Touch.value / 2, Utils.RGBToColor(255, 255, 0 , 128), numsegments=segments, thickness=2.0)
            Overlay().DrawPoly3D(player_x, player_y, player_z, Range.Touch.value    , Utils.RGBToColor(255, 200, 0 , 128), numsegments=segments, thickness=2.0)
            Overlay().DrawPoly3D(player_x, player_y, player_z, Range.Adjacent.value , Utils.RGBToColor(255, 150, 0 , 128), numsegments=segments, thickness=2.0)
            Overlay().DrawPoly3D(player_x, player_y, player_z, Range.Nearby.value   , Utils.RGBToColor(255, 100, 0 , 128), numsegments=segments, thickness=2.0)
            Overlay().DrawPoly3D(player_x, player_y, player_z, Range.Area.value     , Utils.RGBToColor(255, 50 , 0 , 128), numsegments=segments, thickness=2.0)
            Overlay().DrawPoly3D(player_x, player_y, player_z, Range.Earshot.value  , Utils.RGBToColor(255, 25 , 0 , 128), numsegments=segments, thickness=2.0)
            Overlay().DrawPoly3D(player_x, player_y, player_z, Range.Spellcast.value, Utils.RGBToColor(255, 12 , 0 , 128), numsegments=segments, thickness=2.0)

        if show_hero_follow_grid:
            leader_x, leader_y, leader_z = Agent.GetXYZ(GLOBAL_CACHE.Party.GetPartyLeaderID()) #cached_data.data.party_leader_xyz #needs to be live 

            for index, angle in enumerate(hero_formation):
                if index == 0:
                    continue
                angle_on_hero_grid = Agent.GetRotationAngle(GLOBAL_CACHE.Party.GetPartyLeaderID()) + Utils.DegToRad(angle)
                hero_x = Range.Touch.value * math.cos(angle_on_hero_grid) + leader_x
                hero_y = Range.Touch.value * math.sin(angle_on_hero_grid) + leader_y
                
                Overlay().DrawPoly3D(hero_x, hero_y, leader_z, radius=Range.Touch.value /2, color=Utils.RGBToColor(255, 0, 255, 128), numsegments=segments, thickness=2.0)
    
        if show_distance_on_followers:
            for i in range(MAX_NUM_PLAYERS):
                if cached_data.HeroAI_vars.all_player_struct[i].IsActive:
                    Overlay().BeginDraw()
                    player_id = cached_data.HeroAI_vars.all_player_struct[i].PlayerID
                    if player_id == GLOBAL_CACHE.Player.GetAgentID():
                        continue
                    target_x, target_y, target_z = Agent.GetXYZ(player_id)
                    Overlay().DrawPoly3D(target_x, target_y, target_z, radius=72, color=Utils.RGBToColor(255, 255, 255, 128),numsegments=segments,thickness=2.0)
                    z_coord = Overlay().FindZ(target_x, target_y, 0)
                    Overlay().DrawText3D(target_x, target_y, z_coord-130, f"{DistanceFromWaypoint(target_x, target_y):.1f}",color=Utils.RGBToColor(255, 255, 255, 128), autoZ=False, centered=True, scale=2.0)
        
        Overlay().EndDraw()
     
    @staticmethod   
    def DrawOptions(cached_data:CacheData):
        cached_data.ui_state_data.show_classic_controls = PyImGui.checkbox("Show Classic Controls", cached_data.ui_state_data.show_classic_controls)
        #TODO Select combat engine options

    @staticmethod
    def DrawMessagingOptions(cached_data:CacheData):
        def _post_pcon_message(params):
            self_account = GLOBAL_CACHE.ShMem.GetAccountDataFromEmail(cached_data.account_email)
            if not self_account:
                return
            accounts = GLOBAL_CACHE.ShMem.GetAllAccountData()
            sender_email = cached_data.account_email
            for account in accounts:
                ConsoleLog("Messaging", f"Sending Pcon Message to  {account.AccountEmail}")
                
                GLOBAL_CACHE.ShMem.SendMessage(sender_email, account.AccountEmail, SharedCommandType.PCon, params)

        if ImGui.colored_button(f"{IconsFontAwesome5.ICON_TIMES}##commands_resign", HeroAI_Windows.ButtonColors["Resign"].button_color, HeroAI_Windows.ButtonColors["Resign"].hovered_color, HeroAI_Windows.ButtonColors["Resign"].active_color):
        #if PyImGui.button(f"{IconsFontAwesome5.ICON_TIMES}##commands_resign"):
            accounts = GLOBAL_CACHE.ShMem.GetAllAccountData()
            sender_email = cached_data.account_email
            for account in accounts:
                ConsoleLog("Messaging", "Resigning account: " + account.AccountEmail)
                GLOBAL_CACHE.ShMem.SendMessage(sender_email, account.AccountEmail, SharedCommandType.Resign, (0,0,0,0))
        ImGui.show_tooltip("Resign Party")
        
        PyImGui.same_line(0,-1)
        PyImGui.text("|")
        PyImGui.same_line(0,-1)

        if PyImGui.button(f"{IconsFontAwesome5.ICON_COMPRESS_ARROWS_ALT}##commands_pixelstack"):
            self_account = GLOBAL_CACHE.ShMem.GetAccountDataFromEmail(cached_data.account_email)
            if not self_account:
                return
            accounts = GLOBAL_CACHE.ShMem.GetAllAccountData()
            sender_email = cached_data.account_email
            for account in accounts:
                if self_account.AccountEmail == account.AccountEmail:
                    continue
                ConsoleLog("Messaging", "Pixelstacking account: " + account.AccountEmail)
                GLOBAL_CACHE.ShMem.SendMessage(sender_email, account.AccountEmail, SharedCommandType.PixelStack, (self_account.PlayerPosX,self_account.PlayerPosY,0,0))
        ImGui.show_tooltip("Pixel Stack (Carto Helper)")
        
        PyImGui.same_line(0,-1)

        if PyImGui.button(f"{IconsFontAwesome5.ICON_HAND_POINT_RIGHT}##commands_InteractTarget"):
            target = GLOBAL_CACHE.Player.GetTargetID()
            if target == 0:
                ConsoleLog("Messaging", "No target to interact with.")
                return
            self_account = GLOBAL_CACHE.ShMem.GetAccountDataFromEmail(cached_data.account_email)
            if not self_account:
                return
            accounts = GLOBAL_CACHE.ShMem.GetAllAccountData()
            sender_email = cached_data.account_email
            for account in accounts:
                if self_account.AccountEmail == account.AccountEmail:
                    continue
                ConsoleLog("Messaging", f"Ordering {account.AccountEmail} to interact with target: {target}")
                GLOBAL_CACHE.ShMem.SendMessage(sender_email, account.AccountEmail, SharedCommandType.InteractWithTarget, (target,0,0,0))
        ImGui.show_tooltip("Interact with Target")
        PyImGui.same_line(0,-1)

        if PyImGui.button(f"{IconsFontAwesome5.ICON_COMMENT_DOTS}##commands_takedialog"):
            target = GLOBAL_CACHE.Player.GetTargetID()
            if target == 0:
                ConsoleLog("Messaging", "No target to interact with.")
                return
            if not UIManager.IsNPCDialogVisible():
                ConsoleLog("Messaging", "No dialog is open.")
                return
            
            # i need to display a modal dialog here to confirm options
            options = UIManager.GetDialogButtonCount()
            
            self_account = GLOBAL_CACHE.ShMem.GetAccountDataFromEmail(cached_data.account_email)
            if not self_account:
                return
            accounts = GLOBAL_CACHE.ShMem.GetAllAccountData()
            sender_email = cached_data.account_email
            for account in accounts:
                if self_account.AccountEmail == account.AccountEmail:
                    continue
                ConsoleLog("Messaging", f"Ordering {account.AccountEmail} to interact with target: {target}")
                GLOBAL_CACHE.ShMem.SendMessage(sender_email, account.AccountEmail, SharedCommandType.TakeDialogWithTarget, (target,1,0,0))
        ImGui.show_tooltip("Get Dialog")
        PyImGui.separator()
        if PyImGui.collapsing_header("PCons"):
            PyImGui.push_style_color(PyImGui.ImGuiCol.Button, HeroAI_Windows.ButtonColors["Celerity"].button_color.to_tuple_normalized())  # On color
            PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonHovered, HeroAI_Windows.ButtonColors["Celerity"].hovered_color.to_tuple_normalized())  # Hover color
            PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonActive, HeroAI_Windows.ButtonColors["Celerity"].active_color.to_tuple_normalized())
            if ImGui.ImageButton("##Esence_unique_name", HeroAI_Windows.ButtonColors["Celerity"].texture_path, 32, 32):
                _post_pcon_message((ModelID.Essence_Of_Celerity.value, GLOBAL_CACHE.Skill.GetID("Essence_of_Celerity_item_effect"), 0, 0))
            PyImGui.pop_style_color(3)
            ImGui.show_tooltip("Esence of Celerity")
            
            PyImGui.same_line(0,-1)
            PyImGui.push_style_color(PyImGui.ImGuiCol.Button, HeroAI_Windows.ButtonColors["GrailOfMight"].button_color.to_tuple_normalized())  # On color
            PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonHovered, HeroAI_Windows.ButtonColors["GrailOfMight"].hovered_color.to_tuple_normalized())  # Hover color
            PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonActive, HeroAI_Windows.ButtonColors["GrailOfMight"].active_color.to_tuple_normalized())
            if ImGui.ImageButton("##Grail_unique_name", HeroAI_Windows.ButtonColors["GrailOfMight"].texture_path, 32, 32):
                _post_pcon_message((ModelID.Grail_Of_Might.value, GLOBAL_CACHE.Skill.GetID("Grail_of_Might_item_effect"), 0, 0))
            PyImGui.pop_style_color(3)
            ImGui.show_tooltip("Grail of Might")

            PyImGui.same_line(0,-1)
            PyImGui.push_style_color(PyImGui.ImGuiCol.Button, HeroAI_Windows.ButtonColors["ArmorOfSalvation"].button_color.to_tuple_normalized())  # On color
            PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonHovered, HeroAI_Windows.ButtonColors["ArmorOfSalvation"].hovered_color.to_tuple_normalized())  # Hover color
            PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonActive, HeroAI_Windows.ButtonColors["ArmorOfSalvation"].active_color.to_tuple_normalized())
            if ImGui.ImageButton("##Armor_unique_name", HeroAI_Windows.ButtonColors["ArmorOfSalvation"].texture_path, 32, 32):
                _post_pcon_message((ModelID.Armor_Of_Salvation.value, GLOBAL_CACHE.Skill.GetID("Armor_of_Salvation_item_effect"), 0, 0))
            PyImGui.pop_style_color(3)
            ImGui.show_tooltip("Armor of Salvation")
            
            PyImGui.same_line(0,-1)
            PyImGui.text("|")
            PyImGui.same_line(0,-1)
            
            PyImGui.push_style_color(PyImGui.ImGuiCol.Button, HeroAI_Windows.ButtonColors["CandyCane"].button_color.to_tuple_normalized())  # On color
            PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonHovered, HeroAI_Windows.ButtonColors["CandyCane"].hovered_color.to_tuple_normalized())  # Hover color
            PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonActive, HeroAI_Windows.ButtonColors["CandyCane"].active_color.to_tuple_normalized())
            if ImGui.ImageButton("##CandyCane_unique_name", HeroAI_Windows.ButtonColors["CandyCane"].texture_path, 32, 32):
                _post_pcon_message((ModelID.Rainbow_Candy_Cane.value, 0, ModelID.Honeycomb.value, 0))
            PyImGui.pop_style_color(3)
            ImGui.show_tooltip("Rainbow Candy Cane / Honeycomb")
            PyImGui.separator()
            
            PyImGui.push_style_color(PyImGui.ImGuiCol.Button, HeroAI_Windows.ButtonColors["BirthdayCupcake"].button_color.to_tuple_normalized())  # On color
            PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonHovered, HeroAI_Windows.ButtonColors["BirthdayCupcake"].hovered_color.to_tuple_normalized())  # Hover color
            PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonActive, HeroAI_Windows.ButtonColors["BirthdayCupcake"].active_color.to_tuple_normalized())
            if ImGui.ImageButton("##BirthdayCupcake_unique_name", HeroAI_Windows.ButtonColors["BirthdayCupcake"].texture_path, 32, 32):
                _post_pcon_message((ModelID.Birthday_Cupcake.value, GLOBAL_CACHE.Skill.GetID("Birthday_Cupcake_skill"), 0, 0))
            PyImGui.pop_style_color(3)
            ImGui.show_tooltip("Birthday Cupcake")
            
            PyImGui.same_line(0,-1)
            
            PyImGui.push_style_color(PyImGui.ImGuiCol.Button, HeroAI_Windows.ButtonColors["GoldenEgg"].button_color.to_tuple_normalized())  # On color
            PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonHovered, HeroAI_Windows.ButtonColors["GoldenEgg"].hovered_color.to_tuple_normalized())  # Hover color
            PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonActive, HeroAI_Windows.ButtonColors["GoldenEgg"].active_color.to_tuple_normalized())
            if ImGui.ImageButton("##GoldenEgg_unique_name", HeroAI_Windows.ButtonColors["GoldenEgg"].texture_path, 32, 32):
                _post_pcon_message((ModelID.Golden_Egg.value, GLOBAL_CACHE.Skill.GetID("Golden_Egg_skill"), 0, 0))
            PyImGui.pop_style_color(3)
            ImGui.show_tooltip("Golden Egg")
            
            PyImGui.same_line(0,-1)
            
            PyImGui.push_style_color(PyImGui.ImGuiCol.Button, HeroAI_Windows.ButtonColors["CandyCorn"].button_color.to_tuple_normalized())  # On color
            PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonHovered, HeroAI_Windows.ButtonColors["CandyCorn"].hovered_color.to_tuple_normalized())  # Hover color
            PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonActive, HeroAI_Windows.ButtonColors["CandyCorn"].active_color.to_tuple_normalized())
            if ImGui.ImageButton("##CandyCorn_unique_name", HeroAI_Windows.ButtonColors["CandyCorn"].texture_path, 32, 32):
                _post_pcon_message((ModelID.Candy_Corn.value, GLOBAL_CACHE.Skill.GetID("Candy_Corn_skill"), 0, 0))
            PyImGui.pop_style_color(3)
            ImGui.show_tooltip("Candy Corn")
            
            PyImGui.same_line(0,-1)
            PyImGui.text("|")
            PyImGui.same_line(0,-1)
            
            PyImGui.push_style_color(PyImGui.ImGuiCol.Button, HeroAI_Windows.ButtonColors["Alcohol"].button_color.to_tuple_normalized())  # On color
            PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonHovered, HeroAI_Windows.ButtonColors["Alcohol"].hovered_color.to_tuple_normalized())  # Hover color
            PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonActive, HeroAI_Windows.ButtonColors["Alcohol"].active_color.to_tuple_normalized())
            if ImGui.ImageButton("##Alcohol_unique_name", HeroAI_Windows.ButtonColors["Alcohol"].texture_path, 32, 32):
                pass
            PyImGui.pop_style_color(3)
            ImGui.show_tooltip("Alcohol (WIP)")

            PyImGui.separator()
            
            PyImGui.push_style_color(PyImGui.ImGuiCol.Button, HeroAI_Windows.ButtonColors["CandyApple"].button_color.to_tuple_normalized())  # On color
            PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonHovered, HeroAI_Windows.ButtonColors["CandyApple"].hovered_color.to_tuple_normalized())  # Hover color
            PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonActive, HeroAI_Windows.ButtonColors["CandyApple"].active_color.to_tuple_normalized())
            if ImGui.ImageButton("##CandyApple_unique_name", HeroAI_Windows.ButtonColors["CandyApple"].texture_path, 32, 32):
                _post_pcon_message((ModelID.Candy_Apple.value, GLOBAL_CACHE.Skill.GetID("Candy_Apple_skill"), 0, 0))
            PyImGui.pop_style_color(3)
            ImGui.show_tooltip("Candy Apple")
            
            PyImGui.same_line(0,-1)
            
            PyImGui.push_style_color(PyImGui.ImGuiCol.Button, HeroAI_Windows.ButtonColors["PumpkinPie"].button_color.to_tuple_normalized())  # On color
            PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonHovered, HeroAI_Windows.ButtonColors["PumpkinPie"].hovered_color.to_tuple_normalized())  # Hover color
            PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonActive, HeroAI_Windows.ButtonColors["PumpkinPie"].active_color.to_tuple_normalized())
            if ImGui.ImageButton("##PumpkinPie_unique_name", HeroAI_Windows.ButtonColors["PumpkinPie"].texture_path, 32, 32):
                _post_pcon_message((ModelID.Slice_Of_Pumpkin_Pie.value, GLOBAL_CACHE.Skill.GetID("Pie_Induced_Ecstasy"), 0, 0))
            PyImGui.pop_style_color(3)
            ImGui.show_tooltip("Slice of Pumpkin Pie")
            
            PyImGui.same_line(0,-1)
            
            PyImGui.push_style_color(PyImGui.ImGuiCol.Button, HeroAI_Windows.ButtonColors["DrakeKabob"].button_color.to_tuple_normalized())  # On color
            PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonHovered, HeroAI_Windows.ButtonColors["DrakeKabob"].hovered_color.to_tuple_normalized())  # Hover color
            PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonActive, HeroAI_Windows.ButtonColors["DrakeKabob"].active_color.to_tuple_normalized())
            if ImGui.ImageButton("##DrakeKabob_unique_name", HeroAI_Windows.ButtonColors["DrakeKabob"].texture_path, 32, 32):
                _post_pcon_message((ModelID.Slice_Of_Pumpkin_Pie.value, GLOBAL_CACHE.Skill.GetID("Drake_Skin"), 0, 0))
            PyImGui.pop_style_color(3)
            ImGui.show_tooltip("Drake Kabob")

            PyImGui.separator()
            
            PyImGui.push_style_color(PyImGui.ImGuiCol.Button, HeroAI_Windows.ButtonColors["SkalefinSoup"].button_color.to_tuple_normalized())  # On color
            PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonHovered, HeroAI_Windows.ButtonColors["SkalefinSoup"].hovered_color.to_tuple_normalized())  # Hover color
            PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonActive, HeroAI_Windows.ButtonColors["SkalefinSoup"].active_color.to_tuple_normalized())
            if ImGui.ImageButton("##SkalefinSoup_unique_name", HeroAI_Windows.ButtonColors["SkalefinSoup"].texture_path, 32, 32):
                _post_pcon_message((ModelID.Bowl_Of_Skalefin_Soup.value, GLOBAL_CACHE.Skill.GetID("Skale_Vigor"), 0, 0))
            PyImGui.pop_style_color(3)
            ImGui.show_tooltip("Skalefin Soup")
            
            PyImGui.same_line(0,-1)
            
            PyImGui.push_style_color(PyImGui.ImGuiCol.Button, HeroAI_Windows.ButtonColors["PahnaiSalad"].button_color.to_tuple_normalized())  # On color
            PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonHovered, HeroAI_Windows.ButtonColors["PahnaiSalad"].hovered_color.to_tuple_normalized())  # Hover color
            PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonActive, HeroAI_Windows.ButtonColors["PahnaiSalad"].active_color.to_tuple_normalized())
            if ImGui.ImageButton("##PahnaiSalad_unique_name", HeroAI_Windows.ButtonColors["PahnaiSalad"].texture_path, 32, 32):
                _post_pcon_message((ModelID.Pahnai_Salad.value, GLOBAL_CACHE.Skill.GetID("Pahnai_Salad_item_effect"), 0, 0))
            PyImGui.pop_style_color(3)
            ImGui.show_tooltip("Pahnai Salad")
            
            PyImGui.same_line(0,-1)
            
            PyImGui.push_style_color(PyImGui.ImGuiCol.Button, HeroAI_Windows.ButtonColors["WarSupplies"].button_color.to_tuple_normalized())  # On color
            PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonHovered, HeroAI_Windows.ButtonColors["WarSupplies"].hovered_color.to_tuple_normalized())  # Hover color
            PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonActive, HeroAI_Windows.ButtonColors["WarSupplies"].active_color.to_tuple_normalized())
            if ImGui.ImageButton("##WarSupplies_unique_name", HeroAI_Windows.ButtonColors["WarSupplies"].texture_path, 32, 32):
                _post_pcon_message((ModelID.War_Supplies.value, GLOBAL_CACHE.Skill.GetID("Well_Supplied"), 0, 0))
            PyImGui.pop_style_color(3)
            ImGui.show_tooltip("War Supplies")
        
    
    @staticmethod
    def DrawDebugWindow(cached_data:CacheData):
        global MAX_NUM_PLAYERS

        if PyImGui.collapsing_header("Players Debug"):
            HeroAI_Windows.DrawPlayersDebug(cached_data)
        if PyImGui.collapsing_header("Game Options Debug"):
            HeroAI_Windows.DrawGameOptionsDebug(cached_data)

        if PyImGui.collapsing_header("Heroes Debug"):
            HeroAI_Windows.DrawHeroesDebug(cached_data)

        if Map.IsExplorable():
            if PyImGui.collapsing_header("Follow Debug"):
                HeroAI_Windows.DrawPrioritizedSkills(cached_data)
                HeroAI_Windows.DrawFollowDebug(cached_data)
            if PyImGui.collapsing_header("Flag Debug"):
                HeroAI_Windows.DrawFlagDebug(cached_data)
            if PyImGui.collapsing_header("Prioritized Skills"):
                HeroAI_Windows.DrawPrioritizedSkills(cached_data)
            if PyImGui.collapsing_header("Buff Debug"):
                HeroAI_Windows.DrawBuffWindow(cached_data)
            
    @staticmethod
    def DrawMultiboxTools(cached_data:CacheData):
        global MAX_NUM_PLAYERS
        cached_data.HeroAI_windows.tools_window.initialize()

        if cached_data.HeroAI_windows.tools_window.begin():
            if Map.IsOutpost() and GLOBAL_CACHE.Player.GetAgentID() == GLOBAL_CACHE.Party.GetPartyLeaderID():
                if PyImGui.collapsing_header("Party Setup",PyImGui.TreeNodeFlags.DefaultOpen):
                    HeroAI_Windows.DrawCandidateWindow(cached_data)
            if Map.IsExplorable() and GLOBAL_CACHE.Player.GetAgentID() == GLOBAL_CACHE.Party.GetPartyLeaderID():
                if PyImGui.collapsing_header("Flagging"):
                    HeroAI_Windows.DrawFlaggingWindow(cached_data)

            if PyImGui.collapsing_header("Debug Options"):
                HeroAI_Windows.DrawDebugWindow(cached_data)
    
        cached_data.HeroAI_windows.tools_window.process_window()
        cached_data.HeroAI_windows.tools_window.end()

    @staticmethod
    def CompareAndSubmitGameOptions(cached_data:CacheData, game_option: GameOptionStruct):   
        global MAX_NUM_PLAYERS
        # Core Options
        accounts = GLOBAL_CACHE.ShMem.GetAllAccountData()
        if not accounts:
            ConsoleLog("HeroAI", "No accounts found in shared memory.")
            return
        
        if game_option.Following != cached_data.HeroAI_vars.global_control_game_struct.Following:
            cached_data.HeroAI_vars.global_control_game_struct.Following = game_option.Following
            for account in accounts:
                account_email = account.AccountEmail
                hero_ai_data = GLOBAL_CACHE.ShMem.GetHeroAIOptions(account_email)
                if hero_ai_data is None:
                    ConsoleLog("HeroAI", f"Failed to get HeroAI options for {account_email} from shared memory.")
                    continue
                
                hero_ai_data.Following = game_option.Following


        if game_option.Avoidance != cached_data.HeroAI_vars.global_control_game_struct.Avoidance:
            cached_data.HeroAI_vars.global_control_game_struct.Avoidance = game_option.Avoidance
            for account in accounts:
                account_email = account.AccountEmail
                hero_ai_data = GLOBAL_CACHE.ShMem.GetHeroAIOptions(account_email)
                if hero_ai_data is None:
                    ConsoleLog("HeroAI", f"Failed to get HeroAI options for {account_email} from shared memory.")
                    continue
                
                hero_ai_data.Avoidance = game_option.Avoidance

        if game_option.Looting != cached_data.HeroAI_vars.global_control_game_struct.Looting:
            cached_data.HeroAI_vars.global_control_game_struct.Looting = game_option.Looting
            for account in accounts:
                account_email = account.AccountEmail
                hero_ai_data = GLOBAL_CACHE.ShMem.GetHeroAIOptions(account_email)
                if hero_ai_data is None:
                    ConsoleLog("HeroAI", f"Failed to get HeroAI options for {account_email} from shared memory.")
                    continue
                
                hero_ai_data.Looting = game_option.Looting

        if game_option.Targeting != cached_data.HeroAI_vars.global_control_game_struct.Targeting:
            cached_data.HeroAI_vars.global_control_game_struct.Targeting = game_option.Targeting
            for account in accounts:
                account_email = account.AccountEmail
                hero_ai_data = GLOBAL_CACHE.ShMem.GetHeroAIOptions(account_email)
                if hero_ai_data is None:
                    ConsoleLog("HeroAI", f"Failed to get HeroAI options for {account_email} from shared memory.")
                    continue
                
                hero_ai_data.Targeting = game_option.Targeting

        if game_option.Combat != cached_data.HeroAI_vars.global_control_game_struct.Combat:
            cached_data.HeroAI_vars.global_control_game_struct.Combat = game_option.Combat
            for account in accounts:
                account_email = account.AccountEmail
                hero_ai_data = GLOBAL_CACHE.ShMem.GetHeroAIOptions(account_email)
                if hero_ai_data is None:
                    ConsoleLog("HeroAI", f"Failed to get HeroAI options for {account_email} from shared memory.")
                    continue
                
                hero_ai_data.Combat = game_option.Combat

        # Skills
        for skill_index in range(NUMBER_OF_SKILLS):
            if game_option.Skills[skill_index].Active != cached_data.HeroAI_vars.global_control_game_struct.Skills[skill_index].Active:
                cached_data.HeroAI_vars.global_control_game_struct.Skills[skill_index].Active = game_option.Skills[skill_index].Active
                for account in accounts:
                    account_email = account.AccountEmail
                    hero_ai_data = GLOBAL_CACHE.ShMem.GetHeroAIOptions(account_email)
                    if hero_ai_data is None:
                        ConsoleLog("HeroAI", f"Failed to get HeroAI options for {account_email} from shared memory.")
                        continue
                    
                    hero_ai_data.Skills[skill_index] = game_option.Skills[skill_index].Active

    @staticmethod
    def SubmitGameOptions(cached_data:CacheData,party_pos,game_option,original_game_option):
        # Core Options
        hero_ai_data = GLOBAL_CACHE.ShMem.GetGerHeroAIOptionsByPartyNumber(party_pos)
        if hero_ai_data is None:
            ConsoleLog("HeroAI", "Failed to get HeroAI options from shared memory.")
            return
        if game_option.Following != original_game_option.Following:
            hero_ai_data.Following = game_option.Following
            ConsoleLog("HeroAI", f"Following set to {game_option.Following} for party {party_pos}")
            #cached_data.HeroAI_vars.shared_memory_handler.set_game_option_property(index, "Following", game_option.Following)

        if game_option.Avoidance != original_game_option.Avoidance:
            hero_ai_data.Avoidance = game_option.Avoidance
            ConsoleLog("HeroAI", f"Avoidance set to {game_option.Avoidance} for party {party_pos}")
            #cached_data.HeroAI_vars.shared_memory_handler.set_game_option_property(index, "Avoidance", game_option.Avoidance)

        if game_option.Looting != original_game_option.Looting:
            hero_ai_data.Looting = game_option.Looting
            ConsoleLog("HeroAI", f"Looting set to {game_option.Looting} for party {party_pos}")
            #cached_data.HeroAI_vars.shared_memory_handler.set_game_option_property(index, "Looting", game_option.Looting)

        if game_option.Targeting != original_game_option.Targeting:
            hero_ai_data.Targeting = game_option.Targeting
            ConsoleLog("HeroAI", f"Targeting set to {game_option.Targeting} for party {party_pos}")
            #cached_data.HeroAI_vars.shared_memory_handler.set_game_option_property(index, "Targeting", game_option.Targeting)

        if game_option.Combat != original_game_option.Combat:
            hero_ai_data.Combat = game_option.Combat
            ConsoleLog("HeroAI", f"Combat set to {game_option.Combat} for party {party_pos}")
            #cached_data.HeroAI_vars.shared_memory_handler.set_game_option_property(index, "Combat", game_option.Combat)

        # Skills
        for i in range(NUMBER_OF_SKILLS):
            if game_option.Skills[i].Active != original_game_option.Skills[i].Active:
                hero_ai_data.Skills[i] = game_option.Skills[i].Active
                ConsoleLog("HeroAI", f"Skill {i + 1} set to {game_option.Skills[i].Active} for party {party_pos}")
                #cached_data.HeroAI_vars.shared_memory_handler.set_game_option_property(index, f"Skill_{i + 1}", game_option.Skills[i].Active)

    @staticmethod
    def DrawPanelButtons(source_game_option):
        game_option = GameOptionStruct()
        btn_size = 32
        table_width = btn_size * 5 + 30
        skill_size = table_width / NUMBER_OF_SKILLS - 4

        if PyImGui.begin_table("GameOptionTable", 5):
            PyImGui.table_next_row()
            PyImGui.table_next_column()
            game_option.Following = ImGui.toggle_button(IconsFontAwesome5.ICON_RUNNING + "##Following", source_game_option.Following, btn_size, btn_size)
            ImGui.show_tooltip("Following")
            PyImGui.table_next_column()
            game_option.Avoidance = ImGui.toggle_button(IconsFontAwesome5.ICON_PODCAST + "##Avoidance", source_game_option.Avoidance, btn_size, btn_size)
            ImGui.show_tooltip("Avoidance")
            PyImGui.table_next_column()
            game_option.Looting = ImGui.toggle_button(IconsFontAwesome5.ICON_COINS + "##Looting", source_game_option.Looting, btn_size, btn_size)
            ImGui.show_tooltip("Looting")
            PyImGui.table_next_column()
            game_option.Targeting = ImGui.toggle_button(IconsFontAwesome5.ICON_BULLSEYE + "##Targeting", source_game_option.Targeting, btn_size, btn_size)
            ImGui.show_tooltip("Targeting")
            PyImGui.table_next_column()
            game_option.Combat = ImGui.toggle_button(IconsFontAwesome5.ICON_SKULL_CROSSBONES + "##Combat", source_game_option.Combat, btn_size, btn_size)
            ImGui.show_tooltip("Combat")
            PyImGui.end_table()

        if PyImGui.begin_table("SkillsTable", NUMBER_OF_SKILLS + 1):
            PyImGui.table_next_row()
            for i in range(NUMBER_OF_SKILLS):
                PyImGui.table_next_column()
                game_option.Skills[i].Active = ImGui.toggle_button(f"{i + 1}##Skill{i}", source_game_option.Skills[i].Active, skill_size, skill_size)
                ImGui.show_tooltip(f"Skill {i + 1}")
            PyImGui.end_table()
    
        return game_option

    @staticmethod
    def DrawFollowerUI(cached_data:CacheData):
        own_party_number = GLOBAL_CACHE.Party.GetOwnPartyNumber()
        original_game_option = cached_data.HeroAI_vars.all_game_option_struct[own_party_number]
        
        if not original_game_option.WindowVisible:
            return

        if own_party_number <= 0:
            return
                
        def advance_rainbow_color(tick: int) -> tuple[int,Color]:
            tick += 2
            # Use sine waves offset from each other to create a rainbow pulse
            r = int((math.sin(tick * 0.05) * 0.5 + 0.5) * 255)  # Red wave
            g = int((math.sin(tick * 0.05 + 2.0) * 0.5 + 0.5) * 255)  # Green wave
            b = int((math.sin(tick * 0.05 + 4.0) * 0.5 + 0.5) * 255)  # Blue wave
            return tick, Color(r, g, b, 255).copy()
            
        HeroAI_Windows.color_tick, HeroAI_Windows.outline_color = advance_rainbow_color(HeroAI_Windows.color_tick)
        
        party_window_frame = WindowFrames["PartyWindow"]
        party_window_frame.DrawFrameOutline(HeroAI_Windows.outline_color.to_color(), 3)

        left, top, right, _bottom = party_window_frame.GetCoords()
        frame_offset = 5
        width = right - left - frame_offset

        flags = ImGui.PushTransparentWindow()

        PyImGui.set_next_window_pos(left, top - 35)
        PyImGui.set_next_window_size(width, 35)
        if PyImGui.begin("embedded contorl panel", True, flags):
            if PyImGui.begin_tab_bar("HeroAITabs"):
                if PyImGui.begin_tab_item(IconsFontAwesome5.ICON_USERS + "HeroAI##HeroAITab"):
                    pass
                    PyImGui.end_tab_item()
                ImGui.show_tooltip("HeroAI is Active. \nRefer to Leaders control panel for options.")
                PyImGui.end_tab_bar()
        PyImGui.end()

        ImGui.PopTransparentWindow()
        HeroAI_FloatingWindows.DrawFramedContent(cached_data, party_window_frame.GetFrameID())

    @staticmethod
    def DrawButtonBar(cached_data:CacheData):
        from Py4GWCoreLib.GlobalCache.SharedMemory import AccountData
        game_option = GameOptionStruct()
        btn_size = 23
        table_width = btn_size * 6 + 30
        skill_size = table_width / NUMBER_OF_SKILLS - 4

        ImGui.push_font("Regular",10)
        if PyImGui.begin_child("ControlPanelChild", (215, 0), False, PyImGui.WindowFlags.AlwaysAutoResize):
            if PyImGui.begin_table("MessagingTable", 5):
                PyImGui.table_next_row()
                PyImGui.table_next_column()
                if ImGui.colored_button(f"{IconsFontAwesome5.ICON_SKULL}##commands_resign", 
                                        HeroAI_Windows.ButtonColors["Resign"].button_color, 
                                        HeroAI_Windows.ButtonColors["Resign"].hovered_color, 
                                        HeroAI_Windows.ButtonColors["Resign"].active_color,
                                        btn_size, btn_size):
                    accounts = GLOBAL_CACHE.ShMem.GetAllAccountData()
                    sender_email = cached_data.account_email
                    for account in accounts:
                        ConsoleLog("Messaging", "Resigning account: " + account.AccountEmail)
                        GLOBAL_CACHE.ShMem.SendMessage(sender_email, account.AccountEmail, SharedCommandType.Resign, (0,0,0,0))
                ImGui.pop_font()
                ImGui.show_tooltip("Resign Party")
                ImGui.push_font("Regular",10)
                PyImGui.same_line(0,-1)
                PyImGui.text("|")
                PyImGui.same_line(0,-1)

                if PyImGui.button(f"{IconsFontAwesome5.ICON_COMPRESS_ARROWS_ALT}##commands_pixelstack",
                                        btn_size, btn_size):
                    self_account = GLOBAL_CACHE.ShMem.GetAccountDataFromEmail(cached_data.account_email)
                    if not self_account:
                        return
                    accounts = GLOBAL_CACHE.ShMem.GetAllAccountData()
                    sender_email = cached_data.account_email
                    for account in accounts:
                        if self_account.AccountEmail == account.AccountEmail:
                            continue
                        ConsoleLog("Messaging", "Pixelstacking account: " + account.AccountEmail)
                        GLOBAL_CACHE.ShMem.SendMessage(sender_email, account.AccountEmail, SharedCommandType.PixelStack, (self_account.PlayerPosX,self_account.PlayerPosY,0,0))
                ImGui.pop_font()
                ImGui.show_tooltip("Pixel Stack (Carto Helper)")
                ImGui.push_font("Regular",10)
                
                PyImGui.same_line(0,-1)

                if PyImGui.button(f"{IconsFontAwesome5.ICON_HAND_POINT_RIGHT}##commands_InteractTarget",
                                        btn_size, btn_size):
                    target = GLOBAL_CACHE.Player.GetTargetID()
                    if target == 0:
                        ConsoleLog("Messaging", "No target to interact with.")
                        return
                    self_account = GLOBAL_CACHE.ShMem.GetAccountDataFromEmail(cached_data.account_email)
                    if not self_account:
                        return
                    accounts = GLOBAL_CACHE.ShMem.GetAllAccountData()
                    sender_email = cached_data.account_email
                    for account in accounts:
                        if self_account.AccountEmail == account.AccountEmail:
                            continue
                        ConsoleLog("Messaging", f"Ordering {account.AccountEmail} to interact with target: {target}")
                        GLOBAL_CACHE.ShMem.SendMessage(sender_email, account.AccountEmail, SharedCommandType.InteractWithTarget, (target,0,0,0))
                
                ImGui.pop_font()
                ImGui.show_tooltip("Interact with Target")
                ImGui.push_font("Regular",10)
                PyImGui.same_line(0,-1)

                if PyImGui.button(f"{IconsFontAwesome5.ICON_COMMENT_DOTS}##commands_takedialog",
                                        btn_size, btn_size):
                    target = GLOBAL_CACHE.Player.GetTargetID()
                    if target == 0:
                        ConsoleLog("Messaging", "No target to interact with.")
                        return
                    if not UIManager.IsNPCDialogVisible():
                        ConsoleLog("Messaging", "No dialog is open.")
                        return
                    
                    # i need to display a modal dialog here to confirm options
                    options = UIManager.GetDialogButtonCount()
                    
                    self_account = GLOBAL_CACHE.ShMem.GetAccountDataFromEmail(cached_data.account_email)
                    if not self_account:
                        return
                    accounts = GLOBAL_CACHE.ShMem.GetAllAccountData()
                    sender_email = cached_data.account_email
                    for account in accounts:
                        if self_account.AccountEmail == account.AccountEmail:
                            continue
                        ConsoleLog("Messaging", f"Ordering {account.AccountEmail} to interact with target: {target}")
                        GLOBAL_CACHE.ShMem.SendMessage(sender_email, account.AccountEmail, SharedCommandType.TakeDialogWithTarget, (target,1,0,0))
                
                ImGui.pop_font()
                ImGui.show_tooltip("Get Dialog")
                ImGui.push_font("Regular",10)
                PyImGui.same_line(0,-1)
                
                if PyImGui.button(f"{IconsFontAwesome5.ICON_KEY}##unlock_chest",
                                        btn_size, btn_size):
                    sender_email = GLOBAL_CACHE.Player.GetAccountEmail()        
                    target_id = GLOBAL_CACHE.Player.GetTargetID()
                    
                    account_data = GLOBAL_CACHE.ShMem.GetAccountDataFromEmail(sender_email) 
                    if account_data is None:
                        return 
                    
                    party_id = account_data.PartyID
                    map_id = account_data.MapID
                    map_region = account_data.MapRegion
                    map_district = account_data.MapDistrict
                    map_language = account_data.MapLanguage

                    def on_same_map_and_party(account : AccountData) -> bool:                    
                        return (account.PartyID == party_id and
                                account.MapID == map_id and
                                account.MapRegion == map_region and
                                account.MapDistrict == map_district and
                                account.MapLanguage == map_language)
                        
                    all_accounts = [account for account in GLOBAL_CACHE.ShMem.GetAllAccountData() if on_same_map_and_party(account)]
                    lowest_party_index_account = min(all_accounts, key=lambda account: account.PartyPosition, default=None)
                    if lowest_party_index_account is None:
                        return
                    
                    GLOBAL_CACHE.ShMem.SendMessage(sender_email, lowest_party_index_account.AccountEmail, SharedCommandType.OpenChest, (target_id, 1, 0, 0))
            
                ImGui.pop_font()
                ImGui.show_tooltip("Open Chest")
                ImGui.push_font("Regular",10)
                PyImGui.same_line(0,-1)
                
                if PyImGui.button(f"{IconsFontAwesome5.ICON_COINS}##pickup_loot",
                                        btn_size, btn_size):
                    sender_email = GLOBAL_CACHE.Player.GetAccountEmail()        
                    accounts = GLOBAL_CACHE.ShMem.GetAllAccountData()
                    for account in accounts:
                        GLOBAL_CACHE.ShMem.SendMessage(sender_email, account.AccountEmail, SharedCommandType.PickUpLoot, (0, 0, 0, 0))
                
                ImGui.pop_font()
                ImGui.show_tooltip("Pick up Loot")
                ImGui.push_font("Regular",10)
                PyImGui.same_line(0,-1)
                    
                if PyImGui.button(f"{IconsFontAwesome5.ICON_CANDY_CANE}##consumables",btn_size, btn_size):
                    from HeroAI import ui
                    ui.show_configure_consumables_window()
                
                ImGui.pop_font()
                ImGui.show_tooltip("Consumables")
                ImGui.push_font("Regular",10)
                
                PyImGui.end_table()
            PyImGui.end_child()
        ImGui.pop_font()
            
    @staticmethod
    def DrawControlPanelWindow(cached_data:CacheData):
        global MAX_NUM_PLAYERS
        own_party_number = GLOBAL_CACHE.Party.GetOwnPartyNumber()
        game_option = GameOptionStruct()     
        if own_party_number != 0:
            return
        
        def _close_spacing():
            dummy_spacing = 5
            PyImGui.dummy(0,dummy_spacing)
            PyImGui.separator()
            PyImGui.dummy(0,dummy_spacing)

        
        cached_data.HeroAI_windows.control_window.initialize()
        if cached_data.HeroAI_windows.control_window.begin(True, PyImGui.WindowFlags.AlwaysAutoResize):
            if PyImGui.begin_child("ControlPanelChild", (200, 110), False, PyImGui.WindowFlags.AlwaysAutoResize):
                style = ImGui.get_style()
                style.ItemSpacing.push_style_var(2, 2)
                style.CellPadding.push_style_var(2, 2)
            
                game_option = HeroAI_Windows.DrawPanelButtons(cached_data.HeroAI_vars.global_control_game_struct) 
                _close_spacing() 
                HeroAI_Windows.DrawButtonBar(cached_data)
                
                style.CellPadding.pop_style_var()
                style.ItemSpacing.pop_style_var()
                PyImGui.end_child()
        
            HeroAI_Windows.CompareAndSubmitGameOptions(cached_data,game_option)
            PyImGui.separator()
            if PyImGui.tree_node("Players"):
                style = ImGui.get_style()
                style.ItemSpacing.push_style_var(2, 2)
                style.CellPadding.push_style_var(2, 2)
                for index in range(MAX_NUM_PLAYERS):
                    if cached_data.HeroAI_vars.all_player_struct[index].IsActive and not cached_data.HeroAI_vars.all_player_struct[index].IsHero:
                        original_game_option = cached_data.HeroAI_vars.all_game_option_struct[index]
                        login_number = GLOBAL_CACHE.Party.Players.GetLoginNumberByAgentID(cached_data.HeroAI_vars.all_player_struct[index].PlayerID)
                        player_name = GLOBAL_CACHE.Party.Players.GetPlayerNameByLoginNumber(login_number)
                        if PyImGui.tree_node(f"{player_name}##ControlPlayer{index}"):
                            game_option2 = HeroAI_Windows.DrawPanelButtons(original_game_option)
                            #ConsoleLog("HeroAI", f"Submitting game options for player {player_name} at index {index}")
                            HeroAI_Windows.SubmitGameOptions(cached_data, index, game_option2, original_game_option)
                            PyImGui.tree_pop()
                PyImGui.tree_pop()
                style.CellPadding.pop_style_var()
                style.ItemSpacing.pop_style_var()
                
            cached_data.HeroAI_windows.control_window.process_window()
            
        cached_data.HeroAI_windows.control_window.end()
    

