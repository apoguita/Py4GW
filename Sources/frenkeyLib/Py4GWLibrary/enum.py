from enum import IntEnum


class LayoutMode(IntEnum):
    Library = 0
    Compact = 1
    Minimalistic = 2
    
class SortMode(IntEnum):
    ByName = 0
    ByCategory = 1
    ByStatus = 2
    
class ViewMode(IntEnum):
    All = 0
    Favorites = 1
    Actives = 2
    Inactives = 3