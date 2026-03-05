import re
from typing import Optional, cast

import Py4GW

from Py4GWCoreLib.UIManager import UIManager
from Py4GWCoreLib.enums_src.GameData_enums import PROFESSION_ATTRIBUTES, Attribute, AttributeNames, Profession
from Py4GWCoreLib.enums_src.Item_enums import ItemType, Rarity
from Py4GWCoreLib.enums_src.Region_enums import ServerLanguage
from Py4GWCoreLib.enums_src.UI_enums import NumberPreference
from Sources.frenkeyLib.ItemHandling.Mods.decoded_modifier import DecodedModifier
from Sources.frenkeyLib.ItemHandling.Mods.properties import AttributePlusOne, DamagePlusVsSpecies, ItemProperty, OfTheProfession
from Sources.frenkeyLib.ItemHandling.Mods.types import ItemBaneSpecies, ItemUpgrade, ItemUpgradeId, ItemUpgradeType, ModifierIdentifier

def _get_property_factory():
    from Sources.frenkeyLib.ItemHandling.Mods.upgrade_parser import _PROPERTY_FACTORY
    return _PROPERTY_FACTORY

class Upgrade:
    """
    Abstract base class for item upgrades. Each specific upgrade type (e.g., Prefix, Suffix, Inscription) should inherit from this class and implement the necessary properties and methods.
    """
    mod_type : ItemUpgradeType
    id: ItemUpgrade = ItemUpgrade.Unknown
    upgrade_id: ItemUpgradeId = ItemUpgradeId.Unknown
    property_identifiers: list[ModifierIdentifier] = []
    properties: list[ItemProperty] = []
    
    names: dict[ServerLanguage, str] = {}
    descriptions: dict[ServerLanguage, str] = {}

    @classmethod
    def _pre_compose(cls, upgrade: "Upgrade", mod: DecodedModifier, modifiers: list[DecodedModifier],) -> None:
        return None

    @classmethod
    def _post_compose(cls, upgrade: "Upgrade", mod: DecodedModifier, modifiers: list[DecodedModifier],) -> None:
        return None
    
    @classmethod
    def compose_from_modifiers(cls, mod : DecodedModifier, modifiers: list[DecodedModifier]) -> Optional["Upgrade"]:        
        upgrade = cls()
        upgrade.properties = []
        upgrade.upgrade_id = mod.upgrade_id

        cls._pre_compose(upgrade, mod, modifiers)

        property_factory = _get_property_factory()
        for prop_id in upgrade.property_identifiers:
            prop_mod = next((m for m in modifiers if m.identifier == prop_id), None)
            
            if prop_mod:
                prop = property_factory.get(prop_id, lambda m, _: ItemProperty(modifier=m))(prop_mod, modifiers)
                upgrade.properties.append(prop)
            else:
                Py4GW.Console.Log("ItemHandling", f"Missing modifier for property {prop_id.name} in upgrade {upgrade.__class__.__name__}. Upgrade composition failed.")
                return None

        cls._post_compose(upgrade, mod, modifiers)
        return upgrade

    @classmethod
    def has_id(cls, upgrade_id: ItemUpgradeId) -> bool:
        return cls.id.has_id(upgrade_id)
    
    @property
    def name(self) -> str:
        preference = UIManager.GetIntPreference(NumberPreference.TextLanguage)
        server_language = ServerLanguage(preference)
        return self.names.get(server_language, self.names.get(ServerLanguage.English, self.__class__.__name__))
    
    @property
    def description(self) -> str:
        parts = [prop.describe() for prop in self.properties if prop.is_valid()]
        return "\n".join(parts)
    
    @property
    def item_type(self) -> Optional[ItemType]:
        if isinstance(self, WeaponUpgrade):
            return self.target_item_type
        
        elif isinstance(self, Inscription):
            return self.target_item_type
        
        return None
    
class UnknownUpgrade(Upgrade):
    mod_type = ItemUpgradeType.Unknown
    id = ItemUpgrade.Unknown
    property_identifiers = []
    
#region Weapon Upgrades
class WeaponUpgrade(Upgrade):
    target_item_type : ItemType

    @classmethod
    def _pre_compose(cls, upgrade: "Upgrade", mod: DecodedModifier, modifiers: list[DecodedModifier],) -> None:
        weapon_upgrade = cast("WeaponUpgrade", upgrade)
        weapon_upgrade.target_item_type = cls.id.get_item_type(weapon_upgrade.upgrade_id)

#region Prefixes
WEAPON_PREFIX_ITEM_NAME_FORMAT: dict[ItemType, dict[ServerLanguage, str]] = {
    ItemType.Axe: {
        ServerLanguage.English: "{prefix} Axe Haft",
    },
    ItemType.Bow: {
        ServerLanguage.German: "{prefix} Bogensehne",
        ServerLanguage.English: "{prefix} Bow String",
        ServerLanguage.Korean: "{prefix} 활시위",
        ServerLanguage.French: "Corde {prefix}",
        ServerLanguage.Italian: "Corda d'arco {prefix}",
        ServerLanguage.Spanish: "Cuerda de arco {prefix}",
        ServerLanguage.TraditionalChinese: "{prefix} 弓弦",
        ServerLanguage.Japanese: "{prefix} ボウの弦",
        ServerLanguage.Polish: "Cięciwa {prefix}",
        ServerLanguage.Russian: "{prefix} Bow String",
        ServerLanguage.BorkBorkBork: "{prefix} Boostreeng"
    },
    ItemType.Daggers: {
        ServerLanguage.German: "{prefix} Dolchangel",
        ServerLanguage.English: "{prefix} Dagger Tang",
        ServerLanguage.Korean: "{prefix} 단검자루",
        ServerLanguage.French: "Soie de dague {prefix}",
        ServerLanguage.Italian: "Codolo per Pugnale {prefix}",
        ServerLanguage.Spanish: "Afilador de dagas {prefix}",
        ServerLanguage.TraditionalChinese: "{prefix} 匕首刃",
        ServerLanguage.Japanese: "{prefix} ダガーのグリップ",
        ServerLanguage.Polish: "Uchwyt Sztyletu {prefix}",
        ServerLanguage.Russian: "{prefix} Dagger Tang",
        ServerLanguage.BorkBorkBork: "{prefix} Daegger Tung"
    },
    # ItemType.Offhand does not have a prefix mod, so no name format is needed
    ItemType.Hammer: {
        ServerLanguage.German: "{0} Hammerstiel",
        ServerLanguage.English: "{0} Hammer Haft",
        ServerLanguage.Russian: "{0} Hammer Haft"
    },
    ItemType.Scythe: {
        ServerLanguage.English: "{0} Scythe Snathe",
    },
    # ItemType.Shield does not have a prefix mod, so no name format is needed
    ItemType.Spear: {
        ServerLanguage.German: "{0} Speerspitze",
        ServerLanguage.English: "{0} Spearhead",
        ServerLanguage.Korean: "{0} 흡혈의 창촉",
        ServerLanguage.French: "Tête de javelot {0}",
        ServerLanguage.Italian: "Punta per Lancia {0}",
        ServerLanguage.Spanish: "Punta de lanza {0}",
        ServerLanguage.TraditionalChinese: "{0} 矛頭",
        ServerLanguage.Japanese: "{0} スピアヘッド",
        ServerLanguage.Polish: "Grot Włóczni {0}",
        ServerLanguage.Russian: "{0} Spearhead",
        ServerLanguage.BorkBorkBork: "{0} Speaerheaed"
    },
    ItemType.Staff: {
        ServerLanguage.German: "{0} Stabkopf",
        ServerLanguage.English: "{0} Staff Head",
        ServerLanguage.Korean: "{0} 스태프머리",
        ServerLanguage.French: "Pommeau de bâton {0}",
        ServerLanguage.Italian: "Testa del bastone {0}",
        ServerLanguage.Spanish: "Puño de báculo {0}",
        ServerLanguage.TraditionalChinese: "{0} 法杖頭",
        ServerLanguage.Japanese: "{0} スタッフの頭部",
        ServerLanguage.Polish: "Głowica Kostura {0}",
        ServerLanguage.Russian: "{0} Staff Head",
        ServerLanguage.BorkBorkBork: "{0} Staeffff Heaed"
    },
    ItemType.Sword: {
        ServerLanguage.German: "{0} Schwertheft",
        ServerLanguage.English: "{0} Sword Hilt",
        ServerLanguage.Korean: "{0} 칼자루",
        ServerLanguage.French: "Poignée d'épée {0}",
        ServerLanguage.Italian: "Elsa della spada {0}",
        ServerLanguage.Spanish: "Empuñadura de espada {0}",
        ServerLanguage.TraditionalChinese: "{0} 劍柄",
        ServerLanguage.Japanese: "{0} ソードの柄",
        ServerLanguage.Polish: "Rękojeść Miecza {0}",
        ServerLanguage.Russian: "{0} Sword Hilt",
        ServerLanguage.BorkBorkBork: "{0} Svurd Heelt"
    }, 
    # ItemType.Wand does not have a prefix mod, so no name format is needed    
}

class WeaponPrefix(WeaponUpgrade):
    mod_type = ItemUpgradeType.Prefix

    @classmethod
    def get_weapon_upgrade_name(cls, item_type: ItemType, server_language: ServerLanguage = ServerLanguage(UIManager.GetIntPreference(NumberPreference.TextLanguage))) -> Optional[str]:
        if item_type in WEAPON_PREFIX_ITEM_NAME_FORMAT:
            item_type_name_formats = WEAPON_PREFIX_ITEM_NAME_FORMAT.get(item_type, {})
            item_type_name_format = item_type_name_formats.get(server_language, item_type_name_formats.get(ServerLanguage.English, "{prefix} " + item_type.name + " Upgrade"))
            name = cls.names.get(server_language, cls.names.get(ServerLanguage.English, f"Unknown Weapon Prefix {cls.__class__.__name__}"))
            return item_type_name_format.format(prefix=name)
        
        return None
    
class AdeptStaffUpgrade(WeaponPrefix):
    id = ItemUpgrade.Adept
    property_identifiers = [
        ModifierIdentifier.HalvesCastingTimeItemAttribute,
    ]
    names = {
		ServerLanguage.English: "Adept",
		ServerLanguage.Spanish: "de adepto",
		ServerLanguage.Italian: "da Adepto",
		ServerLanguage.German: "Experten-",
		ServerLanguage.Korean: "숙련된",
		ServerLanguage.French: "d'adepte",
		ServerLanguage.TraditionalChinese: "行家",
		ServerLanguage.Japanese: "アデプト",
		ServerLanguage.Polish: "Adepta",
		ServerLanguage.Russian: "Adept",
		ServerLanguage.BorkBorkBork: "Aedept",
	}
    
class BarbedUpgrade(WeaponPrefix):
    id = ItemUpgrade.Barbed
    property_identifiers = [
        ModifierIdentifier.IncreaseConditionDuration,
    ]
    names = {
		ServerLanguage.English: "Barbed",
		ServerLanguage.Spanish: "con espinas",
		ServerLanguage.Italian: "a Punta",
		ServerLanguage.German: "Stachel-",
		ServerLanguage.Korean: "가시 박힌",
		ServerLanguage.French: "à pointes",
		ServerLanguage.TraditionalChinese: "荊棘",
		ServerLanguage.Japanese: "バーブ",
		ServerLanguage.Polish: "Kolców",
		ServerLanguage.Russian: "Barbed",
		ServerLanguage.BorkBorkBork: "Baerbed",
	}
    
class CripplingUpgrade(WeaponPrefix):
    id = ItemUpgrade.Crippling
    property_identifiers = [
        ModifierIdentifier.IncreaseConditionDuration,
    ]
    names = {
		ServerLanguage.English: "Crippling",
		ServerLanguage.Spanish: "letal",
		ServerLanguage.Italian: "Azzoppante",
		ServerLanguage.German: "Verkrüppelungs-",
		ServerLanguage.Korean: "치명적인",
		ServerLanguage.French: "d'infirmité",
		ServerLanguage.TraditionalChinese: "致殘",
		ServerLanguage.Japanese: "クリップル",
		ServerLanguage.Polish: "Kaleczenia",
		ServerLanguage.Russian: "Crippling",
		ServerLanguage.BorkBorkBork: "Creeppleeng",
	}
        
class CruelUpgrade(WeaponPrefix):
    id = ItemUpgrade.Cruel
    property_identifiers = [
        ModifierIdentifier.IncreaseConditionDuration,
    ]
    names = {
		ServerLanguage.English: "Cruel",
		ServerLanguage.Spanish: "cruel",
		ServerLanguage.Italian: "Crudele",
		ServerLanguage.German: "Grausamkeits-",
		ServerLanguage.Korean: "잔인한",
		ServerLanguage.French: "atroce",
		ServerLanguage.TraditionalChinese: "殘酷",
		ServerLanguage.Japanese: "クルーエル",
		ServerLanguage.Polish: "Okrucieństwa",
		ServerLanguage.Russian: "Cruel",
		ServerLanguage.BorkBorkBork: "Crooel",
	}

class DefensiveUpgrade(WeaponPrefix):
    id = ItemUpgrade.Defensive
    property_identifiers = [
        ModifierIdentifier.ArmorPlus,
    ]
    names = {
		ServerLanguage.English: "Defensive",
		ServerLanguage.Spanish: "de defensa",
		ServerLanguage.Italian: "da Difesa",
		ServerLanguage.German: "Verteidigungs-",
		ServerLanguage.Korean: "방어적인",
		ServerLanguage.French: "défensif",
		ServerLanguage.TraditionalChinese: "防衛",
		ServerLanguage.Japanese: "ディフェンス",
		ServerLanguage.Polish: "Obrony",
		ServerLanguage.Russian: "Defensive",
		ServerLanguage.BorkBorkBork: "Deffenseefe-a",
	}
    
class EbonUpgrade(WeaponPrefix):
    id = ItemUpgrade.Ebon
    property_identifiers = [
        ModifierIdentifier.DamageTypeProperty,
    ]
    names = {
		ServerLanguage.English: "Ebon",
		ServerLanguage.Spanish: "con daño de granito",
		ServerLanguage.Italian: "per danno d'ebano",
		ServerLanguage.German: "Ebon-",
		ServerLanguage.Korean: "흑단",
		ServerLanguage.French: "terrestre",
		ServerLanguage.TraditionalChinese: "黑檀",
		ServerLanguage.Japanese: "エボン",
		ServerLanguage.Polish: "z Hebanu",
		ServerLanguage.Russian: "Ebon",
		ServerLanguage.BorkBorkBork: "Ibun",
	}
    
class FieryUpgrade(WeaponPrefix):
    id = ItemUpgrade.Fiery
    property_identifiers = [
        ModifierIdentifier.DamageTypeProperty,
    ]
    names = {
		ServerLanguage.English: "Fiery",
		ServerLanguage.Spanish: "con daño ardiente",
		ServerLanguage.Italian: "per danno da fuoco",
		ServerLanguage.German: "Hitze-",
		ServerLanguage.Korean: "화염의",
		ServerLanguage.French: "incendiaire",
		ServerLanguage.TraditionalChinese: "火焰",
		ServerLanguage.Japanese: "ファイア",
		ServerLanguage.Polish: "Ognia",
		ServerLanguage.Russian: "Fiery",
		ServerLanguage.BorkBorkBork: "Feeery",
	}
    
class FuriousUpgrade(WeaponPrefix):
    id = ItemUpgrade.Furious
    property_identifiers = [
        ModifierIdentifier.Furious,
    ]
    names = {
		ServerLanguage.English: "Furious",
		ServerLanguage.Spanish: "de furor",
		ServerLanguage.Italian: "della Furia",
		ServerLanguage.German: "Zorn-",
		ServerLanguage.Korean: "격노한",
		ServerLanguage.French: "de fureur",
		ServerLanguage.TraditionalChinese: "狂怒",
		ServerLanguage.Japanese: "フューリアス",
		ServerLanguage.Polish: "Wściekłości",
		ServerLanguage.Russian: "Furious",
		ServerLanguage.BorkBorkBork: "Fooreeuoos",
	}
    
class HaleUpgrade(WeaponPrefix):
    id = ItemUpgrade.Hale
    property_identifiers = [
        ModifierIdentifier.HealthPlus,
    ]
    names = {
		ServerLanguage.English: "Hale",
		ServerLanguage.Spanish: "de robustez",
		ServerLanguage.Italian: "del Vigore",
		ServerLanguage.German: "Rüstigkeits-",
		ServerLanguage.Korean: "단단한",
		ServerLanguage.French: "de vigueur",
		ServerLanguage.TraditionalChinese: "健壯",
		ServerLanguage.Japanese: "ヘイル",
		ServerLanguage.Polish: "Wigoru",
		ServerLanguage.Russian: "Hale",
		ServerLanguage.BorkBorkBork: "Haele-a",
	}
    
class HeavyUpgrade(WeaponPrefix):
    id = ItemUpgrade.Heavy
    property_identifiers = [
        ModifierIdentifier.IncreaseConditionDuration,
    ]
    names = {
		ServerLanguage.English: "Heavy",
		ServerLanguage.Spanish: "fuerte",
		ServerLanguage.Italian: "Pesante",
		ServerLanguage.German: "Schwergewichts-",
		ServerLanguage.Korean: "무거운",
		ServerLanguage.French: "de poids",
		ServerLanguage.TraditionalChinese: "沉重",
		ServerLanguage.Japanese: "ヘヴィー",
		ServerLanguage.Polish: "Ciężaru",
		ServerLanguage.Russian: "Heavy",
		ServerLanguage.BorkBorkBork: "Heaefy",
	}
    
class IcyUpgrade(WeaponPrefix):
    id = ItemUpgrade.Icy
    property_identifiers = [
        ModifierIdentifier.DamageTypeProperty,
    ]
    names = {
		ServerLanguage.English: "Icy",
		ServerLanguage.Spanish: "con daño frío",
		ServerLanguage.Italian: "per danno da ghiaccio",
		ServerLanguage.German: "Eis-",
		ServerLanguage.Korean: "냉기",
		ServerLanguage.French: "polaire",
		ServerLanguage.TraditionalChinese: "冰凍",
		ServerLanguage.Japanese: "アイス",
		ServerLanguage.Polish: "Lodu",
		ServerLanguage.Russian: "Icy",
		ServerLanguage.BorkBorkBork: "Icy",
	}
    
class InsightfulUpgrade(WeaponPrefix):
    id = ItemUpgrade.Insightful
    property_identifiers = [
        ModifierIdentifier.EnergyPlus,
    ]
    names = {
		ServerLanguage.English: "Insightful",
		ServerLanguage.Spanish: "de visión",
		ServerLanguage.Italian: "dell'Astuzia",
		ServerLanguage.German: "Einblick-",
		ServerLanguage.Korean: "통찰력의",
		ServerLanguage.French: "de vision",
		ServerLanguage.TraditionalChinese: "洞察",
		ServerLanguage.Japanese: "インサイト",
		ServerLanguage.Polish: "Przenikliwości",
		ServerLanguage.Russian: "Insightful",
		ServerLanguage.BorkBorkBork: "Inseeghtffool",
	}
    
class PoisonousUpgrade(WeaponPrefix):
    id = ItemUpgrade.Poisonous
    property_identifiers = [
        ModifierIdentifier.IncreaseConditionDuration,
    ]
    names = {
		ServerLanguage.English: "Poisonous",
		ServerLanguage.Spanish: "con veneno",
		ServerLanguage.Italian: "del Veleno",
		ServerLanguage.German: "Gift-",
		ServerLanguage.Korean: "맹독의",
		ServerLanguage.French: "de poison",
		ServerLanguage.TraditionalChinese: "淬毒",
		ServerLanguage.Japanese: "ポイズン",
		ServerLanguage.Polish: "Zatrucia",
		ServerLanguage.Russian: "Poisonous",
		ServerLanguage.BorkBorkBork: "Pueesunuoos",
	}
    
class ShockingUpgrade(WeaponPrefix):
    id = ItemUpgrade.Shocking
    property_identifiers = [
        ModifierIdentifier.DamageTypeProperty,
    ]
    names = {
		ServerLanguage.English: "Shocking",
		ServerLanguage.Spanish: "con daño de descarga",
		ServerLanguage.Italian: "per danno da shock",
		ServerLanguage.German: "Schock-",
		ServerLanguage.Korean: "충격의",
		ServerLanguage.French: "de foudre",
		ServerLanguage.TraditionalChinese: "電擊",
		ServerLanguage.Japanese: "ショック",
		ServerLanguage.Polish: "Porażenia",
		ServerLanguage.Russian: "Shocking",
		ServerLanguage.BorkBorkBork: "Shuckeeng",
	}
    
class SilencingUpgrade(WeaponPrefix):
    id = ItemUpgrade.Silencing
    property_identifiers = [
        ModifierIdentifier.IncreaseConditionDuration,
    ]
    names = {
		ServerLanguage.English: "Silencing",
		ServerLanguage.Spanish: "de silencio",
		ServerLanguage.Italian: "del Silenzio",
		ServerLanguage.German: "Dämpfungs-",
		ServerLanguage.Korean: "침묵의",
		ServerLanguage.French: "de silence",
		ServerLanguage.TraditionalChinese: "沈默",
		ServerLanguage.Japanese: "サイレンス",
		ServerLanguage.Polish: "Uciszenia",
		ServerLanguage.Russian: "Silencing",
		ServerLanguage.BorkBorkBork: "Seelenceeng",
	}
    
class SunderingUpgrade(WeaponPrefix):
    id = ItemUpgrade.Sundering
    property_identifiers = [
        ModifierIdentifier.ArmorPenetration,
    ]
    names = {
		ServerLanguage.English: "Sundering",
		ServerLanguage.Spanish: "de penetración",
		ServerLanguage.Italian: "della Separazione",
		ServerLanguage.German: "Trenn-",
		ServerLanguage.Korean: "날카로운",
		ServerLanguage.French: "de fractionnement",
		ServerLanguage.TraditionalChinese: "分離",
		ServerLanguage.Japanese: "サンダリング",
		ServerLanguage.Polish: "Rozdzierania",
		ServerLanguage.Russian: "Sundering",
		ServerLanguage.BorkBorkBork: "Soondereeng",
	}
    
class SwiftStaffUpgrade(WeaponPrefix):
    id = ItemUpgrade.Swift
    property_identifiers = [
        ModifierIdentifier.HalvesCastingTimeGeneral,
    ]
    names = {
		ServerLanguage.English: "Swift",
		ServerLanguage.Spanish: "veloz",
		ServerLanguage.Italian: "della Rapidità",
		ServerLanguage.German: "Schnelligkeits-",
		ServerLanguage.Korean: "재빠른",
		ServerLanguage.French: "rapide",
		ServerLanguage.TraditionalChinese: "迅速",
		ServerLanguage.Japanese: "スウィフト",
		ServerLanguage.Polish: "Szybkości",
		ServerLanguage.Russian: "Swift",
		ServerLanguage.BorkBorkBork: "Sveefft",
	}
    
class VampiricUpgrade(WeaponPrefix):
    id = ItemUpgrade.Vampiric
    property_identifiers = [
        ModifierIdentifier.HealthDegen,
        ModifierIdentifier.HealthStealOnHit,
    ]
    names = {
		ServerLanguage.English: "Vampiric",
		ServerLanguage.Spanish: "de vampiro",
		ServerLanguage.Italian: "del Vampiro",
		ServerLanguage.German: "Vampir-",
		ServerLanguage.Korean: "흡혈의 단검자루",
		ServerLanguage.French: "vampirique",
		ServerLanguage.TraditionalChinese: "吸血鬼 匕首刃",
		ServerLanguage.Japanese: "ヴァンピリック ダガーのグリップ",
		ServerLanguage.Polish: "Wampiryzmu",
		ServerLanguage.Russian: "Vampiric",
		ServerLanguage.BorkBorkBork: "Faempureec",
	}
    
class ZealousUpgrade(WeaponPrefix):
    id = ItemUpgrade.Zealous
    property_identifiers = [
        ModifierIdentifier.EnergyDegen,
        ModifierIdentifier.EnergyGainOnHit,
    ]
    names = {
		ServerLanguage.English: "Zealous",
		ServerLanguage.Spanish: "de afán",
		ServerLanguage.Italian: "Zelante",
		ServerLanguage.German: "Eifer-",
		ServerLanguage.Korean: "광신도의",
		ServerLanguage.French: "de zèle",
		ServerLanguage.TraditionalChinese: "熱望",
		ServerLanguage.Japanese: "ゼラス",
		ServerLanguage.Polish: "Fanatyzmu",
		ServerLanguage.Russian: "Zealous",
		ServerLanguage.BorkBorkBork: "Zeaeluoos",
	}
#endregion Prefixes

#region Suffixes
WEAPON_SUFFIX_ITEM_NAME_FORMAT: dict[ItemType, dict[ServerLanguage, str]] = {
    ItemType.Axe: {
        ServerLanguage.German: "Axtgriff {suffix}",
        ServerLanguage.English: "Axe Grip {suffix}",
        ServerLanguage.Korean: "도끼손잡이 {suffix}",
        ServerLanguage.French: "Poignée de hache {suffix}",
        ServerLanguage.Italian: "Impugnatura dell'ascia {suffix}",
        ServerLanguage.Spanish: "Empuñadura de hacha {suffix}",
        ServerLanguage.TraditionalChinese: "{suffix} 斧把手",
        ServerLanguage.Japanese: "アックスのグリップ {suffix}",
        ServerLanguage.Polish: "Stylisko Topora {suffix}",
        ServerLanguage.Russian: "Axe Grip {suffix}",
        ServerLanguage.BorkBorkBork: "Aexe-a Greep {suffix}",
    },
    ItemType.Bow: {
        ServerLanguage.German: "Bogengriff {suffix}",
        ServerLanguage.English: "Bow Grip {suffix}",
        ServerLanguage.Korean: "활손잡이 {suffix}",
        ServerLanguage.French: "Poignée d'arc {suffix}",
        ServerLanguage.Italian: "Impugnatura dell'arco {suffix}",
        ServerLanguage.Spanish: "Empuñadura de arco {suffix}",
        ServerLanguage.TraditionalChinese: "{suffix} 弓柄",
        ServerLanguage.Japanese: "ボウのグリップ {suffix}",
        ServerLanguage.Polish: "Łęczysko {suffix}",
        ServerLanguage.Russian: "Bow Grip {suffix}",
        ServerLanguage.BorkBorkBork: "Boo Greep {suffix}"
    },
    ItemType.Daggers: {
        ServerLanguage.German: "Dolchgriff {0}",
        ServerLanguage.English: "Dagger Handle {0}",
        ServerLanguage.Korean: "단검손자루 {0}",
        ServerLanguage.French: "Poignée de dague {0}",
        ServerLanguage.Italian: "Impugnatura per Pugnale {0}",
        ServerLanguage.Spanish: "Empuñadura para daga {0}",
        ServerLanguage.TraditionalChinese: "{0} 匕首握柄",
        ServerLanguage.Japanese: "ダガーの柄 {0}",
        ServerLanguage.Polish: "Rękojeść Sztyletu {0}",
        ServerLanguage.Russian: "Dagger Handle {0}",
        ServerLanguage.BorkBorkBork: "Daegger Hundle-a {0}"
    },
    ItemType.Offhand: {
        ServerLanguage.German: "Fokus-Kern {0}",
        ServerLanguage.English: "Focus Core {0}",
        ServerLanguage.Korean: "포커스장식 {0}",
        ServerLanguage.French: "Noyau de focus {0}",
        ServerLanguage.Italian: "Nucleo del Focus {0}",
        ServerLanguage.Spanish: "Mango de foco {0}",
        ServerLanguage.TraditionalChinese: "{0} 聚能器核心",
        ServerLanguage.Japanese: "フォーカスのグリップ {0}",
        ServerLanguage.Polish: "Rdzeń Fokusu {0}",
        ServerLanguage.Russian: "Focus Core {0}",
        ServerLanguage.BorkBorkBork: "Fucoos Cure-a {0}"
    },
    ItemType.Hammer: {
        ServerLanguage.German: "Hammergriff {0}",
        ServerLanguage.English: "Hammer Grip {0}",
        ServerLanguage.Korean: "해머손잡이{0}",
        ServerLanguage.French: "Poignée de marteau {0}",
        ServerLanguage.Italian: "Impugnatura del martello {0}",
        ServerLanguage.Spanish: "Empuñadura de martillo {0}",
        ServerLanguage.TraditionalChinese: "{0} 鎚把手",
        ServerLanguage.Japanese: "ハンマーのグリップ {0}",
        ServerLanguage.Polish: "Uchwyt Młota {0}",
        ServerLanguage.Russian: "Hammer Grip {0}",
        ServerLanguage.BorkBorkBork: "Haemmer Greep {0}"
    },
    ItemType.Scythe: {
        ServerLanguage.German: "Sensengriff {0}",
        ServerLanguage.English: "Scythe Grip {0}",
        ServerLanguage.Korean: "사이드손잡이 {0}",
        ServerLanguage.French: "Poignée de faux {0}",
        ServerLanguage.Italian: "Impugnatura {0}",
        ServerLanguage.Spanish: "Empuñadura de guadaña {0}",
        ServerLanguage.TraditionalChinese: "{0} 鐮刀把",
        ServerLanguage.Japanese: "サイズのグリップ {0}",
        ServerLanguage.Polish: "Drzewce Kosy {0}",
        ServerLanguage.Russian: "Scythe Grip {0}",
        ServerLanguage.BorkBorkBork: "Scyzee Greep {0}"
    },
    ItemType.Shield: {
        ServerLanguage.German: "Schildgriff {0}",
        ServerLanguage.English: "Shield Handle {0}",
        ServerLanguage.Korean: "방패손잡이 {0}",
        ServerLanguage.French: "Poignée de bouclier {0}",
        ServerLanguage.Italian: "Impugnatura dello Scudo {0}",
        ServerLanguage.Spanish: "Mango de escudo {0}",
        ServerLanguage.TraditionalChinese: "{0} 盾握柄",
        ServerLanguage.Japanese: "シールドの柄 {0}",
        ServerLanguage.Polish: "Uchwyt Tarczy {0}",
        ServerLanguage.Russian: "Shield Handle {0}",
        ServerLanguage.BorkBorkBork: "Sheeeld Hundle-a {0}"
    },
    ItemType.Spear: {
        ServerLanguage.German: "Speergriff {0}",
        ServerLanguage.English: "Spear Grip {0}",
        ServerLanguage.Korean: "창손잡이(네크로맨서) {0}",
        ServerLanguage.French: "Poignée de javelot {0}",
        ServerLanguage.Italian: "Impugnatura della Lancia {0}",
        ServerLanguage.Spanish: "Empuñadura de lanza {0}",
        ServerLanguage.TraditionalChinese: "the 矛柄 {0}",
        ServerLanguage.Japanese: "スピアのグリップ (ネクロマンサー) {0}",
        ServerLanguage.Polish: "Drzewce Włóczni {0}",
        ServerLanguage.Russian: "Spear Grip of некромант {0}",
        ServerLanguage.BorkBorkBork: "Speaer Greep {0}"
    },
    ItemType.Staff: {
        ServerLanguage.German: "Stabhülle {0}",
        ServerLanguage.English: "Staff Wrapping {0}",
        ServerLanguage.Korean: "스태프손잡이{0}",
        ServerLanguage.French: "Gaine de bâton {0}",
        ServerLanguage.Italian: "Fascia del bastone {0}",
        ServerLanguage.Spanish: "Envoltura de báculo {0}",
        ServerLanguage.TraditionalChinese: "{0} 法杖把手",
        ServerLanguage.Japanese: "スタッフの柄 {0}",
        ServerLanguage.Polish: "Okład Kostura {0}",
        ServerLanguage.Russian: "Staff Wrapping {0}",
        ServerLanguage.BorkBorkBork: "Staeffff Vraeppeeng {0}"
    },
    ItemType.Sword: {
        ServerLanguage.German: "Schwertknauf {0}",
        ServerLanguage.English: "Sword Pommel {0}",
        ServerLanguage.Korean: "칼머리 {0}",
        ServerLanguage.French: "Pommeau d'épée {0}",
        ServerLanguage.Italian: "Pomolo della spada {0}",
        ServerLanguage.Spanish: "Pomo de espada {0}",
        ServerLanguage.TraditionalChinese: "{0} 劍柄首",
        ServerLanguage.Japanese: "ソードの柄頭 {0}",
        ServerLanguage.Polish: "Głowica Miecza {0}",
        ServerLanguage.Russian: "Sword Pommel {0}",
        ServerLanguage.BorkBorkBork: "Svurd Pummel {0}"
    }, 
    ItemType.Wand: {
        ServerLanguage.German: "Zauberstab-Hülle {0}",
        ServerLanguage.English: "Wand Wrapping {0}",
        ServerLanguage.Korean: "지팡이자루 {0}",
        ServerLanguage.French: "Gaine de baguette {0}",
        ServerLanguage.Italian: "Fascia della Bacchetta {0}",
        ServerLanguage.Spanish: "Envoltura de varita {0}",
        ServerLanguage.TraditionalChinese: "{0} 魔杖把手",
        ServerLanguage.Japanese: "ワンドの布 {0}",
        ServerLanguage.Polish: "Okład Różdżki {0}",
        ServerLanguage.Russian: "Wand Wrapping {0}",
        ServerLanguage.BorkBorkBork: "Vund Vraeppeeng {0}"
    },
}

class WeaponSuffix(WeaponUpgrade):
    mod_type = ItemUpgradeType.Suffix
    
    @classmethod
    def get_weapon_upgrade_name(cls, item_type: ItemType, server_language: ServerLanguage = ServerLanguage(UIManager.GetIntPreference(NumberPreference.TextLanguage))) -> Optional[str]:
        if item_type in WEAPON_PREFIX_ITEM_NAME_FORMAT:
            item_type_name_formats = WEAPON_PREFIX_ITEM_NAME_FORMAT.get(item_type, {})
            item_type_name_format = item_type_name_formats.get(server_language, item_type_name_formats.get(ServerLanguage.English, item_type.name + " Upgrade of {prefix}"))
            name = cls.names.get(server_language, cls.names.get(ServerLanguage.English, f"Unknown Weapon Suffix {cls.__class__.__name__}"))
            return item_type_name_format.format(prefix=name)
        
        return None
    
class OfAttributeUpgrade(WeaponSuffix):
    id = ItemUpgrade.OfAttribute
    property_identifiers = [
        ModifierIdentifier.AttributePlusOne,
    ]
    
    names = {
		ServerLanguage.English: "of {attribute}",
		ServerLanguage.Spanish: "({attribute})",
		ServerLanguage.Italian: "dell'{attribute}",
		ServerLanguage.German: "d. {attribute}",
		ServerLanguage.Korean: "({attribute})",
		ServerLanguage.French: "({attribute})",
		ServerLanguage.TraditionalChinese: "{attribute}",
		ServerLanguage.Japanese: "({attribute})",
		ServerLanguage.Polish: "({attribute})",
		ServerLanguage.Russian: "of {attribute}",
		ServerLanguage.BorkBorkBork: "ooff {attribute}",
	}
    
    attribute : Attribute = Attribute.None_
        
    @classmethod
    def _post_compose(cls, upgrade: "Upgrade", mod: DecodedModifier, modifiers: list[DecodedModifier],) -> None:
        of_attribute_upgrade = cast("OfAttributeUpgrade", upgrade)
        attribute_property = next((p for p in upgrade.properties if isinstance(p, AttributePlusOne)), None)
        of_attribute_upgrade.attribute = attribute_property.attribute if attribute_property else Attribute.None_
    
    @property
    def name(self) -> str:
        preference = UIManager.GetIntPreference(NumberPreference.TextLanguage)
        server_language = ServerLanguage(preference)
        
        return self.names.get(server_language, self.names.get(ServerLanguage.English, self.__class__.__name__)).format(attribute=AttributeNames.get(self.attribute) if self.attribute != Attribute.None_ else "Unknown Attribute")
    
class OfAptitudeUpgrade(WeaponSuffix):
    id = ItemUpgrade.OfAptitude
    property_identifiers = [
        ModifierIdentifier.HalvesCastingTimeItemAttribute,
    ]
    names = {
		ServerLanguage.English: "of Aptitude",
		ServerLanguage.Spanish: "(de aptitud)",
		ServerLanguage.Italian: "della Perspicacia",
		ServerLanguage.German: "d. Begabung",
		ServerLanguage.Korean: "(총명)",
		ServerLanguage.French: "(d'aptitude)",
		ServerLanguage.TraditionalChinese: "天賦",
		ServerLanguage.Japanese: "(アプティテュード)",
		ServerLanguage.Polish: "(Uzdolnienia)",
		ServerLanguage.Russian: "of Aptitude",
		ServerLanguage.BorkBorkBork: "ooff Aepteetoode-a",
	}
    
class OfAxeMasteryUpgrade(WeaponSuffix):
    id = ItemUpgrade.OfAxeMastery
    property_identifiers = [
        ModifierIdentifier.AttributePlusOne,
    ]
    names = {
		ServerLanguage.English: "of Axe Mastery",
		ServerLanguage.Spanish: "(Dominio del hacha)",
		ServerLanguage.Italian: "Abilità con l'Ascia",
		ServerLanguage.German: "d. Axtbeherrschung",
		ServerLanguage.Korean: "(도끼술)",
		ServerLanguage.French: "(Maîtrise de la hache)",
		ServerLanguage.TraditionalChinese: "精通斧術",
		ServerLanguage.Japanese: "(アックス マスタリー)",
		ServerLanguage.Polish: "(Biegłość w Toporach)",
		ServerLanguage.Russian: "of Axe Mastery",
		ServerLanguage.BorkBorkBork: "ooff Aexe-a Maestery",
	}
    
class OfDaggerMasteryUpgrade(WeaponSuffix):
    id = ItemUpgrade.OfDaggerMastery
    property_identifiers = [
        ModifierIdentifier.AttributePlusOne,
    ]   
    names = {
		ServerLanguage.English: "of Dagger Mastery",
		ServerLanguage.Spanish: "(Dominio de la daga)",
		ServerLanguage.Italian: "Abilità con il Pugnale",
		ServerLanguage.German: "d. Dolchbeherrschung",
		ServerLanguage.Korean: "(단검술)",
		ServerLanguage.French: "(Maîtrise de la dague)",
		ServerLanguage.TraditionalChinese: "匕首精通",
		ServerLanguage.Japanese: "(ダガー マスタリー)",
		ServerLanguage.Polish: "(Biegłość w Sztyletach)",
		ServerLanguage.Russian: "of Dagger Mastery",
		ServerLanguage.BorkBorkBork: "ooff Daegger Maestery",
	}
    
class OfDefenseUpgrade(WeaponSuffix):
    id = ItemUpgrade.OfDefense
    property_identifiers = [
        ModifierIdentifier.ArmorPlus,
    ]
    names = {
		ServerLanguage.English: "of Defense",
		ServerLanguage.Spanish: "(de protección)",
		ServerLanguage.Italian: "di Difesa",
		ServerLanguage.German: "d. Verteidigung",
		ServerLanguage.Korean: "(방어)",
		ServerLanguage.French: "(de Défense)",
		ServerLanguage.TraditionalChinese: "防衛",
		ServerLanguage.Japanese: "(ディフェンス)",
		ServerLanguage.Polish: "(Obrony)",
		ServerLanguage.Russian: "of Defense",
		ServerLanguage.BorkBorkBork: "ooff Deffense-a",
	}
    
class OfDevotionUpgrade(WeaponSuffix):
    id = ItemUpgrade.OfDevotion
    property_identifiers = [
        ModifierIdentifier.HealthPlusEnchanted,
    ]
    names = {
		ServerLanguage.English: "of Devotion",
		ServerLanguage.Spanish: "(de devoción)",
		ServerLanguage.Italian: "della Devozione",
		ServerLanguage.German: "d. Hingabe",
		ServerLanguage.Korean: "(헌신)",
		ServerLanguage.French: "(de dévotion)",
		ServerLanguage.TraditionalChinese: "奉獻",
		ServerLanguage.Japanese: "(ディボーション)",
		ServerLanguage.Polish: "(Oddania)",
		ServerLanguage.Russian: "of Devotion",
		ServerLanguage.BorkBorkBork: "ooff Defushun",
	}
    
class OfEnchantingUpgrade(WeaponSuffix):
    id = ItemUpgrade.OfEnchanting
    property_identifiers = [
        ModifierIdentifier.IncreaseEnchantmentDuration,
    ]
    names = {
		ServerLanguage.English: "of Enchanting",
		ServerLanguage.Spanish: "(de encantamientos)",
		ServerLanguage.Italian: "dell'Incantesimo",
		ServerLanguage.German: "d. Verzauberung",
		ServerLanguage.Korean: "(강화)",
		ServerLanguage.French: "(d'Enchantement)",
		ServerLanguage.TraditionalChinese: "附魔",
		ServerLanguage.Japanese: "(エンチャント)",
		ServerLanguage.Polish: "(Zaklinania)",
		ServerLanguage.Russian: "of Enchanting",
		ServerLanguage.BorkBorkBork: "ooff Inchunteeng",
	}
    
class OfEnduranceUpgrade(WeaponSuffix):
    id = ItemUpgrade.OfEndurance
    property_identifiers = [
        ModifierIdentifier.HealthPlusStance,
    ]
    names = {
		ServerLanguage.English: "of Endurance",
		ServerLanguage.Spanish: "(de resistencia)",
		ServerLanguage.Italian: "della Resistenza",
		ServerLanguage.German: "d. Ausdauer",
		ServerLanguage.Korean: "(인내)",
		ServerLanguage.French: "(d'endurance)",
		ServerLanguage.TraditionalChinese: "忍耐",
		ServerLanguage.Japanese: "(インデュランス)",
		ServerLanguage.Polish: "(Wytrzymałości)",
		ServerLanguage.Russian: "of Endurance",
		ServerLanguage.BorkBorkBork: "ooff Indoorunce-a",
	}
    
class OfFortitudeUpgrade(WeaponSuffix):
    id = ItemUpgrade.OfFortitude
    property_identifiers = [
        ModifierIdentifier.HealthPlus,
    ]
    names = {
		ServerLanguage.English: "of Fortitude",
		ServerLanguage.Spanish: "(con poder)",
		ServerLanguage.Italian: "del Coraggio",
		ServerLanguage.German: "d. Tapferkeit",
		ServerLanguage.Korean: "(견고)",
		ServerLanguage.French: "(de Courage)",
		ServerLanguage.TraditionalChinese: "堅忍",
		ServerLanguage.Japanese: "(フォーティチュード)",
		ServerLanguage.Polish: "(Wytrwałości)",
		ServerLanguage.Russian: "of Fortitude",
		ServerLanguage.BorkBorkBork: "ooff Furteetoode-a",
	}
    
class OfHammerMasteryUpgrade(WeaponSuffix):
    id = ItemUpgrade.OfHammerMastery
    property_identifiers = [
        ModifierIdentifier.AttributePlusOne,
    ]
    names = {
		ServerLanguage.English: "of Hammer Mastery",
		ServerLanguage.Spanish: "(Dominio del martillo)",
		ServerLanguage.Italian: "Abilità col Martello",
		ServerLanguage.German: "d. Hammerbeherrschung",
		ServerLanguage.Korean: "(해머술)",
		ServerLanguage.French: "(Maîtrise du marteau)",
		ServerLanguage.TraditionalChinese: "精通鎚術",
		ServerLanguage.Japanese: "(ハンマー マスタリー)",
		ServerLanguage.Polish: "(Biegłość w Młotach)",
		ServerLanguage.Russian: "of Hammer Mastery",
		ServerLanguage.BorkBorkBork: "ooff Haemmer Maestery",
	}
    
class OfMarksmanshipUpgrade(WeaponSuffix):
    id = ItemUpgrade.OfMarksmanship
    property_identifiers = [
        ModifierIdentifier.AttributePlusOne,
    ]
    names = {
		ServerLanguage.English: "of Marksmanship",
		ServerLanguage.Spanish: "(Puntería)",
		ServerLanguage.Italian: "Precisione",
		ServerLanguage.German: "d. Treffsicherheit",
		ServerLanguage.Korean: "(궁술)",
		ServerLanguage.French: "(Adresse au tir)",
		ServerLanguage.TraditionalChinese: "弓術精通",
		ServerLanguage.Japanese: "(ボウ マスタリー)",
		ServerLanguage.Polish: "(Umiejętności Strzeleckie)",
		ServerLanguage.Russian: "of Marksmanship",
		ServerLanguage.BorkBorkBork: "ooff Maerksmunsheep",
	}
    
class OfMasteryUpgrade(WeaponSuffix):
    id = ItemUpgrade.OfMastery
    property_identifiers = [
        ModifierIdentifier.AttributePlusOneItem,
    ]
    names = {
		ServerLanguage.English: "of Mastery",
		ServerLanguage.Spanish: "(de maestría)",
		ServerLanguage.Italian: "della Destrezza da Difesa",
		ServerLanguage.German: "d. Beherrschung",
		ServerLanguage.Korean: "(지배)",
		ServerLanguage.French: "(de maîtrise)",
		ServerLanguage.TraditionalChinese: "支配",
		ServerLanguage.Japanese: "(マスタリー)",
		ServerLanguage.Polish: "(Mistrzostwa)",
		ServerLanguage.Russian: "of Mastery",
		ServerLanguage.BorkBorkBork: "ooff Maestery",
	}
    
class OfMemoryUpgrade(WeaponSuffix):
    id = ItemUpgrade.OfMemory
    property_identifiers = [
        ModifierIdentifier.HalvesSkillRechargeItemAttribute,
    ]
    names = {
		ServerLanguage.English: "of Memory",
		ServerLanguage.Spanish: "(de memoria)",
		ServerLanguage.Italian: "della Memoria",
		ServerLanguage.German: "d. Erinnerung",
		ServerLanguage.Korean: "(기억)",
		ServerLanguage.French: "(de mémoire)",
		ServerLanguage.TraditionalChinese: "記憶",
		ServerLanguage.Japanese: "(メモリー)",
		ServerLanguage.Polish: "(Pamięci)",
		ServerLanguage.Russian: "of Memory",
		ServerLanguage.BorkBorkBork: "ooff Memury",
	}
class OfQuickeningUpgrade(WeaponSuffix):
    id = ItemUpgrade.OfQuickening
    property_identifiers = [
        ModifierIdentifier.HalvesSkillRechargeGeneral,
    ]
    names = {
		ServerLanguage.English: "of Quickening",
		ServerLanguage.Spanish: "(de aceleración)",
		ServerLanguage.Italian: "dell'Accelerazione",
		ServerLanguage.German: "d. Beschleunigung",
		ServerLanguage.Korean: "(활기)",
		ServerLanguage.French: "(de rapidité)",
		ServerLanguage.TraditionalChinese: "復甦",
		ServerLanguage.Japanese: "(クイックニング)",
		ServerLanguage.Polish: "(Przyspieszenia)",
		ServerLanguage.Russian: "of Quickening",
		ServerLanguage.BorkBorkBork: "ooff Qooeeckeneeng",
	}
    
class OfScytheMasteryUpgrade(WeaponSuffix):
    id = ItemUpgrade.OfScytheMastery
    property_identifiers = [
        ModifierIdentifier.AttributePlusOne,
    ]
    names = {
		ServerLanguage.English: "of Scythe Mastery",
		ServerLanguage.Spanish: "(Dominio de la guadaña)",
		ServerLanguage.Italian: "Abilità con la Falce",
		ServerLanguage.German: "d. Sensenbeherrschung",
		ServerLanguage.Korean: "(사이드술)",
		ServerLanguage.French: "(Maîtrise de la faux)",
		ServerLanguage.TraditionalChinese: "鐮刀精通",
		ServerLanguage.Japanese: "(サイズ マスタリー)",
		ServerLanguage.Polish: "(Biegłość w Kosach)",
		ServerLanguage.Russian: "of Scythe Mastery",
		ServerLanguage.BorkBorkBork: "ooff Scyzee Maestery",
	}
    
class OfShelterUpgrade(WeaponSuffix):
    id = ItemUpgrade.OfShelter
    property_identifiers = [
        ModifierIdentifier.ArmorPlusVsPhysical,
    ]
    names = {
		ServerLanguage.English: "of Shelter",
		ServerLanguage.Spanish: "(de refugio)",
		ServerLanguage.Italian: "del Riparo",
		ServerLanguage.German: "d. Zuflucht",
		ServerLanguage.Korean: "(보호)",
		ServerLanguage.French: "(de Refuge)",
		ServerLanguage.TraditionalChinese: "庇護",
		ServerLanguage.Japanese: "(シェルター)",
		ServerLanguage.Polish: "(Ochrony)",
		ServerLanguage.Russian: "of Shelter",
		ServerLanguage.BorkBorkBork: "ooff Shelter",
	}
    
class OfSlayingUpgrade(WeaponSuffix):
    id = ItemUpgrade.OfSlaying
    
    property_identifiers = [
        ModifierIdentifier.DamagePlusVsSpecies,
        # ModifierIdentifier.BaneSpecies,
    ]
    
    names_by_species = {
        ItemBaneSpecies.Undead: {
            ServerLanguage.German: "d. Todesfluches",
            ServerLanguage.English: "of Deathbane",
            ServerLanguage.Korean: "(언데드 상대 무기)",
            ServerLanguage.French: "(anti-mort)",
            ServerLanguage.Italian: "del Flagello Mortale",
            ServerLanguage.Spanish: "(matamuertos)",
            ServerLanguage.TraditionalChinese: "不死族剋星",
            ServerLanguage.Japanese: "(デスベイン)",
            ServerLanguage.Polish: "(Zabijania Nieumarłych)",
            ServerLanguage.Russian: "of Deathbane",
            ServerLanguage.BorkBorkBork: "ooff Deaethbune-a"
        },
        
        ItemBaneSpecies.Charr: {
            ServerLanguage.English: "of Charrslaying",
        },
        
        ItemBaneSpecies.Trolls: {
            ServerLanguage.English: "of Trollslaying",
        },
        
        ItemBaneSpecies.Plants: {            
            ServerLanguage.German: "d. Pflanzentötung",
            ServerLanguage.English: "of Pruning",
            ServerLanguage.Korean: "(식물 상대 무기)",
            ServerLanguage.French: "(anti-plantes)",
            ServerLanguage.Italian: "del martello da Sfoltimento",
            ServerLanguage.Spanish: "(mataplantas)",
            ServerLanguage.TraditionalChinese: "枝葉修整",
            ServerLanguage.Japanese: "(プルーニング)",
            ServerLanguage.Polish: "(Obcinania)",
            ServerLanguage.Russian: "of Pruning",
            ServerLanguage.BorkBorkBork: "ooff Prooneeng"
        },
        
        ItemBaneSpecies.Skeletons: {
            ServerLanguage.English: "of Skeletonslaying",
        },
        
        ItemBaneSpecies.Giants: {
            ServerLanguage.English: "of Giantslaying",
        },
        
        ItemBaneSpecies.Dwarves: {
            ServerLanguage.English: "of Dwarfslaying",
        },
        
        ItemBaneSpecies.Tengus: {
            ServerLanguage.English: "of Tenguslaying",
        },
        
        ItemBaneSpecies.Demons: {
            ServerLanguage.German: "d. Dämonentötung",
            ServerLanguage.English: "of Demonslaying",
            ServerLanguage.Korean: "(데몬 상대 무기)",
            ServerLanguage.French: "(anti-démons)",
            ServerLanguage.Italian: "dell'arco Ammazza-demoni",
            ServerLanguage.Spanish: "(matademonios)",
            ServerLanguage.TraditionalChinese: "惡魔殺手",
            ServerLanguage.Japanese: "(デーモン キラー)",
            ServerLanguage.Polish: "(Zabijania Demonów)",
            ServerLanguage.Russian: "of Demonslaying",
            ServerLanguage.BorkBorkBork: "ooff Demunslaeyeeng"
        },
        
        ItemBaneSpecies.Dragons: {
            ServerLanguage.English: "of Dragonslaying",
        },
        
        ItemBaneSpecies.Ogres: {
            ServerLanguage.English: "of Ogreslaying",
        },
    }
    
    @property
    def name(self) -> str:
        species_property = next((p for p in self.properties if isinstance(p, DamagePlusVsSpecies)), None)
        species = species_property.species if species_property else ItemBaneSpecies.Unknown
        preference = UIManager.GetIntPreference(NumberPreference.TextLanguage)
        server_language = ServerLanguage(preference)
        name_by_species = self.names_by_species.get(species, {})
        return name_by_species.get(server_language, name_by_species.get(ServerLanguage.English, f"Unknown Slaying Suffix for {species.name}"))

class OfSpearMasteryUpgrade(WeaponSuffix):
    id = ItemUpgrade.OfSpearMastery
    property_identifiers = [
        ModifierIdentifier.AttributePlusOne,
    ]
    names = {
		ServerLanguage.English: "of Spear Mastery",
		ServerLanguage.Spanish: "(Dominio de la lanza)",
		ServerLanguage.Italian: "Abilità con la Lancia",
		ServerLanguage.German: "d. Speerbeherrschung",
		ServerLanguage.Korean: "(창술)",
		ServerLanguage.French: "(Maîtrise du javelot)",
		ServerLanguage.TraditionalChinese: "矛術精通",
		ServerLanguage.Japanese: "(スピア マスタリー)",
		ServerLanguage.Polish: "(Biegłość we Włóczniach)",
		ServerLanguage.Russian: "of Spear Mastery",
		ServerLanguage.BorkBorkBork: "ooff Speaer Maestery",
	}
    
class OfSwiftnessUpgrade(WeaponSuffix):
    id = ItemUpgrade.OfSwiftness
    property_identifiers = [
        ModifierIdentifier.HalvesCastingTimeGeneral,
    ]
    names = {
		ServerLanguage.English: "of Swiftness",
		ServerLanguage.Spanish: "(de rapidez)",
		ServerLanguage.Italian: "della Rapidità",
		ServerLanguage.German: "d. Eile",
		ServerLanguage.Korean: "(신속)",
		ServerLanguage.French: "(de Rapidité)",
		ServerLanguage.TraditionalChinese: "迅捷",
		ServerLanguage.Japanese: "(スウィフトネス)",
		ServerLanguage.Polish: "(Szybkości)",
		ServerLanguage.Russian: "of Swiftness",
		ServerLanguage.BorkBorkBork: "ooff Sveefftness",
	}
    
class OfSwordsmanshipUpgrade(WeaponSuffix):
    id = ItemUpgrade.OfSwordsmanship
    property_identifiers = [
        ModifierIdentifier.AttributePlusOne,
    ]
    names = {
		ServerLanguage.English: "of Swordsmanship",
		ServerLanguage.Spanish: "(Esgrima)",
		ServerLanguage.Italian: "Scherma",
		ServerLanguage.German: "d. Schwertkunst",
		ServerLanguage.Korean: "(검술)",
		ServerLanguage.French: "(Maîtrise de l'épée)",
		ServerLanguage.TraditionalChinese: "精通劍術",
		ServerLanguage.Japanese: "(ソード マスタリー)",
		ServerLanguage.Polish: "(Biegłość w Mieczach)",
		ServerLanguage.Russian: "of Swordsmanship",
		ServerLanguage.BorkBorkBork: "ooff Svurdsmunsheep",
	}
    
class OfTheProfessionUpgrade(WeaponSuffix):
    id = ItemUpgrade.OfTheProfession
    
    property_identifiers = [
        ModifierIdentifier.OfTheProfession,
    ]
        
    names = {
		ServerLanguage.English: "of the {profession}",
		ServerLanguage.Spanish: "(el {profession})",
		ServerLanguage.Italian: "dell'arco il {profession}",
		ServerLanguage.German: "d. des {profession}",
		ServerLanguage.Korean: "({profession})",
		ServerLanguage.French: "(le {profession})",
		ServerLanguage.TraditionalChinese: "{profession}",
		ServerLanguage.Japanese: "({profession})",
		ServerLanguage.Polish: "({profession})",
		ServerLanguage.Russian: "of {profession}",
		ServerLanguage.BorkBorkBork: "ooff zee {profession}",
	}
    
    profession : Profession = Profession._None
    
    @classmethod
    def _post_compose(cls, upgrade: "Upgrade", mod: DecodedModifier, modifiers: list[DecodedModifier],) -> None:
        of_the_profession_upgrade = cast("OfTheProfessionUpgrade", upgrade)
        profession_property = next((p for p in upgrade.properties if isinstance(p, OfTheProfession)), None)
        of_the_profession_upgrade.profession = profession_property.profession if profession_property else Profession._None
    
    @property
    def name(self) -> str:
        preference = UIManager.GetIntPreference(NumberPreference.TextLanguage)
        server_language = ServerLanguage(preference)
        
        return self.names.get(server_language, self.names.get(ServerLanguage.English, self.__class__.__name__)).format(profession=self.profession.name if self.profession != Profession._None else "Unknown Profession")
    
    
    
class OfValorUpgrade(WeaponSuffix):
    id = ItemUpgrade.OfValor
    property_identifiers = [
        ModifierIdentifier.HealthPlusHexed,
    ]
    names = {
		ServerLanguage.English: "of Valor",
		ServerLanguage.Spanish: "(de valor)",
		ServerLanguage.Italian: "del Valore",
		ServerLanguage.German: "d. Wertschätzung",
		ServerLanguage.Korean: "(용맹)",
		ServerLanguage.French: "(de valeur)",
		ServerLanguage.TraditionalChinese: "英勇",
		ServerLanguage.Japanese: "(ヴァラー)",
		ServerLanguage.Polish: "(Odwagi)",
		ServerLanguage.Russian: "of Valor",
		ServerLanguage.BorkBorkBork: "ooff Faelur",
	}
    
class OfWardingUpgrade(WeaponSuffix):
    id = ItemUpgrade.OfWarding
    property_identifiers = [
        ModifierIdentifier.ArmorPlusVsElemental,
    ]
    names = {
		ServerLanguage.English: "of Warding",
		ServerLanguage.Spanish: "(de guardia)",
		ServerLanguage.Italian: "della Protezione",
		ServerLanguage.German: "d. Abwehr",
		ServerLanguage.Korean: "(결계)",
		ServerLanguage.French: "(du Protecteur)",
		ServerLanguage.TraditionalChinese: "結界",
		ServerLanguage.Japanese: "(ウォーディング)",
		ServerLanguage.Polish: "(Zapobiegliwości)",
		ServerLanguage.Russian: "of Warding",
		ServerLanguage.BorkBorkBork: "ooff Vaerdeeng",
	}
#endregion Suffixes

#region Inscriptions
class Inscription(Upgrade):
    mod_type = ItemUpgradeType.Inscription
    inventory_icon : str
    id : ItemUpgrade
    names : dict[ServerLanguage, str] = {}
    target_item_type : ItemType
    
    INSCRIPTION_LOCALIZATION = {
            ServerLanguage.English: "Inscription: {name}",
            ServerLanguage.German: "Inschrift: {name}",
            ServerLanguage.French: "Inscription : {name}",
            ServerLanguage.Spanish: "Inscripción: {name}",
            ServerLanguage.Italian: "Iscrizione: {name}",
            ServerLanguage.TraditionalChinese: "鑄印：{name}",
            ServerLanguage.Korean: "마력석: {name}",
            ServerLanguage.Japanese: "刻印：{name}",
            ServerLanguage.Polish: "Inskrypcja: {name}",
            ServerLanguage.Russian: "Надпись: {name}",
            ServerLanguage.BorkBorkBork: "Inscreepshun: {name}"
        }
    
    @classmethod
    def has_id(cls, upgrade_id: ItemUpgradeId) -> bool:
        return cls.id.has_id(upgrade_id)
    
    @property
    def name(self) -> str:
        language = ServerLanguage(UIManager.GetIntPreference(NumberPreference.TextLanguage))
        inscription_format = self.INSCRIPTION_LOCALIZATION.get(language, self.INSCRIPTION_LOCALIZATION[ServerLanguage.English])
        return inscription_format.format(name=self.names.get(language, self.names.get(ServerLanguage.English, "")))

#region Offhand
class BeJustAndFearNot(Inscription):
    id = ItemUpgrade.BeJustAndFearNot
    target_item_type = ItemType.Offhand
    property_identifiers = [
        ModifierIdentifier.ArmorPlusHexed,
    ]
    names = {
		ServerLanguage.English: "\"Be Just and Fear Not\"",
	}
    
class DownButNotOut(Inscription):
    id = ItemUpgrade.DownButNotOut
    target_item_type = ItemType.Offhand
    property_identifiers = [
        ModifierIdentifier.ArmorPlusWhileDown
    ]
    names = {
		ServerLanguage.English: "\"Down But Not Out\"",
	}
    
class FaithIsMyShield(Inscription):
    id = ItemUpgrade.FaithIsMyShield
    target_item_type = ItemType.Offhand
    property_identifiers = [
        ModifierIdentifier.ArmorPlusEnchanted,
    ]
    names = {
		ServerLanguage.English: "\"Faith is My Shield\"",
		ServerLanguage.Spanish: "\"La fe es mi escudo\"",
		ServerLanguage.Italian: "\"La Fede è il Mio Scudo\"",
		ServerLanguage.German: "\"Der Glaube ist mein Schild!\"",
		ServerLanguage.Korean: "신념은 나의 방패다",
		ServerLanguage.French: "\"La foi est mon bouclier\"",
		ServerLanguage.TraditionalChinese: "\"信念是盾\"",
		ServerLanguage.Japanese: "フェイス イズ マイ シールド",
		ServerLanguage.Polish: "\"Wiara jest mą tarczą\"",
		ServerLanguage.Russian: "\"Вера послужит мне щитом\"",
		ServerLanguage.BorkBorkBork: "\"Faeeet is My Sheeeld\"",
	}
    
class ForgetMeNot(Inscription):
    id = ItemUpgrade.ForgetMeNot
    target_item_type = ItemType.Offhand
    property_identifiers = [
        ModifierIdentifier.HalvesSkillRechargeItemAttribute,
    ]
    names = {
		ServerLanguage.English: "\"Forget Me Not\"",
		ServerLanguage.Spanish: "\"No me olvides\"",
		ServerLanguage.Italian: "\"Non Ti Scordar di Me\"",
		ServerLanguage.German: "\"Vergesst mein nicht!\"",
		ServerLanguage.Korean: "물망초",
		ServerLanguage.French: "\"Souvenir gravé à jamais\"",
		ServerLanguage.TraditionalChinese: "\"勿忘我\"",
		ServerLanguage.Japanese: "フォーゲット ミー ノット",
		ServerLanguage.Polish: "\"Nie zapomnij mnie\"",
		ServerLanguage.Russian: "\"Незабудка\"",
		ServerLanguage.BorkBorkBork: "\"Furget Me-a Nut\"",
	}
    
class HailToTheKing(Inscription):
    id = ItemUpgrade.HailToTheKing
    target_item_type = ItemType.Offhand
    property_identifiers = [
        ModifierIdentifier.ArmorPlusAbove,
    ]
    names = {
		ServerLanguage.English: "\"Hail to the King\"",
		ServerLanguage.Spanish: "\"Viva el rey\"",
		ServerLanguage.Italian: "\"Viva il Re\"",
		ServerLanguage.German: "\"Gelobt sei der König\"",
		ServerLanguage.Korean: "국왕 폐하 만세",
		ServerLanguage.French: "\"Longue vie au roi\"",
		ServerLanguage.TraditionalChinese: "\"與王致敬\"",
		ServerLanguage.Japanese: "ヘイル トゥ ザ キング",
		ServerLanguage.Polish: "\"Niech żyje król\"",
		ServerLanguage.Russian: "\"Да здравствует король!\"",
		ServerLanguage.BorkBorkBork: "\"Haeeel tu zee Keeng\"",
	}
    
class IgnoranceIsBliss(Inscription):
    id = ItemUpgrade.IgnoranceIsBliss
    target_item_type = ItemType.Offhand
    property_identifiers = [
        ModifierIdentifier.ArmorPlus,
        ModifierIdentifier.EnergyMinus,
    ]
    names = {
		ServerLanguage.English: "\"Ignorance is Bliss\"",
		ServerLanguage.Spanish: "\"La ignorancia es felicidad\"",
		ServerLanguage.Italian: "\"Benedetta Ignoranza\"",
		ServerLanguage.German: "\"Was ich nicht weiß ...\"",
		ServerLanguage.Korean: "모르는 게 약이다",
		ServerLanguage.French: "\"Il vaut mieux ne pas savoir\"",
		ServerLanguage.TraditionalChinese: "\"傻人有傻福\"",
		ServerLanguage.Japanese: "イグノーランス イズ ブリス",
		ServerLanguage.Polish: "\"Ignorancja jest błogosławieństwem\"",
		ServerLanguage.Russian: "\"Счастлив в неведении\"",
		ServerLanguage.BorkBorkBork: "\"Ignurunce-a is Bleess\"",
	}
    
class KnowingIsHalfTheBattle(Inscription):
    id = ItemUpgrade.KnowingIsHalfTheBattle
    target_item_type = ItemType.Offhand
    property_identifiers = [
        ModifierIdentifier.ArmorPlusCasting,
    ]
    names = {
		ServerLanguage.English: "\"Knowing is Half the Battle\"",
	}
    
class LifeIsPain(Inscription):
    id = ItemUpgrade.LifeIsPain
    target_item_type = ItemType.Offhand
    property_identifiers = [
        ModifierIdentifier.ArmorPlus,
        ModifierIdentifier.HealthMinus,
    ]
    names = {
		ServerLanguage.English: "\"Life is Pain\"",
	}
    
class LiveForToday(Inscription):
    id = ItemUpgrade.LiveForToday
    target_item_type = ItemType.Offhand
    property_identifiers = [
        ModifierIdentifier.EnergyPlus,
        ModifierIdentifier.EnergyDegen,
    ]
    names = {
		ServerLanguage.English: "\"Live for Today\"",
		ServerLanguage.Spanish: "\"Vive el presente\"",
		ServerLanguage.Italian: "\"Vivi alla Giornata\"",
		ServerLanguage.German: "\"Lebt den Tag\"",
		ServerLanguage.Korean: "오늘을 위해 최선을",
		ServerLanguage.French: "\"Aujourd'hui, la vie\"",
		ServerLanguage.TraditionalChinese: "\"活在當下\"",
		ServerLanguage.Japanese: "リブ フォー トゥデイ",
		ServerLanguage.Polish: "\"Żyj dniem dzisiejszym\"",
		ServerLanguage.Russian: "\"Живи сегодняшним днем\"",
		ServerLanguage.BorkBorkBork: "\"Leefe-a fur Tudaey\"",
	}
    
class ManForAllSeasons(Inscription):
    id = ItemUpgrade.ManForAllSeasons
    target_item_type = ItemType.Offhand
    property_identifiers = [
        ModifierIdentifier.ArmorPlusVsElemental,
    ]
    names = {
		ServerLanguage.English: "\"Man for All Seasons\"",
	}
    
class MightMakesRight(Inscription):
    id = ItemUpgrade.MightMakesRight
    target_item_type = ItemType.Offhand
    property_identifiers = [
        ModifierIdentifier.ArmorPlusAttacking,
    ]
    names = {
		ServerLanguage.English: "\"Might Makes Right\"",
	}
    
class SerenityNow(Inscription):
    id = ItemUpgrade.SerenityNow
    target_item_type = ItemType.Offhand
    property_identifiers = [
        ModifierIdentifier.HalvesSkillRechargeGeneral,
    ]
    names = {
		ServerLanguage.English: "\"Serenity Now\"",
		ServerLanguage.Spanish: "\"Calma ahora\"",
		ServerLanguage.Italian: "\"Serenità Immediata\"",
		ServerLanguage.German: "\"Auf die Gelassenheit\"",
		ServerLanguage.Korean: "평정을 찾아라",
		ServerLanguage.French: "\"Un peu de sérénité\"",
		ServerLanguage.TraditionalChinese: "\"平靜\"",
		ServerLanguage.Japanese: "セレニティ ナウ",
		ServerLanguage.Polish: "\"Niech nastanie spokój\"",
		ServerLanguage.Russian: "\"Спокойствие, только спокойствие!\"",
		ServerLanguage.BorkBorkBork: "\"Sereneety Noo\"",
	}
    
class SurvivalOfTheFittest(Inscription):
    id = ItemUpgrade.SurvivalOfTheFittest
    target_item_type = ItemType.Offhand
    property_identifiers = [
        ModifierIdentifier.ArmorPlusVsPhysical,
    ]
    names = {
		ServerLanguage.English: "\"Survival of the Fittest\"",
		ServerLanguage.Spanish: "\"Supervivencia del más fuerte\"",
		ServerLanguage.Italian: "\"Sopravvivenza Integrale\"",
		ServerLanguage.German: "\"Hart wie Stahl\"",
		ServerLanguage.Korean: "적자생존",
		ServerLanguage.French: "\"La survie du plus fort\"",
		ServerLanguage.TraditionalChinese: "\"適者生存\"",
		ServerLanguage.Japanese: "サバイバル オブ ザ フィッテスト",
		ServerLanguage.Polish: "\"Przetrwają najsilniejsi\"",
		ServerLanguage.Russian: "\"Естественный отбор\"",
		ServerLanguage.BorkBorkBork: "\"Soorfeefael ooff zee Feettest\"",
	}
#endregion Offhand

#region Weapon

class BrawnOverBrains(Inscription):
    id = ItemUpgrade.BrawnOverBrains
    target_item_type = ItemType.Weapon
    property_identifiers = [
        ModifierIdentifier.DamagePlusPercent,
        ModifierIdentifier.EnergyMinus,
    ]
    names = {
		ServerLanguage.English: "\"Brawn over Brains\"",
		ServerLanguage.Spanish: "\"Más vale maña que fuerza\"",
		ServerLanguage.Italian: "\"Più Muscoli che Cervello\"",
		ServerLanguage.German: "\"Körper über Geist\"",
		ServerLanguage.Korean: "힘보다는 머리",
		ServerLanguage.French: "\"Tout en muscles\"",
		ServerLanguage.TraditionalChinese: "\"有勇無謀\"",
		ServerLanguage.Japanese: "ブローン オーバー ブレイン",
		ServerLanguage.Polish: "\"Siła ponad umysł\"",
		ServerLanguage.Russian: "\"Сила есть -ума не надо\"",
		ServerLanguage.BorkBorkBork: "\"Braevn oofer Braeeens\"",
	}
        
class DanceWithDeath(Inscription):
    id = ItemUpgrade.DanceWithDeath
    target_item_type = ItemType.Weapon
    property_identifiers = [
        ModifierIdentifier.DamagePlusStance,
    ]
    names = {
		ServerLanguage.English: "\"Dance with Death\"",
		ServerLanguage.Spanish: "\"Baila con la muerte\"",
		ServerLanguage.Italian: "\"Balla coi Lutti\"",
		ServerLanguage.German: "\"Tanz mit dem Tod\"",
		ServerLanguage.Korean: "마력석: 죽음과 함께 춤을",
		ServerLanguage.French: "\"Danse avec la mort\"",
		ServerLanguage.TraditionalChinese: "\"與死亡共舞\"",
		ServerLanguage.Japanese: "ダンス ウィズ デス",
		ServerLanguage.Polish: "\"Taniec ze śmiercią\"",
		ServerLanguage.Russian: "\"Танец со смертью\"",
		ServerLanguage.BorkBorkBork: "\"Dunce-a veet Deaet\"",
	}
         
class DontFearTheReaper(Inscription):
    id = ItemUpgrade.DontFearTheReaper
    target_item_type = ItemType.Weapon
    property_identifiers = [
        ModifierIdentifier.DamagePlusHexed,
    ]
    names = {
		ServerLanguage.English: "\"Don't Fear the Reaper\"",
		ServerLanguage.Spanish: "\"No temas la guadaña\"",
		ServerLanguage.Italian: "\"Non Temere la Falce\"",
		ServerLanguage.German: "\"Keine Angst vorm Sensenmann\"",
		ServerLanguage.Korean: "사신을 두려워하지 마라",
		ServerLanguage.French: "\"Ne craignez pas le Faucheur\"",
		ServerLanguage.TraditionalChinese: "\"無懼死亡\"",
		ServerLanguage.Japanese: "ドント フィアー ザ リーパー",
		ServerLanguage.Polish: "\"Nie bój się żniwiarza\"",
		ServerLanguage.Russian: "\"Не бойся жнеца\"",
		ServerLanguage.BorkBorkBork: "\"Dun't Feaer zee Reaeper\"",
	}
    
class DontThinkTwice(Inscription):
    id = ItemUpgrade.DontThinkTwice
    target_item_type = ItemType.Weapon
    property_identifiers = [
        ModifierIdentifier.HalvesCastingTimeGeneral,
    ]
    names = {
		ServerLanguage.English: "\"Don't Think Twice\"",
		ServerLanguage.Spanish: "\"No te lo pienses\"",
		ServerLanguage.Italian: "\"Non Pensarci Due Volte\"",
		ServerLanguage.German: "\"Zauderei ist keine Zier\"",
		ServerLanguage.Korean: "두 번 생각하지 마라",
		ServerLanguage.French: "\"Pas le temps de réfléchir\"",
		ServerLanguage.TraditionalChinese: "\"別再考慮\"",
		ServerLanguage.Japanese: "ドント シンク トゥワイス",
		ServerLanguage.Polish: "\"Nie zastanawiaj się\"",
		ServerLanguage.Russian: "\"А что тут думать?\"",
		ServerLanguage.BorkBorkBork: "\"Dun't Theenk Tveece-a\"",
	}
    
class GuidedByFate(Inscription):
    id = ItemUpgrade.GuidedByFate
    target_item_type = ItemType.Weapon
    property_identifiers = [
        ModifierIdentifier.DamagePlusEnchanted,
    ]
    names = {
		ServerLanguage.English: "\"Guided by Fate\"",
		ServerLanguage.Spanish: "\"Guiado por el destino\"",
		ServerLanguage.Italian: "\"Guidato dal Fato\"",
		ServerLanguage.German: "\"Wink des Schicksals\"",
		ServerLanguage.Korean: "마력석: 운명의 이끌림",
		ServerLanguage.French: "\"Soyez maître de votre destin\"",
		ServerLanguage.TraditionalChinese: "\"命運\"",
		ServerLanguage.Japanese: "ガイデッド バイ フェイト",
		ServerLanguage.Polish: "\"Prowadzi mnie przeznaczenie\"",
		ServerLanguage.Russian: "\"Ведомый роком\"",
		ServerLanguage.BorkBorkBork: "\"Gooeeded by Faete-a\"",
	}
    
class StrengthAndHonor(Inscription):
    id = ItemUpgrade.StrengthAndHonor
    target_item_type = ItemType.Weapon
    property_identifiers = [
        ModifierIdentifier.DamagePlusWhileUp,
    ]
    names = {
		ServerLanguage.English: "\"Strength and Honor\"",
		ServerLanguage.Spanish: "\"Fuerza y honor\"",
		ServerLanguage.Italian: "\"Forza e Onore\"",
		ServerLanguage.German: "\"Stärke und Ehre\"",
		ServerLanguage.Korean: "마력석: 힘과 명예",
		ServerLanguage.French: "\"Force et honneur\"",
		ServerLanguage.TraditionalChinese: "\"力與榮耀\"",
		ServerLanguage.Japanese: "ストレングス アンド オナー",
		ServerLanguage.Polish: "\"Siła i honor\"",
		ServerLanguage.Russian: "\"Сила и честь\"",
		ServerLanguage.BorkBorkBork: "\"Strengt und Hunur\"",
	}
    
class ToThePain(Inscription):
    id = ItemUpgrade.ToThePain
    target_item_type = ItemType.Weapon
    property_identifiers = [
        ModifierIdentifier.DamagePlusPercent,
        ModifierIdentifier.ArmorMinusAttacking
    ]
    names = {
		ServerLanguage.English: "\"To the Pain!\"",
		ServerLanguage.Spanish: "\"¡A que duele!\"",
		ServerLanguage.Italian: "\"Patisci!\"",
		ServerLanguage.German: "\"Fühlt den Schmerz!\"",
		ServerLanguage.Korean: "오직 공격뿐!",
		ServerLanguage.French: "\"Vive la douleur !\"",
		ServerLanguage.TraditionalChinese: "\"受死吧！\"",
		ServerLanguage.Japanese: "トゥ ザ ペイン！",
		ServerLanguage.Polish: "\"Niech żyje ból!\"",
		ServerLanguage.Russian: "\"Боль!\"",
		ServerLanguage.BorkBorkBork: "\"Tu zee Paeeen!\"",
	}
    
class TooMuchInformation(Inscription):
    id = ItemUpgrade.TooMuchInformation
    target_item_type = ItemType.Weapon
    property_identifiers = [
        ModifierIdentifier.DamagePlusVsHexed,
    ]
    names = {
		ServerLanguage.English: "\"Too Much Information\"",
		ServerLanguage.Spanish: "\"Demasiada información\"",
		ServerLanguage.Italian: "\"Troppe Informazioni\"",
		ServerLanguage.German: "\"Zuviel Information\"",
		ServerLanguage.Korean: "너무 많은 정보",
		ServerLanguage.French: "\"Trop de détails\"",
		ServerLanguage.TraditionalChinese: "\"多說無益\"",
		ServerLanguage.Japanese: "トゥー マッチ インフォメーション",
		ServerLanguage.Polish: "\"Za dużo informacji\"",
		ServerLanguage.Russian: "\"Слишком много информации\"",
		ServerLanguage.BorkBorkBork: "\"Tuu Mooch Inffurmaeshun\"",
	}
    
class VengeanceIsMine(Inscription):
    id = ItemUpgrade.VengeanceIsMine
    target_item_type = ItemType.Weapon
    property_identifiers = [
        ModifierIdentifier.DamagePlusWhileDown,
    ]    
    names = {
		ServerLanguage.English: "\"Vengeance is Mine\"",
		ServerLanguage.Spanish: "\"La venganza será mía\"",
		ServerLanguage.Italian: "\"La Vendetta è Mia\"",
		ServerLanguage.German: "\"Die Rache ist mein\"",
		ServerLanguage.Korean: "복수는 나의 것",
		ServerLanguage.French: "\"La vengeance sera mienne\"",
		ServerLanguage.TraditionalChinese: "\"我要報仇\"",
		ServerLanguage.Japanese: "ヴェンジャンス イズ マイン",
		ServerLanguage.Polish: "\"Zemsta należy do mnie\"",
		ServerLanguage.Russian: "\"Аз воздам\"",
		ServerLanguage.BorkBorkBork: "\"Fengeunce-a is Meene-a\"",
	}
#endregion Weapon

#region MartialWeapon
class IHaveThePower(Inscription):
    id = ItemUpgrade.IHaveThePower
    target_item_type = ItemType.MartialWeapon
    property_identifiers = [
        ModifierIdentifier.EnergyPlus,
    ]
    names = {
		ServerLanguage.English: "\"I have the power!\"",
		ServerLanguage.Spanish: "\"¡Tengo el poder!\"",
		ServerLanguage.Italian: "\"A Me Il Potere!\"",
		ServerLanguage.German: "\"Ich habe die Kraft!\"",
		ServerLanguage.Korean: "마력석: 내겐 에너지가 있다!",
		ServerLanguage.French: "\"Je détiens le pouvoir !\"",
		ServerLanguage.TraditionalChinese: "\"充滿力量！\"",
		ServerLanguage.Japanese: "アイ ハブ ザ パワー！",
		ServerLanguage.Polish: "\"Mam moc!\"",
		ServerLanguage.Russian: "\"Сила в моих руках!\"",
		ServerLanguage.BorkBorkBork: "\"I haefe-a zee pooer!\"",
	}
    
class LetTheMemoryLiveAgain(Inscription):
    id = ItemUpgrade.LetTheMemoryLiveAgain
    target_item_type = ItemType.MartialWeapon
    property_identifiers = [
        ModifierIdentifier.HalvesSkillRechargeGeneral,
    ]
    names = {
		ServerLanguage.English: "\"Let the Memory Live Again\"",
		ServerLanguage.Spanish: "\"Que vuelvan los recuerdos\"",
		ServerLanguage.Italian: "\"Facciamo Rivivere i Ricordi\"",
		ServerLanguage.German: "\"Auf die Erinnerung!\"",
		ServerLanguage.Korean: "기억이여, 되살아나라",
		ServerLanguage.French: "\"Vers l'infini et au-delà\"",
		ServerLanguage.TraditionalChinese: "\"記憶復甦\"",
		ServerLanguage.Japanese: "レット ザ メモリー リブ アゲイン",
		ServerLanguage.Polish: "\"Niech pamięć ponownie ożyje\"",
		ServerLanguage.Russian: "\"Пусть оживут воспоминания\"",
		ServerLanguage.BorkBorkBork: "\"Let zee Memury Leefe-a Aegaeeen\"",
	}
    
#endregion MartialWeapon

#region OffhandOrShield
class CastOutTheUnclean(Inscription):
    id = ItemUpgrade.CastOutTheUnclean
    target_item_type = ItemType.OffhandOrShield
    property_identifiers = [
        ModifierIdentifier.ReduceConditionDuration,
    ]
    names = {
		ServerLanguage.English: "\"Cast Out the Unclean\"",
		ServerLanguage.Spanish: "\"Desterremos a los impuros\"",
		ServerLanguage.Italian: "\"Esorcizza l'Eresia\"",
		ServerLanguage.German: "\"Gute Besserung!\"",
		ServerLanguage.Korean: "불결한 건 가랏!",
		ServerLanguage.French: "\"Au rebut les impurs\"",
		ServerLanguage.TraditionalChinese: "\"驅除不潔\"",
		ServerLanguage.Japanese: "キャスト アウト ザ アンクリーン",
		ServerLanguage.Polish: "\"Wyrzuć nieczystych\"",
		ServerLanguage.Russian: "\"Изгнать нечистых\"",
		ServerLanguage.BorkBorkBork: "\"Caest Oooot zee Uncleun\"",
	}
    
class FearCutsDeeper(Inscription):
    id = ItemUpgrade.FearCutsDeeper
    target_item_type = ItemType.OffhandOrShield
    property_identifiers = [
        ModifierIdentifier.ReduceConditionDuration,
    ]
    names = {
		ServerLanguage.English: "\"Fear Cuts Deeper\"",
		ServerLanguage.Spanish: "\"El miedo hace más daño\"",
		ServerLanguage.Italian: "\"Il Timore Trafigge\"",
		ServerLanguage.German: "\"Die Furcht schneidet tiefer\"",
		ServerLanguage.Korean: "공포는 더 깊은 상처를 낸다",
		ServerLanguage.French: "\"La peur fait plus de mal\"",
		ServerLanguage.TraditionalChinese: "\"戒除恐懼\"",
		ServerLanguage.Japanese: "フィアー カッツ ディーパー",
		ServerLanguage.Polish: "\"Strach rani głęboko\"",
		ServerLanguage.Russian: "\"Страх острее бритвы\"",
		ServerLanguage.BorkBorkBork: "\"Feaer Coots Deeper\"",
	}
    
class ICanSeeClearlyNow(Inscription):
    id = ItemUpgrade.ICanSeeClearlyNow
    target_item_type = ItemType.OffhandOrShield
    property_identifiers = [
        ModifierIdentifier.ReduceConditionDuration,   
    ]
    names = {
		ServerLanguage.English: "\"I Can See Clearly Now\"",
		ServerLanguage.Spanish: "\"He abierto los ojos\"",
		ServerLanguage.Italian: "\"Chiara Come Un'Alba\"",
		ServerLanguage.German: "\"Klar wie Morgentau\"",
		ServerLanguage.Korean: "마력석: 모든 게 뚜렷하게 보인다",
		ServerLanguage.French: "\"Je vois clair à présent\"",
		ServerLanguage.TraditionalChinese: "\"光明再現\"",
		ServerLanguage.Japanese: "アイ キャン シー クリアリー ナウ",
		ServerLanguage.Polish: "\"Widzę to teraz wyraźnie\"",
		ServerLanguage.Russian: "\"Теперь я ясно вижу\"",
		ServerLanguage.BorkBorkBork: "\"I Cun See-a Cleaerly Noo\"",
	}
    
class LeafOnTheWind(Inscription):
    id = ItemUpgrade.LeafOnTheWind
    target_item_type = ItemType.OffhandOrShield
    property_identifiers = [
        ModifierIdentifier.ArmorPlusVsDamage,
    ]
    names = {
		ServerLanguage.English: "\"Leaf on the Wind\"",
		ServerLanguage.Spanish: "\"Hoja en el viento\"",
		ServerLanguage.Italian: "\"Foglia nel Vento\"",
		ServerLanguage.German: "\"Grashalm im Wind\"",
		ServerLanguage.Korean: "바람에 떠다니는 나뭇잎",
		ServerLanguage.French: "\"La feuille portée par le vent\"",
		ServerLanguage.TraditionalChinese: "\"風中之葉\"",
		ServerLanguage.Japanese: "リーフ オン ザ ウインド",
		ServerLanguage.Polish: "\"Liść na wietrze\"",
		ServerLanguage.Russian: "\"Лист на ветру\"",
		ServerLanguage.BorkBorkBork: "\"Leaeff oon zee Veend\"",
	}
    
class LikeARollingStone(Inscription):
    id = ItemUpgrade.LikeARollingStone
    target_item_type = ItemType.OffhandOrShield
    property_identifiers = [
        ModifierIdentifier.ArmorPlusVsDamage,
    ]
    names = {
		ServerLanguage.English: "\"Like a Rolling Stone\"",
		ServerLanguage.Spanish: "\"Like a Rolling Stone\"",
		ServerLanguage.Italian: "\"Come Una Pietra Scalciata\"",
		ServerLanguage.German: "\"Marmor, Stein und Erde bricht\"",
		ServerLanguage.Korean: "구르는 돌처럼",
		ServerLanguage.French: "\"Solide comme le roc\"",
		ServerLanguage.TraditionalChinese: "\"漂泊者\"",
		ServerLanguage.Japanese: "ライク ア ローリング ストーン",
		ServerLanguage.Polish: "\"Jak wędrowiec\"",
		ServerLanguage.Russian: "\"Как перекати-поле\"",
		ServerLanguage.BorkBorkBork: "\"Leeke-a a Rulleeng Stune-a\"",
	}
    
class LuckOfTheDraw(Inscription):
    id = ItemUpgrade.LuckOfTheDraw
    target_item_type = ItemType.OffhandOrShield
    property_identifiers = [
        ModifierIdentifier.ReceiveLessDamage,
    ]
    names = {
		ServerLanguage.English: "\"Luck of the Draw\"",
		ServerLanguage.Spanish: "\"La suerte del apostante\"",
		ServerLanguage.Italian: "\"La Fortuna è Cieca\"",
		ServerLanguage.German: "\"Glück im Spiel ...\"",
		ServerLanguage.Korean: "비김의 행운",
		ServerLanguage.French: "\"Une question de chance\"",
		ServerLanguage.TraditionalChinese: "\"全憑運氣\"",
		ServerLanguage.Japanese: "ラック オブ ザ ドロー",
		ServerLanguage.Polish: "\"Szczęśliwe rozdanie\"",
		ServerLanguage.Russian: "\"Счастливый жребий\"",
		ServerLanguage.BorkBorkBork: "\"Loock ooff zee Draev\"",
	}
    
class MasterOfMyDomain(Inscription):
    id = ItemUpgrade.MasterOfMyDomain
    target_item_type = ItemType.OffhandOrShield
    property_identifiers = [
        ModifierIdentifier.AttributePlusOneItem,
    ]
    names = {
		ServerLanguage.English: "\"Master of My Domain!\"",
		ServerLanguage.Spanish: "\"Amo de mi reino\"",
		ServerLanguage.Italian: "\"Padrone in Casa Mia\"",
		ServerLanguage.German: "\"Herr in meinem Haus\"",
		ServerLanguage.Korean: "마력석: 내 공간의 지배자",
		ServerLanguage.French: "\"Maître du Domaine\"",
		ServerLanguage.TraditionalChinese: "\"這是我的地盤！\"",
		ServerLanguage.Japanese: "マスター オブ マイ ドメイン",
		ServerLanguage.Polish: "\"Pan mego królestwa\"",
		ServerLanguage.Russian: "\"Я сам себе хозяин\"",
		ServerLanguage.BorkBorkBork: "\"Maester ooff My Dumaeeen\"",
	}
    
class NotTheFace(Inscription):
    id = ItemUpgrade.NotTheFace
    target_item_type = ItemType.OffhandOrShield
    property_identifiers = [
        ModifierIdentifier.ArmorPlusVsDamage
    ]
    names = {
		ServerLanguage.English: "\"Not the Face!\"",
		ServerLanguage.Spanish: "\"¡En la cara no!\"",
		ServerLanguage.Italian: "\"Non al Volto!\"",
		ServerLanguage.German: "\"Nicht das Gesicht!\"",
		ServerLanguage.Korean: "얼굴은 안 돼!",
		ServerLanguage.French: "\"Pas le visage !\"",
		ServerLanguage.TraditionalChinese: "\"不要打臉！\"",
		ServerLanguage.Japanese: "ノット ザ フェース！",
		ServerLanguage.Polish: "\"Nie po twarzy!\"",
		ServerLanguage.Russian: "\"Только не в лицо!\"",
		ServerLanguage.BorkBorkBork: "\"Nut zee faece-a!\"",
	}
    
class NothingToFear(Inscription):
    id = ItemUpgrade.NothingToFear
    target_item_type = ItemType.OffhandOrShield
    property_identifiers = [
        ModifierIdentifier.ReceiveLessPhysDamageHexed,
    ]
    names = {
		ServerLanguage.English: "\"Nothing to Fear\"",
		ServerLanguage.Spanish: "\"Nada que temer\"",
		ServerLanguage.Italian: "\"Niente Paura\"",
		ServerLanguage.German: "\"Nichts zu befürchten\"",
		ServerLanguage.Korean: "두려울 건 없다",
		ServerLanguage.French: "\"Rien à craindre\"",
		ServerLanguage.TraditionalChinese: "\"無畏無懼\"",
		ServerLanguage.Japanese: "ナッシング トゥ フィアー",
		ServerLanguage.Polish: "\"Nieulękły\"",
		ServerLanguage.Russian: "\"Нечего бояться\"",
		ServerLanguage.BorkBorkBork: "\"Nutheeng tu Feaer\"",
	}
    
class OnlyTheStrongSurvive(Inscription):
    id = ItemUpgrade.OnlyTheStrongSurvive
    target_item_type = ItemType.OffhandOrShield
    property_identifiers = [
        ModifierIdentifier.ReduceConditionDuration,
    ]
    names = {
		ServerLanguage.English: "\"Only the Strong Survive\"",
		ServerLanguage.Spanish: "\"Sólo sobreviven los más fuertes\"",
		ServerLanguage.Italian: "\"Superstite è soltanto il Forte\"",
		ServerLanguage.German: "\"Nur die Stärksten überleben!\"",
		ServerLanguage.Korean: "강자만이 살아남는다",
		ServerLanguage.French: "\"Seuls les plus forts survivent\"",
		ServerLanguage.TraditionalChinese: "\"強者生存\"",
		ServerLanguage.Japanese: "オンリー ザ ストロング サバイブ",
		ServerLanguage.Polish: "\"Tylko silni przetrwają\"",
		ServerLanguage.Russian: "\"Выживает сильнейший\"",
		ServerLanguage.BorkBorkBork: "\"Oonly zee Strung Soorfeefe-a\"",
	}
    
class PureOfHeart(Inscription):
    id = ItemUpgrade.PureOfHeart
    target_item_type = ItemType.OffhandOrShield
    property_identifiers = [
        ModifierIdentifier.ReduceConditionDuration,
    ]
    names = {
		ServerLanguage.English: "\"Pure of Heart\"",
		ServerLanguage.Spanish: "\"Puro de corazón\"",
		ServerLanguage.Italian: "\"Purezza di Cuore\"",
		ServerLanguage.German: "\"Mein Herz ist rein\"",
		ServerLanguage.Korean: "심장의 깨끗함",
		ServerLanguage.French: "\"Pureté du coeur\"",
		ServerLanguage.TraditionalChinese: "\"純淨之心\"",
		ServerLanguage.Japanese: "ピュア オブ ハート",
		ServerLanguage.Polish: "\"Czystość serca\"",
		ServerLanguage.Russian: "\"Чистые сердцем\"",
		ServerLanguage.BorkBorkBork: "\"Poore-a ooff Heaert\"",
	}
    
class RidersOnTheStorm(Inscription):
    id = ItemUpgrade.RidersOnTheStorm
    target_item_type = ItemType.OffhandOrShield
    property_identifiers = [
        ModifierIdentifier.ArmorPlusVsDamage,
    ]
    names = {
		ServerLanguage.English: "\"Riders on the Storm\"",
		ServerLanguage.Spanish: "\"Jinetes de la tormenta\"",
		ServerLanguage.Italian: "\"Viaggiatori nella Burrasca\"",
		ServerLanguage.German: "\"Geblitzt wird nicht!\"",
		ServerLanguage.Korean: "폭풍의 기수",
		ServerLanguage.French: "\"Les chevaliers du ciel\"",
		ServerLanguage.TraditionalChinese: "\"暴風騎士\"",
		ServerLanguage.Japanese: "ライダー オン ザ ストーム",
		ServerLanguage.Polish: "\"Jeźdźcy burzy\"",
		ServerLanguage.Russian: "\"Всадники бури\"",
		ServerLanguage.BorkBorkBork: "\"Reeders oon zee Sturm\"",
	}
    
class RunForYourLife(Inscription):
    id = ItemUpgrade.RunForYourLife
    target_item_type = ItemType.OffhandOrShield
    property_identifiers = [
        ModifierIdentifier.ReceiveLessPhysDamageStance,
    ]
    names = {
		ServerLanguage.English: "\"Run For Your Life!\"",
		ServerLanguage.Spanish: "\"¡Ponte a salvo!\"",
		ServerLanguage.Italian: "\"Gambe in Spalla!\"",
		ServerLanguage.German: "\"Rennt um Euer Leben!\"",
		ServerLanguage.Korean: "살기 위해 달려라!",
		ServerLanguage.French: "\"Sauve-qui-peut !\"",
		ServerLanguage.TraditionalChinese: "\"逃命\"",
		ServerLanguage.Japanese: "ラン フォー ユア ライフ！",
		ServerLanguage.Polish: "\"Ratuj się kto może!\"",
		ServerLanguage.Russian: "\"Спасайся, кто может!\"",
		ServerLanguage.BorkBorkBork: "\"Roon Fur Yuoor Leeffe-a!\"",
	}
    
class ShelteredByFaith(Inscription):
    id = ItemUpgrade.ShelteredByFaith
    target_item_type = ItemType.OffhandOrShield
    property_identifiers = [
        ModifierIdentifier.ReceiveLessPhysDamageEnchanted,
    ]
    names = {
		ServerLanguage.English: "\"Sheltered by Faith\"",
		ServerLanguage.Spanish: "\"Fe ciega\"",
		ServerLanguage.Italian: "\"Rifugio della Speranza\"",
		ServerLanguage.German: "\"Vertrauen ist gut\"",
		ServerLanguage.Korean: "신념의 보호",
		ServerLanguage.French: "\"Protégé par la Foi\"",
		ServerLanguage.TraditionalChinese: "\"信念守護\"",
		ServerLanguage.Japanese: "シェルター バイ フェイス",
		ServerLanguage.Polish: "\"Chroniony przez wiarę\"",
		ServerLanguage.Russian: "\"Под защитой веры\"",
		ServerLanguage.BorkBorkBork: "\"Sheltered by Faeeet\"",
	}
    
class SleepNowInTheFire(Inscription):
    id = ItemUpgrade.SleepNowInTheFire
    target_item_type = ItemType.OffhandOrShield
    property_identifiers = [
        ModifierIdentifier.ArmorPlusVsDamage,
    ]
    names = {
		ServerLanguage.English: "\"Sleep Now in the Fire\"",
		ServerLanguage.Spanish: "\"Descansa en la hoguera\"",
		ServerLanguage.Italian: "\"Dormi Ardentemente\"",
		ServerLanguage.German: "\"Geborgenheit im Feuer\"",
		ServerLanguage.Korean: "화염 속에 잠들라",
		ServerLanguage.French: "\"Faisons la lumière sur les ténèbres\"",
		ServerLanguage.TraditionalChinese: "\"烈焰中歇息\"",
		ServerLanguage.Japanese: "スリープ ナウ イン ザ ファイア",
		ServerLanguage.Polish: "\"Zaśnij w ogniu\"",
		ServerLanguage.Russian: "\"Покойся в пламени\"",
		ServerLanguage.BorkBorkBork: "\"Sleep Noo in zee Fure-a\"",
	}
    
class SoundnessOfMind(Inscription):
    id = ItemUpgrade.SoundnessOfMind
    target_item_type = ItemType.OffhandOrShield
    property_identifiers = [
        ModifierIdentifier.ReduceConditionDuration,
    ]
    names = {
		ServerLanguage.English: "\"Soundness of Mind\"",
		ServerLanguage.Spanish: "\"Sano juicio\"",
		ServerLanguage.Italian: "\"Mente Sana\"",
		ServerLanguage.German: "\"Ein gesunder Geist ...\"",
		ServerLanguage.Korean: "마음의 소리",
		ServerLanguage.French: "\"Bon sens\"",
		ServerLanguage.TraditionalChinese: "\"堅定意念\"",
		ServerLanguage.Japanese: "サウンドネス オブ マインド",
		ServerLanguage.Polish: "\"Mądrość umysłu\"",
		ServerLanguage.Russian: "\"Здравый рассудок\"",
		ServerLanguage.BorkBorkBork: "\"Suoondness ooff Meend\"",
	}
    
class StrengthOfBody(Inscription):
    id = ItemUpgrade.StrengthOfBody
    target_item_type = ItemType.OffhandOrShield
    property_identifiers = [
        ModifierIdentifier.ReduceConditionDuration,
    ]
    names = {
		ServerLanguage.English: "\"Strength of Body\"",
		ServerLanguage.Spanish: "\"Fuerza bruta\"",
		ServerLanguage.Italian: "\"Corpo Gagliardo\"",
		ServerLanguage.German: "\"Hart im Nehmen\"",
		ServerLanguage.Korean: "육체의 힘",
		ServerLanguage.French: "\"La Force réside du corps\"",
		ServerLanguage.TraditionalChinese: "\"力貫全身\"",
		ServerLanguage.Japanese: "ストレングス オブ ボディ",
		ServerLanguage.Polish: "\"Siła ciała\"",
		ServerLanguage.Russian: "\"Сила тела\"",
		ServerLanguage.BorkBorkBork: "\"Strengt ooff Budy\"",
	}
    
class SwiftAsTheWind(Inscription):
    id = ItemUpgrade.SwiftAsTheWind
    target_item_type = ItemType.OffhandOrShield
    property_identifiers = [
        ModifierIdentifier.ReduceConditionDuration,
    ]
    names = {
		ServerLanguage.English: "\"Swift as the Wind\"",
		ServerLanguage.Spanish: "\"Veloz como el viento\"",
		ServerLanguage.Italian: "\"Raffica di Bora\"",
		ServerLanguage.German: "\"Schnell wie der Wind\"",
		ServerLanguage.Korean: "바람처럼 빠르게",
		ServerLanguage.French: "\"Rapide comme le vent\"",
		ServerLanguage.TraditionalChinese: "\"迅捷如風\"",
		ServerLanguage.Japanese: "スウィフト アズ ザ ウインド",
		ServerLanguage.Polish: "\"Szybki niczym wiatr\"",
		ServerLanguage.Russian: "\"Быстрый как ветер\"",
		ServerLanguage.BorkBorkBork: "\"Sveefft aes zee Veend\"",
	}

class TheRiddleOfSteel(Inscription):
    id = ItemUpgrade.TheRiddleOfSteel
    target_item_type = ItemType.OffhandOrShield
    property_identifiers = [
        ModifierIdentifier.ArmorPlusVsDamage,
    ]
    names = {
		ServerLanguage.English: "\"The Riddle of Steel\"",
		ServerLanguage.Spanish: "\"El enigma de acero\"",
		ServerLanguage.Italian: "\"Enigma d'Acciaio\"",
		ServerLanguage.German: "\"Hieb-und stahlfest\"",
		ServerLanguage.Korean: "강철의 수수께끼",
		ServerLanguage.French: "\"L'énigme de l'acier\"",
		ServerLanguage.TraditionalChinese: "\"鋼鐵之謎\"",
		ServerLanguage.Japanese: "ザ リドル オブ スチール",
		ServerLanguage.Polish: "\"Zagadka stali\"",
		ServerLanguage.Russian: "\"Стальной щит\"",
		ServerLanguage.BorkBorkBork: "\"Zee Reeddle-a ooff Steel\"",
	}
    
class ThroughThickAndThin(Inscription):
    id = ItemUpgrade.ThroughThickAndThin
    target_item_type = ItemType.OffhandOrShield
    property_identifiers = [
        ModifierIdentifier.ArmorPlusVsDamage,
    ]
    names = {
		ServerLanguage.English: "\"Through Thick and Thin\"",
		ServerLanguage.Spanish: "\"En lo bueno y en lo malo\"",
		ServerLanguage.Italian: "\"Nella Buona e nella Cattiva Sorte\"",
		ServerLanguage.German: "\"Durch Dick und Dünn\"",
		ServerLanguage.Korean: "무엇이든 막아내리",
		ServerLanguage.French: "\"Contre vents et marées\"",
		ServerLanguage.TraditionalChinese: "\"同甘共苦\"",
		ServerLanguage.Japanese: "スルー シック アンド シン",
		ServerLanguage.Polish: "\"Poprzez gąszcz\"",
		ServerLanguage.Russian: "\"Сквозь огонь и воду\"",
		ServerLanguage.BorkBorkBork: "\"Thruoogh Theeck und Theen\"",
	}
#endregion OffhandOrShield

#region EquippableItem
class MeasureForMeasure(Inscription):
    id = ItemUpgrade.MeasureForMeasure
    target_item_type = ItemType.EquippableItem
    property_identifiers = [
        ModifierIdentifier.HighlySalvageable,
    ]
    names = {
		ServerLanguage.English: "\"Measure for Measure\"",
		ServerLanguage.Spanish: "\"Ojo por ojo\"",
		ServerLanguage.Italian: "\"Occhio per Occhio\"",
		ServerLanguage.German: "\"Maß für Maß\"",
		ServerLanguage.Korean: "다다익선",
		ServerLanguage.French: "\"Mesure pour mesure.\"",
		ServerLanguage.TraditionalChinese: "\"以牙還牙\"",
		ServerLanguage.Japanese: "メジャー フォー メジャー",
		ServerLanguage.Polish: "\"Miarka za miarkę\"",
		ServerLanguage.Russian: "\"Око за око\"",
		ServerLanguage.BorkBorkBork: "\"Meaesoore-a fur Meaesoore-a\"",
	}
        
class ShowMeTheMoney(Inscription):
    id = ItemUpgrade.ShowMeTheMoney
    target_item_type = ItemType.EquippableItem
    property_identifiers = [
        ModifierIdentifier.IncreasedSaleValue,
    ]    
    names = {
		ServerLanguage.English: "\"Show me the money!\"",
		ServerLanguage.Spanish: "\"¡Enséñame la pasta!\"",
		ServerLanguage.Italian: "\"Mostrami la Grana!\"",
		ServerLanguage.German: "\"Geld macht glücklich!\"",
		ServerLanguage.Korean: "돈이다!",
		ServerLanguage.French: "\"Par ici la monnaie !\"",
		ServerLanguage.TraditionalChinese: "\"給我錢！\"",
		ServerLanguage.Japanese: "ショー ミー ザ マネー！",
		ServerLanguage.Polish: "\"Pokaż pieniądze!\"",
		ServerLanguage.Russian: "\"Покажи мне деньги!\"",
		ServerLanguage.BorkBorkBork: "\"Shoo me-a zee muney!\"",
	}
#endregion EquippableItem

#region SpellcastingWeapon
class AptitudeNotAttitude(Inscription):
    id = ItemUpgrade.AptitudeNotAttitude
    target_item_type = ItemType.SpellcastingWeapon
    property_identifiers = [
        ModifierIdentifier.HalvesCastingTimeItemAttribute,
    ]
    names = {
		ServerLanguage.English: "\"Aptitude not Attitude\"",
		ServerLanguage.Spanish: "\"Aptitud, no actitud\"",
		ServerLanguage.Italian: "\"Inclinazione non Finzione\"",
		ServerLanguage.German: "\"Gut gewirkt ist halb gewonnen\"",
		ServerLanguage.Korean: "마력석: 특성이 아니라 재능이다",
		ServerLanguage.French: "\"Les compétences prévalent\"",
		ServerLanguage.TraditionalChinese: "\"能力而非態度\"",
		ServerLanguage.Japanese: "アプティテュード ノット アティテュード",
		ServerLanguage.Polish: "\"Talent a nie nastawienie\"",
		ServerLanguage.Russian: "\"Главное -способности, а не отношение к делу\"",
		ServerLanguage.BorkBorkBork: "\"Aepteetoode-a nut Aetteetoode-a\"",
	}
    
class DontCallItAComeback(Inscription):
    id = ItemUpgrade.DontCallItAComeback
    target_item_type = ItemType.SpellcastingWeapon
    property_identifiers = [
        ModifierIdentifier.EnergyPlusWhileBelow,
    ]
    names = {
		ServerLanguage.English: "\"Don't call it a comeback!\"",
		ServerLanguage.Spanish: "\"¡No será la última palabra!\"",
		ServerLanguage.Italian: "\"Non Consideratelo un Ritorno!\"",
		ServerLanguage.German: "\"Sie kehren niemals wieder\"",
		ServerLanguage.Korean: "단순한 회복이 아니다!",
		ServerLanguage.French: "\"Aucun recours !\"",
		ServerLanguage.TraditionalChinese: "\"別說我不行！\"",
		ServerLanguage.Japanese: "ドント コール イット ア カムバック！",
		ServerLanguage.Polish: "\"Nie nazywaj tego powrotem!\"",
		ServerLanguage.Russian: "\"Не считай это местью!\"",
		ServerLanguage.BorkBorkBork: "\"Dun't caell it a cumebaeck!\"",
	}
    
class HaleAndHearty(Inscription):
    id = ItemUpgrade.HaleAndHearty
    target_item_type = ItemType.SpellcastingWeapon
    property_identifiers = [
        ModifierIdentifier.EnergyPlusWhileDown,
    ]
    names = {
		ServerLanguage.English: "\"Hale and Hearty\"",
		ServerLanguage.Spanish: "\"Viejo pero joven\"",
		ServerLanguage.Italian: "\"Vivo e Vegeto\"",
		ServerLanguage.German: "\"Gesund und munter\"",
		ServerLanguage.Korean: "마력석: 원기왕성하게!",
		ServerLanguage.French: "\"En pleine santé\"",
		ServerLanguage.TraditionalChinese: "\"健壯的\"",
		ServerLanguage.Japanese: "ヘイル アンド ハーティー",
		ServerLanguage.Polish: "\"Zdrowy i krzepki\"",
		ServerLanguage.Russian: "\"Сильный и здоровый\"",
		ServerLanguage.BorkBorkBork: "\"Haele-a und Heaerty\"",
	}
    
class HaveFaith(Inscription):
    id = ItemUpgrade.HaveFaith
    target_item_type = ItemType.SpellcastingWeapon
    property_identifiers = [
        ModifierIdentifier.EnergyPlusEnchanted,
    ]
    names = {
		ServerLanguage.English: "\"Have Faith\"",
		ServerLanguage.Spanish: "\"Tened fe\"",
		ServerLanguage.Italian: "\"Abbi Fede\"",
		ServerLanguage.German: "\"Habt Vertrauen\"",
		ServerLanguage.Korean: "신념을 가져라",
		ServerLanguage.French: "\"Ayez la foi\"",
		ServerLanguage.TraditionalChinese: "\"信念\"",
		ServerLanguage.Japanese: "ハブ フェイス",
		ServerLanguage.Polish: "\"Miej wiarę\"",
		ServerLanguage.Russian: "\"Не теряй веру\"",
		ServerLanguage.BorkBorkBork: "\"Haefe-a Faeeet\"",
	}
    
class IAmSorrow(Inscription):
    id = ItemUpgrade.IAmSorrow
    target_item_type = ItemType.SpellcastingWeapon
    property_identifiers = [
        ModifierIdentifier.EnergyPlusHexed,
    ]
    names = {
		ServerLanguage.English: "\"I am Sorrow.\"",
		ServerLanguage.Spanish: "\"Un mar de lágrimas\"",
		ServerLanguage.Italian: "\"Io Sono la Sofferenza\"",
		ServerLanguage.German: "\"Ich bin es Leid\"",
		ServerLanguage.Korean: "너무 슬프군",
		ServerLanguage.French: "\"Je suis la douleur\"",
		ServerLanguage.TraditionalChinese: "\"倍感憂傷\"",
		ServerLanguage.Japanese: "アイ アム ソロウ",
		ServerLanguage.Polish: "\"Jestem smutkiem.\"",
		ServerLanguage.Russian: "\"Я -воплощение скорби\"",
		ServerLanguage.BorkBorkBork: "\"I aem Surroo.\"",
	}
    
class SeizeTheDay(Inscription):
    id = ItemUpgrade.SeizeTheDay
    target_item_type = ItemType.SpellcastingWeapon
    property_identifiers = [
        ModifierIdentifier.EnergyPlus,
        ModifierIdentifier.EnergyDegen,
    ]
    names = {
		ServerLanguage.English: "\"Seize the Day\"",
		ServerLanguage.Spanish: "\"Vive el presente\"",
		ServerLanguage.Italian: "\"Vivi alla Giornata\"",
		ServerLanguage.German: "\"Lebt den Tag\"",
		ServerLanguage.Korean: "오늘을 위해 최선을",
		ServerLanguage.French: "\"Aujourd'hui, la vie\"",
		ServerLanguage.TraditionalChinese: "\"活在當下\"",
		ServerLanguage.Japanese: "リブ フォー トゥデイ",
		ServerLanguage.Polish: "\"Żyj dniem dzisiejszym\"",
		ServerLanguage.Russian: "\"Живи сегодняшним днем\"",
		ServerLanguage.BorkBorkBork: "\"Leefe-a fur Tudaey\"",
	}
#endregion SpellcastingWeapon
#endregion Inscriptions

#endregion Weapon Upgrades

#region Armor Upgrades
class Insignia(Upgrade):
    mod_type = ItemUpgradeType.Prefix

    id : ItemUpgrade
    inventory_icon : str
    rarity : Rarity = Rarity.Blue
    profession : Profession = Profession._None

    @classmethod
    def has_id(cls, upgrade_id: ItemUpgradeId) -> bool:
        return cls.id.has_id(upgrade_id)

    @property
    def description(self) -> str:
        return self.get_description()
    
    def get_description(self, language: ServerLanguage | None = None) -> str:
        if language is None:
            language = ServerLanguage(
                UIManager.GetIntPreference(NumberPreference.TextLanguage)
            )
            
        return self.descriptions.get(language, self.descriptions.get(ServerLanguage.English, ""))
    
    @property
    def name(self) -> str:
        return self.get_name()

    @classmethod
    def get_name(cls, language: ServerLanguage | None = None) -> str:
        if language is None:
            language = ServerLanguage(
                UIManager.GetIntPreference(NumberPreference.TextLanguage)
            )

        return cls.names.get(
            language,
            cls.names.get(ServerLanguage.English, f"Unknown Insignia {cls.__name__}")
        )

    @classmethod
    def apply_to_item_name(cls, item_name: str, language : ServerLanguage | None = None) -> str:
        if language is None:
            language = ServerLanguage(
                UIManager.GetIntPreference(NumberPreference.TextLanguage)
            )
            
        remove_profession_regex = r"\s*\[[^\]]+\]"
        remove_insignia_regex = r"(?:\s|-)?(?:Insignia|Insigne|Insegne|徽記|記章|휘장|Befähigung)\b"

        name = cls.get_name(language)
    
        # First remove any existing profession tags
        name = re.sub(remove_profession_regex, "", 
                           name)
        
        # Then replace any existing insignia with {item_name}
        name = re.sub(remove_insignia_regex, "-{item_name}" if language is ServerLanguage.German else " {item_name} ", name)
        
        return name.format(item_name=item_name).replace("  ", " ").strip()
        
    @classmethod
    def remove_from_item_name(cls, item_name: str, language: ServerLanguage | None = None) -> str:
        if language is None:
            language = ServerLanguage(
                UIManager.GetIntPreference(NumberPreference.TextLanguage)
            )

        remove_profession_regex = r"\s*\[[^\]]+\]"
        remove_insignia_regex = r"(?:\s|-)?(?:Insignia|Insigne|Insegne|徽記|記章|휘장|Befähigung)\b"

        # Clean upgrade name first
        name = re.sub(remove_profession_regex, "", cls.get_name(language))
        name = re.sub(remove_insignia_regex, "", name).strip()

        if language == ServerLanguage.German:
            # Remove base + any number of following dashes at start
            return item_name.replace(name + "-", "").strip()

        # Default behavior (non-German)
        return item_name.replace(name, "").strip()

class Rune(Upgrade):
    RUNE_PATTERNS = {
        ServerLanguage.English: r"^.*?\bRune\b\s*",
        ServerLanguage.German: r"^.*?Rune\b\s*",
        ServerLanguage.French: r"^Rune(?:\s+de\s+\S+)?\s*",
        ServerLanguage.Italian: r"^Runa(?:\s+del\s+\S+)?\s*",
        ServerLanguage.Spanish: r"^Runa(?:\s+de\s+\S+)?\s*",
        ServerLanguage.Korean: r"^.*?룬",
        ServerLanguage.Japanese: r"^.*?ルーン",
        ServerLanguage.TraditionalChinese: r"^.*?符文",
        ServerLanguage.Polish: r"^Runa(?:\s+\S+)?\s*",
        ServerLanguage.Russian: r"^.*?\bRune\b\s*",
    }
    
    mod_type = ItemUpgradeType.Suffix

    id : ItemUpgrade
    inventory_icon : str
    rarity : Rarity = Rarity.Blue
    profession : Profession = Profession._None
    names: dict[ServerLanguage, str] = {}

    @classmethod
    def has_id(cls, upgrade_id: ItemUpgradeId) -> bool:
        return cls.id.has_id(upgrade_id)

    @property
    def name(self) -> str:
        return self.get_name()

    @classmethod
    def get_name(cls, language: ServerLanguage | None = None) -> str:
        if language is None:
            language = ServerLanguage(
                UIManager.GetIntPreference(NumberPreference.TextLanguage)
            )
            
        return cls.names.get(language, cls.names.get(ServerLanguage.English, f"Unknown Rune {cls.__class__.__name__}"))

    @classmethod
    def apply_to_item_name(cls, item_name: str, language : ServerLanguage | None = None) -> str:
        if language is None:
            language = ServerLanguage(
                UIManager.GetIntPreference(NumberPreference.TextLanguage)
            )
        
        name = cls.get_name(language)
                
        pattern = cls.RUNE_PATTERNS.get(language)
        
        if pattern:
            new_name = re.sub(pattern, "{item_name} ", name)
            return re.sub(r"\s{2,}", " ", new_name).strip().format(item_name=item_name).replace("  ", " ").strip()
        
        return item_name
    
    @classmethod
    def remove_from_item_name(cls, item_name: str, language : ServerLanguage | None = None) -> str:
        if language is None:
            language = ServerLanguage(
                UIManager.GetIntPreference(NumberPreference.TextLanguage)
            )
        
        pattern = cls.RUNE_PATTERNS.get(language)
        
        if pattern:            
            name = cls.get_name(language)
            new_name = re.sub(pattern, "{item_name} ", name)
            new_name = re.sub(r"\s{2,}", " ", new_name).strip().replace("{item_name}", "").strip()
            return item_name.replace(new_name, "").strip()
        
        return item_name

class AttributeRune(Rune):
    attribute : Attribute
    attribute_level : int

    @classmethod
    def _pre_compose(cls, upgrade: "Upgrade", mod: DecodedModifier, modifiers: list[DecodedModifier],) -> None:
        attribute_rune = cast("AttributeRune", upgrade)
        attribute_rune.attribute = Attribute(mod.arg1)
        attribute_rune.attribute_level = mod.arg2

    @property
    def description(self) -> str:
        parts = [prop.describe() for prop in self.properties if prop.is_valid()]
        return f"{AttributeNames.get(self.attribute)} +{self.attribute_level} (Non-stacking)\n" + "\n".join(parts)

#region No Profession

class SurvivorInsignia(Insignia):
    id = ItemUpgrade.SurvivorInsignia
    names = {
        ServerLanguage.English: "Survivor Insignia",
        ServerLanguage.Korean: "생존자의 휘장",
        ServerLanguage.French: "Insigne du survivant",
        ServerLanguage.German: "Überlebende Befähigung",
        ServerLanguage.Italian: "Insegne del Superstite",
        ServerLanguage.Spanish: "Insignia de superviviente",
        ServerLanguage.TraditionalChinese: "生存 徽記",
        ServerLanguage.Japanese: "サバイバー 記章",
        ServerLanguage.Polish: "Symbol Przetrwania",
        ServerLanguage.Russian: "Survivor Insignia",
        ServerLanguage.BorkBorkBork: "Soorfeefur Inseegneea",
    }
    
    descriptions = {
        ServerLanguage.English: "Health +15 (on chest armor)\nHealth +10 (on leg armor)\nHealth +5 (on other armor)",
    }

class RadiantInsignia(Insignia):
    id = ItemUpgrade.RadiantInsignia
    names = {
        ServerLanguage.English: "Radiant Insignia",
        ServerLanguage.Korean: "눈부신 휘장",
        ServerLanguage.French: "Insigne du rayonnement",
        ServerLanguage.German: "Radianten- Befähigung",
        ServerLanguage.Italian: "Insegne Radianti",
        ServerLanguage.Spanish: "Insignia radiante",
        ServerLanguage.TraditionalChinese: "閃耀 徽記",
        ServerLanguage.Japanese: "ラディアント 記章",
        ServerLanguage.Polish: "Symbol Promieni",
        ServerLanguage.Russian: "Radiant Insignia",
        ServerLanguage.BorkBorkBork: "Raedeeunt Inseegneea",
    }
    
    descriptions = {
        ServerLanguage.English: "Energy +3 (on chest armor)\nEnergy +2 (on leg armor)\nEnergy +1 (on other armor)"
    }

class StalwartInsignia(Insignia):
    id = ItemUpgrade.StalwartInsignia
    property_identifiers = [
        ModifierIdentifier.ArmorPlusVsPhysical,
    ]

    names = {
        ServerLanguage.English: "Stalwart Insignia",
        ServerLanguage.Korean: "튼튼한 휘장",
        ServerLanguage.French: "Insigne robuste",
        ServerLanguage.German: "Entschlossenheits- Befähigung",
        ServerLanguage.Italian: "Insegne della Robustezza",
        ServerLanguage.Spanish: "Insignia firme",
        ServerLanguage.TraditionalChinese: "健壯 徽記",
        ServerLanguage.Japanese: "スタルウォート 記章",
        ServerLanguage.Polish: "Symbol Stanowczości",
        ServerLanguage.Russian: "Stalwart Insignia",
        ServerLanguage.BorkBorkBork: "Staelvaert Inseegneea",
    }
    
    descriptions = {
        ServerLanguage.English: "Armor +10 (vs. physical damage)"
    }

class BrawlersInsignia(Insignia):
    id = ItemUpgrade.BrawlersInsignia
    names = {
        ServerLanguage.English: "Brawler's Insignia",
        ServerLanguage.Korean: "싸움꾼의 휘장",
        ServerLanguage.French: "Insigne de l'agitateur",
        ServerLanguage.German: "Raufbold- Befähigung",
        ServerLanguage.Italian: "Insegne da Lottatore",
        ServerLanguage.Spanish: "Insignia del pendenciero",
        ServerLanguage.TraditionalChinese: "鬥士 徽記",
        ServerLanguage.Japanese: "ブラウラー 記章",
        ServerLanguage.Polish: "Symbol Zapaśnika",
        ServerLanguage.Russian: "Brawler's Insignia",
        ServerLanguage.BorkBorkBork: "Braevler's Inseegneea",
    }
    
    descriptions = {
        ServerLanguage.English: "Armor +10 (while attacking)"
    }

class BlessedInsignia(Insignia):
    id = ItemUpgrade.BlessedInsignia
    names = {
        ServerLanguage.English: "Blessed Insignia",
        ServerLanguage.Korean: "축복의 휘장",
        ServerLanguage.French: "Insigne de la bénédiction",
        ServerLanguage.German: "Segens Befähigung",
        ServerLanguage.Italian: "Insegne della Benedizione",
        ServerLanguage.Spanish: "Insignia con bendición",
        ServerLanguage.TraditionalChinese: "祝福 徽記",
        ServerLanguage.Japanese: "ブレス 記章",
        ServerLanguage.Polish: "Symbol Błogosławieństwa",
        ServerLanguage.Russian: "Blessed Insignia",
        ServerLanguage.BorkBorkBork: "Blessed Inseegneea",
    }
    
    descriptions = {
        ServerLanguage.English: "Armor +10 (while affected by an Enchantment Spell)",
    }

class HeraldsInsignia(Insignia):
    id = ItemUpgrade.HeraldsInsignia
    names = {
        ServerLanguage.English: "Herald's Insignia",
        ServerLanguage.Korean: "전령의 휘장",
        ServerLanguage.French: "Insigne de héraut",
        ServerLanguage.German: "Herold- Befähigung",
        ServerLanguage.Italian: "Insegne da Araldo",
        ServerLanguage.Spanish: "Insignia de heraldo",
        ServerLanguage.TraditionalChinese: "先驅 徽記",
        ServerLanguage.Japanese: "ヘラルド 記章",
        ServerLanguage.Polish: "Symbol Herolda",
        ServerLanguage.Russian: "Herald's Insignia",
        ServerLanguage.BorkBorkBork: "Heraeld's Inseegneea",
    }
    
    descriptions = {
        ServerLanguage.English: f"Armor +10 (while holding an item)"
    }

class SentrysInsignia(Insignia):
    id = ItemUpgrade.SentrysInsignia
    names = {
        ServerLanguage.English: "Sentry's Insignia",
        ServerLanguage.Korean: "보초병의 휘장",
        ServerLanguage.French: "Insigne de factionnaire",
        ServerLanguage.German: "Wachposten- Befähigung",
        ServerLanguage.Italian: "Insegne da Sentinella",
        ServerLanguage.Spanish: "Insignia de centinela",
        ServerLanguage.TraditionalChinese: "哨兵 徽記",
        ServerLanguage.Japanese: "セントリー 記章",
        ServerLanguage.Polish: "Symbol Wartownika",
        ServerLanguage.Russian: "Sentry's Insignia",
        ServerLanguage.BorkBorkBork: "Sentry's Inseegneea",
    }
    
    descriptions = {
        ServerLanguage.English: f"Armor +10 (while in a stance)"
    }

class RuneOfMinorVigor(Rune):
    id = ItemUpgrade.RuneOfMinorVigor
    rarity = Rarity.Blue

    names = {
        ServerLanguage.English: "Rune of Minor Vigor",
        ServerLanguage.Korean: "룬(하급 활력)",
        ServerLanguage.French: "Rune (Vigueur : bonus mineur)",
        ServerLanguage.German: "Rune d. kleineren Lebenskraft",
        ServerLanguage.Italian: "Runa Vigore di grado minore",
        ServerLanguage.Spanish: "Runa (vigor de grado menor)",
        ServerLanguage.TraditionalChinese: "初級 活力 符文",
        ServerLanguage.Japanese: "ルーン (マイナー ビガー)",
        ServerLanguage.Polish: "Runa (Wigoru niższego poziomu)",
        ServerLanguage.Russian: "Rune of Minor Vigor",
        ServerLanguage.BorkBorkBork: "Roone-a ooff Meenur Feegur",
    }
    
    descriptions = {
        ServerLanguage.English: "Health +30 (Non-stacking)"
    }

class RuneOfMinorVigor2(Rune):
    id = ItemUpgrade.RuneOfMinorVigor2
    rarity = Rarity.Blue

    names = {
        ServerLanguage.English: "Rune of Minor Vigor",
        ServerLanguage.Korean: "룬(하급 활력)",
        ServerLanguage.French: "Rune (Vigueur : bonus mineur)",
        ServerLanguage.German: "Rune d. kleineren Lebenskraft",
        ServerLanguage.Italian: "Runa Vigore di grado minore",
        ServerLanguage.Spanish: "Runa (vigor de grado menor)",
        ServerLanguage.TraditionalChinese: "初級 活力 符文",
        ServerLanguage.Japanese: "ルーン (マイナー ビガー)",
        ServerLanguage.Polish: "Runa (Wigoru niższego poziomu)",
        ServerLanguage.Russian: "Rune of Minor Vigor",
        ServerLanguage.BorkBorkBork: "Roone-a ooff Meenur Feegur",
    }

class RuneOfVitae(Rune):
    id = ItemUpgrade.RuneOfVitae
    rarity = Rarity.Blue

    names = {
        ServerLanguage.English: "Rune of Vitae",
        ServerLanguage.Korean: "룬(이력)",
        ServerLanguage.French: "Rune (de la vie)",
        ServerLanguage.German: "Rune d. Lebenskraft",
        ServerLanguage.Italian: "Runa della Vita",
        ServerLanguage.Spanish: "Runa (de vida)",
        ServerLanguage.TraditionalChinese: "生命 符文",
        ServerLanguage.Japanese: "ルーン (ヴィータ)",
        ServerLanguage.Polish: "Runa (Życia)",
        ServerLanguage.Russian: "Rune of Vitae",
        ServerLanguage.BorkBorkBork: "Roone-a ooff Feetaee-a",
    }

class RuneOfAttunement(Rune):
    id = ItemUpgrade.RuneOfAttunement
    rarity = Rarity.Blue

    names = {
        ServerLanguage.English: "Rune of Attunement",
        ServerLanguage.Korean: "룬(조율)",
        ServerLanguage.French: "Rune (d'affinité)",
        ServerLanguage.German: "Rune d. Einstimmung",
        ServerLanguage.Italian: "Runa dell'Armonia",
        ServerLanguage.Spanish: "Runa (de sintonía)",
        ServerLanguage.TraditionalChinese: "調和 符文",
        ServerLanguage.Japanese: "ルーン (アチューン)",
        ServerLanguage.Polish: "Runa (Dostrojenia)",
        ServerLanguage.Russian: "Rune of Attunement",
        ServerLanguage.BorkBorkBork: "Roone-a ooff Aettoonement",
    }

class RuneOfMajorVigor(Rune):
    id = ItemUpgrade.RuneOfMajorVigor
    rarity = Rarity.Purple

    names = {
        ServerLanguage.English: "Rune of Major Vigor",
        ServerLanguage.Korean: "룬(상급 활력)",
        ServerLanguage.French: "Rune (Vigueur : bonus majeur)",
        ServerLanguage.German: "Rune d. hohen Lebenskraft",
        ServerLanguage.Italian: "Runa Vigore di grado maggiore",
        ServerLanguage.Spanish: "Runa (vigor de grado mayor)",
        ServerLanguage.TraditionalChinese: "中級 活力 符文",
        ServerLanguage.Japanese: "ルーン (メジャー ビガー)",
        ServerLanguage.Polish: "Runa (Wigoru wyższego poziomu)",
        ServerLanguage.Russian: "Rune of Major Vigor",
        ServerLanguage.BorkBorkBork: "Roone-a ooff Maejur Feegur",
    }

class RuneOfRecovery(Rune):
    id = ItemUpgrade.RuneOfRecovery
    rarity = Rarity.Purple

    property_identifiers = [
        ModifierIdentifier.ReduceConditionTupleDuration,
    ]

    names = {
        ServerLanguage.English: "Rune of Recovery",
        ServerLanguage.Korean: "룬(회복)",
        ServerLanguage.French: "Rune (de récupération)",
        ServerLanguage.German: "Rune d. Gesundung",
        ServerLanguage.Italian: "Runa della Ripresa",
        ServerLanguage.Spanish: "Runa (de mejoría)",
        ServerLanguage.TraditionalChinese: "恢復 符文",
        ServerLanguage.Japanese: "ルーン (リカバリー)",
        ServerLanguage.Polish: "Runa (Uzdrowienia)",
        ServerLanguage.Russian: "Rune of Recovery",
        ServerLanguage.BorkBorkBork: "Roone-a ooff Recufery",
    }

class RuneOfRestoration(Rune):
    id = ItemUpgrade.RuneOfRestoration
    rarity = Rarity.Purple

    property_identifiers = [
        ModifierIdentifier.ReduceConditionTupleDuration,
    ]

    names = {
        ServerLanguage.English: "Rune of Restoration",
        ServerLanguage.Korean: "룬(복구)",
        ServerLanguage.French: "Rune (de rétablissement)",
        ServerLanguage.German: "Rune d. Wiederherstellung",
        ServerLanguage.Italian: "Runa del Ripristino",
        ServerLanguage.Spanish: "Runa (de restauración)",
        ServerLanguage.TraditionalChinese: "復原 符文",
        ServerLanguage.Japanese: "ルーン (レストレーション)",
        ServerLanguage.Polish: "Runa (Renowacji)",
        ServerLanguage.Russian: "Rune of Restoration",
        ServerLanguage.BorkBorkBork: "Roone-a ooff Resturaeshun",
    }

class RuneOfClarity(Rune):
    id = ItemUpgrade.RuneOfClarity
    rarity = Rarity.Purple

    property_identifiers = [
        ModifierIdentifier.ReduceConditionTupleDuration,
    ]

    names = {
        ServerLanguage.English: "Rune of Clarity",
        ServerLanguage.Korean: "룬(명석)",
        ServerLanguage.French: "Rune (de la clarté)",
        ServerLanguage.German: "Rune d. Klarheit",
        ServerLanguage.Italian: "Runa della Trasparenza",
        ServerLanguage.Spanish: "Runa (de claridad)",
        ServerLanguage.TraditionalChinese: "澄澈 符文",
        ServerLanguage.Japanese: "ルーン (クラリティ)",
        ServerLanguage.Polish: "Runa (Jasności)",
        ServerLanguage.Russian: "Rune of Clarity",
        ServerLanguage.BorkBorkBork: "Roone-a ooff Claereety",
    }

class RuneOfPurity(Rune):
    id = ItemUpgrade.RuneOfPurity
    rarity = Rarity.Purple

    property_identifiers = [
        ModifierIdentifier.ReduceConditionTupleDuration,
    ]

    names = {
        ServerLanguage.English: "Rune of Purity",
        ServerLanguage.Korean: "룬(순수)",
        ServerLanguage.French: "Rune (de la pureté)",
        ServerLanguage.German: "Rune d. Reinheit",
        ServerLanguage.Italian: "Runa della Purezza",
        ServerLanguage.Spanish: "Runa (de pureza)",
        ServerLanguage.TraditionalChinese: "潔淨 符文",
        ServerLanguage.Japanese: "ルーン (ピュリティ)",
        ServerLanguage.Polish: "Runa (Czystości)",
        ServerLanguage.Russian: "Rune of Purity",
        ServerLanguage.BorkBorkBork: "Roone-a ooff Pooreety",
    }

class RuneOfSuperiorVigor(Rune):
    id = ItemUpgrade.RuneOfSuperiorVigor
    rarity = Rarity.Gold

    names = {
        ServerLanguage.English: "Rune of Superior Vigor",
        ServerLanguage.Korean: "룬(고급 활력)",
        ServerLanguage.French: "Rune (Vigueur : bonus supérieur)",
        ServerLanguage.German: "Rune d. überlegenen Lebenskraft",
        ServerLanguage.Italian: "Runa Vigore di grado supremo",
        ServerLanguage.Spanish: "Runa (vigor de grado excepcional)",
        ServerLanguage.TraditionalChinese: "高級 活力 符文",
        ServerLanguage.Japanese: "ルーン (スーペリア ビガー)",
        ServerLanguage.Polish: "Runa (Wigoru najwyższego poziomu)",
        ServerLanguage.Russian: "Rune of Superior Vigor",
        ServerLanguage.BorkBorkBork: "Roone-a ooff Soopereeur Feegur",
    }

#endregion No Profession

#region Warrior

class KnightsInsignia(Insignia):
    id = ItemUpgrade.KnightsInsignia
    names = {
        ServerLanguage.English: "Knight's Insignia [Warrior]",
        ServerLanguage.Korean: "기사의 휘장 [워리어]",
        ServerLanguage.French: "Insigne [Guerrier] de chevalier",
        ServerLanguage.German: "Ritter- [Krieger]-Befähigung",
        ServerLanguage.Italian: "Insegne [Guerriero] da Cavaliere",
        ServerLanguage.Spanish: "Insignia [Guerrero] de caballero",
        ServerLanguage.TraditionalChinese: "騎士 徽記 [戰士]",
        ServerLanguage.Japanese: "ナイト 記章 [ウォーリア]",
        ServerLanguage.Polish: "[Wojownik] Symbol Rycerza",
        ServerLanguage.Russian: "Knight's Insignia [Warrior]",
        ServerLanguage.BorkBorkBork: "Kneeght's Inseegneea [Vaerreeur]",
    }
    
    descriptions = {
        ServerLanguage.English: "Received physical damage -3"
    }

class LieutenantsInsignia(Insignia):
    id = ItemUpgrade.LieutenantsInsignia
    names = {
        ServerLanguage.English: "Lieutenant's Insignia [Warrior]",
        ServerLanguage.Korean: "부관의 휘장 [워리어]",
        ServerLanguage.French: "Insigne [Guerrier] du Lieutenant",
        ServerLanguage.German: "Leutnant- [Krieger]-Befähigung",
        ServerLanguage.Italian: "Insegne [Guerriero] da Luogotenente",
        ServerLanguage.Spanish: "Insignia [Guerrero] de teniente",
        ServerLanguage.TraditionalChinese: "副官 徽記 [戰士]",
        ServerLanguage.Japanese: "ルテナント 記章 [ウォーリア]",
        ServerLanguage.Polish: "[Wojownik] Symbol Porucznika",
        ServerLanguage.Russian: "Lieutenant's Insignia [Warrior]",
        ServerLanguage.BorkBorkBork: "Leeeootenunt's Inseegneea [Vaerreeur]",
    }
    
    descriptions = {
        ServerLanguage.English: f"Reduces Hex durations on you by 20% and damage dealt by you by 5% (Non-stacking)\nArmor -20"
    }

class StonefistInsignia(Insignia):
    id = ItemUpgrade.StonefistInsignia
    names = {
        ServerLanguage.English: "Stonefist Insignia [Warrior]",
        ServerLanguage.Korean: "돌주먹의 휘장 [워리어]",
        ServerLanguage.French: "Insigne [Guerrier] Poing-de-fer",
        ServerLanguage.German: "Steinfaust- [Krieger]-Befähigung",
        ServerLanguage.Italian: "Insegne [Guerriero] di Pietra",
        ServerLanguage.Spanish: "Insignia [Guerrero] de piedra",
        ServerLanguage.TraditionalChinese: "石拳 徽記 [戰士]",
        ServerLanguage.Japanese: "ストーンフィスト 記章 [ウォーリア]",
        ServerLanguage.Polish: "[Wojownik] Symbol Kamiennej Pięści",
        ServerLanguage.Russian: "Stonefist Insignia [Warrior]",
        ServerLanguage.BorkBorkBork: "Stuneffeest Inseegneea [Vaerreeur]",
    }
    
    descriptions = {
        ServerLanguage.English: f"Increases knockdown time on foes by 1 second.\n(Maximum: 3 seconds)"
    }

class DreadnoughtInsignia(Insignia):
    id = ItemUpgrade.DreadnoughtInsignia
    names = {
        ServerLanguage.English: "Dreadnought Insignia [Warrior]",
        ServerLanguage.Korean: "용자의 휘장 [워리어]",
        ServerLanguage.French: "Insigne [Guerrier] de Dreadnaught",
        ServerLanguage.German: "Panzerschiff- [Krieger]-Befähigung",
        ServerLanguage.Italian: "Insegne [Guerriero] da Dreadnought",
        ServerLanguage.Spanish: "Insignia [Guerrero] de Dreadnought",
        ServerLanguage.TraditionalChinese: "無懼 徽記 [戰士]",
        ServerLanguage.Japanese: "ドレッドノート 記章 [ウォーリア]",
        ServerLanguage.Polish: "[Wojownik] Symbol Pancernika",
        ServerLanguage.Russian: "Dreadnought Insignia [Warrior]",
        ServerLanguage.BorkBorkBork: "Dreaednuooght Inseegneea [Vaerreeur]",
    }
    
    descriptions = {
        ServerLanguage.English: f"Armor +10 (vs. elemental damage)"
    }

class SentinelsInsignia(Insignia):
    id = ItemUpgrade.SentinelsInsignia
    names = {
        ServerLanguage.English: "Sentinel's Insignia [Warrior]",
        ServerLanguage.Korean: "감시병의 휘장 [워리어]",
        ServerLanguage.French: "Insigne [Guerrier] de sentinelle",
        ServerLanguage.German: "Wächter- [Krieger]-Befähigung",
        ServerLanguage.Italian: "Insegne [Guerriero] da Sentinella",
        ServerLanguage.Spanish: "Insignia [Guerrero] de centinela",
        ServerLanguage.TraditionalChinese: "警戒 徽記 [戰士]",
        ServerLanguage.Japanese: "センチネル 記章 [ウォーリア]",
        ServerLanguage.Polish: "[Wojownik] Symbol Strażnika",
        ServerLanguage.Russian: "Sentinel's Insignia [Warrior]",
        ServerLanguage.BorkBorkBork: "Senteenel's Inseegneea [Vaerreeur]",
    }
    
    descriptions = {
        ServerLanguage.English: f"Armor +20 (Requires 13 Strength, vs. elemental damage)"
    }

class WarriorRuneOfMinorAbsorption(Rune):
    id = ItemUpgrade.WarriorRuneOfMinorAbsorption
    rarity = Rarity.Blue

    names = {
        ServerLanguage.English: "Warrior Rune of Minor Absorption",
        ServerLanguage.Korean: "워리어 룬(하급 흡수)",
        ServerLanguage.French: "Rune de Guerrier (Absorption : bonus mineur)",
        ServerLanguage.German: "Krieger-Rune d. kleineren Absorption",
        ServerLanguage.Italian: "Runa del Guerriero Assorbimento di grado minore",
        ServerLanguage.Spanish: "Runa de Guerrero (absorción de grado menor)",
        ServerLanguage.TraditionalChinese: "初級 吸收 戰士符文",
        ServerLanguage.Japanese: "ウォーリア ルーン (マイナー アブソープション)",
        ServerLanguage.Polish: "Runa Wojownika (Pochłaniania niższego poziomu)",
        ServerLanguage.Russian: "Warrior Rune of Minor Absorption",
        ServerLanguage.BorkBorkBork: "Vaerreeur Roone-a ooff Meenur Aebsurpshun",
    }

class WarriorRuneOfMinorTactics(AttributeRune):
    id = ItemUpgrade.WarriorRuneOfMinorTactics
    rarity = Rarity.Blue

    names = {
        ServerLanguage.English: "Warrior Rune of Minor Tactics",
        ServerLanguage.Korean: "워리어 룬(하급 전술)",
        ServerLanguage.French: "Rune de Guerrier (Tactique : bonus mineur)",
        ServerLanguage.German: "Krieger-Rune d. kleineren Taktik",
        ServerLanguage.Italian: "Runa del Guerriero Tattica di grado minore",
        ServerLanguage.Spanish: "Runa de Guerrero (Táctica de grado menor)",
        ServerLanguage.TraditionalChinese: "初級 戰術 戰士符文",
        ServerLanguage.Japanese: "ウォーリア ルーン (マイナー タクティクス)",
        ServerLanguage.Polish: "Runa Wojownika (Taktyka niższego poziomu)",
        ServerLanguage.Russian: "Warrior Rune of Minor Tactics",
        ServerLanguage.BorkBorkBork: "Vaerreeur Roone-a ooff Meenur Taecteecs",
    }

class WarriorRuneOfMinorStrength(AttributeRune):
    id = ItemUpgrade.WarriorRuneOfMinorStrength
    rarity = Rarity.Blue

    names = {
        ServerLanguage.English: "Warrior Rune of Minor Strength",
        ServerLanguage.Korean: "워리어 룬(하급 강인함)",
        ServerLanguage.French: "Rune de Guerrier (Force : bonus mineur)",
        ServerLanguage.German: "Krieger-Rune d. kleineren Stärke",
        ServerLanguage.Italian: "Runa del Guerriero Forza di grado minore",
        ServerLanguage.Spanish: "Runa de Guerrero (Fuerza de grado menor)",
        ServerLanguage.TraditionalChinese: "初級 力量 戰士符文",
        ServerLanguage.Japanese: "ウォーリア ルーン (マイナー ストレングス)",
        ServerLanguage.Polish: "Runa Wojownika (Siła niższego poziomu)",
        ServerLanguage.Russian: "Warrior Rune of Minor Strength",
        ServerLanguage.BorkBorkBork: "Vaerreeur Roone-a ooff Meenur Strengt",
    }

class WarriorRuneOfMinorAxeMastery(AttributeRune):
    id = ItemUpgrade.WarriorRuneOfMinorAxeMastery
    rarity = Rarity.Blue

    names = {
        ServerLanguage.English: "Warrior Rune of Minor Axe Mastery",
        ServerLanguage.Korean: "워리어 룬(하급 도끼술)",
        ServerLanguage.French: "Rune de Guerrier (Maîtrise de la hache : bonus mineur)",
        ServerLanguage.German: "Krieger-Rune d. kleineren Axtbeherrschung",
        ServerLanguage.Italian: "Runa del Guerriero Abilità con l'Ascia di grado minore",
        ServerLanguage.Spanish: "Runa de Guerrero (Dominio del hacha de grado menor)",
        ServerLanguage.TraditionalChinese: "初級 精通斧術 戰士符文",
        ServerLanguage.Japanese: "ウォーリア ルーン (マイナー アックス マスタリー)",
        ServerLanguage.Polish: "Runa Wojownika (Biegłość w Toporach niższego poziomu)",
        ServerLanguage.Russian: "Warrior Rune of Minor Axe Mastery",
        ServerLanguage.BorkBorkBork: "Vaerreeur Roone-a ooff Meenur Aexe-a Maestery",
    }

class WarriorRuneOfMinorHammerMastery(AttributeRune):
    id = ItemUpgrade.WarriorRuneOfMinorHammerMastery
    rarity = Rarity.Blue

    names = {
        ServerLanguage.English: "Warrior Rune of Minor Hammer Mastery",
        ServerLanguage.Korean: "워리어 룬(하급 해머술)",
        ServerLanguage.French: "Rune de Guerrier (Maîtrise du marteau : bonus mineur)",
        ServerLanguage.German: "Krieger-Rune d. kleineren Hammerbeherrschung",
        ServerLanguage.Italian: "Runa del Guerriero Abilità col Martello di grado minore",
        ServerLanguage.Spanish: "Runa de Guerrero (Dominio del martillo de grado menor)",
        ServerLanguage.TraditionalChinese: "初級 精通鎚術 戰士符文",
        ServerLanguage.Japanese: "ウォーリア ルーン (マイナー ハンマー マスタリー)",
        ServerLanguage.Polish: "Runa Wojownika (Biegłość w Młotach niższego poziomu)",
        ServerLanguage.Russian: "Warrior Rune of Minor Hammer Mastery",
        ServerLanguage.BorkBorkBork: "Vaerreeur Roone-a ooff Meenur Haemmer Maestery",
    }

class WarriorRuneOfMinorSwordsmanship(AttributeRune):
    id = ItemUpgrade.WarriorRuneOfMinorSwordsmanship
    rarity = Rarity.Blue

    names = {
        ServerLanguage.English: "Warrior Rune of Minor Swordsmanship",
        ServerLanguage.Korean: "워리어 룬(하급 검술)",
        ServerLanguage.French: "Rune de Guerrier (Maîtrise de l'épée : bonus mineur)",
        ServerLanguage.German: "Krieger-Rune d. kleineren Schwertkunst",
        ServerLanguage.Italian: "Runa del Guerriero Scherma di grado minore",
        ServerLanguage.Spanish: "Runa de Guerrero (Esgrima de grado menor)",
        ServerLanguage.TraditionalChinese: "初級 精通劍術 戰士符文",
        ServerLanguage.Japanese: "ウォーリア ルーン (マイナー ソード マスタリー)",
        ServerLanguage.Polish: "Runa Wojownika (Biegłość w Mieczach niższego poziomu)",
        ServerLanguage.Russian: "Warrior Rune of Minor Swordsmanship",
        ServerLanguage.BorkBorkBork: "Vaerreeur Roone-a ooff Meenur Svurdsmunsheep",
    }

class WarriorRuneOfMajorAbsorption(Rune):
    id = ItemUpgrade.WarriorRuneOfMajorAbsorption
    rarity = Rarity.Purple

    names = {
        ServerLanguage.English: "Warrior Rune of Major Absorption",
        ServerLanguage.Korean: "워리어 룬(상급 흡수)",
        ServerLanguage.French: "Rune de Guerrier (Absorption : bonus majeur)",
        ServerLanguage.German: "Krieger-Rune d. hohen Absorption",
        ServerLanguage.Italian: "Runa del Guerriero Assorbimento di grado maggiore",
        ServerLanguage.Spanish: "Runa de Guerrero (absorción de grado mayor)",
        ServerLanguage.TraditionalChinese: "中級 吸收 戰士符文",
        ServerLanguage.Japanese: "ウォーリア ルーン (メジャー アブソープション)",
        ServerLanguage.Polish: "Runa Wojownika (Pochłaniania wyższego poziomu)",
        ServerLanguage.Russian: "Warrior Rune of Major Absorption",
        ServerLanguage.BorkBorkBork: "Vaerreeur Roone-a ooff Maejur Aebsurpshun",
    }

class WarriorRuneOfMajorTactics(AttributeRune):
    id = ItemUpgrade.WarriorRuneOfMajorTactics
    rarity = Rarity.Purple

    property_identifiers = [
        ModifierIdentifier.HealthMinus
    ]

    names = {
        ServerLanguage.English: "Warrior Rune of Major Tactics",
        ServerLanguage.Korean: "워리어 룬(상급 전술)",
        ServerLanguage.French: "Rune de Guerrier (Tactique : bonus majeur)",
        ServerLanguage.German: "Krieger-Rune d. hohen Taktik",
        ServerLanguage.Italian: "Runa del Guerriero Tattica di grado maggiore",
        ServerLanguage.Spanish: "Runa de Guerrero (Táctica de grado mayor)",
        ServerLanguage.TraditionalChinese: "中級 戰術 戰士符文",
        ServerLanguage.Japanese: "ウォーリア ルーン (メジャー タクティクス)",
        ServerLanguage.Polish: "Runa Wojownika (Taktyka wyższego poziomu)",
        ServerLanguage.Russian: "Warrior Rune of Major Tactics",
        ServerLanguage.BorkBorkBork: "Vaerreeur Roone-a ooff Maejur Taecteecs",
    }

class WarriorRuneOfMajorStrength(AttributeRune):
    id = ItemUpgrade.WarriorRuneOfMajorStrength
    rarity = Rarity.Purple

    property_identifiers = [
        ModifierIdentifier.HealthMinus
    ]

    names = {
        ServerLanguage.English: "Warrior Rune of Major Strength",
        ServerLanguage.Korean: "워리어 룬(상급 강인함)",
        ServerLanguage.French: "Rune de Guerrier (Force : bonus majeur)",
        ServerLanguage.German: "Krieger-Rune d. hohen Stärke",
        ServerLanguage.Italian: "Runa del Guerriero Forza di grado maggiore",
        ServerLanguage.Spanish: "Runa de Guerrero (Fuerza de grado mayor)",
        ServerLanguage.TraditionalChinese: "中級 力量 戰士符文",
        ServerLanguage.Japanese: "ウォーリア ルーン (メジャー ストレングス)",
        ServerLanguage.Polish: "Runa Wojownika (Siła wyższego poziomu)",
        ServerLanguage.Russian: "Warrior Rune of Major Strength",
        ServerLanguage.BorkBorkBork: "Vaerreeur Roone-a ooff Maejur Strengt",
    }

class WarriorRuneOfMajorAxeMastery(AttributeRune):
    id = ItemUpgrade.WarriorRuneOfMajorAxeMastery
    rarity = Rarity.Purple

    property_identifiers = [
        ModifierIdentifier.HealthMinus
    ]

    names = {
        ServerLanguage.English: "Warrior Rune of Major Axe Mastery",
        ServerLanguage.Korean: "워리어 룬(상급 도끼술)",
        ServerLanguage.French: "Rune de Guerrier (Maîtrise de la hache : bonus majeur)",
        ServerLanguage.German: "Krieger-Rune d. hohen Axtbeherrschung",
        ServerLanguage.Italian: "Runa del Guerriero Abilità con l'Ascia di grado maggiore",
        ServerLanguage.Spanish: "Runa de Guerrero (Dominio del hacha de grado mayor)",
        ServerLanguage.TraditionalChinese: "中級 精通斧術 戰士符文",
        ServerLanguage.Japanese: "ウォーリア ルーン (メジャー アックス マスタリー)",
        ServerLanguage.Polish: "Runa Wojownika (Biegłość w Toporach wyższego poziomu)",
        ServerLanguage.Russian: "Warrior Rune of Major Axe Mastery",
        ServerLanguage.BorkBorkBork: "Vaerreeur Roone-a ooff Maejur Aexe-a Maestery",
    }

class WarriorRuneOfMajorHammerMastery(AttributeRune):
    id = ItemUpgrade.WarriorRuneOfMajorHammerMastery
    rarity = Rarity.Purple

    property_identifiers = [
        ModifierIdentifier.HealthMinus
    ]

    names = {
        ServerLanguage.English: "Warrior Rune of Major Hammer Mastery",
        ServerLanguage.Korean: "워리어 룬(상급 해머술)",
        ServerLanguage.French: "Rune de Guerrier (Maîtrise du marteau : bonus majeur)",
        ServerLanguage.German: "Krieger-Rune d. hohen Hammerbeherrschung",
        ServerLanguage.Italian: "Runa del Guerriero Abilità col Martello di grado maggiore",
        ServerLanguage.Spanish: "Runa de Guerrero (Dominio del martillo de grado mayor)",
        ServerLanguage.TraditionalChinese: "中級 精通鎚術 戰士符文",
        ServerLanguage.Japanese: "ウォーリア ルーン (メジャー ハンマー マスタリー)",
        ServerLanguage.Polish: "Runa Wojownika (Biegłość w Młotach wyższego poziomu)",
        ServerLanguage.Russian: "Warrior Rune of Major Hammer Mastery",
        ServerLanguage.BorkBorkBork: "Vaerreeur Roone-a ooff Maejur Haemmer Maestery",
    }

class WarriorRuneOfMajorSwordsmanship(AttributeRune):
    id = ItemUpgrade.WarriorRuneOfMajorSwordsmanship
    rarity = Rarity.Purple

    property_identifiers = [
        ModifierIdentifier.HealthMinus
    ]

    names = {
        ServerLanguage.English: "Warrior Rune of Major Swordsmanship",
        ServerLanguage.Korean: "워리어 룬(상급 검술)",
        ServerLanguage.French: "Rune de Guerrier (Maîtrise de l'épée : bonus majeur)",
        ServerLanguage.German: "Krieger-Rune d. hohen Schwertkunst",
        ServerLanguage.Italian: "Runa del Guerriero Scherma di grado maggiore",
        ServerLanguage.Spanish: "Runa de Guerrero (Esgrima de grado mayor)",
        ServerLanguage.TraditionalChinese: "中級 精通劍術 戰士符文",
        ServerLanguage.Japanese: "ウォーリア ルーン (メジャー ソード マスタリー)",
        ServerLanguage.Polish: "Runa Wojownika (Biegłość w Mieczach wyższego poziomu)",
        ServerLanguage.Russian: "Warrior Rune of Major Swordsmanship",
        ServerLanguage.BorkBorkBork: "Vaerreeur Roone-a ooff Maejur Svurdsmunsheep",
    }

class WarriorRuneOfSuperiorAbsorption(Rune):
    id = ItemUpgrade.WarriorRuneOfSuperiorAbsorption
    rarity = Rarity.Gold

    names = {
        ServerLanguage.English: "Warrior Rune of Superior Absorption",
        ServerLanguage.Korean: "워리어 룬(고급 흡수)",
        ServerLanguage.French: "Rune de Guerrier (Absorption : bonus supérieur)",
        ServerLanguage.German: "Krieger-Rune d. überlegenen Absorption",
        ServerLanguage.Italian: "Runa del Guerriero Assorbimento di grado supremo",
        ServerLanguage.Spanish: "Runa de Guerrero (absorción de grado excepcional)",
        ServerLanguage.TraditionalChinese: "高級 吸收 戰士符文",
        ServerLanguage.Japanese: "ウォーリア ルーン (スーペリア アブソープション)",
        ServerLanguage.Polish: "Runa Wojownika (Pochłaniania najwyższego poziomu)",
        ServerLanguage.Russian: "Warrior Rune of Superior Absorption",
        ServerLanguage.BorkBorkBork: "Vaerreeur Roone-a ooff Soopereeur Aebsurpshun",
    }

class WarriorRuneOfSuperiorTactics(AttributeRune):
    id = ItemUpgrade.WarriorRuneOfSuperiorTactics
    rarity = Rarity.Gold

    property_identifiers = [
        ModifierIdentifier.HealthMinus
    ]

    names = {
        ServerLanguage.English: "Warrior Rune of Superior Tactics",
        ServerLanguage.Korean: "워리어 룬(고급 전술)",
        ServerLanguage.French: "Rune de Guerrier (Tactique : bonus supérieur)",
        ServerLanguage.German: "Krieger-Rune d. überlegenen Taktik",
        ServerLanguage.Italian: "Runa del Guerriero Tattica di grado supremo",
        ServerLanguage.Spanish: "Runa de Guerrero (Táctica de grado excepcional)",
        ServerLanguage.TraditionalChinese: "高級 戰術 戰士符文",
        ServerLanguage.Japanese: "ウォーリア ルーン (スーペリア タクティクス)",
        ServerLanguage.Polish: "Runa Wojownika (Taktyka najwyższego poziomu)",
        ServerLanguage.Russian: "Warrior Rune of Superior Tactics",
        ServerLanguage.BorkBorkBork: "Vaerreeur Roone-a ooff Soopereeur Taecteecs",
    }

class WarriorRuneOfSuperiorStrength(AttributeRune):
    id = ItemUpgrade.WarriorRuneOfSuperiorStrength
    rarity = Rarity.Gold

    property_identifiers = [
        ModifierIdentifier.HealthMinus
    ]

    names = {
        ServerLanguage.English: "Warrior Rune of Superior Strength",
        ServerLanguage.Korean: "워리어 룬(고급 강인함)",
        ServerLanguage.French: "Rune de Guerrier (Force : bonus supérieur)",
        ServerLanguage.German: "Krieger-Rune d. überlegenen Stärke",
        ServerLanguage.Italian: "Runa del Guerriero Forza di grado supremo",
        ServerLanguage.Spanish: "Runa de Guerrero (Fuerza de grado excepcional)",
        ServerLanguage.TraditionalChinese: "高級 力量 戰士符文",
        ServerLanguage.Japanese: "ウォーリア ルーン (スーペリア ストレングス)",
        ServerLanguage.Polish: "Runa Wojownika (Siła najwyższego poziomu)",
        ServerLanguage.Russian: "Warrior Rune of Superior Strength",
        ServerLanguage.BorkBorkBork: "Vaerreeur Roone-a ooff Soopereeur Strengt",
    }

class WarriorRuneOfSuperiorAxeMastery(AttributeRune):
    id = ItemUpgrade.WarriorRuneOfSuperiorAxeMastery
    rarity = Rarity.Gold

    property_identifiers = [
        ModifierIdentifier.HealthMinus
    ]

    names = {
        ServerLanguage.English: "Warrior Rune of Superior Axe Mastery",
        ServerLanguage.Korean: "워리어 룬(고급 도끼술)",
        ServerLanguage.French: "Rune de Guerrier (Maîtrise de la hache : bonus supérieur)",
        ServerLanguage.German: "Krieger-Rune d. überlegenen Axtbeherrschung",
        ServerLanguage.Italian: "Runa del Guerriero Abilità con l'Ascia di grado supremo",
        ServerLanguage.Spanish: "Runa de Guerrero (Dominio del hacha de grado excepcional)",
        ServerLanguage.TraditionalChinese: "高級 精通斧術 戰士符文",
        ServerLanguage.Japanese: "ウォーリア ルーン (スーペリア アックス マスタリー)",
        ServerLanguage.Polish: "Runa Wojownika (Biegłość w Toporach najwyższego poziomu)",
        ServerLanguage.Russian: "Warrior Rune of Superior Axe Mastery",
        ServerLanguage.BorkBorkBork: "Vaerreeur Roone-a ooff Soopereeur Aexe-a Maestery",
    }

class WarriorRuneOfSuperiorHammerMastery(AttributeRune):
    id = ItemUpgrade.WarriorRuneOfSuperiorHammerMastery
    rarity = Rarity.Gold

    property_identifiers = [
        ModifierIdentifier.HealthMinus
    ]

    names = {
        ServerLanguage.English: "Warrior Rune of Superior Hammer Mastery",
        ServerLanguage.Korean: "워리어 룬(고급 해머술)",
        ServerLanguage.French: "Rune de Guerrier (Maîtrise du marteau : bonus supérieur)",
        ServerLanguage.German: "Krieger-Rune d. überlegenen Hammerbeherrschung",
        ServerLanguage.Italian: "Runa del Guerriero Abilità col Martello di grado supremo",
        ServerLanguage.Spanish: "Runa de Guerrero (Dominio del martillo de grado excepcional)",
        ServerLanguage.TraditionalChinese: "高級 精通鎚術 戰士符文",
        ServerLanguage.Japanese: "ウォーリア ルーン (スーペリア ハンマー マスタリー)",
        ServerLanguage.Polish: "Runa Wojownika (Biegłość w Młotach najwyższego poziomu)",
        ServerLanguage.Russian: "Warrior Rune of Superior Hammer Mastery",
        ServerLanguage.BorkBorkBork: "Vaerreeur Roone-a ooff Soopereeur Haemmer Maestery",
    }

class WarriorRuneOfSuperiorSwordsmanship(AttributeRune):
    id = ItemUpgrade.WarriorRuneOfSuperiorSwordsmanship
    rarity = Rarity.Gold

    property_identifiers = [
        ModifierIdentifier.HealthMinus
    ]

    names = {
        ServerLanguage.English: "Warrior Rune of Superior Swordsmanship",
        ServerLanguage.Korean: "워리어 룬(고급 검술)",
        ServerLanguage.French: "Rune de Guerrier (Maîtrise de l'épée : bonus supérieur)",
        ServerLanguage.German: "Krieger-Rune d. überlegenen Schwertkunst",
        ServerLanguage.Italian: "Runa del Guerriero Scherma di grado supremo",
        ServerLanguage.Spanish: "Runa de Guerrero (Esgrima de grado excepcional)",
        ServerLanguage.TraditionalChinese: "高級 精通劍術 戰士符文",
        ServerLanguage.Japanese: "ウォーリア ルーン (スーペリア ソード マスタリー)",
        ServerLanguage.Polish: "Runa Wojownika (Biegłość w Mieczach najwyższego poziomu)",
        ServerLanguage.Russian: "Warrior Rune of Superior Swordsmanship",
        ServerLanguage.BorkBorkBork: "Vaerreeur Roone-a ooff Soopereeur Svurdsmunsheep",
    }

class UpgradeMinorRuneWarrior(Upgrade):
    id = ItemUpgrade.UpgradeMinorRuneWarrior
    mod_type = ItemUpgradeType.UpgradeRune

class UpgradeMajorRuneWarrior(Upgrade):
    id = ItemUpgrade.UpgradeMajorRuneWarrior
    mod_type = ItemUpgradeType.UpgradeRune

class UpgradeSuperiorRuneWarrior(Upgrade):
    id = ItemUpgrade.UpgradeSuperiorRuneWarrior
    mod_type = ItemUpgradeType.UpgradeRune

class AppliesToMinorRuneWarrior(Upgrade):
    id = ItemUpgrade.AppliesToMinorRuneWarrior
    mod_type = ItemUpgradeType.AppliesToRune

class AppliesToMajorRuneWarrior(Upgrade):
    id = ItemUpgrade.AppliesToMajorRuneWarrior
    mod_type = ItemUpgradeType.AppliesToRune

class AppliesToSuperiorRuneWarrior(Upgrade):
    id = ItemUpgrade.AppliesToSuperiorRuneWarrior
    mod_type = ItemUpgradeType.AppliesToRune

#endregion Warrior

#region Ranger

class FrostboundInsignia(Insignia):
    id = ItemUpgrade.FrostboundInsignia
    names = {
        ServerLanguage.English: "Frostbound Insignia [Ranger]",
        ServerLanguage.Korean: "얼음결계의 휘장 [레인저]",
        ServerLanguage.French: "Insigne [Rôdeur] de givre",
        ServerLanguage.German: "Permafrost- [Waldläufer]-Befähigung",
        ServerLanguage.Italian: "Insegne [Esploratore] da Ghiaccio",
        ServerLanguage.Spanish: "Insignia [Guardabosques] de montaña",
        ServerLanguage.TraditionalChinese: "霜縛 徽記 [遊俠]",
        ServerLanguage.Japanese: "フロストバウンド 記章 [レンジャー]",
        ServerLanguage.Polish: "[Łowca] Symbol Spętanego przez Lód",
        ServerLanguage.Russian: "Frostbound Insignia [Ranger]",
        ServerLanguage.BorkBorkBork: "Frustbuoond Inseegneea [Runger]",
    }
    
    descriptions = {
        ServerLanguage.English: f"Armor +15 (vs. Cold damage)"
    }

class PyreboundInsignia(Insignia):
    id = ItemUpgrade.PyreboundInsignia
    names = {
        ServerLanguage.English: "Pyrebound Insignia [Ranger]",
        ServerLanguage.Korean: "화염결계의 휘장 [레인저]",
        ServerLanguage.French: "Insigne [Rôdeur] du bûcher",
        ServerLanguage.German: "Scheiterhaufen- [Waldläufer]-Befähigung",
        ServerLanguage.Italian: "Insegne [Esploratore] da Rogo",
        ServerLanguage.Spanish: "Insignia [Guardabosques] de leñero",
        ServerLanguage.TraditionalChinese: "火縛 徽記 [遊俠]",
        ServerLanguage.Japanese: "パイアーバウンド 記章 [レンジャー]",
        ServerLanguage.Polish: "[Łowca] Symbol Spętanego przez Ogień",
        ServerLanguage.Russian: "Pyrebound Insignia [Ranger]",
        ServerLanguage.BorkBorkBork: "Pyrebuoond Inseegneea [Runger]",
    }
    
    descriptions = {
        ServerLanguage.English: f"Armor +15 (vs. Fire damage)"
    }

class StormboundInsignia(Insignia):
    id = ItemUpgrade.StormboundInsignia
    names = {
        ServerLanguage.English: "Stormbound Insignia [Ranger]",
        ServerLanguage.Korean: "폭풍결계의 휘장 [레인저]",
        ServerLanguage.French: "Insigne [Rôdeur] de tonnerre",
        ServerLanguage.German: "Unwetter- [Waldläufer]-Befähigung",
        ServerLanguage.Italian: "Insegne [Esploratore] da Bufera",
        ServerLanguage.Spanish: "Insignia [Guardabosques] de hidromántico",
        ServerLanguage.TraditionalChinese: "風縛 徽記 [遊俠]",
        ServerLanguage.Japanese: "ストームバウンド 記章 [レンジャー]",
        ServerLanguage.Polish: "[Łowca] Symbol Spętanego przez Sztorm",
        ServerLanguage.Russian: "Stormbound Insignia [Ranger]",
        ServerLanguage.BorkBorkBork: "Sturmbuoond Inseegneea [Runger]",
    }
    
    descriptions = {
        ServerLanguage.English: f"Armor +15 (vs. Lightning damage)"
    }

class ScoutsInsignia(Insignia):
    id = ItemUpgrade.ScoutsInsignia
    names = {
        ServerLanguage.English: "Scout's Insignia [Ranger]",
        ServerLanguage.Korean: "정찰병의 휘장 [레인저]",
        ServerLanguage.French: "Insigne [Rôdeur] d'éclaireur",
        ServerLanguage.German: "Späher- [Waldläufer]-Befähigung",
        ServerLanguage.Italian: "Insegne [Esploratore] da Perlustratore",
        ServerLanguage.Spanish: "Insignia [Guardabosques] de explorador",
        ServerLanguage.TraditionalChinese: "偵查者 徽記 [遊俠]",
        ServerLanguage.Japanese: "スカウト 記章 [レンジャー]",
        ServerLanguage.Polish: "[Łowca] Symbol Zwiadowcy",
        ServerLanguage.Russian: "Scout's Insignia [Ranger]",
        ServerLanguage.BorkBorkBork: "Scuoot's Inseegneea [Runger]",
    }
    
    descriptions = {
        ServerLanguage.English: f"Armor +10 (while using a Preparation)"
    }

class EarthboundInsignia(Insignia):
    id = ItemUpgrade.EarthboundInsignia
    names = {
        ServerLanguage.English: "Earthbound Insignia [Ranger]",
        ServerLanguage.Korean: "대지결계의 휘장 [레인저]",
        ServerLanguage.French: "Insigne [Rôdeur] terrestre",
        ServerLanguage.German: "Erdbindungs- [Waldläufer]-Befähigung",
        ServerLanguage.Italian: "Insegne [Esploratore] da Terra",
        ServerLanguage.Spanish: "Insignia [Guardabosques] de tierra",
        ServerLanguage.TraditionalChinese: "地縛 徽記 [遊俠]",
        ServerLanguage.Japanese: "アースバウンド 記章 [レンジャー]",
        ServerLanguage.Polish: "[Łowca] Symbol Spętanego przez Ziemię",
        ServerLanguage.Russian: "Earthbound Insignia [Ranger]",
        ServerLanguage.BorkBorkBork: "Iaerthbuoond Inseegneea [Runger]",
    }
    
    descriptions = {
        ServerLanguage.English: f"Armor +15 (vs. Earth damage)"
    }

class BeastmastersInsignia(Insignia):
    id = ItemUpgrade.BeastmastersInsignia
    names = {
        ServerLanguage.English: "Beastmaster's Insignia [Ranger]",
        ServerLanguage.Korean: "조련사의 휘장 [레인저]",
        ServerLanguage.French: "Insigne [Rôdeur] de belluaire",
        ServerLanguage.German: "Tierbändiger- [Waldläufer]-Befähigung",
        ServerLanguage.Italian: "Insegne [Esploratore] da Domatore",
        ServerLanguage.Spanish: "Insignia [Guardabosques] de domador",
        ServerLanguage.TraditionalChinese: "野獸大師 徽記 [遊俠]",
        ServerLanguage.Japanese: "ビーストマスター 記章 [レンジャー]",
        ServerLanguage.Polish: "[Łowca] Symbol Władcy Zwierząt",
        ServerLanguage.Russian: "Beastmaster's Insignia [Ranger]",
        ServerLanguage.BorkBorkBork: "Beaestmaester's Inseegneea [Runger]",
    }
    
    descriptions = {
        ServerLanguage.English: f"Armor +10 (while your pet is alive)"
    }

class RangerRuneOfMinorWildernessSurvival(AttributeRune):
    id = ItemUpgrade.RangerRuneOfMinorWildernessSurvival
    rarity = Rarity.Blue

    names = {
        ServerLanguage.English: "Ranger Rune of Minor Wilderness Survival",
        ServerLanguage.Korean: "레인저 룬(하급 생존술)",
        ServerLanguage.French: "Rune de Rôdeur (Survie : bonus mineur)",
        ServerLanguage.German: "Waldläufer-Rune d. kleineren Überleben in der Wildnis",
        ServerLanguage.Italian: "Runa dell'Esploratore Sopravvivenza nella Natura di grado minore",
        ServerLanguage.Spanish: "Runa de Guardabosques (Supervivencia naturaleza de grado menor)",
        ServerLanguage.TraditionalChinese: "初級 求生 遊俠符文",
        ServerLanguage.Japanese: "レンジャー ルーン (マイナー サバイバル)",
        ServerLanguage.Polish: "Runa Łowcy (Przetrwanie w Dziczy niższego poziomu)",
        ServerLanguage.Russian: "Ranger Rune of Minor Wilderness Survival",
        ServerLanguage.BorkBorkBork: "Runger Roone-a ooff Meenur Veelderness Soorfeefael",
    }

class RangerRuneOfMinorExpertise(AttributeRune):
    id = ItemUpgrade.RangerRuneOfMinorExpertise
    rarity = Rarity.Blue

    names = {
        ServerLanguage.English: "Ranger Rune of Minor Expertise",
        ServerLanguage.Korean: "레인저 룬(하급 전문성)",
        ServerLanguage.French: "Rune de Rôdeur (Expertise : bonus mineur)",
        ServerLanguage.German: "Waldläufer-Rune d. kleineren Fachkenntnis",
        ServerLanguage.Italian: "Runa dell'Esploratore Esperienza di grado minore",
        ServerLanguage.Spanish: "Runa de Guardabosques (Pericia de grado menor)",
        ServerLanguage.TraditionalChinese: "初級 專精 遊俠符文",
        ServerLanguage.Japanese: "レンジャー ルーン (マイナー エキスパーティーズ)",
        ServerLanguage.Polish: "Runa Łowcy (Specjalizacja niższego poziomu)",
        ServerLanguage.Russian: "Ranger Rune of Minor Expertise",
        ServerLanguage.BorkBorkBork: "Runger Roone-a ooff Meenur Ixperteese-a",
    }

class RangerRuneOfMinorBeastMastery(AttributeRune):
    id = ItemUpgrade.RangerRuneOfMinorBeastMastery
    rarity = Rarity.Blue

    names = {
        ServerLanguage.English: "Ranger Rune of Minor Beast Mastery",
        ServerLanguage.Korean: "레인저 룬(하급 동물 친화)",
        ServerLanguage.French: "Rune de Rôdeur (Domptage : bonus mineur)",
        ServerLanguage.German: "Waldläufer-Rune d. kleineren Tierbeherrschung",
        ServerLanguage.Italian: "Runa dell'Esploratore Potere sulle Belve di grado minore",
        ServerLanguage.Spanish: "Runa de Guardabosques (Dominio de bestias de grado menor)",
        ServerLanguage.TraditionalChinese: "初級 野獸支配 遊俠符文",
        ServerLanguage.Japanese: "レンジャー ルーン (マイナー ビースト マスタリー)",
        ServerLanguage.Polish: "Runa Łowcy (Panowanie nad Zwierzętami niższego poziomu)",
        ServerLanguage.Russian: "Ranger Rune of Minor Beast Mastery",
        ServerLanguage.BorkBorkBork: "Runger Roone-a ooff Meenur Beaest Maestery",
    }

class RangerRuneOfMinorMarksmanship(AttributeRune):
    id = ItemUpgrade.RangerRuneOfMinorMarksmanship
    rarity = Rarity.Blue

    names = {
        ServerLanguage.English: "Ranger Rune of Minor Marksmanship",
        ServerLanguage.Korean: "레인저 룬(하급 궁술)",
        ServerLanguage.French: "Rune de Rôdeur (Adresse au tir : bonus mineur)",
        ServerLanguage.German: "Waldläufer-Rune d. kleineren Treffsicherheit",
        ServerLanguage.Italian: "Runa dell'Esploratore Precisione di grado minore",
        ServerLanguage.Spanish: "Runa de Guardabosques (Puntería de grado menor)",
        ServerLanguage.TraditionalChinese: "初級 弓術精通 遊俠符文",
        ServerLanguage.Japanese: "レンジャー ルーン (マイナー ボウ マスタリー)",
        ServerLanguage.Polish: "Runa Łowcy (Umiejętności Strzeleckie niższego poziomu)",
        ServerLanguage.Russian: "Ranger Rune of Minor Marksmanship",
        ServerLanguage.BorkBorkBork: "Runger Roone-a ooff Meenur Maerksmunsheep",
    }

class RangerRuneOfMajorWildernessSurvival(AttributeRune):
    id = ItemUpgrade.RangerRuneOfMajorWildernessSurvival
    rarity = Rarity.Purple

    property_identifiers = [
        ModifierIdentifier.HealthMinus
    ]

    names = {
        ServerLanguage.English: "Ranger Rune of Major Wilderness Survival",
        ServerLanguage.Korean: "레인저 룬(상급 생존술)",
        ServerLanguage.French: "Rune de Rôdeur (Survie : bonus majeur)",
        ServerLanguage.German: "Waldläufer-Rune d. hohen Überleben in der Wildnis",
        ServerLanguage.Italian: "Runa dell'Esploratore Sopravvivenza nella Natura di grado maggiore",
        ServerLanguage.Spanish: "Runa de Guardabosques (Supervivencia naturaleza de grado mayor)",
        ServerLanguage.TraditionalChinese: "中級 求生 遊俠符文",
        ServerLanguage.Japanese: "レンジャー ルーン (メジャー サバイバル)",
        ServerLanguage.Polish: "Runa Łowcy (Przetrwanie w Dziczy wyższego poziomu)",
        ServerLanguage.Russian: "Ranger Rune of Major Wilderness Survival",
        ServerLanguage.BorkBorkBork: "Runger Roone-a ooff Maejur Veelderness Soorfeefael",
    }

class RangerRuneOfMajorExpertise(AttributeRune):
    id = ItemUpgrade.RangerRuneOfMajorExpertise
    rarity = Rarity.Purple

    property_identifiers = [
        ModifierIdentifier.HealthMinus
    ]

    names = {
        ServerLanguage.English: "Ranger Rune of Major Expertise",
        ServerLanguage.Korean: "레인저 룬(상급 전문성)",
        ServerLanguage.French: "Rune de Rôdeur (Expertise : bonus majeur)",
        ServerLanguage.German: "Waldläufer-Rune d. hohen Fachkenntnis",
        ServerLanguage.Italian: "Runa dell'Esploratore Esperienza di grado maggiore",
        ServerLanguage.Spanish: "Runa de Guardabosques (Pericia de grado mayor)",
        ServerLanguage.TraditionalChinese: "中級 專精 遊俠符文",
        ServerLanguage.Japanese: "レンジャー ルーン (メジャー エキスパーティーズ)",
        ServerLanguage.Polish: "Runa Łowcy (Specjalizacja wyższego poziomu)",
        ServerLanguage.Russian: "Ranger Rune of Major Expertise",
        ServerLanguage.BorkBorkBork: "Runger Roone-a ooff Maejur Ixperteese-a",
    }

class RangerRuneOfMajorBeastMastery(AttributeRune):
    id = ItemUpgrade.RangerRuneOfMajorBeastMastery
    rarity = Rarity.Purple

    property_identifiers = [
        ModifierIdentifier.HealthMinus
    ]

    names = {
        ServerLanguage.English: "Ranger Rune of Major Beast Mastery",
        ServerLanguage.Korean: "레인저 룬(상급 동물 친화)",
        ServerLanguage.French: "Rune de Rôdeur (Domptage : bonus majeur)",
        ServerLanguage.German: "Waldläufer-Rune d. hohen Tierbeherrschung",
        ServerLanguage.Italian: "Runa dell'Esploratore Potere sulle Belve di grado maggiore",
        ServerLanguage.Spanish: "Runa de Guardabosques (Dominio de bestias de grado mayor)",
        ServerLanguage.TraditionalChinese: "中級 野獸支配 遊俠符文",
        ServerLanguage.Japanese: "レンジャー ルーン (メジャー ビースト マスタリー)",
        ServerLanguage.Polish: "Runa Łowcy (Panowanie nad Zwierzętami wyższego poziomu)",
        ServerLanguage.Russian: "Ranger Rune of Major Beast Mastery",
        ServerLanguage.BorkBorkBork: "Runger Roone-a ooff Maejur Beaest Maestery",
    }

class RangerRuneOfMajorMarksmanship(AttributeRune):
    id = ItemUpgrade.RangerRuneOfMajorMarksmanship
    rarity = Rarity.Purple

    property_identifiers = [
        ModifierIdentifier.HealthMinus
    ]

    names = {
        ServerLanguage.English: "Ranger Rune of Major Marksmanship",
        ServerLanguage.Korean: "레인저 룬(상급 궁술)",
        ServerLanguage.French: "Rune de Rôdeur (Adresse au tir : bonus majeur)",
        ServerLanguage.German: "Waldläufer-Rune d. hohen Treffsicherheit",
        ServerLanguage.Italian: "Runa dell'Esploratore Precisione di grado maggiore",
        ServerLanguage.Spanish: "Runa de Guardabosques (Puntería de grado mayor)",
        ServerLanguage.TraditionalChinese: "中級 弓術精通 遊俠符文",
        ServerLanguage.Japanese: "レンジャー ルーン (メジャー ボウ マスタリー)",
        ServerLanguage.Polish: "Runa Łowcy (Umiejętności Strzeleckie wyższego poziomu)",
        ServerLanguage.Russian: "Ranger Rune of Major Marksmanship",
        ServerLanguage.BorkBorkBork: "Runger Roone-a ooff Maejur Maerksmunsheep",
    }

class RangerRuneOfSuperiorWildernessSurvival(AttributeRune):
    id = ItemUpgrade.RangerRuneOfSuperiorWildernessSurvival
    rarity = Rarity.Gold

    property_identifiers = [
        ModifierIdentifier.HealthMinus
    ]

    names = {
        ServerLanguage.English: "Ranger Rune of Superior Wilderness Survival",
        ServerLanguage.Korean: "레인저 룬(고급 생존술)",
        ServerLanguage.French: "Rune de Rôdeur (Survie : bonus supérieur)",
        ServerLanguage.German: "Waldläufer-Rune d. überlegenen Überleben in der Wildnis",
        ServerLanguage.Italian: "Runa dell'Esploratore Sopravvivenza nella Natura di grado supremo",
        ServerLanguage.Spanish: "Runa de Guardabosques (Supervivencia naturaleza de grado excepcional)",
        ServerLanguage.TraditionalChinese: "高級 求生 遊俠符文",
        ServerLanguage.Japanese: "レンジャー ルーン (スーペリア サバイバル)",
        ServerLanguage.Polish: "Runa Łowcy (Przetrwanie w Dziczy najwyższego poziomu)",
        ServerLanguage.Russian: "Ranger Rune of Superior Wilderness Survival",
        ServerLanguage.BorkBorkBork: "Runger Roone-a ooff Soopereeur Veelderness Soorfeefael",
    }

class RangerRuneOfSuperiorExpertise(AttributeRune):
    id = ItemUpgrade.RangerRuneOfSuperiorExpertise
    rarity = Rarity.Gold

    property_identifiers = [
        ModifierIdentifier.HealthMinus
    ]

    names = {
        ServerLanguage.English: "Ranger Rune of Superior Expertise",
        ServerLanguage.Korean: "레인저 룬(고급 전문성)",
        ServerLanguage.French: "Rune de Rôdeur (Expertise : bonus supérieur)",
        ServerLanguage.German: "Waldläufer-Rune d. überlegenen Fachkenntnis",
        ServerLanguage.Italian: "Runa dell'Esploratore Esperienza di grado supremo",
        ServerLanguage.Spanish: "Runa de Guardabosques (Pericia de grado excepcional)",
        ServerLanguage.TraditionalChinese: "高級 專精 遊俠符文",
        ServerLanguage.Japanese: "レンジャー ルーン (スーペリア エキスパーティーズ)",
        ServerLanguage.Polish: "Runa Łowcy (Specjalizacja najwyższego poziomu)",
        ServerLanguage.Russian: "Ranger Rune of Superior Expertise",
        ServerLanguage.BorkBorkBork: "Runger Roone-a ooff Soopereeur Ixperteese-a",
    }

class RangerRuneOfSuperiorBeastMastery(AttributeRune):
    id = ItemUpgrade.RangerRuneOfSuperiorBeastMastery
    rarity = Rarity.Gold

    property_identifiers = [
        ModifierIdentifier.HealthMinus
    ]

    names = {
        ServerLanguage.English: "Ranger Rune of Superior Beast Mastery",
        ServerLanguage.Korean: "레인저 룬(고급 동물 친화)",
        ServerLanguage.French: "Rune de Rôdeur (Domptage : bonus supérieur)",
        ServerLanguage.German: "Waldläufer-Rune d. überlegenen Tierbeherrschung",
        ServerLanguage.Italian: "Runa dell'Esploratore Potere sulle Belve di grado supremo",
        ServerLanguage.Spanish: "Runa de Guardabosques (Dominio de bestias de grado excepcional)",
        ServerLanguage.TraditionalChinese: "高級 野獸支配 遊俠符文",
        ServerLanguage.Japanese: "レンジャー ルーン (スーペリア ビースト マスタリー)",
        ServerLanguage.Polish: "Runa Łowcy (Panowanie nad Zwierzętami najwyższego poziomu)",
        ServerLanguage.Russian: "Ranger Rune of Superior Beast Mastery",
        ServerLanguage.BorkBorkBork: "Runger Roone-a ooff Soopereeur Beaest Maestery",
    }

class RangerRuneOfSuperiorMarksmanship(AttributeRune):
    id = ItemUpgrade.RangerRuneOfSuperiorMarksmanship
    rarity = Rarity.Gold

    property_identifiers = [
        ModifierIdentifier.HealthMinus
    ]

    names = {
        ServerLanguage.English: "Ranger Rune of Superior Marksmanship",
        ServerLanguage.Korean: "레인저 룬(고급 궁술)",
        ServerLanguage.French: "Rune de Rôdeur (Adresse au tir : bonus supérieur)",
        ServerLanguage.German: "Waldläufer-Rune d. überlegenen Treffsicherheit",
        ServerLanguage.Italian: "Runa dell'Esploratore Precisione di grado supremo",
        ServerLanguage.Spanish: "Runa de Guardabosques (Puntería de grado excepcional)",
        ServerLanguage.TraditionalChinese: "高級 弓術精通 遊俠符文",
        ServerLanguage.Japanese: "レンジャー ルーン (スーペリア ボウ マスタリー)",
        ServerLanguage.Polish: "Runa Łowcy (Umiejętności Strzeleckie najwyższego poziomu)",
        ServerLanguage.Russian: "Ranger Rune of Superior Marksmanship",
        ServerLanguage.BorkBorkBork: "Runger Roone-a ooff Soopereeur Maerksmunsheep",
    }

class UpgradeMinorRuneRanger(Upgrade):
    id = ItemUpgrade.UpgradeMinorRuneRanger
    mod_type = ItemUpgradeType.UpgradeRune

class UpgradeMajorRuneRanger(Upgrade):
    id = ItemUpgrade.UpgradeMajorRuneRanger
    mod_type = ItemUpgradeType.UpgradeRune

class UpgradeSuperiorRuneRanger(Upgrade):
    id = ItemUpgrade.UpgradeSuperiorRuneRanger
    mod_type = ItemUpgradeType.UpgradeRune

class AppliesToMinorRuneRanger(Upgrade):
    id = ItemUpgrade.AppliesToMinorRuneRanger
    mod_type = ItemUpgradeType.AppliesToRune

class AppliesToMajorRuneRanger(Upgrade):
    id = ItemUpgrade.AppliesToMajorRuneRanger
    mod_type = ItemUpgradeType.AppliesToRune

class AppliesToSuperiorRuneRanger(Upgrade):
    id = ItemUpgrade.AppliesToSuperiorRuneRanger
    mod_type = ItemUpgradeType.AppliesToRune

#endregion Ranger

#region Monk

class WanderersInsignia(Insignia):
    id = ItemUpgrade.WanderersInsignia
    names = {
        ServerLanguage.English: "Wanderer's Insignia [Monk]",
        ServerLanguage.Korean: "방랑자의 휘장 [몽크]",
        ServerLanguage.French: "Insigne [Moine] de vagabond",
        ServerLanguage.German: "Wanderer- [Mönchs]-Befähigung",
        ServerLanguage.Italian: "Insegne [Mistico] da Vagabondo",
        ServerLanguage.Spanish: "Insignia [Monje] de trotamundos",
        ServerLanguage.TraditionalChinese: "流浪者 徽記 [僧侶]",
        ServerLanguage.Japanese: "ワンダラー 記章 [モンク]",
        ServerLanguage.Polish: "[Mnich] Symbol Wędrowca",
        ServerLanguage.Russian: "Wanderer's Insignia [Monk]",
        ServerLanguage.BorkBorkBork: "Vunderer's Inseegneea [Munk]",
    }
    
    descriptions = {
        ServerLanguage.English: f"Armor +10 (vs. elemental damage)"
    }

class DisciplesInsignia(Insignia):
    id = ItemUpgrade.DisciplesInsignia
    names = {
        ServerLanguage.English: "Disciple's Insignia [Monk]",
        ServerLanguage.Korean: "사도의 휘장 [몽크]",
        ServerLanguage.French: "Insigne [Moine] de disciple",
        ServerLanguage.German: "Jünger- [Mönchs]-Befähigung",
        ServerLanguage.Italian: "Insegne [Mistico] da Discepolo",
        ServerLanguage.Spanish: "Insignia [Monje] de discípulo",
        ServerLanguage.TraditionalChinese: "門徒 徽記 [僧侶]",
        ServerLanguage.Japanese: "ディサイプル 記章 [モンク]",
        ServerLanguage.Polish: "[Mnich] Symbol Ucznia",
        ServerLanguage.Russian: "Disciple's Insignia [Monk]",
        ServerLanguage.BorkBorkBork: "Deesceeple-a's Inseegneea [Munk]",
    }
    
    descriptions = {
        ServerLanguage.English: f"Armor +15 (while affected by a Condition)"
    }

class AnchoritesInsignia(Insignia):
    id = ItemUpgrade.AnchoritesInsignia
    names = {
        ServerLanguage.English: "Anchorite's Insignia [Monk]",
        ServerLanguage.Korean: "은둔자의 휘장 [몽크]",
        ServerLanguage.French: "Insigne [Moine] d'anachorète",
        ServerLanguage.German: "Einsiedler- [Mönchs]-Befähigung",
        ServerLanguage.Italian: "Insegne [Mistico] da Anacoreta",
        ServerLanguage.Spanish: "Insignia [Monje] de anacoreta",
        ServerLanguage.TraditionalChinese: "隱士 徽記 [僧侶]",
        ServerLanguage.Japanese: "アンコライト 記章 [モンク]",
        ServerLanguage.Polish: "[Mnich] Symbol Pustelnika",
        ServerLanguage.Russian: "Anchorite's Insignia [Monk]",
        ServerLanguage.BorkBorkBork: "Unchureete-a's Inseegneea [Munk]",
    }
    
    descriptions = {
        ServerLanguage.English: f"Armor +5 (while recharging 1 or more skills)\nArmor +5 (while recharging 3 or more skills)\nArmor +5 (while recharging 5 or more skills)"

    }

class MonkRuneOfMinorHealingPrayers(AttributeRune):
    id = ItemUpgrade.MonkRuneOfMinorHealingPrayers
    rarity = Rarity.Blue

    names = {
        ServerLanguage.English: "Monk Rune of Minor Healing Prayers",
        ServerLanguage.Korean: "몽크 룬(하급 치유)",
        ServerLanguage.French: "Rune de Moine (Prières de guérison : bonus mineur)",
        ServerLanguage.German: "Mönch-Rune d. kleineren Heilgebete",
        ServerLanguage.Italian: "Runa del Mistico Preghiere Curative di grado minore",
        ServerLanguage.Spanish: "Runa de Monje (Plegarias curativas de grado menor)",
        ServerLanguage.TraditionalChinese: "初級 治療祈禱 僧侶符文",
        ServerLanguage.Japanese: "モンク ルーン (マイナー ヒーリング)",
        ServerLanguage.Polish: "Runa Mnicha (Modlitwy Uzdrawiające niższego poziomu)",
        ServerLanguage.Russian: "Monk Rune of Minor Healing Prayers",
        ServerLanguage.BorkBorkBork: "Munk Roone-a ooff Meenur Heaeleeng Praeyers",
    }

class MonkRuneOfMinorSmitingPrayers(AttributeRune):
    id = ItemUpgrade.MonkRuneOfMinorSmitingPrayers
    rarity = Rarity.Blue

    names = {
        ServerLanguage.English: "Monk Rune of Minor Smiting Prayers",
        ServerLanguage.Korean: "몽크 룬(하급 천벌)",
        ServerLanguage.French: "Rune de Moine (Prières de châtiment : bonus mineur)",
        ServerLanguage.German: "Mönch-Rune d. kleineren Peinigungsgebete",
        ServerLanguage.Italian: "Runa del Mistico Preghiere Punitive di grado minore",
        ServerLanguage.Spanish: "Runa de Monje (Plegarias de ataque de grado menor)",
        ServerLanguage.TraditionalChinese: "初級 懲戒祈禱 僧侶符文",
        ServerLanguage.Japanese: "モンク ルーン (マイナー ホーリー)",
        ServerLanguage.Polish: "Runa Mnicha (Modlitwy Ofensywne niższego poziomu)",
        ServerLanguage.Russian: "Monk Rune of Minor Smiting Prayers",
        ServerLanguage.BorkBorkBork: "Munk Roone-a ooff Meenur Smeeteeng Praeyers",
    }

class MonkRuneOfMinorProtectionPrayers(AttributeRune):
    id = ItemUpgrade.MonkRuneOfMinorProtectionPrayers
    rarity = Rarity.Blue

    names = {
        ServerLanguage.English: "Monk Rune of Minor Protection Prayers",
        ServerLanguage.Korean: "몽크 룬(하급 보호)",
        ServerLanguage.French: "Rune de Moine (Prières de protection : bonus mineur)",
        ServerLanguage.German: "Mönch-Rune d. kleineren Schutzgebete",
        ServerLanguage.Italian: "Runa del Mistico Preghiere Protettive di grado minore",
        ServerLanguage.Spanish: "Runa de Monje (Plegarias de protección de grado menor)",
        ServerLanguage.TraditionalChinese: "初級 防護祈禱 僧侶符文",
        ServerLanguage.Japanese: "モンク ルーン (マイナー プロテクション)",
        ServerLanguage.Polish: "Runa Mnicha (Modlitwy Ochronne niższego poziomu)",
        ServerLanguage.Russian: "Monk Rune of Minor Protection Prayers",
        ServerLanguage.BorkBorkBork: "Munk Roone-a ooff Meenur Prutecshun Praeyers",
    }

class MonkRuneOfMinorDivineFavor(AttributeRune):
    id = ItemUpgrade.MonkRuneOfMinorDivineFavor
    rarity = Rarity.Blue

    names = {
        ServerLanguage.English: "Monk Rune of Minor Divine Favor",
        ServerLanguage.Korean: "몽크 룬(하급 신의 은총)",
        ServerLanguage.French: "Rune de Moine (Faveur divine : bonus mineur)",
        ServerLanguage.German: "Mönch-Rune d. kleineren Gunst der Götter",
        ServerLanguage.Italian: "Runa del Mistico Favore Divino di grado minore",
        ServerLanguage.Spanish: "Runa de Monje (Favor divino de grado menor)",
        ServerLanguage.TraditionalChinese: "初級 神恩 僧侶符文",
        ServerLanguage.Japanese: "モンク ルーン (マイナー ディヴァイン)",
        ServerLanguage.Polish: "Runa Mnicha (Łaska Bogów niższego poziomu)",
        ServerLanguage.Russian: "Monk Rune of Minor Divine Favor",
        ServerLanguage.BorkBorkBork: "Munk Roone-a ooff Meenur Deefeene-a Faefur",
    }

class MonkRuneOfMajorHealingPrayers(AttributeRune):
    id = ItemUpgrade.MonkRuneOfMajorHealingPrayers
    rarity = Rarity.Purple

    property_identifiers = [
        ModifierIdentifier.HealthMinus
    ]

    names = {
        ServerLanguage.English: "Monk Rune of Major Healing Prayers",
        ServerLanguage.Korean: "몽크 룬(상급 치유)",
        ServerLanguage.French: "Rune de Moine (Prières de guérison : bonus majeur)",
        ServerLanguage.German: "Mönch-Rune d. hohen Heilgebete",
        ServerLanguage.Italian: "Runa del Mistico Preghiere Curative di grado maggiore",
        ServerLanguage.Spanish: "Runa de Monje (Plegarias curativas de grado mayor)",
        ServerLanguage.TraditionalChinese: "中級 治療祈禱 僧侶符文",
        ServerLanguage.Japanese: "モンク ルーン (メジャー ヒーリング)",
        ServerLanguage.Polish: "Runa Mnicha (Modlitwy Uzdrawiające wyższego poziomu)",
        ServerLanguage.Russian: "Monk Rune of Major Healing Prayers",
        ServerLanguage.BorkBorkBork: "Munk Roone-a ooff Maejur Heaeleeng Praeyers",
    }

class MonkRuneOfMajorSmitingPrayers(AttributeRune):
    id = ItemUpgrade.MonkRuneOfMajorSmitingPrayers
    rarity = Rarity.Purple

    property_identifiers = [
        ModifierIdentifier.HealthMinus
    ]

    names = {
        ServerLanguage.English: "Monk Rune of Major Smiting Prayers",
        ServerLanguage.Korean: "몽크 룬(상급 천벌)",
        ServerLanguage.French: "Rune de Moine (Prières de châtiment : bonus majeur)",
        ServerLanguage.German: "Mönch-Rune d. hohen Peinigungsgebete",
        ServerLanguage.Italian: "Runa del Mistico Preghiere Punitive di grado maggiore",
        ServerLanguage.Spanish: "Runa de Monje (Plegarias de ataque de grado mayor)",
        ServerLanguage.TraditionalChinese: "中級 懲戒祈禱 僧侶符文",
        ServerLanguage.Japanese: "モンク ルーン (メジャー ホーリー)",
        ServerLanguage.Polish: "Runa Mnicha (Modlitwy Ofensywne wyższego poziomu)",
        ServerLanguage.Russian: "Monk Rune of Major Smiting Prayers",
        ServerLanguage.BorkBorkBork: "Munk Roone-a ooff Maejur Smeeteeng Praeyers",
    }

class MonkRuneOfMajorProtectionPrayers(AttributeRune):
    id = ItemUpgrade.MonkRuneOfMajorProtectionPrayers
    rarity = Rarity.Purple

    property_identifiers = [
        ModifierIdentifier.HealthMinus
    ]

    names = {
        ServerLanguage.English: "Monk Rune of Major Protection Prayers",
        ServerLanguage.Korean: "몽크 룬(상급 보호)",
        ServerLanguage.French: "Rune de Moine (Prières de protection : bonus majeur)",
        ServerLanguage.German: "Mönch-Rune d. hohen Schutzgebete",
        ServerLanguage.Italian: "Runa del Mistico Preghiere Protettive di grado maggiore",
        ServerLanguage.Spanish: "Runa de Monje (Plegarias de protección de grado mayor)",
        ServerLanguage.TraditionalChinese: "中級 防護祈禱 僧侶符文",
        ServerLanguage.Japanese: "モンク ルーン (メジャー プロテクション)",
        ServerLanguage.Polish: "Runa Mnicha (Modlitwy Ochronne wyższego poziomu)",
        ServerLanguage.Russian: "Monk Rune of Major Protection Prayers",
        ServerLanguage.BorkBorkBork: "Munk Roone-a ooff Maejur Prutecshun Praeyers",
    }

class MonkRuneOfMajorDivineFavor(AttributeRune):
    id = ItemUpgrade.MonkRuneOfMajorDivineFavor
    rarity = Rarity.Purple

    property_identifiers = [
        ModifierIdentifier.HealthMinus
    ]

    names = {
        ServerLanguage.English: "Monk Rune of Major Divine Favor",
        ServerLanguage.Korean: "몽크 룬(상급 신의 은총)",
        ServerLanguage.French: "Rune de Moine (Faveur divine : bonus majeur)",
        ServerLanguage.German: "Mönch-Rune d. hohen Gunst der Götter",
        ServerLanguage.Italian: "Runa del Mistico Favore Divino di grado maggiore",
        ServerLanguage.Spanish: "Runa de Monje (Favor divino de grado mayor)",
        ServerLanguage.TraditionalChinese: "中級 神恩 僧侶符文",
        ServerLanguage.Japanese: "モンク ルーン (メジャー ディヴァイン)",
        ServerLanguage.Polish: "Runa Mnicha (Łaska Bogów wyższego poziomu)",
        ServerLanguage.Russian: "Monk Rune of Major Divine Favor",
        ServerLanguage.BorkBorkBork: "Munk Roone-a ooff Maejur Deefeene-a Faefur",
    }

class MonkRuneOfSuperiorHealingPrayers(AttributeRune):
    id = ItemUpgrade.MonkRuneOfSuperiorHealingPrayers
    rarity = Rarity.Gold

    property_identifiers = [
        ModifierIdentifier.HealthMinus
    ]

    names = {
        ServerLanguage.English: "Monk Rune of Superior Healing Prayers",
        ServerLanguage.Korean: "몽크 룬(고급 치유)",
        ServerLanguage.French: "Rune de Moine (Prières de guérison : bonus supérieur)",
        ServerLanguage.German: "Mönch-Rune d. überlegenen Heilgebete",
        ServerLanguage.Italian: "Runa del Mistico Preghiere Curative di grado supremo",
        ServerLanguage.Spanish: "Runa de Monje (Plegarias curativas de grado excepcional)",
        ServerLanguage.TraditionalChinese: "高級 治療祈禱 僧侶符文",
        ServerLanguage.Japanese: "モンク ルーン (スーペリア ヒーリング)",
        ServerLanguage.Polish: "Runa Mnicha (Modlitwy Uzdrawiające najwyższego poziomu)",
        ServerLanguage.Russian: "Monk Rune of Superior Healing Prayers",
        ServerLanguage.BorkBorkBork: "Munk Roone-a ooff Soopereeur Heaeleeng Praeyers",
    }

class MonkRuneOfSuperiorSmitingPrayers(AttributeRune):
    id = ItemUpgrade.MonkRuneOfSuperiorSmitingPrayers
    rarity = Rarity.Gold

    property_identifiers = [
        ModifierIdentifier.HealthMinus
    ]

    names = {
        ServerLanguage.English: "Monk Rune of Superior Smiting Prayers",
        ServerLanguage.Korean: "몽크 룬(고급 천벌)",
        ServerLanguage.French: "Rune de Moine (Prières de châtiment : bonus supérieur)",
        ServerLanguage.German: "Mönch-Rune d. überlegenen Peinigungsgebete",
        ServerLanguage.Italian: "Runa del Mistico Preghiere Punitive di grado supremo",
        ServerLanguage.Spanish: "Runa de Monje (Plegarias de ataque de grado excepcional)",
        ServerLanguage.TraditionalChinese: "高級 懲戒祈禱 僧侶符文",
        ServerLanguage.Japanese: "モンク ルーン (スーペリア ホーリー)",
        ServerLanguage.Polish: "Runa Mnicha (Modlitwy Ofensywne najwyższego poziomu)",
        ServerLanguage.Russian: "Monk Rune of Superior Smiting Prayers",
        ServerLanguage.BorkBorkBork: "Munk Roone-a ooff Soopereeur Smeeteeng Praeyers",
    }

class MonkRuneOfSuperiorProtectionPrayers(AttributeRune):
    id = ItemUpgrade.MonkRuneOfSuperiorProtectionPrayers
    rarity = Rarity.Gold

    property_identifiers = [
        ModifierIdentifier.HealthMinus
    ]

    names = {
        ServerLanguage.English: "Monk Rune of Superior Protection Prayers",
        ServerLanguage.Korean: "몽크 룬(고급 보호)",
        ServerLanguage.French: "Rune de Moine (Prières de protection : bonus supérieur)",
        ServerLanguage.German: "Mönch-Rune d. überlegenen Schutzgebete",
        ServerLanguage.Italian: "Runa del Mistico Preghiere Protettive di grado supremo",
        ServerLanguage.Spanish: "Runa de Monje (Plegarias de protección de grado excepcional)",
        ServerLanguage.TraditionalChinese: "高級 防護祈禱 僧侶符文",
        ServerLanguage.Japanese: "モンク ルーン (スーペリア プロテクション)",
        ServerLanguage.Polish: "Runa Mnicha (Modlitwy Ochronne najwyższego poziomu)",
        ServerLanguage.Russian: "Monk Rune of Superior Protection Prayers",
        ServerLanguage.BorkBorkBork: "Munk Roone-a ooff Soopereeur Prutecshun Praeyers",
    }

class MonkRuneOfSuperiorDivineFavor(AttributeRune):
    id = ItemUpgrade.MonkRuneOfSuperiorDivineFavor
    rarity = Rarity.Gold

    property_identifiers = [
        ModifierIdentifier.HealthMinus
    ]

    names = {
        ServerLanguage.English: "Monk Rune of Superior Divine Favor",
        ServerLanguage.Korean: "몽크 룬(고급 신의 은총)",
        ServerLanguage.French: "Rune de Moine (Faveur divine : bonus supérieur)",
        ServerLanguage.German: "Mönch-Rune d. überlegenen Gunst der Götter",
        ServerLanguage.Italian: "Runa del Mistico Favore Divino di grado supremo",
        ServerLanguage.Spanish: "Runa de Monje (Favor divino de grado excepcional)",
        ServerLanguage.TraditionalChinese: "高級 神恩 僧侶符文",
        ServerLanguage.Japanese: "モンク ルーン (スーペリア ディヴァイン)",
        ServerLanguage.Polish: "Runa Mnicha (Łaska Bogów najwyższego poziomu)",
        ServerLanguage.Russian: "Monk Rune of Superior Divine Favor",
        ServerLanguage.BorkBorkBork: "Munk Roone-a ooff Soopereeur Deefeene-a Faefur",
    }

class UpgradeMinorRuneMonk(Upgrade):
    id = ItemUpgrade.UpgradeMinorRuneMonk
    mod_type = ItemUpgradeType.UpgradeRune

class UpgradeMajorRuneMonk(Upgrade):
    id = ItemUpgrade.UpgradeMajorRuneMonk
    mod_type = ItemUpgradeType.UpgradeRune

class UpgradeSuperiorRuneMonk(Upgrade):
    id = ItemUpgrade.UpgradeSuperiorRuneMonk
    mod_type = ItemUpgradeType.UpgradeRune

class AppliesToMinorRuneMonk(Upgrade):
    id = ItemUpgrade.AppliesToMinorRuneMonk
    mod_type = ItemUpgradeType.AppliesToRune

class AppliesToMajorRuneMonk(Upgrade):
    id = ItemUpgrade.AppliesToMajorRuneMonk
    mod_type = ItemUpgradeType.AppliesToRune

class AppliesToSuperiorRuneMonk(Upgrade):
    id = ItemUpgrade.AppliesToSuperiorRuneMonk
    mod_type = ItemUpgradeType.AppliesToRune

#endregion Monk

#region Necromancer

class BloodstainedInsignia(Insignia):
    id = ItemUpgrade.BloodstainedInsignia
    names = {
        ServerLanguage.English: "Bloodstained Insignia [Necromancer]",
        ServerLanguage.Korean: "혈흔의 휘장 [네크로맨서]",
        ServerLanguage.French: "Insigne [Nécromant] de Sang",
        ServerLanguage.German: "Blutfleck- [Nekromanten]-Befähigung",
        ServerLanguage.Italian: "Insegne [Negromante] di Sangue",
        ServerLanguage.Spanish: "Insignia [Nigromante] con sangre",
        ServerLanguage.TraditionalChinese: "血腥 徽記 [死靈法師]",
        ServerLanguage.Japanese: "ブラッドステイン 記章 [ネクロマンサー]",
        ServerLanguage.Polish: "[Nekromanta] Symbol Okrwawienia",
        ServerLanguage.Russian: "Bloodstained Insignia [Necromancer]",
        ServerLanguage.BorkBorkBork: "Bluudstaeeened Inseegneea [Necrumuncer]",
    }
    
    descriptions = {
        ServerLanguage.English: f"Reduces casting time of spells that exploit corpses by 25% (Non-stacking)"
    }

class TormentorsInsignia(Insignia):
    id = ItemUpgrade.TormentorsInsignia
    names = {
        ServerLanguage.English: "Tormentor's Insignia [Necromancer]",
        ServerLanguage.Korean: "고문가의 휘장 [네크로맨서]",
        ServerLanguage.French: "Insigne [Nécromant] de persécuteur",
        ServerLanguage.German: "Folterer- [Nekromanten]-Befähigung",
        ServerLanguage.Italian: "Insegne [Negromante] da Tormentatore",
        ServerLanguage.Spanish: "Insignia [Nigromante] de torturador",
        ServerLanguage.TraditionalChinese: "苦痛者 徽記 [死靈法師]",
        ServerLanguage.Japanese: "トルメンター 記章 [ネクロマンサー]",
        ServerLanguage.Polish: "[Nekromanta] Symbol Oprawcy",
        ServerLanguage.Russian: "Tormentor's Insignia [Necromancer]",
        ServerLanguage.BorkBorkBork: "Turmentur's Inseegneea [Necrumuncer]",
    }
    
    descriptions = {
        ServerLanguage.English: f"Holy damage you receive increased by 6 (on chest armor)\nHoly damage you receive increased by 4 (on leg armor)\nHoly damage you receive increased by 2 (on other armor)\nArmor +10"

    }

class BonelaceInsignia(Insignia):
    id = ItemUpgrade.BonelaceInsignia
    names = {
        ServerLanguage.English: "Bonelace Insignia [Necromancer]",
        ServerLanguage.Korean: "해골장식 휘장 [네크로맨서]",
        ServerLanguage.French: "Insigne [Nécromant] de dentelle",
        ServerLanguage.German: "Klöppelspitzen- [Nekromanten]-Befähigung",
        ServerLanguage.Italian: "Insegne [Negromante] di Maglia d'Ossa",
        ServerLanguage.Spanish: "Insignia [Nigromante] de cordones de hueso",
        ServerLanguage.TraditionalChinese: "骨飾 徽記 [死靈法師]",
        ServerLanguage.Japanese: "ボーンレース 記章 [ネクロマンサー]",
        ServerLanguage.Polish: "[Nekromanta] Symbol Kościanej Lancy",
        ServerLanguage.Russian: "Bonelace Insignia [Necromancer]",
        ServerLanguage.BorkBorkBork: "Bunelaece-a Inseegneea [Necrumuncer]",
    }
    
    descriptions = {
        ServerLanguage.English: f"Armor +15 (vs. Piercing damage)"
    }

class MinionMastersInsignia(Insignia):
    id = ItemUpgrade.MinionMastersInsignia
    names = {
        ServerLanguage.English: "Minion Master's Insignia [Necromancer]",
        ServerLanguage.Korean: "언데드마스터의 휘장 [네크로맨서]",
        ServerLanguage.French: "Insigne [Nécromant] du Maître des serviteurs",
        ServerLanguage.German: "Dienermeister- [Nekromanten]-Befähigung",
        ServerLanguage.Italian: "Insegne [Negromante] da Domasgherri",
        ServerLanguage.Spanish: "Insignia [Nigromante] de maestro de siervos",
        ServerLanguage.TraditionalChinese: "爪牙大師 徽記 [死靈法師]",
        ServerLanguage.Japanese: "ミニオン マスター 記章 [ネクロマンサー]",
        ServerLanguage.Polish: "[Nekromanta] Symbol Władcy Sług",
        ServerLanguage.Russian: "Minion Master's Insignia [Necromancer]",
        ServerLanguage.BorkBorkBork: "Meeneeun Maester's Inseegneea [Necrumuncer]",
    }
    
    descriptions = {
        ServerLanguage.English: f"Armor +5 (while you control 1 or more minions)\nArmor +5 (while you control 3 or more minions)\nArmor +5 (while you control 5 or more minions)"

    }

class BlightersInsignia(Insignia):
    id = ItemUpgrade.BlightersInsignia
    names = {
        ServerLanguage.English: "Blighter's Insignia [Necromancer]",
        ServerLanguage.Korean: "오염자의 휘장 [네크로맨서]",
        ServerLanguage.French: "Insigne [Nécromant] de destructeur",
        ServerLanguage.German: "Verderber- [Nekromanten]-Befähigung",
        ServerLanguage.Italian: "Insegne [Negromante] da Malfattore",
        ServerLanguage.Spanish: "Insignia [Nigromante] de malhechor",
        ServerLanguage.TraditionalChinese: "破壞者 徽記 [死靈法師]",
        ServerLanguage.Japanese: "ブライター 記章 [ネクロマンサー]",
        ServerLanguage.Polish: "[Nekromanta] Symbol Złoczyńcy",
        ServerLanguage.Russian: "Blighter's Insignia [Necromancer]",
        ServerLanguage.BorkBorkBork: "Bleeghter's Inseegneea [Necrumuncer]",
    }
    
    descriptions = {
        ServerLanguage.English: f"Armor +20 (while affected by a Hex Spell)"
    }

class UndertakersInsignia(Insignia):
    id = ItemUpgrade.UndertakersInsignia
    names = {
        ServerLanguage.English: "Undertaker's Insignia [Necromancer]",
        ServerLanguage.Korean: "장의사의 휘장 [네크로맨서]",
        ServerLanguage.French: "Insigne [Nécromant] du fossoyeur",
        ServerLanguage.German: "Leichenbestatter- [Nekromanten]-Befähigung",
        ServerLanguage.Italian: "Insegne [Negromante] da Becchino",
        ServerLanguage.Spanish: "Insignia [Nigromante] de enterrador",
        ServerLanguage.TraditionalChinese: "承受者 徽記 [死靈法師]",
        ServerLanguage.Japanese: "アンダーテイカー 記章 [ネクロマンサー]",
        ServerLanguage.Polish: "[Nekromanta] Symbol Grabarza",
        ServerLanguage.Russian: "Undertaker's Insignia [Necromancer]",
        ServerLanguage.BorkBorkBork: "Undertaeker's Inseegneea [Necrumuncer]",
    }
    
    descriptions = {
        ServerLanguage.English: f"Armor +5 (while health is below 80%)\nArmor +5 (while health is below 60%)\nArmor +5 (while health is below 40%)\nArmor +5 (while health is below 20%)"

    }

class NecromancerRuneOfMinorBloodMagic(AttributeRune):
    id = ItemUpgrade.NecromancerRuneOfMinorBloodMagic
    rarity = Rarity.Blue

    names = {
        ServerLanguage.English: "Necromancer Rune of Minor Blood Magic",
        ServerLanguage.Korean: "네크로맨서 룬(하급 피)",
        ServerLanguage.French: "Rune de Nécromant (Magie du sang : bonus mineur)",
        ServerLanguage.German: "Nekromanten-Rune d. kleineren Blutmagie",
        ServerLanguage.Italian: "Runa del Negromante Magia del Sangue di grado minore",
        ServerLanguage.Spanish: "Runa de Nigromante (Magia de sangre de grado menor)",
        ServerLanguage.TraditionalChinese: "初級 血魔法 死靈法師符文",
        ServerLanguage.Japanese: "ネクロマンサー ルーン (マイナー ブラッド)",
        ServerLanguage.Polish: "Runa Nekromanty (Magia Krwi niższego poziomu)",
        ServerLanguage.Russian: "Necromancer Rune of Minor Blood Magic",
        ServerLanguage.BorkBorkBork: "Necrumuncer Roone-a ooff Meenur Bluud Maegeec",
    }

class NecromancerRuneOfMinorDeathMagic(AttributeRune):
    id = ItemUpgrade.NecromancerRuneOfMinorDeathMagic
    rarity = Rarity.Blue

    names = {
        ServerLanguage.English: "Necromancer Rune of Minor Death Magic",
        ServerLanguage.Korean: "네크로맨서 룬(하급 죽음)",
        ServerLanguage.French: "Rune de Nécromant (Magie de la mort : bonus mineur)",
        ServerLanguage.German: "Nekromanten-Rune d. kleineren Todesmagie",
        ServerLanguage.Italian: "Runa del Negromante Magia della Morte di grado minore",
        ServerLanguage.Spanish: "Runa de Nigromante (Magia de muerte de grado menor)",
        ServerLanguage.TraditionalChinese: "初級 死亡魔法 死靈法師符文",
        ServerLanguage.Japanese: "ネクロマンサー ルーン (マイナー デス)",
        ServerLanguage.Polish: "Runa Nekromanty (Magia Śmierci niższego poziomu)",
        ServerLanguage.Russian: "Necromancer Rune of Minor Death Magic",
        ServerLanguage.BorkBorkBork: "Necrumuncer Roone-a ooff Meenur Deaet Maegeec",
    }

class NecromancerRuneOfMinorCurses(AttributeRune):
    id = ItemUpgrade.NecromancerRuneOfMinorCurses
    rarity = Rarity.Blue

    names = {
        ServerLanguage.English: "Necromancer Rune of Minor Curses",
        ServerLanguage.Korean: "네크로맨서 룬(하급 저주)",
        ServerLanguage.French: "Rune de Nécromant (Malédictions : bonus mineur)",
        ServerLanguage.German: "Nekromanten-Rune d. kleineren Flüche",
        ServerLanguage.Italian: "Runa del Negromante Maledizioni di grado minore",
        ServerLanguage.Spanish: "Runa de Nigromante (Maldiciones de grado menor)",
        ServerLanguage.TraditionalChinese: "初級 詛咒 死靈法師符文",
        ServerLanguage.Japanese: "ネクロマンサー ルーン (マイナー カース)",
        ServerLanguage.Polish: "Runa Nekromanty (Klątwy niższego poziomu)",
        ServerLanguage.Russian: "Necromancer Rune of Minor Curses",
        ServerLanguage.BorkBorkBork: "Necrumuncer Roone-a ooff Meenur Coorses",
    }

class NecromancerRuneOfMinorSoulReaping(AttributeRune):
    id = ItemUpgrade.NecromancerRuneOfMinorSoulReaping
    rarity = Rarity.Blue

    names = {
        ServerLanguage.English: "Necromancer Rune of Minor Soul Reaping",
        ServerLanguage.Korean: "네크로맨서 룬(하급 영혼)",
        ServerLanguage.French: "Rune de Nécromant (Moisson des âmes : bonus mineur)",
        ServerLanguage.German: "Nekromanten-Rune d. kleineren Seelensammlung",
        ServerLanguage.Italian: "Runa del Negromante Sottrazione dell'Anima di grado minore",
        ServerLanguage.Spanish: "Runa de Nigromante (Cosecha de almas de grado menor)",
        ServerLanguage.TraditionalChinese: "初級 靈魂吸取 死靈法師符文",
        ServerLanguage.Japanese: "ネクロマンサー ルーン (マイナー ソウル リーピング)",
        ServerLanguage.Polish: "Runa Nekromanty (Wydzieranie Duszy niższego poziomu)",
        ServerLanguage.Russian: "Necromancer Rune of Minor Soul Reaping",
        ServerLanguage.BorkBorkBork: "Necrumuncer Roone-a ooff Meenur Suool Reaepeeng",
    }

class NecromancerRuneOfMajorBloodMagic(AttributeRune):
    id = ItemUpgrade.NecromancerRuneOfMajorBloodMagic
    rarity = Rarity.Purple

    property_identifiers = [
        ModifierIdentifier.HealthMinus
    ]

    names = {
        ServerLanguage.English: "Necromancer Rune of Major Blood Magic",
        ServerLanguage.Korean: "네크로맨서 룬(상급 피)",
        ServerLanguage.French: "Rune de Nécromant (Magie du sang : bonus majeur)",
        ServerLanguage.German: "Nekromanten-Rune d. hohen Blutmagie",
        ServerLanguage.Italian: "Runa del Negromante Magia del Sangue di grado maggiore",
        ServerLanguage.Spanish: "Runa de Nigromante (Magia de sangre de grado mayor)",
        ServerLanguage.TraditionalChinese: "中級 血魔法 死靈法師符文",
        ServerLanguage.Japanese: "ネクロマンサー ルーン (メジャー ブラッド)",
        ServerLanguage.Polish: "Runa Nekromanty (Magia Krwi wyższego poziomu)",
        ServerLanguage.Russian: "Necromancer Rune of Major Blood Magic",
        ServerLanguage.BorkBorkBork: "Necrumuncer Roone-a ooff Maejur Bluud Maegeec",
    }

class NecromancerRuneOfMajorDeathMagic(AttributeRune):
    id = ItemUpgrade.NecromancerRuneOfMajorDeathMagic
    rarity = Rarity.Purple

    property_identifiers = [
        ModifierIdentifier.HealthMinus
    ]

    names = {
        ServerLanguage.English: "Necromancer Rune of Major Death Magic",
        ServerLanguage.Korean: "네크로맨서 룬(상급 죽음)",
        ServerLanguage.French: "Rune de Nécromant (Magie de la mort : bonus majeur)",
        ServerLanguage.German: "Nekromanten-Rune d. hohen Todesmagie",
        ServerLanguage.Italian: "Runa del Negromante Magia della Morte di grado maggiore",
        ServerLanguage.Spanish: "Runa de Nigromante (Magia de muerte de grado mayor)",
        ServerLanguage.TraditionalChinese: "中級 死亡魔法 死靈法師符文",
        ServerLanguage.Japanese: "ネクロマンサー ルーン (メジャー デス)",
        ServerLanguage.Polish: "Runa Nekromanty (Magia Śmierci wyższego poziomu)",
        ServerLanguage.Russian: "Necromancer Rune of Major Death Magic",
        ServerLanguage.BorkBorkBork: "Necrumuncer Roone-a ooff Maejur Deaet Maegeec",
    }

class NecromancerRuneOfMajorCurses(AttributeRune):
    id = ItemUpgrade.NecromancerRuneOfMajorCurses
    rarity = Rarity.Purple

    property_identifiers = [
        ModifierIdentifier.HealthMinus
    ]

    names = {
        ServerLanguage.English: "Necromancer Rune of Major Curses",
        ServerLanguage.Korean: "네크로맨서 룬(상급 저주)",
        ServerLanguage.French: "Rune de Nécromant (Malédictions : bonus majeur)",
        ServerLanguage.German: "Nekromanten-Rune d. hohen Flüche",
        ServerLanguage.Italian: "Runa del Negromante Maledizioni di grado maggiore",
        ServerLanguage.Spanish: "Runa de Nigromante (Maldiciones de grado mayor)",
        ServerLanguage.TraditionalChinese: "中級 詛咒 死靈法師符文",
        ServerLanguage.Japanese: "ネクロマンサー ルーン (メジャー カース)",
        ServerLanguage.Polish: "Runa Nekromanty (Klątwy wyższego poziomu)",
        ServerLanguage.Russian: "Necromancer Rune of Major Curses",
        ServerLanguage.BorkBorkBork: "Necrumuncer Roone-a ooff Maejur Coorses",
    }

class NecromancerRuneOfMajorSoulReaping(AttributeRune):
    id = ItemUpgrade.NecromancerRuneOfMajorSoulReaping
    rarity = Rarity.Purple

    property_identifiers = [
        ModifierIdentifier.HealthMinus
    ]

    names = {
        ServerLanguage.English: "Necromancer Rune of Major Soul Reaping",
        ServerLanguage.Korean: "네크로맨서 룬(상급 영혼)",
        ServerLanguage.French: "Rune de Nécromant (Moisson des âmes : bonus majeur)",
        ServerLanguage.German: "Nekromanten-Rune d. hohen Seelensammlung",
        ServerLanguage.Italian: "Runa del Negromante Sottrazione dell'Anima di grado maggiore",
        ServerLanguage.Spanish: "Runa de Nigromante (Cosecha de almas de grado mayor)",
        ServerLanguage.TraditionalChinese: "中級 靈魂吸取 死靈法師符文",
        ServerLanguage.Japanese: "ネクロマンサー ルーン (メジャー ソウル リーピング)",
        ServerLanguage.Polish: "Runa Nekromanty (Wydzieranie Duszy wyższego poziomu)",
        ServerLanguage.Russian: "Necromancer Rune of Major Soul Reaping",
        ServerLanguage.BorkBorkBork: "Necrumuncer Roone-a ooff Maejur Suool Reaepeeng",
    }

class NecromancerRuneOfSuperiorBloodMagic(AttributeRune):
    id = ItemUpgrade.NecromancerRuneOfSuperiorBloodMagic
    rarity = Rarity.Gold

    property_identifiers = [
        ModifierIdentifier.HealthMinus
    ]

    names = {
        ServerLanguage.English: "Necromancer Rune of Superior Blood Magic",
        ServerLanguage.Korean: "네크로맨서 룬(고급 피)",
        ServerLanguage.French: "Rune de Nécromant (Magie du sang : bonus supérieur)",
        ServerLanguage.German: "Nekromanten-Rune d. überlegenen Blutmagie",
        ServerLanguage.Italian: "Runa del Negromante Magia del Sangue di grado supremo",
        ServerLanguage.Spanish: "Runa de Nigromante (Magia de sangre de grado excepcional)",
        ServerLanguage.TraditionalChinese: "高級 血魔法 死靈法師符文",
        ServerLanguage.Japanese: "ネクロマンサー ルーン (スーペリア ブラッド)",
        ServerLanguage.Polish: "Runa Nekromanty (Magia Krwi najwyższego poziomu)",
        ServerLanguage.Russian: "Necromancer Rune of Superior Blood Magic",
        ServerLanguage.BorkBorkBork: "Necrumuncer Roone-a ooff Soopereeur Bluud Maegeec",
    }

class NecromancerRuneOfSuperiorDeathMagic(AttributeRune):
    id = ItemUpgrade.NecromancerRuneOfSuperiorDeathMagic
    rarity = Rarity.Gold

    property_identifiers = [
        ModifierIdentifier.HealthMinus
    ]

    names = {
        ServerLanguage.English: "Necromancer Rune of Superior Death Magic",
        ServerLanguage.Korean: "네크로맨서 룬(고급 죽음)",
        ServerLanguage.French: "Rune de Nécromant (Magie de la mort : bonus supérieur)",
        ServerLanguage.German: "Nekromanten-Rune d. überlegenen Todesmagie",
        ServerLanguage.Italian: "Runa del Negromante Magia della Morte di grado supremo",
        ServerLanguage.Spanish: "Runa de Nigromante (Magia de muerte de grado excepcional)",
        ServerLanguage.TraditionalChinese: "高級 死亡魔法 死靈法師符文",
        ServerLanguage.Japanese: "ネクロマンサー ルーン (スーペリア デス)",
        ServerLanguage.Polish: "Runa Nekromanty (Magia Śmierci najwyższego poziomu)",
        ServerLanguage.Russian: "Necromancer Rune of Superior Death Magic",
        ServerLanguage.BorkBorkBork: "Necrumuncer Roone-a ooff Soopereeur Deaet Maegeec",
    }

class NecromancerRuneOfSuperiorCurses(AttributeRune):
    id = ItemUpgrade.NecromancerRuneOfSuperiorCurses
    rarity = Rarity.Gold

    property_identifiers = [
        ModifierIdentifier.HealthMinus
    ]

    names = {
        ServerLanguage.English: "Necromancer Rune of Superior Curses",
        ServerLanguage.Korean: "네크로맨서 룬(고급 저주)",
        ServerLanguage.French: "Rune de Nécromant (Malédictions : bonus supérieur)",
        ServerLanguage.German: "Nekromanten-Rune d. überlegenen Flüche",
        ServerLanguage.Italian: "Runa del Negromante Maledizioni di grado supremo",
        ServerLanguage.Spanish: "Runa de Nigromante (Maldiciones de grado excepcional)",
        ServerLanguage.TraditionalChinese: "高級 詛咒 死靈法師符文",
        ServerLanguage.Japanese: "ネクロマンサー ルーン (スーペリア カース)",
        ServerLanguage.Polish: "Runa Nekromanty (Klątwy najwyższego poziomu)",
        ServerLanguage.Russian: "Necromancer Rune of Superior Curses",
        ServerLanguage.BorkBorkBork: "Necrumuncer Roone-a ooff Soopereeur Coorses",
    }

class NecromancerRuneOfSuperiorSoulReaping(AttributeRune):
    id = ItemUpgrade.NecromancerRuneOfSuperiorSoulReaping
    rarity = Rarity.Gold

    property_identifiers = [
        ModifierIdentifier.HealthMinus
    ]

    names = {
        ServerLanguage.English: "Necromancer Rune of Superior Soul Reaping",
        ServerLanguage.Korean: "네크로맨서 룬(고급 영혼)",
        ServerLanguage.French: "Rune de Nécromant (Moisson des âmes : bonus supérieur)",
        ServerLanguage.German: "Nekromanten-Rune d. überlegenen Seelensammlung",
        ServerLanguage.Italian: "Runa del Negromante Sottrazione dell'Anima di grado supremo",
        ServerLanguage.Spanish: "Runa de Nigromante (Cosecha de almas de grado excepcional)",
        ServerLanguage.TraditionalChinese: "高級 靈魂吸取 死靈法師符文",
        ServerLanguage.Japanese: "ネクロマンサー ルーン (スーペリア ソウル リーピング)",
        ServerLanguage.Polish: "Runa Nekromanty (Wydzieranie Duszy najwyższego poziomu)",
        ServerLanguage.Russian: "Necromancer Rune of Superior Soul Reaping",
        ServerLanguage.BorkBorkBork: "Necrumuncer Roone-a ooff Soopereeur Suool Reaepeeng",
    }

class UpgradeMinorRuneNecromancer(Upgrade):
    id = ItemUpgrade.UpgradeMinorRuneNecromancer
    mod_type = ItemUpgradeType.UpgradeRune

class UpgradeMajorRuneNecromancer(Upgrade):
    id = ItemUpgrade.UpgradeMajorRuneNecromancer
    mod_type = ItemUpgradeType.UpgradeRune

class UpgradeSuperiorRuneNecromancer(Upgrade):
    id = ItemUpgrade.UpgradeSuperiorRuneNecromancer
    mod_type = ItemUpgradeType.UpgradeRune

class AppliesToMinorRuneNecromancer(Upgrade):
    id = ItemUpgrade.AppliesToMinorRuneNecromancer
    mod_type = ItemUpgradeType.AppliesToRune

class AppliesToMajorRuneNecromancer(Upgrade):
    id = ItemUpgrade.AppliesToMajorRuneNecromancer
    mod_type = ItemUpgradeType.AppliesToRune

class AppliesToSuperiorRuneNecromancer(Upgrade):
    id = ItemUpgrade.AppliesToSuperiorRuneNecromancer
    mod_type = ItemUpgradeType.AppliesToRune

#endregion Necromancer

#region Mesmer

class VirtuososInsignia(Insignia):
    id = ItemUpgrade.VirtuososInsignia
    names = {
        ServerLanguage.English: "Virtuoso's Insignia [Mesmer]",
        ServerLanguage.Korean: "거장의 휘장 [메스머]",
        ServerLanguage.French: "Insigne [Envoûteur] de virtuose",
        ServerLanguage.German: "Virtuosen- [Mesmer]-Befähigung",
        ServerLanguage.Italian: "Insegne [Ipnotizzatore] da Intenditore",
        ServerLanguage.Spanish: "Insignia [Hipnotizador] de virtuoso",
        ServerLanguage.TraditionalChinese: "鑑賞家 徽記 [幻術師]",
        ServerLanguage.Japanese: "ヴァーチュオーソ 記章 [メスマー]",
        ServerLanguage.Polish: "[Mesmer] Symbol Wirtuoza",
        ServerLanguage.Russian: "Virtuoso's Insignia [Mesmer]",
        ServerLanguage.BorkBorkBork: "Furtoousu's Inseegneea [Mesmer]",
    }
    
    descriptions = {
        ServerLanguage.English: f"Armor +15 (while activating skills)"
    }

class ArtificersInsignia(Insignia):
    id = ItemUpgrade.ArtificersInsignia
    names = {
        ServerLanguage.English: "Artificer's Insignia [Mesmer]",
        ServerLanguage.Korean: "장인의 휘장 [메스머]",
        ServerLanguage.French: "Insigne [Envoûteur] de l'artisan",
        ServerLanguage.German: "Feuerwerker- [Mesmer]-Befähigung",
        ServerLanguage.Italian: "Insegne [Ipnotizzatore] da Artefice",
        ServerLanguage.Spanish: "Insignia [Hipnotizador] de artífice",
        ServerLanguage.TraditionalChinese: "巧匠 徽記 [幻術師]",
        ServerLanguage.Japanese: "アーティファサー 記章 [メスマー]",
        ServerLanguage.Polish: "[Mesmer] Symbol Rzemieślnika",
        ServerLanguage.Russian: "Artificer's Insignia [Mesmer]",
        ServerLanguage.BorkBorkBork: "Aerteeffeecer's Inseegneea [Mesmer]",
    }
    
    descriptions = {
        ServerLanguage.English: f"Armor +3 (for each equipped Signet)"
    }

class ProdigysInsignia(Insignia):
    id = ItemUpgrade.ProdigysInsignia
    names = {
        ServerLanguage.English: "Prodigy's Insignia [Mesmer]",
        ServerLanguage.Korean: "천재의 휘장 [메스머]",
        ServerLanguage.French: "Insigne [Envoûteur] prodige",
        ServerLanguage.German: "Wunder- [Mesmer]-Befähigung",
        ServerLanguage.Italian: "Insegne [Ipnotizzatore] da Prodigio",
        ServerLanguage.Spanish: "Insignia [Hipnotizador] de prodigio",
        ServerLanguage.TraditionalChinese: "奇蹟 徽記 [幻術師]",
        ServerLanguage.Japanese: "プロディジー 記章 [メスマー]",
        ServerLanguage.Polish: "[Mesmer] Symbol Geniusza",
        ServerLanguage.Russian: "Prodigy's Insignia [Mesmer]",
        ServerLanguage.BorkBorkBork: "Prudeegy's Inseegneea [Mesmer]",
    }
    
    descriptions = {
        ServerLanguage.English: f"Armor +5 (while recharging 1 or more skills)\nArmor +5 (while recharging 3 or more skills)\nArmor +5 (while recharging 5 or more skills)"
    }

class MesmerRuneOfMinorFastCasting(AttributeRune):
    id = ItemUpgrade.MesmerRuneOfMinorFastCasting
    rarity = Rarity.Blue

    names = {
        ServerLanguage.English: "Mesmer Rune of Minor Fast Casting",
        ServerLanguage.Korean: "메스머 룬(하급 빠른 시전)",
        ServerLanguage.French: "Rune d'Envoûteur (Incantation rapide : bonus mineur)",
        ServerLanguage.German: "Mesmer-Rune d. kleineren Schnellwirkung",
        ServerLanguage.Italian: "Runa dell'Ipnotizzatore Lancio Rapido di grado minore",
        ServerLanguage.Spanish: "Runa de Hipnotizador (Lanzar conjuros rápido de grado menor)",
        ServerLanguage.TraditionalChinese: "初級 快速施法 幻術師符文",
        ServerLanguage.Japanese: "メスマー ルーン (マイナー ファスト キャスト)",
        ServerLanguage.Polish: "Runa Mesmera (Szybkie Rzucanie Czarów niższego poziomu)",
        ServerLanguage.Russian: "Mesmer Rune of Minor Fast Casting",
        ServerLanguage.BorkBorkBork: "Mesmer Roone-a ooff Meenur Faest Caesteeng",
    }

class MesmerRuneOfMinorDominationMagic(AttributeRune):
    id = ItemUpgrade.MesmerRuneOfMinorDominationMagic
    rarity = Rarity.Blue

    names = {
        ServerLanguage.English: "Mesmer Rune of Minor Domination Magic",
        ServerLanguage.Korean: "메스머 룬(하급 지배)",
        ServerLanguage.French: "Rune d'Envoûteur (Magie de domination : bonus mineur)",
        ServerLanguage.German: "Mesmer-Rune d. kleineren Beherrschungsmagie",
        ServerLanguage.Italian: "Runa dell'Ipnotizzatore Magia del Dominio di grado minore",
        ServerLanguage.Spanish: "Runa de Hipnotizador (Magia de dominación de grado menor)",
        ServerLanguage.TraditionalChinese: "初級 支配魔法 幻術師符文",
        ServerLanguage.Japanese: "メスマー ルーン (マイナー ドミネーション)",
        ServerLanguage.Polish: "Runa Mesmera (Magia Dominacji niższego poziomu)",
        ServerLanguage.Russian: "Mesmer Rune of Minor Domination Magic",
        ServerLanguage.BorkBorkBork: "Mesmer Roone-a ooff Meenur Dumeenaeshun Maegeec",
    }

class MesmerRuneOfMinorIllusionMagic(AttributeRune):
    id = ItemUpgrade.MesmerRuneOfMinorIllusionMagic
    rarity = Rarity.Blue

    names = {
        ServerLanguage.English: "Mesmer Rune of Minor Illusion Magic",
        ServerLanguage.Korean: "메스머 룬(하급 환상)",
        ServerLanguage.French: "Rune d'Envoûteur (Magie de l'illusion : bonus mineur)",
        ServerLanguage.German: "Mesmer-Rune d. kleineren Illusionsmagie",
        ServerLanguage.Italian: "Runa dell'Ipnotizzatore Magia Illusoria di grado minore",
        ServerLanguage.Spanish: "Runa de Hipnotizador (Magia de ilusión de grado menor)",
        ServerLanguage.TraditionalChinese: "初級 幻術魔法 幻術師符文",
        ServerLanguage.Japanese: "メスマー ルーン (マイナー イリュージョン)",
        ServerLanguage.Polish: "Runa Mesmera (Magia Iluzji niższego poziomu)",
        ServerLanguage.Russian: "Mesmer Rune of Minor Illusion Magic",
        ServerLanguage.BorkBorkBork: "Mesmer Roone-a ooff Meenur Illooseeun Maegeec",
    }

class MesmerRuneOfMinorInspirationMagic(AttributeRune):
    id = ItemUpgrade.MesmerRuneOfMinorInspirationMagic
    rarity = Rarity.Blue

    names = {
        ServerLanguage.English: "Mesmer Rune of Minor Inspiration Magic",
        ServerLanguage.Korean: "메스머 룬(하급 영감)",
        ServerLanguage.French: "Rune d'Envoûteur (Magie de l'inspiration : bonus mineur)",
        ServerLanguage.German: "Mesmer-Rune d. kleineren Inspirationsmagie",
        ServerLanguage.Italian: "Runa dell'Ipnotizzatore Magia di Ispirazione di grado minore",
        ServerLanguage.Spanish: "Runa de Hipnotizador (Magia de inspiración de grado menor)",
        ServerLanguage.TraditionalChinese: "初級 靈感魔法 幻術師符文",
        ServerLanguage.Japanese: "メスマー ルーン (マイナー インスピレーション)",
        ServerLanguage.Polish: "Runa Mesmera (Magia Inspiracji niższego poziomu)",
        ServerLanguage.Russian: "Mesmer Rune of Minor Inspiration Magic",
        ServerLanguage.BorkBorkBork: "Mesmer Roone-a ooff Meenur Inspuraeshun Maegeec",
    }

class MesmerRuneOfMajorFastCasting(AttributeRune):
    id = ItemUpgrade.MesmerRuneOfMajorFastCasting
    rarity = Rarity.Purple

    property_identifiers = [
        ModifierIdentifier.HealthMinus
    ]

    names = {
        ServerLanguage.English: "Mesmer Rune of Major Fast Casting",
        ServerLanguage.Korean: "메스머 룬(상급 빠른 시전)",
        ServerLanguage.French: "Rune d'Envoûteur (Incantation rapide : bonus majeur)",
        ServerLanguage.German: "Mesmer-Rune d. hohen Schnellwirkung",
        ServerLanguage.Italian: "Runa dell'Ipnotizzatore Lancio Rapido di grado maggiore",
        ServerLanguage.Spanish: "Runa de Hipnotizador (Lanzar conjuros rápido de grado mayor)",
        ServerLanguage.TraditionalChinese: "中級 快速施法 幻術師符文",
        ServerLanguage.Japanese: "メスマー ルーン (メジャー ファスト キャスト)",
        ServerLanguage.Polish: "Runa Mesmera (Szybkie Rzucanie Czarów wyższego poziomu)",
        ServerLanguage.Russian: "Mesmer Rune of Major Fast Casting",
        ServerLanguage.BorkBorkBork: "Mesmer Roone-a ooff Maejur Faest Caesteeng",
    }

class MesmerRuneOfMajorDominationMagic(AttributeRune):
    id = ItemUpgrade.MesmerRuneOfMajorDominationMagic
    rarity = Rarity.Purple

    property_identifiers = [
        ModifierIdentifier.HealthMinus
    ]

    names = {
        ServerLanguage.English: "Mesmer Rune of Major Domination Magic",
        ServerLanguage.Korean: "메스머 룬(상급 지배)",
        ServerLanguage.French: "Rune d'Envoûteur (Magie de domination : bonus majeur)",
        ServerLanguage.German: "Mesmer-Rune d. hohen Beherrschungsmagie",
        ServerLanguage.Italian: "Runa dell'Ipnotizzatore Magia del Dominio di grado maggiore",
        ServerLanguage.Spanish: "Runa de Hipnotizador (Magia de dominación de grado mayor)",
        ServerLanguage.TraditionalChinese: "中級 支配魔法 幻術師符文",
        ServerLanguage.Japanese: "メスマー ルーン (メジャー ドミネーション)",
        ServerLanguage.Polish: "Runa Mesmera (Magia Dominacji wyższego poziomu)",
        ServerLanguage.Russian: "Mesmer Rune of Major Domination Magic",
        ServerLanguage.BorkBorkBork: "Mesmer Roone-a ooff Maejur Dumeenaeshun Maegeec",
    }

class MesmerRuneOfMajorIllusionMagic(AttributeRune):
    id = ItemUpgrade.MesmerRuneOfMajorIllusionMagic
    rarity = Rarity.Purple

    property_identifiers = [
        ModifierIdentifier.HealthMinus
    ]

    names = {
        ServerLanguage.English: "Mesmer Rune of Major Illusion Magic",
        ServerLanguage.Korean: "메스머 룬(상급 환상)",
        ServerLanguage.French: "Rune d'Envoûteur (Magie de l'illusion : bonus majeur)",
        ServerLanguage.German: "Mesmer-Rune d. hohen Illusionsmagie",
        ServerLanguage.Italian: "Runa dell'Ipnotizzatore Magia Illusoria di grado maggiore",
        ServerLanguage.Spanish: "Runa de Hipnotizador (Magia de ilusión de grado mayor)",
        ServerLanguage.TraditionalChinese: "中級 幻術魔法 幻術師符文",
        ServerLanguage.Japanese: "メスマー ルーン (メジャー イリュージョン)",
        ServerLanguage.Polish: "Runa Mesmera (Magia Iluzji wyższego poziomu)",
        ServerLanguage.Russian: "Mesmer Rune of Major Illusion Magic",
        ServerLanguage.BorkBorkBork: "Mesmer Roone-a ooff Maejur Illooseeun Maegeec",
    }

class MesmerRuneOfMajorInspirationMagic(AttributeRune):
    id = ItemUpgrade.MesmerRuneOfMajorInspirationMagic
    rarity = Rarity.Purple

    property_identifiers = [
        ModifierIdentifier.HealthMinus
    ]

    names = {
        ServerLanguage.English: "Mesmer Rune of Major Inspiration Magic",
        ServerLanguage.Korean: "메스머 룬(상급 영감)",
        ServerLanguage.French: "Rune d'Envoûteur (Magie de l'inspiration : bonus majeur)",
        ServerLanguage.German: "Mesmer-Rune d. hohen Inspirationsmagie",
        ServerLanguage.Italian: "Runa dell'Ipnotizzatore Magia di Ispirazione di grado maggiore",
        ServerLanguage.Spanish: "Runa de Hipnotizador (Magia de inspiración de grado mayor)",
        ServerLanguage.TraditionalChinese: "中級 靈感魔法 幻術師符文",
        ServerLanguage.Japanese: "メスマー ルーン (メジャー インスピレーション)",
        ServerLanguage.Polish: "Runa Mesmera (Magia Inspiracji wyższego poziomu)",
        ServerLanguage.Russian: "Mesmer Rune of Major Inspiration Magic",
        ServerLanguage.BorkBorkBork: "Mesmer Roone-a ooff Maejur Inspuraeshun Maegeec",
    }

class MesmerRuneOfSuperiorFastCasting(AttributeRune):
    id = ItemUpgrade.MesmerRuneOfSuperiorFastCasting
    rarity = Rarity.Gold

    property_identifiers = [
        ModifierIdentifier.HealthMinus
    ]

    names = {
        ServerLanguage.English: "Mesmer Rune of Superior Fast Casting",
        ServerLanguage.Korean: "메스머 룬(고급 빠른 시전)",
        ServerLanguage.French: "Rune d'Envoûteur (Incantation rapide : bonus supérieur)",
        ServerLanguage.German: "Mesmer-Rune d. überlegenen Schnellwirkung",
        ServerLanguage.Italian: "Runa dell'Ipnotizzatore Lancio Rapido di grado supremo",
        ServerLanguage.Spanish: "Runa de Hipnotizador (Lanzar conjuros rápido de grado excepcional)",
        ServerLanguage.TraditionalChinese: "高級 快速施法 幻術師符文",
        ServerLanguage.Japanese: "メスマー ルーン (スーペリア ファスト キャスト)",
        ServerLanguage.Polish: "Runa Mesmera (Szybkie Rzucanie Czarów najwyższego poziomu)",
        ServerLanguage.Russian: "Mesmer Rune of Superior Fast Casting",
        ServerLanguage.BorkBorkBork: "Mesmer Roone-a ooff Soopereeur Faest Caesteeng",
    }

class MesmerRuneOfSuperiorDominationMagic(AttributeRune):
    id = ItemUpgrade.MesmerRuneOfSuperiorDominationMagic
    rarity = Rarity.Gold

    property_identifiers = [
        ModifierIdentifier.HealthMinus
    ]

    names = {
        ServerLanguage.English: "Mesmer Rune of Superior Domination Magic",
        ServerLanguage.Korean: "메스머 룬(고급 지배)",
        ServerLanguage.French: "Rune d'Envoûteur (Magie de domination : bonus supérieur)",
        ServerLanguage.German: "Mesmer-Rune d. überlegenen Beherrschungsmagie",
        ServerLanguage.Italian: "Runa dell'Ipnotizzatore Magia del Dominio di grado supremo",
        ServerLanguage.Spanish: "Runa de Hipnotizador (Magia de dominación de grado excepcional)",
        ServerLanguage.TraditionalChinese: "高級 支配魔法 幻術師符文",
        ServerLanguage.Japanese: "メスマー ルーン (スーペリア ドミネーション)",
        ServerLanguage.Polish: "Runa Mesmera (Magia Dominacji najwyższego poziomu)",
        ServerLanguage.Russian: "Mesmer Rune of Superior Domination Magic",
        ServerLanguage.BorkBorkBork: "Mesmer Roone-a ooff Soopereeur Dumeenaeshun Maegeec",
    }

class MesmerRuneOfSuperiorIllusionMagic(AttributeRune):
    id = ItemUpgrade.MesmerRuneOfSuperiorIllusionMagic
    rarity = Rarity.Gold

    property_identifiers = [
        ModifierIdentifier.HealthMinus
    ]

    names = {
        ServerLanguage.English: "Mesmer Rune of Superior Illusion Magic",
        ServerLanguage.Korean: "메스머 룬(고급 환상)",
        ServerLanguage.French: "Rune d'Envoûteur (Magie de l'illusion : bonus supérieur)",
        ServerLanguage.German: "Mesmer-Rune d. überlegenen Illusionsmagie",
        ServerLanguage.Italian: "Runa dell'Ipnotizzatore Magia Illusoria di grado supremo",
        ServerLanguage.Spanish: "Runa de Hipnotizador (Magia de ilusión de grado excepcional)",
        ServerLanguage.TraditionalChinese: "高級 幻術魔法 幻術師符文",
        ServerLanguage.Japanese: "メスマー ルーン (スーペリア イリュージョン)",
        ServerLanguage.Polish: "Runa Mesmera (Magia Iluzji najwyższego poziomu)",
        ServerLanguage.Russian: "Mesmer Rune of Superior Illusion Magic",
        ServerLanguage.BorkBorkBork: "Mesmer Roone-a ooff Soopereeur Illooseeun Maegeec",
    }

class MesmerRuneOfSuperiorInspirationMagic(AttributeRune):
    id = ItemUpgrade.MesmerRuneOfSuperiorInspirationMagic
    rarity = Rarity.Gold

    property_identifiers = [
        ModifierIdentifier.HealthMinus
    ]

    names = {
        ServerLanguage.English: "Mesmer Rune of Superior Inspiration Magic",
        ServerLanguage.Korean: "메스머 룬(고급 영감)",
        ServerLanguage.French: "Rune d'Envoûteur (Magie de l'inspiration : bonus supérieur)",
        ServerLanguage.German: "Mesmer-Rune d. überlegenen Inspirationsmagie",
        ServerLanguage.Italian: "Runa dell'Ipnotizzatore Magia di Ispirazione di grado supremo",
        ServerLanguage.Spanish: "Runa de Hipnotizador (Magia de inspiración de grado excepcional)",
        ServerLanguage.TraditionalChinese: "高級 靈感魔法 幻術師符文",
        ServerLanguage.Japanese: "メスマー ルーン (スーペリア インスピレーション)",
        ServerLanguage.Polish: "Runa Mesmera (Magia Inspiracji najwyższego poziomu)",
        ServerLanguage.Russian: "Mesmer Rune of Superior Inspiration Magic",
        ServerLanguage.BorkBorkBork: "Mesmer Roone-a ooff Soopereeur Inspuraeshun Maegeec",
    }

class UpgradeMinorRuneMesmer(Upgrade):
    id = ItemUpgrade.UpgradeMinorRuneMesmer
    mod_type = ItemUpgradeType.UpgradeRune

class UpgradeMajorRuneMesmer(Upgrade):
    id = ItemUpgrade.UpgradeMajorRuneMesmer
    mod_type = ItemUpgradeType.UpgradeRune

class UpgradeSuperiorRuneMesmer(Upgrade):
    id = ItemUpgrade.UpgradeSuperiorRuneMesmer
    mod_type = ItemUpgradeType.UpgradeRune

class AppliesToMinorRuneMesmer(Upgrade):
    id = ItemUpgrade.AppliesToMinorRuneMesmer
    mod_type = ItemUpgradeType.AppliesToRune

class AppliesToMajorRuneMesmer(Upgrade):
    id = ItemUpgrade.AppliesToMajorRuneMesmer
    mod_type = ItemUpgradeType.AppliesToRune

class AppliesToSuperiorRuneMesmer(Upgrade):
    id = ItemUpgrade.AppliesToSuperiorRuneMesmer
    mod_type = ItemUpgradeType.AppliesToRune

#endregion Mesmer

#region Elementalist

class HydromancerInsignia(Insignia):
    id = ItemUpgrade.HydromancerInsignia
    names = {
        ServerLanguage.English: "Hydromancer Insignia [Elementalist]",
        ServerLanguage.Korean: "물의술사의 휘장 [엘리멘탈리스트]",
        ServerLanguage.French: "Insigne [Elémentaliste] d'hydromancie",
        ServerLanguage.German: "Hydromanten- [Elementarmagier]-Befähigung",
        ServerLanguage.Italian: "Insegne [Elementalista] da Idromante",
        ServerLanguage.Spanish: "Insignia [Elementalista] de hidromante",
        ServerLanguage.TraditionalChinese: "水法師 徽記 [元素使]",
        ServerLanguage.Japanese: "ハイドロマンサー 記章 [エレメンタリスト]",
        ServerLanguage.Polish: "[Elementalista] Symbol Hydromanty",
        ServerLanguage.Russian: "Hydromancer Insignia [Elementalist]",
        ServerLanguage.BorkBorkBork: "Hydrumuncer Inseegneea [Ilementaeleest]",
    }
    
    descriptions = {
        ServerLanguage.English: f"Armor +10 (vs. elemental damage)\nArmor +10 (vs. Cold damage)"
    }

class GeomancerInsignia(Insignia):
    id = ItemUpgrade.GeomancerInsignia
    names = {
        ServerLanguage.English: "Geomancer Insignia [Elementalist]",
        ServerLanguage.Korean: "대지술사의 휘장 [엘리멘탈리스트]",
        ServerLanguage.French: "Insigne [Elémentaliste] de géomancie",
        ServerLanguage.German: "Geomanten- [Elementarmagier]-Befähigung",
        ServerLanguage.Italian: "Insegne [Elementalista] da Geomante",
        ServerLanguage.Spanish: "Insignia [Elementalista] de geomante",
        ServerLanguage.TraditionalChinese: "地法師 徽記 [元素使]",
        ServerLanguage.Japanese: "ジオマンサー 記章 [エレメンタリスト]",
        ServerLanguage.Polish: "[Elementalista] Symbol Geomanty",
        ServerLanguage.Russian: "Geomancer Insignia [Elementalist]",
        ServerLanguage.BorkBorkBork: "Geumuncer Inseegneea [Ilementaeleest]",
    }
    
    descriptions = {
        ServerLanguage.English: f"Armor +10 (vs. elemental damage)\nArmor +10 (vs. Earth damage)"
    }

class PyromancerInsignia(Insignia):
    id = ItemUpgrade.PyromancerInsignia
    names = {
        ServerLanguage.English: "Pyromancer Insignia [Elementalist]",
        ServerLanguage.Korean: "화염술사의 휘장 [엘리멘탈리스트]",
        ServerLanguage.French: "Insigne [Elémentaliste] de pyromancie",
        ServerLanguage.German: "Pyromanten- [Elementarmagier]-Befähigung",
        ServerLanguage.Italian: "Insegne [Elementalista] da Piromante",
        ServerLanguage.Spanish: "Insignia [Elementalista] de piromante",
        ServerLanguage.TraditionalChinese: "火法師 徽記 [元素使]",
        ServerLanguage.Japanese: "パイロマンサー 記章 [エレメンタリスト]",
        ServerLanguage.Polish: "[Elementalista] Symbol Piromanty",
        ServerLanguage.Russian: "Pyromancer Insignia [Elementalist]",
        ServerLanguage.BorkBorkBork: "Pyrumuncer Inseegneea [Ilementaeleest]",
    }
    
    descriptions = {
        ServerLanguage.English: f"Armor +10 (vs. elemental damage)\nArmor +10 (vs. Fire damage)"
    }

class AeromancerInsignia(Insignia):
    id = ItemUpgrade.AeromancerInsignia
    names = {
        ServerLanguage.English: "Aeromancer Insignia [Elementalist]",
        ServerLanguage.Korean: "바람술사의 휘장 [엘리멘탈리스트]",
        ServerLanguage.French: "Insigne [Elémentaliste] d'aéromancie",
        ServerLanguage.German: "Aeromanten- [Elementarmagier]-Befähigung",
        ServerLanguage.Italian: "Insegne [Elementalista] da Aeromante",
        ServerLanguage.Spanish: "Insignia [Elementalista] de aeromante",
        ServerLanguage.TraditionalChinese: "風法師 徽記 [元素使]",
        ServerLanguage.Japanese: "エアロマンサー 記章 [エレメンタリスト]",
        ServerLanguage.Polish: "[Elementalista] Symbol Aeromanty",
        ServerLanguage.Russian: "Aeromancer Insignia [Elementalist]",
        ServerLanguage.BorkBorkBork: "Aeerumuncer Inseegneea [Ilementaeleest]",
    }
    
    descriptions = {
        ServerLanguage.English: f"Armor +10 (vs. elemental damage)\nArmor +10 (vs. Lightning damage)"
    }

class PrismaticInsignia(Insignia):
    id = ItemUpgrade.PrismaticInsignia
    names = {
        ServerLanguage.English: "Prismatic Insignia [Elementalist]",
        ServerLanguage.Korean: "무지갯빛 휘장 [엘리멘탈리스트]",
        ServerLanguage.French: "Insigne [Elémentaliste] prismatique",
        ServerLanguage.German: "Spektral- [Elementarmagier]-Befähigung",
        ServerLanguage.Italian: "Insegne [Elementalista] a Prisma",
        ServerLanguage.Spanish: "Insignia [Elementalista] de prismático",
        ServerLanguage.TraditionalChinese: "稜鏡 徽記 [元素使]",
        ServerLanguage.Japanese: "プリズマティック 記章 [エレメンタリスト]",
        ServerLanguage.Polish: "[Elementalista] Symbol Pryzmatu",
        ServerLanguage.Russian: "Prismatic Insignia [Elementalist]",
        ServerLanguage.BorkBorkBork: "Preesmaeteec Inseegneea [Ilementaeleest]",
    }
    
    descriptions = {
        ServerLanguage.English: f"Armor +5 (requires 9 Air Magic)\nArmor +5 (requires 9 Earth Magic)\nArmor +5 (requires 9 Fire Magic)\nArmor +5 (requires 9 Water Magic)"

    }

class ElementalistRuneOfMinorEnergyStorage(AttributeRune):
    id = ItemUpgrade.ElementalistRuneOfMinorEnergyStorage
    rarity = Rarity.Blue

    names = {
        ServerLanguage.English: "Elementalist Rune of Minor Energy Storage",
        ServerLanguage.Korean: "엘리멘탈리스트 룬(하급 에너지 축적)",
        ServerLanguage.French: "Rune d'Elémentaliste (Conservation d'énergie : bonus mineur)",
        ServerLanguage.German: "Elementarmagier-Rune d. kleineren Energiespeicherung",
        ServerLanguage.Italian: "Runa dell'Elementalista Riserva di Energia di grado minore",
        ServerLanguage.Spanish: "Runa de Elementalista (Almacenamiento energía de grado menor)",
        ServerLanguage.TraditionalChinese: "初級 能量儲存 元素使符文",
        ServerLanguage.Japanese: "エレメンタリスト ルーン (マイナー ストレージ)",
        ServerLanguage.Polish: "Runa Elementalisty (Zapas Energii niższego poziomu)",
        ServerLanguage.Russian: "Elementalist Rune of Minor Energy Storage",
        ServerLanguage.BorkBorkBork: "Ilementaeleest Roone-a ooff Meenur Inergy Sturaege-a",
    }

class ElementalistRuneOfMinorFireMagic(AttributeRune):
    id = ItemUpgrade.ElementalistRuneOfMinorFireMagic
    rarity = Rarity.Blue

    names = {
        ServerLanguage.English: "Elementalist Rune of Minor Fire Magic",
        ServerLanguage.Korean: "엘리멘탈리스트 룬(하급 불)",
        ServerLanguage.French: "Rune d'Elémentaliste (Magie du feu : bonus mineur)",
        ServerLanguage.German: "Elementarmagier-Rune d. kleineren Feuermagie",
        ServerLanguage.Italian: "Runa dell'Elementalista Magia del Fuoco di grado minore",
        ServerLanguage.Spanish: "Runa de Elementalista (Magia de fuego de grado menor)",
        ServerLanguage.TraditionalChinese: "初級 火系魔法 元素使符文",
        ServerLanguage.Japanese: "エレメンタリスト ルーン (マイナー ファイア)",
        ServerLanguage.Polish: "Runa Elementalisty (Magia Ognia niższego poziomu)",
        ServerLanguage.Russian: "Elementalist Rune of Minor Fire Magic",
        ServerLanguage.BorkBorkBork: "Ilementaeleest Roone-a ooff Meenur Fure-a Maegeec",
    }

class ElementalistRuneOfMinorAirMagic(AttributeRune):
    id = ItemUpgrade.ElementalistRuneOfMinorAirMagic
    rarity = Rarity.Blue

    names = {
        ServerLanguage.English: "Elementalist Rune of Minor Air Magic",
        ServerLanguage.Korean: "엘리멘탈리스트 룬(하급 바람)",
        ServerLanguage.French: "Rune d'Elémentaliste (Magie de l'air : bonus mineur)",
        ServerLanguage.German: "Elementarmagier-Rune d. kleineren Luftmagie",
        ServerLanguage.Italian: "Runa dell'Elementalista Magia dell'Aria di grado minore",
        ServerLanguage.Spanish: "Runa de Elementalista (Magia de aire de grado menor)",
        ServerLanguage.TraditionalChinese: "初級 風系魔法 元素使符文",
        ServerLanguage.Japanese: "エレメンタリスト ルーン (マイナー エアー)",
        ServerLanguage.Polish: "Runa Elementalisty (Magia Powietrza niższego poziomu)",
        ServerLanguage.Russian: "Elementalist Rune of Minor Air Magic",
        ServerLanguage.BorkBorkBork: "Ilementaeleest Roone-a ooff Meenur Aeur Maegeec",
    }

class ElementalistRuneOfMinorEarthMagic(AttributeRune):
    id = ItemUpgrade.ElementalistRuneOfMinorEarthMagic
    rarity = Rarity.Blue

    names = {
        ServerLanguage.English: "Elementalist Rune of Minor Earth Magic",
        ServerLanguage.Korean: "엘리멘탈리스트 룬(하급 대지)",
        ServerLanguage.French: "Rune d'Elémentaliste (Magie de la terre : bonus mineur)",
        ServerLanguage.German: "Elementarmagier-Rune d. kleineren Erdmagie",
        ServerLanguage.Italian: "Runa dell'Elementalista Magia della Terra di grado minore",
        ServerLanguage.Spanish: "Runa de Elementalista (Magia de tierra de grado menor)",
        ServerLanguage.TraditionalChinese: "初級 土系魔法 元素使符文",
        ServerLanguage.Japanese: "エレメンタリスト ルーン (マイナー アース)",
        ServerLanguage.Polish: "Runa Elementalisty (Magia Ziemi niższego poziomu)",
        ServerLanguage.Russian: "Elementalist Rune of Minor Earth Magic",
        ServerLanguage.BorkBorkBork: "Ilementaeleest Roone-a ooff Meenur Iaert Maegeec",
    }

class ElementalistRuneOfMinorWaterMagic(AttributeRune):
    id = ItemUpgrade.ElementalistRuneOfMinorWaterMagic
    rarity = Rarity.Blue

    names = {
        ServerLanguage.English: "Elementalist Rune of Minor Water Magic",
        ServerLanguage.Korean: "엘리멘탈리스트 룬(하급 물)",
        ServerLanguage.French: "Rune d'Elémentaliste (Magie de l'eau : bonus mineur)",
        ServerLanguage.German: "Elementarmagier-Rune d. kleineren Wassermagie",
        ServerLanguage.Italian: "Runa dell'Elementalista Magia dell'Acqua di grado minore",
        ServerLanguage.Spanish: "Runa de Elementalista (Magia de agua de grado menor)",
        ServerLanguage.TraditionalChinese: "初級 水系魔法 元素使符文",
        ServerLanguage.Japanese: "エレメンタリスト ルーン (マイナー ウォーター)",
        ServerLanguage.Polish: "Runa Elementalisty (Magia Wody niższego poziomu)",
        ServerLanguage.Russian: "Elementalist Rune of Minor Water Magic",
        ServerLanguage.BorkBorkBork: "Ilementaeleest Roone-a ooff Meenur Vaeter Maegeec",
    }

class ElementalistRuneOfMajorEnergyStorage(AttributeRune):
    id = ItemUpgrade.ElementalistRuneOfMajorEnergyStorage
    rarity = Rarity.Purple

    property_identifiers = [
        ModifierIdentifier.HealthMinus
    ]

    names = {
        ServerLanguage.English: "Elementalist Rune of Major Energy Storage",
        ServerLanguage.Korean: "엘리멘탈리스트 룬(상급 에너지 축적)",
        ServerLanguage.French: "Rune d'Elémentaliste (Conservation d'énergie : bonus majeur)",
        ServerLanguage.German: "Elementarmagier-Rune d. hohen Energiespeicherung",
        ServerLanguage.Italian: "Runa dell'Elementalista Riserva di Energia di grado maggiore",
        ServerLanguage.Spanish: "Runa de Elementalista (Almacenamiento energía de grado mayor)",
        ServerLanguage.TraditionalChinese: "中級 能量儲存 元素使符文",
        ServerLanguage.Japanese: "エレメンタリスト ルーン (メジャー ストレージ)",
        ServerLanguage.Polish: "Runa Elementalisty (Zapas Energii wyższego poziomu)",
        ServerLanguage.Russian: "Elementalist Rune of Major Energy Storage",
        ServerLanguage.BorkBorkBork: "Ilementaeleest Roone-a ooff Maejur Inergy Sturaege-a",
    }

class ElementalistRuneOfMajorFireMagic(AttributeRune):
    id = ItemUpgrade.ElementalistRuneOfMajorFireMagic
    rarity = Rarity.Purple

    property_identifiers = [
        ModifierIdentifier.HealthMinus
    ]

    names = {
        ServerLanguage.English: "Elementalist Rune of Major Fire Magic",
        ServerLanguage.Korean: "엘리멘탈리스트 룬(상급 불)",
        ServerLanguage.French: "Rune d'Elémentaliste (Magie du feu : bonus majeur)",
        ServerLanguage.German: "Elementarmagier-Rune d. hohen Feuermagie",
        ServerLanguage.Italian: "Runa dell'Elementalista Magia del Fuoco di grado maggiore",
        ServerLanguage.Spanish: "Runa de Elementalista (Magia de fuego de grado mayor)",
        ServerLanguage.TraditionalChinese: "中級 火系魔法 元素使符文",
        ServerLanguage.Japanese: "エレメンタリスト ルーン (メジャー ファイア)",
        ServerLanguage.Polish: "Runa Elementalisty (Magia Ognia wyższego poziomu)",
        ServerLanguage.Russian: "Elementalist Rune of Major Fire Magic",
        ServerLanguage.BorkBorkBork: "Ilementaeleest Roone-a ooff Maejur Fure-a Maegeec",
    }

class ElementalistRuneOfMajorAirMagic(AttributeRune):
    id = ItemUpgrade.ElementalistRuneOfMajorAirMagic
    rarity = Rarity.Purple

    property_identifiers = [
        ModifierIdentifier.HealthMinus
    ]

    names = {
        ServerLanguage.English: "Elementalist Rune of Major Air Magic",
        ServerLanguage.Korean: "엘리멘탈리스트 룬(상급 바람)",
        ServerLanguage.French: "Rune d'Elémentaliste (Magie de l'air : bonus majeur)",
        ServerLanguage.German: "Elementarmagier-Rune d. hohen Luftmagie",
        ServerLanguage.Italian: "Runa dell'Elementalista Magia dell'Aria di grado maggiore",
        ServerLanguage.Spanish: "Runa de Elementalista (Magia de aire de grado mayor)",
        ServerLanguage.TraditionalChinese: "中級 風系魔法 元素使符文",
        ServerLanguage.Japanese: "エレメンタリスト ルーン (メジャー エアー)",
        ServerLanguage.Polish: "Runa Elementalisty (Magia Powietrza wyższego poziomu)",
        ServerLanguage.Russian: "Elementalist Rune of Major Air Magic",
        ServerLanguage.BorkBorkBork: "Ilementaeleest Roone-a ooff Maejur Aeur Maegeec",
    }

class ElementalistRuneOfMajorEarthMagic(AttributeRune):
    id = ItemUpgrade.ElementalistRuneOfMajorEarthMagic
    rarity = Rarity.Purple

    property_identifiers = [
        ModifierIdentifier.HealthMinus
    ]

    names = {
        ServerLanguage.English: "Elementalist Rune of Major Earth Magic",
        ServerLanguage.Korean: "엘리멘탈리스트 룬(상급 대지)",
        ServerLanguage.French: "Rune d'Elémentaliste (Magie de la terre : bonus majeur)",
        ServerLanguage.German: "Elementarmagier-Rune d. hohen Erdmagie",
        ServerLanguage.Italian: "Runa dell'Elementalista Magia della Terra di grado maggiore",
        ServerLanguage.Spanish: "Runa de Elementalista (Magia de tierra de grado mayor)",
        ServerLanguage.TraditionalChinese: "中級 土系魔法 元素使符文",
        ServerLanguage.Japanese: "エレメンタリスト ルーン (メジャー アース)",
        ServerLanguage.Polish: "Runa Elementalisty (Magia Ziemi wyższego poziomu)",
        ServerLanguage.Russian: "Elementalist Rune of Major Earth Magic",
        ServerLanguage.BorkBorkBork: "Ilementaeleest Roone-a ooff Maejur Iaert Maegeec",
    }

class ElementalistRuneOfMajorWaterMagic(AttributeRune):
    id = ItemUpgrade.ElementalistRuneOfMajorWaterMagic
    rarity = Rarity.Purple

    property_identifiers = [
        ModifierIdentifier.HealthMinus
    ]

    names = {
        ServerLanguage.English: "Elementalist Rune of Major Water Magic",
        ServerLanguage.Korean: "엘리멘탈리스트 룬(상급 물)",
        ServerLanguage.French: "Rune d'Elémentaliste (Magie de l'eau : bonus majeur)",
        ServerLanguage.German: "Elementarmagier-Rune d. hohen Wassermagie",
        ServerLanguage.Italian: "Runa dell'Elementalista Magia dell'Acqua di grado maggiore",
        ServerLanguage.Spanish: "Runa de Elementalista (Magia de agua de grado mayor)",
        ServerLanguage.TraditionalChinese: "中級 水系魔法 元素使符文",
        ServerLanguage.Japanese: "エレメンタリスト ルーン (メジャー ウォーター)",
        ServerLanguage.Polish: "Runa Elementalisty (Magia Wody wyższego poziomu)",
        ServerLanguage.Russian: "Elementalist Rune of Major Water Magic",
        ServerLanguage.BorkBorkBork: "Ilementaeleest Roone-a ooff Maejur Vaeter Maegeec",
    }

class ElementalistRuneOfSuperiorEnergyStorage(AttributeRune):
    id = ItemUpgrade.ElementalistRuneOfSuperiorEnergyStorage
    rarity = Rarity.Gold

    property_identifiers = [
        ModifierIdentifier.HealthMinus
    ]

    names = {
        ServerLanguage.English: "Elementalist Rune of Superior Energy Storage",
        ServerLanguage.Korean: "엘리멘탈리스트 룬(고급 에너지 축적)",
        ServerLanguage.French: "Rune d'Elémentaliste (Conservation d'énergie : bonus supérieur)",
        ServerLanguage.German: "Elementarmagier-Rune d. überlegenen Energiespeicherung",
        ServerLanguage.Italian: "Runa dell'Elementalista Riserva di Energia di grado supremo",
        ServerLanguage.Spanish: "Runa de Elementalista (Almacenamiento energía de grado excepcional)",
        ServerLanguage.TraditionalChinese: "高級 能量儲存 元素使符文",
        ServerLanguage.Japanese: "エレメンタリスト ルーン (スーペリア ストレージ)",
        ServerLanguage.Polish: "Runa Elementalisty (Zapas Energii najwyższego poziomu)",
        ServerLanguage.Russian: "Elementalist Rune of Superior Energy Storage",
        ServerLanguage.BorkBorkBork: "Ilementaeleest Roone-a ooff Soopereeur Inergy Sturaege-a",
    }

class ElementalistRuneOfSuperiorFireMagic(AttributeRune):
    id = ItemUpgrade.ElementalistRuneOfSuperiorFireMagic
    rarity = Rarity.Gold

    property_identifiers = [
        ModifierIdentifier.HealthMinus
    ]

    names = {
        ServerLanguage.English: "Elementalist Rune of Superior Fire Magic",
        ServerLanguage.Korean: "엘리멘탈리스트 룬(고급 불)",
        ServerLanguage.French: "Rune d'Elémentaliste (Magie du feu : bonus supérieur)",
        ServerLanguage.German: "Elementarmagier-Rune d. überlegenen Feuermagie",
        ServerLanguage.Italian: "Runa dell'Elementalista Magia del Fuoco di grado supremo",
        ServerLanguage.Spanish: "Runa de Elementalista (Magia de fuego de grado excepcional)",
        ServerLanguage.TraditionalChinese: "高級 火系魔法 元素使符文",
        ServerLanguage.Japanese: "エレメンタリスト ルーン (スーペリア ファイア)",
        ServerLanguage.Polish: "Runa Elementalisty (Magia Ognia najwyższego poziomu)",
        ServerLanguage.Russian: "Elementalist Rune of Superior Fire Magic",
        ServerLanguage.BorkBorkBork: "Ilementaeleest Roone-a ooff Soopereeur Fure-a Maegeec",
    }

class ElementalistRuneOfSuperiorAirMagic(AttributeRune):
    id = ItemUpgrade.ElementalistRuneOfSuperiorAirMagic
    rarity = Rarity.Gold

    property_identifiers = [
        ModifierIdentifier.HealthMinus
    ]

    names = {
        ServerLanguage.English: "Elementalist Rune of Superior Air Magic",
        ServerLanguage.Korean: "엘리멘탈리스트 룬(고급 바람)",
        ServerLanguage.French: "Rune d'Elémentaliste (Magie de l'air : bonus supérieur)",
        ServerLanguage.German: "Elementarmagier-Rune d. überlegenen Luftmagie",
        ServerLanguage.Italian: "Runa dell'Elementalista Magia dell'Aria di grado supremo",
        ServerLanguage.Spanish: "Runa de Elementalista (Magia de aire de grado excepcional)",
        ServerLanguage.TraditionalChinese: "高級 風系魔法 元素使符文",
        ServerLanguage.Japanese: "エレメンタリスト ルーン (スーペリア エアー)",
        ServerLanguage.Polish: "Runa Elementalisty (Magia Powietrza najwyższego poziomu)",
        ServerLanguage.Russian: "Elementalist Rune of Superior Air Magic",
        ServerLanguage.BorkBorkBork: "Ilementaeleest Roone-a ooff Soopereeur Aeur Maegeec",
    }

class ElementalistRuneOfSuperiorEarthMagic(AttributeRune):
    id = ItemUpgrade.ElementalistRuneOfSuperiorEarthMagic
    rarity = Rarity.Gold

    property_identifiers = [
        ModifierIdentifier.HealthMinus
    ]

    names = {
        ServerLanguage.English: "Elementalist Rune of Superior Earth Magic",
        ServerLanguage.Korean: "엘리멘탈리스트 룬(고급 대지)",
        ServerLanguage.French: "Rune d'Elémentaliste (Magie de la terre : bonus supérieur)",
        ServerLanguage.German: "Elementarmagier-Rune d. überlegenen Erdmagie",
        ServerLanguage.Italian: "Runa dell'Elementalista Magia della Terra di grado supremo",
        ServerLanguage.Spanish: "Runa de Elementalista (Magia de tierra de grado excepcional)",
        ServerLanguage.TraditionalChinese: "高級 土系魔法 元素使符文",
        ServerLanguage.Japanese: "エレメンタリスト ルーン (スーペリア アース)",
        ServerLanguage.Polish: "Runa Elementalisty (Magia Ziemi najwyższego poziomu)",
        ServerLanguage.Russian: "Elementalist Rune of Superior Earth Magic",
        ServerLanguage.BorkBorkBork: "Ilementaeleest Roone-a ooff Soopereeur Iaert Maegeec",
    }

class ElementalistRuneOfSuperiorWaterMagic(AttributeRune):
    id = ItemUpgrade.ElementalistRuneOfSuperiorWaterMagic
    rarity = Rarity.Gold

    property_identifiers = [
        ModifierIdentifier.HealthMinus
    ]

    names = {
        ServerLanguage.English: "Elementalist Rune of Superior Water Magic",
        ServerLanguage.Korean: "엘리멘탈리스트 룬(고급 물)",
        ServerLanguage.French: "Rune d'Elémentaliste (Magie de l'eau : bonus supérieur)",
        ServerLanguage.German: "Elementarmagier-Rune d. überlegenen Wassermagie",
        ServerLanguage.Italian: "Runa dell'Elementalista Magia dell'Acqua di grado supremo",
        ServerLanguage.Spanish: "Runa de Elementalista (Magia de agua de grado excepcional)",
        ServerLanguage.TraditionalChinese: "高級 水系魔法 元素使符文",
        ServerLanguage.Japanese: "エレメンタリスト ルーン (スーペリア ウォーター)",
        ServerLanguage.Polish: "Runa Elementalisty (Magia Wody najwyższego poziomu)",
        ServerLanguage.Russian: "Elementalist Rune of Superior Water Magic",
        ServerLanguage.BorkBorkBork: "Ilementaeleest Roone-a ooff Soopereeur Vaeter Maegeec",
    }

class UpgradeMinorRuneElementalist(Upgrade):
    id = ItemUpgrade.UpgradeMinorRuneElementalist
    mod_type = ItemUpgradeType.UpgradeRune

class UpgradeMajorRuneElementalist(Upgrade):
    id = ItemUpgrade.UpgradeMajorRuneElementalist
    mod_type = ItemUpgradeType.UpgradeRune

class UpgradeSuperiorRuneElementalist(Upgrade):
    id = ItemUpgrade.UpgradeSuperiorRuneElementalist
    mod_type = ItemUpgradeType.UpgradeRune

class AppliesToMinorRuneElementalist(Upgrade):
    id = ItemUpgrade.AppliesToMinorRuneElementalist
    mod_type = ItemUpgradeType.AppliesToRune

class AppliesToMajorRuneElementalist(Upgrade):
    id = ItemUpgrade.AppliesToMajorRuneElementalist
    mod_type = ItemUpgradeType.AppliesToRune

class AppliesToSuperiorRuneElementalist(Upgrade):
    id = ItemUpgrade.AppliesToSuperiorRuneElementalist
    mod_type = ItemUpgradeType.AppliesToRune

#endregion Elementalist

#region Assassin

class VanguardsInsignia(Insignia):
    id = ItemUpgrade.VanguardsInsignia
    names = {
        ServerLanguage.English: "Vanguard's Insignia [Assassin]",
        ServerLanguage.Korean: "선봉대의 휘장 [어새신]",
        ServerLanguage.French: "Insigne [Assassin] de l'avant-garde",
        ServerLanguage.German: "Hauptmann- [Assassinen]-Befähigung",
        ServerLanguage.Italian: "Insegne [Assassino] da Avanguardia",
        ServerLanguage.Spanish: "Insignia [Asesino] de avanzado",
        ServerLanguage.TraditionalChinese: "前鋒 徽記 [暗殺者]",
        ServerLanguage.Japanese: "ヴァンガード 記章 [アサシン]",
        ServerLanguage.Polish: "[Zabójca] Symbol Awangardy",
        ServerLanguage.Russian: "Vanguard's Insignia [Assassin]",
        ServerLanguage.BorkBorkBork: "Fungooaerd's Inseegneea [Aessaesseen]",
    }
    
    descriptions = {
        ServerLanguage.English: f"Armor +10 (vs. physical damage)\nArmor +10 (vs. Blunt damage)"
    }

class InfiltratorsInsignia(Insignia):
    id = ItemUpgrade.InfiltratorsInsignia
    names = {
        ServerLanguage.English: "Infiltrator's Insignia [Assassin]",
        ServerLanguage.Korean: "침입자의 휘장 [어새신]",
        ServerLanguage.French: "Insigne [Assassin] de l'infiltré",
        ServerLanguage.German: "Eindringlings- [Assassinen]-Befähigung",
        ServerLanguage.Italian: "Insegne [Assassino] da Spia",
        ServerLanguage.Spanish: "Insignia [Asesino] de infiltrado",
        ServerLanguage.TraditionalChinese: "滲透者 徽記 [暗殺者]",
        ServerLanguage.Japanese: "インフィルトレイター 記章 [アサシン]",
        ServerLanguage.Polish: "[Zabójca] Symbol Infiltratora",
        ServerLanguage.Russian: "Infiltrator's Insignia [Assassin]",
        ServerLanguage.BorkBorkBork: "Inffeeltraetur's Inseegneea [Aessaesseen]",
    }
    
    descriptions = {
        ServerLanguage.English: f"Armor +10 (vs. physical damage)\nArmor +10 (vs. Piercing damage)"
    }

class SaboteursInsignia(Insignia):
    id = ItemUpgrade.SaboteursInsignia
    names = {
        ServerLanguage.English: "Saboteur's Insignia [Assassin]",
        ServerLanguage.Korean: "파괴자의 휘장 [어새신]",
        ServerLanguage.French: "Insigne [Assassin] de saboteur",
        ServerLanguage.German: "Saboteur- [Assassinen]-Befähigung",
        ServerLanguage.Italian: "Insegne [Assassino] da Sabotatore",
        ServerLanguage.Spanish: "Insignia [Asesino] de saboteador",
        ServerLanguage.TraditionalChinese: "破壞者 徽記 [暗殺者]",
        ServerLanguage.Japanese: "サボター 記章 [アサシン]",
        ServerLanguage.Polish: "[Zabójca] Symbol Sabotażysty",
        ServerLanguage.Russian: "Saboteur's Insignia [Assassin]",
        ServerLanguage.BorkBorkBork: "Saebuteoor's Inseegneea [Aessaesseen]",
    }
    
    descriptions = {
        ServerLanguage.English: f"Armor +10 (vs. physical damage)\nArmor +10 (vs. Slashing damage)"
    }

class NightstalkersInsignia(Insignia):
    id = ItemUpgrade.NightstalkersInsignia
    names = {
        ServerLanguage.English: "Nightstalker's Insignia [Assassin]",
        ServerLanguage.Korean: "밤추종자의 휘장 [어새신]",
        ServerLanguage.French: "Insigne [Assassin] de traqueur nocturne",
        ServerLanguage.German: "Nachtpirscher- [Assassinen]-Befähigung",
        ServerLanguage.Italian: "Insegne [Assassino] da Inseguitore Notturno",
        ServerLanguage.Spanish: "Insignia [Asesino] de acechador nocturno",
        ServerLanguage.TraditionalChinese: "夜行者 徽記 [暗殺者]",
        ServerLanguage.Japanese: "ナイトストーカー 記章 [アサシン]",
        ServerLanguage.Polish: "[Zabójca] Symbol Nocnego Tropiciela",
        ServerLanguage.Russian: "Nightstalker's Insignia [Assassin]",
        ServerLanguage.BorkBorkBork: "Neeghtstaelker's Inseegneea [Aessaesseen]",
    }
    
    descriptions = {
        ServerLanguage.English: f"Armor +15 (while attacking)"
    }

class AssassinRuneOfMinorCriticalStrikes(AttributeRune):
    id = ItemUpgrade.AssassinRuneOfMinorCriticalStrikes
    rarity = Rarity.Blue

    names = {
        ServerLanguage.English: "Assassin Rune of Minor Critical Strikes",
        ServerLanguage.Korean: "어새신 룬(하급 치명타)",
        ServerLanguage.French: "Rune d'Assassin (Attaques critiques : bonus mineur)",
        ServerLanguage.German: "Assassinen-Rune d. kleineren Kritische Stöße",
        ServerLanguage.Italian: "Runa dell'Assassino Colpi Critici di grado minore",
        ServerLanguage.Spanish: "Runa de Asesino (Impactos críticos de grado menor)",
        ServerLanguage.TraditionalChinese: "初級 致命攻擊 暗殺者符文",
        ServerLanguage.Japanese: "アサシン ルーン (マイナー クリティカル ストライク)",
        ServerLanguage.Polish: "Runa Zabójcy (Trafienia Krytyczne niższego poziomu)",
        ServerLanguage.Russian: "Assassin Rune of Minor Critical Strikes",
        ServerLanguage.BorkBorkBork: "Aessaesseen Roone-a ooff Meenur Creeteecael Streekes",
    }

class AssassinRuneOfMinorDaggerMastery(AttributeRune):
    id = ItemUpgrade.AssassinRuneOfMinorDaggerMastery
    rarity = Rarity.Blue

    names = {
        ServerLanguage.English: "Assassin Rune of Minor Dagger Mastery",
        ServerLanguage.Korean: "어새신 룬(하급 단검술)",
        ServerLanguage.French: "Rune d'Assassin (Maîtrise de la dague : bonus mineur)",
        ServerLanguage.German: "Assassinen-Rune d. kleineren Dolchbeherrschung",
        ServerLanguage.Italian: "Runa dell'Assassino Abilità con il Pugnale di grado minore",
        ServerLanguage.Spanish: "Runa de Asesino (Dominio de la daga de grado menor)",
        ServerLanguage.TraditionalChinese: "初級 匕首精通 暗殺者符文",
        ServerLanguage.Japanese: "アサシン ルーン (マイナー ダガー マスタリー)",
        ServerLanguage.Polish: "Runa Zabójcy (Biegłość w Sztyletach niższego poziomu)",
        ServerLanguage.Russian: "Assassin Rune of Minor Dagger Mastery",
        ServerLanguage.BorkBorkBork: "Aessaesseen Roone-a ooff Meenur Daegger Maestery",
    }

class AssassinRuneOfMinorDeadlyArts(AttributeRune):
    id = ItemUpgrade.AssassinRuneOfMinorDeadlyArts
    rarity = Rarity.Blue

    names = {
        ServerLanguage.English: "Assassin Rune of Minor Deadly Arts",
        ServerLanguage.Korean: "어새신 룬(하급 죽음의 기예)",
        ServerLanguage.French: "Rune d'Assassin (Arts létaux : bonus mineur)",
        ServerLanguage.German: "Assassinen-Rune d. kleineren Tödliche Künste",
        ServerLanguage.Italian: "Runa dell'Assassino Arti Letali di grado minore",
        ServerLanguage.Spanish: "Runa de Asesino (Artes mortales de grado menor)",
        ServerLanguage.TraditionalChinese: "初級 暗殺技巧 暗殺者符文",
        ServerLanguage.Japanese: "アサシン ルーン (マイナー デッドリー アーツ)",
        ServerLanguage.Polish: "Runa Zabójcy (Sztuka Śmierci niższego poziomu)",
        ServerLanguage.Russian: "Assassin Rune of Minor Deadly Arts",
        ServerLanguage.BorkBorkBork: "Aessaesseen Roone-a ooff Meenur Deaedly Aerts",
    }

class AssassinRuneOfMinorShadowArts(AttributeRune):
    id = ItemUpgrade.AssassinRuneOfMinorShadowArts
    rarity = Rarity.Blue

    names = {
        ServerLanguage.English: "Assassin Rune of Minor Shadow Arts",
        ServerLanguage.Korean: "어새신 룬(하급 그림자 기예)",
        ServerLanguage.French: "Rune d'Assassin (Arts des ombres : bonus mineur)",
        ServerLanguage.German: "Assassinen-Rune d. kleineren Schattenkünste",
        ServerLanguage.Italian: "Runa dell'Assassino Arti dell'Ombra di grado minore",
        ServerLanguage.Spanish: "Runa de Asesino (Artes sombrías de grado menor)",
        ServerLanguage.TraditionalChinese: "初級 暗影技巧 暗殺者符文",
        ServerLanguage.Japanese: "アサシン ルーン (マイナー シャドウ アーツ)",
        ServerLanguage.Polish: "Runa Zabójcy (Sztuka Cienia niższego poziomu)",
        ServerLanguage.Russian: "Assassin Rune of Minor Shadow Arts",
        ServerLanguage.BorkBorkBork: "Aessaesseen Roone-a ooff Meenur Shaedoo Aerts",
    }

class AssassinRuneOfMajorCriticalStrikes(AttributeRune):
    id = ItemUpgrade.AssassinRuneOfMajorCriticalStrikes
    rarity = Rarity.Purple

    property_identifiers = [
        ModifierIdentifier.HealthMinus
    ]

    names = {
        ServerLanguage.English: "Assassin Rune of Major Critical Strikes",
        ServerLanguage.Korean: "어새신 룬(상급 치명타)",
        ServerLanguage.French: "Rune d'Assassin (Attaques critiques : bonus majeur)",
        ServerLanguage.German: "Assassinen-Rune d. hohen Kritische Stöße",
        ServerLanguage.Italian: "Runa dell'Assassino Colpi Critici di grado maggiore",
        ServerLanguage.Spanish: "Runa de Asesino (Impactos críticos de grado mayor)",
        ServerLanguage.TraditionalChinese: "中級 致命攻擊 暗殺者符文",
        ServerLanguage.Japanese: "アサシン ルーン (メジャー クリティカル ストライク)",
        ServerLanguage.Polish: "Runa Zabójcy (Trafienia Krytyczne wyższego poziomu)",
        ServerLanguage.Russian: "Assassin Rune of Major Critical Strikes",
        ServerLanguage.BorkBorkBork: "Aessaesseen Roone-a ooff Maejur Creeteecael Streekes",
    }

class AssassinRuneOfMajorDaggerMastery(AttributeRune):
    id = ItemUpgrade.AssassinRuneOfMajorDaggerMastery
    rarity = Rarity.Purple

    property_identifiers = [
        ModifierIdentifier.HealthMinus
    ]

    names = {
        ServerLanguage.English: "Assassin Rune of Major Dagger Mastery",
        ServerLanguage.Korean: "어새신 룬(상급 단검술)",
        ServerLanguage.French: "Rune d'Assassin (Maîtrise de la dague : bonus majeur)",
        ServerLanguage.German: "Assassinen-Rune d. hohen Dolchbeherrschung",
        ServerLanguage.Italian: "Runa dell'Assassino Abilità con il Pugnale di grado maggiore",
        ServerLanguage.Spanish: "Runa de Asesino (Dominio de la daga de grado mayor)",
        ServerLanguage.TraditionalChinese: "中級 匕首精通 暗殺者符文",
        ServerLanguage.Japanese: "アサシン ルーン (メジャー ダガー マスタリー)",
        ServerLanguage.Polish: "Runa Zabójcy (Biegłość w Sztyletach wyższego poziomu)",
        ServerLanguage.Russian: "Assassin Rune of Major Dagger Mastery",
        ServerLanguage.BorkBorkBork: "Aessaesseen Roone-a ooff Maejur Daegger Maestery",
    }

class AssassinRuneOfMajorDeadlyArts(AttributeRune):
    id = ItemUpgrade.AssassinRuneOfMajorDeadlyArts
    rarity = Rarity.Purple

    property_identifiers = [
        ModifierIdentifier.HealthMinus
    ]

    names = {
        ServerLanguage.English: "Assassin Rune of Major Deadly Arts",
        ServerLanguage.Korean: "어새신 룬(상급 죽음의 기예)",
        ServerLanguage.French: "Rune d'Assassin (Arts létaux : bonus majeur)",
        ServerLanguage.German: "Assassinen-Rune d. hohen Tödliche Künste",
        ServerLanguage.Italian: "Runa dell'Assassino Arti Letali di grado maggiore",
        ServerLanguage.Spanish: "Runa de Asesino (Artes mortales de grado mayor)",
        ServerLanguage.TraditionalChinese: "中級 暗殺技巧 暗殺者符文",
        ServerLanguage.Japanese: "アサシン ルーン (メジャー デッドリー アーツ)",
        ServerLanguage.Polish: "Runa Zabójcy (Sztuka Śmierci wyższego poziomu)",
        ServerLanguage.Russian: "Assassin Rune of Major Deadly Arts",
        ServerLanguage.BorkBorkBork: "Aessaesseen Roone-a ooff Maejur Deaedly Aerts",
    }

class AssassinRuneOfMajorShadowArts(AttributeRune):
    id = ItemUpgrade.AssassinRuneOfMajorShadowArts
    rarity = Rarity.Purple

    property_identifiers = [
        ModifierIdentifier.HealthMinus
    ]

    names = {
        ServerLanguage.English: "Assassin Rune of Major Shadow Arts",
        ServerLanguage.Korean: "어새신 룬(상급 그림자 기예)",
        ServerLanguage.French: "Rune d'Assassin (Arts des ombres : bonus majeur)",
        ServerLanguage.German: "Assassinen-Rune d. hohen Schattenkünste",
        ServerLanguage.Italian: "Runa dell'Assassino Arti dell'Ombra di grado maggiore",
        ServerLanguage.Spanish: "Runa de Asesino (Artes sombrías de grado mayor)",
        ServerLanguage.TraditionalChinese: "中級 暗影技巧 暗殺者符文",
        ServerLanguage.Japanese: "アサシン ルーン (メジャー シャドウ アーツ)",
        ServerLanguage.Polish: "Runa Zabójcy (Sztuka Cienia wyższego poziomu)",
        ServerLanguage.Russian: "Assassin Rune of Major Shadow Arts",
        ServerLanguage.BorkBorkBork: "Aessaesseen Roone-a ooff Maejur Shaedoo Aerts",
    }

class AssassinRuneOfSuperiorCriticalStrikes(AttributeRune):
    id = ItemUpgrade.AssassinRuneOfSuperiorCriticalStrikes
    rarity = Rarity.Gold

    property_identifiers = [
        ModifierIdentifier.HealthMinus
    ]

    names = {
        ServerLanguage.English: "Assassin Rune of Superior Critical Strikes",
        ServerLanguage.Korean: "어새신 룬(고급 치명타)",
        ServerLanguage.French: "Rune d'Assassin (Attaques critiques : bonus supérieur)",
        ServerLanguage.German: "Assassinen-Rune d. überlegenen Kritische Stöße",
        ServerLanguage.Italian: "Runa dell'Assassino Colpi Critici di grado supremo",
        ServerLanguage.Spanish: "Runa de Asesino (Impactos críticos de grado excepcional)",
        ServerLanguage.TraditionalChinese: "高級 致命攻擊 暗殺者符文",
        ServerLanguage.Japanese: "アサシン ルーン (スーペリア クリティカル ストライク)",
        ServerLanguage.Polish: "Runa Zabójcy (Trafienia Krytyczne najwyższego poziomu)",
        ServerLanguage.Russian: "Assassin Rune of Superior Critical Strikes",
        ServerLanguage.BorkBorkBork: "Aessaesseen Roone-a ooff Soopereeur Creeteecael Streekes",
    }

class AssassinRuneOfSuperiorDaggerMastery(AttributeRune):
    id = ItemUpgrade.AssassinRuneOfSuperiorDaggerMastery
    rarity = Rarity.Gold

    property_identifiers = [
        ModifierIdentifier.HealthMinus
    ]

    names = {
        ServerLanguage.English: "Assassin Rune of Superior Dagger Mastery",
        ServerLanguage.Korean: "어새신 룬(고급 단검술)",
        ServerLanguage.French: "Rune d'Assassin (Maîtrise de la dague : bonus supérieur)",
        ServerLanguage.German: "Assassinen-Rune d. überlegenen Dolchbeherrschung",
        ServerLanguage.Italian: "Runa dell'Assassino Abilità con il Pugnale di grado supremo",
        ServerLanguage.Spanish: "Runa de Asesino (Dominio de la daga de grado excepcional)",
        ServerLanguage.TraditionalChinese: "高級 匕首精通 暗殺者符文",
        ServerLanguage.Japanese: "アサシン ルーン (スーペリア ダガー マスタリー)",
        ServerLanguage.Polish: "Runa Zabójcy (Biegłość w Sztyletach najwyższego poziomu)",
        ServerLanguage.Russian: "Assassin Rune of Superior Dagger Mastery",
        ServerLanguage.BorkBorkBork: "Aessaesseen Roone-a ooff Soopereeur Daegger Maestery",
    }

class AssassinRuneOfSuperiorDeadlyArts(AttributeRune):
    id = ItemUpgrade.AssassinRuneOfSuperiorDeadlyArts
    rarity = Rarity.Gold

    property_identifiers = [
        ModifierIdentifier.HealthMinus
    ]

    names = {
        ServerLanguage.English: "Assassin Rune of Superior Deadly Arts",
        ServerLanguage.Korean: "어새신 룬(고급 죽음의 기예)",
        ServerLanguage.French: "Rune d'Assassin (Arts létaux : bonus supérieur)",
        ServerLanguage.German: "Assassinen-Rune d. überlegenen Tödliche Künste",
        ServerLanguage.Italian: "Runa dell'Assassino Arti Letali di grado supremo",
        ServerLanguage.Spanish: "Runa de Asesino (Artes mortales de grado excepcional)",
        ServerLanguage.TraditionalChinese: "高級 暗殺技巧 暗殺者符文",
        ServerLanguage.Japanese: "アサシン ルーン (スーペリア デッドリー アーツ)",
        ServerLanguage.Polish: "Runa Zabójcy (Sztuka Śmierci najwyższego poziomu)",
        ServerLanguage.Russian: "Assassin Rune of Superior Deadly Arts",
        ServerLanguage.BorkBorkBork: "Aessaesseen Roone-a ooff Soopereeur Deaedly Aerts",
    }

class AssassinRuneOfSuperiorShadowArts(AttributeRune):
    id = ItemUpgrade.AssassinRuneOfSuperiorShadowArts
    rarity = Rarity.Gold

    property_identifiers = [
        ModifierIdentifier.HealthMinus
    ]

    names = {
        ServerLanguage.English: "Assassin Rune of Superior Shadow Arts",
        ServerLanguage.Korean: "어새신 룬(고급 그림자 기예)",
        ServerLanguage.French: "Rune d'Assassin (Arts des ombres : bonus supérieur)",
        ServerLanguage.German: "Assassinen-Rune d. überlegenen Schattenkünste",
        ServerLanguage.Italian: "Runa dell'Assassino Arti dell'Ombra di grado supremo",
        ServerLanguage.Spanish: "Runa de Asesino (Artes sombrías de grado excepcional)",
        ServerLanguage.TraditionalChinese: "高級 暗影技巧 暗殺者符文",
        ServerLanguage.Japanese: "アサシン ルーン (スーペリア シャドウ アーツ)",
        ServerLanguage.Polish: "Runa Zabójcy (Sztuka Cienia najwyższego poziomu)",
        ServerLanguage.Russian: "Assassin Rune of Superior Shadow Arts",
        ServerLanguage.BorkBorkBork: "Aessaesseen Roone-a ooff Soopereeur Shaedoo Aerts",
    }

class UpgradeMinorRuneAssassin(Upgrade):
    id = ItemUpgrade.UpgradeMinorRuneAssassin
    mod_type = ItemUpgradeType.UpgradeRune

class UpgradeMajorRuneAssassin(Upgrade):
    id = ItemUpgrade.UpgradeMajorRuneAssassin
    mod_type = ItemUpgradeType.UpgradeRune

class UpgradeSuperiorRuneAssassin(Upgrade):
    id = ItemUpgrade.UpgradeSuperiorRuneAssassin
    mod_type = ItemUpgradeType.UpgradeRune

class AppliesToMinorRuneAssassin(Upgrade):
    id = ItemUpgrade.AppliesToMinorRuneAssassin
    mod_type = ItemUpgradeType.AppliesToRune

class AppliesToMajorRuneAssassin(Upgrade):
    id = ItemUpgrade.AppliesToMajorRuneAssassin
    mod_type = ItemUpgradeType.AppliesToRune

class AppliesToSuperiorRuneAssassin(Upgrade):
    id = ItemUpgrade.AppliesToSuperiorRuneAssassin
    mod_type = ItemUpgradeType.AppliesToRune

#endregion Assassin

#region Ritualist

class ShamansInsignia(Insignia):
    id = ItemUpgrade.ShamansInsignia
    names = {
        ServerLanguage.English: "Shaman's Insignia [Ritualist]",
        ServerLanguage.Korean: "주술사의 휘장 [리추얼리스트]",
        ServerLanguage.French: "Insigne [Ritualiste] de chaman",
        ServerLanguage.German: "Schamanen- [Ritualisten]-Befähigung",
        ServerLanguage.Italian: "Insegne [Ritualista] da Sciamano",
        ServerLanguage.Spanish: "Insignia [Ritualista] de chamán",
        ServerLanguage.TraditionalChinese: "巫醫 徽記 [祭祀者]",
        ServerLanguage.Japanese: "シャーマン 記章 [リチュアリスト]",
        ServerLanguage.Polish: "[Rytualista] Symbol Szamana",
        ServerLanguage.Russian: "Shaman's Insignia [Ritualist]",
        ServerLanguage.BorkBorkBork: "Shaemun's Inseegneea [Reetooaeleest]",
    }
    
    descriptions = {
        ServerLanguage.English: f"Armor +5 (while you control 1 or more Spirits)\nArmor +5 (while you control 2 or more Spirits)\nArmor +5 (while you control 3 or more Spirits)"

    }

class GhostForgeInsignia(Insignia):
    id = ItemUpgrade.GhostForgeInsignia
    names = {
        ServerLanguage.English: "Ghost Forge Insignia [Ritualist]",
        ServerLanguage.Korean: "유령화로의 휘장 [리추얼리스트]",
        ServerLanguage.French: "Insigne [Ritualiste] de la forge du fantôme",
        ServerLanguage.German: "Geisterschmiede- [Ritualisten]-Befähigung",
        ServerLanguage.Italian: "Insegne [Ritualista] della Fucina Spettrale",
        ServerLanguage.Spanish: "Insignia [Ritualista] de fragua fantasma",
        ServerLanguage.TraditionalChinese: "魂鎔 徽記 [祭祀者]",
        ServerLanguage.Japanese: "ゴースト フォージ 記章 [リチュアリスト]",
        ServerLanguage.Polish: "[Rytualista] Symbol Kuźni Duchów",
        ServerLanguage.Russian: "Ghost Forge Insignia [Ritualist]",
        ServerLanguage.BorkBorkBork: "Ghust Furge-a Inseegneea [Reetooaeleest]",
    }
    
    descriptions = {
        ServerLanguage.English: f"Armor +15 (while affected by a Weapon Spell)"

    }

class MysticsInsignia(Insignia):
    id = ItemUpgrade.MysticsInsignia
    names = {
        ServerLanguage.English: "Mystic's Insignia [Ritualist]",
        ServerLanguage.Korean: "신비술사의 휘장 [리추얼리스트]",
        ServerLanguage.French: "Insigne [Ritualiste] mystique",
        ServerLanguage.German: "Mystiker- [Ritualisten]-Befähigung",
        ServerLanguage.Italian: "Insegne [Ritualista] del Misticismo",
        ServerLanguage.Spanish: "Insignia [Ritualista] de místico",
        ServerLanguage.TraditionalChinese: "祕法 徽記 [祭祀者]",
        ServerLanguage.Japanese: "ミスティック 記章 [リチュアリスト]",
        ServerLanguage.Polish: "[Rytualista] Symbol Mistyka",
        ServerLanguage.Russian: "Mystic's Insignia [Ritualist]",
        ServerLanguage.BorkBorkBork: "Mysteec's Inseegneea [Reetooaeleest]",
    }
    
    descriptions = {
        ServerLanguage.English: f"Armor +15 (while activating skills)"
    }

class RitualistRuneOfMinorChannelingMagic(AttributeRune):
    id = ItemUpgrade.RitualistRuneOfMinorChannelingMagic
    rarity = Rarity.Blue

    names = {
        ServerLanguage.English: "Ritualist Rune of Minor Channeling Magic",
        ServerLanguage.Korean: "리추얼리스트 룬(하급 마력 증폭)",
        ServerLanguage.French: "Rune du Ritualiste (Magie de la canalisation : bonus mineur)",
        ServerLanguage.German: "Ritualisten-Rune d. kleineren Kanalisierungsmagie",
        ServerLanguage.Italian: "Runa del Ritualista Magia di Incanalamento di grado minore",
        ServerLanguage.Spanish: "Runa de Ritualista (Magia de canalización de grado menor)",
        ServerLanguage.TraditionalChinese: "初級 導引魔法 祭祀者符文",
        ServerLanguage.Japanese: "リチュアリスト ルーン (マイナー チャネリング)",
        ServerLanguage.Polish: "Runa Rytualisty (Magia Połączeń niższego poziomu)",
        ServerLanguage.Russian: "Ritualist Rune of Minor Channeling Magic",
        ServerLanguage.BorkBorkBork: "Reetooaeleest Roone-a ooff Meenur Chunneleeng Maegeec",
    }

class RitualistRuneOfMinorRestorationMagic(AttributeRune):
    id = ItemUpgrade.RitualistRuneOfMinorRestorationMagic
    rarity = Rarity.Blue

    names = {
        ServerLanguage.English: "Ritualist Rune of Minor Restoration Magic",
        ServerLanguage.Korean: "리추얼리스트 룬(하급 마력 회복)",
        ServerLanguage.French: "Rune du Ritualiste (Magie de restauration : bonus mineur)",
        ServerLanguage.German: "Ritualisten-Rune d. kleineren Wiederherstellungsmagie",
        ServerLanguage.Italian: "Runa del Ritualista Magia del Ripristino di grado minore",
        ServerLanguage.Spanish: "Runa de Ritualista (Magia de restauración de grado menor)",
        ServerLanguage.TraditionalChinese: "初級 復原魔法 祭祀者符文",
        ServerLanguage.Japanese: "リチュアリスト ルーン (マイナー レストレーション)",
        ServerLanguage.Polish: "Runa Rytualisty (Magia Odnowy niższego poziomu)",
        ServerLanguage.Russian: "Ritualist Rune of Minor Restoration Magic",
        ServerLanguage.BorkBorkBork: "Reetooaeleest Roone-a ooff Meenur Resturaeshun Maegeec",
    }

class RitualistRuneOfMinorCommuning(AttributeRune):
    id = ItemUpgrade.RitualistRuneOfMinorCommuning
    rarity = Rarity.Blue

    names = {
        ServerLanguage.English: "Ritualist Rune of Minor Communing",
        ServerLanguage.Korean: "리추얼리스트 룬(하급 교감)",
        ServerLanguage.French: "Rune du Ritualiste (Communion : bonus mineur)",
        ServerLanguage.German: "Ritualisten-Rune d. kleineren Zwiesprache",
        ServerLanguage.Italian: "Runa del Ritualista Raccoglimento di grado minore",
        ServerLanguage.Spanish: "Runa de Ritualista (Comunión de grado menor)",
        ServerLanguage.TraditionalChinese: "初級 神諭 祭祀者符文",
        ServerLanguage.Japanese: "リチュアリスト ルーン (マイナー コミューン)",
        ServerLanguage.Polish: "Runa Rytualisty (Zjednoczenie niższego poziomu)",
        ServerLanguage.Russian: "Ritualist Rune of Minor Communing",
        ServerLanguage.BorkBorkBork: "Reetooaeleest Roone-a ooff Meenur Cummooneeng",
    }

class RitualistRuneOfMinorSpawningPower(AttributeRune):
    id = ItemUpgrade.RitualistRuneOfMinorSpawningPower
    rarity = Rarity.Blue

    names = {
        ServerLanguage.English: "Ritualist Rune of Minor Spawning Power",
        ServerLanguage.Korean: "리추얼리스트 룬(하급 생성)",
        ServerLanguage.French: "Rune du Ritualiste (Puissance de l'Invocation : bonus mineur)",
        ServerLanguage.German: "Ritualisten-Rune d. kleineren Macht des Herbeirufens",
        ServerLanguage.Italian: "Runa del Ritualista Riti Sacrificali di grado minore",
        ServerLanguage.Spanish: "Runa de Ritualista (Engendramiento de grado menor)",
        ServerLanguage.TraditionalChinese: "初級 召喚 祭祀者符文",
        ServerLanguage.Japanese: "リチュアリスト ルーン (マイナー スポーン パワー)",
        ServerLanguage.Polish: "Runa Rytualisty (Moc Przywoływania niższego poziomu)",
        ServerLanguage.Russian: "Ritualist Rune of Minor Spawning Power",
        ServerLanguage.BorkBorkBork: "Reetooaeleest Roone-a ooff Meenur Spaevneeng Pooer",
    }

class RitualistRuneOfMajorChannelingMagic(AttributeRune):
    id = ItemUpgrade.RitualistRuneOfMajorChannelingMagic
    rarity = Rarity.Purple

    property_identifiers = [
        ModifierIdentifier.HealthMinus
    ]

    names = {
        ServerLanguage.English: "Ritualist Rune of Major Channeling Magic",
        ServerLanguage.Korean: "리추얼리스트 룬(상급 마력 증폭)",
        ServerLanguage.French: "Rune du Ritualiste (Magie de la canalisation : bonus majeur)",
        ServerLanguage.German: "Ritualisten-Rune d. hohen Kanalisierungsmagie",
        ServerLanguage.Italian: "Runa del Ritualista Magia di Incanalamento di grado maggiore",
        ServerLanguage.Spanish: "Runa de Ritualista (Magia de canalización de grado mayor)",
        ServerLanguage.TraditionalChinese: "中級 導引魔法 祭祀者符文",
        ServerLanguage.Japanese: "リチュアリスト ルーン (メジャー チャネリング)",
        ServerLanguage.Polish: "Runa Rytualisty (Magia Połączeń wyższego poziomu)",
        ServerLanguage.Russian: "Ritualist Rune of Major Channeling Magic",
        ServerLanguage.BorkBorkBork: "Reetooaeleest Roone-a ooff Maejur Chunneleeng Maegeec",
    }

class RitualistRuneOfMajorRestorationMagic(AttributeRune):
    id = ItemUpgrade.RitualistRuneOfMajorRestorationMagic
    rarity = Rarity.Purple

    property_identifiers = [
        ModifierIdentifier.HealthMinus
    ]

    names = {
        ServerLanguage.English: "Ritualist Rune of Major Restoration Magic",
        ServerLanguage.Korean: "리추얼리스트 룬(상급 마력 회복)",
        ServerLanguage.French: "Rune du Ritualiste (Magie de restauration : bonus majeur)",
        ServerLanguage.German: "Ritualisten-Rune d. hohen Wiederherstellungsmagie",
        ServerLanguage.Italian: "Runa del Ritualista Magia del Ripristino di grado maggiore",
        ServerLanguage.Spanish: "Runa de Ritualista (Magia de restauración de grado mayor)",
        ServerLanguage.TraditionalChinese: "中級 復原魔法 祭祀者符文",
        ServerLanguage.Japanese: "リチュアリスト ルーン (メジャー レストレーション)",
        ServerLanguage.Polish: "Runa Rytualisty (Magia Odnowy wyższego poziomu)",
        ServerLanguage.Russian: "Ritualist Rune of Major Restoration Magic",
        ServerLanguage.BorkBorkBork: "Reetooaeleest Roone-a ooff Maejur Resturaeshun Maegeec",
    }

class RitualistRuneOfMajorCommuning(AttributeRune):
    id = ItemUpgrade.RitualistRuneOfMajorCommuning
    rarity = Rarity.Purple

    property_identifiers = [
        ModifierIdentifier.HealthMinus
    ]

    names = {
        ServerLanguage.English: "Ritualist Rune of Major Communing",
        ServerLanguage.Korean: "리추얼리스트 룬(상급 교감)",
        ServerLanguage.French: "Rune du Ritualiste (Communion : bonus majeur)",
        ServerLanguage.German: "Ritualisten-Rune d. hohen Zwiesprache",
        ServerLanguage.Italian: "Runa del Ritualista Raccoglimento di grado maggiore",
        ServerLanguage.Spanish: "Runa de Ritualista (Comunión de grado mayor)",
        ServerLanguage.TraditionalChinese: "中級 神諭 祭祀者符文",
        ServerLanguage.Japanese: "リチュアリスト ルーン (メジャー コミューン)",
        ServerLanguage.Polish: "Runa Rytualisty (Zjednoczenie wyższego poziomu)",
        ServerLanguage.Russian: "Ritualist Rune of Major Communing",
        ServerLanguage.BorkBorkBork: "Reetooaeleest Roone-a ooff Maejur Cummooneeng",
    }

class RitualistRuneOfMajorSpawningPower(AttributeRune):
    id = ItemUpgrade.RitualistRuneOfMajorSpawningPower
    rarity = Rarity.Purple

    property_identifiers = [
        ModifierIdentifier.HealthMinus
    ]

    names = {
        ServerLanguage.English: "Ritualist Rune of Major Spawning Power",
        ServerLanguage.Korean: "리추얼리스트 룬(상급 생성)",
        ServerLanguage.French: "Rune du Ritualiste (Puissance de l'Invocation : bonus majeur)",
        ServerLanguage.German: "Ritualisten-Rune d. hohen Macht des Herbeirufens",
        ServerLanguage.Italian: "Runa del Ritualista Riti Sacrificali di grado maggiore",
        ServerLanguage.Spanish: "Runa de Ritualista (Engendramiento de grado mayor)",
        ServerLanguage.TraditionalChinese: "中級 召喚 祭祀者符文",
        ServerLanguage.Japanese: "リチュアリスト ルーン (メジャー スポーン パワー)",
        ServerLanguage.Polish: "Runa Rytualisty (Moc Przywoływania wyższego poziomu)",
        ServerLanguage.Russian: "Ritualist Rune of Major Spawning Power",
        ServerLanguage.BorkBorkBork: "Reetooaeleest Roone-a ooff Maejur Spaevneeng Pooer",
    }

class RitualistRuneOfSuperiorChannelingMagic(AttributeRune):
    id = ItemUpgrade.RitualistRuneOfSuperiorChannelingMagic
    rarity = Rarity.Gold

    property_identifiers = [
        ModifierIdentifier.HealthMinus
    ]

    names = {
        ServerLanguage.English: "Ritualist Rune of Superior Channeling Magic",
        ServerLanguage.Korean: "리추얼리스트 룬(고급 마력 증폭)",
        ServerLanguage.French: "Rune du Ritualiste (Magie de la canalisation : bonus supérieur)",
        ServerLanguage.German: "Ritualisten-Rune d. überlegenen Kanalisierungsmagie",
        ServerLanguage.Italian: "Runa del Ritualista Magia di Incanalamento di grado supremo",
        ServerLanguage.Spanish: "Runa de Ritualista (Magia de canalización de grado excepcional)",
        ServerLanguage.TraditionalChinese: "高級 導引魔法 祭祀者符文",
        ServerLanguage.Japanese: "リチュアリスト ルーン (スーペリア チャネリング)",
        ServerLanguage.Polish: "Runa Rytualisty (Magia Połączeń najwyższego poziomu)",
        ServerLanguage.Russian: "Ritualist Rune of Superior Channeling Magic",
        ServerLanguage.BorkBorkBork: "Reetooaeleest Roone-a ooff Soopereeur Chunneleeng Maegeec",
    }

class RitualistRuneOfSuperiorRestorationMagic(AttributeRune):
    id = ItemUpgrade.RitualistRuneOfSuperiorRestorationMagic
    rarity = Rarity.Gold

    property_identifiers = [
        ModifierIdentifier.HealthMinus
    ]

    names = {
        ServerLanguage.English: "Ritualist Rune of Superior Restoration Magic",
        ServerLanguage.Korean: "리추얼리스트 룬(고급 마력 회복)",
        ServerLanguage.French: "Rune du Ritualiste (Magie de restauration : bonus supérieur)",
        ServerLanguage.German: "Ritualisten-Rune d. überlegenen Wiederherstellungsmagie",
        ServerLanguage.Italian: "Runa del Ritualista Magia del Ripristino di grado supremo",
        ServerLanguage.Spanish: "Runa de Ritualista (Magia de restauración de grado excepcional)",
        ServerLanguage.TraditionalChinese: "高級 復原魔法 祭祀者符文",
        ServerLanguage.Japanese: "リチュアリスト ルーン (スーペリア レストレーション)",
        ServerLanguage.Polish: "Runa Rytualisty (Magia Odnowy najwyższego poziomu)",
        ServerLanguage.Russian: "Ritualist Rune of Superior Restoration Magic",
        ServerLanguage.BorkBorkBork: "Reetooaeleest Roone-a ooff Soopereeur Resturaeshun Maegeec",
    }

class RitualistRuneOfSuperiorCommuning(AttributeRune):
    id = ItemUpgrade.RitualistRuneOfSuperiorCommuning
    rarity = Rarity.Gold

    property_identifiers = [
        ModifierIdentifier.HealthMinus
    ]

    names = {
        ServerLanguage.English: "Ritualist Rune of Superior Communing",
        ServerLanguage.Korean: "리추얼리스트 룬(고급 교감)",
        ServerLanguage.French: "Rune du Ritualiste (Communion : bonus supérieur)",
        ServerLanguage.German: "Ritualisten-Rune d. überlegenen Zwiesprache",
        ServerLanguage.Italian: "Runa del Ritualista Raccoglimento di grado supremo",
        ServerLanguage.Spanish: "Runa de Ritualista (Comunión de grado excepcional)",
        ServerLanguage.TraditionalChinese: "高級 神諭 祭祀者符文",
        ServerLanguage.Japanese: "リチュアリスト ルーン (スーペリア コミューン)",
        ServerLanguage.Polish: "Runa Rytualisty (Zjednoczenie najwyższego poziomu)",
        ServerLanguage.Russian: "Ritualist Rune of Superior Communing",
        ServerLanguage.BorkBorkBork: "Reetooaeleest Roone-a ooff Soopereeur Cummooneeng",
    }

class RitualistRuneOfSuperiorSpawningPower(AttributeRune):
    id = ItemUpgrade.RitualistRuneOfSuperiorSpawningPower
    rarity = Rarity.Gold

    property_identifiers = [
        ModifierIdentifier.HealthMinus
    ]

    names = {
        ServerLanguage.English: "Ritualist Rune of Superior Spawning Power",
        ServerLanguage.Korean: "리추얼리스트 룬(고급 생성)",
        ServerLanguage.French: "Rune du Ritualiste (Puissance de l'Invocation : bonus supérieur)",
        ServerLanguage.German: "Ritualisten-Rune d. überlegenen Macht des Herbeirufens",
        ServerLanguage.Italian: "Runa del Ritualista Riti Sacrificali di grado supremo",
        ServerLanguage.Spanish: "Runa de Ritualista (Engendramiento de grado excepcional)",
        ServerLanguage.TraditionalChinese: "高級 召喚 祭祀者符文",
        ServerLanguage.Japanese: "リチュアリスト ルーン (スーペリア スポーン パワー)",
        ServerLanguage.Polish: "Runa Rytualisty (Moc Przywoływania najwyższego poziomu)",
        ServerLanguage.Russian: "Ritualist Rune of Superior Spawning Power",
        ServerLanguage.BorkBorkBork: "Reetooaeleest Roone-a ooff Soopereeur Spaevneeng Pooer",
    }

class UpgradeMinorRuneRitualist(Upgrade):
    id = ItemUpgrade.UpgradeMinorRuneRitualist
    mod_type = ItemUpgradeType.UpgradeRune

class UpgradeMajorRuneRitualist(Upgrade):
    id = ItemUpgrade.UpgradeMajorRuneRitualist
    mod_type = ItemUpgradeType.UpgradeRune

class UpgradeSuperiorRuneRitualist(Upgrade):
    id = ItemUpgrade.UpgradeSuperiorRuneRitualist
    mod_type = ItemUpgradeType.UpgradeRune

class AppliesToMinorRuneRitualist(Upgrade):
    id = ItemUpgrade.AppliesToMinorRuneRitualist
    mod_type = ItemUpgradeType.AppliesToRune

class AppliesToMajorRuneRitualist(Upgrade):
    id = ItemUpgrade.AppliesToMajorRuneRitualist
    mod_type = ItemUpgradeType.AppliesToRune

class AppliesToSuperiorRuneRitualist(Upgrade):
    id = ItemUpgrade.AppliesToSuperiorRuneRitualist
    mod_type = ItemUpgradeType.AppliesToRune

#endregion Ritualist

#region Dervish

class WindwalkerInsignia(Insignia):
    id = ItemUpgrade.WindwalkerInsignia
    names = {
        ServerLanguage.English: "Windwalker Insignia [Dervish]",
        ServerLanguage.Korean: "여행가의 휘장 [더비시]",
        ServerLanguage.French: "Insigne [Derviche] du Marche-vent",
        ServerLanguage.German: "Windläufer- [Derwisch]-Befähigung",
        ServerLanguage.Italian: "Insegne [Derviscio] da Camminatore nel Vento",
        ServerLanguage.Spanish: "Insignia [Derviche] de caminante del viento",
        ServerLanguage.TraditionalChinese: "風行者 徽記 [神喚使]",
        ServerLanguage.Japanese: "ウインドウォーカー 記章 [ダルウィーシュ]",
        ServerLanguage.Polish: "[Derwisz] Symbol Włóczywiatru",
        ServerLanguage.Russian: "Windwalker Insignia [Dervish]",
        ServerLanguage.BorkBorkBork: "Veendvaelker Inseegneea [Derfeesh]",
    }
    
    descriptions = {
        ServerLanguage.English: f"Armor +5 (while affected by 1 or more Enchantment Spells)\nArmor +5 (while affected by 2 or more Enchantment Spells)\nArmor +5 (while affected by 3 or more Enchantment Spells)\nArmor +5 (while affected by 4 or more Enchantment Spells)"

    }

class ForsakenInsignia(Insignia):
    id = ItemUpgrade.ForsakenInsignia
    names = {
        ServerLanguage.English: "Forsaken Insignia [Dervish]",
        ServerLanguage.Korean: "고독한 휘장 [더비시]",
        ServerLanguage.French: "Insigne [Derviche] de l'oubli",
        ServerLanguage.German: "Verlassenen- [Derwisch]-Befähigung",
        ServerLanguage.Italian: "Insegne [Derviscio] da Abbandonato",
        ServerLanguage.Spanish: "Insignia [Derviche] de abandonado",
        ServerLanguage.TraditionalChinese: "背離 徽記 [神喚使]",
        ServerLanguage.Japanese: "フォーセイク 記章 [ダルウィーシュ]",
        ServerLanguage.Polish: "[Derwisz] Symbol Zapomnienia",
        ServerLanguage.Russian: "Forsaken Insignia [Dervish]",
        ServerLanguage.BorkBorkBork: "Fursaekee Inseegneea [Derfeesh]",
    }
    
    descriptions = {
        ServerLanguage.English: f"Armor +10 (while not affected by an Enchantment Spell)"
    }

class DervishRuneOfMinorMysticism(AttributeRune):
    id = ItemUpgrade.DervishRuneOfMinorMysticism
    rarity = Rarity.Blue

    names = {
        ServerLanguage.English: "Dervish Rune of Minor Mysticism",
        ServerLanguage.Korean: "더비시 룬(하급 신비주의)",
        ServerLanguage.French: "Rune de Derviche (Mysticisme : bonus mineur)",
        ServerLanguage.German: "Derwisch-Rune d. kleineren Mystik",
        ServerLanguage.Italian: "Runa del Derviscio Misticismo di grado minore",
        ServerLanguage.Spanish: "Runa para Derviche (Misticismo de grado menor)",
        ServerLanguage.TraditionalChinese: "初級 祕法 神喚使符文",
        ServerLanguage.Japanese: "ダルウィーシュ ルーン (マイナー ミスティシズム)",
        ServerLanguage.Polish: "Runa Derwisza (Mistycyzm niższego poziomu)",
        ServerLanguage.Russian: "Dervish Rune of Minor Mysticism",
        ServerLanguage.BorkBorkBork: "Derfeesh Roone-a ooff Meenur Mysteeceesm",
    }

class DervishRuneOfMinorEarthPrayers(AttributeRune):
    id = ItemUpgrade.DervishRuneOfMinorEarthPrayers
    rarity = Rarity.Blue

    names = {
        ServerLanguage.English: "Dervish Rune of Minor Earth Prayers",
        ServerLanguage.Korean: "더비시 룬(하급 대지의 기도)",
        ServerLanguage.French: "Rune de Derviche (Prières de la Terre : bonus mineur)",
        ServerLanguage.German: "Derwisch-Rune d. kleineren Erdgebete",
        ServerLanguage.Italian: "Runa del Derviscio Preghiere della Terra di grado minore",
        ServerLanguage.Spanish: "Runa para Derviche (Plegarias de tierra de grado menor)",
        ServerLanguage.TraditionalChinese: "初級 地之祈禱 神喚使符文",
        ServerLanguage.Japanese: "ダルウィーシュ ルーン (マイナー アース プレイヤー)",
        ServerLanguage.Polish: "Runa Derwisza (Modlitwy Ziemi niższego poziomu)",
        ServerLanguage.Russian: "Dervish Rune of Minor Earth Prayers",
        ServerLanguage.BorkBorkBork: "Derfeesh Roone-a ooff Meenur Iaert Praeyers",
    }

class DervishRuneOfMinorScytheMastery(AttributeRune):
    id = ItemUpgrade.DervishRuneOfMinorScytheMastery
    rarity = Rarity.Blue

    names = {
        ServerLanguage.English: "Dervish Rune of Minor Scythe Mastery",
        ServerLanguage.Korean: "더비시 룬(하급 사이드술)",
        ServerLanguage.French: "Rune de Derviche (Maîtrise de la faux : bonus mineur)",
        ServerLanguage.German: "Derwisch-Rune d. kleineren Sensenbeherrschung",
        ServerLanguage.Italian: "Runa del Derviscio Abilità con la Falce di grado minore",
        ServerLanguage.Spanish: "Runa para Derviche (Dominio de la guadaña de grado menor)",
        ServerLanguage.TraditionalChinese: "初級 鐮刀精通 神喚使符文",
        ServerLanguage.Japanese: "ダルウィーシュ ルーン (マイナー サイズ マスタリー)",
        ServerLanguage.Polish: "Runa Derwisza (Biegłość w Kosach niższego poziomu)",
        ServerLanguage.Russian: "Dervish Rune of Minor Scythe Mastery",
        ServerLanguage.BorkBorkBork: "Derfeesh Roone-a ooff Meenur Scyzee Maestery",
    }

class DervishRuneOfMinorWindPrayers(AttributeRune):
    id = ItemUpgrade.DervishRuneOfMinorWindPrayers
    rarity = Rarity.Blue

    names = {
        ServerLanguage.English: "Dervish Rune of Minor Wind Prayers",
        ServerLanguage.Korean: "더비시 룬(하급 바람의 기도)",
        ServerLanguage.French: "Rune de Derviche (Prières du Vent : bonus mineur)",
        ServerLanguage.German: "Derwisch-Rune d. kleineren Windgebete",
        ServerLanguage.Italian: "Runa del Derviscio Preghiere del Vento di grado minore",
        ServerLanguage.Spanish: "Runa para Derviche (Plegarias de viento de grado menor)",
        ServerLanguage.TraditionalChinese: "初級 風之祈禱 神喚使符文",
        ServerLanguage.Japanese: "ダルウィーシュ ルーン (マイナー ウインド プレイヤー)",
        ServerLanguage.Polish: "Runa Derwisza (Modlitwy Wiatru niższego poziomu)",
        ServerLanguage.Russian: "Dervish Rune of Minor Wind Prayers",
        ServerLanguage.BorkBorkBork: "Derfeesh Roone-a ooff Meenur Veend Praeyers",
    }

class DervishRuneOfMajorMysticism(AttributeRune):
    id = ItemUpgrade.DervishRuneOfMajorMysticism
    rarity = Rarity.Purple

    property_identifiers = [
        ModifierIdentifier.HealthMinus
    ]

    names = {
        ServerLanguage.English: "Dervish Rune of Major Mysticism",
        ServerLanguage.Korean: "더비시 룬(상급 신비주의)",
        ServerLanguage.French: "Rune de Derviche (Mysticisme : bonus majeur)",
        ServerLanguage.German: "Derwisch-Rune d. hohen Mystik",
        ServerLanguage.Italian: "Runa del Derviscio Misticismo di grado maggiore",
        ServerLanguage.Spanish: "Runa para Derviche (Misticismo de grado mayor)",
        ServerLanguage.TraditionalChinese: "中級 祕法 神喚使符文",
        ServerLanguage.Japanese: "ダルウィーシュ ルーン (メジャー ミスティシズム)",
        ServerLanguage.Polish: "Runa Derwisza (Mistycyzm wyższego poziomu)",
        ServerLanguage.Russian: "Dervish Rune of Major Mysticism",
        ServerLanguage.BorkBorkBork: "Derfeesh Roone-a ooff Maejur Mysteeceesm",
    }

class DervishRuneOfMajorEarthPrayers(AttributeRune):
    id = ItemUpgrade.DervishRuneOfMajorEarthPrayers
    rarity = Rarity.Purple

    property_identifiers = [
        ModifierIdentifier.HealthMinus
    ]

    names = {
        ServerLanguage.English: "Dervish Rune of Major Earth Prayers",
        ServerLanguage.Korean: "더비시 룬(상급 대지의 기도)",
        ServerLanguage.French: "Rune de Derviche (Prières de la Terre : bonus majeur)",
        ServerLanguage.German: "Derwisch-Rune d. hohen Erdgebete",
        ServerLanguage.Italian: "Runa del Derviscio Preghiere della Terra di grado maggiore",
        ServerLanguage.Spanish: "Runa para Derviche (Plegarias de tierra de grado mayor)",
        ServerLanguage.TraditionalChinese: "中級 地之祈禱 神喚使符文",
        ServerLanguage.Japanese: "ダルウィーシュ ルーン (メジャー アース プレイヤー)",
        ServerLanguage.Polish: "Runa Derwisza (Modlitwy Ziemi wyższego poziomu)",
        ServerLanguage.Russian: "Dervish Rune of Major Earth Prayers",
        ServerLanguage.BorkBorkBork: "Derfeesh Roone-a ooff Maejur Iaert Praeyers",
    }

class DervishRuneOfMajorScytheMastery(AttributeRune):
    id = ItemUpgrade.DervishRuneOfMajorScytheMastery
    rarity = Rarity.Purple

    property_identifiers = [
        ModifierIdentifier.HealthMinus
    ]

    names = {
        ServerLanguage.English: "Dervish Rune of Major Scythe Mastery",
        ServerLanguage.Korean: "더비시 룬(상급 사이드술)",
        ServerLanguage.French: "Rune de Derviche (Maîtrise de la faux : bonus majeur)",
        ServerLanguage.German: "Derwisch-Rune d. hohen Sensenbeherrschung",
        ServerLanguage.Italian: "Runa del Derviscio Abilità con la Falce di grado maggiore",
        ServerLanguage.Spanish: "Runa para Derviche (Dominio de la guadaña de grado mayor)",
        ServerLanguage.TraditionalChinese: "中級 鐮刀精通 神喚使符文",
        ServerLanguage.Japanese: "ダルウィーシュ ルーン (メジャー サイズ マスタリー)",
        ServerLanguage.Polish: "Runa Derwisza (Biegłość w Kosach wyższego poziomu)",
        ServerLanguage.Russian: "Dervish Rune of Major Scythe Mastery",
        ServerLanguage.BorkBorkBork: "Derfeesh Roone-a ooff Maejur Scyzee Maestery",
    }

class DervishRuneOfMajorWindPrayers(AttributeRune):
    id = ItemUpgrade.DervishRuneOfMajorWindPrayers
    rarity = Rarity.Purple

    property_identifiers = [
        ModifierIdentifier.HealthMinus
    ]

    names = {
        ServerLanguage.English: "Dervish Rune of Major Wind Prayers",
        ServerLanguage.Korean: "더비시 룬(상급 바람의 기도)",
        ServerLanguage.French: "Rune de Derviche (Prières du Vent : bonus majeur)",
        ServerLanguage.German: "Derwisch-Rune d. hohen Windgebete",
        ServerLanguage.Italian: "Runa del Derviscio Preghiere del Vento di grado maggiore",
        ServerLanguage.Spanish: "Runa para Derviche (Plegarias de viento de grado mayor)",
        ServerLanguage.TraditionalChinese: "中級 風之祈禱 神喚使符文",
        ServerLanguage.Japanese: "ダルウィーシュ ルーン (メジャー ウインド プレイヤー)",
        ServerLanguage.Polish: "Runa Derwisza (Modlitwy Wiatru wyższego poziomu)",
        ServerLanguage.Russian: "Dervish Rune of Major Wind Prayers",
        ServerLanguage.BorkBorkBork: "Derfeesh Roone-a ooff Maejur Veend Praeyers",
    }

class DervishRuneOfSuperiorMysticism(AttributeRune):
    id = ItemUpgrade.DervishRuneOfSuperiorMysticism
    rarity = Rarity.Gold

    property_identifiers = [
        ModifierIdentifier.HealthMinus
    ]

    names = {
        ServerLanguage.English: "Dervish Rune of Superior Mysticism",
        ServerLanguage.Korean: "더비시 룬(고급 신비주의)",
        ServerLanguage.French: "Rune de Derviche (Mysticisme : bonus supérieur)",
        ServerLanguage.German: "Derwisch-Rune d. überlegenen Mystik",
        ServerLanguage.Italian: "Runa del Derviscio Misticismo di grado supremo",
        ServerLanguage.Spanish: "Runa para Derviche (Misticismo de grado excepcional)",
        ServerLanguage.TraditionalChinese: "高級 祕法 神喚使符文",
        ServerLanguage.Japanese: "ダルウィーシュ ルーン (スーペリア ミスティシズム)",
        ServerLanguage.Polish: "Runa Derwisza (Mistycyzm najwyższego poziomu)",
        ServerLanguage.Russian: "Dervish Rune of Superior Mysticism",
        ServerLanguage.BorkBorkBork: "Derfeesh Roone-a ooff Soopereeur Mysteeceesm",
    }

class DervishRuneOfSuperiorEarthPrayers(AttributeRune):
    id = ItemUpgrade.DervishRuneOfSuperiorEarthPrayers
    rarity = Rarity.Gold

    property_identifiers = [
        ModifierIdentifier.HealthMinus
    ]

    names = {
        ServerLanguage.English: "Dervish Rune of Superior Earth Prayers",
        ServerLanguage.Korean: "더비시 룬(고급 대지의 기도)",
        ServerLanguage.French: "Rune de Derviche (Prières de la Terre : bonus supérieur)",
        ServerLanguage.German: "Derwisch-Rune d. überlegenen Erdgebete",
        ServerLanguage.Italian: "Runa del Derviscio Preghiere della Terra di grado supremo",
        ServerLanguage.Spanish: "Runa para Derviche (Plegarias de tierra de grado excepcional)",
        ServerLanguage.TraditionalChinese: "高級 地之祈禱 神喚使符文",
        ServerLanguage.Japanese: "ダルウィーシュ ルーン (スーペリア アース プレイヤー)",
        ServerLanguage.Polish: "Runa Derwisza (Modlitwy Ziemi najwyższego poziomu)",
        ServerLanguage.Russian: "Dervish Rune of Superior Earth Prayers",
        ServerLanguage.BorkBorkBork: "Derfeesh Roone-a ooff Soopereeur Iaert Praeyers",
    }

class DervishRuneOfSuperiorScytheMastery(AttributeRune):
    id = ItemUpgrade.DervishRuneOfSuperiorScytheMastery
    rarity = Rarity.Gold

    property_identifiers = [
        ModifierIdentifier.HealthMinus
    ]

    names = {
        ServerLanguage.English: "Dervish Rune of Superior Scythe Mastery",
        ServerLanguage.Korean: "더비시 룬(고급 사이드술)",
        ServerLanguage.French: "Rune de Derviche (Maîtrise de la faux : bonus supérieur)",
        ServerLanguage.German: "Derwisch-Rune d. überlegenen Sensenbeherrschung",
        ServerLanguage.Italian: "Runa del Derviscio Abilità con la Falce di grado supremo",
        ServerLanguage.Spanish: "Runa para Derviche (Dominio de la guadaña de grado excepcional)",
        ServerLanguage.TraditionalChinese: "高級 鐮刀精通 神喚使符文",
        ServerLanguage.Japanese: "ダルウィーシュ ルーン (スーペリア サイズ マスタリー)",
        ServerLanguage.Polish: "Runa Derwisza (Biegłość w Kosach najwyższego poziomu)",
        ServerLanguage.Russian: "Dervish Rune of Superior Scythe Mastery",
        ServerLanguage.BorkBorkBork: "Derfeesh Roone-a ooff Soopereeur Scyzee Maestery",
    }

class DervishRuneOfSuperiorWindPrayers(AttributeRune):
    id = ItemUpgrade.DervishRuneOfSuperiorWindPrayers
    rarity = Rarity.Gold

    property_identifiers = [
        ModifierIdentifier.HealthMinus
    ]

    names = {
        ServerLanguage.English: "Dervish Rune of Superior Wind Prayers",
        ServerLanguage.Korean: "더비시 룬(고급 바람의 기도)",
        ServerLanguage.French: "Rune de Derviche (Prières du Vent : bonus supérieur)",
        ServerLanguage.German: "Derwisch-Rune d. überlegenen Windgebete",
        ServerLanguage.Italian: "Runa del Derviscio Preghiere del Vento di grado supremo",
        ServerLanguage.Spanish: "Runa para Derviche (Plegarias de viento de grado excepcional)",
        ServerLanguage.TraditionalChinese: "高級 風之祈禱 神喚使符文",
        ServerLanguage.Japanese: "ダルウィーシュ ルーン (スーペリア ウインド プレイヤー)",
        ServerLanguage.Polish: "Runa Derwisza (Modlitwy Wiatru najwyższego poziomu)",
        ServerLanguage.Russian: "Dervish Rune of Superior Wind Prayers",
        ServerLanguage.BorkBorkBork: "Derfeesh Roone-a ooff Soopereeur Veend Praeyers",
    }

class UpgradeMinorRuneDervish(Upgrade):
    id = ItemUpgrade.UpgradeMinorRuneDervish
    mod_type = ItemUpgradeType.UpgradeRune

class UpgradeMajorRuneDervish(Upgrade):
    id = ItemUpgrade.UpgradeMajorRuneDervish
    mod_type = ItemUpgradeType.UpgradeRune

class UpgradeSuperiorRuneDervish(Upgrade):
    id = ItemUpgrade.UpgradeSuperiorRuneDervish
    mod_type = ItemUpgradeType.UpgradeRune

class AppliesToMinorRuneDervish(Upgrade):
    id = ItemUpgrade.AppliesToMinorRuneDervish
    mod_type = ItemUpgradeType.AppliesToRune

class AppliesToMajorRuneDervish(Upgrade):
    id = ItemUpgrade.AppliesToMajorRuneDervish
    mod_type = ItemUpgradeType.AppliesToRune

class AppliesToSuperiorRuneDervish(Upgrade):
    id = ItemUpgrade.AppliesToSuperiorRuneDervish
    mod_type = ItemUpgradeType.AppliesToRune

#endregion Dervish

#region Paragon

class CenturionsInsignia(Insignia):
    id = ItemUpgrade.CenturionsInsignia
    names = {
        ServerLanguage.English: "Centurion's Insignia [Paragon]",
        ServerLanguage.Korean: "백부장의 휘장 [파라곤]",
        ServerLanguage.French: "Insigne [Parangon] du centurion",
        ServerLanguage.German: "Zenturio- [Paragon]-Befähigung",
        ServerLanguage.Italian: "Insegne [Paragon] da Centurione",
        ServerLanguage.Spanish: "Insignia [Paragón] de centurión",
        ServerLanguage.TraditionalChinese: "百夫長 徽記 [聖言者]",
        ServerLanguage.Japanese: "センチュリオン 記章 [パラゴン]",
        ServerLanguage.Polish: "[Patron] Symbol Centuriona",
        ServerLanguage.Russian: "Centurion's Insignia [Paragon]",
        ServerLanguage.BorkBorkBork: "Centooreeun's Inseegneea [Paeraegun]",
    }
    
    descriptions = {
        ServerLanguage.English: f"Armor +10 (while affected by a Shout, Echo, or Chant)"
    }

class ParagonRuneOfMinorLeadership(AttributeRune):
    id = ItemUpgrade.ParagonRuneOfMinorLeadership
    rarity = Rarity.Blue

    names = {
        ServerLanguage.English: "Paragon Rune of Minor Leadership",
        ServerLanguage.Korean: "파라곤 룬(하급 리더십)",
        ServerLanguage.French: "Rune de Parangon (Charisme : bonus mineur)",
        ServerLanguage.German: "Paragon-Rune d. kleineren Führung",
        ServerLanguage.Italian: "Runa del Paragon Leadership di grado minore",
        ServerLanguage.Spanish: "Runa de Paragón (Liderazgo de grado menor)",
        ServerLanguage.TraditionalChinese: "初級 領導 聖言者符文",
        ServerLanguage.Japanese: "パラゴン ルーン (マイナー リーダーシップ)",
        ServerLanguage.Polish: "Runa Patrona (Przywództwo niższego poziomu)",
        ServerLanguage.Russian: "Paragon Rune of Minor Leadership",
        ServerLanguage.BorkBorkBork: "Paeraegun Roone-a ooff Meenur Leaedersheep",
    }

class ParagonRuneOfMinorMotivation(AttributeRune):
    id = ItemUpgrade.ParagonRuneOfMinorMotivation
    rarity = Rarity.Blue

    names = {
        ServerLanguage.English: "Paragon Rune of Minor Motivation",
        ServerLanguage.Korean: "파라곤 룬(하급 격려)",
        ServerLanguage.French: "Rune de Parangon (Motivation : bonus mineur)",
        ServerLanguage.German: "Paragon-Rune d. kleineren Motivation",
        ServerLanguage.Italian: "Runa del Paragon Motivazione di grado minore",
        ServerLanguage.Spanish: "Runa de Paragón (Motivación de grado menor)",
        ServerLanguage.TraditionalChinese: "初級 激勵 聖言者符文",
        ServerLanguage.Japanese: "パラゴン ルーン (マイナー モチベーション)",
        ServerLanguage.Polish: "Runa Patrona (Motywacja niższego poziomu)",
        ServerLanguage.Russian: "Paragon Rune of Minor Motivation",
        ServerLanguage.BorkBorkBork: "Paeraegun Roone-a ooff Meenur Muteefaeshun",
    }

class ParagonRuneOfMinorCommand(AttributeRune):
    id = ItemUpgrade.ParagonRuneOfMinorCommand
    rarity = Rarity.Blue

    names = {
        ServerLanguage.English: "Paragon Rune of Minor Command",
        ServerLanguage.Korean: "파라곤 룬(하급 통솔)",
        ServerLanguage.French: "Rune de Parangon (Commandement : bonus mineur)",
        ServerLanguage.German: "Paragon-Rune d. kleineren Befehlsgewalt",
        ServerLanguage.Italian: "Runa del Paragon Comando di grado minore",
        ServerLanguage.Spanish: "Runa de Paragón (Mando de grado menor)",
        ServerLanguage.TraditionalChinese: "初級 命令 聖言者符文",
        ServerLanguage.Japanese: "パラゴン ルーン (マイナー コマンド)",
        ServerLanguage.Polish: "Runa Patrona (Rozkazy niższego poziomu)",
        ServerLanguage.Russian: "Paragon Rune of Minor Command",
        ServerLanguage.BorkBorkBork: "Paeraegun Roone-a ooff Meenur Cummund",
    }

class ParagonRuneOfMinorSpearMastery(AttributeRune):
    id = ItemUpgrade.ParagonRuneOfMinorSpearMastery
    rarity = Rarity.Blue

    names = {
        ServerLanguage.English: "Paragon Rune of Minor Spear Mastery",
        ServerLanguage.Korean: "파라곤 룬(하급 창술)",
        ServerLanguage.French: "Rune de Parangon (Maîtrise du javelot : bonus mineur)",
        ServerLanguage.German: "Paragon-Rune d. kleineren Speerbeherrschung",
        ServerLanguage.Italian: "Runa del Paragon Abilità con la Lancia di grado minore",
        ServerLanguage.Spanish: "Runa de Paragón (Dominio de la lanza de grado menor)",
        ServerLanguage.TraditionalChinese: "初級 矛術精通 聖言者符文",
        ServerLanguage.Japanese: "パラゴン ルーン (マイナー スピア マスタリー)",
        ServerLanguage.Polish: "Runa Patrona (Biegłość we Włóczniach niższego poziomu)",
        ServerLanguage.Russian: "Paragon Rune of Minor Spear Mastery",
        ServerLanguage.BorkBorkBork: "Paeraegun Roone-a ooff Meenur Speaer Maestery",
    }

class ParagonRuneOfMajorLeadership(AttributeRune):
    id = ItemUpgrade.ParagonRuneOfMajorLeadership
    rarity = Rarity.Purple

    property_identifiers = [
        ModifierIdentifier.HealthMinus
    ]

    names = {
        ServerLanguage.English: "Paragon Rune of Major Leadership",
        ServerLanguage.Korean: "파라곤 룬(상급 리더십)",
        ServerLanguage.French: "Rune de Parangon (Charisme : bonus majeur)",
        ServerLanguage.German: "Paragon-Rune d. hohen Führung",
        ServerLanguage.Italian: "Runa del Paragon Leadership di grado maggiore",
        ServerLanguage.Spanish: "Runa de Paragón (Liderazgo de grado mayor)",
        ServerLanguage.TraditionalChinese: "中級 領導 聖言者符文",
        ServerLanguage.Japanese: "パラゴン ルーン (メジャー リーダーシップ)",
        ServerLanguage.Polish: "Runa Patrona (Przywództwo wyższego poziomu)",
        ServerLanguage.Russian: "Paragon Rune of Major Leadership",
        ServerLanguage.BorkBorkBork: "Paeraegun Roone-a ooff Maejur Leaedersheep",
    }

class ParagonRuneOfMajorMotivation(AttributeRune):
    id = ItemUpgrade.ParagonRuneOfMajorMotivation
    rarity = Rarity.Purple

    property_identifiers = [
        ModifierIdentifier.HealthMinus
    ]

    names = {
        ServerLanguage.English: "Paragon Rune of Major Motivation",
        ServerLanguage.Korean: "파라곤 룬(상급 격려)",
        ServerLanguage.French: "Rune de Parangon (Motivation : bonus majeur)",
        ServerLanguage.German: "Paragon-Rune d. hohen Motivation",
        ServerLanguage.Italian: "Runa del Paragon Motivazione di grado maggiore",
        ServerLanguage.Spanish: "Runa de Paragón (Motivación de grado mayor)",
        ServerLanguage.TraditionalChinese: "中級 激勵 聖言者符文",
        ServerLanguage.Japanese: "パラゴン ルーン (メジャー モチベーション)",
        ServerLanguage.Polish: "Runa Patrona (Motywacja wyższego poziomu)",
        ServerLanguage.Russian: "Paragon Rune of Major Motivation",
        ServerLanguage.BorkBorkBork: "Paeraegun Roone-a ooff Maejur Muteefaeshun",
    }

class ParagonRuneOfMajorCommand(AttributeRune):
    id = ItemUpgrade.ParagonRuneOfMajorCommand
    rarity = Rarity.Purple

    property_identifiers = [
        ModifierIdentifier.HealthMinus
    ]

    names = {
        ServerLanguage.English: "Paragon Rune of Major Command",
        ServerLanguage.Korean: "파라곤 룬(상급 통솔)",
        ServerLanguage.French: "Rune de Parangon (Commandement : bonus majeur)",
        ServerLanguage.German: "Paragon-Rune d. hohen Befehlsgewalt",
        ServerLanguage.Italian: "Runa del Paragon Comando di grado maggiore",
        ServerLanguage.Spanish: "Runa de Paragón (Mando de grado mayor)",
        ServerLanguage.TraditionalChinese: "中級 命令 聖言者符文",
        ServerLanguage.Japanese: "パラゴン ルーン (メジャー コマンド)",
        ServerLanguage.Polish: "Runa Patrona (Rozkazy wyższego poziomu)",
        ServerLanguage.Russian: "Paragon Rune of Major Command",
        ServerLanguage.BorkBorkBork: "Paeraegun Roone-a ooff Maejur Cummund",
    }

class ParagonRuneOfMajorSpearMastery(AttributeRune):
    id = ItemUpgrade.ParagonRuneOfMajorSpearMastery
    rarity = Rarity.Purple

    property_identifiers = [
        ModifierIdentifier.HealthMinus
    ]

    names = {
        ServerLanguage.English: "Paragon Rune of Major Spear Mastery",
        ServerLanguage.Korean: "파라곤 룬(상급 창술)",
        ServerLanguage.French: "Rune de Parangon (Maîtrise du javelot : bonus majeur)",
        ServerLanguage.German: "Paragon-Rune d. hohen Speerbeherrschung",
        ServerLanguage.Italian: "Runa del Paragon Abilità con la Lancia di grado maggiore",
        ServerLanguage.Spanish: "Runa de Paragón (Dominio de la lanza de grado mayor)",
        ServerLanguage.TraditionalChinese: "中級 矛術精通 聖言者符文",
        ServerLanguage.Japanese: "パラゴン ルーン (メジャー スピア マスタリー)",
        ServerLanguage.Polish: "Runa Patrona (Biegłość we Włóczniach wyższego poziomu)",
        ServerLanguage.Russian: "Paragon Rune of Major Spear Mastery",
        ServerLanguage.BorkBorkBork: "Paeraegun Roone-a ooff Maejur Speaer Maestery",
    }

class ParagonRuneOfSuperiorLeadership(AttributeRune):
    id = ItemUpgrade.ParagonRuneOfSuperiorLeadership
    rarity = Rarity.Gold

    property_identifiers = [
        ModifierIdentifier.HealthMinus
    ]

    names = {
        ServerLanguage.English: "Paragon Rune of Superior Leadership",
        ServerLanguage.Korean: "파라곤 룬(고급 리더십)",
        ServerLanguage.French: "Rune de Parangon (Charisme : bonus supérieur)",
        ServerLanguage.German: "Paragon-Rune d. überlegenen Führung",
        ServerLanguage.Italian: "Runa del Paragon Leadership di grado supremo",
        ServerLanguage.Spanish: "Runa de Paragón (Liderazgo de grado excepcional)",
        ServerLanguage.TraditionalChinese: "高級 領導 聖言者符文",
        ServerLanguage.Japanese: "パラゴン ルーン (スーペリア リーダーシップ)",
        ServerLanguage.Polish: "Runa Patrona (Przywództwo najwyższego poziomu)",
        ServerLanguage.Russian: "Paragon Rune of Superior Leadership",
        ServerLanguage.BorkBorkBork: "Paeraegun Roone-a ooff Soopereeur Leaedersheep",
    }

class ParagonRuneOfSuperiorMotivation(AttributeRune):
    id = ItemUpgrade.ParagonRuneOfSuperiorMotivation
    rarity = Rarity.Gold

    property_identifiers = [
        ModifierIdentifier.HealthMinus
    ]

    names = {
        ServerLanguage.English: "Paragon Rune of Superior Motivation",
        ServerLanguage.Korean: "파라곤 룬(고급 격려)",
        ServerLanguage.French: "Rune de Parangon (Motivation : bonus supérieur)",
        ServerLanguage.German: "Paragon-Rune d. überlegenen Motivation",
        ServerLanguage.Italian: "Runa del Paragon Motivazione di grado supremo",
        ServerLanguage.Spanish: "Runa de Paragón (Motivación de grado excepcional)",
        ServerLanguage.TraditionalChinese: "高級 激勵 聖言者符文",
        ServerLanguage.Japanese: "パラゴン ルーン (スーペリア モチベーション)",
        ServerLanguage.Polish: "Runa Patrona (Motywacja najwyższego poziomu)",
        ServerLanguage.Russian: "Paragon Rune of Superior Motivation",
        ServerLanguage.BorkBorkBork: "Paeraegun Roone-a ooff Soopereeur Muteefaeshun",
    }

class ParagonRuneOfSuperiorCommand(AttributeRune):
    id = ItemUpgrade.ParagonRuneOfSuperiorCommand
    rarity = Rarity.Gold

    property_identifiers = [
        ModifierIdentifier.HealthMinus
    ]

    names = {
        ServerLanguage.English: "Paragon Rune of Superior Command",
        ServerLanguage.Korean: "파라곤 룬(고급 통솔)",
        ServerLanguage.French: "Rune de Parangon (Commandement : bonus supérieur)",
        ServerLanguage.German: "Paragon-Rune d. überlegenen Befehlsgewalt",
        ServerLanguage.Italian: "Runa del Paragon Comando di grado supremo",
        ServerLanguage.Spanish: "Runa de Paragón (Mando de grado excepcional)",
        ServerLanguage.TraditionalChinese: "高級 命令 聖言者符文",
        ServerLanguage.Japanese: "パラゴン ルーン (スーペリア コマンド)",
        ServerLanguage.Polish: "Runa Patrona (Rozkazy najwyższego poziomu)",
        ServerLanguage.Russian: "Paragon Rune of Superior Command",
        ServerLanguage.BorkBorkBork: "Paeraegun Roone-a ooff Soopereeur Cummund",
    }

class ParagonRuneOfSuperiorSpearMastery(AttributeRune):
    id = ItemUpgrade.ParagonRuneOfSuperiorSpearMastery
    rarity = Rarity.Gold

    property_identifiers = [
        ModifierIdentifier.HealthMinus
    ]

    names = {
        ServerLanguage.English: "Paragon Rune of Superior Spear Mastery",
        ServerLanguage.Korean: "파라곤 룬(고급 창술)",
        ServerLanguage.French: "Rune de Parangon (Maîtrise du javelot : bonus supérieur)",
        ServerLanguage.German: "Paragon-Rune d. überlegenen Speerbeherrschung",
        ServerLanguage.Italian: "Runa del Paragon Abilità con la Lancia di grado supremo",
        ServerLanguage.Spanish: "Runa de Paragón (Dominio de la lanza de grado excepcional)",
        ServerLanguage.TraditionalChinese: "高級 矛術精通 聖言者符文",
        ServerLanguage.Japanese: "パラゴン ルーン (スーペリア スピア マスタリー)",
        ServerLanguage.Polish: "Runa Patrona (Biegłość we Włóczniach najwyższego poziomu)",
        ServerLanguage.Russian: "Paragon Rune of Superior Spear Mastery",
        ServerLanguage.BorkBorkBork: "Paeraegun Roone-a ooff Soopereeur Speaer Maestery",
    }

class UpgradeMinorRuneParagon(Upgrade):
    id = ItemUpgrade.UpgradeMinorRuneParagon
    mod_type = ItemUpgradeType.UpgradeRune

class UpgradeMajorRuneParagon(Upgrade):
    id = ItemUpgrade.UpgradeMajorRuneParagon
    mod_type = ItemUpgradeType.UpgradeRune

class UpgradeSuperiorRuneParagon(Upgrade):
    id = ItemUpgrade.UpgradeSuperiorRuneParagon
    mod_type = ItemUpgradeType.UpgradeRune

class AppliesToMinorRuneParagon(Upgrade):
    id = ItemUpgrade.AppliesToMinorRuneParagon
    mod_type = ItemUpgradeType.AppliesToRune

class AppliesToMajorRuneParagon(Upgrade):
    id = ItemUpgrade.AppliesToMajorRuneParagon
    mod_type = ItemUpgradeType.AppliesToRune

class AppliesToSuperiorRuneParagon(Upgrade):
    id = ItemUpgrade.AppliesToSuperiorRuneParagon
    mod_type = ItemUpgradeType.AppliesToRune

#endregion Paragon

#endregion Armor Upgrades

_UPGRADES: list[type[Upgrade]] = [
    IcyUpgrade,
    EbonUpgrade,
    ShockingUpgrade,
    FieryUpgrade,
    BarbedUpgrade,
    CripplingUpgrade,
    CruelUpgrade,
    PoisonousUpgrade,
    SilencingUpgrade,
    FuriousUpgrade,
    HeavyUpgrade,
    ZealousUpgrade,
    VampiricUpgrade,
    SunderingUpgrade,
    DefensiveUpgrade,
    InsightfulUpgrade,
    HaleUpgrade,
    OfDefenseUpgrade,
    OfWardingUpgrade,
    OfShelterUpgrade,
    OfSlayingUpgrade,
    OfFortitudeUpgrade,
    OfEnchantingUpgrade,
    OfTheProfessionUpgrade,
    OfAxeMasteryUpgrade,
    OfMarksmanshipUpgrade,
    OfDaggerMasteryUpgrade,
    OfHammerMasteryUpgrade,
    OfScytheMasteryUpgrade,
    OfSpearMasteryUpgrade,
    OfSwordsmanshipUpgrade,
    OfAttributeUpgrade,
    OfMasteryUpgrade,
    SwiftStaffUpgrade,
    AdeptStaffUpgrade,
    OfMemoryUpgrade,
    OfQuickeningUpgrade,
    OfAptitudeUpgrade,
    OfDevotionUpgrade,
    OfValorUpgrade,
    OfEnduranceUpgrade,
    OfSwiftnessUpgrade,
    
    BeJustAndFearNot,
    DownButNotOut,
    FaithIsMyShield,
    ForgetMeNot,
    HailToTheKing,
    IgnoranceIsBliss,
    KnowingIsHalfTheBattle,
    LifeIsPain,
    LiveForToday,
    ManForAllSeasons,
    MightMakesRight,
    SerenityNow,
    SurvivalOfTheFittest,
    BrawnOverBrains,
    DanceWithDeath,
    DontFearTheReaper,
    DontThinkTwice,
    GuidedByFate,
    StrengthAndHonor,
    ToThePain,
    TooMuchInformation,
    VengeanceIsMine,
    IHaveThePower,
    LetTheMemoryLiveAgain,
    CastOutTheUnclean,
    FearCutsDeeper,
    ICanSeeClearlyNow,
    LeafOnTheWind,
    LikeARollingStone,
    LuckOfTheDraw,
    MasterOfMyDomain,
    NotTheFace,
    NothingToFear,
    OnlyTheStrongSurvive,
    PureOfHeart,
    RidersOnTheStorm,
    RunForYourLife,
    ShelteredByFaith,
    SleepNowInTheFire,
    SoundnessOfMind,
    StrengthOfBody,
    SwiftAsTheWind,
    TheRiddleOfSteel,
    ThroughThickAndThin,
    MeasureForMeasure,
    ShowMeTheMoney,
    AptitudeNotAttitude,
    DontCallItAComeback,
    HaleAndHearty,
    HaveFaith,
    IAmSorrow,
    SeizeTheDay,
        
    # No Profession
    SurvivorInsignia,
    RadiantInsignia,
    StalwartInsignia,
    BrawlersInsignia,
    BlessedInsignia,
    HeraldsInsignia,
    SentrysInsignia,
    
    # Warrior
    KnightsInsignia,
    LieutenantsInsignia,
    StonefistInsignia,
    DreadnoughtInsignia,
    SentinelsInsignia,
    
    # Ranger
    FrostboundInsignia,
    PyreboundInsignia,
    StormboundInsignia,
    ScoutsInsignia,
    EarthboundInsignia,
    BeastmastersInsignia,
    
    # Monk
    WanderersInsignia,
    DisciplesInsignia,
    AnchoritesInsignia,
    
    # Necromancer
    BloodstainedInsignia,
    TormentorsInsignia,
    BonelaceInsignia,
    MinionMastersInsignia,
    BlightersInsignia,
    UndertakersInsignia,
    
    # Mesmer 
    VirtuososInsignia,
    ArtificersInsignia,
    ProdigysInsignia,
    
    # Elementalist
    HydromancerInsignia,
    GeomancerInsignia,
    PyromancerInsignia,
    AeromancerInsignia,
    PrismaticInsignia,
    
    # Assassin
    VanguardsInsignia,
    InfiltratorsInsignia,
    SaboteursInsignia,
    NightstalkersInsignia,
    
    # Ritualist
    ShamansInsignia,
    GhostForgeInsignia,
    MysticsInsignia,
    
    # Dervish
    WindwalkerInsignia,
    ForsakenInsignia,
    
    # Paragon
    CenturionsInsignia,    
    
    #No Profession
    RuneOfMinorVigor,
    RuneOfMinorVigor2,
    RuneOfVitae,
    RuneOfAttunement,
    RuneOfMajorVigor,
    RuneOfRecovery,
    RuneOfRestoration,
    RuneOfClarity,
    RuneOfPurity,
    RuneOfSuperiorVigor,
    
    # Warrior    
    WarriorRuneOfMinorAbsorption,
    WarriorRuneOfMinorTactics,
    WarriorRuneOfMinorStrength,
    WarriorRuneOfMinorAxeMastery,
    WarriorRuneOfMinorHammerMastery,
    WarriorRuneOfMinorSwordsmanship,
    WarriorRuneOfMajorAbsorption,
    WarriorRuneOfMajorTactics,
    WarriorRuneOfMajorStrength,
    WarriorRuneOfMajorAxeMastery,
    WarriorRuneOfMajorHammerMastery,
    WarriorRuneOfMajorSwordsmanship,
    WarriorRuneOfSuperiorAbsorption,
    WarriorRuneOfSuperiorTactics,
    WarriorRuneOfSuperiorStrength,
    WarriorRuneOfSuperiorAxeMastery,
    WarriorRuneOfSuperiorHammerMastery,
    WarriorRuneOfSuperiorSwordsmanship,
    
    UpgradeMinorRuneWarrior,
    UpgradeMajorRuneWarrior,
    UpgradeSuperiorRuneWarrior,
    AppliesToMinorRuneWarrior,
    AppliesToMajorRuneWarrior,
    AppliesToSuperiorRuneWarrior,
    
    # Ranger        
    RangerRuneOfMinorWildernessSurvival,
    RangerRuneOfMinorExpertise,
    RangerRuneOfMinorBeastMastery,
    RangerRuneOfMinorMarksmanship,
    RangerRuneOfMajorWildernessSurvival,
    RangerRuneOfMajorExpertise,
    RangerRuneOfMajorBeastMastery,
    RangerRuneOfMajorMarksmanship,
    RangerRuneOfSuperiorWildernessSurvival,
    RangerRuneOfSuperiorExpertise,
    RangerRuneOfSuperiorBeastMastery,
    RangerRuneOfSuperiorMarksmanship,
    
    UpgradeMinorRuneRanger,
    UpgradeMajorRuneRanger,
    UpgradeSuperiorRuneRanger,
    AppliesToMinorRuneRanger,
    AppliesToMajorRuneRanger,
    AppliesToSuperiorRuneRanger,
    
    # Monk    
    MonkRuneOfMinorHealingPrayers,
    MonkRuneOfMinorSmitingPrayers,
    MonkRuneOfMinorProtectionPrayers,
    MonkRuneOfMinorDivineFavor,
    MonkRuneOfMajorHealingPrayers,
    MonkRuneOfMajorSmitingPrayers,
    MonkRuneOfMajorProtectionPrayers,
    MonkRuneOfMajorDivineFavor,
    MonkRuneOfSuperiorHealingPrayers,
    MonkRuneOfSuperiorSmitingPrayers,
    MonkRuneOfSuperiorProtectionPrayers,
    MonkRuneOfSuperiorDivineFavor,
    
    UpgradeMinorRuneMonk,
    UpgradeMajorRuneMonk,
    UpgradeSuperiorRuneMonk,
    AppliesToMinorRuneMonk,
    AppliesToMajorRuneMonk,
    AppliesToSuperiorRuneMonk,
    
    # Necromancer
    NecromancerRuneOfMinorBloodMagic,
    NecromancerRuneOfMinorDeathMagic,
    NecromancerRuneOfMinorCurses,
    NecromancerRuneOfMinorSoulReaping,
    NecromancerRuneOfMajorBloodMagic,
    NecromancerRuneOfMajorDeathMagic,
    NecromancerRuneOfMajorCurses,
    NecromancerRuneOfMajorSoulReaping,
    NecromancerRuneOfSuperiorBloodMagic,
    NecromancerRuneOfSuperiorDeathMagic,
    NecromancerRuneOfSuperiorCurses,
    NecromancerRuneOfSuperiorSoulReaping,
    
    UpgradeMinorRuneNecromancer,
    UpgradeMajorRuneNecromancer,
    UpgradeSuperiorRuneNecromancer,
    AppliesToMinorRuneNecromancer,
    AppliesToMajorRuneNecromancer,
    AppliesToSuperiorRuneNecromancer,
    
    # Mesmer 
    MesmerRuneOfMinorFastCasting,
    MesmerRuneOfMinorDominationMagic,
    MesmerRuneOfMinorIllusionMagic,
    MesmerRuneOfMinorInspirationMagic,
    MesmerRuneOfMajorFastCasting,
    MesmerRuneOfMajorDominationMagic,
    MesmerRuneOfMajorIllusionMagic,
    MesmerRuneOfMajorInspirationMagic,
    MesmerRuneOfSuperiorFastCasting,
    MesmerRuneOfSuperiorDominationMagic,
    MesmerRuneOfSuperiorIllusionMagic,
    MesmerRuneOfSuperiorInspirationMagic,
    
    UpgradeMinorRuneMesmer,
    UpgradeMajorRuneMesmer,
    UpgradeSuperiorRuneMesmer,
    AppliesToMinorRuneMesmer,
    AppliesToMajorRuneMesmer,
    AppliesToSuperiorRuneMesmer,
    
    # Elementalist
    ElementalistRuneOfMinorEnergyStorage,
    ElementalistRuneOfMinorFireMagic,
    ElementalistRuneOfMinorAirMagic,
    ElementalistRuneOfMinorEarthMagic,
    ElementalistRuneOfMinorWaterMagic,
    ElementalistRuneOfMajorEnergyStorage,
    ElementalistRuneOfMajorFireMagic,
    ElementalistRuneOfMajorAirMagic,
    ElementalistRuneOfMajorEarthMagic,
    ElementalistRuneOfMajorWaterMagic,
    ElementalistRuneOfSuperiorEnergyStorage,
    ElementalistRuneOfSuperiorFireMagic,
    ElementalistRuneOfSuperiorAirMagic,
    ElementalistRuneOfSuperiorEarthMagic,
    ElementalistRuneOfSuperiorWaterMagic,
    
    UpgradeMinorRuneElementalist,
    UpgradeMajorRuneElementalist,
    UpgradeSuperiorRuneElementalist,
    AppliesToMinorRuneElementalist,
    AppliesToMajorRuneElementalist,
    AppliesToSuperiorRuneElementalist,
    
    # Assassin
    AssassinRuneOfMinorCriticalStrikes,
    AssassinRuneOfMinorDaggerMastery,
    AssassinRuneOfMinorDeadlyArts,
    AssassinRuneOfMinorShadowArts,
    AssassinRuneOfMajorCriticalStrikes,
    AssassinRuneOfMajorDaggerMastery,
    AssassinRuneOfMajorDeadlyArts,
    AssassinRuneOfMajorShadowArts,
    AssassinRuneOfSuperiorCriticalStrikes,
    AssassinRuneOfSuperiorDaggerMastery,
    AssassinRuneOfSuperiorDeadlyArts,
    AssassinRuneOfSuperiorShadowArts,
    
    UpgradeMinorRuneAssassin,
    UpgradeMajorRuneAssassin,
    UpgradeSuperiorRuneAssassin,
    AppliesToMinorRuneAssassin,
    AppliesToMajorRuneAssassin,
    AppliesToSuperiorRuneAssassin,
    
    # Ritualist
    RitualistRuneOfMinorChannelingMagic,
    RitualistRuneOfMinorRestorationMagic,
    RitualistRuneOfMinorCommuning,
    RitualistRuneOfMinorSpawningPower,
    RitualistRuneOfMajorChannelingMagic,
    RitualistRuneOfMajorRestorationMagic,
    RitualistRuneOfMajorCommuning,
    RitualistRuneOfMajorSpawningPower,
    RitualistRuneOfSuperiorChannelingMagic,
    RitualistRuneOfSuperiorRestorationMagic,
    RitualistRuneOfSuperiorCommuning,
    RitualistRuneOfSuperiorSpawningPower,
    
    UpgradeMinorRuneRitualist,
    UpgradeMajorRuneRitualist,
    UpgradeSuperiorRuneRitualist,
    AppliesToMinorRuneRitualist,
    AppliesToMajorRuneRitualist,
    AppliesToSuperiorRuneRitualist,
    
    # Dervish
    DervishRuneOfMinorMysticism,
    DervishRuneOfMinorEarthPrayers,
    DervishRuneOfMinorScytheMastery,
    DervishRuneOfMinorWindPrayers,
    DervishRuneOfMajorMysticism,
    DervishRuneOfMajorEarthPrayers,
    DervishRuneOfMajorScytheMastery,
    DervishRuneOfMajorWindPrayers,
    DervishRuneOfSuperiorMysticism,
    DervishRuneOfSuperiorEarthPrayers,
    DervishRuneOfSuperiorScytheMastery,
    DervishRuneOfSuperiorWindPrayers,
    
    UpgradeMinorRuneDervish,
    UpgradeMajorRuneDervish,
    UpgradeSuperiorRuneDervish,
    AppliesToMinorRuneDervish,
    AppliesToMajorRuneDervish,
    AppliesToSuperiorRuneDervish,
    
    # Paragon    
    ParagonRuneOfMinorLeadership,
    ParagonRuneOfMinorMotivation,
    ParagonRuneOfMinorCommand,
    ParagonRuneOfMinorSpearMastery,
    ParagonRuneOfMajorLeadership,
    ParagonRuneOfMajorMotivation,
    ParagonRuneOfMajorCommand,
    ParagonRuneOfMajorSpearMastery,
    ParagonRuneOfSuperiorLeadership,
    ParagonRuneOfSuperiorMotivation,
    ParagonRuneOfSuperiorCommand,
    ParagonRuneOfSuperiorSpearMastery,   
    
    UpgradeMinorRuneParagon,
    UpgradeMajorRuneParagon,
    UpgradeSuperiorRuneParagon,
    AppliesToMinorRuneParagon,
    AppliesToMajorRuneParagon,
    AppliesToSuperiorRuneParagon, 
]

