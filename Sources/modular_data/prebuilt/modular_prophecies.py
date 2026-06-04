"""Prophecies campaign BT recipe runner."""
from __future__ import annotations

from Py4GWCoreLib.modular import BTRecipeRunner
from Py4GWCoreLib.modular import RecipeSpec
from Py4GWCoreLib.modular import specs_from_campaign_rows


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
    ) -> None:
        self.start_phase_index = int(start_phase_index)
        self.loop = bool(loop)


def build_prophecies_campaign_specs() -> list[RecipeSpec]:
    return specs_from_campaign_rows(PROPHECIES_PHASE_SPECS)


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


def apply_prophecies_start_index(specs: list[RecipeSpec], start_index: int) -> int:
    if not specs:
        return 0
    return max(0, min(int(start_index), len(specs) - 1))


def create_prophecies_campaign_bot(
    *,
    options: PropheciesCampaignOptions | None = None,
    name: str = "Modular Prophecies",
    debug_hook=None,
) -> BTRecipeRunner:
    opts = options or PropheciesCampaignOptions()
    specs = build_prophecies_campaign_specs()
    clamped_start = apply_prophecies_start_index(specs, opts.start_phase_index)
    return BTRecipeRunner(
        name=name,
        specs=specs,
        start_index=clamped_start,
        loop=bool(opts.loop),
        debug_hook=debug_hook,
    )
