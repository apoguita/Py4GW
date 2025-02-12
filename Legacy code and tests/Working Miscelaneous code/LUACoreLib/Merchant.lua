local Trading = {}

function Trading.merchant_instance()
    return PyMerchant.PyMerchant()
end

function Trading.IsTransactionComplete()
    return Trading.merchant_instance():is_transaction_complete()
end

Trading.Trader = {}
function Trading.Trader.GetQuotedItemID()
    return Trading.merchant_instance():get_quoted_item_id()
end

function Trading.Trader.GetQuotedValue()
    return Trading.merchant_instance():get_quoted_value()
end

function Trading.Trader.GetOfferedItems()
    return Trading.merchant_instance():get_trader_item_list()
end

function Trading.Trader.GetOfferedItems2()
    return Trading.merchant_instance():get_trader_item_list2()
end

function Trading.Trader.RequestQuote(item_id)
    Trading.merchant_instance():trader_request_quote(item_id)
end

function Trading.Trader.RequestSellQuote(item_id)
    Trading.merchant_instance():trader_request_sell_quote(item_id)
end

function Trading.Trader.BuyItem(item_id, cost)
    Trading.merchant_instance():trader_buy_item(item_id, cost)
end

function Trading.Trader.SellItem(item_id, cost)
    Trading.merchant_instance():trader_sell_item(item_id, cost)
end

Trading.Merchant = {}
function Trading.Merchant.BuyItem(item_id, cost)
    Trading.merchant_instance():merchant_buy_item(item_id, cost)
end

function Trading.Merchant.SellItem(item_id, cost)
    Trading.merchant_instance():merchant_sell_item(item_id, cost)
end

function Trading.Merchant.GetOfferedItems()
    return Trading.merchant_instance():get_merchant_item_list()
end

Trading.Crafter = {}
function Trading.Crafter.CraftItem(item_id, cost, item_list, item_quantities)
    Trading.merchant_instance():crafter_buy_item(item_id, cost, item_list, item_quantities)
end

function Trading.Crafter.GetOfferedItems()
    return Trading.merchant_instance():get_merchant_item_list()
end

Trading.Collector = {}
function Trading.Collector.ExghangeItem(item_id, item_list, item_quantities)
    Trading.merchant_instance():collector_exchange_item(item_id, 0, item_list, item_quantities)
end

function Trading.Collector.GetOfferedItems()
    return Trading.merchant_instance():get_merchant_item_list()
end

return Trading
