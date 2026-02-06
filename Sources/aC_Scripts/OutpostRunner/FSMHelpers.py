from Py4GWCoreLib import *
from Sources.aC_Scripts.OutpostRunner.map_loader import load_map_data
from Py4GWCoreLib import Routines
from Py4GWCoreLib.py4gwcorelib_src.WidgetManager import get_widget_handler
import math
import time

cached_enabled_widgets = []  # cache for later restore

ALWAYS_ENABLED_WIDGETS = [
    "Skip Cinematics",
    "Titles",
    "Environment Upkeeper",
    "Messaging"
]

class OutpostRunnerFSMHelpers:
    def __init__(self):
        self.current_map_data = None
        self.current_path_index = 0
        self.last_valid_next_point = None
        self.followxy = Routines.Movement.FollowXY()
        self._dumped_segments = set()

    def load_map_script(self, script_name):
        """
        Given a chain entry like:
            "Eye_Of_The_North__1_Eotn_To_Gunnars"
        (note the DOUBLE-underscore between region and run),
        split it properly and delegate to map_loader.
        """
        # split on the double-underscore delimiter
        if "__" in script_name:
            region, run = script_name.split("__", 1)
        else:
            # fallback (shouldn't happen with our UI)
            region, run = script_name.split("_", 1)

        # now load the Python file at maps/<region>/<run>.py
        data = load_map_data(region, run)
        self.current_map_data = data
        return {
            "outpost_path":     data["outpost_path"],
            "segments":         data["segments"],
            "ids":              data["ids"],
        }

    @staticmethod
    def travel_to_outpost(outpost_id):
        if Map.IsMapIDMatch(Map.GetMapID(), outpost_id):
            ConsoleLog("OutpostRunnerFSM", "Already at outpost. Skipping travel.", Console.MessageType.Info)
            return

        ConsoleLog("OutpostRunnerFSM", f"Initiating safe travel to outpost ID {outpost_id}")
        if Map.IsExplorable():
            # === STEP 1: Broadcast resign command to other accounts ===
            accounts = GLOBAL_CACHE.ShMem.GetAllAccountData()
            sender_email = Player.GetAccountEmail()
            for account in accounts:
                ConsoleLog("OutpostRunnerFSM", f"Resigning account: {account.AccountEmail}")
                GLOBAL_CACHE.ShMem.SendMessage(sender_email, account.AccountEmail, SharedCommandType.Resign, (0, 0, 0, 0))
            # === STEP 2: Wait for defeat to trigger Return To Outpost ===
            timeout = 20
            start_time = time.time()

            while time.time() - start_time < timeout:
                if (Map.IsMapReady() and GLOBAL_CACHE.Party.IsPartyLoaded() and Map.IsExplorable() and GLOBAL_CACHE.Party.IsPartyDefeated()):
                    GLOBAL_CACHE.Party.ReturnToOutpost()
                    break

                yield from Routines.Yield.wait(500)
            else:
                ConsoleLog("OutpostRunnerFSM", "Resign return timed out. Stopping bot.", Console.MessageType.Error)
                return

            # === STEP 3: Wait for outpost map to load ===
            timeout = 20
            start_time = time.time()

            while time.time() - start_time < timeout:
                if Routines.Checks.Map.MapValid() and Map.IsOutpost():
                    ConsoleLog("OutpostRunnerFSM", "Returned to outpost. Proceeding to travel...")
                    break

                yield from Routines.Yield.wait(500)
            else:
                ConsoleLog("OutpostRunnerFSM", "Failed to load outpost. Aborting travel.", Console.MessageType.Error)
                return

        # === STEP 4: Perform actual outpost travel ===
        ConsoleLog("OutpostRunnerFSM", f"Traveling to outpost ID {outpost_id}")
        yield from Routines.Yield.Map.TravelToOutpost(outpost_id)

    def wait_for_map_load(self, expected_map_id, timeout=15000):
        """Wait until we’re in the expected map."""
        return Routines.Yield.Map.WaitforMapLoad(expected_map_id, timeout=timeout)

    def follow_path(self, path_coords):
        """Follow a path of coordinates using proper waypoint traversal."""
        if not path_coords:
            # Empty path - this is typically the final segment (destination outpost)
            # Just confirm we're on the correct map and return
            if self.current_map_data:
                segments = self.current_map_data.get("segments", [])
                if segments and len(segments) > 0:
                    last_seg = segments[-1]
                    if not last_seg.get("path"):
                        # This IS the final segment - check if we're on the destination outpost
                        final_map_id = last_seg.get("map_id")
                        try:
                            current_map = Map.GetMapID()
                            if Map.IsMapIDMatch(current_map, final_map_id):
                                # Already on the destination outpost - done with this run
                                ConsoleLog("OutpostRunnerFSM", f"★★★ FINAL SEGMENT CONFIRMED: Arrived at outpost map {final_map_id} ★★★", Console.MessageType.Info)
                                self.followxy.reset()
                                return
                            else:
                                # Not yet on destination, wait for transition
                                ConsoleLog("OutpostRunnerFSM", f"★★★ FINAL SEGMENT: Currently on map {current_map}, waiting for transition to outpost {final_map_id}...", Console.MessageType.Info)
                                
                                transition_timeout = time.time() + 15
                                last_check = time.time()
                                
                                while time.time() < transition_timeout:
                                    current_time = time.time()
                                    if current_time - last_check >= 0.5:
                                        last_check = current_time
                                        try:
                                            current_map = Map.GetMapID()
                                            if Map.IsMapIDMatch(current_map, final_map_id):
                                                # Arrived at destination
                                                ConsoleLog("OutpostRunnerFSM", f"★★★ FINAL SEGMENT COMPLETE: Arrived at outpost {final_map_id} ★★★", Console.MessageType.Info)
                                                self.followxy.reset()
                                                return
                                        except Exception:
                                            pass
                                    
                                    yield from Routines.Yield.wait(100)
                                
                                # Timeout
                                ConsoleLog("OutpostRunnerFSM", f"[PORTAL] Timeout waiting for final segment (15s). Continuing...", Console.MessageType.Warning)
                                return
                        except Exception:
                            pass
            
            ConsoleLog("OutpostRunnerFSM", "Empty path with no segment data; skipping", Console.MessageType.Info)
            yield from Routines.Yield.wait(100)
            return
        # Determine expected map id and segment index for these path coordinates (if available)
        expected_map_id = None
        expected_seg_index = None
        is_outpost_path = False
        if self.current_map_data:
            ids = self.current_map_data.get("ids", {})
            # outpost path belongs to the outpost id
            outpost_path = self.current_map_data.get("outpost_path")
            
            # Helper function: compare paths element-by-element (handles floating point precision)
            def paths_equal(path1, path2):
                if not path1 or not path2 or len(path1) != len(path2):
                    return False
                for p1, p2 in zip(path1, path2):
                    if not isinstance(p1, (list, tuple)) or not isinstance(p2, (list, tuple)):
                        return False
                    if len(p1) < 2 or len(p2) < 2:
                        return False
                    # Compare with small tolerance for floating point
                    if abs(p1[0] - p2[0]) > 0.01 or abs(p1[1] - p2[1]) > 0.01:
                        return False
                return True
            
            if outpost_path and path_coords and paths_equal(outpost_path, path_coords):
                expected_map_id = ids.get("outpost_id")
                expected_seg_index = -1
                is_outpost_path = True
                ConsoleLog("OutpostRunnerFSM", f"[SEGMENT MATCH] Matched OUTPOST_PATH with expected_map_id={expected_map_id}", Console.MessageType.Info)
            else:
                # Try to match segment paths
                segments = self.current_map_data.get("segments", [])
                matched = False
                
                if path_coords and len(path_coords) > 0:
                    # Match by exact path comparison first
                    for si, seg in enumerate(segments):
                        seg_path = seg.get("path", [])
                        if seg_path and paths_equal(seg_path, path_coords):
                            expected_map_id = seg.get("map_id")
                            expected_seg_index = si
                            matched = True
                            ConsoleLog("OutpostRunnerFSM", f"[SEGMENT MATCH] Matched segment {si} with map_id={expected_map_id}", Console.MessageType.Info)
                            break
                
                # Fallback: match by path length and first/last points
                if not matched and path_coords:
                    for si, seg in enumerate(segments):
                        seg_path = seg.get("path", [])
                        if seg_path and len(seg_path) == len(path_coords):
                            # Compare first and last points
                            if len(path_coords) > 0 and len(seg_path) > 0:
                                first_match = (abs(seg_path[0][0] - path_coords[0][0]) < 0.01 and 
                                             abs(seg_path[0][1] - path_coords[0][1]) < 0.01)
                                last_match = (abs(seg_path[-1][0] - path_coords[-1][0]) < 0.01 and 
                                            abs(seg_path[-1][1] - path_coords[-1][1]) < 0.01)
                                if first_match and last_match:
                                    expected_map_id = seg.get("map_id")
                                    expected_seg_index = si
                                    matched = True
                                    ConsoleLog("OutpostRunnerFSM", f"[SEGMENT MATCH FALLBACK] Matched segment {si} by first/last points, map_id={expected_map_id}", Console.MessageType.Warning)
                                    break
                
                # Last resort: match by path length alone
                if not matched and path_coords:
                    for si, seg in enumerate(segments):
                        seg_path = seg.get("path", [])
                        if seg_path and len(seg_path) == len(path_coords):
                            expected_map_id = seg.get("map_id")
                            expected_seg_index = si
                            matched = True
                            ConsoleLog("OutpostRunnerFSM", f"[SEGMENT MATCH LAST RESORT] Matched segment {si} by length only, map_id={expected_map_id}", Console.MessageType.Warning)
                            break
                
                if not matched and path_coords:
                    ConsoleLog("OutpostRunnerFSM", f"[SEGMENT MATCH FAILED] Could not match path (len={len(path_coords)}) to any segment. This is an error!", Console.MessageType.Error)
        
        # OUTPOST PATH SHORTCUT: If walking outpost_path and we've already transitioned to first explorable,
        # skip remaining outpost walking and let the segment walk handle it
        if is_outpost_path and self.current_map_data:
            try:
                current_map = Map.GetMapID()
                segments = self.current_map_data.get("segments", [])
                if segments and len(segments) > 0:
                    first_explorable_map = segments[0].get("map_id")
                    if Map.IsMapIDMatch(current_map, first_explorable_map):
                        ConsoleLog("OutpostRunnerFSM", f"OUTPOST SHORTCUT: Already transitioned to explorable map {first_explorable_map} during outpost walk; skipping remaining outpost path", Console.MessageType.Info)
                        yield from Routines.Yield.wait(100)
                        return
            except Exception:
                pass
        
        # Log when about to enter a map (especially Varajar, map 553)
        if expected_map_id == 553:
            ConsoleLog("OutpostRunnerFSM", f"[VARAJAR] About to enter Varajar Fells (map 553)", Console.MessageType.Info)
        
        # Insert intermediate waypoints if there are large gaps (prevents long straight jumps)
        expanded_path = []
        try:
            player_xy = Player.GetXY()
        except Exception:
            player_xy = None

        # Use the player's current position as the starting reference for interpolation
        prev_x, prev_y = (player_xy[0], player_xy[1]) if player_xy else (path_coords[0][0], path_coords[0][1])
        max_step = 3000.0  # max allowed straight jump before interpolating (tighter to avoid long straight runs)

        for pt in path_coords:
            tx, ty = float(pt[0]), float(pt[1])
            dx = tx - prev_x
            dy = ty - prev_y
            dist = math.hypot(dx, dy)
            if dist > max_step:
                steps = int(math.ceil(dist / max_step))
                for s in range(1, steps + 1):
                    ix = prev_x + dx * (s / float(steps))
                    iy = prev_y + dy * (s / float(steps))
                    expanded_path.append((ix, iy))
            else:
                expanded_path.append((tx, ty))
            prev_x, prev_y = tx, ty

        # Always prepend the player's current position as the first waypoint (outpost and segments)
        # to ensure movement starts from the actual location.
        try:
            cur_player_xy = Player.GetXY()
        except Exception:
            cur_player_xy = None

        if cur_player_xy and expanded_path:
            try:
                sx, sy = float(cur_player_xy[0]), float(cur_player_xy[1])
                ConsoleLog("OutpostRunnerFSM", f"Inserting player start waypoint {cur_player_xy} before first target {expanded_path[0]} (force prepend)", Console.MessageType.Info)
                expanded_path.insert(0, (sx, sy))
            except Exception:
                pass

        # Initialize first point
        self.last_valid_next_point = expanded_path[0] if expanded_path else None
        self.current_path_index = 0

        # Diagnostic log: show summary of the path we're about to follow
        try:
            sample_preview = expanded_path[:3]
        except Exception:
            sample_preview = None
        ConsoleLog("OutpostRunnerFSM", f"follow_path called: expected_map_id={expected_map_id} expected_seg_index={expected_seg_index} original_len={len(path_coords)} expanded_len={len(expanded_path)} preview={sample_preview}", Console.MessageType.Info)
        
        # Walk through each waypoint in sequence with proper arrival detection
        index = 0
        # Small stabilization delay before starting movement on a path
        yield from Routines.Yield.wait(300)
        while index < len(expanded_path):
            point = expanded_path[index]
            self.current_path_index = index
            self.last_valid_next_point = point
            # Validate point
            if (not isinstance(point, (list, tuple))) or len(point) < 2:
                ConsoleLog("OutpostRunnerFSM", f"Invalid waypoint at index {index}: {point}", Console.MessageType.Warning)
                continue
            if point[0] == 0 and point[1] == 0:
                ConsoleLog("OutpostRunnerFSM", f"Skipping null waypoint at index {index}", Console.MessageType.Debug)
                continue

            # If we know which map this path belongs to, ensure we're on that map first
            if expected_map_id:
                current_map = Map.GetMapID()
                if not Map.IsMapIDMatch(current_map, expected_map_id):
                    # OUTPOST PATH SPECIAL CASE: If we're walking an outpost_path and we've transitioned to the explorable,
                    # this is SUCCESS - exit immediately, don't wait for the outpost map to return
                    if is_outpost_path and self.current_map_data:
                        try:
                            segments = self.current_map_data.get("segments", [])
                            if segments and len(segments) > 0:
                                first_explorable_map = segments[0].get("map_id")
                                if Map.IsMapIDMatch(current_map, first_explorable_map):
                                    ConsoleLog("OutpostRunnerFSM", f"MAP TRANSITION SUCCESS: Outpost path successfully led to explorable {first_explorable_map}. Exiting outpost_path walk.", Console.MessageType.Info)
                                    self.followxy.reset()
                                    return  # Exit follow_path entirely - mission accomplished!
                        except Exception:
                            pass
                    
                    # SEGMENT TRANSITION DETECTION: If we're walking a segment (not outpost) and we've transitioned to the next segment,
                    # exit immediately and let FSM handle the next segment
                    if not is_outpost_path and expected_seg_index is not None and expected_seg_index >= 0 and self.current_map_data:
                        try:
                            segments = self.current_map_data.get("segments", [])
                            # Check if current_map matches the NEXT segment's map
                            if expected_seg_index + 1 < len(segments):
                                next_segment = segments[expected_seg_index + 1]
                                next_map_id = next_segment.get("map_id")
                                if Map.IsMapIDMatch(current_map, next_map_id):
                                    ConsoleLog("OutpostRunnerFSM", f"SEGMENT TRANSITION DETECTED: Transitioned from segment {expected_seg_index} (map {expected_map_id}) to segment {expected_seg_index + 1} (map {next_map_id}). Exiting current segment walk.", Console.MessageType.Info)
                                    self.followxy.reset()
                                    return  # Exit follow_path - FSM will handle next segment
                        except Exception:
                            pass
                    
                    ConsoleLog("OutpostRunnerFSM", f"Map mismatch: current {current_map} != expected {expected_map_id}. Waiting...", Console.MessageType.Warning)
                    # Wait for the expected map to load (short timeout)
                    yield from self.wait_for_map_load(expected_map_id, timeout=15000)
                    current_map = Map.GetMapID()
                    if not Map.IsMapIDMatch(current_map, expected_map_id):
                        ConsoleLog("OutpostRunnerFSM", f"Still not on expected map {expected_map_id}; skipping waypoint {point}", Console.MessageType.Warning)
                        index += 1
                        continue
                    # Log generic arrival for any expected map
                    ConsoleLog("OutpostRunnerFSM", f"[MAP ARRIVAL] Successfully arrived in expected map {expected_map_id}", Console.MessageType.Info)
                    # Insert player's current position as an immediate waypoint to avoid a large jump from previous map
                    try:
                        player_xy = Player.GetXY()
                    except Exception:
                        player_xy = None
                    if player_xy:
                        # Insert current player position before the next target so movement starts from actual location
                        expanded_path.insert(index, (float(player_xy[0]), float(player_xy[1])))
                        # do not increment index here; next loop iteration will handle the inserted intermediate point
                        continue

            # Log when starting to move in Varajar coordinates (first waypoint)
            if expected_map_id == 553 and index == 0:
                ConsoleLog("OutpostRunnerFSM", f"[VARAJAR] Starting to move in Varajar - first waypoint: {point}", Console.MessageType.Info)

            # Debug log: include current map, expected map, segment index and path index (log every 5th waypoint to reduce spam)
            if index % 5 == 0:
                try:
                    cur_map = Map.GetMapID()
                except Exception:
                    cur_map = None
                ConsoleLog("OutpostRunnerFSM", f"About to move: cur_map={cur_map} expected_map={expected_map_id} seg_index={expected_seg_index} path_index={index} point={point}", Console.MessageType.Debug)

            # Dump full expanded path once for this segment (helps debugging large jumps)
            try:
                seg_key = (expected_map_id, expected_seg_index)
            except Exception:
                seg_key = None
            if seg_key and expected_seg_index is not None and expected_seg_index >= 0 and seg_key not in self._dumped_segments:
                try:
                    ConsoleLog("OutpostRunnerFSM", f"[PATH DUMP] expanded_path (len={len(expanded_path)}): {expanded_path}", Console.MessageType.Info)
                except Exception:
                    ConsoleLog("OutpostRunnerFSM", "[PATH DUMP] failed to stringify expanded_path", Console.MessageType.Warning)
                self._dumped_segments.add(seg_key)

            # Move to waypoint with dynamic tolerance (higher tolerance near portals)
            # Use 200 for last waypoint (portal), 100 for others
            waypoint_tolerance = 250 if index == len(expanded_path) - 1 else 150

            # Retry loop: on timeout, insert player's current XY and retry up to max_attempts
            # BUT: For outpost paths, use reduced timeout (10s instead of 90s) and no retries (fail fast)
            if is_outpost_path:
                max_attempts = 0  # No retries for outpost paths - fail fast
                timeout_per_waypoint = 10  # 10 seconds per outpost waypoint (generous but not excessive)
            else:
                max_attempts = 3
                timeout_per_waypoint = 90
            
            attempt = 0
            success = False
            while attempt <= max_attempts:
                self.followxy.move_to_waypoint(point[0], point[1], tolerance=waypoint_tolerance)
                ConsoleLog("OutpostRunnerFSM", f"Started move_to_waypoint idx={index} target={point} tol={waypoint_tolerance} attempt={attempt}", Console.MessageType.Debug)
                try:
                    if not self.followxy.is_following():
                        ConsoleLog("OutpostRunnerFSM", f"followxy.is_following() is False immediately after move_to_waypoint for idx={index}", Console.MessageType.Warning)
                except Exception:
                    pass

                # Wait for arrival with timeout
                timeout_time = time.time() + timeout_per_waypoint
                tick = 0
                timed_out = False
                last_map_check_time = time.time()
                is_at_last_waypoint_logged = False
                
                while self.followxy.is_following():
                    current_time = time.time()
                    
                    # EXPLORABLE → EXPLORABLE TRANSITIONS: Check rapidly when at last waypoint
                    if (not is_outpost_path and self.current_map_data and 
                        index == len(expanded_path) - 1):
                        
                        if current_time - last_map_check_time >= 0.5:
                            last_map_check_time = current_time
                            try:
                                current_map = Map.GetMapID()
                                
                                # Only process if map ID is not 0 (loading state)
                                if current_map != 0:
                                    if self.current_map_data is None:
                                        ConsoleLog("OutpostRunnerFSM", f"⚠️ CRITICAL: current_map_data is None at rapid check!", Console.MessageType.Error)
                                    else:
                                        segments = self.current_map_data.get("segments", [])
                                        
                                        # Determine which segment we're currently in by checking current map against all segments
                                        current_seg_idx = None
                                        for seg_idx, seg in enumerate(segments):
                                            if Map.IsMapIDMatch(seg.get("map_id"), current_map):
                                                current_seg_idx = seg_idx
                                                break
                                        
                                        # Now check if we've transitioned to a different segment
                                        if current_seg_idx is not None:
                                            # Check if we've moved to a different segment than expected
                                            if expected_seg_index is not None and current_seg_idx != expected_seg_index:
                                                # We've transitioned to a different segment!
                                                ConsoleLog("OutpostRunnerFSM", f"★★★ MAP TRANSITION DETECTED: Segment {expected_seg_index} (map {expected_map_id}) → Segment {current_seg_idx} (map {current_map}) ★★★", Console.MessageType.Info)
                                                self.followxy.reset()
                                                return
                                            # Check if there's a next segment
                                            elif current_seg_idx + 1 < len(segments):
                                                next_segment = segments[current_seg_idx + 1]
                                                next_map_id = next_segment.get("map_id")
                                                if Map.IsMapIDMatch(current_map, next_map_id):
                                                    # We've transitioned to the next segment!
                                                    current_seg_map = segments[current_seg_idx].get("map_id")
                                                    ConsoleLog("OutpostRunnerFSM", f"★★★ MAP TRANSITION DETECTED: {current_seg_map} → {next_map_id} ★★★", Console.MessageType.Info)
                                                    self.followxy.reset()
                                                    return
                                            else:
                                                # This IS the last segment, no next segment
                                                # Check if we've transitioned INTO this segment
                                                current_seg = segments[current_seg_idx]
                                                seg_map_id = current_seg.get("map_id")
                                                ConsoleLog("OutpostRunnerFSM", f"[RAPID CHECK] Final segment: current_map={current_map}, seg_map_id={seg_map_id}, match={Map.IsMapIDMatch(current_map, seg_map_id)}", Console.MessageType.Info)
                                                if Map.IsMapIDMatch(current_map, seg_map_id):
                                                    # We're on the final segment - run is complete!
                                                    ConsoleLog("OutpostRunnerFSM", f"★★★ FINAL SEGMENT REACHED: Arrived at destination map {current_map} ★★★", Console.MessageType.Info)
                                                    self.followxy.reset()
                                                    return
                                        else:
                                            ConsoleLog("OutpostRunnerFSM", f"[RAPID CHECK] No matching segment found for current_map={current_map}", Console.MessageType.Warning)
                            except Exception as e:
                                ConsoleLog("OutpostRunnerFSM", f"⚠️ Exception in rapid map check: {e}", Console.MessageType.Error)
                                import traceback
                                ConsoleLog("OutpostRunnerFSM", traceback.format_exc(), Console.MessageType.Error)
                    
                    # OUTPOST PATH: Check if transitioned to explorable
                    if is_outpost_path and self.current_map_data and (current_time - last_map_check_time >= 1.0):
                        last_map_check_time = current_time
                        try:
                            current_map = Map.GetMapID()
                            
                            # Only process if map ID is not 0 (loading state)
                            if current_map != 0:
                                segments = self.current_map_data.get("segments", [])
                                if segments and len(segments) > 0:
                                    first_explorable_map = segments[0].get("map_id")
                                    if Map.IsMapIDMatch(current_map, first_explorable_map):
                                        ConsoleLog("OutpostRunnerFSM", f"★★★ MAP TRANSITION DETECTED: {expected_map_id} → explorable {first_explorable_map} ★★★", Console.MessageType.Info)
                                        self.followxy.reset()
                                        return
                        except Exception:
                            pass

                    
                    if time.time() > timeout_time:
                        ConsoleLog("OutpostRunnerFSM", f"Waypoint timeout at index {index}: {point} (attempt={attempt})", Console.MessageType.Warning)
                        
                        # CHECK FOR MAP TRANSITION BEFORE GIVING UP: If this is a segment walk and map changed, exit early
                        if not is_outpost_path and self.current_map_data:
                            try:
                                current_map = Map.GetMapID()
                                segments = self.current_map_data.get("segments", [])
                                if expected_seg_index is not None and expected_seg_index >= 0 and expected_seg_index + 1 < len(segments):
                                    next_segment = segments[expected_seg_index + 1]
                                    next_map_id = next_segment.get("map_id")
                                    if Map.IsMapIDMatch(current_map, next_map_id):
                                        ConsoleLog("OutpostRunnerFSM", f"MAP TRANSITION ON TIMEOUT: Detected transition to map {next_map_id} during timeout. Exiting segment.", Console.MessageType.Info)
                                        self.followxy.reset()
                                        return  # Exit immediately - we've transitioned!
                            except Exception:
                                pass
                        
                        # Force reset movement when timeout occurs
                        self.followxy.reset()
                        timed_out = True
                        break

                    # Update movement state
                    self.followxy.update()
                    # Periodic debug every ~2s to show player position while moving
                    try:
                        tick += 1
                        if tick % 40 == 0:
                            px, py = Player.GetXY()
                            ConsoleLog("OutpostRunnerFSM", f"follow loop idx={index} tick={tick} player=({int(px)},{int(py)}) target={point}", Console.MessageType.Debug)
                    except Exception:
                        pass
                    yield from Routines.Yield.wait(50)  # Reduced from 100ms for smoother movement

                if not timed_out:
                    # Arrived successfully
                    success = True
                    break

                # timed out - decide whether to retry
                attempt += 1
                if attempt <= max_attempts:
                    # Insert player current position as intermediate waypoint and retry
                    try:
                        px, py = Player.GetXY()
                        ConsoleLog("OutpostRunnerFSM", f"Retry: inserting current player pos ({int(px)},{int(py)}) before index {index} and retrying (attempt={attempt})", Console.MessageType.Info)
                        expanded_path.insert(index, (float(px), float(py)))
                        # set point to the newly inserted waypoint for next loop
                        point = expanded_path[index]
                        continue
                    except Exception:
                        ConsoleLog("OutpostRunnerFSM", "Retry: failed to get player position; will not retry further", Console.MessageType.Warning)
                        break
                else:
                    ConsoleLog("OutpostRunnerFSM", f"Giving up on waypoint {point} after {attempt} attempts", Console.MessageType.Warning)
                    break
            
            # If this is the last waypoint of any segment (not outpost, not final segment), detect portal transition
            if index == len(expanded_path) - 1 and not is_outpost_path and self.current_map_data and expected_map_id:
                segments = self.current_map_data.get("segments", [])
                
                # Find which segment we're in by matching expected_map_id
                current_seg_idx = None
                for seg_idx, seg in enumerate(segments):
                    if Map.IsMapIDMatch(seg.get("map_id"), expected_map_id):
                        current_seg_idx = seg_idx
                        break
                
                # Check if there's a next segment (non-final segment) OR if this is the final segment
                if current_seg_idx is not None:
                    # CASE 1: Non-final segment - wait for specific next map
                    if current_seg_idx + 1 < len(segments):
                        next_segment = segments[current_seg_idx + 1]
                        next_map_id = next_segment.get("map_id")
                        ConsoleLog("OutpostRunnerFSM", f"[PORTAL] At last waypoint of segment (map {expected_map_id}). Detecting transition to {next_map_id}...", Console.MessageType.Info)
                        
                        # Continuous detection loop: Keep checking for map change
                        # Don't reset movement - let the bot naturally move through portal
                        transition_timeout = time.time() + 15
                        last_check = time.time()
                        
                        while time.time() < transition_timeout:
                            try:
                                current_time = time.time()
                                # Check every 0.5 seconds for faster detection
                                if current_time - last_check >= 0.5:
                                    last_check = current_time
                                    current_map = Map.GetMapID()
                                    
                                    # Only process if map ID is not 0 (loading state)
                                    if current_map != 0:
                                        if not Map.IsMapIDMatch(current_map, expected_map_id):
                                            # Map changed! Check if it's the expected next map
                                            if Map.IsMapIDMatch(current_map, next_map_id):
                                                ConsoleLog("OutpostRunnerFSM", f"★★★ MAP TRANSITION DETECTED: {expected_map_id} → {next_map_id} ★★★", Console.MessageType.Info)
                                                self.followxy.reset()
                                                return
                                            else:
                                                # Unexpected map! Log it prominently
                                                ConsoleLog("OutpostRunnerFSM", f"⚠️⚠️⚠️ ERROR: Wrong map after portal! Got {current_map}, expected {next_map_id}. Portal waypoint coords may be wrong.", Console.MessageType.Error)
                                                # Try to continue anyway - maybe game will load correct map
                                                # Don't exit yet, keep checking
                            except Exception as e:
                                pass
                            
                            yield from Routines.Yield.wait(100)  # Check frequently
                        
                        # Timeout
                        self.followxy.reset()
                        ConsoleLog("OutpostRunnerFSM", f"[PORTAL] Timeout (no map change detected). Continuing...", Console.MessageType.Warning)
                    
                    # CASE 2: Final segment - any map change means we've completed the run
                    else:
                        ConsoleLog("OutpostRunnerFSM", f"[PORTAL] At last waypoint of FINAL segment (map {expected_map_id}). Waiting for run completion...", Console.MessageType.Info)
                        
                        transition_timeout = time.time() + 15
                        last_check = time.time()
                        
                        while time.time() < transition_timeout:
                            try:
                                current_time = time.time()
                                # Check every 0.5 seconds
                                if current_time - last_check >= 0.5:
                                    last_check = current_time
                                    current_map = Map.GetMapID()

                                    # Only process if map ID is not 0 (loading state)
                                    if current_map != 0 and not Map.IsMapIDMatch(current_map, expected_map_id):
                                        # Any map change = run completion
                                        ConsoleLog("OutpostRunnerFSM", f"★★★ FINAL SEGMENT COMPLETE: Left map {expected_map_id}, now on map {current_map} ★★★", Console.MessageType.Info)
                                        self.followxy.reset()
                                        return
                            except Exception as e:
                                pass
                            
                            yield from Routines.Yield.wait(100)
                        
                        # Timeout
                        self.followxy.reset()
                        ConsoleLog("OutpostRunnerFSM", f"[PORTAL] Timeout waiting for run completion. Continuing...", Console.MessageType.Warning)

            
            # No pause at waypoint - move to next immediately for continuous flow
        
            # move to next waypoint index
            index += 1

        # Mark completion
        self.current_path_index = len(expanded_path) - 1
        self.last_valid_next_point = expanded_path[-1]
        ConsoleLog("OutpostRunnerFSM", f"[SEGMENT COMPLETE] Finished following segment (seg_index={expected_seg_index}) with {len(path_coords)} waypoints", Console.MessageType.Info)
    
    def get_next_path_point(self):
        """Returns the current active path point based on progress."""
        if not self.current_map_data:
            return self.last_valid_next_point
        
        # Merge all paths for current map
        all_points = []
        if self.current_map_data.get("outpost_path"):
            all_points.extend(self.current_map_data["outpost_path"])
        if self.current_map_data.get("segments"):
            for seg in self.current_map_data["segments"]:
                all_points.extend(seg.get("path", []))

        # Clamp index in case we reach the end
        idx = min(self.current_path_index, len(all_points) - 1)
        if idx >= 0 and idx < len(all_points):
            self.last_valid_next_point = all_points[idx]
            return all_points[idx]

        return self.last_valid_next_point
    
    def enable_custom_widget_list(self):
        """Enable only the widgets in ALWAYS_ENABLED_WIDGETS list."""
        for widget_name in ALWAYS_ENABLED_WIDGETS:
            handler = get_widget_handler()
            handler.enable_widget(widget_name)
            ConsoleLog("WidgetHandler", f"'{widget_name}' is Enabled", Console.MessageType.Info)

    def cache_and_disable_all_widgets(self):
        global cached_enabled_widgets
        handler = get_widget_handler()
        cached_enabled_widgets = handler.list_enabled_widgets()  # ✅ only enabled ones
        ConsoleLog("WidgetHandler", f"Currently enabled widgets: {cached_enabled_widgets}", Console.MessageType.Debug)

        # Disable all
        for widget_name in cached_enabled_widgets:
            handler.disable_widget(widget_name)
        ConsoleLog("WidgetHandler", f"Disabled {len(cached_enabled_widgets)} widgets", Console.MessageType.Info)


    def restore_cached_widgets(self):
        global cached_enabled_widgets
        if not cached_enabled_widgets:
            ConsoleLog("WidgetHandler", "No cached widgets to restore!", Console.MessageType.Warning)
            return

        for widget_name in cached_enabled_widgets:
            handler = get_widget_handler()
            handler.enable_widget(widget_name)

        ConsoleLog("WidgetHandler", f"Restored {len(cached_enabled_widgets)} widgets", Console.MessageType.Info)
        cached_enabled_widgets = []  # clear after restore