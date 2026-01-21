from Py4GWCoreLib import Player
from Py4GWCoreLib import GLOBAL_CACHE
from Py4GWCoreLib import SharedCommandType
from Py4GWCoreLib import Timer
from Py4GWCoreLib import Map

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
            GLOBAL_CACHE.ShMem.SendMessage(account_email, account.AccountEmail, SharedCommandType.SetWindowTitle, ExtraData=(account.CharacterName, "", "", ""))
        window_renamer_wait_timer.Start()

def configure():
    pass

if __name__ == "__main__":
    main()
