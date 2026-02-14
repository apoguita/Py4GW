from ctypes import Structure, c_uint
from .Globals import SHMEM_MAX_TITLES
#region Titles  
class TitleUnitStruct(Structure):
    _pack_ = 1
    _fields_ = [
        ("TitleID", c_uint),
        ("CurrentPoints", c_uint),
    ]
    
    # Type hints for IntelliSense
    TitleID: int
    CurrentPoints: int
    
    def reset(self) -> None:
        """Reset all fields to zero."""
        self.TitleID = 0
        self.CurrentPoints = 0

class TitlesStruct(Structure):
    _pack_ = 1
    _fields_ = [
        ("ActiveTitleID", c_uint),
        ("Titles", TitleUnitStruct * SHMEM_MAX_TITLES),  # 48 titles
    ]
    
    # Type hints for IntelliSense
    ActiveTitleID: int
    Titles: list[TitleUnitStruct]
    
    def reset(self) -> None:
        """Reset all fields to zero."""
        self.ActiveTitleID = 0
        for i in range(SHMEM_MAX_TITLES):
            self.Titles[i].reset()
            
    def from_context(self):
        from ...Player import Player
        active_title_id = Player.GetActiveTitleID()
        self.ActiveTitleID = active_title_id if active_title_id is not None else 0
        
        titles_data = Player.GetTitleArrayRaw()
        for i in range(min(SHMEM_MAX_TITLES, len(titles_data))):
            title = self.Titles[i]
            
            title.TitleID = title.TitleID
            title.CurrentPoints = title.CurrentPoints
        
        for i in range(SHMEM_MAX_TITLES):
            title_data = Player.GetTitle(i)
            self.Titles[i].TitleID = i
            self.Titles[i].CurrentPoints = title_data.current_points if title_data is not None else 0
            
  