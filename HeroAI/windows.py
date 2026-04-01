from operator import index
from Py4GWCoreLib import GLOBAL_CACHE, Map,IconsFontAwesome5, ImGui, Utils, Overlay, Range, SharedCommandType, ConsoleLog, Color, ColorPalette
from Py4GWCoreLib import UIManager, ModelID, GLOBAL_CACHE, WindowFrames
from Py4GWCoreLib import Agent, Player
from Py4GWCoreLib import (Routines, ActionQueueManager,Key, Keystroke, ThrottledTimer)
from Py4GWCoreLib.IniManager import IniManager
from Py4GWCoreLib.ImGui_src.WindowModule import WindowModule
from Py4GWCoreLib.GlobalCache.SharedMemory import AccountStruct, HeroAIOptionStruct, SharedMessageStruct
from Py4GWCoreLib.py4gwcorelib_src.WidgetManager import get_widget_handler

from .constants import MAX_NUM_PLAYERS, NUMBER_OF_SKILLS
from .types import SkillType, SkillNature, Skilltarget
from .globals import capture_mouse_timer, show_area_rings, show_hero_follow_grid, show_distance_on_followers, show_broadcast_follow_positions, show_broadcast_follow_threshold_rings, hero_formation, show_flagging_window
from .utils import IsHeroFlagged, DrawFlagAll, DrawHeroFlag, DistanceFromWaypoint, SameMapAsAccount
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
    messages : list[tuple[int, SharedMessageStruct]] = []
    widget_handler = get_widget_handler()
    init_success:bool  = False
    module_info = None
    
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
        window_size=(200, 100),
        window_pos=(200, 200),
        can_close=False,
        window_flags=PyImGui.WindowFlags(PyImGui.WindowFlags.NoTitleBar | PyImGui.WindowFlags.AlwaysAutoResize),
    )
    
    @staticmethod
    def draw_Targeting_floating_buttons(cached_data: CacheData):
        if not HeroAI_FloatingWindows.settings.ShowFloatingTargets:
            return
        
        if not Map.IsExplorable():
            return
        player_pos = Player.GetXY()
        enemy_array = Routines.Agents.GetFilteredEnemyArray(player_pos[0], player_pos[1], Range.SafeCompass.value)

        if len(enemy_array) == 0:
            return

        Overlay().BeginDraw()
        for agent_id in enemy_array:
            x, y, z = Agent.GetXYZ(agent_id)
            screen_x, screen_y = Overlay.WorldToScreen(x, y, z + 25)
            # --- Configuration for "O" (The Outer Ring) ---
            o_x, o_y = screen_x - 12, screen_y - 12
            o_w, o_h = 35, 35

            # --- Configuration for "+" (The Inner Cross) ---
            # Adjust these until the + is perfectly centered inside the O
            plus_x, plus_y = o_x-2, o_y -10
            plus_w, plus_h = 40, 40

            clicked = False

            # 1. Draw the "O" layer
            if ImGui.floating_button(f"O", name=f"O_{agent_id}", 
                                    x=o_x, y=o_y, 
                                    width=o_w, height=o_h, 
                                    font_size=30):
                clicked = True

            # 2. Draw the "+" layer with its own dimensions
            if ImGui.floating_button(f"+", name=f"plus_{agent_id}", 
                                    x=plus_x, y=plus_y, 
                                    width=plus_w, height=plus_h, 
                                    font_size=45):
                clicked = True

            # 3. Shared Logic
            if clicked:
                Player.ChangeTarget(agent_id)
                Player.Interact(agent_id, True)
                ActionQueueManager().AddAction("ACTION", Keystroke.PressAndReleaseCombo, [Key.Ctrl.value, Key.Space.value])
        Overlay().EndDraw()

    @staticmethod
    def DistanceToDestination(cached_data: CacheData):
        account = GLOBAL_CACHE.ShMem.GetAccountDataFromEmail(cached_data.account_email)
        options = GLOBAL_CACHE.ShMem.GetHeroAIOptionsFromEmail(cached_data.account_email)
        
        if not account:
            return 0.0
        
        if not options:
            return 0.0
                
        if options.IsFlagged:
            if account.AgentPartyData.PartyPosition == 0:
                destination = (options.AllFlag.x, options.AllFlag.y)
            else:
                destination = (options.FlagPos.x, options.FlagPos.y)
        else:
            destination = Agent.GetXY(GLOBAL_CACHE.Party.GetPartyLeaderID())
        return Utils.Distance(destination, Agent.GetXY(Player.GetAgentID()))

    @staticmethod
    def _handle_settings():
        if HeroAI_FloatingWindows.SETTINGS_THROTTLE.IsExpired():
            HeroAI_FloatingWindows.SETTINGS_THROTTLE.Reset()
                            
            if not HeroAI_FloatingWindows.settings.ensure_initialized(): 
                HeroAI_FloatingWindows.SETTINGS_THROTTLE.SetThrottleTime(50)                              
                HeroAI_FloatingWindows.hero_windows.clear()
                info = HeroAI_FloatingWindows.settings.get_hero_panel_info(HeroAI_FloatingWindows.command_panel_window.window_name)
                HeroAI_FloatingWindows.command_panel_window.window_pos = (info.x, info.y)
                HeroAI_FloatingWindows.command_panel_window.first_run = True             
                return
            
            elif HeroAI_FloatingWindows.SETTINGS_THROTTLE.throttle_time != 1000:
                HeroAI_FloatingWindows.SETTINGS_THROTTLE.SetThrottleTime(1000)
            
            HeroAI_FloatingWindows.settings.write_settings()
            
    @staticmethod
    def combined_hero_panel(own_data : AccountStruct, cached_data: CacheData):
        combined_identifier = "combined_hero_panel"
        accounts = cached_data.party.accounts.values()
        
        if not HeroAI_FloatingWindows.settings.ShowPanelOnlyOnLeaderAccount or own_data.AgentPartyData.IsPartyLeader:
            if HeroAI_FloatingWindows.settings.ShowHeroPanels:
                messages = GLOBAL_CACHE.ShMem.GetAllMessages()
            
                if HeroAI_FloatingWindows.settings.CombinePanels:
                                
                    if not combined_identifier in HeroAI_FloatingWindows.hero_windows:
                        info = HeroAI_FloatingWindows.settings.get_hero_panel_info(combined_identifier)
                        HeroAI_FloatingWindows.hero_windows[combined_identifier] = WindowModule(
                            module_name=f"HeroAI - {combined_identifier}",
                            window_name=f"Heroes##HeroAI - {combined_identifier}",
                            window_pos=(info.x, info.y),
                            collapse=info.collapsed,
                            can_close=True,
                        )
                        
                    open = HeroAI_FloatingWindows.hero_windows[combined_identifier].begin(True, PyImGui.WindowFlags.AlwaysAutoResize)
                
                for account in accounts:
                    if not account.AccountEmail or not account.IsAccount:
                        continue
                
                    if account.AccountEmail == Player.GetAccountEmail() and not HeroAI_FloatingWindows.settings.ShowLeaderPanel:
                        continue
                    
                    if not HeroAI_FloatingWindows.settings.CombinePanels:
                        email = account.AccountEmail
                        
                        if not email in HeroAI_FloatingWindows.hero_windows:
                            ConsoleLog("HeroAI", f"Creating Hero Panel for account: {email}")
                            
                            info = HeroAI_FloatingWindows.settings.get_hero_panel_info(email)
                            HeroAI_FloatingWindows.hero_windows[email] = WindowModule(
                                module_name=f"HeroAI - {email}",
                                window_name=f"##HeroAI - {email}",
                                window_pos=(info.x, info.y),
                                collapse=info.collapsed, 
                                can_close=True,
                            )
                            
                        draw_hero_panel(HeroAI_FloatingWindows.hero_windows[email], account, cached_data, messages)
                    else:                    
                        draw_combined_hero_panel(account, cached_data, messages)
                        
                if HeroAI_FloatingWindows.settings.CombinePanels:
                    HeroAI_FloatingWindows.hero_windows[combined_identifier].end()
                    
                    if HeroAI_FloatingWindows.hero_windows[combined_identifier].changed:
                        info = HeroAI_FloatingWindows.settings.get_hero_panel_info(combined_identifier)                        
                        info.x = round(HeroAI_FloatingWindows.hero_windows[combined_identifier].window_pos[0])
                        info.y = round(HeroAI_FloatingWindows.hero_windows[combined_identifier].window_pos[1])
                        info.collapsed = HeroAI_FloatingWindows.hero_windows[combined_identifier].collapse
                        info.open = HeroAI_FloatingWindows.hero_windows[combined_identifier].open
                        HeroAI_FloatingWindows.settings.save_settings()
        
    @staticmethod
    def show_ui(cached_data: CacheData):
        from Py4GWCoreLib.Party import Party
        show_ui = not UIManager.IsWorldMapShowing() and not Map.IsMapLoading() and not Map.IsInCinematic() and not Map.Pregame.InCharacterSelectScreen() and Party.IsPartyLoaded()
        if show_ui:  
            own_data = GLOBAL_CACHE.ShMem.GetAccountDataFromEmail(cached_data.account_email)
            if not own_data:
                return
            
            HeroAI_FloatingWindows.combined_hero_panel(own_data, cached_data)

            if HeroAI_FloatingWindows.settings.ShowPartyOverlay:
                draw_party_overlay(cached_data, HeroAI_FloatingWindows.hero_windows)
                
            if HeroAI_FloatingWindows.settings.ShowPartySearchOverlay:
                draw_party_search_overlay(cached_data)
            
            if (HeroAI_FloatingWindows.settings.ShowCommandPanel and (own_data.AgentPartyData.IsPartyLeader or not HeroAI_FloatingWindows.settings.ShowCommandPanelOnlyOnLeaderAccount) 
                ):
                draw_command_panel(HeroAI_FloatingWindows.command_panel_window, cached_data)
            
            if HeroAI_FloatingWindows.settings.CommandHotBars:
                draw_hotbars(cached_data)
                
            draw_dialog_overlay(cached_data, HeroAI_FloatingWindows.messages)
    
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
    capture_hero_index = -1
    capture_hero_flag = False
    capture_flag_all = False
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
            account = GLOBAL_CACHE.ShMem.GetAccountDataFromPartyNumber(index)
            
            if account and account.IsSlotActive:
                if Agent.IsPlayer(account.AgentData.AgentID):
                    player_name = Agent.GetNameByID(account.AgentData.AgentID)
                else:
                    player_name = GLOBAL_CACHE.Party.Heroes.GetNameByAgentID(account.AgentData.AgentID)

                if PyImGui.tree_node(f"{player_name}##DebugBuffsPlayer{index}"):
                    # Retrieve buffs for the player
                    player_buffs = account.AgentData.Buffs.Buffs
                    headers = ["Skill ID", "Skill Name"]
                    data = [(buff.SkillId, GLOBAL_CACHE.Skill.GetName(buff.SkillId)) for buff in player_buffs]
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

                        self_id = Player.GetAgentID()

                        pet_id = GLOBAL_CACHE.Party.Pets.GetPetID(Player.GetAgentID())

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
                            is_casting = Agent.IsCasting(Player.GetAgentID())
                            casting_skill = Agent.GetCastingSkillID(Player.GetAgentID())
                            skillbar_casting = GLOBAL_CACHE.SkillBar.GetCasting()
                            skillbar_recharge = cached_data.combat_handler.skills[HeroAI_Windows.skill_slot].skillbar_data.recharge
                            player_agent_id = Player.GetAgentID()
                            current_energy = Agent.GetEnergy(player_agent_id) * Agent.GetMaxEnergy(player_agent_id)
                            ordered_skill = cached_data.combat_handler.GetOrderedSkill(HeroAI_Windows.skill_slot)
                            if ordered_skill:                        
                                energy_cost = GLOBAL_CACHE.Skill.Data.GetEnergyCost(ordered_skill.skill_id)
                                current_hp = Agent.GetHealth(Player.GetAgentID())
                                target_hp = ordered_skill.custom_skill_data.Conditions.SacrificeHealth
                                health_cost = GLOBAL_CACHE.Skill.Data.GetHealthCost(ordered_skill.skill_id)

                                adrenaline_required = GLOBAL_CACHE.Skill.Data.GetAdrenaline(ordered_skill.skill_id)
                                adrenaline_a = ordered_skill.skillbar_data.adrenaline_a

                                current_overcast = Agent.GetOvercast(Player.GetAgentID())
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
        global show_broadcast_follow_positions, show_broadcast_follow_threshold_rings
        shmem = GLOBAL_CACHE.ShMem
        party = GLOBAL_CACHE.Party
        party_heroes = party.Heroes
        active_account_option_pairs: list[tuple[AccountStruct, HeroAIOptionStruct]] = shmem.GetAllActiveAccountHeroAIPairs(sort_results=False)
        options_by_party: list[HeroAIOptionStruct | None] = [None] * MAX_NUM_PLAYERS
        accounts_by_party: list[AccountStruct | None] = [None] * MAX_NUM_PLAYERS

        # Build once per frame, keyed by party position; source is active IsAccount-only.
        for account, options in active_account_option_pairs:
            party_index: int = account.AgentPartyData.PartyPosition
            if 0 <= party_index < MAX_NUM_PLAYERS:
                accounts_by_party[party_index] = account
                options_by_party[party_index] = options

        leader_options: HeroAIOptionStruct | None = options_by_party[0]
        
        if HeroAI_Windows.capture_hero_flag:
            x, y, _ = Overlay().GetMouseWorldPos()
            if HeroAI_Windows.capture_flag_all:
                DrawFlagAll(x, y)
            else:
                DrawHeroFlag(x, y)

            mouse_clicked = PyImGui.is_mouse_clicked(0)
            if mouse_clicked and HeroAI_Windows.one_time_set_flag:
                HeroAI_Windows.one_time_set_flag = False
                return

            if mouse_clicked:
                capture_index = HeroAI_Windows.capture_hero_index
                hero_count = party.GetHeroCount()

                if 0 < capture_index <= hero_count:
                    if not HeroAI_Windows.capture_flag_all:
                        agent_id = party_heroes.GetHeroAgentIDByPartyPosition(capture_index)
                        party_heroes.FlagHero(agent_id, x, y)
                        HeroAI_Windows.one_time_set_flag = True
                else:
                    if capture_index == 0:
                        hero_ai_index = 0
                        party_heroes.FlagAllHeroes(x, y)
                    else:
                        hero_ai_index = capture_index - hero_count

                    options: HeroAIOptionStruct | None = options_by_party[hero_ai_index] if 0 <= hero_ai_index < MAX_NUM_PLAYERS else None
                    if options:
                        if capture_index == 0:
                            options.AllFlag.x = x
                            options.AllFlag.y = y
                        else:
                            options.FlagPos.x = x
                            options.FlagPos.y = y
                        options.IsFlagged = True
                        options.FlagFacingAngle = Agent.GetRotationAngle(party.GetPartyLeaderID())

                    HeroAI_Windows.one_time_set_flag = True

                HeroAI_Windows.capture_flag_all = False
                HeroAI_Windows.capture_hero_flag = False
                HeroAI_Windows.one_time_set_flag = False
                capture_mouse_timer.Stop()

        #All flag is handled by the game even with no heroes
        if leader_options and leader_options.IsFlagged:
            DrawFlagAll(leader_options.AllFlag.x, leader_options.AllFlag.y)
            
        for i in range(1, MAX_NUM_PLAYERS):
            options: HeroAIOptionStruct | None = options_by_party[i]
            if options is None or not options.IsFlagged:
                continue

            account: AccountStruct | None = accounts_by_party[i]
            if account:
                DrawHeroFlag(options.FlagPos.x, options.FlagPos.y)

        if GLOBAL_CACHE.Party.GetPartyLeaderID() == Player.GetAgentID() and Map.IsExplorable():
            if show_broadcast_follow_positions or show_broadcast_follow_threshold_rings:
                segments = 24
                Overlay().BeginDraw()
                for i in range(1, MAX_NUM_PLAYERS):
                    options: HeroAIOptionStruct | None = options_by_party[i]
                    account: AccountStruct | None = accounts_by_party[i]
                    if options is None or account is None or not account.IsSlotActive:
                        continue
                    fx = float(options.FollowPos.x)
                    fy = float(options.FollowPos.y)
                    if abs(fx) < 0.001 and abs(fy) < 0.001:
                        continue
                    fz = Overlay().FindZ(fx, fy, 0)
                    if show_broadcast_follow_positions:
                        Overlay().DrawPoly3D(
                            fx, fy, fz,
                            radius=Range.Touch.value / 3,
                            color=Utils.RGBToColor(0, 255, 255, 140),
                            numsegments=segments,
                            thickness=2.0
                        )
                        Overlay().DrawText3D(
                            fx, fy, fz - 110,
                            f"F{i}",
                            color=Utils.RGBToColor(0, 255, 255, 220),
                            autoZ=False, centered=True, scale=1.8
                        )
                    if show_broadcast_follow_threshold_rings:
                        thr = max(0.0, float(getattr(options, "FollowMoveThreshold", 0.0)))
                        if thr > 0.0:
                            Overlay().DrawPoly3D(
                                fx, fy, fz,
                                radius=thr,
                                color=Utils.RGBToColor(255, 215, 0, 110),
                                numsegments=max(24, segments),
                                thickness=2.0
                        )
            Overlay().EndDraw()

        if HeroAI_Windows.ClearFlags:
            for i in range(MAX_NUM_PLAYERS):
                options: HeroAIOptionStruct | None = options_by_party[i]
            
                if options:
                    options.IsFlagged = False
                    options.FlagPos.x = 0.0
                    options.FlagPos.y = 0.0
                    options.AllFlag.x = 0.0
                    options.AllFlag.y = 0.0
                    options.FlagFacingAngle = 0.0
                    
                party_heroes.UnflagHero(i)
                
            party_heroes.UnflagAllHeroes()
            HeroAI_Windows.ClearFlags = False
                
        
    @staticmethod
    def DrawFlaggingWindow(cached_data:CacheData):
        party_size = GLOBAL_CACHE.Party.GetPartySize()
        if party_size == 1:
            PyImGui.text("No Follower or Heroes to Flag.")
            return

        #if PyImGui.collapsing_header("Flagging"):
        if PyImGui.button("Pin Down Flag Position"):
            leader_x, leader_y = Agent.GetXY(GLOBAL_CACHE.Party.GetPartyLeaderID())
            leader_options = GLOBAL_CACHE.ShMem.GetHeroAIOptionsByPartyNumber(0)
            if leader_options:
                leader_options.AllFlag.x = leader_x
                leader_options.AllFlag.y = leader_y
                leader_options.IsFlagged = True
                leader_options.FlagFacingAngle = Agent.GetRotationAngle(GLOBAL_CACHE.Party.GetPartyLeaderID())
            GLOBAL_CACHE.Party.Heroes.FlagAllHeroes(leader_x, leader_y)
            HeroAI_Windows.AllFlag = True
            HeroAI_Windows.capture_hero_flag = False
            HeroAI_Windows.capture_flag_all = False
            HeroAI_Windows.capture_hero_index = 0
            HeroAI_Windows.one_time_set_flag = False
            capture_mouse_timer.Stop()
            
        if PyImGui.begin_table("Flags",3):
            PyImGui.table_next_row()
            PyImGui.table_next_column()
            if party_size >= 2:
                HeroAI_Windows.HeroFlags[0] = ImGui.toggle_button("1", IsHeroFlagged(1), 30, 30)
            PyImGui.table_next_column()
            if party_size >= 3:
                HeroAI_Windows.HeroFlags[1] = ImGui.toggle_button("2", IsHeroFlagged(2),30,30)
            PyImGui.table_next_column()
            if party_size >= 4:
                HeroAI_Windows.HeroFlags[2] = ImGui.toggle_button("3", IsHeroFlagged(3),30,30)
            PyImGui.table_next_row()
            PyImGui.table_next_column()
            if party_size >= 5:
                HeroAI_Windows.HeroFlags[3] = ImGui.toggle_button("4", IsHeroFlagged(4),30,30)
            PyImGui.table_next_column()
            HeroAI_Windows.AllFlag = ImGui.toggle_button("All", IsHeroFlagged(0), 30, 30)
            PyImGui.table_next_column()
            if party_size >= 6:
                HeroAI_Windows.HeroFlags[4] = ImGui.toggle_button("5", IsHeroFlagged(5),30,30)
            PyImGui.table_next_row()
            PyImGui.table_next_column()
            if party_size >= 7:
                HeroAI_Windows.HeroFlags[5] = ImGui.toggle_button("6", IsHeroFlagged(6),30,30)
            PyImGui.table_next_column()
            if party_size >= 8:
                HeroAI_Windows.HeroFlags[6] = ImGui.toggle_button("7", IsHeroFlagged(7), 30, 30)
            PyImGui.table_next_column()
            HeroAI_Windows.ClearFlags = ImGui.toggle_button("X", HeroAI_Windows.HeroFlags[7],30,30)
            PyImGui.end_table()
                    
                    
        if HeroAI_Windows.AllFlag != IsHeroFlagged(0):
            HeroAI_Windows.capture_hero_flag = True
            HeroAI_Windows.capture_flag_all = True
            HeroAI_Windows.capture_hero_index = 0
            HeroAI_Windows.one_time_set_flag = False
            capture_mouse_timer.Start()

        for i in range(1, party_size):
            if HeroAI_Windows.HeroFlags[i-1] != IsHeroFlagged(i):
                HeroAI_Windows.capture_hero_flag = True
                HeroAI_Windows.capture_flag_all = False
                HeroAI_Windows.capture_hero_index = i
                HeroAI_Windows.one_time_set_flag = False
                capture_mouse_timer.Start()
            
    

    @staticmethod
    def DrawPlayersDebug(cached_data:CacheData):
        global MAX_NUM_PLAYERS

        own_party_number = GLOBAL_CACHE.Party.GetOwnPartyNumber()
        PyImGui.text(f"Own Party Number: {own_party_number}")
        HeroAI_Windows.slot_to_write = PyImGui.input_int("Slot to write", HeroAI_Windows.slot_to_write)

        if PyImGui.button("Submit"):
            self_id = Player.GetAgentID()
            account = GLOBAL_CACHE.ShMem.GetAllAccounts().AccountData[HeroAI_Windows.slot_to_write]
            options = GLOBAL_CACHE.ShMem.GetAllAccounts().HeroAIOptions[HeroAI_Windows.slot_to_write]

            account.AgentData.AgentID = self_id
            player_id = Player.GetAgentID()
            account.AgentData.Energy.Regen = Agent.GetEnergyRegen(player_id)
            account.AgentData.Energy.Current = Agent.GetEnergy(player_id)
            account.AgentData.Energy.Max = Agent.GetMaxEnergy(player_id)
            account.AgentData.Energy.Pips = Utils.calculate_energy_pips(account.AgentData.Energy.Max, account.AgentData.Energy.Regen)
            account.IsSlotActive = True
            account.IsHero = False
            
            options.IsFlagged = False
            options.FlagPos.x = 0.0
            options.FlagPos.y = 0.0
            options.AllFlag.x = 0.0
            options.AllFlag.y = 0.0

        headers = ["Slot","PlayerID", "EnergyRegen", "Energy", "IsSlotActive", "IsHero", "IsFlagged", "FlagPosX", "FlagPosY", "AllFlagX", "AllFlagY", "LastUpdated"]

        data = []
        for i in range(MAX_NUM_PLAYERS):
            account = GLOBAL_CACHE.ShMem.GetAccountDataFromPartyNumber(i)
            options = GLOBAL_CACHE.ShMem.GetHeroAIOptionsByPartyNumber(i)
            if account and options:
                data.append((
                    i,  # Slot index
                    account.AgentData.AgentID,
                    f"{account.AgentData.Energy.Regen:.4f}", 
                    f"{account.AgentData.Energy.Current:.4f}",       
                    account.IsSlotActive,
                    account.IsHero,
                    options.IsFlagged,
                    f"{options.FlagPos.x:.4f}",
                    f"{options.FlagPos.y:.4f}",
                    f"{options.AllFlag.x:.4f}",
                    f"{options.AllFlag.y:.4f}",
                    account.LastUpdated
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
            cached_data.global_options.Following,
            cached_data.global_options.Avoidance,
            cached_data.global_options.Looting,
            cached_data.global_options.Targeting,
            cached_data.global_options.Combat,
        ]

        row += [
            cached_data.global_options.Skills[j] for j in range(NUMBER_OF_SKILLS)
        ]
        data.append(tuple(row))
        ImGui.table("Control Debug Table", headers, data)

        headers = ["Slot", "Following", "Avoidance", "Looting", "Targeting", "Combat"]
        headers += [f"Skill {j + 1}" for j in range(NUMBER_OF_SKILLS)] 

        data = []
        for i in range(MAX_NUM_PLAYERS):
            options = GLOBAL_CACHE.ShMem.GetHeroAIOptionsByPartyNumber(i)
            
            if options is None:
                continue
            
            row = [
                i,  
                options.Following,
                options.Avoidance,
                options.Looting,
                options.Targeting,
                options.Combat
            ]

            row += [
                options.Skills[j] for j in range(NUMBER_OF_SKILLS)
            ]

            data.append(tuple(row))

        ImGui.table("Game Options Debug Table", headers, data)

    @staticmethod
    def DrawFlagDebug(cached_data:CacheData):
        global MAX_NUM_PLAYERS
        
        PyImGui.text("Flag Debug")
        PyImGui.text(f"HeroAI_Windows.capture_flag_all: {HeroAI_Windows.capture_flag_all}")
        PyImGui.text(f"HeroAI_Windows.capture_hero_flag: {HeroAI_Windows.capture_hero_flag}")
        if PyImGui.button("Toggle Flags"):
            HeroAI_Windows.capture_flag_all = not HeroAI_Windows.capture_flag_all
            HeroAI_Windows.capture_hero_flag = not HeroAI_Windows.capture_hero_flag

        PyImGui.separator()

        x, y, z = Overlay().GetMouseWorldPos()

        PyImGui.text(f"Mouse Position: {x:.2f}, {y:.2f}, {z:.2f}")
        PyImGui.text_colored("Having GetMouseWorldPos active will crash your client on map change",(1, 0.5, 0.05, 1))
        mouse_x, mouse_y = Overlay().GetMouseCoords()
        PyImGui.text(f"Mouse Coords: {mouse_x}, {mouse_y}")
        PyImGui.text(f"Player Position: {Agent.GetXYZ(Player.GetAgentID())}")
        HeroAI_Windows.draw_fake_flag = PyImGui.checkbox("Draw Fake Flag", HeroAI_Windows.draw_fake_flag)

        if HeroAI_Windows.draw_fake_flag:
            DrawFlagAll(x, y)

        PyImGui.separator()

        PyImGui.text(f"HeroAI_Windows.AllFlag: {HeroAI_Windows.AllFlag}")
        PyImGui.text(f"HeroAI_Windows.capture_hero_index: {HeroAI_Windows.capture_hero_index}")

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
        PyImGui.text(f"IsMelee: {Agent.IsMelee(Player.GetAgentID())}")
        PyImGui.text(f"stay_alert_timer: {cached_data.stay_alert_timer.GetElapsedTime()}")
        PyImGui.text(f"Leader Rotation Angle: {Agent.GetRotationAngle(GLOBAL_CACHE.Party.GetPartyLeaderID())}")
        PyImGui.text(f"old_leader_rotation_angle: {cached_data.data.old_angle}")
        PyImGui.text(f"Angle_changed: {cached_data.data.angle_changed}")

        segments = 32
        Overlay().BeginDraw()
        if show_area_rings:
            player_x, player_y, player_z = Agent.GetXYZ(Player.GetAgentID()) #cached_data.data.player_xyz # needs to be live

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
                account = GLOBAL_CACHE.ShMem.GetAccountDataFromPartyNumber(i)
            
                if account and account.IsSlotActive:
                    Overlay().BeginDraw()
                    player_id = account.AgentData.AgentID
                    if player_id == Player.GetAgentID():
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
            
            sender_email = cached_data.account_email
            for account in cached_data.party:
                ConsoleLog("Messaging", f"Sending Pcon Message to  {account.AccountEmail}")
                
                GLOBAL_CACHE.ShMem.SendMessage(sender_email, account.AccountEmail, SharedCommandType.PCon, params)

        if ImGui.colored_button(f"{IconsFontAwesome5.ICON_TIMES}##commands_resign", HeroAI_Windows.ButtonColors["Resign"].button_color, HeroAI_Windows.ButtonColors["Resign"].hovered_color, HeroAI_Windows.ButtonColors["Resign"].active_color):
        #if PyImGui.button(f"{IconsFontAwesome5.ICON_TIMES}##commands_resign"):
            accounts = cached_data.party.accounts.values()
            
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
            
            sender_email = cached_data.account_email
            for account in cached_data.party.accounts.values():
                if self_account.AccountEmail == account.AccountEmail:
                    continue
                ConsoleLog("Messaging", "Pixelstacking account: " + account.AccountEmail)
                GLOBAL_CACHE.ShMem.SendMessage(sender_email, account.AccountEmail, SharedCommandType.PixelStack, (self_account.AgentData.Pos.x,self_account.AgentData.Pos.y,0,0))
        ImGui.show_tooltip("Pixel Stack (Carto Helper)")
        
        PyImGui.same_line(0,-1)

        if PyImGui.button(f"{IconsFontAwesome5.ICON_HAND_POINT_RIGHT}##commands_InteractTarget"):
            target = Player.GetTargetID()
            if target == 0:
                ConsoleLog("Messaging", "No target to interact with.")
                return
            self_account = GLOBAL_CACHE.ShMem.GetAccountDataFromEmail(cached_data.account_email)
            if not self_account:
                return
            
            sender_email = cached_data.account_email
            for account in cached_data.party.accounts.values():
                if self_account.AccountEmail == account.AccountEmail:
                    continue
                ConsoleLog("Messaging", f"Ordering {account.AccountEmail} to interact with target: {target}")
                GLOBAL_CACHE.ShMem.SendMessage(sender_email, account.AccountEmail, SharedCommandType.InteractWithTarget, (target,0,0,0))
        ImGui.show_tooltip("Interact with Target")
        PyImGui.same_line(0,-1)

        if PyImGui.button(f"{IconsFontAwesome5.ICON_COMMENT_DOTS}##commands_takedialog"):
            target = Player.GetTargetID()
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
            accounts = cached_data.party.accounts.values()
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
            
    
