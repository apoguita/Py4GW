import ctypes
from operator import index
import Py4GW
from PyParty import HeroPartyMember, PetInfo
from ctypes import Structure, c_float
from Py4GWCoreLib.enums_src.Multiboxing_enums import SharedCommandType
from Py4GWCoreLib.enums_src.Whiteboard_enums import (
    WhiteboardClaimStrength,
    WhiteboardLockKind,
    WhiteboardLockMode,
    WhiteboardReentryPolicy,
)
from Py4GWCoreLib.py4gwcorelib_src.Console import ConsoleLog

from .Globals import (
    SHMEM_MAX_PLAYERS,
    SHMEM_MODULE_NAME,
    SHMEM_SUBSCRIBE_TIMEOUT_MILLISECONDS,
    SHMEM_MAX_CHAR_LEN,
    SHMEM_MAX_NUMBER_OF_SKILLS,
    SHMEM_MAX_INTENTS,
)

from .SharedMessageStruct import SharedMessageStruct
from .HeroAIOptionStruct import HeroAIOptionStruct
from .AccountStruct import AccountStruct
from .KeyStruct import KeyStruct
from .IntentStruct import IntentStruct

# Master toggle for ALL whiteboard POST/CLEAR/SWEEP console logs.
# Set to False to silence everything in one place.
#
# Runtime toggle:
#   from Py4GWCoreLib.GlobalCache.shared_memory_src import AllAccounts as _wb_mod
#   _wb_mod.WHITEBOARD_DEBUG = False
WHITEBOARD_DEBUG: bool = True

# Per-kind overrides keyed by WhiteboardLockKind int value. Missing key
# falls back to WHITEBOARD_DEBUG. Present + False silences that kind even
# when WHITEBOARD_DEBUG is True. Use this to focus on one lock kind during
# debugging without losing the rest.
#
# Runtime toggle (silence SKILL_TARGET spam, keep HEX_REMOVAL_TARGET):
#   from Py4GWCoreLib.GlobalCache.shared_memory_src import AllAccounts as _wb_mod
#   from Py4GWCoreLib.enums_src.Whiteboard_enums import WhiteboardLockKind
#   _wb_mod.WHITEBOARD_DEBUG_KINDS[int(WhiteboardLockKind.SKILL_TARGET)] = False
WHITEBOARD_DEBUG_KINDS: dict[int, bool] = {
    int(WhiteboardLockKind.SKILL_TARGET): False,
}
_HERO_SUBMIT_RETRY_AFTER: dict[tuple[int, int], int] = {}
_PET_SUBMIT_RETRY_AFTER: dict[tuple[int, int], int] = {}
_SLOT_SUBMIT_RETRY_COOLDOWN_MS = 5000

#region AllAccounts
class AllAccounts(Structure):
    _pack_ = 1
    _fields_ = [
        ("Keys", KeyStruct * SHMEM_MAX_PLAYERS),  # KeyStruct for each player slot
        ("AccountData", AccountStruct * SHMEM_MAX_PLAYERS),
        ("Inbox", SharedMessageStruct * SHMEM_MAX_PLAYERS),  # Messages for each player
        ("HeroAIOptions", HeroAIOptionStruct * SHMEM_MAX_PLAYERS),  # Game options for HeroAI
        ("Intents", IntentStruct * SHMEM_MAX_INTENTS),  # Cross-hero cast-intent whiteboard
    ]

    # Type hints for IntelliSense
    AccountData: list["AccountStruct"]
    Inbox: list["SharedMessageStruct"]
    HeroAIOptions: list[HeroAIOptionStruct]
    Keys: list["KeyStruct"]
    Intents: list["IntentStruct"]

    def reset(self) -> None:
        """Reset all fields to zero."""
        for i in range(SHMEM_MAX_PLAYERS):
            self.Keys[i].reset()
            self.AccountData[i].reset()
            self.Inbox[i].reset()
            self.HeroAIOptions[i].reset()
        for i in range(SHMEM_MAX_INTENTS):
            self.Intents[i].reset()
            
    #region Account
    def GetAccountData(self, index: int) -> AccountStruct:
        if index < 0 or index >= SHMEM_MAX_PLAYERS:
            raise IndexError(f"Index {index} is out of bounds for max players {SHMEM_MAX_PLAYERS}.")
        return self.AccountData[index]
    
    def _is_slot_active(self, index: int) -> bool:
        """Check if the slot at the given index is active."""
        slot_data = self.GetAccountData(index)
        slot_active = slot_data.IsSlotActive    
        last_updated = slot_data.LastUpdated
        
        base_timestamp = Py4GW.Game.get_tick_count64()
        
        if slot_active and (base_timestamp - last_updated) < SHMEM_SUBSCRIBE_TIMEOUT_MILLISECONDS:
            return True
        return False

    def _is_visible_account(self, index: int) -> bool:
        if not self._is_slot_active(index):
            return False
        account = self.AccountData[index]
        return account.IsAccount and not self._is_slot_isolated(index)

    def _is_visible_slot(self, index: int) -> bool:
        if not self._is_slot_active(index):
            return False
        return not self._is_slot_isolated(index)

    def _get_slot_group(self, index: int) -> int:
        """Return IsolationGroupID for slot; hero/pet inherits owner's group."""
        account = self.AccountData[index]
        if account.IsAccount:
            return int(account.IsolationGroupID)
        owner_email = account.AccountEmail
        if not owner_email:
            return 0
        owner_index = self._find_account_slot_by_email(owner_email)
        if owner_index == -1:
            return 0
        return int(self.AccountData[owner_index].IsolationGroupID)

    def _get_local_group_id(self) -> int:
        """Return the local player's IsolationGroupID."""
        try:
            from ...Player import Player
            email = Player.GetAccountEmail()
            if not email:
                return 0
            index = self._find_account_slot_by_email(email)
            if index == -1:
                return 0
            return int(self.AccountData[index].IsolationGroupID)
        except Exception:
            return 0

    def _get_local_account_email(self) -> str:
        try:
            from ...Player import Player
            return str(Player.GetAccountEmail() or "").strip()
        except Exception:
            return ""

    def _get_slot_owner_email(self, index: int) -> str:
        account = self.AccountData[index]
        if account.IsAccount:
            return str(account.AccountEmail or "").strip()
        return str(account.AccountEmail or "").strip()

    def _is_slot_owned_by_email(self, index: int, account_email: str) -> bool:
        if not account_email:
            return False
        return self._get_slot_owner_email(index) == account_email

    def _is_local_owned_slot(self, index: int) -> bool:
        local_email = self._get_local_account_email()
        if not local_email:
            return False
        return self._is_slot_owned_by_email(index, local_email)

    def _is_slot_isolated(self, index: int) -> bool:
        if self._is_local_owned_slot(index):
            return False

        local_g = self._get_local_group_id()
        target_g = self._get_slot_group(index)
        if local_g > 0:
            return target_g != local_g
        elif target_g > 0:
            return True
        account = self.AccountData[index]
        if account.IsAccount:
            return bool(account.IsIsolated)
        owner_email = account.AccountEmail
        if not owner_email:
            return False
        owner_index = self._find_account_slot_by_email(owner_email)
        if owner_index == -1:
            return False
        return bool(self.AccountData[owner_index].IsAccount and self.AccountData[owner_index].IsIsolated)

    def _is_slot_isolated_from_viewer(self, index: int, viewer_index: int) -> bool:
        """Like _is_slot_isolated but with explicit viewer slot instead of local player."""
        if index == viewer_index:
            return False

        viewer_email = self._get_slot_owner_email(viewer_index)
        if viewer_email and self._is_slot_owned_by_email(index, viewer_email):
            return False

        viewer_g = self._get_slot_group(viewer_index)
        target_g = self._get_slot_group(index)
        if viewer_g > 0:
            return target_g != viewer_g
        elif target_g > 0:
            return True
        account = self.AccountData[index]
        if account.IsAccount:
            return bool(account.IsIsolated)
        owner_email = account.AccountEmail
        if not owner_email:
            return False
        owner_index = self._find_account_slot_by_email(owner_email)
        if owner_index == -1:
            return False
        return bool(self.AccountData[owner_index].IsAccount and self.AccountData[owner_index].IsIsolated)

    def _find_account_slot_by_email(self, account_email: str) -> int:
        if not account_email:
            return -1
        all_accounts = self.AccountData
        for i in range(SHMEM_MAX_PLAYERS):
            account = all_accounts[i]
            if account.AccountEmail == account_email and account.IsAccount:
                return i
        return -1

    def _find_player_slot_by_key(self, account_email: str, hwnd: int) -> int:
        if not account_email or not hwnd:
            return -1
        for i in range(SHMEM_MAX_PLAYERS):
            account = self.AccountData[i]
            if not account.IsAccount:
                continue
            if account.AccountEmail != account_email:
                continue
            key = self.Keys[i]
            if key.HWND == hwnd and key.EntityType == 0:
                return i
        return -1

    def _find_slot_by_key(self, hwnd: int, entity_type: int, local_index: int) -> int:
        if not hwnd:
            return -1
        for i in range(SHMEM_MAX_PLAYERS):
            key = self.Keys[i]
            if key.HWND == hwnd and key.EntityType == entity_type and key.LocalIndex == local_index:
                return i
        return -1

    def IsAccountIsolated(self, account_email: str) -> bool:
        index = self._find_account_slot_by_email(account_email)
        if index == -1:
            return False
        return bool(self.AccountData[index].IsIsolated)

    def SetAccountIsolationByEmail(self, account_email: str, isolated: bool) -> bool:
        if not account_email:
            return False
        index = self.GetSlotByEmail(account_email)
        if index == -1:
            return False
        account = self.AccountData[index]
        if not account.IsAccount:
            return False
        account.IsIsolated = isolated
        return True

    def SetAccountIsolatedByEmail(self, account_email: str) -> bool:
        return self.SetAccountIsolationByEmail(account_email, True)

    def RemoveAccountIsolationByEmail(self, account_email: str) -> bool:
        return self.SetAccountIsolationByEmail(account_email, False)

    def SetAccountGroupByEmail(self, account_email: str, group_id: int) -> bool:
        if not account_email:
            return False
        index = self._find_account_slot_by_email(account_email)
        if index == -1:
            return False
        account = self.AccountData[index]
        if not account.IsAccount:
            return False
        account.IsolationGroupID = group_id
        return True

    def GetAccountGroupByEmail(self, account_email: str) -> int:
        index = self._find_account_slot_by_email(account_email)
        if index == -1:
            return 0
        return int(self.AccountData[index].IsolationGroupID)

    def _can_communicate(self, sender_email: str, receiver_email: str) -> bool:
        """Group-aware communication check between two accounts."""
        s_idx = self._find_account_slot_by_email(sender_email)
        r_idx = self._find_account_slot_by_email(receiver_email)
        if s_idx == -1 or r_idx == -1:
            return False
        if sender_email == receiver_email:
            return True

        # Party members are always allowed to exchange coordination messages,
        # even when one side is grouped/isolated differently.
        try:
            s_party = int(getattr(self.AccountData[s_idx].AgentPartyData, "PartyID", 0) or 0)
            r_party = int(getattr(self.AccountData[r_idx].AgentPartyData, "PartyID", 0) or 0)
            if s_party > 0 and s_party == r_party:
                return True
        except Exception:
            pass

        s_g = int(self.AccountData[s_idx].IsolationGroupID)
        r_g = int(self.AccountData[r_idx].IsolationGroupID)
        if s_g > 0 and r_g > 0:
            return s_g == r_g
        if s_g > 0 or r_g > 0:
            return False  # one grouped, one not
        # both ungrouped: legacy
        return not self.AccountData[s_idx].IsIsolated and not self.AccountData[r_idx].IsIsolated

    def _is_slot_expired(self, index: int) -> bool:
        slot_data = self.AccountData[index]
        if not slot_data.IsSlotActive:
            return False
        return (Py4GW.Game.get_tick_count64() - slot_data.LastUpdated) >= SHMEM_SUBSCRIBE_TIMEOUT_MILLISECONDS

    def GetEmptySlot(self, allow_expired_reclaim: bool = True) -> int:
        """Find the first empty or safely reclaimable slot in shared memory."""
        for i, account in enumerate(self.AccountData):
            if not account.IsSlotActive:
                return i    

        if not allow_expired_reclaim:
            return -1

        for i, account in enumerate(self.AccountData):
            if not self._is_slot_expired(i):
                continue
            return i
        return -1
    
    def GetExpiredSlots(self) -> list[int]:
        expired_slots = []
        for i, account in enumerate(self.AccountData):
            slot_data = self.AccountData[i]
            slot_active = slot_data.IsSlotActive 
            last_updated = slot_data.LastUpdated
            base_timestamp = Py4GW.Game.get_tick_count64()
            if slot_active and (base_timestamp - last_updated) >= SHMEM_SUBSCRIBE_TIMEOUT_MILLISECONDS:
                expired_slots.append(i)
                
        return expired_slots
    
    def GetPlayerExpiredSlot(self, account_email: str) -> int:
        """Find the slot index for the given account email that has expired."""
        expired_slots = self.GetExpiredSlots()
        for index in expired_slots:
            if self.AccountData[index].AccountEmail == account_email:
                return index
        return -1
    
    def GetHeroExpiredSlot(self, hero_data: HeroPartyMember) -> int:
        """Find the slot index for the given hero data that has expired."""
        from ...Party import Party
        from ...Player import Player
        owner_email = Player.GetAccountEmail()
        owner_id = Party.Players.GetAgentIDByLoginNumber(hero_data.owner_player_id)
        expired_slots = self.GetExpiredSlots()
        for index in expired_slots:
            account_data = self.AccountData[index]
            if (account_data.IsHero and 
                account_data.AgentData.HeroID == hero_data.hero_id.GetID() and
                (
                    account_data.AccountEmail == owner_email or
                    account_data.AgentData.OwnerAgentID == owner_id
                )):
                return index
        return -1
    
    def GetPetExpiredSlot(self, pet_data: PetInfo) -> int:
        """Find the slot index for the given pet data that has expired."""
        from ...Player import Player
        owner_email = Player.GetAccountEmail()
        expired_slots = self.GetExpiredSlots()
        for index in expired_slots:
            account_data = self.AccountData[index]
            if (account_data.IsPet and (
                account_data.AccountEmail == owner_email or
                (
                    account_data.AgentData.AgentID == pet_data.agent_id and
                    account_data.AgentData.OwnerAgentID == pet_data.owner_agent_id
                )
            )):
                return index
        return -1
    
    def SubmitAccountData(self, account_email: str) -> int:
        """Submit account data to shared memory. Returns the slot index or -1 on failure."""
        if not account_email:
            ConsoleLog(SHMEM_MODULE_NAME, "Account email is empty.", Py4GW.Console.MessageType.Error)
            return -1
        
        slot_index = self.GetPlayerExpiredSlot(account_email)
        if slot_index == -1:
            slot_index = self.GetEmptySlot(allow_expired_reclaim=True)
        if slot_index == -1:
            ConsoleLog(SHMEM_MODULE_NAME, "No empty slot available to submit account data.", Py4GW.Console.MessageType.Error)
            return -1
        
        new_account = AccountStruct()
        new_account.from_context(account_email, slot_index)
        
        Key = KeyStruct().AsPlayerKey(Py4GW.Console.get_gw_window_handle())
        self.Keys[slot_index] = new_account.Key = Key
        self.AccountData[slot_index] = new_account
        

        
        ConsoleLog(SHMEM_MODULE_NAME, f"Submitted account data for {account_email} at slot {slot_index}.", Py4GW.Console.MessageType.Info)
        return slot_index
    
    def SubmitHeroData(self, hero_data: HeroPartyMember) -> int:
        """Submit hero data to shared memory. Returns the slot index or -1 on failure."""
        from ...Party import Party
        owner_id = Party.Players.GetAgentIDByLoginNumber(hero_data.owner_player_id)
        retry_key = (int(hero_data.hero_id.GetID()), int(owner_id))
        now = Py4GW.Game.get_tick_count64()
        if now < _HERO_SUBMIT_RETRY_AFTER.get(retry_key, 0):
            return -1

        slot_index = self.GetHeroExpiredSlot(hero_data)
        if slot_index == -1:
            slot_index = self.GetEmptySlot(allow_expired_reclaim=False)
        if slot_index == -1:
            _HERO_SUBMIT_RETRY_AFTER[retry_key] = now + _SLOT_SUBMIT_RETRY_COOLDOWN_MS
            return -1
        _HERO_SUBMIT_RETRY_AFTER.pop(retry_key, None)
        
        new_account = AccountStruct()
        new_account.from_hero_context(hero_data, slot_index)
        
        Key = KeyStruct().AsHeroKey(Py4GW.Console.get_gw_window_handle(), int(hero_data.hero_id.GetID()))
        self.Keys[slot_index] = new_account.Key = Key
        self.AccountData[slot_index] = new_account

        ConsoleLog(SHMEM_MODULE_NAME, f"Submitted hero data for HeroID {hero_data.hero_id.GetID()} at slot {slot_index}.", Py4GW.Console.MessageType.Debug, log=False)
        return slot_index
    
    def SubmitPetData(self, pet_data: PetInfo) -> int:
        """Submit pet data to shared memory. Returns the slot index or -1 on failure."""
        retry_key = (int(pet_data.agent_id), int(pet_data.owner_agent_id))
        now = Py4GW.Game.get_tick_count64()
        if now < _PET_SUBMIT_RETRY_AFTER.get(retry_key, 0):
            return -1

        slot_index = self.GetPetExpiredSlot(pet_data)
        if slot_index == -1:
            slot_index = self.GetEmptySlot(allow_expired_reclaim=False)
        if slot_index == -1:
            _PET_SUBMIT_RETRY_AFTER[retry_key] = now + _SLOT_SUBMIT_RETRY_COOLDOWN_MS
            return -1
        _PET_SUBMIT_RETRY_AFTER.pop(retry_key, None)
        
        new_account = AccountStruct()
        new_account.from_pet_context(pet_data, slot_index)
        
        Key = KeyStruct().AsPetKey(Py4GW.Console.get_gw_window_handle(), 0)
        self.Keys[slot_index] = new_account.Key = Key
        self.AccountData[slot_index] = new_account
        
        ConsoleLog(SHMEM_MODULE_NAME, f"Submitted pet data for AgentID {pet_data.agent_id} at slot {slot_index}.", Py4GW.Console.MessageType.Info)
        return slot_index
    
    def SetPlayerData(self, account_email: str):
        """Set player data for the account with the given email."""  
        if not account_email:
            return    
        index = self._find_account_slot_by_email(account_email)
        if index == -1:
            self.SubmitAccountData(account_email)
            return
        
        self.AccountData[index].from_context(account_email, index)
        
    def SetHeroesData(self):
        """Set data for all heroes in the given list."""
        from ...Player import Player
        from ...Party import Party
        owner_id = Player.GetAgentID()
        for hero_data in Party.GetHeroes():
            agent_from_login = Party.Players.GetAgentIDByLoginNumber(hero_data.owner_player_id)
            if agent_from_login != owner_id:
                continue
            self.SetHeroData(hero_data)
            
    def SetHeroData(self,hero_data:HeroPartyMember):
        """Set player data for the account with the given email."""     
        index = self.GetHeroSlotByHeroData(hero_data)
        if index == -1:
            return
        
        account = self.AccountData[index]
        account.from_hero_context(hero_data, index)
        if account.AgentData.AgentID == 0:
            return
        
    def SetPetData(self):
        """Set pet data for the account with the given email."""
        from ...Player import Player
        from ...Party import Party
        from ...Agent import Agent
        
        owner_agent_id = Player.GetAgentID()
        pet_info = Party.Pets.GetPetInfo(owner_agent_id)
        if not pet_info or not Agent.IsValid(pet_info.agent_id):
            return
        
        index = self.GetPetSlotByPetData(pet_info)
        if index == -1:
            return
        
        account = self.AccountData[index]
        account.from_pet_context(pet_info, index)
        if account.AgentData.AgentID == 0:
            return

    
    def GetSlotByEmail(self, account_email: str) -> int:
        if not account_email:
            return -1
        
        """Find the index of the account with the given email."""
        hwnd = Py4GW.Console.get_gw_window_handle()
        own_index = self._find_player_slot_by_key(account_email, hwnd)
        if own_index != -1:
            return own_index

        all_accounts = self.AccountData
        for i in range(SHMEM_MAX_PLAYERS):
            account = all_accounts[i]
            if account.AccountEmail == account_email and account.IsAccount and self._is_slot_active(i):
                return i
            
        #submit if not found
        return self.SubmitAccountData(account_email)

    def GetVisibleSlotByEmail(self, account_email: str) -> int:
        index = self._find_account_slot_by_email(account_email)
        if index == -1:
            return -1
        if not self._is_visible_account(index):
            return -1
        return index

    def GetAccountDataFromEmail(self, account_email: str) -> AccountStruct | None:
        """Get the account data for the given email, or None if not found."""
        index = self._find_account_slot_by_email(account_email)
        if index != -1 and self._is_visible_account(index):
            return self.AccountData[index]
        return None
    
    def GetAccountDataFromPartyNumber(self, party_number: int, log : bool = False) -> AccountStruct | None:
        """Get player data for the account with the given party number."""
        all_accounts = self.AccountData
        for i in range(SHMEM_MAX_PLAYERS):
            player = all_accounts[i]
            if self._is_visible_account(i) and player.AgentPartyData.PartyPosition == party_number:
                return player
            
        return None
    
    def GetHeroSlotByHeroData(self, hero_data:HeroPartyMember) -> int:
        """Find the index of the hero with the given ID."""
        from ...Party import Party
        from ...Player import Player
        all_accounts = self.AccountData
        hero_id = hero_data.hero_id.GetID()
        key_slot = self._find_slot_by_key(Py4GW.Console.get_gw_window_handle(), 1, int(hero_id))
        if key_slot != -1:
            return key_slot
        owner_agent_id = Party.Players.GetAgentIDByLoginNumber(hero_data.owner_player_id)
        owner_email = Player.GetAccountEmail()
        for i in range(SHMEM_MAX_PLAYERS):
            player = all_accounts[i]
            if not player.IsHero:
                continue
            if player.AgentData.HeroID != hero_id:
                continue
            if player.AccountEmail == owner_email:
                return i
            # Only enforce owner match when both sides have a known (non-zero) value.
            # If either is 0 (not yet resolved), trust HeroID alone.
            if (owner_agent_id != 0 and player.AgentData.OwnerAgentID != 0 and
                    player.AgentData.OwnerAgentID != owner_agent_id):
                continue
            return i

        #submit if not found
        return self.SubmitHeroData(hero_data)

    
    def GetPetSlotByPetData(self, pet_data:PetInfo) -> int:
        """Find the index of the pet with the given ID."""
        from ...Player import Player
        owner_email = Player.GetAccountEmail()
        key_slot = self._find_slot_by_key(Py4GW.Console.get_gw_window_handle(), 2, 0)
        if key_slot != -1:
            return key_slot
        all_accounts = self.AccountData
        for i in range(SHMEM_MAX_PLAYERS):
            player = all_accounts[i]
  
            if not player.IsPet:
                continue
            if player.AccountEmail == owner_email:
                return i
            if (
                player.AgentData.AgentID == pet_data.agent_id and
                player.AgentData.OwnerAgentID == pet_data.owner_agent_id
            ):
                return i
        return self.SubmitPetData(pet_data)
    
    def GetAllActivePlayers(self, sort_results: bool = True, include_isolated: bool = False) -> list[AccountStruct]:
        """Get all active account players in shared memory."""
        players : list[AccountStruct] = []
        all_accounts = self.AccountData
        for i in range(SHMEM_MAX_PLAYERS):
            account = all_accounts[i]
            if include_isolated:
                if self._is_slot_active(i) and account.IsAccount:
                    players.append(account)
            elif self._is_visible_account(i):
                players.append(account)

        if sort_results and len(players) > 1:
            players.sort(key=lambda p: (
                p.AgentData.Map.MapID,
                p.AgentData.Map.Region,
                p.AgentData.Map.District,
                p.AgentData.Map.Language,
                p.AgentPartyData.PartyID,
                p.AgentPartyData.PartyPosition,
                p.AgentData.LoginNumber,
                p.AgentData.CharacterName
            ))
             
        return players
    
    def GetNumActivePlayers(self) -> int:
        """Get the number of active players in shared memory."""
        return len(self.GetAllActivePlayers())
    
    def GetNumActiveSlots(self) -> int:
        """Get the number of active slots in shared memory."""
        count = 0
        for i in range(SHMEM_MAX_PLAYERS):
            if self._is_visible_slot(i):
                count += 1
        return count
    
    def GetHeroesFromPlayers(self, owner_agent_id: int) -> list[AccountStruct]:
        """Get a list of heroes owned by the specified player."""
        heroes : list[AccountStruct] = []
        all_accounts = self.AccountData
        for i in range(SHMEM_MAX_PLAYERS):   
            account_data = all_accounts[i]

            if (self._is_visible_slot(i) and account_data.IsHero and
                account_data.AgentData.OwnerAgentID == owner_agent_id):
                heroes.append(account_data)
        return heroes
    
    
    def GetNumHeroesFromPlayers(self, owner_agent_id: int) -> int:
        """Get the number of heroes owned by the specified player."""
        return len(self.GetHeroesFromPlayers(owner_agent_id))
    
            
    def GetPetsFromPlayers(self, owner_agent_id: int) -> list[AccountStruct]:
        """Get a list of pets owned by the specified player."""
        pets : list[AccountStruct] = []
        all_accounts = self.AccountData
        for i in range(SHMEM_MAX_PLAYERS):   
            account_data = all_accounts[i]

            if (self._is_visible_slot(i) and account_data.IsPet and
                account_data.AgentData.OwnerAgentID == owner_agent_id):
                pets.append(account_data)
        return pets
    
    def GetNumPetsFromPlayers(self, owner_agent_id: int) -> int:
        """Get the number of pets owned by the specified player."""
        return len(self.GetPetsFromPlayers(owner_agent_id))
    
    def GetAllActiveSlotsData(self) -> list[AccountStruct]:
        """Get all active slot data, ordered by PartyID, PartyPosition, PlayerLoginNumber, CharacterName."""
        accs : list[AccountStruct] = []
        for i in range(SHMEM_MAX_PLAYERS):
            acc = self.AccountData[i]
            if self._is_visible_slot(i):
                accs.append(acc)

        # Sort by PartyID, then PartyPosition, then PlayerLoginNumber, then CharacterName
        accs.sort(key=lambda p: (
            p.AgentData.Map.MapID,
            p.AgentData.Map.Region,
            p.AgentData.Map.District,
            p.AgentData.Map.Language,
            p.AgentPartyData.PartyID,
            p.AgentPartyData.PartyPosition,
            p.AgentData.LoginNumber,
            p.AgentData.CharacterName
        ))

        return accs
    
    def AccountHasEffect(self, account_email: str, effect_id: int) -> bool:
        """Check if the account with the given email has the specified effect."""
        if effect_id == 0: return False

        player = self.GetAccountDataFromEmail(account_email)
        if player:
            for buff in player.AgentData.Buffs.Buffs:
                if buff.SkillId == effect_id:
                    return True
        return False

    #region HeroAI
    def GetAllAccountHeroAIOptions(self) -> list[HeroAIOptionStruct]:
        """Get HeroAI options for all accounts."""
        options = []
        for i in range(SHMEM_MAX_PLAYERS):
            player = self.AccountData[i]
            if self._is_visible_account(i):
                options.append(self.HeroAIOptions[i])
        return options

    def GetAllActiveAccountHeroAIPairs(self, sort_results: bool = True) -> list[tuple[AccountStruct, HeroAIOptionStruct]]:
        """Get active account players and their HeroAI options in a single pass."""
        pairs: list[tuple[AccountStruct, HeroAIOptionStruct]] = []
        all_accounts = self.AccountData
        all_options = self.HeroAIOptions

        for i in range(SHMEM_MAX_PLAYERS):
            account = all_accounts[i]
            if self._is_visible_account(i):
                pairs.append((account, all_options[i]))

        if sort_results and len(pairs) > 1:
            pairs.sort(key=lambda item: (
                item[0].AgentData.Map.MapID,
                item[0].AgentData.Map.Region,
                item[0].AgentData.Map.District,
                item[0].AgentData.Map.Language,
                item[0].AgentPartyData.PartyID,
                item[0].AgentPartyData.PartyPosition,
                item[0].AgentData.LoginNumber,
                item[0].AgentData.CharacterName
            ))

        return pairs
    
    def GetHeroAIOptionsFromEmail(self, account_email: str) -> HeroAIOptionStruct | None:
        """Get HeroAI options for the account with the given email."""
        if not account_email:
            return None
        index = self._find_account_slot_by_email(account_email)
        if index != -1 and self._is_visible_account(index):
            return self.HeroAIOptions[index]
        else:
            ConsoleLog(SHMEM_MODULE_NAME, f"Account {account_email} not found.", Py4GW.Console.MessageType.Error, log = False)
            return None

    def GetHeroAIOptionsByPartyNumber(self, party_number: int) -> HeroAIOptionStruct | None:
        """Get HeroAI options for the account with the given party number."""
        for i in range(SHMEM_MAX_PLAYERS):
            player = self.AccountData[i]
            if self._is_visible_account(i) and player.AgentPartyData.PartyPosition == party_number:
                return self.HeroAIOptions[i]
        return None 
    
    def SetHeroAIOptionsByEmail(self, account_email: str, options: HeroAIOptionStruct):
        """Set HeroAI options for the account with the given email."""
        if not account_email:
            return
        index = self._find_account_slot_by_email(account_email)
        if index != -1 and self._is_visible_account(index):
            self.HeroAIOptions[index] = options
        else:
            ConsoleLog(SHMEM_MODULE_NAME, f"Account {account_email} not found.", Py4GW.Console.MessageType.Error, log = False)

    def SetHeroAIPropertyByEmail(self, account_email: str, property_name: str, value):
        """Set a specific HeroAI property for the account with the given email."""
        if not account_email:
            return
        index = self._find_account_slot_by_email(account_email)
        if index != -1 and self._is_visible_account(index):
            options = self.HeroAIOptions[index]

            if property_name.startswith("Skill_"):
                skill_index = int(property_name.split("_")[1])
                if 0 <= skill_index < SHMEM_MAX_NUMBER_OF_SKILLS:
                    options.Skills[skill_index] = value
                else:
                    ConsoleLog(SHMEM_MODULE_NAME, f"Invalid skill index: {skill_index}.", Py4GW.Console.MessageType.Error)
                return
            
            if hasattr(options, property_name):
                setattr(options, property_name, value)
            else:
                ConsoleLog(SHMEM_MODULE_NAME, f"Property {property_name} does not exist in HeroAIOptions.", Py4GW.Console.MessageType.Error)
        else:
            ConsoleLog(SHMEM_MODULE_NAME, f"Account {account_email} not found.", Py4GW.Console.MessageType.Error, log = False)
    
    def GetMapsFromPlayers(self):
        """Get a list of unique maps from all active players."""
        maps = set()
        for i in range(SHMEM_MAX_PLAYERS):
            player = self.AccountData[i]
            if self._is_visible_account(i):
                maps.add((player.AgentData.Map.MapID, player.AgentData.Map.Region, player.AgentData.Map.District, player.AgentData.Map.Language))
        return list(maps)
    
    def GetPartiesFromMaps(self, map_id: int, map_region: int, map_district: int, map_language: int):
        """
        Get a list of unique PartyIDs for players in the specified map/region/district.
        """
        parties = set()
        for i in range(SHMEM_MAX_PLAYERS):
            player = self.AccountData[i]
            if (self._is_visible_account(i) and
                player.AgentData.Map.MapID == map_id and
                player.AgentData.Map.Region == map_region and
                player.AgentData.Map.District == map_district and
                player.AgentData.Map.Language == map_language):
                parties.add(player.AgentPartyData.PartyID)
        return list(parties)
    
    def GetPlayersFromParty(self, party_id: int, map_id: int, map_region: int, map_district: int, map_language: int):
        """Get a list of players in a specific party on a specific map."""
        players = []
        all_accounts = self.AccountData
        for i in range(SHMEM_MAX_PLAYERS):
            account_data = all_accounts[i]
            if (self._is_visible_account(i) and
                account_data.AgentData.Map.MapID == map_id and
                account_data.AgentData.Map.Region == map_region and
                account_data.AgentData.Map.District == map_district and
                account_data.AgentData.Map.Language == map_language and
                account_data.AgentPartyData.PartyID == party_id):
                players.append(account_data)
        return players
    
    
    #region Messaging
    def _str_to_c_wchar_array(self,value: str, maxlen: int) -> ctypes.Array:
        import ctypes as ct
        """Convert Python string to c_wchar array with maxlen (including terminator)."""
        arr = (ct.c_wchar * maxlen)()
        if value:
            s = value[:maxlen - 1]  # leave room for terminator
            for i, ch in enumerate(s):
                arr[i] = ch
            arr[len(s)] = '\0'
        return arr
    
    def _c_wchar_array_to_str(self,arr: ctypes.Array) -> str:
        """Convert c_wchar array back to Python str, stopping at null terminator."""
        return "".join(ch for ch in arr if ch != '\0').rstrip()
    
    def _pack_extra_data_for_sendmessage(self, extra_tuple, maxlen=128):
        out = []
        for i in range(4):
            val = extra_tuple[i] if i < len(extra_tuple) else ""
            out.append(self._str_to_c_wchar_array(str(val), maxlen))
        return tuple(out)
    
    def GetAllMessages(self) -> list[tuple[int, SharedMessageStruct]]:
        """Get all messages in shared memory with their index."""
        messages = []
        for index in range(SHMEM_MAX_PLAYERS):
            message = self.Inbox[index]
            if message.Active and self._can_communicate(message.SenderEmail, message.ReceiverEmail):
                messages.append((index, message))  # Add index and message
        return messages
    
    def GetInbox(self, index: int) -> SharedMessageStruct:
        if index < 0 or index >= SHMEM_MAX_PLAYERS:
            raise IndexError(f"Index {index} is out of bounds for max players {SHMEM_MAX_PLAYERS}.")
        return self.Inbox[index]
    
    def SendMessage(self, sender_email: str, receiver_email: str, command: SharedCommandType, params: tuple = (0.0, 0.0, 0.0, 0.0), ExtraData: tuple = ()) -> int:
        """Send a message to another player. Returns the message index or -1 on failure."""
        
        import ctypes as ct
        index = self.GetSlotByEmail(receiver_email)
        
        normalized_params = tuple(float(params[i]) if i < len(params) else 0.0 for i in range(4))
        normalized_extra_data = tuple(str(ExtraData[i]) if i < len(ExtraData) else "" for i in range(4))
        
        if index == -1:
            ConsoleLog(SHMEM_MODULE_NAME, f"Receiver account {receiver_email} not found.", Py4GW.Console.MessageType.Error)
            return -1
        
        if not receiver_email:
            ConsoleLog(SHMEM_MODULE_NAME, "Receiver email is empty.", Py4GW.Console.MessageType.Error)
            return -1

        if not sender_email:
            ConsoleLog(SHMEM_MODULE_NAME, "Sender email is empty.", Py4GW.Console.MessageType.Error)
            return -1

        if not self._can_communicate(sender_email, receiver_email):
            ConsoleLog(SHMEM_MODULE_NAME, f"Cannot communicate between {sender_email} and {receiver_email} (isolated or different groups).", Py4GW.Console.MessageType.Warning)
            return -1
        
        for i in range(SHMEM_MAX_PLAYERS):
            message = self.GetInbox(i)
            if not message.Active:
                continue

            if message.ReceiverEmail != receiver_email:
                continue  # This slot is not for the intended receiver
            
            if int(message.Command) != int(command.value):
                continue  # This slot has a different command (could be from another sender)
            
            message_Params = tuple(float(message.Params[j]) for j in range(4))
            
            if message_Params != normalized_params:
                continue  # This slot has different params (could be from another sender or an old message)
            
            message_extra_data = tuple(self._c_wchar_array_to_str(message.ExtraData[j]) for j in range(4))
            
            if message_extra_data != normalized_extra_data:
                continue  # This slot has different extra data (could be from another sender or an old message)
            
            return i  # Matching active message is already queued/running; reuse it instead of duplicating it.
        
        for i in range(SHMEM_MAX_PLAYERS):
            message = self.GetInbox(i)
            if message.Active:
                continue
         
            message.SenderEmail = sender_email
            message.ReceiverEmail = receiver_email
            message.Command = command.value
            message.Params = (ct.c_float * 4)(*normalized_params)
            
            # Pack 4 strings into 4 arrays of c_wchar[SHMEM_MAX_CHAR_LEN]
            arr_type = ct.c_wchar * SHMEM_MAX_CHAR_LEN
            packed = [self._str_to_c_wchar_array(
                        normalized_extra_data[j],
                        SHMEM_MAX_CHAR_LEN)
                    for j in range(4)]
            message.ExtraData = (arr_type * 4)(*packed)
            message.Active = True
            message.Running = False
            message.Timestamp = Py4GW.Game.get_tick_count64()
            return i

        return -1
    
    def GetNextMessage(self, account_email: str) -> tuple[int, SharedMessageStruct | None]:
        """Read the next message for the given account.
        Returns the raw SharedMessage. Use self._c_wchar_array_to_str() to read ExtraData safely.
        """
        for index in range(SHMEM_MAX_PLAYERS):
            message = self.Inbox[index]
            if (message.ReceiverEmail == account_email and message.Active and not message.Running
                and self._can_communicate(message.SenderEmail, account_email)):
                return index, message
        return -1, None

    def PreviewNextMessage(self, account_email: str, include_running: bool = True) -> tuple[int, SharedMessageStruct | None]:
        """Preview the next message for the given account.
        If include_running is True, will also return a running message.
        Ensures ExtraData is returned as tuple[str] using existing helpers.
        """
        for index in range(SHMEM_MAX_PLAYERS):
            message = self.Inbox[index]
            if message.ReceiverEmail != account_email or not message.Active:
                continue
            if not self._can_communicate(message.SenderEmail, account_email):
                continue
            if not message.Running or include_running:
                return index, message
        return -1, None
    
    def MarkMessageAsRunning(self, account_email: str, message_index: int):
        """Mark a specific message as running."""
        if 0 <= message_index < SHMEM_MAX_PLAYERS:
            message = self.Inbox[message_index]
            if message.ReceiverEmail == account_email:
                message.Running = True
                message.Active = True
                message.Timestamp = Py4GW.Game.get_tick_count64()
            else:
                ConsoleLog(SHMEM_MODULE_NAME, f"Message at index {message_index} does not belong to {account_email}.", Py4GW.Console.MessageType.Error)
        else:
            ConsoleLog(SHMEM_MODULE_NAME, f"Invalid message index: {message_index}.", Py4GW.Console.MessageType.Error)
            
    def MarkMessageAsFinished(self, account_email: str, message_index: int):
        """Mark a specific message as finished."""
        import ctypes as ct
        if 0 <= message_index < SHMEM_MAX_PLAYERS:
            message = self.Inbox[message_index]
            if message.ReceiverEmail == account_email:
                message.SenderEmail = ""
                message.ReceiverEmail = ""
                message.Command = SharedCommandType.NoCommand
                message.Params = (c_float * 4)(0.0, 0.0, 0.0, 0.0)

                # Reset ExtraData to 4 empty wide-char arrays
                arr_type = ct.c_wchar * SHMEM_MAX_CHAR_LEN
                empty = [self._str_to_c_wchar_array("", SHMEM_MAX_CHAR_LEN) for _ in range(4)]
                message.ExtraData = (arr_type * 4)(*empty)

                message.Timestamp = Py4GW.Game.get_tick_count64()
                message.Running = False
                message.Active = False
            else:
                ConsoleLog(
                    SHMEM_MODULE_NAME,
                    f"Message at index {message_index} does not belong to {account_email}.",
                    Py4GW.Console.MessageType.Error
                )
        else:
            ConsoleLog(
                SHMEM_MODULE_NAME,
                f"Invalid message index: {message_index}.",
                Py4GW.Console.MessageType.Error
            )

    #region Whiteboard (cross-hero cast-intent)

    def _wb_log(self, kind_id: int, msg: str) -> None:
        """Gated debug log for whiteboard state transitions.

        Two-stage gate:
          1. ``WHITEBOARD_DEBUG`` master toggle — False silences everything.
          2. ``WHITEBOARD_DEBUG_KINDS[kind_id]`` per-kind override — present
             + False silences this kind even when the master is True.

        Missing key in WHITEBOARD_DEBUG_KINDS = use master toggle.
        """
        if not WHITEBOARD_DEBUG:
            return
        if not WHITEBOARD_DEBUG_KINDS.get(int(kind_id), True):
            return
        ConsoleLog("Whiteboard", msg, Py4GW.Console.MessageType.Info)

    def _wb_kind_display(self, kind_id: int) -> str:
        try:
            return WhiteboardLockKind(int(kind_id)).name
        except Exception:
            return f"kind={int(kind_id)}"

    def _wb_mode_display(self, mode: int) -> str:
        try:
            return WhiteboardLockMode(int(mode)).name
        except Exception:
            return f"mode={int(mode)}"

    def _wb_key_display(self, kind_id: int, key_id: int) -> str:
        if int(kind_id) != int(WhiteboardLockKind.SKILL_TARGET):
            return f"key={int(key_id)}"
        try:
            from Py4GWCoreLib import GLOBAL_CACHE
            name = GLOBAL_CACHE.Skill.GetName(int(key_id)) or ""
            name = str(name).strip()
            if name:
                return f"'{name}'(id={int(key_id)})"
        except Exception:
            pass
        return f"skill={int(key_id)}"

    def _wb_lock_display(self, intent: IntentStruct) -> str:
        return (
            f"kind={self._wb_kind_display(intent.KindID)} "
            f"mode={self._wb_mode_display(intent.LockMode)} "
            f"{self._wb_key_display(intent.KindID, intent.SkillID)} "
            f"target={int(intent.TargetAgentID)} "
            f"group={int(intent.IsolationGroupID)}"
        )

    def GetAllIntents(self) -> list[tuple[int, IntentStruct]]:
        """Return (index, IntentStruct) pairs for every active slot."""
        out: list[tuple[int, IntentStruct]] = []
        for i in range(SHMEM_MAX_INTENTS):
            intent = self.Intents[i]
            if intent.Active:
                out.append((i, intent))
        return out

    def ClearIntent(self, index: int) -> None:
        """Zero a single intent slot."""
        if not (0 <= index < SHMEM_MAX_INTENTS):
            return
        intent = self.Intents[index]
        if intent.Active:
            lifetime = int(Py4GW.Game.get_tick_count64()) - int(intent.PostedAtTick)
            self._wb_log(
                int(intent.KindID),
                f"CLEAR slot={index} email='{intent.OwnerEmail}' "
                f"{self._wb_lock_display(intent)} lifetime={lifetime}ms reason=explicit",
            )
        intent.reset()

    def ClearIntentsByOwner(self, owner_email: str) -> int:
        """Zero every whiteboard slot whose OwnerEmail matches. Returns count cleared."""
        if not owner_email:
            return 0
        count = 0
        now = int(Py4GW.Game.get_tick_count64())
        for i in range(SHMEM_MAX_INTENTS):
            intent = self.Intents[i]
            if intent.Active and intent.OwnerEmail == owner_email:
                lifetime = now - int(intent.PostedAtTick)
                self._wb_log(
                    int(intent.KindID),
                    f"CLEAR slot={i} email='{owner_email}' "
                    f"{self._wb_lock_display(intent)} lifetime={lifetime}ms reason=owner_clear",
                )
                intent.reset()
                count += 1
        return count

    def ClearLockByOwnerKindTarget(
        self,
        owner_email: str,
        kind_id: int,
        target_id: int,
        group_id: int,
    ) -> int:
        """Zero active locks matching (owner, kind, target, group). Returns count cleared.

        Used by hex-removal helpers to release a target lock immediately after
        confirming the hex came off, so another client can step in for the next
        dangerous hex on the same teammate.
        """
        if not owner_email:
            return 0
        count = 0
        now = int(Py4GW.Game.get_tick_count64())
        for i in range(SHMEM_MAX_INTENTS):
            intent = self.Intents[i]
            if not intent.Active:
                continue
            if intent.OwnerEmail != owner_email:
                continue
            if int(intent.KindID) != int(kind_id):
                continue
            if int(intent.TargetAgentID) != int(target_id):
                continue
            if int(intent.IsolationGroupID) != int(group_id):
                continue
            lifetime = now - int(intent.PostedAtTick)
            self._wb_log(
                int(intent.KindID),
                f"CLEAR slot={i} email='{owner_email}' "
                f"{self._wb_lock_display(intent)} lifetime={lifetime}ms reason=owner_clear",
            )
            intent.reset()
            count += 1
        return count

    def PostLock(
        self,
        owner_email: str,
        kind_id: int,
        key_id: int,
        target_id: int,
        expires_at_tick: int,
        isolation_group_id: int | None = None,
        lock_mode: int = int(WhiteboardLockMode.EXCLUSIVE),
        max_holders: int = 1,
        reentry_policy: int = int(WhiteboardReentryPolicy.OWNER_REENTRANT),
        claim_strength: int = int(WhiteboardClaimStrength.HARD),
    ) -> int:
        """Claim a generic whiteboard slot. Returns slot index or -1 if full.

        Every lock is a lease. Past or missing expiry is rejected so no caller
        can create a permanent lock.
        """
        now = int(Py4GW.Game.get_tick_count64())
        if not owner_email or kind_id <= 0 or target_id < 0:
            return -1
        if int(expires_at_tick) <= now:
            return -1
        if int(max_holders) <= 0:
            max_holders = 1
        if isolation_group_id is None:
            owner_slot = self._find_account_slot_by_email(owner_email)
            if owner_slot == -1:
                isolation_group_id = 0
            else:
                isolation_group_id = int(self.AccountData[owner_slot].IsolationGroupID)
        for i in range(SHMEM_MAX_INTENTS):
            intent = self.Intents[i]
            if intent.Active:
                continue
            intent.OwnerEmail = owner_email
            intent.KindID = int(kind_id)
            intent.LockMode = int(lock_mode)
            intent.ReentryPolicy = int(reentry_policy)
            intent.ClaimStrength = int(claim_strength)
            intent.MaxHolders = int(max_holders)
            intent.SkillID = int(key_id)
            intent.TargetAgentID = int(target_id)
            intent.IsolationGroupID = int(isolation_group_id)
            intent.PostedAtTick = now
            intent.ExpiresAtTick = int(expires_at_tick)
            intent.Active = True
            budget = int(expires_at_tick) - now
            self._wb_log(
                int(intent.KindID),
                f"POST  slot={i} email='{owner_email}' "
                f"{self._wb_lock_display(intent)} holders={int(max_holders)} "
                f"expires_in={budget}ms",
            )
            return i
        self._wb_log(
            int(kind_id),
            f"POST-FAIL email='{owner_email}' kind={self._wb_kind_display(kind_id)} "
            f"key={int(key_id)} target={int(target_id)} reason=full"
        )
        return -1

    def CountLocks(
        self,
        kind_id: int,
        key_id: int,
        target_id: int,
        group_id: int,
        exclude_email: str,
        now_tick: int,
        reentry_policy: int = int(WhiteboardReentryPolicy.OWNER_REENTRANT),
        claim_strength: int = int(WhiteboardClaimStrength.HARD),
    ) -> int:
        """Count matching active locks. Expired slots are ignored by readers."""
        if kind_id <= 0 or target_id < 0:
            return 0
        count = 0
        for i in range(SHMEM_MAX_INTENTS):
            intent = self.Intents[i]
            if not intent.Active:
                continue
            if now_tick >= int(intent.ExpiresAtTick):
                continue
            if int(intent.KindID) != int(kind_id):
                continue
            if int(intent.SkillID) != int(key_id):
                continue
            if int(intent.TargetAgentID) != int(target_id):
                continue
            if int(intent.IsolationGroupID) != int(group_id):
                continue
            if int(intent.ClaimStrength) != int(claim_strength):
                continue
            policy = int(intent.ReentryPolicy or reentry_policy)
            if (
                policy == int(WhiteboardReentryPolicy.OWNER_REENTRANT)
                and exclude_email
                and intent.OwnerEmail == exclude_email
            ):
                continue
            count += 1
        return count

    def IsLockBlocked(
        self,
        kind_id: int,
        key_id: int,
        target_id: int,
        group_id: int,
        exclude_email: str,
        now_tick: int,
        lock_mode: int = int(WhiteboardLockMode.EXCLUSIVE),
        max_holders: int = 1,
        reentry_policy: int = int(WhiteboardReentryPolicy.OWNER_REENTRANT),
        claim_strength: int = int(WhiteboardClaimStrength.HARD),
    ) -> bool:
        """True when matching unexpired locks should block this caller."""
        if int(max_holders) <= 0:
            max_holders = 1
        mode = int(lock_mode)
        if mode == int(WhiteboardLockMode.BARRIER):
            return False
        count = self.CountLocks(
            kind_id,
            key_id,
            target_id,
            group_id,
            exclude_email,
            now_tick,
            reentry_policy,
            claim_strength,
        )
        if mode == int(WhiteboardLockMode.EXCLUSIVE):
            return count >= 1
        if mode in (int(WhiteboardLockMode.SHARED), int(WhiteboardLockMode.SEMAPHORE)):
            return count >= int(max_holders)
        return False

    def IsLockSatisfied(
        self,
        kind_id: int,
        key_id: int,
        target_id: int,
        group_id: int,
        exclude_email: str,
        now_tick: int,
        required_holders: int,
        claim_strength: int = int(WhiteboardClaimStrength.HARD),
    ) -> bool:
        """Barrier helper: True when enough matching unexpired locks exist."""
        if required_holders <= 0:
            return True
        return self.CountLocks(
            kind_id,
            key_id,
            target_id,
            group_id,
            exclude_email,
            now_tick,
            int(WhiteboardReentryPolicy.NON_REENTRANT),
            claim_strength,
        ) >= int(required_holders)

    def PostIntent(
        self,
        owner_email: str,
        skill_id: int,
        target_agent_id: int,
        expires_at_tick: int,
        isolation_group_id: int | None = None,
    ) -> int:
        """Compatibility wrapper for the original skill-target whiteboard."""
        if skill_id <= 0 or target_agent_id <= 0:
            return -1
        return self.PostLock(
            owner_email,
            int(WhiteboardLockKind.SKILL_TARGET),
            int(skill_id),
            int(target_agent_id),
            int(expires_at_tick),
            isolation_group_id,
            int(WhiteboardLockMode.EXCLUSIVE),
            1,
            int(WhiteboardReentryPolicy.OWNER_REENTRANT),
            int(WhiteboardClaimStrength.HARD),
        )

    def IsIntentClaimed(
        self,
        skill_id: int,
        target_agent_id: int,
        group_id: int,
        exclude_email: str,
        now_tick: int,
    ) -> bool:
        """Compatibility read-gate for original (skill_id, target_agent_id)."""
        if skill_id <= 0 or target_agent_id <= 0:
            return False
        return self.IsLockBlocked(
            int(WhiteboardLockKind.SKILL_TARGET),
            int(skill_id),
            int(target_agent_id),
            int(group_id),
            exclude_email,
            int(now_tick),
            int(WhiteboardLockMode.EXCLUSIVE),
            1,
            int(WhiteboardReentryPolicy.OWNER_REENTRANT),
            int(WhiteboardClaimStrength.HARD),
        )

    def SweepExpiredIntents(self, now_tick: int) -> int:
        """Compact pass: zero expired slots. Returns count cleared."""
        count = 0
        for i in range(SHMEM_MAX_INTENTS):
            intent = self.Intents[i]
            if intent.Active and now_tick >= int(intent.ExpiresAtTick):
                lifetime = int(now_tick) - int(intent.PostedAtTick)
                self._wb_log(
                    int(intent.KindID),
                    f"SWEEP slot={i} email='{intent.OwnerEmail}' "
                    f"{self._wb_lock_display(intent)} lifetime={lifetime}ms reason=expired",
                )
                intent.reset()
                count += 1
        return count
