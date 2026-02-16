from Py4GWCoreLib import Player
from Py4GWCoreLib import GLOBAL_CACHE
from Py4GWCoreLib import SharedCommandType
from Py4GWCoreLib import Timer
from Py4GWCoreLib import Map
import PyImGui
from Py4GWCoreLib import ImGui, Color

#Disabled for debug
#from Py4GWCoreLib import Py4GW

MODULE_NAME = "Window Renamer"
window_renamer_wait_time = 1000 # Set the throttle time to 1 second
window_renamer_wait_timer = Timer()
window_renamer_wait_timer.Start()

def main():
    global window_renamer_wait_timer,window_renamer_wait_time
    if window_renamer_wait_timer.HasElapsed(window_renamer_wait_time) and Map.IsMapReady():
        #Py4GW.Console.Log(MODULE_NAME, f"Map is loaded.")
        account_email = Player.GetAccountEmail()
        accounts = GLOBAL_CACHE.ShMem.GetAllAccountData()
        for account in accounts:
            GLOBAL_CACHE.ShMem.SendMessage(account_email, account.AccountEmail, SharedCommandType.SetWindowTitle, ExtraData=(account.AgentData.CharacterName, "", "", ""))
        window_renamer_wait_timer.Start()

def tooltip():
    PyImGui.begin_tooltip()

    # Title
    title_color = Color(255, 200, 100, 255)
    ImGui.push_font("Regular", 20)
    PyImGui.text_colored("Window Renamer", title_color.to_tuple_normalized())
    ImGui.pop_font()
    PyImGui.spacing()
    PyImGui.separator()

    # Description
    #ellaborate a better description 
    PyImGui.text("Periodically renames the game window")
    
    PyImGui.spacing()

    # Features
    PyImGui.text_colored("Features:", title_color.to_tuple_normalized())
    PyImGui.bullet_text("Periodically renames the game window")
    PyImGui.bullet_text("Sets window title to character name")

    PyImGui.spacing()
    PyImGui.separator()
    PyImGui.spacing()

    # Credits
    PyImGui.text_colored("Credits:", title_color.to_tuple_normalized())
    PyImGui.bullet_text("Developed by PinkMusen")

    PyImGui.end_tooltip()

if __name__ == "__main__":
    main()
