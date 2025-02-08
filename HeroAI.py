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

MODULE_NAME = "HeroAI"

from dataclasses import dataclass, field
from typing import List, Tuple

@dataclass
class GameData:
    def __init__(self):
        #Map data
        self.is_map_ready = False
        self.is_outpost = False
        self.is_explorable = False
        self.is_in_cinematic = False
        self.map_id = 0
        self.region = 0
        self.district = 0
        #Party data
        self.is_party_loaded = False
        self.party_leader_id = 0
        self.party_leader_rotation_angle = 0.0
        self.party_leader_xy = (0.0, 0.0)
        self.party_leader_xyz = (0.0, 0.0, 0.0)
        self.own_party_number = 0
        self.heroes = []
        self.party_size = 0
        self.party_player_count = 0
        self.party_hero_count = 0
        self.party_henchman_count = 0
        #Player data
        self.player_agent_id = 0 
        self.login_number = 0
        self.energy_regen = 0
        self.max_energy = 0
        self.energy = 0
        self.player_xy = (0.0, 0.0)
        self.player_xyz = (0.0, 0.0, 0.0)
        self.player_is_casting = False
        self.player_casting_skill = 0
        self.player_skillbar_casting = False
        self.player_hp = 0.0
        self.player_is_alive = True
        self.player_overcast = 0.0
        self.player_is_knocked_down = False
        self.player_is_moving = False
        self.is_melee = False
        #AgentArray data
        self.enemy_array = []
        self.nearest_enemy = 0
        self.lowest_ally = 0
        self.nearest_npc = 0
        self.nearest_item = 0
        self.nearest_spirit = 0
        self.lowest_minion = 0
        self.nearest_corpse = 0
        self.pet_id = 0
        
        #combat field data
        self.in_aggro = False
        self.angle_changed = False
        self.old_angle = 0.0
        self.free_slots_in_inventory = 0
        self.nearest_item = 0
        self.target_id = 0
        
        #control status vars
        self.is_following_enabled = True
        self.is_avoidance_enabled = True
        self.is_looting_enabled = True
        self.is_targetting_enabled = True
        self.is_combat_enabled = True
        self.is_skill_enabled = [True for _ in range(NUMBER_OF_SKILLS)]
        
    def reset(self):
        self.__init__()
        
    def update(self):
        #Map data
        self.is_map_ready = Map.IsMapReady()
        if not self.is_map_ready:
            self.is_party_loaded = False
            return
        self.map_id = Map.GetMapID()
        self.is_outpost = Map.IsOutpost()
        self.is_explorable = Map.IsExplorable()
        self.is_in_cinematic = Map.IsInCinematic()
        self.region, _ = Map.GetRegion()
        self.district = Map.GetDistrict()
        #Party data
        self.is_party_loaded = Party.IsPartyLoaded()
        if not self.is_party_loaded:
            return
        self.party_leader_id = Party.GetPartyLeaderID()
        self.party_leader_rotation_angle = Agent.GetRotationAngle(self.party_leader_id)
        self.party_leader_xy = Agent.GetXY(self.party_leader_id)
        self.party_leader_xyz = Agent.GetXYZ(self.party_leader_id)
        self.own_party_number = Party.GetOwnPartyNumber()
        self.heroes = Party.GetHeroes()
        self.party_size = Party.GetPartySize()
        self.party_player_count = Party.GetPlayerCount()
        self.party_hero_count = Party.GetHeroCount()
        self.party_henchman_count = Party.GetHenchmanCount()
        #Player data
        self.player_agent_id = Player.GetAgentID()
        self.player_login_number = Agent.GetLoginNumber(self.player_agent_id)
        self.energy_regen = Agent.GetEnergyRegen(self.player_agent_id)
        self.max_energy = Agent.GetMaxEnergy(self.player_agent_id)
        self.energy = GetEnergyValues(self.player_agent_id)
        self.player_xy = Agent.GetXY(self.player_agent_id)
        self.player_xyz = Agent.GetXYZ(self.player_agent_id)
        self.player_is_casting = Agent.IsCasting(self.player_agent_id)
        self.player_casting_skill = Agent.GetCastingSkill(self.player_agent_id)
        self.player_skillbar_casting = SkillBar.GetCasting()
        self.player_hp = Agent.GetHealth(self.player_agent_id)
        self.player_is_alive = Agent.IsAlive(self.player_agent_id)
        self.player_overcast = Agent.GetOvercast(self.player_agent_id)
        self.player_is_knocked_down = Agent.IsKnockedDown(self.player_agent_id)
        self.player_is_moving = Agent.IsMoving(self.player_agent_id)
        self.player_is_melee = Agent.IsMelee(self.player_agent_id)
        #AgentArray data
        self.enemy_array = AgentArray.GetEnemyArray()
        self.pet_id = TargetPet(self.player_agent_id)
        #combat field data
        self.free_slots_in_inventory = Inventory.GetFreeSlotCount()
        self.nearest_item = TargetNearestItem()
        self.target_id = Player.GetTargetID()
        
    

    

class CacheData:
    def __init__(self, throttle_time=75):
        self.combat_handler = CombatClass()
        self.HeroAI_vars = HeroAI_varsClass()
        self.HeroAI_windows = HeroAI_Window_varsClass()
        self.game_throttle_time = throttle_time
        self.game_throttle_timer = Timer()
        self.game_throttle_timer.Start()
        self.shared_memory_timer = Timer()
        self.shared_memory_timer.Start()
        self.stay_alert_timer = Timer()
        self.stay_alert_timer.Start()
        self.aftercast_timer = Timer()
        self.data = GameData()
        self.reset()
        
    def reset(self):
        self.data.reset()   
        
 
    def Update(self):
        if self.game_throttle_timer.HasElapsed(self.game_throttle_time):
            self.game_throttle_timer.Reset()
            self.data.reset()
            self.data.update()
            
            if self.stay_alert_timer.HasElapsed(STAY_ALERT_TIME):
                self.data.in_aggro = InAggro(self.data.enemy_array, Range.Earshot.value)
            else:
                self.data.in_aggro = InAggro(self.data.enemy_array, Range.Spellcast.value)
                
            if self.data.in_aggro:
                self.stay_alert_timer.Reset()
                
            if not self.stay_alert_timer.HasElapsed(STAY_ALERT_TIME):
                self.data.in_aggro = True
                
            if self.data.in_aggro:
                distance = Range.Spellcast.value
            else:
                distance = Range.Earshot.value
            
            #control status vars
            self.data.is_following_enabled = IsFollowingEnabled(self.HeroAI_vars.all_game_option_struct,self.data.own_party_number)
            self.data.is_avoidance_enabled = IsAvoidanceEnabled(self.HeroAI_vars.all_game_option_struct,self.data.own_party_number)
            self.data.is_looting_enabled = IsLootingEnabled(self.HeroAI_vars.all_game_option_struct,self.data.own_party_number)
            self.data.is_targetting_enabled = IsTargetingEnabled(self.HeroAI_vars.all_game_option_struct,self.data.own_party_number)
            self.data.is_combat_enabled = IsCombatEnabled(self.HeroAI_vars.all_game_option_struct,self.data.own_party_number)
            for i in range(NUMBER_OF_SKILLS):
                self.data.is_skill_enabled[i] = IsSkillEnabled(self.HeroAI_vars.all_game_option_struct,self.data.own_party_number, i)
                
            self.combat_handler.Update(self.data)
                     

cache_data = CacheData()

def HandleOutOfCombat(cached_data):
    party_number = cached_data.data.own_party_number
    if not cached_data.data.is_combat_enabled:  # halt operation if combat is disabled
        return False
    if cached_data.data.in_aggro:
        return False

    return cached_data.combat_handler.HandleCombat(ooc= True)



def HandleCombat(cached_data):
    party_number = cached_data.data.own_party_number
    if not cached_data.data.is_combat_enabled:  # halt operation if combat is disabled
        return False
    if not cached_data.data.in_aggro:
        return False

    return cached_data.combat_handler.HandleCombat(ooc= False)


looting_item =0
loot_timer = Timer()
loot_timer.Start()

def Loot(cached_data):
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
        Player.ChangeTarget(looting_item)
        #loot_timer.Reset()
        return True
    
    if loot_timer.HasElapsed(500) and target == looting_item:
        Keystroke.PressAndRelease(Key.Space.value)
        loot_timer.Reset()
        #Player.Interact(item)
        return True
    
    return False



def Follow(cached_data):
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
    Player.Move(xx, yy)
    return True




def UpdateStatus(cached_data):

    #if cached_data.shared_memory_timer.HasElapsed(cache_data.game_throttle_time):
    RegisterCandidate(cached_data) 
    UpdateCandidates(cached_data)           
    ProcessCandidateCommands(cached_data)   
    RegisterPlayer(cached_data)   
    RegisterHeroes(cached_data)
    UpdatePlayers(cached_data)      
    UpdateGameOptions(cached_data)   
    #cache_data.shared_memory_timer.Reset()
    
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
    
    cached_data.combat_handler.PrioritizeSkills()
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
    cached_data.combat_handler.ChooseTarget()

   
def configure():
    pass

def main():
    global cache_data
    try:
        cache_data.Update()
        if cache_data.data.is_map_ready and cache_data.data.is_party_loaded:
            UpdateStatus(cache_data)

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

