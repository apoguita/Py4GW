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
from ...enums_src.Model_enums import ModelID
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
