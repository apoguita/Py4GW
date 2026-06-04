"""Unit tests for Pathing.py refinement helpers.

NOTE: These tests require the game runtime (Py4GW DLLs) because
Py4GWCoreLib imports depend on PyScanner/PyPathing/etc.
Run from within an injected Python session or skip offline.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

try:
    from Py4GWCoreLib.Pathing import (
        _PORTAL_VERT_TOL,
        _PORTAL_HORIZ_TOL,
        _LOS_MARGIN,
        _LOS_STEP_DIST,
        _CHAIKIN_ITERATIONS,
        _CHAIKIN_Q,
        _DENSIFY_THRESHOLD,
        _DENSIFY_EPSILON,
        _START_PREPEND_DIST,
        _BSP_LEAF_SIZE,
        _BSP_MAX_DEPTH,
        _BSP_MIDPOINT_RATIO,
        _PORTAL_TOLERANCE,
        _ADJACENT_SIDE_TOL,
        _FIND_TRAP_TOL,
        _FIND_CONTAIN_TOL,
        _FAST_PLANNER_POLL_MS,
        _reattach_zplane,
        _trapezoid_x_bounds_at_y,
        _is_within_margin,
        _clamp_to_safe_zone,
        _correct_margin,
    )
    IMPORT_OK = True
except ImportError as e:
    IMPORT_OK = False
    _import_error = e


def test_portal_tolerances_are_200():
    assert IMPORT_OK, f"Import failed: {_import_error}"
    assert _PORTAL_VERT_TOL == 200
    assert _PORTAL_HORIZ_TOL == 200


def test_los_margin_is_200():
    assert IMPORT_OK
    assert _LOS_MARGIN == 200
    assert _LOS_STEP_DIST == 200.0


def test_chaikin_iterations_default():
    assert IMPORT_OK
    assert _CHAIKIN_ITERATIONS == 1


def test_chaikin_q_has_correct_values():
    assert IMPORT_OK
    assert _CHAIKIN_Q == (0.75, 0.25)


def test_chaikin_r_derived_correctly():
    assert IMPORT_OK
    r_ratio = 1.0 - _CHAIKIN_Q[0]
    r_inv = 1.0 - _CHAIKIN_Q[1]
    assert r_ratio == 0.25
    assert r_inv == 0.75


def test_densify_threshold():
    assert IMPORT_OK
    assert _DENSIFY_THRESHOLD == 500.0


def test_densify_epsilon():
    assert IMPORT_OK
    assert _DENSIFY_EPSILON == 1e-6


def test_start_prepend_dist():
    assert IMPORT_OK
    assert _START_PREPEND_DIST == 750


def test_reattach_zplane_empty_reference():
    assert IMPORT_OK
    result = _reattach_zplane([(1.0, 2.0), (3.0, 4.0)], [])
    assert result == [(1.0, 2.0, 0), (3.0, 4.0, 0)]


def test_reattach_zplane_nearest_parent():
    assert IMPORT_OK
    path2d = [(5.0, 5.0), (15.0, 15.0)]
    ref3d = [(4.0, 4.0, 10), (16.0, 16.0, 20)]
    result = _reattach_zplane(path2d, ref3d)
    assert result[0][2] == 10
    assert result[1][2] == 20


def test_reattach_zplane_exact_match():
    assert IMPORT_OK
    path2d = [(10.0, 10.0)]
    ref3d = [(10.0, 10.0, 42)]
    result = _reattach_zplane(path2d, ref3d)
    assert result == [(10.0, 10.0, 42)]


# ═══════════════════════════════════════════════════════════════════════════
#  Tests for _correct_margin helpers (pure math — no runtime needed)
# ═══════════════════════════════════════════════════════════════════════════

# -- Minimal mock trapezoid class for offline testing --------------------
class _MockTrap:
    def __init__(self, xbl, xbr, yb, xtl, xtr, yt):
        self.XBL = xbl
        self.XBR = xbr
        self.YB  = yb
        self.XTL = xtl
        self.XTR = xtr
        self.YT  = yt


def _make_rect_trap(x_left, x_right, y_bottom, y_top):
    """Rectangular trapezoid (XBL=XTL, XBR=XTR) — edges are vertical."""
    return _MockTrap(x_left, x_right, y_bottom, x_left, x_right, y_top)


def test_trapezoid_x_bounds_at_y_flat_edges():
    from Py4GWCoreLib.Pathing import _trapezoid_x_bounds_at_y
    trap = _make_rect_trap(0.0, 1000.0, 0.0, 800.0)
    left, right = _trapezoid_x_bounds_at_y(trap, 400.0)
    assert left == 0.0
    assert right == 1000.0


def test_trapezoid_x_bounds_at_y_slanted_edges():
    from Py4GWCoreLib.Pathing import _trapezoid_x_bounds_at_y
    trap = _MockTrap(0.0, 1000.0, 0.0, 200.0, 800.0, 800.0)
    left, right = _trapezoid_x_bounds_at_y(trap, 400.0)
    assert left == 100.0
    assert right == 900.0


def test_trapezoid_x_bounds_at_y_zero_height():
    from Py4GWCoreLib.Pathing import _trapezoid_x_bounds_at_y
    trap = _MockTrap(0.0, 1000.0, 100.0, 200.0, 800.0, 100.0)
    left, right = _trapezoid_x_bounds_at_y(trap, 100.0)
    assert left == 100.0   # (0+200)/2
    assert right == 900.0  # (1000+800)/2


def test_is_within_margin_fully_inside():
    from Py4GWCoreLib.Pathing import _is_within_margin
    trap = _make_rect_trap(0.0, 1000.0, 0.0, 800.0)
    assert _is_within_margin(500.0, 400.0, trap, 200) is True


def test_is_within_margin_fails_y_too_low():
    from Py4GWCoreLib.Pathing import _is_within_margin
    trap = _make_rect_trap(0.0, 1000.0, 0.0, 800.0)
    assert _is_within_margin(500.0, 100.0, trap, 200) is False


def test_is_within_margin_fails_x_too_far_right():
    from Py4GWCoreLib.Pathing import _is_within_margin
    trap = _make_rect_trap(0.0, 1000.0, 0.0, 800.0)
    assert _is_within_margin(900.0, 400.0, trap, 200) is False


def test_is_within_margin_zero_height_returns_false():
    from Py4GWCoreLib.Pathing import _is_within_margin
    trap = _MockTrap(0.0, 1000.0, 100.0, 0.0, 1000.0, 100.0)
    assert _is_within_margin(500.0, 100.0, trap, 200) is False


def test_clamp_to_safe_zone_y_clamped_first():
    from Py4GWCoreLib.Pathing import _clamp_to_safe_zone
    trap = _MockTrap(0.0, 1000.0, 0.0, 200.0, 800.0, 800.0)
    result = _clamp_to_safe_zone(500.0, 10.0, trap, 200)
    assert result is not None
    cx, cy = result
    assert cy == 200.0
    assert cx == 500.0


def test_clamp_to_safe_zone_trapezoid_too_short():
    from Py4GWCoreLib.Pathing import _clamp_to_safe_zone
    trap = _make_rect_trap(0.0, 1000.0, 0.0, 300.0)
    result = _clamp_to_safe_zone(500.0, 150.0, trap, 200)
    assert result is None


def test_clamp_to_safe_zone_trapezoid_too_narrow():
    from Py4GWCoreLib.Pathing import _clamp_to_safe_zone
    trap = _make_rect_trap(0.0, 300.0, 0.0, 800.0)
    result = _clamp_to_safe_zone(150.0, 400.0, trap, 200)
    assert result is None


def test_clamp_to_safe_zone_exactly_400_wide():
    from Py4GWCoreLib.Pathing import _clamp_to_safe_zone
    trap = _make_rect_trap(0.0, 400.0, 0.0, 800.0)
    result = _clamp_to_safe_zone(100.0, 400.0, trap, 200)
    assert result is not None
    cx, cy = result
    assert cx == 200.0
    assert cy == 400.0


def test_correct_margin_empty_path():
    assert IMPORT_OK
    from Py4GWCoreLib.Pathing import _correct_margin
    result = _correct_margin([], None)
    assert result == []


if __name__ == "__main__":
    import traceback
    tests = [
        fn for name, fn in sorted(globals().items())
        if name.startswith("test_") and callable(fn)
    ]
    if not IMPORT_OK:
        print(f"SKIP: Cannot import Py4GWCoreLib (game not running): {_import_error}")
        print(f"\n{len(tests)} tests skipped — run from within injected Python session.\n")
    else:
        passed = 0
        for test in tests:
            try:
                test()
                print(f"  PASS  {test.__name__}")
                passed += 1
            except Exception:
                print(f"  FAIL  {test.__name__}")
                traceback.print_exc()
        print(f"\n{passed}/{len(tests)} tests passed")
