
from Py4GWCoreLib import *


MODULE_NAME = "Reroll Character"

class RerollCharacter:
    def __init__(self):
        self.STATE_IDLE = "IDLE"
        self.STATE_LOGGING_OUT = "LOGGING_OUT"
        self.STATE_WAITING_FOR_CHAR_SELECT = "WAITING_FOR_CHAR_SELECT"
        self.STATE_FINDING_TARGET = "FINDING_TARGET"
        self.STATE_NAVIGATING = "NAVIGATING"
        self.STATE_SELECTING_CHAR = "SELECTING_CHAR"
        self.STATE_LOGGING_IN = "LOGGING_IN"
        self.STATE_TIMED_OUT = "TIMED_OUT"
        self.STATE_ERROR = "ERROR"
        self.state: str = self.STATE_IDLE
        self.available_character_names: List[str] = []
        self.selected_char_index: int = 0
        self.target_character_name: str = ""
        self.characters = list[PyPlayer.LoginCharacterInfo]
        self.target_index: int = -99 # Target index in the character list
        self.last_known_index: int = -99 # Last observed selected index
        self.step_timer = Timer() # For delays between actions (e.g., key presses)
        self.timeout_timer = Timer() # For overall process timeout
        self.step_delay_ms: int = 200 # Delay between navigation steps
        self.process_timeout_ms: int = 30000 # Max time for the whole process
        self._update_character_list() # Initial population of character names
     
    def _is_char_select_context_ready(self) -> bool:
        """Checks if character select is active and context is available."""
        if not Player.InCharacterSelectScreen():
            return False
        pregame = Player.GetPreGameContext()
        return pregame is not None and pregame.chars is not None
    
    def _get_target_index(self):
        """Finds and sets the index of the target character."""
        if not self._is_char_select_context_ready():
            ConsoleLog("Reroll", "Char select context not ready for finding target.", Console.MessageType.Warning)
            return

        pregame = Player.GetPreGameContext()
        target_name = self.target_character_name
        found_index = -99
        try:
            for char in pregame.chars:
                if target_name == char:
                    found_index = pregame.chars.index(target_name)
                    break
        except Exception as e:
            ConsoleLog("Reroll", f"Error accessing character list: {e}", Console.MessageType.Error)
            self.state = self.STATE_ERROR
            return

        if found_index != -99:
            self.target_index = found_index
            self.last_known_index = pregame.index_1
            ConsoleLog("Reroll", f"Found '{target_name}' at index {found_index}. Current selection: {self.last_known_index}", Console.MessageType.Info)
        else:
            ConsoleLog("Reroll", f"Character '{target_name}' not found in list yet.", Console.MessageType.Debug)

    def _navigate_char_select(self):
        """Presses Left/Right arrow keys to navigate."""
        if not self._is_char_select_context_ready():
            ConsoleLog("Reroll", "Char select context not ready during navigation.", Console.MessageType.Warning)
            return

        pregame = Player.GetPreGameContext()
        current_index = pregame.index_1

        if current_index == self.target_index:
            return

        self.last_known_index = current_index

        distance = self.target_index - current_index

        if distance != 0:
            key = Key.RightArrow.value if distance > 0 else Key.LeftArrow.value
            ConsoleLog("Reroll", f"Navigating {'Right' if distance > 0 else 'Left'} (Current: {current_index}, Target: {self.target_index})", Console.MessageType.Debug)
            Keystroke.PressAndRelease(key)
            self.step_timer.Reset()
            
    def _update(self):
        """Processes the state machine logic for rerolling."""
        if self.state == self.STATE_IDLE or \
           self.state == self.STATE_TIMED_OUT or \
           self.state == self.STATE_ERROR:
            return

        if self.timeout_timer.IsRunning() and self.timeout_timer.HasElapsed(self.process_timeout_ms):
            ConsoleLog("Reroll", f"Reroll process timed out in state: {self.state}", Console.MessageType.Error)
            self.state = self.STATE_TIMED_OUT
            self.timeout_timer.Stop()
            return

        if self.state == self.STATE_LOGGING_OUT:
            if Player.InCharacterSelectScreen():
                ConsoleLog("Reroll", "Character select screen detected.", Console.MessageType.Debug)
                self.state = self.STATE_WAITING_FOR_CHAR_SELECT
                self.step_timer.Start()

        elif self.state == self.STATE_WAITING_FOR_CHAR_SELECT:
            if self._is_char_select_context_ready():
                 ConsoleLog("Reroll", "Character select context ready.", Console.MessageType.Debug)
                 self.state = self.STATE_FINDING_TARGET
            elif self.step_timer.HasElapsed(5000):
                 ConsoleLog("Reroll", "Timeout waiting for character select context.", Console.MessageType.Error)
                 self.state = self.STATE_ERROR
                 self.timeout_timer.Stop()

        elif self.state == self.STATE_FINDING_TARGET:
            self._get_target_index()
            if self.target_index != -99:
                self.state = self.STATE_NAVIGATING
                self.step_timer.Start()

        elif self.state == self.STATE_NAVIGATING:
            if not self._is_char_select_context_ready():
                 ConsoleLog("Reroll", "Char select context lost during navigation.", Console.MessageType.Warning)
                 self.state = self.STATE_ERROR
                 self.timeout_timer.Stop()
                 return

            pregame = Player.GetPreGameContext()
            current_index = pregame.index_1

            if current_index == self.target_index:
                ConsoleLog("Reroll", "Target character is selected.", Console.MessageType.Debug)
                self.state = self.STATE_SELECTING_CHAR
                self.step_timer.Start()
            elif self.step_timer.HasElapsed(self.step_delay_ms):
                self._navigate_char_select()

        elif self.state == self.STATE_SELECTING_CHAR:
             if self.step_timer.HasElapsed(self.step_delay_ms * 2):
                ConsoleLog("Reroll", "Pressing 'Play'...", Console.MessageType.Info)
                Keystroke.PressAndRelease(Key.P.value)
                self.state = self.STATE_LOGGING_IN
                self.step_timer.Stop()

        elif self.state == self.STATE_LOGGING_IN:
            if not Player.InCharacterSelectScreen():
                 if Map.IsMapReady() and Party.IsPartyLoaded():
                     ConsoleLog("Reroll", "Character logged in successfully.", Console.MessageType.Success)
                     self.state = self.STATE_IDLE
                     self.timeout_timer.Stop()   
                     
    def _update_character_list(self):
            """Updates the list of available character names if in character select."""
            try:
                characters = Player.GetLoginCharacters()
                if characters:
                    new_names = [char.player_name for char in characters]
                    self.characters = characters
                    if new_names != self.available_character_names:
                        self.available_character_names = new_names
                        if self.selected_char_index >= len(self.available_character_names):
                            self.selected_char_index = 0
                        if self.available_character_names:
                            self.target_character_name = self.available_character_names[self.selected_char_index]
                        else:
                            self.target_character_name = ""
                else:
                    if self.available_character_names:
                        self.available_character_names = []
                        self.selected_char_index = 0
                        self.target_character_name = ""
            except Exception as e:
                ConsoleLog("Reroll", f"Error getting character list: {e}", Console.MessageType.Warning)
    
    def Update(self):
        self._update()
        self._update_character_list()
        
    def start_reroll(self):
        """Initiates the reroll process."""
        if self.state != self.STATE_IDLE:
            ConsoleLog("Reroll", "Reroll already in progress.", Console.MessageType.Warning)
            return

        if not self.target_character_name:
            ConsoleLog("Reroll", "No target character selected.", Console.MessageType.Error)
            return

        ConsoleLog("Reroll", f"Starting reroll to '{self.target_character_name}'...", Console.MessageType.Info)
        self.state = self.STATE_LOGGING_OUT
        self.timeout_timer.Start()
        Player.LogoutToCharacterSelect()
        self.target_index = -99
        self.last_known_index = -99
            

reroll_widget = RerollCharacter()
window_module = ImGui.WindowModule(module_name="RerollCharacter", window_name=MODULE_NAME, window_size=(300, 150), window_flags=PyImGui.WindowFlags.AlwaysAutoResize)

def DrawWindow():
    global window_module
    if window_module.first_run:
        PyImGui.set_next_window_size(window_module.window_size[0], window_module.window_size[1])     
        PyImGui.set_next_window_collapsed(window_module.collapse, 0)
        window_module.first_run = False
    
    new_collapsed = True
    end_pos = window_module.window_pos
    
    if PyImGui.begin(window_module.window_name, window_module.window_flags):
        new_collapsed = PyImGui.is_window_collapsed()
        
        if PyImGui.begin_child("OutpostList",(195, 150), True, PyImGui.WindowFlags.NoFlag):
            for index, character_name in enumerate(reroll_widget.available_character_names):
                is_selected = (index == reroll_widget.selected_char_index)
                if PyImGui.selectable(character_name, is_selected, PyImGui.SelectableFlags.NoFlag, (0.0, 0.0)):
                    reroll_widget.selected_char_index = index
                    selected_name = reroll_widget.available_character_names[index]
                    reroll_widget.target_character_name     = selected_name
                    ConsoleLog("Reroll", f"UI Selected target: {reroll_widget.target_character_name}", Console.MessageType.Debug)
                    reroll_widget.start_reroll()

            PyImGui.end_child()
            
        """
        if PyImGui.begin_child("expandedView", (395, 150), True, PyImGui.WindowFlags.NoFlag):
            if PyImGui.begin_table("ExpandedTable", 5, PyImGui.TableFlags.Borders | PyImGui.TableFlags.Resizable):
                PyImGui.table_setup_column("Reroll")
                PyImGui.table_setup_column("Name")
                PyImGui.table_setup_column("Profession")
                PyImGui.table_setup_column("Level")
                PyImGui.table_setup_column("Map")
                PyImGui.table_setup_column("PvP")
                
                PyImGui.table_headers_row()
                
                for index, character_name in enumerate(reroll_widget.available_character_names):
                    is_selected = (index == reroll_widget.selected_char_index)
                    if is_selected:
                        PyImGui.table_set_column_index(0)
                        if PyImGui.button(f"Reroll##reroll{index}"):
                            reroll_widget.selected_char_index = index
                            selected_name = reroll_widget.available_character_names[index]
                            reroll_widget.target_character_name     = selected_name
                            ConsoleLog("Reroll", f"UI Selected target: {reroll_widget.target_character_name}", Console.MessageType.Debug)
                            reroll_widget.start_reroll()
                            
                        PyImGui.table_set_column_index(1)
                        PyImGui.text(character_name)
                        
                        PyImGui.text(reroll_widget.state)
                
                PyImGui.end_table()
            PyImGui.end_child()

        """
        end_pos = PyImGui.get_window_pos()
    PyImGui.end()

def configure():
    pass

def main():
    global reroll_widget, window_module
    try:
        reroll_widget.Update()
        DrawWindow()
    except Exception as e:
        ConsoleLog(MODULE_NAME, f"Error in main loop: {e}", Console.MessageType.Error)
        ConsoleLog(MODULE_NAME, f"Stack trace: {traceback.format_exc()}", Console.MessageType.Error)

if __name__ == "__main__":
    main()
