# python
# File: `Widgets/CustomBehaviors/skillbars/elementalist_glimmeringmark.py`
from typing import List, override

from Widgets.CustomBehaviors.primitives.behavior_state import BehaviorState
from Widgets.CustomBehaviors.primitives.scores.score_per_agent_quantity_definition import \
    ScorePerAgentQuantityDefinition
from Widgets.CustomBehaviors.primitives.scores.score_static_definition import ScoreStaticDefinition
from Widgets.CustomBehaviors.primitives.skillbars.custom_behavior_base_utility import CustomBehaviorBaseUtility
from Widgets.CustomBehaviors.primitives.skills.custom_skill import CustomSkill
from Widgets.CustomBehaviors.primitives.skills.custom_skill_utility_base import CustomSkillUtilityBase
from Widgets.CustomBehaviors.skills.elementalist.glimmering_mark_utility import GlimmeringMarkUtility
from Widgets.CustomBehaviors.skills.elementalist.chain_lightning_utility import ChainLightningUtility
from Widgets.CustomBehaviors.skills.elementalist.shock_arrow_utility import ShockArrowUtility
from Widgets.CustomBehaviors.skills.generic.preparation_targeted_utility import PreparationTargetedUtility
from Widgets.CustomBehaviors.skills.generic.preparation_utility import PreparationUtility
from Widgets.CustomBehaviors.skills.mesmer.arcane_echo_utility import ArcaneEchoUtility
from Widgets.CustomBehaviors.skills.paragon.fall_back_utility import FallBackUtility
from Widgets.CustomBehaviors.skills.elementalist.shellshock_utility import ShellShockUtility
# from Widgets.CustomBehaviors.skills.generic.preparation_utility import PreparationUtility  # Intensity prep commented out
from Widgets.CustomBehaviors.skills.generic.keep_self_effect_up_utility import KeepSelfEffectUpUtility


class ElementalistGlimmeringMark_UtilitySkillBar(CustomBehaviorBaseUtility):
    """
    Skillbar that provides Glimmering Mark (higher priority), Arcane Echo copy of Glimmering Mark,
    Chain Lightning, Shell Shock, Intensity preparation, maintain skills for elemental_lord_kurzick/elemental_lord_luxon
    and Air Attunement, Shock Arrow and fallback utilities.
    """

    def __init__(self):
        super().__init__()
        in_game_build = list(self.skillbar_management.get_in_game_build().values())

        self.glimmering_mark_utility: GlimmeringMarkUtility = GlimmeringMarkUtility(
            event_bus=self.event_bus,
            current_build=in_game_build,
            score_definition=ScorePerAgentQuantityDefinition(lambda enemy_qte: 84 if enemy_qte >= 3 else 83 if enemy_qte <= 2 else 82),

        )

        # Arcane Echo configured to copy Glimmering Mark (provides a cloned GlimmeringMarkUtility as the copy)
        self.arcane_echo_utility: CustomSkillUtilityBase = ArcaneEchoUtility(
            event_bus=self.event_bus,
            current_build=in_game_build,
            original_skill_to_copy=self.glimmering_mark_utility,
            new_copied_instance=GlimmeringMarkUtility(
                event_bus=self.event_bus,
                current_build=in_game_build,
                score_definition=ScorePerAgentQuantityDefinition(lambda enemy_qte: 85 if enemy_qte >= 3 else 84 if enemy_qte <= 2 else 83),
                mana_required_to_cast=12),
            arcane_echo_score_definition=ScoreStaticDefinition(86))

        self.chain_lightning_utility: ChainLightningUtility = ChainLightningUtility(
            event_bus=self.event_bus,
            current_build=in_game_build
        )

        self.shell_shock_utility: CustomSkillUtilityBase = ShellShockUtility(
            event_bus=self.event_bus,
            current_build=in_game_build,
            score_definition=ScoreStaticDefinition(54),
            mana_required_to_cast=10,
            allowed_states=[BehaviorState.IN_AGGRO]
        )
        self.shock_arrow_utility: CustomSkillUtilityBase = ShockArrowUtility(
            event_bus=self.event_bus,
            current_build=in_game_build,
            score_definition=ScoreStaticDefinition(55),
            mana_required_to_cast=5,
            allowed_states=[BehaviorState.IN_AGGRO]
        )

        # PreparationTargetedUtility that casts Shell Shock first, then Shock Arrow on same target
        self.prep_shellshock_then_shockarrow: CustomSkillUtilityBase = PreparationTargetedUtility(
            event_bus=self.event_bus,
            prep_utility=self.shell_shock_utility,                # first cast Shell Shock
            followup_skill=CustomSkill("Shock_Arrow"),            # then cast Shock Arrow
            target_utilities=[self.shell_shock_utility, self.shock_arrow_utility],  # utilities that can provide targets
            current_build=in_game_build,
            score_definition=ScoreStaticDefinition(60),
            mana_required_to_cast=0,
            allowed_states=[BehaviorState.IN_AGGRO]
        )

        # Preparation: Intensity should only be cast when a follow-up is available.
        # Priority: Chain Lightning first, Shell Shock second.
        # Intensity prep disabled for debugging:
        self.intensity_prep_utility: CustomSkillUtilityBase = PreparationUtility(
             event_bus=self.event_bus,
             prep_skill=CustomSkill("Intensity"),
             target_utilities=[self.chain_lightning_utility, self.shell_shock_utility],
             current_build=in_game_build,
             score_definition=ScoreStaticDefinition(68),
             mana_required_to_cast=0,
             allowed_states=[BehaviorState.IN_AGGRO]
         )

        # Maintain / self-effect skills - used in all behavior states
        # NOTE: skill ids are case-sensitive; use exact names.
        self.elemental_lord_kurzick_utility: CustomSkillUtilityBase = KeepSelfEffectUpUtility(
            event_bus=self.event_bus,
            skill=CustomSkill("Elemental_Lord_kurzick"),
            current_build=in_game_build,
            score_definition=ScoreStaticDefinition(70),
            mana_required_to_cast=10,
            allowed_states=[BehaviorState.IN_AGGRO, BehaviorState.CLOSE_TO_AGGRO, BehaviorState.FAR_FROM_AGGRO]
        )

        self.elemental_lord_luxon_utility: CustomSkillUtilityBase = KeepSelfEffectUpUtility(
            event_bus=self.event_bus,
            skill=CustomSkill("Elemental_Lord_luxon"),
            current_build=in_game_build,
            score_definition=ScoreStaticDefinition(70),
            mana_required_to_cast=10,
            allowed_states=[BehaviorState.IN_AGGRO, BehaviorState.CLOSE_TO_AGGRO, BehaviorState.FAR_FROM_AGGRO]
        )

        self.air_attunement_utility: CustomSkillUtilityBase = KeepSelfEffectUpUtility(
            event_bus=self.event_bus,
            skill=CustomSkill("Air_Attunement"),
            current_build=in_game_build,
            score_definition=ScoreStaticDefinition(70),
            mana_required_to_cast=10,
            allowed_states=[BehaviorState.IN_AGGRO, BehaviorState.CLOSE_TO_AGGRO, BehaviorState.FAR_FROM_AGGRO]
        )

        self.fall_back_utility: CustomSkillUtilityBase = FallBackUtility(event_bus=self.event_bus, current_build=in_game_build)

    @property
    @override
    def skills_allowed_in_behavior(self) -> list[CustomSkillUtilityBase]:
        return [
            self.fall_back_utility,
            self.arcane_echo_utility,
            self.elemental_lord_kurzick_utility,
            self.elemental_lord_luxon_utility,
            self.air_attunement_utility,
            self.glimmering_mark_utility,
            self.shock_arrow_utility,      # added Shock Arrow to allowed skills
            self.intensity_prep_utility,  # Intensity temporarily disabled
            self.chain_lightning_utility,
            self.prep_shellshock_then_shockarrow,
        ]

    @property
    @override
    def skills_required_in_behavior(self) -> list[CustomSkill]:
        return [
            self.glimmering_mark_utility.custom_skill,
        ]
