from Py4GWCoreLib import GLOBAL_CACHE
from Py4GWCoreLib import Bags
from Py4GWCoreLib import ItemArray
from Py4GWCoreLib import ModelID
from Py4GWCoreLib import Routines


def sell_non_essential_mats():
    MERCHABLE_CRAFTING_MATERIALS_MODEL_ID = [
        ModelID.Wood_Plank,
        ModelID.Scale,
        ModelID.Tanned_Hide_Square,
        ModelID.Bolt_Of_Cloth,
        ModelID.Granite_Slab,
        ModelID.Chitin_Fragment,
    ]
    bag_list = ItemArray.CreateBagList(Bags.Backpack, Bags.BeltPouch, Bags.Bag1, Bags.Bag2)
    all_items = ItemArray.GetItemArray(bag_list)
    item_ids_to_sell = []

    for item_id in all_items:
        if GLOBAL_CACHE.Item.GetModelID(item_id) in MERCHABLE_CRAFTING_MATERIALS_MODEL_ID:
            item_ids_to_sell.append(item_id)

    yield from Routines.Yield.Merchant.SellItems(item_ids_to_sell)


def buy_id_kits(custom_amount=1):
    yield from Routines.Yield.wait(1500)
    kits_in_inv = GLOBAL_CACHE.Inventory.GetModelCount(ModelID.Identification_Kit)
    sup_kits_in_inv = GLOBAL_CACHE.Inventory.GetModelCount(ModelID.Superior_Identification_Kit)
    if (kits_in_inv + sup_kits_in_inv) < custom_amount:
        kits_needed = (kits_in_inv + sup_kits_in_inv) - custom_amount
        yield from Routines.Yield.Merchant.BuyIDKits(kits_needed)


def buy_salvage_kits(custom_amount=10):
    yield from Routines.Yield.wait(1500)
    kits_in_inv = GLOBAL_CACHE.Inventory.GetModelCount(ModelID.Salvage_Kit)
    if kits_in_inv < custom_amount:
        kits_needed = custom_amount - kits_in_inv
        yield from Routines.Yield.Merchant.BuySalvageKits(kits_needed)


def withdraw_gold(target_gold=10000, deposit_all=True):
    gold_on_char = GLOBAL_CACHE.Inventory.GetGoldOnCharacter()

    if gold_on_char > target_gold and deposit_all:
        to_deposit = gold_on_char - target_gold
        GLOBAL_CACHE.Inventory.DepositGold(to_deposit)
        yield from Routines.Yield.wait(250)

    if gold_on_char < target_gold:
        to_withdraw = target_gold - gold_on_char
        GLOBAL_CACHE.Inventory.WithdrawGold(to_withdraw)
        yield from Routines.Yield.wait(250)
