import math

import PyImGui
import Py4GW

from Py4GWCoreLib.Agent import Agent
from Py4GWCoreLib.GlobalCache import GLOBAL_CACHE
from Py4GWCoreLib.Map import Map
from Py4GWCoreLib.Pathing import AutoPathing, AStar
from Py4GWCoreLib.Player import Player

MODULE_NAME = "Trapezoid Lookup Test"
MODULE_ICON = "Textures/Module_Icons/Pathing.png"

START_X = -8658.560546875
START_Y = 4971.7080078125
GOAL_X = 10289.0
GOAL_Y = 6405.0

LAST_RESULT = "No test run yet."
LOAD_PENDING = False
AUTOPATH_PENDING = False


def _log_result(message: str, message_type=None):
    global LAST_RESULT
    LAST_RESULT = message
    Py4GW.Console.Log(
        MODULE_NAME,
        message,
        message_type or Py4GW.Console.MessageType.Info,
    )


def _coro_load_navmesh():
    global LOAD_PENDING
    try:
        _log_result(f"Load requested on map {Map.GetMapID()} ({Map.GetMapName()}).")
        yield from AutoPathing().load_pathing_maps()
        navmesh = AutoPathing().get_navmesh()
        if navmesh is None:
            _log_result(
                "NavMesh load finished, but no navmesh is available for the current map.",
                Py4GW.Console.MessageType.Warning,
            )
        else:
            _log_result(
                f"NavMesh ready for map {Map.GetMapID()} with "
                f"{len(navmesh.trapezoids)} trapezoids."
            )
    finally:
        LOAD_PENDING = False
    yield


def _path_length_2d(path_points):
    if not path_points or len(path_points) < 2:
        return 0.0

    total = 0.0
    for p1, p2 in zip(path_points, path_points[1:]):
        total += math.dist((p1[0], p1[1]), (p2[0], p2[1]))
    return total


def _coro_run_autopath():
    global AUTOPATH_PENDING
    try:
        player_id = Player.GetAgentID()
        zplane = Agent.GetZPlane(player_id) if player_id else 0

        _log_result(
            f"AutoPath requested: start=({START_X}, {START_Y}, {zplane}), "
            f"goal=({GOAL_X}, {GOAL_Y}, {zplane})"
        )

        path_points = yield from AutoPathing().get_path(
            (START_X, START_Y, zplane),
            (GOAL_X, GOAL_Y, zplane),
        )

        point_count = len(path_points)
        route_distance = _path_length_2d(path_points)
        first_point = path_points[0] if path_points else None
        last_point = path_points[-1] if path_points else None

        _log_result(
            f"AutoPath result: points={point_count}, route_distance={route_distance:.2f}, "
            f"first={first_point}, last={last_point}"
        )
    finally:
        AUTOPATH_PENDING = False
    yield


def _run_lookup():
    navmesh = AutoPathing().get_navmesh()
    if navmesh is None:
        _log_result("No navmesh loaded. Press 'Load NavMesh' first.", Py4GW.Console.MessageType.Warning)
        return

    start_id = navmesh.find_trapezoid_id_by_coord((START_X, START_Y))
    goal_id = navmesh.find_trapezoid_id_by_coord((GOAL_X, GOAL_Y))
    nearest_goal_id = navmesh.find_nearest_trapezoid_id(GOAL_X, GOAL_Y)
    straight_distance = math.dist((START_X, START_Y), (GOAL_X, GOAL_Y))
    nearest_goal_center = navmesh.get_position(nearest_goal_id) if nearest_goal_id is not None else None
    nearest_goal_distance = (
        math.dist((GOAL_X, GOAL_Y), nearest_goal_center)
        if nearest_goal_center is not None
        else None
    )

    _log_result(
        f"Lookup result: start=({START_X}, {START_Y}) -> {start_id}, "
        f"goal=({GOAL_X}, {GOAL_Y}) -> {goal_id}, "
        f"nearest_goal={nearest_goal_id}, "
        f"straight_distance={straight_distance:.2f}, "
        f"goal_to_nearest_center={nearest_goal_distance:.2f}"
        if nearest_goal_distance is not None
        else
        f"Lookup result: start=({START_X}, {START_Y}) -> {start_id}, "
        f"goal=({GOAL_X}, {GOAL_Y}) -> {goal_id}, "
        f"nearest_goal={nearest_goal_id}, "
        f"straight_distance={straight_distance:.2f}, "
        f"goal_to_nearest_center=None"
    )


def _run_astar():
    navmesh = AutoPathing().get_navmesh()
    if navmesh is None:
        _log_result("No navmesh loaded. Press 'Load NavMesh' first.", Py4GW.Console.MessageType.Warning)
        return

    astar = AStar(navmesh)
    success = astar.search((START_X, START_Y), (GOAL_X, GOAL_Y))
    path = astar.get_path() if success else []
    path_len = len(path)
    route_distance = _path_length_2d(path)
    _log_result(
        f"A* result: success={success}, path_len={path_len}, route_distance={route_distance:.2f}, "
        f"start=({START_X}, {START_Y}), goal=({GOAL_X}, {GOAL_Y})"
    )


def draw_window():
    global START_X, START_Y, GOAL_X, GOAL_Y, LOAD_PENDING, LAST_RESULT, AUTOPATH_PENDING

    if PyImGui.begin(MODULE_NAME):
        PyImGui.text(f"Map [{Map.GetMapID()}] - {Map.GetMapName()}")
        PyImGui.separator()

        PyImGui.text("Start")
        START_X = PyImGui.input_float("Start X", START_X)
        START_Y = PyImGui.input_float("Start Y", START_Y)

        PyImGui.text("Goal")
        GOAL_X = PyImGui.input_float("Goal X", GOAL_X)
        GOAL_Y = PyImGui.input_float("Goal Y", GOAL_Y)

        PyImGui.separator()

        if PyImGui.button("Reset To Error Values"):
            START_X = -8658.560546875
            START_Y = 4971.7080078125
            GOAL_X = 10289.0
            GOAL_Y = 6405.0

        PyImGui.same_line(0, -1)
        if PyImGui.button("Load NavMesh") and not LOAD_PENDING:
            LOAD_PENDING = True
            _log_result("Loading navmesh...")
            GLOBAL_CACHE.Coroutines.append(_coro_load_navmesh())

        if PyImGui.button("Run Trapezoid Lookup"):
            _run_lookup()

        PyImGui.same_line(0, -1)
        if PyImGui.button("Run A*"):
            _run_astar()

        PyImGui.same_line(0, -1)
        if PyImGui.button("Run AutoPath") and not AUTOPATH_PENDING:
            AUTOPATH_PENDING = True
            GLOBAL_CACHE.Coroutines.append(_coro_run_autopath())

        PyImGui.separator()
        PyImGui.text_wrapped(LAST_RESULT)

    PyImGui.end()


def main():
    draw_window()


if __name__ == "__main__":
    main()
