from Py4GWCoreLib import *
module_name = "Skip Cinematic"


class config:
    def __init__(self):
        self.skipped = False

widget_config = config()

def configure():
    pass

def main():
    global widget_config
    if Map.IsMapReady() and Party.IsPartyLoaded() and Map.IsInCinematic() and widget_config.skipped == False:
        Map.SkipCinematic()
        widget_config.skipped = True
    else:
        widget_config.skipped = False

    if not Map.IsInCinematic():
        widget_config.skipped = False
        

if __name__ == "__main__":
    main()

