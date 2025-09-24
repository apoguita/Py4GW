from typing import Any, Generator

from Widgets.CustomBehaviors.primitives import constants
from Widgets.CustomBehaviors.primitives.auto_mover.path_helper import PathHelper


class PathBuilder:
    def __init__(self):
        self.__final_path_2d: list[tuple[float, float]] = []
        self.__waypoint_list: list[tuple[float, float]] = []
        self.__generator_handle = None
        self.__is_generating = False

    def generate_autopathing(self) -> Generator[None, None, None]:
        try:
            path = yield from PathHelper.build_valid_path(self.__waypoint_list)
            self.__final_path_2d = path
            if constants.DEBUG: print(f"generate_autopathing completed with {len(path)} points")
        except Exception as e:
            if constants.DEBUG: print(f"generate_autopathing error: {e}")
            self.__final_path_2d = []
        return

    def set_waypoint_list(self, waypoint_list: list[tuple[float, float]]):
        self.__waypoint_list = waypoint_list
        self.__final_path_2d = []
        # Start path generation if we have a valid path
        if len(waypoint_list) >= 2:
            self.__start_generation()

    def __start_generation(self):
        """Start the path generation process."""
        if not self.__is_generating and len(self.__waypoint_list) >= 2:
            self.__generator_handle = self.generate_autopathing()
            self.__is_generating = True
            if constants.DEBUG: print("Started path generation")

    def process_generation(self):
        """Process the path generation generator. Call this in the main loop."""
        if self.__is_generating and self.__generator_handle is not None:
            try:
                next(self.__generator_handle)
            except StopIteration:
                if constants.DEBUG: print("Path generation completed")
                self.__is_generating = False
                self.__generator_handle = None
            except Exception as e:
                if constants.DEBUG: print(f"Path generation error: {e}")
                self.__is_generating = False
                self.__generator_handle = None
                self.__final_path_2d = []

    def get_final_path(self) -> list[tuple[float, float]]:
        """Get the final processed path."""
        return self.__final_path_2d

    def clear(self):
        """Clear both raw and final paths."""
        self.__final_path_2d = []
        self.__waypoint_list = []
        self.__is_generating = False
        self.__generator_handle = None
