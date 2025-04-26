from Py4GWCoreLib import *

MODULE_NAME = "Reroll Character"

class RerollCharacter:
    STATE_IDLE = "IDLE"
    STATE_LOGGING_OUT = "LOGGING_OUT"
    STATE_WAITING_FOR_CHAR_SELECT = "WAITING_FOR_CHAR_SELECT"
    STATE_FINDING_TARGET = "FINDING_TARGET"
    STATE_NAVIGATING = "NAVIGATING"
    STATE_SELECTING_CHAR = "SELECTING_CHAR"
    STATE_LOGGING_IN = "LOGGING_IN"
    STATE_TIMED_OUT = "TIMED_OUT"
    STATE_ERROR = "ERROR"

    def __init__(self):
        self.state: str = RerollCharacter.STATE_IDLE
        self.available_character_names: List[str] = []
        self.selected_char_index: int = 0
        self.target_character_name: str = ""
        self.target_index: int = -99 # Target index in the character list
        self.last_known_index: int = -99 # Last observed selected index
        self.step_timer = Timer() # For delays between actions (e.g., key presses)
        self.timeout_timer = Timer() # For overall process timeout
        self.step_delay_ms: int = 200 # Delay between navigation steps
        self.process_timeout_ms: int = 30000 # Max time for the whole process
        self._update_character_list() # Initial population of character names

    def _update_character_list(self):
        """Updates the list of available character names if in character select."""
        try:
            characters = Player.GetLoginCharacters()
            if characters:
                new_names = [char.player_name for char in characters]
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
            self.state = RerollCharacter.STATE_ERROR
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

    def start_reroll(self):
        """Initiates the reroll process."""
        if self.state != RerollCharacter.STATE_IDLE:
            ConsoleLog("Reroll", "Reroll already in progress.", Console.MessageType.Warning)
            return

        if not self.target_character_name:
            ConsoleLog("Reroll", "No target character selected.", Console.MessageType.Error)
            return

        ConsoleLog("Reroll", f"Starting reroll to '{self.target_character_name}'...", Console.MessageType.Info)
        self.state = RerollCharacter.STATE_LOGGING_OUT
        self.timeout_timer.Start()
        Player.LogoutToCharacterSelect()
        self.target_index = -99
        self.last_known_index = -99

    def update(self):
        """Processes the state machine logic for rerolling."""
        if self.state == RerollCharacter.STATE_IDLE or \
           self.state == RerollCharacter.STATE_TIMED_OUT or \
           self.state == RerollCharacter.STATE_ERROR:
            return

        if self.timeout_timer.IsRunning() and self.timeout_timer.HasElapsed(self.process_timeout_ms):
            ConsoleLog("Reroll", f"Reroll process timed out in state: {self.state}", Console.MessageType.Error)
            self.state = RerollCharacter.STATE_TIMED_OUT
            self.timeout_timer.Stop()
            return

        if self.state == RerollCharacter.STATE_LOGGING_OUT:
            if Player.InCharacterSelectScreen():
                ConsoleLog("Reroll", "Character select screen detected.", Console.MessageType.Debug)
                self.state = RerollCharacter.STATE_WAITING_FOR_CHAR_SELECT
                self.step_timer.Start()

        elif self.state == RerollCharacter.STATE_WAITING_FOR_CHAR_SELECT:
            if self._is_char_select_context_ready():
                 ConsoleLog("Reroll", "Character select context ready.", Console.MessageType.Debug)
                 self.state = RerollCharacter.STATE_FINDING_TARGET
            elif self.step_timer.HasElapsed(5000):
                 ConsoleLog("Reroll", "Timeout waiting for character select context.", Console.MessageType.Error)
                 self.state = RerollCharacter.STATE_ERROR
                 self.timeout_timer.Stop()

        elif self.state == RerollCharacter.STATE_FINDING_TARGET:
            self._get_target_index()
            if self.target_index != -99:
                self.state = RerollCharacter.STATE_NAVIGATING
                self.step_timer.Start()

        elif self.state == RerollCharacter.STATE_NAVIGATING:
            if not self._is_char_select_context_ready():
                 ConsoleLog("Reroll", "Char select context lost during navigation.", Console.MessageType.Warning)
                 self.state = RerollCharacter.STATE_ERROR
                 self.timeout_timer.Stop()
                 return

            pregame = Player.GetPreGameContext()
            current_index = pregame.index_1

            if current_index == self.target_index:
                ConsoleLog("Reroll", "Target character is selected.", Console.MessageType.Debug)
                self.state = RerollCharacter.STATE_SELECTING_CHAR
                self.step_timer.Start()
            elif self.step_timer.HasElapsed(self.step_delay_ms):
                self._navigate_char_select()

        elif self.state == RerollCharacter.STATE_SELECTING_CHAR:
             if self.step_timer.HasElapsed(self.step_delay_ms * 2):
                ConsoleLog("Reroll", "Pressing 'Play'...", Console.MessageType.Info)
                Keystroke.PressAndRelease(Key.P.value)
                self.state = RerollCharacter.STATE_LOGGING_IN
                self.step_timer.Stop()

        elif self.state == RerollCharacter.STATE_LOGGING_IN:
            if not Player.InCharacterSelectScreen():
                 if Map.IsMapReady() and Party.IsPartyLoaded():
                     ConsoleLog("Reroll", "Character logged in successfully.", Console.MessageType.Success)
                     self.state = RerollCharacter.STATE_IDLE
                     self.timeout_timer.Stop()


reroll_widget = RerollCharacter()
window_module = ImGui.WindowModule(module_name="RerollCharacter", window_name=MODULE_NAME, window_size=(300, 150), window_flags=PyImGui.WindowFlags.AlwaysAutoResize)

def draw():
    """Draws the ImGui widget."""
    reroll_widget.update()
    reroll_widget._update_character_list()

    if not window_module.begin():
        window_module.end()
        return

    PyImGui.begin_group()
    PyImGui.dummy(0, 0)
    if (reroll_widget.state == RerollCharacter.STATE_IDLE):
        PyImGui.text("Target Character:")
    PyImGui.end_group()
    PyImGui.same_line(0,-1)

    original_selected_index = reroll_widget.selected_char_index
    changed = False

    if reroll_widget.available_character_names:
        if (reroll_widget.state == RerollCharacter.STATE_IDLE):
            new_selected_index = PyImGui.combo(
                "##TargetCharacter",
                reroll_widget.selected_char_index,
                reroll_widget.available_character_names
            )
        
            if new_selected_index != original_selected_index:
                changed = True
                reroll_widget.selected_char_index = new_selected_index

        if changed and 0 <= reroll_widget.selected_char_index < len(reroll_widget.available_character_names):
            reroll_widget.target_character_name = reroll_widget.available_character_names[reroll_widget.selected_char_index]
            ConsoleLog("Reroll", f"UI Selected target: {reroll_widget.target_character_name}", Console.MessageType.Debug)

    else:
        PyImGui.text_disabled("(Not in Character Select)")
        if reroll_widget.target_character_name != "":
                reroll_widget.target_character_name = ""
    if (reroll_widget.state == RerollCharacter.STATE_IDLE or not reroll_widget.target_character_name):

        if PyImGui.button("Reroll"):
            reroll_widget.start_reroll()
        PyImGui.same_line(0, 5)
    PyImGui.same_line(0, 5)
    status_text = f"Status: {reroll_widget.state}"

    if reroll_widget.state == RerollCharacter.STATE_NAVIGATING:
            status_text += f" (Current: {reroll_widget.last_known_index}, Target: {reroll_widget.target_index})"
    elif reroll_widget.state == RerollCharacter.STATE_TIMED_OUT or \
            reroll_widget.state == RerollCharacter.STATE_ERROR:
            PyImGui.push_style_color(PyImGui.ImGuiCol.Text, (1.0, 0.0, 0.0, 1.0))
            PyImGui.text(status_text) # Red for errors
            PyImGui.pop_style_color(1)
    else:
            PyImGui.text(status_text)
    window_module.end()

def configure():
    pass

def main():
        try:
            draw()
        except Exception as e:
            ConsoleLog(MODULE_NAME, f"Error in main loop: {e}", Console.MessageType.Error)
            ConsoleLog(MODULE_NAME, f"Stack trace: {traceback.format_exc()}", Console.MessageType.Error)

if __name__ == "__main__":
    main()
