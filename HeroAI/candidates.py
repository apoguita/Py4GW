from Py4GWCoreLib import *

from .constants import (
    CANDIDATES_MODULE_NAME,
    MAX_NUM_PLAYERS,
)

from .types import (
    CandidateStruct,
)

def RegisterCandidate(cache_data):
    """Register the current player as a candidate."""
    try:
        if not cache_data.data.is_outpost:
            return False
        
        if cache_data.data.party_leader_id == cache_data.data.player_agent_id:
            cache_data.HeroAI_vars.submit_candidate_struct.PlayerID = cache_data.data.player_agent_id
            cache_data.HeroAI_vars.submit_candidate_struct.MapID = cache_data.data.map_id
            cache_data.HeroAI_vars.submit_candidate_struct.MapRegion = cache_data.data.region
            cache_data.HeroAI_vars.submit_candidate_struct.MapDistrict = cache_data.data.district

            cache_data.HeroAI_vars.shared_memory_handler.register_candidate(cache_data.HeroAI_vars.submit_candidate_struct)

    except Exception as e:
        # Catch-all for any other unexpected exceptions
        Py4GW.Console.Log(CANDIDATES_MODULE_NAME, f"Unexpected error encountered: {str(e)}", Py4GW.Console.MessageType.Error)
        Py4GW.Console.Log(CANDIDATES_MODULE_NAME, f"Stack trace: {traceback.format_exc()}", Py4GW.Console.MessageType.Error)
    finally:
        pass


def UpdateCandidates(cache_data):
    """Update the candidate list from shared memory."""
    global MAX_NUM_PLAYERS
    try:
        if not cache_data.data.is_outpost:
            return False

        for player in range(MAX_NUM_PLAYERS):
            candidate_data = cache_data.HeroAI_vars.shared_memory_handler.get_candidate(player)

            cache_data.HeroAI_vars.all_candidate_struct[player].PlayerID = candidate_data["PlayerID"]
            cache_data.HeroAI_vars.all_candidate_struct[player].MapID = candidate_data["MapID"]
            cache_data.HeroAI_vars.all_candidate_struct[player].MapRegion = candidate_data["MapRegion"]
            cache_data.HeroAI_vars.all_candidate_struct[player].MapDistrict = candidate_data["MapDistrict"]
            cache_data.HeroAI_vars.all_candidate_struct[player].InvitedBy = candidate_data["InvitedBy"]
            cache_data.HeroAI_vars.all_candidate_struct[player].SummonedBy = candidate_data["SummonedBy"]
            cache_data.HeroAI_vars.all_candidate_struct[player].LastUpdated = candidate_data["LastUpdated"]

    except Exception as e:
        # Catch-all for any other unexpected exceptions
        Py4GW.Console.Log(CANDIDATES_MODULE_NAME, f"Unexpected error encountered: {str(e)}", Py4GW.Console.MessageType.Error)
        Py4GW.Console.Log(CANDIDATES_MODULE_NAME, f"Stack trace: {traceback.format_exc()}", Py4GW.Console.MessageType.Error)
    finally:
        pass

def SendPartyCommand(index, cache_data, command="Invite"):
    try:
        candidate = cache_data.HeroAI_vars.all_candidate_struct[index]

        if command == "Invite":
            Party.Players.InvitePlayer(Agent.GetName(candidate.PlayerID))

        cache_data.HeroAI_vars.all_candidate_struct[index].InvitedBy=cache_data.data.player_agent_id
        updated_candidate = CandidateStruct(
                    PlayerID=candidate.PlayerID,
                    MapID=candidate.MapID,
                    MapRegion=candidate.MapRegion,
                    MapDistrict=candidate.MapDistrict,
                    SummonedBy=cache_data.data.player_agent_id if command == "Summon" else 0,
                    InvitedBy=cache_data.data.player_agent_id  if command == "Invite" else 0,
                )
        cache_data.HeroAI_vars.shared_memory_handler.set_candidate(index, updated_candidate)

    except ImportError as e:
        Py4GW.Console.Log(CANDIDATES_MODULE_NAME, f"ImportError encountered: {str(e)}", Py4GW.Console.MessageType.Error)
        Py4GW.Console.Log(CANDIDATES_MODULE_NAME, f"Stack trace: {traceback.format_exc()}", Py4GW.Console.MessageType.Error)
    except ValueError as e:
        Py4GW.Console.Log(CANDIDATES_MODULE_NAME, f"ValueError encountered: {str(e)}", Py4GW.Console.MessageType.Error)
        Py4GW.Console.Log(CANDIDATES_MODULE_NAME, f"Stack trace: {traceback.format_exc()}", Py4GW.Console.MessageType.Error)
    except TypeError as e:
        Py4GW.Console.Log(CANDIDATES_MODULE_NAME, f"TypeError encountered: {str(e)}", Py4GW.Console.MessageType.Error)
        Py4GW.Console.Log(CANDIDATES_MODULE_NAME, f"Stack trace: {traceback.format_exc()}", Py4GW.Console.MessageType.Error)
    except Exception as e:
        # Catch-all for any other unexpected exceptions
        Py4GW.Console.Log(CANDIDATES_MODULE_NAME, f"Unexpected error encountered: {str(e)}", Py4GW.Console.MessageType.Error)
        Py4GW.Console.Log(CANDIDATES_MODULE_NAME, f"Stack trace: {traceback.format_exc()}", Py4GW.Console.MessageType.Error)
    finally:
        pass  


def ProcessCandidateCommands(cache_data):
    global MAX_NUM_PLAYERS
    try:
        if not cache_data.data.is_outpost or not cache_data.data.is_map_ready:
            return False

        self_index = -1

        for index in range(MAX_NUM_PLAYERS):
            candidate = cache_data.HeroAI_vars.all_candidate_struct[index]
            if candidate.PlayerID == cache_data.data.player_agent_id:
                self_index = index

        if self_index == -1:
            return False

        for index in range(MAX_NUM_PLAYERS):
            candidate = cache_data.HeroAI_vars.all_candidate_struct[index]

            if (candidate.PlayerID == cache_data.data.player_agent_id) and (candidate.InvitedBy != 0):      
                updated_candidate = CandidateStruct(
                    PlayerID=candidate.PlayerID,
                    MapID=candidate.MapID,
                    MapRegion=candidate.MapRegion,
                    MapDistrict=candidate.MapDistrict,
                    InvitedBy=0,
                    SummonedBy=0,
                )
                cache_data.HeroAI_vars.shared_memory_handler.set_candidate(self_index, updated_candidate)

                Party.Players.InvitePlayer(Agent.GetName(candidate.InvitedBy))
                return True

            if (candidate.PlayerID == cache_data.data.player_agent_id) and (candidate.SummonedBy != 0):

                leader_index = -1

                for l_index in range(MAX_NUM_PLAYERS):
                    leader = cache_data.HeroAI_vars.all_candidate_struct[l_index]
                    if leader.PlayerID == candidate.SummonedBy:
                        leader_index = l_index

                if leader_index == -1:
                    return False

                leader = cache_data.HeroAI_vars.all_candidate_struct[leader_index]

                if leader.PlayerID == candidate.SummonedBy:
                    updated_candidate = CandidateStruct(
                    PlayerID=candidate.PlayerID,
                    MapID=candidate.MapID,
                    MapRegion=candidate.MapRegion,
                    MapDistrict=candidate.MapDistrict,
                    InvitedBy=0,
                    SummonedBy=0,
                )
                cache_data.HeroAI_vars.shared_memory_handler.set_candidate(self_index, updated_candidate)

                Map.TravelToDistrict(leader.MapID, leader.MapRegion, leader.MapDistrict)

                return True

    except Exception as e:
        # Catch-all for any other unexpected exceptions
        Py4GW.Console.Log(CANDIDATES_MODULE_NAME, f"Unexpected error encountered: {str(e)}", Py4GW.Console.MessageType.Error)
        Py4GW.Console.Log(CANDIDATES_MODULE_NAME, f"Stack trace: {traceback.format_exc()}", Py4GW.Console.MessageType.Error)
    finally:
        pass
