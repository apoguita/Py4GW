"""
BT routines file notes
======================

This file is both:
- part of the public BT grouped routine surface
- a discovery source for higher-level tooling

Authoring and discovery conventions
-----------------------------------
- Keep existing class names as the system-level grouping surface.
- Use `PascalCase` for public/front-facing routine methods.
- Use `snake_case` for helper/internal methods.
- Use `_snake_case` for explicitly private helpers.
- Keep helper/internal methods out of the public discovery surface.

Routine docstring template
--------------------------
Each user-facing routine method should use:
- a free human-readable description first
- a structured `Meta:` block after it

Template:

    \"\"\"
    One or more human-readable paragraphs explaining what the routine builds.

    Meta:
      Expose: true
      Audience: beginner
      Display: Outpost Imp Service
      Purpose: Build a tree that runs an upkeep or service routine.
      UserDescription: Use this when you want a background upkeep tree beside the main planner.
      Notes: Keep metadata single-line. Structural truth should stay in code.
    \"\"\"

Docstring parsing rules
-----------------------
- Only the `Meta:` section is intended for machine parsing.
- Keep metadata lines single-line and in `Key: Value` form.
- Unknown keys should be safe for tooling to ignore.
- Prefer adding presentation/help metadata in docstrings instead of duplicating
  structural metadata that already exists in code.
"""

from __future__ import annotations

from ...Agent import Agent
from ...GlobalCache import GLOBAL_CACHE
from ...Map import Map
from ...Player import Player
from ...Py4GWcorelib import ConsoleLog, Console
from ...Item import Bag
from ...enums import CONSUMABLE_MODELID_TO_EFFECT_NAME
from ...enums import SharedCommandType
from ...enums_src.Model_enums import ModelID
from ...py4gwcorelib_src.BehaviorTree import BehaviorTree
from ..Checks import Checks
from .composite import BTComposite
from .items import BTItems


def _log(source: str, message: str, *, log: bool = False, message_type=Console.MessageType.Info) -> None:
    ConsoleLog(source, message, message_type, log=log)


def _fail_log(source: str, message: str, message_type=Console.MessageType.Warning) -> None:
    ConsoleLog(source, message, message_type, log=True)


class BTUpkeepers:
    """
    Public BT helper group for upkeep and background service routines.

    Meta:
      Expose: true
      Audience: advanced
      Display: Upkeepers
      Purpose: Group public BT routines related to upkeep services and background support flows.
      UserDescription: Built-in BT helper group for upkeep and service-style routines.
      Notes: Public `PascalCase` methods in this class are discovery candidates when marked exposed.
    """
    SUGAR_RUSH_SHORT_EFFECT_ID = 1860
    SUGAR_RUSH_MEDIUM_EFFECT_ID = 1323
    SUGAR_RUSH_LONG_EFFECT_ID = 1612
    SUGAR_RUSH_MAD_KING_EFFECT_ID = 3070
    SUGAR_JOLT_SHORT_EFFECT_ID = 1916
    SUGAR_JOLT_LONG_EFFECT_ID = 1933
    SUGAR_RUSH_SHORT_MS = 1 * 60 * 1000
    SUGAR_RUSH_MEDIUM_MS = 3 * 60 * 1000
    SUGAR_RUSH_LONG_MS = 5 * 60 * 1000
    SUGAR_JOLT_SHORT_MS = 2 * 60 * 1000
    SUGAR_JOLT_LONG_MS = 5 * 60 * 1000
    TONIC_TIPSINESS_EFFECT_ID = 3402
    TONIC_TIPSINESS_FALLBACK_MS = 5000
    PARTY_ITEM_DEFAULT_COOLDOWN_MS = 1000
    CRATE_FIREWORKS_DISPLAY_MS = 10 * 60 * 1000
    DISCO_BALL_DISPLAY_MS = 3 * 60 * 1000

    CONSUMABLE_UPKEEP_PRESETS = {
        "armor_of_salvation": {
            "rule": "effect_upkeep",
            "model_id": ModelID.Armor_Of_Salvation.value,
            "effect_name": "Armor_of_Salvation_item_effect",
        },
        "essence_of_celerity": {
            "rule": "effect_upkeep",
            "model_id": ModelID.Essence_Of_Celerity.value,
            "effect_name": "Essence_of_Celerity_item_effect",
        },
        "grail_of_might": {
            "rule": "effect_upkeep",
            "model_id": ModelID.Grail_Of_Might.value,
            "effect_name": "Grail_of_Might_item_effect",
        },
        "blue_rock_candy": {
            "rule": "effect_upkeep",
            "model_id": ModelID.Blue_Rock_Candy.value,
            "effect_name": "Blue_Rock_Candy_Rush",
            "require_effect_id": True,
        },
        "green_rock_candy": {
            "rule": "effect_upkeep",
            "model_id": ModelID.Green_Rock_Candy.value,
            "effect_name": "Green_Rock_Candy_Rush",
            "require_effect_id": True,
        },
        "red_rock_candy": {
            "rule": "effect_upkeep",
            "model_id": ModelID.Red_Rock_Candy.value,
            "effect_name": "Red_Rock_Candy_Rush",
            "require_effect_id": True,
        },
        "birthday_cupcake": {
            "rule": "effect_upkeep",
            "model_id": ModelID.Birthday_Cupcake.value,
            "effect_name": "Birthday_Cupcake_skill",
        },
        "bowl_of_skalefin_soup": {
            "rule": "effect_upkeep",
            "model_id": ModelID.Bowl_Of_Skalefin_Soup.value,
            "effect_name": "Skale_Vigor",
        },
        "candy_apple": {
            "rule": "effect_upkeep",
            "model_id": ModelID.Candy_Apple.value,
            "effect_name": "Candy_Apple_skill",
        },
        "candy_corn": {
            "rule": "effect_upkeep",
            "model_id": ModelID.Candy_Corn.value,
            "effect_name": "Candy_Corn_skill",
        },
        "drake_kabob": {
            "rule": "effect_upkeep",
            "model_id": ModelID.Drake_Kabob.value,
            "effect_name": "Drake_Skin",
        },
        "golden_egg": {
            "rule": "effect_upkeep",
            "model_id": ModelID.Golden_Egg.value,
            "effect_name": "Golden_Egg_skill",
        },
        "pahnai_salad": {
            "rule": "effect_upkeep",
            "model_id": ModelID.Pahnai_Salad.value,
            "effect_name": "Pahnai_Salad_item_effect",
        },
        "slice_of_pumpkin_pie": {
            "rule": "effect_upkeep",
            "model_id": ModelID.Slice_Of_Pumpkin_Pie.value,
            "effect_name": "Pie_Induced_Ecstasy",
        },
        "war_supplies": {
            "rule": "effect_upkeep",
            "model_id": ModelID.War_Supplies.value,
            "effect_name": "Well_Supplied",
        },
        "honeycomb": {
            "rule": "party_morale",
            "model_id": ModelID.Honeycomb.value,
            "target_morale": 110,
            "party_wide_morale": True,
            "aftercast_ms": 750,
        },
        "rainbow_candy_cane": {
            "rule": "party_morale",
            "model_id": ModelID.Rainbow_Candy_Cane.value,
            "target_morale": 110,
            "party_wide_morale": True,
            "aftercast_ms": 750,
        },
        "elixir_of_valor": {
            "rule": "party_morale",
            "model_id": ModelID.Elixir_Of_Valor.value,
            "target_morale": 110,
            "party_wide_morale": True,
            "aftercast_ms": 750,
        },
        "powerstone_of_courage": {
            "rule": "party_morale",
            "model_id": ModelID.Powerstone_Of_Courage.value,
            "target_morale": 110,
            "party_wide_morale": True,
            "aftercast_ms": 750,
        },
        "four_leaf_clover": {
            "rule": "party_morale",
            "model_id": ModelID.Four_Leaf_Clover.value,
            "target_morale": 100,
            "party_wide_morale": True,
            "aftercast_ms": 750,
        },
        "oath_of_purity": {
            "rule": "party_morale",
            "model_id": ModelID.Oath_Of_Purity.value,
            "target_morale": 100,
            "party_wide_morale": True,
            "aftercast_ms": 750,
        },
        "pumpkin_cookie": {
            "rule": "self_morale",
            "model_id": ModelID.Pumpkin_Cookie.value,
            "target_morale": 110,
            "aftercast_ms": 750,
        },
        "seal_of_the_dragon_empire": {
            "rule": "self_morale",
            "model_id": ModelID.Seal_Of_The_Dragon_Empire.value,
            "target_morale": 110,
            "aftercast_ms": 750,
        },
        "shining_blade_ration": {
            "rule": "self_morale",
            "model_id": ModelID.Shining_Blade_Ration.value,
            "target_morale": 100,
            "aftercast_ms": 750,
        },
        "refined_jelly": {
            "rule": "self_morale",
            "model_id": ModelID.Refined_Jelly.value,
            "target_morale": 100,
            "aftercast_ms": 750,
        },
        "wintergreen_candy_cane": {
            "rule": "self_morale",
            "model_id": ModelID.Wintergreen_Candy_Cane.value,
            "target_morale": 100,
            "aftercast_ms": 750,
        },
        "peppermint_candy_cane": {
            "rule": "self_morale",
            "model_id": ModelID.Peppermint_Candy_Cane.value,
            "target_morale": 100,
            "aftercast_ms": 750,
        },
        "chocolate_bunny": {
            "rule": "city_speed",
            "model_id": ModelID.Chocolate_Bunny.value,
            "use_where": "outpost",
            "effect_id": SUGAR_JOLT_LONG_EFFECT_ID,
            "require_effect_id": True,
            "fallback_duration_ms": SUGAR_JOLT_LONG_MS,
        },
        "creme_brulee": {
            "rule": "city_speed",
            "model_id": ModelID.Creme_Brulee.value,
            "use_where": "outpost",
            "effect_id": SUGAR_JOLT_LONG_EFFECT_ID,
            "require_effect_id": True,
            "fallback_duration_ms": SUGAR_JOLT_LONG_MS,
        },
        "fruitcake": {
            "rule": "city_speed",
            "model_id": ModelID.Fruitcake.value,
            "use_where": "outpost",
            "effect_id": SUGAR_RUSH_MEDIUM_EFFECT_ID,
            "require_effect_id": True,
            "fallback_duration_ms": SUGAR_RUSH_MEDIUM_MS,
        },
        "jar_of_honey": {
            "rule": "city_speed",
            "model_id": ModelID.Jar_Of_Honey.value,
            "use_where": "outpost",
            "effect_id": SUGAR_RUSH_LONG_EFFECT_ID,
            "fallback_duration_ms": SUGAR_RUSH_LONG_MS,
        },
        "krytan_lokum": {
            "rule": "city_speed",
            "model_id": ModelID.Krytan_Lokum.value,
            "use_where": "outpost",
            "effect_ids": [
                SUGAR_RUSH_SHORT_EFFECT_ID,
                SUGAR_RUSH_MEDIUM_EFFECT_ID,
                SUGAR_RUSH_LONG_EFFECT_ID,
                SUGAR_RUSH_MAD_KING_EFFECT_ID,
            ],
            "fallback_duration_ms": SUGAR_RUSH_MEDIUM_MS,
        },
        "mandragor_root_cake": {
            "rule": "city_speed",
            "model_id": ModelID.Mandragor_Root_Cake.value,
            "use_where": "outpost",
            "effect_ids": [
                SUGAR_RUSH_SHORT_EFFECT_ID,
                SUGAR_RUSH_MEDIUM_EFFECT_ID,
                SUGAR_RUSH_LONG_EFFECT_ID,
                SUGAR_RUSH_MAD_KING_EFFECT_ID,
            ],
            "fallback_duration_ms": SUGAR_RUSH_MEDIUM_MS,
        },
        "delicious_cake": {
            "rule": "city_speed",
            "model_id": ModelID.Delicious_Cake.value,
            "use_where": "outpost",
            "effect_ids": [
                SUGAR_RUSH_SHORT_EFFECT_ID,
                SUGAR_RUSH_MEDIUM_EFFECT_ID,
                SUGAR_RUSH_LONG_EFFECT_ID,
                SUGAR_RUSH_MAD_KING_EFFECT_ID,
            ],
            "fallback_duration_ms": SUGAR_RUSH_MEDIUM_MS,
        },
        "minitreat_of_purity": {
            "rule": "city_speed",
            "model_id": ModelID.Minitreat_Of_Purity.value,
            "use_where": "outpost",
            "effect_ids": [
                SUGAR_RUSH_SHORT_EFFECT_ID,
                SUGAR_RUSH_MEDIUM_EFFECT_ID,
                SUGAR_RUSH_LONG_EFFECT_ID,
                SUGAR_RUSH_MAD_KING_EFFECT_ID,
            ],
            "fallback_duration_ms": SUGAR_RUSH_MEDIUM_MS,
        },
        "red_bean_cake": {
            "rule": "city_speed",
            "model_id": ModelID.Red_Bean_Cake.value,
            "use_where": "outpost",
            "effect_id": SUGAR_RUSH_MEDIUM_EFFECT_ID,
            "require_effect_id": True,
            "fallback_duration_ms": SUGAR_RUSH_MEDIUM_MS,
        },
        "sugary_blue_drink": {
            "rule": "city_speed",
            "model_id": ModelID.Sugary_Blue_Drink.value,
            "use_where": "outpost",
            "effect_id": SUGAR_JOLT_SHORT_EFFECT_ID,
            "fallback_duration_ms": SUGAR_JOLT_SHORT_MS,
        },
        "aged_dwarven_ale": {
            "rule": "alcohol",
            "model_id": ModelID.Aged_Dwarven_Ale.value,
            "use_where": "both",
            "target_alcohol_level": 2,
        },
        "aged_hunters_ale": {
            "rule": "alcohol",
            "model_id": ModelID.Aged_Hunters_Ale.value,
            "use_where": "both",
            "target_alcohol_level": 2,
        },
        "bottle_of_grog": {
            "rule": "alcohol",
            "model_id": ModelID.Bottle_Of_Grog.value,
            "effect_name": "Yo_Ho_Ho_and_a_Bottle_of_Grog",
            "use_where": "both",
            "target_alcohol_level": 2,
        },
        "flask_of_firewater": {
            "rule": "alcohol",
            "model_id": ModelID.Flask_Of_Firewater.value,
            "use_where": "both",
            "target_alcohol_level": 2,
        },
        "keg_of_aged_hunters_ale": {
            "rule": "alcohol",
            "model_id": ModelID.Keg_Of_Aged_Hunters_Ale.value,
            "use_where": "both",
            "target_alcohol_level": 2,
        },
        "krytan_brandy": {
            "rule": "alcohol",
            "model_id": ModelID.Krytan_Brandy.value,
            "use_where": "both",
            "target_alcohol_level": 2,
        },
        "spiked_eggnog": {
            "rule": "alcohol",
            "model_id": ModelID.Spiked_Eggnog.value,
            "use_where": "both",
            "target_alcohol_level": 2,
        },
        "bottle_of_rice_wine": {
            "rule": "alcohol",
            "model_id": ModelID.Bottle_Of_Rice_Wine.value,
            "use_where": "both",
            "target_alcohol_level": 2,
        },
        "eggnog": {
            "rule": "alcohol",
            "model_id": ModelID.Eggnog.value,
            "use_where": "both",
            "target_alcohol_level": 2,
        },
        "dwarven_ale": {
            "rule": "alcohol",
            "model_id": ModelID.Dwarven_Ale.value,
            "use_where": "both",
            "target_alcohol_level": 2,
        },
        "hard_apple_cider": {
            "rule": "alcohol",
            "model_id": ModelID.Hard_Apple_Cider.value,
            "use_where": "both",
            "target_alcohol_level": 2,
        },
        "hunters_ale": {
            "rule": "alcohol",
            "model_id": ModelID.Hunters_Ale.value,
            "use_where": "both",
            "target_alcohol_level": 2,
        },
        "bottle_of_juniberry_gin": {
            "rule": "alcohol",
            "model_id": ModelID.Bottle_Of_Juniberry_Gin.value,
            "use_where": "both",
            "target_alcohol_level": 2,
        },
        "shamrock_ale": {
            "rule": "alcohol",
            "model_id": ModelID.Shamrock_Ale.value,
            "use_where": "both",
            "target_alcohol_level": 2,
        },
        "bottle_of_vabbian_wine": {
            "rule": "alcohol",
            "model_id": ModelID.Bottle_Of_Vabbian_Wine.value,
            "use_where": "both",
            "target_alcohol_level": 2,
        },
        "vial_of_absinthe": {
            "rule": "alcohol",
            "model_id": ModelID.Vial_Of_Absinthe.value,
            "use_where": "both",
            "target_alcohol_level": 2,
        },
        "witchs_brew": {
            "rule": "alcohol",
            "model_id": ModelID.Witchs_Brew.value,
            "use_where": "both",
            "target_alcohol_level": 2,
        },
        "zehtukas_jug": {
            "rule": "alcohol",
            "model_id": ModelID.Zehtukas_Jug.value,
            "use_where": "both",
            "target_alcohol_level": 2,
        },
        "bottle_rocket": {
            "rule": "party_item",
            "model_id": ModelID.Bottle_Rocket.value,
            "use_where": "party_items",
            "fallback_duration_ms": PARTY_ITEM_DEFAULT_COOLDOWN_MS,
        },
        "champagne_popper": {
            "rule": "party_item",
            "model_id": ModelID.Champagne_Popper.value,
            "use_where": "party_items",
            "fallback_duration_ms": PARTY_ITEM_DEFAULT_COOLDOWN_MS,
        },
        "ghost_in_the_box": {
            "rule": "party_item",
            "model_id": ModelID.Ghost_In_The_Box.value,
            "use_where": "party_items",
            "fallback_duration_ms": PARTY_ITEM_DEFAULT_COOLDOWN_MS,
        },
        "snowman_summoner": {
            "rule": "party_item",
            "model_id": ModelID.Snowman_Summoner.value,
            "use_where": "party_items",
            "fallback_duration_ms": PARTY_ITEM_DEFAULT_COOLDOWN_MS,
        },
        "sparkler": {
            "rule": "party_item",
            "model_id": ModelID.Sparkler.value,
            "use_where": "party_items",
            "fallback_duration_ms": PARTY_ITEM_DEFAULT_COOLDOWN_MS,
        },
        "squash_serum": {
            "rule": "party_item",
            "model_id": ModelID.Squash_Serum.value,
            "use_where": "party_items",
            "fallback_duration_ms": PARTY_ITEM_DEFAULT_COOLDOWN_MS,
        },
        "beetle_juice_tonic": {
            "rule": "party_tonic",
            "model_id": ModelID.Beetle_Juice_Tonic.value,
            "use_where": "party_items",
            "blocked_effect_id": TONIC_TIPSINESS_EFFECT_ID,
            "fallback_duration_ms": TONIC_TIPSINESS_FALLBACK_MS,
        },
        "cottontail_tonic": {
            "rule": "party_tonic",
            "model_id": ModelID.Cottontail_Tonic.value,
            "use_where": "party_items",
            "blocked_effect_id": TONIC_TIPSINESS_EFFECT_ID,
            "fallback_duration_ms": TONIC_TIPSINESS_FALLBACK_MS,
        },
        "frosty_tonic": {
            "rule": "party_tonic",
            "model_id": ModelID.Frosty_Tonic.value,
            "use_where": "party_items",
            "blocked_effect_id": TONIC_TIPSINESS_EFFECT_ID,
            "fallback_duration_ms": TONIC_TIPSINESS_FALLBACK_MS,
        },
        "mischievous_tonic": {
            "rule": "party_tonic",
            "model_id": ModelID.Mischievious_Tonic.value,
            "use_where": "party_items",
            "blocked_effect_id": TONIC_TIPSINESS_EFFECT_ID,
            "fallback_duration_ms": TONIC_TIPSINESS_FALLBACK_MS,
        },
        "sinister_automatonic": {
            "rule": "party_tonic",
            "model_id": ModelID.Sinister_Automatonic_Tonic.value,
            "use_where": "party_items",
            "blocked_effect_id": TONIC_TIPSINESS_EFFECT_ID,
            "fallback_duration_ms": TONIC_TIPSINESS_FALLBACK_MS,
        },
        "transmogrifier_tonic": {
            "rule": "party_tonic",
            "model_id": ModelID.Transmogrifier_Tonic.value,
            "use_where": "party_items",
            "blocked_effect_id": TONIC_TIPSINESS_EFFECT_ID,
            "fallback_duration_ms": TONIC_TIPSINESS_FALLBACK_MS,
        },
        "yuletide_tonic": {
            "rule": "party_tonic",
            "model_id": ModelID.Yuletide_Tonic.value,
            "use_where": "party_items",
            "blocked_effect_id": TONIC_TIPSINESS_EFFECT_ID,
            "fallback_duration_ms": TONIC_TIPSINESS_FALLBACK_MS,
        },
        "crate_of_fireworks": {
            "rule": "party_item",
            "model_id": ModelID.Crate_Of_Fireworks.value,
            "use_where": "party_items",
            "fallback_duration_ms": CRATE_FIREWORKS_DISPLAY_MS,
        },
        "disco_ball": {
            "rule": "party_item",
            "model_id": ModelID.Disco_Ball.value,
            "use_where": "party_items",
            "fallback_duration_ms": DISCO_BALL_DISPLAY_MS,
        },
        "party_beacon": {
            "rule": "party_item",
            "model_id": ModelID.Party_Beacon.value,
            "use_where": "party_items",
            "fallback_duration_ms": PARTY_ITEM_DEFAULT_COOLDOWN_MS,
        },
    }
    def _service_tick_due(node: BehaviorTree.Node, state_key: str, check_interval_ms: int) -> bool:
        from ...Py4GWcorelib import Utils

        state = node.blackboard.setdefault(
            state_key,
            {
                "last_attempt_ms": 0,
            },
        )
        now = int(Utils.GetBaseTimestamp())
        if now - int(state["last_attempt_ms"]) < max(0, int(check_interval_ms)):
            return False
        state["last_attempt_ms"] = now
        return True

    @staticmethod
    def _can_run_local_consumable_service() -> bool:
        if Map.IsMapLoading() or not Checks.Map.MapValid() or not Map.IsMapReady():
            return False
        if Agent.IsDead(Player.GetAgentID()):
            return False
        return True

    @staticmethod
    def _can_use_consumable_here(use_where: str) -> bool:
        use_where = str(use_where or "explorable").strip().lower()
        if use_where == "both":
            return Map.IsExplorable() or Map.IsOutpost()
        if use_where in ("outpost", "city", "town"):
            return Map.IsOutpost()
        if use_where in ("party_items", "any"):
            return Map.IsExplorable() or Map.IsOutpost()
        return Map.IsExplorable()

    @staticmethod
    def _min_party_morale() -> int | None:
        try:
            entries = GLOBAL_CACHE.ShMem.GetSharedPartyMorale() or []
            valid_morale = [int(morale) for _, morale in entries if int(morale or 0) > 0]
            if not valid_morale:
                return None
            return min(valid_morale)
        except Exception:
            return None

    @staticmethod
    def _party_morale_debug_rows() -> list[dict[str, object]]:
        current_party_id = int(GLOBAL_CACHE.Party.GetPartyID() or 0)
        current_map_signature = (
            int(Map.GetMapID() or 0),
            int(Map.GetRegion()[0] or 0),
            int(Map.GetDistrict() or 0),
            int(Map.GetLanguage()[0] or 0),
        )
        rows: list[dict[str, object]] = []
        for account in GLOBAL_CACHE.ShMem.GetAllActiveSlotsData() or []:
            if not account or not bool(getattr(account, 'IsSlotActive', False)):
                continue
            if bool(getattr(account, 'IsPet', False)) or bool(getattr(account, 'IsNPC', False)):
                continue
            if not (bool(getattr(account, 'IsAccount', False)) or bool(getattr(account, 'IsHero', False))):
                continue
            if int(getattr(getattr(account, 'AgentPartyData', None), 'PartyID', 0) or 0) != current_party_id:
                continue
            account_map_signature = (
                int(getattr(getattr(getattr(account, 'AgentData', None), 'Map', None), 'MapID', 0) or 0),
                int(getattr(getattr(getattr(account, 'AgentData', None), 'Map', None), 'Region', 0) or 0),
                int(getattr(getattr(getattr(account, 'AgentData', None), 'Map', None), 'District', 0) or 0),
                int(getattr(getattr(getattr(account, 'AgentData', None), 'Map', None), 'Language', 0) or 0),
            )
            if account_map_signature != current_map_signature:
                continue
            morale = int(getattr(getattr(account, 'AgentData', None), 'Morale', 0) or 0)
            if morale <= 0:
                continue
            rows.append(
                {
                    'name': str(getattr(getattr(account, 'AgentData', None), 'CharacterName', '') or '<unnamed>'),
                    'agent_id': int(getattr(getattr(account, 'AgentData', None), 'AgentID', 0) or 0),
                    'party_position': int(getattr(getattr(account, 'AgentPartyData', None), 'PartyPosition', -1) or -1),
                    'party_id': int(getattr(getattr(account, 'AgentPartyData', None), 'PartyID', 0) or 0),
                    'morale': morale,
                    'kind': 'hero' if bool(getattr(account, 'IsHero', False)) else 'account',
                }
            )
        rows.sort(key=lambda row: (int(row['party_position']), str(row['kind']), int(row['agent_id'])))
        return rows

    @staticmethod
    def _get_party_morale_debug_snapshot() -> dict[str, object]:
        raw_entries: list[tuple[int, int]] = []
        shared_error = ''
        try:
            raw_entries = list(GLOBAL_CACHE.ShMem.GetSharedPartyMorale() or [])
        except Exception as exc:
            shared_error = str(exc)

        valid_morale = [int(morale) for _, morale in raw_entries if int(morale or 0) > 0]
        player_agent_id = int(Player.GetAgentID() or 0)
        shared_player_morale = next(
            (int(morale) for agent_id, morale in raw_entries if int(agent_id or 0) == player_agent_id and int(morale or 0) > 0),
            None,
        )
        return {
            'party_id': int(GLOBAL_CACHE.Party.GetPartyID() or 0),
            'player_agent_id': player_agent_id,
            'player_morale': shared_player_morale,
            'map_id': int(Map.GetMapID() or 0),
            'region': int(Map.GetRegion()[0] or 0),
            'district': int(Map.GetDistrict() or 0),
            'language': int(Map.GetLanguage()[0] or 0),
            'shared_entries': raw_entries,
            'shared_rows': BTUpkeepers._party_morale_debug_rows(),
            'shared_min_morale': min(valid_morale) if valid_morale else None,
            'shared_error': shared_error,
        }

    @staticmethod
    def _format_party_morale_snapshot(
        snapshot: dict[str, object],
        *,
        target_morale: int | None,
    ) -> str:
        shared_rows = list(snapshot.get('shared_rows', []) or [])
        shared_entries = list(snapshot.get('shared_entries', []) or [])
        target_value = int(target_morale or 0)
        below_target_rows = [
            row for row in shared_rows if target_morale is not None and int(row.get('morale', 0) or 0) < target_value
        ]
        rows_summary = ", ".join(
            (
                f"pos={int(row['party_position'])} agent={int(row['agent_id'])} morale={int(row['morale'])} "
                f"kind={row['kind']} name={row['name']}"
            )
            for row in shared_rows
        ) or "<no valid shared rows>"
        below_target_summary = ", ".join(
            (
                f"pos={int(row['party_position'])} agent={int(row['agent_id'])} morale={int(row['morale'])} "
                f"kind={row['kind']} name={row['name']}"
            )
            for row in below_target_rows
        ) or "<none>"
        raw_entries_summary = ", ".join(
            f"agent={int(agent_id)} morale={int(morale)}" for agent_id, morale in shared_entries
        ) or "<no shared entries>"
        return (
            f"target={target_value} player_agent={int(snapshot['player_agent_id'])} "
            f"player_morale={int(snapshot['player_morale'])} party_id={int(snapshot['party_id'])} "
            f"map={int(snapshot['map_id'])}/{int(snapshot['region'])}/{int(snapshot['district'])}/{int(snapshot['language'])} "
            f"shared_min={snapshot['shared_min_morale']} shared_error={snapshot['shared_error'] or '<none>'} "
            f"shared_entries=[{raw_entries_summary}] below_target=[{below_target_summary}] rows=[{rows_summary}]"
        )

    @staticmethod
    def _log_party_morale_event(
        source: str,
        event: str,
        target_morale: int | None,
        resolved_model_id: int,
        *,
        message_type=Console.MessageType.Warning,
        extra: str = '',
    ) -> None:
        snapshot = BTUpkeepers._get_party_morale_debug_snapshot()
        suffix = f" {extra}" if extra else ''
        ConsoleLog(
            source,
            (
                f"MORALE EVENT [{event}]: model={int(resolved_model_id)} "
                f"{BTUpkeepers._format_party_morale_snapshot(snapshot, target_morale=target_morale)}{suffix}"
            ),
            message_type,
            log=True,
        )

    @staticmethod
    def _log_debug(source: str, message: str, *, enabled: bool) -> None:
        if not enabled:
            return
        ConsoleLog(source, message, Console.MessageType.Debug, log=True)

    @staticmethod
    def _log_party_morale_debug(
        source: str,
        target_morale: int | None,
        resolved_model_id: int,
        *,
        enabled: bool = True,
        prefix: str = '',
    ) -> None:
        if not enabled:
            return
        snapshot = BTUpkeepers._get_party_morale_debug_snapshot()
        summary = ", ".join(
            (
                f"pos={int(row['party_position'])} agent={int(row['agent_id'])} morale={int(row['morale'])} "
                f"kind={row['kind']} name={row['name']}"
            )
            for row in snapshot['shared_rows']
        ) or "<no valid shared rows>"
        raw_entries = ", ".join(
            f"agent={int(agent_id)} morale={int(morale)}" for agent_id, morale in snapshot['shared_entries']
        ) or "<no shared entries>"
        ConsoleLog(
            source,
            (
                f"{prefix}Morale debug: model={int(resolved_model_id)} target={int(target_morale or 0)} "
                f"player_agent={int(snapshot['player_agent_id'])} player_morale={int(snapshot['player_morale'])} "
                f"party_id={int(snapshot['party_id'])} map={int(snapshot['map_id'])}/"
                f"{int(snapshot['region'])}/{int(snapshot['district'])}/{int(snapshot['language'])} "
                f"shared_min={snapshot['shared_min_morale']} shared_error={snapshot['shared_error'] or '<none>'} "
                f"shared_entries=[{raw_entries}] rows=[{summary}]"
            ),
            Console.MessageType.Debug,
            log=True,
        )

    @staticmethod
    def _log_party_morale_consume_event(
        source: str,
        target_morale: int | None,
        resolved_model_id: int,
        *,
        item_id: int,
    ) -> None:
        BTUpkeepers._log_party_morale_event(
            source,
            'ITEM_CONSUMED',
            target_morale,
            resolved_model_id,
            message_type=Console.MessageType.Warning,
            extra=f"item_id={int(item_id)}",
        )

    @staticmethod
    def _get_shared_effect_ids_for_agent(agent_id: int, headless_cached_data=None) -> set[int]:
        resolved_agent_id = int(agent_id or 0)
        if resolved_agent_id <= 0:
            return set()

        accounts = []
        if headless_cached_data is not None:
            accounts = list(getattr(getattr(headless_cached_data, "party", None), "accounts", {}).values())
        if not accounts:
            accounts = list(GLOBAL_CACHE.ShMem.GetAllAccountData() or [])

        for account in accounts:
            account_agent_id = int(getattr(getattr(account, "AgentData", None), "AgentID", 0) or 0)
            if account_agent_id != resolved_agent_id:
                continue
            buffs = getattr(getattr(getattr(account, "AgentData", None), "Buffs", None), "Buffs", [])
            return {
                int(getattr(buff, "SkillId", 0) or 0)
                for buff in buffs
                if int(getattr(buff, "SkillId", 0) or 0) > 0
            }
        return set()

    @staticmethod
    def _has_any_shared_effect_for_agent(agent_id: int, effect_ids: list[int], headless_cached_data=None) -> bool:
        shared_effect_ids = BTUpkeepers._get_shared_effect_ids_for_agent(agent_id, headless_cached_data=headless_cached_data)
        return any(int(effect_id) > 0 and int(effect_id) in shared_effect_ids for effect_id in effect_ids)

    @staticmethod
    def _get_alcohol_level() -> int:
        try:
            import PyEffects

            return int(PyEffects.PyEffects.GetAlcoholLevel() or 0)
        except Exception:
            return 0

    @staticmethod
    def _find_inventory_item_by_model_id(model_id: int) -> int:
        return int(GLOBAL_CACHE.Inventory.GetFirstModelID(int(model_id)) or 0)

    @staticmethod
    def _tick_service_subtree(
        node: BehaviorTree.Node,
        *,
        state_key: str,
        subtree_factory,
    ) -> BehaviorTree.NodeState:
        state = node.blackboard.setdefault(
            state_key,
            {
                "subtree": None,
            },
        )
        subtree = state.get("subtree")
        if subtree is None:
            subtree = subtree_factory()
            state["subtree"] = subtree

        subtree.blackboard = node.blackboard
        result = BehaviorTree.Node._normalize_state(subtree.tick())
        if result in (BehaviorTree.NodeState.SUCCESS, BehaviorTree.NodeState.FAILURE):
            subtree.reset()
            state["subtree"] = None
        return BehaviorTree.NodeState.RUNNING

    @staticmethod
    def SpawnImp(
        target_bag: int = 1,
        slot: int = 0,
        exclude_list: list[int] | None = None,
        log: bool = False,
        spawn_settle_ms: int = 300,
        move_to_slot: bool = True,
    ) -> BehaviorTree:
        """
        Build a tree that spawns bonus items, prunes extras, and stores the imp stone in a target bag slot.

        Meta:
          Expose: true
          Audience: intermediate
          Display: Spawn Imp
          Purpose: Prepare an imp summoning stone from the bonus item flow.
          UserDescription: Use this when you want to create and organize the imp stone item before using it.
          Notes: Spawns bonus items, destroys other bonus models except exclusions, and moves the imp stone to the target bag slot.
        """
        imp_model_id = ModelID.Igneous_Summoning_Stone.value
        effective_exclude_list = list(exclude_list or [
            imp_model_id,
        ])

        if imp_model_id not in effective_exclude_list:
            effective_exclude_list.append(imp_model_id)

        children: list[BehaviorTree | BehaviorTree.Node] = [
            BTItems.SpawnBonusItems(log=log, aftercast_ms=spawn_settle_ms),
            BTItems.DestroyBonusItems(exclude_list=effective_exclude_list, log=log, aftercast_ms=35),
        ]

        if move_to_slot:
            children.append(
                BTItems.MoveModelToBagSlot(
                    modelID_or_encStr=imp_model_id,
                    target_bag=target_bag,
                    slot=slot,
                    log=log,
                    required=True,
                    aftercast_ms=spawn_settle_ms,
                )
            )

        return BTComposite.Sequence(*children, name="SpawnImp")

    @staticmethod
    def OutpostImpService(
        exclude_list: list[int] | None = None,
        log: bool = False,
    ) -> BehaviorTree:
        """
        Build a service tree that prepares the imp stone once per outpost map.

        Meta:
          Expose: true
          Audience: advanced
          Display: Outpost Imp Service
          Purpose: Run a background outpost service that prepares the imp stone when needed.
          UserDescription: Use this as a service tree when you want imp preparation to happen automatically in outposts.
          Notes: Runs once per ready outpost map and idles until the next relevant map change.
        """
        state = {
            "outpost_visit_signature": None,
            "map_processed": False,
            "spawn_tree": None,
            "last_stage_log": "",
        }

        imp_model_id = ModelID.Igneous_Summoning_Stone.value
        effective_exclude_list = list(exclude_list or [
            imp_model_id,
        ])

        def _get_imp_item_id() -> int:
            return BTUpkeepers._find_inventory_item_by_model_id(imp_model_id)
        

        def _reset_cache_data():
            """
            Reset runtime cache state for the outpost imp service.

            Meta:
              Expose: false
              Audience: advanced
              Display: Internal Reset Imp Service Cache Helper
              Purpose: Clear cached map-processing state and reset any active spawn tree.
            UserDescription: Internal support routine.
            Notes: Resets the cached spawn subtree when map readiness changes.
            """
            state["outpost_visit_signature"] = None
            state["map_processed"] = False
            state["last_stage_log"] = ""
            if state["spawn_tree"] is not None:
                state["spawn_tree"].reset()
                state["spawn_tree"] = None


        def _tick_outpost_imp_service(node: BehaviorTree.Node):
            """
            Drive the outpost imp preparation service loop.

            Meta:
              Expose: false
              Audience: advanced
              Display: Internal Outpost Imp Service Tick Helper
              Purpose: Manage per-map imp preparation in outposts and reuse the spawn subtree when needed.
            UserDescription: Internal support routine.
            Notes: Resets state on loading changes and keeps running until the next eligible map change.
            """
            if (
                Map.IsMapLoading()
                or not Checks.Map.MapValid()
                or not Map.IsMapReady()
                or Map.IsExplorable()
            ):
                _reset_cache_data()
                return BehaviorTree.NodeState.RUNNING

            if not Map.IsOutpost():
                _reset_cache_data()
                return BehaviorTree.NodeState.RUNNING

            current_map_id = Map.GetMapID()
            if current_map_id == 0:
                _reset_cache_data()
                return BehaviorTree.NodeState.RUNNING

            current_instance_uptime = Map.GetInstanceUptime()
            current_visit_signature = state["outpost_visit_signature"]
            if (
                current_visit_signature is None
                or current_visit_signature[0] != current_map_id
            ):
                state["outpost_visit_signature"] = (current_map_id, current_instance_uptime)
                state["map_processed"] = False
                if state["spawn_tree"] is not None:
                    state["spawn_tree"].reset()
                    state["spawn_tree"] = None

            if state["map_processed"]:
                return BehaviorTree.NodeState.RUNNING

            if state["spawn_tree"] is None:
                if _get_imp_item_id() != 0:
                    state["map_processed"] = True
                    if log:
                        _log(
                            "OutpostImpService",
                            f"Imp model {imp_model_id} already present in bags for map {current_map_id}.",
                            message_type=Console.MessageType.Info,
                            log=log,
                        )
                    return BehaviorTree.NodeState.RUNNING

                state["spawn_tree"] = BTUpkeepers.SpawnImp(
                    exclude_list=effective_exclude_list,
                    log=log,
                    move_to_slot=False,
                )

            state["spawn_tree"].blackboard = node.blackboard
            spawn_result = BehaviorTree.Node._normalize_state(state["spawn_tree"].tick())
            if spawn_result is None:
                raise TypeError("OutpostImpService spawn tree returned a non-NodeState result.")

            if spawn_result == BehaviorTree.NodeState.SUCCESS:
                if log:
                    _log(
                        "OutpostImpService",
                        f"Prepared imp model {imp_model_id} in outpost map {current_map_id}.",
                        message_type=Console.MessageType.Success,
                        log=log,
                    )
                state["map_processed"] = True
                state["spawn_tree"].reset()
                state["spawn_tree"] = None
            elif spawn_result == BehaviorTree.NodeState.FAILURE:
                _fail_log(
                    "OutpostImpService",
                    f"Failed to prepare imp model {imp_model_id} in outpost map {current_map_id}; idling until next map change.",
                )
                state["map_processed"] = True
                state["spawn_tree"].reset()
                state["spawn_tree"] = None

            return BehaviorTree.NodeState.RUNNING

        return BehaviorTree(
            BehaviorTree.ConditionNode(
                name="OutpostImpService",
                condition_fn=_tick_outpost_imp_service,
            )
        )

    @staticmethod
    def ExplorableImpService(
        imp_model_id: int = ModelID.Igneous_Summoning_Stone.value,
        log: bool = False,
        check_interval_ms: int = 1000,
    ) -> BehaviorTree:
        """
        Build a service tree that uses the imp stone automatically in eligible explorable maps.

        Meta:
          Expose: true
          Audience: advanced
          Display: Explorable Imp Service
          Purpose: Run a background service that summons the imp in explorable areas when conditions allow.
          UserDescription: Use this as a service tree when you want the imp stone to be used automatically during leveling or farming flows.
          Notes: Skips use while loading, in outposts, when dead, at level 20, during summoning sickness, or when an imp is already alive.
        """
        state = {
            "last_attempt_ms": 0,
        }

        summoning_sickness_effect_id = 2886
        summon_creature_model_ids = {
            513,   # Fire Imp
            1726,  # Fire Imp variant
        }

        def _get_imp_item_id() -> int:
            return BTUpkeepers._find_inventory_item_by_model_id(imp_model_id)

        def _has_alive_imp() -> bool:
            """
            Check whether a summoned imp is already alive in the party.

            Meta:
              Expose: false
              Audience: advanced
              Display: Internal Has Alive Imp Helper
              Purpose: Detect an existing summoned imp before attempting to use the imp stone again.
              UserDescription: Internal support routine.
              Notes: Looks at other party members and filters out dead summons.
            """
            for other in GLOBAL_CACHE.Party.GetOthers():
                if Agent.GetModelID(other) in summon_creature_model_ids and not Agent.IsDead(other):
                    return True
            return False

        def _tick_explorable_imp_service(node: BehaviorTree.Node):
            """
            Drive the explorable imp-summon service loop.

            Meta:
              Expose: false
              Audience: advanced
              Display: Internal Explorable Imp Service Tick Helper
              Purpose: Decide when the imp stone can be used in explorable maps and trigger it when allowed.
              UserDescription: Internal support routine.
              Notes: Skips use when the player is dead, level-capped, loading, ineligible, or already protected by an active imp or summoning sickness.
            """
            if Map.IsMapLoading() or not Checks.Map.MapValid() or not Map.IsMapReady():
                return BehaviorTree.NodeState.RUNNING

            if not Map.IsExplorable():
                return BehaviorTree.NodeState.RUNNING

            if Agent.IsDead(Player.GetAgentID()):
                return BehaviorTree.NodeState.RUNNING

            if Player.GetLevel() >= 20:
                return BehaviorTree.NodeState.RUNNING

            item_id = _get_imp_item_id()
            if item_id == 0:
                return BehaviorTree.NodeState.RUNNING

            if GLOBAL_CACHE.Effects.HasEffect(Player.GetAgentID(), summoning_sickness_effect_id):
                return BehaviorTree.NodeState.RUNNING

            if _has_alive_imp():
                return BehaviorTree.NodeState.RUNNING

            from ...Py4GWcorelib import Utils
            now = Utils.GetBaseTimestamp()

            if now - int(state["last_attempt_ms"]) < check_interval_ms:
                return BehaviorTree.NodeState.RUNNING

            GLOBAL_CACHE.Inventory.UseItem(item_id)
            state["last_attempt_ms"] = int(now)
            if log:
                _log(
                    "ExplorableImpService",
                    f"Used imp stone model {imp_model_id} in explorable map {Map.GetMapID()}.",
                    message_type=Console.MessageType.Info,
                    log=log,
                )

            return BehaviorTree.NodeState.RUNNING

        return BehaviorTree(
            BehaviorTree.ConditionNode(
                name="ExplorableImpService",
                condition_fn=_tick_explorable_imp_service,
            )
        )

    @staticmethod
    def ConsumableService(
        modelID_or_encStr: int,
        effect_name: str = "",
        *,
        effect_id: int = 0,
        effect_ids: list[int] | None = None,
        require_effect_id: bool = False,
        use_where: str = "explorable",
        target_morale: int | None = None,
        party_wide_morale: bool = False,
        target_alcohol_level: int | None = None,
        blocked_effect_id: int = 0,
        fallback_duration_ms: int = 0,
        check_interval_ms: int = 5000,
        aftercast_ms: int = 500,
        debug: bool = False,
    ) -> BehaviorTree:
        """
        Build a background service tree that keeps one consumable effect active in explorable maps.

        Meta:
          Expose: true
          Audience: advanced
          Display: Consumable Service
          Purpose: Run a generic consumable upkeep service for any model/effect pair.
          UserDescription: Use this as a service tree when you want a consumable to be used automatically while exploring.
          Notes: Supports effect, morale, alcohol, outpost sweet, party item, and fallback-duration consumable guards.
        """
        preset = None
        resolved_numeric_model_id = int(modelID_or_encStr)
        for candidate in BTUpkeepers.CONSUMABLE_UPKEEP_PRESETS.values():
            candidate_model_id = candidate.get("model_id")
            if not isinstance(candidate_model_id, int):
                continue
            if int(candidate_model_id) != resolved_numeric_model_id:
                continue
            preset = candidate
            break
        if preset is not None:
            effect_name = effect_name or str(preset.get("effect_name", "") or "")
            effect_id = int(effect_id or preset.get("effect_id", 0) or 0)
            if effect_ids is None:
                effect_ids = list(preset.get("effect_ids", []) or [])
            require_effect_id = bool(require_effect_id or preset.get("require_effect_id", False))
            use_where = str(preset.get("use_where", use_where) or use_where)
            if target_morale is None and preset.get("target_morale") is not None:
                target_morale = int(preset["target_morale"])
            party_wide_morale = bool(party_wide_morale or preset.get("party_wide_morale", False))
            if target_alcohol_level is None and preset.get("target_alcohol_level") is not None:
                target_alcohol_level = int(preset["target_alcohol_level"])
            blocked_effect_id = int(blocked_effect_id or preset.get("blocked_effect_id", 0) or 0)
            fallback_duration_ms = int(fallback_duration_ms or preset.get("fallback_duration_ms", 0) or 0)
            check_interval_ms = int(preset.get("check_interval_ms", check_interval_ms) or check_interval_ms)
            aftercast_ms = int(preset.get("aftercast_ms", aftercast_ms) or aftercast_ms)

        resolved_model_id = BTItems._resolve_model_id_value(modelID_or_encStr)
        resolved_effect_name = effect_name or CONSUMABLE_MODELID_TO_EFFECT_NAME.get(int(resolved_model_id), "")
        configured_effect_ids = tuple(int(value) for value in (effect_ids or []) if int(value or 0) > 0)
        service_key = (
            f"upkeep_service:consumable:{resolved_model_id}:{resolved_effect_name}:{effect_id}:{configured_effect_ids}:"
            f"{use_where}:{target_morale}:{target_alcohol_level}:{blocked_effect_id}:{fallback_duration_ms}"
        )

        def _effect_upkeep_ids() -> list[int]:
            ids = [int(effect_id)] if int(effect_id or 0) > 0 else []
            ids.extend(configured_effect_ids)
            if resolved_effect_name:
                skill_id = int(GLOBAL_CACHE.Skill.GetID(resolved_effect_name) or 0)
                if skill_id > 0:
                    ids.append(skill_id)
            return ids

        def _base_runtime_blocks_use() -> bool:
            if not BTUpkeepers._can_run_local_consumable_service():
                return True
            if not BTUpkeepers._can_use_consumable_here(use_where):
                return True
            return False

        def _use_attempt_throttle_blocks_use(node: BehaviorTree.Node) -> bool:
            return not BTUpkeepers._service_tick_due(node, service_key, check_interval_ms)

        def _effect_upkeep_blocks_use(node: BehaviorTree.Node) -> bool:
            active_effect_ids = _effect_upkeep_ids()
            if require_effect_id and not active_effect_ids:
                return True
            headless_cached_data = node.blackboard.get("headless_heroai_cached_data")
            if active_effect_ids and BTUpkeepers._has_any_shared_effect_for_agent(
                Player.GetAgentID(),
                active_effect_ids,
                headless_cached_data=headless_cached_data,
            ):
                return True
            return False

        def _morale_blocks_use() -> bool:
            if target_morale is None:
                return False

            if not party_wide_morale:
                shared_player_morale = BTUpkeepers._get_party_morale_debug_snapshot().get('player_morale')
                if shared_player_morale is None:
                    return True
                return int(shared_player_morale) >= int(target_morale)

            party_morale = BTUpkeepers._min_party_morale()
            if party_morale is None:
                return True
            return party_morale >= int(target_morale)

        def _alcohol_blocks_use() -> bool:
            if target_alcohol_level is None:
                return False
            return BTUpkeepers._get_alcohol_level() >= int(target_alcohol_level)

        def _blocked_effect_blocks_use(node: BehaviorTree.Node) -> bool:
            if int(blocked_effect_id or 0) <= 0:
                return False
            headless_cached_data = node.blackboard.get("headless_heroai_cached_data")
            return BTUpkeepers._has_any_shared_effect_for_agent(
                Player.GetAgentID(),
                [int(blocked_effect_id)],
                headless_cached_data=headless_cached_data,
            )

        def _fallback_duration_blocks_use(node: BehaviorTree.Node) -> bool:
            if int(fallback_duration_ms or 0) <= 0:
                return False
            state = node.blackboard.setdefault(service_key, {})
            last_used_ms = int(state.get("last_used_ms", 0) or 0)
            if last_used_ms <= 0:
                return False
            from ...Py4GWcorelib import Utils

            return int(Utils.GetBaseTimestamp()) - last_used_ms < int(fallback_duration_ms)

        def _record_fallback_duration_start(node: BehaviorTree.Node) -> None:
            if int(fallback_duration_ms or 0) <= 0:
                return
            from ...Py4GWcorelib import Utils

            state = node.blackboard.setdefault(service_key, {})
            state["last_used_ms"] = int(Utils.GetBaseTimestamp())

        def _broadcast_consumable_message(node: BehaviorTree.Node) -> bool:
            sender_email = str(Player.GetAccountEmail() or "")
            if not sender_email:
                return False

            skill_id = int(GLOBAL_CACHE.Skill.GetID(resolved_effect_name) or 0)
            params = (int(resolved_model_id), skill_id, 0, 0)

            headless_cached_data = node.blackboard.get("headless_heroai_cached_data")
            if headless_cached_data is not None:
                targets = list(getattr(getattr(headless_cached_data, "party", None), "accounts", {}).values())
            else:
                targets = list(GLOBAL_CACHE.ShMem.GetAllAccountData() or [])

            if not targets:
                return False

            filter_effect_ids = tuple(effect_id for effect_id in _effect_upkeep_ids() if int(effect_id) > 0)
            sent_any = False
            target_debug_rows: list[str] = []
            for account in targets:
                account_email = str(getattr(account, "AccountEmail", "") or "")
                if not account_email:
                    continue
                agent_id = int(getattr(getattr(account, "AgentData", None), "AgentID", 0) or 0)
                account_morale = int(getattr(getattr(account, "AgentData", None), "Morale", 0) or 0)

                if target_morale is not None:
                    if account_morale <= 0:
                        target_debug_rows.append(
                            f"skip:{account_email}:agent={agent_id}:morale={account_morale}:reason=no_shared_morale"
                        )
                        continue
                    if account_morale >= int(target_morale):
                        target_debug_rows.append(
                            f"skip:{account_email}:agent={agent_id}:morale={account_morale}:reason=morale_capped"
                        )
                        continue

                account_effect_ids: set[int] = set()
                if filter_effect_ids and agent_id > 0:
                    try:
                        from HeroAI.utils import GetEffectAndBuffIds

                        account_effect_ids = {int(value) for value in GetEffectAndBuffIds(agent_id, cached_data=headless_cached_data) if int(value) > 0}
                    except Exception:
                        buffs = getattr(getattr(getattr(account, "AgentData", None), "Buffs", None), "Buffs", [])
                        account_effect_ids = {int(getattr(buff, "SkillId", 0) or 0) for buff in buffs if int(getattr(buff, "SkillId", 0) or 0) > 0}

                if filter_effect_ids and any(effect_id in account_effect_ids for effect_id in filter_effect_ids):
                    target_debug_rows.append(
                        f"skip:{account_email}:agent={agent_id}:effects={sorted(account_effect_ids)}"
                    )
                    continue
                GLOBAL_CACHE.ShMem.SendMessage(sender_email, account_email, SharedCommandType.PCon, params)
                target_debug_rows.append(
                    f"send:{account_email}:agent={agent_id}:effects={sorted(account_effect_ids)}"
                )
                sent_any = True
            BTUpkeepers._log_debug(
                "ConsumableService",
                (
                    f"Broadcast decision: model={int(resolved_model_id)} sender={sender_email} "
                    f"effect_name={resolved_effect_name or '<none>'} effect_ids={list(filter_effect_ids)} "
                    f"target_morale={target_morale} "
                    f"results=[{'; '.join(target_debug_rows) or '<none>'}]"
                ),
                enabled=debug,
            )
            return sent_any

        def _tick_consumable_service(node: BehaviorTree.Node) -> BehaviorTree.NodeState:
            if _base_runtime_blocks_use():
                BTUpkeepers._log_debug(
                    "ConsumableService",
                    (
                        f"Base runtime blocked: model={int(resolved_model_id)} map_loading={Map.IsMapLoading()} "
                        f"map_valid={Checks.Map.MapValid()} map_ready={Map.IsMapReady()} "
                        f"player_dead={Agent.IsDead(Player.GetAgentID())}"
                    ),
                    enabled=debug,
                )
                return BehaviorTree.NodeState.RUNNING

            if _use_attempt_throttle_blocks_use(node):
                return BehaviorTree.NodeState.RUNNING

            # Morale / death-penalty consumables: Honeycomb-style party morale and self-only morale.
            if _morale_blocks_use():
                return BehaviorTree.NodeState.RUNNING

            # Alcohol consumables: maintain drunk level instead of checking a normal skill effect.
            if _alcohol_blocks_use():
                BTUpkeepers._log_debug(
                    "ConsumableService",
                    (
                        f"Alcohol blocked use: model={int(resolved_model_id)} "
                        f"alcohol_level={BTUpkeepers._get_alcohol_level()} target={target_alcohol_level}"
                    ),
                    enabled=debug,
                )
                return BehaviorTree.NodeState.RUNNING

            # Party item / tonic lockouts: wait while the blocking effect is active.
            if _blocked_effect_blocks_use(node):
                BTUpkeepers._log_debug(
                    "ConsumableService",
                    f"Blocked-effect prevented use: model={int(resolved_model_id)} blocked_effect_id={int(blocked_effect_id)}",
                    enabled=debug,
                )
                return BehaviorTree.NodeState.RUNNING

            # Consumables without reliable effect visibility: local cooldown after a successful use attempt.
            if _fallback_duration_blocks_use(node):
                BTUpkeepers._log_debug(
                    "ConsumableService",
                    (
                        f"Fallback duration blocked use: model={int(resolved_model_id)} "
                        f"fallback_duration_ms={int(fallback_duration_ms)}"
                    ),
                    enabled=debug,
                )
                return BehaviorTree.NodeState.RUNNING

            if _broadcast_consumable_message(node):
                _record_fallback_duration_start(node)
                return BehaviorTree.NodeState.RUNNING

            return BehaviorTree.NodeState.RUNNING

        return BehaviorTree(
            BehaviorTree.ConditionNode(
                name=f"ConsumableService({resolved_model_id})",
                condition_fn=_tick_consumable_service,
            )
        )
