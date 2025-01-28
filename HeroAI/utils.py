from Py4GWCoreLib import *
from .constants import MAX_NUM_PLAYERS
from .globals import HeroAI_vars, overlay
from .targetting import *

import math

def DistanceFromLeader():
    return Utils.Distance(Agent.GetXY(Party.GetPartyLeaderID()),Player.GetXY())

def DistanceFromWaypoint(posX,posY):
    return Utils.Distance((posX,posY), Player.GetXY())


def DegToRad(degrees):
    return degrees * (math.pi / 180)


def RadToDeg(radians):
    return radians * (180 / math.pi)


def RGBToColor(r, g, b, a):
    return (a << 24) | (b << 16) | (g << 8) | r


def RGBToNormal(r, g, b, a):
    return r / 255.0, g / 255.0, b / 255.0, a / 255.0
    

""" main configuration helpers """

def IsFollowingEnabled(index):
    global HeroAI_vars
    return HeroAI_vars.all_game_option_struct[index].Following

def IsAvoidanceEnabled(index):
    global HeroAI_vars
    return HeroAI_vars.all_game_option_struct[index].Avoidance

def IsLootingEnabled(index):
    global HeroAI_vars
    return HeroAI_vars.all_game_option_struct[index].Looting

def IsTargetingEnabled(index):
    global HeroAI_vars
    return HeroAI_vars.all_game_option_struct[index].Targetting

def IsCombatEnabled(index):
    global HeroAI_vars
    return HeroAI_vars.all_game_option_struct[index].Combat


def CheckForEffect(agent_id, skill_id):
    """this function needs to be expanded as more functionality is added"""
    from .globals import HeroAI_vars

    def IsPartyMember(agent_id):
        from .globals import HeroAI_vars

        for i in range(MAX_NUM_PLAYERS):
            player_data = HeroAI_vars.shared_memory_handler.get_player(i)
            if player_data["IsActive"] and player_data["PlayerID"] == agent_id:
                return True
        
        return False

    result = False
    if IsPartyMember(agent_id):
        player_buffs = HeroAI_vars.shared_memory_handler.get_agent_buffs(agent_id)
        for buff in player_buffs:
            #Py4GW.Console.Log("HasEffect-player_buff", f"IsPartyMember: {self.IsPartyMember(agent_id)} agent ID: {agent_id}, effect {skill_id} buff {buff}", Py4GW.Console.MessageType.Info)
            if buff == skill_id:
                result = True
    else:
        result = Effects.BuffExists(agent_id, skill_id) or Effects.EffectExists(agent_id, skill_id)
    
    return result

def GetEnergyValues(agent_id):
    global HeroAI_vars
    for i in range(MAX_NUM_PLAYERS):
        if HeroAI_vars.all_player_struct[i].IsActive and HeroAI_vars.all_player_struct[i].PlayerID == agent_id:
            return HeroAI_vars.all_player_struct[i].Energy #, HeroAI_vars.all_player_struct[i].Energy_Regen
    return 1.0 #default return full energy to prevent issues


def InAggro(aggro_range = Range.Earshot.value):
    enemy_array = AgentArray.GetEnemyArray()
    distance = aggro_range
    enemy_array = AgentArray.Filter.ByCondition(enemy_array, lambda agent_id: Utils.Distance(Player.GetXY(), Agent.GetXY(agent_id)) <= distance)
    enemy_array = AgentArray.Filter.ByCondition(enemy_array, lambda agent_id: Agent.IsAlive(agent_id))
    enemy_array = AgentArray.Filter.ByCondition(enemy_array, lambda agent_id: Player.GetAgentID() != agent_id)
    enemy_array = AgentArray.Sort.ByDistance(enemy_array, Player.GetXY())
    if len(enemy_array) > 0:
        return True
    return False


def IsHeroFlagged(index):
    global HeroAI_vars
    if  index != 0 and index <= Party.GetHeroCount():
        return Party.Heroes.IsHeroFlagged(index)
    else:
        return HeroAI_vars.all_player_struct[index-Party.GetHeroCount()].IsFlagged and HeroAI_vars.all_player_struct[index-Party.GetHeroCount()].IsActive


def DrawFlagAll(pos_x, pos_y):
    global overlay

    pos_z = overlay.FindZ(pos_x, pos_y)

    overlay.BeginDraw()
    overlay.DrawLine3D(pos_x, pos_y, pos_z, pos_x, pos_y, pos_z - 150, RGBToColor(0, 255, 0, 255), 3)
    overlay.DrawFilledTriangle3D(
        pos_x, pos_y, pos_z - 150,               # Base point
        pos_x, pos_y, pos_z - 120,               # 30 units up
        pos_x - 50, pos_y, pos_z - 135,          # 50 units left, 15 units up
        RGBToColor(0, 255, 0, 255)
    )

    overlay.EndDraw()


def DrawHeroFlag(pos_x, pos_y):
    global overlay

    pos_z = overlay.FindZ(pos_x, pos_y)

    overlay.BeginDraw()
    overlay.DrawLine3D(pos_x, pos_y, pos_z, pos_x, pos_y, pos_z - 150, RGBToColor(0, 255, 0, 255), 3)
    overlay.DrawFilledTriangle3D(
        pos_x + 25, pos_y, pos_z - 150,          # Right base
        pos_x - 25, pos_y, pos_z - 150,          # Left base
        pos_x, pos_y, pos_z - 100,               # 50 units up
        RGBToColor(0, 255, 0, 255)
    )
    overlay.EndDraw()


