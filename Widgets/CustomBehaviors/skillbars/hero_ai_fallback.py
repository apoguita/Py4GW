from typing import List, Any, Generator, Callable, override
import time
import importlib
import pkgutil
import inspect

from Widgets.CustomBehaviors.primitives.skillbars.custom_behavior_base_utility import CustomBehaviorBaseUtility
from Widgets.CustomBehaviors.primitives.skills.custom_skill import CustomSkill
from Widgets.CustomBehaviors.primitives.skills.custom_skill_utility_base import CustomSkillUtilityBase
from Widgets.CustomBehaviors.primitives import constants


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
        self._discovered_utilities: list[CustomSkillUtilityBase] = self._discover_all_utility_skills(in_game_build)

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

    def _discover_all_utility_skills(self, in_game_build: list[CustomSkill]) -> list[CustomSkillUtilityBase]:
        """
        Dynamically discovers and instantiates all CustomSkillUtilityBase subclasses from the skills directory.
        Custom overrides take precedence over auto-discovered utilities.

        Args:
            in_game_build: The current in-game skill build

        Returns:
            List of instantiated utility skill objects
        """
        utilities = []
        utilities_by_skill_id: dict[int, CustomSkillUtilityBase] = {}

        # First, add all custom overrides
        for skill_id, custom_utility in self._custom_overrides.items():
            utilities_by_skill_id[skill_id] = custom_utility

        # Directories to scan for utility skills
        skill_packages = [
            "Widgets.CustomBehaviors.skills.common",
            "Widgets.CustomBehaviors.skills.generic",
            "Widgets.CustomBehaviors.skills.mesmer",
            "Widgets.CustomBehaviors.skills.elementalist",
            "Widgets.CustomBehaviors.skills.monk",
            "Widgets.CustomBehaviors.skills.necromancer",
            "Widgets.CustomBehaviors.skills.paragon",
            "Widgets.CustomBehaviors.skills.ranger",
            "Widgets.CustomBehaviors.skills.warrior",
            "Widgets.CustomBehaviors.skills.assassin",
            "Widgets.CustomBehaviors.skills.ritualist",
        ]

        # Discover utilities from packages
        for package_name in skill_packages:
            try:
                discovered = self._load_utilities_from_package(package_name, in_game_build)
                for utility in discovered:
                    # Only add if not already overridden
                    if utility.custom_skill.skill_id not in utilities_by_skill_id:
                        utilities_by_skill_id[utility.custom_skill.skill_id] = utility
            except Exception as e:
                if constants.DEBUG:
                    print(f"Failed to load utilities from {package_name}: {e}")

        # Convert to list
        utilities = list(utilities_by_skill_id.values())

        if constants.DEBUG:
            print(f"HeroAiFallback discovered {len(utilities)} utility skills")
            override_count = len(self._custom_overrides)
            if override_count > 0:
                print(f"  ({override_count} custom overrides)")
            for util in utilities:
                override_marker = " [CUSTOM]" if util.custom_skill.skill_id in self._custom_overrides else ""
                print(f"  - {util.custom_skill.skill_name}{override_marker}")

        return utilities

    def _load_utilities_from_package(self, package_name: str, in_game_build: list[CustomSkill]) -> list[CustomSkillUtilityBase]:
        """
        Loads all utility skill classes from a specific package.

        Args:
            package_name: The package to scan
            in_game_build: The current in-game skill build

        Returns:
            List of instantiated utility skill objects from this package
        """
        utilities = []

        try:
            # Import the package
            package = importlib.import_module(package_name)

            # Iterate over all modules in the package
            for module_info in pkgutil.iter_modules(package.__path__):
                module_name = f"{package_name}.{module_info.name}"

                try:
                    # Dynamically import the module
                    module = importlib.import_module(module_name)

                    # Find all classes in the module
                    for name, obj in inspect.getmembers(module, inspect.isclass):
                        # Check if it's a subclass of CustomSkillUtilityBase (but not the base class itself)
                        if (issubclass(obj, CustomSkillUtilityBase) and
                            obj != CustomSkillUtilityBase and
                            obj.__module__ == module_name):  # Only classes defined in this module

                            # Try to instantiate with default parameters
                            try:
                                utility_instance = self._try_instantiate_utility(obj, in_game_build)
                                if utility_instance:
                                    utilities.append(utility_instance)
                            except Exception as e:
                                if constants.DEBUG:
                                    print(f"Failed to instantiate {name}: {e}")

                except ImportError as e:
                    if constants.DEBUG:
                        print(f"Failed to import module {module_name}: {e}")

        except ImportError as e:
            if constants.DEBUG:
                print(f"Failed to import package {package_name}: {e}")

        return utilities

    def _try_instantiate_utility(self, utility_class: type, in_game_build: list[CustomSkill]) -> CustomSkillUtilityBase | None:
        """
        Attempts to instantiate a utility skill class with default parameters.

        Args:
            utility_class: The utility class to instantiate
            in_game_build: The current in-game skill build

        Returns:
            Instantiated utility object or None if instantiation fails
        """
        try:
            # Build kwargs with required parameters
            kwargs = {
                'event_bus': self.event_bus,
                'current_build': in_game_build,
            }

            # Try to instantiate
            return utility_class(**kwargs)

        except TypeError as e:
            # Some utilities need a 'skill' parameter - skip those (they're generic wrappers)
            # Examples: GenericResurrectionUtility, KeepSelfEffectUpUtility, RawAoeAttackUtility
            if 'skill' in str(e):
                return None
            if constants.DEBUG:
                print(f"Could not instantiate {utility_class.__name__}: {e}")
            return None
        except Exception as e:
            if constants.DEBUG:
                print(f"Could not instantiate {utility_class.__name__} with default params: {e}")
            return None

    @property
    @override
    def skills_allowed_in_behavior(self) -> list[CustomSkillUtilityBase]:
        return self._discovered_utilities

    @property
    @override
    def skills_required_in_behavior(self) -> list[CustomSkill]:
        return [
        ]