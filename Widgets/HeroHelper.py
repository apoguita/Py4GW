from Py4GWCoreLib import *

from collections import namedtuple
import os
import time
import random

MODULE_NAME = "HeroHelper"

script_directory = os.path.dirname(os.path.abspath(__file__))
root_directory = os.path.normpath(os.path.join(script_directory, ".."))
INI_FILE_LOCATION = os.path.join(root_directory, "Widgets/Config/HeroHelper.ini")

# Load configuration settings from the INI file.
ini_handler = IniHandler(INI_FILE_LOCATION)

# Action queue for managing delayed executions.
action_queue = ActionQueue()

class Config:
    # Initialize the configuration and load settings.
    def __init__(self):
        self.tracked_keys = [
            "smart_follow_toggled",
            "attack_toggled",
            "follow_delay",
            "smart_bip_enabled",
            "smart_sos_enabled",
            "smart_st_enabled",
            "smart_honor_enabled",
            "smart_splinter_enabled",
            "smart_vigorous_enabled",
            "hero_behaviour",
            "last_known_hero_behaviour",
            "conditions",
            "hexes",
            "skills_to_rupt",
            "smart_con_cleanse_toggled",
            "smart_hex_cleanse_toggled",
            "smart_interrupt_toggled",
            "user_hex_input",
            "user_skill_input"
        ]

        # Load values from the INI file or use defaults.
        self.smart_follow_toggled = ini_handler.read_bool(MODULE_NAME, "smart_follow_toggled", False)
        self.attack_toggled = ini_handler.read_bool(MODULE_NAME, "attack_toggled", False)
        self.follow_delay = ini_handler.read_int(MODULE_NAME, "follow_delay", 800)
        self.smart_bip_enabled = ini_handler.read_bool(MODULE_NAME, "smart_bip_enabled", False)
        self.smart_sos_enabled = ini_handler.read_bool(MODULE_NAME, "smart_sos_enabled", False)
        self.smart_st_enabled = ini_handler.read_bool(MODULE_NAME, "smart_st_enabled", False)
        self.smart_honor_enabled = ini_handler.read_bool(MODULE_NAME, "smart_honor_enabled", False)
        self.smart_splinter_enabled = ini_handler.read_bool(MODULE_NAME, "smart_splinter_enabled", False)
        self.smart_vigorous_enabled = ini_handler.read_bool(MODULE_NAME, "smart_vigorous_enabled", False)
        self.hero_behaviour = ini_handler.read_int(MODULE_NAME, "hero_behaviour", 0)
        self.last_known_hero_behaviour = ini_handler.read_int(MODULE_NAME, "last_known_hero_behaviour", self.hero_behaviour)
        self.smart_con_cleanse_toggled = ini_handler.read_bool(MODULE_NAME, "smart_con_cleanse_toggled", False)
        self.smart_hex_cleanse_toggled = ini_handler.read_bool(MODULE_NAME, "smart_hex_cleanse_toggled", False)
        self.smart_interrupt_toggled = ini_handler.read_bool(MODULE_NAME, "smart_interrupt_toggled", False)
        
        
        self.user_hex_input = ini_handler.read_key(MODULE_NAME, "user_hex_input", "")
        self.user_skill_input = ini_handler.read_key(MODULE_NAME, "user_skill_input", "")

        self.hexes_melee = []
        self.hexes_caster = []
        self.hexes_all = []
        self.hexes_paragon = []
        self.hexes_user = []

        self.conditions = self.load_conditions()
        self.hexes = self.load_hexes()
        self.skills_to_rupt = self.load_skills_to_rupt()

        self._cache = {key: getattr(self, key) for key in self.tracked_keys}

    # Function: load_conditions
    # Loads condition cleanse settings from the INI file and structures them as dictionaries.
    def load_conditions(self):
        conditions = {}
        for condition in [
            "Bleeding", "Blind", "Burning", "Cracked_Armor", "Crippled",
            "Dazed", "Deep_Wound", "Disease", "Poison", "Weakness"
        ]:
            key = f"smart_cleanse_cond_{condition.lower()}"
            value = ini_handler.read_key(MODULE_NAME, key, "false,false,false")  # Default all false
            values = value.split(",")

            if len(values) != 3:
                values = ["false", "false", "false"]

            conditions[condition] = {
                "id": Skill.GetID(condition),
                "melee": values[0].strip().lower() == "true",
                "caster": values[1].strip().lower() == "true",
                "both": values[2].strip().lower() == "true"
            }

        return conditions

    # Function: save_conditions
    # Saves the current condition cleanse settings back into the INI file.
    def save_conditions(self):
        for condition, data in self.conditions.items():
            key = f"smart_cleanse_cond_{condition.lower()}"
            value = f"{data['melee']},{data['caster']},{data['both']}"
            ini_handler.write_key(MODULE_NAME, key, value)

    # Function: load_hexes
    # Reads hexes from the INI file, ensuring proper formatting and removing empty entries.
    def load_hexes(self):
        self.hexes_melee = ini_handler.read_key(MODULE_NAME, "hexes_melee", "").replace(" ", "_").split(",") if ini_handler.read_key(MODULE_NAME, "hexes_melee", "") else []
        self.hexes_caster = ini_handler.read_key(MODULE_NAME, "hexes_caster", "").replace(" ", "_").split(",") if ini_handler.read_key(MODULE_NAME, "hexes_caster", "") else []
        self.hexes_all = ini_handler.read_key(MODULE_NAME, "hexes_all", "").replace(" ", "_").split(",") if ini_handler.read_key(MODULE_NAME, "hexes_all", "") else []
        self.hexes_paragon = ini_handler.read_key(MODULE_NAME, "hexes_paragon", "").replace(" ", "_").split(",") if ini_handler.read_key(MODULE_NAME, "hexes_paragon", "") else []
        self.hexes_user = ini_handler.read_key(MODULE_NAME, "hexes_user", "").replace(" ", "_").split(",") if ini_handler.read_key(MODULE_NAME, "hexes_user", "") else []

        self.hexes_melee = [h for h in self.hexes_melee if h]
        self.hexes_caster = [h for h in self.hexes_caster if h]
        self.hexes_all = [h for h in self.hexes_all if h]
        self.hexes_paragon = [h for h in self.hexes_paragon if h]
        self.hexes_user = [h for h in self.hexes_user if h]

        return {}
    
    # Function: save_hexes
    # Writes the current hex lists to the INI file, preserving formatting.
    def save_hexes(self):
        ini_handler.write_key(MODULE_NAME, "hexes_melee", ",".join(self.hexes_melee))
        ini_handler.write_key(MODULE_NAME, "hexes_caster", ",".join(self.hexes_caster))
        ini_handler.write_key(MODULE_NAME, "hexes_all", ",".join(self.hexes_all))
        ini_handler.write_key(MODULE_NAME, "hexes_paragon", ",".join(self.hexes_paragon))
        ini_handler.write_key(MODULE_NAME, "hexes_user", ",".join(self.hexes_user))  # Save user-added hexes
    
    # Function: load_skills_to_rupt
    # Loads a predefined list of skills that should be rupted (interrupted) if cast by an enemy.
    def load_skills_to_rupt(self):
        saved_skills = ini_handler.read_key(MODULE_NAME, "skills_to_rupt", "")
        return saved_skills.split(",") if saved_skills else [
            "Panic",
            "Energy_Surge",
            "Chilblains",
            "Meteor",
            "Meteor_Shower",
            "Searing_Flames",
            "Resurrection_Signet",
        ]
        
    # Function: save_skills_to_rupt
    # Saves the current list of skills that should be rupted to the INI file.
    def save_skills_to_rupt(self):
            ini_handler.write_key(MODULE_NAME, "skills_to_rupt", ",".join(self.skills_to_rupt))

    # Function: save
    # Saves all tracked configuration variables to the INI file if changes are detected.
    def save(self):
            for key in self.tracked_keys:
                value = getattr(self, key)

                if isinstance(value, bool):
                    ini_handler.write_key(MODULE_NAME, key, "true" if value else "false")
                elif key == "conditions":
                    self.save_conditions()  # Save conditions separately
                elif key == "hexes":
                    self.save_hexes()  # Save hexes separately
                elif key == "skills_to_rupt":
                    self.save_skills_to_rupt()  # Save hexes separately    
                else:
                    ini_handler.write_key(MODULE_NAME, key, str(value))

                self._cache[key] = value  # Update cache to prevent unnecessary writes


widget_config = Config()
window_module = ImGui.WindowModule(MODULE_NAME, window_name="Hero Helper", window_size=(200, 100), window_flags=PyImGui.WindowFlags.AlwaysAutoResize)
config_module = ImGui.WindowModule(f"Config {MODULE_NAME}", window_name="Hero Helper Configuration", window_size=(300, 175), window_flags=PyImGui.WindowFlags.AlwaysAutoResize)

config_module.window_pos = (
    ini_handler.read_int(MODULE_NAME + " Config", "config_x", 100),
    ini_handler.read_int(MODULE_NAME + " Config", "config_y", 100)
)


class Helper:
    @staticmethod
    # Function: get_safe_to_load
    # Checks whether the game map is loaded and the party data is available.
    def is_game_ready():
        return Map.IsMapReady() and Party.IsPartyLoaded()
        
    @staticmethod
    # Function: get_energy_data
    # Retrieves the energy status (percentage, max, current, and regen) of an agent.
    def get_energy_data(agent_id=None):
        energy_data = namedtuple("energy_data", ["percentage", "max", "current", "regen"])

        if agent_id is None:
            agent_id = Player.GetAgentID()

        if agent_id is None:
            return energy_data(0, 0, 0, 0)

        if Agent.IsDead(agent_id):
            return energy_data(0, 0, 0, 0)

        energy_perc = Agent.GetEnergy(agent_id)
        energy_max = Agent.GetMaxEnergy(agent_id)
        energy_cur = int(energy_perc * energy_max)
        energy_regen = Agent.GetEnergyRegen(agent_id)

        return energy_data(energy_perc, energy_max, energy_cur, energy_regen)
    
    @staticmethod
    # Function: get_hp_data
    # Retrieves the HP status (percentage, max, current, and regen) of an agent.
    def get_hp_data(agent_id=None):
        hp_data = namedtuple("hp_data", ["percentage", "max", "current", "regen"])

        if agent_id is None:
            agent_id = Player.GetAgentID()
            
        if agent_id is None:
            return hp_data(0, 0, 0, 0)

        if Agent.IsDead(agent_id):
            return hp_data(0, 0, 0, 0)

        hp_perc = Agent.GetHealth(agent_id)
        hp_max = Agent.GetMaxHealth(agent_id)
        hp_cur = int(hp_perc * hp_max)
        hp_regen = Agent.GetHealthRegen(agent_id)

        return hp_data(hp_perc, hp_max, hp_cur, hp_regen)
    
    @staticmethod
    # Function: is_agent_alive
    # Checks whether an agent is alive based on their ID.
    def is_agent_alive(agent_id):
        if agent_id is None:
            return False
        
        return Agent.IsLiving(agent_id)
    
    HERO_BEHAVIOUR_FIGHT = 0
    HERO_BEHAVIOUR_GUARD = 1
    HERO_BEHAVIOUR_AVOID_COMBAT = 2
    @staticmethod
    # Function: set_heroes_behaviour
    # Sets the combat behavior of all heroes in the party (Fight, Guard, or Avoid Combat).
    def set_heroes_behaviour(behaviour):
        heroes = Party.GetHeroes()
        if not heroes:
            return

        for hero in heroes:
            agent_id = hero.agent_id
            if agent_id:
                Party.Heroes.SetHeroBehavior(agent_id, behaviour)
                
    @staticmethod
    # Function: flag_heroes
    # Flags all heroes to a specified position, defaulting to the player's position.
    def flag_heroes(*position):
        if not position:  # If no position is provided, use the player's position
            position = Player.GetXY()
        
        if position:
            Party.Heroes.FlagAllHeroes(*position)  # Unpacking the tuple into x, y
    
    @staticmethod
    # Function: unflag_heroes
    # Removes hero flags, allowing them to move freely.
    def unflag_heroes():
        Party.Heroes.UnflagAllHeroes()

    @staticmethod
    # Function: can_execute_with_delay
    # Ensures that a function can only be executed after a certain delay, adding optional random jitter.
    def can_execute_with_delay(identifier, delay_ms, jitter_ms=0):
        if not hasattr(Helper, "execution_timers"):
            Helper.execution_timers = {}  # Initialize storage for last execution times

        current_time = time.time() * 1000  # Convert to milliseconds
        last_execution_time = Helper.execution_timers.get(identifier, 0)
        elapsed_time = current_time - last_execution_time

        jitter = random.randint(-jitter_ms, jitter_ms) if jitter_ms > 0 else 0
        adjusted_delay = delay_ms + jitter  # Apply jitter to the delay

        if elapsed_time >= adjusted_delay:
            Helper.execution_timers[identifier] = current_time  # Update last execution time
            return True  # Execution allowed

        return False  # Execution denied due to cooldown

    @staticmethod
    # Function: create_and_update_checkbox
    # Handles the logic for function execution.
    def create_and_update_checkbox(label, config_attr, tooltip_text=None):
        previous_state = getattr(widget_config, config_attr)

        new_state = PyImGui.checkbox(label, previous_state)
        setattr(widget_config, config_attr, new_state)

        if new_state != previous_state:
            Helper.log_event(message=f"{label} Enabled" if new_state else f"{label} Disabled")

        if tooltip_text and PyImGui.is_item_hovered():
            PyImGui.set_tooltip(tooltip_text)

    last_cast_logs = {}
    console_logs = []

    @staticmethod
    # Function: log_event
    # Logs hero actions, skill casts, and general events to the console with spam prevention.
    def log_event(hero_id=None, skill_name=None, target_name=None, skill_id=None, target_id=None, message=None, cooldown=10):

        if skill_id and target_id:
            last_cast_key = (hero_id, skill_id, target_id)
            current_time = time.time()

            if last_cast_key in Helper.last_cast_logs and (current_time - Helper.last_cast_logs[last_cast_key]) < cooldown:
                return

            Helper.last_cast_logs[last_cast_key] = current_time
            log_message = f"Casting skill [{skill_name}] on target [{target_name}]"

        else:
            log_message = message

        if log_message:
            Helper.console_logs.append(log_message)
            Helper.console_logs = Helper.console_logs[-5:]

            Py4GW.Console.Log(MODULE_NAME, log_message, Py4GW.Console.MessageType.Notice)

    hero_skill_cache = []

    @staticmethod
    # Function: cache_hero_skills
    # Caches all hero skillbars to avoid repeated API calls, updating on map change.
    def cache_hero_skills():

        if not Helper.should_update_cache():
            return Helper.hero_skill_cache

        
        Helper.hero_skill_cache = []
        Helper.last_map_id = Map.GetMapID()

        heroes = Party.GetHeroes() or []
        for hero_index, hero_id in enumerate(heroes, start=1):
            Helper._cache_skills_for_hero(hero_index)

        return Helper.hero_skill_cache

    @staticmethod
    # Function: reset_hero_skill_cache
    # Clears the hero skill cache to force a refresh.
    def reset_hero_skill_cache():
        Helper.hero_skill_cache.clear()

    last_map_id = None
    
    @staticmethod
    # Function: should_update_cache
    # Determines if a cache refresh is needed based on map changes.
    def should_update_cache():
        
        current_map_id = Map.GetMapID()
        
        if current_map_id != Helper.last_map_id:
            return True
        
        return False

    @staticmethod
    # Function: _cache_skills_for_hero
    # Handles the logic for function execution.
    def _cache_skills_for_hero(hero_index):
        hero_skills = SkillBar.GetHeroSkillbar(hero_index)
        if not hero_skills:
            return

        for skill_slot, skill in enumerate(hero_skills, start=1):
            skill_id = skill.id.id
            skill_name = Skill.GetName(skill_id)
            Helper.hero_skill_cache.append({
                "hero_index": hero_index,
                "skill_slot": skill_slot,
                "skill_id": skill_id,
                "skill_name": skill_name
            })

    effect_cache = {}

    @staticmethod
    # Function: get_active_effects
    # Retrieves the list of active effects on an agent, including remaining durations.
    def get_active_effects(agent_id):
        return {
            effect.skill_id: effect.time_remaining if effect.time_remaining else 5
            for effect in Effects.GetEffects(agent_id) or []
        }

    @staticmethod
    # Function: should_check_effect
    # Handles the logic for function execution.
    def should_check_effect(agent_id, effect_id):
        current_time = time.time()
        cache_key = (agent_id, effect_id)

        if cache_key in Helper.effect_cache:
            if current_time < Helper.effect_cache[cache_key]["expires"]:
                return False  # Effect is still valid in cache

        return True  # Effect should be checked

    @staticmethod
    # Function: update_effect_cache
    # Handles the logic for function execution.
    def update_effect_cache(agent_id, effect_id, effect_time_left):
        current_time = time.time()
        Helper.effect_cache[(agent_id, effect_id)] = {
            "result": True,
            "expires": current_time + effect_time_left
        }

    @staticmethod
    # Function: check_for_effects
    # Checks if an agent has a specific effect, using caching for efficiency.
    def check_for_effects(agent_id, effect_ids):
        if not Helper.is_agent_alive(agent_id):
            return False

        current_effects = Helper.get_active_effects(agent_id)

        for effect_id in effect_ids:
            if effect_id not in current_effects:
                continue  # Effect not found, move to the next one

            effect_time_left = current_effects[effect_id]

            if not Helper.should_check_effect(agent_id, effect_id):
                return True  # Cached effect is still valid, no need to check further

            Helper.update_effect_cache(agent_id, effect_id, effect_time_left)
            return True  # Effect is active

        return False  # No requested effects were found

    @staticmethod
    # Function: has_effect_on_player_or_heroes
    # Returns whether a specific effect is present on the player or any hero.
    def has_effect_on_player_or_heroes(effect_id):
        return any(
            Helper.check_for_effects(agent, [effect_id])
            for agent in [Player.GetAgentID()] + [hero.agent_id for hero in Party.GetHeroes()]
        )

    @staticmethod
    # Function: get_heroes_with_skill
    # Finds heroes who have a given skill and are ready to cast it.
    def get_heroes_with_skill(skill_id):
        hero_skills = Helper.cache_hero_skills()
        ready_heroes = [
            hero for hero in hero_skills
            if hero["skill_id"] == skill_id and Helper.can_hero_cast_skill(hero["hero_index"], skill_id)
        ]
        
        return ready_heroes  # Only return heroes with skill ready

    @staticmethod
    # Function: can_hero_cast_skill
    # Checks whether a hero is able to cast a specific skill, considering cooldowns.
    def can_hero_cast_skill(hero_index, skill_id):
        hero_skills = SkillBar.GetHeroSkillbar(hero_index)

        if hero_skills:
            for skill in hero_skills:
                if skill.id.id == skill_id:
                    return skill.recharge == 0
        return False

    @staticmethod
    # Function: cast_hero_skill
    # Commands a hero to cast a specific skill on a target.
    def cast_hero_skill(hero_index, skill_slot, target_id):
        SkillBar.HeroUseSkill(target_id, skill_slot, hero_index)
    
    @staticmethod
    # Function: get_nearby_range
    # Handles the logic for function execution.
    def get_nearby_range():
        return enums.Range.Nearby.value
    
    @staticmethod
    # Function: get_spell_cast_range
    # Handles the logic for function execution.
    def get_spell_cast_range():
        return enums.Range.Spellcast.value

    @staticmethod
    # Function: get_spirit_range
    # Handles the logic for function execution.
    def get_spirit_range():
        return enums.Range.Spirit.value
    
    @staticmethod
    # Function: is_specific_spirit_in_range
    # Handles the logic for function execution.
    def is_specific_spirit_in_range(spirit_id, custom_range):
        spirits = AgentArray.GetSpiritPetArray()
        if not spirits or spirit_id not in spirits:
            return False

        player_x, player_y = Player.GetXY()
        spirit_x, spirit_y = Agent.GetXY(spirit_id)

        check_range = custom_range

        return Utils.Distance((player_x, player_y), (spirit_x, spirit_y)) <= check_range
    
    @staticmethod
    # Function: count_spirits_in_range
    # Handles the logic for function execution.
    def count_spirits_in_range(spirit_ids, custom_range):
        return sum(1 for spirit_id in spirit_ids if Helper.is_specific_spirit_in_range(spirit_id, custom_range))

    @staticmethod
    # Function: count_enemies_in_range
    # Handles the logic for function execution.
    def count_enemies_in_range(custom_range, position=None):
        enemies = AgentArray.GetEnemyArray()
        if not enemies:
            return 0

        if position is None:
            position = Player.GetXY()

        count = sum(
            1 for enemy_id in enemies
            if not Agent.IsDead(enemy_id) and Utils.Distance(position, Agent.GetXY(enemy_id)) <= custom_range
        )

        return count
      
    @staticmethod
    # Function: is_fighting
    # Handles the logic for function execution.
    def is_fighting(agent_id=None):
        if agent_id is None:
            agent_id = Player.GetAgentID()  # Default to player

        return Agent.IsAttacking(agent_id) or Agent.IsCasting(agent_id)
    
    @staticmethod
    # Function: is_auto_attacking
    # Handles the logic for function execution.
    def is_auto_attacking(agent_id=None):
        if agent_id is None:
            agent_id = Player.GetAgentID()  # Default to player

        return Agent.IsAttacking(agent_id)
    
    @staticmethod
    # Function: is_hero_attacking
    # Handles the logic for function execution.
    def is_hero_attacking():
        heroes = Party.GetHeroes()
        if not heroes:
            return False  # No heroes in party
        
        return any(Agent.IsAttacking(hero.agent_id) for hero in heroes if hero.agent_id)

    @staticmethod
    # Function: can_cast
    # Handles the logic for function execution.
    def can_cast(agent_id=None):
        if agent_id is None:
            agent_id = Player.GetAgentID()  # Default to player

        if (Agent.IsDead(agent_id) or
            Agent.IsKnockedDown(agent_id) or
            Agent.IsCasting(agent_id) or
            Agent.IsMoving(agent_id)):
            return False

        return True

    @staticmethod
    # Function: can_attack
    # Handles the logic for function execution.
    def can_attack(agent_id=None):
        if agent_id is None:
            agent_id = Player.GetAgentID()  # Default to player

        if (Agent.IsDead(agent_id) or
            Agent.IsKnockedDown(agent_id) or
            Agent.IsCasting(agent_id) or
            Agent.IsMoving(agent_id) or
            Agent.IsAttacking(agent_id)):
            return False

        return True
    
    @staticmethod
    # Function: can_fight
    # Handles the logic for function execution.
    def can_fight(agent_id=None):
        if agent_id is None:
            agent_id = Player.GetAgentID()  # Default to player

        return Helper.can_attack(agent_id) or Helper.can_cast(agent_id)
    
    @staticmethod
    # Function: get_aftercast
    # Handles the logic for function execution.
    def get_aftercast(skill_id):
        activation = Skill.Data.GetActivation(skill_id)
        aftercast = Skill.Data.GetAftercast(skill_id)    
        return max(activation * 1000 + aftercast * 1000 + Py4GW.PingHandler().GetCurrentPing() + 50, 500)
    
    @staticmethod
    # Function: smartcast_hero_skill
    # Intelligently selects the best hero to cast a skill based on predefined conditions.
    def smartcast_hero_skill(skill_id, min_enemies=0, enemy_range_check=None, 
                            effect_check=False, cast_target_id=None, hero_target=False, 
                            distance_check_range=None, allow_out_of_combat=False,
                            min_health_perc=None, min_energy_perc=None):

        heroes_ready = Helper.get_heroes_with_skill(skill_id)

        if not heroes_ready:
            return None  

        player_id = Player.GetAgentID()

        if not player_id or not Helper.is_agent_alive(player_id):
            return None

        if cast_target_id is None:
            cast_target_id = player_id  # Default target is player

        if min_enemies > 0:
            if enemy_range_check is None:
                enemy_range_check = Helper.get_spell_cast_range()  
            
            num_enemies_in_range = Helper.count_enemies_in_range(enemy_range_check, Player.GetXY())

            if not allow_out_of_combat and (num_enemies_in_range < min_enemies and not Helper.is_fighting()):
                return None  

        if effect_check and Helper.check_for_effects(cast_target_id, [skill_id]):
            return None  

        if distance_check_range is None:
            distance_check_range = Helper.get_spell_cast_range() + 200  

        for hero in heroes_ready:
            hero_index = hero["hero_index"]
            hero_id = Party.Heroes.GetHeroAgentIDByPartyPosition(hero_index)
            hero_pos = Agent.GetXY(hero_id)

            if not hero_pos:
                continue  

            distance = Utils.Distance(Player.GetXY(), hero_pos)

            if distance > distance_check_range:
                continue  

            if hero_target:
                cast_target_id = hero_id

            hero_energy = Helper.get_energy_data(hero_id)
            hero_health = Helper.get_hp_data(hero_id)

            if min_health_perc and hero_health.percentage < min_health_perc:
                continue  

            if min_energy_perc and hero_energy.percentage < min_energy_perc:
                continue  

            if hero_energy.current <= Skill.Data.GetEnergyCost(skill_id):
                continue  

            if Helper.can_hero_cast_skill(hero_index, skill_id):
                skill_name = Skill.GetName(skill_id).replace("_", " ")
                target_name = Helper.agent_name_cache.get(cast_target_id, str(cast_target_id))

                Helper.log_event(hero_id, skill_name, target_name, skill_id, cast_target_id)

                return hero_index, hero["skill_slot"], skill_id, cast_target_id

        return None

    agent_name_cache = {}
    cached_agent_ids = set()

    @staticmethod
    # Function: cache_agent_names
    # Caches agent names to avoid redundant requests, updating on map change.
    def cache_agent_names():
        if Helper.should_update_cache():
            Helper.reset_agent_name_cache()
            Helper.cached_agent_ids.clear()

        agent_ids = set(AgentArray.GetNPCMinipetArray()) | set(AgentArray.GetAllyArray()) | set(AgentArray.GetNeutralArray())

        if not agent_ids:
            return

        new_agent_ids = agent_ids - Helper.cached_agent_ids

        for agent_id in new_agent_ids:
            Agent.RequestName(agent_id)

        for agent_id in agent_ids:
            if agent_id not in Helper.agent_name_cache and Agent.IsNameReady(agent_id):
                Helper.agent_name_cache[agent_id] = Agent.GetName(agent_id)

        Helper.cached_agent_ids.update(new_agent_ids)

    @staticmethod
    # Function: get_agent_name_by_id
    # Retrieves an agent's name, requesting it if not already cached.
    def get_agent_name_by_id(agent_id):
        if agent_id in Helper.agent_name_cache:
            return Helper.agent_name_cache[agent_id]

        Agent.RequestName(agent_id)
        if Agent.IsNameReady(agent_id):
            Helper.agent_name_cache[agent_id] = Agent.GetName(agent_id)
            return Helper.agent_name_cache[agent_id]

        return None  # Name not available yet
    
    @staticmethod
    # Function: reset_agent_name_cache
    # Handles the logic for function execution.
    def reset_agent_name_cache():
        Helper.agent_name_cache.clear()  # Clear the cache

    @staticmethod
    # Function: is_melee_class
    # Determines if the player’s primary profession is a melee class.
    def is_melee_class():
        player_id = Player.GetAgentID()
        if not player_id:
            return False

        player_profession, _ = Agent.GetProfessionNames(player_id)

        melee_classes = {"Assassin", "Dervish", "Warrior", "Paragon", "Ranger"}

        return player_profession in melee_classes
    
    @staticmethod
    # Function: holds_melee_weapon
    # Checks if the player is holding a melee weapon in the main hand.
    def holds_melee_weapon():

        equipped_bag = ItemArray.CreateBagList(Bag.Equipped_Items)
        equipped_items = ItemArray.GetItemArray(equipped_bag)

        if not equipped_items:
            return False

        main_hand_weapon = equipped_items[0] if len(equipped_items) > 0 else None
        if not main_hand_weapon:
            return False

        item_type, _ = Item.GetItemType(main_hand_weapon)

        melee_weapon_types = {
            2, #axe
            15, #hammer
            27, #sword
            32, #daggers
            35, #scythe
            36 #spear
        }

        return item_type in melee_weapon_types
    
    @staticmethod
    # Function: format_spell_title_case
    # Handles the logic for function execution.
    def format_spell_title_case(spell_name):
        small_words = {"of"}
        words = spell_name.split()  # Split into words
        formatted_words = [
            word.capitalize() if word.lower() not in small_words else word.lower()
            for word in words
        ]
        formatted_spell_name = "_".join(formatted_words)  # Rejoin with underscores
        return formatted_spell_name


hero_aftercast_timers = {}

# Function: execute_hero_skill
# Handles the logic for function execution.
def execute_hero_skill(hero_index, skill_slot, skill_id, target_id):
    global hero_aftercast_timers
    current_time = time.time()

    if None in (hero_index, skill_slot, skill_id, target_id):
        Helper.log_event(message=f"Error: Invalid parameters in execute_hero_skill(). "
                                 f"hero_index={hero_index}, skill_slot={skill_slot}, "
                                 f"skill_id={skill_id}, target_id={target_id}")
        return

    # Check if hero can actually cast the skill
    if not Helper.can_hero_cast_skill(hero_index, skill_id):
        return

    # Ensure hero is not still in cooldown
    if hero_index in hero_aftercast_timers and current_time < hero_aftercast_timers[hero_index]:
        return 

    Helper.cast_hero_skill(hero_index, skill_slot, target_id)

    aftercast_delay = Helper.get_aftercast(skill_id) / 1000  # Convert to seconds
    hero_aftercast_timers[hero_index] = current_time + aftercast_delay


# Function: smart_interrupt
# Automatically attempts to interrupt enemy skill casts using heroes.
def smart_interrupt():
    if Party.GetHeroCount() == 0:  
        return  # Exit if there are no heroes in the party

    if not Helper.can_execute_with_delay("smart_interrupt", 250):  
        return  # Prevents executing too often (4 times per second)
    
    skills_to_rupt_ids = {Skill.GetID(skill_name) for skill_name in widget_config.skills_to_rupt}

    SKILL_CLASS_PAIRS = [
        (Skill.GetID("Cry_of_Frustration"), "Mesmer"),
        (Skill.GetID("Power_Drain"), "Mesmer")
    ]

    enemies = AgentArray.GetEnemyArray()
    if not enemies:
        return
    
    enemy_casting = None
    player_position = Player.GetXY()  # Get player's position
    spellcast_range = Helper.get_spell_cast_range()  # Define max range for interrupts

    casting_enemies = []
    for enemy_id in enemies:
        if not Helper.is_agent_alive(enemy_id):
            continue
        
        enemy_position = Agent.GetXY(enemy_id)
        distance_to_enemy = Utils.Distance(player_position, enemy_position)

        if distance_to_enemy > spellcast_range:
            continue
        
        if not Agent.IsCasting(enemy_id):
            continue

        casting_skill = Agent.GetCastingSkill(enemy_id)

        if casting_skill in skills_to_rupt_ids:
            casting_enemies.append(enemy_id)
        
    if not casting_enemies:
        return
    
    casting_enemies.sort(key=lambda eid: Utils.Distance(player_position, Agent.GetXY(eid)))
    
    for enemy_casting in casting_enemies:
        for skill_id, profession in SKILL_CLASS_PAIRS:
            hero_cast_result = Helper.smartcast_hero_skill(
                skill_id=skill_id,
                enemy_range_check=Helper.get_spell_cast_range(),
                cast_target_id=enemy_casting,
                distance_check_range=Helper.get_spell_cast_range() + 200
            )

            if hero_cast_result:
                execute_hero_skill(*hero_cast_result)
                break  # Stop after successfully casting an interrupt


# Function: smart_hex_removal
# Identifies and removes harmful hexes from the player using hero skills.
def smart_hex_removal():
    if not Helper.can_execute_with_delay("smart_hex_removal", 1000):
        return

    if Party.GetHeroCount() == 0:  
        return 
    
    player_id = Player.GetAgentID()

    if not player_id or not Helper.is_agent_alive(player_id):
        return  

    player_professions = Agent.GetProfessionShortNames(player_id)
    is_paragon = "P" in player_professions  # Check if primary or secondary is Paragon

    hexes_melee_set = {Skill.GetID(hex_name) for hex_name in widget_config.hexes_melee}
    hexes_caster_set = {Skill.GetID(hex_name) for hex_name in widget_config.hexes_caster}
    hexes_user_set = {Skill.GetID(hex_name) for hex_name in widget_config.hexes_user}
    hexes_all_set = {Skill.GetID(hex_name) for hex_name in widget_config.hexes_all}
    hexes_paragon_set = {Skill.GetID(hex_name) for hex_name in widget_config.hexes_paragon} if is_paragon else set()

    hex_removal_skills = {
        Skill.GetID("Shatter_Hex"),
        Skill.GetID("Remove_Hex"),
        Skill.GetID("Smite_Hex"),
    }

    has_hex = False
    if Helper.holds_melee_weapon() and Helper.check_for_effects(player_id, hexes_melee_set):
        has_hex = True
    elif not Helper.holds_melee_weapon() and Helper.check_for_effects(player_id, hexes_caster_set):
        has_hex = True
    elif Helper.check_for_effects(player_id, hexes_all_set):
        has_hex = True
    elif hexes_paragon_set and Helper.check_for_effects(player_id, hexes_paragon_set):
        has_hex = True
    elif Helper.check_for_effects(player_id, hexes_user_set):
        has_hex = True

    if not has_hex:
        return  

    for skill_id in hex_removal_skills:
        result = Helper.smartcast_hero_skill(skill_id=skill_id)

        if result:
            execute_hero_skill(*result)  # Executes the skill using the best hero found
            break  # Stop after first successful hex removal


# Function: smart_cond_removal
# Detects and removes conditions from the player using hero skills.
def smart_cond_removal():
    if Party.GetHeroCount() == 0:  
        return  # Exit if there are no heroes in the party

    if not Helper.can_execute_with_delay("smart_cond_removal", 250):  
        return  # Prevents executing too often (4 times per second)

    conditions_melee = {data["id"] for name, data in widget_config.conditions.items() if data["melee"]}
    conditions_caster = {data["id"] for name, data in widget_config.conditions.items() if data["caster"]}
    conditions_both = {data["id"] for name, data in widget_config.conditions.items() if data["both"]}

    condition_removal_skills = {
        Skill.GetID("Mend_Body_and_Soul"),
        Skill.GetID("Dismiss_Condition"),
        Skill.GetID("Mend_Condition"),
        Skill.GetID("Smite_Condition"),
        Skill.GetID("Purge_Conditions"),
    }

    player_id = Player.GetAgentID()
    if not player_id or not Helper.is_agent_alive(player_id):
        return  # No need to return False, just exit

    if Helper.holds_melee_weapon() and Helper.check_for_effects(player_id, conditions_melee):
        pass
    elif not Helper.holds_melee_weapon() and Helper.check_for_effects(player_id, conditions_caster):
        pass
    elif Helper.check_for_effects(player_id, conditions_both):
        pass
    else:
        return  # No conditions found, just exit

    for skill_id in condition_removal_skills:
        result = Helper.smartcast_hero_skill(skill_id=skill_id)

        if result:
            execute_hero_skill(*result)  # Executes the skill using the best hero found
            break


# Function: smart_vigorous
# Maintains Vigorous Spirit on the player when melee combat conditions are met.
def smart_vigorous():
    if Party.GetHeroCount() == 0:
        return
    
    vigorous_id = Skill.GetID("Vigorous_Spirit")

    if not Helper.can_execute_with_delay("smart_vigorous", 1000):
        return

    player_id = Player.GetAgentID()
    if not Helper.is_agent_alive(player_id):
        return

    if not Helper.is_melee_class():
        return

    if not Helper.holds_melee_weapon():
        return

    result = Helper.smartcast_hero_skill(skill_id=vigorous_id, min_enemies=2,
        enemy_range_check=Helper.get_nearby_range(), effect_check=True,
        distance_check_range=Helper.get_spell_cast_range(), allow_out_of_combat=False, 
        min_energy_perc=0.25)

    if result:
        execute_hero_skill(*result)


# Function: smart_splinter
# Ensures Splinter Weapon is cast on the player for melee damage boosts.
def smart_splinter():
    if Party.GetHeroCount() == 0:
        return
    splinter_id = Skill.GetID("Splinter_Weapon")

    if not Helper.can_execute_with_delay("smart_splinter", 1000):
        return

    player_id = Player.GetAgentID()
    if not Helper.is_agent_alive(player_id):
        return

    if not Helper.is_melee_class():
        return

    if not Helper.holds_melee_weapon():
        return

    result = Helper.smartcast_hero_skill(skill_id=splinter_id, min_enemies=2,
        enemy_range_check=Helper.get_nearby_range(), effect_check=True,
        distance_check_range=Helper.get_spell_cast_range(), allow_out_of_combat=False, 
        min_energy_perc=0.25)

    if result:
        execute_hero_skill(*result)


# Function: smart_honor
# Ensures Strength of Honor is maintained on the player when appropriate.
def smart_honor():
    if Party.GetHeroCount() == 0:
        return
    honor_id = Skill.GetID("Strength_of_Honor")

    if not Helper.can_execute_with_delay("smart_honor", 1000):
        return

    player_id = Player.GetAgentID()
    if not Helper.is_agent_alive(player_id):
        return

    if not Helper.is_melee_class():
        return

    if not Helper.holds_melee_weapon():
        return

    result = Helper.smartcast_hero_skill(skill_id=honor_id, min_enemies=0,
        enemy_range_check=Helper.get_spell_cast_range(), effect_check=True,
        distance_check_range=Helper.get_spell_cast_range(), allow_out_of_combat=True, 
        min_energy_perc=0.25)

    if result:
        execute_hero_skill(*result)


# Function: smart_st
# Casts Shelter and Union spirits to mitigate incoming damage when fighting.
def smart_st():
    if Party.GetHeroCount() == 0:
        return
    
    if not Helper.can_execute_with_delay("smart_st", 1000):  
        return

    if not Helper.is_fighting():
        return
    shelter_id = Skill.GetID("Shelter")
    result_shelter = Helper.smartcast_hero_skill(skill_id=shelter_id, min_enemies=3, 
                                               enemy_range_check=Helper.get_spell_cast_range(), hero_target=True, effect_check=True, 
                                               distance_check_range=Helper.get_spirit_range() + 200)
    if result_shelter:
        execute_hero_skill(*result_shelter)  

    union_id = Skill.GetID("Union")
    result_union = Helper.smartcast_hero_skill(skill_id=union_id, min_enemies=3, 
                                             enemy_range_check=Helper.get_spell_cast_range(), hero_target=True, effect_check=True, 
                                             distance_check_range=Helper.get_spirit_range() + 200)
    if result_union:
        execute_hero_skill(*result_union)


# Function: smart_sos
# Ensures Signet of Spirits is cast when beneficial for spirit-based damage.
def smart_sos():
    if Party.GetHeroCount() == 0:
        return
    
    SoS_skill_id = Skill.GetID("Signet_of_Spirits")
    SoS_spirit_ids = [4229, 4230, 4231]  
    custom_range = Helper.get_spell_cast_range()  
    spirit_check_range = Helper.get_spell_cast_range() + 200  

    if not Helper.can_execute_with_delay("smart_sos", 1000):  
        return

    player_position = Player.GetXY()
    num_enemies_in_range = Helper.count_enemies_in_range(custom_range, player_position)
    num_sos_spirits = Helper.count_spirits_in_range(SoS_spirit_ids, spirit_check_range)

    if num_enemies_in_range == 0:
        return

    needs_sos = (
            (num_enemies_in_range > 6 and num_sos_spirits < 3) or
            (num_enemies_in_range > 4 and num_sos_spirits < 2) or
            (num_enemies_in_range > 2 and num_sos_spirits < 1)
        )
    
    if needs_sos and (Helper.is_fighting() or Helper.can_fight()):
        result = Helper.smartcast_hero_skill(skill_id=SoS_skill_id, min_enemies=0, 
                                        enemy_range_check=Helper.get_spell_cast_range(), 
                                        hero_target=True, distance_check_range=Helper.get_spell_cast_range() + 200)
        if result:
            execute_hero_skill(*result)


# Function: smart_bip
# Manages the casting of Blood is Power to support the player’s energy regeneration.
def smart_bip():
    if Party.GetHeroCount() == 0:
        return
    BiP_id = Skill.GetID("Blood_is_Power")
    if not Helper.can_execute_with_delay("smart_bip", 500):
        return

    player_id = Player.GetAgentID()
    energy_data = Helper.get_energy_data()
    player_profession, _ = Agent.GetProfessionNames(player_id)

    player_has_bip = bool(Helper.check_for_effects(player_id, [BiP_id]))
    if not Helper.is_agent_alive(player_id):
        return
    if player_has_bip:
        return
    if energy_data.regen > 0.03:
        return

    energy_thresholds = {
        "Warrior": (25, 0.70), 
        "Ranger": (25, 0.60), 
        "Monk": (30, 0.50),
        "Necromancer": (30, 0.50), 
        "Mesmer": (30, 0.50), 
        "Elementalist": (40, 0.40),
        "Assassin": (25, 0.60), 
        "Ritualist": (30, 0.50), 
        "Paragon": (25, 0.60),
        "Dervish": (25, 0.50),
    }

    if player_profession not in energy_thresholds:
        return

    min_energy, min_percent = energy_thresholds[player_profession]

    if energy_data.current >= min_energy and energy_data.percentage > min_percent:
        return

    result = Helper.smartcast_hero_skill(skill_id=BiP_id, min_enemies=0, 
                                       enemy_range_check=Helper.get_spell_cast_range(), 
                                       effect_check=True,cast_target_id=player_id,
                                       distance_check_range=Helper.get_spell_cast_range() + 200, 
                                       allow_out_of_combat=True, min_health_perc=0.5)
    if result:
        execute_hero_skill(*result)


last_follow_state = None
last_logged_follow_delay = None
last_player_position = None
last_follow_time = 0
follow_toggled_time = 0
last_movement_time = 0
last_autoattack_unfollow_time = 0
is_waiting_to_unfollow = False
is_following_disabled_due_to_idle = False
is_following_disabled_due_to_attack = False
is_following_active = False

# Function: should_unfollow_due_to_idle
# Handles the logic for function execution.
def should_unfollow_due_to_idle(current_position, min_moving_time):
    global last_player_position, last_movement_time
    
    if not last_player_position:
        return False  
    is_idle = current_position == last_player_position
    time_since_last_movement = time.time() - last_movement_time
    return is_idle and time_since_last_movement >= min_moving_time


# Function: smart_hero_follow
# Flags heroes to follow the player at predefined intervals.
def smart_hero_follow():
    global last_follow_state, last_logged_follow_delay, is_following_active
    if last_follow_state is None:
        last_follow_state = widget_config.smart_follow_toggled
        last_logged_follow_delay = widget_config.follow_delay
        return
    
    if not Helper.can_execute_with_delay("FollowFlag", widget_config.follow_delay, 50):
        return

    action_queue.add_action(Helper.flag_heroes)

    if last_follow_state != widget_config.smart_follow_toggled or last_logged_follow_delay != widget_config.follow_delay:
        Helper.log_event(message=f"Heroes on follow every ({widget_config.follow_delay}ms)")
        last_logged_follow_delay = widget_config.follow_delay

    if widget_config.hero_behaviour != Helper.HERO_BEHAVIOUR_AVOID_COMBAT:
        widget_config.last_known_hero_behaviour = widget_config.hero_behaviour
        set_hero_behaviour(Helper.HERO_BEHAVIOUR_AVOID_COMBAT)
        widget_config.hero_behaviour = Helper.HERO_BEHAVIOUR_AVOID_COMBAT

    last_follow_state = widget_config.smart_follow_toggled
    is_following_active = True  # Follow is now active


# Function: smart_hero_unfollow
# Stops hero following to allow free movement.
def smart_hero_unfollow():
    global last_follow_state, is_following_active
    if not is_following_active:
        return  # Prevent redundant unfollow calls

    action_queue.add_action(Helper.unflag_heroes)
    Helper.log_event(message="Heroes have stopped following")

    if widget_config.hero_behaviour != widget_config.last_known_hero_behaviour:
        set_hero_behaviour(widget_config.last_known_hero_behaviour)
        widget_config.hero_behaviour = widget_config.last_known_hero_behaviour

    last_follow_state = widget_config.smart_follow_toggled
    is_following_active = False  # Follow is now disabled


# Function: update_hero_follow_state
# Manages hero follow behavior dynamically based on combat and movement.
def update_hero_follow_state():
    global last_follow_state, last_player_position, last_movement_time, is_waiting_to_unfollow
    global is_following_disabled_due_to_idle, follow_toggled_time, is_following_disabled_due_to_attack
    global last_autoattack_unfollow_time, is_following_active

    if not Helper.can_execute_with_delay("update_follow_state", 500):  
        return
    
    current_time = time.time()
    current_player_position = Player.GetXY()
    num_enemies_near_player = Helper.count_enemies_in_range(Helper.get_spell_cast_range(), current_player_position)
    min_moving_time = 2 if num_enemies_near_player > 0 else 5

    if widget_config.smart_follow_toggled and last_follow_state != widget_config.smart_follow_toggled:
        follow_toggled_time = time.time()

    if Helper.is_auto_attacking(): # or Helper.is_hero_attacking():
        if is_following_active:
            smart_hero_unfollow()
            is_following_disabled_due_to_attack = True
            last_autoattack_unfollow_time = current_time
        return

    is_following_disabled_due_to_attack = False

    if current_time - last_autoattack_unfollow_time < 8:
        return

    if not widget_config.smart_follow_toggled:
        if is_following_active:
            smart_hero_unfollow()
        last_follow_state = widget_config.smart_follow_toggled
        return

    if should_unfollow_due_to_idle(current_player_position, min_moving_time):
        if time.time() - follow_toggled_time >= min_moving_time and not is_waiting_to_unfollow:
            smart_hero_unfollow()
            is_waiting_to_unfollow = True
            is_following_disabled_due_to_idle = True
            last_follow_state = widget_config.smart_follow_toggled
            return

    if current_player_position != last_player_position:
        last_movement_time = time.time()
        is_waiting_to_unfollow = False
        if is_following_disabled_due_to_idle:
            smart_hero_follow()
            is_following_disabled_due_to_idle = False

    if not is_following_disabled_due_to_idle and not is_following_disabled_due_to_attack:
        smart_hero_follow()

    last_player_position = current_player_position
    last_follow_state = widget_config.smart_follow_toggled


# Function: set_hero_behaviour
# Updates hero behavior settings and logs the change.
def set_hero_behaviour(behaviour):
    action_queue.add_action(lambda: Helper.set_heroes_behaviour(behaviour))
    behaviour_names = {0: "Fight", 1: "Guard", 2: "Avoid"}
    behaviour_str = behaviour_names.get(behaviour, f"Unknown ({behaviour})")
    Helper.log_event(message=f"Set all heroes to {behaviour_str}.")


# Function: draw_window
# Handles UI rendering for the Hero Helper module.
def draw_window():
    PyImGui.set_next_window_size(300, 200)

    if PyImGui.begin(window_module.window_name, window_module.window_flags | PyImGui.WindowFlags.NoScrollbar):
        PyImGui.begin_group()

        if PyImGui.begin_child("Console", size=(280.0, 50.0), border=False, flags=0):
            for log in reversed(Helper.console_logs):
                PyImGui.text(log)
            PyImGui.end_child()
        PyImGui.separator()

        PyImGui.text("Set Hero Behaviour")
        PyImGui.separator()

        total_width = PyImGui.get_content_region_avail()[0] - 10  
        button_width = total_width / 3  
        if PyImGui.button("Fight", width=button_width):
            widget_config.hero_behaviour = 0
            set_hero_behaviour(0)
        PyImGui.same_line(0.0, 5.0)
        if PyImGui.button("Guard", width=button_width):
            widget_config.hero_behaviour = 1
            set_hero_behaviour(1)
        PyImGui.same_line(0.0, 5.0)
        if PyImGui.button("Avoid", width=button_width):
            widget_config.hero_behaviour = 2
            set_hero_behaviour(2)
        PyImGui.separator()

        available_width = PyImGui.get_content_region_avail()[0]
        # button_width = int((available_width - 10) / 2)
        button_width = int(available_width)

        new_follow_state = ImGui.toggle_button("Follow", widget_config.smart_follow_toggled, button_width, 30)
        widget_config.smart_follow_toggled = new_follow_state
        PyImGui.same_line(0.0, 10)

    PyImGui.end()


ALL_HEXES = [
    "Amity", "Defender's_Zeal", "Pacifism", "Scourge_Enchantment",
    "Scourge_Healing", "Scourge_Sacrifice",

    "Atrophy", "Barbs", "Blood_Bond", "Cacophony", "Corrupt_Enchantment",
    "Defile_Defenses", "Defile_Flesh", "Depravity", "Faintheartedness",
    "Icy_Veins", "Insidious_Parasite", "Life_Siphon", "Life_Transfer",
    "Lingering_Curse", "Malaise", "Malign_Intervention", "Mark_of_Fury",
    "Mark_of_Pain", "Mark_of_Subversion", "Meekness", "Parasitic_Bond",
    "Price_of_Failure", "Putrid_Bile", "Reaper's_Mark", "Reckless_Haste",
    "Rigor_Mortis", "Rising_Bile", "Shadow_of_Fear", "Shivers_of_Dread",
    "Soul_Barbs", "Soul_Bind", "Soul_Leech", "Spinal_Shivers",
    "Spiteful_Spirit", "Spoil_Victor", "Suffering", "Ulcerous_Lungs",
    "Vile_Miasma", "Vocal_Minority", "Wail_of_Doom", "Weaken_Knees",
    "Wither",

    "Air_of_Disenchantment", "Arcane_Conundrum", "Arcane_Languor", "Backfire",
    "Calculated_Risk", "Clumsiness", "Confusing_Images", "Conjure_Nightmare",
    "Conjure_Phantasm", "Crippling_Anguish", "Diversion", "Empathy",
    "Enchanter's_Conundrum", "Ether_Lord", "Ether_Nightmare", "Ether_Phantom",
    "Ethereal_Burden", "Fevered_Dreams", "Fragility", "Frustration", "Guilt",
    "Ignorance", "Illusion_of_Pain", "Images_of_Remorse", "Imagined_Burden",
    "Ineptitude", "Kitah's_Burden", "Migraine", "Mind_Wrack", "Mistrust",
    "Overload", "Panic", "Phantom_Pain", "Power_Flux", "Power_Leech",
    "Price_of_Pride", "Recurring_Insecurity", "Shame", "Shared_Burden",
    "Shrinking_Armor", "Soothing_Images", "Spirit_Shackles",
    "Spirit_of_Failure", "Stolen_Speed", "Sum_of_All_Fears",
    "Visions_of_Regret", "Wandering_Eye", "Wastrel's_Demise",
    "Wastrel's_Worry", "Web_of_Disruption",

    "Ash_Blast", "Blurred_Vision", "Chilling_Winds", "Deep_Freeze",
    "Earthen_Shackles", "Freezing_Gust", "Frozen_Burst", "Glimmering_Mark",
    "Grasping_Earth", "Ice_Prison", "Ice_Spikes", "Icicles", "Icy_Shackles",
    "Incendiary_Bonds", "Lightning_Strike", "Lightning_Surge",
    "Mark_of_Rodgort", "Mind_Freeze", "Mirror_of_Ice", "Rust", "Shard_Storm",
    "Shatterstone", "Smoldering_Embers", "Teinai's_Prison", "Winter's_Embrace",

    "Assassin's_Promise", "Augury_of_Death", "Dark_Prison", "Enduring_Toxin",
    "Expose_Defenses", "Hidden_Caltrops", "Mark_of_Death", "Mark_of_Insecurity",
    "Mark_of_Instability", "Mirrored_Stance", "Scorpion_Wire", "Seeping_Wound",
    "Shadow_Fang", "Shadow_Prison", "Shadow_Shroud", "Shadowy_Burden",
    "Shameful_Fear", "Siphon_Speed", "Siphon_Strength",

    "Binding_Chains", "Dulled_Weapon", "Lamentation", "Painful_Bond",
    "Renewing_Surge"
]

# Function: configure
# Loads and manages configuration settings via the UI.
def configure():
    global widget_config, config_module, ini_handler
       
    if config_module.first_run:
        PyImGui.set_next_window_size(config_module.window_size[0], config_module.window_size[1])
        PyImGui.set_next_window_pos(config_module.window_pos[0], config_module.window_pos[1])
        config_module.first_run = False
        
    if PyImGui.begin(config_module.window_name, config_module.window_flags):
        
        if PyImGui.begin_tab_bar("Hero Helper Config Tabs"):
            
            if PyImGui.begin_tab_item("Follow"):
                
                PyImGui.text("Follow Delay (ms)")
                widget_config.follow_delay = PyImGui.slider_int("##follow_delay_slider", widget_config.follow_delay, 500, 2000)
                PyImGui.same_line(0,5)
                widget_config.follow_delay = PyImGui.input_int("##hidden_label", widget_config.follow_delay)
                widget_config.follow_delay = max(500, min(2000, widget_config.follow_delay))

                PyImGui.end_tab_item()
                
            if PyImGui.begin_tab_item("Smart Skills"):

                Helper.create_and_update_checkbox("Smart Blood is Power", "smart_bip_enabled", tooltip_text="Automatically cast Blood is Power on player when needed.")
                PyImGui.same_line(0.0, 21)
                Helper.create_and_update_checkbox("Smart Signet of Spirits", "smart_sos_enabled", tooltip_text="Automatically casts Signet of Spirits when necessary.")
                
                Helper.create_and_update_checkbox("Smart Soul Twisting", "smart_st_enabled", tooltip_text="Automatically casts Shelter and Union based on combat conditions.")
                PyImGui.same_line(0.0, 31)
                Helper.create_and_update_checkbox("Smart Strength of Honor", "smart_honor_enabled", tooltip_text="[DISABLE HERO CASTING] If a Melee class with a Melee weapon it maintains Honor on you")
                
                Helper.create_and_update_checkbox("Smart Splinter Weapon", "smart_splinter_enabled", tooltip_text="If a Melee class with a Melee weapon it cast Splinter weapon on you in combat")
                PyImGui.same_line(0.0, 10)
                Helper.create_and_update_checkbox("Smart Vigorous Spirit", "smart_vigorous_enabled", tooltip_text="If a Melee class with a Melee weapon it cast Vigorous Spirit on you in combat")
                
                PyImGui.end_tab_item()
                
            if PyImGui.begin_tab_item("Smart Cleanse"):
                if PyImGui.collapsing_header("Condition Removal", PyImGui.TreeNodeFlags.DefaultOpen):
                    PyImGui.text_wrapped("Assign Prio Cleanse Conditions to Melee, Caster, or Both\n(Leave blank to keep default priority):")

                    if PyImGui.is_item_hovered():
                        PyImGui.set_tooltip("Melee: Prioritizes cleansing melee characters.\n"
                                            "Caster: Prioritizes cleansing caster characters.\n"
                                            "Both: Prio cleanses no matter class.")

                    changes_made = False

                    if PyImGui.begin_table("ConditionTable", 4, PyImGui.TableFlags.Borders | PyImGui.TableFlags.RowBg | PyImGui.TableFlags.SizingStretchSame):
                        PyImGui.table_setup_column("Condition", PyImGui.TableColumnFlags.WidthStretch)
                        PyImGui.table_setup_column("Melee", PyImGui.TableColumnFlags.WidthFixed)
                        PyImGui.table_setup_column("Caster", PyImGui.TableColumnFlags.WidthFixed)
                        PyImGui.table_setup_column("Both", PyImGui.TableColumnFlags.WidthFixed)
                        PyImGui.table_headers_row()

                        for condition_name, data in widget_config.conditions.items():
                            PyImGui.table_next_row()

                            PyImGui.table_next_column()
                            row_height = PyImGui.get_text_line_height_with_spacing()
                            text_height = PyImGui.calc_text_size(condition_name.replace("_", " "))[1]
                            padding = (row_height - text_height) / 2
                            PyImGui.dummy(0, int(padding))
                            PyImGui.text_wrapped(condition_name.replace("_", " "))
                            PyImGui.same_line(0, 0)

                            prev_melee, prev_caster, prev_both = data["melee"], data["caster"], data["both"]

                            PyImGui.table_next_column()
                            new_melee = PyImGui.checkbox(f"##melee_{condition_name}", prev_melee)

                            PyImGui.table_next_column()
                            new_caster = PyImGui.checkbox(f"##caster_{condition_name}", prev_caster)

                            PyImGui.table_next_column()
                            new_both = PyImGui.checkbox(f"##both_{condition_name}", prev_both)

                            if new_melee and not prev_melee:
                                data["melee"], data["caster"], data["both"] = True, False, False
                            elif new_caster and not prev_caster:
                                data["melee"], data["caster"], data["both"] = False, True, False
                            elif new_both and not prev_both:
                                data["melee"], data["caster"], data["both"] = False, False, True
                            elif not new_melee and not new_caster and not new_both:
                                data["melee"], data["caster"], data["both"] = False, False, False

                            changes_made |= (prev_melee != data["melee"] or prev_caster != data["caster"] or prev_both != data["both"])

                    PyImGui.end_table()

                    if changes_made:
                        widget_config.save()

                    if PyImGui.button("Set Recommended Defaults", height=25):
                        recommended_defaults = {
                            "Blind": {"melee": True, "caster": False, "both": False},
                            "Weakness": {"melee": True, "caster": False, "both": False},
                            "Dazed": {"melee": False, "caster": True, "both": False},
                            "Crippled": {"melee": False, "caster": False, "both": True},
                        }

                        for condition in widget_config.conditions:
                            widget_config.conditions[condition]["melee"] = False
                            widget_config.conditions[condition]["caster"] = False
                            widget_config.conditions[condition]["both"] = False

                        for condition, values in recommended_defaults.items():
                            if condition in widget_config.conditions:
                                widget_config.conditions[condition].update(values)

                        widget_config.save()

                    PyImGui.same_line(0.0, -1)
                    available_width = PyImGui.get_content_region_avail()[0]
                    button_width = int(available_width)

                    cleanse_conditions = ImGui.toggle_button("Enable Condition Cleanse", widget_config.smart_con_cleanse_toggled, button_width, 25)
                    widget_config.smart_con_cleanse_toggled = cleanse_conditions
                
                if PyImGui.collapsing_header("Hex Removal", PyImGui.TreeNodeFlags.DefaultOpen):

                    PyImGui.text_wrapped("These hexes will be prioritized for removal.")

                    if PyImGui.is_item_hovered():
                        PyImGui.set_tooltip("Hexes in each list will be removed automatically when detected.")

                    if not hasattr(widget_config, "hexes_melee") or not widget_config.hexes_melee:
                        widget_config.hexes_melee = [
                            "Ineptitude", "Empathy", "Crippling Anguish", "Clumsiness", "Faintheartedness",
                            "Blurred Vision", "Amity"
                        ]
                    if not hasattr(widget_config, "hexes_caster") or not widget_config.hexes_caster:
                        widget_config.hexes_caster = [
                            "Panic", "Backfire", "Mistrust", "Power Leech", "Soul Leech"
                        ]
                    if not hasattr(widget_config, "hexes_all") or not widget_config.hexes_all:
                        widget_config.hexes_all = [
                            "Diversion", "Visions of Regret", "Deep Freeze", "Mind Freeze", "Icy Shackles", "Spiteful Spirit"
                        ]
                    if not hasattr(widget_config, "hexes_paragon") or not widget_config.hexes_paragon:
                        widget_config.hexes_paragon = ["Vocal Minority"]

                    if PyImGui.collapsing_header("Hexes to be priority removed from Melee", PyImGui.TreeNodeFlags.DefaultOpen):
                        PyImGui.columns(2, "melee_hexes", False)
                        for hex_name in widget_config.hexes_melee[:4]:
                            PyImGui.text(f"- {hex_name.replace('_', ' ')}")
                        PyImGui.next_column()
                        for hex_name in widget_config.hexes_melee[4:]:
                            PyImGui.text(f"- {hex_name.replace('_', ' ')}")
                        PyImGui.columns(1, "", False)

                    if PyImGui.collapsing_header("Hexes to be priority removed from Casters", PyImGui.TreeNodeFlags.DefaultOpen):
                        PyImGui.columns(2, "caster_hexes", False)
                        for hex_name in widget_config.hexes_caster[:3]:
                            PyImGui.text(f"- {hex_name.replace('_', ' ')}")
                        PyImGui.next_column()
                        for hex_name in widget_config.hexes_caster[3:]:
                            PyImGui.text(f"- {hex_name.replace('_', ' ')}")
                        PyImGui.columns(1, "", False)

                    if PyImGui.collapsing_header("Hexes to be priority removed from All", PyImGui.TreeNodeFlags.DefaultOpen):
                        PyImGui.columns(2, "ALL_HEXES", False)
                        for hex_name in widget_config.hexes_all[:3]:
                            PyImGui.text(f"- {hex_name.replace('_', ' ')}")
                        PyImGui.next_column()
                        for hex_name in widget_config.hexes_all[3:]:
                            PyImGui.text(f"- {hex_name.replace('_', ' ')}")
                        PyImGui.columns(1, "", False)

                    if PyImGui.collapsing_header("Hexes to be priority removed from Paragons", PyImGui.TreeNodeFlags.DefaultOpen):
                        for hex_name in widget_config.hexes_paragon:
                            PyImGui.text(f"- {hex_name.replace('_', ' ')}")

                    if PyImGui.collapsing_header("Hexes added by user", PyImGui.TreeNodeFlags.DefaultOpen):
                        if PyImGui.is_item_hovered():
                            PyImGui.begin_tooltip()
                            PyImGui.text("These are hexes you manually added. Red circle to remove")
                            PyImGui.end_tooltip()
                        
                        if not hasattr(widget_config, "user_hex_input"):
                            widget_config.user_hex_input = ""
                                                
                        for hex_name in widget_config.hexes_user:
                            PyImGui.text(f"- {hex_name.replace('_', ' ')}")
                            PyImGui.push_style_color(PyImGui.ImGuiCol.Button, (0.8, 0.0, 0.0, 1.0))  # Red background
                            PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonHovered, (1.0, 0.2, 0.2, 1.0))  # Brighter red hover
                            PyImGui.push_style_color(PyImGui.ImGuiCol.Text, (1.0, 1.0, 1.0, 1.0))  # White text
                            

                            PyImGui.push_style_var(10, 0.0)
                            PyImGui.push_style_var(11, 0.0)
                            PyImGui.same_line(0,5)
                            if PyImGui.button(f"##{hex_name}",10,10):
                                widget_config.hexes_user.remove(hex_name.replace(' ', '_'))
                                widget_config.save_hexes()
                                Helper.log_event(message=f"Removed {hex_name} from user hex list")

                            PyImGui.pop_style_color(3)
                            PyImGui.pop_style_var(2)

                        PyImGui.text("Add a hex spell:")
                        widget_config.user_hex_input = PyImGui.input_text("##user_hex_input", widget_config.user_hex_input)

                        PyImGui.same_line(0,5)
                        
                        available_width = PyImGui.get_content_region_avail()[0]
                        button_width = int(available_width)
                        
                        if PyImGui.button("Add Hex", button_width):
                            user_input = widget_config.user_hex_input.strip()
                            formatted_hex = user_input.replace(" ", "_").lower()
                            formatted_title_hex = Helper.format_spell_title_case(user_input)

                            existing_hexes_lower = [hex_name.lower() for hex_name in (
                                widget_config.hexes_melee +
                                widget_config.hexes_caster +
                                widget_config.hexes_all +
                                widget_config.hexes_paragon
                            )]

                            if not formatted_hex:
                                Helper.log_event(message="Input was empty. Skipping.")

                            elif formatted_hex in existing_hexes_lower:
                                Helper.log_event(message=f"{formatted_title_hex} already exists in a predefined hex list. Skipping addition.")

                            elif formatted_hex not in [hex_name.lower() for hex_name in widget_config.hexes_user]:
                                Helper.log_event(message=f"{formatted_title_hex} is not in user list, adding now.")
                                widget_config.hexes_user.append(formatted_title_hex)
                                widget_config.save_hexes()

                            else:
                                Helper.log_event(message=f"{formatted_title_hex} is already added by user, skipping addition.")
                            
                            widget_config.user_hex_input = ""

                    available_width = PyImGui.get_content_region_avail()[0]
                    button_width = int(available_width)

                    hex_cleanse_enabled = ImGui.toggle_button("Enable Hex Cleanse", widget_config.smart_hex_cleanse_toggled, button_width, 25)
                    widget_config.smart_hex_cleanse_toggled = hex_cleanse_enabled

                PyImGui.end_tab_item()

            if PyImGui.begin_tab_item("Smart Interrupt"):
                PyImGui.text_wrapped("Manage skills that heroes will interrupt.")

                if PyImGui.collapsing_header("Skills To Interrupt", PyImGui.TreeNodeFlags.DefaultOpen):
                    for skill_name in widget_config.skills_to_rupt:
                        PyImGui.text(f"- {skill_name.replace('_', ' ')}")

                        PyImGui.push_style_color(PyImGui.ImGuiCol.Button, (0.8, 0.0, 0.0, 1.0))  # Red background
                        PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonHovered, (1.0, 0.2, 0.2, 1.0))  # Brighter red hover
                        PyImGui.push_style_color(PyImGui.ImGuiCol.Text, (1.0, 1.0, 1.0, 1.0))  # White text

                        PyImGui.push_style_var(10, 0.0)  # Zero padding
                        PyImGui.push_style_var(11, 0.0)
                        PyImGui.same_line(0, 5)

                        if PyImGui.button(f"##Remove_{skill_name}", 10, 10):  # Small red "X" button
                            widget_config.skills_to_rupt.remove(skill_name)
                            widget_config.save_skills_to_rupt()
                            Helper.log_event(message=f"Removed {skill_name} from interrupt list")

                        PyImGui.pop_style_color(3)
                        PyImGui.pop_style_var(2)

                PyImGui.text("Add a skill to interrupt:")
                widget_config.user_skill_input = PyImGui.input_text("##user_skill_input", widget_config.user_skill_input)

                PyImGui.same_line(0, 5)
                button_width = int(PyImGui.get_content_region_avail()[0])

                if PyImGui.button("Add Skill", button_width):
                    user_input = widget_config.user_skill_input.strip()
                    formatted_skill = Helper.format_spell_title_case(user_input)

                    if not formatted_skill:
                        Helper.log_event(message="Input was empty. Skipping.")
                    elif formatted_skill in widget_config.skills_to_rupt:
                        Helper.log_event(message=f"{formatted_skill} is already in the interrupt list.")
                    else:
                        widget_config.skills_to_rupt.append(formatted_skill)
                        widget_config.save_skills_to_rupt()
                        Helper.log_event(message=f"Added {formatted_skill} to the interrupt list.")

                    widget_config.user_skill_input = ""

                available_width = PyImGui.get_content_region_avail()[0]
                button_width = int(available_width)

                interrupt_enabled = ImGui.toggle_button("Enable Hero Interrupt", widget_config.smart_interrupt_toggled, button_width, 25)
                widget_config.smart_interrupt_toggled = interrupt_enabled

        end_pos = PyImGui.get_window_pos()
        if end_pos[0] != config_module.window_pos[0] or end_pos[1] != config_module.window_pos[1]:
            config_module.window_pos = (int(end_pos[0]), int(end_pos[1]))
            ini_handler.write_key(MODULE_NAME + " Config", "config_x", str(int(end_pos[0])))
            ini_handler.write_key(MODULE_NAME + " Config", "config_y", str(int(end_pos[1])))   

    PyImGui.end()
    

# Function: main
# Handles the logic for function execution.


def main():

    if Helper.is_game_ready():
        
        if Helper.can_execute_with_delay("cache_agent_names", 2000):
            Helper.cache_agent_names()
            Helper.cache_hero_skills()
                   
        if Map.IsExplorable():
            update_hero_follow_state()
            if widget_config.smart_interrupt_toggled:
                smart_interrupt()
            if widget_config.smart_hex_cleanse_toggled:
                smart_hex_removal()
            if widget_config.smart_con_cleanse_toggled:
                smart_cond_removal()
            if widget_config.smart_vigorous_enabled: 
                smart_vigorous()
            if widget_config.smart_splinter_enabled: 
                smart_splinter()
            if widget_config.smart_honor_enabled: 
                smart_honor()
            if widget_config.smart_st_enabled:   
                smart_st()
            if widget_config.smart_bip_enabled:
                smart_bip()   
            if widget_config.smart_sos_enabled:
                smart_sos()

        draw_window()
        
        if not action_queue.is_empty():
            action_queue.execute_next()
        
        if any(getattr(widget_config, key) != widget_config._cache[key] for key in widget_config.tracked_keys):
            widget_config.save()   
    
    return True

if __name__ == "__main__":
    main()