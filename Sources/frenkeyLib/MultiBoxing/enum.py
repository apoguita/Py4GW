from enum import Enum, auto

class RenameClientType(Enum):
    No_Rename = 0
    Email = auto()
    Character = auto()
    Custom = auto()

class MultiBoxingMessageType(Enum):
    NoMessage = 0
    ReloadSettings = auto()