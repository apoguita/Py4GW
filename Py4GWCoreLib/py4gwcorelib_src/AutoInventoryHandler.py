#region AutoInventory
from typing import Optional, Callable

from .Console import ConsoleLog, Console
from .Timer import ThrottledTimer
from .ActionQueue import ActionQueueManager
from .Lootconfig_src import LootConfig

class AutoInventoryHandler():
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AutoInventoryHandler, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._LOOKUP_TIME:int = 15000
        self.lookup_throttle = ThrottledTimer(self._LOOKUP_TIME)

        self.runtime_initialized = False
        self.status = "Idle"
        self.outpost_handled = False
        self.module_active:bool = False
        self.module_name:str = "AutoInventoryHandler"
        self.debug_item_selection: bool = False
        
        self.id_whites:bool = False
        self.id_blues:bool = False
        self.id_purples:bool = False
        self.id_golds:bool = False
        self.id_greens:bool = False
        self.id_model_blacklist:list[int] = []  # Items that should not be identified, even if they match the ID criteria
        
        self.salvage_whites:bool = False
        self.salvage_rare_materials:bool = False
        self.salvage_blues:bool = False
        self.salvage_purples:bool = False
        self.salvage_golds:bool = False
        self.salvage_dialog_auto_handle:bool = False
        self.salvage_dialog_auto_confirm_materials:bool = False
        self.salvage_dialog_debug:bool = False
        self.salvage_dialog_strategy:int = 0
        self.salvage_dialog_fallback_index:int = 1
        self.item_type_blacklist:list[int] = [] # Item types that should not be salvaged, even if they match the salvage criteria
        self.salvage_blacklist:list[int] = []  # Items that should not be salvaged, even if they match the salvage criteria
        self.blacklisted_model_id:int = 0
        self.model_id_search:str = ""
        self.item_type_search:str = ""
        self.model_id_search_mode:int = 0  # 0 = Contains, 1 = Starts With
        self.item_type_search_mode:int = 0  # 0 = Contains, 1 = Starts With
        self.show_dialog_popup:bool = False 
        self.show_item_type_dialog:bool = False
        
        self.deposit_trophies:bool = False
        self.deposit_materials:bool = False
        self.deposit_blues:bool = False
        self.deposit_purples:bool = False
        self.deposit_golds:bool = False
        self.deposit_greens:bool = False
        self.deposit_event_items:bool = False
        self.deposit_dyes:bool = False
        self.keep_gold:int = 5000
        self.deposit_trophies_blacklist:list[int] = []  # Model IDs of trophies that should not be deposited
        self.deposit_materials_blacklist:list[int] = []  # Model IDs of materials that should not be deposited
        self.deposit_event_items_blacklist:list[int] = []  # Model IDs of event items that should not
        self.deposit_dyes_blacklist:list[int] = []  # Model IDs of dyes that should not be deposited
        self.deposit_model_blacklist:list[int] = []  # Model IDs of items that should not be deposited
        self.last_salvage_failed_item_ids: set[int] = set()

        self._initialized = True

    @property
    def initialized(self):
        # Backward-compatible alias for older callers.
        return self.runtime_initialized

    @initialized.setter
    def initialized(self, value):
        # Backward-compatible alias for older callers.
        self.runtime_initialized = value

    def _normalize_rarity_names(self, rarities=None):
        from ..enums_src.Item_enums import Rarity

        normalized: set[Rarity] = set()
        if rarities is None:
            return normalized

        for rarity in rarities:
            if isinstance(rarity, Rarity):
                normalized.add(rarity)
            elif isinstance(rarity, str) and rarity in Rarity.__members__:
                normalized.add(Rarity[rarity])

        return normalized

    def _debug_log(self, stage: str, message: str, msg_type=None, log_enabled: bool = True):
        if not self.debug_item_selection:
            return
        
        if not log_enabled:
            return
        
        Console.Log(
            f"{self.module_name}:{stage}",
            message,
            msg_type or Console.MessageType.Info,
        )

    def _item_debug_name(self, item) -> str:
        if item is None:
            return "Unknown Item"
        try:
            names = getattr(item, "names", None)
            plain = getattr(names, "plain", "") if names is not None else ""
            if plain:
                return plain
        except Exception:
            pass
        return f"item_id={getattr(item, 'id', 0)}"

    def _item_debug_summary(self, item) -> str:
        if item is None:
            return "item=<none>"
        rarity = getattr(getattr(item, "rarity", None), "name", "Unknown")
        item_type = getattr(getattr(item, "item_type", None), "name", "Unknown")
        return (
            f"{self._item_debug_name(item)} "
            f"[id={item.id}, model={item.model_id}, rarity={rarity}, type={item_type}, "
            f"qty={item.quantity}, identified={item.is_identified}, salvageable={item.is_salvageable}, "
            f"material={item.is_material}, rare_material={item.is_rare_material}, customized={item.is_customized}]"
        )

    def _get_inventory_items(self):
        from Py4GWCoreLib.item_data.item_snapshot import ItemSnapshot
        from Py4GWCoreLib.enums_src.Item_enums import INVENTORY_BAGS

        snapshot = ItemSnapshot.get_bags_snapshot(INVENTORY_BAGS)
        return [
            item
            for bag in INVENTORY_BAGS
            for item in snapshot.get(bag, {}).values()
            if item is not None and item.is_valid and item.is_inventory_item
        ]

    def _tick_bt_node(self, node, poll_ms: int = 50):
        from ..Routines import Routines
        from .BehaviorTree import BehaviorTree

        while True:
            state = node.tick()
            if state == BehaviorTree.NodeState.RUNNING:
                yield from Routines.Yield.wait(max(1, poll_ms))
                continue
            return state

    def _get_identify_item_ids(self, rarities=None):
        from ..enums_src.Item_enums import Rarity

        rarity_filter = self._normalize_rarity_names(rarities)
        if not rarity_filter:
            if self.id_whites:
                rarity_filter.add(Rarity.White)
            if self.id_blues:
                rarity_filter.add(Rarity.Blue)
            if self.id_greens:
                rarity_filter.add(Rarity.Green)
            if self.id_purples:
                rarity_filter.add(Rarity.Purple)
            if self.id_golds:
                rarity_filter.add(Rarity.Gold)

        selected_item_ids: list[int] = []
        self._debug_log(
            "Identify",
            f"Start evaluation rarity_filter={[rarity.name for rarity in sorted(rarity_filter, key=lambda r: r.value)]} "
            f"flags=white:{self.id_whites},blue:{self.id_blues},green:{self.id_greens},purple:{self.id_purples},gold:{self.id_golds} "
            f"blacklist_count={len(self.id_model_blacklist)}",
        )
        for item in self._get_inventory_items():
            summary = self._item_debug_summary(item)
            if item.is_identified:
                self._debug_log("Identify", f"Skip {summary} reason=already_identified")
                continue
            if item.model_id in self.id_model_blacklist:
                self._debug_log("Identify", f"Skip {summary} reason=model_blacklisted")
                continue
            if rarity_filter and item.rarity not in rarity_filter:
                self._debug_log("Identify", f"Skip {summary} reason=rarity_not_selected")
                continue
            self._debug_log("Identify", f"Select {summary} action=identify")
            selected_item_ids.append(item.id)
        return selected_item_ids

    def _normalize_salvage_strategy(self) -> int:
        strategy = int(self.salvage_dialog_strategy)
        if strategy == 2:
            return 1
        if strategy not in (0, 1):
            return 0
        return strategy

    def _get_salvage_kit_capabilities(self):
        from Py4GWCoreLib.enums_src.Model_enums import ModelID

        capabilities = {
            "lesser": False,
            "expert": False,
            "upgrade": False,
        }

        for item in self._get_inventory_items():
            if not item.is_salvage_kit or item.uses <= 0:
                continue
            if item.model_id == ModelID.Salvage_Kit:
                capabilities["lesser"] = True
            elif item.model_id in (ModelID.Expert_Salvage_Kit, ModelID.Superior_Salvage_Kit):
                capabilities["expert"] = True
                capabilities["upgrade"] = True
            elif item.model_id == ModelID.Perfect_Salvage_Kit:
                capabilities["upgrade"] = True

        return capabilities

    def _get_salvage_modes_for_item(self, item, strategy: Optional[int] = None, allow_unidentified_nonwhite: bool = False, respect_settings: bool = True):
        from ..Item import Item
        from ..enums_src.Item_enums import Rarity
        from Py4GWCoreLib.enums_src.Item_enums import SalvageMode

        if item is None or not item.is_valid or not item.is_inventory_item:
            return []
        if item.is_customized or not item.is_salvageable or item.model_id in self.salvage_blacklist:
            return []
        if item.item_type in self.item_type_blacklist:
            return []
        if item.rarity == Rarity.Green:
            return []
        if item.rarity != Rarity.White and not item.is_identified and not allow_unidentified_nonwhite:
            return []

        kit_caps = self._get_salvage_kit_capabilities()
        material_modes: list[SalvageMode] = []
        if item.rarity == Rarity.White:
            if item.is_material and item.is_material_salvageable:
                if respect_settings and not self.salvage_rare_materials:
                    return []
                if kit_caps["expert"]:
                    material_modes.append(SalvageMode.RareCraftingMaterials)
            else:
                if respect_settings and not self.salvage_whites:
                    return []
                if kit_caps["lesser"]:
                    material_modes.append(SalvageMode.LesserCraftingMaterials)
                elif kit_caps["expert"]:
                    material_modes.append(SalvageMode.RareCraftingMaterials)
        elif item.rarity == Rarity.Blue:
            if respect_settings and not self.salvage_blues:
                return []
            if kit_caps["lesser"]:
                material_modes.append(SalvageMode.LesserCraftingMaterials)
            elif kit_caps["expert"]:
                material_modes.append(SalvageMode.RareCraftingMaterials)
        elif item.rarity == Rarity.Purple:
            if respect_settings and not self.salvage_purples:
                return []
            if kit_caps["lesser"]:
                material_modes.append(SalvageMode.LesserCraftingMaterials)
            elif kit_caps["expert"]:
                material_modes.append(SalvageMode.RareCraftingMaterials)
        elif item.rarity == Rarity.Gold:
            if respect_settings and not self.salvage_golds:
                return []
            if kit_caps["lesser"]:
                material_modes.append(SalvageMode.LesserCraftingMaterials)
            elif kit_caps["expert"]:
                material_modes.append(SalvageMode.RareCraftingMaterials)
        else:
            return []

        prefix, suffix, inscription, _ = Item.Customization.GetUpgrades(item.id)
        upgrade_modes: list[SalvageMode] = []
        if kit_caps["upgrade"] and inscription is not None:
            upgrade_modes.append(SalvageMode.Inscription)
        if kit_caps["upgrade"] and suffix is not None:
            upgrade_modes.append(SalvageMode.Suffix)
        if kit_caps["upgrade"] and prefix is not None:
            upgrade_modes.append(SalvageMode.Prefix)

        ordered_modes = material_modes + upgrade_modes if (strategy if strategy is not None else self._normalize_salvage_strategy()) == 0 else upgrade_modes + material_modes

        deduped_modes: list[SalvageMode] = []
        for mode in ordered_modes:
            if mode not in deduped_modes:
                deduped_modes.append(mode)
        return deduped_modes

    def _get_salvage_skip_reason(self, item, rarity_filter, allow_unidentified_nonwhite: bool = False, respect_settings: bool = True):
        from ..enums_src.Item_enums import Rarity

        if item is None or not item.is_valid or not item.is_inventory_item:
            return "invalid_or_not_inventory"
        if rarity_filter and item.rarity not in rarity_filter:
            return "rarity_not_selected"
        if item.is_customized:
            return "customized"
        if not item.is_salvageable:
            return "not_salvageable"
        if item.model_id in self.salvage_blacklist:
            return "model_blacklisted"
        if item.item_type in self.item_type_blacklist:
            return "item_type_blacklisted"
        if item.rarity.name == "Green":
            return "green_items_not_salvaged"
        if item.rarity.name != "White" and not item.is_identified and not allow_unidentified_nonwhite:
            return "nonwhite_not_identified"
        if not respect_settings:
            return None
        if item.rarity == Rarity.White:
            if item.is_material and item.is_material_salvageable and not self.salvage_rare_materials:
                return "white_material_requires_salvage_rare_materials"
            if not item.is_material and not self.salvage_whites:
                return "salvage_whites_disabled"
        elif item.rarity == Rarity.Blue and not self.salvage_blues:
            return "salvage_blues_disabled"
        elif item.rarity == Rarity.Purple and not self.salvage_purples:
            return "salvage_purples_disabled"
        elif item.rarity == Rarity.Gold and not self.salvage_golds:
            return "salvage_golds_disabled"
        return None

    def _should_keep_salvage_item(self, item, rarity_filter):
        return bool(item and item.is_valid and item.is_inventory_item and (not rarity_filter or item.rarity in rarity_filter))

    def IdentifyItems(self, progress_callback: Optional[Callable[[float], None]] = None, log: bool = False, item_ids=None, rarities=None):
        from .BehaviorTree import BehaviorTree
        from Sources.frenkeyLib.ItemHandling.BTNodes import BTNodes

        target_item_ids = list(dict.fromkeys(item_ids if item_ids is not None else self._get_identify_item_ids(rarities)))
        identified_items = 0
        total_items = len(target_item_ids)

        for index, item_id in enumerate(target_item_ids, start=1):
            node = BTNodes.Items.IdentifyItems([item_id], fail_if_no_kit=True, succeed_if_already_identified=True)
            state = yield from self._tick_bt_node(node)
            if state == BehaviorTree.NodeState.SUCCESS:
                identified_items += 1
            elif state == BehaviorTree.NodeState.FAILURE:
                Console.Log("AutoIdentify", f"Identify failed for item_id={item_id}.", Console.MessageType.Warning)
                break

            if progress_callback and total_items > 0:
                progress_callback(index / total_items)

        if identified_items > 0 and log:
            ConsoleLog(self.module_name, f"Identified {identified_items} items", Console.MessageType.Success)

    def SalvageItems(self, progress_callback: Optional[Callable[[float], None]] = None, log: bool = False, item_ids=None, rarities=None, preferred_kit_id: Optional[int] = None, allow_unidentified_nonwhite: bool = False, respect_settings: bool = True, timeout_ms_per_item: int = 5000):
        from .BehaviorTree import BehaviorTree
        from Sources.frenkeyLib.ItemHandling.BTNodes import BTNodes

        rarity_filter = self._normalize_rarity_names(rarities)
        strategy = self._normalize_salvage_strategy()
        target_item_ids = list(dict.fromkeys(item_ids if item_ids is not None else [item.id for item in self._get_inventory_items()]))

        salvaged_items = 0
        total_items = len(target_item_ids)
        failed_item_ids: set[int] = set()
        self._debug_log(
            "Salvage",
            f"Start evaluation target_count={total_items} "
            f"rarity_filter={[rarity.name for rarity in sorted(rarity_filter, key=lambda r: r.value)]} "
            f"strategy={strategy} preferred_kit_id={preferred_kit_id or 0} "
            f"allow_unidentified_nonwhite={allow_unidentified_nonwhite} respect_settings={respect_settings} "
            f"timeout_ms_per_item={timeout_ms_per_item} "
            f"kit_caps={self._get_salvage_kit_capabilities()} "
            f"flags=white:{self.salvage_whites},rare_materials:{self.salvage_rare_materials},blue:{self.salvage_blues},purple:{self.salvage_purples},gold:{self.salvage_golds} "
            f"model_blacklist_count={len(self.salvage_blacklist)} type_blacklist_count={len(self.item_type_blacklist)}",
        )

        for index, item_id in enumerate(target_item_ids, start=1):
            item = next((candidate for candidate in self._get_inventory_items() if candidate.id == item_id), None)
            skip_reason = self._get_salvage_skip_reason(
                item,
                rarity_filter,
                allow_unidentified_nonwhite=allow_unidentified_nonwhite,
                respect_settings=respect_settings,
            )
            if skip_reason is not None:
                self._debug_log("Salvage", f"Skip {self._item_debug_summary(item)} reason={skip_reason}")
                continue

            modes = self._get_salvage_modes_for_item(
                item,
                strategy=strategy,
                allow_unidentified_nonwhite=allow_unidentified_nonwhite,
                respect_settings=respect_settings,
            )
            if not modes:
                self._debug_log("Salvage", f"Skip {self._item_debug_summary(item)} reason=no_salvage_modes_resolved")
                continue

            self._debug_log("Salvage", f"Select {self._item_debug_summary(item)} action=salvage modes={[mode.name for mode in modes]}")
            salvaged = False
            for mode in modes:
                if item is None:
                    Console.Log("AutoSalvage", f"Item with id={item_id} not found in inventory during salvage. Skipping.", Console.MessageType.Warning)
                    break
                node = BTNodes.Items.SalvageItem(
                    item.id,
                    salvage_mode=mode,
                    preferred_kit_id=preferred_kit_id,
                    timeout_ms_per_item=timeout_ms_per_item,
                    debug_enabled=self.debug_item_selection,
                )
                self._debug_log("Salvage", f"Run {self._item_debug_summary(item)} mode={mode.name}")
                state = yield from self._tick_bt_node(node)
                if state == BehaviorTree.NodeState.SUCCESS:
                    self._debug_log("Salvage", f"Result {self._item_debug_summary(item)} mode={mode.name} state=SUCCESS")
                    salvaged_items += 1
                    salvaged = True
                    failed_item_ids.discard(item.id)
                    break
                self._debug_log("Salvage", f"Result {self._item_debug_summary(item)} mode={mode.name} state={state.name}")

            if not salvaged:
                if item is not None:
                    failed_item_ids.add(item.id)
                self._debug_log("Salvage", f"Skip {self._item_debug_summary(item)} reason=all_modes_failed", Console.MessageType.Warning)
                Console.Log("AutoSalvage", f"No salvage mode succeeded for item_id={item_id}.", Console.MessageType.Warning)

            if progress_callback and total_items > 0:
                progress_callback(index / total_items)

        if salvaged_items > 0 and log:
            ConsoleLog(self.module_name, f"Salvaged {salvaged_items} items", Console.MessageType.Success)
        self.last_salvage_failed_item_ids = failed_item_ids

             
             
    def DepositItemsAuto(self):
        from ..enums import Bags, ModelID
        from ..GlobalCache import GLOBAL_CACHE
        from ..Routines import Routines

        event_items = set()
        selected_filters = {
            "Alcohol": None,          # include ALL subcategories
            "Sweets": None,           # include ALL subcategories
            "Party": None,            # include ALL subcategories
            "Death Penalty Removal": None,  # include ALL subcategories
            "Reward Trophies": {"Special Events"},
        }

        # Build once per deposit run instead of once per item.
        for category, subcats in LootConfig().LootGroups.items():
            if category not in selected_filters:
                continue

            allowed_subcats = selected_filters[category]
            for subcat, items in subcats.items():
                if allowed_subcats is not None and subcat not in allowed_subcats:
                    continue
                event_items.update(m.value for m in items)

        self._debug_log(
            "Deposit",
            f"Start evaluation flags=trophies:{self.deposit_trophies},materials:{self.deposit_materials},blues:{self.deposit_blues},purples:{self.deposit_purples},golds:{self.deposit_golds},greens:{self.deposit_greens},event_items:{self.deposit_event_items},dyes:{self.deposit_dyes} "
            f"keep_gold={self.keep_gold} model_blacklist_count={len(self.deposit_model_blacklist)}",
        )

        for bag_id in range(Bags.Backpack, Bags.Bag2+1):
            bag_to_check = GLOBAL_CACHE.ItemArray.CreateBagList(bag_id)
            item_array = GLOBAL_CACHE.ItemArray.GetItemArray(bag_to_check)
            
            for item_id in item_array:
                item = next((candidate for candidate in self._get_inventory_items() if candidate.id == item_id), None)
                # Check if the item is a trophy or material
                is_trophy = GLOBAL_CACHE.Item.Type.IsTrophy(item_id)
                is_tome = GLOBAL_CACHE.Item.Type.IsTome(item_id)
                _, item_type = GLOBAL_CACHE.Item.GetItemType(item_id)
                is_usable = (item_type == "Usable")
                
                is_material = GLOBAL_CACHE.Item.Type.IsMaterial(item_id)
                _, rarity = GLOBAL_CACHE.Item.Rarity.GetRarity(item_id)
                is_white =  rarity == "White"
                is_blue = rarity == "Blue"
                is_green = rarity == "Green"
                is_purple = rarity == "Purple"
                is_gold = rarity == "Gold"
                
                model_id = GLOBAL_CACHE.Item.GetModelID(item_id)
                
                is_dye = model_id == ModelID.Vial_Of_Dye.value

                if item_id in self.last_salvage_failed_item_ids:
                    self._debug_log("Deposit", f"Skip {self._item_debug_summary(item)} reason=salvage_failed_this_run")
                    continue
                
                if model_id in self.deposit_model_blacklist:
                    self._debug_log("Deposit", f"Skip {self._item_debug_summary(item)} reason=model_blacklisted")
                    continue
                
                if is_material and model_id in self.deposit_materials_blacklist:
                    self._debug_log("Deposit", f"Skip {self._item_debug_summary(item)} reason=material_blacklisted")
                    continue
                
                if is_trophy and model_id in self.deposit_trophies_blacklist:
                    self._debug_log("Deposit", f"Skip {self._item_debug_summary(item)} reason=trophy_blacklisted")
                    continue
                
                is_dye = (model_id == ModelID.Vial_Of_Dye.value)
                dye1_to_match = None
                if is_dye:
                    dye_info = GLOBAL_CACHE.Item.Customization.GetDyeInfo(item_id)
                    dye1_to_match = dye_info.dye1.ToInt()
                    
                if is_dye and dye1_to_match in self.deposit_dyes_blacklist:
                    self._debug_log("Deposit", f"Skip {self._item_debug_summary(item)} reason=dye_blacklisted")
                    continue

                deposited = False
                if is_tome:
                    self._debug_log("Deposit", f"Select {self._item_debug_summary(item)} action=deposit reason=tome")
                    GLOBAL_CACHE.Inventory.DepositItemToStorage(item_id)
                    yield from Routines.Yield.wait(350)
                    deposited = True
                 
                if not deposited and is_trophy and self.deposit_trophies and is_white:
                    self._debug_log("Deposit", f"Select {self._item_debug_summary(item)} action=deposit reason=white_trophy")
                    GLOBAL_CACHE.Inventory.DepositItemToStorage(item_id)
                    yield from Routines.Yield.wait(350)
                    deposited = True
                 
                if not deposited and is_material and self.deposit_materials:
                    self._debug_log("Deposit", f"Select {self._item_debug_summary(item)} action=deposit reason=material")
                    GLOBAL_CACHE.Inventory.DepositItemToStorage(item_id)
                    yield from Routines.Yield.wait(350)
                    deposited = True
                 
                if not deposited and is_blue and self.deposit_blues:
                    self._debug_log("Deposit", f"Select {self._item_debug_summary(item)} action=deposit reason=blue")
                    GLOBAL_CACHE.Inventory.DepositItemToStorage(item_id)
                    yield from Routines.Yield.wait(350)
                    deposited = True
                 
                if not deposited and is_purple and self.deposit_purples:
                    self._debug_log("Deposit", f"Select {self._item_debug_summary(item)} action=deposit reason=purple")
                    GLOBAL_CACHE.Inventory.DepositItemToStorage(item_id)
                    yield from Routines.Yield.wait(350)
                    deposited = True
                 
                if not deposited and is_gold and self.deposit_golds and not is_usable and not is_trophy:
                    self._debug_log("Deposit", f"Select {self._item_debug_summary(item)} action=deposit reason=gold_nonusable_nontrophy")
                    GLOBAL_CACHE.Inventory.DepositItemToStorage(item_id)
                    yield from Routines.Yield.wait(350)
                    deposited = True
                 
                if not deposited and is_green and self.deposit_greens:
                    self._debug_log("Deposit", f"Select {self._item_debug_summary(item)} action=deposit reason=green")
                    GLOBAL_CACHE.Inventory.DepositItemToStorage(item_id)
                    yield from Routines.Yield.wait(350)
                    deposited = True
                     
                if not deposited and model_id == ModelID.Vial_Of_Dye.value and self.deposit_dyes:
                    self._debug_log("Deposit", f"Select {self._item_debug_summary(item)} action=deposit reason=dye")
                    GLOBAL_CACHE.Inventory.DepositItemToStorage(item_id)
                    yield from Routines.Yield.wait(350)
                    deposited = True
                         
                if ((not deposited) and
                    (model_id in event_items) and 
                    self.deposit_event_items and
                    model_id not in self.deposit_event_items_blacklist):
                    self._debug_log("Deposit", f"Select {self._item_debug_summary(item)} action=deposit reason=event_item")
                    GLOBAL_CACHE.Inventory.DepositItemToStorage(item_id)
                    yield from Routines.Yield.wait(350)
                    deposited = True

                if not deposited:
                    self._debug_log("Deposit", f"Skip {self._item_debug_summary(item)} reason=no_deposit_rule_matched")
            
            
    def IDAndSalvageItems(self, progress_callback: Optional[Callable[[float], None]] = None):
        self.status = "Identifying"
        yield from self.IdentifyItems()
        if progress_callback:
            progress_callback(0.5)
        self.status = "Salvaging"
        yield from self.SalvageItems()
        self.status = "Idle"
        yield
        
    def IDSalvageDepositItems(self):
        from ..Routines import Routines

        #ConsoleLog("AutoInventoryHandler", "Starting ID, Salvage and Deposit routine", Console.MessageType.Info)
        self.status = "Identifying"
        yield from self.IdentifyItems()
        
        self.status = "Salvaging"
        yield from self.SalvageItems()
        
        self.status = "Depositing"
        yield from self.DepositItemsAuto()
        
        self.status = "Depositing Gold"
        
        yield from Routines.Yield.Items.DepositGold(self.keep_gold, log =False)
        
        self.status = "Idle"
        #ConsoleLog("AutoInventoryHandler", "ID, Salvage and Deposit routine completed", Console.MessageType.Success)


#endregion
