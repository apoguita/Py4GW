from Py4GWCoreLib import GLOBAL_CACHE
from Py4GWCoreLib import Trading
from Py4GWCoreLib import PyItem
from typing import List

import PyImGui

item_id = 0
item_name = "Unknown Item"

def draw_window():
    global item_id, item_name
    if PyImGui.begin("quest data"):
        #merchant_item_list = Trading.Trader.GetOfferedItems()
        #combo_items = [GLOBAL_CACHE.Item.GetName(item_id) for item_id in merchant_item_list]
        
        item_array:List[PyItem] = GLOBAL_CACHE.ItemArray.GetRawItemArray([1,2,3,4])
        for item in item_array:
            item_id = item.item_id
            item_name = GLOBAL_CACHE.Item.GetName(item_id)
            PyImGui.text(f"Item: {item} Item ID: {item_id}, Item Name: {item_name}")

            
            
        PyImGui.end()

def main():
    draw_window()


if __name__ == "__main__":
    main()