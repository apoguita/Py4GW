import PyImGui
from Py4GWCoreLib import ThrottledTimer
import Py4GW

initialized = False
update_timer = ThrottledTimer(1000)
metric_names = []
metrics_dict = {}
metric_records = []

ui_min_avg_threshold_ms = 0.0
ui_show_progress_bars = True
ui_view_mode = 0  # 0=Hierarchy, 1=Leaf Pivot, 2=Treemap
ui_group_dim_1 = 0
ui_group_dim_2 = 2
ui_group_dim_3 = 1
ui_row_label_dim = 6
ui_pivot_sort_mode = 0
ui_hide_totals = False
ui_treemap_max_depth = 3

ui_filter_exec_idx = 0
ui_filter_phase_idx = 0
ui_filter_section1_idx = 0
ui_filter_section2_idx = 0
ui_filter_segment_idx = 0

filter_exec_options = ["All"]
filter_phase_options = ["All"]
filter_section1_options = ["All"]
filter_section2_options = ["All"]
filter_segment_options = ["All"]

VIEW_MODES = ["Hierarchy", "Leaf Pivot", "Treemap"]
GROUP_DIMS = ["exec_bucket", "phase", "script", "section1", "section2", "section3", "leaf", "suffix"]
GROUP_DIM_LABELS = ["Exec Bucket", "Phase", "Script", "Section 1", "Section 2", "Section 3", "Leaf", "Suffix"]
PIVOT_SORT_MODES = ["FrameLoop Total", "Update", "Combined Total", "Draw", "Main"]

FRAME_BUCKET = "FrameLoop (Draw+Main)"
UPDATE_BUCKET = "UpdateLoop"
OTHER_BUCKET = "Other"

TABLE_FLAGS = int(PyImGui.TableFlags.Borders | PyImGui.TableFlags.RowBg | PyImGui.TableFlags.SizingStretchProp)


def _pack_rgba(r, g, b, a=255):
    return ((a & 255) << 24) | ((b & 255) << 16) | ((g & 255) << 8) | (r & 255)


def _new_tree_node():
    return {"children": {}, "rows": [], "sum_avg": 0.0, "count": 0, "bucket_sums": {}}


def _split_metric_name(name):
    tokens = name.split(".")
    path_idx = -1
    for i, token in enumerate(tokens):
        if "/" in token or "\\" in token:
            path_idx = i
            break

    if path_idx != -1:
        prefix_tokens = [t for t in tokens[:path_idx] if t]
        leaf = ".".join(tokens[path_idx:]).strip() or name
        script = leaf
    elif len(tokens) > 1:
        prefix_tokens = [t for t in tokens[:-1] if t]
        leaf = tokens[-1].strip() or name
        script = prefix_tokens[-1] if prefix_tokens else leaf
    else:
        prefix_tokens = []
        leaf = name
        script = name

    phase = prefix_tokens[0] if prefix_tokens else (tokens[0] if tokens else "")
    after_phase = prefix_tokens[1:] if len(prefix_tokens) > 1 else []
    suffix_tokens = tokens[1:] if len(tokens) > 1 else []
    suffix = ".".join(suffix_tokens).strip() if suffix_tokens else name

    # Tokenize by all separators for data-driven filters.
    unified = name.replace("\\", "/").replace(".", "/")
    path_segments = [seg.strip() for seg in unified.split("/") if seg.strip()]

    section1 = after_phase[0] if len(after_phase) > 0 else "(none)"
    section2 = after_phase[1] if len(after_phase) > 1 else "(none)"
    section3 = after_phase[2] if len(after_phase) > 2 else "(none)"

    if phase in ("Draw", "Main"):
        exec_bucket = FRAME_BUCKET
    elif phase == "Update":
        exec_bucket = UPDATE_BUCKET
    else:
        exec_bucket = OTHER_BUCKET

    return {
        "phase": phase or "(none)",
        "exec_bucket": exec_bucket,
        "section1": section1,
        "section2": section2,
        "section3": section3,
        "script": script,
        "leaf": leaf,
        "suffix": suffix,
        "path_segments": path_segments,
    }


def _build_metric_records(names, metrics):
    records = []
    for name in names:
        data = metrics.get(name)
        if data is None:
            continue
        parsed = _split_metric_name(name)
        avg = data["avg"]
        records.append(
            {
                "name": name,
                "data": data,
                "avg": avg,
                "phase": parsed["phase"],
                "exec_bucket": parsed["exec_bucket"],
                "section1": parsed["section1"],
                "section2": parsed["section2"],
                "section3": parsed["section3"],
                "script": parsed["script"],
                "leaf": parsed["leaf"],
                "suffix": parsed["suffix"],
                "path_segments": parsed["path_segments"],
                "is_total": (parsed["leaf"] == "Total") or name.endswith(".Total"),
            }
        )
    records.sort(key=lambda r: r["avg"], reverse=True)
    return records


def _build_filter_options(records):
    global filter_exec_options
    global filter_phase_options
    global filter_section1_options
    global filter_section2_options
    global filter_segment_options

    exec_vals = sorted({r["exec_bucket"] for r in records})
    phase_vals = sorted({r["phase"] for r in records})
    sec1_vals = sorted({r["section1"] for r in records})
    sec2_vals = sorted({r["section2"] for r in records})

    seg_counts = {}
    for r in records:
        for seg in r["path_segments"]:
            seg_counts[seg] = seg_counts.get(seg, 0) + 1
    top_segments = sorted(seg_counts.items(), key=lambda kv: (-kv[1], kv[0]))[:80]

    filter_exec_options = ["All"] + exec_vals
    filter_phase_options = ["All"] + phase_vals
    filter_section1_options = ["All"] + sec1_vals
    filter_section2_options = ["All"] + sec2_vals
    filter_segment_options = ["All"] + [seg for seg, _count in top_segments]


def _sum_buckets(records):
    sums = {FRAME_BUCKET: 0.0, UPDATE_BUCKET: 0.0, OTHER_BUCKET: 0.0}
    total = 0.0
    for rec in records:
        sums[rec["exec_bucket"]] = sums.get(rec["exec_bucket"], 0.0) + rec["avg"]
        total += rec["avg"]
    return sums, total


def _safe_share(value, denom):
    return (value / denom) if denom > 0.0 else 0.0


def _record_share(rec, bucket_sums, visible_total):
    bucket = rec["exec_bucket"]
    if bucket == FRAME_BUCKET:
        return _safe_share(rec["avg"], bucket_sums.get(FRAME_BUCKET, 0.0))
    if bucket == UPDATE_BUCKET:
        return _safe_share(rec["avg"], bucket_sums.get(UPDATE_BUCKET, 0.0))
    return _safe_share(rec["avg"], visible_total)


def _node_share(node, bucket_sums, visible_total):
    shares = []
    for bucket in (FRAME_BUCKET, UPDATE_BUCKET, OTHER_BUCKET):
        val = node["bucket_sums"].get(bucket, 0.0)
        if val <= 0.0:
            continue
        denom = bucket_sums.get(bucket, 0.0) if bucket != OTHER_BUCKET else visible_total
        shares.append((bucket, val, _safe_share(val, denom)))
    return shares


def _distinct_dims(dims):
    seen = set()
    out = []
    for dim in dims:
        if dim not in seen:
            seen.add(dim)
            out.append(dim)
    return out


def _build_dynamic_tree(records, group_dims, row_label_dim):
    root = _new_tree_node()

    for rec in records:
        node = root
        node["sum_avg"] += rec["avg"]
        node["count"] += 1
        node["bucket_sums"][rec["exec_bucket"]] = node["bucket_sums"].get(rec["exec_bucket"], 0.0) + rec["avg"]

        for dim in group_dims:
            value = rec.get(dim, "(none)") or "(none)"
            children = node["children"]
            if value not in children:
                children[value] = _new_tree_node()
            node = children[value]
            node["sum_avg"] += rec["avg"]
            node["count"] += 1
            node["bucket_sums"][rec["exec_bucket"]] = node["bucket_sums"].get(rec["exec_bucket"], 0.0) + rec["avg"]

        row_label = rec.get(row_label_dim, rec["leaf"]) or rec["leaf"]
        node["rows"].append((row_label, rec))

    stack = [root]
    while stack:
        node = stack.pop()
        node["rows"].sort(key=lambda item: item[1]["avg"], reverse=True)
        if node["children"]:
            ordered = sorted(node["children"].items(), key=lambda kv: kv[1]["sum_avg"], reverse=True)
            node["children"] = dict(ordered)
            stack.extend(node["children"].values())

    return root


def _draw_budget_summary(visible_records):
    bucket_sums, visible_total = _sum_buckets(visible_records)
    frame_sum = bucket_sums.get(FRAME_BUCKET, 0.0)
    update_sum = bucket_sums.get(UPDATE_BUCKET, 0.0)
    other_sum = bucket_sums.get(OTHER_BUCKET, 0.0)

    PyImGui.text_disabled(
        f"Visible {len(visible_records)}/{len(metric_records)} | FrameLoop={frame_sum:.2f}ms (Draw+Main) | UpdateLoop={update_sum:.2f}ms | Other={other_sum:.2f}ms"
    )

    if ui_show_progress_bars:
        if frame_sum > 0.0:
            PyImGui.text("FrameLoop budget (Draw + Main)")
            PyImGui.progress_bar(_safe_share(frame_sum, visible_total), -1, 0, f"{frame_sum:.2f}ms")
        if update_sum > 0.0:
            PyImGui.text("UpdateLoop budget")
            PyImGui.progress_bar(_safe_share(update_sum, visible_total), -1, 0, f"{update_sum:.2f}ms")
    return bucket_sums, visible_total


def _draw_metric_rows_table(rows, table_id, bucket_sums, visible_total):
    if not rows:
        return
    if not PyImGui.begin_table(table_id, 10, TABLE_FLAGS):
        return

    PyImGui.table_setup_column("Label", PyImGui.TableColumnFlags.WidthStretch)
    PyImGui.table_setup_column("Phase", PyImGui.TableColumnFlags.WidthFixed, 50)
    PyImGui.table_setup_column("Bucket%", PyImGui.TableColumnFlags.WidthFixed, 60)
    PyImGui.table_setup_column("Usage", PyImGui.TableColumnFlags.WidthFixed, 120)
    PyImGui.table_setup_column("Min", PyImGui.TableColumnFlags.WidthFixed, 55)
    PyImGui.table_setup_column("Avg", PyImGui.TableColumnFlags.WidthFixed, 55)
    PyImGui.table_setup_column("P50", PyImGui.TableColumnFlags.WidthFixed, 55)
    PyImGui.table_setup_column("P95", PyImGui.TableColumnFlags.WidthFixed, 55)
    PyImGui.table_setup_column("P99", PyImGui.TableColumnFlags.WidthFixed, 55)
    PyImGui.table_setup_column("Max", PyImGui.TableColumnFlags.WidthFixed, 55)
    PyImGui.table_headers_row()

    for label, rec in rows:
        share = _record_share(rec, bucket_sums, visible_total)
        d = rec["data"]

        PyImGui.table_next_row()
        PyImGui.table_set_column_index(0)
        PyImGui.text(label)
        if PyImGui.is_item_hovered() and PyImGui.begin_tooltip():
            PyImGui.text(rec["name"])
            PyImGui.text(f"Bucket: {rec['exec_bucket']}")
            PyImGui.text(f"Phase: {rec['phase']}")
            PyImGui.end_tooltip()

        PyImGui.table_set_column_index(1)
        PyImGui.text(rec["phase"])
        PyImGui.table_set_column_index(2)
        PyImGui.text(f"{share * 100:.1f}%")
        PyImGui.table_set_column_index(3)
        if ui_show_progress_bars:
            PyImGui.progress_bar(share, -1, 0, "")
        else:
            PyImGui.text_disabled("-")

        vals = (d["min"], d["avg"], d["p50"], d["p95"], d["p99"], d["max"])
        for col, val in enumerate(vals, start=4):
            PyImGui.table_set_column_index(col)
            PyImGui.text(f"{val:.2f}")

    PyImGui.end_table()


def _draw_tree_node(node, label, path, depth, bucket_sums, visible_total):
    if node["count"] <= 0:
        return

    if depth > 0:
        header = f"{label} ({node['count']})##{path}"
        flags = PyImGui.TreeNodeFlags.DefaultOpen if depth <= 2 else PyImGui.TreeNodeFlags.NoFlag
        if not PyImGui.collapsing_header(header, flags):
            return

    if depth > 0:
        PyImGui.indent(16.0)

    PyImGui.text_disabled(f"sum avg {node['sum_avg']:.2f}ms")
    for bucket_label, bucket_sum, bucket_share in _node_share(node, bucket_sums, visible_total):
        PyImGui.text(f"{bucket_label}: {bucket_sum:.2f}ms ({bucket_share * 100:.1f}%)")
        if ui_show_progress_bars:
            PyImGui.progress_bar(bucket_share, -1, 0, "")

    if node["rows"]:
        _draw_metric_rows_table(node["rows"], f"rows##{path}", bucket_sums, visible_total)

    for child_name, child in node["children"].items():
        _draw_tree_node(child, child_name, f"{path}.{child_name}", depth + 1, bucket_sums, visible_total)

    if depth > 0:
        PyImGui.unindent(16.0)


def _build_pivot_rows(records):
    pivot = {}
    for rec in records:
        key = rec["script"]
        row = pivot.get(key)
        if row is None:
            row = {"key": key, "draw": 0.0, "main": 0.0, "update": 0.0, "other": 0.0}
            pivot[key] = row

        if rec["phase"] == "Draw":
            row["draw"] += rec["avg"]
        elif rec["phase"] == "Main":
            row["main"] += rec["avg"]
        elif rec["phase"] == "Update":
            row["update"] += rec["avg"]
        else:
            row["other"] += rec["avg"]

    rows = list(pivot.values())
    for row in rows:
        row["frame_total"] = row["draw"] + row["main"]
        row["combined_total"] = row["frame_total"] + row["update"] + row["other"]
    return rows


def _pivot_sort_value(row):
    if ui_pivot_sort_mode == 0:
        return row["frame_total"]
    if ui_pivot_sort_mode == 1:
        return row["update"]
    if ui_pivot_sort_mode == 2:
        return row["combined_total"]
    if ui_pivot_sort_mode == 3:
        return row["draw"]
    return row["main"]


def _draw_pivot_table(records, bucket_sums, visible_total):
    rows = _build_pivot_rows(records)
    rows = [r for r in rows if r["combined_total"] >= ui_min_avg_threshold_ms]
    rows.sort(key=_pivot_sort_value, reverse=True)
    if not rows:
        PyImGui.text("No pivot rows match current filters")
        return

    frame_total = bucket_sums.get(FRAME_BUCKET, 0.0)
    update_total = bucket_sums.get(UPDATE_BUCKET, 0.0)

    if not PyImGui.begin_table("pivot_table", 9, TABLE_FLAGS):
        return
    PyImGui.table_setup_column("Script", PyImGui.TableColumnFlags.WidthStretch)
    PyImGui.table_setup_column("Draw", PyImGui.TableColumnFlags.WidthFixed, 60)
    PyImGui.table_setup_column("Main", PyImGui.TableColumnFlags.WidthFixed, 60)
    PyImGui.table_setup_column("Frame", PyImGui.TableColumnFlags.WidthFixed, 60)
    PyImGui.table_setup_column("Frame%", PyImGui.TableColumnFlags.WidthFixed, 60)
    PyImGui.table_setup_column("Update", PyImGui.TableColumnFlags.WidthFixed, 60)
    PyImGui.table_setup_column("Upd%", PyImGui.TableColumnFlags.WidthFixed, 60)
    PyImGui.table_setup_column("Total", PyImGui.TableColumnFlags.WidthFixed, 60)
    PyImGui.table_setup_column("Usage", PyImGui.TableColumnFlags.WidthFixed, 120)
    PyImGui.table_headers_row()

    for row in rows:
        frame_share = _safe_share(row["frame_total"], frame_total)
        update_share = _safe_share(row["update"], update_total)
        total_share = _safe_share(row["combined_total"], visible_total)

        PyImGui.table_next_row()
        PyImGui.table_set_column_index(0)
        PyImGui.text(row["key"])
        PyImGui.table_set_column_index(1)
        PyImGui.text(f"{row['draw']:.2f}")
        PyImGui.table_set_column_index(2)
        PyImGui.text(f"{row['main']:.2f}")
        PyImGui.table_set_column_index(3)
        PyImGui.text(f"{row['frame_total']:.2f}")
        PyImGui.table_set_column_index(4)
        PyImGui.text(f"{frame_share * 100:.1f}%")
        PyImGui.table_set_column_index(5)
        PyImGui.text(f"{row['update']:.2f}")
        PyImGui.table_set_column_index(6)
        PyImGui.text(f"{update_share * 100:.1f}%")
        PyImGui.table_set_column_index(7)
        PyImGui.text(f"{row['combined_total']:.2f}")
        PyImGui.table_set_column_index(8)
        if ui_show_progress_bars:
            PyImGui.progress_bar(total_share, -1, 0, "")
        else:
            PyImGui.text_disabled("-")

    PyImGui.end_table()


def _dominant_bucket_for_node(node):
    bucket_sums = node.get("bucket_sums", {})
    if not bucket_sums:
        return OTHER_BUCKET
    best_bucket = OTHER_BUCKET
    best_val = -1.0
    for bucket in (FRAME_BUCKET, UPDATE_BUCKET, OTHER_BUCKET):
        val = bucket_sums.get(bucket, 0.0)
        if val > best_val:
            best_val = val
            best_bucket = bucket
    return best_bucket


def _treemap_color(bucket, depth):
    if bucket == FRAME_BUCKET:
        base = (70, 130, 210)
    elif bucket == UPDATE_BUCKET:
        base = (210, 120, 55)
    else:
        base = (120, 120, 120)
    # depth tint
    dr = min(base[0] + depth * 10, 245)
    dg = min(base[1] + depth * 7, 245)
    db = min(base[2] + depth * 6, 245)
    return _pack_rgba(dr, dg, db, 235)


def _phase_color(phase, depth, alpha=235):
    if phase == "Draw":
        base = (70, 140, 235)
    elif phase == "Main":
        base = (85, 190, 130)
    elif phase == "Update":
        base = (230, 135, 55)
    else:
        base = (140, 140, 140)
    dr = min(base[0] + depth * 8, 245)
    dg = min(base[1] + depth * 6, 245)
    db = min(base[2] + depth * 6, 245)
    return _pack_rgba(dr, dg, db, alpha)


def _treemap_items(node):
    items = []
    for child_name, child_node in node["children"].items():
        if child_node["sum_avg"] > 0.0:
            items.append(("group", child_name, child_node, child_node["sum_avg"]))
    for row_label, rec in node["rows"]:
        if rec["avg"] > 0.0:
            items.append(("leaf", row_label, rec, rec["avg"]))
    items.sort(key=lambda it: it[3], reverse=True)
    return items


def _treemap_layout(items, x, y, w, h):
    total = sum(it[3] for it in items)
    if total <= 0.0:
        return []
    vertical = w >= h
    rects = []
    offset = 0.0
    last = len(items) - 1
    for i, it in enumerate(items):
        frac = it[3] / total
        if vertical:
            cw = (w - offset) if i == last else max(1.0, w * frac)
            rects.append((it, x + offset, y, cw, h))
            offset += cw
        else:
            ch = (h - offset) if i == last else max(1.0, h * frac)
            rects.append((it, x, y + offset, w, ch))
            offset += ch
    return rects


def _draw_treemap_tooltip_for_item(item, bucket_sums, visible_total):
    item_type, label, payload, weight = item
    if not PyImGui.begin_tooltip():
        return

    if item_type == "leaf":
        rec = payload
        share = _record_share(rec, bucket_sums, visible_total) * 100.0
        d = rec["data"]
        PyImGui.text(rec["name"])
        PyImGui.separator()
        PyImGui.text(f"Bucket: {rec['exec_bucket']}")
        PyImGui.text(f"Phase: {rec['phase']}")
        PyImGui.text(f"Avg: {d['avg']:.3f}ms  ({share:.2f}% bucket)")
        PyImGui.text(f"Min: {d['min']:.3f}  P50: {d['p50']:.3f}  P95: {d['p95']:.3f}")
        PyImGui.text(f"P99: {d['p99']:.3f}  Max: {d['max']:.3f}")
        if rec["path_segments"]:
            PyImGui.text("Segments: " + " / ".join(rec["path_segments"][:8]))
    else:
        node = payload
        PyImGui.text(label)
        PyImGui.separator()
        PyImGui.text(f"Metrics: {node['count']}")
        PyImGui.text(f"Avg Sum: {node['sum_avg']:.3f}ms")
        for bucket_label, bucket_sum, bucket_share in _node_share(node, bucket_sums, visible_total):
            PyImGui.text(f"{bucket_label}: {bucket_sum:.3f}ms ({bucket_share * 100:.1f}%)")

    PyImGui.end_tooltip()


def _draw_treemap_node(node, x, y, w, h, depth, path, bucket_sums, visible_total):
    if w < 4.0 or h < 4.0 or node["sum_avg"] <= 0.0:
        return

    items = _treemap_items(node)
    if not items:
        return

    padding = 1.0 if depth == 0 else 0.5
    content_x = x + padding
    content_y = y + padding
    content_w = max(1.0, w - 2 * padding)
    content_h = max(1.0, h - 2 * padding)

    for idx, (item, rx, ry, rw, rh) in enumerate(_treemap_layout(items, content_x, content_y, content_w, content_h)):
        item_type, label, payload, weight = item
        if rw < 2.0 or rh < 2.0:
            continue

        if item_type == "leaf":
            bucket = payload["exec_bucket"]
        else:
            bucket = _dominant_bucket_for_node(payload)

        fill = _treemap_color(bucket, depth)
        border = _pack_rgba(25, 25, 25, 255)
        PyImGui.draw_list_add_rect_filled(rx, ry, rx + rw, ry + rh, fill, 0.0, 0)
        PyImGui.draw_list_add_rect(rx, ry, rx + rw, ry + rh, border, 0.0, 0, 2.0)

        if rw > 72.0 and rh > 18.0:
            caption = label
            if item_type == "group":
                caption = f"{label}"
            PyImGui.draw_list_add_text(rx + 3, ry + 2, _pack_rgba(255, 255, 255, 255), caption)

        PyImGui.set_cursor_screen_pos(rx, ry)
        PyImGui.invisible_button(f"##tm_{path}_{depth}_{idx}", rw, rh)
        if PyImGui.is_item_hovered():
            _draw_treemap_tooltip_for_item(item, bucket_sums, visible_total)

        if item_type == "group" and depth < ui_treemap_max_depth and rw > 28.0 and rh > 20.0:
            _draw_treemap_node(payload, rx + 1.0, ry + 14.0, max(1.0, rw - 2.0), max(1.0, rh - 15.0), depth + 1, f"{path}_{idx}", bucket_sums, visible_total)


def _draw_treemap(tree, bucket_sums, visible_total):
    avail_w, avail_h = PyImGui.get_content_region_avail()
    canvas_w = max(200.0, avail_w)
    canvas_h = max(260.0, min(520.0, avail_h if avail_h > 0 else 520.0))

    PyImGui.text_disabled("Treemap area proportional to avg time (WinDirStat-style). Hover rectangles for detailed metrics.")
    start_x, start_y = PyImGui.get_cursor_screen_pos()
    PyImGui.dummy(int(canvas_w), int(canvas_h))

    bg = _pack_rgba(22, 22, 22, 255)
    border = _pack_rgba(70, 70, 70, 255)
    PyImGui.draw_list_add_rect_filled(start_x, start_y, start_x + canvas_w, start_y + canvas_h, bg, 0.0, 0)
    PyImGui.draw_list_add_rect(start_x, start_y, start_x + canvas_w, start_y + canvas_h, border, 0.0, 0, 2.0)

    _draw_treemap_node(tree, start_x + 2.0, start_y + 2.0, canvas_w - 4.0, canvas_h - 4.0, 0, "root", bucket_sums, visible_total)


def _build_script_phase_groups(records):
    groups = {}
    for rec in records:
        script = rec["script"] or rec["leaf"]
        group = groups.get(script)
        if group is None:
            group = {
                "script": script,
                "sum_avg": 0.0,
                "count": 0,
                "phases": {"Draw": [], "Main": [], "Update": [], "Other": []},
            }
            groups[script] = group

        group["sum_avg"] += rec["avg"]
        group["count"] += 1
        phase_key = rec["phase"] if rec["phase"] in ("Draw", "Main", "Update") else "Other"
        group["phases"][phase_key].append(rec)

    for group in groups.values():
        for phase_list in group["phases"].values():
            phase_list.sort(key=lambda r: r["avg"], reverse=True)

    return sorted(groups.values(), key=lambda g: g["sum_avg"], reverse=True)


def _draw_script_group_tooltip(group, bucket_sums, visible_total):
    if not PyImGui.begin_tooltip():
        return

    PyImGui.text(group["script"])
    PyImGui.separator()
    PyImGui.text(f"Leaf metrics: {group['count']}")
    PyImGui.text(f"Avg Sum: {group['sum_avg']:.3f}ms")
    for phase_key in ("Draw", "Main", "Update", "Other"):
        phase_sum = sum(r["avg"] for r in group["phases"][phase_key])
        if phase_sum <= 0.0:
            continue
        if phase_key in ("Draw", "Main"):
            denom = bucket_sums.get(FRAME_BUCKET, 0.0)
        elif phase_key == "Update":
            denom = bucket_sums.get(UPDATE_BUCKET, 0.0)
        else:
            denom = visible_total
        PyImGui.text(f"{phase_key}: {phase_sum:.3f}ms ({_safe_share(phase_sum, denom) * 100:.1f}%)")

    PyImGui.end_tooltip()


def _draw_treemap_leaf_only(records, row_label_dim, bucket_sums, visible_total):
    avail_w, avail_h = PyImGui.get_content_region_avail()
    canvas_w = max(200.0, avail_w)
    canvas_h = max(260.0, min(520.0, avail_h if avail_h > 0 else 520.0))

    PyImGui.text_disabled("Treemap mosaic: script containers -> phase partitions -> leaf timings (only leaves count for area).")
    start_x, start_y = PyImGui.get_cursor_screen_pos()
    PyImGui.dummy(int(canvas_w), int(canvas_h))

    bg = _pack_rgba(22, 22, 22, 255)
    border = _pack_rgba(70, 70, 70, 255)
    PyImGui.draw_list_add_rect_filled(start_x, start_y, start_x + canvas_w, start_y + canvas_h, bg, 0.0, 0)
    PyImGui.draw_list_add_rect(start_x, start_y, start_x + canvas_w, start_y + canvas_h, border, 0.0, 0, 2.0)

    script_groups = _build_script_phase_groups(records)
    script_items = [("script", g["script"], g, g["sum_avg"]) for g in script_groups if g["sum_avg"] > 0.0]

    for sidx, (sitem, sx, sy, sw, sh) in enumerate(_treemap_layout(script_items, start_x + 2.0, start_y + 2.0, canvas_w - 4.0, canvas_h - 4.0)):
        _stype, _slabel, group, _sweight = sitem
        if sw < 6.0 or sh < 6.0:
            continue

        # Script container boundary (not a competing metric; area derives from sum of child leaves).
        PyImGui.draw_list_add_rect_filled(sx, sy, sx + sw, sy + sh, _pack_rgba(28, 28, 28, 255), 0.0, 0)
        PyImGui.draw_list_add_rect(sx, sy, sx + sw, sy + sh, _pack_rgba(90, 90, 90, 255), 0.0, 0, 2.0)
        if sw > 90.0 and sh > 22.0:
            PyImGui.draw_list_add_text(sx + 3, sy + 2, _pack_rgba(255, 255, 255, 255), group["script"])

        PyImGui.set_cursor_screen_pos(sx, sy)
        PyImGui.invisible_button(f"##tm_script_{sidx}", sw, sh)
        if PyImGui.is_item_hovered():
            _draw_script_group_tooltip(group, bucket_sums, visible_total)

        header_h = 14.0 if sh > 22.0 else 0.0
        inner_x = sx + 1.0
        inner_y = sy + 1.0 + header_h
        inner_w = max(1.0, sw - 2.0)
        inner_h = max(1.0, sh - 2.0 - header_h)
        if inner_w <= 2.0 or inner_h <= 2.0:
            continue

        phase_items = []
        for phase_key in ("Draw", "Main", "Update", "Other"):
            phase_recs = group["phases"][phase_key]
            phase_sum = sum(r["avg"] for r in phase_recs)
            if phase_sum > 0.0:
                phase_items.append(("phase", phase_key, phase_recs, phase_sum))

        for pidx, (pitem, px, py, pw, ph) in enumerate(_treemap_layout(phase_items, inner_x, inner_y, inner_w, inner_h)):
            _ptype, phase_key, phase_recs, _psum = pitem
            if pw < 4.0 or ph < 4.0:
                continue

            # Phase partition background (container only).
            PyImGui.draw_list_add_rect_filled(px, py, px + pw, py + ph, _phase_color(phase_key, 0, 110), 0.0, 0)
            PyImGui.draw_list_add_rect(px, py, px + pw, py + ph, _pack_rgba(40, 40, 40, 220), 0.0, 0, 1.0)
            if pw > 55.0 and ph > 15.0:
                PyImGui.draw_list_add_text(px + 2, py + 1, _pack_rgba(255, 255, 255, 230), phase_key)

            phase_header_h = 12.0 if ph > 17.0 else 0.0
            leaf_x = px + 1.0
            leaf_y = py + 1.0 + phase_header_h
            leaf_w = max(1.0, pw - 2.0)
            leaf_h = max(1.0, ph - 2.0 - phase_header_h)
            if leaf_w <= 2.0 or leaf_h <= 2.0:
                continue

            leaf_items = []
            for rec in phase_recs:
                label = rec.get(row_label_dim, rec["leaf"]) or rec["leaf"]
                leaf_items.append(("leaf", label, rec, rec["avg"]))

            for lidx, (litem, lx, ly, lw, lh) in enumerate(_treemap_layout(leaf_items, leaf_x, leaf_y, leaf_w, leaf_h)):
                item_type, label, rec, _lweight = litem
                if lw < 2.0 or lh < 2.0:
                    continue

                PyImGui.draw_list_add_rect_filled(lx, ly, lx + lw, ly + lh, _phase_color(phase_key, 1, 235), 0.0, 0)
                PyImGui.draw_list_add_rect(lx, ly, lx + lw, ly + lh, _pack_rgba(20, 20, 20, 220), 0.0, 0, 1.0)
                if lw > 78.0 and lh > 16.0:
                    PyImGui.draw_list_add_text(lx + 2, ly + 1, _pack_rgba(255, 255, 255, 255), label)

                PyImGui.set_cursor_screen_pos(lx, ly)
                PyImGui.invisible_button(f"##tm_leaf_{sidx}_{pidx}_{lidx}", lw, lh)
                if PyImGui.is_item_hovered():
                    _draw_treemap_tooltip_for_item((item_type, label, rec, rec["avg"]), bucket_sums, visible_total)


def _clamp_filter_indices():
    global ui_filter_exec_idx
    global ui_filter_phase_idx
    global ui_filter_section1_idx
    global ui_filter_section2_idx
    global ui_filter_segment_idx
    ui_filter_exec_idx = min(ui_filter_exec_idx, max(0, len(filter_exec_options) - 1))
    ui_filter_phase_idx = min(ui_filter_phase_idx, max(0, len(filter_phase_options) - 1))
    ui_filter_section1_idx = min(ui_filter_section1_idx, max(0, len(filter_section1_options) - 1))
    ui_filter_section2_idx = min(ui_filter_section2_idx, max(0, len(filter_section2_options) - 1))
    ui_filter_segment_idx = min(ui_filter_segment_idx, max(0, len(filter_segment_options) - 1))


def _record_passes_filters(rec):
    if rec["avg"] < ui_min_avg_threshold_ms:
        return False
    if ui_hide_totals and rec["is_total"]:
        return False

    if ui_filter_exec_idx > 0 and rec["exec_bucket"] != filter_exec_options[ui_filter_exec_idx]:
        return False
    if ui_filter_phase_idx > 0 and rec["phase"] != filter_phase_options[ui_filter_phase_idx]:
        return False
    if ui_filter_section1_idx > 0 and rec["section1"] != filter_section1_options[ui_filter_section1_idx]:
        return False
    if ui_filter_section2_idx > 0 and rec["section2"] != filter_section2_options[ui_filter_section2_idx]:
        return False
    if ui_filter_segment_idx > 0:
        seg = filter_segment_options[ui_filter_segment_idx]
        if seg not in rec["path_segments"]:
            return False
    return True


def _draw_filters():
    global ui_min_avg_threshold_ms
    global ui_show_progress_bars
    global ui_hide_totals
    global ui_filter_exec_idx
    global ui_filter_phase_idx
    global ui_filter_section1_idx
    global ui_filter_section2_idx
    global ui_filter_segment_idx

    PyImGui.text("Filters (derived from actual metric paths)")
    ui_show_progress_bars = PyImGui.checkbox("Progress bars", ui_show_progress_bars)
    PyImGui.same_line(0, -1)
    ui_hide_totals = PyImGui.checkbox("Hide .Total rows", ui_hide_totals)

    ui_min_avg_threshold_ms = PyImGui.slider_float("Min Avg Threshold (ms)", ui_min_avg_threshold_ms, 0.0, 10.0)

    PyImGui.set_next_item_width(220)
    ui_filter_exec_idx = PyImGui.combo("Exec Bucket", ui_filter_exec_idx, filter_exec_options)
    PyImGui.set_next_item_width(220)
    ui_filter_phase_idx = PyImGui.combo("Phase", ui_filter_phase_idx, filter_phase_options)
    PyImGui.set_next_item_width(220)
    ui_filter_section1_idx = PyImGui.combo("Section 1", ui_filter_section1_idx, filter_section1_options)
    PyImGui.set_next_item_width(220)
    ui_filter_section2_idx = PyImGui.combo("Section 2", ui_filter_section2_idx, filter_section2_options)
    PyImGui.set_next_item_width(260)
    ui_filter_segment_idx = PyImGui.combo("Any Path Segment", ui_filter_segment_idx, filter_segment_options)


def _draw_view_controls():
    global ui_view_mode
    global ui_group_dim_1
    global ui_group_dim_2
    global ui_group_dim_3
    global ui_row_label_dim
    global ui_pivot_sort_mode
    global ui_treemap_max_depth

    ui_view_mode = PyImGui.combo("View", ui_view_mode, VIEW_MODES)

    if ui_view_mode == 0:
        ui_group_dim_1 = PyImGui.combo("Group Level 1", ui_group_dim_1, GROUP_DIM_LABELS)
        ui_group_dim_2 = PyImGui.combo("Group Level 2", ui_group_dim_2, GROUP_DIM_LABELS)
        ui_group_dim_3 = PyImGui.combo("Group Level 3", ui_group_dim_3, GROUP_DIM_LABELS)
        ui_row_label_dim = PyImGui.combo("Row Label", ui_row_label_dim, GROUP_DIM_LABELS)
    elif ui_view_mode == 1:
        ui_pivot_sort_mode = PyImGui.combo("Pivot Sort", ui_pivot_sort_mode, PIVOT_SORT_MODES)
    else:
        ui_treemap_max_depth = PyImGui.combo("Treemap Depth", ui_treemap_max_depth, ["0", "1", "2", "3", "4", "5"])


def update():
    global initialized
    global metric_names
    global metrics_dict
    global metric_records
    global update_timer

    if update_timer.IsExpired():
        initialized = False
        update_timer.Reset()

    if not initialized:
        initialized = True
        metric_names = Py4GW.Console.get_profiler_metric_names()
        reports = Py4GW.Console.get_profiler_reports()
        metrics_dict = {
            name: {
                "min": min_time,
                "avg": avg_time,
                "p50": p_50,
                "p95": p_95,
                "p99": p_99,
                "max": max_tim,
            }
            for name, min_time, avg_time, p_50, p_95, p_99, max_tim in reports
        }
        metric_records = _build_metric_records(metric_names, metrics_dict)
        _build_filter_options(metric_records)
        _clamp_filter_indices()


def draw():
    if not PyImGui.begin("Profiler Data"):
        PyImGui.end()
        return

    if PyImGui.button("print all"):
        for name, data in metrics_dict.items():
            print(
                f"{name}: Min={data['min']:.2f}ms, Avg={data['avg']:.2f}ms, P50={data['p50']:.2f}ms, "
                f"P95={data['p95']:.2f}ms, P99={data['p99']:.2f}ms, Max={data['max']:.2f}ms"
            )

    _draw_view_controls()
    PyImGui.separator()
    _draw_filters()

    if not metric_records:
        PyImGui.text("No data available")
        PyImGui.end()
        return

    visible_records = [rec for rec in metric_records if _record_passes_filters(rec)]
    bucket_sums, visible_total = _draw_budget_summary(visible_records)
    PyImGui.separator()

    if not visible_records:
        PyImGui.text("No metrics match current filters")
        PyImGui.end()
        return

    selected_dims = _distinct_dims([GROUP_DIMS[ui_group_dim_1], GROUP_DIMS[ui_group_dim_2], GROUP_DIMS[ui_group_dim_3]])
    row_label_dim = GROUP_DIMS[ui_row_label_dim]

    if ui_view_mode == 0:
        tree = _build_dynamic_tree(visible_records, selected_dims, row_label_dim)
        PyImGui.text_disabled("Hierarchy mode: configurable grouping. Draw/Main share FrameLoop; Update is separate.")
        _draw_tree_node(tree, "root", "root", 0, bucket_sums, visible_total)
    elif ui_view_mode == 1:
        PyImGui.text_disabled("Leaf Pivot: compares Draw/Main/Update per script (leaf timings aggregated into script rows).")
        _draw_pivot_table(visible_records, bucket_sums, visible_total)
    else:
        treemap_records = [rec for rec in visible_records if not rec["is_total"]]
        treemap_bucket_sums, treemap_visible_total = _sum_buckets(treemap_records)
        PyImGui.text_disabled("Treemap mode: rectangle area = avg time (leaf metrics only, totals excluded).")
        if treemap_records:
            _draw_treemap_leaf_only(treemap_records, row_label_dim, treemap_bucket_sums, treemap_visible_total)
        else:
            PyImGui.text("No non-total metrics match current filters")

    PyImGui.end()


if __name__ == "__main__":
    update()
