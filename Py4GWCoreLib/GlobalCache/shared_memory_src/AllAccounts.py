import ctypes
import Py4GW
from PyParty import HeroPartyMember, PetInfo
from ctypes import Structure, c_float
from Py4GWCoreLib.enums_src.Multiboxing_enums import SharedCommandType
from Py4GWCoreLib.py4gwcorelib_src.Console import ConsoleLog

from .Globals import (
    SHMEM_MAX_PLAYERS,
    SHMEM_MODULE_NAME,
    SHMEM_SUBSCRIBE_TIMEOUT_MILLISECONDS,
    SHMEM_MAX_CHAR_LEN
    
)

from .SharedMessageStruct import SharedMessageStruct
from .HeroAIOptionStruct import HeroAIOptionStruct
from .AccountStruct import AccountStruct

#region AllAccounts 
class AllAccounts(Structure):
    _pack_ = 1
    _fields_ = [
        ("AccountData", AccountStruct * SHMEM_MAX_PLAYERS),
        ("Inbox", SharedMessageStruct * SHMEM_MAX_PLAYERS),  # Messages for each player
        ("HeroAIOptions", HeroAIOptionStruct * SHMEM_MAX_PLAYERS),  # Game options for HeroAI
    ]
    
    # Type hints for IntelliSense
    AccountData: list["AccountStruct"]
    Inbox: list["SharedMessageStruct"]
    HeroAIOptions: list[HeroAIOptionStruct]
    
    def reset(self) -> None:
        """Reset all fields to zero."""
        for i in range(SHMEM_MAX_PLAYERS):
            self.AccountData[i].reset()
            self.Inbox[i].reset()
            self.HeroAIOptions[i].reset()
            
    def SetPlayerData(self, Account_email: str) -> None:
        """Set player data for a specific account email."""
        if not Account_email:
            return 
        
        index = self.GetSlotByEmail(Account_email)
        if index == -1:
            ConsoleLog(SHMEM_MODULE_NAME, f"No slot found for account {Account_email}.", Py4GW.Console.MessageType.Warning)
            return
        
        account = self.AccountData[index] 
        account.from_context(Account_email, index) 
        
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
    
    def SubmitAccountData(self, account_email: str) -> int:
        """Submit account data to shared memory. Returns the slot index or -1 on failure."""
        if not account_email:
            ConsoleLog(SHMEM_MODULE_NAME, "Account email is empty.", Py4GW.Console.MessageType.Error)
            return -1
        
        slot_index = self.GetEmptySlot()
        if slot_index == -1:
            ConsoleLog(SHMEM_MODULE_NAME, "No empty slot available to submit account data.", Py4GW.Console.MessageType.Error)
            return -1
        
        account_data = self.AccountData[slot_index]
        account_data.AgentData.reset()
        account_data.AccountEmail = account_email
        account_data.SlotNumber = slot_index
        account_data.IsAccount = True
        account_data.IsHero = False
        account_data.IsPet = False
        account_data.IsNPC = False
        account_data.IsSlotActive = True
        account_data.LastUpdated = Py4GW.Game.get_tick_count64()
        
        ConsoleLog(SHMEM_MODULE_NAME, f"Submitted account data for {account_email} at slot {slot_index}.", Py4GW.Console.MessageType.Info)
        return slot_index
    
    def SubmitHeroData(self, hero_data: HeroPartyMember) -> int:
        """Submit hero data to shared memory. Returns the slot index or -1 on failure."""
        slot_index = self.GetEmptySlot()
        if slot_index == -1:
            ConsoleLog(SHMEM_MODULE_NAME, "No empty slot available to submit hero data.", Py4GW.Console.MessageType.Error)
            return -1
        
        account_data = self.AccountData[slot_index]
        account_data.AgentData.reset()
        account_data.AgentData.HeroID = hero_data.hero_id.GetID()
        account_data.AgentData.OwnerAgentID = hero_data.owner_player_id
        account_data.SlotNumber = slot_index
        account_data.IsAccount = False
        account_data.IsHero = True
        account_data.IsPet = False
        account_data.IsNPC = False
        account_data.IsSlotActive = True
        account_data.LastUpdated = Py4GW.Game.get_tick_count64()
        
        ConsoleLog(SHMEM_MODULE_NAME, f"Submitted hero data for HeroID {hero_data.hero_id.GetID()} at slot {slot_index}.", Py4GW.Console.MessageType.Info)
        return slot_index
    
    def SubmitPetData(self, pet_data: PetInfo) -> int:
        """Submit pet data to shared memory. Returns the slot index or -1 on failure."""
        slot_index = self.GetEmptySlot()
        if slot_index == -1:
            ConsoleLog(SHMEM_MODULE_NAME, "No empty slot available to submit pet data.", Py4GW.Console.MessageType.Error)
            return -1
        
        account_data = self.AccountData[slot_index]
        account_data.AgentData.reset()
        account_data.AgentData.AgentID = pet_data.agent_id
        account_data.AgentData.OwnerAgentID = pet_data.owner_agent_id
        account_data.SlotNumber = slot_index
        account_data.IsAccount = False
        account_data.IsHero = False
        account_data.IsPet = True
        account_data.IsNPC = False
        account_data.IsSlotActive = True
        account_data.LastUpdated = Py4GW.Game.get_tick_count64()
        
        ConsoleLog(SHMEM_MODULE_NAME, f"Submitted pet data for AgentID {pet_data.agent_id} at slot {slot_index}.", Py4GW.Console.MessageType.Info)
        return slot_index
    
    
    def GetSlotByEmail(self, account_email: str) -> int:
        if not account_email:
            return -1
        
        """Find the index of the account with the given email."""
        for i in range(SHMEM_MAX_PLAYERS):
            #if not self._is_slot_active(i):
            #    continue
            
            player = self.GetAccountData(i)
            if self.AccountData[i].AccountEmail == account_email and player.IsAccount:
                return i
            
        #submit if not found
        return self.SubmitAccountData(account_email)

    
    def GetHeroSlotByHeroData(self, hero_data:HeroPartyMember) -> int:
        """Find the index of the hero with the given ID."""
        from ...Party import Party
        for i in range(SHMEM_MAX_PLAYERS):
            player = self.AccountData[i]
            #if not player.IsSlotActive:
            #if not self._is_slot_active(i):
            #    continue
            if (player.IsHero and 
                player.AgentData.HeroID == hero_data.hero_id.GetID() and 
                player.AgentData.OwnerAgentID == Party.Players.GetAgentIDByLoginNumber(hero_data.owner_player_id)
            ):
                return i
            
        #submit if not found
        return self.SubmitHeroData(hero_data)

    
    def GetPetSlotByPetData(self, pet_data:PetInfo) -> int:
        """Find the index of the pet with the given ID."""
        for i in range(SHMEM_MAX_PLAYERS):
            player = self.AccountData[i]
            #if not player.IsSlotActive:
            #if not self._is_slot_active(i):
            #    continue
            if (player.IsPet and 
                player.AgentData.AgentID == pet_data.agent_id and 
                player.AgentData.OwnerAgentID == pet_data.owner_agent_id
            ):
                return i
        return self.SubmitPetData(pet_data)
            
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
