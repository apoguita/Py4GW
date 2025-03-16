from Py4GWCoreLib import Timer
from Py4GWCoreLib import Utils
from Py4GWCoreLib import ConsoleLog
from Py4GWCoreLib import ActionQueueNode
from time import sleep
from .enums import *
import inspect
import math

arrived_timer = Timer()

class Routines:
    #region Checks
    class Checks:
        class Inventory:
            @staticmethod
            def InventoryAndLockpickCheck():
                from .Inventory import Inventory
                return Inventory.GetFreeSlotCount() > 0 and Inventory.GetModelCount(22751) > 0 

        class Effects:
            @staticmethod
            def HasBuff(agent_id, skill_id):
                from .Effect import Effects 
                if Effects.BuffExists(agent_id, skill_id) or Effects.EffectExists(agent_id, skill_id):
                    return True
                return False
            
        class Agents:
            @staticmethod
            def InDanger(aggro_area=Range.Earshot):
                from .Agent import Agent
                from .Player import Player
                from .AgentArray import AgentArray
                enemy_array = AgentArray.GetEnemyArray()
                enemy_array = AgentArray.Filter.ByCondition(enemy_array, lambda agent_id: Utils.Distance(Player.GetXY(), Agent.GetXY(agent_id)) <= aggro_area.value)
                enemy_array = AgentArray.Filter.ByCondition(enemy_array, lambda agent_id: Agent.IsAlive(agent_id))
                enemy_array = AgentArray.Filter.ByCondition(enemy_array, lambda agent_id: Player.GetAgentID() != agent_id)
                if len(enemy_array) > 0:
                    return True
                return False
    
            @staticmethod
            def IsEnemyBehind (agent_id):
                from .Agent import Agent
                from .Player import Player

                player_agent_id = Player.GetAgentID()
                target = Player.GetTargetID()
                player_x, player_y = Agent.GetXY(player_agent_id)
                player_angle = Agent.GetRotationAngle(player_agent_id)  # Player's facing direction
                nearest_enemy = agent_id
                if target == 0:
                    Player.ChangeTarget(nearest_enemy)
                    target = nearest_enemy
                nearest_enemy_x, nearest_enemy_y = Agent.GetXY(nearest_enemy)
                            

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
                from .Agent import Agent
                from .Player import Player
                return (Agent.agent_instance(item_id).item_agent.owner_id == Player.GetAgentID()) or (Agent.agent_instance(item_id).item_agent.owner_id == 0)


            
        class Skills:
            @staticmethod
            def HasEnoughEnergy(agent_id, skill_id):
                from .Agent import Agent
                from .Skill import Skill
                """
                Purpose: Check if the player has enough energy to use the skill.
                Args:
                    agent_id (int): The agent ID of the player.
                    skill_id (int): The skill ID to check.
                Returns: bool
                """
                player_energy = Agent.GetEnergy(agent_id) * Agent.GetMaxEnergy(agent_id)
                skill_energy = Skill.Data.GetEnergyCost(skill_id)
                return player_energy >= skill_energy
            
            @staticmethod
            def HasEnoughLife(agent_id, skill_id):
                from .Agent import Agent
                from .Skill import Skill
                """
                Purpose: Check if the player has enough life to use the skill.
                Args:
                    agent_id (int): The agent ID of the player.
                    skill_id (int): The skill ID to check.
                Returns: bool
                """
                player_life = Agent.GetHealth(agent_id)
                skill_life = Skill.Data.GetHealthCost(skill_id)
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
                from .Skill import Skill
                skill_adrenaline = Skill.Data.GetAdrenaline(skill_id)
                skill_adrenaline_a = Skill.Data.GetAdrenalineA(skill_id)
                if skill_adrenaline == 0:
                    return True

                if skill_adrenaline_a >= skill_adrenaline:
                    return True

                return False

            @staticmethod
            def DaggerStatusPass(agent_id, skill_id):
                from .Agent import Agent
                from .Skill import Skill
                """
                Purpose: Check if the player attack dagger status match tha skill requirement.
                Args:
                    agent_id (int): The agent ID of the player.
                    skill_id (int): The skill ID to check.
                Returns: bool
                """
                
                dagger_status = Agent.GetDaggerStatus(agent_id)
                skill_combo = Skill.Data.GetCombo(skill_id)

                if skill_combo == 1 and (dagger_status != 0 and dagger_status != 3):
                    return False

                if skill_combo == 2 and dagger_status != 1:
                    return False

                if skill_combo == 3 and dagger_status != 2:
                    return False

                return True
            
            @staticmethod
            def IsSkillIDReady(skill_id):
                from .Skillbar import SkillBar
                skill = SkillBar.GetSkillData(SkillBar.GetSlotBySkillID(skill_id))
                recharge = skill.recharge
                return recharge == 0

            @staticmethod
            def IsSkillSlotReady(skill_slot):
                from .Skillbar import SkillBar
                skill = SkillBar.GetSkillData(skill_slot)
                return skill.recharge == 0
            
            @staticmethod    
            def CanCast():
                from .Agent import Agent
                from .Player import Player
                from .Skillbar import SkillBar
                
                player_agent_id = Player.GetAgentID()

                if (
                    Agent.IsCasting(player_agent_id) 
                    or Agent.GetCastingSkill(player_agent_id) != 0
                    or Agent.IsKnockedDown(player_agent_id)
                    or Agent.IsDead(player_agent_id)
                    or SkillBar.GetCasting() != 0
                ):
                    return False
                return True
            
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
                from .Effect import Effects
                from .Skill import Skill
                # Get base energy cost for the skill
                cost = Skill.skill_instance(skill_id).energy_cost

                # Adjust base cost for special cases (API inconsistencies)
                if cost == 11:
                    cost = 15    # True cost is 15
                elif cost == 12:
                    cost = 25    # True cost is 25

                # Get all active effects on the agent
                player_effects = Effects.GetEffects(agent_id)

                # Process each effect in order of application
                # Effects are processed in this specific order to match game mechanics
                for effect in player_effects:
                    effect_id = effect.skill_id
                    attr = Effects.EffectAttributeLevel(agent_id, effect_id)

                    match effect_id:
                        case 469:  # Primal Echoes - Forces Signets to cost 10 energy
                            if Skill.Flags.IsSignet(skill_id):
                                cost = 10  # Fixed cost regardless of other effects
                                continue  # Allow other effects to modify this cost

                        case 475:  # Quickening Zephyr - Increases energy cost by 30%
                            cost *= 1.30   # Using multiplication instead of addition for better precision
                            continue

                        case 1725:  # Roaring Winds - Increases Shout/Chant cost based on attribute level
                            if Skill.Flags.IsChant(skill_id) or Skill.Flags.IsShout(skill_id):
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
                            if Skill.Flags.IsEnchantment(skill_id):
                                cost -= 5
                            continue

                        case 1223:  # Anguished Was Lingwah
                            if Skill.Flags.IsHex(skill_id) and Skill.GetProfession(skill_id)[0] == 8:
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
                            if Skill.Flags.IsSpell(skill_id) or Skill.Flags.IsRitual(skill_id):
                                percentage = 5 + (attr * 3) if attr <= 20 else 68
                                cost -= cost * (percentage / 100)
                            continue

                        case 596:  # Chimera of Intensity
                            cost -= cost * 0.50
                            continue

                        case 806:  # Cultist's Fervor
                            if Skill.Flags.IsSpell(skill_id) and Skill.GetProfession(skill_id)[0] == 4:
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
                            if Skill.Flags.IsSpell(skill_id) and Skill.GetProfession(skill_id)[0] == 3:
                                cost -= 5
                            continue

                        case 1569:  # Energizing Chorus
                            if Skill.Flags.IsChant(skill_id) or Skill.Flags.IsShout(skill_id):
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
                            if Skill.Flags.IsAttack(skill_id) and Skill.Data.GetWeaponReq(skill_id) == 2:
                                match attr:
                                    case a if 0 < a <= 7:
                                        cost -= 1
                                    case a if a > 8:
                                        cost -= 2
                                    

                        case 199:  # Glyph of Energy
                            if Skill.Flags.IsSpell(skill_id):
                                if attr == 0:
                                    cost -= 10
                                else:
                                    cost -= (10 + attr)

                        case 200:  # Glyph of Lesser Energy
                            if Skill.Flags.IsSpell(skill_id):
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
                            if Skill.Flags.IsSpell(skill_id) and Skill.Attribute.GetAttribute(skill_id) == 15:
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
                            if Skill.Flags.IsEnchantment(skill_id):
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
                            if Skill.Flags.IsItemSpell(skill_id) or Skill.Flags.IsWeaponSpell(skill_id):
                                percentage = 5 + (attr * 2) if attr <= 20 else 47
                                cost -= cost * (percentage / 100)

                        case 1240:  # Soul Twisting
                            if Skill.Flags.IsRitual(skill_id):
                                cost = 10  # Fixe le coût à 10

                        case 987:  # Way of the Empty Palm
                            if Skill.Data.GetCombo(skill_id) == 2 or Skill.Data.GetCombo(skill_id) == 3:  # Attaque double ou secondaire
                                cost = 0

                cost = max(0, cost)
                return cost

    #region Transitions
    class Transition:
        @staticmethod
        def TravelToOutpost(outpost_id, log= True):
            """
            Purpose: Travel to the specified outpost by ID.
            Args:
                outpost_id (int): The ID of the outpost to travel to.
                log (bool) Optional: Whether to log the action. Default is True.
            Returns: None
            """
            from .Map import Map
            global arrived_timer
            if Map.IsMapReady():
                if Map.GetMapID() != outpost_id and arrived_timer.IsStopped():
                    if log:
                        current_function = (frame := inspect.currentframe()) and frame.f_code.co_name or "Unknown"
                        ConsoleLog(f"{current_function}", f"Outpost Check Failed. ({Map.GetMapName(outpost_id)}), Travelling.", Console.MessageType.Info)
                    Map.Travel(outpost_id)
                    arrived_timer.Start()
                    return

                if log and arrived_timer.IsStopped():
                    current_function = (frame := inspect.currentframe()) and frame.f_code.co_name or "Unknown"
                    ConsoleLog(f"{current_function}", f"Outpost Check Passed. ({Map.GetMapName(outpost_id)}).", Console.MessageType.Info)

        @staticmethod
        def HasArrivedToOutpost(outpost_id, log= True):
            """
            Purpose: Check if the player has arrived at the specified outpost after traveling.
            Args:
                outpost_id (int): The ID of the outpost to check.
                log (bool) Optional: Whether to log the action. Default is True.
            Returns: bool
            """
            from .Map import Map
            global arrived_timer

            if Map.GetMapID() == outpost_id and Routines.Transition.IsOutpostLoaded():
                if log:
                    current_function = (frame := inspect.currentframe()) and frame.f_code.co_name or "Unknown"
                    ConsoleLog(f"{current_function}", f"Outpost Arrive Passed. @{Map.GetMapName(outpost_id)}.", Console.MessageType.Info)
                    arrived_timer.Stop()
                    return True
                else:
                    if arrived_timer.HasElapsed(5000):
                        arrived_timer.Stop()
                        if log:
                            current_function = (frame := inspect.currentframe()) and frame.f_code.co_name or "Unknown"
                            ConsoleLog(f"{current_function}", f"Outpost Arrive Timeout. @{Map.GetMapName(outpost_id)}.", Console.MessageType.Info)
                        return False
            
            if log:
                current_function = (frame := inspect.currentframe()) and frame.f_code.co_name or "Unknown"
                ConsoleLog(f"{current_function}", f"Outpost Arrive Failed. @{Map.GetMapName(outpost_id)}. Retrying.", Console.MessageType.Info)
                
            return False

        @staticmethod
        def IsOutpostLoaded():
            """
            Purpose: Check if the outpost map is loaded.
            Args: None
            Returns: bool
            """
            from .Party import Party
            from .Map import Map
            map_loaded = Map.IsMapReady() and Map.IsOutpost() and Party.IsPartyLoaded()
            if map_loaded:
                ConsoleLog("IsOutpostLoaded", f"Outpost Map Loaded.", Console.MessageType.Info)
            else:
                ConsoleLog("IsOutpostLoaded", f"Outpost Map Not Loaded. Retrying.", Console.MessageType.Info)
            
            return map_loaded

        @staticmethod
        def IsExplorableLoaded(log_actions=False):
            """
            Purpose: Check if the explorable map is loaded.
            Args: None
            Returns: bool
            """
            from .Party import Party
            from .Map import Map
            map_loaded =  Map.IsMapReady() and Map.IsExplorable() and Party.IsPartyLoaded()
            if log_actions:
                if map_loaded:
                    ConsoleLog("IsExplorableLoaded", f"Explorable Map Loaded.", Console.MessageType.Info)
                else:
                    ConsoleLog("IsExplorableLoaded", f"Explorable Map Not Loaded. Retrying.", Console.MessageType.Info)
            
            return map_loaded

    #region Targetting
    class Targeting:
        @staticmethod
        def InteractTarget():
            from .Player import Player
            """Interact with the target"""
            Player.Interact(Player.GetTargetID())
            
        @staticmethod
        def HasArrivedToTarget():
            from .Agent import Agent
            from .Player import Player
            """Check if the player has arrived at the target."""
            player_x, player_y = Player.GetXY()
            target_id = Player.GetTargetID()
            target_x, target_y = Agent.GetXY(target_id)
            return Utils.Distance((player_x, player_y), (target_x, target_y)) < 100
    #endregion
    #region Agents
    class Agents:    
        @staticmethod
        def GetNearestNPCXY(x,y, distance):
            from .AgentArray import AgentArray
            from .Player import Player
            scan_pos = (x,y)
            npc_array = AgentArray.GetNPCMinipetArray()
            npc_array = AgentArray.Filter.ByDistance(npc_array,scan_pos, distance)
            npc_array = AgentArray.Sort.ByDistance(npc_array, scan_pos)
            if len(npc_array) > 0:
                return npc_array[0]
            return 0    
                   
        @staticmethod
        def GetNearestNPC(distance):
            from .Player import Player
            player_pos = Player.GetXY()
            return Routines.Agents.GetNearestNPCXY(player_pos[0], player_pos[1], distance)
      
         
        @staticmethod
        def GetFilteredEnemyArray(x,y,max_distance=4500.0):
            from .AgentArray import AgentArray
            from .Player import Player
            from .Agent import Agent
            """
            Purpose: Get the nearest enemy within the specified range.
            Args:
                range (int): The maximum distance to search for enemies.
            Returns: Agent ID or None
            """
            enemy_array = AgentArray.GetEnemyArray()
            enemy_array = AgentArray.Filter.ByCondition(enemy_array, lambda agent_id: Utils.Distance((x,y), Agent.GetXY(agent_id)) <= max_distance)
            enemy_array = AgentArray.Filter.ByCondition(enemy_array, lambda agent_id: Agent.IsAlive(agent_id))
            enemy_array = AgentArray.Filter.ByCondition(enemy_array, lambda agent_id: Player.GetAgentID() != agent_id)
            return enemy_array
                     
        @staticmethod
        def GetNearestEnemy(max_distance=4500.0):
            from .AgentArray import AgentArray
            from .Player import Player
            from .Agent import Agent
            """
            Purpose: Get the nearest enemy within the specified range.
            Args:
                range (int): The maximum distance to search for enemies.
            Returns: Agent ID or None
            """
            enemy_array = AgentArray.GetEnemyArray()
            enemy_array = AgentArray.Filter.ByCondition(enemy_array, lambda agent_id: Utils.Distance(Player.GetXY(), Agent.GetXY(agent_id)) <= max_distance)
            enemy_array = AgentArray.Filter.ByCondition(enemy_array, lambda agent_id: Agent.IsAlive(agent_id))
            enemy_array = AgentArray.Filter.ByCondition(enemy_array, lambda agent_id: Player.GetAgentID() != agent_id)
            if len(enemy_array) > 0:
                return enemy_array[0]
            return 0
            
        @staticmethod
        def GetNearestItem(max_distance=5000.0):
            from .AgentArray import AgentArray
            from .Player import Player
            """
            Purpose: Get the nearest item within the specified range.
            Args:
                range (int): The maximum distance to search for items.
            Returns: Agent ID or None
            """
            item_array = AgentArray.GetItemArray()
            item_array = AgentArray.Filter.ByDistance(item_array, Player.GetXY(), max_distance)
            item_array = AgentArray.Sort.ByDistance(item_array,Player.GetXY())
            if len(item_array) > 0:
                return item_array[0]    

        @staticmethod
        def GetNearestChest(max_distance=5000):
            from .AgentArray import AgentArray
            from .Agent import Agent
            from .Player import Player
            """
            Purpose: Get the nearest chest within the specified range.
            Args:
                range (int): The maximum distance to search for chests.
            Returns: Agent ID or None
            """
            gadget_array = AgentArray.GetGadgetArray()
            gadget_array = AgentArray.Filter.ByDistance(gadget_array, Player.GetXY(), max_distance)
            gadget_array = AgentArray.Sort.ByDistance(gadget_array,Player.GetXY())
            for agent_id in gadget_array:
                if Agent.GetGadgetID(agent_id) == 8141: #8141 is the ID for a chest
                    return agent_id

            return 0

        @staticmethod
        def GetBestTarget(a_range=1320, casting_only=False, no_hex_only=False, enchanted_only=False):
            """
            Purpose: Returns the best target within the specified range based on criteria like whether the agent is casting, enchanted, or hexed.
            Args:
                a_range (int): The maximum distance for selecting targets.
                casting_only (bool): If True, only select agents that are casting.
                no_hex_only (bool): If True, only select agents that are not hexed.
                enchanted_only (bool): If True, only select agents that are enchanted.
            Returns: PyAgent.PyAgent: The best target agent object, or None if no target matches.
            """
            from .AgentArray import AgentArray
            from .Agent import Agent
            from .Player import Player
            best_target = None
            lowest_sum = float('inf')
            nearest_enemy = None
            nearest_distance = float('inf')
            lowest_hp_target = None
            lowest_hp = float('inf')

            player_pos = Player.GetXY()
            agents = AgentArray.GetEnemyArray()
            agents = AgentArray.Filter.ByCondition(agents, lambda agent_id: Agent.IsAlive(agent_id))
            agents = AgentArray.Filter.ByDistance(agents, player_pos, a_range)

            if enchanted_only:
                agents = AgentArray.Filter.ByCondition(agents, lambda agent_id: Agent.IsEnchanted(agent_id))

            if no_hex_only:
                agents = AgentArray.Filter.ByCondition(agents, lambda agent_id: Agent.IsHexed(agent_id))

            if casting_only:
                agents = AgentArray.Filter.ByCondition(agents, lambda agent_id: Agent.IsCasting(agent_id))

            for agent_id in agents:
                agent = Player.GetAgentID()
                x,y = Agent.GetXY(agent)

                distance_to_self = Utils.Distance(Player.GetXY(), (x, y))

                # Track the nearest enemy
                if distance_to_self < nearest_distance:
                    nearest_enemy = agent
                    nearest_distance = distance_to_self

                # Track the agent with the lowest HP
                agent_hp = Agent.GetHealth(agent)
                if agent_hp < lowest_hp:
                    lowest_hp = agent_hp
                    lowest_hp_target = agent

                # Calculate the sum of distances between this agent and other agents within range
                sum_distances = 0
                for other_agent_id in agents:
                    other_x, other_y = Agent.GetXY(other_agent_id)
                    #no need to filter any agent since the array is filtered already
                    sum_distances += Utils.Distance((x, y), (other_x, other_y))

                # Track the best target based on the sum of distances
                if sum_distances < lowest_sum:
                    lowest_sum = sum_distances
                    best_target = agent

            return best_target

        @staticmethod
        def GetBestMeleeTarget(a_range=1320, casting_only=False, no_hex_only=False, enchanted_only=False):
            """
            Purpose: Returns the best melee most baslled up target within the specified range based on criteria like whether the agent is casting, enchanted, or hexed.
            Args:
                a_range (int): The maximum distance for selecting targets.
                casting_only (bool): If True, only select agents that are casting.
                no_hex_only (bool): If True, only select agents that are not hexed.
                enchanted_only (bool): If True, only select agents that are enchanted.
            Returns: PyAgent.PyAgent: The best melee target agent object, or None if no target matches.
            """
            from .AgentArray import AgentArray
            from .Agent import Agent
            from .Player import Player
            best_target = None
            lowest_sum = float('inf')
            nearest_enemy = None
            nearest_distance = float('inf')
            lowest_hp_target = None
            lowest_hp = float('inf')

            player_pos = Player.GetXY()
            agents = AgentArray.GetEnemyArray()

            # Filter out dead, distant, and non-melee agents
            agents = AgentArray.Filter.ByCondition(agents, lambda agent_id: Agent.IsAlive(agent_id))
            agents = AgentArray.Filter.ByCondition(agents, lambda agent_id: Agent.IsMelee(agent_id))
            agents = AgentArray.Filter.ByDistance(agents, player_pos, a_range)


            if enchanted_only:
                agents = AgentArray.Filter.ByCondition(agents, lambda agent_id: Agent.IsEnchanted(agent_id))

            if no_hex_only:
                agents = AgentArray.Filter.ByCondition(agents, lambda agent_id: Agent.IsHexed(agent_id))

            if casting_only:
                agents = AgentArray.Filter.ByCondition(agents, lambda agent_id: Agent.IsCasting(agent_id))


            for agent_id in agents:
                
                x, y = Agent.GetXY(agent_id)

                distance_to_self = Utils.Distance(Player.GetXY(), (x, y))

                # Track the nearest melee enemy
                if distance_to_self < nearest_distance:
                    nearest_distance = distance_to_self

                # Track the agent with the lowest HP
                agent_hp = Agent.GetHealth(agent_id) 
                if agent_hp < lowest_hp:
                    lowest_hp = agent_hp


                # Calculate the sum of distances between this agent and other agents within range
                sum_distances = 0
                for other_agent_id in agents:
                    other_agent_x, other_agent_y = Agent.GetXY(other_agent_id)
                    sum_distances += Utils.Distance((x, y), (other_agent_x, other_agent_y))

                # Track the best melee target based on the sum of distances
                if sum_distances < lowest_sum:
                    lowest_sum = sum_distances
                    best_target = agent_id

            return best_target


    #region Movement
    class Movement:
        @staticmethod
        def FollowPath(path_handler,follow_handler, log_actions=False):
            """
            Purpose: Follow a path using the path handler and follow handler objects.
            Args:
                path_handler (PathHandler): The PathHandler object containing the path coordinates.
                follow_handler (FollowXY): The FollowXY object for moving to waypoints.
            Returns: None
            """
            
            follow_handler.update()

            if follow_handler.is_following():
                return


            point = path_handler.advance()
            if point is not None:
                follow_handler.move_to_waypoint(point[0], point[1])
                if log_actions:
                    ConsoleLog("FollowPath", f"Moving to {point}", Console.MessageType.Info)

        @staticmethod
        def IsFollowPathFinished(path_handler,follow_handler):
            return path_handler.is_finished() and follow_handler.has_arrived()


        class FollowXY:
            def __init__(self, tolerance=100):
                """
                Initialize the FollowXY object with default values.
                Routine for following a waypoint.
                """
                self.waypoint = (0, 0)
                self.tolerance = tolerance
                self.following = False
                self.arrived = False
                self.timer = Timer()  # Timer to track movement start time
                self.wait_timer = Timer()  # Timer to track waiting after issuing move command
                self.wait_timer_run_once = True


            def calculate_distance(self, pos1, pos2):
                """
                Calculate the Euclidean distance between two points.
                """
                return Utils.Distance(pos1, pos2)


            def move_to_waypoint(self, x=0, y=0, tolerance=None, action_queue = None):
                """
                Move the player to the specified coordinates.
                Args:
                    x (float): X coordinate of the waypoint.
                    y (float): Y coordinate of the waypoint.
                    tolerance (int, optional): The distance threshold to consider arrival. Defaults to the initialized value.
                """
                from .Player import Player
                self.reset()
                self.waypoint = (x, y)
                self.tolerance = tolerance if tolerance is not None else self.tolerance
                self.following = True
                self.arrived = False
                if action_queue is None:
                    Player.Move(x, y)
                else:
                    action_queue.append(Player.Move, x, y)
                self.timer.Start()

            def reset(self):
                """
                Cancel the current move command and reset the waypoint following state.
                """
                self.following = False
                self.arrived = False
                self.timer.Reset()
                self.wait_timer.Reset()

            def update(self, log_actions = False, action_queue = None):
                """
                Update the FollowXY object's state, check if the player has reached the waypoint,
                and issue new move commands if necessary.
                """
                from .Agent import Agent
                from .Player import Player
                if self.following:
                    current_position = Player.GetXY()
                    is_casting = Agent.IsCasting(Player.GetAgentID())
                    is_moving = Agent.IsMoving(Player.GetAgentID())
                    is_knocked_down = Agent.IsKnockedDown(Player.GetAgentID())
                    is_dead = Agent.IsDead(Player.GetAgentID())

                    if is_casting or is_moving or is_knocked_down or is_dead:
                        return 

                     # Check if the wait timer has elapsed and re-enable movement checks
                    if self.wait_timer.HasElapsed(1000):
                        self.wait_timer.Reset()
                        self.wait_timer_run_once = True

                    # Check if the player has arrived at the waypoint
                    if self.calculate_distance(current_position, self.waypoint) <= self.tolerance:
                        self.arrived = True
                        self.following = False
                        return

                    # Re-issue the move command if the player is not moving and not casting
                    if self.wait_timer_run_once:
                        # Use the move_to_waypoint function to reissue movement
                        if action_queue is None:
                            Player.Move(0,0) #reset movement pointer?
                            Player.Move(self.waypoint[0], self.waypoint[1])
                        else:
                            action_queue.add_action(Player.Move, self.waypoint[0]+1, self.waypoint[1]+1)
                            action_queue.add_action(Player.Move, self.waypoint[0], self.waypoint[1])
                            
                        self.wait_timer_run_once  = False  # Disable immediate re-issue
                        self.wait_timer.Start()  # Start the wait timer to prevent spamming movement
                        if log_actions:
                            ConsoleLog("FollowXY", f"Stopped, Reissue move", Console.MessageType.Info)       

            def get_time_elapsed(self):
                """
                Get the elapsed time since the player started moving.
                """
                return self.timer.GetElapsedTime()

            def get_distance_to_waypoint(self):
                """
                Get the distance between the player and the current waypoint.
                """
                from .Player import Player
                current_position = Player.GetXY()
                return Utils.Distance(current_position, self.waypoint)

            def is_following(self):
                """
                Check if the player is currently following a waypoint.
                """
                return self.following

            def has_arrived(self):
                """
                Check if the player has arrived at the current waypoint.
                """
                return self.arrived


        class PathHandler:
            def __init__(self, coordinates):
                """
                Purpose: Initialize the PathHandler with a list of coordinates.
                Args:
                    coordinates (list): A list of tuples representing the points (x, y).
                Returns: None
                """
                self.coordinates = coordinates
                self.index = 0
                self.reverse = False  # By default, move forward
                self.finished = False

            def get_current_point(self):
                """
                Purpose: Get the current point in the list of coordinates.
                Args: None
                Returns: tuple or None
                """
                if not self.coordinates or self.finished:
                    return None
                return self.coordinates[self.index]

            def advance(self):
                """
                Purpose: Advance the pointer in the list based on the current direction (forward or reverse).
                Args: None
                Returns: tuple or None (next point or None if finished)
                """
                if self.finished:
                    return None

                current_point = self.get_current_point()

                # Move forward or backward based on the direction
                if self.reverse:
                    if self.index > 0:
                        self.index -= 1
                    else:
                        self.finished = True
                else:
                    if self.index < len(self.coordinates) - 1:
                        self.index += 1
                    else:
                        self.finished = True

                return current_point

            def toggle_direction(self):
                """
                Purpose: Manually reverse the current direction of traversal.
                Args: None
                Returns: None
                """
                self.reverse = not self.reverse

            def reset(self):
                """
                Purpose: Reset the path traversal to the start or end depending on direction.
                Args: None
                Returns: None
                """
                self.index = 0 if not self.reverse else len(self.coordinates) - 1
                self.finished = False

            def is_finished(self):
                """
                Purpose: Check if the traversal has finished.
                Args: None
                Returns: bool
                """
                return self.finished

            def set_position(self, index):
                """
                Purpose: Set the current index in the list of coordinates.
                Args:
                    index (int): The index to set the position to.
                Returns: None
                """
                if 0 <= index < len(self.coordinates):
                    self.index = index
                    self.finished = False
                else:
                    raise IndexError(f"Index {index} out of bounds for coordinates list")

            def get_position(self):
                """
                Purpose: Get the current index in the list of coordinates.
                Args: None
                Returns: int
                """
                return self.index

            def get_position_count(self):
                """
                Purpose: Get the total number of positions in the list.
                Args: None
                Returns: int
                """
                return len(self.coordinates)
    
    #region Sequential
    class Sequential:
        class Player:
            @staticmethod
            def InteractTarget(action_queue:ActionQueueNode):
                from .Player import Player
                action_queue.add_action(Player.Interact, Player.GetTargetID())
                sleep(0.3)
                
            @staticmethod
            def SendDialog(dialog_id:str, action_queue:ActionQueueNode):
                from .Player import Player
                action_queue.add_action(Player.SendDialog, int(dialog_id, 16))
                sleep(0.3)

            @staticmethod
            def SetTitle(title_id:int, action_queue:ActionQueueNode, log=False):
                from .Player import Player
                action_queue.add_action(Player.SetActiveTitle, title_id)
                sleep(0.3)   
                if log:
                    ConsoleLog("SetTitle", f"Setting title to {title_id}", Console.MessageType.Info) 

                
        class Movement:
            @staticmethod
            def FollowPath(path_handler, movement_object, action_queue, custom_exit_condition= lambda: False):  
                movement_object.reset()

                while not (path_handler.is_finished() and movement_object.has_arrived()):
                    if custom_exit_condition():
                        break
                    #this routine performs the follow, it uses the same movement objects as the asynch method
                    movement_object.update(action_queue=action_queue)
                    if movement_object.is_following():
                        sleep(0.1)
                        continue
                        
                    point_to_follow = path_handler.advance()
                    if point_to_follow is not None:
                        movement_object.move_to_waypoint(point_to_follow[0], point_to_follow[1])
                        sleep(0.1)
                
        class Skills:
            @staticmethod
            def LoadSkillbar(skill_template:str, action_queue:ActionQueueNode, log=False):
                """
                Purpose: Load the specified skillbar.
                Args:
                    skill_template (str): The name of the skill template to load.
                    action_queue (ActionQueueNode): The action queue to add the skill load action to.
                    log (bool) Optional: Whether to log the action. Default is True.
                Returns: None
                """
                from .Skillbar import SkillBar
                action_queue.add_action(SkillBar.LoadSkillTemplate, skill_template)
                ConsoleLog("LoadSkillbar", f"Loading skill Template {skill_template}", log=log)
                sleep(0.5)
            
            @staticmethod    
            def CastSkillID (skill_id:int, action_queue:ActionQueueNode,extra_condition=True, log=False):
                from .Skillbar import SkillBar
                from .Skill import Skill
                from .Player import Player
                player_agent_id = Player.GetAgentID()
                enough_energy = Routines.Checks.Skills.HasEnoughEnergy(player_agent_id,skill_id)
                skill_ready = Routines.Checks.Skills.IsSkillIDReady(skill_id)
                
                if not(enough_energy and skill_ready and extra_condition):
                    return False
                action_queue.add_action(SkillBar.UseSkill, SkillBar.GetSlotBySkillID(skill_id))
                if log:
                    ConsoleLog("CastSkillID", f"Cast {Skill.GetName(skill_id)}, slot: {SkillBar.GetSlotBySkillID(skill_id)}", Console.MessageType.Info)
                return True
            
            
            @staticmethod
            def CastSkillSlot(slot:int, action_queue:ActionQueueNode,extra_condition=True, log=False):
                from .Skillbar import SkillBar
                from .Skill import Skill
                from .Player import Player
                player_agent_id = Player.GetAgentID()
                skill_id = SkillBar.GetSkillIDBySlot(slot)
                enough_energy = Routines.Checks.Skills.HasEnoughEnergy(player_agent_id,skill_id)
                skill_ready = Routines.Checks.Skills.IsSkillSlotReady(slot)
                
                if not(enough_energy and skill_ready and extra_condition):
                    return False
                action_queue.add_action(SkillBar.UseSkill, slot)
                if log:
                    ConsoleLog("CastSkillSlot", f"Cast {Skill.GetName(skill_id)}, slot: {SkillBar.GetSlotBySkillID(skill_id)}", Console.MessageType.Info)
                return True
                
        class Map:  
            @staticmethod
            def SetHardMode(action_queue:ActionQueueNode, log=False):
                from .Party import Party
                """
                Purpose: Set the map to hard mode.
                Args: None
                Returns: None
                """
                action_queue.add_action(Party.SetHardMode)
                sleep(0.5)
                ConsoleLog("SetHardMode", "Hard mode set.", Console.MessageType.Info, log=log)
                
                                
            @staticmethod
            def TravelToOutpost(outpost_id,action_queue:ActionQueueNode, log=False):
                """
                Purpose: Positions yourself safely on the outpost.
                Args:
                    outpost_id (int): The ID of the outpost to travel to.
                    action_queue (ActionQueueNode): The action queue to add the travel action to.
                    log (bool) Optional: Whether to log the action. Default is True.
                Returns: None
                """
                from .Party import Party
                from .Map import Map
                if Map.GetMapID() != outpost_id:
                    ConsoleLog("TravelToOutpost", f"Travelling to {Map.GetMapName(outpost_id)}", log=log)
                    action_queue.add_action(Map.Travel, outpost_id)
                    sleep(1)
                    waititng_for_map_load = True
                    while waititng_for_map_load:
                        if Map.IsMapReady() and Party.IsPartyLoaded() and Map.GetMapID() == outpost_id:
                            waititng_for_map_load = False
                            break
                        sleep(1)
                
                ConsoleLog("TravelToOutpost", f"Arrived at {Map.GetMapName(outpost_id)}", log=log)
    
            @staticmethod
            def WaitforMapLoad(map_id, log=False):
                """
                Purpose: Positions yourself safely on the outpost.
                Args:
                    outpost_id (int): The ID of the outpost to travel to.
                    action_queue (ActionQueueNode): The action queue to add the travel action to.
                    log (bool) Optional: Whether to log the action. Default is True.
                Returns: None
                """
                from .Party import Party
                from .Map import Map

                waititng_for_map_load = True
                while waititng_for_map_load:
                    if Map.IsMapReady() and Party.IsPartyLoaded() and Map.GetMapID() == map_id:
                        waititng_for_map_load = False
                        break
                    sleep(1)
                
                ConsoleLog("WaitforMapLoad", f"Arrived at {Map.GetMapName(map_id)}", log=log)
                
        class Agents:
            @staticmethod
            def ChangeTarget(agent_id, action_queue:ActionQueueNode):
                from .Player import Player
                action_queue.add_action(Player.ChangeTarget, agent_id)
                sleep(0.25)    
                
            @staticmethod
            def TargetNearestNPC(distance, action_queue:ActionQueueNode):
                nearest_npc = Routines.Agents.GetNearestNPC(distance)
                if nearest_npc != 0:
                    Routines.Sequential.Agents.ChangeTarget(nearest_npc, action_queue)

            @staticmethod
            def TargetNearestNPCXY(x,y,distance, action_queue:ActionQueueNode):
                nearest_npc = Routines.Agents.GetNearestNPCXY(x,y, distance)
                if nearest_npc != 0:
                    Routines.Sequential.Agents.ChangeTarget(nearest_npc, action_queue)
        
            @staticmethod
            def TargetNearestEnemy(distance, action_queue:ActionQueueNode):
                nearest_enemy = Routines.Agents.GetNearestEnemy(distance)
                if nearest_enemy != 0: 
                    Routines.Sequential.Agents.ChangeTarget(nearest_enemy, action_queue)
                
        class Merchant:
            @staticmethod
            def SellItems(item_array:list[int], action_queue:ActionQueueNode, log=False):
                from .Item import Item
                from .Merchant import Trading
                if len(item_array) == 0:
                    action_queue.clear()
                    return
                
                for item_id in item_array:
                    quantity = Item.Properties.GetQuantity(item_id)
                    value = Item.Properties.GetValue(item_id)
                    cost = quantity * value
                    action_queue.add_action(Trading.Merchant.SellItem, item_id, cost)
                       
                while not action_queue.is_empty():
                    sleep(0.35)
                
                if log:
                    ConsoleLog("SellItems", f"Sold {len(item_array)} items.", Console.MessageType.Info)

            @staticmethod
            def BuyIDKits(kits_to_buy:int, action_queue:ActionQueueNode, log=False):
                from .Item import Item
                from .ItemArray import ItemArray
                from .Merchant import Trading
                if kits_to_buy <= 0:
                    action_queue.clear()
                    return

                merchant_item_list = Trading.Merchant.GetOfferedItems()
                merchant_item_list = ItemArray.Filter.ByCondition(merchant_item_list, lambda item_id: Item.GetModelID(item_id) == 5899)

                if len(merchant_item_list) == 0:
                    action_queue.clear()
                    return
                
                for i in range(kits_to_buy):
                    item_id = merchant_item_list[0]
                    value = Item.Properties.GetValue(item_id) * 2 # value reported is sell value not buy value
                    action_queue.add_action(Trading.Merchant.BuyItem, item_id, value)
                    
                while not action_queue.is_empty():
                    sleep(0.35)
                    
                if log:
                    ConsoleLog("BuyIDKits", f"Bought {kits_to_buy} ID Kits.", Console.MessageType.Info)

            @staticmethod
            def BuySalvageKits(kits_to_buy:int, action_queue:ActionQueueNode, log=False):
                from .Item import Item
                from .ItemArray import ItemArray
                from .Merchant import Trading
                if kits_to_buy <= 0:
                    action_queue.clear()
                    return

                merchant_item_list = Trading.Merchant.GetOfferedItems()
                merchant_item_list = ItemArray.Filter.ByCondition(merchant_item_list, lambda item_id: Item.GetModelID(item_id) == 2992)

                if len(merchant_item_list) == 0:
                    action_queue.clear()
                    return
                
                for i in range(kits_to_buy):
                    item_id = merchant_item_list[0]
                    value = Item.Properties.GetValue(item_id) * 2
                    action_queue.add_action(Trading.Merchant.BuyItem, item_id, value)
                    
                while not action_queue.is_empty():
                    sleep(0.35)
                
                if log:
                    ConsoleLog("BuySalvageKits", f"Bought {kits_to_buy} Salvage Kits.", Console.MessageType.Info)

        class Items:
            @staticmethod
            def _salvage_item(item_id):
                from .Inventory import Inventory
                salvage_kit = Inventory.GetFirstSalvageKit()
                if salvage_kit == 0:
                    ConsoleLog("SalvageItems", "No salvage kits found.", Console.MessageType.Warning)
                    return
                Inventory.SalvageItem(item_id, salvage_kit)
                
            @staticmethod
            def SalvageItems(item_array:list[int], action_queue:ActionQueueNode, log=False):
                from .Item import Item
                if len(item_array) == 0:
                    action_queue.clear()
                    return
                
                for item_id in item_array:
                    action_queue.add_action(Routines.Sequential.Items._salvage_item, item_id)
                    
                while not action_queue.is_empty():
                    sleep(0.35)
                    
                if log and len(item_array) > 0:
                    ConsoleLog("SalvageItems", f"Salvaged {len(item_array)} items.", Console.MessageType.Info)
                    
            @staticmethod
            def _identify_item(item_id):
                from .Inventory import Inventory
                id_kit = Inventory.GetFirstIDKit()
                if id_kit == 0:
                    ConsoleLog("IdentifyItems", "No ID kits found.", Console.MessageType.Warning)
                    return
                Inventory.IdentifyItem(item_id, id_kit)
                
            @staticmethod
            def IdentifyItems(item_array:list[int], action_queue:ActionQueueNode, log=False):
                from .Item import Item
                if len(item_array) == 0:
                    action_queue.clear()
                    return
                
                for item_id in item_array:
                    action_queue.add_action(Routines.Sequential.Items._identify_item, item_id)
                    
                while not action_queue.is_empty():
                    sleep(0.35)
                    
                if log and len(item_array) > 0:
                    ConsoleLog("IdentifyItems", f"Identified {len(item_array)} items.", Console.MessageType.Info)
                    
            @staticmethod
            def DepositItems(item_array:list[int], action_queue:ActionQueueNode, log=False):
                from .Inventory import Inventory
                if len(item_array) == 0:
                    action_queue.clear()
                    return
                
                total_items, total_capacity = Inventory.GetStorageSpace()
                free_slots = total_capacity - total_items
                
                if free_slots <= 0:
                    return

                for item_id in item_array:
                    action_queue.add_action(Inventory.DepositItemToStorage, item_id)
                    
                while not action_queue.is_empty():
                    sleep(0.35)
                    
                if log and len(item_array) > 0:
                    ConsoleLog("DepositItems", f"Deposited {len(item_array)} items.", Console.MessageType.Info)
                    
            @staticmethod
            def DepositGold(gold_amount_to_leave_on_character: int, action_queue: ActionQueueNode, log=False):
                from .Inventory import Inventory
                
                gold_amount_on_character = Inventory.GetGoldOnCharacter()
                gold_amount_on_storage = Inventory.GetGoldInStorage()
                
                max_allowed_gold = 100000  # Max storage limit
                available_space = max_allowed_gold - gold_amount_on_storage  # How much can be deposited

                # Calculate how much gold we need to deposit
                gold_to_deposit = gold_amount_on_character - gold_amount_to_leave_on_character

                # Ensure we do not deposit more than available storage space
                gold_to_deposit = min(gold_to_deposit, available_space)

                # If storage is full or no gold needs to be deposited, exit
                if available_space <= 0 or gold_to_deposit <= 0:
                    if log:
                        ConsoleLog("DepositGold", "No gold deposited (either storage full or not enough excess gold).", Console.MessageType.Warning)
                    return False

                # Perform the deposit
                action_queue.add_action(Inventory.DepositGold, gold_to_deposit)
                
                sleep(0.35)
                
                if log:
                    ConsoleLog("DepositGold", f"Deposited {gold_to_deposit} gold. Remaining on character: {gold_amount_to_leave_on_character}.", Console.MessageType.Success)
                
                return True

            @staticmethod
            def LootItems(item_array:list[int], action_queue:ActionQueueNode, log=False):
                from .Agent import Agent
                if len(item_array) == 0:
                    action_queue.clear()
                    return
                
                for item_id in item_array:
                    Routines.Sequential.Player.InteractTarget(action_queue)
                    
                while not action_queue.is_empty():
                    sleep(0.35)
                    
                if log and len(item_array) > 0:
                    ConsoleLog("LootItems", f"Looted {len(item_array)} items.", Console.MessageType.Info)


#endregion