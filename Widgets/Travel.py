import Py4GW

from Py4GWCoreLib import Timer
from Py4GWCoreLib import GLOBAL_CACHE
from Py4GWCoreLib import PyImGui
from Py4GWCoreLib import ImGui, GameTextures
from Py4GWCoreLib import IconsFontAwesome5

import json
import os

from Py4GWCoreLib.Py4GWcorelib import ConsoleLog, ThrottledTimer, Utils
from Py4GWCoreLib.enums import Key
module_name = "Outpost Travel"

script_directory = os.path.dirname(os.path.abspath(__file__))
root_directory = os.path.normpath(os.path.join(script_directory, ".."))

save_throttle_time = 1000
save_throttle_timer = Timer()
save_throttle_timer.Start()

game_throttle_time = 50
game_throttle_timer = Timer()
game_throttle_timer.Start()

click_timer = ThrottledTimer(125)
click_timer.Start()

class Config:
    global module_name
    def __init__(self):
        self.button_position = (100, 100)
        self.config_position = (100, 100)
        self.favorites : list[int] = []
        self.save_requested = False
    
    def load(self):
        # Load the configuration from json
        json_file = os.path.join(root_directory, "Widgets/Config/Travel.json")
        
        if os.path.exists(json_file):
            with open(json_file, "r") as f:
                data = json.load(f)
                self.button_position = tuple(data.get("button_position", (100, 100)))
                self.config_position = tuple(data.get("config_position", (100, 100)))
                self.favorites = data.get("favorites", [])
                
    
    def save(self):
        # Save the configuration to json
        dict = {
            "button_position": self.button_position,
            "config_position": self.config_position,
            "favorites": self.favorites,
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
    module_name, 
    window_name="Travel", 
    window_size=(235, 145),
    window_pos=(1500, 100),
    window_flags=PyImGui.WindowFlags(PyImGui.WindowFlags.NoTitleBar | PyImGui.WindowFlags.AlwaysAutoResize),
    can_close=True,
)

new_favorite = 0
config_module = ImGui.WindowModule(f"Config {module_name}", window_name="Travel##config", window_size=(100, 100), window_flags=PyImGui.WindowFlags.AlwaysAutoResize)
outposts = dict(zip(GLOBAL_CACHE.Map.GetOutpostIDs(), GLOBAL_CACHE.Map.GetOutpostNames()))
outposts = {id: outpost.replace("outpost", "") for id, outpost in outposts.items() if outpost}  # Filter out empty names
outpost_index = 0
filtered_outposts = [(id, outpost) for id, outpost in outposts.items()]
filtered_history = []
search_outpost = ""
is_traveling = False
is_map_ready = False
is_party_loaded = False
travel_history = []

window_open = window_module.open = False

def configure():
    global widget_config, config_module, new_favorite
    global module_name

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
                outpost_items = {id: f"{outpost} ({id})" for id, outpost in outposts.items() if outpost}
                #sort outpost_items by name
                outpost_items = dict(sorted(outpost_items.items(), key=lambda item: item[1].lower()))
                
                outpost_ids = list(outpost_items.keys())
                outpost_names = list(outpost_items.values())
                PyImGui.push_item_width(300)
                new_favorite = PyImGui.combo("##NewFavorite", new_favorite, outpost_names)
                PyImGui.same_line(0, 5)
                if themed_button("Add Favorite", 150):
                    if new_favorite >= 0 and new_favorite < len(outposts):
                        id = outpost_ids[new_favorite]
                        
                        if id not in widget_config.favorites:
                            widget_config.favorites.append(id)
                            widget_config.request_save()
                            
                        else:
                            widget_config.favorites.remove(id)
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
                                PyImGui.text(f"{i + 1}")
                                PyImGui.table_next_column()
                                
                                PyImGui.text(outpost)
                                PyImGui.table_next_column()
                                
                                PyImGui.text(f"{id}")
                                PyImGui.table_next_column()
                                
                                if themed_button(f"Remove##{id}", 75, 25):
                                    widget_config.favorites.remove(id)
                                    widget_config.request_save()
                                    
                                PyImGui.table_next_column()
                                ImGui.show_tooltip(f"{outpost} ({id})")
                            else:
                                Py4GW.Console.Log(module_name, f"Favorite outpost {id} not found in outposts.", Py4GW.Console.MessageType.Warning)
                                
                        PyImGui.end_table()
                            
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

def themed_floating_button(button_rect : tuple[float, float, float, float]):
    match(ImGui.Theme):
        case ImGui.StyleTheme.Guild_Wars:
            GameTextures.Button.value.draw_in_drawlist(
                button_rect[0], 
                button_rect[1],
                (button_rect[2], button_rect[3]),
                tint=(255, 255, 255, 255) if ImGui.is_mouse_in_rect(button_rect) else (200, 200, 200, 255),
            )
            
        case ImGui.StyleTheme.Minimalus:
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
        
        case ImGui.StyleTheme.ImGui:
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

def themed_button(label, width : float = 0, height: float = 26) -> bool:
    clicked = False
    remaining_space = PyImGui.get_content_region_avail()
    width = remaining_space[0] if width <= 0 else width
    height = remaining_space[1] - 1 if height <= 0 else height
    
    match(ImGui.Theme):
        case ImGui.StyleTheme.Guild_Wars:
            x,y = PyImGui.get_cursor_screen_pos()
            display_label = label.split("##")[0]

            button_rect = (x, y, width, height)
            
            GameTextures.Button.value.draw_in_drawlist(
                button_rect[0], 
                button_rect[1],
                (button_rect[2], button_rect[3]),
                tint=(255, 255, 255, 255) if ImGui.is_mouse_in_rect(button_rect) else (200, 200, 200, 255),
            )
            
            text_size = PyImGui.calc_text_size(display_label)
            text_x = button_rect[0] + (button_rect[2] - text_size[0]) / 2
            text_y = button_rect[1] + (button_rect[3] - text_size[1]) / 2 
            
            PyImGui.draw_list_add_text(
                text_x,
                text_y,
                Utils.RGBToColor(255, 255, 255, 255),
                display_label,
            )
            
            PyImGui.set_cursor_screen_pos(x, y)            
            clicked = PyImGui.invisible_button(label, width, height)
            
        case ImGui.StyleTheme.Minimalus:
            clicked = PyImGui.button(label, width, height)
        
        case ImGui.StyleTheme.ImGui:
            clicked = PyImGui.button(label, width, height)
        
    return clicked

##TODO: Add on ensure on screen
def DrawWindow():
    global is_traveling, widget_config, search_outpost, window_module, window_open, filtered_outposts, outpost_index, window_x, window_y, filtered_history
    global game_throttle_time, game_throttle_timer, save_throttle_time, save_throttle_timer
    global ini_handler, module_name
    
    
    try:
        active = False
        show_window = False
    
        button_rect = (widget_config.button_position[0], widget_config.button_position[1], 48, 48)
        ## Ensure the button is within the screen bounds
        io = PyImGui.get_io()        
        screen_width, screen_height = io.display_size_x, io.display_size_y
        
        button_rect = ensure_on_screen(button_rect, screen_width, screen_height)
        PyImGui.set_next_window_size(button_rect[2] + 4, button_rect[3] + 4)
        
        PyImGui.push_style_var2(ImGui.ImGuiStyleVar.WindowPadding, 0, 0)
        if PyImGui.begin("##TravelButton", PyImGui.WindowFlags.NoTitleBar | PyImGui.WindowFlags.NoResize | PyImGui.WindowFlags.NoScrollbar | PyImGui.WindowFlags.NoBackground):
            themed_floating_button(button_rect)
            
            icon_rect = (button_rect[0] + 8, button_rect[1] + 6, 32, 32)

            GameTextures.TravelCursor.value.draw_in_drawlist(
                icon_rect[0], 
                icon_rect[1],
                (icon_rect[2], icon_rect[3]),
                tint=(255, 255, 255, 255) if ImGui.is_mouse_in_rect(button_rect) else (200, 200, 200, 255),
            )
            
            if PyImGui.invisible_button("##Open Travel Window", button_rect[2], button_rect[3]):
                window_module.open = True
                show_window = True
                PyImGui.set_next_window_pos(window_module.window_pos[0], window_module.window_pos[1])
            
            elif PyImGui.is_item_active(): 
                delta = PyImGui.get_mouse_drag_delta(0, 0.0)
                PyImGui.reset_mouse_drag_delta(0)
                widget_config.button_position = (widget_config.button_position[0] + delta[0], widget_config.button_position[1] + delta[1])
                widget_config.request_save()
                
                window_module.end_pos = window_module.window_pos = (int(window_module.window_pos[0] + delta[0]), int(window_module.window_pos[1] + delta[1]))
                window_module.open = False
            
                
            PyImGui.end()
        PyImGui.pop_style_var(1)
        
        if not window_module.open:
            return
        
        window_x = widget_config.button_position[0] + 54
        window_y = widget_config.button_position[1]
        
        if window_y + window_module.window_size[1] > screen_height:
            window_y = screen_height - window_module.window_size[1] - (ImGui.Theme is ImGui.StyleTheme.Guild_Wars and 10 or 0)
            
        if window_x + window_module.window_size[0] > screen_width:
            window_x = widget_config.button_position[0] - window_module.window_size[0] - 10
        
        window_module.window_pos = (window_x, window_y)
        PyImGui.set_next_window_pos(window_x, window_y)
        active = False
        
        if window_module.begin():
            
            if widget_config.favorites:
                if PyImGui.is_rect_visible(0, 20):
                    columns = min(len(widget_config.favorites), 4)
                    if PyImGui.begin_table("##Favorites", columns, PyImGui.TableFlags.NoBordersInBody, 0, 0):
                        for i in range(columns):
                            PyImGui.table_setup_column(f"Column {i}", PyImGui.TableColumnFlags.WidthStretch, 0)
                            
                        
                        for id in widget_config.favorites:
                            outpost = outposts.get(id)
                            
                            if outpost:
                                PyImGui.table_next_column()
                                if themed_button(generate_initials(outpost), PyImGui.get_content_region_avail()[0], 25):
                                    click_select_outpost(io, id, 0)
                            
                                active = active or PyImGui.is_item_active() or PyImGui.is_item_focused() or PyImGui.is_item_hovered()
                                
                                ImGui.show_tooltip(f"{outpost} ({id})")
                            else:
                                Py4GW.Console.Log(module_name, f"Favorite outpost {id} not found in outposts.", Py4GW.Console.MessageType.Warning)
                                
                        PyImGui.end_table()
                
                PyImGui.separator()

            if show_window:
                PyImGui.set_keyboard_focus_here(0)                

            
            changed, search = ImGui.search_field("##Search Outpost", search_outpost, "Search ...", 250, PyImGui.InputTextFlags.AutoSelectAll)
            if changed and search != search_outpost:
                search_outpost = search                

                filtered_outposts = [(id, outpost) for id, outpost in outposts.items() if not search or search.lower() in outpost.lower() or search.lower() in generate_initials(outpost).lower()]
                filtered_outposts = sorted(filtered_outposts, key=lambda item: item[1].lower())
                
                filtered_history = [(id, outpost) for id, outpost in travel_history if not search or search.lower() in outpost.lower() or search.lower() in generate_initials(outpost).lower()]
                
                outpost_index = 0
                
            active = (show_window or active or PyImGui.is_item_active()) and PyImGui.is_window_focused()
          
                    
            
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
                        PyImGui.text(IconsFontAwesome5.ICON_HISTORY)
                        ImGui.pop_font()
                        
                        PyImGui.set_cursor_pos(x + 20, y)
                        
                        if PyImGui.selectable(outpost + f" ({id})", is_selected, PyImGui.SelectableFlags.NoFlag, (0, 0)) or is_selected and PyImGui.is_key_pressed(Key.Enter.value):
                            click_select_outpost(io, id, i)
                            
                        is_favorite = id in widget_config.favorites
                        ImGui.show_tooltip(f"Travel to {outpost}\n\n{("Add as favorite with Shift + Left Click" if not is_favorite else "Remove from favorites with Shift + Left Click")}")
                                                                                       
                        if is_selected:
                            PyImGui.set_scroll_here_y(0.5)
                            
                        active = active or PyImGui.is_item_active() or PyImGui.is_item_focused() or PyImGui.is_item_hovered()
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
                            if PyImGui.selectable(outpost + f" ({id})", is_selected, PyImGui.SelectableFlags.NoFlag, (0, 0)) or is_selected and PyImGui.is_key_pressed(Key.Enter.value):
                                click_select_outpost(io, id, i)
                                
                            is_favorite = id in widget_config.favorites
                            ImGui.show_tooltip(f"Travel to {outpost}\n\n{("Add as favorite with Shift + Left Click" if not is_favorite else "Remove from favorites with Shift + Left Click")}")
                                    
                            if is_selected:
                                PyImGui.set_scroll_here_y(0.5)
                                
                            active = active or PyImGui.is_item_active() or PyImGui.is_item_focused() or PyImGui.is_item_hovered()
                    
                    
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
                    
            if not active:
                window_module.open = False
                
        window_module.end()
        
        if PyImGui.is_mouse_clicked(0) and not PyImGui.is_window_hovered() and not active:
            window_module.open = False

        if save_throttle_timer.HasElapsed(save_throttle_time):
            save_throttle_timer.Reset()
            
            if widget_config.save_requested:
                widget_config.save()
            

    except Exception as e:
        is_traveling = False
        Py4GW.Console.Log(module_name, f"Error in DrawWindow: {str(e)}", Py4GW.Console.MessageType.Debug)

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
                
def click_select_outpost(io, id, i):
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
    global is_traveling, widget_config, module_name, travel_history
    
    if not is_traveling:
        ConsoleLog(module_name, f"Traveling to outpost: {outposts[outpost_id]} ({outpost_id})", Py4GW.Console.MessageType.Debug)
        is_traveling = True
        GLOBAL_CACHE.Map.Travel(outpost_id)
        
        if outpost_id in [id for id, _ in travel_history]:
            travel_history = [(id, outpost) for id, outpost in travel_history if id != outpost_id]
        
        # Add the outpost to start of the travel history
        travel_history.insert(0, (outpost_id, outposts[outpost_id]))

        # Remove the last entry if the history exceeds 5 entries
        if len(travel_history) > 5:
            # Remove the oldest entry
            travel_history.pop()
    else:
        ConsoleLog(module_name, "Already traveling, please wait.", Py4GW.Console.MessageType.Warning)

def main():
    """Required main function for the widget"""
    global game_throttle_timer, game_throttle_time, is_traveling
    global is_map_ready, is_party_loaded
    
    try:
        if game_throttle_timer.HasElapsed(game_throttle_time):
            is_map_ready = GLOBAL_CACHE.Map.IsMapReady()
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
        Py4GW.Console.Log(module_name, f"Error in main: {str(e)}", Py4GW.Console.MessageType.Debug)
        return False
    return True

# These functions need to be available at module level
__all__ = ['main', 'configure']

if __name__ == "__main__":
    main()
