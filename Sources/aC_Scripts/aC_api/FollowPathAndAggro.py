from Py4GWCoreLib import *
class FollowPathAndAggro:
    def __init__(self, path_handler, follow_handler, aggro_range=2500, log_actions=False):
        self.path_handler       = path_handler
        self.follow_handler     = follow_handler
        self.aggro_range        = aggro_range
        self.log_actions        = log_actions

        # ── throttle scan state ──────────────────────────────────────
        self._last_scan_pos      = Player.GetXY()
        self._last_scanned_enemy = None
        self._scan_move_thresh   = aggro_range * 0.75
        self._scan_interval_ms   = 500
        self._scan_timer         = Timer()

        # ── move/target dedupe & reissue ───────────────────────────
        self._last_target_id     = None
        self._move_interval_ms   = 200
        self._move_timer         = Timer()

    def _find_nearest_enemy(self):
        my_pos = Player.GetXY()
        enemies = [
            e for e in AgentArray.GetEnemyArray()
            if Agent.IsAlive(e) and Utils.Distance(my_pos, Agent.GetXY(e)) <= self.aggro_range
        ]
        if not enemies:
            return None
        return AgentArray.Sort.ByDistance(enemies, my_pos)[0]

    def _throttled_scan(self):
        curr_pos = Player.GetXY()
        if (Utils.Distance(curr_pos, self._last_scan_pos) >= self._scan_move_thresh
            or self._scan_timer.HasElapsed(self._scan_interval_ms)):
            self._last_scanned_enemy = self._find_nearest_enemy()
            self._last_scan_pos      = curr_pos
            self._scan_timer.Reset()
        return self._last_scanned_enemy

    def _advance_to_next_point(self):
        if not self.follow_handler.is_following():
            next_point = self.path_handler.advance()
            if next_point:
                self.follow_handler.move_to_waypoint(*next_point)
        else:
            px, py = Player.GetXY()
            tx, ty = self._current_path_point
            if Utils.Distance((px, py), (tx, ty)) <= ARRIVAL_TOLERANCE:
                self.follow_handler._following = False
                self.follow_handler.arrived     = True

    def engage(self, enemy):
        # retarget only on change
        if enemy != self._last_target_id:
            Player.ChangeTarget(enemy)
            self._last_target_id = enemy
        # move at least every interval
        tx, ty = Agent.GetXY(enemy)
        if self._move_timer.HasElapsed(self._move_interval_ms):
            Player.Move(int(tx), int(ty))
            self._move_timer.Reset()
        self.follow_handler.update()

    def update(self):
        # path vs combat decision
        target = self._throttled_scan()
        if target:
            self.engage(target)
        else:
            self._advance_to_next_point()
            self.follow_handler.update()