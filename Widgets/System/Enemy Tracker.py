import builtins
import json
import os
import tkinter as tk
from dataclasses import dataclass, field
from tkinter import filedialog
from typing import ClassVar

import PyImGui

from Py4GWCoreLib import Color
from Py4GWCoreLib import GLOBAL_CACHE, Py4GW, Range, Map
from Py4GWCoreLib.Agent import Agent
from Py4GWCoreLib.AgentArray import AgentArray
from Py4GWCoreLib.ImGui import ImGui
from Py4GWCoreLib.IniManager import IniManager
from Py4GWCoreLib.Player import Player
from Py4GWCoreLib.UIManager import UIManager
from Py4GWCoreLib.py4gwcorelib_src.Utils import Utils


MODULE_NAME = "Enemy Tracker"
MODULE_ICON = "Textures/Module_Icons/Environment Upkeeper.png"
OPTIONAL = False
ENEMY_TRACKER_SHARED_VARS_ATTR = "_py4gw_enemy_tracker_shared_vars"


def tooltip():
    PyImGui.begin_tooltip()
    title_color = Color(255, 200, 100, 255)
    ImGui.push_font("Regular", 20)
    PyImGui.text_colored(MODULE_NAME, title_color.to_tuple_normalized())
    ImGui.pop_font()
    PyImGui.separator()
    PyImGui.text("System widget that keeps enemy scanning and enemy data persistence active.")
    PyImGui.text("Use Configure for import/export and data maintenance.")
    PyImGui.end_tooltip()


@dataclass
class EnemyTrackerConfig:
    MODULE_NAME: str = "Enemy Tracker"
    INI_PATH: str = "Widgets/Automation/Helpers/EnemyTracker"
    MAIN_INI_FILENAME: str = "EnemyTracker.ini"
    FLOATING_INI_FILENAME: str = "EnemyTrackerFloating.ini"
    DATA_DIRNAME: str = "EnemyData"
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
    include_dead: bool = False


class EnemyTracker:
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
        shared_vars = _get_shared_vars()
        self.vars = shared_vars if shared_vars is not None else EnemyTrackerVars()
        if shared_vars is None:
            _set_shared_vars(self.vars)
        self.data_root = os.path.join(Py4GW.Console.get_projects_path(), EnemyTrackerConfig.DATA_DIRNAME)
        self.data_path = os.path.join(self.data_root, EnemyTrackerConfig.DATA_FILENAME)
        self.data_dir = os.path.dirname(self.data_path)
        if shared_vars is None or (not self.vars.records and not self.vars.name_records):
            self._load_data()

    def _legacy_data_root(self) -> str:
        return Py4GW.Console.get_projects_path()

    def _legacy_data_path(self) -> str:
        return os.path.join(self._legacy_data_root(), EnemyTrackerConfig.DATA_FILENAME)

    def _load_data(self) -> None:
        try:
            load_path = self.data_path if os.path.exists(self.data_path) else self._legacy_data_path()
            if os.path.exists(load_path):
                with open(load_path, "r", encoding="utf-8") as handle:
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
        for candidate_dir in (self.data_dir, self._legacy_data_root()):
            if not os.path.isdir(candidate_dir):
                continue
            for filename in os.listdir(candidate_dir):
                if not filename.startswith(prefix) or not filename.endswith(suffix):
                    continue
                language = filename[len(prefix):-len(suffix)].strip().lower()
                if not language or language in self.vars.name_records:
                    continue
                path = os.path.join(candidate_dir, filename)
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
            os.makedirs(self.data_dir, exist_ok=True)
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
        os.makedirs(self.data_dir, exist_ok=True)
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

    def _merge_record(self, key: str, incoming: dict) -> None:
        incoming_record = self._normalize_record(str(key), dict(incoming))
        existing = self.vars.records.get(str(key))
        if existing is None:
            self.vars.records[str(key)] = incoming_record
            self.vars.data_dirty = True
            return

        changed = False
        for field_name in ("encoded_names", "model_ids"):
            existing_values = list(existing.get(field_name, []))
            for value in incoming_record.get(field_name, []):
                if value not in existing_values:
                    existing_values.append(value)
                    changed = True
            existing[field_name] = existing_values

        for map_key, map_entry in incoming_record.get("observed_maps", {}).items():
            if map_key not in existing.setdefault("observed_maps", {}):
                existing["observed_maps"][map_key] = map_entry
                changed = True

        for skill_key, skill_entry in incoming_record.get("observed_skills", {}).items():
            if skill_key not in existing.setdefault("observed_skills", {}):
                existing["observed_skills"][skill_key] = skill_entry
                changed = True

        previous_primary = str(existing.get("inferred_primary", "") or "")
        previous_secondary = str(existing.get("inferred_secondary", "") or "")
        primary, secondary = self._infer_professions(existing)
        changed = changed or primary != previous_primary or secondary != previous_secondary

        if changed:
            self.vars.data_dirty = True

    def _export_payload(self) -> dict:
        return {
            "schema": "py4gw_enemy_tracker_bundle",
            "schema_version": 1,
            "enemies": self.vars.records,
            "names_by_language": self.vars.name_records,
        }

    def export_bundle_to(self, path: str) -> bool:
        try:
            if not path:
                return False
            payload = self._export_payload()
            with open(path, "w", encoding="utf-8") as handle:
                json.dump(payload, handle, indent=2, sort_keys=True)
            return True
        except Exception as exc:
            Py4GW.Console.Log(EnemyTrackerConfig.MODULE_NAME, f"Export failed: {exc}", Py4GW.Console.MessageType.Warning)
            return False

    def import_bundle_from(self, path: str) -> bool:
        try:
            if not path or not os.path.exists(path):
                return False
            with open(path, "r", encoding="utf-8") as handle:
                payload = json.load(handle)

            imported_any = False
            incoming_records = dict(payload.get("enemies", {}))
            for key, record in incoming_records.items():
                if isinstance(record, dict):
                    self._merge_record(str(key), record)
                    imported_any = True

            incoming_names = payload.get("names_by_language", {})
            if isinstance(incoming_names, dict):
                for language, names_by_key in incoming_names.items():
                    language_key = str(language or EnemyTrackerConfig.DEFAULT_NAME_LANGUAGE).strip().lower()
                    if not isinstance(names_by_key, dict):
                        continue
                    for key, names in names_by_key.items():
                        for name in self._clean_name_values(names):
                            if self._add_name_record(str(key), language_key, name):
                                self.vars.names_dirty = True
                                imported_any = True

            if imported_any:
                self._save_data_if_needed(force=True)
            return imported_any
        except Exception as exc:
            Py4GW.Console.Log(EnemyTrackerConfig.MODULE_NAME, f"Import failed: {exc}", Py4GW.Console.MessageType.Warning)
            return False

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
        current_enemy_array = list(AgentArray.GetEnemyArray() or [])
        self.vars.enemy_array[:] = current_enemy_array
        for agent_id in self.vars.enemy_array:
            if not Agent.IsValid(agent_id) or not Agent.IsLiving(agent_id):
                continue
            if Agent.IsDead(agent_id) and not self.vars.include_dead:
                continue
            distance = Utils.Distance(player_xy, Agent.GetXY(agent_id))
            if distance > self.SCANNER_RADIUS:
                continue

            name = Agent.GetNameByID(agent_id) or f"Agent {agent_id}"
            enc_name = Agent.GetEncNameStrByID(agent_id)
            model_id = int(Agent.GetModelID(agent_id) or 0)
            key = self._enemy_key(agent_id, name, enc_name, model_id)
            record = self._ensure_record(key, name, enc_name, model_id)
            self._observe_map(key, record, map_info)

            living = Agent.GetLivingAgentByID(agent_id)
            native_skill_id = int(getattr(living, "skill", 0) or 0)
            self._observe_cast(agent_id, record, native_skill_id)

            casting_skill_id = int(Agent.GetCastingSkillID(agent_id) if Agent.IsCasting(agent_id) else 0)
            if casting_skill_id and casting_skill_id != native_skill_id:
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

        self.vars.live_rows[:] = rows
        self._save_data_if_needed()

    def draw_scanner_config(self) -> None:
        PyImGui.text(f"Data folder: {self.data_root}")
        PyImGui.text(f"Known enemies: {len(self.vars.records)}")
        PyImGui.text(f"Languages: {len(self.vars.name_records)}")
        PyImGui.text(f"Live rows cached: {len(self.vars.live_rows)}")
        PyImGui.separator()

        if PyImGui.button("Import / Merge JSON"):
            root = tk.Tk()
            root.withdraw()
            root.attributes("-topmost", True)
            try:
                path = filedialog.askopenfilename(
                    title="Import Enemy Tracker Data",
                    initialdir=self.data_root,
                    filetypes=[("JSON Files", "*.json"), ("All files", "*.*")],
                )
            finally:
                root.destroy()
            if path:
                self.import_bundle_from(path)

        PyImGui.same_line(0, 8)
        if PyImGui.button("Export JSON"):
            root = tk.Tk()
            root.withdraw()
            root.attributes("-topmost", True)
            try:
                path = filedialog.asksaveasfilename(
                    title="Export Enemy Tracker Data",
                    initialdir=self.data_root,
                    defaultextension=".json",
                    filetypes=[("JSON Files", "*.json"), ("All files", "*.*")],
                )
            finally:
                root.destroy()
            if path:
                self.export_bundle_to(path)

    def draw_window(self) -> None:
        expanded, open_ = ImGui.BeginWithClose(
            ini_key=EnemyTrackerConfig.MAIN_INI_KEY,
            name=EnemyTrackerConfig.MODULE_NAME,
            p_open=self.floating_button.visible,
            flags=PyImGui.WindowFlags.AlwaysAutoResize,
        )
        self.floating_button.sync_begin_with_close(open_)

        if expanded:
            PyImGui.text("Enemy Tracker is the scanner and persistence layer.")
            PyImGui.text("Enemy Party owns the visual enemy UI and interaction layer.")
            PyImGui.separator()
            self.draw_scanner_config()

        ImGui.End(EnemyTrackerConfig.MAIN_INI_KEY)

FloatingButton: EnemyTracker | None = None


def _get_shared_vars() -> EnemyTrackerVars | None:
    state = getattr(builtins, ENEMY_TRACKER_SHARED_VARS_ATTR, None)
    return state if state is not None else None


def _set_shared_vars(state: EnemyTrackerVars) -> EnemyTrackerVars:
    setattr(builtins, ENEMY_TRACKER_SHARED_VARS_ATTR, state)
    return state


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


def scanner_main():
    try:
        if not _ensure_ini():
            return
        state = _ensure_state()
        state._poll()
    except Exception as exc:
        Py4GW.Console.Log(EnemyTrackerConfig.MODULE_NAME, f"Scanner error: {exc}", Py4GW.Console.MessageType.Error)
        raise


def configure():
    if not _ensure_ini():
        return
    _ensure_state().draw_scanner_config()


def ui_main():
    try:
        if not _ensure_ini():
            return

        state = _ensure_state()
        state.floating_button.draw(EnemyTrackerConfig.FLOATING_INI_KEY)
    except Exception as exc:
        Py4GW.Console.Log(EnemyTrackerConfig.MODULE_NAME, f"Error: {exc}", Py4GW.Console.MessageType.Error)
        raise


def main():
    scanner_main()


if __name__ == "__main__":
    main()
