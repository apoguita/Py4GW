from Py4GWCoreLib import *
module_name = "Resign on enter Map"

class config:
    def __init__(self):
        self.resigned = False
        self.game_throttle_timer = ThrottledTimer(3000)

widget_config = config()

def configure():
    pass

def main():
    global widget_config
    
    if not (Routines.Checks.Map.MapValid() and Map.IsExplorable()):
        widget_config.game_throttle_timer.Reset()
        widget_config.resigned = False
        return
    
    if widget_config.resigned:
        widget_config.game_throttle_timer.Reset()
        return
    
    if Player.GetAgentID() == Party.GetPartyLeaderID():
        widget_config.game_throttle_timer.Reset()
        widget_config.resigned = True
        return
    
    if widget_config.game_throttle_timer.IsExpired() and not widget_config.resigned:
        ActionQueueManager().AddAction("ACTION", Player.SendChatCommand, "resign")
        widget_config.resigned = True
        
    ActionQueueManager().ProcessQueue("ACTION")
    



if __name__ == "__main__":
    main()

