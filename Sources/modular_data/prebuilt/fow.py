"""
fow module

This module is part of the modular runtime surface.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Optional

from Py4GWCoreLib.EnemyBlacklist import EnemyBlacklist
from Py4GWCoreLib.py4gwcorelib_src.Lootconfig_src import LootConfig
from Py4GWCoreLib.enums_src.Map_enums import name_to_map_id, outposts
from Py4GWCoreLib.enums_src.Item_enums import MaterialMap
from Py4GWCoreLib.enums_src.Model_enums import ModelID
from Py4GWCoreLib.modular import ModularBot
from Py4GWCoreLib.modular.phase import Phase
from Py4GWCoreLib.modular.actions import SUPPORTED_MAP_NPC_SELECTORS
from Py4GWCoreLib.modular.recipes import Quest
from Py4GWCoreLib.modular.recipes.modular_block import (
    build_inline_modular_phase,
    build_modular_block_execution_plan,
)


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
FOW_ENTRY_METHOD_SCROLL = "scroll"
FOW_ENTRY_METHOD_KNEEL = "kneel"
DEFAULT_FOW_ENTRY_METHOD_KEY = FOW_ENTRY_METHOD_SCROLL
FOW_TEMPLE_KNEEL_X = -2435.05
FOW_TEMPLE_KNEEL_Y = 18678.10
FOW_TEMPLE_ENTRY_DIALOG_ID = 0x86
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
FOW_CONS_COMMON_MATERIAL_MODELS = (
    ModelID.Plant_Fiber,
    ModelID.Pile_Of_Glittering_Dust,
    ModelID.Iron_Ingot,
    ModelID.Bone,
    ModelID.Feather,
)
FOW_NON_CONS_COMMON_MATERIAL_MODELS = (
    ModelID.Bolt_Of_Cloth,
    ModelID.Chitin_Fragment,
    ModelID.Granite_Slab,
    ModelID.Scale,
    ModelID.Tanned_Hide_Square,
    ModelID.Wood_Plank,
)


@dataclass(slots=True)
class ModularFowOptions:
    """
    M od ul ar Fo wO pt io ns class.
    
    Meta:
      Expose: true
      Audience: advanced
      Display: Modular Fow Options
      Purpose: Provide explicit modular runtime behavior and metadata.
      UserDescription: Internal class used by modular orchestration and step execution.
      Notes: Keep behavior explicit and side effects contained.
    """
    hard_mode: bool = True
    use_consumables: bool = True
    restock_consumables: bool = True
    auto_loot: bool = True
    upkeep_auto_inventory_management_active: bool = False
    skip_merchant_actions: bool = False
    use_merchant_rules_inventory: bool = False
    debug_logging: bool = False
    entrypoint: str = DEFAULT_FOW_ENTRYPOINT_KEY
    entry_method: str = DEFAULT_FOW_ENTRY_METHOD_KEY
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


def _resolve_entry_method(entry_method: str) -> str:
    key = str(entry_method or DEFAULT_FOW_ENTRY_METHOD_KEY).strip().lower()
    if key == FOW_ENTRY_METHOD_KNEEL:
        return FOW_ENTRY_METHOD_KNEEL
    return DEFAULT_FOW_ENTRY_METHOD_KEY


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
        {"type": "travel_gh", "name": "Travel to Guild Hall", "multibox": True, "per_account_delay_ms": 500},
        {
            "type": "wait_all_accounts_same_map",
            "name": "Wait For Alts In Guild Hall",
            "timeout_ms": 60000,
            "poll_ms": 500,
        },
    ]


def _resolve_materials_to_sell(options: ModularFowOptions) -> list[str] | None:
    if options.sell_non_cons_materials:
        return [
            material_name
            for model_id, material_name in MaterialMap.items()
            if model_id in FOW_NON_CONS_COMMON_MATERIAL_MODELS
        ]
    if options.sell_all_common_materials:
        # None => let sell_materials use runtime material checks:
        # IsMaterial && !IsRareMaterial.
        return None
    return []


def _resolve_materials_to_deposit(options: ModularFowOptions) -> list[str]:
    if not options.sell_non_cons_materials:
        return []
    return [
        material_name
        for model_id, material_name in MaterialMap.items()
        if model_id in FOW_CONS_COMMON_MATERIAL_MODELS
    ]


def build_fow_phases(
    options: ModularFowOptions,
    debug_hook: Optional[Callable[[str], None]] = None,
) -> list[Phase]:
    selected_entrypoint_name, selected_entrypoint_map_id = _resolve_entrypoint(options.entrypoint)
    entry_method = _resolve_entry_method(options.entry_method)
    entrypoint_name = selected_entrypoint_name
    entrypoint_map_id = selected_entrypoint_map_id
    if entry_method == FOW_ENTRY_METHOD_KNEEL:
        entrypoint_name = "Temple of the Ages"
        entrypoint_map_id = TEMPLE_OF_THE_AGES_MAP_ID

    inventory_location_key, inventory_location_name = _resolve_inventory_management_location(
        options.inventory_management_location
    )
    materials_to_sell = _resolve_materials_to_sell(options)
    materials_to_deposit = _resolve_materials_to_deposit(options)

    _debug(
        debug_hook,
        "Registering FoW setup steps "
        f"(hard_mode={options.hard_mode}, use_consumables={options.use_consumables}, "
        f"restock_consumables={options.restock_consumables}, auto_loot={options.auto_loot}, "
        f"upkeep_auto_inventory_management_active={options.upkeep_auto_inventory_management_active}, "
        f"skip_merchant_actions={options.skip_merchant_actions}, "
        f"use_merchant_rules_inventory={options.use_merchant_rules_inventory}, "
        f"entry_method={entry_method}, entrypoint={entrypoint_name}, "
        f"selected_entrypoint={selected_entrypoint_name}, "
        f"sell_non_cons_materials={options.sell_non_cons_materials}, "
        f"sell_all_common_materials={options.sell_all_common_materials}, buy_ectoplasm={options.buy_ectoplasm}, "
        f"inventory_management_location={inventory_location_name})",
    )

    setup_steps = [{"type": "leave_party", "name": "Leave Party", "multibox": True, "ms": 2000}]

    if not options.skip_merchant_actions:
        setup_steps.extend(_build_inventory_setup_steps(inventory_location_key))

    setup_steps.append({"type": "set_auto_looting", "enabled": bool(options.auto_loot)})

    if not options.skip_merchant_actions:
        if options.use_merchant_rules_inventory:
            setup_steps.append(
                {
                    "type": "merchant_rules_execute",
                    "name": "Merchant Rules Execute",
                    "multibox": True,
                    "local": True,
                    "ms": 5000,
                }
            )
        else:
            setup_steps.append({"type": "restock_kits", "name": "Restock Kits", "id_kits": 2, "salvage_kits": 5, "multibox": True})
            if options.use_consumables and options.restock_consumables:
                setup_steps.append({"type": "restock_cons"})
            if options.sell_all_common_materials or materials_to_sell:
                sell_step = {"type": "sell_materials", "name": "Sell Materials", "multibox": True, "ms": 5000}
                if materials_to_sell is not None:
                    sell_step["materials"] = materials_to_sell
                setup_steps.append(sell_step)
            if not options.sell_all_common_materials:
                deposit_step = {
                    "type": "deposit_materials",
                    "name": "Deposit Full Material Stacks",
                    "multibox": True,
                    "ms": 5000,
                }
                if materials_to_deposit:
                    deposit_step["name"] = "Deposit Cons Materials"
                    deposit_step["materials"] = materials_to_deposit
                    deposit_step["exact_quantity"] = 0
                    deposit_step["max_passes"] = 1
                    deposit_step["deposit_wait_ms"] = 120
                setup_steps.append(deposit_step)
            if options.buy_ectoplasm:
                setup_steps.append(
                    {"type": "buy_ectoplasm", "name": "Buy Ectoplasm", "use_storage_gold": False, "multibox": True, "ms": 5000}
                )

    setup_steps.extend(
        [
            {"type": "random_travel", "name": f"Travel to {entrypoint_name}", "target_map_id": entrypoint_map_id},
            {"type": "summon_all_accounts", "name": "Summon Alts", "ms": 8000},
            {"type": "invite_all_accounts", "name": "Invite Alts"},
            {"type": "invite_all_accounts", "name": "Invite Alts"},
            {"type": "enable_widgets", "name": "Enable HeroAI", "widgets": ["HeroAI"], "multibox": True, "ms": 1000},
            {"type": "set_combat_engine", "name": "Use HeroAI Combat Engine", "engine": "hero_ai"},
            {"type": "set_auto_following", "name": "Set HeroAI Following On", "enabled": True},
            {"type": "set_auto_combat", "name": "Set HeroAI Combat On", "enabled": True},
            {"type": "set_auto_looting", "name": "Set HeroAI Looting", "enabled": bool(options.auto_loot)},
            {"type": "set_hard_mode", "enabled": bool(options.hard_mode)},
        ]
    )

    if entry_method == FOW_ENTRY_METHOD_KNEEL:
        setup_steps.extend(
            [
                {"type": "move", "name": "Move to Temple Statue", "point": [FOW_TEMPLE_KNEEL_X, FOW_TEMPLE_KNEEL_Y], "ms": 750},
                {"type": "emote", "name": "Kneel", "command": "kneel", "ms": 4500},
                {"type": "dialog", "name": "Enter FoW via Temple Dialog", "point": [FOW_TEMPLE_KNEEL_X, FOW_TEMPLE_KNEEL_Y], "id": int(FOW_TEMPLE_ENTRY_DIALOG_ID), "ms": 1500},
                {"type": "wait_map_change", "name": "Wait For FoW", "target_map_id": FOW_MAP_ID},
            ]
        )
    else:
        setup_steps.extend(
            [
                {"type": "use_item", "name": "Use FoW Scroll", "model_id": FOW_SCROLL_MODEL_ID},
                {"type": "wait_map_change", "name": "Wait For FoW", "target_map_id": FOW_MAP_ID},
            ]
        )

    if options.use_consumables:
        setup_steps.extend(
            [
                {"type": "upkeep_cons", "name": "Upkeep Conset", "poll_ms": 5000},
                {"type": "upkeep_pcons", "name": "Upkeep Pcons", "multibox": True, "poll_ms": 5000},
            ]
        )

    def _setup_pre_hook(_bot) -> None:
        try:
            EnemyBlacklist().add_name("Wailing Lord")
        except Exception as exc:
            _debug(debug_hook, f"Failed to blacklist Wailing Lord: {exc}")
        try:
            LootConfig().AddToBlacklist(UNHOLY_TEXT_MODEL_ID)
        except Exception as exc:
            _debug(debug_hook, f"Failed to blacklist Unholy Text loot: {exc}")

    setup_phase = build_inline_modular_phase(
        display_name="FoW Setup",
        name="00. Setup: FoW Start Run",
        steps=setup_steps,
        recipe_name="FoWSetup",
        anchor=True,
        pre_run_hook=_setup_pre_hook,
        pre_run_name="FoW Setup Pre Hook",
    )

    reward_plan = build_modular_block_execution_plan(
        "FoW/reward_time",
        kind="quests",
        recipe_name="Quest",
    )
    reward_steps = list(reward_plan.steps)
    reward_steps.extend(
        [
            {"type": "wait_map_load", "name": "Wait Return Map Load", "target_map_id": entrypoint_map_id},
            {"type": "wait", "name": "Post Reward Wait", "ms": 5000},
        ]
    )
    reward_phase = build_inline_modular_phase(
        display_name=str(reward_plan.display_name or "Reward Time"),
        name="",
        steps=reward_steps,
        recipe_name="Quest",
        inventory_guard_source=reward_plan.source_data,
    )

    phases: list[Phase] = [setup_phase]
    for idx, (key, title) in enumerate(FOW_QUEST_ORDER):
        phase_name = f"{idx + 2:02d}. Quest: {title}"
        if key == "reward_time":
            reward_phase.name = phase_name
            phases.append(reward_phase)
        else:
            phases.append(Quest(f"FoW/{key}", phase_name))

    _debug(debug_hook, f"Built phase list with {len(phases)} phases.")
    return phases


def apply_fow_runtime_properties(
    bot,
    options: ModularFowOptions,
    debug_hook: Optional[Callable[[str], None]] = None,
) -> None:
    properties = bot.Properties
    hero_ai_enabled = False
    try:
        from Py4GWCoreLib.py4gwcorelib_src.WidgetManager import get_widget_handler

        widget_handler = get_widget_handler()
        hero_ai_enabled = bool(widget_handler.is_widget_enabled("HeroAI"))
    except Exception as exc:
        _debug(debug_hook, f"Could not resolve widget engine state for FoW runtime properties: {exc}")

    # HeroAI runtime: align alt HeroAI backend options with modular desired
    # runtime toggles. Do not force-follow off here.
    if hero_ai_enabled:
        try:
            from Py4GWCoreLib import GLOBAL_CACHE, Player
            from Py4GWCoreLib.GlobalCache.shared_memory_src.Globals import SHMEM_MAX_NUMBER_OF_SKILLS

            my_email = str(Player.GetAccountEmail() or "")
            me = GLOBAL_CACHE.ShMem.GetAccountDataFromEmail(my_email)
            cfg = getattr(bot, "config", None)
            desired_following = bool(getattr(cfg, "_modular_desired_auto_following", True))
            desired_combat = bool(getattr(cfg, "_modular_desired_auto_combat", True))
            desired_looting = bool(getattr(cfg, "_modular_desired_auto_looting", bool(options.auto_loot)))
            updated = 0

            if me is not None:
                for account in GLOBAL_CACHE.ShMem.GetAllAccountData():
                    same_party = int(account.AgentPartyData.PartyID) == int(me.AgentPartyData.PartyID)
                    if not same_party:
                        continue

                    account_email = str(getattr(account, "AccountEmail", "") or "")
                    if not account_email:
                        continue
                    options_obj = GLOBAL_CACHE.ShMem.GetHeroAIOptionsFromEmail(account_email)
                    if options_obj is None:
                        continue

                    options_obj.Following = bool(desired_following)
                    options_obj.Avoidance = bool(desired_combat)
                    options_obj.Combat = bool(desired_combat)
                    options_obj.Targeting = bool(desired_combat)
                    options_obj.Looting = bool(desired_looting)
                    for skill_index in range(SHMEM_MAX_NUMBER_OF_SKILLS):
                        options_obj.Skills[skill_index] = bool(desired_combat)
                    GLOBAL_CACHE.ShMem.SetHeroAIOptionsByEmail(account_email, options_obj)
                    updated += 1

            _debug(
                debug_hook,
                f"FoW HeroAI runtime options updated for {updated} account(s): "
                f"Following={desired_following}, Combat={desired_combat}, "
                f"Targeting={desired_combat}, Looting={desired_looting}.",
            )
        except Exception as exc:
            _debug(debug_hook, f"Failed to apply HeroAI follow/combat runtime options: {exc}")

    # Let external engines own combat/loot execution.
    # Keep built-in upkeepers disabled to avoid pathing/combat/loot contention.
    if properties.exists("auto_combat") and hero_ai_enabled:
        properties.Disable("auto_combat")

    if properties.exists("auto_loot"):
        if hero_ai_enabled:
            properties.ApplyNow("auto_loot", "active", bool(options.auto_loot))
        elif options.auto_loot:
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
    _debug(
        debug_hook,
        "FoW combat backend profile: backend=hero_ai, template=multibox_aggressive",
    )

    modular_bot = ModularBot(
        name="ModularFow",
        phases=build_fow_phases(options, debug_hook=debug_hook),
        loop=True,
        on_party_wipe="00. Setup: FoW Start Run",
        template="multibox_aggressive",
        start_coroutines_once=True,
        main_ui=main_ui,
        settings_ui=settings_ui,
        help_ui=help_ui,
        debug_logging=bool(options.debug_logging),
        config_draw_path=True,
        upkeep_hero_ai_active=True,
        upkeep_auto_inventory_management_active=bool(options.upkeep_auto_inventory_management_active),
        upkeep_summoning_stone_active=True,
        upkeep_grail_of_might_active=False,
        upkeep_essence_of_celerity_active=False,
        upkeep_armor_of_salvation_active=False,
        upkeep_war_supplies_active=False,
        upkeep_drake_kabob_active=False,
        upkeep_golden_egg_active=False,
        upkeep_candy_corn_active=False,
        upkeep_grail_of_might_restock=3,
        upkeep_essence_of_celerity_restock=3,
        upkeep_armor_of_salvation_restock=3,
        upkeep_war_supplies_restock=3,
        upkeep_drake_kabob_restock=3,
        upkeep_candy_corn_restock=10,
    )
    return modular_bot
