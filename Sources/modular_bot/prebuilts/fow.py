from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Optional

from Py4GWCoreLib.enums_src.Map_enums import name_to_map_id
from Py4GWCoreLib.enums_src.Item_enums import MaterialMap
from Py4GWCoreLib.enums_src.Model_enums import ModelID
from Sources.modular_bot import ModularBot
from Sources.modular_bot.phase import Phase
from Sources.modular_bot.recipes import Quest
from Sources.modular_bot.recipes.modular_actions import register_step as _register_shared_step
from Sources.modular_bot.recipes.runner_common import count_expanded_steps, register_recipe_context, register_repeated_steps


FOW_QUEST_ORDER: list[tuple[str, str]] = [
    ("tower_of_courage", "Tower Of Courage"),
    ("eternal_forgemaster", "Eternal Forgemaster"),
    ("defend_the_temple", "Defend The Temple"),
    ("restore_the_temple", "Restore The Temple"),
    ("khobay", "Khobay"),
    ("tower_of_strength", "Tower Of Strength"),
    ("slaves_of_menzies", "Slaves Of Menzies"),
    ("army_of_darkness", "Army Of Darkness"),
    ("wailing_lord", "Wailing Lord"),
    ("gift_of_griffons", "Gift Of Griffons"),
    ("reward_time", "Reward Time"),
]

ZIN_KU_CORRIDOR_MAP_ID = int(name_to_map_id["Zin Ku Corridor"])
CHANTRY_OF_SECRETS_MAP_ID = int(name_to_map_id["Chantry of Secrets"])
TEMPLE_OF_THE_AGES_MAP_ID = int(name_to_map_id["Temple of the Ages"])
EMBARK_BEACH_MAP_ID = int(name_to_map_id["Embark Beach"])
FOW_MAP_ID = int(name_to_map_id["The Fissure of Woe"])
FOW_SCROLL_MODEL_ID = int(ModelID.Passage_Scroll_Fow.value)

CONSUMABLE_RESTOCK_DEFAULTS = {
    "grail_of_might": 3,
    "essence_of_celerity": 3,
    "armor_of_salvation": 3,
    "war_supplies": 3,
    "drake_kabob": 3,
    "candy_corn": 10,
}

CONSUMABLE_PROPERTY_NAMES = tuple(CONSUMABLE_RESTOCK_DEFAULTS.keys())
FOW_ENTRYPOINTS: dict[str, tuple[str, int]] = {
    "zin_ku_corridor": ("Zin Ku Corridor", ZIN_KU_CORRIDOR_MAP_ID),
    "chantry_of_secrets": ("Chantry of Secrets", CHANTRY_OF_SECRETS_MAP_ID),
    "temple_of_the_ages": ("Temple of the Ages", TEMPLE_OF_THE_AGES_MAP_ID),
    "embark_beach": ("Embark Beach", EMBARK_BEACH_MAP_ID),
}
DEFAULT_FOW_ENTRYPOINT_KEY = "zin_ku_corridor"
GH_MERCHANT_SELECTOR: dict[str, str] = {"npc": "MERCHANT"}
COMMON_MATERIAL_EXCLUDE_FOR_NON_CONS = {
    int(ModelID.Bone.value),
    int(ModelID.Pile_Of_Glittering_Dust.value),
    int(ModelID.Feather.value),
}
ALL_COMMON_MATERIALS = [
    material_name
    for model_id, material_name in MaterialMap.items()
    if int(model_id.value)
    not in {
        int(ModelID.Amber_Chunk.value),
        int(ModelID.Bolt_Of_Damask.value),
        int(ModelID.Bolt_Of_Linen.value),
        int(ModelID.Bolt_Of_Silk.value),
        int(ModelID.Deldrimor_Steel_Ingot.value),
        int(ModelID.Diamond.value),
        int(ModelID.Elonian_Leather_Square.value),
        int(ModelID.Fur_Square.value),
        int(ModelID.Glob_Of_Ectoplasm.value),
        int(ModelID.Jadeite_Shard.value),
        int(ModelID.Leather_Square.value),
        int(ModelID.Lump_Of_Charcoal.value),
        int(ModelID.Monstrous_Claw.value),
        int(ModelID.Monstrous_Eye.value),
        int(ModelID.Monstrous_Fang.value),
        int(ModelID.Obsidian_Shard.value),
        int(ModelID.Onyx_Gemstone.value),
        int(ModelID.Roll_Of_Parchment.value),
        int(ModelID.Roll_Of_Vellum.value),
        int(ModelID.Ruby.value),
        int(ModelID.Sapphire.value),
        int(ModelID.Spiritwood_Plank.value),
        int(ModelID.Steel_Ingot.value),
        int(ModelID.Tempered_Glass_Vial.value),
        int(ModelID.Vial_Of_Ink.value),
    }
]


@dataclass(slots=True)
class ModularFowOptions:
    hard_mode: bool = True
    use_consumables: bool = True
    restock_consumables: bool = True
    auto_loot: bool = True
    debug_logging: bool = False
    entrypoint: str = DEFAULT_FOW_ENTRYPOINT_KEY
    sell_non_cons_materials: bool = False
    sell_all_common_materials: bool = False
    buy_ectoplasm: bool = False


def _debug(debug_hook: Optional[Callable[[str], None]], message: str) -> None:
    if debug_hook is not None:
        debug_hook(message)


def _resolve_entrypoint(entrypoint: str) -> tuple[str, int]:
    key = str(entrypoint or DEFAULT_FOW_ENTRYPOINT_KEY).strip().lower()
    return FOW_ENTRYPOINTS.get(key, FOW_ENTRYPOINTS[DEFAULT_FOW_ENTRYPOINT_KEY])


def _resolve_materials_to_sell(options: ModularFowOptions) -> list[str]:
    if options.sell_all_common_materials:
        return list(ALL_COMMON_MATERIALS)
    if options.sell_non_cons_materials:
        return [
            material_name
            for model_id, material_name in MaterialMap.items()
            if int(model_id.value) in {int(m.value) for m in MaterialMap.keys()}
            and int(model_id.value) not in COMMON_MATERIAL_EXCLUDE_FOR_NON_CONS
            and material_name in ALL_COMMON_MATERIALS
        ]
    return []


def build_fow_phases(
    options: ModularFowOptions,
    debug_hook: Optional[Callable[[str], None]] = None,
) -> list[Phase]:
    def _fow_setup(bot) -> None:
        entrypoint_name, entrypoint_map_id = _resolve_entrypoint(options.entrypoint)
        materials_to_sell = _resolve_materials_to_sell(options)
        _debug(
            debug_hook,
            "Registering FoW setup steps "
            f"(hard_mode={options.hard_mode}, use_consumables={options.use_consumables}, "
            f"restock_consumables={options.restock_consumables}, auto_loot={options.auto_loot}, "
            f"entrypoint={entrypoint_name}, sell_non_cons_materials={options.sell_non_cons_materials}, "
            f"sell_all_common_materials={options.sell_all_common_materials}, buy_ectoplasm={options.buy_ectoplasm})",
        )
        setup_steps = [
            {"type": "leave_party", "name": "Leave Party", "multibox": True},
            {"type": "travel_gh", "name": "Travel to Guild Hall", "ms": 7000, "multibox": True},
            {"type": "restock_kits", "name": "Restock Kits", "id_kits": 2, "salvage_kits": 5, "multibox": True, "ms": 3000, **GH_MERCHANT_SELECTOR},
            {"type": "set_auto_looting", "enabled": bool(options.auto_loot)},
        ]

        if options.use_consumables and options.restock_consumables:
            setup_steps.append({"type": "restock_cons"})

        if materials_to_sell:
            setup_steps.append(
                {"type": "sell_materials", "name": "Sell Materials", "materials": materials_to_sell, "multibox": True}
            )

        setup_steps.append({"type": "deposit_materials", "name": "Deposit Full Material Stacks", "multibox": True})
        
        if options.buy_ectoplasm:
            setup_steps.append(
                {"type": "buy_ectoplasm", "name": "Buy Ectoplasm", "use_storage_gold": False, "multibox": True}
            )

        setup_steps.extend(
            [
                {"type": "random_travel", "name": f"Travel to {entrypoint_name}", "target_map_id": entrypoint_map_id},
                {"type": "summon_all_accounts", "name": "Summon Alts", "ms": 5000},
                {"type": "invite_all_accounts", "name": "Invite Alts"},
                {"type": "set_hard_mode", "enabled": bool(options.hard_mode)},
                {"type": "use_item", "name": "Use FoW Scroll", "model_id": FOW_SCROLL_MODEL_ID},
                {"type": "wait_map_change", "name": "Wait For FoW", "target_map_id": FOW_MAP_ID},
            ]
        )

        register_recipe_context(bot, "FoW Setup", total_steps=count_expanded_steps(setup_steps))
        total_registered_steps = register_repeated_steps(
            bot,
            recipe_name="FoWSetup",
            steps=setup_steps,
            register_step=lambda _bot, step, idx: _register_shared_step(_bot, step, idx, recipe_name="FoWSetup"),
        )
        _debug(debug_hook, f"Registered FoW setup with {total_registered_steps} steps.")

    phases: list[Phase] = [Phase("00. Setup: FoW Start Run", _fow_setup, anchor=True)]
    for idx, (key, title) in enumerate(FOW_QUEST_ORDER):
        phase_name = f"{idx + 2:02d}. Quest: {title}"
        phases.append(Quest(f"FoW/{key}", phase_name))

    _debug(debug_hook, f"Built phase list with {len(phases)} phases.")
    return phases


def apply_fow_runtime_properties(
    bot,
    options: ModularFowOptions,
    debug_hook: Optional[Callable[[str], None]] = None,
) -> None:
    properties = bot.Properties

    if properties.exists("auto_loot"):
        if options.auto_loot:
            properties.Enable("auto_loot")
        else:
            properties.Disable("auto_loot")

    for property_name in CONSUMABLE_PROPERTY_NAMES:
        if not properties.exists(property_name):
            continue

        try:
            properties.ApplyNow(property_name, "active", bool(options.use_consumables))
        except Exception as exc:
            _debug(debug_hook, f"Failed to apply active flag for {property_name}: {exc}")

        try:
            qty = CONSUMABLE_RESTOCK_DEFAULTS[property_name] if options.restock_consumables else 0
            properties.ApplyNow(property_name, "restock_quantity", int(qty))
        except Exception as exc:
            _debug(debug_hook, f"Failed to apply restock quantity for {property_name}: {exc}")


def create_modular_fow_bot(
    *,
    options: ModularFowOptions,
    main_ui=None,
    settings_ui=None,
    help_ui=None,
    debug_hook: Optional[Callable[[str], None]] = None,
) -> ModularBot:
    modular_bot = ModularBot(
        name="ModularFow",
        phases=build_fow_phases(options, debug_hook=debug_hook),
        loop=False,
        on_party_wipe="00. Setup: FoW Start Run",
        template="aggressive",
        use_custom_behaviors=True,
        main_ui=main_ui,
        settings_ui=settings_ui,
        help_ui=help_ui,
        config_draw_path=True,
        upkeep_auto_inventory_management_active=True,
        upkeep_summoning_stone_active=True,
        upkeep_grail_of_might_active=True,
        upkeep_essence_of_celerity_active=True,
        upkeep_armor_of_salvation_active=True,
        upkeep_war_supplies_active=True,
        upkeep_drake_kabob_active=True,
        upkeep_candy_corn_active=True,
        upkeep_grail_of_might_restock=3,
        upkeep_essence_of_celerity_restock=3,
        upkeep_armor_of_salvation_restock=3,
        upkeep_war_supplies_restock=3,
        upkeep_drake_kabob_restock=3,
        upkeep_candy_corn_restock=10,
    )

    base_start_coroutines = modular_bot.bot._start_coroutines

    def _start_coroutines_once():
        if getattr(modular_bot.bot, "_fow_coroutines_started", False):
            return
        base_start_coroutines()
        modular_bot.bot._fow_coroutines_started = True
        _debug(debug_hook, "Started upkeep/event coroutines once for FoW widget bot.")

    modular_bot.bot._start_coroutines = _start_coroutines_once
    modular_bot.bot._fow_coroutines_started = False
    return modular_bot
