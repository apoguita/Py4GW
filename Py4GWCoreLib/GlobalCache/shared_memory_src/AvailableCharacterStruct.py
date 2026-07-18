from ctypes import Structure, c_uint, c_bool, c_wchar
from .Globals import (
    SHMEM_MAX_CHAR_LEN,
    SHMEM_MAX_AVAILABLE_CHARS,
)


class AvailableCharacterUnitStruct(Structure):
    _pack_ = 1
    _fields_ = [
        ("Name", c_wchar * SHMEM_MAX_CHAR_LEN),
        ("Level", c_uint),
        ("IsPvP", c_bool),
        ("MapID", c_uint),
        ("Professions", c_uint * 2),  # Primary and Secondary Profession
        ("CampaignID", c_uint),  
    ]
    
    # Type hints for IntelliSense
    Name: str
    Level: int
    IsPvP: bool
    MapID: int
    Professions: tuple[int, int]
    CampaignID: int
    
    def reset(self) -> None:
        """Reset all fields to default values."""
        self.Name = ""
        self.Level = 0
        self.IsPvP = False
        self.MapID = 0
        self.Professions = (0, 0)
        self.CampaignID = 0
    
class AvailableCharacterStruct(Structure):
    _pack_ = 1
    _fields_ = [
        ("Characters", AvailableCharacterUnitStruct * SHMEM_MAX_AVAILABLE_CHARS),
    ]
    
    # Type hints for IntelliSense
    Characters: list[AvailableCharacterUnitStruct]
    
    def reset(self) -> None:
        """Reset all character slots."""
        for i in range(SHMEM_MAX_AVAILABLE_CHARS):
            self.Characters[i].reset()
            
    def from_context(self) -> None:
        """Populate the structure with available character data from the game."""
        from ...Map import Map
        available_characters = Map.Pregame.GetAvailableCharacterList()
        for i in range(min(SHMEM_MAX_AVAILABLE_CHARS, len(available_characters))):
            char = available_characters[i]
            self.Characters[i].Name = char.player_name
            self.Characters[i].Level = char.level
            self.Characters[i].IsPvP = char.is_pvp
            self.Characters[i].MapID = char.map_id
            self.Characters[i].Professions = (char.primary, char.secondary)
            self.Characters[i].CampaignID = char.campaign
    