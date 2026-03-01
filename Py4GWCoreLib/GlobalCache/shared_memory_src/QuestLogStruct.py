from ctypes import Structure, c_float, c_uint, c_bool
from .Globals import (
    SHMEM_MAX_QUESTS,
)
#region Quests  
class QuestStruct(Structure):
    _pack_ = 1
    _fields_ = [
        ("QuestID", c_uint),
        ("IsCompleted", c_bool),
        ("MarkerX", c_float),
        ("MarkerY", c_float),
    ]
    
    # Type hints for IntelliSense
    QuestID: int
    IsCompleted: bool
    MarkerX: float
    MarkerY: float
    
    def reset(self) -> None:
        """Reset all fields to zero."""
        self.QuestID = 0
        self.IsCompleted = False
        self.MarkerX = 0
        self.MarkerY = 0
    
class QuestLogStruct(Structure):
    _pack_ = 1
    _fields_ = [
        ("ActiveQuestID", c_uint),
        ("Quests", QuestStruct * SHMEM_MAX_QUESTS),  # 150 quests
    ]
    
    # Type hints for IntelliSense
    ActiveQuestID: int
    Quests: list[QuestStruct]
    
    def reset(self) -> None:
        """Reset all fields to zero."""
        self.ActiveQuestID = 0
        for i in range(SHMEM_MAX_QUESTS):
            self.Quests[i].reset()
            
    def from_context(self):
        from ...Quest import Quest
        self.reset()  # Clear existing data before populating
        active_quest_id = Quest.GetActiveQuest()
        self.ActiveQuestID = active_quest_id if active_quest_id is not None else 0
        
        quest_log = Quest.GetQuestLog()
        for i in range(min(SHMEM_MAX_QUESTS, len(quest_log))):
            quest_data = quest_log[i]
            self.Quests[i].QuestID = quest_data.quest_id if quest_data is not None else 0
            self.Quests[i].IsCompleted = quest_data.is_completed if quest_data is not None else False
            self.Quests[i].MarkerX = quest_data.marker_x if quest_data is not None else 0
            self.Quests[i].MarkerY = quest_data.marker_y if quest_data is not None else 0
  
