from Py4GWCoreLib.Agent import Agent
from Py4GWCoreLib.AgentArray import AgentArray
from Py4GWCoreLib.Item import Item
from Py4GWCoreLib.Player import Player
from Py4GWCoreLib.Routines import Routines
from Py4GWCoreLib.enums_src.GameData_enums import Range
from Py4GWCoreLib.enums_src.Item_enums import ItemType
from Sources.frenkeyLib.ItemHandling.Items.item_snapshot import ItemSnapshot
from Sources.frenkeyLib.ItemHandling.Rules.profile import RuleProfile
from Sources.frenkeyLib.ItemHandling.Rules.types import ItemAction


class LootHandler:
    def __init__(self):
        self.enabled: bool = False
        
        self.rules : RuleProfile = RuleProfile.load_by_name("Default Looting Rules")
        self.item_id_blacklist = set()  # For items that are blacklisted by ID
        self.item_id_whitelist = set()  # For items that are whitelisted by ID
        
    def run(self):
        if not self.enabled:
            return
        
        # Handle loot actions here based on your rules and requirements
        pass
    
    def start(self):
        self.enabled = True
    
    def stop(self):
        self.enabled = False
        
    # ------- Item ID Whitelist management -------    
    def AddItemIDToWhitelist(self, item_id: int):
        self.item_id_whitelist.add(item_id)
        
    def RemoveItemIDFromWhitelist(self, item_id: int):
        self.item_id_whitelist.discard(item_id)
    
    def ClearItemIDWhitelist(self):
        self.item_id_whitelist.clear()
        
    def IsItemIDWhitelisted(self, item_id: int):
        return item_id in self.item_id_whitelist
        
    # ------- Item ID Blacklist management -------   
    def AddItemIDToBlacklist(self, item_id: int):
        self.item_id_blacklist.add(item_id)
   
    def RemoveItemIDFromBlacklist(self, item_id: int):
        self.item_id_blacklist.discard(item_id)

    def ClearItemIDBlacklist(self):
        self.item_id_blacklist.clear()

    def IsItemIDBlacklisted(self, item_id: int):
        return item_id in self.item_id_blacklist

    def GetItemIDBlacklist(self):
        return list(self.item_id_blacklist)
    
    
    # ------- Loot Filtering Logic -------
    def GetfilteredLootArray(self, distance: float = Range.SafeCompass.value, multibox_loot: bool = False, allow_unasigned_loot=False) -> list[int]:
        def IsValidItem(item_id):
            if not Agent.IsValid(item_id):
                return False    
            
            player_agent_id = Player.GetAgentID()
            owner_id = Agent.GetItemAgentOwnerID(item_id)
            return ((owner_id == player_agent_id) or (owner_id == 0))
        
        if not Routines.Checks.Map.MapValid():
            return []
            
        loot_array = AgentArray.GetItemArray()
        loot_array = AgentArray.Filter.ByDistance(loot_array, Player.GetXY(), distance)
        loot_array = AgentArray.Filter.ByCondition(
            loot_array,
            lambda item_id: IsValidItem(item_id)
        )
        
        pick_up_array = []

        for agent_id in loot_array[:]:  # Iterate over a copy to avoid modifying while iterating
            item_data = Agent.GetItemAgentByID(agent_id)
            if item_data is None:
                continue
            
            item_id = item_data.item_id
            
            # --- Hard block: blacklists ---
            if self.IsItemIDBlacklisted(agent_id):
                continue
            
            # --- Whitelists ---
            if self.IsItemIDWhitelisted(item_id):
                pick_up_array.append(agent_id)
                continue
            
            action = self.rules.get_action_for_item(item_id)
            item = ItemSnapshot.from_item_id(item_id) if item_id else None  # Ensure the item snapshot is cached for future reference
            if action != ItemAction.PickUp:
                continue
            
            pick_up_array.append(agent_id)
            
        pick_up_array = AgentArray.Sort.ByDistance(pick_up_array, Player.GetXY())

        return pick_up_array