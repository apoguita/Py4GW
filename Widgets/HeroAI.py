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

   
class ItemOwnerCache:
    def __init__(self):
        self.cache = {}  # { item_id: original_owner_id }

    def check_and_cache(self, item_id, owner_id):
        if item_id not in self.cache:
            self.cache[item_id] = owner_id
        return self.cache[item_id]

    def clear_all(self):
        self.cache.clear()


item_owner_cache = ItemOwnerCache()
thread_manager = MultiThreading()
in_looting_routine = False
looting_aftercast = Timer()
looting_aftercast.Start()

def get_looting_array():
    global item_owner_cache
    
    loot_array = AgentArray.GetItemArray()
    
    if not loot_array:
        item_owner_cache.clear_all()
        return []
    
    # Filter valid and in range items
    loot_array = AgentArray.Filter.ByCondition(loot_array, lambda agent_id: Agent.IsValid(agent_id))
    loot_array = AgentArray.Filter.ByDistance(loot_array, Player.GetXY(), Range.Spellcast.value)

    own_party_number = Party.GetOwnPartyNumber()
    player_id = Player.GetAgentID()

    filtered_loot = []

    for item in loot_array:
        item_data = Agent.GetItemAgent(item)
        current_owner_id = item_data.owner_id
        
        cached_owner_id = item_owner_cache.check_and_cache(item_data.item_id, current_owner_id)
        
        if cached_owner_id == player_id:
            filtered_loot.append(item)
        elif cached_owner_id == 0 and own_party_number == 0:
            filtered_loot.append(item)
            
    return filtered_loot


def SequentialLootingRoutine():
    global in_looting_routine, looting_aftercast
    
    filtered_loot = get_looting_array()
    # Loot filtered items
    Routines.Sequential.Items.LootItems(filtered_loot)
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
    
    loot_array = get_looting_array()
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
    ActionQueueManager().AddAction("ACTION", Player.Move, xx, yy)
    return True
    

def draw_looting_floating_buttons():
    gold_coins = get_gold_coin_array()
    if not gold_coins:
        return
    for agent_id in gold_coins:
        x,y,z = Agent.GetXYZ(agent_id)
        screen_x,screen_y = Overlay().WorldToScreen(x,y,z+25)
        if ImGui.floating_button(f"{IconsFontAwesome5.ICON_COINS}##fb_{agent_id}",screen_x,screen_y):
            Player.Interact(agent_id,False)

def draw_targetting_floating_buttons(cached_data:CacheData):
    if not Map.IsExplorable():
        return
    enemies = AgentArray.GetEnemyArray()
    enemies = AgentArray.Filter.ByCondition(enemies, lambda agent_id: Agent.IsAlive(agent_id))
    
    if not enemies:
        return
    for agent_id in enemies:
        x,y,z = Agent.GetXYZ(agent_id)
        screen_x,screen_y = Overlay().WorldToScreen(x,y,z+25)
        if ImGui.floating_button(f"{IconsFontAwesome5.ICON_BULLSEYE}##fb_{agent_id}",screen_x,screen_y):
            ActionQueueManager().AddAction("ACTION", Player.ChangeTarget, agent_id)
            ActionQueueManager().AddAction("ACTION", Player.Interact, agent_id, True)
            ActionQueueManager().AddAction("ACTION", Keystroke.PressAndReleaseCombo, [Key.Ctrl.value, Key.Space.value])

            
            


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

    DrawMainWindow(cached_data)   
    DrawControlPanelWindow(cached_data)
    DrawMultiboxTools(cached_data)
   
    if not cached_data.data.is_explorable:  # halt operation if not in explorable area
        return
    
    if cached_data.data.is_in_cinematic:  # halt operation during cinematic
        return

    DrawFlags(cached_data)
    
    if cached_data.draw_floating_loot_buttons:
        draw_looting_floating_buttons()
    draw_targetting_floating_buttons(cached_data)
    
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
        if cached_data.data.is_combat_enabled and not cached_data.data.player_is_attacking:
            cached_data.combat_handler.ChooseTarget()
        cached_data.auto_attack_timer.Reset()
    

   
def configure():
    pass

def MapValidityCheck():
    if Map.IsMapLoading():
        return False
    if not Map.IsMapReady():
        return False
    if not Party.IsPartyLoaded():
        return False
    return True


def main():
    global cached_data
    try:
        if not MapValidityCheck():
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

