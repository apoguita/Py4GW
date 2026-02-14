"""Pathing-specific fixtures."""

import json
from pathlib import Path
from typing import Any, Callable

import pytest

from Py4GWCoreLib.native_src.context.MapContext import PathingTrapezoid
from Py4GWCoreLib.Pathing import NavMesh

from Tests.pathing.utils.json_dump_loader import JsonDumpData, load_json_dump
from Tests.pathing.utils.navmesh_fixtures import build_navmesh_from_map_data, make_navmesh_inputs

DUMPS_DIR = Path(__file__).resolve().parent / "dumps"
SNAPSHOT_DIR = Path(__file__).resolve().parent / "snapshots"

# Discover all dump files for parameterized fixtures
DUMP_FILES = sorted(DUMPS_DIR.glob("map_*.json.gz"))


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_trap(
    id: int,
    xtl: float, xtr: float, yt: float,
    xbl: float, xbr: float, yb: float,
    neighbor_ids: list[int] | None = None,
) -> PathingTrapezoid:
    return PathingTrapezoid(
        id=id,
        portal_left=0, portal_right=0,
        XTL=xtl, XTR=xtr, YT=yt,
        XBL=xbl, XBR=xbr, YB=yb,
        neighbor_ids=neighbor_ids or [],
    )


def build_navmesh(
    traps: list[PathingTrapezoid],
    map_id: int = 999,
    grid_size: float = 1000,
) -> NavMesh:
    """Build a NavMesh from a flat list of trapezoids (single layer)."""
    layers, raw = make_navmesh_inputs({0: traps})
    return NavMesh(layers, raw, map_id, GRID_SIZE=grid_size)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session", params=DUMP_FILES, ids=lambda p: p.stem)
def map_dump(request) -> JsonDumpData:
    return load_json_dump(request.param)


@pytest.fixture(scope="session")
def map_navmesh(map_dump: JsonDumpData) -> NavMesh:
    return build_navmesh_from_map_data(map_dump)


@pytest.fixture(scope="session")
def map_id(map_dump: JsonDumpData) -> int:
    return map_dump.header.map_hash


# ---------------------------------------------------------------------------
# Other
# ---------------------------------------------------------------------------

@pytest.fixture
def update_snapshots(request) -> bool:
    return request.config.getoption("--update-snapshots")


# ---------------------------------------------------------------------------
# Snapshot helpers
# ---------------------------------------------------------------------------

def _normalize(obj: Any) -> Any:
    """Convert tuples to lists recursively so JSON round-trip comparison works."""
    if isinstance(obj, (list, tuple)):
        return [_normalize(x) for x in obj]
    if isinstance(obj, dict):
        return {k: _normalize(v) for k, v in obj.items()}
    return obj


def assert_or_update_snapshot(
    name: str,
    actual: dict | list,
    update: bool,
    *,
    diff_renderer: Callable[[str, Any, Any], None] | None = None,
) -> bool:
    """Compare *actual* against a stored JSON snapshot.

    Returns True if the snapshot was written (created or updated) rather than
    compared.  Callers that invoke this in a loop should collect the return
    values and call ``skip_if_snapshots_written()`` after the loop so that
    ``pytest.skip`` is only raised once all snapshots have been processed.
    """
    SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
    path = SNAPSHOT_DIR / f"{name}.json"
    normalized = _normalize(actual)
    if update or not path.exists():
        path.write_text(json.dumps(normalized, sort_keys=True, separators=(",", ":")))
        return True
    expected = json.loads(path.read_text())
    if normalized != expected:
        if diff_renderer:
            try:
                diff_renderer(name, expected, normalized)
            except Exception as exc:
                print(f"Warning: diff renderer failed for {name}: {exc}")
        assert False, f"Snapshot mismatch for {name}. Re-run with --update-snapshots to accept changes."
    return False


def skip_if_snapshots_written(written: list[str]) -> None:
    """Call after a loop of ``assert_or_update_snapshot`` calls.

    Raises ``pytest.skip`` once, listing every snapshot that was written.
    """
    if written:
        pytest.skip(f"Snapshots written: {', '.join(written)}")
