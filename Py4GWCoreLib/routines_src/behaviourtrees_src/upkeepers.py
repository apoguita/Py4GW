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
            "target_morale": 110,
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
            "model_id": "Bottle_Rocket",
            "use_where": "party_items",
            "fallback_duration_ms": PARTY_ITEM_DEFAULT_COOLDOWN_MS,
        },
        "champagne_popper": {
            "rule": "party_item",
            "model_id": "Champagne_Popper",
            "use_where": "party_items",
            "fallback_duration_ms": PARTY_ITEM_DEFAULT_COOLDOWN_MS,
        },
        "ghost_in_the_box": {
            "rule": "party_item",
            "model_id": "Ghost_In_The_Box",
            "use_where": "party_items",
            "fallback_duration_ms": PARTY_ITEM_DEFAULT_COOLDOWN_MS,
        },
        "snowman_summoner": {
            "rule": "party_item",
            "model_id": "Snowman_Summoner",
            "use_where": "party_items",
            "fallback_duration_ms": PARTY_ITEM_DEFAULT_COOLDOWN_MS,
        },
        "sparkler": {
            "rule": "party_item",
            "model_id": "Sparkler",
            "use_where": "party_items",
            "fallback_duration_ms": PARTY_ITEM_DEFAULT_COOLDOWN_MS,
        },
        "squash_serum": {
            "rule": "party_item",
            "model_id": "Squash_Serum",
            "use_where": "party_items",
            "fallback_duration_ms": PARTY_ITEM_DEFAULT_COOLDOWN_MS,
        },
        "beetle_juice_tonic": {
            "rule": "party_tonic",
            "model_id": "Beetle_Juice_Tonic",
            "use_where": "party_items",
            "blocked_effect_id": TONIC_TIPSINESS_EFFECT_ID,
            "fallback_duration_ms": TONIC_TIPSINESS_FALLBACK_MS,
        },
        "cottontail_tonic": {
            "rule": "party_tonic",
            "model_id": "Cottontail_Tonic",
            "use_where": "party_items",
            "blocked_effect_id": TONIC_TIPSINESS_EFFECT_ID,
            "fallback_duration_ms": TONIC_TIPSINESS_FALLBACK_MS,
        },
        "frosty_tonic": {
            "rule": "party_tonic",
            "model_id": "Frosty_Tonic",
            "use_where": "party_items",
            "blocked_effect_id": TONIC_TIPSINESS_EFFECT_ID,
            "fallback_duration_ms": TONIC_TIPSINESS_FALLBACK_MS,
        },
        "mischievous_tonic": {
            "rule": "party_tonic",
            "model_id": "Mischievious_Tonic",
            "use_where": "party_items",
            "blocked_effect_id": TONIC_TIPSINESS_EFFECT_ID,
            "fallback_duration_ms": TONIC_TIPSINESS_FALLBACK_MS,
        },
        "sinister_automatonic": {
            "rule": "party_tonic",
            "model_id": "Sinister_Automatonic_Tonic",
            "use_where": "party_items",
            "blocked_effect_id": TONIC_TIPSINESS_EFFECT_ID,
            "fallback_duration_ms": TONIC_TIPSINESS_FALLBACK_MS,
        },
        "transmogrifier_tonic": {
            "rule": "party_tonic",
            "model_id": "Transmogrifier_Tonic",
            "use_where": "party_items",
            "blocked_effect_id": TONIC_TIPSINESS_EFFECT_ID,
            "fallback_duration_ms": TONIC_TIPSINESS_FALLBACK_MS,
        },
        "yuletide_tonic": {
            "rule": "party_tonic",
            "model_id": "Yuletide_Tonic",
            "use_where": "party_items",
            "blocked_effect_id": TONIC_TIPSINESS_EFFECT_ID,
            "fallback_duration_ms": TONIC_TIPSINESS_FALLBACK_MS,
        },
        "crate_of_fireworks": {
            "rule": "party_item",
            "model_id": "Crate_Of_Fireworks",
            "use_where": "party_items",
            "fallback_duration_ms": CRATE_FIREWORKS_DISPLAY_MS,
        },
        "disco_ball": {
            "rule": "party_item",
            "model_id": "Disco_Ball",
            "use_where": "party_items",
            "fallback_duration_ms": DISCO_BALL_DISPLAY_MS,
        },
        "party_beacon": {
            "rule": "party_item",
            "model_id": "Party_Beacon",
            "use_where": "party_items",
            "fallback_duration_ms": PARTY_ITEM_DEFAULT_COOLDOWN_MS,
        },
    }

    @staticmethod
    def _normalize_consumable_key(key: str) -> str:
        return str(key or "").strip().lower().replace("-", "_").replace(" ", "_")

    @staticmethod
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
    def _min_party_morale() -> int:
        try:
            entries = GLOBAL_CACHE.Party.GetPartyMorale() or []
            if not entries:
                return int(Player.GetMorale() or 0)
            return min(int(morale) for _, morale in entries)
        except Exception:
            return int(Player.GetMorale() or 0)

    @staticmethod
    def _has_any_effect(effect_ids: list[int]) -> bool:
        player_id = Player.GetAgentID()
        return any(effect_id > 0 and GLOBAL_CACHE.Effects.HasEffect(player_id, effect_id) for effect_id in effect_ids)

    @staticmethod
    def _get_alcohol_level() -> int:
        try:
            import PyEffects

            return int(PyEffects.PyEffects.GetAlcoholLevel() or 0)
        except Exception:
            return 0

    @staticmethod
    def _find_inventory_item_by_model_id(model_id: int) -> int:
        bags_to_check = [
            Bag.Backpack,
            Bag.Belt_Pouch,
            Bag.Bag_1,
            Bag.Bag_2,
            Bag.Equipment_Pack,
        ]
        for item_id in GLOBAL_CACHE.ItemArray.GetItemArray(bags_to_check):
            if int(GLOBAL_CACHE.Item.GetModelID(item_id) or 0) == int(model_id):
                return int(item_id)
        return 0

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
        target_bag: int = 1,
        slot: int = 0,
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
                    target_bag=target_bag,
                    slot=slot,
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
        modelID_or_encStr: int | str,
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
        if isinstance(modelID_or_encStr, str):
            normalized_key = BTUpkeepers._normalize_consumable_key(modelID_or_encStr)
            preset = BTUpkeepers.CONSUMABLE_UPKEEP_PRESETS.get(normalized_key)
            if preset is not None:
                modelID_or_encStr = preset["model_id"]
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
        configured_effect_ids = tuple(int(value) for value in (effect_ids or []) if int(value or 0) > 0)
        service_key = (
            f"upkeep_service:consumable:{resolved_model_id}:{effect_name}:{effect_id}:{configured_effect_ids}:"
            f"{use_where}:{target_morale}:{target_alcohol_level}:{blocked_effect_id}:{fallback_duration_ms}"
        )

        def _effect_upkeep_ids() -> list[int]:
            ids = [int(effect_id)] if int(effect_id or 0) > 0 else []
            ids.extend(configured_effect_ids)
            if effect_name:
                skill_id = int(GLOBAL_CACHE.Skill.GetID(effect_name) or 0)
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

        def _effect_upkeep_blocks_use() -> bool:
            active_effect_ids = _effect_upkeep_ids()
            if require_effect_id and not active_effect_ids:
                return True
            if active_effect_ids and BTUpkeepers._has_any_effect(active_effect_ids):
                return True
            return False

        def _morale_blocks_use() -> bool:
            if target_morale is None:
                return False

            player_morale = int(Player.GetMorale() or 0)
            if not party_wide_morale:
                return player_morale >= int(target_morale)

            party_morale = BTUpkeepers._min_party_morale()
            return player_morale >= int(target_morale) and party_morale >= int(target_morale)

        def _alcohol_blocks_use() -> bool:
            if target_alcohol_level is None:
                return False
            return BTUpkeepers._get_alcohol_level() >= int(target_alcohol_level)

        def _blocked_effect_blocks_use() -> bool:
            if int(blocked_effect_id or 0) <= 0:
                return False
            return BTUpkeepers._has_any_effect([int(blocked_effect_id)])

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

        def _use_consumable_item(node: BehaviorTree.Node) -> BehaviorTree.NodeState:
            item_id = int(GLOBAL_CACHE.Inventory.GetFirstModelID(resolved_model_id) or 0)
            if item_id <= 0:
                return BehaviorTree.NodeState.SUCCESS
            GLOBAL_CACHE.Inventory.UseItem(item_id)
            _record_fallback_duration_start(node)
            return BehaviorTree.NodeState.SUCCESS

        def _tick_consumable_service(node: BehaviorTree.Node) -> BehaviorTree.NodeState:
            if _base_runtime_blocks_use():
                return BehaviorTree.NodeState.RUNNING

            # Effect upkeep: consets, pcons, and speed sweets with real effect ids.
            if _effect_upkeep_blocks_use():
                return BehaviorTree.NodeState.RUNNING

            # Morale / death-penalty consumables: Honeycomb-style party morale and self-only morale.
            if _morale_blocks_use():
                return BehaviorTree.NodeState.RUNNING

            # Alcohol consumables: maintain drunk level instead of checking a normal skill effect.
            if _alcohol_blocks_use():
                return BehaviorTree.NodeState.RUNNING

            # Party item / tonic lockouts: wait while the blocking effect is active.
            if _blocked_effect_blocks_use():
                return BehaviorTree.NodeState.RUNNING

            # Consumables without reliable effect visibility: local cooldown after a successful use attempt.
            if _fallback_duration_blocks_use(node):
                return BehaviorTree.NodeState.RUNNING

            if _use_attempt_throttle_blocks_use(node):
                return BehaviorTree.NodeState.RUNNING

            result = BTUpkeepers._tick_service_subtree(
                node,
                state_key=f"{service_key}:subtree",
                subtree_factory=lambda: BehaviorTree(
                    BehaviorTree.ActionNode(
                        name=f"UseConsumableItem({resolved_model_id})",
                        action_fn=lambda action_node: _use_consumable_item(action_node),
                        aftercast_ms=aftercast_ms,
                    )
                ),
            )
            return result

        return BehaviorTree(
            BehaviorTree.ConditionNode(
                name=f"ConsumableService({resolved_model_id})",
                condition_fn=_tick_consumable_service,
            )
        )
