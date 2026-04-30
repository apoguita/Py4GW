"""Public hero setup facade for modular party loading and UI."""
from __future__ import annotations

from .hero_setup_model import (
    DEFAULT_HERO_PRIORITY,
    DEFAULT_HERO_TEAMS,
    HERO_CATALOG as _HERO_CATALOG,
    HERO_ID_TO_INDEX as _HERO_ID_TO_INDEX,
    HERO_ID_TO_NAME as _HERO_ID_TO_NAME,
    HERO_IDS as _HERO_IDS,
    HERO_LABELS as _HERO_LABELS,
    HERO_TEMPLATE_IDS as _HERO_TEMPLATE_IDS,
    TEAM_LABELS,
    TEAM_KEY_ALIASES,
    TEAM_SLOT_COUNTS,
    default_hero_config,
    default_hero_config_path,
    get_hero_priority,
    get_team_by_priority,
    get_team_for_size,
    hero_config_path,
    hero_id_from_name,
    load_hero_config,
    load_hero_priority,
    load_hero_teams,
    load_hero_templates,
    max_party_size_for_team_key,
    normalize_hero_config,
    normalize_priority,
    normalize_team_key,
    normalize_teams,
    normalize_templates,
    resolve_hero_ids,
    safe_account_key,
    save_hero_config,
    save_hero_priority,
    save_hero_teams,
    save_hero_templates,
    team_key_for_party_size,
)

# Backward-compatible private names used by older modular widgets while the
# public runtime path imports directly from hero_setup_model.
_normalize_priority = normalize_priority
_normalize_teams = normalize_teams
_normalize_templates = normalize_templates

_UI_EXPORTS = {
    "draw_configure_teams_section",
    "draw_exact_tab",
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
    "DEFAULT_HERO_TEAMS",
    "TEAM_KEY_ALIASES",
    "TEAM_LABELS",
    "TEAM_SLOT_COUNTS",
    "default_hero_config",
    "default_hero_config_path",
    "draw_configure_teams_section",
    "draw_exact_tab",
    "draw_priority_tab",
    "draw_setup_tab",
    "draw_team_configuration_window",
    "get_hero_priority",
    "get_team_by_priority",
    "get_team_for_size",
    "hero_config_path",
    "hero_id_from_name",
    "is_team_configuration_window_visible",
    "load_hero_config",
    "load_hero_priority",
    "load_hero_teams",
    "load_hero_templates",
    "max_party_size_for_team_key",
    "normalize_hero_config",
    "normalize_priority",
    "normalize_team_key",
    "normalize_teams",
    "normalize_templates",
    "resolve_hero_ids",
    "safe_account_key",
    "save_hero_config",
    "save_hero_priority",
    "save_hero_teams",
    "save_hero_templates",
    "show_team_configuration_window",
    "team_key_for_party_size",
    "toggle_team_configuration_window",
]
