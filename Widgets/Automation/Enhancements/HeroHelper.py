from Py4GWCoreLib import *
import Py4GW

from collections import namedtuple
import os
import time
import random

MODULE_NAME = "HeroHelper"

script_directory = os.path.dirname(os.path.abspath(__file__))
root_directory = Py4GW.Console.get_projects_path()
INI_FILE_LOCATION = os.path.join(root_directory, "Widgets/Config/HeroHelper.ini")

ini_handler = IniHandler(INI_FILE_LOCATION)

action_queue = ActionQueue()

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

class Config:
    def __init__(self):
        self.tracked_keys = [
            "smart_follow_toggled",
            "attack_toggled",
            "follow_delay",
            "smart_bip_enabled",
            "smart_sos_enabled",
            "smart_st_enabled",
            "smart_honor_enabled",
            "smart_life_bond_enabled",
            "smart_splinter_enabled",
            "smart_vigorous_enabled",
            "smart_dark_aura_enabled",
            "smart_healing_enabled",
            "hero_behaviour",
            "last_known_hero_behaviour",
            "conditions",
            "hexes",
            "skills_to_rupt",
            "smart_con_cleanse_toggled",
            "smart_hex_cleanse_toggled",
            "smart_interrupt_toggled",
            "smart_incoming_fallback_enabled",
            "user_hex_input",
            "user_skill_input",
            "floating_window_enabled"
        ]

        self.smart_follow_toggled = ini_handler.read_bool(MODULE_NAME, "smart_follow_toggled", False)
        self.attack_toggled = ini_handler.read_bool(MODULE_NAME, "attack_toggled", False)
        self.follow_delay = ini_handler.read_int(MODULE_NAME, "follow_delay", 800)
        self.smart_bip_enabled = ini_handler.read_bool(MODULE_NAME, "smart_bip_enabled", False)
        self.smart_sos_enabled = ini_handler.read_bool(MODULE_NAME, "smart_sos_enabled", False)
        self.smart_st_enabled = ini_handler.read_bool(MODULE_NAME, "smart_st_enabled", False)
        self.smart_honor_enabled = ini_handler.read_bool(MODULE_NAME, "smart_honor_enabled", False)
        self.smart_life_bond_enabled = ini_handler.read_bool(MODULE_NAME, "smart_life_bond_enabled", False)
        self.smart_splinter_enabled = ini_handler.read_bool(MODULE_NAME, "smart_splinter_enabled", False)
        self.smart_vigorous_enabled = ini_handler.read_bool(MODULE_NAME, "smart_vigorous_enabled", False)
        self.smart_dark_aura_enabled = ini_handler.read_bool(MODULE_NAME, "smart_dark_aura_enabled", False)
        self.smart_healing_enabled = ini_handler.read_bool(MODULE_NAME, "smart_healing_enabled", False)
        self.hero_behaviour = ini_handler.read_int(MODULE_NAME, "hero_behaviour", 0)
        self.last_known_hero_behaviour = ini_handler.read_int(MODULE_NAME, "last_known_hero_behaviour", self.hero_behaviour)
        self.smart_con_cleanse_toggled = ini_handler.read_bool(MODULE_NAME, "smart_con_cleanse_toggled", False)
        self.smart_hex_cleanse_toggled = ini_handler.read_bool(MODULE_NAME, "smart_hex_cleanse_toggled", False)
        self.smart_interrupt_toggled = ini_handler.read_bool(MODULE_NAME, "smart_interrupt_toggled", False)
        self.smart_incoming_fallback_enabled = ini_handler.read_bool(MODULE_NAME, "smart_incoming_fallback_enabled", False)
        self.floating_window_enabled = ini_handler.read_bool(MODULE_NAME, "floating_window_enabled", False)
        
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

    def load_conditions(self):
        conditions = {}
        for condition in [
            "Bleeding", "Blind", "Burning", "Cracked_Armor", "Crippled",
            "Dazed", "Deep_Wound", "Disease", "Poison", "Weakness"
        ]:
            key = f"smart_cleanse_cond_{condition.lower()}"
            value = ini_handler.read_key(MODULE_NAME, key, "false,false,false")
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

    def save_conditions(self):
        for condition, data in self.conditions.items():
            key = f"smart_cleanse_cond_{condition.lower()}"
            value = f"{data['melee']},{data['caster']},{data['both']}"
            ini_handler.write_key(MODULE_NAME, key, value)

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

    def save_hexes(self):
        ini_handler.write_key(MODULE_NAME, "hexes_melee", ",".join(self.hexes_melee))
        ini_handler.write_key(MODULE_NAME, "hexes_caster", ",".join(self.hexes_caster))
        ini_handler.write_key(MODULE_NAME, "hexes_all", ",".join(self.hexes_all))
        ini_handler.write_key(MODULE_NAME, "hexes_paragon", ",".join(self.hexes_paragon))
        ini_handler.write_key(MODULE_NAME, "hexes_user", ",".join(self.hexes_user))

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

    def save_skills_to_rupt(self):
            ini_handler.write_key(MODULE_NAME, "skills_to_rupt", ",".join(self.skills_to_rupt))

    def save(self):
            for key in self.tracked_keys:
                value = getattr(self, key)

                if isinstance(value, bool):
                    ini_handler.write_key(MODULE_NAME, key, "true" if value else "false")
                elif key == "conditions":
                    self.save_conditions()
                elif key == "hexes":
                    self.save_hexes()
                elif key == "skills_to_rupt":
                    self.save_skills_to_rupt()
                else:
                    ini_handler.write_key(MODULE_NAME, key, str(value))

                self._cache[key] = value


widget_config = Config()
window_module = ImGui.WindowModule(MODULE_NAME, window_name="Hero Helper", window_size=(200, 100), window_flags=PyImGui.WindowFlags.AlwaysAutoResize)
config_module = ImGui.WindowModule(f"Config {MODULE_NAME}", window_name="Hero Helper Configuration", window_size=(300, 175), window_flags=PyImGui.WindowFlags.AlwaysAutoResize)

config_module.window_pos = (
    ini_handler.read_int(MODULE_NAME + " Config", "config_x", 100),
    ini_handler.read_int(MODULE_NAME + " Config", "config_y", 100)
)


class Helper:
    @staticmethod
    def is_game_ready():
        return Map.IsMapReady() and Party.IsPartyLoaded()
        
    @staticmethod
    def get_energy_data(agent_id=None):
        Energy = namedtuple("energy_data", ["percentage", "max", "current", "regen"])
        agent_id = agent_id or Player.GetAgentID()
        if not agent_id or Agent.IsDead(agent_id):
            return Energy(0, 0, 0, 0)

        perc = Agent.GetEnergy(agent_id)
        max_val = Agent.GetMaxEnergy(agent_id)
        return Energy(perc, max_val, int(perc * max_val), Agent.GetEnergyRegen(agent_id))
    
    @staticmethod
    def get_hp_data(agent_id=None):
        Health = namedtuple("hp_data", ["percentage", "max", "current", "regen"])
        agent_id = agent_id or Player.GetAgentID()
        if not agent_id or Agent.IsDead(agent_id):
            return Health(0, 0, 0, 0)

        perc = Agent.GetHealth(agent_id)
        max_val = Agent.GetMaxHealth(agent_id)
        return Health(perc, max_val, int(perc * max_val), Agent.GetHealthRegen(agent_id))
    
    @staticmethod
    def is_agent_alive(agent_id):
        return agent_id is not None and Agent.IsLiving(agent_id)
        
    HERO_BEHAVIOUR_FIGHT = 0
    HERO_BEHAVIOUR_GUARD = 1
    HERO_BEHAVIOUR_AVOID_COMBAT = 2
    @staticmethod
    def set_heroes_behaviour(behaviour):
        heroes = Party.GetHeroes()
        if not heroes:
            return
        for hero in heroes:
            if hero.agent_id:
                Party.Heroes.SetHeroBehavior(hero.agent_id, behaviour)
                
    @staticmethod
    def flag_heroes(*position):
        x, y = position if position else Player.GetXY()
        if x is not None and y is not None:
            Party.Heroes.FlagAllHeroes(x, y)
    
    @staticmethod
    def unflag_heroes():
        Party.Heroes.UnflagAllHeroes()

    @staticmethod
    def can_execute_with_delay(identifier, delay_ms, jitter_ms=0):
        if not hasattr(Helper, "execution_timers"):
            Helper.execution_timers = {}

        now = time.time() * 1000
        last = Helper.execution_timers.get(identifier, 0)
        jitter = random.randint(-jitter_ms, jitter_ms) if jitter_ms else 0
        if now - last >= delay_ms + jitter:
            Helper.execution_timers[identifier] = now
            return True
        return False
    
    @staticmethod
    def create_and_update_checkbox(label, config_attr, tooltip_text=None):
        prev = getattr(widget_config, config_attr)
        curr = PyImGui.checkbox(label, prev)
        setattr(widget_config, config_attr, curr)

        if curr != prev:
            Helper.log_event(message=f"{label} {'Enabled' if curr else 'Disabled'}")

        if tooltip_text and PyImGui.is_item_hovered():
            PyImGui.set_tooltip(tooltip_text)

    last_cast_logs = {}
    console_logs = []
    @staticmethod
    def log_event(hero_id=None, skill_name=None, target_name=None, skill_id=None, target_id=None, message=None, cooldown=10):
        if skill_id and target_id:
            key = (hero_id, skill_id, target_id)
            now = time.time()
            if key in Helper.last_cast_logs and now - Helper.last_cast_logs[key] < cooldown:
                return
            Helper.last_cast_logs[key] = now
            message = f"Casting skill [{skill_name}] on target [{target_name}]"

        if message:
            Helper.console_logs.append(message)
            Helper.console_logs = Helper.console_logs[-5:]
            Py4GW.Console.Log(MODULE_NAME, message, Py4GW.Console.MessageType.Notice)

    hero_skill_cache = []
    @staticmethod
    def cache_hero_skills():
        if not Helper.should_update_cache():
            return Helper.hero_skill_cache

        Helper.hero_skill_cache.clear()
        Helper.last_map_id = Map.GetMapID()

        for idx, hero in enumerate(Party.GetHeroes() or [], start=1):
            Helper._cache_skills_for_hero(idx)

        return Helper.hero_skill_cache

    @staticmethod
    def reset_hero_skill_cache():
        Helper.hero_skill_cache.clear()

    last_map_id = None
    @staticmethod
    def should_update_cache():
        return Map.GetMapID() != Helper.last_map_id

    @staticmethod
    def _cache_skills_for_hero(hero_index):
        skillbar = SkillBar.GetHeroSkillbar(hero_index)
        if not skillbar:
            return

        for slot, skill in enumerate(skillbar, start=1):
            Helper.hero_skill_cache.append({
                "hero_index": hero_index,
                "skill_slot": slot,
                "skill_id": skill.id.id,
                "skill_name": Skill.GetName(skill.id.id)
            })

    effect_cache = {}
    @staticmethod
    def get_active_effects(agent_id):
        return {
            effect.skill_id: effect.time_remaining or 5
            for effect in Effects.GetEffects(agent_id) or []
        }

    @staticmethod
    def should_check_effect(agent_id, effect_id):
        key = (agent_id, effect_id)
        now = time.time()

        return key not in Helper.effect_cache or now >= Helper.effect_cache[key]["expires"]

    @staticmethod
    def update_effect_cache(agent_id, effect_id, time_left):
        Helper.effect_cache[(agent_id, effect_id)] = {
            "result": True,
            "expires": time.time() + time_left
        }

    @staticmethod
    def check_for_effects(agent_id, effect_ids):
        if not Helper.is_agent_alive(agent_id):
            return False

        active = Helper.get_active_effects(agent_id)
        for effect_id in effect_ids:
            if effect_id not in active:
                continue
            if not Helper.should_check_effect(agent_id, effect_id):
                return True
            Helper.update_effect_cache(agent_id, effect_id, active[effect_id])
            return True
        return False

    @staticmethod
    def has_effect_on_player_or_heroes(effect_id):
        agents = [Player.GetAgentID()] + [h.agent_id for h in Party.GetHeroes()]
        return any(Helper.check_for_effects(aid, [effect_id]) for aid in agents)

    @staticmethod
    def get_heroes_with_skill(skill_id):
        return [
            h for h in Helper.cache_hero_skills()
            if h["skill_id"] == skill_id and Helper.can_hero_cast_skill(h["hero_index"], skill_id)
        ]

    @staticmethod
    def can_hero_cast_skill(hero_index, skill_id):
        skills = SkillBar.GetHeroSkillbar(hero_index)
        return any(s.id.id == skill_id and s.recharge == 0 for s in skills or [])

    @staticmethod
    def cast_hero_skill(hero_index, skill_slot, target_id):
        SkillBar.HeroUseSkill(target_id, skill_slot, hero_index)

    @staticmethod
    def get_nearby_range():
        return enums.Range.Nearby.value

    @staticmethod
    def get_spell_cast_range():
        return enums.Range.Spellcast.value

    @staticmethod
    def get_spirit_range():
        return enums.Range.Spirit.value
    
    @staticmethod
    def is_specific_spirit_in_range(spirit_id, custom_range):
        spirits = AgentArray.GetSpiritPetArray()
        if not spirits or spirit_id not in spirits:
            return False

        px, py = Player.GetXY()
        sx, sy = Agent.GetXY(spirit_id)
        return Utils.Distance((px, py), (sx, sy)) <= custom_range
    
    @staticmethod
    def count_spirits_in_range(spirit_ids, custom_range):
        return sum(1 for sid in spirit_ids if Helper.is_specific_spirit_in_range(sid, custom_range))

    @staticmethod
    def count_enemies_in_range(custom_range, position=None):
        if position is None:
            position = Player.GetXY()
        return sum(
            1 for eid in AgentArray.GetEnemyArray() or []
            if not Agent.IsDead(eid) and Utils.Distance(position, Agent.GetXY(eid)) <= custom_range
        )

    @staticmethod
    def is_fighting(agent_id=None):
        agent_id = agent_id or Player.GetAgentID()
        return Agent.IsAttacking(agent_id) or Agent.IsCasting(agent_id)

    @staticmethod
    def is_auto_attacking(agent_id=None):
        agent_id = agent_id or Player.GetAgentID()
        return Agent.IsAttacking(agent_id)
    
    @staticmethod
    def is_hero_attacking():
        return any(
            Agent.IsAttacking(hero.agent_id)
            for hero in Party.GetHeroes() or []
            if hero.agent_id
        )

    @staticmethod
    def can_cast(agent_id=None):
        agent_id = agent_id or Player.GetAgentID()
        return agent_id and not any([
            Agent.IsDead(agent_id),
            Agent.IsKnockedDown(agent_id),
            Agent.IsCasting(agent_id),
            Agent.IsMoving(agent_id)
        ])

    @staticmethod
    def can_attack(agent_id=None):
        agent_id = agent_id or Player.GetAgentID()
        return agent_id and not any([
            Agent.IsDead(agent_id),
            Agent.IsKnockedDown(agent_id),
            Agent.IsCasting(agent_id),
            Agent.IsMoving(agent_id),
            Agent.IsAttacking(agent_id)
        ])
    
    @staticmethod
    def can_fight(agent_id=None):
        return Helper.can_attack(agent_id) or Helper.can_cast(agent_id)

    @staticmethod
    def get_aftercast(skill_id):
        activation = Skill.Data.GetActivation(skill_id)
        aftercast = Skill.Data.GetAftercast(skill_id)
        ping = Py4GW.PingHandler().GetCurrentPing()
        return max(activation * 1000 + aftercast * 750 + ping + 50, 500)
    
    @staticmethod
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

        cast_target_id = cast_target_id or player_id

        if min_enemies > 0:
            enemy_range_check = enemy_range_check or Helper.get_spell_cast_range()
            enemies_near = Helper.count_enemies_in_range(enemy_range_check, Player.GetXY())

            if not allow_out_of_combat and enemies_near < min_enemies and not Helper.is_fighting():
                return None

        if effect_check and Helper.check_for_effects(cast_target_id, [skill_id]):
            return None

        distance_check_range = distance_check_range or Helper.get_spell_cast_range() + 200

        for hero in heroes_ready:
            hero_index = hero["hero_index"]
            hero_id = Party.Heroes.GetHeroAgentIDByPartyPosition(hero_index)
            if not hero_id:
                continue

            distance = Utils.Distance(Player.GetXY(), Agent.GetXY(hero_id))
            if distance > distance_check_range:
                continue

            if hero_target:
                cast_target_id = hero_id

            energy = Helper.get_energy_data(hero_id)
            health = Helper.get_hp_data(hero_id)

            if min_health_perc and health.percentage < min_health_perc:
                continue
            if min_energy_perc and energy.percentage < min_energy_perc:
                continue
            if energy.current <= Skill.Data.GetEnergyCost(skill_id):
                continue
            if not Helper.can_hero_cast_skill(hero_index, skill_id):
                continue

            # ...existing code...

            return hero_index, hero["skill_slot"], skill_id, cast_target_id

        return None

    agent_name_cache = {}
    cached_agent_ids = set()
    @staticmethod
    def cache_agent_names():
        if Helper.should_update_cache():
            Helper.reset_agent_name_cache()
            Helper.cached_agent_ids.clear()

        agents = (
            set(AgentArray.GetNPCMinipetArray()) |
            set(AgentArray.GetAllyArray()) |
            set(AgentArray.GetNeutralArray())
        )

        new_ids = agents - Helper.cached_agent_ids
        for aid in new_ids:
            Agent.RequestName(aid)

        for aid in agents:
            if aid not in Helper.agent_name_cache and Agent.IsNameReady(aid):
                Helper.agent_name_cache[aid] = Agent.GetNameByID(aid)

        Helper.cached_agent_ids.update(new_ids)

    @staticmethod
    def get_agent_name_by_id(agent_id):
        if agent_id in Helper.agent_name_cache:
            return Helper.agent_name_cache[agent_id]

        Agent.RequestName(agent_id)
        if Agent.IsNameReady(agent_id):
            name = Agent.GetNameByID(agent_id)
            Helper.agent_name_cache[agent_id] = name
            return name

        return None
    
    @staticmethod
    def reset_agent_name_cache():
        Helper.agent_name_cache.clear()

    @staticmethod
    def is_melee_class():
        player_id = Player.GetAgentID()
        if not player_id:
            return False

        profession, _ = Agent.GetProfessionNames(player_id)
        return profession in {"Assassin", "Dervish", "Warrior", "Paragon", "Ranger"}
    
    @staticmethod
    def holds_melee_weapon():
        items = ItemArray.GetItemArray(ItemArray.CreateBagList(Bag.Equipped_Items))
        if not items:
            return False

        main_hand = items[0] if items else None
        if not main_hand:
            return False

        item_type, _ = Item.GetItemType(main_hand)
        return item_type in {2, 15, 27, 32, 35, 36}  # axe, hammer, sword, daggers, scythe, spear

    @staticmethod
    def format_spell_title_case(spell_name):
        skip = {"of"}
        words = spell_name.split()
        return "_".join(
            word.capitalize() if word.lower() not in skip else word.lower()
            for word in words
        )


hero_aftercast_timers = {}
def execute_hero_skill(hero_index, skill_slot, skill_id, target_id):
    now = time.time()

    if None in (hero_index, skill_slot, skill_id, target_id):
        Helper.log_event(message=(
            f"Error: Invalid parameters in execute_hero_skill(). "
            f"hero_index={hero_index}, skill_slot={skill_slot}, "
            f"skill_id={skill_id}, target_id={target_id}"
        ))
        return

    if not Helper.can_hero_cast_skill(hero_index, skill_id):
        return

    if hero_index in hero_aftercast_timers and now < hero_aftercast_timers[hero_index]:
        return

    Helper.cast_hero_skill(hero_index, skill_slot, target_id)
    delay = Helper.get_aftercast(skill_id) / 1000
    hero_aftercast_timers[hero_index] = now + delay

def smart_interrupt():
    if Party.GetHeroCount() == 0:
        return

    if not Helper.can_execute_with_delay("smart_interrupt", 250):
        return

    skills_to_rupt_ids = {Skill.GetID(name) for name in widget_config.skills_to_rupt}
    skill_class_pairs = [
        (Skill.GetID("Cry_of_Frustration"), "Mesmer"),
        (Skill.GetID("Power_Drain"), "Mesmer")
    ]

    spell_range = Helper.get_spell_cast_range()
    player_pos = Player.GetXY()
    enemies = AgentArray.GetEnemyArray() or []

    casting_enemies = [
        eid for eid in enemies
        if Helper.is_agent_alive(eid)
        and Agent.IsCasting(eid)
        and Utils.Distance(player_pos, Agent.GetXY(eid)) <= spell_range
        and Agent.GetCastingSkillID(eid) in skills_to_rupt_ids
    ]

    if not casting_enemies:
        return

    casting_enemies.sort(key=lambda eid: Utils.Distance(player_pos, Agent.GetXY(eid)))

    for enemy_id in casting_enemies:
        for skill_id, _ in skill_class_pairs:
            result = Helper.smartcast_hero_skill(
                skill_id=skill_id,
                enemy_range_check=spell_range,
                cast_target_id=enemy_id,
                distance_check_range=spell_range + 200
            )
            if result:
                execute_hero_skill(*result)
                return  # Interrupt once per cycle

def smart_hex_removal():
    if not Helper.can_execute_with_delay("smart_hex_removal", 1000):
        return
    if Party.GetHeroCount() == 0:
        return

    player_id = Player.GetAgentID()
    if not player_id or not Helper.is_agent_alive(player_id):
        return

    profs = Agent.GetProfessionShortNames(player_id)
    is_paragon = "P" in profs

    hex_sets = [
        (Helper.holds_melee_weapon(), widget_config.hexes_melee),
        (not Helper.holds_melee_weapon(), widget_config.hexes_caster),
        (True, widget_config.hexes_all),
        (is_paragon, widget_config.hexes_paragon),
        (True, widget_config.hexes_user),
    ]

    if not any(
        cond and Helper.check_for_effects(player_id, {Skill.GetID(name) for name in hex_list})
        for cond, hex_list in hex_sets
    ):
        return

    hex_removal_skills = [
        "Shatter_Hex", "Remove_Hex", "Smite_Hex", "Blessed_Light"
    ]

    for skill_id in map(Skill.GetID, hex_removal_skills):
        result = Helper.smartcast_hero_skill(skill_id=skill_id)
        if result:
            execute_hero_skill(*result)
            break

def smart_cond_removal():
    if Party.GetHeroCount() == 0:
        return
    if not Helper.can_execute_with_delay("smart_cond_removal", 250):
        return

    player_id = Player.GetAgentID()
    if not player_id or not Helper.is_agent_alive(player_id):
        return

    cond_sets = {
        "melee": {data["id"] for data in widget_config.conditions.values() if data["melee"]},
        "caster": {data["id"] for data in widget_config.conditions.values() if data["caster"]},
        "both": {data["id"] for data in widget_config.conditions.values() if data["both"]}
    }

    holds_melee = Helper.holds_melee_weapon()
    condition_found = (
        (holds_melee and Helper.check_for_effects(player_id, cond_sets["melee"])) or
        (not holds_melee and Helper.check_for_effects(player_id, cond_sets["caster"])) or
        Helper.check_for_effects(player_id, cond_sets["both"])
    )

    if not condition_found:
        return

    cond_removal_skills = [
        "Mend_Body_and_Soul", "Dismiss_Condition", "Mend_Condition",
        "Smite_Condition", "Purge_Conditions", "Mend_Ailment",
        "Its_Just_a_Flesh_Wound", "Blessed_Light"
    ]

    for skill_id in map(Skill.GetID, cond_removal_skills):
        result = Helper.smartcast_hero_skill(skill_id=skill_id)
        if result:
            execute_hero_skill(*result)
            break

def smart_vigorous():
    if Party.GetHeroCount() == 0:
        return
    if not Helper.can_execute_with_delay("smart_vigorous", 1000):
        return

    player_id = Player.GetAgentID()
    if not Helper.is_agent_alive(player_id):
        return
    if not Helper.is_melee_class() or not Helper.holds_melee_weapon():
        return

    result = Helper.smartcast_hero_skill(
        skill_id=Skill.GetID("Vigorous_Spirit"),
        min_enemies=2,
        enemy_range_check=Helper.get_nearby_range(),
        effect_check=True,
        distance_check_range=Helper.get_spell_cast_range(),
        allow_out_of_combat=False,
        min_energy_perc=0.25
    )

    if result:
        execute_hero_skill(*result)

def smart_splinter():
    if Party.GetHeroCount() == 0:
        return
    if not Helper.can_execute_with_delay("smart_splinter", 1000):
        return

    player_id = Player.GetAgentID()
    if not Helper.is_agent_alive(player_id):
        return
    if not Helper.is_melee_class() or not Helper.holds_melee_weapon():
        return

    result = Helper.smartcast_hero_skill(
        skill_id=Skill.GetID("Splinter_Weapon"),
        min_enemies=2,
        enemy_range_check=Helper.get_spirit_range(),
        effect_check=True,
        distance_check_range=Helper.get_spell_cast_range(),
        allow_out_of_combat=False,
        min_energy_perc=0.25
    )

    if result:
        execute_hero_skill(*result)

def smart_honor():
    if Party.GetHeroCount() == 0:
        return
    if not Helper.can_execute_with_delay("smart_honor", 1000):
        return

    player_id = Player.GetAgentID()
    if not Helper.is_agent_alive(player_id):
        return
    if not Helper.is_melee_class() or not Helper.holds_melee_weapon():
        return

    result = Helper.smartcast_hero_skill(
        skill_id=Skill.GetID("Strength_of_Honor"),
        min_enemies=0,
        enemy_range_check=Helper.get_spell_cast_range(),
        effect_check=True,
        distance_check_range=Helper.get_spell_cast_range(),
        allow_out_of_combat=True,
        min_energy_perc=0.25
    )

    if result:
        execute_hero_skill(*result)

def smart_life_bond():
    if Party.GetHeroCount() == 0:
        return
    if not Helper.can_execute_with_delay("smart_life_bond", 1000):
        return

    player_id = Player.GetAgentID()
    if not Helper.is_agent_alive(player_id):
        return
    if not Helper.is_melee_class() or not Helper.holds_melee_weapon():
        return

    result = Helper.smartcast_hero_skill(
        skill_id=Skill.GetID("Life_Bond"),
        min_enemies=0,
        enemy_range_check=Helper.get_spell_cast_range(),
        effect_check=True,
        distance_check_range=Helper.get_spell_cast_range(),
        allow_out_of_combat=True,
        min_energy_perc=0.25
    )

    if result:
        execute_hero_skill(*result)

def smart_dark_aura():
    if Party.GetHeroCount() == 0:
        return
    if not Helper.can_execute_with_delay("smart_dark_aura", 1000):
        return

    player_id = Player.GetAgentID()
    if not Helper.is_agent_alive(player_id):
        return
    
    # Only cast on Necromancer primary players
    primary, _ = Agent.GetProfessionNames(player_id)
    if primary != "Necromancer":
        return

    masochism_id = Skill.GetID("Masochism")
    dark_aura_id = Skill.GetID("Dark_Aura")
    
    # Get heroes with Dark Aura skill
    heroes_with_dark_aura = Helper.get_heroes_with_skill(dark_aura_id)
    if not heroes_with_dark_aura:
        return
    
    # Check the first hero with Dark Aura
    hero_info = heroes_with_dark_aura[0]
    hero_index = hero_info["hero_index"]
    hero_id = Party.Heroes.GetHeroAgentIDByPartyPosition(hero_index)
    
    if not hero_id or not Helper.is_agent_alive(hero_id):
        return
    
    # Check if the hero has Masochism active on themselves
    if not Helper.check_for_effects(hero_id, [masochism_id]):
        # Cast Masochism on the hero itself
        result = Helper.smartcast_hero_skill(
            skill_id=masochism_id,
            min_enemies=0,
            enemy_range_check=Helper.get_spell_cast_range(),
            effect_check=True,
            hero_target=True,  # Cast on the hero itself
            distance_check_range=Helper.get_spell_cast_range(),
            allow_out_of_combat=True,
            min_energy_perc=0.25
        )
        if result:
            execute_hero_skill(*result)
            return  # Wait for Masochism to be applied before casting Dark Aura
    
    # Only cast Dark Aura if Masochism is already active on the hero
    result = Helper.smartcast_hero_skill(
        skill_id=dark_aura_id,
        min_enemies=0,
        enemy_range_check=Helper.get_spell_cast_range(),
        effect_check=True,
        distance_check_range=Helper.get_spell_cast_range(),
        allow_out_of_combat=True,
        min_energy_perc=0.25
    )

    if result:
        execute_hero_skill(*result)

def smart_st():
    if Party.GetHeroCount() == 0:
        return
    if not Helper.can_execute_with_delay("smart_st", 1000):
        return
    if not Helper.is_fighting():
        return

    spirit_range = Helper.get_spirit_range() + 200
    spell_range = Helper.get_spell_cast_range()

    for skill_name in ["Shelter", "Union"]:
        result = Helper.smartcast_hero_skill(
            skill_id=Skill.GetID(skill_name),
            min_enemies=3,
            enemy_range_check=spell_range,
            hero_target=True,
            effect_check=True,
            distance_check_range=spirit_range
        )
        if result:
            execute_hero_skill(*result)

def smart_sos():
    if Party.GetHeroCount() == 0:
        return
    if not Helper.can_execute_with_delay("smart_sos", 1000):
        return

    player_pos = Player.GetXY()
    enemies_in_range = Helper.count_enemies_in_range(Helper.get_spell_cast_range(), player_pos)
    sos_spirits = [4229, 4230, 4231]
    spirits_in_range = Helper.count_spirits_in_range(sos_spirits, Helper.get_spell_cast_range() + 200)

    needs_sos = (
        (enemies_in_range > 6 and spirits_in_range < 3) or
        (enemies_in_range > 4 and spirits_in_range < 2) or
        (enemies_in_range > 2 and spirits_in_range < 1)
    )

    if not needs_sos or not (Helper.is_fighting() or Helper.can_fight()):
        return

    result = Helper.smartcast_hero_skill(
        skill_id=Skill.GetID("Signet_of_Spirits"),
        min_enemies=0,
        enemy_range_check=Helper.get_spell_cast_range(),
        hero_target=True,
        distance_check_range=Helper.get_spell_cast_range() + 200
    )

    if result:
        execute_hero_skill(*result)

def smart_bip():
    if Party.GetHeroCount() == 0:
        return
    if not Helper.can_execute_with_delay("smart_bip", 500):
        return

    player_id = Player.GetAgentID()
    if not Helper.is_agent_alive(player_id):
        return

    bip_id = Skill.GetID("Blood_is_Power")
    if Helper.check_for_effects(player_id, [bip_id]):
        return

    energy = Helper.get_energy_data()
    if energy.regen > 0.03:
        return

    prof, _ = Agent.GetProfessionNames(player_id)
    thresholds = {
        "Warrior": (25, 0.70), "Ranger": (25, 0.60), "Monk": (30, 0.50),
        "Necromancer": (30, 0.50), "Mesmer": (30, 0.50), "Elementalist": (40, 0.40),
        "Assassin": (25, 0.60), "Ritualist": (30, 0.50), "Paragon": (25, 0.70),
        "Dervish": (25, 0.50),
    }

    if prof not in thresholds:
        return

    min_energy, min_percent = thresholds[prof]
    if energy.current >= min_energy and energy.percentage > min_percent:
        return

    result = Helper.smartcast_hero_skill(
        skill_id=bip_id,
        min_enemies=0,
        enemy_range_check=Helper.get_spell_cast_range(),
        effect_check=True,
        cast_target_id=player_id,
        distance_check_range=Helper.get_spell_cast_range() + 200,
        allow_out_of_combat=True,
        min_health_perc=0.5
    )

    if result:
        execute_hero_skill(*result)

def smart_healing():
    if Party.GetHeroCount() == 0:
        return
    if not Helper.can_execute_with_delay("smart_healing", 500):
        return

    # Get allies (party members, heroes, henchmen) - excludes minions
    ally_array = AgentArray.GetAllyArray()
    if not ally_array:
        return
    
    # Add pets to ally array
    pet_array = AgentArray.GetSpiritPetArray()
    if pet_array:
        # Filter out spirits, keep only pets
        pet_array = [agent_id for agent_id in pet_array if not Agent.IsSpawned(agent_id)]
        ally_array = ally_array + pet_array
    
    spell_range = Helper.get_spell_cast_range()
    player_pos = Player.GetXY()
    
    # Filter allies by distance and alive status
    valid_allies = []
    for agent_id in ally_array:
        if not Helper.is_agent_alive(agent_id):
            continue
        distance = Utils.Distance(player_pos, Agent.GetXY(agent_id))
        if distance > spell_range:
            continue
        health = Helper.get_hp_data(agent_id)
        if health.percentage >= 0.90:
            continue
        valid_allies.append((agent_id, health.percentage))
    
    if not valid_allies:
        return
    
    # Sort by health percentage (lowest first)
    valid_allies.sort(key=lambda x: x[1])
    target_id = valid_allies[0][0]
    
    # Common monk and ritualist healing skills to try in order of priority
    healing_skills = [
        # Monk healing skills
        "Word_of_Healing",
        "Patient_Spirit",
        "Dwaynas_Kiss",
        "Healing_Burst",
        "Healing_Touch",
        "Signet_of_Rejuvenation",
        "Orison_of_Healing",
        "Heal_Other",
        "Healing_Breeze",
        # Ritualist healing skills
        "Mend_Body_and_Soul",
        "Spirit_Light",
        "Soothing_Memories",
        "Weapon_of_Remedy",
        "Vital_Weapon"
    ]
    
    for skill_name in healing_skills:
        skill_id = Skill.GetID(skill_name)
        if skill_id == 0:
            continue
            
        # Check if any hero has this skill and can cast it
        result = Helper.smartcast_hero_skill(
            skill_id=skill_id,
            min_enemies=0,
            enemy_range_check=spell_range,
            effect_check=False,
            cast_target_id=target_id,
            distance_check_range=spell_range + 200,
            allow_out_of_combat=True,
            min_energy_perc=0.2
        )
        
        if result:
            execute_hero_skill(*result)
            break  # Cast only one heal per cycle

def smart_incoming_fallback():
    """Force heroes to use Incoming! and Fall Back! regardless of Essence of Celerity being active."""
    if Party.GetHeroCount() == 0:
        return
    if not Helper.can_execute_with_delay("smart_incoming_fallback", 500):
        return

    player_id = Player.GetAgentID()
    if not Helper.is_agent_alive(player_id):
        return

    # Only use these shouts out of combat
    if Helper.count_enemies_in_range(Helper.get_spell_cast_range(), Player.GetXY()) > 0:
        return

    incoming_id = Skill.GetID("Incoming")
    fallback_id = Skill.GetID("Fall_Back")

    # Both shouts are party-wide: if the player already has either one active, no cast needed
    if Helper.check_for_effects(player_id, [incoming_id, fallback_id]):
        return

    # Try Incoming first, then Fall Back — whichever a hero has ready
    for skill_id in [incoming_id, fallback_id]:
        result = Helper.smartcast_hero_skill(
            skill_id=skill_id,
            min_enemies=0,
            effect_check=False,          # combined check already done above
            hero_target=True,            # shout is Self-targeting, cast on the hero itself
            distance_check_range=Helper.get_spell_cast_range() + 200,
            allow_out_of_combat=True,
        )
        if result:
            execute_hero_skill(*result)
            return

# Track which hero skills have been disabled
last_follow_state = None
last_player_position = None
follow_toggled_time = 0
last_movement_time = 0
last_autoattack_unfollow_time = 0
is_waiting_to_unfollow = False
is_following_disabled_due_to_idle = False
is_following_disabled_due_to_attack = False
is_following_active = False
def should_unfollow_due_to_idle(current_position, min_moving_time):
    global last_player_position, last_movement_time
    if not last_player_position:
        return False
    return current_position == last_player_position and (time.time() - last_movement_time) >= min_moving_time


def smart_hero_follow():
    global is_following_active, last_logged_follow_delay, last_follow_state

    if not is_following_active:
        Helper.log_event(message=f"Heroes on follow every ({widget_config.follow_delay}ms)")

    action_queue.add_action(Helper.flag_heroes)
    is_following_active = True
    last_logged_follow_delay = widget_config.follow_delay
    last_follow_state = widget_config.smart_follow_toggled

    if widget_config.hero_behaviour != Helper.HERO_BEHAVIOUR_AVOID_COMBAT:
        widget_config.last_known_hero_behaviour = widget_config.hero_behaviour
        set_hero_behaviour(Helper.HERO_BEHAVIOUR_AVOID_COMBAT)
        widget_config.hero_behaviour = Helper.HERO_BEHAVIOUR_AVOID_COMBAT


def smart_hero_unfollow():
    global is_following_active, last_follow_state

    if not is_following_active:
        return

    action_queue.add_action(Helper.unflag_heroes)
    Helper.log_event(message="Heroes have stopped following")

    if widget_config.hero_behaviour != widget_config.last_known_hero_behaviour:
        set_hero_behaviour(widget_config.last_known_hero_behaviour)
        widget_config.hero_behaviour = widget_config.last_known_hero_behaviour

    is_following_active = False
    last_follow_state = widget_config.smart_follow_toggled


def update_hero_follow_state():
    global last_follow_state, last_player_position, last_movement_time
    global follow_toggled_time, last_autoattack_unfollow_time
    global is_waiting_to_unfollow, is_following_disabled_due_to_idle
    global is_following_disabled_due_to_attack, is_following_active

    if not Helper.can_execute_with_delay("update_follow_state", 500):
        return

    now = time.time()
    current_pos = Player.GetXY()
    enemies_nearby = Helper.count_enemies_in_range(Helper.get_spell_cast_range(), current_pos)
    idle_threshold = 2 if enemies_nearby > 0 else 5

    if widget_config.smart_follow_toggled and last_follow_state != widget_config.smart_follow_toggled:
        follow_toggled_time = now

    if Helper.is_auto_attacking():
        smart_hero_unfollow()
        is_following_disabled_due_to_attack = True
        last_autoattack_unfollow_time = now
        return

    if now - last_autoattack_unfollow_time < 8:
        return

    is_following_disabled_due_to_attack = False

    if not widget_config.smart_follow_toggled:
        smart_hero_unfollow()
        return

    if should_unfollow_due_to_idle(current_pos, idle_threshold):
        if now - follow_toggled_time >= idle_threshold and not is_waiting_to_unfollow:
            smart_hero_unfollow()
            is_waiting_to_unfollow = True
            is_following_disabled_due_to_idle = True
            return

    if current_pos != last_player_position:
        last_movement_time = now
        is_waiting_to_unfollow = False
        if is_following_disabled_due_to_idle:
            smart_hero_follow()
            is_following_disabled_due_to_idle = False

    if not is_following_disabled_due_to_idle and not is_following_disabled_due_to_attack:
        smart_hero_follow()

    last_player_position = current_pos
    last_follow_state = widget_config.smart_follow_toggled
    
def set_hero_behaviour(behaviour):
    action_queue.add_action(lambda: Helper.set_heroes_behaviour(behaviour))

    behaviour_str = {
        Helper.HERO_BEHAVIOUR_FIGHT: "Fight",
        Helper.HERO_BEHAVIOUR_GUARD: "Guard",
        Helper.HERO_BEHAVIOUR_AVOID_COMBAT: "Avoid"
    }.get(behaviour, f"Unknown ({behaviour})")

    Helper.log_event(message=f"Set all heroes to {behaviour_str}.")


def colored_button(label: str, button_color=0, hovered_color=0, active_color=0, width=0, height=0):
    PyImGui.push_style_color(PyImGui.ImGuiCol.Button, Utils.ColorToTuple(button_color))
    PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonHovered, Utils.ColorToTuple(hovered_color))
    PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonActive, Utils.ColorToTuple(active_color))

    clicked = PyImGui.button(label, width, height)

    PyImGui.pop_style_color(3)
    return clicked

def color_toggle_button(label: str, state: bool, button_color=0, hovered_color=0, active_color=0, width=0, height=0):
    icon = IconsFontAwesome5.ICON_CHECK_CIRCLE if state else IconsFontAwesome5.ICON_CIRCLE
    return colored_button(f"{icon}##{label}", active_color if state else button_color, active_color, active_color, width, height)

def toggle_config_value(label: str, attr: str, width: int = 0, height: int = 25, tooltip: str = ""):
    curr = getattr(widget_config, attr)
    toggled = ImGui.toggle_button(label, curr, width, height)

    if toggled != curr:
        setattr(widget_config, attr, toggled)
        Helper.log_event(message=f"{label} {'Enabled' if toggled else 'Disabled'}")

    if tooltip and PyImGui.is_item_hovered():
        PyImGui.set_tooltip(tooltip)

def draw_tab_follow(config):
    PyImGui.text("Follow Delay (ms)")
    config.follow_delay = PyImGui.slider_int("##follow_delay_slider", config.follow_delay, 500, 2000)
    PyImGui.same_line(0, 5)
    config.follow_delay = PyImGui.input_int("##hidden_label", config.follow_delay)
    config.follow_delay = max(500, min(2000, config.follow_delay))
    
def draw_tab_smart_skills(config):
    Helper.create_and_update_checkbox("Smart Blood is Power", "smart_bip_enabled", tooltip_text="Automatically cast Blood is Power on player when needed.")
    PyImGui.same_line(0.0, 21)
    Helper.create_and_update_checkbox("Smart Signet of Spirits", "smart_sos_enabled", tooltip_text="Automatically casts Signet of Spirits when necessary.")

    Helper.create_and_update_checkbox("Smart Soul Twisting", "smart_st_enabled", tooltip_text="Automatically casts Shelter and Union based on combat conditions.")
    PyImGui.same_line(0.0, 31)
    Helper.create_and_update_checkbox("Smart Strength of Honor", "smart_honor_enabled", tooltip_text="[DISABLE HERO CASTING] Maintains Honor on melee player.")

    Helper.create_and_update_checkbox("Smart Life Bond", "smart_life_bond_enabled", tooltip_text="[DISABLE HERO CASTING] Maintains Life Bond on melee player.")
    PyImGui.same_line(0.0, 60)
    Helper.create_and_update_checkbox("Smart Dark Aura", "smart_dark_aura_enabled", tooltip_text="Hero maintains Masochism on itself, then Dark Aura on Necromancer player.")

    Helper.create_and_update_checkbox("Smart Splinter Weapon", "smart_splinter_enabled", tooltip_text="Casts Splinter on melee player in combat.")
    PyImGui.same_line(0.0, 10)
    Helper.create_and_update_checkbox("Smart Vigorous Spirit", "smart_vigorous_enabled", tooltip_text="Casts Vigorous Spirit on melee player in combat.")
    
    Helper.create_and_update_checkbox("Smart Healing", "smart_healing_enabled", tooltip_text="Monk/Rit heals lowest health ally/pet (excludes minions).")
    PyImGui.same_line(0.0, 10)
    Helper.create_and_update_checkbox("Smart Incoming/Fall Back", "smart_incoming_fallback_enabled", tooltip_text="Hero uses Incoming! and Fall Back! even when Essence of Celerity is active.")

def draw_tab_condition_cleanse(config):
    if not PyImGui.collapsing_header("Condition Removal", PyImGui.TreeNodeFlags.DefaultOpen):
        return

    PyImGui.text_wrapped("Assign Prio Cleanse Conditions to Melee, Caster, or Both\n(Leave blank to keep default priority):")

    if PyImGui.begin_table("ConditionTable", 4, PyImGui.TableFlags.Borders | PyImGui.TableFlags.RowBg | PyImGui.TableFlags.SizingStretchSame):
        for header in ["Condition", "Melee", "Caster", "Both"]:
            PyImGui.table_setup_column(header)
        PyImGui.table_headers_row()

        changed = False
        for condition, data in config.conditions.items():
            PyImGui.table_next_row()

            PyImGui.table_next_column()
            PyImGui.text(condition.replace("_", " "))

            PyImGui.table_next_column()
            new_melee = PyImGui.checkbox(f"##melee_{condition}", data["melee"])

            PyImGui.table_next_column()
            new_caster = PyImGui.checkbox(f"##caster_{condition}", data["caster"])

            PyImGui.table_next_column()
            new_both = PyImGui.checkbox(f"##both_{condition}", data["both"])

            prev = (data["melee"], data["caster"], data["both"])

            if new_melee and not data["melee"]:
                data.update(melee=True, caster=False, both=False)
            elif new_caster and not data["caster"]:
                data.update(melee=False, caster=True, both=False)
            elif new_both and not data["both"]:
                data.update(melee=False, caster=False, both=True)
            elif not new_melee and not new_caster and not new_both:
                data.update(melee=False, caster=False, both=False)

            changed |= (prev != (data["melee"], data["caster"], data["both"]))

        PyImGui.end_table()
        if changed:
            config.save()

    if PyImGui.button("Set Recommended Defaults", height=25):
        defaults = {
            "Blind": {"melee": True},
            "Weakness": {"melee": True},
            "Dazed": {"caster": True},
            "Crippled": {"both": True},
        }
        for cond, values in defaults.items():
            if cond in config.conditions:
                config.conditions[cond].update(melee=False, caster=False, both=False)
                config.conditions[cond].update(values)
        config.save()

    PyImGui.same_line(0.0, -1)
    button_width = int(PyImGui.get_content_region_avail()[0])
    toggle_config_value("Enable Condition Cleanse", "smart_con_cleanse_toggled", button_width, 25, "Toggle automatic condition cleansing")



def render_hex_group(title, hex_list):
    if not hex_list:
        return

    if PyImGui.collapsing_header(f"Hexes to be priority removed from {title}", PyImGui.TreeNodeFlags.DefaultOpen):
        PyImGui.columns(2, f"{title}_hexes", False)
        midpoint = (len(hex_list) + 1) // 2
        for i, hex_name in enumerate(hex_list):
            PyImGui.text(f"- {hex_name.replace('_', ' ')}")
            if i == midpoint - 1:
                PyImGui.next_column()
        PyImGui.columns(1, "hex_columns", False)

def render_user_hex_editor(config):
    if not PyImGui.collapsing_header("Hexes added by user", PyImGui.TreeNodeFlags.DefaultOpen):
        return

    PyImGui.set_tooltip("These are hexes you manually added. Red circle to remove")

    for hex_name in config.hexes_user:
        PyImGui.text(f"- {hex_name.replace('_', ' ')}")
        PyImGui.push_style_color(PyImGui.ImGuiCol.Button, (0.8, 0.0, 0.0, 1.0))
        PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonHovered, (1.0, 0.2, 0.2, 1.0))
        PyImGui.push_style_color(PyImGui.ImGuiCol.Text, (1.0, 1.0, 1.0, 1.0))
        PyImGui.same_line(0, 5)
        if PyImGui.button(f"##{hex_name}", 10, 10):
            config.hexes_user.remove(hex_name.replace(" ", "_"))
            config.save_hexes()
            Helper.log_event(message=f"Removed {hex_name} from user hex list")
        PyImGui.pop_style_color(3)

    PyImGui.text("Add a hex spell:")
    config.user_hex_input = PyImGui.input_text("##user_hex_input", config.user_hex_input)
    PyImGui.same_line(0, 5)

    if PyImGui.button("Add Hex", int(PyImGui.get_content_region_avail()[0])):
        user_input = config.user_hex_input.strip()
        formatted = Helper.format_spell_title_case(user_input)

        if not formatted:
            Helper.log_event(message="Input was empty. Skipping.")
        elif formatted not in [h.lower() for h in config.hexes_user]:
            config.hexes_user.append(formatted)
            config.save_hexes()
            Helper.log_event(message=f"Added {formatted} to the user hex list.")
        else:
            Helper.log_event(message=f"{formatted} is already in the list. Skipping.")

        config.user_hex_input = ""

def draw_tab_hex_removal(config):
    if not PyImGui.collapsing_header("Hex Removal", PyImGui.TreeNodeFlags.DefaultOpen):
        return

    PyImGui.text_wrapped("These hexes will be prioritized for removal.")
    PyImGui.set_tooltip("Hexes in each list will be removed automatically when detected.")

    render_hex_group("Melee", config.hexes_melee)
    render_hex_group("Casters", config.hexes_caster)
    render_hex_group("All", config.hexes_all)
    render_hex_group("Paragons", config.hexes_paragon)
    render_user_hex_editor(config)

    available_width = PyImGui.get_content_region_avail()[0]
    button_width = int(available_width)

    toggle_config_value("Enable Hex Cleanse", "smart_hex_cleanse_toggled", button_width, 25, "Toggle automatic hex removal")


def draw_tab_interrupt(config):
    PyImGui.text_wrapped("Manage skills that heroes will interrupt.")

    if PyImGui.collapsing_header("Skills To Interrupt", PyImGui.TreeNodeFlags.DefaultOpen):
        for skill in config.skills_to_rupt:
            PyImGui.text(f"- {skill.replace('_', ' ')}")
            PyImGui.same_line(0, 5)
            if PyImGui.button(f"##Remove_{skill}", 10, 10):
                config.skills_to_rupt.remove(skill)
                config.save_skills_to_rupt()
                Helper.log_event(message=f"Removed {skill} from interrupt list")

    config.user_skill_input = PyImGui.input_text("##user_skill_input", config.user_skill_input)
    PyImGui.same_line(0, 5)

    button_width = int(PyImGui.get_content_region_avail()[0])
    if PyImGui.button("Add Skill", button_width):
        input_str = config.user_skill_input.strip()
        formatted = Helper.format_spell_title_case(input_str)

        if not formatted:
            Helper.log_event(message="Input was empty. Skipping.")
        elif formatted in config.skills_to_rupt:
            Helper.log_event(message=f"{formatted} is already in the interrupt list.")
        else:
            config.skills_to_rupt.append(formatted)
            config.save_skills_to_rupt()
            Helper.log_event(message=f"Added {formatted} to the interrupt list.")

        config.user_skill_input = ""

    button_width = int(PyImGui.get_content_region_avail()[0])
    toggle_config_value("Enable Hero Interrupt", "smart_interrupt_toggled", button_width, 25, "Toggle automatic hero interrupts")

def draw_config_tabs(widget_config):
    if not PyImGui.begin_tab_bar("Hero Helper Config Tabs"):
        return

    if PyImGui.begin_tab_item("Follow"):
        draw_tab_follow(widget_config)
        PyImGui.end_tab_item()

    if PyImGui.begin_tab_item("Smart Skills"):
        draw_tab_smart_skills(widget_config)
        PyImGui.end_tab_item()

    if PyImGui.begin_tab_item("Condition Cleanse"):
        draw_tab_condition_cleanse(widget_config)
        PyImGui.end_tab_item()

    if PyImGui.begin_tab_item("Hex Removal"):
        draw_tab_hex_removal(widget_config)
        PyImGui.end_tab_item()

    if PyImGui.begin_tab_item("Smart Interrupt"):
        draw_tab_interrupt(widget_config)
        PyImGui.end_tab_item()

    PyImGui.end_tab_bar()

def _render_behavior_buttons():
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


def _render_toggle_row(toggles):
    for i, (label, config_key, tooltip) in enumerate(toggles):
        state = getattr(widget_config, config_key)
        if color_toggle_button(label, state,
                               Utils.RGBToColor(26, 26, 26, 225),
                               Utils.RGBToColor(255, 255, 255, 25),
                               Utils.RGBToColor(0, 170, 255, 125)):
            new_state = not state
            setattr(widget_config, config_key, new_state)
            Helper.log_event(message=f"{label} {'Enabled' if new_state else 'Disabled'}")

        ImGui.show_tooltip(tooltip)
        if i != len(toggles) - 1:
            PyImGui.same_line(0, 1)


def draw_options_window():
    if not PyImGui.begin_child("Console", size=(280.0, 50.0), border=False, flags=0):
        return

    for log in reversed(Helper.console_logs):
        PyImGui.text(log)
    PyImGui.end_child()
    PyImGui.separator()

    _render_behavior_buttons()
    PyImGui.separator()

    available_width = PyImGui.get_content_region_avail()[0]
    button_width = int(available_width)

    new_state = ImGui.toggle_button("Follow", widget_config.smart_follow_toggled, button_width, 30)
    if new_state != widget_config.smart_follow_toggled:
        Helper.log_event(message=f"Hero Follow {'Enabled' if new_state else 'Disabled'}")
    widget_config.smart_follow_toggled = new_state

    _render_toggle_row([
        ("Smart BiP", "smart_bip_enabled", "Smart BiP"),
        ("Smart SoS", "smart_sos_enabled", "Smart SoS"),
        ("Smart ST", "smart_st_enabled", "Smart ST"),
        ("Smart SoH", "smart_honor_enabled", "Smart SoH"),
        ("Smart LB", "smart_life_bond_enabled", "Smart Life Bond"),
        ("Smart SW", "smart_splinter_enabled", "Smart SW"),
        ("Smart VS", "smart_vigorous_enabled", "Smart VS"),
        ("Smart CC", "smart_con_cleanse_toggled", "Condition Cleanse"),
        ("Smart HR", "smart_hex_cleanse_toggled", "Hex Removal"),
        ("Smart Int", "smart_interrupt_toggled", "Smart Interrupt"),
        ("Smart I/F", "smart_incoming_fallback_enabled", "Smart Incoming/Fall Back"),
    ])

def draw_window():
    PyImGui.set_next_window_size(300, 200)

    if not PyImGui.begin(window_module.window_name, window_module.window_flags | PyImGui.WindowFlags.NoScrollbar):
        return

    PyImGui.begin_group()
    draw_options_window()
    PyImGui.end()

PARTY_WINDOW_HASH = 3332025202
PARTY_WINDOW_FRAME_OUTPOST_OFFSETS = [1]
PARTY_WINDOW_FRAME_EXPLORABLE_OFFSETS = [0]

class Tabs(Enum):
    party_default = 1
    options_panel = 2
    configs_panel = 3

selected_tab:Tabs = Tabs.party_default

def draw_frame_content(content_frame_id):
    global selected_tab

    if selected_tab == Tabs.party_default:
        return

    left, top, right, bottom = UIManager.GetFrameCoords(content_frame_id)
    width, height = right - left, bottom - top

    UIManager().DrawFrame(content_frame_id, Utils.RGBToColor(0, 0, 0, 255))

    flags = (
        PyImGui.WindowFlags.NoCollapse |
        PyImGui.WindowFlags.NoTitleBar |
        PyImGui.WindowFlags.NoResize |
        PyImGui.WindowFlags.AlwaysHorizontalScrollbar |
        PyImGui.WindowFlags.AlwaysVerticalScrollbar
    )

    PyImGui.push_style_var(ImGui.ImGuiStyleVar.WindowRounding, 0.0)
    PyImGui.set_next_window_pos(left, top)
    PyImGui.set_next_window_size(width, height)

    if not PyImGui.begin("##help_framed_content", True, flags):
        return

    if selected_tab == Tabs.options_panel:
        draw_options_window()
        Helper.create_and_update_checkbox("Old Window", "floating_window_enabled", tooltip_text="enable the floating")
    elif selected_tab == Tabs.configs_panel:
        draw_config_tabs(widget_config)

    PyImGui.end()

def draw_embedded_window():
    global selected_tab
    parent_frame_id = UIManager.GetFrameIDByHash(PARTY_WINDOW_HASH)
    if parent_frame_id == 0:
        return
    outpost_content_frame_id = UIManager.GetChildFrameID( PARTY_WINDOW_HASH, PARTY_WINDOW_FRAME_OUTPOST_OFFSETS)
    explorable_content_frame_id = UIManager.GetChildFrameID( PARTY_WINDOW_HASH, PARTY_WINDOW_FRAME_EXPLORABLE_OFFSETS) 
    
    if Map.IsMapReady() and Map.IsExplorable():
        content_frame_id = explorable_content_frame_id
    else:
        content_frame_id = outpost_content_frame_id
    
    left, top, right, bottom = UIManager.GetFrameCoords(parent_frame_id)
    sidebar_width = 30
    sidebar_height = bottom - top

    flags = ImGui.PushTransparentWindow()
    PyImGui.set_next_window_pos(left - sidebar_width - 2, top)
    PyImGui.set_next_window_size(sidebar_width, sidebar_height)

    if PyImGui.begin("HeroHelper Vertical Tabs", True, flags):
        
        if PyImGui.button(IconsFontAwesome5.ICON_BORDER_NONE + "##cleartab", -1, 0):  # -1 width, 0 height auto
            selected_tab = Tabs.party_default
        if PyImGui.button(IconsFontAwesome5.ICON_CHECK_SQUARE + "##optiontab", -1, 0):
            selected_tab = Tabs.options_panel
        if PyImGui.button(IconsFontAwesome5.ICON_LIST_OL + "##configtab", -1, 0):
            selected_tab = Tabs.configs_panel
        PyImGui.end()
    ImGui.PopTransparentWindow()
    draw_frame_content(content_frame_id)

def configure():
    global widget_config, config_module, ini_handler
       
    if config_module.first_run:
        PyImGui.set_next_window_size(config_module.window_size[0], config_module.window_size[1])
        PyImGui.set_next_window_pos(config_module.window_pos[0], config_module.window_pos[1])
        config_module.first_run = False
        
    if PyImGui.begin(config_module.window_name, config_module.window_flags):
        draw_config_tabs(widget_config)
                

        end_pos = PyImGui.get_window_pos()
        if end_pos[0] != config_module.window_pos[0] or end_pos[1] != config_module.window_pos[1]:
            config_module.window_pos = (int(end_pos[0]), int(end_pos[1]))
            ini_handler.write_key(MODULE_NAME + " Config", "config_x", str(int(end_pos[0])))
            ini_handler.write_key(MODULE_NAME + " Config", "config_y", str(int(end_pos[1])))   

    PyImGui.end()
    
def tooltip():
    PyImGui.begin_tooltip()

    # Title
    title_color = Color(255, 200, 100, 255)
    ImGui.push_font("Regular", 20)
    PyImGui.text_colored("HeroHelper", title_color.to_tuple_normalized())
    ImGui.pop_font()
    PyImGui.spacing()
    PyImGui.separator()

    # Description
    PyImGui.text("An advanced reactive combat assistant that enhances Guild Wars heroes")
    PyImGui.text("with high-level logic for interrupts, cleansing, and elite skill")
    PyImGui.text("management. It automates critical support roles for the party.")
    PyImGui.spacing()

    # Features
    PyImGui.text_colored("Features:", title_color.to_tuple_normalized())
    PyImGui.bullet_text("Smart Interrupt: High-speed automated interrupts on enemy casters")
    PyImGui.bullet_text("Condition/Hex Removal: Priority-based cleansing of dangerous debuffs")
    PyImGui.bullet_text("Elite Management: Optimized logic for BiP, Soul Twisting, and SoS")
    PyImGui.bullet_text("Buff Maintenance: Automated upkeep of Splinter Weapon, Honor, and Life Bond")
    PyImGui.bullet_text("Smart Healing: Ally/Pet healing that excludes minions from targeting")
    PyImGui.bullet_text("Action Queue: Sequential skill execution to prevent animation canceling")
    PyImGui.bullet_text("Status HUD: Embedded window showing real-time hero state and toggles")

    PyImGui.spacing()
    PyImGui.separator()
    PyImGui.spacing()

    # Credits
    PyImGui.text_colored("Credits:", title_color.to_tuple_normalized())
    PyImGui.bullet_text("Developed by Torx")
    PyImGui.bullet_text("Contributors: Apo, TyanNuttall, Wick-Divinus, Greg-76")

    PyImGui.end_tooltip()

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
            if widget_config.smart_life_bond_enabled:
                smart_life_bond()
            if widget_config.smart_dark_aura_enabled:
                smart_dark_aura()
            if widget_config.smart_st_enabled:   
                smart_st()
            if widget_config.smart_bip_enabled:
                smart_bip()   
            if widget_config.smart_sos_enabled:
                smart_sos()
            if widget_config.smart_healing_enabled:
                smart_healing()
            if widget_config.smart_incoming_fallback_enabled:
                smart_incoming_fallback()

        if widget_config.floating_window_enabled:
            draw_window()
        draw_embedded_window()

        if not action_queue.is_empty():
            action_queue.execute_next()
        
        if any(getattr(widget_config, key) != widget_config._cache[key] for key in widget_config.tracked_keys):
            widget_config.save()   
    
    return True

if __name__ == "__main__":
    main()