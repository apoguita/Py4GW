from Py4GWCoreLib import GLOBAL_CACHE
from .constants import MAX_NUM_PLAYERS
from .cache_data import CacheData


def RegisterPlayer(cached_data:CacheData):
    """Register the current player to the shared memory."""
    if GLOBAL_CACHE.Party.GetOwnPartyNumber() == -1:
        return False

    cached_data.HeroAI_vars.shared_memory_handler.set_player_property(GLOBAL_CACHE.Party.GetOwnPartyNumber(), "PlayerID", GLOBAL_CACHE.Player.GetAgentID())
    cached_data.HeroAI_vars.shared_memory_handler.set_player_property(GLOBAL_CACHE.Party.GetOwnPartyNumber(), "Energy_Regen", GLOBAL_CACHE.Agent.GetEnergyRegen(GLOBAL_CACHE.Player.GetAgentID()))
    cached_data.HeroAI_vars.shared_memory_handler.set_player_property(GLOBAL_CACHE.Party.GetOwnPartyNumber(), "Energy", GLOBAL_CACHE.Agent.GetEnergy(GLOBAL_CACHE.Player.GetAgentID()))
    cached_data.HeroAI_vars.shared_memory_handler.set_player_property(GLOBAL_CACHE.Party.GetOwnPartyNumber(), "IsActive", True)
    cached_data.HeroAI_vars.shared_memory_handler.set_player_property(GLOBAL_CACHE.Party.GetOwnPartyNumber(), "IsHero", False)

    cached_data.HeroAI_vars.shared_memory_handler.register_buffs(GLOBAL_CACHE.Player.GetAgentID())


def RegisterHeroes(cached_data:CacheData):
    for index, hero in enumerate(GLOBAL_CACHE.Party.GetHeroes()):
        hero_party_number = GLOBAL_CACHE.Party.GetPlayerCount() + index
        agent_id = hero.agent_id
        if hero.owner_player_id == GLOBAL_CACHE.Agent.GetLoginNumber(GLOBAL_CACHE.Player.GetAgentID()): 
            cached_data.HeroAI_vars.shared_memory_handler.set_player_property(hero_party_number, "PlayerID", agent_id)
            cached_data.HeroAI_vars.shared_memory_handler.set_player_property(hero_party_number, "Energy_Regen", GLOBAL_CACHE.Agent.GetEnergyRegen(agent_id))
            cached_data.HeroAI_vars.shared_memory_handler.set_player_property(hero_party_number, "Energy", GLOBAL_CACHE.Agent.GetEnergy(agent_id))
            cached_data.HeroAI_vars.shared_memory_handler.set_player_property(hero_party_number, "IsActive", True)
            cached_data.HeroAI_vars.shared_memory_handler.set_player_property(hero_party_number, "IsHero", True)

            cached_data.HeroAI_vars.shared_memory_handler.register_buffs(agent_id)
        
    pet_id = GLOBAL_CACHE.Party.Pets.GetPetID(GLOBAL_CACHE.Player.GetAgentID())
    if pet_id != 0:
        cached_data.HeroAI_vars.shared_memory_handler.register_buffs(pet_id)

def UpdatePlayers(cached_data:CacheData):
    """Update the player list from shared memory."""
    global MAX_NUM_PLAYERS
    for player in range(MAX_NUM_PLAYERS):
        player_data = cached_data.HeroAI_vars.shared_memory_handler.get_player(player)
        if player_data is None:
            continue

        cached_data.HeroAI_vars.all_player_struct[player].PlayerID = player_data["PlayerID"]
        cached_data.HeroAI_vars.all_player_struct[player].Energy_Regen = player_data["Energy_Regen"]
        cached_data.HeroAI_vars.all_player_struct[player].Energy = player_data["Energy"]
        cached_data.HeroAI_vars.all_player_struct[player].IsActive = player_data["IsActive"]
        cached_data.HeroAI_vars.all_player_struct[player].IsHero = player_data["IsHero"]
        cached_data.HeroAI_vars.all_player_struct[player].IsFlagged = player_data["IsFlagged"]
        cached_data.HeroAI_vars.all_player_struct[player].FlagPosX = player_data["FlagPosX"]
        cached_data.HeroAI_vars.all_player_struct[player].FlagPosY = player_data["FlagPosY"]
        cached_data.HeroAI_vars.all_player_struct[player].FollowAngle = player_data["FollowAngle"]
        cached_data.HeroAI_vars.all_player_struct[player].LastUpdated = player_data["LastUpdated"]