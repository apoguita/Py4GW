from Py4GWCoreLib import Botting, GLOBAL_CACHE, ModelID, UIManager, ConsoleLog, Console, Routines, ColorPalette
import PyImGui
from typing import Any, Generator

MODULE_NAME = "Bag Equipper"
bot = Botting(MODULE_NAME)

def _merchant_frame_exists() -> bool:
    MERCHANT_FRAME = 3613855137
    merchant_frame_id = UIManager.GetFrameIDByHash(MERCHANT_FRAME)
    merchant_frame_exists = UIManager.FrameExists(merchant_frame_id)
    return merchant_frame_exists

def _buy_item(model_id: int, desired_quantity: int):
        if _merchant_frame_exists(): # and self._is_merchant(): 
            offered_items = GLOBAL_CACHE.Trading.Merchant.GetOfferedItems()
            for item in offered_items:
                item_model = GLOBAL_CACHE.Item.GetModelID(item)
                if item_model == model_id:
                    value = GLOBAL_CACHE.Item.Properties.GetValue(item) * 2
                    bought = 0
                    while bought < desired_quantity:
                        GLOBAL_CACHE.Trading.Merchant.BuyItem(item, value)
                        bought += 1
                    break
                
def EquipItem(model_id: int):       
    item_id = GLOBAL_CACHE.Inventory.GetFirstModelID(model_id)
    if item_id:
        GLOBAL_CACHE.Inventory.EquipItem(item_id, GLOBAL_CACHE.Player.GetAgentID())
    else:
        return False
    return True

def UseItem(model_id: int):
    item_id = GLOBAL_CACHE.Inventory.GetFirstModelID(model_id)
    if item_id:
        GLOBAL_CACHE.Inventory.UseItem(item_id)
    else:
        return False
    return True

def _get_parent_hash():
    INVENTORY_FRAME_HASH = 291586130  
    return INVENTORY_FRAME_HASH

def _get_offsets(bag_id:int, slot:int):
        return [0,0,0,bag_id-1,slot+2]

def _double_click_item(bag_id: int, slot: int):

    frame_id = UIManager.GetChildFrameID(_get_parent_hash(), _get_offsets(bag_id, slot))
    if not UIManager.FrameExists(frame_id):
        ConsoleLog("Vaettir Prepper", f"Frame does not exist for bag {bag_id} slot {slot}.", Console.MessageType.Error)
        return False
    
    color = ColorPalette.GetColor("white").to_color()
    UIManager().DrawFrame(frame_id, color)
    UIManager.TestMouseAction(frame_id=frame_id, current_state=8, wparam_value=0, lparam_value=0)


def draw_window():
    if PyImGui.begin("Vaettir Prepper Debug"):
        PyImGui.text("Debug info for Vaettir Prepper ")
        if PyImGui.button("buy beltpouch"):
            _buy_item(ModelID.Belt_Pouch.value, 1)
            
        if PyImGui.button("move bag to slot 0 "):
            GLOBAL_CACHE.Inventory.MoveModelToBagSlot(ModelID.Bag.value, 
                                                       target_bag=1,
                                                       target_slot=0)
            
        if PyImGui.button("move rune of holding to slot 1 "):
            GLOBAL_CACHE.Inventory.MoveModelToBagSlot(ModelID.Rune_Of_Holding.value, 
                                                       target_bag=1,
                                                       target_slot=1)
            
        if PyImGui.button("activate rune of holding"):
            _double_click_item(bag_id=1, slot=1)
            
        if PyImGui.button("use bag"):
            UseItem(ModelID.Bag.value)

    PyImGui.end()
    
bot = Botting(MODULE_NAME)

def bot_routine(bot: Botting) -> None:
    bot.States.AddHeader(MODULE_NAME)
    bot.UI.OpenAllBags()
    bot.Items.MoveModelToBagSlot(ModelID.Belt_Pouch.value, target_bag=1, slot=0)
    bot.UI.BagItemDoubleClick(bag_id=1, slot=0) #equip beltpouch
    bot.Items.MoveModelToBagSlot(ModelID.Bag.value, target_bag=1, slot=0)
    bot.Items.MoveModelToBagSlot(ModelID.Rune_Of_Holding.value, target_bag=1, slot=1)
    
    bot.UI.BagItemDoubleClick(bag_id=1, slot=1) #activate rune of holding
    bot.UI.BagItemClick(bag_id=1, slot=0) #apply to bag
    
    bot.UI.FrameClickOnBagSlot(bag_id=1, slot=0) #apply to bag
        #bot.UI.BagItemDoubleClick(bag_id=1, slot=0) #equip bag
    #bot.UI.CloseAllBags()
    
bot.SetMainRoutine(bot_routine)   

def main():
    draw_window()
    bot.Update()
    bot.UI.draw_window()

if __name__ == "__main__":
    main()
