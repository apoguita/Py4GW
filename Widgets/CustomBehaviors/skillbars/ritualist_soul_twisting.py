from typing import override

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
from Widgets.CustomBehaviors.skills.paragon.fall_back_utility import FallBackUtility
from Widgets.CustomBehaviors.skills.ritualist.armor_of_unfeeling_utility import ArmorOfUnfeelingUtility
from Widgets.CustomBehaviors.skills.ritualist.summon_spirit_utility import SummonSpiritUtility

class RitualistSoulTwisting_UtilitySkillBar(CustomBehaviorBaseUtility):

    def __init__(self):
        super().__init__()
        in_game_build = list(self.skillbar_management.get_in_game_build().values())

        # core skills
        self.soul_twisting_utility: CustomSkillUtilityBase = KeepSelfEffectUpUtility(skill=CustomSkill("Soul_Twisting"), current_build=in_game_build, score_definition=ScoreStaticDefinition(95), allowed_states=[BehaviorState.IN_AGGRO, BehaviorState.CLOSE_TO_AGGRO])
        self.boon_of_creation_utility: CustomSkillUtilityBase = KeepSelfEffectUpUtility(skill=CustomSkill("Boon_of_Creation"), current_build=in_game_build, score_definition=ScoreStaticDefinition(85), renew_before_expiration_in_milliseconds=1800, allowed_states=[BehaviorState.IN_AGGRO, BehaviorState.CLOSE_TO_AGGRO, BehaviorState.FAR_FROM_AGGRO])
        self.shelter_utility: CustomSkillUtilityBase = ProtectiveSpiritUtility(skill=CustomSkill("Shelter"), current_build=in_game_build, score_definition=ScoreStaticDefinition(66), owned_spirit_model_id=SpiritModelID.SHELTER)
        self.union_utility: CustomSkillUtilityBase = ProtectiveSpiritUtility(skill=CustomSkill("Union"), current_build=in_game_build, score_definition=ScoreStaticDefinition(65), owned_spirit_model_id=SpiritModelID.UNION)
        self.displacement_utility: CustomSkillUtilityBase = ProtectiveSpiritUtility(skill=CustomSkill("Displacement"), current_build=in_game_build, score_definition=ScoreStaticDefinition(64), owned_spirit_model_id=SpiritModelID.DISPLACEMENT)
        self.summon_spirit_kurzick: CustomSkillUtilityBase = SummonSpiritUtility(skill=CustomSkill("Summon_Spirits_kurzick"), current_build=in_game_build, score_definition=ScoreStaticDefinition(95))
        self.summon_spirit_luxon: CustomSkillUtilityBase = SummonSpiritUtility(skill=CustomSkill("Summon_Spirits_luxon"), current_build=in_game_build, score_definition=ScoreStaticDefinition(95))
        self.armor_of_unfeeling_utility: CustomSkillUtilityBase = ArmorOfUnfeelingUtility(current_build=in_game_build, score_definition=ScoreStaticDefinition(80))

        # optional
        self.breath_of_the_great_dwarf_utility: CustomSkillUtilityBase = BreathOfTheGreatDwarfUtility(current_build=in_game_build, score_definition=ScorePerHealthGravityDefinition(0))
        self.flesh_of_my_flesh_utility: CustomSkillUtilityBase = HeroAiUtility(skill=CustomSkill("Flesh_of_My_Flesh"), current_build=in_game_build)
        self.strength_of_honor_utility: CustomSkillUtilityBase = StrengthOfHonorUtility(current_build=in_game_build, score_definition=ScoreStaticDefinition(20))
        self.great_dwarf_weapon_utility: CustomSkillUtilityBase = GreatDwarfWeaponUtility(current_build=in_game_build, score_definition=ScoreStaticDefinition(30), mana_required_to_cast=10)

        # common
        self.ebon_vanguard_assassin_support: CustomSkillUtilityBase = EbonVanguardAssassinSupportUtility(score_definition=ScoreStaticDefinition(71), current_build=in_game_build, mana_required_to_cast=15)
        self.ebon_battle_standard_of_wisdom: CustomSkillUtilityBase = EbonBattleStandardOfWisdom(score_definition= ScorePerAgentQuantityDefinition(lambda agent_qte: 80 if agent_qte >= 3 else 60 if agent_qte <= 2 else 40), current_build=in_game_build, mana_required_to_cast=18)
        self.i_am_unstopabble: CustomSkillUtilityBase = IAmUnstoppableUtility(current_build=in_game_build, score_definition=ScoreStaticDefinition(99))
        self.fall_back_utility: CustomSkillUtilityBase = FallBackUtility(current_build=in_game_build)
        self.spirits_gift_utility: CustomSkillUtilityBase = KeepSelfEffectUpUtility(skill=CustomSkill("Spirits_Gift"), current_build=in_game_build, score_definition=ScoreStaticDefinition(75), allowed_states=[BehaviorState.IN_AGGRO, BehaviorState.CLOSE_TO_AGGRO])
    
    @property
    @override
    def complete_build_with_generic_skills(self) -> bool:
        return False # because I'm playing it myself
    
    @property
    @override
    def skills_allowed_in_behavior(self) -> list[CustomSkillUtilityBase]:
        return [
            self.soul_twisting_utility,
            self.boon_of_creation_utility,
            self.shelter_utility,
            self.union_utility,
            self.displacement_utility,
            self.summon_spirit_kurzick,
            self.summon_spirit_luxon,
            self.armor_of_unfeeling_utility,
            self.breath_of_the_great_dwarf_utility,
            self.flesh_of_my_flesh_utility,
            self.strength_of_honor_utility,
            self.ebon_vanguard_assassin_support,
            self.ebon_battle_standard_of_wisdom,
            self.i_am_unstopabble,
            self.fall_back_utility,
            self.great_dwarf_weapon_utility,
            self.spirits_gift_utility,
        ]

    @property
    @override
    def skills_required_in_behavior(self) -> list[CustomSkill]:
        return [
            self.soul_twisting_utility.custom_skill,
            self.shelter_utility.custom_skill,
            self.union_utility.custom_skill,
        ]
