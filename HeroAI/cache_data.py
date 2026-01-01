from dataclasses import dataclass

from .constants import SHARED_MEMORY_FILE_NAME, STAY_ALERT_TIME, MAX_NUM_PLAYERS, NUMBER_OF_SKILLS
from .globals import HeroAI_varsClass, HeroAI_Window_varsClass
from .combat import CombatClass
from Py4GWCoreLib import GLOBAL_CACHE
from Py4GWCoreLib import Timer, ThrottledTimer
from Py4GWCoreLib import Range, Utils, ConsoleLog
from Py4GWCoreLib import AgentArray, Weapon, Routines

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
        #attributes
        self.fast_casting_exists = False
        self.fast_casting_level = 0
        self.expertise_exists = False
        self.expertise_level = 0

        
        #combat field data
        self.in_aggro = False
        self.weapon_type = 0
        
        #control status vars
        self.is_following_enabled = True
        self.is_avoidance_enabled = True
        self.is_looting_enabled = True
        self.is_targeting_enabled = True
        self.is_combat_enabled = True
        self.is_skill_enabled = [True for _ in range(NUMBER_OF_SKILLS)]
      
        
    def update(self):
        
        #Player data
        attributes = GLOBAL_CACHE.Agent.GetAttributes(GLOBAL_CACHE.Player.GetAgentID())
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
        player_living = GLOBAL_CACHE.Agent.GetLivingAgentByID(GLOBAL_CACHE.Player.GetAgentID())
        if player_living is None:
            return 0
        
        attack_speed = player_living.weapon_attack_speed
        attack_speed_modifier = player_living.attack_speed_modifier if player_living.attack_speed_modifier != 0 else 1.0
        
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
            self.account_email = ""
            self.combat_handler = CombatClass()
            self.HeroAI_vars: HeroAI_varsClass = HeroAI_varsClass()
            self.HeroAI_windows: HeroAI_Window_varsClass = HeroAI_Window_varsClass()
            self.name_refresh_throttle = ThrottledTimer(1000)
            self.game_throttle_time = throttle_time
            self.game_throttle_timer = Timer()
            self.game_throttle_timer.Start()
            self.shared_memory_timer = Timer()
            self.shared_memory_timer.Start()
            self.stay_alert_timer = Timer()
            self.stay_alert_timer.Start()
            self.aftercast_timer = Timer()
            self.data: GameData = GameData()
            self.auto_attack_timer = Timer()
            self.auto_attack_timer.Start()
            self.auto_attack_time =  self.GetWeaponAttackAftercast()
            self.draw_floating_loot_buttons = False
            self.reset()
            self.ui_state_data = UIStateData()
            self.follow_throttle_timer = ThrottledTimer(1000)
            self.follow_throttle_timer.Start()
            self.option_show_floating_targets = True
            
            self._initialized = True 
            
            self.in_looting_routine = False
        
    def reset(self):
        self.data.reset()   
        
    def InAggro(self, enemy_array, aggro_range = Range.Earshot.value):
        return Routines.Checks.Agents.InAggro(aggro_range)
        
        
    def UpdateGameOptions(self):
        #control status vars
        self.data.is_following_enabled = self.HeroAI_vars.all_game_option_struct[GLOBAL_CACHE.Party.GetOwnPartyNumber()].Following
        self.data.is_avoidance_enabled = self.HeroAI_vars.all_game_option_struct[GLOBAL_CACHE.Party.GetOwnPartyNumber()].Avoidance
        self.data.is_looting_enabled = self.HeroAI_vars.all_game_option_struct[GLOBAL_CACHE.Party.GetOwnPartyNumber()].Looting
        self.data.is_targeting_enabled = self.HeroAI_vars.all_game_option_struct[GLOBAL_CACHE.Party.GetOwnPartyNumber()].Targeting
        self.data.is_combat_enabled = self.HeroAI_vars.all_game_option_struct[GLOBAL_CACHE.Party.GetOwnPartyNumber()].Combat
        for i in range(NUMBER_OF_SKILLS):
            self.data.is_skill_enabled[i] = self.HeroAI_vars.all_game_option_struct[GLOBAL_CACHE.Party.GetOwnPartyNumber()].Skills[i].Active
  
        
    def UdpateCombat(self):
        self.combat_handler.Update(self.data)
        self.combat_handler.PrioritizeSkills()
        
    def Update(self):
        try:
            if self.game_throttle_timer.HasElapsed(self.game_throttle_time):
                self.game_throttle_timer.Reset()
                self.account_email = GLOBAL_CACHE.Player.GetAccountEmail()
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
                       
            
                     