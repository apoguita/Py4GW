from __future__ import annotations

from typing import List, Tuple, Callable, Optional, Generator, Any

from ...Agent import Agent
from ...Player import Player
from ...GlobalCache import GLOBAL_CACHE
from ...Py4GWcorelib import ConsoleLog, Console, Utils, ActionQueueManager
from ...enums_src.UI_enums import ControlAction
from .helpers import wait
from .keybinds import Keybinds
from .player import Player as YieldPlayer


class Movement:
    @staticmethod
    def StopMovement(log=False):
        yield from Movement.WalkBackwards(125, log=log)

    @staticmethod
    def WalkBackwards(duration_ms: int, log=False):
        yield from Keybinds.PressKeybind(ControlAction.ControlAction_MoveBackward.value, duration_ms, log=log)

    @staticmethod
    def WalkForwards(duration_ms: int, log=False):
        yield from Keybinds.PressKeybind(ControlAction.ControlAction_MoveForward.value, duration_ms, log=log)

    @staticmethod
    def StrafeLeft(duration_ms: int, log=False):
        yield from Keybinds.PressKeybind(ControlAction.ControlAction_StrafeLeft.value, duration_ms, log=log)

    @staticmethod
    def StrafeRight(duration_ms: int, log=False):
        yield from Keybinds.PressKeybind(ControlAction.ControlAction_StrafeRight.value, duration_ms, log=log)

    @staticmethod
    def TurnLeft(duration_ms: int, log=False):
        yield from Keybinds.PressKeybind(ControlAction.ControlAction_TurnLeft.value, duration_ms, log=log)

    @staticmethod
    def TurnRight(duration_ms: int, log=False):
        yield from Keybinds.PressKeybind(ControlAction.ControlAction_TurnRight.value, duration_ms, log=log)

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
        autopath: bool = True,
    ):
        import random
        from ..Checks import Checks
        from ...Pathing import AutoPathing
        from ...Map import Map as _Map

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

        def _rebuild_remaining_path(resume_index: int) -> Generator[Any, Any, tuple[int, bool]]:
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
                    ConsoleLog("FollowPath", "Party wiped detected, stopping all movement.", Console.MessageType.Warning, log=True)
                    ActionQueueManager().ResetAllQueues()
                    return False

            Player.Move(target_x, target_y)
            ConsoleLog("FollowPath", f"Issued move command to ({target_x}, {target_y}).", Console.MessageType.Debug, log=detailed_log)

            yield from wait(250)
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
                    ConsoleLog("FollowPath", "Party wiped detected, stopping all movement.", Console.MessageType.Warning, log=True)
                    ActionQueueManager().ResetAllQueues()
                    return False

                if Agent.IsValid(Player.GetAgentID()) and Agent.IsCasting(Player.GetAgentID()):
                    ConsoleLog("FollowPath", "Player casting detected, waiting 750ms...", Console.MessageType.Debug, log=detailed_log)

                    yield from wait(750)
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
                        yield from wait(750)

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

                        if autopath:
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
                        yield from wait(250)
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
                        YieldPlayer.SendChatCommand("stuck")
                        ConsoleLog("FollowPath", "No progress made, sending /stuck command.", Console.MessageType.Warning, log=log)

                        retries = 0
                        stuck_count += 1

                        # --- PixelStack recovery if too many stucks ---
                        if stuck_count >= max_stuck_commands:
                            ConsoleLog("FollowPath", "Too many stucks, performing strafe recovery.", Console.MessageType.Warning, log=log)

                            start_x, start_y = Player.GetXY()

                            # Backwards
                            yield from Movement.WalkBackwards(1000)
                            if not _map_still_valid():
                                return _abort_on_map_invalid("Map changed during backwards recovery.")
                            # Strafe left
                            yield from Movement.StrafeLeft(1000)
                            if not _map_still_valid():
                                return _abort_on_map_invalid("Map changed during strafe-left recovery.")

                            # Strafe right if no movement
                            left_x, left_y = Player.GetXY()
                            if Utils.Distance((start_x, start_y), (left_x, left_y)) < 50:
                                yield from Movement.StrafeRight(1000)
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

                yield from wait(250)

            #After reaching each point, report progress
            if progress_callback:
                progress_callback((idx + 1) / total_points)
                ConsoleLog("FollowPath", f"Progress callback: {((idx + 1) / total_points) * 100:.1f}% done.", Console.MessageType.Debug, log=detailed_log)

            idx += 1

        ConsoleLog("FollowPath", "Path traversal completed successfully.", Console.MessageType.Success, log=log)
        return True
