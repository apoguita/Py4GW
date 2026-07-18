#region STATES
from typing import TYPE_CHECKING, List, Tuple, Optional, Callable

if TYPE_CHECKING:
    from Py4GWCoreLib.botting_src.helpers import BottingClass
    
from ..helpers_src.decorators import _yield_step
from typing import Any, Generator


#region MOVE
class _MOVE:
    def __init__(self, parent: "BottingClass"):
        self.parent = parent
        self._config = parent.config
        self._helpers = parent.helpers
        self._Events = parent.helpers.Events
        
    #region Coroutines (_coro_)
    def _coro_get_path_to(self, x: float, y: float) -> Generator[Any, Any, None]:
        from ...Pathing import AutoPathing
        from ...Player import Player
        path = yield from AutoPathing().get_path_to(x, y)
        self._config.path = path.copy()
        current_pos = Player.GetXY()
        self._config.path_to_draw.clear()
        self._config.path_to_draw.append((current_pos[0], current_pos[1]))
        self._config.path_to_draw.extend(path.copy())
        yield
        
    def _coro_follow_path_to(
        self,
        forced_timeout=-1,
        autopath: bool = True,
        fail_on_unmanaged: bool = True,
    ) -> Generator[Any, Any, bool]:
        from ...Routines import Routines
        from ...Map import Map
        from ...py4gwcorelib_src.Lootconfig_src import LootConfig
        from ...enums import Range
        from ...GlobalCache import GLOBAL_CACHE
        from ...Py4GWcorelib import ConsoleLog, Console
        
        log_actions = self._config.config_properties.log_actions.is_active()
        fsm = self.parent.config.FSM
        path = self._config.path
        initial_map_id = Map.GetMapID()
        initial_district = Map.GetDistrict()
        initial_region_id = Map.GetRegion()[0]
        initial_language_id = Map.GetLanguage()[0]
        initial_instance_uptime = Map.GetInstanceUptime()

        def map_transition_detected() -> bool:
            if Map.IsInCinematic():
                return True
            # Any map-invalid/loading phase should let movement step exit cleanly.
            if not Routines.Checks.Map.MapValid() or Map.IsMapLoading():
                return True

            if Map.GetMapID() != initial_map_id:
                return True
            if Map.GetDistrict() != initial_district:
                return True
            if Map.GetRegion()[0] != initial_region_id:
                return True
            if Map.GetLanguage()[0] != initial_language_id:
                return True

            current_instance_uptime = Map.GetInstanceUptime()
            # Instance timer resets on zoning, including same-map/district hops.
            if initial_instance_uptime > 0 and current_instance_uptime + 2000 < initial_instance_uptime:
                return True

            return False

        exit_condition = (
            (lambda: map_transition_detected() or Routines.Checks.Player.IsDead())
            if self._config.config_properties.halt_on_death.is_active()
            else map_transition_detected
        )

        # --- pause sources ---
        danger_pause = (
            self._config.pause_on_danger_fn
            if self._config.config_properties.pause_on_danger.is_active()
            else None
        )

        loot_config_enabled = self._config.upkeep.auto_loot.is_active()
        loot_singleton = LootConfig()

        def loot_pause() -> bool:
            if not loot_config_enabled:
                return False
            loot_array = loot_singleton.GetfilteredLootArray(
                distance=Range.Earshot.value,
                multibox_loot=True,
                allow_unasigned_loot=False,
            )
            return len(loot_array) > 0

        def fsm_pause() -> bool:
            return fsm.is_paused()

        # --- merged pause condition ---
        def pause_condition() -> bool:
            # Death should hard-pause movement so timeout windows do not
            # expire while waiting for revive.
            if Routines.Checks.Player.IsDead():
                return True
            if danger_pause and danger_pause():
                return True
            if loot_config_enabled and loot_pause():
                return True
            if Map.IsInCinematic():
                return True
            if fsm_pause():
                return True
            return False

        if forced_timeout > 0:
            f_timeout = forced_timeout
        else:
            f_timeout = self._config.config_properties.movement_timeout.get("value")
            
        success_movement = yield from Routines.Yield.Movement.FollowPath(
            path_points=path,
            custom_exit_condition=exit_condition,
            log=log_actions,
            custom_pause_fn=pause_condition,
            stop_on_party_wipe=self._config.config_properties.stop_on_party_wipe.is_active(),
            timeout=f_timeout,
            tolerance=self._config.config_properties.movement_tolerance.get("value"),
            map_transition_exit_success=True,
            autopath=autopath,
        )

        self._config.config_properties.follow_path_succeeded.set_now("value", success_movement)
        if not success_movement:
            if (Routines.Checks.Map.MapValid() and (Routines.Checks.Party.IsPartyWiped() or GLOBAL_CACHE.Party.IsPartyDefeated())):
                ConsoleLog("_follow_path", "halting movement due to party wipe", Console.MessageType.Warning, log=True)
                self._config.FSM.pause()
                return True  # continue FSM without halting

            if exit_condition():
                return True

            if fail_on_unmanaged:
                self._Events.on_unmanaged_fail()
            return False

        return True

    def _coro_set_path_to(self, path: List[Tuple[float, float]]) -> Generator[Any, Any, None]:
        self._config.path = path.copy()
        self._config.path_to_draw = path.copy()
        yield
        
    def _coro_to_model(self, model_id: int) -> Generator[Any, Any, bool]:
        from ...Routines import Routines
        from ...Agent import Agent
        agent_id = Routines.Agents.GetAgentIDByModelID(model_id)
        x,y = Agent.GetXY(agent_id)
        yield from self._coro_get_path_to(x, y)
        yield from self._coro_follow_path_to()
        return True

    def _coro_xy(
        self,
        x: float,
        y: float,
        step_name: str = "",
        forced_timeout: int = -1,
        fail_on_unmanaged: bool = True,
    ) -> Generator[Any, Any, bool]:
        if step_name == "":
            step_name = f"MoveTo_{self._config.get_counter('MOVE_TO')}"

        yield from self._coro_get_path_to(x, y)
        # pass forced_timeout through to the follow-path stage
        result = yield from self._coro_follow_path_to(
            forced_timeout,
            fail_on_unmanaged=fail_on_unmanaged,
        )
        return bool(result)
        
    def _coro_xy_and_exit_map(self, x: float, y: float, target_map_id: int = 0, target_map_name: str = "", step_name: str="") -> Generator[Any, Any, None]:
        if step_name == "":
            step_name = f"MoveAndExitMapTo_{self._config.get_counter('MOVE_AND_EXIT_MAP_TO')}"
            
        yield from self._coro_get_path_to(x, y)
        yield from self._coro_follow_path_to()
        yield from self.parent.Wait._coro_for_map_load(target_map_id=target_map_id, target_map_name=target_map_name)
        
    def _coro_xy_and_dialog(self, x: float, y: float, dialog_id: int, step_name: str="") -> Generator[Any, Any, None]:
        if step_name == "":
            step_name = f"MoveAndDialogTo_{self._config.get_counter('MOVE_AND_DIALOG_TO')}"
            
        yield from self._coro_get_path_to(x, y)
        yield from self._coro_follow_path_to()
        yield from self.parent.Dialogs._coro_at_xy(x, y, dialog_id)
    
    def _coro_xy_and_interact_npc(self, x: float, y: float, step_name: str="") -> Generator[Any, Any, None]:
        if step_name == "":
            step_name = f"MoveAndInteractNPC_{self._config.get_counter('MOVE_AND_INTERACT_NPC_TO')}"
            
        yield from self._coro_get_path_to(x, y)
        yield from self._coro_follow_path_to()
        yield from self.parent.Interact._coro_with_npc_at_xy(x, y)
        
    def _coro_xy_and_interact_gadget(self, x: float, y: float, step_name: str="") -> Generator[Any, Any, None]:
        if step_name == "":
            step_name = f"MoveAndInteractGadget_{self._config.get_counter('MOVE_AND_INTERACT_GADGET_TO')}"
            
        yield from self._coro_get_path_to(x, y)
        yield from self._coro_follow_path_to()
        yield from self.parent.Interact._coro_with_gadget_at_xy(x, y)
        
    def _coro_xy_and_interact_item(self, x: float, y: float, step_name: str="") -> Generator[Any, Any, None]:
        if step_name == "":
            step_name = f"MoveAndInteractItem_{self._config.get_counter('MOVE_AND_INTERACT_ITEM_TO')}"
            
        yield from self._coro_get_path_to(x, y)
        yield from self._coro_follow_path_to()
        yield from self.parent.Interact._coro_with_item_at_xy(x, y)


    def _coro_follow_path(self, path: List[Tuple[float, float]]) -> Generator[Any, Any, bool]:
        yield from self._coro_set_path_to(path)
        result = yield from self._coro_follow_path_to(autopath=False)
        return result

    def _coro_follow_auto_path(self, points: List[Tuple[float, float]], step_name: str = "") -> Generator[Any, Any, None]:
        """
        For each (x, y) target point, compute an autopath and follow it.
        Input format matches FollowPath, but each point is autpathed independently.
        """
        if step_name == "":
            step_name = f"FollowAutoPath_{self._config.get_counter('FOLLOW_AUTOPATH')}"

        for x, y in points:
            yield from self._coro_get_path_to(x, y)   # autopath to this target
            yield from self._coro_follow_path_to()       # then execute the path

    def _coro_follow_path_to_aggro(
        self,
        detection_radius: float = 1248.0,
        clear_radius: float = 2500.0,
        forced_timeout: int = -1,
        on_enemy_detected: "Optional[Callable[[float, float], None]]" = None,
    ) -> Generator[Any, Any, bool]:
        """
        Follow self._config.path while proactively scanning for and
        engaging enemies within *detection_radius* of the player.

        When enemies are found, computes an autopath to the nearest enemy
        via AutoPathing, follows it, engages, waits until the area is clear
        (no alive enemies within *clear_radius*), and resumes the path.

        If *on_enemy_detected* is provided, it is called with (x, y) of the
        first enemy each time a new engagement starts.
        
        After resume path completes, verify arrival at target waypoint
        before returning to aggro scan. This prevents zigzag behavior when enemies
        are detected during/after resume.
        """
        import random
        from ...Routines import Routines
        from ...Map import Map
        from ...py4gwcorelib_src.Lootconfig_src import LootConfig
        from ...enums import Range
        from ...GlobalCache import GLOBAL_CACHE
        from ...Py4GWcorelib import ConsoleLog, Console, Utils, ActionQueueManager
        from ...Player import Player
        from ...Agent import Agent
        from ...AgentArray import AgentArray
        from ...Pathing import AutoPathing
        from ...routines_src.yield_src.helpers import wait
        from ...routines_src.yield_src.movement import Movement as YieldMovement
        from ...routines_src.yield_src.player import Player as YieldPlayer

        log = self._config.config_properties.log_actions.is_active()
        fsm = self.parent.config.FSM
        path_points = list(self._config.path or [])
        initial_map_id = Map.GetMapID()
        initial_district = Map.GetDistrict()
        initial_region_id = Map.GetRegion()[0]
        initial_language_id = Map.GetLanguage()[0]
        initial_instance_uptime = Map.GetInstanceUptime()

        def _map_changed() -> bool:
            if Map.IsInCinematic():
                return True
            if not Routines.Checks.Map.MapValid() or Map.IsMapLoading():
                return True
            if Map.GetMapID() != initial_map_id:
                return True
            if Map.GetDistrict() != initial_district:
                return True
            if Map.GetRegion()[0] != initial_region_id:
                return True
            if Map.GetLanguage()[0] != initial_language_id:
                return True
            cur = Map.GetInstanceUptime()
            if initial_instance_uptime > 0 and cur + 2000 < initial_instance_uptime:
                return True
            return False

        exit_condition = (
            (lambda: _map_changed() or Routines.Checks.Player.IsDead())
            if self._config.config_properties.halt_on_death.is_active()
            else _map_changed
        )

        danger_pause = (
            self._config.pause_on_danger_fn
            if self._config.config_properties.pause_on_danger.is_active()
            else None
        )
        loot_enabled = self._config.upkeep.auto_loot.is_active()
        loot_cfg = LootConfig()

        def _loot_pause() -> bool:
            if not loot_enabled:
                return False
            return len(loot_cfg.GetfilteredLootArray(
                distance=Range.Earshot.value,
                multibox_loot=True,
                allow_unasigned_loot=False,
            )) > 0

        def _pause() -> bool:
            # Death should hard-pause movement so timeout windows do not
            # expire while waiting for revive.
            if Routines.Checks.Player.IsDead():
                return True
            if danger_pause and danger_pause():
                return True
            if loot_enabled and _loot_pause():
                return True
            if Map.IsInCinematic():
                return True
            if fsm.is_paused():
                return True
            return False

        def _alive_enemies(radius: float) -> list:
            px, py = Player.GetXY()
            arr = AgentArray.GetEnemyArray()
            arr = AgentArray.Filter.ByDistance(arr, (px, py), radius)
            arr = AgentArray.Filter.ByCondition(arr, lambda a: Agent.IsAlive(a))
            arr = AgentArray.Sort.ByDistance(arr, (px, py))
            return arr

        def _abort(msg: str) -> bool:
            ConsoleLog("FollowPathAggro", msg, Console.MessageType.Warning, log=True)
            ActionQueueManager().ResetAllQueues()
            return True

        def _pick_resume(current_idx: int) -> int:
            remaining = path_points[current_idx:]
            if not remaining:
                return current_idx
            pos = Player.GetXY()
            threshold = max(tolerance, 200.0)
            nearby = []
            best_rel = 0
            best_dist = float("inf")
            for ri, pt in enumerate(remaining):
                d = Utils.Distance(pos, pt)
                if d <= threshold:
                    nearby.append(ri)
                if d < best_dist:
                    best_dist = d
                    best_rel = ri
            if nearby:
                return current_idx + max(nearby)
            return current_idx + best_rel

        timeout = forced_timeout if forced_timeout > 0 else self._config.config_properties.movement_timeout.get("value")
        tolerance = self._config.config_properties.movement_tolerance.get("value")
        stop_on_wipe = self._config.config_properties.stop_on_party_wipe.is_active()
        total = len(path_points)

        if total == 0:
            ConsoleLog("FollowPathAggro", "Empty path -> success.", Console.MessageType.Warning, log=True)
            return True

        ConsoleLog("FollowPathAggro",
                    f"Starting path ({total} pts, detect={detection_radius:.0f}, clear={clear_radius:.0f}).",
                    Console.MessageType.Info, log=log)

        retries = 0
        max_retries = 30
        stuck_count = 0
        max_stuck = 2
        idx = 0

        while idx < len(path_points):
            tx, ty = path_points[idx]
            t0 = Utils.GetBaseTimestamp()

            if _map_changed():
                return _abort("Map changed before waypoint.")
            if stop_on_wipe and (Routines.Checks.Party.IsPartyWiped() or GLOBAL_CACHE.Party.IsPartyDefeated()):
                ConsoleLog("FollowPathAggro", "Party wiped.", Console.MessageType.Warning, log=True)
                ActionQueueManager().ResetAllQueues()
                return False

            Player.Move(tx, ty)
            yield from wait(250)
            if _map_changed():
                return _abort("Map changed after move issue.")

            prev_dist = Utils.Distance(Player.GetXY(), (tx, ty))

            while True:
                if _map_changed():
                    return _abort("Map changed mid-run.")
                if exit_condition():
                    ConsoleLog("FollowPathAggro", "Exit condition met.", Console.MessageType.Info, log=log)
                    return False
                if stop_on_wipe and (Routines.Checks.Party.IsPartyWiped() or GLOBAL_CACHE.Party.IsPartyDefeated()):
                    ConsoleLog("FollowPathAggro", "Party wiped.", Console.MessageType.Warning, log=True)
                    ActionQueueManager().ResetAllQueues()
                    return False

                if Agent.IsValid(Player.GetAgentID()) and Agent.IsCasting(Player.GetAgentID()):
                    yield from wait(750)
                    continue

                if _pause():
                    while _pause():
                        if _map_changed():
                            return _abort("Map changed while paused.")
                        if exit_condition():
                            return False
                        if stop_on_wipe and (Routines.Checks.Map.MapValid()
                            and (Routines.Checks.Party.IsPartyWiped() or GLOBAL_CACHE.Party.IsPartyDefeated())):
                            ConsoleLog("FollowPathAggro", "Party wiped during pause.", Console.MessageType.Warning, log=True)
                            ActionQueueManager().ResetAllQueues()
                            return False
                        t0 = Utils.GetBaseTimestamp()
                        yield from wait(750)

                    idx = _pick_resume(idx)
                    if idx >= len(path_points):
                        return True
                    tx, ty = path_points[idx]
                    Player.Move(tx, ty)
                    yield from wait(250)
                    if _map_changed():
                        return _abort("Map changed resuming after pause.")
                    prev_dist = Utils.Distance(Player.GetXY(), (tx, ty))
                    retries = 0
                    stuck_count = 0
                    continue

                # ══════════════════════════════════════════════════
                # AGGRO: enemy detection
                # ══════════════════════════════════════════════════
                if not Agent.IsDead(Player.GetAgentID()):
                    enemies = _alive_enemies(detection_radius)
                    if enemies:
                        first = enemies[0]
                        ex, ey = Agent.GetXY(first)
                        ConsoleLog("FollowPathAggro",
                                   f"{len(enemies)} enemies at ({ex:.0f},{ey:.0f}). Engaging.",
                                   Console.MessageType.Info, log=log)

                        # Notify callback of enemy position
                        if on_enemy_detected is not None:
                            on_enemy_detected(ex, ey)

                        current_target = first
                        engage_range = 1248.0  # Spellcast range

                        # ── chase loop: navigate to enemies via autopath ──
                        while True:
                            if _map_changed():
                                return _abort("Map changed during chase.")
                            if exit_condition():
                                return False
                            if Agent.IsDead(Player.GetAgentID()):
                                yield from wait(1000)
                                continue

                            # Re-scan: pick nearest alive enemy
                            alive = _alive_enemies(clear_radius)
                            if len(alive) == 0:
                                ConsoleLog("FollowPathAggro", "Area clear. Resuming.",
                                           Console.MessageType.Success, log=log)
                                break

                            current_target = alive[0]
                            target_x_e, target_y_e = Agent.GetXY(current_target)
                            dist_to_target = Utils.Distance(Player.GetXY(), (target_x_e, target_y_e))

                            # Already within engage range
                            if dist_to_target <= engage_range:
                                Player.ChangeTarget(current_target)
                                Player.Interact(current_target, False)
                                yield from wait(750)
                                continue

                            # Too far — compute autopath to enemy

                            # Pause for loot/danger before computing chase path
                            while _pause():
                                if _map_changed():
                                    return _abort("Map changed while paused before chase.")
                                if exit_condition():
                                    return False
                                yield from wait(750)

                            ConsoleLog("FollowPathAggro",
                                       f"Pathing to enemy {current_target} at ({target_x_e:.0f},{target_y_e:.0f}), dist={dist_to_target:.0f}.",
                                       Console.MessageType.Info, log=log)

                            cur_px, cur_py = Player.GetXY()
                            chase_path = yield from AutoPathing().get_path(
                                (cur_px, cur_py, 0),
                                (target_x_e, target_y_e, 0))

                            if not chase_path:
                                ConsoleLog("FollowPathAggro",
                                           "No autopath to enemy, using direct interact.",
                                           Console.MessageType.Warning, log=log)
                                Player.ChangeTarget(current_target)
                                Player.Interact(current_target, False)
                                yield from wait(750)
                                continue

                            chase_points = [(p[0], p[1]) for p in chase_path]

                            # ── mini follow-path: walk toward enemy ──
                            retarget = False
                            chase_stuck_count = 0
                            for cp_x, cp_y in chase_points:
                                if _map_changed():
                                    return _abort("Map changed during chase path.")
                                if exit_condition():
                                    return False

                                # Pause for loot/danger before moving to next chase waypoint
                                while _pause():
                                    if _map_changed():
                                        return _abort("Map changed while paused during chase.")
                                    if exit_condition():
                                        return False
                                    yield from wait(750)

                                Player.Move(cp_x, cp_y)
                                yield from wait(250)

                                chase_prev_dist = Utils.Distance(Player.GetXY(), (cp_x, cp_y))
                                chase_retries = 0

                                for _tick in range(120):  # ~30s max per waypoint
                                    if _map_changed():
                                        return _abort("Map changed during chase walk.")
                                    if Agent.IsDead(Player.GetAgentID()):
                                        break

                                    if not Agent.IsAlive(current_target):
                                        break
                                    dist_to_enemy = Utils.Distance(Player.GetXY(), Agent.GetXY(current_target))
                                    if dist_to_enemy <= engage_range:
                                        break
                                    cp_dist = Utils.Distance(Player.GetXY(), (cp_x, cp_y))
                                    if cp_dist <= tolerance:
                                        break

                                    # Check if a closer enemy appeared
                                    nearby = _alive_enemies(detection_radius)
                                    if nearby and nearby[0] != current_target:
                                        new_dist = Utils.Distance(Player.GetXY(), Agent.GetXY(nearby[0]))
                                        if new_dist < dist_to_enemy:
                                            ConsoleLog("FollowPathAggro",
                                                       f"Closer enemy detected during chase. Retargeting.",
                                                       Console.MessageType.Info, log=log)
                                            retarget = True
                                            break

                                    # Pause for loot/danger during chase walk
                                    if _pause():
                                        while _pause():
                                            if _map_changed():
                                                return _abort("Map changed while paused during chase walk.")
                                            if exit_condition():
                                                return False
                                            yield from wait(750)
                                        Player.Move(cp_x, cp_y)
                                        yield from wait(250)
                                        chase_prev_dist = Utils.Distance(Player.GetXY(), (cp_x, cp_y))
                                        chase_retries = 0
                                        continue

                                    # Stuck detection
                                    if _tick > 0:
                                        if not (cp_dist < chase_prev_dist):
                                            ox = random.uniform(-5, 5)
                                            oy = random.uniform(-5, 5)
                                            Player.Move(cp_x + ox, cp_y + oy)
                                            chase_retries += 1
                                            if chase_retries >= 20:
                                                YieldPlayer.SendChatCommand("stuck")
                                                ConsoleLog("FollowPathAggro", "Chase /stuck sent.", Console.MessageType.Warning, log=True)
                                                chase_retries = 0
                                                chase_stuck_count += 1
                                                if chase_stuck_count >= 2:
                                                    ConsoleLog("FollowPathAggro", "Chase strafe recovery.", Console.MessageType.Warning, log=True)
                                                    sx, sy = Player.GetXY()
                                                    yield from YieldMovement.WalkBackwards(1000)
                                                    if _map_changed():
                                                        return _abort("Map changed during chase recovery.")
                                                    yield from YieldMovement.StrafeLeft(1000)
                                                    if _map_changed():
                                                        return _abort("Map changed during chase recovery.")
                                                    lx, ly = Player.GetXY()
                                                    if Utils.Distance((sx, sy), (lx, ly)) < 50:
                                                        yield from YieldMovement.StrafeRight(1000)
                                                        if _map_changed():
                                                            return _abort("Map changed during chase recovery.")
                                                    chase_stuck_count = 0
                                        else:
                                            chase_retries = 0
                                            chase_stuck_count = 0
                                        chase_prev_dist = cp_dist

                                    if Agent.IsValid(Player.GetAgentID()) and Agent.IsCasting(Player.GetAgentID()):
                                        yield from wait(750)
                                        continue

                                    yield from wait(250)

                                if retarget:
                                    break

                                if Agent.IsDead(Player.GetAgentID()):
                                    break
                                if not Agent.IsAlive(current_target):
                                    break
                                dist_now = Utils.Distance(Player.GetXY(), Agent.GetXY(current_target))
                                if dist_now <= engage_range:
                                    Player.ChangeTarget(current_target)
                                    Player.Interact(current_target, False)
                                    break
                            # End of chase_points — re-scans at top of chase loop

                        # ── area clear: resume from best waypoint ──

                        # Pause for loot/danger at combat site before moving
                        while _pause():
                            if _map_changed():
                                return _abort("Map changed while looting after combat.")
                            if exit_condition():
                                return False
                            yield from wait(750)

                        new_idx = _pick_resume(idx)
                        if new_idx != idx:
                            ConsoleLog("FollowPathAggro",
                                       f"Resume wp {new_idx+1}/{len(path_points)} (was {idx+1}).",
                                       Console.MessageType.Info, log=log)
                            idx = new_idx
                        if idx >= len(path_points):
                            return True
                        tx, ty = path_points[idx]

                        # Autopath back to the resume waypoint
                        resume_px, resume_py = Player.GetXY()
                        resume_dist = Utils.Distance((resume_px, resume_py), (tx, ty))
                        if resume_dist > tolerance:
                            resume_path = yield from AutoPathing().get_path(
                                (resume_px, resume_py, 0), (tx, ty, 0))
                            if resume_path:
                                ConsoleLog("FollowPathAggro",
                                           f"Autopathing back to wp {idx+1} ({len(resume_path)} pts, dist={resume_dist:.0f}).",
                                           Console.MessageType.Info, log=log)
                                for rp_x, rp_y in [(p[0], p[1]) for p in resume_path]:
                                    if _map_changed():
                                        return _abort("Map changed during resume path.")
                                    if exit_condition():
                                        return False

                                    # Pause for loot/danger encountered on the way back
                                    while _pause():
                                        if _map_changed():
                                            return _abort("Map changed while paused during resume.")
                                        if exit_condition():
                                            return False
                                        yield from wait(750)

                                    Player.Move(rp_x, rp_y)
                                    yield from wait(250)
                                    resume_prev_dist = Utils.Distance(Player.GetXY(), (rp_x, rp_y))
                                    resume_retries = 0
                                    resume_stuck_count = 0

                                    for _tick in range(120):  # ~30s max per waypoint
                                        if _map_changed():
                                            return _abort("Map changed during resume walk.")
                                        rp_dist = Utils.Distance(Player.GetXY(), (rp_x, rp_y))
                                        if rp_dist <= tolerance:
                                            break
                                        # Pause for loot/danger during waypoint walk
                                        if _pause():
                                            while _pause():
                                                if _map_changed():
                                                    return _abort("Map changed while paused during resume walk.")
                                                if exit_condition():
                                                    return False
                                                yield from wait(750)
                                            Player.Move(rp_x, rp_y)
                                            yield from wait(250)
                                            resume_prev_dist = Utils.Distance(Player.GetXY(), (rp_x, rp_y))
                                            resume_retries = 0
                                            continue
                                        # Stuck detection
                                        if _tick > 0:
                                            if not (rp_dist < resume_prev_dist):
                                                ox = random.uniform(-5, 5)
                                                oy = random.uniform(-5, 5)
                                                Player.Move(rp_x + ox, rp_y + oy)
                                                resume_retries += 1
                                                if resume_retries >= 20:
                                                    YieldPlayer.SendChatCommand("stuck")
                                                    ConsoleLog("FollowPathAggro", "Resume /stuck sent.", Console.MessageType.Warning, log=True)
                                                    resume_retries = 0
                                                    resume_stuck_count += 1
                                                    if resume_stuck_count >= 2:
                                                        ConsoleLog("FollowPathAggro", "Resume strafe recovery.", Console.MessageType.Warning, log=True)
                                                        sx, sy = Player.GetXY()
                                                        yield from YieldMovement.WalkBackwards(1000)
                                                        if _map_changed():
                                                            return _abort("Map changed during resume recovery.")
                                                        yield from YieldMovement.StrafeLeft(1000)
                                                        if _map_changed():
                                                            return _abort("Map changed during resume recovery.")
                                                        lx, ly = Player.GetXY()
                                                        if Utils.Distance((sx, sy), (lx, ly)) < 50:
                                                            yield from YieldMovement.StrafeRight(1000)
                                                            if _map_changed():
                                                                return _abort("Map changed during resume recovery.")
                                                        resume_stuck_count = 0
                                            else:
                                                resume_retries = 0
                                                resume_stuck_count = 0
                                            resume_prev_dist = rp_dist
                                        if Agent.IsValid(Player.GetAgentID()) and Agent.IsCasting(Player.GetAgentID()):
                                            yield from wait(750)
                                            continue
                                        yield from wait(250)
                            else:
                                ConsoleLog("FollowPathAggro",
                                           f"No autopath for resume, using direct move.",
                                           Console.MessageType.Warning, log=log)
                                Player.Move(tx, ty)
                                yield from wait(250)
                        else:
                            Player.Move(tx, ty)
                            yield from wait(250)

                        # ╔═══════════════════════════════════════════════════════════╗
                        # ║ Check if we reached target waypoint after resume          ║
                        # ╚═══════════════════════════════════════════════════════════╝
                        final_dist = Utils.Distance(Player.GetXY(), (tx, ty))
                        ConsoleLog("FollowPathAggro",
                                   f"Resume complete. Distance to wp {idx+1}: {final_dist:.0f}.",
                                   Console.MessageType.Info, log=log)
                        
                        if final_dist <= tolerance:
                            # ✓ Successfully reached waypoint after resume
                            ConsoleLog("FollowPathAggro",
                                       f"Reached wp {idx+1}/{len(path_points)} after resume.",
                                       Console.MessageType.Success, log=log)
                            break  # ← EXIT inner while, advance to next waypoint
                        
                        # ✗ Did not reach waypoint yet, reset timers and retry
                        prev_dist = Utils.Distance(Player.GetXY(), (tx, ty))
                        retries = 0
                        stuck_count = 0
                        t0 = Utils.GetBaseTimestamp()
                        # ← CONTINUE inner while to retry reaching waypoint
                        continue

                # ══════════════════════════════════════════════════════════════════════════
                # PATH PROGRESS (standard FollowPath logic)
                # ══════════════════════════════════════════════════════════════════════════
                if _map_changed():
                    return _abort("Map changed before finishing waypoint.")

                elapsed = Utils.GetBaseTimestamp() - t0
                if timeout > 0 and elapsed > timeout:
                    ConsoleLog("FollowPathAggro", f"Timeout wp {idx+1}.", Console.MessageType.Warning, log=True)
                    return False

                cur_dist = Utils.Distance(Player.GetXY(), (tx, ty))

                if not (cur_dist < prev_dist):
                    ox = random.uniform(-5, 5)
                    oy = random.uniform(-5, 5)
                    Player.Move(tx + ox, ty + oy)
                    retries += 1
                    if retries >= max_retries:
                        YieldPlayer.SendChatCommand("stuck")
                        ConsoleLog("FollowPathAggro", "/stuck sent.", Console.MessageType.Warning, log=True)
                        retries = 0
                        stuck_count += 1
                        if stuck_count >= max_stuck:
                            ConsoleLog("FollowPathAggro", "Strafe recovery.", Console.MessageType.Warning, log=True)
                            sx, sy = Player.GetXY()
                            yield from YieldMovement.WalkBackwards(1000)
                            if _map_changed():
                                return _abort("Map changed during recovery.")
                            yield from YieldMovement.StrafeLeft(1000)
                            if _map_changed():
                                return _abort("Map changed during recovery.")
                            lx, ly = Player.GetXY()
                            if Utils.Distance((sx, sy), (lx, ly)) < 50:
                                yield from YieldMovement.StrafeRight(1000)
                                if _map_changed():
                                    return _abort("Map changed during recovery.")
                            stuck_count = 0
                else:
                    retries = 0
                    stuck_count = 0

                prev_dist = cur_dist

                if cur_dist <= tolerance:
                    ConsoleLog("FollowPathAggro", f"Reached wp {idx+1}/{len(path_points)}.",
                               Console.MessageType.Success, log=log)
                    break

                yield from wait(250)

            idx += 1

        ConsoleLog("FollowPathAggro", "Aggro path complete.", Console.MessageType.Success, log=log)
        return True

    def _coro_follow_auto_path_aggro(
        self,
        points: List[Tuple[float, float]],
        detection_radius: float = 1248.0,
        clear_radius: float = 2500.0,
        step_name: str = "",
        on_enemy_detected: "Optional[Callable[[float, float], None]]" = None,
    ) -> Generator[Any, Any, None]:
        """
        For each (x, y) in *points*, compute an autopath then follow it
        with aggressive enemy engagement (via _coro_follow_path_to_aggro).
        """
        if step_name == "":
            step_name = f"FollowAutoPathAggro_{self._config.get_counter('FOLLOW_AUTOPATH_AGGRO')}"

        for x, y in points:
            yield from self._coro_get_path_to(x, y)
            yield from self._coro_follow_path_to_aggro(
                detection_radius=detection_radius,
                clear_radius=clear_radius,
                on_enemy_detected=on_enemy_detected,
            )


            
    def _coro_follow_path_and_dialog(self, path: List[Tuple[float, float]], dialog_id: int, step_name: str="") -> Generator[Any, Any, None]:
        yield from self._coro_follow_path(path)
        last_point = path[-1]
        yield from self.parent.Dialogs._coro_at_xy(last_point[0], last_point[1], dialog_id)
        
    def _coro_follow_path_and_exit_map(self, path: List[Tuple[float, float]], target_map_id: int = 0, target_map_name: str = "", step_name: str="") -> Generator[Any, Any, None]:
        yield from self._coro_follow_path(path)
        yield from self.parent.Wait._coro_for_map_load(target_map_id=target_map_id, target_map_name=target_map_name)
        
    #region Yield Steps (ys_)
    @_yield_step(label="GetPathTo", counter_key="GET_PATH_TO")
    def ys_get_path_to(self, x: float, y: float):
        yield from self._coro_get_path_to(x, y)

    @_yield_step(label="SetPathTo", counter_key="SET_PATH_TO")
    def ys_set_path_to(self, path: List[Tuple[float, float]]):
        yield from self._coro_set_path_to(path)
        
    @_yield_step(label="FollowPath", counter_key="FOLLOW_PATH")
    def ys_follow_path(self, path):
        yield from self._coro_follow_path(path)
    
    @_yield_step(label="FollowAutoPath", counter_key="FOLLOW_AUTOPATH")
    def ys_follow_auto_path(self, points: List[Tuple[float, float]], step_name: str = "") -> Generator[Any, Any, None]:
        yield from self._coro_follow_auto_path(points, step_name)

    @_yield_step(label="FollowAutoPathAggro", counter_key="FOLLOW_AUTOPATH_AGGRO")
    def ys_follow_auto_path_aggro(
        self,
        points: List[Tuple[float, float]],
        detection_radius: float = 1248.0,
        clear_radius: float = 2500.0,
        step_name: str = "",
        on_enemy_detected: "Optional[Callable[[float, float], None]]" = None,
    ) -> Generator[Any, Any, None]:
        yield from self._coro_follow_auto_path_aggro(
            points, detection_radius, clear_radius, step_name,
            on_enemy_detected,
        )


    
    @_yield_step(label="ToModelID", counter_key="TO_MODEL_ID")
    def ys_to_model(self, model_id: int, step_name: str="") -> Generator[Any, Any, bool]:
        result = yield from self._coro_to_model(model_id)
        return result
    
    @_yield_step(label="XY", counter_key="MOVE_TO")
    def ys_xy(self, x: float, y: float, step_name: str="", forced_timeout: int = -1) -> Generator[Any, Any, None]:
        yield from self._coro_xy(x, y, step_name, forced_timeout)
        
    @_yield_step(label="XYAndExitMap", counter_key="MOVE_AND_EXIT_MAP_TO")
    def ys_xy_and_exit_map(self, x: float, y: float, target_map_id: int = 0, target_map_name: str = "", step_name: str="") -> Generator[Any, Any, None]:
        yield from self._coro_xy_and_exit_map(x, y, target_map_id, target_map_name, step_name)
        
    @_yield_step(label="XYAndDialog", counter_key="MOVE_AND_DIALOG_TO")
    def ys_xy_and_dialog(self, x: float, y: float, dialog_id: int, step_name: str="") -> Generator[Any, Any, None]:
        yield from self._coro_xy_and_dialog(x, y, dialog_id, step_name)
        
    @_yield_step(label="XYAndInteractNPC", counter_key="MOVE_AND_INTERACT_NPC_TO")
    def ys_xy_and_interact_npc(self, x: float, y: float, step_name: str="") -> Generator[Any, Any, None]:
        yield from self._coro_xy_and_interact_npc(x, y, step_name)

    @_yield_step(label="XYAndInteractGadget", counter_key="MOVE_AND_INTERACT_GADGET_TO")
    def ys_xy_and_interact_gadget(self, x: float, y: float, step_name: str="") -> Generator[Any, Any, None]:
        yield from self._coro_xy_and_interact_gadget(x, y, step_name)
    
    @_yield_step(label="XYAndInteractItem", counter_key="MOVE_AND_INTERACT_ITEM_TO")
    def ys_xy_and_interact_item(self, x: float, y: float, step_name: str="") -> Generator[Any, Any, None]:
        yield from self._coro_xy_and_interact_item(x, y, step_name)
        
    @_yield_step(label="FollowPathAndDialog", counter_key="FOLLOW_PATH_AND_DIALOG")
    def ys_follow_path_and_dialog(self, path: List[Tuple[float, float]], dialog_id: int, step_name: str="") -> Generator[Any, Any, None]:
        yield from self._coro_follow_path_and_dialog(path, dialog_id, step_name)
        
    @_yield_step(label="FollowPathAndExitMap", counter_key="FOLLOW_PATH_AND_EXIT_MAP")
    def ys_follow_path_and_exit_map(self, path: List[Tuple[float, float]], target_map_id: int = 0, target_map_name: str = "", step_name: str="") -> Generator[Any, Any, None]:
        yield from self._coro_follow_path_and_exit_map(path, target_map_id, target_map_name, step_name)


    #region public Helpers
    def XY(self, x:float, y:float, step_name: str="", forced_timeout: int = -1):
        # keep original calling style: step_name is optional; forced_timeout can be provided by name
        self.ys_xy(x, y, step_name=step_name, forced_timeout=forced_timeout)

    def XYAndDialog(self, x: float, y: float, dialog_id: int, step_name: str="") -> None:
        self.ys_xy_and_dialog(x, y, dialog_id, step_name=step_name)

    def XYAndInteractNPC(self, x: float, y: float, step_name: str="") -> None:
        self.ys_xy_and_interact_npc(x, y, step_name=step_name)

    def XYAndInteractGadget(self, x: float, y: float, step_name: str="") -> None:
        self.ys_xy_and_interact_gadget(x, y, step_name=step_name)

    def XYAndInteractItem(self, x: float, y: float, step_name: str="") -> None:
        self.ys_xy_and_interact_item(x, y, step_name=step_name)

    def XYAndExitMap(self, x: float, y: float, target_map_id: int = 0, target_map_name: str = "", step_name: str="") -> None:
        self.ys_xy_and_exit_map(x, y, target_map_id, target_map_name, step_name=step_name)

    def FollowPath(self, path: List[Tuple[float, float]], step_name: str="") -> None:
        self.ys_follow_path(path)

    def FollowPathAndDialog(self, path: List[Tuple[float, float]], dialog_id: int, step_name: str="") -> None:
        self.ys_follow_path_and_dialog(path, dialog_id, step_name=step_name)

    def FollowPathAndExitMap(self, path: List[Tuple[float, float]], target_map_id: int = 0, target_map_name: str = "", step_name: str="") -> None:
        self.ys_follow_path_and_exit_map(path, target_map_id, target_map_name, step_name=step_name)

    def FollowAutoPath(self, points: List[Tuple[float, float]], step_name: str = "") -> None:
        self.ys_follow_auto_path(points, step_name=step_name)

    def FollowAutoPathAggro(
        self,
        points: List[Tuple[float, float]],
        detection_radius: float = 1248.0,
        clear_radius: float = 2500.0,
        step_name: str = "",
        on_enemy_detected: "Optional[Callable[[float, float], None]]" = None,
    ) -> None:
        self.ys_follow_auto_path_aggro(
            points, detection_radius, clear_radius, step_name=step_name,
            on_enemy_detected=on_enemy_detected,
        )



    def FollowModel(self, model_id: int, follow_range: float, exit_condition: Optional[Callable[[], bool]] = lambda:False) -> None:
        self._helpers.Move.follow_model(model_id, follow_range, exit_condition)
        
    def ToModel(self, model_id: int, step_name: str = "") -> None:
        self.ys_to_model(model_id, step_name=step_name)
