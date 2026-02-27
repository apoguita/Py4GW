import re
import random
from dataclasses import dataclass, asdict
from collections.abc import Callable

import Py4GW
import PyImGui
from Py4GWCoreLib.py4gwcorelib_src.Timer import ThrottledTimer
from Py4GWCoreLib.py4gwcorelib_src.Color import Color, ColorPalette

update_throttle = ThrottledTimer(1000)  # Throttle updates to at most once per second


@dataclass
class ParsedMetricName:
    """Normalized representation of a profiler metric name.

    The profiler emits one metric schema with multiple naming patterns:
    pure dotted names (e.g. `Draw.Callback.Data.SharedMemory.Update`) and
    dotted prefixes followed by path-like script names (e.g.
    `Main.Callback.Update.Guild Wars\\Items & Loot/InventoryPlus.py`).

    This dataclass stores both the raw tokenization and semantic fields used for
    grouping (`phase`, `subject_token`, `operation_token`, `display_token`).
    """

    raw_name: str
    dot_tokens: list[str]
    hierarchy_tokens: list[str]
    semantic_hierarchy_tokens: list[str]
    path_tokens: list[str]
    path_tail_tokens: list[str]
    all_tokens: list[str]
    phase: str
    dot_prefix_tokens: list[str]
    path_tail: str
    is_path_metric: bool
    script_path: str
    script_name: str
    script_like: str
    leaf_token: str
    operation_token: str
    subject_token: str
    display_token: str

    def to_dict(self) -> dict:
        """Return the parsed record as a plain dictionary."""
        return asdict(self)


class ProfilerMetricNameCatalog:
    """Encapsulate profiler metric-name fetching, parsing, indexing, and lookup.

    The class is designed to be portable: a caller can use it without relying on
    any UI helpers. It can ingest data from either live Py4GW profiler metrics or
    pasted console output, parse the naming patterns, and expose indexed/grouped
    access to the normalized results.

    Typical usage:
        catalog = ProfilerMetricNameCatalog()
        catalog.refresh_from_live()
        # or catalog.load_console_dump(text)
        rows = catalog.items
        grouped = catalog.group_by_attr("subject_token")
    """

    _METRIC_LINE_RE = re.compile(
        r"""
        ^.*?\[print:\]\s*
        (?P<name>.+?)
        :\s+Min=
        """,
        re.VERBOSE,
    )

    _GENERIC_OPERATION_LEAVES = {
        "update",
        "draw",
        "main",
        "total",
        "updateptr",
        "updatecache",
    }

    def __init__(self) -> None:
        """Create an empty catalog with no loaded data and no indexes."""
        self.raw_names: list[str] = []
        self.items: list[ParsedMetricName] = []
        self.stats_by_raw_name: dict[str, dict[str, float]] = {}
        self.history_by_raw_name: dict[str, list[float]] = {}

        self.by_raw_name: dict[str, ParsedMetricName] = {}
        self.by_phase: dict[str, list[ParsedMetricName]] = {}
        self.by_subject: dict[str, list[ParsedMetricName]] = {}
        self.by_display: dict[str, list[ParsedMetricName]] = {}
        self.by_script_path: dict[str, list[ParsedMetricName]] = {}
        self.by_script_name: dict[str, list[ParsedMetricName]] = {}
        self.by_operation: dict[str, list[ParsedMetricName]] = {}
        self.by_semantic_key: dict[tuple[str, ...], list[ParsedMetricName]] = {}

    def clear(self) -> None:
        """Remove loaded names, parsed items, and all indexes."""
        self.raw_names.clear()
        self.items.clear()
        self.stats_by_raw_name.clear()
        self.history_by_raw_name.clear()
        self.by_raw_name.clear()
        self.by_phase.clear()
        self.by_subject.clear()
        self.by_display.clear()
        self.by_script_path.clear()
        self.by_script_name.clear()
        self.by_operation.clear()
        self.by_semantic_key.clear()

    def extract_metric_name_from_console_line(self, line: str) -> str | None:
        """Extract a raw metric name from a console print line.

        Args:
            line: Console output line that may contain a profiler metric print.

        Returns:
            The metric name if the line matches the profiler print format,
            otherwise `None`.
        """
        match = self._METRIC_LINE_RE.match(line.strip())
        if not match:
            return None
        return match.group("name").strip()

    def parse_name(self, name: str) -> ParsedMetricName:
        """Parse a single raw profiler metric name into semantic tokens.

        Naming rules handled here:
        - Common leading categories split by `.` (phase, callback buckets, etc.)
        - Optional path-like tail split by `/` or `\\`
        - Path metrics preserve full path (`script_path`) but expose a compact
          filename leaf (`script_name`) for display
        - Generic trailing operation markers (`Update`, `Draw`, `UpdatePtr`, ...)
          are recognized so grouping can prefer the measured subject instead

        Args:
            name: Raw profiler metric name.

        Returns:
            ParsedMetricName: Normalized parsed representation.
        """
        raw = name.strip()
        dot_tokens = [t for t in raw.split(".") if t]
        phase = dot_tokens[0] if dot_tokens else ""

        path_start_idx = -1
        for i, token in enumerate(dot_tokens):
            if "/" in token or "\\" in token:
                path_start_idx = i
                break

        is_path_metric = path_start_idx >= 0
        if is_path_metric:
            dot_prefix_tokens = dot_tokens[:path_start_idx]
            path_tail = ".".join(dot_tokens[path_start_idx:])
        else:
            dot_prefix_tokens = dot_tokens[:-1] if len(dot_tokens) > 1 else []
            path_tail = dot_tokens[-1] if dot_tokens else raw

        path_tail_tokens = [t for t in re.split(r"[\\/]+", path_tail) if t]
        path_tokens = [t for t in re.split(r"[\\/]+", raw) if t]
        hierarchy_tokens = (dot_prefix_tokens + path_tail_tokens) if is_path_metric else list(dot_tokens)
        all_tokens = [t for t in re.split(r"[./\\\\]+", raw) if t]

        leaf_token = path_tail_tokens[-1] if (is_path_metric and path_tail_tokens) else (dot_tokens[-1] if dot_tokens else raw)

        if is_path_metric:
            script_like = path_tail
        elif len(dot_tokens) >= 2:
            script_like = dot_tokens[-2]
        else:
            script_like = leaf_token

        script_path = path_tail if is_path_metric else ""
        script_name = path_tail_tokens[-1] if (is_path_metric and path_tail_tokens) else script_like

        operation_token = leaf_token
        subject_token = script_name if is_path_metric else script_like

        leaf_is_generic_operation = operation_token.lower() in self._GENERIC_OPERATION_LEAVES

        if is_path_metric:
            display_token = script_name
        elif leaf_is_generic_operation:
            display_token = subject_token
        else:
            display_token = leaf_token

        semantic_hierarchy_tokens = list(hierarchy_tokens)
        if semantic_hierarchy_tokens:
            if is_path_metric:
                semantic_hierarchy_tokens[-1] = script_name
            elif leaf_is_generic_operation and len(semantic_hierarchy_tokens) >= 2:
                semantic_hierarchy_tokens = semantic_hierarchy_tokens[:-1]

        return ParsedMetricName(
            raw_name=raw,
            dot_tokens=dot_tokens,
            hierarchy_tokens=hierarchy_tokens,
            semantic_hierarchy_tokens=semantic_hierarchy_tokens,
            path_tokens=path_tokens,
            path_tail_tokens=path_tail_tokens,
            all_tokens=all_tokens,
            phase=phase,
            dot_prefix_tokens=dot_prefix_tokens,
            path_tail=path_tail,
            is_path_metric=is_path_metric,
            script_path=script_path,
            script_name=script_name,
            script_like=script_like,
            leaf_token=leaf_token,
            operation_token=operation_token,
            subject_token=subject_token,
            display_token=display_token,
        )

    def load_names(self, names: list[str]) -> list[ParsedMetricName]:
        """Load and parse raw metric names, replacing the catalog contents.

        Args:
            names: List of raw metric names.

        Returns:
            Parsed records in the same order as the input (after trimming empty
            entries).
        """
        self.clear()
        self.raw_names = [n.strip() for n in names if n and n.strip()]
        self.items = [self.parse_name(name) for name in self.raw_names]
        self._rebuild_indexes()
        return self.items

    def load_console_dump(self, text: str) -> list[ParsedMetricName]:
        """Parse profiler metric names from pasted console output and store them.

        Args:
            text: Multiline console dump containing `[print:] ...: Min=...` rows.

        Returns:
            Parsed metric-name records extracted from the dump.
        """
        names: list[str] = []
        for line in text.splitlines():
            name = self.extract_metric_name_from_console_line(line)
            if name:
                names.append(name)
        return self.load_names(names)

    def get_live_metric_names(self) -> list[str]:
        """Fetch live profiler metric names from Py4GW if available.

        Returns:
            List of raw metric names. Returns an empty list when Py4GW is not
            available or the call fails.
        """
        if Py4GW is None:
            return []
        try:
            return list(Py4GW.Console.get_profiler_metric_names())
        except Exception:
            return []

    def get_live_profiler_reports(self) -> list[tuple]:
        """Fetch live profiler report rows from Py4GW if available.

        Returns:
            A list of report tuples in the format expected from
            `Py4GW.Console.get_profiler_reports()`, or an empty list on failure.
        """
        if Py4GW is None:
            return []
        try:
            return list(Py4GW.Console.get_profiler_reports())
        except Exception:
            return []

    def refresh_from_live(self) -> list[ParsedMetricName]:
        """Fetch live metric names from Py4GW, parse them, and rebuild indexes.

        Returns:
            Parsed metric-name records for the live profiler set.
        """
        parsed = self.load_names(self.get_live_metric_names())
        self._load_stats_from_reports(self.get_live_profiler_reports())
        return parsed

    def get_live_profiler_history(self, name: str) -> list[float]:
        """Fetch a profiler history trace for a metric from Py4GW, if available."""
        if Py4GW is None:
            return []
        try:
            return [float(v) for v in Py4GW.Console.get_profiler_history(name)]
        except Exception:
            return []

    def has_usage_stats(self) -> bool:
        """Return `True` when live profiler timing stats are available."""
        return bool(self.stats_by_raw_name)

    def clear_usage_stats(self) -> None:
        """Clear cached profiler timing stats while keeping parsed names/indexes."""
        self.stats_by_raw_name.clear()
        self.history_by_raw_name.clear()
        Py4GW.Console.clear_profiler_history()

    def get_stats(self, raw_name: str) -> dict[str, float] | None:
        """Return timing stats for a raw metric name, if available."""
        return self.stats_by_raw_name.get(raw_name)

    def get_history(self, raw_name: str, refresh: bool = False) -> list[float]:
        """Return cached profiler history for a raw metric name, optionally refreshing."""
        if not refresh and raw_name in self.history_by_raw_name:
            return self.history_by_raw_name[raw_name]
        hist = self.get_live_profiler_history(raw_name)
        self.history_by_raw_name[raw_name] = hist
        return hist

    def get(self, raw_name: str) -> ParsedMetricName | None:
        """Return the parsed record for an exact raw metric name, if present."""
        return self.by_raw_name.get(raw_name)

    def filter(self, predicate: Callable[[ParsedMetricName], bool]) -> list[ParsedMetricName]:
        """Return parsed items matching a predicate.

        Args:
            predicate: Function that receives a parsed record and returns `True`
                when the record should be included.

        Returns:
            Matching parsed records.
        """
        return [item for item in self.items if predicate(item)]

    def filter_text(self, needle: str) -> list[ParsedMetricName]:
        """Return parsed items whose normalized fields contain a text fragment.

        Args:
            needle: Case-insensitive substring matched against raw name, phase,
                display token, subject token, script path/name, and all tokens.

        Returns:
            Matching parsed records. Empty `needle` returns all items.
        """
        if not needle:
            return list(self.items)
        n = needle.lower()
        return self.filter(
            lambda item: (
                n in item.raw_name.lower()
                or n in item.phase.lower()
                or n in item.display_token.lower()
                or n in item.subject_token.lower()
                or n in item.script_name.lower()
                or n in item.script_path.lower()
                or any(n in tok.lower() for tok in item.all_tokens)
            )
        )

    def group_by_attr(self, attr_name: str) -> dict[str, list[ParsedMetricName]]:
        """Group records by any attribute on `ParsedMetricName`.

        Args:
            attr_name: Name of a `ParsedMetricName` attribute (for example
                `phase`, `subject_token`, `operation_token`, `script_path`).

        Returns:
            Mapping from attribute value (as string) to matching records.
        """
        grouped: dict[str, list[ParsedMetricName]] = {}
        for item in self.items:
            value = getattr(item, attr_name, "")
            grouped.setdefault(str(value), []).append(item)
        return grouped

    def group_by_semantic_prefix(self, depth: int) -> dict[tuple[str, ...], list[ParsedMetricName]]:
        """Group records by a prefix of `semantic_hierarchy_tokens`.

        Args:
            depth: Number of semantic hierarchy tokens to keep in the grouping
                key. `0` groups all records together.

        Returns:
            Mapping from semantic token tuple prefix to matching records.
        """
        depth = max(0, depth)
        grouped: dict[tuple[str, ...], list[ParsedMetricName]] = {}
        for item in self.items:
            key = tuple(item.semantic_hierarchy_tokens[:depth])
            grouped.setdefault(key, []).append(item)
        return grouped

    def summary_counts(self) -> dict[str, int]:
        """Return lightweight diagnostics about the loaded catalog.

        Returns:
            Counts for total records and distinct keys in core indexes.
        """
        return {
            "items": len(self.items),
            "phases": len(self.by_phase),
            "subjects": len(self.by_subject),
            "displays": len(self.by_display),
            "script_paths": len(self.by_script_path),
            "script_names": len(self.by_script_name),
            "operations": len(self.by_operation),
            "semantic_keys": len(self.by_semantic_key),
        }

    def print_sample(self, limit: int = 20) -> None:
        """Print a sample of parsed records for manual verification.

        Args:
            limit: Maximum number of parsed records to print.
        """
        for idx, item in enumerate(self.items[:limit], start=1):
            print(f"[{idx}] {item.raw_name}")
            print(f"  phase       : {item.phase}")
            print(f"  script_path : {item.script_path}")
            print(f"  script_name : {item.script_name}")
            print(f"  subject     : {item.subject_token}")
            print(f"  operation   : {item.operation_token}")
            print(f"  display     : {item.display_token}")
            print(f"  semantic    : {item.semantic_hierarchy_tokens}")
            stats = self.stats_by_raw_name.get(item.raw_name)
            if stats:
                print(f"  avg         : {stats['avg']:.4f}ms")
        if len(self.items) > limit:
            print(f"... ({len(self.items) - limit} more)")

    def build_usage_groups_by_display(
        self,
        items: list[ParsedMetricName] | None = None,
        include_phases: set[str] | None = None,
    ) -> list[dict]:
        """Aggregate usage stats by normalized display token (leaf/entity label).

        A single display group may contain metrics from multiple phases
        (`Draw`, `Main`, `Update`). This method aggregates those phase-specific
        average timings and returns rows sorted by the selected-phase total.

        Args:
            items: Optional subset of parsed items to aggregate. If omitted, all
                catalog items are used.
            include_phases: Optional phase filter controlling which phases
                contribute to `selected_total_avg`. If omitted, `Draw`, `Main`,
                and `Update` are all included.

        Returns:
            list[dict]: Aggregated usage rows with phase totals, member records,
            and sort-ready totals.
        """
        source_items = self.items if items is None else items
        selected_phases = include_phases or {"Draw", "Main", "Update"}

        grouped: dict[str, dict] = {}
        for item in source_items:
            row = grouped.get(item.display_token)
            if row is None:
                row = {
                    "display": item.display_token,
                    "subjects": set(),
                    "script_paths": set(),
                    "members": [],
                    "phase_stats": {
                        "Draw": {"min": 0.0, "avg": 0.0, "p50": 0.0, "p95": 0.0, "p99": 0.0, "max": 0.0},
                        "Main": {"min": 0.0, "avg": 0.0, "p50": 0.0, "p95": 0.0, "p99": 0.0, "max": 0.0},
                        "Update": {"min": 0.0, "avg": 0.0, "p50": 0.0, "p95": 0.0, "p99": 0.0, "max": 0.0},
                    },
                    "selected_stats": {"min": 0.0, "avg": 0.0, "p50": 0.0, "p95": 0.0, "p99": 0.0, "max": 0.0},
                    "all_stats": {"min": 0.0, "avg": 0.0, "p50": 0.0, "p95": 0.0, "p99": 0.0, "max": 0.0},
                }
                grouped[item.display_token] = row

            row["subjects"].add(item.subject_token)
            if item.script_path:
                row["script_paths"].add(item.script_path)
            row["members"].append(item)

            stats = self.stats_by_raw_name.get(item.raw_name)
            if not stats:
                continue

            phase_key = item.phase if item.phase in ("Draw", "Main", "Update") else None

            for metric_key in ("min", "avg", "p50", "p95", "p99", "max"):
                value = stats[metric_key]
                row["all_stats"][metric_key] += value
                if item.phase in selected_phases:
                    row["selected_stats"][metric_key] += value
                if phase_key is not None:
                    row["phase_stats"][phase_key][metric_key] += value

        rows = list(grouped.values())
        for row in rows:
            row["subjects"] = sorted(row["subjects"])
            row["script_paths"] = sorted(row["script_paths"])
            row["members"].sort(
                key=lambda m: self.stats_by_raw_name.get(m.raw_name, {}).get("avg", 0.0),
                reverse=True,
            )

        rows.sort(key=lambda r: r["selected_stats"]["avg"], reverse=True)
        return rows

    def _load_stats_from_reports(self, reports: list[tuple]) -> None:
        """Load timing stats from profiler reports into a raw-name lookup map."""
        self.stats_by_raw_name = {}
        for row in reports:
            try:
                name, min_time, avg_time, p50, p95, p99, max_time = row
            except Exception:
                continue
            self.stats_by_raw_name[str(name)] = {
                "min": float(min_time),
                "avg": float(avg_time),
                "p50": float(p50),
                "p95": float(p95),
                "p99": float(p99),
                "max": float(max_time),
            }

    def _rebuild_indexes(self) -> None:
        """Rebuild all lookup indexes from the current `items` list."""
        self.by_raw_name = {item.raw_name: item for item in self.items}
        self.by_phase = {}
        self.by_subject = {}
        self.by_display = {}
        self.by_script_path = {}
        self.by_script_name = {}
        self.by_operation = {}
        self.by_semantic_key = {}

        for item in self.items:
            self.by_phase.setdefault(item.phase, []).append(item)
            self.by_subject.setdefault(item.subject_token, []).append(item)
            self.by_display.setdefault(item.display_token, []).append(item)
            if item.script_path:
                self.by_script_path.setdefault(item.script_path, []).append(item)
            self.by_script_name.setdefault(item.script_name, []).append(item)
            self.by_operation.setdefault(item.operation_token, []).append(item)
            self.by_semantic_key.setdefault(tuple(item.semantic_hierarchy_tokens), []).append(item)


# Lightweight viewer state (optional UI built on top of the catalog).
_initialized = False
_catalog = ProfilerMetricNameCatalog()
_ui_filter_text = ""
_ui_show_details = False
_ui_max_rows = 15
_ui_include_draw = True
_ui_include_main = True
_ui_include_update = True
_ui_selected_entry = ""
_ui_show_selected_window = True
_history_seconds_per_sample = 0.1
_history_tick_seconds = 5.0
_ui_entry_color_map: dict[str, str] = {}
_ui_palette_order: list[str] = []


def _ensure_loaded() -> None:
    """Initialize the viewer cache once from live metrics."""
    global _initialized
    if _initialized:
        return
    _initialized = True
    _catalog.refresh_from_live()


def _auto_refresh_if_needed() -> None:
    """Refresh the shared catalog at most once per second using the throttle."""
    if update_throttle.IsExpired():
        _catalog.refresh_from_live()
        update_throttle.Reset()


def _entry_palette_names() -> list[str]:
    """Return a randomized full-palette order using every ColorPalette entry."""
    global _ui_palette_order
    if _ui_palette_order:
        return list(_ui_palette_order)
    _ui_palette_order = [n.lower() for n in ColorPalette.ListColors()]
    random.shuffle(_ui_palette_order)
    return list(_ui_palette_order)


def _c4(name: str, alpha: float | None = None) -> tuple[float, float, float, float]:
    """Return a normalized color tuple from ColorPalette, optionally overriding alpha."""
    c = ColorPalette.GetColor(name).copy()
    if alpha is not None:
        c = c.opacity(alpha)
    return c.to_tuple_normalized()


def _c32(name: str, alpha: float | None = None) -> int:
    """Return packed ABGR color from ColorPalette, optionally overriding alpha."""
    c = ColorPalette.GetColor(name).copy()
    if alpha is not None:
        c = c.opacity(alpha)
    return c.to_color()


def _entry_color_name(key: str) -> str:
    """Deterministically map an entry label to a palette color name."""
    mapped = _ui_entry_color_map.get(key)
    if mapped:
        return mapped
    names = _entry_palette_names()
    if not names:
        return "dodger_blue"
    h = 0
    for ch in key:
        h = (h * 131 + ord(ch)) & 0xFFFFFFFF
    return names[h % len(names)]


def _entry_color32(key: str) -> int:
    """Packed color for a grouped entry, consistent across widgets."""
    return _c32(_entry_color_name(key))


def _entry_color4(key: str) -> tuple[float, float, float, float]:
    """Normalized color for a grouped entry, consistent across widgets."""
    return _c4(_entry_color_name(key))


def _color_luminance(color_name: str) -> float:
    """Return perceptual luminance of a palette color (0..1)."""
    c = ColorPalette.GetColor(color_name)
    return (0.2126 * c.r + 0.7152 * c.g + 0.0722 * c.b) / 255.0


def _contrast_text_color32(fill_color_name: str) -> int:
    """Pick black/white text based on fill brightness."""
    return _c32("black") if _color_luminance(fill_color_name) >= 0.60 else _c32("white")


def _reroll_entry_palette() -> None:
    """Randomize the full palette order again (uses every palette entry name)."""
    global _ui_palette_order
    _ui_palette_order = [n.lower() for n in ColorPalette.ListColors()]
    random.shuffle(_ui_palette_order)


def _log_color_pool_and_assignments(rows: list[dict] | None = None) -> None:
    """Log all palette entries and current entry assignments (reuse diagnostics)."""
    pool = _entry_palette_names()
    print("=== Profiler UI Color Pool (full ColorPalette, randomized order) ===")
    rgba_aliases: dict[tuple[int, int, int, int], list[str]] = {}
    for i, name in enumerate(pool, start=1):
        c = ColorPalette.GetColor(name)
        rgba = c.to_tuple()
        rgba_aliases.setdefault(rgba, []).append(name)
        print(f"[{i:03d}] {name:<18} rgba={rgba} lum={_color_luminance(name):.3f}")

    dup_alias_sets = [names for names in rgba_aliases.values() if len(names) > 1]
    if dup_alias_sets:
        print("=== Palette aliases sharing the same RGBA ===")
        for names in dup_alias_sets:
            print(" - " + ", ".join(names))

    if rows is None:
        return

    print("=== Current Entry -> Color Assignment ===")
    reverse: dict[str, list[str]] = {}
    for row in rows:
        display = str(row.get("display", ""))
        if not display or display == "Others":
            continue
        color_name = _entry_color_name(display)
        reverse.setdefault(color_name, []).append(display)
        print(f"{display} -> {color_name}")

    reused = {k: v for k, v in reverse.items() if len(v) > 1}
    if reused:
        print("=== Reused colors detected ===")
        for color_name, displays in reused.items():
            print(f"{color_name}: {', '.join(displays)}")
    else:
        print("No color reuse detected for visible entries.")


def _refresh_entry_color_assignments(rows: list[dict]) -> None:
    """Assign unique palette colors to visible rows before any reuse.

    Colors are assigned in current row order (usually usage-descending), which
    makes top consumers get the best visual distinction first.
    """
    global _ui_entry_color_map
    pool = _entry_palette_names()
    if not pool:
        _ui_entry_color_map = {}
        return
    new_map: dict[str, str] = {}
    pool_len = len(pool)
    for idx, row in enumerate(rows):
        display = str(row.get("display", ""))
        if not display or display == "Others":
            continue
        # Unique until pool exhaustion, then wrap.
        new_map[display] = pool[idx % pool_len]
    _ui_entry_color_map = new_map


def _phase_color_name(phase: str) -> str:
    """Map profiler phase names to palette color names."""
    mapping = {
        "Draw": "dodger_blue",
        "Main": "gold",
        "Update": "light_green",
    }
    return mapping.get(phase, "light_gray")


def _dominant_phase(row: dict) -> str:
    """Return the phase with the highest avg usage for a grouped row."""
    phase_stats = row.get("phase_stats", {})
    best_phase = "Update"
    best_avg = -1.0
    for phase in ("Draw", "Main", "Update"):
        avg = float(phase_stats.get(phase, {}).get("avg", 0.0))
        if avg > best_avg:
            best_avg = avg
            best_phase = phase
    return best_phase


def _draw_top_usage_stacked_bar(rows: list[dict]) -> str | None:
    """Draw a stacked 100% usage bar with an 'Others' bucket for tiny entries.

    Returns:
        The clicked entry display token, `__others__` for Others, or `None`.
    """
    if not rows:
        return None

    total_usage = sum(r["selected_stats"]["avg"] for r in rows)
    if total_usage <= 0.0:
        PyImGui.text("No usage totals available for stacked bar")
        return None

    avail_w, _avail_h = PyImGui.get_content_region_avail()
    bar_w = max(220.0, avail_w)
    bar_h = 22.0
    start_x, start_y = PyImGui.get_cursor_screen_pos()

    PyImGui.text_colored("Usage Share", _c4("light_blue"))
    PyImGui.same_line(0, -1)
    PyImGui.text(f"(100% of included avg totals, frame total {total_usage:.3f}ms)")
    PyImGui.dummy(int(bar_w), int(bar_h))

    bg = _c32("gw_disabled")
    border = _c32("dark_gray")
    PyImGui.draw_list_add_rect_filled(start_x, start_y + 16, start_x + bar_w, start_y + 16 + bar_h, bg, 0.0, 0)
    PyImGui.draw_list_add_rect(start_x, start_y + 16, start_x + bar_w, start_y + 16 + bar_h, border, 0.0, 0, 1.5)

    # Build visible segments and collapse too-small ones into Others.
    min_px = 14.0
    visible_segments = []
    others_rows = []
    for row in rows:
        width_px = (row["selected_stats"]["avg"] / total_usage) * bar_w
        if width_px < min_px:
            others_rows.append(row)
        else:
            visible_segments.append(row)

    if others_rows:
        others_total = sum(r["selected_stats"]["avg"] for r in others_rows)
        visible_segments.append(
            {
                "display": "Others",
                "selected_stats": {"avg": others_total},
                "members": [m for r in others_rows for m in r["members"]],
                "_others_rows": others_rows,
            }
        )

    clicked_entry: str | None = None
    offset = 0.0
    inner_y1 = start_y + 17
    inner_y2 = start_y + 16 + bar_h - 1

    for idx, row in enumerate(visible_segments):
        share = row["selected_stats"]["avg"] / total_usage
        seg_w = (bar_w - offset) if idx == len(visible_segments) - 1 else max(1.0, share * bar_w)
        x1 = start_x + offset
        x2 = start_x + offset + seg_w
        offset += seg_w

        color_name = _entry_color_name(row["display"]) if row["display"] != "Others" else "dark_gray"
        color = _c32(color_name)
        PyImGui.draw_list_add_rect_filled(x1, inner_y1, x2, inner_y2, color, 0.0, 0)
        PyImGui.draw_list_add_rect(x1, inner_y1, x2, inner_y2, border, 0.0, 0, 1.0)

        if seg_w > 60:
            label = row["display"]
            if len(label) > 18:
                label = label[:15] + "..."
            PyImGui.draw_list_add_text(x1 + 3, inner_y1 + 2, _contrast_text_color32(color_name), label)

        PyImGui.set_cursor_screen_pos(x1, inner_y1)
        if PyImGui.invisible_button(f"##usage_stack_{idx}", seg_w, max(1.0, inner_y2 - inner_y1)):
            clicked_entry = "__others__" if row["display"] == "Others" else row["display"]
        if PyImGui.is_item_hovered() and PyImGui.begin_tooltip():
            pct = share * 100.0
            PyImGui.text_colored(row["display"], _c4("gold"))
            PyImGui.text(f"Included total avg: {row['selected_stats']['avg']:.3f}ms")
            PyImGui.text(f"Usage share: {pct:.1f}%")
            if row["display"] == "Others":
                subrows = row.get("_others_rows", [])
                PyImGui.separator()
                PyImGui.text(f"Collapsed entries: {len(subrows)}")
                for sub in subrows[:10]:
                    PyImGui.text(f"  {sub['display']} ({sub['selected_stats']['avg']:.3f}ms)")
            PyImGui.end_tooltip()

    PyImGui.spacing()
    return clicked_entry


def _draw_usage_groups(rows: list[dict]) -> str | None:
    """Draw aggregated usage rows grouped by normalized display token.

    Returns:
        The clicked entry display token, or `None` when no row was clicked.
    """
    clicked_entry: str | None = None
    total_usage = sum(row["selected_stats"]["avg"] for row in rows)
    flags = int(PyImGui.TableFlags.Borders | PyImGui.TableFlags.RowBg | PyImGui.TableFlags.SizingStretchProp)
    if not PyImGui.begin_table("prof_usage_groups", 5, flags):
        return None

    PyImGui.table_setup_column("Entry", PyImGui.TableColumnFlags.WidthStretch)
    PyImGui.table_setup_column("Total", PyImGui.TableColumnFlags.WidthFixed, 100)
    PyImGui.table_setup_column("% Usage", PyImGui.TableColumnFlags.WidthFixed, 70)
    PyImGui.table_setup_column("Usage Bar", PyImGui.TableColumnFlags.WidthFixed, 140)
    PyImGui.table_setup_column("Members", PyImGui.TableColumnFlags.WidthFixed, 60)
    PyImGui.table_headers_row()

    for row in rows[:_ui_max_rows]:
        pct = (row["selected_stats"]["avg"] / total_usage) if total_usage > 0.0 else 0.0
        PyImGui.table_next_row()
        PyImGui.table_set_column_index(0)
        if PyImGui.selectable(
            f"{row['display']}##usage_row",
            _ui_selected_entry == row["display"],
            PyImGui.SelectableFlags.NoFlag,
            (0.0, 0.0),
        ):
            clicked_entry = row["display"]
        if PyImGui.is_item_hovered() and PyImGui.begin_tooltip():
            PyImGui.text_colored(row["display"], _c4("gold"))
            PyImGui.text(f"Included total avg: {row['selected_stats']['avg']:.3f}ms")
            PyImGui.text(f"Usage share: {pct * 100:.1f}%")
            PyImGui.separator()
            PyImGui.text(f"Subjects: {', '.join(row['subjects'][:6])}")
            PyImGui.text(
                f"Phase avgs: Draw={row['phase_stats']['Draw']['avg']:.3f} | "
                f"Main={row['phase_stats']['Main']['avg']:.3f} | Update={row['phase_stats']['Update']['avg']:.3f}"
            )
            if row["script_paths"]:
                PyImGui.text("Script paths:")
                for sp in row["script_paths"][:6]:
                    PyImGui.text(f"  {sp}")
            PyImGui.separator()
            PyImGui.text("Top members:")
            for item in row["members"][:10]:
                stats = _catalog.get_stats(item.raw_name)
                if stats:
                    PyImGui.text(
                        f"  {item.phase}: avg={stats['avg']:.3f} p50={stats['p50']:.3f} "
                        f"p95={stats['p95']:.3f} p99={stats['p99']:.3f} max={stats['max']:.3f}"
                    )
                PyImGui.text(f"    {item.raw_name}")
            PyImGui.end_tooltip()

        PyImGui.table_set_column_index(1)
        PyImGui.text(f"{row['selected_stats']['avg']:.3f}")
        PyImGui.table_set_column_index(2)
        PyImGui.text(f"{pct * 100:.1f}%")
        PyImGui.table_set_column_index(3)
        PyImGui.push_style_color(PyImGui.ImGuiCol.PlotHistogram, _entry_color4(row["display"]))
        PyImGui.push_style_color(PyImGui.ImGuiCol.FrameBg, _c4("gw_disabled"))
        PyImGui.progress_bar(pct, -1, 0, "")
        PyImGui.pop_style_color(2)
        PyImGui.table_set_column_index(4)
        PyImGui.text(str(len(row["members"])))

    PyImGui.end_table()
    return clicked_entry


def _draw_usage_group_details(rows: list[dict], selected_display: str) -> None:
    """Draw a styled detail card for the selected usage row."""
    row = next((r for r in rows if r["display"] == selected_display), None)
    if row is None:
        return

    if not PyImGui.begin_child("SelectedUsageCard", (0, 0), True):
        return
    accent = _entry_color4(row["display"])
    PyImGui.text_colored("Selected Entry", _c4("light_blue"))
    PyImGui.same_line(0, -1)
    PyImGui.text_colored(row["display"], accent)
    PyImGui.separator()

    PyImGui.text(f"Included Avg Total: {row['selected_stats']['avg']:.3f}ms")
    PyImGui.text(f"Members: {len(row['members'])}")
    PyImGui.text(f"Subjects: {', '.join(row['subjects'][:6])}")

    if row["script_paths"]:
        PyImGui.text("Script Paths:")
        for sp in row["script_paths"]:
            PyImGui.text(f"  {sp}")

    total_avg = max(0.0, float(row["selected_stats"]["avg"]))
    if total_avg > 0.0:
        PyImGui.spacing()
        PyImGui.text_colored("Phase Contribution", _c4("light_blue"))
        for phase_name in ("Draw", "Main", "Update"):
            phase_avg = float(row["phase_stats"][phase_name]["avg"])
            frac = phase_avg / total_avg if total_avg > 0.0 else 0.0
            PyImGui.text_colored(f"{phase_name}", _c4(_phase_color_name(phase_name)))
            PyImGui.same_line(0, -1)
            PyImGui.text(f"{phase_avg:.3f}ms ({frac * 100:.1f}%)")
            PyImGui.push_style_color(PyImGui.ImGuiCol.PlotHistogram, _c4(_phase_color_name(phase_name)))
            PyImGui.push_style_color(PyImGui.ImGuiCol.FrameBg, _c4("gw_disabled"))
            PyImGui.progress_bar(frac, -1, 0, "")
            PyImGui.pop_style_color(2)

    PyImGui.spacing()
    if PyImGui.collapsing_header("Metric History (Top Members)", PyImGui.TreeNodeFlags.DefaultOpen):
        for item in row["members"][: min(6, max(3, _ui_max_rows // 4))]:
            stats = _catalog.get_stats(item.raw_name)
            if not stats:
                continue
            hist = _catalog.get_history(item.raw_name)
            PyImGui.text_colored(f"{item.phase} | {item.raw_name}", _c4(_phase_color_name(item.phase)))
            if hist:
                _draw_sparkline(
                    f"hist##{item.raw_name}",
                    hist,
                    width=0.0,
                    height=48.0,
                    line_col=_entry_color32(row["display"]),
                    fill_col=_c32(_entry_color_name(row["display"]), 0.18),
                )
                PyImGui.text(
                    f"n={len(hist)}  min={min(hist):.3f}  max={max(hist):.3f}  latest={hist[-1]:.3f}"
                )
            else:
                PyImGui.text("No history samples available")
            PyImGui.spacing()

    PyImGui.spacing()
    flags = int(PyImGui.TableFlags.Borders | PyImGui.TableFlags.RowBg | PyImGui.TableFlags.SizingStretchProp)
    if not PyImGui.begin_table(f"usage_group_phase_summary##{selected_display}", 7, flags):
        PyImGui.end_child()
        return

    PyImGui.table_setup_column("Phase", PyImGui.TableColumnFlags.WidthFixed, 70)
    PyImGui.table_setup_column("Min Sum", PyImGui.TableColumnFlags.WidthFixed, 70)
    PyImGui.table_setup_column("Avg Sum", PyImGui.TableColumnFlags.WidthFixed, 70)
    PyImGui.table_setup_column("P50 Sum", PyImGui.TableColumnFlags.WidthFixed, 70)
    PyImGui.table_setup_column("P95 Sum", PyImGui.TableColumnFlags.WidthFixed, 70)
    PyImGui.table_setup_column("P99 Sum", PyImGui.TableColumnFlags.WidthFixed, 70)
    PyImGui.table_setup_column("Max Sum", PyImGui.TableColumnFlags.WidthFixed, 70)
    PyImGui.table_headers_row()

    for phase_name in ("Draw", "Main", "Update"):
        phase_stats = row["phase_stats"][phase_name]
        PyImGui.table_next_row()
        PyImGui.table_set_column_index(0)
        PyImGui.text_colored(phase_name, _c4(_phase_color_name(phase_name)))
        PyImGui.table_set_column_index(1)
        PyImGui.text(f"{phase_stats['min']:.3f}")
        PyImGui.table_set_column_index(2)
        PyImGui.text(f"{phase_stats['avg']:.3f}")
        PyImGui.table_set_column_index(3)
        PyImGui.text(f"{phase_stats['p50']:.3f}")
        PyImGui.table_set_column_index(4)
        PyImGui.text(f"{phase_stats['p95']:.3f}")
        PyImGui.table_set_column_index(5)
        PyImGui.text(f"{phase_stats['p99']:.3f}")
        PyImGui.table_set_column_index(6)
        PyImGui.text(f"{phase_stats['max']:.3f}")

    PyImGui.end_table()
    PyImGui.spacing()

    if PyImGui.collapsing_header(f"Member Metrics ({len(row['members'])})", PyImGui.TreeNodeFlags.DefaultOpen):
        if PyImGui.begin_table(f"usage_group_members##{selected_display}", 9, flags):
            PyImGui.table_setup_column("Phase", PyImGui.TableColumnFlags.WidthFixed, 70)
            PyImGui.table_setup_column("Min", PyImGui.TableColumnFlags.WidthFixed, 70)
            PyImGui.table_setup_column("Avg", PyImGui.TableColumnFlags.WidthFixed, 70)
            PyImGui.table_setup_column("P50", PyImGui.TableColumnFlags.WidthFixed, 70)
            PyImGui.table_setup_column("P95", PyImGui.TableColumnFlags.WidthFixed, 70)
            PyImGui.table_setup_column("P99", PyImGui.TableColumnFlags.WidthFixed, 70)
            PyImGui.table_setup_column("Max", PyImGui.TableColumnFlags.WidthFixed, 70)
            PyImGui.table_setup_column("Operation", PyImGui.TableColumnFlags.WidthFixed, 150)
            PyImGui.table_setup_column("Raw Name", PyImGui.TableColumnFlags.WidthStretch)
            PyImGui.table_headers_row()

            for item in row["members"][:max(15, _ui_max_rows)]:
                stats = _catalog.get_stats(item.raw_name)
                if not stats:
                    continue
                PyImGui.table_next_row()
                PyImGui.table_set_column_index(0)
                PyImGui.text_colored(item.phase, _c4(_phase_color_name(item.phase)))
                PyImGui.table_set_column_index(1)
                PyImGui.text(f"{stats['min']:.3f}")
                PyImGui.table_set_column_index(2)
                PyImGui.text(f"{stats['avg']:.3f}")
                PyImGui.table_set_column_index(3)
                PyImGui.text(f"{stats['p50']:.3f}")
                PyImGui.table_set_column_index(4)
                PyImGui.text(f"{stats['p95']:.3f}")
                PyImGui.table_set_column_index(5)
                PyImGui.text(f"{stats['p99']:.3f}")
                PyImGui.table_set_column_index(6)
                PyImGui.text(f"{stats['max']:.3f}")
                PyImGui.table_set_column_index(7)
                PyImGui.text(item.operation_token)
                PyImGui.table_set_column_index(8)
                PyImGui.text(item.raw_name)
            PyImGui.end_table()
    PyImGui.end_child()


def _draw_sparkline(
    id_str: str,
    values: list[float],
    width: float = 0.0,
    height: float = 42.0,
    line_col: int | None = None,
    fill_col: int | None = None,
) -> None:
    """Draw a simple sparkline/area chart using draw-list primitives."""
    avail_w, _ = PyImGui.get_content_region_avail()
    w = max(120.0, avail_w if width <= 0 else width)
    h = max(16.0, height)
    x, y = PyImGui.get_cursor_screen_pos()
    PyImGui.invisible_button(id_str, w, h)

    draw_bg = _c32("gw_disabled")
    draw_border = _c32("slate_gray")
    draw_line = line_col if line_col is not None else _c32("dodger_blue")
    draw_fill = fill_col if fill_col is not None else _c32("dark_blue", 0.22)

    PyImGui.draw_list_add_rect_filled(x, y, x + w, y + h, draw_bg, 0.0, 0)
    PyImGui.draw_list_add_rect(x, y, x + w, y + h, draw_border, 0.0, 0, 1.0)

    if not values:
        return
    if len(values) == 1:
        yy = y + h * 0.5
        PyImGui.draw_list_add_line(x + 2, yy, x + w - 2, yy, draw_line, 2.0)
        return

    vmin = min(values)
    vmax = max(values)
    vrange = (vmax - vmin) if vmax > vmin else 1.0
    inner_pad = 2.0
    px_prev = x + inner_pad
    py_prev = y + h - inner_pad - (((values[0] - vmin) / vrange) * (h - inner_pad * 2))
    for i in range(1, len(values)):
        t = i / (len(values) - 1)
        px = x + inner_pad + t * (w - inner_pad * 2)
        py = y + h - inner_pad - (((values[i] - vmin) / vrange) * (h - inner_pad * 2))
        PyImGui.draw_list_add_line(px_prev, py_prev, px, py, draw_line, 1.5)
        PyImGui.draw_list_add_line(px, py, px, y + h - inner_pad, draw_fill, 1.0)
        px_prev, py_prev = px, py

    # Time segmentation overlay (seconds) for easier visual grouping.
    total_seconds = (len(values) - 1) * _history_seconds_per_sample
    if total_seconds >= _history_tick_seconds:
        plot_w = max(1.0, w - inner_pad * 2)
        tick_seconds = _history_tick_seconds
        max_ticks = max(2, int(plot_w / 70.0))
        tick_count = int(total_seconds / tick_seconds)
        if tick_count > max_ticks:
            tick_seconds *= int((tick_count + max_ticks - 1) / max_ticks)

        tick_color = _c32("slate_gray", 0.45)
        label_color = _c32("light_gray", 0.70)
        tick_time = 0.0
        while tick_time <= total_seconds + 1e-6:
            ratio = tick_time / total_seconds
            px = x + inner_pad + ratio * plot_w
            PyImGui.draw_list_add_line(px, y + 1.0, px, y + h - 1.0, tick_color, 1.0)
            label = f"{int(round(total_seconds - tick_time))}s"
            text_w, _ = PyImGui.calc_text_size(label)
            tx = max(x + 1.0, min(px - text_w * 0.5, x + w - text_w - 1.0))
            PyImGui.draw_list_add_text(tx, y + h - 12.0, label_color, label)
            tick_time += tick_seconds

    if PyImGui.is_item_hovered() and PyImGui.begin_tooltip():
        PyImGui.text(f"Samples: {len(values)}")
        PyImGui.text(f"Min: {vmin:.3f}ms")
        PyImGui.text(f"Max: {vmax:.3f}ms")
        PyImGui.text(f"Latest: {values[-1]:.3f}ms")
        PyImGui.end_tooltip()


def _draw_selected_entry_window(rows: list[dict]) -> None:
    """Render selected entry details in a separate window to reduce main-view clutter."""
    global _ui_show_selected_window, _ui_selected_entry
    if not _ui_selected_entry:
        return

    PyImGui.set_next_window_size((900, 560), PyImGui.ImGuiCond.FirstUseEver)
    PyImGui.push_style_color(PyImGui.ImGuiCol.WindowBg, _c4("black", 0.92))
    PyImGui.push_style_color(PyImGui.ImGuiCol.ChildBg, _c4("dark_gray", 0.28))
    PyImGui.push_style_color(PyImGui.ImGuiCol.Border, _c4("slate_gray", 0.9))
    PyImGui.push_style_color(PyImGui.ImGuiCol.Header, _c4("dark_blue", 0.75))
    PyImGui.push_style_color(PyImGui.ImGuiCol.HeaderHovered, _c4("dodger_blue", 0.65))
    PyImGui.push_style_color(PyImGui.ImGuiCol.HeaderActive, _c4("dodger_blue", 0.85))
    PyImGui.push_style_color(PyImGui.ImGuiCol.TableHeaderBg, _c4("midnight_violet", 0.55))
    detail_flags = int(PyImGui.WindowFlags.AlwaysAutoResize)
   

    if not PyImGui.begin("Profiler Entry Details", detail_flags):
        PyImGui.pop_style_color(7)
        PyImGui.end()
        return

    _ui_show_selected_window = PyImGui.checkbox("Show details window", _ui_show_selected_window)
    PyImGui.same_line(0, -1)
    if PyImGui.button("Clear Selection"):
        _ui_selected_entry = ""
        PyImGui.pop_style_color(7)
        PyImGui.end()
        return

    PyImGui.spacing()
    _draw_usage_group_details(rows, _ui_selected_entry)
    PyImGui.pop_style_color(7)
    PyImGui.end()


def draw() -> None:
    """Optional UI viewer for the parsed catalog.

    This viewer is intentionally lightweight. The catalog class remains the
    reusable core; this function only visualizes the already-processed data.
    """
    global _ui_filter_text, _ui_show_details, _ui_max_rows, _ui_selected_entry
    global _ui_include_draw, _ui_include_main, _ui_include_update, _ui_show_selected_window

    if PyImGui is None:
        return

    _ensure_loaded()
    _auto_refresh_if_needed()

    PyImGui.set_next_window_size((900, 900), PyImGui.ImGuiCond.FirstUseEver)
    if not PyImGui.begin("Profiler Name Catalog"):
        PyImGui.end()
        return

    if PyImGui.button("Refresh Live Metrics"):
        _catalog.refresh_from_live()
    PyImGui.same_line(0, -1)
    if PyImGui.button("Re-roll Colors"):
        _reroll_entry_palette()
    PyImGui.same_line(0, -1)
    if PyImGui.button("Clear Stats Cache"):
        _catalog.clear_usage_stats()
    PyImGui.same_line(0, -1)
    if PyImGui.button("Print Sample (30)"):
        _catalog.print_sample(30)

    _ui_show_details = PyImGui.checkbox("Verbose tooltips", _ui_show_details)
    PyImGui.same_line(0, -1)
    _ui_show_selected_window = PyImGui.checkbox("Details Window", _ui_show_selected_window)
    _ui_filter_text = PyImGui.input_text("Filter", _ui_filter_text)
    _ui_max_rows = PyImGui.slider_int("Max Rows", _ui_max_rows, 5, 200)
    _ui_include_draw = PyImGui.checkbox("Include Draw", _ui_include_draw)
    PyImGui.same_line(0, -1)
    _ui_include_main = PyImGui.checkbox("Include Main", _ui_include_main)
    PyImGui.same_line(0, -1)
    _ui_include_update = PyImGui.checkbox("Include Update", _ui_include_update)

    counts = _catalog.summary_counts()
    PyImGui.text(
        f"Items={counts['items']} | Phases={counts['phases']} | Subjects={counts['subjects']} | "
        f"ScriptPaths={counts['script_paths']} | Ops={counts['operations']} | Stats={'yes' if _catalog.has_usage_stats() else 'no'}"
    )

    visible = _catalog.filter_text(_ui_filter_text)
    PyImGui.text(f"Filtered rows: {len(visible)}")
    selected_phases = set()
    if _ui_include_draw:
        selected_phases.add("Draw")
    if _ui_include_main:
        selected_phases.add("Main")
    if _ui_include_update:
        selected_phases.add("Update")

    usage_rows = _catalog.build_usage_groups_by_display(visible, include_phases=selected_phases)
    _refresh_entry_color_assignments(usage_rows)
    if PyImGui.button("Log Colors"):
        _log_color_pool_and_assignments(usage_rows)
    PyImGui.text(
        "Grouped by normalized entry (display_token), sorted by included usage total. "
        "Only source avg totals are shown here; percentiles remain in tooltip/details."
    )
    bar_clicked = _draw_top_usage_stacked_bar(usage_rows)
    if bar_clicked is not None and bar_clicked != "__others__":
        _ui_selected_entry = "" if _ui_selected_entry == bar_clicked else bar_clicked
    clicked = _draw_usage_groups(usage_rows)
    if clicked is not None:
        _ui_selected_entry = "" if _ui_selected_entry == clicked else clicked
    if _ui_selected_entry and not any(r["display"] == _ui_selected_entry for r in usage_rows):
        _ui_selected_entry = ""

    PyImGui.end()
    if _ui_show_selected_window and _ui_selected_entry:
        _draw_selected_entry_window(usage_rows)


def update() -> None:
    """Refresh the shared catalog on a throttled interval (non-UI hook)."""
    _ensure_loaded()
    if update_throttle.IsExpired():
        _catalog.refresh_from_live()
        update_throttle.Reset()

if __name__ == "__main__":
    update()
