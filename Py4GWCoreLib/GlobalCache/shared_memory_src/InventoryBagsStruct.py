from ctypes import Structure

from Py4GWCoreLib.enums_src.Item_enums import Bags

from .InventoryBagStruct import InventoryBagStruct


class InventoryBagsStruct(Structure):
    _pack_ = 1
    _fields_ = [
        ("Backpack", InventoryBagStruct),
        ("BeltPouch", InventoryBagStruct),
        ("Bag1", InventoryBagStruct),
        ("Bag2", InventoryBagStruct),
    ]

    Backpack: InventoryBagStruct
    BeltPouch: InventoryBagStruct
    Bag1: InventoryBagStruct
    Bag2: InventoryBagStruct

    def reset(self) -> None:
        self.Backpack.reset()
        self.Backpack.BagID = int(Bags.Backpack.value)
        self.BeltPouch.reset()
        self.BeltPouch.BagID = int(Bags.BeltPouch.value)
        self.Bag1.reset()
        self.Bag1.BagID = int(Bags.Bag1.value)
        self.Bag2.reset()
        self.Bag2.BagID = int(Bags.Bag2.value)

    def iter_bags(self):
        yield self.Backpack
        yield self.BeltPouch
        yield self.Bag1
        yield self.Bag2
