from dataclasses import dataclass

from .constants import SHARED_MEMORY_FILE_NAME, STAY_ALERT_TIME, MAX_NUM_PLAYERS, NUMBER_OF_SKILLS
from .globals import HeroAI_varsClass, HeroAI_Window_varsClass
from .combat import CombatClass
from Py4GWCoreLib import GLOBAL_CACHE
from Py4GWCoreLib import Timer, ThrottledTimer
from Py4GWCoreLib import Range, Utils, ConsoleLog
from Py4GWCoreLib import AgentArray, Weapon

@dataclass
class GameData:
    _instance = None  # Singleton instance
    def __new__(cls, name=SHARED_MEMORY_FILE_NAME, num_players=MAX_NUM_PLAYERS):
        if cls._instance is None:
            cls._instance = super(GameData, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        self.reset()
        
        self.angle_changed = False
        self.old_angle = 0.0
      
        
    def reset(self):
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
        
        #attributes
        self.fast_casting_exists = False
        self.fast_casting_level = 0
        self.expertise_exists = False
        self.expertise_level = 0
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
        self.free_slots_in_inventory = 0
        self.target_id = 0
        self.target_is_alive =  False
        self.weapon_type = 0
        
        #control status vars
        self.is_following_enabled = True
        self.is_avoidance_enabled = True
        self.is_looting_enabled = True
        self.is_targeting_enabled = True
        self.is_combat_enabled = True
        self.is_skill_enabled = [True for _ in range(NUMBER_OF_SKILLS)]
      
        
    def update(self):
        #Map data
        self.is_map_ready = GLOBAL_CACHE.Map.IsMapReady()
        if not self.is_map_ready:
            self.is_party_loaded = False
            return
        self.map_id = GLOBAL_CACHE.Map.GetMapID()
        self.is_outpost = GLOBAL_CACHE.Map.IsOutpost()
        self.is_explorable = GLOBAL_CACHE.Map.IsExplorable()
        self.is_in_cinematic = GLOBAL_CACHE.Map.IsInCinematic()
        self.region, _ = GLOBAL_CACHE.Map.GetRegion()
        self.district = GLOBAL_CACHE.Map.GetDistrict()
        #Party data
        self.is_party_loaded = GLOBAL_CACHE.Party.IsPartyLoaded()
        if not self.is_party_loaded:
            return
        self.party_leader_id = GLOBAL_CACHE.Party.GetPartyLeaderID()
        
        self.party_leader_rotation_angle = GLOBAL_CACHE.Agent.GetRotationAngle(self.party_leader_id)

        if self.old_angle != self.party_leader_rotation_angle:
            self.angle_changed = True
            self.old_angle = self.party_leader_rotation_angle
        #never reset, so if it changed once, it will be true until the move is issued

        
        self.party_leader_xy = GLOBAL_CACHE.Agent.GetXY(self.party_leader_id)
        self.party_leader_xyz = GLOBAL_CACHE.Agent.GetXYZ(self.party_leader_id)
        self.own_party_number = GLOBAL_CACHE.Party.GetOwnPartyNumber()
        self.heroes = GLOBAL_CACHE.Party.GetHeroes()
        self.party_size = GLOBAL_CACHE.Party.GetPartySize()
        self.party_player_count = GLOBAL_CACHE.Party.GetPlayerCount()
        self.party_hero_count = GLOBAL_CACHE.Party.GetHeroCount()
        self.party_henchman_count = GLOBAL_CACHE.Party.GetHenchmanCount()
        #Player data
        self.player_agent_id = GLOBAL_CACHE.Player.GetAgentID()
        self.player_login_number = GLOBAL_CACHE.Agent.GetLoginNumber(self.player_agent_id)
        self.player_energy_regen = GLOBAL_CACHE.Agent.GetEnergyRegen(self.player_agent_id)
        self.player_max_energy = GLOBAL_CACHE.Agent.GetMaxEnergy(self.player_agent_id)
        self.player_energy = GLOBAL_CACHE.Agent.GetEnergy(self.player_agent_id)
        self.player_xy = GLOBAL_CACHE.Agent.GetXY(self.player_agent_id)
        self.player_xyz = GLOBAL_CACHE.Agent.GetXYZ(self.player_agent_id)
        self.player_is_casting = GLOBAL_CACHE.Agent.IsCasting(self.player_agent_id)
        self.player_casting_skill = GLOBAL_CACHE.Agent.GetCastingSkill(self.player_agent_id)
        self.player_skillbar_casting = GLOBAL_CACHE.SkillBar.GetCasting()
        self.player_hp = GLOBAL_CACHE.Agent.GetHealth(self.player_agent_id)
        self.player_is_alive = GLOBAL_CACHE.Agent.IsAlive(self.player_agent_id)
        self.player_overcast = GLOBAL_CACHE.Agent.GetOvercast(self.player_agent_id)
        self.player_is_knocked_down = GLOBAL_CACHE.Agent.IsKnockedDown(self.player_agent_id)
        self.player_is_attacking = GLOBAL_CACHE.Agent.IsAttacking(self.player_agent_id)
        self.player_is_moving = GLOBAL_CACHE.Agent.IsMoving(self.player_agent_id)
        self.player_is_melee = GLOBAL_CACHE.Agent.IsMelee(self.player_agent_id)
        self.weapon_type, _ = GLOBAL_CACHE.Agent.GetWeaponType(self.player_agent_id)
        
        attributes = GLOBAL_CACHE.Agent.GetAttributes(self.player_agent_id)
        self.fast_casting_exists = False
        self.fast_casting_level = 0
        self.expertise_exists = False
        self.expertise_level = 0
        #check for attributes
        for attribute in attributes:
            if attribute.GetName() == "Fast Casting":
                self.fast_casting_exists = True
                self.fast_casting_level = attribute.level
                
            if attribute.GetName() == "Expertise":
                self.expertise_exists = True
                self.expertise_level = attribute.level
            
        #AgentArray data
        self.pet_id = GLOBAL_CACHE.Party.Pets.GetPetID(self.player_agent_id)
        #combat field data
        self.free_slots_in_inventory = GLOBAL_CACHE.Inventory.GetFreeSlotCount()
        self.target_id = GLOBAL_CACHE.Player.GetTargetID()
        self.target_is_alive = GLOBAL_CACHE.Agent.IsAlive(self.target_id)

        
    
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
    
    def GetWeaponAttackAftercast(self):
        """
        Returns the attack speed of the current weapon.
        """
        weapon_type,_ = GLOBAL_CACHE.Agent.GetWeaponType(GLOBAL_CACHE.Player.GetAgentID())
        player = GLOBAL_CACHE.Agent.GetAgentByID(GLOBAL_CACHE.Player.GetAgentID())
        if player is None:
            return 0
        
        attack_speed = player.living_agent.weapon_attack_speed
        attack_speed_modifier = player.living_agent.attack_speed_modifier if player.living_agent.attack_speed_modifier != 0 else 1.0
        
        if attack_speed == 0:
            match weapon_type:
                case Weapon.Bow.value:
                    attack_speed = 2.475
                case Weapon.Axe.value:
                    attack_speed = 1.33
                case Weapon.Hammer.value:
                    attack_speed = 1.75
                case Weapon.Daggers.value:
                    attack_speed = 1.33
                case Weapon.Scythe.value:
                    attack_speed = 1.5
                case Weapon.Spear.value:
                    attack_speed = 1.5
                case Weapon.Sword.value:
                    attack_speed = 1.33
                case Weapon.Scepter.value:
                    attack_speed = 0.5
                case Weapon.Scepter2.value:
                    attack_speed = 0.5
                case Weapon.Wand.value:
                    attack_speed = 0.5
                case Weapon.Staff1.value:
                    attack_speed = 0.5
                case Weapon.Staff.value:
                    attack_speed = 0.5
                case Weapon.Staff2.value:
                    attack_speed = 0.5
                case Weapon.Staff3.value:
                    attack_speed = 0.5
                case _:
                    attack_speed = 0.5
                    
        return int((attack_speed / attack_speed_modifier) * 1000)
    
    def __init__(self, throttle_time=75):
        if not self._initialized:
            self.combat_handler = CombatClass()
            self.HeroAI_vars = HeroAI_varsClass()
            self.HeroAI_windows = HeroAI_Window_varsClass()
            self.name_refresh_throttle = ThrottledTimer(1000)
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
            self.auto_attack_time =  self.GetWeaponAttackAftercast()
            self.draw_floating_loot_buttons = False
            self.reset()
            self.ui_state_data = UIStateData()
            self.follow_throttle_timer = ThrottledTimer(1000)
            
            self._initialized = True 
            
            self.in_looting_routine = False
        
    def reset(self):
        self.data.reset()   
        
    def InAggro(self, enemy_array, aggro_range = Range.Earshot.value):
        distance = aggro_range
        enemy_array = AgentArray.Filter.ByCondition(enemy_array, lambda agent_id: Utils.Distance(GLOBAL_CACHE.Player.GetXY(), GLOBAL_CACHE.Agent.GetXY(agent_id)) <= distance)
        enemy_array = AgentArray.Filter.ByCondition(enemy_array, lambda agent_id: GLOBAL_CACHE.Agent.IsAlive(agent_id))
        enemy_array = AgentArray.Filter.ByCondition(enemy_array, lambda agent_id: GLOBAL_CACHE.Player.GetAgentID() != agent_id)
        enemy_array = AgentArray.Sort.ByDistance(enemy_array, GLOBAL_CACHE.Player.GetXY())
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
        
        if GLOBAL_CACHE.Map.IsMapLoading():
            return
        
        if not GLOBAL_CACHE.Party.IsPartyLoaded():
            return
        
        party_number = GLOBAL_CACHE.Party.GetOwnPartyNumber()
        if party_number > 0:
            return 
        
        if self.name_refresh_throttle.IsExpired():
            self.name_refresh_throttle.Reset()
            if GLOBAL_CACHE.Map.IsOutpost():
                for index in range(MAX_NUM_PLAYERS):
                    candidate = self.HeroAI_vars.all_candidate_struct[index]
                    agent_name = GLOBAL_CACHE.Agent.GetName(candidate.PlayerID)
        
    def UdpateCombat(self):
        self.combat_handler.Update(self.data)
        self.combat_handler.PrioritizeSkills()
        
    def Update(self):
        try:
            if self.game_throttle_timer.HasElapsed(self.game_throttle_time):
                self.game_throttle_timer.Reset()
                self.data.reset()
                self.data.update()
                
                if self.stay_alert_timer.HasElapsed(STAY_ALERT_TIME):
                    self.data.in_aggro = self.InAggro(GLOBAL_CACHE.AgentArray.GetEnemyArray(), Range.Earshot.value)
                else:
                    self.data.in_aggro = self.InAggro(GLOBAL_CACHE.AgentArray.GetEnemyArray(), Range.Spellcast.value)
                    
                if self.data.in_aggro:
                    self.stay_alert_timer.Reset()
                    
                if not self.stay_alert_timer.HasElapsed(STAY_ALERT_TIME):
                    self.data.in_aggro = True
                    
                self.auto_attack_time = self.GetWeaponAttackAftercast()
                
        except Exception as e:
            ConsoleLog(f"Update Cahe Data Error:", e)
                       
            
                     