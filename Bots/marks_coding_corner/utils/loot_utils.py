from Py4GWCoreLib import GLOBAL_CACHE
from Py4GWCoreLib import AutoInventoryHandler
from Py4GWCoreLib import AgentArray
from Py4GWCoreLib import Player
from Py4GWCoreLib import Item
from Py4GWCoreLib import ModelID
from Py4GWCoreLib import Agent
from Py4GWCoreLib import Range
from Py4GWCoreLib import Routines

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
    ModelID.Hard_Apple_Cider,
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
}


def get_valid_loot_array(viable_loot=VIABLE_LOOT):
    loot_array = AgentArray.GetItemArray()
    loot_array = AgentArray.Filter.ByDistance(loot_array, GLOBAL_CACHE.Player.GetXY(), Range.Spellcast.value * 3.00)

    def is_valid_item(item_id):
        if not Agent.IsValid(item_id):
            return False
        player_agent_id = Player.GetAgentID()
        owner_id = Agent.GetItemAgentOwnerID(item_id)
        if (owner_id == player_agent_id) or (owner_id == 0):
            return True
        return False

    filtered_agent_ids = []
    for agent_id in loot_array[:]:  # Iterate over a copy to avoid modifying while iterating
        item_data = Agent.GetItemAgent(agent_id)
        item_id = item_data.item_id
        model_id = Item.GetModelID(item_id)
        if model_id in viable_loot and is_valid_item(agent_id):
            # Black and White Dyes
            if (
                model_id == ModelID.Vial_Of_Dye
                and (GLOBAL_CACHE.Item.GetDyeColor(item_id) == 10 or GLOBAL_CACHE.Item.GetDyeColor(item_id) == 12)
                or model_id != ModelID.Vial_Of_Dye
            ):
                filtered_agent_ids.append(agent_id)
    return filtered_agent_ids


def get_valid_salvagable_loot_array(viable_loot=VIABLE_LOOT):
    loot_array = AgentArray.GetItemArray()
    loot_array = AgentArray.Filter.ByDistance(loot_array, GLOBAL_CACHE.Player.GetXY(), Range.Spellcast.value * 2.00)

    def is_valid_item(item_id):
        if not Agent.IsValid(item_id):
            return False
        player_agent_id = Player.GetAgentID()
        owner_id = Agent.GetItemAgentOwnerID(item_id)
        if (owner_id == player_agent_id) or (owner_id == 0):
            return True
        return False

    agent_array = AgentArray.GetItemArray()

    item_array_model = AgentArray.Filter.ByCondition(
        agent_array, lambda agent_id: Item.GetModelID(Agent.GetItemAgent(agent_id).item_id) in viable_loot
    )

    item_array_salv = []
    item_array_salv = AgentArray.Filter.ByCondition(
        agent_array, lambda agent_id: Item.Usage.IsSalvageable(Agent.GetItemAgent(agent_id).item_id)
    )

    item_array = list(set(item_array_model + item_array_salv))
    item_array = AgentArray.Sort.ByDistance(item_array, GLOBAL_CACHE.Player.GetXY())

    # return item_array
    filtered_agent_ids = []
    for agent_id in loot_array[:]:  # Iterate over a copy to avoid modifying while iterating
        item_data = Agent.GetItemAgent(agent_id)
        item_id = item_data.item_id
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
