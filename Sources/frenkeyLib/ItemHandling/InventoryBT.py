from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Sequence, cast

import Py4GW

from Py4GWCoreLib.Item import Bag
from Py4GWCoreLib.Map import Map
from Py4GWCoreLib.enums_src.Item_enums import INVENTORY_BAGS, STORAGE_BAGS, Bags, ItemAction, ItemType, SalvageMode
from Py4GWCoreLib.enums_src.Model_enums import ModelID
from Py4GWCoreLib.py4gwcorelib_src.BehaviorTree import BehaviorTree
from Py4GWCoreLib.py4gwcorelib_src.FrameCache import frame_cache
from Sources.frenkeyLib.ItemHandling.UIManagerExtensions import UIManagerExtensions
from Sources.frenkeyLib.ItemHandling.BTNodes import BTNodes
from Sources.frenkeyLib.ItemHandling.GlobalConfigs.InventoryConfig import InventoryConfig
from Sources.frenkeyLib.ItemHandling.GlobalConfigs.Rule import ExtractUpgradeRule, Rule
from Py4GWCoreLib.item_data.item_snapshot import ItemSnapshot

@dataclass(slots=True)
class InventoryPreviewEntry:
    item: ItemSnapshot
    action: Optional[ItemAction]
    rule: Optional[Rule]
    note: str = ""
    executable: bool = True


class InventoryBT:
    NodeState = BehaviorTree.NodeState

    _ACTIVE_NODE_KEY = "inventory_bt_active_node"
    _ACTIVE_ACTION_KEY = "inventory_bt_active_action"
    _ACTIVE_ITEM_IDS_KEY = "inventory_bt_active_item_ids"
    _EXTRACT_WARNING_CACHE_KEY = "inventory_bt_extract_warning_cache"
    _ITEM_COOLDOWNS_KEY = "inventory_bt_item_cooldowns"
    _SUCCESS_COOLDOWN_TICKS = 1
    _FAILURE_COOLDOWN_TICKS = 15

    ACTION_PRIORITY: tuple[ItemAction, ...] = (
        ItemAction.Sell_To_Merchant,
        ItemAction.Sell_To_Trader,
        ItemAction.Stash,
        ItemAction.Destroy,
        ItemAction.Drop,
        ItemAction.Use,
        ItemAction.Identify,
        ItemAction.Salvage_Common_Materials,
        ItemAction.Salvage_Rare_Materials,
        ItemAction.ExtractUpgrade,
    )

    def __init__(self, config: Optional[InventoryConfig] = None):
        self.config = config or InventoryConfig()
        self.tree = self.Build(self.config)

    def tick(self) -> BehaviorTree.NodeState:
        return self.tree.tick()

    def reset(self) -> None:
        self.tree.reset()
        self.tree.blackboard.pop(self._ACTIVE_NODE_KEY, None)
        self.tree.blackboard.pop(self._ACTIVE_ACTION_KEY, None)
        self.tree.blackboard.pop(self._ACTIVE_ITEM_IDS_KEY, None)
        self.tree.blackboard.pop(self._EXTRACT_WARNING_CACHE_KEY, None)
        self.tree.blackboard.pop(self._ITEM_COOLDOWNS_KEY, None)

    @classmethod
    def Build(cls, config: Optional[InventoryConfig] = None) -> BehaviorTree:
        inventory_config = config or InventoryConfig()
        return BehaviorTree(cls._build_root_node(inventory_config))

    @classmethod
    @frame_cache(category="InventoryBT", source_lib="Preview")
    def Preview(
        cls,
        config: Optional[InventoryConfig] = None,
        bags: Optional[Sequence[Bags]] = None,
    ) -> list[InventoryPreviewEntry]:
        inventory_config = config or InventoryConfig()
        preview_entries: list[InventoryPreviewEntry] = []
        preview_bags = list(bags) if bags is not None else INVENTORY_BAGS

        if not preview_bags:
            return preview_entries

        snapshot = ItemSnapshot.get_bags_snapshot(preview_bags)
        for bag in preview_bags:
            for item in snapshot.get(bag, {}).values():
                if item is None or not item.is_valid:
                    continue

                preview_entries.append(cls._build_preview_entry(inventory_config, item))

        return preview_entries

    @classmethod
    @frame_cache(category="InventoryBT", source_lib="GetExecuteableInventoryActions")
    def GetExecuteableInventoryActions(cls, config: InventoryConfig):
        entries = cls.Preview(config)
        return [
            entry for entry in entries
            if entry.executable and entry.action is not None and entry.action not in (ItemAction.NONE, ItemAction.Ignore)
        ]
    
    @classmethod
    @frame_cache(category="InventoryBT", source_lib="HasExecuteableInventoryActions")
    def HasExecuteableInventoryActions(cls, config: InventoryConfig) -> bool:
        entries = cls.Preview(config)
        return any(
             entry.executable and entry.action is not None and entry.action not in (ItemAction.NONE, ItemAction.Ignore)
             for entry in entries
        ) or cls._needs_inventory_sorting()
        
    @classmethod
    def _build_root_node(cls, config: InventoryConfig) -> BehaviorTree.Node:
        def _tick(node: BehaviorTree.Node) -> BehaviorTree.NodeState:            
            cls._advance_item_cooldowns(node.blackboard)
            active_node = cast(BehaviorTree.Node | None, node.blackboard.get(cls._ACTIVE_NODE_KEY))
            if active_node is not None:                
                active_node.blackboard = node.blackboard
                active_state = active_node.tick()

                if active_state == BehaviorTree.NodeState.RUNNING:
                    return BehaviorTree.NodeState.RUNNING

                active_item_ids = cast(list[int], node.blackboard.get(cls._ACTIVE_ITEM_IDS_KEY, []))
                node.blackboard.pop(cls._ACTIVE_NODE_KEY, None)
                node.blackboard.pop(cls._ACTIVE_ACTION_KEY, None)
                node.blackboard.pop(cls._ACTIVE_ITEM_IDS_KEY, None)

                if active_state == BehaviorTree.NodeState.FAILURE:
                    cls._set_item_cooldown(node.blackboard, active_item_ids, cls._FAILURE_COOLDOWN_TICKS)
                    return BehaviorTree.NodeState.FAILURE

                cls._set_item_cooldown(node.blackboard, active_item_ids, cls._SUCCESS_COOLDOWN_TICKS)
                return active_state

            action_batches = cls._collect_action_batches(config, node.blackboard)
            if not action_batches:
                if cls._needs_inventory_sorting():
                    action_node = BTNodes.Bags.SortBags(INVENTORY_BAGS)
                    Py4GW.Console.Log(
                        "InventoryBT",
                        "Dispatching inventory sort maintenance.",
                        Py4GW.Console.MessageType.Info,
                    )
                    node.blackboard[cls._ACTIVE_NODE_KEY] = action_node
                    node.blackboard[cls._ACTIVE_ACTION_KEY] = "SortInventory"
                    node.blackboard[cls._ACTIVE_ITEM_IDS_KEY] = []
                    action_node.blackboard = node.blackboard
                    return action_node.tick()

                return BehaviorTree.NodeState.SUCCESS

            for action in cls.ACTION_PRIORITY:
                item_ids = action_batches.get(action, [])
                if not item_ids:
                    continue

                action_node, active_item_ids = cls._build_action_node(config, action, item_ids, node.blackboard)
                if action_node is None:
                    continue

                Py4GW.Console.Log(
                    "InventoryBT",
                    f"Dispatching {action.name} for {len(item_ids)} item(s).",
                    Py4GW.Console.MessageType.Info,
                )

                node.blackboard[cls._ACTIVE_NODE_KEY] = action_node
                node.blackboard[cls._ACTIVE_ACTION_KEY] = action.name
                node.blackboard[cls._ACTIVE_ITEM_IDS_KEY] = active_item_ids
                action_node.blackboard = node.blackboard
                return action_node.tick()

            return BehaviorTree.NodeState.SUCCESS

        return BehaviorTree.ActionNode(name="InventoryBT.ProcessInventory", action_fn=_tick)

    @classmethod
    def _collect_action_batches(cls, config: InventoryConfig, blackboard: Optional[dict] = None) -> dict[ItemAction, list[int]]:
        action_batches: dict[ItemAction, list[int]] = {}
        item_cooldowns = cast(dict[int, int], blackboard.setdefault(cls._ITEM_COOLDOWNS_KEY, {})) if blackboard is not None else {}
        inventory_item_ids = cls._get_inventory_item_ids()

        if item_cooldowns:
            current_item_ids = set(inventory_item_ids)
            stale_item_ids = [item_id for item_id in item_cooldowns if item_id not in current_item_ids]
            for item_id in stale_item_ids:
                item_cooldowns.pop(item_id, None)

        for item_id in inventory_item_ids:
            if item_cooldowns.get(item_id, 0) > 0:
                continue

            action = cls._get_action_for_item(config, item_id)
            if action in (None, ItemAction.NONE, ItemAction.Ignore, ItemAction.Hold):
                continue

            if action == ItemAction.ExtractUpgrade:
                if cls._get_single_extractable_match(config, item_id, blackboard) is None:
                    continue
            
            if action == ItemAction.Stash:
                depositable_item_ids = BTNodes.Items.GetDepositableItemIds([item_id], log_plans=False)
                if item_id not in depositable_item_ids:
                    continue

            action_batches.setdefault(action, []).append(item_id)

        return action_batches

    @classmethod
    def _build_preview_entry(cls, config: InventoryConfig, item: ItemSnapshot) -> InventoryPreviewEntry:
        rule = cls._get_first_matching_rule(config, item.id)
        if rule is None:
            return InventoryPreviewEntry(item=item, action=None, rule=None, note="No matching rule.", executable=False)

        action = cls._get_rule_action(rule, item.id)
        if action in (ItemAction.NONE, ItemAction.Ignore, ItemAction.Hold):
            return InventoryPreviewEntry(
                item=item,
                action=action,
                rule=rule,
                note="No inventory action will be executed.",
                executable=False,
            )

        if not cls._is_action_dispatchable(action):
            return InventoryPreviewEntry(
                item=item,
                action=action,
                rule=rule,
                note=cls._get_blocked_action_note(action),
                executable=False,
            )

        if action == ItemAction.Stash:
            depositable_item_ids = BTNodes.Items.GetDepositableItemIds([item.id], log_plans=False)
            if item.id not in depositable_item_ids:
                return InventoryPreviewEntry(
                    item=item,
                    action=action,
                    rule=rule,
                    note="Skipped because the full item quantity does not fit in storage or material storage.",
                    executable=False,
            )

        if action == ItemAction.ExtractUpgrade:
            matches = rule.get_matching_upgrades(item.id) if isinstance(rule, ExtractUpgradeRule) else []
            if len(matches) == 1 and item.is_salvageable and item.item_type is not ItemType.Rune_Mod:
                _, salvage_mode = matches[0]
                return InventoryPreviewEntry(
                    item=item,
                    action=action,
                    rule=rule,
                    note=f"Will extract {cls._format_upgrade_match_name(salvage_mode, item.id)}.",
                )

            elif len(matches) > 1:
                match_names = ", ".join(cls._format_upgrade_match_name(salvage_mode, item.id) for _, salvage_mode in matches)
                return InventoryPreviewEntry(
                    item=item,
                    action=action,
                    rule=rule,
                    note=f"Skipped because multiple upgrades match: {match_names}.",
                    executable=False,
                )
                
            elif not item.is_salvageable or item.item_type is ItemType.Rune_Mod:
                return InventoryPreviewEntry(
                    item=item,
                    action=action,
                    rule=rule,
                    note="Skipped because the item is not salvageable or is an Upgrade.",
                    executable=False,
                )

            return InventoryPreviewEntry(
                item=item,
                action=action,
                rule=rule,
                note="Skipped because no extractable upgrade matched the rule.",
                executable=False,
            )

        if isinstance(rule, ExtractUpgradeRule) and item.item_type is ItemType.Rune_Mod:
            return InventoryPreviewEntry(
                item=item,
                action=action,
                rule=rule,
                note=f"Already extracted upgrade matched the rule. Using {action.name}.",
            )

        return InventoryPreviewEntry(item=item, action=action, rule=rule, note="")

    @staticmethod
    def _get_inventory_item_ids() -> list[int]:
        items = ItemSnapshot.get_items(INVENTORY_BAGS)
        item_ids: list[int] = []

        for item in items:
            if item is None or not item.is_valid or not item.is_inventory_item:
                continue
            
            if item.is_customized:
                continue

            item_ids.append(item.id)

        return item_ids

    @classmethod
    def _get_action_for_item(cls, config: InventoryConfig, item_id: int) -> Optional[ItemAction]:
        rule = cls._get_first_matching_rule(config, item_id)
        if rule is None:
            return None

        return cls._get_rule_action(rule, item_id)

    @staticmethod
    def _get_rule_action(rule: Rule, item_id: int) -> ItemAction:
        if isinstance(rule, ExtractUpgradeRule):
            return rule.get_effective_action(item_id)

        return rule.action

    @classmethod
    def _needs_inventory_sorting(cls) -> bool:
        snapshot = ItemSnapshot.get_bags_snapshot(INVENTORY_BAGS)
        planned_layout = BTNodes.Bags.GetPlannedBagLayout(INVENTORY_BAGS)

        for bag in INVENTORY_BAGS:
            current_bag = snapshot.get(bag, {})
            planned_bag = planned_layout.get(bag, {})

            for slot in sorted(current_bag.keys()):
                current_item = current_bag.get(slot)
                planned_item = planned_bag.get(slot)

                current_signature = (
                    current_item.id,
                    current_item.quantity,
                ) if current_item is not None and current_item.is_valid else None
                planned_signature = (
                    planned_item.id,
                    planned_item.quantity,
                ) if planned_item is not None and planned_item.is_valid else None

                if current_signature != planned_signature:
                    return True

        return False

    @staticmethod
    def _get_first_matching_rule(config: InventoryConfig, item_id: int) -> Optional[Rule]:
        if item_id in config.blacklisted_items:
            return None

        for rule in config:
            if rule.applies(item_id):
                return rule

        return None

    @classmethod
    def _build_action_node(
        cls,
        config: InventoryConfig,
        action: ItemAction,
        item_ids: list[int],
        blackboard: Optional[dict] = None,
    ) -> tuple[Optional[BehaviorTree.Node], list[int]]:
        if not cls._is_action_dispatchable(action):
            return None, []

        match action:
            case ItemAction.Identify:
                unidentified_item_ids = [item_id for item_id in item_ids if (item := ItemSnapshot.from_item_id(item_id)) is not None and not item.is_identified]
                if not unidentified_item_ids:
                    return None, []
                
                items = ItemSnapshot.get_items(INVENTORY_BAGS)
                identification_kit_model_ids = {ModelID.Superior_Identification_Kit, ModelID.Identification_Kit}
                
                if any(item is not None and item.is_valid and item.model_id in identification_kit_model_ids for item in items):
                    return BTNodes.Items.IdentifyItems(unidentified_item_ids), unidentified_item_ids
            
            case ItemAction.Use:
                return BTNodes.Items.UseItems(item_ids), item_ids
            
            case ItemAction.Drop:
                if Map.IsExplorable():
                    return BTNodes.Items.DropItems(item_ids), item_ids
            
            case ItemAction.Destroy:
                return BTNodes.Items.DestroyItems(item_ids), item_ids
            
            case ItemAction.Stash:
                if Map.IsOutpost() or Map.IsGuildHall():
                    instructions = BTNodes.Items.GetTransferInstructions(
                        item_ids,
                        STORAGE_BAGS,
                        fill_materials_first=True,
                    )
                    depositable_item_ids = BTNodes.Items._get_planned_transfer_item_ids(instructions) if instructions else []
                    if depositable_item_ids:
                        return BTNodes.Items.DepositItems(
                            depositable_item_ids,
                            target=STORAGE_BAGS,
                            fill_materials_first=True,
                            precomputed_instructions=instructions,
                        ), depositable_item_ids
            
            case ItemAction.Sell_To_Merchant:
                if UIManagerExtensions.MerchantWindow.IsOpen():
                    return BTNodes.Merchant.SellItems(item_ids), item_ids
                
            case ItemAction.Sell_To_Trader:
                if UIManagerExtensions.MerchantWindow.IsOpen():
                    item_id = cls._get_first_valid_item_id(item_ids)
                    if item_id is not None:
                        return BTNodes.Trader.SellItem(item_id), [item_id]
            
            case ItemAction.Salvage_Common_Materials:
                items = ItemSnapshot.get_items(INVENTORY_BAGS)
                salvage_kit_model_ids = {ModelID.Salvage_Kit, ModelID.Salvage_Kit_preSearing}
                
                if any(item is not None and item.is_valid and item.model_id in salvage_kit_model_ids for item in items):
                    item_id = cls._get_first_salvageable_item_id(item_ids)
                    if item_id is not None:
                        return BTNodes.Items.SalvageItem(
                            item_id,
                            salvage_mode=SalvageMode.LesserCraftingMaterials,
                            allow_expert_for_common_materials=True,
                            state_key=f"inventory_bt_salvage_common_{item_id}",
                            debug_enabled=True,
                        ), [item_id]
                    
            case ItemAction.Salvage_Rare_Materials: 
                items = ItemSnapshot.get_items(INVENTORY_BAGS)
                salvage_kit_model_ids = {ModelID.Expert_Salvage_Kit, ModelID.Superior_Salvage_Kit}
                
                if any(item is not None and item.is_valid and item.model_id in salvage_kit_model_ids for item in items):
                    item_id = cls._get_first_salvageable_item_id(item_ids)
                    if item_id is not None:
                        return BTNodes.Items.SalvageItem(
                            item_id,
                            salvage_mode=SalvageMode.RareCraftingMaterials,
                            state_key=f"inventory_bt_salvage_rare_{item_id}",
                            debug_enabled=True,
                        ), [item_id]
                
            case ItemAction.ExtractUpgrade:
                items = ItemSnapshot.get_items(INVENTORY_BAGS)
                salvage_kit_model_ids = {ModelID.Expert_Salvage_Kit, ModelID.Superior_Salvage_Kit}
                
                if any(item is not None and item.is_valid and item.model_id in salvage_kit_model_ids for item in items):
                    item_id, salvage_mode = cls._get_first_extractable_item(config, item_ids, blackboard)
                    if item_id is not None and salvage_mode is not None:
                        return BTNodes.Items.SalvageItem(
                            item_id,
                            salvage_mode=salvage_mode,
                            state_key=f"inventory_bt_extract_{item_id}",
                            debug_enabled=True,
                        ), [item_id]
            
            case _:
                return None, []

        return None, []

    @staticmethod
    def _is_action_dispatchable(action: ItemAction) -> bool:
        match action:
            case ItemAction.Drop:
                return Map.IsExplorable()
            case ItemAction.Stash:
                return Map.IsOutpost() or Map.IsGuildHall()
            case ItemAction.Sell_To_Merchant | ItemAction.Sell_To_Trader:
                return UIManagerExtensions.MerchantWindow.IsOpen()
            case _:
                return True

    @staticmethod
    def _get_blocked_action_note(action: ItemAction) -> str:
        match action:
            case ItemAction.Drop:
                return "Waiting until the item can be processed in an explorable area."
            case ItemAction.Stash:
                return "Waiting until storage is available in an outpost or guild hall."
            case ItemAction.Sell_To_Merchant:
                return "Waiting until a merchant window is open."
            case ItemAction.Sell_To_Trader:
                return "Waiting until a trader window is open."
            case _:
                return "Waiting until the action can be dispatched."

    @staticmethod
    def _get_first_valid_item_id(item_ids: list[int]) -> Optional[int]:
        for item_id in item_ids:
            item = ItemSnapshot.from_item_id(item_id)
            if item is not None and item.is_valid and item.is_inventory_item:
                return item_id

        return None

    @staticmethod
    def _get_first_salvageable_item_id(item_ids: list[int]) -> Optional[int]:
        for item_id in item_ids:
            item = ItemSnapshot.from_item_id(item_id)
            if item is not None and item.is_valid and item.is_inventory_item and item.is_salvageable:
                return item_id

        return None

    @classmethod
    def _get_first_extractable_item(
        cls,
        config: InventoryConfig,
        item_ids: list[int],
        blackboard: Optional[dict] = None,
    ) -> tuple[Optional[int], Optional[SalvageMode]]:
        for item_id in item_ids:
            item = ItemSnapshot.from_item_id(item_id)
            if item is None or not item.is_valid or not item.is_inventory_item or not item.is_salvageable:
                continue

            match = cls._get_single_extractable_match(config, item_id, blackboard)
            if match is not None:
                _, salvage_mode = match
                return item_id, salvage_mode

        return None, None

    @staticmethod
    def _format_upgrade_match_name(salvage_mode: SalvageMode, item_id: int) -> str:
        item = ItemSnapshot.from_item_id(item_id)
        if item is None:
            return salvage_mode.name

        if salvage_mode == SalvageMode.Prefix and item.prefix is not None:
            return f"{salvage_mode.name}: {type(item.prefix).__name__}"

        if salvage_mode == SalvageMode.Suffix and item.suffix is not None:
            return f"{salvage_mode.name}: {type(item.suffix).__name__}"

        if salvage_mode == SalvageMode.Inscription and item.inscription is not None:
            return f"{salvage_mode.name}: {type(item.inscription).__name__}"

        return salvage_mode.name

    @classmethod
    def _get_single_extractable_match(
        cls,
        config: InventoryConfig,
        item_id: int,
        blackboard: Optional[dict] = None,
    ) -> Optional[tuple[object, SalvageMode]]:
        rule = cls._get_first_matching_rule(config, item_id)
        if not isinstance(rule, ExtractUpgradeRule):
            return None

        matches = rule.get_matching_upgrades(item_id)
        if len(matches) == 1:
            return matches[0]

        if len(matches) > 1:
            cls._log_ambiguous_extract_upgrade(item_id, rule, matches, blackboard)

        return None

    @classmethod
    def _log_ambiguous_extract_upgrade(
        cls,
        item_id: int,
        rule: ExtractUpgradeRule,
        matches: Sequence[tuple[object, SalvageMode]],
        blackboard: Optional[dict],
    ) -> None:
        if blackboard is not None:
            warning_cache = cast(set[int], blackboard.setdefault(cls._EXTRACT_WARNING_CACHE_KEY, set()))
            if item_id in warning_cache:
                return
            warning_cache.add(item_id)

        item = ItemSnapshot.from_item_id(item_id)
        item_name = item.names.plain if item is not None and item.names.plain else f"Item {item_id}"
        match_names = ", ".join(cls._format_upgrade_match_name(salvage_mode, item_id) for _, salvage_mode in matches)

        Py4GW.Console.Log(
            "InventoryBT",
            f"Skipping upgrade extraction for '{item_name}' (ID: {item_id}) because rule '{rule.name or type(rule).__name__}' matched multiple upgrades: {match_names}.",
            Py4GW.Console.MessageType.Warning,
        )

    @classmethod
    def _advance_item_cooldowns(cls, blackboard: dict) -> None:
        item_cooldowns = cast(dict[int, int], blackboard.setdefault(cls._ITEM_COOLDOWNS_KEY, {}))
        expired_item_ids: list[int] = []

        for item_id, remaining_ticks in item_cooldowns.items():
            next_ticks = remaining_ticks - 1
            if next_ticks <= 0:
                expired_item_ids.append(item_id)
            else:
                item_cooldowns[item_id] = next_ticks

        for item_id in expired_item_ids:
            item_cooldowns.pop(item_id, None)

    @classmethod
    def _set_item_cooldown(cls, blackboard: dict, item_ids: Sequence[int], ticks: int) -> None:
        if ticks <= 0:
            return

        item_cooldowns = cast(dict[int, int], blackboard.setdefault(cls._ITEM_COOLDOWNS_KEY, {}))
        for item_id in item_ids:
            item_cooldowns[item_id] = max(ticks, item_cooldowns.get(item_id, 0))


__all__ = ["InventoryBT", "InventoryPreviewEntry"]
