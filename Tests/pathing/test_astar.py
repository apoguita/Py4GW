"""A* pathfinding tests (synthetic)."""

from Py4GWCoreLib.Pathing import AStar, NavMesh, densify_path2d

from Tests.pathing.conftest import make_trap, build_navmesh


# ============================================================================
# Synthetic A*
# ============================================================================

class TestAStarSynthetic:
    def test_same_trapezoid(self):
        t = make_trap(0, xtl=0, xtr=100, yt=100, xbl=0, xbr=100, yb=0)
        nm = build_navmesh([t])
        astar = AStar(nm)
        assert astar.search((50, 50), (80, 80))
        path = astar.get_path()
        assert path[0] == (50, 50)
        assert path[-1] == (80, 80)

    def test_adjacent_traps(self):
        a = make_trap(0, xtl=0, xtr=100, yt=200, xbl=0, xbr=100, yb=100,
                       neighbor_ids=[1])
        b = make_trap(1, xtl=0, xtr=100, yt=100, xbl=0, xbr=100, yb=0,
                       neighbor_ids=[0])
        nm = build_navmesh([a, b])
        astar = AStar(nm)
        assert astar.search((50, 150), (50, 50))
        path = astar.get_path()
        assert len(path) >= 2
        assert path[0] == (50, 150)
        assert path[-1] == (50, 50)

    def test_unreachable(self):
        # Two traps, not connected
        a = make_trap(0, xtl=0, xtr=100, yt=100, xbl=0, xbr=100, yb=0)
        b = make_trap(1, xtl=500, xtr=600, yt=100, xbl=500, xbr=600, yb=0)
        nm = build_navmesh([a, b])
        astar = AStar(nm)
        assert not astar.search((50, 50), (550, 50))

    def test_invalid_start_coord(self):
        t = make_trap(0, xtl=0, xtr=100, yt=100, xbl=0, xbr=100, yb=0)
        nm = build_navmesh([t])
        astar = AStar(nm)
        assert not astar.search((9999, 9999), (50, 50))

    def test_linear_chain(self):
        # 3 traps stacked vertically
        traps = [
            make_trap(0, xtl=0, xtr=100, yt=300, xbl=0, xbr=100, yb=200,
                       neighbor_ids=[1]),
            make_trap(1, xtl=0, xtr=100, yt=200, xbl=0, xbr=100, yb=100,
                       neighbor_ids=[0, 2]),
            make_trap(2, xtl=0, xtr=100, yt=100, xbl=0, xbr=100, yb=0,
                       neighbor_ids=[1]),
        ]
        nm = build_navmesh(traps)
        astar = AStar(nm)
        assert astar.search((50, 250), (50, 50))
        path = astar.get_path()
        # Path should pass through trap 1 centroid
        assert len(path) >= 3
        # Y values should be monotonically decreasing
        ys = [p[1] for p in path]
        assert ys == sorted(ys, reverse=True)


# ============================================================================
# Full pipeline: A* + smoothing + densify
# ============================================================================

class TestFullPipeline:
    def test_pipeline_on_chain(self):
        traps = [
            make_trap(0, xtl=0, xtr=200, yt=600, xbl=0, xbr=200, yb=400,
                       neighbor_ids=[1]),
            make_trap(1, xtl=0, xtr=200, yt=400, xbl=0, xbr=200, yb=200,
                       neighbor_ids=[0, 2]),
            make_trap(2, xtl=0, xtr=200, yt=200, xbl=0, xbr=200, yb=0,
                       neighbor_ids=[1]),
        ]
        nm = build_navmesh(traps)
        astar = AStar(nm)
        assert astar.search((100, 500), (100, 100))

        raw = astar.get_path()
        smoothed = nm.smooth_path_by_los(raw, margin=20, step_dist=50)
        dense = densify_path2d(smoothed, threshold=200)

        assert dense[0] == raw[0]
        assert dense[-1] == raw[-1]
        # All segments should be <= 200 + epsilon
        for i in range(len(dense) - 1):
            dx = dense[i + 1][0] - dense[i][0]
            dy = dense[i + 1][1] - dense[i][1]
            dist = (dx**2 + dy**2) ** 0.5
            assert dist <= 200 + 1.0
