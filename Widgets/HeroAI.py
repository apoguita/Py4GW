#region Imports
import math
import traceback
import Py4GW

MODULE_NAME = "HeroAI"

from Py4GWCoreLib.Map import Map

from HeroAI.cache_data import CacheData
from HeroAI.constants import (FOLLOW_DISTANCE_OUT_OF_COMBAT, MELEE_RANGE_VALUE, RANGED_RANGE_VALUE)
from HeroAI.game_option import UpdateGameOptions
from HeroAI.globals import hero_formation
from HeroAI.players import (RegisterHeroes, RegisterPlayer, UpdatePlayers)
from HeroAI.utils import (DistanceFromWaypoint)
from HeroAI.windows import (HeroAI_FloatingWindows ,HeroAI_Windows,)
from HeroAI.ui import (draw_configure_window, draw_skip_cutscene_overlay)
from Py4GWCoreLib import (GLOBAL_CACHE, Agent, ActionQueueManager, LootConfig,
                          Range, Routines, ThrottledTimer, SharedCommandType, Utils)

#region GLOBALS
FOLLOW_COMBAT_DISTANCE = 25.0  # if body blocked, we get close enough.
LEADER_FLAG_TOUCH_RANGE_THRESHOLD_VALUE = Range.Touch.value * 1.1
LOOT_THROTTLE_CHECK = ThrottledTimer(250)

cached_data = CacheData()
map_quads : list[Map.Pathing.Quad] = []

#region Combat
def HandleOutOfCombat(cached_data: CacheData):
    if not cached_data.data.is_combat_enabled:  # halt operation if combat is disabled
        return False
    if cached_data.data.in_aggro:
        return False

    return cached_data.combat_handler.HandleCombat(ooc=True)
def HandleCombatFlagging(cached_data: CacheData):
    # Suspends all activity until HeroAI has made it to the flagged position
    # Still goes into combat as long as its within the combat follow range value of the expected flag
    party_number = GLOBAL_CACHE.Party.GetOwnPartyNumber()
    all_player_struct = cached_data.HeroAI_vars.all_player_struct
    if all_player_struct[party_number].IsFlagged:
        own_follow_x = all_player_struct[party_number].FlagPosX
        own_follow_y = all_player_struct[party_number].FlagPosY
        own_flag_coords = (own_follow_x, own_follow_y)
        if (
            Utils.Distance(own_flag_coords, Agent.GetXY(GLOBAL_CACHE.Player.GetAgentID()))
            >= FOLLOW_COMBAT_DISTANCE
        ):
            return True  # Forces a reset on autoattack timer
    elif all_player_struct[0].IsFlagged:
        leader_follow_x = all_player_struct[0].FlagPosX
        leader_follow_y = all_player_struct[0].FlagPosY
        leader_flag_coords = (leader_follow_x, leader_follow_y)
        if (
            Utils.Distance(leader_flag_coords, Agent.GetXY(GLOBAL_CACHE.Player.GetAgentID()))
            >= LEADER_FLAG_TOUCH_RANGE_THRESHOLD_VALUE
        ):
            return True  # Forces a reset on autoattack timer
    return False


def HandleCombat(cached_data: CacheData):
    if not cached_data.data.is_combat_enabled:  # halt operation if combat is disabled
        return False
    if not cached_data.data.in_aggro:
        return False

    combat_flagging_handled = HandleCombatFlagging(cached_data)
    if combat_flagging_handled:
        return combat_flagging_handled
    return cached_data.combat_handler.HandleCombat(ooc=False)

def HandleAutoAttack(cached_data: CacheData) -> bool:
    target_id = GLOBAL_CACHE.Player.GetTargetID()
    _, target_aliegance = Agent.GetAllegiance(target_id)

    if target_id == 0 or Agent.IsDead(target_id) or (target_aliegance != "Enemy"):
        if (
            cached_data.data.is_combat_enabled
            and (not Agent.IsAttacking(GLOBAL_CACHE.Player.GetAgentID()))
            and (not Agent.IsCasting(GLOBAL_CACHE.Player.GetAgentID()))
            and (not Agent.IsMoving(GLOBAL_CACHE.Player.GetAgentID()))
        ):
            cached_data.combat_handler.ChooseTarget()
            cached_data.auto_attack_timer.Reset()
            return True

    # auto attack
    if cached_data.auto_attack_timer.HasElapsed(cached_data.auto_attack_time) and cached_data.data.weapon_type != 0:
        if (
            cached_data.data.is_combat_enabled
            and (not Agent.IsAttacking(GLOBAL_CACHE.Player.GetAgentID()))
            and (not Agent.IsCasting(GLOBAL_CACHE.Player.GetAgentID()))
            and (not Agent.IsMoving(GLOBAL_CACHE.Player.GetAgentID()))
        ):
            cached_data.combat_handler.ChooseTarget()
        cached_data.auto_attack_timer.Reset()
        cached_data.combat_handler.ResetSkillPointer()
        return True
    return False


cached_data.in_looting_routine = False

#region Looting
def LootingRoutineActive():
    account_email = GLOBAL_CACHE.Player.GetAccountEmail()
    index, message = GLOBAL_CACHE.ShMem.PreviewNextMessage(account_email)

    if index == -1 or message is None:
        return False

    if message.Command != SharedCommandType.PickUpLoot:
        return False
    return True


def Loot(cached_data: CacheData):
    global LOOT_THROTTLE_CHECK

    if not cached_data.data.is_looting_enabled:
        return False

    if cached_data.data.in_aggro:
        return False

    if LootingRoutineActive():
        return True

    if not LOOT_THROTTLE_CHECK.IsExpired():
        cached_data.in_looting_routine = True
        return True

    # Stop if inventory is full
    if GLOBAL_CACHE.Inventory.GetFreeSlotCount() < 1:
        return False

    # Build the loot array based on filtering rules
    loot_array = LootConfig().GetfilteredLootArray(
        Range.Earshot.value,
        multibox_loot=True,
        allow_unasigned_loot=False,
    )
    if len(loot_array) == 0:
        cached_data.in_looting_routine = False
        return False

    cached_data.in_looting_routine = True
    self_account = GLOBAL_CACHE.ShMem.GetAccountDataFromEmail(cached_data.account_email)
    if not self_account:
        cached_data.in_looting_routine = False
        return False

    # === Throttled Send ===
    if LOOT_THROTTLE_CHECK.IsExpired():
        GLOBAL_CACHE.ShMem.SendMessage(
            self_account.AccountEmail,
            self_account.AccountEmail,
            SharedCommandType.PickUpLoot,
            (0, 0, 0, 0),
        )
        LOOT_THROTTLE_CHECK.Reset()

    return True


following_flag = False


#region Following
def Follow(cached_data: CacheData):
    global FOLLOW_DISTANCE_ON_COMBAT, following_flag, map_quads
    
    if not cached_data.follow_throttle_timer.IsExpired():
        return False
    
    if not map_quads:
        map_quads = Map.Pathing.GetMapQuads()

    if GLOBAL_CACHE.Player.GetAgentID() == GLOBAL_CACHE.Party.GetPartyLeaderID():
        cached_data.follow_throttle_timer.Reset()
        return False

    party_number = GLOBAL_CACHE.Party.GetOwnPartyNumber()
    if not cached_data.data.is_following_enabled:  # halt operation if following is disabled
        return False

    follow_x = 0.0
    follow_y = 0.0
    follow_angle = -1.0

    all_player_struct = cached_data.HeroAI_vars.all_player_struct
    if all_player_struct[party_number].IsFlagged:  # my own flag
        follow_x = all_player_struct[party_number].FlagPosX
        follow_y = all_player_struct[party_number].FlagPosY
        follow_angle = all_player_struct[party_number].FollowAngle
        following_flag = True
    elif all_player_struct[0].IsFlagged:  # leader's flag
        follow_x = all_player_struct[0].FlagPosX
        follow_y = all_player_struct[0].FlagPosY
        follow_angle = all_player_struct[0].FollowAngle
        following_flag = False
    else:  # follow leader
        following_flag = False
        follow_x, follow_y = Agent.GetXY(GLOBAL_CACHE.Party.GetPartyLeaderID())
        follow_angle = Agent.GetRotationAngle(GLOBAL_CACHE.Party.GetPartyLeaderID())

    if following_flag:
        FOLLOW_DISTANCE_ON_COMBAT = FOLLOW_COMBAT_DISTANCE
    elif Agent.IsMelee(GLOBAL_CACHE.Player.GetAgentID()):
        FOLLOW_DISTANCE_ON_COMBAT = MELEE_RANGE_VALUE
    else:
        FOLLOW_DISTANCE_ON_COMBAT = RANGED_RANGE_VALUE

    if cached_data.data.in_aggro:
        follow_distance = FOLLOW_DISTANCE_ON_COMBAT
    else:
        follow_distance = FOLLOW_DISTANCE_OUT_OF_COMBAT if not following_flag else 0.0

    angle_changed_pass = False
    if cached_data.data.angle_changed and (not cached_data.data.in_aggro):
        angle_changed_pass = True

    close_distance_check = DistanceFromWaypoint(follow_x, follow_y) <= follow_distance

    if not angle_changed_pass and close_distance_check:
        return False

    hero_grid_pos = party_number + GLOBAL_CACHE.Party.GetHeroCount() + GLOBAL_CACHE.Party.GetHenchmanCount()
    angle_on_hero_grid = follow_angle + Utils.DegToRad(hero_formation[hero_grid_pos])

    def is_position_on_map(x, y) -> bool:
        if not HeroAI_FloatingWindows.settings.ConfirmFollowPoint:
            return True
        
        for quad in map_quads:    
            if Map.Pathing._point_in_quad(x, y, quad):
                return True
            
        return False
    
    if following_flag:
        xx = follow_x
        yy = follow_y
    else:
        xx = Range.Touch.value * math.cos(angle_on_hero_grid) + follow_x
        yy = Range.Touch.value * math.sin(angle_on_hero_grid) + follow_y
            
        if not is_position_on_map(xx, yy):
            ## fallback to direct follow if calculated point is off-map to avoid getting stuck or falling behind
            xx = follow_x
            yy = follow_y
    
    cached_data.data.angle_changed = False
    ActionQueueManager().ResetQueue("ACTION")
    GLOBAL_CACHE.Player.Move(xx, yy)
    return True


def register_data(cached_data: CacheData):
    RegisterPlayer(cached_data)
    RegisterHeroes(cached_data)
    UpdatePlayers(cached_data)
    UpdateGameOptions(cached_data)
    cached_data.UpdateGameOptions()

def handle_UI (cached_data: CacheData):      
    if not cached_data.ui_state_data.show_classic_controls:   
        HeroAI_FloatingWindows.DrawEmbeddedWindow(cached_data)
    else:
        HeroAI_Windows.DrawControlPanelWindow(cached_data)           
        HeroAI_Windows.DrawFollowerUI(cached_data)
        
    HeroAI_FloatingWindows.show_ui(cached_data) 
   
def initialize(cached_data: CacheData) -> bool:
    if Map.IsMapReady() and GLOBAL_CACHE.Party.IsPartyLoaded():
    
        register_data(cached_data)

        if HeroAI_FloatingWindows.disable_main_automation(cached_data):
            return False
        
        handle_UI (cached_data)
        
        if not Map.IsExplorable():  # halt operation if not in explorable area
            return False

        if Map.IsInCinematic():  # halt operation during cinematic
            return False
        
        HeroAI_Windows.DrawFlags(cached_data)
        HeroAI_FloatingWindows.draw_Targeting_floating_buttons(cached_data)     
        cached_data.UdpateCombat()
    return True
        
#region main  
def UpdateStatus(cached_data: CacheData) -> bool:
    if (
        not Agent.IsAlive(GLOBAL_CACHE.Player.GetAgentID())
        or (HeroAI_FloatingWindows.DistanceToDestination(cached_data) >= Range.SafeCompass.value)
        or Agent.IsKnockedDown(GLOBAL_CACHE.Player.GetAgentID())
        or cached_data.combat_handler.InCastingRoutine()
        or Agent.IsCasting(GLOBAL_CACHE.Player.GetAgentID())
    ):
        return False

    if LootingRoutineActive():
        return True

    if HandleOutOfCombat(cached_data):
        return True

    if Agent.IsMoving(GLOBAL_CACHE.Player.GetAgentID()):
        return False

    if Loot(cached_data):
        return True

    if Follow(cached_data):
        cached_data.follow_throttle_timer.Reset()
        return True

    if HandleCombat(cached_data):
        cached_data.auto_attack_timer.Reset()
        return True

    if not cached_data.data.in_aggro:
        return False

    if HandleAutoAttack(cached_data):
        return True
    
    return False


#region real_main
def configure():
    draw_configure_window(MODULE_NAME, HeroAI_FloatingWindows.configure_window)



def main():
    global cached_data, map_quads
    
    try:        
        cached_data.Update()
        HeroAI_FloatingWindows.update()
        
        if initialize(cached_data):
            UpdateStatus(cached_data)
        else:
            map_quads.clear()


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

def minimal():    
    draw_skip_cutscene_overlay()

def on_enable():
    HeroAI_FloatingWindows.settings.reset()
    HeroAI_FloatingWindows.SETTINGS_THROTTLE.SetThrottleTime(50)

__all__ = ['main', 'configure', 'on_enable']
