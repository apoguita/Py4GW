from Py4GWCoreLib import *

from HeroAI.types import *
from HeroAI.globals import *
from HeroAI.constants import MELEE_RANGE_VALUE, RANGED_RANGE_VALUE, FOLLOW_DISTANCE_OUT_OF_COMBAT
from HeroAI.shared_memory_manager import *
from HeroAI.utils import *
from HeroAI.candidates import *
from HeroAI.players import *
from HeroAI.game_option import *
from HeroAI.windows import *
from HeroAI.targeting import *
from HeroAI.combat import *
from HeroAI.cache_data import *

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


thread_manager = MultiThreading(log_actions=True)
in_looting_routine = False
looting_aftercast = Timer()
looting_aftercast.Start()


def SequentialLootingRoutine():
    global in_looting_routine, looting_aftercast
    
    filtered_loot = LootConfig().GetfilteredLootArray(Range.Earshot.value, multibox_loot= True) # Changed for LootManager - aC
    # Loot filtered items
    ActionQueueManager().ResetQueue("ACTION")
    Routines.Sequential.Items.LootItems(filtered_loot,log = False)
    looting_aftercast.Reset()
    in_looting_routine = False



def Loot(cached_data:CacheData):
    global in_looting_routine, looting_aftercast
    if not cached_data.data.is_looting_enabled:  # halt operation if looting is disabled
        return False
    
    if cached_data.data.in_aggro:
        return False
    
    if in_looting_routine:
        return True
    
    if not looting_aftercast.HasElapsed(3000):
        return False
    
    loot_array = LootConfig().GetfilteredLootArray(Range.Earshot.value, multibox_loot= True) # Changed for LootManager - aC
    if len(loot_array) == 0:
        return False

    in_looting_routine = True
    thread_manager.stop_thread("SequentialLootingRoutine")
    thread_manager.add_thread("SequentialLootingRoutine", SequentialLootingRoutine)



def Follow(cached_data:CacheData):
    global MELEE_RANGE_VALUE, RANGED_RANGE_VALUE, FOLLOW_DISTANCE_ON_COMBAT

    leader_id = cached_data.data.party_leader_id
    if leader_id == cached_data.data.player_agent_id:  # halt operation if player is leader
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
    elif cached_data.HeroAI_vars.all_player_struct[0].IsFlagged:  # leader's flag
        follow_x = cached_data.HeroAI_vars.all_player_struct[0].FlagPosX
        follow_y = cached_data.HeroAI_vars.all_player_struct[0].FlagPosY
        follow_angle = cached_data.HeroAI_vars.all_player_struct[0].FollowAngle
    else:  # follow leader
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

    if (cached_data.data.old_angle != follow_angle) and not cached_data.data.angle_changed:
        cached_data.data.old_angle = follow_angle
        cached_data.data.angle_changed = True

    angle_changed_pass = False
    if cached_data.data.angle_changed and not cached_data.data.in_aggro:
        angle_changed_pass = True

    if DistanceFromWaypoint(follow_x, follow_y) <= follow_distance and not angle_changed_pass:
        return False
    
    hero_grid_pos = party_number + cached_data.data.party_hero_count + cached_data.data.party_henchman_count
    angle_on_hero_grid = follow_angle + Utils.DegToRad(hero_formation[hero_grid_pos])

    #if IsPointValid(follow_x, follow_y):
    #   return False

    xx = Range.Touch.value * math.cos(angle_on_hero_grid) + follow_x
    yy = Range.Touch.value * math.sin(angle_on_hero_grid) + follow_y

    cached_data.data.angle_changed = False
    ActionQueueManager().ResetQueue("ACTION")
    ActionQueueManager().AddAction("ACTION", Player.Move, xx, yy)
    return True
    


def draw_Targeting_floating_buttons(cached_data:CacheData):
    if not Map.IsExplorable():
        return
    enemies = AgentArray.GetEnemyArray()
    enemies = AgentArray.Filter.ByCondition(enemies, lambda agent_id: Agent.IsAlive(agent_id))
    
    if not enemies:
        return
    for agent_id in enemies:
        x,y,z = Agent.GetXYZ(agent_id)
        screen_x,screen_y = Overlay.WorldToScreen(x,y,z+25)
        if ImGui.floating_button(f"{IconsFontAwesome5.ICON_BULLSEYE}##fb_{agent_id}",screen_x,screen_y):
            ActionQueueManager().ResetQueue("ACTION")
            ActionQueueManager().AddAction("ACTION", Player.ChangeTarget, agent_id)
            ActionQueueManager().AddAction("ACTION", Player.Interact, agent_id, True)
            ActionQueueManager().AddAction("ACTION", Keystroke.PressAndReleaseCombo, [Key.Ctrl.value, Key.Space.value])

      
#TabType 
class TabType(Enum):
    party = 1
    control_panel = 2
    candidates = 3
    flagging = 4
    config = 5
    debug = 6 
    
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
                                login_number = Party.Players.GetLoginNumberByAgentID(cached_data.HeroAI_vars.all_player_struct[index].PlayerID)
                                player_name = Party.Players.GetPlayerNameByLoginNumber(login_number)
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

        
    PyImGui.end()
    PyImGui.pop_style_var(1)
    
       
def DrawEmbeddedWindow(cached_data:CacheData):
    global selected_tab
    parent_frame_id = UIManager.GetFrameIDByHash(PARTY_WINDOW_HASH)   
    outpost_content_frame_id = UIManager.GetChildFrameID( PARTY_WINDOW_HASH, PARTY_WINDOW_FRAME_OUTPOST_OFFSETS)
    explorable_content_frame_id = UIManager.GetChildFrameID( PARTY_WINDOW_HASH, PARTY_WINDOW_FRAME_EXPLORABLE_OFFSETS)
    
    if Map.IsMapReady() and Map.IsExplorable():
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
            if PyImGui.begin_tab_item(IconsFontAwesome5.ICON_USER_PLUS + "##candidatesTab"):
                selected_tab = TabType.candidates
                PyImGui.end_tab_item()
            ImGui.show_tooltip("Candidates")
            if PyImGui.begin_tab_item(IconsFontAwesome5.ICON_FLAG + "##flaggingTab"):
                selected_tab = TabType.flagging
                PyImGui.end_tab_item()
            ImGui.show_tooltip("Flagging")
            if PyImGui.begin_tab_item(IconsFontAwesome5.ICON_COGS + "##configTab"):
                selected_tab = TabType.config
                PyImGui.end_tab_item()
            ImGui.show_tooltip("Config")
            if PyImGui.begin_tab_item(IconsFontAwesome5.ICON_BUG + "##debugTab"):
                selected_tab = TabType.debug
                PyImGui.end_tab_item()
            ImGui.show_tooltip("Debug Options")
            PyImGui.end_tab_bar()
    PyImGui.end()
    
    ImGui.PopTransparentWindow()    
    DrawFramedContent(cached_data,content_frame_id)
    
    

def UpdateStatus(cached_data:CacheData):
    global in_looting_routine
    
    RegisterCandidate(cached_data) 
    UpdateCandidates(cached_data)           
    ProcessCandidateCommands(cached_data)   
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
    
    if in_looting_routine:
        return
     
    cached_data.UdpateCombat()
    if HandleOutOfCombat(cached_data):
        return
    
    if cached_data.data.player_is_moving:
        return
    
    if Loot(cached_data):
       return
   
    if Follow(cached_data):
        return

    if HandleCombat(cached_data):
        return
    
    #if were here we are not doing anything
    #auto attack
    if cached_data.auto_attack_timer.HasElapsed(cached_data.auto_attack_time):
        if (cached_data.data.is_combat_enabled and (not cached_data.data.player_is_attacking)):
            cached_data.combat_handler.ChooseTarget()
        cached_data.auto_attack_timer.Reset()
        return

   
def configure():
    pass


def main():
    global cached_data
    try:
        if not Routines.Checks.Map.MapValid():
            ActionQueueManager().ResetQueue("ACTION")
            return
        
        cached_data.Update()
        if cached_data.data.is_map_ready and cached_data.data.is_party_loaded:
            UpdateStatus(cached_data)
            ActionQueueManager().ProcessQueue("ACTION")



            
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

