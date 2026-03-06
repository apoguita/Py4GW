"""
WorldMap+Debug
==============
Two-tab debug GUI:
  Tab 1 – Portal List   : all maps with portal counts. Red = explorable + 0 portals + has DAT.
  Tab 2 – Find Unknowns : scans boundary props of explorable maps with 0 portals to find
                          candidate model IDs not yet in _KNOWN_PORTAL_MODEL_FILE_IDS.

How "Find Unknowns" works
──────────────────────────
For every explorable map that has a DAT entry but 0 portals, the tool reads the raw FFNA
prop list and keeps only props whose position is near the pathing boundary (outer 20% of the
X/Y extent derived from trapezoids).  The model IDs of those boundary props are collected.
IDs that are already known are ignored.  Candidates are sorted by how many maps they appear
in – the ones at the top are most likely unregistered portal models.
"""

import PyImGui
import Py4GW
import os

from Py4GWCoreLib import Map, Player
from Py4GWCoreLib.native_src.methods.MapMethods import MapMethods
from Py4GWCoreLib.native_src.methods.FfnaMapMethods import (
    FfnaMapMethods,
    _KNOWN_PORTAL_MODEL_FILE_IDS,
    parse_ffna_prop_filenames,
    parse_ffna_prop_positions,
    parse_ffna_pathing,
    is_ffna_pathing,
)

MODULE_NAME = "WorldMap+Debug"

try:
    _SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
except NameError:
    _SCRIPT_DIR = os.path.join(
        Py4GW.Console.get_projects_path(),
        "Widgets", "Guild Wars", "Screen Overlays"
    )

import Py4GWCoreLib.WorldPathing as _WP
_WP.configure(_SCRIPT_DIR)
from Py4GWCoreLib.WorldPathing import (
    _ICON_BOUNDS, _MAP_META,
    _PORTAL_ICON_POS,
    _ensure_portal_dots,
    _load_portal_destinations,
)

_MAX_MAP_ID    = 900
_RT_EXPLORABLE = 2

# ── Shared state ───────────────────────────────────────────────────────────────
_initialized = [False]

# ── Tab 1 state ────────────────────────────────────────────────────────────────
_scan_done         = [False]
_filter_text       = [""]
_show_only_missing = [False]
_show_only_explo   = [True]
_selected_map_id   = [0]
# (map_id, name, portal_count, has_dat, rtype)
_portal_list: list[tuple[int, str, int, bool, int]] = []

# ── Tab 2 state ────────────────────────────────────────────────────────────────
_candidate_done   = [False]
_candidate_status = [""]
_cand_filter      = [""]
# (hex_str, map_count, [map_id, ...])
_candidates: list[tuple[str, int, list[int]]] = []
_cand_selected_id = [0]
# {model_id: [(map_id, x, y), ...]}
_cand_positions: dict[int, list[tuple[int, float, float]]] = {}
_window_size_set = [False]

# ── Tab 3 state ────────────────────────────────────────────────────────────────
_near_radius      = [500]
_near_status      = [""]
# (dist, model_id_hex, x, y, known_label)  known_label="" if unknown
_near_results: list[tuple[float, str, float, float, str]] = []



def _init() -> None:
    if _MAP_META:
        return
    for mid in range(1, _MAX_MAP_ID + 1):
        info = MapMethods.GetMapInfo(mid)
        if info is None or (info.flags & 0x20):
            _ICON_BOUNDS[mid] = None
            continue
        if info.icon_start_x != 0 or info.icon_end_x != 0:
            l = float(info.icon_start_x); t = float(info.icon_start_y)
            r = float(info.icon_end_x);   b = float(info.icon_end_y)
        elif info.icon_start_x_dupe != 0 or info.icon_end_x_dupe != 0:
            l = float(info.icon_start_x_dupe); t = float(info.icon_start_y_dupe)
            r = float(info.icon_end_x_dupe);   b = float(info.icon_end_y_dupe)
        else:
            _ICON_BOUNDS[mid] = None
            continue
        if l > r: l, r = r, l
        if t > b: t, b = b, t
        if l == r or t == b:
            _ICON_BOUNDS[mid] = None
            continue
        _ICON_BOUNDS[mid] = (l, t, r, b)
        try:
            name = Map.GetMapName(mid) or f"Map {mid}"
        except Exception:
            name = f"Map {mid}"
        _MAP_META[mid] = (int(info.type), name, int(info.campaign))
    _load_portal_destinations()


def _do_scan() -> None:
    global _portal_list
    _portal_list = []
    cmap = Map.GetMapID()
    for mid in sorted(_ICON_BOUNDS.keys()):
        if _ICON_BOUNDS.get(mid) is None or mid not in _MAP_META:
            continue
        rtype, name, _ = _MAP_META[mid]
        _ensure_portal_dots(mid, is_live=(mid == cmap))
        dots    = _PORTAL_ICON_POS.get(mid, [])
        has_dat = FfnaMapMethods.HasDatEntry(mid)
        _portal_list.append((mid, name, len(dots), has_dat, rtype))
    _scan_done[0] = True
    miss = sum(1 for e in _portal_list if e[2] == 0 and e[4] == _RT_EXPLORABLE)
    Py4GW.Console.Log(MODULE_NAME,
        f"Scan: {len(_portal_list)} maps, {miss} explorables with 0 portals.",
        Py4GW.Console.MessageType.Info)


# ── Tab 2 helpers ──────────────────────────────────────────────────────────────
_BOUNDARY_FRACTION = 0.20


def _get_pathing_extents(data: bytes) -> tuple[float, float, float, float] | None:
    if not is_ffna_pathing(data):
        return None
    planes = parse_ffna_pathing(data)
    if not planes:
        return None
    gx_min = float('inf');  gx_max = float('-inf')
    gy_min = float('inf');  gy_max = float('-inf')
    for plane in planes:
        for t in plane.trapezoids:
            for x in (t.xtl, t.xtr, t.xbl, t.xbr):
                if x < gx_min: gx_min = x
                if x > gx_max: gx_max = x
            for y in (t.yt, t.yb):
                if y < gy_min: gy_min = y
                if y > gy_max: gy_max = y
    if gx_min == float('inf') or gx_max <= gx_min or gy_max <= gy_min:
        return None
    return gx_min, gx_max, gy_min, gy_max


def _is_boundary(x: float, y: float,
                 xmin: float, xmax: float,
                 ymin: float, ymax: float,
                 frac: float) -> bool:
    mx = (xmax - xmin) * frac
    my = (ymax - ymin) * frac
    return x <= xmin + mx or x >= xmax - mx or y <= ymin + my or y >= ymax - my


def _do_find_candidates() -> None:
    global _candidates, _cand_positions
    _candidates = []
    _cand_positions = {}
    _candidate_status[0] = "Scanning…"

    cand_maps: dict[int, set[int]] = {}
    cand_pos_raw: dict[int, list[tuple[int, float, float]]] = {}

    cmap = Map.GetMapID()
    scanned = 0
    for mid in sorted(_ICON_BOUNDS.keys()):
        if _ICON_BOUNDS.get(mid) is None or mid not in _MAP_META:
            continue
        rtype, _, _ = _MAP_META[mid]
        if rtype != _RT_EXPLORABLE:
            continue
        _ensure_portal_dots(mid, is_live=(mid == cmap))
        if len(_PORTAL_ICON_POS.get(mid, [])) > 0:
            continue      # already has portals – skip
        if not FfnaMapMethods.HasDatEntry(mid):
            continue

        data = FfnaMapMethods._read_ffna(mid)
        if data is None:
            continue
        extents = _get_pathing_extents(data)
        if extents is None:
            continue
        xmin, xmax, ymin, ymax = extents

        filenames = parse_ffna_prop_filenames(data)
        positions = parse_ffna_prop_positions(data)
        if not filenames or not positions:
            continue

        scanned += 1
        for fi, px, py, _pz in positions:
            if fi >= len(filenames):
                continue
            fid = filenames[fi]
            if fid in _KNOWN_PORTAL_MODEL_FILE_IDS or fid == 0:
                continue
            if not _is_boundary(px, py, xmin, xmax, ymin, ymax, _BOUNDARY_FRACTION):
                continue
            cand_maps.setdefault(fid, set()).add(mid)
            cand_pos_raw.setdefault(fid, []).append((mid, px, py))

    sorted_cands = sorted(cand_maps.items(), key=lambda kv: -len(kv[1]))
    _candidates = [(f"0x{fid:X}", len(mids), sorted(mids))
                   for fid, mids in sorted_cands]
    _cand_positions = {fid: pos for fid, pos in cand_pos_raw.items()}
    _candidate_done[0] = True
    _candidate_status[0] = (
        f"Done. Scanned {scanned} explorable maps with 0 portals. "
        f"Found {len(_candidates)} candidate model IDs."
    )
    Py4GW.Console.Log(MODULE_NAME, _candidate_status[0], Py4GW.Console.MessageType.Info)


def _do_near_player_scan() -> None:
    """Read all props from current map DAT (or live TravelPortals if no DAT) within _near_radius."""
    global _near_results
    _near_results = []
    _near_status[0] = ""

    cmap = Map.GetMapID()

    try:
        px, py = Player.GetXY()
    except Exception as e:
        _near_status[0] = f"Could not get player position: {e}"
        return

    radius = float(_near_radius[0])
    results: list[tuple[float, str, float, float, str]] = []

    if not FfnaMapMethods.HasDatEntry(cmap):
        # No DAT entry – fall back to live TravelPortal data from game memory
        try:
            live_portals = Map.Pathing.GetTravelPortals()
        except Exception as e:
            _near_status[0] = f"Map {cmap} has no DAT entry and live read failed: {e}"
            return
        for tp in live_portals:
            dx   = tp.x - px
            dy   = tp.y - py
            dist = (dx * dx + dy * dy) ** 0.5
            if dist > radius:
                continue
            fid         = tp.model_file_id
            fid_hex     = f"0x{fid:X}"
            known_label = _KNOWN_PORTAL_MODEL_FILE_IDS.get(fid, "")
            results.append((dist, fid_hex, tp.x, tp.y, known_label))
        source = "live"
    else:
        data = FfnaMapMethods._read_ffna(cmap)
        if data is None:
            _near_status[0] = f"Could not read DAT for map {cmap}."
            return

        filenames = parse_ffna_prop_filenames(data)
        positions = parse_ffna_prop_positions(data)
        if not filenames or not positions:
            _near_status[0] = "No prop data found."
            return

        for fi, prop_x, prop_y, _pz in positions:
            if fi >= len(filenames):
                continue
            fid  = filenames[fi]
            dx   = prop_x - px
            dy   = prop_y - py
            dist = (dx * dx + dy * dy) ** 0.5
            if dist > radius:
                continue
            fid_hex     = f"0x{fid:X}"
            known_label = _KNOWN_PORTAL_MODEL_FILE_IDS.get(fid, "")
            results.append((dist, fid_hex, prop_x, prop_y, known_label))
        source = "dat"

    results.sort(key=lambda r: r[0])
    _near_results = results
    _near_status[0] = (
        f"[{source}] Player: ({px:.0f}, {py:.0f})   Map {cmap}   "
        f"radius {radius:.0f}   found {len(results)} props"
    )
    Py4GW.Console.Log(MODULE_NAME, _near_status[0], Py4GW.Console.MessageType.Info)


# ── Entry point ────────────────────────────────────────────────────────────────
def main() -> None:
    try:
        if not _initialized[0]:
            _init()
            _initialized[0] = True

        if not _window_size_set[0]:
            PyImGui.set_next_window_size(700, 640)
            _window_size_set[0] = True
        if not PyImGui.begin("WorldMap+ Debug##wmpd", True, PyImGui.WindowFlags.NoFlag):
            PyImGui.end()
            return

        win_w = PyImGui.get_content_region_avail()[0]

        if PyImGui.begin_tab_bar("##wmpd_tabs"):

            # ── TAB 1: Portal List ─────────────────────────────────────────
            if PyImGui.begin_tab_item("Portal List##wmpd_t1"):
                if PyImGui.button("Scan All Maps##wmpd_scan", win_w, 0):
                    _do_scan()
                if _scan_done[0]:
                    miss = sum(1 for e in _portal_list if e[2] == 0 and e[4] == _RT_EXPLORABLE)
                    PyImGui.text(f"{len(_portal_list)} maps   {miss} explorables with 0 portals")
                else:
                    PyImGui.text_disabled("Press 'Scan All Maps' to populate the list")
                PyImGui.spacing()
                _show_only_missing[0] = PyImGui.checkbox("Only missing##wmpd_miss", _show_only_missing[0])
                PyImGui.same_line(0, 12)
                _show_only_explo[0]   = PyImGui.checkbox("Explorables only##wmpd_explo", _show_only_explo[0])
                PyImGui.spacing()
                PyImGui.push_item_width(win_w)
                _filter_text[0] = PyImGui.input_text("##wmpd_filter", _filter_text[0], 128)
                PyImGui.pop_item_width()
                PyImGui.text_disabled("filter by name or map ID")
                PyImGui.separator()

                if _scan_done[0]:
                    flt     = _filter_text[0].strip().lower()
                    sel_mid = _selected_map_id[0]
                    detail_h = 90 if sel_mid > 0 else 0
                    avail_h  = PyImGui.get_content_region_avail()[1]
                    list_h   = max(60, avail_h - detail_h - 8)

                    if PyImGui.begin_child("##wmpd_list", (win_w, list_h), False, PyImGui.WindowFlags.NoFlag):
                        PyImGui.text_colored("   ID    Type    DAT    Portals    Name", (0.6, 0.85, 1.0, 1.0))
                        PyImGui.separator()
                        for mid, name, pcnt, has_dat, rtype in _portal_list:
                            if _show_only_explo[0] and rtype != _RT_EXPLORABLE:
                                continue
                            if _show_only_missing[0] and pcnt > 0:
                                continue
                            if flt and flt not in name.lower() and flt not in str(mid):
                                continue
                            type_str = "Explo" if rtype == _RT_EXPLORABLE else f"t{rtype:02d}"
                            dat_str  = "yes" if has_dat else " no"
                            row_lbl  = f"{mid:>5}    {type_str}    {dat_str}    {pcnt:>7}    {name}"
                            if rtype == _RT_EXPLORABLE and pcnt == 0 and has_dat:
                                col = (1.0, 0.35, 0.35, 1.0)
                            elif rtype == _RT_EXPLORABLE and pcnt == 0 and not has_dat:
                                col = (1.0, 0.85, 0.3, 1.0)
                            elif rtype == _RT_EXPLORABLE:
                                col = (0.6, 1.0, 0.6, 1.0)
                            else:
                                col = (0.72, 0.72, 0.72, 1.0)
                            PyImGui.push_style_color(PyImGui.ImGuiCol.Text, col)
                            selected = (mid == sel_mid)
                            if PyImGui.selectable(row_lbl + f"##wmpd_{mid}", selected,
                                                  PyImGui.SelectableFlags.NoFlag, (0, 0)):
                                _selected_map_id[0] = mid if not selected else 0
                            PyImGui.pop_style_color(1)
                    PyImGui.end_child()

                    if sel_mid > 0:
                        PyImGui.separator()
                        meta     = _MAP_META.get(sel_mid)
                        sel_name = meta[1] if meta else f"Map {sel_mid}"
                        rtype2   = meta[0] if meta else 0
                        has_dat2 = FfnaMapMethods.HasDatEntry(sel_mid)
                        PyImGui.text_colored(
                            f"Map {sel_mid}: {sel_name}  (type {rtype2})  DAT: {'yes' if has_dat2 else 'no'}",
                            (0.9, 0.95, 1.0, 1.0))
                        dots = _PORTAL_ICON_POS.get(sel_mid, [])
                        cmap = Map.GetMapID()
                        if dots:
                            for d in dots:
                                gid = int(d[4]) if len(d) >= 5 else -1
                                if len(d) >= 7:
                                    gx, gy = float(d[5]), float(d[6])
                                    PyImGui.text(f"  portal_id={gid}   game({gx:.0f}, {gy:.0f})")
                                    if cmap == sel_mid:
                                        PyImGui.same_line(0, 8)
                                        if PyImGui.button(f"MoveTo##{gid}", 0, 0):
                                            Player.Move(gx, gy)
                                else:
                                    PyImGui.text(f"  portal_id={gid}   (no game coords)")
                        else:
                            PyImGui.text_disabled("  (no portals detected)")

                PyImGui.end_tab_item()

            # ── TAB 2: Find Unknown Portals ────────────────────────────────
            if PyImGui.begin_tab_item("Find Unknowns##wmpd_t2"):
                PyImGui.text_wrapped(
                    "Scans boundary props of explorable maps with 0 portals. "
                    "Already-known model IDs are excluded. "
                    "More maps = more likely a real portal model."
                )
                PyImGui.spacing()
                PyImGui.text_colored("Currently known IDs:", (0.6, 0.85, 1.0, 1.0))
                for fid, label in _KNOWN_PORTAL_MODEL_FILE_IDS.items():
                    PyImGui.text(f"  0x{fid:X}  {label}")
                PyImGui.spacing()
                PyImGui.separator()
                PyImGui.spacing()

                if PyImGui.button("Find Candidate Models##wmpd_findbtn", win_w, 0):
                    _do_find_candidates()

                if _candidate_status[0]:
                    PyImGui.text_wrapped(_candidate_status[0])

                if _candidate_done[0]:
                    PyImGui.spacing()
                    PyImGui.push_item_width(win_w)
                    _cand_filter[0] = PyImGui.input_text("##wmpd_cfilter", _cand_filter[0], 64)
                    PyImGui.pop_item_width()
                    PyImGui.text_disabled("filter by hex ID or map ID")
                    PyImGui.separator()

                    csel    = _cand_selected_id[0]
                    cf      = _cand_filter[0].strip().lower()
                    det2_h  = 120 if csel > 0 else 0
                    avail2  = PyImGui.get_content_region_avail()[1]
                    list2_h = max(60, avail2 - det2_h - 8)

                    if PyImGui.begin_child("##wmpd_clist", (win_w, list2_h), False, PyImGui.WindowFlags.NoFlag):
                        PyImGui.text_colored(
                            "  Model ID              Maps    Map IDs (first 8)",
                            (0.6, 0.85, 1.0, 1.0))
                        PyImGui.separator()
                        for cand_hex, cand_cnt, cand_ids in _candidates:
                            if cf and cf not in cand_hex.lower() and not any(cf in str(m) for m in cand_ids):
                                continue
                            preview  = " ".join(str(m) for m in cand_ids[:8])
                            suffix   = f" +{cand_cnt - 8}" if cand_cnt > 8 else ""
                            row_lbl  = f"  {cand_hex:<20}  {cand_cnt:>4}    {preview}{suffix}"
                            if cand_cnt >= 5:
                                col = (1.0, 0.9, 0.3, 1.0)
                            elif cand_cnt >= 2:
                                col = (0.6, 1.0, 0.6, 1.0)
                            else:
                                col = (0.75, 0.75, 0.75, 1.0)
                            fid_int   = int(cand_hex, 16)
                            selected2 = (fid_int == csel)
                            PyImGui.push_style_color(PyImGui.ImGuiCol.Text, col)
                            if PyImGui.selectable(row_lbl + f"##wmpdc_{cand_hex}",
                                                  selected2,
                                                  PyImGui.SelectableFlags.NoFlag, (0, 0)):
                                _cand_selected_id[0] = fid_int if not selected2 else 0
                            PyImGui.pop_style_color(1)
                    PyImGui.end_child()

                    if csel > 0:
                        PyImGui.separator()
                        csel_hex = f"0x{csel:X}"
                        pos_list = _cand_positions.get(csel, [])
                        n_maps   = len({p[0] for p in pos_list})
                        cmap = Map.GetMapID()
                        PyImGui.text_colored(
                            f"{csel_hex} – {len(pos_list)} boundary occurrences in {n_maps} maps",
                            (0.9, 0.95, 1.0, 1.0))
                        det_h = min(80, 18 * len(pos_list) + 4)
                        if PyImGui.begin_child("##wmpd_cdet", (win_w, det_h), False, PyImGui.WindowFlags.NoFlag):
                            for (dmid, dx, dy) in pos_list[:30]:
                                dmeta = _MAP_META.get(dmid)
                                dname = dmeta[1] if dmeta else f"Map {dmid}"
                                PyImGui.text(f"  map {dmid} ({dname})  game({dx:.0f}, {dy:.0f})")
                                if cmap == dmid:
                                    PyImGui.same_line(0, 8)
                                    if PyImGui.button(f"MoveTo##cd_{dmid}_{int(dx)}_{int(dy)}", 0, 0):
                                        Player.Move(dx, dy)
                            if len(pos_list) > 30:
                                PyImGui.text_disabled(f"  … +{len(pos_list) - 30} more")
                        PyImGui.end_child()

                PyImGui.end_tab_item()

            # ── TAB 3: Near Player ─────────────────────────────────────────
            if PyImGui.begin_tab_item("Near Player##wmpd_t3"):
                PyImGui.text_wrapped(
                    "Reads ALL props from the current map's DAT file and lists those "
                    "within the given radius of your character. Stand next to a portal "
                    "and scan to identify its model ID."
                )
                PyImGui.spacing()

                cmap3 = Map.GetMapID()
                try:
                    px3, py3 = Player.GetXY()
                    PyImGui.text(f"Player pos: ({px3:.0f}, {py3:.0f})   Map: {cmap3}")
                except Exception:
                    PyImGui.text_disabled("Player position unavailable")

                PyImGui.spacing()
                PyImGui.text("Search radius:")
                PyImGui.push_item_width(160)
                _near_radius[0] = PyImGui.input_int("##wmpd_radius", _near_radius[0])
                PyImGui.pop_item_width()
                if _near_radius[0] < 1:
                    _near_radius[0] = 1

                PyImGui.same_line(0, 12)
                if PyImGui.button("Scan##wmpd_near_scan", 0, 0):
                    _do_near_player_scan()

                if _near_status[0]:
                    PyImGui.text_wrapped(_near_status[0])

                if _near_results:
                    PyImGui.separator()
                    PyImGui.text_colored(
                        "  Dist      Model ID              Known?           X           Y",
                        (0.6, 0.85, 1.0, 1.0))
                    PyImGui.separator()

                    avail3   = PyImGui.get_content_region_avail()[1]
                    list3_h  = max(60, avail3 - 4)
                    if PyImGui.begin_child("##wmpd_nearlist", (win_w, list3_h), False, PyImGui.WindowFlags.NoFlag):
                        cmap_now = Map.GetMapID()
                        for dist, fid_hex, nx, ny, known in _near_results:
                            if known:
                                col  = (0.6, 1.0, 0.6, 1.0)   # green = already known
                                klbl = known
                            else:
                                col  = (1.0, 0.85, 0.3, 1.0)  # yellow = unknown
                                klbl = "UNKNOWN"
                            row = f"  {dist:>7.1f}   {fid_hex:<20}  {klbl:<16}  {nx:>10.0f}  {ny:>10.0f}"
                            PyImGui.push_style_color(PyImGui.ImGuiCol.Text, col)
                            PyImGui.selectable(row + f"##wmpdn_{fid_hex}_{int(nx)}_{int(ny)}",
                                               False, PyImGui.SelectableFlags.NoFlag, (0, 0))
                            PyImGui.pop_style_color(1)
                            if cmap_now == cmap3:
                                PyImGui.same_line(0, 8)
                                if PyImGui.button(f"Move##nr_{fid_hex}_{int(nx)}_{int(ny)}", 0, 0):
                                    Player.Move(nx, ny)
                    PyImGui.end_child()

                PyImGui.end_tab_item()

            PyImGui.end_tab_bar()

        PyImGui.end()

    except Exception as exc:
        try:
            import traceback
            Py4GW.Console.Log(MODULE_NAME,
                f"Error: {exc}\n{traceback.format_exc()}",
                Py4GW.Console.MessageType.Error)
        except Exception:
            pass
