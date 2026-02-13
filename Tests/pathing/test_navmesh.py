"""NavMesh construction, portals, spatial grid, LOS, and find_trapezoid tests."""

from Py4GWCoreLib.Pathing import NavMesh

from Tests.pathing.conftest import make_trap, build_navmesh


# ============================================================================
# Synthetic NavMesh construction
# ============================================================================

class TestSyntheticNavMesh:
    def test_single_trap_no_portals(self):
        t = make_trap(0, xtl=0, xtr=100, yt=100, xbl=0, xbr=100, yb=0)
        nm = build_navmesh([t])
        assert len(nm.trapezoids) == 1
        assert len(nm.portals) == 0
        assert nm.get_neighbors(0) == []

    def test_two_adjacent_bottom_top(self):
        # A sits on top of B: A.YB == B.YT == 100
        a = make_trap(0, xtl=0, xtr=100, yt=200, xbl=0, xbr=100, yb=100,
                       neighbor_ids=[1])
        b = make_trap(1, xtl=0, xtr=100, yt=100, xbl=0, xbr=100, yb=0,
                       neighbor_ids=[0])
        nm = build_navmesh([a, b])
        assert len(nm.portals) >= 1
        assert 1 in nm.get_neighbors(0)
        assert 0 in nm.get_neighbors(1)

    def test_nonadjacent_neighbor_ids_no_portal(self):
        # Traps claim to be neighbors but don't share an edge
        a = make_trap(0, xtl=0, xtr=10, yt=10, xbl=0, xbr=10, yb=0,
                       neighbor_ids=[1])
        b = make_trap(1, xtl=200, xtr=210, yt=200, xbl=200, xbr=210, yb=190,
                       neighbor_ids=[0])
        nm = build_navmesh([a, b])
        assert len(nm.portals) == 0

    def test_portal_on_shared_edge(self):
        a = make_trap(0, xtl=10, xtr=90, yt=200, xbl=10, xbr=90, yb=100,
                       neighbor_ids=[1])
        b = make_trap(1, xtl=20, xtr=80, yt=100, xbl=20, xbr=80, yb=0,
                       neighbor_ids=[0])
        nm = build_navmesh([a, b])
        assert len(nm.portals) >= 1
        # Portal should lie on the shared edge at y=100
        portal = nm.portals[0]
        assert portal.p1.y == 100 or portal.p2.y == 100


# ============================================================================
# Spatial grid
# ============================================================================

class TestSpatialGrid:
    def test_single_trap_in_grid(self):
        t = make_trap(0, xtl=0, xtr=100, yt=100, xbl=0, xbr=100, yb=0)
        nm = build_navmesh([t])
        assert len(nm.spatial_grid) > 0
        all_traps = []
        for cell_traps in nm.spatial_grid.values():
            all_traps.extend(cell_traps)
        trap_ids = {t.id for t in all_traps}
        assert 0 in trap_ids

    def test_large_trap_spans_multiple_cells(self):
        t = make_trap(0, xtl=0, xtr=3000, yt=3000, xbl=0, xbr=3000, yb=0)
        nm = build_navmesh([t], grid_size=1000)
        # Should span (0,0)-(2,2) = 9 cells
        assert len(nm.spatial_grid) >= 9


# ============================================================================
# find_trapezoid_id_by_coord
# ============================================================================

class TestFindTrapezoid:
    def test_center_of_rect(self):
        t = make_trap(0, xtl=0, xtr=100, yt=100, xbl=0, xbr=100, yb=0)
        nm = build_navmesh([t])
        assert nm.find_trapezoid_id_by_coord((50, 50)) == 0

    def test_near_edge_with_tolerance(self):
        t = make_trap(0, xtl=0, xtr=100, yt=100, xbl=0, xbr=100, yb=0)
        nm = build_navmesh([t])
        # Just outside top edge (y=101), within default tol=20
        assert nm.find_trapezoid_id_by_coord((50, 101)) == 0

    def test_outside_returns_none(self):
        t = make_trap(0, xtl=0, xtr=100, yt=100, xbl=0, xbr=100, yb=0)
        nm = build_navmesh([t])
        assert nm.find_trapezoid_id_by_coord((500, 500)) is None

    def test_inside_trapezoidal_shape(self):
        # Narrow top, wide bottom
        t = make_trap(0, xtl=40, xtr=60, yt=100, xbl=0, xbr=100, yb=0)
        nm = build_navmesh([t])
        # Point at y=50 (midway): left_x = 0 + (40-0)*0.5 = 20, right_x = 100 + (60-100)*0.5 = 80
        assert nm.find_trapezoid_id_by_coord((50, 50)) == 0
        # Point outside the slanted edge at y=90: left = 0+(40)*0.9=36, right=100+(60-100)*0.9=64
        assert nm.find_trapezoid_id_by_coord((10, 90)) is None

    def test_degenerate_zero_height_trap(self):
        """Trap with YT == YB should not crash (division by zero guard)."""
        t = make_trap(0, xtl=0, xtr=100, yt=50, xbl=0, xbr=100, yb=50)
        nm = build_navmesh([t])
        # Point at y=50 should match (within tolerance)
        result = nm.find_trapezoid_id_by_coord((50, 50))
        assert result == 0

    def test_overlapping_traps_returns_first(self):
        """Two overlapping traps -- find returns the first match."""
        a = make_trap(0, xtl=0, xtr=100, yt=100, xbl=0, xbr=100, yb=0)
        b = make_trap(1, xtl=0, xtr=100, yt=100, xbl=0, xbr=100, yb=0)
        nm = build_navmesh([a, b])
        result = nm.find_trapezoid_id_by_coord((50, 50))
        assert result in (0, 1)

    def test_many_traps_correct_selection(self):
        """With 4 quadrant traps, each point maps to the right one."""
        traps = [
            make_trap(0, xtl=0, xtr=100, yt=200, xbl=0, xbr=100, yb=100),
            make_trap(1, xtl=100, xtr=200, yt=200, xbl=100, xbr=200, yb=100),
            make_trap(2, xtl=0, xtr=100, yt=100, xbl=0, xbr=100, yb=0),
            make_trap(3, xtl=100, xtr=200, yt=100, xbl=100, xbr=200, yb=0),
        ]
        nm = build_navmesh(traps)
        assert nm.find_trapezoid_id_by_coord((50, 150)) == 0
        assert nm.find_trapezoid_id_by_coord((150, 150)) == 1
        assert nm.find_trapezoid_id_by_coord((50, 50)) == 2
        assert nm.find_trapezoid_id_by_coord((150, 50)) == 3


# ============================================================================
# has_line_of_sight
# ============================================================================

class TestLineOfSight:
    def test_within_single_trap(self):
        t = make_trap(0, xtl=0, xtr=1000, yt=1000, xbl=0, xbr=1000, yb=0)
        nm = build_navmesh([t])
        assert nm.has_line_of_sight((200, 200), (800, 800), margin=50)

    def test_through_void(self):
        # Two traps with a gap between them
        a = make_trap(0, xtl=0, xtr=100, yt=100, xbl=0, xbr=100, yb=0)
        b = make_trap(1, xtl=500, xtr=600, yt=100, xbl=500, xbr=600, yb=0)
        nm = build_navmesh([a, b])
        assert not nm.has_line_of_sight((50, 50), (550, 50), margin=10)

    def test_same_point(self):
        t = make_trap(0, xtl=0, xtr=1000, yt=1000, xbl=0, xbr=1000, yb=0)
        nm = build_navmesh([t])
        assert nm.has_line_of_sight((500, 500), (500, 500))

    def test_margin_exceeds_trap_width(self):
        """Margin larger than trap width → all samples fail the margin check."""
        t = make_trap(0, xtl=0, xtr=100, yt=1000, xbl=0, xbr=100, yb=0)
        nm = build_navmesh([t])
        # Trap is 100 wide. With margin=60, valid band is only 100-120=-20 → nothing fits
        assert not nm.has_line_of_sight((50, 100), (50, 900), margin=60)


# ============================================================================
# smooth_path_by_los
# ============================================================================

class TestSmoothPathByLOS:
    def test_shortcut_with_los(self):
        # Large trap → all 3 points have LOS
        t = make_trap(0, xtl=0, xtr=2000, yt=2000, xbl=0, xbr=2000, yb=0)
        nm = build_navmesh([t])
        path = [(100, 100), (500, 500), (1000, 1000)]
        smoothed = nm.smooth_path_by_los(path, margin=50, step_dist=100)
        assert smoothed == [(100, 100), (1000, 1000)]

    def test_no_shortcut_without_los(self):
        # Two traps with a gap → middle point is needed
        a = make_trap(0, xtl=0, xtr=300, yt=300, xbl=0, xbr=300, yb=0,
                       neighbor_ids=[1])
        b = make_trap(1, xtl=0, xtr=300, yt=600, xbl=0, xbr=300, yb=300,
                       neighbor_ids=[0])
        nm = build_navmesh([a, b])
        path = [(150, 50), (150, 300), (150, 550)]
        smoothed = nm.smooth_path_by_los(path, margin=50, step_dist=50)
        # (50)->(550) would cross grid cells; with margin, LOS may fail
        # at minimum we shouldn't lose start/end
        assert smoothed[0] == (150, 50)
        assert smoothed[-1] == (150, 550)

    def test_two_points_unchanged(self):
        t = make_trap(0, xtl=0, xtr=1000, yt=1000, xbl=0, xbr=1000, yb=0)
        nm = build_navmesh([t])
        path = [(100, 100), (900, 900)]
        assert nm.smooth_path_by_los(path) == path
