import PyQuest

class Quest:
    def quest_instance():
        return PyQuest.PyQuest()

    @staticmethod
    def GetActiveQuest():
        """
        Purpose: Retrieve the active quest.
        Args: None
        Returns: int
        """
        return Quest.quest_instance().get_active_quest_id()

    @staticmethod
    def SetActiveQuest(quest_id):
        """
        Purpose: Set the active quest.
        Args:
            quest_id (int): The quest ID to set.
        Returns: None
        """
        Quest.quest_instance().set_active_quest_id(quest_id)

    @staticmethod
    def AbandonQuest(quest_id):
        """
        Purpose: Abandon a quest.
        Args:
            quest_id (int): The quest ID to abandon.
        Returns: None
        """
        Quest.quest_instance().abandon_quest(quest_id)
