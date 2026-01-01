from Py4GWCoreLib import *
from BotUtilities import *
from WindowUtilites import *

import Mapping
import Enemies

bot_name = "Nikons Pahnai Salad Farm"

salad_selected = True
salad_exchange = False
salad_short_route = True
salad_input = 250

class Salad_Window(BasicWindow):
    global salad_selected, salad_input, salad_exchange
    
    salad_original_size = [350.0, 400.0]
    salad_explanded_size = [350.0, 475.0]
    minimum_slots = 5

    config_test_collect = salad_input
    config_test_farm = salad_selected
    config_test_exchange = salad_exchange

    def __init__(self, window_name="Basic Window", window_size = [350.0, 470.0], show_logger = True, show_state = True):
        super().__init__(window_name, window_size, show_logger, show_state)
        self.collect_coins = False
        self.collect_items_white = False
        self.collect_items_blue = False
        self.collect_items_grape = False
        self.sell_items_white = False
        self.sell_items_blue = False
        self.sell_items_grape = False
        self.sell_items_gold = False
        self.sell_materials = False

    def ShowMainControls(self):
        if PyImGui.collapsing_header("About - Farm Requirements"):
            PyImGui.begin_child("About_child_window", (0, 235), False, 0)
            PyImGui.text("- Dervish/Elementalist or Elementalist/Dervish")
            PyImGui.text("- Suggest Zealous Enchanting Scythe.")
            PyImGui.text("  \t*Droknars Reaper is perfect.")
            PyImGui.text("- Equip Scythe in Slot 2.")
            PyImGui.text("- Equip Staff in Slot 1 (not required).")
            PyImGui.text("- Inventory Snapshot Taken : Current Slots Safe.")
            PyImGui.text("- During salvage, saved slots are not touched.")
            PyImGui.text("- Moving items, you risk losing during sell.")
            PyImGui.text("- Just dont move items.")
            PyImGui.text("- Will not sell Iboga Petals, Rare Mats, Salv or Id kits.")
            PyImGui.text("- It takes 2 Iboga Petals per Salad.")
            PyImGui.end_child()
        PyImGui.separator()

    def ShowConfigSettingsTabItem(self):
        global salad_selected, salad_input, salad_exchange, salad_short_route

        if PyImGui.begin_table("Collect_Inputs", 2, PyImGui.TableFlags.SizingStretchProp):
            PyImGui.table_next_row()
            PyImGui.table_next_column()
            salad_selected = PyImGui.checkbox("Farm Iboga Petal Salad", salad_selected)  
            PyImGui.table_next_column()
            salad_input = PyImGui.input_int("# Salad", salad_input) if salad_input >= 0 else 0 
            PyImGui.table_next_row()
            PyImGui.table_next_column()
            salad_exchange = PyImGui.checkbox("Exchange Iboga Petals", salad_exchange)
            PyImGui.table_next_row()
            PyImGui.table_next_column()
            salad_short_route = PyImGui.checkbox("Short Route", salad_short_route)
            PyImGui.table_next_column()
            if salad_short_route:
                PyImGui.text_colored("~ 2-2.5 minutes", (0, 1, 0, 1))
            else:
                PyImGui.text_colored("~ 5 minutes", (1, 0, 0, 1))
            PyImGui.table_next_row()
            PyImGui.table_next_column()
            self.leave_party = PyImGui.checkbox("Leave Party", self.leave_party)
            PyImGui.end_table()

    def ShowResults(self):
        global salad_input

        PyImGui.separator()
        
        if PyImGui.collapsing_header("Results##Iboga Petals", int(PyImGui.TreeNodeFlags.DefaultOpen)):
            if PyImGui.begin_table("Runs_Results", 6):
                salad_data = GetSaladData()
                PyImGui.table_next_row()
                PyImGui.table_next_column()
                PyImGui.text(f"Runs:")
                PyImGui.table_next_column() 
                PyImGui.text(f"{salad_data[0]}")
                PyImGui.table_next_column() 
                PyImGui.text(f"Success: ")
                PyImGui.table_next_column()
                PyImGui.text_colored(f"{salad_data[1]}", (0, 1, 0, 1))
                PyImGui.table_next_column()
                PyImGui.text(f"Fails:")
                PyImGui.table_next_column()
                fails = salad_data[0] - salad_data[1]

                if fails > 0:
                    PyImGui.text_colored(f"{fails}", (1, 0, 0, 1))
                else:
                    PyImGui.text(f"{fails}")

                PyImGui.table_next_row()
                PyImGui.table_next_column()
                PyImGui.text("Salad:")
                PyImGui.table_next_column()
                salad_count = GetSaladCollected()
                if salad_selected and salad_input > 0 and salad_count == 0:            
                    PyImGui.text_colored(f"{salad_count}", (1, 0, 0, 1))
                else:
                    PyImGui.text_colored(f"{salad_count}", (0, 1, 0, 1))
                PyImGui.table_next_column()
                PyImGui.text(f"collected of")
                PyImGui.table_next_column()                
                PyImGui.text(f"{salad_input}")
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
        global salad_input, salad_exchange, salad_selected
        super().ApplyAndUpdateSettings()

        if self.config_test_collect != salad_input or \
            self.config_test_exchange != salad_exchange or \
            self.config_test_farm != salad_selected:
            self.ApplyConfigSettings()
    
            self.config_test_collect = salad_input
            self.config_test_farm = salad_selected
            self.config_test_exchange = salad_exchange

    def ApplyLootMerchantSettings(self) -> None:
        ApplyLootAndMerchantSelections()

    def ApplyConfigSettings(self) -> None:
        global salad_input, salad_exchange, salad_short_route
        ApplySaladConfigSettings(self.leave_party, salad_input, salad_exchange, salad_short_route)
        
    def ApplyInventorySettings(self) -> None:
        ApplySaladInventorySettings(self.minimum_slots, self.minimum_gold, self.depo_items, self.depo_mats)


    def GetSaladSettings(self):
        global salad_input

        return (salad_input, self.id_Items, self.collect_coins, self.collect_events, self.collect_items_white, self.collect_items_blue, \
                self.collect_items_grape, self.collect_items_gold, self.collect_dye, self.sell_items, self.sell_items_white, \
                self.sell_items_blue, self.sell_items_grape, self.sell_items_gold, self.sell_materials, self.salvage_items, self.salvage_items_white, \
                self.salvage_items_blue, self.salvage_items_grape, self.salvage_items_gold)
                
class Salad_Farm(ReportsProgress):
    class Salad_Skillbar:    
        def __init__(self):
            self.ride_lightning = SkillBar.GetSkillIDBySlot(1)
            self.ride_lightning_slot = 1
            self.zealous = SkillBar.GetSkillIDBySlot(2)
            self.zealous_slot = 2
            self.dstab = SkillBar.GetSkillIDBySlot(6)
            self.dstab_slot = 6
            self.drunkMaster = SkillBar.GetSkillIDBySlot(7)
            self.drunkMaster_slot = 7
            self.regen = SkillBar.GetSkillIDBySlot(8)
            self.regen_slot = 8

    # salad_Routine is the FSM instance
    salad_Routine = FSM("salad_Main")
    salad_Exchange_Routine = FSM("salad_Exchange")
    inventoryRoutine = InventoryFsm(None, None, 0, None, None)

    salad_primary_dervish_skillbar_code = "Ogakgwp5ayOERzFIAAAAAwdpqI7F"
    salad_primary_elementalist_skillbar_code = "Ogakgwp5ayOERD3HAAAAAwdpqI7F"

    salad_exchange_travel = "Salad- Exchange Travel Champions_Dawn"
    salad_exchange_wait_map = "Salad- Exchange Waiting Map"
    salad_exchange_move_to_collector = "Salad- Exchange Go to Chef"
    salad_exchange_target_collector = "Salad- Exchange Target"
    salad_exchange_interact_collector = "Salad- Exchange Interact"
    salad_exchange_do_exchange_all = "Salad- Exchange Salad"
    salad_exchange_salad_routine_start = "Salad- Go Exchange Salad 1"
    salad_exchange_salad_routine_end = "Salad- Go Exchange Salad 2"
    
    salad_start_farm = "Salad- Check Farm"
    salad_inventory_routine = "DoInventoryRoutine"
    salad_initial_check_inventory = "Salad- Inventory Check"
    salad_check_inventory_after_handle_inventory = "Salad- Inventory Handled?"
    salad_travel_state_name = "Salad- Traveling to Kamadan"
    salad_set_normal_mode = "Salad- Set Normal Mode"
    salad_leave_party_name = "Salad- Leave Party Check"
    salad_load_skillbar_state_name = "Salad- Load Skillbar"
    salad_pathing_1_state_name = "Salad- Leaving Outpost 1"
    salad_resign_pathing_state_name = "Salad- Setup Resign"
    salad_pathing_2_state_name = "Salad- Leaving Outpost 2"
    salad_waiting_map_state_name = "Salad- Farm Map Loading"
    salad_change_weapon_staff = "Salad- Change to Staff"
    salad_change_weapon_scythe = "Salad- Change to Scythe"
    salad_running_group_1 = "Salad- Move Group 1"
    salad_killing_group_1 = "Salad- Kill Group 1"
    salad_looting_group_1 = "Salad- Loot Group 1"
    salad_running_group_2 = "Salad- Move Group 2"
    salad_killing_group_2 = "Salad- Kill Group 2"
    salad_looting_group_2 = "Salad- Loot Group 2"
    salad_running_group_3 = "Salad- Move Group 3"
    salad_killing_group_3 = "Salad- Kill Group 3"
    salad_looting_group_3 = "Salad- Loot Group 3"
    salad_running_group_4 = "Salad- Move Group 4"
    salad_killing_group_4 = "Salad- Kill Group 4"
    salad_looting_group_4 = "Salad- Loot Group 4"
    salad_running_group_5 = "Salad- Move Group 5"
    salad_killing_group_5 = "Salad- Kill Group 5"
    salad_looting_group_5 = "Salad- Loot Group 5"
    salad_running_group_6 = "Salad- Move Group 6"
    salad_killing_group_6 = "Salad- Kill Group 6"
    salad_looting_group_6 = "Salad- Loot Group 6"
    salad_running_group_7 = "Salad- Move Group 7"
    salad_killing_group_7 = "Salad- Kill Group 7"
    salad_looting_group_7 = "Salad- Loot Group 7"
    salad_running_group_8 = "Salad- Move Group 8"
    salad_killing_group_8 = "Salad- Kill Group 8"
    salad_looting_group_8 = "Salad- Loot Group 8"
    salad_running_group_9 = "Salad- Move Group 9"
    salad_killing_group_9 = "Salad- Kill Group 9"
    salad_looting_group_9 = "Salad- Loot Group 9"
    salad_running_group_10 = "Salad- Move Group 10"
    salad_killing_group_10 = "Salad- Kill Group 10"
    salad_looting_group_10 = "Salad- Loot Group 10"
    salad_running_group_11 = "Salad- Move Group 11"
    salad_killing_group_11 = "Salad- Kill Group 11"
    salad_looting_group_11 = "Salad- Loot Group 11"
    salad_running_group_12 = "Salad- Move Group 12"
    salad_killing_group_12 = "Salad- Kill Group 12"
    salad_looting_group_12 = "Salad- Loot Group 12"
    salad_running_group_13 = "Salad- Move Group 13"
    salad_killing_group_13 = "Salad- Kill Group 13"
    salad_looting_group_13 = "Salad- Loot Group 13"
    salad_running_group_14 = "Salad- Move Group 14"
    salad_killing_group_14 = "Salad- Kill Group 14"
    salad_looting_group_14 = "Salad- Loot Group 14"
    salad_running_group_15 = "Salad- Move Group 15"
    salad_killing_group_15 = "Salad- Kill Group 15"
    salad_looting_group_15 = "Salad- Loot Group 15"
    salad_running_group_16 = "Salad- Move Group 16"
    salad_killing_group_16 = "Salad- Kill Group 16"
    salad_looting_group_16 = "Salad- Loot Group 16"
    salad_running_group_17 = "Salad- Move Group 17"
    salad_killing_group_17 = "Salad- Kill Group 17"
    salad_looting_group_17 = "Salad- Loot Group 17"
    salad_running_group_18 = "Salad- Move Group 18"
    salad_killing_group_18 = "Salad- Kill Group 18"
    salad_looting_group_18 = "Salad- Loot Group 18"
    salad_running_group_19 = "Salad- Move Group 19"
    salad_killing_group_19 = "Salad- Kill Group 19"
    salad_looting_group_19 = "Salad- Loot Group 19"
    salad_running_short_group_1 = "Salad- Move Short Group 1"
    salad_looting_short_group_1 = "Salad- Loot Short Group 1"
    salad_killing_short_group_1 = "Salad- Kill Short Group 1"
    salad_running_short_group_2 = "Salad- Move Short Group 2"
    salad_looting_short_group_2 = "Salad- Loot Short Group 2"
    salad_killing_short_group_2 = "Salad- Kill Short Group 2"
    salad_running_short_group_3 = "Salad- Move Short Group 3"
    salad_looting_short_group_3 = "Salad- Loot Short Group 3"
    salad_killing_short_group_3 = "Salad- Kill Short Group 3"
    salad_running_short_group_4 = "Salad- Move Short Group 4"
    salad_looting_short_group_4 = "Salad- Loot Short Group 4"
    salad_killing_short_group_4 = "Salad- Kill Short Group 4"
    salad_running_short_group_5 = "Salad- Move Short Group 5"
    salad_looting_short_group_5 = "Salad- Loot Short Group 5"
    salad_killing_short_group_5 = "Salad- Kill Short Group 5"
    salad_running_short_group_6 = "Salad- Move Short Group 6"
    salad_looting_short_group_6 = "Salad- Loot Short Group 6"
    salad_killing_short_group_6 = "Salad- Kill Short Group 6"
    salad_running_short_group_7 = "Salad- Move Short Group 7"
    salad_looting_short_group_7 = "Salad- Loot Short Group 7"
    salad_killing_short_group_7 = "Salad- Kill Short Group 7"
    salad_running_short_group_8 = "Salad- Move Short Group 8"
    salad_looting_short_group_8 = "Salad- Loot Short Group 8"
    salad_killing_short_group_8 = "Salad- Kill Short Group 8"
    salad_running_short_group_9 = "Salad- Move Short Group 9"
    salad_looting_short_group_9 = "Salad- Loot Short Group 9"
    salad_killing_short_group_9 = "Salad- Kill Short Group 9"
    salad_running_short_group_10 = "Salad- Move Short Group 10"
    salad_looting_short_group_10 = "Salad- Loot Short Group 10"
    salad_killing_short_group_10 = "Salad- Kill Short Group 10"
    salad_running_short_group_11 = "Salad- Move Short Group 11"
    salad_looting_short_group_11 = "Salad- Loot Short Group 11"
    salad_killing_short_group_11 = "Salad- Kill Short Group 11"
    salad_end_check_sink = "Salad- Check Run"
    salad_run_success = "Salad- Success Run"
    salad_resign_state_name = "Salad- Resigning"
    salad_wait_return_state_name = "Salad- Wait Return"
    salad_inventory_state_name = "Salad- Handle Inventory 1"
    salad_inventory_state_name_end = "Salad-Handle Inventory 2"
    salad_end_state_name = "Salad- End Routine"
    salad_forced_stop = "Salad- End Forced"
    salad_outpost_portal = [(-9053, 16088), (-9218, 16985)]#[(-92, -72), (-1599, -1007), (-2900, -1090)]
    salad_outpost_resign_pathing = [(18378, -1450)]#[(20020, 10900), (20472, 8784)]
    salad_outpost_post_resign_pathing = [(-9218, 16985)]#[(-2900, -1090)]
    salad_merchant_position = [(-10372, 15269)]#[(1045, 218),(2809, 2026), (3219, 2257)]
    salad_running_group_1_path = [(17613, -22), (15167, 555)]
    salad_running_group_2_path = [(10110, -3254)]
    salad_running_group_3_path = [(11715, -4855), (11576, -6633)]
    salad_running_group_4_path = [(8814, -9355), (5058, -11212)]
    salad_running_group_5_path = [(2809, -9783), (1893, -9548)]
    salad_running_group_6_path = [(-344, -9709)]
    salad_running_group_7_path = [(-326, -7460)]
    salad_running_group_8_path = [(-73, -3765), (-71, -149)]
    salad_running_group_9_path = [(2452, 6867), (4999, 14081)]
    salad_running_group_10_path = [(3820, 15448)]
    salad_running_group_11_path = [(7202, 14842)]
    salad_running_group_12_path = [(7953, 17083)]
    salad_running_group_13_path = [(9050, 15491)]
    salad_running_group_14_path = [(9877, 13433)]
    salad_running_group_15_path = [(15744, 7853)]
    salad_running_group_16_path = [(13103, 7050)]
    salad_running_group_17_path = [(13631, 4017)]
    salad_running_group_18_path = [(13029, 1698)]
    salad_running_group_19_path = [(10625, 1051)]
    salad_running_cross_to_group_9 = [(5046, 14112)]
    salad_pathing_portal_only_handler_1 = Routines.Movement.PathHandler(salad_outpost_portal)
    salad_pathing_portal_only_handler_2 = Routines.Movement.PathHandler(salad_outpost_post_resign_pathing)
    salad_pathing_resign_portal_handler = Routines.Movement.PathHandler(salad_outpost_resign_pathing)
    salad_pathing_group_1 = Routines.Movement.PathHandler(salad_running_group_1_path)
    salad_pathing_group_2 = Routines.Movement.PathHandler(salad_running_group_2_path)
    salad_pathing_group_3 = Routines.Movement.PathHandler(salad_running_group_3_path)
    salad_pathing_group_4 = Routines.Movement.PathHandler(salad_running_group_4_path)
    salad_pathing_group_5 = Routines.Movement.PathHandler(salad_running_group_5_path)
    salad_pathing_group_6 = Routines.Movement.PathHandler(salad_running_group_6_path)
    salad_pathing_group_7 = Routines.Movement.PathHandler(salad_running_group_7_path)
    salad_pathing_group_8 = Routines.Movement.PathHandler(salad_running_group_8_path)
    salad_pathing_group_9 = Routines.Movement.PathHandler(salad_running_group_9_path)
    salad_pathing_group_10 = Routines.Movement.PathHandler(salad_running_group_10_path)
    salad_pathing_group_11 = Routines.Movement.PathHandler(salad_running_group_11_path)
    salad_pathing_group_12 = Routines.Movement.PathHandler(salad_running_group_12_path)
    salad_pathing_group_13 = Routines.Movement.PathHandler(salad_running_group_13_path)
    salad_pathing_group_14 = Routines.Movement.PathHandler(salad_running_group_14_path)
    salad_pathing_group_15 = Routines.Movement.PathHandler(salad_running_group_15_path)
    salad_pathing_group_16 = Routines.Movement.PathHandler(salad_running_group_16_path)
    salad_pathing_group_17 = Routines.Movement.PathHandler(salad_running_group_17_path)
    salad_pathing_group_18 = Routines.Movement.PathHandler(salad_running_group_18_path)
    salad_pathing_group_19 = Routines.Movement.PathHandler(salad_running_group_19_path)
    salad_pathing_group_20 = Routines.Movement.PathHandler(salad_running_cross_to_group_9)
    
    salad_exchange_pathing = [(23896, 9244), (23507, 11446)]
    salad_exchange_pathing_handler = Routines.Movement.PathHandler(salad_exchange_pathing)
    exchange_movement_Handler = Routines.Movement.FollowXY(50)
    portal_movement_Handler = Routines.Movement.FollowXY(50)
    resign_movement_Handler = Routines.Movement.FollowXY(50)
    post_resign_movement_Handler = Routines.Movement.FollowXY(50)
    running_movement_Handler = Routines.Movement.FollowXY(50)
    cross_over_movement_Handler = Routines.Movement.FollowXY(50)
    
    keep_list = []
    keep_list.extend(IdSalveItems_Array)
    keep_list.extend(EventItems_Array)
    keep_list.append(ModelID.Iboga_Petal)
    keep_list.append(ModelID.Vial_Of_Dye)

    enemy_list = [Enemies.Fanged_Iboga_Smallest, Enemies.Fanged_Iboga_Small]
    
    salad_first_after_reset = False
    salad_wait_to_kill = False
    salad_ready_to_kill = False
    salad_killing_staggering_casted = False
    salad_killing_eremites_casted = False
    salad_exchange = False
    salad_short_route = True

    player_stuck_hos_count = 0
    player_skillbar_load_count = 0
    player_previous_hp = 100

    weapon_slot_staff = 1
    weapon_slot_scythe = 2
    salad_collected = 0
    add_koss_tries = 0
    current_lootable = 0
    current_loot_tries = 0
    current_run_time = 0
    average_run_time = 0
    default_min_slots = 5
    average_run_history = []
    
    salad_runs = 0
    salad_success = 0
    salad_fails = 0
    
    second_timer_elapsed = 1000
    loot_timer_elapsed = 1000
    
    pyParty = PyParty.PyParty()
    pyMerchant = PyMerchant.PyMerchant()
    salad_exchange_timer = Timer()
    salad_second_timer = Timer()
    salad_step_done_timer = Timer()
    salad_stuck_timer = Timer()
    salad_loot_timer = Timer()
    salad_loot_done_timer = Timer()
    salad_stay_alive_timer = Timer()

    stuckPosition = []

    ### --- SETUP --- ###
    def __init__(self, window):
        self.current_inventory = GetInventoryItemSlots()

        super().__init__(window, Mapping.Kamadan, self.salad_merchant_position, self.current_inventory, self.keep_list)
        
        # Iboga Petal Exchange Sub Routine
        self.salad_Exchange_Routine.AddState(self.salad_exchange_travel,
                                             execute_fn=lambda: self.ExecuteStep(self.salad_exchange_travel, Routines.Transition.TravelToOutpost(Mapping.Champions_Dawn)),
                                             exit_condition=lambda: Routines.Transition.HasArrivedToOutpost(Mapping.Champions_Dawn),
                                             transition_delay_ms=1000)
        self.salad_Exchange_Routine.AddState(self.salad_exchange_move_to_collector,
                                             execute_fn=lambda: self.ExecuteStep(self.salad_exchange_move_to_collector, Routines.Movement.FollowPath(self.salad_exchange_pathing_handler, self.exchange_movement_Handler)),
                                             exit_condition=lambda: Routines.Movement.IsFollowPathFinished(self.salad_exchange_pathing_handler, self.exchange_movement_Handler),
                                             run_once=False)
        
        self.salad_Exchange_Routine.AddState(name=self.salad_exchange_target_collector,
                                             execute_fn=lambda: self.ExecuteStep(self.salad_exchange_target_collector, TargetNearestNpc()),
                                             transition_delay_ms=1000)
        
        self.salad_Exchange_Routine.AddState(name=self.salad_exchange_interact_collector,
                                             execute_fn=lambda: self.ExecuteStep(self.salad_exchange_interact_collector, Routines.Targeting.InteractTarget()),
                                             exit_condition=lambda: Routines.Targeting.HasArrivedToTarget() or GetDistance(Player.GetAgentID(), Player.GetTargetID()) < GameAreas.Area)
        
        self.salad_Exchange_Routine.AddState(name=self.salad_exchange_do_exchange_all,
                                             execute_fn=lambda: self.ExecuteStep(self.salad_exchange_do_exchange_all, self.ExchangeSalads()),
                                             exit_condition=lambda: self.ExchangeSaladsDone(), 
                                             run_once=False)
        # Iboga Petal Exchange Sub Routine
        
        # Salad Farm Main Routine
        self.salad_Routine.AddSubroutine(self.salad_exchange_salad_routine_start,
                       sub_fsm=self.salad_Exchange_Routine,
                       condition_fn=lambda: self.CheckExchangeSalads() and CheckIfInventoryHasItem(ModelID.Iboga_Petal))        
        self.salad_Routine.AddState(self.salad_start_farm,
                                    execute_fn=lambda: self.ExecuteStep(self.salad_start_farm, self.CheckIfShouldRunFarm()))
        self.salad_Routine.AddState(self.salad_travel_state_name,
                       execute_fn=lambda: self.ExecuteStep(self.salad_travel_state_name, Routines.Transition.TravelToOutpost(Mapping.Kamadan)),
                       exit_condition=lambda: Routines.Transition.HasArrivedToOutpost(Mapping.Kamadan),
                       transition_delay_ms=1000)
        self.salad_Routine.AddState(self.salad_initial_check_inventory, execute_fn=lambda: self.CheckInventory())
        self.salad_Routine.AddState(self.salad_set_normal_mode,
                       execute_fn=lambda: self.ExecuteStep(self.salad_set_normal_mode, self.InternalStart()),
                       transition_delay_ms=1000)
        self.salad_Routine.AddState(self.salad_leave_party_name,
                       execute_fn=lambda: self.ExecuteStep(self.salad_leave_party_name, Party.LeaveParty() if self.leave_party else None), # Ensure only one hero in party
                       transition_delay_ms=1000)
        self.salad_Routine.AddState(self.salad_load_skillbar_state_name,
                       execute_fn=lambda: self.ExecuteStep(self.salad_load_skillbar_state_name, self.LoadSkillBar()), # Ensure only one hero in party                       
                       exit_condition=lambda: self.IsSkillBarLoaded(),
                       transition_delay_ms=1500)
        self.salad_Routine.AddState(self.salad_pathing_1_state_name,
                       execute_fn=lambda: self.ExecuteStep(self.salad_pathing_1_state_name, Routines.Movement.FollowPath(self.salad_pathing_portal_only_handler_1, self.portal_movement_Handler)),
                       exit_condition=lambda: (Map.GetMapID() == Mapping.Plains_Of_Jarin and Party.IsPartyLoaded()),
                       run_once=False)
        self.salad_Routine.AddState(self.salad_resign_pathing_state_name,
                       execute_fn=lambda: self.ExecuteStep(self.salad_resign_pathing_state_name, Routines.Movement.FollowPath(self.salad_pathing_resign_portal_handler, self.resign_movement_Handler)),
                       exit_condition=lambda: (Map.GetMapID() == Mapping.Kamadan and Party.IsPartyLoaded()),
                       run_once=False)
        self.salad_Routine.AddSubroutine(self.salad_inventory_state_name,
                       sub_fsm = self.inventoryRoutine, # dont add execute function wrapper here
                       condition_fn=lambda: not self.salad_first_after_reset and Inventory.GetFreeSlotCount() <= self.default_min_slots)
        self.salad_Routine.AddState(self.salad_check_inventory_after_handle_inventory, execute_fn=lambda: self.CheckInventory())
        
        # Switch back n forth between staff/scythe to ensure have enough energy at each point.  
        self.salad_Routine.AddState(self.salad_change_weapon_staff,
                       execute_fn=lambda: self.ExecuteStep(self.salad_change_weapon_staff, self.RunStarting()),
                       transition_delay_ms=1000)
        self.salad_Routine.AddState(self.salad_pathing_2_state_name,
                       execute_fn=lambda: self.ExecuteStep(self.salad_pathing_2_state_name, Routines.Movement.FollowPath(self.salad_pathing_portal_only_handler_2, self.post_resign_movement_Handler)),
                       exit_condition=lambda: Map.GetMapID() == Mapping.Plains_Of_Jarin,
                       run_once=False)
        self.salad_Routine.AddState(self.salad_waiting_map_state_name,
                       execute_fn=lambda: self.ExecuteStep(self.salad_waiting_map_state_name, Routines.Transition.IsExplorableLoaded()),
                       transition_delay_ms=1000)
        
        ### === BELOW HERE IS RUN > FIGHT > LOOT LOOP === ###
        ### FIRST GROUP ###
        self.salad_Routine.AddState(self.salad_running_group_1,
                       execute_fn=lambda: self.ExecuteTimedStep(self.salad_running_group_1, self.TimeToRunToGroup(self.salad_pathing_group_1, self.running_movement_Handler)),
                       exit_condition=lambda: self.RunToGroupDone(self.salad_pathing_group_1, self.running_movement_Handler),
                       run_once=False)
        self.salad_Routine.AddState(self.salad_change_weapon_scythe,
                       execute_fn=lambda: self.ExecuteStep(self.salad_change_weapon_scythe, ChangeWeaponSet(self.weapon_slot_scythe)),
                       transition_delay_ms=1000)
        self.salad_Routine.AddState(self.salad_killing_group_1,
                       execute_fn=lambda: self.ExecuteTimedStep(self.salad_killing_group_1, self.KillLoopStart()),
                       exit_condition=lambda: self.KillLoopComplete(),
                       run_once=False)
        self.salad_Routine.AddState(self.salad_looting_group_1,
                       execute_fn=lambda: self.ExecuteTimedStep(self.salad_looting_group_1, self.LootLoopStart()),
                       exit_condition=lambda: self.CheckFirstGroupComplete(),
                       run_once=False)
        ### FIRST GROUP ###
        ### SECOND GROUP ###        
        self.salad_Routine.AddState(self.salad_running_group_2,
                       execute_fn=lambda: self.ExecuteTimedStep(self.salad_running_group_2, self.TimeToRunToGroup(self.salad_pathing_group_2, self.running_movement_Handler)),
                       exit_condition=lambda: self.RunToGroupDone(self.salad_pathing_group_2, self.running_movement_Handler),
                       run_once=False)
        self.salad_Routine.AddState(self.salad_killing_group_2,
                       execute_fn=lambda: self.ExecuteTimedStep(self.salad_killing_group_2, self.KillLoopStart()),
                       exit_condition=lambda: self.KillLoopComplete(),
                       run_once=False)
        self.salad_Routine.AddState(self.salad_looting_group_2,
                       execute_fn=lambda: self.ExecuteTimedStep(self.salad_looting_group_2, self.LootLoopStart()),
                       exit_condition=lambda: self.LootLoopComplete() or self.ShouldForceTransitionStep(),
                       run_once=False)
        ### SECOND GROUP ###
        ### THIRD GROUP ###        
        self.salad_Routine.AddState(self.salad_running_group_3,
                       execute_fn=lambda: self.ExecuteTimedStep(self.salad_running_group_3, self.TimeToRunToGroup(self.salad_pathing_group_3, self.running_movement_Handler)),
                       exit_condition=lambda: self.RunToGroupDone(self.salad_pathing_group_3, self.running_movement_Handler),
                       run_once=False)
        self.salad_Routine.AddState(self.salad_killing_group_3,
                       execute_fn=lambda: self.ExecuteTimedStep(self.salad_killing_group_3, self.KillLoopStart()),
                       exit_condition=lambda: self.KillLoopComplete(),
                       run_once=False)
        self.salad_Routine.AddState(self.salad_looting_group_3,
                       execute_fn=lambda: self.ExecuteTimedStep(self.salad_looting_group_3, self.LootLoopStart()),
                       exit_condition=lambda: self.LootLoopComplete() or self.ShouldForceTransitionStep(),
                       run_once=False)
        ### THIRD GROUP ###
        ### FOURTH GROUP ###        
        self.salad_Routine.AddState(self.salad_running_group_4,
                       execute_fn=lambda: self.ExecuteTimedStep(self.salad_running_group_4, self.TimeToRunToGroup(self.salad_pathing_group_4, self.running_movement_Handler)),
                       exit_condition=lambda: self.RunToGroupDone(self.salad_pathing_group_4, self.running_movement_Handler),
                       run_once=False)
        self.salad_Routine.AddState(self.salad_killing_group_4,
                       execute_fn=lambda: self.ExecuteTimedStep(self.salad_killing_group_4, self.KillLoopStart()),
                       exit_condition=lambda: self.KillLoopComplete(),
                       run_once=False)
        self.salad_Routine.AddState(self.salad_looting_group_4,
                       execute_fn=lambda: self.ExecuteTimedStep(self.salad_looting_group_4, self.LootLoopStart()),
                       exit_condition=lambda: self.LootLoopComplete() or self.ShouldForceTransitionStep(),
                       run_once=False)
        ### FOURTH GROUP ###
        ### FIFTH GROUP ###        
        self.salad_Routine.AddState(self.salad_running_group_5,
                       execute_fn=lambda: self.ExecuteTimedStep(self.salad_running_group_5, self.TimeToRunToGroup(self.salad_pathing_group_5, self.running_movement_Handler)),
                       exit_condition=lambda: self.RunToGroupDone(self.salad_pathing_group_5, self.running_movement_Handler),
                       run_once=False)
        self.salad_Routine.AddState(self.salad_killing_group_5,
                       execute_fn=lambda: self.ExecuteTimedStep(self.salad_killing_group_5, self.KillLoopStart()),
                       exit_condition=lambda: self.KillLoopComplete(),
                       run_once=False)
        self.salad_Routine.AddState(self.salad_looting_group_5,
                       execute_fn=lambda: self.ExecuteTimedStep(self.salad_looting_group_5, self.LootLoopStart()),
                       exit_condition=lambda: self.LootLoopComplete() or self.ShouldForceTransitionStep(),
                       run_once=False)
        ### FIFTH GROUP ###
        ### SIXTH GROUP ###        
        self.salad_Routine.AddState(self.salad_running_group_6,
                       execute_fn=lambda: self.ExecuteTimedStep(self.salad_running_group_6, self.TimeToRunToGroup(self.salad_pathing_group_6, self.running_movement_Handler)),
                       exit_condition=lambda: self.RunToGroupDone(self.salad_pathing_group_6, self.running_movement_Handler),
                       run_once=False)
        self.salad_Routine.AddState(self.salad_killing_group_6,
                       execute_fn=lambda: self.ExecuteTimedStep(self.salad_killing_group_6, self.KillLoopStart()),
                       exit_condition=lambda: self.KillLoopComplete(),
                       run_once=False)
        self.salad_Routine.AddState(self.salad_looting_group_6,
                       execute_fn=lambda: self.ExecuteTimedStep(self.salad_looting_group_6, self.LootLoopStart()),
                       exit_condition=lambda: self.LootLoopComplete() or self.ShouldForceTransitionStep(),
                       run_once=False)
        ### SIXTH GROUP ###
        ### SEVENTH GROUP ###        
        self.salad_Routine.AddState(self.salad_running_group_7,
                       execute_fn=lambda: self.ExecuteTimedStep(self.salad_running_group_7, self.TimeToRunToGroup(self.salad_pathing_group_7, self.running_movement_Handler)),
                       exit_condition=lambda: self.RunToGroupDone(self.salad_pathing_group_7, self.running_movement_Handler),
                       run_once=False)
        self.salad_Routine.AddState(self.salad_killing_group_7,
                       execute_fn=lambda: self.ExecuteTimedStep(self.salad_killing_group_7, self.KillLoopStart()),
                       exit_condition=lambda: self.KillLoopComplete(),
                       run_once=False)
        self.salad_Routine.AddState(self.salad_looting_group_7,
                       execute_fn=lambda: self.ExecuteTimedStep(self.salad_looting_group_7, self.LootLoopStart()),
                       exit_condition=lambda: self.LootLoopComplete() or self.ShouldForceTransitionStep(),
                       run_once=False)
        ### SEVENTH GROUP ###
        ### EIGTH GROUP ###        
        self.salad_Routine.AddState(self.salad_running_group_8,
                       execute_fn=lambda: self.ExecuteTimedStep(self.salad_running_group_8, self.TimeToRunToGroup(self.salad_pathing_group_8, self.running_movement_Handler)),
                       exit_condition=lambda: self.RunToGroupDone(self.salad_pathing_group_8, self.running_movement_Handler),
                       run_once=False)
        self.salad_Routine.AddState(self.salad_killing_group_8,
                       execute_fn=lambda: self.ExecuteTimedStep(self.salad_killing_group_8, self.KillLoopStart()),
                       exit_condition=lambda: self.KillLoopComplete(),
                       run_once=False)
        self.salad_Routine.AddState(self.salad_looting_group_8,
                       execute_fn=lambda: self.ExecuteTimedStep(self.salad_looting_group_8, self.LootLoopStart()),
                       exit_condition=lambda: self.LootLoopComplete() or self.ShouldForceTransitionStep(),
                       run_once=False)
        ### EIGTH GROUP ###
        ### NINTH GROUP ###        
        self.salad_Routine.AddState(self.salad_running_group_9,
                       execute_fn=lambda: self.ExecuteTimedStep(self.salad_running_group_9, self.TimeToRunToGroup(self.salad_pathing_group_9, self.running_movement_Handler)),
                       exit_condition=lambda: self.RunToGroupDone(self.salad_pathing_group_9, self.running_movement_Handler),
                       run_once=False)
        self.salad_Routine.AddState(self.salad_killing_group_9,
                       execute_fn=lambda: self.ExecuteTimedStep(self.salad_killing_group_9, self.KillLoopStart()),
                       exit_condition=lambda: self.KillLoopComplete(),
                       run_once=False)
        self.salad_Routine.AddState(self.salad_looting_group_9,
                       execute_fn=lambda: self.ExecuteTimedStep(self.salad_looting_group_9, self.LootLoopStart()),
                       exit_condition=lambda: self.LootLoopComplete() or self.ShouldForceTransitionStep(),
                       run_once=False)
        ### NINTH GROUP ###        
        ### TENTH GROUP ###        
        self.salad_Routine.AddState(self.salad_running_group_10,
                       execute_fn=lambda: self.ExecuteTimedStep(self.salad_running_group_10, self.TimeToRunToGroup(self.salad_pathing_group_10, self.running_movement_Handler)),
                       exit_condition=lambda: self.RunToGroupDone(self.salad_pathing_group_10, self.running_movement_Handler),
                       run_once=False)
        self.salad_Routine.AddState(self.salad_killing_group_10,
                       execute_fn=lambda: self.ExecuteTimedStep(self.salad_killing_group_10, self.KillLoopStart()),
                       exit_condition=lambda: self.KillLoopComplete(),
                       run_once=False)
        self.salad_Routine.AddState(self.salad_looting_group_10,
                       execute_fn=lambda: self.ExecuteTimedStep(self.salad_looting_group_10, self.LootLoopStart()),
                       exit_condition=lambda: self.LootLoopComplete() or self.ShouldForceTransitionStep(),
                       run_once=False)
        ### TENTH GROUP ###        
        ### ELEVENTH GROUP ###        
        self.salad_Routine.AddState(self.salad_running_group_11,
                       execute_fn=lambda: self.ExecuteTimedStep(self.salad_running_group_11, self.TimeToRunToGroup(self.salad_pathing_group_11, self.running_movement_Handler)),
                       exit_condition=lambda: self.RunToGroupDone(self.salad_pathing_group_11, self.running_movement_Handler),
                       run_once=False)
        self.salad_Routine.AddState(self.salad_killing_group_11,
                       execute_fn=lambda: self.ExecuteTimedStep(self.salad_killing_group_11, self.KillLoopStart()),
                       exit_condition=lambda: self.KillLoopComplete(),
                       run_once=False)
        self.salad_Routine.AddState(self.salad_looting_group_11,
                       execute_fn=lambda: self.ExecuteTimedStep(self.salad_looting_group_11, self.LootLoopStart()),
                       exit_condition=lambda: self.LootLoopComplete() or self.ShouldForceTransitionStep(),
                       run_once=False)
        ### ELEVENTH GROUP ###        
        ### TWELFTH GROUP ###        
        self.salad_Routine.AddState(self.salad_running_group_12,
                       execute_fn=lambda: self.ExecuteTimedStep(self.salad_running_group_12, self.TimeToRunToGroup(self.salad_pathing_group_12, self.running_movement_Handler)),
                       exit_condition=lambda: self.RunToGroupDone(self.salad_pathing_group_12, self.running_movement_Handler),
                       run_once=False)
        self.salad_Routine.AddState(self.salad_killing_group_12,
                       execute_fn=lambda: self.ExecuteTimedStep(self.salad_killing_group_12, self.KillLoopStart()),
                       exit_condition=lambda: self.KillLoopComplete(),
                       run_once=False)
        self.salad_Routine.AddState(self.salad_looting_group_12,
                       execute_fn=lambda: self.ExecuteTimedStep(self.salad_looting_group_12, self.LootLoopStart()),
                       exit_condition=lambda: self.LootLoopComplete() or self.ShouldForceTransitionStep(),
                       run_once=False)
        ### TWELFTH GROUP ###       
        ### 13 GROUP ###        
        self.salad_Routine.AddState(self.salad_running_group_13,
                       execute_fn=lambda: self.ExecuteTimedStep(self.salad_running_group_13, self.TimeToRunToGroup(self.salad_pathing_group_13, self.running_movement_Handler)),
                       exit_condition=lambda: self.RunToGroupDone(self.salad_pathing_group_13, self.running_movement_Handler),
                       run_once=False)
        self.salad_Routine.AddState(self.salad_killing_group_13,
                       execute_fn=lambda: self.ExecuteTimedStep(self.salad_killing_group_13, self.KillLoopStart()),
                       exit_condition=lambda: self.KillLoopComplete(),
                       run_once=False)
        self.salad_Routine.AddState(self.salad_looting_group_13,
                       execute_fn=lambda: self.ExecuteTimedStep(self.salad_looting_group_13, self.LootLoopStart()),
                       exit_condition=lambda: self.LootLoopComplete() or self.ShouldForceTransitionStep(),
                       run_once=False)
        ### 13 GROUP ###       
        ### 14 GROUP ###        
        self.salad_Routine.AddState(self.salad_running_group_14,
                       execute_fn=lambda: self.ExecuteTimedStep(self.salad_running_group_14, self.TimeToRunToGroup(self.salad_pathing_group_14, self.running_movement_Handler)),
                       exit_condition=lambda: self.RunToGroupDone(self.salad_pathing_group_14, self.running_movement_Handler),
                       run_once=False)
        self.salad_Routine.AddState(self.salad_killing_group_14,
                       execute_fn=lambda: self.ExecuteTimedStep(self.salad_killing_group_14, self.KillLoopStart()),
                       exit_condition=lambda: self.KillLoopComplete(),
                       run_once=False)
        self.salad_Routine.AddState(self.salad_looting_group_14,
                       execute_fn=lambda: self.ExecuteTimedStep(self.salad_looting_group_14, self.LootLoopStart()),
                       exit_condition=lambda: self.LootLoopComplete() or self.ShouldForceTransitionStep(),
                       run_once=False)
        ### 14 GROUP ###       
        ### 15 GROUP ###        
        self.salad_Routine.AddState(self.salad_running_group_15,
                       execute_fn=lambda: self.ExecuteTimedStep(self.salad_running_group_15, self.TimeToRunToGroup(self.salad_pathing_group_15, self.running_movement_Handler)),
                       exit_condition=lambda: self.RunToGroupDone(self.salad_pathing_group_15, self.running_movement_Handler),
                       run_once=False)
        self.salad_Routine.AddState(self.salad_killing_group_15,
                       execute_fn=lambda: self.ExecuteTimedStep(self.salad_killing_group_15, self.KillLoopStart()),
                       exit_condition=lambda: self.KillLoopComplete(),
                       run_once=False)
        self.salad_Routine.AddState(self.salad_looting_group_15,
                       execute_fn=lambda: self.ExecuteTimedStep(self.salad_looting_group_15, self.LootLoopStart()),
                       exit_condition=lambda: self.LootLoopComplete() or self.ShouldForceTransitionStep(),
                       run_once=False)
        ### 15 GROUP ###       
        ### 16 GROUP ###        
        self.salad_Routine.AddState(self.salad_running_group_16,
                       execute_fn=lambda: self.ExecuteTimedStep(self.salad_running_group_16, self.TimeToRunToGroup(self.salad_pathing_group_16, self.running_movement_Handler)),
                       exit_condition=lambda: self.RunToGroupDone(self.salad_pathing_group_16, self.running_movement_Handler),
                       run_once=False)
        self.salad_Routine.AddState(self.salad_killing_group_16,
                       execute_fn=lambda: self.ExecuteTimedStep(self.salad_killing_group_16, self.KillLoopStart()),
                       exit_condition=lambda: self.KillLoopComplete(),
                       run_once=False)
        self.salad_Routine.AddState(self.salad_looting_group_16,
                       execute_fn=lambda: self.ExecuteTimedStep(self.salad_looting_group_16, self.LootLoopStart()),
                       exit_condition=lambda: self.LootLoopComplete() or self.ShouldForceTransitionStep(),
                       run_once=False)
        ### 16 GROUP ###       
        ### 17 GROUP ###        
        self.salad_Routine.AddState(self.salad_running_group_17,
                       execute_fn=lambda: self.ExecuteTimedStep(self.salad_running_group_17, self.TimeToRunToGroup(self.salad_pathing_group_17, self.running_movement_Handler)),
                       exit_condition=lambda: self.RunToGroupDone(self.salad_pathing_group_17, self.running_movement_Handler),
                       run_once=False)
        self.salad_Routine.AddState(self.salad_killing_group_17,
                       execute_fn=lambda: self.ExecuteTimedStep(self.salad_killing_group_17, self.KillLoopStart()),
                       exit_condition=lambda: self.KillLoopComplete(),
                       run_once=False)
        self.salad_Routine.AddState(self.salad_looting_group_17,
                       execute_fn=lambda: self.ExecuteTimedStep(self.salad_looting_group_17, self.LootLoopStart()),
                       exit_condition=lambda: self.LootLoopComplete() or self.ShouldForceTransitionStep(),
                       run_once=False)
        ### 17 GROUP ###       
        ### 18 GROUP ###        
        self.salad_Routine.AddState(self.salad_running_group_18,
                       execute_fn=lambda: self.ExecuteTimedStep(self.salad_running_group_18, self.TimeToRunToGroup(self.salad_pathing_group_18, self.running_movement_Handler)),
                       exit_condition=lambda: self.RunToGroupDone(self.salad_pathing_group_18, self.running_movement_Handler),
                       run_once=False)
        self.salad_Routine.AddState(self.salad_killing_group_18,
                       execute_fn=lambda: self.ExecuteTimedStep(self.salad_killing_group_18, self.KillLoopStart()),
                       exit_condition=lambda: self.KillLoopComplete(),
                       run_once=False)
        self.salad_Routine.AddState(self.salad_looting_group_18,
                       execute_fn=lambda: self.ExecuteTimedStep(self.salad_looting_group_18, self.LootLoopStart()),
                       exit_condition=lambda: self.LootLoopComplete() or self.ShouldForceTransitionStep(),
                       run_once=False)
        ### 18 GROUP ###       
        ### 19 GROUP ###        
        self.salad_Routine.AddState(self.salad_running_group_19,
                       execute_fn=lambda: self.ExecuteTimedStep(self.salad_running_group_19, self.TimeToRunToGroup(self.salad_pathing_group_19, self.running_movement_Handler)),
                       exit_condition=lambda: self.RunToGroupDone(self.salad_pathing_group_19, self.running_movement_Handler),
                       run_once=False)
        self.salad_Routine.AddState(self.salad_killing_group_19,
                       execute_fn=lambda: self.ExecuteTimedStep(self.salad_killing_group_19, self.KillLoopStart()),
                       exit_condition=lambda: self.KillLoopComplete(),
                       run_once=False)
        self.salad_Routine.AddState(self.salad_looting_group_19,
                       execute_fn=lambda: self.ExecuteTimedStep(self.salad_looting_group_19, self.LootLoopStart()),
                       exit_condition=lambda: self.CheckLastGroupComplete(),
                       run_once=False)
        ### 19 GROUP ###
        ### === ABOVE HERE IS RUN > FIGHT > LOOT LOOP === ###

        ### === BELOW HERE IS SHORT LOOP RUN > FIGHT > LOOT LOOP === ###
        ### 18 or 1 SHORT GROUP ###
        self.salad_Routine.AddState(self.salad_running_short_group_1,
                       execute_fn=lambda: self.ExecuteTimedStep(self.salad_running_short_group_1, self.TimeToRunToGroup(self.salad_pathing_group_18, self.running_movement_Handler)),
                       exit_condition=lambda: self.RunToGroupDone(self.salad_pathing_group_18, self.running_movement_Handler),
                       run_once=False)
        self.salad_Routine.AddState(self.salad_killing_short_group_1,
                       execute_fn=lambda: self.ExecuteTimedStep(self.salad_killing_short_group_1, self.KillLoopStart()),
                       exit_condition=lambda: self.KillLoopComplete(),
                       run_once=False)
        self.salad_Routine.AddState(self.salad_looting_short_group_1,
                       execute_fn=lambda: self.ExecuteTimedStep(self.salad_looting_short_group_1, self.LootLoopStart()),
                       exit_condition=lambda: self.LootLoopComplete() or self.ShouldForceTransitionStep(),
                       run_once=False)
        ### 18 or 1 SHORT GROUP ###
        ### 19 or 2 SHORT GROUP ###        
        self.salad_Routine.AddState(self.salad_running_short_group_2,
                       execute_fn=lambda: self.ExecuteTimedStep(self.salad_running_short_group_2, self.TimeToRunToGroup(self.salad_pathing_group_19, self.running_movement_Handler)),
                       exit_condition=lambda: self.RunToGroupDone(self.salad_pathing_group_19, self.running_movement_Handler),
                       run_once=False)
        self.salad_Routine.AddState(self.salad_killing_short_group_2,
                       execute_fn=lambda: self.ExecuteTimedStep(self.salad_killing_short_group_2, self.KillLoopStart()),
                       exit_condition=lambda: self.KillLoopComplete(),
                       run_once=False)
        self.salad_Routine.AddState(self.salad_looting_short_group_2,
                       execute_fn=lambda: self.ExecuteTimedStep(self.salad_looting_short_group_2, self.LootLoopStart()),
                       exit_condition=lambda: self.LootLoopComplete() or self.ShouldForceTransitionStep(),
                       run_once=False)
        ### 19 or 2 SHORT GROUP ###
        ### 17 or 3 SHORT GROUP ###
        self.salad_Routine.AddState(self.salad_running_short_group_3,
                       execute_fn=lambda: self.ExecuteTimedStep(self.salad_running_short_group_3, self.TimeToRunToGroup(self.salad_pathing_group_17, self.running_movement_Handler)),
                       exit_condition=lambda: self.RunToGroupDone(self.salad_pathing_group_17, self.running_movement_Handler),
                       run_once=False)
        self.salad_Routine.AddState(self.salad_killing_short_group_3,
                       execute_fn=lambda: self.ExecuteTimedStep(self.salad_killing_short_group_3, self.KillLoopStart()),
                       exit_condition=lambda: self.KillLoopComplete(),
                       run_once=False)
        self.salad_Routine.AddState(self.salad_looting_short_group_3,
                       execute_fn=lambda: self.ExecuteTimedStep(self.salad_looting_short_group_3, self.LootLoopStart()),
                       exit_condition=lambda: self.LootLoopComplete() or self.ShouldForceTransitionStep(),
                       run_once=False)
        ### 17 or 2 SHORT GROUP ###
        ### 16 or 4 SHORT GROUP ###
        self.salad_Routine.AddState(self.salad_running_short_group_4,
                       execute_fn=lambda: self.ExecuteTimedStep(self.salad_running_short_group_4, self.TimeToRunToGroup(self.salad_pathing_group_16, self.running_movement_Handler)),
                       exit_condition=lambda: self.RunToGroupDone(self.salad_pathing_group_16, self.running_movement_Handler),
                       run_once=False)
        self.salad_Routine.AddState(self.salad_killing_short_group_4,
                       execute_fn=lambda: self.ExecuteTimedStep(self.salad_killing_short_group_4, self.KillLoopStart()),
                       exit_condition=lambda: self.KillLoopComplete(),
                       run_once=False)
        self.salad_Routine.AddState(self.salad_looting_short_group_4,
                       execute_fn=lambda: self.ExecuteTimedStep(self.salad_looting_short_group_4, self.LootLoopStart()),
                       exit_condition=lambda: self.LootLoopComplete() or self.ShouldForceTransitionStep(),
                       run_once=False)
        ### 16 or 4 SHORT GROUP ###
        ### 15 or 5 SHORT GROUP ###
        self.salad_Routine.AddState(self.salad_running_short_group_5,
                       execute_fn=lambda: self.ExecuteTimedStep(self.salad_running_short_group_5, self.TimeToRunToGroup(self.salad_pathing_group_15, self.running_movement_Handler)),
                       exit_condition=lambda: self.RunToGroupDone(self.salad_pathing_group_15, self.running_movement_Handler),
                       run_once=False)
        self.salad_Routine.AddState(self.salad_killing_short_group_5,
                       execute_fn=lambda: self.ExecuteTimedStep(self.salad_killing_short_group_5, self.KillLoopStart()),
                       exit_condition=lambda: self.KillLoopComplete(),
                       run_once=False)
        self.salad_Routine.AddState(self.salad_looting_short_group_5,
                       execute_fn=lambda: self.ExecuteTimedStep(self.salad_looting_short_group_5, self.LootLoopStart()),
                       exit_condition=lambda: self.LootLoopComplete() or self.ShouldForceTransitionStep(),
                       run_once=False)
        ### 15 or 5 SHORT GROUP ###
        ### 14 or 6 SHORT GROUP ###
        self.salad_Routine.AddState(self.salad_running_short_group_6,
                       execute_fn=lambda: self.ExecuteTimedStep(self.salad_running_short_group_6, self.TimeToRunToGroup(self.salad_pathing_group_14, self.running_movement_Handler)),
                       exit_condition=lambda: self.RunToGroupDone(self.salad_pathing_group_14, self.running_movement_Handler),
                       run_once=False)
        self.salad_Routine.AddState(self.salad_killing_short_group_6,
                       execute_fn=lambda: self.ExecuteTimedStep(self.salad_killing_short_group_6, self.KillLoopStart()),
                       exit_condition=lambda: self.KillLoopComplete(),
                       run_once=False)
        self.salad_Routine.AddState(self.salad_looting_short_group_6,
                       execute_fn=lambda: self.ExecuteTimedStep(self.salad_looting_short_group_6, self.LootLoopStart()),
                       exit_condition=lambda: self.LootLoopComplete() or self.ShouldForceTransitionStep(),
                       run_once=False)
        ### 14 or 6 SHORT GROUP ###
        ### 13 or 7 SHORT GROUP ###
        self.salad_Routine.AddState(self.salad_running_short_group_7,
                       execute_fn=lambda: self.ExecuteTimedStep(self.salad_running_short_group_7, self.TimeToRunToGroup(self.salad_pathing_group_13, self.running_movement_Handler)),
                       exit_condition=lambda: self.RunToGroupDone(self.salad_pathing_group_13, self.running_movement_Handler),
                       run_once=False)
        self.salad_Routine.AddState(self.salad_killing_short_group_7,
                       execute_fn=lambda: self.ExecuteTimedStep(self.salad_killing_short_group_7, self.KillLoopStart()),
                       exit_condition=lambda: self.KillLoopComplete(),
                       run_once=False)
        self.salad_Routine.AddState(self.salad_looting_short_group_7,
                       execute_fn=lambda: self.ExecuteTimedStep(self.salad_looting_short_group_7, self.LootLoopStart()),
                       exit_condition=lambda: self.LootLoopComplete() or self.ShouldForceTransitionStep(),
                       run_once=False)
        ### 13 or 7 SHORT GROUP ###
        ### 12 or 8 SHORT GROUP ###
        self.salad_Routine.AddState(self.salad_running_short_group_8,
                       execute_fn=lambda: self.ExecuteTimedStep(self.salad_running_short_group_8, self.TimeToRunToGroup(self.salad_pathing_group_12, self.running_movement_Handler)),
                       exit_condition=lambda: self.RunToGroupDone(self.salad_pathing_group_12, self.running_movement_Handler),
                       run_once=False)
        self.salad_Routine.AddState(self.salad_killing_short_group_8,
                       execute_fn=lambda: self.ExecuteTimedStep(self.salad_killing_short_group_8, self.KillLoopStart()),
                       exit_condition=lambda: self.KillLoopComplete(),
                       run_once=False)
        self.salad_Routine.AddState(self.salad_looting_short_group_8,
                       execute_fn=lambda: self.ExecuteTimedStep(self.salad_looting_short_group_8, self.LootLoopStart()),
                       exit_condition=lambda: self.LootLoopComplete() or self.ShouldForceTransitionStep(),
                       run_once=False)
        ### 12 or 8 SHORT GROUP ###
        ### 10 or 10 SHORT GROUP ###
        self.salad_Routine.AddState(self.salad_running_short_group_9,
                       execute_fn=lambda: self.ExecuteTimedStep(self.salad_running_short_group_9, self.TimeToRunToGroup(self.salad_pathing_group_10, self.running_movement_Handler)),
                       exit_condition=lambda: self.RunToGroupDone(self.salad_pathing_group_10, self.running_movement_Handler),
                       run_once=False)
        self.salad_Routine.AddState(self.salad_killing_short_group_9,
                       execute_fn=lambda: self.ExecuteTimedStep(self.salad_killing_short_group_9, self.KillLoopStart()),
                       exit_condition=lambda: self.KillLoopComplete(),
                       run_once=False)
        self.salad_Routine.AddState(self.salad_looting_short_group_9,
                       execute_fn=lambda: self.ExecuteTimedStep(self.salad_looting_short_group_9, self.LootLoopStart()),
                       exit_condition=lambda: self.LootLoopComplete() or self.ShouldForceTransitionStep(),
                       run_once=False)
        ### 10 or 10 SHORT GROUP ###
        ### 9 or 11 SHORT GROUP ###
        self.salad_Routine.AddState(self.salad_running_short_group_10,
                       execute_fn=lambda: self.ExecuteTimedStep(self.salad_running_short_group_10, self.TimeToRunToGroup(self.salad_pathing_group_20, self.running_movement_Handler)),
                       exit_condition=lambda: self.RunToGroupDone(self.salad_pathing_group_20, self.running_movement_Handler),
                       run_once=False)
        self.salad_Routine.AddState(self.salad_killing_short_group_10,
                       execute_fn=lambda: self.ExecuteTimedStep(self.salad_killing_short_group_10, self.KillLoopStart()),
                       exit_condition=lambda: self.KillLoopComplete(),
                       run_once=False)
        self.salad_Routine.AddState(self.salad_looting_short_group_10,
                       execute_fn=lambda: self.ExecuteTimedStep(self.salad_looting_short_group_10, self.LootLoopStart()),
                       exit_condition=lambda: self.LootLoopComplete() or self.ShouldForceTransitionStep(),
                       run_once=False)
        ### 9 or 11 SHORT GROUP ###
        ### 11 or 9 SHORT GROUP ###
        self.salad_Routine.AddState(self.salad_running_short_group_11,
                       execute_fn=lambda: self.ExecuteTimedStep(self.salad_running_short_group_11, self.TimeToRunToGroup(self.salad_pathing_group_11, self.running_movement_Handler)),
                       exit_condition=lambda: self.RunToGroupDone(self.salad_pathing_group_11, self.running_movement_Handler),
                       run_once=False)
        self.salad_Routine.AddState(self.salad_killing_short_group_11,
                       execute_fn=lambda: self.ExecuteTimedStep(self.salad_killing_short_group_11, self.KillLoopStart()),
                       exit_condition=lambda: self.KillLoopComplete(),
                       run_once=False)
        self.salad_Routine.AddState(self.salad_looting_short_group_11,
                       execute_fn=lambda: self.ExecuteTimedStep(self.salad_looting_short_group_11, self.LootLoopStart()),
                       exit_condition=lambda: self.LootLoopComplete() or self.ShouldForceTransitionStep(),
                       run_once=False)
        ### 11 or 9 SHORT GROUP ###
        ### === ABOVE HERE IS SHORT LOOP RUN > FIGHT > LOOT LOOP === ###

        # Resign after all are done
        self.salad_Routine.AddState(self.salad_end_check_sink)
        self.salad_Routine.AddState(self.salad_run_success,
                       execute_fn=lambda: self.ExecuteStep(self.salad_run_success, self.SuccessResign()))
        self.salad_Routine.AddState(self.salad_resign_state_name,
                       execute_fn=lambda: self.ExecuteStep(self.salad_resign_state_name, Player.SendChatCommand("resign")),
                       exit_condition=lambda: Agent.IsDead(Player.GetAgentID()) or Map.GetMapID() == Mapping.Kamadan,
                       transition_delay_ms=3000)
        self.salad_Routine.AddState(self.salad_wait_return_state_name,
                       execute_fn=lambda: self.ExecuteTimedStep(self.salad_wait_return_state_name, Party.ReturnToOutpost()),
                       exit_condition=lambda: Map.GetMapID() == Mapping.Kamadan and Party.IsPartyLoaded(),
                       transition_delay_ms=3000)
        self.salad_Routine.AddState(self.salad_end_state_name,
                       execute_fn=lambda: self.ExecuteStep(self.salad_end_state_name, self.CheckSaladRoutineEnd()),
                       transition_delay_ms=1000)        
        self.salad_Routine.AddSubroutine(self.salad_inventory_state_name_end,
                       sub_fsm = self.inventoryRoutine)       
        self.salad_Routine.AddSubroutine(self.salad_exchange_salad_routine_end,
                       condition_fn=lambda: self.CheckExchangeSalads() and CheckIfInventoryHasItem(ModelID.Iboga_Petal))
        self.salad_Routine.AddState(self.salad_forced_stop,                                    
                       execute_fn=lambda: self.ExecuteStep(self.salad_forced_stop, None))
        
        self.RunTimer = Timer()
        self.TotalTimer = Timer()

    def CheckExchangeSalads(self):
        self.Log(f"Exchange Iboga Petals: {self.salad_exchange}")
        return self.salad_exchange
    
    def ApplyConfigSettingsOverride(self, leave_party, collect_input, do_salad_exchange, do_short_route) -> None:
        self.ApplyConfigSettings(leave_party, collect_input)
        self.salad_exchange = do_salad_exchange
        self.salad_short_route = do_short_route
        
    # Start the Salad routine from the first state after soft reset in case player moved around.
    def Start(self):
        if self.salad_Routine and not self.salad_Routine.is_started():
            self.SoftReset()
            self.salad_Routine.start()
            self.window.StartBot()

    # Stop the Salad routine.
    def Stop(self):
        if not self.salad_Routine:
            return
        
        self.InternalStop()
        
        if self.salad_Routine.is_started():
            self.salad_Routine.stop()
            self.window.StopBot()

    def InternalStart(self):
        Party.SetNormalMode()
        self.TotalTimer.Start()

    def InternalStop(self):
        self.salad_Routine.jump_to_state_by_name(self.salad_forced_stop)
        self.window.StopBot()
        self.TotalTimer.Stop()
        self.RunTimer.Stop()

    def Reset(self):     
        if self.salad_Routine:
            self.InternalStop()
        
        self.salad_collected = 0    
        self.salad_runs = 0
        self.salad_success = 0
        self.salad_fails = 0

        self.salad_first_after_reset = True      
        self.average_run_history.clear()
        self.average_run_time = 0
        self.current_run_time = 0   

        self.SoftReset()

        # Get new set of inventory slots to keep around in case player went and did some shit, then came back
        self.window.ResetBot()

    def SoftReset(self):
        self.player_stuck = False
        self.salad_wait_to_kill = False
        self.salad_ready_to_kill = False
        self.salad_killing_staggering_casted = False
        self.salad_killing_eremites_casted = False
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
        self.salad_exchange_pathing_handler.reset()
        self.salad_loot_timer.Stop()
        self.salad_loot_done_timer.Stop()
        self.salad_stuck_timer.Stop()
        self.salad_second_timer.Stop()
        self.salad_stay_alive_timer.Stop()
        self.salad_step_done_timer.Stop()
        self.salad_pathing_resign_portal_handler.reset()
        self.salad_pathing_portal_only_handler_1.reset()
        self.salad_pathing_portal_only_handler_2.reset()
        self.salad_pathing_group_1.reset()
        self.salad_pathing_group_2.reset()
        self.salad_pathing_group_3.reset()
        self.salad_pathing_group_4.reset()
        self.salad_pathing_group_5.reset()
        self.salad_pathing_group_6.reset()
        self.salad_pathing_group_7.reset()
        self.salad_pathing_group_8.reset()
        self.salad_pathing_group_9.reset()
        self.salad_pathing_group_10.reset()
        self.salad_pathing_group_11.reset()
        self.salad_pathing_group_12.reset()
        self.salad_pathing_group_13.reset()
        self.salad_pathing_group_14.reset()
        self.salad_pathing_group_15.reset()
        self.salad_pathing_group_16.reset()
        self.salad_pathing_group_17.reset()
        self.salad_pathing_group_18.reset()
        self.salad_pathing_group_19.reset()
        self.salad_pathing_group_20.reset()

    def IsBotRunning(self):
        return self.salad_Routine.is_started() and not self.salad_Routine.is_finished()

    def Update(self):
        if self.salad_Routine.is_started() and not self.salad_Routine.is_finished():
            self.salad_Routine.update()

    def Resign(self):
        if self.salad_Routine.is_started():
            self.salad_runs += 1
            self.salad_Routine.jump_to_state_by_name(self.salad_resign_state_name)

    def SuccessResign(self):
        self.Resign()
        self.salad_success += 1

    def FailResign(self):
        self.Resign()
        self.salad_fails += 1

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
        global salad_selected
        if not salad_selected:
            self.salad_Routine.jump_to_state_by_name(self.salad_end_state_name)

    def GetCurrentRunTime(self):
        return self.RunTimer.GetElapsedTime()
    
    def GetAverageTime(self):
        return self.average_run_time
    
    def GetTotalTime(self):
        return self.TotalTimer.GetElapsedTime()
    
    def ExchangeSalads(self):
        if not self.salad_exchange_timer.IsRunning():
            self.salad_exchange_timer.Start()

        if not self.salad_exchange_timer.HasElapsed(40):
            return
        
        self.salad_exchange_timer.Reset()

        try:
            turn_in = GetItemIdFromModelId(ModelID.Iboga_Petal, 2)
            count = GetModelIdCount(ModelID.Iboga_Petal)

            if turn_in == 0 or count < 2:
                self.Log(f"Not enough items to trade. Ending")
                return
            
            items3 = self.pyMerchant.get_merchant_item_list()
            if items3:
                for item in items3:
                    if Item.GetModelID(item) == ModelID.Pahnai_Salad:
                        buy = [2]
                        if len(turn_in) > 1:
                            buy = [1, 1]
                        self.pyMerchant.collector_buy_item(item, 0, turn_in, buy)

        except Exception as e:
            self.Log(f"Error in Exchanging Salad: {str(e)}", Py4GW.Console.MessageType.Error)

    def ExchangeSaladsDone(self):
        return not CheckIfInventoryHasItem(ModelID.Iboga_Petal, 2)
        
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
        
        if primary == Professions.Name.Dervish:
            SkillBar.LoadSkillTemplate(self.salad_primary_dervish_skillbar_code)
        elif primary == Professions.Name.Elementalist:
            SkillBar.LoadSkillTemplate(self.salad_primary_elementalist_skillbar_code)
        else:
            self.Log("For Best Results use D/E or E/D")
            self.InternalStop()
    
    def IsSkillBarLoaded(self):
        primary, secondary = Agent.GetProfessionNames(Player.GetAgentID())
        
        if primary != Professions.Name.Dervish and secondary != Professions.Name.Elementalist and primary != Professions.Name.Elementalist and secondary != Professions.Name.Dervish :        
            self.Log("Bot Requires D/E or E/D", Py4GW.Console.MessageType.Error)            
            self.InternalStop()
            return False
        else:
            # Only require 1,2,3,4 and 8
            if SkillBar.GetSkillIDBySlot(1) == 0 or SkillBar.GetSkillIDBySlot(2) == 0 or \
            SkillBar.GetSkillIDBySlot(6) == 0 or SkillBar.GetSkillIDBySlot(7) == 0 or \
            SkillBar.GetSkillIDBySlot(8) == 0:
                self.player_skillbar_load_count += 1
                if self.player_skillbar_load_count > 10:
                    self.Log("Unable to Load Skills")
                    self.InternalStop()
                return False
        
        self.skillBar = self.Salad_Skillbar()
        return True

    # This function is executed for each run to skales
    def TimeToRunToGroup(self, path_handler, movement_handler):
        if not self.salad_second_timer.IsRunning():
            self.salad_second_timer.Start()

        if not self.salad_second_timer.HasElapsed(100):
            return
        
        self.salad_second_timer.Reset()
                      
        try:
            player_id = Player.GetAgentID()
            if Agent.IsDead(player_id):
                self.FailResign()
                return
                            
            # Run the stay alive script.
            self.StayAliveLoop()

            # Try to follow the path based on pathing points and movement handler.
            Routines.Movement.FollowPath(path_handler, movement_handler)
        except Exception as e:
            Py4GW.Console.Log("Run To Drakes", str(e), Py4GW.Console.MessageType.Error)

    def RunToGroupDone(self, path_handler, movement_handler):
        if not self.salad_step_done_timer.IsRunning():
            self.salad_step_done_timer.Start()

        if not self.salad_step_done_timer.HasElapsed(250):
            return False
        
        pathDone = Routines.Movement.IsFollowPathFinished(path_handler, movement_handler)         
        surrounded = IsEnemyModelListInRange(self.enemy_list, GameAreas.Earshot)
        #forceStep = self.ShouldForceTransitionStep()

        done = pathDone or surrounded or self.player_stuck
        if done:
            self.salad_step_done_timer.Stop()

        self.salad_step_done_timer.Reset()
        return done

    def KillLoopStart(self):
        self.StayAliveLoop()
        self.Kill()

    # Stay alive using all heal buffs and hos if available
    def StayAliveLoop(self):
        if not self.salad_stay_alive_timer.IsRunning():
            self.salad_stay_alive_timer.Start()

        if not self.salad_stay_alive_timer.HasElapsed(200):
            return
        
        self.salad_stay_alive_timer.Reset()

        try:            
            player_id = Player.GetAgentID()

            if Agent.IsDead(player_id):
                self.FailResign()
                return
                
            if not CanCast(player_id):
                return            
            
            dstab_time_remaining = 0
            regen_time_remain = 0
            drunk_time_remain = 0
                                  
            player_buffs = Effects.GetEffects(player_id)

            for buff in player_buffs:
                if buff.skill_id == self.skillBar.regen:
                    regen_time_remain = buff.time_remaining 
                if buff.skill_id == self.skillBar.dstab:
                    dstab_time_remaining = buff.time_remaining 
                if buff.skill_id == self.skillBar.drunkMaster:
                    drunk_time_remain = buff.time_remaining

            # Only cast dstab if we are about to use drunk master
            if drunk_time_remain < 10000 and dstab_time_remaining <= 3000:
                CastSkillByIdAndSlot(self.skillBar.dstab, self.skillBar.dstab_slot)
                return

            
            if HasBuff(player_id, self.skillBar.dstab) and drunk_time_remain < 10000:
                CastSkillByIdAndSlot(self.skillBar.drunkMaster, self.skillBar.drunkMaster_slot)
             
            # Cast stay alive spells if needed.
            maxHp = Agent.GetMaxHealth(player_id)                
            hp = Agent.GetHealth(player_id) * maxHp
            dangerHp = .6 * maxHp                                                  
            
            if hp < dangerHp and regen_time_remain < 3000 and HasEnoughEnergy(self.skillBar.regen) and IsSkillReadyById(self.skillBar.regen):
                CastSkillByIdAndSlot(self.skillBar.regen, self.skillBar.regen_slot)
        except Exception as e:
            Py4GW.Console.Log("StayAlive", str(e), Py4GW.Console.MessageType.Error)

    def Kill(self):
        if not self.salad_second_timer.IsRunning():
            self.salad_second_timer.Start()

        if not self.salad_second_timer.HasElapsed(200):
            return
        
        self.salad_second_timer.Reset()

        try:  
            # Start waiting to kill routine. 
            player_id = Player.GetAgentID()            

            if Agent.IsDead(player_id):
                self.FailResign()
                return
            
            if not CanCast(player_id):
                return  

            if (Map.IsMapReady() and not Map.IsMapLoading()):
                if (Map.IsExplorable() and Map.GetMapID() == Mapping.Plains_Of_Jarin and Party.IsPartyLoaded()):
                    enemy = GetTargetNearestEnemyByModelIdList(self.enemy_list, GameAreas.Great_Spellcast)
                                           
                    # Ensure have damage mitigation up before attacking
                    if enemy == 0:
                        return
                                            
                    if GetDistance(player_id, enemy) > GameAreas.Nearby and IsSkillReadyById(self.skillBar.ride_lightning) and HasEnoughEnergy(self.skillBar.ride_lightning): 
                        CastSkillByIdAndSlot(self.skillBar.ride_lightning, self.skillBar.ride_lightning_slot)
                        return                    
                    
                    if IsSkillReadyById(self.skillBar.zealous) and HasEnoughEnergy(self.skillBar.zealous):
                        CastSkillByIdAndSlot(self.skillBar.zealous, self.skillBar.zealous_slot)
                        return
                      
                    Player.Interact(enemy)
        except Exception as e:
            Py4GW.Console.Log("Kill Loop Error", f"Kill Loop Error {str(e)}", Py4GW.Console.MessageType.Error)

    def KillLoopComplete(self):
        try:
            if Agent.IsDead(Player.GetAgentID()):
                self.FailResign()
                return False
        
            enemy = GetNearestEnemyByModelIdList(self.enemy_list, GameAreas.Great_Spellcast)
                                           
            if enemy == 0:
                self.current_lootable = 0
                self.current_loot_tries = 0
                self.salad_second_timer.Stop()
                self.salad_stay_alive_timer.Stop()
                self.running_movement_Handler.reset()
                return True

            return False
        except:
            self.Log("Kill Loop Error", Py4GW.Console.MessageType.Error)

    # If issues comment internals and call super().CanPickUp()
    def CanPickUp(self, agentId, player_id):
        # Check if our item is a Salad first, otherwise let base hangle it.

        item_owner_id = Agent.GetItemAgentOwnerID(agentId)
        item_id = Agent.GetItemAgentItemID(agentId)

        if item_owner_id:
            if item_owner_id != 0 and player_id != 0 and item_owner_id != player_id:
                return False
            
            model = Item.GetModelID(item_id)

            if model == ModelID.Iboga_Petal:
                return True
            else:
                return super().CanPickUp(agentId, player_id)
              
        return False
    
    def LootLoopStart(self):
        try:
            if not self.salad_loot_timer.IsRunning():
                self.salad_loot_timer.Start()

            if self.salad_loot_timer.HasElapsed(self.loot_timer_elapsed):                
                self.salad_loot_timer.Reset()

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

                if model == ModelID.Iboga_Petal:
                    self.salad_collected += 1

                Player.Interact(item)
        except Exception as e:
            Py4GW.Console.Log("Loot Loop", f"Error during looting {str(e)}", Py4GW.Console.MessageType.Error)

    def LootLoopComplete(self):
        try:
            if not self.salad_loot_done_timer.IsRunning():
                self.salad_loot_done_timer.Start()

            if self.salad_loot_done_timer.HasElapsed(self.loot_timer_elapsed):
                self.salad_loot_done_timer.Reset()

                if self.current_lootable == 0 or Inventory.GetFreeSlotCount() == 0:
                    self.salad_loot_timer.Stop()
                    self.salad_loot_done_timer.Stop()
                    self.step_transition_threshold_timer.Stop()
                    return True

            return False
        except Exception as e:
            Py4GW.Console.Log("Loot Loop Complete", f"Error during looting {str(e)}", Py4GW.Console.MessageType.Error)
    
    def CheckFirstGroupComplete(self):
        done = self.LootLoopComplete() or self.ShouldForceTransitionStep()

        if done and self.salad_short_route:
            self.salad_Routine.jump_to_state_by_name(self.salad_running_short_group_1)
            return False
        return done

    def CheckLastGroupComplete(self):
        done = self.LootLoopComplete() or self.ShouldForceTransitionStep()
        
        if done and not self.salad_short_route:
            self.salad_Routine.jump_to_state_by_name(self.salad_end_check_sink)

        return done

    def GetSaladCollected(self):
        return self.salad_collected

    def GetSaladStats(self):
        return (self.salad_runs, self.salad_success)
    
    # Jump back to output pathing if not done collecting
    def CheckSaladRoutineEnd(self):
        global salad_selected, salad_exchange

        # Don't reset the Salad count
        self.RunEnding()
        self.SoftReset()

        self.salad_first_after_reset = False

        if not salad_selected:
            self.Log("Not Farming Salad - AutoStop")
            if salad_exchange:
                self.salad_Routine.jump_to_state_by_name(self.salad_exchange_salad_routine_end)
            else:
                self.InternalStop()
            return
        
        if (self.salad_collected / 2) < self.main_item_collect:
            # mapping to outpost may have failed OR the threshold was reached. Try to map there and start over.
            if Map.GetMapID() != Mapping.Kamadan:
                self.salad_Routine.jump_to_state_by_name(self.salad_travel_state_name)
            else:
                # already at outpost, check slot count, handle inv or continue farm
                if Inventory.GetFreeSlotCount() <= self.default_min_slots:
                    self.UpdateState(self.salad_inventory_state_name)
                    self.salad_Routine.jump_to_state_by_name(self.salad_inventory_state_name)
                else:
                    self.salad_Routine.jump_to_state_by_name(self.salad_change_weapon_staff)
        elif salad_exchange:
            self.salad_Routine.jump_to_state_by_name(self.salad_exchange_salad_routine_end)
        else:
            self.Log("Salad Count Matched - AutoStop")
            self.InternalStop()
      
  ### --- ROUTINE FUNCTIONS --- ###

def GetSaladCollected():
    return salad_Routine.GetSaladCollected() / 2.0

def GetSaladData():
    return salad_Routine.GetSaladStats()

salad_Window = Salad_Window(bot_name)
salad_Routine = Salad_Farm(salad_Window)

def ApplyLootAndMerchantSelections():
    global salad_input
    salad_Routine.ApplySelections(salad_input, salad_Window.id_Items, salad_Window.collect_coins, salad_Window.collect_events, salad_Window.collect_items_white, salad_Window.collect_items_blue, \
                salad_Window.collect_items_grape, salad_Window.collect_items_gold, salad_Window.collect_dye, salad_Window.sell_items, salad_Window.sell_items_white, \
                salad_Window.sell_items_blue, salad_Window.sell_items_grape, salad_Window.sell_items_gold, salad_Window.sell_items_green, salad_Window.sell_materials, salad_Window.salvage_items, salad_Window.salvage_items_white, \
                salad_Window.salvage_items_blue, salad_Window.salvage_items_grape, salad_Window.salvage_items_gold)

def ApplySaladConfigSettings(leave_party, salad_input, salad_exchange, salad_short_route):
    salad_Routine.ApplyConfigSettingsOverride(leave_party, salad_input, salad_exchange, salad_short_route)

def ApplySaladInventorySettings(min_slots, min_gold, depo_items, depo_mats):
    salad_Routine.ApplyInventorySettings(min_slots, min_gold, depo_items, depo_mats)

def StartBot():
    ApplyLootAndMerchantSelections()
    salad_Routine.Start()

def StopBot():
    if salad_Routine.IsBotRunning():
        salad_Routine.Stop()

def ResetBot():
    # Stop the main state machine  
    salad_Routine.Stop()
    salad_Routine.Reset()

def PrintData():
    salad_Routine.PrintData()

def GetRunTime():
    return salad_Routine.GetCurrentRunTime()

def GetAverageRunTime():
    return salad_Routine.GetAverageTime()

def GetTotalRunTime():
    return salad_Routine.GetTotalTime()

### --- MAIN --- ###
def main():
    try:
        if salad_Window:
            salad_Window.Show()

        # Could just put a main timer here and only fire the updates in some interval, but I like more control specific to tasks (eg. Staying Alive, Kill, Loot, etc)
        if Party.IsPartyLoaded():
            if salad_Routine and salad_Routine.IsBotRunning():
                salad_Routine.Update()
                
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