local Item = {}

function Item.item_instance(item_id)
    return PyItem.PyItem(item_id)
end

function Item.GetAgentID(item_id)
    return Item.item_instance(item_id).agent_id
end

function Item.GetAgentItemID(item_id)
    return Item.item_instance(item_id).agent_item_id
end

function Item.GetItemIdFromModelID(model_id)
    local bags_to_check = {Bag.Backpack, Bag.Belt_Pouch, Bag.Bag_1, Bag.Bag_2}
    for _, bag_enum in pairs(bags_to_check) do
        local bag_instance = PyInventory.Bag(bag_enum.value, bag_enum.name)
        for _, item in pairs(bag_instance:GetItems()) do
            local pyitem_instance = PyItem.PyItem(item.item_id)
            if pyitem_instance.model_id == model_id then
                return pyitem_instance.item_id
            end
        end
    end
    return 0
end

function Item.GetItemByAgentID(agent_id)
    local bags_to_check = {Bag.Backpack, Bag.Belt_Pouch, Bag.Bag_1, Bag.Bag_2}
    for _, bag_enum in pairs(bags_to_check) do
        local bag_instance = PyInventory.Bag(bag_enum.value, bag_enum.name)
        for _, item in pairs(bag_instance:GetItems()) do
            local pyitem_instance = PyItem.PyItem(item.item_id)
            if pyitem_instance.agent_id == agent_id then
                return pyitem_instance
            end
        end
    end
    return nil
end

function Item.GetName(item_id)
    return Item.item_instance(item_id).name
end

function Item.GetItemType(item_id)
    return Item.item_instance(item_id).item_type.ToInt(), Item.item_instance(item_id).item_type.GetName()
end

function Item.GetModelID(item_id)
    return Item.item_instance(item_id).model_id
end

function Item.GetSlot(item_id)
    return Item.item_instance(item_id).slot
end

function Item.Rarity.GetRarity(item_id)
    if item.rarity == nil then
        return 0, "Unknown"
    end
    return Item.item_instance(item_id).rarity.value, Item.item_instance(item_id).rarity.name
end

function Item.Rarity.IsWhite(item_id)
    local rarity_value, rarity_name = Item.Rarity.GetRarity(item_id)
    return rarity_name == "White"
end

function Item.Rarity.IsBlue(item_id)
    local rarity_value, rarity_name = Item.Rarity.GetRarity(item_id)
    return rarity_name == "Blue"
end

function Item.Rarity.IsPurple(item_id)
    local rarity_value, rarity_name = Item.Rarity.GetRarity(item_id)
    return rarity_name == "Purple"
end

function Item.Rarity.IsGold(item_id)
    local rarity_value, rarity_name = Item.Rarity.GetRarity(item_id)
    return rarity_name == "Gold"
end

function Item.Rarity.IsGreen(item_id)
    local rarity_value, rarity_name = Item.Rarity.GetRarity(item_id)
    return rarity_name == "Green"
end

function Item.Properties.IsCustomized(item_id)
    return Item.item_instance(item_id).is_customized
end

function Item.Properties.GetValue(item_id)
    return Item.item_instance(item_id).value
end

function Item.Properties.GetQuantity(item_id)
    return Item.item_instance(item_id).quantity
end

function Item.Properties.IsEquipped(item_id)
    return Item.item_instance(item_id).equipped
end

function Item.Properties.GetProfession(item_id)
    return Item.item_instance(item_id).profession
end

function Item.Properties.GetInteraction(item_id)
    return Item.item_instance(item_id).interaction
end

function Item.Type.IsWeapon(item_id)
    return Item.item_instance(item_id).is_weapon
end

function Item.Type.IsArmor(item_id)
    return Item.item_instance(item_id).is_armor
end

function Item.Type.IsInventoryItem(item_id)
    return Item.item_instance(item_id).is_inventory_item
end

function Item.Type.IsStorageItem(item_id)
    return Item.item_instance(item_id).is_storage_item
end

function Item.Type.IsMaterial(item_id)
    return Item.item_instance(item_id).is_material
end

function Item.Type.IsRareMaterial(item_id)
    return Item.item_instance(item_id).is_rare_material
end

function Item.Type.IsZCoin(item_id)
    return Item.item_instance(item_id).is_zcoin
end

function Item.Type.IsTome(item_id)
    return Item.item_instance(item_id).is_tome
end

function Item.Usage.IsUsable(item_id)
    return Item.item_instance(item_id).is_usable
end

function Item.Usage.GetUses(item_id)
    return Item.item_instance(item_id).uses
end

function Item.Usage.IsSalvageable(item_id)
    return Item.item_instance(item_id).is_salvageable
end

function Item.Usage.IsMaterialSalvageable(item_id)
    return Item.item_instance(item_id).is_material_salvageable
end

function Item.Usage.IsSalvageKit(item_id)
    return Item.item_instance(item_id).is_salvage_kit
end

function Item.Usage.IsLesserKit(item_id)
    return Item.item_instance(item_id).is_lesser_kit
end

function Item.Usage.IsExpertSalvageKit(item_id)
    return Item.item_instance(item_id).is_expert_salvage_kit
end

function Item.Usage.IsPerfectSalvageKit(item_id)
    return Item.item_instance(item_id).is_perfect_salvage_kit
end

function Item.Usage.IsIDKit(item_id)
    return Item.item_instance(item_id).is_id_kit
end

function Item.Usage.IsIdentified(item_id)
    return Item.item_instance(item_id).is_identified
end

function Item.Customization.IsInscription(item_id)
    return Item.item_instance(item_id).is_inscription
end

function Item.Customization.IsInscribable(item_id)
    return Item.item_instance(item_id).is_inscribable
end

function Item.Customization.IsPrefixUpgradable(item_id)
    return Item.item_instance(item_id).is_prefix_upgradable
end

function Item.Customization.IsSuffixUpgradable(item_id)
    return Item.item_instance(item_id).is_suffix_upgradable
end

function Item.Customization.Modifiers.GetModifierCount(item_id)
    return #Item.item_instance(item_id).modifiers
end

function Item.Customization.Modifiers.GetModifiers(item_id)
    return Item.item_instance(item_id).modifiers
end

function Item.Customization.Modifiers.ModifierExists(item_id, identifier_lookup)
    for _, modifier in pairs(Item.Customization.Modifiers.GetModifiers(item_id)) do
        if modifier:GetIdentifier() == identifier_lookup then
            return true
        end
    end
    return false
end

function Item.Customization.Modifiers.GetModifierValues(item_id, identifier_lookup)
    for _, modifier in pairs(Item.Customization.Modifiers.GetModifiers(item_id)) do
        if modifier:GetIdentifier() == identifier_lookup then
            local arg = modifier:GetArg()
            local arg1 = modifier:GetArg1()
            local arg2 = modifier:GetArg2()
            return arg, arg1, arg2
        end
    end
    return nil, nil, nil
end

function Item.Customization.GetDyeInfo(item_id)
    return Item.item_instance(item_id).dye_info
end

function Item.Customization.GetItemFormula(item_id)
    return Item.item_instance(item_id).item_formula
end

function Item.Customization.IsStackable(item_id)
    return Item.item_instance(item_id).is_stackable
end

function Item.Customization.IsSparkly(item_id)
    return Item.item_instance(item_id).is_sparkly
end

function Item.Trade.IsOfferedInTrade(item_id)
    return Item.item_instance(item_id).is_offered_in_trade
end

function Item.Trade.IsTradable(item_id)
    return Item.item_instance(item_id).is_tradable
end

return Item
