import inspect
import importlib
import pkgutil
from typing import Generator, Any, List

from Sources.oazix.CustomBehaviors.primitives import constants

from Sources.oazix.CustomBehaviors.primitives.bus.event_bus import EventBus
from Sources.oazix.CustomBehaviors.primitives.bus.stub_event_bus import StubEventBus
from Sources.oazix.CustomBehaviors.primitives.skillbars.custom_behavior_base_utility import CustomBehaviorBaseUtility
from Sources.oazix.CustomBehaviors.skillbars.autocombat_fallback import AutoCombatFallback_UtilitySkillBar

class MatchResult:
    def __init__(self, build_size: int, matching_count: int, instance: CustomBehaviorBaseUtility, is_matched_with_current_build: bool):
        self.build_size = build_size
        self.matching_count: int = matching_count
        self.matching_result = build_size - matching_count
        self.is_matched_with_current_build: bool = is_matched_with_current_build
        self.instance: CustomBehaviorBaseUtility = instance

class CustomBehaviorLoader:
    _instance = None  # Singleton instance

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(CustomBehaviorLoader, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if not self._initialized:
            self.custom_combat_behavior:CustomBehaviorBaseUtility | None = None
            self._has_loaded = False
            self.__behaviors_found:list[MatchResult] = []
            self._initialized = True
            # Botting daemon state - stores FSM and factory for re-registration after FSM restart
            self._botting_daemon_fsm = None
            self._botting_daemon_factory = None

    # internal

    def __find_subclasses_in_folder(self, base_class, package_name: str) -> list[type]:
        """
        Finds all direct subclasses of `base_class` within the given package.
        Excludes utility classes and non-direct children.

        Args:
            base_class: The base class to search for.
            package_name: The package name where the search should happen.

        Returns:
            A list of direct subclasses of the base_class.
        """

        def __load_all_modules_in_folder(full_package_name: str):
            """
            Dynamically loads all modules in the given package.

            Args:
                full_package_name: The dot-separated name of the package (e.g., 'HeroAI.custom_combat_behavior').

            Returns:
                A list of `ModuleType` objects representing the loaded modules.
            """
            loaded_modules = []

            # Get the package object (to resolve its __path__)
            package = importlib.import_module(full_package_name)

            # Iterate over all modules in the package
            for module_info in pkgutil.iter_modules(package.__path__):
                module_name = f"{full_package_name}.{module_info.name}"  # Full dotted module name

                try:
                    # Dynamically import the module
                    module = importlib.import_module(module_name)
                    if constants.DEBUG: print(f"Loaded module: {module.__name__}")
                    loaded_modules.append(module)
                except ImportError as e:
                    print(f"Failed to import module {module_name}: {e}")

            return loaded_modules

        subclasses = []
        modules = __load_all_modules_in_folder(package_name)

        if constants.DEBUG:
            print(f"\nSearching for subclasses of {base_class.__name__}")
            for module in modules:
                print(f"Module: {module.__name__}")

        for module in modules:
            # Inspect module contents for subclasses
            for name, obj in inspect.getmembers(module):
                
                if("_UtilitySkillBar" in name):
                    if constants.DEBUG: print(f"Found subclass: {obj.__name__}")
                    subclasses.append(obj)
                    break

        if constants.DEBUG: print(f"Total subclasses found: {len(subclasses)}")

        return subclasses

    def __find_and_order_custom_behaviors(self) -> List[MatchResult]:
        
        subclasses: list[type] = self.__find_subclasses_in_folder(CustomBehaviorBaseUtility, "Sources.oazix.CustomBehaviors.skillbars")
        matches: List[MatchResult] = []

        for subclass in subclasses:
            try:
                if constants.DEBUG: print(f"Checking subclass: {subclass.__name__} (defined in {subclass.__module__})")

                # Create temporary instance with StubEventBus ONLY for matching check
                instance: CustomBehaviorBaseUtility = subclass(StubEventBus())

                build_size = len(instance.skills_required_in_behavior)
                if constants.DEBUG: print(f"build_size: {build_size}")
                matching_count = instance.count_matches_between_custom_behavior_and_in_game_build()
                if constants.DEBUG: print(f"matching_count: {matching_count}")

                if matching_count == build_size:
                    if constants.DEBUG: print(f"Found custom behavior: {subclass.__name__} (defined in {subclass.__module__})")
                    is_matched_with_current_build = True if matching_count > 0 else False
                    matches.append(MatchResult(build_size=build_size, matching_count=matching_count, instance=instance, is_matched_with_current_build=is_matched_with_current_build))
                else:
                    if constants.DEBUG: print(f"{subclass.__name__} (defined in {subclass.__module__} - Custom behavior does not match in-game build.")
                    matches.append(MatchResult(build_size=build_size, matching_count=matching_count, instance=instance, is_matched_with_current_build=False))

            except Exception as e:
                # if there are errors on buildign out a skill bar class load the other classes but log the errors that prevented this one from loading
                print(f"Exception loading subclass: {e}")
                raise e

        matches = sorted(matches, key=lambda x: (x.matching_result, -x.matching_count))
        return matches

    # public

    def initialize_custom_behavior_candidate(self):

        if self._has_loaded:
            return False
        
        self.__behaviors_found: list[MatchResult] = self.__find_and_order_custom_behaviors()
        __behaviors_candidates = [behavior for behavior in self.__behaviors_found if behavior.is_matched_with_current_build]
        result: CustomBehaviorBaseUtility | None = __behaviors_candidates[0].instance if len(__behaviors_candidates) > 0 else None

        if result is not None:
            if constants.DEBUG: print(f"custom behavior instance {result.__class__.__name__} affected")
            # let's recreate the instance with a real event bus
            result_with_real_event_bus: CustomBehaviorBaseUtility | None = result.__class__(EventBus())
            self.custom_combat_behavior = result_with_real_event_bus
            self.custom_combat_behavior.enable()
        else:
            if constants.DEBUG: print(f"no custom behavior found, fallback to generic skillbar.")
            self.custom_combat_behavior = AutoCombatFallback_UtilitySkillBar(EventBus())
            self.custom_combat_behavior.enable()

        self._has_loaded = True
        return True

    def refresh_custom_behavior_candidate(self):
        #load all and refresh
        self._has_loaded = False
        pass

    def get_all_custom_behavior_candidates(self) -> list[MatchResult] | None:
        if self._has_loaded: return self.__behaviors_found
        return None

    # botting daemon
    
    def register_botting_daemon(self, fsm, daemon_factory):
        """
        Store the FSM and daemon factory for later re-registration.
        Called by UseCustomBehavior to enable daemon persistence across FSM restarts.
        """
        self._botting_daemon_fsm = fsm
        self._botting_daemon_factory = daemon_factory

    def ensure_botting_daemon_running(self):
        """
        Ensure the botting daemon is registered with the FSM.
        Should be called from the widget's daemon() on every frame.
        This handles re-registration after FSM.restart() clears managed_coroutines.
        """
        if self._botting_daemon_fsm is None or self._botting_daemon_factory is None:
            return

        fsm = self._botting_daemon_fsm
        # Only register if FSM is running and daemon is not already attached
        if fsm.current_state is not None and not fsm.HasManagedCoroutine("CustomBehaviorsBottingDaemon"):
            print("CustomBehaviorsBottingDaemon re-registering (daemon loop)")
            fsm.AddManagedCoroutine("CustomBehaviorsBottingDaemon", self._botting_daemon_factory)