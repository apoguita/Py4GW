
from typing import Generator, Optional

from Py4GWCoreLib import Merchant
from Py4GWCoreLib.Inventory import Inventory
from Py4GWCoreLib.Item import Bag
from Sources.frenkeyLib.ItemHandling.Items.item_snapshot import ItemSnapshot
from Sources.frenkeyLib.ItemHandling.Rules.profile import RuleProfile
from Sources.frenkeyLib.ItemHandling.Rules.types import ACTION_LIMITS_PER_FRAME, ItemAction
from Sources.frenkeyLib.ItemHandling.utility import GetZeroFilledBags



class MerchantConfig:
    def __init__(self):
        self.rules : RuleProfile = RuleProfile.load_by_name("Default Merchant Rules")
        
    
    def run(self):
        merchant_open = False
        
        if merchant_open:
            start_bag : Bag = Bag.Backpack
            end_bag : Bag = Bag.Bag_2
            inventory_array, inventory_sizes = GetZeroFilledBags(start_bag, end_bag)
            
            # Handle all yield based actions (ACTION_LIMITS_PER_FRAME)
            if self.yield_action is not None:
                try:
                    next(self.yield_action)

                except StopIteration:
                    self.yield_action = None

            # Selling Actions (Sell_To_Trader, Sell_To_Merchant)
            for item_id in inventory_array:
                if item_id == 0:
                    continue
                
                action = self.rules.get_action_for_item(item_id)
                item = ItemSnapshot.from_item_id(item_id) if item_id else None
                
                if item is None:
                    continue
                
                if action != ItemAction.NONE:
                    if action is ItemAction.Sell_To_Trader:
                        # If we don't have an action in progress and the new action is a yield based action, start it                
                        if self.yield_action is None:
                            # Start the action and store the generator
                            generator = self.get_generator_for_action(item_id, action)
                            if generator is not None:
                                self.yield_action = generator
                        
                    else:
                        match action:
                            case ItemAction.Sell_To_Merchant:
                                Merchant.Trading.Merchant.SellItem(item.id, item.quantity * item.value)
            
            for item_id in Merchant.Trading.Merchant.GetOfferedItems():
                action = self.rules.get_action_for_item(item_id)
                item = ItemSnapshot.from_item_id(item_id) if item_id else None
                
                if action != ItemAction.NONE:
                    if action is ItemAction.Buy_From_Merchant:
                        # If we don't have an action in progress and the new action is a yield based action, start it                
                        if self.yield_action is None:
                            # Start the action and store the generator
                            generator = self.get_generator_for_action(item_id, action)
                            if generator is not None:
                                self.yield_action = generator
                        
                    else:
                        match action:
                            case ItemAction.Buy_From_Merchant:
                                Merchant.Trading.Merchant.BuyItem(item.id, item.quantity * item.value)
                        
    def get_generator_for_action(self, item_id: int, action: ItemAction) -> Optional[Generator]:
        # This function should return a generator for the given action
        # For example, if the action is Salvage, it would return a generator that performs the salvage action on the item
        # You would need to implement the actual logic for each action type here
        
        match action:
            case ItemAction.Sell_To_Trader:
                yield
                
            case ItemAction.Buy_From_Trader:
                yield
                
            case _:
                return None