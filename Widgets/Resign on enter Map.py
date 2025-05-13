from Py4GWCoreLib import *
module_name = "Resign on enter Map"

class config:
    def __init__(self):
        self.resigned = False
        self.resign_timer = ThrottledTimer(3000)

widget_config = config()

def configure():
    pass

def safe_resign():
    if not Routines.Checks.Map.MapValid() or not Map.IsExplorable():
        return 
    Player.SendChatCommand("resign")
    
def resigned():
    global widget_config
    if not Routines.Checks.Map.MapValid():
        widget_config.resign_timer.Reset()
        widget_config.resigned = False
        return False
        
    if not Map.IsExplorable():
        widget_config.resign_timer.Reset()
        widget_config.resigned = False
        return False
        
    if not widget_config.resign_timer.IsExpired():
        return False
    
    if widget_config.resigned:
        return False
    
    if Player.GetAgentID() == Party.GetPartyLeaderID():
        return False
     
    for i in range(0, 3):
        ActionQueueManager().AddAction("ACTION",safe_resign)
    widget_config.resigned = True
    
    return True

def main():
    if not resigned():
        return
    
    ActionQueueManager().ProcessQueue("ACTION")
    

if __name__ == "__main__":
    main()

