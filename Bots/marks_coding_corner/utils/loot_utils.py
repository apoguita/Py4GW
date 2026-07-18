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
from Py4GWCoreLib.IniManager import IniManager


INI_PATH = "Inventory/InventoryPlus"  # path to save ini key
INI_FILENAME = "InventoryPlus.ini"  # ini file name
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
    ModelID.Frosty_Tonic,
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
    '''Set autoloot options for custom bots using the InventoryPlus INI'''

    ini_key = ''
    if not ini_key:
        ini_key = IniManager().ensure_key(INI_PATH, INI_FILENAME)
        if not ini_key:
            return

    # === Module State ===
    IniManager().set(key=ini_key, section="AutoManager", var_name="module_active", value=module_active)

    # === Salvage Settings ===
    IniManager().set(key=ini_key, section="AutoSalvage", var_name="salvage_whites", value=True)
    IniManager().set(key=ini_key, section="AutoSalvage", var_name="salvage_rare_materials", value=False)
    IniManager().set(key=ini_key, section="AutoSalvage", var_name="salvage_blues", value=True)
    IniManager().set(key=ini_key, section="AutoSalvage", var_name="salvage_purples", value=True)
    IniManager().set(key=ini_key, section="AutoSalvage", var_name="salvage_golds", value=salvage_golds)

    # === Identification Settings ===
    IniManager().set(key=ini_key, section="AutoIdentify", var_name="id_whites", value=True)
    IniManager().set(key=ini_key, section="AutoIdentify", var_name="id_blues", value=True)
    IniManager().set(key=ini_key, section="AutoIdentify", var_name="id_purples", value=True)
    IniManager().set(key=ini_key, section="AutoIdentify", var_name="id_golds", value=True)
    IniManager().set(key=ini_key, section="AutoIdentify", var_name="id_greens", value=False)

    # === Deposit Settings ===
    IniManager().set(key=ini_key, section="AutoDeposit", var_name="deposit_trophies", value=False)
    IniManager().set(key=ini_key, section="AutoDeposit", var_name="deposit_materials", value=False)
    IniManager().set(key=ini_key, section="AutoDeposit", var_name="deposit_event_items", value=False)
    IniManager().set(key=ini_key, section="AutoDeposit", var_name="deposit_dyes", value=False)
    IniManager().set(key=ini_key, section="AutoDeposit", var_name="deposit_golds", value=not salvage_golds)
    IniManager().set(key=ini_key, section="AutoDeposit", var_name="deposit_greens", value=True)
    IniManager().set(key=ini_key, section="AutoDeposit", var_name="keep_gold", value=10000)

    # === Blacklists ===
    IniManager().set(
        key=ini_key, section="AutoSalvage", var_name="salvage_blacklist", value="31202,31203,31204"
    )  # remove glacial stones
