from typing import List, Any, Generator, Callable, override
import time
from Py4GWCoreLib.enums import SpiritModelID
from Widgets.CustomBehaviors.primitives.behavior_state import BehaviorState
from Widgets.CustomBehaviors.primitives.scores.score_per_agent_quantity_definition import ScorePerAgentQuantityDefinition
from Widgets.CustomBehaviors.primitives.scores.score_per_health_gravity_definition import ScorePerHealthGravityDefinition
from Widgets.CustomBehaviors.primitives.scores.score_static_definition import ScoreStaticDefinition
from Widgets.CustomBehaviors.primitives.skillbars.custom_behavior_base_utility import CustomBehaviorBaseUtility
from Widgets.CustomBehaviors.primitives.skills.custom_skill import CustomSkill
from Widgets.CustomBehaviors.primitives.skills.custom_skill_utility_base import CustomSkillUtilityBase
from Widgets.CustomBehaviors.skills.common.auto_attack_utility import AutoAttackUtility
from Widgets.CustomBehaviors.skills.common.breath_of_the_great_dwarf_utility import BreathOfTheGreatDwarfUtility
from Widgets.CustomBehaviors.skills.common.ebon_battle_standard_of_wisdom_utility import EbonBattleStandardOfWisdom
from Widgets.CustomBehaviors.skills.common.ebon_vanguard_assassin_support_utility import EbonVanguardAssassinSupportUtility
from Widgets.CustomBehaviors.skills.common.great_dwarf_weapon_utility import GreatDwarfWeaponUtility
from Widgets.CustomBehaviors.skills.common.i_am_unstoppable_utility import IAmUnstoppableUtility
from Widgets.CustomBehaviors.skills.generic.hero_ai_utility import HeroAiUtility
from Widgets.CustomBehaviors.skills.generic.keep_self_effect_up_utility import KeepSelfEffectUpUtility
from Widgets.CustomBehaviors.skills.generic.protective_spirit_utility import ProtectiveSpiritUtility
from Widgets.CustomBehaviors.skills.monk.strength_of_honor_utility import StrengthOfHonorUtility
from Widgets.CustomBehaviors.skills.necromancer.blood_bond_utility import BloodBondUtility
from Widgets.CustomBehaviors.skills.necromancer.blood_is_power_utility import BloodIsPowerUtility
from Widgets.CustomBehaviors.skills.paragon.fall_back_utility import FallBackUtility
from Widgets.CustomBehaviors.skills.ritualist.armor_of_unfeeling_utility import ArmorOfUnfeelingUtility
from Widgets.CustomBehaviors.skills.ritualist.mend_body_and_soul_utility import MendBodyAndSoulUtility
from Widgets.CustomBehaviors.skills.ritualist.protective_was_kaolai_utility import ProtectiveWasKaolaiUtility
from Widgets.CustomBehaviors.skills.ritualist.soothing_memories_utility import SoothingMemoriesUtility
from Widgets.CustomBehaviors.skills.ritualist.spirit_light_utility import SpiritLightUtility
from Widgets.CustomBehaviors.skills.ritualist.summon_spirit_utility import SummonSpiritUtility

class NecromancerBipRestoration_UtilitySkillBar(CustomBehaviorBaseUtility):

    def __init__(self):
        super().__init__()
        in_game_build = list(self.skillbar_management.get_in_game_build().values())
        self.auto_attack: CustomSkillUtilityBase = AutoAttackUtility(current_build=in_game_build)

        # core skills
        self.blood_is_power_utility: CustomSkillUtilityBase = BloodIsPowerUtility(current_build=in_game_build, score_definition=ScoreStaticDefinition(33))
        self.great_dwarf_weapon_utility: CustomSkillUtilityBase = GreatDwarfWeaponUtility(current_build=in_game_build, score_definition=ScoreStaticDefinition(30), mana_required_to_cast=10)

        self.breath_of_the_great_dwarf_utility: CustomSkillUtilityBase = BreathOfTheGreatDwarfUtility(current_build=in_game_build, score_definition=ScorePerHealthGravityDefinition(9))
        self.spirit_light_utility: CustomSkillUtilityBase = SpiritLightUtility(current_build=in_game_build, score_definition=ScorePerHealthGravityDefinition(8))
        self.mend_body_and_soul_utility: CustomSkillUtilityBase = MendBodyAndSoulUtility(current_build=in_game_build, score_definition=ScorePerHealthGravityDefinition(7))
        self.soothing_memories_utility: CustomSkillUtilityBase = SoothingMemoriesUtility(current_build=in_game_build, score_definition=ScorePerHealthGravityDefinition(6))
        self.protective_was_kaolai_utility: CustomSkillUtilityBase = ProtectiveWasKaolaiUtility(current_build=in_game_build, score_definition=ScorePerHealthGravityDefinition(5))

        # optional
        self.flesh_of_my_flesh_utility: CustomSkillUtilityBase = HeroAiUtility(skill=CustomSkill("Flesh_of_My_Flesh"), current_build=in_game_build)
        self.blood_bond_utility: CustomSkillUtilityBase = BloodBondUtility(current_build=in_game_build, score_definition=ScorePerAgentQuantityDefinition(lambda enemy_qte: 25 if enemy_qte >= 2 else 0), mana_required_to_cast=15)

        # common
        self.ebon_vanguard_assassin_support: CustomSkillUtilityBase = EbonVanguardAssassinSupportUtility(score_definition=ScoreStaticDefinition(71), current_build=in_game_build, mana_required_to_cast=15)
        self.ebon_battle_standard_of_wisdom: CustomSkillUtilityBase = EbonBattleStandardOfWisdom(score_definition= ScorePerAgentQuantityDefinition(lambda agent_qte: 80 if agent_qte >= 3 else 60 if agent_qte <= 2 else 40), current_build=in_game_build, mana_required_to_cast=18)
        self.i_am_unstopabble: CustomSkillUtilityBase = IAmUnstoppableUtility(current_build=in_game_build, score_definition=ScoreStaticDefinition(99))
        self.fall_back_utility: CustomSkillUtilityBase = FallBackUtility(current_build=in_game_build)
    

    @property
    @override
    def additional_autonomous_skills(self) -> list[CustomSkillUtilityBase]:
        return [
            self.auto_attack,
        ]

    @property
    @override
    def complete_build_with_generic_skills(self) -> bool:
        return False # because I'm playing it myself
    
    @property
    @override
    def skills_allowed_in_behavior(self) -> list[CustomSkillUtilityBase]:
        return [
            self.blood_is_power_utility,
            self.great_dwarf_weapon_utility,
            self.breath_of_the_great_dwarf_utility,
            self.spirit_light_utility,
            self.mend_body_and_soul_utility,
            self.soothing_memories_utility,
            self.protective_was_kaolai_utility, 
            self.flesh_of_my_flesh_utility,
            self.blood_bond_utility,
            self.ebon_vanguard_assassin_support,
            self.ebon_battle_standard_of_wisdom,
            self.i_am_unstopabble,
            self.fall_back_utility,
        ]

    @property
    @override
    def skills_required_in_behavior(self) -> list[CustomSkill]:
        return [
            self.blood_is_power_utility.custom_skill,
            self.spirit_light_utility.custom_skill,
            self.mend_body_and_soul_utility.custom_skill,
        ]