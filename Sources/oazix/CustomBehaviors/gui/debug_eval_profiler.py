from collections import deque

from Py4GWCoreLib import PyImGui
from Sources.oazix.CustomBehaviors.primitives.helpers.eval_profiler import (
    EvalProfiler,
    EvalCycleSample,
)

_SKILL_COL_COUNT = 7

_WINDOW_PRESETS = [15, 30, 60, 120, 300]

_AGG_FIELDS = (
    "enemy_targeting_ms", "enemy_targeting_calls",
    "ally_targeting_ms", "ally_targeting_calls",
    "enemy_neighbor_counting_ms", "enemy_neighbor_counting_calls",
    "ally_neighbor_counting_ms", "ally_neighbor_counting_calls",
    "gravity_center_ms", "gravity_center_calls",
    "cache_hits", "cache_misses",
)


def _percentile(sorted_values: list[float], p: float) -> float:
    """Return the p-th percentile (0-100) from a pre-sorted list."""
    if not sorted_values:
        return 0.0
    k = (len(sorted_values) - 1) * p / 100.0
    f = int(k)
    c = min(f + 1, len(sorted_values) - 1)
    d = k - f
    return sorted_values[f] + d * (sorted_values[c] - sorted_values[f])


def _compute_skill_data(history: deque[EvalCycleSample], eval_total_avg: float):
    """Compute per-skill stats from history. Returns (skill_rows, skill_infra_avgs, skill_infra_peaks)."""
    skill_totals: dict[str, list[float]] = {}
    skill_infra_sums: dict[str, dict[str, float]] = {}
    skill_infra_peaks: dict[str, dict[str, float]] = {}
    skill_infra_counts: dict[str, int] = {}
    for s in history:
        for name, ms in s.skill_timings.items():
            skill_totals.setdefault(name, []).append(ms)
        for name, infra in s.skill_infra.items():
            sums = skill_infra_sums.setdefault(name, {})
            peaks = skill_infra_peaks.setdefault(name, {})
            skill_infra_counts[name] = skill_infra_counts.get(name, 0) + 1
            for key, val in infra.items():
                sums[key] = sums.get(key, 0.0) + val
                if val > peaks.get(key, 0.0):
                    peaks[key] = val
    skill_infra_avgs: dict[str, dict[str, float]] = {}
    for name, sums in skill_infra_sums.items():
        cnt = skill_infra_counts[name]
        skill_infra_avgs[name] = {k: v / cnt for k, v in sums.items()}

    skill_rows = []
    for name, values in skill_totals.items():
        sorted_vals = sorted(values)
        skill_avg = sum(sorted_vals) / len(sorted_vals)
        p50 = _percentile(sorted_vals, 50)
        p95 = _percentile(sorted_vals, 95)
        pct_eval = (skill_avg / eval_total_avg * 100) if eval_total_avg > 0 else 0
        skill_rows.append((name, skill_avg, p50, p95, sorted_vals[-1], pct_eval, len(sorted_vals)))

    skill_rows.sort(key=lambda r: r[1], reverse=True)
    return skill_rows, skill_infra_avgs, skill_infra_peaks


def _generate_csv(history: deque[EvalCycleSample]) -> str:
    """Generate a CSV export of the profiler data for LLM analysis or spreadsheet use."""
    n = len(history)
    if n == 0:
        return ""

    def avg(fld: str) -> float:
        return sum(getattr(s, fld) for s in history) / n

    def peak(fld: str) -> float:
        return max(getattr(s, fld) for s in history)

    eval_total_avg = sum(sum(s.skill_timings.values()) for s in history) / n
    eval_total_peak = max((sum(s.skill_timings.values()) for s in history), default=0.0)
    targeting_avg = avg("enemy_targeting_ms") + avg("ally_targeting_ms")
    gravity_avg = avg("gravity_center_ms")

    total_hits = sum(s.cache_hits for s in history)
    total_misses = sum(s.cache_misses for s in history)
    total_lookups = total_hits + total_misses

    skill_rows, skill_infra_avgs, skill_infra_peaks = _compute_skill_data(history, eval_total_avg)

    lines = []

    # Metadata header (commented for CSV parsers, readable for LLMs)
    lines.append(f"# Eval Profiler Export — {n} samples")
    lines.append(f"# Eval total: {eval_total_avg:.3f}ms avg, {eval_total_peak:.3f}ms peak")
    lines.append(f"# Targeting: {targeting_avg:.3f}ms avg ({targeting_avg / eval_total_avg * 100:.0f}%)" if eval_total_avg > 0 else "# Targeting: 0ms")
    lines.append(f"# Gravity center: {gravity_avg:.3f}ms avg")
    if total_lookups > 0:
        lines.append(f"# Cache: {total_hits / total_lookups * 100:.0f}% hit ({total_hits}/{total_lookups})")
    lines.append("#")

    # Per-skill CSV
    lines.append("skill,avg_ms,p50_ms,p95_ms,peak_ms,pct_eval,samples,infra_enemy_avg,infra_enemy_peak,infra_ally_avg,infra_ally_peak,infra_gravity_avg,infra_gravity_peak")
    for name, avg_ms, p50, p95, peak_ms, pct_eval, freq in skill_rows:
        infra = skill_infra_avgs.get(name, {})
        peaks = skill_infra_peaks.get(name, {})
        lines.append(
            f"{name},{avg_ms:.4f},{p50:.4f},{p95:.4f},{peak_ms:.4f},{pct_eval:.1f},{freq},"
            f"{infra.get('enemy_targeting', 0.0):.4f},{peaks.get('enemy_targeting', 0.0):.4f},"
            f"{infra.get('ally_targeting', 0.0):.4f},{peaks.get('ally_targeting', 0.0):.4f},"
            f"{infra.get('gravity_center', 0.0):.4f},{peaks.get('gravity_center', 0.0):.4f}"
        )

    # Pipeline section
    lines.append("")
    lines.append("# Pipeline Infrastructure")
    lines.append("section,avg_ms,peak_ms,calls_per_cycle")
    pipeline_rows = [
        ("enemy_targeting", "enemy_targeting_ms", "enemy_targeting_calls"),
        ("enemy_neighbor_counting", "enemy_neighbor_counting_ms", "enemy_neighbor_counting_calls"),
        ("ally_targeting", "ally_targeting_ms", "ally_targeting_calls"),
        ("ally_neighbor_counting", "ally_neighbor_counting_ms", "ally_neighbor_counting_calls"),
        ("gravity_center", "gravity_center_ms", "gravity_center_calls"),
    ]
    for label, ms_fld, calls_fld in pipeline_rows:
        lines.append(f"{label},{avg(ms_fld):.4f},{peak(ms_fld):.4f},{avg(calls_fld):.1f}")

    return "\n".join(lines)


def render():
    TABLE_FLAGS = int(PyImGui.TableFlags.Borders | PyImGui.TableFlags.RowBg | PyImGui.TableFlags.SizingStretchProp)
    SORTABLE_TABLE_FLAGS = int(PyImGui.TableFlags.Borders | PyImGui.TableFlags.RowBg | PyImGui.TableFlags.SizingStretchProp | PyImGui.TableFlags.Sortable)

    profiler = EvalProfiler()
    profiler.enabled = PyImGui.checkbox("Enable eval profiler", profiler.enabled)

    if profiler.enabled:
        PyImGui.same_line(0, -1)
        raw = PyImGui.slider_int("##window", profiler.window_seconds, _WINDOW_PRESETS[0], _WINDOW_PRESETS[-1])
        profiler.window_seconds = min(_WINDOW_PRESETS, key=lambda p: abs(p - raw))
        PyImGui.same_line(0, -1)
        PyImGui.text("sec")

    if not profiler.enabled or len(profiler.history) == 0:
        PyImGui.text_disabled("Enable profiler and enter combat to collect data.")
        return

    history = profiler.history
    n = len(history)

    # --- single-pass aggregation (O(1) avg/peak instead of O(n) per field) ---
    _sums: dict[str, float] = {f: 0.0 for f in _AGG_FIELDS}
    _maxes: dict[str, float] = {f: 0.0 for f in _AGG_FIELDS}
    eval_total_sum = 0.0
    eval_total_peak = 0.0
    combined_infra_peak = 0.0

    for s in history:
        for fld in _AGG_FIELDS:
            v = getattr(s, fld)
            _sums[fld] += v
            if v > _maxes[fld]:
                _maxes[fld] = v
        et = sum(s.skill_timings.values())
        eval_total_sum += et
        if et > eval_total_peak:
            eval_total_peak = et
        ci = s.enemy_targeting_ms + s.ally_targeting_ms + s.gravity_center_ms
        if ci > combined_infra_peak:
            combined_infra_peak = ci

    eval_total_avg = eval_total_sum / n

    def avg(fld: str) -> float:
        return _sums[fld] / n

    def peak(fld: str) -> float:
        return _maxes[fld]

    # --- summary ---
    targeting_avg = avg("enemy_targeting_ms") + avg("ally_targeting_ms")
    other_avg = max(eval_total_avg - targeting_avg, 0.0)
    targeting_pct = (targeting_avg / eval_total_avg * 100) if eval_total_avg > 0 else 0

    PyImGui.text(f"Samples: {n} eval cycles")
    PyImGui.same_line(0, -1)
    if PyImGui.button("Copy CSV"):
        csv = _generate_csv(history)
        PyImGui.set_clipboard_text(csv)
    PyImGui.separator()
    PyImGui.text(f"Eval total: {eval_total_avg:.2f}ms avg | {eval_total_peak:.2f}ms peak")
    PyImGui.text(f"  Targeting: {targeting_avg:.2f}ms ({targeting_pct:.0f}%)  |  Other: {other_avg:.2f}ms ({100 - targeting_pct:.0f}%)")

    total_hits = int(_sums["cache_hits"])
    total_misses = int(_sums["cache_misses"])
    total_lookups = total_hits + total_misses
    if total_lookups > 0:
        hit_rate = total_hits / total_lookups * 100
        PyImGui.text(f"  Cache: {hit_rate:.0f}% hit ({total_hits} / {total_lookups})")

    PyImGui.spacing()

    # --- per-skill breakdown ---
    PyImGui.text("Per-Skill Eval Cost:")
    PyImGui.same_line(0, -1)
    PyImGui.text_disabled("(?)")
    if PyImGui.is_item_hovered():
        PyImGui.begin_tooltip()
        PyImGui.text("Skills that early-return (cooldown, wrong state) cost <0.01ms.")
        PyImGui.text("Percentiles reveal the true cost distribution:")
        PyImGui.spacing()
        PyImGui.text("P50 near 0, P95 high  = expensive only when active (e.g. in combat)")
        PyImGui.text("P50 high              = consistently expensive every eval")
        PyImGui.spacing()
        PyImGui.text("Avg(ms) — mean across all evals (drives %Eval)")
        PyImGui.text("P50     — median eval cost (typical case)")
        PyImGui.text("P95     — 95th percentile (near-worst case)")
        PyImGui.end_tooltip()
    if PyImGui.begin_child("skill_breakdown", size=(0, 250), border=True, flags=0):
        skill_rows, skill_infra_avgs, skill_infra_peaks = _compute_skill_data(history, eval_total_avg)

        if PyImGui.begin_table("skill_table", 7, SORTABLE_TABLE_FLAGS):
            PyImGui.table_setup_column("Skill", PyImGui.TableColumnFlags.WidthStretch)
            PyImGui.table_setup_column("Avg(ms)", PyImGui.TableColumnFlags.WidthFixed | PyImGui.TableColumnFlags.DefaultSort, 70)
            PyImGui.table_setup_column("P50", PyImGui.TableColumnFlags.WidthFixed, 50)
            PyImGui.table_setup_column("P95", PyImGui.TableColumnFlags.WidthFixed, 50)
            PyImGui.table_setup_column("Peak", PyImGui.TableColumnFlags.WidthFixed, 50)
            PyImGui.table_setup_column("%Eval", PyImGui.TableColumnFlags.WidthFixed, 45)
            PyImGui.table_setup_column("Calls", PyImGui.TableColumnFlags.WidthFixed, 40)
            PyImGui.table_headers_row()

            # Apply sort from clicked header
            sort_specs = PyImGui.table_get_sort_specs()
            if sort_specs is not None and sort_specs.Specs is not None:
                col = sort_specs.Specs.ColumnIndex
                if 0 <= col < _SKILL_COL_COUNT:
                    desc = sort_specs.Specs.SortDirection == PyImGui.SortDirection.Descending
                    skill_rows.sort(key=lambda r: r[col], reverse=desc)

            for name, avg_ms, p50, p95, peak_ms, pct_eval, freq in skill_rows:
                PyImGui.table_next_row()
                PyImGui.table_next_column()
                PyImGui.text(name)
                if PyImGui.is_item_hovered():
                    infra = skill_infra_avgs.get(name, {})
                    peaks = skill_infra_peaks.get(name, {})
                    enemy = infra.get("enemy_targeting", 0.0)
                    ally = infra.get("ally_targeting", 0.0)
                    gravity = infra.get("gravity_center", 0.0)
                    other = max(avg_ms - enemy - ally - gravity, 0.0)
                    PyImGui.begin_tooltip()
                    PyImGui.text("Eval cost breakdown (avg / peak):")
                    if enemy > 0.001:
                        PyImGui.text(f"  Enemy targeting:  {enemy:.3f} / {peaks.get('enemy_targeting', 0.0):.3f}ms")
                    if ally > 0.001:
                        PyImGui.text(f"  Ally targeting:   {ally:.3f} / {peaks.get('ally_targeting', 0.0):.3f}ms")
                    if gravity > 0.001:
                        PyImGui.text(f"  Gravity center:   {gravity:.3f} / {peaks.get('gravity_center', 0.0):.3f}ms")
                    if other > 0.001:
                        PyImGui.text(f"  Other logic:      {other:.3f}ms")
                    if enemy <= 0.001 and ally <= 0.001 and gravity <= 0.001:
                        PyImGui.text("  No infrastructure calls during eval")
                    PyImGui.end_tooltip()
                PyImGui.table_next_column()
                PyImGui.text(f"{avg_ms:.3f}")
                PyImGui.table_next_column()
                PyImGui.text(f"{p50:.3f}")
                PyImGui.table_next_column()
                PyImGui.text(f"{p95:.3f}")
                PyImGui.table_next_column()
                PyImGui.text(f"{peak_ms:.3f}")
                PyImGui.table_next_column()
                PyImGui.text(f"{pct_eval:.1f}%")
                PyImGui.table_next_column()
                PyImGui.text(str(freq))

            PyImGui.end_table()
        PyImGui.end_child()

    PyImGui.spacing()

    # --- pipeline breakdown ---
    PyImGui.text("Targeting Infrastructure:")
    PyImGui.same_line(0, -1)
    PyImGui.text_disabled("(?)")
    if PyImGui.is_item_hovered():
        PyImGui.begin_tooltip()
        PyImGui.text("Total cost of targeting functions across all phases (eval + execute).")
        PyImGui.text("Unlike per-skill eval cost above, this includes work done")
        PyImGui.text("during skill execution (e.g. gravity center before casting).")
        PyImGui.end_tooltip()
    if PyImGui.begin_table("pipeline_table", 4, TABLE_FLAGS):
        PyImGui.table_setup_column("Section", PyImGui.TableColumnFlags.WidthStretch)
        PyImGui.table_setup_column("Avg(ms)", PyImGui.TableColumnFlags.WidthFixed, 65)
        PyImGui.table_setup_column("Peak(ms)", PyImGui.TableColumnFlags.WidthFixed, 65)
        PyImGui.table_setup_column("Calls/cycle", PyImGui.TableColumnFlags.WidthFixed, 70)
        PyImGui.table_headers_row()

        rows = [
            ("Enemy targeting", "enemy_targeting_ms", "enemy_targeting_calls",
             "Full enemy query: get_combined_enemy_targets + filtering + sortable data build.\nIncludes distance, HP, profession checks per candidate."),
            ("  Neighbor counting", "enemy_neighbor_counting_ms", "enemy_neighbor_counting_calls",
             "O(n^2) distance checks counting nearby enemies per candidate.\nDrives AoE skill target prioritization (range_to_count_enemies)."),
            ("Ally targeting", "ally_targeting_ms", "ally_targeting_calls",
             "Full ally query: array fetch + alive/distance filter + sortable data build.\nIncludes distance, HP, profession, energy checks per candidate."),
            ("  Neighbor counting", "ally_neighbor_counting_ms", "ally_neighbor_counting_calls",
             "O(n^2) distance checks counting nearby enemies/allies per candidate.\nDrives healing priority (range_to_count_enemies, range_to_count_allies)."),
            ("Gravity center", "gravity_center_ms", "gravity_center_calls",
             "find_optimal_gravity_center: brute-force geometric search for best\ncasting position to maximize ally coverage within range.\nCalled during execute phase by positioning skills (TAO, EBSoH, etc.)."),
        ]

        for label, ms_field, calls_field, tooltip in rows:
            PyImGui.table_next_row()
            PyImGui.table_next_column()
            PyImGui.text(label)
            if PyImGui.is_item_hovered():
                PyImGui.begin_tooltip()
                for line in tooltip.split("\n"):
                    PyImGui.text(line)
                PyImGui.end_tooltip()
            PyImGui.table_next_column()
            PyImGui.text(f"{avg(ms_field):.3f}")
            PyImGui.table_next_column()
            PyImGui.text(f"{peak(ms_field):.3f}")
            PyImGui.table_next_column()
            PyImGui.text(f"{avg(calls_field):.1f}")

        # total row
        total_infra_avg = targeting_avg + avg("gravity_center_ms")
        PyImGui.table_next_row()
        PyImGui.table_next_column()
        PyImGui.text("TOTAL")
        PyImGui.table_next_column()
        PyImGui.text(f"{total_infra_avg:.3f}")
        PyImGui.table_next_column()
        PyImGui.text(f"{combined_infra_peak:.3f}")
        PyImGui.table_next_column()

        PyImGui.end_table()
