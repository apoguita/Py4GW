"""Pure geometry helpers for BT real-time local obstacle avoidance.

The global route remains owned by :mod:`Py4GWCoreLib.Pathing`.  This module
only selects a short-lived steering point around dynamic circular obstacles.
It deliberately has no game-runtime imports so the geometry can be tested
offline.
"""

from __future__ import annotations

from dataclasses import dataclass
import math
from collections.abc import Callable, Sequence


Point2D = tuple[float, float]
WalkableCheck = Callable[[Point2D, Point2D], bool]


@dataclass(frozen=True, slots=True)
class CircularObstacle:
    """A dynamic obstacle represented by its collision centre and radius."""

    agent_id: int
    position: Point2D
    radius: float


@dataclass(frozen=True, slots=True)
class AvoidanceDecision:
    """A temporary steering target selected around the first blocker."""

    blocker_id: int
    target: Point2D
    side: int
    clearance: float


def _distance_to_segment(point: Point2D, start: Point2D, end: Point2D) -> tuple[float, float]:
    """Return distance to a segment and the clamped projection ratio."""

    segment_x = end[0] - start[0]
    segment_y = end[1] - start[1]
    segment_length_sq = segment_x * segment_x + segment_y * segment_y
    if segment_length_sq <= 1e-9:
        return math.dist(point, start), 0.0

    relative_x = point[0] - start[0]
    relative_y = point[1] - start[1]
    projection = (relative_x * segment_x + relative_y * segment_y) / segment_length_sq
    projection = max(0.0, min(1.0, projection))
    nearest = (
        start[0] + segment_x * projection,
        start[1] + segment_y * projection,
    )
    return math.dist(point, nearest), projection


def segment_clearance(start: Point2D, end: Point2D, obstacles: Sequence[CircularObstacle]) -> float:
    """Return the smallest free distance between a segment and all obstacles."""

    if not obstacles:
        return float("inf")

    clearance = float("inf")
    for obstacle in obstacles:
        distance, _ = _distance_to_segment(obstacle.position, start, end)
        clearance = min(clearance, distance - max(0.0, float(obstacle.radius)))
    return clearance


def find_first_blocker(
    start: Point2D,
    target: Point2D,
    obstacles: Sequence[CircularObstacle],
    *,
    lookahead: float,
) -> CircularObstacle | None:
    """Find the earliest obstacle intersecting the forward lookahead segment."""

    target_x = target[0] - start[0]
    target_y = target[1] - start[1]
    target_distance = math.hypot(target_x, target_y)
    if target_distance <= 1e-6:
        return None

    direction_x = target_x / target_distance
    direction_y = target_y / target_distance
    probe_distance = min(target_distance, max(1.0, float(lookahead)))
    probe_end = (
        start[0] + direction_x * probe_distance,
        start[1] + direction_y * probe_distance,
    )

    first: CircularObstacle | None = None
    first_projection = float("inf")
    for obstacle in obstacles:
        distance, projection = _distance_to_segment(obstacle.position, start, probe_end)
        if projection <= 1e-4:
            continue
        if distance >= max(0.0, float(obstacle.radius)):
            continue
        if projection < first_projection:
            first = obstacle
            first_projection = projection
    return first


def choose_avoidance_target(
    start: Point2D,
    target: Point2D,
    obstacles: Sequence[CircularObstacle],
    *,
    lookahead: float = 500.0,
    steering_distance: float = 400.0,
    preferred_side: int = 0,
    is_walkable: WalkableCheck | None = None,
) -> AvoidanceDecision | None:
    """Choose a safe temporary target around a blocker in the desired corridor.

    Candidate headings remain forward-facing.  The score favours progress,
    clearance, small angular changes, and the previously selected side so the
    mover does not oscillate left/right while passing an agent.
    """

    blocker = find_first_blocker(start, target, obstacles, lookahead=lookahead)
    if blocker is None:
        return None

    delta_x = target[0] - start[0]
    delta_y = target[1] - start[1]
    target_distance = math.hypot(delta_x, delta_y)
    if target_distance <= 1e-6:
        return None

    direction_angle = math.atan2(delta_y, delta_x)
    step = min(target_distance, max(150.0, float(steering_distance)))

    stable_side = 1 if preferred_side > 0 else -1 if preferred_side < 0 else 0
    if stable_side:
        sides = (stable_side, -stable_side)
    else:
        sides = (1, -1)

    candidates: list[tuple[float, AvoidanceDecision]] = []
    for angle_degrees in (25.0, 40.0, 55.0, 70.0):
        for side in sides:
            angle = direction_angle + math.radians(angle_degrees * side)
            candidate = (
                start[0] + math.cos(angle) * step,
                start[1] + math.sin(angle) * step,
            )
            if is_walkable is not None and not is_walkable(start, candidate):
                continue

            clearance = segment_clearance(start, candidate, obstacles)
            if clearance < 0.0:
                continue

            progress = (
                (candidate[0] - start[0]) * (delta_x / target_distance)
                + (candidate[1] - start[1]) * (delta_y / target_distance)
            )
            side_bonus = 80.0 if stable_side and side == stable_side else 0.0
            score = progress + min(clearance, 300.0) * 1.5 - angle_degrees * 1.5 + side_bonus
            candidates.append(
                (
                    score,
                    AvoidanceDecision(
                        blocker_id=int(blocker.agent_id),
                        target=candidate,
                        side=side,
                        clearance=clearance,
                    ),
                )
            )

    if not candidates:
        return None
    return max(candidates, key=lambda candidate: candidate[0])[1]
