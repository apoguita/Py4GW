import ctypes
from ctypes import c_void_p, c_uint32, c_size_t, POINTER
from typing import Generic, TypeVar, Optional, Iterator, List


# -----------------------------------------------------------
# C++: template <typename T> struct TLink
# Python: parameterize at use-site via elem_type in view
# -----------------------------------------------------------
class GW_TLink(ctypes.Structure):
    _pack_ = 1
    _fields_ = [
        ("prev_link", c_void_p),   # TLink*
        ("next_node", c_void_p),   # T*
    ]

    # ---- direct equivalents ----
    def IsLinked(self) -> bool:
        return int(self.prev_link) != ctypes.addressof(self)

    def Next(self, elem_type):
        addr = int(self.next_node)
        if addr & 1 or addr == 0:
            return None
        addr &= ~1
        return ctypes.cast(addr, POINTER(elem_type)).contents

    def Prev(self, elem_type):
        # prev_link->prev_link->next_node
        prev_link = ctypes.cast(self.prev_link, POINTER(GW_TLink)).contents
        prev_prev = ctypes.cast(prev_link.prev_link, POINTER(GW_TLink)).contents
        addr = int(prev_prev.next_node)
        if addr & 1 or addr == 0:
            return None
        addr &= ~1
        return ctypes.cast(addr, POINTER(elem_type)).contents

    def NextLink(self, elem_type, offset: int):
        """
        C++:
            const size_t offset = this - (prev_link->next_node & ~1);
            return (next_node & ~1) + offset
        but we compute offset externally as TList.offset
        """
        next_addr = int(self.next_node)
        if next_addr == 0:
            return None
        next_addr &= ~1
        return next_addr + offset

    def PrevLink(self):
        return int(self.prev_link)


class GW_TList(ctypes.Structure):
    _pack_ = 1
    _fields_ = [
        ("offset", c_uint32),   # offsetof(TLink inside T)
        ("link",   GW_TLink),   # sentinel node
    ]

# required by the original code
assert ctypes.sizeof(GW_TList) == 0xC

T = TypeVar("T")



class GW_TList_View(Generic[T]):
    __slots__ = ("_lst", "_elem_type")

    def __init__(self, lst: GW_TList, elem_type: type[T]) -> None:
        self._lst = lst
        self._elem_type = elem_type

    # ---- parity with GW_Array_View ----

    def valid(self) -> bool:
        return bool(int(self._lst.link.next_node))

    def size(self) -> int:
        # No m_size field => count
        return sum(1 for _ in self)

    def capacity(self) -> int:
        # list has no notion of capacity
        return self.size()

    # ---- element access ----

    def get(self, index: int) -> Optional[T]:
        if index < 0:
            index = self.size() + index
            if index < 0:
                return None
        for i, elem in enumerate(self):
            if i == index:
                return elem
        return None

    def __len__(self) -> int:
        return self.size()

    def __getitem__(self, index: int) -> T:
        elem = self.get(index)
        if elem is None:
            raise IndexError(index)
        return elem

    # ---- iteration like C++ iterator ----

    def __iter__(self) -> Iterator[T]:
        if not self.valid():
            return
        
        lst = self._lst
        elem_type = self._elem_type
        offset = int(lst.offset)

        # sentinel start
        curr_link_addr = ctypes.addressof(lst.link)

        while True:
            curr_link = ctypes.cast(
                curr_link_addr,
                POINTER(GW_TLink)
            ).contents

            next_addr = int(curr_link.next_node)
            if next_addr == 0 or (next_addr & 1):
                break

            next_addr &= ~1
            node_ptr = ctypes.cast(next_addr, ctypes.POINTER(elem_type))  # type: ignore[arg-type]

            yield node_ptr.contents   # T&

            # C++: iterator++ → current = current->NextLink()
            curr_link_addr = curr_link.NextLink(elem_type, offset)
            if curr_link_addr is None:
                break

    def __reversed__(self) -> Iterator[T]:
        return reversed(self.to_list())

    def to_list(self) -> List[T]:
        return list(self)