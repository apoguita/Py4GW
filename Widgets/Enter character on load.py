
from Py4GWCoreLib import GLOBAL_CACHE
from Py4GWCoreLib import Timer
from Py4GWCoreLib import UIManager
from Py4GWCoreLib import Keystroke
from Py4GWCoreLib import Key
from Py4GWCoreLib import ConsoleLog

module_name = "Enter character on load"
play_button_hash = 184818986
loading_in_character_screen = True
start_timer = Timer()
start_timer.Start()

def main():
    global loading_in_character_screen, start_timer, play_button_hash
    if start_timer.IsStopped():
        return
    if GLOBAL_CACHE.Player.InCharacterSelectScreen() and start_timer.HasElapsed(1000) and loading_in_character_screen:
        frame_id = UIManager.GetFrameIDByHash(play_button_hash)
        if UIManager.FrameExists(frame_id):
            ConsoleLog(module_name, f"Entering Game.")
            #UIManager.FrameClick(frame_id)
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

