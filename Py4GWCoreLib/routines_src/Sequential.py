from time import sleep
from typing import List, Tuple, Callable

import importlib

class _RProxy:
    def __getattr__(self, name: str):
        root_pkg = importlib.import_module("Py4GWCoreLib")
        return getattr(root_pkg.Routines, name)

Routines = _RProxy()

#region Sequential
class Sequential:
    class Player:
        @staticmethod
        def InteractAgent(agent_id:int):
            from ..GlobalCache import GLOBAL_CACHE
            GLOBAL_CACHE.Player.Interact(agent_id, False)
            sleep(0.1)
            
        @staticmethod
        def InteractTarget():
            from ..GlobalCache import GLOBAL_CACHE
            target_id = GLOBAL_CACHE.Player.GetTargetID()
            if target_id != 0:
                Sequential.Player.InteractAgent(target_id)

        @staticmethod
        def SendDialog(dialog_id:str):
            from ..GlobalCache import GLOBAL_CACHE
            GLOBAL_CACHE.Player.SendDialog(int(dialog_id, 16))
            sleep(0.3)

        @staticmethod
        def SetTitle(title_id:int, log=False):
            from ..GlobalCache import GLOBAL_CACHE
            from ..Py4GWcorelib import ConsoleLog, Console
            GLOBAL_CACHE.Player.SetActiveTitle(title_id)
            sleep(0.3)   
            if log:
                ConsoleLog("SetTitle", f"Setting title to {title_id}", Console.MessageType.Info) 

        @staticmethod
        def SendChatCommand(command:str, log=False):
            from ..GlobalCache import GLOBAL_CACHE
            from ..Py4GWcorelib import ConsoleLog, Console
            GLOBAL_CACHE.Player.SendChatCommand(command)
            sleep(0.3)
            if log:
                ConsoleLog("SendChatCommand", f"Sending chat command {command}", Console.MessageType.Info)

        @staticmethod
        def Move(x:float, y:float, log=False):
            from ..GlobalCache import GLOBAL_CACHE
            from ..Py4GWcorelib import ConsoleLog, Console
            GLOBAL_CACHE.Player.Move(x, y)
            sleep(0.1)
            if log:
                ConsoleLog("MoveTo", f"Moving to {x}, {y}", Console.MessageType.Info)

    class Movement:
        @staticmethod
        def FollowPath(path_points: List[Tuple[float, float]], custom_exit_condition:Callable[[], bool] =lambda: False, tolerance:float=150):
            import random
            from ..Player import Player
            from ..GlobalCache import GLOBAL_CACHE
            from ..Py4GWcorelib import Utils
            from .Checks import Checks

            for idx, (target_x, target_y) in enumerate(path_points):
                if not Checks.Map.MapValid():
                    return []
                    
                GLOBAL_CACHE.Player.Move(target_x, target_y)
                    
                current_x, current_y = Player.GetXY()
                previous_distance = Utils.Distance((current_x, current_y), (target_x, target_y))

                while True:
                    if custom_exit_condition():
                        return
                    
                    if not Checks.Map.MapValid():
                        return []
                    
                    
                    current_x, current_y = Player.GetXY()
                    current_distance = Utils.Distance((current_x, current_y), (target_x, target_y))
                    
                    # If not getting closer, enforce move
                    if not (current_distance < previous_distance):
                        # Inside reissue logic
                        offset_x = random.uniform(-5, 5)
                        offset_y = random.uniform(-5, 5)
                        GLOBAL_CACHE.Player.Move(target_x + offset_x, target_y + offset_y)
                    previous_distance = current_distance                    
                    
                    # Check if arrived
                    if current_distance <= tolerance:
                        break  # Arrived at this waypoint, move to next

                    sleep(0.5)

    class Skills:
        @staticmethod
        def LoadSkillbar(skill_template:str, log=False):
            """
            Purpose: Load the specified skillbar.
            Args:
                skill_template (str): The name of the skill template to load.
                log (bool) Optional: Whether to log the action. Default is True.
            Returns: None
            """
            from ..GlobalCache import GLOBAL_CACHE
            from ..Py4GWcorelib import ConsoleLog, Console
            GLOBAL_CACHE.SkillBar.LoadSkillTemplate(skill_template)
            ConsoleLog("LoadSkillbar", f"Loading skill Template {skill_template}", log=log)
            sleep(0.5)
        
        @staticmethod    
        def CastSkillID (skill_id:int,extra_condition=True, log=False):
            from ..GlobalCache import GLOBAL_CACHE
            from ..Py4GWcorelib import ConsoleLog, Console
            from .Checks import Checks
            from ..Map import Map
            if not Map.IsMapReady():
                return False
            player_agent_id = GLOBAL_CACHE.Player.GetAgentID()
            enough_energy = Checks.Skills.HasEnoughEnergy(player_agent_id,skill_id)
            skill_ready = Checks.Skills.IsSkillIDReady(skill_id)
            
            if not(enough_energy and skill_ready and extra_condition):
                return False
            
            GLOBAL_CACHE.SkillBar.UseSkill(GLOBAL_CACHE.SkillBar.GetSlotBySkillID(skill_id))
            if log:
                ConsoleLog("CastSkillID", f"Cast {GLOBAL_CACHE.Skill.GetName(skill_id)}, slot: {GLOBAL_CACHE.SkillBar.GetSlotBySkillID(skill_id)}", Console.MessageType.Info)
            return True

        @staticmethod
        def CastSkillSlot(slot:int,extra_condition=True, log=False):
            from ..GlobalCache import GLOBAL_CACHE
            from ..Py4GWcorelib import ConsoleLog, Console
            from .Checks import Checks
            player_agent_id = GLOBAL_CACHE.Player.GetAgentID()
            skill_id = GLOBAL_CACHE.SkillBar.GetSkillIDBySlot(slot)
            enough_energy = Checks.Skills.HasEnoughEnergy(player_agent_id,skill_id)
            skill_ready = Checks.Skills.IsSkillSlotReady(slot)
            
            if not(enough_energy and skill_ready and extra_condition):
                return False
            
            GLOBAL_CACHE.SkillBar.UseSkill(slot)
            if log:
                ConsoleLog("CastSkillSlot", f"Cast {GLOBAL_CACHE.Skill.GetName(skill_id)}, slot: {GLOBAL_CACHE.SkillBar.GetSlotBySkillID(skill_id)}", Console.MessageType.Info)
            return True
            
    class Map:  
        @staticmethod
        def SetHardMode(log=False):
            """
            Purpose: Set the map to hard mode.
            Args: None
            Returns: None
            """
            from ..GlobalCache import GLOBAL_CACHE
            from ..Py4GWcorelib import ConsoleLog, Console
            GLOBAL_CACHE.Party.SetHardMode()
            sleep(0.5)
            ConsoleLog("SetHardMode", "Hard mode set.", Console.MessageType.Info, log=log)

        @staticmethod
        def TravelToOutpost(outpost_id, log=False):
            """
            Purpose: Positions yourself safely on the outpost.
            Args:
                outpost_id (int): The ID of the outpost to travel to.
                log (bool) Optional: Whether to log the action. Default is True.
            Returns: None
            """
            from ..GlobalCache import GLOBAL_CACHE
            from ..Map import Map
            from ..Py4GWcorelib import ConsoleLog, Console
            if Map.GetMapID() != outpost_id:
                ConsoleLog("TravelToOutpost", f"Travelling to {Map.GetMapName(outpost_id)}", log=log)
                Map.Travel(outpost_id)
                sleep(3)
                waititng_for_map_load = True
                while waititng_for_map_load:
                    if Map.IsMapReady() and GLOBAL_CACHE.Party.IsPartyLoaded() and Map.GetMapID() == outpost_id:
                        waititng_for_map_load = False
                        break
                    sleep(1)
                sleep(1)
            
            ConsoleLog("TravelToOutpost", f"Arrived at {Map.GetMapName(outpost_id)}", log=log)

        @staticmethod
        def WaitforMapLoad(map_id, log=False):
            """
            Purpose: Positions yourself safely on the map.
            Args:
                outpost_id (int): The ID of the map to travel to.
                log (bool) Optional: Whether to log the action. Default is True.
            Returns: None
            """
            from ..GlobalCache import GLOBAL_CACHE
            from ..Py4GWcorelib import ConsoleLog
            from ..Agent import Agent
            from ..Map import Map
            waititng_for_map_load = True
            while waititng_for_map_load:
                if not (Map.IsMapReady() and GLOBAL_CACHE.Party.IsPartyLoaded() and Map.GetMapID() == map_id):
                    sleep(1)
                else:
                    waititng_for_map_load = False
                    break
            
            ConsoleLog("WaitforMapLoad", f"Arrived at {Map.GetMapName(map_id)}", log=log)
            sleep(1)
            
    class Agents:
        @staticmethod
        def GetAgentIDByName(agent_name):
            from ..GlobalCache import GLOBAL_CACHE
            from ..AgentArray import AgentArray
            from ..Agent import Agent   
            agent_ids = AgentArray.GetAgentArray()
            agent_names = {}

            # Request all names
            for agent_id in agent_ids:
                Agent.RequestName(agent_id)

            # Wait until all names are ready (with timeout safeguard)
            timeout = 2.0  # seconds
            poll_interval = 0.1
            elapsed = 0.0

            while elapsed < timeout:
                all_ready = True
                for agent_id in agent_ids:
                    if not Agent.IsNameReady(agent_id):
                        all_ready = False
                        break  # no need to check further

                if all_ready:
                    break  # exit early, all names ready

                sleep(poll_interval)
                elapsed += poll_interval

            # Populate agent_names dictionary
            for agent_id in agent_ids:
                if Agent.IsNameReady(agent_id):
                    agent_names[agent_id] = Agent.GetNameByID(agent_id)

            # Partial, case-insensitive match
            search_lower = agent_name.lower()
            for agent_id, name in agent_names.items():
                if search_lower in name.lower():
                    return agent_id

            return 0  # Not found
        
        @staticmethod
        def GetAgentIDByModelID(model_id:int):
            """
            Purpose: Get the agent ID by model ID.
            Args:
                model_id (int): The model ID of the agent.
            Returns: int: The agent ID or 0 if not found.
            """
            from ..GlobalCache import GLOBAL_CACHE
            from ..Py4GWcorelib import ConsoleLog, Console
            from ..AgentArray import AgentArray
            from ..Agent import Agent
            agent_ids = AgentArray.GetAgentArray()
            for agent_id in agent_ids:
                if Agent.GetModelID(agent_id) == model_id:
                    return agent_id
            return 0

        @staticmethod
        def ChangeTarget(agent_id):
            from ..GlobalCache import GLOBAL_CACHE
            if agent_id != 0:
                GLOBAL_CACHE.Player.ChangeTarget(agent_id)
                sleep(0.25)    
            
        @staticmethod
        def TargetAgentByName(agent_name:str):
            agent_id = Sequential.Agents.GetAgentIDByName(agent_name)
            if agent_id != 0:
                Sequential.Agents.ChangeTarget(agent_id)

        @staticmethod
        def TargetNearestNPC(distance:float = 4500.0):
            from .Agents import Agents
            nearest_npc = Agents.GetNearestNPC(distance)
            if nearest_npc != 0:
                Sequential.Agents.ChangeTarget(nearest_npc)

        @staticmethod
        def TargetNearestNPCXY(x,y,distance):
            from .Agents import Agents
            nearest_npc = Agents.GetNearestNPCXY(x,y, distance)
            if nearest_npc != 0:
                Sequential.Agents.ChangeTarget(nearest_npc)
    
        @staticmethod
        def TargetNearestEnemy(distance):
            from .Agents import Agents
            nearest_enemy = Agents.GetNearestEnemy(distance)
            if nearest_enemy != 0: 
                Sequential.Agents.ChangeTarget(nearest_enemy)
        
        @staticmethod
        def TargetNearestItem(distance):
            from .Agents import Agents
            nearest_item = Agents.GetNearestItem(distance)
            if nearest_item != 0:
                Sequential.Agents.ChangeTarget(nearest_item)
                
        @staticmethod
        def TargetNearestChest(distance):
            from .Agents import Agents
            nearest_chest = Agents.GetNearestChest(distance)
            if nearest_chest != 0:
                Sequential.Agents.ChangeTarget(nearest_chest)
                
        @staticmethod
        def InteractWithNearestChest():
            """Target and interact with chest and items."""
            from ..Py4GWcorelib import ActionQueueManager
            from ..Py4GWcorelib import LootConfig
            from ..Py4GWcorelib import Utils
            from ..GlobalCache import GLOBAL_CACHE
            from ..enums_src.GameData_enums import Range
            from .Agents import Agents
            from ..Agent import Agent
            nearest_chest = Agents.GetNearestChest(2500)
            chest_x, chest_y = Agent.GetXY(nearest_chest)


            Sequential.Movement.FollowPath([(chest_x, chest_y)])
            sleep(0.5)
        
            Sequential.Player.InteractAgent(nearest_chest)
            sleep(0.5)
            ActionQueueManager().AddAction("ACTION",GLOBAL_CACHE.Player.SendDialog, 2)
            sleep(1)

            Sequential.Agents.TargetNearestItem(distance=300)
            filtered_loot = LootConfig().GetfilteredLootArray(Range.Area.value, multibox_loot= True)
            item = Utils.GetFirstFromArray(filtered_loot)
            Sequential.Agents.ChangeTarget(item)
            Sequential.Player.InteractTarget()
            sleep(1)
            
        @staticmethod
        def InteractWithAgentByName(agent_name:str):
            from ..GlobalCache import GLOBAL_CACHE
            from ..Agent import Agent
            Sequential.Agents.TargetAgentByName(agent_name)
            agent_x, agent_y = Agent.GetXY(GLOBAL_CACHE.Player.GetTargetID())

            Sequential.Movement.FollowPath([(agent_x, agent_y)])
            sleep(0.5)
            
            Sequential.Player.InteractTarget()
            sleep(1)
            
        @staticmethod
        def InteractWithAgentXY(x:float, y:float):
            from ..GlobalCache import GLOBAL_CACHE
            from ..Agent import Agent
            Sequential.Agents.TargetNearestNPCXY(x, y, 100)
            agent_x, agent_y = Agent.GetXY(GLOBAL_CACHE.Player.GetTargetID())

            Sequential.Movement.FollowPath([(agent_x, agent_y)])
            sleep(1)
            
            Sequential.Player.InteractTarget()
            sleep(1)
            
    class Merchant:
        @staticmethod
        def SellItems(item_array:list[int], log=False):
            from Py4GWCoreLib import ActionQueueManager
            from ..GlobalCache import GLOBAL_CACHE
            from ..Py4GWcorelib import ConsoleLog, Console
            if len(item_array) == 0:
                ActionQueueManager().ResetQueue("MERCHANT")
                return
            
            for item_id in item_array:
                quantity = GLOBAL_CACHE.Item.Properties.GetQuantity(item_id)
                value = GLOBAL_CACHE.Item.Properties.GetValue(item_id)
                cost = quantity * value
                GLOBAL_CACHE.Trading.Merchant.SellItem(item_id, cost)
                    
            while not ActionQueueManager().IsEmpty("MERCHANT"):
                sleep(0.35)
            
            if log:
                ConsoleLog("SellItems", f"Sold {len(item_array)} items.", Console.MessageType.Info)

        @staticmethod
        def BuyIDKits(kits_to_buy:int, log=False):
            from ..ItemArray import ItemArray
            from Py4GWCoreLib import ActionQueueManager
            from ..GlobalCache import GLOBAL_CACHE
            from ..Py4GWcorelib import ConsoleLog, Console
            if kits_to_buy <= 0:
                ActionQueueManager().ResetQueue("MERCHANT")
                return

            merchant_item_list = GLOBAL_CACHE.Trading.Merchant.GetOfferedItems()
            merchant_item_list = ItemArray.Filter.ByCondition(merchant_item_list, lambda item_id: GLOBAL_CACHE.Item.GetModelID(item_id) == 5899)

            if len(merchant_item_list) == 0:
                ActionQueueManager().ResetQueue("MERCHANT")
                return
            
            for i in range(kits_to_buy):
                item_id = merchant_item_list[0]
                value = GLOBAL_CACHE.Item.Properties.GetValue(item_id) * 2 # value reported is sell value not buy value
                GLOBAL_CACHE.Trading.Merchant.BuyItem(item_id, value)
                
            while not ActionQueueManager().IsEmpty("MERCHANT"):
                sleep(0.35)
                
            if log:
                ConsoleLog("BuyIDKits", f"Bought {kits_to_buy} ID Kits.", Console.MessageType.Info)

        @staticmethod
        def BuySalvageKits(kits_to_buy:int, log=False):
            from ..ItemArray import ItemArray
            from Py4GWCoreLib import ActionQueueManager
            from ..GlobalCache import GLOBAL_CACHE
            from ..Py4GWcorelib import ConsoleLog, Console
            if kits_to_buy <= 0:
                ActionQueueManager().ResetQueue("MERCHANT")
                return

            merchant_item_list = GLOBAL_CACHE.Trading.Merchant.GetOfferedItems()
            merchant_item_list = ItemArray.Filter.ByCondition(merchant_item_list, lambda item_id: GLOBAL_CACHE.Item.GetModelID(item_id) == 2992)

            if len(merchant_item_list) == 0:
                ActionQueueManager().ResetQueue("MERCHANT")
                return
            
            for i in range(kits_to_buy):
                item_id = merchant_item_list[0]
                value = GLOBAL_CACHE.Item.Properties.GetValue(item_id) * 2
                GLOBAL_CACHE.Trading.Merchant.BuyItem(item_id, value)
                
            while not ActionQueueManager().IsEmpty("MERCHANT"):
                sleep(0.35)
            
            if log:
                ConsoleLog("BuySalvageKits", f"Bought {kits_to_buy} Salvage Kits.", Console.MessageType.Info)

    class Items:
        @staticmethod
        def _salvage_item(item_id):
            from ..Inventory import Inventory
            from ..GlobalCache import GLOBAL_CACHE
            from ..Py4GWcorelib import ConsoleLog, Console
            salvage_kit = GLOBAL_CACHE.Inventory.GetFirstSalvageKit()
            if salvage_kit == 0:
                ConsoleLog("SalvageItems", "No salvage kits found.", Console.MessageType.Warning)
                return
            Inventory.SalvageItem(item_id, salvage_kit)
            
        @staticmethod
        def SalvageItems(item_array:list[int], log=False):
            from Py4GWCoreLib import ActionQueueManager
            from ..Inventory import Inventory
            from ..Py4GWcorelib import ConsoleLog, Console
            if len(item_array) == 0:
                ActionQueueManager().ResetQueue("SALVAGE")
                return
            
            for item_id in item_array:
                ActionQueueManager().AddAction("SALVAGE",Sequential.Items._salvage_item, item_id)
                ActionQueueManager().AddAction("SALVAGE",Inventory.AcceptSalvageMaterialsWindow)
            while not ActionQueueManager().IsEmpty("SALVAGE"):
                sleep(0.35)
                
            if log and len(item_array) > 0:
                ConsoleLog("SalvageItems", f"Salvaged {len(item_array)} items.", Console.MessageType.Info)
                
        @staticmethod
        def _identify_item(item_id):
            from ..GlobalCache import GLOBAL_CACHE
            from ..Py4GWcorelib import ConsoleLog, Console
            from ..Inventory import Inventory
            id_kit = GLOBAL_CACHE.Inventory.GetFirstIDKit()
            if id_kit == 0:
                ConsoleLog("IdentifyItems", "No ID kits found.", Console.MessageType.Warning)
                return
            Inventory.IdentifyItem(item_id, id_kit)
            
        @staticmethod
        def IdentifyItems(item_array:list[int], log=False):
            from Py4GWCoreLib import ActionQueueManager
            from ..Py4GWcorelib import ConsoleLog, Console
            if len(item_array) == 0:
                ActionQueueManager().ResetQueue("IDENTIFY")
                return
            
            for item_id in item_array:
                ActionQueueManager().AddAction("IDENTIFY",Sequential.Items._identify_item, item_id)
                
            while not ActionQueueManager().IsEmpty("IDENTIFY"):
                sleep(0.35)
                
            if log and len(item_array) > 0:
                ConsoleLog("IdentifyItems", f"Identified {len(item_array)} items.", Console.MessageType.Info)
                
        @staticmethod
        def DepositItems(item_array:list[int], log=False):
            from Py4GWCoreLib import ActionQueueManager
            from ..GlobalCache import GLOBAL_CACHE
            from ..Py4GWcorelib import ConsoleLog, Console
            if len(item_array) == 0:
                ActionQueueManager().ResetQueue("ACTION")
                return
            
            total_items, total_capacity = GLOBAL_CACHE.Inventory.GetStorageSpace()
            free_slots = total_capacity - total_items
            
            if free_slots <= 0:
                return

            for item_id in item_array:
                GLOBAL_CACHE.Inventory.DepositItemToStorage(item_id)
                
            while not ActionQueueManager().IsEmpty("ACTION"):
                sleep(0.35)
                
            if log and len(item_array) > 0:
                ConsoleLog("DepositItems", f"Deposited {len(item_array)} items.", Console.MessageType.Info)
                
        @staticmethod
        def DepositGold(gold_amount_to_leave_on_character: int, log=False):
            from ..GlobalCache import GLOBAL_CACHE
            from ..Py4GWcorelib import ConsoleLog, Console
            gold_amount_on_character = GLOBAL_CACHE.Inventory.GetGoldOnCharacter()
            gold_amount_on_storage = GLOBAL_CACHE.Inventory.GetGoldInStorage()
            
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
            GLOBAL_CACHE.Inventory.DepositGold(gold_to_deposit)
            
            sleep(0.35)
            
            if log:
                ConsoleLog("DepositGold", f"Deposited {gold_to_deposit} gold. Remaining on character: {gold_amount_to_leave_on_character}.", Console.MessageType.Success)
            
            return True

        @staticmethod
        def LootItems(item_array:list[int], log=False):
            from ..Agent import Agent
            from ..GlobalCache import GLOBAL_CACHE
            from ..Py4GWcorelib import ConsoleLog, Console, ActionQueueManager
            from .Checks import Checks
            if len(item_array) == 0:
                return
            
            if not Checks.Map.MapValid():
                ActionQueueManager().ResetAllQueues()
                return

            while len (item_array) > 0:
                item_id = item_array.pop(0)
                if item_id == 0:
                    continue
                if not Agent.IsValid(item_id):
                    continue
                item_x, item_y = Agent.GetXY(item_id)
                if not Checks.Map.MapValid():
                    ActionQueueManager().ResetAllQueues()
                    return
                Sequential.Movement.FollowPath([(item_x, item_y)])
                if not Checks.Map.MapValid():
                    ActionQueueManager().ResetAllQueues()
                    return
                if Agent.IsValid(item_id):
                    GLOBAL_CACHE.Player.Interact(item_id, False)
                    sleep(1.250)
                
            if log and len(item_array) > 0:
                ConsoleLog("LootItems", f"Looted {len(item_array)} items.", Console.MessageType.Info)


#endregion