"""Gzipped-JSON pathing dump loader.

Reads map_*.json.gz files captured by the Pathing Data Dumper widget.
"""

import gzip
import json
from dataclasses import dataclass, field
from pathlib import Path

from Py4GWCoreLib.native_src.context.MapContext import PathingTrapezoid


@dataclass(slots=True)
class MapHeader:
    map_hash: int
    trapezoid_count: int
    adjacent_count: int
    start_x: float
    start_y: float
    width: float
    height: float


@dataclass(slots=True)
class MarkerPoint:
    """A test marker placed in-game during data capture."""
    name: str
    coords: tuple[float, float]
    z_plane: int
    trapezoid_id: int
    notes: str = ""


@dataclass(slots=True)
class JsonPortal:
    """A portal connecting two layers, with associated trapezoid IDs."""
    layer_index: int
    left_layer_id: int
    right_layer_id: int
    trapezoid_indices: list[int]
    pair_index: int


@dataclass(slots=True)
class BlockingProp:
    """A collision circle from MapStaticData.blockingProps."""
    x: float
    y: float
    radius: float


@dataclass(slots=True)
class JsonDumpData:
    """Full pathing dump data from a gzipped JSON file."""
    header: MapHeader
    trapezoids: list[PathingTrapezoid]
    planes: dict[int, list[int]] = field(default_factory=dict)
    map_name: str = ""
    test_points: list[MarkerPoint] = field(default_factory=list)
    layer_portals: list[JsonPortal] = field(default_factory=list)
    blocking_props: list[BlockingProp] = field(default_factory=list)


def load_json_dump(filepath: str | Path) -> JsonDumpData:
    """Parse a gzipped JSON pathing dump into JsonDumpData."""
    with gzip.open(filepath, "rt", encoding="utf-8") as f:
        data = json.load(f)

    trapezoids: list[PathingTrapezoid] = []
    planes: dict[int, list[int]] = {}

    for layer_idx, layer in enumerate(data["layers"]):
        for t in layer["trapezoids"]:
            trapezoids.append(PathingTrapezoid(
                id=t["id"],
                portal_left=t.get("portal_left", 0),
                portal_right=t.get("portal_right", 0),
                XTL=t["XTL"], XTR=t["XTR"], YT=t["YT"],
                XBL=t["XBL"], XBR=t["XBR"], YB=t["YB"],
                neighbor_ids=t["neighbor_ids"],
            ))
            planes.setdefault(layer_idx, []).append(t["id"])

    all_x: list[float] = []
    all_y: list[float] = []
    for t in trapezoids:
        all_x.extend([t.XTL, t.XTR, t.XBL, t.XBR])
        all_y.extend([t.YT, t.YB])

    min_x = min(all_x) if all_x else 0.0
    min_y = min(all_y) if all_y else 0.0
    max_x = max(all_x) if all_x else 0.0
    max_y = max(all_y) if all_y else 0.0

    header = MapHeader(
        map_hash=data["map_id"],
        trapezoid_count=len(trapezoids),
        adjacent_count=sum(len(t.neighbor_ids) for t in trapezoids),
        start_x=min_x,
        start_y=min_y,
        width=max_x - min_x,
        height=max_y - min_y,
    )

    test_points = [
        MarkerPoint(
            name=tp["name"],
            coords=tuple(tp["coords"]),
            z_plane=tp["z_plane"],
            trapezoid_id=tp["trapezoid_id"],
            notes=tp.get("notes", ""),
        )
        for tp in data.get("test_points", [])
    ]

    layer_portals: list[JsonPortal] = []
    for layer_idx, layer in enumerate(data["layers"]):
        for p in layer.get("portals", []):
            layer_portals.append(JsonPortal(
                layer_index=layer_idx,
                left_layer_id=p["left_layer_id"],
                right_layer_id=p["right_layer_id"],
                trapezoid_indices=p["trapezoid_indices"],
                pair_index=p["pair_index"],
            ))

    blocking_props = [
        BlockingProp(x=bp["x"], y=bp["y"], radius=bp["radius"])
        for bp in data.get("blocking_props", [])
    ]

    return JsonDumpData(
        header=header,
        trapezoids=trapezoids,
        planes=planes,
        map_name=data.get("map_name", ""),
        test_points=test_points,
        layer_portals=layer_portals,
        blocking_props=blocking_props,
    )
