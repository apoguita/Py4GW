
from enum import IntEnum

from Py4GWCoreLib.Item import Bag

INVENTORY_BAGS = [Bag.Backpack, Bag.Belt_Pouch, Bag.Bag_1, Bag.Bag_2]
STORAGE_BAGS = [Bag.Storage_1, Bag.Storage_2, Bag.Storage_3, Bag.Storage_4, Bag.Storage_5, Bag.Storage_6, Bag.Storage_7, Bag.Storage_8, Bag.Storage_9, Bag.Storage_10, Bag.Storage_11, Bag.Storage_12, Bag.Storage_13, Bag.Storage_14]


class MaterialType(IntEnum):
    None_ = 0
    Common = 1
    Rare = 2