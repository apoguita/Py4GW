from Py4GWCoreLib import Map
from Py4GWCoreLib.GlobalCache import GLOBAL_CACHE
from Py4GWCoreLib.GlobalCache.SharedMemory import AccountData, HeroAIOptionStruct
from Py4GWCoreLib.py4gwcorelib_src.Console import ConsoleLog


class PartyCache():
    def __init__(self):
        super().__init__()
        
        self.accounts : dict[int, AccountData] = {}
        self.options : dict[int, HeroAIOptionStruct] = {}
        
        self.party_id = 0
        
    def __iter__(self):
        """ Iterate over all accounts in the party cache. """
        for acc in self.accounts.values():
            yield acc
    
    def get_by_player_id(self, player_id: int) -> AccountData | None:
        """ Get account data by player ID. """
        return self.accounts.get(player_id, None)
    
    def get_by_party_pos(self, party_pos: int) -> AccountData | None:
        """ Get account data by party position. """
        for acc in self.accounts.values():
            if acc.PartyPosition == party_pos:
                return acc
        
        return None
    
    def reset(self):
        """ Reset the party cache. """
        self.accounts.clear()
        self.party_id = 0
        
    def update(self):
        """ Update the party cache from shared memory. """
        from HeroAI.utils import SameMapOrPartyAsAccount
        self.party_id = GLOBAL_CACHE.Party.GetPartyID()
        
        shmem_accounts = GLOBAL_CACHE.ShMem.GetAllAccountData()
        
        for acc in shmem_accounts:
            if acc.IsSlotActive and SameMapOrPartyAsAccount(acc):
                self.accounts[acc.PlayerID] = acc
                
                options = GLOBAL_CACHE.ShMem.GetHeroAIOptions(acc.AccountEmail)
                
                if options is None:
                    ConsoleLog("PartyCache", f"Account {acc.AccountEmail} has no HeroAI options in shared memory, creating default options.")
                    
                self.options[acc.PlayerID] = options if options is not None else HeroAIOptionStruct()