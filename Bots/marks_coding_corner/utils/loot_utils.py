from Py4GWCoreLib import GLOBAL_CACHE
from Py4GWCoreLib import Agent
from Py4GWCoreLib import AgentArray
from Py4GWCoreLib import AutoInventoryHandler
from Py4GWCoreLib import Bags
from Py4GWCoreLib import Item
from Py4GWCoreLib import ItemArray
from Py4GWCoreLib import ModelID
from Py4GWCoreLib import Player
from Py4GWCoreLib import Range
from Py4GWCoreLib import Routines


AUTOLOOT_SECTION = "AutoLootOptions"
VIABLE_LOOT = {
    # Coin
    ModelID.Gold_Coins,
    # Materials
    ModelID.Bone,
    ModelID.Plant_Fiber,
    ModelID.Pile_Of_Glittering_Dust,
    ModelID.Feather,
    # Materials from Farms
    ModelID.Abnormal_Seed,
    ModelID.Feathered_Crest,
    ModelID.Shadowy_Remnants,
    # Alcohol Pts
    ModelID.Bottle_Of_Rice_Wine,
    ModelID.Bottle_Of_Vabbian_Wine,
    ModelID.Dwarven_Ale,
    ModelID.Eggnog,
    # ModelID.Hard_Apple_Cider,
    ModelID.Hunters_Ale,
    ModelID.Shamrock_Ale,
    ModelID.Witchs_Brew,
    ModelID.Zehtukas_Jug,
    ModelID.Aged_Dwarven_Ale,
    ModelID.Bottle_Of_Grog,
    ModelID.Krytan_Brandy,
    ModelID.Spiked_Eggnog,
    # Dye
    ModelID.Vial_Of_Dye,
    # Commonish Rare Materials
    ModelID.Monstrous_Claw,
    ModelID.Monstrous_Eye,
    # Lockpick
    ModelID.Lockpick,
    # Halloween
    ModelID.Candy_Apple,
    ModelID.Pumpkin_Cookie,
    ModelID.Candy_Corn,
    ModelID.Squash_Serum,
    ModelID.Trick_Or_Treat_Bag,
    ModelID.Vial_Of_Absinthe,
    ModelID.Witchs_Brew,
    # Sweet Treat
    ModelID.Slice_Of_Pumpkin_Pie,
    ModelID.Candy_Cane_Shard,
    ModelID.Fruitcake,
    ModelID.Snowman_Summoner,
    ModelID.Frosty_Tonic
}


def is_valid_item(item_id):
    if not Agent.IsValid(item_id):
        return False
    player_agent_id = Player.GetAgentID()
    owner_id = Agent.GetItemAgentOwnerID(item_id)
    if (owner_id == player_agent_id) or (owner_id == 0):
        return True
    return False


def get_valid_loot_array(viable_loot=VIABLE_LOOT, loot_salvagables=False):
    loot_array = AgentArray.GetItemArray()
    loot_array = AgentArray.Filter.ByDistance(loot_array, Player.GetXY(), Range.Spellcast.value * 3.00)

    agent_array = AgentArray.GetItemArray()

    item_array_model = AgentArray.Filter.ByCondition(
        agent_array, lambda agent_id: Item.GetModelID(Agent.GetItemAgentItemID(agent_id)) in viable_loot
    )

    item_array_salv = []
    if loot_salvagables:
        item_array_salv = AgentArray.Filter.ByCondition(
            agent_array, lambda agent_id: Item.Usage.IsSalvageable(Agent.GetItemAgentItemID(agent_id))
        )

    item_array = list(set(item_array_model + item_array_salv))
    item_array = AgentArray.Sort.ByDistance(item_array, Player.GetXY())

    # return item_array
    filtered_agent_ids = []
    for agent_id in loot_array[:]:  # Iterate over a copy to avoid modifying while iterating
        item_id = Agent.GetItemAgentItemID(agent_id)
        item_id = item_id
        model_id = Item.GetModelID(item_id)
        if model_id in viable_loot and is_valid_item(agent_id):
            # Black and White Dyes
            if (
                model_id == ModelID.Vial_Of_Dye
                and (GLOBAL_CACHE.Item.GetDyeColor(item_id) == 10 or GLOBAL_CACHE.Item.GetDyeColor(item_id) == 12)
                or model_id != ModelID.Vial_Of_Dye
            ):
                filtered_agent_ids.append(agent_id)
    return list(set(filtered_agent_ids + item_array_salv))


def identify_and_salvage_items():
    yield from Routines.Yield.wait(1500)
    yield from AutoInventoryHandler().IDAndSalvageItems()


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


def set_autoloot_options_for_custom_bots(salvage_golds=False, module_active=False):
    ''' We use autohandler for most of the bots, this sets the autoloot ini to correspond to correct bot'''
    return


    auto_inventory_handler = AutoInventoryHandler()
    ini = auto_inventory_handler.ini

    # === Module State ===
    ini.write_key(AUTOLOOT_SECTION, "module_active", "True" if module_active else "False")

    # === Salvage Settings ===
    SALVAGE_DEFAULTS = {
        "salvage_whites": "True",
        "salvage_rare_materials": "False",
        "salvage_blues": "True",
        "salvage_purples": "True",
        "salvage_golds": "True" if salvage_golds else "False",
    }
    for key, value in SALVAGE_DEFAULTS.items():
        ini.write_key(AUTOLOOT_SECTION, key, value)

    # === Identification Settings ===
    ID_DEFAULTS = {
        "id_whites": "True",
        "id_blues": "True",
        "id_purples": "True",
        "id_golds": "True",
        "id_greens": "False",
    }
    for key, value in ID_DEFAULTS.items():
        ini.write_key(AUTOLOOT_SECTION, key, value)

    # === Deposit Settings ===
    DEPOSIT_DEFAULTS = {
        "deposit_trophies": "False",
        "deposit_materials": "False",
        "deposit_dyes": "False",
        "deposit_golds": "True" if not salvage_golds else "False",
        "deposit_greens": "True",
        "keep_gold": "10000",
    }
    for key, value in DEPOSIT_DEFAULTS.items():
        ini.write_key(AUTOLOOT_SECTION, key, value)

    ini.write_key(AUTOLOOT_SECTION, "salvage_blacklist", "31202,31203,31204")  # remove glacial stones
    auto_inventory_handler.load_from_ini(ini, AUTOLOOT_SECTION)
