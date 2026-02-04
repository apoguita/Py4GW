
import os
import sys
import time
from typing import Optional

from Py4GW import Console
import Py4GW

from Py4GWCoreLib import ImGui, Routines
from Py4GWCoreLib.GlobalCache import GLOBAL_CACHE
from Py4GWCoreLib.Py4GWcorelib import ThrottledTimer
from Py4GWCoreLib.py4gwcorelib_src.WidgetManager import get_widget_handler
from Py4GWCoreLib.py4gwcorelib_src.Console import Console

MODULE_NAME = "MultiBoxing"
for module_name in list(sys.modules.keys()):
    if module_name not in ("sys", "importlib", "cache_data"):
        try:            
            if f"{MODULE_NAME}." in module_name:
                del sys.modules[module_name]
                # importlib.reload(module_name)
                pass
        except Exception as e:
            Py4GW.Console.Log(MODULE_NAME, f"Error reloading module {module_name}: {e}")
            
from Sources.frenkeyLib.MultiBoxing.messaging import HandleReceivedMessages
from Sources.frenkeyLib.MultiBoxing.enum import RenameClientType
from Sources.frenkeyLib.MultiBoxing.settings import Settings
from Sources.frenkeyLib.MultiBoxing.region import Region
from Sources.frenkeyLib.MultiBoxing.window_handling import is_window_active, set_window_title
from Sources.frenkeyLib.MultiBoxing.gui import GUI

throttle_timer = ThrottledTimer(250)
script_directory = os.path.dirname(os.path.abspath(__file__))

widget_handler = get_widget_handler()
module_info = None

settings = Settings()

access_window = ImGui.WindowModule(MODULE_NAME, MODULE_NAME, (300, 600))
configure_window = ImGui.WindowModule(MODULE_NAME, MODULE_NAME + " Configure", (1400, 800), can_close=True)
gui = GUI(configure_window, access_window)

regions: list[Region] = []
active_region: Optional[Region] = None  
screen_size_changed : bool = False

def configure():
    global module_info
    
    if not module_info:
        module_info = widget_handler.get_widget_info(MODULE_NAME)
        
    try:
        gui.draw_configure_window()
        
    except Exception as e:
        Py4GW.Console.Log(MODULE_NAME, f"Error in draw(): {e}", Console.MessageType.Error)

def draw():    
    try:          
        gui.draw_access_window()
        
    except Exception as e:
        Py4GW.Console.Log(MODULE_NAME, f"Error in draw(): {e}",  Console.MessageType.Error)
    
def on_enable():
    settings.load_layouts()
    settings.load_settings()    
    
    if settings.layout != "None":
        settings.load_layout(settings.layout)    
    pass

def on_disable():
    Py4GW.Console.Log(MODULE_NAME, "Module disabled.")
    pass

last_character_name : str = ""
last_rename_type : RenameClientType = RenameClientType.No_Rename
last_append_gw : bool = True
is_on_main : bool = False

toggled_widget_ui : bool = False
initial_resized : bool = False

def set_widget_visibility(visible: bool):
    global toggled_widget_ui
    
    if settings.hide_widgets_on_slave and (widget_handler.show_widget_ui != visible):
        widget_handler.set_widget_ui_visibility(visible)
        

def is_client_in_region(region: Region) -> bool:
    client_rect = Console.get_window_rect()
    client_rect = (client_rect[0], client_rect[1], client_rect[2]-client_rect[0], client_rect[3]-client_rect[1])
    
    offset_by_x = abs(client_rect[0] - region.x)
    offset_by_y = abs(client_rect[1] - region.y)

    on_region = (offset_by_x <= 5 and offset_by_y <= 5 and
                 abs(client_rect[2] - region.w) <= 5 and abs(client_rect[3] - region.h) <= 5)
                    
    return on_region

def set_client_to_region(region: Region | None):       
    if region:
        Console.set_window_geometry(region.x, region.y, region.w, region.h)

        time.sleep(0.1)
        Console.set_window_geometry(region.x, region.y, region.w, region.h)
            
    pass    

def main():    
    global throttle_timer, last_character_name, last_rename_type, last_append_gw, is_on_main, toggled_widget_ui, screen_size_changed, initial_resized, module_info
    
    try:                    
        if settings.accounts:
            draw()
        
    except Exception as e:
        Py4GW.Console.Log(MODULE_NAME, f"Error in draw(): {e}",  Console.MessageType.Error)
    
    if not Routines.Checks.Map.MapValid():
        return 
    
    
    if throttle_timer.IsExpired():
        throttle_timer.Reset()
        
        is_active = is_window_active() ## Should be Console.is_window_active() once fixed
        settings.set_accounts(GLOBAL_CACHE.ShMem.GetAllAccountData())
        
        HandleReceivedMessages()
        set_client_title()
            
        if settings.accounts:            
            account_data = next((acc for acc in settings.accounts if acc.AccountEmail == settings.get_account_mail()), None)
            
            if account_data and account_data.AccountEmail:                      
                region = next((r for r in settings.regions if r.account == account_data.AccountEmail), None) if settings.regions else None
                is_main = region and region.main
                main_region = settings.main_region
                
                desired_region = main_region if (is_main or (is_active and settings.move_slave_to_main)) else region
                
                if desired_region and settings.move_on_focus and not is_client_in_region(desired_region):
                    if settings.move_on_focus:
                        set_client_to_region(desired_region)
        
                if (is_main or is_active) and (not is_main or toggled_widget_ui):
                    set_widget_visibility(True)
                    
                elif (not is_active and not is_main) and settings.move_slave_to_main:
                    set_widget_visibility(False)
                    toggled_widget_ui = True                                                    

def set_client_title():
    global last_character_name, last_rename_type, last_append_gw
    
    current_account = next((acc for acc in settings.accounts if acc.AccountEmail == settings.get_account_mail()), None)
        
    if current_account and (last_character_name != current_account.CharacterName or last_rename_type != settings.rename_to or last_append_gw != settings.append_gw):
        match settings.rename_to:
            case RenameClientType.Custom:
                new_title = settings.custom_names.get(current_account.AccountEmail, "")
            case RenameClientType.Email:
                new_title = current_account.AccountEmail if current_account else ""
            case RenameClientType.Character:
                new_title = current_account.CharacterName if current_account else ""
            case RenameClientType.No_Rename:
                new_title = "Guild Wars"
            case _:
                new_title = ""
                
        if new_title:
            if settings.append_gw and settings.rename_to is not RenameClientType.No_Rename:
                new_title += " - Guild Wars"

            set_window_title(new_title)
            last_character_name = current_account.CharacterName if current_account else ""
            last_rename_type = settings.rename_to
            last_append_gw = settings.append_gw            

__all__ = ['main', 'configure']
