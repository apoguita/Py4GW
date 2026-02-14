"""Converts JSON dump data into NavMesh-compatible constructor inputs."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass

from Py4GWCoreLib.native_src.context.MapContext import PathingTrapezoid
from Py4GWCoreLib.Pathing import AABB, NavMesh

from Tests.pathing.utils.json_dump_loader import JsonDumpData


@dataclass
class FakePathingLayer:
    """Duck-types pathing_maps[i] expected by NavMesh.__init__."""
    trapezoids: list[PathingTrapezoid]


@dataclass
class FakeRawLayer:
    """Duck-types pathing_maps_raw[i] expected by NavMesh.__init__."""
    portals: list


def make_navmesh_inputs(
    trapezoids_by_layer: dict[int, list[PathingTrapezoid]],
) -> tuple[list[FakePathingLayer], list[FakeRawLayer]]:
    """Build (pathing_maps, pathing_maps_raw) for NavMesh().

    Args:
        trapezoids_by_layer: plane_id -> list of PathingTrapezoid for that layer.
    """
    sorted_planes = sorted(trapezoids_by_layer.keys())

    pathing_maps = [
        FakePathingLayer(trapezoids=trapezoids_by_layer[plane])
        for plane in sorted_planes
    ]
    pathing_maps_raw = [
        FakeRawLayer(portals=[])
        for _ in sorted_planes
    ]

    return pathing_maps, pathing_maps_raw


def build_navmesh_from_map_data(data: JsonDumpData) -> NavMesh:
    """Build a NavMesh from JsonDumpData, including cross-layer portals."""
    traps_by_layer = {
        plane: [data.trapezoids[tid] for tid in tids]
        for plane, tids in data.planes.items()
    }
    layers, raw = make_navmesh_inputs(traps_by_layer)
    nm = NavMesh(layers, raw, map_id=data.header.map_hash)

    if data.layer_portals:
        _create_cross_layer_portals(nm, data)

    return nm


def _create_cross_layer_portals(nm: NavMesh, data: JsonDumpData) -> None:
    """Wire up cross-layer portals from JSON dump portal metadata.

    The dump includes portal structs declaring which layers connect and which
    trapezoid IDs are involved.  This translates those declarations into actual
    NavMesh Portal objects (which the ctypes-based path can't do in tests).
    """
    connections: dict[frozenset, dict[int, set[int]]] = defaultdict(lambda: defaultdict(set))

    for p in data.layer_portals:
        if p.left_layer_id == p.right_layer_id:
            continue
        pair_key = frozenset({p.left_layer_id, p.right_layer_id})
        connections[pair_key][p.left_layer_id].update(p.trapezoid_indices)

    for sides in connections.values():
        layer_ids = list(sides.keys())
        if len(layer_ids) < 2:
            continue

        for i in range(len(layer_ids)):
            for j in range(i + 1, len(layer_ids)):
                traps_i = [nm.trapezoids[tid] for tid in sides[layer_ids[i]]
                           if tid in nm.trapezoids]
                traps_j = [nm.trapezoids[tid] for tid in sides[layer_ids[j]]
                           if tid in nm.trapezoids]

                for ti in traps_i:
                    ai = AABB(ti)
                    for tj in traps_j:
                        if ti.id == tj.id:
                            continue
                        aj = AABB(tj)
                        if nm.touching(ai, aj):
                            nm.create_portal(ai, aj, None)
