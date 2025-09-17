from typing import Any, Generator

from Widgets.CustomBehaviors.primitives import constants
from Widgets.CustomBehaviors.primitives.auto_mover.path_helper import PathHelper


class AutoPathingBuilder:
    def __init__(self):
        self.final_path_2d: list[tuple[float, float]] = []
        self.raw_path_2d: list[tuple[float, float]] = []
        self._generator_handle = None
        self._is_generating = False

    def generate_autopathing(self) -> Generator[None, None, None]:
        try:
            path = yield from PathHelper.build_valid_path(self.raw_path_2d)
            self.final_path_2d = path
            if constants.DEBUG: print(f"generate_autopathing completed with {len(path)} points")
        except Exception as e:
            if constants.DEBUG: print(f"generate_autopathing error: {e}")
            self.final_path_2d = []
        return

    def set_raw_path(self, path: list[tuple[float, float]]):
        self.raw_path_2d = path
        self.final_path_2d = []
        # Start path generation if we have a valid path
        if len(path) >= 2:
            self._start_generation()

    def _start_generation(self):
        """Start the path generation process."""
        if not self._is_generating and len(self.raw_path_2d) >= 2:
            self._generator_handle = self.generate_autopathing()
            self._is_generating = True
            if constants.DEBUG: print("Started path generation")

    def process_generation(self):
        """Process the path generation generator. Call this in the main loop."""
        if self._is_generating and self._generator_handle is not None:
            try:
                next(self._generator_handle)
            except StopIteration:
                if constants.DEBUG: print("Path generation completed")
                self._is_generating = False
                self._generator_handle = None
            except Exception as e:
                if constants.DEBUG: print(f"Path generation error: {e}")
                self._is_generating = False
                self._generator_handle = None
                self.final_path_2d = []

    def get_final_path(self) -> list[tuple[float, float]]:
        """Get the final processed path."""
        return self.final_path_2d

    def get_raw_path(self) -> list[tuple[float, float]]:
        """Get the raw path points."""
        return self.raw_path_2d

    def has_final_path(self) -> bool:
        """Check if a final path has been built."""
        return len(self.final_path_2d) > 0

    def has_raw_path(self) -> bool:
        """Check if raw path points exist."""
        return len(self.raw_path_2d) > 0

    def clear(self):
        """Clear both raw and final paths."""
        self.final_path_2d = []
        self.raw_path_2d = []
        self._is_generating = False
        self._generator_handle = None
