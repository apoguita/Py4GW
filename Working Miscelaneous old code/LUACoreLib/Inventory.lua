local Inventory = {}

function Inventory.inventory_instance()
    return PyInventory.PyInventory()
end

function Inventory.GetInventorySpace()
    local bags_to_check = ItemArray.CreateBagList(1, 2, 3, 4)
    local item_array = ItemArray.GetItemArray(bags_to_check)
    local total_items = #item_array
    local total_capacity = 0
    for _, bag_enum in pairs(bags_to_check) do
        total_capacity = total_capacity + PyInventory.Bag(bag_enum.value, bag_enum.name).GetSize()
    end
    return total_items, total_capacity
end

function Inventory.GetStorageSpace()
    local bags_to_check = ItemArray.CreateBagList(8, 9, 10, 11)
    local item_array = ItemArray.GetItemArray(bags_to_check)
    local total_items = #item_array
    local total_capacity = 0
    for _, bag_enum in pairs(bags_to_check) do
        total_capacity = total_capacity + PyInventory.Bag(bag_enum.value, bag_enum.name).GetSize()
    end
    return total_items, total_capacity
end

function Inventory.GetFreeSlotCount()
    local total_items, total_capacity = Inventory.GetInventorySpace()
    local free_slots = total_capacity - total_items
    return math.max(free_slots, 0)
end

function Inventory.GetItemCount(item_id)
    local bags_to_check = ItemArray.CreateBagList(1, 2, 3, 4)
    local item_array = ItemArray.GetItemArray(bags_to_check)
    local matching_items = ItemArray.Filter.ByCondition(item_array, function(item) return item == item_id end)
    local total_quantity = 0
    for _, item in pairs(matching_items) do
        total_quantity = total_quantity + Item.Properties.GetQuantity(item)
    end
    return total_quantity
end

function Inventory.GetModelCount(model_id)
    local bags_to_check = ItemArray.CreateBagList(1, 2, 3, 4)
    local item_array = ItemArray.GetItemArray(bags_to_check)
    local matching_items = ItemArray.Filter.ByCondition(item_array, function(item_id) return Item.GetModelID(item_id) == model_id end)
    local total_quantity = 0
    for _, item_id in pairs(matching_items) do
        total_quantity = total_quantity + Item.Properties.GetQuantity(item_id)
    end
    return total_quantity
end

function Inventory.GetFirstIDKit()
    local bags_to_check = ItemArray.CreateBagList(1, 2, 3, 4)
    local item_array = ItemArray.GetItemArray(bags_to_check)
    local id_kits = ItemArray.Filter.ByCondition(item_array, Item.Usage.IsIDKit)
    if #id_kits > 0 then
        local id_kit_with_lowest_uses = id_kits[1]
        for _, id_kit in pairs(id_kits) do
            if Item.Usage.GetUses(id_kit) < Item.Usage.GetUses(id_kit_with_lowest_uses) then
                id_kit_with_lowest_uses = id_kit
            end
        end
        return id_kit_with_lowest_uses
    else
        return 0
    end
end

function Inventory.GetFirstUnidentifiedItem()
    local bags_to_check = ItemArray.CreateBagList(1, 2, 3, 4)
    local item_array = ItemArray.GetItemArray(bags_to_check)
    local unidentified_items = ItemArray.Filter.ByCondition(item_array, function(item_id) return not Item.Usage.IsIdentified(item_id) end)
    if #unidentified_items > 0 then
        return unidentified_items[1]
    else
        return 0
    end
end

function Inventory.GetFirstSalvageKit()
    local bags_to_check = ItemArray.CreateBagList(1, 2, 3, 4)
    local item_array = ItemArray.GetItemArray(bags_to_check)
    local salvage_kits = ItemArray.Filter.ByCondition(item_array, Item.Usage.IsSalvageKit)
    if #salvage_kits > 0 then
        local salvage_kit_with_lowest_uses = salvage_kits[1]
        for _, salvage_kit in pairs(salvage_kits) do
            if Item.Usage.GetUses(salvage_kit) < Item.Usage.GetUses(salvage_kit_with_lowest_uses) then
                salvage_kit_with_lowest_uses = salvage_kit
            end
        end
        return salvage_kit_with_lowest_uses
    else
        return 0
    end
end

function Inventory.GetFirstSalvageableItem()
    local bags_to_check = ItemArray.CreateBagList(1, 2, 3, 4)
    local item_array = ItemArray.GetItemArray(bags_to_check)
    local salvageable_items = ItemArray.Filter.ByCondition(item_array, Item.Usage.IsSalvageable)
    if #salvageable_items > 0 then
        return salvageable_items[1]
    else
        return 0
    end
end

function Inventory.IdentifyItem(item_id, id_kit_id)
    local inventory = PyInventory.PyInventory()
    inventory.IdentifyItem(id_kit_id, item_id)
end

function Inventory.IdentifyFirst()
    local id_kit_id = Inventory.GetFirstIDKit()
    if id_kit_id ~= 0 then
        local unid_item_id = Inventory.GetFirstUnidentifiedItem()
        if unid_item_id ~= 0 then
            Inventory.IdentifyItem(unid_item_id, id_kit_id)
            return true
        end
    end
    return false
end

function Inventory.SalvageItem(item_id, salvage_kit_id)
    local inventory = PyInventory.PyInventory()
    if not inventory.IsSalvaging() then
        inventory.StartSalvage(salvage_kit_id, item_id)
    end
    if inventory.IsSalvaging() and inventory.IsSalvageTransactionDone() then
        inventory.FinishSalvage()
    end
end

function Inventory.SalvageFirst()
    local salvage_kit_id = Inventory.GetFirstSalvageKit()
    if salvage_kit_id ~= 0 then
        local salvage_item_id = Inventory.GetFirstSalvageableItem()
        if salvage_item_id ~= 0 then
            Inventory.SalvageItem(salvage_item_id, salvage_kit_id)
            return true
        end
    end
    return false
end

function Inventory.IsInSalvageSession()
    return Inventory.inventory_instance().IsSalvaging()
end

function Inventory.IsSalvageSessionDone()
    return Inventory.inventory_instance().IsSalvageTransactionDone()
end

function Inventory.FinishSalvage()
    if Inventory.inventory_instance().IsSalvaging() and Inventory.inventory_instance().IsSalvageTransactionDone() then
        Inventory.inventory_instance().FinishSalvage()
        return true
    end
    return false
end

function Inventory.OpenXunlaiWindow()
    Inventory.inventory_instance().OpenXunlaiWindow()
    return Inventory.inventory_instance().GetIsStorageOpen()
end

function Inventory.IsStorageOpen()
    return Inventory.inventory_instance().GetIsStorageOpen()
end

function Inventory.PickUpItem(item_id, call_target)
    Inventory.inventory_instance().PickUpItem(item_id, call_target)
end

function Inventory.DropItem(item_id, quantity)
    Inventory.inventory_instance().DropItem(item_id, quantity)
end

function Inventory.EquipItem(item_id, agent_id)
    Inventory.inventory_instance().EquipItem(item_id, agent_id)
end

function Inventory.UseItem(item_id)
    Inventory.inventory_instance().UseItem(item_id)
end

function Inventory.DestroyItem(item_id)
    Inventory.inventory_instance().DestroyItem(item_id)
end

function Inventory.GetHoveredItemID()
    return Inventory.inventory_instance().GetHoveredItemID()
end

function Inventory.GetGoldOnCharacter()
    return Inventory.inventory_instance().GetGoldAmount()
end

function Inventory.GetGoldInStorage()
    return Inventory.inventory_instance().GetGoldAmountInStorage()
end

function Inventory.DepositGold(amount)
    Inventory.inventory_instance().DepositGold(amount)
end

function Inventory.WithdrawGold(amount)
    Inventory.inventory_instance().WithdrawGold(amount)
end

function Inventory.DropGold(amount)
    Inventory.inventory_instance().DropGold(amount)
end

function Inventory.MoveItem(item_id, bag_id, slot, quantity)
    Inventory.inventory_instance().MoveItem(item_id, bag_id, slot, quantity)
end

function Inventory.FindItemBagAndSlot(item_id)
    local bags_to_check = ItemArray.CreateBagList(1, 2, 3, 4)
    local items = ItemArray.GetItemArray(bags_to_check)
    for _, bag_enum in pairs(bags_to_check) do
        local bag_items = ItemArray.GetItemArray({bag_enum})
        for _, item in pairs(bag_items) do
            if item == item_id then
                local slot = Item.Properties.GetSlot(item)
                return bag_enum.value, slot
            end
        end
    end
    return nil, nil
end

function Inventory.DepositItemToStorage(item_id, quantity)
    local storage_bags = ItemArray.CreateBagList(8, 9, 10, 11)
    for _, storage_bag in pairs(storage_bags) do
        local bag_instance = PyInventory.Bag(storage_bag.value, storage_bag.name)
        local items_in_bag = bag_instance.GetItems()
        local occupied_slots = {}
        for _, item in pairs(items_in_bag) do
            occupied_slots[Item.GetSlot(item.item_id)] = true
        end
        local total_slots = bag_instance.GetSize()
        for slot = 0, total_slots - 1 do
            if not occupied_slots[slot] then
                if quantity == 0 then
                    quantity = Item.Properties.GetQuantity(item_id)
                end
                Inventory.MoveItem(item_id, storage_bag.value, slot, quantity)
                return true
            end
        end
    end
    return false
end

return Inventory
