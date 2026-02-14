"""Unit tests for pure functions in Pathing.py."""

import math
import pytest

from Py4GWCoreLib.native_src.context.MapContext import PathingTrapezoid
from Py4GWCoreLib.Pathing import (
    AABB,
    NavMesh,
    chaikin_smooth_path,
    densify_path2d,
)

from Tests.pathing.conftest import make_trap, build_navmesh


# ============================================================================
# chaikin_smooth_path
# ============================================================================

class TestChaikinSmooth:
    def test_two_points_adds_midpoints(self):
        # Even with 2 points, chaikin inserts q/r for the single segment
        pts = [(0.0, 0.0), (100.0, 0.0)]
        result = chaikin_smooth_path(pts, iterations=1)
        assert result[0] == pts[0]
        assert result[-1] == pts[-1]
        assert len(result) == 4  # start + q + r + end

    def test_three_points_produces_seven(self):
        pts = [(0, 0), (100, 0), (100, 100)]
        result = chaikin_smooth_path(pts, iterations=1)
        # 2 original endpoints + 2*(n-1) = 4 interior = 6; plus endpoints = 7
        # Actually: [pts[0]] + [q,r] * (n-1) + [pts[-1]] = 1 + 4 + 1 = 6? No...
        # Loop: for i in range(2): produces q,r for segment 0->1 and 1->2
        # new_points = [pts[0], q01, r01, q12, r12, pts[-1]] = 6
        assert len(result) == 6

    def test_preserves_endpoints(self):
        pts = [(10, 20), (50, 60), (90, 10), (130, 80)]
        for iters in (1, 2, 3):
            result = chaikin_smooth_path(pts, iterations=iters)
            assert result[0] == pts[0]
            assert result[-1] == pts[-1]

    def test_weighted_midpoints(self):
        pts = [(0, 0), (100, 0), (100, 100)]
        result = chaikin_smooth_path(pts, iterations=1)
        # First segment (0,0)->(100,0): q = 0.75*(0,0) + 0.25*(100,0) = (25,0)
        #                                r = 0.25*(0,0) + 0.75*(100,0) = (75,0)
        assert result[1] == pytest.approx((25.0, 0.0))
        assert result[2] == pytest.approx((75.0, 0.0))

    def test_zero_iterations_identity(self):
        pts = [(0, 0), (50, 50), (100, 0)]
        assert chaikin_smooth_path(pts, iterations=0) == pts


# ============================================================================
# densify_path2d
# ============================================================================

class TestDensifyPath:
    def test_short_segment_no_split(self):
        pts = [(0, 0), (100, 0)]
        result = densify_path2d(pts, threshold=500)
        assert result == pts

    def test_long_segment_splits(self):
        pts = [(0, 0), (1000, 0)]
        result = densify_path2d(pts, threshold=500)
        assert len(result) == 3
        assert result[0] == (0, 0)
        assert result[1] == pytest.approx((500, 0))
        assert result[2] == (1000, 0)

    def test_exact_multiple(self):
        pts = [(0, 0), (1500, 0)]
        result = densify_path2d(pts, threshold=500)
        assert len(result) == 4
        xs = [p[0] for p in result]
        assert xs == pytest.approx([0, 500, 1000, 1500])

    def test_diagonal(self):
        pts = [(0, 0), (300, 400)]  # dist = 500
        result = densify_path2d(pts, threshold=250)
        assert len(result) == 3
        assert result[0] == (0, 0)
        assert result[-1] == (300, 400)
        # Midpoint should be at 250/500 = 0.5 of the way
        assert result[1] == pytest.approx((150, 200))

    def test_single_point(self):
        assert densify_path2d([(5, 5)], threshold=100) == [(5, 5)]

    def test_empty(self):
        assert densify_path2d([], threshold=100) == []

    def test_zero_threshold_returns_copy(self):
        pts = [(0, 0), (1000, 0)]
        result = densify_path2d(pts, threshold=0)
        assert result == pts

    def test_multi_segment_path(self):
        pts = [(0, 0), (1000, 0), (1000, 1000)]
        result = densify_path2d(pts, threshold=500)
        assert result[0] == (0, 0)
        assert result[-1] == (1000, 1000)
        # Each 1000-unit segment should be split into 3 points
        assert len(result) == 5  # 0, 500, 1000, +500, +1000

    def test_nearly_threshold_segment(self):
        # Segment just barely over threshold
        pts = [(0, 0), (500.01, 0)]
        result = densify_path2d(pts, threshold=500)
        assert len(result) == 3  # split into 2 hops

    def test_negative_threshold_returns_copy(self):
        pts = [(0, 0), (1000, 0)]
        result = densify_path2d(pts, threshold=-1)
        assert result == pts

    def test_collinear_duplicates(self):
        """Duplicate consecutive points (zero-length segment)."""
        pts = [(0, 0), (0, 0), (100, 0)]
        result = densify_path2d(pts, threshold=50)
        assert result[0] == (0, 0)
        assert result[-1] == (100, 0)


# ============================================================================
# AABB
# ============================================================================

class TestAABB:
    def test_rectangular_trap(self):
        t = make_trap(0, xtl=10, xtr=50, yt=100, xbl=10, xbr=50, yb=0)
        box = AABB(t)
        assert box.m_min == (10, 0)
        assert box.m_max == (50, 100)

    def test_trapezoidal_shape(self):
        # Top is narrower than bottom
        t = make_trap(0, xtl=20, xtr=40, yt=100, xbl=0, xbr=60, yb=0)
        box = AABB(t)
        assert box.m_min == (0, 0)      # min of XBL and XTL
        assert box.m_max == (60, 100)   # max of XBR and XTR

    def test_inverted_trapezoid(self):
        # Top wider than bottom
        t = make_trap(0, xtl=0, xtr=100, yt=50, xbl=20, xbr=80, yb=0)
        box = AABB(t)
        assert box.m_min == (0, 0)   # min(XTL, XBL) = min(0, 20) = 0
        assert box.m_max == (100, 50)

    def test_degenerate_zero_height(self):
        t = make_trap(0, xtl=0, xtr=100, yt=50, xbl=0, xbr=100, yb=50)
        box = AABB(t)
        assert box.m_min[1] == box.m_max[1] == 50

    def test_degenerate_zero_width(self):
        t = make_trap(0, xtl=50, xtr=50, yt=100, xbl=50, xbr=50, yb=0)
        box = AABB(t)
        assert box.m_min[0] == box.m_max[0] == 50


# ============================================================================
# NavMesh.get_position (centroid)
# ============================================================================

class TestGetPosition:
    def test_rectangular(self):
        t = make_trap(0, xtl=0, xtr=100, yt=100, xbl=0, xbr=100, yb=0)
        nm = build_navmesh([t])
        cx, cy = nm.get_position(0)
        assert cx == pytest.approx(50.0)
        assert cy == pytest.approx(50.0)

    def test_trapezoidal(self):
        t = make_trap(0, xtl=20, xtr=80, yt=200, xbl=0, xbr=100, yb=0)
        nm = build_navmesh([t])
        cx, cy = nm.get_position(0)
        assert cx == pytest.approx((20 + 80 + 0 + 100) / 4)
        assert cy == pytest.approx(100.0)


# ============================================================================
# NavMesh.get_adjacent_side
# ============================================================================

class TestGetAdjacentSide:
    def _nm(self):
        t = make_trap(0, xtl=0, xtr=10, yt=10, xbl=0, xbr=10, yb=0)
        return build_navmesh([t])

    def test_bottom_top(self):
        a = make_trap(0, xtl=0, xtr=100, yt=100, xbl=0, xbr=100, yb=50)
        b = make_trap(1, xtl=0, xtr=100, yt=50, xbl=0, xbr=100, yb=0)
        nm = self._nm()
        assert nm.get_adjacent_side(a, b) == "bottom_top"

    def test_top_bottom(self):
        a = make_trap(0, xtl=0, xtr=100, yt=50, xbl=0, xbr=100, yb=0)
        b = make_trap(1, xtl=0, xtr=100, yt=100, xbl=0, xbr=100, yb=50)
        nm = self._nm()
        assert nm.get_adjacent_side(a, b) == "top_bottom"

    def test_right_left(self):
        a = make_trap(0, xtl=0, xtr=50, yt=100, xbl=0, xbr=50, yb=0)
        b = make_trap(1, xtl=50, xtr=100, yt=100, xbl=50, xbr=100, yb=0)
        nm = self._nm()
        assert nm.get_adjacent_side(a, b) == "right_left"

    def test_left_right(self):
        a = make_trap(0, xtl=50, xtr=100, yt=100, xbl=50, xbr=100, yb=0)
        b = make_trap(1, xtl=0, xtr=50, yt=100, xbl=0, xbr=50, yb=0)
        nm = self._nm()
        assert nm.get_adjacent_side(a, b) == "left_right"

    def test_no_adjacency(self):
        a = make_trap(0, xtl=0, xtr=10, yt=10, xbl=0, xbr=10, yb=0)
        b = make_trap(1, xtl=200, xtr=210, yt=200, xbl=200, xbr=210, yb=190)
        nm = self._nm()
        assert nm.get_adjacent_side(a, b) is None
