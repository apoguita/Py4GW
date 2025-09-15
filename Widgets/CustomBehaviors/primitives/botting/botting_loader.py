
import inspect
import importlib
import pkgutil
from typing import Any, Generator, List

from Widgets.CustomBehaviors.primitives.botting.botting_abstract import BottingAbstract
from Widgets.CustomBehaviors.primitives import constants

class AvailableBot:
    def __init__(self, instance: BottingAbstract):
        self.instance: BottingAbstract = instance

class BottingLoader:
    _instance = None  # Singleton instance
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(BottingLoader, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if not self._initialized:
            self._has_loaded = False
            self.available_bots: list[AvailableBot] = []
            self._initialized = True

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
                full_package_name: The dot-separated name of the package (e.g., 'Widgets.CustomBehaviors.bots').

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
                if inspect.isclass(obj) and issubclass(obj, base_class) and obj != base_class:
                    if constants.DEBUG: print(f"Found subclass: {obj.__name__}")
                    subclasses.append(obj)

        if constants.DEBUG: print(f"Total subclasses found: {len(subclasses)}")

        return subclasses

    def refresh_bot_list(self):
        self._has_loaded = False

    def load_bot_list(self):
        if self._has_loaded:
            return False

        # Load & instantiate bots
        subclasses: list[type] = self.__find_subclasses_in_folder(BottingAbstract, "Widgets.CustomBehaviors.bots")
        self.available_bots.clear()
        
        for subclass in subclasses:
            try:
                instance: BottingAbstract = subclass()
                available_bot = AvailableBot(instance)
                self.available_bots.append(available_bot)
                if constants.DEBUG: print(f"Loaded bot: {instance.name}")
            except Exception as e:
                print(f"Failed to instantiate bot {subclass.__name__}: {e}")

        self._has_loaded = True
        return True
        



