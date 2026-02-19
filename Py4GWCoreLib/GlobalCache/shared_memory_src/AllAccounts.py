import ctypes
from operator import index
import Py4GW
from PyParty import HeroPartyMember, PetInfo
from ctypes import Structure, c_float
from Py4GWCoreLib.enums_src.Multiboxing_enums import SharedCommandType
from Py4GWCoreLib.py4gwcorelib_src.Console import ConsoleLog

from .Globals import (
    SHMEM_MAX_PLAYERS,
    SHMEM_MODULE_NAME,
    SHMEM_SUBSCRIBE_TIMEOUT_MILLISECONDS,
    SHMEM_MAX_CHAR_LEN,
    SHMEM_MAX_NUMBER_OF_SKILLS
    
)

from .SharedMessageStruct import SharedMessageStruct
from .HeroAIOptionStruct import HeroAIOptionStruct
from .AccountStruct import AccountStruct
from .KeyStruct import KeyStruct

#region AllAccounts 
class AllAccounts(Structure):
    _pack_ = 1
    _fields_ = [
        ("Keys", KeyStruct * SHMEM_MAX_PLAYERS),  # KeyStruct for each player slot
        ("AccountData", AccountStruct * SHMEM_MAX_PLAYERS),
        ("Inbox", SharedMessageStruct * SHMEM_MAX_PLAYERS),  # Messages for each player
        ("HeroAIOptions", HeroAIOptionStruct * SHMEM_MAX_PLAYERS),  # Game options for HeroAI
    ]
    
    # Type hints for IntelliSense
    AccountData: list["AccountStruct"]
    Inbox: list["SharedMessageStruct"]
    HeroAIOptions: list[HeroAIOptionStruct]
    Keys: list["KeyStruct"]
    
    def reset(self) -> None:
        """Reset all fields to zero."""
        for i in range(SHMEM_MAX_PLAYERS):
            self.Keys[i].reset()
            self.AccountData[i].reset()
            self.Inbox[i].reset()
            self.HeroAIOptions[i].reset()
            
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
    
    def GetEmptySlot(self) -> int:
        """Find the first empty slot in shared memory."""    
        for i, account in enumerate(self.AccountData):
            if not self._is_slot_active(i):
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
        owner_id = Party.Players.GetAgentIDByLoginNumber(hero_data.owner_player_id)
        expired_slots = self.GetExpiredSlots()
        for index in expired_slots:
            account_data = self.AccountData[index]
            if (account_data.IsHero and 
                account_data.AgentData.HeroID == hero_data.hero_id.GetID() and 
                account_data.AgentData.OwnerAgentID == owner_id):
                return index
        return -1
    
    def GetPetExpiredSlot(self, pet_data: PetInfo) -> int:
        """Find the slot index for the given pet data that has expired."""
        expired_slots = self.GetExpiredSlots()
        for index in expired_slots:
            account_data = self.AccountData[index]
            if (account_data.IsPet and 
                account_data.AgentData.AgentID == pet_data.agent_id and 
                account_data.AgentData.OwnerAgentID == pet_data.owner_agent_id):
                return index
        return -1
    
    def SubmitAccountData(self, account_email: str) -> int:
        """Submit account data to shared memory. Returns the slot index or -1 on failure."""
        if not account_email:
            ConsoleLog(SHMEM_MODULE_NAME, "Account email is empty.", Py4GW.Console.MessageType.Error)
            return -1
        
        slot_index = self.GetEmptySlot()
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
        slot_index = self.GetEmptySlot()
        if slot_index == -1:
            ConsoleLog(SHMEM_MODULE_NAME, "No empty slot available to submit hero data.", Py4GW.Console.MessageType.Error)
            return -1
        
        new_account = AccountStruct()
        new_account.from_hero_context(hero_data, slot_index)
        
        Key = KeyStruct().AsHeroKey(Py4GW.Console.get_gw_window_handle(), slot_index)
        self.Keys[slot_index] = new_account.Key = Key
        self.AccountData[slot_index] = new_account

        ConsoleLog(SHMEM_MODULE_NAME, f"Submitted hero data for HeroID {hero_data.hero_id.GetID()} at slot {slot_index}.", Py4GW.Console.MessageType.Info)
        return slot_index
    
    def SubmitPetData(self, pet_data: PetInfo) -> int:
        """Submit pet data to shared memory. Returns the slot index or -1 on failure."""
        slot_index = self.GetEmptySlot()
        if slot_index == -1:
            ConsoleLog(SHMEM_MODULE_NAME, "No empty slot available to submit pet data.", Py4GW.Console.MessageType.Error)
            return -1
        
        new_account = AccountStruct()
        new_account.from_pet_context(pet_data, slot_index)
        
        Key = KeyStruct().AsPetKey(Py4GW.Console.get_gw_window_handle(), slot_index)
        self.Keys[slot_index] = new_account.Key = Key
        self.AccountData[slot_index] = new_account
        
        ConsoleLog(SHMEM_MODULE_NAME, f"Submitted pet data for AgentID {pet_data.agent_id} at slot {slot_index}.", Py4GW.Console.MessageType.Info)
        return slot_index
    
    def SetPlayerData(self, account_email: str):
        """Set player data for the account with the given email."""  
        if not account_email:
            return    
        index = self.GetSlotByEmail(account_email)
        if index == -1:
            ConsoleLog(SHMEM_MODULE_NAME, f"No slot found for account {account_email}.", Py4GW.Console.MessageType.Warning)
            return
        
        new_account = AccountStruct()
        new_account.from_context(account_email, index)
        
        self.AccountData[index] = new_account
        
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
            ConsoleLog(SHMEM_MODULE_NAME, f"No slot found for hero {hero_data.hero_id.GetName()} (ID: {hero_data.hero_id.GetID()}).", Py4GW.Console.MessageType.Warning)
            return
        
        new_account = AccountStruct()
        new_account.from_hero_context(hero_data, index)
        if new_account.AgentData.AgentID== 0:
            return
        self.AccountData[index] = new_account
        
    def SetPetData(self):
        """Set pet data for the account with the given email."""
        from ...Player import Player
        from ...Party import Party
        
        owner_agent_id = Player.GetAgentID()
        pet_info = Party.Pets.GetPetInfo(owner_agent_id)
        # if not pet_info or pet_info.agent_id == 102298104:
        if not pet_info or (not pet_info.agent_id in Party.GetOthers()):
            return
        
        index = self.GetPetSlotByPetData(pet_info)
        if index == -1:
            ConsoleLog(SHMEM_MODULE_NAME, f"No slot found for pet {pet_info.agent_id}.", Py4GW.Console.MessageType.Warning)
            return
        
        new_account = AccountStruct()
        new_account.from_pet_context(pet_info, index)
        if new_account.AgentData.AgentID == 0:
            return
        self.AccountData[index] = new_account

    
    def GetSlotByEmail(self, account_email: str) -> int:
        if not account_email:
            return -1
        
        """Find the index of the account with the given email."""
        all_accounts = self.AccountData
        for i in range(SHMEM_MAX_PLAYERS):
            account = all_accounts[i]
            if account.AccountEmail == account_email and account.IsAccount:
                return i
            
        #submit if not found
        return self.SubmitAccountData(account_email)
    
    def GetAccountDataFromEmail(self, account_email: str) -> AccountStruct | None:
        """Get the account data for the given email, or None if not found."""
        index = self.GetSlotByEmail(account_email)
        if index != -1:
            return self.AccountData[index]
        return None
    
    def GetAccountDataFromPartyNumber(self, party_number: int, log : bool = False) -> AccountStruct | None:
        """Get player data for the account with the given party number."""
        all_accounts = self.AccountData
        for i in range(SHMEM_MAX_PLAYERS):
            player = all_accounts[i]
            if self._is_slot_active(i) and player.AgentPartyData.PartyPosition == party_number:
                return player
            
        return None
    
    def GetHeroSlotByHeroData(self, hero_data:HeroPartyMember) -> int:
        """Find the index of the hero with the given ID."""
        from ...Party import Party
        all_accounts = self.AccountData
        for i in range(SHMEM_MAX_PLAYERS):
            player = all_accounts[i]
   
            if (player.IsHero and 
                player.AgentData.HeroID == hero_data.hero_id.GetID() and 
                player.AgentData.OwnerAgentID == Party.Players.GetAgentIDByLoginNumber(hero_data.owner_player_id)
            ):
                return i
            
        #submit if not found
        return self.SubmitHeroData(hero_data)

    
    def GetPetSlotByPetData(self, pet_data:PetInfo) -> int:
        """Find the index of the pet with the given ID."""
        all_accounts = self.AccountData
        for i in range(SHMEM_MAX_PLAYERS):
            player = all_accounts[i]
  
            if (player.IsPet and 
                player.AgentData.AgentID == pet_data.agent_id and 
                player.AgentData.OwnerAgentID == pet_data.owner_agent_id
            ):
                return i
        return self.SubmitPetData(pet_data)
    
    def GetAllActivePlayers(self) -> list[AccountStruct]:
        """Get all active players in shared memory."""
        players : list[AccountStruct] = []
        for i in range(SHMEM_MAX_PLAYERS):
            account = self.AccountData[i]
            if account.IsSlotActive and account.IsAccount:
                players.append(account)
                
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
            if self._is_slot_active(i):
                count += 1
        return count
    
    def GetHeroesFromPlayers(self, owner_agent_id: int) -> list[AccountStruct]:
        """Get a list of heroes owned by the specified player."""
        heroes : list[AccountStruct] = []
        all_accounts = self.AccountData
        for i in range(SHMEM_MAX_PLAYERS):   
            account_data = all_accounts[i]

            if (self._is_slot_active(i) and account_data.IsHero and
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

            if (self._is_slot_active(i) and account_data.IsPet and
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
            if self._is_slot_active(i):
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
            if self._is_slot_active(i) and player.IsAccount:
                options.append(self.HeroAIOptions[i])
        return options
    
    def GetHeroAIOptionsFromEmail(self, account_email: str) -> HeroAIOptionStruct | None:
        """Get HeroAI options for the account with the given email."""
        if not account_email:
            return None
        index = self.GetSlotByEmail(account_email)
        if index != -1:
            return self.HeroAIOptions[index]
        else:
            ConsoleLog(SHMEM_MODULE_NAME, f"Account {account_email} not found.", Py4GW.Console.MessageType.Error, log = False)
            return None
        
    def GetHeroAIOptionsByPartyNumber(self, party_number: int) -> HeroAIOptionStruct | None:
        """Get HeroAI options for the account with the given party number."""
        for i in range(SHMEM_MAX_PLAYERS):
            player = self.AccountData[i]
            if self._is_slot_active(i) and player.AgentPartyData.PartyPosition == party_number:
                return self.HeroAIOptions[i]
        return None 
    
    def SetHeroAIOptionsByEmail(self, account_email: str, options: HeroAIOptionStruct):
        """Set HeroAI options for the account with the given email."""
        if not account_email:
            return
        index = self.GetSlotByEmail(account_email)
        if index != -1:
            self.HeroAIOptions[index] = options
        else:
            ConsoleLog(SHMEM_MODULE_NAME, f"Account {account_email} not found.", Py4GW.Console.MessageType.Error, log = False)
    
    def SetHeroAIPropertyByEmail(self, account_email: str, property_name: str, value):
        """Set a specific HeroAI property for the account with the given email."""
        if not account_email:
            return
        index = self.GetSlotByEmail(account_email)
        if index != -1:
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
            if self._is_slot_active(i) and player.IsAccount:
                maps.add((player.AgentData.Map.MapID, player.AgentData.Map.Region, player.AgentData.Map.District, player.AgentData.Map.Language))
        return list(maps)
    
    def GetPartiesFromMaps(self, map_id: int, map_region: int, map_district: int, map_language: int):
        """
        Get a list of unique PartyIDs for players in the specified map/region/district.
        """
        parties = set()
        for i in range(SHMEM_MAX_PLAYERS):
            player = self.AccountData[i]
            if (self._is_slot_active(i) and player.IsAccount and
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
            if (self._is_slot_active(i) and account_data.IsAccount and
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
            if message.Active:
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
        
        if index == -1:
            ConsoleLog(SHMEM_MODULE_NAME, f"Receiver account {receiver_email} not found.", Py4GW.Console.MessageType.Error)
            return -1
        
        if not receiver_email:
            ConsoleLog(SHMEM_MODULE_NAME, "Receiver email is empty.", Py4GW.Console.MessageType.Error)
            return -1
        
        if not sender_email:
            ConsoleLog(SHMEM_MODULE_NAME, "Sender email is empty.", Py4GW.Console.MessageType.Error)
            return -1
        
        for i in range(SHMEM_MAX_PLAYERS):
            message = self.GetInbox(i)
            if message.Active:
                continue  # Find the first unfinished message slot
            
            message.SenderEmail = sender_email
            message.ReceiverEmail = receiver_email
            message.Command = command.value
            message.Params = (c_float * 4)(*params)
            # Pack 4 strings into 4 arrays of c_wchar[SHMEM_MAX_CHAR_LEN]
            arr_type = ct.c_wchar * SHMEM_MAX_CHAR_LEN
            packed = [self._str_to_c_wchar_array(
                        ExtraData[j] if j < len(ExtraData) else "",
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
            if message.ReceiverEmail == account_email and message.Active and not message.Running:
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
