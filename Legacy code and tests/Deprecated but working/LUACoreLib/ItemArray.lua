local ItemArray = {}

function ItemArray.CreateBagList(...)
    local bags_to_check = {}
    for _, bag_id in pairs({...}) do
        local bag_enum = Bag(bag_id)
        if bag_enum then
            table.insert(bags_to_check, bag_enum)
        else
            Py4GW.Console.Log("CreateBagList", "Invalid bag ID: " .. tostring(bag_id), Py4GW.Console.MessageType.Error)
        end
    end
    return bags_to_check
end

function ItemArray.GetItemArray(bags_to_check)
    local all_item_ids = {}
    for _, bag_enum in pairs(bags_to_check) do
        local bag_instance = PyInventory.Bag(bag_enum.value, bag_enum.name)
        local items_in_bag = bag_instance:GetItems()
        for _, item in pairs(items_in_bag) do
            table.insert(all_item_ids, item.item_id)
        end
    end
    return all_item_ids
end

ItemArray.Filter = {}
function ItemArray.Filter.ByAttribute(item_array, attribute, condition_func, negate)
    local filtered_items = {}
    for _, item_id in pairs(item_array) do
        local attr_value = Item[attribute](item_id)
        local result = condition_func and condition_func(attr_value) or attr_value
        if (not negate and result) or (negate and not result) then
            table.insert(filtered_items, item_id)
        end
    end
    return filtered_items
end

function ItemArray.Filter.ByCondition(item_array, filter_func)
    local filtered_items = {}
    for _, item_id in pairs(item_array) do
        if filter_func(item_id) then
            table.insert(filtered_items, item_id)
        end
    end
    return filtered_items
end

ItemArray.Manipulation = {}
function ItemArray.Manipulation.Merge(array1, array2)
    local merged_array = {}
    for _, item_id in pairs(array1) do
        merged_array[item_id] = true
    end
    for _, item_id in pairs(array2) do
        merged_array[item_id] = true
    end
    local result = {}
    for item_id, _ in pairs(merged_array) do
        table.insert(result, item_id)
    end
    return result
end

function ItemArray.Manipulation.Subtract(array1, array2)
    local subtracted_array = {}
    for _, item_id in pairs(array1) do
        local found = false
        for _, id in pairs(array2) do
            if id == item_id then
                found = true
                break
            end
        end
        if not found then
            table.insert(subtracted_array, item_id)
        end
    end
    return subtracted_array
end

function ItemArray.Manipulation.Intersect(array1, array2)
    local intersected_array = {}
    for _, item_id in pairs(array1) do
        for _, id in pairs(array2) do
            if id == item_id then
                table.insert(intersected_array, item_id)
                break
            end
        end
    end
    return intersected_array
end

ItemArray.Sort = {}
function ItemArray.Sort.SortByAttribute(item_array, attribute, reverse)
    local sorted_array = {}
    for _, item_id in pairs(item_array) do
        table.insert(sorted_array, { item_id = item_id, value = Item[attribute](item_id) })
    end
    table.sort(sorted_array, function(a, b)
        if reverse then
            return a.value > b.value
        else
            return a.value < b.value
        end
    end)
    local result = {}
    for _, item in pairs(sorted_array) do
        table.insert(result, item.item_id)
    end
    return result
end

function ItemArray.Sort.SortByCondition(item_array, condition_func, reverse)
    local sorted_array = {}
    for _, item_id in pairs(item_array) do
        table.insert(sorted_array, { item_id = item_id, value = condition_func(item_id) })
    end
    table.sort(sorted_array, function(a, b)
        if reverse then
            return a.value > b.value
        else
            return a.value < b.value
        end
    end)
    local result = {}
    for _, item in pairs(sorted_array) do
        table.insert(result, item.item_id)
    end
    return result
end

return ItemArray
