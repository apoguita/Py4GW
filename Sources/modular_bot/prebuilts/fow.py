from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Optional

from Py4GWCoreLib.EnemyBlacklist import EnemyBlacklist
from Py4GWCoreLib.py4gwcorelib_src.Lootconfig_src import LootConfig
from Py4GWCoreLib.enums_src.Map_enums import name_to_map_id, outposts
from Py4GWCoreLib.enums_src.Item_enums import MaterialMap
from Py4GWCoreLib.enums_src.Model_enums import ModelID
from Sources.modular_bot import ModularBot
from Sources.modular_bot.phase import Phase
from Sources.modular_bot.recipes.actions_inventory import SUPPORTED_MAP_NPC_SELECTORS
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
EYE_OF_THE_NORTH_MAP_ID = 642
FOW_MAP_ID = int(name_to_map_id["The Fissure of Woe"])
FOW_SCROLL_MODEL_ID = int(ModelID.Passage_Scroll_Fow.value)
UNHOLY_TEXT_MODEL_ID = 2619

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


def _format_inventory_location_label(map_id: int) -> str:
    label = str(outposts.get(int(map_id), f"Map {int(map_id)}"))
    if label.endswith(" outpost"):
        label = label[: -len(" outpost")]
    return label


def _build_inventory_management_locations() -> dict[str, str]:
    locations: dict[str, str] = {"guild_hall": "Guild Hall"}
    for map_id in sorted(int(mid) for mid in SUPPORTED_MAP_NPC_SELECTORS.keys()):
        locations[f"map_{map_id}"] = _format_inventory_location_label(map_id)
    return locations


INVENTORY_MANAGEMENT_LOCATIONS: dict[str, str] = _build_inventory_management_locations()
DEFAULT_INVENTORY_MANAGEMENT_LOCATION_KEY = "guild_hall"
COMMON_MATERIAL_EXCLUDE_FOR_NON_CONS = {
    int(ModelID.Bone.value),
    int(ModelID.Pile_Of_Glittering_Dust.value),
    int(ModelID.Feather.value),
    int(ModelID.Iron_Ingot.value),
}
FOW_NON_CONS_COMMON_MATERIAL_MODELS = (
    ModelID.Bolt_Of_Cloth,
    ModelID.Chitin_Fragment,
    ModelID.Granite_Slab,
    ModelID.Plant_Fiber,
    ModelID.Scale,
    ModelID.Tanned_Hide_Square,
    ModelID.Wood_Plank,
)


@dataclass(slots=True)
class ModularFowOptions:
    hard_mode: bool = True
    use_consumables: bool = True
    restock_consumables: bool = True
    auto_loot: bool = True
    upkeep_auto_inventory_management_active: bool = False
    skip_merchant_actions: bool = False
    debug_logging: bool = False
    entrypoint: str = DEFAULT_FOW_ENTRYPOINT_KEY
    sell_non_cons_materials: bool = False
    sell_all_common_materials: bool = False
    buy_ectoplasm: bool = False
    inventory_management_location: str = DEFAULT_INVENTORY_MANAGEMENT_LOCATION_KEY


def _debug(debug_hook: Optional[Callable[[str], None]], message: str) -> None:
    if debug_hook is not None:
        debug_hook(message)


def _resolve_entrypoint(entrypoint: str) -> tuple[str, int]:
    key = str(entrypoint or DEFAULT_FOW_ENTRYPOINT_KEY).strip().lower()
    return FOW_ENTRYPOINTS.get(key, FOW_ENTRYPOINTS[DEFAULT_FOW_ENTRYPOINT_KEY])


def _resolve_inventory_management_location(location: str) -> tuple[str, str]:
    key = str(location or DEFAULT_INVENTORY_MANAGEMENT_LOCATION_KEY).strip().lower()
    # Backward compatibility with previous FoW-specific key.
    if key == "eye_of_the_north":
        key = f"map_{EYE_OF_THE_NORTH_MAP_ID}"
    resolved_key = key if key in INVENTORY_MANAGEMENT_LOCATIONS else DEFAULT_INVENTORY_MANAGEMENT_LOCATION_KEY
    return resolved_key, INVENTORY_MANAGEMENT_LOCATIONS[resolved_key]


def _build_inventory_setup_steps(location_key: str) -> list[dict]:
    if location_key != "guild_hall":
        try:
            target_map_id = int(str(location_key).split("_", 1)[1])
        except (IndexError, ValueError):
            target_map_id = EYE_OF_THE_NORTH_MAP_ID
        return [
            {
                "type": "random_travel",
                "name": f"Travel to {_format_inventory_location_label(target_map_id)}",
                "target_map_id": target_map_id,
            },
            {"type": "summon_all_accounts", "name": "Summon Alts to Inventory Outpost", "ms": 7000},
        ]

    return [
        {"type": "travel_gh", "name": "Travel to Guild Hall", "ms": 7000, "multibox": True}
    ]


def _resolve_materials_to_sell(options: ModularFowOptions) -> list[str] | None:
    if options.sell_all_common_materials:
        # None => let sell_materials use runtime material checks:
        # IsMaterial && !IsRareMaterial.
        return None
    if options.sell_non_cons_materials:
        return [
            material_name
            for model_id, material_name in MaterialMap.items()
            if model_id in FOW_NON_CONS_COMMON_MATERIAL_MODELS
        ]
    return []


def build_fow_phases(
    options: ModularFowOptions,
    debug_hook: Optional[Callable[[str], None]] = None,
) -> list[Phase]:
    def _fow_setup(bot) -> None:
        def _configure_cb_following_spread() -> None:
            try:
                from Py4GWCoreLib import GLOBAL_CACHE, ConsoleLog
                from Sources.oazix.CustomBehaviors.primitives.following_behavior_priority import (
                    FollowingBehaviorPriority,
                )
                from Sources.oazix.CustomBehaviors.primitives.parties.custom_behavior_party import (
                    CustomBehaviorParty,
                )

                party = CustomBehaviorParty()
                party.set_party_is_following_enabled(True)
                party.set_party_following_behavior_priority(FollowingBehaviorPriority.LOW_PRIORITY)

                manager = party.party_following_manager
                updated = 0
                for account in GLOBAL_CACHE.ShMem.GetAllAccountData():
                    email = str(getattr(account, "AccountEmail", "") or "").strip()
                    if not email:
                        continue
                    manager.initialize_account_forces(email)
                    current_leader = manager.get_is_attraction_leader_active(email)
                    current_enemies = manager.get_is_repulsion_enemies_active(email)
                    manager.set_account_forces(
                        email,
                        is_repulsion_allies_active=True,
                        is_attraction_leader_active=current_leader,
                        is_repulsion_enemies_active=current_enemies,
                    )
                    updated += 1

                ConsoleLog(
                    "FoWSetup",
                    f"CB following set to LOW_PRIORITY; allies repulsion enabled for {updated} account(s).",
                )
            except Exception as exc:
                _debug(debug_hook, f"Failed to configure CB following spread: {exc}")

        bot.States.AddCustomState(_configure_cb_following_spread, "Configure CB Following Spread")
        bot.States.AddCustomState(lambda: EnemyBlacklist().add_name("Wailing Lord"), "Blacklist Wailing Lord")
        bot.States.AddCustomState(
            lambda: LootConfig().AddToBlacklist(UNHOLY_TEXT_MODEL_ID),
            "Blacklist Unholy Text Loot",
        )
        entrypoint_name, entrypoint_map_id = _resolve_entrypoint(options.entrypoint)
        inventory_location_key, inventory_location_name = _resolve_inventory_management_location(
            options.inventory_management_location
        )
        materials_to_sell = _resolve_materials_to_sell(options)
        _debug(
            debug_hook,
            "Registering FoW setup steps "
            f"(hard_mode={options.hard_mode}, use_consumables={options.use_consumables}, "
            f"restock_consumables={options.restock_consumables}, auto_loot={options.auto_loot}, "
            f"upkeep_auto_inventory_management_active={options.upkeep_auto_inventory_management_active}, "
            f"skip_merchant_actions={options.skip_merchant_actions}, "
            f"entrypoint={entrypoint_name}, sell_non_cons_materials={options.sell_non_cons_materials}, "
            f"sell_all_common_materials={options.sell_all_common_materials}, buy_ectoplasm={options.buy_ectoplasm}, "
            f"inventory_management_location={inventory_location_name})",
        )
        setup_steps = [
            {"type": "leave_party", "name": "Leave Party", "multibox": True},
            {"type": "set_auto_looting", "enabled": bool(options.auto_loot)},
        ]

        if not options.skip_merchant_actions:
            setup_steps[1:1] = _build_inventory_setup_steps(inventory_location_key)

            for _ in range(3):
                setup_steps.append(
                    {"type": "restock_kits", "name": "Restock Kits", "id_kits": 2, "salvage_kits": 5, "multibox": True}
                )

            if options.use_consumables and options.restock_consumables:
                setup_steps.append({"type": "restock_cons"})

            if options.sell_all_common_materials or materials_to_sell:
                sell_step = {"type": "sell_materials", "name": "Sell Materials", "multibox": True, "ms": 5000}
                if materials_to_sell is not None:
                    sell_step["materials"] = materials_to_sell
                setup_steps.append(sell_step)

            setup_steps.append(
                {"type": "deposit_materials", "name": "Deposit Full Material Stacks", "multibox": True, "ms": 5000}
            )

            if options.buy_ectoplasm:
                setup_steps.append(
                    {"type": "buy_ectoplasm", "name": "Buy Ectoplasm", "use_storage_gold": False, "multibox": True, "ms": 5000}
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
        upkeep_auto_inventory_management_active=bool(options.upkeep_auto_inventory_management_active),
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
