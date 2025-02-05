from Py4GWCoreLib import *

from .constants import (
    MAX_NUM_PLAYERS,
)


def RegisterPlayer(cache_data):
    """Register the current player to the shared memory."""
    if cache_data.data.own_party_number == -1:
        return False

    cache_data.HeroAI_vars.shared_memory_handler.set_player_property(cache_data.data.own_party_number, "PlayerID", cache_data.data.player_agent_id)
    cache_data.HeroAI_vars.shared_memory_handler.set_player_property(cache_data.data.own_party_number, "Energy_Regen", cache_data.data.energy_regen)
    cache_data.HeroAI_vars.shared_memory_handler.set_player_property(cache_data.data.own_party_number, "Energy", cache_data.data.energy)
    cache_data.HeroAI_vars.shared_memory_handler.set_player_property(cache_data.data.own_party_number, "IsActive", True)
    cache_data.HeroAI_vars.shared_memory_handler.set_player_property(cache_data.data.own_party_number, "IsHero", False)

    cache_data.HeroAI_vars.shared_memory_handler.register_buffs(cache_data.data.player_agent_id)


def RegisterHeroes(cache_data):
    for index, hero in enumerate(cache_data.data.heroes):
        hero_party_number =cache_data.data.party_player_count + index
        agent_id = hero.agent_id
        if hero.owner_player_id == cache_data.data.player_login_number: 
            cache_data.HeroAI_vars.shared_memory_handler.set_player_property(hero_party_number, "PlayerID", agent_id)
            cache_data.HeroAI_vars.shared_memory_handler.set_player_property(hero_party_number, "Energy_Regen", Agent.GetEnergyRegen(agent_id))
            cache_data.HeroAI_vars.shared_memory_handler.set_player_property(hero_party_number, "Energy", Agent.GetEnergy(agent_id))
            cache_data.HeroAI_vars.shared_memory_handler.set_player_property(hero_party_number, "IsActive", True)
            cache_data.HeroAI_vars.shared_memory_handler.set_player_property(hero_party_number, "IsHero", True)

            cache_data.HeroAI_vars.shared_memory_handler.register_buffs(agent_id)

def UpdatePlayers(cache_data):
    """Update the player list from shared memory."""
    global MAX_NUM_PLAYERS
    for player in range(MAX_NUM_PLAYERS):
        player_data = cache_data.HeroAI_vars.shared_memory_handler.get_player(player)

        cache_data.HeroAI_vars.all_player_struct[player].PlayerID = player_data["PlayerID"]
        cache_data.HeroAI_vars.all_player_struct[player].Energy_Regen = player_data["Energy_Regen"]
        cache_data.HeroAI_vars.all_player_struct[player].Energy = player_data["Energy"]
        cache_data.HeroAI_vars.all_player_struct[player].IsActive = player_data["IsActive"]
        cache_data.HeroAI_vars.all_player_struct[player].IsHero = player_data["IsHero"]
        cache_data.HeroAI_vars.all_player_struct[player].IsFlagged = player_data["IsFlagged"]
        cache_data.HeroAI_vars.all_player_struct[player].FlagPosX = player_data["FlagPosX"]
        cache_data.HeroAI_vars.all_player_struct[player].FlagPosY = player_data["FlagPosY"]
        cache_data.HeroAI_vars.all_player_struct[player].FollowAngle = player_data["FollowAngle"]
        cache_data.HeroAI_vars.all_player_struct[player].LastUpdated = player_data["LastUpdated"]
