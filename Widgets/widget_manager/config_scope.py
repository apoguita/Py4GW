# config_scope.py
selected_settings_scope = 0  # 0 = Global, 1 = Account

def use_account_settings():
    return selected_settings_scope == 1