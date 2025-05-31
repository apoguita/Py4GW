from Py4GWCoreLib import Timer
from Py4GWCoreLib import GLOBAL_CACHE

module_name = "Return to Outpost"

class config:
    def __init__(self):
        self.returned = False

widget_config = config()

game_throttle_time = 50
game_throttle_timer = Timer()
game_throttle_timer.Start()

is_map_ready = False
is_party_loaded = False
is_explorable = False
is_party_defeated = False

def configure():
    pass

def main():
    global widget_config
    global is_map_ready, is_party_loaded, is_party_defeated, is_explorable
    global game_throttle_time, game_throttle_timer
    
    if game_throttle_timer.HasElapsed(game_throttle_time):
        is_map_ready = GLOBAL_CACHE.Map.IsMapReady()
        is_party_loaded = GLOBAL_CACHE.Party.IsPartyLoaded()
        is_explorable = GLOBAL_CACHE.Map.IsExplorable()
        
        if is_map_ready and is_party_loaded and is_explorable:
            is_party_defeated = GLOBAL_CACHE.Party.IsPartyDefeated()
        game_throttle_timer.Start()
    
    if not is_party_defeated:
        widget_config.returned = False
        return
        
    if is_map_ready and is_party_loaded and is_explorable and is_party_defeated and widget_config.returned == False:
        GLOBAL_CACHE.Party.ReturnToOutpost()
        #ActionQueueManager().AddAction("ACTION",Party.ReturnToOutpost)
        widget_config.returned = True
    else:
        widget_config.returned = False
     
        

if __name__ == "__main__":
    main()

