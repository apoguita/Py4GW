"""
Utility Skill Finder module for dynamically discovering CustomSkillUtilityBase subclasses.
"""
import importlib
import pkgutil
import inspect

from Sources.oazix.CustomBehaviors.primitives.bus.event_bus import EventBus
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill import CustomSkill
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill_utility_base import CustomSkillUtilityBase
from Sources.oazix.CustomBehaviors.primitives import constants
from Sources.oazix.CustomBehaviors.skills.generic.implementations.generic_utility_skills_list import GenericUtilitySkillsList

# Default skill packages to scan for utility skills
DEFAULT_SKILL_PACKAGES = [
    "Sources.oazix.CustomBehaviors.skills.common",
    "Sources.oazix.CustomBehaviors.skills.generic",
    "Sources.oazix.CustomBehaviors.skills.mesmer",
    "Sources.oazix.CustomBehaviors.skills.elementalist",
    "Sources.oazix.CustomBehaviors.skills.monk",
    "Sources.oazix.CustomBehaviors.skills.necromancer",
    "Sources.oazix.CustomBehaviors.skills.paragon",
    "Sources.oazix.CustomBehaviors.skills.ranger",
    "Sources.oazix.CustomBehaviors.skills.warrior",
    "Sources.oazix.CustomBehaviors.skills.assassin",
    "Sources.oazix.CustomBehaviors.skills.ritualist",
]

def discover_all_utility_skills(
    event_bus: EventBus,
    in_game_build: list[CustomSkill],
    custom_overrides: dict[int, CustomSkillUtilityBase] | None = None,
    debug: bool = False
) -> dict[int, CustomSkillUtilityBase]:
    """
    Dynamically discovers and instantiates all CustomSkillUtilityBase subclasses from the skills directory.
    Custom overrides take precedence over auto-discovered utilities.

    Args:
        event_bus: The event bus for skill communication
        in_game_build: The current in-game skill build
        custom_overrides: Optional dictionary mapping skill_id to custom utility instance
        debug: Whether to print debug information

    Returns:
        Dictionary mapping skill_id to instantiated utility skill objects
    """
    utilities_by_skill_id: dict[int, CustomSkillUtilityBase] = {}

    # First, add all custom overrides
    if custom_overrides:
        for skill_id, custom_utility in custom_overrides.items():
            utilities_by_skill_id[skill_id] = custom_utility

    # Discover utilities from packages
    for package_name in DEFAULT_SKILL_PACKAGES:
        try:
            discovered = __load_utilities_from_package(package_name, event_bus, in_game_build)
            for utility in discovered:
                # Only add if not already overridden
                if utility.custom_skill.skill_id not in utilities_by_skill_id:
                    utilities_by_skill_id[utility.custom_skill.skill_id] = utility
        except Exception as e:
            if debug or constants.DEBUG:
                print(f"Failed to load utilities from {package_name}: {e}")

    # Gather skills from GenericUtilitySkillsList (pre-configured generic utilities)
    try:
        generic_skills = GenericUtilitySkillsList.get_generic_utility_skills_list(event_bus, in_game_build)
        for utility in generic_skills:
            # Only add if not already overridden or discovered
            if utility.custom_skill.skill_id not in utilities_by_skill_id:
                utilities_by_skill_id[utility.custom_skill.skill_id] = utility
    except Exception as e:
        if debug or constants.DEBUG:
            print(f"Failed to load utilities from GenericUtilitySkillsList: {e}")

    if debug or constants.DEBUG:
        override_count = len(custom_overrides) if custom_overrides else 0
        print(f"UtilitySkillFinder discovered {len(utilities_by_skill_id)} utility skills")
        if override_count > 0:
            print(f"  ({override_count} custom overrides)")
        for util in utilities_by_skill_id.values():
            override_marker = " [CUSTOM]" if custom_overrides and util.custom_skill.skill_id in custom_overrides else ""
            print(f"  - {util.custom_skill.skill_name}{override_marker}")

    return utilities_by_skill_id

def __load_utilities_from_package(
    package_name: str,
    event_bus: EventBus,
    in_game_build: list[CustomSkill]
) -> list[CustomSkillUtilityBase]:
    """
    Loads all utility skill classes from a specific package.

    Args:
        package_name: The package to scan
        event_bus: The event bus for skill communication
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
                            utility_instance = __try_instantiate_utility(obj, event_bus, in_game_build)
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

def __try_instantiate_utility(
    utility_class: type,
    event_bus: EventBus,
    in_game_build: list[CustomSkill]
) -> CustomSkillUtilityBase | None:
    """
    Attempts to instantiate a utility skill class with default parameters.

    Args:
        utility_class: The utility class to instantiate
        event_bus: The event bus for skill communication
        in_game_build: The current in-game skill build

    Returns:
        Instantiated utility object or None if instantiation fails
    """
    try:
        # Build kwargs with required parameters
        kwargs = {
            'event_bus': event_bus,
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