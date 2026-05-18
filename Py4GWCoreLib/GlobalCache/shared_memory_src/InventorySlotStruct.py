from ctypes import Structure, c_uint


class InventorySlotStruct(Structure):
    _pack_ = 1
    _fields_ = [
        ("BagID", c_uint),
        ("Slot", c_uint),
        ("ModelID", c_uint),
        ("Quantity", c_uint),
    ]

    BagID: int
    Slot: int
    ModelID: int
    Quantity: int

    def reset(self) -> None:
        self.BagID = 0
        self.Slot = 0
        self.ModelID = 0
        self.Quantity = 0
