from Py4GWCoreLib import *

from .constants import (
    CANDIDATES_MODULE_NAME,
    MAX_NUM_PLAYERS,
)

from .types import (
    PlayerStruct,
    CandidateStruct,
    GameOptionStruct,
    GameStruct,
)
from .globals import HeroAI_vars, HeroAI_windows, Debug_window_vars

def RegisterCandidate():
    """Register the current player as a candidate."""
    global HeroAI_vars
    try:

        if not Map.IsOutpost():
            return False

        if Party.GetPartyLeaderID() == Player.GetAgentID():
            HeroAI_vars.submit_candidate_struct.PlayerID = Player.GetAgentID()
            HeroAI_vars.submit_candidate_struct.MapID = Map.GetMapID()
            region, _ = Map.GetRegion()
            HeroAI_vars.submit_candidate_struct.MapRegion = region
            HeroAI_vars.submit_candidate_struct.MapDistrict = Map.GetDistrict()

            HeroAI_vars.shared_memory_handler.register_candidate(HeroAI_vars.submit_candidate_struct)

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


def UpdateCandidates():
    """Update the candidate list from shared memory."""
    global HeroAI_vars
    try:
        if not Map.IsOutpost():
            return False

        for player in range(MAX_NUM_PLAYERS):
            candidate_data = HeroAI_vars.shared_memory_handler.get_candidate(player)

            HeroAI_vars.all_candidate_struct[player].PlayerID = candidate_data["PlayerID"]
            HeroAI_vars.all_candidate_struct[player].MapID = candidate_data["MapID"]
            HeroAI_vars.all_candidate_struct[player].MapRegion = candidate_data["MapRegion"]
            HeroAI_vars.all_candidate_struct[player].MapDistrict = candidate_data["MapDistrict"]
            HeroAI_vars.all_candidate_struct[player].InvitedBy = candidate_data["InvitedBy"]
            HeroAI_vars.all_candidate_struct[player].SummonedBy = candidate_data["SummonedBy"]
            HeroAI_vars.all_candidate_struct[player].LastUpdated = candidate_data["LastUpdated"]

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

def SendPartyCommand(index, command="Invite"):
    global HeroAI_vars
    try:
        candidate = HeroAI_vars.all_candidate_struct[index]

        if command == "Invite":
            Party.Players.InvitePlayer(Agent.GetName(candidate.PlayerID))

        HeroAI_vars.all_candidate_struct[index].InvitedBy=Player.GetAgentID()
        updated_candidate = CandidateStruct(
                    PlayerID=candidate.PlayerID,
                    MapID=candidate.MapID,
                    MapRegion=candidate.MapRegion,
                    MapDistrict=candidate.MapDistrict,
                    SummonedBy=Player.GetAgentID() if command == "Summon" else 0,
                    InvitedBy=Player.GetAgentID()  if command == "Invite" else 0,
                )
        HeroAI_vars.shared_memory_handler.set_candidate(index, updated_candidate)

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


def ProcessCandidateCommands():
    global HeroAI_vars
    try:
        if not Map.IsOutpost():
            return False

        self_index = -1

        for index in range(MAX_NUM_PLAYERS):
            candidate = HeroAI_vars.all_candidate_struct[index]
            if candidate.PlayerID == Player.GetAgentID():
                self_index = index

        if self_index == -1:
            return False

        for index in range(MAX_NUM_PLAYERS):
            candidate = HeroAI_vars.all_candidate_struct[index]

            if candidate.PlayerID == Player.GetAgentID() and candidate.InvitedBy != 0:      
                updated_candidate = CandidateStruct(
                    PlayerID=candidate.PlayerID,
                    MapID=candidate.MapID,
                    MapRegion=candidate.MapRegion,
                    MapDistrict=candidate.MapDistrict,
                    InvitedBy=0,
                    SummonedBy=0,
                )
                HeroAI_vars.shared_memory_handler.set_candidate(self_index, updated_candidate)

                Party.Players.InvitePlayer(Agent.GetName(candidate.InvitedBy))
                return True

            if candidate.PlayerID == Player.GetAgentID() and candidate.SummonedBy != 0:

                leader_index = -1

                for l_index in range(MAX_NUM_PLAYERS):
                    leader = HeroAI_vars.all_candidate_struct[l_index]
                    if leader.PlayerID == candidate.SummonedBy:
                        leader_index = l_index

                if leader_index == -1:
                    return False

                leader = HeroAI_vars.all_candidate_struct[leader_index]

                if leader.PlayerID == candidate.SummonedBy:
                    updated_candidate = CandidateStruct(
                    PlayerID=candidate.PlayerID,
                    MapID=candidate.MapID,
                    MapRegion=candidate.MapRegion,
                    MapDistrict=candidate.MapDistrict,
                    InvitedBy=0,
                    SummonedBy=0,
                )
                HeroAI_vars.shared_memory_handler.set_candidate(self_index, updated_candidate)

                Map.TravelToDistrict(leader.MapID, leader.MapRegion, leader.MapDistrict)

                return True

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
