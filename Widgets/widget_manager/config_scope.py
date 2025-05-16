from Py4GWCoreLib import UIManager, Map, Party
# config_scope.py
selected_settings_scope = 0  # 0 = Global, 1 = Account
character_select = False

def use_account_settings():
    return selected_settings_scope == 1

def is_in_character_select():
    if Party.IsPartyLoaded():
        return False
    
    cs_base = UIManager.GetFrameIDByHash(2232987037)
    cs_c0 = UIManager.GetChildFrameID(2232987037, [0])
    cs_c1 = UIManager.GetChildFrameID(2232987037, [1])
    ig_menu = UIManager.GetFrameIDByHash(1144678641)
    
    frames = {
        "cs_base": cs_base,
        "cs_c0": cs_c0,
        "cs_c1": cs_c1,
        "ig_menu": ig_menu,
    }
    
    in_load_screen = all(isinstance(f, int) and f == 0 for f in frames.values())
    in_char_select = (
        not in_load_screen and
        any(isinstance(f, int) and f > 0 for f in (cs_base, cs_c0, cs_c1)) and 
        not Party.IsPartyLoaded()
    )
    
    return in_char_select
