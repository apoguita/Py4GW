from Py4GWCoreLib import *
from Sources.Nikon_Scripts.BotUtilities import *
from Sources.Nikon_Scripts.WindowUtilites import *

from Sources.Nikon_Scripts import Mapping

bot_name = "Nikons Kabob Farm"

kabob_selected = True
do_kabob_exchange = False
kabob_input = 250
show_about_popup = False

class Kabob_Window(BasicWindow):
    global kabob_selected, kabob_input, do_kabob_exchange
    
    kabob_original_size = [350.0, 400.0]
    kabob_explanded_size = [350.0, 475.0]

    config_test_collect = kabob_input
    config_test_farm = kabob_selected
    config_test_exchange = do_kabob_exchange

    def __init__(self, window_name="Basic Window", window_size = [350.0, 470.0], show_logger = True, show_state = True):
        super().__init__(window_name, window_size, show_logger, show_state)

    def ShowMainControls(self):
        global kabob_selected, kabob_input, do_kabob_exchange, show_about_popup

        if PyImGui.collapsing_header("About - Farm Requirements"):
            PyImGui.begin_child("About_child_window", (0, 250), False, 0)
            PyImGui.text("- Required Quest: Drakes on the Plain")
            PyImGui.text("- Full windwalker, +4 Earth, +1 Scyth, +1 Mysticism")
            PyImGui.text("- Whatever HP rune you can afford and attunement.")
            PyImGui.text("- Suggest Zealous Enchanting Scythe.")
            PyImGui.text("  \t*Droknars Reaper is perfect.")
            PyImGui.text("- Equip Scythe in Slot 2 if not already.")
            PyImGui.text("- Equip Staff in Slot 1 if not already (not required).")
            PyImGui.text(f"- Inventory Snapshot Taken : Current Slots Safe.")
            PyImGui.text(f"- During salvage, saved slots are not touched.")
            PyImGui.text(f"- Moving items you risk losing during sell.")
            PyImGui.text(f"- Just dont move items.")
            PyImGui.text(f"- Will not sell Drake Flesh, Salv or Id kits.")
            PyImGui.end_child()
        PyImGui.separator()

    def ShowConfigSettingsTabItem(self):
        global kabob_selected, kabob_input, do_kabob_exchange

        if PyImGui.begin_table("Collect_Inputs", 2, PyImGui.TableFlags.SizingStretchSame):
            PyImGui.table_next_row()
            PyImGui.table_next_column()
            kabob_selected = PyImGui.checkbox("Farm Drake Flesh", kabob_selected)  
            PyImGui.table_next_column()
            kabob_input = PyImGui.input_int("# Flesh##1", kabob_input) if kabob_input >= 0 else 0 
            PyImGui.table_next_row()
            PyImGui.table_next_column()
            do_kabob_exchange = PyImGui.checkbox("Exchange Drake Flesh", do_kabob_exchange)
            PyImGui.table_next_row()
            PyImGui.table_next_column()
            self.leave_party = PyImGui.checkbox("Leave Party", self.leave_party)
            PyImGui.end_table()

    def ShowResults(self):
        global kabob_input

        PyImGui.separator()
        
        if PyImGui.collapsing_header("Results##Kabob", int(PyImGui.TreeNodeFlags.DefaultOpen)):
            if PyImGui.begin_table("Runs_Results", 6):
                kabob_data = GetKabobData()
                PyImGui.table_next_row()
                PyImGui.table_next_column()
                PyImGui.text(f"Runs:")
                PyImGui.table_next_column() 
                PyImGui.text(f"{kabob_data[0]}")
                PyImGui.table_next_column() 
                PyImGui.text(f"Success: ")
                PyImGui.table_next_column()
                PyImGui.text_colored(f"{kabob_data[1]}", (0, 1, 0, 1))
                PyImGui.table_next_column()
                PyImGui.text(f"Fails:")
                PyImGui.table_next_column()
                fails = kabob_data[0] - kabob_data[1]

                if fails > 0:
                    PyImGui.text_colored(f"{fails}", (1, 0, 0, 1))
                else:
                    PyImGui.text(f"{fails}")

                PyImGui.table_next_row()
                PyImGui.table_next_column()
                PyImGui.text("Kabobs:")
                PyImGui.table_next_column()
                if kabob_selected and kabob_input > 0 and GetKabobCollected() == 0:            
                    PyImGui.text_colored(f"{GetKabobCollected()}", (1, 0, 0, 1))
                else:
                    PyImGui.text_colored(f"{GetKabobCollected()}", (0, 1, 0, 1))
                PyImGui.table_next_column()
                PyImGui.text(f"collected of")
                PyImGui.table_next_column()                
                PyImGui.text(f"{kabob_input}")
                PyImGui.table_next_row()
                PyImGui.end_table()

            if PyImGui.begin_table("Run_Times", 2):
                PyImGui.table_next_row()
                PyImGui.table_next_column()
                PyImGui.text(f"Current:")
                PyImGui.table_next_column()
                PyImGui.text(f"      {FormatTime(GetRunTime(), "mm:ss:ms")}")
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
        global kabob_input, do_kabob_exchange, kabob_selected
        super().ApplyAndUpdateSettings()

        if self.config_test_collect != kabob_input or \
            self.config_test_exchange != do_kabob_exchange or \
            self.config_test_farm != kabob_selected:
            self.ApplyConfigSettings()
    
            self.config_test_collect = kabob_input
            self.config_test_farm = do_kabob_exchange
            self.config_test_exchange = kabob_selected

    def ApplyLootMerchantSettings(self) -> None:
        ApplyLootAndMerchantSelections()

    def ApplyConfigSettings(self) -> None:
        global kabob_input, do_kabob_exchange
        ApplyKabobConfigSettings(self.leave_party, kabob_input, do_kabob_exchange)
        
    def ApplyInventorySettings(self) -> None:
        ApplyKabobInventorySettings(self.minimum_slots, self.minimum_gold, self.depo_items, self.depo_mats)

    def GetKabobSettings(self):
        global kabob_input

        return (kabob_input, self.id_Items, self.collect_coins, self.collect_events, self.collect_items_white, self.collect_items_blue, \
                self.collect_items_grape, self.collect_items_gold, self.collect_dye, self.sell_items, self.sell_items_white, \
                self.sell_items_blue, self.sell_items_grape, self.sell_items_gold, self.sell_materials, self.salvage_items, self.salvage_items_white, \
                self.salvage_items_blue, self.salvage_items_grape, self.salvage_items_gold)
                
class Kabob_Farm(ReportsProgress):
    class Kabob_Skillbar:    
        def __init__(self):
            self.sand_shards = SkillBar.GetSkillIDBySlot(1)
            self.sand_shards_slot = 1
            self.vos = SkillBar.GetSkillIDBySlot(2)
            self.vos_slot = 2
            self.staggering = SkillBar.GetSkillIDBySlot(3)
            self.staggering_slot = 3
            self.eremites = SkillBar.GetSkillIDBySlot(4)
            self.eremites_slot = 4
            self.intimidating = SkillBar.GetSkillIDBySlot(5)
            self.intimidating_slot = 5
            self.sanctity = SkillBar.GetSkillIDBySlot(6)
            self.sanctity_slot = 6
            self.regen = SkillBar.GetSkillIDBySlot(7)
            self.regen_slot = 7
            self.hos = SkillBar.GetSkillIDBySlot(8)
            self.hos_slot = 8

    # Kabob_Routine is the FSM instance
    Kabob_Routine = FSM("Kabob_Main")
    Kabob_Exchange_Routine = FSM("Kabob_Exchange")

    Kabob_Skillbar_Code = "Ogek8Np5Kzmj59brdbu731L7FBC"
    Kabob_Hero_Skillbar_Code = "OQkiUxm8sjJxsYAAAAAAAAAA"

    kabob_exchange_travel = "Kabob- Exchange Travel Kamadan"
    kabob_exchange_wait_map = "Kabob- Exchange Waiting Map"
    kabob_exchange_move_to_collector = "Kabob- Exchange Go to Chef"
    kabob_exchange_target_collector = "Kabob- Exchange Target"
    kabob_exchange_interact_collector = "Kabob- Exchange Interact"
    kabob_exchange_do_exchange_all = "Kabob- Exchange Kabobs"
    kabob_exchange_Kabobs_routine_start = "Kabob- Go Exchange Kabobs 1"
    kabob_exchange_Kabobs_routine_end = "Kabob- Go Exchange Kabobs 2"

    kabob_start_farm = "Kabob- Check Farm"
    kabob_inventory_routine = "DoInventoryRoutine"
    kabob_initial_check_inventory = "Kabob- Inventory Check"
    kabob_check_inventory_after_handle_inventory = "Kabob- Inventory Handled?"
    kabob_travel_state_name = "Kabob- Traveling to Rihlon"
    kabob_set_normal_mode = "Kabob- Set Normal Mode"
    kabob_add_hero_state_name = "Kabob- Adding Koss"
    kabob_load_skillbar_state_name = "Kabob- Load Skillbar"
    kabob_pathing_1_state_name = "Kabob- Leaving Outpost 1"
    kabob_resign_pathing_state_name = "Kabob- Setup Resign"
    kabob_pathing_2_state_name = "Kabob- Leaving Outpost 2"
    kabob_waiting_map_state_name = "Kabob- Farm Map Loading"
    kabob_change_weapon_staff = "Kabob- Change to Staff"
    kabob_change_weapon_scythe = "Kabob- Change to Scythe"
    kabob_kill_koss_state_name = "Kabob- Killing Koss"
    kabob_waiting_run_state_name = "Kabob- Move to Farm Spot"
    kabob_waiting_kill_state_name = "Kabob- Killing Drakes"
    kabob_looting_state_name = "Kabob- Picking Up Loot"
    kabob_resign_state_name = "Kabob- Resigning"
    kabob_wait_return_state_name = "Kabob- Wait Return"
    kabob_inventory_state_name = "Kabob- Handle Inventory"
    kabob_inventory_state_name_end = "Kabob-Handle Inventory 2"
    kabob_end_state_name = "Kabob- End Routine"
    kabob_forced_stop = "Kabob- End Forced"
    kabob_outpost_portal = [(-15022, 8470)] # Used by itself if spawn close to Floodplain portal
    kabob_outpost_pathing = [(-15480, 11138), (-16009, 10219), (-15022, 8470)] # Used when spawn location is near xunlai chest or merchant
    kabob_farm_run_pathing = [(-14512, 8238), (-12469, 9387), (-12243, 10163), (-10703, 10952), (-10066, 11265), (-9550, 11550), (-9179, 11663), (-8740, 11771)]
    kabob_outpost_resign_pathing = [(-15743, 9784)]
    kabob_merchant_position = [(-15082, 11368)]
    kabob_pathing_portal_only_handler_1 = Routines.Movement.PathHandler(kabob_outpost_portal)
    kabob_pathing_portal_only_handler_2 = Routines.Movement.PathHandler(kabob_outpost_portal)
    kabob_pathing_resign_portal_handler = Routines.Movement.PathHandler(kabob_outpost_resign_pathing)
    kabob_pathing_move_to_portal_handler = Routines.Movement.PathHandler(kabob_outpost_pathing)
    kabob_pathing_move_to_kill_handler = Routines.Movement.PathHandler(kabob_farm_run_pathing)
    
    kabob_exchange_pathing = [(-8608, 14646), (-11170, 15188)]
    kabob_exchange_pathing_handler = Routines.Movement.PathHandler(kabob_exchange_pathing)
    movement_Handler = Routines.Movement.FollowXY(50)
    
    keep_list = []
    keep_list.extend(IdSalveItems_Array)
    keep_list.extend(EventItems_Array)
    keep_list.append(ModelID.Chunk_Of_Drake_Flesh)
    keep_list.append(ModelID.Vial_Of_Dye)
    
    kabob_first_after_reset = False
    kabob_wait_to_kill = False
    kabob_ready_to_kill = False
    kabob_killing_staggering_casted = False
    kabob_killing_eremites_casted = False
    kabob_exchange = False

    player_stuck_hos_count = 0
    player_skillbar_load_count = 0
    player_previous_hp = 100

    weapon_slot_staff = 1
    weapon_slot_scythe = 2
    kabob_collected = 0
    add_koss_tries = 0
    current_lootable = 0
    current_loot_tries = 0
    current_run_time = 0
    average_run_time = 0
    average_run_history = []
    
    kabob_runs = 0
    kabob_success = 0
    kabob_fails = 0
    
    second_timer_elapsed = 1000
    loot_timer_elapsed = 1500
    
    pyParty = PyParty.PyParty()
    pyMerchant = PyMerchant.PyMerchant()
    kabob_exchange_timer = Timer()
    kabob_second_timer = Timer()
    kabob_step_done_timer = Timer()
    kabob_stuck_timer = Timer()
    kabob_loot_timer = Timer()
    kabob_loot_done_timer = Timer()
    kabob_stay_alive_timer = Timer()

    stuckPosition = []

    ### --- SETUP --- ###
    def __init__(self, window):
        self.current_inventory = GetInventoryItemSlots()

        # Base ReportsProgress type now handles inventory also
        super().__init__(window, Mapping.Rilohn_Refuge, self.kabob_merchant_position, self.current_inventory, self.keep_list)
        
        self.skillBar = self.Kabob_Skillbar()

        self.Kabob_Exchange_Routine.AddState(self.kabob_exchange_travel,
                                             execute_fn=lambda: self.ExecuteStep(self.kabob_exchange_travel, Routines.Transition.TravelToOutpost(Mapping.Kamadan)),
                                             exit_condition=lambda: Routines.Transition.HasArrivedToOutpost(Mapping.Kamadan),
                                             transition_delay_ms=1000)
        self.Kabob_Exchange_Routine.AddState(self.kabob_exchange_move_to_collector,
                                             execute_fn=lambda: self.ExecuteStep(self.kabob_exchange_move_to_collector, Routines.Movement.FollowPath(self.kabob_exchange_pathing_handler, self.movement_Handler)),
                                             exit_condition=lambda: Routines.Movement.IsFollowPathFinished(self.kabob_exchange_pathing_handler, self.movement_Handler),
                                             run_once=False)
        
        self.Kabob_Exchange_Routine.AddState(name=self.kabob_exchange_target_collector,
                                             execute_fn=lambda: self.ExecuteStep(self.kabob_exchange_target_collector, TargetNearestNpc()),
                                             transition_delay_ms=1000)
        
        self.Kabob_Exchange_Routine.AddState(name=self.kabob_exchange_interact_collector,
                                             execute_fn=lambda: self.ExecuteStep(self.kabob_exchange_interact_collector, Routines.Targeting.InteractTarget()),
                                             exit_condition=lambda: Routines.Targeting.HasArrivedToTarget())
        
        self.Kabob_Exchange_Routine.AddState(name=self.kabob_exchange_do_exchange_all,
                                             execute_fn=lambda: self.ExecuteStep(self.kabob_exchange_do_exchange_all, self.ExchangeKabobs()),
                                             exit_condition=lambda: self.ExchangeKabobsDone(), 
                                             run_once=False)    
        self.Kabob_Routine.AddSubroutine(self.kabob_exchange_Kabobs_routine_start,
                       sub_fsm=self.Kabob_Exchange_Routine,
                       condition_fn=lambda: self.CheckExchangeKabobs() and CheckIfInventoryHasItem(ModelID.Chunk_Of_Drake_Flesh))        
        self.Kabob_Routine.AddState(self.kabob_start_farm,
                                    execute_fn=lambda: self.ExecuteStep(self.kabob_start_farm, self.CheckIfShouldRunFarm()))
        self.Kabob_Routine.AddState(self.kabob_travel_state_name,
                       execute_fn=lambda: self.ExecuteStep(self.kabob_travel_state_name, Routines.Transition.TravelToOutpost(  Mapping.Rilohn_Refuge)),
                       exit_condition=lambda: Routines.Transition.HasArrivedToOutpost(Mapping.Rilohn_Refuge),
                       transition_delay_ms=1000)
        self.Kabob_Routine.AddState(self.kabob_initial_check_inventory, execute_fn=lambda: self.CheckInventory())
        self.Kabob_Routine.AddState(self.kabob_set_normal_mode,
                       execute_fn=lambda: self.ExecuteStep(self.kabob_set_normal_mode, self.InternalStart()),
                       transition_delay_ms=1000)
        self.Kabob_Routine.AddState(self.kabob_add_hero_state_name,
                       execute_fn=lambda: self.ExecuteStep(self.kabob_add_hero_state_name, self.PutKossInParty()), # Ensure only one hero in party
                       transition_delay_ms=1000)
        self.Kabob_Routine.AddState(self.kabob_load_skillbar_state_name,
                       execute_fn=lambda: self.ExecuteStep(self.kabob_load_skillbar_state_name, self.LoadSkillBar()), # Ensure only one hero in party                       
                       exit_condition=lambda: self.IsSkillBarLoaded(),
                       transition_delay_ms=1500)
        self.Kabob_Routine.AddState(self.kabob_pathing_1_state_name,
                       execute_fn=lambda: self.ExecuteStep(self.kabob_pathing_1_state_name, Routines.Movement.FollowPath(self.kabob_pathing_portal_only_handler_1, self.movement_Handler)),
                       exit_condition=lambda: Routines.Movement.IsFollowPathFinished(self.kabob_pathing_portal_only_handler_1, self.movement_Handler) or Map.GetMapID() == Mapping.Floodplain_Of_Mahnkelon,
                       run_once=False)
        self.Kabob_Routine.AddState(self.kabob_resign_pathing_state_name,
                       execute_fn=lambda: self.ExecuteStep(self.kabob_resign_pathing_state_name, Routines.Movement.FollowPath(self.kabob_pathing_resign_portal_handler, self.movement_Handler)),
                       exit_condition=lambda: Map.GetMapID() == Mapping.Rilohn_Refuge and Party.IsPartyLoaded(), # or Routines.Movement.IsFollowPathFinished(kabob_pathing_resign_portal_handler, movement_Handler) or Map.GetMapID() == Mapping.Rilohn_Refuge,
                       run_once=False)
        self.Kabob_Routine.AddSubroutine(self.kabob_inventory_state_name,
                       sub_fsm = self.inventoryRoutine, # dont add execute function wrapper here
                       condition_fn=lambda: not self.kabob_first_after_reset and Inventory.GetFreeSlotCount() <= self.GetMinimumSlots())        
        self.Kabob_Routine.AddState(self.kabob_check_inventory_after_handle_inventory, 
                       execute_fn=lambda: self.CheckInventory())
        self.Kabob_Routine.AddState(self.kabob_change_weapon_staff,
                       execute_fn=lambda: self.ExecuteStep(self.kabob_change_weapon_staff, self.RunStarting()),
                       transition_delay_ms=1000)
        self.Kabob_Routine.AddState(self.kabob_pathing_2_state_name,
                       execute_fn=lambda: self.ExecuteStep(self.kabob_pathing_2_state_name, Routines.Movement.FollowPath(self.kabob_pathing_portal_only_handler_2, self.movement_Handler)),
                       exit_condition=lambda: Routines.Movement.IsFollowPathFinished(self.kabob_pathing_portal_only_handler_2, self.movement_Handler) or Map.GetMapID() == Mapping.Floodplain_Of_Mahnkelon,
                       run_once=False)
        self.Kabob_Routine.AddState(self.kabob_waiting_map_state_name,
                       execute_fn=lambda: self.ExecuteStep(self.kabob_waiting_map_state_name, Routines.Transition.IsExplorableLoaded()),
                       transition_delay_ms=1000)
        self.Kabob_Routine.AddState(self.kabob_kill_koss_state_name,
                       execute_fn=lambda: self.ExecuteStep(self.kabob_kill_koss_state_name, self.KillKoss()),
                       transition_delay_ms=1000)
        self.Kabob_Routine.AddState(self.kabob_waiting_run_state_name,
                       execute_fn=lambda: self.ExecuteTimedStep(self.kabob_waiting_run_state_name, self.TimeToRunToDrakes()),
                       exit_condition=lambda: self.RunToDrakesDone(),
                       run_once=False)
        self.Kabob_Routine.AddState(self.kabob_change_weapon_scythe,
                       execute_fn=lambda: self.ExecuteStep(self.kabob_change_weapon_scythe, ChangeWeaponSet(self.weapon_slot_scythe)),
                       transition_delay_ms=1500)
        self.Kabob_Routine.AddState(self.kabob_waiting_kill_state_name,
                       execute_fn=lambda: self.ExecuteTimedStep(self.kabob_waiting_kill_state_name, self.KillLoopStart()),
                       exit_condition=lambda: self.KillLoopComplete() or self.ShouldForceTransitionStep(),
                       run_once=False)
        self.Kabob_Routine.AddState(self.kabob_looting_state_name,
                       execute_fn=lambda: self.ExecuteTimedStep(self.kabob_looting_state_name, self.LootLoopStart()),
                       exit_condition=lambda: self.LootLoopComplete() or self.ShouldForceTransitionStep(),
                       run_once=False)
        self.Kabob_Routine.AddState(self.kabob_resign_state_name,
                       execute_fn=lambda: self.ExecuteStep(self.kabob_resign_state_name, Player.SendChatCommand("resign")),
                       exit_condition=lambda: Agent.IsDead(Player.GetAgentID()) or Map.GetMapID() == Mapping.Rilohn_Refuge,
                       transition_delay_ms=3000)
        self.Kabob_Routine.AddState(self.kabob_wait_return_state_name,
                       execute_fn=lambda: self.ExecuteTimedStep(self.kabob_wait_return_state_name, Party.ReturnToOutpost()),
                       exit_condition=lambda: Map.GetMapID() == Mapping.Rilohn_Refuge and Party.IsPartyLoaded() or self.ShouldForceTransitionStep(),
                       transition_delay_ms=3000)
        self.Kabob_Routine.AddState(self.kabob_end_state_name,
                       execute_fn=lambda: self.ExecuteStep(self.kabob_end_state_name, self.CheckKabobRoutineEnd()),
                       transition_delay_ms=1000)        
        self.Kabob_Routine.AddSubroutine(self.kabob_inventory_state_name_end,
                       sub_fsm = self.inventoryRoutine)       
        self.Kabob_Routine.AddSubroutine(self.kabob_exchange_Kabobs_routine_end,
                       condition_fn=lambda: self.CheckExchangeKabobs() and CheckIfInventoryHasItem(ModelID.Chunk_Of_Drake_Flesh))
        self.Kabob_Routine.AddState(self.kabob_forced_stop,                                    
                       execute_fn=lambda: self.ExecuteStep(self.kabob_forced_stop, None))
        
        self.RunTimer = Timer()
        self.TotalTimer = Timer()

    def CheckExchangeKabobs(self):
        self.Log(f"Do Kabob Exchange: {self.kabob_exchange}")
        return self.kabob_exchange
    
    def ApplyConfigSettingsOverride(self, leave_party, collect_input, do_kabob_exchange) -> None:
        self.ApplyConfigSettings(leave_party, collect_input)
        self.kabob_exchange = do_kabob_exchange

    # Start the kabob routine from the first state after soft reset in case player moved around.
    def Start(self):
        if self.Kabob_Routine and not self.Kabob_Routine.is_started():
            self.SoftReset()
            self.Kabob_Routine.start()
            self.window.StartBot()

    # Stop the kabob routine.
    def Stop(self):
        if not self.Kabob_Routine:
            return
        
        self.InternalStop()

    def InternalStart(self):
        Party.SetNormalMode()
        self.TotalTimer.Start()

    def InternalStop(self):
        self.Kabob_Routine.jump_to_state_by_name(self.kabob_forced_stop)
        self.window.StopBot()
        self.TotalTimer.Stop()
        self.RunTimer.Stop()

    def Reset(self):     
        if self.Kabob_Routine:
            self.InternalStop()
        
        self.kabob_collected = 0    
        self.kabob_runs = 0
        self.kabob_success = 0
        self.kabob_fails = 0

        self.kabob_first_after_reset = True     
        self.average_run_history.clear()
        self.average_run_time = 0
        self.current_run_time = 0 

        self.SoftReset()

        # Get new set of inventory slots to keep around in case player went and did some shit, then came back
        self.window.ResetBot()

    def SoftReset(self):
        self.player_stuck = False
        self.kabob_wait_to_kill = False
        self.kabob_ready_to_kill = False
        self.kabob_killing_staggering_casted = False
        self.kabob_killing_eremites_casted = False
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
        self.movement_Handler.reset()
        self.kabob_loot_timer.Stop()
        self.kabob_loot_done_timer.Stop()
        self.kabob_stuck_timer.Stop()
        self.kabob_second_timer.Stop()
        self.kabob_stay_alive_timer.Stop()
        self.kabob_step_done_timer.Stop()
        self.kabob_pathing_move_to_kill_handler.reset()
        self.kabob_pathing_resign_portal_handler.reset()
        self.kabob_pathing_portal_only_handler_1.reset()
        self.kabob_pathing_portal_only_handler_2.reset()
        self.kabob_pathing_move_to_portal_handler.reset()

    def IsBotRunning(self):
        return self.Kabob_Routine.is_started() and not self.Kabob_Routine.is_finished()

    def Update(self):
        if self.Kabob_Routine.is_started() and not self.Kabob_Routine.is_finished():
            self.Kabob_Routine.update()

    def Resign(self):
        if self.Kabob_Routine.is_started():
            self.kabob_runs += 1
            self.Kabob_Routine.jump_to_state_by_name(self.kabob_resign_state_name)

    def SuccessResign(self):
        self.Resign()
        self.kabob_success += 1

    def FailResign(self):
        self.Resign()
        self.kabob_fails += 1

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
        global kabob_selected
        if not kabob_selected:
            self.Kabob_Routine.jump_to_state_by_name(self.kabob_end_state_name)

    def GetCurrentRunTime(self):
        return self.RunTimer.GetElapsedTime()
    
    def GetAverageTime(self):
        return self.average_run_time
    
    def GetTotalTime(self):
        return self.TotalTimer.GetElapsedTime()

    def ExchangeKabobs(self):
        if not self.kabob_exchange_timer.IsRunning():
            self.kabob_exchange_timer.Start()

        if not self.kabob_exchange_timer.HasElapsed(40):
            return
        
        self.kabob_exchange_timer.Reset()

        try:
            turn_in = GetItemIdFromModelId(ModelID.Chunk_Of_Drake_Flesh)

            if turn_in == 0:
                return
            
            items3 = self.pyMerchant.get_merchant_item_list()
            if items3:
                for item in items3:
                    if Item.GetModelID(item) == ModelID.Drake_Kabob:
                        self.pyMerchant.collector_buy_item(item, 0, turn_in, [1])

        except Exception as e:
            self.Log(f"Error in Exchanging Kabobs: {str(e)}", Py4GW.Console.MessageType.Error)

    def ExchangeKabobsDone(self):
        return not CheckIfInventoryHasItem(ModelID.Chunk_Of_Drake_Flesh)
    
    def CheckInventory(self):
        if Inventory.GetFreeSlotCount() <= self.default_min_slots:
            self.Log("Bags Full - Manually Handle")
            self.InternalStop()

    def Log(self, text, msgType=Py4GW.Console.MessageType.Info):
        if self.window:
            self.window.Log(text, msgType)
    ### --- SETUP --- ###

    ### --- ROUTINE FUNCTIONS --- ###
    def LoadSkillBar(self):
        primary_profession, _ = Agent.GetProfessionNames(Player.GetAgentID())

        if primary_profession != "Dervish":
            self.Log("Bot Requires Dervish Primary")
            self.InternalStop()
        else:
            SkillBar.LoadSkillTemplate(self.Kabob_Skillbar_Code)

            # Dont really care about koss if he doesnt have the skills, but try to set a build anyway
            SkillBar.LoadHeroSkillTemplate (1, self.Kabob_Hero_Skillbar_Code)
    
    def IsSkillBarLoaded(self):
        primary_profession, secondary = Agent.GetProfessionNames(Player.GetAgentID())
        
        if primary_profession != "Dervish":        
            self.Log("Bot Requires Dervish Primary", Py4GW.Console.MessageType.Error)            
            self.InternalStop()
            return False        
        elif secondary != "Assassin":
            self.Log("Bot Requires Assassin Secondary")
            self.InternalStop()
            return False
        else:
            if SkillBar.GetSkillIDBySlot(1) == 0 or SkillBar.GetSkillIDBySlot(2) == 0 or \
                SkillBar.GetSkillIDBySlot(3) == 0 or SkillBar.GetSkillIDBySlot(4) == 0 or \
                SkillBar.GetSkillIDBySlot(5) == 0 or SkillBar.GetSkillIDBySlot(6) == 0 or \
                SkillBar.GetSkillIDBySlot(7) == 0 or SkillBar.GetSkillIDBySlot(8) == 0:
                self.player_skillbar_load_count += 1
                if self.player_skillbar_load_count > 10:
                    self.Log("Unable to Load Skills")
                    self.InternalStop()
                return False
            
        self.skillBar = self.Kabob_Skillbar()
        return True

    def PutKossInParty(self): 
        if self.leave_party:
            self.pyParty.LeaveParty()
        self.pyParty.AddHero(Heroes.Koss)

    def IsKossInParty(self):
        if not IsHeroInParty(Heroes.Koss):
            self.add_koss_tries += 1

        # If Koss not added after ~5 seconds, fail and end kabob farming.
        if self.add_koss_tries >= 5:
            self.Log("Unable to add Koss to Party!")
            self.InternalStop()
            return True
        
        return False
    
    def KillKoss(self):
        self.RunStarting()
        agent_id = Player.GetAgentID()

        # The echo takes longest, but lasts longest, cast first.
        SkillBar.HeroUseSkill(agent_id, 3, 1)

        # Now flag hero to mesmers and use chant then shout.
        self.pyParty.FlagHero(self.pyParty.GetHeroAgentID(1), -16749, 5382)
        SkillBar.HeroUseSkill(agent_id, 2, 1)
        SkillBar.HeroUseSkill(agent_id, 1, 1)

        maxHp = Agent.GetMaxHealth(Player.GetAgentID())                
        self.player_previous_hp = Agent.GetHealth(Player.GetAgentID()) * maxHp

    def TimeToRunToDrakes(self):
        if not self.kabob_second_timer.IsRunning():
            self.kabob_second_timer.Start()

        if not self.kabob_second_timer.HasElapsed(100):
            return
        
        self.kabob_second_timer.Reset()
                      
        try:
            if Agent.IsDead(Player.GetAgentID()):
                self.FailResign()
                return
                
            # Checking whether the player is stuck
            self.HandleStuck()

            # Run the stay alive script.
            self.StayAliveLoop()

            # Try to follow the path based on pathing points and movement handler.
            Routines.Movement.FollowPath(self.kabob_pathing_move_to_kill_handler, self.movement_Handler)
        except Exception as e:
            Py4GW.Console.Log("Run To Drakes", str(e), Py4GW.Console.MessageType.Error)

    def RunToDrakesDone(self):
        if not self.kabob_step_done_timer.IsRunning():
            self.kabob_step_done_timer.Start()

        if not self.kabob_step_done_timer.HasElapsed(500):
            return False
        
        self.kabob_step_done_timer.Reset()

        pathDone = Routines.Movement.IsFollowPathFinished(self.kabob_pathing_move_to_kill_handler, self.movement_Handler)         
        surrounded = CheckSurrounded(6)
        forceStep = self.ShouldForceTransitionStep()

        return pathDone or surrounded or forceStep or self.player_stuck

    def KillLoopStart(self):
        self.Kill(self.StayAliveLoop())

    # Stay alive using all heal buffs and hos if available
    def StayAliveLoop(self):
        if not self.kabob_stay_alive_timer.IsRunning():
            self.kabob_stay_alive_timer.Start()

        if not self.kabob_stay_alive_timer.HasElapsed(1000):
            return False
        
        self.kabob_stay_alive_timer.Reset()

        try:            
            player_id = Player.GetAgentID()

            if Agent.IsDead(player_id):
                self.FailResign()
                return False
                
            if not CanCast(player_id):
                return False
             
            if self.kabob_killing_staggering_casted and HasBuff(player_id, self.skillBar.staggering):
                return False

            enemies = AgentArray.GetEnemyArray()
            enemies = AgentArray.Filter.ByDistance(enemies, Player.GetXY(), GameAreas.Spellcast)
            enemies = AgentArray.Filter.ByAttribute(enemies, 'IsAlive')

            # Cast stay alive spells if needed.
            maxHp = Agent.GetMaxHealth(player_id)                
            hp = Agent.GetHealth(player_id) * maxHp
            dangerHp = .7 * maxHp

            temp = self.player_previous_hp
            self.player_previous_hp = hp

            if len(enemies) > 0 or self.player_stuck or hp < temp:
                # Cast HOS is available but find enemy in behind if able, otherwise just use since need to heal.
                if self.player_stuck or (self.kabob_ready_to_kill and hp < dangerHp) or (len(enemies) == 0 and hp < temp):
                    if len(enemies) > 0:
                        # If stuck, find enemy behind to cast hos
                        if self.player_stuck:
                            for enemy in enemies:
                                if IsEnemyBehind(enemy):
                                    break
                        # not stuck, just need heal.
                        else:
                            for enemy in enemies:
                                if IsEnemyInFront(enemy):
                                    break

                    if HasEnoughEnergy(self.skillBar.hos) and IsSkillReadyById(self.skillBar.hos):
                        CastSkillByIdAndSlot(self.skillBar.hos, self.skillBar.hos_slot)

                        if self.player_stuck:
                            self.player_stuck_hos_count += 1

                            if self.player_stuck_hos_count > 2:
                                # kill shit then if not already
                                self.kabob_ready_to_kill = True
                                self.Kabob_Routine.jump_to_state_by_name(self.kabob_change_weapon_scythe)
                        return True
                    
                regen_time_remain = 0
                intimidate_time_remain = 0
                sanctity_time_remain = 0
                shards_time_remain = 0 
                                  
                player_buffs = Effects.GetEffects(player_id)

                for buff in player_buffs:
                    if buff.skill_id == self.skillBar.regen:
                        regen_time_remain = buff.time_remaining
                    if buff.skill_id == self.skillBar.intimidating:
                        intimidate_time_remain = buff.time_remaining
                    if buff.skill_id == self.skillBar.sanctity:
                        sanctity_time_remain = buff.time_remaining     
                    if buff.skill_id == self.skillBar.sand_shards:
                        shards_time_remain = buff.time_remaining
                                 
                # Only cast these when waiting for the killing to start.
                if self.Kabob_Routine.get_current_step_name() == self.kabob_waiting_kill_state_name or hp < dangerHp:
                    if intimidate_time_remain < 3000 and HasEnoughEnergy(self.skillBar.intimidating) and IsSkillReadyById(self.skillBar.intimidating):
                        CastSkillByIdAndSlot(self.skillBar.intimidating, self.skillBar.intimidating_slot)
                        return True

                    if sanctity_time_remain < 3000 and HasEnoughEnergy(self.skillBar.sanctity) and IsSkillReadyById(self.skillBar.sanctity):
                        CastSkillByIdAndSlot(self.skillBar.sanctity, self.skillBar.sanctity_slot)
                        return True
                
                if regen_time_remain < 3000 and HasEnoughEnergy(self.skillBar.regen) and IsSkillReadyById(self.skillBar.regen):
                    CastSkillByIdAndSlot(self.skillBar.regen ,self.skillBar.regen_slot)
                    return True 
                
                if not self.kabob_ready_to_kill and shards_time_remain < 5000 and IsSkillReadyById(self.skillBar.sand_shards) and HasEnoughEnergy(self.skillBar.sand_shards) and len(enemies) > 1:
                    CastSkillByIdAndSlot(self.skillBar.sand_shards, self.skillBar.sand_shards_slot)
                    return True
                                    
        except Exception as e:
            Py4GW.Console.Log("StayAlive", str(e), Py4GW.Console.MessageType.Error)
        
        return False

    def Kill(self, stayAliveCasting):
        if not self.kabob_second_timer.IsRunning():
            self.kabob_second_timer.Start()

        if stayAliveCasting or not self.kabob_second_timer.HasElapsed(1000):
            return
        
        self.kabob_second_timer.Reset()

        try:  
            # Start waiting to kill routine. 
            player_id = Player.GetAgentID()            

            if Agent.IsDead(player_id):
                self.FailResign()
                return
            
            if not CanCast(player_id):
                return  

            if (Map.IsMapReady() and not Map.IsMapLoading()):
                if (Map.IsExplorable() and Map.GetMapID() == Mapping.Floodplain_Of_Mahnkelon and Party.IsPartyLoaded()):
                    enemies = AgentArray.GetEnemyArray()
                    enemies = AgentArray.Filter.ByDistance(enemies, Player.GetXY(), GameAreas.Nearby)
                    enemies = AgentArray.Filter.ByAttribute(enemies, 'IsAlive')

                    if len(enemies) == 0:
                        enemies = AgentArray.GetEnemyArray()
                        enemies = AgentArray.Filter.ByDistance(enemies, Player.GetXY(), GameAreas.Earshot)
                        enemies = AgentArray.Filter.ByAttribute(enemies, 'IsAlive')

                        if len(enemies) > 0:
                            if HasEnoughEnergy(self.skillBar.hos) and IsSkillReadyById(self.skillBar.hos):
                                CastSkillByIdAndSlot(self.skillBar.hos, self.skillBar.hos_slot)
                        return
                                                            
                    if not self.kabob_ready_to_kill:
                        if len(enemies) < 7 and not self.player_stuck:
                            return
                        
                        self.kabob_ready_to_kill = True

                        # Use hos so we get them balled up a bit better (sometimes)
                        for enemy in enemies:
                            if IsEnemyInFront(enemy):
                                break

                        if HasEnoughEnergy(self.skillBar.hos) and IsSkillReadyById(self.skillBar.hos):
                            CastSkillByIdAndSlot(self.skillBar.hos, self.skillBar.hos_slot)
                            return
                    
                    # Ensure have damage mitigation up before attacking
                    if len(enemies) > 2 and (not HasBuff(player_id, self.skillBar.intimidating) or not HasBuff(player_id, self.skillBar.sanctity)):
                        return
                    
                    target = Player.GetTargetID()

                    if target not in enemies:
                        target = enemies[0]

                    Player.ChangeTarget(target)
                        
                    if self.kabob_killing_staggering_casted and HasBuff(player_id, self.skillBar.staggering) and IsSkillReadyById(self.skillBar.eremites) and HasEnoughEnergy(self.skillBar.eremites):  
                        self.kabob_killing_staggering_casted = False
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

                    if not self.kabob_killing_staggering_casted and shards_time_remain < 5000 and IsSkillReadyById(self.skillBar.sand_shards) and HasEnoughEnergy(self.skillBar.sand_shards) and len(enemies) > 1:
                        CastSkillByIdAndSlot(self.skillBar.sand_shards, self.skillBar.sand_shards_slot)
                        return
                                            
                    # Get Ready for killing
                    # Need find a way to change weapon set since  sending the change keys is not working for F1-F4
                    # For now assume we're good to go.
                    if not self.kabob_killing_staggering_casted and vos_time_remain < 3000 and IsSkillReadyById(self.skillBar.vos) and HasEnoughEnergy(self.skillBar.vos):   
                        CastSkillByIdAndSlot(self.skillBar.vos, self.skillBar.vos_slot)
                        return
                        
                    if IsSkillReadyById(self.skillBar.eremites) and HasEnoughEnergy(self.skillBar.eremites):
                        if IsSkillReadyById(self.skillBar.staggering) and HasEnoughEnergy(self.skillBar.staggering):
                            self.kabob_killing_staggering_casted = True
                            CastSkillByIdAndSlot(self.skillBar.staggering, self.skillBar.staggering_slot)
                    elif not Agent.IsAttacking(player_id) and not Agent.IsCasting(player_id):
                        # Normal Attack
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
                return True

            return False
        except:
            self.Log("Kill Loop Error", Py4GW.Console.MessageType.Error)

    # If issues comment internals and call super().CanPickUp()
    def CanPickUp(self, agentId, player_id):
        # Check if our item is a kabob first, otherwise let base hangle it.

        item_owner_id = Agent.GetItemAgentOwnerID(agentId)

        if item_owner_id:        
            if item_owner_id != 0 and player_id != 0 and item_owner_id != player_id:
                return False
            
            model = Item.GetModelID(item_owner_id)
            if model == ModelID.Chunk_Of_Drake_Flesh:
                return True
            else:
                return super().CanPickUp(agentId, player_id)
              
        return False
    
    def LootLoopStart(self):
        try:
            if not self.kabob_loot_timer.IsRunning():
                self.kabob_loot_timer.Start()

            if self.kabob_loot_timer.HasElapsed(self.loot_timer_elapsed):                
                self.kabob_loot_timer.Reset()

                # Check if the current item has been picked up.
                if self.current_lootable != 0:
                    test = Agent.GetItemAgentItemID(self.current_lootable)

                    if test != 0:
                        self.current_loot_tries += 1

                        if self.current_loot_tries > 10:
                            self.Log("Loot- 1000 meters away? Frig it.")
                            self.SuccessResign()
                        return  
                    else:
                        self.current_lootable = 0
                
                item = self.GetNearestPickupItem(Player.GetAgentID())

                if item == 0 or item == None:
                    self.current_lootable = 0
                    return                
                
                if self.current_lootable != item:
                    self.current_lootable = item

                item_id = Agent.GetItemAgentItemID(self.current_lootable)
                model = Item.GetModelID(item_id)

                if model == ModelID.Chunk_Of_Drake_Flesh:
                    self.kabob_collected += 1

                Player.Interact(item)
        except Exception as e:
            Py4GW.Console.Log("Loot Loop", f"Error during looting {str(e)}", Py4GW.Console.MessageType.Error)

    def LootLoopComplete(self):
        try:
            if not self.kabob_loot_done_timer.IsRunning():
                self.kabob_loot_done_timer.Start()

            if self.kabob_loot_done_timer.HasElapsed(self.loot_timer_elapsed):
                self.kabob_loot_done_timer.Reset()

                if self.current_lootable == 0 or Inventory.GetFreeSlotCount() == 0:                    
                    self.kabob_runs += 1
                    self.kabob_success += 1
                    return True

        except Exception as e:
            Py4GW.Console.Log("Loot Loop Complete", f"Error during looting {str(e)}", Py4GW.Console.MessageType.Error)
    
        return False
    
    def GetKabobCollected(self):
        return self.kabob_collected

    def GetKabobStats(self):
        return (self.kabob_runs, self.kabob_success)
    
    # Jump back to output pathing if not done collecting
    def CheckKabobRoutineEnd(self):
        global kabob_selected, do_kabob_exchange

        # Don't reset the kabob count
        self.RunEnding()
        self.SoftReset()

        self.kabob_first_after_reset = False

        if not kabob_selected:
            self.Log("Not Farming Kabob - AutoStop")

            if do_kabob_exchange:
                self.Kabob_Routine.jump_to_state_by_name(self.kabob_exchange_Kabobs_routine_end)
            else:
                self.InternalStop()
            return

        if self.kabob_collected < self.main_item_collect:
            # mapping to outpost may have failed OR the threshold was reached. Try to map there and start over.
            if Map.GetMapID() != Mapping.Rilohn_Refuge:
                self.Kabob_Routine.jump_to_state_by_name(self.kabob_travel_state_name)
            else:
                # already at outpost, check slot count, handle inv or continue farm
                if Inventory.GetFreeSlotCount() <= self.default_min_slots:
                    self.UpdateState(self.kabob_inventory_state_name)
                    self.Kabob_Routine.jump_to_state_by_name(self.kabob_inventory_state_name)
                else:
                    self.Kabob_Routine.jump_to_state_by_name(self.kabob_change_weapon_staff)
        elif do_kabob_exchange:
            self.Kabob_Routine.jump_to_state_by_name(self.kabob_exchange_Kabobs_routine_end)
        else:
            self.Log("Kabob Count Matched - AutoStop")
            self.InternalStop()

    def HandleStuck(self):  
        try:
            if (Map.IsExplorable() and Party.IsPartyLoaded()):
                if not self.kabob_stuck_timer.IsRunning():
                    self.kabob_stuck_timer.Start()

                currentStep = self.Kabob_Routine.get_current_step_name()

                playerId = Player.GetAgentID()
                localPosition = Player.GetXY()

                if currentStep == self.kabob_waiting_run_state_name and self.stuckPosition:                
                    if not Agent.IsCasting(playerId) and not Agent.IsKnockedDown(playerId) and not Agent.IsMoving(playerId) or (abs(localPosition[0] - self.stuckPosition[0]) <= 20 and abs(localPosition[1] - self.stuckPosition[1]) <= 20):
                        if self.kabob_stuck_timer.HasElapsed(4000):
                            self.player_stuck = True
                            self.kabob_stuck_timer.Reset()
                    else:                    
                        self.kabob_stuck_timer.Stop()
                        self.player_stuck = False

                self.stuckPosition = localPosition
            else:
                self.kabob_stuck_timer.Stop()
                self.kabob_stuck_timer.Reset()
                self.player_stuck = False
        except Exception as e:
            Py4GW.Console.Log("Handle Stuck", f"Error during checking stuck {str(e)}", Py4GW.Console.MessageType.Error)
  
    def ApplySelections(self, main_item_collect_count, id_items, collect_coins, collect_events, collect_items_white, collect_items_blue, \
                        collect_items_grape, collect_items_gold, collect_dye, sell_items, sell_items_white, \
                        sell_items_blue, sell_items_grape, sell_items_gold, sell_items_green, sell_materials, salvage_items, salvage_items_white, \
                        salvage_items_blue, salvage_items_grape, salvage_items_gold):
        super().ApplySelections(main_item_collect_count, id_items, collect_coins, collect_events, collect_items_white, collect_items_blue, \
                                 collect_items_grape, collect_items_gold, collect_dye, sell_items, sell_items_white, \
                                 sell_items_blue, sell_items_grape, sell_items_gold, sell_items_green, sell_materials, salvage_items, salvage_items_white, \
                                 salvage_items_blue, salvage_items_grape, salvage_items_gold)
        
        self.inventoryRoutine.ApplySelections(idItems=id_items, sellItems=sell_items, sellWhites=sell_items_white,
                                              sellBlues=sell_items_blue, sellGrapes=sell_items_grape, sellGolds=sell_items_gold, sellGreens=sell_items_green,
                                              sellMaterials=sell_materials, salvageItems=salvage_items, salvWhites=salvage_items_white, salvBlue=salvage_items_blue,
                                              salvGrapes=salvage_items_grape, salvGolds=salvage_items_gold)

  ### --- ROUTINE FUNCTIONS --- ###

def GetKabobCollected():
    return kabob_Routine.GetKabobCollected()

def GetKabobData():
    return kabob_Routine.GetKabobStats()

kabob_Window = Kabob_Window(bot_name)
kabob_Routine = Kabob_Farm(kabob_Window)

def ApplyLootAndMerchantSelections():
    global kabob_input
    kabob_Routine.ApplySelections(kabob_input, kabob_Window.id_Items, kabob_Window.collect_coins, kabob_Window.collect_events, kabob_Window.collect_items_white, kabob_Window.collect_items_blue, \
                kabob_Window.collect_items_grape, kabob_Window.collect_items_gold, kabob_Window.collect_dye, kabob_Window.sell_items, kabob_Window.sell_items_white, \
                kabob_Window.sell_items_blue, kabob_Window.sell_items_grape, kabob_Window.sell_items_gold, kabob_Window.sell_items_green, kabob_Window.sell_materials, kabob_Window.salvage_items, kabob_Window.salvage_items_white, \
                kabob_Window.salvage_items_blue, kabob_Window.salvage_items_grape, kabob_Window.salvage_items_gold)

def ApplyKabobConfigSettings(leave_party, soup_input, soup_exchange):
    kabob_Routine.ApplyConfigSettingsOverride(leave_party, soup_input, soup_exchange)

def ApplyKabobInventorySettings(min_slots, min_gold, depo_items, depo_mats):
    kabob_Routine.ApplyInventorySettings(min_slots, min_gold, depo_items, depo_mats)

def StartBot():
    if not kabob_Routine.IsBotRunning():
        ApplyLootAndMerchantSelections()
        # ApplyKabobConfigSettings()
        # ApplyKabobInventorySettings(kabob_Window.minimum_slots)
        kabob_Routine.Start()

def StopBot():
    if kabob_Routine.IsBotRunning():
        kabob_Routine.Stop()

def ResetBot():
    # Stop the main state machine  
    kabob_Routine.Stop()
    kabob_Routine.Reset()

def PrintData():
    kabob_Routine.PrintData()

def GetRunTime():
    return kabob_Routine.GetCurrentRunTime()

def GetAverageRunTime():
    return kabob_Routine.GetAverageTime()

def GetTotalRunTime():
    return kabob_Routine.GetTotalTime()

### --- MAIN --- ###
def main():
    try:
        # Could just put a main timer here and only fire the updates in some interval, but I like more control specific to tasks (eg. Staying Alive, Kill, Loot, etc)
        if Routines.Checks.Map.MapValid():
            if kabob_Window:
                kabob_Window.Show()
            
            if kabob_Routine and kabob_Routine.IsBotRunning():
                kabob_Routine.Update()
                
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