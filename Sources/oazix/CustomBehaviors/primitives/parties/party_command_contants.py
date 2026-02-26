import random
import time
from typing import Generator, Any
from Py4GWCoreLib.GlobalCache import GLOBAL_CACHE
from Py4GWCoreLib.Map import Map
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
    def resign_and_return_to_outpost(timeout_ms: int = 45_000) -> Generator[Any, None, None]:
        account_email = Player.GetAccountEmail()
        timeout_s = max(5.0, float(timeout_ms) / 1000.0)
        started_at = time.time()
        next_resign_send_at = 0.0

        while (time.time() - started_at) <= timeout_s:
            if Map.IsOutpost():
                return

            now_ts = time.time()
            if now_ts >= next_resign_send_at:
                accounts = GLOBAL_CACHE.ShMem.GetAllAccountData()
                for account in accounts:
                    if constants.DEBUG: print(f"SendMessage {account_email} to {account.AccountEmail}")
                    GLOBAL_CACHE.ShMem.SendMessage(account_email, account.AccountEmail, SharedCommandType.Resign, ())
                    yield from custom_behavior_helpers.Helpers.wait_for(30)
                next_resign_send_at = now_ts + 4.0

            if GLOBAL_CACHE.Party.IsPartyDefeated():
                GLOBAL_CACHE.Party.ReturnToOutpost()
                yield from custom_behavior_helpers.Helpers.wait_for(250)
                if Map.IsOutpost():
                    return

            yield from custom_behavior_helpers.Helpers.wait_for(120)

        yield
    
    @staticmethod
    def interract_with_target() -> Generator[Any, None, None]:
        # todo with a random.
        account_email = Player.GetAccountEmail()
        self_account = GLOBAL_CACHE.ShMem.GetAccountDataFromEmail(account_email)
        self_party_id = int(self_account.AgentPartyData.PartyID) if self_account is not None else 0
        accounts = GLOBAL_CACHE.ShMem.GetAllAccountData()
        target = Player.GetTargetID()
        for account in accounts:
            if account.AccountEmail == account_email:
                continue
            if self_party_id <= 0 or int(account.AgentPartyData.PartyID) != self_party_id:
                continue
            if constants.DEBUG: print(f"SendMessage {account_email} to {account.AccountEmail}")
            GLOBAL_CACHE.ShMem.SendMessage(account_email, account.AccountEmail, SharedCommandType.InteractWithTarget, (target,0,0,0))
            # randomize wait
            yield from custom_behavior_helpers.Helpers.wait_for(random.randint(100, 800))
        yield

    @staticmethod
    def interract_with_leader_selected_target() -> Generator[Any, None, None]:
        """
        Interact using leader's currently selected target.
        Fallback to shared party custom target if no live target is selected.
        Applies to all members, including the sender/leader.
        """
        from Sources.oazix.CustomBehaviors.primitives.parties.custom_behavior_party import CustomBehaviorParty
        account_email = Player.GetAccountEmail()
        self_account = GLOBAL_CACHE.ShMem.GetAccountDataFromEmail(account_email)
        self_party_id = int(self_account.AgentPartyData.PartyID) if self_account is not None else 0
        target = Player.GetTargetID()
        if target is None or int(target) == 0:
            target = CustomBehaviorParty().get_party_custom_target()
        if target is None or int(target) == 0:
            yield
            return

        Player.Interact(int(target), call_target=False)

        accounts = GLOBAL_CACHE.ShMem.GetAllAccountData()
        for account in accounts:
            if account.AccountEmail == account_email:
                continue
            if self_party_id <= 0 or int(account.AgentPartyData.PartyID) != self_party_id:
                continue
            if constants.DEBUG: print(f"SendMessage {account_email} to {account.AccountEmail}")
            GLOBAL_CACHE.ShMem.SendMessage(account_email, account.AccountEmail, SharedCommandType.InteractWithTarget, (int(target), 0, 0, 0))
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
