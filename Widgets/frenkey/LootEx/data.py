import datetime
import json
import os
import shutil
from typing import Optional

from Py4GW import Console
import Py4GW
from Py4GWCoreLib.enums_src.GameData_enums import DyeColor
from Widgets.frenkey.LootEx import models
from Widgets.frenkey.LootEx.enum import ItemCategory, ModType, ModsModels
from Py4GWCoreLib.GlobalCache import GLOBAL_CACHE
from Py4GWCoreLib.Py4GWcorelib import ConsoleLog
from Py4GWCoreLib.enums import Attribute, ServerLanguage
from Py4GWCoreLib.enums import ItemType, Profession
from Widgets.frenkey.LootEx.texture_scraping_models import ScrapedItem

class Data():
    _instance = None
    _initialized = False
                    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        # only initialize once
        if self._initialized:
            return
        
        self._initialized = True
    
        self.is_loaded: bool = False

        self.ColorNames: dict[ServerLanguage, dict[DyeColor, str]] = {
            ServerLanguage.English: {
                DyeColor.Blue: "Blue",
                DyeColor.Green: "Green",
                DyeColor.Purple: "Purple",
                DyeColor.Red: "Red",
                DyeColor.Yellow: "Yellow",
                DyeColor.Brown: "Brown",
                DyeColor.Orange: "Orange",
                DyeColor.Silver: "Silver",
                DyeColor.Black: "Black",
                DyeColor.Gray: "Gray",
                DyeColor.White: "White",
                DyeColor.Pink: "Pink",
            },
            ServerLanguage.Korean: {
                DyeColor.Blue: "파란색",
                DyeColor.Green: "초록색",
                DyeColor.Purple: "보라색",
                DyeColor.Red: "빨간색",
                DyeColor.Yellow: "노란색",
                DyeColor.Brown: "갈색",
                DyeColor.Orange: "주황색",
                DyeColor.Silver: "은색",
                DyeColor.Black: "검은색",
                DyeColor.Gray: "회색",
                DyeColor.White: "흰색",
                DyeColor.Pink: "분홍색",
            },
            ServerLanguage.French: {
                DyeColor.Blue: "Bleu",
                DyeColor.Green: "Vert",
                DyeColor.Purple: "Pourpre",
                DyeColor.Red: "Rouge",
                DyeColor.Yellow: "Jaune",
                DyeColor.Brown: "Marrone",
                DyeColor.Orange: "Orange",
                DyeColor.Silver: "Argent",
                DyeColor.Black: "Noir",
                DyeColor.Gray: "Gris",
                DyeColor.White: "Blanc",
                DyeColor.Pink: "Rose",
            },
            ServerLanguage.German: {
                DyeColor.Blue: "Blau",
                DyeColor.Green: "Grün",
                DyeColor.Purple: "Lila",
                DyeColor.Red: "Rot",
                DyeColor.Yellow: "Gelb",
                DyeColor.Brown: "Braun",
                DyeColor.Orange: "Orange",
                DyeColor.Silver: "Silber",
                DyeColor.Black: "Schwarz",
                DyeColor.Gray: "Grau",
                DyeColor.White: "Weiß",
                DyeColor.Pink: "Rosa",
            },
            ServerLanguage.Italian: {
                DyeColor.Blue: "Blu",
                DyeColor.Green: "Verde",
                DyeColor.Purple: "Porpora",
                DyeColor.Red: "Rosso",
                DyeColor.Yellow: "Giallo",
                DyeColor.Brown: "Marrone",
                DyeColor.Orange: "Arancione",
                DyeColor.Silver: "Argento",
                DyeColor.Black: "Nero",
                DyeColor.Gray: "Grigio",
                DyeColor.White: "Bianco",
                DyeColor.Pink: "Rosa",
            },
            ServerLanguage.Spanish: {
                DyeColor.Blue: "Azul",
                DyeColor.Green: "Verde",
                DyeColor.Purple: "Púrpura",
                DyeColor.Red: "Rojo",
                DyeColor.Yellow: "Amarillo",
                DyeColor.Brown: "Marrón",
                DyeColor.Orange: "Naranja",
                DyeColor.Silver: "Plata",
                DyeColor.Black: "Negro",
                DyeColor.Gray: "Gris",
                DyeColor.White: "Blanco",
                DyeColor.Pink: "Rosa",
            },
            ServerLanguage.TraditionalChinese: {
                DyeColor.Blue: "藍色",
                DyeColor.Green: "綠色",
                DyeColor.Purple: "紫色",
                DyeColor.Red: "紅色",
                DyeColor.Yellow: "黃色",
                DyeColor.Brown: "棕色",
                DyeColor.Orange: "橙色",
                DyeColor.Silver: "銀色",
                DyeColor.Black: "黑色",
                DyeColor.Gray: "灰色",
                DyeColor.White: "白色",
                DyeColor.Pink: "粉紅色",
            },
            ServerLanguage.Japanese: {
                DyeColor.Blue: "青",
                DyeColor.Green: "緑",
                DyeColor.Purple: "紫",
                DyeColor.Red: "赤",
                DyeColor.Yellow: "黄",
                DyeColor.Brown: "茶色",
                DyeColor.Orange: "オレンジ",
                DyeColor.Silver: "銀",
                DyeColor.Black: "黒",
                DyeColor.Gray: "灰色",
                DyeColor.White: "白",
                DyeColor.Pink: "ピンク",
            },
            ServerLanguage.Polish: {
                DyeColor.Blue: "Niebieski",
                DyeColor.Green: "Zielony",
                DyeColor.Purple: "Fioletowy",
                DyeColor.Red: "Czerwony",
                DyeColor.Yellow: "Żółty",
                DyeColor.Brown: "Brązowy",
                DyeColor.Orange: "Pomarańczowy",
                DyeColor.Silver: "Srebrny",
                DyeColor.Black: "Czarny",
                DyeColor.Gray: "Szary",
                DyeColor.White: "Biały",
                DyeColor.Pink: "Różowy",
            },
            ServerLanguage.Russian: {
                DyeColor.Blue: "Синий",
                DyeColor.Green: "Зеленый",
                DyeColor.Purple: "Пурпурный",
                DyeColor.Red: "Красный",
                DyeColor.Yellow: "Желтый",
                DyeColor.Brown: "Коричневый",
                DyeColor.Orange: "Оранжевый",
                DyeColor.Silver: "Серебряный",
                DyeColor.Black: "Черный",
                DyeColor.Gray: "Серый",
                DyeColor.White: "Белый",
                DyeColor.Pink: "Розовый",
            },
            ServerLanguage.BorkBorkBork: {
                DyeColor.Blue: "Blooe-a",
                DyeColor.Green: "Greee",
                DyeColor.Purple: "Poorple-a",
                DyeColor.Red: "Red",
                DyeColor.Yellow: "Yelloo",
                DyeColor.Brown: "Broon",
                DyeColor.Orange: "Oorunge-a",
                DyeColor.Silver: "Seelfer",
                DyeColor.Black: "Blaeck",
                DyeColor.Gray: "Graey",
                DyeColor.White: "Vheete-a",
                DyeColor.Pink: "Peenk",
            },

        }
        
        self.ModsByItemType: dict[ItemType, models.ModsPair] = {
            ItemType.Axe: models.ModsPair(ModsModels.AxeHaft, ModsModels.AxeGrip),
            ItemType.Bow: models.ModsPair(ModsModels.BowString, ModsModels.BowGrip),
            ItemType.Daggers: models.ModsPair(ModsModels.DaggerTang, ModsModels.DaggerHandle),
            ItemType.Offhand: models.ModsPair(None, ModsModels.FocusCore),
            ItemType.Hammer: models.ModsPair(ModsModels.HammerHaft, ModsModels.HammerGrip),
            ItemType.Scythe: models.ModsPair(ModsModels.ScytheSnathe, ModsModels.ScytheGrip),
            ItemType.Shield: models.ModsPair(None, ModsModels.ShieldHandle),
            ItemType.Spear: models.ModsPair(ModsModels.Spearhead, ModsModels.SpearGrip),
            ItemType.Staff: models.ModsPair(ModsModels.StaffHead, ModsModels.StaffWrapping),
            ItemType.Sword: models.ModsPair(ModsModels.SwordPommel, ModsModels.SwordHilt),
            ItemType.Wand: models.ModsPair(None, ModsModels.WandWrapping),
        }

        self.DamageRanges: dict[ItemType, dict[int, models.IntRange]] = {
            ItemType.Axe: {
                0:  models.IntRange(6, 12),
                1:  models.IntRange(6, 12),
                2:  models.IntRange(6, 14),
                3:  models.IntRange(6, 17),
                4:  models.IntRange(6, 19),
                5:  models.IntRange(6, 22),
                6:  models.IntRange(6, 24),
                7:  models.IntRange(6, 25),
                8:  models.IntRange(6, 27),
                9:  models.IntRange(6, 28),
            },
            
            ItemType.Bow: {
                0:  models.IntRange(9, 13),
                1:  models.IntRange(9, 14),
                2:  models.IntRange(10, 16),
                3:  models.IntRange(11, 18),
                4:  models.IntRange(12, 20),
                5:  models.IntRange(13, 22),
                6:  models.IntRange(14, 25),
                7:  models.IntRange(14, 25),
                8:  models.IntRange(14, 27),
                9:  models.IntRange(14, 28),
            },

            ItemType.Daggers: {
                0:  models.IntRange(4, 8),
                1:  models.IntRange(4, 8),
                2:  models.IntRange(5, 9),
                3:  models.IntRange(5, 11),
                4:  models.IntRange(6, 12),
                5:  models.IntRange(6, 13),
                6:  models.IntRange(7, 14),
                7:  models.IntRange(7, 15),
                8:  models.IntRange(7, 16),
                9:  models.IntRange(7, 17),
            },

            ItemType.Offhand: {
                0:  models.IntRange(6),
                1:  models.IntRange(6),
                2:  models.IntRange(7),
                3:  models.IntRange(8),
                4:  models.IntRange(9),
                5:  models.IntRange(10),
                6:  models.IntRange(11),
                7:  models.IntRange(11),
                8:  models.IntRange(12),
                9:  models.IntRange(12),
            },

            ItemType.Hammer: {
                0:  models.IntRange(11, 15),
                1:  models.IntRange(11, 16),
                2:  models.IntRange(12, 19),
                3:  models.IntRange(14, 22),
                4:  models.IntRange(15, 24),
                5:  models.IntRange(16, 28),
                6:  models.IntRange(17, 30),
                7:  models.IntRange(18, 32),
                8:  models.IntRange(18, 34),
                9:  models.IntRange(19, 35),
            },

            ItemType.Scythe: {
                0:  models.IntRange(8, 17),
                1:  models.IntRange(8, 18),
                2:  models.IntRange(9, 21),
                3:  models.IntRange(10, 24),
                4:  models.IntRange(10, 28),
                5:  models.IntRange(10, 32),
                6:  models.IntRange(10, 35),
                7:  models.IntRange(10, 36),
                8:  models.IntRange(9, 40),
                9:  models.IntRange(9, 41),
            },

            ItemType.Shield: {
                0:  models.IntRange(8),
                1:  models.IntRange(9),
                2:  models.IntRange(10),
                3:  models.IntRange(11),
                4:  models.IntRange(12),
                5:  models.IntRange(13),
                6:  models.IntRange(14),
                7:  models.IntRange(15),
                8:  models.IntRange(16),
                9:  models.IntRange(16),
            },

            ItemType.Spear: {
                0:  models.IntRange(8, 12),
                1:  models.IntRange(8, 13),
                2:  models.IntRange(10, 15),
                3:  models.IntRange(11, 17),
                4:  models.IntRange(11, 19),
                5:  models.IntRange(12, 21),
                6:  models.IntRange(13, 23),
                7:  models.IntRange(13, 25),
                8:  models.IntRange(14, 26),
                9:  models.IntRange(14, 27),
            },

            ItemType.Staff: {
                0:  models.IntRange(7, 11),
                1:  models.IntRange(7, 11),
                2:  models.IntRange(8, 13),
                3:  models.IntRange(9, 14),
                4:  models.IntRange(10, 16),
                5:  models.IntRange(10, 18),
                6:  models.IntRange(10, 19),
                7:  models.IntRange(11, 20),
                8:  models.IntRange(11, 21),
                9:  models.IntRange(11, 22),
            },

            ItemType.Sword: {
                0:  models.IntRange(8, 10),
                1:  models.IntRange(8, 11),
                2:  models.IntRange(9, 13),
                3:  models.IntRange(11, 14),
                4:  models.IntRange(12, 16),
                5:  models.IntRange(13, 18),
                6:  models.IntRange(14, 19),
                7:  models.IntRange(14, 20),
                8:  models.IntRange(15, 22),
                9:  models.IntRange(15, 22),
            },

            ItemType.Wand: {
                0:  models.IntRange(7, 11),
                1:  models.IntRange(7, 11),
                2:  models.IntRange(8, 13),
                3:  models.IntRange(9, 14),
                4:  models.IntRange(10, 16),
                5:  models.IntRange(10, 18),
                6:  models.IntRange(11, 19),
                7:  models.IntRange(11, 20),
                8:  models.IntRange(11, 21),
                9:  models.IntRange(11, 22),
            },
        }

        for item_type, damage_ranges in self.DamageRanges.items():
            for i in range(10, 14):
                if i not in damage_ranges:
                    damage_ranges[i] = models.IntRange(damage_ranges[i-1].min, damage_ranges[i-1].max)

        self.ItemType_MetaTypes: dict[ItemType, list[ItemType]] = {
            ItemType.Weapon: [
                ItemType.Axe,
                ItemType.Bow,
                ItemType.Daggers,
                ItemType.Hammer,
                ItemType.Scythe,
                ItemType.Spear,
                ItemType.Staff,
                ItemType.Sword,
                ItemType.Wand
            ],

            ItemType.MartialWeapon: [
                ItemType.Axe,
                ItemType.Bow,
                ItemType.Daggers,
                ItemType.Hammer,
                ItemType.Scythe,
                ItemType.Spear,
                ItemType.Sword
            ],

            ItemType.OffhandOrShield: [
                ItemType.Offhand,
                ItemType.Shield
            ],

            ItemType.EquippableItem: [
                ItemType.Axe,
                ItemType.Bow,
                ItemType.Daggers,
                ItemType.Hammer,
                ItemType.Offhand,
                ItemType.Scythe,
                ItemType.Shield,
                ItemType.Spear,
                ItemType.Staff,
                ItemType.Sword,
                ItemType.Wand
            ],

            ItemType.SpellcastingWeapon: [
                # ItemType.Offhand,
                ItemType.Staff,
                ItemType.Wand
            ],
        }

        self.Caster_Attributes: list[Attribute] = [
            Attribute.FastCasting,
            Attribute.IllusionMagic,
            Attribute.DominationMagic,
            Attribute.InspirationMagic,
            Attribute.BloodMagic,
            Attribute.DeathMagic,
            Attribute.SoulReaping,
            Attribute.Curses,
            Attribute.AirMagic,
            Attribute.EarthMagic,
            Attribute.FireMagic,
            Attribute.WaterMagic,
            Attribute.EnergyStorage,
            Attribute.HealingPrayers,
            Attribute.SmitingPrayers,
            Attribute.ProtectionPrayers,
            Attribute.DivineFavor,
            Attribute.Communing,
            Attribute.RestorationMagic,
            Attribute.ChannelingMagic,
            Attribute.SpawningPower,
        ]
        self.Shield_Attributes: list[Attribute] = [
            Attribute.Strength,
            Attribute.Tactics,
            Attribute.Command,
            Attribute.Motivation,
            Attribute.Leadership,
        ]
        self.Item_Attributes: dict[ItemType, list[Attribute]] = {
            ItemType.Axe: [Attribute.AxeMastery],
            ItemType.Bow: [Attribute.Marksmanship],
            ItemType.Daggers: [Attribute.DaggerMastery],
            ItemType.Hammer: [Attribute.HammerMastery],
            ItemType.Scythe: [Attribute.ScytheMastery],
            ItemType.Shield: self.Shield_Attributes,
            ItemType.Spear: [Attribute.SpearMastery],
            ItemType.Sword: [Attribute.Swordsmanship],
            ItemType.Offhand: self.Caster_Attributes,
            ItemType.Wand: self.Caster_Attributes,
            ItemType.Staff: self.Caster_Attributes,
        }

        self.ScrapedItems: dict[str, ScrapedItem] = {}
        self.Items: models.ItemsByType = models.ItemsByType()
        self.ItemsBySkins: dict[str, list[models.Item]] = {}
        self.Nick_Items: dict[int, models.Item] = {}
        self.Nick_Cycle: list[models.Item] = []

        self.Runes: dict[str, models.Rune] = {}
        self.Runes_by_Profession: dict[Profession, dict[str, models.Rune]] = {}

        # Change to be a dictionary of dictionaries per identifier so we can handle mods like "Fortitude" (Suffix) and "Hale" (Prefix) which share the same identifier
        # We should also be able to get mods with non perfect stats like a +29 health Fortitude mod
        # We need to iterate from the mod with the most modifiers to the least modifiers, specialized to less specialized
        self.Weapon_Mods: dict[str, models.WeaponMod] = {}

        self.Nick_Cycle_Start_Date = datetime.datetime(2009, 4, 20)
        self.Nick_Cycle_Count = 137

        self.Materials: dict[int, models.Material] = {}
        self.Common_Materials: dict[int, models.Material] = {}
        self.Rare_Materials: dict[int, models.Material] = {}
        self.Rare_Weapon_Names = [
                # Dungeon & Elite Area weapons
                    "Astral Staff",
                    "Aureate Blade",
                    "Bone Dragon Staff",
                    "Bonecage Scythe",
                    "Ceremonial Spear",
                    "Cerulean Edge",
                    "Chrysocola Staff",
                    "Clockwork Scythe",
                    "Cobalt Staff",
                    "Crab Claw Maul",
                    "Crystal Flame Staff",
                    "Crystalline Sword",
                    "Demon Fangs",
                    "Demoncrest Spear",
                    "Dhuum's Soul Reaper",
                    "Draconic Scythe",
                    "Dryad Bow",
                    "Eaglecrest Axe",
                    "Embercrest Staff",
                    "Emerald Blade",
                    "Emerald Edge",
                    "Exalted Aegis",
                    "Frog Scepter",
                    "Golden Hammer",
                    "Goldhorn Staff",
                    "Icicle Staff",
                    "Insectoid Scythe",
                    "Insectoid Staff",
                    "Legendary Sword",
                    "Moldavite Staff",
                    "Notched Blade",
                    "Obsidian Edge",
                    "Pronged Fan",
                    "Serpentine Scepter",
                    "Signet Shield",
                    "Silverwing Recurve Bow",
                    "Singing Blade",
                    "Steelhead Scythe",
                    "Storm Daggers",
                    "Stygian Reaver",
                    "Suntouched Staff",
                    "Tentacle Scythe",
                    "Topaz Scepter",
                    "Turquoise Staff",
                    "Violet Edge",
                    "Voltaic Spear",
                    "Wingcrest Maul"
                
                # Available everywhere
                    "Bear's Sloth",
                    "Fox's Greed",
                    "Hog's Gluttony",
                    "Lion's Pride",
                    "Scorpion's Lust",
                    "Scorpion Bow",
                    "Snake's Envy",
                    "Unicorn's Wrath",
                    "Black Hawk's Lust",
                    "Dragon's Envy",
                    "Peacock's Wrath",
                    "Rhino's Sloth",
                    "Spider's Gluttony",
                    "Tiger's Pride",
                    "Wolf's Greed",
                    "Bonecrusher",
                    "Bronze Guardian",
                    "Death's Head",
                    "Heaven's Arch",
                    "Quicksilver",
                    "Storm Ember",
                    "Ominous Aegis",

                    # Only available in Tyria
                    "Bone Idol",
                    "Canthan Targe",
                    "Censor's Icon",
                    "Chimeric Prism",
                    "Ithas Bow",
                    "War Pick",

                    # Only available in Cantha
                    "Dragon Fangs",
                    "Spiritbinder",
                    "Japan 1st Anniversary Shield",

                    # Only available in Elona
                    "Soulbreaker",
                    "Sunspear (weapon)",

                    # Only available in Eye of the North regions
                    "Darksteel Longbow",
                    "Glacial Blade",
                    "Glacial Blades",
                    "Hourglass Staff",
                    "Lesser Etched Sword",
                    "Etched Sword",
                    "Greater Etched Sword",
                    "Arced Blade",
                    "Greater Arced Blade",
                    "Lesser Granite Edge",
                    "Granite Edge",
                    "Greater Granite Edge",
                    "Lesser Stoneblade",
                    "Stoneblade",
                    "Greater Stoneblade" 
                ]

    
    def get_mods_models(self, item_type: ItemType) -> models.ModsPair | None:
        try:
            return self.ModsByItemType[item_type]
        except KeyError:
            return None

    def get_mod_model(self, item_type: ItemType, mod_type: ModType) -> models.ModsModels | None:
        try:
            mods_pair = self.ModsByItemType.get(item_type, None)
            
            if mods_pair:
                return mods_pair.get(mod_type)

        except KeyError:
            return None    
        
        return None
        

    def UpdateLanguage(self, server_language: ServerLanguage):
        for item in self.Items.All:
            item.update_language(server_language)
            
        self.Items.sort_items()
            
        for rune in self.Runes.values():
            rune.update_language(server_language)

        for weapon_mod in self.Weapon_Mods.values():
            weapon_mod.update_language(server_language)
            
        for material in self.Materials.values():
            material.update_language(server_language)

    def Reload(self):        
        self.is_loaded = False
        
        # Load the runes
        self.LoadRunes()

        # Load the weapon mods
        self.LoadWeaponMods()
        
        # Load the items
        self.LoadItems()
        
        # Load the Materials
        self.LoadMaterials()
        
        # Load the scraped items
        self.LoadScrapedItems()
        
        self.is_loaded = True

    def Load(self):
        self.Reload()
        
    def LoadScrapedItems(self):        
        file_directory = os.path.dirname(os.path.abspath(__file__))
        data_directory = os.path.join(file_directory, "data")
        path = os.path.join(data_directory, "scraped_items.json")
        
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                item_data = json.load(f)
            
            scraped_items = {name: ScrapedItem.from_json(data) for name, data in item_data.items()}
            
            ## remove duplicates based on inventory icon and item name
            unique_items = {}
            for (file_name, item) in scraped_items.items():
                key = (item.inventory_icon_url, item.name)
                
                if key not in unique_items:
                    unique_items[key] = (file_name, item)
            
            self.ScrapedItems = {file_name: item for file_name, item in unique_items.values()}
            return self.ScrapedItems
        
        self.ScrapedItems = {}
        return self.ScrapedItems

    def LoadMaterials(self):
        # Load materials from data/materials.json
        file_directory = os.path.dirname(os.path.abspath(__file__))
        data_directory = os.path.join(file_directory, "data")
        path = os.path.join(data_directory, "materials.json")

        ConsoleLog(
            "LootEx", f"Loading materials...", Console.MessageType.Debug)

        if not os.path.exists(data_directory):
            os.makedirs(data_directory)

        if not os.path.exists(path):
            with open(path, 'w', encoding='utf-8') as file:
                file.write('{}')

        with open(path, 'r', encoding='utf-8') as file:
            materials = json.load(file)

            for value in materials.values():
                material = models.Material.from_json(value)
                self.Materials[material.model_id] = material

        self.Materials = dict(sorted(self.Materials.items(), key=lambda item: (item[1].name)))
        
        self.Common_Materials = {
            model_id: material for model_id, material in self.Materials.items() if material.material_type == models.MaterialType.Common}
        
        self.Rare_Materials = {
            model_id: material for model_id, material in self.Materials.items() if material.material_type == models.MaterialType.Rare}
        
    def SaveMaterials(self):
        # Save materials to data/materials.json
        file_directory = os.path.dirname(os.path.abspath(__file__))
        data_directory = os.path.join(file_directory, "data")
        path = os.path.join(data_directory, "materials.json")

        if not os.path.exists(data_directory):
            os.makedirs(data_directory)

        with open(path, 'w', encoding='utf-8') as file:
            ConsoleLog(
                "LootEx", f"Saving materials ...", Console.MessageType.Debug)
            json.dump({material.model_id: material.to_json()
                    for material in self.Materials.values()}, file, indent=4, ensure_ascii=False)

    def LoadWeaponMods(self):
        # Load weapon mods from data/weapon_mods.json
        file_directory = os.path.dirname(os.path.abspath(__file__))
        data_directory = os.path.join(file_directory, "data")
        path = os.path.join(data_directory, "weapon_mods.json")

        ConsoleLog(
            "LootEx", f"Loading weapon mods from {path}...", Console.MessageType.Debug)

        if not os.path.exists(data_directory):
            os.makedirs(data_directory)

        if not os.path.exists(path):
            with open(path, 'w', encoding='utf-8') as file:
                file.write('{}')

        with open(path, 'r', encoding='utf-8') as file:
            weapon_mods = json.load(file)

            if weapon_mods:  
                for value in weapon_mods.values():
                    mod = models.WeaponMod.from_json(value)
                    
                    if not mod.identifier in self.Weapon_Mods:
                        self.Weapon_Mods[mod.identifier] = mod

        account_file = os.path.join(Console.get_projects_path(), "Widgets", "Config", "DataCollection", GLOBAL_CACHE.Player.GetAccountEmail(), "weapon_mods.json")
        if os.path.exists(account_file):
            with open(account_file, 'r', encoding='utf-8') as file:
                weapon_mods = json.load(file)
                
                if weapon_mods:               
                    for value in weapon_mods.values():
                        mod = models.WeaponMod.from_json(value)
                        
                        if not mod.identifier in self.Weapon_Mods:
                            self.Weapon_Mods[mod.identifier] = mod
                        else:
                            # If the mod already exists, we can update it
                            self.Weapon_Mods[mod.identifier].update(mod)

        # sort the weapon mods by mod.mod_type, then by name
        self.Weapon_Mods = dict(sorted(self.Weapon_Mods.items(), key=lambda item: (item[1].mod_type, item[1].name)))

    def get_data_collection_directory(self) -> str:
        from Widgets.frenkey.LootEx.settings import Settings
        settings = Settings()
        
        return settings.data_collection_path
    
    def SaveWeaponMods(self, shared_file: bool = False, mods: Optional[dict[str, models.WeaponMod]] = None):
        # Save weapon mods to data/weapon_mods.json
        file_directory = os.path.dirname(os.path.abspath(__file__))
        data_directory = os.path.join(file_directory, "data")

        if not shared_file:
            account_name = GLOBAL_CACHE.Player.GetAccountEmail()
            data_directory = os.path.join(self.get_data_collection_directory(), account_name)

        path = os.path.join(data_directory, "weapon_mods.json")


        if not os.path.exists(data_directory):
            os.makedirs(data_directory)

        if not shared_file:
            if mods is not None:
                mods = dict(sorted(mods.items(), key=lambda item: item[0]))
        else:
            mods = self.Weapon_Mods

        if mods is None:
            ConsoleLog(
                "LootEx", "No weapon mods to save.", Console.MessageType.Warning)
            return
        
        with open(path, 'w', encoding='utf-8') as file:
            ConsoleLog(
                "LootEx", f"Saving weapon mods ...", Console.MessageType.Debug)
            json.dump({mod.identifier: mod.to_json()
                    for mod in mods.values()}, file, indent=4, ensure_ascii=False)


    def LoadRunes(self):
        # Load runes from data/runes.json
        file_directory = os.path.dirname(os.path.abspath(__file__))
        data_directory = os.path.join(file_directory, "data")
        path = os.path.join(data_directory, "runes.json")

        ConsoleLog(
            "LootEx", f"Loading runes ...", Console.MessageType.Debug)

        if not os.path.exists(data_directory):
            os.makedirs(data_directory)

        if not os.path.exists(path):
            with open(path, 'w', encoding='utf-8') as file:
                file.write('{}')

        with open(path, 'r', encoding='utf-8') as file:
            runes = json.load(file)

            for value in runes.values():
                rune = models.Rune.from_json(value)
                self.Runes[rune.identifier] = rune
        
        self.Runes = dict(sorted(self.Runes.items(), key=lambda item: (item[1].profession, item[1].mod_type, item[1].rarity.value, item[1].name)))

        for rune in self.Runes.values():
            if rune.profession not in self.Runes_by_Profession:
                self.Runes_by_Profession[rune.profession] = {}

            self.Runes_by_Profession[rune.profession][rune.identifier] = rune

        for profession in self.Runes_by_Profession:
            self.Runes_by_Profession[profession] = dict(sorted(self.Runes_by_Profession[profession].items(), key=lambda item: (item[1].mod_type, item[1].rarity.value, item[1].name)))


    def SaveRunes(self, debug : bool = False):
        # Save runes to data/runes.json
        file_directory = os.path.dirname(os.path.abspath(__file__))
        data_directory = os.path.join(file_directory, "data")    
        path = os.path.join(data_directory, "runes.json")


        if not os.path.exists(data_directory):
            os.makedirs(data_directory)

        with open(path, 'w', encoding='utf-8') as file:
            if debug:
                ConsoleLog(
                    "LootEx", f"Saving runes ...", Console.MessageType.Debug)
                
            json.dump({rune.identifier: rune.to_json() for rune in self.Runes.values()}, file, indent=4, ensure_ascii=False)

    def LoadItems(self):
        # Load items from data/items.json
        file_directory = os.path.dirname(os.path.abspath(__file__))
        data_directory = os.path.join(file_directory, "data")
        path = os.path.join(data_directory, "items.json")

        ConsoleLog(
            "LootEx", f"Loading items...", Console.MessageType.Debug)

        if not os.path.exists(data_directory):
            os.makedirs(data_directory)

        if not os.path.exists(path):
            with open(path, 'w', encoding='utf-8') as file:
                file.write('{}')

        with open(path, 'r', encoding='utf-8') as file:
            self.Items = models.ItemsByType.from_dict(json.load(file))

        account_file = os.path.join(self.get_data_collection_directory(), GLOBAL_CACHE.Player.GetAccountEmail(), "items.json")
        if os.path.exists(account_file):
            with open(account_file, 'r', encoding='utf-8') as file:
                account_items = models.ItemsByType.from_dict(json.load(file))
                
                for item_type, items in account_items.items():
                    if item_type not in self.Items:
                        self.Items[item_type] = {}
                        
                    for model_id, item in items.items():
                        item.is_account_data = True
                        
                        if model_id not in self.Items[item_type]:
                            self.Items.add_item(item)
                        else:
                            self.Items[item_type][model_id].update(item)
              
              
        local_path = os.path.join(Console.get_projects_path(), "Widgets", "Config", "LootEx", "items.json")
        if os.path.exists(local_path):
            with open(local_path, 'r', encoding='utf-8') as file:
                local_items = models.ItemsByType.from_dict(json.load(file))
                
                for item_type, items in local_items.items():
                    if item_type not in self.Items:
                        self.Items[item_type] = {}
                        
                    for model_id, item in items.items():
                        item.is_account_data = True
                        
                        if model_id not in self.Items[item_type]:
                            self.Items.add_item(item)
                        else:
                            self.Items[item_type][model_id].update(item)
                            
        self.ItemsBySkins.clear()
        
        self.Items.sort_items()
        nick_items : dict[int, models.Item] = {}
        for item_type, items in self.Items.items():
            for model_id, item in items.items():        
                if item.inventory_icon:
                    if item.inventory_icon not in self.ItemsBySkins:
                        self.ItemsBySkins[item.inventory_icon] = []
                        
                    self.ItemsBySkins[item.inventory_icon].append(item)
                
                if item.is_nick_item and item.nick_index is not None:
                    nick_items[item.nick_index] = item
        
        
        self.Nick_Cycle = [nick_items[index] for index in range(1, self.Nick_Cycle_Count + 1) if index in nick_items]
        self.Nick_Items = {item.model_id: item for item in self.Nick_Cycle if item.model_id is not None}
        
        
        ConsoleLog(
            "LootEx", f"Loaded {len(self.Items.All)} items ({len(self.Nick_Items)} Nick items).", Console.MessageType.Debug)

    def SaveItems(self, shared_file: bool = False, items: Optional[models.ItemsByType] = None):
        # Save items to data/items.json
        file_directory = os.path.dirname(os.path.abspath(__file__))
        data_directory = os.path.join(file_directory, "data")
        
        account_name = GLOBAL_CACHE.Player.GetAccountEmail()
        account_directory = os.path.join(self.get_data_collection_directory(), account_name)
    
        data_directory = account_directory if shared_file else data_directory

        path = os.path.join(data_directory, "items.json")

        if not os.path.exists(data_directory):
            os.makedirs(data_directory)

        if not shared_file:
            if items is not None:
                items.sort_items()

        else:
            items = self.Items
            items.sort_items()

        if items is None:
            return

        for item in items.All:
            items_of_type = self.Items.get(item.item_type, {}) 
            existing_item = items_of_type.get(item.model_id, None)
            
            if existing_item:
                existing_item.update(item)

        json_string = items.to_json()
        with open(path, 'w', encoding='utf-8') as file:
            json.dump(json_string, file, indent=4, ensure_ascii=False)
        
        
        if shared_file:
            local_path = os.path.join(Console.get_projects_path(), "Widgets", "Config", "LootEx", "items.json")
            
            with open(local_path, 'w', encoding='utf-8') as file:
                json.dump(json_string, file, indent=4, ensure_ascii=False)

    def MergeDiffItems(self):
        path = self.get_data_collection_directory()
        
        if path == "":
            return
        
        dirs = os.listdir(path)
        
        items_found = False
        for dir_name in dirs:
            file_path = os.path.join(path, dir_name, "items.json")
            
            if os.path.exists(file_path):                            
                with open(file_path, 'r', encoding='utf-8') as file:                    
                    file_data = json.load(file)
                    file_items = models.ItemsByType.from_dict(file_data)
                    items_found = len(file_items.items()) > 0 or items_found
                    
                    for item_type, items in file_items.items():
                        if item_type not in self.Items:
                            self.Items[item_type] = {}
                            
                        # Iterate through the items in the diff file
                        for model_id, item in items.items():
                            self.Items.add_item(item)
                            
                            name = item.names.get(ServerLanguage.English, None)
                            if name is not None and name != "":
                                if name in self.Rare_Weapon_Names:
                                    item.category = ItemCategory.RareWeapon                                
            
                # Delete the diff file after merging
                os.remove(file_path)
        
        if items_found:
            ConsoleLog(
                "LootEx", f"Saving merged items...", Console.MessageType.Debug)
            self.SaveItems(shared_file=True, items=self.Items)
        
        
        mods_found = False
        for dir_name in dirs:
            file_path = os.path.join(self.get_data_collection_directory(), dir_name, "weapon_mods.json")
            
            if os.path.exists(file_path):            
                with open(file_path, 'r', encoding='utf-8') as file:
                    # ConsoleLog(
                    #     "LootEx", f"Merging diff items from {file_path}...", Console.MessageType.Debug)
                    
                    mods = json.load(file)
                    mods_found = len(mods.values()) > 0 or mods_found
                    
                    for value in mods.values():
                        mod = models.WeaponMod.from_json(value)
                        
                        if mod.identifier not in self.Weapon_Mods:
                            self.Weapon_Mods[mod.identifier] = mod
                        else:
                            # If the item already exists, we can update it
                            self.Weapon_Mods[mod.identifier].update(mod)
            
                # Delete the diff file after merging
                os.remove(file_path)
        if mods_found:
            self.SaveWeaponMods(shared_file=True, mods=self.Weapon_Mods)