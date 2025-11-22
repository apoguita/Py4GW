from Py4GWCoreLib import Agent, AgentArray, Player
from Py4GWCoreLib.GlobalCache import GLOBAL_CACHE
from Widgets.frenkey.LootEx.cache import Cached_Item
from Widgets.frenkey.LootEx.enum import ItemAction
from Py4GWCoreLib.Py4GWcorelib import ConsoleLog, LootConfig
from Py4GWCoreLib.enums import Console, ItemType, ModelID, Range, SharedCommandType


class LootHandler:
    _instance = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        from Widgets.frenkey.LootEx.settings import Settings
        
        # only initialize once
        if self._initialized:
            return
        self._initialized = True
        self.settings = Settings()

    def reset(self):                
        if self.settings.profile is None:
            return
        
        pass
    
    def Stop(self):
        ConsoleLog("LootEx", "Stopping Loot Handler", Console.MessageType.Info)
        
        lootconfig = LootConfig()
        lootconfig.RemoveCustomItemCheck(self.Should_Loot_Item)
        
        from Widgets.frenkey.LootEx.settings import Settings
        settings = Settings()
        settings.enable_loot_filters = False
        settings.save()
        

    def Start(self):
        ConsoleLog("LootEx", "Starting Loot Handler", Console.MessageType.Info)        
    
        lootconfig = LootConfig()
        lootconfig.AddCustomItemCheck(self.Should_Loot_Item)
        
        lootconfig.AddToBlacklist(6102)  # Spear of Archemorus
        lootconfig.AddToBlacklist(6104)  # Urn of Saint Viktor
        
        from Widgets.frenkey.LootEx.settings import Settings
        settings = Settings()
        settings.enable_loot_filters = True
        settings.save()
        

    def SetLootRange(self, loot_range: int):
        if self.settings.profile is None:
            ConsoleLog("LootEx", "No profile selected. Cannot set loot range.", Console.MessageType.Warning)
            return
                
        for index, message in GLOBAL_CACHE.ShMem.GetAllMessages():            
            if message.Command == SharedCommandType.PickUpLoot:
                GLOBAL_CACHE.ShMem.MarkMessageAsFinished(message.ReceiverEmail, index)                  
    
    def LootingRoutineActive(self):
        account_email = GLOBAL_CACHE.Player.GetAccountEmail()
        index, message = GLOBAL_CACHE.ShMem.PreviewNextMessage(account_email)
        
        if index == -1 or message is None:
            return False
        
        if message.Command != SharedCommandType.PickUpLoot:
            return False
        
        return True
                  
    def IsEnabled(self) -> bool:
        return self.settings.enable_loot_filters and self.settings.profile is not None
                        
    def Should_Loot_Item(self, item_id: int) -> bool:
        # ConsoleLog("LootEx", f"Checking if item {item_id} should be looted.", Console.MessageType.Debug)
                
        if self.settings.profile is None:
            ConsoleLog("LootEx", "No profile selected. Cannot determine loot action.", Console.MessageType.Warning)
            return False
        
        if self.settings.enable_loot_filters == False:
            return False
        
        cached_item = Cached_Item(item_id)
                
        if not cached_item.data:
            if cached_item.item_type != ItemType.Bundle:
                ConsoleLog("LootEx", f"Item {item_id} has no cached data. Cannot determine loot action.", Console.MessageType.Warning)
                return True
        
        if cached_item.model_id == ModelID.Vial_Of_Dye:
            if cached_item.IsVial_Of_DyeToKeep():
                # ConsoleLog("LootEx", f"Item {item_id} is a Vial of Dye that we want to keep.", Console.MessageType.Debug)
                return True
            else:
                # ConsoleLog("LootEx", f"Item {item_id} is a Vial of Dye that we do not want to keep.", Console.MessageType.Debug)
                return False
        
        if cached_item.matches_weapon_rule:
            ConsoleLog("LootEx", f"Item {item_id} matches weapon rule. Should loot.", Console.MessageType.Debug)
            return True
        
        if cached_item.matches_skin_rule:
            ConsoleLog("LootEx", f"Item {item_id} matches skin rule. Should loot.", Console.MessageType.Debug)
            return True

        for filter in self.settings.profile.filters:
            action = filter.get_action(cached_item)

            if action == ItemAction.Loot:
                ConsoleLog("LootEx", f"Item {item_id} matches filter rule. Should loot.", Console.MessageType.Debug)
                return True
        
        # If the item is a salvage item we check for runes we want to pick up and sell
        if cached_item.is_armor:
            if cached_item.runes_to_keep:
                ConsoleLog("LootEx", f"Item {item_id} is armor with runes to keep. Should loot.", Console.MessageType.Debug)
                return True
        
        # If the item is a weapon we check if it has a weapon mod we want to keep
        if cached_item.is_weapon:
            if cached_item.weapon_mods_to_keep:
                ConsoleLog("LootEx", f"Item {item_id} is weapon with mods to keep. Should loot.", Console.MessageType.Debug)
                return True
            
        return False