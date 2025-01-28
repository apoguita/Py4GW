import PyMerchant

class Trading:
    @staticmethod
    def merchant_instance():
        """
        Purpose: Create an instance of an Merchant Object
        Args:
            None
        Returns: PyMerchant
        """
        return PyMerchant.PyMerchant()

    @staticmethod
    def IsTransactionComplete():
        """
        Purpose: Check if the transaction is complete.
        Args:
            None
        Returns: bool
        """
        return Trading.merchant_instance().is_transaction_complete()

    class Trader:
        @staticmethod
        def GetQuotedItemID():
            """
            Purpose: Retrieve the quoted item ID from the merchant.
            Args:
                None
            Returns: int
            """
            return Trading.merchant_instance().get_quoted_item_id()

        @staticmethod
        def GetQuotedValue():
            """
            Purpose: Retrieve the quoted value from the merchant.
            Args:
                None
            Returns: int
            """
            return Trading.merchant_instance().get_quoted_value()
            
        @staticmethod
        def GetOfferedItems():
            """
            Purpose: Retrieve the offered items from the Trader.
            Args:
                None
            Returns: list[int]
            """
            return Trading.merchant_instance().get_trader_item_list()

        @staticmethod
        def GetOfferedItems2():
            """
            Purpose: Retrieve the offered items from the Trader.
            Args:
                None
            Returns: list[int]
            """
            return Trading.merchant_instance().get_trader_item_list2()

        @staticmethod
        def RequestQuote(item_id):
            """
            Purpose: Request a quote from the merchant.
            Args:
                item_id (int): The item ID to request a quote for.
            Returns: None
            """
            Trading.merchant_instance().trader_request_quote(item_id)

        @staticmethod
        def RequestSellQuote(item_id):
            """
            Purpose: Request a sell quote from the merchant.
            Args:
                item_id (int): The item ID to request a sell quote for.
            Returns: None
            """
            Trading.merchant_instance().trader_request_sell_quote(item_id)

        @staticmethod
        def BuyItem(item_id, cost):
            """
            Purpose: Buy an item from the merchant.
            Args:
                item_id (int): The item ID to buy.
                cost (int): The cost of the item.
                quantity (int): The quantity of the item.
            Returns: None
            """
            Trading.merchant_instance().trader_buy_item(item_id, cost)

        @staticmethod
        def SellItem(item_id, cost):
            """
            Purpose: Sell an item to the merchant.
            Args:
                item_id (int): The item ID to sell.
                cost (int): The cost of the item.
                quantity (int): The quantity of the item.
            Returns: None
            """
            Trading.merchant_instance().trader_sell_item(item_id, cost)

    class Merchant:
        @staticmethod
        def BuyItem(item_id, cost):
            """
            Purpose: Buy an item from the merchant.
            Args:
                item_id (int): The item ID to buy.
                cost (int): The cost of the item.
                quantity (int): The quantity of the item.
            Returns: None
            """
            Trading.merchant_instance().merchant_buy_item(item_id, cost)

        @staticmethod
        def SellItem(item_id, cost):
            """
            Purpose: Sell an item to the merchant.
            Args:
                item_id (int): The item ID to sell.
                cost (int): The cost of the item.
                quantity (int): The quantity of the item.
            Returns: None
            """
            Trading.merchant_instance().merchant_sell_item(item_id, cost)

        @staticmethod
        def GetOfferedItems():
            """
            Purpose: Retrieve the offered items from the merchant.
            Args:
                None
            Returns: list[int]
            """
            return Trading.merchant_instance().get_merchant_item_list()

    class Crafter:
        @staticmethod
        def CraftItem(item_id, cost, item_list, item_quantities):
            """
            Purpose: Craft an item.
            Args:
                item_id (int): The item ID to craft.
                cost (int): The cost of the item.
                item_list (list[int]): The list of items to craft the item with.
                item_quantities (list[int]): The list of quantities to craft the item with.
            Returns: None
            """
            Trading.merchant_instance().crafter_buy_item(item_id, cost, item_list, item_quantities)

        @staticmethod
        def GetOfferedItems():
            """
            Purpose: Retrieve the offered items from the merchant.
            Args:
                None
            Returns: list[int]
            """
            return Trading.merchant_instance().get_merchant_item_list()

    class Collector:
        @staticmethod
        def ExghangeItem(item_id, item_list, item_quantities):
            """
            Purpose: Exchange an item.
            Args:
                item_id (int): The item ID to exchange.
                item_list (list[int]): The list of items to exchange the item with.
                item_quantities (list[int]): The list of quantities to exchange the item with.
                cost (int): The cost of the item.
            Returns: None
            """
            Trading.merchant_instance().collector_exchange_item(item_id, 0,  item_list, item_quantities)

        @staticmethod
        def GetOfferedItems():
            """
            Purpose: Retrieve the offered items from the merchant.
            Args:
                None
            Returns: list[int]
            """
            return Trading.merchant_instance().get_merchant_item_list()
