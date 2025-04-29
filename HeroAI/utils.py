from Py4GWCoreLib import *
from .constants import MAX_NUM_PLAYERS
from .targeting import *
from .cache_data import CacheData

import math

def DistanceFromLeader(cached_data:CacheData):
    return Utils.Distance(cached_data.data.party_leader_xy,cached_data.data.player_xy)

def DistanceFromWaypoint(posX,posY):
    return Utils.Distance((posX,posY), Player.GetXY())


""" main configuration helpers """

def CheckForEffect(agent_id, skill_id):
    """this function needs to be expanded as more functionality is added"""
    import HeroAI.shared_memory_manager as shared_memory_manager
    shared_memory_handler = shared_memory_manager.SharedMemoryManager()   
    
    def _IsPartyMember(agent_id):
        for i in range(MAX_NUM_PLAYERS):
            player_data = shared_memory_handler.get_player(i)
            if player_data and player_data["IsActive"] and player_data["PlayerID"] == agent_id:
                return True
            
        allegiance , _ = Agent.GetAllegiance(agent_id)
        if allegiance == Allegiance.SpiritPet.value and not Agent.IsSpawned(agent_id):
            return True
        
        return False

    """
    allegiance , _ = Agent.GetAllegiance(agent_id)
    if allegiance == Allegiance.NpcMinipet.value:
        return True
    """
    result = False
    if _IsPartyMember(agent_id):
        player_buffs = shared_memory_handler.get_agent_buffs(agent_id)
        for buff in player_buffs:
            if buff == skill_id:
                result = True
    else:
        result = Effects.BuffExists(agent_id, skill_id) or Effects.EffectExists(agent_id, skill_id)
    
    return result

def IsHeroFlagged(cached_data:CacheData,index):
    if  index != 0 and index <= cached_data.data.party_hero_count:
        return Party.Heroes.IsHeroFlagged(index)
    else:
        return cached_data.HeroAI_vars.all_player_struct[index-cached_data.data.party_hero_count].IsFlagged and cached_data.HeroAI_vars.all_player_struct[index-cached_data.data.party_hero_count].IsActive


def DrawFlagAll(pos_x, pos_y):
    pos_z = Overlay().FindZ(pos_x, pos_y)

    Overlay().BeginDraw()
    Overlay().DrawLine3D(pos_x, pos_y, pos_z, pos_x, pos_y, pos_z - 150, Utils.RGBToColor(0, 255, 0, 255), 3)
    Overlay().DrawTriangleFilled3D(
        pos_x, pos_y, pos_z - 150,               # Base point
        pos_x, pos_y, pos_z - 120,               # 30 units up
        pos_x - 50, pos_y, pos_z - 135,          # 50 units left, 15 units up
        Utils.RGBToColor(0, 255, 0, 255)
    )

    Overlay().EndDraw()


def DrawHeroFlag(pos_x, pos_y):
    pos_z = Overlay().FindZ(pos_x, pos_y)

    Overlay().BeginDraw()
    Overlay().DrawLine3D(pos_x, pos_y, pos_z, pos_x, pos_y, pos_z - 150, Utils.RGBToColor(0, 255, 0, 255), 3)
    Overlay().DrawTriangleFilled3D(
        pos_x + 25, pos_y, pos_z - 150,          # Right base
        pos_x - 25, pos_y, pos_z - 150,          # Left base
        pos_x, pos_y, pos_z - 100,               # 50 units up
        Utils.RGBToColor(0, 255, 0, 255)
    )
    Overlay().EndDraw()


