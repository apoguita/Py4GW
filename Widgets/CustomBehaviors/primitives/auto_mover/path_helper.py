from typing import Any, Generator

from Py4GWCoreLib import Map, Agent
from Py4GWCoreLib.GlobalCache import GLOBAL_CACHE
from Py4GWCoreLib.Pathing import AutoPathing


class PathHelper:

    @staticmethod
    def __chain_paths(waypoints: list[tuple[float, float]], z: float) -> Generator[Any, None, list[tuple[float, float]]]:
        """
        Chains multiple (x, y) waypoints using AutoPathing().get_path.
        Each segment starts at the end of the previous.
        
        Parameters:
            waypoints: A list of 2D (x, y) target points.
            z: The elevation to use (same for all points).
        
        Returns:
            A full 2D path as List[(x, y)], chained across all waypoints.
        """
        if not waypoints or len(waypoints) < 2:
            return [(waypoints[0][0], waypoints[0][1])] if waypoints else []

        full_path: list[tuple[float, float, float]] = []
        start: tuple[float, float, float] = waypoints[0] + (z,)
        full_path.append(start)

        for target in waypoints[1:]:
            end: tuple[float, float, float] = target + (z,)
            segment = yield from AutoPathing().get_path(start, end)
            full_path.extend(segment)
            start = segment[-1] if segment else end  # fallback in case of empty segment

        return [(x, y) for x, y, _ in full_path]

    @staticmethod
    def build_valid_path(path_2d: list[tuple[float, float]]) -> Generator[Any, None, list[tuple[float, float]]]:
        z = float(Agent.GetZPlane(GLOBAL_CACHE.Player.GetAgentID()))
        result = yield from PathHelper.__chain_paths(path_2d, z)
        return result