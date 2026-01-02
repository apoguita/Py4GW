from Py4GWCoreLib import Timer
from Py4GWCoreLib import GLOBAL_CACHE
from Py4GWCoreLib import Map

module_name = "Return to Outpost"

class config:
    def __init__(self):
        self.returned = False
        self.defeat_timestamp = 0

widget_config = config()

game_throttle_time = 50
game_throttle_timer = Timer()
game_throttle_timer.Start()

# Delay before auto-accepting return to outpost (gives bot time to process death)
RETURN_DELAY_MS = 3000  # 3 seconds

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
    import time
    
    if game_throttle_timer.HasElapsed(game_throttle_time):
        is_map_ready = Map.IsMapReady()
        is_party_loaded = GLOBAL_CACHE.Party.IsPartyLoaded()
        is_explorable = Map.IsExplorable()
        
        if is_map_ready and is_party_loaded and is_explorable:
            is_party_defeated = GLOBAL_CACHE.Party.IsPartyDefeated()
        game_throttle_timer.Start()
    
    if not is_party_defeated:
        widget_config.returned = False
        widget_config.defeat_timestamp = 0
        return
    
    # When party just got defeated, record the timestamp
    if is_party_defeated and widget_config.defeat_timestamp == 0:
        widget_config.defeat_timestamp = int(time.time() * 1000)  # milliseconds
        return
        
    # Wait for RETURN_DELAY_MS before auto-accepting return to outpost
    if is_map_ready and is_party_loaded and is_explorable and is_party_defeated and widget_config.returned == False:
        elapsed = int(time.time() * 1000) - widget_config.defeat_timestamp
        if elapsed >= RETURN_DELAY_MS:
            GLOBAL_CACHE.Party.ReturnToOutpost()
            widget_config.returned = True
    else:
        widget_config.returned = False
     
        

if __name__ == "__main__":
    main()

