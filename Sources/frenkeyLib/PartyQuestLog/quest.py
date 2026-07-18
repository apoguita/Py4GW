from enum import IntEnum

from Sources.ApoSource.account_data_src.quest_data_src import QuestData

PERSISTENT = True

class QuestCache():
    __instance = None
    __initialized = False
    
    def __new__(cls):
        if cls.__instance is None:
            cls.__instance = super(QuestCache, cls).__new__(cls)
        return cls.__instance
    
    def __init__(self):
        if not self.__initialized:
            self.__initialized = True
            self.quest_data : QuestData = QuestData()
            
    