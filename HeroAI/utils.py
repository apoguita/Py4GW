from Py4GWCoreLib import *
from .constants import MAX_NUM_PLAYERS
from .globals import overlay
from .targetting import *

import math

def DistanceFromLeader(cached_data):
    return Utils.Distance(cached_data.data.party_leader_xy,cached_data.data.player_xy)

def DistanceFromWaypoint(posX,posY):
    return Utils.Distance((posX,posY), Player.GetXY())


""" main configuration helpers """

def IsFollowingEnabled(all_game_option_struct,index):
    return all_game_option_struct[index].Following

def IsAvoidanceEnabled(all_game_option_struct,index):
    return all_game_option_struct[index].Avoidance

def IsLootingEnabled(all_game_option_struct,index):
    return all_game_option_struct[index].Looting

def IsTargetingEnabled(all_game_option_struct,index):
    return all_game_option_struct[index].Targetting

def IsCombatEnabled(all_game_option_struct,index):
    return all_game_option_struct[index].Combat

def IsSkillEnabled(all_game_option_struct,index,slot):
    return all_game_option_struct[index].Skills[slot].Active


def CheckForEffect(agent_id, skill_id):
    """this function needs to be expanded as more functionality is added"""
    from .globals import HeroAI_varsClass  
    shared_memory_handler = HeroAI_varsClass().shared_memory_handler
    def IsPartyMember(agent_id):

        for i in range(MAX_NUM_PLAYERS):
            player_data = shared_memory_handler.get_player(i)
            if player_data["IsActive"] and player_data["PlayerID"] == agent_id:
                return True
        
        return False

    result = False
    if IsPartyMember(agent_id):
        player_buffs = shared_memory_handler.get_agent_buffs(agent_id)
        for buff in player_buffs:
            #Py4GW.Console.Log("HasEffect-player_buff", f"IsPartyMember: {self.IsPartyMember(agent_id)} agent ID: {agent_id}, effect {skill_id} buff {buff}", Py4GW.Console.MessageType.Info)
            if buff == skill_id:
                result = True
    else:
        result = Effects.BuffExists(agent_id, skill_id) or Effects.EffectExists(agent_id, skill_id)
    
    return result

def GetEnergyValues(agent_id):
    return 1.0
    from .globals import HeroAI_varsClass
    shared_memory_handler = HeroAI_varsClass().shared_memory_handler

    for i in range(MAX_NUM_PLAYERS):
        player_data = shared_memory_handler.get_player(i)
        if player_data["IsActive"] and player_data["PlayerID"] == agent_id:
            return player_data["Energy"]
    return 1.0 #default return full energy to prevent issues


def InAggro(enemy_array, aggro_range = Range.Earshot.value):
    distance = aggro_range
    enemy_array = AgentArray.Filter.ByCondition(enemy_array, lambda agent_id: Utils.Distance(Player.GetXY(), Agent.GetXY(agent_id)) <= distance)
    enemy_array = AgentArray.Filter.ByCondition(enemy_array, lambda agent_id: Agent.IsAlive(agent_id))
    enemy_array = AgentArray.Filter.ByCondition(enemy_array, lambda agent_id: Player.GetAgentID() != agent_id)
    enemy_array = AgentArray.Sort.ByDistance(enemy_array, Player.GetXY())
    if len(enemy_array) > 0:
        return True
    return False


def IsHeroFlagged(cached_data,index):
    if  index != 0 and index <= cached_data.data.party_hero_count:
        return Party.Heroes.IsHeroFlagged(index)
    else:
        return cached_data.HeroAI_vars.all_player_struct[index-cached_data.data.party_hero_count].IsFlagged and cached_data.HeroAI_vars.all_player_struct[index-cached_data.data.party_hero_count].IsActive


def DrawFlagAll(pos_x, pos_y):
    global overlay

    pos_z = overlay.FindZ(pos_x, pos_y)

    overlay.BeginDraw()
    overlay.DrawLine3D(pos_x, pos_y, pos_z, pos_x, pos_y, pos_z - 150, Utils.RGBToColor(0, 255, 0, 255), 3)
    overlay.DrawFilledTriangle3D(
        pos_x, pos_y, pos_z - 150,               # Base point
        pos_x, pos_y, pos_z - 120,               # 30 units up
        pos_x - 50, pos_y, pos_z - 135,          # 50 units left, 15 units up
        Utils.RGBToColor(0, 255, 0, 255)
    )

    overlay.EndDraw()


def DrawHeroFlag(pos_x, pos_y):
    global overlay

    pos_z = overlay.FindZ(pos_x, pos_y)

    overlay.BeginDraw()
    overlay.DrawLine3D(pos_x, pos_y, pos_z, pos_x, pos_y, pos_z - 150, Utils.RGBToColor(0, 255, 0, 255), 3)
    overlay.DrawFilledTriangle3D(
        pos_x + 25, pos_y, pos_z - 150,          # Right base
        pos_x - 25, pos_y, pos_z - 150,          # Left base
        pos_x, pos_y, pos_z - 100,               # 50 units up
        Utils.RGBToColor(0, 255, 0, 255)
    )
    overlay.EndDraw()


