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

from ...Agent import Agent
from ...GlobalCache import GLOBAL_CACHE
from ...Player import Player
from ...Py4GWcorelib import ConsoleLog, Console
from ...UIManager import UIManager
from ...enums_src.Item_enums import Bags
from ...enums_src.Model_enums import ModelID
from ...enums_src.UI_enums import ControlAction
from ...py4gwcorelib_src.BehaviorTree import BehaviorTree
from .composite import BTComposite
from .player import BTPlayer


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
    def EquipItemByModelID(modelID_or_encStr: int | str, aftercast_ms: int = 750) -> BehaviorTree:
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
            item_id = GLOBAL_CACHE.Inventory.GetFirstModelID(resolved_model_id)
            if item_id == 0:
                return BehaviorTree.NodeState.FAILURE

            GLOBAL_CACHE.Inventory.EquipItem(item_id, Player.GetAgentID())
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
                    ConsoleLog(
                        "EquipInventoryBag",
                        f"Item model {resolved_model_id} not found in inventory.",
                        Console.MessageType.Error,
                        log=True,
                    )
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
                    ConsoleLog(
                        "EquipInventoryBag",
                        f"Native UseItem did not populate bag {target_bag}; trying backpack slot double-click fallback for model {int(state['resolved_model_id'])}.",
                        Console.MessageType.Warning,
                        log=log,
                    )
                    state["stage"] = "fallback_wait_before_open"
                    state["next_check_ms"] = now + 250
                else:
                    ConsoleLog(
                        "EquipInventoryBag",
                        f"Fallback move to backpack slot 0 failed for model {int(state['resolved_model_id'])}.",
                        Console.MessageType.Warning,
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
                state["next_check_ms"] = now + 125
                return BehaviorTree.NodeState.RUNNING

            if state["stage"] == "fallback_toggle_bags_release":
                if now < int(state["key_up_ms"]):
                    return BehaviorTree.NodeState.RUNNING

                UIManager.Keyup(ControlAction.ControlAction_ToggleAllBags.value, 0)
                state["stage"] = "fallback_wait_before_double_click"
                state["next_check_ms"] = now + 175
                return BehaviorTree.NodeState.RUNNING

            if state["stage"] == "fallback_wait_before_double_click":
                if now < int(state["next_check_ms"]):
                    return BehaviorTree.NodeState.RUNNING

                frame_id = _get_backpack_slot_frame_id()
                if not UIManager.FrameExists(frame_id):
                    ConsoleLog(
                        "EquipInventoryBag",
                        "Frame does not exist for backpack slot 0.",
                        Console.MessageType.Error,
                        log=True,
                    )
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
                    ConsoleLog(
                        "EquipInventoryBag",
                        "Frame does not exist for backpack slot 0.",
                        Console.MessageType.Error,
                        log=True,
                    )
                    _reset_state()
                    return BehaviorTree.NodeState.FAILURE

                UIManager.TestMouseClickAction(frame_id=frame_id, current_state=9, wparam_value=0, lparam_value=0)
                state["stage"] = "final_wait"
                state["next_check_ms"] = now + 125
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

                ConsoleLog(
                    "EquipInventoryBag",
                    (
                        f"Failed to equip model {int(state['resolved_model_id'])} item {int(state['item_id'])} into bag {target_bag} within {timeout_ms}ms. "
                        f"container_item={GLOBAL_CACHE.Inventory.GetBagContainerItem(target_bag)} "
                        f"size={GLOBAL_CACHE.Inventory.GetBagSize(target_bag)}."
                    ),
                    Console.MessageType.Error,
                    log=True,
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
            ConsoleLog("SpawnBonusItems", "Sent /bonus command.", Console.MessageType.Info, log=log)
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
                ConsoleLog(
                    "DestroyItem",
                    f"Item model {resolved_model_id} was not found in inventory for destruction.",
                    Console.MessageType.Warning if required else Console.MessageType.Info,
                    log=True,
                )
                if required:
                    ConsoleLog(
                        "DestroyItem",
                        f"Item model {resolved_model_id} was not found for destruction.",
                        Console.MessageType.Warning,
                        log=True if required else log,
                    )
                    return BehaviorTree.NodeState.FAILURE
                return BehaviorTree.NodeState.SUCCESS

            GLOBAL_CACHE.Inventory.DestroyItem(item_id)
            ConsoleLog(
                "DestroyItem",
                f"Queued destroy for item model {resolved_model_id} (item_id={item_id}).",
                Console.MessageType.Info,
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
        aftercast_ms: int = 100,
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
                ConsoleLog(
                    "DestroyItems",
                    f"Queued destroy for item model {model_id} (item_id={item_id}).",
                    Console.MessageType.Info,
                    log=log,
                )
                return BehaviorTree.NodeState.RUNNING

            ConsoleLog(
                "DestroyItems",
                f"Destroy pass completed for models: {models_to_destroy}",
                Console.MessageType.Info,
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
                    ConsoleLog("WaitForAnyModelInInventory", f"Detected inventory model {model_id} as item_id={item_id}.", Console.MessageType.Info, log=log)
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
                    ConsoleLog(
                        "MoveModelToBagSlot",
                        f"Failed to move model {resolved_model_id} to bag {target_bag} slot {slot}.",
                        Console.MessageType.Warning,
                        log=True if required else log,
                    )
                    return BehaviorTree.NodeState.FAILURE
                return BehaviorTree.NodeState.SUCCESS

            ConsoleLog(
                "MoveModelToBagSlot",
                f"Moved model {resolved_model_id} to bag {target_bag} slot {slot}.",
                Console.MessageType.Info,
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
    def ExchangeCollectorItem(
        output_model_id: int,
        trade_model_ids: list[int],
        quantity_list: list[int],
        cost: int = 0,
        aftercast_ms: int = 500,
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

            GLOBAL_CACHE.Trading.Collector.ExghangeItem(
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
                    ConsoleLog(
                        "SellInventoryItems",
                        "No eligible inventory items found to sell.",
                        Console.MessageType.Info,
                        log=True,
                    )
                return BehaviorTree.NodeState.SUCCESS

            if log:
                excluded_models_text = ", ".join(str(model_id) for model_id in sorted(set(exclude_models or []))) or "none"
                ConsoleLog(
                    "SellInventoryItems",
                    f"Selling {len(sellable_item_ids)} inventory items. Excluded models: {excluded_models_text}.",
                    Console.MessageType.Info,
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
            merchant_queue.ResetQueue("MERCHANT")

            queued_count = 0
            for item_id in item_ids:
                quantity = GLOBAL_CACHE.Item.Properties.GetQuantity(item_id)
                value = GLOBAL_CACHE.Item.Properties.GetValue(item_id)
                cost = quantity * value

                if quantity <= 0 or value <= 0:
                    continue

                merchant_queue.AddAction(
                    "MERCHANT",
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

            if not ActionQueueManager().IsEmpty("MERCHANT"):
                return BehaviorTree.NodeState.RUNNING

            if log:
                ConsoleLog(
                    "SellInventoryItems",
                    f"Sold {queued_count} inventory items through merchant queue.",
                    Console.MessageType.Info,
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
                ConsoleLog(
                    "DestroyZeroValueItems",
                    f"Queued destroy for zero-value item model {model_id} (item_id={item_id}).",
                    Console.MessageType.Info,
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

