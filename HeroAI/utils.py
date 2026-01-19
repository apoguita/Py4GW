from Py4GWCoreLib import GLOBAL_CACHE, Allegiance, Overlay, Map, Agent, Player
from Py4GWCoreLib.GlobalCache.SharedMemory import AccountData
from .constants import MAX_NUM_PLAYERS
from .targeting import *
from .cache_data import CacheData


def SameMapAsAccount(account : AccountData):
    own_map_id = Map.GetMapID()
    own_region = Map.GetRegion()[0]
    own_district = Map.GetDistrict()
    own_language = Map.GetLanguage()[0]
    return own_map_id == account.MapID and own_region == account.MapRegion and own_district == account.MapDistrict and own_language == account.MapLanguage

def DistanceFromLeader(cached_data:CacheData):
    return Utils.Distance(Agent.GetXY(GLOBAL_CACHE.Party.GetPartyLeaderID()),Agent.GetXY(Player.GetAgentID()))

def DistanceFromWaypoint(posX,posY):
    distance = Utils.Distance((posX,posY), Player.GetXY())
    return distance if distance > 200 else 0


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
        result = GLOBAL_CACHE.Effects.BuffExists(agent_id, skill_id) or GLOBAL_CACHE.Effects.EffectExists(agent_id, skill_id)
    
    return result

def IsHeroFlagged(cached_data:CacheData,index):
    if  index != 0 and index <= GLOBAL_CACHE.Party.GetHeroCount():
        return GLOBAL_CACHE.Party.Heroes.IsHeroFlagged(index)
    else:
        return cached_data.HeroAI_vars.all_player_struct[index-GLOBAL_CACHE.Party.GetHeroCount()].IsFlagged and cached_data.HeroAI_vars.all_player_struct[index-GLOBAL_CACHE.Party.GetHeroCount()].IsActive


def DrawFlagAll(pos_x, pos_y):
    overlay = Overlay()
    pos_z = overlay.FindZ(pos_x, pos_y)

    overlay.BeginDraw()
    overlay.DrawLine3D(pos_x, pos_y, pos_z, pos_x, pos_y, pos_z - 150, Utils.RGBToColor(0, 255, 0, 255), 3)    
    overlay.DrawTriangleFilled3D(
        pos_x, pos_y, pos_z - 150,               # Base point
        pos_x, pos_y, pos_z - 120,               # 30 units up
        pos_x - 50, pos_y, pos_z - 135,          # 50 units left, 15 units up
        Utils.RGBToColor(0, 255, 0, 255)
    )

    overlay.EndDraw()

def DrawHeroFlag(pos_x, pos_y):
    overlay = Overlay()
    
    pos_z = overlay.FindZ(pos_x, pos_y)

    overlay.BeginDraw()
    overlay.DrawLine3D(pos_x, pos_y, pos_z, pos_x, pos_y, pos_z - 150, Utils.RGBToColor(0, 255, 0, 255), 3)
    overlay.DrawTriangleFilled3D(
        pos_x + 25, pos_y, pos_z - 150,          # Right base
        pos_x - 25, pos_y, pos_z - 150,          # Left base
        pos_x, pos_y, pos_z - 100,               # 50 units up
        Utils.RGBToColor(0, 255, 0, 255)
    )
        
    overlay.EndDraw()