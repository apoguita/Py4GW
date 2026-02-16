import random
from typing import Generator, Any
from Py4GWCoreLib.GlobalCache import GLOBAL_CACHE
from Py4GWCoreLib.Player import Player
from Py4GWCoreLib.enums_src.Multiboxing_enums import SharedCommandType
from Py4GWCoreLib.routines_src.Yield import Yield
from Sources.oazix.CustomBehaviors.primitives import constants
from Sources.oazix.CustomBehaviors.primitives.helpers import custom_behavior_helpers

class PartyCommandConstants:

    @staticmethod    
    def summon_all_to_current_map() -> Generator[Any, None, None]:
        account_email = Player.GetAccountEmail()
        self_account = GLOBAL_CACHE.ShMem.GetAccountDataFromEmail(account_email)
        if self_account is not None:
            accounts = GLOBAL_CACHE.ShMem.GetAllAccountData()
            for account in accounts:
                if account.AccountEmail == account_email:
                    continue
                if constants.DEBUG: print(f"SendMessage {account_email} to {account.AccountEmail}")
                GLOBAL_CACHE.ShMem.SendMessage(account_email, account.AccountEmail, SharedCommandType.TravelToMap, (self_account.AgentData.Map.MapID, self_account.AgentData.Map.Region, self_account.AgentData.Map.District, 0))
        yield

    @staticmethod    
    def travel_gh() -> Generator[Any, None, None]:
        account_email = Player.GetAccountEmail()
        self_account = GLOBAL_CACHE.ShMem.GetAccountDataFromEmail(account_email)
        if self_account is not None:
            accounts = GLOBAL_CACHE.ShMem.GetAllAccountData()
            for account in accounts:
                if constants.DEBUG: print(f"SendMessage {account_email} to {account.AccountEmail}")
                GLOBAL_CACHE.ShMem.SendMessage(account_email, account.AccountEmail, SharedCommandType.TravelToGuildHall, (0,0,0,0))
        yield

    @staticmethod
    def invite_all_to_leader_party() -> Generator[Any, None, None]:
        account_email = Player.GetAccountEmail()
        self_account = GLOBAL_CACHE.ShMem.GetAccountDataFromEmail(account_email)
        if self_account is not None:
            accounts = GLOBAL_CACHE.ShMem.GetAllAccountData()
            for account in accounts:
                if account.AccountEmail == account_email:
                    continue
                if constants.DEBUG: print(f"SendMessage {account_email} to {account.AccountEmail}")
                if (self_account.AgentData.Map.MapID == account.AgentData.Map.MapID and
                    self_account.AgentData.Map.Region == account.AgentData.Map.Region and
                    self_account.AgentData.Map.District == account.AgentData.Map.District and
                    self_account.AgentPartyData.PartyID != account.AgentPartyData.PartyID):
                    GLOBAL_CACHE.Party.Players.InvitePlayer(account.AgentData.CharacterName)
                    GLOBAL_CACHE.ShMem.SendMessage(account_email, account.AccountEmail, SharedCommandType.InviteToParty, (0,0,0,0))
                    yield from custom_behavior_helpers.Helpers.wait_for(300)
    
    @staticmethod
    def leave_current_party() -> Generator[Any, None, None]:
        account_email = Player.GetAccountEmail()
        self_account = GLOBAL_CACHE.ShMem.GetAccountDataFromEmail(account_email)
        accounts = GLOBAL_CACHE.ShMem.GetAllAccountData()
        for account in accounts:
            if account.AccountEmail == account_email:
                continue
            if constants.DEBUG: print(f"SendMessage {account_email} to {account.AccountEmail}")
            GLOBAL_CACHE.ShMem.SendMessage(account_email, account.AccountEmail, SharedCommandType.LeaveParty, ())
            yield from custom_behavior_helpers.Helpers.wait_for(30)
        yield
    
    @staticmethod
    def resign() -> Generator[Any, None, None]:
        account_email = Player.GetAccountEmail()
        accounts = GLOBAL_CACHE.ShMem.GetAllAccountData()
        for account in accounts:
            if constants.DEBUG: print(f"SendMessage {account_email} to {account.AccountEmail}")
            GLOBAL_CACHE.ShMem.SendMessage(account_email, account.AccountEmail, SharedCommandType.Resign, ())
            yield from custom_behavior_helpers.Helpers.wait_for(30)
        yield
    
    @staticmethod
    def interract_with_target() -> Generator[Any, None, None]:
        # todo with a random.
        account_email = Player.GetAccountEmail()
        accounts = GLOBAL_CACHE.ShMem.GetAllAccountData()
        target = Player.GetTargetID()
        for account in accounts:
            if account.AccountEmail == account_email:
                continue
            if constants.DEBUG: print(f"SendMessage {account_email} to {account.AccountEmail}")
            GLOBAL_CACHE.ShMem.SendMessage(account_email, account.AccountEmail, SharedCommandType.InteractWithTarget, (target,0,0,0))
            # randomize wait
            yield from custom_behavior_helpers.Helpers.wait_for(random.randint(100, 800))
        yield

    @staticmethod
    def rename_gw_windows() -> Generator[Any, None, None]:
        account_email = Player.GetAccountEmail()
        accounts = GLOBAL_CACHE.ShMem.GetAllAccountData()
        for account in accounts:
            if constants.DEBUG: print(f"SendMessage {account_email} to {account.AccountEmail}")
            GLOBAL_CACHE.ShMem.SendMessage(account_email, account.AccountEmail, SharedCommandType.SetWindowTitle, ExtraData=(account.AgentData.CharacterName, "", "", ""))
            yield from custom_behavior_helpers.Helpers.wait_for(100)
        yield

    @staticmethod
    def focus_window(target_account_email: str) -> Generator[Any, None, None]:
        """Focus/activate a specific game window by account email."""
        yield from custom_behavior_helpers.Helpers.wait_for(1000)

        account_email = Player.GetAccountEmail()
        if constants.DEBUG: print(f"SendMessage {account_email} to {target_account_email} - SetWindowActive")
        GLOBAL_CACHE.ShMem.SendMessage(account_email, target_account_email, SharedCommandType.SetWindowActive, (0, 0, 0, 0))
        yield

    @staticmethod
    def invite_player(target_account_email: str, character_name: str) -> Generator[Any, None, None]:
        """Invite a specific player to the party using chat command and messaging."""
        account_email = Player.GetAccountEmail()
        if constants.DEBUG: print(f"Inviting {character_name} ({target_account_email}) to party")
        GLOBAL_CACHE.Party.Players.InvitePlayer(character_name)
        GLOBAL_CACHE.ShMem.SendMessage(account_email, target_account_email, SharedCommandType.InviteToParty, (0, 0, 0, 0))
        yield from custom_behavior_helpers.Helpers.wait_for(300)
        yield