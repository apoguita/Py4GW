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
from HeroAI.targetting import *
from HeroAI.combat import *
from HeroAI.cache_data import *

MODULE_NAME = "HeroAI"

cached_data = CacheData()

def HandleOutOfCombat(cached_data:CacheData):
    party_number = cached_data.data.own_party_number
    if not cached_data.data.is_combat_enabled:  # halt operation if combat is disabled
        return False
    if cached_data.data.in_aggro:
        return False

    return cached_data.combat_handler.HandleCombat(ooc= True)



def HandleCombat(cached_data:CacheData):
    party_number = cached_data.data.own_party_number
    if not cached_data.data.is_combat_enabled:  # halt operation if combat is disabled
        return False
    if not cached_data.data.in_aggro:
        return False

    return cached_data.combat_handler.HandleCombat(ooc= False)


looting_item =0
loot_timer = Timer()
loot_timer.Start()

def Loot(cached_data:CacheData):
    global looting_item
    global loot_timer
    if cached_data.data.in_aggro:  # halt operation if in combat:
        return False
    
    party_number = cached_data.data.own_party_number
    if not cached_data.data.is_looting_enabled:  # halt operation if looting is disabled
        return False
    
    if cached_data.data.free_slots_in_inventory == 0:
        return False
    
    item = cached_data.data.nearest_item
    
    if item == 0:
        looting_item = 0
        return False

    if looting_item != item:
        looting_item = item

    target =cached_data.data.target_id

    if target != looting_item:
        #Player.ChangeTarget(looting_item)
        cached_data.action_queue.add_action(Player.ChangeTarget, looting_item)
        #loot_timer.Reset()
        return True
    
    if loot_timer.HasElapsed(500) and target == looting_item:
        #Keystroke.PressAndRelease(Key.Space.value)
        cached_data.action_queue.add_action(Keystroke.PressAndRelease, Key.Space.value)
        loot_timer.Reset()
        #Player.Interact(item)
        return True
    
    return False



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
    #Player.Move(xx, yy)
    cached_data.action_queue.add_action(Player.Move, xx, yy)
    return True




def UpdateStatus(cached_data:CacheData):
    RegisterCandidate(cached_data) 
    UpdateCandidates(cached_data)           
    ProcessCandidateCommands(cached_data)   
    RegisterPlayer(cached_data)   
    RegisterHeroes(cached_data)
    UpdatePlayers(cached_data)      
    UpdateGameOptions(cached_data)   
    
    cached_data.UpdateGameOptions()
    
    DrawMainWindow(cached_data)   
    DrawControlPanelWindow(cached_data)
    DrawMultiboxTools(cached_data)
    
    if not cached_data.data.is_explorable:  # halt operation if not in explorable area
        return
    
    if cached_data.data.is_in_cinematic:  # halt operation during cinematic
        return
    
    DrawFlags(cached_data)
    
    if (
        not cached_data.data.player_is_alive or
        DistanceFromLeader(cached_data) >= Range.SafeCompass.value or
        cached_data.data.player_is_knocked_down or 
        cached_data.combat_handler.InCastingRoutine()
    ):
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
    if cached_data.data.is_combat_enabled:
        cached_data.combat_handler.ChooseTarget()

   
def configure():
    pass

def main():
    global cached_data
    try:
        cached_data.Update()
        if cached_data.data.is_map_ready and cached_data.data.is_party_loaded:
            UpdateStatus(cached_data)
            
        cached_data.UpdateActionQueue()
            
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

