from typing import cast

from Py4GWCoreLib import GLOBAL_CACHE, Agent, Map, Player
from Py4GWCoreLib.GlobalCache.SharedMemory import AccountStruct

from Sources.oazix.CustomBehaviors.primitives.parties.memory_cache_manager import MemoryCacheManager


class CustomBehaviorHelperParty:
    @staticmethod
    def _get_account_from_agent_id(agent_id: int) -> AccountStruct | None:
        for account in GLOBAL_CACHE.ShMem.GetAllAccountData():
            if int(account.AgentData.AgentID) == int(agent_id):
                return account
        return None

    @staticmethod
    def _resolve_default_party_leader_email() -> str | None:
        account = CustomBehaviorHelperParty._get_account_from_agent_id(GLOBAL_CACHE.Party.GetPartyLeaderID())
        if account is None:
            return None
        result = account.AccountEmail
        MemoryCacheManager().set("party_leader_email", result)
        return result

    @staticmethod
    def _resolve_valid_party_leader_email(candidate_email: str | None) -> str | None:
        normalized_email = str(candidate_email or "").strip()
        if not normalized_email:
            return None

        leader_account = GLOBAL_CACHE.ShMem.GetAccountDataFromEmail(normalized_email)
        if leader_account is None:
            return None
        if not CustomBehaviorHelperParty.is_account_in_same_map_as_current_account(leader_account):
            return None
        return normalized_email

    @staticmethod
    def get_party_custom_target() -> int | None:
        # todo: rework need better abstraction
        from Sources.oazix.CustomBehaviors.primitives.parties.custom_behavior_shared_memory import (
            CustomBehaviorWidgetMemoryManager,
        )

        party_target_id: int | None = CustomBehaviorWidgetMemoryManager().GetCustomBehaviorWidgetData().party_target_id
        return party_target_id

    @staticmethod
    def is_account_in_same_map_as_current_account(account: AccountStruct):
        current_map_id = Map.GetMapID()
        current_region = Map.GetRegion()[0]
        current_district = Map.GetDistrict()
        current_language = Map.GetLanguage()[0]
        current_party_id = GLOBAL_CACHE.Party.GetPartyID()

        if current_map_id != account.AgentData.Map.MapID:
            return False

        if not Map.IsExplorable():
            # weird but in explorable, region can be different but still same map
            if current_region != account.AgentData.Map.Region:
                return False

        if current_district != account.AgentData.Map.District:
            return False
        if current_language != account.AgentData.Map.Language:
            return False
        if current_party_id != account.AgentPartyData.PartyID:
            return False

        return True

    @staticmethod
    def _get_party_leader_email() -> str | None:
        if MemoryCacheManager().has("party_leader_email"):
            cached_email = cast(str | None, MemoryCacheManager().get("party_leader_email"))
            resolved_cached_email = CustomBehaviorHelperParty._resolve_valid_party_leader_email(cached_email)
            if resolved_cached_email is not None:
                return resolved_cached_email

        # todo: rework need better abstraction
        from Sources.oazix.CustomBehaviors.primitives.parties.custom_behavior_shared_memory import (
            CustomBehaviorWidgetMemoryManager,
        )

        party_leader_email = CustomBehaviorWidgetMemoryManager().GetCustomBehaviorWidgetData().party_leader_email
        resolved_widget_email = CustomBehaviorHelperParty._resolve_valid_party_leader_email(party_leader_email)
        if resolved_widget_email is not None:
            MemoryCacheManager().set("party_leader_email", resolved_widget_email)
            return resolved_widget_email

        return CustomBehaviorHelperParty._resolve_default_party_leader_email()

    @staticmethod
    def is_party_leader() -> bool:
        if CustomBehaviorHelperParty._get_party_leader_email() == Player.GetAccountEmail():
            return True
        return False

    @staticmethod
    def get_party_leader_id() -> int:
        leader_email = CustomBehaviorHelperParty._get_party_leader_email()

        if leader_email is not None:
            account = GLOBAL_CACHE.ShMem.GetAccountDataFromEmail(leader_email)
            if account is not None and CustomBehaviorHelperParty.is_account_in_same_map_as_current_account(account):
                leader_agent_id = int(account.AgentData.AgentID)
                if leader_agent_id > 0 and Agent.IsValid(leader_agent_id):
                    return leader_agent_id

        return int(GLOBAL_CACHE.Party.GetPartyLeaderID())

    @staticmethod
    def get_own_party_index() -> int:
        players = GLOBAL_CACHE.Party.GetPlayers()
        my_id = Player.GetAgentID()
        for i, player in enumerate(players):
            agent_id = GLOBAL_CACHE.Party.Players.GetAgentIDByLoginNumber(player.login_number)
            if agent_id == my_id:
                return i
        return 0
