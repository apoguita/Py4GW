import json
import os
from dataclasses import dataclass, field

import PyImGui

from HeroAI.call_target import CallTarget
from Py4GWCoreLib import GLOBAL_CACHE, Py4GW, Range, Map
from Py4GWCoreLib.Agent import Agent
from Py4GWCoreLib.AgentArray import AgentArray
from Py4GWCoreLib.ImGui import ImGui
from Py4GWCoreLib.IniManager import IniManager
from Py4GWCoreLib.Player import Player
from Py4GWCoreLib.py4gwcorelib_src.Utils import Utils


@dataclass
class EnemyTrackerConfig:
    MODULE_NAME: str = "Enemy Tracker"
    INI_PATH: str = "Widgets/Automation/Helpers/EnemyTracker"
    MAIN_INI_FILENAME: str = "EnemyTracker.ini"
    FLOATING_INI_FILENAME: str = "EnemyTrackerFloating.ini"
    DATA_FILENAME: str = "EnemyTrackerData.json"

    MAIN_INI_KEY: str = ""
    FLOATING_INI_KEY: str = ""
    INI_INIT: bool = False
    ICON_PATH: str = os.path.join(Py4GW.Console.get_projects_path(), "crossed swords.png")


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
    records: dict[str, dict] = field(default_factory=dict)
    data_dirty: bool = False
    last_save_ms: int = 0
    range_filter: int = 2500
    range_preset_index: int = 0
    sort_index: int = 0
    profession_filter_index: int = 0
    include_dead: bool = False


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
    SORT_OPTIONS = ["Proximity", "Health", "Profession", "Name", "Level"]
    RANGE_PRESETS = [("Manual", None)] + [
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
                self.vars.records = dict(data.get("enemies", {}))
        except Exception as exc:
            Py4GW.Console.Log(EnemyTrackerConfig.MODULE_NAME, f"Failed to load data: {exc}", Py4GW.Console.MessageType.Warning)

    def _save_data_if_needed(self, force: bool = False) -> None:
        if not self.vars.data_dirty and not force:
            return
        now = int(Py4GW.Game.get_tick_count64())
        if not force and now - self.vars.last_save_ms < 2000:
            return
        try:
            payload = {
                "schema": "py4gw_enemy_tracker_v1",
                "enemies": self.vars.records,
            }
            with open(self.data_path, "w", encoding="utf-8") as handle:
                json.dump(payload, handle, indent=2, sort_keys=True)
            self.vars.data_dirty = False
            self.vars.last_save_ms = now
        except Exception as exc:
            Py4GW.Console.Log(EnemyTrackerConfig.MODULE_NAME, f"Failed to save data: {exc}", Py4GW.Console.MessageType.Warning)

    def _enemy_key(self, agent_id: int, name: str, enc_name: str, model_id: int) -> str:
        if enc_name:
            return f"enc:{enc_name}"
        if model_id:
            return f"model:{model_id}:{name}"
        return f"name:{name}"

    def _skill_info(self, skill_id: int) -> tuple[str, int, str]:
        if skill_id <= 0:
            return "", 0, ""
        try:
            skill_name = GLOBAL_CACHE.Skill.GetName(skill_id)
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
                "names": [],
                "encoded_names": [],
                "model_ids": [],
                "observed_skills": {},
                "profession_counts": {},
                "inferred_primary": "",
                "inferred_secondary": "",
                "last_seen": 0,
            }
            self.vars.records[key] = record
            self.vars.data_dirty = True

        if name and name not in record["names"]:
            record["names"].append(name)
            self.vars.data_dirty = True
        if enc_name and enc_name not in record["encoded_names"]:
            record["encoded_names"].append(enc_name)
            self.vars.data_dirty = True
        if model_id and model_id not in record["model_ids"]:
            record["model_ids"].append(model_id)
            self.vars.data_dirty = True
        record["last_seen"] = int(Py4GW.Game.get_tick_count64())
        return record

    def _infer_professions(self, record: dict) -> tuple[str, str]:
        counts = record.get("profession_counts", {})
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
        entry = skills.setdefault(
            skill_key,
            {
                "id": int(skill_id),
                "name": skill_name,
                "profession_id": int(prof_id),
                "profession": prof_name,
                "count": 0,
                "last_seen": 0,
            },
        )
        entry["name"] = skill_name
        entry["profession_id"] = int(prof_id)
        entry["profession"] = prof_name
        entry["count"] = int(entry.get("count", 0)) + 1
        entry["last_seen"] = int(Py4GW.Game.get_tick_count64())
        if prof_name:
            counts = record.setdefault("profession_counts", {})
            counts[prof_name] = int(counts.get(prof_name, 0)) + 1
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
        self.vars.enemy_array = AgentArray.GetEnemyArray()
        for agent_id in self.vars.enemy_array:
            if not Agent.IsValid(agent_id) or not Agent.IsLiving(agent_id):
                continue
            if Agent.IsDead(agent_id) and not self.vars.include_dead:
                continue
            distance = Utils.Distance(player_xy, Agent.GetXY(agent_id))
            if self.vars.range_filter > 0 and distance > self.vars.range_filter:
                continue

            name = Agent.GetNameByID(agent_id) or f"Agent {agent_id}"
            enc_name = Agent.GetEncNameStrByID(agent_id)
            model_id = int(Agent.GetModelID(agent_id) or 0)
            key = self._enemy_key(agent_id, name, enc_name, model_id)
            record = self._ensure_record(key, name, enc_name, model_id)

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

    def _sort_rows(self, rows: list[EnemyLiveState]) -> list[EnemyLiveState]:
        mode = self.SORT_OPTIONS[max(0, min(self.vars.sort_index, len(self.SORT_OPTIONS) - 1))]
        if mode == "Health":
            return sorted(rows, key=lambda row: (row.health, row.distance))
        if mode == "Profession":
            return sorted(rows, key=lambda row: (row.inferred_primary, row.inferred_secondary, row.distance))
        if mode == "Name":
            return sorted(rows, key=lambda row: (row.name, row.distance))
        if mode == "Level":
            return sorted(rows, key=lambda row: (-row.level, row.distance))
        return sorted(rows, key=lambda row: row.distance)

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
        if PyImGui.is_item_hovered():
            PyImGui.begin_tooltip()
            PyImGui.text(f"HP: {int(row.health * 100)}%")
            PyImGui.text(f"Agent: {row.agent_id}")
            PyImGui.text(f"Model: {row.model_id}")
            if row.enc_name:
                PyImGui.text(f"Enc: {row.enc_name}")
            PyImGui.end_tooltip()
        PyImGui.table_next_column()
        PyImGui.text(str(int(row.distance)))
        PyImGui.table_next_column()
        PyImGui.text(",".join(row.statuses)[:18])
        PyImGui.table_next_column()
        PyImGui.text(skill_text[:24])

    def _draw_controls(self) -> None:
        preset_names = [name for name, _ in self.RANGE_PRESETS]
        new_preset = PyImGui.combo("Range Preset", self.vars.range_preset_index, preset_names)
        if new_preset != self.vars.range_preset_index:
            self.vars.range_preset_index = new_preset
            preset_value = self.RANGE_PRESETS[new_preset][1]
            if preset_value is not None:
                self.vars.range_filter = int(preset_value)

        max_range = int(max(float(range_value.value) for range_value in Range))
        new_range = int(ImGui.slider_int("Range", int(self.vars.range_filter), 0, max_range))
        if new_range != self.vars.range_filter:
            self.vars.range_filter = max(0, new_range)
            self._sync_range_preset_from_filter()
        PyImGui.same_line(0, 8)
        self.vars.include_dead = PyImGui.checkbox("Dead", self.vars.include_dead)
        self.vars.sort_index = PyImGui.combo("Sort", self.vars.sort_index, self.SORT_OPTIONS)
        filters = self._profession_filters()
        self.vars.profession_filter_index = PyImGui.combo("Profession", self.vars.profession_filter_index, filters)
        if PyImGui.button("Save Data"):
            self._save_data_if_needed(force=True)
        PyImGui.same_line(0, 8)
        PyImGui.text(f"Known: {len(self.vars.records)}")

    def draw_window(self) -> None:
        expanded, open_ = ImGui.BeginWithClose(
            ini_key=EnemyTrackerConfig.MAIN_INI_KEY,
            name=EnemyTrackerConfig.MODULE_NAME,
            p_open=self.floating_button.visible,
            flags=PyImGui.WindowFlags.NoCollapse,
        )
        self.floating_button.sync_begin_with_close(open_)

        if expanded:
            self._poll()
            self._draw_controls()
            rows = self._filtered_rows()
            PyImGui.text(f"Visible: {len(rows)} / Polled: {len(self.vars.live_rows)}")
            if PyImGui.begin_table(
                "EnemyTrackerRows",
                5,
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
                PyImGui.table_setup_column(
                    "Dist",
                    PyImGui.TableColumnFlags.WidthFixed,
                    60
                )
                PyImGui.table_setup_column(
                    "Status",
                    PyImGui.TableColumnFlags.WidthFixed,
                    90
                )
                PyImGui.table_setup_column(
                    "Casting",
                    PyImGui.TableColumnFlags.WidthFixed,
                    120
                )

                PyImGui.table_headers_row()

                for row in rows:
                    self._draw_row(row)

                PyImGui.end_table()

        ImGui.End(EnemyTrackerConfig.MAIN_INI_KEY)

    def draw_mission_map_range_ring(self) -> None:
        if self.vars.range_filter <= 0 or not Map.MissionMap.IsWindowOpen() or not Player.IsPlayerLoaded():
            return

        left, top, right, bottom = Map.MissionMap.GetMissionMapContentsCoords()
        width = right - left
        height = bottom - top
        if width <= 0 or height <= 0:
            return

        player_x, player_y = Player.GetXY()
        screen_x, screen_y = Map.MissionMap.MapProjection.GameMapToScreen(player_x, player_y)
        radius = Utils.GwinchToPixels(float(self.vars.range_filter))
        if radius <= 0:
            return

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
                outline = Utils.RGBToColor(0, 0, 0, 220)
                segments = 64 if radius >= 220 else 48 if radius >= 130 else 32 if radius >= 70 else 24
                PyImGui.draw_list_add_circle(screen_x, screen_y, radius + 1.0, outline, segments, 2.0)
                PyImGui.draw_list_add_circle(screen_x, screen_y, radius, color, segments, 2.0)
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
        state.draw_mission_map_range_ring()
    except Exception as exc:
        Py4GW.Console.Log(EnemyTrackerConfig.MODULE_NAME, f"Error: {exc}", Py4GW.Console.MessageType.Error)
        raise


if __name__ == "__main__":
    main()
