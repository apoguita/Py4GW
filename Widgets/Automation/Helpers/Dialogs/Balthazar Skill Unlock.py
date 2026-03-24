from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from typing import List, Optional

import Py4GW

from Py4GWCoreLib import Agent, Color, Console, ConsoleLog, Dialog, ImGui, Map, Party, Player, PyImGui, Skill, Utils

MODULE_NAME = "Balthazar Skill Unlock"
MODULE_ICON = "Textures/Module_Icons/Skill Learner.png"

GREAT_TEMPLE_OF_BALTHAZAR_MAP_ID = 248
PRIEST_OF_BALTHAZAR_MODEL_ID = 218
DEFAULT_SEARCH_RESULT_LIMIT = 80
SEARCH_RESULT_LIMIT = DEFAULT_SEARCH_RESULT_LIMIT
SEND_THROTTLE_SECONDS = 0.4
VERIFY_DELAY_SECONDS = 1.2
VERIFY_TIMEOUT_SECONDS = 5.0


@dataclass(frozen=True)
class _SkillOption:
    skill_id: int
    name: str


@dataclass(frozen=True)
class _BalthazarTargetSummary:
    target_id: int
    target_name: str
    model_id: int


@dataclass
class _BalthazarSkillUnlockAttempt:
    requested_skill_id: int
    requested_skill_name: str
    send_skill_id: int
    raw_dialog_id: int
    target_id: int
    target_name: str
    target_model_id: int
    estimated_unlock_cost: int
    balthazar_points_before: int
    unlocked_requested_before: bool
    unlocked_send_before: bool
    sent_at: float = 0.0


@dataclass(frozen=True)
class _BalthazarSkillUnlockResult:
    ok: bool
    message: str
    attempt: Optional[_BalthazarSkillUnlockAttempt] = None


@dataclass(frozen=True)
class _BalthazarSkillUnlockVerification:
    complete: bool
    success: bool
    message: str
    elapsed_seconds: float
    balthazar_points_now: int
    unlocked_requested_now: bool
    unlocked_send_now: bool


def _candidate_skill_json_paths() -> List[str]:
    project_root = str(Py4GW.Console.get_projects_path() or "")
    candidates = []
    if project_root:
        candidates.append(os.path.join(project_root, "Py4GWCoreLib", "skill_descriptions.json"))
    candidates.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "Py4GWCoreLib", "skill_descriptions.json")))
    return candidates


def _parse_search_as_skill_id(query: str) -> int:
    value = str(query or "").strip()
    if not value:
        return 0
    try:
        return int(value, 0)
    except Exception:
        return 0


def _load_skill_catalog() -> tuple[List[_SkillOption], str]:
    for path in _candidate_skill_json_paths():
        if not os.path.exists(path):
            continue
        try:
            with open(path, encoding="utf-8") as handle:
                raw = json.load(handle)
        except Exception as exc:
            return [], f"Failed to read skill catalog: {exc}"

        catalog: List[_SkillOption] = []
        for key, payload in raw.items():
            try:
                skill_id = int(key)
            except Exception:
                continue
            if skill_id <= 0 or not isinstance(payload, dict):
                continue
            name = str(payload.get("name", "") or "").strip()
            if not name:
                continue
            catalog.append(_SkillOption(skill_id=skill_id, name=name))

        catalog.sort(key=lambda item: (item.name.lower(), item.skill_id))
        return catalog, ""

    return [], "Could not locate Py4GWCoreLib/skill_descriptions.json."


def _get_skill_option(skill_id: int, catalog_by_id: Optional[dict[int, _SkillOption]] = None) -> Optional[_SkillOption]:
    if catalog_by_id is None:
        return None
    return catalog_by_id.get(int(skill_id or 0))


def _get_skill_name(skill_id: int, catalog_by_id: Optional[dict[int, _SkillOption]] = None) -> str:
    resolved = int(skill_id or 0)
    if resolved <= 0:
        return "None"

    option = _get_skill_option(resolved, catalog_by_id)
    if option is not None:
        return option.name

    try:
        return str(Skill.GetName(resolved) or f"Skill {resolved}")
    except Exception:
        return f"Skill {resolved}"


def _search_skill_catalog(
    query: str,
    catalog: List[_SkillOption],
    catalog_by_id: dict[int, _SkillOption],
    limit: int = DEFAULT_SEARCH_RESULT_LIMIT,
) -> List[_SkillOption]:
    query_text = str(query or "").strip()
    if not query_text:
        return []

    numeric_id = _parse_search_as_skill_id(query_text)
    if numeric_id > 0:
        option = _get_skill_option(numeric_id, catalog_by_id)
        if option is not None:
            return [option]
        return [_SkillOption(skill_id=numeric_id, name=_get_skill_name(numeric_id, catalog_by_id))]

    if len(query_text) < 2:
        return []

    query_lower = query_text.lower()
    exact_matches: List[_SkillOption] = []
    prefix_matches: List[_SkillOption] = []
    contains_matches: List[_SkillOption] = []

    for item in catalog:
        lowered = item.name.lower()
        if lowered == query_lower:
            exact_matches.append(item)
        elif lowered.startswith(query_lower):
            prefix_matches.append(item)
        elif query_lower in lowered:
            contains_matches.append(item)

    results = exact_matches + prefix_matches + contains_matches
    return results[: max(0, int(limit or 0))]


def _get_current_balthazar_points() -> int:
    try:
        current_balth, _, _ = Player.GetBalthazarData()
        return int(current_balth or 0)
    except Exception:
        return 0


def _is_skill_unlocked(skill_id: int) -> bool:
    resolved = int(skill_id or 0)
    if resolved <= 0:
        return False
    try:
        masks = Player.GetUnlockedCharacterSkills() or []
    except Exception:
        return False
    index = resolved // 32
    bit = resolved % 32
    if index < 0 or index >= len(masks):
        return False
    return bool((int(masks[index]) >> bit) & 1)


def _build_raw_dialog_id(skill_id: int, use_pvp_remap: bool = True) -> int:
    return int(Utils.BalthazarSkillIdToDialogId(int(skill_id or 0), use_pvp_remap=use_pvp_remap) or 0)


def _resolve_send_skill_id(skill_id: int, use_pvp_remap: bool = True) -> int:
    raw_dialog_id = _build_raw_dialog_id(skill_id, use_pvp_remap=use_pvp_remap)
    if raw_dialog_id <= 0:
        return 0
    return int(raw_dialog_id & 0xFFFF)


def _estimated_unlock_cost(skill_id: int) -> int:
    try:
        return 3000 if bool(Skill.Flags.IsElite(skill_id)) else 1000
    except Exception:
        return 0


def _get_target_summary(target_id: int = 0) -> _BalthazarTargetSummary:
    resolved_target_id = int(target_id or Player.GetTargetID() or 0)
    if resolved_target_id <= 0:
        return _BalthazarTargetSummary(target_id=0, target_name="No current target", model_id=0)

    try:
        target_name = str(Agent.GetNameByID(resolved_target_id) or f"Target {resolved_target_id}")
    except Exception:
        target_name = f"Target {resolved_target_id}"
    try:
        model_id = int(Agent.GetModelID(resolved_target_id) or 0)
    except Exception:
        model_id = 0
    return _BalthazarTargetSummary(
        target_id=resolved_target_id,
        target_name=target_name,
        model_id=model_id,
    )


def _build_unlock_attempt(
    skill_id: int,
    *,
    target_id: int = 0,
    use_pvp_remap: bool = True,
    require_priest_target: bool = True,
    allow_already_unlocked: bool = False,
) -> _BalthazarSkillUnlockResult:
    requested_skill_id = int(skill_id or 0)
    if requested_skill_id <= 0:
        return _BalthazarSkillUnlockResult(
            ok=False,
            message="Select a valid skill ID before sending an unlock request.",
        )

    target = _get_target_summary(target_id)
    if require_priest_target and target.model_id != PRIEST_OF_BALTHAZAR_MODEL_ID:
        return _BalthazarSkillUnlockResult(
            ok=False,
            message=(
                f"Current target is {target.target_name} (model {target.model_id}), not Priest of Balthazar "
                f"({PRIEST_OF_BALTHAZAR_MODEL_ID})."
            ),
        )

    raw_dialog_id = _build_raw_dialog_id(requested_skill_id, use_pvp_remap=use_pvp_remap)
    send_skill_id = _resolve_send_skill_id(requested_skill_id, use_pvp_remap=use_pvp_remap)
    if raw_dialog_id <= 0 or send_skill_id <= 0:
        return _BalthazarSkillUnlockResult(
            ok=False,
            message="Could not resolve a valid Balthazar send skill ID.",
        )

    unlocked_requested = _is_skill_unlocked(requested_skill_id)
    unlocked_send = _is_skill_unlocked(send_skill_id)
    if (unlocked_requested or unlocked_send) and not allow_already_unlocked:
        return _BalthazarSkillUnlockResult(
            ok=False,
            message="Selected skill already appears unlocked. Enable override to send anyway.",
        )

    attempt = _BalthazarSkillUnlockAttempt(
        requested_skill_id=requested_skill_id,
        requested_skill_name=_get_skill_name(requested_skill_id),
        send_skill_id=send_skill_id,
        raw_dialog_id=raw_dialog_id,
        target_id=target.target_id,
        target_name=target.target_name,
        target_model_id=target.model_id,
        estimated_unlock_cost=_estimated_unlock_cost(requested_skill_id),
        balthazar_points_before=_get_current_balthazar_points(),
        unlocked_requested_before=unlocked_requested,
        unlocked_send_before=unlocked_send,
    )
    return _BalthazarSkillUnlockResult(
        ok=True,
        message=(
            f"Prepared Balthazar unlock for {attempt.requested_skill_name} "
            f"using raw dialog 0x{attempt.raw_dialog_id:08X}."
        ),
        attempt=attempt,
    )


def _verify_unlock_attempt(
    attempt: _BalthazarSkillUnlockAttempt,
    *,
    verify_delay_seconds: float = 0.0,
    verify_timeout_seconds: Optional[float] = None,
) -> _BalthazarSkillUnlockVerification:
    elapsed = max(0.0, time.monotonic() - float(attempt.sent_at or 0.0))
    unlocked_requested_now = _is_skill_unlocked(attempt.requested_skill_id)
    unlocked_send_now = _is_skill_unlocked(attempt.send_skill_id)
    balthazar_points_now = _get_current_balthazar_points()

    if elapsed < verify_delay_seconds:
        return _BalthazarSkillUnlockVerification(
            complete=False,
            success=False,
            message=(
                f"Waiting to verify {attempt.requested_skill_name} "
                f"({elapsed:.2f}s < {verify_delay_seconds:.2f}s)."
            ),
            elapsed_seconds=elapsed,
            balthazar_points_now=balthazar_points_now,
            unlocked_requested_now=unlocked_requested_now,
            unlocked_send_now=unlocked_send_now,
        )

    if (
        (not attempt.unlocked_requested_before and unlocked_requested_now)
        or (not attempt.unlocked_send_before and unlocked_send_now)
    ):
        return _BalthazarSkillUnlockVerification(
            complete=True,
            success=True,
            message=(
                f"Verified unlock for {attempt.requested_skill_name}. "
                f"Balthazar faction: {attempt.balthazar_points_before} -> {balthazar_points_now}."
            ),
            elapsed_seconds=elapsed,
            balthazar_points_now=balthazar_points_now,
            unlocked_requested_now=unlocked_requested_now,
            unlocked_send_now=unlocked_send_now,
        )

    if balthazar_points_now < attempt.balthazar_points_before:
        return _BalthazarSkillUnlockVerification(
            complete=True,
            success=True,
            message=(
                f"Faction decreased after send ({attempt.balthazar_points_before} -> {balthazar_points_now}) "
                f"for {attempt.requested_skill_name}. Unlock likely succeeded, but the bitmask has not been observed yet."
            ),
            elapsed_seconds=elapsed,
            balthazar_points_now=balthazar_points_now,
            unlocked_requested_now=unlocked_requested_now,
            unlocked_send_now=unlocked_send_now,
        )

    if verify_timeout_seconds is not None and elapsed >= verify_timeout_seconds:
        return _BalthazarSkillUnlockVerification(
            complete=True,
            success=False,
            message=(
                f"Sent 0x{attempt.raw_dialog_id:08X} for {attempt.requested_skill_name}, "
                "but no unlock or faction change was verified."
            ),
            elapsed_seconds=elapsed,
            balthazar_points_now=balthazar_points_now,
            unlocked_requested_now=unlocked_requested_now,
            unlocked_send_now=unlocked_send_now,
        )

    return _BalthazarSkillUnlockVerification(
        complete=False,
        success=False,
        message=f"Unlock request still pending for {attempt.requested_skill_name}.",
        elapsed_seconds=elapsed,
        balthazar_points_now=balthazar_points_now,
        unlocked_requested_now=unlocked_requested_now,
        unlocked_send_now=unlocked_send_now,
    )


class BalthazarSkillUnlockWidget:
    def __init__(self) -> None:
        self.catalog_error = ""
        self.skill_catalog: List[_SkillOption] = []
        self.skill_catalog_by_id: dict[int, _SkillOption] = {}
        self.search_text = ""
        self.manual_skill_id = 0
        self.selected_skill_id = 0
        self.selected_match_index = 0
        self.status_message = "Ready."
        self.use_pvp_remap = True
        self.allow_without_priest_target = False
        self.allow_already_unlocked = False
        self.matches: List[_SkillOption] = []
        self.pending_unlock: Optional[_BalthazarSkillUnlockAttempt] = None
        self.last_send_time = 0.0
        self.last_search_signature = ""
        self.refresh_skill_catalog()

    def refresh_skill_catalog(self) -> None:
        self.skill_catalog, self.catalog_error = _load_skill_catalog()
        self.skill_catalog_by_id = {item.skill_id: item for item in self.skill_catalog}

    def _refresh_matches(self) -> None:
        signature = self.search_text
        if signature == self.last_search_signature:
            return
        self.last_search_signature = signature
        self.matches = _search_skill_catalog(
            self.search_text,
            self.skill_catalog,
            self.skill_catalog_by_id,
            limit=SEARCH_RESULT_LIMIT,
        )
        if self.matches:
            self.selected_match_index = min(max(self.selected_match_index, 0), len(self.matches) - 1)
        else:
            self.selected_match_index = 0

    def _skill_name(self, skill_id: int) -> str:
        return _get_skill_name(skill_id, self.skill_catalog_by_id)

    def _current_balthazar_points(self) -> int:
        return _get_current_balthazar_points()

    def _skill_is_unlocked(self, skill_id: int) -> bool:
        return _is_skill_unlocked(skill_id)

    def _resolve_send_skill_id(self, skill_id: int) -> int:
        return _resolve_send_skill_id(skill_id, use_pvp_remap=self.use_pvp_remap)

    def _build_raw_dialog_id(self, skill_id: int) -> int:
        return _build_raw_dialog_id(skill_id, use_pvp_remap=self.use_pvp_remap)

    def _estimated_unlock_cost(self, skill_id: int) -> int:
        return _estimated_unlock_cost(skill_id)

    def _target_summary(self) -> tuple[int, str, int]:
        target = _get_target_summary()
        return target.target_id, target.target_name, target.model_id

    def _select_match(self, option: _SkillOption) -> None:
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

        prepared = _build_unlock_attempt(
            selected_skill_id,
            use_pvp_remap=self.use_pvp_remap,
            require_priest_target=not self.allow_without_priest_target,
            allow_already_unlocked=self.allow_already_unlocked,
        )
        self.status_message = prepared.message
        if not prepared.ok or prepared.attempt is None:
            return

        attempt = prepared.attempt
        Player.UnlockBalthazarSkill(selected_skill_id, use_pvp_remap=self.use_pvp_remap)
        attempt.sent_at = now
        self.last_send_time = now
        self.pending_unlock = attempt
        self.status_message = (
            f"Queued unlock request for {attempt.requested_skill_name} "
            f"using raw dialog 0x{attempt.raw_dialog_id:08X}."
        )
        ConsoleLog(
            MODULE_NAME,
            (
                f"Queued Balthazar unlock request target_id={attempt.target_id} "
                f"model_id={attempt.target_model_id} requested_skill_id={attempt.requested_skill_id} "
                f"send_skill_id={attempt.send_skill_id} raw_dialog=0x{attempt.raw_dialog_id:08X}"
            ),
            Console.MessageType.Info,
        )

    def _update_pending_unlock(self) -> None:
        pending = self.pending_unlock
        if pending is None:
            return

        verification = _verify_unlock_attempt(
            pending,
            verify_delay_seconds=VERIFY_DELAY_SECONDS,
            verify_timeout_seconds=VERIFY_TIMEOUT_SECONDS,
        )
        if verification.complete:
            self.status_message = verification.message
            self.pending_unlock = None

    def update(self) -> None:
        self._refresh_matches()
        self._update_pending_unlock()

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

        selected_name = self._skill_name(selected_skill_id)
        send_skill_id = self._resolve_send_skill_id(selected_skill_id)
        raw_dialog_id = self._build_raw_dialog_id(selected_skill_id)
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
        PyImGui.text(f"Send skill ID: {send_skill_id} | Raw dialog: 0x{raw_dialog_id:08X}")
        PyImGui.text(f"Unlocked bitmask: requested={requested_unlocked} | send-id={send_unlocked}")
        if concise:
            PyImGui.separator()
            PyImGui.text_wrapped(concise)
            PyImGui.separator()

        self.use_pvp_remap = bool(
            PyImGui.checkbox("Use Balthazar vendor skill PvP ID remap", self.use_pvp_remap)
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
                f"Pending unlock: {pending.requested_skill_name} "
                f"| raw=0x{pending.raw_dialog_id:08X} | elapsed={elapsed:.2f}s"
            )

        try:
            sent_entries = Dialog.get_dialog_callback_journal_sent()[-5:]
        except Exception:
            sent_entries = []

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
                "Widget-owned Balthazar unlock workflow over the low-level Player/Utils primitives. "
                "Select a skill, confirm the current target, and queue the vendor raw dialog family."
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
    PyImGui.text("Verification watches unlocked-skill bits and Balthazar faction after send.")
    PyImGui.text("Low-level primitives: Player.UnlockBalthazarSkill(...) and Utils.BalthazarSkillIdToDialogId(...).")
    PyImGui.end_tooltip()


_widget = BalthazarSkillUnlockWidget()


def main() -> None:
    _widget.update()
    _widget.draw()


if __name__ == "__main__":
    main()
