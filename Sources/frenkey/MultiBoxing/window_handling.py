import ctypes

from Py4GW import Console
import PyImGui

from Py4GWCoreLib import Routines
from Py4GWCoreLib.GlobalCache import GLOBAL_CACHE
from Py4GWCoreLib.GlobalCache.SharedMemory import AccountData
from Py4GWCoreLib.enums_src.Multiboxing_enums import SharedCommandType
from Py4GWCoreLib.py4gwcorelib_src.Console import ConsoleLog
from Sources.frenkey.MultiBoxing.settings import Settings

MODULE_NAME = __file__.split("\\")[-2]

def set_window_active(acc: AccountData, settings: Settings, ctrl_pressed: bool = False):
    try:
        ConsoleLog(MODULE_NAME, f"Setting window active for account: {acc.AccountEmail}", Console.MessageType.Info,False)
        account_mail = settings.get_account_mail()
        
        # if ctrl_pressed:
        #     while PyImGui.get_io().key_ctrl:
        #         yield from Routines.Yield.wait(100)
                
        # if settings.move_slave_to_main and not ctrl_pressed:
        #     main_region = settings.main_region
        #     if main_region:
                
        #         if account_mail:
        #             GLOBAL_CACHE.ShMem.SendMessage(account_mail, acc.AccountEmail, SharedCommandType.SetWindowGeometry, (main_region.x, main_region.y, main_region.w, main_region.h))

        GLOBAL_CACHE.ShMem.SendMessage(account_mail, acc.AccountEmail, SharedCommandType.SetWindowActive, (0,0,0,0))
    except Exception as e:
        ConsoleLog(MODULE_NAME, f"Error setting window active: {e}", message_type=1)
    pass


def is_window_active() -> bool:
    try:
        # user32 = ctypes.windll.user32
        # foreground_window = user32.GetForegroundWindow()
        # gw_window = Console.get_gw_window_handle()
        return Console.is_window_active()
    
    except Exception as e:
        ConsoleLog(MODULE_NAME, f"Error checking if window is active: {e}", Console.MessageType.Error)
        return False

def set_window_title(title: str):
    try:
        Console.set_window_title(title)
    except Exception as e:
        ConsoleLog(MODULE_NAME, f"Error setting window title: {e}", message_type=1)
    pass