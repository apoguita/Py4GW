
import importlib

class _RProxy:
    def __getattr__(self, name: str):
        root_pkg = importlib.import_module("Py4GWCoreLib")
        return getattr(root_pkg.Routines, name)

Routines = _RProxy()


#region Movement
class Movement:
    @staticmethod
    def FollowPath(path_handler, follow_handler, log_actions=False):
        from ..Py4GWcorelib import ConsoleLog
        """
        Purpose: Follow a path using the path handler and follow handler objects.
        Args:
            path_handler (PathHandler): The PathHandler object containing the path coordinates.
            follow_handler (FollowXY): The FollowXY object for moving to waypoints.
        Returns: None
        """
        if follow_handler.is_paused():
            return
        if hasattr(path_handler, "is_paused") and path_handler.is_paused():
            return
        
        follow_handler.update()

        if follow_handler.is_following():
            return

        point = path_handler.advance()
        if point is not None:
            follow_handler.move_to_waypoint(point[0], point[1])
            if log_actions:
                ConsoleLog("FollowPath", f"Moving to {point}")

    @staticmethod
    def IsFollowPathFinished(path_handler,follow_handler):
        return path_handler.is_finished() and follow_handler.has_arrived()

    class FollowXY:
        def __init__(self, tolerance=100):
            from ..Py4GWcorelib import Timer
            """
            Initialize the FollowXY object with default values.
            Routine for following a waypoint.
            """
            self.waypoint = (0, 0)
            self.tolerance = tolerance
            self.following = False
            self.arrived = False
            self.timer = Timer()  # Timer to track movement start time
            self.wait_timer = Timer()  # Timer to track waiting after issuing move command
            self.wait_timer_run_once = True
            self._paused = False

        def calculate_distance(self, pos1, pos2):
            """
            Calculate the Euclidean distance between two points.
            """
            from ..Py4GWcorelib import Utils
            return Utils.Distance(pos1, pos2)

        def move_to_waypoint(self, x=0, y=0, tolerance=None, use_action_queue = False):
            """
            Move the player to the specified coordinates.
            Args:
                x (float): X coordinate of the waypoint.
                y (float): Y coordinate of the waypoint.
                tolerance (int, optional): The distance threshold to consider arrival. Defaults to the initialized value.
            """
            from ..GlobalCache import GLOBAL_CACHE
            self.reset()
            self.waypoint = (x, y)
            self.tolerance = tolerance if tolerance is not None else self.tolerance
            self.following = True
            self.arrived = False

            GLOBAL_CACHE.Player.Move(x, y)

            self.timer.Start()

        def reset(self):
            """
            Cancel the current move command and reset the waypoint following state.
            """
            self.following = False
            self.arrived = False
            self.timer.Reset()
            self.wait_timer.Reset()

        def update(self, log_actions = False, use_action_queue = False):
            """
            Update the FollowXY object's state, check if the player has reached the waypoint,
            and issue new move commands if necessary.
            """
            from ..GlobalCache import GLOBAL_CACHE
            from ..Py4GWcorelib import ConsoleLog
            from ..Agent import Agent
            
            if self._paused:
                return
            
            if self.following:
                current_position = GLOBAL_CACHE.Player.GetXY()
                is_casting = Agent.IsCasting(GLOBAL_CACHE.Player.GetAgentID())
                is_moving = Agent.IsMoving(GLOBAL_CACHE.Player.GetAgentID())
                is_knocked_down = Agent.IsKnockedDown(GLOBAL_CACHE.Player.GetAgentID())
                is_dead = Agent.IsDead(GLOBAL_CACHE.Player.GetAgentID())

                if is_casting or is_moving or is_knocked_down or is_dead:
                    return 

                    # Check if the wait timer has elapsed and re-enable movement checks
                if self.wait_timer.HasElapsed(1000):
                    self.wait_timer.Reset()
                    self.wait_timer_run_once = True

                # Check if the player has arrived at the waypoint
                if self.calculate_distance(current_position, self.waypoint) <= self.tolerance:
                    self.arrived = True
                    self.following = False
                    return

                # Re-issue the move command if the player is not moving and not casting
                if self.wait_timer_run_once:
                    # Use the move_to_waypoint function to reissue movement

                    GLOBAL_CACHE.Player.Move(0,0) #reset movement pointer?
                    GLOBAL_CACHE.Player.Move(self.waypoint[0], self.waypoint[1])

                    self.wait_timer_run_once  = False  # Disable immediate re-issue
                    self.wait_timer.Start()  # Start the wait timer to prevent spamming movement
                    if log_actions:
                        ConsoleLog("FollowXY", f"Stopped, Reissue move")       

        def get_time_elapsed(self):
            """
            Get the elapsed time since the player started moving.
            """
            return self.timer.GetElapsedTime()

        def get_distance_to_waypoint(self):
            """
            Get the distance between the player and the current waypoint.
            """
            from ..GlobalCache import GLOBAL_CACHE
            from ..Py4GWcorelib import Utils
            current_position = GLOBAL_CACHE.Player.GetXY()
            return Utils.Distance(current_position, self.waypoint)

        def is_following(self):
            """
            Check if the player is currently following a waypoint.
            """
            return self.following

        def has_arrived(self):
            """
            Check if the player has arrived at the current waypoint.
            """
            return self.arrived
        
        def pause(self):
            self._paused = True

        def resume(self):
            self._paused = False

        def is_paused(self):
            return self._paused

    class PathHandler:
        def __init__(self, coordinates):
            """
            Purpose: Initialize the PathHandler with a list of coordinates.
            Args:
                coordinates (list): A list of tuples representing the points (x, y).
            Returns: None
            """
            self.coordinates = coordinates
            self.index = 0
            self.reverse = False  # By default, move forward
            self.finished = False
            self._paused = False

        def get_current_point(self):
            """
            Purpose: Get the current point in the list of coordinates.
            Args: None
            Returns: tuple or None
            """
            if not self.coordinates or self.finished:
                return None
            return self.coordinates[self.index]

        def advance(self):
            """
            Purpose: Advance the pointer in the list based on the current direction (forward or reverse).
            Args: None
            Returns: tuple or None (next point or None if finished)
            """
            if self._paused or self.finished:
                return None

            current_point = self.get_current_point()

            # Move forward or backward based on the direction
            if self.reverse:
                if self.index > 0:
                    self.index -= 1
                else:
                    self.finished = True
            else:
                if self.index < len(self.coordinates) - 1:
                    self.index += 1
                else:
                    self.finished = True

            return current_point

        def toggle_direction(self):
            """
            Purpose: Manually reverse the current direction of traversal.
            Args: None
            Returns: None
            """
            self.reverse = not self.reverse

        def reset(self):
            """
            Purpose: Reset the path traversal to the start or end depending on direction.
            Args: None
            Returns: None
            """
            self.index = 0 if not self.reverse else len(self.coordinates) - 1
            self.finished = False

        def is_finished(self):
            """
            Purpose: Check if the traversal has finished.
            Args: None
            Returns: bool
            """
            return self.finished

        def set_position(self, index):
            """
            Purpose: Set the current index in the list of coordinates.
            Args:
                index (int): The index to set the position to.
            Returns: None
            """
            if 0 <= index < len(self.coordinates):
                self.index = index
                self.finished = False
            else:
                raise IndexError(f"Index {index} out of bounds for coordinates list")

        def get_position(self):
            """
            Purpose: Get the current index in the list of coordinates.
            Args: None
            Returns: int
            """
            return self.index

        def get_position_count(self):
            """
            Purpose: Get the total number of positions in the list.
            Args: None
            Returns: int
            """
            return len(self.coordinates)
        
        def pause(self):
            self._paused = True

        def resume(self):
            self._paused = False

        def is_paused(self):
            return self._paused