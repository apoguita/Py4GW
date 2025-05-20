import PyQuest
from Py4GWCoreLib.Py4GWcorelib import ActionQueueManager


class QuestCache:
    def __init__(self, action_queue_manager):
        self._quest_instance = PyQuest.PyQuest()
        self._action_queue_manager:ActionQueueManager = action_queue_manager

    def GetActiveQuest(self):
        return self._quest_instance.get_active_quest_id()
    
    def SetActiveQuest(self, quest_id):
        self._action_queue_manager.AddAction("ACTION", self._quest_instance.set_active_quest_id, quest_id)
        
    def AbandonQuest(self, quest_id):
        self._action_queue_manager.AddAction("ACTION", self._quest_instance.abandon_quest_id, quest_id)
        
    def IsQuestCompleted(self, quest_id):
        return self._quest_instance.is_quest_completed(quest_id)
    
    def IsQuestPrimary(self, quest_id):
        return self._quest_instance.is_quest_primary(quest_id)
    
    def GetQuestData(self, quest_id):
        return self._quest_instance.get_quest_data(quest_id)
    
    def GetQuestLog(self):
        return self._quest_instance.get_quest_log()
    
    def RequestQuestInfo(self, quest_id, update_marker=False):
        self._action_queue_manager.AddAction("ACTION", self._quest_instance.request_quest_info, quest_id, update_marker)