from Py4GWCoreLib import GLOBAL_CACHE
from Py4GWCoreLib import ThrottledTimer
from Py4GWCoreLib import ActionQueueNode
from Py4GWCoreLib import ConsoleLog
from Py4GWCoreLib import Map, ImGui, Color
import PyImGui

MODULE_NAME = "Skip Cinematic"
MODULE_ICON = "Textures/Module_Icons/Skip Cinematic.png"

module_name = "Skip Cinematic"

class config:
    def __init__(self):
        self.skipped = False
        self.is_map_ready = False
        self.is_party_loaded = False
        self.is_in_cinematic = False
        self.game_throttle_timer = ThrottledTimer(500)
        self.custom_action_queue = ActionQueueNode(100)

widget_config = config()

def tooltip():
    PyImGui.begin_tooltip()

    # Title
    title_color = Color(255, 200, 100, 255)
    ImGui.push_font("Regular", 20)
    PyImGui.text_colored("Skip Cinematics", title_color.to_tuple_normalized())
    ImGui.pop_font()
    PyImGui.spacing()
    PyImGui.separator()

    # Description
    PyImGui.text("Automatically skips in-game cinematics when they start.")
    
    PyImGui.spacing()
    PyImGui.separator()

    # Features
    PyImGui.text_colored("Features:", title_color.to_tuple_normalized())
    PyImGui.bullet_text("Automatically skips cinematics.")
    
    PyImGui.spacing()
    PyImGui.separator()

    # Credits
    PyImGui.text_colored("Credits:", title_color.to_tuple_normalized())
    PyImGui.bullet_text("Developed by Apo")
    
    PyImGui.end_tooltip()

def main():
    global widget_config
        
    if widget_config.game_throttle_timer.IsExpired():
        widget_config.is_map_ready = Map.IsMapReady()
        widget_config.is_party_loaded = GLOBAL_CACHE.Party.IsPartyLoaded()
        if widget_config.is_map_ready and widget_config.is_party_loaded:
            widget_config.is_in_cinematic = Map.IsInCinematic()
        widget_config.game_throttle_timer.Reset()
       
        
    if widget_config.is_map_ready and widget_config.is_party_loaded and widget_config.is_in_cinematic and widget_config.skipped == False:
        for i in range(0,2):
            widget_config.custom_action_queue.add_action(Map.SkipCinematic)
        widget_config.skipped = True
    else:
        widget_config.skipped = False

    if not widget_config.custom_action_queue.is_empty():
        widget_config.custom_action_queue.execute_next()

if __name__ == "__main__":
    main()

