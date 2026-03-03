import PyImGui
from Py4GWCoreLib import *
from Py4GWCoreLib.HotkeyManager import HOTKEY_MANAGER


#do not ever disable this module, it is the main module for everything
MODULE_NAME = "Environment Upkeeper"
MODULE_ICON = "Textures/Module_Icons/Environment Upkeeper.png"
OPTIONAL = False

__widget__ = {
    "name": "Environment Upkeeper",
    "enabled": True,
    "category": "Coding",
    "subcategory": "Environment",
    "icon": "ICON_TREE",
    "quickdock": False,
    "hidden": True ##special category for Environment Upkeeper (do not use)
}

class WidgetConfig:
    def __init__(self):
        self.action_queue_manager = ActionQueueManager()
        #LootConfig is kept alive by itself being an instance of LootConfig
        self.loot_config = LootConfig()

        self.overlay = Overlay()
        
        self.throttle_action_queue = ThrottledTimer(50)
        self.throttle_transition_queue = ThrottledTimer(50)
        self.throttle_loot_queue = ThrottledTimer(1250)
        self.throttle_merchant_queue = ThrottledTimer(750)
        self.throttle_salvage_queue = ThrottledTimer(325)
        self.throttle_identify_queue = ThrottledTimer(250)
        self.throttle_fast_queue = ThrottledTimer(20)

widget_config = WidgetConfig()

def reset_on_load():
    global widget_config

    widget_config.throttle_action_queue.Reset()
    widget_config.throttle_transition_queue.Reset()
    widget_config.throttle_loot_queue.Reset()
    widget_config.throttle_merchant_queue.Reset()
    widget_config.throttle_salvage_queue.Reset()
    widget_config.throttle_identify_queue.Reset()
    widget_config.throttle_fast_queue.Reset()
    
    #Resetting all queues
    widget_config.action_queue_manager.ResetAllQueues()

def tooltip():
    PyImGui.begin_tooltip()

    # Title
    title_color = Color(255, 200, 100, 255)
    ImGui.push_font("Regular", 20)
    PyImGui.text_colored("Environment Upkeeper", title_color.to_tuple_normalized())
    ImGui.pop_font()
    red = ColorPalette.GetColor("red")
    PyImGui.text_colored("This is a system Widget, deactivating it will cause issues.", red.to_tuple_normalized())
    PyImGui.separator()
    
    # Description
    PyImGui.text("This widget is responsible for managing the environment upkeep tasks")
    PyImGui.text("such as processing action queues for various activities like looting,")
    PyImGui.text("merchant interactions, salvaging, and identifying items. It ensures")
    PyImGui.text("that these tasks are performed efficiently and in a timely manner,")
    PyImGui.text("enhancing the overall experience.")
    
    PyImGui.spacing()

    # Features
    PyImGui.text_colored("Features:", title_color.to_tuple_normalized())
    PyImGui.bullet_text("Manages multiple action queues for different activities.")
    PyImGui.bullet_text("Throttles queue processing to optimize performance.")
    PyImGui.bullet_text("Integrates with LootConfig for item management.")
    PyImGui.bullet_text("Upkeeps Singletons")
    
    PyImGui.spacing()

    # Credits
    PyImGui.text_colored("Credits:", title_color.to_tuple_normalized())
    PyImGui.bullet_text("Developed by Apo")
    
    PyImGui.end_tooltip()

def main():
    global widget_config

    HOTKEY_MANAGER.update()
    
    if Routines.Checks.Map.MapValid():
        GLOBAL_CACHE._update_cache()
    else:
        LootConfig().ClearItemIDBlacklist()
    
    for routine in GLOBAL_CACHE.Coroutines[:]:
        try:
            next(routine)
        except StopIteration:
            GLOBAL_CACHE.Coroutines.remove(routine)
    
    if Map.IsMapLoading() or Map.IsInCinematic():
        widget_config.action_queue_manager.ResetNonTransitionQueues()
        
        if widget_config.throttle_transition_queue.IsExpired():
            widget_config.action_queue_manager.ProcessQueue("TRANSITION")
            widget_config.throttle_transition_queue.Reset()
        return
    
    if not Routines.Checks.Map.MapValid():
        return
    
    if widget_config.throttle_action_queue.IsExpired():
        widget_config.action_queue_manager.ProcessQueue("ACTION")
        widget_config.throttle_action_queue.Reset()
        
    if widget_config.throttle_loot_queue.IsExpired():
        widget_config.action_queue_manager.ProcessQueue("LOOT")
        widget_config.throttle_loot_queue.Reset()
        
    if widget_config.throttle_merchant_queue.IsExpired():
        widget_config.action_queue_manager.ProcessQueue("MERCHANT")
        widget_config.throttle_merchant_queue.Reset()
        
    if widget_config.throttle_salvage_queue.IsExpired():
        widget_config.action_queue_manager.ProcessQueue("SALVAGE")
        widget_config.throttle_salvage_queue.Reset()
        
    if widget_config.throttle_identify_queue.IsExpired():
        widget_config.action_queue_manager.ProcessQueue("IDENTIFY")
        widget_config.throttle_identify_queue.Reset()
        
    if widget_config.throttle_fast_queue.IsExpired():
        widget_config.action_queue_manager.ProcessQueue("FAST")
        widget_config.throttle_fast_queue.Reset()
        
    widget_config.overlay.UpkeepTextures()
         
    
if __name__ == "__main__":
    main()
