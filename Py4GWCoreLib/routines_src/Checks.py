
import importlib, typing
from typing import Tuple

import importlib

class _RProxy:
    def __getattr__(self, name: str):
        root_pkg = importlib.import_module("Py4GWCoreLib")
        return getattr(root_pkg.Routines, name)

Routines = _RProxy()

class Checks:
#region Player
    class Player:
        @staticmethod
        def CanAct():
            if not Checks.Map.MapValid():
                return False
            if Checks.Player.IsDead():
                return False
            if Checks.Player.IsKnockedDown():
                return False
            if Checks.Player.IsCasting():
                return False
            return True
        
        @staticmethod
        def IsDead():
            from ..GlobalCache import GLOBAL_CACHE
            return GLOBAL_CACHE.Agent.IsDead(GLOBAL_CACHE.Player.GetAgentID())
        
        @staticmethod
        def IsCasting():
            from ..GlobalCache import GLOBAL_CACHE
            return GLOBAL_CACHE.Agent.IsCasting(GLOBAL_CACHE.Player.GetAgentID())
        
        @staticmethod
        def IsKnockedDown():
            from ..GlobalCache import GLOBAL_CACHE
            return GLOBAL_CACHE.Agent.IsKnockedDown(GLOBAL_CACHE.Player.GetAgentID())

#region Party
    class Party:
        @staticmethod
        def IsPartyMemberDead():
            from ..GlobalCache import GLOBAL_CACHE
            if not Checks.Map.MapValid():
                return False
            is_someone_dead = False
            players = GLOBAL_CACHE.Party.GetPlayers()
            henchmen = GLOBAL_CACHE.Party.GetHenchmen()
            heroes = GLOBAL_CACHE.Party.GetHeroes()
    
            for player in players:
                agent_id = GLOBAL_CACHE.Party.Players.GetAgentIDByLoginNumber(player.login_number)
                if GLOBAL_CACHE.Agent.IsDead(agent_id):
                    is_someone_dead = True
                    break
            for henchman in henchmen:
                if GLOBAL_CACHE.Agent.IsDead(henchman.agent_id):
                    is_someone_dead = True
                    break
                
            for hero in heroes:
                if GLOBAL_CACHE.Agent.IsDead(hero.agent_id):
                    is_someone_dead = True
                    break

            return is_someone_dead
        
        @staticmethod
        def IsPartyWiped():
            from ..GlobalCache import GLOBAL_CACHE
            if not Checks.Map.MapValid():
                return False

            all_dead = True
            players = GLOBAL_CACHE.Party.GetPlayers()
            henchmen = GLOBAL_CACHE.Party.GetHenchmen()
            heroes = GLOBAL_CACHE.Party.GetHeroes()
            
            for player in players:
                agent_id = GLOBAL_CACHE.Party.Players.GetAgentIDByLoginNumber(player.login_number) 
                if not GLOBAL_CACHE.Agent.IsDead(agent_id):
                    all_dead = False
                    break
            
            for henchman in henchmen:
                if not GLOBAL_CACHE.Agent.IsDead(henchman.agent_id):
                    all_dead = False
                    break
            
            for hero in heroes:
                if not GLOBAL_CACHE.Agent.IsDead(hero.agent_id):
                    all_dead = False
                    break

            return all_dead

#region Map
    class Map:
        @staticmethod
        def MapValid():
            import PyMap
            import PyParty
            current_map = PyMap.PyMap()

            if  current_map.instance_type.GetName() == "Loading":
                return False
            if not current_map.is_map_ready:
                return False
            party = PyParty.PyParty()
            if not party.is_party_loaded:
                return False
            if  current_map.is_in_cinematic:
                return False
            return True
        
        @staticmethod
        def IsExplorable():
            from ..GlobalCache import GLOBAL_CACHE
            if not Checks.Map.MapValid():
                return False
            return GLOBAL_CACHE.Map.IsExplorable()
        
        @staticmethod
        def IsOutpost():
            from ..GlobalCache import GLOBAL_CACHE
            if not Checks.Map.MapValid():
                return False
            return GLOBAL_CACHE.Map.IsOutpost()
        
        @staticmethod
        def IsLoading():
            import PyMap
            if not Checks.Map.MapValid():
                return True
            current_map = PyMap.PyMap()
            if  current_map.instance_type.GetName() == "Loading":
                return True
            return False
        
        @staticmethod
        def IsMapReady():
            import PyMap
            if not Checks.Map.MapValid():
                return False
            current_map = PyMap.PyMap()
            return current_map.is_map_ready
        
        @staticmethod
        def IsInCinematic():
            import PyMap
            if not Checks.Map.MapValid():
                return False
            current_map = PyMap.PyMap()
            return current_map.is_in_cinematic
        
#region Inventory
    class Inventory:
        @staticmethod
        def InventoryAndLockpickCheck():
            from ..GlobalCache import GLOBAL_CACHE
            return GLOBAL_CACHE.Inventory.GetFreeSlotCount() > 0 and GLOBAL_CACHE.Inventory.GetModelCount(22751) > 0 
        
        @staticmethod
        def IsModelInInventory(model_id: int):
            from ..GlobalCache import GLOBAL_CACHE
            return GLOBAL_CACHE.Inventory.GetModelCount(model_id) > 0
        
        @staticmethod
        def IsItemInInventory(item_id: int):
            from ..GlobalCache import GLOBAL_CACHE
            return GLOBAL_CACHE.Inventory.GetItemCount(item_id) > 0
        
        @staticmethod
        def IsModelEquipped(model_id: int):
            from ..GlobalCache import GLOBAL_CACHE
            return GLOBAL_CACHE.Inventory.GetModelCountInEquipped(model_id) > 0
        
        @staticmethod
        def IsModelInBank(model_id: int):
            from ..GlobalCache import GLOBAL_CACHE
            return GLOBAL_CACHE.Inventory.GetModelCountInStorage(model_id) > 0
        
        @staticmethod
        def IsModelInInventoryOrBank(model_id: int):
            from ..GlobalCache import GLOBAL_CACHE
            return (GLOBAL_CACHE.Inventory.GetModelCount(model_id) + GLOBAL_CACHE.Inventory.GetModelCountInStorage(model_id)) > 0
        
        @staticmethod
        def IsModelInInventoryOrEquipped(model_id: int):
            from ..GlobalCache import GLOBAL_CACHE
            return (GLOBAL_CACHE.Inventory.GetModelCount(model_id) + GLOBAL_CACHE.Inventory.GetModelCountInEquipped(model_id)) > 0
        
        
        
#region Effects
    class Effects:
        @staticmethod
        def HasBuff(agent_id, skill_id):
            from ..GlobalCache import GLOBAL_CACHE
            if GLOBAL_CACHE.Effects.HasEffect(agent_id, skill_id):
                return True
            return False
#region Agents
    class Agents:
        from ..Py4GWcorelib import Range
        @staticmethod
        def InDanger(aggro_area=Range.Earshot, aggressive_only = False):
            from ..AgentArray import AgentArray
            from ..GlobalCache import GLOBAL_CACHE
            from ..Py4GWcorelib import Utils
            if not Checks.Map.MapValid():
                return False
            
            enemy_array = GLOBAL_CACHE.AgentArray.GetEnemyArray()
            if len(enemy_array) == 0:
                return False
            enemy_array = AgentArray.Filter.ByCondition(enemy_array, lambda agent_id: Utils.Distance(GLOBAL_CACHE.Player.GetXY(), GLOBAL_CACHE.Agent.GetXY(agent_id)) <= aggro_area.value)
            enemy_array = AgentArray.Filter.ByCondition(enemy_array, lambda agent_id: GLOBAL_CACHE.Agent.IsAlive(agent_id))
            enemy_array = AgentArray.Filter.ByCondition(enemy_array, lambda agent_id: GLOBAL_CACHE.Player.GetAgentID() != agent_id)
            if aggressive_only:
                enemy_array = AgentArray.Filter.ByCondition(enemy_array, lambda agent_id: GLOBAL_CACHE.Agent.IsAggressive(agent_id))
            if len(enemy_array) > 0:
                return True
            return False
        
        

        @staticmethod
        def IsEnemyBehind (agent_id):
            from ..GlobalCache import GLOBAL_CACHE
            import math
            player_agent_id = GLOBAL_CACHE.Player.GetAgentID()
            target = GLOBAL_CACHE.Player.GetTargetID()
            player_x, player_y = GLOBAL_CACHE.Agent.GetXY(player_agent_id)
            player_angle = GLOBAL_CACHE.Agent.GetRotationAngle(player_agent_id)  # Player's facing direction
            nearest_enemy = agent_id
            if target == 0:
                GLOBAL_CACHE.Player.ChangeTarget(nearest_enemy)
                target = nearest_enemy
            nearest_enemy_x, nearest_enemy_y = GLOBAL_CACHE.Agent.GetXY(nearest_enemy)
                        

            # Calculate the angle between the player and the enemy
            dx = nearest_enemy_x - player_x
            dy = nearest_enemy_y - player_y
            angle_to_enemy = math.atan2(dy, dx)  # Angle in radians
            angle_to_enemy = math.degrees(angle_to_enemy)  # Convert to degrees
            angle_to_enemy = (angle_to_enemy + 360) % 360  # Normalize to [0, 360]

            # Calculate the relative angle to the enemy
            angle_diff = (angle_to_enemy - player_angle + 360) % 360

            if angle_diff < 90 or angle_diff > 270:
                return True
            return False
        
        @staticmethod
        def IsValidItem(item_id):
            from ..GlobalCache import GLOBAL_CACHE
            owner = GLOBAL_CACHE.Agent.GetItemAgentOwnerID(item_id)
            return (owner == GLOBAL_CACHE.Player.GetAgentID()) or (owner == 0)
        
        @staticmethod
        def HasEffect(agent_id, skill_id, exact_weapon_spell=False):
            from ..GlobalCache import GLOBAL_CACHE
            from ..Skill import Skill
            from ..Agent import Agent
            result = GLOBAL_CACHE.Effects.HasEffect(agent_id, skill_id)

            if not result and not exact_weapon_spell:
                skilltype, _ = Skill.GetType(skill_id)
                if skilltype == 25: #SkillType.WeaponSpell.value:
                    result = Agent.IsWeaponSpelled(agent_id)

            return result

#region Skills
    class Skills:
        @staticmethod
        def HasEnoughEnergy(agent_id, skill_id):
            """
            Purpose: Check if the player has enough energy to use the skill.
            Args:
                agent_id (int): The agent ID of the player.
                skill_id (int): The skill ID to check.
            Returns: bool
            """
            from ..GlobalCache import GLOBAL_CACHE
            player_energy = GLOBAL_CACHE.Agent.GetEnergy(agent_id) * GLOBAL_CACHE.Agent.GetMaxEnergy(agent_id)
            skill_energy = GLOBAL_CACHE.Skill.Data.GetEnergyCost(skill_id)
            return player_energy >= skill_energy
        
        @staticmethod
        def HasEnoughLife(agent_id, skill_id):
            """
            Purpose: Check if the player has enough life to use the skill.
            Args:
                agent_id (int): The agent ID of the player.
                skill_id (int): The skill ID to check.
            Returns: bool
            """
            from ..GlobalCache import GLOBAL_CACHE
            player_life = GLOBAL_CACHE.Agent.GetHealth(agent_id)
            skill_life = GLOBAL_CACHE.Skill.Data.GetHealthCost(skill_id)
            return player_life > skill_life

        @staticmethod
        def HasEnoughAdrenaline(agent_id, skill_id):
            """
            Purpose: Check if the player has enough adrenaline to use the skill.
            Args:
                agent_id (int): The agent ID of the player.
                skill_id (int): The skill ID to check.
            Returns: bool
            """
            from ..GlobalCache import GLOBAL_CACHE
            skill_adrenaline = GLOBAL_CACHE.Skill.Data.GetAdrenaline(skill_id)
            skill_adrenaline_a = GLOBAL_CACHE.Skill.Data.GetAdrenalineA(skill_id)
            if skill_adrenaline == 0:
                return True

            if skill_adrenaline_a >= skill_adrenaline:
                return True

            return False

        @staticmethod
        def DaggerStatusPass(agent_id, skill_id):
            """
            Purpose: Check if the player attack dagger status match tha skill requirement.
            Args:
                agent_id (int): The agent ID of the player.
                skill_id (int): The skill ID to check.
            Returns: bool
            """
            from ..GlobalCache import GLOBAL_CACHE
            dagger_status = GLOBAL_CACHE.Agent.GetDaggerStatus(agent_id)
            skill_combo = GLOBAL_CACHE.Skill.Data.GetCombo(skill_id)

            if skill_combo == 1 and (dagger_status != 0 and dagger_status != 3):
                return False

            if skill_combo == 2 and dagger_status != 1:
                return False

            if skill_combo == 3 and dagger_status != 2:
                return False

            return True
        
        @staticmethod
        def IsSkillIDReady(skill_id):
            from ..GlobalCache import GLOBAL_CACHE
            slot = GLOBAL_CACHE.SkillBar.GetSlotBySkillID(skill_id)
            return Checks.Skills.IsSkillSlotReady(slot)


        @staticmethod
        def IsSkillSlotReady(skill_slot):
            from ..GlobalCache import GLOBAL_CACHE
            if skill_slot <= 0 or skill_slot > 8:
                return False
            skill = GLOBAL_CACHE.SkillBar.GetSkillData(skill_slot)
            return skill.recharge == 0
        
        @staticmethod    
        def CanCast():
            if not Checks.Map.MapValid():
                return False
            
            from ..GlobalCache import GLOBAL_CACHE
            player_agent_id = GLOBAL_CACHE.Player.GetAgentID()

            if (
                Checks.Player.IsCasting() or
                Checks.Player.IsDead() or
                Checks.Player.IsKnockedDown() or
                GLOBAL_CACHE.SkillBar.GetCasting() != 0
            ):
                return False
            return True
        
        @staticmethod
        def InCastingProcess():
            from ..GlobalCache import GLOBAL_CACHE
            player_agent_id = GLOBAL_CACHE.Player.GetAgentID()
            if GLOBAL_CACHE.Agent.IsCasting(player_agent_id) or GLOBAL_CACHE.SkillBar.GetCasting() != 0:
                return True
            return False
        
        @staticmethod
        def apply_fast_casting(skill_id: int, fast_casting_level =0) -> Tuple[float, float]:
            """
            Applies Fast Casting effects for cast time and recharge time, following exact in-game mechanics.

            :param agent_id: ID of the agent using the skill.
            :param skill_id: ID of the skill being evaluated.
            :return: (adjusted_cast_time, adjusted_recharge_time)
            """
            from ..GlobalCache import GLOBAL_CACHE
            activation_time = GLOBAL_CACHE.Skill.Data.GetActivation(skill_id)
            recharge_time = GLOBAL_CACHE.Skill.Data.GetRecharge(skill_id)
            
            #return activation_time, recharge_time

            if fast_casting_level <= 0:
                return activation_time, recharge_time

            # Get skill type and professions
            is_spell = GLOBAL_CACHE.Skill.Flags.IsSpell(skill_id)
            is_signet = GLOBAL_CACHE.Skill.Flags.IsSignet(skill_id)
            _, skill_profession = GLOBAL_CACHE.Skill.GetProfession(skill_id)

            # --- CAST TIME REDUCTION ---
            if is_spell or is_signet:
                # Mesmer spells/signets → always affected
                if skill_profession == "Mesmer":
                    activation_time *= 0.955 ** fast_casting_level
                    activation_time = round(activation_time, 3)
                # Non-Mesmer spells/signets → only affected if cast time >= 2s
                elif activation_time >= 2.0:
                    activation_time *= 0.955 ** fast_casting_level
                    activation_time = round(activation_time, 3)

            # --- RECHARGE TIME REDUCTION ---
            if skill_profession == "Mesmer" and is_spell:
                recharge_time *= (1.0 - 0.03 * fast_casting_level)
                recharge_time = round(recharge_time)

            return activation_time, recharge_time


        
        @staticmethod
        def apply_expertise_reduction(base_cost: int, expertise_level: int, skill_id) -> int:
            """
            Applies the Guild Wars expertise cost reduction correctly.
            
            :param base_cost: The original energy cost of the skill.
            :param expertise_level: The level of Expertise (0-20).
            :return: The reduced cost, rounded down to an integer.
            """
            #return base_cost  # Default to no reduction
            from ..GlobalCache import GLOBAL_CACHE
            skill_type, _ = GLOBAL_CACHE.Skill.GetType(skill_id)
            _, skill_profession = GLOBAL_CACHE.Skill.GetProfession(skill_id)
            if (skill_type == 14 or #attack skills
                GLOBAL_CACHE.Skill.Flags.IsRitual(skill_id) or
                GLOBAL_CACHE.Skill.Flags.IsTouchRange(skill_id) or
                skill_profession == "Ranger"):

                EXPERTISE_REDUCTION = [
                    1.00, 0.96, 0.92, 0.88, 0.84, 0.80, 0.76, 0.72, 0.68, 0.64, 0.60,
                    0.56, 0.52, 0.48, 0.44, 0.40, 0.36, 0.32, 0.28, 0.24, 0.20
                ]
                if expertise_level < 0 or expertise_level > 20:
                    expertise_level = max(0, min(expertise_level, 20))  # clamp
                reduction_factor = EXPERTISE_REDUCTION[expertise_level]
                return max(0, int(base_cost * reduction_factor))  # floor after applying
            
            return base_cost  # No reduction for other skills

        
        @staticmethod
        def GetEnergyCostWithEffects(skill_id, agent_id):
            """Retrieve the actual energy cost of a skill by its ID and effects.

            Args:
                skill_id (int): ID of the skill.
                agent_id (int): ID of the agent (player or hero).

            Returns:
                float: Final energy cost after applying all effects.
                    Values are rounded to integers.
                    Minimum cost is 0 unless otherwise specified by an effect.
            """
            from ..GlobalCache import GLOBAL_CACHE
            # Get base energy cost for the skill
            cost = GLOBAL_CACHE.Skill.Data.GetEnergyCost(skill_id)
            
            # Get all active effects on the agent
            player_effects = GLOBAL_CACHE.Effects.GetEffects(agent_id)

            # Process each effect in order of application
            # Effects are processed in this specific order to match game mechanics
            for effect in player_effects:
                effect_id = effect.skill_id
                attr = GLOBAL_CACHE.Effects.EffectAttributeLevel(agent_id, effect_id)

                match effect_id:
                    case 469:  # Primal Echoes - Forces Signets to cost 10 energy
                        if GLOBAL_CACHE.Skill.Flags.IsSignet(skill_id):
                            cost = 10  # Fixed cost regardless of other effects
                            continue  # Allow other effects to modify this cost

                    case 475:  # Quickening Zephyr - Increases energy cost by 30%
                        cost *= 1.30   # Using multiplication instead of addition for better precision
                        continue

                    case 1725:  # Roaring Winds - Increases Shout/Chant cost based on attribute level
                        if GLOBAL_CACHE.Skill.Flags.IsChant(skill_id) or GLOBAL_CACHE.Skill.Flags.IsShout(skill_id):
                            match attr:
                                case a if 0 < a <= 1:
                                    cost += 1
                                case a if 2 <= a <= 5:
                                    cost += 2
                                case a if 6 <= a <= 9:
                                    cost += 3
                                case a if 10 <= a <= 13:
                                    cost += 4
                                case a if 14 <= a <= 16:
                                    cost += 5
                                case a if 17 <= a <= 20:
                                    cost += 6
                            continue

                    case 1677:  # Veiled Nightmare - Increases all costs by 40%
                        cost *= 1.40
                        continue

                    case 856:  # "Kilroy Stonekin" - Reduces all costs by 50%
                        cost *= 0.50
                        continue

                    case 1115:  # Air of Enchantment
                        if GLOBAL_CACHE.Skill.Flags.IsEnchantment(skill_id):
                            cost -= 5
                        continue

                    case 1223:  # Anguished Was Lingwah
                        if GLOBAL_CACHE.Skill.Flags.IsHex(skill_id) and GLOBAL_CACHE.Skill.GetProfession(skill_id)[0] == 8:
                            match attr:
                                case a if 0 < a <= 1:
                                    cost -= 1
                                case a if 2 <= a <= 5:
                                    cost -= 2
                                case a if 6 <= a <= 9:
                                    cost -= 3
                                case a if 10 <= a <= 13:
                                    cost -= 4
                                case a if 14 <= a <= 16:
                                    cost -= 5
                                case a if 17 <= a <= 20:
                                    cost -= 6
                                case a if a > 20:
                                    cost -= 7
                            continue

                    case 1220:  # Attuned Was Songkai
                        if GLOBAL_CACHE.Skill.Flags.IsSpell(skill_id) or GLOBAL_CACHE.Skill.Flags.IsRitual(skill_id):
                            percentage = 5 + (attr * 3) if attr <= 20 else 68
                            cost -= cost * (percentage / 100)
                        continue

                    case 596:  # Chimera of Intensity
                        cost -= cost * 0.50
                        continue

                    case 806:  # Cultist's Fervor
                        if GLOBAL_CACHE.Skill.Flags.IsSpell(skill_id) and GLOBAL_CACHE.Skill.GetProfession(skill_id)[0] == 4:
                            match attr:
                                case a if 0 < a <= 1:
                                    cost -= 1
                                case a if 2 <= a <= 4:
                                    cost -= 2
                                case a if 5 <= a <= 7:
                                    cost -= 3
                                case a if 8 <= a <= 10:
                                    cost -= 4
                                case a if 11 <= a <= 13:
                                    cost -= 5
                                case a if 14 <= a <= 16:
                                    cost -= 6
                                case a if 17 <= a <= 19:
                                    cost -= 7
                                case a if a > 19:
                                    cost -= 8
                            continue

                    case 310:  # Divine Spirit
                        if GLOBAL_CACHE.Skill.Flags.IsSpell(skill_id) and GLOBAL_CACHE.Skill.GetProfession(skill_id)[0] == 3:
                            cost -= 5
                        continue

                    case 1569:  # Energizing Chorus
                        if GLOBAL_CACHE.Skill.Flags.IsChant(skill_id) or GLOBAL_CACHE.Skill.Flags.IsShout(skill_id):
                            match attr:
                                case a if 0 < a <= 1:
                                    cost -= 3
                                case a if 2 <= a <= 5:
                                    cost -= 4
                                case a if 6 <= a <= 9:
                                    cost -= 5
                                case a if 10 <= a <= 13:
                                    cost -= 6
                                case a if 14 <= a <= 16:
                                    cost -= 7
                                case a if 17 <= a <= 20:
                                    cost -= 8
                                case a if a > 20:
                                    cost -= 9
                            continue

                    case 474:  # Energizing Wind
                        if cost >= 15:
                            cost -= 15
                        else:
                            cost = 0
                        continue

                    case 2145:  # Expert Focus
                        if GLOBAL_CACHE.Skill.Flags.IsAttack(skill_id) and GLOBAL_CACHE.Skill.Data.GetWeaponReq(skill_id) == 2:
                            match attr:
                                case a if 0 < a <= 7:
                                    cost -= 1
                                case a if a > 8:
                                    cost -= 2
                                

                    case 199:  # Glyph of Energy
                        if GLOBAL_CACHE.Skill.Flags.IsSpell(skill_id):
                            if attr == 0:
                                cost -= 10
                            else:
                                cost -= (10 + attr)

                    case 200:  # Glyph of Lesser Energy
                        if GLOBAL_CACHE.Skill.Flags.IsSpell(skill_id):
                            match attr:
                                case 0:
                                    cost -= 10
                                case a if 1 <= a <= 2:
                                    cost -= 11
                                case a if 3 <= a <= 4:
                                    cost -= 12
                                case a if 5 <= a <= 6:
                                    cost -= 13
                                case a if 7 <= a <= 8:
                                    cost -= 14
                                case a if 9 <= a <= 10:
                                    cost -= 15
                                case a if 11 <= a <= 12:
                                    cost -= 16
                                case a if 13 <= a <= 14:
                                    cost -= 17
                                case 15:
                                    cost -= 18
                                case a if 16 <= a <= 16:
                                    cost -= 19
                                case a if 17 <= a <= 18:
                                    cost -= 20
                                case a if a >= 20:
                                    cost -= 21

                    case 1394:  # Healer's Covenant
                        if GLOBAL_CACHE.Skill.Flags.IsSpell(skill_id) and GLOBAL_CACHE.Skill.Attribute.GetAttribute(skill_id).attribute_id == 15:
                            match attr:
                                case a if 0 < a <= 3:
                                    cost -= 1
                                case a if 4 <= a <= 11:
                                    cost -= 2
                                case a if 12 <= a <= 18:
                                    cost -= 3
                                case a if a >= 19:
                                    cost -= 4

                    case 763:  # Jaundiced Gaze
                        if GLOBAL_CACHE.Skill.Flags.IsEnchantment(skill_id):
                            match attr:
                                case 0:
                                    cost -= 1
                                case a if 1 <= a <= 2:
                                    cost -= 2
                                case a if 3 <= a <= 4:
                                    cost -= 3
                                case 5:
                                    cost -= 4
                                case a if 6 <= a <= 7:
                                    cost -= 5
                                case a if 8 <= a <= 9:
                                    cost -= 6
                                case 10:
                                    cost -= 7
                                case a if 11 <= a <= 12:
                                    cost -= 8
                                case a if 13 <= a <= 14:
                                    cost -= 9
                                case 15:
                                    cost -= 10
                                case a if 16 <= a <= 17:
                                    cost -= 11
                                case a if 18 <= a <= 19:
                                    cost -= 12
                                case 20:
                                    cost -= 13
                                case a if a > 20:
                                    cost -= 14

                    case 1739:  # Renewing Memories
                        if GLOBAL_CACHE.Skill.Flags.IsItemSpell(skill_id) or GLOBAL_CACHE.Skill.Flags.IsWeaponSpell(skill_id):
                            percentage = 5 + (attr * 2) if attr <= 20 else 47
                            cost -= cost * (percentage / 100)

                    case 1240:  # Soul Twisting
                        if GLOBAL_CACHE.Skill.Flags.IsRitual(skill_id):
                            cost = 10  # Fixe le coût à 10

                    case 987:  # Way of the Empty Palm
                        if GLOBAL_CACHE.Skill.Data.GetCombo(skill_id) == 2 or GLOBAL_CACHE.Skill.Data.GetCombo(skill_id) == 3:  # Attaque double ou secondaire
                            cost = 0

            cost = max(0, cost)

            return cost