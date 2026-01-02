import Py4GW
from typing import Optional, Union
import math
import random
import json
import os
from Py4GWCoreLib import ThrottledTimer
from Py4GWCoreLib import PyImGui, ImGui, Color
from Py4GWCoreLib import FSM
from Py4GWCoreLib import AutoInventoryHandler
from Py4GWCoreLib import IniHandler
from Py4GWCoreLib import GLOBAL_CACHE
from Py4GWCoreLib import ConsoleLog
from Py4GWCoreLib.Builds import ShadowFormAssassinVaettir, ShadowFormMesmerVaettir



from .ProgressTracker import ProgressTracker
from .LogConsole import LogConsole
from .StatsMgr import RunStatistics
from .FSMHelpers import _FSM_Helpers
from .FSM import YAVB_FSM
from .GUI import YAVB_GUI
from Py4GWCoreLib import Routines
from Py4GWCoreLib import AgentArray
from Py4GWCoreLib import AgentModelID
from Py4GWCoreLib import Range
from Py4GWCoreLib import Map


class YAVB:
    def __init__(self):
        self.name = "YAVB"
        self.version = "1.0"
        self.author = "Apo"
        self.description = "Yet Another Vaettir Bot"
        base_path = os.path.dirname(__file__)
        self.icon = os.path.join(base_path, "resources", "yavb_mascot.png")
        self.tagline_file = os.path.join(base_path, "Config", "YAVB_taglines.json")
        self.ini_file = os.path.join(base_path, "Config", "YAVB.ini")
        #line randomizer
        self.prhase_throttled_timer = ThrottledTimer()
        self.current_tagline = ""
        
        #title banner
        self.banner_string = self.description + " by " + self.author + "   -   "
        self.banner_color = Color(255, 255, 0, 255)  # Yellow color
        self.banner_font_size = 1.4
        self.banner_throttled_timer = ThrottledTimer(250)
        self.banner_index = 0
        
        #build
        self.build: Optional[Union[ShadowFormAssassinVaettir, ShadowFormMesmerVaettir]] = None
        self.supported_professions = {}
    
        #merchant options
        self.identification_kits_restock = 2
        self.salvage_kits_restock = 5
        self.keep_empty_inventory_slots = 2
        
        #bot options
        self.detailed_logging = False
        self.script_running = False
        self.script_paused = False
        self.state = "Idle"  # Current state of the bot
        self.state_percentage = 0.0  # Percentage of completion for the current state
        self.overall_progress = 0.0  # Overall progress of the bot
        self.progress_tracker = ProgressTracker()
        self.FSM = FSM("YAVB FSM", log_actions=False)
        self.FSM_Helpers = _FSM_Helpers(self)
        self.FSM_Handler = YAVB_FSM(self)
        
        #UI checks
        self.GUI = YAVB_GUI(self)
        self.primary_profession = 0 #default to prevent crashes
        self.secondary_profession = 0 #default to prevent crashes
        self.prof_supported = False
        
        #window vars
        self.window_flags = PyImGui.WindowFlags(
            PyImGui.WindowFlags.AlwaysAutoResize | 
            PyImGui.WindowFlags.MenuBar
        )
        self.main_window_pos = (100, 100)  # fallback default
        self.main_window_size = (400, 300) # fallback default
        self.option_window_pos = (100, 100)  # fallback default
        self.option_window_size = (300, 250)  # fallback default
        self.console_pos = (100, 100)  # fallback default
        self.console_size = (400, 300)  # fallback default
        #option window
        self.option_window_visible = False
        self.option_window_snapped = True
        self.option_window_snapped_border = "Bottom"
        #Console
        self.console_visible = False
        self.console_snapped = True
        self.console_snapped_border = "Right"
        self.console_log_to_file = False
        
        self.console = LogConsole(
            module_name="YAVB Console",
            window_pos=self.main_window_pos,
            window_size=self.main_window_size,
            is_snapped=self.option_window_snapped, 
            log_to_file=False
        )
        
        #bot behavior
        self.inventory_handler = AutoInventoryHandler()
        self.use_cupcakes = False
        self.use_pumpkin_cookies = False
        self.pumpkin_cookies_restock = 4
        self.stuck_counter = 0
        self.stuck_timer = ThrottledTimer(5000)  
        self.movement_check_timer = ThrottledTimer(3000) 
        self.old_player_position = (0, 0)
        self.running_to_jaga = False
        self.in_killing_routine = False
        self.finished_routine = False
        self.in_waiting_routine = False
        self.ini_handler = IniHandler(self.ini_file)
        
        #statistics
        self.run_to_jaga_stats = RunStatistics()
        self.farming_stats = RunStatistics()
        self.current_run_node: Optional[RunStatistics.RunNode] = None
        
        
        self.load_config()
        
        # Initialize the main window module

        
        self.window_module = ImGui.WindowModule(
            module_name=self.name,
            window_name=f"{self.name} {self.version} by {self.author}",
            window_pos=self.main_window_pos,
            window_size=self.main_window_size,
            window_flags=self.window_flags,
            
        )
        
        self.option_window_module = ImGui.WindowModule(
            module_name=f"{self.name} Options",
            window_name=f"{self.name} Options",
            window_flags= PyImGui.WindowFlags(
                PyImGui.WindowFlags.AlwaysAutoResize)
            )
        
        
        self.console.SetSnapped(self.console_snapped, self.console_snapped_border)
        self.console.SetWindowPosition(self.console_pos)
        self.console.SetWindowSize(self.console_size)
        self.console.SetMainWindowPosition(self.main_window_pos)
        self.console.SetMainWindowSize(self.main_window_size)
        self.console.SetLogToFile(self.console_log_to_file)
        
        self.LONGEYES_LEDGE = Map.GetMapIDByName("Longeyes Ledge")
        self.BJORA_MARCHES = Map.GetMapIDByName("Bjora Marches")
        self.JAGA_MORAINE = Map.GetMapIDByName("Jaga Moraine")
        
        self.FSM_Handler._initialize_fsm()
        
        self.console.LogMessage("YAVB initialized", "", LogConsole.LogSeverity.SUCCESS)
        
    def LogMessage(self, message: str, extra_info: Optional[str] = None, severity: LogConsole.LogSeverity = LogConsole.LogSeverity.INFO):
        """Log a message to the console."""
        if not self.console:
            return
        self.console.LogMessage(message, extra_info, severity)

        match severity:
            case LogConsole.LogSeverity.INFO:
                console_severity = Py4GW.Console.MessageType.Info
            case LogConsole.LogSeverity.WARNING:
                console_severity = Py4GW.Console.MessageType.Warning
            case LogConsole.LogSeverity.ERROR:
                console_severity = Py4GW.Console.MessageType.Error
            case LogConsole.LogSeverity.CRITICAL:
                console_severity = Py4GW.Console.MessageType.Performance
            case LogConsole.LogSeverity.SUCCESS:
                console_severity = Py4GW.Console.MessageType.Success
            case _:
                console_severity = Py4GW.Console.MessageType.Info
            
        ConsoleLog(f"{self.name}", f"{message} - {extra_info}", console_severity,log= self.detailed_logging)
        
    def LogDetailedMessage(self, message: str, extra_info: Optional[str] = None, severity: LogConsole.LogSeverity = LogConsole.LogSeverity.INFO):
        if self.detailed_logging:
            """Log a detailed message to the console."""
            self.LogMessage(message, extra_info, severity)

    def save_config(self):
        ih = self.ini_handler

        # Main Window
        ih.write_key("MainWindow", "pos_x", self.main_window_pos[0])
        ih.write_key("MainWindow", "pos_y", self.main_window_pos[1])
        ih.write_key("MainWindow", "size_x", self.main_window_size[0])
        ih.write_key("MainWindow", "size_y", self.main_window_size[1])

        # Option Window
        ih.write_key("OptionWindow", "pos_x", self.option_window_pos[0])
        ih.write_key("OptionWindow", "pos_y", self.option_window_pos[1])
        ih.write_key("OptionWindow", "size_x", self.option_window_size[0])
        ih.write_key("OptionWindow", "size_y", self.option_window_size[1])
        ih.write_key("OptionWindow", "visible", self.option_window_visible)
        ih.write_key("OptionWindow", "snapped", self.option_window_snapped)
        ih.write_key("OptionWindow", "snapped_border", self.option_window_snapped_border)

        # Console
        ih.write_key("Console", "pos_x", self.console_pos[0])
        ih.write_key("Console", "pos_y", self.console_pos[1])
        ih.write_key("Console", "size_x", self.console_size[0])
        ih.write_key("Console", "size_y", self.console_size[1])
        ih.write_key("Console", "visible", self.console_visible)
        ih.write_key("Console", "snapped", self.console_snapped)
        ih.write_key("Console", "snapped_border", self.console_snapped_border)
        ih.write_key("Console", "log_to_file", self.console_log_to_file)
        ih.write_key("Console", "detailed_logging", self.detailed_logging)

        #Merchant
        ih.write_key("Merchant", "identification_kits_restock", self.identification_kits_restock)
        ih.write_key("Merchant", "salvage_kits_restock", self.salvage_kits_restock)
        ih.write_key("Merchant", "keep_empty_inventory_slots", self.keep_empty_inventory_slots)
        
        ih.write_key("BotConfigs", "use_cupcakes", self.use_cupcakes)
        ih.write_key("BotConfigs", "use_pumpkin_cookies", self.use_pumpkin_cookies)
        ih.write_key("BotConfigs", "pumpkin_cookies_restock", self.pumpkin_cookies_restock)



    def load_config(self):
        ih = self.ini_handler
        
        ConsoleLog("debug", "Loading configuration from INI file", log=True)

        # Main Window
        self.main_window_pos = (
            ih.read_float("MainWindow", "pos_x", self.main_window_pos[0]),
            ih.read_float("MainWindow", "pos_y", self.main_window_pos[1]),
        )
        self.main_window_size = (
            ih.read_float("MainWindow", "size_x", self.main_window_size[0]),
            ih.read_float("MainWindow", "size_y", self.main_window_size[1]),
        )

        # Option Window
        self.option_window_pos = (
            ih.read_float("OptionWindow", "pos_x", self.option_window_pos[0]),
            ih.read_float("OptionWindow", "pos_y", self.option_window_pos[1]),
        )
        self.option_window_size = (
            ih.read_float("OptionWindow", "size_x", self.option_window_size[0]),
            ih.read_float("OptionWindow", "size_y", self.option_window_size[1]),
        )
        self.option_window_visible = ih.read_bool("OptionWindow", "visible", self.option_window_visible)
        self.option_window_snapped = ih.read_bool("OptionWindow", "snapped", self.option_window_snapped)
        self.option_window_snapped_border = ih.read_key("OptionWindow", "snapped_border", self.option_window_snapped_border)

        # Console
        self.console_pos = (
            ih.read_float("Console", "pos_x", self.console_pos[0]),
            ih.read_float("Console", "pos_y", self.console_pos[1]),
        )
        self.console_size = (
            ih.read_float("Console", "size_x", self.console_size[0]),
            ih.read_float("Console", "size_y", self.console_size[1]),
        )
        self.console_visible = ih.read_bool("Console", "visible", self.console_visible)
        self.console_snapped = ih.read_bool("Console", "snapped", self.console_snapped)
        self.console_snapped_border = ih.read_key("Console", "snapped_border", self.console_snapped_border)
        self.console_log_to_file = ih.read_bool("Console", "log_to_file", self.console_log_to_file)
        self.detailed_logging = ih.read_bool("Console", "detailed_logging", self.detailed_logging)
        
        if self.detailed_logging:
            self.LogMessage("Detailed logging", "ENABLED", LogConsole.LogSeverity.INFO)
        
        #Merchant
        self.identification_kits_restock = ih.read_int("Merchant", "identification_kits_restock", self.identification_kits_restock)
        self.salvage_kits_restock = ih.read_int("Merchant", "salvage_kits_restock", self.salvage_kits_restock)
        self.keep_empty_inventory_slots = ih.read_int("Merchant", "keep_empty_inventory_slots", self.keep_empty_inventory_slots)
        
        self.supported_professions = {
                k: v for k, v in ih.list_keys("SupportedProfessions").items()
                if k.isdigit()
            }
        
        #Bot configs
        self.use_cupcakes = ih.read_bool("BotConfigs", "use_cupcakes", self.use_cupcakes)
        self.use_pumpkin_cookies = ih.read_bool("BotConfigs", "use_pumpkin_cookies", self.use_pumpkin_cookies)
        self.pumpkin_cookies_restock = ih.read_int("BotConfigs", "pumpkin_cookies_restock", self.pumpkin_cookies_restock)
        
    def SetCurrentStep(self, step_name: str, step_weight: float = 1.0):
        """
        Set the current step in the progress tracker.
        This will finalize the previous step and start a new one.
        """
        self.progress_tracker.set_step(step_name, step_weight)
        self.state = self.progress_tracker.get_step_name()
        self.state_percentage = 0.0
        self.overall_progress = self.progress_tracker.get_overall_progress()       

    def AdvanceProgress(self, percent: float):
        """
        Advance the progress of the current step.
        Percent should be between 0.0 and 1.0.
        """
        if percent < 0.0 or percent > 1.0:
            percent = max(0.0, min(percent, 1.0))  # Clamp to valid range
        
        self.progress_tracker.update_progress(percent)
        self.state_percentage = self.progress_tracker.state_percentage
        self.overall_progress = self.progress_tracker.get_overall_progress()

    def ResetCurrentProgress(self):
        """
        Reset the current step's progress to 0%.
        """
        self.progress_tracker.reset()
        self.state_percentage = 0.0
        self.overall_progress = self.progress_tracker.get_overall_progress()


#region Stuck
    def HandleStuckBjoraMarches(self):
        while True:
            if not Routines.Checks.Map.MapValid():
                yield from Routines.Yield.wait(1000)  # Wait for map to be valid
                
            if not self.script_running:
                return
            
            if self.script_paused:
                yield from Routines.Yield.wait(1000)
                continue
                
            if GLOBAL_CACHE.Agent.IsDead(GLOBAL_CACHE.Player.GetAgentID()):
                return
            
            if self.in_waiting_routine:
                yield from Routines.Yield.wait(1000)  # Wait for waiting routine to finish
                continue
            
            if self.finished_routine:
                self.stuck_counter = 0
                
            if self.current_run_node and self.current_run_node.GetRunDuration() > 30000:
                self.LogMessage("Stuck Detection", "Current run node is taking too long, resetting.", LogConsole.LogSeverity.WARNING)
                self.stuck_counter = 0
                yield from self.FSM_Helpers._reset_execution()
                continue


            if Map.GetMapID() == self.BJORA_MARCHES:
                if self.stuck_timer.IsExpired():
                    GLOBAL_CACHE.Player.SendChatCommand("stuck")
                    self.stuck_timer.Reset()

                if self.movement_check_timer.IsExpired():
                    current_player_pos = GLOBAL_CACHE.Player.GetXY()
                    if self.old_player_position == current_player_pos:
                        self.LogMessage("Stuck Detection", "Player is stuck, sending stuck command.", LogConsole.LogSeverity.WARNING)
                        GLOBAL_CACHE.Player.SendChatCommand("stuck")
                        player_pos = GLOBAL_CACHE.Player.GetXY() #(x,y)
                        facing_direction = GLOBAL_CACHE.Agent.GetRotationAngle(GLOBAL_CACHE.Player.GetAgentID())
                        left_angle = facing_direction + math.pi / 2
                        distance = 200
                        offset_x = math.cos(left_angle) * distance
                        offset_y = math.sin(left_angle) * distance

                        sidestep_pos = (player_pos[0] + offset_x, player_pos[1] + offset_y)
                        for i in range(3):
                            GLOBAL_CACHE.Player.Move(sidestep_pos[0], sidestep_pos[1])
                        self.stuck_timer.Reset()
                    else:
                        self.old_player_position = current_player_pos
                        
                    self.movement_check_timer.Reset()
                
                build = self.build or ShadowFormAssassinVaettir()   
                yield from build.CastShroudOfDistress()
                    
                agent_array = AgentArray.GetEnemyArray()
                agent_array = AgentArray.Filter.ByCondition(agent_array, lambda agent: GLOBAL_CACHE.Agent.GetModelID(agent) in (AgentModelID.FROZEN_ELEMENTAL.value, AgentModelID.FROST_WURM.value))
                agent_array = AgentArray.Filter.ByDistance(agent_array, GLOBAL_CACHE.Player.GetXY(), Range.Spellcast.value)
                if len(agent_array) > 0:
                    yield from build.DefensiveActions()  
            else:
                return  # Exit the loop if not in Bjora Marches
                     
            yield from Routines.Yield.wait(500)
            
    def HandleStuckJagaMoraine(self):
        while True:
            if not Routines.Checks.Map.MapValid():
                yield from Routines.Yield.wait(1000)  # Wait for map to be valid
            
            if not self.script_running:
                return
            
            if self.script_paused:
                yield from Routines.Yield.wait(1000)
                continue
                
            if GLOBAL_CACHE.Agent.IsDead(GLOBAL_CACHE.Player.GetAgentID()):
                return
            
            if self.current_run_node and self.current_run_node.GetRunDuration() > 30000:
                self.LogMessage("Stuck Detection", "Current run node is taking too long, resetting.", LogConsole.LogSeverity.WARNING)
                self.stuck_counter = 0
                yield from self.FSM_Helpers._reset_execution()
                continue
              
            build = self.build or ShadowFormAssassinVaettir() 
            if self.in_waiting_routine:
                self.stuck_counter = 0
                build.SetStuckCounter(self.stuck_counter)
                self.stuck_timer.Reset()
                yield from Routines.Yield.wait(1000)
                continue
                
            if self.finished_routine:
                self.stuck_counter = 0
                build.SetStuckCounter(self.stuck_counter)
                self.stuck_timer.Reset()
                yield from Routines.Yield.wait(1000)
                continue
            
            if self.in_killing_routine:
                self.stuck_counter = 0
                build.SetStuckCounter(self.stuck_counter)
                self.stuck_timer.Reset()
                yield from Routines.Yield.wait(1000)
                continue

            if Map.GetMapID() == self.JAGA_MORAINE:
                if self.stuck_timer.IsExpired():
                    GLOBAL_CACHE.Player.SendChatCommand("stuck")
                    self.stuck_timer.Reset()
                  
                if self.movement_check_timer.IsExpired():
                    current_player_pos = GLOBAL_CACHE.Player.GetXY()
                    if self.old_player_position == current_player_pos:
                        self.LogMessage("Stuck Detection", "Player is stuck, sending stuck command.", LogConsole.LogSeverity.WARNING)
                        GLOBAL_CACHE.Player.SendChatCommand("stuck")
                        self.stuck_counter += 1
                        build.SetStuckCounter(self.stuck_counter)
                        self.stuck_timer.Reset()
                    else:
                        self.old_player_position = current_player_pos
                        self.stuck_counter = 0
                        
                    self.movement_check_timer.Reset()
                    
                if self.stuck_counter >= 10:
                    self.LogMessage("Stuck Detection", "Unrecoverable stuck detected, resetting.", LogConsole.LogSeverity.ERROR)
                    self.stuck_counter = 0
                    build.SetStuckCounter(self.stuck_counter)
                    yield from self.FSM_Helpers._reset_execution()

            else:
                return  # Exit the loop if not in Bjora Marches
                     
            yield from Routines.Yield.wait(500)

    
    def IsProfessionSupported(self, profession_id: int) -> bool:
        return str(profession_id) in self.supported_professions
        

#endregion


    #region LineRandomizer
    def _randomize_throttle_timer(self):
        new_time = random.randint(30000, 90000)  # milliseconds
        self.prhase_throttled_timer.SetThrottleTime(new_time)
        self.prhase_throttled_timer.Reset()
        
    def _load_taglines(self, path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Failed to load taglines: {e}")
            return []
    
    def _get_random_tagline(self):
        with open(self.tagline_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        taglines = data.get("taglines", [])
        if not taglines:
            return "Why are you reading this? wheres the config file?."
        return random.choice(taglines)
     
    def GetTagLine(self)-> str:
        if self.prhase_throttled_timer.IsExpired() or not self.current_tagline:
            self._randomize_throttle_timer()
            self.current_tagline = self._get_random_tagline()
            return self.current_tagline
        return self.current_tagline
    
    #endregion
    #region Banner

    def GetBanner(self):
        if self.banner_throttled_timer.IsExpired():
            self.banner_index = (self.banner_index + 1) % len(self.banner_string)
            self.banner_throttled_timer.Reset()
        return self.banner_string[self.banner_index:] + self.banner_string[:self.banner_index]

    #endregion