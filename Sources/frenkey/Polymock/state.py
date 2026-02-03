import datetime
from Py4GWCoreLib import AgentArray, Quest
from Py4GWCoreLib.GlobalCache import GLOBAL_CACHE
from Py4GWCoreLib.Item import Bag
from Py4GWCoreLib import Map, Agent
from Py4GWCoreLib.Py4GWcorelib import ConsoleLog, Utils
from Py4GWCoreLib.enums import Allegiance, Bags, ItemType
from Sources.frenkey.Polymock.data import Polymock_Quest, Polymock_Quests, Polymock_Spawns, PolymockPieces


class WidgetState:
    instance = None

    def __new__(cls):
        if cls.instance is None:
            cls.instance = super(WidgetState, cls).__new__(cls)            
            cls.quest: Polymock_Quest | None = None
            cls.in_arena: bool = False
            cls.match_started: bool = False
            cls.has_polymock_piece: bool = False       
            cls.status_message: str = ""
            cls.debug: bool = False    

        return cls.instance
    
    def Log(self, message: str):
        self.status_message = "[" + datetime.datetime.now().strftime("%H:%M:%S") + "] " + message
        
        if self.debug:
            ConsoleLog("Polymock", message)
        
    def update(self):
        self.get_quest()
        self.check_for_polymock_pieces()
        pass
    
    def check_for_polymock_pieces(self):
        model_ids = [
            piece.value.item_model_id for piece in PolymockPieces
        ]
        
        inventory = GLOBAL_CACHE.ItemArray.GetItemArray([Bag.Backpack, Bag.Belt_Pouch, Bag.Bag_1, Bag.Bag_2])
        
        self.has_polymock_piece = any(
            GLOBAL_CACHE.Item.GetModelID(item_id) in model_ids and GLOBAL_CACHE.Item.GetItemType(item_id)[0] == ItemType.Trophy.value for item_id in inventory
        )
    
    def get_quest(self):        
        map_id = Map.GetMapID()
        
        self.in_arena = False
        for spawn in Polymock_Spawns:
            if spawn.value[0] == map_id:
                self.in_arena = True                
                self.match_started = len(AgentArray.GetAgentArray()) == 9 or self.match_started
                
                target_id = self.GetAgentAtPosition()
                quest = Polymock_Quests.get_quest_by_model_id(Agent.GetModelID(target_id))
                
                if quest:                
                    self.quest = quest       
                     
                    if GLOBAL_CACHE.Quest.GetActiveQuest() != self.quest.quest_id:
                        GLOBAL_CACHE.Quest.SetActiveQuest(self.quest.quest_id)   
                            
                    return
        
        if not self.in_arena:
            self.match_started = False
            quests = GLOBAL_CACHE.Quest.GetQuestLog()
            for quest in reversed(quests):
                for polymock_quest in Polymock_Quests:
                    if quest.quest_id == polymock_quest.value.quest_id:
                        self.quest = polymock_quest.value
                                                
                        if GLOBAL_CACHE.Quest.GetActiveQuest() != self.quest.quest_id:
                            GLOBAL_CACHE.Quest.SetActiveQuest(self.quest.quest_id)
                            
                        return
        
        self.quest = None
    
    def GetAgentAtPosition(self) -> int:
        agents = AgentArray.GetAgentArray()
        map_id = Map.GetMapID()

        spawn_point = next(
            (spawn for spawn in Polymock_Spawns if spawn.value[0] == map_id), None)

        if not spawn_point:
            return 0

        spawn_point = spawn_point.value[1]

        agent_array = AgentArray.Filter.ByDistance(agents, spawn_point, 250)
        agent_array = AgentArray.Sort.ByDistance(agent_array, spawn_point)
        agent_id = Utils.GetFirstFromArray(agent_array)

        if agent_id:
            x, y = Agent.GetXY(agent_id)
            distance = Utils.Distance(spawn_point, [x, y])
            if distance < 250.0:
                return agent_id

        return 0