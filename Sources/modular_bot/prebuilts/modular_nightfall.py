from __future__ import annotations

from typing import Optional

from Py4GWCoreLib import ConsoleLog
from Py4GWCoreLib.enums_src.Title_enums import TITLE_TIERS, TitleID
from Sources.modular_bot import ModularBot
from Sources.modular_bot.phase import Phase
from Sources.modular_bot.recipes.modular_block import modular_block_run


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
        team_selection: str = "priority",
    ) -> None:
        self.start_phase_index = int(start_phase_index)
        self.loop = bool(loop)
        mode = str(team_selection or "priority").strip().lower()
        if mode not in ("priority", "exact", "henchman"):
            mode = "priority"
        self.team_selection = mode


def _nightfall_load_party_overrides(team_selection: str) -> dict:
    mode = str(team_selection or "priority").strip().lower()
    if mode == "exact":
        return {"team_mode": "exact", "use_priority": False, "fill_with_henchmen": False}
    if mode == "henchman":
        return {"team_mode": "henchman", "use_priority": False, "fill_with_henchmen": True}
    # priority (default): use priority list first, then fill missing slots with henchmen.
    return {"team_mode": "priority", "use_priority": True, "fill_with_henchmen": True}


def build_nightfall_campaign_phases(team_selection: str = "priority") -> list[Phase]:
    from Py4GWCoreLib import Player
    load_party_overrides = _nightfall_load_party_overrides(team_selection)

    def _sunspear_points() -> int:
        try:
            title = Player.GetTitle(int(TitleID.Sunspear))
            return int(getattr(title, "current_points", 0) or 0) if title is not None else 0
        except Exception:
            return 0

    def _repeat_phase_by_name(bot, phase_name: str) -> bool:
        owner = getattr(bot, "_modular_owner", None)
        if owner is not None and hasattr(owner, "get_phase_header"):
            try:
                header_name = owner.get_phase_header(phase_name)
                if header_name:
                    bot.config.FSM.jump_to_state_by_name(header_name)
                    ConsoleLog("NightfallCampaign", f"Sunspear gate: repeating phase {phase_name!r} via {header_name}.")
                    return True
            except Exception:
                pass

        # Fallback for safety if owner/header lookup is unavailable.
        fsm = bot.config.FSM
        current_state = getattr(fsm, "current_state", None)
        if current_state is None:
            return False
        states = list(getattr(fsm, "states", []) or [])
        try:
            current_index = states.index(current_state)
        except ValueError:
            return False
        for idx in range(current_index, -1, -1):
            state_name = str(getattr(states[idx], "name", "") or "")
            if state_name.startswith("[H]"):
                fsm.jump_to_state_by_name(state_name)
                ConsoleLog("NightfallCampaign", f"Sunspear gate: repeating phase {phase_name!r} via {state_name}.")
                return True
        return False

    def _farm_phase_with_sunspear_gate(farm_key: str, phase_name: str, party_overrides: dict):
        def _runner(bot):
            modular_block_run(
                bot,
                farm_key,
                kind="farms",
                recipe_name="Farm",
                load_party_overrides=party_overrides,
            )

            def _gate():
                points = _sunspear_points()
                if points >= SUNSPEAR_POINTS_REQUIRED:
                    ConsoleLog(
                        "NightfallCampaign",
                        f"Sunspear gate passed ({points}/{SUNSPEAR_POINTS_REQUIRED}). Continuing campaign.",
                    )
                    return
                ConsoleLog(
                    "NightfallCampaign",
                    f"Sunspear gate not met ({points}/{SUNSPEAR_POINTS_REQUIRED}). Repeating farm phase.",
                )
                if not _repeat_phase_by_name(bot, phase_name):
                    ConsoleLog(
                        "NightfallCampaign",
                        f"Sunspear gate could not find header for {phase_name!r}; continuing without repeat.",
                    )

            bot.States.AddCustomState(_gate, f"{phase_name}: Sunspear Rank Gate")

        return _runner

    def _farm_phase_without_gate(farm_key: str, phase_name: str, party_overrides: dict):
        def _runner(bot):
            modular_block_run(
                bot,
                farm_key,
                kind="farms",
                recipe_name="Farm",
                load_party_overrides=party_overrides,
            )

        return _runner

    def _mission_runner(mission_key: str, party_overrides: dict):
        def _runner(bot):
            modular_block_run(
                bot,
                mission_key,
                kind="missions",
                recipe_name="Mission",
                load_party_overrides=party_overrides,
            )

        return _runner

    def _quest_runner(quest_key: str, party_overrides: dict):
        def _runner(bot):
            modular_block_run(
                bot,
                quest_key,
                kind="quests",
                recipe_name="Quest",
                load_party_overrides=party_overrides,
            )

        return _runner

    phases: list[Phase] = []
    for idx, spec in enumerate(NIGHTFALL_PHASE_SPECS):
        kind = spec[KIND_IDX]
        key = spec[KEY_IDX]
        title = spec[TITLE_IDX]
        phase_name = f"{idx + 1:02d}. {kind.title()}: {title}"
        if kind == "mission":
            phases.append(Phase(phase_name, _mission_runner(key, load_party_overrides), anchor=True))
        elif kind == "farm":
            if key == SUNSPEAR_REPEAT_FARM_KEY:
                phases.append(Phase(phase_name, _farm_phase_with_sunspear_gate(key, phase_name, load_party_overrides), anchor=True))
            else:
                phases.append(Phase(phase_name, _farm_phase_without_gate(key, phase_name, load_party_overrides), anchor=True))
        else:
            phases.append(Phase(phase_name, _quest_runner(key, load_party_overrides), anchor=True))
    return phases


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


def apply_nightfall_start_index(phases: list[Phase], start_index: int) -> int:
    if not phases:
        return 0
    return max(0, min(int(start_index), len(phases) - 1))


def create_nightfall_campaign_bot(
    *,
    options: NightfallCampaignOptions | None = None,
    main_ui=None,
    settings_ui=None,
    help_ui=None,
    name: str = "Modular Nightfall",
) -> ModularBot:
    opts = options or NightfallCampaignOptions()
    all_phases = build_nightfall_campaign_phases(opts.team_selection)
    clamped_start = apply_nightfall_start_index(all_phases, opts.start_phase_index)
    phases = all_phases[clamped_start:] if all_phases else []

    restart_target: Optional[str] = phases[0].name if phases else None

    return ModularBot(
        name=name,
        phases=phases,
        loop=bool(opts.loop),
        # Modular Nightfall is locked to HeroAI runtime behavior.
        template="multibox_aggressive",
        on_party_wipe=restart_target,
        # Nightfall flow should only recover on true party wipe.
        # Player-only deaths can be resurrected in-place without phase rewind.
        on_death=None,
        main_ui=main_ui,
        settings_ui=settings_ui,
        help_ui=help_ui,
        upkeep_hero_ai_active=True,
    )
