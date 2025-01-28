from Py4GWCoreLib import *

from .constants import (
    PLAYERS_MODULE_NAME,
    MAX_NUM_PLAYERS,
)

from .types import (
    PlayerStruct,
    CandidateStruct,
    GameOptionStruct,
    GameStruct,
)
from .globals import HeroAI_vars

def RegisterPlayer():
    """Register the current player to the shared memory."""
    global HeroAI_vars

    own_party_number = Party.GetOwnPartyNumber()
    if own_party_number == -1:
        return False

    self_id = Player.GetAgentID()

    HeroAI_vars.shared_memory_handler.set_player_property(own_party_number, "PlayerID", self_id)
    HeroAI_vars.shared_memory_handler.set_player_property(own_party_number, "Energy_Regen", Agent.GetEnergyRegen(self_id))
    HeroAI_vars.shared_memory_handler.set_player_property(own_party_number, "Energy", Agent.GetEnergy(self_id))
    HeroAI_vars.shared_memory_handler.set_player_property(own_party_number, "IsActive", True)
    HeroAI_vars.shared_memory_handler.set_player_property(own_party_number, "IsHero", False)

    HeroAI_vars.shared_memory_handler.register_buffs(self_id)


def RegisterHeroes():
    global HeroAI_vars

    heroes = Party.GetHeroes()
    for index, hero in enumerate(heroes):
        hero_party_number = Party.GetPlayerCount() + index
        agent_id = hero.agent_id
        if hero.owner_player_id == Agent.GetLoginNumber(Player.GetAgentID()): 
            HeroAI_vars.shared_memory_handler.set_player_property(hero_party_number, "PlayerID", agent_id)
            HeroAI_vars.shared_memory_handler.set_player_property(hero_party_number, "Energy_Regen", Agent.GetEnergyRegen(agent_id))
            HeroAI_vars.shared_memory_handler.set_player_property(hero_party_number, "Energy", Agent.GetEnergy(agent_id))
            HeroAI_vars.shared_memory_handler.set_player_property(hero_party_number, "IsActive", True)
            HeroAI_vars.shared_memory_handler.set_player_property(hero_party_number, "IsHero", True)

            HeroAI_vars.shared_memory_handler.register_buffs(agent_id)

def UpdatePlayers():
    """Update the player list from shared memory."""
    global HeroAI_vars

    for player in range(MAX_NUM_PLAYERS):
        player_data = HeroAI_vars.shared_memory_handler.get_player(player)

        HeroAI_vars.all_player_struct[player].PlayerID = player_data["PlayerID"]
        HeroAI_vars.all_player_struct[player].Energy_Regen = player_data["Energy_Regen"]
        HeroAI_vars.all_player_struct[player].Energy = player_data["Energy"]
        HeroAI_vars.all_player_struct[player].IsActive = player_data["IsActive"]
        HeroAI_vars.all_player_struct[player].IsHero = player_data["IsHero"]
        HeroAI_vars.all_player_struct[player].IsFlagged = player_data["IsFlagged"]
        HeroAI_vars.all_player_struct[player].FlagPosX = player_data["FlagPosX"]
        HeroAI_vars.all_player_struct[player].FlagPosY = player_data["FlagPosY"]
        HeroAI_vars.all_player_struct[player].FollowAngle = player_data["FollowAngle"]
        HeroAI_vars.all_player_struct[player].LastUpdated = player_data["LastUpdated"]
