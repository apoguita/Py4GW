# PyQuest.pyi - Type stub for PyQuest (PyBind11 bindings)
class QuestData:
    quest_id: int
    log_state : int
    #location :str
    #name : str
    #npc : str
    map_from : int
    map_to : int
    marker_x : float
    marker_y : float
    h0024 : int
    #description : str
    #objectives : str
    
    is_completed : bool
    is_current_mission_quest : bool
    is_area_primary : bool
    is_primary : bool

class PyQuest:
    def __init__(self) -> None: ...
    def set_active_quest_id(self, quest_id: int) -> None: ...
    def get_active_quest_id(self) -> int: ...
    def abandon_quest_id(self, quest_id: int) -> None: ...
    def is_quest_completed(self, quest_id: int) -> bool: ...
    def is_quest_primary(self, quest_id: int) -> bool: ...
    def get_quest_data(self, quest_id: int) -> QuestData: ...
    def get_quest_log (self) -> list[QuestData]: ...
    def request_quest_info(self, quest_id: int, update_marker: bool = False) -> None: ...
