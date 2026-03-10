from typing import override

from Sources.oazix.CustomBehaviors.primitives.behavior_state import BehaviorState
from Sources.oazix.CustomBehaviors.primitives.scores.score_per_agent_quantity_definition import ScorePerAgentQuantityDefinition
from Sources.oazix.CustomBehaviors.primitives.scores.score_static_definition import ScoreStaticDefinition
from Sources.oazix.CustomBehaviors.primitives.skillbars.custom_behavior_base_utility import CustomBehaviorBaseUtility
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill import CustomSkill
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill_utility_base import CustomSkillUtilityBase
from Sources.oazix.CustomBehaviors.skills.common.by_urals_hammer_utility import ByUralsHammerUtility
from Sources.oazix.CustomBehaviors.skills.common.ebon_battle_standard_of_honor_utility import EbonBattleStandardOfHonorUtility
from Sources.oazix.CustomBehaviors.skills.common.ebon_vanguard_assassin_support_utility import EbonVanguardAssassinSupportUtility
from Sources.oazix.CustomBehaviors.skills.common.i_am_unstoppable_utility import IAmUnstoppableUtility
from Sources.oazix.CustomBehaviors.skills.generic.auto_combat_utility import AutoCombatUtility
from Sources.oazix.CustomBehaviors.skills.generic.keep_self_effect_up_utility import KeepSelfEffectUpUtility
from Sources.oazix.CustomBehaviors.skills.generic.raw_aoe_attack_utility import RawAoeAttackUtility
from Sources.oazix.CustomBehaviors.skills.ranger.comfort_animal_utility import ComfortAnimalUtility


class WarriorSevenWeaponsAxe_UtilitySkillBar(CustomBehaviorBaseUtility):
    def __init__(self):
        super().__init__()
        in_game_build = list(self.skillbar_management.get_in_game_build().values())

        # Core stance upkeep
        self.seven_weapons_stance_utility: CustomSkillUtilityBase = KeepSelfEffectUpUtility(
            event_bus=self.event_bus,
            skill=CustomSkill("Seven_Weapons_Stance"),
            current_build=in_game_build,
            score_definition=ScoreStaticDefinition(96),
            allowed_states=[BehaviorState.IN_AGGRO, BehaviorState.CLOSE_TO_AGGRO],
        )

        # Common support for this archetype
        self.for_great_justice_utility: CustomSkillUtilityBase = KeepSelfEffectUpUtility(
            event_bus=self.event_bus,
            skill=CustomSkill("For_Great_Justice"),
            current_build=in_game_build,
            score_definition=ScoreStaticDefinition(92),
            allowed_states=[BehaviorState.IN_AGGRO, BehaviorState.CLOSE_TO_AGGRO],
        )

        # Core axe attacks
        self.dismember_utility: CustomSkillUtilityBase = AutoCombatUtility(
            event_bus=self.event_bus,
            skill=CustomSkill("Dismember"),
            current_build=in_game_build,
            score_definition=ScoreStaticDefinition(74),
        )
        self.axe_rake_utility: CustomSkillUtilityBase = AutoCombatUtility(
            event_bus=self.event_bus,
            skill=CustomSkill("Axe_Rake"),
            current_build=in_game_build,
            score_definition=ScoreStaticDefinition(70),
        )

        # Optional skills requested
        self.executioners_strike_utility: CustomSkillUtilityBase = AutoCombatUtility(
            event_bus=self.event_bus,
            skill=CustomSkill("Executioners_Strike"),
            current_build=in_game_build,
            score_definition=ScoreStaticDefinition(69),
        )
        self.endure_pain_utility: CustomSkillUtilityBase = KeepSelfEffectUpUtility(
            event_bus=self.event_bus,
            skill=CustomSkill("Endure_Pain"),
            current_build=in_game_build,
            score_definition=ScoreStaticDefinition(80),
            allowed_states=[BehaviorState.IN_AGGRO, BehaviorState.CLOSE_TO_AGGRO],
        )
        self.whirlwind_attack_utility: CustomSkillUtilityBase = RawAoeAttackUtility(
            event_bus=self.event_bus,
            skill=CustomSkill("Whirlwind_Attack"),
            current_build=in_game_build,
            score_definition=ScorePerAgentQuantityDefinition(lambda enemy_qte: 69 if enemy_qte >= 3 else 63 if enemy_qte == 2 else 0),
            mana_required_to_cast=0,
        )
        self.cyclone_axe_utility: CustomSkillUtilityBase = RawAoeAttackUtility(
            event_bus=self.event_bus,
            skill=CustomSkill("Cyclone_Axe"),
            current_build=in_game_build,
            score_definition=ScorePerAgentQuantityDefinition(lambda enemy_qte: 68 if enemy_qte >= 3 else 62 if enemy_qte == 2 else 0),
            mana_required_to_cast=0,
        )
        self.comfort_animal_utility: CustomSkillUtilityBase = ComfortAnimalUtility(
            event_bus=self.event_bus,
            current_build=in_game_build,
            score_definition=ScoreStaticDefinition(82),
        )
        self.call_of_protection_utility: CustomSkillUtilityBase = KeepSelfEffectUpUtility(
            event_bus=self.event_bus,
            skill=CustomSkill("Call_of_Protection"),
            current_build=in_game_build,
            score_definition=ScoreStaticDefinition(65),
            allowed_states=[BehaviorState.IN_AGGRO, BehaviorState.CLOSE_TO_AGGRO],
        )

        # Common PvE optionals
        self.ebon_vanguard_assassin_support: CustomSkillUtilityBase = EbonVanguardAssassinSupportUtility(
            event_bus=self.event_bus,
            score_definition=ScoreStaticDefinition(66),
            current_build=in_game_build,
            mana_required_to_cast=15,
        )
        self.ebon_battle_standard_of_honor_utility: CustomSkillUtilityBase = EbonBattleStandardOfHonorUtility(
            event_bus=self.event_bus,
            score_definition=ScorePerAgentQuantityDefinition(lambda agent_qte: 45 if agent_qte >= 3 else 35 if agent_qte <= 2 else 25),
            current_build=in_game_build,
            mana_required_to_cast=15,
        )
        self.i_am_unstopabble: CustomSkillUtilityBase = IAmUnstoppableUtility(
            event_bus=self.event_bus,
            current_build=in_game_build,
            score_definition=ScoreStaticDefinition(99),
        )
        self.by_urals_hammer_utility: CustomSkillUtilityBase = ByUralsHammerUtility(
            event_bus=self.event_bus,
            current_build=in_game_build,
        )

    @property
    @override
    def custom_skills_in_behavior(self) -> list[CustomSkillUtilityBase]:
        return [
            self.seven_weapons_stance_utility,
            self.for_great_justice_utility,
            self.dismember_utility,
            self.axe_rake_utility,
            self.executioners_strike_utility,
            self.endure_pain_utility,
            self.whirlwind_attack_utility,
            self.cyclone_axe_utility,
            self.comfort_animal_utility,
            self.call_of_protection_utility,
            self.ebon_vanguard_assassin_support,
            self.ebon_battle_standard_of_honor_utility,
            self.i_am_unstopabble,
            self.by_urals_hammer_utility,
        ]

    @property
    @override
    def skills_required_in_behavior(self) -> list[CustomSkill]:
        return [
            self.seven_weapons_stance_utility.custom_skill,
        ]
