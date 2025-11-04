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
    def IsMissionMapQuestAvailable():
        """
        Purpose: Check if a mission map quest is available.
        Args: None
        Returns: bool
        """
        return Quest.quest_instance().is_mission_map_quest_available()

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
    def GetQuestLogIds():
        """
        Purpose: Retrieve the quest log IDs.
        Args: None
        Returns: list[int]
        """
        return Quest.quest_instance().get_quest_log_ids()

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
        
    @staticmethod
    def RequestQuestName(quest_id):
        """
        Purpose: Request the name of a quest.
        Args:
            quest_id (int): The quest ID to request the name for.
        Returns: None
        """
        Quest.quest_instance().request_quest_name(quest_id)
        
    @staticmethod
    def IsQuestNameReady(quest_id):
        """
        Purpose: Check if the quest name is ready.
        Args: None
        Returns: bool
        """
        return Quest.quest_instance().is_quest_name_ready(quest_id)
    
    @staticmethod
    def GetQuestName(quest_id):
        """
        Purpose: Retrieve the name of the quest.
        Args: None
        Returns: str
        """
        return Quest.quest_instance().get_quest_name(quest_id)
    
    @staticmethod
    def RequestQuestDescription(quest_id):
        """
        Purpose: Request the description of a quest.
        Args:
            quest_id (int): The quest ID to request the description for.
        Returns: None
        """
        Quest.quest_instance().request_quest_description(quest_id)
        
    @staticmethod
    def IsQuestDescriptionReady(quest_id):
        """
        Purpose: Check if the quest description is ready.
        Args: None
        Returns: bool
        """
        return Quest.quest_instance().is_quest_description_ready(quest_id)
    
    @staticmethod
    def GetQuestDescription(quest_id):
        """
        Purpose: Retrieve the description of the quest.
        Args: None
        Returns: str
        """
        return Quest.quest_instance().get_quest_description(quest_id)
    
    @staticmethod
    def RequestQuestObjectives(quest_id):
        """
        Purpose: Request the objectives of a quest.
        Args:
            quest_id (int): The quest ID to request the objectives for.
        Returns: None
        """
        Quest.quest_instance().request_quest_objectives(quest_id)
        
    @staticmethod
    def IsQuestObjectivesReady(quest_id):
        """
        Purpose: Check if the quest objectives are ready.
        Args: None
        Returns: bool
        """
        return Quest.quest_instance().is_quest_objectives_ready(quest_id)
    
    @staticmethod
    def GetQuestObjectives(quest_id):
        """
        Purpose: Retrieve the objectives of the quest.
        Args: None
        Returns: str
        """
        return Quest.quest_instance().get_quest_objectives(quest_id)
    
    @staticmethod
    def RequestQuestLocation(quest_id):
        """
        Purpose: Request the location of a quest.
        Args:
            quest_id (int): The quest ID to request the location for.
        Returns: None
        """
        Quest.quest_instance().request_quest_location(quest_id)
        
    @staticmethod
    def IsQuestLocationReady(quest_id):
        """
        Purpose: Check if the quest location is ready.
        Args: None
        Returns: bool
        """
        return Quest.quest_instance().is_quest_location_ready(quest_id)
    
    @staticmethod
    def GetQuestLocation(quest_id):
        """
        Purpose: Retrieve the location of the quest.
        Args: None
        Returns: str
        """
        return Quest.quest_instance().get_quest_location(quest_id)
    
    @staticmethod
    def RequestQuestNPC(quest_id):
        """
        Purpose: Request the NPC associated with a quest.
        Args:
            quest_id (int): The quest ID to request the NPC for.
        Returns: None
        """
        Quest.quest_instance().request_quest_npc(quest_id)
        
    @staticmethod
    def IsQuestNPCReady(quest_id):
        """
        Purpose: Check if the quest NPC is ready.
        Args: None
        Returns: bool
        """
        return Quest.quest_instance().is_quest_npc_ready(quest_id)
    
    @staticmethod
    def GetQuestNPC(quest_id):
        """
        Purpose: Retrieve the NPC associated with the quest.
        Args: None
        Returns: str
        """
        return Quest.quest_instance().get_quest_npc(quest_id)   
    
        