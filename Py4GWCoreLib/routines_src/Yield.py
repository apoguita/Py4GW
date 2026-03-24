from typing import List, Tuple, Callable, Optional, Generator, Any

from Py4GWCoreLib.enums_src.IO_enums import Key
from Py4GWCoreLib.py4gwcorelib_src.Keystroke import Keystroke
from Py4GWCoreLib.py4gwcorelib_src.Timer import Timer, ThrottledTimer
from Py4GWCoreLib.enums_src.IO_enums import Key
from Py4GWCoreLib.py4gwcorelib_src.Keystroke import Keystroke
from Py4GWCoreLib.Agent import Agent
from Py4GWCoreLib.Player import Player
from Py4GWCoreLib.routines_src import Checks
from ..Map import Map

from ..GlobalCache import GLOBAL_CACHE
from ..Py4GWcorelib import ConsoleLog, Console, Utils, ActionQueueManager

from ..enums_src.Model_enums import ModelID
from ..enums_src.UI_enums import ControlAction
from .BehaviourTrees import BT

import functools
import importlib

class _RProxy:
    def __getattr__(self, name: str):
        root_pkg = importlib.import_module("Py4GWCoreLib")
        return getattr(root_pkg.Routines, name)

Routines = _RProxy()

def _run_bt_tree(tree, return_bool: bool=False, throttle_ms: int = 100):
    """
    Drives a BT tree until SUCCESS / FAILURE, yielding periodically.
    Always yields at least once to guarantee cooperative scheduling.
    If return_bool is True -> returns True/False.
    If return_bool is False -> just exits.
    """
    while True:
        state = tree.tick()

        if state in (BT.NodeState.SUCCESS, BT.NodeState.FAILURE):
            yield
            if return_bool:
                return state == BT.NodeState.SUCCESS
            return

        yield from Yield.wait(throttle_ms)



class Yield:
    @staticmethod
    def wait(ms: int, break_on_map_transition: bool = False):
        import time
        if break_on_map_transition:
            from .Checks import Checks
            from ..Map import Map as _Map

            initial_map_id = _Map.GetMapID()
            initial_district = _Map.GetDistrict()
            initial_region_id = _Map.GetRegion()[0]
            initial_language_id = _Map.GetLanguage()[0]
            initial_instance_uptime = _Map.GetInstanceUptime()

            def _map_transition_detected() -> bool:
                if not Checks.Map.MapValid() or _Map.IsMapLoading():
                    return True
                if _Map.GetMapID() != initial_map_id:
                    return True
                if _Map.GetDistrict() != initial_district:
                    return True
                if _Map.GetRegion()[0] != initial_region_id:
                    return True
                if _Map.GetLanguage()[0] != initial_language_id:
                    return True

                current_instance_uptime = _Map.GetInstanceUptime()
                if initial_instance_uptime > 0 and current_instance_uptime + 2000 < initial_instance_uptime:
                    return True

                return False

        start = time.time()
        while (time.time() - start) * 1000 < ms:
            if break_on_map_transition and _map_transition_detected():
                break
            yield

#region Player
    class Player:
        @staticmethod
        def InteractAgent(agent_id:int, log:bool=False):
            """
            Purpose: Interact with the specified agent.
            Args:
                agent_id (int): The ID of the agent to interact with.
                log (bool) Optional: Whether to log the action. Default is False.
            """
            tree = BT.Player.InteractAgent(agent_id=agent_id, log=log)
            yield from _run_bt_tree(tree , throttle_ms=100)
        @staticmethod
        def InteractTarget(log:bool=False):
            """
            Purpose: Interact with the currently selected target.
            Args:
                log (bool) Optional: Whether to log the action. Default is False.
            """
            tree = BT.Player.InteractTarget(log=log)
            yield from _run_bt_tree(tree , throttle_ms=100)
            
        @staticmethod
        def ChangeTarget(agent_id:int, log:bool=False):
            """
            Purpose: Change the player's target to the specified agent ID.
            Args:
                agent_id (int): The ID of the agent to target.
                log (bool) Optional: Whether to log the action. Default is False.
            Returns: None
            """
            tree = BT.Player.ChangeTarget(agent_id, log=log)
            yield from _run_bt_tree(tree, throttle_ms=250)

        @staticmethod
        def SendDialog(dialog_id:str, log:bool=False):
            """
            Purpose: Send a dialog to the specified dialog ID.
            Args:
                dialog_id (str): The ID of the dialog to send.
                log (bool) Optional: Whether to log the action. Default is False.
            Returns: None
            """
            tree = BT.Player.SendDialog(dialog_id, log=log)
            yield from _run_bt_tree(tree,throttle_ms=300)

        @staticmethod
        def SetTitle(title_id:int, log:bool=False):
            """
            Purpose: Set the player's title to the specified title ID.
            Args:
                title_id (int): The ID of the title to set.
                log (bool) Optional: Whether to log the action. Default is False.
            Returns: None
            """
            tree = BT.Player.SetTitle(title_id, log=log)
            yield from _run_bt_tree(tree, throttle_ms=300)

        @staticmethod
        def BuySkill(skill_id: int, log: bool = False):
            """
            Purpose: Buy/Learn a skill from a Skill Trainer.
            Args:
                skill_id (int): The ID of the skill to purchase.
                log (bool) Optional: Whether to log the action. Default is False.
            Returns: None
            """
            tree = BT.Player.BuySkill(skill_id, log=log)
            yield from _run_bt_tree(tree, throttle_ms=300)

        @staticmethod
        def UnlockBalthazarSkill(skill_id: int, use_pvp_remap: bool = True, log: bool = False):
            """
            Purpose: Unlock a skill from the Priest of Balthazar vendor.
            Args:
                skill_id (int): The ID of the skill to unlock.
                use_pvp_remap (bool) Optional: Whether to remap via PvP skill id. Default is True.
                log (bool) Optional: Whether to log the action. Default is False.
            Returns: None
            """
            tree = BT.Player.UnlockBalthazarSkill(skill_id, use_pvp_remap=use_pvp_remap, log=log)
            yield from _run_bt_tree(tree, throttle_ms=300)

        @staticmethod
        def SendChatCommand(command:str, log=False):
            """
            Purpose: Send a chat command.
            Args:
                command (str): The chat command to send.
                log (bool) Optional: Whether to log the action. Default is False.
            Returns: None
            """
            tree = BT.Player.SendChatCommand(command, log=log)
            yield from _run_bt_tree(tree, throttle_ms=300)  

        @staticmethod
        def Resign(log:bool=False):
            """
            Purpose: Resign from the current map.
            Args:
                log (bool) Optional: Whether to log the action. Default is False.
            Returns: None
            """
            tree = BT.Player.SendChatCommand("resign", log=log)
            yield from _run_bt_tree(tree, throttle_ms=250)
            
        @staticmethod
        def SendChatMessage(channel:str, message:str, log=False):
            """
            Purpose: Send a chat message to the specified channel.
            Args:
                channel (str): The channel to send the message to.
                message (str): The message to send.
                log (bool) Optional: Whether to log the action. Default is True.
            Returns: None
            """
            tree = BT.Player.SendChatMessage(channel, message, log=log)
            yield from _run_bt_tree(tree, throttle_ms=300)
            
        @staticmethod
        def PrintMessageToConsole(source:str, message: str, message_type: int = Console.MessageType.Info):
            """
            Purpose: Print a message to the console.
            Args:
                message (str): The message to print.
            Returns: None
            """
            tree = BT.Player.PrintMessageToConsole(source, message, message_type)
            yield from _run_bt_tree(tree , throttle_ms=100)

            
        @staticmethod
        def Move(x:float, y:float, log=False):
            """
            Purpose: Move the player to the specified coordinates.
            Args:
                x (float): The x coordinate.
                y (float): The y coordinate.
                log (bool) Optional: Whether to log the action. Default is False.
            Returns: None
            """
            tree = BT.Player.Move(x, y, log=log)
            yield from _run_bt_tree(tree , throttle_ms=100)
            
        @staticmethod
        def MoveXYZ(x:float, y:float, zplane:int, log=False):
            """
            Purpose: Move the player to the specified coordinates and z-plane.
            Args:
                x (float): The x coordinate.
                y (float): The y coordinate.
                zplane (int): The z-plane.
                log (bool) Optional: Whether to log the action. Default is False.
            Returns: None
            """
            tree = BT.Player.MoveXYZ(x, y, zplane, log=log)
            yield from _run_bt_tree(tree , throttle_ms=100)

#region Skills
    class Skills:       
        @staticmethod
        def GenerateSkillbarTemplate():
            """
            Purpose: Generate template code for player's skillbar
            Args: None
            Returns: str: The current skillbar template.
            """
            skillbar_template = Utils.GenerateSkillbarTemplate()
            yield
            return skillbar_template

        @staticmethod
        def ParseSkillbarTemplate(template:str):
            '''
            Purpose: Parse a skillbar template into its components.
            Args:
                template (str): The skillbar template to parse.
            Returns:
                prof_primary (int): The primary profession ID.
                prof_secondary (int): The secondary profession ID.
                attributes (dict): A dictionary of attribute IDs and levels.
                skills (list): A list of skill IDs.
            '''

            result = Utils.ParseSkillbarTemplate(template)
            yield
            return result

        @staticmethod
        def LoadSkillbar(skill_template:str, log=False):
            """
            Purpose: Load the specified skillbar.
            Args:
                skill_template (str): The name of the skill template to load.
                log (bool) Optional: Whether to log the action. Default is True.
            Returns: None
            """
            tree = BT.Skills.LoadSkillbar(skill_template, log)
            yield from _run_bt_tree(tree, throttle_ms=500)

        @staticmethod
        def LoadHeroSkillbar(hero_index:int, skill_template:str, log=False):
            """
            Purpose: Load the specified hero skillbar.
            Args:
                hero_index (int): The index of the hero (1-4).
                skill_template (str): The name of the skill template to load.
                log (bool) Optional: Whether to log the action. Default is True.
            Returns: None
            """
            tree = BT.Skills.LoadHeroSkillbar(hero_index, skill_template, log)
            yield from _run_bt_tree(tree, throttle_ms=500)
        
            
        @staticmethod
        def IsSkillIDUsable(skill_id: int):
            """
            Purpose: Check if a skill by its ID is usable using a Behavior Tree.
            Args:
                skill_id (int): The ID of the skill to check.
            Returns: bool: True if the skill is usable, False otherwise.
            """
            tree = BT.Skills.IsSkillIDUsable(skill_id)
            result = yield from _run_bt_tree(tree, return_bool=True, throttle_ms=0)
            return result

        
        @staticmethod
        def IsSkillSlotUsable(skill_slot: int):
            """
            Purpose: Check if a skill in a specific slot is usable using a Behavior Tree.
            Args:
                skill_slot (int): The slot number of the skill to check.
            Returns: A Behavior Tree that checks if the skill in the slot is usable.
            """
            tree = BT.Skills.IsSkillSlotUsable(skill_slot)
            result = yield from _run_bt_tree(tree, return_bool=True, throttle_ms=0)
            return result
        
        @staticmethod    
        def CastSkillID (skill_id:int,target_agent_id:int =0, extra_condition=True, aftercast_delay=0,  log=False):
            """
            Purpose: Cast a skill by its ID using a coroutine.
            Args:
                skill_id (int): The ID of the skill to cast.
                target_agent_id (int) Optional: The ID of the target agent. Default is 0.
                extra_condition (bool) Optional: An extra condition to check before casting. Default is True.
                aftercast_delay (int) Optional: Delay in milliseconds after casting the skill. Default is 0.
                log (bool) Optional: Whether to log the action. Default is False.
            Returns: bool: True if the skill was cast successfully, False otherwise.
            """
            tree = BT.Skills.CastSkillID(skill_id, target_agent_id, extra_condition, aftercast_delay, log)
            result = yield from _run_bt_tree(tree, return_bool=True, throttle_ms=aftercast_delay)
            return result
            

        @staticmethod
        def CastSkillSlot(slot:int,extra_condition=True, aftercast_delay=0, log=False):
            """
            purpose: Cast a skill in a specific slot using a coroutine.

            Args:
                slot (int): The slot number of the skill to cast.
                extra_condition (bool) Optional: An extra condition to check before casting. Default is True.
                aftercast_delay (int) Optional: Delay in milliseconds after casting the skill. Default is 0.
                log (bool) Optional: Whether to log the action. Default is False.
            Returns: bool: True if the skill was cast successfully, False otherwise.
            """
            tree = BT.Skills.CastSkillSlot(slot=slot, extra_condition=extra_condition, aftercast_delay=aftercast_delay, log=log)
            result = yield from _run_bt_tree(tree, return_bool=True, throttle_ms=aftercast_delay)
            return result
            
#region Map      
    class Map:  
        @staticmethod
        def SetHardMode(hard_mode=True, log=False):
            """
            Purpose: Set the map to hard mode.
            Args: None
            Returns: None
            """
            tree = BT.Map.SetHardMode(hard_mode, log)
            yield from _run_bt_tree(tree, return_bool=False, throttle_ms=100)
                
        @staticmethod
        def TravelToOutpost(outpost_id, log=False, timeout:int=10000):
            """
            Purpose: Positions yourself safely on the outpost.
            Args:
                outpost_id (int): The ID of the outpost to travel to.
                log (bool) Optional: Whether to log the action. Default is False.
            Returns: None
            """
            
            tree = BT.Map.TravelToOutpost(outpost_id, log, timeout)
            result = yield from _run_bt_tree(tree, return_bool=True, throttle_ms=100)
            return result


        @staticmethod
        def TravelToRegion(outpost_id, region, district, language=0, log=False):
            """
            Purpose: Positions yourself safely on the outpost.
            Args:
                outpost_id (int): The ID of the outpost to travel to.
                region (int): The region ID to travel to.
                district (int): The district ID to travel to.
                language (int): The language ID to travel to. Default is 0.
                log (bool) Optional: Whether to log the action. Default is True.
            Returns: None
            """
            
            tree = BT.Map.TravelToRegion(outpost_id, region, district, language, log)
            result = yield from _run_bt_tree(tree, return_bool=True, throttle_ms=100)
            return result


        @staticmethod
        def WaitforMapLoad(map_id, log=False, timeout: int = 10000, map_name: str =""):
            """
            Purpose: Wait for the map to load completely.
            Args:
                map_id (int): The ID of the map to wait for.
                log (bool) Optional: Whether to log the action. Default is False.
                timeout (int) Optional: Timeout in milliseconds. Default is 10000.
                map_name (str) Optional: The name of the map to wait for. Default is "".
            Returns: bool: True if the map loaded successfully, False if timed out.
            """
            
            tree = BT.Map.WaitforMapLoad(map_id, log, timeout, map_name)
            result = yield from _run_bt_tree(tree, return_bool=True, throttle_ms=500)
            return result
        
#region Movement
    class Movement:
        @staticmethod
        def StopMovement(log=False):
            yield from Yield.Movement.WalkBackwards(125, log=log)

        @staticmethod   
        def WalkBackwards(duration_ms:int, log=False):
            yield from Yield.Keybinds.PressKeybind(ControlAction.ControlAction_MoveBackward.value, duration_ms, log=log)

        @staticmethod
        def WalkForwards(duration_ms:int, log=False):
            yield from Yield.Keybinds.PressKeybind(ControlAction.ControlAction_MoveForward.value, duration_ms, log=log)
        @staticmethod
        def StrafeLeft(duration_ms:int, log=False):
            yield from Yield.Keybinds.PressKeybind(ControlAction.ControlAction_StrafeLeft.value, duration_ms, log=log)

        @staticmethod
        def StrafeRight(duration_ms:int, log=False):
            yield from Yield.Keybinds.PressKeybind(ControlAction.ControlAction_StrafeRight.value, duration_ms, log=log)
        @staticmethod
        def TurnLeft(duration_ms:int, log=False):
            yield from Yield.Keybinds.PressKeybind(ControlAction.ControlAction_TurnLeft.value, duration_ms, log=log)

        @staticmethod
        def TurnRight(duration_ms:int, log=False):
            yield from Yield.Keybinds.PressKeybind(ControlAction.ControlAction_TurnRight.value, duration_ms, log=log)
        
        #region FollowPath
        @staticmethod
        def FollowPath(
            path_points: List[Tuple[float, float]],
            custom_exit_condition: Callable[[], bool] = lambda: False,
            tolerance: float = 150,
            log: bool = False,
            timeout: int = -1,
            progress_callback: Optional[Callable[[float], None]] = None,
            custom_pause_fn: Optional[Callable[[], bool]] = None,
            stop_on_party_wipe: bool = True,
            map_transition_exit_success: bool = False,
        ):
            import random
            from .Checks import Checks
            from ..Pathing import AutoPathing
            from ..Map import Map as _Map

            #log = True #force logging
            detailed_log = False #always detailed log for now

            path_points = list(path_points or [])
            total_points = len(path_points)
            retries = 0
            max_retries = 30  # after this, send stuck command
            stuck_count = 0
            max_stuck_commands = 2  # after this, do PixelStack recovery

            # Capture starting map so we can detect fast transitions (new map valid before next tick)
            _initial_map_id = _Map.GetMapID()

            def _map_still_valid() -> bool:
                return Checks.Map.MapValid() and _Map.GetMapID() == _initial_map_id

            def _abort_on_map_invalid(msg: str) -> bool:
                ConsoleLog("FollowPath", msg, Console.MessageType.Warning, log=log)
                ActionQueueManager().ResetAllQueues()
                return map_transition_exit_success

            if total_points == 0:
                ConsoleLog("FollowPath", "Empty path provided, treating as success.", Console.MessageType.Warning, log=log)
                return True

            def _pick_resume_index(current_index: int) -> int:
                remaining = path_points[current_index:]
                if not remaining:
                    return current_index

                current_pos = Player.GetXY()
                nearby_threshold = max(tolerance, 200.0)
                nearby_indices: list[int] = []
                best_relative_index = 0
                best_distance = float("inf")

                for relative_index, point in enumerate(remaining):
                    distance = Utils.Distance(current_pos, point)
                    if distance <= nearby_threshold:
                        nearby_indices.append(relative_index)
                    if distance < best_distance:
                        best_distance = distance
                        best_relative_index = relative_index

                if nearby_indices:
                    return current_index + max(nearby_indices)

                return current_index + best_relative_index

            def _rebuild_remaining_path(resume_index: int) -> tuple[int, bool]:
                if resume_index >= len(path_points):
                    return resume_index, False

                resume_target = path_points[resume_index]
                current_pos = Player.GetXY()
                distance_to_resume = Utils.Distance(current_pos, resume_target)
                bridge_threshold = max(tolerance * 3.0, 600.0)

                if distance_to_resume <= bridge_threshold:
                    return resume_index, False

                bridge_path = yield from AutoPathing().get_path_to(resume_target[0], resume_target[1])
                if not bridge_path:
                    return resume_index, False

                trimmed_bridge: List[Tuple[float, float]] = []
                for point in bridge_path:
                    if not trimmed_bridge and Utils.Distance(current_pos, point) <= tolerance:
                        continue
                    trimmed_bridge.append(point)

                if not trimmed_bridge:
                    return resume_index, False

                remaining_tail = path_points[resume_index + 1:]
                path_points[:] = trimmed_bridge + remaining_tail
                return 0, True

            ConsoleLog("FollowPath", f"Starting path with {total_points} points.", Console.MessageType.Info, log=log)

            idx = 0
            while idx < len(path_points):
                total_points = len(path_points)
                target_x, target_y = path_points[idx]
                start_time = Utils.GetBaseTimestamp()
                
                ConsoleLog("FollowPath", f"Starting point {idx+1}/{total_points} - ({target_x}, {target_y}) distance {Utils.Distance(Player.GetXY(), (target_x, target_y))}", Console.MessageType.Info, log=detailed_log)


                if not _map_still_valid():
                    return _abort_on_map_invalid("Map invalid before starting point, aborting movement point.")

                if stop_on_party_wipe and (
                        Checks.Party.IsPartyWiped() or GLOBAL_CACHE.Party.IsPartyDefeated()
                    ):
                        ConsoleLog("FollowPath", "Party wiped detected, stopping all movement.", Console.MessageType.Warning, log=True  )
                        ActionQueueManager().ResetAllQueues()
                        return False

                Player.Move(target_x, target_y)
                ConsoleLog("FollowPath", f"Issued move command to ({target_x}, {target_y}).", Console.MessageType.Debug, log=detailed_log)

                yield from Yield.wait(250)
                if not _map_still_valid():
                    return _abort_on_map_invalid("Map changed or became invalid right after issuing move.")

                current_x, current_y = Player.GetXY()
                previous_distance = Utils.Distance((current_x, current_y), (target_x, target_y))

                while True:
                    ConsoleLog("FollowPath", "Movement loop iteration...", Console.MessageType.Debug, log=detailed_log)

                    if not _map_still_valid():
                        return _abort_on_map_invalid("Map changed or became invalid mid-run, aborting movement.")

                    if custom_exit_condition():
                        ConsoleLog("FollowPath", "Custom exit condition met, stopping movement.", Console.MessageType.Info, log=log)
                        return False

                    if stop_on_party_wipe and (
                        Checks.Party.IsPartyWiped() or GLOBAL_CACHE.Party.IsPartyDefeated()
                    ):
                        ConsoleLog("FollowPath", "Party wiped detected, stopping all movement.", Console.MessageType.Warning, log=True   )
                        ActionQueueManager().ResetAllQueues()
                        return False


                    if Agent.IsValid(Player.GetAgentID()) and Agent.IsCasting(Player.GetAgentID()):
                        ConsoleLog("FollowPath", "Player casting detected, waiting 750ms...", Console.MessageType.Debug, log=detailed_log)

                        yield from Yield.wait(750)
                        continue

                    if custom_pause_fn:
                        was_paused = False
                        while custom_pause_fn():
                            was_paused = True
                            if not _map_still_valid():
                                return _abort_on_map_invalid("Map changed while movement was paused, aborting.")
                            if custom_exit_condition():
                                ConsoleLog("FollowPath", "Custom exit condition met while movement was paused, stopping movement.", Console.MessageType.Info, log=log)
                                return False
                            if stop_on_party_wipe and (Checks.Map.MapValid() and
                                    (Checks.Party.IsPartyWiped() or GLOBAL_CACHE.Party.IsPartyDefeated())
                                ):
                                    ConsoleLog("FollowPath", "Party wiped detected during pause, stopping all movement.", Console.MessageType.Warning, log=True)
                                    ActionQueueManager().ResetAllQueues()
                                    return False
                            ConsoleLog("FollowPath", "Custom pause condition active, pausing movement...", Console.MessageType.Debug, log=log)
                            start_time = Utils.GetBaseTimestamp()  # Reset timeout timer
                            yield from Yield.wait(750)

                        if was_paused:
                            resume_idx = _pick_resume_index(idx)
                            if resume_idx != idx:
                                ConsoleLog(
                                    "FollowPath",
                                    f"Pause ended, resuming from point {resume_idx + 1}/{len(path_points)} instead of {idx + 1}/{len(path_points)}.",
                                    Console.MessageType.Info,
                                    log=log,
                                )
                                idx = resume_idx

                            rebuilt_idx, rebuilt = yield from _rebuild_remaining_path(idx)
                            if rebuilt:
                                idx = rebuilt_idx
                                total_points = len(path_points)
                                ConsoleLog(
                                    "FollowPath",
                                    f"Pause ended far from route, rebuilt remaining path with {total_points} points.",
                                    Console.MessageType.Info,
                                    log=log,
                                )
                            elif rebuilt_idx != idx:
                                idx = rebuilt_idx

                            if idx >= len(path_points):
                                return True

                            target_x, target_y = path_points[idx]
                            Player.Move(target_x, target_y)
                            yield from Yield.wait(250)
                            if not _map_still_valid():
                                return _abort_on_map_invalid("Map changed while resuming movement after pause.")
                            current_x, current_y = Player.GetXY()
                            previous_distance = Utils.Distance((current_x, current_y), (target_x, target_y))
                            retries = 0
                            stuck_count = 0
                            continue

                    if not _map_still_valid():
                        return _abort_on_map_invalid("Map changed while traversing path.")

                    current_time = Utils.GetBaseTimestamp()
                    delta = current_time - start_time
                    if delta > timeout and timeout > 0:
                        ConsoleLog("FollowPath", f"Timeout reached, stopping movement. distance to failes point {Utils.Distance(Player.GetXY(), (target_x, target_y))}", Console.MessageType.Warning, log=log)
                        return False

                    current_x, current_y = Player.GetXY()
                    current_distance = Utils.Distance((current_x, current_y), (target_x, target_y))

                    if not (current_distance < previous_distance):
                        offset_x = random.uniform(-5, 5)
                        offset_y = random.uniform(-5, 5)
                        ConsoleLog("FollowPath", f"move to {target_x + offset_x}, {target_y + offset_y}", Console.MessageType.Info, log=log)
                        if not _map_still_valid():
                            return _abort_on_map_invalid("Map changed before retrying move with offset.")
                        Player.Move(target_x + offset_x, target_y + offset_y)
                        retries += 1
                        if retries >= max_retries:
                            Player.SendChatCommand("stuck")
                            ConsoleLog("FollowPath", "No progress made, sending /stuck command.", Console.MessageType.Warning, log=log)

                            retries = 0
                            stuck_count += 1

                            # --- PixelStack recovery if too many stucks ---
                            if stuck_count >= max_stuck_commands:
                                ConsoleLog("FollowPath", "Too many stucks, performing strafe recovery.", Console.MessageType.Warning, log=log)

                                start_x, start_y = Player.GetXY()

                                # Backwards
                                yield from Yield.Movement.WalkBackwards(1000)
                                if not _map_still_valid():
                                    return _abort_on_map_invalid("Map changed during backwards recovery.")
                                # Strafe left
                                yield from Yield.Movement.StrafeLeft(1000)
                                if not _map_still_valid():
                                    return _abort_on_map_invalid("Map changed during strafe-left recovery.")

                                # Strafe right if no movement
                                left_x, left_y = Player.GetXY()
                                if Utils.Distance((start_x, start_y), (left_x, left_y)) < 50:
                                    yield from Yield.Movement.StrafeRight(1000)
                                    if not _map_still_valid():
                                        return _abort_on_map_invalid("Map changed during strafe-right recovery.")

                                stuck_count = 0  # reset after recovery
                    else:
                        retries = 0  # reset retries if making progress
                        stuck_count = 0  # reset stuck count if making progress
                        ConsoleLog("FollowPath", "Progress detected, reset retry counters.", Console.MessageType.Debug, log=detailed_log)

                    if not _map_still_valid():
                        return _abort_on_map_invalid("Map changed before finishing current waypoint.")
                    #common
                    previous_distance = current_distance

                    if current_distance <= tolerance:
                        ConsoleLog("FollowPath", f"Reached target point {idx+1}/{total_points}.", Console.MessageType.Success, log=log)
                        break
                    else:
                        ConsoleLog("FollowPath", f"Current distance to target: {current_distance}, waiting...", Console.MessageType.Debug, log=detailed_log)


                    yield from Yield.wait(250)

                #After reaching each point, report progress
                if progress_callback:
                    progress_callback((idx + 1) / total_points)
                    ConsoleLog("FollowPath", f"Progress callback: {((idx + 1) / total_points) * 100:.1f}% done.", Console.MessageType.Debug, log=detailed_log)

                idx += 1


            ConsoleLog("FollowPath", "Path traversal completed successfully.", Console.MessageType.Success, log=log)
            return True
    


#region Agents        
    class Agents:
        @staticmethod
        def GetAgentIDByName(agent_name):
            tree = BT.Agents.GetAgentIDByName(agent_name)
            yield from _run_bt_tree(tree, throttle_ms=100)
            agent = tree.blackboard.get("result", 0)
            return agent
            


        @staticmethod
        def GetAgentIDByModelID(model_id:int):
            """
            Purpose: Get the agent ID by model ID.
            Args:
                model_id (int): The model ID of the agent.
            Returns: int: The agent ID or 0 if not found.
            """
            tree = BT.Agents.GetAgentIDByModelID(model_id)
            yield from _run_bt_tree(tree, throttle_ms=100)
            agent = tree.blackboard.get("result", 0)
            return agent

        @staticmethod
        def ChangeTarget(agent_id, log=False):
            """
            Purpose: Change the player's target to the specified agent ID.
            Args:
                agent_id (int): The ID of the agent to target.
            Returns: None
            """
            yield from Yield.Player.ChangeTarget(agent_id, log=log)
                
        @staticmethod
        def InteractAgent(agent_id:int, log:bool=False):
            """
            Purpose: Interact with the specified agent.
            Args:
                agent_id (int): The ID of the agent to interact with.
                log (bool) Optional: Whether to log the action. Default is False.
            """
            yield from Yield.Player.InteractAgent(agent_id, log=log)
            
        @staticmethod
        def TargetAgentByName(agent_name:str, log:bool=False):
            """
            Purpose: Target an agent by name.
            Args:
                agent_name (str): The name of the agent to target.
            Returns: None
            """
            tree = BT.Agents.TargetAgentByName(agent_name, log=log)
            yield from _run_bt_tree(tree, throttle_ms=100)


        @staticmethod
        def TargetNearestNPC(distance:float = 4500.0, log:bool=False):
            """
            Purpose: Target the nearest NPC within a specified distance.
            Args:
                distance (float) Optional: The maximum distance to search for an NPC. Default is 4500.0.
            Returns: None
            """
            tree = BT.Agents.TargetNearestNPC(distance, log=log)
            yield from _run_bt_tree(tree, throttle_ms=100)
            
        @staticmethod
        def TargetNearestNPCXY(x,y,distance, log:bool=False):
            """
            Purpose: Target the nearest NPC to specified coordinates within a certain distance.
            Args:
                x (float): The x coordinate.
                y (float): The y coordinate.
                distance (float): The maximum distance to search for an NPC.
            Returns: None
            """
            tree = BT.Agents.TargetNearestNPCXY(x,y,distance, log=log)
            yield from _run_bt_tree(tree, throttle_ms=100)

                
        @staticmethod
        def TargetNearestGadgetXY(x,y,distance, log:bool=False):
            """
            Purpose: Target the nearest gadget to specified coordinates within a certain distance.
            Args:
                x (float): The x coordinate.
                y (float): The y coordinate.
                distance (float): The maximum distance to search for a gadget.
            Returns: None
            """
            tree = BT.Agents.TargetNearestGadgetXY(x,y,distance, log=log)
            yield from _run_bt_tree(tree, throttle_ms=100)

        @staticmethod
        def TargetNearestItemXY(x,y,distance, log:bool=False):
            """
            Purpose: Target the nearest item to specified coordinates within a certain distance.
            Args:
                x (float): The x coordinate.
                y (float): The y coordinate.
                distance (float): The maximum distance to search for an item.
            Returns: None
            """
            tree = BT.Agents.TargetNearestItemXY(x,y,distance, log=log)
            yield from _run_bt_tree(tree, throttle_ms=100)

        @staticmethod
        def TargetNearestEnemy(distance, log:bool=False):
            """
            Purpose: Target the nearest enemy within a specified distance.
            Args:
                distance (float): The maximum distance to search for an enemy.
            Returns: None
            """
            tree = BT.Agents.TargetNearestEnemy(distance, log=log)
            yield from _run_bt_tree(tree, throttle_ms=100)
        
        @staticmethod
        def TargetNearestItem(distance, log:bool=False):
            """
            Purpose: Target the nearest item within a specified distance.
            Args:
                distance (float): The maximum distance to search for an item.
            Returns: None
            """
            tree = BT.Agents.TargetNearestItem(distance, log=log)
            yield from _run_bt_tree(tree, throttle_ms=100)
                
        @staticmethod
        def TargetNearestChest(distance, log:bool=False):
            """
            Purpose: Target the nearest chest within a specified distance.
            Args:
                distance (float): The maximum distance to search for a chest.
            Returns: None
            """
            tree = BT.Agents.TargetNearestChest(distance, log=log)
            yield from _run_bt_tree(tree, throttle_ms=100)
            
        @staticmethod
        def InteractWithNearestChest(max_distance:int = 2500, before_interact_fn = lambda: None, after_interact_fn = lambda: None):
            """Target and interact with chest and items."""
            from .Agents import Agents
            
            from ..Py4GWcorelib import LootConfig, Utils
            from ..enums_src.GameData_enums import Range

            nearest_chest = Agents.GetNearestChest(max_distance)
            chest_x, chest_y = Agent.GetXY(nearest_chest)


            yield from Yield.Movement.FollowPath([(chest_x, chest_y)])
            yield from Yield.wait(500)

            before_interact_fn()

            yield from Yield.Player.InteractAgent(nearest_chest)
            yield from Yield.wait(500)
            Player.SendDialog(2)
            yield from Yield.wait(500)

            yield from Yield.Agents.TargetNearestItem(distance=300)
            filtered_loot = LootConfig().GetfilteredLootArray(Range.Area.value, multibox_loot= True)
            item = Utils.GetFirstFromArray(filtered_loot)
            yield from Yield.Agents.ChangeTarget(item)
            yield from Yield.Player.InteractTarget()

            after_interact_fn()
            
            yield from Yield.wait(1000)
            
        @staticmethod
        def InteractWithAgentByName(agent_name:str):
            
            yield from Yield.Agents.TargetAgentByName(agent_name)
            agent_x, agent_y = Agent.GetXY(Player.GetTargetID())

            yield from Yield.Movement.FollowPath([(agent_x, agent_y)])
            yield from Yield.wait(500)
            
            yield from Yield.Player.InteractTarget()
            yield from Yield.wait(1000)
            
        @staticmethod
        def InteractWithAgentXY(x:float, y:float, timeout_ms: int = 5000, tolerance: float = 200.0):
            
            from ..Py4GWcorelib import ConsoleLog, Utils
            yield from Yield.Agents.TargetNearestNPCXY(x, y, 100)
            target_id = Player.GetTargetID()
            if not target_id:
                ConsoleLog("InteractWithGadgetXY", "No target after targeting.")
                return False

            # 2) Interact once — the game will auto-move to the target
            yield from Yield.Player.InteractTarget()

            # 3) Wait until we’re inside the threshold (or timeout), re-issuing every 1000 ms
            elapsed = 0
            since_reissue = 0
            reissue_interval = 1000
            step = 100  # ms
            while elapsed < timeout_ms:
                px, py = Player.GetXY()
                tx, ty = Agent.GetXY(target_id)
                if Utils.Distance((px, py), (tx, ty)) <= tolerance:
                    break

                if since_reissue >= reissue_interval:
                    yield from Yield.Agents.TargetNearestGadgetXY(x, y, 100)
                    yield from Yield.Player.InteractTarget()
                    since_reissue = 0

                yield from Yield.wait(step)
                elapsed += step
                since_reissue += step

            if elapsed >= timeout_ms:
                ConsoleLog("InteractWithAgentXY", "TIMEOUT waiting to reach target range.")
                return False

            # 4) Small settle
            yield from Yield.wait(500)
            return True
        
        @staticmethod
        def InteractWithGadgetXY(x: float, y: float, tolerance: float = 200.0, timeout_ms: int = 15000):
            
            from ..Py4GWcorelib import ConsoleLog, Utils
            # 1) Aim at the nearest gadget around (x, y)
            yield from Yield.Agents.TargetNearestGadgetXY(x, y, 100)
            target_id = Player.GetTargetID()
            if not target_id:
                ConsoleLog("InteractWithGadgetXY", "No target after targeting.")
                return False

            # 2) Interact once — the game will auto-move to the target
            yield from Yield.Player.InteractTarget()

            # 3) Wait until we’re inside the threshold (or timeout), re-issuing every 1000 ms
            elapsed = 0
            since_reissue = 0
            step = 100  # ms
            while elapsed < timeout_ms:
                px, py = Player.GetXY()
                tx, ty = Agent.GetXY(target_id)
                if Utils.Distance((px, py), (tx, ty)) <= tolerance:
                    break

                if since_reissue >= 1000:
                    yield from Yield.Agents.TargetNearestGadgetXY(x, y, 100)
                    yield from Yield.Player.InteractTarget()
                    since_reissue = 0

                yield from Yield.wait(step)
                elapsed += step
                since_reissue += step

            if elapsed >= timeout_ms:
                ConsoleLog("InteractWithAgentXY", "TIMEOUT waiting to reach target range.")
                return False

            # 4) Small settle
            yield from Yield.wait(500)
            return True
        
        @staticmethod
        def InteractWithItemXY(x: float, y: float, tolerance: float = 200.0, timeout_ms: int = 15000):
            
            from ..Py4GWcorelib import ConsoleLog, Utils
            # 1) Aim at the nearest item around (x, y)
            yield from Yield.Agents.TargetNearestItemXY(x, y, 100)
            target_id = Player.GetTargetID()
            if not target_id:
                ConsoleLog("InteractWithItemXY", "No target after targeting.")
                return False

            # 2) Interact once — the game will auto-move to the target
            yield from Yield.Player.InteractTarget()

            # 3) Wait until we’re inside the threshold (or timeout), re-issuing every 1000 ms
            elapsed = 0
            since_reissue = 0
            step = 100  # ms
            while elapsed < timeout_ms:
                px, py = Player.GetXY()
                tx, ty = Agent.GetXY(target_id)
                if Utils.Distance((px, py), (tx, ty)) <= tolerance:
                    break

                if since_reissue >= 1000:
                    yield from Yield.Agents.TargetNearestItemXY(x, y, 100)
                    yield from Yield.Player.InteractTarget()
                    since_reissue = 0

                yield from Yield.wait(step)
                elapsed += step
                since_reissue += step

            if elapsed >= timeout_ms:
                ConsoleLog("InteractWithAgentXY", "TIMEOUT waiting to reach target range.")
                return False

            # 4) Small settle
            yield from Yield.wait(500)
            return True



#region Merchant      
    class Merchant:
        @staticmethod
        def _get_trader_batch_size(trader_items: list[int] | None = None) -> int:
            offered_items = trader_items if trader_items is not None else list(GLOBAL_CACHE.Trading.Trader.GetOfferedItems())
            offered_models = {int(GLOBAL_CACHE.Item.GetModelID(item_id)) for item_id in offered_items}
            return 10 if int(ModelID.Wood_Plank.value) in offered_models else 1

        @staticmethod
        def _wait_for_trader_inventory(timeout_ms: int = 2500, step_ms: int = 5):
            trader_items = []
            wait_elapsed_ms = 0
            while wait_elapsed_ms < timeout_ms:
                trader_items = list(GLOBAL_CACHE.Trading.Trader.GetOfferedItems())
                if trader_items:
                    break
                wait_elapsed_ms += step_ms
                yield from Yield.wait(step_ms)
            return trader_items

        @staticmethod
        def _wait_for_quote(request_fn, request_id: int, timeout_ms: int, step_ms: int):
            matched_quote = -1
            request_fn(request_id)
            wait_elapsed_ms = 0
            request_retry_elapsed_ms = 0
            while wait_elapsed_ms < timeout_ms:
                yield from Yield.wait(step_ms)
                wait_elapsed_ms += step_ms
                request_retry_elapsed_ms += step_ms

                quoted_item_id = int(GLOBAL_CACHE.Trading.Trader.GetQuotedItemID())
                quoted_value = int(GLOBAL_CACHE.Trading.Trader.GetQuotedValue())
                if quoted_value >= 0 and quoted_item_id == request_id:
                    matched_quote = quoted_value
                    break
                if request_retry_elapsed_ms >= 150:
                    request_fn(request_id)
                    request_retry_elapsed_ms = 0
            return matched_quote

        @staticmethod
        def _wait_for_transaction(timeout_ms: int, step_ms: int):
            wait_elapsed_ms = 0
            while wait_elapsed_ms < timeout_ms:
                yield from Yield.wait(step_ms)
                if GLOBAL_CACHE.Trading.IsTransactionComplete():
                    return True
                wait_elapsed_ms += step_ms
            return False

        @staticmethod
        def _wait_for_stack_quantity_drop(
            item_id: int,
            previous_quantity: int,
            timeout_ms: int,
            step_ms: int,
        ):
            """
            Wait for a sold stack to decrease (or disappear from inventory).
            Material-trader transactions can report completion before inventory state refreshes.
            """
            wait_elapsed_ms = 0
            while wait_elapsed_ms < timeout_ms:
                yield from Yield.wait(step_ms)
                current_quantity = int(GLOBAL_CACHE.Item.Properties.GetQuantity(item_id))
                if current_quantity < previous_quantity:
                    return current_quantity
                wait_elapsed_ms += step_ms

            # Final read so callers can compare against the latest observed state.
            return int(GLOBAL_CACHE.Item.Properties.GetQuantity(item_id))

        @staticmethod
        def _scan_material_item_ids(selected_models: set[int] | None = None, exact_quantity: int | None = None) -> list[int]:
            bags_to_check = GLOBAL_CACHE.ItemArray.CreateBagList(1, 2, 3, 4)
            bag_item_array = GLOBAL_CACHE.ItemArray.GetItemArray(bags_to_check)
            item_ids: list[int] = []
            for item_id in bag_item_array:
                if not GLOBAL_CACHE.Item.Type.IsMaterial(item_id):
                    continue
                if GLOBAL_CACHE.Item.Type.IsRareMaterial(item_id):
                    continue

                model_id = int(GLOBAL_CACHE.Item.GetModelID(item_id))
                if selected_models is not None and model_id not in selected_models:
                    continue
                if exact_quantity is not None and int(GLOBAL_CACHE.Item.Properties.GetQuantity(item_id)) != exact_quantity:
                    continue

                item_ids.append(int(item_id))
            return item_ids

        @staticmethod
        def _interact_with_trader_xy(x: float, y: float, inventory_timeout_ms: int = 2500, inventory_step_ms: int = 5):
            yield from Yield.Movement.FollowPath([(x, y)])
            yield from Yield.wait(100)
            yield from Yield.Agents.InteractWithAgentXY(x, y)
            yield from Yield.wait(500)
            return (
                yield from Yield.Merchant._wait_for_trader_inventory(
                    timeout_ms=inventory_timeout_ms,
                    step_ms=inventory_step_ms,
                )
            )

        @staticmethod
        def SellMaterialsAtTrader(
            x: float,
            y: float,
            selected_models: set[int] | None = None,
            *,
            max_sell_quantity_per_item: int | None = None,
            deposit_threshold: int = 80_000,
            gold_to_keep: int = 10_000,
            inventory_timeout_ms: int = 2500,
            inventory_step_ms: int = 5,
            quote_timeout_ms: int = 250,
            quote_step_ms: int = 5,
            transaction_timeout_ms: int = 250,
            transaction_step_ms: int = 5,
            sale_delay_min_ms: int = 20,
            sale_delay_max_ms: int = 50,
        ):
            from ..Inventory import Inventory
            import random
            metrics = {
                "trader_loaded": 0,
                "batch_size": 10,
                "candidate_items": 0,
                "items_considered": 0,
                "sales_completed": 0,
                "quote_failures": 0,
                "transaction_timeouts": 0,
                "no_progress_breaks": 0,
                "gold_deposit_triggered": 0,
            }

            trader_items = yield from Yield.Merchant._interact_with_trader_xy(
                x,
                y,
                inventory_timeout_ms=inventory_timeout_ms,
                inventory_step_ms=inventory_step_ms,
            )
            if not trader_items:
                return metrics
            metrics["trader_loaded"] = 1
            batch_size = Yield.Merchant._get_trader_batch_size(trader_items)
            metrics["batch_size"] = int(batch_size)

            trader_models = {int(GLOBAL_CACHE.Item.GetModelID(item_id)) for item_id in trader_items}
            material_item_ids = Yield.Merchant._scan_material_item_ids(selected_models)
            metrics["candidate_items"] = int(len(material_item_ids))
            for item_id in material_item_ids:
                model_id = int(GLOBAL_CACHE.Item.GetModelID(item_id))
                if model_id not in trader_models:
                    continue

                metrics["items_considered"] = int(metrics["items_considered"]) + 1
                stack_quantity = int(GLOBAL_CACHE.Item.Properties.GetQuantity(item_id))
                quantity_cap = None if max_sell_quantity_per_item is None else max(0, int(max_sell_quantity_per_item))
                sold_quantity = 0
                while stack_quantity >= batch_size:
                    if quantity_cap is not None and sold_quantity >= quantity_cap:
                        break
                    if quantity_cap is not None and (sold_quantity + batch_size) > quantity_cap:
                        break
                    quoted_value = yield from Yield.Merchant._wait_for_quote(
                        GLOBAL_CACHE.Trading.Trader.RequestSellQuote,
                        item_id,
                        timeout_ms=quote_timeout_ms,
                        step_ms=quote_step_ms,
                    )
                    if quoted_value <= 0:
                        metrics["quote_failures"] = int(metrics["quote_failures"]) + 1
                        break

                    GLOBAL_CACHE.Trading.Trader.SellItem(item_id, quoted_value)
                    updated_quantity = yield from Yield.Merchant._wait_for_stack_quantity_drop(
                        item_id,
                        stack_quantity,
                        timeout_ms=transaction_timeout_ms,
                        step_ms=transaction_step_ms,
                    )
                    if updated_quantity >= stack_quantity:
                        metrics["transaction_timeouts"] = int(metrics["transaction_timeouts"]) + 1
                        metrics["no_progress_breaks"] = int(metrics["no_progress_breaks"]) + 1
                        break
                    sold_quantity += (stack_quantity - updated_quantity)
                    metrics["sales_completed"] = int(metrics["sales_completed"]) + 1
                    stack_quantity = updated_quantity
                    low = max(0, int(sale_delay_min_ms))
                    high = max(low, int(sale_delay_max_ms))
                    if high > 0:
                        yield from Yield.wait(random.randint(low, high))

            gold_on_character = int(GLOBAL_CACHE.Inventory.GetGoldOnCharacter())
            if gold_on_character > deposit_threshold:
                metrics["gold_deposit_triggered"] = 1
                Inventory.OpenXunlaiWindow()
                yield from Yield.wait(1000)
                yield from Yield.Items.DepositGold(gold_to_keep, log=False)
            return metrics

        @staticmethod
        def DepositMaterials(
            selected_models: set[int] | None = None,
            *,
            exact_quantity: int = 250,
            max_deposit_items: int | None = None,
            open_wait_ms: int = 1000,
            deposit_wait_ms: int = 40,
            max_passes: int = 2,
        ):
            from ..Inventory import Inventory
            metrics = {
                "opened_storage": 0,
                "passes_run": 0,
                "candidates_seen": 0,
                "deposited_items": 0,
            }

            if not Inventory.IsStorageOpen():
                Inventory.OpenXunlaiWindow()
                yield from Yield.wait(open_wait_ms)
                metrics["opened_storage"] = 1

            pass_count = max(1, int(max_passes))
            max_items = None if max_deposit_items is None else max(0, int(max_deposit_items))
            deposited = 0
            for _ in range(pass_count):
                metrics["passes_run"] = int(metrics["passes_run"]) + 1
                material_item_ids = Yield.Merchant._scan_material_item_ids(
                    selected_models,
                    exact_quantity=exact_quantity,
                )
                metrics["candidates_seen"] = int(metrics["candidates_seen"]) + int(len(material_item_ids))
                if not material_item_ids:
                    break
                for item_id in material_item_ids:
                    if max_items is not None and deposited >= max_items:
                        return metrics
                    GLOBAL_CACHE.Inventory.DepositItemToStorage(item_id)
                    yield from Yield.wait(deposit_wait_ms)
                    deposited += 1
                    metrics["deposited_items"] = int(metrics["deposited_items"]) + 1
            return metrics

        @staticmethod
        def BuyEctoplasm(
            x: float,
            y: float,
            *,
            use_storage_gold: bool = True,
            start_threshold: int = 900_000,
            stop_threshold: int = 500_000,
            open_wait_ms: int = 500,
            withdraw_wait_ms: int = 350,
            inventory_timeout_ms: int = 2000,
            inventory_step_ms: int = 10,
            quote_timeout_ms: int = 750,
            quote_step_ms: int = 10,
            transaction_timeout_ms: int = 750,
            transaction_step_ms: int = 10,
            max_character_gold: int = 100_000,
            max_no_progress_cycles: int = 3,
            max_ecto_to_buy: int | None = None,
        ):
            from ..Inventory import Inventory
            metrics = {
                "trader_loaded_cycles": 0,
                "withdrawals": 0,
                "bought_items": 0,
                "quote_failures": 0,
                "transaction_timeouts": 0,
                "no_progress_breaks": 0,
                "inventory_load_failures": 0,
            }

            if stop_threshold < 0:
                stop_threshold = 0
            if start_threshold < stop_threshold:
                start_threshold = stop_threshold

            ecto_model_id = int(ModelID.Glob_Of_Ectoplasm.value)
            character_gold = int(GLOBAL_CACHE.Inventory.GetGoldOnCharacter())
            storage_gold = int(GLOBAL_CACHE.Inventory.GetGoldInStorage())

            if use_storage_gold:
                if storage_gold <= start_threshold:
                    return metrics
            elif character_gold <= 0:
                return metrics

            max_to_buy = None if max_ecto_to_buy is None else max(0, int(max_ecto_to_buy))
            while True:
                if max_to_buy is not None and int(metrics["bought_items"]) >= max_to_buy:
                    break
                character_gold = int(GLOBAL_CACHE.Inventory.GetGoldOnCharacter())
                storage_gold = int(GLOBAL_CACHE.Inventory.GetGoldInStorage())
                if use_storage_gold:
                    if storage_gold <= stop_threshold:
                        break

                    withdraw_amount = min(max_character_gold - character_gold, storage_gold - stop_threshold)
                    if withdraw_amount > 0:
                        if not Inventory.IsStorageOpen():
                            Inventory.OpenXunlaiWindow()
                            yield from Yield.wait(open_wait_ms)
                        GLOBAL_CACHE.Inventory.WithdrawGold(int(withdraw_amount))
                        yield from Yield.wait(withdraw_wait_ms)
                        metrics["withdrawals"] = int(metrics["withdrawals"]) + 1
                elif character_gold <= 0:
                    break

                trader_items = yield from Yield.Merchant._interact_with_trader_xy(
                    x,
                    y,
                    inventory_timeout_ms=inventory_timeout_ms,
                    inventory_step_ms=inventory_step_ms,
                )
                if not trader_items:
                    metrics["inventory_load_failures"] = int(metrics["inventory_load_failures"]) + 1
                    break
                metrics["trader_loaded_cycles"] = int(metrics["trader_loaded_cycles"]) + 1

                trader_item_id = 0
                for candidate in trader_items:
                    if int(GLOBAL_CACHE.Item.GetModelID(candidate)) == ecto_model_id:
                        trader_item_id = int(candidate)
                        break
                if trader_item_id <= 0:
                    break

                batch_size = Yield.Merchant._get_trader_batch_size(trader_items)
                no_progress_cycles = 0
                while int(GLOBAL_CACHE.Inventory.GetGoldOnCharacter()) > 0:
                    if max_to_buy is not None and int(metrics["bought_items"]) >= max_to_buy:
                        return metrics
                    gold_before = int(GLOBAL_CACHE.Inventory.GetGoldOnCharacter())
                    quoted_value = yield from Yield.Merchant._wait_for_quote(
                        GLOBAL_CACHE.Trading.Trader.RequestQuote,
                        trader_item_id,
                        timeout_ms=quote_timeout_ms,
                        step_ms=quote_step_ms,
                    )
                    if quoted_value <= 0 or gold_before < quoted_value:
                        if quoted_value <= 0:
                            metrics["quote_failures"] = int(metrics["quote_failures"]) + 1
                        break

                    GLOBAL_CACHE.Trading.Trader.BuyItem(trader_item_id, quoted_value)
                    completed = yield from Yield.Merchant._wait_for_transaction(
                        timeout_ms=transaction_timeout_ms,
                        step_ms=transaction_step_ms,
                    )
                    if not completed:
                        metrics["transaction_timeouts"] = int(metrics["transaction_timeouts"]) + 1
                        break

                    gold_after = int(GLOBAL_CACHE.Inventory.GetGoldOnCharacter())
                    if gold_after >= gold_before:
                        no_progress_cycles += 1
                        if no_progress_cycles >= max_no_progress_cycles:
                            metrics["no_progress_breaks"] = int(metrics["no_progress_breaks"]) + 1
                            break
                    else:
                        no_progress_cycles = 0
                        metrics["bought_items"] = int(metrics["bought_items"]) + int(batch_size)

                if not use_storage_gold:
                    break
            return metrics

        @staticmethod
        def SellItems(item_array:list[int], log=False):
            
            if len(item_array) == 0:
                ActionQueueManager().ResetQueue("MERCHANT")
                return
            
            for item_id in item_array:
                quantity = GLOBAL_CACHE.Item.Properties.GetQuantity(item_id)
                value = GLOBAL_CACHE.Item.Properties.GetValue(item_id)
                cost = quantity * value
                GLOBAL_CACHE.Trading.Merchant.SellItem(item_id, cost)
                    
            while not ActionQueueManager().IsEmpty("MERCHANT"):
                yield from Yield.wait(50)
            
            if log:
                ConsoleLog("SellItems", f"Sold {len(item_array)} items.", Console.MessageType.Info)

        @staticmethod
        def BuyIDKits(kits_to_buy:int, log=False):
            from ..Py4GWcorelib import ActionQueueManager, ConsoleLog, Console
            from ..ItemArray import ItemArray
            
            if kits_to_buy <= 0:
                ActionQueueManager().ResetQueue("MERCHANT")
                return

            merchant_item_list = GLOBAL_CACHE.Trading.Merchant.GetOfferedItems()
            merchant_item_list = ItemArray.Filter.ByCondition(merchant_item_list, lambda item_id: GLOBAL_CACHE.Item.GetModelID(item_id) == 5899)

            if len(merchant_item_list) == 0:
                ActionQueueManager().ResetQueue("MERCHANT")
                return
            
            for i in range(kits_to_buy):
                item_id = merchant_item_list[0]
                value = GLOBAL_CACHE.Item.Properties.GetValue(item_id) * 2 # value reported is sell value not buy value
                GLOBAL_CACHE.Trading.Merchant.BuyItem(item_id, value)
                
            while not ActionQueueManager().IsEmpty("MERCHANT"):
                yield from Yield.wait(50)
                
            if log:
                ConsoleLog("BuyIDKits", f"Bought {kits_to_buy} ID Kits.", Console.MessageType.Info)

        @staticmethod
        def BuySalvageKits(kits_to_buy:int, log=False):
            from ..ItemArray import ItemArray
            from ..Py4GWcorelib import ActionQueueManager, ConsoleLog, Console
            
            if kits_to_buy <= 0:
                ActionQueueManager().ResetQueue("MERCHANT")
                return

            merchant_item_list = GLOBAL_CACHE.Trading.Merchant.GetOfferedItems()
            merchant_item_list = ItemArray.Filter.ByCondition(merchant_item_list, lambda item_id: GLOBAL_CACHE.Item.GetModelID(item_id) == 2992)

            if len(merchant_item_list) == 0:
                ActionQueueManager().ResetQueue("MERCHANT")
                return
            
            for i in range(kits_to_buy):
                item_id = merchant_item_list[0]
                value = GLOBAL_CACHE.Item.Properties.GetValue(item_id) * 2
                GLOBAL_CACHE.Trading.Merchant.BuyItem(item_id, value)
                
            while not ActionQueueManager().IsEmpty("MERCHANT"):
                yield from Yield.wait(50)
            
            if log:
                ConsoleLog("BuySalvageKits", f"Bought {kits_to_buy} Salvage Kits.", Console.MessageType.Info)
                
        @staticmethod
        def BuyMaterial(model_id: int):
            MODULE_NAME = "Inventory + Buy Material"

            def _is_material_trader():
                merchant_models = [
                    GLOBAL_CACHE.Item.GetModelID(item_id)
                    for item_id in GLOBAL_CACHE.Trading.Trader.GetOfferedItems()
                ]
                return ModelID.Wood_Plank.value in merchant_models

            def _get_minimum_quantity():
                return 10 if _is_material_trader() else 1

            required_quantity = _get_minimum_quantity()
            merchant_item_list = GLOBAL_CACHE.Trading.Trader.GetOfferedItems()

            # resolve merchant item ID from model_id
            item_id = None
            for candidate in merchant_item_list:
                if GLOBAL_CACHE.Item.GetModelID(candidate) == model_id:
                    item_id = candidate
                    break

            if item_id is None:
                ConsoleLog(MODULE_NAME, f"Model {model_id} not sold here.", Console.MessageType.Warning)
                return False

            # Request a single quote
            GLOBAL_CACHE.Trading.Trader.RequestQuote(item_id)

            while True:
                yield from Yield.wait(50)
                cost = GLOBAL_CACHE.Trading.Trader.GetQuotedValue()
                if cost >= 0:
                    break

            if cost == 0:
                ConsoleLog(MODULE_NAME, f"Item {item_id} has no price.", Console.MessageType.Warning)
                return False

            # Perform a single buy transaction
            GLOBAL_CACHE.Trading.Trader.BuyItem(item_id, cost)

            while True:
                yield from Yield.wait(50)
                if GLOBAL_CACHE.Trading.IsTransactionComplete():
                    break

            ConsoleLog(
                MODULE_NAME,
                f"Bought {required_quantity} units of model {model_id} for {cost} gold.",
                Console.MessageType.Success
            )
            return True
        
        @staticmethod
        def SellMaterial(model_id: int):
            MODULE_NAME = "Inventory + Sell Material"

            def _is_material_trader():
                merchant_models = [
                    GLOBAL_CACHE.Item.GetModelID(item_id)
                    for item_id in GLOBAL_CACHE.Trading.Trader.GetOfferedItems()
                ]
                return ModelID.Wood_Plank.value in merchant_models

            def _get_minimum_quantity():
                return 10 if _is_material_trader() else 1

            required_quantity = _get_minimum_quantity()
            merchant_item_list = GLOBAL_CACHE.Trading.Trader.GetOfferedItems()

            # resolve merchant item ID from model_id
            item_id = None
            for candidate in merchant_item_list:
                if GLOBAL_CACHE.Item.GetModelID(candidate) == model_id:
                    item_id = candidate
                    break

            if item_id is None:
                ConsoleLog(MODULE_NAME, f"Model {model_id} not sold here.", Console.MessageType.Warning)
                return False

            # Request a single quote
            # GLOBAL_CACHE.Trading.Trader.RequestQuote(item_id)
            GLOBAL_CACHE.Trading.Trader.RequestSellQuote(item_id)
            ConsoleLog(MODULE_NAME, f"Requested Sell Quote for item {item_id}.", Console.MessageType.Warning)

            while True:
                yield from Yield.wait(50)
                quoted_id = GLOBAL_CACHE.Trading.Trader.GetQuotedItemID()
                cost = GLOBAL_CACHE.Trading.Trader.GetQuotedValue()
                ConsoleLog(MODULE_NAME, f"Attempted to request sell quote for item {quoted_id}.", Console.MessageType.Warning)
                ConsoleLog(MODULE_NAME, f"Received sell quote for item {item_id} at cost: {cost}", Console.MessageType.Warning)
                if cost >= 0:
                    break

            if cost == 0:
                ConsoleLog(MODULE_NAME, f"Item {item_id} has no price.", Console.MessageType.Warning)
                return False

            # Perform a single buy transaction
            GLOBAL_CACHE.Trading.Trader.SellItem(item_id, cost)

            while True:
                yield from Yield.wait(50)
                if GLOBAL_CACHE.Trading.IsTransactionComplete():
                    break

            ConsoleLog(
                MODULE_NAME,
                f"Bought {required_quantity} units of model {model_id} for {cost} gold.",
                Console.MessageType.Success
            )
            return True



#region Items
    class Items:
        @staticmethod
        def GetItemNameByItemID(item_id):
            tree = BT.Items.GetItemNameByItemID(item_id)
            yield from _run_bt_tree(tree, throttle_ms=100)
            item_name = tree.blackboard.get("result", '')
            return item_name

        @staticmethod
        def _wait_for_salvage_materials_window(timeout_ms: int = 1200, poll_ms: int = 50, initial_wait_ms: int = 150):
            from ..UIManager import UIManager
            yield from Yield.wait(max(0, initial_wait_ms))

            parent_hash = 140452905
            yes_button_offsets = [6, 110, 6]
            waited_ms = 0

            while waited_ms < max(0, timeout_ms):
                salvage_materials_frame = UIManager.GetChildFrameID(parent_hash, yes_button_offsets)
                if salvage_materials_frame and UIManager.FrameExists(salvage_materials_frame):
                    yield from Yield.wait(max(0, poll_ms))
                    return True

                yield from Yield.wait(max(1, poll_ms))
                waited_ms += max(1, poll_ms)

            yield from Yield.wait(max(0, poll_ms))
            return False
            
        @staticmethod
        def _wait_for_empty_queue(queue_name:str, timeout_ms: Optional[int] = None, poll_ms: int = 50):
            from ..Py4GWcorelib import ActionQueueManager
            poll_ms = max(1, poll_ms)
            waited_ms = 0
            while not ActionQueueManager().IsEmpty(queue_name):
                if timeout_ms is not None and waited_ms >= max(0, timeout_ms):
                    ConsoleLog(
                        "Yield.Items",
                        f"Timed out waiting for queue '{queue_name}' to empty.",
                        Console.MessageType.Warning
                    )
                    return False
                yield from Yield.wait(poll_ms)
                waited_ms += poll_ms
            return True
        
        @staticmethod
        def _salvage_item(item_id):
            from ..Inventory import Inventory
            

            salvage_kit = GLOBAL_CACHE.Inventory.GetFirstSalvageKit()
            if salvage_kit == 0:
                ConsoleLog("SalvageItems", "No salvage kits found.", Console.MessageType.Warning)
                return
            Inventory.SalvageItem(item_id, salvage_kit)
            
        @staticmethod
        def SalvageItems(item_array:list[int], log=False):
            from ..Py4GWcorelib import ActionQueueManager, ConsoleLog, Console
            from ..Inventory import Inventory
            queue_wait_timeout_ms = 5000
            
            if len(item_array) == 0:
                ActionQueueManager().ResetQueue("SALVAGE")
                return
            
            for item_id in item_array:
                _,rarity = GLOBAL_CACHE.Item.Rarity.GetRarity(item_id)
                is_purple = rarity == "Purple"
                is_gold = rarity == "Gold"
                ActionQueueManager().AddAction("SALVAGE", Yield.Items._salvage_item, item_id)
                queue_drained = yield from Yield.Items._wait_for_empty_queue("SALVAGE", timeout_ms=queue_wait_timeout_ms)
                if not queue_drained:
                    ConsoleLog("SalvageItems", f"Timed out waiting for salvage queue after starting salvage (item_id={item_id}).", Console.MessageType.Warning)
                    continue
                
                if (is_purple or is_gold):
                    found_confirm_window = yield from Yield.Items._wait_for_salvage_materials_window()
                    if not found_confirm_window:
                        ConsoleLog("SalvageItems", f"Timed out waiting for salvage confirmation window (item_id={item_id}).", Console.MessageType.Warning)
                        continue
                    ActionQueueManager().AddAction("SALVAGE", Inventory.AcceptSalvageMaterialsWindow)
                    queue_drained = yield from Yield.Items._wait_for_empty_queue("SALVAGE", timeout_ms=queue_wait_timeout_ms)
                    if not queue_drained:
                        ConsoleLog("SalvageItems", f"Timed out waiting for salvage queue after confirmation (item_id={item_id}).", Console.MessageType.Warning)
                        continue
                    
                yield from Yield.wait(100)
                
            if log and len(item_array) > 0:
                ConsoleLog("SalvageItems", f"Salvaged {len(item_array)} items.", Console.MessageType.Info)     
                
        @staticmethod
        def _identify_item(item_id):
            from ..Inventory import Inventory
            

            id_kit = GLOBAL_CACHE.Inventory.GetFirstIDKit()
            if id_kit == 0:
                ConsoleLog("IdentifyItems", "No ID kits found.", Console.MessageType.Warning)
                return
            Inventory.IdentifyItem(item_id, id_kit)

        @staticmethod
        def IdentifyItems(item_array:list[int], log=False):
            from ..Py4GWcorelib import ActionQueueManager, ConsoleLog, Console
            if len(item_array) == 0:
                ActionQueueManager().ResetQueue("IDENTIFY")
                return
            
            for item_id in item_array:
                ActionQueueManager().AddAction("IDENTIFY",Yield.Items._identify_item, item_id)
                
            while not ActionQueueManager().IsEmpty("IDENTIFY"):
                yield from Yield.wait(350)
                
            if log and len(item_array) > 0:
                ConsoleLog("IdentifyItems", f"Identified {len(item_array)} items.", Console.MessageType.Info)
                
                
        @staticmethod
        def DepositItems(item_array:list[int], log=False):
            from ..Py4GWcorelib import ActionQueueManager, ConsoleLog, Console
            
            if len(item_array) == 0:
                ActionQueueManager().ResetQueue("ACTION")
                return
            
            total_items, total_capacity = GLOBAL_CACHE.Inventory.GetStorageSpace()
            free_slots = total_capacity - total_items
            
            if free_slots <= 0:
                return

            for item_id in item_array:
                GLOBAL_CACHE.Inventory.DepositItemToStorage(item_id)
                
            while not ActionQueueManager().IsEmpty("ACTION"):
                yield from Yield.wait(350)
                
            if log and len(item_array) > 0:
                ConsoleLog("DepositItems", f"Deposited {len(item_array)} items.", Console.MessageType.Info)
                
        @staticmethod
        def DepositGold(gold_amount_to_leave_on_character: int, log=False):
            gold_amount_on_character = GLOBAL_CACHE.Inventory.GetGoldOnCharacter()
            gold_amount_on_storage = GLOBAL_CACHE.Inventory.GetGoldInStorage()
            
            max_allowed_gold = 1_000_000  # Max storage limit
            available_space = max_allowed_gold - gold_amount_on_storage

            # Too much gold → deposit
            if gold_amount_on_character > gold_amount_to_leave_on_character:
                gold_to_deposit = gold_amount_on_character - gold_amount_to_leave_on_character
                gold_to_deposit = min(gold_to_deposit, available_space)

                if gold_to_deposit > 0:
                    GLOBAL_CACHE.Inventory.DepositGold(gold_to_deposit)
                    yield from Yield.wait(350)
                    if log:
                        ConsoleLog("DepositGold", f"Deposited {gold_to_deposit} gold.", Console.MessageType.Success)
                    return True

                if log:
                    ConsoleLog("DepositGold", "No gold deposited, storage full.", Console.MessageType.Warning)
                return False

            # Too little gold → withdraw
            elif gold_amount_on_character < gold_amount_to_leave_on_character:
                gold_needed = gold_amount_to_leave_on_character - gold_amount_on_character
                gold_to_withdraw = min(gold_needed, gold_amount_on_storage)

                if gold_to_withdraw > 0:
                    GLOBAL_CACHE.Inventory.WithdrawGold(gold_to_withdraw)
                    yield from Yield.wait(350)
                    if log:
                        ConsoleLog("DepositGold", f"Withdrew {gold_to_withdraw} gold.", Console.MessageType.Success)
                    return True

                if log:
                    ConsoleLog("DepositGold", "No gold withdrawn, storage empty.", Console.MessageType.Warning)
                return False

            # Already balanced
            if log:
                ConsoleLog("DepositGold", f"Gold already balanced at {gold_amount_to_leave_on_character}.", Console.MessageType.Info)
            return True


        @staticmethod
        def WithdrawGold(target_gold: int, deposit_all: bool = True, log: bool = False):
            """Ensure the character has exactly `target_gold` on hand.
            If deposit_all is True and the character has more than target_gold, the excess is deposited first.
            Then, if the character has less than target_gold, the shortfall is withdrawn from storage.
            """
            gold_on_char = GLOBAL_CACHE.Inventory.GetGoldOnCharacter()

            if deposit_all and gold_on_char > target_gold:
                to_deposit = gold_on_char - target_gold
                gold_in_storage = GLOBAL_CACHE.Inventory.GetGoldInStorage()
                available_space = 1_000_000 - gold_in_storage
                to_deposit = min(to_deposit, available_space)
                if to_deposit > 0:
                    GLOBAL_CACHE.Inventory.DepositGold(to_deposit)
                    yield from Yield.wait(350)
                    if log:
                        ConsoleLog("WithdrawGold", f"Deposited {to_deposit} gold (excess).", Console.MessageType.Info)
                    gold_on_char = GLOBAL_CACHE.Inventory.GetGoldOnCharacter()

            if gold_on_char < target_gold:
                to_withdraw = target_gold - gold_on_char
                gold_in_storage = GLOBAL_CACHE.Inventory.GetGoldInStorage()
                to_withdraw = min(to_withdraw, gold_in_storage)
                if to_withdraw > 0:
                    GLOBAL_CACHE.Inventory.WithdrawGold(to_withdraw)
                    yield from Yield.wait(350)
                    if log:
                        ConsoleLog("WithdrawGold", f"Withdrew {to_withdraw} gold.", Console.MessageType.Info)
                elif log:
                    ConsoleLog("WithdrawGold", "Not enough gold in storage to reach target.", Console.MessageType.Warning)

        @staticmethod
        def LootItems(item_array:list[int], log=False, progress_callback: Optional[Callable[[float], None]] = None, pickup_timeout:int=5000):
            from ..AgentArray import AgentArray
            from .Checks import Checks
            
            if len(item_array) == 0:
                return True
            
            yield from Yield.wait(1000)
            if not Checks.Map.MapValid():
                item_array.clear()
                ActionQueueManager().ResetAllQueues()
                return False
            
            total_items = len(item_array)
            while len (item_array) > 0:
                item_id = item_array.pop(0)
                if item_id == 0:
                    continue
                
                free_slots_in_inventory = GLOBAL_CACHE.Inventory.GetFreeSlotCount()
                if free_slots_in_inventory <= 0:
                    item_array.clear()
                    ActionQueueManager().ResetAllQueues()
                    return False
                
                if not Checks.Map.MapValid():
                    item_array.clear()
                    ActionQueueManager().ResetAllQueues()
                    return False
                
                if not Agent.IsValid(item_id):
                    continue
                
                item_x, item_y = Agent.GetXY(item_id)
                item_reached = yield from Yield.Movement.FollowPath([(item_x, item_y)], timeout=pickup_timeout)
                if not item_reached:
                    item_array.clear()
                    ActionQueueManager().ResetAllQueues()
                    return False
                
                if not Checks.Map.MapValid():
                    item_array.clear()
                    ActionQueueManager().ResetAllQueues()
                    return False
                if Agent.IsValid(item_id):
                    yield from Yield.Player.InteractAgent(item_id)
                    while True:
                        yield from Yield.wait(50)
                        live_items  = AgentArray.GetItemArray()
                        if item_id not in live_items :
                            break
                    
                if progress_callback and total_items > 0:
                    progress_callback(1 - len(item_array) / total_items)
                        
                        
            return True

        @staticmethod
        def LootItemsWithMaxAttempts(
            item_array: list[int],
            log: bool = False,
            progress_callback: Optional[Callable[[float], None]] = None,
            pickup_timeout: int = 5000,
            max_attempts: int = 5,
            attempts_timeout_seconds: int = 3,
        ):
            from ..AgentArray import AgentArray
            from .Checks import Checks

            if len(item_array) == 0:
                return []

            failed_items: list[int] = []
            total_items = len(item_array)

            while len(item_array) > 0:
                item_id = item_array.pop(0)
                if item_id == 0:
                    continue

                free_slots_in_inventory = GLOBAL_CACHE.Inventory.GetFreeSlotCount()
                if free_slots_in_inventory <= 0:
                    ConsoleLog("LootItems", "No free slots in inventory, stopping loot.", Console.MessageType.Warning)
                    ActionQueueManager().ResetAllQueues()
                    return failed_items + item_array

                if not Checks.Map.MapValid():
                    ActionQueueManager().ResetAllQueues()
                    return failed_items + item_array

                if not Agent.IsValid(item_id):
                    continue

                # Try to walk to item
                item_x, item_y = Agent.GetXY(item_id)
                item_reached = yield from Yield.Movement.FollowPath([(item_x, item_y)], timeout=pickup_timeout)
                if not item_reached:
                    ConsoleLog("LootItems", f"Failed to reach item {item_id}, skipping.", Console.MessageType.Warning)
                    failed_items.append(item_id)
                    continue

                if Agent.IsValid(item_id):
                    attempts = 0
                    picked_up = False

                    while attempts < max_attempts and not picked_up:
                        if Agent.IsValid(item_id):
                            yield from Yield.Player.InteractAgent(item_id)

                        for _ in range(attempts_timeout_seconds * 10):  # default 3s
                            yield from Yield.wait(100)
                            live_items = AgentArray.GetItemArray()
                            if item_id not in live_items:
                                picked_up = True
                                break

                        if not picked_up:
                            attempts += 1

                    if not picked_up:
                        ConsoleLog("Loot", f"Failed to pick up item {item_id} after {max_attempts} attempts.")
                        failed_items.append(item_id)

                if progress_callback and total_items > 0:
                    progress_callback(1 - len(item_array) / total_items)

            if log:
                ConsoleLog(
                    "LootItems",
                    f"Looted {total_items - len(failed_items)} items. Failed: {len(failed_items)}",
                    Console.MessageType.Info,
                )

            return failed_items

        @staticmethod
        def WithdrawItems(model_id:int, quantity:int) -> Generator[Any, Any, bool]:

            item_in_storage = GLOBAL_CACHE.Inventory.GetModelCountInStorage(model_id)
            if item_in_storage < quantity:
                return False

            items_withdrawn = GLOBAL_CACHE.Inventory.WithdrawItemFromStorageByModelID(model_id, quantity)
            yield from Yield.wait(500)
            if not items_withdrawn:
                return False

            return True

        @staticmethod
        def WithdrawUpTo(model_id: int, max_quantity: int) -> Generator[Any, Any, None]:
            """Withdraw up to max_quantity of model_id from storage. No-op if none available."""
            available = GLOBAL_CACHE.Inventory.GetModelCountInStorage(model_id)
            to_withdraw = min(available, max_quantity)
            if to_withdraw > 0:
                GLOBAL_CACHE.Inventory.WithdrawItemFromStorageByModelID(model_id, to_withdraw)
                yield from Yield.wait(500)

        @staticmethod
        def WithdrawFirstAvailable(model_ids: list, max_quantity: int) -> Generator[Any, Any, None]:
            """Withdraw up to max_quantity from the first model_id in the list that has stock in storage."""
            for model_id in model_ids:
                available = GLOBAL_CACHE.Inventory.GetModelCountInStorage(model_id)
                if available > 0:
                    to_withdraw = min(available, max_quantity)
                    GLOBAL_CACHE.Inventory.WithdrawItemFromStorageByModelID(model_id, to_withdraw)
                    yield from Yield.wait(500)
                    return

        @staticmethod
        def DepositAllInventory() -> Generator[Any, Any, None]:
            """Deposits all items from inventory bags (Backpack, Belt Pouch, Bag 1, Bag 2) to storage."""
            item_ids = GLOBAL_CACHE.Inventory.GetAllInventoryItemIds()
            for item_id in item_ids:
                GLOBAL_CACHE.Inventory.DepositItemToStorage(item_id)
                yield from Yield.wait(350)

        @staticmethod
        def RestockItems(model_id: int, desired_quantity: int) -> Generator[Any, Any, bool]:
            """
            Ensure we have `desired_quantity` of `model_id` in bags by withdrawing from storage.
            - Try exact need first.
            - If that fails, try withdrawing as much as possible (fallback = min(need, in_storage)).
            - Return True iff final bag count >= desired_quantity.
            """

            # Current bag count
            in_bags = GLOBAL_CACHE.Inventory.GetModelCount(model_id)
            if in_bags >= desired_quantity:
                return True

            need = desired_quantity - in_bags
            in_storage = GLOBAL_CACHE.Inventory.GetModelCountInStorage(model_id)

            if need <= 0 or in_storage <= 0:
                return False  # nothing needed or nothing in storage

            # 1) Try to withdraw exactly what's needed
            ok = GLOBAL_CACHE.Inventory.WithdrawItemFromStorageByModelID(model_id, need)
            yield from Yield.wait(250)

            # 2) If that failed, try fallback: as much as possible from storage
            if not ok:
                fallback_amount = min(need, in_storage)
                if fallback_amount > 0:
                    ok = GLOBAL_CACHE.Inventory.WithdrawItemFromStorageByModelID(model_id, fallback_amount)
                    yield from Yield.wait(250)

            # Re-check final bag count to determine success
            final_bags = GLOBAL_CACHE.Inventory.GetModelCount(model_id)
            return final_bags >= desired_quantity


        @staticmethod
        def CraftItem(output_model_id: int, 
                       cost: int,
                       trade_model_ids: list[int], 
                       quantity_list: list[int])-> Generator[Any, Any, bool]:
            
            # Align lists (no exceptions; clamp to shortest)
            k = min(len(trade_model_ids), len(quantity_list))
            if k == 0:
                return False
            trade_model_ids = trade_model_ids[:k]
            quantity_list   = quantity_list[:k]

            # Resolve each model -> first matching item in inventory
            trade_item_ids: list[int] = []
            for m in trade_model_ids:
                item_id = GLOBAL_CACHE.Inventory.GetFirstModelID(m)
                trade_item_ids.append(item_id or 0)

            # Bail if any required item is missing
            if any(i == 0 for i in trade_item_ids):
                return False

            # Find the crafter’s offered item that matches the desired output model
            target_item_id = 0
            for offered_item_id in GLOBAL_CACHE.Trading.Merchant.GetOfferedItems():
                if GLOBAL_CACHE.Item.GetModelID(offered_item_id) == output_model_id:
                    target_item_id = offered_item_id
                    break
            if target_item_id == 0:
                return False

            # Craft, then give a short yield
            GLOBAL_CACHE.Trading.Crafter.CraftItem(target_item_id, cost, trade_item_ids, quantity_list)
            yield from Yield.wait(500)
            return True
        
        @staticmethod
        def EquipItem(model_id: int) -> Generator[Any, Any, bool]:
            
            item_id = GLOBAL_CACHE.Inventory.GetFirstModelID(model_id)
            if item_id:
                GLOBAL_CACHE.Inventory.EquipItem(item_id, Player.GetAgentID())
                yield from Yield.wait(750)
            else:
                return False
            return True
        
        @staticmethod
        def DestroyItem(model_id: int) -> Generator[Any, Any, bool]:
            item_id = GLOBAL_CACHE.Inventory.GetFirstModelID(model_id)
            if item_id:
                GLOBAL_CACHE.Inventory.DestroyItem(item_id)
                yield from Yield.wait(600)
            else:
                return False
            return True
        
        @staticmethod
        def UseItem(model_id: int) -> Generator[Any, Any, bool]:
            item_id = GLOBAL_CACHE.Inventory.GetFirstModelID(model_id)
            if item_id:
                GLOBAL_CACHE.Inventory.UseItem(item_id)
                yield from Yield.wait(600)
            else:
                return False
            return True

        @staticmethod
        def SpawnBonusItems():
            Player.SendChatCommand("bonus")
            yield from Yield.wait(250)
            

#region Upkeepers
    class Upkeepers:

        ALCOHOL_ITEMS = [
            ModelID.Aged_Dwarven_Ale, ModelID.Aged_Hunters_Ale, ModelID.Bottle_Of_Grog,
            ModelID.Flask_Of_Firewater, ModelID.Keg_Of_Aged_Hunters_Ale,
            ModelID.Krytan_Brandy, ModelID.Spiked_Eggnog,
            ModelID.Bottle_Of_Rice_Wine, ModelID.Eggnog, ModelID.Dwarven_Ale,
            ModelID.Hard_Apple_Cider, ModelID.Hunters_Ale, ModelID.Bottle_Of_Juniberry_Gin,
            ModelID.Shamrock_Ale, ModelID.Bottle_Of_Vabbian_Wine, ModelID.Vial_Of_Absinthe,
            ModelID.Witchs_Brew, ModelID.Zehtukas_Jug,
        ]

        CITY_SPEED_ITEMS = [ModelID.Creme_Brulee, ModelID.Jar_Of_Honey, ModelID.Krytan_Lokum,
                            ModelID.Chocolate_Bunny, ModelID.Fruitcake, ModelID.Red_Bean_Cake,
                            ModelID.Mandragor_Root_Cake,
                            ModelID.Delicious_Cake, ModelID.Minitreat_Of_Purity,
                            ModelID.Sugary_Blue_Drink]
        
        CITY_SPEED_EFFECTS = [1860, #Sugar_Rush_short, // 1 minute
                              1323, #Sugar_Rush_medium, // 3 minute
                              1612, #Sugar_Rush_long, // 5 minute
                              3070, #Sugar_Rush_Agent_of_the_Mad_King
                              1916, #Sugar_Jolt_short, // 2 minute
                              1933, #Sugar_Jolt_long, // 5 minute
        ]

        MORALE_ITEMS = [
            ModelID.Honeycomb, ModelID.Rainbow_Candy_Cane, ModelID.Elixir_Of_Valor,
            ModelID.Pumpkin_Cookie, ModelID.Powerstone_Of_Courage, ModelID.Seal_Of_The_Dragon_Empire,
            ModelID.Four_Leaf_Clover, ModelID.Oath_Of_Purity, ModelID.Peppermint_Candy_Cane,
            ModelID.Refined_Jelly, ModelID.Shining_Blade_Ration, ModelID.Wintergreen_Candy_Cane,
        ]
        
        @staticmethod
        def Upkeep_Imp():
            from .Checks import Checks
            
            if ((not Checks.Map.MapValid())):
                yield from Yield.wait(500)
                return

            if (not Map.IsExplorable()):
                yield from Yield.wait(500)
                return

            if Agent.IsDead(Player.GetAgentID()):
                yield from Yield.wait(500)
                return

            level = Agent.GetLevel(Player.GetAgentID())

            if level >= 20:
                yield from Yield.wait(500)
                return

            summoning_stone = ModelID.Igneous_Summoning_Stone.value
            stone_id = GLOBAL_CACHE.Inventory.GetFirstModelID(summoning_stone)
            imp_effect_id = 2886
            has_effect = GLOBAL_CACHE.Effects.HasEffect(Player.GetAgentID(), imp_effect_id)

            imp_model_id = 513
            others = GLOBAL_CACHE.Party.GetOthers()
            cast_imp = True  # Assume we should cast

            for other in others:
                if Agent.GetModelID(other) == imp_model_id:
                    if not Agent.IsDead(other):
                        # Imp is alive — no need to cast
                        cast_imp = False
                    break  # Found the imp, no need to keep checking

            if stone_id and not has_effect and cast_imp:
                GLOBAL_CACHE.Inventory.UseItem(stone_id)
                yield from Yield.wait(500)

            yield from Yield.wait(500)
        
        @staticmethod
        def _upkeep_consumable(model_id:int, effect_name:str):
            from .Checks import Checks

            if ((not Checks.Map.MapValid())):
                yield from Yield.wait(500)
                return

            if (not Map.IsExplorable()):
                yield from Yield.wait(500)
                return

            if Agent.IsDead(Player.GetAgentID()):
                yield from Yield.wait(500)
                return

            effect_id = GLOBAL_CACHE.Skill.GetID(effect_name)
            if not GLOBAL_CACHE.Effects.HasEffect(Player.GetAgentID(), effect_id):
                item_id = GLOBAL_CACHE.Inventory.GetFirstModelID(model_id)
                if item_id:
                    GLOBAL_CACHE.Inventory.UseItem(item_id)
                    yield from Yield.wait(500)

            yield from Yield.wait(500)
     
        @staticmethod
        def Upkeep_ArmorOfSalvation():
            yield from Yield.Upkeepers._upkeep_consumable(ModelID.Armor_Of_Salvation, "Armor_of_Salvation_item_effect")  
        
        @staticmethod
        def Upkeep_EssenceOfCelerity():
            yield from Yield.Upkeepers._upkeep_consumable(ModelID.Essence_Of_Celerity, "Essence_of_Celerity_item_effect")
            
        @staticmethod
        def Upkeep_GrailOfMight():
            yield from Yield.Upkeepers._upkeep_consumable(ModelID.Grail_Of_Might, "Grail_of_Might_item_effect")
            
        @staticmethod
        def Upkeep_BlueRockCandy():
            yield from Yield.Upkeepers._upkeep_consumable(ModelID.Blue_Rock_Candy, "Blue_Rock_Candy_Rush")

        @staticmethod
        def Upkeep_GreenRockCandy():
            yield from Yield.Upkeepers._upkeep_consumable(ModelID.Green_Rock_Candy, "Green_Rock_Candy_Rush")
        
        @staticmethod
        def Upkeep_RedRockCandy():
            yield from Yield.Upkeepers._upkeep_consumable(ModelID.Red_Rock_Candy, "Red_Rock_Candy_Rush")
            
        @staticmethod
        def Upkeep_BirthdayCupcake():
            yield from Yield.Upkeepers._upkeep_consumable(ModelID.Birthday_Cupcake, "Birthday_Cupcake_skill")
      
        @staticmethod
        def Upkeep_SliceOfPumpkinPie():
            yield from Yield.Upkeepers._upkeep_consumable(ModelID.Slice_Of_Pumpkin_Pie, "Pie_Induced_Ecstasy")
            
        @staticmethod
        def Upkeep_BowlOfSkalefinSoup():
            yield from Yield.Upkeepers._upkeep_consumable(ModelID.Bowl_Of_Skalefin_Soup, "Skale_Vigor")
            
        @staticmethod
        def Upkeep_CandyApple():
            yield from Yield.Upkeepers._upkeep_consumable(ModelID.Candy_Apple, "Candy_Apple_skill")
            
        @staticmethod
        def Upkeep_CandyCorn():
            yield from Yield.Upkeepers._upkeep_consumable(ModelID.Candy_Corn, "Candy_Corn_skill")
        
        @staticmethod
        def Upkeep_DrakeKabob():
            yield from Yield.Upkeepers._upkeep_consumable(ModelID.Drake_Kabob, "Drake_Skin")
            
        @staticmethod
        def Upkeep_GoldenEgg():
            yield from Yield.Upkeepers._upkeep_consumable(ModelID.Golden_Egg, "Golden_Egg_skill")
            
        @staticmethod
        def Upkeep_PahnaiSalad():
            yield from Yield.Upkeepers._upkeep_consumable(ModelID.Pahnai_Salad, "Pahnai_Salad_item_effect")
            
        @staticmethod
        def Upkeep_WarSupplies():
            yield from Yield.Upkeepers._upkeep_consumable(ModelID.War_Supplies, "Well_Supplied")

        @staticmethod
        def Upkeep_Morale(target_morale=110):
            from .Checks import Checks

            # Party-wide morale items: affect all members, so check party morale too.
            # Player-only items must not be spent trying to raise party morale.
            PARTY_MORALE_MODELS = frozenset(
                m.value if hasattr(m, "value") else int(m)
                for m in (
                    ModelID.Honeycomb, ModelID.Rainbow_Candy_Cane,
                    ModelID.Elixir_Of_Valor, ModelID.Powerstone_Of_Courage,
                )
            )

            morale_models = [
                (m.value if hasattr(m, "value") else int(m))
                for m in Yield.Upkeepers.MORALE_ITEMS
            ]

            if not (Checks.Map.MapValid() and Map.IsExplorable()):
                yield from Yield.wait(500)
                return

            if Agent.IsDead(Player.GetAgentID()):
                yield from Yield.wait(500)
                return

            def _min_party_morale():
                try:
                    entries = GLOBAL_CACHE.Party.GetPartyMorale() or []
                    if not entries:
                        return Player.GetMorale()
                    return min(int(m) for _, m in entries)
                except Exception:
                    return Player.GetMorale()

            player_morale = Player.GetMorale()
            min_party = _min_party_morale()

            while player_morale < target_morale or min_party < target_morale:
                item_id = 0
                need_player_morale = player_morale < target_morale
                need_party_morale = min_party < target_morale

                # If any party member is below target, only party-wide morale items can help.
                if need_party_morale:
                    for model_id in morale_models:
                        if model_id in PARTY_MORALE_MODELS:
                            item_id = GLOBAL_CACHE.Inventory.GetFirstModelID(model_id)
                            if item_id:
                                break

                # Only use player-only morale items when the player still needs morale.
                if not item_id and need_player_morale:
                    for model_id in morale_models:
                        item_id = GLOBAL_CACHE.Inventory.GetFirstModelID(model_id)
                        if item_id:
                            break

                if not item_id:
                    # nothing to use right now
                    yield from Yield.wait(500)
                    break

                GLOBAL_CACHE.Inventory.UseItem(item_id)
                yield from Yield.wait(750)

                # Recalculate after use
                player_morale = Player.GetMorale()
                min_party = _min_party_morale()

            yield from Yield.wait(500)

        @staticmethod
        def Upkeep_Alcohol(target_alc_level=2, disable_drunk_effects=False):
            import PyEffects
            from .Checks import Checks
            alcohol_models = [
                (m.value if hasattr(m, "value") else int(m))
                for m in Yield.Upkeepers.ALCOHOL_ITEMS
            ]

            #if disable_drunk_effects:
            #    PyEffects.PyEffects.ApplyDrunkEffect(0, 0)

            
            if not (Checks.Map.MapValid() and Map.IsExplorable()):
                yield from Yield.wait(500)
                return

            if Agent.IsDead(Player.GetAgentID()):
                yield from Yield.wait(500)
                return

            while True:
                drunk_level = PyEffects.PyEffects.GetAlcoholLevel()
                if drunk_level >= target_alc_level:
                    yield from Yield.wait(500)
                    break

                item_id = 0
                for model_id in alcohol_models:
                    item_id = GLOBAL_CACHE.Inventory.GetFirstModelID(model_id)
                    if item_id:
                        break
                    
                if not item_id:
                    # nothing to use right now
                    yield from Yield.wait(500)
                    break

                GLOBAL_CACHE.Inventory.UseItem(item_id)
                yield from Yield.wait(500)
                
            yield from Yield.wait(500)
                
        @staticmethod
        def Upkeep_City_Speed():
            from .Checks import Checks

            # resolve enum -> int once
            item_models = [(m.value if hasattr(m, "value") else int(m)) for m in Yield.Upkeepers.CITY_SPEED_ITEMS]
            effect_ids = list(Yield.Upkeepers.CITY_SPEED_EFFECTS)
            player_id = lambda: Player.GetAgentID()
            period_ms: int = 1000


            # basic guards
            if not Checks.Map.MapValid():
                yield from Yield.wait(period_ms)
                return
            # City speed is for towns/outposts, so skip if explorable
            if not Map.IsOutpost():
                yield from Yield.wait(period_ms)
                return
            if Agent.IsDead(player_id()):
                yield from Yield.wait(period_ms)
                return

            # already have ANY acceptable city-speed effect?
            if any(GLOBAL_CACHE.Effects.HasEffect(player_id(), eid) for eid in effect_ids):
                yield from Yield.wait(period_ms)
                return

            # use first available item by priority
            used = False
            for mid in item_models:
                item_id = GLOBAL_CACHE.Inventory.GetFirstModelID(mid)
                if item_id:
                    GLOBAL_CACHE.Inventory.UseItem(item_id)
                    yield from Yield.wait(period_ms)
                    used = True
                    break

            # short cooldown either way
            yield from Yield.wait(period_ms)

#endregion

#region Keybinds
    class Keybinds:
        @staticmethod
        def PressKeybind(keybind_index:int, duration_ms:int=125, log=False):
            tree = BT.Keybinds.PressKeybind(keybind_index, duration_ms, log)
            yield from _run_bt_tree(tree)
  
        @staticmethod
        def TakeScreenshot(log=False):
            yield from Yield.Keybinds.PressKeybind(ControlAction.ControlAction_Screenshot.value, 75, log=log)
        
        @staticmethod
        def CallTarget(log=False):
            ActionQueueManager().AddAction("ACTION", Keystroke.PressAndReleaseCombo, [Key.Ctrl.value, Key.Space.value])
            yield from Yield.wait(100)
           
        #Panels
        @staticmethod
        def CloseAllPanels(log=False):
            yield from Yield.Keybinds.PressKeybind(ControlAction.ControlAction_CloseAllPanels.value, 75, log=log)
            
        @staticmethod
        def ToggleInventory(log=False):
            yield from Yield.Keybinds.PressKeybind(ControlAction.ControlAction_ToggleInventoryWindow.value, 75, log=log)
                
        @staticmethod
        def OpenScoreChart(log=False):
            yield from Yield.Keybinds.PressKeybind(ControlAction.ControlAction_OpenScoreChart.value, 75, log=log)
            
        @staticmethod
        def OpenTemplateManager(log=False):
            yield from Yield.Keybinds.PressKeybind(ControlAction.ControlAction_OpenTemplateManager.value, 75, log=log)
            
        @staticmethod
        def OpenSaveEquipmentTemplate(log=False):
            yield from Yield.Keybinds.PressKeybind(ControlAction.ControlAction_OpenSaveEquipmentTemplate.value, 75, log=log)
            
        @staticmethod
        def OpenSaveSkillTemplate(log=False):
            yield from Yield.Keybinds.PressKeybind(ControlAction.ControlAction_OpenSaveSkillTemplate.value, 75, log=log)
            
        @staticmethod
        def OpenParty(log=False):
            yield from Yield.Keybinds.PressKeybind(ControlAction.ControlAction_OpenParty.value, 75, log=log)
            
        @staticmethod
        def OpenGuild(log=False):
            yield from Yield.Keybinds.PressKeybind(ControlAction.ControlAction_OpenGuild.value, 75, log=log)
            
        @staticmethod
        def OpenFriends(log=False):
            yield from Yield.Keybinds.PressKeybind(ControlAction.ControlAction_OpenFriends.value, 75, log=log)
            
        @staticmethod
        def ToggleAllBags(log=False):
            yield from Yield.Keybinds.PressKeybind(ControlAction.ControlAction_ToggleAllBags.value, 75, log=log)
            
        @staticmethod
        def OpenMissionMap(log=False):
            yield from Yield.Keybinds.PressKeybind(ControlAction.ControlAction_OpenMissionMap.value, 75, log=log)
            
        @staticmethod
        def OpenBag2(log=False):
            yield from Yield.Keybinds.PressKeybind(ControlAction.ControlAction_OpenBag2.value, 75, log=log)
            
        @staticmethod
        def OpenBag1(log=False):
            yield from Yield.Keybinds.PressKeybind(ControlAction.ControlAction_OpenBag1.value, 75, log=log)
            
        @staticmethod
        def OpenBelt(log=False):
            yield from Yield.Keybinds.PressKeybind(ControlAction.ControlAction_OpenBelt.value, 75, log=log)
            
        @staticmethod
        def OpenBackpack(log=False):
            yield from Yield.Keybinds.PressKeybind(ControlAction.ControlAction_OpenBackpack.value, 75, log=log)
            
        @staticmethod
        def OpenSkillsAndAttributes(log=False):
            yield from Yield.Keybinds.PressKeybind(ControlAction.ControlAction_OpenSkillsAndAttributes.value, 75, log=log)
            
        @staticmethod
        def OpenQuestLog(log=False):
            yield from Yield.Keybinds.PressKeybind(ControlAction.ControlAction_OpenQuestLog.value, 75, log=log)
            
        @staticmethod
        def OpenWorldMap(log=False):
            yield from Yield.Keybinds.PressKeybind(ControlAction.ControlAction_OpenWorldMap.value, 75, log=log)
            
        @staticmethod
        def OpenHeroPanel(log=False):
            yield from Yield.Keybinds.PressKeybind(ControlAction.ControlAction_OpenHero.value, 75, log=log)    
        #weapon sets
        @staticmethod
        def CycleEquipment(log=False):
            yield from Yield.Keybinds.PressKeybind(ControlAction.ControlAction_CycleEquipment, 75, log=log)
            
        @staticmethod
        def ActivateWeaponSet(index:int, log=False):
            if index < 1 or index > 4:
                return
            yield from Yield.Keybinds.PressKeybind(ControlAction.ControlAction_ActivateWeaponSet1.value + (index - 1), 75, log=log)

        @staticmethod
        def DropBundle(log=False):
            yield from Yield.Keybinds.PressKeybind(ControlAction.ControlAction_DropItem, 75, log=log)
            
        @staticmethod
        def OpenChat(log=False):
            yield from Yield.Keybinds.PressKeybind(ControlAction.ControlAction_OpenChat, 75, log=log)
            
        @staticmethod
        def ReplyToChat(log=False):
            yield from Yield.Keybinds.PressKeybind(ControlAction.ControlAction_ChatReply, 75, log=log)
            
        @staticmethod
        def OpenAlliance(log=False):
            yield from Yield.Keybinds.PressKeybind(ControlAction.ControlAction_OpenAlliance, 75, log=log)
            
        #movement 
        @staticmethod   
        def MoveBackwards(duration_ms:int, log=False):
            yield from Yield.Keybinds.PressKeybind(ControlAction.ControlAction_MoveBackward.value, duration_ms, log=log)

        @staticmethod
        def MoveForwards(duration_ms:int, log=False):
            yield from Yield.Keybinds.PressKeybind(ControlAction.ControlAction_MoveForward.value, duration_ms, log=log)

        @staticmethod
        def StrafeLeft(duration_ms:int, log=False):
            yield from Yield.Keybinds.PressKeybind(ControlAction.ControlAction_StrafeLeft.value, duration_ms, log=log)
        @staticmethod
        def StrafeRight(duration_ms:int, log=False):
            yield from Yield.Keybinds.PressKeybind(ControlAction.ControlAction_StrafeRight.value, duration_ms, log=log)

        @staticmethod
        def TurnLeft(duration_ms:int, log=False):
            yield from Yield.Keybinds.PressKeybind(ControlAction.ControlAction_TurnLeft.value, duration_ms, log=log)
        @staticmethod
        def TurnRight(duration_ms:int, log=False):
            yield from Yield.Keybinds.PressKeybind(ControlAction.ControlAction_TurnRight.value, duration_ms, log=log)
            
        @staticmethod
        def ReverseCamera(log=False):
            yield from Yield.Keybinds.PressKeybind(ControlAction.ControlAction_ReverseCamera.value, 75, log=log)
            
        @staticmethod
        def CancelAction(log=False):
            yield from Yield.Keybinds.PressKeybind(ControlAction.ControlAction_CancelAction.value, 75, log=log)
            
        @staticmethod
        def Interact(log=False):
            yield from Yield.Keybinds.PressKeybind(ControlAction.ControlAction_Interact.value, 75, log=log)
            
        @staticmethod
        def ReverseDirection(log=False):
            yield from Yield.Keybinds.PressKeybind(ControlAction.ControlAction_ReverseDirection.value, 75, log=log)
            
        @staticmethod
        def AutoRun(log=False):
            yield from Yield.Keybinds.PressKeybind(ControlAction.ControlAction_Autorun.value, 75, log=log)
            
        @staticmethod
        def Follow(log=False):
            yield from Yield.Keybinds.PressKeybind(ControlAction.ControlAction_Follow.value, 75, log=log)
            
        #targeting     
        @staticmethod
        def TargetPartyMember(index:int, log=False):
            if index < 1 or index > 12:
                return
            yield from Yield.Keybinds.PressKeybind(ControlAction.ControlAction_TargetPartyMember1.value + (index - 1), 75, log=log)
        
        @staticmethod
        def TargetNearestItem(log=False):
            yield from Yield.Keybinds.PressKeybind(ControlAction.ControlAction_TargetNearestItem.value, 75, log=log)
            
        @staticmethod
        def TargetNextItem(log=False):
            yield from Yield.Keybinds.PressKeybind(ControlAction.ControlAction_TargetNextItem.value, 75, log=log)
            
        @staticmethod
        def TargetPreviousItem(log=False):
            yield from Yield.Keybinds.PressKeybind(ControlAction.ControlAction_TargetPreviousItem.value, 75, log=log)
            
        @staticmethod
        def TargetPartyMemberNext(log=False):
            yield from Yield.Keybinds.PressKeybind(ControlAction.ControlAction_TargetPartyMemberNext.value, 75, log=log)
            
        @staticmethod
        def TargetPartyMemberPrevious(log=False):
            yield from Yield.Keybinds.PressKeybind(ControlAction.ControlAction_TargetPartyMemberPrevious.value, 75, log=log)
            
        @staticmethod
        def TargetAllyNearest(log=False):
            yield from Yield.Keybinds.PressKeybind(ControlAction.ControlAction_TargetAllyNearest.value, 75, log=log)
            
        @staticmethod
        def ClearTarget(log=False):
            yield from Yield.Keybinds.PressKeybind(ControlAction.ControlAction_ClearTarget.value, 75, log=log)
            
        @staticmethod
        def TargetSelf(log=False):
            yield from Yield.Keybinds.PressKeybind(ControlAction.ControlAction_TargetSelf.value, 75, log=log)
            
        @staticmethod
        def TargetPriorityTarget(log=False):
            yield from Yield.Keybinds.PressKeybind(ControlAction.ControlAction_TargetPriorityTarget.value, 75, log=log)
            
        @staticmethod
        def TargetNearestEnemy(log=False):
            yield from Yield.Keybinds.PressKeybind(ControlAction.ControlAction_TargetNearestEnemy.value, 75, log=log)
            
        @staticmethod
        def TargetNextEnemy(log=False):
            yield from Yield.Keybinds.PressKeybind(ControlAction.ControlAction_TargetNextEnemy.value, 75, log=log)
            
        @staticmethod
        def TargetPreviousEnemy(log=False):
            yield from Yield.Keybinds.PressKeybind(ControlAction.ControlAction_TargetPreviousEnemy.value, 75, log=log)
            
        @staticmethod
        def ShowOthers(log=False):
            yield from Yield.Keybinds.PressKeybind(ControlAction.ControlAction_ShowOthers.value, 75, log=log)
            
        @staticmethod
        def ShowTargets(log=False):
            yield from Yield.Keybinds.PressKeybind(ControlAction.ControlAction_ShowTargets.value, 75, log=log)
            
        @staticmethod
        def CameraZoomIn(log=False):
            yield from Yield.Keybinds.PressKeybind(ControlAction.ControlAction_CameraZoomIn.value, 75, log=log)
            
        @staticmethod
        def CameraZoomOut(log=False):
            yield from Yield.Keybinds.PressKeybind(ControlAction.ControlAction_CameraZoomOut.value, 75, log=log)
            
        # Party / Hero commands
        @staticmethod
        def ClearPartyCommands(log=False):
            yield from Yield.Keybinds.PressKeybind(ControlAction.ControlAction_ClearPartyCommands.value, 75, log=log)
            
        @staticmethod
        def CommandParty(log=False):
            yield from Yield.Keybinds.PressKeybind(ControlAction.ControlAction_CommandParty.value, 75, log=log)
            
        @staticmethod
        def CommandHero(hero_index:int, log=False):
            if hero_index < 1 or hero_index > 7:
                return
            yield from Yield.Keybinds.PressKeybind(ControlAction.ControlAction_CommandHero1.value + (hero_index - 1), 75, log=log)
        
            
        @staticmethod
        def OpenHeroPetCommander(hero_index:int, log=False):
            if hero_index < 1 or hero_index > 7:
                return
            yield from Yield.Keybinds.PressKeybind(ControlAction.ControlAction_OpenHero1PetCommander.value + (hero_index - 1), 75, log=log)

        @staticmethod
        def OpenHeroCommander(hero_index:int, log=False):
            if hero_index < 1 or hero_index > 7:
                return
            yield from Yield.Keybinds.PressKeybind(ControlAction.ControlAction_OpenHeroCommander1.value + (hero_index - 1), 75, log=log)
            
        @staticmethod
        def HeroSkill(hero_index:int, skill_slot:int, log=False):
            party_size = GLOBAL_CACHE.Party.GetPartySize()
            if hero_index < 1 or hero_index > party_size:
                return
            # if skill_slot < 1 or skill_slot > 8:
            #     return
            yield from Yield.Keybinds.PressKeybind(ControlAction.ControlAction_Hero1Skill1.value + (hero_index - 1) * 8 + (skill_slot - 1), 75, log=log)
            
        @staticmethod
        def UseSkill(slot:int, log=False):
            if slot < 1 or slot > 8:
                return
            yield from Yield.Keybinds.PressKeybind(ControlAction.ControlAction_UseSkill1.value + (slot - 1), 75, log=log)

#region Character Reroll
    class RerollCharacter:
        @staticmethod
        def DeleteCharacter(character_name_to_delete: str, timeout_ms: int = 10000, log: bool = False) -> Generator[Any, Any, bool]:
            import PyImGui
            from ..UIManager import WindowFrames
            from ..Context import GWContext
            def _failed() -> bool:
                return timeout_timer.IsExpired() or not Map.Pregame.InCharacterSelectScreen()
            
            def _timeout_reached() -> bool:
                return timeout_timer.IsExpired()
            
            #A new character is not reported here until next login, so we skip this check
            """
            character_names = [char.player_name for char in Player.GetLoginCharacters()]
            if character_name_to_delete not in character_names:
                ConsoleLog("Reroll", f"Character '{character_name_to_delete}' not found among login characters.", Console.MessageType.Error, log)
                yield from Yield.wait(100)
                return False
            """
            
            timeout_timer = ThrottledTimer(timeout_ms)
            ActionQueueManager().ResetAllQueues()

            if not Map.Pregame.InCharacterSelectScreen():
                ConsoleLog("Reroll", "Logging out to character select screen...", Console.MessageType.Info, log)
                Map.Pregame.LogoutToCharacterSelect() 
                while not Map.Pregame.InCharacterSelectScreen() and not timeout_timer.IsExpired():
                    yield from Yield.wait(250)
                    
            if _timeout_reached():
                ConsoleLog("Reroll", "Timeout while waiting to reach character select screen.", Console.MessageType.Error, log)
                yield from Yield.wait(100)
                return False
                
            yield from Yield.wait(1000)
            pregame = GWContext.PreGame.GetContext()
            if pregame is None:
                ConsoleLog("Reroll", "Failed to retrieve pregame context.", Console.MessageType.Error, log)
                yield from Yield.wait(100)
                return False
            
            character_index = pregame.chars_list.index(character_name_to_delete) if character_name_to_delete in pregame.chars_list else -1
            last_known_index = pregame.chosen_character_index
            
            """if character_index == -1:
                ConsoleLog("Reroll", f"Character '{character_name_to_delete}' not found in character list.", Console.MessageType.Error)
                yield from Yield.wait(100)
                return False
            
            while last_known_index != character_index and not _failed(): 
                distance = character_index - last_known_index
                
                if distance != 0:
                    key = Key.RightArrow.value if distance > 0 else Key.LeftArrow.value
                    ConsoleLog("Reroll", f"Navigating {'Right' if distance > 0 else 'Left'} (Current: {last_known_index}, Target: {character_index})", Console.MessageType.Debug, log)
                    Keystroke.PressAndRelease(key)
                    yield from Yield.wait(250)
                    pregame = Player.GetPreGameContext()
                    last_known_index = pregame.index_1
                    
            if _failed():
                ConsoleLog("Reroll", "Timeout while navigating to target character.", Console.MessageType.Error, log)
                yield from Yield.wait(100)
                return False"""
            
            WindowFrames["DeleteCharacterButton"].FrameClick()
            yield from Yield.wait(750)
            PyImGui.set_clipboard_text(character_name_to_delete)
            Keystroke.PressAndReleaseCombo([Key.Ctrl.value, Key.V.value])
            yield from Yield.wait(750)
            WindowFrames["FinalDeleteCharacterButton"].FrameClick()
            yield from Yield.wait(750)
            
            return True
        
        @staticmethod
        def CreateCharacter(character_name: str,campaign_name: str, profession_name: str, timeout_ms: int = 15000, log: bool = False) -> Generator[Any, Any, None]:
            import PyImGui
            from ..UIManager import WindowFrames
            def _failed() -> bool:
                return timeout_timer.IsExpired() or not Map.Pregame.InCharacterSelectScreen()
            
            def _timeout_reached() -> bool:
                return timeout_timer.IsExpired()
            
            def _select_character_type(character_type: str) -> Generator[Any, Any, None]:
                if character_type == "PvE":
                    # Default, do nothing
                    yield from Yield.wait(100)
                    return
                
                Keystroke.PressAndRelease(Key.RightArrow.value)
                yield from Yield.wait(100)
            
            def _select_campaign(campaign_name: str) -> Generator[Any, Any, None]:
                repeats = 0
                if campaign_name == "Prophecies":
                    repeats = 1
                elif campaign_name == "Factions":
                    repeats = 2
                elif campaign_name == "Nightfall":
                    repeats = 0
                
                for _ in range(repeats):
                    Keystroke.PressAndRelease(Key.RightArrow.value)
                    yield from Yield.wait(100)
                yield from Yield.wait(100)
                
            def _select_profession(profession_name: str) -> Generator[Any, Any, None]:
                profession_map = {
                    "Warrior": 0,
                    "Ranger": 1,
                    "Monk": 2,
                    "Necromancer": 3,
                    "Mesmer": 4,
                    "Elementalist": 5,
                    "Assassin": 6,
                    "Ritualist": 7,
                    "Paragon": 6,
                    "Dervish": 7
                }
                
                target_index = profession_map.get(profession_name, -1)
                if target_index == -1:
                    ConsoleLog("Reroll", f"Unknown profession '{profession_name}'.", Console.MessageType.Error, log)
                    yield from Yield.wait(100)
                    return
                
                for _ in range(target_index):
                    Keystroke.PressAndRelease(Key.RightArrow.value)
                    yield from Yield.wait(100)
                yield from Yield.wait(100)
            
            """character_names = [char.player_name for char in Player.GetLoginCharacters()]
            if character_name in character_names:
                ConsoleLog("Reroll", f"Character '{character_name}' already exists among login characters.", Console.MessageType.Error, log)
                yield from Yield.wait(100)
                return  """
            
            yield from Yield.wait(1000)
            timeout_timer = ThrottledTimer(timeout_ms)
            ActionQueueManager().ResetAllQueues()

            if not Map.Pregame.InCharacterSelectScreen():
                ConsoleLog("Reroll", "Logging out to character select screen...", Console.MessageType.Info, log)
                Map.Pregame.LogoutToCharacterSelect() 
                while not Map.Pregame.InCharacterSelectScreen() and not timeout_timer.IsExpired():
                    yield from Yield.wait(250)
                    
            if _timeout_reached():
                ConsoleLog("Reroll", "Timeout while waiting to reach character select screen.", Console.MessageType.Error, log)
                yield from Yield.wait(100)
                return
                
            ConsoleLog("Reroll", "Creating new character...", Console.MessageType.Info, log)
            WindowFrames["CreateCharacterButton1"].FrameClick()
            yield from Yield.wait(500)
            WindowFrames["CreateCharacterButton2"].FrameClick()
            yield from Yield.wait(1000)
            # Select character type
            yield from _select_character_type("PvE")
            yield from Yield.wait(500)
            WindowFrames["CreateCharacterTypeNextButton"].FrameClick()
            yield from Yield.wait(1000)
            # Select campaign
            yield from _select_campaign(campaign_name)
            yield from Yield.wait(500)

            WindowFrames["CreateCharacterNextButtonGeneric"].FrameClick()
            yield from Yield.wait(1000)
            # Select profession
            yield from _select_profession(profession_name)
            yield from Yield.wait(500)
            WindowFrames["CreateCharacterNextButtonGeneric"].FrameClick()
            yield from Yield.wait(1000)
            #Selct Gender (default)
            WindowFrames["CreateCharacterNextButtonGeneric"].FrameClick()
            yield from Yield.wait(1000)
            #select Appearance (default)
            WindowFrames["CreateCharacterNextButtonGeneric"].FrameClick()
            yield from Yield.wait(1000)
            #sxelect Body (default)
            WindowFrames["CreateCharacterNextButtonGeneric"].FrameClick()
            yield from Yield.wait(1000)
            # Enter name and finalize     
            PyImGui.set_clipboard_text(character_name)
            Keystroke.PressAndReleaseCombo([Key.Ctrl.value, Key.V.value])    
            yield from Yield.wait(1000)
            WindowFrames["FinalCreateCharacterButton"].FrameClick()
            yield from Yield.wait(3000)
            
        @staticmethod
        def DeleteAndCreateCharacter(character_name_to_delete: str, new_character_name: str,
                             campaign_name: str, profession_name: str,
                             timeout_ms: int = 25000, log: bool = False) -> Generator[Any, Any, None]:
            result = yield from Yield.RerollCharacter.DeleteCharacter(character_name_to_delete, timeout_ms=timeout_ms//2, log=log)
            if not result:
                return
            yield from Yield.wait(1000)  # brief wait before creating new character
            yield from Yield.RerollCharacter.CreateCharacter(new_character_name, campaign_name, profession_name, timeout_ms=timeout_ms//2, log=log)    


                    
        @staticmethod
        def Reroll(target_character_name: str, timeout_ms: int = 10000, log: bool = False) -> Generator[Any, Any, None]:
            from ..Context import GWContext
            def _failed() -> bool:
                return timeout_timer.IsExpired() or not Map.Pregame.InCharacterSelectScreen()
            
            def _timeout_reached() -> bool:
                return timeout_timer.IsExpired()
            
            character_names = [char.player_name for char in Map.Pregame.GetAvailableCharacterList()]
            if target_character_name not in character_names:
                ConsoleLog("Reroll", f"Character '{target_character_name}' not found among login characters.", Console.MessageType.Error, log)
                yield from Yield.wait(100)
                return  
            
            if Player.GetName() == target_character_name and not Map.Pregame.InCharacterSelectScreen():
                ConsoleLog("Reroll", f"Already logged in as '{target_character_name}'. No reroll needed.", Console.MessageType.Info, log)
                yield from Yield.wait(100)
                return
            
            timeout_timer = ThrottledTimer(timeout_ms)
            ActionQueueManager().ResetAllQueues()

            if not Map.Pregame.InCharacterSelectScreen():
                ConsoleLog("Reroll", "Logging out to character select screen...", Console.MessageType.Info, log)
                Map.Pregame.LogoutToCharacterSelect() 
                while not Map.Pregame.InCharacterSelectScreen() and not timeout_timer.IsExpired():
                    yield from Yield.wait(250)
                    
            if _timeout_reached():
                ConsoleLog("Reroll", "Timeout while waiting to reach character select screen.", Console.MessageType.Error, log)
                yield from Yield.wait(100)
                return
                
            pregame = GWContext.PreGame.GetContext()
            if pregame is None:
                ConsoleLog("Reroll", "Failed to retrieve pregame context.", Console.MessageType.Error, log)
                yield from Yield.wait(100)
                return
            character_index = pregame.chars_list.index(target_character_name) if target_character_name in pregame.chars_list else -1
            last_known_index = pregame.chosen_character_index
            
            if character_index == -1:
                ConsoleLog("Reroll", f"Character '{target_character_name}' not found in character list.", Console.MessageType.Error)
                yield from Yield.wait(100)
                return
            
            while last_known_index != character_index and not _failed(): 
                distance = character_index - last_known_index
                
                if distance != 0:
                    key = Key.RightArrow.value if distance > 0 else Key.LeftArrow.value
                    ConsoleLog("Reroll", f"Navigating {'Right' if distance > 0 else 'Left'} (Current: {last_known_index}, Target: {character_index})", Console.MessageType.Debug, log)
                    Keystroke.PressAndRelease(key)
                    yield from Yield.wait(250)
                    pregame = GWContext.PreGame.GetContext()
                    if pregame is None:
                        ConsoleLog("Reroll", "Failed to retrieve pregame context.", Console.MessageType.Error, log)
                        yield from Yield.wait(100)
                        return
                    
                    last_known_index = pregame.chosen_character_index
                    
            if _failed():
                ConsoleLog("Reroll", "Timeout while navigating to target character.", Console.MessageType.Error, log)
                yield from Yield.wait(100)
                return
            
            ConsoleLog("Reroll", f"Selecting character '{target_character_name}'.", Console.MessageType.Info, log)
            Keystroke.PressAndRelease(Key.P.value)
            yield from Yield.wait(50)
            
            while not Map.IsMapReady() and not _timeout_reached():
                yield from Yield.wait(250)
                
            if _timeout_reached():
                ConsoleLog("Reroll", "Timeout reached while waiting for map to load.", Console.MessageType.Error)
                return
            
            ConsoleLog("Reroll", f"Successfully logged in as '{target_character_name}'.", Console.MessageType.Info, log)
            yield                  
