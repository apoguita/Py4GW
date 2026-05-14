

from Sources.frenkeyLib.ItemHandling.Rules.base_rule import *


RULE_DESCRIPTIONS = {
    ModelIdRule: "Compares against the item model id. This is very basic but is a fast way to identify specific items. However it isn't 100%% reliable as the model id is shared across item types and rarities. For example, all white items of the same type share the same model id, regardless of their rarity or attributes.",
    ItemTypesRule: "Compares against the item type. This is a more general rule that can be used to identify items of a certain type, regardless of their model id or attributes. For example, you could use this rule to apply to all axes, spears, ..., or all materials.",
    RaritiesRule: "Compares against the item rarity. This is a simple rule that can be used to identify items of a certain rarity, regardless of their type or attributes. For example, you could use this rule to apply to all rare (gold) items, or all uncommon (purple) items.",
    DyesRule : "A rule which only applies to Vial of Dye items and compares against the dye color. This is useful for picking up specific dyes or ignoring certain colors.",
    ItemSkinRule: "Compares against the item skin. Basic rule which has similar drawbacks as the model id. This is useful for picking up specific skins. For example, you could use this rule to pick up all items with the 'Shadow Blade' skin.\n\nThe skin is populated from the items.json file so it is important to keep that file updated to ensure all skins are recognized.",
    ItemTypeAndRarityRule: "Compares against both the item type and rarity. This is a more specific rule that can be used to identify items of a certain type and rarity. For example, you could use this rule to apply to all rare (gold) axes, or all uncommon (purple) swords.",
    WeaponSkinRule: "Compares against the weapon/item skin, as well as the required attribute level and properties. This is useful for picking up specific skins or items with certain attributes like a 'Old School Q9 Shadow Blade with 15^50'.\n\nThe skin is populated from the items.json file so it is important to keep that file updated to ensure all skins are recognized.",
    WeaponTypeRule: "Compares against the weapon type, as well as the required attribute level and properties. This is a more specific rule that can be used to identify weapons of a certain type. For example, you could use this rule to apply to all Q9 and Q10 axes, or all spears etc.",
    UpgradeRule: "Compares against the upgrade components of an item. This is a more specific rule that can be used to identify items with certain upgrades. For example, you could use this rule to apply to all items with a certain rune or weapon upgrade.",
    SalvagesToMaterialRule: "Compares against the salvage components of an item. This is a more specific rule that can be used to identify items with certain salvages. For example, you could use this rule to apply to all items with a certain salvage component, or all items that salvage into a certain material.\n\nThe salvage components are populated from the items.json file so it is important to keep that file updated to ensure all salvages are recognized.",
}