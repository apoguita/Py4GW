from Py4GWCoreLib import *
module_name = "Return to Outpost"

class config:
    def __init__(self):
        self.returned = False

widget_config = config()

def configure():
    pass

def main():
    global widget_config
    if Map.IsMapReady() and Party.IsPartyLoaded() and Party.IsPartyDefeated() and widget_config.returned == False:
        Party.ReturnToOutpost()
        widget_config.returned = True
    else:
        widget_config.returned = False
        
    if not Party.IsPartyDefeated():
        widget_config.returned = False

if __name__ == "__main__":
    main()

