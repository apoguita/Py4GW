from ctypes import Structure, c_uint, c_uint64
import Py4GW

#region Key
class KeyStruct(Structure):
    _pack_ = 1
    _fields_ = [
        ("HWND", c_uint64),
        ("EntityType", c_uint), #0 = player, 1 = hero, 2 = pet , 3 = npc, 4 = minion
        ("LocalIndex", c_uint),
    ]
    
    HWND: int
    EntityType: int
    LocalIndex: int
    
    def reset(self) -> None:
        """Reset all fields to zero."""
        self.HWND = 0
        self.EntityType = 0
        self.LocalIndex = 0

    def AsPlayerKey(self, hwnd: int) -> "KeyStruct":
        """Set the key for a player."""
        self.HWND = hwnd
        self.EntityType = 0x0
        self.LocalIndex = 0
        return self

    def AsHeroKey(self, hwnd: int, hero_index: int) -> "KeyStruct":
        """Set the key for a hero."""
        self.HWND = hwnd
        self.EntityType = 0x1
        self.LocalIndex = hero_index
        return self

    def AsPetKey(self, hwnd: int, pet_index: int) -> "KeyStruct":
        """Set the key for a pet."""
        self.HWND = hwnd
        self.EntityType = 0x2
        self.LocalIndex = pet_index
        return self

        
    def AsNPCKey(self, hwnd: int, npc_index: int) -> "KeyStruct":
        """Set the key for an NPC."""
        self.HWND = hwnd
        self.EntityType = 0x3
        self.LocalIndex = npc_index
        return self

    def AsMinionKey(self, hwnd: int, minion_index: int) -> "KeyStruct":
        """Set the key for a minion."""
        self.HWND = hwnd
        self.EntityType = 0x4
        self.LocalIndex = minion_index
        return self
        
    def to_tuple(self) -> tuple[int, int, int]:
        """Return the key as a tuple (HWND, EntityType, LocalIndex)."""
        return (self.HWND, self.EntityType, self.LocalIndex)
    
    def from_tuple(self, data: tuple[int, int, int]) -> None:
        """Set the key from a tuple (HWND, EntityType, LocalIndex)."""
        self.HWND, self.EntityType, self.LocalIndex = data
        
    @property
    def is_valid(self) -> bool:
        """Return True if the key is valid (HWND is not zero)."""
        return self.HWND != 0
    
    
    @property
    def is_player(self) -> bool:
        """Return True if the key is for a player."""
        return self.EntityType == 0x0
    
    @property
    def is_hero(self) -> bool:
        """Return True if the key is for a hero."""
        return self.EntityType == 0x1
    
    @property
    def is_pet(self) -> bool:
        """Return True if the key is for a pet."""
        return self.EntityType == 0x2
    
    @property
    def is_npc(self) -> bool:
        """Return True if the key is for an NPC."""
        return self.EntityType == 0x3
    
    @property
    def is_minion(self) -> bool:
        """Return True if the key is for a minion."""
        return self.EntityType == 0x4
    
    #operators
    def is_child_of(self, parent_key: "KeyStruct") -> bool:
        """Return True if the current key is a child of the given parent key."""
        if not self.is_valid or not parent_key.is_valid:
            return False
        if self.HWND != parent_key.HWND:
            return False
        if self.EntityType == 0x1 and parent_key.EntityType == 0x0:  # Hero is child of Player
            return True
        if self.EntityType == 0x2 and parent_key.EntityType == 0x1:  # Pet is child of Hero
            return True
        if self.EntityType == 0x3 and parent_key.EntityType in (0x0, 0x1):  # NPC can be child of Player or Hero
            return True
        if self.EntityType == 0x4 and parent_key.EntityType in (0x1, 0x3):  # Minion can be child of Hero or NPC
            return True
        return False
    
    def __hash__(self):
        return hash((self.HWND, self.EntityType, self.LocalIndex))
    
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, KeyStruct):
            return NotImplemented
        return (self.HWND == other.HWND and
                self.EntityType == other.EntityType and
                self.LocalIndex == other.LocalIndex)
