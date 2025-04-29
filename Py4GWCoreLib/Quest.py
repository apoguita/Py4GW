import PyQuest

class Quest:
    @staticmethod
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
        Quest.quest_instance().abandon_quest_id(quest_id)
        
    @staticmethod
    def IsQuestCompleted(quest_id):
        """
        Purpose: Check if a quest is completed.
        Args:
            quest_id (int): The quest ID to check.
        Returns: bool
        """
        return Quest.quest_instance().is_quest_completed(quest_id)

    @staticmethod
    def IsQuestPrimary(quest_id):
        """
        Purpose: Check if a quest is primary.
        Args:
            quest_id (int): The quest ID to check.
        Returns: bool
        """
        return Quest.quest_instance().is_quest_primary(quest_id)

    @staticmethod
    def GetQuestData(quest_id):
        """
        Purpose: Retrieve quest data.
        Args:
            quest_id (int): The quest ID to retrieve data for.
        Returns: QuestData
        """
        return Quest.quest_instance().get_quest_data(quest_id)
    
    @staticmethod
    def GetQuestLog():
        """
        Purpose: Retrieve the quest log.
        Args: None
        Returns: list[int]
        """
        return Quest.quest_instance().get_quest_log()
    
    @staticmethod
    def RequestQuestInfo(quest_id, update_marker=False):
        """
        Purpose: Request information about a quest.
        Args:
            quest_id (int): The quest ID to request information for.
            update_marker (bool): Whether to update the marker or not.
        Returns: None
        """
        Quest.quest_instance().request_quest_info(quest_id, update_marker)
        