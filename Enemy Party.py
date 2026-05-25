import builtins
import math
import os
import sys
from dataclasses import dataclass, field

import PyImGui

from Py4GWCoreLib import GLOBAL_CACHE, Map, Py4GW, Range
from Py4GWCoreLib.Agent import Agent
from Py4GWCoreLib.AgentArray import AgentArray
from Py4GWCoreLib.ImGui import ImGui
from Py4GWCoreLib.IniManager import IniManager
from Py4GWCoreLib.Overlay import Overlay
from Py4GWCoreLib.Party import Party
from Py4GWCoreLib.Player import Player
from Py4GWCoreLib.py4gwcorelib_src.Utils import Utils


@dataclass
class EnemyTrackerConfig:
    MODULE_NAME: str = "Enemy Party"
    INI_PATH: str = "Widgets/Automation/Helpers/EnemyTracker"
    MAIN_INI_FILENAME: str = "EnemyTracker.ini"
    FLOATING_INI_FILENAME: str = "EnemyTrackerFloating.ini"

    MAIN_INI_KEY: str = ""
    FLOATING_INI_KEY: str = ""
    INI_INIT: bool = False
    ICON_PATH: str = os.path.join(Py4GW.Console.get_projects_path(), "crossed swords.png")
    DEFAULT_NAME_LANGUAGE: str = "en"


ENEMY_TRACKER_SHARED_VARS_ATTR = "_py4gw_enemy_tracker_shared_vars"
ENEMY_BAR_DEBUG = False
ENEMY_BAR_DEBUG_STARTUP_LOGGED = False


def _enemy_bar_debug(message: str) -> None:
    if not ENEMY_BAR_DEBUG:
        return
    Py4GW.Console.Log(EnemyTrackerConfig.MODULE_NAME, f"[EnemyBarDebug] {message}", Py4GW.Console.MessageType.Warning)


def _call_target(agent_id: int, interact: bool = False) -> bool:
    if agent_id == 0 or not Agent.IsValid(agent_id) or Agent.IsDead(agent_id):
        return False

    _, target_allegiance = Agent.GetAllegiance(agent_id)
    if target_allegiance != "Enemy":
        return False

    Player.ChangeTarget(agent_id)
    Player.CallTarget(agent_id)
    if interact:
        Player.Interact(agent_id, True)
    return True


@dataclass
class EnemyLiveState:
    agent_id: int
    key: str
    name: str
    enc_name: str
    model_id: int
    level: int
    distance: float
    health: float
    max_health: int
    casting_skill_id: int
    statuses: list[str] = field(default_factory=list)
    inferred_primary: str = ""
    inferred_secondary: str = ""


@dataclass
class EnemyPartyUI:
    range_filter: int = 2500
    range_preset_index: int = 0
    sort_index: int = 0
    sort_reverse: bool = False
    profession_filter_index: int = 0
    include_dead: bool = False
    draw_mission_map_range: bool = True
    scan_angle_start: int = -45
    scan_angle_end: int = 45
    scan_offset_forward: int = 0
    scan_offset_right: int = 0
    include_earshot_bubble: bool = True
    called_target_id: int = 0
    hovered_agent_id: int = 0
    draw_hover_row_outline: bool = True
    draw_hover_mission_map: bool = True
    draw_hover_world_circle: bool = True
    draw_called_world_circle: bool = True
    atlas_search: str = ""
    atlas_selected_key: str = ""
    atlas_selected_skill_id: int = 0


@dataclass
class EnemyBarInteraction:
    rect: tuple[float, float, float, float]
    hovered: bool = False
    clicked: bool = False
    double_clicked: bool = False


class EnemyBarWidget:
    def __init__(self, width: float = 280.0, height: float = 18.0) -> None:
        self.width = width
        self.height = height
        self.empty_color = Utils.RGBToColor(70, 70, 70, 230)
        self.text_color = Utils.RGBToColor(245, 245, 245, 255)
        self.text_shadow_color = Utils.RGBToColor(0, 0, 0, 220)
        self.double_click_ms = 350
        self.double_click_max_move = 8.0
        self._last_click_by_id: dict[int, tuple[int, float, float]] = {}
        self._hover_state_by_id: dict[int, bool] = {}

    def _debug_log(self, row_id: int, event: str, **data: object) -> None:
        details = ", ".join(f"{key}={value}" for key, value in data.items())
        message = f"row={row_id} event={event}"
        if details:
            message = f"{message} {details}"
        _enemy_bar_debug(message)

    def draw(self, row_id: int, progress: float, label: str, fill_color: int) -> EnemyBarInteraction:
        progress = max(0.0, min(1.0, float(progress)))

        ImGui.invisible_button(f"##enemy_bar_{row_id}", self.width, self.height)
        hovered = PyImGui.is_item_hovered()
        clicked = PyImGui.is_item_clicked(0)
        io = PyImGui.get_io()
        now = int(Py4GW.Game.get_tick_count64())
        mouse_x = float(getattr(io, "mouse_pos_x", 0.0))
        mouse_y = float(getattr(io, "mouse_pos_y", 0.0))
        double_clicked = False
        was_hovered = bool(self._hover_state_by_id.get(int(row_id), False))
        if hovered != was_hovered:
            self._hover_state_by_id[int(row_id)] = hovered
            self._debug_log(
                row_id,
                "hover_on" if hovered else "hover_off",
                mouse_x=round(mouse_x, 1),
                mouse_y=round(mouse_y, 1),
            )
        if clicked:
            self._debug_log(
                row_id,
                "clicked",
                mouse_x=round(mouse_x, 1),
                mouse_y=round(mouse_y, 1),
                label=label,
            )
            last_click = self._last_click_by_id.get(int(row_id))
            if last_click is not None:
                last_ms, last_x, last_y = last_click
                dx = mouse_x - last_x
                dy = mouse_y - last_y
                moved_too_far = (dx * dx + dy * dy) > (self.double_click_max_move * self.double_click_max_move)
                if (now - last_ms) <= self.double_click_ms and not moved_too_far:
                    double_clicked = True
                    self._last_click_by_id.pop(int(row_id), None)
                    self._debug_log(
                        row_id,
                        "double_clicked",
                        dt_ms=now - last_ms,
                        move_px=round((dx * dx + dy * dy) ** 0.5, 2),
                    )
                else:
                    self._last_click_by_id[int(row_id)] = (now, mouse_x, mouse_y)
                    self._debug_log(
                        row_id,
                        "click_rearmed",
                        dt_ms=now - last_ms,
                        move_px=round((dx * dx + dy * dy) ** 0.5, 2),
                        moved_too_far=moved_too_far,
                    )
            else:
                self._last_click_by_id[int(row_id)] = (now, mouse_x, mouse_y)
                self._debug_log(row_id, "click_armed", at_ms=now)

        item_min, item_max, item_size = ImGui.get_item_rect()
        x1, y1 = item_min
        x2, y2 = item_max

        _enemy_bar_debug(
            f"bar draw row={row_id} hovered={hovered} clicked={clicked} "
            f"double_clicked={double_clicked} rect=({round(x1,1)},{round(y1,1)},{round(x2,1)},{round(y2,1)}) "
            f"mouse=({round(mouse_x,1)},{round(mouse_y,1)})"
        )

        width = x2 - x1
        height = y2 - y1

        fill_x2 = x1 + (width * progress)

        PyImGui.draw_list_add_rect_filled(
            x1, y1,
            x2, y2,
            self.empty_color,
            0.0,
            0
        )

        if progress > 0.0:
            PyImGui.draw_list_add_rect_filled(
                x1, y1,
                fill_x2, y2,
                fill_color,
                0.0,
                0
            )

        if label:
            text = label
            text_size = PyImGui.calc_text_size(text)

            max_text_width = width - 6.0
            if text_size[0] > max_text_width:
                max_chars = max(4, int(len(text) * ((width - 10.0) / max(1.0, text_size[0]))))
                text = text[:max_chars - 3] + "..."
                text_size = PyImGui.calc_text_size(text)

            text_x = x1 + 4.0
            text_y = y1 + ((height - text_size[1]) * 0.5)

            PyImGui.draw_list_add_text(text_x + 1.0, text_y + 1.0, self.text_shadow_color, text)
            PyImGui.draw_list_add_text(text_x, text_y, self.text_color, text)

        return EnemyBarInteraction(
            rect=(x1, y1, x2, y2),
            hovered=hovered,
            clicked=clicked,
            double_clicked=double_clicked,
        )


PROFESSION_ABBREVIATIONS = {
    "Warrior": "W",
    "Ranger": "R",
    "Monk": "Mo",
    "Necromancer": "N",
    "Mesmer": "Me",
    "Elementalist": "E",
    "Assassin": "A",
    "Ritualist": "Rt",
    "Paragon": "P",
    "Dervish": "D",
}


@dataclass
class _FallbackData:
    records: dict = field(default_factory=dict)
    name_records: dict = field(default_factory=dict)
    live_rows: list = field(default_factory=list)
    enemy_array: list = field(default_factory=list)


class EnemyTracker:
    SORT_OPTIONS = ["Agent ID", "Distance", "Name", "Health", "Level", "Profession"]
    SORT_LABELS = {
        "Agent ID": "ID",
        "Distance": "Dist",
        "Name": "Name",
        "Health": "HP",
        "Level": "Lvl",
        "Profession": "Prof",
    }
    RANGE_PRESETS = [("Manual", None)] + [
        (range_value.name, int(range_value.value))
        for range_value in sorted(Range, key=lambda value: float(value.value))
    ]
    RANGE_BUTTONS = [("All", 0)] + [
        (range_value.name, int(range_value.value))
        for range_value in sorted(Range, key=lambda value: float(value.value))
    ]
    SCANNER_RADIUS = float(Range.SafeCompass.value)

    def __init__(self) -> None:
        self.floating_button = ImGui.FloatingIcon(
            icon_path=EnemyTrackerConfig.ICON_PATH,
            window_id="##floating_icon_enemy_tracker_button",
            window_name="Enemy Tracker Toggle",
            tooltip_visible="Hide window",
            tooltip_hidden="Show window",
            toggle_ini_key=EnemyTrackerConfig.FLOATING_INI_KEY,
            toggle_var_name="show_main_window",
            toggle_default=True,
            draw_callback=self.draw_window,
        )
        self.ui = EnemyPartyUI()
        self._sync_range_preset_from_filter()
        self.enemy_bar = EnemyBarWidget(width=220.0, height=18.0)
        self._fallback = _FallbackData()
        self._called_target_id = 0

    def _shared(self):
        shared = _get_shared_vars()
        if shared is not None:
            return shared
        return self._fallback

    def _sync_range_preset_from_filter(self) -> None:
        self.ui.range_preset_index = 0
        for index, (_, preset_value) in enumerate(self.RANGE_PRESETS):
            if preset_value is not None and int(preset_value) == int(self.ui.range_filter):
                self.ui.range_preset_index = index
                return

    def _enemy_key(self, agent_id: int, name: str, enc_name: str, model_id: int) -> str:
        if enc_name:
            return f"enc:{enc_name}"
        if model_id:
            return f"model:{model_id}"
        return f"name:{name}"

    def _clean_name_values(self, names: object) -> list[str]:
        if isinstance(names, str):
            values = [names]
        elif isinstance(names, list):
            values = names
        else:
            return []

        clean_names: list[str] = []
        for value in values:
            name = str(value or "").strip()
            if name and name not in clean_names:
                clean_names.append(name)
        return clean_names

    def _record_names(self, key: str, language: str = EnemyTrackerConfig.DEFAULT_NAME_LANGUAGE) -> list[str]:
        shared = self._shared()
        language_key = str(language or EnemyTrackerConfig.DEFAULT_NAME_LANGUAGE).strip().lower()
        if language_key in shared.name_records and key in shared.name_records[language_key]:
            return shared.name_records[language_key][key]
        if EnemyTrackerConfig.DEFAULT_NAME_LANGUAGE in shared.name_records and key in shared.name_records[EnemyTrackerConfig.DEFAULT_NAME_LANGUAGE]:
            return shared.name_records[EnemyTrackerConfig.DEFAULT_NAME_LANGUAGE][key]
        for names_by_key in shared.name_records.values():
            names = names_by_key.get(key, [])
            if names:
                return names
        return []

    def _skill_info(self, skill_id: int) -> tuple[str, int, str]:
        if skill_id <= 0:
            return "", 0, ""
        try:
            skill_name = GLOBAL_CACHE.Skill.GetNameFromWiki(skill_id) or GLOBAL_CACHE.Skill.GetName(skill_id)
        except Exception:
            skill_name = f"Skill {skill_id}"
        try:
            prof_id, prof_name = GLOBAL_CACHE.Skill.GetProfession(skill_id)
        except Exception:
            prof_id, prof_name = 0, ""
        return skill_name or f"Skill {skill_id}", int(prof_id or 0), str(prof_name or "")

    def _skill_detail_lines(self, skill_id: int, compact: bool = False) -> list[str]:
        if skill_id <= 0:
            return ["Skill: Unknown"]

        skill_name, _prof_id, prof_name = self._skill_info(skill_id)
        try:
            _skill_type_id, skill_type_name = GLOBAL_CACHE.Skill.GetType(skill_id)
        except Exception:
            skill_type_name = ""

        lines = [
            skill_name,
            f"ID: {int(skill_id)}",
        ]

        if prof_name or skill_type_name:
            descriptor_parts = [part for part in (prof_name, skill_type_name) if part]
            lines.append(" | ".join(descriptor_parts))

        meta_parts: list[str] = []
        try:
            energy_cost = int(GLOBAL_CACHE.Skill.Data.GetEnergyCost(skill_id) or 0)
            if energy_cost > 0:
                meta_parts.append(f"E {energy_cost}")
        except Exception:
            pass
        try:
            adrenaline_cost = int(GLOBAL_CACHE.Skill.Data.GetAdrenaline(skill_id) or 0)
            if adrenaline_cost > 0:
                meta_parts.append(f"A {adrenaline_cost}")
        except Exception:
            pass
        try:
            health_cost = int(GLOBAL_CACHE.Skill.Data.GetHealthCost(skill_id) or 0)
            if health_cost > 0:
                meta_parts.append(f"HP {health_cost}%")
        except Exception:
            pass
        try:
            activation_time = float(GLOBAL_CACHE.Skill.Data.GetActivation(skill_id) or 0.0)
            if activation_time > 0:
                meta_parts.append(f"Cast {activation_time:.2f}s")
        except Exception:
            pass
        try:
            recharge_time = int(GLOBAL_CACHE.Skill.Data.GetRecharge(skill_id) or 0)
            if recharge_time > 0:
                meta_parts.append(f"Recharge {recharge_time}s")
        except Exception:
            pass
        if meta_parts:
            lines.append(" | ".join(meta_parts))

        try:
            description = GLOBAL_CACHE.Skill.GetConciseDescription(skill_id) or GLOBAL_CACHE.Skill.GetDescription(skill_id) or ""
        except Exception:
            description = ""
        description = str(description).strip()
        if description:
            if compact and len(description) > 180:
                description = f"{description[:177]}..."
            lines.append(description)

        return lines

    def _draw_skill_info_default(self, skill_id: int, compact: bool = False) -> None:
        for line in self._skill_detail_lines(skill_id, compact=compact):
            PyImGui.text_wrapped(line)

    def _draw_skill_tooltip(self, skill_id: int, skill: dict | None = None) -> None:
        if skill_id <= 0 or not PyImGui.begin_tooltip():
            return
        try:
            self._draw_skill_info_default(skill_id, compact=True)
            if skill is not None:
                self._draw_skill_observation_meta(skill)
        finally:
            PyImGui.end_tooltip()

    def _infer_professions(self, record: dict) -> tuple[str, str]:
        counts: dict[str, int] = {}
        for skill in record.get("observed_skills", {}).values():
            prof_name = str(skill.get("profession", "") or "")
            if prof_name:
                counts[prof_name] = counts.get(prof_name, 0) + 1
        ranked = sorted(
            ((name, int(count)) for name, count in counts.items() if name),
            key=lambda item: (-item[1], item[0]),
        )
        primary = ranked[0][0] if len(ranked) >= 1 else ""
        secondary = ranked[1][0] if len(ranked) >= 2 else ""
        return primary, secondary

    def _statuses(self, agent_id: int) -> list[str]:
        statuses: list[str] = []
        if Agent.IsDead(agent_id):
            statuses.append("Dead")
        if Agent.IsDegenHexed(agent_id):
            statuses.append("DegenHex")
        if Agent.IsHexed(agent_id):
            statuses.append("Hex")
        if Agent.IsConditioned(agent_id):
            statuses.append("Cond")
        if Agent.IsEnchanted(agent_id):
            statuses.append("Ench")
        if Agent.IsWeaponSpelled(agent_id):
            statuses.append("Wpn")
        if Agent.IsBleeding(agent_id):
            statuses.append("Bleed")
        if Agent.IsPoisoned(agent_id):
            statuses.append("Pois")
        if Agent.IsCrippled(agent_id):
            statuses.append("Crip")
        if Agent.IsDeepWounded(agent_id):
            statuses.append("Deep")
        return statuses

    def _normalize_degrees(self, angle: float) -> float:
        return (float(angle) + 180.0) % 360.0 - 180.0

    def _player_facing_degrees(self) -> float:
        player_id = Player.GetAgentID()
        try:
            facing_x = float(Agent.GetRotationCos(player_id) or 0.0)
            facing_y = float(Agent.GetRotationSin(player_id) or 0.0)
            if abs(facing_x) > 0.0001 or abs(facing_y) > 0.0001:
                return math.degrees(math.atan2(facing_y, facing_x))
        except Exception:
            pass
        try:
            return math.degrees(float(Agent.GetRotationAngle(player_id) or 0.0))
        except Exception:
            return 0.0

    def _scan_origin_xy(self, player_xy: tuple[float, float]) -> tuple[float, float]:
        facing_radians = math.radians(self._player_facing_degrees())
        forward_x = math.cos(facing_radians)
        forward_y = math.sin(facing_radians)
        right_x = math.cos(facing_radians + (math.pi * 0.5))
        right_y = math.sin(facing_radians + (math.pi * 0.5))
        player_x, player_y = player_xy
        return (
            player_x + (forward_x * float(self.ui.scan_offset_forward)) + (right_x * float(self.ui.scan_offset_right)),
            player_y + (forward_y * float(self.ui.scan_offset_forward)) + (right_y * float(self.ui.scan_offset_right)),
        )

    def _relative_angle_to_point(self, origin_xy: tuple[float, float], target_xy: tuple[float, float]) -> float:
        origin_x, origin_y = origin_xy
        target_x, target_y = target_xy
        point_angle = math.degrees(math.atan2(target_y - origin_y, target_x - origin_x))
        return self._normalize_degrees(point_angle - self._player_facing_degrees())

    def _is_angle_in_scan(self, relative_angle: float) -> bool:
        start = self._normalize_degrees(self.ui.scan_angle_start)
        end = self._normalize_degrees(self.ui.scan_angle_end)
        angle = self._normalize_degrees(relative_angle)
        if start <= end:
            return start <= angle <= end
        return angle >= start or angle <= end

    def _is_inside_scan_frustum(
        self,
        player_xy: tuple[float, float],
        target_xy: tuple[float, float],
        distance: float,
    ) -> bool:
        if self.ui.include_earshot_bubble and distance <= float(Range.Earshot.value):
            return True
        scan_origin = self._scan_origin_xy(player_xy)
        scan_distance = Utils.Distance(scan_origin, target_xy)
        if self.ui.range_filter > 0 and scan_distance > self.ui.range_filter:
            return False
        return self._is_angle_in_scan(self._relative_angle_to_point(scan_origin, target_xy))

    def _sort_rows(self, rows: list[EnemyLiveState]) -> list[EnemyLiveState]:
        mode = self.SORT_OPTIONS[max(0, min(self.ui.sort_index, len(self.SORT_OPTIONS) - 1))]
        if mode == "Agent ID":
            return sorted(rows, key=lambda row: row.agent_id, reverse=self.ui.sort_reverse)
        if mode == "Health":
            return sorted(rows, key=lambda row: row.health, reverse=self.ui.sort_reverse)
        if mode == "Profession":
            return sorted(rows, key=lambda row: row.inferred_primary, reverse=self.ui.sort_reverse)
        if mode == "Name":
            return sorted(rows, key=lambda row: row.name, reverse=self.ui.sort_reverse)
        if mode == "Level":
            return sorted(rows, key=lambda row: row.level, reverse=not self.ui.sort_reverse)
        return sorted(rows, key=lambda row: row.distance, reverse=self.ui.sort_reverse)

    def _set_sort(self, mode: str) -> None:
        if mode not in self.SORT_OPTIONS:
            return
        index = self.SORT_OPTIONS.index(mode)
        if self.ui.sort_index == index:
            self.ui.sort_reverse = not self.ui.sort_reverse
        else:
            self.ui.sort_index = index
            self.ui.sort_reverse = mode == "Level"

    def _sort_button(self, mode: str, label: str | None = None) -> None:
        active = self.SORT_OPTIONS[max(0, min(self.ui.sort_index, len(self.SORT_OPTIONS) - 1))] == mode
        suffix = " v" if self.ui.sort_reverse else " ^"
        button_label = f"{label or self.SORT_LABELS.get(mode, mode)}{suffix if active else ''}##sort_{mode}_{label or 'button'}"
        if PyImGui.button(button_label):
            self._set_sort(mode)

    def _current_range_label(self) -> str:
        for label, value in self.RANGE_BUTTONS:
            if int(value) == int(self.ui.range_filter):
                return label
        return str(int(self.ui.range_filter))

    def _range_combo_index(self) -> int:
        for index, (_, value) in enumerate(self.RANGE_BUTTONS, start=1):
            if int(value) == int(self.ui.range_filter):
                return index
        return 0

    def _clamp_int(self, value: int, value_min: int, value_max: int) -> int:
        return max(value_min, min(value_max, int(value)))

    def _slider_with_input_int(self, label: str, value: int, value_min: int, value_max: int) -> int:
        new_value = int(ImGui.slider_int(label, int(value), value_min, value_max))
        PyImGui.same_line(0, 6)
        edited_value = PyImGui.input_int(f"##{label}_input", new_value)
        return self._clamp_int(edited_value, value_min, value_max)

    def _profession_filters(self) -> list[str]:
        names = {"All"}
        for record in self._shared().records.values():
            if record.get("inferred_primary"):
                names.add(record["inferred_primary"])
            if record.get("inferred_secondary"):
                names.add(record["inferred_secondary"])
        return ["All"] + sorted(name for name in names if name != "All")

    def _filtered_rows(self) -> list[EnemyLiveState]:
        return self._refresh_rows()

    def _refresh_rows(self) -> list[EnemyLiveState]:
        if not Map.IsMapReady() or not Player.IsPlayerLoaded() or not Map.IsExplorable():
            return []

        shared = self._shared()
        player_xy = Player.GetXY()

        filters = self._profession_filters()
        self.ui.profession_filter_index = max(0, min(self.ui.profession_filter_index, len(filters) - 1))
        prof_filter = filters[self.ui.profession_filter_index]

        rows: list[EnemyLiveState] = []
        for row in shared.live_rows:
            if not Agent.IsValid(row.agent_id):
                continue
            if not self._is_inside_scan_frustum(player_xy, Agent.GetXY(row.agent_id), row.distance):
                continue
            if prof_filter != "All" and row.inferred_primary != prof_filter and row.inferred_secondary != prof_filter:
                continue
            rows.append(row)

        return self._sort_rows(rows)

    def _profession_abbrev(self, profession: str) -> str:
        return PROFESSION_ABBREVIATIONS.get(profession, profession[:2] if profession else "?")

    def _profession_prefix(self, row: EnemyLiveState) -> str:
        primary = self._profession_abbrev(row.inferred_primary)
        secondary = self._profession_abbrev(row.inferred_secondary)
        return f"{primary}/{secondary}" if row.inferred_secondary else primary

    def _health_label(self, row: EnemyLiveState) -> str:
        return f"{self._profession_prefix(row)} [{row.level}] {row.name}  {int(row.health * 100)}%"

    def _health_color(self, row: EnemyLiveState) -> int:
        if "Dead" in row.statuses:
            return Utils.RGBToColor(54, 54, 54, 255)
        if "Pois" in row.statuses:
            return Utils.RGBToColor(72, 150, 72, 255)
        if "Bleed" in row.statuses:
            return Utils.RGBToColor(224, 119, 119, 255)
        if "DegenHex" in row.statuses:
            return Utils.RGBToColor(196, 56, 150, 255)
        return Utils.RGBToColor(204, 0, 0, 255)

    def _magenta_color(self, alpha: int = 255) -> int:
        return Utils.RGBToColor(255, 0, 255, alpha)

    def _yellow_color(self, alpha: int = 255) -> int:
        return Utils.RGBToColor(255, 220, 40, alpha)

    def _resolve_called_target_id(self) -> int:
        try:
            called_target_id = int(Party.GetPartyTarget() or 0)
        except Exception:
            called_target_id = 0

        if called_target_id > 0 and Agent.IsValid(called_target_id):
            self._called_target_id = called_target_id
        else:
            self._called_target_id = 0
        return self._called_target_id

    def _draw_target_outline(
        self,
        x1: float,
        y1: float,
        x2: float,
        y2: float,
        color: int,
    ) -> None:
        PyImGui.draw_list_add_rect(x1 - 2.0, y1 - 2.0, x2 + 2.0, y2 + 2.0, color, 0.0, 0, 2.0)

    def _draw_row(self, row: EnemyLiveState) -> None:
        skill_text = ""
        if row.casting_skill_id:
            skill_name, _, _ = self._skill_info(row.casting_skill_id)
            skill_text = skill_name
        called_target_id = self._called_target_id
        is_called_target = row.agent_id == called_target_id

        _enemy_bar_debug(f"draw_row start agent_id={row.agent_id} name={row.name} distance={int(row.distance)}")

        PyImGui.table_next_row()
        PyImGui.table_next_column()
        if PyImGui.button(f"Call##call_{row.agent_id}"):
            _enemy_bar_debug(f"call button clicked agent_id={row.agent_id} name={row.name}")
            _call_target(row.agent_id, interact=False)
        call_hovered = PyImGui.is_item_hovered()
        call_item_min, call_item_max, _ = ImGui.get_item_rect()
        call_x1, call_y1 = call_item_min
        call_x2, call_y2 = call_item_max
        if call_hovered:
            self.ui.hovered_agent_id = row.agent_id
            _enemy_bar_debug(f"call button hovered agent_id={row.agent_id} name={row.name}")
        PyImGui.table_next_column()
        bar_state = self.enemy_bar.draw(
            row.agent_id,
            row.health,
            self._health_label(row),
            self._health_color(row),
        )
        x1, y1, x2, y2 = bar_state.rect
        row_x1 = min(call_x1, x1)
        row_y1 = min(call_y1, y1)
        row_x2 = max(call_x2, x2)
        row_y2 = max(call_y2, y2)
        row_hovered = ImGui.is_mouse_in_rect((row_x1, row_y1, row_x2 - row_x1, row_y2 - row_y1))
        _enemy_bar_debug(
            f"row geometry agent_id={row.agent_id} "
            f"call_rect=({round(call_x1,1)},{round(call_y1,1)},{round(call_x2,1)},{round(call_y2,1)}) "
            f"bar_rect=({round(x1,1)},{round(y1,1)},{round(x2,1)},{round(y2,1)}) "
            f"row_rect=({round(row_x1,1)},{round(row_y1,1)},{round(row_x2,1)},{round(row_y2,1)}) "
            f"row_hovered={row_hovered}"
        )
        if bar_state.double_clicked:
            _enemy_bar_debug(f"row handler double click agent_id={row.agent_id} name={row.name}")
            _call_target(row.agent_id, interact=False)
        hovered = call_hovered or bar_state.hovered or row_hovered
        if hovered:
            self.ui.hovered_agent_id = row.agent_id
            _enemy_bar_debug(
                f"row hovered agent_id={row.agent_id} name={row.name} "
                f"call_hovered={call_hovered} bar_hovered={bar_state.hovered} row_hovered={row_hovered}"
            )
        if hovered and self.ui.draw_hover_row_outline and not is_called_target:
            self._draw_target_outline(row_x1, row_y1, row_x2, row_y2, self._magenta_color())
        if is_called_target:
            self._draw_target_outline(row_x1, row_y1, row_x2, row_y2, self._yellow_color())
        if hovered:
            PyImGui.begin_tooltip()
            self._draw_enemy_hover_card(row)
            if is_called_target:
                PyImGui.separator()
                PyImGui.text("Called target")
            PyImGui.end_tooltip()

    def _draw_controls(self) -> None:
        PyImGui.text("Range:")
        PyImGui.same_line(0, -1)

        range_names = ["Custom"] + [label for label, _ in self.RANGE_BUTTONS]
        selected_range = PyImGui.combo("##enemy_tracker_range_combo", self._range_combo_index(), range_names)
        if 1 <= selected_range <= len(self.RANGE_BUTTONS):
            self.ui.range_filter = int(self.RANGE_BUTTONS[selected_range - 1][1])
            self._sync_range_preset_from_filter()

        max_offset = int(max(float(range_value.value) for range_value in Range))
        self.ui.range_filter = self._slider_with_input_int("Range", int(self.ui.range_filter), 0, max_offset)
        self._sync_range_preset_from_filter()
        self.ui.scan_angle_start = self._slider_with_input_int("Angle start", int(self.ui.scan_angle_start), -180, 180)
        self.ui.scan_angle_end = self._slider_with_input_int("Angle end", int(self.ui.scan_angle_end), -180, 180)
        self.ui.scan_offset_forward = self._slider_with_input_int("Offset forward", int(self.ui.scan_offset_forward), -max_offset, max_offset)
        self.ui.scan_offset_right = self._slider_with_input_int("Offset right", int(self.ui.scan_offset_right), -max_offset, max_offset)

        self.ui.include_earshot_bubble = PyImGui.checkbox("Include Earshot bubble", self.ui.include_earshot_bubble)
        self.ui.draw_mission_map_range = PyImGui.checkbox("Draw in Mission map+", self.ui.draw_mission_map_range)
        self.ui.draw_hover_row_outline = PyImGui.checkbox("Hover row outline", self.ui.draw_hover_row_outline)
        self.ui.draw_hover_mission_map = PyImGui.checkbox("Hover mission map marker", self.ui.draw_hover_mission_map)
        self.ui.draw_hover_world_circle = PyImGui.checkbox("Hover 3D touch circle", self.ui.draw_hover_world_circle)
        self.ui.draw_called_world_circle = PyImGui.checkbox("Called 3D touch circle", self.ui.draw_called_world_circle)

    def _draw_sort_controls(self) -> None:
        self._sort_button("Agent ID")
        PyImGui.same_line(0, 4)
        self._sort_button("Distance")
        PyImGui.same_line(0, 4)
        self._sort_button("Name")
        PyImGui.same_line(0, 4)
        self._sort_button("Health")
        PyImGui.same_line(0, 4)
        self._sort_button("Level")
        PyImGui.same_line(0, 4)
        self._sort_button("Profession")

    def _draw_tracker_tab(self, rows: list[EnemyLiveState]) -> None:
        self._draw_sort_controls()
        if len(rows) == 0:
            PyImGui.text("No enemies found.")
        else:
            if PyImGui.begin_table(
                "EnemyTrackerRows",
                2,
                PyImGui.TableFlags.RowBg | PyImGui.TableFlags.BordersInnerV
            ):
                PyImGui.table_setup_column(
                    "Call",
                    PyImGui.TableColumnFlags.WidthFixed,
                    45
                )
                PyImGui.table_setup_column(
                    "Enemy / HP",
                    PyImGui.TableColumnFlags.WidthFixed,
                    220
                )

                for row in rows:
                    self._draw_row(row)

                PyImGui.end_table()

        PyImGui.separator()
        shared_live = self._shared().live_rows
        PyImGui.text(f"Visible: {len(rows)} / Polled: {len(shared_live)}")

    def _draw_config_tab(self) -> None:
        self._draw_controls()

    def _record_label(self, key: str, record: dict) -> str:
        names = self._record_names(key)
        name = names[0] if names else key
        primary = record.get("inferred_primary") or "?"
        secondary = record.get("inferred_secondary") or ""
        profession = f"{primary}/{secondary}" if secondary else primary
        return f"{name} [{profession}]"

    def _record_search_text(self, key: str, record: dict) -> str:
        shared = self._shared()
        parts = [key]
        for language, names_by_key in shared.name_records.items():
            names = names_by_key.get(key, [])
            if not names:
                continue
            parts.append(str(language))
            parts.extend(str(name) for name in names)
        for field_name in ("encoded_names", "model_ids"):
            parts.extend(str(value) for value in record.get(field_name, []))
        parts.append(str(record.get("inferred_primary", "")))
        parts.append(str(record.get("inferred_secondary", "")))
        for map_entry in record.get("observed_maps", {}).values():
            parts.append(str(map_entry.get("id", "")))
            parts.append(str(map_entry.get("name", "")))
            parts.append(str(map_entry.get("base_id", "")))
            parts.append(str(map_entry.get("instance_type", "")))
        for skill in record.get("observed_skills", {}).values():
            parts.append(str(skill.get("id", "")))
            parts.append(str(skill.get("name", "")))
            parts.append(str(skill.get("profession", "")))
        return " ".join(parts).lower()

    def _atlas_matches(self) -> list[tuple[str, dict]]:
        query = str(self.ui.atlas_search or "").strip().lower()
        matches = []
        for key, record in self._shared().records.items():
            if not query or query in self._record_search_text(key, record):
                matches.append((key, record))
        return sorted(matches, key=lambda item: self._record_label(item[0], item[1]).lower())

    def _observed_skills_for_record(self, record: dict) -> list[dict]:
        skills = list(record.get("observed_skills", {}).values())
        skills.sort(key=lambda skill: str(skill.get("name", "")))
        return skills

    def _observed_maps_for_record(self, record: dict) -> list[dict]:
        maps = list(record.get("observed_maps", {}).values())
        maps.sort(key=lambda map_entry: (str(map_entry.get("name", "")), int(map_entry.get("id", 0))))
        return maps

    def _draw_enemy_card(self, key: str, record: dict) -> None:
        shared = self._shared()
        PyImGui.begin_group()
        PyImGui.text(self._record_label(key, record))
        PyImGui.text(f"Key: {key}")
        english_names = ", ".join(str(name) for name in shared.name_records.get(EnemyTrackerConfig.DEFAULT_NAME_LANGUAGE, {}).get(key, [])) or "?"
        encoded_names = ", ".join(str(name) for name in record.get("encoded_names", [])) or "?"
        model_ids = ", ".join(str(model_id) for model_id in record.get("model_ids", [])) or "?"
        PyImGui.text(f"English names: {english_names}")
        other_languages = sorted(
            language for language, names_by_key in shared.name_records.items()
            if language != EnemyTrackerConfig.DEFAULT_NAME_LANGUAGE and key in names_by_key
        )
        for language in other_languages:
            localized_names = ", ".join(str(name) for name in shared.name_records.get(language, {}).get(key, [])) or "?"
            PyImGui.text(f"{language} names: {localized_names}")
        PyImGui.text(f"Encoded: {encoded_names}")
        PyImGui.text(f"Models: {model_ids}")
        PyImGui.text(f"Primary: {record.get('inferred_primary', '') or '?'}")
        PyImGui.text(f"Secondary: {record.get('inferred_secondary', '') or '?'}")
        observed_maps = self._observed_maps_for_record(record)
        PyImGui.text(f"Maps observed: {len(observed_maps)}")
        for map_entry in observed_maps[:8]:
            map_name = str(map_entry.get("name", "") or "Unknown Map")
            map_id = int(map_entry.get("id", 0) or 0)
            PyImGui.bullet_text(f"{map_name} ({map_id})")
        if len(observed_maps) > 8:
            PyImGui.bullet_text(f"... {len(observed_maps) - 8} more")

        profession_names = sorted({
            str(skill.get("profession", "") or "")
            for skill in record.get("observed_skills", {}).values()
            if str(skill.get("profession", "") or "")
        })
        if profession_names:
            PyImGui.text("Profession evidence:")
            for name in profession_names[:6]:
                PyImGui.bullet_text(name)
        PyImGui.end_group()

    def _draw_skill_observation_meta(self, skill: dict) -> None:
        skill_id = int(skill.get("id", 0))
        PyImGui.text(f"ID: {skill_id}")

    def _draw_observed_skill_icon_grid(self, skills: list[dict]) -> None:
        cards_per_row = 8
        for index, skill in enumerate(skills):
            skill_id = int(skill.get("id", 0))
            selected = self.ui.atlas_selected_skill_id == skill_id
            texture_path = GLOBAL_CACHE.Skill.ExtraData.GetTexturePath(skill_id)
            if ImGui.image_toggle_button(f"enemy_atlas_skill_{skill_id}_{index}", texture_path, selected, 42, 42):
                self.ui.atlas_selected_skill_id = skill_id

            if PyImGui.is_item_hovered():
                self._draw_skill_tooltip(skill_id, skill)

            if (index + 1) % cards_per_row != 0 and index + 1 < len(skills):
                PyImGui.same_line(0, 8)

    def _draw_observed_skillbar_mini(self, skills: list[dict], icon_size: float = 28.0) -> None:
        shown_skills = skills[:8]
        if not shown_skills:
            PyImGui.text("No observed skills yet.")
            return

        for index, skill in enumerate(shown_skills):
            skill_id = int(skill.get("id", 0) or 0)
            texture_path = GLOBAL_CACHE.Skill.ExtraData.GetTexturePath(skill_id) if skill_id > 0 else ""
            if texture_path:
                ImGui.DrawTexture(texture_path, icon_size, icon_size)
            else:
                ImGui.dummy(icon_size, icon_size)

            if PyImGui.is_item_hovered():
                self._draw_skill_tooltip(skill_id, skill)

            if index + 1 < len(shown_skills):
                PyImGui.same_line(0, 4)

        if len(skills) > len(shown_skills):
            PyImGui.same_line(0, 8)
            PyImGui.text(f"+{len(skills) - len(shown_skills)}")

    def _draw_enemy_hover_card(self, row: EnemyLiveState) -> None:
        record = self._shared().records.get(row.key)
        if not record:
            PyImGui.text(row.name)
            PyImGui.text(f"Profession: {self._profession_prefix(row)}")
            return

        names = self._record_names(row.key)
        primary = str(record.get("inferred_primary", "") or row.inferred_primary or "?")
        secondary = str(record.get("inferred_secondary", "") or row.inferred_secondary or "")
        profession_text = f"{primary}/{secondary}" if secondary else primary
        observed_maps = self._observed_maps_for_record(record)
        observed_skills = self._observed_skills_for_record(record)

        PyImGui.text(names[0] if names else row.name)
        PyImGui.text(f"Profession: {profession_text}")
        PyImGui.separator()
        PyImGui.text("Skillbar")
        self._draw_observed_skillbar_mini(observed_skills)
        PyImGui.separator()
        PyImGui.text(f"Maps Observed: {len(observed_maps)}")
        for map_entry in observed_maps[:6]:
            map_name = str(map_entry.get("name", "") or "Unknown Map")
            map_id = int(map_entry.get("id", 0) or 0)
            PyImGui.bullet_text(f"{map_name} id:({map_id})")
        if len(observed_maps) > 6:
            PyImGui.bullet_text(f"... {len(observed_maps) - len(observed_maps[:6])} more")

    def _draw_atlas_skills(self, record: dict) -> None:
        skills = self._observed_skills_for_record(record)
        PyImGui.text(f"Observed skills: {len(skills)}")
        if not skills:
            PyImGui.text("No observed skills yet.")
            return

        valid_ids = [int(skill.get("id", 0)) for skill in skills if int(skill.get("id", 0)) > 0]
        if self.ui.atlas_selected_skill_id not in valid_ids:
            self.ui.atlas_selected_skill_id = valid_ids[0] if valid_ids else 0

        self._draw_observed_skill_icon_grid(skills)
        selected_skill = next((skill for skill in skills if int(skill.get("id", 0)) == self.ui.atlas_selected_skill_id), None)
        if selected_skill:
            PyImGui.separator()
            self._draw_skill_observation_meta(selected_skill)
            self._draw_skill_info_default(int(selected_skill.get("id", 0)), compact=False)

    def _draw_enemy_atlas(self) -> None:
        shared = self._shared()
        self.ui.atlas_search = PyImGui.input_text("Search##enemy_atlas_search", self.ui.atlas_search, 128)
        matches = self._atlas_matches()
        PyImGui.text(f"Matches: {len(matches)} / Known: {len(shared.records)}")
        if matches and self.ui.atlas_selected_key not in shared.records:
            self.ui.atlas_selected_key = matches[0][0]

        if PyImGui.begin_table("EnemyAtlasLayout", 2, PyImGui.TableFlags.BordersInnerV):
            PyImGui.table_setup_column("Enemies", PyImGui.TableColumnFlags.WidthFixed, 230)
            PyImGui.table_setup_column("Data", PyImGui.TableColumnFlags.WidthFixed, 390)
            PyImGui.table_next_row()
            PyImGui.table_next_column()
            for key, record in matches[:200]:
                selected = key == self.ui.atlas_selected_key
                if PyImGui.selectable(f"{self._record_label(key, record)}##atlas_{key}", selected, PyImGui.SelectableFlags.NoFlag, (0.0, 0.0)):
                    self.ui.atlas_selected_key = key

            PyImGui.table_next_column()
            record = shared.records.get(self.ui.atlas_selected_key)
            if not record:
                PyImGui.text("Select an enemy.")
            else:
                self._draw_enemy_card(self.ui.atlas_selected_key, record)
                PyImGui.separator()
                self._draw_atlas_skills(record)
            PyImGui.end_table()

    def draw_scanner_config(self) -> None:
        return

    def draw_window(self) -> None:
        expanded, open_ = ImGui.BeginWithClose(
            ini_key=EnemyTrackerConfig.MAIN_INI_KEY,
            name=EnemyTrackerConfig.MODULE_NAME,
            p_open=self.floating_button.visible,
            flags=PyImGui.WindowFlags.AlwaysAutoResize,
        )
        self.floating_button.sync_begin_with_close(open_)

        if expanded:
            self._resolve_called_target_id()
            rows = self._filtered_rows()
            self.ui.hovered_agent_id = 0

            if PyImGui.begin_tab_bar("EnemyTrackerTabs"):
                if PyImGui.begin_tab_item("Tracker"):
                    self._draw_tracker_tab(rows)
                    PyImGui.end_tab_item()
                if PyImGui.begin_tab_item("Config"):
                    self._draw_config_tab()
                    PyImGui.end_tab_item()
                if PyImGui.begin_tab_item("Enemy Atlas"):
                    self._draw_enemy_atlas()
                    PyImGui.end_tab_item()
                PyImGui.end_tab_bar()

        ImGui.End(EnemyTrackerConfig.MAIN_INI_KEY)

    def _draw_agent_mission_map_marker(self, agent_id: int, color: int) -> None:
        if agent_id <= 0 or not Agent.IsValid(agent_id):
            return
        agent_x, agent_y = Agent.GetXY(agent_id)
        screen_x, screen_y = Map.MissionMap.MapProjection.GameMapToScreen(agent_x, agent_y, self._mission_map_mega_zoom())
        PyImGui.draw_list_add_circle(screen_x, screen_y, 7.0, Utils.RGBToColor(0, 0, 0, 230), 24, 4.0)
        PyImGui.draw_list_add_circle(screen_x, screen_y, 7.0, color, 24, 2.5)

    def draw_world_agent_markers(self) -> None:
        if not Player.IsPlayerLoaded():
            return

        called_target_id = self._called_target_id
        draw_hover = (
            self.ui.draw_hover_world_circle
            and self.ui.hovered_agent_id > 0
            and Agent.IsValid(self.ui.hovered_agent_id)
            and self.ui.hovered_agent_id != called_target_id
        )
        draw_called = (
            self.ui.draw_called_world_circle
            and called_target_id > 0
        )
        if not draw_hover and not draw_called:
            return

        overlay = Overlay()
        overlay.BeginDraw()
        try:
            if draw_hover:
                x, y, z = Agent.GetXYZ(self.ui.hovered_agent_id)
                overlay.DrawPoly3D(x, y, z, float(Range.Touch.value), self._magenta_color(), 32, 4.0)
            if draw_called:
                x, y, z = Agent.GetXYZ(called_target_id)
                overlay.DrawPoly3D(x, y, z, float(Range.Touch.value), self._yellow_color(), 32, 4.0)
        finally:
            overlay.EndDraw()

    def _mission_map_mega_zoom(self) -> float:
        for module in tuple(sys.modules.values()):
            mission_map = getattr(module, "mission_map", None)
            if mission_map is None:
                continue
            try:
                if mission_map.__class__.__name__ == "MissionMap":
                    return float(getattr(mission_map, "mega_zoom", 0.0) or 0.0)
            except Exception:
                continue
        return 0.0

    def _scan_frustum_points(self, player_x: float, player_y: float, segments: int = 24) -> list[tuple[float, float]]:
        radius = float(self.ui.range_filter)
        if radius <= 0:
            return []

        start = float(self.ui.scan_angle_start)
        end = float(self.ui.scan_angle_end)
        span = (end - start) % 360.0
        if span <= 0.0:
            span = 360.0
        if span > 359.0:
            span = 360.0

        facing_angle = self._player_facing_degrees()

        step_count = max(2, min(48, int(segments * (span / 360.0)) + 2))
        points = [(player_x, player_y)]
        for index in range(step_count + 1):
            angle = facing_angle + start + (span * index / step_count)
            radians = math.radians(angle)
            points.append((player_x + math.cos(radians) * radius, player_y + math.sin(radians) * radius))
        return points

    def draw_mission_map_range_ring(self) -> None:
        if not self.ui.draw_mission_map_range or not Map.MissionMap.IsWindowOpen() or not Player.IsPlayerLoaded():
            return

        left, top, right, bottom = Map.MissionMap.GetMissionMapContentsCoords()
        width = right - left
        height = bottom - top
        if width <= 0 or height <= 0:
            return

        mega_zoom = self._mission_map_mega_zoom()
        player_x, player_y = Player.GetXY()
        screen_x, screen_y = Map.MissionMap.MapProjection.GameMapToScreen(player_x, player_y, mega_zoom)
        scan_x, scan_y = self._scan_origin_xy((player_x, player_y))
        radius = Utils.GwinchToPixels(float(self.ui.range_filter), mega_zoom)

        flags = (
            PyImGui.WindowFlags.NoTitleBar |
            PyImGui.WindowFlags.NoScrollbar |
            PyImGui.WindowFlags.NoScrollWithMouse |
            PyImGui.WindowFlags.NoCollapse |
            PyImGui.WindowFlags.NoBackground |
            PyImGui.WindowFlags.NoInputs
        )
        PyImGui.set_next_window_pos(left, top)
        PyImGui.set_next_window_size(width, height)
        PyImGui.push_style_var2(ImGui.ImGuiStyleVar.WindowPadding, 0.0, 0.0)
        PyImGui.push_style_var2(ImGui.ImGuiStyleVar.FramePadding, 0.0, 0.0)
        try:
            if PyImGui.begin("##enemy_tracker_mission_map_range_ring", flags):
                color = Utils.RGBToColor(80, 190, 255, 230)
                fill_color = Utils.RGBToColor(80, 190, 255, 36)
                outline = Utils.RGBToColor(0, 0, 0, 220)
                if self.ui.include_earshot_bubble:
                    earshot_radius = Utils.GwinchToPixels(float(Range.Earshot.value), mega_zoom)
                    PyImGui.draw_list_add_circle(screen_x, screen_y, earshot_radius + 1.0, outline, 48, 2.0)
                    PyImGui.draw_list_add_circle(screen_x, screen_y, earshot_radius, Utils.RGBToColor(255, 205, 80, 230), 48, 2.0)
                if radius > 0:
                    frustum_points = [
                        Map.MissionMap.MapProjection.GameMapToScreen(point_x, point_y, mega_zoom)
                        for point_x, point_y in self._scan_frustum_points(scan_x, scan_y)
                    ]
                    for index in range(1, max(1, len(frustum_points) - 1)):
                        x1, y1 = frustum_points[0]
                        x2, y2 = frustum_points[index]
                        x3, y3 = frustum_points[index + 1]
                        PyImGui.draw_list_add_triangle_filled(x1, y1, x2, y2, x3, y3, fill_color)
                    for index in range(0, len(frustum_points) - 1):
                        x1, y1 = frustum_points[index]
                        x2, y2 = frustum_points[index + 1]
                        PyImGui.draw_list_add_line(x1, y1, x2, y2, outline, 3.0)
                        PyImGui.draw_list_add_line(x1, y1, x2, y2, color, 2.0)
                called_target_id = self._called_target_id
                if called_target_id > 0:
                    self._draw_agent_mission_map_marker(called_target_id, self._yellow_color())
                elif self.ui.draw_hover_mission_map:
                    self._draw_agent_mission_map_marker(self.ui.hovered_agent_id, self._magenta_color())
            PyImGui.end()
        finally:
            PyImGui.pop_style_var(2)


FloatingButton: EnemyTracker | None = None


def _get_shared_vars():
    state = getattr(builtins, ENEMY_TRACKER_SHARED_VARS_ATTR, None)
    return state if state is not None else None

def _ensure_ini() -> bool:
    if EnemyTrackerConfig.INI_INIT:
        return True

    EnemyTrackerConfig.MAIN_INI_KEY = IniManager().ensure_key(EnemyTrackerConfig.INI_PATH, EnemyTrackerConfig.MAIN_INI_FILENAME)
    EnemyTrackerConfig.FLOATING_INI_KEY = IniManager().ensure_key(EnemyTrackerConfig.INI_PATH, EnemyTrackerConfig.FLOATING_INI_FILENAME)
    if not EnemyTrackerConfig.MAIN_INI_KEY or not EnemyTrackerConfig.FLOATING_INI_KEY:
        return False

    IniManager().load_once(EnemyTrackerConfig.MAIN_INI_KEY)
    IniManager().load_once(EnemyTrackerConfig.FLOATING_INI_KEY)

    EnemyTrackerConfig.INI_INIT = True
    return True


def _ensure_state() -> EnemyTracker:
    global FloatingButton
    if FloatingButton is None:
        FloatingButton = EnemyTracker()
        FloatingButton.floating_button.load_visibility()
    return FloatingButton


def GetCurrentRangeFilter() -> int:
    if FloatingButton is None:
        return 0
    return int(FloatingButton.ui.range_filter)


def scanner_main():
    try:
        if not _ensure_ini():
            return
        _ensure_state()
    except Exception as exc:
        Py4GW.Console.Log(EnemyTrackerConfig.MODULE_NAME, f"Scanner error: {exc}", Py4GW.Console.MessageType.Error)
        raise


def configure():
    return


def ui_main():
    try:
        if not _ensure_ini():
            return

        global ENEMY_BAR_DEBUG_STARTUP_LOGGED
        if ENEMY_BAR_DEBUG and not ENEMY_BAR_DEBUG_STARTUP_LOGGED:
            ENEMY_BAR_DEBUG_STARTUP_LOGGED = True
            _enemy_bar_debug("Enemy Party ui_main started")
        state = _ensure_state()
        state.floating_button.draw(EnemyTrackerConfig.FLOATING_INI_KEY)
        state.draw_world_agent_markers()
        state.draw_mission_map_range_ring()
    except Exception as exc:
        Py4GW.Console.Log(EnemyTrackerConfig.MODULE_NAME, f"Error: {exc}", Py4GW.Console.MessageType.Error)
        raise


def main():
    ui_main()


if __name__ == "__main__":
    main()
