import json
import os
import time
from typing import List, Optional

import Py4GW
from Py4GWCoreLib import Agent, Color, Console, ConsoleLog, ImGui, Map, Party, Player, PyImGui, Skill

MODULE_NAME = "Balthazar Skill Unlock"
MODULE_ICON = "Textures/Module_Icons/Skill Learner.png"

GREAT_TEMPLE_OF_BALTHAZAR_MAP_ID = 248
PRIEST_OF_BALTHAZAR_MODEL_ID = 218
BALTHAZAR_UNLOCK_DIALOG_MASK = 0x10000000
PVP_REMAP_SENTINEL = 0x0D6C
SEARCH_RESULT_LIMIT = 80
SEND_THROTTLE_SECONDS = 0.4
VERIFY_DELAY_SECONDS = 1.2
VERIFY_TIMEOUT_SECONDS = 5.0


class SkillOption:
    __slots__ = ("skill_id", "name")

    def __init__(self, skill_id: int, name: str) -> None:
        self.skill_id = int(skill_id)
        self.name = str(name or "")

class PendingUnlock:
    __slots__ = (
        "requested_skill_id",
        "send_skill_id",
        "raw_dialog_id",
        "balth_before",
        "unlocked_requested_before",
        "unlocked_send_before",
        "sent_at",
    )

    def __init__(
        self,
        requested_skill_id: int,
        send_skill_id: int,
        raw_dialog_id: int,
        balth_before: int,
        unlocked_requested_before: bool,
        unlocked_send_before: bool,
        sent_at: float,
    ) -> None:
        self.requested_skill_id = int(requested_skill_id)
        self.send_skill_id = int(send_skill_id)
        self.raw_dialog_id = int(raw_dialog_id)
        self.balth_before = int(balth_before)
        self.unlocked_requested_before = bool(unlocked_requested_before)
        self.unlocked_send_before = bool(unlocked_send_before)
        self.sent_at = float(sent_at)


class BalthazarSkillUnlockWidget:
    def __init__(self) -> None:
        self.search_text = ""
        self.manual_skill_id = 0
        self.selected_skill_id = 0
        self.selected_match_index = 0
        self.status_message = "Ready."
        self.use_pvp_remap = True
        self.allow_without_priest_target = False
        self.allow_already_unlocked = False
        self.matches: List[SkillOption] = []
        self.pending_unlock: Optional[PendingUnlock] = None
        self.last_send_time = 0.0
        self.last_search_signature = ""
        self.skill_catalog: List[SkillOption] = []
        self.catalog_error = ""
        self.skill_catalog = self._load_skill_catalog()

    def _candidate_skill_json_paths(self) -> List[str]:
        project_root = str(Py4GW.Console.get_projects_path() or "")
        script_dir = os.path.dirname(globals().get("__file__", MODULE_NAME))
        candidates = []
        if project_root:
            candidates.append(os.path.join(project_root, "Py4GWCoreLib", "skill_descriptions.json"))
        candidates.append(
            os.path.abspath(
                os.path.join(
                    script_dir,
                    "..",
                    "..",
                    "..",
                    "..",
                    "Py4GWCoreLib",
                    "skill_descriptions.json",
                )
            )
        )
        return candidates

    def _load_skill_catalog(self) -> List[SkillOption]:
        for path in self._candidate_skill_json_paths():
            if not os.path.exists(path):
                continue
            try:
                with open(path, encoding="utf-8") as handle:
                    raw = json.load(handle)
            except Exception as exc:
                self.catalog_error = f"Failed to read skill catalog: {exc}"
                return []

            catalog: List[SkillOption] = []
            for key, payload in raw.items():
                try:
                    skill_id = int(key)
                except Exception:
                    continue
                if skill_id <= 0:
                    continue
                if not isinstance(payload, dict):
                    continue
                name = str(payload.get("name", "") or "").strip()
                if not name:
                    continue
                catalog.append(SkillOption(skill_id=skill_id, name=name))

            catalog.sort(key=lambda item: (item.name.lower(), item.skill_id))
            return catalog

        self.catalog_error = "Could not locate Py4GWCoreLib/skill_descriptions.json."
        return []

    def _safe_skill_name(self, skill_id: int) -> str:
        if skill_id <= 0:
            return "None"
        try:
            return str(Skill.GetName(skill_id) or f"Skill {skill_id}")
        except Exception:
            return f"Skill {skill_id}"

    def _parse_search_as_skill_id(self, text: str) -> int:
        value = str(text or "").strip()
        if not value:
            return 0
        try:
            return int(value, 0)
        except Exception:
            return 0

    def _skill_option_by_id(self, skill_id: int) -> Optional[SkillOption]:
        if skill_id <= 0:
            return None
        for item in self.skill_catalog:
            if item.skill_id == skill_id:
                return item
        return None

    def _refresh_matches(self) -> None:
        signature = f"{self.search_text}|{self.selected_skill_id}"
        if signature == self.last_search_signature:
            return
        self.last_search_signature = signature

        query = str(self.search_text or "").strip().lower()
        numeric_id = self._parse_search_as_skill_id(query)
        results: List[SkillOption] = []

        if numeric_id > 0:
            option = self._skill_option_by_id(numeric_id)
            if option is not None:
                results.append(option)
            else:
                results.append(SkillOption(skill_id=numeric_id, name=self._safe_skill_name(numeric_id)))
        elif len(query) >= 2:
            exact_matches: List[SkillOption] = []
            prefix_matches: List[SkillOption] = []
            contains_matches: List[SkillOption] = []
            for item in self.skill_catalog:
                lowered = item.name.lower()
                if lowered == query:
                    exact_matches.append(item)
                elif lowered.startswith(query):
                    prefix_matches.append(item)
                elif query in lowered:
                    contains_matches.append(item)

            results = exact_matches + prefix_matches + contains_matches
            results = results[:SEARCH_RESULT_LIMIT]

        self.matches = results
        if self.matches:
            self.selected_match_index = min(max(self.selected_match_index, 0), len(self.matches) - 1)
        else:
            self.selected_match_index = 0

    def _current_balthazar_points(self) -> int:
        try:
            current_balth, _, _ = Player.GetBalthazarData()
            return int(current_balth or 0)
        except Exception:
            return 0

    def _skill_is_unlocked(self, skill_id: int) -> bool:
        if skill_id <= 0:
            return False
        try:
            masks = Player.GetUnlockedCharacterSkills() or []
        except Exception:
            return False
        index = skill_id // 32
        bit = skill_id % 32
        if index < 0 or index >= len(masks):
            return False
        return bool((int(masks[index]) >> bit) & 1)

    def _normalize_send_skill_id(self, skill_id: int) -> int:
        resolved = int(skill_id or 0)
        if resolved <= 0:
            return 0
        if not self.use_pvp_remap:
            return resolved
        try:
            pvp_id = int(Skill.ExtraData.GetIDPvP(resolved) or 0)
        except Exception:
            pvp_id = 0
        if pvp_id == PVP_REMAP_SENTINEL:
            return resolved
        if pvp_id > 0 and pvp_id != resolved:
            return pvp_id
        return resolved

    def _estimated_unlock_cost(self, skill_id: int) -> int:
        try:
            return 3000 if bool(Skill.Flags.IsElite(skill_id)) else 1000
        except Exception:
            return 0

    def _target_summary(self) -> tuple[int, str, int]:
        target_id = int(Player.GetTargetID() or 0)
        if target_id <= 0:
            return 0, "No current target", 0

        try:
            target_name = str(Agent.GetNameByID(target_id) or f"Target {target_id}")
        except Exception:
            target_name = f"Target {target_id}"
        try:
            model_id = int(Agent.GetModelID(target_id) or 0)
        except Exception:
            model_id = 0
        return target_id, target_name, model_id

    def _select_match(self, option: SkillOption) -> None:
        self.selected_skill_id = int(option.skill_id)
        self.manual_skill_id = int(option.skill_id)
        self.status_message = f"Selected {option.name} [{option.skill_id}]."

    def _send_unlock_request(self) -> None:
        selected_skill_id = int(self.selected_skill_id or 0)
        if selected_skill_id <= 0:
            self.status_message = "Select a skill from search results or enter a manual skill ID."
            return

        now = time.monotonic()
        if (now - self.last_send_time) < SEND_THROTTLE_SECONDS:
            self.status_message = "Send throttled. Wait a moment before sending another unlock request."
            return

        target_id, target_name, model_id = self._target_summary()
        if not self.allow_without_priest_target and model_id != PRIEST_OF_BALTHAZAR_MODEL_ID:
            self.status_message = (
                f"Current target is {target_name} (model {model_id}), not Priest of Balthazar "
                f"({PRIEST_OF_BALTHAZAR_MODEL_ID}). Enable override to send anyway."
            )
            return

        send_skill_id = self._normalize_send_skill_id(selected_skill_id)
        if send_skill_id <= 0:
            self.status_message = "Could not resolve a valid send skill ID."
            return

        unlocked_requested = self._skill_is_unlocked(selected_skill_id)
        unlocked_send = self._skill_is_unlocked(send_skill_id)
        if (unlocked_requested or unlocked_send) and not self.allow_already_unlocked:
            self.status_message = "Selected skill already appears unlocked. Enable override to send anyway."
            return

        raw_dialog_id = BALTHAZAR_UNLOCK_DIALOG_MASK | (send_skill_id & 0xFFFF)
        balth_before = self._current_balthazar_points()
        Player.SendRawDialog(raw_dialog_id)
        self.last_send_time = now
        self.pending_unlock = PendingUnlock(
            requested_skill_id=selected_skill_id,
            send_skill_id=send_skill_id,
            raw_dialog_id=raw_dialog_id,
            balth_before=balth_before,
            unlocked_requested_before=unlocked_requested,
            unlocked_send_before=unlocked_send,
            sent_at=now,
        )
        self.status_message = (
            f"Sent unlock request for {self._safe_skill_name(selected_skill_id)} "
            f"using raw dialog 0x{raw_dialog_id:08X}."
        )
        ConsoleLog(
            MODULE_NAME,
            (
                f"Sent Balthazar unlock request target_id={target_id} model_id={model_id} "
                f"requested_skill_id={selected_skill_id} send_skill_id={send_skill_id} "
                f"raw_dialog=0x{raw_dialog_id:08X}"
            ),
            Console.MessageType.Info,
        )

    def _update_pending_unlock(self) -> None:
        pending = self.pending_unlock
        if pending is None:
            return

        elapsed = time.monotonic() - pending.sent_at
        if elapsed < VERIFY_DELAY_SECONDS:
            return

        unlocked_requested_now = self._skill_is_unlocked(pending.requested_skill_id)
        unlocked_send_now = self._skill_is_unlocked(pending.send_skill_id)
        balth_now = self._current_balthazar_points()

        if (
            (not pending.unlocked_requested_before and unlocked_requested_now)
            or (not pending.unlocked_send_before and unlocked_send_now)
        ):
            self.status_message = (
                f"Verified unlock for {self._safe_skill_name(pending.requested_skill_id)}. "
                f"Balthazar faction: {pending.balth_before} -> {balth_now}."
            )
            self.pending_unlock = None
            return

        if balth_now < pending.balth_before:
            self.status_message = (
                f"Faction decreased after send ({pending.balth_before} -> {balth_now}) "
                f"for {self._safe_skill_name(pending.requested_skill_id)}. "
                "Unlock likely succeeded, but the bitmask has not been observed yet."
            )
            self.pending_unlock = None
            return

        if elapsed >= VERIFY_TIMEOUT_SECONDS:
            self.status_message = (
                f"Sent 0x{pending.raw_dialog_id:08X} for {self._safe_skill_name(pending.requested_skill_id)}, "
                "but no unlock/faction change was verified."
            )
            self.pending_unlock = None

    def update(self) -> None:
        self._refresh_matches()
        self._update_pending_unlock()

    def _recent_dialog_journal_entries(self) -> List[object]:
        dialog_api = getattr(Py4GW, "Dialog", None)
        if dialog_api is None:
            return []

        getter = getattr(dialog_api, "get_dialog_callback_journal_sent", None)
        if getter is None:
            return []

        try:
            return list(getter() or [])[-5:]
        except Exception:
            return []

    def _draw_status_panel(self) -> None:
        current_map_id = int(Map.GetMapID() or 0)
        current_map_name = str(Map.GetMapName(current_map_id) or "Unknown")
        current_balth = self._current_balthazar_points()
        target_id, target_name, model_id = self._target_summary()
        priest_ok = model_id == PRIEST_OF_BALTHAZAR_MODEL_ID
        map_ok = current_map_id == GREAT_TEMPLE_OF_BALTHAZAR_MAP_ID

        PyImGui.text(f"Map: {current_map_name} ({current_map_id})")
        PyImGui.text_colored(
            f"Target: {target_name} [{target_id}] | model {model_id}",
            (0.6, 1.0, 0.6, 1.0) if priest_ok else (1.0, 0.8, 0.4, 1.0),
        )
        PyImGui.text(f"Current Balthazar faction: {current_balth}")
        if not map_ok:
            PyImGui.text_colored(
                f"Warning: expected map {GREAT_TEMPLE_OF_BALTHAZAR_MAP_ID} for Great Temple of Balthazar.",
                (1.0, 0.8, 0.4, 1.0),
            )
        if PyImGui.button("Travel to GToB"):
            Map.Travel(GREAT_TEMPLE_OF_BALTHAZAR_MAP_ID)

    def _draw_search_panel(self) -> None:
        new_search = str(PyImGui.input_text("Search Skill", self.search_text, 128))
        if new_search != self.search_text:
            self.search_text = new_search
            self.last_search_signature = ""

        self.manual_skill_id = int(PyImGui.input_int("Manual Skill ID", int(self.manual_skill_id or 0)))
        if PyImGui.button("Use Manual ID"):
            self.selected_skill_id = int(self.manual_skill_id or 0)
            self.status_message = f"Selected manual skill ID {self.selected_skill_id}."
        PyImGui.same_line(0.0, -1.0)
        if PyImGui.button("Clear Selection"):
            self.selected_skill_id = 0
            self.manual_skill_id = 0
            self.status_message = "Cleared selected skill."

        PyImGui.separator()
        if not self.matches:
            PyImGui.text("Type at least 2 characters to search, or enter a skill ID.")
            return

        if PyImGui.begin_child("BalthazarSkillMatches", (0, 220), True, PyImGui.WindowFlags.NoFlag):
            for index, option in enumerate(self.matches):
                label = f"{option.name} [{option.skill_id}]"
                is_selected = int(option.skill_id) == int(self.selected_skill_id or 0)
                if PyImGui.selectable(f"{label}##balth_skill_{index}", is_selected, PyImGui.SelectableFlags.NoFlag, (0, 0)):
                    self._select_match(option)
            PyImGui.end_child()

    def _draw_selected_skill_panel(self) -> None:
        selected_skill_id = int(self.selected_skill_id or 0)
        if selected_skill_id <= 0:
            PyImGui.text("No skill selected.")
            return

        selected_name = self._safe_skill_name(selected_skill_id)
        send_skill_id = self._normalize_send_skill_id(selected_skill_id)
        raw_dialog_id = BALTHAZAR_UNLOCK_DIALOG_MASK | (send_skill_id & 0xFFFF)
        requested_unlocked = self._skill_is_unlocked(selected_skill_id)
        send_unlocked = self._skill_is_unlocked(send_skill_id)
        estimated_cost = self._estimated_unlock_cost(selected_skill_id)

        try:
            _, profession_name = Skill.GetProfession(selected_skill_id)
        except Exception:
            profession_name = "Unknown"
        try:
            _, campaign_name = Skill.GetCampaign(selected_skill_id)
        except Exception:
            campaign_name = "Unknown"
        try:
            _, type_name = Skill.GetType(selected_skill_id)
        except Exception:
            type_name = "Unknown"
        try:
            concise = str(Skill.GetConciseDescription(selected_skill_id) or "")
        except Exception:
            concise = ""

        try:
            is_pvp = bool(Skill.Flags.IsPvP(selected_skill_id))
        except Exception:
            is_pvp = False
        try:
            is_playable = bool(Skill.Flags.IsPlayable(selected_skill_id))
        except Exception:
            is_playable = False
        try:
            is_elite = bool(Skill.Flags.IsElite(selected_skill_id))
        except Exception:
            is_elite = False

        PyImGui.text(f"Selected: {selected_name}")
        PyImGui.text(f"Skill ID: {selected_skill_id}")
        PyImGui.text(f"Profession: {profession_name} | Campaign: {campaign_name} | Type: {type_name}")
        PyImGui.text(f"Playable: {is_playable} | PvP skill: {is_pvp} | Elite: {is_elite}")
        PyImGui.text(f"Estimated unlock cost: {estimated_cost if estimated_cost > 0 else 'Unknown'}")
        PyImGui.text(
            f"Send skill ID: {send_skill_id} | Raw dialog: 0x{raw_dialog_id:08X}"
        )
        PyImGui.text(
            f"Unlocked bitmask: requested={requested_unlocked} | send-id={send_unlocked}"
        )
        if concise:
            PyImGui.separator()
            PyImGui.text_wrapped(concise)
            PyImGui.separator()

        self.use_pvp_remap = bool(
            PyImGui.checkbox("Use PvP remap when Skill.ExtraData.GetIDPvP(...) differs", self.use_pvp_remap)
        )
        self.allow_without_priest_target = bool(
            PyImGui.checkbox("Allow send without Priest of Balthazar target", self.allow_without_priest_target)
        )
        self.allow_already_unlocked = bool(
            PyImGui.checkbox("Allow send even if the skill already looks unlocked", self.allow_already_unlocked)
        )

        if PyImGui.button("Unlock Selected Skill"):
            self._send_unlock_request()

    def _draw_diagnostics(self) -> None:
        if not PyImGui.collapsing_header("Diagnostics"):
            return

        if self.catalog_error:
            PyImGui.text_wrapped(f"Catalog error: {self.catalog_error}")

        pending = self.pending_unlock
        if pending is None:
            PyImGui.text("Pending unlock: none")
        else:
            elapsed = time.monotonic() - pending.sent_at
            PyImGui.text(
                f"Pending unlock: {self._safe_skill_name(pending.requested_skill_id)} "
                f"| raw=0x{pending.raw_dialog_id:08X} | elapsed={elapsed:.2f}s"
            )

        sent_entries = self._recent_dialog_journal_entries()

        if sent_entries:
            PyImGui.separator()
            PyImGui.text("Recent sent dialog journal entries:")
            for entry in reversed(sent_entries):
                event_type = str(getattr(entry, "event_type", "") or "?")
                dialog_id = int(getattr(entry, "dialog_id", 0) or 0)
                agent_id = int(getattr(entry, "agent_id", 0) or 0)
                PyImGui.text(f"{event_type} | dialog=0x{dialog_id:08X} | agent={agent_id}")

    def draw(self) -> None:
        if PyImGui.begin(MODULE_NAME):
            PyImGui.text_wrapped(
                "Python-side prototype for the Priest of Balthazar skill-unlock vendor. "
                "Select a skill, confirm the current target, and send the Balthazar unlock dialog family."
            )
            PyImGui.separator()

            if not Map.IsMapReady() or not Party.IsPartyLoaded():
                PyImGui.text("Waiting for map and party readiness.")
            else:
                self._draw_status_panel()
                PyImGui.separator()
                self._draw_search_panel()
                PyImGui.separator()
                self._draw_selected_skill_panel()

            PyImGui.separator()
            PyImGui.text_wrapped(self.status_message)
            self._draw_diagnostics()
        PyImGui.end()


def tooltip() -> None:
    PyImGui.begin_tooltip()
    title_color = Color(255, 200, 100, 255)
    ImGui.push_font("Regular", 20)
    PyImGui.text_colored(MODULE_NAME, title_color.to_tuple_normalized())
    ImGui.pop_font()
    PyImGui.separator()
    PyImGui.text("Search or enter a skill ID, then send the Balthazar unlock dialog.")
    PyImGui.text("The helper verifies result by watching unlocked-skill bits and Balthazar faction.")
    PyImGui.text("It uses Player.SendRawDialog() through the approved UI message path.")
    PyImGui.end_tooltip()


_widget = BalthazarSkillUnlockWidget()


def main() -> None:
    _widget.update()
    _widget.draw()


if __name__ == "__main__":
    main()
