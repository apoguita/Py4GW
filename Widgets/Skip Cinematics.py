from Py4GWCoreLib import *
module_name = "Skip Cinematic"


class config:
    def __init__(self):
        self.skipped = False

widget_config = config()

game_throttle_time = 50
game_throttle_timer = Timer()
game_throttle_timer.Start()

is_map_ready = False
is_party_loaded = False
is_in_cinematic = False
is_explorable = False

def configure():
    pass

def main():
    global widget_config
    global is_map_ready, is_party_loaded, is_in_cinematic, is_explorable
    global game_throttle_time, game_throttle_timer
        
    if game_throttle_timer.HasElapsed(game_throttle_time):
        is_map_ready = Map.IsMapReady()
        is_party_loaded = Party.IsPartyLoaded()
        is_explorable = Map.IsExplorable()
        if is_map_ready and is_party_loaded and is_explorable:
            is_in_cinematic = Map.IsInCinematic()
        game_throttle_timer.Start()
        
    if is_map_ready and is_party_loaded and is_in_cinematic and is_explorable and widget_config.skipped == False:
        Map.SkipCinematic()
        widget_config.skipped = True
    else:
        widget_config.skipped = False
        

if __name__ == "__main__":
    main()

