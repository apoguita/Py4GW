"""NavMesh and A* tests against real JSON dump data."""

from itertools import combinations

from Py4GWCoreLib.Pathing import AStar, NavMesh, densify_path2d

from Tests.pathing.conftest import assert_or_update_snapshot, skip_if_snapshots_written
from Tests.pathing.utils.json_dump_loader import JsonDumpData
from Tests.pathing.utils.svg_diff import render_path_diff


def _marker_pairs(
    map_dump: JsonDumpData,
) -> list[tuple[int, int, tuple[float, float], tuple[float, float]]]:
    """All unique (i, j, coords_i, coords_j) pairs from test points."""
    pts = map_dump.test_points
    return [
        (i, j, pts[i].coords, pts[j].coords)
        for i, j in combinations(range(len(pts)), 2)
    ]


# ============================================================================
# NavMesh construction
# ============================================================================

class TestNavMeshStructure:
    def test_trapezoid_count_matches(self, map_dump: JsonDumpData, map_navmesh: NavMesh):
        assert len(map_navmesh.trapezoids) == map_dump.header.trapezoid_count

    def test_has_portals(self, map_navmesh: NavMesh):
        assert len(map_navmesh.portals) > 0

    def test_spatial_grid_populated(self, map_navmesh: NavMesh):
        assert len(map_navmesh.spatial_grid) > 0

    def test_portal_graph_deterministic(self, map_navmesh: NavMesh):
        assert len(map_navmesh.portal_graph) > 0
        for tid, neighbors in map_navmesh.portal_graph.items():
            assert isinstance(tid, int)
            assert all(isinstance(n, int) for n in neighbors)

    def test_find_trapezoid_for_centroid(self, map_dump: JsonDumpData, map_navmesh: NavMesh):
        """Centroid of first trap should be findable."""
        t = map_dump.trapezoids[0]
        cx = (t.XTL + t.XTR + t.XBL + t.XBR) / 4
        cy = (t.YT + t.YB) / 2
        found = map_navmesh.find_trapezoid_id_by_coord((cx, cy))
        assert found is not None


# ============================================================================
# Test point validation
# ============================================================================

class TestTestPointLookup:
    """Verify that test_points from the JSON dump resolve to the correct trapezoid."""

    def test_test_points_match_recorded_trap(self, map_dump: JsonDumpData, map_navmesh: NavMesh):
        """Each test point should resolve to the trapezoid ID recorded during capture."""
        assert map_dump.test_points
        for tp in map_dump.test_points:
            found = map_navmesh.find_trapezoid_id_by_coord(tp.coords)
            assert found == tp.trapezoid_id, (
                f"Test point '{tp.name}' at {tp.coords}: "
                f"expected trap {tp.trapezoid_id}, got {found}"
            )


# ============================================================================
# A* pathfinding
# ============================================================================

class TestAStar:
    def test_path_between_all_markers(self, map_dump: JsonDumpData, map_navmesh: NavMesh):
        """Path between every pair of markers; all should succeed."""
        pairs = _marker_pairs(map_dump)
        assert pairs
        for i, j, start, goal in pairs:
            astar = AStar(map_navmesh)
            found = astar.search(start, goal)
            assert found, (
                f"No path from marker {i} to {j}: {start} -> {goal}"
            )
            path = astar.get_path()
            assert len(path) >= 2
            assert path[0] == start
            assert path[-1] == goal

    def test_full_pipeline(self, map_dump: JsonDumpData, map_navmesh: NavMesh):
        """A* + LOS smooth + densify between all marker pairs."""
        pairs = _marker_pairs(map_dump)
        assert pairs
        for i, j, start, goal in pairs:
            astar = AStar(map_navmesh)
            found = astar.search(start, goal)
            assert found, f"No path from marker {i} to {j}"
            raw = astar.get_path()
            smoothed = map_navmesh.smooth_path_by_los(raw)
            dense = densify_path2d(smoothed)
            assert dense[0] == raw[0]
            assert dense[-1] == raw[-1]
            for k in range(len(dense) - 1):
                dx = dense[k + 1][0] - dense[k][0]
                dy = dense[k + 1][1] - dense[k][1]
                dist = (dx**2 + dy**2) ** 0.5
                assert dist <= 500 + 1.0, (
                    f"Markers {i}->{j}, segment {k}: dist={dist:.1f}"
                )


# ============================================================================
# Regression snapshots
# ============================================================================

class TestSnapshots:
    def test_portal_graph(self, map_navmesh: NavMesh, map_id: int, update_snapshots: bool):
        snapshot = {
            str(k): sorted(v)
            for k, v in sorted(map_navmesh.portal_graph.items())
        }
        written = assert_or_update_snapshot(
            f"map_navmesh_portal_graph_{map_id}", snapshot, update_snapshots,
        )
        skip_if_snapshots_written([f"portal_graph_{map_id}"] if written else [])

    def test_spatial_grid_keys(self, map_navmesh: NavMesh, map_id: int, update_snapshots: bool):
        snapshot = sorted([list(k) for k in map_navmesh.spatial_grid.keys()])
        written = assert_or_update_snapshot(
            f"map_navmesh_spatial_grid_keys_{map_id}", snapshot, update_snapshots,
        )
        skip_if_snapshots_written([f"spatial_grid_keys_{map_id}"] if written else [])

    def test_astar_paths(self, map_dump: JsonDumpData, map_navmesh: NavMesh, map_id: int, update_snapshots: bool):
        """Snapshot raw A* path for each marker pair."""
        pairs = _marker_pairs(map_dump)
        assert pairs
        written: list[str] = []
        for i, j, start, goal in pairs:
            astar = AStar(map_navmesh)
            found = astar.search(start, goal)
            assert found, f"No path from marker {i} to {j}"
            path = [(round(x, 2), round(y, 2)) for x, y in astar.get_path()]
            snap_name = f"astar_path_{map_id}_{i}_{j}"
            if assert_or_update_snapshot(
                snap_name, path, update_snapshots,
                diff_renderer=lambda name, exp, act: render_path_diff(name, map_navmesh, exp, act),
            ):
                written.append(snap_name)
        skip_if_snapshots_written(written)

    def test_astar_smoothed_paths(self, map_dump: JsonDumpData, map_navmesh: NavMesh, map_id: int, update_snapshots: bool):
        """Snapshot smoothed+densified path for each marker pair."""
        pairs = _marker_pairs(map_dump)
        assert pairs
        written: list[str] = []
        for i, j, start, goal in pairs:
            astar = AStar(map_navmesh)
            found = astar.search(start, goal)
            assert found, f"No path from marker {i} to {j}"
            raw = astar.get_path()
            smoothed = map_navmesh.smooth_path_by_los(raw)
            dense = densify_path2d(smoothed)
            path = [(round(x, 2), round(y, 2)) for x, y in dense]
            snap_name = f"astar_smoothed_path_{map_id}_{i}_{j}"
            if assert_or_update_snapshot(
                snap_name, path, update_snapshots,
                diff_renderer=lambda name, exp, act: render_path_diff(name, map_navmesh, exp, act),
            ):
                written.append(snap_name)
        skip_if_snapshots_written(written)
