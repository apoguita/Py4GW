from Py4GWCoreLib import *
from .custom_skill import *
from .types import *
from .targeting import *
from typing import Optional


MAX_SKILLS = 8
custom_skill_data_handler = CustomSkillClass()

SPIRIT_BUFF_MAP = {
    SpiritModelID.FROZEN_SOIL: Skill.GetID("Frozen_Soil"),
    SpiritModelID.LIFE: Skill.GetID("Life"),
    SpiritModelID.BLOODSONG: Skill.GetID("Bloodsong"),
    SpiritModelID.ANGER: Skill.GetID("Signet_of_Spirits"),
    SpiritModelID.HATE: Skill.GetID("Signet_of_Spirits"),
    SpiritModelID.SUFFERING: Skill.GetID("Signet_of_Spirits"),
    SpiritModelID.ANGUISH: Skill.GetID("Anguish"),
    SpiritModelID.DISENCHANTMENT: Skill.GetID("Disenchantment"),
    SpiritModelID.DISSONANCE: Skill.GetID("Dissonance"),
    SpiritModelID.PAIN: Skill.GetID("Pain"),
    SpiritModelID.SHADOWSONG: Skill.GetID("Shadowsong"),
    SpiritModelID.WANDERLUST: Skill.GetID("Wanderlust"),
    SpiritModelID.VAMPIRISM: Skill.GetID("Vampirism"),
    SpiritModelID.AGONY: Skill.GetID("Agony"),
    SpiritModelID.DISPLACEMENT: Skill.GetID("Displacement"),
    SpiritModelID.EARTHBIND: Skill.GetID("Earthbind"),
    SpiritModelID.EMPOWERMENT: Skill.GetID("Empowerment"),
    SpiritModelID.PRESERVATION: Skill.GetID("Preservation"),
    SpiritModelID.RECOVERY: Skill.GetID("Recovery"),
    SpiritModelID.RECUPERATION: Skill.GetID("Recuperation"),
    SpiritModelID.REJUVENATION: Skill.GetID("Rejuvenation"),
    SpiritModelID.SHELTER: Skill.GetID("Shelter"),
    SpiritModelID.SOOTHING: Skill.GetID("Soothing"),
    SpiritModelID.UNION: Skill.GetID("Union"),
    SpiritModelID.DESTRUCTION: Skill.GetID("Destruction"),
    SpiritModelID.RESTORATION: Skill.GetID("Restoration"),
    SpiritModelID.WINDS: Skill.GetID("Winds"),
    SpiritModelID.BRAMBLES: Skill.GetID("Brambles"),
    SpiritModelID.CONFLAGRATION: Skill.GetID("Conflagration"),
    SpiritModelID.ENERGIZING_WIND: Skill.GetID("Energizing_Wind"),
    SpiritModelID.EQUINOX: Skill.GetID("Equinox"),
    SpiritModelID.EDGE_OF_EXTINCTION: Skill.GetID("Edge_of_Extinction"),
    SpiritModelID.FAMINE: Skill.GetID("Famine"),
    SpiritModelID.FAVORABLE_WINDS: Skill.GetID("Favorable_Winds"),
    SpiritModelID.FERTILE_SEASON: Skill.GetID("Fertile_Season"),
    SpiritModelID.GREATER_CONFLAGRATION: Skill.GetID("Greater_Conflagration"),
    SpiritModelID.INFURIATING_HEAT: Skill.GetID("Infuriating_Heat"),
    SpiritModelID.LACERATE: Skill.GetID("Lacerate"),
    SpiritModelID.MUDDY_TERRAIN: Skill.GetID("Muddy_Terrain"),
    SpiritModelID.NATURES_RENEWAL: Skill.GetID("Natures_Renewal"),
    SpiritModelID.PESTILENCE: Skill.GetID("Pestilence"),
    SpiritModelID.PREDATORY_SEASON: Skill.GetID("Predatory_Season"),
    SpiritModelID.PRIMAL_ECHOES: Skill.GetID("Primal_Echoes"),
    SpiritModelID.QUICKENING_ZEPHYR: Skill.GetID("Quickening_Zephyr"),
    SpiritModelID.QUICKSAND: Skill.GetID("Quicksand"),
    SpiritModelID.ROARING_WINDS: Skill.GetID("Roaring_Winds"),
    SpiritModelID.SYMBIOSIS: Skill.GetID("Symbiosis"),
    SpiritModelID.TOXICITY: Skill.GetID("Toxicity"),
    SpiritModelID.TRANQUILITY: Skill.GetID("Tranquility"),
    SpiritModelID.WINTER: Skill.GetID("Winter"),
    SpiritModelID.WINNOWING: Skill.GetID("Winnowing"),
}

class CombatClass:
    global MAX_SKILLS, custom_skill_data_handler

    class SkillData:
        def __init__(self, slot):
            self.skill_id = SkillBar.GetSkillIDBySlot(slot)  # slot is 1 based
            self.skillbar_data = SkillBar.GetSkillData(slot)  # Fetch additional data from the skill bar
            self.custom_skill_data = custom_skill_data_handler.get_skill(self.skill_id)  # Retrieve custom skill data

    def __init__(self):
        import HeroAI.shared_memory_manager as shared_memory_manager
        """
        Initializes the CombatClass with an empty skill set and order.
        """
        self.skills = []
        self.skill_order = [0] * MAX_SKILLS
        self.skill_pointer = 0
        self.in_casting_routine = False
        self.aftercast = 0
        self.aftercast_timer = Timer()
        self.aftercast_timer.Start()
        self.ping_handler = Py4GW.PingHandler()
        self.oldCalledTarget = 0
        self.shared_memory_handler = shared_memory_manager.SharedMemoryManager()
        
        self.in_aggro = False
        self.is_targeting_enabled = False
        self.is_combat_enabled = False
        self.is_skill_enabled = []
        
        self.nearest_enemy = Routines.Agents.GetNearestEnemy(self.get_combat_distance())
        self.lowest_ally = TargetLowestAlly()
        self.lowest_ally_energy = TargetLowestAllyEnergy()
        self.nearest_npc = Routines.Agents.GetNearestNPC(Range.Spellcast.value)
        self.nearest_spirit = Routines.Agents.GetNearestSpirit(Range.Spellcast.value)
        self.lowest_minion = Routines.Agents.GetLowestMinion(Range.Spellcast.value)
        self.nearest_corpse = Routines.Agents.GetNearestCorpse(Range.Spellcast.value)
        
        self.energy_drain = Skill.GetID("Energy_Drain") 
        self.energy_tap = Skill.GetID("Energy_Tap")
        self.ether_lord = Skill.GetID("Ether_Lord")
        self.essence_strike = Skill.GetID("Essence_Strike")
        self.glowing_signet = Skill.GetID("Glowing_Signet")
        self.clamor_of_souls = Skill.GetID("Clamor_of_Souls")
        self.waste_not_want_not = Skill.GetID("Waste_Not_Want_Not")
        self.mend_body_and_soul = Skill.GetID("Mend_Body_and_Soul")
        self.grenths_balance = Skill.GetID("Grenths_Balance")
        self.deaths_retreat = Skill.GetID("Deaths_Retreat")
        self.plague_sending = Skill.GetID("Plague_Sending")
        self.plague_signet = Skill.GetID("Plague_Signet")
        self.plague_touch = Skill.GetID("Plague_Touch")
        self.golden_fang_strike = Skill.GetID("Golden_Fang_Strike")
        self.golden_fox_strike = Skill.GetID("Golden_Fox_Strike")
        self.golden_lotus_strike = Skill.GetID("Golden_Lotus_Strike")
        self.golden_phoenix_strike = Skill.GetID("Golden_Phoenix_Strike")
        self.golden_skull_strike = Skill.GetID("Golden_Skull_Strike")
        self.brutal_weapon = Skill.GetID("Brutal_Weapon")
        self.signet_of_removal = Skill.GetID("Signet_of_Removal")
        self.dwaynas_kiss = Skill.GetID("Dwaynas_Kiss")
        self.unnatural_signet = Skill.GetID("Unnatural_Signet")
        self.toxic_chill = Skill.GetID("Toxic_Chill")
        self.discord = Skill.GetID("Discord")
        self.empathic_removal = Skill.GetID("Empathic_Removal")
        self.iron_palm = Skill.GetID("Iron_Palm")
        self.melandrus_resilience = Skill.GetID("Melandrus_Resilience")
        self.necrosis = Skill.GetID("Necrosis")
        self.peace_and_harmony = Skill.GetID("Peace_and_Harmony")
        self.purge_signet = Skill.GetID("Purge_Signet")
        self.resilient_weapon = Skill.GetID("Resilient_Weapon")
        self.gaze_from_beyond = Skill.GetID("Gaze_from_Beyond")
        self.spirit_burn = Skill.GetID("Spirit_Burn")
        self.signet_of_ghostly_might = Skill.GetID("Signet_of_Ghostly_Might")
        self.burning = Skill.GetID("Burning")
        self.blind = Skill.GetID("Blind")
        self.cracked_armor = Skill.GetID("Cracked_Armor")
        self.crippled = Skill.GetID("Crippled")
        self.dazed = Skill.GetID("Dazed")
        self.deep_wound = Skill.GetID("Deep_Wound")
        self.disease = Skill.GetID("Disease")
        self.poison = Skill.GetID("Poison")
        self.weakness = Skill.GetID("Weakness")
        self.comfort_animal = Skill.GetID("Comfort_Animal")
        self.heal_as_one = Skill.GetID("Heal_as_One")
        self.heroic_refrain = Skill.GetID("Heroic_Refrain")
        
    def Update(self, cached_data):
        self.in_aggro = cached_data.in_aggro
        self.is_targeting_enabled = cached_data.is_targeting_enabled
        self.is_combat_enabled = cached_data.is_combat_enabled
        self.is_skill_enabled = cached_data.is_skill_enabled
        

    def PrioritizeSkills(self):
        """
        Create a priority-based skill execution order.
        """
        #initialize skillbar
        original_skills = []
        for i in range(MAX_SKILLS):
            original_skills.append(self.SkillData(i+1))

        # Initialize the pointer and tracking list
        ptr = 0
        ptr_chk = [False] * MAX_SKILLS
        ordered_skills = []
        
        priorities = [
            SkillNature.Interrupt,
            SkillNature.Enchantment_Removal,
            SkillNature.Healing,
            SkillNature.Hex_Removal,
            SkillNature.Condi_Cleanse,
            SkillNature.EnergyBuff,
            SkillNature.Resurrection,
            SkillNature.Buff
        ]

        for priority in priorities:
            for i in range(ptr,MAX_SKILLS):
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
            for i in range(ptr,MAX_SKILLS):
                skill = original_skills[i]
                if not ptr_chk[i] and skill.custom_skill_data.SkillType == skill_type.value:
                    self.skill_order[ptr] = i
                    ptr_chk[i] = True
                    ptr += 1
                    ordered_skills.append(skill)

        combos = [3, 2, 1]  # Dual attack, off-hand attack, lead attack
        for combo in combos:
            for i in range(ptr,MAX_SKILLS):
                skill = original_skills[i]
                if not ptr_chk[i] and Skill.Data.GetCombo(skill.skill_id) == combo:
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
            
    def GetEnergyValues(self,agent_id):
        for i in range(MAX_NUM_PLAYERS):
            player_data = self.shared_memory_handler.get_player(i)
            if player_data and player_data["IsActive"] and player_data["PlayerID"] == agent_id:
                return player_data["Energy"]
        return 1.0 #default return full energy to prevent issues

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
            #if self.in_aggro:
            #    self.ChooseTarget(interact=True)
            self.aftercast_timer.Reset()

        return self.in_casting_routine
 
    def GetPartyTargetID(self):
        if not Party.IsPartyLoaded():
            return 0

        players = Party.GetPlayers()
        target = players[0].called_target_id

        if Agent.IsValid(target):
            return target  
        
        return 0 

    def SafeChangeTarget(self, target_id):
        if Agent.IsValid(target_id):
            Player.ChangeTarget(target_id)
            
    def SafeInteract(self, target_id):
        if Agent.IsValid(target_id):
            Player.Interact(target_id)


    def GetPartyTarget(self):
        party_target = self.GetPartyTargetID()
        if self.is_targeting_enabled and party_target != 0:
            current_target = Player.GetTargetID()
            if current_target != party_target:
                if Agent.IsLiving(party_target):
                    _, alliegeance = Agent.GetAllegiance(party_target)
                    if alliegeance != 'Ally' and alliegeance != 'NPC/Minipet' and self.is_combat_enabled:
                        ActionQueueManager().AddAction("ACTION", self.SafeChangeTarget, party_target)
                        return party_target
        return 0

    def get_combat_distance(self):
        return Range.Spellcast.value if self.in_aggro else Range.Earshot.value

    def GetAppropiateTarget(self, slot):
        v_target = 0

        if not self.is_targeting_enabled:
            return Player.GetTargetID()

        targeting_strict = self.skills[slot].custom_skill_data.Conditions.TargetingStrict
        target_allegiance = self.skills[slot].custom_skill_data.TargetAllegiance
        
        
        nearest_enemy = Routines.Agents.GetNearestEnemy(self.get_combat_distance())
        lowest_ally = TargetLowestAlly(filter_skill_id=self.skills[slot].skill_id)

        if self.skills[slot].skill_id == self.heroic_refrain:
            if not self.HasEffect(Player.GetAgentID(), self.heroic_refrain):
                return Player.GetAgentID()

        if target_allegiance == Skilltarget.Enemy:
            v_target = self.GetPartyTarget()
            if v_target == 0:
                v_target = nearest_enemy
        elif target_allegiance == Skilltarget.EnemyCaster:
            v_target = Routines.Agents.GetNearestEnemyCaster(self.get_combat_distance())
            if v_target == 0 and not targeting_strict:
                v_target =nearest_enemy
        elif target_allegiance == Skilltarget.EnemyMartial:
            v_target = Routines.Agents.GetNearestEnemyMartial(self.get_combat_distance())
            if v_target == 0 and not targeting_strict:
                v_target = nearest_enemy
        elif target_allegiance == Skilltarget.EnemyMartialMelee:
            v_target = Routines.Agents.GetNearestEnemyMelee(self.get_combat_distance())
            if v_target == 0 and not targeting_strict:
                v_target = nearest_enemy
        elif target_allegiance == Skilltarget.AllyMartialRanged:
            v_target = Routines.Agents.GetNearestEnemyRanged(self.get_combat_distance())
            if v_target == 0 and not targeting_strict:
                v_target = nearest_enemy
        elif target_allegiance == Skilltarget.Ally:
            v_target = lowest_ally
        elif target_allegiance == Skilltarget.AllyCaster:
            v_target = TargetLowestAllyCaster(filter_skill_id=self.skills[slot].skill_id)
            if v_target == 0 and not targeting_strict:
                v_target = lowest_ally
        elif target_allegiance == Skilltarget.AllyMartial:
            v_target = TargetLowestAllyMartial(filter_skill_id=self.skills[slot].skill_id)
            if v_target == 0 and not targeting_strict:
                v_target = lowest_ally
        elif target_allegiance == Skilltarget.AllyMartialMelee:
            v_target = TargetLowestAllyMelee(filter_skill_id=self.skills[slot].skill_id)
            if v_target == 0 and not targeting_strict:
                v_target = lowest_ally
        elif target_allegiance == Skilltarget.AllyMartialRanged:
            v_target = TargetLowestAllyRanged(filter_skill_id=self.skills[slot].skill_id)
            if v_target == 0 and not targeting_strict:
                v_target = lowest_ally
        elif target_allegiance == Skilltarget.OtherAlly:
            if self.skills[slot].custom_skill_data.Nature == SkillNature.EnergyBuff.value:
                v_target = TargetLowestAllyEnergy(other_ally=True, filter_skill_id=self.skills[slot].skill_id)
                #print("Energy Buff Target: ", RawAgentArray().get_name(v_target))
            else:
                v_target = TargetLowestAlly(other_ally=True, filter_skill_id=self.skills[slot].skill_id)
        elif target_allegiance == Skilltarget.Self:
            v_target = Player.GetAgentID()
        elif target_allegiance == Skilltarget.Pet:
            v_target = Party.Pets.GetPetID(Player.GetAgentID())
        elif target_allegiance == Skilltarget.DeadAlly:
            v_target = Routines.Agents.GetDeadAlly(Range.Spellcast.value)
        elif target_allegiance == Skilltarget.Spirit:
            v_target = Routines.Agents.GetNearestSpirit(Range.Spellcast.value)
        elif target_allegiance == Skilltarget.Minion:
            v_target = Routines.Agents.GetLowestMinion(Range.Spellcast.value)
        elif target_allegiance == Skilltarget.Corpse:
            v_target = Routines.Agents.GetNearestCorpse(Range.Spellcast.value)
        else:
            v_target = self.GetPartyTarget()
            if v_target == 0:
                v_target = nearest_enemy
        return v_target

    def IsPartyMember(self, agent_id):
        for i in range(MAX_NUM_PLAYERS):
            player_data = self.shared_memory_handler.get_player(i)
            if player_data and player_data["IsActive"] and player_data["PlayerID"] == agent_id:
                return True
            
        allegiance , _ = Agent.GetAllegiance(agent_id)
        if allegiance == Allegiance.SpiritPet.value and not Agent.IsSpawned(agent_id):
            return True
        
        return False
        
    def HasEffect(self, agent_id, skill_id, exact_weapon_spell=False):
        """
        alliegeance, _ = Agent.GetAllegiance(agent_id)
        
        if alliegeance == Allegiance.NpcMinipet:
            return True
        """
        result = False
        if self.IsPartyMember(agent_id):
            player_buffs = self.shared_memory_handler.get_agent_buffs(agent_id)
            for buff in player_buffs:
                if buff == skill_id:
                    result = True
        else:
            result = Effects.BuffExists(agent_id, skill_id) or Effects.EffectExists(agent_id, skill_id)

        if not result and not exact_weapon_spell:
           skilltype, _ = Skill.GetType(skill_id)
           if skilltype == SkillType.WeaponSpell.value:
               result = Agent.IsWeaponSpelled(agent_id)

        return result


    def AreCastConditionsMet(self, slot, vTarget):
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
                life = Agent.GetHealth(Player.GetAgentID()) < Conditions.LessLife
                return life and Agent.IsConditioned(vTarget)

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

        if Conditions.IsAlive:
            if Agent.IsAlive(vTarget):
                number_of_features += 1

        if Conditions.HasCondition:
            if Agent.IsConditioned(vTarget):
                number_of_features += 1

        if Conditions.HasBleeding:
            if Agent.IsBleeding(vTarget):
                number_of_features += 1

        if Conditions.HasBlindness:
            if self.HasEffect(vTarget, self.blind):
                number_of_features += 1

        if Conditions.HasBurning:
            if self.HasEffect(vTarget, self.burning):
                number_of_features += 1

        if Conditions.HasCrackedArmor:
            if self.HasEffect(vTarget, self.cracked_armor):
                number_of_features += 1
          
        if Conditions.HasCrippled:
            if Agent.IsCrippled(vTarget):
                number_of_features += 1
                
        if Conditions.HasDazed:
            if self.HasEffect(vTarget, self.dazed):
                number_of_features += 1
          
        if Conditions.HasDeepWound:
            if self.HasEffect(vTarget, self.deep_wound):
                number_of_features += 1
                
        if Conditions.HasDisease:
            if self.HasEffect(vTarget, self.disease):
                number_of_features += 1

        if Conditions.HasPoison:
            if Agent.IsPoisoned(vTarget):
                number_of_features += 1

        if Conditions.HasWeakness:
            if self.HasEffect(vTarget, self.weakness):
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
            if Player.GetAgentID() == vTarget:
                buff_list = self.shared_memory_handler.get_agent_buffs(vTarget)
                for buff in buff_list:
                    skill_type, _ = Skill.GetType(buff)
                    if skill_type == SkillType.Enchantment.value:
                        _, profession = Skill.GetProfession(buff)
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
                buff_list = self.shared_memory_handler.get_agent_buffs(vTarget)
                for buff in buff_list:
                    skill_type, _ = Skill.GetType(buff)
                    if skill_type == SkillType.Chant.value:
                        if len(Conditions.ChantList) == 0:
                            number_of_features += 1
                        else:
                            if buff in Conditions.ChantList:
                                number_of_features += 1
                                break
                                
        if Conditions.IsCasting:
            if Agent.IsCasting(vTarget):
                casting_skill_id = Agent.GetCastingSkill(vTarget)
                if Skill.Data.GetActivation(casting_skill_id) >= 0.250:
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
            if self.IsPartyMember(vTarget):
                for i in range(MAX_NUM_PLAYERS):
                    player_data = self.shared_memory_handler.get_player(i)
                    if player_data and player_data["IsActive"] and player_data["PlayerID"] == vTarget:
                        if player_data["Energy"] < Conditions.LessEnergy:
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
                    
        if self.skills[slot].custom_skill_data.SkillType == SkillType.PetAttack.value:
            pet_id = Party.Pets.GetPetID(Player.GetAgentID())
            if Agent.IsDead(pet_id):
                return False
            
            pet_attack_list = [Skill.GetID("Bestial_Mauling"),
                               Skill.GetID("Bestial_Pounce"),
                               Skill.GetID("Brutal_Strike"),
                               Skill.GetID("Disrupting_Lunge"),
                               Skill.GetID("Enraged_Lunge"),
                               Skill.GetID("Feral_Lunge"),
                               Skill.GetID("Ferocious_Strike"),
                               Skill.GetID("Maiming_Strike"),
                               Skill.GetID("Melandrus_Assault"),
                               Skill.GetID("Poisonous_Bite"),
                               Skill.GetID("Pounce"),
                               Skill.GetID("Predators_Pounce"),
                               Skill.GetID("Savage_Pounce"),
                               Skill.GetID("Scavenger_Strike")
                               ]
            
            for skill_id in pet_attack_list:
                if self.skills[slot].skill_id == skill_id:
                    if self.HasEffect(pet_id,self.skills[slot].skill_id ):
                        return False
            

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
        # Check if the player is already casting
         # Validate target
        v_target = self.GetAppropiateTarget(slot)
        if v_target is None or v_target == 0:
            self.in_casting_routine = False
            return False, 0

        if Agent.IsCasting(Player.GetAgentID()):
            self.in_casting_routine = False
            return False, v_target
        if Agent.GetCastingSkill(Player.GetAgentID()) != 0:
            self.in_casting_routine = False
            return False, v_target
        if SkillBar.GetCasting() != 0:
            self.in_casting_routine = False
            return False, v_target
        # Check if no skill is assigned to the slot
        if self.skills[slot].skill_id == 0:
            self.in_casting_routine = False
            return False, v_target
        # Check if the skill is recharging
        if self.skills[slot].skillbar_data.recharge != 0:
            self.in_casting_routine = False
            return False, v_target
        
        # Check if there is enough energy
        current_energy = self.GetEnergyValues(Player.GetAgentID()) * Agent.GetMaxEnergy(Player.GetAgentID())
        if current_energy < Routines.Checks.Skills.GetEnergyCostWithEffects(self.skills[slot].skill_id,Player.GetAgentID()):  
        #if current_energy < Skill.Data.GetEnergyCost(self.skills[slot].skill_id):
            self.in_casting_routine = False
            return False, v_target
        # Check if there is enough health
        current_hp = Agent.GetHealth(Player.GetAgentID())
        target_hp = self.skills[slot].custom_skill_data.Conditions.SacrificeHealth
        health_cost = Skill.Data.GetHealthCost(self.skills[slot].skill_id)
        if (current_hp < target_hp) and health_cost > 0:
            self.in_casting_routine = False
            return False, v_target
     
        # Check if there is enough adrenaline
        adrenaline_required = Skill.Data.GetAdrenaline(self.skills[slot].skill_id)
        if adrenaline_required > 0 and self.skills[slot].skillbar_data.adrenaline_a < adrenaline_required:
            self.in_casting_routine = False
            return False, v_target

        """
        # Check overcast conditions
        current_overcast = Agent.GetOvercast(Player.GetAgentID())
        overcast_target = self.skills[slot].custom_skill_data.Conditions.Overcast
        skill_overcast = Skill.Data.GetOvercast(self.skills[slot].skill_id)
        if (current_overcast >= overcast_target) and (skill_overcast > 0):
            self.in_casting_routine = False
            return False, 0
        """
                
        # Check combo conditions
        combo_type = Skill.Data.GetCombo(self.skills[slot].skill_id)
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
        
        if self.SpiritBuffExists(self.skills[slot].skill_id):
            self.in_casting_routine = False
            return False, v_target

        if self.HasEffect(v_target,self.skills[slot].skill_id):
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

        target_id = Player.GetTargetID()
        if Agent.IsValid(target_id) or target_id == 0:
            _, target_aliegance = Agent.GetAllegiance(target_id)
        
            if target_aliegance != 'Enemy' or target_id == 0:      
                nearest = Routines.Agents.GetNearestEnemy(self.get_combat_distance())
                called_target = self.GetPartyTarget()

                attack_target = 0

                if Agent.IsValid(called_target):
                    attack_target = called_target
                elif Agent.IsValid(nearest):
                    attack_target = nearest
                else:
                    return False

                ActionQueueManager().AddAction("ACTION", self.SafeChangeTarget, attack_target)
                ActionQueueManager().AddAction("ACTION", self.SafeInteract, attack_target)
                return True
            else:
                ActionQueueManager().AddAction("ACTION", self.SafeInteract, target_id)
                return True
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
         
         
        is_read_to_cast, target_agent_id = self.IsReadyToCast(slot)
 
        if not is_read_to_cast:
            self.AdvanceSkillPointer()
            return False
        
        is_ooc_skill = self.IsOOCSkill(slot)

        if ooc and not is_ooc_skill:
            self.AdvanceSkillPointer()
            return False

        if target_agent_id == 0:
            self.AdvanceSkillPointer()
            return False

        if not Agent.IsLiving(target_agent_id):
            return False
            
        self.in_casting_routine = True

        self.aftercast = Skill.Data.GetActivation(skill_id) * 1000
        self.aftercast += Skill.Data.GetAftercast(skill_id) * 1000 #750
        #self.aftercast += 150 #manually setting a 50ms delay to test issues with pinghandler
        self.aftercast += self.ping_handler.GetCurrentPing()

        self.aftercast_timer.Reset()
        ActionQueueManager().AddAction("ACTION", SkillBar.UseSkill, self.skill_order[self.skill_pointer]+1, target_agent_id)
        self.ResetSkillPointer()
        return True
