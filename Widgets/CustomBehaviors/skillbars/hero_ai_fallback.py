from typing import override

from Widgets.CustomBehaviors.primitives.skillbars.custom_behavior_base_utility import CustomBehaviorBaseUtility
from Widgets.CustomBehaviors.primitives.skills.custom_skill import CustomSkill
from Widgets.CustomBehaviors.primitives.skills.custom_skill_utility_base import CustomSkillUtilityBase
from Widgets.CustomBehaviors.primitives.skillbars.utility_skill_finder import discover_all_utility_skills

class HeroAiFallback_UtilitySkillBar(CustomBehaviorBaseUtility):
    """
    Generic fallback skillbar that automatically discovers and uses all custom utility skills.

    This skillbar dynamically scans the skills directory and instantiates all CustomSkillUtilityBase
    subclasses with default parameters, allowing any skill in your build to be used automatically.

    You can override specific skills by defining them in _get_custom_skill_overrides() to provide
    custom score definitions, mana requirements, or other parameters.
    """

    def __init__(self):
        super().__init__()
        in_game_build = list(self.skillbar_management.get_in_game_build().values())

        # Get custom overrides first (if any)
        self._custom_overrides: dict[int, CustomSkillUtilityBase] = self._get_custom_skill_overrides(in_game_build)

        # Dynamically discover and instantiate all custom utility skills
        self._discovered_utilities: dict[int, CustomSkillUtilityBase] = self._discover_all_utility_skills(in_game_build)

    def _get_custom_skill_overrides(self, in_game_build: list[CustomSkill]) -> dict[int, CustomSkillUtilityBase]:
        """
        Override this method to provide custom configurations for specific skills.

        Example:
            return {
                GLOBAL_CACHE.Skill.GetID("Fall_Back"): FallBackUtility(
                    event_bus=self.event_bus,
                    current_build=in_game_build,
                    score_definition=ScoreStaticDefinition(95)  # Custom score
                ),
                GLOBAL_CACHE.Skill.GetID("Ineptitude"): IneptitudeUtility(
                    event_bus=self.event_bus,
                    current_build=in_game_build,
                    score_definition=ScorePerAgentQuantityDefinition(lambda q: 80 if q >= 3 else 50),
                    mana_required_to_cast=10
                ),
            }

        Args:
            in_game_build: The current in-game skill build

        Returns:
            Dictionary mapping skill_id to custom utility instance
        """
        return {}

    def _discover_all_utility_skills(self, in_game_build: list[CustomSkill]) -> dict[int, CustomSkillUtilityBase]:
        """
        Dynamically discovers and instantiates all CustomSkillUtilityBase subclasses from the skills directory.
        Custom overrides take precedence over auto-discovered utilities.

        Args:
            in_game_build: The current in-game skill build

        Returns:
            Dictionary mapping skill_id to instantiated utility skill objects
        """
        return discover_all_utility_skills(
            event_bus=self.event_bus,
            in_game_build=in_game_build,
            custom_overrides=self._custom_overrides
        )

    @property
    @override
    def custom_skills_in_behavior(self) -> list[CustomSkillUtilityBase]:
        return list(self._discovered_utilities.values())

    @property
    @override
    def skills_required_in_behavior(self) -> list[CustomSkill]:
        return [
        ]