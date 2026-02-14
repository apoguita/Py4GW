from typing import Optional
from Py4GWCoreLib import GLOBAL_CACHE, Allegiance, Overlay, Map, Agent
from Py4GWCoreLib.GlobalCache.SharedMemory import AccountData
from .constants import MAX_NUM_PLAYERS
from .targeting import *
from .cache_data import CacheData


def SameMapAsAccount(account : AccountData):
    if not Map.IsMapReady():
        return False
    
    own_map_id = Map.GetMapID()
    own_region = Map.GetRegion()[0]
    own_district = Map.GetDistrict()
    own_language = Map.GetLanguage()[0]
    return own_map_id == account.MapID and own_region == account.MapRegion and own_district == account.MapDistrict and own_language == account.MapLanguage

def SameMapOrPartyAsAccount(account : AccountData):
    if not Map.IsMapReady():
        return False
    
    own_map_id = Map.GetMapID()
    own_region = Map.GetRegion()[0]
    own_district = Map.GetDistrict()
    own_language = Map.GetLanguage()[0]
    party_members = [GLOBAL_CACHE.Party.Players.GetAgentIDByLoginNumber(party_member.login_number) for party_member in GLOBAL_CACHE.Party.GetPlayers()]
    
    same_map = own_map_id == account.MapID and own_district == account.MapDistrict and own_language == account.MapLanguage
    
    if same_map and account.PlayerID in party_members and account.PartyID == GLOBAL_CACHE.Party.GetPartyID():
        return True
    
    return same_map and own_region == account.MapRegion

def DistanceFromLeader():
    return Utils.Distance(Agent.GetXY(GLOBAL_CACHE.Party.GetPartyLeaderID()),Agent.GetXY(Player.GetAgentID()))

def DistanceFromWaypoint(posX, posY):
    distance = Utils.Distance((posX, posY), Player.GetXY())
    return distance if distance > 200 else 0


""" main configuration helpers """

def IsPartyMember(agent_id, cached_data : Optional[CacheData] = None) -> bool:
    cached_data = cached_data if cached_data is not None else CacheData()
                
    for acc in cached_data.party:
        if acc.IsSlotActive and acc.PlayerID == agent_id and SameMapOrPartyAsAccount(acc) and acc.PartyID == cached_data.party.party_id:
            return True
        
    allegiance , _ = Agent.GetAllegiance(agent_id)
    if (allegiance == Allegiance.SpiritPet.value and 
        not Agent.IsSpawned(agent_id)):
        return True
    
    return False

def GetConditions(agent_id, cached_data : Optional[CacheData] = None) -> list[int]:
    CONDITIONS = [
        485, # Dazed
        2077, # Cracked Armor
        479, # Blind
        478, # Bleeding
        480, # Burning
        484, # Poison
        483, # Disease
        486, # Weakness
        482, # Deep Wound
        481, # Crippled        
    ]
    cached_data = cached_data if cached_data is not None else CacheData()
                
    for acc in cached_data.party:
        if acc.IsSlotActive and acc.PlayerID == agent_id and SameMapOrPartyAsAccount(acc) and acc.PartyID == cached_data.party.party_id:
            return [buff.SkillId for buff in acc.PlayerBuffs if buff.SkillId in CONDITIONS]
        
    return []

def GetEnergyValues(agent_id, cached_data : Optional[CacheData] = None):
    cached_data = cached_data if cached_data is not None else CacheData()
                
    for acc in cached_data.party:
        if acc.IsSlotActive and acc.PlayerID == agent_id and SameMapOrPartyAsAccount(acc) and acc.PartyID == cached_data.party.party_id:
            return acc.PlayerEnergy
        
    return 1.0 #default return full energy to prevent issues

def CheckForEffect(agent_id, skill_id, cached_data : Optional[CacheData] = None) -> bool:
    """
    check if the given agent has the effect or buff with the given skill id
    """    
    cached_data = cached_data if cached_data is not None else CacheData()
    
    for acc in cached_data.party:
        if acc.IsSlotActive and acc.PlayerID == agent_id and SameMapOrPartyAsAccount(acc) and acc.PartyID == cached_data.party.party_id:
            return any(buff.SkillId == skill_id for buff in acc.PlayerBuffs)        

    allegiance , _ = Agent.GetAllegiance(agent_id)
    if allegiance == Allegiance.SpiritPet.value and not Agent.IsSpawned(agent_id):
        ## spirit pets do not have buffs in shared memory, so we check effects only
        return True 
    
    return GLOBAL_CACHE.Effects.HasEffect(agent_id, skill_id)

def GetEffectAndBuffIds(agent_id, cached_data : Optional[CacheData] = None) -> list[int]:
    """
    get all effect and buff skill ids for the given agent
    """
    cached_data = cached_data if cached_data is not None else CacheData()
    
    for acc in cached_data.party:
        if acc.IsSlotActive and acc.PlayerID == agent_id and SameMapOrPartyAsAccount(acc) and acc.PartyID == cached_data.party.party_id:
            return [buff.SkillId for buff in acc.PlayerBuffs]
    
    return [effect.skill_id for effect in GLOBAL_CACHE.Effects.GetBuffs(agent_id) + GLOBAL_CACHE.Effects.GetEffects(agent_id)]


def IsHeroFlagged(index):    
    if  index != 0 and index <= GLOBAL_CACHE.Party.GetHeroCount():
        return GLOBAL_CACHE.Party.Heroes.IsHeroFlagged(index)
    else:
        acc = GLOBAL_CACHE.ShMem.GetGerHeroAIOptionsByPartyNumber(index)
        return acc is not None and acc.IsFlagged 


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