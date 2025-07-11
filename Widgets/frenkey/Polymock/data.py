from enum import Enum, IntEnum
from typing import Callable
from Py4GWCoreLib.GlobalCache import GLOBAL_CACHE

Polymock_Registration = [640, [15506, 18910]]
Polymock_Registration = [640, [15506, 18910]]

class SkillReaction(IntEnum):
    None_ = 0
    Interrupt = 1
    Block = 2
    BlockOrInterrupt = 3

class Polymock_Skill():
    def __init__(self, skill_id: int, reaction: SkillReaction = SkillReaction.None_, use_glyph_of_concentration: bool = False):
        self.skill_id: int = skill_id
        self.name: str = GLOBAL_CACHE.Skill.GetName(skill_id)
        self.reaction: SkillReaction = reaction
        self.use_glyph_of_concentration: bool = use_glyph_of_concentration

class PolymockBar():
    def __init__(self, name: str, item_model_id: int, item_texture: str, skills: dict[int, Polymock_Skill]):
        self.name: str = name
        self.item_model_id: int = item_model_id
        self.item_texture: str = item_texture
        self.skills: dict[int, Polymock_Skill] = skills
        self.damage_skills: dict[int, Polymock_Skill] = skills.copy()
        
        self.skill_ids = {
            skill.skill_id: skill for skill in self.skills.values() if skill.skill_id > 0}

        self.skills[8] = Polymock_Skill(GLOBAL_CACHE.Skill.GetID(
            "Polymock_Glyph_of_Power"), SkillReaction.None_)  # Glyph of Power
        self.skills[7] = Polymock_Skill(GLOBAL_CACHE.Skill.GetID(
            "Polymock_Ether_Signet"), SkillReaction.None_)  # Ether Signet
        self.skills[6] = Polymock_Skill(GLOBAL_CACHE.Skill.GetID(
            "Polymock_Glyph_of_Concentration"), SkillReaction.None_)  # Glyph of Concentration
        self.skills[5] = Polymock_Skill(GLOBAL_CACHE.Skill.GetID(
            "Polymock_Block"), SkillReaction.None_)  # Block
        self.skills[4] = Polymock_Skill(GLOBAL_CACHE.Skill.GetID(
            "Polymock_Power_Drain"), SkillReaction.None_)  # Power Drain

    def has_skill(self, skill_id: int) -> bool:
        return skill_id in self.skill_ids

    def get_skill_reaction(self, skill_id: int) -> SkillReaction:
        for skill in self.skills.values():
            if skill.skill_id == skill_id:
                return skill.reaction

        return SkillReaction.None_

    def should_use_glyph(self, skill_id: int) -> bool:
        for skill in self.skills.values():
            if skill.skill_id == skill_id:
                return skill.use_glyph_of_concentration

        return False

    def __repr__(self):
        return f"PolymockBar(name='{self.name}', skills={self.skills})"

class PolymockPieces(Enum):
    Gargoyle = PolymockBar("Gargoyle", 24361, "[24361] - Gargoyle Polymock Piece.png", {
        1: Polymock_Skill(GLOBAL_CACHE.Skill.GetID("Polymock_Lightning_Strike"), SkillReaction.Block),
        2: Polymock_Skill(GLOBAL_CACHE.Skill.GetID("Polymock_Lightning_Orb"), SkillReaction.BlockOrInterrupt, True),
        3: Polymock_Skill(GLOBAL_CACHE.Skill.GetID("Polymock_Lightning_Djinns_Haste")),
    })

    Mergoyle = PolymockBar("Mergoyle", 24369, "[24369] - Mergoyle Polymock Piece.png", {
        1: Polymock_Skill(GLOBAL_CACHE.Skill.GetID("Polymock_Overload"), SkillReaction.Block),
        2: Polymock_Skill(GLOBAL_CACHE.Skill.GetID("Polymock_Glyph_Destabilization"), SkillReaction.Block),
        3: Polymock_Skill(GLOBAL_CACHE.Skill.GetID("Polymock_Mind_Wreck"), SkillReaction.BlockOrInterrupt, True),
    })

    Skale = PolymockBar("Skale", 24373, "[24373] - Skale Polymock Piece.png", {
        1: Polymock_Skill(GLOBAL_CACHE.Skill.GetID("Polymock_Deathly_Chill"), SkillReaction.Block),
        2: Polymock_Skill(GLOBAL_CACHE.Skill.GetID("Polymock_Rising_Bile"), SkillReaction.Block, True),
        3: Polymock_Skill(GLOBAL_CACHE.Skill.GetID("Polymock_Rotting_Flesh"), SkillReaction.BlockOrInterrupt),
    })

    Fire_Imp = PolymockBar("Fire Imp", 24359, "[24359] - Fire Imp Polymock Piece.png", {
        1: Polymock_Skill(GLOBAL_CACHE.Skill.GetID("Polymock_Flare"), SkillReaction.Block),
        2: Polymock_Skill(GLOBAL_CACHE.Skill.GetID("Polymock_Immolate"), SkillReaction.Block),
        3: Polymock_Skill(GLOBAL_CACHE.Skill.GetID("Polymock_Meteor"), SkillReaction.BlockOrInterrupt, True),
    })

    Kappa = PolymockBar("Kappa", 24367, "[24367] - Kappa Polymock Piece.png", {
        1: Polymock_Skill(GLOBAL_CACHE.Skill.GetID("Polymock_Ice_Spear"), SkillReaction.Block),
        2: Polymock_Skill(GLOBAL_CACHE.Skill.GetID("Polymock_Ice_Shard_Storm"), SkillReaction.Block),
        3: Polymock_Skill(GLOBAL_CACHE.Skill.GetID("Polymock_Frozen_Trident"), SkillReaction.BlockOrInterrupt, True),
    })

    Ice_Imp = PolymockBar("Ice Imp", 24366, "[24366] - Ice Imp Polymock Piece.png", {
        1: Polymock_Skill(GLOBAL_CACHE.Skill.GetID("Polymock_Ice_Spear"), SkillReaction.Block),
        2: Polymock_Skill(GLOBAL_CACHE.Skill.GetID("Polymock_Icy_Prison"), SkillReaction.Block),
        3: Polymock_Skill(GLOBAL_CACHE.Skill.GetID("Polymock_Mind_Freeze"), SkillReaction.BlockOrInterrupt, True),
    })

    Earth_Elemental = PolymockBar("Earth Elemental", 24357, "[24357] - Earth Elemental Polymock Piece.png", {
        1: Polymock_Skill(GLOBAL_CACHE.Skill.GetID("Polymock_Stone_Daggers"), SkillReaction.Block),
        2: Polymock_Skill(GLOBAL_CACHE.Skill.GetID("Polymock_Obsidian_Flame"), SkillReaction.BlockOrInterrupt, True),
        3: Polymock_Skill(GLOBAL_CACHE.Skill.GetID("Polymock_Earthquake"), SkillReaction.BlockOrInterrupt, True),
    })

    Ice_Elemental = PolymockBar("Ice Elemental", 24365, "[24365] - Ice Elemental Polymock Piece.png", {
        1: Polymock_Skill(GLOBAL_CACHE.Skill.GetID("Polymock_Ice_Spear"), SkillReaction.Block),
        2: Polymock_Skill(GLOBAL_CACHE.Skill.GetID("Polymock_Frozen_Armor"), SkillReaction.Interrupt),
        3: Polymock_Skill(GLOBAL_CACHE.Skill.GetID("Polymock_Glyph_Freeze"), SkillReaction.Block, True),
    })

    Fire_Elemental = PolymockBar("Fire Elemental", 24358, "[24358] - Fire Elemental Polymock Piece.png", {
        1: Polymock_Skill(GLOBAL_CACHE.Skill.GetID("Polymock_Flare"), SkillReaction.Block),
        2: Polymock_Skill(GLOBAL_CACHE.Skill.GetID("Polymock_Fireball"), SkillReaction.Block, True),
        3: Polymock_Skill(GLOBAL_CACHE.Skill.GetID("Polymock_Rodgorts_Invocation"), SkillReaction.BlockOrInterrupt),
    })

    Aloe_Seed = PolymockBar("Aloe Seed", 24355, "[24355] - Aloe Seed Polymock Piece.png", {
        1: Polymock_Skill(GLOBAL_CACHE.Skill.GetID("Polymock_Smite"), SkillReaction.Block),
        2: Polymock_Skill(GLOBAL_CACHE.Skill.GetID("Polymock_Smite_Hex"), SkillReaction.Interrupt),
        3: Polymock_Skill(GLOBAL_CACHE.Skill.GetID("Polymock_Bane_Signet"), SkillReaction.Block, True),
    })

    Mirage_Iboga = PolymockBar("Mirage Iboga", 24363, "[24363] - Mirage Iboga Polymock Piece.png", {
        1: Polymock_Skill(GLOBAL_CACHE.Skill.GetID("Polymock_Overload"), SkillReaction.Block),
        2: Polymock_Skill(GLOBAL_CACHE.Skill.GetID("Polymock_Calculated_Risk"), SkillReaction.Block),
        3: Polymock_Skill(GLOBAL_CACHE.Skill.GetID("Polymock_Recurring_Insecurity"), SkillReaction.BlockOrInterrupt, True),
    })

    Gaki = PolymockBar("Gaki", 24360, "[24360] - Gaki Polymock Piece.png", {
        1: Polymock_Skill(GLOBAL_CACHE.Skill.GetID("Polymock_Smite"), SkillReaction.Interrupt),
        2: Polymock_Skill(GLOBAL_CACHE.Skill.GetID("Polymock_Signet_of_Revenge"), SkillReaction.Block),
        3: Polymock_Skill(GLOBAL_CACHE.Skill.GetID("Polymock_Signet_of_Smiting"), SkillReaction.Block, True),
    })

    Mantis_Dreamweaver = PolymockBar("Mantis Dreamweaver", 0, "", {
        1: Polymock_Skill(GLOBAL_CACHE.Skill.GetID("Polymock_Overload"), SkillReaction.Block),
        2: Polymock_Skill(GLOBAL_CACHE.Skill.GetID("Polymock_Signet_of_Clumsiness"), SkillReaction.Block),
        3: Polymock_Skill(GLOBAL_CACHE.Skill.GetID("Polymock_Migraine"), SkillReaction.BlockOrInterrupt, True),
    })

    Mursaat_Elementalist = PolymockBar("Mursaat Elementalist", 24370, "[24370] - Mursaat Elementalist Polymock Piece.png", {
        1: Polymock_Skill(GLOBAL_CACHE.Skill.GetID("Polymock_Lightning_Strike"), SkillReaction.Block),
        2: Polymock_Skill(GLOBAL_CACHE.Skill.GetID("Polymock_Mind_Shock"), SkillReaction.Block),
        3: Polymock_Skill(GLOBAL_CACHE.Skill.GetID("Polymock_Shock_Arrow"), SkillReaction.BlockOrInterrupt, True),
    })

    Naga_Shaman = PolymockBar("Naga Shaman", 24372, "[24372] - Naga Shaman Polymock Piece.png", {
        1: Polymock_Skill(GLOBAL_CACHE.Skill.GetID("Polymock_Lamentation"), SkillReaction.Block),
        2: Polymock_Skill(GLOBAL_CACHE.Skill.GetID("Polymock_Spirit_Rift"), SkillReaction.Block),
        3: Polymock_Skill(GLOBAL_CACHE.Skill.GetID("Polymock_Painful_Bond"), SkillReaction.BlockOrInterrupt, True),
    })

    Ruby_Djinn = PolymockBar("Ruby Djinn", 24371, "[24371] - Ruby Djinn Polymock Piece.png", {
        1: Polymock_Skill(GLOBAL_CACHE.Skill.GetID("Polymock_Flare"), SkillReaction.Block),
        2: Polymock_Skill(GLOBAL_CACHE.Skill.GetID("Polymock_Searing_Flames"), SkillReaction.Block),
        3: Polymock_Skill(GLOBAL_CACHE.Skill.GetID("Polymock_Glowing_Gaze"), SkillReaction.BlockOrInterrupt, True),
    })

    Stone_Rain = PolymockBar("Stone Rain", 24374, "[24374] - Stone Rain Polymock Piece.png", {
        1: Polymock_Skill(GLOBAL_CACHE.Skill.GetID("Polymock_Stone_Daggers"), SkillReaction.Block),
        2: Polymock_Skill(GLOBAL_CACHE.Skill.GetID("Polymock_Eruption"), SkillReaction.Block),
        3: Polymock_Skill(GLOBAL_CACHE.Skill.GetID("Polymock_Stoning"), SkillReaction.BlockOrInterrupt, True),
    })

    Wind_Rider = PolymockBar("Wind Rider", 24356, "[24356] - Wind Rider Polymock Piece.png", {
        1: Polymock_Skill(GLOBAL_CACHE.Skill.GetID("Polymock_Overload"), SkillReaction.Block),
        2: Polymock_Skill(GLOBAL_CACHE.Skill.GetID("Polymock_Backfire"), SkillReaction.Block),
        3: Polymock_Skill(GLOBAL_CACHE.Skill.GetID("Polymock_Guilt"), SkillReaction.BlockOrInterrupt, True),
    })

    Bone_Dragon = PolymockBar("Bone Dragon", 0, "", {
        1: Polymock_Skill(GLOBAL_CACHE.Skill.GetID("Polymock_Deathly_Chill"), SkillReaction.Block),
        2: Polymock_Skill(GLOBAL_CACHE.Skill.GetID("Polymock_Rising_Bile"), SkillReaction.BlockOrInterrupt),
        3: Polymock_Skill(GLOBAL_CACHE.Skill.GetID("Polymock_Poisoned_Ground"), SkillReaction.Block, True),
    })

    Charr_Flamecaller = PolymockBar("Charr Flamecaller", 0, "", {
        1: Polymock_Skill(GLOBAL_CACHE.Skill.GetID("Polymock_Flare"), SkillReaction.Block),
        2: Polymock_Skill(GLOBAL_CACHE.Skill.GetID("Polymock_Fireball"), SkillReaction.Block),
        3: Polymock_Skill(GLOBAL_CACHE.Skill.GetID("Polymock_Mind_Blast"), SkillReaction.BlockOrInterrupt, True),
    })

    Charr_Shaman = PolymockBar("Charr Shaman", 0, "", {
        1: Polymock_Skill(GLOBAL_CACHE.Skill.GetID("Polymock_Smite"), SkillReaction.Block),
        2: Polymock_Skill(GLOBAL_CACHE.Skill.GetID("Polymock_Piercing_Light_Spear"), SkillReaction.Block),
        3: Polymock_Skill(GLOBAL_CACHE.Skill.GetID("Polymock_Signet_of_Smiting"), SkillReaction.BlockOrInterrupt, True),
    })

    Dolyak_Rider = PolymockBar("Dolyak Rider", 0, "", {
        1: Polymock_Skill(GLOBAL_CACHE.Skill.GetID("Polymock_Smite"), SkillReaction.Block),
        2: Polymock_Skill(GLOBAL_CACHE.Skill.GetID("Polymock_Banish"), SkillReaction.BlockOrInterrupt, True),
        3: Polymock_Skill(GLOBAL_CACHE.Skill.GetID("Polymock_Bane_Signet"), SkillReaction.Block),
    })

    Dredge = PolymockBar("Dredge", 0, "", {
        1: Polymock_Skill(GLOBAL_CACHE.Skill.GetID("Polymock_Ice_Spear"), SkillReaction.Block),
        2: Polymock_Skill(GLOBAL_CACHE.Skill.GetID("Polymock_Icy_Bonds"), SkillReaction.Block),
        3: Polymock_Skill(GLOBAL_CACHE.Skill.GetID("Polymock_Mind_Freeze"), SkillReaction.BlockOrInterrupt, True),
    })

    Dwarven_Arcanist = PolymockBar("Dwarven Arcanist", 0, "", {
        1: Polymock_Skill(GLOBAL_CACHE.Skill.GetID("Polymock_Stone_Daggers"), SkillReaction.Block),
        2: Polymock_Skill(GLOBAL_CACHE.Skill.GetID("Polymock_Sandstorm"), SkillReaction.Block),
        3: Polymock_Skill(GLOBAL_CACHE.Skill.GetID("Polymock_Earthquake"), SkillReaction.BlockOrInterrupt, True),
    })

    Skeletal_Mage = PolymockBar("Skeletal Mage", 0, "", {
        1: Polymock_Skill(GLOBAL_CACHE.Skill.GetID("Polymock_Overload"), SkillReaction.Block),
        2: Polymock_Skill(GLOBAL_CACHE.Skill.GetID("Polymock_Backfire"), SkillReaction.Block),
        3: Polymock_Skill(GLOBAL_CACHE.Skill.GetID("Polymock_Diversion"), SkillReaction.BlockOrInterrupt, True),
    })

    Smoke_Wraith = PolymockBar("Smoke Wraith", 0, "", {
        1: Polymock_Skill(GLOBAL_CACHE.Skill.GetID("Polymock_Lightning_Strike"), SkillReaction.Block),
        2: Polymock_Skill(GLOBAL_CACHE.Skill.GetID("Polymock_Mind_Shock"), SkillReaction.Block),
        3: Polymock_Skill(GLOBAL_CACHE.Skill.GetID("Polymock_Lightning_Blast"), SkillReaction.BlockOrInterrupt, True),
    })

    Titan = PolymockBar("Titan", 0, "", {
        1: Polymock_Skill(GLOBAL_CACHE.Skill.GetID("Polymock_Flare")),
        2: Polymock_Skill(GLOBAL_CACHE.Skill.GetID("Polymock_Rodgorts_Invocation"), SkillReaction.Block),
        3: Polymock_Skill(GLOBAL_CACHE.Skill.GetID("Polymock_Savannah_Heat"), SkillReaction.BlockOrInterrupt, True),
    })

class Polymock_Quest():
    def __init__(self, quest_name: str, opponent_name: str, quest_id: int, marker_position : tuple[float, float], model_id: int, polymock_pieces: list[PolymockPieces], counter_pieces: list[PolymockPieces] = []):
        self.polymock_pieces = polymock_pieces
        self.counter_pieces = counter_pieces
        self.quest_id = quest_id
        self.model_id = model_id
        self.name = quest_name
        self.opponent_name = opponent_name
        self.marker_x = marker_position[0]
        self.marker_y = marker_position[1]
        
    def get_quest_data(self):
        return GLOBAL_CACHE.Quest.GetQuestData(self.quest_id)

class Polymock_Spawns(Enum):
    Polymock_Glacier = [687, [-703, -311]]
    Polymock_Coliseum = [686, [4165.00, -591.00]]
    Polymock_Crossing = [688, [4019.00, 765.00]]

class Polymock_Quests(Enum):
    @staticmethod
    def get_quest_by_model_id(model_id: int) -> 'Polymock_Quest|None':
        for quest in Polymock_Quests:
            if quest.value.model_id == model_id:
                return quest.value

        return None  

    Yulma = Polymock_Quest("Polymock: Defeat Yulma", "Yulma", 882, (19231, 19669) ,6752,
                           [PolymockPieces.Gargoyle, PolymockPieces.Skale,
                               PolymockPieces.Mergoyle],
                           [PolymockPieces.Skale, PolymockPieces.Mergoyle, PolymockPieces.Gargoyle])

    Plurgg = Polymock_Quest("Polymock: Defeat Plurgg", "Plurgg", 875, (16382, 17753), 6753,
                            [PolymockPieces.Fire_Imp, PolymockPieces.Ice_Imp,
                                PolymockPieces.Kappa],
                            [PolymockPieces.Skale, PolymockPieces.Fire_Imp, PolymockPieces.Gargoyle])

    Blarp = Polymock_Quest("Polymock: Defeat Blarp", "Blarp", 881, (-8940, -21799), 6754,
                           [PolymockPieces.Earth_Elemental, PolymockPieces.Ice_Elemental,
                               PolymockPieces.Fire_Elemental],
                           [PolymockPieces.Kappa, PolymockPieces.Fire_Imp, PolymockPieces.Skale])

    Fonk = Polymock_Quest("Polymock: Defeat Fonk", "Fonk", 876, (19789, -3760), 6782,
                          [PolymockPieces.Kappa, PolymockPieces.Aloe_Seed,
                              PolymockPieces.Wind_Rider],
                          [PolymockPieces.Gargoyle, PolymockPieces.Kappa, PolymockPieces.Fire_Imp])

    Dune_Teardrinker = Polymock_Quest("Polymock: Defeat Dune Teardrinker", "Dune Teardrinker", 877, (-13317, 15435), 6606,
                                      [PolymockPieces.Charr_Shaman,
                                          PolymockPieces.Charr_Flamecaller, PolymockPieces.Titan],
                                      [PolymockPieces.Earth_Elemental, PolymockPieces.Fire_Imp, PolymockPieces.Kappa, PolymockPieces.Fire_Elemental])

    Grulhammer_Silverfist = Polymock_Quest("Polymock: Defeat Grulhammer Silverfist", "Grulhammer Silverfist", 878, (-22492, 13722), 6215,
                                           [PolymockPieces.Dredge, PolymockPieces.Dolyak_Rider,
                                               PolymockPieces.Dwarven_Arcanist],
                                           [PolymockPieces.Kappa, PolymockPieces.Earth_Elemental, PolymockPieces.Ice_Imp, PolymockPieces.Ice_Elemental])

    Necromancer_Volumandus = Polymock_Quest("Polymock: Defeat Necromancer Volumandus", "Necromancer Volumandus", 879, (23229, -12794), 1991,
                                            [PolymockPieces.Skeletal_Mage,
                                                PolymockPieces.Smoke_Wraith, PolymockPieces.Bone_Dragon],
                                            [PolymockPieces.Earth_Elemental, PolymockPieces.Fire_Imp, PolymockPieces.Kappa, PolymockPieces.Fire_Elemental, PolymockPieces.Aloe_Seed])

    Master_Hoff = Polymock_Quest("Polymock: Defeat Master Hoff", "Master Hoff", 880, (15933, 19115), 6778,
                                 [PolymockPieces.Bone_Dragon, PolymockPieces.Dolyak_Rider, PolymockPieces.Gaki, PolymockPieces.Mantis_Dreamweaver, PolymockPieces.Mirage_Iboga,
                                     PolymockPieces.Naga_Shaman, PolymockPieces.Ruby_Djinn, PolymockPieces.Stone_Rain, PolymockPieces.Titan, PolymockPieces.Wind_Rider, PolymockPieces.Mursaat_Elementalist],
                                 [PolymockPieces.Fire_Elemental, PolymockPieces.Ice_Elemental, PolymockPieces.Earth_Elemental, PolymockPieces.Fire_Elemental, PolymockPieces.Aloe_Seed])
