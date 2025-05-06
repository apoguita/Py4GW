from dataclasses import dataclass, field
from typing import List, Tuple

from .constants import *
from .globals import *
from .targeting import *
from .combat import *
from .custom_skill import CustomSkillClass

@dataclass
class GameData:
    _instance = None  # Singleton instance
    def __new__(cls, name=SHARED_MEMORY_FILE_NAME, num_players=MAX_NUM_PLAYERS):
        if cls._instance is None:
            cls._instance = super(GameData, cls).__new__(cls)
        return cls._instance
    
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
        self.player_is_attacking = False
        self.player_is_moving = False
        self.is_melee = False
        #AgentArray data
        self.nearest_enemy = 0
        self.lowest_ally = 0
        self.nearest_npc = 0
        self.nearest_spirit = 0
        self.lowest_minion = 0
        self.nearest_corpse = 0
        self.pet_id = 0
        
        #combat field data
        self.in_aggro = False
        self.angle_changed = False
        self.old_angle = 0.0
        self.free_slots_in_inventory = 0
        self.target_id = 0
        
        #control status vars
        self.is_following_enabled = True
        self.is_avoidance_enabled = True
        self.is_looting_enabled = True
        self.is_targeting_enabled = True
        self.is_combat_enabled = True
        self.is_skill_enabled = [True for _ in range(NUMBER_OF_SKILLS)]
        self.RAW_AGENT_ARRAY = None
        
        
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
        self.player_energy_regen = Agent.GetEnergyRegen(self.player_agent_id)
        self.player_max_energy = Agent.GetMaxEnergy(self.player_agent_id)
        self.player_energy = Agent.GetEnergy(self.player_agent_id)
        self.player_xy = Agent.GetXY(self.player_agent_id)
        self.player_xyz = Agent.GetXYZ(self.player_agent_id)
        self.player_is_casting = Agent.IsCasting(self.player_agent_id)
        self.player_casting_skill = Agent.GetCastingSkill(self.player_agent_id)
        self.player_skillbar_casting = SkillBar.GetCasting()
        self.player_hp = Agent.GetHealth(self.player_agent_id)
        self.player_is_alive = Agent.IsAlive(self.player_agent_id)
        self.player_overcast = Agent.GetOvercast(self.player_agent_id)
        self.player_is_knocked_down = Agent.IsKnockedDown(self.player_agent_id)
        self.player_is_attacking = Agent.IsAttacking(self.player_agent_id)
        self.player_is_moving = Agent.IsMoving(self.player_agent_id)
        self.player_is_melee = Agent.IsMelee(self.player_agent_id)
        #AgentArray data
        self.pet_id = Party.Pets.GetPetID(self.player_agent_id)
        #combat field data
        self.free_slots_in_inventory = Inventory.GetFreeSlotCount()
        self.target_id = Player.GetTargetID()
        if self.is_outpost:
            if self.RAW_AGENT_ARRAY is None:
                self.RAW_AGENT_ARRAY = RawAgentArray(100)
            self.RAW_AGENT_ARRAY.update() 
        
    
@dataclass
class UIStateData:
    def __init__(self):
        self.show_classic_controls = False

class CacheData:
    _instance = None  # Singleton instance
    def __new__(cls, name=SHARED_MEMORY_FILE_NAME, num_players=MAX_NUM_PLAYERS):
        if cls._instance is None:
            cls._instance = super(CacheData, cls).__new__(cls)
            cls._instance._initialized = False  # Ensure __init__ runs only once
        return cls._instance
    
    def __init__(self, throttle_time=75):
        if not self._initialized:
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
            self.auto_attack_timer = Timer()
            self.auto_attack_timer.Start()
            self.auto_attack_time = 100
            self.draw_floating_loot_buttons = False
            self.reset()
            self.ui_state_data = UIStateData()
            
            self._initialized = True 
        
    def reset(self):
        self.data.reset()   
        
    def InAggro(self, enemy_array, aggro_range = Range.Earshot.value):
        distance = aggro_range
        enemy_array = AgentArray.Filter.ByCondition(enemy_array, lambda agent_id: Utils.Distance(Player.GetXY(), Agent.GetXY(agent_id)) <= distance)
        enemy_array = AgentArray.Filter.ByCondition(enemy_array, lambda agent_id: Agent.IsAlive(agent_id))
        enemy_array = AgentArray.Filter.ByCondition(enemy_array, lambda agent_id: Player.GetAgentID() != agent_id)
        enemy_array = AgentArray.Sort.ByDistance(enemy_array, Player.GetXY())
        if len(enemy_array) > 0:
            return True
        return False
        
    def UpdateGameOptions(self):
        #control status vars
        self.data.is_following_enabled = self.HeroAI_vars.all_game_option_struct[self.data.own_party_number].Following
        self.data.is_avoidance_enabled = self.HeroAI_vars.all_game_option_struct[self.data.own_party_number].Avoidance
        self.data.is_looting_enabled = self.HeroAI_vars.all_game_option_struct[self.data.own_party_number].Looting
        self.data.is_targeting_enabled = self.HeroAI_vars.all_game_option_struct[self.data.own_party_number].Targeting
        self.data.is_combat_enabled = self.HeroAI_vars.all_game_option_struct[self.data.own_party_number].Combat
        for i in range(NUMBER_OF_SKILLS):
            self.data.is_skill_enabled[i] = self.HeroAI_vars.all_game_option_struct[self.data.own_party_number].Skills[i].Active
        
    def UdpateCombat(self):
        self.combat_handler.Update(self.data)
        self.combat_handler.PrioritizeSkills()
        
    def Update(self):
        try:
            if self.game_throttle_timer.HasElapsed(self.game_throttle_time):
                self.game_throttle_timer.Reset()
                
                # Updating critical data
                self.data.player_agent_id = Player.GetAgentID()
                self.data.player_xy = Agent.GetXY(self.data.player_agent_id)
                self.data.player_is_casting = Agent.IsCasting(self.data.player_agent_id)
                self.data.player_is_moving = Agent.IsMoving(self.data.player_agent_id)
                
                # If moving or casting a spell, limit updates
                if not self.data.player_is_moving and not self.data.player_is_casting:
                    self.data.reset()
                    self.data.update()
                    
                    # Variable combat state update
                    alert_range = Range.Earshot.value
                    if not self.stay_alert_timer.HasElapsed(STAY_ALERT_TIME):
                        alert_range = Range.Spellcast.value
                        
                    self.data.in_aggro = self.InAggro(AgentArray.GetEnemyArray(), alert_range)
                        
                    if self.data.in_aggro:
                        self.stay_alert_timer.Reset()
                        
                    if not self.stay_alert_timer.HasElapsed(STAY_ALERT_TIME):
                        self.data.in_aggro = True
                    
        except Exception as e:
            ConsoleLog(f"Update Cache Data Error:", e)       