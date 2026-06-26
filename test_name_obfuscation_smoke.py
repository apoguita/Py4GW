"""
Safe manual-control harness for the PyNameObfuscator embedded module.

This file is intentionally passive on import/load:
  - no PyNameObfuscator import at module load time
  - no auto-enable
  - no polling loops
  - no sleeps or blocking waits

Use the callable functions below from the Py4GW console/widget runtime to stage
testing manually.
"""

from __future__ import annotations

import traceback
from typing import Any


EXPECTED_API = (
    'enable',
    'disable',
    'is_enabled',
    'is_map_ready',
    'set_alias',
    'remove_alias',
    'clear_aliases',
    'clear',
    'alias_count',
    'get_aliases',
    'clear_observed_cache',
    'observed_count',
    'get_observed_players',
    'get_diagnostics',
    'reset_diagnostics',
)

_last_error: str | None = None
_ui_real_name = ''
_ui_fake_name = ''


def _log(message: str) -> None:
    print(f'[NameObfuscationManual] {message}')


def _module() -> Any | None:
    """Import PyNameObfuscator lazily so loading this file stays passive."""
    global _last_error

    try:
        import PyNameObfuscator  # type: ignore[import-not-found]
    except Exception as exc:  # noqa: BLE001 - manual harness should report import failures.
        _last_error = repr(exc)
        _log(f'PyNameObfuscator import failed: {exc!r}')
        traceback.print_exc()
        return None

    _last_error = None
    return PyNameObfuscator


def _call(label: str, func: Any, *args: Any) -> Any | None:
    global _last_error

    try:
        value = func(*args)
    except Exception as exc:  # noqa: BLE001 - manual harness should report and stay usable.
        _last_error = repr(exc)
        _log(f'{label} failed: {exc!r}')
        traceback.print_exc()
        return None

    _last_error = None
    return value


def _field(obj: Any, name: str, default: Any = None) -> Any:
    try:
        return getattr(obj, name)
    except Exception:  # noqa: BLE001
        return default


def _format_aliases(aliases: Any) -> str:
    if aliases is None:
        return '<unavailable>'
    if isinstance(aliases, dict):
        return ', '.join(f'{real!r}->{fake!r}' for real, fake in aliases.items()) or '<empty>'
    return repr(aliases)


def _format_observed_player(player: Any) -> dict[str, Any]:
    return {
        'player_number': _field(player, 'player_number', '?'),
        'agent_id': _field(player, 'agent_id', '?'),
        'real_name': _field(player, 'real_name', '?'),
        'display_name': _field(player, 'display_name', '?'),
        'aliased': _field(player, 'aliased', '?'),
    }


def check_import_api() -> bool:
    """Import PyNameObfuscator lazily and verify the expected API surface."""
    module = _module()
    if module is None:
        return False

    missing = [name for name in EXPECTED_API if not hasattr(module, name)]
    if missing:
        _log(f'missing expected API: {missing}')
        return False


    _log('PyNameObfuscator import/API OK')
    return True


def check_import() -> bool:
    """Short alias for check_import_api()."""
    return check_import_api()


def api() -> bool:
    """Short alias for check_import_api()."""
    return check_import_api()


def status() -> dict[str, Any]:
    """Print and return one non-blocking status snapshot."""
    module = _module()
    if module is None:
        result = {'import_ok': False, 'last_error': _last_error}
        _log(f'status: {result}')
        return result

    result = {
        'import_ok': True,
        'enabled': _call('is_enabled()', module.is_enabled),
        'map_ready': _call('is_map_ready()', module.is_map_ready),
        'alias_count': _call('alias_count()', module.alias_count),
        'observed_count': _call('observed_count()', module.observed_count),
        'last_error': _last_error,
    }
    _log(f'status: {result}')
    return result


def set_alias(real: str, fake: str) -> bool:
    """Manually add/update one alias. Does not enable obfuscation."""
    module = _module()
    if module is None:
        return False

    _call('set_alias()', module.set_alias, real, fake)
    _log(f'alias set: {real!r} -> {fake!r}')
    return True


def enable() -> bool:
    """Manually enable name obfuscation."""
    module = _module()
    if module is None:
        return False

    _call('enable()', module.enable)
    status()
    return True


def disable() -> bool:
    """Manually disable name obfuscation."""
    module = _module()
    if module is None:
        return False

    _call('disable()', module.disable)
    status()
    return True


def clear_aliases() -> bool:
    """Manually clear configured aliases. Does not change enabled state."""
    module = _module()
    if module is None:
        return False

    _call('clear_aliases()', module.clear_aliases)
    _log('aliases cleared')
    return True


def clear_observed_cache() -> bool:
    """Manually clear the observed-player cache. Does not change enabled state."""
    module = _module()
    if module is None:
        return False

    _call('clear_observed_cache()', module.clear_observed_cache)
    _log('observed cache cleared')
    return True


def observed(limit: int = 20) -> list[dict[str, Any]]:
    """Print and return a single observed-player snapshot. No polling."""
    module = _module()
    if module is None:
        return []

    players = _call('get_observed_players()', module.get_observed_players) or []
    rows = [_format_observed_player(player) for player in list(players)[: max(0, limit)]]
    for index, row in enumerate(rows):
        _log(f'observed[{index}]: {row}')
    if not rows:
        _log('observed: <empty>')
    return rows


def diagnostics() -> dict[str, Any]:
    """Print and return non-blocking native diagnostic counters."""
    module = _module()
    if module is None:
        return {}

    diag = _call('get_diagnostics()', module.get_diagnostics) or {}
    result = dict(diag)
    _log(f'diagnostics: {result}')
    return result


def reset_diagnostics() -> bool:
    """Manually reset native diagnostic counters."""
    module = _module()
    if module is None:
        return False

    _call('reset_diagnostics()', module.reset_diagnostics)
    _log('diagnostics reset')
    return True


def dump_aliases() -> Any:
    """Print and return the configured aliases."""
    module = _module()
    if module is None:
        return None

    aliases = _call('get_aliases()', module.get_aliases)
    _log(f'aliases: {_format_aliases(aliases)}')
    return aliases


def draw_window() -> None:
    """
    Optional Py4GW/ImGui manual UI.

    This only draws controls and calls actions when the user clicks buttons. It
    does not auto-enable, poll, sleep, or import PyNameObfuscator unless a
    button/status action is clicked.
    """
    global _ui_fake_name, _ui_real_name

    try:
        import PyImGui  # type: ignore[import-not-found]
    except Exception as exc:  # noqa: BLE001
        _log(f'PyImGui unavailable: {exc!r}')
        return

    if PyImGui.begin('Name Obfuscation Manual Test'):
        PyImGui.text('Passive harness: no auto-enable, no polling.')

        if PyImGui.button('Check import/API'):
            check_import_api()
        PyImGui.same_line(0, -1)
        if PyImGui.button('Status'):
            status()

        _ui_real_name = PyImGui.input_text('Real name', _ui_real_name)
        _ui_fake_name = PyImGui.input_text('Fake name', _ui_fake_name)
        if PyImGui.button('Set alias'):
            set_alias(_ui_real_name, _ui_fake_name)
        PyImGui.same_line(0, -1)
        if PyImGui.button('Dump aliases'):
            dump_aliases()

        if PyImGui.button('Enable'):
            enable()
        PyImGui.same_line(0, -1)
        if PyImGui.button('Disable'):
            disable()

        if PyImGui.button('Clear aliases'):
            clear_aliases()
        PyImGui.same_line(0, -1)
        if PyImGui.button('Clear observed cache'):
            clear_observed_cache()

        if PyImGui.button('Observed snapshot'):
            observed()
        PyImGui.same_line(0, -1)
        if PyImGui.button('Diagnostics'):
            diagnostics()
        PyImGui.same_line(0, -1)
        if PyImGui.button('Reset diagnostics'):
            reset_diagnostics()

        if _last_error:
            PyImGui.text(f'Last error: {_last_error}')
    PyImGui.end()


def main() -> None:
    """Widget-style entry point: draw the manual window once per frame."""
    draw_window()


_log('loaded; call check_import_api(), status(), set_alias(), enable(), disable(), observed(), diagnostics(), etc. manually')
