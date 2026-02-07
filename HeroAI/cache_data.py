from dataclasses import dataclass
from HeroAI.party_cache import PartyCache
from Py4GWCoreLib.GlobalCache.SharedMemory import SHMEM_NUMBER_OF_SKILLS, AccountData, HeroAIOptionStruct

from .constants import SHARED_MEMORY_FILE_NAME, STAY_ALERT_TIME, MAX_NUM_PLAYERS, NUMBER_OF_SKILLS
from .globals import HeroAI_varsClass, HeroAI_Window_varsClass
from .combat import CombatClass
from Py4GWCoreLib import GLOBAL_CACHE
from Py4GWCoreLib import Timer, ThrottledTimer
from Py4GWCoreLib import Range, Agent, ConsoleLog, Player
from Py4GWCoreLib import AgentArray, Weapon, Routines
from Py4GWCoreLib.IniManager import IniManager

INI_DIR = "HeroAI"
MAIN_WINDOW_INI = "main_window.ini"
CONSUMABLES_WINDOW_INI = "consumables_window.ini"

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
              
        
    def update(self):
        from Py4GWCoreLib.Map import Map
        if not Map.IsMapReady():
                return False
            
        if Map.IsInCinematic():
            return False
        
        #Player data
        attributes = Agent.GetAttributes(Player.GetAgentID())
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
        self.show_classic_controls = True

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
        weapon_type,_ = Agent.GetWeaponType(Player.GetAgentID())
        player_living = Agent.GetLivingAgentByID(Player.GetAgentID())
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
            self.ini_key : str = ""
            self.consumables_ini_key : str = ""
            
            self.party_position : int = -1
            self.party : PartyCache = PartyCache()
            self.account_data : AccountData = AccountData()
            self.account_options : HeroAIOptionStruct = HeroAIOptionStruct()
            
            self.combat_handler = CombatClass()
            # self.HeroAI_vars: HeroAI_varsClass = HeroAI_varsClass()
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
            self.global_options = HeroAIOptionStruct()
            
            for i in range(SHMEM_NUMBER_OF_SKILLS):
                self.global_options.Skills[i] = True
                
            self.global_options.Following = True
            self.global_options.Avoidance = True
            self.global_options.Looting = True
            self.global_options.Targeting = True
            self.global_options.Combat = True
            
            self._initialized = True             
            self.in_looting_routine = False
            
        
    def reset(self):
        self.data.reset()   
        
    def InAggro(self, enemy_array, aggro_range = Range.Earshot.value):
        return Routines.Checks.Agents.InAggro(aggro_range) 
        
    def UpdateCombat(self):
        self.combat_handler.Update(self)
        self.combat_handler.PrioritizeSkills()
        
    def Update(self):
        try:
            if not self.ini_key:
                self.ini_key = IniManager().ensure_key(f"{INI_DIR}/", MAIN_WINDOW_INI)
                
            if not self.consumables_ini_key:
                self.consumables_ini_key = IniManager().ensure_key(f"{INI_DIR}/", CONSUMABLES_WINDOW_INI)
                
            if not self.ini_key or not self.consumables_ini_key:
                return
            

            if self.game_throttle_timer.HasElapsed(self.game_throttle_time):
                self.game_throttle_timer.Reset()
                self.account_email = Player.GetAccountEmail()
                self.data.reset()
                self.data.update()
                
                self.party.reset()
                self.party.update()
                
                self.account_data = GLOBAL_CACHE.ShMem.GetAccountDataFromEmail(self.account_email) or self.account_data
                self.account_options = GLOBAL_CACHE.ShMem.GetHeroAIOptions(self.account_email) or self.account_options
                
                if self.stay_alert_timer.HasElapsed(STAY_ALERT_TIME):
                    self.data.in_aggro = self.InAggro(AgentArray.GetEnemyArray(), Range.Earshot.value)
                else:
                    self.data.in_aggro = self.InAggro(AgentArray.GetEnemyArray(), Range.Spellcast.value)
                    
                if self.data.in_aggro:
                    self.stay_alert_timer.Reset()
                    
                if not self.stay_alert_timer.HasElapsed(STAY_ALERT_TIME):
                    self.data.in_aggro = True
                    
                self.auto_attack_time = self.GetWeaponAttackAftercast()
                
        except Exception as e:
            ConsoleLog(f"Update Cahe Data Error:", e)
                       
            
                     