from typing import List, Any, Generator, Callable, override
import time
from Widgets.CustomBehaviors.primitives.behavior_state import BehaviorState
from Widgets.CustomBehaviors.primitives.scores.score_per_agent_quantity_definition import ScorePerAgentQuantityDefinition
from Widgets.CustomBehaviors.primitives.scores.score_per_health_gravity_definition import ScorePerHealthGravityDefinition
from Widgets.CustomBehaviors.primitives.scores.score_static_definition import ScoreStaticDefinition
from Widgets.CustomBehaviors.primitives.skillbars.custom_behavior_base_utility import CustomBehaviorBaseUtility
from Widgets.CustomBehaviors.primitives.skills.custom_skill import CustomSkill
from Widgets.CustomBehaviors.primitives.skills.custom_skill_utility_base import CustomSkillUtilityBase
from Widgets.CustomBehaviors.skills.common.auto_attack_utility import AutoAttackUtility
from Widgets.CustomBehaviors.skills.common.ebon_battle_standard_of_wisdom_utility import EbonBattleStandardOfWisdom
from Widgets.CustomBehaviors.skills.common.ebon_vanguard_assassin_support_utility import EbonVanguardAssassinSupportUtility
from Widgets.CustomBehaviors.skills.common.great_dwarf_weapon_utility import GreatDwarfWeaponUtility
from Widgets.CustomBehaviors.skills.common.i_am_unstoppable_utility import IAmUnstoppableUtility
from Widgets.CustomBehaviors.skills.generic.keep_self_effect_up_utility import KeepSelfEffectUpUtility
from Widgets.CustomBehaviors.skills.generic.protective_shout_utility import ProtectiveShoutUtility
from Widgets.CustomBehaviors.skills.monk.infuse_health_utility import InfuseHealthUtility
from Widgets.CustomBehaviors.skills.monk.protective_bond_utility import ProtectiveBondUtility
from Widgets.CustomBehaviors.skills.monk.seed_of_life_utility import SeedOfLifeUtility
from Widgets.CustomBehaviors.skills.monk.spirit_bond_utility import SpiritBondUtility
from Widgets.CustomBehaviors.skills.paragon.fall_back_utility import FallBackUtility
from Widgets.CustomBehaviors.skills.paragon.heroic_refrain_utility import HeroicRefrainUtility

class ElementalistEmo_UtilitySkillBar(CustomBehaviorBaseUtility):

    def __init__(self):
        super().__init__()
        in_game_build = list(self.skillbar_management.get_in_game_build().values())

        #core
        self.ether_renewal_utility: CustomSkillUtilityBase = KeepSelfEffectUpUtility(event_bus=self.event_bus, skill=CustomSkill("Ether_Renewal"), current_build=in_game_build, score_definition=ScoreStaticDefinition(80), allowed_states=[BehaviorState.IN_AGGRO, BehaviorState.CLOSE_TO_AGGRO, BehaviorState.FAR_FROM_AGGRO])
        self.seed_of_life_utility: CustomSkillUtilityBase = SeedOfLifeUtility(event_bus=self.event_bus, current_build=in_game_build, score_definition=ScorePerHealthGravityDefinition(8), mana_required_to_cast=0, allowed_states=[BehaviorState.IN_AGGRO, BehaviorState.CLOSE_TO_AGGRO, BehaviorState.FAR_FROM_AGGRO])
        self.protective_bond_utility: CustomSkillUtilityBase = ProtectiveBondUtility(event_bus=self.event_bus, current_build=in_game_build, score_definition=ScoreStaticDefinition(20))
        self.aura_of_restoration_utility: CustomSkillUtilityBase = KeepSelfEffectUpUtility(event_bus=self.event_bus,
                                                                                     skill=CustomSkill("Aura_of_Restoration"),
                                                                                     current_build=in_game_build,
                                                                                     score_definition=ScoreStaticDefinition(
                                                                                         80), allowed_states=[
                BehaviorState.IN_AGGRO, BehaviorState.CLOSE_TO_AGGRO, BehaviorState.FAR_FROM_AGGRO])
        self.burning_speed_utility: CustomSkillUtilityBase = KeepSelfEffectUpUtility(event_bus=self.event_bus,
                                                                                     skill=CustomSkill("Burning_Speed"),
                                                                                     current_build=in_game_build,
                                                                                     score_definition=ScoreStaticDefinition(
                                                                                         50), mana_required_to_cast=10,allowed_states=[BehaviorState.IN_AGGRO, BehaviorState.CLOSE_TO_AGGRO, BehaviorState.FAR_FROM_AGGRO])
        self.life_attunement_utility: CustomSkillUtilityBase = KeepSelfEffectUpUtility(event_bus=self.event_bus,
                                                                                     skill=CustomSkill("Life_Attunement"),
                                                                                     current_build=in_game_build,
                                                                                     score_definition=ScoreStaticDefinition(
                                                                                         50), mana_required_to_cast=10,
                                                                                     allowed_states=[
                                                                                         BehaviorState.IN_AGGRO,
                                                                                         BehaviorState.CLOSE_TO_AGGRO,
                                                                                         BehaviorState.FAR_FROM_AGGRO])
        self.infuse_health_utility: CustomSkillUtilityBase = InfuseHealthUtility(event_bus=self.event_bus,
                                                                                 score_definition=ScorePerHealthGravityDefinition(10),
                                                                                 current_build=in_game_build)
        #optional

        #common
        self.spirit_bond_utility: CustomSkillUtilityBase = SpiritBondUtility(event_bus=self.event_bus, current_build=in_game_build, mana_required_to_cast=0)
        self.ebon_vanguard_assassin_support: CustomSkillUtilityBase = EbonVanguardAssassinSupportUtility(event_bus=self.event_bus, score_definition=ScoreStaticDefinition(71), current_build=in_game_build, mana_required_to_cast=15)
        self.ebon_battle_standard_of_wisdom: CustomSkillUtilityBase = EbonBattleStandardOfWisdom(event_bus=self.event_bus, score_definition= ScorePerAgentQuantityDefinition(lambda agent_qte: 80 if agent_qte >= 3 else 60 if agent_qte <= 2 else 40), current_build=in_game_build, mana_required_to_cast=18)
        self.i_am_unstopabble: CustomSkillUtilityBase = IAmUnstoppableUtility(event_bus=self.event_bus, current_build=in_game_build, score_definition=ScoreStaticDefinition(99))
        self.fall_back_utility: CustomSkillUtilityBase = FallBackUtility(event_bus=self.event_bus, current_build=in_game_build)
        self.great_dwarf_weapon_utility: CustomSkillUtilityBase = GreatDwarfWeaponUtility(event_bus=self.event_bus,
                                                                                          current_build=in_game_build,
                                                                                          score_definition=ScoreStaticDefinition(
                                                                                              30))


    @property
    @override
    def complete_build_with_generic_skills(self) -> bool:
        return False

    @property
    @override
    def skills_allowed_in_behavior(self) -> list[CustomSkillUtilityBase]:
        return [

            self.ebon_vanguard_assassin_support,
            self.ebon_battle_standard_of_wisdom,
            self.i_am_unstopabble,
            self.fall_back_utility,
            self.aura_of_restoration_utility,
            self.protective_bond_utility,
            self.burning_speed_utility,
            self.seed_of_life_utility,
            self.spirit_bond_utility,
            self.ether_renewal_utility,
            self.life_attunement_utility,
            self.great_dwarf_weapon_utility,
            self.burning_speed_utility,
            self.infuse_health_utility,
        ]

    @property
    @override
    def skills_required_in_behavior(self) -> list[CustomSkill]:
        return [
            self.ether_renewal_utility.custom_skill,
            self.protective_bond_utility.custom_skill,
            self.aura_of_restoration_utility.custom_skill,
            self.infuse_health_utility.custom_skill,
        ]