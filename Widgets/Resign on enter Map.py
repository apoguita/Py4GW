from Py4GWCoreLib import *
module_name = "Resign on enter Map"

class config:
    def __init__(self):
        self.resigned = False

widget_config = config()

game_throttle_time = 50
game_throttle_timer = Timer()
game_throttle_timer.Start()

is_map_ready = False
is_party_loaded = False
party_leader_id = 0
player_agent_id = 0
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
            party_leader_id = Party.GetPartyLeaderID()
            player_agent_id = Player.GetAgentID()
        game_throttle_timer.Start()
    
    if not is_explorable:
        widget_config.resigned = False
    
    if (is_map_ready and is_party_loaded and is_explorable and party_leader_id != player_agent_id and widget_config.resigned == False):
        Player.SendChatCommand("resign")
        widget_config.resigned = True

        
    

if __name__ == "__main__":
    main()

