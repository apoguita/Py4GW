import Py4GW
import PyImGui

from Py4GWCoreLib import ColorPalette, get_texture_for_model
from Py4GWCoreLib import IconsFontAwesome5
from Py4GWCoreLib import ImGui
from Py4GWCoreLib import LootConfig
from Py4GWCoreLib import ModelID
from Py4GWCoreLib import UIManager
from Py4GWCoreLib import Utils
from Widgets.InvPlus.GUI_Helpers import (Frame, game_toggle_button, _get_parent_hash)

#region LootGroups
LootGroups = {
    "Alcohol": {
        "1 Points": [
            ModelID.Bottle_Of_Rice_Wine,
            ModelID.Bottle_Of_Vabbian_Wine,
            ModelID.Dwarven_Ale,
            ModelID.Eggnog,
            ModelID.Hard_Apple_Cider,
            ModelID.Hunters_Ale,
            ModelID.Shamrock_Ale,
            ModelID.Vial_Of_Absinthe,
            ModelID.Witchs_Brew,
            ModelID.Zehtukas_Jug,
        ],
        "3 Points": [
            ModelID.Aged_Dwarven_Ale,
            ModelID.Bottle_Of_Grog,
            ModelID.Krytan_Brandy,
            ModelID.Spiked_Eggnog,
        ],
        "50 Points": [
            ModelID.Battle_Isle_Iced_Tea,
        ],
    },
    "Sweets": {
        "1 Points": [
            ModelID.Fruitcake,
            ModelID.Golden_Egg,
            ModelID.Sugary_Blue_Drink,
            ModelID.Honeycomb,
            ModelID.Slice_Of_Pumpkin_Pie,
            ModelID.Wintergreen_Candy_Cane,
            ModelID.Rainbow_Candy_Cane,
        ],
        "2 Points": [
            ModelID.Peppermint_Candy_Cane,
            ModelID.Birthday_Cupcake,
            ModelID.Chocolate_Bunny,
            ModelID.Red_Bean_Cake,
            ModelID.Creme_Brulee,
        ],
        "50 Points": [
            ModelID.Delicious_Cake,
        ],
    },
    "Party": {
        "1 Points": [
            ModelID.Bottle_Rocket,
            ModelID.Champagne_Popper,
            ModelID.Sparkler,
            ModelID.Snowman_Summoner,
        ],
        "2 Points": [
            ModelID.El_Mischievious_Tonic,
            ModelID.El_Yuletide_Tonic,
        ],
        "50 Points": [
            ModelID.Party_Beacon,
        ],
    },
    "Death Penalty Removal": {
        "Lucky Points": [
            ModelID.Four_Leaf_Clover,
        ],
    },
    "Scrolls": {
        "Common XP Scrolls": [
            ModelID.Scroll_Of_Hunters_Insight,
            ModelID.Scroll_Of_Rampagers_Insight,
            ModelID.Scroll_Of_Adventurers_Insight,
        ],
        "Rare XP Scrolls": [
            ModelID.Scroll_Of_Heros_Insight,
            ModelID.Scroll_of_Slayers_Insight,
            ModelID.Scroll_Of_Berserkers_Insight,
        ],
        "Passage Scrolls": [
            ModelID.Passage_Scroll_Deep,
            ModelID.Passage_Scroll_Fow,
            ModelID.Passage_Scroll_Urgoz,
            ModelID.Passage_Scroll_Uw,
        ],
    },
    "Tomes": {
        "Normal Tomes": [
            ModelID.Assassin_Tome,
            ModelID.Dervish_Tome,
            ModelID.Elementalist_Tome,
            ModelID.Mesmer_Tome,
            ModelID.Monk_Tome,
            ModelID.Necromancer_Tome,
            ModelID.Paragon_Tome,
            ModelID.Ranger_Tome,
            ModelID.Ritualist_Tome,
            ModelID.Warrior_Tome,
        ],
        "Elite Tomes": [
            ModelID.Assassin_Elite_Tome,
            ModelID.Dervish_Elite_Tome,
            ModelID.Elementalist_Elite_Tome,
            ModelID.Mesmer_Elite_Tome,
            ModelID.Monk_Elite_Tome,
            ModelID.Necromancer_Elite_Tome,
            ModelID.Paragon_Elite_Tome,
            ModelID.Ranger_Elite_Tome,
            ModelID.Ritualist_Elite_Tome,
            ModelID.Warrior_Elite_Tome,
        ],
    },
    "Keys": {
        "Core Keys": [
            ModelID.Lockpick,
            ModelID.Phantom_Key,
            ModelID.Obsidian_Key,
        ],
        "Prophecies Keys": [
            ModelID.Ascalonian_Key,
            ModelID.Steel_Key,
            ModelID.Krytan_Key,
            ModelID.Maguuma_Key,
            ModelID.Elonian_Key,
            ModelID.Shiverpeak_Key,
            ModelID.Darkstone_Key,
            ModelID.Miners_Key,
        ],
        "Factions Keys": [
            ModelID.Shing_Jea_Key,
            ModelID.Canthan_Key,
            ModelID.Kurzick_Key,
            ModelID.Stoneroot_Key,
            ModelID.Luxon_Key,
            ModelID.Deep_Jade_Key,
            ModelID.Forbidden_Key,
        ],
        "Nightfall Keys": [
            ModelID.Istani_Key,
            ModelID.Kournan_Key,
            ModelID.Vabbian_Key,
            ModelID.Ancient_Elonian_Key,
            ModelID.Margonite_Key,
            ModelID.Demonic_Key,
        ],
    },
    "Materials": {
        "Common Materials": [
            ModelID.Bolt_Of_Cloth,
            ModelID.Bone,
            ModelID.Chitin_Fragment,
            ModelID.Feather,
            ModelID.Granite_Slab,
            ModelID.Iron_Ingot,
            ModelID.Pile_Of_Glittering_Dust,
            ModelID.Plant_Fiber,
            ModelID.Scale,
            ModelID.Tanned_Hide_Square,
            ModelID.Wood_Plank,
        ],
        "Rare Materials": [
            ModelID.Amber_Chunk,
            ModelID.Bolt_Of_Damask,
            ModelID.Bolt_Of_Linen,
            ModelID.Bolt_Of_Silk,
            ModelID.Deldrimor_Steel_Ingot,
            ModelID.Diamond,
            ModelID.Elonian_Leather_Square,
            ModelID.Fur_Square,
            ModelID.Glob_Of_Ectoplasm,
            ModelID.Jadeite_Shard,
            ModelID.Leather_Square,
            ModelID.Lump_Of_Charcoal,
            ModelID.Monstrous_Claw,
            ModelID.Monstrous_Eye,
            ModelID.Monstrous_Fang,
            ModelID.Obsidian_Shard,
            ModelID.Onyx_Gemstone,
            ModelID.Roll_Of_Parchment,
            ModelID.Roll_Of_Vellum,
            ModelID.Ruby,
            ModelID.Sapphire,
            ModelID.Spiritwood_Plank,
            ModelID.Steel_Ingot,
            ModelID.Tempered_Glass_Vial,
            ModelID.Vial_Of_Ink,
        ],
    },
    "Trophies": {
        "A": [
            ModelID.Abnormal_Seed,
            ModelID.Alpine_Seed,
            ModelID.Amphibian_Tongue,
            ModelID.Ancient_Eye,
            ModelID.Ancient_Kappa_Shell,
            ModelID.Animal_Hide,
            ModelID.Archaic_Kappa_Shell,
            ModelID.Ashen_Wurm_Husk,
            ModelID.Augmented_Flesh,
            ModelID.Azure_Crest,
            ModelID.Azure_Remains,
        ],
        "B": [
            ModelID.Baked_Husk,
            ModelID.Beetle_Egg,
            ModelID.Behemoth_Hide,
            ModelID.Behemoth_Jaw,
            ModelID.Berserker_Horn,
            ModelID.Black_Pearl,
            ModelID.Bleached_Carapace,
            ModelID.Bleached_Shell,
            ModelID.Blob_Of_Ooze,
            ModelID.Blood_Drinker_Pelt,
            ModelID.Bog_Skale_Fin,
            ModelID.Bone_Charm,
            ModelID.Bonesnap_Shell,
            ModelID.Branch_Of_Juni_Berries,
            ModelID.Bull_Trainer_Giant_Jawbone,
        ],
        "C": [
            ModelID.Celestial_Essence,
            ModelID.Charr_Carving,
            ModelID.Chromatic_Scale,
            ModelID.Chunk_Of_Drake_Flesh,
            ModelID.Cobalt_Talon,
            ModelID.Copper_Crimson_Skull_Coin,
            ModelID.Copper_Shilling,
            ModelID.Corrosive_Spider_Leg,
            ModelID.Curved_Minotaur_Horn,
        ],
        "D": [
            ModelID.Dark_Claw,
            ModelID.Dark_Flame_Fang,
            ModelID.Dark_Remains,
            ModelID.Decayed_Orr_Emblem,
            ModelID.Demonic_Fang,
            ModelID.Demonic_Relic,
            ModelID.Demonic_Remains,
            ModelID.Dessicated_Hydra_Claw,
            ModelID.Destroyer_Core,
            ModelID.Diamond_Djinn_Essence,
            ModelID.Diessa_Chalice,
            ModelID.Dragon_Root,
            ModelID.Dredge_Charm,
            ModelID.Dredge_Incisor,
            ModelID.Dredge_Manifesto,
            ModelID.Dryder_Web,
            ModelID.Dull_Carapace,
            ModelID.Dune_Burrower_Jaw,
            ModelID.Dusty_Insect_Carapace,
        ],
        "E": [
            ModelID.Ebon_Spider_Leg,
            ModelID.Elder_Kappa_Shell,
            ModelID.Enchanted_Lodestone,
            ModelID.Enchanted_Vine,
            ModelID.Encrusted_Lodestone,
            ModelID.Enslavement_Stone,
        ],
        "F": [
            ModelID.Feathered_Avicara_Scalp,
            ModelID.Feathered_Caromi_Scalp,
            ModelID.Feathered_Crest,
            ModelID.Feathered_Scalp,
            ModelID.Fetid_Carapace,
            ModelID.Fibrous_Mandragor_Root,
            ModelID.Fiery_Crest,
            ModelID.Fledglin_Skree_Wing,
            ModelID.Fleshreaver_Morsel,
            ModelID.Forest_Minotaur_Horn,
            ModelID.Forgotten_Seal,
            ModelID.Forgotten_Trinket_Box,
            ModelID.Frigid_Heart,
            ModelID.Frigid_Mandragor_Husk,
            ModelID.Frosted_Griffon_Wing,
            ModelID.Frostfire_Fang,
            ModelID.Frozen_Remnant,
            ModelID.Frozen_Shell,
            ModelID.Frozen_Wurm_Husk,
            ModelID.Fungal_Root,
        ],
        "G": [
            ModelID.Gargantuan_Jawbone,
            ModelID.Gargoyle_Skull,
            ModelID.Geode,
            ModelID.Ghostly_Remains,
            ModelID.Giant_Tusk,
            ModelID.Glacial_Stone,
            ModelID.Gloom_Seed,
            ModelID.Glowing_Heart,
            ModelID.Gold_Crimson_Skull_Coin,
            ModelID.Gold_Doubloon,
            ModelID.Golden_Rin_Relic,
            ModelID.Golem_Runestone,
            ModelID.Grawl_Necklace,
            ModelID.Gruesome_Ribcage,
            ModelID.Gruesome_Sternum,
            ModelID.Guardian_Moss,
        ],
        "H": [
            ModelID.Hardened_Hump,
            ModelID.Heket_Tongue,
            ModelID.Huge_Jawbone,
            ModelID.Hunting_Minotaur_Horn,
        ],
        "I": [
            ModelID.Iboga_Petal,
            ModelID.Icy_Hump,
            ModelID.Icy_Lodestone,
            ModelID.Igneous_Hump,
            ModelID.Igneous_Spider_Leg,
            ModelID.Immolated_Djinn_Essence,
            ModelID.Incubus_Wing,
            ModelID.Inscribed_Shard,
            ModelID.Insect_Appendage,
            ModelID.Insect_Carapace,
            ModelID.Intricate_Grawl_Necklace,
            ModelID.Iridescent_Griffon_Wing,
            ModelID.Ivory_Troll_Tusk,
        ],
        "J": [
            ModelID.Jade_Bracelet,
            ModelID.Jade_Mandible,
            ModelID.Jade_Wind_Orb,
            ModelID.Jotun_Pelt,
            ModelID.Jungle_Skale_Fin,
            ModelID.Jungle_Troll_Tusk,
            ModelID.Juvenile_Termite_Leg,
        ],
        "K": [
            ModelID.Kappa_Hatchling_Shell,
            ModelID.Kappa_Shell,
            ModelID.Keen_Oni_Claw,
            ModelID.Keen_Oni_Talon,
            ModelID.Kirin_Horn,
            ModelID.Kournan_Pendant,
            ModelID.Krait_Skin,
            ModelID.Kraken_Eye,
            ModelID.Kurzick_Bauble,
            ModelID.Kuskale_Claw,
        ],
        "L": [
            ModelID.Lavastrider_Appendage,
            ModelID.Leather_Belt,
            ModelID.Leathery_Claw,
            ModelID.Losaru_Mane,
            ModelID.Luxon_Pendant,
        ],
        "M": [
            ModelID.Maguuma_Mane,
            ModelID.Mahgo_Claw,
            ModelID.Mandragor_Carapace,
            ModelID.Mandragor_Husk,
            ModelID.Mandragor_Root,
            ModelID.Mandragor_Swamproot,
            ModelID.Mantid_Pincer,
            ModelID.Mantid_Ungula,
            ModelID.Mantis_Pincer,
            ModelID.Margonite_Mask,
            ModelID.Massive_Jawbone,
            ModelID.Mergoyle_Skull,
            ModelID.Minotaur_Horn,
            ModelID.Modniir_Mane,
            ModelID.Molten_Claw,
            ModelID.Molten_Eye,
            ModelID.Molten_Heart,
            ModelID.Mossy_Mandible,
            ModelID.Mountain_Root,
            ModelID.Mountain_Troll_Tusk,
            ModelID.Moon_Shell,
            ModelID.Mummy_Wrapping,
            ModelID.Mursaat_Token,
        ],
        "N": [
            ModelID.Naga_Hide,
            ModelID.Naga_Pelt,
            ModelID.Naga_Skin,
        ],
        "O": [
            ModelID.Obsidian_Burrower_Jaw,
            ModelID.Oni_Claw,
            ModelID.Oni_Talon,
            ModelID.Ornate_Grawl_Necklace,
        ],
        "P": [
            ModelID.Patch_of_Simian_Fur,
            ModelID.Phantom_Residue,
            ModelID.Pile_Of_Elemental_Dust,
            ModelID.Plague_Idol,
            ModelID.Pulsating_Growth,
            ModelID.Putrid_Cyst,
        ],
        "Q": [
            ModelID.Quetzal_Crest,
        ],
        "R": [
            ModelID.Rawhide_Belt,
            ModelID.Red_Iris_Flower,
            ModelID.Rinkhal_Talon,
            ModelID.Roaring_Ether_Claw,
            ModelID.Rot_Wallow_Tusk,
            ModelID.Ruby_Djinn_Essence,
        ],
        "S": [
            ModelID.Shadowy_Husk,
            ModelID.Shadowy_Remnants,
            ModelID.Shiverpeak_Mane,
            ModelID.Shriveled_Eye,
            ModelID.Silver_Bullion_Coin,
            ModelID.Silver_Crimson_Skull_Coin,
            ModelID.Singed_Gargoyle_Skull,
            ModelID.Skale_Claw,
            ModelID.Skale_Fang,
            ModelID.Skale_Fin,
            ModelID.Skale_Fin_PreSearing,
            ModelID.Skale_Tooth,
            ModelID.Skeletal_Limb,
            ModelID.Skeleton_Bone,
            ModelID.Skelk_Claw,
            ModelID.Skelk_Fang,
            ModelID.Skree_Wing,
            ModelID.Skull_Juju,
            ModelID.Smoking_Remains,
            ModelID.Soul_Stone,
            ModelID.Spider_Leg,
            ModelID.Spiked_Crest,
            ModelID.Spiny_Seed,
            ModelID.Stolen_Provisions,
            ModelID.Stolen_Supplies,
            ModelID.Stone_Carving,
            ModelID.Stone_Claw,
            ModelID.Stone_Grawl_Necklace,
            ModelID.Stone_Horn,
            ModelID.Stone_Summit_Badge,
            ModelID.Stone_Summit_Emblem,
            ModelID.Stormy_Eye,
            ModelID.Superb_Charr_Carving,
        ],
        "T": [
            ModelID.Tangled_Seed,
            ModelID.Thorny_Carapace,
            ModelID.Topaz_Crest,
            ModelID.Truffle,
        ],
        "U": [
            ModelID.Umbral_Eye,
            ModelID.Umbral_Shell,
            ModelID.Umbral_Skeletal_Limb,
            ModelID.Unctuous_Remains,
            ModelID.Undead_Bone,
            ModelID.Unnatural_Seed,
        ],
        "V": [
            ModelID.Vaettir_Essence,
            ModelID.Vampiric_Fang,
            ModelID.Venerable_Mantid_Pincer,
            ModelID.Vermin_Hide,
        ],
        "W": [
            ModelID.War_Supplies,
            ModelID.Warden_Horn,
            ModelID.Water_Djinn_Essence,
            ModelID.Weaver_Leg,
            ModelID.White_Mantle_Badge,
            ModelID.White_Mantle_Emblem,
            ModelID.Worn_Belt,
        ],
    },
    "Reward Trophies": {
        "Prophecies": [
            ModelID.Confessors_Orders,
        ],
        "Nightfall": [
            ModelID.Torment_Gemstone,
            ModelID.Margonite_Gemstone,
            ModelID.Stygian_Gemstone,
            ModelID.Titan_Gemstone,
        ],
        "Eye Of North": [
            ModelID.Deldrimor_Armor_Remnant,
            ModelID.Cloth_Of_The_Brotherhood,
        ],
        "Winds Of Change": [
            ModelID.Ministerial_Commendation,
        ],
        "Special Events": [
            ModelID.Lunar_Token,
            ModelID.Blessing_Of_War,
            ModelID.Victory_Token,
            ModelID.Wayfarer_Mark,
            ModelID.Candy_Cane_Shard,
            ModelID.Glob_Of_Frozen_Ectoplasm,
            ModelID.Trick_Or_Treat_Bag,
        ],
    },
    "Quest Items": {
        "Map Pieces": [
            ModelID.Map_Piece_Bottom_Left,
            ModelID.Map_Piece_Bottom_Right,
            ModelID.Map_Piece_Top_Left,
            ModelID.Map_Piece_Top_Right,
        ],
        "Dungeon quest items": [
            ModelID.Spectral_Crystal,
            ModelID.Shimmering_Essence,
            ModelID.Arcane_Crystal_Shard,
            ModelID.Exquisite_Surmia_Carving,
            ModelID.Hammer_of_Kathandrax,
            ModelID.Prismatic_Gelatinous_Material,
        ],
    },
}

class LootModule:
    def __init__(self, inventory_frame: Frame):
        self.MODULE_NAME = "Loot Config"
        self.inventory_frame = inventory_frame
        self.loot_singleton = LootConfig()
        
    def DrawLootConfig(self):
        global global_vars
        
        content_frame = UIManager.GetChildFrameID(_get_parent_hash(), [0])
        left, top, right, bottom = UIManager.GetFrameCoords(content_frame)
        y_offset = 2
        x_offset = 0
        height = bottom - top + y_offset
        width = right - left + x_offset
        if width < 100:
            width = 100
        if height < 100:
            height = 100
            
        UIManager().DrawFrame(content_frame, Utils.RGBToColor(0, 0, 0, 255))
        

        flags = ( PyImGui.WindowFlags.NoCollapse | 
                PyImGui.WindowFlags.NoTitleBar |
                PyImGui.WindowFlags.NoResize
        )
        PyImGui.push_style_var(ImGui.ImGuiStyleVar.WindowRounding,0.0)
        
        PyImGui.set_next_window_pos(left, top)
        PyImGui.set_next_window_size(width, height)
        
        if PyImGui.begin("Embedded Loot config",True, flags):
           
            PyImGui.push_style_var2(ImGui.ImGuiStyleVar.WindowPadding, 5, 5)
            PyImGui.push_style_var2(ImGui.ImGuiStyleVar.FramePadding, 0, 0)
            
            if PyImGui.button(IconsFontAwesome5.ICON_SAVE + "##save_loot_config", width=25, height=25):
                pass
            PyImGui.show_tooltip("Save Loot Config")
            
            PyImGui.same_line(0,-1)
            PyImGui.text("|")
            PyImGui.same_line(0,-1)
            if PyImGui.button(IconsFontAwesome5.ICON_FILE_EXPORT + "##export_loot_config", width=25, height=25):
                # Reset loot config logic here
                pass
            PyImGui.show_tooltip("Export Loot Config to File")
            
            PyImGui.same_line(0,-1)
            if PyImGui.button(IconsFontAwesome5.ICON_FILE_IMPORT + "##import_loot_config", width=25, height=25):
                # Import loot config logic here
                pass
            PyImGui.show_tooltip("Import Loot Config from File")
            PyImGui.separator()

            state = self.loot_singleton.loot_whites
            color = ColorPalette.GetColor("GW_White")
            if game_toggle_button("##BasicLootFilterWhiteButton","Loot White Items",state, width=20, height=20, color=color):
                self.loot_singleton.loot_whites = not self.loot_singleton.loot_whites
            PyImGui.same_line(0,3)  
            state = self.loot_singleton.loot_blues
            color = ColorPalette.GetColor("GW_Blue")
            if game_toggle_button("##BasicLootFilterBlueButton","Loot Blue Items",state, width=20, height=20, color=color):
                self.loot_singleton.loot_blues = not self.loot_singleton.loot_blues
            PyImGui.same_line(0,3)
            state = self.loot_singleton.loot_purples
            color = ColorPalette.GetColor("GW_Purple")  
            if game_toggle_button("##BasicLootFilterPurpleButton","Loot Purple Items",state, width=20, height=20, color=color):
                self.loot_singleton.loot_purples = not self.loot_singleton.loot_purples
            PyImGui.same_line(0,3)
            state = self.loot_singleton.loot_golds
            color = ColorPalette.GetColor("GW_Gold")
            if game_toggle_button("##BasicLootFilterGoldButton","Loot Gold Items",state, width=20, height=20, color=color):
                self.loot_singleton.loot_golds = not self.loot_singleton.loot_golds
            PyImGui.same_line(0,3)
            state = self.loot_singleton.loot_greens
            color = ColorPalette.GetColor("GW_Green")
            if game_toggle_button("##BasicLootFilterGreenButton","Loot Green Items",state, width=20, height=20, color=color):
                self.loot_singleton.loot_greens = not self.loot_singleton.loot_greens
            PyImGui.same_line(0,3)
            self.loot_singleton.loot_gold_coins = ImGui.toggle_button(IconsFontAwesome5.ICON_COINS + "##BasicLootFilterGoldCoinsButton", self.loot_singleton.loot_gold_coins, width=20, height=20)
            ImGui.show_tooltip("Loot Gold Coins")
            PyImGui.separator()

            if PyImGui.tree_node("Advanced Loot Filters"):
                for group_name, group_items in LootGroups.items():
                    if PyImGui.tree_node(group_name):
                        for subgroup, items in group_items.items():
                            if PyImGui.tree_node(subgroup):
                                if PyImGui.begin_table(f"##table_{group_name}_{subgroup}", 3, PyImGui.TableFlags.Borders | PyImGui.TableFlags.RowBg):
                                    col = 0
                                    for item_model_id in items:
                                        item_texture = get_texture_for_model(item_model_id)
                                        enum_entry = ModelID(item_model_id)
                                        enum_name = ' '.join(word.capitalize() for word in enum_entry.name.split('_'))

                                        PyImGui.table_next_column()
                                        PyImGui.begin_group()

                                        state = self.loot_singleton.IsWhitelisted(item_model_id)
                                        new_state = ImGui.image_toggle_button(
                                            f"##loot_toggle_{item_model_id}",
                                            item_texture,
                                            state,
                                            width=48,
                                            height=48
                                        )

                                        if new_state != state:
                                            if new_state:
                                                self.loot_singleton.AddToWhitelist(item_model_id)
                                            else:
                                                self.loot_singleton.RemoveFromWhitelist(item_model_id)

                                        PyImGui.text_wrapped(enum_name)
                                        PyImGui.end_group()

                                        col += 1
                                        if col % 3 == 0:
                                            PyImGui.table_next_row()
                                    PyImGui.end_table()
                                PyImGui.tree_pop()
                        PyImGui.tree_pop()
                PyImGui.tree_pop()

            
        PyImGui.end() 
        PyImGui.pop_style_var(3)