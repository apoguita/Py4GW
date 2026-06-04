"""Nightfall campaign BT recipe runner."""
from __future__ import annotations

from Py4GWCoreLib.enums_src.Title_enums import TITLE_TIERS, TitleID
from Py4GWCoreLib.modular import BTRecipeRunner
from Py4GWCoreLib.modular import RecipeSpec
from Py4GWCoreLib.modular import specs_from_campaign_rows


SUNSPEAR_REPEAT_FARM_KEY = "sunspear/yohlon_insects"


# tuple format: (region, kind, key, title)
NIGHTFALL_PHASE_SPECS: list[tuple[str, str, str, str]] = [
    ("Istan", "quest", "nightfall/the_honorable_general", "The Honorable General"),
    ("Istan", "quest", "nightfall/signs_and_portents", "Signs and Portents"),
    ("Istan", "mission", "nightfall/jokanur_diggings", "Jokanur Diggings"),
    ("Istan", "quest", "nightfall/isle_of_the_dead", "Isle of the Dead"),
    ("Istan", "quest", "nightfall/bad_tide_rising", "Bad Tide Rising"),
    ("Istan", "quest", "nightfall/zaishen_elite", "Zaishen Elite"),
    ("Istan", "quest", "nightfall/student_sousuke", "Student Sousuke"),
    ("Istan", "quest", "nightfall/special_delivery", "Special Delivery"),
    ("Istan", "quest", "nightfall/big_news_small_package", "Big News, Small Package"),
    ("Istan", "quest", "nightfall/following_the_trail", "Following the Trail"),
    ("Istan", "mission", "nightfall/blacktide_den", "Blacktide Den"),
    ("Istan", "quest", "nightfall/the_iron_truth", "The Iron Truth"),
    ("Istan", "quest", "nightfall/trial_by_fire", "Trial by Fire"),
    ("Istan", "quest", "nightfall/war_preparations_recruit_training", "War Preparations (Recruit Training)"),
    ("Istan", "quest", "nightfall/war_preparations_ghost_reconnaissance", "War Preparations (Ghost Reconnaissance)"),
    ("Istan", "quest", "nightfall/war_preparations_wind_and_water", "War Preparations (Wind and Water)"),
    ("Istan", "quest", "nightfall/the_time_is_nigh", "The Time is Nigh"),
    ("Kourna", "mission", "nightfall/consulate_docks", "Consulate Docks"),
    ("Kourna", "quest", "nightfall/hunted", "Hunted!"),
    ("Kourna", "quest", "nightfall/the_great_escape", "The Great Escape"),
    ("Kourna", "farm", "sunspear/yohlon_insects_setup", "Prepare Yohlon farm"),
    ("Kourna", "farm", "sunspear/yohlon_insects", "Farm up Sunspear title"),
    ("Kourna", "quest", "nightfall/and_a_hero_shall_lead_them", "And a Hero Shall Lead Them"),
    ("Kourna", "mission", "nightfall/venta_cemetry", "Venta Cemetery"),
    ("Kourna", "quest", "nightfall/the_council_is_called", "The Council is Called"),
    ("Kourna", "quest", "nightfall/to_vabbi", "To Vabbi!"),
    ("Kourna", "quest", "nightfall/centaur_blackmail", "Centaur Blackmail"),
    ("Kourna", "mission", "nightfall/kodonur_crossroads", "Kodonur Crossroads"),
    ("Kourna", "quest", "nightfall/mysterious_message", "Mysterious Message"),
    ("Kourna", "quest", "nightfall/secrets_in_the_shadow", "Secrets in the Shadow"),
    ("Kourna", "quest", "nightfall/to_kill_a_demon", "To Kill a Demon"),
    ("Kourna", "mission", "nightfall/rihlon_refuge", "Rilohn Refuge"),
    ("Kourna", "mission", "nightfall/moddock_crevice", "Moddok Crevice"),
    ("Vabbi", "quest", "nightfall/rally_the_princess", "Rally The Princes"),
    ("Vabbi", "mission", "nightfall/tihark_orchard", "Tihark Orchard"),
    ("Vabbi", "quest", "nightfall/alls_well_that_ends_well", "All's Well That Ends Well"),
    ("Vabbi", "quest", "nightfall/warning_kehanni", "Warning Kehanni"),
    ("Vabbi", "quest", "nightfall/calling_the_order", "Calling the Order"),
    ("Vabbi", "mission", "nightfall/dzagonur_bastion", "Dzagonur Bastion"),
    ("Vabbi", "quest", "nightfall/brains_or_brawn", "Brains or Brawn"),
    ("Vabbi", "quest", "nightfall/the_role_of_a_lifetime", "The Role of a Lifetime"),
    ("Vabbi", "quest", "nightfall/pledge_to_the_merchant_princes", "Pledge of the Merchant Princes"),
    ("Vabbi", "mission", "nightfall/grand_court_of_sebelkeh", "Grand Court of Sebelkeh"),
    ("Vabbi", "quest", "nightfall/attack_at_the_kodash", "Attack at the Kodash"),
    ("Vabbi", "quest", "nightfall/heart_or_mind_ronjok_in_danger", "Heart or Mind: Ronjok in Danger"),
    ("Vabbi", "mission", "nightfall/nundu_bay", "Nundu Bay"),
    ("Desolation", "quest", "nightfall/crossing_the_desolation", "Crossing the Desolation"),
    ("Desolation", "mission", "nightfall/gate_of_desolation", "Gate of Desolation"),
    ("Desolation", "quest", "nightfall/a_deals_a_deal", "A Deal's a Deal"),
    ("Desolation", "quest", "nightfall/horde_of_darkness", "Horde of Darkness"),
    ("Desolation", "mission", "nightfall/ruins_of_morah", "Ruins of Morah"),
    ("Realm of Torment", "quest", "nightfall/uncharted_territory", "Uncharted Territory"),
    ("Realm of Torment", "mission", "nightfall/gate_of_pain", "Gate of Pain"),
    ("Realm of Torment", "quest", "nightfall/kormirs_crusade", "Kormir's Crusade"),
    ("Realm of Torment", "quest", "nightfall/all_alone_in_the_darkness", "All Alone in the Darkness"),
    ("Realm of Torment", "mission", "nightfall/gate_of_madness", "Gate of Madness"),
    ("Realm of Torment", "mission", "nightfall/abbadons_gate", "Abaddon's Gate"),
]

REGION_IDX = 0
KIND_IDX = 1
KEY_IDX = 2
TITLE_IDX = 3
SUNSPEAR_RANK_REQUIRED = 7
SUNSPEAR_POINTS_REQUIRED = int(TITLE_TIERS[int(TitleID.Sunspear)][SUNSPEAR_RANK_REQUIRED - 1].required)


class NightfallCampaignOptions:
    def __init__(
        self,
        *,
        start_phase_index: int = 0,
        loop: bool = False,
    ) -> None:
        self.start_phase_index = int(start_phase_index)
        self.loop = bool(loop)


def build_nightfall_campaign_specs() -> list[RecipeSpec]:
    return specs_from_campaign_rows(NIGHTFALL_PHASE_SPECS)


def derive_nightfall_region_spans(
    specs: list[tuple[str, str, str, str]] | None = None,
) -> list[tuple[str, int, int]]:
    source_specs = specs if specs is not None else NIGHTFALL_PHASE_SPECS
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


NIGHTFALL_REGION_SPANS = derive_nightfall_region_spans()


def apply_nightfall_start_index(specs: list[RecipeSpec], start_index: int) -> int:
    if not specs:
        return 0
    return max(0, min(int(start_index), len(specs) - 1))


def create_nightfall_campaign_bot(
    *,
    options: NightfallCampaignOptions | None = None,
    name: str = "Modular Nightfall",
    debug_hook=None,
) -> BTRecipeRunner:
    opts = options or NightfallCampaignOptions()
    specs = build_nightfall_campaign_specs()
    clamped_start = apply_nightfall_start_index(specs, opts.start_phase_index)
    return BTRecipeRunner(
        name=name,
        specs=specs,
        start_index=clamped_start,
        loop=bool(opts.loop),
        debug_hook=debug_hook,
    )
