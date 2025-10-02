import os

from Bots.marks_coding_corner.utils.loot_utils import move_all_crafting_materials_to_storage
from Py4GWCoreLib import GLOBAL_CACHE
from Py4GWCoreLib import Bags
from Py4GWCoreLib import Botting
from Py4GWCoreLib import ConsoleLog
from Py4GWCoreLib import Item
from Py4GWCoreLib import ItemArray
from Py4GWCoreLib import ModelID
from Py4GWCoreLib import Py4GW
from Py4GWCoreLib import PyImGui
from Py4GWCoreLib import Routines
from Py4GWCoreLib import Trading

try:
    script_directory = os.path.dirname(os.path.abspath(__file__))
except NameError:
    # __file__ is not defined (e.g. running in interactive mode or embedded interpreter)
    script_directory = os.getcwd()
project_root = os.path.abspath(os.path.join(script_directory, os.pardir))
base_dir = os.path.join(project_root, "marks_coding_corner/textures")

selected_step = 0
EMBARK_BEACH = "Embark Beach"
MODULE_NAME = 'Cons Printing'
SELLABLE_CRAFTING_MATERIALS_MODEL_ID = [
    ModelID.Scale,
    ModelID.Granite_Slab,
]
MERCHABLE_CRAFTING_MATERIALS_MODEL_ID = [
    ModelID.Wood_Plank,
    ModelID.Scale,
    ModelID.Tanned_Hide_Square,
    ModelID.Bolt_Of_Cloth,
    ModelID.Granite_Slab,
    ModelID.Chitin_Fragment,
]
PER_CONSET = {
    ModelID.Iron_Ingot: 100,
    ModelID.Pile_Of_Glittering_Dust: 100,
    ModelID.Bone: 50,
    ModelID.Feather: 50,
}
GOLD_PER_CONSET = 750
TEXTURE_ICON_PATH = os.path.join(base_dir, "conset_printer.png")


bot = Botting(MODULE_NAME)


def sell_non_cons_material_from_inventory():
    MAX_WITHDRAW_ATTEMPTS = 20
    REQUIRED_QUANTITY = 10
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
    BUFFER_SLOTS = 4
    MIN_REQUIRED_SLOTS = len(PER_CONSET) + BUFFER_SLOTS  # 4 mats + 4 buffer = 8

    # Step 0: Check inventory space
    free_slots = GLOBAL_CACHE.Inventory.GetFreeSlotCount()
    if free_slots < MIN_REQUIRED_SLOTS:
        ConsoleLog("Conset Withdraw", f"Not enough free slots ({free_slots}), need at least {MIN_REQUIRED_SLOTS}.")
        return

    # Step 1: Check how many we can craft based on materials
    max_possible = 9999
    for model_id, req_amount in PER_CONSET.items():
        available = GLOBAL_CACHE.Inventory.GetModelCountInStorage(model_id)
        possible = available // req_amount
        max_possible = min(max_possible, possible)

    # Step 2: Check gold availability
    gold_available = GLOBAL_CACHE.Inventory.GetGoldInStorage() + GLOBAL_CACHE.Inventory.GetGoldOnCharacter()
    possible_gold = gold_available // GOLD_PER_CONSET
    max_possible = min(max_possible, possible_gold)

    # Step 3: Check skill points availability
    current_skill_points, _ = GLOBAL_CACHE.Player.GetSkillPointData()
    possible_skillpoints = current_skill_points // 3
    max_possible = min(max_possible, possible_skillpoints)

    # Step 4: Cap to what can actually fit in slots
    def can_fit(conset_count):
        slots_needed = 0
        for model_id, req_amount in PER_CONSET.items():
            total_needed = req_amount * conset_count
            already_have = GLOBAL_CACHE.Inventory.GetModelCount(model_id)
            # Remaining items after filling existing stack(s)
            remaining = max(0, total_needed - already_have)
            # Each slot holds up to 250
            slots_needed += (remaining + 249) // 250
        return slots_needed + BUFFER_SLOTS <= free_slots

    # Reduce max_possible if inventory can't fit
    while max_possible > 0 and not can_fit(max_possible):
        max_possible -= 1

    if max_possible <= 0:
        ConsoleLog("Conset Withdraw", "Not enough space/materials/skill points to craft any consets.")
        return

    # Step 5: Withdraw materials
    for model_id, req_amount in PER_CONSET.items():
        total_needed = req_amount * max_possible
        already_have = GLOBAL_CACHE.Inventory.GetModelCount(model_id)
        target_amount = already_have + total_needed

        while GLOBAL_CACHE.Inventory.GetModelCount(model_id) < target_amount:
            remaining = target_amount - GLOBAL_CACHE.Inventory.GetModelCount(model_id)
            withdraw_amount = min(250, remaining)

            GLOBAL_CACHE.Inventory.WithdrawItemFromStorageByModelID(model_id, withdraw_amount)
            yield from Routines.Yield.wait(250)

        ConsoleLog("Withdraw", f"Got {total_needed} {model_id} for consets.")

    # Step 6: Withdraw gold
    needed_gold = GOLD_PER_CONSET * max_possible
    gold_on_char = GLOBAL_CACHE.Inventory.GetGoldOnCharacter()

    if gold_on_char < needed_gold:
        to_withdraw = needed_gold - gold_on_char
        GLOBAL_CACHE.Inventory.WithdrawGold(to_withdraw)
        yield from Routines.Yield.wait(250)

    consets_to_make = max_possible
    ConsoleLog(
        "Conset Withdraw",
        f"Withdrew materials, {needed_gold}g, and reserved {max_possible * 3} skill points for {max_possible} consets.",
    )


def can_make_at_least_one_conset_from_storage():
    # Check mats
    for model_id, req_amount in PER_CONSET.items():
        available = GLOBAL_CACHE.Inventory.GetModelCountInStorage(model_id)
        if available < req_amount:
            return False

    # Check gold
    gold_available = GLOBAL_CACHE.Inventory.GetGoldInStorage()
    if gold_available < GOLD_PER_CONSET:
        return False

    return True


def merch_non_cons_material_from_inventory():
    MAX_WITHDRAW_ATTEMPTS = 20
    for model_id in MERCHABLE_CRAFTING_MATERIALS_MODEL_ID:
        attempts = 0
        while GLOBAL_CACHE.Inventory.GetModelCountInStorage(model_id) and attempts < MAX_WITHDRAW_ATTEMPTS:
            attempts += 1
            GLOBAL_CACHE.Inventory.WithdrawItemFromStorageByModelID(model_id)
            yield from Routines.Yield.wait(250)

    bag_list = ItemArray.CreateBagList(Bags.Backpack, Bags.BeltPouch, Bags.Bag1, Bags.Bag2)
    all_items = ItemArray.GetItemArray(bag_list)
    item_ids_to_sell = []

    for item_id in all_items:
        if GLOBAL_CACHE.Item.GetModelID(item_id) in MERCHABLE_CRAFTING_MATERIALS_MODEL_ID:
            item_ids_to_sell.append(item_id)

    yield from Routines.Yield.Merchant.SellItems(item_ids_to_sell)

    # Store remaining non-sold sellables
    item_ids_to_store = []
    for item_id in all_items:
        if GLOBAL_CACHE.Item.GetModelID(item_id) in MERCHABLE_CRAFTING_MATERIALS_MODEL_ID:
            item_ids_to_store.append(item_id)

    for item_id in item_ids_to_store:
        GLOBAL_CACHE.Inventory.DepositItemToStorage(item_id)
        yield from Routines.Yield.wait(250)


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
                    total_collected = 0
                    item_refs = GLOBAL_CACHE.Inventory.GetAllItemIdsByModelID(mat_id)
                    if not item_refs:
                        Py4GW.Console.Log(
                            MODULE_NAME,
                            f"Required item {mat_id} not found in bags.",
                            Py4GW.Console.MessageType.Error,
                        )
                        return

                    for item_ref in item_refs:
                        if total_collected >= per_craft_qty:
                            break

                        stack_qty = GLOBAL_CACHE.Inventory.GetItemCount(item_ref)
                        take_qty = min(stack_qty, per_craft_qty - total_collected)

                        trade_item_list.append(item_ref)
                        quantity_list.append(take_qty)

                        total_collected += take_qty

                    if total_collected < per_craft_qty:
                        Py4GW.Console.Log(
                            MODULE_NAME,
                            f"Not enough {mat_id} for this craft: needed {per_craft_qty}, found {total_collected}.",
                            Py4GW.Console.MessageType.Error,
                        )
                        return

                GLOBAL_CACHE.Trading.Crafter.CraftItem(item_id, 250, trade_item_list, quantity_list)
                yield from Routines.Yield.wait(1000)
            break


def craft_multiple_item_at_once(target_model_id, required_mats, per_craft_mats, crafts=5):
    # === Step 1: Check if we have enough mats in bags ===
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

    # === Step 2: Find target item in crafter’s merchant list ===
    merchant_item_list = GLOBAL_CACHE.Trading.Merchant.GetOfferedItems()
    for item_id in merchant_item_list:
        if GLOBAL_CACHE.Item.GetModelID(item_id) == target_model_id:

            trade_item_list = []
            quantity_list = []

            for mat_model_id, per_craft_qty in per_craft_mats.items():
                total_needed = per_craft_qty * crafts
                total_collected = 0

                item_ids = GLOBAL_CACHE.Inventory.GetAllItemIdsByModelID(mat_model_id)
                for mat_item_id in item_ids:
                    if total_collected >= total_needed:
                        break

                    item_qty = GLOBAL_CACHE.Inventory.GetItemCount(mat_item_id)
                    take_qty = min(item_qty, total_needed - total_collected)

                    trade_item_list.append(mat_item_id)
                    quantity_list.append(take_qty)

                    total_collected += take_qty

                if total_collected < total_needed:
                    Py4GW.Console.Log(
                        MODULE_NAME,
                        f"Missing {mat_model_id}: needed {total_needed}, only found {total_collected}.",
                        Py4GW.Console.MessageType.Error,
                    )
                    return

            # === Step 4: Craft all at once ===
            GLOBAL_CACHE.Trading.Crafter.CraftItem(item_id, 250 * crafts, trade_item_list, quantity_list)
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


def deposit_sellable_crafting_material_items():
    bag_list = ItemArray.CreateBagList(Bags.Backpack, Bags.BeltPouch, Bags.Bag1, Bags.Bag2)
    all_items = ItemArray.GetItemArray(bag_list)
    item_ids_to_sell = []

    for item_id in all_items:
        if GLOBAL_CACHE.Item.GetModelID(item_id) in SELLABLE_CRAFTING_MATERIALS_MODEL_ID:
            item_ids_to_sell.append(item_id)

        # Store remaining non-sold sellables
    item_ids_to_store = []
    for item_id in all_items:
        if GLOBAL_CACHE.Item.GetModelID(item_id) in SELLABLE_CRAFTING_MATERIALS_MODEL_ID:
            item_ids_to_store.append(item_id)

    for item_id in item_ids_to_store:
        GLOBAL_CACHE.Inventory.DepositItemToStorage(item_id)
        yield from Routines.Yield.wait(250)


def check_reset_if_necessary(bot: Botting):
    can_craft = can_make_at_least_one_conset_from_storage()
    if can_craft:
        bot.config.FSM.pause()
        bot.config.FSM.jump_to_state_by_name('[H]Craft Consumables_1')
        bot.config.FSM.resume()
    return


def analyze_conset_material_balance():
    # === Step 1: Consets possible per material ===
    possible_per_mat = {}
    for model_id, req_amount in PER_CONSET.items():
        available = GLOBAL_CACHE.Inventory.GetModelCountInStorage(model_id)
        possible_per_mat[model_id] = available // req_amount

    # === Step 2: Gold constraint ===
    gold_available = GLOBAL_CACHE.Inventory.GetGoldInStorage()
    possible_gold = gold_available // GOLD_PER_CONSET

    # === Step 3: Actual possible = min of all ===
    limiting_consets = min(min(possible_per_mat.values()), possible_gold)

    # === Step 4: Find bottleneck material(s) ===
    bottlenecks = [mid for mid, count in possible_per_mat.items() if count == limiting_consets]

    # === Step 5: Calculate shortages relative to bottleneck ===
    shortages = {}
    for model_id, req_amount in PER_CONSET.items():
        available = GLOBAL_CACHE.Inventory.GetModelCountInStorage(model_id)
        target_amount = req_amount * limiting_consets
        shortages[model_id] = max(0, target_amount - available)

    # === Step 6: Suggest best farm target ===
    farm_costs = {}
    for model_id, req_amount in PER_CONSET.items():
        available = GLOBAL_CACHE.Inventory.GetModelCountInStorage(model_id)
        target_amount = req_amount * (limiting_consets + 1)
        farm_costs[model_id] = max(0, target_amount - available)

    best_to_farm = None
    min_cost = float("inf")
    for model_id, cost in farm_costs.items():
        if cost > 0 and cost < min_cost:
            min_cost = cost
            best_to_farm = model_id

    # === Step 7: Log results ===
    ConsoleLog("Conset Analysis", f"Can make {limiting_consets} consets with current storage and gold.")

    for model_id, possible in possible_per_mat.items():
        name = model_id.name if hasattr(model_id, "name") else str(model_id)
        need = shortages[model_id]
        if model_id in bottlenecks:
            ConsoleLog("Conset Analysis", f"- {name}: {possible} consets (BOTTLENECK)")
        else:
            ConsoleLog("Conset Analysis", f"- {name}: {possible} consets (need +{need} to match bottleneck)")

    ConsoleLog("Conset Analysis", f"- Gold allows for {possible_gold} consets")

    if best_to_farm:
        name = best_to_farm.name if hasattr(best_to_farm, "name") else str(best_to_farm)
        ConsoleLog(
            "Conset Analysis", f"==> Best to farm next: {name} (+{farm_costs[best_to_farm]} needed for 1 more conset)"
        )
    else:
        ConsoleLog("Conset Analysis", "==> No farming needed, all materials balanced with gold.")

    yield


def cons_printer_bot(bot: Botting) -> None:
    map_id = GLOBAL_CACHE.Map.GetMapID()
    if map_id != 640:
        bot.Map.Travel(target_map_name=EMBARK_BEACH)
        bot.Wait.ForMapLoad(target_map_name=EMBARK_BEACH)
    bot.States.AddCustomState(move_all_crafting_materials_to_storage, 'Attempt to move all common mats')
    bot.Move.XY(2925.52, -2258.74, "Go to Material Trader")
    bot.Interact.WithNpcAtXY(2997.00, -2271.00, "Interact with Material Trader")
    bot.States.AddCustomState(sell_non_cons_material_from_inventory, 'Sell Non-Cons Mats')
    bot.Move.XY(2155.87, -1934.52, "Go to Merch")
    bot.Interact.WithNpcAtXY(2158.00, -2006.00, "Interact with the Merch")
    bot.States.AddCustomState(merch_non_cons_material_from_inventory, 'Sell Non-Cons Mats')

    bot.States.AddHeader('Craft Consumables')
    bot.Move.XY(3254.94, 167.96, "Go to Consumables NPCs")
    bot.States.AddCustomState(withdraw_cons_materials_from_inventory, 'Take items needed for cons')
    bot.Interact.WithNpcAtXY(3743.00, -106.00, 'Talk to the dwarf')
    bot.States.AddCustomState(craft_armor_of_salvation, 'Make Armors of Salvation')
    bot.Interact.WithNpcAtXY(3666.00, 90.00, 'Make Essences of Celerity')
    bot.States.AddCustomState(craft_essence_of_celerity, 'Make Essences of Celerity')
    bot.Interact.WithNpcAtXY(3414.00, 644.00, 'Make Grails of Might')
    bot.States.AddCustomState(craft_grail_of_might, 'Make Grails of of Might')
    bot.States.AddCustomState(move_all_cons_to_storage, 'Move cons to storage')
    bot.States.AddCustomState(move_all_crafting_materials_to_storage, 'Attempt to move all common mats')
    bot.States.AddCustomState(lambda: check_reset_if_necessary(bot), 'Attempt to craft more if we can')
    bot.States.AddHeader('Calculate next farm item')
    bot.States.AddCustomState(analyze_conset_material_balance, 'Calculate final need')
    bot.Wait.ForTime(3000)


def additoinal_ui():
    if PyImGui.begin_child("Cons printing machine options"):
        PyImGui.text("Cons Printing Additional Options")
        PyImGui.separator()

        if PyImGui.button("Calculate next farm item"):
            bot.StartAtStep("[H]Calculate next farm item_2")
        PyImGui.end_child()


bot.SetMainRoutine(cons_printer_bot)


def main():
    bot.Update()
    bot.UI.draw_window(main_child_dimensions=(350, 450), icon_path=TEXTURE_ICON_PATH, addtional_ui=additoinal_ui)


if __name__ == "__main__":
    main()
