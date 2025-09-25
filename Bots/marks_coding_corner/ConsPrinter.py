from Py4GWCoreLib import GLOBAL_CACHE
from Py4GWCoreLib import Bags
from Py4GWCoreLib import Botting
from Py4GWCoreLib import Item
from Py4GWCoreLib import ItemArray
from Py4GWCoreLib import ModelID
from Py4GWCoreLib import Py4GW
from Py4GWCoreLib import Routines
from Py4GWCoreLib import Trading
from Py4GWCoreLib import ConsoleLog

selected_step = 0
EMBARK_BEACH = "Embark Beach"
MODULE_NAME = 'Cons Printing'


bot = Botting(MODULE_NAME)


def move_all_crafting_materials_to_storage():
    COMMON_FARMED_CRAFTING_MATERIALS = [
        ModelID.Wood_Plank,
        ModelID.Scale,
        ModelID.Tanned_Hide_Square,
        ModelID.Bolt_Of_Cloth,
        ModelID.Granite_Slab,
        ModelID.Bone,
        ModelID.Iron_Ingot,
        ModelID.Pile_Of_Glittering_Dust,
        ModelID.Feather,
    ]
    bag_list = ItemArray.CreateBagList(Bags.Backpack, Bags.BeltPouch, Bags.Bag1, Bags.Bag2)
    all_items = ItemArray.GetItemArray(bag_list)
    # Store remaining non-sold sellables
    item_ids_to_store = []
    for item_id in all_items:
        if GLOBAL_CACHE.Item.GetModelID(item_id) in COMMON_FARMED_CRAFTING_MATERIALS:
            item_ids_to_store.append(item_id)

    for item_id in item_ids_to_store:
        GLOBAL_CACHE.Inventory.DepositItemToStorage(item_id)
        yield from Routines.Yield.wait(250)


def sell_non_cons_material_from_inventory():
    MAX_WITHDRAW_ATTEMPTS = 20
    REQUIRED_QUANTITY = 10
    SELLABLE_CRAFTING_MATERIALS_MODEL_ID = [
        ModelID.Wood_Plank,
        ModelID.Scale,
        ModelID.Tanned_Hide_Square,
        ModelID.Bolt_Of_Cloth,
        ModelID.Granite_Slab,
        ModelID.Chitin_Fragment,
    ]
    for model_id in SELLABLE_CRAFTING_MATERIALS_MODEL_ID:
        attempts = 0
        while GLOBAL_CACHE.Inventory.GetModelCountInStorage(model_id) and attempts < MAX_WITHDRAW_ATTEMPTS:
            attempts += 1
            GLOBAL_CACHE.Inventory.WithdrawItemFromStorageByModelID(model_id)
            yield from Routines.Yield.wait(250)

    bag_list = ItemArray.CreateBagList(Bags.Backpack, Bags.BeltPouch, Bags.Bag1, Bags.Bag2)
    all_items = ItemArray.GetItemArray(bag_list)
    item_ids_to_sell = []

    for item_id in all_items:
        if GLOBAL_CACHE.Item.GetModelID(item_id) in SELLABLE_CRAFTING_MATERIALS_MODEL_ID:
            item_ids_to_sell.append(item_id)

    for item_id in item_ids_to_sell:
        while True:
            item_array = ItemArray.GetItemArray(bag_list)
            if item_id not in item_array:
                break

            quantity = Item.Properties.GetQuantity(item_id)
            if quantity < REQUIRED_QUANTITY:
                break

            # Request quote
            GLOBAL_CACHE.Trading.Trader.RequestSellQuote(item_id)
            while True:
                yield from Routines.Yield.wait(50)
                quoted_value = Trading.Trader.GetQuotedValue()
                if quoted_value >= 0:
                    break

            if quoted_value == 0:
                break

            # Proceed with sale
            GLOBAL_CACHE.Trading.Trader.SellItem(item_id, quoted_value)

            # Wait for confirmation
            while True:
                yield from Routines.Yield.wait(50)
                if Trading.IsTransactionComplete():
                    break

    # Store remaining non-sold sellables
    item_ids_to_store = []
    for item_id in all_items:
        if GLOBAL_CACHE.Item.GetModelID(item_id) in SELLABLE_CRAFTING_MATERIALS_MODEL_ID:
            item_ids_to_store.append(item_id)

    for item_id in item_ids_to_store:
        GLOBAL_CACHE.Inventory.DepositItemToStorage(item_id)
        yield from Routines.Yield.wait(250)


def withdraw_cons_materials_from_inventory():
    global consets_to_make

    consets_to_make = 0
    PER_CONSET = {
        ModelID.Iron_Ingot: 100,
        ModelID.Pile_Of_Glittering_Dust: 100,
        ModelID.Bone: 50,
        ModelID.Feather: 50,
    }
    GOLD_PER_CONSET = 750

    # Step 1: Check how many we can craft
    max_possible = 99999  # unrealistically high number
    for model_id, req_amount in PER_CONSET.items():
        available = GLOBAL_CACHE.Inventory.GetModelCountInStorage(model_id)
        possible = available // req_amount
        max_possible = min(max_possible, possible)

    gold_available = GLOBAL_CACHE.Inventory.GetGoldInStorage() + GLOBAL_CACHE.Inventory.GetGoldOnCharacter()
    possible_gold = gold_available // GOLD_PER_CONSET
    max_possible = min(max_possible, possible_gold)

    if max_possible <= 0:
        ConsoleLog("Conset Withdraw", "Not enough materials to craft any consets.")
        return

    # Step 2: Withdraw materials
    for model_id, req_amount in PER_CONSET.items():
        total_needed = req_amount * max_possible
        withdrawn = 0
        while withdrawn < total_needed:
            withdraw_amount = min(250, total_needed - withdrawn)
            GLOBAL_CACHE.Inventory.WithdrawItemFromStorageByModelID(model_id, withdraw_amount)
            withdrawn += withdraw_amount
            yield from Routines.Yield.wait(250)

    # Step 3: Withdraw gold
    needed_gold = GOLD_PER_CONSET * max_possible
    gold_on_char = GLOBAL_CACHE.Inventory.GetGoldOnCharacter()

    if gold_on_char < needed_gold:
        to_withdraw = needed_gold - gold_on_char
        GLOBAL_CACHE.Inventory.WithdrawGold(to_withdraw)
        yield from Routines.Yield.wait(250)

    consets_to_make = max_possible
    ConsoleLog("Conset Withdraw", f"Withdrew materials and {needed_gold}g for {max_possible} consets.")


def craft_item(target_model_id, required_mats, per_craft_mats, crafts=5):
    # Check if we have mats in bags
    for model_id, required_qty in required_mats.items():
        qty = GLOBAL_CACHE.Inventory.GetModelCount(model_id)
        if qty < required_qty:
            Py4GW.Console.Log(
                MODULE_NAME,
                f"Not enough {model_id} to craft {crafts}x {target_model_id}. "
                f"Required: {required_qty}, Found: {qty}",
                Py4GW.Console.MessageType.Error,
            )
            return

    yield from Routines.Yield.wait(500)

    # === Find target item in crafter’s merchant list ===
    merchant_item_list = GLOBAL_CACHE.Trading.Merchant.GetOfferedItems()
    for item_id in merchant_item_list:
        if GLOBAL_CACHE.Item.GetModelID(item_id) == target_model_id:

            # Craft N times
            for _ in range(crafts):
                trade_item_list = []
                quantity_list = []
                for mat_id, per_craft_qty in per_craft_mats.items():
                    item_ref = GLOBAL_CACHE.Inventory.GetFirstModelID(mat_id)
                    if not item_ref:
                        Py4GW.Console.Log(
                            MODULE_NAME,
                            f"Required item {mat_id} not found in bags.",
                            Py4GW.Console.MessageType.Error,
                        )
                        return
                    trade_item_list.append(item_ref)
                    quantity_list.append(per_craft_qty)

                GLOBAL_CACHE.Trading.Crafter.CraftItem(item_id, 250, trade_item_list, quantity_list)
                yield from Routines.Yield.wait(1000)
            break


def craft_armor_of_salvation():
    global consets_to_make
    REQUIRED_MATS = {
        ModelID.Iron_Ingot: 50 * consets_to_make,  # enough for 5 crafts
        ModelID.Bone: 50 * consets_to_make,
    }
    PER_CRAFT = {
        ModelID.Iron_Ingot: 50,
        ModelID.Bone: 50,
    }
    yield from craft_item(ModelID.Armor_Of_Salvation, REQUIRED_MATS, PER_CRAFT, crafts=consets_to_make)


def craft_essence_of_celerity():
    global consets_to_make
    REQUIRED_MATS = {
        ModelID.Feather: 50 * consets_to_make,  # enough for 5 crafts
        ModelID.Pile_Of_Glittering_Dust: 50 * consets_to_make,
    }
    PER_CRAFT = {
        ModelID.Feather: 50,
        ModelID.Pile_Of_Glittering_Dust: 50,
    }
    yield from craft_item(ModelID.Essence_Of_Celerity, REQUIRED_MATS, PER_CRAFT, crafts=consets_to_make)


def craft_grail_of_might():
    global consets_to_make
    REQUIRED_MATS = {
        ModelID.Iron_Ingot: 50 * consets_to_make,  # enough for 5 crafts
        ModelID.Pile_Of_Glittering_Dust: 50 * consets_to_make,
    }
    PER_CRAFT = {
        ModelID.Iron_Ingot: 50,
        ModelID.Pile_Of_Glittering_Dust: 50,
    }
    yield from craft_item(ModelID.Grail_Of_Might, REQUIRED_MATS, PER_CRAFT, crafts=consets_to_make)


def move_all_cons_to_storage():
    CONS = [
        ModelID.Armor_Of_Salvation,
        ModelID.Essence_Of_Celerity,
        ModelID.Grail_Of_Might,
    ]
    bag_list = ItemArray.CreateBagList(Bags.Backpack, Bags.BeltPouch, Bags.Bag1, Bags.Bag2)
    all_items = ItemArray.GetItemArray(bag_list)
    # Store remaining non-sold sellables
    item_ids_to_store = []
    for item_id in all_items:
        if GLOBAL_CACHE.Item.GetModelID(item_id) in CONS:
            item_ids_to_store.append(item_id)

    for item_id in item_ids_to_store:
        GLOBAL_CACHE.Inventory.DepositItemToStorage(item_id)
        yield from Routines.Yield.wait(250)


def main_bot(bot: Botting) -> None:
    map_id = GLOBAL_CACHE.Map.GetMapID()
    if map_id != 640:
        bot.Map.Travel(target_map_name=EMBARK_BEACH)
        bot.Wait.ForMapLoad(target_map_name=EMBARK_BEACH)
    bot.States.AddCustomState(move_all_crafting_materials_to_storage, 'Attempt to move all common mats')
    bot.Move.XY(2925.52, -2258.74, "Go to Material Trader")
    bot.Interact.WithNpcAtXY(2997.00, -2271.00, "Interact with Material Trader")
    bot.States.AddCustomState(sell_non_cons_material_from_inventory, 'Sell Non-Cons Mats')

    bot.Move.XY(3254.94, 167.96, "Go to Consumables NPCs")
    bot.States.AddCustomState(withdraw_cons_materials_from_inventory, 'Take items needed for cons')
    bot.Interact.WithNpcAtXY(3743.00, -106.00, 'Talk to the dwarf')
    bot.States.AddCustomState(craft_armor_of_salvation, 'Make 5 Armors of Salvation')
    bot.Interact.WithNpcAtXY(3666.00, 90.00, 'Make 5 Essences of Celerity')
    bot.States.AddCustomState(craft_essence_of_celerity, 'Make 5 Armors of Salvation')
    bot.Interact.WithNpcAtXY(3414.00, 644.00, 'Make 5 Grails of Might')
    bot.States.AddCustomState(craft_grail_of_might, 'Make 5 Armors of Salvation')
    bot.States.AddCustomState(move_all_cons_to_storage, 'Move cons to storage')
    bot.States.AddCustomState(move_all_crafting_materials_to_storage, 'Attempt to move all common mats')


bot.SetMainRoutine(main_bot)


def main():
    bot.Update()
    bot.UI.draw_window(icon_path="cof_art.png")


if __name__ == "__main__":
    main()
