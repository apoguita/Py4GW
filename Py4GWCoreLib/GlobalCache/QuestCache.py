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
    
    def IsMissionMapQuestAvailable(self):
        return self._quest_instance.is_mission_map_quest_available()
    
    def GetQuestData(self, quest_id):
        return self._quest_instance.get_quest_data(quest_id)
    
    def GetQuestLog(self):
        return self._quest_instance.get_quest_log()
    
    def GetQuestLogIds(self):
        return self._quest_instance.get_quest_log_ids()
    
    def RequestQuestInfo(self, quest_id, update_marker=False):
        self._action_queue_manager.AddAction("ACTION", self._quest_instance.request_quest_info, quest_id, update_marker)
        
    def RequestQuestName(self, quest_id):
        self._action_queue_manager.AddAction("ACTION", self._quest_instance.request_quest_name, quest_id)
        
    def IsQuestNameReady(self, quest_id):
        return self._quest_instance.is_quest_name_ready(quest_id)

    def GetQuestName(self, quest_id):
        return self._quest_instance.get_quest_name(quest_id)
    
    def RequestQuestDescription(self, quest_id):
        self._action_queue_manager.AddAction("ACTION", self._quest_instance.request_quest_description, quest_id)
        
    def IsQuestDescriptionReady(self, quest_id):
        return self._quest_instance.is_quest_description_ready(quest_id)
    
    def GetQuestDescription(self, quest_id):
        return self._quest_instance.get_quest_description(quest_id)
    
    def RequestQuestObjectives(self, quest_id):
        self._action_queue_manager.AddAction("ACTION", self._quest_instance.request_quest_objectives, quest_id)
        
    def IsQuestObjectivesReady(self, quest_id):
        return self._quest_instance.is_quest_objectives_ready(quest_id)
    
    def GetQuestObjectives(self, quest_id):
        return self._quest_instance.get_quest_objectives(quest_id)
    
    def RequestQuestLocation(self, quest_id):
        self._action_queue_manager.AddAction("ACTION", self._quest_instance.request_quest_location, quest_id)
        
    def IsQuestLocationReady(self, quest_id):
        return self._quest_instance.is_quest_location_ready(quest_id)
    
    def GetQuestLocation(self, quest_id):
        return self._quest_instance.get_quest_location(quest_id)
    
    def RequestQuestNPC(self, quest_id):
        self._action_queue_manager.AddAction("ACTION", self._quest_instance.request_quest_npc, quest_id)
        
    def IsQuestNPCReady(self, quest_id):
        return self._quest_instance.is_quest_npc_ready(quest_id)
    
    def GetQuestNPC(self, quest_id):
        return self._quest_instance.get_quest_npc(quest_id)