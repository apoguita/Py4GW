"""Validate loaded dump data: header, geometry, adjacency, planes, test points."""

from Tests.pathing.utils.json_dump_loader import JsonDumpData


class TestHeader:
    def test_trapezoid_count_positive(self, map_dump: JsonDumpData):
        assert map_dump.header.trapezoid_count > 0

    def test_trapezoid_list_matches_header(self, map_dump: JsonDumpData):
        assert len(map_dump.trapezoids) == map_dump.header.trapezoid_count

    def test_bounds_nonzero(self, map_dump: JsonDumpData):
        h = map_dump.header
        assert h.width > 0
        assert h.height > 0


class TestGeometry:
    def test_yt_gte_yb(self, map_dump: JsonDumpData):
        for t in map_dump.trapezoids:
            assert t.YT >= t.YB, f"Trap {t.id}: YT={t.YT} < YB={t.YB}"



class TestAdjacency:
    def test_has_neighbor_data(self, map_dump: JsonDumpData):
        traps_with_neighbors = sum(1 for t in map_dump.trapezoids if t.neighbor_ids)
        assert traps_with_neighbors > 0, "No trapezoids have neighbor data"

    def test_neighbor_ids_in_range(self, map_dump: JsonDumpData):
        n = map_dump.header.trapezoid_count
        for t in map_dump.trapezoids:
            for nid in t.neighbor_ids:
                assert 0 <= nid < n, (
                    f"Trap {t.id}: neighbor {nid} out of range [0, {n})"
                )

    def test_adjacency_symmetry(self, map_dump: JsonDumpData):
        """Game-provided adjacency should be highly symmetric."""
        traps = {t.id: t for t in map_dump.trapezoids}
        total = 0
        symmetric = 0
        for t in map_dump.trapezoids:
            for nid in t.neighbor_ids:
                total += 1
                nb = traps.get(nid)
                if nb and t.id in nb.neighbor_ids:
                    symmetric += 1
        ratio = symmetric / total if total > 0 else 1.0
        assert ratio > 0.95, f"Adjacency symmetry ratio {ratio:.2%}"


class TestPlanes:
    def test_planes_cover_all_traps(self, map_dump: JsonDumpData):
        all_ids = set()
        for tids in map_dump.planes.values():
            all_ids.update(tids)
        assert all_ids == set(range(len(map_dump.trapezoids)))


class TestTestPoints:
    def test_has_sufficient_test_points(self, map_dump: JsonDumpData):
        assert len(map_dump.test_points) >= 2, (
            "Dumps must have at least 2 test points for A* pair testing"
        )

    def test_test_point_coords_valid(self, map_dump: JsonDumpData):
        for tp in map_dump.test_points:
            assert len(tp.coords) == 2
            assert isinstance(tp.coords[0], (int, float))
            assert isinstance(tp.coords[1], (int, float))

    def test_test_point_trap_ids_in_range(self, map_dump: JsonDumpData):
        n = map_dump.header.trapezoid_count
        for tp in map_dump.test_points:
            assert 0 <= tp.trapezoid_id < n, (
                f"Test point '{tp.name}': trap {tp.trapezoid_id} out of range [0, {n})"
            )


class TestMetadata:
    def test_map_name(self, map_dump: JsonDumpData):
        assert map_dump.map_name != ""
