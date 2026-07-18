from Py4GWCoreLib import *

MODULE_NAME = "tester for everything"

window_open = True 

def is_item_salvage(item_id):
    """
    Check if the item is salvageable.
    """
    is_blue = Item.Rarity.IsBlue(item_id)
    is_purple = Item.Rarity.IsPurple(item_id)
    is_gold = Item.Rarity.IsGold(item_id)
    
    item_type, _ = Item.GetItemType(item_id)
    
    if item_type == ItemType.Salvage.value:
        return is_blue or is_purple or is_gold
    return False

def is_item_blue(item_id):
    """
    Check if the item is blue.
    """
    return Item.Rarity.IsBlue(item_id)

def evaluate_item_conditions(item_id, eval_fn):
    """
    Evaluate the item conditions based on the provided function.
    """
    if eval_fn(item_id):
        return True
    return False

item_id = 0

def main():
    global item_id

    if PyImGui.begin("close button test"):
    
        item_id = PyImGui.input_int("item id", item_id)
        
        if evaluate_item_conditions(item_id, lambda id: is_item_salvage(id)):
            PyImGui.text("Item is salvage")
        else:
            PyImGui.text("Item is not salvage")

        if evaluate_item_conditions(item_id, lambda id: is_item_blue(id)):
            PyImGui.text("Item is blue")
        else:
            PyImGui.text("Item is not blue")
        
           
    PyImGui.end()
    
if __name__ == "__main__":
    main()
