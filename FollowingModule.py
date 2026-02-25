import math

import PyImGui

from Py4GWCoreLib import GLOBAL_CACHE
from Py4GWCoreLib.ImGui import ImGui
from Py4GWCoreLib.Agent import Agent
from Py4GWCoreLib.Player import Player
from Py4GWCoreLib.enums_src.GameData_enums import Range
from Py4GWCoreLib.py4gwcorelib_src.Color import Color, ColorPalette
from Py4GWCoreLib.Overlay import Overlay
from Py4GWCoreLib.IniManager import IniManager


ini_file_path = "HeroAI"
ini_filename = "FollowModule.ini"
INI_KEY = ""

FORMATIONS_SECTION = "Formations"
EDITOR_SECTION = "Editor"
FORMATION_SECTION_PREFIX = "Formation:"
DEFAULT_FORMATION_NAME = "Default"
GRID_STEP_WORLD = Range.Touch.value / 2
MAX_FOLLOW_POINTS = 11


class RingConfig:
    def __init__(self, radius: Range | float, color: Color, thickness, show=True):
        if isinstance(radius, Range):
            name = radius.name
        else:
            name = f"{radius:.1f}"

        self.caption = name
        self.show = show
        self.radius = radius.value if isinstance(radius, Range) else radius
        self.color: Color = color
        self.thickness = thickness


class FollowerPoint:
    def __init__(self, x: float, y: float, color: Color):
        self.x = float(x)
        self.y = float(y)
        self.color = color

    def copy(self) -> "FollowerPoint":
        return FollowerPoint(self.x, self.y, self.color.copy())


class FollowSettings:
    def __init__(self):
        self.scale = 0.5
        self.draw_area_rings = True
        self.area_rings = [
            RingConfig(Range.Touch.value / 2, ColorPalette.GetColor("gw_green"), 2),
            RingConfig(Range.Touch, ColorPalette.GetColor("gw_assassin"), 2, False),
            RingConfig(Range.Adjacent, ColorPalette.GetColor("gw_blue"), 2),
            RingConfig(Range.Nearby, ColorPalette.GetColor("blue"), 2),
            RingConfig(Range.Area, ColorPalette.GetColor("firebrick"), 2),
            RingConfig(Range.Earshot, ColorPalette.GetColor("gw_purple"), 2, False),
            RingConfig(Range.Spellcast, ColorPalette.GetColor("gold"), 2, False),
        ]

        self.draw_3d_area_rings = True
        self.show_canvas = True
        self.canvas_size: tuple[int, int] = (500, 500)
        self.follower_points: list[FollowerPoint] = []

        self.formation_names: list[str] = []
        self.selected_formation_index = 0
        self.formation_name_input = DEFAULT_FORMATION_NAME
        self.point_default_color = ColorPalette.GetColor("white")
        self.selected_point_index = -1
        self.dragging_point_index = -1
        self.canvas_click_add = True
        self.canvas_drag_edit = True
        self.canvas_snap_to_grid = True
        self.auto_apply_to_shared_memory = True
        self.clear_unassigned_follow_positions = True
        self.show_party_preview = True
        self.last_status = ""
        self.loaded_from_ini = False
        self.points_dirty = False
        self.shared_mem_dirty = False


follow_settings = FollowSettings()


def _clone_points(points: list[FollowerPoint]) -> list[FollowerPoint]:
    return [pt.copy() for pt in points]


def _safe_formation_name(name: str) -> str:
    cleaned = "".join(ch for ch in (name or "").strip() if ch not in "[]\r\n\t")
    return cleaned or DEFAULT_FORMATION_NAME


def _formation_section(name: str) -> str:
    return f"{FORMATION_SECTION_PREFIX}{_safe_formation_name(name)}"


def _mark_dirty() -> None:
    follow_settings.points_dirty = True
    follow_settings.shared_mem_dirty = True


def _current_formation_name() -> str:
    if not follow_settings.formation_names:
        return DEFAULT_FORMATION_NAME
    idx = max(0, min(follow_settings.selected_formation_index, len(follow_settings.formation_names) - 1))
    return follow_settings.formation_names[idx]


def _set_selected_formation_by_name(name: str) -> None:
    safe = _safe_formation_name(name)
    for i, existing in enumerate(follow_settings.formation_names):
        if existing == safe:
            follow_settings.selected_formation_index = i
            follow_settings.formation_name_input = safe
            return


def _color_to_ini_value(color: Color) -> str:
    r, g, b, a = color.to_tuple()
    return f"{r},{g},{b},{a}"


def _color_from_ini_value(value: str, default: Color | None = None) -> Color:
    if default is None:
        default = ColorPalette.GetColor("white")
    try:
        parts = [int(p.strip()) for p in str(value).split(",")]
        if len(parts) != 4:
            return default.copy()
        return Color(parts[0], parts[1], parts[2], parts[3])
    except Exception:
        return default.copy()


def _point_from_canvas(center_x: float, center_y: float, mouse_x: float, mouse_y: float) -> tuple[float, float]:
    local_x = mouse_x - center_x
    local_y = mouse_y - center_y
    world_x = -(local_x / max(follow_settings.scale, 0.01))
    world_y = (local_y / max(follow_settings.scale, 0.01))

    if follow_settings.canvas_snap_to_grid:
        world_x = round(world_x / GRID_STEP_WORLD) * GRID_STEP_WORLD
        world_y = round(world_y / GRID_STEP_WORLD) * GRID_STEP_WORLD

    return world_x, world_y


def _point_to_canvas(center_x: float, center_y: float, pt: FollowerPoint) -> tuple[float, float]:
    draw_x = center_x + (-pt.x * follow_settings.scale)
    draw_y = center_y + (pt.y * follow_settings.scale)
    return draw_x, draw_y


def _find_point_under_mouse(center_x: float, center_y: float, mouse_x: float, mouse_y: float) -> int:
    if not follow_settings.follower_points:
        return -1

    touch_radius = (Range.Touch.value / 2) * follow_settings.scale
    pick_radius_sq = max(10.0, touch_radius * 1.25) ** 2

    best_idx = -1
    best_dist_sq = pick_radius_sq
    for i, pt in enumerate(follow_settings.follower_points):
        px, py = _point_to_canvas(center_x, center_y, pt)
        dx = mouse_x - px
        dy = mouse_y - py
        dist_sq = (dx * dx) + (dy * dy)
        if dist_sq <= best_dist_sq:
            best_idx = i
            best_dist_sq = dist_sq
    return best_idx


def _save_editor_settings() -> None:
    if not INI_KEY:
        return
    im = IniManager()
    im.write_key(INI_KEY, EDITOR_SECTION, "show_canvas", int(follow_settings.show_canvas))
    im.write_key(INI_KEY, EDITOR_SECTION, "canvas_width", int(follow_settings.canvas_size[0]))
    im.write_key(INI_KEY, EDITOR_SECTION, "canvas_height", int(follow_settings.canvas_size[1]))
    im.write_key(INI_KEY, EDITOR_SECTION, "scale", float(follow_settings.scale))
    im.write_key(INI_KEY, EDITOR_SECTION, "draw_area_rings", int(follow_settings.draw_area_rings))
    im.write_key(INI_KEY, EDITOR_SECTION, "draw_3d_area_rings", int(follow_settings.draw_3d_area_rings))
    im.write_key(INI_KEY, EDITOR_SECTION, "canvas_click_add", int(follow_settings.canvas_click_add))
    im.write_key(INI_KEY, EDITOR_SECTION, "canvas_drag_edit", int(follow_settings.canvas_drag_edit))
    im.write_key(INI_KEY, EDITOR_SECTION, "canvas_snap_to_grid", int(follow_settings.canvas_snap_to_grid))
    im.write_key(INI_KEY, EDITOR_SECTION, "auto_apply_to_shared_memory", int(follow_settings.auto_apply_to_shared_memory))
    im.write_key(INI_KEY, EDITOR_SECTION, "clear_unassigned_follow_positions", int(follow_settings.clear_unassigned_follow_positions))
    im.write_key(INI_KEY, EDITOR_SECTION, "show_party_preview", int(follow_settings.show_party_preview))
    im.write_key(INI_KEY, FORMATIONS_SECTION, "selected", _current_formation_name())


def _load_editor_settings() -> None:
    if not INI_KEY:
        return
    im = IniManager()
    w = im.read_int(INI_KEY, EDITOR_SECTION, "canvas_width", follow_settings.canvas_size[0])
    h = im.read_int(INI_KEY, EDITOR_SECTION, "canvas_height", follow_settings.canvas_size[1])
    follow_settings.canvas_size = (max(100, w), max(100, h))
    follow_settings.scale = max(0.05, min(2.0, im.read_float(INI_KEY, EDITOR_SECTION, "scale", follow_settings.scale)))
    follow_settings.show_canvas = im.read_bool(INI_KEY, EDITOR_SECTION, "show_canvas", follow_settings.show_canvas)
    follow_settings.draw_area_rings = im.read_bool(INI_KEY, EDITOR_SECTION, "draw_area_rings", follow_settings.draw_area_rings)
    follow_settings.draw_3d_area_rings = im.read_bool(INI_KEY, EDITOR_SECTION, "draw_3d_area_rings", follow_settings.draw_3d_area_rings)
    follow_settings.canvas_click_add = im.read_bool(INI_KEY, EDITOR_SECTION, "canvas_click_add", follow_settings.canvas_click_add)
    follow_settings.canvas_drag_edit = im.read_bool(INI_KEY, EDITOR_SECTION, "canvas_drag_edit", follow_settings.canvas_drag_edit)
    follow_settings.canvas_snap_to_grid = im.read_bool(INI_KEY, EDITOR_SECTION, "canvas_snap_to_grid", follow_settings.canvas_snap_to_grid)
    follow_settings.auto_apply_to_shared_memory = im.read_bool(INI_KEY, EDITOR_SECTION, "auto_apply_to_shared_memory", follow_settings.auto_apply_to_shared_memory)
    follow_settings.clear_unassigned_follow_positions = im.read_bool(
        INI_KEY, EDITOR_SECTION, "clear_unassigned_follow_positions", follow_settings.clear_unassigned_follow_positions
    )
    follow_settings.show_party_preview = im.read_bool(INI_KEY, EDITOR_SECTION, "show_party_preview", follow_settings.show_party_preview)


def _save_formations_index() -> None:
    if not INI_KEY:
        return
    im = IniManager()
    im.write_key(INI_KEY, FORMATIONS_SECTION, "count", len(follow_settings.formation_names))
    for i, name in enumerate(follow_settings.formation_names):
        im.write_key(INI_KEY, FORMATIONS_SECTION, f"name_{i}", name)
    im.write_key(INI_KEY, FORMATIONS_SECTION, "selected", _current_formation_name())


def _load_formations_index() -> list[str]:
    if not INI_KEY:
        return []
    im = IniManager()
    names: list[str] = []
    count = max(0, im.read_int(INI_KEY, FORMATIONS_SECTION, "count", 0))
    for i in range(count):
        name = _safe_formation_name(im.read_key(INI_KEY, FORMATIONS_SECTION, f"name_{i}", ""))
        if name and name not in names:
            names.append(name)
    return names


def _save_formation(name: str, points: list[FollowerPoint]) -> str:
    if not INI_KEY:
        return ""
    safe = _safe_formation_name(name)
    im = IniManager()
    section = _formation_section(safe)
    im.delete_section(INI_KEY, section)
    im.write_key(INI_KEY, section, "name", safe)
    im.write_key(INI_KEY, section, "count", len(points))
    for i, pt in enumerate(points):
        im.write_key(INI_KEY, section, f"p{i}_x", float(pt.x))
        im.write_key(INI_KEY, section, f"p{i}_y", float(pt.y))
        im.write_key(INI_KEY, section, f"p{i}_color", _color_to_ini_value(pt.color))
    return safe


def _load_formation(name: str) -> list[FollowerPoint]:
    if not INI_KEY:
        return []
    safe = _safe_formation_name(name)
    im = IniManager()
    section = _formation_section(safe)
    count = max(0, im.read_int(INI_KEY, section, "count", 0))
    points: list[FollowerPoint] = []
    for i in range(count):
        x = im.read_float(INI_KEY, section, f"p{i}_x", 0.0)
        y = im.read_float(INI_KEY, section, f"p{i}_y", 0.0)
        c = _color_from_ini_value(im.read_key(INI_KEY, section, f"p{i}_color", "255,255,255,255"))
        points.append(FollowerPoint(x, y, c))
    return points


def _delete_formation(name: str) -> None:
    if not INI_KEY:
        return
    IniManager().delete_section(INI_KEY, _formation_section(name))


def _save_current_formation() -> None:
    name = _safe_formation_name(follow_settings.formation_name_input or _current_formation_name())
    current_name = _current_formation_name()

    if not follow_settings.formation_names:
        follow_settings.formation_names = [name]
        follow_settings.selected_formation_index = 0
    elif name != current_name:
        follow_settings.formation_names[follow_settings.selected_formation_index] = name

    saved_name = _save_formation(name, follow_settings.follower_points)
    follow_settings.formation_name_input = saved_name
    _save_formations_index()
    _save_editor_settings()
    follow_settings.points_dirty = False
    follow_settings.shared_mem_dirty = False
    follow_settings.last_status = f"Saved formation '{saved_name}' ({len(follow_settings.follower_points)} points)."


def _load_selected_formation_into_editor() -> None:
    if not follow_settings.formation_names:
        follow_settings.follower_points = []
        follow_settings.formation_name_input = DEFAULT_FORMATION_NAME
        follow_settings.selected_point_index = -1
        follow_settings.points_dirty = False
        follow_settings.shared_mem_dirty = False
        return

    name = _current_formation_name()
    follow_settings.follower_points = _clone_points(_load_formation(name))
    follow_settings.formation_name_input = name
    if not follow_settings.follower_points:
        follow_settings.selected_point_index = -1
    else:
        follow_settings.selected_point_index = min(
            max(follow_settings.selected_point_index, 0),
            len(follow_settings.follower_points) - 1,
        )
    follow_settings.points_dirty = False
    follow_settings.shared_mem_dirty = False
    follow_settings.last_status = f"Loaded formation '{name}'."


def _create_new_formation(copy_current: bool) -> None:
    base = _safe_formation_name(follow_settings.formation_name_input or "Formation")
    if base in ("", DEFAULT_FORMATION_NAME):
        base = "Formation"
    candidate = base
    n = 1
    existing = set(follow_settings.formation_names)
    while candidate in existing:
        n += 1
        candidate = f"{base} {n}"

    follow_settings.formation_names.append(candidate)
    follow_settings.selected_formation_index = len(follow_settings.formation_names) - 1
    follow_settings.formation_name_input = candidate
    follow_settings.follower_points = _clone_points(follow_settings.follower_points) if copy_current else []
    follow_settings.selected_point_index = -1
    follow_settings.points_dirty = True
    follow_settings.shared_mem_dirty = True
    _save_formations_index()
    _save_editor_settings()
    follow_settings.last_status = f"Created formation '{candidate}'."


def _delete_selected_formation() -> None:
    if not follow_settings.formation_names:
        return

    name = _current_formation_name()
    _delete_formation(name)
    follow_settings.formation_names.pop(follow_settings.selected_formation_index)

    if not follow_settings.formation_names:
        follow_settings.formation_names = [DEFAULT_FORMATION_NAME]
        follow_settings.selected_formation_index = 0
        follow_settings.formation_name_input = DEFAULT_FORMATION_NAME
        follow_settings.follower_points = []
        _save_formation(DEFAULT_FORMATION_NAME, follow_settings.follower_points)
    else:
        follow_settings.selected_formation_index = min(
            follow_settings.selected_formation_index, len(follow_settings.formation_names) - 1
        )
        follow_settings.formation_name_input = _current_formation_name()
        _load_selected_formation_into_editor()

    _save_formations_index()
    _save_editor_settings()
    follow_settings.last_status = f"Deleted formation '{name}'."


def _load_formations_from_ini() -> None:
    follow_settings.formation_names = _load_formations_index()
    if not follow_settings.formation_names:
        follow_settings.formation_names = [DEFAULT_FORMATION_NAME]
        follow_settings.selected_formation_index = 0
        follow_settings.formation_name_input = DEFAULT_FORMATION_NAME
        follow_settings.follower_points = []
        _save_formation(DEFAULT_FORMATION_NAME, [])
        _save_formations_index()
    else:
        selected_name = _safe_formation_name(IniManager().read_key(INI_KEY, FORMATIONS_SECTION, "selected", ""))
        if selected_name:
            _set_selected_formation_by_name(selected_name)
        else:
            follow_settings.selected_formation_index = 0
            follow_settings.formation_name_input = _current_formation_name()
        _load_selected_formation_into_editor()

    _load_editor_settings()
    follow_settings.loaded_from_ini = True


def _get_party_follow_targets() -> list[tuple[int, str, object]]:
    rows: list[tuple[int, str, object]] = []
    try:
        pairs = GLOBAL_CACHE.ShMem.GetAllActiveAccountHeroAIPairs(sort_results=False)
    except Exception:
        return rows

    for account, options in pairs:
        try:
            party_position = int(account.AgentPartyData.PartyPosition)
        except Exception:
            continue
        if party_position <= 0:
            continue
        try:
            name = account.AgentData.CharacterName or account.AccountEmail or f"Party {party_position}"
        except Exception:
            name = f"Party {party_position}"
        rows.append((party_position, str(name), options))
    rows.sort(key=lambda x: x[0])
    return rows


def _apply_to_shared_memory() -> None:
    return
    try:
        rows = _get_party_follow_targets()
        assigned = 0
        cleared = 0
        for party_position, _name, options in rows:
            idx = party_position - 1
            if 0 <= idx < len(follow_settings.follower_points):
                pt = follow_settings.follower_points[idx]
                options.FollowPos.x = float(pt.x)
                options.FollowPos.y = float(pt.y)
                assigned += 1
            elif follow_settings.clear_unassigned_follow_positions:
                options.FollowPos.x = 0.0
                options.FollowPos.y = 0.0
                cleared += 1

        follow_settings.shared_mem_dirty = False
        follow_settings.last_status = f"Applied formation to shared memory ({assigned} assigned, {cleared} cleared)."
    except Exception as e:
        follow_settings.last_status = f"Shared memory apply failed: {e}"


def _handle_canvas_point_editing(canvas_pos: tuple[float, float], center_x: float, center_y: float) -> None:
    if not follow_settings.show_canvas:
        return

    io = PyImGui.get_io()
    mouse_x = io.mouse_pos_x
    mouse_y = io.mouse_pos_y
    canvas_x, canvas_y = canvas_pos
    canvas_w, canvas_h = follow_settings.canvas_size

    inside_canvas = canvas_x <= mouse_x <= (canvas_x + canvas_w) and canvas_y <= mouse_y <= (canvas_y + canvas_h)
    if not inside_canvas or not PyImGui.is_window_hovered():
        if PyImGui.is_mouse_released(0):
            follow_settings.dragging_point_index = -1
        return

    if follow_settings.dragging_point_index != -1:
        if PyImGui.is_mouse_down(0):
            wx, wy = _point_from_canvas(center_x, center_y, mouse_x, mouse_y)
            pt = follow_settings.follower_points[follow_settings.dragging_point_index]
            pt.x = wx
            pt.y = wy
            follow_settings.selected_point_index = follow_settings.dragging_point_index
            _mark_dirty()
            return
        if PyImGui.is_mouse_released(0):
            follow_settings.dragging_point_index = -1
            return

    if PyImGui.is_mouse_clicked(1):
        hit_index = _find_point_under_mouse(center_x, center_y, mouse_x, mouse_y)
        if hit_index != -1:
            follow_settings.follower_points.pop(hit_index)
            if follow_settings.selected_point_index >= len(follow_settings.follower_points):
                follow_settings.selected_point_index = len(follow_settings.follower_points) - 1
            _mark_dirty()
            return

    if PyImGui.is_mouse_clicked(0):
        hit_index = _find_point_under_mouse(center_x, center_y, mouse_x, mouse_y)
        if hit_index != -1 and follow_settings.canvas_drag_edit:
            follow_settings.selected_point_index = hit_index
            follow_settings.dragging_point_index = hit_index
            return

        if follow_settings.canvas_click_add and len(follow_settings.follower_points) < MAX_FOLLOW_POINTS:
            wx, wy = _point_from_canvas(center_x, center_y, mouse_x, mouse_y)
            follow_settings.follower_points.append(FollowerPoint(wx, wy, follow_settings.point_default_color.copy()))
            follow_settings.selected_point_index = len(follow_settings.follower_points) - 1
            _mark_dirty()


def _draw_formations_panel() -> None:
    if not PyImGui.collapsing_header("Formations", PyImGui.TreeNodeFlags.DefaultOpen):
        return

    names = follow_settings.formation_names or [DEFAULT_FORMATION_NAME]
    selected_before = follow_settings.selected_formation_index
    follow_settings.selected_formation_index = PyImGui.combo("Formation", follow_settings.selected_formation_index, names)
    follow_settings.selected_formation_index = max(0, min(follow_settings.selected_formation_index, len(names) - 1))
    if follow_settings.selected_formation_index != selected_before:
        follow_settings.formation_name_input = _current_formation_name()
        _load_selected_formation_into_editor()
        _save_editor_settings()

    follow_settings.formation_name_input = _safe_formation_name(
        PyImGui.input_text("Name", follow_settings.formation_name_input)
    )

    if PyImGui.button("Load Selected"):
        _load_selected_formation_into_editor()
    PyImGui.same_line(0, 6)
    if PyImGui.button("Save Current"):
        _save_current_formation()
    PyImGui.same_line(0, 6)
    if PyImGui.button("Apply To HeroAI"):
        _apply_to_shared_memory()

    if PyImGui.button("New Empty"):
        _create_new_formation(copy_current=False)
    PyImGui.same_line(0, 6)
    if PyImGui.button("Duplicate"):
        _create_new_formation(copy_current=True)
    PyImGui.same_line(0, 6)
    if PyImGui.button("Delete Selected"):
        _delete_selected_formation()

    follow_settings.auto_apply_to_shared_memory = PyImGui.checkbox(
        "Auto Apply To Shared Memory", follow_settings.auto_apply_to_shared_memory
    )
    follow_settings.clear_unassigned_follow_positions = PyImGui.checkbox(
        "Clear Unassigned Follower Slots", follow_settings.clear_unassigned_follow_positions
    )

    if follow_settings.last_status:
        PyImGui.separator()
        PyImGui.text_wrapped(follow_settings.last_status)


def _draw_canvas(center_x: float, center_y: float, canvas_pos: tuple[float, float]) -> None:
    touch_color = follow_settings.area_rings[0].color.copy()
    touch_color.set_a(100)
    touch_radius = follow_settings.area_rings[0].radius * follow_settings.scale

    grid_color = ColorPalette.GetColor("gray").copy()
    grid_color.set_a(80)
    grid_step = GRID_STEP_WORLD * follow_settings.scale

    canvas_x, canvas_y = canvas_pos
    canvas_w, canvas_h = follow_settings.canvas_size
    left = canvas_x
    right = canvas_x + canvas_w
    top = canvas_y
    bottom = canvas_y + canvas_h

    x = center_x
    while x <= right:
        PyImGui.draw_list_add_line(x, top, x, bottom, grid_color.to_color(), 1)
        x += grid_step
    x = center_x - grid_step
    while x >= left:
        PyImGui.draw_list_add_line(x, top, x, bottom, grid_color.to_color(), 1)
        x -= grid_step

    y = center_y
    while y <= bottom:
        PyImGui.draw_list_add_line(left, y, right, y, grid_color.to_color(), 1)
        y += grid_step
    y = center_y - grid_step
    while y >= top:
        PyImGui.draw_list_add_line(left, y, right, y, grid_color.to_color(), 1)
        y -= grid_step

    PyImGui.draw_list_add_circle_filled(center_x, center_y, touch_radius, touch_color.to_color(), 64)

    if follow_settings.draw_area_rings:
        for ring in follow_settings.area_rings:
            if ring.show:
                PyImGui.draw_list_add_circle(center_x, center_y, ring.radius * follow_settings.scale, ring.color.to_color(), 32, ring.thickness)

    point_radius = (Range.Touch.value / 2) * follow_settings.scale
    for i, pt in enumerate(follow_settings.follower_points):
        draw_x, draw_y = _point_to_canvas(center_x, center_y, pt)
        fill_color = pt.color.copy()
        fill_color.set_a(120)
        if i == follow_settings.selected_point_index:
            fill_color = fill_color.shift(ColorPalette.GetColor("gold"), 0.35)

        PyImGui.draw_list_add_circle_filled(draw_x, draw_y, point_radius, fill_color.to_color(), 32)
        PyImGui.draw_list_add_circle(draw_x, draw_y, point_radius, pt.color.to_color(), 32, 3 if i == follow_settings.selected_point_index else 2)
        PyImGui.draw_list_add_text(draw_x - 4, draw_y - 6, ColorPalette.GetColor("white").to_color(), str(i + 1))

    _handle_canvas_point_editing(canvas_pos, center_x, center_y)


def _draw_canvas_settings() -> None:
    if not PyImGui.collapsing_header("Canvas", PyImGui.TreeNodeFlags.DefaultOpen):
        return

    follow_settings.show_canvas = PyImGui.checkbox("Show Canvas", follow_settings.show_canvas)
    changed_w = PyImGui.input_int("Width", follow_settings.canvas_size[0])
    changed_h = PyImGui.input_int("Height", follow_settings.canvas_size[1])
    follow_settings.canvas_size = (max(100, changed_w), max(100, changed_h))

    PyImGui.separator()
    follow_settings.scale = PyImGui.slider_float("Scale", follow_settings.scale, 0.1, 1.5)
    follow_settings.draw_3d_area_rings = PyImGui.checkbox("Draw 3D Area Rings", follow_settings.draw_3d_area_rings)
    follow_settings.draw_area_rings = PyImGui.checkbox("Draw Area Rings", follow_settings.draw_area_rings)
    follow_settings.canvas_click_add = PyImGui.checkbox("Canvas Click Adds Points", follow_settings.canvas_click_add)
    follow_settings.canvas_drag_edit = PyImGui.checkbox("Canvas Drag Edits Points", follow_settings.canvas_drag_edit)
    follow_settings.canvas_snap_to_grid = PyImGui.checkbox("Snap Points To Grid", follow_settings.canvas_snap_to_grid)
    PyImGui.text_wrapped("Canvas controls: left-click empty space to add, drag point to move, right-click point to delete.")


def _draw_area_rings_settings() -> None:
    if not follow_settings.draw_area_rings:
        return
    if not PyImGui.collapsing_header("Area Rings", PyImGui.TreeNodeFlags.DefaultOpen):
        return

    ring_table_flags = PyImGui.TableFlags.Borders | PyImGui.TableFlags.RowBg | PyImGui.TableFlags.SizingStretchProp
    if not PyImGui.begin_table("AreaRingsTable", 5, ring_table_flags):
        return

    PyImGui.table_setup_column("Show", PyImGui.TableColumnFlags.WidthFixed, 80)
    PyImGui.table_setup_column("Radius", PyImGui.TableColumnFlags.WidthFixed, 70)
    PyImGui.table_setup_column("Thickness", PyImGui.TableColumnFlags.WidthFixed, 60)
    PyImGui.table_setup_column("Color", PyImGui.TableColumnFlags.WidthStretch)
    PyImGui.table_setup_column("Name", PyImGui.TableColumnFlags.WidthFixed, 90)
    PyImGui.table_headers_row()

    for i, ring in enumerate(follow_settings.area_rings):
        PyImGui.table_next_row()
        PyImGui.table_next_column()
        ring.show = PyImGui.checkbox(f"##ShowRing{i}", ring.show)
        PyImGui.table_next_column()
        ring.radius = max(1.0, PyImGui.input_float(f"##Radius{i}", ring.radius))
        PyImGui.table_next_column()
        ring.thickness = max(1, PyImGui.input_int(f"##Thickness{i}", int(ring.thickness)))
        PyImGui.table_next_column()

        old_color = ring.color.to_tuple_normalized()
        flags = (
            PyImGui.ColorEditFlags.NoInputs
            | PyImGui.ColorEditFlags.NoTooltip
            | PyImGui.ColorEditFlags.NoLabel
            | PyImGui.ColorEditFlags.NoDragDrop
            | PyImGui.ColorEditFlags.AlphaPreview
        )
        new_color_vec = PyImGui.color_edit4(f"##Color{i}", old_color, PyImGui.ColorEditFlags(flags))
        if new_color_vec != old_color:
            ring.color = Color.from_tuple_normalized(new_color_vec)

        PyImGui.table_next_column()
        PyImGui.text(ring.caption)

    PyImGui.end_table()


def _draw_follower_points_settings() -> None:
    if not PyImGui.collapsing_header("Follower Points", PyImGui.TreeNodeFlags.DefaultOpen):
        return

    PyImGui.text(f"Points in formation: {len(follow_settings.follower_points)} / {MAX_FOLLOW_POINTS}")
    if PyImGui.button("Add Point") and len(follow_settings.follower_points) < MAX_FOLLOW_POINTS:
        follow_settings.follower_points.append(FollowerPoint(0.0, 0.0, follow_settings.point_default_color.copy()))
        follow_settings.selected_point_index = len(follow_settings.follower_points) - 1
        _mark_dirty()
    PyImGui.same_line(0, 6)
    if PyImGui.button("Clear All"):
        follow_settings.follower_points.clear()
        follow_settings.selected_point_index = -1
        _mark_dirty()

    old_default = follow_settings.point_default_color.to_tuple_normalized()
    new_default = PyImGui.color_edit4("Default Point Color", old_default)
    if new_default != old_default:
        follow_settings.point_default_color = Color.from_tuple_normalized(new_default)

    table_flags = PyImGui.TableFlags.Borders | PyImGui.TableFlags.RowBg | PyImGui.TableFlags.SizingStretchProp
    if not PyImGui.begin_table("FollowerPointsTable", 7, table_flags):
        return

    PyImGui.table_setup_column("#", PyImGui.TableColumnFlags.WidthFixed, 30)
    PyImGui.table_setup_column("X", PyImGui.TableColumnFlags.WidthFixed, 90)
    PyImGui.table_setup_column("Y", PyImGui.TableColumnFlags.WidthFixed, 90)
    PyImGui.table_setup_column("Color", PyImGui.TableColumnFlags.WidthStretch)
    PyImGui.table_setup_column("Pick", PyImGui.TableColumnFlags.WidthFixed, 50)
    PyImGui.table_setup_column("Move", PyImGui.TableColumnFlags.WidthFixed, 85)
    PyImGui.table_setup_column("Delete", PyImGui.TableColumnFlags.WidthFixed, 70)
    PyImGui.table_headers_row()

    remove_index = -1
    move_up_index = -1
    move_down_index = -1

    for i, pt in enumerate(follow_settings.follower_points):
        PyImGui.table_next_row()

        PyImGui.table_next_column()
        if PyImGui.selectable(f"{i + 1}", i == follow_settings.selected_point_index):
            follow_settings.selected_point_index = i

        PyImGui.table_next_column()
        edit_x = -pt.x
        new_edit_x = PyImGui.slider_float(f"##FP_X{i}", edit_x, -Range.Earshot.value / 2, Range.Earshot.value / 2)
        if new_edit_x != edit_x:
            pt.x = -new_edit_x
            _mark_dirty()

        PyImGui.table_next_column()
        new_y = PyImGui.slider_float(f"##FP_Y{i}", pt.y, -Range.Earshot.value / 2, Range.Earshot.value / 2)
        if new_y != pt.y:
            pt.y = new_y
            _mark_dirty()

        PyImGui.table_next_column()
        old_color = pt.color.to_tuple_normalized()
        flags = (
            PyImGui.ColorEditFlags.NoInputs
            | PyImGui.ColorEditFlags.NoTooltip
            | PyImGui.ColorEditFlags.NoLabel
            | PyImGui.ColorEditFlags.AlphaPreview
        )
        new_color = PyImGui.color_edit4(f"##FP_Color{i}", old_color, PyImGui.ColorEditFlags(flags))
        if new_color != old_color:
            pt.color = Color.from_tuple_normalized(new_color)
            _mark_dirty()

        PyImGui.table_next_column()
        if PyImGui.button(f"Sel##FP{i}"):
            follow_settings.selected_point_index = i

        PyImGui.table_next_column()
        if PyImGui.button(f"Up##FP{i}") and i > 0:
            move_up_index = i
        PyImGui.same_line(0, 3)
        if PyImGui.button(f"Dn##FP{i}") and i < len(follow_settings.follower_points) - 1:
            move_down_index = i

        PyImGui.table_next_column()
        if PyImGui.button(f"Delete##FP{i}"):
            remove_index = i

    if move_up_index != -1:
        pts = follow_settings.follower_points
        pts[move_up_index - 1], pts[move_up_index] = pts[move_up_index], pts[move_up_index - 1]
        follow_settings.selected_point_index = move_up_index - 1
        _mark_dirty()
    if move_down_index != -1:
        pts = follow_settings.follower_points
        pts[move_down_index + 1], pts[move_down_index] = pts[move_down_index], pts[move_down_index + 1]
        follow_settings.selected_point_index = move_down_index + 1
        _mark_dirty()
    if remove_index != -1:
        follow_settings.follower_points.pop(remove_index)
        if follow_settings.selected_point_index >= len(follow_settings.follower_points):
            follow_settings.selected_point_index = len(follow_settings.follower_points) - 1
        _mark_dirty()

    PyImGui.end_table()


def _draw_party_preview() -> None:
    follow_settings.show_party_preview = PyImGui.checkbox("Show Party Slot Preview", follow_settings.show_party_preview)
    if not follow_settings.show_party_preview:
        return
    if not PyImGui.collapsing_header("Party / Shared Memory Preview", PyImGui.TreeNodeFlags.DefaultOpen):
        return

    rows = _get_party_follow_targets()
    if not rows:
        PyImGui.text("No active follower accounts found in shared memory.")
        return

    if not PyImGui.begin_table("FollowPartyPreview", 5, PyImGui.TableFlags.Borders | PyImGui.TableFlags.RowBg):
        return

    PyImGui.table_setup_column("Party", PyImGui.TableColumnFlags.WidthFixed, 45)
    PyImGui.table_setup_column("Follower", PyImGui.TableColumnFlags.WidthStretch)
    PyImGui.table_setup_column("Assigned", PyImGui.TableColumnFlags.WidthFixed, 80)
    PyImGui.table_setup_column("Shared X", PyImGui.TableColumnFlags.WidthFixed, 80)
    PyImGui.table_setup_column("Shared Y", PyImGui.TableColumnFlags.WidthFixed, 80)
    PyImGui.table_headers_row()

    for party_position, name, options in rows:
        idx = party_position - 1
        assigned = f"#{idx + 1}" if idx < len(follow_settings.follower_points) else "-"

        PyImGui.table_next_row()
        PyImGui.table_next_column()
        PyImGui.text(str(party_position))
        PyImGui.table_next_column()
        PyImGui.text(name)
        PyImGui.table_next_column()
        PyImGui.text(assigned)
        PyImGui.table_next_column()
        PyImGui.text(f"options.FollowPos.x:.1f")
        PyImGui.table_next_column()
        PyImGui.text(f"options.FollowPos.y:.1f")

    PyImGui.end_table()


def _draw_3d_overlay() -> None:
    Overlay().BeginDraw()
    if follow_settings.draw_3d_area_rings:
        grid_color = ColorPalette.GetColor("gray").copy()
        grid_color.set_a(120)
        grid_step = GRID_STEP_WORLD
        grid_extent = Range.Spellcast.value
        player_x, player_y, player_z = Agent.GetXYZ(Player.GetAgentID())
        origin_x = round(player_x / grid_step) * grid_step
        origin_y = round(player_y / grid_step) * grid_step

        y = origin_y - grid_extent
        while y <= origin_y + grid_extent:
            Overlay().DrawLine3D(origin_x - grid_extent, y, player_z, origin_x + grid_extent, y, player_z, grid_color.to_color(), 1)
            y += grid_step
        x = origin_x - grid_extent
        while x <= origin_x + grid_extent:
            Overlay().DrawLine3D(x, origin_y - grid_extent, player_z, x, origin_y + grid_extent, player_z, grid_color.to_color(), 1)
            x += grid_step

    player_x, player_y, player_z = Agent.GetXYZ(Player.GetAgentID())
    for ring in follow_settings.area_rings:
        if ring.show and follow_settings.draw_3d_area_rings:
            Overlay().DrawPoly3D(player_x, player_y, player_z, ring.radius, ring.color.to_color(), 64, ring.thickness * 2)

    player_id = Player.GetAgentID()
    player_x, player_y, player_z = Agent.GetXYZ(player_id)
    angle = Agent.GetRotationAngle(player_id) - math.pi / 2
    rotation_angle_cos = -math.cos(angle)
    rotation_angle_sin = -math.sin(angle)
    radius = Range.Touch.value / 2

    for pt in follow_settings.follower_points:
        rot_x = (pt.x * rotation_angle_cos) - (pt.y * rotation_angle_sin)
        rot_y = (pt.x * rotation_angle_sin) + (pt.y * rotation_angle_cos)
        Overlay().DrawPoly3D(player_x + rot_x, player_y + rot_y, player_z, radius, pt.color.to_color(), 32, 2)

    Overlay().EndDraw()


def main():
    global INI_KEY

    if not INI_KEY:
        INI_KEY = IniManager().ensure_key(ini_file_path, ini_filename)
        if not INI_KEY:
            return

    if not follow_settings.loaded_from_ini:
        _load_formations_from_ini()

    canvas_w, canvas_h = follow_settings.canvas_size
    settings_width = 480
    window_w = (canvas_w + settings_width) if follow_settings.show_canvas else settings_width
    window_h = max(500, canvas_h + 80)
    PyImGui.set_next_window_size((window_w, window_h), PyImGui.ImGuiCond.Always)

    if ImGui.Begin(ini_key=INI_KEY, name="Following Module", flags=PyImGui.WindowFlags.NoFlag):
        table_flags = PyImGui.TableFlags.Borders | PyImGui.TableFlags.SizingStretchProp
        column_count = 2 if follow_settings.show_canvas else 1

        if PyImGui.begin_table("FollowSettingsMainTable", column_count, table_flags):
            if follow_settings.show_canvas:
                PyImGui.table_setup_column("Canvas", PyImGui.TableColumnFlags.WidthFixed, follow_settings.canvas_size[0] + 20)
            PyImGui.table_setup_column("Settings", PyImGui.TableColumnFlags.WidthStretch)

            PyImGui.table_next_row()

            if follow_settings.show_canvas:
                PyImGui.table_next_column()
                child_flags = PyImGui.WindowFlags.NoTitleBar | PyImGui.WindowFlags.NoResize | PyImGui.WindowFlags.NoMove
                if PyImGui.begin_child("FollowSettingsChild", follow_settings.canvas_size, True, child_flags):
                    canvas_pos = PyImGui.get_cursor_screen_pos()
                    center_x = canvas_pos[0] + follow_settings.canvas_size[0] / 2
                    center_y = canvas_pos[1] + follow_settings.canvas_size[1] / 2
                    _draw_canvas(center_x, center_y, canvas_pos)
                    PyImGui.end_child()
                PyImGui.table_next_column()
            else:
                PyImGui.table_next_column()

            _draw_formations_panel()
            PyImGui.separator()
            _draw_canvas_settings()
            _draw_area_rings_settings()
            _draw_follower_points_settings()
            _draw_party_preview()

            PyImGui.end_table()

        if follow_settings.auto_apply_to_shared_memory and follow_settings.shared_mem_dirty:
            _apply_to_shared_memory()

        _save_editor_settings()
        if follow_settings.formation_names and not follow_settings.points_dirty:
            _save_formations_index()

        _draw_3d_overlay()

    ImGui.End(ini_key=INI_KEY)


if __name__ == "__main__":
    main()
