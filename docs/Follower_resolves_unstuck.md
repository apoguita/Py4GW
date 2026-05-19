# Per-Follower Smart Unstuck

## Context

Followers in HeroAI chase the leader's published `FollowPos` (a navmesh-snapped slot offset). When world geometry (pillars, fence corners, scenery) or an enemy hitbox physically blocks a single follower, the engine just keeps issuing the same `Player.Move` until something external changes. This module gives each follower an automatic local self-rescue: detect that no progress is being made toward `FollowPos`, build a short detour path, and walk it via `BT.Movement.MoveDirect`.

Two detour modes run inside the same state machine:

- **Enemy slalom (primary).** When any enemy sits within `enemy_detection_range`, overlapping enemy touch-circles are merged into welded "peanut" shapes and the follower walks tangents around the **union outline** of each cluster, picking the side that yields the shortest fully-walkable path.
- **Single front-of-follower circle (fallback).** No enemy in range — generate a half-arc around an imaginary obstacle one `touch_radius` ahead of the follower.

The module is per-follower and entirely follower-side. Leader publish, shared memory, and party formation logic do not change. Cross-client sync of the live-tunable settings (sliders + the visualisation toggle) is handled through `FollowRuntime.ini` on a 1-second poll inside `update_smart_unstuck`.

## Files

| File | Role |
|---|---|
| `HeroAI/follow/smart_unstuck.py` | Central module: config, state, detection loop, slalom + single-circle path generators, BT.Move integration, INI sync, snapshot publication. |
| `HeroAI/follow/follower_runtime.py` | Per-tick integration. Owns `FollowExecutionState.stuck`, ticks `update_smart_unstuck`, swaps the follow throttle between idle (250 ms) and detour (0 ms), and skips its own `Player.Move` while the detour state machine owns the wheel. |
| `Widgets/Automation/Multiboxing/HeroAI.py` | `movement_interrupt()` patch. Returns `FAILURE` while `state.stuck.mode != "idle"` so the Follow branch runs every BT tick during a detour. Without this patch BT.Move can only sample at waypoint-arrival moments and the smoothing tolerance becomes a no-op. |
| `HeroAI/ui_base.py` | GUI section "Follower Resolves (unstuck)" with 8 live-tunable sliders + 2 checkboxes. Also hosts `DrawSmartUnstuck3DOverlay`, which renders the per-cluster union polylines and waypoint markers. |
| `HeroAI/globals.py` | `show_followers_unstuck_overlay`, `show_stuck_avoidance_debug`, `smart_unstuck_debug_snapshot` (the dict the overlay reads). |

## Module reference: `smart_unstuck.py`

The module was previously named `stuck_avoidance.py`; the rename to `smart_unstuck.py` preserved INI key strings (`stuck_touch_radius`, `stuck_enemy_detection_range`, `stuck_sample_count`, `show_stuck_avoidance_debug`, etc.) and log prefixes (`stuck.detected`, `stuck.detour`, `stuck.tick`, `stuck.exit`, `stuck.cfg_reload`, …) so saved user settings and existing console-grep workflows keep working. GUI labels ("Stuck Circle Radius", "Stuck Sample Count", "Stuck Avoidance Verbose Logs", "Follower Resolves (unstuck)") were also kept verbatim.

### `SmartUnstuckConfig` — knobs

Grouped by purpose. ★ = live-tunable via GUI slider and INI cross-client sync.

**Geometry**

| Field | Default | Live | Notes |
|---|---|---|---|
| `waypoint_smoothing` | 77.0 | ★ | BT.Move "advance on approach" threshold. Larger = smoother / cuts corners. Smaller = closer adherence to the arc but risks stopping at each waypoint. |
| `touch_radius` | 120.0 | ★ | Detour-circle / per-enemy circle radius. Slalom union outline and front-of-follower arc both scale from this. |
| `enemy_detection_range` | 250.0 | ★ | Radius from follower used to pull enemy candidates for slalom mode. When zero enemies fall in range, fallback (single-circle) mode runs. |
| `waypoint_count` | 5 | — | Front-of-follower mode only; slalom uses adaptive count along arc length. |
| `arc_span_rad` | π | — | Front-of-follower mode: half-circle per side. |
| `navmesh_contains_margin` | 50.0 | — | Margin used by `navmesh.contains()`. |
| `navmesh_snap_tolerance` | 80.0 | — | A `find_nearest_reachable` snap is accepted only if its drift from the ideal is ≤ this. |
| `arc_walkability_required_fraction` | 0.5 | — | Front-of-follower mode side acceptance threshold. |
| `preferred_side_when_both_walkable` | 1 | — | Front-of-follower mode tiebreaker (+1 right, −1 left). |

**Detection**

| Field | Default | Live | Notes |
|---|---|---|---|
| `progress_sample_interval_ms` | 500 | — | Idle-mode sampling period. |
| `no_progress_move_units` | 15.0 | ★ | Sample counts as no-progress if the avatar moved less than this in the interval. |
| `no_progress_close_units` | 10.0 | ★ | Sample counts as no-progress if the gap to `follow_xy` shrank by less than this. |
| `stuck_sample_count` | 1 | ★ | Consecutive no-progress samples required to trigger. With the default 1, trigger fires on the first comparison after baseline (≈ 500 ms after entering idle). |
| `min_distance_activate_unstuck` | 500.0 | ★ | Short-circuit guard: detection skips entirely while `dist_to_follow < this`. |

**Termination**

| Field | Default | Live | Notes |
|---|---|---|---|
| `total_detour_timeout_ms` | 12000 | — | Hard cap on a single detour. |
| `obstacle_cleared_delta` | 500.0 | ★ | Detour exits early once `detour_start_dist − dist_to_follow ≥ this`. Exposed in the GUI as "Min Dist Early Exit" (range 50–800). |

### `SmartUnstuckState` — per-follower state (slots=True)

- `mode: str` — `"idle"` or `"detouring"` (no other modes exist anymore).
- **Detection scratch:** `progress_timer`, `prev_sample_xy`, `prev_sample_dist`, `no_progress_samples`.
- **Detour scratch:** `waypoints`, `waypoint_idx`, `abort_waypoint_idx`, `detour_started_ms`, `waypoint_started_ms`, `detour_start_dist`, `sides_tried`, `detour_tree`.
- **Detour rendering / shape:** `circle_center` (front-of-follower mode), `slalom_centers` (per-enemy positions accepted in slalom mode), `slalom_union_boundaries` (closed polylines drawn by the overlay).
- **Diagnostics:** `tick_count`, `last_tick_ms`, `last_tick_xy`, `waypoint_enter_ms`.

### Public API

```python
def update_smart_unstuck(
    state: SmartUnstuckState,
    cfg: SmartUnstuckConfig,
    *,
    current_xy: tuple[float, float],
    follow_xy: tuple[float, float],
    assigned_changed: bool,
) -> None
```
Ticks the per-follower state machine. **Mutates state and returns None.** Contract: when `state.mode != "idle"` after the call returns, BT.Move has already issued `Player.Move` this tick — the caller MUST skip its own `Player.Move` / `ActionQueueManager().ResetQueue("ACTION")` to avoid clobbering the in-flight path.

```python
def reset_smart_unstuck(state: SmartUnstuckState) -> None
```
Idempotent reset: returns the state to idle, clears detour scratch and detection counters, and clears `hero_globals.smart_unstuck_debug_snapshot`.

```python
def reload_smart_unstuck_config_from_ini(force_reload: bool = False) -> None
```
The cross-client sync entry point. Called once per `update_smart_unstuck` tick; internal `ThrottledTimer(1000)` makes the actual file read at most once per second. `force_reload=True` is used by the GUI handler so the leader's own process picks up its own slider change immediately. See the **Cross-client configuration sync** section.

### `update_smart_unstuck` state machine flow

1. **Always:** call `reload_smart_unstuck_config_from_ini()` (throttled poll).
2. **`assigned_changed` branch:**
   - Non-idle: log `stuck.exit reason=assigned_changed`, full `reset_smart_unstuck`, return.
   - Idle: re-baseline `prev_sample_dist = Utils.Distance(prev_sample_xy, follow_xy)`. Do **not** wipe the no-progress counter. Fall through. (This is what lets detection work while the leader is walking — without it, every `assigned_changed` reset the counter and stuck never accumulated.)
3. **`mode == "detouring"`:** check exits in this order — total timeout / `obstacle_cleared_delta` reached / tree gone / tick the tree once via `_tick_tree_safe` / advance `waypoint_idx` if the BT blackboard moved / early-abort if `waypoint_idx >= abort_waypoint_idx` / BT `SUCCESS` / BT `FAILURE`. Publish snapshot. Return.
4. **`mode == "idle"`:**
   - **Guard:** if `dist_to_follow < cfg.min_distance_activate_unstuck`, clear in-flight detection scratch and return (the leader-parked / settled-into-slot case).
   - Init the lazy `ThrottledTimer(cfg.progress_sample_interval_ms)` if absent. If not expired, return.
   - First sample after entering idle: store baseline (`prev_sample_xy`, `prev_sample_dist`), return.
   - Comparison sample: compute `moved = Utils.Distance(prev_sample_xy, current_xy)` and `closed = prev_sample_dist - dist_to_follow`. If `moved < no_progress_move_units AND closed < no_progress_close_units` → `no_progress_samples += 1`; else reset to 0.
   - Update baseline (`prev_sample_xy`, `prev_sample_dist`).
   - If `no_progress_samples >= stuck_sample_count`: log `stuck.detected`, call `_enter_detour`, publish snapshot.

## Detour generation

### Mode A — Enemy slalom (primary)

`_enter_detour` tries slalom first. The pipeline:

1. **`_get_enemies_in_range(current_xy, enemy_detection_range)`** — uses the library's existing primitives:
   - `AgentArray.GetEnemyArray()`
   - `AgentArray.Filter.ByCondition(ids, lambda aid: Agent.IsValid(int(aid)) and not Agent.IsDead(int(aid)))` — project-canonical validity gate (see `HeroAI/targeting.py`)
   - `AgentArray.Filter.ByDistance(ids, current_xy, range_units)`
   - `AgentArray.Sort.ByDistance(ids, current_xy)`
   - Output loop dereferences each ID to `(x, y)` via `Agent.GetXY` and rejects zero-XY (`abs(x) < 0.001 and abs(y) < 0.001`).
2. **`_cluster_enemy_indices`** — union-find over enemies whose `touch_radius` circles overlap (centre distance < `2 * touch_radius`). Produces one tuple of indices per cluster.
3. **`_build_union_boundary(member_circles)`** — for each cluster, sample 360 rays from the cluster centroid (1° resolution) and take the **farthest** ray-circle hit across all member circles. This is the welded union outline; overlap regions disappear because the ray always exits at the outermost circle's perimeter. Returns a closed CCW polyline.
4. **Iteration:**
   - Pick the closest still-blocking cluster (closest along the `current → follow_xy` axis whose union outline crosses the direct segment).
   - `_find_boundary_tangent_indices(current, boundary)` and `_find_boundary_tangent_indices(follow_xy, boundary)` — extremal angular directions to the boundary samples = tangent points. Exact for convex unions, tight approximation for the near-convex peanut shapes from clustered circles.
   - Walk the boundary BOTH ways (`_build_path_for_side` for `arc_dir = +1` and `−1`) and rank: prefer fully-walkable (`failed_segs == 0`) and shorter; fall back to least-failed (`failed_segs` ascending, then `path_len`) so the follower at least attempts a detour rather than staying stuck.
   - `_build_navmesh_aware_waypoints_with_segments` does the actual placement: uniform arc-length spacing along the boundary (`actual_spacing = total_length / ceil(total_length / _WAYPOINT_SPACING_UNITS)`, where `_WAYPOINT_SPACING_UNITS = 80.0`), each candidate snapped through `_resolve_navmesh_position`, and each segment between emitted waypoints validated by `_segment_walkable_on_navmesh` (samples every `max(20, actual_spacing/4)` units along the segment).
   - Move `current` to the chosen path's exit waypoint, drop the cluster from the remaining set, repeat.
5. **`abort_waypoint_idx`** is computed as the path index whose waypoint sits closest to `follow_xy`. Once BT reaches it during detour ticking, the detour exits early — remaining waypoints would only arc back away from the goal.
6. **State written:** `mode="detouring"`, `arc_side=0` (slalom uses per-cluster directions; this is just a sentinel), `circle_center`, `slalom_centers`, `slalom_union_boundaries`, `waypoints`, `abort_waypoint_idx`, `detour_tree = _build_detour_tree(waypoints, cfg)`. BT is ticked once immediately so `Player.Move(first_waypoint)` goes out this frame.

### Mode B — Single front-of-follower circle (fallback)

If `_get_enemies_in_range` returned an empty tuple, OR the slalom yielded no walkable waypoints, the function falls through to the single-circle path:

- `_generate_arc_waypoints` builds 5 waypoints on the chosen side of an imaginary circle centred one `touch_radius` ahead of the follower. The follower sits at the circle's 6-o'clock (bottom tangent).
- Side selection: each side accepted only if `walkable_count / waypoint_count >= arc_walkability_required_fraction`. If both sides pass, `preferred_side_when_both_walkable` breaks the tie. If neither passes, log `stuck.no_walkable_side -> idle`, reset, return.
- Same BT.Move build + first-tick fire-and-forget pattern as slalom mode.

### `_build_detour_tree`

Both modes hand their waypoint tuple to:

```python
BT.Movement.MoveDirect(
    path_points=[Vec2f(x, y) for x, y in waypoints],
    tolerance=max(1.0, float(cfg.waypoint_smoothing)),
    log=hero_globals.show_stuck_avoidance_debug,
)
```

Tolerance is captured at construction. Subsequent slider changes apply to the **next** detour, not the in-flight one.

## Cross-client configuration sync

Each Py4GW account is a separate OS process with its own `hero_globals` and its own `SMART_UNSTUCK_CFG`. A slider change on the leader must reach every follower's process.

**Write side** (leader):

1. Slider handler in `ui_base.py` updates `SMART_UNSTUCK_CFG.<field>` and `hero_globals.<flag>` locally.
2. Calls `HeroAI_BaseUI._save_follow_runtime_config(...)` which writes every registered key to `FollowRuntime.ini`.
3. Calls `reload_smart_unstuck_config_from_ini(force_reload=True)` so the leader's own process re-reads the file immediately (otherwise the leader would be a second behind its own slider).

**Read side** (every process, including the leader):

`update_smart_unstuck` runs once per BT tick when the follower is following on the same map. The first thing it does is `reload_smart_unstuck_config_from_ini()` (no force). The function is throttled by `_CONFIG_RELOAD_TIMER = ThrottledTimer(1000)` — the actual `IniManager.reload()` + per-key `read_*` calls run at most once per second. Each value changed is logged as `stuck.cfg_reload <key> <old>-><new>`.

**Nine keys flow through this path:**

| INI key (`[FollowRuntime]`) | Type | Bound to |
|---|---|---|
| `waypoint_smoothing` | float | `SMART_UNSTUCK_CFG.waypoint_smoothing` |
| `stuck_touch_radius` | float | `SMART_UNSTUCK_CFG.touch_radius` |
| `stuck_enemy_detection_range` | float | `SMART_UNSTUCK_CFG.enemy_detection_range` |
| `stuck_sample_count` | int | `SMART_UNSTUCK_CFG.stuck_sample_count` |
| `min_distance_activate_unstuck` | float | `SMART_UNSTUCK_CFG.min_distance_activate_unstuck` |
| `no_progress_move_units` | float | `SMART_UNSTUCK_CFG.no_progress_move_units` |
| `no_progress_close_units` | float | `SMART_UNSTUCK_CFG.no_progress_close_units` |
| `obstacle_cleared_delta` | float | `SMART_UNSTUCK_CFG.obstacle_cleared_delta` |
| `show_followers_unstuck_overlay` | bool | `hero_globals.show_followers_unstuck_overlay` |

Clamp bounds are applied at three layers (slider input, INI load, INI reload) so a hand-edited INI cannot escape the documented ranges (`_RADIUS_MIN/MAX`, `_SAMPLE_COUNT_MIN/MAX`, `_MIN_DISTANCE_MIN/MAX`, `_PROGRESS_UNITS_MIN/MAX`).

**Documented limitation:** other display flags (`show_broadcast_follow_positions`, `show_broadcast_follow_threshold_rings`, `show_stuck_avoidance_debug`) are NOT in the throttled poll — they sync only at process-startup `_load_follow_runtime_config`. Toggling them on the leader does not propagate live.

## Runtime integration — `follower_runtime.py`

- `FollowExecutionState` gained `stuck: SmartUnstuckState = field(default_factory=SmartUnstuckState)`.
- `_reset_follow_runtime()`, the map-signature-change block, and the leader-publish-signature-change block all call `reset_smart_unstuck(state.stuck)`.
- **Throttle swap:** when `state.stuck.mode != "idle"`, `cached_data.follow_throttle_timer.SetThrottleTime(0)`. Otherwise 250 ms. This is what makes BT.Move tick at the full HeroAI BT rate during a detour and lets the smoothing tolerance ("advance on approach") actually fire mid-walk.
- **Tolerance early-return:** after the upstream `effective_follow_distance` recovery override, the runtime calls `reset_smart_unstuck` + returns FAILURE when the follower is within tolerance.
- **`update_smart_unstuck` call:** runs when `follow_z == 0 and not own_flag_active`. (Cross-z keypress path and personally-flagged followers are excluded.)
- **Skip own movement:** after the call, if `state.stuck.mode != "idle"`, the runtime resets `state.last_follow_move_point`, resets the throttle, and returns FAILURE. BT.Move owns the wheel.

### Coexistence with upstream "follow recovery"

Upstream's `is_follow_recovery_active` mechanism handles long-distance catch-up. It is **orthogonal** to smart_unstuck — they operate at different distance scales, on different problems, and can both fire in the same tick. Together they cover the full failure spectrum: recovery handles "the party walked away from me," smart_unstuck handles "I can't physically reach the slot."

**Recovery — what it does** (defined in `HeroAI/follow/follower_runtime.py`; the current values reflect upstream commit `dbb39f72` "Adding enemy tracker widget"):

- **Activation threshold:** `FOLLOW_RECOVERY_START_DISTANCE = 4000.0` (raised from the pre-`dbb39f72` `max(Range.Spellcast, Range.SafeCompass * 0.85)` ≈ 2125u — recovery now activates at much greater distances).
- **Release threshold:** `FOLLOW_RECOVERY_RELEASE_DISTANCE = Range.Spellcast.value` ≈ 1248u (was `max(Spellcast, START - 700)` ≈ 1425u — slightly tighter, follower closes further before recovery exits).
- **On entry:** broadcasts `"Hey, Wait for me!"` via `SharedCommandType.ConsoleMessage` shared-memory to the leader (was party chat in `'#'` pre-`dbb39f72`).
- **While active (per the BT patches in `HeroAI/follow/headless_tree.py` and `Widgets/Automation/Multiboxing/HeroAI.py`):**
  - `LootingNode` returns FAILURE — looting suppressed.
  - `HandleOutOfCombat` returns False — out-of-combat scripts skipped.
  - `GlobalGuardNode.DistanceSafe` forced True — the combat tree keeps ticking even when far from the party.
  - `CastingBlockNode` bypassed for `combat_handler.InCastingRoutine()` — recovery interrupts in-flight combat casting routines so the follower can move (note: `Agent.IsCasting()` is still respected at the BT level, but the in-function check at `execute_follower_follow:201` is NOT — see Known Issues).
  - `effective_follow_distance = min(follow_distance, FOLLOW_RECOVERY_RELEASE_DISTANCE)` — tightens the "are we close enough" early-return so the follower keeps closing instead of stopping at slot tolerance.
- **Pet recovery (added in `dbb39f72`):** `_maybe_notify_pet_recovery(...)` runs inside `is_follow_recovery_active`. When a follower's pet has fallen ≥ `FOLLOW_RECOVERY_START_DISTANCE` from the destination, a `"pet lagged behind at x=…, y=…"` console message is broadcast to the leader. Tracked via `state.pet_recovery_notified: bool` to avoid spam.

**Distance scales — how the two systems compose:**

| | Recovery | Smart_unstuck |
|---|---|---|
| **Scale** | Long (activates ≥ 4000u, releases < 1248u) | Short (no-progress detection skipped if `dist_to_follow < 500u`) |
| **Problem** | Follower fell behind the party; suppress competing routines and walk | Follower physically blocked; route around obstacle |
| **Mechanism** | Tightens follow tolerance, suppresses peer BT nodes, keeps base `Player.Move` firing | Builds detour waypoints (slalom or single-circle), drives `BT.Move` at full tick rate |
| **Trigger** | `dist_to_destination ≥ START_DISTANCE` (hysteresis on RELEASE_DISTANCE) | `no_progress_samples ≥ stuck_sample_count` |
| **Termination** | `dist_to_destination < RELEASE_DISTANCE` | Cleared `obstacle_cleared_delta` / 12 s timeout / reached `abort_waypoint_idx` / BT terminal |

The **integration zone** (where both can be active simultaneously) is **500u – 4000u** distance to destination — much wider than the pre-`dbb39f72` window (500u – 2125u). The wider band means smart_unstuck will trigger during recovery more often in practice, which is exactly what the integration was designed for.

**Stuck-during-recovery cycle** (the typical scenario the two systems jointly handle):

1. Follower falls ≥ 4000u behind the destination. Recovery activates, `"Hey, Wait for me!"` notification fires. Looting / OOC scripts suppressed. Base `Player.Move(slot)` continues firing every tick.
2. En route, the follower hits a wall (terrain blocker or enemy hitbox). The engine reports `Agent.IsMoving == False` despite `Player.Move` being called.
3. After ~500 ms of no progress (`moved < no_progress_move_units AND closed < no_progress_close_units`), `update_smart_unstuck` triggers `_enter_detour`.
4. `state.stuck.mode = "detouring"`. Throttle drops to 0 ms. `BT.Move` drives the detour at the full BT rate. `execute_follower_follow` skips its own `Player.Move` for the duration.
5. Detour exits when one of the standard conditions fires (`obstacle_cleared_delta` ≥ 500u closed / 12 s / `abort_waypoint_idx` reached / BT terminal). `reset_smart_unstuck` → `state.stuck.mode = "idle"`. Throttle returns to 250 ms.
6. Recovery is **still active** (follower is still > 1248u from destination). Normal `Player.Move(slot)` resumes — keeps closing toward the leader.
7. If the follower gets stuck again, the cycle repeats from step 3.
8. Eventually the follower closes within 1248u → recovery releases → normal follow behaviour resumes; smart_unstuck's `min_distance_activate_unstuck = 500u` guard then disables stuck detection too.

**No coupling between the two state machines.** Recovery and smart_unstuck share `FollowExecutionState` but read/write disjoint fields — recovery owns `recovery_active` and `pet_recovery_notified`; smart_unstuck owns `stuck` (a `SmartUnstuckState` instance). Neither resets the other's state. The only crosswire is the `effective_follow_distance` read in `execute_follower_follow:297` — smart_unstuck's early-return uses the recovery-tightened distance as the "close enough to stop detecting" threshold during recovery, which is exactly the correct semantics (don't stop detecting until recovery would have stopped walking).

## BT integration — `Widgets/Automation/Multiboxing/HeroAI.py`

`movement_interrupt()` short-circuits the BT Selector when `Agent.IsMoving()` is True. Without intervention, that means while a detour is walking, Follow gets bypassed at every tick except the brief stops at waypoint arrivals — and at those exact moments BT.Move sees `wp_dist ≈ 0` and the smoothing tolerance is useless. The patch:

```python
def movement_interrupt() -> BehaviorTree.NodeState:
    if follow_execution_state.stuck.mode != "idle":
        return BehaviorTree.NodeState.FAILURE  # let Follow run every tick during detour
    if Agent.IsMoving(Player.GetAgentID()):
        return BehaviorTree.NodeState.SUCCESS
    return BehaviorTree.NodeState.FAILURE
```

This was the keystone fix for getting the smoothing parameter to have any visible effect.

## GUI — `ui_base.py`

The "Follower Resolves (unstuck)" section sits in `DrawFollowFormationsQuickWindow`, placed beneath "Follow Publish" / threshold presets.

**Sliders** (each a `PyImGui.input_float` / `input_int`, with min/max clamps applied at the slider, on INI load, and inside `reload_smart_unstuck_config_from_ini`):

| Label | Field | Range |
|---|---|---|
| Waypoint Smoothing | `waypoint_smoothing` | ≥ 1.0 (no upper clamp) |
| Stuck Circle Radius | `touch_radius` | 50 – 400 |
| Enemy Detection Range | `enemy_detection_range` | 50 – 400 |
| Stuck Sample Count | `stuck_sample_count` | 1 – 10 |
| Min Distance Activate Unstuck | `min_distance_activate_unstuck` | 50 – 600 |
| No-Progress Move Units | `no_progress_move_units` | 1 – 100 |
| No-Progress Close Units | `no_progress_close_units` | 1 – 100 |
| Min Dist Early Exit | `obstacle_cleared_delta` | 50 – 800 |

**Checkboxes** (in the "Follow Publish" section above):

- **Draw Followers Unstuck (3D)** → `hero_globals.show_followers_unstuck_overlay`. Gates `DrawSmartUnstuck3DOverlay`. Cross-client synced via the INI poll.
- **Stuck Avoidance Verbose Logs** → `hero_globals.show_stuck_avoidance_debug`. Gates the per-tick / per-sample / per-probe log spam. NOT cross-client synced (startup load only).

On any slider/checkbox change in the unstuck block: `dirty_runtime_cfg = True`, then explicit `_save_follow_runtime_config(...)` + `reload_smart_unstuck_config_from_ini(force_reload=True)` so the change is written and re-read in the leader's own frame.

**`DrawSmartUnstuck3DOverlay`:**
- Early-returns if `not hero_globals.show_followers_unstuck_overlay` (rendering disabled, detection still runs).
- Early-returns if the snapshot is None (no active detour).
- Reads `union_boundaries` from the snapshot. Renders each cluster's closed polyline as a magenta line strip, stride 6 (~60 segments out of the 360 vertices) for performance.
- Falls back to drawing the legacy `circle_center` ring when `union_boundaries` is empty (front-of-follower mode).
- Draws each waypoint as an inner coloured dot (current = yellow, done = grey, upcoming = green) plus a faint outer ring at `_OVERLAY_TOUCH_RADIUS` (25.0) marking the touch threshold.

## Diagnostic instrumentation

All gated behind `hero_globals.show_stuck_avoidance_debug` except the `stuck.cfg_reload`, `stuck.detected`, and `stuck.exit reason=…` lines, which always fire so changes can be traced post-mortem from the console history.

| Event | Log prefix |
|---|---|
| Detection trigger | `stuck.detected dist=… samples=… pos=…` |
| Detour entry, slalom | `stuck.detour start mode=slalom enemies=… clusters=… waypoints=… abort_idx=… arc_dirs=[…] dist=… tolerance=… radius=…` |
| Detour entry, single-circle | `stuck.detour start mode=single side=… center=… dist=… waypoints=… tolerance=… radius=…` |
| Slalom side probe (per cluster) | `stuck.slalom.probe arc_dir=… waypoints=… failed_segs=… dropped=… path_len=…` |
| Slalom cluster chosen | `stuck.slalom.cluster_chosen arc_dir=… waypoints=… path_len=… failed_segs=… fallback=… fully_walkable_sides=N/M` |
| Slalom cluster rejected (both sides empty) | `stuck.slalom.skip enemy=…` / `stuck.slalom.empty enemies_in_range=… -> falling back to front-of-follower circle` |
| Detour init geometry dump | `stuck.detour_init` / `stuck.detour_init.bt_params` / `stuck.detour_init.cfg` / `stuck.wp[i]` |
| Per-tick state (verbose) | `stuck.tick #N t=…ms dt=…ms pos=… speed=… moved=… wp_idx=… wp_dist=… next_wp_dist=… dist_to_follow=… bt_state=… last_move=… stall_retries=… result=…` |
| Waypoint advance | `stuck.advance from=… to=… time_on_prev_wp_ms=… seg_dist=… avg_seg_speed=… dist_to_new_wp=…` |
| Idle skip (close to slot) | `stuck.skip reason=close_to_followpos dist=… threshold=…` |
| Exit | `stuck.exit reason=cleared\|total_timeout\|closest_to_goal\|assigned_changed` |
| BT terminal | `stuck.bt_finished reason=success` / `stuck.bt_failed reason=… total_time_ms=… ticks=…` |
| Cross-client config drift | `stuck.cfg_reload <key> <old>-><new> force=…` |

## Defaults summary

| Field | Default |
|---|---|
| `waypoint_smoothing` | 77.0 |
| `touch_radius` | 120.0 |
| `enemy_detection_range` | 250.0 |
| `stuck_sample_count` | 1 |
| `min_distance_activate_unstuck` | 500.0 |
| `no_progress_move_units` | 15.0 |
| `no_progress_close_units` | 10.0 |
| `progress_sample_interval_ms` | 500 |
| `total_detour_timeout_ms` | 12000 |
| `obstacle_cleared_delta` | 500.0 |
| `waypoint_count` | 5 |
| `arc_span_rad` | π |
| `navmesh_contains_margin` | 50.0 |
| `navmesh_snap_tolerance` | 80.0 |
| `arc_walkability_required_fraction` | 0.5 |
| `preferred_side_when_both_walkable` | +1 |

Slider INI defaults in `_ensure_follow_window_ini_vars` mirror these.

## Known issues / cleanup TODOs

- **`Agent.IsCasting` short-circuits smart_unstuck during recovery.** In `execute_follower_follow` ([follower_runtime.py:201-202](../../../dev/Guildwars/sloppynacho-py4gw/Py4GW/HeroAI/follow/follower_runtime.py)), the early-return `if Agent.IsCasting(player_agent_id): return FAILURE` runs *after* `recovery_active = is_follow_recovery_active(...)` is captured but *before* `update_smart_unstuck(...)` is called. Recovery's BT-level `CastingBlockNode` bypass (`HeroAI.py:303-306`) only suppresses `combat_handler.InCastingRoutine()`, not this in-function `Agent.IsCasting` check. **Symptom**: if a healer follower is mid-skill-cast when stuck during recovery, the detour won't start until the cast finishes (typically 1–3 s). **Suggested fix**: `if Agent.IsCasting(player_agent_id) and not recovery_active: return FAILURE` — mirrors the BT-level bypass and matches recovery's "catch up trumps everything" semantics. One-line change. Not yet applied.
- **Display flags are per-client by design.** `show_broadcast_follow_positions`, `show_broadcast_follow_threshold_rings`, and `show_stuck_avoidance_debug` sync at process startup only (NOT in the cross-client INI poll). This is intentional — they're personal preferences, not party-wide settings. Forcing the leader to override every follower's debug-overlay state would be wrong. Only `show_followers_unstuck_overlay` is party-wide (it's a multibox-debugging aid).
- **`Enable Combat Avoidance Mix` checkbox is a no-op.** It still toggles `cached_data.global_options.Avoidance` but the underlying `vector_fields.py` module that consumed it was deleted upstream. The `Avoidance` field is left in place because it's deeply wired (shared memory layout, per-player toggle row, Botting API, party headers); only the consuming module is gone. Separate cleanup if/when the field is purged from `HeroAIOptions`.

## Verification

In-game manual test plan:

1. **Baseline (no detection).** Park leader. Stand follower in formation slot, distance < 500. Verify `stuck.detected` never fires (the `min_distance_activate_unstuck` guard).
2. **Slalom trigger.** Move leader to a position with 1–2 enemies between leader and follower. Within ~500 ms of no progress, console shows `stuck.detected`, then `stuck.detour start mode=slalom enemies=…`. Toggle "Draw Followers Unstuck (3D)" on — the merged peanut outline and waypoints render in 3D. Follower walks around the cluster, exits with `stuck.exit reason=closest_to_goal` or `=cleared`.
3. **Single-circle fallback.** Move leader so no enemy is within `enemy_detection_range` of the follower but world geometry blocks the direct path. Console shows `stuck.detour start mode=single`. Follower attempts the half-arc.
4. **Slalom-fail fallthrough.** Pin the follower between enemies and impassable terrain so both slalom sides fail. Console shows `stuck.slalom.cluster_skipped` for the blocking cluster, then `-> falling back to front-of-follower circle`.
5. **Leader-moving detection.** Walk the leader continuously past a blocking obstacle so `assigned_changed` fires every sample. With the re-baseline (not reset) logic, the follower still accumulates no-progress samples and triggers within ~500 ms once stuck.
6. **Cross-client slider sync.** Open Follow Formations Quick Settings on the leader. Change "Waypoint Smoothing" to 200. Follower's console shows `stuck.cfg_reload waypoint_smoothing 77.0->200.0 force=False` within ~1 second.
7. **Cross-client overlay toggle.** Tick "Draw Followers Unstuck (3D)" on the leader. Follower's console shows `stuck.cfg_reload show_followers_unstuck_overlay False->True`. Follower's overlay starts rendering on its next detour.

Code-level smoke checks:

```bash
python -m py_compile HeroAI/follow/smart_unstuck.py
python -m py_compile HeroAI/follow/follower_runtime.py
python -m py_compile HeroAI/ui_base.py
python -m py_compile HeroAI/globals.py
python -m py_compile Widgets/Automation/Multiboxing/HeroAI.py
```

Architecture doc consistency checks (run from repo root with this doc on disk):

```bash
# 1. No legacy/removed terms.
grep -nE 'step.back|stepping_back|vector_fields|_pump_detour_tree|hero_globals\.py|Apo' \
  C:/Users/mkwal/.claude/plans/focus-on-the-current-inherited-stonebraker.md
# Expected: zero hits.

# 2. Slider labels in the doc match exact strings in ui_base.py.
for label in 'Waypoint Smoothing' 'Stuck Circle Radius' 'Enemy Detection Range' \
             'Stuck Sample Count' 'Min Distance Activate Unstuck' \
             'No-Progress Move Units' 'No-Progress Close Units' \
             'Min Dist Early Exit' 'Draw Followers Unstuck (3D)' \
             'Stuck Avoidance Verbose Logs'; do
  grep -q -F "$label" HeroAI/ui_base.py || echo "MISSING IN ui_base.py: $label"
done
# Expected: silent (no MISSING lines).

# 3. Renamed symbols must not appear in code anywhere (the rename history note
#    in this doc deliberately mentions the old module filename; that's OK).
grep -rnE 'StuckAvoidanceConfig|StuckAvoidanceState|STUCK_AVOIDANCE_CFG|update_stuck_avoidance|reset_stuck_avoidance|reload_stuck_config_from_ini|DrawStuckAvoidance3DOverlay|stuck_avoidance_debug_snapshot' \
  HeroAI/ Widgets/Automation/Multiboxing/HeroAI.py
# Expected: zero hits.
```
