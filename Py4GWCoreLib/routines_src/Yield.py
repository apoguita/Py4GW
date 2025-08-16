from typing import List, Tuple, Callable, Optional, Generator, Any
from ..GlobalCache import GLOBAL_CACHE
from ..Py4GWcorelib import ConsoleLog, Console, Utils, ActionQueueManager


import importlib, typing

class _RProxy:
    def __getattr__(self, name: str):
        root_pkg = importlib.import_module("Py4GWCoreLib")
        return getattr(root_pkg.Routines, name)

Routines = _RProxy()


#region yield
class Yield:
    @staticmethod
    def wait(ms: int):
        import time
        start = time.time()
        while (time.time() - start) * 1000 < ms:
            yield
            
    class Player:
        @staticmethod
        def InteractAgent(agent_id:int):
            GLOBAL_CACHE.Player.Interact(agent_id, False)
            yield from Yield.wait(100)
            
        @staticmethod
        def InteractTarget():
            
            target_id = GLOBAL_CACHE.Player.GetTargetID()
            if target_id != 0:
                yield from Yield.Player.InteractAgent(target_id)

        @staticmethod
        def SendDialog(dialog_id:str):
            
            GLOBAL_CACHE.Player.SendDialog(int(dialog_id, 16))
            yield from Yield.wait(300)

        @staticmethod
        def SetTitle(title_id:int, log=False):
            

            GLOBAL_CACHE.Player.SetActiveTitle(title_id)
            yield from Yield.wait(300)   
            if log:
                ConsoleLog("SetTitle", f"Setting title to {title_id}", Console.MessageType.Info) 

        @staticmethod
        def SendChatCommand(command:str, log=False):
            

            GLOBAL_CACHE.Player.SendChatCommand(command)
            yield from Yield.wait(300)
            if log:
                ConsoleLog("SendChatCommand", f"Sending chat command {command}", Console.MessageType.Info)

        @staticmethod
        def Move(x:float, y:float, log=False):
            

            GLOBAL_CACHE.Player.Move(x, y)
            yield from Yield.wait(100)
            if log:
                ConsoleLog("MoveTo", f"Moving to {x}, {y}", Console.MessageType.Info)

    class Movement:
        @staticmethod
        def FollowPath(
            path_points: List[Tuple[float, float]],
            custom_exit_condition: Callable[[], bool] = lambda: False,
            tolerance: float = 150,
            log: bool = False,
            timeout: int = -1,
            progress_callback: Optional[Callable[[float], None]] = None,
            custom_pause_fn: Optional[Callable[[], bool]] = None 
        ):
            import random
            from .Checks import Checks
            
            total_points = len(path_points)

            for idx, (target_x, target_y) in enumerate(path_points):
                start_time = Utils.GetBaseTimestamp()
                
                if not Checks.Map.MapValid():
                    ActionQueueManager().ResetAllQueues()
                    return False

                GLOBAL_CACHE.Player.Move(target_x, target_y)

                current_x, current_y = GLOBAL_CACHE.Player.GetXY()
                previous_distance = Utils.Distance((current_x, current_y), (target_x, target_y))

                while True:
                    if custom_exit_condition():
                        if log:
                            ConsoleLog("FollowPath", "Custom exit condition met, stopping movement.", Console.MessageType.Info)
                        return False

                    if not Checks.Map.MapValid():
                        ActionQueueManager().ResetAllQueues()
                        return False
                    
                    if custom_pause_fn:
                        while custom_pause_fn():
                            if log:
                                ConsoleLog("FollowPath", "Custom pause condition active, pausing movement...", Console.MessageType.Debug)
                            start_time = Utils.GetBaseTimestamp()  # Reset timeout timer
                            yield from Yield.wait(500)
                    

                    current_time = Utils.GetBaseTimestamp()
                    delta = current_time - start_time
                    if delta > timeout and timeout > 0:
                        ConsoleLog("FollowPath", "Timeout reached, stopping movement.", Console.MessageType.Warning)
                        return False

                    current_x, current_y = GLOBAL_CACHE.Player.GetXY()
                    current_distance = Utils.Distance((current_x, current_y), (target_x, target_y))

                    if not (current_distance < previous_distance):
                        offset_x = random.uniform(-5, 5)
                        offset_y = random.uniform(-5, 5)
                        if log:
                            ConsoleLog("FollowPath", f"move to {target_x + offset_x}, {target_y + offset_y}", Console.MessageType.Info)
                        if not Checks.Map.MapValid():
                            ActionQueueManager().ResetAllQueues()
                            return False
                        GLOBAL_CACHE.Player.Move(target_x + offset_x, target_y + offset_y)

                    previous_distance = current_distance

                    if current_distance <= tolerance:
                        break
                    else:
                        if log:
                            ConsoleLog("FollowPath", f"Current distance to target: {current_distance}, waiting...", Console.MessageType.Info)

                    yield from Yield.wait(250)

                #After reaching each point, report progress
                if progress_callback:
                    progress_callback((idx + 1) / total_points)

            return True


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
            

            GLOBAL_CACHE.SkillBar.LoadSkillTemplate(skill_template)
            ConsoleLog("LoadSkillbar", f"Loading skill Template {skill_template}", log=log)
            yield from Yield.wait(500)
        
        @staticmethod    
        def CastSkillID (skill_id:int,extra_condition=True, aftercast_delay=0,  log=False):
            from .Checks import Checks
            

            if not GLOBAL_CACHE.Map.IsMapReady():
                return False
            player_agent_id = GLOBAL_CACHE.Player.GetAgentID()
            enough_energy = Checks.Skills.HasEnoughEnergy(player_agent_id,skill_id)
            skill_ready = Checks.Skills.IsSkillIDReady(skill_id)
            
            if not(enough_energy and skill_ready and extra_condition):
                return False
            GLOBAL_CACHE.SkillBar.UseSkill(GLOBAL_CACHE.SkillBar.GetSlotBySkillID(skill_id), aftercast_delay=aftercast_delay)
            if log:
                ConsoleLog("CastSkillID", f"Cast {GLOBAL_CACHE.Skill.GetName(skill_id)}, slot: {GLOBAL_CACHE.SkillBar.GetSlotBySkillID(skill_id)}", Console.MessageType.Info)
            return True

        @staticmethod
        def CastSkillSlot(slot:int,extra_condition=True, aftercast_delay=0, log=False):
            from .Checks import Checks
            

            player_agent_id = GLOBAL_CACHE.Player.GetAgentID()
            skill_id = GLOBAL_CACHE.SkillBar.GetSkillIDBySlot(slot)
            enough_energy = Checks.Skills.HasEnoughEnergy(player_agent_id,skill_id)
            skill_ready = Checks.Skills.IsSkillSlotReady(slot)
            
            if not(enough_energy and skill_ready and extra_condition):
                return False
            GLOBAL_CACHE.SkillBar.UseSkill(slot, aftercast_delay=aftercast_delay)
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
            

            GLOBAL_CACHE.Party.SetHardMode()
            yield from Yield.wait(500)
            ConsoleLog("SetHardMode", "Hard mode set.", Console.MessageType.Info, log=log)

        @staticmethod
        def TravelToOutpost(outpost_id, log=False, timeout:int=10000):
            """
            Purpose: Positions yourself safely on the outpost.
            Args:
                outpost_id (int): The ID of the outpost to travel to.
                log (bool) Optional: Whether to log the action. Default is True.
            Returns: None
            """
            
            from ..Py4GWcorelib import ConsoleLog, Utils
            start_time = Utils.GetBaseTimestamp()
            if GLOBAL_CACHE.Map.GetMapID() != outpost_id:
                ConsoleLog("TravelToOutpost", f"Travelling to {GLOBAL_CACHE.Map.GetMapName(outpost_id)}", log=log)
                GLOBAL_CACHE.Map.Travel(outpost_id)
                yield from Yield.wait(3000)
                waititng_for_map_load = True
                while waititng_for_map_load:
                    if GLOBAL_CACHE.Map.IsMapReady() and GLOBAL_CACHE.Party.IsPartyLoaded() and GLOBAL_CACHE.Map.GetMapID() == outpost_id:
                        waititng_for_map_load = False
                        break
                    delta = Utils.GetBaseTimestamp() - start_time
                    if delta > timeout and timeout > 0:
                        ConsoleLog("TravelToOutpost", "Timeout reached, stopping waiting for map load.", log=log)
                        return False
                    yield from Yield.wait(1000)
                yield from Yield.wait(1000)
            
            ConsoleLog("TravelToOutpost", f"Arrived at {GLOBAL_CACHE.Map.GetMapName(outpost_id)}", log=log)
            return True

        @staticmethod
        def TravelToRegion(outpost_id, region, district, language=0, log=False):
            """
            Purpose: Positions yourself safely on the outpost.
            Args:
                outpost_id (int): The ID of the outpost to travel to.
                region (int): The region ID to travel to.
                district (int): The district ID to travel to.
                laguage (int): The language ID to travel to. Default is 0.
                log (bool) Optional: Whether to log the action. Default is True.
            Returns: None
            """
            
            from ..Py4GWcorelib import ConsoleLog
            
            if GLOBAL_CACHE.Map.GetMapID() != outpost_id:
                ConsoleLog("TravelToRegion", f"Travelling to {GLOBAL_CACHE.Map.GetMapName(outpost_id)}", log=log)
                GLOBAL_CACHE.Map.TravelToRegion(outpost_id, region, district, language)
                yield from Yield.wait(2000)
                waititng_for_map_load = True
                while waititng_for_map_load:
                    if GLOBAL_CACHE.Map.IsMapReady() and GLOBAL_CACHE.Party.IsPartyLoaded() and GLOBAL_CACHE.Map.GetMapID() == outpost_id:
                        waititng_for_map_load = False
                        break
                    yield from Yield.wait(1000)
                yield from Yield.wait(1000)
            
            ConsoleLog("TravelToRegion", f"Arrived at {GLOBAL_CACHE.Map.GetMapName(outpost_id)}", log=log)


        @staticmethod
        def WaitforMapLoad(map_id, log=False, timeout:int=10000):
            from .Checks import Checks
            
            from ..Py4GWcorelib import ConsoleLog, Utils
            """
            Purpose: Positions yourself safely on the map.
            Args:
                outpost_id (int): The ID of the map to travel to.
                log (bool) Optional: Whether to log the action. Default is True.
            Returns: None
            """
            yield from Yield.wait(1000)
            start_time = Utils.GetBaseTimestamp()
            waititng_for_map_load = True
            while waititng_for_map_load:
                if not Checks.Map.MapValid():
                    yield from Yield.wait(1000)
                    ConsoleLog("WaitforMapLoad", "Map not valid, waiting...", log=log)
                    continue
                
                delta = Utils.GetBaseTimestamp() - start_time
                if delta > timeout and timeout > 0:
                    ConsoleLog("WaitforMapLoad", "Timeout reached, stopping waiting for map load.", log=log)
                    return False
                    
                current_map = GLOBAL_CACHE.Map.GetMapID()
                
                if (GLOBAL_CACHE.Map.IsExplorable() or GLOBAL_CACHE.Map.IsOutpost()) and current_map != map_id:
                    ConsoleLog("WaitforMapLoad", f"Something went wrong, halting", log=log)
                    yield from Yield.wait(1000)
                    return False
                
                if not current_map == map_id:
                    yield from Yield.wait(1000)
                    ConsoleLog("WaitforMapLoad", f"Waiting for map load {map_id} (current: {current_map})", log=log)
                    continue
            
                waititng_for_map_load = False

            
            ConsoleLog("WaitforMapLoad", f"Arrived at {GLOBAL_CACHE.Map.GetMapName(map_id)}", log=log)
            yield from Yield.wait(1000)
            return True
            
    class Agents:
        @staticmethod
        def GetAgentIDByName(agent_name):
            
            agent_ids = GLOBAL_CACHE.AgentArray.GetAgentArray()
            agent_names = {}

            # Request all names
            for agent_id in agent_ids:
                GLOBAL_CACHE.Agent.RequestName(agent_id)

            # Wait until all names are ready (with timeout safeguard)
            timeout = 2.0  # seconds
            poll_interval = 0.1
            elapsed = 0.0

            while elapsed < timeout:
                all_ready = True
                for agent_id in agent_ids:
                    if not GLOBAL_CACHE.Agent.IsNameReady(agent_id):
                        all_ready = False
                        break  # no need to check further

                if all_ready:
                    break  # exit early, all names ready

                yield from Yield.wait(int(poll_interval) * 1000)
                elapsed += poll_interval

            # Populate agent_names dictionary
            for agent_id in agent_ids:
                if GLOBAL_CACHE.Agent.IsNameReady(agent_id):
                    agent_names[agent_id] = GLOBAL_CACHE.Agent.GetName(agent_id)

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
            
            agent_ids = GLOBAL_CACHE.AgentArray.GetAgentArray()
            for agent_id in agent_ids:
                if GLOBAL_CACHE.Agent.GetModelID(agent_id) == model_id:
                    return agent_id
            return 0

        @staticmethod
        def ChangeTarget(agent_id):
            if agent_id != 0:
                
                GLOBAL_CACHE.Player.ChangeTarget(agent_id)
                yield from Yield.wait(250)   
                
        @staticmethod
        def InteractAgent(agent_id:int):
            
            if agent_id != 0:
                GLOBAL_CACHE.Player.Interact(agent_id, False)
                yield from Yield.wait(100) 
            
        @staticmethod
        def TargetAgentByName(agent_name:str):
            agent_id =  yield from Yield.Agents.GetAgentIDByName(agent_name)
            if agent_id != 0:
                yield from Yield.Agents.ChangeTarget(agent_id)

        @staticmethod
        def TargetNearestNPC(distance:float = 4500.0):
            from .Agents import Agents
            nearest_npc = Agents.GetNearestNPC(distance)
            if nearest_npc != 0:
                yield from Yield.Agents.ChangeTarget(nearest_npc)

        @staticmethod
        def TargetNearestNPCXY(x,y,distance):
            from .Agents import Agents
            nearest_npc = Agents.GetNearestNPCXY(x,y, distance)
            if nearest_npc != 0:
                yield from Yield.Agents.ChangeTarget(nearest_npc)
                
        @staticmethod
        def TargetNearestGadgetXY(x,y,distance):
            from .Agents import Agents
            nearest_gadget = Agents.GetNearestGadgetXY(x,y, distance)
            if nearest_gadget != 0:
                yield from Yield.Agents.ChangeTarget(nearest_gadget)

        @staticmethod
        def TargetNearestEnemy(distance):
            from .Agents import Agents
            nearest_enemy = Agents.GetNearestEnemy(distance)
            if nearest_enemy != 0: 
                yield from Yield.Agents.ChangeTarget(nearest_enemy)
        
        @staticmethod
        def TargetNearestItem(distance):
            from .Agents import Agents
            nearest_item = Agents.GetNearestItem(distance)
            if nearest_item != 0:
                yield from Yield.Agents.ChangeTarget(nearest_item)
                
        @staticmethod
        def TargetNearestChest(distance):
            from .Agents import Agents
            nearest_chest = Agents.GetNearestChest(distance)
            if nearest_chest != 0:
                yield from Yield.Agents.ChangeTarget(nearest_chest)
                
        @staticmethod
        def InteractWithNearestChest():
            """Target and interact with chest and items."""
            from .Agents import Agents
            
            from ..Py4GWcorelib import LootConfig, Utils, Range
            nearest_chest = Agents.GetNearestChest(2500)
            chest_x, chest_y = GLOBAL_CACHE.Agent.GetXY(nearest_chest)


            yield from Yield.Movement.FollowPath([(chest_x, chest_y)])
            yield from Yield.wait(500)
        
            yield from Yield.Player.InteractAgent(nearest_chest)
            yield from Yield.wait(500)
            GLOBAL_CACHE.Player.SendDialog(2)
            yield from Yield.wait(1000)

            yield from Yield.Agents.TargetNearestItem(distance=300)
            filtered_loot = LootConfig().GetfilteredLootArray(Range.Area.value, multibox_loot= True)
            item = Utils.GetFirstFromArray(filtered_loot)
            yield from Yield.Agents.ChangeTarget(item)
            yield from Yield.Player.InteractTarget()
            yield from Yield.wait(1000)
            
        @staticmethod
        def InteractWithAgentByName(agent_name:str):
            
            yield from Yield.Agents.TargetAgentByName(agent_name)
            agent_x, agent_y = GLOBAL_CACHE.Agent.GetXY(GLOBAL_CACHE.Player.GetTargetID())

            yield from Yield.Movement.FollowPath([(agent_x, agent_y)])
            yield from Yield.wait(500)
            
            yield from Yield.Player.InteractTarget()
            yield from Yield.wait(1000)
            
        @staticmethod
        def InteractWithAgentXY(x:float, y:float, timeout_ms: int = 5000, tolerance: float = 200.0):
            
            from ..Py4GWcorelib import ConsoleLog, Utils
            yield from Yield.Agents.TargetNearestNPCXY(x, y, 100)
            target_id = GLOBAL_CACHE.Player.GetTargetID()
            if not target_id:
                ConsoleLog("InteractWithGadgetXY", "No target after targeting.")
                return False

            # 2) Interact once — the game will auto-move to the target
            yield from Yield.Player.InteractTarget()

            # 3) Wait until we’re inside the threshold (or timeout), re-issuing every 1000 ms
            elapsed = 0
            since_reissue = 0
            reissue_interval = 1000
            step = 100  # ms
            while elapsed < timeout_ms:
                px, py = GLOBAL_CACHE.Player.GetXY()
                tx, ty = GLOBAL_CACHE.Agent.GetXY(target_id)
                if Utils.Distance((px, py), (tx, ty)) <= tolerance:
                    break

                if since_reissue >= reissue_interval:
                    yield from Yield.Agents.TargetNearestGadgetXY(x, y, 100)
                    yield from Yield.Player.InteractTarget()
                    since_reissue = 0

                yield from Yield.wait(step)
                elapsed += step
                since_reissue += step

            if elapsed >= timeout_ms:
                ConsoleLog("InteractWithAgentXY", "TIMEOUT waiting to reach target range.")
                return False

            # 4) Small settle
            yield from Yield.wait(500)
            return True
        
        @staticmethod
        def InteractWithGadgetXY(x: float, y: float, tolerance: float = 200.0, timeout_ms: int = 15000):
            
            from ..Py4GWcorelib import ConsoleLog, Utils
            # 1) Aim at the nearest gadget around (x, y)
            yield from Yield.Agents.TargetNearestGadgetXY(x, y, 100)
            target_id = GLOBAL_CACHE.Player.GetTargetID()
            if not target_id:
                ConsoleLog("InteractWithGadgetXY", "No target after targeting.")
                return False

            # 2) Interact once — the game will auto-move to the target
            yield from Yield.Player.InteractTarget()

            # 3) Wait until we’re inside the threshold (or timeout), re-issuing every 1000 ms
            elapsed = 0
            since_reissue = 0
            step = 100  # ms
            while elapsed < timeout_ms:
                px, py = GLOBAL_CACHE.Player.GetXY()
                tx, ty = GLOBAL_CACHE.Agent.GetXY(target_id)
                if Utils.Distance((px, py), (tx, ty)) <= tolerance:
                    break

                if since_reissue >= 1000:
                    yield from Yield.Agents.TargetNearestGadgetXY(x, y, 100)
                    yield from Yield.Player.InteractTarget()
                    since_reissue = 0

                yield from Yield.wait(step)
                elapsed += step
                since_reissue += step

            if elapsed >= timeout_ms:
                ConsoleLog("InteractWithAgentXY", "TIMEOUT waiting to reach target range.")
                return False

            # 4) Small settle
            yield from Yield.wait(500)
            return True


            
    class Merchant:
        @staticmethod
        def SellItems(item_array:list[int], log=False):
            
            if len(item_array) == 0:
                ActionQueueManager().ResetQueue("MERCHANT")
                return
            
            for item_id in item_array:
                quantity = GLOBAL_CACHE.Item.Properties.GetQuantity(item_id)
                value = GLOBAL_CACHE.Item.Properties.GetValue(item_id)
                cost = quantity * value
                GLOBAL_CACHE.Trading.Merchant.SellItem(item_id, cost)
                    
            while not ActionQueueManager().IsEmpty("MERCHANT"):
                yield from Yield.wait(50)
            
            if log:
                ConsoleLog("SellItems", f"Sold {len(item_array)} items.", Console.MessageType.Info)

        @staticmethod
        def BuyIDKits(kits_to_buy:int, log=False):
            from ..Py4GWcorelib import ActionQueueManager, ConsoleLog, Console
            from ..ItemArray import ItemArray
            
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
                yield from Yield.wait(50)
                
            if log:
                ConsoleLog("BuyIDKits", f"Bought {kits_to_buy} ID Kits.", Console.MessageType.Info)

        @staticmethod
        def BuySalvageKits(kits_to_buy:int, log=False):
            from ..ItemArray import ItemArray
            from ..Py4GWcorelib import ActionQueueManager, ConsoleLog, Console
            
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
                yield from Yield.wait(50)
            
            if log:
                ConsoleLog("BuySalvageKits", f"Bought {kits_to_buy} Salvage Kits.", Console.MessageType.Info)

    class Items:
        @staticmethod
        def _wait_for_salvage_materials_window():
            from ..UIManager import UIManager
            yield from Yield.wait(150)
            salvage_materials_frame = UIManager.GetChildFrameID(140452905, [6, 100, 6])
            while not UIManager.FrameExists(salvage_materials_frame):
                yield from Yield.wait(50)
            yield from Yield.wait(50)
        
        @staticmethod
        def _wait_for_empty_queue(queue_name:str):
            from ..Py4GWcorelib import ActionQueueManager
            while not ActionQueueManager().IsEmpty(queue_name):
                yield from Yield.wait(50)
            
        @staticmethod
        def _salvage_item(item_id):
            from ..Inventory import Inventory
            

            salvage_kit = GLOBAL_CACHE.Inventory.GetFirstSalvageKit()
            if salvage_kit == 0:
                ConsoleLog("SalvageItems", "No salvage kits found.", Console.MessageType.Warning)
                return
            Inventory.SalvageItem(item_id, salvage_kit)
            
        @staticmethod
        def SalvageItems(item_array:list[int], log=False):
            from ..Py4GWcorelib import ActionQueueManager, ConsoleLog, Console
            from ..Inventory import Inventory
            
            if len(item_array) == 0:
                ActionQueueManager().ResetQueue("SALVAGE")
                return
            
            for item_id in item_array:
                _,rarity = GLOBAL_CACHE.Item.Rarity.GetRarity(item_id)
                is_purple = rarity == "Purple"
                is_gold = rarity == "Gold"
                ActionQueueManager().AddAction("SALVAGE", Yield.Items._salvage_item, item_id)
                yield from Yield.Items._wait_for_empty_queue("SALVAGE")
                
                if (is_purple or is_gold):
                    yield from Yield.Items._wait_for_salvage_materials_window()
                    ActionQueueManager().AddAction("SALVAGE", Inventory.AcceptSalvageMaterialsWindow)
                    yield from Yield.Items._wait_for_empty_queue("SALVAGE")
                    
                yield from Yield.wait(100)
                
            if log and len(item_array) > 0:
                ConsoleLog("SalvageItems", f"Salvaged {len(item_array)} items.", Console.MessageType.Info)
                
        @staticmethod
        def _identify_item(item_id):
            from ..Inventory import Inventory
            

            id_kit = GLOBAL_CACHE.Inventory.GetFirstIDKit()
            if id_kit == 0:
                ConsoleLog("IdentifyItems", "No ID kits found.", Console.MessageType.Warning)
                return
            Inventory.IdentifyItem(item_id, id_kit)
            
        @staticmethod
        def IdentifyItems(item_array:list[int], log=False):
            from ..Py4GWcorelib import ActionQueueManager, ConsoleLog, Console
            if len(item_array) == 0:
                ActionQueueManager().ResetQueue("IDENTIFY")
                return
            
            for item_id in item_array:
                ActionQueueManager().AddAction("IDENTIFY",Yield.Items._identify_item, item_id)
                
            while not ActionQueueManager().IsEmpty("IDENTIFY"):
                yield from Yield.wait(350)
                
            if log and len(item_array) > 0:
                ConsoleLog("IdentifyItems", f"Identified {len(item_array)} items.", Console.MessageType.Info)
                
        @staticmethod
        def DepositItems(item_array:list[int], log=False):
            from ..Py4GWcorelib import ActionQueueManager, ConsoleLog, Console
            
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
                yield from Yield.wait(350)
                
            if log and len(item_array) > 0:
                ConsoleLog("DepositItems", f"Deposited {len(item_array)} items.", Console.MessageType.Info)
                
        @staticmethod
        def DepositGold(gold_amount_to_leave_on_character: int, log=False):

            
            
            gold_amount_on_character = GLOBAL_CACHE.Inventory.GetGoldOnCharacter()
            gold_amount_on_storage = GLOBAL_CACHE.Inventory.GetGoldInStorage()
            
            max_allowed_gold = 1_000_000  # Max storage limit
            available_space = max_allowed_gold - gold_amount_on_storage  # How much can be deposited

            # Calculate how much gold we need to deposit
            gold_to_deposit = gold_amount_on_character - gold_amount_to_leave_on_character

            # Ensure we do not deposit more than available storage space
            gold_to_deposit = min(gold_to_deposit, available_space)

            # If storage is full or no gold needs to be deposited, exit
            if available_space <= 0:
                if log:
                    ConsoleLog("DepositGold", "No gold deposited, storage full.", Console.MessageType.Warning)
                return False
            
            if gold_to_deposit <= 0:
                if log:
                    ConsoleLog("DepositGold", "No gold deposited, not enough excess gold.", Console.MessageType.Warning)
                return False

            # Perform the deposit
            GLOBAL_CACHE.Inventory.DepositGold(gold_to_deposit)
            
            yield from Yield.wait(350)
            
            if log:
                ConsoleLog("DepositGold", f"Deposited {gold_to_deposit} gold.", Console.MessageType.Success)
            
            return True

        @staticmethod
        def LootItems(item_array:list[int], log=False, progress_callback: Optional[Callable[[float], None]] = None):
            from ..AgentArray import AgentArray
            from .Checks import Checks
            
            if len(item_array) == 0:
                return True
            
            total_items = len(item_array)
            while len (item_array) > 0:
                item_id = item_array.pop(0)
                if item_id == 0:
                    continue
                
                free_slots_in_inventory = GLOBAL_CACHE.Inventory.GetFreeSlotCount()
                if free_slots_in_inventory <= 0:
                    ConsoleLog("LootItems", "No free slots in inventory, stopping loot.", Console.MessageType.Warning)
                    item_array.clear()
                    ActionQueueManager().ResetAllQueues()
                    return False
                
                if not Checks.Map.MapValid():
                    item_array.clear()
                    ActionQueueManager().ResetAllQueues()
                    return False
                
                if not GLOBAL_CACHE.Agent.IsValid(item_id):
                    continue
                
                item_x, item_y = GLOBAL_CACHE.Agent.GetXY(item_id)
                item_reached = yield from Yield.Movement.FollowPath([(item_x, item_y)], timeout=5000)
                if not item_reached:
                    ConsoleLog("LootItems", "Failed to reach item, stopping loot.", Console.MessageType.Warning)
                    item_array.clear()
                    ActionQueueManager().ResetAllQueues()
                    return False
                
                if not Checks.Map.MapValid():
                    item_array.clear()
                    ActionQueueManager().ResetAllQueues()
                    return False
                if GLOBAL_CACHE.Agent.IsValid(item_id):
                    yield from Yield.Player.InteractAgent(item_id)
                    while True:
                        yield from Yield.wait(50)
                        live_items  = AgentArray.GetItemArray()
                        if item_id not in live_items :
                            break

                    
                if progress_callback and total_items > 0:
                    progress_callback(1 - len(item_array) / total_items)
            if log and len(item_array) > 0:
                ConsoleLog("LootItems", f"Looted {len(item_array)} items.", Console.MessageType.Info)
                
            return True

        @staticmethod
        def WithdrawItems(model_id:int, quantity:int) -> Generator[Any, Any, bool]:
            
            item_in_storage = GLOBAL_CACHE.Inventory.GetModelCountInStorage(model_id)
            if item_in_storage < quantity:
                return False

            items_withdrawn = GLOBAL_CACHE.Inventory.WithdrawItemFromStorageByModelID(model_id, quantity)
            yield from Yield.wait(500)
            if not items_withdrawn:
                return False

            return True
        
        @staticmethod
        def CraftItem(output_model_id: int, 
                       count: int,
                       trade_model_ids: list[int], 
                       quantity_list: list[int])-> Generator[Any, Any, bool]:
            
            # Align lists (no exceptions; clamp to shortest)
            k = min(len(trade_model_ids), len(quantity_list))
            if k == 0:
                return False
            trade_model_ids = trade_model_ids[:k]
            quantity_list   = quantity_list[:k]

            # Resolve each model -> first matching item in inventory
            trade_item_ids: list[int] = []
            for m in trade_model_ids:
                item_id = GLOBAL_CACHE.Inventory.GetFirstModelID(m)
                trade_item_ids.append(item_id or 0)

            # Bail if any required item is missing
            if any(i == 0 for i in trade_item_ids):
                return False

            # Find the crafter’s offered item that matches the desired output model
            target_item_id = 0
            for offered_item_id in GLOBAL_CACHE.Trading.Merchant.GetOfferedItems():
                if GLOBAL_CACHE.Item.GetModelID(offered_item_id) == output_model_id:
                    target_item_id = offered_item_id
                    break
            if target_item_id == 0:
                return False

            # Craft, then give a short yield
            GLOBAL_CACHE.Trading.Crafter.CraftItem(target_item_id, count, trade_item_ids, quantity_list)
            yield from Yield.wait(500)
            return True
        
        @staticmethod
        def EquipItem(model_id: int) -> Generator[Any, Any, bool]:
            
            item_id = GLOBAL_CACHE.Inventory.GetFirstModelID(model_id)
            if item_id:
                GLOBAL_CACHE.Inventory.EquipItem(item_id, GLOBAL_CACHE.Player.GetAgentID())
                yield from Yield.wait(500)
            else:
                return False
            return True
        
        @staticmethod
        def SpawnBonusItems():
            
            from ..Py4GWcorelib import ModelID
            summoning_stone_in_bags = GLOBAL_CACHE.Inventory.GetModelCount(ModelID.Igneous_Summoning_Stone.value)
            if summoning_stone_in_bags < 1:
                GLOBAL_CACHE.Player.SendChatCommand("bonus")
                yield from Yield.wait(250)

#endregion