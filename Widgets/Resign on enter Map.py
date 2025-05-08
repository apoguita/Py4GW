from Py4GWCoreLib import *
module_name = "Resign on enter Map"

class config:
    def __init__(self):
        self.resigned = False
        self.game_throttle_timer = ThrottledTimer(3000)
        self.action_queue = ActionQueueNode(1000)
        self.map_valid = False
        self.is_explorable = False
        self.party_leader_id = 0
        self.player_agent_id = 0

widget_config = config()

def configure():
    pass

def main():
    global widget_config

    if widget_config.game_throttle_timer.IsExpired():
        widget_config.map_valid = Routines.Checks.Map.MapValid()
        if widget_config.map_valid:
            widget_config.party_leader_id = Party.GetPartyLeaderID()
            widget_config.player_agent_id = Player.GetAgentID()
            widget_config.is_explorable = Map.IsExplorable()
        widget_config.game_throttle_timer.Reset()
    
        if not widget_config.map_valid:
            widget_config.resigned = False
            return
        
        if not widget_config.is_explorable:
            widget_config.resigned = False
            return
        
        if widget_config.party_leader_id == widget_config.player_agent_id:
            return
        
        for i in range(0,3):
            widget_config.action_queue.add_action(Player.SendChatCommand, "resign")
        widget_config.resigned = True

    if widget_config.map_valid and widget_config.is_explorable:
        if widget_config.action_queue.IsExpired():
            widget_config.action_queue.execute_next()  
    else:
        widget_config.resigned = False
        widget_config.game_throttle_timer.Reset()
        widget_config.action_queue.clear() 


if __name__ == "__main__":
    main()

