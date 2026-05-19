import math

from dataclasses import dataclass, field
from typing import Protocol

from Py4GWCoreLib import Agent, Party, Player, Range, ThrottledTimer
from Py4GWCoreLib.IniManager import IniManager
from Py4GWCoreLib.Map import Map
from Py4GWCoreLib.Pathing import AutoPathing
from Py4GWCoreLib.py4gwcorelib_src.Utils import Utils
from Py4GWCoreLib.GlobalCache.shared_memory_src.AccountStruct import AccountStruct
from Py4GWCoreLib.GlobalCache.shared_memory_src.AllAccounts import AllAccounts
from Py4GWCoreLib.GlobalCache.shared_memory_src.HeroAIOptionStruct import HeroAIOptionStruct
from Py4GWCoreLib.native_src.internals.types import Vec2f


# Force-load the navmesh on first call. AutoPathing's cache is normally
# populated by get_path() coroutine pumps; leader-side validation skips that.
def _get_navmesh():
    autopath = AutoPathing()
    nav = autopath.get_navmesh()
    if nav is not None:
        return nav
    try:
        for _ in autopath.load_pathing_maps():
            pass
    except Exception:
        return None
    return autopath.get_navmesh()


class SharedMemoryManagerProtocol(Protocol):
    max_num_players: int

    def GetAllAccounts(self) -> AllAccounts:
        ...


@dataclass(slots=True)
class FollowIniConfig:
    global_ini_path: str = "HeroAI"
    formations_ini_name: str = "FollowModule_Formations.ini"
    settings_ini_name: str = "FollowModule_Settings.ini"
    runtime_ini_name: str = "FollowRuntime.ini"
    formations_section: str = "Formations"
    runtime_section: str = "FollowRuntime"
    formation_id_prefix: str = "FormationId:"
    formation_name_prefix: str = "Formation:"
    selected_id_key: str = "selected_id"
    selected_name_key: str = "selected"
    formation_count_var_name: str = "formation_count"
    count_key: str = "count"
    point_count_key: str = "point_count"
    point_x_key_template: str = "p{index}_x"
    point_y_key_template: str = "p{index}_y"
    max_follow_slots: int = 11
    ini_reload_ms: int = 1000
    publish_interval_ms: int = 100
    combat_publish_interval_ms: int = 1000


@dataclass(slots=True)
class FollowThresholdConfig:
    default_follow_threshold: float = field(default_factory=lambda: float(Range.Area.value))
    combat_follow_threshold: float = field(default_factory=lambda: float(Range.Adjacent.value))
    flagged_follow_threshold: float = 0.0
    disabled_threshold: float = -1.0


@dataclass(slots=True)
class FollowTuningConfig:
    nonzero_epsilon: float = 0.001
    leader_move_release_distance: float = 1.0
    # Off-mesh snap distance cap. Snaps farther than this fall back to anchor.
    followpos_max_reach: float = field(default_factory=lambda: float(Range.Area.value))
    # Allow a small amount of extra distance from the leader beyond the
    # intended formation radius before we give up and stack at the anchor.
    followpos_anchor_slack: float = 50.0
    # NavMesh.contains margin — points just barely off-mesh still count as on.
    followpos_contains_margin: float = 20.0


@dataclass(slots=True)
class FollowPublisherState:
    formations_ini_key: str = ""
    settings_ini_key: str = ""
    runtime_ini_key: str = ""
    ini_vars_registered: bool = False
    registered_follow_sections: set[str] = field(default_factory=set)
    selected_id_cache: str = ""
    points_cache: list[tuple[float, float]] = field(default_factory=list)
    map_signature: tuple[int, int, int, int, int] | None = None
    hold_until_leader_moves: bool = False
    leader_entry_pos: tuple[float, float] | None = None
    leader_in_combat_last: bool = False
    combat_anchor_facing: float | None = None


class FollowFormationPublisher:
    def __init__(self, shared_memory_manager: SharedMemoryManagerProtocol):
        self.shared_memory_manager = shared_memory_manager
        self.ini = FollowIniConfig()
        self.thresholds = FollowThresholdConfig()
        self.tuning = FollowTuningConfig()
        self.state = FollowPublisherState()
        self.state.selected_id_cache = "builtin_default"
        self.state.points_cache = self._get_default_follow_points()
        self.ini_reload_timer = ThrottledTimer(self.ini.ini_reload_ms)
        self.publish_timer = ThrottledTimer(self.ini.publish_interval_ms)
        self.combat_publish_timer = ThrottledTimer(self.ini.combat_publish_interval_ms)

    def _get_default_follow_points(self) -> list[tuple[float, float]]:
        # Stable built-in fallback so follow publication never collapses to an empty template.
        return [
            (144.0, 180.0),
            (0.0, 180.0),
            (-144.0, 180.0),
            (216.0, 324.0),
            (72.0, 324.0),
            (-72.0, 324.0),
            (-216.0, 324.0),
            (288.0, 468.0),
            (144.0, 468.0),
            (0.0, 468.0),
            (-144.0, 468.0),
        ]

    def _ensure_global_ini_key_strict(self, path: str, filename: str) -> str:
        im = IniManager()
        key = im.ensure_global_key(path, filename)
        if not key:
            return ""
        try:
            node = im._get_node(key)
            if node and getattr(node, "is_global", False):
                return key
            if hasattr(im, "_handlers") and key in im._handlers:
                del im._handlers[key]
            key = im.ensure_global_key(path, filename)
        except Exception:
            pass
        return key

    def _ensure_follow_ini_keys(self) -> None:
        if not self.state.formations_ini_key:
            self.state.formations_ini_key = self._ensure_global_ini_key_strict(self.ini.global_ini_path, self.ini.formations_ini_name)
        if not self.state.settings_ini_key:
            self.state.settings_ini_key = self._ensure_global_ini_key_strict(self.ini.global_ini_path, self.ini.settings_ini_name)
        if not self.state.runtime_ini_key:
            self.state.runtime_ini_key = self._ensure_global_ini_key_strict(self.ini.global_ini_path, self.ini.runtime_ini_name)
        if self.state.ini_vars_registered:
            return

        im = IniManager()
        if self.state.settings_ini_key:
            im.add_str(self.state.settings_ini_key, self.ini.selected_id_key, self.ini.formations_section, self.ini.selected_id_key, "")
            im.add_str(self.state.settings_ini_key, self.ini.selected_name_key, self.ini.formations_section, self.ini.selected_name_key, "")
        if self.state.formations_ini_key:
            im.add_int(self.state.formations_ini_key, self.ini.formation_count_var_name, self.ini.formations_section, self.ini.count_key, 0)
        if self.state.runtime_ini_key:
            im.add_float(
                self.state.runtime_ini_key,
                "follow_move_threshold_default",
                self.ini.runtime_section,
                "follow_move_threshold_default",
                self.thresholds.default_follow_threshold,
            )
            im.add_float(
                self.state.runtime_ini_key,
                "follow_move_threshold_combat",
                self.ini.runtime_section,
                "follow_move_threshold_combat",
                self.thresholds.combat_follow_threshold,
            )
            im.add_float(
                self.state.runtime_ini_key,
                "follow_move_threshold_flagged",
                self.ini.runtime_section,
                "follow_move_threshold_flagged",
                self.thresholds.flagged_follow_threshold,
            )
        self.state.ini_vars_registered = True

    def _load_ini_vars_once(
        self,
        key: str,
        force_var_refresh: bool = False,
        reload_from_disk: bool = False,
    ) -> None:
        if not key:
            return
        im = IniManager()
        try:
            node = im._get_node(key)
            if reload_from_disk:
                im.reload(key)
            if node and force_var_refresh:
                node.vars_loaded = False
            im.load_once(key)
        except Exception:
            pass

    def _ensure_follow_section_var_defs(self, section: str) -> None:
        if not self.state.formations_ini_key or not section:
            return
        if section in self.state.registered_follow_sections:
            return
        im = IniManager()
        sec_tag = section.replace(":", "_")
        im.add_int(self.state.formations_ini_key, f"{sec_tag}_{self.ini.point_count_key}", section, self.ini.point_count_key, 0)
        for index in range(self.ini.max_follow_slots):
            x_key = self.ini.point_x_key_template.format(index=index)
            y_key = self.ini.point_y_key_template.format(index=index)
            im.add_float(self.state.formations_ini_key, f"{sec_tag}_{x_key}", section, x_key, 0.0)
            im.add_float(self.state.formations_ini_key, f"{sec_tag}_{y_key}", section, y_key, 0.0)
        self.state.registered_follow_sections.add(section)
        self._load_ini_vars_once(self.state.formations_ini_key, force_var_refresh=True)

    def _reload_thresholds(self, im: IniManager) -> None:
        if not self.state.runtime_ini_key:
            return
        self.thresholds.default_follow_threshold = max(
            0.0,
            float(im.getFloat(self.state.runtime_ini_key, "follow_move_threshold_default", float(Range.Area.value), section=self.ini.runtime_section))
        )
        self.thresholds.combat_follow_threshold = max(
            0.0,
            float(im.getFloat(self.state.runtime_ini_key, "follow_move_threshold_combat", float(Range.Adjacent.value), section=self.ini.runtime_section))
        )
        self.thresholds.flagged_follow_threshold = max(
            0.0,
            float(im.getFloat(self.state.runtime_ini_key, "follow_move_threshold_flagged", 0.0, section=self.ini.runtime_section))
        )

    def _resolve_selected_formation_id(self, im: IniManager) -> str:
        selected_id = str(im.getStr(self.state.settings_ini_key, self.ini.selected_id_key, "", section=self.ini.formations_section) or "").strip()
        if selected_id:
            return selected_id

        selected_name = str(im.getStr(self.state.settings_ini_key, self.ini.selected_name_key, "", section=self.ini.formations_section) or "").strip()
        formation_count = max(
            0,
            im.getInt(self.state.formations_ini_key, self.ini.formation_count_var_name, 0, section=self.ini.formations_section),
        )
        for index in range(formation_count):
            name = str(im.read_key(self.state.formations_ini_key, self.ini.formations_section, f"name_{index}", "") or "").strip()
            if name == selected_name:
                return str(im.read_key(self.state.formations_ini_key, self.ini.formations_section, f"id_{index}", "") or "").strip()
        for index in range(formation_count):
            formation_id = str(im.read_key(self.state.formations_ini_key, self.ini.formations_section, f"id_{index}", "") or "").strip()
            if formation_id:
                return formation_id
        return ""

    def _resolve_selected_formation_section(self, im: IniManager, selected_id: str) -> str:
        section = f"{self.ini.formation_id_prefix}{selected_id}"
        if im.read_key(self.state.formations_ini_key, section, "name", ""):
            return section

        formation_count = max(0, im.read_int(self.state.formations_ini_key, self.ini.formations_section, self.ini.count_key, 0))
        for index in range(formation_count):
            formation_id = str(im.read_key(self.state.formations_ini_key, self.ini.formations_section, f"id_{index}", "") or "").strip()
            if formation_id == selected_id:
                name = str(im.read_key(self.state.formations_ini_key, self.ini.formations_section, f"name_{index}", "") or "").strip()
                if name:
                    return f"{self.ini.formation_name_prefix}{name}"
                break
        return section

    def _reload_follow_points_from_ini(self) -> None:
        try:
            self._ensure_follow_ini_keys()
            if not self.state.formations_ini_key or not self.state.settings_ini_key:
                self.state.selected_id_cache = "builtin_default"
                self.state.points_cache = self._get_default_follow_points()
                return

            im = IniManager()
            self._load_ini_vars_once(
                self.state.settings_ini_key,
                force_var_refresh=True,
                reload_from_disk=True,
            )
            self._load_ini_vars_once(
                self.state.formations_ini_key,
                force_var_refresh=True,
                reload_from_disk=True,
            )
            self._load_ini_vars_once(
                self.state.runtime_ini_key,
                force_var_refresh=True,
                reload_from_disk=True,
            )
            self._reload_thresholds(im)

            selected_id = self._resolve_selected_formation_id(im)
            if not selected_id:
                self.state.selected_id_cache = "builtin_default"
                self.state.points_cache = self._get_default_follow_points()
                return

            section = self._resolve_selected_formation_section(im, selected_id)
            self._ensure_follow_section_var_defs(section)
            sec_tag = section.replace(":", "_")
            point_count = max(
                0,
                min(
                    self.ini.max_follow_slots,
                    im.getInt(self.state.formations_ini_key, f"{sec_tag}_{self.ini.point_count_key}", 0, section=section),
                ),
            )
            points: list[tuple[float, float]] = []
            for index in range(point_count):
                x_key = self.ini.point_x_key_template.format(index=index)
                y_key = self.ini.point_y_key_template.format(index=index)
                x = float(im.getFloat(self.state.formations_ini_key, f"{sec_tag}_{x_key}", 0.0, section=section))
                y = float(im.getFloat(self.state.formations_ini_key, f"{sec_tag}_{y_key}", 0.0, section=section))
                points.append((x, y))

            self.state.selected_id_cache = selected_id
            self.state.points_cache = points if points else self._get_default_follow_points()
        except Exception:
            self.state.selected_id_cache = "builtin_default"
            self.state.points_cache = self._get_default_follow_points()

    def _get_follow_points(self) -> list[tuple[float, float]]:
        if (not self.state.points_cache) or self.ini_reload_timer.IsExpired():
            self._reload_follow_points_from_ini()
            self.ini_reload_timer.Reset()
        return self.state.points_cache

    @staticmethod
    def _rotate_local_to_world(local_x: float, local_y: float, facing_angle: float) -> tuple[float, float]:
        angle = float(facing_angle) - (math.pi / 2.0)
        c = -math.cos(angle)
        s = -math.sin(angle)
        return ((local_x * c) - (local_y * s), (local_x * s) + (local_y * c))

    @staticmethod
    def _same_party_and_map(a: AccountStruct, b: AccountStruct) -> bool:
        return (
            a.AgentPartyData.PartyID == b.AgentPartyData.PartyID and
            a.AgentData.Map.MapID == b.AgentData.Map.MapID and
            a.AgentData.Map.Region == b.AgentData.Map.Region and
            a.AgentData.Map.District == b.AgentData.Map.District and
            a.AgentData.Map.Language == b.AgentData.Map.Language
        )

    def _is_nonzero_vec2(self, vec: Vec2f) -> bool:
        return abs(float(vec.x)) > self.tuning.nonzero_epsilon or abs(float(vec.y)) > self.tuning.nonzero_epsilon

    def _reset_follow_slot(
        self,
        options: HeroAIOptionStruct,
        *,
        invalidate_flags: bool = False,
    ) -> None:
        options.FollowPos.x = 0.0
        options.FollowPos.y = 0.0
        options.FollowPos.z = 0.0
        options.FollowOffset.x = 0.0
        options.FollowOffset.y = 0.0
        options.FollowMoveThreshold = self.thresholds.disabled_threshold
        options.FollowMoveThresholdCombat = self.thresholds.disabled_threshold
        options.LeaderFollowReady = False
        if invalidate_flags:
            options.IsFlagged = False
            options.FlagPos.x = 0.0
            options.FlagPos.y = 0.0
            options.AllFlag.x = 0.0
            options.AllFlag.y = 0.0
            options.FlagFacingAngle = 0.0

    def _clear_follow_publish_state(
        self,
        all_accounts: AllAccounts,
        leader_index: int,
        *,
        invalidate_flags: bool = False,
    ) -> None:
        self.state.map_signature = None
        self.state.hold_until_leader_moves = False
        self.state.leader_entry_pos = None
        self.state.leader_in_combat_last = False
        self.state.combat_anchor_facing = None
        for index in range(self.shared_memory_manager.max_num_players):
            account = all_accounts.AccountData[index]
            if (not account.IsAccount) or all_accounts._is_slot_isolated_from_viewer(index, leader_index):
                continue
            self._reset_follow_slot(all_accounts.HeroAIOptions[index], invalidate_flags=invalidate_flags)

    def _handle_map_signature_change(
        self,
        all_accounts: AllAccounts,
        leader_index: int,
        current_map_signature: tuple[int, int, int, int, int],
        leader_x: float,
        leader_y: float,
    ) -> None:
        self._clear_follow_publish_state(all_accounts, leader_index, invalidate_flags=True)
        self.state.map_signature = current_map_signature
        self.state.hold_until_leader_moves = True
        self.state.leader_entry_pos = (float(leader_x), float(leader_y))

    def _apply_idle_slot(self, options: HeroAIOptionStruct) -> None:
        options.FollowPos.x = 0.0
        options.FollowPos.y = 0.0
        options.FollowPos.z = 0.0
        options.FollowOffset.x = 0.0
        options.FollowOffset.y = 0.0
        options.FollowMoveThreshold = self.thresholds.disabled_threshold
        options.FollowMoveThresholdCombat = self.thresholds.disabled_threshold
        options.LeaderFollowReady = False

    def _apply_missing_point_slot(self, options: HeroAIOptionStruct, account: AccountStruct, leader_zplane: int) -> None:
        options.FollowOffset.x = 0.0
        options.FollowOffset.y = 0.0
        if self.state.hold_until_leader_moves:
            options.FollowPos.x = float(account.AgentData.Pos.x)
            options.FollowPos.y = float(account.AgentData.Pos.y)
            options.FollowPos.z = float(leader_zplane)
        else:
            options.FollowPos.x = 0.0
            options.FollowPos.y = 0.0
            options.FollowPos.z = 0.0
        options.FollowMoveThreshold = self.thresholds.disabled_threshold
        options.FollowMoveThresholdCombat = self.thresholds.disabled_threshold
        options.LeaderFollowReady = False

    def _apply_held_slot(self, options: HeroAIOptionStruct, account: AccountStruct, leader_zplane: int) -> None:
        options.FollowPos.x = float(account.AgentData.Pos.x)
        options.FollowPos.y = float(account.AgentData.Pos.y)
        options.FollowPos.z = float(leader_zplane)

    def _apply_personal_flag_slot(self, options: HeroAIOptionStruct, leader_zplane: int) -> None:
        options.FollowPos.x = float(options.FlagPos.x)
        options.FollowPos.y = float(options.FlagPos.y)
        options.FollowPos.z = float(leader_zplane)
        options.FollowMoveThreshold = self.thresholds.flagged_follow_threshold
        options.FollowMoveThresholdCombat = self.thresholds.flagged_follow_threshold

    def _update_combat_anchor_facing(self, leader_in_combat: bool, leader_facing: float) -> None:
        if leader_in_combat:
            if (not self.state.leader_in_combat_last) or self.state.combat_anchor_facing is None:
                self.state.combat_anchor_facing = float(leader_facing)
        else:
            self.state.combat_anchor_facing = None
        self.state.leader_in_combat_last = leader_in_combat

    def _is_combat_active_for_mode(
        self,
        all_accounts: AllAccounts,
        leader_index: int,
        leader_account: AccountStruct,
    ) -> bool:
        from HeroAI.settings import Settings

        mode = Settings().get_combat_range_mode()
        if int(getattr(leader_account.AgentPartyData, "PartyPosition", -1)) == 0:
            return bool(getattr(leader_account, "InAggro", False))
        if mode == Settings.COMBAT_RANGE_MODE_LEGACY:
            return bool(getattr(leader_account, "InAggro", False))

        for index in range(self.shared_memory_manager.max_num_players):
            account = all_accounts.AccountData[index]
            if not (account.IsSlotActive and account.IsAccount) or all_accounts._is_slot_isolated_from_viewer(index, leader_index):
                continue
            if not self._same_party_and_map(leader_account, account):
                continue
            if bool(getattr(account, "InAggro", False)):
                return True
        return False

    def _resolve_anchor(
        self,
        leader_options: HeroAIOptionStruct,
        leader_x: float,
        leader_y: float,
        leader_facing: float,
        leader_in_combat: bool,
    ) -> tuple[float, float, float, float, float]:
        if bool(leader_options.IsFlagged) and self._is_nonzero_vec2(leader_options.AllFlag):
            return (
                float(leader_options.AllFlag.x),
                float(leader_options.AllFlag.y),
                float(leader_options.FlagFacingAngle),
                self.thresholds.flagged_follow_threshold,
                self.thresholds.flagged_follow_threshold,
            )
        return (
            float(leader_x),
            float(leader_y),
            float(self.state.combat_anchor_facing if leader_in_combat and self.state.combat_anchor_facing is not None else leader_facing),
            self.thresholds.default_follow_threshold,
            self.thresholds.combat_follow_threshold,
        )

    def _validate_followpos(
        self,
        raw_x: float,
        raw_y: float,
        fallback_x: float,
        fallback_y: float,
        leader_zplane: int,
        fallback_candidates: list[tuple[float, float]] | None = None,
    ) -> tuple[float, float]:
        """Use the raw FollowPos when valid; otherwise fall back near party mass."""

        navmesh = _get_navmesh()
        if navmesh is None:
            return (raw_x, raw_y)

        try:
            if navmesh.contains(raw_x, raw_y, self.tuning.followpos_contains_margin):
                return (raw_x, raw_y)
        except Exception:
            return (raw_x, raw_y)
        max_fallback_distance = float(Range.Spellcast.value)

        def _resolve_candidate(candidate_x: float, candidate_y: float) -> tuple[float, float] | None:
            try:
                if navmesh.contains(candidate_x, candidate_y, self.tuning.followpos_contains_margin):
                    resolved_x = float(candidate_x)
                    resolved_y = float(candidate_y)
                else:
                    snapped = navmesh.find_nearest_reachable((candidate_x, candidate_y))
                    if snapped is None:
                        return None
                    resolved_x = float(snapped[0])
                    resolved_y = float(snapped[1])
            except Exception:
                return None

            if math.hypot(resolved_x - fallback_x, resolved_y - fallback_y) > max_fallback_distance:
                return None
            return (resolved_x, resolved_y)

        candidate_centers = [
            (float(candidate_x), float(candidate_y))
            for candidate_x, candidate_y in (fallback_candidates or [])
        ]

        midpoint_candidates: list[tuple[float, float]] = []
        candidate_count = len(candidate_centers)
        for i in range(candidate_count):
            left_x, left_y = candidate_centers[i]
            for j in range(i + 1, candidate_count):
                right_x, right_y = candidate_centers[j]
                midpoint_candidates.append(
                    ((left_x + right_x) / 2.0, (left_y + right_y) / 2.0)
                )

        midpoint_candidates.sort(key=lambda pos: math.hypot(pos[0] - raw_x, pos[1] - raw_y))
        for midpoint_x, midpoint_y in midpoint_candidates:
            resolved_midpoint = _resolve_candidate(midpoint_x, midpoint_y)
            if resolved_midpoint is not None:
                return resolved_midpoint

        candidate_centers.sort(key=lambda pos: math.hypot(pos[0] - raw_x, pos[1] - raw_y))
        adjacent_radius = float(Range.Adjacent.value)
        for center_x, center_y in candidate_centers:
            vec_x = raw_x - center_x
            vec_y = raw_y - center_y
            length = math.hypot(vec_x, vec_y)
            if length <= 0.001:
                norm_x, norm_y = 0.0, -1.0
            else:
                norm_x, norm_y = vec_x / length, vec_y / length

            tang_x, tang_y = -norm_y, norm_x
            search_points = [
                (center_x + (norm_x * adjacent_radius), center_y + (norm_y * adjacent_radius)),
                (center_x - (norm_x * adjacent_radius), center_y - (norm_y * adjacent_radius)),
                (center_x + (tang_x * adjacent_radius), center_y + (tang_y * adjacent_radius)),
                (center_x - (tang_x * adjacent_radius), center_y - (tang_y * adjacent_radius)),
                (center_x, center_y),
            ]

            for candidate_x, candidate_y in search_points:
                resolved_candidate = _resolve_candidate(candidate_x, candidate_y)
                if resolved_candidate is not None:
                    return resolved_candidate

        resolved_raw_snap = _resolve_candidate(raw_x, raw_y)
        if resolved_raw_snap is not None:
            return resolved_raw_snap

        return (fallback_x, fallback_y)

    def _publish_active_slot(
        self,
        options: HeroAIOptionStruct,
        local_x: float,
        local_y: float,
        anchor_x: float,
        anchor_y: float,
        facing: float,
        leader_zplane: int,
        move_threshold: float,
        combat_threshold: float,
        fallback_candidates: list[tuple[float, float]] | None = None,
    ) -> None:
        options.FollowOffset.x = float(local_x)
        options.FollowOffset.y = float(local_y)
        options.FollowMoveThreshold = float(move_threshold)
        options.FollowMoveThresholdCombat = float(combat_threshold)
        rx, ry = self._rotate_local_to_world(local_x, local_y, facing)
        # Snap-or-fallback against navmesh; bails to anchor on elevated terrain.
        pos_x, pos_y = self._validate_followpos(
            float(anchor_x + rx),
            float(anchor_y + ry),
            float(anchor_x),
            float(anchor_y),
            int(leader_zplane),
            fallback_candidates=fallback_candidates,
        )
        options.FollowPos.x = pos_x
        options.FollowPos.y = pos_y
        options.FollowPos.z = float(leader_zplane)
        options.LeaderFollowReady = True

    def refresh_from_ini(self) -> None:
        self._reload_follow_points_from_ini()
        self.ini_reload_timer.Reset()

    def publish(self, force: bool = False) -> None:
        account_email = Player.GetAccountEmail()
        if not account_email:
            return

        all_accounts: AllAccounts = self.shared_memory_manager.GetAllAccounts()
        leader_index = all_accounts.GetSlotByEmail(account_email)
        if leader_index < 0:
            return

        leader_account: AccountStruct = all_accounts.AccountData[leader_index]
        leader_options: HeroAIOptionStruct = all_accounts.HeroAIOptions[leader_index]
        if not leader_account.IsSlotActive or not leader_account.IsAccount:
            return

        if (not Map.IsMapReady()) or Map.IsMapLoading() or (not Map.IsExplorable()):
            self._clear_follow_publish_state(all_accounts, leader_index, invalidate_flags=True)
            return

        if not Party.IsPartyLoaded():
            return
        leader_agent_id = Party.GetPartyLeaderID()
        if not Agent.IsValid(leader_agent_id):
            return
        if Player.GetAgentID() != leader_agent_id:
            return

        points = self._get_follow_points()
        leader_x, leader_y = Player.GetXY()
        leader_zplane = int(Agent.GetZPlane(leader_agent_id))
        leader_facing = Agent.GetRotationAngle(leader_agent_id)

        current_map_signature = (
            int(leader_account.AgentData.Map.MapID),
            int(leader_account.AgentData.Map.Region),
            int(leader_account.AgentData.Map.District),
            int(leader_account.AgentData.Map.Language),
            int(leader_account.AgentPartyData.PartyID),
        )
        if self.state.map_signature != current_map_signature:
            self._handle_map_signature_change(
                all_accounts,
                leader_index,
                current_map_signature,
                leader_x,
                leader_y,
            )

        if self.state.hold_until_leader_moves and self.state.leader_entry_pos is not None:
            entry_x, entry_y = self.state.leader_entry_pos
            if Utils.Distance((leader_x, leader_y), (entry_x, entry_y)) > self.tuning.leader_move_release_distance:
                self.state.hold_until_leader_moves = False

        leader_in_combat = self._is_combat_active_for_mode(all_accounts, leader_index, leader_account)
        if not force:
            if leader_in_combat:
                if not self.combat_publish_timer.IsExpired():
                    return
                self.combat_publish_timer.Reset()
                self.publish_timer.Reset()
            else:
                if not self.publish_timer.IsExpired():
                    return
                self.publish_timer.Reset()
                self.combat_publish_timer.Reset()

        self._update_combat_anchor_facing(leader_in_combat, leader_facing)
        anchor_x, anchor_y, anchor_facing, move_threshold, combat_threshold = self._resolve_anchor(
            leader_options,
            leader_x,
            leader_y,
            leader_facing,
            leader_in_combat,
        )
        party_positions: list[tuple[float, float]] = []
        for index in range(self.shared_memory_manager.max_num_players):
            account = all_accounts.AccountData[index]
            if not (account.IsSlotActive and account.IsAccount) or all_accounts._is_slot_isolated_from_viewer(index, leader_index):
                continue
            if not self._same_party_and_map(leader_account, account):
                continue
            party_positions.append((float(account.AgentData.Pos.x), float(account.AgentData.Pos.y)))

        for index in range(self.shared_memory_manager.max_num_players):
            account: AccountStruct = all_accounts.AccountData[index]
            if not (account.IsSlotActive and account.IsAccount) or all_accounts._is_slot_isolated_from_viewer(index, leader_index):
                continue
            if not self._same_party_and_map(leader_account, account):
                continue

            party_pos = int(account.AgentPartyData.PartyPosition)
            options: HeroAIOptionStruct = all_accounts.HeroAIOptions[index]

            if party_pos <= 0:
                self._apply_idle_slot(options)
                continue

            slot_index = party_pos - 1
            if slot_index < 0 or slot_index >= len(points):
                self._apply_missing_point_slot(options, account, leader_zplane)
                continue

            local_x, local_y = points[slot_index]
            options.FollowOffset.x = float(local_x)
            options.FollowOffset.y = float(local_y)
            options.FollowMoveThreshold = float(self.thresholds.default_follow_threshold)
            options.FollowMoveThresholdCombat = float(self.thresholds.combat_follow_threshold)
            options.LeaderFollowReady = False
            fallback_candidates = [
                pos for pos in party_positions
                if abs(float(pos[0]) - float(account.AgentData.Pos.x)) > self.tuning.nonzero_epsilon
                or abs(float(pos[1]) - float(account.AgentData.Pos.y)) > self.tuning.nonzero_epsilon
            ]

            if self.state.hold_until_leader_moves:
                self._apply_held_slot(options, account, leader_zplane)
                continue

            if bool(options.IsFlagged) and self._is_nonzero_vec2(options.FlagPos):
                self._apply_personal_flag_slot(options, leader_zplane)
                continue

            if leader_in_combat:
                self._publish_active_slot(
                    options,
                    local_x,
                    local_y,
                    anchor_x,
                    anchor_y,
                    anchor_facing,
                    leader_zplane,
                    move_threshold,
                    combat_threshold,
                    fallback_candidates=fallback_candidates,
                )
                continue

            self._publish_active_slot(
                options,
                local_x,
                local_y,
                anchor_x,
                anchor_y,
                anchor_facing,
                leader_zplane,
                move_threshold,
                combat_threshold,
                fallback_candidates=fallback_candidates,
            )
