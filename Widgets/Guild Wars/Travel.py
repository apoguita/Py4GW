from typing import Optional
import Py4GW
import PyImGui

from Py4GWCoreLib import Timer, UIManager
from Py4GWCoreLib import GLOBAL_CACHE
from Py4GWCoreLib import ImGui
from Py4GWCoreLib import ThemeTextures
from Py4GWCoreLib import Style
from Py4GWCoreLib import Map
from Py4GWCoreLib import IconsFontAwesome5
from Py4GWCoreLib import Color, ColorPalette

import json
import os

from Py4GWCoreLib.ImGui_src.types import Alignment
from Py4GWCoreLib.Py4GWcorelib import ConsoleLog, ThrottledTimer, Utils
from Py4GWCoreLib.enums import Key
from Py4GWCoreLib.py4gwcorelib_src.WidgetManager import Widget, WidgetHandler, get_widget_handler
MODULE_NAME = "Travel"

script_directory = os.path.dirname(os.path.abspath(__file__))
root_directory = Py4GW.Console.get_projects_path()

save_throttle_time = 1000
save_throttle_timer = Timer()
save_throttle_timer.Start()

game_throttle_time = 50
game_throttle_timer = Timer()
game_throttle_timer.Start()

click_timer = ThrottledTimer(125)
click_timer.Start()

MODULE_ICON = "Textures\\Module_Icons\\travel_cursor.png"
class Config:
    global MODULE_NAME
    def __init__(self):
        self.button_position : tuple[float, float] = (100, 100)
        self.config_position : tuple[float, float] = (100, 100)
        self.show_travel_history : bool = True
        self.history_length : int = 5
        self.favorites : list[int] = []
        self.show_favorites : bool = True
        self.save_requested : bool = False
        self.close_after_travel : bool = True
        self.button_size : int = 48
    
    def load(self):
        # Load the configuration from json
        json_file = os.path.join(root_directory, "Widgets/Config/Travel.json")
        
        if os.path.exists(json_file):
            with open(json_file, "r") as f:
                data = json.load(f)
                self.button_position = tuple(data.get("button_position", (100, 100)))
                self.config_position = tuple(data.get("config_position", (100, 100)))
                self.favorites = data.get("favorites", [])
                self.show_travel_history = data.get("show_travel_history", True)
                self.show_favorites = data.get("show_favorites", True)
                self.history_length = data.get("history_length", 5)
                self.close_after_travel = data.get("close_after_travel", True)
                self.button_size = data.get("button_size", 48)
                
    
    def save(self):
        # Save the configuration to json
        dict = {
            "button_position": self.button_position,
            "config_position": self.config_position,
            "favorites": self.favorites,
            "show_travel_history": self.show_travel_history,
            "show_favorites": self.show_favorites,
            "history_length": self.history_length,
            "close_after_travel": self.close_after_travel,
            "button_size": self.button_size,
        }
        
        
        json_file = os.path.join(root_directory, "Widgets/Config/Travel.json")
        
        with open(json_file, "w") as f:
            json.dump(dict, f, indent=4)
        
        self.save_requested = False
            
    def request_save(self):
        self.save_requested = True


widget_config = Config()
widget_config.load()

window_module = ImGui.WindowModule(
    MODULE_NAME, 
    window_name="Travel", 
    window_size=(235, 145),
    window_pos=(1500, 100),
    window_flags=PyImGui.WindowFlags(PyImGui.WindowFlags.NoTitleBar | PyImGui.WindowFlags.AlwaysAutoResize),
    can_close=True,
)

new_favorite = 0
config_module = ImGui.WindowModule(f"Config {MODULE_NAME}", window_name="Travel##config", window_size=(100, 100), window_flags=PyImGui.WindowFlags.AlwaysAutoResize, can_close=True)
outposts = dict(zip(Map.GetOutpostIDs(), Map.GetOutpostNames()))
outposts = {id: outpost.replace("outpost", "") for id, outpost in outposts.items() if outpost}  # Filter out empty names
outpost_index = 0
filtered_outposts = [(id, outpost) for id, outpost in outposts.items()]
filtered_history = []
search_outpost = ""
is_traveling = False
is_dragging = False
is_map_ready = False
is_party_loaded = False
travel_history = []
priority_outposts = {
    194 : "Kaineng Center",
    817 : "Kaineng Center",
    857 : "Embark Beach",
    449 : "Kamadan Jewel of Istan",
    818 : "Kamadan Jewel of Istan",
    819 : "Kamadan Jewel of Istan",
    642 : "Eye of the North",
    821 : "Eye of the North",
}

window_open = window_module.open = False

widget_handler : WidgetHandler = get_widget_handler()
widget_info : Optional[Widget] = None

def tooltip():
    PyImGui.set_next_window_size((600, 0))
    PyImGui.begin_tooltip()
    # Title
    title_color = Color(255, 200, 100, 255)
    ImGui.image(MODULE_ICON, (32, 32))
    PyImGui.same_line(0, 10)
    ImGui.push_font("Regular", 20)
    ImGui.text_aligned(MODULE_NAME, alignment=Alignment.MidLeft, color=title_color.color_tuple, height=32)
    ImGui.pop_font()
    PyImGui.spacing()
    PyImGui.spacing()
    PyImGui.separator()
    # Description
    #ellaborate a better description 
    PyImGui.text("This widget provides a comprehensive interface")
    PyImGui.text("for traveling to outposts within the game.")
    PyImGui.text("Features include searching for outposts,")
    PyImGui.text("maintaining a travel history, and")
    PyImGui.text("managing favorite outposts for quick access.")
    PyImGui.spacing()
    
    # Features
    PyImGui.text_colored("Features:", title_color.to_tuple_normalized())
    PyImGui.bullet_text("Search for outposts by name or initials.")
    PyImGui.bullet_text("Travel to the highlighted outpost by pressing Enter.")
    PyImGui.bullet_text("Travel history shows the last 5 outposts you traveled to.")
    PyImGui.bullet_text("Mark or unmark outposts as favorites with Shift + Left Click.")
    PyImGui.spacing()
    # Credits
    PyImGui.text_colored("Credits:", title_color.to_tuple_normalized())
    PyImGui.bullet_text("Developed by frenkey")
    
    PyImGui.end_tooltip()

def configure():
    global widget_config, config_module, new_favorite, widget_info, widget_handler
    global MODULE_NAME
    
    if widget_info is None:
        widget_info = widget_handler.get_widget_info(MODULE_NAME)
    
    config_module.open = True

    if config_module.first_run:
        PyImGui.set_next_window_size(config_module.window_size[0], config_module.window_size[1])     
        PyImGui.set_next_window_pos(config_module.window_pos[0], config_module.window_pos[1])
        PyImGui.set_next_window_collapsed(config_module.collapse, 0)
        config_module.first_run = False

    new_collapsed = True
    end_pos = config_module.window_pos
    if config_module.begin():
        new_collapsed = PyImGui.is_window_collapsed()
        
        
        if PyImGui.begin_tab_bar("##TravelConfigTabs"):                
            if PyImGui.begin_tab_item("Favorites"):
                show_favorites = ImGui.checkbox("Show Favorites on Travel Window", widget_config.show_favorites)
                if show_favorites != widget_config.show_favorites:
                    widget_config.show_favorites = show_favorites
                    widget_config.request_save()
                    
                PyImGui.spacing()
                PyImGui.separator()
                PyImGui.spacing()
                
                outpost_items = {id: f"{outpost} ({id})" for id, outpost in outposts.items() if outpost}
                #sort outpost_items by name
                outpost_items = dict(sorted(outpost_items.items(), key=lambda item: item[1].lower()))
                
                outpost_ids = list(outpost_items.keys())
                outpost_names = list(outpost_items.values())
                PyImGui.push_item_width(300)
                new_favorite = PyImGui.combo("##NewFavorite", new_favorite, outpost_names)
                PyImGui.same_line(0, 5)
                if ImGui.button("Add Favorite", 150):
                    if new_favorite >= 0 and new_favorite < len(outposts):
                        id = outpost_ids[new_favorite]
                        
                        if id not in widget_config.favorites:
                            widget_config.favorites.append(id)
                            widget_config.request_save()
                            
                PyImGui.spacing()
                PyImGui.separator()
                PyImGui.spacing()
                if widget_config.favorites:
                    if PyImGui.begin_table("##FavoritesTable", 4, PyImGui.TableFlags.NoBordersInBody, 0, 0):
                        PyImGui.table_setup_column(f"Number", PyImGui.TableColumnFlags.WidthFixed, 25)
                        PyImGui.table_setup_column(f"Outpost", PyImGui.TableColumnFlags.WidthStretch, 0)
                        PyImGui.table_setup_column(f"Id", PyImGui.TableColumnFlags.WidthFixed, 50)
                        PyImGui.table_setup_column(f"Action", PyImGui.TableColumnFlags.WidthFixed, 75)
                        
                        PyImGui.table_next_row()
                        PyImGui.table_next_column()

                        for (i, id) in enumerate(widget_config.favorites):
                            outpost = outposts.get(id)
                            
                            if outpost:
                                PyImGui.set_cursor_pos_y(PyImGui.get_cursor_pos_y() + 5)
                                PyImGui.text(f"{i + 1}")
                                PyImGui.table_next_column()
                                
                                PyImGui.set_cursor_pos_y(PyImGui.get_cursor_pos_y() + 5)
                                PyImGui.text(outpost)
                                PyImGui.table_next_column()
                                
                                PyImGui.set_cursor_pos_y(PyImGui.get_cursor_pos_y() + 5)
                                PyImGui.text(f"{id}")
                                PyImGui.table_next_column()
                                
                                if ImGui.button(f"Remove##{id}", 75, 25):
                                    widget_config.favorites.remove(id)
                                    widget_config.request_save()
                                    
                                PyImGui.table_next_column()
                                ImGui.show_tooltip(f"{outpost} ({id})")
                            else:
                                Py4GW.Console.Log(MODULE_NAME, f"Favorite outpost {id} not found in outposts.", Py4GW.Console.MessageType.Warning)
                                
                        PyImGui.end_table()
                            
                PyImGui.end_tab_item()
            
            if PyImGui.begin_tab_item("General"):
                show_history = ImGui.checkbox("Show Travel History on Travel Window", widget_config.show_travel_history)
                if show_history != widget_config.show_travel_history:
                    widget_config.show_travel_history = show_history
                    widget_config.request_save()
                
                ImGui.text_aligned(f"Travel History Length ({widget_config.history_length})", width=100, height=24, alignment=Alignment.MidLeft)
                PyImGui.same_line(0, 2)
                history_length = ImGui.slider_int(f"##Travel History Length", widget_config.history_length, 1, 20)
                if history_length != widget_config.history_length:
                    widget_config.history_length = max(1, min(20, history_length))
                    widget_config.request_save()
                
                ImGui.text_aligned("Travel Button Size", width=100, height=24, alignment=Alignment.MidLeft)
                PyImGui.same_line(0, 2)
                button_size = ImGui.slider_int(f"##Travel Button Size", widget_config.button_size, 32, 256)
                if button_size != widget_config.button_size:
                    widget_config.button_size = max(32, min(256, button_size))
                    widget_config.request_save()
                
                PyImGui.end_tab_item()
                
            if PyImGui.begin_tab_item("Help"):
                PyImGui.dummy(455, 0)
                PyImGui.text("Outpost Travel Configuration")
                PyImGui.separator()
                PyImGui.text("This widget allows you to travel to outposts.")
                PyImGui.bullet_text("search for outposts by name or initials")
                PyImGui.bullet_text("travel to the highlighted outpost by pressing Enter")
                PyImGui.bullet_text("travel history shows the last 5 outposts you traveled to.")
                PyImGui.bullet_text("mark or unmark outposts as favorites with Shift + Left Click")
                PyImGui.end_tab_item()
            PyImGui.end_tab_bar()  
        
        config_module.process_window()
        
        if config_module.window_pos != config_module.end_pos:
            config_module.window_pos = config_module.end_pos
            widget_config.config_position = config_module.window_pos
            widget_config.request_save()            
        
    config_module.end()
    
    if not config_module.open:
        if widget_info and widget_info.configuring:
            widget_handler.set_widget_configuring(MODULE_NAME, False)

        pass

def themed_floating_button(button_rect : tuple[float, float, float, float]):
    match(ImGui.get_style().Theme):
        case Style.StyleTheme.Guild_Wars:
            ThemeTextures.Button_Background.value.get_texture().draw_in_drawlist(
                button_rect[:2], 
                button_rect[2:],
                tint=(255, 255, 255, 255) if ImGui.is_mouse_in_rect(button_rect) else (200, 200, 200, 255),
            )
            
            ThemeTextures.Button_Frame.value.get_texture().draw_in_drawlist(
                button_rect[:2], 
                button_rect[2:],
                tint=(255, 255, 255, 255) if ImGui.is_mouse_in_rect(button_rect) else (200, 200, 200, 255),
            )
            
        case Style.StyleTheme.Minimalus:
            PyImGui.draw_list_add_rect_filled(
                button_rect[0] + 1,
                button_rect[1] + 1,
                button_rect[0] + button_rect[2] -1,
                button_rect[1] + button_rect[3] -1,
                Utils.RGBToColor(48, 48, 48, 150) if ImGui.is_mouse_in_rect(button_rect) else Utils.RGBToColor(0, 0, 0, 150),
                0,
                0,
            )   
            
            PyImGui.draw_list_add_rect(
                button_rect[0] + 1,
                button_rect[1] + 1,
                button_rect[0] + button_rect[2] -1,
                button_rect[1] + button_rect[3] -1,
                Utils.RGBToColor(255, 255, 255, 75) if ImGui.is_mouse_in_rect(button_rect) else Utils.RGBToColor(200, 200, 200, 50),
                0,
                0,
                1,
            )            
            
            pass
        
        case Style.StyleTheme.ImGui:
            PyImGui.draw_list_add_rect_filled(
                button_rect[0] + 1,
                button_rect[1] + 1,
                button_rect[0] + button_rect[2] -1,
                button_rect[1] + button_rect[3] -1,
                Utils.RGBToColor(51, 76, 102, 255) if ImGui.is_mouse_in_rect(button_rect) else Utils.RGBToColor(26, 38, 51, 255),
                4,
                0,
            )   
            
            PyImGui.draw_list_add_rect(
                button_rect[0] + 1,
                button_rect[1] + 1,
                button_rect[0] + button_rect[2] -1,
                button_rect[1] + button_rect[3] -1,
                Utils.RGBToColor(204, 204, 212, 50),
                4,
                0,
                1,
            )
            pass

def DrawWindow():
    global is_traveling, widget_config, search_outpost, window_module, window_open, filtered_outposts, outpost_index, window_x, window_y, filtered_history, is_dragging
    global game_throttle_time, game_throttle_timer, save_throttle_time, save_throttle_timer
    
    try:    
        show_ui = not UIManager.IsWorldMapShowing() and not Map.IsMapLoading() and not Map.IsInCinematic() and not Map.Pregame.InCharacterSelectScreen()
        
        if not show_ui:
            return
        
        padding = widget_config.button_size * 0.05
        style = ImGui.get_style()
        button_rect = (widget_config.button_position[0], widget_config.button_position[1], widget_config.button_size, widget_config.button_size)
        ## Ensure the button is within the screen bounds
        io = PyImGui.get_io()  
        screen_width, screen_height = io.display_size_x, io.display_size_y
        
        button_rect = ensure_on_screen(button_rect, screen_width, screen_height)                
        PyImGui.set_next_window_size(button_rect[2], button_rect[3])
        
        style.WindowPadding.push_style_var_direct(padding, padding)
        if PyImGui.begin("##TravelButton", PyImGui.WindowFlags.NoTitleBar | PyImGui.WindowFlags.NoResize | PyImGui.WindowFlags.NoScrollbar):
            is_hovered = ImGui.is_mouse_in_rect(button_rect)
            button_size = PyImGui.get_content_region_avail()[0] * (1 if is_hovered else 0.8)
            
            icon_rect = (button_rect[0] + (button_rect[2] - button_size) / 2, button_rect[1] + (button_rect[3] - button_size) / 2, button_size, button_size)

            ThemeTextures.TravelCursor.value.get_texture().draw_in_drawlist(
                icon_rect[:2],
                icon_rect[2:],
            )
            
            if PyImGui.invisible_button("##Open Travel Window", button_rect[2], button_rect[3]):
                window_module.open = not window_module.open
                PyImGui.set_next_window_pos(window_module.window_pos[0], window_module.window_pos[1])
            
            elif PyImGui.is_item_active(): 
                delta = PyImGui.get_mouse_drag_delta(0, 0.0)                    
                PyImGui.reset_mouse_drag_delta(0)
                widget_config.button_position = (widget_config.button_position[0] + delta[0], widget_config.button_position[1] + delta[1])
                widget_config.request_save()
                
                window_module.end_pos = window_module.window_pos = (int(window_module.window_pos[0] + delta[0]), int(window_module.window_pos[1] + delta[1]))
                # window_module.open = False
                            
            PyImGui.end()
        style.WindowPadding.pop_style_var_direct()
        
        if not window_module.open:
            return
        
        window_x = widget_config.button_position[0] + button_rect[2] + style.WindowBorderSize.value1
        window_y = widget_config.button_position[1]
        
        if window_y + window_module.window_size[1] > screen_height:
            window_y = screen_height - window_module.window_size[1] - (ImGui.get_style().Theme is Style.StyleTheme.Guild_Wars and 10 or 0)
            
        if window_x + window_module.window_size[0] > screen_width:
            window_x = widget_config.button_position[0] - window_module.window_size[0] - 10
        
        window_module.window_pos = (window_x, window_y)
        PyImGui.set_next_window_pos(window_x, window_y)
        
        if window_module.open:
            PyImGui.set_next_window_focus()
        
        traveled = False
        if window_module.begin():
            search_focused = False
            
            style = ImGui.get_style()
            
            if widget_config.favorites and widget_config.show_favorites:
                if PyImGui.is_rect_visible(0, 20):
                    columns = min(len(widget_config.favorites), 4)
                    if PyImGui.begin_table("##Favorites", columns, PyImGui.TableFlags.NoBordersInBody, 0, 0):
                        for i in range(columns):
                            PyImGui.table_setup_column(f"Column {i}", PyImGui.TableColumnFlags.WidthStretch, 0)
                            
                        
                        for id in widget_config.favorites:
                            outpost = outposts.get(id)
                            
                            if outpost:
                                PyImGui.table_next_column()
                                if ImGui.button(generate_initials(outpost), PyImGui.get_content_region_avail()[0], 25):
                                    click_select_outpost(io, id, 0)
                                    traveled = True
                            
                                
                                ImGui.show_tooltip(f"{outpost} ({id})")
                            else:
                                Py4GW.Console.Log(MODULE_NAME, f"Favorite outpost {id} not found in outposts.", Py4GW.Console.MessageType.Warning)
                                
                        PyImGui.end_table()
                
                PyImGui.separator()

            PyImGui.push_item_width(250)
            changed, search = ImGui.search_field("##Search Outpost", search_outpost, "Search ...", PyImGui.InputTextFlags.AutoSelectAll)
            if changed and search != search_outpost:
                search_outpost = search                
                search = search_outpost.lower()
                
                filtered_outposts = [(id, outpost) for id, outpost in outposts.items() if not search or search in outpost.lower() or search in generate_initials(outpost).lower()]
                ## filter priority outposts to the top then alphabetically                
                # filtered_outposts = sorted(filtered_outposts, key=lambda item: item[1].lower())                
                filtered_outposts.sort(key=lambda item: (0 if item[0] in priority_outposts else 1, priority_outposts.get(item[0], ""), item[1].lower()))
                
                filtered_history = [(id, outpost) for id, outpost in travel_history if not search or search in outpost.lower() or search in generate_initials(outpost).lower()] if widget_config.show_travel_history else []
                
                outpost_index = 0
            
            if PyImGui.is_window_appearing():
                PyImGui.set_keyboard_focus_here(-1)
            
            search_focused = PyImGui.is_item_active() or PyImGui.is_item_focused()    
          
            items_height = max(1, min(300, ((len(filtered_outposts) * 20 if search else 0) + (len(filtered_history) * 20 + (20 if search and filtered_outposts else 0) if filtered_history else 0))))
            if items_height > 1:
                PyImGui.spacing()
            
                if PyImGui.begin_child("##OutpostList", (0, items_height), False, PyImGui.WindowFlags.NoFlag):                                
                    travel_history_len = len(filtered_history)
                    ImGui.push_font("Italic", 12)
                    PyImGui.indent(10)
                    
                    for i, (id, outpost) in enumerate(filtered_history):
                        is_selected = i == outpost_index                        
                        
                        y = PyImGui.get_cursor_pos_y()
                        x = PyImGui.get_cursor_pos_x()
                        
                        ImGui.push_font("Regular", 8)
                        PyImGui.set_cursor_pos_y(y + 2)
                        ImGui.text(IconsFontAwesome5.ICON_HISTORY)
                        ImGui.pop_font()
                        
                        PyImGui.set_cursor_pos(x + 20, y)
                        
                        ImGui.selectable(outpost + f" ({id})", is_selected, PyImGui.SelectableFlags.NoFlag, (0, 0))
                        if PyImGui.is_item_clicked(0) or (is_selected and PyImGui.is_key_pressed(Key.Enter.value)):
                            ConsoleLog(MODULE_NAME, f"Traveling to outpost {outpost} ({id}) from history.", Py4GW.Console.MessageType.Info)
                            click_select_outpost(io, id, i)
                            traveled = True
                            
                        is_favorite = id in widget_config.favorites
                        ImGui.show_tooltip(f"Travel to {outpost} ({id})\n\n{("Add as favorite with Shift + Left Click" if not is_favorite else "Remove from favorites with Shift + Left Click")}")
                                                                                       
                        if is_selected:
                            PyImGui.set_scroll_here_y(0.5)
                            
                    ImGui.pop_font()
                    
                    if filtered_history and search and filtered_outposts:
                        PyImGui.spacing()
                        PyImGui.separator()
                        PyImGui.spacing()
                    
                    PyImGui.unindent(10)
                    
                    ImGui.push_font("Regular", 14)
                    if filtered_outposts and search:
                        for i in range(travel_history_len, len(filtered_outposts) + travel_history_len):
                            id, outpost = filtered_outposts[i - travel_history_len]

                            is_selected = i == outpost_index
                            ImGui.selectable(outpost + f" ({id})", is_selected, PyImGui.SelectableFlags.NoFlag, (0, 0))
                            if PyImGui.is_item_clicked(0) or (is_selected and PyImGui.is_key_pressed(Key.Enter.value)):
                                ConsoleLog(MODULE_NAME, f"Traveling to outpost {outpost} ({id}) from search results.", Py4GW.Console.MessageType.Info)
                                click_select_outpost(io, id, i)                                
                                traveled = True
                            
                            is_favorite = id in widget_config.favorites
                            ImGui.show_tooltip(f"Travel to {outpost}\n\n{("Add as favorite with Shift + Left Click" if not is_favorite else "Remove from favorites with Shift + Left Click")}")
                                    
                            if is_selected:
                                PyImGui.set_scroll_here_y(0.5)
                                
                    
                    
                    ImGui.pop_font()
        
                    if click_timer.IsExpired():
                        max_index = (len(filtered_outposts) if search and filtered_outposts else 0) + travel_history_len - 1
                        
                        if max_index < 0:
                            max_index = 0
                        
                        if PyImGui.is_key_down(Key.DownArrow.value):
                            if outpost_index < max_index:
                                outpost_index += 1
                                click_timer.Reset()
                                
                        elif PyImGui.is_key_down(Key.UpArrow.value):
                            if outpost_index > 0:
                                outpost_index -= 1
                                click_timer.Reset()
                                
                                
                PyImGui.end_child()
                                
            window_module.process_window()
            
            if PyImGui.is_mouse_clicked(0):
                window_rect = (window_x, window_y, window_module.window_size[0], window_module.window_size[1])     
                if not ImGui.is_mouse_in_rect(button_rect) and not ImGui.is_mouse_in_rect(window_rect):
                    window_module.open = False
                    
                elif ImGui.is_mouse_in_rect(button_rect):
                    window_module.open = not window_module.open
                                 
                                   
                
        window_module.end()
        

        if save_throttle_timer.HasElapsed(save_throttle_time):
            save_throttle_timer.Reset()
            
            if widget_config.save_requested:
                widget_config.save()
            

    except Exception as e:
        is_traveling = False
        Py4GW.Console.Log(MODULE_NAME, f"Error in DrawWindow: {str(e)}", Py4GW.Console.MessageType.Debug)

def ensure_on_screen(button_rect, screen_width, screen_height) -> tuple[float, float, float, float]:
    global widget_config
    
    """Ensure the button rectangle is within the screen bounds."""
    
    if button_rect[0] < 0:
        button_rect = (0, button_rect[1], button_rect[2], button_rect[3])
            
    elif button_rect[0] + button_rect[2] > screen_width:
        button_rect = (screen_width - button_rect[2], button_rect[1], button_rect[2], button_rect[3])
            
    if button_rect[1] < 0:
        button_rect = (button_rect[0], 0, button_rect[2], button_rect[3])
    elif button_rect[1] + button_rect[3] > screen_height:
        button_rect = (button_rect[0], screen_height - button_rect[3], button_rect[2], button_rect[3])
        
    widget_config.button_position = (button_rect[0], button_rect[1])
    PyImGui.set_next_window_pos(button_rect[0], button_rect[1])
    
    return button_rect

def generate_initials(name):
    return ''.join(word[0] for word in name.split() if word)
                
def click_select_outpost(io : PyImGui.ImGuiIO, id, i):
    global widget_config, outpost_index, travel_history, filtered_history
    
    if io.key_shift:
        if id not in widget_config.favorites:
            widget_config.favorites.append(id)
            widget_config.request_save()
        else:
            widget_config.favorites.remove(id)
            widget_config.request_save()
    else:
        outpost_index = i
        TravelToOutpost(id)
        filtered_history = [(id, outpost) for id, outpost in travel_history if not search_outpost or search_outpost.lower() in outpost.lower() or search_outpost.lower() in generate_initials(outpost).lower()]

def TravelToOutpost(outpost_id):
    global is_traveling, widget_config, MODULE_NAME, travel_history
    
    if not is_traveling:
        if outpost_id != Map.GetMapID():
            ConsoleLog(MODULE_NAME, f"Traveling to outpost: {outposts[outpost_id]} ({outpost_id})", Py4GW.Console.MessageType.Debug)
            is_traveling = True
            Map.Travel(outpost_id)
            
            if outpost_id in [id for id, _ in travel_history]:
                travel_history = [(id, outpost) for id, outpost in travel_history if id != outpost_id]
            
            # Add the outpost to start of the travel history
            travel_history.insert(0, (outpost_id, outposts[outpost_id]))

            # Remove the last entry if the history exceeds 5 entries
            if len(travel_history) > widget_config.history_length:
                # Remove the oldest entry
                travel_history.pop()
    else:
        ConsoleLog(MODULE_NAME, "Already traveling, please wait.", Py4GW.Console.MessageType.Warning)
    
    if widget_config.close_after_travel:
        window_module.open = False
        


def main():
    """Required main function for the widget"""
    global game_throttle_timer, game_throttle_time, is_traveling
    global is_map_ready, is_party_loaded
    
    try:
        if game_throttle_timer.HasElapsed(game_throttle_time):
            is_map_ready = Map.IsMapReady()
            is_party_loaded = GLOBAL_CACHE.Party.IsPartyLoaded()
            game_throttle_timer.Start()
            
            if is_map_ready and is_party_loaded:
                is_traveling = False
        
        if widget_config.save_requested and save_throttle_timer.HasElapsed(save_throttle_time):
            widget_config.save()
            save_throttle_timer.Reset()
            
        if is_map_ready and is_party_loaded:
            DrawWindow()
            
    except Exception as e:
        Py4GW.Console.Log(MODULE_NAME, f"Error in main: {str(e)}", Py4GW.Console.MessageType.Debug)
        return False
    return True

# These functions need to be available at module level
__all__ = ['main', 'configure']

if __name__ == "__main__":
    main()
