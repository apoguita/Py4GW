import collections
from typing import Optional

import PyImGui
from Py4GWCoreLib import ProfilingRegistry, SimpleProfiler, WidgetHandler, IconsFontAwesome5, ThrottledTimer

MODULE_NAME = "Widget Profiler"
MODULE_ICON = "Textures/Module_Icons/Widget Profiler.png"
OPTIONAL = True

PHASES = ("minimal", "update", "draw", "main")
WINDOW_SIZES = [60, 120, 300]
PROFILE_DURATION = 120

COLOR_DEFAULT = (1.0, 1.0, 1.0, 1.0)
COLOR_WARN = (1.0, 0.9, 0.3, 1.0)
COLOR_BAD = (1.0, 0.3, 0.3, 1.0)

# Rolling history: "widget_id:phase" -> deque of nanosecond values
history: dict[str, collections.deque] = {}
window_size_index: int = 1
window: int = WINDOW_SIZES[1]

# Profiler state
active_profiles: dict[str, SimpleProfiler] = {}  # wid -> SimpleProfiler
profile_stats: dict[str, dict] = {}  # wid -> {func_key: (cc,nc,tt,ct,callers)}
profile_names: dict[str, dict[tuple, str]] = {}  # wid -> {func_key: display_name}
profile_callees: dict[str, dict[tuple, list]] = {}  # wid -> {key: [(callee_key, edge_ct)]}
profile_roots: dict[str, list[tuple]] = {}  # wid -> [(func_key, ct)] sorted
profile_frames_remaining: dict[str, int] = {}
icicle_zoom: dict[str, Optional[tuple]] = {}  # wid -> zoomed func_key or None
icicle_open: set[str] = set()  # wids with open icicle windows
icicle_sized: set[str] = set()  # wids whose window has been initially sized
icicle_hovered: dict[str, Optional[tuple]] = {}  # wid -> hovered func_key (for highlight)

ICICLE_ROW_H = 22
_PHASE_NAMES = {"draw", "main", "update", "minimal", "on_imgui_render"}
ICICLE_MAX_DEPTH = 8
ICICLE_MIN_PX = 2

_ICICLE_PALETTE = [
    0xFF4B49A0, 0xFF385FA3, 0xFF408585, 0xFF638563,
    0xFF858540, 0xFF856340, 0xFF856385, 0xFF354D8A,
]

# Per-frame computed state shared between update() and draw()
# phase_stats: list of (phase_name, mean, p50, p95, pct)
# row: (wid, name, phase_stats, total_mean, total_p50, total_p95, total_pct)
_rows: list[tuple] = []
_fps: float = 60.0
_total_ms: float = 0.0
_stats_timer: ThrottledTimer = ThrottledTimer(1000)


def on_enable():
    ProfilingRegistry().enabled = True


def on_disable():
    reg = ProfilingRegistry()
    reg.enabled = False
    reg.timings.clear()
    for prof in active_profiles.values():
        try:
            prof.disable()
        except Exception:
            pass
    reg.cprofile_targets.clear()
    history.clear()
    active_profiles.clear()
    profile_stats.clear()
    profile_names.clear()
    profile_callees.clear()
    profile_roots.clear()
    profile_frames_remaining.clear()
    icicle_zoom.clear()
    icicle_open.clear()
    icicle_sized.clear()


def _ms_color(ms: float) -> tuple[float, float, float, float]:
    if ms < 1.0:
        return COLOR_DEFAULT
    if ms <= 5.0:
        return COLOR_WARN
    return COLOR_BAD


def _fmt_ms(ms: float) -> str:
    if ms < 0.01:
        return f"{ms * 1000:.0f}us"
    return f"{ms:.2f}ms"


def _percentile(sorted_vals: list[float], p: float) -> float:
    if not sorted_vals:
        return 0.0
    idx = int(len(sorted_vals) * p)
    idx = min(idx, len(sorted_vals) - 1)
    return sorted_vals[idx]


def _start_profile(wid: str):
    reg = ProfilingRegistry()
    prof = SimpleProfiler()
    active_profiles[wid] = prof
    profile_frames_remaining[wid] = PROFILE_DURATION
    wh = WidgetHandler()
    w = wh.widgets.get(wid)
    for phase in PHASES:
        if w and getattr(w, phase, None) is not None:
            reg.cprofile_targets[f"{wid}:{phase}"] = prof


def _func_display_name(filename: str, funcname: str) -> str:
    if filename == '~':
        return funcname
    base = filename.rsplit('\\', 1)[-1].rsplit('/', 1)[-1]
    if base.endswith('.py'):
        base = base[:-3]
    return f"{base}.{funcname}"


def _finish_profile(wid: str):
    reg = ProfilingRegistry()
    prof = active_profiles.pop(wid, None)
    profile_frames_remaining.pop(wid, None)
    for phase in PHASES:
        reg.cprofile_targets.pop(f"{wid}:{phase}", None)
    if prof is None:
        return

    # Convert SimpleProfiler data to icicle-compatible format
    # all_stats[key] = (nc, nc, self_ns, cum_ns, callers_dict)
    # where callers_dict = {caller_key: (count, cum_ns)}
    raw = prof.stats       # {key: [nc, self_ns, cum_ns]}
    raw_callers = prof.callers  # {key: {caller_key: [count, cum_ns]}}
    all_stats: dict[tuple, tuple] = {}
    for key, (nc, self_ns, cum_ns) in raw.items():
        callers = {ck: tuple(cv) for ck, cv in raw_callers.get(key, {}).items()}
        all_stats[key] = (nc, nc, self_ns, cum_ns, callers)

    # Display names
    func_names: dict[tuple, str] = {}
    for func_key in all_stats:
        func_names[func_key] = _func_display_name(func_key[0], func_key[2])
    profile_stats[wid] = all_stats
    profile_names[wid] = func_names

    # Build callees mapping: parent -> [(callee_key, edge_cum_ns, edge_count)]
    # Sorted by first-seen call order
    callees: dict[tuple, list[tuple]] = {}
    children_set: set[tuple] = set()
    edge_seq = prof.edge_order
    for func_key, (cc, nc, tt, ct, callers) in all_stats.items():
        for caller_key, (edge_count, edge_cum) in callers.items():
            callees.setdefault(caller_key, []).append((func_key, edge_cum, edge_count))
            children_set.add(func_key)
    for key in callees:
        callees[key].sort(key=lambda c: edge_seq.get((key, c[0]), 0))
    profile_callees[wid] = callees

    # Root detection
    _INFRA_BASES = {'Profiling.py', 'WidgetManager.py', 'traceback.py',
                    'Widget Profiler.py'}
    w = WidgetHandler().widgets.get(wid)
    widget_script = w.script_path.replace("/", "\\") if w else ""
    seen_roots: set[tuple] = set()
    widget_roots = []

    def _is_infra(k: tuple) -> bool:
        if k[0] in ('~', '<string>'):
            return True
        base = k[0].rsplit('\\', 1)[-1].rsplit('/', 1)[-1]
        return base in _INFRA_BASES

    # 1) Widget's own functions: promote from infra/ghost parents
    infra_parents = set(callees.keys()) - set(all_stats.keys())
    for k in all_stats:
        if _is_infra(k) and k in callees:
            infra_parents.add(k)
    for parent_key in infra_parents:
        for callee_key, _edge_ct, _edge_n in callees[parent_key]:
            if callee_key in seen_roots or _is_infra(callee_key):
                continue
            if callee_key[0].replace("/", "\\") == widget_script:
                widget_roots.append((callee_key, all_stats[callee_key][3]))
                seen_roots.add(callee_key)

    # 2) Orphaned non-infra functions
    for k in all_stats:
        if k in children_set or k in seen_roots or _is_infra(k):
            continue
        widget_roots.append((k, all_stats[k][3]))
        seen_roots.add(k)

    widget_roots.sort(key=lambda r: r[1], reverse=True)
    profile_roots[wid] = widget_roots

    icicle_zoom[wid] = None
    icicle_open.add(wid)


def update():
    global _rows, _fps, _total_ms

    reg = ProfilingRegistry()
    wh = WidgetHandler()

    widget_timings = reg.timings.get("widgets", {})

    # Append to rolling history (cheap, every frame)
    for key, ns in widget_timings.items():
        if key not in history:
            history[key] = collections.deque(maxlen=window)
        history[key].append(ns)

    # Manage profiler countdowns
    finished = [wid for wid, r in profile_frames_remaining.items() if r <= 1]
    for wid in profile_frames_remaining:
        profile_frames_remaining[wid] -= 1
    for wid in finished:
        _finish_profile(wid)

    # Only recompute stats on a throttled timer
    if not _stats_timer.IsExpired() and _rows:
        return
    _stats_timer.Reset()

    io = PyImGui.get_io()
    _fps = io.framerate if io.framerate > 0 else 60.0
    _total_ms = sum(widget_timings.values()) / 1_000_000

    frame_time_ms = 1000.0 / _fps

    # Group by widget_id
    per_widget: dict[str, dict[str, int]] = {}
    for key, ns in widget_timings.items():
        sep = key.rfind(":")
        if sep < 0:
            continue
        per_widget.setdefault(key[:sep], {})[key[sep + 1:]] = ns

    # Build hierarchical rows
    rows = []
    for wid in per_widget:
        w = wh.widgets.get(wid)
        if w is None or not w.enabled:
            continue
        phase_stats = []
        phase_deqs: list[tuple[str, collections.deque]] = []
        for phase in PHASES:
            deq = history.get(f"{wid}:{phase}")
            if deq and len(deq) > 0:
                phase_deqs.append((phase, deq))

        if not phase_deqs:
            continue

        # Per-phase stats using sorted list
        for phase, deq in phase_deqs:
            vals = sorted(deq)
            n = len(vals)
            mean = sum(vals) / n / 1_000_000
            p50 = vals[n // 2] / 1_000_000
            p95 = vals[min(int(n * 0.95), n - 1)] / 1_000_000
            pct = (mean / frame_time_ms * 100) if frame_time_ms > 0 else 0
            phase_stats.append((phase, mean, p50, p95, pct))

        # Widget-level: sum phases per frame
        min_len = min(len(deq) for _, deq in phase_deqs)
        if min_len > 0:
            totals = sorted(
                sum(deq[i] for _, deq in phase_deqs)
                for i in range(min_len)
            )
            n = len(totals)
            total_mean = sum(totals) / n / 1_000_000
            total_p50 = totals[n // 2] / 1_000_000
            total_p95 = totals[min(int(n * 0.95), n - 1)] / 1_000_000
        else:
            total_mean = sum(s[1] for s in phase_stats)
            total_p50 = sum(s[2] for s in phase_stats)
            total_p95 = sum(s[3] for s in phase_stats)

        total_pct = (total_mean / frame_time_ms * 100) if frame_time_ms > 0 else 0
        rows.append((wid, w.plain_name, phase_stats,
                      total_mean, total_p50, total_p95, total_pct))

    rows.sort(key=lambda r: r[3], reverse=True)
    _rows = rows


def draw():
    global window_size_index, window

    wh = WidgetHandler()

    if not PyImGui.begin(MODULE_NAME, PyImGui.WindowFlags.AlwaysAutoResize):
        PyImGui.end()
        return

    # Header
    frame_ms = 1000.0 / _fps if _fps > 0 else 16.67

    fps_color = COLOR_DEFAULT if _fps >= 55 else COLOR_WARN if _fps >= 30 else COLOR_BAD

    # Render combo first to establish line height, then overlay text via same_line
    PyImGui.set_next_item_width(60)
    new_idx = PyImGui.combo("##Samples", window_size_index, [str(s) for s in WINDOW_SIZES])
    if new_idx != window_size_index:
        window_size_index = new_idx
        window = WINDOW_SIZES[new_idx]
        for k in history:
            history[k] = collections.deque(history[k], maxlen=window)
    PyImGui.same_line(0, 4)
    PyImGui.text("samples")
    PyImGui.same_line(0, 20)

    PyImGui.push_style_color(PyImGui.ImGuiCol.Text, _ms_color(_total_ms))
    PyImGui.text(f"{_total_ms:.1f}ms")
    PyImGui.pop_style_color(1)
    PyImGui.same_line(0, 4)
    PyImGui.text(f"/ {frame_ms:.1f}ms")
    PyImGui.same_line(0, 20)

    PyImGui.push_style_color(PyImGui.ImGuiCol.Text, fps_color)
    PyImGui.text(f"{_fps:.0f}")
    PyImGui.pop_style_color(1)
    PyImGui.same_line(0, 4)
    PyImGui.text("FPS")

    PyImGui.spacing()

    # Main table: Name | Mean | P50 | P95 | % Frame | Prof
    col_count = 6
    table_flags = (
        PyImGui.TableFlags.Borders
        | PyImGui.TableFlags.RowBg
        | PyImGui.TableFlags.SizingStretchProp
        | PyImGui.TableFlags.ScrollY
    )

    if PyImGui.begin_table("##ProfilerTable", col_count, table_flags, 0, 300):
        PyImGui.table_setup_column("Name", PyImGui.TableColumnFlags.WidthFixed, 180)
        PyImGui.table_setup_column("Mean", PyImGui.TableColumnFlags.WidthFixed, 65)
        PyImGui.table_setup_column("P50", PyImGui.TableColumnFlags.WidthFixed, 65)
        PyImGui.table_setup_column("P95", PyImGui.TableColumnFlags.WidthFixed, 65)
        PyImGui.table_setup_column("% Frame", PyImGui.TableColumnFlags.WidthFixed, 100)
        PyImGui.table_setup_column("##prof", PyImGui.TableColumnFlags.WidthFixed, 45)
        PyImGui.table_headers_row()

        for wid, display_name, phase_stats, total_mean, total_p50, total_p95, total_pct in _rows:
            PyImGui.table_next_row()

            # Col 0: tree node for widget
            PyImGui.table_set_column_index(0)
            tree_open = PyImGui.tree_node_ex(
                f"{display_name}##{wid}",
                PyImGui.TreeNodeFlags.SpanFullWidth
            )
            if PyImGui.is_item_hovered():
                PyImGui.show_tooltip(wid)

            # Col 1: Mean
            PyImGui.table_set_column_index(1)
            PyImGui.text_colored(_fmt_ms(total_mean), _ms_color(total_mean))

            # Col 2: P50
            PyImGui.table_set_column_index(2)
            PyImGui.text_colored(_fmt_ms(total_p50), _ms_color(total_p50))

            # Col 3: P95
            PyImGui.table_set_column_index(3)
            PyImGui.text_colored(_fmt_ms(total_p95), _ms_color(total_p95))

            # Col 4: % Frame
            PyImGui.table_set_column_index(4)
            bar_frac = min(total_pct / 100.0, 1.0)
            PyImGui.progress_bar(bar_frac, -1, f"{total_pct:.1f}%")

            # Col 5: Profile button (skip for self)
            PyImGui.table_set_column_index(5)
            if 'Widget Profiler' not in wid:
                if wid in active_profiles:
                    remaining = profile_frames_remaining.get(wid, 0)
                    PyImGui.text_disabled(f"{remaining}")
                else:
                    if PyImGui.button(f"{IconsFontAwesome5.ICON_SEARCH}##{wid}", 0, 0):
                        _start_profile(wid)

            # Phase child rows
            if tree_open:
                for phase, mean, p50, p95, pct in phase_stats:
                    PyImGui.table_next_row()

                    PyImGui.table_set_column_index(0)
                    PyImGui.tree_node_ex(
                        f"{phase}##{wid}_{phase}",
                        PyImGui.TreeNodeFlags.Leaf
                        | PyImGui.TreeNodeFlags.NoTreePushOnOpen
                        | PyImGui.TreeNodeFlags.SpanFullWidth
                    )

                    PyImGui.table_set_column_index(1)
                    PyImGui.text_colored(_fmt_ms(mean), _ms_color(mean))

                    PyImGui.table_set_column_index(2)
                    PyImGui.text_colored(_fmt_ms(p50), _ms_color(p50))

                    PyImGui.table_set_column_index(3)
                    PyImGui.text_colored(_fmt_ms(p95), _ms_color(p95))

                    PyImGui.table_set_column_index(4)
                    child_frac = min(pct / 100.0, 1.0)
                    PyImGui.progress_bar(child_frac, -1, f"{pct:.1f}%")

                PyImGui.tree_pop()

        PyImGui.end_table()

    PyImGui.end()

    # Profiler icicle popup windows (separate resizable windows)
    for wid in list(icicle_open):
        if wid not in profile_roots:
            icicle_open.discard(wid)
            continue
        w = wh.widgets.get(wid)
        name = w.plain_name if w else wid

        if wid not in icicle_sized:
            PyImGui.set_next_window_size(600, 300)
            icicle_sized.add(wid)
        showing = PyImGui.begin(f"Profile: {name}##icicle_{wid}", 0)
        if not showing:
            PyImGui.end()
            continue

        if PyImGui.small_button(f"Close##close_{wid}"):
            for d in (profile_stats, profile_names, profile_callees, profile_roots, icicle_zoom):
                d.pop(wid, None)
            icicle_open.discard(wid)
            PyImGui.end()
            continue
        if icicle_zoom.get(wid) is not None:
            PyImGui.same_line(0, 10)
            if PyImGui.small_button(f"Zoom Out##zout_{wid}"):
                icicle_zoom[wid] = None
        PyImGui.same_line(0, 10)
        if PyImGui.small_button(f"Re-profile##reprof_{wid}"):
            for d in (profile_stats, profile_names, profile_callees, profile_roots, icicle_zoom):
                d.pop(wid, None)
            icicle_open.discard(wid)
            _start_profile(wid)
            PyImGui.end()
            continue

        _draw_icicle(wid)
        PyImGui.end()


def _icicle_color_idx(func_key: tuple, parent_idx: int, prev_sibling_idx: int) -> int:
    """Palette index for func_key, shifted to avoid parent and previous sibling."""
    n = len(_ICICLE_PALETTE)
    idx = hash(func_key) % n
    avoid = {parent_idx, prev_sibling_idx}
    while idx in avoid:
        idx = (idx + 1) % n
    return idx


def _icicle_color(idx: int, highlight: bool = False) -> int:
    base = _ICICLE_PALETTE[idx]
    r = base & 0xFF
    g = (base >> 8) & 0xFF
    b = (base >> 16) & 0xFF
    if highlight:
        r = min(255, r + 80)
        g = min(255, g + 80)
        b = min(255, b + 80)
    return (0xFF << 24) | (b << 16) | (g << 8) | r


def _draw_icicle(wid: str):
    raw = profile_stats.get(wid, {})
    names = profile_names.get(wid, {})
    callees = profile_callees.get(wid, {})
    roots = profile_roots.get(wid, [])
    frames = PROFILE_DURATION
    prev_hovered = icicle_hovered.get(wid)

    avail_w = PyImGui.get_content_region_avail()[0]
    if avail_w < 50:
        return

    zoom_key = icicle_zoom.get(wid)
    if zoom_key is not None and zoom_key in raw:
        top_level = [(zoom_key, raw[zoom_key][3])]
    else:
        top_level = roots

    total_ct = sum(ct for _, ct in top_level) or 1.0

    sx, sy = PyImGui.get_cursor_screen_pos()

    # BFS: each level is [(func_key, x_px, width_px, allotted_ct, edge_calls, parent_cidx, prev_sib_cidx)]
    current_level: list[tuple] = []
    x = sx
    prev_sib = -1
    for key, ct in top_level:
        w_px = (ct / total_ct) * avail_w
        if w_px < ICICLE_MIN_PX:
            continue
        nc_root = raw[key][1] if key in raw else 0
        current_level.append((key, x, w_px, ct, nc_root, -1, prev_sib))
        prev_sib = _icicle_color_idx(key, -1, prev_sib)
        x += w_px

    rendered_depth = 0
    clicked_key: Optional[tuple] = None
    new_hovered: Optional[tuple] = None
    io = PyImGui.get_io()
    mx, my = io.mouse_pos_x, io.mouse_pos_y

    for depth in range(ICICLE_MAX_DEPTH):
        if not current_level:
            break
        rendered_depth = depth + 1
        y = sy + depth * ICICLE_ROW_H
        next_level: list[tuple] = []

        for func_key, fx, fw, allotted_ct, edge_calls, parent_cidx, prev_sib_cidx in current_level:
            entry = raw.get(func_key)
            if entry is None:
                continue
            cc, nc, tt, ct, callers_dict = entry

            # Draw filled rect (highlight if same function as hovered)
            is_hl = prev_hovered is not None and func_key == prev_hovered
            cidx = _icicle_color_idx(func_key, parent_cidx, prev_sib_cidx)
            color = _icicle_color(cidx, highlight=is_hl)
            PyImGui.draw_list_add_rect_filled(fx, y, fx + fw, y + ICICLE_ROW_H - 1, color, 0, 0)
            if is_hl:
                PyImGui.draw_list_add_rect(fx, y, fx + fw, y + ICICLE_ROW_H - 1, 0xFFFFFFFF, 0, 0, 1.0)

            # Text label if wide enough
            display = names.get(func_key, "?")
            self_ms = tt / frames / 1_000_000
            char_w = 6.5
            max_chars = int(fw / char_w)
            if max_chars > 3:
                label = display[:max_chars]
                PyImGui.draw_list_add_text(fx + 3, y + 4, 0xFF000000, label)
                PyImGui.draw_list_add_text(fx + 2, y + 3, 0xFFFFFFFF, label)

            # Hover detection
            if fx <= mx <= fx + fw and y <= my <= y + ICICLE_ROW_H:
                new_hovered = func_key
                cum_ms = ct / frames / 1_000_000
                calls_per_f = edge_calls / frames
                tip = display
                tip += f"\nSelf: {_fmt_ms(self_ms)}  |  Cum: {_fmt_ms(cum_ms)}"
                tip += f"\n{calls_per_f:.1f} calls/frame"
                if nc != edge_calls:
                    tip += f"  ({nc / frames:.1f} from all callers)"
                PyImGui.set_tooltip(tip)
                if PyImGui.is_mouse_clicked(0):
                    clicked_key = func_key

            # Build children for next level
            # Use parent's actual cumulative time (not allotted edge) to size children,
            # since edge times are global totals not split by call path.
            if func_key in callees:
                parent_ct = ct  # actual cumulative from stats
                child_x = fx
                remaining = fw
                child_prev_sib = -1
                for callee_key, edge_ct, edge_n in callees[func_key]:
                    child_w = (edge_ct / parent_ct) * fw if parent_ct > 0 else 0
                    child_w = min(child_w, remaining)
                    if child_w < ICICLE_MIN_PX:
                        continue
                    next_level.append((callee_key, child_x, child_w, edge_ct, edge_n, cidx, child_prev_sib))
                    child_prev_sib = _icicle_color_idx(callee_key, cidx, child_prev_sib)
                    child_x += child_w
                    remaining -= child_w

        current_level = next_level

    # Reserve space
    total_h = max(rendered_depth, 1) * ICICLE_ROW_H + 4
    PyImGui.dummy(int(avail_w), int(total_h))

    # Update state
    icicle_hovered[wid] = new_hovered
    if clicked_key is not None:
        icicle_zoom[wid] = clicked_key
