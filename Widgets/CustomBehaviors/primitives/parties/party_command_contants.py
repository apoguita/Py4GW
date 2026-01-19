from typing import Generator, Any
from Py4GWCoreLib.GlobalCache import GLOBAL_CACHE
from Py4GWCoreLib.Player import Player
from Py4GWCoreLib.enums_src.Multiboxing_enums import SharedCommandType
from Py4GWCoreLib.routines_src.Yield import Yield
from Widgets.CustomBehaviors.primitives import constants
from Widgets.CustomBehaviors.primitives.helpers import custom_behavior_helpers

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
                GLOBAL_CACHE.ShMem.SendMessage(account_email, account.AccountEmail, SharedCommandType.TravelToMap, (self_account.MapID, self_account.MapRegion, self_account.MapDistrict, 0))
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
                if (self_account.MapID == account.MapID and
                    self_account.MapRegion == account.MapRegion and
                    self_account.MapDistrict == account.MapDistrict and
                    self_account.PartyID != account.PartyID):
                    GLOBAL_CACHE.Party.Players.InvitePlayer(account.CharacterName)
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
            yield from custom_behavior_helpers.Helpers.wait_for(100)
        yield

    @staticmethod
    def rename_gw_windows() -> Generator[Any, None, None]:
        account_email = Player.GetAccountEmail()
        accounts = GLOBAL_CACHE.ShMem.GetAllAccountData()
        for account in accounts:
            if constants.DEBUG: print(f"SendMessage {account_email} to {account.AccountEmail}")
            GLOBAL_CACHE.ShMem.SendMessage(account_email, account.AccountEmail, SharedCommandType.SetWindowTitle, ExtraData=(account.CharacterName, "", "", ""))
            yield from custom_behavior_helpers.Helpers.wait_for(100)
        yield