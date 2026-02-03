from enum import Enum, auto


class EventType(Enum):

    SPIRIT_CREATED = auto()

    PLAYER_STUCK = auto()
    
    PLAYER_CRITICAL_STUCK = auto()
    PARTY_DEATH = auto()
    PLAYER_CRITICAL_DEATH = auto()

    MAP_CHANGED = auto()

    CHEST_OPENED = auto()