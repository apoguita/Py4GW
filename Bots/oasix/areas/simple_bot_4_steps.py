from abc import abstractmethod
from ast import Raise
from collections.abc import Callable, Generator
import sys
import time
from typing import Any

from Py4GWCoreLib import Map, Routines, Agent
from Py4GWCoreLib.GlobalCache import GLOBAL_CACHE
from Py4GWCoreLib.Py4GWcorelib import LootConfig
from Py4GWCoreLib.enums import Range, SharedCommandType
from Widgets.CustomBehaviors.primitives.behavior_state import BehaviorState
from Widgets.CustomBehaviors.primitives.custom_behavior_loader import CustomBehaviorLoader
from Widgets.CustomBehaviors.primitives.helpers import custom_behavior_helpers
from Widgets.CustomBehaviors.primitives.helpers.custom_behavior_helpers import Helpers
from Widgets.CustomBehaviors.primitives.parties.custom_behavior_party import CustomBehaviorParty
from Widgets.CustomBehaviors.primitives.skillbars.custom_behavior_base_utility import CustomBehaviorBaseUtility
from Widgets.CustomBehaviors.skills.botting.move_if_stuck import MoveIfStuckUtility
from Widgets.CustomBehaviors.skills.botting.move_to_distant_chest_if_path_exists import MoveToDistantChestIfPathExistsUtility
from Widgets.CustomBehaviors.skills.botting.move_to_enemy_if_close_enough import MoveToEnemyIfCloseEnoughUtility
from Widgets.CustomBehaviors.skills.botting.move_to_party_member_if_dead import MoveToPartyMemberIfDeadUtility
from Widgets.CustomBehaviors.skills.botting.move_to_party_member_if_in_aggro import MoveToPartyMemberIfInAggroUtility
from Widgets.CustomBehaviors.skills.botting.resign_if_needed import ResignIfNeededUtility
from Widgets.CustomBehaviors.skills.botting.wait_if_in_aggro import WaitIfInAggroUtility
from Widgets.CustomBehaviors.skills.botting.wait_if_party_member_mana_too_low import WaitIfPartyMemberManaTooLowUtility
from Widgets.CustomBehaviors.skills.botting.wait_if_party_member_needs_to_loot import WaitIfPartyMemberNeedsToLootUtility
from Widgets.CustomBehaviors.skills.botting.wait_if_party_member_too_far import WaitIfPartyMemberTooFarUtility

class SimpleBot4Steps:

    tolerance = 150

    def __init__(self):
        
        print("init")
        instance:CustomBehaviorBaseUtility = CustomBehaviorLoader().custom_combat_behavior
        if instance is None: Raise("CustomBehavior widget is required.")

        # some are not finalized
        # instance.inject_additionnal_utility_skills(ResignIfNeededUtility(instance.in_game_build))
        # instance.inject_additionnal_utility_skills(MoveToDistantChestIfPathExistsUtility(instance.in_game_build))
        
        instance.inject_additionnal_utility_skills(MoveIfStuckUtility(instance.in_game_build))
        instance.inject_additionnal_utility_skills(MoveToPartyMemberIfInAggroUtility(instance.in_game_build))
        instance.inject_additionnal_utility_skills(MoveToEnemyIfCloseEnoughUtility(instance.in_game_build))
        instance.inject_additionnal_utility_skills(MoveToPartyMemberIfDeadUtility(instance.in_game_build))
        instance.inject_additionnal_utility_skills(WaitIfPartyMemberManaTooLowUtility(instance.in_game_build))
        instance.inject_additionnal_utility_skills(WaitIfPartyMemberTooFarUtility(instance.in_game_build))
        instance.inject_additionnal_utility_skills(WaitIfPartyMemberNeedsToLootUtility(instance.in_game_build))
        instance.inject_additionnal_utility_skills(WaitIfInAggroUtility(instance.in_game_build))


    @property
    @abstractmethod
    def item_model_id(self) -> int:
        pass

    @property
    @abstractmethod
    def outpost_id(self) -> int:
        pass

    @property
    @abstractmethod
    def leave_outpost_coords(self) -> list[tuple[float, float]]:
        pass

    @property
    @abstractmethod
    def explorable_area_id(self) -> int:
        pass

    @property
    @abstractmethod
    def explorable_area_coords(self) -> list[tuple[float, float]]:
        pass

    def act(self)-> Generator[Any, None, bool]:
        while(True):
            self.loot_config = LootConfig()
            self.loot_config.AddToWhitelist(self.item_model_id)

            result = yield from self.__teleport_to_outpost()
            if result == False:continue

            result = yield from self._move_to_explorable_area()
            if result == False:continue

            result = yield from self.__move_across_coords_and_kill_if_needed()
            if result == False:continue

            result = yield from self.__wait_being_back_to_outpost()
            if result == False:continue
            
            yield

    def __teleport_to_outpost(self) -> Generator[Any, None, bool]:
        yield from Routines.Yield.Map.TravelToOutpost(self.outpost_id)
        while Map.GetMapID() != self.outpost_id:
            yield from Routines.Yield.wait(1_000)
        # Party.SetHardMode()
        yield from Routines.Yield.wait(200)
        return True

    @abstractmethod
    def _move_to_explorable_area(self) -> Generator[Any, None, bool]:
        '''
        can be overriden if we need a complex acces (NPC / Mission)
        '''
        
        yield from Routines.Yield.Movement.FollowPath(
                path_points=self.leave_outpost_coords, 
                custom_exit_condition=lambda: Map.GetMapID() == self.explorable_area_id, 
                tolerance=self.tolerance, 
                log=True, 
                timeout=60_000, 
                progress_callback=lambda progress: print(f"leave_outpost_coords: progress: {progress}"))

        yield from Routines.Yield.wait(3_000)
        return True

    def __move_across_coords_and_kill_if_needed(self) -> Generator[Any, None, bool]:
        
        print("__move_across_coords_and_kill_if_needed")

        if Map.GetMapID() != self.explorable_area_id:
            return False

        instance:CustomBehaviorBaseUtility = CustomBehaviorLoader._instance.custom_combat_behavior
        if instance is None: Raise("CustomBehavior widget is required.")

        custom_pause_fn: Callable[[], bool] | None = lambda: instance.is_executing_utility_skills() == True # meaning we pause moving across coords, if we have any action that is higher priority

        movement_generator = Routines.Yield.Movement.FollowPath(
                path_points=self.explorable_area_coords, 
                custom_exit_condition=lambda: self.__is_party_defeated(), # todo change to party is dead.
                tolerance=150, 
                log=True, 
                timeout=-1, 
                progress_callback=lambda progress: print(f"move_across_coords_and_kill_if_needed: progress: {progress}"),
                custom_pause_fn=custom_pause_fn)

        yield from movement_generator
        yield from Routines.Yield.wait(20_000) # we wait until last enemy die
        return True

    
    @staticmethod
    def __is_party_defeated() -> bool:
        
        players = GLOBAL_CACHE.Party.GetPlayers()
        count = 0
        for player in players:
            agent_id = GLOBAL_CACHE.Party.Players.GetAgentIDByLoginNumber(player.login_number)
            if Agent.IsDead(agent_id):
                count += 1
            
        if count > 5: return True
        return False

    def __wait_being_back_to_outpost(self) -> Generator[Any, None, bool]:

        # CustomBehaviorParty._instance.set_party_forced_state(BehaviorState.IDLE)
        # yield from Routines.Yield.wait(5_000)

        loop_counter = 0
        while not GLOBAL_CACHE.Party.IsPartyDefeated():
            accounts = GLOBAL_CACHE.ShMem.GetAllAccountData()
            sender_email = GLOBAL_CACHE.Player.GetAccountEmail()
            for account in accounts:
                print("Resigning account: " + account.AccountEmail)
                GLOBAL_CACHE.ShMem.SendMessage(sender_email, account.AccountEmail, SharedCommandType.Resign, (0,0,0,0))

            yield from Routines.Yield.wait(8_000)
            loop_counter += 1
            if loop_counter > 4:
                print("Loop counter Resign is too high, the script is stuck")

            if Map.GetMapID() == self.outpost_id:
                break

        print("Party is defeated")
        loop_counter = 0

        timeout = 15.0
        start_time = time.time()

        while time.time() - start_time < timeout:
            is_map_ready = Map.IsMapReady()
            is_party_loaded = GLOBAL_CACHE.Party.IsPartyLoaded()
            is_explorable = Map.IsExplorable()
            is_party_defeated = GLOBAL_CACHE.Party.IsPartyDefeated()

            if is_map_ready and is_party_loaded and is_explorable and is_party_defeated:
                print(f"Party resigned. Returning to outpost {self.outpost_id}")
                GLOBAL_CACHE.Party.ReturnToOutpost()
                break
            yield from Routines.Yield.wait(500)
        else:
            print(f"Something failed, i am not able to recover - stopping bot.")

        # while not Map.GetMapID() != self.outpost_id:
        #     print("GLOBAL_CACHE.Party.ReturnToOutpost")
        #     GLOBAL_CACHE.Party.ReturnToOutpost()

        #     yield from Routines.Yield.wait(8_000)
        #     loop_counter += 1
        #     if loop_counter > 4:
        #         print("Loop counter ReturnToOutpost is too high, the script is stuck")

        # CustomBehaviorParty._instance.set_party_forced_state(None)
        print("__wait_being_back_to_outpost finalized")
        return True