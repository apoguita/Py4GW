from Py4GWCoreLib import *
from Sources.Nikon_Scripts.BotUtilities import *
from Sources.Nikon_Scripts.WindowUtilites import *

from Sources.Nikon_Scripts import Mapping

bot_name = "Nikons Skalefin Soup Farm"

soup_selected = True
soup_exchange = False
soup_input = 250

class Soup_Window(BasicWindow):
    global soup_selected, soup_input, soup_exchange
    
    soup_original_size = [350.0, 400.0]
    soup_explanded_size = [350.0, 475.0]
    minimum_slots = 5

    config_test_collect = soup_input
    config_test_farm = soup_selected
    config_test_exchange = soup_exchange

    def __init__(self, window_name="Basic Window", window_size = [350.0, 470.0], show_logger = True, show_state = True):
        super().__init__(window_name, window_size, show_logger, show_state)

    def ShowMainControls(self):
        if PyImGui.collapsing_header("About - Farm Requirements"):
            PyImGui.begin_child("About_child_window", (0, 235), False, 0)
            PyImGui.text("- Dervish/Any or Any/Dervish")
            PyImGui.text("- Suggest Zealous Enchanting Scythe.")
            PyImGui.text("  \t*Droknars Reaper is perfect.")
            PyImGui.text("- Equip Scythe in Slot 2.")
            PyImGui.text("- Equip Staff in Slot 1 (not required).")
            PyImGui.text("- Inventory Snapshot Taken : Current Slots Safe.")
            PyImGui.text("- During salvage, saved slots are not touched.")
            PyImGui.text("- Moving items, you risk losing during sell.")
            PyImGui.text("- Just dont move items.")
            PyImGui.text("- Will not sell Skalefins, Rare Mats, Salv or Id kits.")
            PyImGui.text("- It takes 2 Skalefins per Soup.")
            PyImGui.end_child()
        PyImGui.separator()

    def ShowConfigSettingsTabItem(self):
        global soup_selected, soup_input, soup_exchange

        if PyImGui.begin_table("Collect_Inputs", 2, PyImGui.TableFlags.SizingStretchProp):
            PyImGui.table_next_row()
            PyImGui.table_next_column()
            soup_selected = PyImGui.checkbox("Farm Skalefin Soup", soup_selected)  
            PyImGui.table_next_column()
            soup_input = PyImGui.input_int("# Soup", soup_input) if soup_input >= 0 else 0 
            PyImGui.table_next_row()
            PyImGui.table_next_column()
            soup_exchange = PyImGui.checkbox("Exchange Skalefins", soup_exchange)
            PyImGui.table_next_row()
            PyImGui.table_next_column()
            self.leave_party = PyImGui.checkbox("Leave Party", self.leave_party)
            PyImGui.end_table()

    def ShowResults(self):
        global soup_input

        PyImGui.separator()
        
        if PyImGui.collapsing_header("Results##Soups", int(PyImGui.TreeNodeFlags.DefaultOpen)):
            if PyImGui.begin_table("Runs_Results", 6):
                soup_data = GetSoupData()
                PyImGui.table_next_row()
                PyImGui.table_next_column()
                PyImGui.text(f"Runs:")
                PyImGui.table_next_column() 
                PyImGui.text(f"{soup_data[0]}")
                PyImGui.table_next_column() 
                PyImGui.text(f"Success: ")
                PyImGui.table_next_column()
                PyImGui.text_colored(f"{soup_data[1]}", (0, 1, 0, 1))
                PyImGui.table_next_column()
                PyImGui.text(f"Fails:")
                PyImGui.table_next_column()
                fails = soup_data[0] - soup_data[1]

                if fails > 0:
                    PyImGui.text_colored(f"{fails}", (1, 0, 0, 1))
                else:
                    PyImGui.text(f"{fails}")

                PyImGui.table_next_row()
                PyImGui.table_next_column()
                PyImGui.text("Soup:")
                PyImGui.table_next_column()
                soup_count = GetSoupCollected()
                if soup_selected and soup_input > 0 and soup_count == 0:            
                    PyImGui.text_colored(f"{soup_count}", (1, 0, 0, 1))
                else:
                    PyImGui.text_colored(f"{soup_count}", (0, 1, 0, 1))
                PyImGui.table_next_column()
                PyImGui.text(f"collected of")
                PyImGui.table_next_column()                
                PyImGui.text(f"{soup_input}")
                PyImGui.table_next_row()
                PyImGui.end_table()

            if PyImGui.begin_table("Run_Times", 2):
                PyImGui.table_next_row()
                PyImGui.table_next_column()
                PyImGui.text(f"Current:")
                PyImGui.table_next_column()
                PyImGui.text(f"     {FormatTime(GetRunTime(), "mm:ss:ms")}")
                PyImGui.table_next_row()
                PyImGui.table_next_column()
                PyImGui.text(f"Avg. Run:")
                PyImGui.table_next_column()
                PyImGui.text(f"     {FormatTime(GetAverageRunTime(), "mm:ss:ms")}")
                PyImGui.table_next_row()
                PyImGui.table_next_column()
                PyImGui.text(f"Total:")
                PyImGui.table_next_column()
                PyImGui.text(f"{FormatTime(GetTotalRunTime())}")
                PyImGui.table_next_row()
                PyImGui.end_table()

        PyImGui.separator()

    def ShowBotControls(self):
        if PyImGui.begin_table("Bot_Controls", 4):
            PyImGui.table_next_row()
            PyImGui.table_next_column()

            if not self.IsBotRunning():
                if PyImGui.button("Start"):
                    StartBot()
            else:          
                if PyImGui.button("Stop"):
                    StopBot()     
                
            PyImGui.table_next_column()            
            if PyImGui.button("Reset"):
                ResetBot()  

            PyImGui.table_next_column()            
            if PyImGui.button("Print Saved Slots"):
                PrintData()  

            PyImGui.end_table() 
    
    def ApplyAndUpdateSettings(self):
        global soup_input, soup_exchange, soup_selected
        super().ApplyAndUpdateSettings()

        if self.config_test_collect != soup_input or \
            self.config_test_exchange != soup_exchange or \
            self.config_test_farm != soup_selected:
            self.ApplyConfigSettings()
    
            self.config_test_collect = soup_input
            self.config_test_farm = soup_selected
            self.config_test_exchange = soup_exchange

    def ApplyLootMerchantSettings(self) -> None:
        ApplyLootAndMerchantSelections()

    def ApplyConfigSettings(self) -> None:
        global soup_input, soup_exchange
        ApplySoupConfigSettings(self.leave_party, soup_input, soup_exchange)
        
    def ApplyInventorySettings(self) -> None:
        ApplySoupInventorySettings(self.minimum_slots, self.minimum_gold, self.depo_items, self.depo_mats)


    def GetSoupSettings(self):
        global soup_input

        return (soup_input, self.id_Items, self.collect_coins, self.collect_events, self.collect_items_white, self.collect_items_blue, \
                self.collect_items_grape, self.collect_items_gold, self.collect_dye, self.sell_items, self.sell_items_white, \
                self.sell_items_blue, self.sell_items_grape, self.sell_items_gold, self.sell_materials, self.salvage_items, self.salvage_items_white, \
                self.salvage_items_blue, self.salvage_items_grape, self.salvage_items_gold)
                
class Soup_Farm(ReportsProgress):
    class Soup_Skillbar:    
        def __init__(self):
            self.sand_shards = SkillBar.GetSkillIDBySlot(1)
            self.sand_shards_slot = 1
            self.vos = SkillBar.GetSkillIDBySlot(2)
            self.vos_slot = 2
            self.staggering = SkillBar.GetSkillIDBySlot(3)
            self.staggering_slot = 3
            self.eremites = SkillBar.GetSkillIDBySlot(4)
            self.eremites_slot = 4
            self.drunkMaster = SkillBar.GetSkillIDBySlot(7)
            self.drunkMaster_slot = 7
            self.regen = SkillBar.GetSkillIDBySlot(8)
            self.regen_slot = 8

    # soup_Routine is the FSM instance
    soup_Routine = FSM("soup_Main")
    soup_Exchange_Routine = FSM("soup_Exchange")
    inventoryRoutine = InventoryFsm(None, None, 0, None, None)

    soup_primary_dervish_skillbar_code = "Ogek8Np5Kzmk513m2VzFAAAgqI7F" #DASH VARIANT "Ogek8Np5Kzmj59brdbuAAAwEk9C" ABOUT THE SAME SPEED AS DRUNKEN AT 15%#

    soup_exchange_travel = "Soup- Exchange Travel Astralarium"
    soup_exchange_wait_map = "Soup- Exchange Waiting Map"
    soup_exchange_move_to_collector = "Soup- Exchange Go to Chef"
    soup_exchange_target_collector = "Soup- Exchange Target"
    soup_exchange_interact_collector = "Soup- Exchange Interact"
    soup_exchange_do_exchange_all = "Soup- Exchange Soup"
    soup_exchange_soup_routine_start = "Soup- Go Exchange Soup 1"
    soup_exchange_soup_routine_end = "Soup- Go Exchange Soup 2"
    
    soup_start_farm = "Soup- Check Farm"
    soup_inventory_routine = "DoInventoryRoutine"
    soup_initial_check_inventory = "Soup- Inventory Check"
    soup_check_inventory_after_handle_inventory = "Soup- Inventory Handled?"
    soup_travel_state_name = "Soup- Traveling to Jokanur"
    soup_set_normal_mode = "Soup- Set Normal Mode"
    soup_leave_party_name = "Soup- Leave Party Check"
    soup_load_skillbar_state_name = "Soup- Load Skillbar"
    soup_pathing_1_state_name = "Soup- Leaving Outpost 1"
    soup_resign_pathing_state_name = "Soup- Setup Resign"
    soup_pathing_2_state_name = "Soup- Leaving Outpost 2"
    soup_waiting_map_state_name = "Soup- Farm Map Loading"
    soup_change_weapon_staff = "Soup- Change to Staff"
    soup_change_weapon_scythe = "Soup- Change to Scythe"
    soup_running_group_1 = "Soup- Move Group 1"
    soup_killing_group_1 = "Soup- Kill Group 1"
    soup_looting_group_1 = "Soup- Loot Group 1"
    soup_running_group_2 = "Soup- Move Group 2"
    soup_killing_group_2 = "Soup- Kill Group 2"
    soup_looting_group_2 = "Soup- Loot Group 2"
    soup_running_group_3 = "Soup- Move Group 3"
    soup_killing_group_3 = "Soup- Kill Group 3"
    soup_looting_group_3 = "Soup- Loot Group 3"
    soup_running_group_4 = "Soup- Move Group 4"
    soup_killing_group_4 = "Soup- Kill Group 4"
    soup_looting_group_4 = "Soup- Loot Group 4"
    soup_running_group_5 = "Soup- Move Group 5"
    soup_killing_group_5 = "Soup- Kill Group 5"
    soup_looting_group_5 = "Soup- Loot Group 5"
    soup_running_group_6 = "Soup- Move Group 6"
    soup_killing_group_6 = "Soup- Kill Group 6"
    soup_looting_group_6 = "Soup- Loot Group 6"
    soup_running_group_7 = "Soup- Move Group 7"
    soup_killing_group_7 = "Soup- Kill Group 7"
    soup_looting_group_7 = "Soup- Loot Group 7"
    soup_running_group_8 = "Soup- Move Group 8"
    soup_killing_group_8 = "Soup- Kill Group 8"
    soup_looting_group_8 = "Soup- Loot Group 8"
    soup_run_success = "Soup- Success Run"
    soup_resign_state_name = "Soup- Resigning"
    soup_wait_return_state_name = "Soup- Wait Return"
    soup_inventory_state_name = "Soup- Handle Inventory 1"
    soup_inventory_state_name_end = "Soup-Handle Inventory 2"
    soup_end_state_name = "Soup- End Routine"
    soup_forced_stop = "Soup- End Forced"
    soup_outpost_portal = [(-92, -72), (-1599, -1007), (-2900, -1090)]
    soup_outpost_resign_pathing = [(20020, 10900), (20472, 8784)]
    soup_outpost_post_resign_pathing = [(-2900, -1090)]
    soup_merchant_position = [(1045, 218),(2809, 2026), (3219, 2257)]
    soup_running_group_1_path = [(17161, 12293)]
    soup_running_group_2_path = [(14739, 13352), (12892, 13348), (11291, 14052), (10976, 15984)]
    soup_running_group_3_path = [(9939, 18724), (9566, 18872)]
    soup_running_group_4_path = [(6140, 16900), (5925, 14401), (5812, 12975)]
    soup_running_group_5_path = [(4675, 12205), (4220, 10995)]
    soup_running_group_6_path = [(2939, 11926), (1679, 12360)]
    soup_running_group_7_path = [(1435, 13820), (2798, 14328)]
    soup_running_group_8_path = [(1248, 14083), (830, 15170), (1748, 16596)]
    soup_pathing_portal_only_handler_1 = Routines.Movement.PathHandler(soup_outpost_portal)
    soup_pathing_portal_only_handler_2 = Routines.Movement.PathHandler(soup_outpost_post_resign_pathing)
    soup_pathing_resign_portal_handler = Routines.Movement.PathHandler(soup_outpost_resign_pathing)
    soup_pathing_group_1 = Routines.Movement.PathHandler(soup_running_group_1_path)
    soup_pathing_group_2 = Routines.Movement.PathHandler(soup_running_group_2_path)
    soup_pathing_group_3 = Routines.Movement.PathHandler(soup_running_group_3_path)
    soup_pathing_group_4 = Routines.Movement.PathHandler(soup_running_group_4_path)
    soup_pathing_group_5 = Routines.Movement.PathHandler(soup_running_group_5_path)
    soup_pathing_group_6 = Routines.Movement.PathHandler(soup_running_group_6_path)
    soup_pathing_group_7 = Routines.Movement.PathHandler(soup_running_group_7_path)
    soup_pathing_group_8 = Routines.Movement.PathHandler(soup_running_group_8_path)
    
    soup_exchange_pathing = [(-1545, 2133), (-1638, 3894)]
    soup_exchange_pathing_handler = Routines.Movement.PathHandler(soup_exchange_pathing)
    exchange_movement_Handler = Routines.Movement.FollowXY(50)
    portal_movement_Handler = Routines.Movement.FollowXY(50)
    resign_movement_Handler = Routines.Movement.FollowXY(50)
    post_resign_movement_Handler = Routines.Movement.FollowXY(50)
    running_movement_Handler = Routines.Movement.FollowXY(50)
    
    keep_list = []
    keep_list.extend(IdSalveItems_Array)
    keep_list.extend(EventItems_Array)
    keep_list.append(ModelID.Skale_Fin)
    keep_list.append(ModelID.Vial_Of_Dye)
    
    soup_first_after_reset = False
    soup_wait_to_kill = False
    soup_ready_to_kill = False
    soup_killing_staggering_casted = False
    soup_killing_eremites_casted = False
    soup_exchange = False

    player_stuck_hos_count = 0
    player_skillbar_load_count = 0
    player_previous_hp = 100

    weapon_slot_staff = 1
    weapon_slot_scythe = 2
    soup_collected = 0
    add_koss_tries = 0
    current_lootable = 0
    current_loot_tries = 0
    current_run_time = 0
    average_run_time = 0
    default_min_slots = 5
    average_run_history = []
    
    soup_runs = 0
    soup_success = 0
    soup_fails = 0
    
    second_timer_elapsed = 1000
    loot_timer_elapsed = 1000
    
    pyParty = PyParty.PyParty()
    pyMerchant = PyMerchant.PyMerchant()
    soup_exchange_timer = Timer()
    soup_second_timer = Timer()
    soup_step_done_timer = Timer()
    soup_stuck_timer = Timer()
    soup_loot_timer = Timer()
    soup_loot_done_timer = Timer()
    soup_stay_alive_timer = Timer()

    stuckPosition = []

    ### --- SETUP --- ###
    def __init__(self, window):
        self.current_inventory = GetInventoryItemSlots()

        super().__init__(window, Mapping.Jokanur_Diggings, self.soup_merchant_position, self.current_inventory, self.keep_list)
        
        # Skalefin Exchange Sub Routine
        self.soup_Exchange_Routine.AddState(self.soup_exchange_travel,
                                             execute_fn=lambda: self.ExecuteStep(self.soup_exchange_travel, Routines.Transition.TravelToOutpost(Mapping.Astralarium)),
                                             exit_condition=lambda: Routines.Transition.HasArrivedToOutpost(Mapping.Astralarium),
                                             transition_delay_ms=1000)
        self.soup_Exchange_Routine.AddState(self.soup_exchange_move_to_collector,
                                             execute_fn=lambda: self.ExecuteStep(self.soup_exchange_move_to_collector, Routines.Movement.FollowPath(self.soup_exchange_pathing_handler, self.exchange_movement_Handler)),
                                             exit_condition=lambda: Routines.Movement.IsFollowPathFinished(self.soup_exchange_pathing_handler, self.exchange_movement_Handler),
                                             run_once=False)
        
        self.soup_Exchange_Routine.AddState(name=self.soup_exchange_target_collector,
                                             execute_fn=lambda: self.ExecuteStep(self.soup_exchange_target_collector, TargetNearestNpc()),
                                             transition_delay_ms=1000)
        
        self.soup_Exchange_Routine.AddState(name=self.soup_exchange_interact_collector,
                                             execute_fn=lambda: self.ExecuteStep(self.soup_exchange_interact_collector, Routines.Targeting.InteractTarget()),
                                             exit_condition=lambda: Routines.Targeting.HasArrivedToTarget())
        
        self.soup_Exchange_Routine.AddState(name=self.soup_exchange_do_exchange_all,
                                             execute_fn=lambda: self.ExecuteStep(self.soup_exchange_do_exchange_all, self.ExchangeSoups()),
                                             exit_condition=lambda: self.ExchangeSoupsDone(), 
                                             run_once=False)
        # Skalefin Exchange Sub Routine
        
        # Soup Farm Main Routine
        self.soup_Routine.AddSubroutine(self.soup_exchange_soup_routine_start,
                       sub_fsm=self.soup_Exchange_Routine,
                       condition_fn=lambda: self.CheckExchangeSoups() and CheckIfInventoryHasItem(ModelID.Skale_Fin))        
        self.soup_Routine.AddState(self.soup_start_farm,
                                    execute_fn=lambda: self.ExecuteStep(self.soup_start_farm, self.CheckIfShouldRunFarm()))
        self.soup_Routine.AddState(self.soup_travel_state_name,
                       execute_fn=lambda: self.ExecuteStep(self.soup_travel_state_name, Routines.Transition.TravelToOutpost(Mapping.Jokanur_Diggings)),
                       exit_condition=lambda: Routines.Transition.HasArrivedToOutpost(Mapping.Jokanur_Diggings),
                       transition_delay_ms=1000)
        self.soup_Routine.AddState(self.soup_initial_check_inventory, execute_fn=lambda: self.CheckInventory())
        self.soup_Routine.AddState(self.soup_set_normal_mode,
                       execute_fn=lambda: self.ExecuteStep(self.soup_set_normal_mode, self.InternalStart()),
                       transition_delay_ms=1000)
        self.soup_Routine.AddState(self.soup_leave_party_name,
                       execute_fn=lambda: self.ExecuteStep(self.soup_leave_party_name, Party.LeaveParty() if self.leave_party else None), # Ensure only one hero in party
                       transition_delay_ms=1000)
        self.soup_Routine.AddState(self.soup_load_skillbar_state_name,
                       execute_fn=lambda: self.ExecuteStep(self.soup_load_skillbar_state_name, self.LoadSkillBar()), # Ensure only one hero in party                       
                       exit_condition=lambda: self.IsSkillBarLoaded(),
                       transition_delay_ms=1500)
        self.soup_Routine.AddState(self.soup_pathing_1_state_name,
                       execute_fn=lambda: self.ExecuteStep(self.soup_pathing_1_state_name, Routines.Movement.FollowPath(self.soup_pathing_portal_only_handler_1, self.portal_movement_Handler)),
                       exit_condition=lambda: Routines.Movement.IsFollowPathFinished(self.soup_pathing_portal_only_handler_1, self.portal_movement_Handler) or (Map.GetMapID() == Mapping.Fahranur_First_City and Party.IsPartyLoaded()),
                       run_once=False)
        self.soup_Routine.AddState(self.soup_resign_pathing_state_name,
                       execute_fn=lambda: self.ExecuteStep(self.soup_resign_pathing_state_name, Routines.Movement.FollowPath(self.soup_pathing_resign_portal_handler, self.resign_movement_Handler)),
                       exit_condition=lambda: Routines.Movement.IsFollowPathFinished(self.soup_pathing_resign_portal_handler, self.resign_movement_Handler) or (Map.GetMapID() == Mapping.Jokanur_Diggings and Party.IsPartyLoaded()),
                       run_once=False)
        self.soup_Routine.AddSubroutine(self.soup_inventory_state_name,
                       sub_fsm = self.inventoryRoutine, # dont add execute function wrapper here
                       condition_fn=lambda: not self.soup_first_after_reset and Inventory.GetFreeSlotCount() <= self.default_min_slots)
        self.soup_Routine.AddState(self.soup_check_inventory_after_handle_inventory, execute_fn=lambda: self.CheckInventory())
        
        # Switch back n forth between staff/scythe to ensure have enough energy at each point.  
        self.soup_Routine.AddState(self.soup_change_weapon_staff,
                       execute_fn=lambda: self.ExecuteStep(self.soup_change_weapon_staff, self.RunStarting()),
                       transition_delay_ms=1000)
        self.soup_Routine.AddState(self.soup_pathing_2_state_name,
                       execute_fn=lambda: self.ExecuteStep(self.soup_pathing_2_state_name, Routines.Movement.FollowPath(self.soup_pathing_portal_only_handler_2, self.post_resign_movement_Handler)),
                       exit_condition=lambda: Routines.Movement.IsFollowPathFinished(self.soup_pathing_portal_only_handler_2, self.post_resign_movement_Handler) or Map.GetMapID() == Mapping.Fahranur_First_City,
                       run_once=False)
        self.soup_Routine.AddState(self.soup_waiting_map_state_name,
                       execute_fn=lambda: self.ExecuteStep(self.soup_waiting_map_state_name, Routines.Transition.IsExplorableLoaded()),
                       transition_delay_ms=1000)
        
        ### === BELOW HERE IS RUN > FIGHT > LOOT LOOP === ###
        ### FIRST GROUP ###
        self.soup_Routine.AddState(self.soup_running_group_1,
                       execute_fn=lambda: self.ExecuteTimedStep(self.soup_running_group_1, self.TimeToRunToSkale(self.soup_pathing_group_1, self.running_movement_Handler)),
                       exit_condition=lambda: self.RunToSkaleDone(self.soup_pathing_group_1, self.running_movement_Handler),
                       run_once=False)
        self.soup_Routine.AddState(self.soup_change_weapon_scythe,
                       execute_fn=lambda: self.ExecuteStep(self.soup_change_weapon_scythe, ChangeWeaponSet(self.weapon_slot_scythe)),
                       transition_delay_ms=1000)
        self.soup_Routine.AddState(self.soup_killing_group_1,
                       execute_fn=lambda: self.ExecuteTimedStep(self.soup_killing_group_1, self.KillLoopStart()),
                       exit_condition=lambda: self.KillLoopComplete(),
                       run_once=False)
        self.soup_Routine.AddState(self.soup_looting_group_1,
                       execute_fn=lambda: self.ExecuteTimedStep(self.soup_looting_group_1, self.LootLoopStart()),
                       exit_condition=lambda: self.LootLoopComplete() or self.ShouldForceTransitionStep(),
                       run_once=False)
        ### FIRST GROUP ###
        ### SECOND GROUP ###        
        self.soup_Routine.AddState(self.soup_running_group_2,
                       execute_fn=lambda: self.ExecuteTimedStep(self.soup_running_group_2, self.TimeToRunToSkale(self.soup_pathing_group_2, self.running_movement_Handler)),
                       exit_condition=lambda: self.RunToSkaleDone(self.soup_pathing_group_2, self.running_movement_Handler),
                       run_once=False)
        self.soup_Routine.AddState(self.soup_killing_group_2,
                       execute_fn=lambda: self.ExecuteTimedStep(self.soup_killing_group_2, self.KillLoopStart()),
                       exit_condition=lambda: self.KillLoopComplete(),
                       run_once=False)
        self.soup_Routine.AddState(self.soup_looting_group_2,
                       execute_fn=lambda: self.ExecuteTimedStep(self.soup_looting_group_2, self.LootLoopStart()),
                       exit_condition=lambda: self.LootLoopComplete() or self.ShouldForceTransitionStep(),
                       run_once=False)
        ### SECOND GROUP ###
        ### THIRD GROUP ###        
        self.soup_Routine.AddState(self.soup_running_group_3,
                       execute_fn=lambda: self.ExecuteTimedStep(self.soup_running_group_3, self.TimeToRunToSkale(self.soup_pathing_group_3, self.running_movement_Handler)),
                       exit_condition=lambda: self.RunToSkaleDone(self.soup_pathing_group_3, self.running_movement_Handler),
                       run_once=False)
        self.soup_Routine.AddState(self.soup_killing_group_3,
                       execute_fn=lambda: self.ExecuteTimedStep(self.soup_killing_group_3, self.KillLoopStart()),
                       exit_condition=lambda: self.KillLoopComplete(),
                       run_once=False)
        self.soup_Routine.AddState(self.soup_looting_group_3,
                       execute_fn=lambda: self.ExecuteTimedStep(self.soup_looting_group_3, self.LootLoopStart()),
                       exit_condition=lambda: self.LootLoopComplete() or self.ShouldForceTransitionStep(),
                       run_once=False)
        ### THIRD GROUP ###
        ### FOURTH GROUP ###        
        self.soup_Routine.AddState(self.soup_running_group_4,
                       execute_fn=lambda: self.ExecuteTimedStep(self.soup_running_group_4, self.TimeToRunToSkale(self.soup_pathing_group_4, self.running_movement_Handler)),
                       exit_condition=lambda: self.RunToSkaleDone(self.soup_pathing_group_4, self.running_movement_Handler),
                       run_once=False)
        self.soup_Routine.AddState(self.soup_killing_group_4,
                       execute_fn=lambda: self.ExecuteTimedStep(self.soup_killing_group_4, self.KillLoopStart()),
                       exit_condition=lambda: self.KillLoopComplete(),
                       run_once=False)
        self.soup_Routine.AddState(self.soup_looting_group_4,
                       execute_fn=lambda: self.ExecuteTimedStep(self.soup_looting_group_4, self.LootLoopStart()),
                       exit_condition=lambda: self.LootLoopComplete() or self.ShouldForceTransitionStep(),
                       run_once=False)
        ### FOURTH GROUP ###
        ### FIFTH GROUP ###        
        self.soup_Routine.AddState(self.soup_running_group_5,
                       execute_fn=lambda: self.ExecuteTimedStep(self.soup_running_group_5, self.TimeToRunToSkale(self.soup_pathing_group_5, self.running_movement_Handler)),
                       exit_condition=lambda: self.RunToSkaleDone(self.soup_pathing_group_5, self.running_movement_Handler),
                       run_once=False)
        self.soup_Routine.AddState(self.soup_killing_group_5,
                       execute_fn=lambda: self.ExecuteTimedStep(self.soup_killing_group_5, self.KillLoopStart()),
                       exit_condition=lambda: self.KillLoopComplete(),
                       run_once=False)
        self.soup_Routine.AddState(self.soup_looting_group_5,
                       execute_fn=lambda: self.ExecuteTimedStep(self.soup_looting_group_5, self.LootLoopStart()),
                       exit_condition=lambda: self.LootLoopComplete() or self.ShouldForceTransitionStep(),
                       run_once=False)
        ### FIFTH GROUP ###
        ### SIXTH GROUP ###        
        self.soup_Routine.AddState(self.soup_running_group_6,
                       execute_fn=lambda: self.ExecuteTimedStep(self.soup_running_group_6, self.TimeToRunToSkale(self.soup_pathing_group_6, self.running_movement_Handler)),
                       exit_condition=lambda: self.RunToSkaleDone(self.soup_pathing_group_6, self.running_movement_Handler),
                       run_once=False)
        self.soup_Routine.AddState(self.soup_killing_group_6,
                       execute_fn=lambda: self.ExecuteTimedStep(self.soup_killing_group_6, self.KillLoopStart()),
                       exit_condition=lambda: self.KillLoopComplete(),
                       run_once=False)
        self.soup_Routine.AddState(self.soup_looting_group_6,
                       execute_fn=lambda: self.ExecuteTimedStep(self.soup_looting_group_6, self.LootLoopStart()),
                       exit_condition=lambda: self.LootLoopComplete() or self.ShouldForceTransitionStep(),
                       run_once=False)
        ### SIXTH GROUP ###
        ### SEVENTH GROUP ###        
        self.soup_Routine.AddState(self.soup_running_group_7,
                       execute_fn=lambda: self.ExecuteTimedStep(self.soup_running_group_7, self.TimeToRunToSkale(self.soup_pathing_group_7, self.running_movement_Handler)),
                       exit_condition=lambda: self.RunToSkaleDone(self.soup_pathing_group_7, self.running_movement_Handler),
                       run_once=False)
        self.soup_Routine.AddState(self.soup_killing_group_7,
                       execute_fn=lambda: self.ExecuteTimedStep(self.soup_killing_group_7, self.KillLoopStart()),
                       exit_condition=lambda: self.KillLoopComplete(),
                       run_once=False)
        self.soup_Routine.AddState(self.soup_looting_group_7,
                       execute_fn=lambda: self.ExecuteTimedStep(self.soup_looting_group_7, self.LootLoopStart()),
                       exit_condition=lambda: self.LootLoopComplete() or self.ShouldForceTransitionStep(),
                       run_once=False)
        ### SEVENTH GROUP ###
        ### EIGTH GROUP ###        
        self.soup_Routine.AddState(self.soup_running_group_8,
                       execute_fn=lambda: self.ExecuteTimedStep(self.soup_running_group_8, self.TimeToRunToSkale(self.soup_pathing_group_8, self.running_movement_Handler)),
                       exit_condition=lambda: self.RunToSkaleDone(self.soup_pathing_group_8, self.running_movement_Handler),
                       run_once=False)
        self.soup_Routine.AddState(self.soup_killing_group_8,
                       execute_fn=lambda: self.ExecuteTimedStep(self.soup_killing_group_8, self.KillLoopStart()),
                       exit_condition=lambda: self.KillLoopComplete(),
                       run_once=False)
        self.soup_Routine.AddState(self.soup_looting_group_8,
                       execute_fn=lambda: self.ExecuteTimedStep(self.soup_looting_group_8, self.LootLoopStart()),
                       exit_condition=lambda: self.LootLoopComplete() or self.ShouldForceTransitionStep(),
                       run_once=False)
        ### EIGTH GROUP ###
        ### === ABOVE HERE IS RUN > FIGHT > LOOT LOOP === ###

        # Resign after all are done
        self.soup_Routine.AddState(self.soup_run_success,
                       execute_fn=lambda: self.ExecuteStep(self.soup_run_success, self.SuccessResign()))
        self.soup_Routine.AddState(self.soup_resign_state_name,
                       execute_fn=lambda: self.ExecuteStep(self.soup_resign_state_name, Player.SendChatCommand("resign")),
                       exit_condition=lambda: Agent.IsDead(Player.GetAgentID()) or Map.GetMapID() == Mapping.Jokanur_Diggings,
                       transition_delay_ms=3000)
        self.soup_Routine.AddState(self.soup_wait_return_state_name,
                       execute_fn=lambda: self.ExecuteTimedStep(self.soup_wait_return_state_name, Party.ReturnToOutpost()),
                       exit_condition=lambda: Map.GetMapID() == Mapping.Jokanur_Diggings and Party.IsPartyLoaded(),
                       transition_delay_ms=3000)
        self.soup_Routine.AddState(self.soup_end_state_name,
                       execute_fn=lambda: self.ExecuteStep(self.soup_end_state_name, self.CheckSoupRoutineEnd()),
                       transition_delay_ms=1000)        
        self.soup_Routine.AddSubroutine(self.soup_inventory_state_name_end,
                       sub_fsm = self.inventoryRoutine)       
        self.soup_Routine.AddSubroutine(self.soup_exchange_soup_routine_end,
                       condition_fn=lambda: self.CheckExchangeSoups() and CheckIfInventoryHasItem(ModelID.Skale_Fin))
        self.soup_Routine.AddState(self.soup_forced_stop,                                    
                       execute_fn=lambda: self.ExecuteStep(self.soup_forced_stop, None))
        
        self.RunTimer = Timer()
        self.TotalTimer = Timer()

    def CheckExchangeSoups(self):
        self.Log(f"Exchange Skalefins: {self.soup_exchange}")
        return self.soup_exchange
    
    def ApplyConfigSettingsOverride(self, leave_party, collect_input, do_soup_exchange) -> None:
        self.ApplyConfigSettings(leave_party, collect_input)
        self.soup_exchange = do_soup_exchange
        
    # Start the Soup routine from the first state after soft reset in case player moved around.
    def Start(self):
        if self.soup_Routine and not self.soup_Routine.is_started():
            self.SoftReset()
            self.soup_Routine.start()
            self.window.StartBot()

    # Stop the Soup routine.
    def Stop(self):
        if not self.soup_Routine:
            return
        
        self.InternalStop()
        
        if self.soup_Routine.is_started():
            self.soup_Routine.stop()
            self.window.StopBot()

    def InternalStart(self):
        Party.SetNormalMode()
        self.TotalTimer.Start()

    def InternalStop(self):
        self.soup_Routine.jump_to_state_by_name(self.soup_forced_stop)
        self.window.StopBot()
        self.TotalTimer.Stop()
        self.RunTimer.Stop()

    def Reset(self):     
        if self.soup_Routine:
            self.InternalStop()
        
        self.soup_collected = 0    
        self.soup_runs = 0
        self.soup_success = 0
        self.soup_fails = 0

        self.soup_first_after_reset = True      
        self.average_run_history.clear()
        self.average_run_time = 0
        self.current_run_time = 0   

        self.SoftReset()

        # Get new set of inventory slots to keep around in case player went and did some shit, then came back
        self.window.ResetBot()

    def SoftReset(self):
        self.player_stuck = False
        self.soup_wait_to_kill = False
        self.soup_ready_to_kill = False
        self.soup_killing_staggering_casted = False
        self.soup_killing_eremites_casted = False
        self.step_transition_threshold_timer.Reset()
        
        self.add_koss_tries = 0
        self.player_stuck_hos_count = 0
        self.current_lootable = 0
        self.current_loot_tries = 0
        
        self.inventoryRoutine.Reset()
        self.inventoryRoutine.ApplySelections(idItems=self.idItems, sellItems=self.sellItems, sellWhites=self.sellWhites, 
                                             sellBlues=self.sellBlues, sellGrapes=self.sellGrapes, sellGolds=self.sellGolds, sellGreens=self.sellGreens, 
                                             sellMaterials=self.sellMaterials, salvageItems=self.salvageItems, salvWhites=self.salvWhites, salvBlue=self.salvBlues,
                                             salvGrapes=self.salvGrapes, salvGolds=self.salvGold)
        self.ResetPathing()

    def ResetPathing(self):        
        self.running_movement_Handler.reset()
        self.portal_movement_Handler.reset()
        self.resign_movement_Handler.reset()
        self.post_resign_movement_Handler.reset()
        self.exchange_movement_Handler.reset()

        self.soup_exchange_pathing_handler.reset()
        self.soup_loot_timer.Stop()
        self.soup_loot_done_timer.Stop()
        self.soup_stuck_timer.Stop()
        self.soup_second_timer.Stop()
        self.soup_stay_alive_timer.Stop()
        self.soup_step_done_timer.Stop()
        self.soup_pathing_resign_portal_handler.reset()
        self.soup_pathing_portal_only_handler_1.reset()
        self.soup_pathing_portal_only_handler_2.reset()
        self.soup_pathing_group_1.reset()
        self.soup_pathing_group_2.reset()
        self.soup_pathing_group_3.reset()
        self.soup_pathing_group_4.reset()
        self.soup_pathing_group_5.reset()
        self.soup_pathing_group_6.reset()
        self.soup_pathing_group_7.reset()
        self.soup_pathing_group_8.reset()

    def IsBotRunning(self):
        return self.soup_Routine.is_started() and not self.soup_Routine.is_finished()

    def Update(self):
        if self.soup_Routine.is_started() and not self.soup_Routine.is_finished():
            self.soup_Routine.update()

    def Resign(self):
        if self.soup_Routine.is_started():
            self.soup_runs += 1
            self.soup_Routine.jump_to_state_by_name(self.soup_resign_state_name)

    def SuccessResign(self):
        self.Resign()
        self.soup_success += 1

    def FailResign(self):
        self.Resign()
        self.soup_fails += 1

    def RunStarting(self):
        self.RunTimer.Reset()

        if not self.TotalTimer.IsRunning():
            self.TotalTimer.Start()

        # starting new run, change to staff if available
        ChangeWeaponSet(self.weapon_slot_staff)

    def RunEnding(self):
        elapsed = self.RunTimer.GetElapsedTime()
        self.RunTimer.Stop()

        self.average_run_history.append(elapsed)

        if len(self.average_run_history) >= 100:
            self.average_run_history.pop(0)

        self.average_run_time = sum(self.average_run_history) / len(self.average_run_history)

    def CheckIfShouldRunFarm(self):
        global soup_selected
        if not soup_selected:
            self.soup_Routine.jump_to_state_by_name(self.soup_end_state_name)

    def GetCurrentRunTime(self):
        return self.RunTimer.GetElapsedTime()
    
    def GetAverageTime(self):
        return self.average_run_time
    
    def GetTotalTime(self):
        return self.TotalTimer.GetElapsedTime()
    
    def ExchangeSoups(self):
        if not self.soup_exchange_timer.IsRunning():
            self.soup_exchange_timer.Start()

        if not self.soup_exchange_timer.HasElapsed(40):
            return
        
        self.soup_exchange_timer.Reset()

        try:
            turn_in = GetItemIdFromModelId(ModelID.Skale_Fin, 2)
            count = GetModelIdCount(ModelID.Skale_Fin)

            if turn_in == 0 or count < 2:
                return
            
            items3 = self.pyMerchant.get_merchant_item_list()                
            if items3:
                for item in items3:
                    if Item.GetModelID(item) == ModelID.Bowl_Of_Skalefin_Soup:
                        buy = [2]
                        if len(turn_in) > 1:
                            buy = [1, 1]
                        self.pyMerchant.collector_buy_item(item, 0, turn_in, buy)

        except Exception as e:
            self.Log(f"Error in Exchanging soup: {str(e)}", Py4GW.Console.MessageType.Error)

    def ExchangeSoupsDone(self):
        return not CheckIfInventoryHasItem(ModelID.Skale_Fin, 2)
        
    def CheckInventory(self):
        if Inventory.GetFreeSlotCount() <= self.default_min_slots:
            self.Log("Bags Full - Manually Handle")
            self.Stop()

    def Log(self, text, msgType=Py4GW.Console.MessageType.Info):
        if self.window:
            self.window.Log(text, msgType)
    ### --- SETUP --- ###

    ### --- ROUTINE FUNCTIONS --- ###
    def LoadSkillBar(self):
        primary, _ = Agent.GetProfessionNames(Player.GetAgentID())
        
        if primary == "Dervish":
            SkillBar.LoadSkillTemplate(self.soup_primary_dervish_skillbar_code)
        #elif secondary == "Dervish":
        #    pass
        else:
            self.Log("For Best Results use Dervish Primary")
            self.InternalStop()

    
    def IsSkillBarLoaded(self):
        primary, _ = Agent.GetProfessionNames(Player.GetAgentID())
        
        if primary != "Dervish":        
            self.Log("Bot Requires Dervish Primary", Py4GW.Console.MessageType.Error)            
            self.InternalStop()
            return False        
        # elif secondary != "Assassin":
        #     self.Log("Bot Requires Assassin Secondary")
        #     self.InternalStop()
        #     return False
        else:
            # Only require 1,2,3,4 and 8
            if SkillBar.GetSkillIDBySlot(1) == 0 or SkillBar.GetSkillIDBySlot(2) == 0 or \
            SkillBar.GetSkillIDBySlot(3) == 0 or SkillBar.GetSkillIDBySlot(4) == 0 or \
            SkillBar.GetSkillIDBySlot(8) == 0:
                self.player_skillbar_load_count += 1
                if self.player_skillbar_load_count > 10:
                    self.Log("Unable to Load Skills")
                    self.InternalStop()
                return False
        
        self.skillBar = self.Soup_Skillbar()
        return True

    # This function is executed for each run to skales
    def TimeToRunToSkale(self, path_handler, movement_handler):
        if not self.soup_second_timer.IsRunning():
            self.soup_second_timer.Start()

        if not self.soup_second_timer.HasElapsed(100):
            return
        
        self.soup_second_timer.Reset()
                      
        try:
            player_id = Player.GetAgentID()
            if Agent.IsDead(player_id):
                self.FailResign()
                return
            
            if not HasBuff(player_id, self.skillBar.drunkMaster):
                CastSkillByIdAndSlot(self.skillBar.drunkMaster, self.skillBar.drunkMaster_slot)
                
            # Run the stay alive script.
            self.StayAliveLoop()

            # Try to follow the path based on pathing points and movement handler.
            Routines.Movement.FollowPath(path_handler, movement_handler)
        except Exception as e:
            Py4GW.Console.Log("Run To Drakes", str(e), Py4GW.Console.MessageType.Error)

    def RunToSkaleDone(self, path_handler, movement_handler):
        if not self.soup_step_done_timer.IsRunning():
            self.soup_step_done_timer.Start()

        if not self.soup_step_done_timer.HasElapsed(500):
            return False
        
        self.soup_step_done_timer.Reset()

        pathDone = Routines.Movement.IsFollowPathFinished(path_handler, movement_handler)         
        surrounded = CheckSurrounded(2)
        forceStep = self.ShouldForceTransitionStep()

        done = pathDone or surrounded or forceStep or self.player_stuck
        if done:
            self.soup_step_done_timer.Stop()

        return done

    def KillLoopStart(self):
        self.StayAliveLoop()
        self.Kill()

    # Stay alive using all heal buffs and hos if available
    def StayAliveLoop(self):
        if not self.soup_stay_alive_timer.IsRunning():
            self.soup_stay_alive_timer.Start()

        if not self.soup_stay_alive_timer.HasElapsed(1000):
            return
        
        self.soup_stay_alive_timer.Reset()

        try:            
            player_id = Player.GetAgentID()

            if Agent.IsDead(player_id):
                self.FailResign()
                return
                
            if not CanCast(player_id):
                return
             
            if self.soup_killing_staggering_casted:
                return

            enemies = AgentArray.GetEnemyArray()
            enemies = AgentArray.Filter.ByDistance(enemies, Player.GetXY(), GameAreas.Spellcast)
            enemies = AgentArray.Filter.ByAttribute(enemies, 'IsAlive')

            if len(enemies) > 0:
                # Cast stay alive spells if needed.
                maxHp = Agent.GetMaxHealth(player_id)                
                hp = Agent.GetHealth(player_id) * maxHp
                dangerHp = .8 * maxHp
                                                  
                regen_time_remain = 0
                shards_time_remain = 0 
                                  
                player_buffs = Effects.GetEffects(player_id)

                for buff in player_buffs:
                    if buff.skill_id == self.skillBar.regen:
                        regen_time_remain = buff.time_remaining 
                    if buff.skill_id == self.skillBar.sand_shards:
                        shards_time_remain = buff.time_remaining

                if hp < dangerHp and regen_time_remain < 3000 and HasEnoughEnergy(self.skillBar.regen) and IsSkillReadyById(self.skillBar.regen):
                    CastSkillByIdAndSlot(self.skillBar.regen, self.skillBar.regen_slot)
                    return
               
                if shards_time_remain < 4000 and IsSkillReadyById(self.skillBar.sand_shards) and HasEnoughEnergy(self.skillBar.sand_shards) and len(enemies) > 1:
                    CastSkillByIdAndSlot(self.skillBar.sand_shards, self.skillBar.sand_shards_slot)
        except Exception as e:
            Py4GW.Console.Log("StayAlive", str(e), Py4GW.Console.MessageType.Error)

    def Kill(self):
        if not self.soup_second_timer.IsRunning():
            self.soup_second_timer.Start()

        if not self.soup_second_timer.HasElapsed(1000):
            return
        
        self.soup_second_timer.Reset()

        try:  
            # Start waiting to kill routine. 
            player_id = Player.GetAgentID()            

            if Agent.IsDead(player_id):
                self.FailResign()
                return
            
            if not CanCast(player_id):
                return  

            if (Map.IsMapReady() and not Map.IsMapLoading()):
                if (Map.IsExplorable() and Map.GetMapID() == Mapping.Fahranur_First_City and Party.IsPartyLoaded()):
                    enemies = AgentArray.GetEnemyArray()
                    enemies = AgentArray.Filter.ByDistance(enemies, Player.GetXY(), GameAreas.Lesser_Earshot)
                    enemies = AgentArray.Filter.ByAttribute(enemies, 'IsAlive')
                    enemies = AgentArray.Sort.ByDistance(enemies, Player.GetXY())
                                           
                    # Ensure have damage mitigation up before attacking
                    if len(enemies) == 0:
                        return
                    
                    target = Player.GetTargetID()

                    if target != enemies[0]:
                        target = enemies[0]

                    Player.ChangeTarget(target)
                        
                    if self.soup_killing_staggering_casted and IsSkillReadyById(self.skillBar.eremites) and HasEnoughEnergy(self.skillBar.eremites):  
                        self.soup_killing_staggering_casted = False
                        CastSkillByIdAndSlot(self.skillBar.eremites, self.skillBar.eremites_slot)
                        return                    
                    
                    vos_time_remain = 0
                    shards_time_remain = 0 

                    # Cast stay alive spells if needed.      
                    player_buffs = Effects.GetEffects(player_id)
                    
                    for buff in player_buffs:
                        if buff.skill_id == self.skillBar.vos:
                            vos_time_remain = buff.time_remaining
                        if buff.skill_id == self.skillBar.sand_shards:
                            shards_time_remain = buff.time_remaining

                    if not self.soup_killing_staggering_casted and shards_time_remain < 4000 and IsSkillReadyById(self.skillBar.sand_shards) and HasEnoughEnergy(self.skillBar.sand_shards) and len(enemies) > 1:
                        CastSkillByIdAndSlot(self.skillBar.sand_shards, self.skillBar.sand_shards_slot)
                        return
                                            
                    # Get Ready for killing
                    # Need find a way to change weapon set since  sending the change keys is not working for F1-F4
                    # For now assume we're good to go.
                    if not self.soup_killing_staggering_casted and vos_time_remain < 3000 and IsSkillReadyById(self.skillBar.vos) and HasEnoughEnergy(self.skillBar.vos):                        
                        CastSkillByIdAndSlot(self.skillBar.vos, self.skillBar.vos_slot)
                        return
                        
                    if IsSkillReadyById(self.skillBar.eremites) and HasEnoughEnergy(self.skillBar.eremites) and GetDistance(player_id, target) <= GameAreas.Nearby:
                        if IsSkillReadyById(self.skillBar.staggering) and HasEnoughEnergy(self.skillBar.staggering):
                            self.soup_killing_staggering_casted = True
                            CastSkillByIdAndSlot(self.skillBar.staggering, self.skillBar.staggering_slot)
                            return
                    Player.Interact(target)
        except Exception as e:
            Py4GW.Console.Log("Kill Loop Error", f"Kill Loop Error {str(e)}", Py4GW.Console.MessageType.Error)

    def KillLoopComplete(self):
        try:
            if Agent.IsDead(Player.GetAgentID()):
                self.FailResign()
                return False
        
            enemies = AgentArray.GetEnemyArray()
            enemies = AgentArray.Filter.ByDistance(enemies, Player.GetXY(), GameAreas.Lesser_Earshot)
            enemies = AgentArray.Filter.ByAttribute(enemies, 'IsAlive')

            if len(enemies) == 0:
                self.current_lootable = 0
                self.current_loot_tries = 0
                self.soup_second_timer.Stop()
                self.soup_stay_alive_timer.Stop()
                self.running_movement_Handler.reset()
                return True

            return False
        except:
            self.Log("Kill Loop Error", Py4GW.Console.MessageType.Error)

    # If issues comment internals and call super().CanPickUp()
    def CanPickUp(self, agentId, player_id):
        # Check if our item is a Soup first, otherwise let base hangle it.
        item_owner_id = Agent.GetItemAgentOwnerID(agentId)
        item_id = Agent.GetItemAgentItemID(agentId)

        if item_id:
            if item_owner_id != 0 and player_id != 0 and item_owner_id != player_id:
                return False
            
            model = Item.GetModelID(item_id)
            if model == ModelID.Skale_Fin:
                return True
            else:
                return super().CanPickUp(agentId, player_id)
              
        return False
    
    def LootLoopStart(self):
        try:
            if not self.soup_loot_timer.IsRunning():
                self.soup_loot_timer.Start()

            if self.soup_loot_timer.HasElapsed(self.loot_timer_elapsed):                
                self.soup_loot_timer.Reset()

                # Check if the current item has been picked up.
                if self.current_lootable != 0:
                    test = Agent.GetItemAgentItemID(self.current_lootable)

                    if test != 0:
                        self.current_loot_tries += 1
                   
                        if self.current_loot_tries > 5:
                            self.current_lootable = 0
                        else:
                            return
                
                self.current_lootable = 0
                self.current_loot_tries = 0
                item = self.GetNearestPickupItem(Player.GetAgentID())

                if item == 0 or item == None:
                    self.current_lootable = 0
                    return                
                
                if self.current_lootable != item:
                    self.current_lootable = item

                item_id = Agent.GetItemAgentItemID(self.current_lootable)
                model = Item.GetModelID(item_id)

                if model == ModelID.Skale_Fin:
                    self.soup_collected += 1

                Player.Interact(item)
        except Exception as e:
            Py4GW.Console.Log("Loot Loop", f"Error during looting {str(e)}", Py4GW.Console.MessageType.Error)

    def LootLoopComplete(self):
        try:
            if not self.soup_loot_done_timer.IsRunning():
                self.soup_loot_done_timer.Start()

            if self.soup_loot_done_timer.HasElapsed(self.loot_timer_elapsed):
                self.soup_loot_done_timer.Reset()

                if self.current_lootable == 0 or Inventory.GetFreeSlotCount() == 0:
                    self.soup_loot_timer.Stop()
                    self.soup_loot_done_timer.Stop()
                    return True

            return False
        except Exception as e:
            Py4GW.Console.Log("Loot Loop Complete", f"Error during looting {str(e)}", Py4GW.Console.MessageType.Error)
    
    def GetSoupCollected(self):
        return self.soup_collected

    def GetSoupStats(self):
        return (self.soup_runs, self.soup_success)
    
    # Jump back to output pathing if not done collecting
    def CheckSoupRoutineEnd(self):
        global soup_selected, soup_exchange

        # Don't reset the Soup count
        self.RunEnding()
        self.SoftReset()

        self.soup_first_after_reset = False

        if not soup_selected:
            self.Log("Not Farming Soup - AutoStop")
            if soup_exchange:
                self.soup_Routine.jump_to_state_by_name(self.soup_exchange_soup_routine_end)
            else:
                self.InternalStop()
            return
        
        if (self.soup_collected / 2) < self.main_item_collect:
            # mapping to outpost may have failed OR the threshold was reached. Try to map there and start over.
            if Map.GetMapID() != Mapping.Jokanur_Diggings:
                self.soup_Routine.jump_to_state_by_name(self.soup_travel_state_name)
            else:
                # already at outpost, check slot count, handle inv or continue farm
                if Inventory.GetFreeSlotCount() <= self.default_min_slots:
                    self.UpdateState(self.soup_inventory_state_name)
                    self.soup_Routine.jump_to_state_by_name(self.soup_inventory_state_name)
                else:
                    self.soup_Routine.jump_to_state_by_name(self.soup_change_weapon_staff)
        elif soup_exchange:
            self.soup_Routine.jump_to_state_by_name(self.soup_exchange_soup_routine_end)
        else:
            self.Log("Soup Count Matched - AutoStop")
            self.InternalStop()
      
  ### --- ROUTINE FUNCTIONS --- ###

def GetSoupCollected():
    return soup_Routine.GetSoupCollected() / 2.0

def GetSoupData():
    return soup_Routine.GetSoupStats()

soup_Window = Soup_Window(bot_name)
soup_Routine = Soup_Farm(soup_Window)

def ApplyLootAndMerchantSelections():
    global soup_input
    soup_Routine.ApplySelections(soup_input, soup_Window.id_Items, soup_Window.collect_coins, soup_Window.collect_events, soup_Window.collect_items_white, soup_Window.collect_items_blue, \
                soup_Window.collect_items_grape, soup_Window.collect_items_gold, soup_Window.collect_dye, soup_Window.sell_items, soup_Window.sell_items_white, \
                soup_Window.sell_items_blue, soup_Window.sell_items_grape, soup_Window.sell_items_gold, soup_Window.sell_items_green, soup_Window.sell_materials, soup_Window.salvage_items, soup_Window.salvage_items_white, \
                soup_Window.salvage_items_blue, soup_Window.salvage_items_grape, soup_Window.salvage_items_gold)

def ApplySoupConfigSettings(leave_party, soup_input, soup_exchange):
    soup_Routine.ApplyConfigSettingsOverride(leave_party, soup_input, soup_exchange)

def ApplySoupInventorySettings(min_slots, min_gold, depo_items, depo_mats):
    soup_Routine.ApplyInventorySettings(min_slots, min_gold, depo_items, depo_mats)

def StartBot():
    ApplyLootAndMerchantSelections()
    soup_Routine.Start()

def StopBot():
    if soup_Routine.IsBotRunning():
        soup_Routine.Stop()

def ResetBot():
    # Stop the main state machine  
    soup_Routine.Stop()
    soup_Routine.Reset()

def PrintData():
    soup_Routine.PrintData()

def GetRunTime():
    return soup_Routine.GetCurrentRunTime()

def GetAverageRunTime():
    return soup_Routine.GetAverageTime()

def GetTotalRunTime():
    return soup_Routine.GetTotalTime()

### --- MAIN --- ###
def main():
    try:
        if soup_Window:
            soup_Window.Show()

        # Could just put a main timer here and only fire the updates in some interval, but I like more control specific to tasks (eg. Staying Alive, Kill, Loot, etc)
        if Party.IsPartyLoaded():
            if soup_Routine and soup_Routine.IsBotRunning():
                soup_Routine.Update()
                
    except ImportError as e:
        Py4GW.Console.Log(bot_name, f"ImportError encountered: {str(e)}", Py4GW.Console.MessageType.Error)
        Py4GW.Console.Log(bot_name, f"Stack trace: {traceback.format_exc()}", Py4GW.Console.MessageType.Error)
    except ValueError as e:
        Py4GW.Console.Log(bot_name, f"ValueError encountered: {str(e)}", Py4GW.Console.MessageType.Error)
        Py4GW.Console.Log(bot_name, f"Stack trace: {traceback.format_exc()}", Py4GW.Console.MessageType.Error)
    except TypeError as e:
        Py4GW.Console.Log(bot_name, f"TypeError encountered: {str(e)}", Py4GW.Console.MessageType.Error)
        Py4GW.Console.Log(bot_name, f"Stack trace: {traceback.format_exc()}", Py4GW.Console.MessageType.Error)
    except Exception as e:
        Py4GW.Console.Log(bot_name, f"Unexpected error encountered: {str(e)}", Py4GW.Console.MessageType.Error)
        Py4GW.Console.Log(bot_name, f"Stack trace: {traceback.format_exc()}", Py4GW.Console.MessageType.Error)
    finally:
        pass

if __name__ == "__main__":
    main()

### -- MAIN -- ###