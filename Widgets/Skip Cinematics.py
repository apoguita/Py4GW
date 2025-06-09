from Py4GWCoreLib import GLOBAL_CACHE
from Py4GWCoreLib import ThrottledTimer
from Py4GWCoreLib import ActionQueueNode
from Py4GWCoreLib import ConsoleLog
from Py4GWCoreLib import Map

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

def configure():
    pass

def main():
    global widget_config
        
    if widget_config.game_throttle_timer.IsExpired():
        widget_config.is_map_ready = GLOBAL_CACHE.Map.IsMapReady()
        widget_config.is_party_loaded = GLOBAL_CACHE.Party.IsPartyLoaded()
        if widget_config.is_map_ready and widget_config.is_party_loaded:
            widget_config.is_in_cinematic = GLOBAL_CACHE.Map.IsInCinematic()
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

