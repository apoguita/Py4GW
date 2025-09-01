   
from Py4GWCoreLib import PyImGui, ImGui, Color
from .LogConsole import LogConsole
from .StatsMgr import RunStatistics
from Py4GWCoreLib import Routines
from Py4GWCoreLib import GLOBAL_CACHE
from Py4GWCoreLib import Profession
from Py4GWCoreLib import IconsFontAwesome5
from Py4GWCoreLib import LootConfig
from Py4GWCoreLib import Range
from Py4GWCoreLib import Item
from Py4GWCoreLib import Agent
from Py4GWCoreLib import ImguiFonts

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .YAVBMain import YAVB

#region OptionsWindow
class YAVB_GUI:

    def __init__(self, parent: "YAVB"):
        self.parent = parent


    def DrawOptionsWindow(self):
        self.parent.option_window_module.initialize()
        border = self.parent.option_window_snapped_border.lower()
        if border == "right":
            snapped_x = self.parent.main_window_pos[0] + self.parent.main_window_size[0] + 1
            snapped_y = self.parent.main_window_pos[1]
        elif border == "left":
            snapped_x = self.parent.main_window_pos[0] - self.option_window_size[0] - 1
            snapped_y = self.parent.main_window_pos[1]
        elif border == "top":
            snapped_x = self.parent.main_window_pos[0]
            snapped_y = self.parent.main_window_pos[1] - self.option_window_size[1] - 1
        elif border == "bottom":
            snapped_x = self.parent.main_window_pos[0]
            snapped_y = self.parent.main_window_pos[1] + self.parent.main_window_size[1] + 1
        else:
            # Fallback to right
            snapped_x = self.parent.main_window_pos[0] + self.parent.main_window_size[0] + 1
            snapped_y = self.parent.main_window_pos[1]

        if self.parent.option_window_snapped:
            PyImGui.set_next_window_pos(snapped_x, snapped_y)
        
        if self.parent.option_window_module.begin():
            if PyImGui.begin_child("YAVB Options Child Window", (300, 250), True, PyImGui.WindowFlags.NoFlag):
                if PyImGui.collapsing_header("Looting Options"):
                    PyImGui.text_wrapped("Looting is handled by the Looting Manager Widget, configure it there.")
                PyImGui.separator()
                if PyImGui.collapsing_header("ID & Salvage Options"):
                    PyImGui.text_wrapped("ID & Salvage is handled by AutoHandler Module of the Inventory+ Widget. Configure it there.")
                if PyImGui.collapsing_header("Merchant Options"):
                    PyImGui.text_wrapped("After inventory AutoHandler has finished, all remaining items are sent to the Merchant for id/selling.")
                    PyImGui.separator()
                    PyImGui.push_item_width(100)
                    self.parent.identification_kits_restock = PyImGui.input_int("ID Kits to Restock", self.parent.identification_kits_restock)
                    ImGui.show_tooltip("ID Kits to Restock")
                    self.parent.salvage_kits_restock = PyImGui.input_int("Salvage Kits to Restock", self.parent.salvage_kits_restock)
                    ImGui.show_tooltip("Salvage Kits to Restock")
                    self.parent.keep_empty_inventory_slots = PyImGui.input_int("Keep Empty Inventory Slots", self.parent.keep_empty_inventory_slots)
                    ImGui.show_tooltip("Keep Empty Inventory Slots")
                    PyImGui.pop_item_width()
                    
                if PyImGui.collapsing_header("Bot Options"):
                    self.parent.use_cupcakes = PyImGui.checkbox("Use Cupcakes", self.parent.use_cupcakes)
                    ImGui.show_tooltip("Withdraw 1 cupcake from inventory and use it for traversing Bjora Marches")
                    self.parent.use_pumpkin_cookies = PyImGui.checkbox("Use Pumpkin Cookies", self.parent.use_pumpkin_cookies)
                    ImGui.show_tooltip("Use Pumpkin Cookies for clearing Death Penalty in case of death.")
                    self.parent.pumpkin_cookies_restock = PyImGui.input_int("Pumpkin Cookies Restock", self.parent.pumpkin_cookies_restock)
                    ImGui.show_tooltip("Number of Pumpkin Cookies to keep in inventory.")
                
                
                PyImGui.end_child()
            
            self.parent.option_window_module.process_window()
            self.option_window_pos = PyImGui.get_window_pos()
            self.option_window_size = PyImGui.get_window_size() 
        self.parent.option_window_module.end()

#endregion

     
   
#region MainWindow
    def DrawMainWindow(self):
        self.parent.window_module.initialize()
        if self.parent.window_module.begin():
            if PyImGui.begin_menu_bar():
                # Direct clickable item on the menu bar
                if PyImGui.begin_menu("File"):
                    # Items inside the File menu
                    if PyImGui.menu_item("Save Config"):
                        self.parent.save_config()
                        self.parent.LogMessage("Configuration saved", "", LogConsole.LogSeverity.SUCCESS)
                    if PyImGui.menu_item("Load Config"):
                        self.parent.load_config()
                        self.parent.LogMessage("Configuration loaded", "", LogConsole.LogSeverity.SUCCESS)
                    PyImGui.end_menu()
                if PyImGui.begin_menu("Options"):
                    self.parent.option_window_visible = PyImGui.checkbox("Show window", self.parent.option_window_visible)
                    self.parent.option_window_snapped = PyImGui.checkbox("Snapped", self.parent.option_window_snapped)
                    if self.parent.option_window_snapped:
                        snap_directions = ["Right", "Left", "Bottom"]
                        current_index = snap_directions.index(self.parent.option_window_snapped_border)
                        selected_index = PyImGui.combo("Snap Direction", current_index, snap_directions)
                        self.parent.option_window_snapped_border = snap_directions[selected_index]
                    PyImGui.end_menu()

                # Dropdown menu called "Console"
                if PyImGui.begin_menu("Console"):
                    # Items inside the Console submenu
                    self.parent.console_visible = PyImGui.checkbox("Show Console", self.parent.console_visible)
                    prev_value = self.parent.console_log_to_file
                    self.parent.console_log_to_file = PyImGui.checkbox("Log to File", self.parent.console_log_to_file)
                    if prev_value != self.parent.console_log_to_file:
                        self.parent.console.SetLogToFile(self.parent.console_log_to_file)
                    ImGui.show_tooltip("Feature WIP, not implemented yet.")
                    
                    prev_value = self.parent.detailed_logging
                    self.parent.detailed_logging = PyImGui.checkbox("Detailed Logging", self.parent.detailed_logging)
                    if prev_value != self.parent.detailed_logging:
                        self.parent.LogDetailedMessage("Detailed logging",f"{'ENABLED' if self.parent.detailed_logging else 'DISABLED'}.", LogConsole.LogSeverity.INFO)
                    ImGui.show_tooltip("Will output Extra Info to the YAVB Console,\nWill output Full Logging to the Py4GWConsole.")
                    
                    prev_value = self.parent.console_snapped
                    self.parent.console_snapped = PyImGui.checkbox("Snapped", self.parent.console_snapped)
                    if prev_value != self.parent.console_snapped:
                        self.parent.console.SetSnapped(self.parent.console_snapped, self.parent.console_snapped_border)
                    
                    if self.parent.console_snapped:
                        prev_value = self.parent.console_snapped_border
                        snap_directions = ["Right", "Left", "Bottom"]
                        current_index = snap_directions.index(self.parent.console_snapped_border)
                        selected_index = PyImGui.combo("Snap Direction", current_index, snap_directions)
                        self.parent.console_snapped_border = snap_directions[selected_index]
                        if prev_value != self.parent.console_snapped_border:
                            self.parent.console.SetSnapped(self.parent.console_snapped, self.parent.console_snapped_border)

                    PyImGui.end_menu()

                PyImGui.end_menu_bar()
            
            
            child_width = 300
            child_height = 275
            if PyImGui.begin_child("YAVB Child Window",(child_width, child_height), True, PyImGui.WindowFlags.NoFlag):
                table_flags = PyImGui.TableFlags.RowBg | PyImGui.TableFlags.BordersOuterH
                if PyImGui.begin_table("YAVBtoptable", 2, table_flags):
                    iconwidth = 64
                    PyImGui.table_setup_column("Icon", PyImGui.TableColumnFlags.WidthFixed, iconwidth)
                    PyImGui.table_setup_column("titles", PyImGui.TableColumnFlags.WidthFixed, child_width - iconwidth)
                    PyImGui.table_next_row()
                    PyImGui.table_set_column_index(0)
                    ImGui.DrawTexture(self.parent.icon, width=64, height=64)
                    PyImGui.table_set_column_index(1)
                    if PyImGui.begin_table("YAVB Info", 1, PyImGui.TableFlags.NoFlag):
                        PyImGui.table_next_row()
                        PyImGui.table_set_column_index(0)
                        ImGui.push_font("Regular", 20)
                        PyImGui.push_style_color(PyImGui.ImGuiCol.Text, Color(255, 255, 0, 255).to_tuple_normalized())
                        #PyImGui.text_scaled(f"{self.parent.GetBanner()}", Color(255, 255, 0, 255).to_tuple_normalized(), 1.4)
                        PyImGui.text(f"{self.parent.GetBanner()}")
                        PyImGui.pop_style_color(1)
                        ImGui.pop_font()
                        PyImGui.table_next_row()
                        PyImGui.table_set_column_index(0)
                        PyImGui.text_wrapped(f"{self.parent.GetTagLine()}")
                        PyImGui.end_table()
                    PyImGui.end_table()
                    
                    map_valid = Routines.Checks.Map.MapValid()
                    if map_valid:
                        self.parent.primary_profession, self.secondary_profession = GLOBAL_CACHE.Agent.GetProfessionIDs(GLOBAL_CACHE.Player.GetAgentID())
                        self.parent.prof_supported = self.parent.IsProfessionSupported(self.parent.primary_profession)
                    
                    
                    if not self.parent.prof_supported:
                        if PyImGui.begin_table("YAVB maintable", 1, PyImGui.TableFlags.NoFlag):
                            PyImGui.table_next_row()
                            PyImGui.table_set_column_index(0)
                            color = Color(250, 100, 0, 255).to_tuple_normalized()

                            PyImGui.push_style_color(PyImGui.ImGuiCol.Text, color)
                            PyImGui.text_wrapped(
                                f"Your profession {Profession(self.parent.primary_profession).name.upper()} is not currently supported by this script.\n\n"
                                "Switch to a character with one of the following supported professions:"
                            )
                            PyImGui.pop_style_color(1)
                            for prof_id in self.parent.supported_professions.keys():
                                if not prof_id.isdigit():
                                    continue  # Skip non-integer keys

                                prof = Profession(int(prof_id))
                                PyImGui.text(f"{prof.name.upper()}")

                                
                                
                            PyImGui.end_table()
                    else:
                        if PyImGui.begin_table("YAVB maintable", 1, PyImGui.TableFlags.NoFlag):
                            PyImGui.table_next_row()
                            PyImGui.table_set_column_index(0)
                            if PyImGui.begin_tab_bar("YAVB Tabs"):
                                if PyImGui.begin_tab_item("Main"):
                                    icon = IconsFontAwesome5.ICON_CIRCLE
                                    if self.parent.script_running and not self.script_paused:
                                        icon = IconsFontAwesome5.ICON_PAUSE_CIRCLE
                                    if self.parent.script_running and self.script_paused:
                                        icon = IconsFontAwesome5.ICON_PLAY_CIRCLE
                                    if not self.parent.script_running:
                                        icon = IconsFontAwesome5.ICON_PLAY_CIRCLE
                                        
                                    if PyImGui.button(icon +  "##Playbutton"):
                                        if self.parent.script_running:
                                            if self.script_paused:
                                                self.parent.FSM.resume()
                                                self.script_paused = False
                                                self.parent.LogDetailedMessage("Script resumed", "", LogConsole.LogSeverity.INFO)
                                                self.parent.state = "Running"
                                            else:
                                                self.parent.FSM.pause()
                                                self.script_paused = True
                                                self.parent.LogDetailedMessage("Script paused", "", LogConsole.LogSeverity.INFO) 
                                                self.parent.state = "Paused"
                                        else:
                                            self.parent.script_running = True
                                            self.script_paused = False
                                            
                                            self.parent.LogDetailedMessage("Script started", "", LogConsole.LogSeverity.INFO)
                                            self.parent.state = "Running"
                                            
                                            self.parent.FSM.restart()
                                            
                                    PyImGui.same_line(0,-1)
                                    
                                    #change button to grey if script is not running
                                    if not self.parent.script_running:
                                        PyImGui.push_style_color(PyImGui.ImGuiCol.Button, Color(50, 50, 50, 255).to_tuple_normalized())
                                        PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonHovered, Color(70, 70, 70, 255).to_tuple_normalized())
                                        PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonActive, Color(90, 90, 90, 255).to_tuple_normalized())
                                        PyImGui.push_style_color(PyImGui.ImGuiCol.Text, Color(70, 70, 70, 255).to_tuple_normalized())
                                        
                                    
                                    
                                    if PyImGui.button(IconsFontAwesome5.ICON_STOP_CIRCLE + "##Stopbutton"):
                                        if self.parent.script_running:
                                            self.parent.script_running = False
                                            self.parent.script_paused = False
                                            self.parent.in_killing_routine = False
                                            self.parent.finished_routine = False
                                            if self.parent.build is not None:
                                                build = self.parent.build  # now Pylance sees it as non-Optional
                                                build.SetKillingRoutine(self.parent.in_killing_routine)
                                                build.SetRoutineFinished(self.parent.finished_routine)
                                            self.parent.LogMessage("Script stopped", "", LogConsole.LogSeverity.INFO)
                                            self.parent.state = "Idle"
                                            self.parent.FSM.stop()
                                            
                                            GLOBAL_CACHE.Coroutines.clear()  # Clear all coroutines


                                    if not self.parent.script_running:
                                        PyImGui.pop_style_color(4)
                                        
                                    PyImGui.same_line(0,-1)
                                    PyImGui.text(f"State: {self.parent.state}")
                                    PyImGui.separator()
                                    PyImGui.text("Step Progress")
                                    PyImGui.push_item_width(child_width - 10)
                                    PyImGui.progress_bar(self.parent.state_percentage, (child_width - 10), 0, f"{self.parent.state_percentage * 100:.2f}%")
                                    PyImGui.pop_item_width()
                                    PyImGui.separator()
                                    PyImGui.text("Overall Progress")
                                    PyImGui.push_item_width(child_width - 10)
                                    PyImGui.progress_bar(self.parent.overall_progress, (child_width - 10), 0, f"{self.parent.overall_progress * 100:.2f}%")   
                                    PyImGui.pop_item_width()
                                                
                                    PyImGui.end_tab_item()
                                
                                if PyImGui.begin_tab_item("Statistics"):
                                    PyImGui.text("Statistics")
                                    PyImGui.separator()
                                    
                                    if self.parent.running_to_jaga:
                                        current_run = self.parent.run_to_jaga_stats.GetCurrentRun()
                                    else:
                                        current_run = self.parent.farming_stats.GetCurrentRun()
                                     
                                    def format_duration(seconds: float) -> str:
                                        minutes = int(seconds // 60)
                                        secs = int(seconds % 60)
                                        millis = int((seconds - int(seconds)) * 1000)
                                        return f"{minutes:02}:{secs:02}:{millis:03}"  
                                     
                                    if not self.parent.current_run_node:
                                        self.parent.current_run_node = RunStatistics.RunNode()
                                        
                                    if current_run:
                                        self.parent.current_run_node = current_run
                                        
                                    current_run = self.parent.current_run_node 
                                    PyImGui.text(f"Run Start Time: {current_run.start_time.strftime('%H:%M:%S')}")
                                    PyImGui.text(f"Run Duration: {format_duration(current_run.GetRunDuration())}")
                                    quickest = self.parent.farming_stats.GetQuickestRun()
                                    run_time = quickest.GetRunDuration() if quickest else 0
                                    PyImGui.text(f"Quickest Run: {format_duration(run_time)}")
                                    longest = self.parent.farming_stats.GetLongestRun()
                                    run_time = longest.GetRunDuration() if longest else 0
                                    PyImGui.text(f"Longest Run: {format_duration(run_time)}")
                                    avg_duration = self.parent.farming_stats.GetAverageRunDuration()
                                    PyImGui.text(f"Average Run Duration: {format_duration(avg_duration)}")
                                    PyImGui.text(f"Total Runs: {self.parent.farming_stats.GetTotalRuns()}")
                                    PyImGui.text(f"Failed Runs: {self.parent.farming_stats.GetTotalFailures()}")
                                    PyImGui.text(f"Run Effectivity: {self.parent.farming_stats.GetRuneffectivity():.2f}%")
                                    PyImGui.text(f"Kill Effectivity: {self.parent.farming_stats.GetKillEffectivity():.2f}%")
                                    PyImGui.text(f"Avg Kills on Success: {self.parent.farming_stats.GetAverageKillsOnSuccess():.2f}")
                                    
                                    PyImGui.end_tab_item()
                                        
                                if PyImGui.begin_tab_item("Debug"):
                                    PyImGui.text("Debug Information")
                                    PyImGui.separator()
                                    loot_singleton = LootConfig()
                                    PyImGui.text(f"white_config = {loot_singleton.loot_whites}")

                                    filtered_agent_ids = loot_singleton.GetfilteredLootArray(distance=Range.Earshot.value, multibox_loot=False, allow_unasigned_loot=True)

                                    PyImGui.separator()
                                    for agent_id in filtered_agent_ids:
                                        item_data = Agent.GetItemAgent(agent_id)
                                        item_id = item_data.item_id
                                        model_id = Item.GetModelID(item_id)
                                        name = GLOBAL_CACHE.Agent.GetName(agent_id)
                                        PyImGui.text(f"agent_id: {agent_id}, name: {name}, item_id: {item_id}, model_id: {model_id}")

                                    PyImGui.end_tab_item()
                                    
                                PyImGui.end_tab_bar()   
                            PyImGui.end_table()
                        
                PyImGui.end_child()
            
            self.parent.window_module.process_window()            
        self.parent.window_module.end()
#endregion