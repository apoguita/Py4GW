import Py4GW
import PyInventory
from typing import TypedDict, cast

from .Item import Item
from .ItemArray import ItemArray


class VisibleFrameEntry(TypedDict):
    frame_id: int
    parent_id: int
    offset: int
    left: float
    top: float
    width: float
    height: float
    area: float
    template_type: int
    text: str


class SalvageChoiceEntry(VisibleFrameEntry, total=False):
    subtree_depth: int
    source_depth: int
    path: str
    path_root_frame_ids: list[int]
    group_frame_ids: list[int]
    group_size: int
    order: int


class SalvageChoiceOptionSource(TypedDict):
    offset: int
    path_offsets: list[int]
    fallback_frame_id: int
    source_depth: int
    container_frame_id: int | None


class Inventory:
    SALVAGE_CHOICE_DIALOG_LABEL = "Salvage Window"
    SALVAGE_CHOICE_OPTION_CONTAINER_LABEL = "Salvage Window.Options"
    SALVAGE_CHOICE_CONFIRM_LABEL = "Salvage Window.Salvage Button"
    SALVAGE_CHOICE_MATERIAL_CONFIRM_YES_LABEL = "Salvage Materials Dialog.Yes Button"
    SALVAGE_CHOICE_FALLBACK_DIALOG_HASH = 684387150
    SALVAGE_CHOICE_FALLBACK_OPTION_CONTAINER_OFFSET = 5
    SALVAGE_CHOICE_FALLBACK_CONFIRM_OFFSET = 2
    SALVAGE_CHOICE_FALLBACK_MATERIAL_CONFIRM_ROOT_OFFSET = 0
    SALVAGE_CHOICE_FALLBACK_MATERIAL_CONFIRM_YES_OFFSET = 6

    @staticmethod
    def inventory_instance():
        return PyInventory.PyInventory()

    @staticmethod
    def GetInventorySpace():
        """
        Purpose: Calculate and return the total number of items and the combined capacity of bags 1, 2, 3, and 4.
        Args: None
        Returns: tuple: (total_items, total_capacity)
            - total_items: The sum of items in the four bags.
            - total_capacity: The combined capacity (size) of the four bags.
        """
        bags_to_check = ItemArray.CreateBagList(1,2,3,4)
        item_array = ItemArray.GetItemArray(bags_to_check)
        total_items = len(item_array)
        total_capacity = sum(PyInventory.Bag(bag_enum.value, bag_enum.name).GetSize() for bag_enum in bags_to_check)

        return total_items, total_capacity

    @staticmethod
    def GetStorageSpace(Anniversary_panel = True, ExtraStoragePanes = 0):
        from .enums import Bags
        """
        Purpose: Calculate and return the total number of items and the combined capacity of bags 8, 9, 10, and 11 (storage bags).
        Args: None
        Returns:
            tuple: (total_items, total_capacity)
                - total_items: The sum of items in the storage bags.
                - total_capacity: The combined capacity (size) of the storage bags.
        """
        # Define the storage bags to check
        if not Anniversary_panel:
            bags_to_check = ItemArray.CreateBagList(Bags.Storage1, Bags.Storage2, Bags.Storage3, Bags.Storage4)
        else:
            bags_to_check = ItemArray.CreateBagList(Bags.Storage1, Bags.Storage2, Bags.Storage3, Bags.Storage4,Bags.Storage5)
    
        # Retrieve the item array for the storage bags
        item_array = ItemArray.GetItemArray(bags_to_check)
    
        # Count the number of items
        total_items = len(item_array)
    
        # Dynamically calculate the total capacity using PyInventory.Bag
        total_capacity = sum(
            PyInventory.Bag(bag_enum.value, bag_enum.name).GetSize() for bag_enum in bags_to_check
        )
    
        return total_items, total_capacity
    
    @staticmethod
    def GetZeroFilledStorageArray(Anniversary_panel = True, ExtraStoragePanes = 0):
        """
        Returns a flat list of item_ids ordered by bag and slot.
        Empty slots are represented as 0.
        """
        from .enums import Bags
        result = []
        
        if not Anniversary_panel:
            bags_to_check = ItemArray.CreateBagList(Bags.Storage1, Bags.Storage2, Bags.Storage3, Bags.Storage4)
        else:
            bags_to_check = ItemArray.CreateBagList(Bags.Storage1, Bags.Storage2, Bags.Storage3, Bags.Storage4,Bags.Storage5)
    

        for bag_enum in bags_to_check:
            bag = PyInventory.Bag(bag_enum.value, bag_enum.name)
            size = bag.GetSize()
            item_slots = [0] * size  # Pre-fill all slots with 0s

            for item in bag.GetItems():
                if 0 <= item.slot < size:
                    item_slots[item.slot] = item.item_id

            result.extend(item_slots)

        return result





    @staticmethod
    def GetFreeSlotCount():
        """
        Purpose: Calculate and return the number of free slots in bags 1, 2, 3, and 4.
        Args: None
        Returns: int: The number of free slots available across the four bags.
        """
        total_items, total_capacity = Inventory.GetInventorySpace()
        free_slots = total_capacity - total_items
        return max(free_slots, 0)

    @staticmethod
    def GetItemCount(item_id):
        """
        Purpose: Count the number of items with the specified item_id in bags 1, 2, 3, and 4.
        Args:
            item_id (int): The ID of the item to count.
        Returns: int: The total number of items matching the item_id in bags 1, 2, 3, and 4.
        """
        bags_to_check = ItemArray.CreateBagList(1,2,3,4)
        item_array = ItemArray.GetItemArray(bags_to_check)

        # Filter to get only the items that match the specified item_id
        matching_items = ItemArray.Filter.ByCondition(item_array, lambda item: item == item_id)

        # Use a lambda to sum the quantity of each matching item using Item.Properties.GetQuantity
        total_quantity = sum(Item.Properties.GetQuantity(item) for item in matching_items)

        return total_quantity

    @staticmethod
    def GetModelCount(model_id):
        """
        Purpose: Count the number of items with the specified model_id in bags 1, 2, 3, and 4.
        Args:
            model_id (int): The model ID of the item to count.
        Returns: int: The total number of items matching the model_id in bags 1, 2, 3, and 4.
        """
        bags_to_check = ItemArray.CreateBagList(1,2,3,4)
        item_array = ItemArray.GetItemArray(bags_to_check)
        
        # Filter items by the specified model_id using Item.GetModelID
        matching_items = ItemArray.Filter.ByCondition(item_array, lambda item_id: Item.GetModelID(item_id) == model_id)
        # Sum the quantity of each matching item using Item.Properties.GetQuantity
        total_quantity = sum(Item.Properties.GetQuantity(item_id) for item_id in matching_items)

        return total_quantity
    
    @staticmethod
    def GetModelCountInStorage(model_id):
        """
        Purpose: Count the number of items with the specified model_id in storage.
        Args:
            model_id (int): The model ID of the item to count.
        Returns: int: The total number of items matching the model_id in bags 1, 2, 3, and 4.
        """
        bags_to_check = ItemArray.CreateBagList(8,9,10,11,12,13,14,15,16,17,18,19,20,21)
        item_array = ItemArray.GetItemArray(bags_to_check)
        
        # Filter items by the specified model_id using Item.GetModelID
        matching_items = ItemArray.Filter.ByCondition(item_array, lambda item_id: Item.GetModelID(item_id) == model_id)
        # Sum the quantity of each matching item using Item.Properties.GetQuantity
        total_quantity = sum(Item.Properties.GetQuantity(item_id) for item_id in matching_items)

        return total_quantity
    
    @staticmethod
    def GetModelCountInEquipped(model_id):
        """
        Purpose: Count the number of items with the specified model_id in storage.
        Args:
            model_id (int): The model ID of the item to count.
        Returns: int: The total number of items matching the model_id in bags 1, 2, 3, and 4.
        """
        bags_to_check = ItemArray.CreateBagList(22)
        item_array = ItemArray.GetItemArray(bags_to_check)
        
        # Filter items by the specified model_id using Item.GetModelID
        matching_items = ItemArray.Filter.ByCondition(item_array, lambda item_id: Item.GetModelID(item_id) == model_id)
        # Sum the quantity of each matching item using Item.Properties.GetQuantity
        total_quantity = sum(Item.Properties.GetQuantity(item_id) for item_id in matching_items)

        return total_quantity

    @staticmethod
    def GetFirstIDKit():
        """
        Purpose: Find the Identification Kit (ID Kit) with the lowest remaining uses in bags 1, 2, 3, and 4.
        Returns:
            int: The Item ID of the ID Kit with the lowest uses, or 0 if no ID Kit is found.
        """
        bags_to_check = ItemArray.CreateBagList(1,2,3,4)
        item_array = ItemArray.GetItemArray(bags_to_check)
        # Filter to find items that are ID Kits using Item.Usage.IsIDKit
        id_kits = ItemArray.Filter.ByCondition(item_array, Item.Usage.IsIDKit)
        
        if not id_kits:
            return 0  # Return 0 if no ID Kit is found
        # Sort the ID Kits by remaining uses using Item.Usage.GetUses and get the one with the lowest uses
        id_kit_with_lowest_uses = min(id_kits, key=lambda item_id: Item.Usage.GetUses(item_id))

        return id_kit_with_lowest_uses


    @staticmethod
    def GetFirstUnidentifiedItem():
        """
        Purpose: Find the first unidentified item in bags 1, 2, 3, and 4.
        Returns:
            int: The Item ID of the first unidentified item found, or 0 if no unidentified item is found.
        """
        bags_to_check = ItemArray.CreateBagList(1,2,3,4)
        item_array = ItemArray.GetItemArray(bags_to_check)

        unidentified_items = ItemArray.Filter.ByCondition(item_array, lambda item_id: not Item.Usage.IsIdentified(item_id))
        
        return unidentified_items[0] if unidentified_items else 0
        
    @staticmethod
    def GetFirstSalvageKit(use_lesser =True):
        """
        Purpose: Find the salvage kit with the lowest remaining uses in bags 1, 2, 3, and 4.
        Returns:
            int: The Item ID of the salvage kit with the lowest uses, or 0 if no salvage kit is found.
        """
        bags_to_check = ItemArray.CreateBagList(1,2,3,4)
        item_array = ItemArray.GetItemArray(bags_to_check)

        salvage_kits = ItemArray.Filter.ByCondition(item_array, Item.Usage.IsSalvageKit)
        if use_lesser:
            salvage_kits = ItemArray.Filter.ByCondition(salvage_kits, lambda item_id: Item.Usage.IsLesserKit(item_id))
            
        if not salvage_kits:
            return 0  # Return 0 if no salvage kit is found
        salvage_kit_with_lowest_uses = min(salvage_kits, key=lambda item_id: Item.Usage.GetUses(item_id))
        
        return salvage_kit_with_lowest_uses


    
    @staticmethod
    def GetFirstSalvageableItem():
        """
        Purpose: Find the first salvageable item in bags 1, 2, 3, and 4.
        Returns:
            int: The Item ID of the first salvageable item found, or 0 if no salvageable item is found.
        """
        bags_to_check = ItemArray.CreateBagList(1,2,3,4)
        item_array = ItemArray.GetItemArray(bags_to_check)
    
        salvageable_items = ItemArray.Filter.ByCondition(item_array, Item.Usage.IsSalvageable)

        return salvageable_items[0] if salvageable_items else 0


    @staticmethod
    def IdentifyItem (item_id, id_kit_id):
        """
        Purpose: Identify an item using an Identification Kit.
        Args:
            item_id (int): The ID of the item to identify.
            id_kit_id (int): The ID of the Identification Kit to use.
        Returns: None
        """
        inventory = PyInventory.PyInventory()
        inventory.IdentifyItem(id_kit_id, item_id)

    @staticmethod
    def IdentifyFirst():
        """
        Purpose: Identify the first unidentified item found in bags 1, 2, 3, and 4 using the first available ID kit.
                 Items are filtered by the given list of exact rarities (e.g., ["White", "Purple", "Gold"]).
        Args:
            rarities (list of str, optional): The rarity filter for identification.
        Returns:
            bool: True if an item was identified, False if no unidentified item or ID kit was found.
        """
        # Get the first ID Kit
        id_kit_id = Inventory.GetFirstIDKit()
        if id_kit_id == 0:
            Py4GW.Console.Log("IdentifyFirst", "No ID Kit found.")
            return False

        # Find the first unidentified item based on the rarity filter
        unid_item_id = Inventory.GetFirstUnidentifiedItem()
        if unid_item_id == 0:
            Py4GW.Console.Log("IdentifyFirst", "No unidentified item found.")
            return False

        # Use the ID Kit to identify the item
        inventory = PyInventory.PyInventory()
        inventory.IdentifyItem(id_kit_id, unid_item_id)
        Py4GW.Console.Log("IdentifyFirst", f"Identified item with Item ID: {unid_item_id} using ID Kit ID: {id_kit_id}")
        return True

    @staticmethod
    def SalvageItem(item_id,salvage_kit_id):
        """
        Purpose: Salvage an item using a Salvage Kit.
        Args:
            salvage_kit_id (int): The ID of the Salvage Kit to use.
            item_id (int): The ID of the item to salvage.
        Returns: None
        """
        inventory = PyInventory.PyInventory()
        inventory.Salvage(salvage_kit_id, item_id)

    @staticmethod
    def SalvageFirst():
        """
        Purpose: Salvage the first salvageable item found in bags 1, 2, 3, and 4 using the first available salvage kit.
                 Items are filtered by the given list of exact rarities (e.g., ["White", "Purple", "Gold"]).
        Args:
            rarities (list of str, optional): The rarity filter for salvage.
        Returns:
            bool: True if an item was salvaged, False if no salvageable item or salvage kit was found.
        """
        # Get the first available Salvage Kit
        salvage_kit_id = Inventory.GetFirstSalvageKit()
        if salvage_kit_id == 0:
            Py4GW.Console.Log("SalvageFirst", "No salvage kit found.")
            return False

        # Find the first salvageable item based on the rarity filter
        salvage_item_id = Inventory.GetFirstSalvageableItem()
        if salvage_item_id == 0:
            Py4GW.Console.Log("SalvageFirst", "No salvageable item found.")
            return False

        # Use the Salvage Kit to salvage the item
        inventory = PyInventory.PyInventory()
        inventory.Salvage(salvage_kit_id, salvage_item_id)
        Py4GW.Console.Log("SalvageFirst", f"Started salvaging item with Item ID: {salvage_item_id} using Salvage Kit ID: {salvage_kit_id}")

        return False

    
    
    @staticmethod
    def AcceptSalvageMaterialsWindow():
        """
        Checks if the Salvage Materials Dialog frame exists and clicks it if it hasn't already been clicked.
        Returns:
            bool: True if click was performed, False otherwise.
        """
        from .GWUI import GWUI
        from .UIManager import UIManager

        parent_hash = 140452905
        yes_button_offsets = [6,110,6]
        
        salvage_material_window = UIManager.GetChildFrameID(parent_hash, yes_button_offsets)
        UIManager.FrameClick(salvage_material_window)
     
        #return Inventory.inventory_instance().AcceptSalvageWindow()

    @staticmethod
    def _get_frame_id_by_alias(frame_label: str) -> int:
        from .UIManager import UIManager

        frame_id = int(UIManager.GetFrameIDByCustomLabel(frame_label=frame_label) or 0)
        if frame_id == 0 or not UIManager.FrameExists(frame_id):
            return 0
        return frame_id

    @staticmethod
    def _get_all_child_frame_ids_from_frame_id(root_frame_id: int, child_offsets: list[int]) -> list[int]:
        from .UIManager import UIManager
        import PyUIManager

        if root_frame_id == 0:
            return []

        matching_ids: list[int] = []
        for frame_id in UIManager.GetFrameArray():
            try:
                current_frame = PyUIManager.UIFrame(frame_id)
            except Exception:
                continue

            offsets: list[int] = []
            trace = current_frame
            for _ in range(len(child_offsets)):
                offsets.insert(0, int(trace.child_offset_id))
                if trace.parent_id == 0:
                    break
                trace = PyUIManager.UIFrame(trace.parent_id)

            if int(trace.frame_id) == root_frame_id and offsets == child_offsets:
                matching_ids.append(int(current_frame.frame_id))

        return matching_ids

    @staticmethod
    def _get_salvage_choice_material_confirm_yes_frame_id() -> int:
        from .UIManager import UIManager

        yes_frame_id = Inventory._get_frame_id_by_alias(Inventory.SALVAGE_CHOICE_MATERIAL_CONFIRM_YES_LABEL)
        if yes_frame_id != 0:
            return yes_frame_id

        fallback_frame_id = UIManager.GetChildFrameID(
            Inventory.SALVAGE_CHOICE_FALLBACK_DIALOG_HASH,
            [
                Inventory.SALVAGE_CHOICE_FALLBACK_MATERIAL_CONFIRM_ROOT_OFFSET,
                Inventory.SALVAGE_CHOICE_FALLBACK_MATERIAL_CONFIRM_YES_OFFSET,
            ],
        )
        if fallback_frame_id == 0 or not UIManager.FrameExists(fallback_frame_id):
            return 0
        return fallback_frame_id

    @staticmethod
    def IsSalvageChoiceMaterialConfirmVisible() -> bool:
        return Inventory._get_salvage_choice_material_confirm_yes_frame_id() != 0

    @staticmethod
    def _get_salvage_choice_dialog_frame_id() -> int:
        from .UIManager import UIManager

        dialog_frame_id = Inventory._get_frame_id_by_alias(Inventory.SALVAGE_CHOICE_DIALOG_LABEL)
        if dialog_frame_id != 0:
            return dialog_frame_id

        fallback_frame_id = UIManager.GetFrameIDByHash(Inventory.SALVAGE_CHOICE_FALLBACK_DIALOG_HASH)
        if fallback_frame_id == 0 or not UIManager.FrameExists(fallback_frame_id):
            return 0
        return fallback_frame_id

    @staticmethod
    def _get_salvage_choice_option_container_frame_id() -> int:
        from .UIManager import UIManager

        option_parent_id = Inventory._get_frame_id_by_alias(Inventory.SALVAGE_CHOICE_OPTION_CONTAINER_LABEL)
        if option_parent_id != 0:
            return option_parent_id

        fallback_frame_id = UIManager.GetChildFrameID(
            Inventory.SALVAGE_CHOICE_FALLBACK_DIALOG_HASH,
            [Inventory.SALVAGE_CHOICE_FALLBACK_OPTION_CONTAINER_OFFSET],
        )
        if fallback_frame_id == 0 or not UIManager.FrameExists(fallback_frame_id):
            return 0
        return fallback_frame_id

    @staticmethod
    def _get_salvage_choice_confirm_frame_id() -> int:
        from .UIManager import UIManager

        confirm_frame_id = Inventory._get_frame_id_by_alias(Inventory.SALVAGE_CHOICE_CONFIRM_LABEL)
        if confirm_frame_id != 0:
            return confirm_frame_id

        fallback_frame_id = UIManager.GetChildFrameID(
            Inventory.SALVAGE_CHOICE_FALLBACK_DIALOG_HASH,
            [Inventory.SALVAGE_CHOICE_FALLBACK_CONFIRM_OFFSET],
        )
        if fallback_frame_id == 0 or not UIManager.FrameExists(fallback_frame_id):
            return 0
        return fallback_frame_id

    @staticmethod
    def IsSalvageChoiceDialogVisible() -> bool:
        return Inventory._get_salvage_choice_dialog_frame_id() != 0

    @staticmethod
    def _build_frame_children_map() -> dict[int, list[int]]:
        from collections import defaultdict
        from .UIManager import UIManager
        import PyUIManager

        children_map: dict[int, list[int]] = defaultdict(list)
        for frame_id in UIManager.GetFrameArray():
            try:
                frame = PyUIManager.UIFrame(frame_id)
            except Exception:
                continue
            children_map[frame.parent_id].append(frame_id)

        return children_map

    @staticmethod
    def _build_visible_frame_entry_map() -> dict[int, list[VisibleFrameEntry]]:
        from collections import defaultdict
        from .UIManager import UIManager
        import PyUIManager

        visible_entries_by_parent: dict[int, list[VisibleFrameEntry]] = defaultdict(list)
        for frame_id in UIManager.GetFrameArray():
            try:
                frame = PyUIManager.UIFrame(frame_id)
            except Exception:
                continue

            if not frame.is_created or not frame.is_visible:
                continue

            width = float(frame.position.width_on_screen)
            height = float(frame.position.height_on_screen)
            if width <= 0 or height <= 0:
                continue

            template_type = getattr(frame, "template_type", -1)
            if template_type is None:
                template_type = -1

            visible_entries_by_parent[int(frame.parent_id)].append({
                "frame_id": int(frame.frame_id),
                "parent_id": int(frame.parent_id),
                "offset": int(getattr(frame, "child_offset_id", -1)),
                "left": float(frame.position.left_on_screen),
                "top": float(frame.position.top_on_screen),
                "width": width,
                "height": height,
                "area": width * height,
                "template_type": int(template_type),
                "text": "",
            })

        for child_entries in visible_entries_by_parent.values():
            child_entries.sort(key=lambda entry: (entry["offset"], entry["top"], entry["frame_id"]))

        return visible_entries_by_parent

    @staticmethod
    def _collect_frame_text(frame_id: int, children_map: dict[int, list[int]] | None = None, max_depth: int = 1) -> str:
        from collections import deque
        import PyUIManager

        text_attrs = (
            "text",
            "label",
            "caption",
            "component_label",
            "component_text",
            "frame_label",
            "name",
            "name_enc",
        )

        collected_text: list[str] = []
        queued_frames = deque([(frame_id, 0)])
        visited_frames: set[int] = set()

        while queued_frames:
            current_frame_id, depth = queued_frames.popleft()
            if current_frame_id in visited_frames:
                continue
            visited_frames.add(current_frame_id)

            try:
                frame = PyUIManager.UIFrame(current_frame_id)
                if hasattr(frame, "get_context"):
                    frame.get_context()
            except Exception:
                continue

            for attr_name in text_attrs:
                value = getattr(frame, attr_name, None)
                if isinstance(value, bytes):
                    try:
                        value = value.decode("utf-8", errors="ignore")
                    except Exception:
                        value = ""
                if not isinstance(value, str):
                    continue

                normalized_text = " ".join(value.split()).strip()
                if normalized_text and normalized_text not in collected_text:
                    collected_text.append(normalized_text)

            if children_map is None or depth >= max_depth:
                continue

            for child_frame_id in children_map.get(current_frame_id, []):
                queued_frames.append((child_frame_id, depth + 1))

        return " | ".join(collected_text)

    @staticmethod
    def _collect_salvage_choice_option_text(
        frame_ids: list[int],
        children_map: dict[int, list[int]] | None = None,
        max_depth: int = 2,
    ) -> str:
        collected_text: list[str] = []
        for frame_id in frame_ids:
            frame_text = Inventory._collect_frame_text(frame_id, children_map=children_map, max_depth=max_depth)
            for text_part in frame_text.split(" | "):
                normalized_text = " ".join(text_part.split()).strip()
                if normalized_text and normalized_text not in collected_text:
                    collected_text.append(normalized_text)

        return " | ".join(collected_text)

    @staticmethod
    def _collect_visible_frame_subtree_entries(
        root_frame_ids: list[int],
        visible_entries_by_parent: dict[int, list[VisibleFrameEntry]],
        max_depth: int = 2,
    ) -> list[SalvageChoiceEntry]:
        from collections import deque

        visible_entries_by_frame: dict[int, SalvageChoiceEntry] = {
            int(entry["frame_id"]): cast(SalvageChoiceEntry, dict(entry))
            for child_entries in visible_entries_by_parent.values()
            for entry in child_entries
        }

        collected_entries: list[SalvageChoiceEntry] = []
        visited_frame_ids: set[int] = set()
        queued_frame_ids = deque((int(frame_id), 0) for frame_id in root_frame_ids)

        while queued_frame_ids:
            frame_id, depth = queued_frame_ids.popleft()
            if frame_id in visited_frame_ids:
                continue
            visited_frame_ids.add(frame_id)

            current_entry = visible_entries_by_frame.get(frame_id)
            if current_entry is None:
                continue

            current_entry = cast(SalvageChoiceEntry, dict(current_entry))
            current_entry["subtree_depth"] = depth
            collected_entries.append(current_entry)

            if depth >= max_depth:
                continue

            for child_entry in visible_entries_by_parent.get(frame_id, []):
                queued_frame_ids.append((int(child_entry["frame_id"]), depth + 1))

        return collected_entries

    @staticmethod
    def _pick_salvage_choice_click_entry(
        candidate_entries: list[SalvageChoiceEntry],
    ) -> SalvageChoiceEntry | None:
        if not candidate_entries:
            return None

        def _priority(entry: SalvageChoiceEntry) -> tuple[int, float, int, float, int, int]:
            template_type = int(entry.get("template_type", -1))
            subtree_depth = int(entry.get("subtree_depth", 0))
            priority_bucket = 0 if template_type == 1 and subtree_depth > 0 else 1 if template_type == 1 else 2 if subtree_depth > 0 else 3
            return (
                priority_bucket,
                -float(entry.get("area", 0.0)),
                subtree_depth,
                float(entry.get("top", 0.0)),
                int(entry.get("offset", -1)),
                int(entry.get("frame_id", 0)),
            )

        sorted_candidates = sorted(candidate_entries, key=_priority)
        return cast(SalvageChoiceEntry, dict(sorted_candidates[0]))

    @staticmethod
    def _get_salvage_choice_dialog_options(
        visible_entries_by_parent: dict[int, list[VisibleFrameEntry]] | None = None,
    ) -> tuple[int, list[VisibleFrameEntry], list[SalvageChoiceEntry]]:
        option_parent_id = Inventory._get_salvage_choice_option_container_frame_id()
        if option_parent_id == 0:
            return 0, [], []

        if visible_entries_by_parent is None:
            visible_entries_by_parent = Inventory._build_visible_frame_entry_map()

        direct_children = [
            cast(VisibleFrameEntry, dict(entry))
            for entry in visible_entries_by_parent.get(option_parent_id, [])
        ]

        direct_positive_entries = [
            entry
            for entry in direct_children
            if int(entry.get("offset", -1)) >= 1
        ]

        nested_option_sources: list[SalvageChoiceOptionSource] = []
        container_candidates = sorted(
            [entry for entry in direct_children if int(entry.get("offset", -1)) == 0],
            key=lambda entry: (
                0 if int(entry.get("template_type", -1)) == 1 else 1,
                -float(entry.get("area", 0.0)),
                float(entry.get("top", 0.0)),
                int(entry.get("frame_id", 0)),
            ),
        )
        for container_entry in container_candidates:
            nested_children = visible_entries_by_parent.get(int(container_entry["frame_id"]), [])
            positive_nested_children = [
                nested_entry
                for nested_entry in nested_children
                if int(nested_entry.get("offset", -1)) >= 1
            ]
            if not positive_nested_children:
                continue

            for nested_entry in positive_nested_children:
                nested_offset = int(nested_entry.get("offset", -1))
                nested_option_sources.append({
                    "offset": nested_offset,
                    "path_offsets": [0, nested_offset],
                    "fallback_frame_id": int(nested_entry["frame_id"]),
                    "source_depth": 2,
                    "container_frame_id": int(container_entry["frame_id"]),
                })

            if nested_option_sources:
                break

        option_sources: list[SalvageChoiceOptionSource] = []
        if nested_option_sources:
            option_sources.extend(nested_option_sources)
            nested_offsets = {int(source["offset"]) for source in nested_option_sources}
            for direct_entry in direct_positive_entries:
                direct_offset = int(direct_entry.get("offset", -1))
                if direct_offset in nested_offsets:
                    continue

                option_sources.append({
                    "offset": direct_offset,
                    "path_offsets": [direct_offset],
                    "fallback_frame_id": int(direct_entry["frame_id"]),
                    "source_depth": 1,
                    "container_frame_id": None,
                })
        else:
            for direct_entry in direct_positive_entries:
                direct_offset = int(direct_entry.get("offset", -1))
                option_sources.append({
                    "offset": direct_offset,
                    "path_offsets": [direct_offset],
                    "fallback_frame_id": int(direct_entry["frame_id"]),
                    "source_depth": 1,
                    "container_frame_id": None,
                })

        option_entries: list[SalvageChoiceEntry] = []
        seen_offsets: set[int] = set()
        for source in sorted(option_sources, key=lambda item: (int(item["offset"]), len(item["path_offsets"]))):
            option_offset = int(source["offset"])
            if option_offset in seen_offsets:
                continue
            seen_offsets.add(option_offset)

            path_offsets = [int(offset) for offset in source["path_offsets"]]
            path_root_frame_ids = Inventory._get_all_child_frame_ids_from_frame_id(option_parent_id, path_offsets)

            fallback_frame_id = int(source["fallback_frame_id"])
            if not path_root_frame_ids and fallback_frame_id != 0:
                path_root_frame_ids = [fallback_frame_id]

            candidate_entries = Inventory._collect_visible_frame_subtree_entries(
                path_root_frame_ids,
                visible_entries_by_parent,
                max_depth=2,
            )
            if not candidate_entries and fallback_frame_id != 0:
                candidate_entries = Inventory._collect_visible_frame_subtree_entries(
                    [fallback_frame_id],
                    visible_entries_by_parent,
                    max_depth=2,
                )
                if not path_root_frame_ids:
                    path_root_frame_ids = [fallback_frame_id]

            click_entry = Inventory._pick_salvage_choice_click_entry(candidate_entries)
            if click_entry is None:
                continue

            click_entry["offset"] = option_offset
            click_entry["source_depth"] = int(source["source_depth"])
            click_entry["path"] = "->".join(str(offset) for offset in path_offsets)
            click_entry["path_root_frame_ids"] = [int(frame_id) for frame_id in path_root_frame_ids]
            click_entry["group_frame_ids"] = [int(entry["frame_id"]) for entry in candidate_entries]
            click_entry["group_size"] = len(candidate_entries)
            option_entries.append(click_entry)

        if not option_entries:
            template_entries = [
                cast(SalvageChoiceEntry, dict(entry))
                for entry in direct_children
                if int(entry.get("template_type", -1)) == 1
            ]
            option_entries = template_entries or [cast(SalvageChoiceEntry, dict(entry)) for entry in direct_children]
            for entry in option_entries:
                if "path" not in entry:
                    entry["path"] = f"Options->{int(entry.get('offset', -1))}"
                if "group_frame_ids" not in entry:
                    entry["group_frame_ids"] = [int(entry["frame_id"])]
                if "group_size" not in entry:
                    entry["group_size"] = 1
                if "source_depth" not in entry:
                    entry["source_depth"] = 1

        option_entries.sort(key=lambda item: (int(item.get("offset", -1)), float(item.get("top", 0.0)), int(item["frame_id"])))
        return option_parent_id, direct_children, option_entries

    @staticmethod
    def _choose_salvage_choice_dialog_option(
        option_entries: list[SalvageChoiceEntry],
        strategy: int,
    ) -> tuple[SalvageChoiceEntry | None, str]:
        material_keywords = (
            "crafting material",
            "crafting materials",
            "materials",
            "material",
        )
        non_material_keywords = (
            "inscription",
            "grip",
            "haft",
            "snathe",
            "pommel",
            "hilt",
            "handle",
            "head",
            "wrapping",
            "string",
        )

        if not option_entries:
            return None, "no options"

        if strategy == 0:
            for entry in option_entries:
                option_text = str(entry.get("text", "")).lower()
                if any(keyword in option_text for keyword in material_keywords):
                    return entry, "prefer crafting materials (text match)"
            return option_entries[-1], "prefer crafting materials (last visible option fallback)"

        if strategy == 1:
            for entry in option_entries:
                option_text = str(entry.get("text", "")).lower()
                if any(keyword in option_text for keyword in non_material_keywords):
                    return entry, "prefer upgrades/components (text match)"

            material_frame_ids = {
                int(entry["frame_id"])
                for entry in option_entries
                if any(keyword in str(entry.get("text", "")).lower() for keyword in material_keywords)
            }
            if material_frame_ids and len(material_frame_ids) < len(option_entries):
                for entry in option_entries:
                    if int(entry["frame_id"]) not in material_frame_ids:
                        return entry, "prefer upgrades/components (non-material fallback)"

            return option_entries[0], "prefer upgrades/components (first visible option fallback)"

        return option_entries[0], "prefer upgrades/components (strategy fallback)"

    # DEBUG BLOCK START: salvage choice dialog troubleshooting
    @staticmethod
    def _salvage_choice_debug_log(debug_enabled: bool, log_module: str, message: str):
        if not debug_enabled:
            return

        from .Py4GWcorelib import ConsoleLog, Console

        ConsoleLog(log_module, message, Console.MessageType.Debug)

    @staticmethod
    def _format_salvage_choice_option(option_entry: SalvageChoiceEntry, total_options: int) -> str:
        option_index = option_entry["order"] if "order" in option_entry else 0
        frame_id = option_entry["frame_id"]
        child_offset = option_entry["offset"]
        option_text = option_entry["text"].strip()
        source_depth = option_entry["source_depth"] if "source_depth" in option_entry else 1
        option_path = option_entry["path"].strip() if "path" in option_entry else ""
        group_size = option_entry["group_size"] if "group_size" in option_entry else 0
        subtree_depth = option_entry["subtree_depth"] if "subtree_depth" in option_entry else 0
        template_type = option_entry["template_type"]

        summary = f"index={option_index}/{max(1, total_options)} frame_id={frame_id} child_offset={child_offset}"
        if option_path:
            summary += f" path={option_path}"
        if group_size > 0:
            summary += f" group_frames={group_size}"
        if source_depth > 1:
            summary += f" depth={source_depth}"
        if subtree_depth > 0:
            summary += f" click_depth={subtree_depth}"
        if template_type >= 0:
            summary += f" template={template_type}"
        if option_text:
            summary += f" text='{option_text}'"
        return summary
    # DEBUG BLOCK END

    @staticmethod
    def HandleSalvageChoiceMaterialConfirmDialog(
        auto_confirm: bool = False,
        queue_name: str = "SALVAGE",
        log_module: str = "SalvageItems",
        queue_wait_timeout_ms: int = 5000,
        poll_ms: int = 50,
        close_timeout_ms: int = 1500,
        debug_enabled: bool = False,
        item_id: int = 0,
    ):
        from .Py4GWcorelib import ActionQueueManager
        from .Routines import Routines
        from .UIManager import UIManager

        item_prefix = f"item_id={item_id} " if item_id else ""
        yes_frame_id = Inventory._get_salvage_choice_material_confirm_yes_frame_id()
        if yes_frame_id == 0:
            return "not_visible"

        if not auto_confirm:
            Inventory._salvage_choice_debug_log(
                debug_enabled,
                log_module,
                f"{item_prefix}destructive materials confirm visible yes_frame_id={yes_frame_id}; auto-confirm disabled.",
            )
            return "confirm_pending"

        Inventory._salvage_choice_debug_log(
            debug_enabled,
            log_module,
            f"{item_prefix}destructive materials confirm detected yes_frame_id={yes_frame_id}.",
        )
        ActionQueueManager().AddAction(queue_name, UIManager.FrameClick, yes_frame_id)
        ActionQueueManager().AddAction(queue_name, UIManager.TestMouseAction, yes_frame_id, 8, 0, 0)
        queue_drained = yield from Routines.Yield.Items._wait_for_empty_queue(
            queue_name,
            timeout_ms=queue_wait_timeout_ms,
            poll_ms=poll_ms,
        )
        if not queue_drained:
            Inventory._salvage_choice_debug_log(
                debug_enabled,
                log_module,
                f"{item_prefix}early exit: timed out waiting for queue '{queue_name}' after clicking destructive materials confirm yes.",
            )
            return "queue_timeout"

        waited_ms = 0
        while waited_ms < max(0, close_timeout_ms):
            if not Inventory.IsSalvageChoiceMaterialConfirmVisible():
                Inventory._salvage_choice_debug_log(
                    debug_enabled,
                    log_module,
                    f"{item_prefix}destructive materials confirm closed after yes in about {waited_ms}ms.",
                )
                return "handled"

            yield from Routines.Yield.wait(max(1, poll_ms))
            waited_ms += max(1, poll_ms)

        Inventory._salvage_choice_debug_log(
            debug_enabled,
            log_module,
            f"{item_prefix}timeout: destructive materials confirm stayed open for at least {close_timeout_ms}ms after clicking yes.",
        )
        return "close_timeout"

    @staticmethod
    def _wait_for_salvage_choice_dialog_close(
        auto_confirm_materials_warning: bool = False,
        queue_name: str = "SALVAGE",
        log_module: str = "SalvageItems",
        queue_wait_timeout_ms: int = 5000,
        poll_ms: int = 50,
        close_timeout_ms: int = 1500,
        debug_enabled: bool = False,
        item_id: int = 0,
        after_action_label: str = "confirm click",
    ):
        from .Routines import Routines

        item_prefix = f"item_id={item_id} " if item_id else ""
        waited_ms = 0
        while waited_ms < max(0, close_timeout_ms):
            confirm_status = yield from Inventory.HandleSalvageChoiceMaterialConfirmDialog(
                auto_confirm=auto_confirm_materials_warning,
                queue_name=queue_name,
                log_module=log_module,
                queue_wait_timeout_ms=queue_wait_timeout_ms,
                poll_ms=poll_ms,
                close_timeout_ms=close_timeout_ms,
                debug_enabled=debug_enabled,
                item_id=item_id,
            )
            if confirm_status == "handled":
                waited_ms = 0
                continue
            if confirm_status == "confirm_pending":
                return "confirm_pending"
            if confirm_status not in {"not_visible"}:
                return f"materials_confirm_{confirm_status}"

            if not Inventory.IsSalvageChoiceDialogVisible():
                Inventory._salvage_choice_debug_log(
                    debug_enabled,
                    log_module,
                    f"{item_prefix}dialog closed after {after_action_label} in about {waited_ms}ms.",
                )
                return "handled"

            yield from Routines.Yield.wait(max(1, poll_ms))
            waited_ms += max(1, poll_ms)

        Inventory._salvage_choice_debug_log(
            debug_enabled,
            log_module,
            f"{item_prefix}timeout: dialog stayed open for at least {close_timeout_ms}ms after {after_action_label}.",
        )
        return "close_timeout"

    @staticmethod
    def HandleSalvageChoiceDialog(
        auto_handle: bool = False,
        strategy: int = 0,
        auto_confirm_materials_warning: bool = False,
        queue_name: str = "SALVAGE",
        log_module: str = "SalvageItems",
        queue_wait_timeout_ms: int = 5000,
        poll_ms: int = 50,
        close_timeout_ms: int = 1500,
        debug_enabled: bool = False,
        item_id: int = 0,
    ):
        from .Py4GWcorelib import ActionQueueManager
        from .Routines import Routines
        from .UIManager import UIManager

        item_prefix = f"item_id={item_id} " if item_id else ""
        strategy_name = {
            0: "prefer_materials",
            1: "prefer_upgrades",
        }.get(strategy, f"unknown_{strategy}")

        if not auto_handle:
            Inventory._salvage_choice_debug_log(
                debug_enabled,
                log_module,
                f"{item_prefix}skip dialog handler: auto_handle disabled.",
            )
            return "disabled"

        dialog_frame_id = Inventory._get_salvage_choice_dialog_frame_id()
        if dialog_frame_id == 0:
            return "not_visible"

        Inventory._salvage_choice_debug_log(
            debug_enabled,
            log_module,
            f"{item_prefix}dialog detected label='{Inventory.SALVAGE_CHOICE_DIALOG_LABEL}' frame_id={dialog_frame_id} strategy={strategy_name}.",
        )

        if Inventory.IsSalvageChoiceMaterialConfirmVisible():
            return (yield from Inventory._wait_for_salvage_choice_dialog_close(
                auto_confirm_materials_warning=auto_confirm_materials_warning,
                queue_name=queue_name,
                log_module=log_module,
                queue_wait_timeout_ms=queue_wait_timeout_ms,
                poll_ms=poll_ms,
                close_timeout_ms=close_timeout_ms,
                debug_enabled=debug_enabled,
                item_id=item_id,
                after_action_label="materials confirm",
            ))

        children_map = Inventory._build_frame_children_map()
        visible_entries_by_parent = Inventory._build_visible_frame_entry_map()
        option_parent_id, option_parent_children, option_entries = Inventory._get_salvage_choice_dialog_options(visible_entries_by_parent)
        raw_child_summary = ", ".join(
            f"offset={int(entry.get('offset', -1))} frame_id={int(entry.get('frame_id', 0))} template={int(entry.get('template_type', -1))}"
            for entry in option_parent_children
        ) or "none"
        Inventory._salvage_choice_debug_log(
            debug_enabled,
            log_module,
            f"{item_prefix}option container label='{Inventory.SALVAGE_CHOICE_OPTION_CONTAINER_LABEL}' frame_id={option_parent_id} visible children: {raw_child_summary}.",
        )
        nested_container_summary = []
        for direct_entry in option_parent_children:
            if int(direct_entry.get("offset", -1)) != 0:
                continue
            nested_children = visible_entries_by_parent.get(int(direct_entry["frame_id"]), [])
            positive_nested_children = [
                entry
                for entry in nested_children
                if int(entry.get("offset", -1)) >= 1
            ]
            if not positive_nested_children:
                continue
            nested_child_summary = ", ".join(
                f"offset={int(entry.get('offset', -1))} frame_id={int(entry.get('frame_id', 0))} template={int(entry.get('template_type', -1))}"
                for entry in positive_nested_children
            )
            nested_container_summary.append(
                f"frame_id={int(direct_entry.get('frame_id', 0))}: {nested_child_summary}"
            )
        if nested_container_summary:
            Inventory._salvage_choice_debug_log(
                debug_enabled,
                log_module,
                f"{item_prefix}nested option rows under options container child[0]: {'; '.join(nested_container_summary)}.",
            )
        if not option_entries:
            Inventory._salvage_choice_debug_log(
                debug_enabled,
                log_module,
                f"{item_prefix}safety exit: dialog visible but no selectable options were found under the options container.",
            )
            return "no_option"

        for order, entry in enumerate(option_entries, start=1):
            entry["order"] = order
            path_root_frame_ids = list(entry["path_root_frame_ids"]) if "path_root_frame_ids" in entry else [int(entry["frame_id"])]
            entry["text"] = Inventory._collect_salvage_choice_option_text(
                path_root_frame_ids,
                children_map=children_map,
                max_depth=2,
            )

        selectable_indices = [int(entry["order"]) if "order" in entry else 0 for entry in option_entries]
        option_summaries = ", ".join(
            Inventory._format_salvage_choice_option(entry, len(option_entries))
            for entry in option_entries
        )
        Inventory._salvage_choice_debug_log(
            debug_enabled,
            log_module,
            f"{item_prefix}selectable options count={len(option_entries)} indices={selectable_indices}: {option_summaries}",
        )

        selected_entry, strategy_description = Inventory._choose_salvage_choice_dialog_option(
            option_entries,
            strategy,
        )
        if selected_entry is None:
            Inventory._salvage_choice_debug_log(
                debug_enabled,
                log_module,
                f"{item_prefix}safety exit: {strategy_description}.",
            )
            return "no_option"

        selected_summary = Inventory._format_salvage_choice_option(selected_entry, len(option_entries))
        Inventory._salvage_choice_debug_log(
            debug_enabled,
            log_module,
            f"{item_prefix}strategy result={strategy_description}; selected {selected_summary}.",
        )

        selected_frame_id = int(selected_entry["frame_id"])
        if not UIManager.FrameExists(selected_frame_id):
            Inventory._salvage_choice_debug_log(
                debug_enabled,
                log_module,
                f"{item_prefix}safety exit: selected option frame_id={selected_frame_id} is no longer clickable.",
            )
            return "option_missing"

        Inventory._salvage_choice_debug_log(
            debug_enabled,
            log_module,
            f"{item_prefix}activate option via test_mouse_click_action {selected_summary}.",
        )
        ActionQueueManager().AddAction(queue_name, UIManager.TestMouseClickAction, selected_frame_id, 0, 0)
        queue_drained = yield from Routines.Yield.Items._wait_for_empty_queue(
            queue_name,
            timeout_ms=queue_wait_timeout_ms,
            poll_ms=poll_ms,
        )
        if not queue_drained:
            Inventory._salvage_choice_debug_log(
                debug_enabled,
                log_module,
                f"{item_prefix}early exit: timed out waiting for queue '{queue_name}' after option click.",
            )
            return "queue_timeout"

        selection_settle_ms = max(150, poll_ms * 4)
        yield from Routines.Yield.wait(selection_settle_ms)

        if not Inventory.IsSalvageChoiceDialogVisible():
            Inventory._salvage_choice_debug_log(
                debug_enabled,
                log_module,
                f"{item_prefix}dialog closed after option click in about {selection_settle_ms}ms.",
            )
            return "handled"

        confirm_frame_id = Inventory._get_salvage_choice_confirm_frame_id()
        if confirm_frame_id == 0:
            Inventory._salvage_choice_debug_log(
                debug_enabled,
                log_module,
                f"{item_prefix}safety exit: confirm button alias='{Inventory.SALVAGE_CHOICE_CONFIRM_LABEL}' was not available after selecting the option.",
            )
            return "confirm_missing"

        Inventory._salvage_choice_debug_log(
            debug_enabled,
            log_module,
            f"{item_prefix}dialog still visible after option click; clicking confirm frame_id={confirm_frame_id}.",
        )
        ActionQueueManager().AddAction(queue_name, UIManager.FrameClick, confirm_frame_id)
        queue_drained = yield from Routines.Yield.Items._wait_for_empty_queue(
            queue_name,
            timeout_ms=queue_wait_timeout_ms,
            poll_ms=poll_ms,
        )
        if not queue_drained:
            Inventory._salvage_choice_debug_log(
                debug_enabled,
                log_module,
                f"{item_prefix}early exit: timed out waiting for queue '{queue_name}' after confirm click.",
            )
            return "queue_timeout"

        return (yield from Inventory._wait_for_salvage_choice_dialog_close(
            auto_confirm_materials_warning=auto_confirm_materials_warning,
            queue_name=queue_name,
            log_module=log_module,
            queue_wait_timeout_ms=queue_wait_timeout_ms,
            poll_ms=poll_ms,
            close_timeout_ms=close_timeout_ms,
            debug_enabled=debug_enabled,
            item_id=item_id,
            after_action_label="confirm click",
        ))

    @staticmethod
    def OpenXunlaiWindow():
        """
        Purpose: Open the Xunlai Storage window.
        Returns: bool: True if the Xunlai Storage window is opened, False if not.
        """
        Inventory.inventory_instance().OpenXunlaiWindow()
        return Inventory.inventory_instance().GetIsStorageOpen()

    @staticmethod
    def IsStorageOpen():
        """
        Purpose: Check if the Xunlai Storage window is open.
        Returns: bool: True if the Xunlai Storage window is open, False if not.
        """
        return Inventory.inventory_instance().GetIsStorageOpen()

    @staticmethod
    def PickUpItem(item_id, call_target=False):
        """
        Purpose: Pick up an item from the ground.
        Args:
            item_id (int): The ID of the item to pick up. (not agent_id)
            call_target (bool, optional): True to call the target, False to pick up the item directly.
        Returns: None
        """
        Inventory.inventory_instance().PickUpItem(item_id, call_target)

    @staticmethod
    def DropItem(item_id, quantity=1):
        """
        Purpose: Drop an item from the inventory.
        Args:
            item_id (int): The ID of the item to drop.
            quantity (int, optional): The quantity of the item to drop.
        Returns: None
        """
        return Inventory.inventory_instance().DropItem(item_id, quantity)

    @staticmethod
    def EquipItem(item_id, agent_id):
        """
        Purpose: Equip an item from the inventory.
        Args:
            item_id (int): The ID of the item to equip.
            agent_id (int): The agent ID of the player to equip the item.
        Returns: None
        """
        Inventory.inventory_instance().EquipItem(item_id, agent_id)

    @staticmethod
    def UseItem(item_id):
        """ 
        Purpose: Use an item from the inventory.
        Args:
            item_id (int): The ID of the item to use.
        Returns: None
        """
        Inventory.inventory_instance().UseItem(item_id)

    @staticmethod
    def DestroyItem(item_id):
        """
        Purpose: Destroy an item from the inventory.
        Args:
            item_id (int): The ID of the item to destroy.
        Returns: None
        """
        Inventory.inventory_instance().DestroyItem(item_id)

    @staticmethod
    def GetHoveredItemID():
        """
        Purpose: Get the hovered item ID.
        Args: None
        Returns: int: The hovered item ID.
        """
        return Inventory.inventory_instance().GetHoveredItemID()

    @staticmethod
    def GetGoldOnCharacter():
        """         
        Purpose: Retrieve the amount of gold on the character.
        Args: None
        Returns: int: The amount of gold on the character.
        """
        return Inventory.inventory_instance().GetGoldAmount()

    @staticmethod
    def GetGoldInStorage():
        """
        Purpose: Retrieve the amount of gold in storage.
        Args: None
        Returns: int: The amount of gold in storage.
        """
        return Inventory.inventory_instance().GetGoldAmountInStorage()

    @staticmethod
    def DepositGold(amount):
        """
        Purpose: Deposit gold into storage.
        Args:
            amount (int): The amount of gold to deposit.
        Returns: None
        """
        Inventory.inventory_instance().DepositGold(amount)

    @staticmethod
    def WithdrawGold(amount):
        """
        Purpose: Withdraw gold from storage.
        Args:
            amount (int): The amount of gold to withdraw.
        Returns: None
        """
        Inventory.inventory_instance().WithdrawGold(amount)

    @staticmethod
    def DropGold(amount):
        """
        Purpose: Drop a certain amount of gold.
        Args:
            amount (int): The amount of gold to drop.
        Returns: None
        """
        Inventory.inventory_instance().DropGold(amount)
           
    @staticmethod
    def MoveItem(item_id, bag_id, slot, quantity=1):
        """ 
        Purpose: Move an item within a bag.
        Args:
            item_id (int): The ID of the item to move.
            bag_id (int): The ID of the bag to move the item to.
            slot (int): The slot to move the item to.
            quantity (int, optional): The quantity of the item to move.
        Returns: None
        """
        Inventory.inventory_instance().MoveItem(item_id, bag_id, slot, quantity)

    @staticmethod
    def FindItemBagAndSlot(item_id):
        """
        Locate the bag ID and slot of the given item ID in inventory bags (1, 2, 3, 4).
    
        Args:
            item_id (int): The ID of the item to locate.
    
        Returns:
            tuple: (bag_id, slot) if the item is found, or (None, None) if not found.
        """
        # Convert integers to Bag enum members using CreateBagList
        bags_to_check = ItemArray.CreateBagList(1, 2, 3, 4)
    
        # Locate the item in the retrieved items
        for bag_enum in bags_to_check:
            bag_items = ItemArray.GetItemArray([bag_enum])  # Get items in the specific bag
            for item in bag_items:
                if item == item_id:
                    slot = Item.GetSlot(item)  # Get the item's slot
                    return bag_enum.value, slot  # Return bag ID and slot
        return None, None

    @staticmethod
    def DepositItemToStorage(item_id, Anniversary_panel = True):
        """
        Moves the specified item to storage, filling partial stacks first.
        Args:
            item_id (int): ID of the item to deposit.
            quantity (int): Amount to move. 0 means 'move all available'.
        Returns:
            bool: True if moved at least some of the items, False if failed.
        """
        from .enums import Bags
        
        def GetBags():
            possible_bags = ItemArray.CreateBagList(Bags.Storage1, Bags.Storage2, Bags.Storage3, Bags.Storage4,
                                                    *([Bags.Storage5] if Anniversary_panel else []),
                                                    Bags.Storage6,Bags.Storage7,Bags.Storage8,Bags.Storage9,Bags.Storage10,
                                                    Bags.Storage11,Bags.Storage12,Bags.Storage13,Bags.Storage14)
        
            # Dynamically calculate the total capacity using PyInventory.Bag
            total_capacity = sum(
                PyInventory.Bag(bag_enum.value, bag_enum.name).GetSize() for bag_enum in possible_bags
            )

            bags = total_capacity // 25

            storage_bags = []

            for i in range(1, bags + 1):
                    bag = getattr(Bags, f"Storage{i}")
                    storage_bags.append(bag)

            return storage_bags
    
        MAX_STACK_SIZE = 250

        is_stackable = Item.Customization.IsStackable(item_id)
        quantity = Item.Properties.GetQuantity(item_id)

        if quantity == 0:
            return False  # Nothing to move

        # Gather target bags
        storage_bags = GetBags()
    
        remaining_quantity = quantity
        moved_any = False

        for bag_enum in storage_bags:
            bag = PyInventory.Bag(bag_enum.value, bag_enum.name)
            size = bag.GetSize()
            items = bag.GetItems()

            # Fill existing partial stacks (only if stackable)
            if is_stackable:
                for item in items:
                    if item.model_id == Item.GetModelID(item_id):
                        item_qty = Item.Properties.GetQuantity(item.item_id)
                        if item_qty < MAX_STACK_SIZE:
                            space_left = MAX_STACK_SIZE - item_qty
                            to_move = min(space_left, remaining_quantity)
                            if to_move > 0:
                                Inventory.MoveItem(item_id, bag_enum.value, item.slot, to_move)
                                remaining_quantity -= to_move
                                moved_any = True
                                if remaining_quantity == 0:
                                    return True

            # Fill empty slots
            occupied_slots = {item.slot for item in items}
            for slot in range(size):
                if slot in occupied_slots:
                    continue

                to_move = remaining_quantity if not is_stackable else min(remaining_quantity, MAX_STACK_SIZE)
                Inventory.MoveItem(item_id, bag_enum.value, slot, to_move)
                remaining_quantity -= to_move
                moved_any = True
                if remaining_quantity == 0:
                    return True

        return moved_any

    @staticmethod
    def WithdrawItemFromStorage(item_id):
        """
        Moves the specified item from storage to player inventory, filling partial stacks first.
        Args:
            item_id (int): ID of the item to withdraw.
        Returns:
            bool: True if moved at least some of the items, False otherwise.
        """
        from .enums import Bags
        MAX_STACK_SIZE = 250

        is_stackable = Item.Customization.IsStackable(item_id)
        quantity = Item.Properties.GetQuantity(item_id)

        if quantity == 0:
            return False  # Nothing to move

        # Gather target bags (Backpack, Belt Pouch, Bag1, Bag2)
        inventory_bags = ItemArray.CreateBagList(Bags.Backpack, Bags.BeltPouch, Bags.Bag1, Bags.Bag2)

        remaining_quantity = quantity
        moved_any = False

        for bag_enum in inventory_bags:
            bag = PyInventory.Bag(bag_enum.value, bag_enum.name)
            size = bag.GetSize()
            items = bag.GetItems()

            # Fill existing partial stacks
            if is_stackable:
                for item in items:
                    if item.model_id == Item.GetModelID(item_id):
                        item_qty = Item.Properties.GetQuantity(item.item_id)
                        if item_qty < MAX_STACK_SIZE:
                            space_left = MAX_STACK_SIZE - item_qty
                            to_move = min(space_left, remaining_quantity)
                            if to_move > 0:
                                Inventory.MoveItem(item_id, bag_enum.value, item.slot, to_move)
                                remaining_quantity -= to_move
                                moved_any = True
                                if remaining_quantity == 0:
                                    return True

            # Fill empty slots
            occupied_slots = {item.slot for item in items}
            for slot in range(size):
                if slot in occupied_slots:
                    continue

                to_move = remaining_quantity if not is_stackable else min(remaining_quantity, MAX_STACK_SIZE)
                Inventory.MoveItem(item_id, bag_enum.value, slot, to_move)
                remaining_quantity -= to_move
                moved_any = True
                if remaining_quantity == 0:
                    return True

        return moved_any






