"""Type stub for the native PyMap module (added by py_map.cpp in Py4GW.dll).

RAW collision-raycast bridge: these functions return the engine's raw numbers
verbatim and do NO derived math. Normalize, segment length, the blocked decision,
hit-point reconstruction and the prop-mesh v*M transform all live on the Python
side (Py4GWCoreLib.Map.Raycast). Prefer the ergonomic Map.Raycast.* API over
calling these directly.
"""
from typing import List, Tuple


def RayCast(start: Tuple[float, float, float],
            unit_dir: Tuple[float, float, float]) -> Tuple[bool, float, float, float, int]:
    """RAW combined terrain + walkable-prop raycast (MapCliQueryIntersection).

    The engine primitive inherently writes a hit POINT (not a fraction), so this is
    the one function that returns a point. `unit_dir` is the caller-normalized unit
    direction; no distance bound is applied here.

    Returns (has_hit, hit_x, hit_y, hit_z, prop_layer):
      * has_hit    -> the engine returned a contact (within ~25000 units).
      * hit_*      -> the raw contact point (0.0 when has_hit is False).
      * prop_layer -> 0 when the nearest hit was terrain (or no hit); != 0 when the
        nearest hit was a prop MESH (PathGetMap-packed layer<<16|index).
    """
    ...


def RayCastTerrain(start: Tuple[float, float, float],
                   end: Tuple[float, float, float]) -> Tuple[bool, float]:
    """RAW terrain-only raycast (TerrainQueryIntersection) from start to end.

    Returns (has_hit, frac):
      * has_hit -> the engine terrain contact flag.
      * frac    -> parametric hit position in [0,1] along start->end (NOT world units --
        the bound terrain kernel writes a fraction, not the rescaled distance). Only
        meaningful when has_hit. The Python side (Map.Raycast.CastTerrain) multiplies
        frac by seg_len to get the world distance, reconstructs the hit point and
        decides blocked.
    """
    ...


def RayCastInteractive(start: Tuple[float, float, float],
                       unit_dir: Tuple[float, float, float],
                       max_range: float) -> Tuple[bool, float, int, int]:
    """RAW interactive-object mesh probe over interactive-prop geosets.

    Tests start + t*unit_dir (t in [0, max_range]) against the collision geosets of
    props that carry an interactive_model (doors, gates, gadgets) -- which the
    walkable-prop raycast (RayCast) does not always cover. Calls the GrModel geoset
    intersect resolved by a stable assertion anchor.

    Returns (has_hit, dist, prop_id, n_scanned):
      * has_hit   -> an interactive prop's mesh was hit within max_range.
      * dist      -> nearest hit distance along unit_dir (only meaningful when has_hit).
      * prop_id   -> propArray index of that prop (-1 if none).
      * n_scanned -> interactive props tested when the probe ran (0 => the map has no
        interactive-prop meshes, a legitimate clear). -1 => the probe could NOT run
        (unresolved symbol / no map-props context / non-unit dir) -- distinct from a
        clear result so callers do not read it as line of sight.
    """
    ...


def GetProps() -> List[Tuple[int, float, float, float, bool, int]]:
    """Enumerate all map props for overlay debugging ("draw the props").

    Returns a list of (prop_id, x, y, z, is_interactive, rec_count) per prop:
      * prop_id        -> propArray index (matches RayCastInteractive's prop_id).
      * x, y, z        -> prop world position.
      * is_interactive -> prop carries an interactive_model (the set
        RayCastInteractive scans).
      * rec_count      -> collision geoset count; >0 means it has collision meshes.
    """
    ...


def GetPropGeometry(prop_id: int) -> List[Tuple[
        Tuple[float, float, float, float, float, float,
              float, float, float, float, float, float],
        List[Tuple[float, float, float, float, float, float, float, float, float]]]]:
    """RAW collision MESH of one prop (the same geosets RayCastInteractive tests).

    Returns a list of (matrix12, tris_local) per submodel:
      * matrix12   -> 12 floats, a row-major 3x4 affine world matrix for the submodel.
      * tris_local -> list of (lx1,ly1,lz1, lx2,ly2,lz2, lx3,ly3,lz3) LOCAL-space
        triangles.
    Empty if the prop has no collision geometry. The per-vertex v*M world transform is
    applied in Python (Map.Raycast.GetPropGeometry), which yields world-space triangles
    for wireframe drawing via Overlay.DrawTriangle3D.
    """
    ...
