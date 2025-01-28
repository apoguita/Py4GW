from Py4GWCoreLib import *

from HeroAI.types import *
from HeroAI.globals import *
from HeroAI.constants import MELEE_RANGE_VALUE, RANGED_RANGE_VALUE, FOLLOW_DISTANCE_OUT_OF_COMBAT
from HeroAI.shared_memory_manager import *
from HeroAI.utils import *
from HeroAI.candidates import *
from HeroAI.players import *
from HeroAI.game_option import *
from HeroAI.windows import *
from HeroAI.targetting import *
from HeroAI.combat import *

MODULE_NAME = "HeroAI"

combat_handler = CombatClass()

def HandleOutOfCombat():
    global combat_handler
    party_number = Party.GetOwnPartyNumber()
    if not IsCombatEnabled(party_number):  # halt operation if combat is disabled
        return False
    if InAggro():
        return False

    combat_handler.HandleCombat(ooc= True)


def HandleCombat():
    global combat_handler
    party_number = Party.GetOwnPartyNumber()
    if not IsCombatEnabled(party_number):  # halt operation if combat is disabled
        return False
    if not InAggro():
        return False

    combat_handler.ResetStayAlertTimer()
    combat_handler.HandleCombat()


looting_item =0
loot_timer = Timer()
loot_timer.Start()

def Loot():
    global looting_item
    global loot_timer
    if InAggro():
        return False
    
    party_number = Party.GetOwnPartyNumber()
    if not IsLootingEnabled(party_number):  # halt operation if looting is disabled
        return False

    if Inventory.GetFreeSlotCount() == 0:
        return False

    item = TargetNearestItem()

    if item == 0:
        looting_item = 0
        return False

    if looting_item != item:
        looting_item = item

    target = Player.GetTargetID()

    if target != looting_item:
        Player.ChangeTarget(looting_item)
        return True

    if loot_timer.HasElapsed(500):
        Keystroke.PressAndRelease(Key.Space.value)
        loot_timer.Reset()
        #Player.Interact(item)

    return True



def Follow():
    global HeroAI_vars
    global MELEE_RANGE_VALUE, RANGED_RANGE_VALUE, FOLLOW_DISTANCE_ON_COMBAT
    global oldAngle, Angle_changed

    leader_id = Party.GetPartyLeaderID()
    if leader_id == Player.GetAgentID():  # halt operation if player is leader
        return False
    party_number = Party.GetOwnPartyNumber()
    if not IsFollowingEnabled(party_number): # halt operation following is disabled
        return False

    follow_x = 0.0
    follow_y = 0.0
    follow_angle = -1.0

    if HeroAI_vars.all_player_struct[party_number].IsFlagged: #my own flag
        follow_x = HeroAI_vars.all_player_struct[party_number].FlagPosX
        follow_y = HeroAI_vars.all_player_struct[party_number].FlagPosY
        follow_angle = HeroAI_vars.all_player_struct[party_number].FollowAngle
    elif HeroAI_vars.all_player_struct[0].IsFlagged:  # leader's flag
        follow_x = HeroAI_vars.all_player_struct[0].FlagPosX
        follow_y = HeroAI_vars.all_player_struct[0].FlagPosY
        follow_angle = HeroAI_vars.all_player_struct[0].FollowAngle
    else:  # follow leader
        follow_x, follow_y = Agent.GetXY(leader_id)
        follow_angle = Agent.GetRotationAngle(leader_id)

    if Agent.IsMelee(Player.GetAgentID()):
        FOLLOW_DISTANCE_ON_COMBAT = MELEE_RANGE_VALUE
    else:
        FOLLOW_DISTANCE_ON_COMBAT = RANGED_RANGE_VALUE

    if InAggro():
        follow_distance = FOLLOW_DISTANCE_ON_COMBAT
    else:
        follow_distance = FOLLOW_DISTANCE_OUT_OF_COMBAT

    if (oldAngle != follow_angle) and not Angle_changed:
        oldAngle = follow_angle;
        Angle_changed = True

    angle_changed_pass = False
    if Angle_changed and not InAggro():
        angle_changed_pass = True

    if DistanceFromWaypoint(follow_x, follow_y) <= follow_distance and not angle_changed_pass:
        return False
    
    hero_grid_pos = party_number + Party.GetHeroCount() + Party.GetHenchmanCount()
    angle_on_hero_grid = follow_angle + DegToRad(hero_formation[hero_grid_pos])

    #if IsPointValid(follow_x, follow_y):
    #   return False

    xx = Range.Touch.value * math.cos(angle_on_hero_grid) + follow_x
    yy = Range.Touch.value * math.sin(angle_on_hero_grid) + follow_y

    Angle_changed = False
    Player.Move(xx, yy)
    return True


game_throttle_timer = Timer()
game_throttle_timer.Start()

def UpdateStatus():
    global game_throttle_timer
    global combat_handler

    throttle_allow = game_throttle_timer.HasElapsed(50)
    if throttle_allow:
        game_throttle_timer.Reset()

    if throttle_allow:
        RegisterCandidate() 
        UpdateCandidates()           
        ProcessCandidateCommands()   
        RegisterPlayer()   
        RegisterHeroes()
        UpdatePlayers()      
        UpdateGameOptions()   

    if Map.IsInCinematic():  # halt operation during cinematic
        return

    DrawMainWindow()
    DrawControlPanelWindow()
    DrawMultiboxTools()

    if not Map.IsExplorable():  # halt operation outside explorable areas
        return
    
    DrawFlags()
    
    if not Agent.IsAlive(Player.GetAgentID()): # halt operation if player is dead
        return  

    if DistanceFromLeader() >= Range.SafeCompass.value:  # halt operation if player is too far from leader
        return

    if Agent.IsKnockedDown(Player.GetAgentID()): # halt operation if player is knocked down
        return


    if throttle_allow:
        if combat_handler.InCastingRoutine():
            return

        combat_handler.PrioritizeSkills()

        if HandleOutOfCombat():
            return
    
        if Agent.IsMoving(Player.GetAgentID()):  # halt operation if player is moving
            return

        if Loot():
            return
        
        if Follow():
            return

        if HandleCombat():
           return

def TrueFalseColor(condition):
    if condition:
        return RGBToNormal(0, 255, 0, 255)
    else:
        return RGBToNormal(255, 0, 0, 255)
    
def configure():
    pass


def main():
    global combat_handler
    try:
        if Map.IsMapReady() and Party.IsPartyLoaded():
            UpdateStatus()

    except ImportError as e:
        Py4GW.Console.Log(MODULE_NAME, f"ImportError encountered: {str(e)}", Py4GW.Console.MessageType.Error)
        Py4GW.Console.Log(MODULE_NAME, f"Stack trace: {traceback.format_exc()}", Py4GW.Console.MessageType.Error)
    except ValueError as e:
        Py4GW.Console.Log(MODULE_NAME, f"ValueError encountered: {str(e)}", Py4GW.Console.MessageType.Error)
        Py4GW.Console.Log(MODULE_NAME, f"Stack trace: {traceback.format_exc()}", Py4GW.Console.MessageType.Error)
    except TypeError as e:
        Py4GW.Console.Log(MODULE_NAME, f"TypeError encountered: {str(e)}", Py4GW.Console.MessageType.Error)
        Py4GW.Console.Log(MODULE_NAME, f"Stack trace: {traceback.format_exc()}", Py4GW.Console.MessageType.Error)
    except Exception as e:
        # Catch-all for any other unexpected exceptions
        Py4GW.Console.Log(MODULE_NAME, f"Unexpected error encountered: {str(e)}", Py4GW.Console.MessageType.Error)
        Py4GW.Console.Log(MODULE_NAME, f"Stack trace: {traceback.format_exc()}", Py4GW.Console.MessageType.Error)
    finally:
        pass
        

if __name__ == "__main__":
    main()

