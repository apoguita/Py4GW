"""Prophecies campaign chain (missions + primary quests)."""

import os

import Py4GW
import PyImGui

from Sources.modular_bot import ModularBot
from Sources.modular_bot.hero_setup import draw_setup_tab
from Sources.modular_bot.phase import Phase
from Sources.modular_bot.recipes import Mission, Quest


def _project_root() -> str:
    try:
        root = str(Py4GW.Console.get_projects_path() or "").strip()
    except Exception:
        root = ""
    if not root:
        root = os.getcwd()
    return os.path.normpath(root)


# PHASE_SPECS tuple format:
# (region, kind, key, title)
# - region: UI grouping bucket (collapsible section / "Start here" range).
# - kind: "mission" or "quest" (selects Mission(...) vs Quest(...) recipe loader).
# - key: JSON file key under Sources/modular_bot/{missions|quests}/<key>.json.
# - title: Human-readable phase label shown in the campaign UI and phase names.
PHASE_SPECS: list[tuple[str, str, str, str]] = [
    ("Ascalon", "mission", "the_great_northern_wall", "The Great Northern Wall"),
    ("Ascalon", "mission", "fort_ranik", "Fort Ranik"),
    ("Ascalon", "quest", "ruins_of_surmia", "Ruins of Surmia"),
    ("Ascalon", "mission", "ruins_of_surmia", "Ruins of Surmia"),
    ("Northern Shiverpeaks", "mission", "nolani_academy", "Nolani Academy"),
    ("Northern Shiverpeaks", "quest", "the_way_is_blocked", "The Way Is Blocked"),
    ("Northern Shiverpeaks", "mission", "borlis_pass", "Borlis Pass"),
    ("Kryta", "mission", "the_frost_gate", "The Frost Gate"),
    ("Kryta", "quest", "to_kryta_refugees", "To Kryta: Refugees"),
    ("Kryta", "quest", "to_kryta_the_ice_cave", "To Kryta: The Ice Cave"),
    ("Kryta", "quest", "to_kryta_the_journey_end", "To Kryta: Journey's End"),
    ("Kryta", "mission", "gates_of_kryta", "Gates of Kryta"),
    ("Kryta", "quest", "report_to_the_white_mantle", "Report to the White Mantle"),
    ("Kryta", "mission", "d_alessio_seaboard", "D'Alessio Seaboard"),
    ("Maguuma Jungle", "mission", "divinity_coast", "Divinity Coast"),
    ("Maguuma Jungle", "quest", "a_brothers_fury", "A Brother's Fury"),
    ("Maguuma Jungle", "mission", "the_wilds", "The Wilds"),
    ("Maguuma Jungle", "mission", "bloodstone_fen", "Bloodstone Fen"),
    ("Maguuma Jungle", "quest", "white_mantle_wrath_demagogue_vanguard", "White Mantle Wrath: Demagogue's Vanguard"),
    ("Maguuma Jungle", "quest", "urgent_warning", "Urgent Warning"),
    ("Maguuma Jungle", "mission", "aurora_glade", "Aurora Glade"),
    ("Kryta Extended", "quest", "passage_through_the_dark_river", "Passage Through The Dark River"),
    ("Kryta Extended", "mission", "riverside_province", "Riverside Province"),
    ("Kryta Extended", "mission", "sanctum_cay", "Sanctum Cay"),
]
REGION_IDX = 0
KIND_IDX = 1
KEY_IDX = 2
TITLE_IDX = 3

start_phase_index = 0
show_all_regions = False
_validation_issues: list[str] = []
_last_jump_message = ""


def _build_phases_from_specs(specs: list[tuple[str, str, str, str]]) -> list[Phase]:
    phases: list[Phase] = []
    for idx, spec in enumerate(specs):
        kind = spec[KIND_IDX]
        key = spec[KEY_IDX]
        title = spec[TITLE_IDX]
        pretty_name = f"{idx + 1:02d}. {kind.title()}: {title}"
        phase = Mission(key, pretty_name) if kind == "mission" else Quest(key, pretty_name)
        phases.append(phase)
    return phases


PHASE_DEFS: list[Phase] = _build_phases_from_specs(PHASE_SPECS)


def _derive_region_spans(specs: list[tuple[str, str, str, str]]) -> list[tuple[str, int, int]]:
    if not specs:
        return []
    spans: list[tuple[str, int, int]] = []
    current_name = specs[0][REGION_IDX]
    start = 0
    for i, spec in enumerate(specs[1:], start=1):
        if spec[REGION_IDX] != current_name:
            spans.append((current_name, start, i - 1))
            current_name = spec[REGION_IDX]
            start = i
    spans.append((current_name, start, len(specs) - 1))
    return spans


REGION_SPANS: list[tuple[str, int, int]] = _derive_region_spans(PHASE_SPECS)


def _validate_configuration() -> list[str]:
    errors: list[str] = []

    if not PHASE_SPECS:
        errors.append("No phase specs configured.")
        return errors

    for idx, spec in enumerate(PHASE_SPECS):
        if spec[KIND_IDX] not in ("mission", "quest"):
            errors.append(f"Invalid phase kind at index {idx}: {spec[KIND_IDX]!r}")
        if not spec[KEY_IDX].strip():
            errors.append(f"Empty phase key at index {idx}")
        if not spec[TITLE_IDX].strip():
            errors.append(f"Empty phase title at index {idx}")

    if len(PHASE_DEFS) != len(PHASE_SPECS):
        errors.append(f"Phase definition mismatch: specs={len(PHASE_SPECS)} phases={len(PHASE_DEFS)}")

    for span in REGION_SPANS:
        if span[1] > span[2]:
            errors.append(f"Invalid region span {span[0]}: start={span[1]}, end={span[2]}")

    return errors


def _phase_title(index: int) -> str:
    if 0 <= index < len(bot._phases):
        return bot._phases[index].name
    return f"Phase {index + 1}"


def _set_start_phase_index(index: int) -> None:
    global start_phase_index
    total = len(bot._phases)
    if total <= 0:
        start_phase_index = 0
        return
    start_phase_index = max(0, min(index, total - 1))
    for idx, phase in enumerate(bot._phases):
        phase.condition = (lambda _i=idx: _i >= start_phase_index)


def _phase_summary() -> tuple[int, int, float]:
    total = len(bot._phases)
    remaining = max(0, total - start_phase_index)
    skipped_pct = 0.0 if total == 0 else (start_phase_index / total) * 100.0
    return total, remaining, skipped_pct


def _find_next_kind_index(kind: str, start_idx: int) -> int | None:
    for idx in range(start_idx + 1, len(PHASE_SPECS)):
        if PHASE_SPECS[idx][KIND_IDX] == kind:
            return idx
    return None


def _detect_current_phase_index() -> int | None:
    try:
        current_step = bot.bot.config.FSM.get_current_step_name()
    except Exception:
        return None

    for idx, phase in enumerate(bot._phases):
        header_name = bot.get_phase_header(phase.name)
        if header_name and current_step.startswith(header_name):
            return idx

    # Fallback when headers are not available yet.
    for idx, phase in enumerate(bot._phases):
        if phase.name in current_step:
            return idx
    return None


def _draw_current_activity() -> None:
    current_phase_idx = _detect_current_phase_index()
    try:
        current_step = bot.bot.config.FSM.get_current_step_name()
    except Exception:
        current_step = "FSM not initialized"

    PyImGui.text("Current Activity")
    PyImGui.separator()
    if current_phase_idx is None:
        PyImGui.text_colored("Phase: Not detected yet", (0.85, 0.7, 0.35, 1.0))
    else:
        spec = PHASE_SPECS[current_phase_idx]
        PyImGui.text_colored(
            f"Phase {current_phase_idx + 1:02d}: {spec[KIND_IDX].title()} - {spec[TITLE_IDX]}",
            (0.95, 0.85, 0.35, 1.0),
        )
    PyImGui.text_wrapped(f"FSM Step: {current_step}")


def _draw_main() -> None:
    global show_all_regions, _last_jump_message

    total_phases, remaining, skipped_pct = _phase_summary()
    _set_start_phase_index(start_phase_index)

    PyImGui.text("Prophecies Campaign")
    PyImGui.text(f"Phases: {total_phases} | Remaining from start: {remaining}")
    PyImGui.text(f"Skipped: {start_phase_index} ({skipped_pct:.1f}%)")

    if PyImGui.button("Start From Phase 1"):
        _set_start_phase_index(0)
    PyImGui.same_line(0, -1)
    show_all_regions = PyImGui.checkbox("Show all regions", show_all_regions)

    next_mission = _find_next_kind_index("mission", start_phase_index)
    next_quest = _find_next_kind_index("quest", start_phase_index)

    if PyImGui.button("Jump To Next Mission"):
        if next_mission is not None:
            _set_start_phase_index(next_mission)
            _last_jump_message = f"Start set to: {_phase_title(start_phase_index)}"
        else:
            _last_jump_message = "No next mission found."
    PyImGui.same_line(0, -1)
    if PyImGui.button("Jump To Next Quest"):
        if next_quest is not None:
            _set_start_phase_index(next_quest)
            _last_jump_message = f"Start set to: {_phase_title(start_phase_index)}"
        else:
            _last_jump_message = "No next quest found."
    PyImGui.same_line(0, -1)
    PyImGui.text_colored(_last_jump_message if _last_jump_message else " ", (0.85, 0.8, 0.45, 1.0))

    PyImGui.separator()
    _draw_current_activity()
    PyImGui.separator()

    for span in REGION_SPANS:
        span_name, span_start, span_end = span
        if span_start >= total_phases:
            continue
        region_end = min(span_end, total_phases - 1)
        region_total = region_end - span_start + 1
        region_remaining = max(0, region_end - start_phase_index + 1) if start_phase_index <= region_end else 0
        header_label = f"{span_name} ({region_remaining}/{region_total})###{span_name}"

        open_region = show_all_regions or PyImGui.collapsing_header(header_label)
        if not open_region:
            continue

        if PyImGui.button(f"Start here##{span_name}"):
            _set_start_phase_index(span_start)
        PyImGui.same_line(0, -1)
        PyImGui.text(f"Range: {span_start + 1:02d}-{region_end + 1:02d}")

        for idx in range(span_start, region_end + 1):
            selected = idx == start_phase_index
            enabled = idx >= start_phase_index
            changed = PyImGui.checkbox(f"##phase_start_{idx}", enabled)
            PyImGui.same_line(0, -1)
            label = _phase_title(idx)
            if selected:
                PyImGui.text_colored(label, (0.95, 0.85, 0.35, 1.0))
            elif enabled:
                PyImGui.text(label)
            else:
                PyImGui.text_colored(label, (0.55, 0.55, 0.55, 1.0))
            if changed != enabled:
                _set_start_phase_index(idx)

    PyImGui.separator()
    PyImGui.text(f"Start from: {start_phase_index + 1:02d}. {_phase_title(start_phase_index)}")

    if _validation_issues:
        PyImGui.separator()
        PyImGui.text_colored("Configuration Warnings", (0.9, 0.5, 0.3, 1.0))
        for issue in _validation_issues[:5]:
            PyImGui.bullet_text(issue)


def _draw_settings() -> None:
    draw_setup_tab()


def _main_dimensions() -> tuple[int, int]:
    return (780, 920)


bot = ModularBot(
    name="Prophecies Campaign",
    phases=PHASE_DEFS,
    loop=False,
    template="aggressive",
    use_custom_behaviors=True,
    main_ui=_draw_main,
    icon_path=os.path.join(_project_root(), "Bots", "modular_bot", "assets", "prophecies.jpg"),
    main_child_dimensions=_main_dimensions(),
    settings_ui=_draw_settings,
)

_validation_issues = _validate_configuration()
_set_start_phase_index(start_phase_index)


def main():
    bot.update()
