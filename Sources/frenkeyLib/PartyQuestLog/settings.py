
import os
from typing import Optional

from Py4GWCoreLib.GlobalCache.SharedMemory import AccountData
from Py4GWCoreLib.HotkeyManager import HotKey
from Py4GWCoreLib.enums_src.IO_enums import Key, ModifierKey
from Py4GWCoreLib.py4gwcorelib_src.IniHandler import IniHandler
from Py4GWCoreLib.py4gwcorelib_src.Console import Console, ConsoleLog
from Py4GWCoreLib.py4gwcorelib_src.Timer import ThrottledTimer


class Settings:
    _instance = None
    _initialized = False    
        
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Settings, cls).__new__(cls)
        return cls._instance
    
    def __init__(self): 
        # guard: only initialize once
        if self.__class__._initialized:
            return
        
        self.__class__._initialized = True
        
        base_path = Console.get_projects_path()
        self.ini_path = os.path.join(base_path, "Widgets", "Config", "PartyQuestLog.ini")
        
        self.save_requested = False        
        if not os.path.exists(self.ini_path):
            ConsoleLog("Party Quest Log", "Settings file not found. Creating default settings...")
            self.save_requested = True  
        
        self.save_throttle_timer = ThrottledTimer(1000)
        self.ini_handler = IniHandler(self.ini_path)
        
        self.LogOpen : bool = False
        self.LogPosX : float = 0
        self.LogPosY : float = 0
        self.LogPosHeight : float = 800
        self.LogPosWidth : float = 300
            
        self.ShowOnlyInParty : bool = True
        self.ShowOnlyOnLeader : bool = True
        self.ShowFollowerActiveQuestOnMinimap : bool = True
        self.ShowFollowerActiveQuestOnMissionMap : bool = True
        
        self.HotKeyKey : Key = Key.L
        self.Modifiers : ModifierKey = ModifierKey.Ctrl
        
        self.hotkey : Optional[HotKey] = None
        self.show_quests_for_accounts : dict[str, bool] = {}
            
    def save_settings(self):
        self.save_requested = True
    
    def write_settings(self):               
        if not self.save_requested:
            return
        
        if not self.save_throttle_timer.IsExpired():
            return        
        
        self.save_throttle_timer.Reset()
        self.save_requested = False
        
        self.ini_handler.write_key("Window", "LogOpen", str(self.LogOpen))
        self.ini_handler.write_key("Window", "LogPosX", str(self.LogPosX))
        self.ini_handler.write_key("Window", "LogPosY", str(self.LogPosY))
        self.ini_handler.write_key("Window", "LogPosHeight", str(self.LogPosHeight))
        self.ini_handler.write_key("Window", "LogPosWidth", str(self.LogPosWidth))
        
        self.ini_handler.write_key("QuestLog", "ShowOnlyInParty", str(self.ShowOnlyInParty))
        self.ini_handler.write_key("QuestLog", "ShowOnlyOnLeader", str(self.ShowOnlyOnLeader))
        
        self.ini_handler.write_key("Overlays", "ShowFollowerActiveQuestOnMinimap", str(self.ShowFollowerActiveQuestOnMinimap))
        self.ini_handler.write_key("Overlays", "ShowFollowerActiveQuestOnMissionMap", str(self.ShowFollowerActiveQuestOnMissionMap))
        
        self.ini_handler.write_key("Hotkey", "HotKeyKey", self.HotKeyKey.name.replace('VK_',''))
        self.ini_handler.write_key("Hotkey", "Modifiers", self.Modifiers.name)
        
        for account_email, enabled in self.show_quests_for_accounts.items():
            self.ini_handler.write_key("OverlayAccounts", account_email, str(enabled))
        
    def load_settings(self):
        self.LogOpen = self.ini_handler.read_bool("Window", "LogOpen", self.LogOpen)
        self.LogPosX = self.ini_handler.read_float("Window", "LogPosX", self.LogPosX)
        self.LogPosY = self.ini_handler.read_float("Window", "LogPosY", self.LogPosY)
        self.LogPosHeight = self.ini_handler.read_float("Window", "LogPosHeight", self.LogPosHeight)
        self.LogPosWidth = self.ini_handler.read_float("Window", "LogPosWidth", self.LogPosWidth)
        
        self.ShowOnlyInParty = self.ini_handler.read_bool("QuestLog", "ShowOnlyInParty", self.ShowOnlyInParty)
        self.ShowOnlyOnLeader = self.ini_handler.read_bool("QuestLog", "ShowOnlyOnLeader", self.ShowOnlyOnLeader)
        self.ShowFollowerActiveQuestOnMinimap = self.ini_handler.read_bool("Overlays", "ShowFollowerActiveQuestOnMinimap", self.ShowFollowerActiveQuestOnMinimap)
        self.ShowFollowerActiveQuestOnMissionMap = self.ini_handler.read_bool("Overlays", "ShowFollowerActiveQuestOnMissionMap", self.ShowFollowerActiveQuestOnMissionMap)
        
        hotkeykey = self.ini_handler.read_key("Hotkey", "HotKeyKey", "VK_L")
        modifiers = self.ini_handler.read_key("Hotkey", "Modifiers", "Ctrl")
        
        try:
            self.HotKeyKey = Key[hotkeykey]
            ConsoleLog("Party Quest Log", f"Loaded HotKeyKey '{hotkeykey}' from settings.")
            
        except KeyError:
            ConsoleLog("Party Quest Log", f"Invalid HotKeyKey '{hotkeykey}' in settings. Using default 'VK_L'.")
            self.HotKeyKey = Key.L
            
        try:
            self.Modifiers = ModifierKey[modifiers]
            ConsoleLog("Party Quest Log", f"Loaded Modifiers '{modifiers}' from settings.")
            
        except KeyError:
            ConsoleLog("Party Quest Log", f"Invalid Modifiers '{modifiers}' in settings. Using default 'Ctrl'.")
            self.Modifiers = ModifierKey.Ctrl
            
        account_section = self.ini_handler.list_keys("OverlayAccounts")

        if account_section:
            for account_email, _ in account_section.items():
                self.show_quests_for_accounts[account_email] = self.ini_handler.read_bool("OverlayAccounts", account_email, True)
        pass

    def set_questlog_hotkey_keys(self, key: Key, modifiers: ModifierKey):
        self.HotKeyKey = key
        self.Modifiers = modifiers
        
        if self.hotkey:
            self.hotkey.key = key
            self.hotkey.modifiers = modifiers
            
        self.save_settings()
    
    