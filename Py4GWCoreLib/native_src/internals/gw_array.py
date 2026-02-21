import ctypes
from ctypes import c_uint32


class GW_BaseArray(ctypes.Structure):
    """GWCA BaseArray<T> — 0x0C bytes (buffer, capacity, size)."""
    _pack_ = 1
    _fields_ = [
        ("m_buffer", ctypes.c_void_p),  # T*
        ("m_capacity", c_uint32),
        ("m_size", c_uint32),
    ]

assert ctypes.sizeof(GW_BaseArray) == 0x0C


class GW_Array(ctypes.Structure):
    """GWCA Array<T> — 0x10 bytes (buffer, capacity, size, param)."""
    _pack_ = 1
    _fields_ = [
        ("m_buffer", ctypes.c_void_p),  # T*
        ("m_capacity", c_uint32),
        ("m_size", c_uint32),
        ("m_param", c_uint32),
    ]

assert ctypes.sizeof(GW_Array) == 0x10

class GW_Array_View:
    """
    ctx = WorldMapContext.get_context()
    if not ctx:
        return

    subcontexts = GW_Array_View(ctx.h0020, MissionMapSubContext)

    if subcontexts.valid():
        first = subcontexts[0]
        print(first.h0000[0])

    for sc in subcontexts:
        pass

    """
    __slots__ = ("_arr", "_elem_type")

    def __init__(self, arr: GW_Array, elem_type):
        self._arr = arr
        self._elem_type = elem_type

    # ---- C++ parity ----

    def valid(self) -> bool:
        return bool(self._arr.m_buffer)

    def size(self) -> int:
        return self._arr.m_size

    def capacity(self) -> int:
        return self._arr.m_capacity

    # ---- Safe typed access ----

    def get(self, index: int):
        if not self.valid():
            return None
        if index < 0 or index >= self._arr.m_size:
            return None

        buf = ctypes.cast(
            self._arr.m_buffer,
            ctypes.POINTER(ctypes.POINTER(self._elem_type))
        )
        return buf[index].contents

    def __len__(self):
        return self._arr.m_size

    def __getitem__(self, index: int):
        elem = self.get(index)
        if elem is None:
            raise IndexError(index)
        return elem

    def __iter__(self):
        if not self.valid():
            return
        buf = ctypes.cast(
            self._arr.m_buffer,
            ctypes.POINTER(ctypes.POINTER(self._elem_type))
        )
        for i in range(self._arr.m_size):
            yield buf[i].contents

    def __reversed__(self):
        if not self.valid():
            return
        buf = ctypes.cast(
            self._arr.m_buffer,
            ctypes.POINTER(ctypes.POINTER(self._elem_type))
        )
        for i in range(self._arr.m_size - 1, -1, -1):
            yield buf[i].contents
            
    def to_list(self):
        if not self.valid():
            return []

        buf = ctypes.cast(
            self._arr.m_buffer,
            ctypes.POINTER(ctypes.POINTER(self._elem_type))
        )
        size = self._arr.m_size
        return [buf[i].contents for i in range(size)]
    

class GW_Array_Value_View:
    """
    For GW::Array<T>  (value arrays, not pointer arrays)

    Example:
        agents = GW_Array_Value_View(ctx.map_agents_array, MapAgent).to_list()
    """
    __slots__ = ("_arr", "_elem_type")

    def __init__(self, arr: GW_Array, elem_type):
        self._arr = arr
        self._elem_type = elem_type

    def valid(self) -> bool:
        return bool(self._arr.m_buffer)

    def size(self) -> int:
        return self._arr.m_size

    def get(self, index: int):
        if not self.valid():
            return None
        if index < 0 or index >= self._arr.m_size:
            return None

        base = ctypes.cast(
            self._arr.m_buffer,
            ctypes.POINTER(self._elem_type)
        )
        return base[index]

    def __len__(self):
        return self._arr.m_size

    def __getitem__(self, index: int):
        elem = self.get(index)
        if elem is None:
            raise IndexError(index)
        return elem

    def __iter__(self):
        if not self.valid():
            return
        base = ctypes.cast(
            self._arr.m_buffer,
            ctypes.POINTER(self._elem_type)
        )
        for i in range(self._arr.m_size):
            yield base[i]

    def to_list(self):
        if not self.valid():
            return []
        base = ctypes.cast(
            self._arr.m_buffer,
            ctypes.POINTER(self._elem_type)
        )
        return [base[i] for i in range(self._arr.m_size)]
