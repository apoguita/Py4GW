
from Py4GWCoreLib import *


quantity_to_consume = 250
hunters_ale = ModelID.Hunters_Ale.value  # Change to desired item model ID
sugary_blue_drink = ModelID.Sugary_Blue_Drink.value  # Change to desired item model ID
champagne_popper = ModelID.Champagne_Popper.value  # Change to desired item model ID

def eat_items(model_id: int, quantity: int):
    for _ in range(quantity):
        item_id = GLOBAL_CACHE.Inventory.GetFirstModelID(model_id)
        if item_id:
            GLOBAL_CACHE.Inventory.UseItem(item_id)
            yield from Yield.wait(50)



def main():
    global quantity_to_consume, model_to_consume

    if PyImGui.begin("item eater", PyImGui.WindowFlags.AlwaysAutoResize):
        quantity_to_consume = PyImGui.input_int("Quantity to eat", quantity_to_consume)
        if PyImGui.button("eat hunters ale"):
            GLOBAL_CACHE.Coroutines.append(eat_items(hunters_ale, quantity_to_consume))
        if PyImGui.button("eat sugary blue drink"):
            GLOBAL_CACHE.Coroutines.append(eat_items(sugary_blue_drink, quantity_to_consume))
        if PyImGui.button("eat champagne popper"):
            GLOBAL_CACHE.Coroutines.append(eat_items(champagne_popper, quantity_to_consume))

    PyImGui.end()


if __name__ == "__main__":
    main()