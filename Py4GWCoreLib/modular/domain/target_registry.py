"""
target_registry module

This module is part of the modular runtime surface.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class TargetRegistryKind(str, Enum):
    """
    T ar ge tR eg is tr yK in d class.
    
    Meta:
      Expose: true
      Audience: advanced
      Display: Target Registry Kind
      Purpose: Provide explicit modular runtime behavior and metadata.
      UserDescription: Internal class used by modular orchestration and step execution.
      Notes: Keep behavior explicit and side effects contained.
    """
    NPC = "npc"
    ENEMY = "enemy"
    GADGET = "gadget"


@dataclass(frozen=True)
class AgentTargetDefinition:
    """
    A ge nt Ta rg et De fi ni ti on class.
    
    Meta:
      Expose: true
      Audience: advanced
      Display: Agent Target Definition
      Purpose: Provide explicit modular runtime behavior and metadata.
      UserDescription: Internal class used by modular orchestration and step execution.
      Notes: Keep behavior explicit and side effects contained.
    """
    display_name: str = ""
    encoded_names: tuple[tuple[int, ...], ...] = ()
    model_id: int | None = None


AgentTargetValue = AgentTargetDefinition | tuple[tuple[int, ...], str] | tuple[tuple[tuple[int, ...], ...], str]


NPC_TARGETS: dict[str, AgentTargetValue] = {
    "MERCHANT": ((223, 12, 0, 0), "Merchant"),
    "CRAFTING_MATERIAL_TRADER": (((218, 12, 0, 0),), "Crafting Material Trader"),
    "RARE_MATERIAL_TRADER": (((219, 12, 0, 0),), "Rare Material Trader"),
    "MARYANN_MERCHANT": (((2, 129, 174, 30, 76, 243, 39, 168, 94, 124, 0, 0),), "Maryann [Merchant]"),
    "IDA_MATERIAL_TRADER": (((2, 129, 176, 30, 206, 207, 175, 180, 46, 22, 0, 0),), "Ida [Material Trader]"),
    "ROLAND_RARE_MATERIAL_TRADER": (
        ((2, 129, 177, 30, 121, 158, 107, 174, 125, 37, 0, 0),),
        "Roland [Rare Material Trader]",
    ),
    "ADRIANA_MERCHANT": (((2, 129, 168, 30, 186, 208, 140, 169, 52, 21, 0, 0),), "Adriana [Merchant]"),
    "ANDERS_MATERIAL_TRADER": (((2, 129, 169, 30, 23, 235, 100, 134, 4, 116, 0, 0),), "Anders [Material Trader]"),
    "HELENA_RARE_MATERIAL_TRADER": (
        ((2, 129, 170, 30, 160, 235, 64, 210, 12, 77, 0, 0),),
        "Helena [Rare Material Trader]",
    ),
    "ABJORN_MERCHANT": (((2, 129, 182, 30, 106, 181, 11, 203, 35, 83, 0, 0),), "Abjorn [Merchant]"),
    "VATHI_MATERIAL_TRADER": (((2, 129, 183, 30, 66, 135, 156, 218, 94, 9, 0, 0),), "Vathi [Material Trader]"),
    "BIRNA_RARE_MATERIAL_TRADER": (
        ((2, 129, 184, 30, 4, 141, 74, 238, 47, 64, 0, 0),),
        "Birna [Rare Material Trader]",
    ),
    "LOKAI_MERCHANT": (((1, 129, 198, 63, 103, 215, 156, 210, 48, 50, 0, 0),), "Lokai [Merchant]"),
    "GUUL_MATERIAL_TRADER": (((1, 129, 199, 63, 243, 201, 146, 243, 222, 35, 0, 0),), "Guul [Material Trader]"),
    "NEHGOYO_RARE_MATERIAL_TRADER": (
        ((1, 129, 200, 63, 176, 139, 78, 232, 74, 58, 0, 0),),
        "Nehgoyo [Rare Material Trader]",
    ),
    "RASTIGAN_THE_ETERNAL": (((147, 60, 51, 178, 63, 250, 201, 17, 0, 0),), "Rastigan the Eternal"),
    "ETERNAL_FORGEMASTER": (((149, 60, 95, 250, 204, 193, 241, 13, 0, 0),), "Eternal Forgemaster"),
    "ETERNAL_LORD_TAERES": (((145, 60, 28, 148, 190, 146, 92, 75, 0, 0),), "Eternal Lord Taeres"),
    "ETERNAL_WEAPONSMITH": (((161, 60, 142, 182, 136, 229, 188, 67, 0, 0),), "Eternal Weaponsmith"),
    "KROMRIL_THE_ETERNAL": (((143, 60, 231, 221, 50, 213, 172, 33, 0, 0),), "Kromril the Eternal"),
    "MIKO_THE_UNCHAINED": (((153, 60, 144, 135, 227, 178, 148, 90, 0, 0),), "Miko the Unchained"),
    "NIMROS_THE_HUNTER": (((151, 60, 106, 254, 155, 244, 189, 59, 0, 0),), "Nimros the Hunter"),
    "NIKA": (((203, 94, 0, 243, 160, 248, 38, 109, 0, 0),), "Nika"),
    "FISHMONGER_BIHZUN": (((113, 96, 50, 191, 11, 216, 178, 28, 0, 0),), "Fishmonger Bihzun"),
    "LOUD_KOU": (((213, 95, 115, 159, 143, 243, 151, 49, 0, 0),), "Loud Kou"),
    "ADEPT_NAI": (((173, 76, 22, 253, 52, 170, 169, 27, 0, 0),), "Adept Nai"),
    "CLERK_ARLON": (((1, 129, 97, 37, 185, 181, 231, 129, 86, 119, 0, 0),), "Clerk Arlon"),
    "DINJA": (((1, 129, 61, 75, 24, 159, 133, 218, 48, 105, 0, 0),), "Dinja"),
    "IMPERIAL_GUARDSMAN_LINRO": (((1, 129, 13, 79, 157, 162, 185, 247, 94, 101, 0, 0),), "Imperial Guardsman Linro"),
    "ZENMAI": (((1, 129, 17, 57, 0, 0),), "Zenmai"),
    "CASTELLAN_PUUBA": (((1, 129, 82, 32, 155, 168, 95, 159, 72, 69, 0, 0),), "Castellan Puuba"),
    "FIELD_GENERAL_HAYAO": (((1, 129, 55, 56, 139, 170, 251, 224, 167, 63, 0, 0),), "Field General Hayao"),
    "GENERAL_YURUKARO": (((1, 129, 53, 56, 201, 154, 61, 191, 33, 5, 0, 0),), "General Yurukaro"),
    "FIRST_SPEAR_DEHVAD": (((1, 129, 148, 56, 163, 142, 132, 232, 237, 5, 0, 0),), "First Spear Dehvad"),
    "JEREK": (((1, 129, 134, 56, 31, 183, 97, 252, 255, 51, 0, 0),), "Jerek"),
    "SAVAGE_NUNBE": (((1, 129, 87, 61, 194, 171, 138, 216, 216, 93, 0, 0),), "Savage Nunbe"),
    "CAPTAIN_BESUZ": (((1, 129, 196, 55, 221, 239, 214, 206, 18, 39, 0, 0),), "Captain Besuz"),
    "CAPTAIN_MINDHEBEH": (((1, 129, 6, 61, 236, 175, 29, 193, 178, 124, 0, 0),), "Captain Mindhebeh"),
    "IRONFIST": (((1, 129, 220, 64, 162, 197, 32, 146, 126, 76, 0, 0),), "Ironfist"),
    "LIONGUARD_FIGO": (((1, 129, 252, 78, 235, 179, 236, 223, 85, 52, 0, 0),), "Lionguard Figo"),
    "LIONGUARD_NEIRO": (((1, 129, 238, 1, 30, 225, 94, 182, 64, 96, 0, 0),), "Lionguard Neiro"),
    "LATHAM": (((1, 129, 157, 122, 30, 229, 130, 189, 135, 44, 0, 0),), "Latham"),
    "OLIAS": (((1, 129, 251, 56, 0, 0),), "Olias"),
    "ELDER_SUHL": (((1, 129, 205, 19, 150, 248, 63, 173, 90, 92, 0, 0),), "Elder Suhl"),
    "GENERAL_MORGAHN": (((1, 129, 46, 56, 190, 161, 71, 197, 251, 127, 0, 0),), "General Morgahn"),
    "AHTOK": (((1, 129, 125, 56, 106, 177, 11, 136, 96, 42, 0, 0),), "Ahtok"),
    "KORMIR": (
        (
            (1, 129, 99, 37, 33, 177, 160, 145, 148, 4, 0, 0),
            (1, 129, 126, 61, 72, 165, 95, 227, 251, 120, 0, 0),
        ),
        "Kormir",
    ),
    "ACOLYTE_JIN": (((1, 129, 195, 38, 0, 0),), "Acolyte Jin"),
    "ACOLYTE_SOUSUKE": (((1, 129, 194, 38, 0, 0),), "Acolyte Sousuke"),
    "GOREN": (((1, 129, 223, 56, 0, 0),), "Goren"),
    "KEEPER_OF_SECRETS": (((1, 129, 187, 94, 109, 130, 168, 208, 227, 1, 0, 0),), "Keeper of Secrets"),
    "VOLATISS": (((1, 129, 175, 89, 152, 210, 71, 207, 40, 48, 0, 0),), "Volatiss"),
    "NERASHI": (
        (
            (10, 125, 128, 169, 227, 169, 51, 104, 0, 0),
            (1, 129, 135, 56, 41, 214, 175, 185, 82, 94, 0, 0),
        ),
        "Nerashi",
    ),
    "ROJIS": (
        (
            (1, 129, 120, 56, 134, 201, 165, 210, 151, 62, 0, 0),
            (1, 129, 26, 61, 101, 235, 183, 238, 21, 44, 0, 0),
            (1, 129, 23, 21, 100, 226, 185, 151, 171, 13, 0, 0),
        ),
        "Rojis",
    ),
    "CAPTAIN_BOLDUHR": (((1, 129, 223, 55, 169, 136, 1, 221, 158, 113, 0, 0),), "Captain Bolduhr"),
    "KINYA_KELA": (((1, 129, 51, 56, 53, 211, 16, 247, 22, 3, 0, 0),), "Kinya Kela"),
    "SOGOLON_THE_PROTECTOR": (((1, 129, 130, 56, 100, 249, 67, 233, 153, 83, 0, 0),), "Sogolon the Protector"),
    "ASSISTANT_HAHNNA": (((1, 129, 10, 61, 224, 250, 191, 196, 17, 101, 0, 0),), "Assistant Hahnna"),
    "RAIDMARSHAL_MEHDARA": (((1, 129, 93, 61, 43, 154, 67, 234, 15, 111, 0, 0),), "Raidmarshal Mehdara"),
    "SECOND_SPEAR_BINAH": (((1, 129, 139, 56, 4, 233, 32, 222, 95, 126, 0, 0),), "Second Spear Binah"),
    "ELDER_JONAH": (((222, 124, 49, 200, 101, 210, 82, 76, 0, 0),), "Elder Jonah"),
    "SUNSPEAR_MODIKI": (((1, 129, 182, 77, 117, 165, 42, 248, 57, 37, 0, 0),), "Sunspear Modiki"),
    "ZUDASH_DEJARIN": (((8, 125, 106, 185, 25, 211, 100, 127, 0, 0),), "Zudash Dejarin"),
    "KOSS": (((1, 129, 168, 56, 0, 0),), "Koss"),
    "DUNKORO": (((1, 129, 170, 56, 0, 0),), "Dunkoro"),
    "MARGRID_THE_SLY": (((1, 129, 199, 56, 0, 0),), "Margrid the Sly"),
    "COMMANDER_SUHA": (((1, 129, 126, 19, 204, 138, 149, 185, 75, 106, 0, 0),), "Commander Suha"),
    "LONAI": (((13, 125, 39, 207, 73, 140, 81, 76, 0, 0),), "Lonai"),
    "DOCKMASTER_AHLARO": (((1, 129, 211, 19, 200, 201, 159, 139, 136, 119, 0, 0),), "Dockmaster Ahlaro"),
    "GUARDSMAN_BAHSI": (((1, 129, 216, 19, 10, 130, 127, 237, 98, 18, 0, 0),), "Guardsman Bahsi"),
    "WHISPERS_ADEPT": (((1, 129, 175, 77, 42, 232, 67, 129, 200, 84, 0, 0),), "Whispers Adept"),
    "DEHJAH": (
        (
            (1, 129, 222, 19, 100, 138, 73, 198, 1, 39, 0, 0),
            (1, 129, 204, 64, 81, 207, 108, 155, 124, 56, 0, 0),
            (1, 129, 134, 19, 109, 158, 126, 229, 163, 67, 0, 0),
        ),
        "Dehjah",
    ),
    "DIGMASTER_GATAH": (((1, 129, 75, 61, 216, 254, 39, 174, 146, 96, 0, 0),), "Digmaster Gatah"),
    "DISCIPLE_OF_SECRETS": (
        (
            (1, 129, 108, 20, 70, 247, 250, 158, 75, 26, 0, 0),
            (1, 129, 119, 26, 61, 241, 188, 168, 241, 37, 0, 0),
        ),
        "Disciple of Secrets",
    ),
    "ELDER_DAHUT": (((1, 129, 209, 19, 73, 242, 61, 141, 254, 88, 0, 0),), "Elder Dahut"),
    "ELDER_NAHLO": (((1, 129, 207, 19, 108, 207, 104, 236, 114, 54, 0, 0),), "Elder Nahlo"),
    "KEHANNI": (((1, 129, 3, 14, 68, 210, 88, 190, 229, 34, 0, 0),), "Kehanni"),
    "KUWAME": (((1, 129, 148, 16, 185, 240, 112, 164, 106, 60, 0, 0),), "Kuwame"),
    "PRIESTESS_HAILA": (((1, 129, 122, 19, 88, 233, 41, 194, 182, 25, 0, 0),), "Priestess Haila"),
    "SEEKER_OF_WHISPERS_LIGHTBRINGER_RANKS": (((142, 2, 64, 245, 92, 144, 245, 8, 0, 0),), "Seeker of Whispers [Lightbringer Ranks]"),
    "EVENT_PLANNER_KAZSHA": (((1, 129, 20, 61, 126, 215, 114, 147, 141, 108, 0, 0),), "Event Planner Kazsha"),
    "MESSENGER_OF_LYSSA": (((1, 129, 149, 29, 239, 129, 78, 216, 25, 29, 0, 0),), "Messenger of Lyssa"),
    "EMISSARY_DAJMIR": (((1, 129, 107, 56, 59, 172, 149, 235, 254, 72, 0, 0),), "Emissary Dajmir"),
    "MORGAHN": (((1, 129, 71, 27, 12, 130, 248, 236, 224, 76, 0, 0),), "Morgahn"),
    "ZERAI_THE_LEARNER": (((1, 129, 14, 30, 181, 224, 160, 226, 90, 116, 0, 0),), "Zerai the Learner"),
    "RECORDS_KEEPER_PALIN": (((1, 129, 172, 60, 176, 140, 241, 227, 52, 8, 0, 0),), "Records Keeper Palin"),
    "BUTOH_THE_BOLD": (((1, 129, 47, 33, 177, 163, 89, 240, 197, 52, 0, 0),), "Butoh the Bold"),
    "DREAMER_HAHLA": (((1, 129, 59, 33, 142, 199, 185, 153, 124, 93, 0, 0),), "Dreamer Hahla"),
    "DREAMER_RAJA": (((1, 129, 45, 61, 86, 198, 253, 179, 210, 95, 0, 0),), "Dreamer Raja"),
    "DIRAH_TRAPTAIL": (((1, 129, 69, 33, 45, 248, 105, 168, 69, 37, 0, 0),), "Dirah Traptail"),
    "LAPH_LONGMANE": (((1, 129, 51, 61, 134, 181, 112, 148, 220, 62, 0, 0),), "Laph Longmane"),
    "MIRZA_VELDRUNNER": (((1, 129, 39, 8, 150, 233, 241, 135, 47, 67, 0, 0),), "Mirza Veldrunner"),
    "PALAWA_JOKO": (
        (
            (1, 129, 249, 34, 0, 139, 146, 250, 153, 112, 0, 0),
            (1, 129, 42, 14, 225, 209, 198, 206, 88, 125, 0, 0),
        ),
        "Palawa Joko",
    ),
    "GENERAL_HUDUH": (((1, 129, 250, 34, 135, 239, 31, 174, 122, 43, 0, 0),), "General Huduh"),
    "CAPTAIN_MEHHAN": (
        (
            (1, 129, 136, 36, 216, 219, 37, 230, 110, 127, 0, 0),
            (1, 129, 57, 61, 165, 186, 134, 245, 160, 49, 0, 0),
        ),
        "Captain Mehhan",
    ),
    "PEHAI": (((1, 129, 124, 61, 23, 219, 34, 173, 168, 8, 0, 0),), "Pehai"),
    "JARINDOK": (((1, 129, 63, 61, 46, 173, 250, 185, 254, 99, 0, 0),), "Jarindok"),
    "TORTURED_SUNSPEAR": (((1, 129, 254, 60, 2, 190, 129, 222, 219, 103, 0, 0),), "Tortured Sunspear"),
    "RAHMOR": (((1, 129, 120, 61, 235, 182, 201, 194, 180, 56, 0, 0),), "Rahmor"),
    "KEEPER_HALYSSI": (((1, 129, 122, 61, 241, 211, 196, 200, 145, 120, 0, 0),), "Keeper Halyssi"),
    "SCOUT_AHTOK": (((1, 129, 2, 61, 160, 148, 9, 149, 70, 103, 0, 0),), "Scout Ahtok"),
    "SUNSPEAR_SCOUT": (((1, 129, 192, 71, 144, 187, 17, 211, 164, 104, 0, 0),), "Sunspear Scout"),
    "RUNIC_ORACLE": (((1, 129, 69, 61, 141, 192, 134, 177, 78, 21, 0, 0),), "Runic Oracle"),
    "KEEPER_SHARISSH": (((1, 129, 81, 61, 172, 192, 55, 143, 147, 31, 0, 0),), "Keeper Sharissh"),
    "PRIEST_KEHMTUT": (((1, 129, 251, 34, 97, 237, 6, 204, 91, 25, 0, 0),), "Priest Kehmtut"),
    "SAHLAHJAR_THE_DEAD": (((1, 129, 145, 54, 191, 148, 205, 232, 38, 44, 0, 0),), "Sahlahjar the Dead"),
    "INSCRIBED_WALL": (((1, 129, 204, 60, 42, 161, 6, 233, 181, 55, 0, 0),), "Inscribed Wall"),
    "DENDE": (((1, 129, 252, 16, 226, 249, 48, 192, 241, 24, 0, 0),), "Dende"),
    "DUEL_MASTER_LUMBO": (((1, 129, 156, 16, 206, 210, 223, 172, 48, 50, 0, 0),), "Duel Master Lumbo"),
    "JEJUMBA": (((1, 129, 132, 16, 92, 139, 91, 161, 83, 15, 0, 0),), "Jejumba"),
    "MASTER_OF_CEREMONIES": (((1, 129, 216, 16, 6, 243, 22, 206, 252, 14, 0, 0),), "Master of Ceremonies"),
    "MINA": (((1, 129, 4, 17, 40, 169, 74, 136, 206, 20, 0, 0),), "Mina"),
    "PRINCE_AHMTUR_THE_MIGHTY": (
        (
            (1, 129, 241, 16, 224, 219, 241, 208, 247, 126, 0, 0),
            (1, 129, 63, 27, 183, 173, 132, 251, 98, 69, 0, 0),
        ),
        "Prince Ahmtur the Mighty",
    ),
    "PRINCE_BOKKA_THE_MAGNIFICENT": (((1, 129, 236, 16, 19, 166, 225, 142, 206, 56, 0, 0),), "Prince Bokka the Magnificent"),
    "PRINCE_MEHTU_THE_WISE": (((1, 129, 231, 16, 83, 211, 75, 243, 157, 38, 0, 0),), "Prince Mehtu the Wise"),
    "ROYAL_FINANCE_MINISTER_OLUDA": (((1, 129, 166, 16, 152, 146, 112, 244, 113, 52, 0, 0),), "Royal Finance Minister Oluda"),
    "ROYAL_FOOD_TASTER_RENDU": (((1, 129, 178, 16, 72, 142, 44, 213, 105, 91, 0, 0),), "Royal Food Taster Rendu"),
    "VAUGHN_THE_VENERABLE": (((1, 129, 31, 27, 68, 149, 6, 234, 108, 123, 0, 0),), "Vaughn the Venerable"),
    "HEAD_PRIEST_VAHMANI": (((1, 129, 192, 64, 45, 223, 213, 242, 67, 122, 0, 0),), "Head Priest Vahmani"),
    "LIEUTENANT_MURUNDA": (((1, 129, 181, 64, 227, 210, 169, 228, 241, 101, 0, 0),), "Lieutenant  Murunda"),
    "VABBI_NOBLE": (((126, 123, 240, 171, 153, 155, 5, 21, 0, 0),), "Vabbi Noble"),
    "ZILO_THE_DRUNKARD": (((1, 129, 116, 17, 100, 184, 52, 150, 154, 103, 0, 0),), "Zilo the Drunkard"),
    "CAPTAIN_BOHSEDA": (((1, 129, 217, 76, 52, 227, 69, 133, 106, 87, 0, 0),), "Captain Bohseda"),
    "UNLUCKY_SIMON": (((1, 129, 210, 64, 2, 255, 85, 247, 4, 21, 0, 0),), "Unlucky Simon"),
    "ESTATE_GUARD_RIKESH": (((1, 129, 198, 64, 115, 238, 240, 228, 116, 121, 0, 0),), "Estate Guard Rikesh"),
    "HAROJ_FIREMANE": (((1, 129, 130, 19, 36, 204, 137, 211, 19, 41, 0, 0),), "Haroj Firemane"),
    "MELONNI": (((1, 129, 172, 56, 0, 0),), "Melonni"),
    "MASTER_OF_WHISPERS": (((1, 129, 221, 56, 0, 0),), "Master of Whispers"),
    "NORGU": (((1, 129, 225, 56, 0, 0),), "Norgu"),
    "BINDING_GUARDIAN": (((1, 129, 83, 39, 13, 163, 0, 150, 246, 77, 0, 0),), "Binding Guardian"),
    "CHAPLAIN_PHYRATYSS": (((1, 129, 164, 40, 239, 190, 66, 133, 177, 17, 0, 0),), "Chaplain Phyratyss"),
    "GUARDIAN_OF_WHISPERS": (((1, 129, 189, 91, 14, 130, 45, 249, 80, 87, 0, 0),), "Guardian of Whispers"),
    "KEEPER_SHAFOSS": (((1, 129, 29, 99, 221, 238, 140, 155, 139, 87, 0, 0),), "Keeper Shafoss"),
    "RAZAH": (((1, 129, 250, 56, 0, 0),), "Razah"),
    "SEER_OF_TRUTH": (((1, 129, 189, 86, 226, 218, 27, 220, 88, 106, 0, 0),), "Seer of Truth"),
    "GWEN": (((2, 129, 175, 17, 0, 0),), "Gwen"),
    "MEDANDO_SKILLS": (((1, 129, 76, 34, 75, 223, 120, 139, 110, 127, 0, 0),), "Medando [Skills]"),
    "MHENLO": (((1, 129, 26, 79, 235, 179, 80, 160, 65, 54, 0, 0),), "Mhenlo"),
    "BROTHER_MHENLO": (((1, 129, 26, 79, 235, 179, 80, 160, 65, 54, 0, 0),), "Brother Mhenlo"),
    "GUARDSMAN_CHOW": AgentTargetDefinition(display_name="Guardsman Chow"),
    "GUARDSMAN_CHOW_OUTPOST": AgentTargetDefinition(display_name="Guardsman Chow"),
    "KAHDASH": AgentTargetDefinition(display_name="Kahdash"),
    "MICHIKO_SKILLS": (((2, 110, 190, 167, 165, 179, 120, 49, 0, 0),), "Michiko [Skills]"),
    "NPC": (((2, 129, 155, 34, 73, 236, 154, 195, 76, 124, 0, 0),), ""),
    "OGDEN_STONEHEALER": (((2, 129, 86, 6, 0, 0),), "Ogden Stonehealer"),
    "DEVONA": (((2, 129, 211, 58, 125, 199, 132, 219, 242, 1, 0, 0),), "Devona"),
    "PIKIN_HERO_SKILLS": (((1, 129, 250, 82, 43, 183, 147, 243, 123, 11, 0, 0),), "Pikin [Hero Skills]"),
    "SCRYING_POOL": (((2, 129, 155, 34, 73, 236, 154, 195, 76, 124, 0, 0),), "Scrying Pool"),
    "TOHN_SKILLS": (((1, 129, 186, 31, 67, 130, 51, 248, 20, 68, 0, 0),), "Tohn [Skills]"),
    "VEKK": (((2, 129, 79, 6, 0, 0),), "Vekk"),
    "WANDERING_PRIEST": (((1, 129, 30, 82, 119, 217, 105, 203, 18, 88, 0, 0),), "Wandering Priest"),
    "WHISPERS_ACOLYTE": (((1, 129, 230, 24, 20, 173, 107, 164, 59, 115, 0, 0),), "Whispers Acolyte"),
    "ZHED_SHADOWHOOF": (((1, 129, 177, 56, 0, 0),), "Zhed Shadowhoof"),
    "WAILING_LORD": (((40, 31, 154, 140, 42, 223, 196, 52, 0, 0),), "Wailing Lord"),
    # "TOWER_OF_COURAGE_NPC": (((1, 129, 216, 71, 88, 179, 225, 255, 119, 64, 0, 0),), "Tower of Courage NPC"),
}

ENEMY_TARGETS: dict[str, AgentTargetValue] = {
    "INFERNAL_WURM": (((225, 20, 149, 206, 31, 225, 185, 90, 0, 0),), "Infernal Wurm"),
    "SHARD_WOLF": (((77, 31, 140, 221, 57, 157, 245, 44, 0, 0),), "Shard Wolf"),
    "WAILING_LORD": (((26, 31, 5, 191, 239, 149, 25, 80, 0, 0),), "Wailing Lord"),
    "ERULAI_THE_INIMICAL": (((1, 129, 101, 19, 21, 248, 75, 221, 120, 51, 0, 0),), "Erulai the Inimical"),
    "JEREK": (((1, 129, 134, 56, 31, 183, 97, 252, 255, 51, 0, 0),), "Jerek"),
    "RINKHAL_MONITOR": (((1, 129, 5, 33, 180, 156, 4, 130, 168, 124, 0, 0),), "Rinkhal Monitor"),
    "IRONFIST": (((1, 129, 220, 64, 162, 197, 32, 146, 126, 76, 0, 0),), "Ironfist"),
    "KOURNAN_FIELD_COMMANDER": (((1, 129, 99, 85, 124, 138, 53, 167, 241, 45, 0, 0),), "Kournan Field Commander"),
    "KOURNAN_TASKMASTER": (((1, 129, 61, 11, 112, 166, 86, 251, 234, 51, 0, 0),), "Kournan Taskmaster"),
    "OVERSEER_HAUBEH": (((1, 129, 167, 76, 179, 194, 195, 206, 180, 17, 0, 0),), "Overseer Haubeh"),
    "TASKMASTER_SADI_BELAI": (((1, 129, 67, 40, 182, 140, 81, 209, 203, 48, 0, 0),), "Taskmaster Sadi-Belai"),
    "TASKMASTER_SULI": (((1, 129, 68, 40, 94, 190, 24, 190, 226, 10, 0, 0),), "Taskmaster Suli"),
    "TASKMASTER_VANAHK": (((1, 129, 66, 40, 19, 137, 213, 187, 248, 63, 0, 0),), "Taskmaster Vanahk"),
    "HARBINGER_OF_TWILIGHT": (((1, 129, 93, 25, 213, 160, 97, 164, 190, 52, 0, 0),), "Harbinger of Twilight"),
    "THE_DROUGHT": (((1, 129, 218, 4, 156, 178, 56, 141, 187, 82, 0, 0),), "The Drought"),
    "CORSAIR_RUNNER": (((1, 129, 163, 76, 54, 255, 228, 199, 85, 73, 0, 0),), "Corsair Runner"),
    "THE_HUNGER": (((1, 129, 138, 17, 190, 204, 108, 226, 48, 123, 0, 0),), "The Hunger"),
    "SOLITARY_COLOSSUS": (((1, 129, 142, 37, 81, 233, 163, 236, 14, 127, 0, 0),), "Solitary Colossus"),
    "APOCRYPHA": AgentTargetDefinition(display_name="Apocrypha"),
    # "FANGED_IBOGA": (((1, 2, 3, 4),), "Fanged Iboga"),
}

GADGET_TARGETS: dict[str, AgentTargetValue] = {
    "CHEST": (((123, 32, 56, 239, 111, 184, 88, 49, 0, 0),), "Chest"),
    "CHEST_OF_WOE": (((2, 129, 148, 49, 154, 172, 124, 229, 33, 98, 0, 0),), "Chest of Woe"),
    "CHEST_OF_BURROWS": (((2, 129, 87, 40, 105, 234, 7, 193, 85, 122, 0, 0),), "Chest of Burrows"),
    "MAZ_S_CHEST": (((2, 129, 115, 60, 0, 0),), "Maz's Chest"),
    "CELL_LOCK": (((1, 129, 84, 25, 121, 157, 164, 216, 47, 4, 0, 0),), "Cell Lock"),
    "MONUMENT_TO_THE_DEFEAT_OF_PALAWA_JOKO": (((1, 129, 215, 34, 159, 146, 43, 245, 183, 58, 0, 0),), "Monument to the Defeat of Palawa Joko"),
    "WURM_SPOOR": (((1, 129, 13, 38, 234, 223, 171, 254, 11, 49, 0, 0),), "Wurm Spoor"),
    "BOSS_LOCK": (((2, 129, 129, 25, 72, 206, 22, 143, 238, 93, 0, 0),), "Boss Lock"),
    "DUNGEON_LOCK": (((2, 129, 128, 25, 89, 218, 32, 206, 95, 122, 0, 0),), "Dungeon Lock"),
    "STONE_PEDESTAL": AgentTargetDefinition(display_name="Stone Pedestal"),
}

def _normalize_agent_target(value: AgentTargetValue | None) -> AgentTargetDefinition | None:
    if value is None:
        return None
    if isinstance(value, AgentTargetDefinition):
        return value

    encoded_names_raw, display_name = value
    if encoded_names_raw and isinstance(encoded_names_raw[0], int):
        encoded_names = (tuple(int(v) for v in encoded_names_raw),)
    else:
        encoded_names = tuple(tuple(int(v) for v in encoded_name) for encoded_name in encoded_names_raw)

    return AgentTargetDefinition(
        display_name=str(display_name or ""),
        encoded_names=encoded_names,
    )


def get_named_agent_target(kind: str, key: Any) -> AgentTargetDefinition | None:
    key_str = str(key or "").strip()
    if not key_str:
        return None

    registries = {
        TargetRegistryKind.NPC.value: NPC_TARGETS,
        TargetRegistryKind.ENEMY.value: ENEMY_TARGETS,
        TargetRegistryKind.GADGET.value: GADGET_TARGETS,
    }
    return _normalize_agent_target(registries.get(kind, {}).get(key_str))


def get_target_registry() -> dict[str, dict[str, AgentTargetValue]]:
    return {
        TargetRegistryKind.NPC.value: NPC_TARGETS,
        TargetRegistryKind.ENEMY.value: ENEMY_TARGETS,
        TargetRegistryKind.GADGET.value: GADGET_TARGETS,
    }
