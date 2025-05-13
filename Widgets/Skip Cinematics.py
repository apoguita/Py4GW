from Py4GWCoreLib import *
module_name = "Skip Cinematic"

class config:
    def __init__(self):
        self.skipped = False
        self.is_map_ready = False
        self.is_party_loaded = False
        self.is_in_cinematic = False
        self.action_queue = ActionQueueNode(1000)
        self.game_throttle_timer = ThrottledTimer(1000)

widget_config = config()

def configure():
    pass

def main():
    global widget_config
        
    if widget_config.game_throttle_timer.IsExpired():
        widget_config.is_map_ready = Map.IsMapReady()
        widget_config.is_party_loaded = Party.IsPartyLoaded()
        if widget_config.is_map_ready and widget_config.is_party_loaded:
            widget_config.is_in_cinematic = Map.IsInCinematic()
        widget_config.game_throttle_timer.Reset()
       
        
    if widget_config.is_map_ready and widget_config.is_party_loaded and widget_config.is_in_cinematic and widget_config.skipped == False:
        for i in range(0,3):
            widget_config.action_queue.add_action(Map.SkipCinematic)
        widget_config.skipped = True
    else:
        widget_config.skipped = False
        
    if widget_config.is_map_ready and widget_config.is_party_loaded and widget_config.is_in_cinematic:   
        if widget_config.action_queue.IsExpired():
            widget_config.action_queue.execute_next()
        

if __name__ == "__main__":
    main()

