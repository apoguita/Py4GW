from typing import Optional

import Py4GW

from Py4GWCoreLib import Map, Merchant, Player
from Py4GWCoreLib.Item import Bag
from Py4GWCoreLib.enums_src.GameData_enums import Attribute, Profession
from Py4GWCoreLib.enums_src.Item_enums import ItemType
from Py4GWCoreLib.enums_src.Region_enums import ServerLanguage
from Py4GWCoreLib.native_src.internals import string_table
from Py4GWCoreLib.py4gwcorelib_src.Timer import ThrottledTimer
from Sources.frenkeyLib.Core.encoded_names import ItemName
from Sources.frenkeyLib.ItemHandling.Items.ItemCache import ITEM_CACHE
from Sources.frenkeyLib.ItemHandling.Items.ItemData import ITEM_DATA, ItemData
from Sources.frenkeyLib.ItemHandling.Items.item_snapshot import ItemSnapshot

INVENTORY_BAGS = [
    Bag.Backpack,
    Bag.Belt_Pouch,
    Bag.Bag_1,
    Bag.Bag_2,
    Bag.Equipment_Pack,
    Bag.Equipped_Items,
]

STORAGE_BAGS = [
    Bag.Material_Storage,
    Bag.Storage_1,
    Bag.Storage_2,
    Bag.Storage_3,
    Bag.Storage_4,
    Bag.Storage_5,
    Bag.Storage_6,
    Bag.Storage_7,
    Bag.Storage_8,
    Bag.Storage_9,
    Bag.Storage_10,
    Bag.Storage_11,
    Bag.Storage_12,
    Bag.Storage_13,
    Bag.Storage_14,
]


class ItemCollector:
    def __init__(self, inventory_interval_ms: int = 5_000, save_interval_ms: int = 1_000):
        self.checked_item_ids: set[int] = set()
        self.checked_model_keys: set[tuple[ItemType, int]] = set()
        self.current_context_key = ""
        self.storage_checked_for_context = False
        self.force_inventory_scan = True

        self.run_throttle = ThrottledTimer(250)
        self.inventory_throttle = ThrottledTimer(inventory_interval_ms)
        self.trader_throttle = ThrottledTimer(1_000)
        self.save_throttle = ThrottledTimer(save_interval_ms)

    def run(self):
        if not self.run_throttle.IsExpired():
            self.flush_pending_save()
            return

        self.run_throttle.Reset()
        self.flush_pending_save()

        if not self._is_ready():
            return

        self._handle_context_change()

        if not self.storage_checked_for_context:
            self._scan_bags(STORAGE_BAGS)
            self.storage_checked_for_context = True

        if self.force_inventory_scan or self.inventory_throttle.IsExpired():
            self.inventory_throttle.Reset()
            self.force_inventory_scan = False
            self._scan_bags(INVENTORY_BAGS)

        if self.trader_throttle.IsExpired():
            self.trader_throttle.Reset()
            self._scan_trader_items()

        self.flush_pending_save()

    def flush_pending_save(self):
        if ITEM_DATA.requires_save and self.save_throttle.IsExpired():
            ITEM_DATA.save_data_if_queued()
            self.save_throttle.Reset()

    def _is_ready(self) -> bool:
        return Map.IsMapReady() and Player.IsPlayerLoaded()

    def _handle_context_change(self):
        context_key = self._get_context_key()
        if context_key == self.current_context_key:
            return

        self.current_context_key = context_key
        self.storage_checked_for_context = False
        self.force_inventory_scan = True
        self.checked_item_ids.clear()
        self.checked_model_keys.clear()
        ITEM_CACHE.reset()

    def _get_context_key(self) -> str:
        account_email = str(Player.GetAccountEmail() or "").strip()
        player_name = str(Player.GetName() or "").strip()
        map_id = int(Map.GetMapID() or 0)
        return f"{account_email}|{player_name}|{map_id}"

    def _scan_bags(self, bags: list[Bag]):
        ITEM_CACHE.reset()
        snapshot = ITEM_CACHE.get_bags_snapshot(bags)
        items = [item for bag in snapshot.values() for item in bag.values() if item is not None]

        for item in items:
            self._collect_item(item)

    def _scan_trader_items(self):
        offered_items = Merchant.Trading.Merchant.GetOfferedItems()
        offered_items = offered_items + Merchant.Trading.Trader.GetOfferedItems()
        offered_items = offered_items + Merchant.Trading.Trader.GetOfferedItems2()
        offered_items = offered_items + Merchant.Trading.Crafter.GetOfferedItems()
        offered_items = offered_items + Merchant.Trading.Collector.GetOfferedItems()
        
        for item_id in offered_items:
            item = ITEM_CACHE.get_item_snapshot(item_id) if item_id else None
            if item is None:
                continue
            self._collect_item(item)

    def _collect_item(self, item: ItemSnapshot):
        if not item.is_valid or item.model_id <= 0 or item.item_type == ItemType.Unknown:
            return

        model_key = (item.item_type, item.model_id)
        item_data = ITEM_DATA.get_or_create_item_data(item.item_type, item.model_id)
        if (item.id in self.checked_item_ids or model_key in self.checked_model_keys) and not self._item_needs_more_data(item_data):
            return

        changed = False

        if item_data.model_file_id <= 0 and item.model_file_id > 0:
            item_data.model_file_id = item.model_file_id
            changed = True

        name_encoded = self._get_name_enc_encoded(item)
        if name_encoded and item_data.name_encoded != name_encoded:
            item_data.name_encoded = name_encoded
            changed = True

        name_enc = self._get_name_enc(item)
        if name_enc and item_data.english_name != name_enc:
            item_data.english_name = name_enc
            changed = True

        if item.attribute not in (None, Attribute.None_) and item.attribute not in item_data.attributes:
            item_data.attributes = sorted(item_data.attributes + [item.attribute], key=lambda attr: attr.name)
            changed = True

        if item.profession not in (None, Profession._None) and item_data.profession != item.profession:
            item_data.profession = item.profession
            changed = True

        if changed:
            ITEM_DATA.queue_save()

        if not self._item_needs_more_data(item_data):
            self.checked_item_ids.add(item.id)
            self.checked_model_keys.add(model_key)

    def _item_needs_more_data(self, item_data: ItemData) -> bool:
        return (
            item_data.model_file_id <= 0
            or not item_data.name_encoded
            or not item_data.english_name
            or (
                item_data.item_type in {
                    ItemType.Axe,
                    ItemType.Bow,
                    ItemType.Daggers,
                    ItemType.Hammer,
                    ItemType.Offhand,
                    ItemType.Scythe,
                    ItemType.Shield,
                    ItemType.Spear,
                    ItemType.Staff,
                    ItemType.Sword,
                    ItemType.Wand,
                    ItemType.Headpiece,
                    ItemType.Chestpiece,
                    ItemType.Gloves,
                    ItemType.Leggings,
                    ItemType.Boots,
                }
                and len(item_data.attributes) == 0
            )
        )

    def _get_name_enc_encoded(self, item: ItemSnapshot) -> bytes:
        name_enc = item.name_enc
        try:
            if isinstance(name_enc, bytes):
                return name_enc
            if isinstance(name_enc, bytearray):
                return bytes(name_enc)
            if isinstance(name_enc, (list, tuple)):
                return bytes(name_enc)
        except Exception:
            pass

        return bytes()

    def _get_name_enc(self, item: ItemSnapshot) -> str:
        candidate = self._coerce_bytes(item.name_enc)
        if candidate:
            try:
                decoded = string_table.decode_plain(candidate, language=ServerLanguage.English)
                if decoded:
                    return decoded
            except Exception:
                pass

        return ""

    def _coerce_bytes(self, value) -> bytes:
        try:
            if isinstance(value, bytes):
                return value
            if isinstance(value, bytearray):
                return bytes(value)
            if isinstance(value, (list, tuple)):
                return bytes(value)
        except Exception:
            pass

        return bytes()


ITEM_COLLECTOR = ItemCollector()


def collect_item_data():
    ITEM_COLLECTOR.run()
