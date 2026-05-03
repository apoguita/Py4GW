import json
import math
import os
import sys
from dataclasses import dataclass, field
from typing import ClassVar

import PyImGui

from HeroAI.call_target import CallTarget
from HeroAI.ui_base import HeroAI_BaseUI
from Py4GWCoreLib import GLOBAL_CACHE, Py4GW, Range, Map
from Py4GWCoreLib.Agent import Agent
from Py4GWCoreLib.AgentArray import AgentArray
from Py4GWCoreLib.ImGui import ImGui
from Py4GWCoreLib.IniManager import IniManager
from Py4GWCoreLib.Overlay import Overlay
from Py4GWCoreLib.Party import Party
from Py4GWCoreLib.Player import Player
from Py4GWCoreLib.UIManager import UIManager
from Py4GWCoreLib.py4gwcorelib_src.Utils import Utils


@dataclass
class EnemyTrackerConfig:
    MODULE_NAME: str = "Enemy Tracker"
    INI_PATH: str = "Widgets/Automation/Helpers/EnemyTracker"
    MAIN_INI_FILENAME: str = "EnemyTracker.ini"
    FLOATING_INI_FILENAME: str = "EnemyTrackerFloating.ini"
    DATA_FILENAME: str = "EnemyTrackerData.json"
    NAME_DATA_PREFIX: str = "EnemyTrackerNames"

    MAIN_INI_KEY: str = ""
    FLOATING_INI_KEY: str = ""
    INI_INIT: bool = False
    ICON_PATH: str = os.path.join(Py4GW.Console.get_projects_path(), "crossed swords.png")
    DEFAULT_NAME_LANGUAGE: str = "en"
    NAME_LANGUAGE_CODES: ClassVar[dict[int, str]] = {
        0: "en",
        1: "ko",
        2: "fr",
        3: "de",
        4: "it",
        5: "es",
        6: "zh-Hant",
        8: "ja",
        9: "pl",
        10: "ru",
        17: "bork",
    }


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
class EnemyTrackerVars:
    enemy_array: list[int] = field(default_factory=list)
    live_rows: list[EnemyLiveState] = field(default_factory=list)
    last_cast_skill_by_agent: dict[int, int] = field(default_factory=dict)
    observed_agent_map_keys: set[str] = field(default_factory=set)
    current_map_id: int = 0
    records: dict[str, dict] = field(default_factory=dict)
    name_records: dict[str, dict[str, list[str]]] = field(default_factory=dict)
    data_dirty: bool = False
    names_dirty: bool = False
    last_save_ms: int = 0
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


class HealthBar:
    def __init__(self, width: float = 280.0, height: float = 18.0) -> None:
        self.width = width
        self.height = height
        self.progress = 0.0
        self.empty_color = Utils.RGBToColor(70, 70, 70, 230)
        self.text_color = Utils.RGBToColor(245, 245, 245, 255)
        self.text_shadow_color = Utils.RGBToColor(0, 0, 0, 220)
        
    def draw(self, progress: float, label: str, fill_color: int) -> bool:
        self.progress = max(0.0, min(1.0, float(progress)))

        ImGui.dummy(self.width, self.height)

        item_min, item_max, item_size = ImGui.get_item_rect()
        x1, y1 = item_min
        x2, y2 = item_max

        width = x2 - x1
        height = y2 - y1

        fill_x2 = x1 + (width * self.progress)

        # 100% background / empty bar
        PyImGui.draw_list_add_rect_filled(
            x1, y1,
            x2, y2,
            self.empty_color,
            0.0,
            0
        )

        # Remaining life fill
        if self.progress > 0.0:
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

        return PyImGui.is_item_clicked(0)


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
        self.vars = EnemyTrackerVars()
        self._sync_range_preset_from_filter()
        self.health_bar = HealthBar(width=220.0, height=18.0)
        self.data_path = os.path.join(Py4GW.Console.get_projects_path(), EnemyTrackerConfig.DATA_FILENAME)
        self.data_dir = os.path.dirname(self.data_path)
        self._load_data()

    def _sync_range_preset_from_filter(self) -> None:
        self.vars.range_preset_index = 0
        for index, (_, preset_value) in enumerate(self.RANGE_PRESETS):
            if preset_value is not None and int(preset_value) == int(self.vars.range_filter):
                self.vars.range_preset_index = index
                return

    def _load_data(self) -> None:
        try:
            if os.path.exists(self.data_path):
                with open(self.data_path, "r", encoding="utf-8") as handle:
                    data = json.load(handle)
                self.vars.records = self._normalize_records(dict(data.get("enemies", {})))
                if int(data.get("schema_version", 1) or 1) < 2:
                    self.vars.data_dirty = True
            self._load_name_data()
        except Exception as exc:
            Py4GW.Console.Log(EnemyTrackerConfig.MODULE_NAME, f"Failed to load data: {exc}", Py4GW.Console.MessageType.Warning)

    def _name_data_path(self, language: str) -> str:
        language_key = str(language or EnemyTrackerConfig.DEFAULT_NAME_LANGUAGE).strip()
        return os.path.join(self.data_dir, f"{EnemyTrackerConfig.NAME_DATA_PREFIX}.{language_key}.json")

    def _load_name_data(self) -> None:
        prefix = f"{EnemyTrackerConfig.NAME_DATA_PREFIX}."
        suffix = ".json"
        if not os.path.isdir(self.data_dir):
            return
        for filename in os.listdir(self.data_dir):
            if not filename.startswith(prefix) or not filename.endswith(suffix):
                continue
            language = filename[len(prefix):-len(suffix)].strip().lower()
            if not language:
                continue
            path = os.path.join(self.data_dir, filename)
            try:
                with open(path, "r", encoding="utf-8") as handle:
                    data = json.load(handle)
                self.vars.name_records[language] = self._normalize_name_records(dict(data.get("names", {})))
            except Exception as exc:
                Py4GW.Console.Log(EnemyTrackerConfig.MODULE_NAME, f"Failed to load {filename}: {exc}", Py4GW.Console.MessageType.Warning)

    def _save_data_if_needed(self, force: bool = False) -> None:
        if not self.vars.data_dirty and not self.vars.names_dirty and not force:
            return
        now = int(Py4GW.Game.get_tick_count64())
        if not force and now - self.vars.last_save_ms < 2000:
            return
        try:
            if self.vars.data_dirty or force:
                payload = {
                    "schema": "py4gw_enemy_tracker",
                    "schema_version": 2,
                    "enemies": self.vars.records,
                }
                with open(self.data_path, "w", encoding="utf-8") as handle:
                    json.dump(payload, handle, indent=2, sort_keys=True)
            if self.vars.names_dirty or force:
                self._save_name_data()
            self.vars.data_dirty = False
            self.vars.names_dirty = False
            self.vars.last_save_ms = now
        except Exception as exc:
            Py4GW.Console.Log(EnemyTrackerConfig.MODULE_NAME, f"Failed to save data: {exc}", Py4GW.Console.MessageType.Warning)

    def _save_name_data(self) -> None:
        for language, names in self.vars.name_records.items():
            payload = {
                "schema": "py4gw_enemy_tracker_names",
                "schema_version": 1,
                "language": language,
                "names": names,
            }
            with open(self._name_data_path(language), "w", encoding="utf-8") as handle:
                json.dump(payload, handle, indent=2, sort_keys=True)

    def _enemy_key(self, agent_id: int, name: str, enc_name: str, model_id: int) -> str:
        if enc_name:
            return f"enc:{enc_name}"
        if model_id:
            return f"model:{model_id}"
        return f"name:{name}"

    def _current_name_language(self) -> str:
        try:
            language_id = int(UIManager.GetTextLanguage())
        except Exception:
            language_id = 0
        return EnemyTrackerConfig.NAME_LANGUAGE_CODES.get(
            language_id,
            EnemyTrackerConfig.DEFAULT_NAME_LANGUAGE,
        )

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

    def _normalize_names_by_language(self, record: dict) -> dict[str, list[str]]:
        language_names: dict[str, list[str]] = {}
        raw_language_names = record.get("names_by_language", {})
        if isinstance(raw_language_names, dict):
            for language, names in raw_language_names.items():
                language_key = str(language or "").strip().lower()
                if not language_key:
                    continue
                clean_names = self._clean_name_values(names)
                if clean_names:
                    language_names[language_key] = clean_names

        legacy_names = self._clean_name_values(record.get("names", []))
        if legacy_names:
            english_names = language_names.setdefault(EnemyTrackerConfig.DEFAULT_NAME_LANGUAGE, [])
            for name in legacy_names:
                if name not in english_names:
                    english_names.append(name)

        record.pop("names", None)
        record.pop("names_by_language", None)
        return language_names

    def _add_name_record(self, key: str, language: str, name: str) -> bool:
        clean_name = str(name or "").strip()
        if not clean_name:
            return False
        language_key = str(language or EnemyTrackerConfig.DEFAULT_NAME_LANGUAGE).strip().lower()
        names = self.vars.name_records.setdefault(language_key, {}).setdefault(key, [])
        if clean_name in names:
            return False
        names.append(clean_name)
        return True

    def _normalize_name_records(self, raw_names: dict[str, object]) -> dict[str, list[str]]:
        normalized: dict[str, list[str]] = {}
        for key, names in raw_names.items():
            clean_names = self._clean_name_values(names)
            if clean_names:
                normalized[str(key)] = clean_names
        return normalized

    def _normalize_record(self, key: str, record: dict) -> dict:
        for language, names in self._normalize_names_by_language(record).items():
            for name in names:
                if self._add_name_record(key, language, name):
                    self.vars.names_dirty = True
        record.setdefault("observed_maps", {})
        record.setdefault("observed_skills", {})
        record.pop("profession_counts", None)
        record.setdefault("encoded_names", [])
        record.setdefault("model_ids", [])
        record.setdefault("inferred_primary", "")
        record.setdefault("inferred_secondary", "")
        return record

    def _normalize_records(self, records: dict[str, dict]) -> dict[str, dict]:
        normalized: dict[str, dict] = {}
        for key, record in records.items():
            if isinstance(record, dict):
                normalized[str(key)] = self._normalize_record(str(key), record)
        return normalized

    def _record_names(self, key: str, language: str = EnemyTrackerConfig.DEFAULT_NAME_LANGUAGE) -> list[str]:
        language_key = str(language or EnemyTrackerConfig.DEFAULT_NAME_LANGUAGE).strip().lower()
        if language_key in self.vars.name_records and key in self.vars.name_records[language_key]:
            return self.vars.name_records[language_key][key]
        if EnemyTrackerConfig.DEFAULT_NAME_LANGUAGE in self.vars.name_records and key in self.vars.name_records[EnemyTrackerConfig.DEFAULT_NAME_LANGUAGE]:
            return self.vars.name_records[EnemyTrackerConfig.DEFAULT_NAME_LANGUAGE][key]
        for names_by_key in self.vars.name_records.values():
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

    def _ensure_record(self, key: str, name: str, enc_name: str, model_id: int) -> dict:
        record = self.vars.records.get(key)
        if record is None:
            record = {
                "encoded_names": [],
                "model_ids": [],
                "observed_maps": {},
                "observed_skills": {},
                "inferred_primary": "",
                "inferred_secondary": "",
            }
            self.vars.records[key] = record
            self.vars.data_dirty = True

        self._normalize_record(key, record)
        language = self._current_name_language()
        if self._add_name_record(key, language, name):
            self.vars.names_dirty = True
        if enc_name and enc_name not in record["encoded_names"]:
            record["encoded_names"].append(enc_name)
            self.vars.data_dirty = True
        if model_id and model_id not in record["model_ids"]:
            record["model_ids"].append(model_id)
            self.vars.data_dirty = True
        return record

    def _current_map_observation(self) -> dict | None:
        try:
            map_id = int(Map.GetMapID() or 0)
        except Exception:
            map_id = 0
        if map_id <= 0:
            return None

        try:
            map_name = Map.GetMapName(map_id)
        except Exception:
            map_name = ""
        try:
            base_map_id = int(Map.GetBaseMapID(map_id) or map_id)
        except Exception:
            base_map_id = map_id
        try:
            instance_type = Map.GetInstanceTypeName()
        except Exception:
            instance_type = ""

        return {
            "id": map_id,
            "name": map_name,
            "base_id": base_map_id,
            "instance_type": instance_type,
        }

    def _observe_map(self, record_key: str, record: dict, map_info: dict | None) -> None:
        if not map_info:
            return

        map_id = int(map_info.get("id", 0) or 0)
        if map_id <= 0:
            return

        if self.vars.current_map_id != map_id:
            self.vars.current_map_id = map_id
            self.vars.observed_agent_map_keys.clear()

        seen_key = f"{record_key}|{map_id}"
        if seen_key in self.vars.observed_agent_map_keys:
            return
        self.vars.observed_agent_map_keys.add(seen_key)

        maps = record.setdefault("observed_maps", {})
        map_key = str(map_id)
        if map_key in maps:
            return

        maps[map_key] = {
            "id": map_id,
            "name": str(map_info.get("name", "") or ""),
            "base_id": int(map_info.get("base_id", map_id) or map_id),
            "instance_type": str(map_info.get("instance_type", "") or ""),
        }
        self.vars.data_dirty = True

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
        if record.get("inferred_primary") != primary or record.get("inferred_secondary") != secondary:
            record["inferred_primary"] = primary
            record["inferred_secondary"] = secondary
            self.vars.data_dirty = True
        return primary, secondary

    def _observe_cast(self, agent_id: int, record: dict, skill_id: int) -> None:
        if skill_id <= 0:
            self.vars.last_cast_skill_by_agent[agent_id] = 0
            return

        if self.vars.last_cast_skill_by_agent.get(agent_id) == skill_id:
            return
        self.vars.last_cast_skill_by_agent[agent_id] = skill_id

        skill_name, prof_id, prof_name = self._skill_info(skill_id)
        skills = record.setdefault("observed_skills", {})
        skill_key = str(skill_id)
        if skill_key in skills:
            return

        skills[skill_key] = {
            "id": int(skill_id),
            "name": skill_name,
            "profession_id": int(prof_id),
            "profession": prof_name,
        }
        self._infer_professions(record)
        self.vars.data_dirty = True

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

    def _poll(self) -> None:
        player_xy = Player.GetXY()
        rows: list[EnemyLiveState] = []
        map_info = self._current_map_observation()
        try:
            self.vars.called_target_id = int(Party.GetPartyTarget() or 0)
        except Exception:
            self.vars.called_target_id = 0
        self.vars.enemy_array = AgentArray.GetEnemyArray()
        for agent_id in self.vars.enemy_array:
            if not Agent.IsValid(agent_id) or not Agent.IsLiving(agent_id):
                continue
            if Agent.IsDead(agent_id) and not self.vars.include_dead:
                continue
            distance = Utils.Distance(player_xy, Agent.GetXY(agent_id))
            if not self._is_inside_scan_frustum(player_xy, Agent.GetXY(agent_id), distance):
                continue

            name = Agent.GetNameByID(agent_id) or f"Agent {agent_id}"
            enc_name = Agent.GetEncNameStrByID(agent_id)
            model_id = int(Agent.GetModelID(agent_id) or 0)
            key = self._enemy_key(agent_id, name, enc_name, model_id)
            record = self._ensure_record(key, name, enc_name, model_id)
            self._observe_map(key, record, map_info)

            casting_skill_id = int(Agent.GetCastingSkillID(agent_id) if Agent.IsCasting(agent_id) else 0)
            self._observe_cast(agent_id, record, casting_skill_id)
            primary, secondary = self._infer_professions(record)

            rows.append(
                EnemyLiveState(
                    agent_id=agent_id,
                    key=key,
                    name=name,
                    enc_name=enc_name,
                    model_id=model_id,
                    level=int(Agent.GetLevel(agent_id) or 0),
                    distance=distance,
                    health=float(Agent.GetHealth(agent_id) or 0.0),
                    max_health=int(Agent.GetMaxHealth(agent_id) or 0),
                    casting_skill_id=casting_skill_id,
                    statuses=self._statuses(agent_id),
                    inferred_primary=primary,
                    inferred_secondary=secondary,
                )
            )

        self.vars.live_rows = self._sort_rows(rows)
        self._save_data_if_needed()

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
            player_x + (forward_x * float(self.vars.scan_offset_forward)) + (right_x * float(self.vars.scan_offset_right)),
            player_y + (forward_y * float(self.vars.scan_offset_forward)) + (right_y * float(self.vars.scan_offset_right)),
        )

    def _relative_angle_to_point(self, origin_xy: tuple[float, float], target_xy: tuple[float, float]) -> float:
        origin_x, origin_y = origin_xy
        target_x, target_y = target_xy
        point_angle = math.degrees(math.atan2(target_y - origin_y, target_x - origin_x))
        return self._normalize_degrees(point_angle - self._player_facing_degrees())

    def _is_angle_in_scan(self, relative_angle: float) -> bool:
        start = self._normalize_degrees(self.vars.scan_angle_start)
        end = self._normalize_degrees(self.vars.scan_angle_end)
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
        if self.vars.include_earshot_bubble and distance <= float(Range.Earshot.value):
            return True
        scan_origin = self._scan_origin_xy(player_xy)
        scan_distance = Utils.Distance(scan_origin, target_xy)
        if self.vars.range_filter > 0 and scan_distance > self.vars.range_filter:
            return False
        return self._is_angle_in_scan(self._relative_angle_to_point(scan_origin, target_xy))

    def _sort_rows(self, rows: list[EnemyLiveState]) -> list[EnemyLiveState]:
        mode = self.SORT_OPTIONS[max(0, min(self.vars.sort_index, len(self.SORT_OPTIONS) - 1))]
        if mode == "Agent ID":
            return sorted(rows, key=lambda row: row.agent_id, reverse=self.vars.sort_reverse)
        if mode == "Health":
            return sorted(rows, key=lambda row: row.health, reverse=self.vars.sort_reverse)
        if mode == "Profession":
            return sorted(rows, key=lambda row: row.inferred_primary, reverse=self.vars.sort_reverse)
        if mode == "Name":
            return sorted(rows, key=lambda row: row.name, reverse=self.vars.sort_reverse)
        if mode == "Level":
            return sorted(rows, key=lambda row: row.level, reverse=not self.vars.sort_reverse)
        return sorted(rows, key=lambda row: row.distance, reverse=self.vars.sort_reverse)

    def _set_sort(self, mode: str) -> None:
        if mode not in self.SORT_OPTIONS:
            return
        index = self.SORT_OPTIONS.index(mode)
        if self.vars.sort_index == index:
            self.vars.sort_reverse = not self.vars.sort_reverse
        else:
            self.vars.sort_index = index
            self.vars.sort_reverse = mode == "Level"
        self.vars.live_rows = self._sort_rows(self.vars.live_rows)

    def _sort_button(self, mode: str, label: str | None = None) -> None:
        active = self.SORT_OPTIONS[max(0, min(self.vars.sort_index, len(self.SORT_OPTIONS) - 1))] == mode
        suffix = " v" if self.vars.sort_reverse else " ^"
        button_label = f"{label or self.SORT_LABELS.get(mode, mode)}{suffix if active else ''}##sort_{mode}_{label or 'button'}"
        if PyImGui.button(button_label):
            self._set_sort(mode)

    def _current_range_label(self) -> str:
        for label, value in self.RANGE_BUTTONS:
            if int(value) == int(self.vars.range_filter):
                return label
        return str(int(self.vars.range_filter))

    def _range_combo_index(self) -> int:
        for index, (_, value) in enumerate(self.RANGE_BUTTONS, start=1):
            if int(value) == int(self.vars.range_filter):
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
        for record in self.vars.records.values():
            if record.get("inferred_primary"):
                names.add(record["inferred_primary"])
            if record.get("inferred_secondary"):
                names.add(record["inferred_secondary"])
        return ["All"] + sorted(name for name in names if name != "All")

    def _filtered_rows(self) -> list[EnemyLiveState]:
        filters = self._profession_filters()
        self.vars.profession_filter_index = max(0, min(self.vars.profession_filter_index, len(filters) - 1))
        prof_filter = filters[self.vars.profession_filter_index]
        if prof_filter == "All":
            return self.vars.live_rows
        return [
            row for row in self.vars.live_rows
            if row.inferred_primary == prof_filter or row.inferred_secondary == prof_filter
        ]

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

    def _draw_row(self, row: EnemyLiveState) -> None:
        skill_text = ""
        if row.casting_skill_id:
            skill_name, _, _ = self._skill_info(row.casting_skill_id)
            skill_text = skill_name

        PyImGui.table_next_row()
        PyImGui.table_next_column()
        if PyImGui.button(f"Call##call_{row.agent_id}"):
            CallTarget(row.agent_id, interact=False)
        PyImGui.table_next_column()
        self.health_bar.draw(row.health, self._health_label(row), self._health_color(row))
        hovered = PyImGui.is_item_hovered()
        if hovered:
            self.vars.hovered_agent_id = row.agent_id
        if hovered and self.vars.draw_hover_row_outline:
            item_min, item_max, _ = ImGui.get_item_rect()
            x1, y1 = item_min
            x2, y2 = item_max
            PyImGui.draw_list_add_rect(x1 - 2.0, y1 - 2.0, x2 + 2.0, y2 + 2.0, self._magenta_color(), 0.0, 0, 2.0)
        if row.agent_id == self.vars.called_target_id:
            item_min, item_max, _ = ImGui.get_item_rect()
            x1, y1 = item_min
            x2, y2 = item_max
            PyImGui.draw_list_add_rect(x1 - 1.0, y1 - 1.0, x2 + 1.0, y2 + 1.0, self._yellow_color(), 0.0, 0, 2.0)
        if hovered:
            PyImGui.begin_tooltip()
            PyImGui.text(f"HP: {int(row.health * 100)}%")
            if row.agent_id == self.vars.called_target_id:
                PyImGui.text("Called target")
            PyImGui.text(f"Distance: {int(row.distance)}")
            PyImGui.text(f"Agent: {row.agent_id}")
            PyImGui.text(f"Model: {row.model_id}")
            if skill_text:
                PyImGui.text(f"Casting: {skill_text}")
            if row.statuses:
                PyImGui.text(f"Status: {', '.join(row.statuses)}")
            if row.enc_name:
                PyImGui.text(f"Enc: {row.enc_name}")
            PyImGui.end_tooltip()

    def _draw_controls(self) -> None:
        
        PyImGui.text("Range:")
        PyImGui.same_line(0, -1)
        
        range_names = ["Custom"] + [label for label, _ in self.RANGE_BUTTONS]
        selected_range = PyImGui.combo("##enemy_tracker_range_combo", self._range_combo_index(), range_names)
        if 1 <= selected_range <= len(self.RANGE_BUTTONS):
            self.vars.range_filter = int(self.RANGE_BUTTONS[selected_range - 1][1])
            self._sync_range_preset_from_filter()

        max_offset = int(max(float(range_value.value) for range_value in Range))
        self.vars.range_filter = self._slider_with_input_int("Range", int(self.vars.range_filter), 0, max_offset)
        self._sync_range_preset_from_filter()
        self.vars.scan_angle_start = self._slider_with_input_int("Angle start", int(self.vars.scan_angle_start), -180, 180)
        self.vars.scan_angle_end = self._slider_with_input_int("Angle end", int(self.vars.scan_angle_end), -180, 180)
        self.vars.scan_offset_forward = self._slider_with_input_int("Offset forward", int(self.vars.scan_offset_forward), -max_offset, max_offset)
        self.vars.scan_offset_right = self._slider_with_input_int("Offset right", int(self.vars.scan_offset_right), -max_offset, max_offset)

        #PyImGui.same_line(0, -1)
        
        self.vars.include_earshot_bubble = PyImGui.checkbox("Include Earshot bubble", self.vars.include_earshot_bubble)
        self.vars.draw_mission_map_range = PyImGui.checkbox("Draw in Mission map+", self.vars.draw_mission_map_range)
        self.vars.draw_hover_row_outline = PyImGui.checkbox("Hover row outline", self.vars.draw_hover_row_outline)
        self.vars.draw_hover_mission_map = PyImGui.checkbox("Hover mission map marker", self.vars.draw_hover_mission_map)
        self.vars.draw_hover_world_circle = PyImGui.checkbox("Hover 3D touch circle", self.vars.draw_hover_world_circle)
        self.vars.draw_called_world_circle = PyImGui.checkbox("Called 3D touch circle", self.vars.draw_called_world_circle)

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
        PyImGui.text(f"Visible: {len(rows)} / Polled: {len(self.vars.live_rows)}")
        PyImGui.separator()
        self._draw_controls()

    def _record_label(self, key: str, record: dict) -> str:
        names = self._record_names(key)
        name = names[0] if names else key
        primary = record.get("inferred_primary") or "?"
        secondary = record.get("inferred_secondary") or ""
        profession = f"{primary}/{secondary}" if secondary else primary
        return f"{name} [{profession}]"

    def _record_search_text(self, key: str, record: dict) -> str:
        parts = [key]
        for language, names_by_key in self.vars.name_records.items():
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
        query = str(self.vars.atlas_search or "").strip().lower()
        matches = []
        for key, record in self.vars.records.items():
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
        PyImGui.begin_group()
        PyImGui.text(self._record_label(key, record))
        PyImGui.text(f"Key: {key}")
        english_names = ", ".join(str(name) for name in self.vars.name_records.get(EnemyTrackerConfig.DEFAULT_NAME_LANGUAGE, {}).get(key, [])) or "?"
        encoded_names = ", ".join(str(name) for name in record.get("encoded_names", [])) or "?"
        model_ids = ", ".join(str(model_id) for model_id in record.get("model_ids", [])) or "?"
        PyImGui.text(f"English names: {english_names}")
        other_languages = sorted(
            language for language, names_by_key in self.vars.name_records.items()
            if language != EnemyTrackerConfig.DEFAULT_NAME_LANGUAGE and key in names_by_key
        )
        for language in other_languages:
            localized_names = ", ".join(str(name) for name in self.vars.name_records.get(language, {}).get(key, [])) or "?"
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
            selected = self.vars.atlas_selected_skill_id == skill_id
            texture_path = GLOBAL_CACHE.Skill.ExtraData.GetTexturePath(skill_id)
            if ImGui.image_toggle_button(f"enemy_atlas_skill_{skill_id}_{index}", texture_path, selected, 42, 42):
                self.vars.atlas_selected_skill_id = skill_id

            if PyImGui.is_item_hovered():
                if PyImGui.begin_tooltip():
                    HeroAI_BaseUI._draw_skill_info_card(skill_id, compact=True, tooltip=True)
                    self._draw_skill_observation_meta(skill)
                    PyImGui.end_tooltip()

            if (index + 1) % cards_per_row != 0 and index + 1 < len(skills):
                PyImGui.same_line(0, 8)

    def _draw_atlas_skills(self, record: dict) -> None:
        skills = self._observed_skills_for_record(record)
        PyImGui.text(f"Observed skills: {len(skills)}")
        if not skills:
            PyImGui.text("No observed skills yet.")
            return

        valid_ids = [int(skill.get("id", 0)) for skill in skills if int(skill.get("id", 0)) > 0]
        if self.vars.atlas_selected_skill_id not in valid_ids:
            self.vars.atlas_selected_skill_id = valid_ids[0] if valid_ids else 0

        self._draw_observed_skill_icon_grid(skills)
        selected_skill = next((skill for skill in skills if int(skill.get("id", 0)) == self.vars.atlas_selected_skill_id), None)
        if selected_skill:
            PyImGui.separator()
            self._draw_skill_observation_meta(selected_skill)
            HeroAI_BaseUI._draw_skill_info_card(int(selected_skill.get("id", 0)), compact=False, tooltip=False)

    def _draw_enemy_atlas(self) -> None:
        self.vars.atlas_search = PyImGui.input_text("Search##enemy_atlas_search", self.vars.atlas_search, 128)
        matches = self._atlas_matches()
        PyImGui.text(f"Matches: {len(matches)} / Known: {len(self.vars.records)}")
        if matches and self.vars.atlas_selected_key not in self.vars.records:
            self.vars.atlas_selected_key = matches[0][0]

        if PyImGui.begin_table("EnemyAtlasLayout", 2, PyImGui.TableFlags.BordersInnerV):
            PyImGui.table_setup_column("Enemies", PyImGui.TableColumnFlags.WidthFixed, 230)
            PyImGui.table_setup_column("Data", PyImGui.TableColumnFlags.WidthFixed, 390)
            PyImGui.table_next_row()
            PyImGui.table_next_column()
            for key, record in matches[:200]:
                selected = key == self.vars.atlas_selected_key
                if PyImGui.selectable(f"{self._record_label(key, record)}##atlas_{key}", selected, PyImGui.SelectableFlags.NoFlag, (0.0, 0.0)):
                    self.vars.atlas_selected_key = key

            PyImGui.table_next_column()
            record = self.vars.records.get(self.vars.atlas_selected_key)
            if not record:
                PyImGui.text("Select an enemy.")
            else:
                self._draw_enemy_card(self.vars.atlas_selected_key, record)
                PyImGui.separator()
                self._draw_atlas_skills(record)
            PyImGui.end_table()

    def draw_window(self) -> None:
        expanded, open_ = ImGui.BeginWithClose(
            ini_key=EnemyTrackerConfig.MAIN_INI_KEY,
            name=EnemyTrackerConfig.MODULE_NAME,
            p_open=self.floating_button.visible,
            flags=PyImGui.WindowFlags.AlwaysAutoResize,
        )
        self.floating_button.sync_begin_with_close(open_)

        if expanded:
            self._poll()
            rows = self._filtered_rows()
            self.vars.hovered_agent_id = 0

            if PyImGui.begin_tab_bar("EnemyTrackerTabs"):
                if PyImGui.begin_tab_item("Tracker"):
                    self._draw_tracker_tab(rows)
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

        draw_hover = (
            self.vars.draw_hover_world_circle
            and self.vars.hovered_agent_id > 0
            and Agent.IsValid(self.vars.hovered_agent_id)
        )
        draw_called = (
            self.vars.draw_called_world_circle
            and self.vars.called_target_id > 0
            and Agent.IsValid(self.vars.called_target_id)
        )
        if not draw_hover and not draw_called:
            return

        overlay = Overlay()
        overlay.BeginDraw()
        try:
            if draw_hover:
                x, y, z = Agent.GetXYZ(self.vars.hovered_agent_id)
                overlay.DrawPoly3D(x, y, z, float(Range.Touch.value), self._magenta_color(), 32, 4.0)
            if draw_called:
                x, y, z = Agent.GetXYZ(self.vars.called_target_id)
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
        radius = float(self.vars.range_filter)
        if radius <= 0:
            return []

        start = float(self.vars.scan_angle_start)
        end = float(self.vars.scan_angle_end)
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
        if not self.vars.draw_mission_map_range or not Map.MissionMap.IsWindowOpen() or not Player.IsPlayerLoaded():
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
        radius = Utils.GwinchToPixels(float(self.vars.range_filter), mega_zoom)

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
                if self.vars.include_earshot_bubble:
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
                if self.vars.draw_hover_mission_map:
                    self._draw_agent_mission_map_marker(self.vars.hovered_agent_id, self._magenta_color())
            PyImGui.end()
        finally:
            PyImGui.pop_style_var(2)


FloatingButton: EnemyTracker | None = None


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
    return int(FloatingButton.vars.range_filter)


def main():
    try:
        if not _ensure_ini():
            return

        state = _ensure_state()
        state.floating_button.draw(EnemyTrackerConfig.FLOATING_INI_KEY)
        state.draw_world_agent_markers()
        state.draw_mission_map_range_ring()
    except Exception as exc:
        Py4GW.Console.Log(EnemyTrackerConfig.MODULE_NAME, f"Error: {exc}", Py4GW.Console.MessageType.Error)
        raise


if __name__ == "__main__":
    main()
