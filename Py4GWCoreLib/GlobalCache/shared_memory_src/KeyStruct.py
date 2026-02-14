from ctypes import Structure, c_uint, c_uint64

#region Key
class KeyStruct(Structure):
    _pack_ = 1
    _fields_ = [
        ("HWND", c_uint64),
        ("EntityType", c_uint), #0 = player, 1 = hero, 2 = pet , 3 = npc, 4 = minion
        ("LocalIndex", c_uint),
        ("LastUpdated", c_uint64),
    ]
    
    HWND: int
    EntityType: int
    LocalIndex: int
    LastUpdated: int
    
    def reset(self) -> None:
        """Reset all fields to zero."""
        self.HWND = 0
        self.EntityType = 0
        self.LocalIndex = 0
        self.LastUpdated = 0
    
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
    
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, KeyStruct):
            return NotImplemented
        return (self.HWND == other.HWND and
                self.EntityType == other.EntityType and
                self.LocalIndex == other.LocalIndex)
