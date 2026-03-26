import math

from dataclasses import dataclass, field
from typing import Protocol

from Py4GWCoreLib import Agent, Party, Player, Range, ThrottledTimer
from Py4GWCoreLib.IniManager import IniManager
from Py4GWCoreLib.Map import Map
from Py4GWCoreLib.py4gwcorelib_src.Utils import Utils
from Py4GWCoreLib.GlobalCache.shared_memory_src.AccountStruct import AccountStruct
from Py4GWCoreLib.GlobalCache.shared_memory_src.AllAccounts import AllAccounts
from Py4GWCoreLib.GlobalCache.shared_memory_src.HeroAIOptionStruct import HeroAIOptionStruct
from Py4GWCoreLib.native_src.internals.types import Vec2f


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
    publish_interval_ms: int = 250


@dataclass(slots=True)
class FollowThresholdConfig:
    default_follow_threshold: float = field(default_factory=lambda: float(Range.Area.value))
    combat_follow_threshold: float = field(default_factory=lambda: float(Range.Touch.value))
    flagged_follow_threshold: float = 0.0
    disabled_threshold: float = -1.0


@dataclass(slots=True)
class FollowTuningConfig:
    nonzero_epsilon: float = 0.001
    leader_move_release_distance: float = 1.0
    combat_grid_spacing: float = field(default_factory=lambda: float(Range.Touch.value))


@dataclass(slots=True)
class FollowPublisherState:
    formations_ini_key: str = ""
    settings_ini_key: str = ""
    runtime_ini_key: str = ""
    ini_vars_registered: bool = False
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
        self.ini_reload_timer = ThrottledTimer(self.ini.ini_reload_ms)
        self.publish_timer = ThrottledTimer(self.ini.publish_interval_ms)

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

    def _ini_reload_vars(self, key: str) -> None:
        if not key:
            return
        im = IniManager()
        try:
            im.reload(key)
            node = im._get_node(key)
            if node:
                node.vars_loaded = False
            im.load_once(key)
        except Exception:
            pass

    def _ensure_follow_section_var_defs(self, section: str) -> None:
        if not self.state.formations_ini_key or not section:
            return
        im = IniManager()
        sec_tag = section.replace(":", "_")
        im.add_int(self.state.formations_ini_key, f"{sec_tag}_{self.ini.point_count_key}", section, self.ini.point_count_key, 0)
        for index in range(self.ini.max_follow_slots):
            x_key = self.ini.point_x_key_template.format(index=index)
            y_key = self.ini.point_y_key_template.format(index=index)
            im.add_float(self.state.formations_ini_key, f"{sec_tag}_{x_key}", section, x_key, 0.0)
            im.add_float(self.state.formations_ini_key, f"{sec_tag}_{y_key}", section, y_key, 0.0)

    def _reload_thresholds(self, im: IniManager) -> None:
        if not self.state.runtime_ini_key:
            return
        self.thresholds.default_follow_threshold = max(
            0.0,
            float(im.getFloat(self.state.runtime_ini_key, "follow_move_threshold_default", float(Range.Area.value), section=self.ini.runtime_section))
        )
        self.thresholds.combat_follow_threshold = max(
            0.0,
            float(im.getFloat(self.state.runtime_ini_key, "follow_move_threshold_combat", float(Range.Touch.value), section=self.ini.runtime_section))
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
        self._ensure_follow_ini_keys()
        if not self.state.formations_ini_key or not self.state.settings_ini_key:
            return

        im = IniManager()
        self._ini_reload_vars(self.state.settings_ini_key)
        self._ini_reload_vars(self.state.formations_ini_key)
        self._ini_reload_vars(self.state.runtime_ini_key)
        self._reload_thresholds(im)

        selected_id = self._resolve_selected_formation_id(im)
        if not selected_id:
            self.state.selected_id_cache = ""
            self.state.points_cache = []
            return

        section = self._resolve_selected_formation_section(im, selected_id)
        self._ensure_follow_section_var_defs(section)
        self._ini_reload_vars(self.state.formations_ini_key)
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
        self.state.points_cache = points

    def _get_follow_points(self) -> list[tuple[float, float]]:
        if self.ini_reload_timer.IsExpired():
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

    def _clear_follow_publish_state(self, all_accounts: AllAccounts, leader_account: AccountStruct) -> None:
        self.state.map_signature = None
        self.state.hold_until_leader_moves = False
        self.state.leader_entry_pos = None
        self.state.leader_in_combat_last = False
        self.state.combat_anchor_facing = None
        for index in range(self.shared_memory_manager.max_num_players):
            account = all_accounts.AccountData[index]
            if not (account.IsSlotActive and account.IsAccount) or account.IsIsolated:
                continue
            if not self._same_party_and_map(leader_account, account):
                continue
            options = all_accounts.HeroAIOptions[index]
            options.FollowPos.x = 0.0
            options.FollowPos.y = 0.0
            options.FollowPos.z = 0.0
            options.FollowOffset.x = 0.0
            options.FollowOffset.y = 0.0
            options.FollowMoveThreshold = self.thresholds.disabled_threshold
            options.FollowMoveThresholdCombat = self.thresholds.disabled_threshold
            options.LeaderFollowReady = False

    def _apply_idle_slot(self, options: HeroAIOptionStruct) -> None:
        options.FollowOffset.x = 0.0
        options.FollowOffset.y = 0.0
        options.FollowMoveThreshold = self.thresholds.disabled_threshold
        options.FollowMoveThresholdCombat = self.thresholds.disabled_threshold
        options.LeaderFollowReady = (not self.state.hold_until_leader_moves)

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
    ) -> None:
        options.FollowOffset.x = float(local_x)
        options.FollowOffset.y = float(local_y)
        options.FollowMoveThreshold = float(move_threshold)
        options.FollowMoveThresholdCombat = float(combat_threshold)
        rx, ry = self._rotate_local_to_world(local_x, local_y, facing)
        options.FollowPos.x = anchor_x + rx
        options.FollowPos.y = anchor_y + ry
        options.FollowPos.z = float(leader_zplane)
        options.LeaderFollowReady = True

    def _snap_world_coord_to_grid_center(self, value: float) -> float:
        spacing = max(self.tuning.combat_grid_spacing, self.tuning.nonzero_epsilon)
        return round(float(value) / spacing) * spacing

    def _snap_follow_pos_to_combat_grid(self, options: HeroAIOptionStruct) -> None:
        options.FollowPos.x = self._snap_world_coord_to_grid_center(float(options.FollowPos.x))
        options.FollowPos.y = self._snap_world_coord_to_grid_center(float(options.FollowPos.y))

    def publish(self) -> None:
        if not self.publish_timer.IsExpired():
            return
        self.publish_timer.Reset()

        try:
            if not Party.IsPartyLoaded():
                return
            leader_agent_id = Party.GetPartyLeaderID()
            if not Agent.IsValid(leader_agent_id):
                return
            if Player.GetAgentID() != leader_agent_id:
                return
        except Exception:
            return

        account_email = Player.GetAccountEmail()
        if not account_email:
            return

        all_accounts: AllAccounts = self.shared_memory_manager.GetAllAccounts()
        leader_index = all_accounts.GetSlotByEmail(account_email)
        if leader_index < 0:
            return

        leader_account: AccountStruct = all_accounts.AccountData[leader_index]
        leader_options: HeroAIOptionStruct = all_accounts.HeroAIOptions[leader_index]
        if not leader_account.IsSlotActive or not leader_account.IsAccount or leader_account.IsIsolated:
            return

        if (not Map.IsMapReady()) or Map.IsMapLoading() or (not Map.IsExplorable()):
            self._clear_follow_publish_state(all_accounts, leader_account)
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
            self.state.map_signature = current_map_signature
            self.state.hold_until_leader_moves = True
            self.state.leader_entry_pos = (float(leader_x), float(leader_y))

        if self.state.hold_until_leader_moves and self.state.leader_entry_pos is not None:
            entry_x, entry_y = self.state.leader_entry_pos
            if Utils.Distance((leader_x, leader_y), (entry_x, entry_y)) > self.tuning.leader_move_release_distance:
                self.state.hold_until_leader_moves = False

        leader_in_combat = bool(getattr(leader_account, "InAggro", False))
        self._update_combat_anchor_facing(leader_in_combat, leader_facing)
        anchor_x, anchor_y, anchor_facing, move_threshold, combat_threshold = self._resolve_anchor(
            leader_options,
            leader_x,
            leader_y,
            leader_facing,
            leader_in_combat,
        )

        for index in range(self.shared_memory_manager.max_num_players):
            account: AccountStruct = all_accounts.AccountData[index]
            if not (account.IsSlotActive and account.IsAccount) or account.IsIsolated:
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

            if self.state.hold_until_leader_moves:
                self._apply_held_slot(options, account, leader_zplane)
                continue

            if bool(options.IsFlagged) and self._is_nonzero_vec2(options.FlagPos):
                self._apply_personal_flag_slot(options, leader_zplane)
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
            )
            if leader_in_combat:
                self._snap_follow_pos_to_combat_grid(options)
