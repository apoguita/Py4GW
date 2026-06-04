from __future__ import annotations

import os
import traceback

import Py4GW
import PyImGui

from Py4GWCoreLib.ImGui import ImGui
from Py4GWCoreLib.IniManager import IniManager
from Py4GWCoreLib.hero_team_manager import HERO_BEHAVIOR_LABELS
from Py4GWCoreLib.hero_team_manager import HERO_BEHAVIOR_DONT_CHANGE
from Py4GWCoreLib.hero_team_manager import HERO_BEHAVIOR_VALUES
from Py4GWCoreLib.hero_team_manager import HERO_ID_TO_INDEX
from Py4GWCoreLib.hero_team_manager import HERO_IDS
from Py4GWCoreLib.hero_team_manager import HERO_SLOT_COUNT
from Py4GWCoreLib.hero_team_manager import HeroTeamApplyOperation
from Py4GWCoreLib.hero_team_manager import HeroTeamConfig
from Py4GWCoreLib.hero_team_manager import add_team
from Py4GWCoreLib.hero_team_manager import add_template
from Py4GWCoreLib.hero_team_manager import apply_template_to_current_party_hero
from Py4GWCoreLib.hero_team_manager import build_load_preflight
from Py4GWCoreLib.hero_team_manager import classify_template_profession
from Py4GWCoreLib.hero_team_manager import clear_hero_alias
from Py4GWCoreLib.hero_team_manager import config_to_dict
from Py4GWCoreLib.hero_team_manager import create_apply_operation
from Py4GWCoreLib.hero_team_manager import current_party_hero_targets
from Py4GWCoreLib.hero_team_manager import current_party_hero_targets_for_template
from Py4GWCoreLib.hero_team_manager import dedupe_team_slots
from Py4GWCoreLib.hero_team_manager import delete_team
from Py4GWCoreLib.hero_team_manager import delete_template
from Py4GWCoreLib.hero_team_manager import duplicate_team
from Py4GWCoreLib.hero_team_manager import ensure_team_slots
from Py4GWCoreLib.hero_team_manager import get_team
from Py4GWCoreLib.hero_team_manager import get_template
from Py4GWCoreLib.hero_team_manager import hero_alias
from Py4GWCoreLib.hero_team_manager import hero_default_name
from Py4GWCoreLib.hero_team_manager import hero_display_name
from Py4GWCoreLib.hero_team_manager import hero_labels
from Py4GWCoreLib.hero_team_manager import is_pristine_default_config
from Py4GWCoreLib.hero_team_manager import load_config
from Py4GWCoreLib.hero_team_manager import resolve_slot_template_code
from Py4GWCoreLib.hero_team_manager import safe_account_key
from Py4GWCoreLib.hero_team_manager import save_config
from Py4GWCoreLib.hero_team_manager import save_current_party_as_team
from Py4GWCoreLib.hero_team_manager import set_hero_alias
from Py4GWCoreLib.hero_team_manager import summarize_skill_template


MODULE_NAME = 'Hero Team Manager'
MODULE_ICON = 'Textures\\Module_Icons\\Hero Team Manager.png'
MODULE_CATEGORY = 'Guild Wars'
MODULE_TAGS = ['Guild Wars', 'Customization', 'Heroes', 'Builds']
OPTIONAL = True


_config: HeroTeamConfig | None = None
_selected_template_id = ''
_active_tab = 'teams'
_status = ''
_operation: HeroTeamApplyOperation | None = None
_dirty = False
_saved_editable_state: dict[str, object] | None = None
_rename_kind = ''
_rename_id = ''
_rename_draft = ''
_code_edit_template_id = ''
_code_edit_draft = ''
_selected_apply_target_hero_id = 0
_confirm_action = ''
_confirm_title = ''
_confirm_message = ''
_confirm_payload: dict[str, str] = {}
_confirm_popup_requested = False
_window_ini_ready = False
_window_ini_key = ''
_floating_ui_ini_key = ''
_floating_button = None
_show_main_window = True
_expand_main_window_on_next_show = False
_template_group_order_loaded = False
_template_group_order: list[str] = []
_template_group_drag_from = ''
_template_group_drag_to = ''
_template_filter_loaded = False
_only_show_compatible_templates = True

TEAM_ROW_SLOT_WIDTH = 42.0
TEAM_ROW_NAME_WIDTH = 198.0
TEAM_ROW_TEMPLATE_WEIGHT = 0.45
TEAM_ROW_HERO_WEIGHT = 0.55
TEAM_ROW_BEHAVIOR_WIDTH = 132.0
TEMPLATE_PREVIEW_ICON_SIZE = 28.0
ALIAS_RESET_BUTTON_WIDTH = 22.0
RENAME_BUTTON_WIDTH = 64
RENAME_BUTTON_HEIGHT = 22
RENAME_TEXT_Y_OFFSET = 5.0
CODE_EDIT_BUTTON_WIDTH = 64
CODE_EDIT_BUTTON_HEIGHT = 22
CODE_COPY_BUTTON_WIDTH = 84
APPLY_TEMPLATE_BUTTON_WIDTH = 116
APPLY_TARGET_WIDTH = 300
TEMPLATE_BROWSER_LIST_WIDTH = 260.0
TEMPLATE_BROWSER_HEIGHT = 360.0
TEMPLATE_DETAILS_STACK_WIDTH = 520.0
TEMPLATE_DETAILS_MIN_SPLIT_WIDTH = 280.0
TEMPLATE_BROWSER_COLUMN_GAP = 28.0
TEMPLATE_BROWSER_MIN_SPLIT_WIDTH = (
    TEMPLATE_BROWSER_LIST_WIDTH + TEMPLATE_DETAILS_MIN_SPLIT_WIDTH + TEMPLATE_BROWSER_COLUMN_GAP
)
CONFIRM_POPUP_ID = 'Confirm Hero Team Manager Action##hero_team_manager_confirm'
WINDOW_INI_PATH = 'Widgets/Hero Team Manager'
WINDOW_INI_FILE = 'Hero Team Manager.MainWindow.ini'
FLOATING_UI_INI_FILE = 'Hero Team Manager.FloatingIcon.ini'
FLOATING_ICON_WINDOW_ID = '##hero_team_manager_floating_icon_button'
FLOATING_ICON_WINDOW_NAME = 'Hero Team Manager Toggle'
TEMPLATE_GROUP_ORDER_SECTION = 'Templates'
TEMPLATE_GROUP_ORDER_KEY = 'profession_group_order'
TEMPLATE_GROUP_DRAG_HANDLE_WIDTH = 34.0
TEMPLATE_FILTER_SECTION = 'Teams'
TEMPLATE_FILTER_KEY = 'only_show_compatible_templates'
UI_COLOR_SUCCESS = (0.45, 0.82, 0.45, 1.0)
UI_COLOR_WARNING = (1.0, 0.78, 0.30, 1.0)
UI_COLOR_DANGER = (0.95, 0.40, 0.40, 1.0)
UI_COLOR_MUTED = (0.65, 0.65, 0.65, 1.0)
UI_COLOR_NAV_SELECTED = (0.34, 0.48, 0.64, 1.0)
UI_COLOR_BUTTON_TEXT = (0.96, 0.97, 0.94, 1.0)
UI_COLOR_TABLE_HEADER_BG = (0.10, 0.17, 0.23, 0.92)
UI_COLOR_TABLE_HEADER_HOVERED = (0.13, 0.21, 0.29, 0.96)
UI_COLOR_TABLE_HEADER_ACTIVE = (0.08, 0.14, 0.20, 1.0)
UI_COLOR_TABLE_HEADER_TEXT = (0.86, 0.90, 0.92, 1.0)
UI_COLOR_ROW_ACTIVE_BG = (0.09, 0.12, 0.16, 0.22)
UI_COLOR_ROW_EMPTY_BG = (0.05, 0.06, 0.07, 0.62)
UI_COLOR_ROW_WARNING_BG = (0.28, 0.20, 0.08, 0.34)
UI_COLOR_ROW_ERROR_BG = (0.28, 0.08, 0.08, 0.30)
UI_COLOR_SLOT_ACTIVE = (0.76, 0.90, 1.0, 1.0)
UI_COLOR_SLOT_EMPTY = (0.42, 0.45, 0.46, 1.0)
UI_COLOR_SKIPPED_TEXT = (0.50, 0.53, 0.54, 1.0)
UI_COLOR_EMPTY_CONTROL_TEXT = (0.47, 0.50, 0.51, 1.0)
UI_COLOR_EMPTY_COMBO_BG = (0.045, 0.052, 0.060, 0.90)
UI_COLOR_EMPTY_COMBO_HOVERED = (0.065, 0.078, 0.090, 0.96)
UI_COLOR_EMPTY_COMBO_ACTIVE = (0.075, 0.092, 0.105, 1.0)
UI_COLOR_COMBO_POPUP_HEADER = (0.11, 0.18, 0.24, 0.92)
UI_COLOR_COMBO_POPUP_HEADER_HOVERED = (0.16, 0.25, 0.33, 0.96)
UI_COLOR_COMBO_POPUP_HEADER_ACTIVE = (0.18, 0.30, 0.38, 1.0)
EMPTY_CONTROL_TEXT_PAD = 6.0
PROFESSION_PALETTE_NAMES = {
    1: 'gw_warrior',
    2: 'gw_ranger',
    3: 'gw_monk',
    4: 'gw_necromancer',
    5: 'gw_mesmer',
    6: 'gw_elementalist',
    7: 'gw_assassin',
    8: 'gw_ritualist',
    9: 'gw_paragon',
    10: 'gw_dervish',
}


def _log_error(exc: Exception) -> None:
    Py4GW.Console.Log(MODULE_NAME, f'{exc}', Py4GW.Console.MessageType.Error)
    Py4GW.Console.Log(MODULE_NAME, traceback.format_exc(), Py4GW.Console.MessageType.Error)


def _editable_config_state(config: HeroTeamConfig) -> dict[str, object]:
    state = config_to_dict(config)
    state.pop('hero_profession_cache', None)
    return state


def _capture_saved_editable_state(config: HeroTeamConfig) -> None:
    global _saved_editable_state
    _saved_editable_state = _editable_config_state(config)


def _is_editable_state_dirty(config: HeroTeamConfig) -> bool:
    global _saved_editable_state
    current_state = _editable_config_state(config)
    if _saved_editable_state is None:
        _saved_editable_state = current_state
        return False
    return current_state != _saved_editable_state


def _sync_dirty_state(
    config: HeroTeamConfig | None = None,
    *,
    dirty_message: str = 'Unsaved changes.',
    clean_message: str = 'Saved.',
    update_status: bool = False,
) -> bool:
    global _dirty, _status
    current_config = config if config is not None else _ensure_config()
    was_dirty = bool(_dirty)
    _dirty = _is_editable_state_dirty(current_config)
    if update_status:
        if _dirty:
            _status = dirty_message
        elif was_dirty:
            _status = clean_message
    return _dirty


def _ensure_config() -> HeroTeamConfig:
    global _config, _dirty
    current_key = safe_account_key()
    if _config is None:
        _config = load_config(current_key)
        _capture_saved_editable_state(_config)
        _dirty = False
    elif (_config.account_key or 'default') == 'default' and current_key != 'default' and is_pristine_default_config(_config):
        _config = load_config(current_key)
        _capture_saved_editable_state(_config)
        _dirty = False
    return _config


def _save_status(message: str = 'Saved.') -> None:
    global _dirty, _status
    config = _ensure_config()
    save_config(config)
    _capture_saved_editable_state(config)
    _dirty = False
    _status = message


def _mark_dirty(message: str = 'Unsaved changes.') -> None:
    _sync_dirty_state(dirty_message=message, clean_message='Saved.', update_status=True)


def _clear_dirty(message: str = 'Saved.') -> None:
    global _dirty, _status
    _capture_saved_editable_state(_ensure_config())
    _dirty = False
    _status = message


def _reload_saved_config() -> None:
    global _config, _selected_template_id
    _config = load_config(safe_account_key())
    _selected_template_id = ''
    _clear_rename()
    _clear_code_edit()
    _clear_dirty('Reloaded saved configuration.')


def _operation_running() -> bool:
    return _operation is not None and not bool(getattr(_operation, 'done', False))


def _request_confirmation(action: str, title: str, message: str, payload: dict[str, str] | None = None) -> None:
    global _confirm_action, _confirm_title, _confirm_message, _confirm_payload, _confirm_popup_requested
    _confirm_action = str(action or '')
    _confirm_title = str(title or 'Confirm Action')
    _confirm_message = str(message or '')
    _confirm_payload = dict(payload or {})
    _confirm_popup_requested = True


def _clear_confirmation() -> None:
    global _confirm_action, _confirm_title, _confirm_message, _confirm_payload, _confirm_popup_requested
    _confirm_action = ''
    _confirm_title = ''
    _confirm_message = ''
    _confirm_payload = {}
    _confirm_popup_requested = False


def _input_text(label: str, value: str, max_len: int = 512) -> str:
    try:
        result = PyImGui.input_text(label, str(value), PyImGui.InputTextFlags.NoFlag)
    except Exception:
        result = PyImGui.input_text(label, str(value))
    text = str(result[1]) if isinstance(result, tuple) and len(result) >= 2 else str(result)
    return text[:max_len] if max_len > 0 else text


def _button(label: str, width: int = 0, height: int = 0) -> bool:
    try:
        return bool(PyImGui.button(label, width, height))
    except Exception:
        return bool(PyImGui.button(label))


def _button_disabled(label: str, disabled: bool, width: int = 0, height: int = 0) -> bool:
    if not disabled:
        return _button(label, width, height)

    began_disabled = _begin_disabled(True)
    try:
        _button(label, width, height)
    finally:
        _end_disabled(began_disabled)
    return False


def _semantic_color(severity: str = 'info') -> tuple[float, float, float, float]:
    severity = str(severity or 'info').lower()
    if severity in {'success', 'good', 'ready', 'safe', 'selected'}:
        return UI_COLOR_SUCCESS
    if severity in {'error', 'danger', 'blocked', 'missing', 'destructive'}:
        return UI_COLOR_DANGER
    if severity in {'warning', 'warn', 'incomplete', 'running', 'review'}:
        return UI_COLOR_WARNING
    return UI_COLOR_MUTED


def _button_tint(color: tuple[float, float, float, float], alpha: float, lift: float = 0.0) -> tuple[float, float, float, float]:
    return (
        min(max(float(color[0]) + lift, 0.0), 1.0),
        min(max(float(color[1]) + lift, 0.0), 1.0),
        min(max(float(color[2]) + lift, 0.0), 1.0),
        min(max(float(alpha), 0.0), 1.0),
    )


def _packed_color(color: tuple[float, float, float, float]) -> int:
    r = int(min(max(float(color[0]), 0.0), 1.0) * 255.0)
    g = int(min(max(float(color[1]), 0.0), 1.0) * 255.0)
    b = int(min(max(float(color[2]), 0.0), 1.0) * 255.0)
    a = int(min(max(float(color[3]), 0.0), 1.0) * 255.0)
    return ((a & 0xFF) << 24) | ((b & 0xFF) << 16) | ((g & 0xFF) << 8) | (r & 0xFF)


def _set_current_table_row_bg(color: tuple[float, float, float, float]) -> None:
    try:
        PyImGui.table_set_bg_color(2, _packed_color(color), -1)
    except Exception:
        pass


def _draw_team_table_headers() -> None:
    pushed = 0
    try:
        PyImGui.push_style_color(PyImGui.ImGuiCol.Header, UI_COLOR_TABLE_HEADER_BG)
        pushed += 1
        PyImGui.push_style_color(PyImGui.ImGuiCol.HeaderHovered, UI_COLOR_TABLE_HEADER_HOVERED)
        pushed += 1
        PyImGui.push_style_color(PyImGui.ImGuiCol.HeaderActive, UI_COLOR_TABLE_HEADER_ACTIVE)
        pushed += 1
        PyImGui.push_style_color(PyImGui.ImGuiCol.Text, UI_COLOR_TABLE_HEADER_TEXT)
        pushed += 1
        PyImGui.table_headers_row()
    except Exception:
        PyImGui.table_headers_row()
    finally:
        if pushed:
            try:
                PyImGui.pop_style_color(pushed)
            except Exception:
                pass


def _push_button_style(severity: str = 'info', active: bool = False) -> int:
    color = _semantic_color(severity)
    base_alpha = 0.54 if active else 0.42
    hover_alpha = 0.66 if active else 0.54
    active_alpha = 0.78 if active else 0.66
    PyImGui.push_style_color(PyImGui.ImGuiCol.Button, _button_tint(color, base_alpha, -0.10))
    PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonHovered, _button_tint(color, hover_alpha, -0.05))
    PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonActive, _button_tint(color, active_alpha, -0.15))
    PyImGui.push_style_color(PyImGui.ImGuiCol.Text, UI_COLOR_BUTTON_TEXT)
    return 4


def _push_selected_tab_button_style() -> int:
    PyImGui.push_style_color(PyImGui.ImGuiCol.Button, _button_tint(UI_COLOR_NAV_SELECTED, 0.74))
    PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonHovered, _button_tint(UI_COLOR_NAV_SELECTED, 0.86, 0.04))
    PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonActive, _button_tint(UI_COLOR_NAV_SELECTED, 0.98, -0.06))
    PyImGui.push_style_color(PyImGui.ImGuiCol.Text, UI_COLOR_BUTTON_TEXT)
    return 4


def _push_empty_combo_style() -> int:
    pushed = 0
    try:
        PyImGui.push_style_color(PyImGui.ImGuiCol.FrameBg, UI_COLOR_EMPTY_COMBO_BG)
        pushed += 1
        PyImGui.push_style_color(PyImGui.ImGuiCol.FrameBgHovered, UI_COLOR_EMPTY_COMBO_HOVERED)
        pushed += 1
        PyImGui.push_style_color(PyImGui.ImGuiCol.FrameBgActive, UI_COLOR_EMPTY_COMBO_ACTIVE)
        pushed += 1
    except Exception:
        if pushed:
            try:
                PyImGui.pop_style_color(pushed)
            except Exception:
                pass
        pushed = 0
    return pushed


def _push_combo_popup_style() -> int:
    pushed = 0
    try:
        PyImGui.push_style_color(PyImGui.ImGuiCol.Header, UI_COLOR_COMBO_POPUP_HEADER)
        pushed += 1
        PyImGui.push_style_color(PyImGui.ImGuiCol.HeaderHovered, UI_COLOR_COMBO_POPUP_HEADER_HOVERED)
        pushed += 1
        PyImGui.push_style_color(PyImGui.ImGuiCol.HeaderActive, UI_COLOR_COMBO_POPUP_HEADER_ACTIVE)
        pushed += 1
    except Exception:
        if pushed:
            try:
                PyImGui.pop_style_color(pushed)
            except Exception:
                pass
        pushed = 0
    return pushed


def _pop_style_colors(count: int) -> None:
    if count <= 0:
        return
    try:
        PyImGui.pop_style_color(int(count))
    except Exception:
        pass


def _button_selected_tab(label: str, width: int = 0, height: int = 0) -> bool:
    pushed = _push_selected_tab_button_style()
    try:
        return _button(label, width, height)
    finally:
        PyImGui.pop_style_color(pushed)


def _button_colored(
    label: str,
    severity: str,
    width: int = 0,
    height: int = 0,
    *,
    active: bool = False,
) -> bool:
    pushed = _push_button_style(severity, active=active)
    try:
        return _button(label, width, height)
    finally:
        PyImGui.pop_style_color(pushed)


def _button_colored_disabled(
    label: str,
    disabled: bool,
    severity: str,
    width: int = 0,
    height: int = 0,
    *,
    active: bool = False,
) -> bool:
    if disabled:
        return _button_disabled(label, True, width, height)
    return _button_colored(label, severity, width, height, active=active)


def _begin_disabled(disabled: bool) -> bool:
    if not disabled:
        return False
    try:
        PyImGui.begin_disabled(True)
        return True
    except Exception:
        return False


def _end_disabled(began_disabled: bool) -> None:
    if not began_disabled:
        return
    try:
        PyImGui.end_disabled()
    except Exception:
        pass


def _same_line(spacing: int = 6) -> None:
    try:
        PyImGui.same_line(0, spacing)
    except Exception:
        PyImGui.same_line()


def _muted_text(text: str) -> None:
    try:
        PyImGui.push_style_color(PyImGui.ImGuiCol.Text, UI_COLOR_MUTED)
        PyImGui.text(str(text))
        PyImGui.pop_style_color(1)
    except Exception:
        PyImGui.text(str(text))


def _tinted_text(text: str, color: tuple[float, float, float, float]) -> None:
    try:
        PyImGui.push_style_color(PyImGui.ImGuiCol.Text, color)
        PyImGui.text(str(text))
        PyImGui.pop_style_color(1)
    except Exception:
        PyImGui.text(str(text))


def _padded_tinted_text(text: str, color: tuple[float, float, float, float], pad: float = EMPTY_CONTROL_TEXT_PAD) -> None:
    try:
        PyImGui.set_cursor_pos_x(float(PyImGui.get_cursor_pos_x()) + float(pad))
    except Exception:
        pass
    _tinted_text(text, color)


def _colored_text(text: str, severity: str = 'info', wrapped: bool = False) -> None:
    try:
        PyImGui.push_style_color(PyImGui.ImGuiCol.Text, _semantic_color(severity))
        try:
            if wrapped:
                PyImGui.text_wrapped(str(text))
            else:
                PyImGui.text(str(text))
        except Exception:
            PyImGui.text(str(text))
        PyImGui.pop_style_color(1)
    except Exception:
        PyImGui.text(str(text))


def _row_colored_text(text: str, row_y: float | None, severity: str = 'info') -> None:
    _set_cursor_pos_y(None if row_y is None else row_y + RENAME_TEXT_Y_OFFSET)
    _colored_text(text, severity)


def _wrapped_text(text: str) -> None:
    try:
        PyImGui.text_wrapped(str(text))
    except Exception:
        PyImGui.text(str(text))


def _warning_color(severity: str = 'warning') -> tuple[float, float, float, float]:
    severity = str(severity or 'warning')
    if severity in {'error', 'danger'}:
        return _semantic_color('error')
    if severity == 'info':
        return _semantic_color('info')
    if severity == 'success':
        return _semantic_color('success')
    return _semantic_color('warning')


def _warning_text(text: str, severity: str = 'warning') -> None:
    try:
        PyImGui.push_style_color(PyImGui.ImGuiCol.Text, _warning_color(severity))
        try:
            PyImGui.text_wrapped(str(text))
        except Exception:
            PyImGui.text(str(text))
        PyImGui.pop_style_color(1)
    except Exception:
        PyImGui.text(str(text))


def _inline_status_text(text: str, severity: str = 'info') -> None:
    _colored_text(text, severity)


def _row_warning_severity(warnings: list[object]) -> str:
    codes = {str(getattr(warning, 'code', '') or '') for warning in warnings}
    if codes.intersection({'missing_template_reference', 'missing_template_code'}):
        return 'error'
    if any(getattr(warning, 'severity', 'warning') != 'info' for warning in warnings):
        return 'warning'
    return 'info'


def _status_severity(message: str) -> str:
    text = str(message or '').strip().lower()
    if not text:
        return 'info'

    warning_markers = (
        'unsaved',
        'click save',
        'warning',
        'running',
        'paused',
        'starting',
        'waiting',
        'leaving',
        'clearing',
        'adding',
        'applying',
        'duplicate',
        'truncated',
        'not applied',
        'unchanged',
        'finish code edit',
        'no current party heroes',
        'no template code',
    )
    danger_markers = (
        'error',
        'failed',
        'blocked',
        'load skipped',
        'could not',
        'cannot',
        'missing',
        'no available hero slot',
        'not an outpost',
        'not party leader',
    )
    neutral_markers = (
        'no duplicate slots found',
        'no team duplicated',
        'no template deleted',
        'no team selected',
    )
    success_markers = (
        'saved',
        'copied',
        'loaded',
        'renamed and saved',
        'reloaded saved configuration',
    )

    if any(marker in text for marker in danger_markers):
        return 'error'
    if any(marker in text for marker in warning_markers):
        return 'warning'
    if any(marker in text for marker in neutral_markers):
        return 'info'
    if any(marker in text for marker in success_markers):
        return 'success'
    return 'info'


def _show_item_tooltip(text: str) -> None:
    try:
        if PyImGui.is_item_hovered():
            PyImGui.set_tooltip(str(text))
    except Exception:
        pass


def _cursor_pos_y() -> float | None:
    try:
        return float(PyImGui.get_cursor_pos_y())
    except Exception:
        return None


def _set_cursor_pos_y(value: float | None) -> None:
    if value is None:
        return
    try:
        PyImGui.set_cursor_pos_y(float(value))
    except Exception:
        pass


def _rename_row_text(text: str, row_y: float | None) -> None:
    _set_cursor_pos_y(None if row_y is None else row_y + RENAME_TEXT_Y_OFFSET)
    PyImGui.text(str(text))


def _begin_rename(kind: str, item_id: str, current_name: str) -> None:
    global _rename_kind, _rename_id, _rename_draft
    _rename_kind = str(kind or '')
    _rename_id = str(item_id or '')
    _rename_draft = str(current_name or '')


def _clear_rename() -> None:
    global _rename_kind, _rename_id, _rename_draft
    _rename_kind = ''
    _rename_id = ''
    _rename_draft = ''


def _is_renaming(kind: str, item_id: str) -> bool:
    return _rename_kind == str(kind or '') and _rename_id == str(item_id or '')


def _draw_rename_control(
    kind: str,
    item_id: str,
    current_name: str,
    fallback_name: str,
    label: str,
    disabled: bool = False,
    stacked: bool = False,
) -> tuple[str, bool]:
    global _rename_draft, _status
    original_name = str(current_name or '')
    display_name = original_name.strip() or str(fallback_name or 'Unnamed')
    if stacked:
        PyImGui.text('Name')
        if not _is_renaming(kind, item_id):
            _wrapped_text(display_name)
            _show_item_tooltip(display_name)
            if _button_disabled(
                f'Rename##rename_{kind}_{item_id}',
                disabled,
                RENAME_BUTTON_WIDTH,
                RENAME_BUTTON_HEIGHT,
            ):
                _begin_rename(kind, item_id, display_name)
            _show_item_tooltip('Team load is running.' if disabled else 'Rename')
            return original_name, False

        try:
            PyImGui.set_next_item_width(-1)
        except Exception:
            pass
        began_disabled = _begin_disabled(disabled)
        try:
            _rename_draft = _input_text(f'##rename_name_{kind}_{item_id}', _rename_draft, 128)
        finally:
            _end_disabled(began_disabled)
        if _button_disabled(f'Apply##apply_rename_{kind}_{item_id}', disabled, 72, 24):
            cleaned = str(_rename_draft or '').strip()
            if not cleaned:
                _status = f'{label} name cannot be empty.'
                return original_name, False
            return cleaned[:128], True
        _same_line(4)
        if _button(f'Cancel##cancel_rename_{kind}_{item_id}', 72, 24):
            _clear_rename()
        return original_name, False

    row_y = _cursor_pos_y()
    _rename_row_text('Name', row_y)
    _same_line(8)

    if not _is_renaming(kind, item_id):
        _rename_row_text(display_name, row_y)
        _show_item_tooltip(display_name)
        _same_line(8)
        _set_cursor_pos_y(row_y)
        if _button_disabled(f'Rename##rename_{kind}_{item_id}', disabled, RENAME_BUTTON_WIDTH, RENAME_BUTTON_HEIGHT):
            _begin_rename(kind, item_id, display_name)
        _show_item_tooltip('Team load is running.' if disabled else 'Rename')
        return original_name, False

    _set_cursor_pos_y(row_y)
    try:
        PyImGui.set_next_item_width(360)
    except Exception:
        pass
    began_disabled = _begin_disabled(disabled)
    try:
        _rename_draft = _input_text(f'##rename_name_{kind}_{item_id}', _rename_draft, 128)
    finally:
        _end_disabled(began_disabled)
    _same_line(8)
    if _button_disabled(f'Apply##apply_rename_{kind}_{item_id}', disabled, 72, 24):
        cleaned = str(_rename_draft or '').strip()
        if not cleaned:
            _status = f'{label} name cannot be empty.'
            return original_name, False
        return cleaned[:128], True
    _same_line(4)
    if _button(f'Cancel##cancel_rename_{kind}_{item_id}', 72, 24):
        _clear_rename()
    return original_name, False


def _begin_code_edit(template_id: str, current_code: str) -> None:
    global _code_edit_template_id, _code_edit_draft
    _code_edit_template_id = str(template_id or '')
    _code_edit_draft = str(current_code or '')


def _clear_code_edit() -> None:
    global _code_edit_template_id, _code_edit_draft
    _code_edit_template_id = ''
    _code_edit_draft = ''


def _is_editing_code(template_id: str) -> bool:
    return _code_edit_template_id == str(template_id or '')


def _code_display_text(code: str) -> str:
    cleaned = str(code or '').strip()
    if not cleaned:
        return '<Empty>'
    return cleaned if len(cleaned) <= 96 else f'{cleaned[:93]}...'


def _draw_template_code_control(
    template_id: str,
    current_code: str,
    disabled: bool = False,
    stacked: bool = False,
) -> tuple[str, bool]:
    global _code_edit_draft, _status
    original_code = str(current_code or '')
    if stacked:
        PyImGui.text('Code')
        if not _is_editing_code(template_id):
            display = _code_display_text(original_code)
            if original_code.strip():
                _wrapped_text(display)
            else:
                _colored_text(display, 'warning', wrapped=True)
            _show_item_tooltip(original_code or '<Empty>')
            if _button_disabled(
                f'Edit##edit_template_code_{template_id}',
                disabled,
                CODE_EDIT_BUTTON_WIDTH,
                CODE_EDIT_BUTTON_HEIGHT,
            ):
                _begin_code_edit(template_id, original_code)
            _show_item_tooltip('Team load is running.' if disabled else 'Edit code')
            _same_line(4)
            if _button(f'Copy Code##copy_template_code_{template_id}', CODE_COPY_BUTTON_WIDTH, CODE_EDIT_BUTTON_HEIGHT):
                if original_code.strip():
                    try:
                        PyImGui.set_clipboard_text(original_code.strip())
                        _status = 'Template code copied.'
                    except Exception as exc:
                        _status = f'Copy failed: {exc}'
                else:
                    _status = 'No template code to copy.'
            _show_item_tooltip('Copy selected template code to clipboard.')
            return original_code, False

        try:
            PyImGui.set_next_item_width(-1)
        except Exception:
            pass
        began_disabled = _begin_disabled(disabled)
        try:
            _code_edit_draft = _input_text(f'##template_code_{template_id}', _code_edit_draft, 512)
        finally:
            _end_disabled(began_disabled)
        if _button_disabled(f'Apply##apply_template_code_{template_id}', disabled, 72, 24):
            cleaned = str(_code_edit_draft or '')[:512]
            _clear_code_edit()
            return cleaned, True
        _same_line(4)
        if _button(f'Cancel##cancel_template_code_{template_id}', 72, 24):
            _clear_code_edit()
        return original_code, False

    row_y = _cursor_pos_y()
    _rename_row_text('Code', row_y)
    _same_line(8)

    if not _is_editing_code(template_id):
        display = _code_display_text(original_code)
        if original_code.strip():
            _rename_row_text(display, row_y)
        else:
            _row_colored_text(display, row_y, 'warning')
        _show_item_tooltip(original_code or '<Empty>')
        _same_line(8)
        _set_cursor_pos_y(row_y)
        if _button_disabled(f'Edit##edit_template_code_{template_id}', disabled, CODE_EDIT_BUTTON_WIDTH, CODE_EDIT_BUTTON_HEIGHT):
            _begin_code_edit(template_id, original_code)
        _show_item_tooltip('Team load is running.' if disabled else 'Edit code')
        _same_line(4)
        _set_cursor_pos_y(row_y)
        if _button(f'Copy Code##copy_template_code_{template_id}', CODE_COPY_BUTTON_WIDTH, CODE_EDIT_BUTTON_HEIGHT):
            if original_code.strip():
                try:
                    PyImGui.set_clipboard_text(original_code.strip())
                    _status = 'Template code copied.'
                except Exception as exc:
                    _status = f'Copy failed: {exc}'
            else:
                _status = 'No template code to copy.'
        _show_item_tooltip('Copy selected template code to clipboard.')
        return original_code, False

    _set_cursor_pos_y(row_y)
    try:
        PyImGui.set_next_item_width(max(180.0, _content_width(520.0) - 170.0))
    except Exception:
        pass
    began_disabled = _begin_disabled(disabled)
    try:
        _code_edit_draft = _input_text(f'##template_code_{template_id}', _code_edit_draft, 512)
    finally:
        _end_disabled(began_disabled)
    _same_line(8)
    if _button_disabled(f'Apply##apply_template_code_{template_id}', disabled, 72, 24):
        cleaned = str(_code_edit_draft or '')[:512]
        _clear_code_edit()
        return cleaned, True
    _same_line(4)
    if _button(f'Cancel##cancel_template_code_{template_id}', 72, 24):
        _clear_code_edit()
    return original_code, False


def _commit_active_code_edit(config: HeroTeamConfig) -> bool:
    if not _code_edit_template_id:
        return False
    template = get_template(config, _code_edit_template_id)
    changed = False
    if template is not None:
        new_code = str(_code_edit_draft or '')[:512]
        changed = new_code != str(template.code or '')
        template.code = new_code
    _clear_code_edit()
    return changed


def _active_code_edit_changed(config: HeroTeamConfig) -> bool:
    if not _code_edit_template_id:
        return False
    template = get_template(config, _code_edit_template_id)
    if template is None:
        return False
    return str(_code_edit_draft or '')[:512] != str(template.code or '')


def _draw_skill_tooltip(skill_id: int, fallback_name: str = '') -> None:
    skill_id = int(skill_id or 0)
    if skill_id <= 0:
        PyImGui.text(str(fallback_name or 'Unknown skill'))
        return

    try:
        from HeroAI.ui_base import HeroAI_BaseUI

        HeroAI_BaseUI._draw_skill_info_card(skill_id, compact=True, tooltip=True)
        return
    except Exception:
        pass

    try:
        from Py4GWCoreLib.Skill import Skill

        skill_name = Skill.GetNameFromWiki(skill_id) or Skill.GetName(skill_id) or fallback_name or f'Skill {skill_id}'
        PyImGui.text(str(skill_name))
        PyImGui.separator()
        description = Skill.GetConciseDescription(skill_id) or Skill.GetDescription(skill_id) or ''
        if str(description or '').strip() and str(description).strip() != 'No description available.':
            try:
                PyImGui.push_text_wrap_pos(PyImGui.get_cursor_pos_x() + 360.0)
                PyImGui.text_wrapped(str(description).strip())
                PyImGui.pop_text_wrap_pos()
            except Exception:
                PyImGui.text(str(description).strip())
        _muted_text(f'ID: {skill_id}')
    except Exception:
        PyImGui.text(str(fallback_name or f'Skill {skill_id}'))


def _draw_template_preview(preview, title: str = '', compact: bool = False) -> None:
    header = str(title or preview.template_name or 'Template')
    _wrapped_text(header)
    if preview.profession_label:
        _wrapped_text(preview.profession_label)
    if preview.attribute_summary and not compact:
        _wrapped_text(preview.attribute_summary)

    icons = [
        (skill_id, icon_path, skill_name)
        for skill_id, icon_path, skill_name in zip(
            preview.skill_ids[:8],
            preview.skill_icon_paths[:8],
            preview.skill_names[:8],
        )
        if int(skill_id or 0) > 0 and icon_path
    ]
    if icons:
        for icon_index, (skill_id, icon_path, skill_name) in enumerate(icons):
            if icon_index > 0:
                _same_line(2)
            ImGui.DrawTexture(icon_path, TEMPLATE_PREVIEW_ICON_SIZE, TEMPLATE_PREVIEW_ICON_SIZE)
            if PyImGui.is_item_hovered():
                PyImGui.begin_tooltip()
                try:
                    _draw_skill_tooltip(int(skill_id), str(skill_name or ''))
                finally:
                    PyImGui.end_tooltip()
        return

    if preview.profession_icon_path:
        ImGui.DrawTexture(preview.profession_icon_path, TEMPLATE_PREVIEW_ICON_SIZE, TEMPLATE_PREVIEW_ICON_SIZE)
        return

    if not compact:
        PyImGui.text('No skill icons available.')


def _draw_template_preview_or_fallback(template, template_name: str = '', title: str = '', compact: bool = False) -> None:
    preview = summarize_skill_template(template, template_name=template_name or None)
    if preview is None:
        if title:
            PyImGui.text(str(title))
        _colored_text('Template code could not be parsed.', 'error')
        return
    _draw_template_preview(preview, title=title, compact=compact)


def _draw_selected_template_preview(template) -> None:
    PyImGui.text('Preview')
    try:
        PyImGui.indent(16.0)
    except Exception:
        pass
    _draw_template_preview_or_fallback(template)
    try:
        PyImGui.unindent(16.0)
    except Exception:
        pass


def _begin_tooltip_if_hovered() -> bool:
    try:
        if not PyImGui.is_item_hovered():
            return False
        PyImGui.begin_tooltip()
        return True
    except Exception:
        return False


def _end_tooltip() -> None:
    try:
        PyImGui.end_tooltip()
    except Exception:
        pass


def _show_template_tooltip(template) -> None:
    tooltip_open = _begin_tooltip_if_hovered()
    if not tooltip_open:
        return
    try:
        if template is None:
            PyImGui.text('<None>')
            return
        _draw_template_preview_or_fallback(template)
    finally:
        _end_tooltip()


def _collapsing_header(label: str, default_open: bool = False) -> bool:
    flags = getattr(getattr(PyImGui, 'TreeNodeFlags', None), 'NoFlag', 0)
    if default_open:
        flags = int(flags) | int(getattr(getattr(PyImGui, 'TreeNodeFlags', None), 'DefaultOpen', 0))
    try:
        return bool(PyImGui.collapsing_header(label, flags))
    except Exception:
        try:
            return bool(PyImGui.collapsing_header(label))
        except Exception:
            return True


def _profession_color(profession_id: int) -> tuple[float, float, float, float] | None:
    try:
        profession_id = int(profession_id or 0)
    except (TypeError, ValueError):
        return None
    palette_name = PROFESSION_PALETTE_NAMES.get(profession_id)
    if not palette_name:
        return None

    try:
        from Py4GWCoreLib.py4gwcorelib_src.Color import ColorPalette

        color = ColorPalette.GetColor(palette_name).to_tuple_normalized()
        if profession_id == 4:
            return (0.28, 1.0, 0.48, 1.0)
        return color if profession_id == 3 else _brighten_profession_header_color(color)
    except Exception:
        return None


def _profession_group_header_color(group) -> tuple[float, float, float, float]:
    if not bool(getattr(group, 'is_known_profession', False)):
        group_key = str(getattr(group, 'group_key', '') or '').lower()
        return UI_COLOR_WARNING if 'invalid' in group_key else UI_COLOR_MUTED

    profession_id = int(getattr(group, 'primary_profession_id', 0) or 0)
    return _profession_color(profession_id) or UI_COLOR_MUTED


def _brighten_profession_header_color(color: tuple[float, float, float, float]) -> tuple[float, float, float, float]:
    r, g, b, _a = color
    return (
        min((float(r) * 1.18) + 0.08, 1.0),
        min((float(g) * 1.18) + 0.08, 1.0),
        min((float(b) * 1.18) + 0.08, 1.0),
        1.0,
    )


def _collapsing_header_colored(label: str, color: tuple[float, float, float, float], default_open: bool = False) -> bool:
    try:
        PyImGui.push_style_color(PyImGui.ImGuiCol.Text, color)
        pushed = True
    except Exception:
        pushed = False
    try:
        return _collapsing_header(label, default_open=default_open)
    finally:
        if pushed:
            try:
                PyImGui.pop_style_color(1)
            except Exception:
                pass


def _parse_template_group_order(raw_value: str) -> list[str]:
    order: list[str] = []
    seen: set[str] = set()
    for value in str(raw_value or '').split(','):
        key = value.strip()
        if not key or key in seen:
            continue
        seen.add(key)
        order.append(key)
    return order


def _load_template_group_order_once() -> None:
    global _template_group_order_loaded, _template_group_order
    if _template_group_order_loaded:
        return
    if not _init_window_persistence_once():
        return
    _template_group_order_loaded = True
    raw_order = IniManager().read_key(
        _window_ini_key,
        TEMPLATE_GROUP_ORDER_SECTION,
        TEMPLATE_GROUP_ORDER_KEY,
        '',
    )
    _template_group_order = _parse_template_group_order(raw_order)


def _default_template_group_order(ordered_groups: list[tuple[object, list[object]]]) -> list[str]:
    order: list[str] = []
    for group, _templates in ordered_groups:
        key = str(getattr(group, 'group_key', '') or '')
        if key:
            order.append(key)
    return order


def _visible_template_group_order(ordered_groups: list[tuple[object, list[object]]]) -> list[str]:
    _load_template_group_order_once()
    default_order = _default_template_group_order(ordered_groups)
    available = set(default_order)
    visible_order: list[str] = []
    seen: set[str] = set()
    for key in _template_group_order:
        if key in available and key not in seen:
            visible_order.append(key)
            seen.add(key)
    for key in default_order:
        if key not in seen:
            visible_order.append(key)
            seen.add(key)
    return visible_order


def _save_template_group_order(visible_order: list[str]) -> None:
    global _template_group_order
    seen: set[str] = set()
    merged_order: list[str] = []
    for key in list(visible_order) + [key for key in _template_group_order if key not in visible_order]:
        if not key or key in seen:
            continue
        seen.add(key)
        merged_order.append(key)
    _template_group_order = merged_order
    if _init_window_persistence_once():
        IniManager().write_key(
            _window_ini_key,
            TEMPLATE_GROUP_ORDER_SECTION,
            TEMPLATE_GROUP_ORDER_KEY,
            ','.join(_template_group_order),
        )


def _draw_template_group_drag_handle(
    group_key: str,
    is_source: bool,
    is_target: bool,
    selectable_flags,
) -> None:
    global _template_group_drag_from, _template_group_drag_to
    marker = '>>' if is_source else '[::]'
    try:
        PyImGui.selectable(
            f'{marker}##template_group_drag_handle_{group_key}',
            bool(is_source or is_target),
            selectable_flags,
            (TEMPLATE_GROUP_DRAG_HANDLE_WIDTH, 0.0),
        )
    except Exception:
        PyImGui.selectable(f'{marker}##template_group_drag_handle_{group_key}', bool(is_source or is_target))
    _show_item_tooltip('Drag to reorder profession groups.')

    try:
        if PyImGui.is_item_active() and PyImGui.is_mouse_dragging(0, 0.0):
            _template_group_drag_from = group_key
        if _template_group_drag_from and PyImGui.is_item_hovered():
            _template_group_drag_to = group_key
    except Exception:
        pass


def _finish_template_group_drag(visible_order: list[str]) -> None:
    global _template_group_drag_from, _template_group_drag_to, _status
    try:
        mouse_down = bool(PyImGui.is_mouse_down(0))
    except Exception:
        mouse_down = False
    if mouse_down or not _template_group_drag_from:
        return

    source_key = _template_group_drag_from
    target_key = _template_group_drag_to or source_key
    if source_key in visible_order and target_key in visible_order and source_key != target_key:
        new_order = list(visible_order)
        moved = new_order.pop(new_order.index(source_key))
        insert_at = new_order.index(target_key) if target_key in new_order else len(new_order)
        if visible_order.index(target_key) > visible_order.index(source_key):
            insert_at += 1
        new_order.insert(min(insert_at, len(new_order)), moved)
        _save_template_group_order(new_order)
        _status = 'Template profession order updated.'

    _template_group_drag_from = ''
    _template_group_drag_to = ''


def _draw_template_group_selector(config: HeroTeamConfig) -> bool:
    global _selected_template_id, _template_group_drag_from, _template_group_drag_to
    groups: dict[str, tuple[object, list[object]]] = {}
    for template in config.templates:
        group = classify_template_profession(template)
        if group.group_key not in groups:
            groups[group.group_key] = (group, [])
        groups[group.group_key][1].append(template)

    ordered_groups = sorted(
        groups.values(),
        key=lambda entry: (entry[0].sort_order, str(entry[0].label).lower()),
    )
    groups_by_key = {
        str(getattr(group, 'group_key', '') or ''): (group, templates)
        for group, templates in ordered_groups
    }
    visible_group_order = _visible_template_group_order(ordered_groups)
    ordered_groups = [groups_by_key[key] for key in visible_group_order if key in groups_by_key]
    selectable_flags = getattr(getattr(PyImGui, 'SelectableFlags', None), 'NoFlag', 0)

    PyImGui.separator()
    PyImGui.text('Templates')
    any_group_open = False
    for group, templates in ordered_groups:
        group_key = str(getattr(group, 'group_key', '') or '')
        templates.sort(key=lambda template: str(getattr(template, 'name', '') or '').lower())
        contains_selected = any(template.template_id == _selected_template_id for template in templates)
        is_drag_source = _template_group_drag_from == group_key
        is_drop_target = bool(_template_group_drag_from and _template_group_drag_to == group_key and not is_drag_source)
        _draw_template_group_drag_handle(group_key, is_drag_source, is_drop_target, selectable_flags)
        _same_line(4)
        drop_marker = ' <DROP>' if is_drop_target else ''
        header_label = f'{group.label} ({len(templates)}){drop_marker}##template_group_{group.group_key}'
        header_open = _collapsing_header_colored(
            header_label,
            _profession_group_header_color(group),
            default_open=contains_selected,
        )
        if _template_group_drag_from:
            try:
                if PyImGui.is_item_hovered():
                    _template_group_drag_to = group_key
            except Exception:
                pass
        if not header_open:
            if contains_selected:
                _selected_template_id = ''
                _clear_code_edit()
            continue
        any_group_open = True
        try:
            PyImGui.indent(8.0)
        except Exception:
            pass
        for template in templates:
            template_name = str(template.name or 'New Template')
            selected = template.template_id == _selected_template_id
            if selected:
                PyImGui.push_style_color(PyImGui.ImGuiCol.Text, UI_COLOR_SUCCESS)
            try:
                clicked = bool(
                    PyImGui.selectable(
                        f'{template_name}##template_group_item_{template.template_id}',
                        selected,
                        selectable_flags,
                        (0.0, 0.0),
                    )
                )
            except Exception:
                clicked = bool(
                    PyImGui.selectable(
                        f'{template_name}##template_group_item_{template.template_id}',
                        selected,
                    )
                )
            finally:
                if selected:
                    PyImGui.pop_style_color(1)
            if clicked and template.template_id != _selected_template_id:
                _selected_template_id = template.template_id
                _clear_code_edit()
            _show_template_tooltip(template)
        try:
            PyImGui.unindent(8.0)
        except Exception:
            pass
    _finish_template_group_drag(visible_group_order)
    return any_group_open


def _target_label(target) -> str:
    return f'H{int(target.hero_index)}: {target.hero_name}'


def _draw_template_apply_control(config: HeroTeamConfig, template, stacked: bool = False) -> None:
    global _selected_apply_target_hero_id, _status
    targets = current_party_hero_targets_for_template(config, template)
    row_y = None
    if stacked:
        PyImGui.text('Apply to')
    else:
        row_y = _cursor_pos_y()
        _rename_row_text('Apply to', row_y)
        _same_line(8)

    if not targets:
        preview = summarize_skill_template(template)
        if preview is None or int(preview.primary_profession_id or 0) <= 0:
            if stacked:
                _colored_text('Template code could not be parsed.', 'error', wrapped=True)
            else:
                _row_colored_text('Template code could not be parsed.', row_y, 'error')
        else:
            if stacked:
                _colored_text('<No matching current-party heroes>', 'warning', wrapped=True)
            else:
                _row_colored_text('<No matching current-party heroes>', row_y, 'warning')
        return

    target_ids = [int(target.hero_id) for target in targets]
    if _selected_apply_target_hero_id not in target_ids:
        preferred_id = int(getattr(template, 'hero_id', 0) or 0)
        _selected_apply_target_hero_id = preferred_id if preferred_id in target_ids else target_ids[0]

    try:
        current = target_ids.index(_selected_apply_target_hero_id)
    except ValueError:
        current = 0
    labels = [_target_label(target) for target in targets]
    if not stacked:
        _set_cursor_pos_y(row_y)
    try:
        PyImGui.set_next_item_width(-1 if stacked else APPLY_TARGET_WIDTH)
    except Exception:
        pass
    selected = _combo(f'##apply_template_target_{template.template_id}', current, labels)
    if 0 <= selected < len(targets):
        target = targets[selected]
        _selected_apply_target_hero_id = int(target.hero_id)
        _show_item_tooltip(_target_label(target))
    else:
        target = targets[current]

    if not stacked:
        _same_line(8)
        _set_cursor_pos_y(row_y)
    running = _operation_running()
    can_apply = not running and not _is_editing_code(template.template_id)
    if _button_colored_disabled(
        f'Apply Template##apply_template_to_current_hero_{template.template_id}',
        running,
        'success' if can_apply else 'warning',
        APPLY_TEMPLATE_BUTTON_WIDTH,
        24,
    ):
        if _is_editing_code(template.template_id):
            _status = 'Finish code edit before applying template.'
            return
        result = apply_template_to_current_party_hero(
            config,
            template,
            target_hero_id=int(target.hero_id),
            target_hero_index=int(target.hero_index),
        )
        _status = result.message
    tooltip = 'Team load is running.' if running else 'Apply selected saved template to the selected current party hero.'
    _show_item_tooltip(tooltip)


def _show_team_tooltip(config: HeroTeamConfig, team) -> None:
    tooltip_open = _begin_tooltip_if_hovered()
    if not tooltip_open:
        return
    try:
        if team is None:
            PyImGui.text('No team selected.')
            return

        PyImGui.text(str(team.name or 'Team'))
        row_count = 0
        for slot_index, slot in enumerate(team.slots[:HERO_SLOT_COUNT]):
            hero_id = int(slot.hero_id or 0)
            if hero_id <= 0:
                continue

            if row_count > 0:
                try:
                    PyImGui.separator()
                except Exception:
                    pass
            row_count += 1

            hero_name = hero_display_name(config, hero_id)
            template_code, template_name = resolve_slot_template_code(slot, config.templates)
            if not template_code:
                PyImGui.text(f'H{slot_index + 1}: {hero_name}')
                PyImGui.text('No template')
                continue

            title = f'H{slot_index + 1}: {hero_name} - {template_name or "Template"}'
            template = get_template(config, slot.template_id)
            if template is not None and not str(slot.template_code or '').strip():
                _draw_template_preview_or_fallback(template, title=title, compact=True)
            else:
                _draw_template_preview_or_fallback(template_code, template_name=template_name, title=title, compact=True)

        if row_count <= 0:
            PyImGui.text('No heroes configured.')
    finally:
        _end_tooltip()


def _combo(label: str, index: int, values: list[str]) -> int:
    if not values:
        values = ['']
    index = max(0, min(int(index), len(values) - 1))
    try:
        return int(PyImGui.combo(label, index, values))
    except Exception:
        return index


def _combo_with_popup_style(label: str, index: int, values: list[str]) -> int:
    pushed = _push_combo_popup_style()
    try:
        return _combo(label, index, values)
    finally:
        _pop_style_colors(pushed)


def _init_window_persistence_once() -> bool:
    global _window_ini_ready, _window_ini_key, _floating_ui_ini_key
    if _window_ini_ready:
        return bool(_window_ini_key and _floating_ui_ini_key)

    _window_ini_key = IniManager().ensure_key(WINDOW_INI_PATH, WINDOW_INI_FILE)
    if not _window_ini_key:
        return False

    IniManager().load_once(_window_ini_key)

    _floating_ui_ini_key = IniManager().ensure_key(WINDOW_INI_PATH, FLOATING_UI_INI_FILE)
    if not _floating_ui_ini_key:
        return False

    _window_ini_ready = True
    return True


def _get_floating_icon_path() -> str:
    return os.path.join(Py4GW.Console.get_projects_path(), MODULE_ICON)


def _set_main_window_visible(visible: bool, *, persist: bool = False, expand_on_show: bool = True) -> None:
    global _show_main_window, _expand_main_window_on_next_show
    _show_main_window = bool(visible)
    if _show_main_window and expand_on_show:
        _expand_main_window_on_next_show = True
    if _floating_button is not None:
        _floating_button.set_visible(
            _show_main_window,
            persist=persist,
            invoke_callback=False,
        )


def _on_floating_icon_visibility_toggled(visible: bool) -> None:
    _set_main_window_visible(bool(visible), persist=False, expand_on_show=bool(visible))


def _ensure_floating_ui():
    global _floating_button, _show_main_window
    if _floating_button is None:
        _floating_button = ImGui.FloatingIcon(
            icon_path=_get_floating_icon_path(),
            window_id=FLOATING_ICON_WINDOW_ID,
            window_name=FLOATING_ICON_WINDOW_NAME,
            tooltip_visible='Hide Hero Team Manager window',
            tooltip_hidden='Show Hero Team Manager window',
            visible=bool(_show_main_window),
            toggle_ini_key=_floating_ui_ini_key,
            toggle_var_name='show_main_window',
            toggle_default=True,
            on_toggle=_on_floating_icon_visibility_toggled,
        )
        _floating_button.load_visibility()
        _show_main_window = bool(_floating_button.visible)
    return _floating_button


def _begin_window() -> bool:
    global _expand_main_window_on_next_show
    if _expand_main_window_on_next_show:
        try:
            PyImGui.set_next_window_collapsed(False, PyImGui.ImGuiCond.Always)
        except Exception:
            pass
        _expand_main_window_on_next_show = False

    try:
        PyImGui.set_next_window_size((720, 620), PyImGui.ImGuiCond.FirstUseEver)
    except Exception:
        pass

    persistence_ready = _init_window_persistence_once()
    if persistence_ready:
        IniManager().begin_window_config(_window_ini_key)

    try:
        expanded = bool(PyImGui.begin(MODULE_NAME, PyImGui.WindowFlags.NoFlag))
    except TypeError:
        expanded = bool(PyImGui.begin(MODULE_NAME, True, PyImGui.WindowFlags.NoFlag))

    if persistence_ready:
        IniManager().track_window_collapsed(_window_ini_key, expanded)
        if expanded:
            IniManager().mark_begin_success(_window_ini_key)

    return expanded


def _end_window() -> None:
    if _window_ini_key:
        ImGui.End(_window_ini_key)
    else:
        PyImGui.end()


def _draw_tab_bar() -> None:
    global _active_tab
    for key, label in [('teams', 'Teams'), ('templates', 'Templates')]:
        if key != 'teams':
            _same_line(4)
        active = key == _active_tab
        clicked = (
            _button_selected_tab(f'{label}##tab_{key}', 96, 24)
            if active
            else _button(f'{label}##tab_{key}', 96, 24)
        )
        if clicked:
            _active_tab = key
    PyImGui.separator()


def _team_combo(config: HeroTeamConfig, disabled: bool = False) -> None:
    team_ids = [team.team_id for team in config.teams]
    labels = [team.name for team in config.teams]
    if not team_ids:
        return
    try:
        current = team_ids.index(config.active_team_id)
    except ValueError:
        current = 0
    current = max(0, min(current, len(team_ids) - 1))
    selected = current
    combo_open = False
    began_disabled = _begin_disabled(disabled)
    try:
        combo_flags = getattr(getattr(PyImGui, 'ImGuiComboFlags', None), 'NoFlag', 0)
        selectable_flags = getattr(getattr(PyImGui, 'SelectableFlags', None), 'NoFlag', 0)
        combo_open = bool(PyImGui.begin_combo('Team##hero_team_selector', labels[current], combo_flags))
        if combo_open:
            for option_index, label in enumerate(labels):
                if PyImGui.selectable(
                    f'{label}##hero_team_option_{team_ids[option_index]}',
                    option_index == current,
                    selectable_flags,
                    (0.0, 0.0),
                ):
                    selected = option_index
                _show_team_tooltip(config, config.teams[option_index])
        else:
            _show_team_tooltip(config, config.teams[current])
    except Exception:
        selected = _combo('Team##hero_team_selector', current, labels)
        if 0 <= selected < len(config.teams):
            _show_team_tooltip(config, config.teams[selected])
    finally:
        if combo_open:
            try:
                PyImGui.end_combo()
            except Exception:
                pass
        _end_disabled(began_disabled)
    if not disabled and 0 <= selected < len(team_ids):
        selected_team_id = team_ids[selected]
        if selected_team_id != config.active_team_id:
            config.active_team_id = selected_team_id


def _load_template_filter_once() -> None:
    global _template_filter_loaded, _only_show_compatible_templates
    if _template_filter_loaded:
        return
    if not _init_window_persistence_once():
        return
    _template_filter_loaded = True
    _only_show_compatible_templates = bool(
        IniManager().read_bool(
            _window_ini_key,
            TEMPLATE_FILTER_SECTION,
            TEMPLATE_FILTER_KEY,
            True,
        )
    )


def _template_filter_enabled() -> bool:
    _load_template_filter_once()
    return bool(_only_show_compatible_templates)


def _save_template_filter_preference() -> None:
    if _init_window_persistence_once():
        IniManager().write_key(
            _window_ini_key,
            TEMPLATE_FILTER_SECTION,
            TEMPLATE_FILTER_KEY,
            'True' if _only_show_compatible_templates else 'False',
        )


def _draw_template_filter_toggle() -> None:
    global _only_show_compatible_templates
    _load_template_filter_once()
    try:
        enabled = bool(
            PyImGui.checkbox(
                'Only show compatible templates##hero_team_template_filter',
                bool(_only_show_compatible_templates),
            )
        )
    except Exception:
        return
    _show_item_tooltip('Filters hero-row template dropdowns when the selected hero profession is known.')
    if enabled != bool(_only_show_compatible_templates):
        _only_show_compatible_templates = enabled
        _save_template_filter_preference()


def _current_party_hero_primary_professions(config: HeroTeamConfig) -> dict[int, int]:
    try:
        targets = current_party_hero_targets(config, only_owned=True)
    except Exception:
        return {}

    professions: dict[int, int] = {}
    for target in targets:
        try:
            hero_id = int(getattr(target, 'hero_id', 0) or 0)
            primary_id = int(getattr(target, 'primary_profession_id', 0) or 0)
        except Exception:
            continue
        if hero_id > 0 and primary_id > 0:
            professions[hero_id] = primary_id
    return professions


def _template_primary_profession_id(template, preview_cache: dict[str, object | None]) -> int:
    template_id = str(getattr(template, 'template_id', '') or '')
    if template_id not in preview_cache:
        preview_cache[template_id] = summarize_skill_template(template)
    preview = preview_cache.get(template_id)
    try:
        return int(getattr(preview, 'primary_profession_id', 0) or 0)
    except Exception:
        return 0


def _template_options_for_slot(
    config: HeroTeamConfig,
    template_id: str,
    hero_id: int,
    hero_primary_professions: dict[int, int],
    preview_cache: dict[str, object | None],
) -> list[tuple[str, str, object | None]]:
    selected_template_id = str(template_id or '')
    target_primary_id = int(hero_primary_professions.get(int(hero_id or 0), 0) or 0)
    filter_active = bool(_template_filter_enabled() and target_primary_id > 0)
    options: list[tuple[str, str, object | None]] = [('', '<None>', None)]

    for template in config.templates:
        current_template_id = str(getattr(template, 'template_id', '') or '')
        include_template = True
        if filter_active:
            include_template = _template_primary_profession_id(template, preview_cache) == target_primary_id
            if not include_template and current_template_id == selected_template_id:
                include_template = True
        if include_template:
            options.append((current_template_id, str(getattr(template, 'name', '') or 'Template'), template))

    if selected_template_id and all(option_id != selected_template_id for option_id, _label, _template in options):
        selected_template = get_template(config, selected_template_id)
        if selected_template is not None:
            options.append((selected_template_id, str(selected_template.name or 'Template'), selected_template))
    return options


def _template_combo_for_slot(
    config: HeroTeamConfig,
    template_id: str,
    label: str,
    hero_id: int = 0,
    hero_primary_professions: dict[int, int] | None = None,
    preview_cache: dict[str, object | None] | None = None,
) -> str:
    hero_primary_professions = hero_primary_professions or {}
    preview_cache = preview_cache if preview_cache is not None else {}
    options = _template_options_for_slot(
        config,
        template_id,
        hero_id,
        hero_primary_professions,
        preview_cache,
    )
    template_ids = [option_id for option_id, _option_label, _template in options]
    labels = [option_label for _option_id, option_label, _template in options]
    try:
        current = template_ids.index(template_id)
    except ValueError:
        current = 0
    current = max(0, min(current, len(template_ids) - 1))
    selected = current
    combo_open = False
    use_fallback_combo = False
    pushed_combo_style = _push_combo_popup_style()
    try:
        combo_flags = getattr(getattr(PyImGui, 'ImGuiComboFlags', None), 'NoFlag', 0)
        selectable_flags = getattr(getattr(PyImGui, 'SelectableFlags', None), 'NoFlag', 0)
        combo_open = bool(PyImGui.begin_combo(label, labels[current], combo_flags))
        if combo_open:
            for option_index, option_label in enumerate(labels):
                try:
                    clicked = bool(
                        PyImGui.selectable(
                            f'{option_label}##template_slot_option_{label}_{option_index}',
                            option_index == current,
                            selectable_flags,
                            (0.0, 0.0),
                        )
                    )
                except Exception:
                    clicked = bool(
                        PyImGui.selectable(
                            f'{option_label}##template_slot_option_{label}_{option_index}',
                            option_index == current,
                        )
                    )
                if clicked:
                    selected = option_index
                option_template = options[option_index][2]
                if option_template is not None:
                    _show_template_tooltip(option_template)
        elif current > 0:
            selected_template = options[current][2]
            if selected_template is not None:
                _show_template_tooltip(selected_template)
    except Exception:
        use_fallback_combo = True
    finally:
        if combo_open:
            try:
                PyImGui.end_combo()
            except Exception:
                pass
        _pop_style_colors(pushed_combo_style)
    if use_fallback_combo:
        selected = _combo_with_popup_style(label, current, labels)
    return template_ids[selected] if 0 <= selected < len(template_ids) else ''


def _behavior_combo_for_slot(behavior: int, label: str) -> int:
    try:
        current = HERO_BEHAVIOR_VALUES.index(int(behavior))
    except (ValueError, TypeError):
        current = 0
    selected = _combo_with_popup_style(label, current, HERO_BEHAVIOR_LABELS)
    if 0 <= selected < len(HERO_BEHAVIOR_VALUES):
        return int(HERO_BEHAVIOR_VALUES[selected])
    return int(HERO_BEHAVIOR_VALUES[0])


def _content_width(default: float) -> float:
    try:
        return max(0.0, float(PyImGui.get_content_region_avail()[0]))
    except Exception:
        return float(default)


def _begin_child(child_id: str, width: float = 0.0, height: float = 0.0, border: bool = False) -> bool:
    try:
        return bool(
            PyImGui.begin_child(
                child_id,
                (float(width), float(height)),
                bool(border),
                PyImGui.WindowFlags.NoFlag,
            )
        )
    except Exception:
        try:
            return bool(PyImGui.begin_child(child_id, (float(width), float(height)), bool(border)))
        except Exception:
            try:
                return bool(PyImGui.begin_child(child_id, int(width), int(height), bool(border)))
            except Exception:
                return False


def _end_child() -> None:
    try:
        PyImGui.end_child()
    except Exception:
        pass


def _draw_slot_label(row_index: int, hero_id: int, warnings: list[object]) -> None:
    label = f'H{row_index + 1}'
    severity = _row_warning_severity(warnings) if warnings else 'info'
    if severity == 'error':
        _colored_text(label, 'error')
    elif severity == 'warning':
        _colored_text(label, 'warning')
    elif int(hero_id or 0) <= 0:
        _tinted_text(label, UI_COLOR_SLOT_EMPTY)
    else:
        _tinted_text(label, UI_COLOR_SLOT_ACTIVE)

    if warnings:
        details = '\n'.join(f'- {getattr(warning, "message", "")}' for warning in warnings)
        _show_item_tooltip(details)
    elif int(hero_id or 0) <= 0:
        _show_item_tooltip('Empty slot will be skipped until a hero is chosen.')


def _draw_alias_editor(
    config: HeroTeamConfig,
    row_index: int,
    hero_id: int,
    disabled: bool = False,
    alias_color: tuple[float, float, float, float] | None = None,
) -> None:
    hero_id = int(hero_id or 0)
    if hero_id <= 0:
        _muted_text('<Empty>')
        _same_line(8)
        _tinted_text('Skipped', UI_COLOR_SKIPPED_TEXT)
        _show_item_tooltip('Empty slot will be skipped until a hero is chosen.')
        return

    remaining_width = _content_width(TEAM_ROW_NAME_WIDTH)
    input_width = max(48.0, remaining_width - ALIAS_RESET_BUTTON_WIDTH - 6.0)
    try:
        PyImGui.set_next_item_width(input_width)
    except Exception:
        pass

    default_name = hero_default_name(hero_id)
    display_name = hero_display_name(config, hero_id)
    previous_alias = hero_alias(config, hero_id)
    pushed_alias_color = 0
    if alias_color is not None:
        try:
            PyImGui.push_style_color(PyImGui.ImGuiCol.Text, alias_color)
            pushed_alias_color = 1
        except Exception:
            pushed_alias_color = 0
    began_disabled = _begin_disabled(disabled)
    try:
        alias = _input_text(f'##hero_alias_{row_index}_{hero_id}', display_name, 64)
    finally:
        _end_disabled(began_disabled)
        _pop_style_colors(pushed_alias_color)
    if not disabled:
        new_alias = set_hero_alias(config, hero_id, alias)
        if new_alias != previous_alias:
            _mark_dirty('Hero alias updated. Click Save to persist.')
    tooltip = f'Default: {default_name}'
    if hero_alias(config, hero_id):
        tooltip = f'{tooltip}\nAlias changes the account-level display name only.'
    if disabled:
        tooltip = f'{tooltip}\nTeam load is running.'
    _show_item_tooltip(tooltip)

    _same_line(4)
    if _button_disabled(f'x##reset_alias_{row_index}_{hero_id}', disabled, int(ALIAS_RESET_BUTTON_WIDTH), 0):
        had_alias = bool(hero_alias(config, hero_id))
        clear_hero_alias(config, hero_id)
        if had_alias:
            _mark_dirty('Hero alias reset. Click Save to persist.')
    _show_item_tooltip('Reset alias')


def _draw_choose_hero_first_message() -> None:
    _padded_tinted_text('Choose hero first', UI_COLOR_EMPTY_CONTROL_TEXT)


def _draw_operation_status() -> None:
    global _operation, _status
    if _operation is None:
        return
    _operation.tick()
    _status = _operation.message
    if _operation.done:
        _operation = None


def _row_warnings(preflight, row_index: int) -> list[object]:
    if preflight is None:
        return []
    return list(getattr(preflight, 'row_warnings', {}).get(int(row_index), []))


def _draw_row_warnings(warnings: list[object]) -> None:
    if not warnings:
        return
    severity = _row_warning_severity(warnings)
    message = str(getattr(warnings[0], 'message', '') or '')
    if len(warnings) > 1:
        message = f'{message} (+{len(warnings) - 1})'
    prefix = '! ' if severity in {'warning', 'error'} else ''
    _warning_text(f'{prefix}{message}', severity)
    details = '\n'.join(f'- {getattr(warning, "message", "")}' for warning in warnings)
    _show_item_tooltip(details)


def _preflight_warning_count(preflight) -> int:
    if preflight is None:
        return 0
    return sum(
        1
        for warnings in getattr(preflight, 'row_warnings', {}).values()
        for warning in warnings
        if getattr(warning, 'severity', 'warning') != 'info'
    )


def _draw_preflight_summary(preflight) -> None:
    if preflight is None:
        return
    blocking = list(getattr(preflight, 'blocking_messages', []) or [])
    if blocking:
        _warning_text(f'Load blocked: {" ".join(blocking)}', 'error')
        return
    warnings = [
        warning
        for warning in (getattr(preflight, 'warnings', []) or [])
        if warning != 'Load will leave the current party before loading this team.'
    ]
    if warnings:
        _warning_text(f'Preflight: {" ".join(warnings)}', 'warning')


def _save_or_confirm(config: HeroTeamConfig, *, commit_code_edit: bool = False) -> None:
    dirty = _sync_dirty_state(config)
    if dirty or (commit_code_edit and _active_code_edit_changed(config)):
        _request_confirmation(
            'save_changes',
            'Save Changes',
            'These unsaved Hero Team Manager changes will be saved.',
            {'commit_code_edit': '1' if commit_code_edit else ''},
        )
        return

    if commit_code_edit and _commit_active_code_edit(config):
        _mark_dirty('Template code updated. Saving.')
    _save_status()


def _run_confirmed_action(config: HeroTeamConfig) -> None:
    global _selected_template_id, _status
    if _confirm_action == 'save_changes':
        if _confirm_payload.get('commit_code_edit') == '1' and _commit_active_code_edit(config):
            _mark_dirty('Template code updated. Saving.')
        _save_status()
        return

    if _confirm_action == 'delete_team':
        team_id = str(_confirm_payload.get('team_id', '') or config.active_team_id)
        if delete_team(config, team_id):
            _mark_dirty('Team deleted. Click Save to persist.')
        else:
            _status = 'Keep at least one team.'
        return

    if _confirm_action == 'delete_template':
        template_id = str(_confirm_payload.get('template_id', '') or _selected_template_id)
        if template_id and delete_template(config, template_id):
            if _selected_template_id == template_id:
                _selected_template_id = ''
            _clear_code_edit()
            _mark_dirty('Template deleted. Click Save to persist.')
        else:
            _status = 'No template deleted.'
        return

    if _confirm_action == 'save_current_team':
        team_id = str(_confirm_payload.get('team_id', '') or config.active_team_id)
        team_name = str(_confirm_payload.get('team_name', '') or '')
        try:
            saved_team, count = save_current_party_as_team(config, team_id=team_id, team_name=team_name)
            if count <= 0:
                _status = 'No current party heroes found; team unchanged.'
            else:
                save_config(config)
                _clear_dirty(f'Saved {count} current heroes to {saved_team.name}.')
        except Exception as exc:
            _status = f'Save current team failed: {exc}'


def _confirm_action_severity() -> str:
    if _confirm_action in {'delete_team', 'delete_template'}:
        return 'error'
    if _confirm_action in {'save_changes', 'save_current_team'}:
        return 'warning'
    return 'info'


def _draw_confirmation_popup(config: HeroTeamConfig) -> None:
    global _confirm_popup_requested
    if not _confirm_action:
        return

    if _confirm_popup_requested:
        PyImGui.open_popup(CONFIRM_POPUP_ID)
        _confirm_popup_requested = False

    try:
        PyImGui.set_next_window_size((380, 0), PyImGui.ImGuiCond.Always)
    except Exception:
        pass
    if not PyImGui.begin_popup_modal(CONFIRM_POPUP_ID, True, PyImGui.WindowFlags.AlwaysAutoResize):
        return

    severity = _confirm_action_severity()
    _colored_text(_confirm_title, severity)
    PyImGui.separator()
    try:
        if severity in {'error', 'warning'}:
            _colored_text(_confirm_message, severity, wrapped=True)
        else:
            PyImGui.text_wrapped(_confirm_message)
    except Exception:
        PyImGui.text(_confirm_message)
    PyImGui.spacing()

    width = _content_width(360.0)
    button_width = int(max(80.0, (width - 8.0) / 2.0))
    if _button_colored('Confirm##confirm_hero_team_action', severity, button_width, 24):
        _run_confirmed_action(config)
        _clear_confirmation()
        PyImGui.close_current_popup()
    _same_line(8)
    if _button('Cancel##cancel_hero_team_action', button_width, 24):
        _clear_confirmation()
        PyImGui.close_current_popup()

    PyImGui.end_popup_modal()


def _draw_team_rows(config: HeroTeamConfig, disabled: bool = False, preflight=None) -> None:
    team = get_team(config)
    if team is None:
        return

    slots = ensure_team_slots(team)
    labels = hero_labels(config)
    hero_primary_professions = _current_party_hero_primary_professions(config)
    template_preview_cache: dict[str, object | None] = {}
    PyImGui.separator()
    flags = int(
        PyImGui.TableFlags.RowBg
        | PyImGui.TableFlags.BordersInnerH
        | PyImGui.TableFlags.BordersInnerV
        | PyImGui.TableFlags.SizingStretchProp
        | PyImGui.TableFlags.NoSavedSettings
    )
    if PyImGui.begin_table('HeroTeamRows', 5, flags):
        PyImGui.table_setup_column('Slot', PyImGui.TableColumnFlags.WidthFixed, TEAM_ROW_SLOT_WIDTH)
        PyImGui.table_setup_column('Alias', PyImGui.TableColumnFlags.WidthFixed, TEAM_ROW_NAME_WIDTH)
        PyImGui.table_setup_column('Template', PyImGui.TableColumnFlags.WidthStretch, TEAM_ROW_TEMPLATE_WEIGHT)
        PyImGui.table_setup_column('Choose Hero', PyImGui.TableColumnFlags.WidthStretch, TEAM_ROW_HERO_WEIGHT)
        PyImGui.table_setup_column('Hero Behavior', PyImGui.TableColumnFlags.WidthFixed, TEAM_ROW_BEHAVIOR_WIDTH)
        _draw_team_table_headers()

        for index, slot in enumerate(slots):
            hero_id = int(slot.hero_id or 0)
            warnings = _row_warnings(preflight, index)
            PyImGui.table_next_row()
            if hero_id <= 0:
                _set_current_table_row_bg(UI_COLOR_ROW_EMPTY_BG)
            elif warnings:
                severity = _row_warning_severity(warnings)
                if severity == 'error':
                    _set_current_table_row_bg(UI_COLOR_ROW_ERROR_BG)
                elif severity == 'warning':
                    _set_current_table_row_bg(UI_COLOR_ROW_WARNING_BG)
                else:
                    _set_current_table_row_bg(UI_COLOR_ROW_ACTIVE_BG)
            else:
                _set_current_table_row_bg(UI_COLOR_ROW_ACTIVE_BG)

            PyImGui.table_next_column()
            _draw_slot_label(index, hero_id, warnings)

            PyImGui.table_next_column()
            alias_color = _profession_color(hero_primary_professions.get(hero_id, 0)) if hero_id > 0 else None
            _draw_alias_editor(config, index, hero_id, disabled=disabled, alias_color=alias_color)
            if hero_id > 0:
                _draw_row_warnings(warnings)

            PyImGui.table_next_column()
            if hero_id <= 0:
                _draw_choose_hero_first_message()
            elif config.templates:
                try:
                    PyImGui.set_next_item_width(-1)
                except Exception:
                    pass
                previous_template_id = str(slot.template_id or '')
                began_disabled = _begin_disabled(disabled)
                try:
                    selected_template_id = _template_combo_for_slot(
                        config,
                        slot.template_id,
                        f'##template_slot_{index}',
                        hero_id,
                        hero_primary_professions,
                        template_preview_cache,
                    )
                finally:
                    _end_disabled(began_disabled)
                if not disabled and selected_template_id != previous_template_id:
                    slot.template_id = selected_template_id
                    _mark_dirty('Team slot template changed. Click Save to persist.')
            else:
                _muted_text('<No templates>')

            PyImGui.table_next_column()
            hero_index = HERO_ID_TO_INDEX.get(hero_id, 0)
            try:
                PyImGui.set_next_item_width(-1)
            except Exception:
                pass
            empty_combo_style = _push_empty_combo_style() if hero_id <= 0 else 0
            began_disabled = _begin_disabled(disabled)
            try:
                selected_hero_index = _combo_with_popup_style(f'##hero_slot_{index}', hero_index, labels)
            finally:
                _end_disabled(began_disabled)
                _pop_style_colors(empty_combo_style)
            selected_hero_id = int(HERO_IDS[selected_hero_index])
            if not disabled and selected_hero_id != hero_id:
                slot.hero_id = selected_hero_id
                _mark_dirty('Team slot hero changed. Click Save to persist.')
            _show_item_tooltip(labels[selected_hero_index])

            PyImGui.table_next_column()
            if hero_id <= 0:
                _draw_choose_hero_first_message()
            else:
                try:
                    PyImGui.set_next_item_width(-1)
                except Exception:
                    pass
                try:
                    previous_behavior = int(slot.behavior)
                except (TypeError, ValueError):
                    previous_behavior = HERO_BEHAVIOR_DONT_CHANGE
                began_disabled = _begin_disabled(disabled)
                try:
                    selected_behavior = _behavior_combo_for_slot(slot.behavior, f'##behavior_slot_{index}')
                finally:
                    _end_disabled(began_disabled)
                if not disabled and selected_behavior != previous_behavior:
                    slot.behavior = selected_behavior
                    _mark_dirty('Team slot behavior changed. Click Save to persist.')
                try:
                    behavior_index = HERO_BEHAVIOR_VALUES.index(int(slot.behavior))
                except (ValueError, TypeError):
                    behavior_index = 0
                _show_item_tooltip(HERO_BEHAVIOR_LABELS[behavior_index])

            if not disabled and slot.hero_id == 0:
                if slot.template_id or slot.template_code or slot.behavior != HERO_BEHAVIOR_DONT_CHANGE:
                    slot.template_id = ''
                    slot.template_code = ''
                    slot.behavior = HERO_BEHAVIOR_DONT_CHANGE
                    _mark_dirty('Empty team slot cleared. Click Save to persist.')

        PyImGui.end_table()


def _draw_teams_tab(config: HeroTeamConfig) -> None:
    global _active_tab, _operation, _status
    running = _operation_running()
    _team_combo(config, disabled=running)
    preflight = build_load_preflight(
        config,
        config.active_team_id,
        include_runtime=True,
        leave_party_first=True,
        clear_existing=True,
    )
    warning_count = _preflight_warning_count(preflight)
    plan = preflight.plan

    if _button_disabled('New##new_team', running, 72, 24):
        add_team(config)
        _mark_dirty('New team created. Click Save to persist.')
    _same_line()
    if _button_disabled('Duplicate##duplicate_team', running, 90, 24):
        if duplicate_team(config, config.active_team_id) is not None:
            _mark_dirty('Team duplicated. Click Save to persist.')
        else:
            _status = 'No team duplicated.'
    _same_line()
    if _button_colored_disabled('Delete##delete_team', running, 'error', 72, 24):
        _request_confirmation(
            'delete_team',
            'Delete Team',
            'This saved team will be removed.',
            {'team_id': str(config.active_team_id or '')},
        )
    _same_line()
    if _button_colored_disabled('Save##save_team', running, 'success', 72, 24):
        _save_or_confirm(config)
    _same_line()
    load_disabled = running or not bool(getattr(preflight, 'can_load', True))
    if _button_disabled('Load Team##load_team', load_disabled, 96, 24):
        try:
            _operation = create_apply_operation(
                config,
                config.active_team_id,
                leave_party_first=True,
                clear_existing=True,
            )
            _status = 'Starting team load from unsaved changes.' if _dirty else 'Starting team load.'
        except Exception as exc:
            _status = f'Load start failed: {exc}'
    if running:
        _show_item_tooltip('Team load is already running.')
    elif not bool(getattr(preflight, 'can_load', True)):
        _show_item_tooltip('\n'.join(getattr(preflight, 'blocking_messages', []) or ['Load is blocked.']))

    if not config.templates:
        PyImGui.separator()
        _colored_text('No templates saved for assignment.', 'warning')
        _same_line(8)
        if _button('Templates##open_templates_from_teams', 96, 24):
            _active_tab = 'templates'

    team = get_team(config)
    if team is None:
        _colored_text('No team selected.', 'error')
        return

    PyImGui.separator()
    team_name, rename_applied = _draw_rename_control(
        'team',
        team.team_id,
        team.name,
        'New Hero Team',
        'Team',
        disabled=running,
    )
    if rename_applied:
        previous_name = team.name
        team.name = team_name
        try:
            save_config(config)
            _clear_rename()
            _clear_dirty('Team renamed and saved.')
        except Exception as exc:
            team.name = previous_name
            _status = f'Team rename save failed: {exc}'
    else:
        team.name = team_name

    if _button_disabled('Save Current Team##save_current_party', running, 144, 24):
        _request_confirmation(
            'save_current_team',
            'Save Current Team',
            'The selected saved team will be overwritten with the current party/team state.',
            {'team_id': str(config.active_team_id or ''), 'team_name': str(team.name or '')},
        )
    _same_line(8)
    dedupe_clicked = (
        _button_colored_disabled('Dedupe##dedupe_team', running, 'warning', 88, 24)
        if plan.skipped_duplicates
        else _button_disabled('Dedupe##dedupe_team', running, 88, 24)
    )
    if dedupe_clicked:
        count, _cleared = dedupe_team_slots(team)
        if count > 0:
            _mark_dirty(f'Removed {count} duplicate slots. Click Save to persist.')
        else:
            _status = 'No duplicate slots found.'

    _same_line(8)
    heroes_severity = 'success' if bool(getattr(preflight, 'can_load', True)) and warning_count <= 0 else 'info'
    _inline_status_text(f'Heroes {len(plan.slots)}', heroes_severity)
    if plan.skipped_empty:
        _same_line(8)
        _inline_status_text(f'Empty {len(plan.skipped_empty)}', 'info')
    if plan.skipped_duplicates:
        _same_line(8)
        _inline_status_text(f'Duplicates {len(plan.skipped_duplicates)}', 'warning')
    if plan.truncated_slots:
        _same_line(8)
        _inline_status_text(f'Truncated {len(plan.truncated_slots)}', 'warning')
    if warning_count:
        _same_line(8)
        _inline_status_text(f'Warnings {warning_count}', 'warning')
    _draw_preflight_summary(preflight)

    if config.templates:
        _draw_template_filter_toggle()

    _draw_team_rows(config, disabled=running, preflight=preflight)


def _draw_selected_template_details(config: HeroTeamConfig, template, running: bool) -> None:
    global _status
    if template is None:
        return

    stacked = _content_width(720.0) < TEMPLATE_DETAILS_STACK_WIDTH
    PyImGui.separator()
    template_name, rename_applied = _draw_rename_control(
        'template',
        template.template_id,
        template.name,
        'New Template',
        'Template',
        disabled=running,
        stacked=stacked,
    )
    if rename_applied:
        previous_name = template.name
        template.name = template_name
        try:
            save_config(config)
            _clear_rename()
            _clear_dirty('Template renamed and saved.')
        except Exception as exc:
            template.name = previous_name
            _status = f'Template rename save failed: {exc}'
    else:
        template.name = template_name

    hero_index = HERO_ID_TO_INDEX.get(int(template.hero_id), 0)
    if stacked:
        PyImGui.text('Preferred hero')
    try:
        PyImGui.set_next_item_width(-1 if stacked else 280)
    except Exception:
        pass
    began_disabled = _begin_disabled(running)
    try:
        hero_combo_label = '##template_hero' if stacked else 'Preferred hero##template_hero'
        selected_hero = _combo(hero_combo_label, hero_index, hero_labels(config))
    finally:
        _end_disabled(began_disabled)
    selected_hero_id = int(HERO_IDS[selected_hero])
    if not running and selected_hero_id != int(template.hero_id or 0):
        template.hero_id = selected_hero_id
        _mark_dirty('Template preferred hero changed. Click Save to persist.')
    _show_item_tooltip(
        'Team load is running.'
        if running
        else 'Preferred direct-apply target for this template; team assignment is still controlled in the Teams tab.'
    )

    template_code, code_applied = _draw_template_code_control(
        template.template_id,
        template.code,
        disabled=running,
        stacked=stacked,
    )
    if code_applied and template_code != str(template.code or ''):
        template.code = template_code
        _mark_dirty('Template code updated. Click Save to persist.')

    _draw_selected_template_preview(template)
    _draw_template_apply_control(config, template, stacked=stacked)


def _draw_template_selector_pane(config: HeroTeamConfig) -> bool:
    if _begin_child('HeroTeamTemplateListPane', 0.0, TEMPLATE_BROWSER_HEIGHT, True):
        try:
            return _draw_template_group_selector(config)
        finally:
            _end_child()

    return _draw_template_group_selector(config)


def _draw_template_detail_pane(config: HeroTeamConfig, running: bool, show_details: bool) -> None:
    template = get_template(config, _selected_template_id) if show_details else None
    if _begin_child('HeroTeamTemplateDetailPane', 0.0, TEMPLATE_BROWSER_HEIGHT, False):
        try:
            _draw_selected_template_details(config, template, running)
        finally:
            _end_child()
        return

    _draw_selected_template_details(config, template, running)


def _draw_template_browser_layout(config: HeroTeamConfig, running: bool) -> None:
    available_width = _content_width(720.0)
    if available_width < TEMPLATE_BROWSER_MIN_SPLIT_WIDTH:
        show_details = _draw_template_group_selector(config)
        if show_details:
            _draw_selected_template_details(config, get_template(config, _selected_template_id), running)
        return

    flags = int(
        PyImGui.TableFlags.BordersInnerV
        | PyImGui.TableFlags.SizingStretchProp
        | PyImGui.TableFlags.NoSavedSettings
    )
    try:
        opened = bool(PyImGui.begin_table('HeroTeamTemplateBrowserLayout', 2, flags))
    except Exception:
        opened = False
    if not opened:
        show_details = _draw_template_group_selector(config)
        if show_details:
            _draw_selected_template_details(config, get_template(config, _selected_template_id), running)
        return

    try:
        PyImGui.table_setup_column('Templates', PyImGui.TableColumnFlags.WidthFixed, TEMPLATE_BROWSER_LIST_WIDTH)
        PyImGui.table_setup_column('Template Details', PyImGui.TableColumnFlags.WidthStretch, 1.0)
        PyImGui.table_next_row()
        PyImGui.table_next_column()
        show_details = _draw_template_selector_pane(config)
        PyImGui.table_next_column()
        _draw_template_detail_pane(config, running, show_details)
    finally:
        PyImGui.end_table()


def _draw_templates_tab(config: HeroTeamConfig) -> None:
    global _selected_template_id, _status
    running = _operation_running()
    if _button_disabled('New##new_template', running, 72, 24):
        template = add_template(config)
        _selected_template_id = template.template_id
        _clear_code_edit()
        _mark_dirty('New template created. Click Save to persist.')
    _same_line()
    if _button_colored_disabled('Delete##delete_template', running, 'error', 72, 24):
        if _selected_template_id:
            _request_confirmation(
                'delete_template',
                'Delete Template',
                'This saved template will be removed.',
                {'template_id': str(_selected_template_id or '')},
            )
        else:
            _status = 'No template deleted.'
    _same_line()
    if _button_colored_disabled('Save##save_template', running, 'success', 72, 24):
        _save_or_confirm(config, commit_code_edit=True)

    if not config.templates:
        PyImGui.separator()
        _colored_text('No templates saved.', 'warning')
        return

    template_ids = [template.template_id for template in config.templates]
    if _selected_template_id and _selected_template_id not in template_ids:
        _selected_template_id = template_ids[0]
        _clear_code_edit()

    _draw_template_browser_layout(config, running)


def _active_account_label(config: HeroTeamConfig) -> str:
    return str(config.account_key or safe_account_key() or 'default')


def _draw_save_state_footer(config: HeroTeamConfig) -> None:
    running = _operation_running()
    dirty = _sync_dirty_state(config)

    PyImGui.separator()
    _muted_text(f'Account: {_active_account_label(config)}')
    _same_line(12)
    _colored_text(f'Save state: {"Unsaved changes" if dirty else "Saved"}', 'warning' if dirty else 'success')
    if running:
        _same_line(12)
        _colored_text('Team load running; editing controls are paused.', 'warning')
    if dirty:
        _same_line(8)
        if _button_colored_disabled('Reload Saved##reload_saved_config', running, 'warning', 128, 24):
            _reload_saved_config()
        tooltip = (
            'Wait for team load to finish before reloading saved configuration.'
            if running
            else 'Discard unsaved edits and reload the saved configuration for this account.'
        )
        _show_item_tooltip(tooltip)


def main() -> None:
    global _config, _status, _show_main_window
    try:
        config = _ensure_config()
        _draw_operation_status()

        if not _init_window_persistence_once():
            return

        floating_button = _ensure_floating_ui()
        floating_button.draw(_floating_ui_ini_key)
        _show_main_window = bool(floating_button.visible)
        if not _show_main_window:
            return

        if not _begin_window():
            _end_window()
            return

        _draw_tab_bar()
        if _active_tab == 'templates':
            _draw_templates_tab(config)
        else:
            _draw_teams_tab(config)

        _draw_confirmation_popup(config)
        _draw_save_state_footer(config)

        if _status:
            PyImGui.separator()
            _colored_text(_status, _status_severity(_status), wrapped=True)
        _end_window()
    except Exception as exc:
        _log_error(exc)
        _status = f'Error: {exc}'
        try:
            _end_window()
        except Exception:
            pass


if __name__ == '__main__':
    main()
