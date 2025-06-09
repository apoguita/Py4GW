import Py4GW
from Py4GWCoreLib import MultiThreading, Timer, Range, LootConfig, Routines, Utils, Overlay, IconsFontAwesome5, Keystroke, Key, ImGui, PyImGui
from Py4GWCoreLib import AgentArray, UIManager, ActionQueueManager, SharedCommandType
from Py4GWCoreLib import GLOBAL_CACHE, ConsoleLog

#from HeroAI.types import *
from HeroAI.globals import hero_formation
from HeroAI.constants import MELEE_RANGE_VALUE, RANGED_RANGE_VALUE, FOLLOW_DISTANCE_OUT_OF_COMBAT, MAX_NUM_PLAYERS, PARTY_WINDOW_HASH, PARTY_WINDOW_FRAME_OUTPOST_OFFSETS, PARTY_WINDOW_FRAME_EXPLORABLE_OFFSETS
#from HeroAI.shared_memory_manager import *
from HeroAI.utils import DistanceFromWaypoint, DistanceFromLeader
from HeroAI.players import RegisterPlayer, UpdatePlayers, RegisterHeroes
from HeroAI.game_option import UpdateGameOptions
from HeroAI.windows import DrawMainWindow, DrawControlPanelWindow, DrawMultiboxTools, DrawPanelButtons, DrawCandidateWindow, DrawFlaggingWindow, DrawOptions, DrawFlags, CompareAndSubmitGameOptions, SubmitGameOptions
from HeroAI.windows import DrawMessagingOptions
#from HeroAI.targeting import *
#from HeroAI.combat import *
from HeroAI.cache_data import CacheData
import math
from enum import Enum
import traceback

MODULE_NAME = "HeroAI"

cached_data = CacheData()

def HandleOutOfCombat(cached_data:CacheData):
    if not cached_data.data.is_combat_enabled:  # halt operation if combat is disabled
        return False
    if cached_data.data.in_aggro:
        return False

    return cached_data.combat_handler.HandleCombat(ooc= True)


def HandleCombat(cached_data:CacheData):
    if not cached_data.data.is_combat_enabled:  # halt operation if combat is disabled
        return False
    if not cached_data.data.in_aggro:
        return False

    return cached_data.combat_handler.HandleCombat(ooc= False)


cached_data.in_looting_routine = False

def LootingRoutineActive():
    account_email = GLOBAL_CACHE.Player.GetAccountEmail()
    index, message = GLOBAL_CACHE.ShMem.PreviewNextMessage(account_email)
    
    if index == -1 or message is None:
        return False
    
    if message.Command != SharedCommandType.PickUpLoot:
        return False
    return True

def Loot(cached_data:CacheData):
    if not cached_data.data.is_looting_enabled:  # halt operation if looting is disabled
        return False
    
    if cached_data.data.in_aggro:
        return False
    
    if LootingRoutineActive():
        return True
    
    if GLOBAL_CACHE.Inventory.GetFreeSlotCount() < 1:
        return False

    loot_array = LootConfig().GetfilteredLootArray(Range.Earshot.value, multibox_loot= True) # Changed for LootManager - aC
    if len(loot_array) == 0:
        cached_data.in_looting_routine = False
        return False

    cached_data.in_looting_routine = True
    self_account = GLOBAL_CACHE.ShMem.GetAccountDataFromEmail(cached_data.account_email)
    if not self_account:
        cached_data.in_looting_routine = False
        return False
    
    GLOBAL_CACHE.ShMem.SendMessage(self_account.AccountEmail, self_account.AccountEmail, SharedCommandType.PickUpLoot, (0,0,0,0))
    return True


following_flag = False
def Follow(cached_data:CacheData):
    global MELEE_RANGE_VALUE, RANGED_RANGE_VALUE, FOLLOW_DISTANCE_ON_COMBAT, following_flag
    
    if GLOBAL_CACHE.Player.GetAgentID() == GLOBAL_CACHE.Party.GetPartyLeaderID():
        cached_data.follow_throttle_timer.Reset()
        return False
    
    party_number = cached_data.data.own_party_number
    if not cached_data.data.is_following_enabled:  # halt operation if following is disabled
        return False

    follow_x = 0.0
    follow_y = 0.0
    follow_angle = -1.0

    if cached_data.HeroAI_vars.all_player_struct[party_number].IsFlagged: #my own flag
        follow_x = cached_data.HeroAI_vars.all_player_struct[party_number].FlagPosX
        follow_y = cached_data.HeroAI_vars.all_player_struct[party_number].FlagPosY
        follow_angle = cached_data.HeroAI_vars.all_player_struct[party_number].FollowAngle
        following_flag = True
    elif cached_data.HeroAI_vars.all_player_struct[0].IsFlagged:  # leader's flag
        follow_x = cached_data.HeroAI_vars.all_player_struct[0].FlagPosX
        follow_y = cached_data.HeroAI_vars.all_player_struct[0].FlagPosY
        follow_angle = cached_data.HeroAI_vars.all_player_struct[0].FollowAngle
        following_flag = False
    else:  # follow leader
        following_flag = False
        follow_x, follow_y = cached_data.data.party_leader_xy
        follow_angle = cached_data.data.party_leader_rotation_angle

    if cached_data.data.is_melee:
        FOLLOW_DISTANCE_ON_COMBAT = MELEE_RANGE_VALUE
    else:
        FOLLOW_DISTANCE_ON_COMBAT = RANGED_RANGE_VALUE

    if cached_data.data.in_aggro:
        follow_distance = FOLLOW_DISTANCE_ON_COMBAT
    else:
        follow_distance = FOLLOW_DISTANCE_OUT_OF_COMBAT

    angle_changed_pass = False
    if cached_data.data.angle_changed and (not cached_data.data.in_aggro):
        angle_changed_pass = True

    close_distance_check =  (DistanceFromWaypoint(follow_x, follow_y) <= follow_distance)
    
    if not angle_changed_pass and close_distance_check:
        return False
    

    hero_grid_pos = party_number + cached_data.data.party_hero_count + cached_data.data.party_henchman_count
    angle_on_hero_grid = follow_angle + Utils.DegToRad(hero_formation[hero_grid_pos])

    #if IsPointValid(follow_x, follow_y):
    #   return False
    if following_flag:
        xx = follow_x
        yy = follow_y
    else:   
        xx = Range.Touch.value * math.cos(angle_on_hero_grid) + follow_x
        yy = Range.Touch.value * math.sin(angle_on_hero_grid) + follow_y

    cached_data.data.angle_changed = False
    ActionQueueManager().ResetQueue("ACTION")
    #ConsoleLog("HeroAI follow","distance: " + str(DistanceFromWaypoint(follow_x, follow_y)) + "target: " + str(follow_distance))
    GLOBAL_CACHE.Player.Move(xx, yy)
    #ActionQueueManager().AddAction("ACTION", Player.Move, xx, yy)
    return True
    


def draw_Targeting_floating_buttons(cached_data:CacheData):
    if not cached_data.option_show_floating_targets:
        return
    if not GLOBAL_CACHE.Map.IsExplorable():
        return
    player_pos = GLOBAL_CACHE.Player.GetXY()
    enemy_array = Routines.Agents.GetFilteredEnemyArray(player_pos[0], player_pos[1], Range.SafeCompass.value)

    if len(enemy_array) == 0:
        return
    
    Overlay().BeginDraw()
    for agent_id in enemy_array:
        x,y,z = GLOBAL_CACHE.Agent.GetXYZ(agent_id)
        screen_x,screen_y = Overlay.WorldToScreen(x,y,z+25)
        if ImGui.floating_button(f"{IconsFontAwesome5.ICON_CROSSHAIRS}##fb_{agent_id}",screen_x,screen_y):         
            GLOBAL_CACHE.Player.ChangeTarget (agent_id)
            GLOBAL_CACHE.Player.Interact (agent_id, True)
            ActionQueueManager().AddAction("ACTION", Keystroke.PressAndReleaseCombo, [Key.Ctrl.value, Key.Space.value])
    Overlay().EndDraw()

      
#TabType 
class TabType(Enum):
    party = 1
    control_panel = 2
    candidates = 3
    flagging = 4
    config = 5
    debug = 6 
    messaging = 7
    
selected_tab:TabType = TabType.party

def DrawFramedContent(cached_data:CacheData,content_frame_id):
    global selected_tab
    
    if selected_tab == TabType.party:
        return
    
    child_left, child_top, child_right, child_bottom = UIManager.GetFrameCoords(content_frame_id) 
    width = child_right - child_left
    height = child_bottom - child_top 

    UIManager().DrawFrame(content_frame_id, Utils.RGBToColor(0, 0, 0, 255))
    
    flags = ( PyImGui.WindowFlags.NoCollapse | 
            PyImGui.WindowFlags.NoTitleBar |
            PyImGui.WindowFlags.NoResize
    )
    PyImGui.push_style_var(ImGui.ImGuiStyleVar.WindowRounding,0.0)
    PyImGui.set_next_window_pos(child_left, child_top)
    PyImGui.set_next_window_size(width, height)
    
    if PyImGui.begin("##heroai_framed_content",True, flags):
        match selected_tab:
            case TabType.control_panel:
                own_party_number = cached_data.data.own_party_number
                if own_party_number == 0:
                    #leader control panel
                    game_option = DrawPanelButtons(cached_data.HeroAI_vars.global_control_game_struct)
                    CompareAndSubmitGameOptions(cached_data,game_option)

                    if PyImGui.collapsing_header("Player Control"):
                        for index in range(MAX_NUM_PLAYERS):
                            if cached_data.HeroAI_vars.all_player_struct[index].IsActive and not cached_data.HeroAI_vars.all_player_struct[index].IsHero:
                                original_game_option = cached_data.HeroAI_vars.all_game_option_struct[index]
                                login_number = GLOBAL_CACHE.Party.Players.GetLoginNumberByAgentID(cached_data.HeroAI_vars.all_player_struct[index].PlayerID)
                                player_name = GLOBAL_CACHE.Party.Players.GetPlayerNameByLoginNumber(login_number)
                                if PyImGui.tree_node(f"{player_name}##ControlPlayer{index}"):
                                    game_option = DrawPanelButtons(original_game_option)
                                    SubmitGameOptions(cached_data, index, game_option, original_game_option)
                                    PyImGui.tree_pop()
                else:
                    #follower control panel
                    original_game_option = cached_data.HeroAI_vars.all_game_option_struct[own_party_number]
                    game_option = DrawPanelButtons(original_game_option)
                    SubmitGameOptions(cached_data,own_party_number,game_option,original_game_option)
            case TabType.candidates:
                DrawCandidateWindow(cached_data)
            case TabType.flagging:
                DrawFlaggingWindow(cached_data)
            case TabType.config:
                DrawOptions(cached_data)
            case TabType.messaging:
                # Placeholder for messaging tab
                DrawMessagingOptions(cached_data)

        
    PyImGui.end()
    PyImGui.pop_style_var(1)
    
       
def DrawEmbeddedWindow(cached_data:CacheData):
    global selected_tab
    parent_frame_id = UIManager.GetFrameIDByHash(PARTY_WINDOW_HASH)   
    outpost_content_frame_id = UIManager.GetChildFrameID( PARTY_WINDOW_HASH, PARTY_WINDOW_FRAME_OUTPOST_OFFSETS)
    explorable_content_frame_id = UIManager.GetChildFrameID( PARTY_WINDOW_HASH, PARTY_WINDOW_FRAME_EXPLORABLE_OFFSETS)
    
    if GLOBAL_CACHE.Map.IsMapReady() and GLOBAL_CACHE.Map.IsExplorable():
        content_frame_id = explorable_content_frame_id
    else:
        content_frame_id = outpost_content_frame_id
        
    left, top, right, bottom = UIManager.GetFrameCoords(parent_frame_id)  
    title_offset = 20
    frame_offset = 5
    height = bottom - top - title_offset
    width = right - left - frame_offset
     
    flags= ImGui.PushTransparentWindow()
    
    PyImGui.set_next_window_pos(left, top-35)
    PyImGui.set_next_window_size(width, 35)
    if PyImGui.begin("embedded contorl panel",True, flags):
        if PyImGui.begin_tab_bar("HeroAITabs"):
            if PyImGui.begin_tab_item(IconsFontAwesome5.ICON_USERS + "Party##PartyTab"):
                selected_tab = TabType.party
                PyImGui.end_tab_item()
            ImGui.show_tooltip("Party")
            if PyImGui.begin_tab_item(IconsFontAwesome5.ICON_RUNNING + "HeroAI##controlpanelTab"):
                selected_tab = TabType.control_panel
                PyImGui.end_tab_item()
            ImGui.show_tooltip("HeroAI Control Panel")
            if PyImGui.begin_tab_item(IconsFontAwesome5.ICON_BULLHORN + "##messagingTab"):
                selected_tab = TabType.messaging
                PyImGui.end_tab_item()
            ImGui.show_tooltip("Messaging")
            if GLOBAL_CACHE.Map.IsOutpost():
                if PyImGui.begin_tab_item(IconsFontAwesome5.ICON_USER_PLUS + "##candidatesTab"):
                    selected_tab = TabType.candidates
                    PyImGui.end_tab_item()
                ImGui.show_tooltip("Candidates")
            else:
                if PyImGui.begin_tab_item(IconsFontAwesome5.ICON_FLAG + "##flaggingTab"):
                    selected_tab = TabType.flagging
                    PyImGui.end_tab_item()
                ImGui.show_tooltip("Flagging")
            if PyImGui.begin_tab_item(IconsFontAwesome5.ICON_COGS + "##configTab"):
                selected_tab = TabType.config
                PyImGui.end_tab_item()
            ImGui.show_tooltip("Config")
            PyImGui.end_tab_bar()
    PyImGui.end()
    
    ImGui.PopTransparentWindow()    
    DrawFramedContent(cached_data,content_frame_id)
    
    

def UpdateStatus(cached_data:CacheData): 
    RegisterPlayer(cached_data)   
    RegisterHeroes(cached_data)
    UpdatePlayers(cached_data)      
    UpdateGameOptions(cached_data)   
    
    cached_data.UpdateGameOptions()

    DrawEmbeddedWindow(cached_data)
    if cached_data.ui_state_data.show_classic_controls:
        DrawMainWindow(cached_data)   
        DrawControlPanelWindow(cached_data)
        DrawMultiboxTools(cached_data)
   
    if not cached_data.data.is_explorable:  # halt operation if not in explorable area
        return
    
    if cached_data.data.is_in_cinematic:  # halt operation during cinematic
        return


    DrawFlags(cached_data)
    
    draw_Targeting_floating_buttons(cached_data)
    
    if (
        not cached_data.data.player_is_alive or
        DistanceFromLeader(cached_data) >= Range.SafeCompass.value or
        cached_data.data.player_is_knocked_down or 
        cached_data.combat_handler.InCastingRoutine() or 
        cached_data.data.player_is_casting
    ):
        return
    
    if LootingRoutineActive():
        return
     
    cached_data.UdpateCombat()
    if HandleOutOfCombat(cached_data):
        return
    
    if cached_data.data.player_is_moving:
        return
    
    if Loot(cached_data):
       return
   
    if cached_data.follow_throttle_timer.IsExpired():
        if Follow(cached_data):
            cached_data.follow_throttle_timer.Reset()
            return
        

    if HandleCombat(cached_data):
        cached_data.auto_attack_timer.Reset()
        return
    
    if not cached_data.data.in_aggro:
        return
    
    target_id = GLOBAL_CACHE.Player.GetTargetID()
    _, target_aliegance = GLOBAL_CACHE.Agent.GetAllegiance(target_id)
     
    if target_id == 0 or GLOBAL_CACHE.Agent.IsDead(target_id) or (target_aliegance != "Enemy"):
        if (cached_data.data.is_combat_enabled and (not cached_data.data.player_is_attacking) and (not cached_data.data.player_is_casting) and (not cached_data.data.player_is_moving)):
            cached_data.combat_handler.ChooseTarget()
            cached_data.auto_attack_timer.Reset()
            return
    
    #auto attack
    if cached_data.auto_attack_timer.HasElapsed(cached_data.auto_attack_time) and cached_data.data.weapon_type != 0:
        if (cached_data.data.is_combat_enabled and (not cached_data.data.player_is_attacking) and (not cached_data.data.player_is_casting) and (not cached_data.data.player_is_moving)):
            cached_data.combat_handler.ChooseTarget()
        cached_data.auto_attack_timer.Reset()
        cached_data.combat_handler.ResetSkillPointer()
        return

    
    
   
def configure():
    pass


def main():
    global cached_data
    try:
        if not Routines.Checks.Map.MapValid():
            return
        
        cached_data.Update()
        if cached_data.data.is_map_ready and cached_data.data.is_party_loaded:
            UpdateStatus(cached_data)



            
    except ImportError as e:
        Py4GW.Console.Log(MODULE_NAME, f"ImportError encountered: {str(e)}", Py4GW.Console.MessageType.Error)
        Py4GW.Console.Log(MODULE_NAME, f"Stack trace: {traceback.format_exc()}", Py4GW.Console.MessageType.Error)
    except ValueError as e:
        Py4GW.Console.Log(MODULE_NAME, f"ValueError encountered: {str(e)}", Py4GW.Console.MessageType.Error)
        Py4GW.Console.Log(MODULE_NAME, f"Stack trace: {traceback.format_exc()}", Py4GW.Console.MessageType.Error)
    except TypeError as e:
        Py4GW.Console.Log(MODULE_NAME, f"TypeError encountered: {str(e)}", Py4GW.Console.MessageType.Error)
        Py4GW.Console.Log(MODULE_NAME, f"Stack trace: {traceback.format_exc()}", Py4GW.Console.MessageType.Error)
    except Exception as e:
        # Catch-all for any other unexpected exceptions
        Py4GW.Console.Log(MODULE_NAME, f"Unexpected error encountered: {str(e)}", Py4GW.Console.MessageType.Error)
        Py4GW.Console.Log(MODULE_NAME, f"Stack trace: {traceback.format_exc()}", Py4GW.Console.MessageType.Error)
    finally:
        pass
        

if __name__ == "__main__":
    main()

