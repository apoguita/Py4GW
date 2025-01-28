from Py4GWCoreLib import *
module_name = "Resign on enter Map"

class config:
    def __init__(self):
        self.resigned = False

widget_config = config()

def configure():
    pass

def main():
    global widget_config
    if (Map.IsMapReady() and Map.IsExplorable() and Party.IsPartyLoaded() and (Party.GetPartyLeaderID() != Player.GetAgentID()) and widget_config.resigned == False):
        Player.SendChatCommand("resign")
        widget_config.resigned = True
        
    if not Map.IsExplorable():
        widget_config.resigned = False

if __name__ == "__main__":
    main()

