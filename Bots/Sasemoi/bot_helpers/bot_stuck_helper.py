

import Py4GW
from Py4GWCoreLib import GLOBAL_CACHE
from Py4GWCoreLib import Routines
from Py4GWCoreLib import ThrottledTimer
from Py4GWCoreLib import ConsoleLog
from Py4GWCoreLib import Utils
from typing import Any, Tuple, Callable, NotRequired
from typing import TypedDict
from collections.abc import Iterable

StuckHandler = Tuple[str, Callable[..., bool], Callable[..., Any]]

class StuckHelperConfig(TypedDict):
    custom_scenarios: NotRequired[Iterable[StuckHandler]]
    log_enabled: NotRequired[bool]
    stuck_interval_ms: NotRequired[int]
    movement_check_interval_ms: NotRequired[int]
    movement_timeout_ms: NotRequired[int]
    movement_timeout_handler: NotRequired[Callable[..., Any]]
    movement_not_moved_distance: NotRequired[int]

default_config: StuckHelperConfig = {
    "custom_scenarios": [],
    "log_enabled": True,
    "stuck_interval_ms": 5000,
    "movement_check_interval_ms": 3000,
    "movement_timeout_ms": 45000,
    "movement_timeout_handler": lambda: None,
    "movement_not_moved_distance": 300
}

class BotStuckHelper:
    def __init__(self, config: StuckHelperConfig = default_config) -> None:
        self.name = "BotStuckHelper"

        # Config
        self.custom_scenarios = config.get("custom_scenarios", [])
        self.log_enabled = config.get("log_enabled", True)
        self.STUCK_INTERVAL = config.get("stuck_interval_ms", 5000)
        self.MOVEMENT_INTERVAL = config.get("movement_check_interval_ms", 3000)
        self.MOVEMENT_TIMEOUT = config.get("movement_timeout_ms", 45000)
        self.movement_timeout_handler = config.get("movement_timeout_handler", lambda: None)
        self.MOVEMENT_NOT_MOVED_DISTANCE = config.get("movement_not_moved_distance", 300)

        # state
        self.prev_pos = (0, 0)
        self.movement_stuck_time = 0
        self.is_active = True

        # Timers
        self.stuck_timer = ThrottledTimer(self.STUCK_INTERVAL)
        self.stuck_timer.Start()
        self.movement_timer = ThrottledTimer(self.MOVEMENT_INTERVAL)
        self.movement_timer.Start()

    def __name__(self) -> str:
        return "BotStuckHelper"

    # Private handlers for top-level checks (each is a generator so we can `yield from` them)
    def _check_map_valid(self):
        if not Routines.Checks.Map.MapValid():
            ConsoleLog(self.name, "Map is not valid, halting...", Py4GW.Console.MessageType.Debug, self.log_enabled)
            yield from Routines.Yield.wait(1000)

        # If map is valid this generator simply completes without yielding.
        return None

    def _check_player_dead(self):
        if GLOBAL_CACHE.Agent.IsDead(GLOBAL_CACHE.Player.GetAgentID()):
            ConsoleLog(self.name, "Player is dead, waiting...", Py4GW.Console.MessageType.Debug, self.log_enabled)
            yield from Routines.Yield.wait(1000)
        # Generator completes (returns None) when player is alive
        return None

    def _handle_movement_timeout(self):
        if self.movement_stuck_time >= self.MOVEMENT_TIMEOUT:
            ConsoleLog(self.name, "Movement timeout exceeded, executing movement timeout handler...", Py4GW.Console.MessageType.Debug, self.log_enabled)
            result = self.movement_timeout_handler()

            # If result is an iterable (but not a string/bytes), yield from it.
            if isinstance(result, Iterable):
                yield from result

            else:
                yield

            self.movement_stuck_time = 0  # Reset counter after handling
            self.is_active = False  # Optionally stop the helper after timeout handling


    def _scheduled_stuck_command(self):
        if self.stuck_timer.IsExpired():
            ConsoleLog(self.name, "Stuck timer expired, issuing scheduled stuck command...", Py4GW.Console.MessageType.Debug, self.log_enabled)
            GLOBAL_CACHE.Player.SendChatCommand("stuck")
            self.stuck_timer.Reset()

        yield None

    def _scheduled_movement_check(self):
        if self.movement_timer.IsExpired():
            current_player_pos = GLOBAL_CACHE.Player.GetXY()
            ConsoleLog(self.name, f"Checking movement. Old pos: {self.prev_pos}, Current pos: {current_player_pos}", Py4GW.Console.MessageType.Debug, self.log_enabled)

            # Check if player has not moved significantly
            if Utils.Distance(current_player_pos, self.prev_pos) < self.MOVEMENT_NOT_MOVED_DISTANCE:
                self.movement_stuck_time += self.MOVEMENT_INTERVAL
                ConsoleLog(self.name, f"No significant movement detected. Bot has been stuck for: {self.movement_stuck_time}ms", Py4GW.Console.MessageType.Debug, self.log_enabled)
            else:
                self.movement_stuck_time = 0  # Reset counter if moved
                ConsoleLog(self.name, "Significant movement detected, resetting stuck counter.", Py4GW.Console.MessageType.Debug, self.log_enabled)

            self.prev_pos = current_player_pos
            self.movement_timer.Reset()

        yield None

    def _handle_custom_scenarios(self):
        for (handler_name, condition_fn, handler) in self.custom_scenarios:
            if condition_fn():
                ConsoleLog(self.name, f"Executing stuck handler: {handler_name}", Py4GW.Console.MessageType.Debug, self.log_enabled)
                result = handler()

                # if handler returns a generator/iterable, yield from it; otherwise yield the result
                if isinstance(result, Iterable):
                    yield from result

                else:
                    yield None

                # Break after handling one scenario to avoid multiple handlers in one cycle
                self.is_active = False  # Optionally stop the helper after timeout handling
                break
        yield None


    def Run(self):
        ConsoleLog(self.name, "Starting BotStuckHelper...", Py4GW.Console.MessageType.Debug, self.log_enabled)
        
        # Main lop which checks for stuck conditions in order of priority
        # Assuming the custom scenarios have priority over the base checks
        while self.is_active:
            yield from self._check_map_valid()
            yield from self._check_player_dead()
            yield from self._handle_custom_scenarios()
            yield from self._handle_movement_timeout()
            yield from self._scheduled_stuck_command()
            yield from self._scheduled_movement_check()
            yield  # Yield to allow other routines to run in case none of the above yielded anything


    def Activate(self):
        self.is_active = True
        ConsoleLog(self.name, "BotStuckHelper activated.", Py4GW.Console.MessageType.Debug, self.log_enabled)
