from __future__ import annotations

from typing import Optional

from Sources.modular_bot import ModularBot
from Sources.modular_bot.phase import Phase
from Sources.modular_bot.recipes import Mission, Quest, Route


# tuple format: (region, kind, key, title)
PROPHECIES_PHASE_SPECS: list[tuple[str, str, str, str]] = [
    ("Ascalon", "mission", "prophecies/the_great_northern_wall", "The Great Northern Wall"),
    ("Ascalon", "mission", "prophecies/fort_ranik", "Fort Ranik"),
    ("Ascalon", "quest", "prophecies/ruins_of_surmia", "Ruins of Surmia"),
    ("Ascalon", "mission", "prophecies/ruins_of_surmia", "Ruins of Surmia"),
    ("Ascalon", "mission", "prophecies/nolani_academy", "Nolani Academy"),
    ("Northern Shiverpeaks", "quest", "prophecies/the_way_is_blocked", "The Way Is Blocked"),
    ("Northern Shiverpeaks", "mission", "prophecies/borlis_pass", "Borlis Pass"),
    ("Northern Shiverpeaks", "mission", "prophecies/the_frost_gate", "The Frost Gate"),
    ("Kryta", "quest", "prophecies/to_kryta_refugees_icecave_journeyend", "To Kryta: Refugees, Ice Caves and End"),
    ("Kryta", "mission", "prophecies/gates_of_kryta", "Gates of Kryta"),
    ("Kryta", "quest", "prophecies/report_to_the_white_mantle", "Report to the White Mantle"),
    ("Kryta", "mission", "prophecies/d_alessio_seaboard", "D'Alessio Seaboard"),
    ("Kryta", "mission", "prophecies/divinity_coast", "Divinity Coast"),
    ("Maguuma Jungle", "quest", "prophecies/a_brothers_fury", "A Brother's Fury"),
    ("Maguuma Jungle", "mission", "prophecies/the_wilds", "The Wilds"),
    ("Maguuma Jungle", "mission", "prophecies/bloodstone_fen", "Bloodstone Fen"),
    ("Maguuma Jungle", "quest", "prophecies/white_mantle_wrath_demagogue_vanguard", "White Mantle Wrath: Demagogue's Vanguard"),
    ("Maguuma Jungle", "quest", "prophecies/urgent_warning", "Urgent Warning"),
    ("Maguuma Jungle", "mission", "prophecies/aurora_glade", "Aurora Glade"),
    ("Kryta Extended", "quest", "prophecies/passage_through_the_dark_river", "Passage Through The Dark River"),
    ("Kryta Extended", "mission", "prophecies/riverside_province", "Riverside Province"),
    ("Kryta Extended", "mission", "prophecies/sanctum_cay", "Sanctum Cay"),
    ("Temple Transit", "route", "lions_arch_to_d_alessio_seaboard", "Lion's Arch to D'Alessio"),
    ("Temple Transit", "route", "d_alessio_seaboard_to_bergen_hot_springs", "D'Alessio to Bergen"),
    ("Temple Transit", "route", "bergen_hot_springs_to_temple_of_ages", "Bergen to Temple of the Ages"),
    ("Southern Shiverpeaks Transit", "route", "la_to_beacons", "LA to Beacons"),
    ("Southern Shiverpeaks Transit", "route", "beacons_to_rankor", "Beacons to Camp Rankor"),
    ("Southern Shiverpeaks Transit", "route", "camp_rankor_to_droks", "Camp Rankor to Droknar's"),
    ("Southern Shiverpeaks Transit", "route", "droks_to_ice_caves", "Droknar's to Ice Caves"),
    ("Southern Shiverpeaks Missions", "mission", "prophecies/ice_caves_of_sorrow", "Ice Caves of Sorrow"),
    ("Southern Shiverpeaks Missions", "mission", "prophecies/iron_mines_of_moladune", "Iron Mines of Moladune"),
    ("Southern Shiverpeaks Missions", "mission", "prophecies/thunderhead_keep", "Thunderhead Keep"),
    ("Ring of Fire", "quest", "prophecies/final_blow", "Final Blow"),
    ("Ring of Fire", "mission", "prophecies/ring_of_fire", "Ring of Fire"),
    ("Ring of Fire", "mission", "prophecies/abaddons_mouth", "Abaddon's Mouth"),
    ("Ring of Fire", "mission", "prophecies/hells_precipice", "Hell's Precipice"),
]

REGION_IDX = 0
KIND_IDX = 1
KEY_IDX = 2
TITLE_IDX = 3


class PropheciesCampaignOptions:
    def __init__(
        self,
        *,
        start_phase_index: int = 0,
        loop: bool = False,
        template: str = "aggressive",
        use_custom_behaviors: bool = True,
    ) -> None:
        self.start_phase_index = int(start_phase_index)
        self.loop = bool(loop)
        self.template = str(template)
        self.use_custom_behaviors = bool(use_custom_behaviors)


def build_prophecies_campaign_phases() -> list[Phase]:
    phases: list[Phase] = []
    for idx, spec in enumerate(PROPHECIES_PHASE_SPECS):
        kind = spec[KIND_IDX]
        key = spec[KEY_IDX]
        title = spec[TITLE_IDX]
        phase_name = f"{idx + 1:02d}. {kind.title()}: {title}"
        if kind == "mission":
            phases.append(Mission(key, phase_name, anchor=True))
        elif kind == "quest":
            phases.append(Quest(key, phase_name, anchor=True))
        else:
            phases.append(Route(key, phase_name, anchor=True))
    return phases


def derive_prophecies_region_spans(
    specs: list[tuple[str, str, str, str]] | None = None,
) -> list[tuple[str, int, int]]:
    source_specs = specs if specs is not None else PROPHECIES_PHASE_SPECS
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


PROPHECIES_REGION_SPANS = derive_prophecies_region_spans()


def apply_prophecies_start_index(phases: list[Phase], start_index: int) -> int:
    if not phases:
        return 0
    return max(0, min(int(start_index), len(phases) - 1))


def create_prophecies_campaign_bot(
    *,
    options: PropheciesCampaignOptions | None = None,
    main_ui=None,
    settings_ui=None,
    help_ui=None,
    name: str = "Modular Prophecies",
) -> ModularBot:
    opts = options or PropheciesCampaignOptions()
    all_phases = build_prophecies_campaign_phases()
    clamped_start = apply_prophecies_start_index(all_phases, opts.start_phase_index)
    phases = all_phases[clamped_start:] if all_phases else []

    restart_target: Optional[str] = phases[0].name if phases else None

    return ModularBot(
        name=name,
        phases=phases,
        loop=bool(opts.loop),
        template=str(opts.template),
        use_custom_behaviors=bool(opts.use_custom_behaviors),
        on_party_wipe=restart_target,
        on_death=restart_target,
        main_ui=main_ui,
        settings_ui=settings_ui,
        help_ui=help_ui,
    )

