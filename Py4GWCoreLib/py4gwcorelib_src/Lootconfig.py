from ..enums_src.GameData_enums import Range
from ..enums_src.Model_enums import ModelID

#region ConfigCalsses
class LootConfig:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(LootConfig, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self.reset()
        self._initialized = True

    def reset(self):
        self.loot_gold_coins = False
        self.loot_whites = False
        self.loot_blues = False
        self.loot_purples = False
        self.loot_golds = False
        self.loot_greens = False
        self.whitelist = set()  # Avoid duplicates
        self.blacklist = set()
        self.item_id_blacklist = set()  # For items that are blacklisted by ID
        self.item_id_whitelist = set()  # For items that are whitelisted by ID
        self.dye_whitelist = set()
        self.dye_blacklist = set()

    def SetProperties(self, loot_whites=False, loot_blues=False, loot_purples=False, loot_golds=False, loot_greens=False, loot_gold_coins=False):
        self.loot_gold_coins = loot_gold_coins
        self.loot_whites = loot_whites
        self.loot_blues = loot_blues
        self.loot_purples = loot_purples
        self.loot_golds = loot_golds
        self.loot_greens = loot_greens

    # ------- Whitelist management -------
    def AddToWhitelist(self, model_id: int):
        self.whitelist.add(model_id)
        
    def RemoveFromWhitelist(self, model_id: int):
        self.whitelist.discard(model_id)
        
    def ClearWhitelist(self):
        self.whitelist.clear()
    
    def IsWhitelisted(self, model_id: int):
        return model_id in self.whitelist
    
    def GetWhitelist(self):
        return list(self.whitelist)
        
    # ------- Blacklist management ------
    def AddToBlacklist(self, model_id: int):
        self.blacklist.add(model_id)
        
    def RemoveFromBlacklist(self, model_id: int):
        self.blacklist.discard(model_id)
        
    def ClearBlacklist(self):
        self.blacklist.clear()
        
    def IsBlacklisted(self, model_id: int):
        return model_id in self.blacklist
    
    def GetBlacklist(self):
        return list(self.blacklist)
        
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
    
    # === Dye-based lists (by dye1 int) ===
    # -- Dye Whitelist management -------
    def AddToDyeWhitelist(self, dye1_int: int):
        self.dye_whitelist.add(dye1_int)

    def RemoveFromDyeWhitelist(self, dye1_int: int):
        self.dye_whitelist.discard(dye1_int)
        
    def ClearDyeWhitelist(self):
        self.dye_whitelist.clear()
        
    def IsDyeWhitelisted(self, dye1_int: int):
        return dye1_int in self.dye_whitelist
    
    def GetDyeWhitelist(self):
        return list(self.dye_whitelist)
        
    # -- Dye Blacklist management -------
    def AddToDyeBlacklist(self, dye1_int: int):
        self.dye_blacklist.add(dye1_int)

    def RemoveFromDyeBlacklist(self, dye1_int: int):
        self.dye_blacklist.discard(dye1_int)

    def ClearDyeBlacklist(self):
        self.dye_blacklist.clear()

    def IsDyeBlacklisted(self, dye1_int: int):
        return dye1_int in self.dye_blacklist

    def GetDyeBlacklist(self):
        return list(self.dye_blacklist)

    def GetfilteredLootArray(self, distance: float = Range.SafeCompass.value, multibox_loot: bool = False, allow_unasigned_loot=False) -> list[int]:
        from ..AgentArray import AgentArray
        from ..GlobalCache import GLOBAL_CACHE
        from ..Routines import Routines
        from ..Agent import Agent
        from ..Item import Item
        from ..Player import Player
        from ..Party import Party
        
        def IsValidItem(item_id):
            if not Agent.IsValid(item_id):
                return False    
            player_agent_id = Player.GetAgentID()
            owner_id = Agent.GetItemAgentOwnerID(item_id)
            return ((owner_id == player_agent_id) or (owner_id == 0))
        
        def IsValidLeaderItem(item_id, allow_unasigned_loot: bool):
            if not Agent.IsValid(item_id):
                return False
            
            player_agent_id = Player.GetAgentID()
            owner_id = Agent.GetItemAgentOwnerID(item_id)

            # Always pick up own items
            if owner_id == player_agent_id:
                return True

            # Always pick up gold coins (if unassigned)
            agent = Agent.agent_instance(item_id)
            item_agent_id = agent.item_agent.item_id
            model_id = Item.GetModelID(item_agent_id)
            if model_id == ModelID.Gold_Coins.value and owner_id == 0:
                return True

            # If allowed, pick up other unassigned items
            if allow_unasigned_loot and owner_id == 0:
                return True

            return False

        def IsValidFollowerItem(item_id):
            if not Agent.IsValid(item_id):
                return False
            
            player_agent_id = Player.GetAgentID()
            owner_id = Agent.GetItemAgentOwnerID(item_id)

            # Followers only pick up their own items
            return owner_id == player_agent_id

        
        if not Routines.Checks.Map.MapValid():
            return []
            
        loot_array = AgentArray.GetItemArray()
        loot_array = AgentArray.Filter.ByDistance(loot_array, Player.GetXY(), distance)

        party_leader_id = Party.GetPartyLeaderID()
        player_agent_id = Player.GetAgentID()

        if party_leader_id == player_agent_id:  # Leader or solo
            loot_array = AgentArray.Filter.ByCondition(
                loot_array, lambda item_id: IsValidLeaderItem(item_id, allow_unasigned_loot)
            )
        else:  # Follower
            loot_array = AgentArray.Filter.ByCondition(
                loot_array, lambda item_id: IsValidFollowerItem(item_id)
            )



        for agent_id in loot_array[:]:  # Iterate over a copy to avoid modifying while iterating
            item_data = Agent.GetItemAgent(agent_id)
            item_id = item_data.item_id
            model_id = Item.GetModelID(item_id)
            
            # --- Hard block: blacklists ---
            if self.IsItemIDBlacklisted(item_id):
                loot_array.remove(agent_id)
                continue

            if self.IsBlacklisted(model_id):
                loot_array.remove(agent_id)
                continue

            # --- Whitelists ---
            if self.IsItemIDWhitelisted(item_id):
                continue

            if self.IsWhitelisted(model_id):
                continue

                
            # Rarity filtering
            if Item.Rarity.IsWhite(item_id):
                if not self.loot_whites:
                    loot_array.remove(agent_id)
                    continue

            if Item.Rarity.IsBlue(item_id):
                if not self.loot_blues:
                    loot_array.remove(agent_id)
                    continue

            if Item.Rarity.IsPurple(item_id):
                if not self.loot_purples:
                    loot_array.remove(agent_id)
                    continue

            if Item.Rarity.IsGold(item_id):
                if not self.loot_golds:
                    loot_array.remove(agent_id)
                    continue

            if Item.Rarity.IsGreen(item_id):
                if not self.loot_greens:
                    loot_array.remove(agent_id)
                    continue

        loot_array = AgentArray.Sort.ByDistance(loot_array, Player.GetXY())

        return loot_array
#endregion