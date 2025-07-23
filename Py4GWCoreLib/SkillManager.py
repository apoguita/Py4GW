from HeroAI.custom_skill import CustomSkillClass
from HeroAI.types import SkillType,SkillNature, Skilltarget
from .Agent import Agent
from.AgentArray import AgentArray
from .Player import Player
from .Skill import Skill
from .Skillbar import SkillBar
from .Party import Party
from typing import Optional
from .Py4GWcorelib import ThrottledTimer
from .Py4GWcorelib import ActionQueueManager
from .Py4GWcorelib import Console
from .Py4GWcorelib import ConsoleLog
from .Py4GWcorelib import *
from .enums import Range
from .Routines import Routines
from .Effect import Effects
from HeroAI.cache_data import CacheData
from HeroAI.players import *

            
class SkillIDS:
    def __init__(self):
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
            
SPIRIT_BUFF_MAP = {
            2882: Skill.GetID("Frozen_Soil"),
            4218: Skill.GetID("Life"),
            4227: Skill.GetID("Bloodsong"),
            4229: Skill.GetID("Signet_of_Spirits"),  # anger
            4230: Skill.GetID("Signet_of_Spirits"),  # hate
            4231: Skill.GetID("Signet_of_Spirits"),  # suffering
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
            2876: Skill.GetID("Edge_of_Extinction"),
            4238: Skill.GetID("Famine"),
            2883: Skill.GetID("Favorable_Winds"),
            2878: Skill.GetID("Fertile_Season"),
            2877: Skill.GetID("Greater_Conflagration"),
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

MAX_SKILLS = 8
MAX_NUM_PLAYERS = 8


class SkillManager:
    class Autocombat: 
        custom_skill_data_handler = CustomSkillClass()
        class _SkillData:
            def __init__(self, slot):
                self.skill_id = SkillBar.GetSkillIDBySlot(slot)  # slot is 1 based
                self.skillbar_data = SkillBar.GetSkillData(slot)  # Fetch additional data from the skill bar
                self.custom_skill_data = SkillManager.Autocombat.custom_skill_data_handler.get_skill(self.skill_id)  # Retrieve custom skill data
                                
        def __init__(self):
            import Py4GW
            self.skill_id = SkillIDS()
            self.skills: list[SkillManager.Autocombat._SkillData] = []
            self.skill_order = [0] * MAX_SKILLS
            self.skill_pointer = 0
            self.aftercast_timer = ThrottledTimer()
            self.stay_alert_timer = ThrottledTimer(2500)
            self.game_throttle_timer = ThrottledTimer(75)
            self.auto_attack_timer = ThrottledTimer(750)
            self.ping_handler = Py4GW.PingHandler()
            self.in_casting_routine = True
            self.aggressive_enemies_only = False

        def SetAggressiveEnemiesOnly(self, state, log_action=False):
            self.aggressive_enemies_only = state
            if log_action:
                if state:
                    ConsoleLog("Autocombat", f"Fighting aggressive enemies only.", Console.MessageType.Info)
                else:
                    ConsoleLog("Autocombat", f"Fighting all enemies", Console.MessageType.Info)

        def PrioritizeSkills(self):
            """
            Create a priority-based skill execution order.
            """
            #initialize skillbar
            original_skills = []
            for i in range(MAX_SKILLS):
                original_skills.append(self._SkillData(i+1))

            # Initialize the pointer and tracking list
            ptr = 0
            ptr_chk = [False] * MAX_SKILLS
            ordered_skills = []
            
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
        
        def GetOrderedSkill(self, index:int)-> Optional[_SkillData]:
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
                
        def GetEnergyValues(self,agent_id):
            agent_energy = Agent.GetEnergy(agent_id)
            if agent_energy <= 0:
                return 1.0 #default return full energy to prevent issues
            
            return agent_energy

        def IsSkillReady(self, slot):
            if self.skills[slot].skill_id == 0:
                return False
            if self.skills[slot].skillbar_data.recharge != 0:
                return False
            return True
        
        def InCastingRoutine(self):
            if self.aftercast_timer.IsExpired():
                self.in_casting_routine = False
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
            party_target = self.GetPartyTargetID()
            if party_target != 0:
                current_target = Player.GetTargetID()
                if current_target != party_target:
                    if Agent.IsLiving(party_target):
                        _, alliegeance = Agent.GetAllegiance(party_target)
                        if alliegeance != 'Ally' and alliegeance != 'NPC/Minipet':
                            ActionQueueManager().AddAction("ACTION", Player.ChangeTarget, party_target)
                            return party_target
            return 0
        
        def InAggro(self):
            if self.stay_alert_timer.IsExpired():
                in_danger = Routines.Checks.Agents.InDanger(Range.Earshot, self.aggressive_enemies_only)
            else:
                in_danger = Routines.Checks.Agents.InDanger(Range.Spellcast, self.aggressive_enemies_only)
                
            if in_danger:
                self.stay_alert_timer.Reset()
                return True
                
        
        def get_combat_distance(self):
            return Range.Spellcast.value if self.InAggro() else Range.Earshot.value
        
        def GetAppropiateTarget(self, slot):
            from HeroAI.targeting import (
                TargetLowestAlly, 
                TargetLowestAllyCaster, 
                TargetLowestAllyMartial, 
                TargetLowestAllyMelee, 
                TargetLowestAllyRanged, 
                TargetLowestAllyEnergy,
            )
            
            v_target = 0

            targeting_strict = self.skills[slot].custom_skill_data.Conditions.TargetingStrict
            target_allegiance = self.skills[slot].custom_skill_data.TargetAllegiance
            
            nearest_enemy = Routines.Agents.GetNearestEnemy(self.get_combat_distance())
            lowest_ally = TargetLowestAlly(filter_skill_id=self.skills[slot].skill_id)

            if target_allegiance == Skilltarget.Enemy:
                v_target = self.GetPartyTarget()
                if v_target == 0:
                    v_target = nearest_enemy
            elif target_allegiance == Skilltarget.EnemyCaster:
                v_target = Routines.Agents.GetNearestEnemyCaster(self.get_combat_distance(), self.aggressive_enemies_only)
                if v_target == 0 and not targeting_strict:
                    v_target =nearest_enemy
            elif target_allegiance == Skilltarget.EnemyMartial:
                v_target = Routines.Agents.GetNearestEnemyMartial(self.get_combat_distance(), self.aggressive_enemies_only)
                if v_target == 0 and not targeting_strict:
                    v_target = nearest_enemy
            elif target_allegiance == Skilltarget.EnemyMartialMelee:
                v_target = Routines.Agents.GetNearestEnemyMelee(self.get_combat_distance(), self.aggressive_enemies_only)
                if v_target == 0 and not targeting_strict:
                    v_target = nearest_enemy
            elif target_allegiance == Skilltarget.AllyMartialRanged:
                v_target = Routines.Agents.GetNearestEnemyRanged(self.get_combat_distance(), self.aggressive_enemies_only)
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
                if self.skills[slot].custom_skill_data.Nature == SkillNature.EnergyBuff:
                    v_target = TargetLowestAllyEnergy(other_ally=True, filter_skill_id=self.skills[slot].skill_id)
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
            players = Party.GetPlayers()
            for player in players:
                player_agent_id = Party.Players.GetAgentIDByLoginNumber(player.login_number)
                if player_agent_id == agent_id:
                    return True
            return False
        
        def HasEffect(self, agent_id, skill_id, exact_weapon_spell=False):
            result = False
            result = Effects.BuffExists(agent_id, skill_id) or Effects.EffectExists(agent_id, skill_id)

            if not result and not exact_weapon_spell:
                skilltype, _ = Skill.GetType(skill_id)
                if skilltype == SkillType.WeaponSpell.value:
                    result = Agent.IsWeaponSpelled(agent_id)

            return result
            
        def GetAgentBuffList(self, agent_id):
                result_list = []
                buff_list = Effects.GetBuffs(agent_id)
                for buff in buff_list:
                    result_list.append(buff.skill_id)
                        
                effect_list = Effects.GetEffects(agent_id)
                for effect in effect_list:
                    result_list.append(effect.skill_id)    
                return result_list
                        
        def AreCastConditionsMet(self, slot, vTarget):
            number_of_features = 0
            feature_count = 0

            Conditions = self.skills[slot].custom_skill_data.Conditions

            """ Check if the skill is a resurrection skill and the target is dead """
            if self.skills[slot].custom_skill_data.Nature == SkillNature.Resurrection.value:
                return True if Agent.IsDead(vTarget) else False

            if self.skills[slot].custom_skill_data.Conditions.UniqueProperty:
                """ check all UniqueProperty skills """
                if (self.skills[slot].skill_id == self.skill_id.energy_drain or 
                    self.skills[slot].skill_id == self.skill_id.energy_tap or
                    self.skills[slot].skill_id == self.skill_id.ether_lord 
                    ):
                    return self.GetEnergyValues(Player.GetAgentID()) < Conditions.LessEnergy
            
                if (self.skills[slot].skill_id == self.skill_id.essence_strike):
                    energy = self.GetEnergyValues(Player.GetAgentID()) < Conditions.LessEnergy
                    return energy and (Routines.Agents.GetNearestSpirit(Range.Spellcast.value) != 0)

                if (self.skills[slot].skill_id == self.skill_id.glowing_signet):
                    energy= self.GetEnergyValues(Player.GetAgentID()) < Conditions.LessEnergy
                    return energy and self.HasEffect(vTarget, self.skill_id.burning)

                if (self.skills[slot].skill_id == self.skill_id.clamor_of_souls):
                    energy = self.GetEnergyValues(Player.GetAgentID()) < Conditions.LessEnergy
                    weapon_type, _ = Agent.GetWeaponType(Player.GetAgentID())
                    return energy and weapon_type == 0

                if (self.skills[slot].skill_id == self.skill_id.waste_not_want_not):
                    energy= self.GetEnergyValues(Player.GetAgentID()) < Conditions.LessEnergy
                    return energy and not Agent.IsCasting(vTarget) and not Agent.IsAttacking(vTarget)

                if (self.skills[slot].skill_id == self.skill_id.mend_body_and_soul):
                    life = Agent.GetHealth(Player.GetAgentID()) < Conditions.LessLife
                    return life and Agent.IsConditioned(vTarget)

                if (self.skills[slot].skill_id == self.skill_id.grenths_balance):
                    life = Agent.GetHealth(Player.GetAgentID()) < Conditions.LessLife
                    return life and Agent.GetHealth(Player.GetAgentID()) < Agent.GetHealth(vTarget)

                if (self.skills[slot].skill_id == self.skill_id.deaths_retreat):
                    return Agent.GetHealth(Player.GetAgentID()) < Agent.GetHealth(vTarget)

                if (self.skills[slot].skill_id == self.skill_id.plague_sending or
                    self.skills[slot].skill_id == self.skill_id.plague_signet or
                    self.skills[slot].skill_id == self.skill_id.plague_touch
                    ):
                    return Agent.IsConditioned(Player.GetAgentID())

                if (self.skills[slot].skill_id == self.skill_id.golden_fang_strike or
                    self.skills[slot].skill_id == self.skill_id.golden_fox_strike or
                    self.skills[slot].skill_id == self.skill_id.golden_lotus_strike or
                    self.skills[slot].skill_id == self.skill_id.golden_phoenix_strike or
                    self.skills[slot].skill_id == self.skill_id.golden_skull_strike
                    ):
                    return Agent.IsEnchanted(Player.GetAgentID())

                if (self.skills[slot].skill_id == self.skill_id.brutal_weapon):
                    return not Agent.IsEnchanted(Player.GetAgentID())

                if (self.skills[slot].skill_id == self.skill_id.signet_of_removal):
                    return not Agent.IsEnchanted(vTarget) and Agent.IsConditioned(vTarget)

                if (self.skills[slot].skill_id == self.skill_id.dwaynas_kiss or
                    self.skills[slot].skill_id == self.skill_id.unnatural_signet or
                    self.skills[slot].skill_id == self.skill_id.toxic_chill
                    ):
                    return Agent.IsHexed(vTarget) or Agent.IsEnchanted(vTarget)

                if (self.skills[slot].skill_id == self.skill_id.discord):
                    return (Agent.IsHexed(vTarget) and Agent.IsConditioned(vTarget)) or (Agent.IsEnchanted(vTarget))

                if (self.skills[slot].skill_id == self.skill_id.empathic_removal or
                    self.skills[slot].skill_id == self.skill_id.iron_palm or
                    self.skills[slot].skill_id == self.skill_id.melandrus_resilience or
                    self.skills[slot].skill_id == self.skill_id.necrosis or
                    self.skills[slot].skill_id == self.skill_id.peace_and_harmony or
                    self.skills[slot].skill_id == self.skill_id.purge_signet or
                    self.skills[slot].skill_id == self.skill_id.resilient_weapon
                    ):
                    return Agent.IsHexed(vTarget) or Agent.IsConditioned(vTarget)

                if (self.skills[slot].skill_id == self.skill_id.gaze_from_beyond or
                    self.skills[slot].skill_id == self.skill_id.spirit_burn or
                    self.skills[slot].skill_id == self.skill_id.signet_of_ghostly_might
                    ):
                    return True if Routines.Agents.GetNearestSpirit(Range.Spellcast.value) != 0 else False

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
                if self.HasEffect(vTarget, self.skill_id.blind):
                    number_of_features += 1

            if Conditions.HasBurning:
                if self.HasEffect(vTarget, self.skill_id.burning):
                    number_of_features += 1

            if Conditions.HasCrackedArmor:
                if self.HasEffect(vTarget, self.skill_id.cracked_armor):
                    number_of_features += 1
            
            if Conditions.HasCrippled:
                if Agent.IsCrippled(vTarget):
                    number_of_features += 1
                    
            if Conditions.HasDazed:
                if self.HasEffect(vTarget, self.skill_id.dazed):
                    number_of_features += 1
            
            if Conditions.HasDeepWound:
                if self.HasEffect(vTarget, self.skill_id.deep_wound):
                    number_of_features += 1
                    
            if Conditions.HasDisease:
                if self.HasEffect(vTarget, self.skill_id.disease):
                    number_of_features += 1

            if Conditions.HasPoison:
                if Agent.IsPoisoned(vTarget):
                    number_of_features += 1

            if Conditions.HasWeakness:
                if self.HasEffect(vTarget, self.skill_id.weakness):
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
                player_agent_id = Player.GetAgentID()
                buff_list = self.GetAgentBuffList(player_agent_id)
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
                player_agent_id = Player.GetAgentID()
                buff_list = self.GetAgentBuffList(player_agent_id)
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
                target_energy = self.GetEnergyValues(vTarget)
                if target_energy < Conditions.LessEnergy:
                    number_of_features += 1
      
            if Conditions.Overcast != 0:
                if Player.GetAgentID() == vTarget:
                    if Agent.GetOvercast(vTarget) < Conditions.Overcast:
                        number_of_features += 1
                        
            if self.skills[slot].custom_skill_data.SkillType == SkillType.PetAttack.value:
                pet_id = Party.Pets.GetPetID(Player.GetAgentID())
                
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
            #if Agent.GetCastingSkill(Player.GetAgentID()) != 0:
            #    self.in_casting_routine = False
            #    return False, v_target
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
            if not self.InAggro():
                return False

            _, target_aliegance = Agent.GetAllegiance(Player.GetTargetID())
            
            if Player.GetTargetID() == 0 or (target_aliegance != 'Enemy'):
                                
                nearest = Routines.Agents.GetNearestEnemy(self.get_combat_distance(), self.aggressive_enemies_only)
                called_target = self.GetPartyTarget()

                attack_target = 0

                if called_target != 0:
                    attack_target = called_target
                elif nearest != 0:
                    attack_target = nearest
                else:
                    return False

                ActionQueueManager().AddAction("ACTION", Player.ChangeTarget, attack_target)
                return True
            else:
                target_id = Player.GetTargetID()
                if not Agent.IsLiving(target_id):
                    return

                _, alliegeance = Agent.GetAllegiance(target_id)
                if alliegeance == 'Enemy':
                    target_id = Player.GetTargetID()
                    if target_id == 0:
                        return
                    
                    ActionQueueManager().AddAction("ACTION", Player.Interact, target_id)
                    return True
                
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
                        attack_speed = 0.75 #1.75
                    case Weapon.Scepter2.value:
                        attack_speed = 0.75 #1.75
                    case Weapon.Wand.value:
                        attack_speed = 0.75 #1.75
                    case Weapon.Staff1.value:
                        attack_speed = 0.75 #1.75
                    case Weapon.Staff.value:
                        attack_speed = 0.75 #1.75
                    case Weapon.Staff2.value:
                        attack_speed = 0.75 #1.75
                    case Weapon.Staff3.value:
                        attack_speed = 0.75 #1.75
                    case _:
                        attack_speed = 0.75 #1.75
                        
            return int((attack_speed / attack_speed_modifier) * 1000)
        
        def _HandleCombat(self,ooc=False):
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

            if ooc:
                if not is_ooc_skill:
                    self.AdvanceSkillPointer()
                    return False

            if target_agent_id == 0:
                self.AdvanceSkillPointer()
                return False

            if not Agent.IsLiving(target_agent_id):
                return False
                
            self.in_casting_routine = True
            
            aftercast = Skill.Data.GetActivation(skill_id) * 1000
            aftercast += Skill.Data.GetAftercast(skill_id) * 1000
            aftercast += self.ping_handler.GetCurrentPing()
            
            skill_type, _ = GLOBAL_CACHE.Skill.GetType(skill_id)
            if skill_type == SkillType.Attack.value:
                self.aftercast += self.GetWeaponAttackAftercast()
            
            
            
            self.aftercast_timer.SetThrottleTime(aftercast)
            self.aftercast_timer.Reset()
            ActionQueueManager().AddAction("ACTION", SkillBar.UseSkill, self.skill_order[self.skill_pointer]+1, target_agent_id)
            self.AdvanceSkillPointer()
            return True
			
			
			

        
        def HandleCombat(self):
            if self.game_throttle_timer.IsExpired():
                self.game_throttle_timer.Reset()
                self.PrioritizeSkills()
                if not self.InAggro():
                    self._HandleCombat(ooc=True)
                    return
                    
                if self._HandleCombat(ooc=False):
                    return
                
                if self.auto_attack_timer.IsExpired():
                    self.auto_attack_timer.Reset()
                    if self.ChooseTarget():
                        return
                
                