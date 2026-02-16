from typing import Callable

import PyImGui
from Py4GWCoreLib.enums_src.IO_enums import Key, ModifierKey
from Py4GWCoreLib.py4gwcorelib_src import Console

class HotKey():
    def __init__(self,  identifier: str, callback: Callable, key: Key, name: str = "",  modifiers : ModifierKey = ModifierKey.NoneKey):
        self.key = key
        self.modifiers = modifiers
        self.identifier = identifier
        self.name = name if name else identifier
        self.callback = callback

    def matches(self, key: Key, modifiers : ModifierKey):
        return self.key == key and self.modifiers == modifiers
        
    def format_hotkey(self) -> str:
        mods = self.format_modifiers(self.modifiers)
        if mods:
            return f"{mods}+{self.key.name.replace('VK_','')}"
        
        return self.key.name.replace('VK_','')
        
    def format_modifiers(self, modifiers: ModifierKey) -> str:
        if modifiers == ModifierKey.NoneKey:
            return ""

        parts = []
        for mod in ModifierKey:
            if mod is ModifierKey.NoneKey:
                continue
            if modifiers & mod:
                parts.append(mod.name)

        return "+".join(parts)

class HotkeyManager():
    __instance = None
    __initialized = False
    
    def __new__(cls):
        if cls.__instance is None:
            cls.__instance = super(HotkeyManager, cls).__new__(cls)
        return cls.__instance
    
    def __init__(self):
        if not self.__initialized:
            self.__initialized = True
            self.hotkeys : dict[str, HotKey] = {}
    
    def register_hotkey(self, key: Key, identifier: str, callback: Callable, name: str = "", modifiers : ModifierKey = ModifierKey.NoneKey) -> HotKey:      
        self.hotkeys[identifier] = HotKey(identifier=identifier, name=name, callback=callback, key=key, modifiers=modifiers)
        return self.hotkeys[identifier]
        
    def unregister_hotkey(self, identifier: str):
        if identifier in self.hotkeys:
            del self.hotkeys[identifier]
            
    def update(self, log: bool = False):
        from Py4GWCoreLib.py4gwcorelib_src.Console import ConsoleLog
        
        io = PyImGui.get_io()
        modifiers = ModifierKey.NoneKey
        
        if io.key_shift:
            modifiers |= ModifierKey.Shift
            
        if io.key_ctrl:
            modifiers |= ModifierKey.Ctrl
            
        if io.key_alt:
            modifiers |= ModifierKey.Alt
                                         
        assigned_keys = [hotkey.key for hotkey in self.hotkeys.values()]    
        for key in assigned_keys:
            if key is Key.Unmapped or key is Key.Unused or key is Key.Unmappable or key is Key.VK_0x00:
                continue
            
            hot_keys = {identifier: hotkey for identifier, hotkey in self.hotkeys.items() if hotkey.key == key}
            
            if PyImGui.is_key_pressed(key.value):
                for hotkey in hot_keys.values():
                    if hotkey.matches(key, modifiers):
                        
                        try:
                            ConsoleLog("HotkeyManager", f"Executing hotkey '{hotkey.name}' with identifier '{hotkey.identifier}' for hotkey '{hotkey.format_hotkey()}'", message_type=Console.Console.MessageType.Debug, log=log)
                            hotkey.callback()
                        except Exception as e:
                            ConsoleLog("HotkeyManager", f"Error while executing hotkey '{hotkey.name}' with identifier '{hotkey.identifier}' for hotkey '{hotkey.format_hotkey()}': {e}", message_type=Console.Console.MessageType.Error, log=log)
    
HOTKEY_MANAGER = HotkeyManager()