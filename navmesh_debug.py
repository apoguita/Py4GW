import math
import time

import PyImGui

from Py4GWCoreLib import Py4GW
from Py4GWCoreLib.Agent import Agent
from Py4GWCoreLib.DXOverlay import DXOverlay
from Py4GWCoreLib.GlobalCache import GLOBAL_CACHE
from Py4GWCoreLib.Map import Map
from Py4GWCoreLib.Pathing import AutoPathing
from Py4GWCoreLib.Player import Player


MODULE_NAME = 'NavMesh Debug'

_autopath = AutoPathing()
_logs: list[str] = []
_target_x = 0
_target_y = 0
_path_result: list[tuple[float, float, float]] = []
_path_requested = False
_path_started_at = 0.0
_path_completed_in = 0.0
_last_probe_xy: tuple[float, float] | None = None


def log(msg: str) -> None:
    line = f'[{time.strftime("%H:%M:%S")}] {msg}'
    _logs.append(line)
    if len(_logs) > 200:
        _logs.pop(0)
    print(line)


def _safe_player_xy() -> tuple[float, float]:
    try:
        return Player.GetXY()
    except Exception:
        return (0.0, 0.0)


def _safe_player_zplane() -> int:
    try:
        return int(Agent.GetZPlane(Player.GetAgentID()))
    except Exception:
        return 0


def _layer_summary(layers) -> list[str]:
    lines: list[str] = []
    for idx, layer in enumerate(layers):
        trapezoids = getattr(layer, 'trapezoids', []) or []
        portals = getattr(layer, 'portals', []) or []
        sinks = getattr(layer, 'sinks', []) or []
        if trapezoids:
            x_min = min(min(t.XTL, t.XBL) for t in trapezoids)
            x_max = max(max(t.XTR, t.XBR) for t in trapezoids)
            y_min = min(t.YB for t in trapezoids)
            y_max = max(t.YT for t in trapezoids)
            bounds = f'x=[{x_min:.1f},{x_max:.1f}] y=[{y_min:.1f},{y_max:.1f}]'
        else:
            bounds = 'empty'
        lines.append(
            f'layer {idx}: traps={len(trapezoids)} portals={len(portals)} sinks={len(sinks)} {bounds}'
        )
    return lines


def _safe_map_metadata() -> dict[str, object]:
    try:
        region_id, region_name = Map.GetRegion()
    except Exception:
        region_id, region_name = 0, '?'
    try:
        language_id, language_name = Map.GetLanguage()
    except Exception:
        language_id, language_name = 0, '?'
    try:
        district = Map.GetDistrict()
    except Exception:
        district = 0
    try:
        map_name = Map.GetMapName()
    except Exception:
        map_name = '?'
    try:
        instance_type = Map.GetInstanceTypeName()
    except Exception:
        instance_type = '?'
    try:
        uptime = Map.GetInstanceUptime()
    except Exception:
        uptime = 0
    return {
        'map_name': map_name,
        'region_id': int(region_id or 0),
        'region_name': str(region_name),
        'district': int(district or 0),
        'language_id': int(language_id or 0),
        'language_name': str(language_name),
        'instance_type': str(instance_type),
        'uptime': int(uptime or 0),
    }


def _safe_cache_snapshot() -> dict[str, object]:
    map_id = int(Map.GetMapID() or 0)
    group_key = _autopath._get_group_key(map_id) if map_id else ()
    return {
        'group_key': group_key,
        'cache_keys': [str(key) for key in _autopath.pathing_map_cache.keys()],
        'cache_size': len(_autopath.pathing_map_cache),
        'live_map_cache_size': len(getattr(Map.Pathing.GetPathingMaps.__globals__.get('MapContext', object), '_pathing_maps_cache', {}))
        if False else None,
    }


def _iter_active_shared_slots() -> list[tuple[int, object, object]]:
    rows: list[tuple[int, object, object]] = []
    try:
        all_accounts = GLOBAL_CACHE.ShMem.GetAllAccounts()
    except Exception as exc:
        log(f'shared memory read failed: {exc}')
        return rows

    for index in range(GLOBAL_CACHE.ShMem.max_num_players):
        account = all_accounts.AccountData[index]
        if not (account.IsSlotActive and account.IsAccount):
            continue
        options = all_accounts.HeroAIOptions[index]
        rows.append((index, account, options))
    return rows


def _get_live_follow_publisher():
    return getattr(GLOBAL_CACHE.ShMem, 'follow_publisher', None)


def _safe_same_party_and_map(publisher, leader_account, account) -> bool:
    try:
        return bool(publisher._same_party_and_map(leader_account, account))
    except Exception:
        return False


def _dump_leader_publish_math() -> None:
    publisher = _get_live_follow_publisher()
    if publisher is None:
        log('leader publish math unavailable: GLOBAL_CACHE.ShMem.follow_publisher is missing')
        return

    try:
        all_accounts = GLOBAL_CACHE.ShMem.GetAllAccounts()
        account_email = Player.GetAccountEmail()
        leader_index = all_accounts.GetSlotByEmail(account_email)
    except Exception as exc:
        log(f'leader publish math unavailable: {exc}')
        return

    if leader_index < 0:
        log('leader publish math unavailable: local player has no visible slot')
        return

    leader_account = all_accounts.AccountData[leader_index]
    leader_options = all_accounts.HeroAIOptions[leader_index]
    if not (leader_account.IsSlotActive and leader_account.IsAccount):
        log('leader publish math unavailable: leader slot is not active/account')
        return

    try:
        points = publisher._get_follow_points()
        leader_x, leader_y = Player.GetXY()
        leader_agent_id = Player.GetAgentID()
        leader_zplane = int(Agent.GetZPlane(leader_agent_id))
        leader_facing = float(Agent.GetRotationAngle(leader_agent_id))
        leader_in_combat = bool(publisher._is_combat_active_for_mode(all_accounts, leader_index, leader_account))
        publisher._update_combat_anchor_facing(leader_in_combat, leader_facing)
        anchor_x, anchor_y, anchor_facing, move_threshold, combat_threshold = publisher._resolve_anchor(
            leader_options,
            leader_x,
            leader_y,
            leader_facing,
            leader_in_combat,
        )
    except Exception as exc:
        log(f'leader publish math failed during anchor resolution: {exc}')
        return

    log('--- leader publish math ---')
    log(
        f'selected_formation={publisher.state.selected_id_cache}'
        f' point_count={len(points)} hold_until_moves={publisher.state.hold_until_leader_moves}'
        f' leader_in_combat={leader_in_combat}'
        f' combat_anchor_facing={publisher.state.combat_anchor_facing}'
    )
    log(
        f'leader anchor=({anchor_x:.1f},{anchor_y:.1f})'
        f' facing={anchor_facing:.4f} raw_leader=({leader_x:.1f},{leader_y:.1f},{leader_zplane})'
        f' thresholds=({move_threshold:.1f},{combat_threshold:.1f})'
    )

    party_positions: list[tuple[float, float]] = []
    for index in range(GLOBAL_CACHE.ShMem.max_num_players):
        account = all_accounts.AccountData[index]
        if not (account.IsSlotActive and account.IsAccount):
            continue
        if all_accounts._is_slot_isolated_from_viewer(index, leader_index):
            continue
        if not _safe_same_party_and_map(publisher, leader_account, account):
            continue
        party_positions.append((float(account.AgentData.Pos.x), float(account.AgentData.Pos.y)))

    navmesh = _autopath.get_navmesh()
    for index in range(GLOBAL_CACHE.ShMem.max_num_players):
        account = all_accounts.AccountData[index]
        if not (account.IsSlotActive and account.IsAccount):
            continue
        if all_accounts._is_slot_isolated_from_viewer(index, leader_index):
            continue
        if not _safe_same_party_and_map(publisher, leader_account, account):
            continue

        options = all_accounts.HeroAIOptions[index]
        party_pos = int(account.AgentPartyData.PartyPosition)
        if party_pos <= 0:
            log(f'slot={index} name="{account.AccountName}" role=idle party_pos={party_pos}')
            continue

        slot_index = party_pos - 1
        if slot_index < 0 or slot_index >= len(points):
            log(
                f'slot={index} name="{account.AccountName}" role=missing-point'
                f' party_pos={party_pos} point_count={len(points)}'
            )
            continue

        local_x, local_y = points[slot_index]
        raw_dx, raw_dy = publisher._rotate_local_to_world(local_x, local_y, anchor_facing)
        raw_x = float(anchor_x + raw_dx)
        raw_y = float(anchor_y + raw_dy)
        published_x = float(options.FollowPos.x)
        published_y = float(options.FollowPos.y)
        published_z = float(options.FollowPos.z)
        branch = 'active'
        if publisher.state.hold_until_leader_moves:
            branch = 'hold'
        elif bool(options.IsFlagged) and publisher._is_nonzero_vec2(options.FlagPos):
            branch = 'personal-flag'

        raw_contains = None
        raw_trap = None
        nearest = None
        snap_dist = None
        if navmesh is not None:
            try:
                raw_contains = navmesh.contains(raw_x, raw_y, publisher.tuning.followpos_contains_margin)
                raw_trap = navmesh.find_trapezoid_id_by_coord((raw_x, raw_y))
                nearest = navmesh.find_nearest_reachable((raw_x, raw_y))
                if nearest is not None:
                    snap_dist = math.hypot(nearest[0] - raw_x, nearest[1] - raw_y)
            except Exception as exc:
                log(f'slot={index} navmesh probe failed: {exc}')

        delta_to_published = math.hypot(published_x - raw_x, published_y - raw_y)
        log(
            f'slot={index} name="{account.AccountName}" branch={branch}'
            f' party_pos={party_pos} local=({local_x:.1f},{local_y:.1f})'
            f' raw=({raw_x:.1f},{raw_y:.1f},{leader_zplane})'
            f' published=({published_x:.1f},{published_y:.1f},{published_z:.1f})'
            f' raw_contains={raw_contains} raw_trap={raw_trap} nearest={nearest}'
            f' snap_dist={snap_dist} raw_to_published={delta_to_published:.1f}'
        )


def _refresh_leader_publish(reload_ini: bool = False) -> None:
    publisher = _get_live_follow_publisher()
    if publisher is None:
        log('leader publish refresh skipped: GLOBAL_CACHE.ShMem.follow_publisher is missing')
        return
    try:
        if reload_ini and hasattr(publisher, 'refresh_from_ini'):
            publisher.refresh_from_ini()
            log('leader publish INI reloaded')
        publisher.publish(force=True)
        log('leader publish refreshed with force=True')
    except Exception as exc:
        log(f'leader publish refresh failed: {exc}')


def _dump_leader_publish_state() -> None:
    local_email = ''
    try:
        local_email = str(Player.GetAccountEmail() or '')
    except Exception:
        pass

    log('--- leader publish / shared-memory state ---')
    log(f'local account email={local_email or "(none)"}')
    for index, account, options in _iter_active_shared_slots():
        pos_x = float(account.AgentData.Pos.x)
        pos_y = float(account.AgentData.Pos.y)
        follow_x = float(options.FollowPos.x)
        follow_y = float(options.FollowPos.y)
        follow_z = float(options.FollowPos.z)
        offset_x = float(options.FollowOffset.x)
        offset_y = float(options.FollowOffset.y)
        flagged = bool(options.IsFlagged)
        ready = bool(options.LeaderFollowReady)
        in_aggro = bool(getattr(account, 'InAggro', False))
        distance = math.hypot(follow_x - pos_x, follow_y - pos_y)
        log(
            f'slot={index} name="{account.AccountName}" email="{account.AccountEmail}"'
            f' party_pos={int(account.AgentPartyData.PartyPosition)}'
            f' active={bool(account.IsSlotActive)} aggro={in_aggro}'
            f' ready={ready} flagged={flagged}'
            f' agent=({pos_x:.1f},{pos_y:.1f})'
            f' follow=({follow_x:.1f},{follow_y:.1f},{follow_z:.1f})'
            f' offset=({offset_x:.1f},{offset_y:.1f})'
            f' dist_to_follow={distance:.1f}'
        )


def _probe_shared_follow_points() -> None:
    log('--- probing shared FollowPos values against current navmesh ---')
    navmesh = _autopath.get_navmesh()
    if navmesh is None:
        log('shared FollowPos probe aborted: navmesh is not loaded')
        return

    for index, account, options in _iter_active_shared_slots():
        follow_x = float(options.FollowPos.x)
        follow_y = float(options.FollowPos.y)
        follow_z = float(options.FollowPos.z)
        contains_20 = navmesh.contains(follow_x, follow_y, 20.0)
        contains_100 = navmesh.contains(follow_x, follow_y, 100.0)
        trap_id = navmesh.find_trapezoid_id_by_coord((follow_x, follow_y))
        nearest = navmesh.find_nearest_reachable((follow_x, follow_y))
        if nearest is None:
            snap_dist = -1.0
        else:
            snap_dist = math.hypot(nearest[0] - follow_x, nearest[1] - follow_y)
        log(
            f'slot={index} name="{account.AccountName}"'
            f' ready={bool(options.LeaderFollowReady)}'
            f' follow=({follow_x:.1f},{follow_y:.1f},{follow_z:.1f})'
            f' contains20={contains_20} contains100={contains_100}'
            f' trap_id={trap_id} nearest={nearest} snap_dist={snap_dist:.1f}'
        )


def _clear_offline_cache() -> None:
    Map.Pathing.ClearPathingCache()
    log('cleared offline FFNA pathing cache')


def _clear_live_cache() -> None:
    Map.Pathing.ClearPathingCache(include_live=True)
    log('cleared live pathing snapshots and AutoPathing navmesh cache')


def _refresh_without_reload() -> None:
    navmesh_before = _autopath.get_navmesh()
    log(f'refresh requested: navmesh_loaded_before={navmesh_before is not None}')
    for _ in _autopath.load_pathing_maps():
        pass
    navmesh_after = _autopath.get_navmesh()
    log(f'refresh completed: navmesh_loaded_after={navmesh_after is not None}')


def dump_snapshot(label: str = 'snapshot') -> None:
    map_id = Map.GetMapID()
    map_ready = Map.IsMapReady()
    map_loading = Map.IsMapLoading()
    is_explorable = Map.IsExplorable()
    metadata = _safe_map_metadata()
    player_xy = _safe_player_xy()
    player_zplane = _safe_player_zplane()
    live_layers = Map.Pathing.GetPathingMaps()
    raw_layers = Map.Pathing.GetPathingMapsRaw()
    navmesh = _autopath.get_navmesh()
    group_key = _autopath._get_group_key(map_id) if map_id else ()
    cache_entry = _autopath.pathing_map_cache.get(group_key) if group_key else None

    log(f'--- {label} ---')
    log(
        'map'
        f' id={map_id} ready={map_ready} loading={map_loading} explorable={is_explorable}'
        f' name="{metadata["map_name"]}" type={metadata["instance_type"]}'
        f' region={metadata["region_id"]}:{metadata["region_name"]}'
        f' district={metadata["district"]}'
        f' language={metadata["language_id"]}:{metadata["language_name"]}'
        f' uptime_ms={metadata["uptime"]}'
        f' player=({player_xy[0]:.1f}, {player_xy[1]:.1f}, z={player_zplane})'
    )
    log(
        f'autopath cache_keys={len(_autopath.pathing_map_cache)}'
        f' group_key={group_key}'
        f' cache_hit={cache_entry is not None}'
        f' navmesh_loaded={navmesh is not None}'
    )
    log(f'live pathing layers={len(live_layers)} raw layers={len(raw_layers)}')
    for line in _layer_summary(live_layers):
        log(line)
    if raw_layers:
        raw_counts = [len(getattr(layer, 'trapezoids', []) or []) for layer in raw_layers]
        log(f'raw layer trapezoid counts={raw_counts}')

    if navmesh is None:
        log('navmesh: NONE')
        return

    player_trap = navmesh.find_trapezoid_id_by_coord(player_xy)
    player_contains = navmesh.contains(player_xy[0], player_xy[1], 20.0)
    nearest_player = navmesh.find_nearest_reachable(player_xy)
    log(
        f'navmesh: map_id={navmesh.map_id} trapezoids={len(navmesh.trapezoids)}'
        f' player_contains={player_contains} player_trap={player_trap}'
        f' nearest_player={nearest_player}'
    )
    _dump_leader_publish_state()


def probe_point(x: float, y: float, label: str) -> None:
    global _last_probe_xy

    _last_probe_xy = (x, y)
    navmesh = _autopath.get_navmesh()
    log(f'--- probe {label} ({x:.1f}, {y:.1f}) ---')
    if navmesh is None:
        log('probe aborted: navmesh is not loaded')
        return

    contains_0 = navmesh.contains(x, y, 0.0)
    contains_20 = navmesh.contains(x, y, 20.0)
    contains_100 = navmesh.contains(x, y, 100.0)
    trap_id = navmesh.find_trapezoid_id_by_coord((x, y))
    nearest_trap = navmesh.find_nearest_trapezoid_id(x, y)
    nearest_reachable = navmesh.find_nearest_reachable((x, y))

    log(
        f'contains margin0={contains_0} margin20={contains_20} margin100={contains_100}'
        f' trap_id={trap_id} nearest_trap={nearest_trap} nearest_reachable={nearest_reachable}'
    )

    if nearest_reachable is not None:
        dx = nearest_reachable[0] - x
        dy = nearest_reachable[1] - y
        log(f'nearest_reachable_delta=({dx:.1f}, {dy:.1f}) dist={math.hypot(dx, dy):.1f}')

    player_xy = _safe_player_xy()
    try:
        los = navmesh.has_line_of_sight(player_xy, (x, y))
    except Exception as exc:
        log(f'line_of_sight failed: {exc}')
    else:
        log(f'line_of_sight player->{label}={los}')


def _force_reload_and_dump() -> None:
    before_navmesh = _autopath.get_navmesh()
    before_cache = len(_autopath.pathing_map_cache)
    log(
        f'force reload requested: before navmesh_loaded={before_navmesh is not None}'
        f' cache_keys={before_cache}'
    )
    Map.Pathing.ForceReloadNavMesh()
    after_navmesh = _autopath.get_navmesh()
    after_cache = len(_autopath.pathing_map_cache)
    log(
        f'force reload completed: after navmesh_loaded={after_navmesh is not None}'
        f' cache_keys={after_cache}'
    )
    dump_snapshot('after force reload')


def _request_path() -> None:
    global _path_requested, _path_started_at, _path_result, _path_completed_in

    if _path_requested:
        log('path request ignored: search already in progress')
        return

    player_xy = _safe_player_xy()
    player_zplane = _safe_player_zplane()
    _path_requested = True
    _path_started_at = time.time()
    _path_result = []
    _path_completed_in = 0.0
    log(
        f'path request start=({player_xy[0]:.1f}, {player_xy[1]:.1f}, {player_zplane})'
        f' goal=({_target_x:.1f}, {_target_y:.1f}, {player_zplane})'
    )

    def _path_coro():
        global _path_requested, _path_result, _path_completed_in

        _path_result = yield from _autopath.get_path(
            (player_xy[0], player_xy[1], player_zplane),
            (float(_target_x), float(_target_y), player_zplane),
        )
        _path_completed_in = time.time() - _path_started_at
        _path_requested = False
        log(
            f'path request completed: points={len(_path_result)}'
            f' elapsed={_path_completed_in:.3f}s'
        )
        if _path_result:
            first = _path_result[0]
            last = _path_result[-1]
            log(f'path endpoints: first={first} last={last}')
        yield

    GLOBAL_CACHE.Coroutines.append(_path_coro())


def _draw_path_overlay() -> None:
    if len(_path_result) < 2:
        return

    color = 0xFF00FFFF
    for idx in range(len(_path_result) - 1):
        x1, y1, z1 = _path_result[idx]
        x2, y2, z2 = _path_result[idx + 1]
        DXOverlay().DrawLine3D(x1, y1, z1 - 125, x2, y2, z2 - 125, color, False)


def main() -> None:
    global _target_x, _target_y

    if PyImGui.begin('NavMesh Debug', PyImGui.WindowFlags.AlwaysAutoResize):
        player_xy = _safe_player_xy()
        player_zplane = _safe_player_zplane()

        if _target_x == 0 and _target_y == 0:
            _target_x = int(player_xy[0])
            _target_y = int(player_xy[1])

        PyImGui.text(f'Map ID: {Map.GetMapID()}')
        metadata = _safe_map_metadata()
        PyImGui.text(
            f'Map Ready: {Map.IsMapReady()} | Loading: {Map.IsMapLoading()} | Explorable: {Map.IsExplorable()}'
        )
        PyImGui.text(
            f'Map: {metadata["map_name"]} | Type: {metadata["instance_type"]} | Uptime: {metadata["uptime"]} ms'
        )
        PyImGui.text(
            f'Region: {metadata["region_id"]}:{metadata["region_name"]} | District: {metadata["district"]} | '
            f'Language: {metadata["language_id"]}:{metadata["language_name"]}'
        )
        PyImGui.text(f'Player: ({player_xy[0]:.1f}, {player_xy[1]:.1f}, z={player_zplane})')
        PyImGui.text(f'NavMesh Loaded: {_autopath.get_navmesh() is not None}')
        PyImGui.text(f'AutoPath cache keys: {len(_autopath.pathing_map_cache)}')

        if PyImGui.button('Dump Snapshot'):
            dump_snapshot()
        PyImGui.same_line(0, -1)
        if PyImGui.button('Force Reload + Dump'):
            _force_reload_and_dump()
        PyImGui.same_line(0, -1)
        if PyImGui.button('Clear Live Cache'):
            _clear_live_cache()
        PyImGui.same_line(0, -1)
        if PyImGui.button('Clear Offline Cache'):
            _clear_offline_cache()
        PyImGui.same_line(0, -1)
        if PyImGui.button('Refresh NavMesh'):
            _refresh_without_reload()
        PyImGui.same_line(0, -1)
        if PyImGui.button('Use Player As Target'):
            _target_x = int(player_xy[0])
            _target_y = int(player_xy[1])
            log(f'target set to player: ({_target_x}, {_target_y})')

        PyImGui.separator()
        _target_x = int(PyImGui.input_int('Target X', int(_target_x)))
        _target_y = int(PyImGui.input_int('Target Y', int(_target_y)))

        if PyImGui.button('Probe Player'):
            probe_point(player_xy[0], player_xy[1], 'player')
        PyImGui.same_line(0, -1)
        if PyImGui.button('Probe Target'):
            probe_point(float(_target_x), float(_target_y), 'target')
        PyImGui.same_line(0, -1)
        if PyImGui.button('Probe Shared FollowPos'):
            _probe_shared_follow_points()
        PyImGui.same_line(0, -1)
        if PyImGui.button('Dump Leader State'):
            _dump_leader_publish_state()
        PyImGui.same_line(0, -1)
        if PyImGui.button('Dump Leader Math'):
            _dump_leader_publish_math()
        PyImGui.same_line(0, -1)
        if PyImGui.button('Refresh Leader Publish'):
            _refresh_leader_publish(reload_ini=False)
        PyImGui.same_line(0, -1)
        if PyImGui.button('Reload INI + Publish'):
            _refresh_leader_publish(reload_ini=True)
        PyImGui.same_line(0, -1)
        if PyImGui.button('Search Path'):
            _request_path()

        if _path_requested:
            PyImGui.text('Path search in progress...')
        else:
            PyImGui.text(f'Last path points: {len(_path_result)} | Elapsed: {_path_completed_in:.3f}s')

        if _last_probe_xy is not None:
            PyImGui.text(f'Last probe: ({_last_probe_xy[0]:.1f}, {_last_probe_xy[1]:.1f})')

        if PyImGui.collapsing_header('Shared Follow State', PyImGui.TreeNodeFlags.DefaultOpen):
            for index, account, options in _iter_active_shared_slots():
                PyImGui.text(
                    f'[{index}] {account.AccountName} ready={bool(options.LeaderFollowReady)} '
                    f'flagged={bool(options.IsFlagged)} party_pos={int(account.AgentPartyData.PartyPosition)}'
                )
                PyImGui.text(
                    f'    agent=({float(account.AgentData.Pos.x):.1f}, {float(account.AgentData.Pos.y):.1f}) '
                    f'follow=({float(options.FollowPos.x):.1f}, {float(options.FollowPos.y):.1f}, {float(options.FollowPos.z):.1f}) '
                    f'offset=({float(options.FollowOffset.x):.1f}, {float(options.FollowOffset.y):.1f})'
                )

        if PyImGui.collapsing_header('Leader Publisher', PyImGui.TreeNodeFlags.DefaultOpen):
            publisher = _get_live_follow_publisher()
            if publisher is None:
                PyImGui.text('follow_publisher unavailable on GLOBAL_CACHE.ShMem')
            else:
                PyImGui.text(f'selected_formation={publisher.state.selected_id_cache}')
                PyImGui.text(
                    f'hold_until_leader_moves={publisher.state.hold_until_leader_moves} '
                    f'combat_anchor_facing={publisher.state.combat_anchor_facing}'
                )
                PyImGui.text(
                    f'followpos_bypass_unreachable_validation='
                    f'{publisher.tuning.followpos_bypass_unreachable_validation}'
                )
                entry = publisher.state.leader_entry_pos
                if entry is not None:
                    PyImGui.text(f'leader_entry_pos=({entry[0]:.1f}, {entry[1]:.1f})')
                points = publisher._get_follow_points()
                PyImGui.text(f'formation_points={len(points)}')
                for idx, (fx, fy) in enumerate(points[:11]):
                    PyImGui.text(f'  p{idx + 1}=({fx:.1f}, {fy:.1f})')

        if PyImGui.collapsing_header('Recent Log', PyImGui.TreeNodeFlags.DefaultOpen):
            for line in _logs[-30:]:
                PyImGui.text_wrapped(line)

        PyImGui.end()

    _draw_path_overlay()


if __name__ == '__main__':
    main()
