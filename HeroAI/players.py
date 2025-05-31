from Py4GWCoreLib import GLOBAL_CACHE
from .constants import MAX_NUM_PLAYERS
from .cache_data import CacheData


def RegisterPlayer(cached_data:CacheData):
    """Register the current player to the shared memory."""
    if cached_data.data.own_party_number == -1:
        return False

    cached_data.HeroAI_vars.shared_memory_handler.set_player_property(cached_data.data.own_party_number, "PlayerID", cached_data.data.player_agent_id)
    cached_data.HeroAI_vars.shared_memory_handler.set_player_property(cached_data.data.own_party_number, "Energy_Regen", cached_data.data.player_energy_regen)
    cached_data.HeroAI_vars.shared_memory_handler.set_player_property(cached_data.data.own_party_number, "Energy", cached_data.data.player_energy)
    cached_data.HeroAI_vars.shared_memory_handler.set_player_property(cached_data.data.own_party_number, "IsActive", True)
    cached_data.HeroAI_vars.shared_memory_handler.set_player_property(cached_data.data.own_party_number, "IsHero", False)

    cached_data.HeroAI_vars.shared_memory_handler.register_buffs(cached_data.data.player_agent_id)


def RegisterHeroes(cached_data:CacheData):
    for index, hero in enumerate(cached_data.data.heroes):
        hero_party_number =cached_data.data.party_player_count + index
        agent_id = hero.agent_id
        if hero.owner_player_id == cached_data.data.player_login_number: 
            cached_data.HeroAI_vars.shared_memory_handler.set_player_property(hero_party_number, "PlayerID", agent_id)
            cached_data.HeroAI_vars.shared_memory_handler.set_player_property(hero_party_number, "Energy_Regen", GLOBAL_CACHE.Agent.GetEnergyRegen(agent_id))
            cached_data.HeroAI_vars.shared_memory_handler.set_player_property(hero_party_number, "Energy", GLOBAL_CACHE.Agent.GetEnergy(agent_id))
            cached_data.HeroAI_vars.shared_memory_handler.set_player_property(hero_party_number, "IsActive", True)
            cached_data.HeroAI_vars.shared_memory_handler.set_player_property(hero_party_number, "IsHero", True)

            cached_data.HeroAI_vars.shared_memory_handler.register_buffs(agent_id)
        
    pet_id = GLOBAL_CACHE.Party.Pets.GetPetID(cached_data.data.player_agent_id)
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
