"""Pure-Python math + result types for ``Map.Raycast``.

This module is the home for ALL the geometry math that was moved off the native
PyMap bridge: segment length, normalize, hit-point reconstruction, the blocked
decision and the prop-mesh ``v*M`` transform. It has NO native (DLL) dependency,
so it is unit-testable in isolation -- the native side returns raw engine numbers
and everything derived happens here.

GW world Z is negative-up. These primitives are geometry-only and agent-agnostic:
callers pass exact world endpoints. Any eye-height lift is the caller's concern and
is deliberately kept out of here.
"""
import math
from typing import Iterable, List, NamedTuple, Optional, Tuple

Vec3 = Tuple[float, float, float]
Matrix12 = Tuple[float, float, float, float, float, float,
                 float, float, float, float, float, float]
Triangle = Tuple[float, float, float, float, float, float, float, float, float]

# An obstruction within this many world units of the segment end is treated as the
# endpoint's own footing / float noise, not a block. Matches the literal the C++ side
# used before the blocked decision moved to Python.
DEFAULT_SLACK = 8.0

# Segments shorter than this are degenerate; normalize would divide by ~0, so the
# raycast primitives report "clear" without calling the engine. Matches the old native
# ``seg_len <= 1.0`` short-circuit.
MIN_SEGMENT_LENGTH = 1.0

# Result-source tags for RaycastHit.source.
SOURCE_NONE = "none"               # clear line of sight
SOURCE_TERRAIN = "terrain"         # blocked by terrain
SOURCE_PROPS = "props"             # blocked by a prop / interactive mesh
SOURCE_UNAVAILABLE = "unavailable" # probe could not run (stale DLL / no map context)


class RaycastHit(NamedTuple):
    """Result of a point->point cast / line-of-sight query.

    blocked  : True if an obstruction sits before the segment end (minus slack).
    point    : nearest contact point (world x,y,z), or None when clear / unavailable.
    distance : distance from start to ``point``, or None.
    source   : which test produced the answer -- 'terrain', 'props', 'none' (clear) or
               'unavailable' (probe could not run). For the combined engine cast,
               'terrain'/'props' is decided from the engine's prop_layer.
    """
    blocked: bool
    point: Optional[Vec3]
    distance: Optional[float]
    source: str


class PropHit(NamedTuple):
    """Result of an interactive-prop mesh cast (adds prop_id / n_scanned).

    n_scanned == -1 is the sentinel for "probe could not run" (the native call raised:
    stale DLL / missing symbol); n_scanned == 0 from a successful call simply means the
    map carries no interactive-prop meshes (a legitimate clear).
    """
    blocked: bool
    point: Optional[Vec3]
    distance: Optional[float]
    prop_id: int
    n_scanned: int


class PropInfo(NamedTuple):
    """One enumerated map prop (``Map.Raycast.GetProps``)."""
    prop_id: int
    x: float
    y: float
    z: float
    is_interactive: bool
    rec_count: int


# ----- vector helpers -------------------------------------------------------

def segment_length(start: Vec3, end: Vec3) -> float:
    """Euclidean distance between two world points."""
    return math.dist(start, end)


def direction(start: Vec3, end: Vec3) -> Tuple[Optional[Vec3], float]:
    """Return (unit_dir, seg_len). unit_dir is None for a degenerate segment."""
    seg_len = math.dist(start, end)
    if seg_len <= MIN_SEGMENT_LENGTH:
        return None, seg_len
    inv = 1.0 / seg_len
    return (((end[0] - start[0]) * inv,
             (end[1] - start[1]) * inv,
             (end[2] - start[2]) * inv), seg_len)


def point_along(start: Vec3, unit_dir: Vec3, dist: float) -> Vec3:
    """Reconstruct the world point at ``dist`` along unit_dir from start."""
    return (start[0] + dist * unit_dir[0],
            start[1] + dist * unit_dir[1],
            start[2] + dist * unit_dir[2])


def is_blocked(hit_dist: float, seg_len: float, slack: float = DEFAULT_SLACK) -> bool:
    """A hit blocks LoS only if it sits before the segment end minus slack."""
    return hit_dist < seg_len - slack


def transform_point(matrix12: Matrix12, v: Vec3) -> Vec3:
    """Apply a row-major 3x4 affine world matrix to a local vertex (v*M)."""
    lx, ly, lz = v
    m = matrix12
    return (m[0] * lx + m[1] * ly + m[2] * lz + m[3],
            m[4] * lx + m[5] * ly + m[6] * lz + m[7],
            m[8] * lx + m[9] * ly + m[10] * lz + m[11])


def transform_local_triangles(submodels: Iterable) -> List[Triangle]:
    """Flatten native GetPropGeometry output to world-space triangles.

    Input: an iterable of (matrix12, tris_local) per submodel, where each local
    triangle is a 9-float (lx1,ly1,lz1, lx2,ly2,lz2, lx3,ly3,lz3). Applies v*M per
    vertex and returns a flat list of world-space 9-float triangles.
    """
    world: List[Triangle] = []
    for matrix12, tris_local in submodels:
        for tri in tris_local:
            w0 = transform_point(matrix12, (tri[0], tri[1], tri[2]))
            w1 = transform_point(matrix12, (tri[3], tri[4], tri[5]))
            w2 = transform_point(matrix12, (tri[6], tri[7], tri[8]))
            world.append((w0[0], w0[1], w0[2],
                          w1[0], w1[1], w1[2],
                          w2[0], w2[1], w2[2]))
    return world


def nearest_block(hits: Iterable[RaycastHit]) -> RaycastHit:
    """Combine cast results: the nearest blocking hit wins; clear if none block.

    If no source blocks but every supplied probe was unavailable, the combined result
    is 'unavailable' (so callers do not read a failed probe as clear line of sight).
    """
    hits = list(hits)
    blocking = [h for h in hits if h.blocked and h.distance is not None]
    if blocking:
        return min(blocking, key=lambda h: h.distance)
    if hits and all(h.source == SOURCE_UNAVAILABLE for h in hits):
        return RaycastHit(False, None, None, SOURCE_UNAVAILABLE)
    return RaycastHit(False, None, None, SOURCE_NONE)
