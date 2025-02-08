from Py4GWCoreLib import *
from .custom_skill import *
from .types import *
from .targetting import *
from .utils import *

MAX_SKILLS = 8
custom_skill_data_handler = CustomSkillClass()

SPIRIT_BUFF_MAP = {
    2882: Skill.GetID("Frozen Soil"),
    4218: Skill.GetID("Life"),
    4227: Skill.GetID("Bloodsong"),
    4229: Skill.GetID("Signet of Spirits"),  # anger
    4230: Skill.GetID("Signet of Spirits"),  # hate
    4231: Skill.GetID("Signet of Spirits"),  # suffering
    5720: Skill.GetID("Anguish"),
    4225: Skill.GetID("Disenchantment"),
    4221: Skill.GetID("Dissonance"),
    4214: Skill.GetID("Pain"),
    4213: Skill.GetID("Shadowsong"),
    4228: Skill.GetID("Wanderlust"),
    5723: Skill.GetID("Vampirism"),
    5854: Skill.GetID("Agony"),
    4217: Skill.GetID("Displacement"),
    4222: Skill.GetID("Earthbind"),
    5721: Skill.GetID("Empowerment"),
    4219: Skill.GetID("Preservation"),
    5719: Skill.GetID("Recovery"),
    4220: Skill.GetID("Recuperation"),
    5853: Skill.GetID("Rejuvenation"),
    4223: Skill.GetID("Shelter"),
    4216: Skill.GetID("Soothing"),
    4224: Skill.GetID("Union"),
    4215: Skill.GetID("Destruction"),
    4226: Skill.GetID("Restoration"),
    2884: Skill.GetID("Winds"),
    4239: Skill.GetID("Brambles"),
    4237: Skill.GetID("Conflagration"),
    2885: Skill.GetID("Energizing Wind"),
    4236: Skill.GetID("Equinox"),
    2876: Skill.GetID("Edge of Extinction"),
    4238: Skill.GetID("Famine"),
    2883: Skill.GetID("Favorable Winds"),
    2878: Skill.GetID("Fertile Season"),
    2877: Skill.GetID("Greater Conflagration"),
    5715: Skill.GetID("Infuriating Heat"),
    4232: Skill.GetID("Lacerate"),
    2888: Skill.GetID("Muddy Terrain"),
    2887: Skill.GetID("Nature's Renewal"),
    4234: Skill.GetID("Pestilence"),
    2881: Skill.GetID("Predatory Season"),
    2880: Skill.GetID("Primal Echoes"),
    2886: Skill.GetID("Quickening Zephyr"),
    5718: Skill.GetID("Quicksand"),
    5717: Skill.GetID("Roaring Winds"),
    2879: Skill.GetID("Symbiosis"),
    5716: Skill.GetID("Toxicity"),
    4235: Skill.GetID("Tranquility"),
    2874: Skill.GetID("Winter"),
    2875: Skill.GetID("Winnowing"),
}

class CombatClass:
    global MAX_SKILLS, custom_skill_data_handler

    class SkillData:
        def __init__(self, slot):
            self.skill_id = SkillBar.GetSkillIDBySlot(slot)  # slot is 1 based
            self.skillbar_data = SkillBar.GetSkillData(slot)  # Fetch additional data from the skill bar
            self.custom_skill_data = custom_skill_data_handler.get_skill(self.skill_id)  # Retrieve custom skill data

    def __init__(self):
        from .globals import HeroAI_varsClass
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
        self.shared_memory_handler = HeroAI_varsClass().shared_memory_handler
        
        self.in_aggro = False
        self.is_targetting_enabled = False
        self.is_combat_enabled = False
        self.is_skill_enabled = []
        
        self.nearest_enemy = TargetNearestEnemy()
        self.lowest_ally = TargetLowestAlly()
        self.lowest_ally_energy = TargetLowestAllyEnergy()
        self.nearest_npc = TargetNearestNpc()
        self.nearest_item = TargetNearestItem()
        self.nearest_spirit = TargetNearestSpirit()
        self.lowest_minion = TargetLowestMinion()
        self.nearest_corpse = TargetNearestCorpse()
        
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
        
    def Update(self, cached_data):
        self.in_aggro = cached_data.in_aggro
        self.is_targetting_enabled = cached_data.is_targetting_enabled
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
        

    def GetOrderedSkill(self, index):
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

    def IsSkillReady(self, slot):
        if self.skills[slot].skill_id == 0:
            return False

        if self.skills[slot].skillbar_data.recharge != 0:
            return False
        return True and self.is_skill_enabled[slot]
        
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

        if target is None or target == 0:
            return 0
        else:
            return target   


    def GetPartyTarget(self):
        party_number = Party.GetOwnPartyNumber()
        party_target = self.GetPartyTargetID()
        if self.is_targetting_enabled and party_target != 0:
            current_target = Player.GetTargetID()
            if current_target != party_target:
                if Agent.IsLiving(party_target):
                    _, alliegeance = Agent.GetAlliegance(party_target)
                    if alliegeance != 'Ally' and alliegeance != 'NPC/Minipet' and self.is_combat_enabled:
                        Player.ChangeTarget(party_target)
                        #Player.Interact(party_target)
                        return party_target
        return 0

    def get_combat_distance(self):
        return Range.Spellcast.value if self.in_aggro else Range.Earshot.value

    def GetAppropiateTarget(self, slot):
        v_target = 0

        party_number = Party.GetOwnPartyNumber()
        if not self.is_targetting_enabled:
            return Player.GetTargetID()

        targeting_strict = self.skills[slot].custom_skill_data.Conditions.TargetingStrict
        target_allegiance = self.skills[slot].custom_skill_data.TargetAllegiance

        if target_allegiance == Skilltarget.Enemy.value:
            v_target = self.GetPartyTarget()
            if v_target == 0:
                v_target = TargetNearestEnemy(self.get_combat_distance())
        elif target_allegiance == Skilltarget.EnemyCaster.value:
            v_target = TargetNearestEnemyCaster()
            if v_target == 0 and not targeting_strict:
                v_target = TargetNearestEnemy(self.get_combat_distance())
        elif target_allegiance == Skilltarget.EnemyMartial.value:
            v_target = TargetNearestEnemyMartial(self.get_combat_distance())
            if v_target == 0 and not targeting_strict:
                v_target = TargetNearestEnemy(self.get_combat_distance())
        elif target_allegiance == Skilltarget.EnemyMartialMelee.value:
            v_target = TargetNearestEnemyMelee(self.get_combat_distance())
            if v_target == 0 and not targeting_strict:
                v_target = TargetNearestEnemy(self.get_combat_distance())
        elif target_allegiance == Skilltarget.AllyMartialRanged.value:
            v_target = TargetNearestEnemyRanged(self.get_combat_distance())
            if v_target == 0 and not targeting_strict:
                v_target = TargetNearestEnemy(self.get_combat_distance())
        elif target_allegiance == Skilltarget.Ally.value:
            v_target = TargetLowestAlly(filter_skill_id=self.skills[slot].skill_id)
        elif target_allegiance == Skilltarget.AllyCaster.value:
            v_target = TargetLowestAllyCaster(filter_skill_id=self.skills[slot].skill_id)
            if v_target == 0 and not targeting_strict:
                v_target = TargetLowestAlly(filter_skill_id=self.skills[slot].skill_id)
        elif target_allegiance == Skilltarget.AllyMartial.value:
            v_target = TargetLowestAllyMartial(filter_skill_id=self.skills[slot].skill_id)
            if v_target == 0 and not targeting_strict:
                v_target = TargetLowestAlly(filter_skill_id=self.skills[slot].skill_id)
        elif target_allegiance == Skilltarget.AllyMartialMelee.value:
            v_target = TargetLowestAllyMelee(filter_skill_id=self.skills[slot].skill_id)
            if v_target == 0 and not targeting_strict:
                v_target = TargetLowestAlly(filter_skill_id=self.skills[slot].skill_id)
        elif target_allegiance == Skilltarget.AllyMartialRanged.value:
            v_target = TargetLowestAllyRanged(filter_skill_id=self.skills[slot].skill_id)
            if v_target == 0 and not targeting_strict:
                v_target = TargetLowestAlly(filter_skill_id=self.skills[slot].skill_id)
        elif target_allegiance == Skilltarget.OtherAlly.value:
            if self.skills[slot].custom_skill_data.Nature == SkillNature.EnergyBuff.value:
                v_target = TargetLowestAllyEnergy(other_ally=True, filter_skill_id=self.skills[slot].skill_id)
            else:
                v_target = TargetLowestAlly(other_ally=True, filter_skill_id=self.skills[slot].skill_id)
        elif target_allegiance == Skilltarget.Self.value:
            v_target = Player.GetAgentID()
        elif target_allegiance == Skilltarget.DeadAlly.value:
            v_target = TargetDeadAllyInAggro()
        elif target_allegiance == Skilltarget.Spirit.value:
            v_target = TargetNearestSpirit()
        elif target_allegiance == Skilltarget.Minion.value:
            v_target = TargetLowestMinion()
        elif target_allegiance == Skilltarget.Corpse.value:
            v_target = TargetNearestCorpse()
        else:
            v_target = self.GetPartyTarget()
            if v_target == 0:
                v_target = TargetNearestEnemy()
        return v_target

    def IsPartyMember(self, agent_id):
        for i in range(MAX_NUM_PLAYERS):
            player_data = self.shared_memory_handler.get_player(i)
            if player_data["IsActive"] and player_data["PlayerID"] == agent_id:
                return True
        
        return False
        
    def HasEffect(self, agent_id, skill_id, exact_weapon_spell=False):
        result = False
        if self.IsPartyMember(agent_id):
            player_buffs = self.shared_memory_handler.get_agent_buffs(agent_id)
            for buff in player_buffs:
                #Py4GW.Console.Log("HasEffect-player_buff", f"IsPartyMember: {self.IsPartyMember(agent_id)} agent ID: {agent_id}, effect {skill_id} buff {buff}", Py4GW.Console.MessageType.Info)
                if buff == skill_id:
                    result = True
        else:
            result = Effects.BuffExists(agent_id, skill_id) or Effects.EffectExists(agent_id, skill_id)

        #Py4GW.Console.Log("HasEffect", f"IsPartyMember: {self.IsPartyMember(agent_id)} agent ID: {agent_id}, effect {skill_id} result {result}", Py4GW.Console.MessageType.Info)
       
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
                return GetEnergyValues(Player.GetAgentID()) < Conditions.LessEnergy
        
            if (self.skills[slot].skill_id == self.essence_strike):
                energy = GetEnergyValues(Player.GetAgentID()) < Conditions.LessEnergy
                return energy and (TargetNearestSpirit() != 0)

            if (self.skills[slot].skill_id == self.glowing_signet):
                energy= GetEnergyValues(Player.GetAgentID()) < Conditions.LessEnergy
                return energy and self.HasEffect(vTarget, self.burning)

            if (self.skills[slot].skill_id == self.clamor_of_souls):
                energy = GetEnergyValues(Player.GetAgentID()) < Conditions.LessEnergy
                weapon_type, _ = Agent.GetWeaponType(Player.GetAgentID())
                return energy and weapon_type == 0

            if (self.skills[slot].skill_id == self.waste_not_want_not):
                energy= GetEnergyValues(Player.GetAgentID()) < Conditions.LessEnergy
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
                return True if TargetNearestSpirit() != 0 else False

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
                    if player_data["IsActive"] and player_data["PlayerID"] == vTarget:
                        if player_data["Energy"] < Conditions.LessEnergy:
                            number_of_features += 1
            else:
                number_of_features += 1 #henchmen, allies, pets or something else thats not reporting energy

        if Conditions.Overcast != 0:
            if Player.GetAgentID() == vTarget:
                if Agent.GetOvercast(vTarget) < Conditions.Overcast:
                    number_of_features += 1

        #Py4GW.Console.Log("AreCastConditionsMet", f"feature count: {feature_count}, No of features {number_of_features}", Py4GW.Console.MessageType.Info)
        
        if feature_count == number_of_features:
            return True

        return False


    def SpiritBuffExists(self,skill_id):
        spirit_array = AgentArray.GetSpiritPetArray()
        distance = Range.Earshot.value
        spirit_array = AgentArray.Filter.ByDistance(spirit_array, Player.GetXY(), distance)
        spirit_array = AgentArray.Filter.ByCondition(spirit_array, lambda agent_id: Agent.IsAlive(agent_id))

        for spirit_id in spirit_array:
            spirit_model_id = Agent.GetPlayerNumber(spirit_id)
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
        current_energy = GetEnergyValues(Player.GetAgentID()) * Agent.GetMaxEnergy(Player.GetAgentID())
        if current_energy < Skill.Data.GetEnergyCost(self.skills[slot].skill_id):
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
        own_party_number = Party.GetOwnPartyNumber()
        
        if not self.is_targetting_enabled:
            return False

        if not self.in_aggro:
            return False

        _, target_aliegance = Agent.GetAlliegance(Player.GetTargetID())
        
        if Player.GetTargetID() == 0 or (target_aliegance != 'Enemy'):
                            
            nearest = TargetNearestEnemy()
            called_target = self.GetPartyTarget()

            attack_target = 0

            if called_target != 0:
                attack_target = called_target
            elif nearest != 0:
                attack_target = nearest
            else:
                return False

            Player.ChangeTarget(attack_target)
            return True
            """
            if self.is_combat_enabled:
                weapon_type, _ = Agent.GetWeaponType(Player.GetAgentID())
                if weapon_type != 0 and interact:

                    Player.Interact(attack_target)
                    return True
            """
        else:
            target_id = Player.GetTargetID()
            if not Agent.IsLiving(target_id):
                return

            _, alliegeance = Agent.GetAlliegance(target_id)
            if alliegeance == 'Enemy' and self.is_combat_enabled:
                Player.Interact(Player.GetTargetID())


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
        self.aftercast += Skill.Data.GetAftercast(skill_id) * 1000
        self.aftercast += self.ping_handler.GetCurrentPing()

        self.aftercast_timer.Reset()
        SkillBar.UseSkill(self.skill_order[self.skill_pointer]+1, target_agent_id)
        self.AdvanceSkillPointer()
        return True