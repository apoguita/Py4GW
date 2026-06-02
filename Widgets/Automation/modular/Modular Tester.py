"""Run a single modular JSON recipe through the BT-native compiler."""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import PyImGui

from Py4GWCoreLib import Console
from Py4GWCoreLib import ConsoleLog
from Py4GWCoreLib.botting_tree_src.ui import BottingTreeUIMovePathMixin
from Py4GWCoreLib.modular import BTRecipeRunner
from Py4GWCoreLib.modular import RecipeSpec
from Py4GWCoreLib.modular.paths import modular_data_root
from Py4GWCoreLib.modular.widget_runtime import guarded_widget_main


MODULE_NAME = "Modular Tester"
MODULE_ICON = "Textures/Module_Icons/Route Planner.png"
MODULE_TAGS = ["Automation", "modular_bot"]

ACCENT = (0.30, 0.78, 0.86, 1.0)
GOOD = (0.42, 0.88, 0.55, 1.0)
WARN = (1.00, 0.78, 0.32, 1.0)
BAD = (1.00, 0.38, 0.38, 1.0)
MUTED = (0.62, 0.66, 0.70, 1.0)
TEXT = (0.92, 0.94, 0.96, 1.0)
WINDOW_BG = (0.055, 0.070, 0.085, 0.985)
PANEL_BG = (0.080, 0.100, 0.120, 0.965)
PANEL_ALT_BG = (0.105, 0.125, 0.145, 0.965)
BORDER = (0.18, 0.27, 0.31, 0.78)
HEADER_BG = (0.10, 0.34, 0.40, 0.82)
HEADER_HOVER = (0.12, 0.43, 0.50, 0.92)
HEADER_ACTIVE = (0.08, 0.28, 0.34, 0.94)


@dataclass(frozen=True)
class RecipeSummary:
    title: str
    kind: str
    steps: int
    anchors: int
    first_step: str


_recipe_files: list[str] = []
_recipe_tree: dict[str, object] = {"dirs": {}, "files": []}
_recipe_titles: dict[str, str] = {}
_recipe_summaries: dict[str, RecipeSummary] = {}
_selected_recipe = ""
_browser_path: list[str] = []
_filter_text = ""
_runner: BTRecipeRunner | None = None
_status = ""
_last_recipe = ""
_loop = False
_debug_logging = False
_preview_step_index = 0
_start_step_index = 0
_draw_move_path = True
_draw_move_path_labels = False
_draw_move_path_thickness = 4.0
_draw_move_waypoint_radius = 15.0
_draw_move_current_waypoint_radius = 20.0


class _TesterMovePathDrawer(BottingTreeUIMovePathMixin):
    def __init__(self) -> None:
        self.blackboard: dict = {}
        self.draw_move_path_enabled = True
        self.draw_move_path_labels = False
        self.draw_move_path_thickness = 4.0
        self.draw_move_waypoint_radius = 15.0
        self.draw_move_current_waypoint_radius = 20.0
        self.tree = self

    def draw(self) -> None:
        return


_path_drawer = _TesterMovePathDrawer()


def _debug(message: str) -> None:
    if _debug_logging:
        ConsoleLog(MODULE_NAME, message, Console.MessageType.Info)


def _refresh_recipe_files() -> None:
    global _recipe_files, _recipe_tree, _recipe_titles, _recipe_summaries, _selected_recipe, _preview_step_index, _start_step_index
    root = Path(modular_data_root())
    recipes: list[str] = []
    titles: dict[str, str] = {}
    summaries: dict[str, RecipeSummary] = {}
    for path in root.rglob("*.json"):
        rel = path.relative_to(root).as_posix()
        if rel.startswith("tools/") or rel.startswith("prebuilt/"):
            continue
        recipes.append(rel)
        summary = _recipe_summary(rel)
        titles[rel] = summary.title
        summaries[rel] = summary
    _recipe_files = sorted(recipes)
    _recipe_titles = titles
    _recipe_summaries = summaries
    _recipe_tree = _build_recipe_tree(_recipe_files)
    if _selected_recipe not in _recipe_files:
        _selected_recipe = ""
        _preview_step_index = 0
        _start_step_index = 0


def _build_recipe_tree(paths: list[str]) -> dict[str, object]:
    root: dict[str, object] = {"dirs": {}, "files": []}
    for relative_path in paths:
        parts = relative_path.split("/")
        node = root
        for folder in parts[:-1]:
            dirs = node.setdefault("dirs", {})
            if not isinstance(dirs, dict):
                dirs = {}
                node["dirs"] = dirs
            node = dirs.setdefault(folder, {"dirs": {}, "files": []})
        files = node.setdefault("files", [])
        if isinstance(files, list):
            files.append(relative_path)
    return root


def _visible_recipe_files() -> list[str]:
    needle = _filter_text.strip().lower()
    if not needle:
        return list(_recipe_files)
    return [
        path
        for path in _recipe_files
        if needle in path.lower() or needle in (_recipe_titles.get(path) or "").lower()
    ]


def _selected_recipe_path() -> str:
    if _selected_recipe in _recipe_files:
        return _selected_recipe
    return ""


def _browser_node() -> dict[str, object]:
    node = _recipe_tree
    for folder in _browser_path:
        dirs = node.get("dirs", {})
        if not isinstance(dirs, dict):
            return {"dirs": {}, "files": []}
        child = dirs.get(folder)
        if not isinstance(child, dict):
            return {"dirs": {}, "files": []}
        node = child
    return node


def _browser_label() -> str:
    return "/".join(_browser_path) if _browser_path else "modular_data"


def _read_recipe(relative_path: str) -> dict[str, Any]:
    if not relative_path:
        return {}
    path = Path(modular_data_root()) / relative_path
    try:
        recipe = json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception:
        return {}
    return recipe if isinstance(recipe, dict) else {}


def _recipe_summary(relative_path: str) -> RecipeSummary:
    recipe = _read_recipe(relative_path)
    title = str(recipe.get("name") or "").strip()
    if not title:
        title = Path(relative_path).stem.replace("_", " ").title()
    steps = recipe.get("steps", [])
    step_dicts = [step for step in steps if isinstance(step, dict)] if isinstance(steps, list) else []
    first_step = _step_label(step_dicts[0], 0) if step_dicts else "No steps"
    kind = Path(relative_path).parts[0] if Path(relative_path).parts else "recipes"
    anchors = sum(1 for step in step_dicts if bool(step.get("anchor")))
    return RecipeSummary(title=title, kind=kind, steps=len(step_dicts), anchors=anchors, first_step=first_step)


def _recipe_steps_for_display(relative_path: str) -> list[dict[str, object]]:
    recipe = _read_recipe(relative_path)
    steps = recipe.get("steps", [])
    if not isinstance(steps, list):
        return []
    return [step for step in steps if isinstance(step, dict)]


def _step_label(step: dict[str, object], index: int) -> str:
    title = str(step.get("name") or "").strip()
    step_type = str(step.get("type") or "").strip()
    action = str(step.get("action") or step.get("mode") or step.get("target") or "").strip()
    parts = [f"{index + 1:02d}."]
    if title:
        parts.append(title)
    elif step_type:
        parts.append(step_type)
    else:
        parts.append("Step")
    detail = ".".join(part for part in (step_type, action) if part)
    if detail:
        parts.append(f"({detail})")
    if bool(step.get("anchor")):
        parts.append("[anchor]")
    return " ".join(parts)


def _step_type_label(step: dict[str, object]) -> str:
    step_type = str(step.get("type") or "step").strip()
    action = str(step.get("action") or step.get("mode") or "").strip()
    return ".".join(part for part in (step_type, action) if part)


def _points_count(step: dict[str, object]) -> int:
    points = step.get("points")
    if isinstance(points, list):
        return len(points)
    if "x" in step and "y" in step:
        return 1
    return 0


def _coerce_point(value: object) -> tuple[float, float] | None:
    if isinstance(value, (list, tuple)) and len(value) >= 2:
        try:
            return float(value[0]), float(value[1])
        except (TypeError, ValueError):
            return None
    return None


def _step_points(step: dict[str, object]) -> list[tuple[float, float]]:
    points: list[tuple[float, float]] = []
    raw_points = step.get("points")
    if isinstance(raw_points, list):
        for raw_point in raw_points:
            point = _coerce_point(raw_point)
            if point is not None:
                points.append(point)
    point = _coerce_point(step.get("point"))
    if point is not None:
        points.append(point)
    if "x" in step and "y" in step:
        try:
            points.append((float(step["x"]), float(step["y"])))
        except (TypeError, ValueError):
            pass
    return points


def _recipe_route_points(relative_path: str, *, start_step_index: int = 0) -> list[tuple[float, float]]:
    steps = _recipe_steps_for_display(relative_path)
    route_points: list[tuple[float, float]] = []
    for step in steps[max(0, int(start_step_index)) :]:
        if str(step.get("type") or "").strip() != "route":
            continue
        route_points.extend(_step_points(step))
    return route_points


def _path_draw_blackboard() -> dict:
    if _runner is not None:
        blackboard = _runner.get_runtime_blackboard()
        points = blackboard.get("move_path_points")
        if isinstance(points, list) and points:
            state = str(blackboard.get("move_state") or "")
            if state in ("running", "paused") or _runner_is_running() or _runner_is_paused():
                blackboard["move_state"] = "running" if _runner_is_running() else "paused"
                return blackboard

    points = _recipe_route_points(_selected_recipe_path(), start_step_index=_start_step_index)
    if not points:
        return {}
    current_index = min(max(0, _preview_step_index - _start_step_index), len(points) - 1)
    return {
        "move_state": "paused",
        "move_reason": "selected recipe preview",
        "move_target": points[-1],
        "move_path_index": 0,
        "move_path_count": len(points),
        "move_path_points": points,
        "move_current_waypoint": points[current_index],
        "move_current_waypoint_index": current_index,
    }


def _draw_move_path_overlay() -> None:
    if not _draw_move_path:
        return
    blackboard = _path_draw_blackboard()
    if not blackboard:
        return
    _path_drawer.blackboard = blackboard
    _path_drawer.draw_move_path_labels = _draw_move_path_labels
    _path_drawer.draw_move_path_thickness = _draw_move_path_thickness
    _path_drawer.draw_move_waypoint_radius = _draw_move_waypoint_radius
    _path_drawer.draw_move_current_waypoint_radius = _draw_move_current_waypoint_radius
    _path_drawer.DrawMovePathIfEnabled()


def _spec_from_relative_path(relative_path: str) -> RecipeSpec:
    rel = Path(relative_path)
    if len(rel.parts) < 2:
        raise ValueError("Recipe must be inside a modular_data subfolder.")
    kind = rel.parts[0]
    key = Path(*rel.parts[1:]).with_suffix("").as_posix()
    title = _recipe_titles.get(relative_path) or Path(relative_path).stem.replace("_", " ").title()
    return RecipeSpec(kind=kind, key=key, title=title)


def _start_selected_recipe() -> None:
    global _runner, _status, _last_recipe
    relative_path = _selected_recipe_path()
    if not relative_path:
        _status = "No recipe selected."
        return
    try:
        runner = BTRecipeRunner(
            name=f"Modular Tester: {relative_path}",
            specs=[_spec_from_relative_path(relative_path)],
            start_step_index=_start_step_index,
            loop=bool(_loop),
            debug_hook=_debug,
        )
        runner.start()
        _runner = runner
        _last_recipe = relative_path
        _status = f"Started {relative_path}."
    except Exception as exc:
        _runner = None
        _status = f"Start failed: {exc}"


def _stop_runner() -> None:
    global _status
    if _runner is not None:
        _runner.stop()
    _status = "Stopped."


def _pause_runner() -> None:
    global _status
    if _runner is not None:
        _runner.pause()
    _status = "Paused."


def _resume_runner() -> None:
    global _status
    if _runner is not None:
        _runner.resume()
    _status = "Resumed."


def _runner_is_running() -> bool:
    return _runner is not None and bool(_runner.is_running())


def _runner_is_paused() -> bool:
    return _runner is not None and bool(_runner.is_paused())


def _progress_fraction() -> float:
    if _runner is None:
        return 0.0
    step_current, step_total, _recipe_title, _step_title = _runner.get_step_progress()
    if step_total <= 0:
        return 0.0
    return max(0.0, min(1.0, float(step_current) / float(step_total)))


def _kind_counts() -> dict[str, int]:
    counts: dict[str, int] = {}
    for summary in _recipe_summaries.values():
        counts[summary.kind] = counts.get(summary.kind, 0) + 1
    return counts


def _draw_text(label: str, color: tuple[float, float, float, float] = TEXT) -> None:
    PyImGui.text_colored(label, color)


def _draw_label_value(label: str, value: str, color: tuple[float, float, float, float] = TEXT) -> None:
    PyImGui.text_colored(label, MUTED)
    PyImGui.same_line(0, 6)
    PyImGui.text_colored(value, color)


def _draw_button_style(
    base: tuple[float, float, float, float],
    hover: tuple[float, float, float, float],
    active: tuple[float, float, float, float],
) -> None:
    PyImGui.push_style_color(PyImGui.ImGuiCol.Button, base)
    PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonHovered, hover)
    PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonActive, active)


def _pop_button_style() -> None:
    PyImGui.pop_style_color(3)


def _selectable_row(label: str, selected: bool = False) -> bool:
    return PyImGui.selectable(label, selected, int(PyImGui.SelectableFlags.SpanAllColumns), [0.0, 0.0])


def _push_tester_theme() -> int:
    colors = [
        (PyImGui.ImGuiCol.WindowBg, WINDOW_BG),
        (PyImGui.ImGuiCol.ChildBg, PANEL_BG),
        (PyImGui.ImGuiCol.PopupBg, PANEL_BG),
        (PyImGui.ImGuiCol.Border, BORDER),
        (PyImGui.ImGuiCol.FrameBg, PANEL_ALT_BG),
        (PyImGui.ImGuiCol.FrameBgHovered, (0.13, 0.17, 0.19, 1.0)),
        (PyImGui.ImGuiCol.FrameBgActive, (0.15, 0.22, 0.25, 1.0)),
        (PyImGui.ImGuiCol.TitleBg, (0.055, 0.070, 0.085, 1.0)),
        (PyImGui.ImGuiCol.TitleBgActive, (0.080, 0.125, 0.145, 1.0)),
        (PyImGui.ImGuiCol.Header, HEADER_BG),
        (PyImGui.ImGuiCol.HeaderHovered, HEADER_HOVER),
        (PyImGui.ImGuiCol.HeaderActive, HEADER_ACTIVE),
        (PyImGui.ImGuiCol.Separator, BORDER),
        (PyImGui.ImGuiCol.SeparatorHovered, ACCENT),
        (PyImGui.ImGuiCol.SeparatorActive, ACCENT),
        (PyImGui.ImGuiCol.Tab, (0.075, 0.105, 0.125, 1.0)),
        (PyImGui.ImGuiCol.TabHovered, HEADER_HOVER),
        (PyImGui.ImGuiCol.TabActive, (0.10, 0.32, 0.38, 1.0)),
        (PyImGui.ImGuiCol.TabUnfocused, (0.065, 0.080, 0.095, 1.0)),
        (PyImGui.ImGuiCol.TabUnfocusedActive, (0.085, 0.145, 0.165, 1.0)),
        (PyImGui.ImGuiCol.TableHeaderBg, (0.09, 0.13, 0.15, 1.0)),
        (PyImGui.ImGuiCol.TableBorderStrong, BORDER),
        (PyImGui.ImGuiCol.TableBorderLight, (0.13, 0.18, 0.20, 0.70)),
        (PyImGui.ImGuiCol.TableRowBg, (0.08, 0.10, 0.12, 0.68)),
        (PyImGui.ImGuiCol.TableRowBgAlt, (0.10, 0.12, 0.14, 0.72)),
        (PyImGui.ImGuiCol.ScrollbarBg, (0.055, 0.070, 0.085, 0.88)),
        (PyImGui.ImGuiCol.ScrollbarGrab, (0.18, 0.29, 0.33, 0.90)),
        (PyImGui.ImGuiCol.ScrollbarGrabHovered, (0.23, 0.39, 0.45, 1.0)),
        (PyImGui.ImGuiCol.ScrollbarGrabActive, (0.28, 0.54, 0.62, 1.0)),
        (PyImGui.ImGuiCol.CheckMark, ACCENT),
        (PyImGui.ImGuiCol.TextSelectedBg, (0.22, 0.54, 0.62, 0.38)),
    ]
    for color_index, color in colors:
        PyImGui.push_style_color(color_index, color)
    return len(colors)


def _primary_button(label: str, width: float = 0.0) -> bool:
    _draw_button_style((0.10, 0.45, 0.52, 1.0), (0.12, 0.58, 0.66, 1.0), (0.08, 0.36, 0.42, 1.0))
    clicked = PyImGui.button(label, width, 28)
    _pop_button_style()
    return clicked


def _danger_button(label: str, width: float = 0.0) -> bool:
    _draw_button_style((0.56, 0.18, 0.18, 1.0), (0.70, 0.22, 0.22, 1.0), (0.42, 0.12, 0.12, 1.0))
    clicked = PyImGui.button(label, width, 28)
    _pop_button_style()
    return clicked


def _quiet_button(label: str, width: float = 0.0) -> bool:
    _draw_button_style((0.18, 0.21, 0.24, 1.0), (0.24, 0.28, 0.32, 1.0), (0.14, 0.16, 0.18, 1.0))
    clicked = PyImGui.button(label, width, 28)
    _pop_button_style()
    return clicked


def _status_color() -> tuple[float, float, float, float]:
    if _runner_is_running():
        return GOOD
    if _runner_is_paused():
        return WARN
    if _status.lower().startswith("start failed"):
        return BAD
    if _runner is not None:
        return WARN
    return MUTED


def _status_text() -> str:
    if _runner_is_running():
        return "Running"
    if _runner_is_paused():
        return "Paused"
    if _runner is None:
        return "Ready"
    return "Stopped"


def _draw_top_bar() -> None:
    global _loop, _debug_logging, _draw_move_path, _draw_move_path_labels
    PyImGui.begin_group()
    PyImGui.text_scaled("Modular Tester", ACCENT, 1.22)
    PyImGui.text_colored("Browse Sources/modular_data, choose a JSON recipe, pick a start step, run it.", MUTED)
    PyImGui.end_group()
    PyImGui.same_line(max(0.0, PyImGui.get_content_region_avail()[0] - 84.0), 10)
    _draw_text(_status_text(), _status_color())
    PyImGui.separator()
    _loop = PyImGui.checkbox("Loop", _loop)
    PyImGui.same_line(0, 14)
    _debug_logging = PyImGui.checkbox("Debug logging", _debug_logging)
    PyImGui.same_line(0, 14)
    _draw_move_path = PyImGui.checkbox("Draw path", _draw_move_path)
    PyImGui.same_line(0, 14)
    _draw_move_path_labels = PyImGui.checkbox("Path labels", _draw_move_path_labels)


def _draw_recipe_picker() -> None:
    global _filter_text
    if not _recipe_files:
        _refresh_recipe_files()

    _draw_section_title("Recipes", f"{len(_recipe_files)} loaded")
    _draw_selection_controls()
    PyImGui.spacing()
    PyImGui.set_next_item_width(max(120.0, PyImGui.get_content_region_avail()[0] - 82.0))
    _filter_text = PyImGui.input_text("##modular_tester_filter", _filter_text, 128)
    PyImGui.same_line(0, 6)
    if _quiet_button("Refresh", 74):
        _refresh_recipe_files()
    PyImGui.spacing()
    _draw_kind_strip()
    PyImGui.spacing()
    if _filter_text.strip():
        _draw_filtered_recipes()
    else:
        _draw_button_browser()


def _draw_selection_controls() -> None:
    selected = _selected_recipe_path()
    running = _runner_is_running()
    paused = _runner_is_paused()
    can_go_up = bool(_browser_path) and not _filter_text.strip()
    PyImGui.begin_disabled(not can_go_up)
    if _quiet_button("Up", 42):
        _go_up()
    PyImGui.end_disabled()
    PyImGui.same_line(0, 6)
    PyImGui.begin_disabled(not selected or running)
    if _primary_button("Run", 58):
        _start_selected_recipe()
    PyImGui.end_disabled()
    PyImGui.same_line(0, 6)
    PyImGui.begin_disabled(not running)
    if _quiet_button("Pause", 58):
        _pause_runner()
    PyImGui.end_disabled()
    PyImGui.same_line(0, 6)
    PyImGui.begin_disabled(not paused)
    if _primary_button("Resume", 68):
        _resume_runner()
    PyImGui.end_disabled()
    PyImGui.same_line(0, 6)
    PyImGui.begin_disabled(not (running or paused))
    if _danger_button("Stop", 52):
        _stop_runner()
    PyImGui.end_disabled()


def _go_up() -> None:
    global _browser_path
    if _browser_path:
        _browser_path = _browser_path[:-1]


def _draw_kind_strip() -> None:
    global _browser_path, _filter_text
    counts = _kind_counts()
    if not counts:
        PyImGui.text_colored("No recipes found.", MUTED)
        return
    if PyImGui.begin_child("##modular_tester_kind_strip", (0, 118), True, PyImGui.WindowFlags.NoFlag):
        flags = PyImGui.TableFlags.SizingStretchSame | PyImGui.TableFlags.NoSavedSettings
        if PyImGui.begin_table("##modular_tester_kind_table", 2, flags):
            for index, kind in enumerate(sorted(counts)):
                if index % 2 == 0:
                    PyImGui.table_next_row()
                PyImGui.table_set_column_index(index % 2)
                selected = bool(_browser_path and _browser_path[0] == kind)
                label = f"{kind}  {counts[kind]}##kind_{kind}"
                if selected:
                    _draw_button_style(
                        (0.10, 0.45, 0.52, 1.0),
                        (0.12, 0.58, 0.66, 1.0),
                        (0.08, 0.36, 0.42, 1.0),
                    )
                if PyImGui.button(label, max(96.0, PyImGui.get_content_region_avail()[0]), 24):
                    _browser_path = [kind]
                    _filter_text = ""
                if selected:
                    _pop_button_style()
            PyImGui.end_table()
    PyImGui.end_child()


def _draw_filtered_recipes() -> None:
    visible = _visible_recipe_files()
    _draw_section_title("Matches", f"{len(visible)}")
    if PyImGui.begin_child("##modular_tester_matches", (0, 0), True, PyImGui.WindowFlags.HorizontalScrollbar):
        if not visible:
            PyImGui.text_colored("No matching recipes.", MUTED)
        for relative_path in visible:
            _draw_recipe_row(relative_path)
    PyImGui.end_child()


def _draw_button_browser() -> None:
    _draw_breadcrumbs()
    node = _browser_node()
    dirs = node.get("dirs", {})
    files = node.get("files", [])
    if PyImGui.begin_child("##modular_tester_recipe_browser", (0, 0), True, PyImGui.WindowFlags.HorizontalScrollbar):
        drew_any = False
        if isinstance(dirs, dict):
            for folder_name in sorted(str(name) for name in dirs):
                _draw_folder_row(folder_name)
                drew_any = True
        if isinstance(files, list):
            for relative_path in sorted(str(path) for path in files):
                _draw_recipe_row(relative_path)
                drew_any = True
        if not drew_any:
            PyImGui.text_colored("No recipes here.", MUTED)
    PyImGui.end_child()


def _draw_breadcrumbs() -> None:
    global _browser_path
    PyImGui.text_colored("Path", MUTED)
    PyImGui.same_line(0, 8)
    if PyImGui.small_button("modular_data##crumb_root"):
        _browser_path = []
    current: list[str] = []
    for depth, folder in enumerate(_browser_path):
        current.append(folder)
        PyImGui.same_line(0, 4)
        PyImGui.text_colored("/", MUTED)
        PyImGui.same_line(0, 4)
        if PyImGui.small_button(f"{folder}##crumb_{depth}_{'/'.join(current)}"):
            _browser_path = list(current)
    if _browser_path:
        PyImGui.same_line(0, 10)
        if PyImGui.small_button("Up##browser_up"):
            _go_up()


def _draw_folder_row(folder_name: str) -> None:
    global _browser_path
    label = f"> {folder_name}##folder_{_browser_label()}_{folder_name}"
    if _selectable_row(label):
        _browser_path = [*_browser_path, folder_name]
    PyImGui.text_colored(f"  {_browser_label()}/{folder_name}", MUTED)


def _draw_recipe_row(relative_path: str) -> None:
    global _selected_recipe, _preview_step_index, _start_step_index
    summary = _recipe_summaries.get(relative_path) or _recipe_summary(relative_path)
    selected = relative_path == _selected_recipe
    prefix = "* " if selected else "  "
    label = f"{prefix}{summary.title}##recipe_{relative_path}"
    if _selectable_row(label, selected):
        _selected_recipe = relative_path
        _preview_step_index = 0
        _start_step_index = 0
    PyImGui.text_colored(f"  {relative_path}  |  {summary.steps} steps", MUTED)


def _draw_section_title(title: str, meta: str = "") -> None:
    PyImGui.text_colored(title, ACCENT)
    if meta:
        PyImGui.same_line(0, 8)
        PyImGui.text_colored(meta, MUTED)


def _draw_recipe_overview() -> None:
    selected = _selected_recipe_path()
    summary = _recipe_summaries.get(selected)
    if not selected or summary is None:
        PyImGui.text_colored("Select a JSON recipe from Sources/modular_data.", MUTED)
        return

    _draw_section_title(summary.title, summary.kind)
    PyImGui.text_wrapped(selected)
    PyImGui.spacing()
    if PyImGui.begin_table("##modular_tester_metrics", 3, PyImGui.TableFlags.SizingStretchSame | PyImGui.TableFlags.NoSavedSettings):
        PyImGui.table_next_row()
        PyImGui.table_set_column_index(0)
        _draw_metric("Steps", str(summary.steps), ACCENT)
        PyImGui.table_set_column_index(1)
        _draw_metric("Anchors", str(summary.anchors), WARN if summary.anchors else MUTED)
        PyImGui.table_set_column_index(2)
        _draw_metric("Mode", "Loop" if _loop else "Single", GOOD if _loop else TEXT)
        PyImGui.end_table()
    start_label = "1"
    steps = _recipe_steps_for_display(selected)
    if steps:
        start_label = f"{_start_step_index + 1}: {_step_label(steps[min(_start_step_index, len(steps) - 1)], min(_start_step_index, len(steps) - 1))}"
    _draw_label_value("Start at", start_label, ACCENT)
    route_points = _recipe_route_points(selected, start_step_index=_start_step_index)
    _draw_label_value("Path preview", f"{len(route_points)} waypoint(s)", GOOD if route_points else MUTED)
    PyImGui.spacing()


def _draw_metric(label: str, value: str, color: tuple[float, float, float, float]) -> None:
    PyImGui.text_colored(label, MUTED)
    PyImGui.text_scaled(value, color, 1.12)


def _draw_progress_panel() -> None:
    if _runner is None:
        PyImGui.progress_bar(0.0, -1.0, 0.0, "Idle")
        return

    running = _runner_is_running()
    paused = _runner_is_paused()
    phase_current, phase_total, phase_title = _runner.get_phase_progress()
    step_current, step_total, recipe_title, step_title = _runner.get_step_progress()
    metadata = _runner.get_current_step_metadata()
    overlay = f"{step_current}/{step_total}" if step_total > 0 else _status_text()
    PyImGui.progress_bar(_progress_fraction(), -1.0, 0.0, overlay)
    PyImGui.spacing()
    run_state = "Running" if running else "Paused" if paused else "Stopped"
    _draw_label_value("Run", run_state, GOOD if running else WARN)
    if phase_total > 0:
        _draw_label_value("Phase", f"{phase_current}/{phase_total} {phase_title}")
    if recipe_title:
        _draw_label_value("Recipe", recipe_title)
    if step_total > 0:
        anchor_label = " anchor" if metadata is not None and bool(metadata.anchor) else ""
        _draw_label_value("Step", f"{step_current}/{step_total} {step_title}{anchor_label}", ACCENT)
    else:
        _draw_label_value("Step", "not started", MUTED)


def _draw_runtime_controls() -> None:
    selected = _selected_recipe_path()
    running = _runner_is_running()
    paused = _runner_is_paused()
    PyImGui.begin_disabled(not selected or running)
    if _primary_button("Run selected", 116):
        _start_selected_recipe()
    PyImGui.end_disabled()
    PyImGui.same_line(0, 6)
    PyImGui.begin_disabled(not running)
    if _quiet_button("Pause", 78):
        _pause_runner()
    PyImGui.end_disabled()
    PyImGui.same_line(0, 6)
    PyImGui.begin_disabled(not paused)
    if _primary_button("Resume", 82):
        _resume_runner()
    PyImGui.end_disabled()
    PyImGui.same_line(0, 6)
    PyImGui.begin_disabled(not (running or paused))
    if _danger_button("Stop", 70):
        _stop_runner()
    PyImGui.end_disabled()


def _draw_step_timeline() -> None:
    global _preview_step_index, _start_step_index
    selected = _selected_recipe_path()
    steps = _recipe_steps_for_display(selected)
    if not steps:
        PyImGui.text_colored("No selected recipe steps.", MUTED)
        return
    active_index = 0
    if _runner is not None and selected == _last_recipe:
        step_current, _step_total, _recipe_title, _step_title = _runner.get_step_progress()
        active_index = int(step_current or 0)
    if _preview_step_index >= len(steps):
        _preview_step_index = max(0, len(steps) - 1)
    if _start_step_index >= len(steps):
        _start_step_index = max(0, len(steps) - 1)
    PyImGui.text_colored("Select a step before running to start from there.", MUTED)
    if PyImGui.begin_child("##modular_tester_steps", (0, 0), True, PyImGui.WindowFlags.HorizontalScrollbar):
        for index, step in enumerate(steps):
            completed = bool(active_index and index + 1 < active_index)
            active = bool(active_index and index + 1 == active_index)
            start_step = index == _start_step_index
            selected_step = index == _preview_step_index
            row_color = GOOD if completed else ACCENT if active else TEXT
            if bool(step.get("anchor")) and not active:
                row_color = WARN
            start_prefix = "[start] " if start_step and not active else ""
            label = f"{start_prefix}{_step_label(step, index)}"
            if _selectable_row(f"{label}##step_{index}", selected_step):
                _preview_step_index = index
                if not (_runner_is_running() or _runner_is_paused()):
                    _start_step_index = index
            PyImGui.text_colored(f"  {_step_type_label(step)}", row_color if active else MUTED)
    PyImGui.end_child()


def _draw_step_detail() -> None:
    global _start_step_index
    selected = _selected_recipe_path()
    steps = _recipe_steps_for_display(selected)
    if not steps:
        PyImGui.text_colored("No step selected.", MUTED)
        return
    index = min(max(0, _preview_step_index), len(steps) - 1)
    step = steps[index]
    _draw_section_title(_step_label(step, index), f"{index + 1}/{len(steps)}")
    PyImGui.begin_disabled(_runner_is_running() or _runner_is_paused())
    if _primary_button("Start from this step", 170):
        _start_step_index = index
    PyImGui.end_disabled()
    PyImGui.spacing()
    if PyImGui.begin_table("##modular_tester_step_detail", 2, PyImGui.TableFlags.SizingStretchProp | PyImGui.TableFlags.RowBg):
        _draw_detail_row("Type", str(step.get("type") or ""))
        _draw_detail_row("Action", str(step.get("action") or step.get("mode") or ""))
        _draw_detail_row("Target", str(step.get("target") or step.get("npc") or step.get("gadget") or ""))
        _draw_detail_row("Map", str(step.get("map_id") or step.get("target_map_id") or step.get("map") or ""))
        _draw_detail_row("Points", str(_points_count(step)))
        _draw_detail_row("Anchor", "yes" if bool(step.get("anchor")) else "no")
        PyImGui.end_table()


def _draw_detail_row(label: str, value: str) -> None:
    PyImGui.table_next_row()
    PyImGui.table_set_column_index(0)
    PyImGui.text_colored(label, MUTED)
    PyImGui.table_set_column_index(1)
    PyImGui.text_wrapped(value or "-")


def _draw_right_panel() -> None:
    _draw_recipe_overview()
    _draw_runtime_controls()
    PyImGui.spacing()
    _draw_progress_panel()
    if _status:
        PyImGui.spacing()
        PyImGui.text_colored(_status, _status_color())
    PyImGui.separator()
    if PyImGui.begin_tab_bar("##modular_tester_tabs", PyImGui.TabBarFlags.NoFlag):
        if PyImGui.begin_tab_item("Timeline"):
            _draw_step_timeline()
            PyImGui.end_tab_item()
        if PyImGui.begin_tab_item("Step Detail"):
            _draw_step_detail()
            PyImGui.end_tab_item()
        PyImGui.end_tab_bar()


def _draw_main_layout() -> None:
    flags = PyImGui.TableFlags.Resizable | PyImGui.TableFlags.SizingStretchProp | PyImGui.TableFlags.BordersInnerV
    if PyImGui.begin_table("##modular_tester_layout", 2, flags, 0.0, 0.0):
        PyImGui.table_setup_column("##recipes", PyImGui.TableColumnFlags.WidthFixed, 320.0)
        PyImGui.table_setup_column("##runner", PyImGui.TableColumnFlags.WidthStretch)
        PyImGui.table_next_row()
        PyImGui.table_set_column_index(0)
        if PyImGui.begin_child("##modular_tester_left", (0, 0), True, PyImGui.WindowFlags.NoFlag):
            _draw_recipe_picker()
        PyImGui.end_child()
        PyImGui.table_set_column_index(1)
        if PyImGui.begin_child("##modular_tester_right", (0, 0), True, PyImGui.WindowFlags.NoFlag):
            _draw_right_panel()
        PyImGui.end_child()
        PyImGui.end_table()
    else:
        _draw_recipe_picker()
        PyImGui.separator()
        _draw_right_panel()


def _main_impl() -> None:
    if _runner is not None and _runner.is_running():
        _runner.update()

    PyImGui.set_next_window_size((880, 640), PyImGui.ImGuiCond.FirstUseEver)
    PyImGui.set_next_window_bg_alpha(1.0)
    theme_colors = _push_tester_theme()
    if not PyImGui.begin(MODULE_NAME):
        PyImGui.end()
        PyImGui.pop_style_color(theme_colors)
        return
    _draw_top_bar()
    _draw_main_layout()
    PyImGui.end()
    _draw_move_path_overlay()
    PyImGui.pop_style_color(theme_colors)


def main() -> None:
    guarded_widget_main(MODULE_NAME, _main_impl, get_bot=lambda: _runner)


def tooltip() -> None:
    PyImGui.set_next_window_size((430, 0))
    PyImGui.begin_tooltip()
    PyImGui.text(MODULE_NAME)
    PyImGui.separator()
    PyImGui.text_wrapped("Run one canonical modular JSON recipe through the BT compiler.")
    PyImGui.text_wrapped("Use this for checking a newly recorded bot before adding it to a campaign.")
    PyImGui.end_tooltip()


if __name__ == "__main__":
    main()
