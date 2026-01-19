
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
            yield from Routines.Yield.wait(50)
            
def exchange_pumpkins_for_pie(quantity: int):
    for _ in range(quantity):
        target = Player.GetTargetID()
        Player.Interact(target, False)
        yield from Routines.Yield.wait(250)
        UIManager.ClickDialogButton(int(2))
        yield from Routines.Yield.wait(100)
        UIManager.ClickDialogButton(int(1))
        yield from Routines.Yield.wait(100)



def main():
    global quantity_to_consume, model_to_consume

    if PyImGui.begin("item eater", PyImGui.WindowFlags.AlwaysAutoResize):
        quantity_to_consume = PyImGui.input_int("Quantity to eat", quantity_to_consume)
        if PyImGui.button("open tot bags"):
            GLOBAL_CACHE.Coroutines.append(eat_items(ModelID.Trick_Or_Treat_Bag.value, quantity_to_consume))
            
        if PyImGui.button("exchange pumpkins for pie"):
            GLOBAL_CACHE.Coroutines.append(exchange_pumpkins_for_pie(quantity_to_consume))
            
        if PyImGui.button("eat sugary blue drink"):
            GLOBAL_CACHE.Coroutines.append(eat_items(sugary_blue_drink, quantity_to_consume))
            
        if PyImGui.button("eat creme brulee"):
            GLOBAL_CACHE.Coroutines.append(eat_items(ModelID.Creme_Brulee.value, quantity_to_consume))
            
        if PyImGui.button("eat fruitcake"):
            GLOBAL_CACHE.Coroutines.append(eat_items(ModelID.Fruitcake.value, quantity_to_consume))

        if PyImGui.button("eat eggnogs"):
            GLOBAL_CACHE.Coroutines.append(eat_items(ModelID.Eggnog.value, quantity_to_consume))
            
        if PyImGui.button("eat snowman sumonner"):
            GLOBAL_CACHE.Coroutines.append(eat_items(ModelID.Snowman_Summoner.value, quantity_to_consume))

        if PyImGui.button("eat wintersday gift"):
            GLOBAL_CACHE.Coroutines.append(eat_items(ModelID.Wintersday_Gift.value, quantity_to_consume))            

    PyImGui.end()


if __name__ == "__main__":
    main()