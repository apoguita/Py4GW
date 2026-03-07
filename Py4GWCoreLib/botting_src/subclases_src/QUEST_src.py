#region QUEST
from typing import TYPE_CHECKING

from Py4GWCoreLib.Quest import Quest

if TYPE_CHECKING:
    from Py4GWCoreLib.botting_src.helpers import BottingClass

#region QUEST
class _QUEST:
    def __init__(self, parent: "BottingClass"):
        self.parent = parent
        self._config = parent.config
        self._helpers = parent.helpers
        
    def AbandonQuest(self, quest_id: int) -> None:
        """Abandon a quest by its ID."""
        Quest.AbandonQuest(quest_id)
        
    def SetActiveQuest(self, quest_id: int) -> None:
        """Set the active quest by its ID."""
        Quest.SetActiveQuest(quest_id)
        
    def GetActiveQuest(self) -> int:
        """Get the currently active quest ID."""
        return Quest.GetActiveQuest()

    def IsQuestCompleted(self, quest_id: int) -> bool:
        """Check if a quest is completed and reward can be taken."""
        return Quest.IsQuestCompleted(quest_id)

    def GetQuestLogIds(self) -> list:
        """Get list of all quest IDs currently in the quest log."""
        return Quest.GetQuestLogIds()
