from Py4GWCoreLib import *
# config_scope.py
selected_settings_scope = 0  # 0 = Global, 1 = Account

def use_account_settings():
    return selected_settings_scope == 1

def is_in_character_select():
    cs_base = UIManager.GetFrameIDByHash(2232987037)
    cs_c0 = UIManager.GetChildFrameID(2232987037, [0])
    cs_c1 = UIManager.GetChildFrameID(2232987037, [1])
    
    visible = [
        not UIManager.IsWindowVisible(cs_c0),
        not UIManager.IsWindowVisible(cs_c1),
        not UIManager.IsWindowVisible(cs_base),
    ]
    
    return any(visible)
