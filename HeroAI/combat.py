import Py4GW
from Py4GWCoreLib import Player, GLOBAL_CACHE, SpiritModelID, Timer, Agent, Routines, Range, Allegiance, AgentArray, Utils, CombatEvents, ConsoleLog, ThrottledTimer
from Py4GWCoreLib import Weapon, Effects
from Py4GWCoreLib.enums import SPIRIT_BUFF_MAP, ModelID
from .custom_skill import CustomSkillClass
from .targeting import TargetLowestAlly, TargetLowestAllyEnergy, TargetClusteredEnemy, TargetLowestAllyCaster, TargetLowestAllyMartial, TargetLowestAllyMelee, TargetLowestAllyRanged, GetAllAlliesArray
from .targeting import GetEnemyAttacking, GetEnemyCasting, GetEnemyCastingSpell, GetEnemyInjured, GetEnemyConditioned, GetEnemyHealthy
from .targeting import GetEnemyHexed, GetEnemyDegenHexed, GetEnemyEnchanted, GetEnemyMoving, GetEnemyKnockedDown
from .targeting import GetEnemyBleeding, GetEnemyPoisoned, GetEnemyCrippled
from .types import SkillNature, Skilltarget, SkillType
from .constants import MAX_NUM_PLAYERS
from typing import Optional


MAX_SKILLS = 8
custom_skill_data_handler = CustomSkillClass()

# Alcohol items for Drunken Master optimization (+1 drunk level items)
ALCOHOL_MODEL_IDS = [
    ModelID.Dwarven_Ale.value,
    ModelID.Hunters_Ale.value,
    ModelID.Bottle_Of_Rice_Wine.value,
    ModelID.Bottle_Of_Vabbian_Wine.value,
    ModelID.Bottle_Of_Juniberry_Gin.value,
    ModelID.Shamrock_Ale.value,
    ModelID.Hard_Apple_Cider.value,
    ModelID.Eggnog.value,
    ModelID.Vial_Of_Absinthe.value,
    ModelID.Witchs_Brew.value,
]

#region CombatClass
class CombatClass:
    global MAX_SKILLS, custom_skill_data_handler

    class SkillData:
        def __init__(self, slot):
            self.skill_id = GLOBAL_CACHE.SkillBar.GetSkillIDBySlot(slot)  # slot is 1 based
            self.skillbar_data = GLOBAL_CACHE.SkillBar.GetSkillData(slot)  # Fetch additional data from the skill bar
            self.custom_skill_data = custom_skill_data_handler.get_skill(self.skill_id)  # Retrieve custom skill data

    def __init__(self):
        """
        Initializes the CombatClass with an empty skill set and order.
        """
        self.skills : list[CombatClass.SkillData] = []
        self.skill_order = [0] * MAX_SKILLS
        self.skill_pointer = 0
        self.in_casting_routine = False
        self.aftercast = 0
        self.aftercast_timer = Timer()
        self.aftercast_timer.Start()
        self.movement_throttle_timer = ThrottledTimer(250)
        self.ping_handler = Py4GW.PingHandler()
        self.oldCalledTarget = 0
        
        self.in_aggro = False
        self.is_targeting_enabled = False
        self.is_combat_enabled = False
        self.is_skill_enabled = []
        self.fast_casting_exists = False
        self.fast_casting_level = 0
        self.expertise_exists = False
        self.expertise_level = 0
        
        self.nearest_enemy = Routines.Agents.GetNearestEnemy(self.get_combat_distance())
        self.lowest_ally = 0
        self.lowest_ally_energy = 0
        self.nearest_npc = Routines.Agents.GetNearestNPC(Range.Spellcast.value)
        self.nearest_spirit = Routines.Agents.GetNearestSpirit(Range.Spellcast.value)
        self.lowest_minion = Routines.Agents.GetLowestMinion(Range.Spellcast.value)
        self.nearest_corpse = Routines.Agents.GetNearestCorpse(Range.Spellcast.value)
        
        self.energy_drain = GLOBAL_CACHE.Skill.GetID("Energy_Drain") 
        self.energy_tap = GLOBAL_CACHE.Skill.GetID("Energy_Tap")
        self.ether_lord = GLOBAL_CACHE.Skill.GetID("Ether_Lord")
        self.essence_strike = GLOBAL_CACHE.Skill.GetID("Essence_Strike")
        self.glowing_signet = GLOBAL_CACHE.Skill.GetID("Glowing_Signet")
        self.clamor_of_souls = GLOBAL_CACHE.Skill.GetID("Clamor_of_Souls")
        self.waste_not_want_not = GLOBAL_CACHE.Skill.GetID("Waste_Not_Want_Not")
        self.mend_body_and_soul = GLOBAL_CACHE.Skill.GetID("Mend_Body_and_Soul")
        self.grenths_balance = GLOBAL_CACHE.Skill.GetID("Grenths_Balance")
        self.deaths_retreat = GLOBAL_CACHE.Skill.GetID("Deaths_Retreat")
        self.plague_sending = GLOBAL_CACHE.Skill.GetID("Plague_Sending")
        self.plague_signet = GLOBAL_CACHE.Skill.GetID("Plague_Signet")
        self.plague_touch = GLOBAL_CACHE.Skill.GetID("Plague_Touch")
        self.golden_fang_strike = GLOBAL_CACHE.Skill.GetID("Golden_Fang_Strike")
        self.golden_fox_strike = GLOBAL_CACHE.Skill.GetID("Golden_Fox_Strike")
        self.golden_lotus_strike = GLOBAL_CACHE.Skill.GetID("Golden_Lotus_Strike")
        self.golden_phoenix_strike = GLOBAL_CACHE.Skill.GetID("Golden_Phoenix_Strike")
        self.golden_skull_strike = GLOBAL_CACHE.Skill.GetID("Golden_Skull_Strike")
        self.brutal_weapon = GLOBAL_CACHE.Skill.GetID("Brutal_Weapon")
        self.signet_of_removal = GLOBAL_CACHE.Skill.GetID("Signet_of_Removal")
        self.dwaynas_kiss = GLOBAL_CACHE.Skill.GetID("Dwaynas_Kiss")
        self.unnatural_signet = GLOBAL_CACHE.Skill.GetID("Unnatural_Signet")
        self.toxic_chill = GLOBAL_CACHE.Skill.GetID("Toxic_Chill")
        self.discord = GLOBAL_CACHE.Skill.GetID("Discord")
        self.empathic_removal = GLOBAL_CACHE.Skill.GetID("Empathic_Removal")
        self.iron_palm = GLOBAL_CACHE.Skill.GetID("Iron_Palm")
        self.melandrus_resilience = GLOBAL_CACHE.Skill.GetID("Melandrus_Resilience")
        self.necrosis = GLOBAL_CACHE.Skill.GetID("Necrosis")
        self.peace_and_harmony = GLOBAL_CACHE.Skill.GetID("Peace_and_Harmony")
        self.purge_signet = GLOBAL_CACHE.Skill.GetID("Purge_Signet")
        self.resilient_weapon = GLOBAL_CACHE.Skill.GetID("Resilient_Weapon")
        self.gaze_from_beyond = GLOBAL_CACHE.Skill.GetID("Gaze_from_Beyond")
        self.spirit_burn = GLOBAL_CACHE.Skill.GetID("Spirit_Burn")
        self.signet_of_ghostly_might = GLOBAL_CACHE.Skill.GetID("Signet_of_Ghostly_Might")
        self.burning = GLOBAL_CACHE.Skill.GetID("Burning")
        self.blind = GLOBAL_CACHE.Skill.GetID("Blind")
        self.cracked_armor = GLOBAL_CACHE.Skill.GetID("Cracked_Armor")
        self.crippled = GLOBAL_CACHE.Skill.GetID("Crippled")
        self.dazed = GLOBAL_CACHE.Skill.GetID("Dazed")
        self.deep_wound = GLOBAL_CACHE.Skill.GetID("Deep_Wound")
        self.disease = GLOBAL_CACHE.Skill.GetID("Disease")
        self.poison = GLOBAL_CACHE.Skill.GetID("Poison")
        self.weakness = GLOBAL_CACHE.Skill.GetID("Weakness")
        self.comfort_animal = GLOBAL_CACHE.Skill.GetID("Comfort_Animal")
        self.heal_as_one = GLOBAL_CACHE.Skill.GetID("Heal_as_One")
        self.heroic_refrain = GLOBAL_CACHE.Skill.GetID("Heroic_Refrain")
        self.natures_blessing = GLOBAL_CACHE.Skill.GetID("Natures_Blessing")
        self.relentless_assault = GLOBAL_CACHE.Skill.GetID("Relentless_Assault")
        #junundu
        self.junundu_wail = GLOBAL_CACHE.Skill.GetID("Junundu_Wail")
        self.unknown_junundu_ability = GLOBAL_CACHE.Skill.GetID("Unknown_Junundu_Ability")
        self.leave_junundu = GLOBAL_CACHE.Skill.GetID("Leave_Junundu")
        self.junundu_tunnel = GLOBAL_CACHE.Skill.GetID("Junundu_Tunnel")
        
    def Update(self, cached_data):
        self.cached_data = cached_data
        self.in_aggro = cached_data.data.in_aggro
        
        self.fast_casting_exists = cached_data.data.fast_casting_exists
        self.fast_casting_level = cached_data.data.fast_casting_level
        self.expertise_exists = cached_data.data.expertise_exists
        self.expertise_level = cached_data.data.expertise_level
        
        options = cached_data.account_options
        self.is_targeting_enabled = options.Targeting if options is not None else False
        self.is_combat_enabled = options.Combat if options is not None else False
        self.is_skill_enabled = options.Skills if options is not None else [False]*MAX_SKILLS
        

    def PrioritizeSkills(self):
        """
        Create a priority-based skill execution order.
        """
        #initialize skillbar
        original_skills : list[CombatClass.SkillData] = []
        for i in range(MAX_SKILLS):
            original_skills.append(self.SkillData(i+1))

        # Initialize the pointer and tracking list
        ptr = 0
        ptr_chk = [False] * MAX_SKILLS
        ordered_skills  : list[CombatClass.SkillData] = []
        
        priorities = [
            SkillNature.CustomA,
            SkillNature.Interrupt,
            SkillNature.CustomB,
            SkillNature.Enchantment_Removal,
            SkillNature.CustomC,
            SkillNature.Healing,
            SkillNature.CustomD,
            SkillNature.Resurrection,
            SkillNature.CustomE,
            SkillNature.Hex_Removal,
            SkillNature.CustomF,
            SkillNature.Condi_Cleanse,
            SkillNature.CustomG,
            SkillNature.SelfTargeted,
            SkillNature.CustomH,
            SkillNature.EnergyBuff,
            SkillNature.CustomI,
            SkillNature.Buff,
            SkillNature.CustomJ,
            SkillNature.OffensiveA,
            SkillNature.CustomK,
            SkillNature.OffensiveB,
            SkillNature.CustomL,
            SkillNature.OffensiveC,
            SkillNature.CustomM,
            SkillNature.Offensive,
            SkillNature.CustomN,
        ]

        for priority in priorities:
            #for i in range(ptr,MAX_SKILLS):
            for i in range(MAX_SKILLS):
                skill = original_skills[i]
                if not ptr_chk[i] and skill.custom_skill_data.Nature == priority.value:
                    self.skill_order[ptr] = i
                    ptr_chk[i] = True
                    ptr += 1
                    ordered_skills.append(skill)
        
        skill_types = [
            SkillType.Form,
            SkillType.Enchantment,
            SkillType.EchoRefrain,
            SkillType.WeaponSpell,
            SkillType.Chant,
            SkillType.Preparation,
            SkillType.Ritual,
            SkillType.Ward,
            SkillType.Well,
            SkillType.Stance,
            SkillType.Shout,
            SkillType.Glyph,
            SkillType.Signet,
            SkillType.Hex,
            SkillType.Trap,
            SkillType.Spell,
            SkillType.Skill,
            SkillType.PetAttack,
            SkillType.Attack,
        ]

        
        for skill_type in skill_types:
            #for i in range(ptr,MAX_SKILLS):
            for i in range(MAX_SKILLS):
                skill = original_skills[i]
                if not ptr_chk[i] and skill.custom_skill_data.SkillType == skill_type.value:
                    self.skill_order[ptr] = i
                    ptr_chk[i] = True
                    ptr += 1
                    ordered_skills.append(skill)

        combos = [3, 2, 1]  # Dual attack, off-hand attack, lead attack
        for combo in combos:
            #for i in range(ptr,MAX_SKILLS):
            for i in range(MAX_SKILLS):
                skill = original_skills[i]
                if not ptr_chk[i] and GLOBAL_CACHE.Skill.Data.GetCombo(skill.skill_id) == combo:
                    self.skill_order[ptr] = i
                    ptr_chk[i] = True
                    ptr += 1
                    ordered_skills.append(skill)
        
        # Fill in remaining unprioritized skills
        for i in range(MAX_SKILLS):
            if not ptr_chk[i]:
                self.skill_order[ptr] = i
                ptr_chk[i] = True
                ptr += 1
                ordered_skills.append(original_skills[i])
        
        self.skills = ordered_skills
        
        
    def GetSkills(self):
        """
        Retrieve the prioritized skill set.
        """
        return self.skills
        

    def GetOrderedSkill(self, index:int)-> Optional[SkillData]:
        """
        Retrieve the skill at the given index in the prioritized order.
        """
        if 0 <= index < MAX_SKILLS:
            return self.skills[index]
        return None  # Return None if the index is out of bounds

    def AdvanceSkillPointer(self):
        self.skill_pointer += 1
        if self.skill_pointer >= MAX_SKILLS:
            self.skill_pointer = 0
            
    def ResetSkillPointer(self):
        self.skill_pointer = 0
        
    def SetSkillPointer(self, pointer):
        if 0 <= pointer < MAX_SKILLS:
            self.skill_pointer = pointer
        else:
            self.skill_pointer = 0
            
    def GetSkillPointer(self):
        return self.skill_pointer
            
    def GetEnergyValues(self,agent_id):
        from .utils import GetEnergyValues
        return GetEnergyValues(agent_id)

    def IsSkillReady(self, slot):
        original_index = self.skill_order[slot] 
        
        if self.skills[slot].skill_id == 0:
            return False

        if self.skills[slot].skillbar_data.recharge != 0:
            return False
        
        return self.is_skill_enabled[original_index]
        
    def InCastingRoutine(self):
        if self.aftercast_timer.HasElapsed(self.aftercast):
            self.in_casting_routine = False
            self.aftercast_timer.Reset()

        return self.in_casting_routine
 
    def GetPartyTargetID(self):
        if not GLOBAL_CACHE.Party.IsPartyLoaded():
            return 0

        # 1. Called Target (Ctrl+Click) - retrieved from Local Client Memory (flawless sync not guaranteed but safe)
        players = GLOBAL_CACHE.Party.GetPlayers()
        if players:
            target = players[0].called_target_id
            if Agent.IsValid(target) and Agent.IsLiving(target):
                 _, alleg = Agent.GetAllegiance(target)
                 if alleg == "Enemy":
                     return target
        
        # 2. Sync: Leader's current selected target from Shared Memory (Fastest)
        leader_acc = self.cached_data.party.get_by_party_pos(0)
        
        if leader_acc and leader_acc.PlayerID != 0:
            # Leader's Selected Target
            target = leader_acc.PlayerTargetID
            if Agent.IsValid(target) and Agent.IsLiving(target):
                _, alleg = Agent.GetAllegiance(target)
                if alleg == "Enemy":
                    return target
            

        
        return 0 
 

    def SafeChangeTarget(self, target_id):
        if Agent.IsValid(target_id):
            Player.ChangeTarget(target_id)
            
    def SafeInteract(self, target_id):
        if Agent.IsValid(target_id):
            Player.ChangeTarget(target_id)
            Player.Interact(target_id, False)


    def GetPartyTarget(self):
        party_target = self.GetPartyTargetID()
        if party_target != 0:
            current_target = Player.GetTargetID()
            if current_target != party_target:
                 self.SafeChangeTarget(party_target)
                 return party_target
        return 0

    def get_combat_distance(self):
        # Reduced from 5000.0 to 2800.0 to match Engagement Limit.
        # This prevents "Generic" selectors (like GetNearestEnemyCaster) from picking targets 
        # that we are not allowed to charge towards.
        return 2800.0 if self.in_aggro else Range.Earshot.value

    def GetWeaponRange(self, agent_id):
        """
        Returns the effective range of the agent's equipped weapon.
        """
        from .constants import MELEE_RANGE_VALUE, RANGED_RANGE_VALUE
        from Py4GWCoreLib.enums import Weapon
        
        # Get the specific weapon type (Enum) from the agent
        weapon_type = Agent.GetWeaponType(agent_id)
        
        # Ranges:
        # Melee: Axe, Hammer, Daggers, Scythe, Sword
        # Ranged: Bow, Spear
        # Caster: Scepter, Wand, Staff (Use Spellcast range)
        
        if weapon_type in [Weapon.Axe, Weapon.Hammer, Weapon.Daggers, Weapon.Scythe, Weapon.Sword]:
            return MELEE_RANGE_VALUE
            
        elif weapon_type in [Weapon.Bow, Weapon.Spear]:
            return RANGED_RANGE_VALUE
            
        elif weapon_type in [Weapon.Scepter, Weapon.Scepter2, Weapon.Wand, Weapon.Staff, Weapon.Staff1, Weapon.Staff2, Weapon.Staff3]:
             return Range.Spellcast.value # 1248.0
             
        # Fallback based on broader categories if exact type fails
        if Agent.IsMelee(agent_id):
            return MELEE_RANGE_VALUE
        elif Agent.IsRanged(agent_id):
            return RANGED_RANGE_VALUE
            
        return Range.Spellcast.value 

    # def StopMovement(self):
    #     """
    #     Stops the character's movement by tapping the backward key.
    #     This is necessary because Player.Move() is "sticky".
    #     """
    #     from Py4GWCoreLib.enums import Key
    #     import PyKeystroke
        
    #     # Create a keystroke instance
    #     keystroke = PyKeystroke.PyScanCodeKeystroke()
        
    #     # Tap 'S' (Backward) very briefly to break movement
    #     # We use PushKey for a single frame press/release usually, or explicit Press/Release
    #     keystroke.PushKey(Key.S.value) 

    def is_valid_defensive_target(self, agent_id):
        """
        An enemy is a valid target ONLY if:
        1. It is within Earshot (1000u) range.
        2. OR it is within Compass (3500u) range AND it is actively attacking a party member.
        """
        if agent_id == 0: return False
        
        my_pos = Agent.GetXY(Player.GetAgentID())
        target_pos = Agent.GetXY(agent_id)
        dist = Utils.Distance(my_pos, target_pos)
        
        # Rule 1: Nearby is always valid
        if dist <= Range.Earshot.value:
            # ConsoleLog("HeroAI", f"Target {agent_id} valid: Nearby ({int(dist)})") # Too noisy
            return True
            
        # Rule 2: Compass range checks (3500u)
        if dist <= Range.Compass.value:
            # Threat check: Enemy is attacking/casting at a party member
            target_of_enemy = CombatEvents.get_cast_target(agent_id) or CombatEvents.get_attack_target(agent_id)
            if target_of_enemy != 0:
                party_member_ids = AgentArray.GetAllyArray()
                if target_of_enemy in party_member_ids:
                    ConsoleLog("HeroAI", f"Target {agent_id} valid: Attacking Party ({int(dist)})")
                    return True
            
        # Rule 3: Offensive Sync (Global range for party support)
        # If ANY party member is attacking this specific enemy, we assist regardless of distance
        # We check both local client actions AND shared memory actions for maximum reliability
        party_member_ids = AgentArray.GetAllyArray()
        for member_id in party_member_ids:
            # Check local client action (best for immediate neighbors)
            if Agent.IsAttacking(member_id) or Agent.IsCasting(member_id):
                party_target = CombatEvents.get_cast_target(member_id) or CombatEvents.get_attack_target(member_id)
                if party_target == agent_id:
                    ConsoleLog("HeroAI", f"Target {agent_id} valid: Locally Assisting {member_id} ({int(dist)})")
                    return True
                    
        # Check Shared Memory states (best for cross-client sync during auto-attacks)
        for acc in self.cached_data.party:
            if acc.IsSlotActive and (acc.PlayerData.AgentData.Is_Attacking or acc.PlayerData.AgentData.Is_Casting):
                if acc.PlayerTargetID == agent_id:
                     ConsoleLog("HeroAI", f"Target {agent_id} valid: Sync Assisting {acc.PlayerID} ({int(dist)})")
                     return True
                    
        return False

    def GetAppropiateTarget(self, slot):
        v_target = 0

        if not self.is_targeting_enabled:
            return Player.GetTargetID()

        targeting_strict = self.skills[slot].custom_skill_data.Conditions.TargetingStrict
        target_allegiance = self.skills[slot].custom_skill_data.TargetAllegiance

        # Lazy helpers — only call expensive scans when a branch actually needs them
        _nearest_enemy = None
        def get_nearest_enemy():
            nonlocal _nearest_enemy
            if _nearest_enemy is None:
                from .settings import Settings
                mode = Settings().targeting_mode
                
                if mode == Settings.TargetingMode.Smart:
                    _nearest_enemy = self.GetSmartTarget()
                elif mode == Settings.TargetingMode.Assist:
                    _nearest_enemy = self.GetAssistTarget()
                    
                if not _nearest_enemy:
                    _nearest_enemy = Routines.Agents.GetNearestEnemy(self.get_combat_distance())
                
                # FINAL Defensive Filter: If it's not a valid defensive target, discard it
                if _nearest_enemy != 0 and not self.is_valid_defensive_target(_nearest_enemy):
                    _nearest_enemy = 0
            return _nearest_enemy

        _lowest_ally = None
        def get_lowest_ally():
            nonlocal _lowest_ally
            if _lowest_ally is None:
                _lowest_ally = TargetLowestAlly(filter_skill_id=self.skills[slot].skill_id)
            return _lowest_ally

        if self.skills[slot].skill_id == self.heroic_refrain:
            if not self.HasEffect(Player.GetAgentID(), self.heroic_refrain):
                return Player.GetAgentID()

        if target_allegiance == Skilltarget.Enemy:
            v_target = self.GetPartyTarget()
            if v_target == 0:
                v_target = get_nearest_enemy()
        elif target_allegiance == Skilltarget.EnemyCaster:
            v_target = Routines.Agents.GetNearestEnemyCaster(self.get_combat_distance())
            if v_target == 0 and not targeting_strict:
                v_target = get_nearest_enemy()
        elif target_allegiance == Skilltarget.EnemyMartial:
            v_target = Routines.Agents.GetNearestEnemyMartial(self.get_combat_distance())
            if v_target == 0 and not targeting_strict:
                v_target = get_nearest_enemy()
        elif target_allegiance == Skilltarget.EnemyMartialMelee:
            v_target = Routines.Agents.GetNearestEnemyMelee(self.get_combat_distance())
            if v_target == 0 and not targeting_strict:
                v_target = get_nearest_enemy()
        elif target_allegiance == Skilltarget.EnemyClustered:
            v_target = TargetClusteredEnemy(self.get_combat_distance())
            if v_target == 0 and not targeting_strict:
                v_target = get_nearest_enemy()
        elif target_allegiance == Skilltarget.EnemyAttacking:
            v_target = GetEnemyAttacking(self.get_combat_distance())
            if v_target == 0 and not targeting_strict:
                v_target = get_nearest_enemy()
        elif target_allegiance == Skilltarget.EnemyCasting:
            v_target = GetEnemyCasting(self.get_combat_distance())
            if v_target == 0 and not targeting_strict:
                v_target = get_nearest_enemy()
        elif target_allegiance == Skilltarget.EnemyCastingSpell:
            v_target = GetEnemyCastingSpell(self.get_combat_distance())
            if v_target == 0 and not targeting_strict:
                v_target = get_nearest_enemy()
        elif target_allegiance == Skilltarget.EnemyInjured:
            v_target = GetEnemyInjured(self.get_combat_distance())
            if v_target == 0 and not targeting_strict:
                v_target = get_nearest_enemy()
        elif target_allegiance == Skilltarget.EnemyConditioned:
            v_target = GetEnemyConditioned(self.get_combat_distance())
            if v_target == 0 and not targeting_strict:
                v_target = get_nearest_enemy()
        elif target_allegiance == Skilltarget.EnemyBleeding:
            v_target = GetEnemyBleeding(self.get_combat_distance())
            if v_target == 0 and not targeting_strict:
                v_target = get_nearest_enemy()
        elif target_allegiance == Skilltarget.EnemyPoisoned:
            v_target = GetEnemyPoisoned(self.get_combat_distance())
            if v_target == 0 and not targeting_strict:
                v_target = get_nearest_enemy()
        elif target_allegiance == Skilltarget.EnemyCrippled:
            v_target = GetEnemyCrippled(self.get_combat_distance())
            if v_target == 0 and not targeting_strict:
                v_target = get_nearest_enemy()
        elif target_allegiance == Skilltarget.EnemyHexed:
            v_target = GetEnemyHexed(self.get_combat_distance())
            if v_target == 0 and not targeting_strict:
                v_target = get_nearest_enemy()
        elif target_allegiance == Skilltarget.EnemyDegenHexed:
            v_target = GetEnemyDegenHexed(self.get_combat_distance())
            if v_target == 0 and not targeting_strict:
                v_target = get_nearest_enemy()
        elif target_allegiance == Skilltarget.EnemyEnchanted:
            v_target = GetEnemyEnchanted(self.get_combat_distance())
            if v_target == 0 and not targeting_strict:
                v_target = get_nearest_enemy()
        elif target_allegiance == Skilltarget.EnemyMoving:
            v_target = GetEnemyMoving(self.get_combat_distance())
            if v_target == 0 and not targeting_strict:
                v_target = get_nearest_enemy()
        elif target_allegiance == Skilltarget.EnemyKnockedDown:
            v_target = GetEnemyKnockedDown(self.get_combat_distance())
            if v_target == 0 and not targeting_strict:
                v_target = get_nearest_enemy()
        elif target_allegiance == Skilltarget.AllyMartialRanged:
            v_target = Routines.Agents.GetNearestEnemyRanged(self.get_combat_distance())
            if v_target == 0 and not targeting_strict:
                v_target = get_nearest_enemy()
        elif target_allegiance == Skilltarget.Ally:
            v_target = get_lowest_ally()
        elif target_allegiance == Skilltarget.AllyCaster:
            v_target = TargetLowestAllyCaster(filter_skill_id=self.skills[slot].skill_id)
            if v_target == 0 and not targeting_strict:
                v_target = get_lowest_ally()
        elif target_allegiance == Skilltarget.AllyMartial:
            v_target = TargetLowestAllyMartial(filter_skill_id=self.skills[slot].skill_id)
            if v_target == 0 and not targeting_strict:
                v_target = get_lowest_ally()
        elif target_allegiance == Skilltarget.AllyMartialMelee:
            v_target = TargetLowestAllyMelee(filter_skill_id=self.skills[slot].skill_id)
            if v_target == 0 and not targeting_strict:
                v_target = get_lowest_ally()
        elif target_allegiance == Skilltarget.AllyMartialRanged:
            v_target = TargetLowestAllyRanged(filter_skill_id=self.skills[slot].skill_id)
            if v_target == 0 and not targeting_strict:
                v_target = get_lowest_ally()
        elif target_allegiance == Skilltarget.OtherAlly:
            if self.skills[slot].custom_skill_data.Nature == SkillNature.EnergyBuff.value:
                v_target = TargetLowestAllyEnergy(other_ally=True, filter_skill_id=self.skills[slot].skill_id, less_energy=self.skills[slot].custom_skill_data.Conditions.LessEnergy)
                #print("Energy Buff Target: ", RawAgentArray().get_name(v_target))
            else:
                v_target = TargetLowestAlly(other_ally=True, filter_skill_id=self.skills[slot].skill_id)
        elif target_allegiance == Skilltarget.Self:
            v_target = Player.GetAgentID()
        elif target_allegiance == Skilltarget.Pet:
            v_target = GLOBAL_CACHE.Party.Pets.GetPetID(Player.GetAgentID())
        elif target_allegiance == Skilltarget.DeadAlly:
            v_target = Routines.Agents.GetDeadAlly(Range.Spellcast.value)
        elif target_allegiance == Skilltarget.Spirit:
            v_target = Routines.Agents.GetNearestSpirit(Range.Spellcast.value)
        elif target_allegiance == Skilltarget.Minion:
            v_target = Routines.Agents.GetLowestMinion(Range.Spellcast.value)
        elif target_allegiance == Skilltarget.Corpse:
            v_target = Routines.Agents.GetNearestCorpse(Range.Spellcast.value)
        else: # Fallback for generic targets
            v_target = self.GetPartyTarget()
            if v_target == 0:
                v_target = get_nearest_enemy()
        return v_target

    def GetSmartTarget(self):
        # Smart Target looks further (5000) to find the Leader's target,
        # but uses scoring to reject distant non-leader targets.
        search_range = 5000.0 if self.in_aggro else Range.Earshot.value
        enemy_array = Routines.Agents.GetFilteredEnemyArray(0, 0, search_range)
        if not enemy_array:
            return 0

        best_target = 0
        best_score = -1000.0
        
        my_id = Player.GetAgentID()
        my_target = Player.GetTargetID()
        my_pos = Agent.GetXY(my_id)
        
        for agent_id in enemy_array:
            if not Agent.IsAlive(agent_id):
                continue
            
            # Filter: Is this a valid defensive target?
            if not self.is_valid_defensive_target(agent_id):
                continue
                
            score = 0.0
            
            # 1. Health Score (0-50 pts) - Lower health = higher score
            health_pct = Agent.GetHealth(agent_id)
            score += (1.0 - health_pct) * 50.0
            
            # 2. Profession Score (0-100 pts)
            prof, _ = Agent.GetProfessionNames(agent_id)
            if prof == "Monk" or prof == "Ritualist":
                score += 100.0
            elif prof == "Mesmer" or prof == "Elementalist" or prof == "Necromancer":
                score += 60.0
            
            # 3. Distance Penalty
            dist = Utils.Distance(my_pos, Agent.GetXY(agent_id))
            score -= dist * 0.01  # -10 pts per 1000 units
            
            # 3b. Leader "Danger Zone" Bonus (Protect the Leader!)
            # If enemy is within 1250 units of the LEADER, give a big bonus.
            # This ensures we clear the area around the leader first.
            leader_acc = self.cached_data.party.get_by_party_pos(0)
            if leader_acc and leader_acc.PlayerID != 0:
                 leader_pos = Agent.GetXY(leader_acc.PlayerID)
                 dist_to_leader = Utils.Distance(leader_pos, Agent.GetXY(agent_id))
                 if dist_to_leader < 1250.0:
                     score += 1000.0
            
            # 3c. Party "Danger Zone" Bonus (Protect the Team)
            # If enemy is within 1250 units of ANY party member, give a moderate bonus.
            # (We skip the leader here since they are handled above, but checks are cheap)
            allies = AgentArray.GetAllyArray()
            for ally_id in allies:
                if Utils.Distance(Agent.GetXY(ally_id), Agent.GetXY(agent_id)) < 1250.0:
                    score += 500.0
                    break # Only apply bonus once

            
             # 4. Stickiness (Hysteresis)
            if agent_id == my_target:
                score += 40.0
                
            # 5. Leader Target Bonus & Distance Penalty
            # We want to strongly prioritize the leader's target to maintain cohesion.
            leader_target_id = self.GetPartyTargetID() # This fetches Leader Target or Called Target
            
            is_leader_target = (agent_id == leader_target_id)
            
            if is_leader_target:
                score += 2000.0 # Massive bonus to ensure we pick leader's target
            
            # If target is far away and NOT the leader's target, penalize it heavily.
            # This aligns with HandleCombat's engagement limit (2800) to prevent selecting targets we won't attack.
            if not is_leader_target and dist > 2800.0:
                 score -= 5000.0
                 
                
            if score > best_score:
                best_score = score
                best_target = agent_id
                
        return best_target

    def GetAssistTarget(self):
        # 1. Check for called target first (Party Leader's target)
        party_target = self.GetPartyTargetID()
        if Agent.IsValid(party_target) and Agent.IsEnemy(party_target) and Agent.IsAlive(party_target):
             return party_target

        # 2. Count attackers on each enemy
        # Search far (5000) to find assists even if they are distant
        search_range = 5000.0 if self.in_aggro else Range.Earshot.value
        enemy_array = Routines.Agents.GetFilteredEnemyArray(0, 0, search_range)
        if not enemy_array:
            return 0
            
        target_counts = {}
        party_members = AgentArray.GetAllyArray()
        
        for member_id in party_members:
            if member_id == Player.GetAgentID(): 
                continue # Don't count self
            
            t_id = CombatEvents.get_cast_target(member_id) or CombatEvents.get_attack_target(member_id)
            if t_id in enemy_array and Agent.IsAlive(t_id): # Only count if they are targeting an enemy we can see
                # Filter: Is this a valid defensive target?
                if self.is_valid_defensive_target(t_id):
                    target_counts[t_id] = target_counts.get(t_id, 0) + 1
        
        # 3. Choose target with most attackers
        best_target = 0
        max_attackers = 0
        
        for t_id, count in target_counts.items():
            if count > max_attackers:
                max_attackers = count
                best_target = t_id
            elif count == max_attackers and count > 0:
                # Tie-breaker: Use Smart logic (Health/Dist) or just nearest
                if self.GetEnergyValues(t_id) < self.GetEnergyValues(best_target): # Arbitrary tie-breaker using existing helper
                     best_target = t_id
        
        if best_target != 0:
            return best_target
            
        # Fallback to Smart if no one is attacking anything or no consensus
        return self.GetSmartTarget()

    def IsPartyMember(self, agent_id):
        from .utils import IsPartyMember
        return IsPartyMember(agent_id)
        
    def HasEffect(self, agent_id, skill_id, exact_weapon_spell=False):

        result = False
        custom_skill_data = custom_skill_data_handler.get_skill(skill_id)
        shared_effects = getattr(custom_skill_data.Conditions, "SharedEffects", []) if custom_skill_data else []


        if self.IsPartyMember(agent_id):
            from .utils import CheckForEffect
            return CheckForEffect(agent_id, skill_id)
                    
        else:
            result = (
                GLOBAL_CACHE.Effects.BuffExists(agent_id, skill_id) 
                or GLOBAL_CACHE.Effects.EffectExists(agent_id, skill_id)
                or any(GLOBAL_CACHE.Effects.BuffExists(agent_id, shared_buff) or GLOBAL_CACHE.Effects.EffectExists(agent_id, shared_buff) for shared_buff in shared_effects))

        if not result and not exact_weapon_spell:
           skilltype, _ = GLOBAL_CACHE.Skill.GetType(skill_id)
           if skilltype == SkillType.WeaponSpell.value:
               result = Agent.IsWeaponSpelled(agent_id)

        return result


    def AreCastConditionsMet(self, slot, vTarget):
        from .utils import GetEffectAndBuffIds
        
        number_of_features = 0
        feature_count = 0

        Conditions = self.skills[slot].custom_skill_data.Conditions

        """ Check if the skill is a resurrection skill and the target is dead """
        if self.skills[slot].custom_skill_data.Nature == SkillNature.Resurrection.value:
            return True if Agent.IsDead(vTarget) else False


        if self.skills[slot].custom_skill_data.Conditions.UniqueProperty:
            
            """ check all UniqueProperty skills """
            if (self.skills[slot].skill_id == self.energy_drain or 
                self.skills[slot].skill_id == self.energy_tap or
                self.skills[slot].skill_id == self.ether_lord 
                ):
                return self.GetEnergyValues(Player.GetAgentID()) < Conditions.LessEnergy
        
            if (self.skills[slot].skill_id == self.essence_strike):
                energy = self.GetEnergyValues(Player.GetAgentID()) < Conditions.LessEnergy
                return energy and (Routines.Agents.GetNearestSpirit(Range.Spellcast.value) != 0)

            if (self.skills[slot].skill_id == self.glowing_signet):
                energy= self.GetEnergyValues(Player.GetAgentID()) < Conditions.LessEnergy
                return energy and self.HasEffect(vTarget, self.burning)

            if (self.skills[slot].skill_id == self.clamor_of_souls):
                energy = self.GetEnergyValues(Player.GetAgentID()) < Conditions.LessEnergy
                weapon_type, _ = Agent.GetWeaponType(Player.GetAgentID())
                return energy and weapon_type == 0

            if (self.skills[slot].skill_id == self.waste_not_want_not):
                energy= self.GetEnergyValues(Player.GetAgentID()) < Conditions.LessEnergy
                return energy and not Agent.IsCasting(vTarget) and not Agent.IsAttacking(vTarget)

            if (self.skills[slot].skill_id == self.mend_body_and_soul):
                spirits_exist = Routines.Agents.GetNearestSpirit(Range.Earshot.value)
                life = Agent.GetHealth(Player.GetAgentID()) < Conditions.LessLife
                return life or (spirits_exist and Agent.IsConditioned(vTarget))

            if (self.skills[slot].skill_id == self.grenths_balance):
                life = Agent.GetHealth(Player.GetAgentID()) < Conditions.LessLife
                return life and Agent.GetHealth(Player.GetAgentID()) < Agent.GetHealth(vTarget)

            if (self.skills[slot].skill_id == self.deaths_retreat):
                return Agent.GetHealth(Player.GetAgentID()) < Agent.GetHealth(vTarget)

            if (self.skills[slot].skill_id == self.plague_sending or
                self.skills[slot].skill_id == self.plague_signet or
                self.skills[slot].skill_id == self.plague_touch
                ):
                return Agent.IsConditioned(Player.GetAgentID())

            if (self.skills[slot].skill_id == self.golden_fang_strike or
                self.skills[slot].skill_id == self.golden_fox_strike or
                self.skills[slot].skill_id == self.golden_lotus_strike or
                self.skills[slot].skill_id == self.golden_phoenix_strike or
                self.skills[slot].skill_id == self.golden_skull_strike
                ):
                return Agent.IsEnchanted(Player.GetAgentID())

            if (self.skills[slot].skill_id == self.brutal_weapon):
                return not Agent.IsEnchanted(Player.GetAgentID())

            if (self.skills[slot].skill_id == self.signet_of_removal):
                return not Agent.IsEnchanted(vTarget) and Agent.IsConditioned(vTarget)

            if (self.skills[slot].skill_id == self.dwaynas_kiss or
                self.skills[slot].skill_id == self.unnatural_signet or
                self.skills[slot].skill_id == self.toxic_chill
                ):
                return Agent.IsHexed(vTarget) or Agent.IsEnchanted(vTarget)

            if (self.skills[slot].skill_id == self.discord):
                return (Agent.IsHexed(vTarget) and Agent.IsConditioned(vTarget)) or (Agent.IsEnchanted(vTarget))

            if (self.skills[slot].skill_id == self.empathic_removal or
                self.skills[slot].skill_id == self.iron_palm or
                self.skills[slot].skill_id == self.melandrus_resilience or
                self.skills[slot].skill_id == self.necrosis or
                self.skills[slot].skill_id == self.peace_and_harmony or
                self.skills[slot].skill_id == self.purge_signet or
                self.skills[slot].skill_id == self.resilient_weapon
                ):
                return Agent.IsHexed(vTarget) or Agent.IsConditioned(vTarget)
            
            if (self.skills[slot].skill_id == self.gaze_from_beyond or
                self.skills[slot].skill_id == self.spirit_burn or
                self.skills[slot].skill_id == self.signet_of_ghostly_might
                ):
                return True if Routines.Agents.GetNearestSpirit(Range.Spellcast.value) != 0 else False
            
            if (self.skills[slot].skill_id == self.comfort_animal or
                self.skills[slot].skill_id == self.heal_as_one
                ):
                LessLife = Agent.GetHealth(vTarget) < Conditions.LessLife
                dead = Agent.IsDead(vTarget)
                return LessLife or dead
                
            if (self.skills[slot].skill_id == self.natures_blessing):
                player_life = Agent.GetHealth(Player.GetAgentID()) < Conditions.LessLife
                nearest_npc = Routines.Agents.GetNearestNPC(Range.Spirit.value)
                if nearest_npc == 0:
                    return player_life

                nearest_NPC_life = Agent.GetHealth(nearest_npc) < Conditions.LessLife
                return player_life or nearest_NPC_life
            
            if (self.skills[slot].skill_id == self.relentless_assault
                ):
                return Agent.IsHexed(Player.GetAgentID()) or Agent.IsConditioned(Player.GetAgentID())
            
            if (self.skills[slot].skill_id == self.junundu_wail):
                nearest_corpse = Routines.Agents.GetDeadAlly(Range.Earshot.value)
                if nearest_corpse != 0:
                    return True
                
                life = Agent.GetHealth(Player.GetAgentID()) < Conditions.LessLife
                nearest = Routines.Agents.GetNearestEnemy(Range.Earshot.value)
                if nearest == 0:
                    return life
                
                return False


            if (self.skills[slot].skill_id == self.junundu_tunnel):
                return Routines.Agents.GetNearestEnemy(Range.Earshot.value) == 0

            if ((self.skills[slot].skill_id == self.unknown_junundu_ability) or
                (self.skills[slot].skill_id == self.leave_junundu)
                ):
                return False


            return True  # if no unique property is configured, return True for all UniqueProperty
        
        feature_count += (1 if Conditions.IsAlive else 0)
        feature_count += (1 if Conditions.HasCondition else 0)
        feature_count += (1 if Conditions.HasBleeding else 0)
        feature_count += (1 if Conditions.HasBlindness else 0)
        feature_count += (1 if Conditions.HasBurning else 0)
        feature_count += (1 if Conditions.HasCrackedArmor else 0)
        feature_count += (1 if Conditions.HasCrippled else 0)
        feature_count += (1 if Conditions.HasDazed else 0)
        feature_count += (1 if Conditions.HasDeepWound else 0)
        feature_count += (1 if Conditions.HasDisease else 0)
        feature_count += (1 if Conditions.HasPoison else 0)
        feature_count += (1 if Conditions.HasWeakness else 0)
        feature_count += (1 if Conditions.HasWeaponSpell else 0)
        feature_count += (1 if Conditions.HasEnchantment else 0)
        feature_count += (1 if Conditions.HasDervishEnchantment else 0)
        feature_count += (1 if Conditions.HasHex else 0)
        feature_count += (1 if Conditions.HasChant else 0)
        feature_count += (1 if Conditions.IsCasting else 0)
        feature_count += (1 if Conditions.IsKnockedDown else 0)
        feature_count += (1 if Conditions.IsMoving else 0)
        feature_count += (1 if Conditions.IsAttacking else 0)
        feature_count += (1 if Conditions.IsHoldingItem else 0)
        feature_count += (1 if Conditions.LessLife > 0 else 0)
        feature_count += (1 if Conditions.MoreLife > 0 else 0)
        feature_count += (1 if Conditions.LessEnergy > 0 else 0)
        feature_count += (1 if Conditions.Overcast > 0 else 0)
        feature_count += (1 if Conditions.IsPartyWide else 0)
        feature_count += (1 if Conditions.RequiresSpiritInEarshot else 0)
        feature_count += (1 if Conditions.EnemiesInRange > 0 else 0)
        feature_count += (1 if Conditions.AlliesInRange > 0 else 0)
        feature_count += (1 if Conditions.SpiritsInRange > 0 else 0)
        feature_count += (1 if Conditions.MinionsInRange > 0 else 0)

        if Conditions.IsAlive:
            if Agent.IsAlive(vTarget):
                number_of_features += 1

        is_conditioned = Agent.IsConditioned(vTarget)
        is_bleeding = Agent.IsBleeding(vTarget)
        is_blind = self.HasEffect(vTarget, self.blind)
        is_burning = self.HasEffect(vTarget, self.burning)
        is_cracked_armor = self.HasEffect(vTarget, self.cracked_armor)
        is_crippled = Agent.IsCrippled(vTarget)
        is_dazed = self.HasEffect(vTarget, self.dazed)
        is_deep_wound = self.HasEffect(vTarget, self.deep_wound)
        is_disease = self.HasEffect(vTarget, self.disease)
        is_poison = Agent.IsPoisoned(vTarget)
        is_weakness = self.HasEffect(vTarget, self.weakness)
        
        if Conditions.HasCondition:
            if (is_conditioned or 
                is_bleeding or 
                is_blind or 
                is_burning or 
                is_cracked_armor or 
                is_crippled or 
                is_dazed or 
                is_deep_wound or 
                is_disease or 
                is_poison or 
                is_weakness):
                number_of_features += 1


        if Conditions.HasBleeding:
            if is_bleeding:
                number_of_features += 1

        if Conditions.HasBlindness:
            if is_blind:
                number_of_features += 1

        if Conditions.HasBurning:
            if is_burning:
                number_of_features += 1

        if Conditions.HasCrackedArmor:
            if is_cracked_armor:
                number_of_features += 1
          
        if Conditions.HasCrippled:
            if is_crippled:
                number_of_features += 1
                
        if Conditions.HasDazed:
            if is_dazed:
                number_of_features += 1
          
        if Conditions.HasDeepWound:
            if is_deep_wound:
                number_of_features += 1
                
        if Conditions.HasDisease:
            if is_disease:
                number_of_features += 1

        if Conditions.HasPoison:
            if is_poison:
                number_of_features += 1

        if Conditions.HasWeakness:
            if is_weakness:
                number_of_features += 1
         
        if Conditions.HasWeaponSpell:
            if Agent.IsWeaponSpelled(vTarget):
                if len(Conditions.WeaponSpellList) == 0:
                    number_of_features += 1
                else:
                    for skill_id in Conditions.WeaponSpellList:
                        if self.HasEffect(vTarget, skill_id, exact_weapon_spell=True):
                            number_of_features += 1
                            break

        if Conditions.HasEnchantment:
            if Agent.IsEnchanted(vTarget):
                if len(Conditions.EnchantmentList) == 0:
                    number_of_features += 1
                else:
                    for skill_id in Conditions.EnchantmentList:
                        if self.HasEffect(vTarget, skill_id):
                            number_of_features += 1
                            break

        if Conditions.HasDervishEnchantment:
            buff_list = GetEffectAndBuffIds(vTarget)
            for buff in buff_list:
                skill_type, _ = GLOBAL_CACHE.Skill.GetType(buff)
                if skill_type == SkillType.Enchantment.value:
                    _, profession = GLOBAL_CACHE.Skill.GetProfession(buff)
                    if profession == "Dervish":
                        number_of_features += 1
                        break

        if Conditions.HasHex:
            if Agent.IsHexed(vTarget):
                if len(Conditions.HexList) == 0:
                    number_of_features += 1
                else:
                    for skill_id in Conditions.HexList:
                        if self.HasEffect(vTarget, skill_id):
                            number_of_features += 1
                            break

        if Conditions.HasChant:
            if self.IsPartyMember(vTarget):                
                buff_list = GetEffectAndBuffIds(vTarget)
                
                for buff in buff_list:
                    skill_type, _ = GLOBAL_CACHE.Skill.GetType(buff)
                    if skill_type == SkillType.Chant.value:
                        if len(Conditions.ChantList) == 0:
                            number_of_features += 1
                        else:
                            if buff in Conditions.ChantList:
                                number_of_features += 1
                                break
                                
        if Conditions.IsCasting:
            if Agent.IsCasting(vTarget):
                casting_skill_id = Agent.GetCastingSkillID(vTarget)
                if GLOBAL_CACHE.Skill.Data.GetActivation(casting_skill_id) >= 0.250:
                    if len(Conditions.CastingSkillList) == 0:
                        number_of_features += 1
                    else:
                        if casting_skill_id in Conditions.CastingSkillList:
                            number_of_features += 1

        if Conditions.IsKnockedDown:
            if Agent.IsKnockedDown(vTarget):
                number_of_features += 1
                            
        if Conditions.IsMoving:
            if Agent.IsMoving(vTarget):
                number_of_features += 1
        
        if Conditions.IsAttacking:
            if Agent.IsAttacking(vTarget):
                number_of_features += 1

        if Conditions.IsHoldingItem:
            weapon_type, _ = Agent.GetWeaponType(vTarget)
            if weapon_type == 0:
                number_of_features += 1

        if Conditions.LessLife != 0:
            if Agent.GetHealth(vTarget) < Conditions.LessLife:
                number_of_features += 1

        if Conditions.MoreLife != 0:
            if Agent.GetHealth(vTarget) > Conditions.MoreLife:
                number_of_features += 1
        
        if Conditions.LessEnergy != 0:
            from .utils import GetEnergyValues
            if self.IsPartyMember(vTarget):
                player_energy = GetEnergyValues(vTarget)
                if player_energy < Conditions.LessEnergy:
                    number_of_features += 1
            else:
                number_of_features += 1 #henchmen, allies, pets or something else thats not reporting energy

        if Conditions.Overcast != 0:
            if Player.GetAgentID() == vTarget:
                if Agent.GetOvercast(vTarget) < Conditions.Overcast:
                    number_of_features += 1
                    
        if Conditions.IsPartyWide:
            area = Range.SafeCompass.value if Conditions.PartyWideArea == 0 else Conditions.PartyWideArea
            less_life = Conditions.LessLife
            
            allies_array = GetAllAlliesArray(area)
            total_group_life = 0.0
            for agent in allies_array:
                total_group_life += Agent.GetHealth(agent)
                
            total_group_life /= len(allies_array)
            
            if total_group_life < less_life:
                number_of_features += 1
                                    
        if Conditions.RequiresSpiritInEarshot:            
            distance = Range.Earshot.value
            spirit_array = AgentArray.GetSpiritPetArray()
            spirit_array = AgentArray.Filter.ByDistance(spirit_array, Player.GetXY(), distance)            
            spirit_array = AgentArray.Filter.ByCondition(spirit_array, lambda agent_id: Agent.IsAlive(agent_id))
            
            if(len(spirit_array) > 0):
                number_of_features += 1
                    
        if self.skills[slot].custom_skill_data.SkillType == SkillType.PetAttack.value:
            pet_id = GLOBAL_CACHE.Party.Pets.GetPetID(Player.GetAgentID())
            if Agent.IsDead(pet_id):
                return False
            
            pet_attack_list = [GLOBAL_CACHE.Skill.GetID("Bestial_Mauling"),
                               GLOBAL_CACHE.Skill.GetID("Bestial_Pounce"),
                               GLOBAL_CACHE.Skill.GetID("Brutal_Strike"),
                               GLOBAL_CACHE.Skill.GetID("Disrupting_Lunge"),
                               GLOBAL_CACHE.Skill.GetID("Enraged_Lunge"),
                               GLOBAL_CACHE.Skill.GetID("Feral_Lunge"),
                               GLOBAL_CACHE.Skill.GetID("Ferocious_Strike"),
                               GLOBAL_CACHE.Skill.GetID("Maiming_Strike"),
                               GLOBAL_CACHE.Skill.GetID("Melandrus_Assault"),
                               GLOBAL_CACHE.Skill.GetID("Poisonous_Bite"),
                               GLOBAL_CACHE.Skill.GetID("Pounce"),
                               GLOBAL_CACHE.Skill.GetID("Predators_Pounce"),
                               GLOBAL_CACHE.Skill.GetID("Savage_Pounce"),
                               GLOBAL_CACHE.Skill.GetID("Scavenger_Strike")
                               ]
            
            for skill_id in pet_attack_list:
                if self.skills[slot].skill_id == skill_id:
                    if self.HasEffect(pet_id,self.skills[slot].skill_id ):
                        return False
            
        if Conditions.EnemiesInRange != 0:
            player_pos = Player.GetXY()
            enemy_array = enemy_array = Routines.Agents.GetFilteredEnemyArray(player_pos[0], player_pos[1], Conditions.EnemiesInRangeArea)
            if len(enemy_array) >= Conditions.EnemiesInRange:
                number_of_features += 1
            else:
                number_of_features = 0
                
        if Conditions.AlliesInRange != 0:
            player_pos = Player.GetXY()
            ally_array = ally_array = Routines.Agents.GetFilteredAllyArray(player_pos[0], player_pos[1], Conditions.AlliesInRangeArea,other_ally=True)
            if len(ally_array) >= Conditions.AlliesInRange:
                number_of_features += 1
            else:
                number_of_features = 0
                
        if Conditions.SpiritsInRange != 0:
            player_pos = Player.GetXY()
            ally_array = ally_array = Routines.Agents.GetFilteredSpiritArray(player_pos[0], player_pos[1], Conditions.SpiritsInRangeArea)
            if len(ally_array) >= Conditions.SpiritsInRange:
                number_of_features += 1
            else:
                number_of_features = 0
                
        if Conditions.MinionsInRange != 0:
            player_pos = Player.GetXY()
            ally_array = ally_array = Routines.Agents.GetFilteredMinionArray(player_pos[0], player_pos[1], Conditions.MinionsInRangeArea)
            if len(ally_array) >= Conditions.MinionsInRange:
                number_of_features += 1
            else:
                number_of_features = 0
            

        #Py4GW.Console.Log("AreCastConditionsMet", f"feature count: {feature_count}, No of features {number_of_features}", Py4GW.Console.MessageType.Info)
        
        if feature_count == number_of_features:
            return True

        return False


    def SpiritBuffExists(self, skill_id):
        spirit_array = AgentArray.GetSpiritPetArray()
        distance = Range.Earshot.value
        spirit_array = AgentArray.Filter.ByDistance(spirit_array, Player.GetXY(), distance)
        spirit_array = AgentArray.Filter.ByCondition(spirit_array, lambda agent_id: Agent.IsAlive(agent_id))

        for spirit_id in spirit_array:
            model_value = Agent.GetPlayerNumber(spirit_id)

            # Check if model_value is valid for SpiritModelID Enum
            if model_value in SpiritModelID._value2member_map_:
                spirit_model_id = SpiritModelID(model_value)
                if SPIRIT_BUFF_MAP.get(spirit_model_id) == skill_id:
                    return True


        return False



    def IsReadyToCast(self, slot):
        # --- Cheap target-independent checks first (avoid expensive target resolution) ---

        if Agent.IsCasting(Player.GetAgentID()):
            self.in_casting_routine = False
            return False, 0
        if GLOBAL_CACHE.SkillBar.GetCasting() != 0:
            self.in_casting_routine = False
            return False, 0

        # Check if no skill is assigned to the slot
        if self.skills[slot].skill_id == 0:
            self.in_casting_routine = False
            return False, 0

        # Check if the skill is recharging
        if not Routines.Checks.Skills.IsSkillIDReady(self.skills[slot].skill_id):
            self.in_casting_routine = False
            return False, 0

        # Check if there is enough energy
        current_energy = self.GetEnergyValues(Player.GetAgentID()) * Agent.GetMaxEnergy(Player.GetAgentID())
        energy_cost = Routines.Checks.Skills.GetEnergyCostWithEffects(self.skills[slot].skill_id, Player.GetAgentID())

        if self.expertise_exists:
            energy_cost = Routines.Checks.Skills.apply_expertise_reduction(energy_cost, self.expertise_level, self.skills[slot].skill_id)

        if current_energy < energy_cost:
            self.in_casting_routine = False
            return False, 0

        # Check if there is enough health
        current_hp = Agent.GetHealth(Player.GetAgentID())
        target_hp = self.skills[slot].custom_skill_data.Conditions.SacrificeHealth
        health_cost = GLOBAL_CACHE.Skill.Data.GetHealthCost(self.skills[slot].skill_id)
        if (current_hp < target_hp) and health_cost > 0:
            self.in_casting_routine = False
            return False, 0

        # Check if there is enough adrenaline
        adrenaline_required = GLOBAL_CACHE.Skill.Data.GetAdrenaline(self.skills[slot].skill_id)
        if adrenaline_required > 0 and self.skills[slot].skillbar_data.adrenaline_a < adrenaline_required:
            self.in_casting_routine = False
            return False, 0

        # Check spirit buff (target-independent)
        if self.SpiritBuffExists(self.skills[slot].skill_id):
            self.in_casting_routine = False
            return False, 0

        # --- Expensive target resolution (only if all cheap checks passed) ---
        v_target = self.GetAppropiateTarget(slot)

        if v_target is None or v_target == 0:
            self.in_casting_routine = False
            return False, 0

        # --- Target-dependent checks ---

        # Check combo conditions
        combo_type = GLOBAL_CACHE.Skill.Data.GetCombo(self.skills[slot].skill_id)
        dagger_status = Agent.GetDaggerStatus(v_target)
        if ((combo_type == 1 and dagger_status not in (0, 3)) or
            (combo_type == 2 and dagger_status != 1) or
            (combo_type == 3 and dagger_status != 2)):
            self.in_casting_routine = False
            return False, v_target

        # Check if the skill has the required conditions
        if not self.AreCastConditionsMet(slot, v_target):
            self.in_casting_routine = False
            return False, v_target

        # Check if effect already exists on target (uses shared memory for party members)
        if self.HasEffect(v_target, self.skills[slot].skill_id):
            self.in_casting_routine = False
            return False, v_target

        return True, v_target

    def IsOOCSkill(self, slot):
        if self.skills[slot].custom_skill_data.Conditions.IsOutOfCombat:
            return True

        skill_type = self.skills[slot].custom_skill_data.SkillType
        skill_nature = self.skills[slot].custom_skill_data.Nature

        if(skill_type == SkillType.Form.value or
           skill_type == SkillType.Preparation.value or
           skill_nature == SkillNature.Healing.value or
           skill_nature == SkillNature.Hex_Removal.value or
           skill_nature == SkillNature.Condi_Cleanse.value or
           skill_nature == SkillNature.EnergyBuff.value or
           skill_nature == SkillNature.Resurrection.value
        ):
            return True

        return False

    def ChooseTarget(self, interact=True):       
        if not self.is_targeting_enabled:
            return False

        if not self.in_aggro:
            return False

            
        called_target = self.GetPartyTarget()
        #if Agent.IsAlive(called_target):
        if called_target != 0:
            self.SafeInteract(called_target)
            return True
            
        nearest = Routines.Agents.GetNearestEnemy(self.get_combat_distance())
        if nearest != 0:
            self.SafeInteract(nearest)
            return True
        
        
        
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
                    attack_speed = 1.75
                case Weapon.Scepter2.value:
                    attack_speed = 1.75
                case Weapon.Wand.value:
                    attack_speed = 1.75
                case Weapon.Staff1.value:
                    attack_speed = 1.75
                case Weapon.Staff.value:
                    attack_speed = 1.75
                case Weapon.Staff2.value:
                    attack_speed = 1.75
                case Weapon.Staff3.value:
                    attack_speed = 1.75
                case _:
                    attack_speed = 1.75
                    
        return int((attack_speed / attack_speed_modifier) * 1000)

    def GetDrunkLevel(self):
        """
        Get current drunk level (0-5). Returns 0 if unable to determine.
        """
        try:
            level = Effects.GetAlcoholLevel()
            return max(0, min(5, int(level)))
        except Exception:
            pass
        return 0

    def UseAlcoholIfAvailable(self):
        """
        Checks inventory for alcohol and uses the first available one.
        Only uses alcohol if drunk level is 0 (not drunk).
        Returns True if alcohol was used, False otherwise.
        """
        try:
            # Check if already drunk
            drunk_level = self.GetDrunkLevel()
            Py4GW.Console.Log("HeroAI", f"Drunken Master: drunk level = {drunk_level}", Py4GW.Console.MessageType.Debug)
            
            if drunk_level > 0:
                Py4GW.Console.Log("HeroAI", f"Already drunk (level {drunk_level}), skipping alcohol", Py4GW.Console.MessageType.Debug)
                return False
            
            for alcohol_model_id in ALCOHOL_MODEL_IDS:
                if GLOBAL_CACHE.Inventory.GetModelCount(alcohol_model_id) > 0:
                    item_id = GLOBAL_CACHE.Item.GetItemIdFromModelID(alcohol_model_id)
                    if item_id:
                        Py4GW.Console.Log("HeroAI", f"Using alcohol item_id {item_id}", Py4GW.Console.MessageType.Info)
                        GLOBAL_CACHE.Inventory.UseItem(item_id)
                        return True
            
            Py4GW.Console.Log("HeroAI", "No alcohol found in inventory", Py4GW.Console.MessageType.Debug)
        except Exception as e:
            Py4GW.Console.Log("HeroAI", f"Error in UseAlcoholIfAvailable: {e}", Py4GW.Console.MessageType.Warning)
        return False

    def HandleCombat(self,ooc=False):
        """
        tries to Execute the next skill in the skill order.
        """
       
        slot = self.skill_pointer
        skill_id = self.skills[slot].skill_id
        
        is_skill_ready = self.IsSkillReady(slot)
            
        if not is_skill_ready:
            self.AdvanceSkillPointer()
            return False
        
        is_ooc_skill = self.IsOOCSkill(slot)

        if ooc and not is_ooc_skill:
            self.AdvanceSkillPointer()
            return False
         
         
        is_read_to_cast, target_agent_id = self.IsReadyToCast(slot)
 
        if not is_read_to_cast:
            # If we don't have a target for THIS skill, we might still have a target for another
            # or we might just be waiting. But if we reach the end of the loop and no target was found 
            # for ANY skill, then we are not engaged.
            self.AdvanceSkillPointer()
            # If we just reached the end of the skill order, we've checked everything
            if self.skill_pointer == 0:
                # OLD: return False
                # NEW: If we have a valid target, proceed to Movement Logic instead of giving up!
                target_agent_id = Player.GetTargetID()
                
                # Manual validation since IsValidEnemyTarget helper doesn't exist
                if not Agent.IsValid(target_agent_id) or Agent.IsDead(target_agent_id):
                     return False
                
                _, alleg = Agent.GetAllegiance(target_agent_id)
                if alleg != "Enemy":
                     return False
                     
                # Fall through to Movement Logic
            else:
                return True # Stay in combat mode while checking other skills
        

        if target_agent_id == 0:
            self.AdvanceSkillPointer()
            return False

        # --- Aggro Response: Movement Logic ---
        # If we have a target but we aren't "ready to cast" (likely due to range), 
        # let's try to move towards the target if we are in combat mode.
        my_pos = Agent.GetXY(Player.GetAgentID())
        target_pos = Agent.GetXY(target_agent_id)
        dist_to_target = Utils.Distance(my_pos, target_pos)
        
        # Check if Follow Module is busy pathing (Mutual Exclusion)
        from HeroAI.following import follower_states
        my_id = Player.GetAgentID()
        state = follower_states.get(my_id)
        
        # Determine maximum effective range for this skill
        try:
            # Most skills are Spellcast (1000), but we check specifically if possible
            skill_range = GLOBAL_CACHE.Skill.Data.GetRange(skill_id)
            if skill_range == 0: 
                # If skill has no range (e.g. self-buff or shout), use Weapon Range
                # This prevents "charging" to melee range if we have a bow
                weapon_range = self.GetWeaponRange(Player.GetAgentID())
                skill_range = weapon_range
        except:
             skill_range = Range.Spellcast.value

        # --- Engagement Leash ---
        # 1. Limit raw engagement distance (Don't charge across the map)
        # 1. Limit raw engagement distance (Don't charge across the map)
        # Reduced from 5000.0 to 2800.0 to prevent wandering far from current position (approx Longbow range + buffer)
        engagement_limit = 2800.0 
        
        # 2. Leader Leash (Stay near the party leader)
        leader_acc = self.cached_data.party.get_by_party_pos(0)
        max_dist_from_leader = 2000.0
        
        can_engage = dist_to_target <= engagement_limit
        
        # --- Distant Leader Assist Override ---
        # If the target is the Leader's target, we allow engagement up to a much further distance (e.g. 5000).
        # This ensures we assist the leader even if they are engaging from max compass range.
        leader_target_id = 0
        if leader_acc:
             leader_target_id = leader_acc.PlayerTargetID
        
        is_leader_target = (target_agent_id == leader_target_id)
        
        if is_leader_target:
            can_engage = dist_to_target <= 5000.0 # Override engagement limit for leader assist
            
        # If NOT leader target, enforce stricter engagement rules.
        # This prevents chasing random distant enemies.
        if not is_leader_target and dist_to_target > skill_range * 1.5 and dist_to_target > engagement_limit:
             can_engage = False
        
        if leader_acc and leader_acc.PlayerID != 0 and Agent.IsLiving(leader_acc.PlayerID):
            leader_pos = Agent.GetXY(leader_acc.PlayerID)
            dist_to_leader = Utils.Distance(my_pos, leader_pos)
            if dist_to_leader > max_dist_from_leader:
                can_engage = False
            # Also check if target is way too far from leader
            # Also check if target is way too far from leader
            # Reduced from 5000.0 to 3500.0 to prevent chasing targets far outside the group's area of operation.
            if Utils.Distance(target_pos, leader_pos) > 3500.0:
                can_engage = False

        # Removed the local "Distant Target Filter" block here because it caused a deadlock.
        # (The bot would select a target via GetAppropiateTarget, then reject it here, resulting in inaction).
        # We now handle the distance logic via `can_engage` override above.

        # If we are out of skill range but within our safe engagement limits, move!
        # If we are out of skill range but within our safe engagement limits, engage!
        if dist_to_target > skill_range and can_engage:
            # MOVEMENT OVERRIDE: If we want to charge, we MUST break the follow path
            if state and state.path:
                state.path = [] # Clear the follow path instantly
                
            # Use Player.Interact to move into range. This handles stopping at the correct weapon range automatically.
            # We removed Player.Move() because it is sticky and causes over-running to melee.
            if not Agent.IsCasting(Player.GetAgentID()):
                 # Define force_engage: If we are not moving, we assume this is the initial engagement 
                 # and we want to react instantly (bypass throttle).
                 force_engage = not Agent.IsMoving(Player.GetAgentID())
                 
                 # Use throttle to avoid packet spam, but allow instant first engage
                 if self.movement_throttle_timer.IsExpired() or force_engage:
                     Player.Interact(target_agent_id)
                     self.movement_throttle_timer.Reset()

            return True # Returning True indicates we handled the combat tick (by engaging)
        elif dist_to_target > skill_range and not can_engage:
            # If we are out of range and cannot safely engage, fall back to Follow logic
            ConsoleLog("HeroAI", f"Combat Charge Blocked: Target {target_agent_id} Dist:{int(dist_to_target)}")
            return False
        
        # If we are within skill range OR can_engage is blocked by pathing, 
        # we consider combat "Active" but might not move.
        if dist_to_target <= skill_range:
            # We are in range to fight. 
            
            # We removed the manual StopMovement() call here because we now use Interact() to approach,
            # which correctly stops at weapon range. Manual stopping was checking Agent.IsMoving() which
            # is true during the Interact approach, causing stutter/cancellation.

            # Ensure we are attacking if not casting.
            if not Agent.IsAttacking(Player.GetAgentID()) and not Agent.IsCasting(Player.GetAgentID()):
                 # Throttle interaction to avoid spam
                 if self.movement_throttle_timer.IsExpired():
                     Player.Interact(target_agent_id)
                     self.movement_throttle_timer.Reset()
            pass 
        else:
            # We are outside range but can't/won't move (either pathing or leashed)
            # If leashed, we already returned False above.
            # If pathing, we fall through and might return True to keep combat "active" (blocking Follow pathing? No, that's bad).
            # If Follow pathing is active, we should probably allow Follow to continue.
            if not can_engage_with_movement:
                return False 

        if not Agent.IsLiving(target_agent_id):
            return False
        
        # Auto-use alcohol before alcohol-dependent PVE skills for optimal effect
        alcohol_skills = [
            GLOBAL_CACHE.Skill.GetID("Drunken_Master"),
            GLOBAL_CACHE.Skill.GetID("Dwarven_Stability"),
            GLOBAL_CACHE.Skill.GetID("Feel_No_Pain")
        ]
        
        if skill_id in alcohol_skills:
            Py4GW.Console.Log("HeroAI", f"Detected alcohol-dependent skill, checking for alcohol...", Py4GW.Console.MessageType.Info)
            self.UseAlcoholIfAvailable()
            
        self.in_casting_routine = True
        
        if self.fast_casting_exists:
            activation, recharge = Routines.Checks.Skills.apply_fast_casting(skill_id, self.fast_casting_level)
        else:
            activation = GLOBAL_CACHE.Skill.Data.GetActivation(skill_id)

        self.aftercast = activation * 1000
        self.aftercast += GLOBAL_CACHE.Skill.Data.GetAftercast(skill_id) * 1000 #750
        
        skill_type, _ = GLOBAL_CACHE.Skill.GetType(skill_id)
        if skill_type == SkillType.Attack.value:
            self.aftercast += self.GetWeaponAttackAftercast()
            
            
        self.aftercast += self.ping_handler.GetCurrentPing()

        self.aftercast_timer.Reset()
        GLOBAL_CACHE.SkillBar.UseSkill(self.skill_order[self.skill_pointer]+1, target_agent_id)
        self.ResetSkillPointer()
        return True