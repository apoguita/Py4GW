# Pathing Tests

## Test Categories

| File | What it tests |
|------|---------------|
| `test_pure_functions.py` | Unit tests for `chaikin_smooth_path`, `densify_path2d`, `AABB`, `get_position`, `get_adjacent_side` |
| `test_navmesh.py` | Synthetic NavMesh construction, portal creation, spatial grid, `find_trapezoid_id_by_coord`, LOS, path smoothing |
| `test_astar.py` | Synthetic A* pathfinding (same-trap, adjacent, unreachable, chains) and full pipeline (A* + LOS smooth + densify) |
| `test_dump_validation.py` | Validates dump data: header, geometry, neighbor symmetry, plane coverage, test points, metadata |
| `test_real_navmesh.py` | NavMesh + A* on real map dumps with cross-layer portals, test point validation, and snapshot regression |

### Data sources

**Synthetic tests** (`test_pure_functions.py`, `test_navmesh.py`, `test_astar.py`) build small hand-crafted trapezoid layouts using `make_trap()` / `build_navmesh()` from `conftest.py`.

**Real-data tests** (`test_dump_validation.py`, `test_real_navmesh.py`) are parameterized over all `dumps/map_*.json.gz` files. Path snapshot tests use the dump's test point markers to generate all pairwise A* paths.

## Running Locally

```
pip install pytest
python -m pytest Tests/ -v
```

## Updating Snapshots

When a code change intentionally alters output, accept the new baselines:

```
python -m pytest Tests/ -v --update-snapshots
```

This overwrites `snapshots/*.json` with current output and skips the affected tests. Commit the updated snapshots.

## Diff SVGs

When a path snapshot test fails, `utils/svg_diff.py` writes an SVG to `diff/` showing expected (green) vs actual (red) overlaid on the map geometry. On CI, these are uploaded as the `regression-diff-svgs` artifact.
