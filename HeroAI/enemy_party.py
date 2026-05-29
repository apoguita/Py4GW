import importlib.util
import sys
from pathlib import Path
from types import ModuleType


_IMPL_MODULE_NAME = 'HeroAI._enemy_party_impl'
_IMPL_PATH = Path(__file__).resolve().parent.parent / 'Widgets' / 'Legacy' / 'Automation' / 'Helpers' / 'Enemy Party.py'
_ENABLED = False


def is_enabled() -> bool:
    return _ENABLED


def _load_impl() -> ModuleType:
    if not _ENABLED:
        raise RuntimeError('Enemy Party is disabled')
    module = sys.modules.get(_IMPL_MODULE_NAME)
    if module is not None:
        return module

    spec = importlib.util.spec_from_file_location(_IMPL_MODULE_NAME, _IMPL_PATH)
    if spec is None or spec.loader is None:
        raise ImportError(f'Unable to load Enemy Party module from {_IMPL_PATH}')

    module = importlib.util.module_from_spec(spec)
    sys.modules[_IMPL_MODULE_NAME] = module
    spec.loader.exec_module(module)
    return module


def _get_state():
    if not _ENABLED:
        return None
    impl = _load_impl()
    if not impl._ensure_ini():
        return None
    return impl._ensure_state()


def is_window_open() -> bool:
    state = _get_state()
    if state is None:
        return False
    return bool(state.floating_button.visible)


def set_window_open(visible: bool) -> bool:
    state = _get_state()
    if state is None:
        return False
    state.floating_button.visible = bool(visible)
    return bool(state.floating_button.visible)


def toggle_window() -> bool:
    return set_window_open(not is_window_open())


def scanner_main() -> None:
    if not _ENABLED:
        return
    _load_impl().scanner_main()


def configure() -> None:
    if not _ENABLED:
        return
    _load_impl().configure()


def ui_main() -> None:
    if not _ENABLED:
        return
    _load_impl().ui_main()


def main() -> None:
    ui_main()
