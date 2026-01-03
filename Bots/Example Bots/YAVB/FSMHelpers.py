from Py4GWCoreLib.Builds import ShadowFormAssassinVaettir, ShadowFormMesmerVaettir
from .LogConsole import LogConsole
from Py4GWCoreLib import GLOBAL_CACHE, Agent
from Py4GWCoreLib import Routines
from Py4GWCoreLib.enums import ModelID, TitleID, SharedCommandType, Range
from Py4GWCoreLib import ItemArray
from Py4GWCoreLib import Utils
from Py4GWCoreLib import Map
from typing import List, Tuple
from Py4GWCoreLib import LootConfig
from Py4GWCoreLib import Profession

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .YAVBMain import YAVB

path_points_to_leave_outpost: List[Tuple[float, float]] = [(-24380, 15074), (-26375, 16180)]
path_points_to_traverse_bjora_marches: List[Tuple[float, float]] = [
    (17810, -17649),(17516, -17270),(17166, -16813),(16862, -16324),(16472, -15934),
    (15929, -15731),(15387, -15521),(14849, -15312),(14311, -15101),(13776, -14882),
    (13249, -14642),(12729, -14386),(12235, -14086),(11748, -13776),(11274, -13450),
    (10839, -13065),(10572, -12590),(10412, -12036),(10238, -11485),(10125, -10918),
    (10029, -10348),(9909, -9778)  ,(9599, -9327)  ,(9121, -9009)  ,(8674, -8645)  ,
    (8215, -8289)  ,(7755, -7945)  ,(7339, -7542)  ,(6962, -7103)  ,(6587, -6666)  ,
    (6210, -6226)  ,(5834, -5788)  ,(5457, -5349)  ,(5081, -4911)  ,(4703, -4470)  ,
    (4379, -3990)  ,(4063, -3507)  ,(3773, -3031)  ,(3452, -2540)  ,(3117, -2070)  ,
    (2678, -1703)  ,(2115, -1593)  ,(1541, -1614)  ,(960, -1563)   ,(388, -1491)   ,
    (-187, -1419)  ,(-770, -1426)  ,(-1343, -1440) ,(-1922, -1455) ,(-2496, -1472) ,
    (-3073, -1535) ,(-3650, -1607) ,(-4214, -1712) ,(-4784, -1759) ,(-5278, -1492) ,
    (-5754, -1164) ,(-6200, -796)  ,(-6632, -419)  ,(-7192, -300)  ,(-7770, -306)  ,
    (-8352, -286)  ,(-8932, -258)  ,(-9504, -226)  ,(-10086, -201) ,(-10665, -215) ,
    (-11247, -242) ,(-11826, -262) ,(-12400, -247) ,(-12979, -216) ,(-13529, -53)  ,
    (-13944, 341)  ,(-14358, 743)  ,(-14727, 1181) ,(-15109, 1620) ,(-15539, 2010) ,
    (-15963, 2380) ,(-18048, 4223 ), (-19196, 4986),(-20000, 5595) ,(-20300, 5600)
    ]
path_points_to_npc:List[Tuple[float, float]]  = [(13367, -20771)]
path_points_to_farming_route1: List[Tuple[float, float]] = [
    (11375, -22761), (10925, -23466), (10917, -24311), (10280, -24620), (9640, -23175),
    (7815, -23200), (7765, -22940), (8213, -22829), (8740, -22475), (8880, -21384),
    (8684, -20833), (8982, -20576),
]

path_points_to_farming_route2: List[Tuple[float, float]] = [
    (10196, -20124), (10123, -19529),(10049, -18933), (9976, -18338), (11316, -18056),
    (10392, -17512), (10114, -16948),(10729, -16273), (10505, -14750),(10815, -14790),
    (11090, -15345), (11670, -15457),(12604, -15320), (12450, -14800),(12725, -14850),
    (12476, -16157),
]

path_points_to_killing_spot: List[Tuple[float, float]] = [
    (13070, -16911), (12938, -17081), (12790, -17201), (12747, -17220), (12703, -17239),
    (12684, -17184), # (12429.97, -17150.89) testing new ball end location
]

path_points_to_exit_jaga_moraine: List[Tuple[float, float]] = [(12289, -17700) ,(13970, -18920), (15400, -20400),(15850,-20550)]
path_points_to_return_to_jaga_moraine: List[Tuple[float, float]] = [(-20300, 5600 )]



class _FSM_Helpers:
        def __init__(self, parent: 'YAVB'):
            self._parent = parent
            self.loot_singleton = LootConfig()
            
        def _init_build(self):
            profession = self._parent.primary_profession
            match profession:
                case Profession.Assassin.value:
                    self._parent.build = ShadowFormAssassinVaettir()
                case Profession.Mesmer.value:
                    self._parent.build = ShadowFormMesmerVaettir()  # Placeholder for Mesmer build
            
        def _stop_execution(self):
            if self._parent.script_running:
                self._parent.script_running = False
                self._parent.script_paused = False
                self._parent.in_killing_routine = False
                self._parent.finished_routine = False
                if self._parent.build is not None:
                    build = self._parent.build  # now Pylance sees it as non-Optional
                    build.SetKillingRoutine(self._parent.in_killing_routine)
                    build.SetRoutineFinished(self._parent.finished_routine)
                self._parent.LogMessage("Script stopped", "", LogConsole.LogSeverity.INFO)
                self._parent.state = "Idle"
                self._parent.FSM.stop()
                
                build = self._parent.build or ShadowFormAssassinVaettir() if self._parent.primary_profession == Profession.Assassin.value else ShadowFormMesmerVaettir()
                GLOBAL_CACHE.Coroutines.clear()  # Clear all coroutines

            yield from Routines.Yield.wait(100)
            
        def _reset_execution(self):
            if self._parent.script_running:
                self._parent.in_killing_routine = False
                self._parent.finished_routine = False
                if self._parent.build is not None:
                    build = self._parent.build  # now Pylance sees it as non-Optional
                    build.SetKillingRoutine(self._parent.in_killing_routine)
                    build.SetRoutineFinished(self._parent.finished_routine)
                self._parent.LogMessage("Script reset", "", LogConsole.LogSeverity.INFO)
                self._parent.state = "Idle"
                self._parent.FSM.restart()
                
                build = self._parent.build or ShadowFormAssassinVaettir()
                GLOBAL_CACHE.Coroutines.clear()  # Clear all coroutines

                    
                self._parent.farming_stats.EndCurrentRun(failed= True, deaths= 1)
                
            yield from Routines.Yield.wait(100)
            
        def _send_message(self,message:SharedCommandType, params: tuple = ()):
            account_email = GLOBAL_CACHE.Player.GetAccountEmail()
            GLOBAL_CACHE.ShMem.SendMessage(account_email,account_email, message, params)
            
        def _get_materials_to_sell(self):
            bags_to_check = GLOBAL_CACHE.ItemArray.CreateBagList(1, 2, 3, 4)
            bag_item_array = GLOBAL_CACHE.ItemArray.GetItemArray(bags_to_check)
            materials_to_sell = ItemArray.Filter.ByCondition(bag_item_array, lambda item_id: GLOBAL_CACHE.Item.Type.IsMaterial(item_id))
            return materials_to_sell
        
        def _get_number_of_id_kits_to_buy(self):
            count_of_id_kits = GLOBAL_CACHE.Inventory.GetModelCount(ModelID.Superior_Identification_Kit.value)
            if count_of_id_kits < self._parent.identification_kits_restock:
                return self._parent.identification_kits_restock - count_of_id_kits
            return 0
        
        def _get_number_of_salvage_kits_to_buy(self):
            count_of_salvage_kits = GLOBAL_CACHE.Inventory.GetModelCount(ModelID.Salvage_Kit.value)
            if count_of_salvage_kits < self._parent.salvage_kits_restock:
                return self._parent.salvage_kits_restock - count_of_salvage_kits
            return 0
        
        def _get_unidentified_items(self):
            bags_to_check = GLOBAL_CACHE.ItemArray.CreateBagList(1, 2, 3, 4)
            bag_item_array = GLOBAL_CACHE.ItemArray.GetItemArray(bags_to_check)
            unidentified_items = ItemArray.Filter.ByCondition(bag_item_array, lambda item_id: not (GLOBAL_CACHE.Item.Usage.IsIdentified(item_id)))
            white_items = ItemArray.Filter.ByCondition(bag_item_array, lambda item_id: GLOBAL_CACHE.Item.Rarity.IsWhite(item_id) and not GLOBAL_CACHE.Item.Usage.IsIdentified(item_id))
            unidentified_items = [item for item in unidentified_items if item not in white_items]  # Remove white items from unidentified items
            
            return unidentified_items if len(unidentified_items) > 0 else []
        
        def _get_items_to_salvage(self):
            bags_to_check = GLOBAL_CACHE.ItemArray.CreateBagList(1, 2, 3, 4)
            bag_item_array = GLOBAL_CACHE.ItemArray.GetItemArray(bags_to_check)
            white_items_to_salvage = ItemArray.Filter.ByCondition(bag_item_array, lambda item_id: GLOBAL_CACHE.Item.Usage.IsSalvageable(item_id) and GLOBAL_CACHE.Item.Rarity.IsWhite(item_id))
            items_to_salvage = ItemArray.Filter.ByCondition(bag_item_array, lambda item_id: GLOBAL_CACHE.Item.Usage.IsSalvageable(item_id) and GLOBAL_CACHE.Item.Usage.IsIdentified(item_id))
            items_to_salvage.extend(white_items_to_salvage)
            #remove duplicates
            items_to_salvage = list(set(items_to_salvage))
            return items_to_salvage
            
        def _inventory_handling_checks(self):
            free_slots_in_inventory = GLOBAL_CACHE.Inventory.GetFreeSlotCount()
            if free_slots_in_inventory < self._parent.keep_empty_inventory_slots:
                return True
            count_of_id_kits = GLOBAL_CACHE.Inventory.GetModelCount(ModelID.Superior_Identification_Kit.value)
            if count_of_id_kits < self._parent.identification_kits_restock:
                return True
            count_of_salvage_kits = GLOBAL_CACHE.Inventory.GetModelCount(ModelID.Salvage_Kit.value) #2992 model for salvage kit
            if count_of_salvage_kits < self._parent.salvage_kits_restock:
                return True
            
            
            materials_to_sell = self._get_materials_to_sell()
            if len(materials_to_sell) > 0:
                return True
            
            unidentified_items = self._get_unidentified_items()
            if len(unidentified_items) > 0:
                return True
            
            items_to_salvage = self._get_items_to_salvage()
            if len(items_to_salvage) > 0:
                return True
            
            return False
        
        def _need_to_return_for_inventory_handling(self):
            free_slots_in_inventory = GLOBAL_CACHE.Inventory.GetFreeSlotCount()
            if free_slots_in_inventory < self._parent.keep_empty_inventory_slots:
                return True
            
            count_of_id_kits = GLOBAL_CACHE.Inventory.GetModelCount(ModelID.Superior_Identification_Kit.value)
            if count_of_id_kits == 0:
                return True
            
            count_of_salvage_kits = GLOBAL_CACHE.Inventory.GetModelCount(ModelID.Salvage_Kit.value)
            if count_of_salvage_kits == 0:
                return True
        
        def _movement_eval_exit_on_map_loading(self):
            if Map.IsMapLoading():
                return True
            
            if not self._parent.script_running:
                return True
            
            return False
        
        def _movement_eval_exit_on_map_loading_or_death(self):
            if Map.IsMapLoading():
                return True
            
            if not self._parent.script_running:
                return True
            
            if Agent.IsDead(GLOBAL_CACHE.Player.GetAgentID()):
                return True
            
            return False
            
            
        def DeactivateInventoryHandler(self):
            self._parent.SetCurrentStep("Deactivate Inventory+ AutoHandler", 0.02)
            self._parent.AdvanceProgress(0.5)
            self._parent.LogMessage("Inventory+ AutoHandler", "Forcing Deactivation", LogConsole.LogSeverity.INFO)
            self._parent.inventory_handler.module_active = False
   
        def DeactivateHeroAI(self):
            from Py4GW_widget_manager import get_widget_handler
            self._parent.SetCurrentStep("Deactivate Hero AI", 0.02)
            handler = get_widget_handler()
            handler.disable_widget("HeroAI")
            self._parent.LogMessage("HeroAI", "Disabled.", LogConsole.LogSeverity.INFO)
            
        def TravelToLongeyesLedge(self):
            self._parent.SetCurrentStep("Travel to Longeyes Ledge",0.02)
            current_map = Map.GetMapID()
            if current_map != self._parent.LONGEYES_LEDGE:
                self._parent.AdvanceProgress(0.5)
                self._parent.LogMessage("Map Check", "Traveling to Longeyes Ledge", LogConsole.LogSeverity.INFO)
                if not (yield from Routines.Yield.Map.TravelToOutpost(self._parent.LONGEYES_LEDGE, log=self._parent.detailed_logging)):
                    self._parent.LogMessage("Failed to travel to Longeyes Ledge", "TIMEOUT", LogConsole.LogSeverity.ERROR)
                    yield from self._stop_execution()
            
        def LoadSkillBar(self):
            if not self._parent.build:
                self._init_build()
            build = self._parent.build or ShadowFormAssassinVaettir()
            self._parent.SetCurrentStep("Load Skill Bar", 0.02)
            self._parent.LogMessage("Loading Skill Bar", f"{build.build_name}.", LogConsole.LogSeverity.INFO)
            yield from build.LoadSkillBar()
            self._parent.AdvanceProgress(0.33)
            if not (yield from build.ValidateSkills()):
                self._parent.AdvanceProgress(0.66)
                self._parent.LogMessage("Skillbar validation", "FAILED, Check your skillbar configuration.", LogConsole.LogSeverity.ERROR)
                yield from self._stop_execution()
            else:
                self._parent.AdvanceProgress(0.66)
                self._parent.LogDetailedMessage("Skillbar validation", "PASSED.", LogConsole.LogSeverity.SUCCESS)
                
        def InventoryHandling(self):
            #Inventory Handling
            self._parent.LogMessage("Inventory Handling", "Starting Inventory Handling", LogConsole.LogSeverity.INFO)
            self._parent.SetCurrentStep("Inventory Handling", 0.12)
            progress = 0.0
            yield from self._parent.inventory_handler.IDSalvageDepositItems()
            progress += 0.8
            self._parent.AdvanceProgress(progress)
            for cycle in range(2):
                if self._inventory_handling_checks():
                    progress += 0.4
                    self._parent.AdvanceProgress(progress)
                    self._parent.LogMessage("Inventory Handling", "checks failed, starting Inventory handling", LogConsole.LogSeverity.INFO)
                    interact_result = yield from Routines.Yield.Agents.InteractWithAgentXY(-23110, 14942)
                    if not interact_result:
                        self._parent.LogMessage("Inventory Handling", "Failed to interact with Merchant, stopping script.", LogConsole.LogSeverity.ERROR)
                        yield from self._stop_execution()
                        return
                    
                    if not self._parent.script_running:
                        yield from Routines.Yield.wait(100)
                
                    progress += 0.4
                    self._parent.AdvanceProgress(progress)
                    if len(self._get_materials_to_sell()) > 0:
                        self._parent.LogMessage("Inventory Handling", f"Selling Materials to make Space", LogConsole.LogSeverity.INFO)
                        yield from Routines.Yield.Merchant.SellItems(self._get_materials_to_sell(), log=self._parent.detailed_logging)

                    if not self._parent.script_running:
                        yield from Routines.Yield.wait(100)
                        
                    progress += 0.8
                    self._parent.AdvanceProgress(progress)
                    if self._get_number_of_id_kits_to_buy() > 0:
                        self._parent.LogMessage("Inventory Handling", "Restocking ID Kits", LogConsole.LogSeverity.INFO)
                        yield from Routines.Yield.Merchant.BuyIDKits(self._get_number_of_id_kits_to_buy(),log=self._parent.detailed_logging)

                    if not self._parent.script_running:
                        yield from Routines.Yield.wait(100)
                        
                    progress += 0.8
                    self._parent.AdvanceProgress(progress)
                    if self._get_number_of_salvage_kits_to_buy() > 0:
                        self._parent.LogMessage("Inventory Handling", "Restocking Salvage Kits", LogConsole.LogSeverity.INFO)
                        yield from Routines.Yield.Merchant.BuySalvageKits(self._get_number_of_salvage_kits_to_buy(),log=self._parent.detailed_logging)

                    if not self._parent.script_running:
                        yield from Routines.Yield.wait(100)
                        
                    progress += 0.8
                    self._parent.AdvanceProgress(progress)
                    if len(self._get_unidentified_items()) > 0:
                        self._parent.LogMessage("Inventory Handling", "Identifying Items", LogConsole.LogSeverity.INFO)
                        yield from Routines.Yield.Items.IdentifyItems(self._get_unidentified_items(), log=self._parent.detailed_logging)

                    if not self._parent.script_running:
                        yield from Routines.Yield.wait(100)
                        
                    progress += 0.8
                    self._parent.AdvanceProgress(progress)
                    if len(self._get_items_to_salvage()) > 0:
                        self._parent.LogMessage("Inventory Handling", "Salvaging Items", LogConsole.LogSeverity.INFO)
                        yield from Routines.Yield.Items.SalvageItems(self._get_items_to_salvage(), log=self._parent.detailed_logging)

                    if not self._parent.script_running:
                        yield from Routines.Yield.wait(100)
                        
                else:
                    self._parent.LogDetailedMessage("Inventory Handling", "No Inventory Handling needed, skipping.", LogConsole.LogSeverity.SUCCESS)
                    break
                    
            
        def WitdrawBirthdayCupcake(self):
            self._parent.SetCurrentStep("Withdraw Cupcake", 0.02)
            if not self._parent.use_cupcakes:
                return
            
            cupcackes_in_inventory = GLOBAL_CACHE.Inventory.GetModelCount(ModelID.Birthday_Cupcake.value)
            if cupcackes_in_inventory > 0:
                return  # Cupcake already in inventory, no need to withdraw
            
            if GLOBAL_CACHE.Inventory.GetModelCountInStorage(ModelID.Birthday_Cupcake.value) > 0:
                self._parent.LogMessage("Cupcake Usage", "Withdraw (1) Cupcake from Inventory", LogConsole.LogSeverity.INFO)
                items_witdrawn = GLOBAL_CACHE.Inventory.WithdrawItemFromStorageByModelID(ModelID.Birthday_Cupcake.value, 1)
                self._parent.AdvanceProgress(0.5)
                if not items_witdrawn:
                    self._parent.LogMessage("Cupcake Usage", "Failed to withdraw Cupcake from Storage", LogConsole.LogSeverity.ERROR)
                yield from Routines.Yield.wait(150)

                
        def WitdrawPumpkinCookie(self):
            self._parent.SetCurrentStep("Withdraw Pumpkin Cookie", 0.02)
            if not self._parent.use_pumpkin_cookies:
                return
            
            cookies_in_inventory = GLOBAL_CACHE.Inventory.GetModelCount(ModelID.Pumpkin_Cookie.value)
            cookies_to_restock = self._parent.pumpkin_cookies_restock
                
            total_needed_cookies = cookies_to_restock - cookies_in_inventory
            if total_needed_cookies < 0:    
                total_needed_cookies = 0
                
            if total_needed_cookies > 0:
                self._parent.LogDetailedMessage("Pumpkin Cookie", f"Withdrawing {total_needed_cookies} Cookies from Storage", LogConsole.LogSeverity.INFO)
                items_witdrawn = GLOBAL_CACHE.Inventory.WithdrawItemFromStorageByModelID(ModelID.Pumpkin_Cookie.value, total_needed_cookies)
                self._parent.AdvanceProgress(0.5)
                if not items_witdrawn:
                    self._parent.LogDetailedMessage("Pumpkin Cookie", "Failed to withdraw Pumpkin Cookies from Storage", LogConsole.LogSeverity.ERROR)
                yield from Routines.Yield.wait(150)
            else:
                self._parent.LogDetailedMessage("Pumpkin Cookie", "No need to withdraw Pumpkin Cookies, already have enough.", LogConsole.LogSeverity.SUCCESS)


        def SetHardMode(self):
            self._parent.SetCurrentStep("Set Hard Mode", 0.02)
            if GLOBAL_CACHE.Party.IsHardModeUnlocked():
                if not GLOBAL_CACHE.Party.IsHardMode():
                    self._parent.LogMessage("Hard Mode", "Switching to Hard Mode.", LogConsole.LogSeverity.INFO)
                    yield from Routines.Yield.Map.SetHardMode(log=self._parent.detailed_logging)
                    self._parent.AdvanceProgress(0.5)

   
        def LeaveOutpost(self):
            self._parent.SetCurrentStep("Leave Outpost", 0.04)
            self._parent.LogMessage("Leaving Outpost", "Longeyes Ledge", LogConsole.LogSeverity.INFO)
            success_movement = yield from Routines.Yield.Movement.FollowPath(path_points= path_points_to_leave_outpost, 
                                                                             custom_exit_condition=lambda: self._movement_eval_exit_on_map_loading(),
                                                                             log=False,
                                                                             progress_callback=self._parent.AdvanceProgress)
            if not success_movement:
                if not self._parent.script_running:
                    return
                if not Map.IsMapLoading():
                    self._parent.LogMessage("Failed to leave outpost", "TIMEOUT", LogConsole.LogSeverity.ERROR)
                    yield from self._stop_execution()
                
        def WaitforBjoraMarchesMapLoad(self):
            self._parent.SetCurrentStep("Wait for Bjora Marches Map Load", 0.02)
            self._parent.LogMessage("Waiting for Map Loading", "Bjora Marches", LogConsole.LogSeverity.INFO)
            wait_of_map_load = yield from Routines.Yield.Map.WaitforMapLoad(self._parent.BJORA_MARCHES)
            if not wait_of_map_load:
                self._parent.LogMessage("Map Load", "Timeout Loading Bjora Marches, stopping script.", LogConsole.LogSeverity.ERROR)
                yield from self._stop_execution()
            yield from Routines.Yield.wait(1000)  # Wait a bit to ensure the mobs start moving
                
        def AddBjoraMarchesStuckCoroutine(self):
            self._parent.finished_routine = False
            self._parent.in_killing_routine = False
            self._parent.running_to_jaga = True
            self._parent.run_to_jaga_stats.StartNewRun()
            self._parent.SetCurrentStep("Add Bjora Marches Coroutine", 0.02)
            GLOBAL_CACHE.Coroutines.append(self._parent.HandleStuckBjoraMarches())
            self._parent.LogDetailedMessage("Stuck Coroutine", "Added to Bjora Marches Stuck Coroutines.", LogConsole.LogSeverity.INFO)
        
        def SetNornTitle(self):
            self._parent.SetCurrentStep("Set Norn Title", 0.02)
            self._parent.LogMessage("Title", "Setting PVE Norn Title", LogConsole.LogSeverity.INFO)
            yield from Routines.Yield.Player.SetTitle(TitleID.Norn.value, log=self._parent.detailed_logging)  
            
        def UseCupcake(self):
            self._parent.SetCurrentStep("Use Cupcake", 0.02)
            if self._parent.use_cupcakes:
                self._parent.LogMessage("Cupcake Usage", "Using Cupcake for Bjora Marches Traversal", LogConsole.LogSeverity.INFO)
                self._send_message(SharedCommandType.PCon,(ModelID.Birthday_Cupcake.value, GLOBAL_CACHE.Skill.GetID("Birthday_Cupcake_skill"), 0, 0))
                
        def TraverseBjoraMarches(self):
            self._parent.SetCurrentStep("Traverse Bjora Marches", 0.62)
            self._parent.LogMessage("Traverse", "Traversing Bjora Marches", LogConsole.LogSeverity.INFO)
            success_movement = yield from Routines.Yield.Movement.FollowPath(
                        path_points= path_points_to_traverse_bjora_marches, 
                        custom_exit_condition=lambda: self._movement_eval_exit_on_map_loading_or_death(),
                        log=False,
                        timeout=300000, # 5 minutes timeout
                        progress_callback=self._parent.AdvanceProgress)   
            if not success_movement:
                yield from Routines.Yield.wait(1000)
                if not self._parent.script_running:
                    return
                
                if Map.IsMapLoading():
                    return
 
                if Agent.IsDead(GLOBAL_CACHE.Player.GetAgentID()):
                    self._parent.run_to_jaga_stats.EndCurrentRun(failed=True, deaths=1)
                    self._parent.running_to_jaga = False
                    self._parent.LogMessage("Death", "Player is dead, restarting.", LogConsole.LogSeverity.WARNING)
                    yield from Routines.Yield.wait(1000)
                    yield from self._reset_execution()
            
                if Map.GetMapID() != self._parent.JAGA_MORAINE:
                    self._parent.running_to_jaga = False
                    self._parent.run_to_jaga_stats.EndCurrentRun(failed=True, stuck_timeouts=1)
                    self._parent.LogMessage("Failed to traverse Bjora Marches", "TIMEOUT", LogConsole.LogSeverity.ERROR)
                    yield from Routines.Yield.wait(1000)
                    yield from self._reset_execution()
                
        def WaitforJagaMoraineMapLoad(self):
            self._parent.LogMessage("Waiting for Map Loading", "Jaga Moraine", LogConsole.LogSeverity.INFO)
            wait_of_map_load = yield from Routines.Yield.Map.WaitforMapLoad(self._parent.JAGA_MORAINE, log=self._parent.detailed_logging)
            if not wait_of_map_load:
                self._parent.LogMessage("Map Load", "Timeout Loading Jaga Moraine, stopping script.", LogConsole.LogSeverity.ERROR)
                self._parent.run_to_jaga_stats.EndCurrentRun(failed=True, stuck_timeouts=1)
                self._parent.running_to_jaga = False
                yield from self._stop_execution()
                
            
            self._parent.finished_routine = False
            self._parent.in_killing_routine = False
            self._parent.in_waiting_routine = False
            if self._parent.build is not None:
                    build = self._parent.build  
                    build.SetKillingRoutine(self._parent.in_killing_routine)
                    build.SetRoutineFinished(self._parent.finished_routine)
            self._parent.run_to_jaga_stats.EndCurrentRun()
            
        def RemoveBjoraMarchesStuckCoroutine(self):
            self._parent.running_to_jaga = False
            self._parent.SetCurrentStep("Remove Bjora Marches Stuck Coroutine", 0.02)
            if self._parent.HandleStuckBjoraMarches() in GLOBAL_CACHE.Coroutines:
                GLOBAL_CACHE.Coroutines.remove(self._parent.HandleStuckBjoraMarches())
            self._parent.LogDetailedMessage("Stuck Coroutine", "Removed from Bjora Marches Stucvk Coroutines.", LogConsole.LogSeverity.INFO)
                    
        def AddSkillCastingCoroutine(self):
            self._parent.farming_stats.StartNewRun()
            GLOBAL_CACHE.Coroutines.append(self._parent.HandleStuckJagaMoraine())
            build = self._parent.build or ShadowFormAssassinVaettir()
            GLOBAL_CACHE.Coroutines.append(build.ProcessSkillCasting())
            self._parent.LogDetailedMessage("Skill Casting Coroutine", "Added to Coroutines.", LogConsole.LogSeverity.INFO)
            
        def TakeBounty(self):
            self._parent.ResetCurrentProgress()
            self._parent.SetCurrentStep("Take Bounty", 0.05)
            self._parent.LogMessage("Taking Bounty", "Jaga Moraine", LogConsole.LogSeverity.INFO)
            self._parent.AdvanceProgress(0.33)
            timeout = yield from Routines.Yield.Movement.FollowPath(path_points_to_npc, 
                                                          custom_exit_condition=lambda: self._movement_eval_exit_on_map_loading_or_death(),
                                                          timeout=20000
                                                          )
            if not timeout:
                if not self._parent.script_running:
                    return
                
                self._parent.LogMessage("Failed to take Bounty", "TIMEOUT", LogConsole.LogSeverity.ERROR)
                yield from self._reset_execution()
                return
            
            timeout = yield from Routines.Yield.Agents.InteractWithAgentXY(13367, -20771)
            if not timeout:
                if not self._parent.script_running:
                    return
                
                self._parent.LogMessage("Failed to take Bounty", "TIMEOUT", LogConsole.LogSeverity.ERROR)
                yield from self._reset_execution()
                return
            
            self._parent.AdvanceProgress(0.33)
            yield from Routines.Yield.Player.SendDialog("0x84")
            
        def FarmingRoute1(self):
            self._parent.SetCurrentStep("Farming Route 1", 0.25)
            self._parent.LogMessage("Farming Route", "Starting Farming Route 1", LogConsole.LogSeverity.INFO)
            movement_success = yield from Routines.Yield.Movement.FollowPath(path_points_to_farming_route1,
                                            custom_exit_condition=lambda: self._movement_eval_exit_on_map_loading_or_death(),
                                            timeout=150000,  # 2.5 minutes timeout
                                            progress_callback=self._parent.AdvanceProgress)
            if not movement_success:
                if not self._parent.script_running:
                    return
                
                if Agent.IsDead(GLOBAL_CACHE.Player.GetAgentID()):
                    self._parent.LogMessage("Death", "Player is dead, restarting.", LogConsole.LogSeverity.WARNING)
                    yield from self._reset_execution()
                
        def WaitforLeftAggroBall(self):
            from Py4GWCoreLib.Agent import Agent
            self._parent.LogMessage("Waiting for Left Aggro Ball", "Waiting for enemies to ball up.", LogConsole.LogSeverity.INFO)
            self._parent.SetCurrentStep("Wait for Left Aggro Ball", 0.05)
            self._parent.in_waiting_routine = True

            player_id = GLOBAL_CACHE.Player.GetAgentID()
            start_time = 0

            while start_time < 150:  # 150 * 100ms = 15 seconds
                # Wait 100 ms
                yield from Routines.Yield.wait(100)
                start_time += 1
                self._parent.AdvanceProgress(start_time / 150.0)

                # Get current player position
                player_pos = GLOBAL_CACHE.Player.GetXY()
                px, py = player_pos[0], player_pos[1]

                # Get nearby enemies
                enemies_ids = Routines.Agents.GetFilteredEnemyArray(px, py, Range.Earshot.value)

                # Check if ALL enemies are within Adjacent range
                all_in_adjacent = True
                for enemy_id in enemies_ids:
                    enemy = Agent.GetAgentByID(enemy_id)
                    if enemy is None:
                        continue
                    ex, ey = enemy.pos.x, enemy.pos.y
                    dx, dy = ex - px, ey - py
                    dist_sq = dx * dx + dy * dy
                    if dist_sq > (Range.Adjacent.value ** 2):
                        all_in_adjacent = False
                        break

                if all_in_adjacent:
                    break  # exit early if all enemies are balled up

            self._parent.in_waiting_routine = False

            # Death check
            if Agent.IsDead(player_id):
                self._parent.LogMessage("Death", "Player is dead, restarting.", LogConsole.LogSeverity.WARNING)
                yield from self._reset_execution()

            # Resume build
            build = self._parent.build or ShadowFormAssassinVaettir()
            yield from build.CastHeartOfShadow()
                
        def FarmingRoute2(self):
            self._parent.SetCurrentStep("Farming Route 2", 0.25)
            self._parent.LogMessage("Farming Route", "Starting Farming Route 2", LogConsole.LogSeverity.INFO)
            movement_success = yield from Routines.Yield.Movement.FollowPath(
                        path_points_to_farming_route2,
                        custom_exit_condition=lambda: self._movement_eval_exit_on_map_loading_or_death(),
                        timeout=150000,  # 2.5 minutes timeout
                        progress_callback=self._parent.AdvanceProgress)
            if not movement_success:
                if not self._parent.script_running:
                    return
                
                if Agent.IsDead(GLOBAL_CACHE.Player.GetAgentID()):
                    self._parent.LogMessage("Death", "Player is dead, restarting.", LogConsole.LogSeverity.WARNING)
                    yield from self._reset_execution()
                    
        def WaitforRightAggroBall(self):
            from Py4GWCoreLib.Agent import Agent
            self._parent.LogMessage("Waiting for Right Aggro Ball", "Waiting for enemies to ball up.", LogConsole.LogSeverity.INFO)
            self._parent.SetCurrentStep("Wait for Right Aggro Ball", 0.05)
            self._parent.in_waiting_routine = True

            player_id = GLOBAL_CACHE.Player.GetAgentID()
            elapsed = 0

            while elapsed < 150:  # 150 * 100ms = 15s max
                yield from Routines.Yield.wait(100)
                elapsed += 1
                self._parent.AdvanceProgress(elapsed / 150.0)

                # Get player position
                px, py = GLOBAL_CACHE.Player.GetXY()

                # Get enemies within earshot
                enemies_ids = Routines.Agents.GetFilteredEnemyArray(px, py, Range.Earshot.value)

                # Check if all enemies are within Adjacent range
                all_in_adjacent = True
                for enemy_id in enemies_ids:
                    enemy = Agent.GetAgentByID(enemy_id)
                    if enemy is None:
                        continue
                    dx, dy = enemy.pos.x - px, enemy.pos.y - py
                    if dx * dx + dy * dy > (Range.Adjacent.value ** 2):
                        all_in_adjacent = False
                        break

                if all_in_adjacent:
                    break  # Exit early if enemies are balled up

            self._parent.in_waiting_routine = False

            # Death check
            if Agent.IsDead(player_id):
                self._parent.LogMessage("Death", "Player is dead, restarting.", LogConsole.LogSeverity.WARNING)
                yield from self._reset_execution()

            # Resume build
            build = self._parent.build or ShadowFormAssassinVaettir()
            yield from build.CastHeartOfShadow()
                
        def FarmingRoutetoKillSpot(self):
            self._parent.SetCurrentStep("Farming Route to Kill Spot", 0.10)
            self._parent.LogMessage("Farming Route", "Starting Farming Route to Kill Spot", LogConsole.LogSeverity.INFO)
            movement_success = yield from Routines.Yield.Movement.FollowPath(
                        path_points_to_killing_spot,
                        tolerance=25,
                        custom_exit_condition=lambda: self._movement_eval_exit_on_map_loading_or_death(),
                        timeout=60000,  # 1 minute timeout
                        progress_callback=self._parent.AdvanceProgress)
            if not movement_success:
                if not self._parent.script_running:
                    return

                if Agent.IsDead(GLOBAL_CACHE.Player.GetAgentID()):
                    self._parent.LogMessage("Death", "Player is dead, restarting.", LogConsole.LogSeverity.WARNING)
                yield from self._reset_execution()
                
        def KillEnemies(self):
            self._parent.LogMessage("Killing Routine", "Starting Killing Routine", LogConsole.LogSeverity.INFO)
            self._parent.in_killing_routine = True
            if self._parent.build is not None:
                    build = self._parent.build  # now Pylance sees it as non-Optional
                    build.SetKillingRoutine(self._parent.in_killing_routine)

            player_pos = GLOBAL_CACHE.Player.GetXY()
            enemy_array = Routines.Agents.GetFilteredEnemyArray(player_pos[0],player_pos[1],Range.Spellcast.value)
            
            start_time = Utils.GetBaseTimestamp()
            timeout = 120000
            
            while len(enemy_array) > 0: #sometimes not all enemies are killed
                current_time = Utils.GetBaseTimestamp()
                delta = current_time - start_time
                if delta > timeout and timeout > 0:
                    self._parent.LogMessage("Killing Routine", "Timeout reached, restarting.", LogConsole.LogSeverity.ERROR)
                    yield from self._reset_execution()
                    return
                
                if not self._parent.script_running:
                    return
                    
                if Agent.IsDead(GLOBAL_CACHE.Player.GetAgentID()):
                    self._parent.LogMessage("Death", "Player is dead, restarting.", LogConsole.LogSeverity.WARNING)
                    yield from self._reset_execution()   
                yield from Routines.Yield.wait(1000)
                enemy_array = Routines.Agents.GetFilteredEnemyArray(player_pos[0],player_pos[1],Range.Spellcast.value)
            
            self._parent.in_killing_routine = False
            self._parent.finished_routine = True
            if self._parent.build is not None:
                build = self._parent.build  # now Pylance sees it as non-Optional
                build.SetKillingRoutine(self._parent.in_killing_routine)
                build.SetRoutineFinished(self._parent.finished_routine)
            self._parent.LogMessage("Killing Routine", "Finished Killing Routine", LogConsole.LogSeverity.INFO)
            yield from Routines.Yield.wait(1000)  # Wait a bit to ensure the enemies are dead
          
        def RemoveSkillCastingCoroutine(self):
            build = self._parent.build or ShadowFormAssassinVaettir()
            if build.ProcessSkillCasting() in GLOBAL_CACHE.Coroutines:
                GLOBAL_CACHE.Coroutines.remove(build.ProcessSkillCasting())
            if self._parent.HandleStuckJagaMoraine() in GLOBAL_CACHE.Coroutines:
                GLOBAL_CACHE.Coroutines.remove(self._parent.HandleStuckJagaMoraine())
            self._parent.farming_stats.EndCurrentRun(vaettirs_killed=Map.GetFoesKilled())
            self._parent.LogDetailedMessage("Skill Casting Coroutine", "Removed from Coroutines.", LogConsole.LogSeverity.INFO)
  
 
        def LootItems(self):
            self._parent.LogMessage("Looting Items", "Starting Looting Routine", LogConsole.LogSeverity.INFO)
            self._parent.SetCurrentStep("Loot Items", 0.10)
            yield from Routines.Yield.wait(1500)  # Wait for a second before starting to loot
            
            filtered_agent_ids = self.loot_singleton.GetfilteredLootArray(distance=Range.Earshot.value, multibox_loot=False, allow_unasigned_loot=True)
            yield from Routines.Yield.Items.LootItems(filtered_agent_ids, 
                                                      log=self._parent.detailed_logging,
                                                      progress_callback=self._parent.AdvanceProgress)
            
        def IdentifyAndSalvageItems(self):
            self._parent.LogMessage("Identifying and Salvaging Items", "Starting Identification and Salvaging Routine", LogConsole.LogSeverity.INFO)
            self._parent.SetCurrentStep("Identify and Salvage Items", 0.10)
            yield from self._parent.inventory_handler.IDAndSalvageItems(progress_callback=self._parent.AdvanceProgress)
            
        def CheckInventory(self):
            if  self._need_to_return_for_inventory_handling():
                yield from self._reset_execution()
                            
            
        def ExitJagaMoraine(self):
            self._parent.LogMessage("Exiting Jaga Moraine", "Resetting farm loop", LogConsole.LogSeverity.INFO)
            self._parent.SetCurrentStep("Exit Jaga Moraine", 0.05)
            self._parent.LogMessage("Exiting Jaga Moraine", "Reseting farm loop", LogConsole.LogSeverity.INFO)
            success_movement = yield from Routines.Yield.Movement.FollowPath(
                        path_points_to_exit_jaga_moraine,
                        custom_exit_condition=lambda: self._movement_eval_exit_on_map_loading(),
                        timeout=30000,  # 30 seconds timeout
                        log=False,
                        progress_callback=self._parent.AdvanceProgress)
            if not success_movement:
                yield from Routines.Yield.wait(1000)
                if not self._parent.script_running:
                    return
                
                if Agent.IsDead(GLOBAL_CACHE.Player.GetAgentID()):
                    self._parent.LogMessage("Death", "Player is dead, restarting.", LogConsole.LogSeverity.WARNING)
                    yield from Routines.Yield.wait(1000)
                    yield from self._reset_execution()
            
                if not Map.IsMapLoading():
                    if Map.GetMapID() != self._parent.BJORA_MARCHES:
                        self._parent.LogMessage("Failed to traverse Bjora Marches", "TIMEOUT", LogConsole.LogSeverity.ERROR)
                        yield from Routines.Yield.wait(1000)
                        yield from self._reset_execution()  
                    
        def WaitforBjoraMarches_returnMapLoad(self):
            self._parent.LogMessage("Waiting for Map Loading", "Bjora Marches", LogConsole.LogSeverity.INFO)
            wait_of_map_load = yield from Routines.Yield.Map.WaitforMapLoad(self._parent.BJORA_MARCHES, log=self._parent.detailed_logging)
            if not wait_of_map_load:
                self._parent.LogMessage("Map Load", "Timeout Loading Bjora Marches, stopping script.", LogConsole.LogSeverity.ERROR)
                yield from self._stop_execution()
                
        def ReturnToJagaMoraine(self):
            self._parent.LogMessage("Returning to Jaga Moraine", "Resetting farm loop", LogConsole.LogSeverity.INFO)
            success_movement = yield from Routines.Yield.Movement.FollowPath(
                        path_points_to_return_to_jaga_moraine,
                        custom_exit_condition=lambda: self._movement_eval_exit_on_map_loading(),
                        timeout= 30000,  # 30 seconds timeout
                        progress_callback=self._parent.AdvanceProgress)
            if not success_movement:
                yield from Routines.Yield.wait(1000)
                if not self._parent.script_running:
                    return
                
                if Agent.IsDead(GLOBAL_CACHE.Player.GetAgentID()):
                    self._parent.LogMessage("Death", "Player is dead, restarting.", LogConsole.LogSeverity.WARNING)
                    yield from self._reset_execution()
            
                if not Map.IsMapLoading():
                    if Map.GetMapID() != self._parent.JAGA_MORAINE:
                        self._parent.LogMessage("Failed to return to Jaga Moraine", "TIMEOUT", LogConsole.LogSeverity.ERROR)
                        yield from Routines.Yield.wait(1000)
                        yield from self._reset_execution()
            
            self._parent.FSM.jump_to_state_by_name("Wait for Jaga Moraine Map Load")

        