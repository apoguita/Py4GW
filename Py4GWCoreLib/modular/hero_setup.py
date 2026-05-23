"""Public hero setup facade for modular party loading and UI."""
from __future__ import annotations

from .hero_setup_model import (
    DEFAULT_HERO_PRIORITY,
    HERO_CATALOG as _HERO_CATALOG,
    HERO_ID_TO_NAME as _HERO_ID_TO_NAME,
    default_hero_config,
    default_hero_config_path,
    get_hero_priority,
    get_team_by_priority,
    hero_config_path,
    hero_id_from_name,
    load_hero_config,
    load_hero_priority,
    normalize_hero_config,
    normalize_priority,
    resolve_hero_ids,
    safe_account_key,
    save_hero_config,
    save_hero_priority,
)

_UI_EXPORTS = {
    "draw_configure_teams_section",
    "draw_priority_tab",
    "draw_setup_tab",
    "draw_team_configuration_window",
    "is_team_configuration_window_visible",
    "show_team_configuration_window",
    "toggle_team_configuration_window",
}


def __getattr__(name: str):
    if name not in _UI_EXPORTS:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    from . import hero_setup_ui

    value = getattr(hero_setup_ui, name)
    globals()[name] = value
    return value

__all__ = [
    "DEFAULT_HERO_PRIORITY",
    "default_hero_config",
    "default_hero_config_path",
    "draw_configure_teams_section",
    "draw_priority_tab",
    "draw_setup_tab",
    "draw_team_configuration_window",
    "get_hero_priority",
    "get_team_by_priority",
    "hero_config_path",
    "hero_id_from_name",
    "is_team_configuration_window_visible",
    "load_hero_config",
    "load_hero_priority",
    "normalize_hero_config",
    "normalize_priority",
    "resolve_hero_ids",
    "safe_account_key",
    "save_hero_config",
    "save_hero_priority",
    "show_team_configuration_window",
    "toggle_team_configuration_window",
]
