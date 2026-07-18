from datetime import datetime
from PyItem import DyeInfo, ItemModifier
from Py4GWCoreLib import Item
from Py4GWCoreLib.enums import Attribute, DyeColor, ItemType, ModelID, Rarity
from Py4GWCoreLib.enums_src.GameData_enums import Profession
from Py4GWCoreLib.enums_src.Region_enums import ServerLanguage
from Py4GWCoreLib.py4gwcorelib_src.Console import Console, ConsoleLog
from Sources.frenkeyLib.LootEx.enum import ModType, ModifierIdentifier
from Sources.frenkeyLib.LootEx.models import ItemModifiersInformation, RuneModInfo, WeaponModInfo

class Cached_Item:
    def __init__(self, item_id: int, slot: int = -1):
        from Sources.frenkeyLib.LootEx import utility, models, enum, skin_rule, weapon_rule
        from Sources.frenkeyLib.LootEx.data import Data
        data = Data()
        
        from Sources.frenkeyLib.LootEx.settings import Settings
        settings = Settings()

        item = Item.item_instance(item_id) if item_id > 0 else None
        
        self.id: int = item_id
        self.is_valid: bool = item.IsItemValid(item_id) if item else False
        self.model_id: int = item.model_id if item else -1
        self.model_file_id: int = item.model_file_id if item else -1
        self.item_type: ItemType = ItemType(
            item.item_type.ToInt()) if item else ItemType.Unknown
        self.rarity: Rarity = Rarity(
            item.rarity.value) if item and item.rarity and item.rarity.value in Rarity else Rarity.White
        self.profession : Profession = Profession(
            item.profession) if item and item.profession in Profession else Profession._None
        
        self.data: models.Item | None = data.Items.get_item(
            self.item_type, self.model_id) if self.model_id > -1 and self.item_type in data.Items else None
        self.wiki_data_scraped: bool = self.data.wiki_scraped if self.data else False

        self.is_identified: bool = item.is_identified if item else False
        self.value: int = item.value if item else 0
        self.is_salvageable: bool = item.is_salvageable if item else False
        self.is_inscribable: bool = item.is_inscribable if item else False
        
        self.quantity: int = item.quantity if item else 0
        self.uses: int = item.uses if item else 0
        self.is_stackable: bool = Item.Customization.IsStackable(item_id) if item_id > 0 else False
        self.is_customized: bool = item.is_customized if item else False
        self.dye_info: DyeInfo = item.dye_info if item else DyeInfo()
        
        self.is_identification_kit: bool = item.is_id_kit if item else False
        self.is_salvage_kit: bool = item.is_salvage_kit if item else False
        self.is_weapon: bool = utility.Util.IsWeaponType(self.item_type)
        self.is_armor: bool = utility.Util.IsArmorType(self.item_type)
        self.is_upgrade: bool = self.item_type == ItemType.Rune_Mod
        self.is_rune: bool = False
        self.target_item_type: ItemType = ItemType.Unknown

        self.slot: int = slot if slot > -1 else item.slot if item else -1
        self.is_inventory_item: bool = item.is_inventory_item if item else False
        self.is_storage_item: bool = item.is_storage_item if item else False

        self.color: DyeColor = utility.Util.get_color_from_info(
            self.dye_info) if self.dye_info else DyeColor.NoColor

        self.shield_armor: tuple[int, int] = (0, 0)
        self.damage: tuple[int, int] = (0, 0)
        attribute, requirements = (Attribute.None_, 0)

        self.attribute: Attribute = attribute
        self.requirements: int = requirements

        self.material: models.Material | None = None
        if self.item_type == ItemType.Materials_Zcoins:
            if self.model_id in data.Materials:
                self.material = data.Materials[self.model_id]
        
        self.common_material : bool = self.material in data.Common_Materials.values() if self.material else False
        self.rare_material : bool = self.material in data.Rare_Materials.values() if self.material else False

        self.skin = self.data.inventory_icon if self.data else None
        
        # self.config = settings.current.profile.items.get_item_config(
        #     self.item_type, self.model_id) if settings.current.profile and self.model_id > -1 else None
        self.is_blacklisted: bool = settings.profile.is_blacklisted(
            self.item_type, self.model_id) if settings.profile and self.model_id > -1 else False

        self.action: enum.ItemAction = enum.ItemAction.NONE
        self.savlage_tries: int = 0
        self.salvage_started: datetime | None = None
        self.salvage_requires_confirmation: bool = False
        self.salvage_confirmed: bool = False
        self.salvage_requires_material_confirmation: bool = False
        self.salvage_option: enum.SalvageOption = enum.SalvageOption.None_

        self.has_mods: bool = False
        self.modifiers: list[ItemModifier] = item.modifiers if item else []
        
        self.is_highly_salvageable: bool = False
        self.has_increased_value: bool = False
        
        self.is_rare_weapon : bool = utility.Util.IsRareWeapon(self.model_id) and self.rarity == Rarity.Gold
        self.is_rare_weapon_to_keep : bool = self.is_rare_weapon and settings.profile.rare_weapons.get(self.data.name, False) if self.data and settings.profile else False
        
        mods_info = ItemModifiersInformation.GetModsFromModifiers(self.modifiers, self.item_type, self.model_id, self.is_inscribable)
        
        self.target_item_type: ItemType = mods_info.target_item_type
        self.damage: tuple[int, int] = mods_info.damage
        self.shield_armor: tuple[int, int] = mods_info.shield_armor
        self.requirements: int = mods_info.requirements
        self.attribute: Attribute = mods_info.attribute
        self.is_highly_salvageable: bool = mods_info.is_highly_salvageable
        self.has_increased_value: bool = mods_info.has_increased_value
        
        self.runes: list[RuneModInfo] = mods_info.runes
        self.max_runes: list[RuneModInfo] = mods_info.max_runes
        self.runes_to_keep: list[RuneModInfo] = mods_info.runes_to_keep
        self.runes_to_sell: list[RuneModInfo] = mods_info.runes_to_sell
        
        self.weapon_mods: list[WeaponModInfo] = mods_info.weapon_mods
        self.max_weapon_mods: list[WeaponModInfo] = mods_info.max_weapon_mods
        self.weapon_mods_to_keep: list[WeaponModInfo] = mods_info.weapon_mods_to_keep
        self.mods: list[RuneModInfo | WeaponModInfo] = mods_info.mods
        
        self.has_mods: bool = False
        
        self.name : str = self.get_name()
                
        self.skin_rule: skin_rule.SkinRule | None = None
        self.matches_skin_rule: bool = False
        if settings.profile and settings.profile.skin_rules_by_model.get(self.item_type, {}).get(self.model_id, None):
            self.skin_rule = next((
                rule for rule in settings.profile.skin_rules_by_model[self.item_type][self.model_id]
                if rule.skin == self.skin and self.skin is not None
            ), None)      
            
            self.matches_skin_rule = self.skin_rule.matches(self) if self.skin_rule else False
            
        
        self.weapon_rule: weapon_rule.WeaponRule | None = None
        self.matches_weapon_rule: bool = False
        
        if settings.profile and settings.profile.weapon_rules.get(self.item_type, {}):
            self.weapon_rule = settings.profile.weapon_rules[self.item_type]
        
        if self.weapon_rule:
            self.matches_weapon_rule = self.weapon_rule.matches(self)

        pass
    
    def get_name(self) -> str:
        from Sources.frenkeyLib.LootEx.settings import Settings
        settings = Settings()
        
        from Sources.frenkeyLib.LootEx.data import Data
        data = Data()
        
        color_names = data.ColorNames.get(settings.language, {})
        
        if self.data:
            if self.data.name:                
                if self.item_type == ItemType.Dye:
                    if self.dye_info is not None:
                        color_name = color_names.get(DyeColor(self.dye_info.dye1.ToInt()))
                        return self.data.name.format(color_name, self.quantity)
                    pass
                
                if self.item_type == ItemType.Rune_Mod:
                    if self.mods:
                        if not self.is_rune:
                            mod_name = self.mods[0].Mod.name
                            return self.data.name.format(mod_name)
                        else:
                            return self.mods[0].Mod.name
                    pass
                
                if self.mods:
                    if self.is_armor or self.is_weapon:                              
                        armor_formats = {                          
                            ServerLanguage.German: "{Prefix} {Item} {Suffix}",
                            ServerLanguage.English: "{Prefix} {Item} {Suffix}",
                            ServerLanguage.Korean: "{Prefix} {Item} {Suffix}",
                            ServerLanguage.French: "{Item} {Prefix} {Suffix}",
                            ServerLanguage.Italian: "{Item} {Suffix} {Prefix}",   
                            ServerLanguage.Spanish: "{Item} {Prefix} {Suffix}",                          
                            ServerLanguage.TraditionalChinese: "{Suffix} {Prefix} {Item}",                          
                            ServerLanguage.Japanese: "{Prefix} {Item} {Suffix}",  
                            ServerLanguage.Polish: "{Item} {Prefix} {Suffix}",    
                            ServerLanguage.Russian: "{Prefix} {Item} {Suffix}", 
                            ServerLanguage.BorkBorkBork: "{Prefix} {Item} {Suffix}",                   
                        }
                        
                        prefix = next((mod.Mod.name for mod in self.mods if mod.Mod.mod_type == ModType.Prefix), "")
                        suffix = next((mod.Mod.name for mod in self.mods if mod.Mod.mod_type == ModType.Suffix), "")
                        
                        fmt = armor_formats.get(settings.language, "{Prefix} {Item} {Suffix}")
                        return fmt.format(Item=self.data.name, Prefix=prefix, Suffix=suffix).strip()
                
                if self.is_stackable and self.quantity > 1:
                    return f"{self.quantity} {self.data.name}"
                
                return self.data.name
        
        return "Unknown Item"
    
    def IsVial_Of_DyeToKeep(self) -> bool:
        from Sources.frenkeyLib.LootEx.settings import Settings
        settings = Settings()
        
        Profile = settings.profile

        if Profile is None:
            return False

        if self.model_id == ModelID.Vial_Of_Dye:
                if self.color is not None and self.color in Profile.dyes:
                    return Profile.dyes[self.color]

        return False
    
    def Update(self):
        item = Item.item_instance(self.id) if self.id > 0 else None
        if item is None or not item.IsItemValid(self.id):
            return
        
        self.is_inventory_item = item.is_inventory_item
        self.is_identified = item.is_identified
        self.quantity = item.quantity
        self.uses = item.uses
        self.is_customized = item.is_customized
        self.dye_info = item.dye_info
        self.value = item.value
        
        self.ResetMods()
        self.GetModsFromModifiers()

                    

    def ExistsInCache(self, cache: list["Cached_Item"]) -> bool:
        item = next((item for item in cache if item.id == self.id), None)
        return item is not None and item.quantity >= self.quantity

    def ExistsInInventory(self) -> bool:
        if self.id <= 0:
            return False

        item = Item.item_instance(self.id) if self.id > 0 else None
        return item.is_inventory_item if item else False

    def IsSalvaged(self) -> tuple[bool, int]:
        if self.id <= 0:
            return False, -1

        item = Cached_Item(self.id, self.slot) if self.id > 0 else None
        if item is None:
            return True, -1
        
        # if item.mods is different from self.mods return True, -1
        if item.mods != self.mods:
            return True, -1        
        
        salvaged = not item.is_inventory_item or item.quantity < self.quantity or item.model_id != self.model_id
        self.quantity = item.quantity if item.is_inventory_item else 0        

        return salvaged, self.quantity

    def ResetMods(self):
        self.mods = []
        self.runes = []
        self.weapon_mods = []
        self.has_mods = False
        self.max_runes = []
        self.max_weapon_mods = []
        self.is_highly_salvageable = False
        self.has_increased_value = False

    def GetModsFromModifiers(self) -> tuple[list[RuneModInfo], list[WeaponModInfo]]:
        from Sources.frenkeyLib.LootEx.enum import ModifierIdentifier
        from Sources.frenkeyLib.LootEx.models import WeaponModInfo        
        from Sources.frenkeyLib.LootEx.settings import Settings
        settings = Settings()
        
        modifier_values: list[tuple[int, int, int]] = [
            (modifier.GetIdentifier(), modifier.GetArg1(), modifier.GetArg2())
            for modifier in self.modifiers if modifier is not None
        ]

        if not modifier_values:
            return [], []
            
        for identifier, arg1, arg2 in modifier_values:
            if identifier is None or arg1 is None or arg2 is None:
                continue

            if identifier == ModifierIdentifier.TargetItemType.value:
                self.target_item_type = ItemType(
                    arg1) if arg1 is not None else ItemType.Unknown
                self.is_rune = arg1 == 0 and arg2 == 0 and self.is_upgrade

            if identifier == ModifierIdentifier.Damage.value:
                self.damage = (
                    arg2, arg1) if arg1 is not None and arg2 is not None else (0, 0)

            if identifier == ModifierIdentifier.Damage_NoReq.value:
                self.damage = (
                    arg2, arg1) if arg1 is not None and arg2 is not None else (0, 0)

            if identifier == ModifierIdentifier.ShieldArmor.value:
                self.shield_armor = (
                    arg1, arg2) if arg1 is not None and arg2 is not None else (0, 0)

            if identifier == ModifierIdentifier.Requirement.value:
                self.requirements = arg2 if arg2 is not None else 0
                self.attribute = Attribute(
                    arg1) if arg1 is not None else Attribute.None_
            
            if identifier == ModifierIdentifier.ImprovedVendorValue.value:
                self.has_increased_value = True
                
            if identifier == ModifierIdentifier.HighlySalvageable.value:
                self.is_highly_salvageable = True
                
        if self.is_armor or self.is_rune:
            runes = RuneModInfo.get_from_modifiers(modifier_values, self.item_type)
            self.runes = runes if runes else []
            self.max_runes = [rune for rune in self.runes if rune.IsMaxed]
            self.runes_to_keep = []
            self.runes_to_sell = []
            
            for rune in self.runes:
                setting = settings.profile.runes.get(rune.Rune.identifier, None) if settings.profile else None   
                if setting and setting.valuable:
                    self.runes_to_keep.append(rune)

                if setting and setting.should_sell:
                    self.runes_to_sell.append(rune)

        if self.is_weapon or (self.is_upgrade and not self.is_rune):            
            self.weapon_mods = WeaponModInfo.get_from_modifiers(modifier_values, self.item_type, self.model_id) or []
            self.max_weapon_mods = [mod for mod in self.weapon_mods if mod.IsMaxed]
            self.weapon_mods_to_keep = [mod for mod in self.max_weapon_mods if settings.profile and settings.profile.weapon_mods.get(mod.WeaponMod.identifier, {}).get(self.item_type.name, False)]
                            
        
        self.mods = self.runes + self.weapon_mods
        self.has_mods = bool(self.runes or self.weapon_mods)
        
        return self.runes, self.weapon_mods        

    def HasModToKeep(self) -> tuple[bool, list, list]:
        return True if self.max_runes or self.max_weapon_mods else False, self.max_runes, self.max_weapon_mods

    def HasMods(self) -> bool:
        return self.has_mods