from Py4GWCoreLib import GLOBAL_CACHE
from Py4GWCoreLib import ThrottledTimer

module_name = "Skip Cinematic"

class config:
    def __init__(self):
        self.skipped = False
        self.is_map_ready = False
        self.is_party_loaded = False
        self.is_in_cinematic = False
        self.game_throttle_timer = ThrottledTimer(1000)

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
        for i in range(0,3):
            GLOBAL_CACHE.Map.SkipCinematic()
        widget_config.skipped = True
    else:
        widget_config.skipped = False

        

if __name__ == "__main__":
    main()

