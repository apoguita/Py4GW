from ctypes import Structure, c_uint

from .Globals import SHMEM_MAX_INVENTORY_BAG_SLOTS
from .InventorySlotStruct import InventorySlotStruct


class InventoryBagStruct(Structure):
    _pack_ = 1
    _fields_ = [
        ("BagID", c_uint),
        ("Size", c_uint),
        ("Slots", InventorySlotStruct * SHMEM_MAX_INVENTORY_BAG_SLOTS),
    ]

    BagID: int
    Size: int
    Slots: list[InventorySlotStruct]

    def reset(self) -> None:
        self.BagID = 0
        self.Size = 0
        for slot in self.Slots:
            slot.reset()
