"""
modular_eotn module

This module is part of the modular runtime surface.
"""
from __future__ import annotations

from typing import Optional

from Py4GWCoreLib.modular import ModularBot
from Py4GWCoreLib.modular.phase import Phase
from Py4GWCoreLib.modular.recipes.modular_block import (
    build_modular_block_phase,
)


# tuple format: (region, kind, key, title)
EOTN_PHASE_SPECS: list[tuple[str, str, str, str]] = [
    ("Access", "quest", "eotn/what_lies_beneath", "What Lies Beneath"),
    ("Access", "route", "eotn/boreal_to_eotn", "Boreal Station to Eye of the North"),
    ("Access", "quest", "eotn/against_the_destroyers_start", "Against the Destroyers Start"),
    ("Outpost Unlocks", "route", "eotn/eotn_to_gunnars", "Eye of the North to Gunnar's Hold"),
    ("Outpost Unlocks", "route", "eotn/gunnars_to_longeyes", "Gunnar's Hold to Longeye's Ledge"),
    ("Outpost Unlocks", "route", "eotn/longeyes_to_doomlore", "Longeye's Ledge to Doomlore Shrine"),
    ("Outpost Unlocks", "route", "eotn/gunnars_to_sifhala", "Gunnar's Hold to Sifhalla"),
    ("Outpost Unlocks", "route", "eotn/sifhalla_to_olafstead", "Sifhalla to Olafstead"),
    ("Outpost Unlocks", "route", "eotn/olafstead_to_umbral_grotto", "Olafstead to Umbral Grotto"),
    ("Outpost Unlocks", "route", "eotn/umbral_grotto_to_vlox", "Umbral Grotto to Vlox's Falls"),
    ("Outpost Unlocks", "route", "eotn/vlox_to_gadds", "Vlox's Falls to Gadd's Encampment"),
    ("Outpost Unlocks", "route", "eotn/vlox_to_tarnished", "Vlox's Falls to Tarnished Haven"),
    ("Outpost Unlocks", "route", "eotn/tarnished_to_rata", "Tarnished Haven to Rata Sum"),
    ("Asura", "quest", "eotn/finding_gadd", "Finding Gadd"),
    ("Asura", "mission", "eotn/finding_the_bloodstone", "Finding the Bloodstone"),
    ("Asura", "quest", "eotn/lab_space", "Lab Space"),
    ("Asura", "mission", "eotn/the_elusive_golemancer", "The Elusive Golemancer"),
    ("Asura", "quest", "eotn/a_little_help", "A Little Help"),
    ("Asura", "mission", "eotn/genius_operated_living_enchanted_manifestation", "G.O.L.E.M"),
    ("Ebon Vanguard", "quest", "eotn/search_for_the_ebon_vanguard", "Search for the Ebon Vanguard"),
    ("Ebon Vanguard", "mission", "eotn/against_the_charr", "Against the Charr"),
    ("Ebon Vanguard", "quest", "eotn/the_dawn_of_rebellion", "The Dawn of Rebellion"),
    ("Ebon Vanguard", "mission", "eotn/warband_of_brothers", "Warband of Brothers"),
    ("Ebon Vanguard", "quest", "eotn/what_must_be_done", "What Must Be Done"),
    ("Ebon Vanguard", "mission", "eotn/assault_on_the_stronghold", "Assault on the Stronghold"),
    ("Norn", "quest", "eotn/northern_allies_reward", "Northern Allies Reward"),
    ("Norn", "quest", "eotn/tracking_the_nornbear", "Tracking the Nornbear"),
    ("Norn", "mission", "eotn/curse_of_the_nornbear", "Curse of the Nornbear"),
    ("Norn", "quest", "eotn/flames_of_the_bear_spirit", "Flames of the Bear Spirit"),
    ("Norn", "mission", "eotn/blood_washes_blood", "Blood Washes Blood"),
    ("Norn", "quest", "eotn/vision_of_the_raven_spirit", "Vision of the Raven Spirit"),
    ("Norn", "mission", "eotn/a_gate_too_far", "A Gate Too Far"),
    ("Finale", "quest", "eotn/the_final_vision", "The Final Vision"),
    ("Finale", "dungeon", "heart_of_the_shiverpeaks", "Heart of the Shiverpeaks"),
    ("Finale", "mission", "eotn/destructions_depths", "Destruction's Depths"),
    ("Finale", "mission", "eotn/a_time_for_heroes", "A Time for Heroes"),
]

REGION_IDX = 0
KIND_IDX = 1
KEY_IDX = 2
TITLE_IDX = 3


class EotnCampaignOptions:
    """
    EotnCampaignOptions class.

    Meta:
      Expose: true
      Audience: advanced
      Display: EotN Campaign Options
      Purpose: Provide explicit modular runtime behavior and metadata.
      UserDescription: Internal class used by modular orchestration and step execution.
      Notes: Keep behavior explicit and side effects contained.
    """

    def __init__(
        self,
        *,
        start_phase_index: int = 0,
        loop: bool = False,
        team_selection: str = "priority",
        debug_logging: bool = False,
    ) -> None:
        self.start_phase_index = int(start_phase_index)
        self.loop = bool(loop)
        mode = str(team_selection or "priority").strip().lower()
        if mode not in ("priority", "exact", "henchman"):
            mode = "priority"
        self.team_selection = mode
        self.debug_logging = bool(debug_logging)


def _eotn_load_party_overrides(team_selection: str) -> dict:
    mode = str(team_selection or "priority").strip().lower()
    if mode == "exact":
        return {"team_mode": "exact", "fill_with_henchmen": False}
    if mode == "henchman":
        return {"team_mode": "henchman", "fill_with_henchmen": True}
    return {"hero_team": "priority", "fill_with_henchmen": True}


def _block_kind_for_phase_kind(kind: str) -> str:
    if kind == "mission":
        return "missions"
    if kind == "quest":
        return "quests"
    if kind == "route":
        return "routes"
    if kind == "dungeon":
        return "dungeons"
    return kind


def _recipe_name_for_phase_kind(kind: str) -> str:
    if not kind:
        return "ModularBlock"
    return kind.title()


def build_eotn_campaign_phases(team_selection: str = "priority") -> list[Phase]:
    load_party_overrides = _eotn_load_party_overrides(team_selection)
    phases: list[Phase] = []
    for idx, spec in enumerate(EOTN_PHASE_SPECS):
        kind = spec[KIND_IDX]
        key = spec[KEY_IDX]
        title = spec[TITLE_IDX]
        phase_name = f"{idx + 1:02d}. {kind.title()}: {title}"
        phases.append(
            build_modular_block_phase(
                key,
                name=phase_name,
                kind=_block_kind_for_phase_kind(kind),
                recipe_name=_recipe_name_for_phase_kind(kind),
                anchor=True,
                load_party_overrides=load_party_overrides,
            )
        )
    return phases


def derive_eotn_region_spans(
    specs: list[tuple[str, str, str, str]] | None = None,
) -> list[tuple[str, int, int]]:
    source_specs = specs if specs is not None else EOTN_PHASE_SPECS
    if not source_specs:
        return []

    spans: list[tuple[str, int, int]] = []
    current_region = source_specs[0][REGION_IDX]
    start = 0
    for idx, spec in enumerate(source_specs[1:], start=1):
        if spec[REGION_IDX] != current_region:
            spans.append((current_region, start, idx - 1))
            current_region = spec[REGION_IDX]
            start = idx
    spans.append((current_region, start, len(source_specs) - 1))
    return spans


EOTN_REGION_SPANS = derive_eotn_region_spans()


def apply_eotn_start_index(phases: list[Phase], start_index: int) -> int:
    if not phases:
        return 0
    return max(0, min(int(start_index), len(phases) - 1))


def create_eotn_campaign_bot(
    *,
    options: EotnCampaignOptions | None = None,
    main_ui=None,
    settings_ui=None,
    help_ui=None,
    name: str = "Modular EotN",
) -> ModularBot:
    opts = options or EotnCampaignOptions()
    all_phases = build_eotn_campaign_phases(opts.team_selection)
    clamped_start = apply_eotn_start_index(all_phases, opts.start_phase_index)
    phases = all_phases[clamped_start:] if all_phases else []

    restart_target: Optional[str] = phases[0].name if phases else None

    return ModularBot(
        name=name,
        phases=phases,
        loop=bool(opts.loop),
        template="multibox_aggressive",
        on_party_wipe=restart_target,
        on_death=restart_target,
        main_ui=main_ui,
        settings_ui=settings_ui,
        help_ui=help_ui,
        upkeep_hero_ai_active=True,
        debug_logging=bool(opts.debug_logging),
    )
