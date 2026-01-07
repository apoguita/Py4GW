from typing import override

from Py4GWCoreLib.enums import SpiritModelID
from Widgets.CustomBehaviors.primitives.scores.score_per_agent_quantity_definition import ScorePerAgentQuantityDefinition
from Widgets.CustomBehaviors.primitives.scores.score_per_health_gravity_definition import ScorePerHealthGravityDefinition
from Widgets.CustomBehaviors.primitives.scores.score_static_definition import ScoreStaticDefinition
from Widgets.CustomBehaviors.primitives.skillbars.custom_behavior_base_utility import CustomBehaviorBaseUtility
from Widgets.CustomBehaviors.primitives.skills.custom_skill import CustomSkill
from Widgets.CustomBehaviors.primitives.skills.custom_skill_utility_base import CustomSkillUtilityBase
from Widgets.CustomBehaviors.skills.common.auto_attack_utility import AutoAttackUtility
from Widgets.CustomBehaviors.skills.common.breath_of_the_great_dwarf_utility import BreathOfTheGreatDwarfUtility
from Widgets.CustomBehaviors.skills.common.by_urals_hammer_utility import ByUralsHammerUtility
from Widgets.CustomBehaviors.skills.common.ebon_battle_standard_of_honor_utility import EbonBattleStandardOfHonorUtility
from Widgets.CustomBehaviors.skills.common.ebon_vanguard_assassin_support_utility import EbonVanguardAssassinSupportUtility
from Widgets.CustomBehaviors.skills.common.great_dwarf_weapon_utility import GreatDwarfWeaponUtility
from Widgets.CustomBehaviors.skills.common.i_am_unstoppable_utility import IAmUnstoppableUtility
from Widgets.CustomBehaviors.skills.generic.generic_resurrection_utility import GenericResurrectionUtility
from Widgets.CustomBehaviors.skills.generic.raw_aoe_attack_utility import RawAoeAttackUtility
from Widgets.CustomBehaviors.skills.generic.raw_spirit_utility import RawSpiritUtility
from Widgets.CustomBehaviors.skills.paragon.fall_back_utility import FallBackUtility
from Widgets.CustomBehaviors.skills.ritualist.armor_of_unfeeling_utility import ArmorOfUnfeelingUtility
from Widgets.CustomBehaviors.skills.ritualist.gaze_of_fury_utility import GazeOfFuryUtility
from Widgets.CustomBehaviors.skills.ritualist.signet_of_spirits_utility import SignetOfSpiritsUtility
from Widgets.CustomBehaviors.skills.ritualist.summon_spirit_utility import SummonSpiritUtility

class RitualistSos_UtilitySkillBar(CustomBehaviorBaseUtility):

    def __init__(self):
        super().__init__()
        in_game_build = list(self.skillbar_management.get_in_game_build().values())

        # core
        self.signet_of_spirits_utility: CustomSkillUtilityBase = SignetOfSpiritsUtility(event_bus=self.event_bus, current_build=in_game_build, score_definition=ScoreStaticDefinition(92))
        self.vampirism_utility: CustomSkillUtilityBase = RawSpiritUtility(event_bus=self.event_bus, skill=CustomSkill("Vampirism"), current_build=in_game_build, score_definition=ScoreStaticDefinition(91), owned_spirit_model_id=SpiritModelID.VAMPIRISM)
        self.bloodsong_utility: CustomSkillUtilityBase = RawSpiritUtility(event_bus=self.event_bus, skill=CustomSkill("Bloodsong"), current_build=in_game_build, score_definition=ScoreStaticDefinition(90), owned_spirit_model_id=SpiritModelID.BLOODSONG)
        self.gaze_of_fury_utility: CustomSkillUtilityBase = GazeOfFuryUtility(event_bus=self.event_bus, current_build=in_game_build, score_definition=ScoreStaticDefinition(80))
        self.summon_spirit_kurzick: CustomSkillUtilityBase = SummonSpiritUtility(event_bus=self.event_bus, skill=CustomSkill("Summon_Spirits_kurzick"), current_build=in_game_build, score_definition=ScoreStaticDefinition(95))
        self.summon_spirit_luxon: CustomSkillUtilityBase = SummonSpiritUtility(event_bus=self.event_bus, skill=CustomSkill("Summon_Spirits_luxon"), current_build=in_game_build, score_definition=ScoreStaticDefinition(95))

        #optional
        self.painful_bond_utility: CustomSkillUtilityBase = RawAoeAttackUtility(event_bus=self.event_bus, skill=CustomSkill("Painful_Bond"), current_build=in_game_build, mana_required_to_cast=25, score_definition=ScorePerAgentQuantityDefinition(lambda enemy_qte: 40 if enemy_qte >= 3 else 0 if enemy_qte <= 2 else 0))
        self.armor_of_unfeeling_utility: CustomSkillUtilityBase = ArmorOfUnfeelingUtility(event_bus=self.event_bus, current_build=in_game_build, score_definition=ScoreStaticDefinition(35))
        self.breath_of_the_great_dwarf_utility: CustomSkillUtilityBase = BreathOfTheGreatDwarfUtility(event_bus=self.event_bus, current_build=in_game_build, score_definition=ScorePerHealthGravityDefinition(0))
        self.great_dwarf_weapon_utility: CustomSkillUtilityBase = GreatDwarfWeaponUtility(event_bus=self.event_bus, current_build=in_game_build, score_definition=ScoreStaticDefinition(30))
        self.flesh_of_my_flesh_utility: CustomSkillUtilityBase = GenericResurrectionUtility(event_bus=self.event_bus, skill=CustomSkill("Flesh_of_My_Flesh"), current_build=in_game_build,score_definition=ScoreStaticDefinition(12))

        #common
        self.ebon_battle_standard_of_honor_utility: CustomSkillUtilityBase = EbonBattleStandardOfHonorUtility(event_bus=self.event_bus, score_definition=ScorePerAgentQuantityDefinition(lambda enemy_qte: 68 if enemy_qte >= 3 else 50 if enemy_qte <= 2 else 25), current_build=in_game_build,  mana_required_to_cast=15)
        self.ebon_vanguard_assassin_support: CustomSkillUtilityBase = EbonVanguardAssassinSupportUtility(event_bus=self.event_bus, score_definition=ScoreStaticDefinition(71), current_build=in_game_build, mana_required_to_cast=15)
        self.i_am_unstopabble: CustomSkillUtilityBase = IAmUnstoppableUtility(event_bus=self.event_bus, current_build=in_game_build, score_definition=ScoreStaticDefinition(99))
        self.fall_back_utility: CustomSkillUtilityBase = FallBackUtility(event_bus=self.event_bus, current_build=in_game_build)
        self.by_urals_hammer_utility: CustomSkillUtilityBase = ByUralsHammerUtility(event_bus=self.event_bus, current_build=in_game_build)
    
    @property
    @override
    def custom_skills_in_behavior(self) -> list[CustomSkillUtilityBase]:
        return [
            self.signet_of_spirits_utility,
            self.vampirism_utility,
            self.bloodsong_utility,
            self.gaze_of_fury_utility,
            self.summon_spirit_kurzick,
            self.summon_spirit_luxon,
            self.painful_bond_utility,
            self.armor_of_unfeeling_utility,
            self.breath_of_the_great_dwarf_utility,
            self.great_dwarf_weapon_utility,
            self.ebon_battle_standard_of_honor_utility,
            self.ebon_vanguard_assassin_support,
            self.i_am_unstopabble,
            self.fall_back_utility,
            self.flesh_of_my_flesh_utility,
            self.by_urals_hammer_utility,
        ]

    @property
    @override
    def skills_required_in_behavior(self) -> list[CustomSkill]:
        return [
            self.signet_of_spirits_utility.custom_skill,
            self.vampirism_utility.custom_skill,
            self.bloodsong_utility.custom_skill,
            self.gaze_of_fury_utility.custom_skill,
        ]
