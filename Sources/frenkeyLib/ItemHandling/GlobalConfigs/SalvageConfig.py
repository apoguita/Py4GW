

from Py4GWCoreLib.Agent import Agent
from Py4GWCoreLib.AgentArray import AgentArray
from Py4GWCoreLib.Item import Bag, Item
from Py4GWCoreLib.ItemArray import ItemArray
from Py4GWCoreLib.Player import Player
from Py4GWCoreLib.Routines import Routines
from Py4GWCoreLib.enums_src.GameData_enums import Range

from Sources.frenkeyLib.ItemHandling.GlobalConfigs.RuleConfig import RuleConfig

class SalvageConfig(RuleConfig):    
    def GetSalvageItems(self, bags : list[Bag]) -> list[int]:                        
        if not Routines.Checks.Map.MapValid():
            return []
            
        item_ids = ItemArray.GetItemArray(ItemArray.CreateBagList(*bags))        
        filtered_array = []

        for item_id in item_ids[:]:  # Iterate over a copy to avoid modifying while iterating
            if not self.EvaluateItem(item_id):
                continue
            
            filtered_array.append(item_id)
            
        return filtered_array
