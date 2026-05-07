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
      Display: Loot Item
      Purpose: Build a tree that interacts with a target item flow.
      UserDescription: Use this when you want to perform a common item interaction routine.
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

import time
from collections.abc import Sequence

from ...Agent import Agent
from ...GlobalCache import GLOBAL_CACHE
from ...Player import Player
from ...Py4GWcorelib import ConsoleLog, Console
from ...UIManager import UIManager
from ...enums_src.Item_enums import Bags
from ...enums_src.Model_enums import ModelID
from ...enums_src.UI_enums import ControlAction
from ...py4gwcorelib_src.Lootconfig_src import LootConfig
from ...py4gwcorelib_src.BehaviorTree import BehaviorTree
from .composite import BTComposite
from .player import BTPlayer


def _log(source: str, message: str, *, log: bool = False, message_type=Console.MessageType.Info) -> None:
    ConsoleLog(source, message, message_type, log=log)


def _fail_log(source: str, message: str, message_type=Console.MessageType.Warning) -> None:
    ConsoleLog(source, message, message_type, log=True)


class BTItems:
    """
    Public BT helper group for inventory and item-management routines.

    Meta:
      Expose: true
      Audience: advanced
      Display: Items
      Purpose: Group public BT routines related to inventory item spawning, movement, destruction, and lookup.
      UserDescription: Built-in BT helper group for item and inventory routines.
      Notes: Public `PascalCase` methods in this class are discovery candidates when marked exposed.
    """
    BONUS_ITEM_MODELS = [
        ModelID.Bonus_Luminescent_Scepter.value,
        ModelID.Bonus_Nevermore_Flatbow.value,
        ModelID.Bonus_Rhinos_Charge.value,
        ModelID.Bonus_Serrated_Shield.value,
        ModelID.Bonus_Soul_Shrieker.value,
        ModelID.Bonus_Tigers_Roar.value,
        ModelID.Bonus_Wolfs_Favor.value,
        ModelID.Igneous_Summoning_Stone.value,
    ]

    @staticmethod
    def _resolve_model_id_value(modelID_or_encStr: int | str) -> int:
        if isinstance(modelID_or_encStr, str):
            return Agent.GetModelIDByEncString(modelID_or_encStr)
        return int(modelID_or_encStr)

    @staticmethod
    def EquipItemByModelID(modelID_or_encStr: int | str, aftercast_ms: int = 750, log: bool = False) -> BehaviorTree:
        """
        Build a tree that equips an item by its model ID.

        Meta:
          Expose: true
          Audience: beginner
          Display: Equip Item
          Purpose: Equip an item by its model ID.
          UserDescription: Use this when you want to equip a specific item from your inventory.
          Notes: Completes after a configurable aftercast delay to allow the inventory to update.
        """
        def _equip_item() -> BehaviorTree.NodeState:
            resolved_model_id = BTItems._resolve_model_id_value(modelID_or_encStr)
            equipped_count = GLOBAL_CACHE.Inventory.GetModelCountInEquipped(resolved_model_id)
            inventory_count = GLOBAL_CACHE.Inventory.GetModelCount(resolved_model_id)
            _log(
                "EquipItemByModelID",
                (
                    f"Resolved model {modelID_or_encStr!r} -> {resolved_model_id}. "
                    f"inventory_count={inventory_count}, equipped_count={equipped_count}."
                ),
                log=log,
            )
            item_id = GLOBAL_CACHE.Inventory.GetFirstModelID(resolved_model_id)
            if item_id == 0:
                _fail_log(
                    "EquipItemByModelID",
                    f"Item model {resolved_model_id} not found in inventory.",
                    Console.MessageType.Error,
                )
                return BehaviorTree.NodeState.FAILURE

            _log(
                "EquipItemByModelID",
                f"Equipping item_id={item_id} for model {resolved_model_id} on player {Player.GetAgentID()}.",
                log=log,
            )
            GLOBAL_CACHE.Inventory.EquipItem(item_id, Player.GetAgentID())
            _log(
                "EquipItemByModelID",
                f"Equip request sent for item_id={item_id}.",
                log=log,
            )
            return BehaviorTree.NodeState.SUCCESS

        return BehaviorTree(
            BehaviorTree.ActionNode(
                name=f"EquipItemByModelID({modelID_or_encStr})",
                action_fn=_equip_item,
                aftercast_ms=aftercast_ms,
            )
        )

    @staticmethod
    def EquipInventoryBag(
        modelID_or_encStr: int | str,
        target_bag: int,
        timeout_ms: int = 2500,
        poll_interval_ms: int = 125,
        log: bool = False,
    ) -> BehaviorTree:
        """
        Build a tree that equips an inventory bag item into the requested bag slot.

        Meta:
          Expose: true
          Audience: intermediate
          Display: Equip Inventory Bag
          Purpose: Equip an inventory bag item into a specific bag slot.
          UserDescription: Use this when you want to equip a belt pouch or bag from inventory into its container slot.
          Notes: Mirrors the bag-equip helper flow, including the backpack-slot fallback when native item use does not populate the target bag.
        """
        from ...Py4GWcorelib import Utils

        inventory_frame_hash = 291586130
        state = {
            "stage": "init",
            "resolved_model_id": 0,
            "item_id": 0,
            "native_deadline_ms": 0,
            "final_deadline_ms": 0,
            "next_check_ms": 0,
            "key_up_ms": 0,
        }

        def _reset_state() -> None:
            state["stage"] = "init"
            state["resolved_model_id"] = 0
            state["item_id"] = 0
            state["native_deadline_ms"] = 0
            state["final_deadline_ms"] = 0
            state["next_check_ms"] = 0
            state["key_up_ms"] = 0

        def _bag_is_populated() -> bool:
            target_container_item = GLOBAL_CACHE.Inventory.GetBagContainerItem(target_bag)
            target_bag_size = GLOBAL_CACHE.Inventory.GetBagSize(target_bag)
            return target_container_item != 0 or target_bag_size > 0

        def _get_backpack_slot_frame_id() -> int:
            return UIManager.GetChildFrameID(
                inventory_frame_hash,
                [0, 0, 0, Bags.Backpack - 1, 2],
            )

        def _equip_inventory_bag(node: BehaviorTree.Node) -> BehaviorTree.NodeState:
            now = int(Utils.GetBaseTimestamp())

            if _bag_is_populated():
                _reset_state()
                return BehaviorTree.NodeState.SUCCESS

            if state["stage"] == "init":
                resolved_model_id = BTItems._resolve_model_id_value(modelID_or_encStr)
                item_id = GLOBAL_CACHE.Inventory.GetFirstModelID(resolved_model_id)
                if item_id == 0:
                    _fail_log("EquipInventoryBag", f"Item model {resolved_model_id} not found in inventory.", Console.MessageType.Error)
                    _reset_state()
                    return BehaviorTree.NodeState.FAILURE

                GLOBAL_CACHE.Inventory.UseItem(item_id)
                state["stage"] = "wait_native"
                state["resolved_model_id"] = resolved_model_id
                state["item_id"] = item_id
                state["native_deadline_ms"] = now + min(timeout_ms, 250)
                state["final_deadline_ms"] = now + timeout_ms
                state["next_check_ms"] = now + poll_interval_ms
                node.blackboard["equip_inventory_bag_last_model_id"] = resolved_model_id
                node.blackboard["equip_inventory_bag_last_item_id"] = item_id
                return BehaviorTree.NodeState.RUNNING

            if state["stage"] == "wait_native":
                if now < int(state["next_check_ms"]):
                    return BehaviorTree.NodeState.RUNNING

                if now <= int(state["native_deadline_ms"]):
                    state["next_check_ms"] = now + poll_interval_ms
                    return BehaviorTree.NodeState.RUNNING

                if GLOBAL_CACHE.Inventory.MoveModelToBagSlot(int(state["resolved_model_id"]), Bags.Backpack, 0):
                    _log(
                        "EquipInventoryBag",
                        f"Native UseItem did not populate bag {target_bag}; trying backpack slot double-click fallback for model {int(state['resolved_model_id'])}.",
                        message_type=Console.MessageType.Warning,
                        log=log,
                    )
                    state["stage"] = "fallback_wait_before_open"
                    state["next_check_ms"] = now + poll_interval_ms
                else:
                    _log(
                        "EquipInventoryBag",
                        f"Fallback move to backpack slot 0 failed for model {int(state['resolved_model_id'])}.",
                        message_type=Console.MessageType.Warning,
                        log=log,
                    )
                    state["stage"] = "final_wait"
                    state["next_check_ms"] = now + poll_interval_ms

                return BehaviorTree.NodeState.RUNNING

            if state["stage"] == "fallback_wait_before_open":
                if now < int(state["next_check_ms"]):
                    return BehaviorTree.NodeState.RUNNING

                if not GLOBAL_CACHE.Inventory.IsInventoryBagsOpen():
                    UIManager.Keydown(ControlAction.ControlAction_ToggleAllBags.value, 0)
                    state["stage"] = "fallback_toggle_bags_release"
                    state["key_up_ms"] = now + 75
                    return BehaviorTree.NodeState.RUNNING

                state["stage"] = "fallback_wait_before_double_click"
                state["next_check_ms"] = now + poll_interval_ms
                return BehaviorTree.NodeState.RUNNING

            if state["stage"] == "fallback_toggle_bags_release":
                if now < int(state["key_up_ms"]):
                    return BehaviorTree.NodeState.RUNNING

                UIManager.Keyup(ControlAction.ControlAction_ToggleAllBags.value, 0)
                state["stage"] = "fallback_wait_before_double_click"
                state["next_check_ms"] = now + poll_interval_ms
                return BehaviorTree.NodeState.RUNNING

            if state["stage"] == "fallback_wait_before_double_click":
                if now < int(state["next_check_ms"]):
                    return BehaviorTree.NodeState.RUNNING

                frame_id = _get_backpack_slot_frame_id()
                if not UIManager.FrameExists(frame_id):
                    _fail_log("EquipInventoryBag", "Frame does not exist for backpack slot 0.", Console.MessageType.Error)
                    _reset_state()
                    return BehaviorTree.NodeState.FAILURE

                UIManager.TestMouseAction(frame_id=frame_id, current_state=9, wparam_value=0, lparam_value=0)
                state["stage"] = "fallback_double_click_confirm"
                state["next_check_ms"] = now + 60
                return BehaviorTree.NodeState.RUNNING

            if state["stage"] == "fallback_double_click_confirm":
                if now < int(state["next_check_ms"]):
                    return BehaviorTree.NodeState.RUNNING

                frame_id = _get_backpack_slot_frame_id()
                if not UIManager.FrameExists(frame_id):
                    _fail_log("EquipInventoryBag", "Frame does not exist for backpack slot 0.", Console.MessageType.Error)
                    _reset_state()
                    return BehaviorTree.NodeState.FAILURE

                UIManager.TestMouseClickAction(frame_id=frame_id, current_state=9, wparam_value=0, lparam_value=0)
                state["stage"] = "final_wait"
                state["next_check_ms"] = now + 60
                return BehaviorTree.NodeState.RUNNING

            if state["stage"] == "final_wait":
                if now < int(state["next_check_ms"]):
                    return BehaviorTree.NodeState.RUNNING

                if _bag_is_populated():
                    _reset_state()
                    return BehaviorTree.NodeState.SUCCESS

                if now <= int(state["final_deadline_ms"]):
                    state["next_check_ms"] = now + poll_interval_ms
                    return BehaviorTree.NodeState.RUNNING

                _fail_log(
                    "EquipInventoryBag",
                    (
                        f"Failed to equip model {int(state['resolved_model_id'])} item {int(state['item_id'])} into bag {target_bag} within {timeout_ms}ms. "
                        f"container_item={GLOBAL_CACHE.Inventory.GetBagContainerItem(target_bag)} "
                        f"size={GLOBAL_CACHE.Inventory.GetBagSize(target_bag)}."
                    ),
                    Console.MessageType.Error,
                )
                _reset_state()
                return BehaviorTree.NodeState.FAILURE

            _reset_state()
            return BehaviorTree.NodeState.FAILURE

        return BehaviorTree(
            BehaviorTree.ConditionNode(
                name=f"EquipInventoryBag({modelID_or_encStr}, {target_bag})",
                condition_fn=_equip_inventory_bag,
            )
        )
        
    @staticmethod
    def IsItemInInventoryBags(modelID_or_encStr: int | str) -> BehaviorTree:
        def _is_item_in_inventory_bags() -> bool:
            resolved_model_id = BTItems._resolve_model_id_value(modelID_or_encStr)
            return GLOBAL_CACHE.Inventory.GetModelCount(resolved_model_id) > 0

        return BehaviorTree(
            BehaviorTree.ConditionNode(
                name=f"IsItemInInventoryBags({modelID_or_encStr})",
                condition_fn=_is_item_in_inventory_bags,
            )
        )

    @staticmethod
    def IsItemEquipped(modelID_or_encStr: int | str) -> BehaviorTree:
        def _is_item_equipped() -> bool:
            resolved_model_id = BTItems._resolve_model_id_value(modelID_or_encStr)
            return GLOBAL_CACHE.Inventory.GetModelCountInEquipped(resolved_model_id) > 0

        return BehaviorTree(
            BehaviorTree.ConditionNode(
                name=f"IsItemEquipped({modelID_or_encStr})",
                condition_fn=_is_item_equipped,
            )
        )

    @staticmethod
    def UseConsumable(
        modelID_or_encStr: int | str,
        effect_name: str = "",
        aftercast_ms: int = 100,
    ) -> BehaviorTree:
        """
        Build a tree that uses a single consumable item when runtime checks allow it.

        Meta:
          Expose: true
          Audience: intermediate
          Display: Use Consumable
          Purpose: Use one consumable item with map, life-state, and active-effect checks.
          UserDescription: Use this when you want to consume one item safely without duplicating active effects.
          Notes: Succeeds quietly when the effect is already active or the item is missing.
        """
        def _use_consumable(node: BehaviorTree.Node) -> BehaviorTree.NodeState:
            from ..Checks import Checks
            from ...Map import Map

            if not Checks.Map.MapValid():
                return BehaviorTree.NodeState.FAILURE

            if not Map.IsExplorable():
                return BehaviorTree.NodeState.FAILURE

            if Agent.IsDead(Player.GetAgentID()):
                return BehaviorTree.NodeState.FAILURE

            resolved_model_id = BTItems._resolve_model_id_value(modelID_or_encStr)

            if effect_name:
                effect_id = GLOBAL_CACHE.Skill.GetID(effect_name)
                if GLOBAL_CACHE.Effects.HasEffect(Player.GetAgentID(), effect_id):
                    return BehaviorTree.NodeState.SUCCESS

            item_id = GLOBAL_CACHE.Inventory.GetFirstModelID(resolved_model_id)
            if item_id == 0:
                return BehaviorTree.NodeState.SUCCESS

            GLOBAL_CACHE.Inventory.UseItem(item_id)
            return BehaviorTree.NodeState.SUCCESS

        return BehaviorTree(
            BehaviorTree.ActionNode(
                name=f"UseConsumable({modelID_or_encStr})",
                action_fn=_use_consumable,
                aftercast_ms=aftercast_ms,
            )
        )

    @staticmethod
    def UseConsumables(
        consumable_effects: Sequence[tuple[int | str, str]],
        aftercast_ms: int = 100,
    ) -> BehaviorTree:
        """
        Build a tree that uses a list of consumables with per-item checks.

        Meta:
          Expose: true
          Audience: intermediate
          Display: Use Consumables
          Purpose: Use several consumables safely through individual checked BT item nodes.
          UserDescription: Use this when you want a batch consumable pass that skips active or missing effects/items.
          Notes: Internally composes `UseConsumable` nodes into a sequence.
        """
        return BTComposite.Sequence(
            *[
                BTItems.UseConsumable(
                    model_id,
                    effect_name,
                    aftercast_ms=aftercast_ms,
                )
                for model_id, effect_name in consumable_effects
            ],
            name="UseConsumables",
        )


    @staticmethod
    def SpawnBonusItems(log: bool = False, aftercast_ms: int = 500) -> BehaviorTree:
        """
        Build a tree that issues the `/bonus` command to spawn bonus items.

        Meta:
          Expose: true
          Audience: beginner
          Display: Spawn Bonus Items
          Purpose: Spawn available bonus items through the `/bonus` command.
          UserDescription: Use this when you want bonus items to appear in inventory before other item routines run.
          Notes: Completes after a configurable aftercast delay to allow the inventory to update.
        """
        def _spawn_bonus_items():
            """
            Issue the `/bonus` command to spawn bonus inventory items.

            Meta:
              Expose: false
              Audience: advanced
              Display: Internal Spawn Bonus Items Helper
              Purpose: Send the `/bonus` chat command for the enclosing item routine.
              UserDescription: Internal support routine.
              Notes: Returns success immediately after sending the command.
            """
            Player.SendChatCommand("bonus")
            _log("SpawnBonusItems", "Sent /bonus command.", message_type=Console.MessageType.Info, log=log)
            return BehaviorTree.NodeState.SUCCESS

        tree = BehaviorTree.ActionNode(
            name="SpawnBonusItems",
            action_fn=_spawn_bonus_items,
            aftercast_ms=aftercast_ms,
        )
        return BehaviorTree(tree)

    @staticmethod
    def DestroyItem(
        modelID_or_encStr: int | str,
        log: bool = False,
        required: bool = False,
        aftercast_ms: int = 600,
    ) -> BehaviorTree:
        """
        Build a tree that destroys the first inventory item matching a model id.

        Meta:
          Expose: true
          Audience: intermediate
          Display: Destroy Item
          Purpose: Destroy the first inventory item matching a model id.
          UserDescription: Use this when you want to remove a specific item model from inventory.
          Notes: Can be marked optional or required; required mode fails when the item is missing.
        """
        def _destroy_item():
            """
            Destroy the first inventory item matching the requested model id.

            Meta:
              Expose: false
              Audience: advanced
              Display: Internal Destroy Item Helper
              Purpose: Perform the actual inventory lookup and destroy request for a single item model.
              UserDescription: Internal support routine.
              Notes: Required mode fails when the item is missing; optional mode succeeds quietly.
            """
            resolved_model_id = BTItems._resolve_model_id_value(modelID_or_encStr)
            item_id = GLOBAL_CACHE.Inventory.GetFirstModelID(resolved_model_id)
            if item_id == 0:
                _fail_log(
                    "DestroyItem",
                    f"Item model {resolved_model_id} was not found in inventory for destruction.",
                    Console.MessageType.Warning if required else Console.MessageType.Info,
                )
                if required:
                    return BehaviorTree.NodeState.FAILURE
                return BehaviorTree.NodeState.SUCCESS

            GLOBAL_CACHE.Inventory.DestroyItem(item_id)
            _log(
                "DestroyItem",
                f"Queued destroy for item model {resolved_model_id} (item_id={item_id}).",
                message_type=Console.MessageType.Info,
                log=log,
            )
            return BehaviorTree.NodeState.SUCCESS

        tree = BehaviorTree.ActionNode(
            name="DestroyItem",
            action_fn=_destroy_item,
            aftercast_ms=aftercast_ms,
        )
        return BehaviorTree(tree)

    @staticmethod
    def DestroyBonusItems(
        exclude_list: list[int] | None = None,
        log: bool = False,
        aftercast_ms: int = 125,
    ) -> BehaviorTree:
        """
        Build a tree that destroys spawned bonus items except for excluded models.

        Meta:
          Expose: true
          Audience: intermediate
          Display: Destroy Bonus Items
          Purpose: Destroy bonus item models while preserving any excluded models.
          UserDescription: Use this after spawning bonus items when you only want to keep selected bonus models.
          Notes: Runs a composed destroy pass over the known bonus item model list.
        """
        excluded_models = set(exclude_list or [
            ModelID.Igneous_Summoning_Stone.value,
        ])
        bonus_models_to_destroy = [
            model_id
            for model_id in BTItems.BONUS_ITEM_MODELS
            if model_id not in excluded_models
        ]

        return BTComposite.Sequence(
            BTPlayer.PrintMessageToConsole(
                source="DestroyBonusItems",
                message=f"Destroy pass starting for models: {bonus_models_to_destroy}",
            ),
            *[
                BTItems.DestroyItem(modelID_or_encStr=model_id, log=log, required=False, aftercast_ms=aftercast_ms)
                for model_id in bonus_models_to_destroy
            ],
            name="DestroyBonusItems",
        )

    @staticmethod
    def CustomizeWeapon(
        frame_label: str = "Merchant.CustomizeWeaponButton",
        aftercast_ms: int = 500,
    ) -> BehaviorTree:
        """
        Build a tree that clicks the merchant customize-weapon button by UI alias.

        Meta:
          Expose: true
          Audience: intermediate
          Display: Customize Weapon
          Purpose: Click the customize-weapon button when the merchant window is open.
          UserDescription: Use this when you want to trigger weapon customization from an open merchant or crafter window.
          Notes: Resolves the target frame through `frame_aliases.json` using the provided label.
        """
        def _click_customize_weapon() -> BehaviorTree.NodeState:
            frame_id = UIManager.GetFrameIDByCustomLabel(frame_label=frame_label)
            if frame_id == 0 or not UIManager.FrameExists(frame_id):
                return BehaviorTree.NodeState.FAILURE

            UIManager.FrameClick(frame_id)
            return BehaviorTree.NodeState.SUCCESS

        return BehaviorTree(
            BehaviorTree.ActionNode(
                name=f"CustomizeWeapon({frame_label})",
                action_fn=_click_customize_weapon,
                aftercast_ms=aftercast_ms,
            )
        )

    @staticmethod
    def DestroyItems(
        model_ids: list[int],
        log: bool = False,
        aftercast_ms: int = 100,
    ) -> BehaviorTree:
        """
        Build a tree that repeatedly destroys any inventory items matching a list of model ids.

        Meta:
          Expose: true
          Audience: intermediate
          Display: Destroy Items
          Purpose: Destroy all matching inventory items across a list of model ids.
          UserDescription: Use this when you want to clear several item models from inventory over multiple ticks.
          Notes: Processes one matching item at a time and returns RUNNING between destroy attempts using the configured throttle.
        """
        from ...Py4GWcorelib import Utils

        models_to_destroy = [int(model_id) for model_id in model_ids]
        state = {
            "next_attempt_ms": 0,
        }

        def _destroy_items(node: BehaviorTree.Node) -> BehaviorTree.NodeState:
            """
            Process one pending destroy step from the configured model list.

            Meta:
              Expose: false
              Audience: advanced
              Display: Internal Destroy Items Helper
              Purpose: Drive the repeated destroy loop for a list of model ids over multiple ticks.
              UserDescription: Internal support routine.
              Notes: Stores the last destroyed model and item ids on the blackboard and throttles repeated destroy attempts.
            """
            now = Utils.GetBaseTimestamp()
            if now < int(state["next_attempt_ms"]):
                return BehaviorTree.NodeState.RUNNING

            for model_id in models_to_destroy:
                item_id = GLOBAL_CACHE.Inventory.GetFirstModelID(model_id)
                if item_id == 0:
                    continue

                GLOBAL_CACHE.Inventory.DestroyItem(item_id)
                state["next_attempt_ms"] = int(now + aftercast_ms)
                node.blackboard["destroy_items_last_model_id"] = model_id
                node.blackboard["destroy_items_last_item_id"] = item_id
                _log(
                    "DestroyItems",
                    f"Queued destroy for item model {model_id} (item_id={item_id}).",
                    message_type=Console.MessageType.Info,
                    log=log,
                )
                return BehaviorTree.NodeState.RUNNING

            _log(
                "DestroyItems",
                f"Destroy pass completed for models: {models_to_destroy}",
                message_type=Console.MessageType.Info,
                log=log,
            )
            return BehaviorTree.NodeState.SUCCESS

        return BehaviorTree(
            BehaviorTree.ConditionNode(
                name="DestroyItems",
                condition_fn=_destroy_items,
            )
        )

    @staticmethod
    def WaitForAnyModelInInventory(
        model_ids: list[int],
        timeout_ms: int = 5000,
        throttle_interval_ms: int = 100,
        log: bool = False,
    ) -> BehaviorTree:
        """
        Build a tree that waits until any requested model id appears in inventory.

        Meta:
          Expose: true
          Audience: intermediate
          Display: Wait For Any Model In Inventory
          Purpose: Wait until at least one of the requested model ids exists in inventory.
          UserDescription: Use this when a later step depends on any one of several item models being present.
          Notes: Uses a wait-until node with throttling and timeout support.
        """
        def _wait_for_any_model() -> BehaviorTree.NodeState:
            """
            Check whether any requested model id is currently present in inventory.

            Meta:
              Expose: false
              Audience: advanced
              Display: Internal Wait For Any Model Helper
              Purpose: Probe inventory for the first available model among the requested ids.
              UserDescription: Internal support routine.
              Notes: Returns success as soon as any matching item is found and otherwise keeps the wait node running.
            """
            for model_id in model_ids:
                item_id = GLOBAL_CACHE.Inventory.GetFirstModelID(model_id)
                if item_id != 0:
                    _log("WaitForAnyModelInInventory", f"Detected inventory model {model_id} as item_id={item_id}.", message_type=Console.MessageType.Info, log=log)
                    return BehaviorTree.NodeState.SUCCESS
            return BehaviorTree.NodeState.RUNNING

        return BehaviorTree(
            BehaviorTree.WaitUntilNode(
                name="WaitForAnyModelInInventory",
                condition_fn=_wait_for_any_model,
                throttle_interval_ms=throttle_interval_ms,
                timeout_ms=timeout_ms,
            )
        )

    @staticmethod
    def MoveModelToBagSlot(
        modelID_or_encStr: int | str,
        target_bag: int = 1,
        slot: int = 0,
        log: bool = False,
        required: bool = True,
        aftercast_ms: int = 250,
    ) -> BehaviorTree:
        """
        Build a tree that moves the first matching model id into a target bag slot.

        Meta:
          Expose: true
          Audience: intermediate
          Display: Move Model To Bag Slot
          Purpose: Move an inventory item model into a specific bag and slot.
          UserDescription: Use this when you want a known model to be organized into a specific inventory location.
          Notes: Optional mode succeeds quietly on failure, while required mode fails and logs a warning.
        """
        def _move_model_to_bag_slot():
            """
            Move the first matching model id into the requested bag slot.

            Meta:
              Expose: false
              Audience: advanced
              Display: Internal Move Model To Bag Slot Helper
              Purpose: Perform the actual inventory move request for the enclosing routine.
              UserDescription: Internal support routine.
              Notes: Required mode fails on move failure; optional mode succeeds quietly.
            """
            resolved_model_id = BTItems._resolve_model_id_value(modelID_or_encStr)
            moved = GLOBAL_CACHE.Inventory.MoveModelToBagSlot(resolved_model_id, target_bag, slot)
            if not moved:
                if required:
                    _fail_log(
                        "MoveModelToBagSlot",
                        f"Failed to move model {resolved_model_id} to bag {target_bag} slot {slot}.",
                    )
                    return BehaviorTree.NodeState.FAILURE
                return BehaviorTree.NodeState.SUCCESS

            _log(
                "MoveModelToBagSlot",
                f"Moved model {resolved_model_id} to bag {target_bag} slot {slot}.",
                message_type=Console.MessageType.Info,
                log=log,
            )
            return BehaviorTree.NodeState.SUCCESS

        tree = BehaviorTree.ActionNode(
            name="MoveModelToBagSlot",
            action_fn=_move_model_to_bag_slot,
            aftercast_ms=aftercast_ms,
        )
        return BehaviorTree(tree)

    @staticmethod
    def GetItemNameByItemID(item_id: int) -> BehaviorTree:
        """
        Build a tree that requests and retrieves an item name by item id.

        Meta:
          Expose: true
          Audience: advanced
          Display: Get Item Name By Item ID
          Purpose: Request an item name and store the resolved name on the blackboard.
          UserDescription: Use this when you need the item name text for a known item id during tree execution.
          Notes: Stores the resolved name in `blackboard['result']` and waits up to 2000ms for the name to become ready.
        """
        def _request_item_name(node):
            """
            Request item-name resolution for the provided item id.

            Meta:
              Expose: false
              Audience: advanced
              Display: Internal Request Item Name Helper
              Purpose: Dispatch the item-name request before the wait step begins.
              UserDescription: Internal support routine.
              Notes: Returns success immediately after sending the request.
            """
            GLOBAL_CACHE.Item.RequestName(item_id)
            return BehaviorTree.NodeState.SUCCESS

        def _check_item_name_ready(node):
            """
            Check whether the requested item name has been populated yet.

            Meta:
              Expose: false
              Audience: advanced
              Display: Internal Check Item Name Ready Helper
              Purpose: Gate the repeater until the requested item name is available.
              UserDescription: Internal support routine.
              Notes: Returns failure while the item name is still pending so the repeater keeps waiting.
            """
            if not GLOBAL_CACHE.Item.IsNameReady(item_id):
                return BehaviorTree.NodeState.FAILURE
            return BehaviorTree.NodeState.SUCCESS

        def _get_item_name(node):
            """
            Read the resolved item name and store it on the blackboard.

            Meta:
              Expose: false
              Audience: advanced
              Display: Internal Get Item Name Helper
              Purpose: Store the resolved item name in `blackboard['result']` for later steps.
              UserDescription: Internal support routine.
              Notes: Returns failure if the name is still empty after the ready check sequence.
            """
            name = ''
            if GLOBAL_CACHE.Item.IsNameReady(item_id):
                name = GLOBAL_CACHE.Item.GetName(item_id)

            node.blackboard["result"] = name
            return BehaviorTree.NodeState.SUCCESS if name else BehaviorTree.NodeState.FAILURE

        tree = BehaviorTree.SequenceNode(
            name="GetItemNameByItemIDRoot",
            children=[
                BehaviorTree.ActionNode(name="RequestItemName", action_fn=_request_item_name),
                BehaviorTree.RepeaterUntilSuccessNode(
                    name="WaitUntilItemNameReadyRepeater",
                    timeout_ms=2000,
                    child=BehaviorTree.SelectorNode(
                        name="WaitUntilItemNameReadySelector",
                        children=[
                            BehaviorTree.ConditionNode(name="CheckItemNameReady", condition_fn=_check_item_name_ready),
                            BehaviorTree.SequenceNode(
                                name="WaitForThrottle",
                                children=[
                                    BehaviorTree.WaitForTimeNode(name="Throttle100ms", duration_ms=100),
                                    BehaviorTree.FailerNode(name="FailToRepeat")
                                ]
                            ),
                        ]
                    )
                ),
                BehaviorTree.ActionNode(name="GetItemName", action_fn=_get_item_name)
            ]
        )
        return BehaviorTree(tree)

    @staticmethod
    def HasItemQuantity(model_id: int, quantity: int) -> BehaviorTree:
        """
        Build a tree that checks for at least a certain quantity of an item model in inventory.

        Meta:
          Expose: true
          Audience: intermediate
          Display: Wait For Item Quantity
          Purpose: Check for at least a certain quantity of an item model in inventory.
          UserDescription: Use this when you want to check for a specific quantity of an item model before proceeding.
          Notes: Returns success if the requested quantity is met or exceeded, and failure otherwise.
        """
        return BehaviorTree(
            BehaviorTree.ConditionNode(
                name=f"HasItemQuantity({model_id}, {quantity})",
                condition_fn=lambda: GLOBAL_CACHE.Inventory.GetModelCount(model_id) >= quantity,
            )
        )

    @staticmethod
    def SpawnAndDestroyBonusItems(exclude_list: list[int] | None = None, log: bool = False) -> BehaviorTree:
        """
        Build a tree that spawns bonus items and then destroys the unwanted ones.

        Meta:
          Expose: true
          Audience: intermediate
          Display: Spawn And Destroy Bonus Items
          Purpose: Spawn available bonus items and immediately clean them up except for excluded models.
          UserDescription: Use this when you want a one-step bonus spawn and cleanup routine.
          Notes: Composes the existing spawn and destroy bonus item routines with a short settle delay.
        """
        from ..BehaviourTrees import BT

        return BT.Composite.Sequence(
            BT.Items.SpawnBonusItems(log=log),
            BT.Player.Wait(duration_ms=125, log=False),
            BT.Items.DestroyBonusItems(exclude_list=exclude_list, log=log),
            name="SpawnAndDestroyBonusItems",
        )

    @staticmethod
    def AddModelToLootWhitelist(model_id: int, aftercast_ms: int = 50) -> BehaviorTree:
        """
        Build a tree that adds a model id to the loot whitelist.

        Meta:
          Expose: true
          Audience: intermediate
          Display: Add Model To Loot Whitelist
          Purpose: Add an item model id to the active loot whitelist.
          UserDescription: Use this when a routine should mark an item model as lootable before item collection starts.
          Notes: Returns success immediately after mutating the local loot configuration.
        """
        def _add_model_to_loot_whitelist() -> BehaviorTree.NodeState:
            LootConfig().AddToWhitelist(model_id)
            return BehaviorTree.NodeState.SUCCESS

        return BehaviorTree(
            BehaviorTree.ActionNode(
                name=f"AddModelToLootWhitelist({model_id})",
                action_fn=_add_model_to_loot_whitelist,
                aftercast_ms=aftercast_ms,
            )
        )

    @staticmethod
    def LootItems(distance: float, timeout_ms: int = 10000, aftercast_ms: int = 500) -> BehaviorTree:
        """
        Build a tree that loots nearby items until no loot remains, inventory fills, or timeout expires.

        Meta:
          Expose: true
          Audience: intermediate
          Display: Loot Items
          Purpose: Interact with nearby loot items using the active loot configuration.
          UserDescription: Use this when you want to perform a bounded nearby loot pass.
          Notes: Stops when no items remain, bags are full, or the timeout expires.
        """
        state = {
            "started_at": 0.0,
            "last_item_agent_id": 0,
        }

        def _loot_items() -> BehaviorTree.NodeState:
            if state["started_at"] == 0.0:
                state["started_at"] = time.monotonic()

            if GLOBAL_CACHE.Inventory.GetFreeSlotCount() <= 0:
                state["started_at"] = 0.0
                return BehaviorTree.NodeState.SUCCESS

            loot_array = LootConfig().GetfilteredLootArray(
                distance=distance,
                multibox_loot=True,
                allow_unasigned_loot=False,
            )
            if not loot_array:
                state["started_at"] = 0.0
                return BehaviorTree.NodeState.SUCCESS

            if (time.monotonic() - state["started_at"]) * 1000 >= timeout_ms:
                state["started_at"] = 0.0
                return BehaviorTree.NodeState.SUCCESS

            item_agent_id = loot_array[0]
            state["last_item_agent_id"] = item_agent_id
            Player.ChangeTarget(item_agent_id)
            Player.Interact(item_agent_id, False)
            return BehaviorTree.NodeState.RUNNING

        return BehaviorTree(
            BehaviorTree.ActionNode(
                name="LootItems",
                action_fn=_loot_items,
                aftercast_ms=aftercast_ms,
            )
        )

    @staticmethod
    def RestockItems(model_id: int, desired_quantity: int, allow_missing: bool = False) -> BehaviorTree:
        """
        Build a tree that restocks an inventory model from storage up to the requested quantity.

        Meta:
          Expose: true
          Audience: intermediate
          Display: Restock Items
          Purpose: Withdraw a model from storage until the requested on-character quantity is met.
          UserDescription: Use this when a step needs a consumable or item restocked from storage before leaving outpost.
          Notes: Mirrors the original coroutine flow using native BT state: check, withdraw once, wait, then re-check.
        """
        from ...Py4GWcorelib import Utils

        state = {
            "started": False,
            "resume_ms": 0,
        }

        def _reset_state() -> None:
            state["started"] = False
            state["resume_ms"] = 0

        def _restock_items(node: BehaviorTree.Node) -> BehaviorTree.NodeState:
            now = int(Utils.GetBaseTimestamp())
            current_bags = int(GLOBAL_CACHE.Inventory.GetModelCount(model_id) or 0)
            desired = int(desired_quantity)

            if current_bags >= desired:
                _reset_state()
                return BehaviorTree.NodeState.SUCCESS

            if not state["started"]:
                needed = desired - current_bags
                available = int(GLOBAL_CACHE.Inventory.GetModelCountInStorage(model_id) or 0)
                if needed <= 0:
                    _reset_state()
                    return BehaviorTree.NodeState.SUCCESS
                if available <= 0:
                    _reset_state()
                    return BehaviorTree.NodeState.SUCCESS if allow_missing else BehaviorTree.NodeState.FAILURE

                moved = bool(GLOBAL_CACHE.Inventory.WithdrawItemFromStorageByModelID(model_id, needed))
                if not moved:
                    fallback_amount = min(needed, available)
                    if fallback_amount > 0:
                        moved = bool(GLOBAL_CACHE.Inventory.WithdrawItemFromStorageByModelID(model_id, fallback_amount))
                    if not moved:
                        _reset_state()
                        return BehaviorTree.NodeState.SUCCESS if allow_missing else BehaviorTree.NodeState.FAILURE

                state["started"] = True
                state["resume_ms"] = now + 100
                node.blackboard["restock_items_last_model_id"] = int(model_id)
                node.blackboard["restock_items_last_requested_quantity"] = desired
                return BehaviorTree.NodeState.RUNNING

            if now < int(state["resume_ms"]):
                return BehaviorTree.NodeState.RUNNING

            final_bags = int(GLOBAL_CACHE.Inventory.GetModelCount(model_id) or 0)
            _reset_state()
            if final_bags >= desired:
                return BehaviorTree.NodeState.SUCCESS
            return BehaviorTree.NodeState.SUCCESS if allow_missing else BehaviorTree.NodeState.FAILURE

        return BehaviorTree(
            BehaviorTree.ActionNode(
                name=f"RestockItems({model_id},{desired_quantity})",
                action_fn=_restock_items,
            )
        )

    @staticmethod
    def RestockItemsFromList(
        items: Sequence[tuple[int, int]],
        allow_missing: bool = False,
    ) -> BehaviorTree:
        """
        Build a tree that restocks multiple inventory models from storage up to their requested quantities.

        Meta:
          Expose: true
          Audience: intermediate
          Display: Restock Items From List
          Purpose: Restock several models from storage in sequence using `(model_id, desired_quantity)` pairs.
          UserDescription: Use this when a step needs several consumables or items restocked before leaving outpost.
          Notes: Reuses the single-item restock routine for each list entry and preserves the same allow-missing behavior.
        """
        return BTComposite.Sequence(
            *[
                BTItems.RestockItems(
                    model_id=int(model_id),
                    desired_quantity=int(desired_quantity),
                    allow_missing=allow_missing,
                )
                for model_id, desired_quantity in items
            ],
            name="RestockItemsFromList",
        )

    @staticmethod
    def DepositModelToStorage(model_id: int, aftercast_ms: int = 350) -> BehaviorTree:
        """
        Build a tree that deposits all inventory items of a specific model into storage.

        Meta:
          Expose: true
          Audience: intermediate
          Display: Deposit Model To Storage
          Purpose: Deposit all items matching a model id into Xunlai storage.
          UserDescription: Use this when you want to move one inventory model to storage.
          Notes: Repeats until no matching inventory item remains.
        """
        def _deposit_model_to_storage() -> BehaviorTree.NodeState:
            item_id = GLOBAL_CACHE.Inventory.GetFirstModelID(model_id)
            if item_id == 0:
                return BehaviorTree.NodeState.SUCCESS

            GLOBAL_CACHE.Inventory.DepositItemToStorage(item_id)
            return BehaviorTree.NodeState.RUNNING

        return BehaviorTree(
            BehaviorTree.ActionNode(
                name=f"DepositModelToStorage({model_id})",
                action_fn=_deposit_model_to_storage,
                aftercast_ms=aftercast_ms,
            )
        )

    @staticmethod
    def DepositGoldKeep(gold_amount_to_leave_on_character: int = 0, aftercast_ms: int = 350) -> BehaviorTree:
        """
        Build a tree that deposits character gold while preserving a requested amount on the character.

        Meta:
          Expose: true
          Audience: intermediate
          Display: Deposit Gold Keep
          Purpose: Deposit as much gold as possible into storage while leaving a specified amount on the character.
          UserDescription: Use this when you want to clean up character gold without fully emptying it.
          Notes: Obeys storage cap and succeeds quietly when nothing needs to be deposited.
        """
        def _deposit_gold_keep() -> BehaviorTree.NodeState:
            gold_on_character = GLOBAL_CACHE.Inventory.GetGoldOnCharacter()
            gold_in_storage = GLOBAL_CACHE.Inventory.GetGoldInStorage()
            if gold_on_character <= gold_amount_to_leave_on_character:
                return BehaviorTree.NodeState.SUCCESS

            available_storage = max(0, 1_000_000 - gold_in_storage)
            gold_to_deposit = min(
                gold_on_character - gold_amount_to_leave_on_character,
                available_storage,
            )
            if gold_to_deposit <= 0:
                return BehaviorTree.NodeState.SUCCESS

            GLOBAL_CACHE.Inventory.DepositGold(gold_to_deposit)
            return BehaviorTree.NodeState.SUCCESS

        return BehaviorTree(
            BehaviorTree.ActionNode(
                name=f"DepositGoldKeep({gold_amount_to_leave_on_character})",
                action_fn=_deposit_gold_keep,
                aftercast_ms=aftercast_ms,
            )
        )

    @staticmethod
    def EqualizeGold(
        target_gold: int,
        deposit_all: bool = True,
        log: bool = False,
        aftercast_ms: int = 150,
    ) -> BehaviorTree:
        """
        Build a tree that adjusts character gold toward a target amount by optionally depositing excess first and then withdrawing.

        Meta:
          Expose: true
          Audience: intermediate
          Display: Withdraw Gold
          Purpose: Bring character gold toward a target amount while respecting storage availability and cap.
          UserDescription: Use this when a step needs a target amount of character gold before proceeding.
          Notes: Mirrors the existing yield helper flow: deposit excess if requested, wait, then withdraw toward target and wait again.
        """
        from ...Py4GWcorelib import Utils

        state = {
            "stage": "init",
            "resume_ms": 0,
        }

        def _reset_state() -> None:
            state["stage"] = "init"
            state["resume_ms"] = 0

        def _withdraw_gold() -> BehaviorTree.NodeState:
            now = int(Utils.GetBaseTimestamp())

            if state["stage"] == "wait_after_deposit":
                if now < int(state["resume_ms"]):
                    return BehaviorTree.NodeState.RUNNING
                state["stage"] = "withdraw"

            if state["stage"] == "wait_after_withdraw":
                if now < int(state["resume_ms"]):
                    return BehaviorTree.NodeState.RUNNING
                _reset_state()
                return BehaviorTree.NodeState.SUCCESS

            gold_on_char = int(GLOBAL_CACHE.Inventory.GetGoldOnCharacter() or 0)

            if state["stage"] == "init":
                if deposit_all and gold_on_char > target_gold:
                    to_deposit = gold_on_char - int(target_gold)
                    gold_in_storage = int(GLOBAL_CACHE.Inventory.GetGoldInStorage() or 0)
                    available_space = max(0, 1_000_000 - gold_in_storage)
                    to_deposit = min(to_deposit, available_space)
                    if to_deposit > 0:
                        GLOBAL_CACHE.Inventory.DepositGold(to_deposit)
                        if log:
                            _log("WithdrawGold", f"Deposited {to_deposit} gold (excess).", message_type=Console.MessageType.Info, log=log)
                        state["stage"] = "wait_after_deposit"
                        state["resume_ms"] = now + max(0, int(aftercast_ms))
                        return BehaviorTree.NodeState.RUNNING
                state["stage"] = "withdraw"

            if state["stage"] == "withdraw":
                if gold_on_char < target_gold:
                    to_withdraw = int(target_gold) - gold_on_char
                    gold_in_storage = int(GLOBAL_CACHE.Inventory.GetGoldInStorage() or 0)
                    to_withdraw = min(to_withdraw, gold_in_storage)
                    if to_withdraw > 0:
                        GLOBAL_CACHE.Inventory.WithdrawGold(to_withdraw)
                        if log:
                            _log("WithdrawGold", f"Withdrew {to_withdraw} gold.", message_type=Console.MessageType.Info, log=log)
                        state["stage"] = "wait_after_withdraw"
                        state["resume_ms"] = now + max(0, int(aftercast_ms))
                        return BehaviorTree.NodeState.RUNNING
                    _fail_log("WithdrawGold", "Not enough gold in storage to reach target.")
                _reset_state()
                return BehaviorTree.NodeState.SUCCESS

            _reset_state()
            return BehaviorTree.NodeState.FAILURE

        return BehaviorTree(
            BehaviorTree.ActionNode(
                name=f"WithdrawGold({target_gold})",
                action_fn=_withdraw_gold,
            )
        )

    @staticmethod
    def BuyMaterial(
        model_id: int,
        log: bool = False,
        aftercast_ms: int = 250,
    ) -> BehaviorTree:
        return BTItems.BuyMaterials(
            model_id=model_id,
            batches=1,
            log=log,
            aftercast_ms=aftercast_ms,
        )

    @staticmethod
    def BuyMaterials(
        model_id: int,
        batches: int = 1,
        log: bool = False,
        aftercast_ms: int = 250,
    ) -> BehaviorTree:
        """
        Build a tree that buys one or more material-trader batches of the requested material.

        Meta:
          Expose: true
          Audience: intermediate
          Display: Buy Materials
          Purpose: Buy one or more batches of a material from the currently open trader window.
          UserDescription: Use this when a material trader is already open and you need to buy a material multiple times.
          Notes: Mirrors the original helper flow: resolve the offered item, request a quote, wait for the quote, buy, wait for completion, then repeat for the requested batch count.
        """
        target_batches = max(0, int(batches))
        state = {
            "stage": "init",
            "item_id": 0,
            "remaining_batches": target_batches,
        }

        def _reset_state() -> None:
            state["stage"] = "init"
            state["item_id"] = 0
            state["remaining_batches"] = target_batches

        def _is_material_trader() -> bool:
            merchant_models = [
                GLOBAL_CACHE.Item.GetModelID(item_id)
                for item_id in GLOBAL_CACHE.Trading.Trader.GetOfferedItems()
            ]
            return ModelID.Wood_Plank.value in merchant_models

        def _buy_material() -> BehaviorTree.NodeState:
            if state["remaining_batches"] <= 0:
                _reset_state()
                return BehaviorTree.NodeState.SUCCESS

            if state["stage"] == "init":
                item_id = 0
                for candidate in GLOBAL_CACHE.Trading.Trader.GetOfferedItems():
                    if GLOBAL_CACHE.Item.GetModelID(candidate) == model_id:
                        item_id = candidate
                        break

                if item_id == 0:
                    _fail_log("BuyMaterial", f"Model {model_id} not sold here.")
                    _reset_state()
                    return BehaviorTree.NodeState.FAILURE

                state["item_id"] = item_id
                GLOBAL_CACHE.Trading.Trader.RequestQuote(item_id)
                state["stage"] = "wait_for_quote"
                return BehaviorTree.NodeState.RUNNING

            if state["stage"] == "wait_for_quote":
                cost = int(GLOBAL_CACHE.Trading.Trader.GetQuotedValue() or -1)
                if cost < 0:
                    return BehaviorTree.NodeState.RUNNING

                if cost == 0:
                    _fail_log("BuyMaterial", f"Item {state['item_id']} has no price.")
                    _reset_state()
                    return BehaviorTree.NodeState.FAILURE

                GLOBAL_CACHE.Trading.Trader.BuyItem(int(state["item_id"]), cost)
                state["stage"] = "wait_for_completion"
                return BehaviorTree.NodeState.RUNNING

            if state["stage"] == "wait_for_completion":
                if not GLOBAL_CACHE.Trading.IsTransactionComplete():
                    return BehaviorTree.NodeState.RUNNING

                state["remaining_batches"] -= 1
                if log:
                    quantity = 10 if _is_material_trader() else 1
                    _log(
                        "BuyMaterials",
                        f"Bought batch {target_batches - state['remaining_batches']}/{target_batches} for model {model_id} ({quantity} units).",
                        message_type=Console.MessageType.Success,
                        log=log,
                    )
                if state["remaining_batches"] <= 0:
                    _reset_state()
                    return BehaviorTree.NodeState.SUCCESS

                state["stage"] = "init"
                state["item_id"] = 0
                return BehaviorTree.NodeState.RUNNING

            _reset_state()
            return BehaviorTree.NodeState.FAILURE

        return BehaviorTree(
            BehaviorTree.ActionNode(
                name=f"BuyMaterials({model_id}, {target_batches})",
                action_fn=_buy_material,
                aftercast_ms=aftercast_ms,
            )
        )

    @staticmethod
    def BuyMaterialsFromList(
        materials: list[tuple[int, int]],
        log: bool = False,
        aftercast_ms: int = 125,
    ) -> BehaviorTree:
        """
        Build a tree that buys multiple materials from a list of `(model_id, batches)` entries.

        Meta:
          Expose: true
          Audience: intermediate
          Display: Buy Materials From List
          Purpose: Buy several material batches from the currently open trader window.
          UserDescription: Use this when a material trader is already open and you want to buy a prepared list of materials and batch counts.
          Notes: Runs the existing single-material BT purchase routine sequentially for each entry in the provided list.
        """
        return BehaviorTree(
            BehaviorTree.SequenceNode(
                name="BuyMaterialsFromList",
                children=[
                    BTItems.BuyMaterials(
                        model_id=model_id,
                        batches=batches,
                        log=log,
                        aftercast_ms=aftercast_ms,
                    ).root
                    for model_id, batches in materials
                ],
            )
        )

    @staticmethod
    def BuyMerchantItem(
        model_id: int,
        quantity: int = 1,
        log: bool = False,
        aftercast_ms: int = 250,
    ) -> BehaviorTree:
        """
        Build a tree that buys one or more copies of a merchant item by model id.

        Meta:
          Expose: true
          Audience: intermediate
          Display: Buy Merchant Item
          Purpose: Buy one or more copies of a standard merchant item from the currently open merchant window.
          UserDescription: Use this when a merchant window is already open and you want to buy a specific item model a fixed number of times.
          Notes: Resolves the offered item once, buys at merchant price, then waits for each transaction to complete before the next purchase.
        """
        target_quantity = max(0, int(quantity))
        state = {
            "stage": "init",
            "item_id": 0,
            "remaining_quantity": target_quantity,
            "item_value": 0,
        }

        def _reset_state() -> None:
            state["stage"] = "init"
            state["item_id"] = 0
            state["remaining_quantity"] = target_quantity
            state["item_value"] = 0

        def _buy_merchant_item() -> BehaviorTree.NodeState:
            if state["remaining_quantity"] <= 0:
                _reset_state()
                return BehaviorTree.NodeState.SUCCESS

            if state["stage"] == "init":
                item_id = 0
                item_value = 0
                for candidate in GLOBAL_CACHE.Trading.Merchant.GetOfferedItems():
                    if GLOBAL_CACHE.Item.GetModelID(candidate) != model_id:
                        continue
                    item_id = candidate
                    item_value = int(GLOBAL_CACHE.Item.Properties.GetValue(candidate) or 0)
                    break

                if item_id == 0 or item_value <= 0:
                    _fail_log("BuyMerchantItem", f"Model {model_id} not sold here.")
                    _reset_state()
                    return BehaviorTree.NodeState.FAILURE

                state["item_id"] = item_id
                state["item_value"] = item_value
                GLOBAL_CACHE.Trading.Merchant.BuyItem(item_id, item_value * 2)
                state["stage"] = "wait_for_completion"
                return BehaviorTree.NodeState.RUNNING

            if state["stage"] == "wait_for_completion":
                if not GLOBAL_CACHE.Trading.IsTransactionComplete():
                    return BehaviorTree.NodeState.RUNNING

                state["remaining_quantity"] -= 1
                if log:
                    _log(
                        "BuyMerchantItem",
                        f"Bought {target_quantity - state['remaining_quantity']}/{target_quantity} of model {model_id}.",
                        message_type=Console.MessageType.Success,
                        log=log,
                    )
                if state["remaining_quantity"] <= 0:
                    _reset_state()
                    return BehaviorTree.NodeState.SUCCESS

                state["stage"] = "init"
                return BehaviorTree.NodeState.RUNNING

            _reset_state()
            return BehaviorTree.NodeState.FAILURE

        return BehaviorTree(
            BehaviorTree.ActionNode(
                name=f"BuyMerchantItem({model_id}, {target_quantity})",
                action_fn=_buy_merchant_item,
                aftercast_ms=aftercast_ms,
            )
        )

    @staticmethod
    def ExchangeCollectorItem(
        output_model_id: int,
        trade_model_ids: list[int],
        quantity_list: list[int],
        cost: int = 0,
        aftercast_ms: int = 250,
    ) -> BehaviorTree:
        """
        Build a tree that exchanges collector items based on the specified output model, trade models, and quantities.

        Meta:
          Expose: true
          Audience: intermediate
          Display: Exchange Collector Item
          Purpose: Exchange collector items based on the specified output model, trade models, and quantities.
          UserDescription: Use this when you want to exchange collector items with specific models and quantities.
          Notes: Returns success if the exchange is successful, and failure otherwise.
        """
        def _exchange_item() -> BehaviorTree.NodeState:
            k = min(len(trade_model_ids), len(quantity_list))
            if k == 0:
                return BehaviorTree.NodeState.FAILURE

            requested_models = trade_model_ids[:k]
            requested_quantities = quantity_list[:k]

            offered_item_id = 0
            for candidate in GLOBAL_CACHE.Trading.Collector.GetOfferedItems():
                if GLOBAL_CACHE.Item.GetModelID(candidate) == output_model_id:
                    offered_item_id = candidate
                    break

            if offered_item_id == 0:
                return BehaviorTree.NodeState.FAILURE

            trade_item_ids: list[int] = []
            trade_item_quantities: list[int] = []

            for model_id, required_quantity in zip(requested_models, requested_quantities):
                remaining_quantity = int(required_quantity)

                for item_id in GLOBAL_CACHE.Inventory.GetAllInventoryItemIds():
                    if item_id == 0:
                        continue
                    if GLOBAL_CACHE.Item.GetModelID(item_id) != model_id:
                        continue

                    item_quantity = int(GLOBAL_CACHE.Item.Properties.GetQuantity(item_id) or 1)
                    if item_quantity <= 0:
                        continue

                    used_quantity = min(item_quantity, remaining_quantity)
                    trade_item_ids.append(item_id)
                    trade_item_quantities.append(used_quantity)
                    remaining_quantity -= used_quantity

                    if remaining_quantity <= 0:
                        break

                if remaining_quantity > 0:
                    return BehaviorTree.NodeState.FAILURE

            GLOBAL_CACHE.Trading.Collector.ExchangeItem(
                offered_item_id,
                cost,
                trade_item_ids,
                trade_item_quantities,
            )
            return BehaviorTree.NodeState.SUCCESS

        return BehaviorTree(
            BehaviorTree.ActionNode(
                name=f"ExchangeCollectorItem({output_model_id})",
                action_fn=_exchange_item,
                aftercast_ms=aftercast_ms,
            )
        )

    @staticmethod
    def CraftItem(
        output_model_id: int,
        cost: int,
        trade_model_ids: list[int],
        quantity_list: list[int],
        aftercast_ms: int = 500,
    ) -> BehaviorTree:
        """
        Build a tree that crafts an offered item using the requested trade materials and gold cost.

        Meta:
          Expose: true
          Audience: intermediate
          Display: Craft Item
          Purpose: Craft an offered item through the crafter window.
          UserDescription: Use this when a crafter is already open and you want to craft a specific offered model.
          Notes: Resolves the offered item id and the input inventory item ids before dispatching the craft action.
        """
        def _craft_item() -> BehaviorTree.NodeState:
            k = min(len(trade_model_ids), len(quantity_list))
            if k == 0:
                return BehaviorTree.NodeState.FAILURE

            target_item_id = 0
            for offered_item_id in GLOBAL_CACHE.Trading.Merchant.GetOfferedItems():
                if GLOBAL_CACHE.Item.GetModelID(offered_item_id) == output_model_id:
                    target_item_id = offered_item_id
                    break
            if target_item_id == 0:
                return BehaviorTree.NodeState.FAILURE

            trade_item_ids: list[int] = []
            for model_id in trade_model_ids[:k]:
                item_id = GLOBAL_CACHE.Inventory.GetFirstModelID(model_id)
                if item_id == 0:
                    return BehaviorTree.NodeState.FAILURE
                trade_item_ids.append(item_id)

            GLOBAL_CACHE.Trading.Crafter.CraftItem(
                target_item_id,
                cost,
                trade_item_ids,
                quantity_list[:k],
            )
            return BehaviorTree.NodeState.SUCCESS

        return BehaviorTree(
            BehaviorTree.ActionNode(
                name=f"CraftItem({output_model_id})",
                action_fn=_craft_item,
                aftercast_ms=aftercast_ms,
            )
        )

    @staticmethod
    def _collect_sellable_inventory_item_ids(exclude_models: list[int] | None = None) -> list[int]:
        excluded_models = set(exclude_models or [])
        sellable_item_ids: list[int] = []

        for item_id in GLOBAL_CACHE.Inventory.GetAllInventoryItemIds():
            if item_id == 0:
                continue

            model_id = GLOBAL_CACHE.Item.GetModelID(item_id)
            if model_id in excluded_models:
                continue

            item_value = GLOBAL_CACHE.Item.Properties.GetValue(item_id)
            if item_value <= 0:
                continue

            sellable_item_ids.append(item_id)

        return sellable_item_ids
    
    @staticmethod
    def _collect_zero_value_inventory_item_ids(exclude_models: list[int] | None = None) -> list[int]:
        excluded_models = set(exclude_models or [])
        zero_value_item_ids: list[int] = []

        for item_id in GLOBAL_CACHE.Inventory.GetAllInventoryItemIds():
            if item_id == 0:
                continue

            model_id = GLOBAL_CACHE.Item.GetModelID(item_id)
            if model_id in excluded_models:
                continue

            item_value = GLOBAL_CACHE.Item.Properties.GetValue(item_id)
            if item_value > 0:
                continue

            zero_value_item_ids.append(item_id)

        return zero_value_item_ids

    @staticmethod
    def NeedsInventoryCleanup(exclude_models: list[int] | None = None) -> BehaviorTree:
        def _needs_inventory_cleanup() -> bool:
            return bool(BTItems._collect_sellable_inventory_item_ids(exclude_models=exclude_models)) or bool(
                BTItems._collect_zero_value_inventory_item_ids(exclude_models=exclude_models)
            )

        return BehaviorTree(
            BehaviorTree.ConditionNode(
                name="NeedsInventoryCleanupExcluding",
                condition_fn=_needs_inventory_cleanup,
            )
        )

    @staticmethod
    def SellInventoryItems(
        exclude_models: list[int] | None = None,
        log: bool = False,
    ) -> BehaviorTree:
        """
        Build a tree that sells all inventory items with value greater than zero while excluding specified models.

        Meta:
          Expose: true
          Audience: intermediate
          Display: Sell Inventory Items
          Purpose: Sell all inventory items with value greater than zero while excluding specified models.
          UserDescription: Use this when you want to clear out inventory space by selling items but want to keep certain models.
          Notes: Processes all eligible items in a single tick by queuing them up in the merchant action queue; logs the count of sold items if logging is enabled.
        """
        def _collect_items(node: BehaviorTree.Node) -> BehaviorTree.NodeState:
            sellable_item_ids = BTItems._collect_sellable_inventory_item_ids(exclude_models=exclude_models)
            node.blackboard["merchant_sell_item_ids"] = sellable_item_ids
            node.blackboard["merchant_sell_queued_count"] = 0

            if not sellable_item_ids:
                if log:
                    _log(
                        "SellInventoryItems",
                        "No eligible inventory items found to sell.",
                        message_type=Console.MessageType.Info,
                        log=True,
                    )
                return BehaviorTree.NodeState.SUCCESS

            if log:
                excluded_models_text = ", ".join(str(model_id) for model_id in sorted(set(exclude_models or []))) or "none"
                _log(
                    "SellInventoryItems",
                    f"Selling {len(sellable_item_ids)} inventory items. Excluded models: {excluded_models_text}.",
                    message_type=Console.MessageType.Info,
                    log=True,
                )

            return BehaviorTree.NodeState.SUCCESS

        def _queue_sell_items(node: BehaviorTree.Node) -> BehaviorTree.NodeState:
            from Py4GWCoreLib.Py4GWcorelib import ActionQueueManager
            item_ids = list(node.blackboard.get("merchant_sell_item_ids", []))
            if not item_ids:
                node.blackboard["merchant_sell_queued_count"] = 0
                return BehaviorTree.NodeState.SUCCESS

            merchant_queue = ActionQueueManager()
            merchant_queue.ResetQueue("ACTION")

            queued_count = 0
            for item_id in item_ids:
                quantity = GLOBAL_CACHE.Item.Properties.GetQuantity(item_id)
                value = GLOBAL_CACHE.Item.Properties.GetValue(item_id)
                cost = quantity * value

                if quantity <= 0 or value <= 0:
                    continue

                merchant_queue.AddAction(
                    "ACTION",
                    GLOBAL_CACHE.Trading._merchant_instance.merchant_sell_item,
                    item_id,
                    cost,
                )
                queued_count += 1

            node.blackboard["merchant_sell_queued_count"] = queued_count
            return BehaviorTree.NodeState.SUCCESS

        def _wait_for_sell_queue_to_finish(node: BehaviorTree.Node) -> BehaviorTree.NodeState:
            from Py4GWCoreLib.Py4GWcorelib import ActionQueueManager
            queued_count = int(node.blackboard.get("merchant_sell_queued_count", 0) or 0)
            if queued_count <= 0:
                return BehaviorTree.NodeState.SUCCESS

            if not ActionQueueManager().IsEmpty("ACTION"):
                return BehaviorTree.NodeState.RUNNING

            if log:
                _log(
                    "SellInventoryItems",
                    f"Sold {queued_count} inventory items through merchant queue.",
                    message_type=Console.MessageType.Info,
                    log=True,
                )
            return BehaviorTree.NodeState.SUCCESS

        tree = BehaviorTree.SequenceNode(
            name="SellInventoryItemsExcluding",
            children=[
                BehaviorTree.ActionNode(
                    name="CollectSellableInventoryItems",
                    action_fn=_collect_items,
                    aftercast_ms=0,
                ),
                BehaviorTree.ActionNode(
                    name="QueueMerchantSellItems",
                    action_fn=_queue_sell_items,
                    aftercast_ms=0,
                ),
                BehaviorTree.ActionNode(
                    name="WaitForMerchantSellQueue",
                    action_fn=_wait_for_sell_queue_to_finish,
                    aftercast_ms=0,
                ),
            ],
        )
        return BehaviorTree(tree)

    @staticmethod
    def DestroyZeroValueItems(
        exclude_models: list[int] | None = None,
        log: bool = False,
        aftercast_ms: int = 100,
    ) -> BehaviorTree:
        state = {
            "next_attempt_ms": 0,
        }

        def _collect_items(node: BehaviorTree.Node) -> BehaviorTree.NodeState:
            zero_value_item_ids = BTItems._collect_zero_value_inventory_item_ids(exclude_models=exclude_models)
            node.blackboard["zero_value_destroy_item_ids"] = zero_value_item_ids
            node.blackboard["zero_value_destroy_index"] = 0
            return BehaviorTree.NodeState.SUCCESS

        def _destroy_items(node: BehaviorTree.Node) -> BehaviorTree.NodeState:
            from Py4GWCoreLib.Py4GWcorelib import Utils
            now = Utils.GetBaseTimestamp()
            if now < int(state["next_attempt_ms"]):
                return BehaviorTree.NodeState.RUNNING

            item_ids = list(node.blackboard.get("zero_value_destroy_item_ids", []))
            item_index = int(node.blackboard.get("zero_value_destroy_index", 0) or 0)
            if item_index >= len(item_ids):
                return BehaviorTree.NodeState.SUCCESS

            item_id = item_ids[item_index]
            model_id = GLOBAL_CACHE.Item.GetModelID(item_id)
            GLOBAL_CACHE.Inventory.DestroyItem(item_id)
            node.blackboard["zero_value_destroy_index"] = item_index + 1
            state["next_attempt_ms"] = int(now + aftercast_ms)

            if log:
                _log(
                    "DestroyZeroValueItems",
                    f"Queued destroy for zero-value item model {model_id} (item_id={item_id}).",
                    message_type=Console.MessageType.Info,
                    log=True,
                )

            return BehaviorTree.NodeState.RUNNING

        return BehaviorTree(
            BehaviorTree.SequenceNode(
                name="DestroyZeroValueItemsExcluding",
                children=[
                    BehaviorTree.ActionNode(
                        name="CollectZeroValueItems",
                        action_fn=_collect_items,
                        aftercast_ms=0,
                    ),
                    BehaviorTree.ConditionNode(
                        name="DestroyZeroValueItems",
                        condition_fn=_destroy_items,
                    ),
                ],
            )
        )
