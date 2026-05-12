import os
import re
from typing import TYPE_CHECKING, Callable, Protocol, cast

import Py4GW
import PyImGui

from ..GlobalCache import GLOBAL_CACHE
from ..ImGui import ImGui
from ..Overlay import Overlay
from ..Player import Player
from ..py4gwcorelib_src.Color import Color, ColorPalette
from ..py4gwcorelib_src.WindowFactory import ManagedWindowSpec, WindowFactory

if TYPE_CHECKING:
    from ..BottingTree import BottingTree


class _BottingTreeUIMovePathHost(Protocol):
    class _DrawableTree(Protocol):
        def draw(self) -> None: ...

    blackboard: dict
    draw_move_path_enabled: bool
    draw_move_path_labels: bool
    draw_move_path_thickness: float
    draw_move_waypoint_radius: float
    draw_move_current_waypoint_radius: float
    tree: _DrawableTree

    def DrawMovePath(
        self,
        draw_labels: bool = False,
        player_to_waypoint_color: Color = ColorPalette.GetColor('aqua'),
        remaining_path_color: Color = ColorPalette.GetColor('orange'),
        waypoint_color: Color = ColorPalette.GetColor('dodger_blue'),
        current_waypoint_color: Color = ColorPalette.GetColor('tomato'),
        player_marker_color: Color = ColorPalette.GetColor('white'),
        path_thickness: float = 4.0,
        waypoint_radius: float = 15.0,
        current_waypoint_radius: float = 20.0,
    ) -> None: ...

    def GetMoveData(self) -> dict: ...


class BottingTreeUIMovePathMixin:
    def GetMoveData(self) -> dict:
        host = cast(_BottingTreeUIMovePathHost, self)
        bb = host.blackboard
        path_points_raw = bb.get('move_path_points', [])
        path_points: list[tuple[float, float]] = []
        if isinstance(path_points_raw, list):
            for point in path_points_raw:
                if isinstance(point, tuple) and len(point) == 2:
                    path_points.append((float(point[0]), float(point[1])))

        current_waypoint_raw = bb.get('move_current_waypoint')
        current_waypoint: tuple[float, float] | None = None
        if isinstance(current_waypoint_raw, tuple) and len(current_waypoint_raw) == 2:
            current_waypoint = (float(current_waypoint_raw[0]), float(current_waypoint_raw[1]))

        target_raw = bb.get('move_target')
        move_target: tuple[float, float] | None = None
        if isinstance(target_raw, tuple) and len(target_raw) == 2:
            move_target = (float(target_raw[0]), float(target_raw[1]))

        last_move_point_raw = bb.get('move_last_move_point')
        last_move_point: tuple[float, float] | None = None
        if isinstance(last_move_point_raw, tuple) and len(last_move_point_raw) == 2:
            last_move_point = (float(last_move_point_raw[0]), float(last_move_point_raw[1]))

        return {
            'state': str(bb.get('move_state', '')),
            'reason': str(bb.get('move_reason', '')),
            'target': move_target,
            'path_points': path_points,
            'path_index': int(bb.get('move_path_index', 0) or 0),
            'path_count': int(bb.get('move_path_count', len(path_points)) or 0),
            'current_waypoint': current_waypoint,
            'current_waypoint_index': int(bb.get('move_current_waypoint_index', -1) or -1),
            'last_move_point': last_move_point,
            'resume_recovery_active': bool(bb.get('move_resume_recovery_active', False)),
        }

    def SetMovePathDrawingEnabled(self, enabled: bool) -> None:
        host = cast(_BottingTreeUIMovePathHost, self)
        host.draw_move_path_enabled = bool(enabled)

    def IsMovePathDrawingEnabled(self) -> bool:
        host = cast(_BottingTreeUIMovePathHost, self)
        return bool(host.draw_move_path_enabled)

    def DrawMovePathDebugOptions(self, label: str = 'Draw Move Path Debug Options') -> None:
        host = cast(_BottingTreeUIMovePathHost, self)
        if PyImGui.collapsing_header(label):
            host.draw_move_path_enabled = PyImGui.checkbox(
                'Draw Move Path',
                host.draw_move_path_enabled,
            )
            host.draw_move_path_labels = PyImGui.checkbox(
                'Draw Path Labels',
                host.draw_move_path_labels,
            )
            host.draw_move_path_thickness = PyImGui.slider_float(
                'Path Thickness',
                host.draw_move_path_thickness,
                1.0,
                6.0,
            )
            host.draw_move_waypoint_radius = PyImGui.slider_float(
                'Waypoint Radius',
                host.draw_move_waypoint_radius,
                15.0,
                100.0,
            )
            host.draw_move_current_waypoint_radius = PyImGui.slider_float(
                'Current Waypoint Radius',
                host.draw_move_current_waypoint_radius,
                20.0,
                120.0,
            )

    def DrawMovePathIfEnabled(self) -> None:
        host = cast(_BottingTreeUIMovePathHost, self)
        if not host.draw_move_path_enabled:
            return
        host.DrawMovePath(
            draw_labels=host.draw_move_path_labels,
            path_thickness=host.draw_move_path_thickness,
            waypoint_radius=host.draw_move_waypoint_radius,
            current_waypoint_radius=host.draw_move_current_waypoint_radius,
        )

    def DrawMovePath(
        self,
        draw_labels: bool = False,
        player_to_waypoint_color: Color = ColorPalette.GetColor('aqua'),
        remaining_path_color: Color = ColorPalette.GetColor('orange'),
        waypoint_color: Color = ColorPalette.GetColor('dodger_blue'),
        current_waypoint_color: Color = ColorPalette.GetColor('tomato'),
        player_marker_color: Color = ColorPalette.GetColor('white'),
        path_thickness: float = 4.0,
        waypoint_radius: float = 15.0,
        current_waypoint_radius: float = 20.0,
    ) -> None:
        host = cast(_BottingTreeUIMovePathHost, self)
        move_data = host.GetMoveData()
        move_state = move_data['state']
        path_points = move_data['path_points']
        if move_state not in ('running', 'paused') or not path_points:
            return

        path_index = move_data['path_index']
        current_waypoint = move_data['current_waypoint']
        player_x, player_y = Player.GetXY()
        overlay = Overlay()

        def _ground_z(x: float, y: float) -> float:
            return float(Overlay.FindZ(float(x), float(y)))

        def _is_visible(x: float, y: float) -> bool:
            return bool(GLOBAL_CACHE.Camera.IsPointInFOV(float(x), float(y)))

        def _draw_waypoint_marker(point_x: float, point_y: float, radius: float, color: int) -> None:
            if not _is_visible(point_x, point_y):
                return
            point_z = _ground_z(point_x, point_y)
            overlay.DrawPolyFilled3D(point_x, point_y, point_z, radius, color, 24)

        overlay.BeginDraw()
        try:
            if current_waypoint is not None:
                current_x, current_y = current_waypoint
                if _is_visible(player_x, player_y) and _is_visible(current_x, current_y):
                    overlay.DrawLine3D(
                        player_x,
                        player_y,
                        _ground_z(player_x, player_y),
                        current_x,
                        current_y,
                        _ground_z(current_x, current_y),
                        player_to_waypoint_color.to_color(),
                        path_thickness,
                    )

            start_index = max(0, min(path_index, len(path_points) - 1))
            for i in range(start_index, len(path_points) - 1):
                x1, y1 = path_points[i]
                x2, y2 = path_points[i + 1]
                if not (_is_visible(x1, y1) and _is_visible(x2, y2)):
                    continue
                overlay.DrawLine3D(
                    x1,
                    y1,
                    _ground_z(x1, y1),
                    x2,
                    y2,
                    _ground_z(x2, y2),
                    remaining_path_color.to_color(),
                    path_thickness,
                )

            for i, (point_x, point_y) in enumerate(path_points[start_index:], start=start_index):
                is_current = (i == move_data['current_waypoint_index'])
                marker_color = current_waypoint_color if is_current else waypoint_color
                marker_radius = current_waypoint_radius if is_current else waypoint_radius
                _draw_waypoint_marker(point_x, point_y, marker_radius, marker_color.to_color())
                if draw_labels and _is_visible(point_x, point_y):
                    point_z = _ground_z(point_x, point_y)
                    overlay.DrawText3D(point_x, point_y, point_z - 100.0, str(i), marker_color.to_color(), False, True, 2.0)

            if _is_visible(player_x, player_y):
                overlay.DrawPoly3D(player_x, player_y, _ground_z(player_x, player_y), waypoint_radius, player_marker_color.to_color(), 24, 2.0, False)
        finally:
            overlay.EndDraw()

    def Draw(self):
        host = cast(_BottingTreeUIMovePathHost, self)
        host.tree.draw()


class _BottingTreeUI:
    def __init__(self, parent: 'BottingTree'):
        self.parent = parent
        self.draw_texture_fn: Callable[[], None] | None = None
        self.draw_config_fn: Callable[[], None] | None = None
        self.draw_help_fn: Callable[[], None] | None = None
        self._selected_start_index = 0
        self._show_tree = True
        self._debug_console_height = 200.0
        self._window_factory: WindowFactory | None = None
        self._floating_button: ImGui.FloatingIcon | None = None
        self._window_factory_ready = False
        self._window_args: dict[str, object] = {
            'main_child_dimensions': (350, 325),
            'icon_path': '',
            'iconwidth': 96,
            'additional_ui': None,
            'extra_tabs': None,
        }

    @staticmethod
    def _sanitize_identifier(value: str) -> str:
        return re.sub(r'[^A-Za-z0-9_-]+', '_', value).strip('_') or 'BottingTree'

    def _default_icon_path(self) -> str:
        return os.path.join(Py4GW.Console.get_projects_path(), 'python_icon_round.png')

    def _ensure_window_factory(self) -> bool:
        if self._window_factory_ready and self._window_factory is not None:
            return True

        safe_name = self._sanitize_identifier(self.parent.bot_name)
        ini_path = f'Widgets/Automation/BottingTree/{safe_name}'
        factory = WindowFactory(ini_path)
        factory.register_window(
            ManagedWindowSpec(
                identifier='main',
                filename='BottingTreeUI.ini',
                title=self.parent.bot_name,
                flags=PyImGui.WindowFlags(PyImGui.WindowFlags.AlwaysAutoResize),
                open_var_name='show_main_window',
                open_default=True,
            )
        )
        factory.register_window(
            ManagedWindowSpec(
                identifier='floating',
                filename='BottingTreeFloating.ini',
                title=f'{self.parent.bot_name} Toggle',
            )
        )

        if not factory.ensure_ini():
            return False

        self._window_factory = factory
        self._window_factory_ready = True
        return True

    def _ensure_floating_button(self, icon_path: str = '') -> ImGui.FloatingIcon | None:
        if not self._ensure_window_factory() or self._window_factory is None:
            return None

        resolved_icon_path = icon_path or self._default_icon_path()
        if self._floating_button is None:
            safe_name = self._sanitize_identifier(self.parent.bot_name)
            self._floating_button = ImGui.FloatingIcon(
                icon_path=resolved_icon_path,
                window_id=f'##{safe_name}_floating_toggle_button',
                window_name=f'{self.parent.bot_name} Toggle',
                tooltip_visible=f'Hide {self.parent.bot_name}',
                tooltip_hidden=f'Show {self.parent.bot_name}',
                toggle_ini_key=self._window_factory.key('main'),
                toggle_var_name='show_main_window',
                toggle_default=True,
                draw_callback=self._draw_managed_window,
            )
            self._floating_button.load_visibility()
            self._floating_button.load_config(self._window_factory.key('floating'))
        else:
            self._floating_button.icon_path = resolved_icon_path
            self._floating_button.draw_callback = self._draw_managed_window

        return self._floating_button

    def _draw_managed_window(self) -> None:
        if self._window_factory is None:
            return

        expanded, open_ = self._window_factory.begin(
            'main',
            p_open=(self._floating_button.visible if self._floating_button is not None else self._window_factory.is_open('main')),
        )
        if self._floating_button is not None:
            self._floating_button.sync_begin_with_close(open_)

        if expanded:
            main_child_dimensions = cast(tuple[int, int], self._window_args['main_child_dimensions'])
            icon_path = cast(str, self._window_args['icon_path'])
            iconwidth = cast(int, self._window_args['iconwidth'])
            additional_ui = cast(Callable[[], None] | None, self._window_args['additional_ui'])
            extra_tabs = cast(list[tuple[str, Callable[[], None]]] | None, self._window_args['extra_tabs'])

            if PyImGui.begin_tab_bar(self.parent.bot_name + '_tabs'):
                if PyImGui.begin_tab_item('Main'):
                    if PyImGui.begin_child(f'{self.parent.bot_name} - Main', main_child_dimensions, True, PyImGui.WindowFlags.NoFlag):
                        self._draw_main_child(main_child_dimensions, icon_path, iconwidth)
                        if additional_ui is not None:
                            PyImGui.separator()
                            additional_ui()
                    PyImGui.end_child()
                    PyImGui.end_tab_item()

                if PyImGui.begin_tab_item('Navigation'):
                    self._draw_navigation_child(main_child_dimensions)
                    PyImGui.end_tab_item()

                if PyImGui.begin_tab_item('Settings'):
                    self._draw_settings_child()
                    PyImGui.end_tab_item()

                if PyImGui.begin_tab_item('Help'):
                    self._draw_help_child()
                    PyImGui.end_tab_item()

                if PyImGui.begin_tab_item('Debug'):
                    self.draw_debug_window()
                    PyImGui.end_tab_item()

                if extra_tabs:
                    for tab_label, tab_draw_fn in extra_tabs:
                        if PyImGui.begin_tab_item(tab_label):
                            if callable(tab_draw_fn):
                                tab_draw_fn()
                            PyImGui.end_tab_item()

                PyImGui.end_tab_bar()

        ImGui.End(self._window_factory.key('main'))

    def override_draw_texture(self, draw_fn: Callable[[], None] | None = None) -> None:
        self.draw_texture_fn = draw_fn

    def override_draw_config(self, draw_fn: Callable[[], None] | None = None) -> None:
        self.draw_config_fn = draw_fn

    def override_draw_help(self, draw_fn: Callable[[], None] | None = None) -> None:
        self.draw_help_fn = draw_fn

    def PrintMessageToConsole(self, source: str, message: str) -> None:
        Py4GW.Console.Log(source, message, Py4GW.Console.MessageType.Info)

    def _draw_texture(self, icon_path: str = '', size: tuple[float, float] = (96.0, 96.0)) -> None:
        if self.draw_texture_fn is not None:
            self.draw_texture_fn()
            return
        if not icon_path:
            return

        try:
            from ..ImGui import ImGui

            ImGui.DrawTextureExtended(
                texture_path=icon_path,
                size=size,
                uv0=(0.0, 0.0),
                uv1=(1.0, 1.0),
                tint=(255, 255, 255, 255),
                border_color=(0, 0, 0, 0),
            )
        except Exception:
            PyImGui.text(icon_path)

    def _colored_bool(self, label: str, value: bool) -> None:
        color = (0, 255, 0, 255) if value else (255, 80, 80, 255)
        PyImGui.text_colored(f'{label}: {value}', color)

    def _current_step_name(self) -> str:
        current_step_name = str(self.parent.GetBlackboardValue('current_step_name', '') or '')
        if current_step_name:
            return current_step_name
        planner_status = str(self.parent.GetBlackboardValue('PLANNER_STATUS', '') or '')
        return planner_status or 'Idle'

    def _draw_main_child(
        self,
        main_child_dimensions: tuple[int, int] = (350, 300),
        icon_path: str = '',
        iconwidth: int = 96,
    ) -> None:
        if PyImGui.begin_table('botting_tree_header_table', 2, PyImGui.TableFlags.RowBg | PyImGui.TableFlags.BordersOuterH):
            PyImGui.table_setup_column('Icon', PyImGui.TableColumnFlags.WidthFixed, iconwidth)
            PyImGui.table_setup_column('Status', PyImGui.TableColumnFlags.WidthFixed, main_child_dimensions[0] - iconwidth)
            PyImGui.table_next_row()
            PyImGui.table_set_column_index(0)
            self._draw_texture(icon_path, (float(iconwidth), float(iconwidth)))
            PyImGui.table_set_column_index(1)
            PyImGui.text(self.parent.bot_name)
            PyImGui.text(f'Current: {self._current_step_name()}')
            PyImGui.text(f"HeroAI: {self.parent.GetBlackboardValue('HEROAI_STATUS', 'Idle')}")
            PyImGui.text(f"Planner: {self.parent.GetBlackboardValue('PLANNER_STATUS', 'Idle')}")
            PyImGui.end_table()

        if self.parent.IsStarted():
            if PyImGui.button('Stop##BottingTreeStop'):
                self.parent.Stop()
            PyImGui.same_line(0, -1)
            if self.parent.IsPaused():
                if PyImGui.button('Resume##BottingTreePause'):
                    self.parent.Pause(False)
            else:
                if PyImGui.button('Pause##BottingTreePause'):
                    self.parent.Pause(True)
        else:
            step_names = self.parent.GetNamedPlannerStepNames()
            if step_names:
                self._selected_start_index = max(0, min(self._selected_start_index, len(step_names) - 1))
                self._selected_start_index = PyImGui.combo('Start At', self._selected_start_index, step_names)
                if PyImGui.button('Start##BottingTreeStart'):
                    self.parent.RestartFromNamedPlannerStep(step_names[self._selected_start_index], auto_start=True)
            else:
                if PyImGui.button('Start##BottingTreeStart'):
                    self.parent.Start()

        PyImGui.separator()
        self._colored_bool('Started', self.parent.IsStarted())
        self._colored_bool('Paused', self.parent.IsPaused())
        self._colored_bool('Headless HeroAI', self.parent.IsHeadlessHeroAIEnabled())
        self._colored_bool('Looting', self.parent.IsLootingEnabled())
        self._colored_bool('Account Isolation', self.parent.IsIsolationEnabled())
        self._colored_bool('Pause On Combat', bool(self.parent.GetBlackboardValue('pause_on_combat', self.parent.pause_on_combat)))
        self._colored_bool('Combat Active', bool(self.parent.GetBlackboardValue('COMBAT_ACTIVE', False)))
        self._colored_bool('Looting Active', bool(self.parent.GetBlackboardValue('LOOTING_ACTIVE', False)))

    def _draw_navigation_child(self, child_size: tuple[int, int] = (350, 275)) -> None:
        step_names = self.parent.GetNamedPlannerStepNames()
        if not step_names:
            PyImGui.text('No named planner steps configured.')
            return

        self._selected_start_index = max(0, min(self._selected_start_index, len(step_names) - 1))
        self._selected_start_index = PyImGui.combo('Restart From', self._selected_start_index, step_names)
        if PyImGui.button('Restart Selected'):
            self.parent.RestartFromNamedPlannerStep(step_names[self._selected_start_index], auto_start=True)

        PyImGui.separator()
        if PyImGui.begin_child('BottingTreeNamedSteps', child_size, True, PyImGui.WindowFlags.HorizontalScrollbar):
            for index, step_name in enumerate(step_names):
                marker = '>' if index == self._selected_start_index else ' '
                PyImGui.text(f'{marker} {index}: {step_name}')
        PyImGui.end_child()

    def _draw_settings_child(self) -> None:
        if self.draw_config_fn is not None:
            self.draw_config_fn()
            return

        self.parent.pause_on_combat = PyImGui.checkbox('Pause Planner On Combat', self.parent.pause_on_combat)
        headless_heroai_enabled = PyImGui.checkbox('Headless HeroAI', self.parent.IsHeadlessHeroAIEnabled())
        if headless_heroai_enabled != self.parent.IsHeadlessHeroAIEnabled():
            self.parent.SetHeadlessHeroAIEnabled(headless_heroai_enabled, reset_runtime=False)

        looting_enabled = PyImGui.checkbox('Looting', self.parent.IsLootingEnabled())
        if looting_enabled != self.parent.IsLootingEnabled():
            self.parent.SetLootingEnabled(looting_enabled)

        isolation_enabled = PyImGui.checkbox('Account Isolation', self.parent.IsIsolationEnabled())
        if isolation_enabled != self.parent.IsIsolationEnabled():
            self.parent.SetIsolationEnabled(isolation_enabled)
        PyImGui.separator()
        self.parent.DrawMovePathDebugOptions()

    def _draw_help_child(self) -> None:
        if self.draw_help_fn is not None:
            self.draw_help_fn()
            return

        PyImGui.text('BottingTree default UI')
        PyImGui.separator()
        PyImGui.text('Use SetMainRoutine(...) with a BehaviorTree, node, callable, child list, or named step list.')
        PyImGui.text('Call tick() every frame, then draw_window(...).')

    def draw_debug_window(self) -> None:
        if PyImGui.collapsing_header('Runtime'):
            PyImGui.text(f"HeroAI Status: {self.parent.GetBlackboardValue('HEROAI_STATUS', '')}")
            PyImGui.text(f"Planner Status: {self.parent.GetBlackboardValue('PLANNER_STATUS', '')}")
            PyImGui.text(f'Last UI Log: {self.parent.GetDebugConsoleLastMessage()}')

        if PyImGui.collapsing_header('Blackboard'):
            for key in sorted(self.parent.blackboard.keys()):
                value = self.parent.blackboard.get(key)
                PyImGui.text_wrapped(f'{key}: {value}')

        if PyImGui.collapsing_header('Debug Console'):
            self.parent.DrawDebugConsole(height=self._debug_console_height)

        if PyImGui.collapsing_header('Behavior Tree'):
            self._show_tree = PyImGui.checkbox('Show Tree', self._show_tree)
            if self._show_tree:
                self.parent.Draw()

    def draw_window(
        self,
        main_child_dimensions: tuple[int, int] = (350, 325),
        icon_path: str = '',
        iconwidth: int = 96,
        additional_ui: Callable[[], None] | None = None,
        extra_tabs: list[tuple[str, Callable[[], None]]] | None = None,
    ) -> bool:
        self._window_args = {
            'main_child_dimensions': main_child_dimensions,
            'icon_path': icon_path,
            'iconwidth': iconwidth,
            'additional_ui': additional_ui,
            'extra_tabs': extra_tabs,
        }

        floating_button = self._ensure_floating_button(icon_path)
        if floating_button is not None and self._window_factory is not None:
            floating_button.draw(self._window_factory.key('floating'))
        else:
            self._draw_managed_window()

        self.parent.DrawMovePathIfEnabled()
        return True

    DrawWindow = draw_window
    DrawDebugWindow = draw_debug_window
