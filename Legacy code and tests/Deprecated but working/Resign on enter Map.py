from Py4GWCoreLib import ThrottledTimer
from Py4GWCoreLib import Routines
from Py4GWCoreLib import GLOBAL_CACHE
from Py4GWCoreLib import Map, Player

module_name = "Resign on enter Map"

resigned = False
explorable_loaded_timer = ThrottledTimer(2000)

def main():
    global resigned, explorable_loaded_timer
    if not Routines.Checks.Map.MapValid():
        resigned = False
        explorable_loaded_timer.Reset()
        return
    
    if not Map.IsExplorable():
        resigned = False
        explorable_loaded_timer.Reset()
        return
    
    if Player.GetAgentID() == GLOBAL_CACHE.Party.GetPartyLeaderID():
        resigned = True
        explorable_loaded_timer.Reset()
        return
    
    if not resigned and explorable_loaded_timer.IsExpired():
        resigned = True
        explorable_loaded_timer.Reset()
        Player.SendChatCommand("resign")
        
def configure():
    pass

if __name__ == "__main__":
    main()

