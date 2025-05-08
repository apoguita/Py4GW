from Py4GWCoreLib import *

from .constants import (
    CANDIDATES_MODULE_NAME,
    MAX_NUM_PLAYERS,
)

from .types import (
    CandidateStruct,
)

from .cache_data import CacheData

def RegisterCandidate(cached_data:CacheData):
    """Register the current player as a candidate."""
    if not cached_data.data.is_outpost:
        return False
    
    if cached_data.data.party_leader_id == cached_data.data.player_agent_id:
        cached_data.HeroAI_vars.submit_candidate_struct.PlayerID = cached_data.data.player_agent_id
        cached_data.HeroAI_vars.submit_candidate_struct.MapID = cached_data.data.map_id
        cached_data.HeroAI_vars.submit_candidate_struct.MapRegion = cached_data.data.region
        cached_data.HeroAI_vars.submit_candidate_struct.MapDistrict = cached_data.data.district

        cached_data.HeroAI_vars.shared_memory_handler.register_candidate(cached_data.HeroAI_vars.submit_candidate_struct)


def UpdateCandidates(cached_data:CacheData):
    """Update the candidate list from shared memory."""
    global MAX_NUM_PLAYERS

    if not cached_data.data.is_outpost:
        return False

    for player in range(MAX_NUM_PLAYERS):
        candidate_data = cached_data.HeroAI_vars.shared_memory_handler.get_candidate(player)
        if candidate_data is None:
            continue

        cached_data.HeroAI_vars.all_candidate_struct[player].PlayerID = candidate_data["PlayerID"]
        cached_data.HeroAI_vars.all_candidate_struct[player].MapID = candidate_data["MapID"]
        cached_data.HeroAI_vars.all_candidate_struct[player].MapRegion = candidate_data["MapRegion"]
        cached_data.HeroAI_vars.all_candidate_struct[player].MapDistrict = candidate_data["MapDistrict"]
        cached_data.HeroAI_vars.all_candidate_struct[player].InvitedBy = candidate_data["InvitedBy"]
        cached_data.HeroAI_vars.all_candidate_struct[player].SummonedBy = candidate_data["SummonedBy"]
        cached_data.HeroAI_vars.all_candidate_struct[player].LastUpdated = candidate_data["LastUpdated"]


def SendPartyCommand(index, cached_data:CacheData, command="Invite"):
    candidate = cached_data.HeroAI_vars.all_candidate_struct[index]

    if command == "Invite":
        if cached_data.data.RAW_AGENT_ARRAY is None:
            return False
        invited_by = cached_data.data.RAW_AGENT_ARRAY.get_name(candidate.PlayerID)
        #invited_by = Agent.GetName(candidate.PlayerID)
        #this is exempt of the action queue to allow instant invite
        Party.Players.InvitePlayer(invited_by)

    cached_data.HeroAI_vars.all_candidate_struct[index].InvitedBy=cached_data.data.player_agent_id
    updated_candidate = CandidateStruct(
                PlayerID=candidate.PlayerID,
                MapID=candidate.MapID,
                MapRegion=candidate.MapRegion,
                MapDistrict=candidate.MapDistrict,
                SummonedBy=cached_data.data.player_agent_id if command == "Summon" else 0,
                InvitedBy=cached_data.data.player_agent_id  if command == "Invite" else 0,
            )
    cached_data.HeroAI_vars.shared_memory_handler.set_candidate(index, updated_candidate)



def ProcessCandidateCommands(cached_data:CacheData):
    global MAX_NUM_PLAYERS
    try:
        if not cached_data.data.is_outpost or not cached_data.data.is_map_ready:
            return False

        self_index = -1

        for index in range(MAX_NUM_PLAYERS):
            candidate = cached_data.HeroAI_vars.all_candidate_struct[index]
            if candidate.PlayerID == cached_data.data.player_agent_id:
                self_index = index

        if self_index == -1:
            return False

        for index in range(MAX_NUM_PLAYERS):
            candidate = cached_data.HeroAI_vars.all_candidate_struct[index]

            if (candidate.PlayerID == cached_data.data.player_agent_id) and (candidate.InvitedBy != 0):      
                updated_candidate = CandidateStruct(
                    PlayerID=candidate.PlayerID,
                    MapID=candidate.MapID,
                    MapRegion=candidate.MapRegion,
                    MapDistrict=candidate.MapDistrict,
                    InvitedBy=0,
                    SummonedBy=0,
                )
                cached_data.HeroAI_vars.shared_memory_handler.set_candidate(self_index, updated_candidate)

                if cached_data.data.RAW_AGENT_ARRAY is None:
                    return False
                invited_by = cached_data.data.RAW_AGENT_ARRAY.get_name(candidate.InvitedBy)
                #invited_by = Agent.GetName(candidate.InvitedBy)
                ActionQueueManager().AddAction("ACTION", Party.Players.InvitePlayer, invited_by)
                return True

            if (candidate.PlayerID == cached_data.data.player_agent_id) and (candidate.SummonedBy != 0):

                leader_index = -1

                for l_index in range(MAX_NUM_PLAYERS):
                    leader = cached_data.HeroAI_vars.all_candidate_struct[l_index]
                    if leader.PlayerID == candidate.SummonedBy:
                        leader_index = l_index

                if leader_index == -1:
                    return False

                leader = cached_data.HeroAI_vars.all_candidate_struct[leader_index]
                updated_candidate = None
                if leader.PlayerID == candidate.SummonedBy:
                    updated_candidate = CandidateStruct(
                    PlayerID=candidate.PlayerID,
                    MapID=candidate.MapID,
                    MapRegion=candidate.MapRegion,
                    MapDistrict=candidate.MapDistrict,
                    InvitedBy=0,
                    SummonedBy=0,
                )
                cached_data.HeroAI_vars.shared_memory_handler.set_candidate(self_index, updated_candidate)

                ActionQueueManager().AddAction("ACTION", Map.TravelToDistrict, leader.MapID, leader.MapRegion, leader.MapDistrict)

                return True

    except Exception as e:
        # Catch-all for any other unexpected exceptions
        Py4GW.Console.Log(CANDIDATES_MODULE_NAME, f"Unexpected error encountered: {str(e)}", Py4GW.Console.MessageType.Error)
        Py4GW.Console.Log(CANDIDATES_MODULE_NAME, f"Stack trace: {traceback.format_exc()}", Py4GW.Console.MessageType.Error)
    finally:
        pass
