# PyQuest.pyi - Type stub for PyQuest (PyBind11 bindings)
class QuestData:
    quest_id: int
    log_state : int
    location :str
    name : str
    npc : str
    map_from : int
    map_to : int
    marker_x : float
    marker_y : float
    h0024 : int
    description : str
    objectives : str
    
    is_completed : bool
    is_current_mission_quest : bool
    is_area_primary : bool
    is_primary : bool

class PyQuest:
    def __init__(self) -> None: ...

    @staticmethod
    def set_active_quest_id(quest_id: int) -> None: ...
    
    @staticmethod
    def get_active_quest_id() -> int: ...
    
    @staticmethod
    def abandon_quest_id(quest_id: int) -> None: ...
    
    @staticmethod
    def is_quest_completed(quest_id: int) -> bool: ...
    
    @staticmethod
    def is_quest_primary(quest_id: int) -> bool: ...
    
    @staticmethod
    def is_mission_map_quest_available() -> bool: ...
    
    @staticmethod
    def get_quest_data(quest_id: int) -> QuestData: ...
    
    @staticmethod
    def get_quest_log() -> list[QuestData]: ...
    
    @staticmethod
    def get_quest_log_ids() -> list[int]: ...
    
    @staticmethod
    def request_quest_info(quest_id: int, update_markers: bool = False) -> bool: ...
    
    @staticmethod
    def request_quest_name(quest_id: int) -> None: ...
    
    @staticmethod
    def is_quest_name_ready(quest_id: int) -> bool: ...
    
    @staticmethod
    def get_quest_name(quest_id: int) -> str: ...
    
    @staticmethod
    def request_quest_description(quest_id: int) -> None: ...
    
    @staticmethod
    def is_quest_description_ready(quest_id: int) -> bool: ...
    
    @staticmethod
    def get_quest_description(quest_id: int) -> str: ...
    
    @staticmethod
    def request_quest_objectives(quest_id: int) -> None: ...
    
    @staticmethod
    def is_quest_objectives_ready(quest_id: int) -> bool: ...
    
    @staticmethod
    def get_quest_objectives(quest_id: int) -> str: ...

    @staticmethod
    def request_quest_location(quest_id: int) -> None: ...
    
    @staticmethod
    def is_quest_location_ready(quest_id: int) -> bool: ...
    
    @staticmethod
    def get_quest_location(quest_id: int) -> str: ...
    
    @staticmethod
    def request_quest_npc(quest_id: int) -> None: ...

    @staticmethod
    def is_quest_npc_ready(quest_id: int) -> bool: ...

    @staticmethod
    def get_quest_npc(quest_id: int) -> str: ...