
from Py4GWCoreLib import *

module_name = "Enter character on load"
loading_in_character_screen = True
start_timer = Timer()
start_timer.Start()

def main():
    global loading_in_character_screen, start_timer
    if not Map.IsMapReady() and start_timer.HasElapsed(1000):
        Py4GW.Console.Log(module_name, f"Entering Game.", Py4GW.Console.MessageType.Info)
        Keystroke.PressAndRelease(Key.Enter.value)
        loading_in_character_screen = False
        start_timer.Stop()

    if start_timer.HasElapsed(1500): #if never triggered before, we didnt load on character screen
        loading_in_character_screen = False
        start_timer.Stop()
        
        
def configure():
    pass

if __name__ == "__main__":
    main()

