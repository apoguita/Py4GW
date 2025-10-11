from __future__ import annotations
from typing import List, Tuple
from datetime import date, timedelta


import PyImGui
from Py4GWCoreLib import *

YEARS: List[str] = ["2020", "2021", "2022", "2023", "2024", "2025", "2026", "2027", "2028", "2029", "2030"]

MONTHS = [
    ("January", "Jan"),
    ("February", "Feb"),
    ("March", "Mar"),
    ("April", "Apr"),
    ("May", "May"),
    ("June", "Jun"),
    ("July", "Jul"),
    ("August", "Aug"),
    ("September", "Sep"),
    ("October", "Oct"),
    ("November", "Nov"),
    ("December", "Dec"),
]

#region SPECIAL_EVENTS
EVENTS = {
    "Canthan New Year": {
        "start_date": (1, 31),   # January 31
        "duration_days": 8,
        "colors": {
            "button": (90, 0, 10, 255),
            "button_active": (255, 80, 80, 255),
            "button_hover": (255, 120, 120, 255),
        },
        "dropped_items": [
            ModelID.Bottle_Of_Rice_Wine,
            ModelID.Champagne_Popper,
            ModelID.Lunar_Token,
            ModelID.Sparkler,
            ModelID.Bottle_Rocket,
            ModelID.Crate_Of_Fireworks,
            ModelID.Red_Bean_Cake,
            ModelID.Sugary_Blue_Drink,
        ]
    },
    "Lucky Treats Week": {
        "start_date": (3, 14),
        "duration_days": 8,
        "colors": {
            "button": (0, 90, 10, 255),
            "button_active": (80, 255, 80, 255),
            "button_hover": (120, 255, 120, 255),
        },
        "dropped_items": [
            ModelID.Four_Leaf_Clover,
            ModelID.Shamrock_Ale,
        ]
    },
    "April Fools' Day": {
        "start_date": (4, 1),
        "duration_days": 2,
        "colors": {
            "button": (96, 104, 39, 255),
            "button_active": (248, 255, 0, 255),
            "button_hover": (160, 156, 0, 255),
        },
        "dropped_items": []
    },
    "Sweet Treats Week": {
        "start_date": (4, 10),
        "duration_days": 8,
        "colors": {
            "button": (193, 100, 148, 255),
            "button_active": (255, 150, 200, 255),
            "button_hover": (255, 180, 220, 255),
        },
        "dropped_items": [
            ModelID.Chocolate_Bunny,
            ModelID.Golden_Egg,
        ]
    },
    "Anniversary Celebration": {
        "start_date": (4, 22),
        "duration_days": 15,
        "colors": {
            "button": (188, 100, 30, 255),
            "button_active": (255, 112, 0, 255),
            "button_hover": (255, 193, 145, 255),
        },
        "dropped_items": [
            ModelID.Proof_Of_Legend,
            ModelID.Hard_Apple_Cider,
            ModelID.Hunters_Ale,
            ModelID.Krytan_Brandy,
            ModelID.Battle_Isle_Iced_Tea,
            ModelID.Bottle_Rocket,
            ModelID.Champagne_Popper,
            ModelID.Sparkler,
            ModelID.Party_Beacon,
            ModelID.Birthday_Cupcake,
            ModelID.Honeycomb,
            ModelID.Sugary_Blue_Drink,
            ModelID.Delicious_Cake,
            ModelID.Victory_Token,
        ]
    },
    "Dragon Festival": {
        "start_date": (6, 27),
        "duration_days": 8,
        "colors": {
            "button": (90, 0, 10, 255),
            "button_active": (255, 80, 80, 255),
            "button_hover": (255, 120, 120, 255),
        },
        "dropped_items": [
            ModelID.Bottle_Of_Rice_Wine,
            ModelID.Champagne_Popper,
            ModelID.Flask_Of_Firewater,
            ModelID.Red_Bean_Cake,
            ModelID.Bottle_Rocket,
            ModelID.Creme_Brulee,
            ModelID.Sparkler,
            ModelID.Sugary_Blue_Drink,
            ModelID.Victory_Token,
        ]
    },
    "Wintersday in July": {
        "start_date": (7, 24),
        "duration_days": 8,
        "colors": {
            "button": (119, 166, 186, 255),
            "button_active": (80, 200, 255, 255),
            "button_hover": (120, 220, 255, 255),
        },
        "dropped_items": [
            ModelID.Eggnog,
            ModelID.Frosty_Tonic,
            ModelID.Fruitcake,
            ModelID.Mischievious_Tonic,
            ModelID.Snowman_Summoner,
        ]
    },
    "Wayfarer's Reverie": {
        "start_date": (8, 25),
        "duration_days": 8,
        "colors": {
            "button": (120, 120, 120, 255),
            "button_active": (160, 160, 160, 255),
            "button_hover": (200, 200, 200, 255),
        },
        "dropped_items": [
            ModelID.Wayfarer_Mark
        ]
    },
    "Pirate Week": {
        "start_date": (9, 13),
        "duration_days": 8,
        "colors": {
            "button": (180, 120, 60, 255),
            "button_active": (220, 160, 100, 255),
            "button_hover": (240, 200, 140, 255),
        },
        "dropped_items": [
            ModelID.Bottle_Of_Grog,
        ]
    },
    "Halloween": {
        "start_date": (10, 18),
        "duration_days": 16,
        "colors": {
            "button": (189, 104, 0, 255),
            "button_active": (255, 180, 60, 255),
            "button_hover": (255, 200, 100, 255),
        },
        "dropped_items": [
            ModelID.Trick_Or_Treat_Bag,
            ModelID.Vial_Of_Absinthe,
            ModelID.Witchs_Brew,
            ModelID.Ghost_In_The_Box,
            ModelID.Squash_Serum,
            ModelID.Transmogrifier_Tonic,
            ModelID.Candy_Apple,
            ModelID.Candy_Corn,
            ModelID.Pumpkin_Cookie,
        ]
    },
    "Breast Cancer Awareness Month": {
        "start_date": (10, 1),
        "duration_days": 31,
        "colors": {
            "button": (193, 100, 148, 255),
            "button_active": (255, 140, 200, 255),
            "button_hover": (255, 180, 220, 255),
        },
        "dropped_items": [
            ModelID.Vial_Of_Dye,
        ]
    },
    "Special Treats Week": {
        "start_date": (11, 21),
        "duration_days": 8,
        "colors": {
            "button": (142, 107, 0, 255),
            "button_active": (240, 190, 60, 255),
            "button_hover": (255, 210, 100, 255),
        },
        "dropped_items": [
            ModelID.Hard_Apple_Cider,
            ModelID.Slice_Of_Pumpkin_Pie,
        ]
    },
    "Wintersday": {
        "start_date": (12, 19),
        "duration_days": 13,  # Dec 19–31
        "colors": {
            "button": (119, 166, 186, 255),
            "button_active": (80, 200, 255, 255),
            "button_hover": (120, 220, 255, 255),
        },
        "dropped_items": [
            ModelID.Eggnog,
            ModelID.Frosty_Tonic,
            ModelID.Fruitcake,
            ModelID.Mischievious_Tonic,
            ModelID.Snowman_Summoner,
        ]
    },
    "Wintersday-end": {
        "start_date": (1, 1),
        "duration_days": 2,  # Jan 1–2
        "colors": {
            "button": (119, 166, 186, 255),
            "button_active": (80, 200, 255, 255),
            "button_hover": (120, 220, 255, 255),
        },
        "dropped_items": [
            ModelID.Eggnog,
            ModelID.Frosty_Tonic,
            ModelID.Fruitcake,
            ModelID.Mischievious_Tonic,
            ModelID.Snowman_Summoner,
        ]
    },
}

#region nick cycle

#region PVE_WEEKLY_BONUSES
PVE_WEEKLY_BONUSES: list[dict] = [
    {
        "name": "Extra Luck Bonus",
        "description": "Keys and lockpicks drop at 4× the usual rate and double Lucky/Unlucky points.",
        "colors": {
            "button": (255, 215, 0, 255),
            "button_active": (255, 230, 80, 255),
            "button_hover": (255, 240, 120, 255),
        },
    },
    {
        "name": "Elonian Support Bonus",
        "description": "Double Sunspear and Lightbringer points.",
        "colors": {
            "button": (255, 160, 0, 255),
            "button_active": (255, 190, 60, 255),
            "button_hover": (255, 210, 100, 255),
        },
    },
    {
        "name": "Zaishen Bounty Bonus",
        "description": "Double copper Zaishen Coin rewards for Zaishen bounties.",
        "colors": {
            "button": (200, 255, 200, 255),
            "button_active": (220, 255, 220, 255),
            "button_hover": (240, 255, 240, 255),
        },
    },
    {
        "name": "Factions Elite Bonus",
        "description": "The Deep and Urgoz’s Warren can be entered from Kaineng Center.",
        "colors": {
            "button": (160, 200, 255, 255),
            "button_active": (190, 220, 255, 255),
            "button_hover": (210, 240, 255, 255),
        },
    },
    {
        "name": "Northern Support Bonus",
        "description": "Double Asura, Deldrimor, Ebon Vanguard, and Norn reputation points.",
        "colors": {
            "button": (120, 255, 180, 255),
            "button_active": (160, 255, 200, 255),
            "button_hover": (200, 255, 220, 255),
        },
    },
    {
        "name": "Zaishen Mission Bonus",
        "description": "Double copper Zaishen Coin rewards for Zaishen missions.",
        "colors": {
            "button": (200, 200, 255, 255),
            "button_active": (220, 220, 255, 255),
            "button_hover": (240, 240, 255, 255),
        },
    },
    {
        "name": "Pantheon Bonus",
        "description": "Free passage to the Underworld and the Fissure of Woe.",
        "colors": {
            "button": (255, 120, 200, 255),
            "button_active": (255, 160, 220, 255),
            "button_hover": (255, 190, 230, 255),
        },
    },
    {
        "name": "Faction Support Bonus",
        "description": "Double Kurzick and Luxon title points for faction exchanges.",
        "colors": {
            "button": (120, 200, 255, 255),
            "button_active": (160, 220, 255, 255),
            "button_hover": (200, 240, 255, 255),
        },
    },
    {
        "name": "Zaishen Vanquishing Bonus",
        "description": "Double copper Zaishen Coin rewards for Zaishen vanquishes.",
        "colors": {
            "button": (200, 255, 120, 255),
            "button_active": (220, 255, 160, 255),
            "button_hover": (240, 255, 200, 255),
        },
    },
]

#region PVP_WEEKLY_BONUSES
PVP_WEEKLY_BONUSES: list[dict] = [
    {
        "name": "Random Arenas Bonus",
        "description": "Double Balthazar faction and Gladiator title points in Random Arenas.",
        "colors": {
            "button": (255, 100, 100, 255),
            "button_active": (255, 140, 140, 255),
            "button_hover": (255, 180, 180, 255),
        },
    },
    {
        "name": "Guild Versus Guild Bonus",
        "description": "Double Balthazar faction and Champion title points in GvG.",
        "colors": {
            "button": (120, 120, 255, 255),
            "button_active": (160, 160, 255, 255),
            "button_hover": (200, 200, 255, 255),
        },
    },
    {
        "name": "Competitive Mission Bonus",
        "description": "Double Balthazar and Imperial faction in Jade Quarry & Fort Aspenwood.",
        "colors": {
            "button": (120, 255, 120, 255),
            "button_active": (160, 255, 160, 255),
            "button_hover": (200, 255, 200, 255),
        },
    },
    {
        "name": "Heroes' Ascent Bonus",
        "description": "Double Balthazar faction, Hero points, and chest loot in HA.",
        "colors": {
            "button": (255, 200, 100, 255),
            "button_active": (255, 220, 140, 255),
            "button_hover": (255, 240, 180, 255),
        },
    },
    {
        "name": "Codex Arena Bonus",
        "description": "Double Balthazar faction and Codex title points in Codex Arena.",
        "colors": {
            "button": (180, 120, 255, 255),
            "button_active": (200, 160, 255, 255),
            "button_hover": (220, 200, 255, 255),
        },
    },
    {
        "name": "Alliance Battle Bonus",
        "description": "Double Balthazar and Imperial faction in Alliance Battles.",
        "colors": {
            "button": (255, 140, 0, 255),
            "button_active": (255, 180, 60, 255),
            "button_hover": (255, 200, 100, 255),
        },
    },
]

#region NICHOLAS_CYCLE

NICHOLAS_CYCLE: list[dict] = [
    {
        "week": date(2025, 8, 25),
        "item": "Sapphire Djinn Essence",
        "model_id": ModelID.Sapphire_Djinn_Essence,
        "location": "Resplendent Makuun",
        "region": "Vabbi",
        "campaign": "Nightfall",
        "map_url": "https://wiki.guildwars.com/wiki/File:Nicholas_the_Traveler_Resplendent_Makuun_map.jpg",
    },
    {
        "week": date(2025, 9, 1),
        "item": "Stone Carving",
        "model_id": ModelID.Stone_Carving,
        "location": "Arborstone (explorable area)",
        "region": "Echovald Forest",
        "campaign": "Factions",
        "map_url": "https://wiki.guildwars.com/wiki/File:Nicholas_the_Traveler_Arborstone_(explorable_area)_map.jpg",
    },
    {
        "week": date(2025, 9, 8),
        "item": "Feathered Caromi Scalps",
        "model_id": ModelID.Feathered_Caromi_Scalp,
        "location": "North Kryta Province",
        "region": "Kryta",
        "campaign": "Prophecies",
        "map_url": "https://wiki.guildwars.com/wiki/File:Nicholas_the_Traveler_North_Kryta_Province_map.jpg",
    },
    {
        "week": date(2025, 9, 15),
        "item": "Pillaged Goods",
        "model_id": ModelID.Pillaged_Goods,
        "location": "Holdings of Chokhin",
        "region": "Vabbi",
        "campaign": "Nightfall",
        "map_url": "https://wiki.guildwars.com/wiki/File:Nicholas_the_Traveler_Holdings_of_Chokhin_map.jpg",
    },
    {
        "week": date(2025, 9, 22),
        "item": "Gold Crimson Skull Coin",
        "model_id": ModelID.Gold_Crimson_Skull_Coin,
        "location": "Haiju Lagoon",
        "region": "Shing Jea Island",
        "campaign": "Factions",
        "map_url": "https://wiki.guildwars.com/wiki/File:Nicholas_the_Traveler_Haiju_Lagoon_map.jpg",
    },
    {
        "week": date(2025, 9, 29),
        "item": "Jade Bracelets",
        "model_id": ModelID.Jade_Bracelet,
        "location": "Tahnnakai Temple (explorable area)",
        "region": "Kaineng City",
        "campaign": "Factions",
        "map_url": "https://wiki.guildwars.com/wiki/File:Nicholas_the_Traveler_Tahnnakai_Temple_(explorable_area)_map.jpg",
    },
    {
        "week": date(2025, 10, 6),
        "item": "Minotaur Horns",
        "model_id": ModelID.Minotaur_Horn,
        "location": "Prophet's Path",
        "region": "Crystal Desert",
        "campaign": "Prophecies",
        "map_url": "https://wiki.guildwars.com/wiki/File:Nicholas_the_Traveler_Prophet%27s_Path_map.jpg",
    },
    {
        "week": date(2025, 10, 13),
        "item": "Frosted Griffon Wings",
        "model_id": ModelID.Frosted_Griffon_Wing,
        "location": "Snake Dance",
        "region": "Southern Shiverpeaks",
        "campaign": "Prophecies",
        "map_url": "https://wiki.guildwars.com/wiki/File:Nicholas_the_Traveler_Snake_Dance_map.jpg",
    },
    {
        "week": date(2025, 10, 20),
        "item": "Silver Bullion Coins",
        "model_id": ModelID.Silver_Bullion_Coin,
        "location": "Mehtani Keys",
        "region": "Istan",
        "campaign": "Nightfall",
        "map_url": "https://wiki.guildwars.com/wiki/File:Nicholas_the_Traveler_Mehtani_Keys_map.jpg",
    },
    {
        "week": date(2025, 10, 27),
        "item": "Truffle",
        "model_id": ModelID.Truffle,
        "location": "Morostav Trail",
        "region": "Echovald Forest",
        "campaign": "Factions",
        "map_url": "https://wiki.guildwars.com/wiki/File:Nicholas_the_Traveler_Morostav_Trail_map.jpg",
    },
    {
        "week": date(2025, 11, 3),
        "item": "Skelk Claws",
        "model_id": ModelID.Skelk_Claw,
        "location": "Verdant Cascades",
        "region": "Tarnished Coast",
        "campaign": "Eye of the North",
        "map_url": "https://wiki.guildwars.com/wiki/File:Nicholas_the_Traveler_Verdant_Cascades_map.jpg",
    },
    {
        "week": date(2025, 11, 10),
        "item": "Dessicated Hydra Claws",
        "model_id": ModelID.Dessicated_Hydra_Claw,
        "location": "The Scar",
        "region": "Crystal Desert",
        "campaign": "Prophecies",
        "map_url": "https://wiki.guildwars.com/wiki/File:Nicholas_the_Traveler_The_Scar_map.jpg",
    },
    {
        "week": date(2025, 11, 17),
        "item": "Frigid Hearts",
        "model_id": ModelID.Frigid_Heart,
        "location": "Spearhead Peak",
        "region": "Southern Shiverpeaks",
        "campaign": "Prophecies",
        "map_url": "https://wiki.guildwars.com/wiki/File:Nicholas_the_Traveler_Spearhead_Peak_map.jpg",
    },
    {
        "week": date(2025, 11, 24),
        "item": "Celestial Essences",
        "model_id": ModelID.Celestial_Essence,
        "location": "Nahpui Quarter (explorable area)",
        "region": "Kaineng City",
        "campaign": "Factions",
        "map_url": "https://wiki.guildwars.com/wiki/File:Nicholas_the_Traveler_Nahpui_Quarter_(explorable_area)_map.jpg",
    },
    {
        "week": date(2025, 12, 1),
        "item": "Phantom Residue",
        "model_id": ModelID.Phantom_Residue,
        "location": "Lornar's Pass",
        "region": "Southern Shiverpeaks",
        "campaign": "Prophecies",
        "map_url": "https://wiki.guildwars.com/wiki/File:Nicholas_the_Traveler_Lornar%27s_Pass_map.jpg",
    },
    {
        "week": date(2025, 12, 8),
        "item": "Drake Kabob",
        "model_id": ModelID.Drake_Kabob,
        "location": "Issnur Isles",
        "region": "Istan",
        "campaign": "Nightfall",
        "map_url": "https://wiki.guildwars.com/wiki/File:Nicholas_the_Traveler_Issnur_Isles_map.jpg",
    },
    {
        "week": date(2025, 12, 15),
        "item": "Amber Chunks",
        "model_id": ModelID.Amber_Chunk,
        "location": "Ferndale",
        "region": "Echovald Forest",
        "campaign": "Factions",
        "map_url": "https://wiki.guildwars.com/wiki/File:Nicholas_the_Traveler_Ferndale_map.jpg",
    },
    {
        "week": date(2025, 12, 22),
        "item": "Glowing Hearts",
        "model_id": ModelID.Glowing_Heart,
        "location": "Stingray Strand",
        "region": "Kryta",
        "campaign": "Prophecies",
        "map_url": "https://wiki.guildwars.com/wiki/File:Nicholas_the_Traveler_Stingray_Strand_map.jpg",
    },
    {
        "week": date(2025, 12, 29),
        "item": "Saurian Bones",
        "model_id": ModelID.Saurian_Bone,
        "location": "Riven Earth",
        "region": "Tarnished Coast",
        "campaign": "Eye of the North",
        "map_url": "https://wiki.guildwars.com/wiki/File:Nicholas_the_Traveler_Riven_Earth_map.jpg",
    },
    {
        "week": date(2026, 1, 5),
        "item": "Behemoth Hides",
        "model_id": ModelID.Behemoth_Hide,
        "location": "Wilderness of Bahdza",
        "region": "Vabbi",
        "campaign": "Nightfall",
        "map_url": "https://wiki.guildwars.com/wiki/File:Nicholas_the_Traveler_Wilderness_of_Bahdza_map.jpg",
    },
    {
        "week": date(2026, 1, 12),
        "item": "Luminous Stone",
        "model_id": ModelID.Luminous_Stone,
        "location": "Crystal Overlook",
        "region": "The Desolation",
        "campaign": "Nightfall",
        "map_url": "https://wiki.guildwars.com/wiki/File:Nicholas_the_Traveler_Crystal_Overlook_map.jpg",
    },
    {
        "week": date(2026, 1, 19),
        "item": "Intricate Grawl Necklaces",
        "model_id": ModelID.Intricate_Grawl_Necklace,
        "location": "Witman's Folly",
        "region": "Southern Shiverpeaks",
        "campaign": "Prophecies",
        "map_url": "https://wiki.guildwars.com/wiki/File:Nicholas_the_Traveler_Witman%27s_Folly_map.jpg",
    },
    {
        "week": date(2026, 1, 26),
        "item": "Jadeite Shards",
        "model_id": ModelID.Jadeite_Shard,
        "location": "Shadow's Passage",
        "region": "Kaineng City",
        "campaign": "Factions",
        "map_url": "https://wiki.guildwars.com/wiki/File:Nicholas_the_Traveler_Shadow%27s_Passage_map.jpg",
    },
    {
        "week": date(2026, 2, 2),
        "item": "Gold Doubloon",
        "model_id": ModelID.Gold_Doubloon,
        "location": "Barbarous Shore",
        "region": "Kourna",
        "campaign": "Nightfall",
        "map_url": "https://wiki.guildwars.com/wiki/File:Nicholas_the_Traveler_Barbarous_Shore_map.jpg",
    },
    {
        "week": date(2026, 2, 9),
        "item": "Shriveled Eyes",
        "model_id": ModelID.Shriveled_Eye,
        "location": "Skyward Reach",
        "region": "Crystal Desert",
        "campaign": "Prophecies",
        "map_url": "https://wiki.guildwars.com/wiki/File:Nicholas_the_Traveler_Skyward_Reach_map.jpg",
    },
    {
        "week": date(2026, 2, 16),
        "item": "Icy Lodestones",
        "model_id": ModelID.Icy_Lodestone,
        "location": "Icedome",
        "region": "Southern Shiverpeaks",
        "campaign": "Prophecies",
        "map_url": "https://wiki.guildwars.com/wiki/File:Nicholas_the_Traveler_Icedome_map.jpg",
    },
    {
        "week": date(2026, 2, 23),
        "item": "Keen Oni Talon",
        "model_id": ModelID.Keen_Oni_Talon,
        "location": "Silent Surf",
        "region": "The Jade Sea",
        "campaign": "Factions",
        "map_url": "https://wiki.guildwars.com/wiki/File:Nicholas_the_Traveler_Silent_Surf_map.jpg",
    },
    {
        "week": date(2026, 3, 2),
        "item": "Hardened Humps",
        "model_id": ModelID.Hardened_Hump,
        "location": "Nebo Terrace",
        "region": "Kryta",
        "campaign": "Prophecies",
        "map_url": "https://wiki.guildwars.com/wiki/File:Nicholas_the_Traveler_Nebo_Terrace_map.jpg",
    },
    {
        "week": date(2026, 3, 9),
        "item": "Piles of Elemental Dust",
        "model_id": ModelID.Pile_Of_Elemental_Dust,
        "location": "Drakkar Lake",
        "region": "Far Shiverpeaks",
        "campaign": "Eye of the North",
        "map_url": "https://wiki.guildwars.com/wiki/File:Nicholas_the_Traveler_Drakkar_Lake_map.jpg",
    },
    {
        "week": date(2026, 3, 16),
        "item": "Naga Hides",
        "model_id": ModelID.Naga_Hide,
        "location": "Panjiang Peninsula",
        "region": "Shing Jea Island",
        "campaign": "Factions",
        "map_url": "https://wiki.guildwars.com/wiki/File:Nicholas_the_Traveler_Panjiang_Peninsula_map.jpg",
    },
    {
        "week": date(2026, 3, 23),
        "item": "Spiritwood Planks",
        "model_id": ModelID.Spiritwood_Plank,
        "location": "Griffon's Mouth",
        "region": "Northern Shiverpeaks",
        "campaign": "Prophecies",
        "map_url": "https://wiki.guildwars.com/wiki/File:Nicholas_the_Traveler_Griffon%27s_Mouth_map.jpg",
    },
    {
        "week": date(2026, 3, 30),
        "item": "Stormy Eye",
        "model_id": ModelID.Stormy_Eye,
        "location": "Pockmark Flats",
        "region": "Ascalon",
        "campaign": "Prophecies",
        "map_url": "https://wiki.guildwars.com/wiki/File:Nicholas_the_Traveler_Pockmark_Flats_map.jpg",
    },
    {
        "week": date(2026, 4, 6),
        "item": "Skree Wings",
        "model_id": ModelID.Skree_Wing,
        "location": "Forum Highlands",
        "region": "Vabbi",
        "campaign": "Nightfall",
        "map_url": "https://wiki.guildwars.com/wiki/File:Nicholas_the_Traveler_Forum_Highlands_map.jpg",
    },
    {
        "week": date(2026, 4, 13),
        "item": "Soul Stones",
        "model_id": ModelID.Soul_Stone,
        "location": "Raisu Palace (explorable area)",
        "region": "Kaineng City",
        "campaign": "Factions",
        "map_url": "https://wiki.guildwars.com/wiki/File:Nicholas_the_Traveler_Raisu_Palace_(explorable_area)_map.jpg",
    },
    {
        "week": date(2026, 4, 20),
        "item": "Spiked Crest",
        "model_id": ModelID.Spiked_Crest,
        "location": "Tears of the Fallen",
        "region": "Kryta",
        "campaign": "Prophecies",
        "map_url": "https://wiki.guildwars.com/wiki/File:Nicholas_the_Traveler_Tears_of_the_Fallen_map.jpg",
    },
    {
        "week": date(2026, 4, 27),
        "item": "Dragon Root",
        "model_id": ModelID.Dragon_Root,
        "location": "Drazach Thicket",
        "region": "Echovald Forest",
        "campaign": "Factions",
        "map_url": "https://wiki.guildwars.com/wiki/File:Nicholas_the_Traveler_Drazach_Thicket_map.jpg",
    },
    {
        "week": date(2026, 5, 4),
        "item": "Berserker Horns",
        "model_id": ModelID.Berserker_Horn,
        "location": "Jaga Moraine",
        "region": "Far Shiverpeaks",
        "campaign": "Eye of the North",
        "map_url": "https://wiki.guildwars.com/wiki/File:Nicholas_the_Traveler_Jaga_Moraine_map.jpg",
    },
    {
        "week": date(2026, 5, 11),
        "item": "Behemoth Jaw",
        "model_id": ModelID.Behemoth_Jaw,
        "location": "Mamnoon Lagoon",
        "region": "Maguuma Jungle",
        "campaign": "Prophecies",
        "map_url": "https://wiki.guildwars.com/wiki/File:Nicholas_the_Traveler_Mamnoon_Lagoon_map.jpg",
    },
    {
        "week": date(2026, 5, 18),
        "item": "Bowl of Skalefin Soup",
        "model_id": ModelID.Bowl_Of_Skalefin_Soup,
        "location": "Zehlon Reach",
        "region": "Istan",
        "campaign": "Nightfall",
        "map_url": "https://wiki.guildwars.com/wiki/File:Nicholas_the_Traveler_Zehlon_Reach_map.jpg",
    },
    {
        "week": date(2026, 5, 25),
        "item": "Forest Minotaur Horns",
        "model_id": ModelID.Forest_Minotaur_Horn,
        "location": "Kessex Peak",
        "region": "Kryta",
        "campaign": "Prophecies",
        "map_url": "https://wiki.guildwars.com/wiki/File:Nicholas_the_Traveler_Kessex_Peak_map.jpg",
    },
    {
        "week": date(2026, 6, 1),
        "item": "Putrid Cysts",
        "model_id": ModelID.Putrid_Cyst,
        "location": "Sunjiang District (explorable area)",
        "region": "Kaineng City",
        "campaign": "Factions",
        "map_url": "https://wiki.guildwars.com/wiki/File:Nicholas_the_Traveler_Sunjiang_District_(explorable_area)_map.jpg",
    },
    {
        "week": date(2026, 6, 8),
        "item": "Jade Mandibles",
        "model_id": ModelID.Jade_Mandible,
        "location": "Salt Flats",
        "region": "Crystal Desert",
        "campaign": "Prophecies",
        "map_url": "https://wiki.guildwars.com/wiki/File:Nicholas_the_Traveler_Salt_Flats_map.jpg",
    },
    {
        "week": date(2026, 6, 15),
        "item": "Maguuma Manes",
        "model_id": ModelID.Maguuma_Mane,
        "location": "Silverwood",
        "region": "Maguuma Jungle",
        "campaign": "Prophecies",
        "map_url": "https://wiki.guildwars.com/wiki/File:Nicholas_the_Traveler_Silverwood_map.jpg",
    },
    {
        "week": date(2026, 6, 22),
        "item": "Skull Juju",
        "model_id": ModelID.Skull_Juju,
        "location": "The Eternal Grove (explorable area)",
        "region": "Echovald Forest",
        "campaign": "Factions",
        "map_url": "https://wiki.guildwars.com/wiki/File:Nicholas_the_Traveler_The_Eternal_Grove_(explorable_area)_map.jpg",
    },
    {
        "week": date(2026, 6, 29),
        "item": "Mandragor Swamproots",
        "model_id": ModelID.Mandragor_Swamproot,
        "location": "Lahtenda Bog",
        "region": "Istan",
        "campaign": "Nightfall",
        "map_url": "https://wiki.guildwars.com/wiki/File:Nicholas_the_Traveler_Lahtenda_Bog_map.jpg",
    },
    {
        "week": date(2026, 7, 6),
        "item": "Bottle of Vabbian Wine",
        "model_id": ModelID.Bottle_Of_Vabbian_Wine,
        "location": "Vehtendi Valley",
        "region": "Vabbi",
        "campaign": "Nightfall",
        "map_url": "https://wiki.guildwars.com/wiki/File:Nicholas_the_Traveler_Vehtendi_Valley_map.jpg",
    },
    {
        "week": date(2026, 7, 13),
        "item": "Weaver Legs",
        "model_id": ModelID.Weaver_Leg,
        "location": "Magus Stones",
        "region": "Tarnished Coast",
        "campaign": "Eye of the North",
        "map_url": "https://wiki.guildwars.com/wiki/File:Nicholas_the_Traveler_Magus_Stones_map.jpg",
    },
    {
        "week": date(2026, 7, 20),
        "item": "Topaz Crest",
        "model_id": ModelID.Topaz_Crest,
        "location": "Diviner's Ascent",
        "region": "Crystal Desert",
        "campaign": "Prophecies",
        "map_url": "https://wiki.guildwars.com/wiki/File:Nicholas_the_Traveler_Diviner%27s_Ascent_map.jpg",
    },
    {
        "week": date(2026, 7, 27),
        "item": "Rot Wallow Tusks",
        "model_id": ModelID.Rot_Wallow_Tusk,
        "location": "Pongmei Valley",
        "region": "Kaineng City",
        "campaign": "Factions",
        "map_url": "https://wiki.guildwars.com/wiki/File:Nicholas_the_Traveler_Pongmei_Valley_map.jpg",
    },
    {
        "week": date(2026, 8, 3),
        "item": "Frostfire Fangs",
        "model_id": ModelID.Frostfire_Fang,
        "location": "Anvil Rock",
        "region": "Northern Shiverpeaks",
        "campaign": "Prophecies",
        "map_url": "https://wiki.guildwars.com/wiki/File:Nicholas_the_Traveler_Anvil_Rock_map.jpg",
    },
    {
        "week": date(2026, 8, 10),
        "item": "Demonic Relic",
        "model_id": ModelID.Demonic_Relic,
        "location": "The Ruptured Heart",
        "region": "The Desolation",
        "campaign": "Nightfall",
        "map_url": "https://wiki.guildwars.com/wiki/File:Nicholas_the_Traveler_The_Ruptured_Heart_map.jpg",
    },
    {
        "week": date(2026, 8, 17),
        "item": "Abnormal Seeds",
        "model_id": ModelID.Abnormal_Seed,
        "location": "Talmark Wilderness",
        "region": "Kryta",
        "campaign": "Prophecies",
        "map_url": "https://wiki.guildwars.com/wiki/File:Nicholas_the_Traveler_Talmark_Wilderness_map.jpg",
    },
    {
        "week": date(2026, 8, 24),
        "item": "Diamond Djinn Essence",
        "model_id": ModelID.Diamond_Djinn_Essence,
        "location": "The Hidden City of Ahdashim",
        "region": "Vabbi",
        "campaign": "Nightfall",
        "map_url": "https://wiki.guildwars.com/wiki/File:Nicholas_the_Traveler_The_Hidden_City_of_Ahdashim_map.jpg",
    },
    {
        "week": date(2026, 8, 31),
        "item": "Forgotten Seals",
        "model_id": ModelID.Forgotten_Seal,
        "location": "Vulture Drifts",
        "region": "Crystal Desert",
        "campaign": "Prophecies",
        "map_url": "https://wiki.guildwars.com/wiki/File:Nicholas_the_Traveler_Vulture_Drifts_map.jpg",
    },
    {
        "week": date(2026, 9, 7),
        "item": "Copper Crimson Skull Coins",
        "model_id": ModelID.Copper_Crimson_Skull_Coin,
        "location": "Kinya Province",
        "region": "Shing Jea Island",
        "campaign": "Factions",
        "map_url": "https://wiki.guildwars.com/wiki/File:Nicholas_the_Traveler_Kinya_Province_map.jpg",
    },
    {
        "week": date(2026, 9, 14),
        "item": "Mossy Mandibles",
        "model_id": ModelID.Mossy_Mandible,
        "location": "Ettin's Back",
        "region": "Maguuma Jungle",
        "campaign": "Prophecies",
        "map_url": "https://wiki.guildwars.com/wiki/File:Nicholas_the_Traveler_Ettin%27s_Back_map.jpg",
    },
    {
        "week": date(2026, 9, 21),
        "item": "Enslavement Stones",
        "model_id": ModelID.Enslavement_Stone,
        "location": "Grenth's Footprint",
        "region": "Southern Shiverpeaks",
        "campaign": "Prophecies",
        "map_url": "https://wiki.guildwars.com/wiki/File:Nicholas_the_Traveler_Grenth%27s_Footprint_map.jpg",
    },
    {
        "week": date(2026, 9, 28),
        "item": "Elonian Leather Squares",
        "model_id": ModelID.Elonian_Leather_Square,
        "location": "Jahai Bluffs",
        "region": "Kourna",
        "campaign": "Nightfall",
        "map_url": "https://wiki.guildwars.com/wiki/File:Nicholas_the_Traveler_Jahai_Bluffs_map.jpg",
    },
    {
        "week": date(2026, 10, 5),
        "item": "Cobalt Talons",
        "model_id": ModelID.Cobalt_Talon,
        "location": "Vehjin Mines",
        "region": "Vabbi",
        "campaign": "Nightfall",
        "map_url": "https://wiki.guildwars.com/wiki/File:Nicholas_the_Traveler_Vehjin_Mines_map.jpg",
    },
    {
        "week": date(2026, 10, 12),
        "item": "Maguuma Spider Web",
        "model_id": ModelID.Maguuma_Spider_Web,
        "location": "Reed Bog",
        "region": "Maguuma Jungle",
        "campaign": "Prophecies",
        "map_url": "https://wiki.guildwars.com/wiki/File:Nicholas_the_Traveler_Reed_Bog_map.jpg",
    },
    {
        "week": date(2026, 10, 19),
        "item": "Forgotten Trinket Boxes",
        "model_id": ModelID.Forgotten_Trinket_Box,
        "location": "Minister Cho's Estate (explorable area)",
        "region": "Shing Jea Island",
        "campaign": "Factions",
        "map_url": "https://wiki.guildwars.com/wiki/File:Nicholas_the_Traveler_Minister_Cho%27s_Estate_(explorable_area)_map.jpg",
    },
    {
        "week": date(2026, 10, 26),
        "item": "Icy Humps",
        "model_id": ModelID.Icy_Hump,
        "location": "Iron Horse Mine",
        "region": "Northern Shiverpeaks",
        "campaign": "Prophecies",
        "map_url": "https://wiki.guildwars.com/wiki/File:Nicholas_the_Traveler_Iron_Horse_Mine_map.jpg",
    },
    {
        "week": date(2026, 11, 2),
        "item": "Sandblasted Lodestone",
        "model_id": ModelID.Sandblasted_Lodestone,
        "location": "The Shattered Ravines",
        "region": "The Desolation",
        "campaign": "Nightfall",
        "map_url": "https://wiki.guildwars.com/wiki/File:Nicholas_the_Traveler_The_Shattered_Ravines_map.jpg",
    },
    {
        "week": date(2026, 11, 9),
        "item": "Black Pearls",
        "model_id": ModelID.Black_Pearl,
        "location": "Archipelagos",
        "region": "The Jade Sea",
        "campaign": "Factions",
        "map_url": "https://wiki.guildwars.com/wiki/File:Nicholas_the_Traveler_Archipelagos_map.jpg",
    },
    {
        "week": date(2026, 11, 16),
        "item": "Insect Carapaces",
        "model_id": ModelID.Insect_Carapace,
        "location": "Marga Coast",
        "region": "Kourna",
        "campaign": "Nightfall",
        "map_url": "https://wiki.guildwars.com/wiki/File:Nicholas_the_Traveler_Marga_Coast_map.jpg",
    },
    {
        "week": date(2026, 11, 23),
        "item": "Mergoyle Skulls",
        "model_id": ModelID.Mergoyle_Skull,
        "location": "Watchtower Coast",
        "region": "Kryta",
        "campaign": "Prophecies",
        "map_url": "https://wiki.guildwars.com/wiki/File:Nicholas_the_Traveler_Watchtower_Coast_map.jpg",
    },
    {
        "week": date(2026, 11, 30),
        "item": "Decayed Orr Emblems",
        "model_id": ModelID.Decayed_Orr_Emblem,
        "location": "Cursed Lands",
        "region": "Kryta",
        "campaign": "Prophecies",
        "map_url": "https://wiki.guildwars.com/wiki/File:Nicholas_the_Traveler_Cursed_Lands_map.jpg",
    },
    {
        "week": date(2026, 12, 7),
        "item": "Tempered Glass Vials",
        "model_id": ModelID.Tempered_Glass_Vial,
        "location": "Mourning Veil Falls",
        "region": "Echovald Forest",
        "campaign": "Factions",
        "map_url": "https://wiki.guildwars.com/wiki/File:Nicholas_the_Traveler_Mourning_Veil_Falls_map.jpg",
    },
    {
        "week": date(2026, 12, 14),
        "item": "Scorched Lodestones",
        "model_id": ModelID.Scorched_Lodestone,
        "location": "Old Ascalon",
        "region": "Ascalon",
        "campaign": "Prophecies",
        "map_url": "https://wiki.guildwars.com/wiki/File:Nicholas_the_Traveler_Old_Ascalon_map.jpg",
    },
    {
        "week": date(2026, 12, 21),
        "item": "Water Djinn Essence",
        "model_id": ModelID.Water_Djinn_Essence,
        "location": "Turai's Procession",
        "region": "The Desolation",
        "campaign": "Nightfall",
        "map_url": "https://wiki.guildwars.com/wiki/File:Nicholas_the_Traveler_Turai%27s_Procession_map.jpg",
    },
    {
        "week": date(2026, 12, 28),
        "item": "Guardian Moss",
        "model_id": ModelID.Guardian_Moss,
        "location": "Maishang Hills",
        "region": "The Jade Sea",
        "campaign": "Factions",
        "map_url": "https://wiki.guildwars.com/wiki/File:Nicholas_the_Traveler_Maishang_Hills_map.jpg",
    },
    {
        "week": date(2027, 1, 4),
        "item": "Dwarven Ales",
        "model_id": ModelID.Dwarven_Ale,
        "location": "The Floodplain of Mahnkelon",
        "region": "Kourna",
        "campaign": "Nightfall",
        "map_url": "https://wiki.guildwars.com/wiki/File:Nicholas_the_Traveler_The_Floodplain_of_Mahnkelon_map.jpg",
    },
    {
        "week": date(2027, 1, 11),
        "item": "Amphibian Tongues",
        "model_id": ModelID.Amphibian_Tongue,
        "location": "Sparkfly Swamp",
        "region": "Tarnished Coast",
        "campaign": "Eye of the North",
        "map_url": "https://wiki.guildwars.com/wiki/File:Nicholas_the_Traveler_Sparkfly_Swamp_map.jpg",
    },
    {
        "week": date(2027, 1, 18),
        "item": "Alpine Seeds",
        "model_id": ModelID.Alpine_Seed,
        "location": "Frozen Forest",
        "region": "Southern Shiverpeaks",
        "campaign": "Prophecies",
        "map_url": "https://wiki.guildwars.com/wiki/File:Nicholas_the_Traveler_Frozen_Forest_map.jpg",
    },
    {
        "week": date(2027, 1, 25),
        "item": "Tangled Seeds",
        "model_id": ModelID.Tangled_Seed,
        "location": "Dry Top",
        "region": "Maguuma Jungle",
        "campaign": "Prophecies",
        "map_url": "https://wiki.guildwars.com/wiki/File:Nicholas_the_Traveler_Dry_Top_map.jpg",
    },
    {
        "week": date(2027, 2, 1),
        "item": "Stolen Supplies",
        "model_id": ModelID.Stolen_Supplies,
        "location": "Jaya Bluffs",
        "region": "Shing Jea Island",
        "campaign": "Factions",
        "map_url": "https://wiki.guildwars.com/wiki/File:Nicholas_the_Traveler_Jaya_Bluffs_map.jpg",
    },
    {
        "week": date(2027, 2, 8),
        "item": "Pahnai Salad",
        "model_id": ModelID.Pahnai_Salad,
        "location": "Plains of Jarin",
        "region": "Istan",
        "campaign": "Nightfall",
        "map_url": "https://wiki.guildwars.com/wiki/File:Nicholas_the_Traveler_Plains_of_Jarin_map.jpg",
    },
    {
        "week": date(2027, 2, 15),
        "item": "Vermin Hides",
        "model_id": ModelID.Vermin_Hide,
        "location": "Xaquang Skyway",
        "region": "Kaineng City",
        "campaign": "Factions",
        "map_url": "https://wiki.guildwars.com/wiki/File:Nicholas_the_Traveler_Xaquang_Skyway_map.jpg",
    },
    {
        "week": date(2027, 2, 22),
        "item": "Roaring Ether Heart",
        "model_id": ModelID.Roaring_Ether_Heart,
        "location": "The Mirror of Lyss",
        "region": "Vabbi",
        "campaign": "Nightfall",
        "map_url": "https://wiki.guildwars.com/wiki/File:Nicholas_the_Traveler_The_Mirror_of_Lyss_map.jpg",
    },
    {
        "week": date(2027, 3, 1),
        "item": "Leathery Claws",
        "model_id": ModelID.Leathery_Claw,
        "location": "Ascalon Foothills",
        "region": "Ascalon",
        "campaign": "Prophecies",
        "map_url": "https://wiki.guildwars.com/wiki/File:Nicholas_the_Traveler_Ascalon_Foothills_map.jpg",
    },
    {
        "week": date(2027, 3, 8),
        "item": "Azure Crest",
        "model_id": ModelID.Azure_Crest,
        "location": "Unwaking Waters (explorable area)",
        "region": "The Jade Sea",
        "campaign": "Factions",
        "map_url": "https://wiki.guildwars.com/wiki/File:Nicholas_the_Traveler_Unwaking_Waters_(explorable_area)_map.jpg",
    },
    {
        "week": date(2027, 3, 15),
        "item": "Jotun Pelt",
        "model_id": ModelID.Jotun_Pelt,
        "location": "Bjora Marches",
        "region": "Far Shiverpeaks",
        "campaign": "Eye of the North",
        "map_url": "https://wiki.guildwars.com/wiki/File:Nicholas_the_Traveler_Bjora_Marches_map.jpg",
    },
    {
        "week": date(2027, 3, 22),
        "item": "Heket Tongues",
        "model_id": ModelID.Heket_Tongue,
        "location": "Dejarin Estate",
        "region": "Kourna",
        "campaign": "Nightfall",
        "map_url": "https://wiki.guildwars.com/wiki/File:Nicholas_the_Traveler_Dejarin_Estate_map.jpg",
    },
    {
        "week": date(2027, 3, 29),
        "item": "Mountain Troll Tusks",
        "model_id": ModelID.Mountain_Troll_Tusk,
        "location": "Talus Chute",
        "region": "Southern Shiverpeaks",
        "campaign": "Prophecies",
        "map_url": "https://wiki.guildwars.com/wiki/File:Nicholas_the_Traveler_Talus_Chute_map.jpg",
    },
    {
        "week": date(2027, 4, 5),
        "item": "Vials of Ink",
        "model_id": ModelID.Vial_Of_Ink,
        "location": "Shenzun Tunnels",
        "region": "Kaineng City",
        "campaign": "Factions",
        "map_url": "https://wiki.guildwars.com/wiki/File:Nicholas_the_Traveler_Shenzun_Tunnels_map.jpg",
    },
    {
        "week": date(2027, 4, 12),
        "item": "Kournan Pendants",
        "model_id": ModelID.Kournan_Pendant,
        "location": "Gandara, the Moon Fortress",
        "region": "Kourna",
        "campaign": "Nightfall",
        "map_url": "https://wiki.guildwars.com/wiki/File:Nicholas_the_Traveler_Gandara,_the_Moon_Fortress_map.jpg",
    },
    {
        "week": date(2027, 4, 19),
        "item": "Singed Gargoyle Skulls",
        "model_id": ModelID.Singed_Gargoyle_Skull,
        "location": "Diessa Lowlands",
        "region": "Ascalon",
        "campaign": "Prophecies",
        "map_url": "https://wiki.guildwars.com/wiki/File:Nicholas_the_Traveler_Diessa_Lowlands_map.jpg",
    },
    {
        "week": date(2027, 4, 26),
        "item": "Dredge Incisors",
        "model_id": ModelID.Dredge_Incisor,
        "location": "Melandru's Hope",
        "region": "Echovald Forest",
        "campaign": "Factions",
        "map_url": "https://wiki.guildwars.com/wiki/File:Nicholas_the_Traveler_Melandru%27s_Hope_map.jpg",
    },
    {
        "week": date(2027, 5, 3),
        "item": "Stone Summit Badges",
        "model_id": ModelID.Stone_Summit_Badge,
        "location": "Tasca's Demise",
        "region": "Southern Shiverpeaks",
        "campaign": "Prophecies",
        "map_url": "https://wiki.guildwars.com/wiki/File:Nicholas_the_Traveler_Tasca%27s_Demise_map.jpg",
    },
    {
        "week": date(2027, 5, 10),
        "item": "Krait Skins",
        "model_id": ModelID.Krait_Skin,
        "location": "Arbor Bay",
        "region": "Tarnished Coast",
        "campaign": "Eye of the North",
        "map_url": "https://wiki.guildwars.com/wiki/File:Nicholas_the_Traveler_Arbor_Bay_map.jpg",
    },
    {
        "week": date(2027, 5, 17),
        "item": "Inscribed Shards",
        "model_id": ModelID.Inscribed_Shard,
        "location": "Joko's Domain",
        "region": "The Desolation",
        "campaign": "Nightfall",
        "map_url": "https://wiki.guildwars.com/wiki/File:Nicholas_the_Traveler_Joko%27s_Domain_map.jpg",
    },
    {
        "week": date(2027, 5, 24),
        "item": "Feathered Scalps",
        "model_id": ModelID.Feathered_Scalp,
        "location": "Sunqua Vale",
        "region": "Shing Jea Island",
        "campaign": "Factions",
        "map_url": "https://wiki.guildwars.com/wiki/File:Nicholas_the_Traveler_Sunqua_Vale_map.jpg",
    },
    {
        "week": date(2027, 5, 31),
        "item": "Mummy Wrappings",
        "model_id": ModelID.Mummy_Wrapping,
        "location": "The Sulfurous Wastes",
        "region": "The Desolation",
        "campaign": "Nightfall",
        "map_url": "https://wiki.guildwars.com/wiki/File:Nicholas_the_Traveler_The_Sulfurous_Wastes_map.jpg",
    },
    {
        "week": date(2027, 6, 7),
        "item": "Shadowy Remnants",
        "model_id": ModelID.Shadowy_Remnants,
        "location": "The Black Curtain",
        "region": "Kryta",
        "campaign": "Prophecies",
        "map_url": "https://wiki.guildwars.com/wiki/File:Nicholas_the_Traveler_The_Black_Curtain_map.jpg",
    },
    {
        "week": date(2027, 6, 14),
        "item": "Ancient Kappa Shells",
        "model_id": ModelID.Ancient_Kappa_Shell,
        "location": "The Undercity",
        "region": "Kaineng City",
        "campaign": "Factions",
        "map_url": "https://wiki.guildwars.com/wiki/File:Nicholas_the_Traveler_The_Undercity_map.jpg",
    },
    {
        "week": date(2027, 6, 21),
        "item": "Geode",
        "model_id": ModelID.Geode,
        "location": "Yatendi Canyons",
        "region": "Vabbi",
        "campaign": "Nightfall",
        "map_url": "https://wiki.guildwars.com/wiki/File:Nicholas_the_Traveler_Yatendi_Canyons_map.jpg",
    },
    {
        "week": date(2027, 6, 28),
        "item": "Fibrous Mandragor Roots",
        "model_id": ModelID.Fibrous_Mandragor_Root,
        "location": "Grothmar Wardowns",
        "region": "Charr Homelands",
        "campaign": "Eye of the North",
        "map_url": "https://wiki.guildwars.com/wiki/File:Nicholas_the_Traveler_Grothmar_Wardowns_map.jpg",
    },
    {
        "week": date(2027, 7, 5),
        "item": "Gruesome Ribcages",
        "model_id": ModelID.Gruesome_Ribcage,
        "location": "Dragon's Gullet",
        "region": "Ascalon",
        "campaign": "Prophecies",
        "map_url": "https://wiki.guildwars.com/wiki/File:Nicholas_the_Traveler_Dragon%27s_Gullet_map.jpg",
    },
    {
        "week": date(2027, 7, 12),
        "item": "Kraken Eyes",
        "model_id": ModelID.Kraken_Eye,
        "location": "Boreas Seabed (explorable area)",
        "region": "The Jade Sea",
        "campaign": "Factions",
        "map_url": "https://wiki.guildwars.com/wiki/File:Nicholas_the_Traveler_Boreas_Seabed_(explorable_area)_map.jpg",
    },
    {
        "week": date(2027, 7, 19),
        "item": "Bog Skale Fins",
        "model_id": ModelID.Bog_Skale_Fin,
        "location": "Scoundrel's Rise",
        "region": "Kryta",
        "campaign": "Prophecies",
        "map_url": "https://wiki.guildwars.com/wiki/File:Nicholas_the_Traveler_Scoundrel%27s_Rise_map.jpg",
    },
    {
        "week": date(2027, 7, 26),
        "item": "Sentient Spores",
        "model_id": ModelID.Sentient_Spore,
        "location": "Sunward Marches",
        "region": "Kourna",
        "campaign": "Nightfall",
        "map_url": "https://wiki.guildwars.com/wiki/File:Nicholas_the_Traveler_Sunward_Marches_map.jpg",
    },
    {
        "week": date(2027, 8, 2),
        "item": "Ancient Eyes",
        "model_id": ModelID.Ancient_Eye,
        "location": "Sage Lands",
        "region": "Maguuma Jungle",
        "campaign": "Prophecies",
        "map_url": "https://wiki.guildwars.com/wiki/File:Nicholas_the_Traveler_Sage_Lands_map.jpg",
    },
    {
        "week": date(2027, 8, 9),
        "item": "Copper Shillings",
        "model_id": ModelID.Copper_Shilling,
        "location": "Cliffs of Dohjok",
        "region": "Istan",
        "campaign": "Nightfall",
        "map_url": "https://wiki.guildwars.com/wiki/File:Nicholas_the_Traveler_Cliffs_of_Dohjok_map.jpg",
    },
    {
        "week": date(2027, 8, 16),
        "item": "Frigid Mandragor Husks",
        "model_id": ModelID.Frigid_Mandragor_Husk,
        "location": "Norrhart Domains",
        "region": "Far Shiverpeaks",
        "campaign": "Eye of the North",
        "map_url": "https://wiki.guildwars.com/wiki/File:Nicholas_the_Traveler_Norrhart_Domains_map.jpg",
    },
    {
        "week": date(2027, 8, 23),
        "item": "Bolts of Linen",
        "model_id": ModelID.Bolt_Of_Linen,
        "location": "Traveler's Vale",
        "region": "Northern Shiverpeaks",
        "campaign": "Prophecies",
        "map_url": "https://wiki.guildwars.com/wiki/File:Nicholas_the_Traveler_Traveler%27s_Vale_map.jpg",
    },
    {
        "week": date(2027, 8, 30),
        "item": "Charr Carvings",
        "model_id": ModelID.Charr_Carving,
        "location": "Flame Temple Corridor",
        "region": "Ascalon",
        "campaign": "Prophecies",
        "map_url": "https://wiki.guildwars.com/wiki/File:Nicholas_the_Traveler_Flame_Temple_Corridor_map.jpg",
    },
    {
        "week": date(2027, 9, 6),
        "item": "Red Iris Flowers",
        "model_id": ModelID.Red_Iris_Flower,
        "location": "Regent Valley",
        "region": "Ascalon",
        "campaign": "Prophecies",
        "map_url": "https://wiki.guildwars.com/wiki/File:Nicholas_the_Traveler_Regent_Valley_map.jpg",
    },
    {
        "week": date(2027, 9, 13),
        "item": "Feathered Avicara Scalps",
        "model_id": ModelID.Feathered_Avicara_Scalp,
        "location": "Mineral Springs",
        "region": "Southern Shiverpeaks",
        "campaign": "Prophecies",
        "map_url": "https://wiki.guildwars.com/wiki/File:Nicholas_the_Traveler_Mineral_Springs_map.jpg",
    },
    {
        "week": date(2027, 9, 20),
        "item": "Margonite Masks",
        "model_id": ModelID.Margonite_Mask,
        "location": "Poisoned Outcrops",
        "region": "The Desolation",
        "campaign": "Nightfall",
        "map_url": "https://wiki.guildwars.com/wiki/File:Nicholas_the_Traveler_Poisoned_Outcrops_map.jpg",
    },
    {
        "week": date(2027, 9, 27),
        "item": "Quetzal Crests",
        "model_id": ModelID.Quetzal_Crest,
        "location": "Alcazia Tangle",
        "region": "Tarnished Coast",
        "campaign": "Eye of the North",
        "map_url": "https://wiki.guildwars.com/wiki/File:Nicholas_the_Traveler_Alcazia_Tangle_map.jpg",
    },
    {
        "week": date(2027, 10, 4),
        "item": "Plague Idols",
        "model_id": ModelID.Plague_Idol,
        "location": "Wajjun Bazaar",
        "region": "Kaineng City",
        "campaign": "Factions",
        "map_url": "https://wiki.guildwars.com/wiki/File:Nicholas_the_Traveler_Wajjun_Bazaar_map.jpg",
    },
    {
        "week": date(2027, 10, 11),
        "item": "Azure Remains",
        "model_id": ModelID.Azure_Remains,
        "location": "Dreadnought's Drift",
        "region": "Southern Shiverpeaks",
        "campaign": "Prophecies",
        "map_url": "https://wiki.guildwars.com/wiki/File:Nicholas_the_Traveler_Dreadnought%27s_Drift_map.jpg",
    },
    {
        "week": date(2027, 10, 18),
        "item": "Mandragor Root Cake",
        "model_id": ModelID.Mandragor_Root_Cake,
        "location": "Arkjok Ward",
        "region": "Kourna",
        "campaign": "Nightfall",
        "map_url": "https://wiki.guildwars.com/wiki/File:Nicholas_the_Traveler_Arkjok_Ward_map.jpg",
    },
    {
        "week": date(2027, 10, 25),
        "item": "Mahgo Claw",
        "model_id": ModelID.Mahgo_Claw,
        "location": "Perdition Rock",
        "region": "Ring of Fire Islands",
        "campaign": "Prophecies",
        "map_url": "https://wiki.guildwars.com/wiki/File:Nicholas_the_Traveler_Perdition_Rock_map.jpg",
    },
    {
        "week": date(2027, 11, 1),
        "item": "Mantid Pincers",
        "model_id": ModelID.Mantid_Pincer,
        "location": "Saoshang Trail",
        "region": "Shing Jea Island",
        "campaign": "Factions",
        "map_url": "https://wiki.guildwars.com/wiki/File:Nicholas_the_Traveler_Saoshang_Trail_map.jpg",
    },
    {
        "week": date(2027, 11, 8),
        "item": "Sentient Seeds",
        "model_id": ModelID.Sentient_Seed,
        "location": "Fahranur, The First City",
        "region": "Istan",
        "campaign": "Nightfall",
        "map_url": "https://wiki.guildwars.com/wiki/File:Nicholas_the_Traveler_Fahranur,_The_First_City_map.jpg",
    },
    {
        "week": date(2027, 11, 15),
        "item": "Stone Grawl Necklaces",
        "model_id": ModelID.Stone_Grawl_Necklace,
        "location": "Sacnoth Valley",
        "region": "Charr Homelands",
        "campaign": "Eye of the North",
        "map_url": "https://wiki.guildwars.com/wiki/File:Nicholas_the_Traveler_Sacnoth_Valley_map.jpg",
    },
    {
        "week": date(2027, 11, 22),
        "item": "Herring",
        "model_id": ModelID.Herring,
        "location": "Twin Serpent Lakes",
        "region": "Kryta",
        "campaign": "Prophecies",
        "map_url": "https://wiki.guildwars.com/wiki/File:Nicholas_the_Traveler_Twin_Serpent_Lakes_map.jpg",
    },
    {
        "week": date(2027, 11, 29),
        "item": "Naga Skins",
        "model_id": ModelID.Naga_Skin,
        "location": "Mount Qinkai",
        "region": "The Jade Sea",
        "campaign": "Factions",
        "map_url": "https://wiki.guildwars.com/wiki/File:Nicholas_the_Traveler_Mount_Qinkai_map.jpg",
    },
    {
        "week": date(2027, 12, 6),
        "item": "Gloom Seed",
        "model_id": ModelID.Gloom_Seed,
        "location": "The Falls",
        "region": "Maguuma Jungle",
        "campaign": "Prophecies",
        "map_url": "https://wiki.guildwars.com/wiki/File:Nicholas_the_Traveler_The_Falls_map.jpg",
    },
    {
        "week": date(2027, 12, 13),
        "item": "Charr Hide",
        "model_id": ModelID.Charr_Hide,
        "location": "The Breach",
        "region": "Ascalon",
        "campaign": "Prophecies",
        "map_url": "https://wiki.guildwars.com/wiki/File:Nicholas_the_Traveler_The_Breach_map.jpg",
    },
    {
        "week": date(2027, 12, 20),
        "item": "Ruby Djinn Essence",
        "model_id": ModelID.Ruby_Djinn_Essence,
        "location": "The Alkali Pan",
        "region": "The Desolation",
        "campaign": "Nightfall",
        "map_url": "https://wiki.guildwars.com/wiki/File:Nicholas_the_Traveler_The_Alkali_Pan_map.jpg",
    },
    {
        "week": date(2027, 12, 27),
        "item": "Thorny Carapaces",
        "model_id": ModelID.Thorny_Carapace,
        "location": "Majesty's Rest",
        "region": "Kryta",
        "campaign": "Prophecies",
        "map_url": "https://wiki.guildwars.com/wiki/File:Nicholas_the_Traveler_Majesty%27s_Rest_map.jpg",
    },
    {
        "week": date(2028, 1, 3),
        "item": "Bone Charms",
        "model_id": ModelID.Bone_Charm,
        "location": "Rhea's Crater",
        "region": "The Jade Sea",
        "campaign": "Factions",
        "map_url": "https://wiki.guildwars.com/wiki/File:Nicholas_the_Traveler_Rhea%27s_Crater_map.jpg",
    },
    {
        "week": date(2028, 1, 10),
        "item": "Modniir Manes",
        "model_id": ModelID.Modniir_Mane,
        "location": "Varajar Fells",
        "region": "Far Shiverpeaks",
        "campaign": "Eye of the North",
        "map_url": "https://wiki.guildwars.com/wiki/File:Nicholas_the_Traveler_Varajar_Fells_map.jpg",
    },
    {
        "week": date(2028, 1, 17),
        "item": "Superb Charr Carvings",
        "model_id": ModelID.Superb_Charr_Carving,
        "location": "Dalada Uplands",
        "region": "Charr Homelands",
        "campaign": "Eye of the North",
        "map_url": "https://wiki.guildwars.com/wiki/File:Nicholas_the_Traveler_Dalada_Uplands_map.jpg",
    },
    {
        "week": date(2028, 1, 24),
        "item": "Rolls of Parchment",
        "model_id": ModelID.Roll_Of_Parchment,
        "location": "Zen Daijun (explorable area)",
        "region": "Shing Jea Island",
        "campaign": "Factions",
        "map_url": "https://wiki.guildwars.com/wiki/File:Nicholas_the_Traveler_Zen_Daijun_(explorable_area)_map.jpg",
    },
    {
        "week": date(2028, 1, 31),
        "item": "Roaring Ether Claws",
        "model_id": ModelID.Roaring_Ether_Claw,
        "location": "Garden of Seborhin",
        "region": "Vabbi",
        "campaign": "Nightfall",
        "map_url": "https://wiki.guildwars.com/wiki/File:Nicholas_the_Traveler_Garden_of_Seborhin_map.jpg",
    },
    {
        "week": date(2028, 2, 7),
        "item": "Branches of Juni Berries",
        "model_id": ModelID.Branch_Of_Juni_Berries,
        "location": "Bukdek Byway",
        "region": "Kaineng City",
        "campaign": "Factions",
        "map_url": "https://wiki.guildwars.com/wiki/File:Nicholas_the_Traveler_Bukdek_Byway_map.jpg",
    },
    {
        "week": date(2028, 2, 14),
        "item": "Shiverpeak Manes",
        "model_id": ModelID.Shiverpeak_Mane,
        "location": "Deldrimor Bowl",
        "region": "Northern Shiverpeaks",
        "campaign": "Prophecies",
        "map_url": "https://wiki.guildwars.com/wiki/File:Nicholas_the_Traveler_Deldrimor_Bowl_map.jpg",
    },
    {
        "week": date(2028, 2, 21),
        "item": "Fetid Carapaces",
        "model_id": ModelID.Fetid_Carapace,
        "location": "Eastern Frontier",
        "region": "Ascalon",
        "campaign": "Prophecies",
        "map_url": "https://wiki.guildwars.com/wiki/File:Nicholas_the_Traveler_Eastern_Frontier_map.jpg",
    },
    {
        "week": date(2028, 2, 28),
        "item": "Moon Shells",
        "model_id": ModelID.Moon_Shell,
        "location": "Gyala Hatchery (explorable area)",
        "region": "The Jade Sea",
        "campaign": "Factions",
        "map_url": "https://wiki.guildwars.com/wiki/File:Nicholas_the_Traveler_Gyala_Hatchery_(explorable_area)_map.jpg",
    },
    {
        "week": date(2028, 3, 6),
        "item": "Massive Jawbone",
        "model_id": ModelID.Massive_Jawbone,
        "location": "The Arid Sea",
        "region": "Crystal Desert",
        "campaign": "Prophecies",
        "map_url": "https://wiki.guildwars.com/wiki/File:Nicholas_the_Traveler_The_Arid_Sea_map.jpg",
    },
    {
        "week": date(2028, 3, 13),
        "item": "Chromatic Scale",
        "model_id": ModelID.Chromatic_Scale,
        "location": "Ice Cliff Chasms",
        "region": "Far Shiverpeaks",
        "campaign": "Eye of the North",
        "map_url": "https://wiki.guildwars.com/wiki/File:Nicholas_the_Traveler_Ice_Cliff_Chasms_map.jpg",
    },
    {
        "week": date(2028, 3, 20),
        "item": "Mursaat Tokens",
        "model_id": ModelID.Mursaat_Token,
        "location": "Ice Floe",
        "region": "Southern Shiverpeaks",
        "campaign": "Prophecies",
        "map_url": "https://wiki.guildwars.com/wiki/File:Nicholas_the_Traveler_Ice_Floe_map.jpg",
    },
    {
        "week": date(2028, 3, 27),
        "item": "Sentient Lodestone",
        "model_id": ModelID.Sentient_Lodestone,
        "location": "Bahdok Caverns",
        "region": "Kourna",
        "campaign": "Nightfall",
        "map_url": "https://wiki.guildwars.com/wiki/File:Nicholas_the_Traveler_Bahdok_Caverns_map.jpg",
    },
    {
        "week": date(2028, 4, 3),
        "item": "Jungle Troll Tusks",
        "model_id": ModelID.Jungle_Troll_Tusk,
        "location": "Tangle Root",
        "region": "Maguuma Jungle",
        "campaign": "Prophecies",
        "map_url": "https://wiki.guildwars.com/wiki/File:Nicholas_the_Traveler_Tangle_Root_map.jpg",
    },
    {
        "week": date(2028, 4, 10),
        "item": "Sapphire Djinn Essence",
        "model_id": ModelID.Sapphire_Djinn_Essence,
        "location": "Resplendent Makuun",
        "region": "Vabbi",
        "campaign": "Nightfall",
        "map_url": "https://wiki.guildwars.com/wiki/File:Nicholas_the_Traveler_Resplendent_Makuun_map.jpg",
    },
    {
        "week": date(2028, 4, 17),
        "item": "Stone Carving",
        "model_id": ModelID.Stone_Carving,
        "location": "Arborstone (explorable area)",
        "region": "Echovald Forest",
        "campaign": "Factions",
        "map_url": "https://wiki.guildwars.com/wiki/File:Nicholas_the_Traveler_Arborstone_(explorable_area)_map.jpg",
    },
    {
        "week": date(2028, 4, 24),
        "item": "Feathered Caromi Scalps",
        "model_id": ModelID.Feathered_Caromi_Scalp,
        "location": "North Kryta Province",
        "region": "Kryta",
        "campaign": "Prophecies",
        "map_url": "https://wiki.guildwars.com/wiki/File:Nicholas_the_Traveler_North_Kryta_Province_map.jpg",
    },
]
#endregion

REFERENCE_WEEK = date(2013, 5, 13)  # First Monday after update
ROTATION_START = REFERENCE_WEEK  # baseline for modulo rotation

def get_weekly_bonuses(day: date) -> tuple[dict, dict]:
    """Return (PvE_bonus, PvP_bonus) active for the given date."""
    # Normalize to Monday of this week
    monday = day - timedelta(days=day.weekday())  # Monday start
    if monday < ROTATION_START:
        return PVE_WEEKLY_BONUSES[0], PVP_WEEKLY_BONUSES[0]

    weeks = (monday - ROTATION_START).days // 7

    pve_index = weeks % len(PVE_WEEKLY_BONUSES)
    pvp_index = weeks % len(PVP_WEEKLY_BONUSES)

    return PVE_WEEKLY_BONUSES[pve_index], PVP_WEEKLY_BONUSES[pvp_index]


from datetime import date, timedelta

def expand_cycle_if_needed(day: date) -> None:
    """Expand NICHOLAS_CYCLE in place if 'day' is outside its current range."""
    global NICHOLAS_CYCLE

    if not NICHOLAS_CYCLE:
        return

    num_weeks = len(NICHOLAS_CYCLE)
    shift_days = num_weeks * 7

    first_week = NICHOLAS_CYCLE[0]["week"]
    last_week = NICHOLAS_CYCLE[-1]["week"]

    # If the date is before the first known week → prepend one cycle
    while day < first_week:
        shifted = []
        for entry in NICHOLAS_CYCLE:
            new_entry = entry.copy()
            new_entry["week"] = entry["week"] - timedelta(days=shift_days)
            shifted.append(new_entry)
        NICHOLAS_CYCLE = shifted + NICHOLAS_CYCLE
        first_week = NICHOLAS_CYCLE[0]["week"]

    # If the date is after the last known week → append one cycle
    while day > last_week:
        shifted = []
        for entry in NICHOLAS_CYCLE:
            new_entry = entry.copy()
            new_entry["week"] = entry["week"] + timedelta(days=shift_days)
            shifted.append(new_entry)
        NICHOLAS_CYCLE = NICHOLAS_CYCLE + shifted
        last_week = NICHOLAS_CYCLE[-1]["week"]


def get_nicholas_for_day(day: date) -> dict | None:
    """Return Nicholas dict for any given date, expanding cycle on demand."""
    if not NICHOLAS_CYCLE:
        return None

    # Normalize to Monday
    monday = day - timedelta(days=day.weekday())

    # Ensure dataset covers the requested Monday
    expand_cycle_if_needed(monday)

    # Now find the exact Monday in the dataset
    for entry in NICHOLAS_CYCLE:
        if entry["week"] == monday:
            return entry

    return None






def get_event_for_day(day: date) -> dict | None:
    """Return event dict if 'day' falls within an event's range."""
    for name, info in EVENTS.items():
        start_month, start_day = info["start_date"]
        start = date(day.year, start_month, start_day)
        end = start + timedelta(days=info["duration_days"])
        if start <= day < end:
            return {"name": name, **info}
    return None



class Calendar:
    def __init__(self, current: date | None = None):
        # Default to today if nothing passed
        self.current = current or date.today()

    # -------------------------
    # Basics
    # -------------------------
    def get_current_date(self) -> Tuple[int, int, int]:
        return self.current.year, self.current.month, self.current.day

    def to_string(self) -> str:
        return self.current.strftime("%B %d, %Y")

    def get_year(self) -> str:
        return str(self.current.year)

    def get_month(self) -> str:
        return str(self.current.month)

    def get_month_name(self) -> str:
        return MONTHS[self.current.month - 1][0]

    def get_month_short_name(self) -> str:
        return MONTHS[self.current.month - 1][1]

    def get_month_year(self) -> str:
        return f"{self.get_month_name()} - {self.current.year}"

    def get_short_month_year(self) -> str:
        return f"{self.get_month_short_name()} - {self.current.year}"

    def get_day(self) -> str:
        return str(self.current.day)

    def get_day_of_week(self) -> str:
        return self.current.strftime("%A")

    def get_week_of_month(self) -> int:
        first_day = self.current.replace(day=1)
        adjusted_dom = self.current.day + first_day.weekday()
        return int((adjusted_dom - 1) / 7) + 1
    
    # -------------------------
    # Navigation
    # -------------------------
    def set_date(self, year: int, month: int, day: int):
        self.current = date(year, month, day)

    def reset_date(self):
        self.current = date.today()

    def next_day(self):
        self.current += timedelta(days=1)

    def previous_day(self):
        self.current -= timedelta(days=1)

    def next_month(self):
        year, month = self.current.year, self.current.month
        if month == 12:
            year, month = year + 1, 1
        else:
            month += 1
        self.current = self.current.replace(year=year, month=month, day=1)

    def previous_month(self):
        year, month = self.current.year, self.current.month
        if month == 1:
            year, month = year - 1, 12
        else:
            month -= 1
        self.current = self.current.replace(year=year, month=month, day=1)

    def next_year(self):
        self.current = self.current.replace(year=self.current.year + 1)

    def previous_year(self):
        self.current = self.current.replace(year=self.current.year - 1)
        
    # -------------------------
    # Grid Helpers
    # -------------------------
    def month_grid(self):
        """Return a 2D list representing the current month (weeks × days)."""
        import calendar
        cal = calendar.Calendar(firstweekday=0)  # Sunday=6
        return [
            [d if d.month == self.current.month else None
             for d in week]
            for week in cal.monthdatescalendar(self.current.year, self.current.month)
        ]
        
    # -------------------------
    # Conversions
    # -------------------------
    def iso_format(self) -> str:
        return self.current.isoformat()

    def us_format(self) -> str:
        return self.current.strftime("%m/%d/%Y")

    def eu_format(self) -> str:
        return self.current.strftime("%d/%m/%Y")

    def short_label(self) -> str:
        return self.current.strftime("%d %b %Y")

    def long_label(self) -> str:
        return self.current.strftime("%A, %B %d, %Y")
    
    # -------------------------
    # Utilities
    # -------------------------
    def is_today(self) -> bool:
        return self.current == date.today()

    def is_weekend(self) -> bool:
        return self.current.weekday() >= 5  # 5=Saturday, 6=Sunday

    def days_until(self, other: "Calendar") -> int:
        return (other.current - self.current).days

    # -------------------------
    # Events Integration
    # -------------------------
    def get_events_for_day(self, events_dict: dict) -> Optional[dict]:
        """events_dict format: {year: {month: {day: {"event": str, "link": str}}}}"""
        return (
            events_dict
            .get(self.current.year, {})
            .get(self.current.month, {})
            .get(self.current.day)
        )

    def highlighted(self, events_dict: dict) -> bool:
        return self.get_events_for_day(events_dict) is not None

    # -------------------------
    # Representation & Comparison
    # -------------------------
    def __eq__(self, other: object) -> bool:
        if isinstance(other, Calendar):
            return self.current == other.current
        return NotImplemented

    def __lt__(self, other: object) -> bool:
        if isinstance(other, Calendar):
            return self.current < other.current
        return NotImplemented

    def __repr__(self) -> str:
        return f"Calendar(current={self.current})"

    def __str__(self) -> str:
        return self.to_string()

def toggle_button(label: str, v: bool, width=0, height =0, button_color:Color=Color(0, 0,0,255), hover_color:Color=Color(0, 0,0,255), active_color:Color=Color(0, 0,0,255)) -> bool:
    """
    Purpose: Create a toggle button that changes its state and color based on the current state.
    Args:
        label (str): The label of the button.
        v (bool): The current toggle state (True for on, False for off).
    Returns: bool: The new state of the button after being clicked.
    """
    clicked = False
    
    black = Color(0, 0, 0, 255)
    if button_color == black:
        button_color = Color.from_tuple(ImGui.style.get_color(PyImGui.ImGuiCol.Button))
        
    if hover_color == black:
        hover_color = Color.from_tuple(ImGui.style.get_color(PyImGui.ImGuiCol.ButtonHovered))
        
    if active_color == black:
        active_color = Color.from_tuple(ImGui.style.get_color(PyImGui.ImGuiCol.ButtonActive))

    if v:
        PyImGui.push_style_color(PyImGui.ImGuiCol.Button, active_color.to_tuple_normalized())  # On color
        PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonHovered, hover_color.to_tuple_normalized())  # Hover color
        PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonActive, active_color.to_tuple_normalized())
        if width != 0 and height != 0:
            clicked = PyImGui.button(label, width, height)
        else:
            clicked = PyImGui.button(label)
        PyImGui.pop_style_color(3)
    else:
        if width != 0 and height != 0:
            clicked = PyImGui.button(label, width, height)
        else:
            clicked = PyImGui.button(label)

    if clicked:
        v = not v

    return v


class ToggleButton:
    def __init__(self, label: str, toggled: bool = False, width: int = 30, height: int = 30):
        self.label = label
        self.toggled = toggled
        self.width = width
        self.height = height

    def is_toggled(self) -> bool:
        self.toggled = toggle_button(self.label, self.toggled, width=self.width, height=self.height)
        return self.toggled
    
    def set_toggled(self, state: bool) -> None:
        self.toggled = state
        
        
class Button:
    def __init__(self, label: str, width: int = 30, height: int = 30):
        self.label = label
        self.width = width
        self.height = height

    def draw(self, width: int | None = None, height: int | None = None) -> bool:
        w = width if width is not None else self.width
        h = height if height is not None else self.height
        return PyImGui.button(self.label, w, h)
      
calendar = Calendar()

class ButtonLayout:
    def __init__(self):
        self.button_width = 30
        self.button_height = 30
        self.period_caption = "MONTH - YEAR"

        self.button_day = ToggleButton(f"{IconsFontAwesome5.ICON_CALENDAR_DAY}", toggled=True,
                                       width=self.button_width, height=self.button_height)
        self.button_trimester = ToggleButton(f"{IconsFontAwesome5.ICON_CALENDAR_WEEK}", toggled=False,
                                             width=self.button_width, height=self.button_height)
        self.button_year = ToggleButton(f"{IconsFontAwesome5.ICON_CALENDAR_DAYS}", toggled=False,
                                        width=self.button_width, height=self.button_height)

        self.button_prev = Button(f"{IconsFontAwesome5.ICON_CHEVRON_LEFT}", width=self.button_width, height=self.button_height)
        self.button_next = Button(f"{IconsFontAwesome5.ICON_CHEVRON_RIGHT}", width=self.button_width, height=self.button_height)
        self.button_period = Button(self.period_caption, width=0, height=self.button_height)
        

    def get_active_scope(self) -> str:
        if self.button_day.toggled:
            return "month"
        if self.button_trimester.toggled:
            return "trimester"
        if self.button_year.toggled:
            return "year"
        return "month"

    def update_period_caption(self):
        scope = self.get_active_scope()
        if scope == "month":
            self.period_caption = calendar.get_short_month_year()
        elif scope == "trimester":
            q = (calendar.current.month - 1) // 3 + 1
            self.period_caption = f"Q{q} - {calendar.current.year}"
        elif scope == "year":
            self.period_caption = str(calendar.current.year)
        self.button_period.label = self.period_caption

    def draw(self):
        # Scope toggles
        if self.button_day.is_toggled():
            self.button_trimester.set_toggled(False)
            self.button_year.set_toggled(False)
        ImGui.show_tooltip("Month")
        PyImGui.same_line(0, -1)

        if self.button_trimester.is_toggled():
            self.button_day.set_toggled(False)
            self.button_year.set_toggled(False)
        ImGui.show_tooltip("Trimester")
        PyImGui.same_line(0, -1)

        if self.button_year.is_toggled():
            self.button_day.set_toggled(False)
            self.button_trimester.set_toggled(False)
        ImGui.show_tooltip("Year")
        PyImGui.same_line(0, -1)

        # Prev button
        if self.button_prev.draw():
            scope = self.get_active_scope()
            if scope == "month":
                calendar.previous_month()
            elif scope == "trimester":
                for _ in range(3):
                    calendar.previous_month()
            elif scope == "year":
                calendar.previous_year()

        PyImGui.same_line(0, -1)

        # Period caption
        self.update_period_caption()
        min_width = 100
        PyImGui.push_item_width(min_width)
        if self.button_period.draw(width=min_width):
            Py4GW.Console.Log("Calendar", "Period button clicked.", Py4GW.Console.MessageType.Info)
        PyImGui.pop_item_width()
        ImGui.show_tooltip("Select period")

        PyImGui.same_line(0, -1)
        
        # Next button
        if self.button_next.draw():
            scope = self.get_active_scope()
            if scope == "month":
                calendar.next_month()
            elif scope == "trimester":
                for _ in range(3):
                    calendar.next_month()
            elif scope == "year":
                calendar.next_year()
        

button_layout = ButtonLayout()
calendar = Calendar()



def draw_month(cal: Calendar, width: int = 300, height: int = 265):
    """Draw a single month inside a child so formatting stays intact."""
    child_id = f"month_{cal.current.month}_{cal.current.year}"
    if PyImGui.begin_child(child_id, (width, height), True, PyImGui.WindowFlags.NoFlag):
        # Caption
        PyImGui.text_colored(cal.get_month_year(), ColorPalette.GetColor("yellow").to_tuple_normalized())

        headers = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        if PyImGui.begin_table(f"calendar_table_{child_id}", 7, PyImGui.TableFlags.Borders):
            for h in headers:
                PyImGui.table_setup_column(h)
            PyImGui.table_headers_row()

            grid = cal.month_grid()
            for week in grid:
                PyImGui.table_next_row()
                for day in week:
                    PyImGui.table_next_column()
                    if day is None or day.month != cal.current.month:
                        PyImGui.text("")
                    else:
                        # Event check
                        event = get_event_for_day(day)
                        pve_bonus, pvp_bonus = get_weekly_bonuses(day)
                        nicholas = get_nicholas_for_day(day)
                        colors = event["colors"] if event else None

                        if event and colors:
                            PyImGui.push_style_color(PyImGui.ImGuiCol.Button, tuple(c/255 for c in colors["button"]))
                            PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonHovered, tuple(c/255 for c in colors["button_hover"]))
                            PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonActive, tuple(c/255 for c in colors["button_active"]))

                        if PyImGui.button(str(day.day), 30, 30):
                            calendar.set_date(day.year, day.month, day.day)   # 👈 this makes clicked date active

                            Py4GW.Console.Log("Calendar", f"Clicked raw day: {day}", Py4GW.Console.MessageType.Info)
                            Py4GW.Console.Log("Calendar", f"Global calendar set to: {calendar.current}", Py4GW.Console.MessageType.Info)



                        if event and colors:
                            PyImGui.pop_style_color(3)

                        if PyImGui.is_item_hovered():
                            if PyImGui.begin_tooltip():
                                PyImGui.text(f"{day.strftime('%A, %B %d, %Y')}")
                                if event and colors:
                                    PyImGui.text_colored(f"Event: {event['name']}", tuple(c/255 for c in colors["button_active"]))
                                if pve_bonus:
                                    PyImGui.text(f"PvE Weekly Bonus: {pve_bonus['name']}")
                                if pvp_bonus:
                                    PyImGui.text(f"PvP Weekly Bonus: {pvp_bonus['name']}")
                                if nicholas:  # << NEW tooltip info
                                    PyImGui.separator()
                                    PyImGui.text_colored("Nicholas the Traveler", (200/255, 155/255, 0, 1))
                                    PyImGui.text(f"Item: {nicholas['item']}")
                                else:
                                    PyImGui.text("Nicholas the Traveler: Not visiting this week.")
                                PyImGui.end_tooltip()

            PyImGui.end_table()
    PyImGui.end_child()

def get_script_path_for_model(model: int) -> Optional[str]:
    """
    Resolve the script filename for a given model ID.
    Returns the full path if found, otherwise None.
    """
    base_path = Py4GW.Console.get_projects_path()
    bots_path = os.path.join(base_path, "Bots", "Nicholas the Traveler")

    try:
        for file in os.listdir(bots_path):
            if file.startswith(f"{model}-") and file.endswith(".py"):
                return os.path.join(bots_path, file)
    except Exception as e:
        Py4GW.Console.Log(
            "script loader",
            f"Error scanning for model {model}: {str(e)}",
            Py4GW.Console.MessageType.Error,
        )

    return None

def DrawDayCard():
    selected_day = calendar.current   # 👈 use current calendar date, not today
    current_event = get_event_for_day(selected_day)
    pve_bonus, pvp_bonus = get_weekly_bonuses(selected_day)
    nicholas = get_nicholas_for_day(selected_day)

    # Show the selected date (defaults to today)
    PyImGui.text_colored(f"{calendar.get_day_of_week()}, {selected_day.strftime('%B %d, %Y')}",  ColorPalette.GetColor("yellow").to_tuple_normalized())
    PyImGui.text_colored(f"PvE Bonus:",  ColorPalette.GetColor("gw_gold").to_tuple_normalized())
    PyImGui.same_line(0, -1)
    PyImGui.text(f"{pve_bonus['name']}")
    PyImGui.text_colored(f"PvP Bonus:",  ColorPalette.GetColor("gw_gold").to_tuple_normalized())
    PyImGui.same_line(0, -1)
    PyImGui.text(f"{pvp_bonus['name']}")
    
    if nicholas:
        table_flags = PyImGui.TableFlags.RowBg | PyImGui.TableFlags.BordersOuterH
        if PyImGui.begin_table("Nictable", 2, table_flags):
            iconwidth = 96
            child_width = 300
            child_height = 275
            PyImGui.table_setup_column("Icon", PyImGui.TableColumnFlags.WidthFixed, iconwidth)
            PyImGui.table_setup_column("titles", PyImGui.TableColumnFlags.WidthFixed, child_width - iconwidth)
            PyImGui.table_next_row()
            PyImGui.table_set_column_index(0)
            ImGui.DrawTexture(get_texture_for_item(nicholas["model_id"]), iconwidth, iconwidth)
            PyImGui.table_set_column_index(1)
            if PyImGui.begin_table("Nick Info", 1, PyImGui.TableFlags.NoFlag):
                PyImGui.table_next_row()
                PyImGui.table_set_column_index(0)
                ImGui.push_font("Regular", 20)
                PyImGui.push_style_color(PyImGui.ImGuiCol.Text, ColorPalette.GetColor("yellow").to_tuple_normalized())
                PyImGui.text(f"Nicholas the Traveler")
                PyImGui.pop_style_color(1)
                ImGui.pop_font()
                PyImGui.table_next_row()
                PyImGui.table_set_column_index(0)
                PyImGui.text(f"Item: {nicholas['item']}")
                PyImGui.text(f"Location: {nicholas['location']}")
                PyImGui.text(f"Region: {nicholas['region']}")
                PyImGui.text(f"Campaign: {nicholas['campaign']}")
                if nicholas["map_url"]:
                    if PyImGui.button("View Map"):
                        import webbrowser
                        webbrowser.open(nicholas["map_url"])
                    ImGui.show_tooltip("Open map in browser")
                    farm_script = get_script_path_for_model(nicholas["model_id"])
                    if farm_script:
                        PyImGui.same_line(0, -1)
                        if PyImGui.button("Load Farm"):
                            Py4GW.Console.Log("Calendar", f"Loading farm script: {farm_script}", Py4GW.Console.MessageType.Info)
                            Py4GW.Console.defer_stop_load_and_run(farm_script, 500)
                        ImGui.show_tooltip(f"Load farm script for {nicholas['item']}")

                    
                             
                PyImGui.end_table()
            PyImGui.end_table()

    else:
        PyImGui.text(f"No Nicholas data to show for {selected_day}")

    if current_event:
        colors = current_event["colors"]

        # Draw the button with event name
        PyImGui.text(f"Current Event: {current_event['name']}")
        if "dropped_items" in current_event and current_event["dropped_items"]:
            PyImGui.separator()
            PyImGui.text_colored("Event Drops", (0.8, 0.8, 0.2, 1))  # yellowish

            # --- First row: textures ---
            for i, item in enumerate(current_event["dropped_items"]):
                ImGui.DrawTexture(get_texture_for_item(item), 48, 48)
                if i < len(current_event["dropped_items"]) - 1:
                    PyImGui.same_line(0, 5)  # spacing between textures

            # --- Second row: names ---
            for i, item in enumerate(current_event["dropped_items"]):
                PyImGui.text(str(item.name))
                if i < len(current_event["dropped_items"]) - 1:
                    PyImGui.same_line(0, 40)  # spacing between names (match texture width)

            PyImGui.separator()
    else:
        # No event: just draw a text label
        PyImGui.text("Current Event: - No Event Active")



def DrawWindow() -> None:
    global button_layout, calendar
    window_flags = PyImGui.WindowFlags.AlwaysAutoResize

    if PyImGui.begin("Calendar", window_flags):
        button_layout.draw()
        PyImGui.separator()

        scope = button_layout.get_active_scope()

        if scope == "month":
            draw_month(calendar)

        elif scope == "trimester":
            q = (calendar.current.month - 1) // 3
            start_month = q * 3 + 1
            for i in range(3):
                month_cal = Calendar(date(calendar.current.year, start_month + i, 1))
                draw_month(month_cal)
                if i < 2:
                    PyImGui.same_line(0,-1)

        elif scope == "year":
            for i in range(12):
                month_cal = Calendar(date(calendar.current.year, i + 1, 1))
                draw_month(month_cal)
                if (i + 1) % 4 != 0:  # 4 per row
                    PyImGui.same_line(0,-1)

    PyImGui.end()

def DrawDayWindow():
    if PyImGui.begin("Event Details", PyImGui.WindowFlags.AlwaysAutoResize):
        DrawDayCard()
    PyImGui.end()


def configure():
    pass

def main():
    global bot

    try:
        DrawWindow()
        DrawDayWindow()
        #bot.Update()
        #bot.UI.draw_window()
        
    except Exception as e:
        Py4GW.Console.Log("Calendar", f"Error: {str(e)}", Py4GW.Console.MessageType.Error)
        raise

if __name__ == "__main__":
    main()
