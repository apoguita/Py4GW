import PyMerchant
from Py4GWCoreLib.Py4GWcorelib import ActionQueueManager

class TradingCache:
    def __init__(self, action_queue_manager):
        self._action_queue_manager:ActionQueueManager = action_queue_manager
        self._merchant_instance = PyMerchant.PyMerchant()
        self.Trader = self._Trader(self)
        self.Merchant = self._Merchant(self)
        self.Crafter = self._Crafter(self)
        self.Collector = self._Collector(self)

    def IsTransactionComplete(self):
        return self._merchant_instance.is_transaction_complete()
    
    class _Trader:
        def __init__(self, parent):
            self._parent = parent
            
        def GetQuotedItemID(self):
            return self._parent._merchant_instance.get_quoted_item_id()
        
        def GetQuotedValue(self):
            return self._parent._merchant_instance.get_quoted_value()
        
        def GetOfferedItems(self):
            return self._parent._merchant_instance.get_trader_item_list()
        
        def GetOfferedItems2(self):
            return self._parent._merchant_instance.get_trader_item_list2()
        
        def RequestQuote(self, item_id):
            self._parent._action_queue_manager.AddAction("ACTION", self._parent._merchant_instance.trader_request_quote,item_id)
            
        def RequestSellQuote(self, item_id):
            self._parent._action_queue_manager.AddAction("ACTION", self._parent._merchant_instance.trader_request_sell_quote,item_id)
            
        def BuyItem(self, item_id, cost):
            self._parent._action_queue_manager.AddAction("ACTION", self._parent._merchant_instance.trader_buy_item,item_id, cost)
        
        def SellItem(self, item_id, cost):
            self._parent._action_queue_manager.AddAction("ACTION", self._parent._merchant_instance.trader_sell_item,item_id, cost)   
            
    class _Merchant:
        def __init__(self, parent):
            self._parent = parent
            
        def BuyItem(self, item_id, cost):
            self._parent._action_queue_manager.AddAction("ACTION", self._parent._merchant_instance.merchant_buy_item,item_id, cost)
            
        def SellItem(self, item_id, cost):
            self._parent._action_queue_manager.AddAction("ACTION", self._parent._merchant_instance.merchant_sell_item,item_id, cost)    
            
        def GetOfferedItems(self):
            return self._parent._merchant_instance.get_merchant_item_list()    
            
    class _Crafter:
        def __init__(self, parent):
            self._parent = parent
            
        def CraftItem(self,item_id, cost, item_list, item_quantities):
            self._parent._action_queue_manager.AddAction("ACTION", self._parent._merchant_instance.crafter_buy_item,item_id, cost, item_list, item_quantities)
            
        def GetOfferedItems(self):
            return self._parent._merchant_instance.get_merchant_item_list()   
            
    class _Collector:
        def __init__(self, parent):
            self._parent = parent
            
        def ExghangeItem(self, item_id, cost =0, item_list=[], item_quantities=[]):
            self._parent._action_queue_manager.AddAction("ACTION", self._parent._merchant_instance.collector_buy_item,item_id, cost, item_list, item_quantities)
            
        def GetOfferedItems(self):
            return self._parent._merchant_instance.get_merchant_item_list()
            
            