from typing import ClassVar, Self, cast

from Py4GWCoreLib.Agent import Agent
from Py4GWCoreLib.AgentArray import AgentArray
from Py4GWCoreLib.Player import Player
from Py4GWCoreLib.Routines import Routines
from Py4GWCoreLib.enums_src.GameData_enums import Range

from Py4GWCoreLib.enums_src.Item_enums import ItemAction
from Sources.frenkeyLib.ItemHandling.GlobalConfigs.RuleConfig import RuleConfig

class LootConfig(RuleConfig):
    _initialized: bool = False
    _instances: ClassVar[dict[type[Self], Self]] = {}

    def __new__(cls: type[Self]) -> Self:
        instance = cast(Self | None, cls._instances.get(cls))
        if instance is None:
            instance = cast(Self, super().__new__(cls))
            instance._initialized = False
            cls._instances[cls] = instance
        return instance

    def __init__(self: Self) -> None:
        if self._initialized:
            return

        self._initialized = True
        super().__init__()
        
    def EvaluateItem(self, item_id):
        if not super().EvaluateItem(item_id):
            return False
        
        matched_rule = self.GetMatchedRule(item_id)
        return matched_rule is not None and matched_rule.action is ItemAction.PickUp

    def GetfilteredLootArray(self, distance: float = Range.SafeCompass.value, multibox_loot: bool = False, allow_unasigned_loot=False) -> list[int]:        
        def IsValidItem(item_id):
            if not Agent.IsValid(item_id):
                return False    
            player_agent_id = Player.GetAgentID()
            owner_id = Agent.GetItemAgentOwnerID(item_id)
            return ((owner_id == player_agent_id) or (owner_id == 0))
        
        if not Routines.Checks.Map.MapValid():
            return []
            
        item_array = AgentArray.GetItemArray()
        item_array = AgentArray.Filter.ByDistance(item_array, Player.GetXY(), distance)

        item_array = AgentArray.Filter.ByCondition(
            item_array,
            lambda item_id: IsValidItem(item_id)
        )
        
        filtered_array = []

        for agent_id in item_array[:]:  # Iterate over a copy to avoid modifying while iterating
            item_data = Agent.GetItemAgentByID(agent_id)
            if item_data is None:
                continue
            
            item_id = item_data.item_id
            
            if not self.EvaluateItem(item_id):
                continue
            
            filtered_array.append(agent_id)
            
        return AgentArray.Sort.ByDistance(filtered_array, Player.GetXY())
