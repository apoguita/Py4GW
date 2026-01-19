from typing import List, Tuple
from enum import Enum

class PathStatus(Enum):
    Idle = 0
    Pending = 1
    Ready = 2
    Failed = 3


class PathPlanner:
    def __init__(self) -> None: ...
    """Create a new path planner instance."""

    def plan(self,
             start_x: float,
             start_y: float,
             start_z: float,
             goal_x: float,
             goal_y: float,
             goal_z: float) -> None: ...
    """Submit a path planning task to the game thread."""
    
    def compute_immediate(self, start_x: float, start_y: float, start_z: float,
                                goal_x: float, goal_y: float, goal_z: float) -> list[tuple[float, float, float]]:
        """Compute an immediate path without submitting to the game thread.
        Returns a list of (x, y, z) tuples if successful, or an empty list if failed."""

    def get_status(self) -> PathStatus: ...
    """Get current status of the path planner."""

    def is_ready(self) -> bool: ...
    """Return True if a valid path is ready to retrieve."""

    def was_successful(self) -> bool: ...
    """Return True if the path was successfully planned."""

    def get_path(self) -> List[Tuple[float, float, float]]: ...
    """Retrieve the calculated path as a list of (x, y, z) tuples."""

    def reset(self) -> None: ...
    """Reset the planner to Idle and clear the last result."""
