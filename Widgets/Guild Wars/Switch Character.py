import PyImGui
from Py4GWCoreLib import List
from Py4GWCoreLib import Timer
from Py4GWCoreLib import ConsoleLog
from Py4GWCoreLib import Console
from Py4GWCoreLib import Keystroke
from Py4GWCoreLib import Key
from Py4GWCoreLib import Color, ColorPalette
from Py4GWCoreLib import ProfessionShort, Profession, Campaign
from Py4GWCoreLib import UIManager
from Py4GWCoreLib import PyImGui
from Py4GWCoreLib import ImGui
from Py4GWCoreLib import Routines
from Py4GWCoreLib import GLOBAL_CACHE
from Py4GWCoreLib import Map
from Py4GWCoreLib import ProfessionTextureMap
from Py4GWCoreLib import GWContext
import traceback

MODULE_NAME = "Switch Character"
MODULE_ICON = "Textures/Module_Icons/Switch Character.png"

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
        self.characters = []
        self.target_index: int = -99 # Target index in the character list
        self.last_known_index: int = -99 # Last observed selected index
        self.step_timer = Timer() # For delays between actions (e.g., key presses)
        self.timeout_timer = Timer() # For overall process timeout
        self.step_delay_ms: int = 200 # Delay between navigation steps
        self.process_timeout_ms: int = 30000 # Max time for the whole process
        self._update_character_list() # Initial population of character names
     
    def _is_char_select_context_ready(self) -> bool:
        """Checks if character select is active and context is available."""
        if not Map.Pregame.InCharacterSelectScreen():
            return False
        pregame = GWContext.PreGame.GetContext()
        return pregame is not None and pregame.chars_list is not None
    
    def _get_target_index(self):
        """Finds and sets the index of the target character."""
        if not self._is_char_select_context_ready():
            ConsoleLog("Reroll", "Char select context not ready for finding target.", Console.MessageType.Warning)
            return

        pregame = GWContext.PreGame.GetContext()
        target_name = self.target_character_name
        found_index = -99
        try:
            if pregame and pregame.chars_list:
                for idx, char in enumerate(pregame.chars_list):
                    if target_name == char.character_name:
                        found_index = idx
                        break
        except Exception as e:
            ConsoleLog("Reroll", f"Error accessing character list: {e}", Console.MessageType.Error)
            self.state = self.STATE_ERROR
            return

        if found_index != -99 and pregame:
            self.target_index = found_index
            self.last_known_index = pregame.chosen_character_index
            ConsoleLog("Reroll", f"Found '{target_name}' at index {found_index}. Current selection: {self.last_known_index}", Console.MessageType.Info)
        else:
            ConsoleLog("Reroll", f"Character '{target_name}' not found in list yet.", Console.MessageType.Debug)

    def _navigate_char_select(self):
        """Presses Left/Right arrow keys to navigate."""
        if not self._is_char_select_context_ready():
            ConsoleLog("Reroll", "Char select context not ready during navigation.", Console.MessageType.Warning)
            return

        pregame = GWContext.PreGame.GetContext()
        if pregame is None:
            return
        current_index = pregame.chosen_character_index

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
            if Map.Pregame.InCharacterSelectScreen():
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

            pregame = GWContext.PreGame.GetContext()
            if pregame is None:
                return
            current_index = pregame.chosen_character_index

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
            if not Map.Pregame.InCharacterSelectScreen():
                 if Map.IsMapReady() and GLOBAL_CACHE.Party.IsPartyLoaded():
                     ConsoleLog("Reroll", "Character logged in successfully.", Console.MessageType.Success)
                     self.state = self.STATE_IDLE
                     self.timeout_timer.Stop()   
                     
    def _update_character_list(self):
            """Updates the list of available character names if in character select."""
            try:
                characters = Map.Pregame.GetAvailableCharacterList()
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
        Map.Pregame.LogoutToCharacterSelect()
        self.target_index = -99
        self.last_known_index = -99
            

reroll_widget = RerollCharacter()
window_module = ImGui.WindowModule(module_name="RerollCharacter", window_name=MODULE_NAME, window_size=(337, 326), window_flags=PyImGui.WindowFlags.AlwaysAutoResize)
is_visible = False

tmp_is_selected = False
def DrawWindow():
    def _show_tooltip():
        """Helper function to show a tooltip."""
        if PyImGui.is_item_hovered():
            if PyImGui.begin_tooltip():
                #PyImGui.text(f"Name: {name_text}\nLevel: {level}\nProfessions: {ProfessionShort(primary_prof).name}/{ProfessionShort(secondary_prof).name}")
                profession_name = Profession(primary_prof).name if primary_prof else ""
                secondary_prof_name = Profession(secondary_prof).name if secondary_prof else ""
                
                #row_color
                PyImGui.push_style_color(PyImGui.ImGuiCol.ChildBg, row_color.to_tuple_normalized())
                if PyImGui.begin_child("Tooltipchild", (200, 165), True, PyImGui.WindowFlags.NoFlag):
                    table_flags = PyImGui.TableFlags.RowBg | PyImGui.TableFlags.BordersOuterH
                    if PyImGui.begin_table("tooltipinfotable", 3, table_flags):
                        PyImGui.table_setup_column("Primary", PyImGui.TableColumnFlags.WidthFixed, 32)
                        PyImGui.table_setup_column("Secondary", PyImGui.TableColumnFlags.WidthFixed, 32)
                        PyImGui.table_setup_column("Name", PyImGui.TableColumnFlags.WidthFixed, 150)
                        PyImGui.table_next_row()
                        PyImGui.table_set_column_index(0)
                        ImGui.DrawTexture(primary_texture,32,32)
                        PyImGui.table_set_column_index(1)
                        ImGui.DrawTexture(secondary_texture,32,32)
                        PyImGui.table_set_column_index(2)
                        PyImGui.text(f"{profession_name}")
                        PyImGui.text(f"{secondary_prof_name}")
                        PyImGui.end_table()
                        #PyImGui.separator()
                        PyImGui.text(f"Name: {name_text}")
                        PyImGui.text(f"Level: {level}")
                        PyImGui.text(f"Map: {current_map_name}")
                        PyImGui.text(f"Campaign: {campaign_name}")
                        if character.is_pvp:
                            PyImGui.text("Type: PvP")
                        else:
                            PyImGui.text("Type: PvE")
                    
                    
                    PyImGui.end_child()
                PyImGui.pop_style_color(1)
                
                PyImGui.end_tooltip()
                
                    
          
    def _item_clicked():
        """Helper function to check if an item was clicked."""
        if PyImGui.is_item_clicked(0):
            reroll_widget.selected_char_index = index
            reroll_widget.target_character_name = character.player_name
            ConsoleLog("Reroll", f"UI Selected target: {character.player_name}", Console.MessageType.Debug)
            reroll_widget.start_reroll()  
            
    global window_module, tmp_is_selected
    if window_module.first_run:
        PyImGui.set_next_window_size(window_module.window_size[0], window_module.window_size[1])     
        PyImGui.set_next_window_collapsed(window_module.collapse, 0)
        window_module.first_run = False
    
    new_collapsed = True
    end_pos = window_module.window_pos
    
    if ImGui.gw_window.begin( name = window_module.window_name,
                                  pos  = (window_module.window_pos[0], window_module.window_pos[1]),
                                  size = (window_module.window_size[0], window_module.window_size[1]),
                                  collapsed = window_module.collapse,
                                  pos_cond = PyImGui.ImGuiCond.FirstUseEver,
                                  size_cond = PyImGui.ImGuiCond.Always):
        
    #if PyImGui.begin(window_module.window_name, window_module.window_flags):
        new_collapsed = PyImGui.is_window_collapsed()      
        characters = sorted(Map.Pregame.GetAvailableCharacterList(), key=lambda c: c.player_name.lower())
        
        
        # Define per-profession row colors using RGBA integers (0–255)
        profession_row_colors = {
            1: Color(222, 185, 104, 100),     # Warrior
            2: Color(147, 194, 74 , 100),     # Ranger
            3: Color(171, 215, 229, 100),  # Monk
            4: Color(87 , 174, 112, 100),     # Necromancer
            5: Color(161, 84 , 146, 100),    # Mesmer
            6: Color(197, 75 , 75 , 100),    # Elementalist
            7: Color(234, 18 , 125, 100),     # Assassin
            8: Color(39 , 234, 204, 100),    # Ritualist
            9: Color(208, 122, 14 , 100),   # Paragon
            10:Color(97 , 115, 163, 100),  # Dervish
        }

        img_size =20

        if PyImGui.begin_child("characterList2", (300, 270), True, PyImGui.WindowFlags.NoFlag):
            if PyImGui.begin_table("CharTable", 4, PyImGui.TableFlags.RowBg | PyImGui.TableFlags.BordersInnerV):
                
                PyImGui.table_setup_column("Primary", PyImGui.TableColumnFlags.WidthFixed, 20)
                PyImGui.table_setup_column("Secondary", PyImGui.TableColumnFlags.WidthFixed, 20)
                PyImGui.table_setup_column("Name", PyImGui.TableColumnFlags.WidthStretch)
                PyImGui.table_setup_column("Lvl",  PyImGui.TableColumnFlags.WidthFixed, 30)
                PyImGui.table_headers_row()

                for index, character in enumerate(characters):
                    name_text = character.player_name + (" (PvP)" if character.is_pvp else "")
                    primary_prof = character.primary
                    secondary_prof = character.secondary
                    primary_texture = f"Textures\\Profession_Icons\\{ProfessionTextureMap.get(character.primary, 'unknown')}"
                    secondary_texture = f"Textures\\Profession_Icons\\{ProfessionTextureMap.get(character.secondary, 'unknown')}"
                    level = 20 if character.is_pvp else character.level
                    current_map = character.map_id
                    campaign_origin = character.campaign
                    current_map_name = Map.GetMapName(current_map)
                    campaign_name = Campaign(campaign_origin).name if campaign_origin else "Unknown"
                    row_color = Color(0, 0, 0, 50)  # Default row color
                    
                    PyImGui.table_next_row()

                    if primary_prof != 0:
                        # Set the row color based on the primary profession
                        row_color = profession_row_colors.get(primary_prof, Color(255, 255, 255, 50))
                        PyImGui.table_set_bg_color(2, row_color.to_color(), 1)
  
                    #Primary
                    PyImGui.table_set_column_index(0)
                    ImGui.DrawTexture(primary_texture,img_size,img_size)
                    _show_tooltip()
                    _item_clicked()
                    # Secondary
                    PyImGui.table_set_column_index(1)
                    ImGui.DrawTexture(secondary_texture,img_size,img_size)
                    _show_tooltip()
                    _item_clicked()

                    # Name
                    PyImGui.table_set_column_index(2)
                    PyImGui.text(name_text)

                    _show_tooltip()
                    _item_clicked()

                    # Level
                    PyImGui.table_set_column_index(3)
                    PyImGui.text(f"{level:02}")
                    _show_tooltip()
                    _item_clicked()

                PyImGui.end_table()
        PyImGui.end_child()

        end_pos = PyImGui.get_window_pos()
    #PyImGui.end()
    ImGui.gw_window.end(window_module.window_name)

def tooltip():
    PyImGui.begin_tooltip()
    # Title
    title_color = Color(255, 200, 100, 255)
    ImGui.push_font("Regular", 20)
    PyImGui.text_colored("Switch Character", title_color.to_tuple_normalized())
    ImGui.pop_font()
    PyImGui.spacing()
    PyImGui.separator()
    
    # Description
    #ellaborate a better description 
    PyImGui.text("This widget allows you to quickly switch between")
    PyImGui.text("characters from the character select screen.")
    PyImGui.text("Select a character from the list and the widget")
    PyImGui.text("will log out and switch to the selected character")
    PyImGui.text("automatically.")
    PyImGui.spacing()
    
    # Features
    PyImGui.text_colored("Features:", title_color.to_tuple_normalized())
    PyImGui.bullet_text("Displays a list of available characters.")
    PyImGui.bullet_text("Allows quick selection and switching between characters.")
    PyImGui.bullet_text("Automates logout and login process.")
    
    PyImGui.spacing()
    # Credits
    PyImGui.text_colored("Credits:", title_color.to_tuple_normalized())
    PyImGui.bullet_text("Developed by Torx")
    PyImGui.bullet_text("Contributors: Apo")
    
    PyImGui.end_tooltip()
  
def is_in_character_select():
    if GLOBAL_CACHE.Party.IsPartyLoaded():
        return False
    
    cs_base = UIManager.GetFrameIDByHash(2232987037)
    cs_c0 = UIManager.GetChildFrameID(2232987037, [0])
    cs_c1 = UIManager.GetChildFrameID(2232987037, [1])
    ig_menu = UIManager.GetFrameIDByHash(1144678641)
    
    frames = {
        "cs_base": cs_base,
        "cs_c0": cs_c0,
        "cs_c1": cs_c1,
        "ig_menu": ig_menu,
    }
    
    in_load_screen = all(isinstance(f, int) and f == 0 for f in frames.values())
    in_char_select = (
        not in_load_screen and
        any(isinstance(f, int) and f > 0 for f in (cs_base, cs_c0, cs_c1)) and 
        not GLOBAL_CACHE.Party.IsPartyLoaded()
    )
    
    return in_char_select

def main():
    global reroll_widget, window_module, character_select, is_visible
    try:
        character_select = is_in_character_select()

        if not character_select and not Routines.Checks.Map.MapValid():
            return
        
        reroll_widget.Update()
        
        frame_id = UIManager.GetChildFrameID(1144678641, [0])
        left, top, right, bottom = 0, 0, 0, 0
        if UIManager.FrameExists(frame_id): 
            left, top, right, bottom = UIManager.GetFrameCoords(frame_id)
            
        is_visible = ImGui.floating_toggle_button(
            caption="Switch Character",
            x=left,
            y=top-25,
            v=is_visible,
            width=right-left,
            height=25,
            color=Color(80, 91, 136, 255),
            name="SwitchCharacterButton"
        )

        if is_visible:
            DrawWindow()
            
    except Exception as e:
        ConsoleLog(MODULE_NAME, f"Error in main loop: {e}", Console.MessageType.Error)
        ConsoleLog(MODULE_NAME, f"Stack trace: {traceback.format_exc()}", Console.MessageType.Error)

if __name__ == "__main__":
    main()