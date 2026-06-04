from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from dataclasses import field
import json
import os
import re
from time import monotonic
from typing import Any
from uuid import uuid4

from Py4GWCoreLib.modular.hero_setup_model import HERO_ID_TO_NAME
from Py4GWCoreLib.modular.hero_setup_model import HERO_OPTIONS
from Py4GWCoreLib.modular.hero_setup_model import safe_account_key as _shared_safe_account_key
from Py4GWCoreLib.modular.paths import project_root as _shared_project_root


HERO_SLOT_COUNT = 7
CONFIG_VERSION = 1
SETTINGS_DIR_NAME = 'HeroTeamManager'
MERCENARY_HERO_IDS = set(range(28, 36))
HERO_IDS = [hero_id for hero_id, _name in HERO_OPTIONS]
HERO_ID_TO_INDEX = {hero_id: idx for idx, hero_id in enumerate(HERO_IDS)}

HERO_BEHAVIOR_DONT_CHANGE = -1
HERO_BEHAVIOR_FIGHT = 0
HERO_BEHAVIOR_GUARD = 1
HERO_BEHAVIOR_AVOID_COMBAT = 2
HERO_BEHAVIOR_CHOICES = [
    (HERO_BEHAVIOR_DONT_CHANGE, "Don't change"),
    (HERO_BEHAVIOR_FIGHT, 'Fight'),
    (HERO_BEHAVIOR_GUARD, 'Guard'),
    (HERO_BEHAVIOR_AVOID_COMBAT, 'Avoid Combat'),
]
HERO_BEHAVIOR_VALUES = [value for value, _label in HERO_BEHAVIOR_CHOICES]
HERO_BEHAVIOR_LABELS = [label for _value, label in HERO_BEHAVIOR_CHOICES]
EMPTY_SKILLBAR_TEMPLATE_NAME = 'Empty skill bar'


def hero_id_from_member(hero_member) -> int:
    try:
        hero_id_obj = getattr(hero_member, 'hero_id', None)
        if hero_id_obj is None:
            return 0
        if hasattr(hero_id_obj, 'GetID'):
            return int(hero_id_obj.GetID() or 0)
        return int(hero_id_obj or 0)
    except Exception:
        return 0


def current_hero_ids(party_api=None) -> set[int]:
    if party_api is None:
        from Py4GWCoreLib import Party as party_api

    hero_ids: set[int] = set()
    for hero in party_api.GetHeroes() or []:
        hero_id = hero_id_from_member(hero)
        if hero_id > 0:
            hero_ids.add(hero_id)
    return hero_ids


def hero_party_index_one_based(hero_id: int, party_api=None) -> int:
    if party_api is None:
        from Py4GWCoreLib import Party as party_api

    heroes = party_api.GetHeroes() or []
    for idx, hero in enumerate(heroes, start=1):
        if hero_id_from_member(hero) == int(hero_id):
            return int(idx)
    return 0


def hero_slot_capacity(*, map_api=None, party_api=None, default: int = 7) -> int:
    if map_api is None or party_api is None:
        from Py4GWCoreLib import Map
        from Py4GWCoreLib import Party

        map_api = map_api or Map
        party_api = party_api or Party

    try:
        map_size = int(map_api.GetMaxPartySize() or 0)
    except Exception:
        map_size = 0
    if map_size <= 0:
        try:
            map_size = int(party_api.GetPartySize() or 0)
        except Exception:
            map_size = 0
    try:
        player_count = int(party_api.GetPlayerCount() or 1)
    except Exception:
        player_count = 1

    if map_size <= 0:
        return max(0, int(default))
    return max(0, min(int(default), map_size - max(1, player_count)))


@dataclass(slots=True)
class HeroTemplateEntry:
    template_id: str
    name: str
    code: str = ''
    hero_id: int = 0


@dataclass(slots=True)
class HeroTeamSlot:
    hero_id: int = 0
    template_id: str = ''
    template_code: str = ''
    behavior: int = HERO_BEHAVIOR_DONT_CHANGE


@dataclass(slots=True)
class HeroTeamSetup:
    team_id: str
    name: str
    slots: list[HeroTeamSlot] = field(default_factory=list)


@dataclass(slots=True)
class HeroTeamConfig:
    version: int = CONFIG_VERSION
    active_team_id: str = ''
    teams: list[HeroTeamSetup] = field(default_factory=list)
    templates: list[HeroTemplateEntry] = field(default_factory=list)
    hero_names: dict[str, str] = field(default_factory=dict)
    hero_profession_cache: dict[str, dict[str, Any]] = field(default_factory=dict)
    account_key: str = ''


@dataclass(slots=True)
class ResolvedHeroSlot:
    slot_index: int
    hero_id: int
    hero_name: str
    template_code: str = ''
    template_name: str = ''
    template_assigned: bool = False
    template_missing: bool = False
    clear_skillbar: bool = False
    behavior: int = HERO_BEHAVIOR_DONT_CHANGE


@dataclass(slots=True)
class HeroTeamLoadPlan:
    slots: list[ResolvedHeroSlot] = field(default_factory=list)
    skipped_empty: list[int] = field(default_factory=list)
    skipped_duplicates: list[int] = field(default_factory=list)
    truncated_slots: list[int] = field(default_factory=list)


@dataclass(slots=True)
class HeroTeamRowWarning:
    slot_index: int
    code: str
    message: str
    severity: str = 'warning'


@dataclass(slots=True)
class HeroTeamLoadPreflight:
    plan: HeroTeamLoadPlan = field(default_factory=HeroTeamLoadPlan)
    row_warnings: dict[int, list[HeroTeamRowWarning]] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)
    blocking_messages: list[str] = field(default_factory=list)
    max_heroes: int = HERO_SLOT_COUNT

    @property
    def can_load(self) -> bool:
        return not self.blocking_messages


@dataclass(slots=True)
class SkillTemplatePreview:
    template_name: str = ''
    primary_profession_id: int = 0
    secondary_profession_id: int = 0
    profession_label: str = ''
    profession_icon_path: str = ''
    attribute_summary: str = ''
    skill_ids: list[int] = field(default_factory=list)
    skill_names: list[str] = field(default_factory=list)
    skill_icon_paths: list[str] = field(default_factory=list)


@dataclass(slots=True)
class TemplateProfessionGroup:
    group_key: str
    label: str
    sort_order: int = 999
    primary_profession_id: int = 0
    is_known_profession: bool = False


@dataclass(slots=True)
class CurrentPartyHeroTarget:
    hero_index: int
    hero_id: int
    hero_name: str
    agent_id: int = 0
    primary_profession_id: int = 0
    secondary_profession_id: int = 0
    profession_label: str = ''


@dataclass(slots=True)
class ApplyTemplateToHeroResult:
    success: bool
    message: str
    hero_id: int = 0
    hero_index: int = 0


_CURRENT_HERO_PROFESSION_CACHE: dict[tuple[int, int], tuple[int, int]] = {}
_CURRENT_HERO_IDENTITY_PROFESSION_CACHE: dict[tuple[int, str], tuple[int, int]] = {}
_CURRENT_HERO_PROFESSION_CACHE_ACCOUNT_KEY = ''


def _project_root() -> str:
    return os.path.normpath(_shared_project_root())


def _safe_filename(value: str) -> str:
    cleaned = re.sub(r'[<>:"/\\|?*]+', '_', str(value or '').strip())
    cleaned = cleaned.strip(' .')
    return cleaned or 'default'


def safe_account_key() -> str:
    return _safe_filename(_shared_safe_account_key())


def resolved_account_key(account_key: str | None = None) -> str:
    return _safe_filename(account_key if account_key is not None else safe_account_key())


def settings_root() -> str:
    return os.path.join(_project_root(), 'Settings', SETTINGS_DIR_NAME)


def account_config_path(account_key: str | None = None) -> str:
    key = resolved_account_key(account_key)
    return os.path.join(settings_root(), 'accounts', f'{key}.json')


def _new_id(prefix: str, name: str = '') -> str:
    seed = re.sub(r'[^a-z0-9]+', '_', str(name or prefix).strip().lower()).strip('_')
    return f'{prefix}_{seed or "item"}_{uuid4().hex[:8]}'


def _coerce_hero_id(value: Any) -> int:
    try:
        hero_id = int(value or 0)
    except (TypeError, ValueError):
        return 0
    return hero_id if hero_id in HERO_ID_TO_INDEX else 0


def _coerce_behavior(value: Any) -> int:
    try:
        behavior = int(value)
    except (TypeError, ValueError):
        return HERO_BEHAVIOR_DONT_CHANGE
    return behavior if behavior in HERO_BEHAVIOR_VALUES else HERO_BEHAVIOR_DONT_CHANGE


def _clean_display_name(value: Any) -> str:
    return str(value or '').strip()


def empty_slots(count: int = HERO_SLOT_COUNT) -> list[HeroTeamSlot]:
    return [HeroTeamSlot() for _ in range(max(0, int(count)))]


def new_team(name: str = 'New Hero Team') -> HeroTeamSetup:
    return HeroTeamSetup(team_id=_new_id('team', name), name=str(name or 'New Hero Team'), slots=empty_slots())


def new_template(name: str = 'New Template', code: str = '', hero_id: int = 0) -> HeroTemplateEntry:
    return HeroTemplateEntry(
        template_id=_new_id('template', name),
        name=str(name or 'New Template'),
        code=str(code or ''),
        hero_id=_coerce_hero_id(hero_id),
    )


def default_config(account_key: str | None = None) -> HeroTeamConfig:
    team = new_team()
    resolved_key = resolved_account_key(account_key) if account_key is not None else ''
    return HeroTeamConfig(active_team_id=team.team_id, teams=[team], templates=[], account_key=resolved_key)


def template_to_dict(template: HeroTemplateEntry) -> dict[str, Any]:
    return {
        'id': str(template.template_id),
        'name': str(template.name),
        'code': str(template.code),
        'hero_id': int(template.hero_id),
    }


def slot_to_dict(slot: HeroTeamSlot) -> dict[str, Any]:
    return {
        'hero_id': int(slot.hero_id),
        'template_id': str(slot.template_id or ''),
        'template_code': str(slot.template_code or ''),
        'behavior': _coerce_behavior(slot.behavior),
    }


def team_to_dict(team: HeroTeamSetup) -> dict[str, Any]:
    return {
        'id': str(team.team_id),
        'name': str(team.name),
        'slots': [slot_to_dict(slot) for slot in normalize_slots(team.slots)],
    }


def config_to_dict(config: HeroTeamConfig) -> dict[str, Any]:
    normalized = normalize_config(config_to_raw(config))
    return {
        'version': int(normalized.version),
        'active_team_id': str(normalized.active_team_id),
        'teams': [team_to_dict(team) for team in normalized.teams],
        'templates': [template_to_dict(template) for template in normalized.templates],
        'hero_names': dict(normalized.hero_names),
        'hero_profession_cache': dict(normalized.hero_profession_cache),
    }


def config_to_raw(config: HeroTeamConfig | dict[str, Any] | None) -> dict[str, Any]:
    if isinstance(config, HeroTeamConfig):
        return {
            'version': config.version,
            'active_team_id': config.active_team_id,
            'teams': [team_to_dict(team) for team in config.teams],
            'templates': [template_to_dict(template) for template in config.templates],
            'hero_names': dict(config.hero_names),
            'hero_profession_cache': dict(config.hero_profession_cache),
            'account_key': str(config.account_key or ''),
        }
    return config if isinstance(config, dict) else {}


def _template_from_raw(raw: Any, used_ids: set[str]) -> HeroTemplateEntry | None:
    if isinstance(raw, HeroTemplateEntry):
        name = str(raw.name or '').strip() or 'New Template'
        template_id = str(raw.template_id or '').strip()
        if not template_id or template_id in used_ids:
            template_id = _new_id('template', name)
        used_ids.add(template_id)
        return HeroTemplateEntry(
            template_id=template_id,
            name=name,
            code=str(raw.code or ''),
            hero_id=_coerce_hero_id(raw.hero_id),
        )
    if not isinstance(raw, dict):
        return None
    name = str(raw.get('name', '') or '').strip() or 'New Template'
    template_id = str(raw.get('id', raw.get('template_id', '')) or '').strip()
    if not template_id or template_id in used_ids:
        template_id = _new_id('template', name)
    used_ids.add(template_id)
    return HeroTemplateEntry(
        template_id=template_id,
        name=name,
        code=str(raw.get('code', raw.get('template', '')) or ''),
        hero_id=_coerce_hero_id(raw.get('hero_id', 0)),
    )


def _slot_from_raw(raw: Any) -> HeroTeamSlot:
    if isinstance(raw, HeroTeamSlot):
        return HeroTeamSlot(
            hero_id=_coerce_hero_id(raw.hero_id),
            template_id=str(raw.template_id or ''),
            template_code=str(raw.template_code or ''),
            behavior=_coerce_behavior(getattr(raw, 'behavior', HERO_BEHAVIOR_DONT_CHANGE)),
        )
    if not isinstance(raw, dict):
        return HeroTeamSlot()
    return HeroTeamSlot(
        hero_id=_coerce_hero_id(raw.get('hero_id', 0)),
        template_id=str(raw.get('template_id', '') or ''),
        template_code=str(raw.get('template_code', raw.get('template', '')) or ''),
        behavior=_coerce_behavior(raw.get('behavior', raw.get('hero_behavior', HERO_BEHAVIOR_DONT_CHANGE))),
    )


def _is_valid_primary_profession_id(profession_id: int) -> bool:
    try:
        profession_id = int(profession_id or 0)
    except Exception:
        return False
    return 1 <= profession_id <= 10


def _is_valid_secondary_profession_id(profession_id: int) -> bool:
    try:
        profession_id = int(profession_id or 0)
    except Exception:
        return False
    return profession_id == 0 or _is_valid_primary_profession_id(profession_id)


def _hero_profession_cache_storage_key(hero_id: int, identity_name: str) -> str:
    identity_key = _hero_profession_identity_key(hero_id, identity_name)
    if identity_key is None:
        return ''
    return f'{identity_key[0]}:{identity_key[1]}'


def _split_hero_profession_cache_storage_key(value: Any) -> tuple[int, str]:
    hero_id_text, separator, identity_name = str(value or '').partition(':')
    if not separator:
        return 0, ''
    return _coerce_hero_id(hero_id_text), _normalize_hero_identity_name(identity_name)


def _normalize_hero_profession_cache(raw_cache: Any) -> dict[str, dict[str, Any]]:
    source = raw_cache if isinstance(raw_cache, dict) else {}
    normalized: dict[str, dict[str, Any]] = {}
    for raw_key, raw_entry in source.items():
        if not isinstance(raw_entry, dict):
            continue

        key_hero_id, key_identity_name = _split_hero_profession_cache_storage_key(raw_key)
        hero_id = _coerce_hero_id(raw_entry.get('hero_id', 0)) or key_hero_id
        identity_name = _clean_display_name(
            raw_entry.get('identity_name', raw_entry.get('display_name', ''))
        )
        if not identity_name:
            identity_name = key_identity_name

        primary_id = _profession_id(
            raw_entry.get('primary_profession_id', raw_entry.get('primary_id', raw_entry.get('primary', 0)))
        )
        secondary_id = _profession_id(
            raw_entry.get('secondary_profession_id', raw_entry.get('secondary_id', raw_entry.get('secondary', 0)))
        )
        if not _is_valid_primary_profession_id(primary_id):
            continue
        if not _is_valid_secondary_profession_id(secondary_id):
            secondary_id = 0

        storage_key = _hero_profession_cache_storage_key(hero_id, identity_name)
        if not storage_key:
            continue
        normalized[storage_key] = {
            'hero_id': int(hero_id),
            'identity_name': str(identity_name),
            'primary_profession_id': int(primary_id),
            'secondary_profession_id': int(secondary_id),
        }
    return normalized


def normalize_slots(raw_slots: Any, count: int = HERO_SLOT_COUNT) -> list[HeroTeamSlot]:
    source = raw_slots if isinstance(raw_slots, list) else []
    slots = [_slot_from_raw(source[index]) if index < len(source) else HeroTeamSlot() for index in range(int(count))]
    return slots[: int(count)]


def ensure_team_slots(team: HeroTeamSetup, count: int = HERO_SLOT_COUNT) -> list[HeroTeamSlot]:
    while len(team.slots) < int(count):
        team.slots.append(HeroTeamSlot())
    return team.slots[: int(count)]


def _team_from_raw(raw: Any, used_ids: set[str]) -> HeroTeamSetup | None:
    if isinstance(raw, HeroTeamSetup):
        name = str(raw.name or '').strip() or 'New Hero Team'
        team_id = str(raw.team_id or '').strip()
        if not team_id or team_id in used_ids:
            team_id = _new_id('team', name)
        used_ids.add(team_id)
        return HeroTeamSetup(team_id=team_id, name=name, slots=normalize_slots(raw.slots))
    if not isinstance(raw, dict):
        return None
    name = str(raw.get('name', '') or '').strip() or 'New Hero Team'
    team_id = str(raw.get('id', raw.get('team_id', '')) or '').strip()
    if not team_id or team_id in used_ids:
        team_id = _new_id('team', name)
    used_ids.add(team_id)
    return HeroTeamSetup(team_id=team_id, name=name, slots=normalize_slots(raw.get('slots', [])))


def normalize_config(raw: dict[str, Any] | HeroTeamConfig | None) -> HeroTeamConfig:
    source = config_to_raw(raw)
    template_source = source.get('templates', [])
    team_source = source.get('teams', [])
    hero_names_source = source.get('hero_names', {})
    hero_profession_cache_source = source.get('hero_profession_cache', {})

    if isinstance(template_source, dict):
        template_source = [
            {'id': key, **(value if isinstance(value, dict) else {'code': value})}
            for key, value in template_source.items()
        ]
    if isinstance(team_source, dict):
        team_source = [
            {'id': key, **(value if isinstance(value, dict) else {'slots': value})}
            for key, value in team_source.items()
        ]

    used_template_ids: set[str] = set()
    templates = [
        template
        for template in (_template_from_raw(entry, used_template_ids) for entry in template_source)
        if template is not None
    ]
    valid_template_ids = {template.template_id for template in templates}

    used_team_ids: set[str] = set()
    teams = [team for team in (_team_from_raw(entry, used_team_ids) for entry in team_source) if team is not None]
    if not teams:
        teams = [new_team()]

    for team in teams:
        for slot in team.slots:
            if slot.template_id and slot.template_id not in valid_template_ids:
                slot.template_id = ''

    active_team_id = str(source.get('active_team_id', '') or '').strip()
    if active_team_id not in {team.team_id for team in teams}:
        active_team_id = teams[0].team_id

    hero_names: dict[str, str] = {}
    if isinstance(hero_names_source, dict):
        for key, value in hero_names_source.items():
            hero_id = _coerce_hero_id(key)
            name = _clean_display_name(value)
            if hero_id > 0 and name:
                hero_names[str(hero_id)] = name

    return HeroTeamConfig(
        version=CONFIG_VERSION,
        active_team_id=active_team_id,
        teams=teams,
        templates=templates,
        hero_names=hero_names,
        hero_profession_cache=_normalize_hero_profession_cache(hero_profession_cache_source),
        account_key=str(source.get('account_key', '') or '').strip(),
    )


def load_config(account_key: str | None = None) -> HeroTeamConfig:
    key = resolved_account_key(account_key)
    path = account_config_path(key)
    if not os.path.isfile(path):
        return default_config(account_key=key)
    try:
        with open(path, 'r', encoding='utf-8') as handle:
            raw = json.load(handle)
    except Exception:
        return default_config(account_key=key)
    config = normalize_config(raw if isinstance(raw, dict) else {})
    config.account_key = key
    return config


def save_config(config: HeroTeamConfig, account_key: str | None = None) -> None:
    key = resolved_account_key(account_key if account_key is not None else config.account_key or None)
    config.account_key = key
    path = account_config_path(key)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as handle:
        json.dump(config_to_dict(config), handle, indent=2, sort_keys=True)
        handle.write('\n')


def is_pristine_default_config(config: HeroTeamConfig) -> bool:
    if config.templates or config.hero_names or len(config.teams) != 1:
        return False
    team = config.teams[0]
    if str(team.name or '') != 'New Hero Team':
        return False
    return all(
        slot.hero_id == 0
        and not slot.template_id
        and not slot.template_code
        and _coerce_behavior(slot.behavior) == HERO_BEHAVIOR_DONT_CHANGE
        for slot in normalize_slots(team.slots)
    )


def get_team(config: HeroTeamConfig, team_id: str | None = None) -> HeroTeamSetup | None:
    wanted = str(team_id or config.active_team_id or '').strip()
    for team in config.teams:
        if team.team_id == wanted:
            return team
    return config.teams[0] if config.teams else None


def get_template(config: HeroTeamConfig, template_id: str) -> HeroTemplateEntry | None:
    wanted = str(template_id or '').strip()
    if not wanted:
        return None
    for template in config.templates:
        if template.template_id == wanted:
            return template
    return None


def hero_default_name(hero_id: int) -> str:
    hero_id = _coerce_hero_id(hero_id)
    if hero_id <= 0:
        return 'Empty'
    return HERO_ID_TO_NAME.get(hero_id, f'Hero {hero_id}')


def hero_alias(config: HeroTeamConfig | None, hero_id: int) -> str:
    hero_id = _coerce_hero_id(hero_id)
    if config is None or hero_id <= 0:
        return ''
    return _clean_display_name(config.hero_names.get(str(hero_id), ''))


def set_hero_alias(config: HeroTeamConfig, hero_id: int, alias: str) -> str:
    hero_id = _coerce_hero_id(hero_id)
    if hero_id <= 0:
        return ''
    cleaned = _clean_display_name(alias)[:128]
    if cleaned and cleaned != hero_default_name(hero_id):
        config.hero_names[str(hero_id)] = cleaned
        return cleaned
    config.hero_names.pop(str(hero_id), None)
    return ''


def clear_hero_alias(config: HeroTeamConfig, hero_id: int) -> None:
    hero_id = _coerce_hero_id(hero_id)
    if hero_id > 0:
        config.hero_names.pop(str(hero_id), None)


def hero_display_name(config: HeroTeamConfig | None, hero_id: int) -> str:
    hero_id = _coerce_hero_id(hero_id)
    if hero_id <= 0:
        return 'Empty'
    if config is not None:
        custom_name = hero_alias(config, hero_id)
        if custom_name:
            return custom_name
    return hero_default_name(hero_id)


def _hero_display_name_from_aliases(hero_names: dict[str, str] | None, hero_id: int) -> str:
    hero_id = _coerce_hero_id(hero_id)
    if hero_id <= 0:
        return 'Empty'
    if isinstance(hero_names, dict):
        custom_name = _clean_display_name(hero_names.get(str(hero_id), ''))
        if custom_name:
            return custom_name
    return hero_default_name(hero_id)


def hero_labels(config: HeroTeamConfig | None = None) -> list[str]:
    return [f'{hero_display_name(config, hero_id)} ({hero_id})' for hero_id in HERO_IDS]


def _human_enum_name(name: str) -> str:
    cleaned = str(name or '').replace('_', ' ').strip()
    return re.sub(r'(?<!^)(?=[A-Z])', ' ', cleaned).strip()


def _profession_id_from_text(value: Any) -> int:
    normalized = re.sub(r'[^a-z0-9]+', '', str(value or '').strip().lower())
    if not normalized:
        return 0
    names = {
        'warrior': 1,
        'w': 1,
        'ranger': 2,
        'r': 2,
        'monk': 3,
        'mo': 3,
        'necromancer': 4,
        'n': 4,
        'mesmer': 5,
        'me': 5,
        'elementalist': 6,
        'e': 6,
        'assassin': 7,
        'a': 7,
        'ritualist': 8,
        'rt': 8,
        'paragon': 9,
        'p': 9,
        'dervish': 10,
        'd': 10,
    }
    return int(names.get(normalized, 0))


def _profession_id(value: Any) -> int:
    def _method_int(method_name: str) -> int:
        method = getattr(value, method_name, None)
        if callable(method):
            try:
                return _profession_id(method())
            except Exception:
                return 0
        return 0

    def _method_text(method_name: str) -> str:
        method = getattr(value, method_name, None)
        if callable(method):
            try:
                return str(method() or '').strip()
            except Exception:
                return ''
        return ''

    if value is None:
        return 0
    if isinstance(value, int):
        return int(value)

    try:
        for method_name in ('ToInt', 'Get', 'to_int', 'get'):
            profession_id = _method_int(method_name)
            if profession_id > 0:
                return profession_id
        direct_id = int(value or 0)
        if direct_id > 0:
            return direct_id
    except Exception:
        pass

    for attr_name in ('value', 'id', 'profession', 'primary'):
        try:
            attr_value = getattr(value, attr_name)
        except Exception:
            continue
        if callable(attr_value) or attr_value is value:
            continue
        profession_id = _profession_id(attr_value)
        if profession_id > 0:
            return profession_id

    for text in (_method_text('GetName'), _method_text('GetShortName'), str(value or '').strip()):
        profession_id = _profession_id_from_text(text)
        if profession_id > 0:
            return profession_id
    return 0


def _profession_short_label(primary_id: int, secondary_id: int = 0) -> str:
    try:
        from Py4GWCoreLib.enums_src.GameData_enums import ProfessionShort
        from Py4GWCoreLib.enums_src.GameData_enums import ProfessionShort_Names

        primary = ProfessionShort_Names.get(ProfessionShort(int(primary_id or 0)), '')
        secondary = ProfessionShort_Names.get(ProfessionShort(int(secondary_id or 0)), '')
        return '/'.join(label for label in [primary, secondary] if label and label != 'None')
    except Exception:
        return ''


def _profession_name(profession_id: int) -> str:
    try:
        from Py4GWCoreLib.enums_src.GameData_enums import Profession
        from Py4GWCoreLib.enums_src.GameData_enums import Profession_Names

        return str(Profession_Names.get(Profession(int(profession_id or 0)), '') or '').strip()
    except Exception:
        return ''


def _agent_profession_ids(agent_id: int) -> tuple[int, int]:
    agent_id = int(agent_id or 0)
    if agent_id <= 0:
        return 0, 0
    try:
        from Py4GWCoreLib.Agent import Agent

        primary_id, secondary_id = Agent.GetProfessionIDs(agent_id)
        primary_id = _profession_id(primary_id)
        secondary_id = _profession_id(secondary_id)
        if primary_id > 0:
            return primary_id, secondary_id

        living = Agent.GetLivingAgentByID(agent_id)
        if living is None:
            return primary_id, secondary_id
        primary_id = _profession_id(getattr(living, 'primary', 0)) or _profession_id(getattr(living, 'profession', 0))
        secondary_id = _profession_id(getattr(living, 'secondary', 0)) or _profession_id(
            getattr(living, 'secondary_profession', 0)
        )
        return primary_id, secondary_id
    except Exception:
        return 0, 0


def _hero_object_primary_profession_id(hero_member) -> int:
    try:
        hero_id_obj = getattr(hero_member, 'hero_id', None)
        get_profession = getattr(hero_id_obj, 'GetProfession', None)
        if callable(get_profession):
            return _profession_id(get_profession())
    except Exception:
        pass
    return 0


def _hero_agent_id_by_party_position(party_api, hero_index: int) -> int:
    hero_index = int(hero_index or 0)
    if party_api is None or hero_index <= 0:
        return 0

    lookups = [
        (getattr(party_api, 'Heroes', None), 'GetHeroAgentIDByPartyPosition'),
        (party_api, 'GetHeroAgentID'),
    ]
    for owner, method_name in lookups:
        if owner is None:
            continue
        method = getattr(owner, method_name, None)
        if not callable(method):
            continue
        try:
            agent_id = int(method(hero_index) or 0)
        except Exception:
            agent_id = 0
        if agent_id > 0:
            return agent_id
    return 0


def _hero_member_by_party_position(party_api, hero_index: int):
    hero_index = int(hero_index or 0)
    if party_api is None or hero_index <= 0:
        return None
    try:
        heroes = party_api.GetHeroes() or []
    except Exception:
        return None
    if hero_index > len(heroes):
        return None
    return heroes[hero_index - 1]


def _normalize_hero_identity_name(value: Any) -> str:
    cleaned = re.sub(r'\s+', ' ', _clean_display_name(value))
    return cleaned.casefold()


def _hero_profession_identity_name(hero_member, hero_id: int) -> str:
    hero_id = _coerce_hero_id(hero_id)
    if hero_id <= 0:
        return ''

    display_name = _detect_current_party_hero_display_name(hero_member, hero_id)
    if display_name:
        return display_name

    if hero_id in MERCENARY_HERO_IDS:
        return ''
    return hero_default_name(hero_id)


def _hero_profession_identity_key(hero_id: int, identity_name: str = '') -> tuple[int, str] | None:
    hero_id = _coerce_hero_id(hero_id)
    normalized_name = _normalize_hero_identity_name(identity_name)
    if hero_id <= 0 or not normalized_name:
        return None
    return hero_id, normalized_name


def _sync_current_party_hero_profession_cache_account() -> None:
    global _CURRENT_HERO_PROFESSION_CACHE_ACCOUNT_KEY
    try:
        account_key = safe_account_key()
    except Exception:
        return
    if not _CURRENT_HERO_PROFESSION_CACHE_ACCOUNT_KEY:
        _CURRENT_HERO_PROFESSION_CACHE_ACCOUNT_KEY = account_key
        return
    if account_key == _CURRENT_HERO_PROFESSION_CACHE_ACCOUNT_KEY:
        return
    _CURRENT_HERO_PROFESSION_CACHE.clear()
    _CURRENT_HERO_IDENTITY_PROFESSION_CACHE.clear()
    _CURRENT_HERO_PROFESSION_CACHE_ACCOUNT_KEY = account_key


def _write_hero_profession_cache_entry_to_disk(
    config: HeroTeamConfig | None,
    storage_key: str,
    entry: dict[str, Any],
) -> None:
    if config is None:
        return
    try:
        key = resolved_account_key(config.account_key or None)
        path = account_config_path(key)
    except Exception:
        return
    if not os.path.isfile(path):
        return

    try:
        with open(path, 'r', encoding='utf-8') as handle:
            raw = json.load(handle)
    except Exception:
        return
    if not isinstance(raw, dict):
        return

    raw_cache = raw.get('hero_profession_cache', {})
    if not isinstance(raw_cache, dict):
        raw_cache = {}
    raw_cache[str(storage_key)] = dict(entry)
    raw['hero_profession_cache'] = _normalize_hero_profession_cache(raw_cache)
    try:
        with open(path, 'w', encoding='utf-8') as handle:
            json.dump(raw, handle, indent=2, sort_keys=True)
            handle.write('\n')
    except Exception:
        return


def _remember_persisted_hero_profession(
    config: HeroTeamConfig | None,
    hero_id: int,
    identity_name: str,
    primary_id: int,
    secondary_id: int = 0,
) -> None:
    if config is None:
        return
    hero_id = _coerce_hero_id(hero_id)
    primary_id = _profession_id(primary_id)
    secondary_id = _profession_id(secondary_id)
    if not _is_valid_primary_profession_id(primary_id):
        return
    if not _is_valid_secondary_profession_id(secondary_id):
        secondary_id = 0

    storage_key = _hero_profession_cache_storage_key(hero_id, identity_name)
    if not storage_key:
        return
    entry = {
        'hero_id': int(hero_id),
        'identity_name': str(identity_name),
        'primary_profession_id': int(primary_id),
        'secondary_profession_id': int(secondary_id),
    }
    if not hasattr(config, 'hero_profession_cache') or not isinstance(config.hero_profession_cache, dict):
        config.hero_profession_cache = {}
    if config.hero_profession_cache.get(storage_key) == entry:
        return
    config.hero_profession_cache[storage_key] = entry
    _write_hero_profession_cache_entry_to_disk(config, storage_key, entry)


def _persisted_current_party_hero_profession(
    config: HeroTeamConfig | None,
    hero_id: int,
    identity_name: str,
) -> tuple[int, int]:
    if config is None:
        return 0, 0
    cache = getattr(config, 'hero_profession_cache', {})
    if not isinstance(cache, dict):
        return 0, 0
    storage_key = _hero_profession_cache_storage_key(hero_id, identity_name)
    if not storage_key:
        return 0, 0
    entry = cache.get(storage_key)
    if not isinstance(entry, dict):
        return 0, 0
    primary_id = _profession_id(entry.get('primary_profession_id', 0))
    secondary_id = _profession_id(entry.get('secondary_profession_id', 0))
    if not _is_valid_primary_profession_id(primary_id):
        return 0, 0
    if not _is_valid_secondary_profession_id(secondary_id):
        secondary_id = 0
    return primary_id, secondary_id


def _remember_current_party_hero_profession(
    hero_id: int,
    agent_id: int,
    primary_id: int,
    secondary_id: int = 0,
    identity_name: str = '',
    config: HeroTeamConfig | None = None,
    persist: bool = False,
) -> None:
    _sync_current_party_hero_profession_cache_account()
    hero_id = _coerce_hero_id(hero_id)
    try:
        agent_id = int(agent_id or 0)
    except Exception:
        agent_id = 0
    primary_id = _profession_id(primary_id)
    secondary_id = _profession_id(secondary_id)
    if hero_id <= 0 or primary_id <= 0:
        return
    cached_profession = (primary_id, max(0, secondary_id))
    if agent_id > 0:
        _CURRENT_HERO_PROFESSION_CACHE[(hero_id, agent_id)] = cached_profession
    identity_key = _hero_profession_identity_key(hero_id, identity_name)
    if identity_key is not None:
        _CURRENT_HERO_IDENTITY_PROFESSION_CACHE[identity_key] = cached_profession
    if persist:
        _remember_persisted_hero_profession(config, hero_id, identity_name, primary_id, secondary_id)


def _cached_current_party_hero_profession(
    hero_id: int,
    agent_id: int,
    identity_name: str = '',
) -> tuple[int, int]:
    _sync_current_party_hero_profession_cache_account()
    hero_id = _coerce_hero_id(hero_id)
    try:
        agent_id = int(agent_id or 0)
    except Exception:
        agent_id = 0
    if hero_id <= 0:
        return 0, 0
    if agent_id > 0:
        cached_profession = _CURRENT_HERO_PROFESSION_CACHE.get((hero_id, agent_id))
        if cached_profession is not None:
            return cached_profession
    identity_key = _hero_profession_identity_key(hero_id, identity_name)
    if identity_key is not None:
        return _CURRENT_HERO_IDENTITY_PROFESSION_CACHE.get(identity_key, (0, 0))
    return 0, 0


def _current_party_hero_profession_cache_keys(party_api) -> set[tuple[int, int]] | None:
    if party_api is None:
        return None
    try:
        heroes = party_api.GetHeroes() or []
    except Exception:
        return None

    keys: set[tuple[int, int]] = set()
    for hero_index, hero_member in enumerate(heroes, start=1):
        hero_id = _coerce_hero_id(hero_id_from_member(hero_member))
        if hero_id <= 0:
            continue
        try:
            agent_id = int(getattr(hero_member, 'agent_id', 0) or 0)
        except Exception:
            agent_id = 0
        if agent_id <= 0:
            agent_id = _hero_agent_id_by_party_position(party_api, hero_index)
        if agent_id > 0:
            keys.add((hero_id, agent_id))
    return keys


def _current_party_hero_profession_identity_keys(party_api) -> set[tuple[int, str]] | None:
    if party_api is None:
        return None
    try:
        heroes = party_api.GetHeroes() or []
    except Exception:
        return None

    keys: set[tuple[int, str]] = set()
    for hero_member in heroes:
        hero_id = _coerce_hero_id(hero_id_from_member(hero_member))
        identity_key = _hero_profession_identity_key(
            hero_id,
            _hero_profession_identity_name(hero_member, hero_id),
        )
        if identity_key is not None:
            keys.add(identity_key)
    return keys


def _prune_current_party_hero_profession_cache(party_api) -> None:
    _sync_current_party_hero_profession_cache_account()
    keys = _current_party_hero_profession_cache_keys(party_api)
    if keys is None:
        return
    if not keys:
        _CURRENT_HERO_PROFESSION_CACHE.clear()
    else:
        for key in list(_CURRENT_HERO_PROFESSION_CACHE):
            if key not in keys:
                _CURRENT_HERO_PROFESSION_CACHE.pop(key, None)

    identity_keys = _current_party_hero_profession_identity_keys(party_api)
    if not identity_keys:
        return
    current_identity_hero_ids = {hero_id for hero_id, _name in identity_keys}
    for key in list(_CURRENT_HERO_IDENTITY_PROFESSION_CACHE):
        hero_id, _identity_name = key
        if hero_id in current_identity_hero_ids and key not in identity_keys:
            _CURRENT_HERO_IDENTITY_PROFESSION_CACHE.pop(key, None)


def _object_int(value: Any, *attr_names: str) -> int:
    for attr_name in attr_names:
        try:
            candidate = getattr(value, attr_name)
        except Exception:
            continue
        try:
            return int(candidate() if callable(candidate) else candidate)
        except Exception:
            continue
    try:
        return int(value)
    except Exception:
        return 0


def _agent_primary_profession_id_from_attributes(agent_id: int) -> int:
    agent_id = int(agent_id or 0)
    if agent_id <= 0:
        return 0

    try:
        from Py4GWCoreLib.Agent import Agent
        from Py4GWCoreLib.enums_src.GameData_enums import Attribute

        attributes = Agent.GetAttributes(agent_id) or []
    except Exception:
        return 0

    detected_professions: set[int] = set()
    for attribute_data in attributes:
        attribute_id = _object_int(attribute_data, 'attribute_id', 'Id', 'id')
        level = max(
            _object_int(attribute_data, 'level_base', 'BaseValue', 'base_value'),
            _object_int(attribute_data, 'level', 'Value', 'value'),
        )
        if level <= 0:
            continue
        try:
            attribute = Attribute(attribute_id)
        except Exception:
            continue
        if not bool(getattr(attribute, 'is_primary', False)):
            continue
        profession_id = _profession_id(attribute.get_profession())
        if profession_id > 0:
            detected_professions.add(profession_id)

    if len(detected_professions) == 1:
        return detected_professions.pop()
    return 0


def _current_party_hero_profession_ids(
    hero_member,
    party_api,
    hero_index: int,
    hero_id: int = 0,
    config: HeroTeamConfig | None = None,
) -> tuple[int, int, int]:
    hero_id = _coerce_hero_id(hero_id)
    identity_name = _hero_profession_identity_name(hero_member, hero_id)
    try:
        agent_id = int(getattr(hero_member, 'agent_id', 0) or 0)
    except Exception:
        agent_id = 0

    primary_id = _profession_id(getattr(hero_member, 'primary', 0))
    secondary_id = _profession_id(getattr(hero_member, 'secondary', 0))

    if primary_id <= 0:
        primary_id = _hero_object_primary_profession_id(hero_member)

    candidate_agent_ids = [agent_id]
    position_agent_id = _hero_agent_id_by_party_position(party_api, hero_index)
    if position_agent_id > 0 and position_agent_id not in candidate_agent_ids:
        candidate_agent_ids.append(position_agent_id)
    if agent_id <= 0 and position_agent_id > 0:
        agent_id = position_agent_id

    for candidate_agent_id in candidate_agent_ids:
        if candidate_agent_id <= 0:
            continue
        if primary_id > 0 and secondary_id > 0:
            break
        agent_primary_id, agent_secondary_id = _agent_profession_ids(candidate_agent_id)
        if primary_id <= 0 and agent_primary_id > 0:
            primary_id = _profession_id(agent_primary_id)
        if primary_id <= 0:
            primary_id = _agent_primary_profession_id_from_attributes(candidate_agent_id)
        if secondary_id <= 0 and agent_secondary_id > 0:
            secondary_id = _profession_id(agent_secondary_id)
        if agent_id <= 0 and (primary_id > 0 or agent_primary_id > 0 or agent_secondary_id > 0):
            agent_id = candidate_agent_id

    live_primary_id = primary_id
    live_secondary_id = secondary_id
    cached_primary_id, cached_secondary_id = _cached_current_party_hero_profession(
        hero_id,
        agent_id,
        identity_name,
    )
    if primary_id <= 0 and cached_primary_id > 0:
        primary_id = cached_primary_id
    if secondary_id <= 0 and cached_secondary_id > 0:
        secondary_id = cached_secondary_id

    if primary_id <= 0:
        persisted_primary_id, persisted_secondary_id = _persisted_current_party_hero_profession(
            config,
            hero_id,
            identity_name,
        )
        if persisted_primary_id > 0:
            primary_id = persisted_primary_id
        if secondary_id <= 0 and persisted_secondary_id > 0:
            secondary_id = persisted_secondary_id

    if primary_id > 0:
        _remember_current_party_hero_profession(
            hero_id,
            agent_id,
            primary_id,
            live_secondary_id if live_primary_id > 0 else secondary_id,
            identity_name,
            config,
            persist=live_primary_id > 0,
        )

    return primary_id, secondary_id, agent_id


def summarize_skill_template(
    template: HeroTemplateEntry | str,
    template_name: str | None = None,
) -> SkillTemplatePreview | None:
    if isinstance(template, HeroTemplateEntry):
        code = str(template.code or '').strip()
        name = str(template_name if template_name is not None else template.name or '').strip()
    else:
        code = str(template or '').strip()
        name = str(template_name or '').strip()

    if len(code) < 16 or not re.fullmatch(r'[A-Za-z0-9+/]+', code):
        return None

    try:
        from Py4GWCoreLib.Skill import Skill
        from Py4GWCoreLib.enums_src.GameData_enums import Attribute
        from Py4GWCoreLib.enums_src.GameData_enums import Profession
        from Py4GWCoreLib.enums_src.GameData_enums import ProfessionShort
        from Py4GWCoreLib.enums_src.GameData_enums import ProfessionShort_Names
        from Py4GWCoreLib.enums_src.Texture_enums import ProfessionTextureMap
        from Py4GWCoreLib.py4gwcorelib_src.Utils import Utils

        encoded = ''.join(Utils.base64_to_bin64(char) for char in code)
        if len(encoded) < 4 or Utils.bin64_to_dec(encoded[:4]) != 14:
            return None

        primary, secondary, attributes, skills = Utils.ParseSkillbarTemplate(code)
        primary_id = int(primary or 0)
        secondary_id = int(secondary or 0)
        profession_ids = {int(profession) for profession in Profession}
        if primary_id not in profession_ids:
            return None
        if secondary_id not in profession_ids:
            return None
        if not isinstance(skills, list) or len(skills) != 8:
            return None

        primary_label = ProfessionShort_Names.get(ProfessionShort(primary_id), '') if primary_id else ''
        secondary_label = ProfessionShort_Names.get(ProfessionShort(secondary_id), '') if secondary_id else ''
        profession_label = '/'.join(
            label for label in [primary_label, secondary_label] if label and label != 'None'
        )
        profession_icon_name = ProfessionTextureMap.get(primary_id, '')
        profession_icon_path = f'Textures\\Profession_Icons\\{profession_icon_name}' if profession_icon_name else ''

        attribute_parts: list[str] = []
        if isinstance(attributes, dict):
            for attribute_id, level in attributes.items():
                level = int(level or 0)
                if level <= 0:
                    continue
                try:
                    attribute_name = _human_enum_name(Attribute(int(attribute_id)).name)
                except Exception:
                    attribute_name = f'Attribute {int(attribute_id)}'
                attribute_parts.append(f'{attribute_name} {level}')

        skill_ids = [max(0, int(skill_id or 0)) for skill_id in skills[:8]]
        skill_names: list[str] = []
        skill_icon_paths: list[str] = []
        for skill_id in skill_ids:
            if skill_id <= 0:
                skill_names.append('')
                skill_icon_paths.append('')
                continue
            try:
                skill_name = (
                    Skill.GetNameFromWiki(skill_id)
                    or Skill.GetName(skill_id)
                    or f'Skill {skill_id}'
                )
            except Exception:
                skill_name = f'Skill {skill_id}'
            try:
                icon_path = Skill.ExtraData.GetTexturePath(skill_id)
            except Exception:
                icon_path = ''
            skill_names.append(str(skill_name or f'Skill {skill_id}'))
            skill_icon_paths.append(str(icon_path or ''))

        return SkillTemplatePreview(
            template_name=name or 'Template',
            primary_profession_id=primary_id,
            secondary_profession_id=secondary_id,
            profession_label=profession_label,
            profession_icon_path=profession_icon_path,
            attribute_summary=', '.join(attribute_parts),
            skill_ids=skill_ids,
            skill_names=skill_names,
            skill_icon_paths=skill_icon_paths,
        )
    except Exception:
        return None


def classify_template_profession(template: HeroTemplateEntry | str) -> TemplateProfessionGroup:
    if isinstance(template, HeroTemplateEntry):
        code = str(template.code or '').strip()
    else:
        code = str(template or '').strip()

    if not code:
        return TemplateProfessionGroup(
            group_key='unknown_empty',
            label='Unknown / Empty',
            sort_order=900,
        )
    if len(code) < 16 or not re.fullmatch(r'[A-Za-z0-9+/]+', code):
        return TemplateProfessionGroup(
            group_key='unknown_invalid',
            label='Unknown / Invalid',
            sort_order=901,
        )

    try:
        from Py4GWCoreLib.enums_src.GameData_enums import Profession
        from Py4GWCoreLib.enums_src.GameData_enums import Profession_Names
        from Py4GWCoreLib.py4gwcorelib_src.Utils import Utils

        encoded = ''.join(Utils.base64_to_bin64(char) for char in code)
        if len(encoded) < 4 or Utils.bin64_to_dec(encoded[:4]) != 14:
            return TemplateProfessionGroup(
                group_key='unknown_invalid',
                label='Unknown / Invalid',
                sort_order=901,
            )

        primary, _secondary, _attributes, _skills = Utils.ParseSkillbarTemplate(code)
        primary_id = int(primary or 0)
        profession = Profession(primary_id)
        label = str(Profession_Names.get(profession, '') or '').strip()
        if primary_id <= 0 or not label or label == 'None':
            return TemplateProfessionGroup(
                group_key='unknown_no_profession',
                label='Unknown / No Profession',
                sort_order=902,
            )
        return TemplateProfessionGroup(
            group_key=f'profession_{primary_id}',
            label=label,
            sort_order=primary_id,
            primary_profession_id=primary_id,
            is_known_profession=True,
        )
    except Exception:
        return TemplateProfessionGroup(
            group_key='unknown_invalid',
            label='Unknown / Invalid',
            sort_order=901,
        )


def add_team(config: HeroTeamConfig, name: str = 'New Hero Team') -> HeroTeamSetup:
    team = new_team(name)
    config.teams.append(team)
    config.active_team_id = team.team_id
    return team


def duplicate_team(config: HeroTeamConfig, team_id: str) -> HeroTeamSetup | None:
    source = get_team(config, team_id)
    if source is None:
        return None
    team = HeroTeamSetup(
        team_id=_new_id('team', f'{source.name} Copy'),
        name=f'{source.name} Copy',
        slots=deepcopy(normalize_slots(source.slots)),
    )
    config.teams.append(team)
    config.active_team_id = team.team_id
    return team


def delete_team(config: HeroTeamConfig, team_id: str) -> bool:
    if len(config.teams) <= 1:
        return False
    before = len(config.teams)
    config.teams = [team for team in config.teams if team.team_id != team_id]
    if len(config.teams) == before:
        return False
    if config.active_team_id == team_id:
        config.active_team_id = config.teams[0].team_id
    return True


def add_template(
    config: HeroTeamConfig,
    name: str = 'New Template',
    code: str = '',
    hero_id: int = 0,
) -> HeroTemplateEntry:
    template = new_template(name=name, code=code, hero_id=hero_id)
    config.templates.append(template)
    return template


def delete_template(config: HeroTeamConfig, template_id: str) -> bool:
    before = len(config.templates)
    config.templates = [template for template in config.templates if template.template_id != template_id]
    if len(config.templates) == before:
        return False
    for team in config.teams:
        for slot in team.slots:
            if slot.template_id == template_id:
                slot.template_id = ''
    return True


def dedupe_team_slots(team: HeroTeamSetup) -> tuple[int, list[int]]:
    seen: set[int] = set()
    cleared: list[int] = []
    slots = normalize_slots(team.slots)
    for index, slot in enumerate(slots):
        hero_id = _coerce_hero_id(slot.hero_id)
        if hero_id <= 0:
            continue
        if hero_id in seen:
            slot.hero_id = 0
            slot.template_id = ''
            slot.template_code = ''
            slot.behavior = HERO_BEHAVIOR_DONT_CHANGE
            cleared.append(index)
            continue
        seen.add(hero_id)
    team.slots = slots
    return len(cleared), cleared


def _existing_slot_assignments(team: HeroTeamSetup | None) -> dict[int, tuple[str, str]]:
    assignments: dict[int, tuple[str, str]] = {}
    if team is None:
        return assignments
    for slot in normalize_slots(team.slots):
        hero_id = _coerce_hero_id(slot.hero_id)
        if hero_id > 0 and hero_id not in assignments:
            assignments[hero_id] = (str(slot.template_id or ''), str(slot.template_code or ''))
    return assignments


def _detect_current_party_hero_display_name(hero_member, hero_id: int) -> str:
    if hero_id not in MERCENARY_HERO_IDS:
        return ''
    agent_id = int(getattr(hero_member, 'agent_id', 0) or 0)
    name = ''
    if agent_id > 0:
        try:
            from Py4GWCoreLib.Agent import Agent

            name = _clean_display_name(Agent.GetNameByID(agent_id))
        except Exception:
            name = ''
    if not name:
        try:
            hero_id_obj = getattr(hero_member, 'hero_id', None)
            if hero_id_obj is not None and hasattr(hero_id_obj, 'GetName'):
                name = _clean_display_name(hero_id_obj.GetName())
        except Exception:
            name = ''

    generic_name = HERO_ID_TO_NAME.get(hero_id, '')
    return name if name and name != generic_name else ''


def save_current_party_as_team(
    config: HeroTeamConfig,
    *,
    team_id: str | None = None,
    team_name: str | None = None,
    party_api=None,
) -> tuple[HeroTeamSetup, int]:
    if party_api is None:
        from Py4GWCoreLib.GlobalCache import GLOBAL_CACHE

        party_api = GLOBAL_CACHE.Party

    team = get_team(config, team_id)
    existing_assignments = _existing_slot_assignments(team)
    slots: list[HeroTeamSlot] = []
    seen: set[int] = set()
    detected_names: dict[str, str] = {}

    for hero_member in party_api.GetHeroes() or []:
        hero_id = _coerce_hero_id(hero_id_from_member(hero_member))
        if hero_id <= 0 or hero_id in seen:
            continue
        seen.add(hero_id)
        template_id, template_code = existing_assignments.get(hero_id, ('', ''))
        slots.append(
            HeroTeamSlot(
                hero_id=hero_id,
                template_id=template_id,
                template_code=template_code,
                behavior=HERO_BEHAVIOR_DONT_CHANGE,
            )
        )

        display_name = _detect_current_party_hero_display_name(hero_member, hero_id)
        if display_name:
            detected_names[str(hero_id)] = display_name

        if len(slots) >= HERO_SLOT_COUNT:
            break

    if not seen:
        if team is None:
            raise ValueError('No selected team and no current party heroes to save.')
        return team, 0

    if team is None:
        team = add_team(config, team_name or 'Current Hero Team')
    if team_name is not None:
        team.name = str(team_name or 'Current Hero Team')

    while len(slots) < HERO_SLOT_COUNT:
        slots.append(HeroTeamSlot())

    team.slots = slots
    config.active_team_id = team.team_id
    for hero_id, display_name in detected_names.items():
        if not hero_alias(config, int(hero_id)):
            config.hero_names[hero_id] = display_name
    return team, min(len(seen), HERO_SLOT_COUNT)


def current_party_hero_targets(
    config: HeroTeamConfig | None = None,
    *,
    party_api=None,
    player_agent_id: int | None = None,
    only_owned: bool = True,
) -> list[CurrentPartyHeroTarget]:
    if party_api is None:
        from Py4GWCoreLib.GlobalCache import GLOBAL_CACHE

        party_api = GLOBAL_CACHE.Party
    if player_agent_id is None:
        try:
            from Py4GWCoreLib.Player import Player

            player_agent_id = int(Player.GetAgentID() or 0)
        except Exception:
            player_agent_id = 0

    try:
        player_count = int(party_api.GetPlayerCount() or 0)
    except Exception:
        player_count = 0

    _prune_current_party_hero_profession_cache(party_api)

    targets: list[CurrentPartyHeroTarget] = []
    for hero_index, hero_member in enumerate(party_api.GetHeroes() or [], start=1):
        owner_agent_id = 0
        try:
            players_api = getattr(party_api, 'Players', None)
            owner_login = int(getattr(hero_member, 'owner_player_id', 0) or 0)
            if players_api is not None and owner_login > 0:
                owner_agent_id = int(players_api.GetAgentIDByLoginNumber(owner_login) or 0)
        except Exception:
            owner_agent_id = 0
        if only_owned and int(player_agent_id or 0) > 0:
            if owner_agent_id > 0 and owner_agent_id != int(player_agent_id):
                continue
            if player_count > 1 and owner_agent_id <= 0:
                continue

        hero_id = _coerce_hero_id(hero_id_from_member(hero_member))
        if hero_id <= 0:
            continue
        primary_id, secondary_id, agent_id = _current_party_hero_profession_ids(
            hero_member,
            party_api,
            hero_index,
            hero_id,
            config,
        )
        detected_name = _detect_current_party_hero_display_name(hero_member, hero_id)
        hero_name = hero_alias(config, hero_id) if config is not None else ''
        hero_name = hero_name or detected_name or hero_default_name(hero_id)
        targets.append(
            CurrentPartyHeroTarget(
                hero_index=int(hero_index),
                hero_id=hero_id,
                hero_name=hero_name,
                agent_id=agent_id,
                primary_profession_id=primary_id,
                secondary_profession_id=secondary_id,
                profession_label=_profession_short_label(primary_id, secondary_id),
            )
        )
    return targets


def current_party_hero_targets_for_template(
    config: HeroTeamConfig | None,
    template: HeroTemplateEntry,
    *,
    party_api=None,
    player_agent_id: int | None = None,
    only_owned: bool = True,
) -> list[CurrentPartyHeroTarget]:
    preview = summarize_skill_template(template)
    if preview is None:
        return []
    template_primary_id = int(preview.primary_profession_id or 0)
    if template_primary_id <= 0:
        return []
    return [
        target
        for target in current_party_hero_targets(
            config,
            party_api=party_api,
            player_agent_id=player_agent_id,
            only_owned=only_owned,
        )
        if int(target.primary_profession_id or 0) == template_primary_id
    ]


def _find_current_party_hero_target(
    targets: list[CurrentPartyHeroTarget],
    *,
    target_hero_id: int = 0,
    target_hero_index: int = 0,
) -> CurrentPartyHeroTarget | None:
    hero_id = _coerce_hero_id(target_hero_id)
    hero_index = int(target_hero_index or 0)
    if hero_id > 0 and hero_index > 0:
        for target in targets:
            if target.hero_id == hero_id and target.hero_index == hero_index:
                return target
    if hero_id > 0:
        matches = [target for target in targets if target.hero_id == hero_id]
        if len(matches) == 1:
            return matches[0]
    if hero_id <= 0 and hero_index > 0:
        for target in targets:
            if target.hero_index == hero_index:
                return target
    return None


def apply_template_to_current_party_hero(
    config: HeroTeamConfig | None,
    template: HeroTemplateEntry,
    *,
    target_hero_id: int = 0,
    target_hero_index: int = 0,
    party_api=None,
    skillbar_api=None,
    map_api=None,
) -> ApplyTemplateToHeroResult:
    template_name = str(getattr(template, 'name', '') or 'Template')
    template_code = str(getattr(template, 'code', '') or '').strip()
    preview = summarize_skill_template(template)
    if not template_code or preview is None:
        return ApplyTemplateToHeroResult(False, 'Template not applied: template code could not be parsed.')

    if party_api is None or skillbar_api is None:
        from Py4GWCoreLib.GlobalCache import GLOBAL_CACHE

        party_api = party_api or GLOBAL_CACHE.Party
        skillbar_api = skillbar_api or GLOBAL_CACHE.SkillBar
    if map_api is None:
        from Py4GWCoreLib.Map import Map

        map_api = Map

    try:
        if not map_api.IsOutpost():
            return ApplyTemplateToHeroResult(False, 'Template not applied: current map is not an outpost.')
    except Exception:
        return ApplyTemplateToHeroResult(False, 'Template not applied: could not verify current map.')
    try:
        if not party_api.IsPartyLoaded():
            return ApplyTemplateToHeroResult(False, 'Template not applied: party is not loaded.')
    except Exception:
        return ApplyTemplateToHeroResult(False, 'Template not applied: could not read current party.')
    try:
        if not party_api.IsPartyLeader():
            return ApplyTemplateToHeroResult(False, 'Template not applied: current character is not party leader.')
    except Exception:
        return ApplyTemplateToHeroResult(False, 'Template not applied: could not verify party leader.')

    targets = current_party_hero_targets(config, party_api=party_api, only_owned=True)
    target = _find_current_party_hero_target(
        targets,
        target_hero_id=target_hero_id,
        target_hero_index=target_hero_index,
    )
    if target is None:
        return ApplyTemplateToHeroResult(False, 'Template not applied: selected hero is not in the current party.')

    template_primary_id = int(preview.primary_profession_id or 0)
    target_primary_id = int(target.primary_profession_id or 0)
    if template_primary_id <= 0:
        return ApplyTemplateToHeroResult(False, 'Template not applied: template code could not be parsed.')
    if target_primary_id <= 0:
        return ApplyTemplateToHeroResult(
            False,
            f'Template not applied: could not read profession for {target.hero_name}.',
            hero_id=target.hero_id,
            hero_index=target.hero_index,
        )
    if template_primary_id != target_primary_id:
        template_profession = _profession_name(template_primary_id) or f'profession {template_primary_id}'
        target_profession = _profession_name(target_primary_id) or f'profession {target_primary_id}'
        return ApplyTemplateToHeroResult(
            False,
            f'Template not applied: {template_name} is {template_profession}, '
            f'but {target.hero_name} is {target_profession}.',
            hero_id=target.hero_id,
            hero_index=target.hero_index,
        )

    try:
        skillbar_api.LoadHeroSkillTemplate(int(target.hero_index), template_code)
    except Exception as exc:
        return ApplyTemplateToHeroResult(
            False,
            f'Template apply failed for {target.hero_name}: {exc}',
            hero_id=target.hero_id,
            hero_index=target.hero_index,
        )

    return ApplyTemplateToHeroResult(
        True,
        f'Template apply queued: {template_name} -> {target.hero_name}.',
        hero_id=target.hero_id,
        hero_index=target.hero_index,
    )


def resolve_slot_template_code(slot: HeroTeamSlot, templates: list[HeroTemplateEntry]) -> tuple[str, str]:
    inline_code = str(slot.template_code or '').strip()
    if inline_code:
        return inline_code, 'Inline'
    template_id = str(slot.template_id or '').strip()
    if not template_id:
        return '', ''
    for template in templates:
        if template.template_id == template_id:
            return str(template.code or '').strip(), str(template.name or '')
    return '', ''


def build_load_plan(
    team: HeroTeamSetup,
    templates: list[HeroTemplateEntry],
    max_heroes: int = HERO_SLOT_COUNT,
    hero_names: dict[str, str] | None = None,
) -> HeroTeamLoadPlan:
    plan = HeroTeamLoadPlan()
    seen: set[int] = set()
    max_heroes = max(0, int(max_heroes))
    for index, slot in enumerate(normalize_slots(team.slots)):
        hero_id = _coerce_hero_id(slot.hero_id)
        if hero_id <= 0:
            plan.skipped_empty.append(index)
            continue
        if hero_id in seen:
            plan.skipped_duplicates.append(index)
            continue
        if len(plan.slots) >= max_heroes:
            plan.truncated_slots.append(index)
            continue
        seen.add(hero_id)
        template_code, template_name = resolve_slot_template_code(slot, templates)
        template_assigned = bool(str(slot.template_id or '').strip() or str(slot.template_code or '').strip())
        clear_skillbar = not template_assigned
        plan.slots.append(
            ResolvedHeroSlot(
                slot_index=index,
                hero_id=hero_id,
                hero_name=_hero_display_name_from_aliases(hero_names, hero_id),
                template_code=template_code,
                template_name=template_name or (EMPTY_SKILLBAR_TEMPLATE_NAME if clear_skillbar else ''),
                template_assigned=template_assigned,
                template_missing=template_assigned and not bool(template_code),
                clear_skillbar=clear_skillbar,
                behavior=_coerce_behavior(slot.behavior),
            )
        )
    return plan


def _add_row_warning(
    preflight: HeroTeamLoadPreflight,
    slot_index: int,
    code: str,
    message: str,
    severity: str = 'warning',
) -> None:
    warnings = preflight.row_warnings.setdefault(int(slot_index), [])
    if any(warning.code == code for warning in warnings):
        return
    warnings.append(
        HeroTeamRowWarning(
            slot_index=int(slot_index),
            code=str(code),
            message=str(message),
            severity=str(severity or 'warning'),
        )
    )


def _runtime_preflight_max_heroes(
    preflight: HeroTeamLoadPreflight,
    *,
    include_runtime: bool,
    leave_party_first: bool,
    clear_existing: bool,
    map_api=None,
    party_api=None,
) -> int:
    max_heroes = HERO_SLOT_COUNT
    if not include_runtime:
        return max_heroes

    if map_api is None:
        try:
            from Py4GWCoreLib.Map import Map

            map_api = Map
        except Exception:
            map_api = None
    if party_api is None:
        try:
            from Py4GWCoreLib.GlobalCache import GLOBAL_CACHE

            party_api = GLOBAL_CACHE.Party
        except Exception:
            party_api = None

    if map_api is None:
        preflight.blocking_messages.append('Load skipped: could not verify current map.')
    else:
        try:
            if not map_api.IsOutpost():
                preflight.blocking_messages.append('Load skipped: current map is not an outpost.')
        except Exception:
            preflight.blocking_messages.append('Load skipped: could not verify current map.')

    if party_api is not None and not leave_party_first:
        try:
            if not party_api.IsPartyLeader():
                preflight.blocking_messages.append('Load skipped: current character is not party leader.')
        except Exception:
            preflight.blocking_messages.append('Load skipped: could not verify party leader.')

    if leave_party_first:
        try:
            map_size = int(map_api.GetMaxPartySize() or 0) if map_api is not None else 0
        except Exception:
            map_size = 0
        if map_size > 0:
            max_heroes = max(0, min(HERO_SLOT_COUNT, map_size - 1))
        if party_api is not None:
            try:
                if (
                    int(party_api.GetPlayerCount() or 0) > 1
                    or int(party_api.GetHeroCount() or 0) > 0
                    or int(party_api.GetHenchmanCount() or 0) > 0
                    or not bool(party_api.IsPartyLeader())
                ):
                    preflight.warnings.append('Load will leave the current party before loading this team.')
            except Exception:
                pass
    elif clear_existing:
        try:
            map_size = int(map_api.GetMaxPartySize() or 0) if map_api is not None else 0
        except Exception:
            map_size = 0
        if map_size > 0:
            try:
                player_count = int(party_api.GetPlayerCount() or 1) if party_api is not None else 1
            except Exception:
                player_count = 1
            max_heroes = max(0, min(HERO_SLOT_COUNT, map_size - max(1, player_count)))
    else:
        try:
            max_heroes = hero_slot_capacity(map_api=map_api, party_api=party_api, default=HERO_SLOT_COUNT)
        except Exception:
            max_heroes = HERO_SLOT_COUNT

    if max_heroes <= 0:
        preflight.blocking_messages.append('Load skipped: there is no available hero slot in this party.')
    return max_heroes


def build_load_preflight(
    config: HeroTeamConfig,
    team_id: str | None = None,
    *,
    include_runtime: bool = False,
    leave_party_first: bool = False,
    clear_existing: bool = True,
    map_api=None,
    party_api=None,
) -> HeroTeamLoadPreflight:
    preflight = HeroTeamLoadPreflight()
    team = get_team(config, team_id)
    if team is None:
        preflight.blocking_messages.append('Load skipped: no team selected.')
        return preflight

    max_heroes = _runtime_preflight_max_heroes(
        preflight,
        include_runtime=include_runtime,
        leave_party_first=leave_party_first,
        clear_existing=clear_existing,
        map_api=map_api,
        party_api=party_api,
    )
    preflight.max_heroes = max_heroes
    preflight.plan = build_load_plan(
        team,
        config.templates,
        max_heroes=max_heroes,
        hero_names=config.hero_names,
    )

    slots = normalize_slots(team.slots)
    templates_by_id = {str(template.template_id): template for template in config.templates}

    for slot_index in preflight.plan.skipped_empty:
        _add_row_warning(preflight, slot_index, 'skipped_empty', 'Empty slot will be skipped.', 'info')
    for slot_index in preflight.plan.skipped_duplicates:
        _add_row_warning(
            preflight,
            slot_index,
            'duplicate_hero',
            'Duplicate hero; only the first copy will load.',
            'warning',
        )
    for slot_index in preflight.plan.truncated_slots:
        _add_row_warning(
            preflight,
            slot_index,
            'truncated_slot',
            'No available party slot; this row will not load.',
            'warning',
        )

    for slot_index, slot in enumerate(slots):
        hero_id = _coerce_hero_id(slot.hero_id)
        if hero_id <= 0:
            continue
        template_id = str(slot.template_id or '').strip()
        inline_code = str(slot.template_code or '').strip()
        if not template_id:
            continue
        template = templates_by_id.get(template_id)
        if template is None:
            _add_row_warning(
                preflight,
                slot_index,
                'missing_template_reference',
                'Assigned template is missing; no template will be applied.',
                'warning',
            )
            continue
        if not inline_code and not str(template.code or '').strip():
            _add_row_warning(
                preflight,
                slot_index,
                'empty_assigned_template',
                'Assigned template has no code; no template will be applied.',
                'warning',
            )

    for resolved_slot in preflight.plan.slots:
        if resolved_slot.template_missing:
            _add_row_warning(
                preflight,
                resolved_slot.slot_index,
                'missing_template_code',
                'Assigned template could not be resolved; no template will be applied.',
                'warning',
            )

    if not preflight.plan.slots:
        preflight.blocking_messages.append('Load skipped: selected team has no non-empty hero slots.')

    warning_count = sum(
        1
        for warnings in preflight.row_warnings.values()
        for warning in warnings
        if warning.severity != 'info'
    )
    if warning_count:
        preflight.warnings.append(f'{warning_count} row warning{"s" if warning_count != 1 else ""}.')
    return preflight


def _current_hero_slot_capacity() -> int:
    try:
        from Py4GWCoreLib.GlobalCache import GLOBAL_CACHE
        from Py4GWCoreLib.Map import Map

        return hero_slot_capacity(map_api=Map, party_api=GLOBAL_CACHE.Party, default=HERO_SLOT_COUNT)
    except Exception:
        return HERO_SLOT_COUNT


def _empty_skillbar_template_for_hero_position(hero_index: int, party_api=None) -> str:
    hero_index = int(hero_index or 0)
    if hero_index <= 0:
        return ''

    if party_api is None:
        try:
            from Py4GWCoreLib.GlobalCache import GLOBAL_CACHE

            party_api = GLOBAL_CACHE.Party
        except Exception:
            party_api = None

    hero_member = _hero_member_by_party_position(party_api, hero_index)
    hero_id = _coerce_hero_id(hero_id_from_member(hero_member)) if hero_member is not None else 0
    if hero_member is not None:
        primary_id, secondary_id, agent_id = _current_party_hero_profession_ids(
            hero_member,
            party_api,
            hero_index,
            hero_id,
        )
    else:
        agent_id = _hero_agent_id_by_party_position(party_api, hero_index)
        primary_id, secondary_id = _agent_profession_ids(agent_id)
        if primary_id <= 0:
            primary_id = _agent_primary_profession_id_from_attributes(agent_id)
        if primary_id > 0:
            _remember_current_party_hero_profession(hero_id, agent_id, primary_id, secondary_id)
    if primary_id <= 0:
        return ''

    try:
        from Py4GWCoreLib.py4gwcorelib_src.Utils import Utils

        return Utils.GenerateSkillbarTemplateFrom(primary_id, secondary_id, {}, [0] * 8)
    except Exception:
        return ''


class HeroTeamApplyOperation:
    def __init__(
        self,
        team: HeroTeamSetup,
        templates: list[HeroTemplateEntry],
        *,
        hero_names: dict[str, str] | None = None,
        leave_party_first: bool = False,
        clear_existing: bool = True,
        leave_timeout_ms: int = 5000,
        leave_poll_ms: int = 250,
        add_delay_ms: int = 250,
        post_kick_wait_ms: int = 500,
        post_add_wait_ms: int = 1000,
        template_delay_ms: int = 500,
    ) -> None:
        self.team = deepcopy(team)
        self.templates = deepcopy(templates)
        self.hero_names = dict(hero_names or {})
        self.leave_party_first = bool(leave_party_first)
        self.clear_existing = bool(clear_existing)
        self.leave_timeout_ms = max(0, int(leave_timeout_ms))
        self.leave_poll_ms = max(50, int(leave_poll_ms))
        self.add_delay_ms = max(0, int(add_delay_ms))
        self.post_kick_wait_ms = max(0, int(post_kick_wait_ms))
        self.post_add_wait_ms = max(0, int(post_add_wait_ms))
        self.template_delay_ms = max(0, int(template_delay_ms))

        self.plan = HeroTeamLoadPlan()
        self.state = 'pending'
        self.message = 'Pending.'
        self.done = False
        self.success = False
        self.added_hero_ids: list[int] = []
        self.applied_template_hero_ids: list[int] = []
        self.cleared_skillbar_hero_ids: list[int] = []
        self.applied_behavior_hero_ids: list[int] = []
        self.missing_hero_ids: list[int] = []
        self.failed_template_slots: list[ResolvedHeroSlot] = []

        self._phase = 'leave_party' if self.leave_party_first else 'validate'
        self._next_at = 0.0
        self._leave_dispatched = False
        self._leave_deadline = 0.0
        self._add_index = 0
        self._behavior_index = 0
        self._template_index = 0

    def _wait(self, ms: int) -> None:
        self._next_at = monotonic() + (max(0, int(ms)) / 1000.0)

    def _ready(self) -> bool:
        return monotonic() >= self._next_at

    def _finish(self, success: bool, message: str) -> None:
        self.done = True
        self.success = bool(success)
        self.state = 'done' if success else 'failed'
        self.message = message

    def _party_loaded(self, party_api) -> bool:
        try:
            return bool(party_api.IsPartyLoaded())
        except Exception:
            return False

    def _party_player_count(self, party_api) -> int:
        try:
            return int(party_api.GetPlayerCount() or 0)
        except Exception:
            return 0

    def _party_hero_count(self, party_api) -> int:
        try:
            return int(party_api.GetHeroCount() or 0)
        except Exception:
            return 0

    def _party_henchman_count(self, party_api) -> int:
        try:
            return int(party_api.GetHenchmanCount() or 0)
        except Exception:
            return 0

    def _is_party_leader(self, party_api) -> bool:
        try:
            return bool(party_api.IsPartyLeader())
        except Exception:
            return False

    def _needs_leave_party(self, party_api) -> bool:
        return (
            self._party_player_count(party_api) > 1
            or self._party_hero_count(party_api) > 0
            or self._party_henchman_count(party_api) > 0
            or not self._is_party_leader(party_api)
        )

    def _party_settled_after_leave(self, party_api) -> bool:
        if not self._party_loaded(party_api):
            return False
        return (
            self._party_player_count(party_api) <= 1
            and self._party_henchman_count(party_api) <= 0
            and self._is_party_leader(party_api)
        )

    def _slot_label(self, slot: ResolvedHeroSlot, *, include_slot: bool = False) -> str:
        label = str(slot.hero_name or hero_default_name(slot.hero_id))
        return f'H{slot.slot_index + 1}: {label}' if include_slot else label

    def _template_slot_label(self, slot: ResolvedHeroSlot) -> str:
        label = self._slot_label(slot, include_slot=True)
        template_name = str(slot.template_name or '').strip()
        return f'{label} ({template_name})' if template_name else label

    def _join_labels(self, values: list[str]) -> str:
        return ', '.join(str(value) for value in values if str(value or '').strip())

    def _count_label(self, count: int, singular: str, plural: str | None = None) -> str:
        count = int(count)
        return f'{count} {singular if count == 1 else plural or singular + "s"}'

    def _final_status(self) -> str:
        missing_ids = set(int(hero_id) for hero_id in self.missing_hero_ids)
        loaded_count = len([slot for slot in self.plan.slots if int(slot.hero_id) not in missing_ids])
        template_count = len(self.applied_template_hero_ids)
        clear_count = len(self.cleared_skillbar_hero_ids)
        behavior_count = len(self.applied_behavior_hero_ids)
        details: list[str] = [f'Loaded {self._count_label(loaded_count, "hero", "heroes")}']
        if behavior_count:
            details.append(f'applied {self._count_label(behavior_count, "behavior setting")}')
        if template_count:
            details.append(f'applied {self._count_label(template_count, "template")}')
        if clear_count:
            details.append(f'cleared {self._count_label(clear_count, "skill bar")}')
        if self.plan.skipped_duplicates:
            details.append(f'skipped {self._count_label(len(self.plan.skipped_duplicates), "duplicate")}')
        if self.plan.truncated_slots:
            details.append(f'truncated {self._count_label(len(self.plan.truncated_slots), "slot")}')
        if missing_ids:
            details.append(f'missing {self._count_label(len(missing_ids), "hero", "heroes")}')

        messages = [', '.join(details) + '.']
        missing_slots = [slot for slot in self.plan.slots if int(slot.hero_id) in missing_ids]
        if missing_slots:
            messages.append(f'Failed to add: {self._join_labels([self._slot_label(slot) for slot in missing_slots])}.')

        missing_template_slots = [slot for slot in self.plan.slots if slot.template_missing]
        if missing_template_slots:
            labels = [self._template_slot_label(slot) for slot in missing_template_slots]
            messages.append(f'Missing template for: {self._join_labels(labels)}.')

        applied_template_ids = set(int(hero_id) for hero_id in self.applied_template_hero_ids)
        cleared_skillbar_ids = set(int(hero_id) for hero_id in self.cleared_skillbar_hero_ids)
        unapplied_template_slots = [
            slot
            for slot in self.plan.slots
            if (
                (slot.template_code and int(slot.hero_id) not in applied_template_ids)
                or (slot.clear_skillbar and int(slot.hero_id) not in cleared_skillbar_ids)
            )
        ]
        if self.failed_template_slots:
            failed_ids = {int(slot.hero_id) for slot in self.failed_template_slots}
            unapplied_template_slots = [
                slot for slot in unapplied_template_slots if int(slot.hero_id) not in failed_ids
            ] + self.failed_template_slots
        if unapplied_template_slots:
            labels = [self._template_slot_label(slot) for slot in unapplied_template_slots]
            messages.append(f'Template not applied for: {self._join_labels(labels)}.')

        return ' '.join(messages)

    def tick(self) -> bool:
        if self.done:
            return True
        if not self._ready():
            return False

        try:
            self._tick()
        except Exception as exc:
            self._finish(False, f'Hero team load failed: {exc}')
        return self.done

    def _tick(self) -> None:
        from Py4GWCoreLib.GlobalCache import GLOBAL_CACHE
        from Py4GWCoreLib.Map import Map

        if self._phase == 'leave_party':
            if not Map.IsOutpost():
                self._finish(False, 'Load skipped: current map is not an outpost.')
                return

            if self._leave_deadline <= 0:
                self._leave_deadline = monotonic() + (self.leave_timeout_ms / 1000.0)

            if not self._party_loaded(GLOBAL_CACHE.Party):
                if monotonic() >= self._leave_deadline:
                    self._finish(False, 'Load skipped: could not leave current party.')
                    return
                self.message = 'Waiting for party state.'
                self._wait(self.leave_poll_ms)
                return

            if not self._leave_dispatched and not self._needs_leave_party(GLOBAL_CACHE.Party):
                self._phase = 'validate'
            elif not self._leave_dispatched:
                GLOBAL_CACHE.Party.LeaveParty()
                self._leave_dispatched = True
                self.message = 'Leaving current party.'
                self._wait(self.leave_poll_ms)
                return
            elif self._party_settled_after_leave(GLOBAL_CACHE.Party):
                self._phase = 'validate'
                self.message = 'Current party left. Loading team.'
            elif monotonic() >= self._leave_deadline:
                self._finish(False, 'Load skipped: could not leave current party.')
                return
            else:
                self.message = 'Waiting to leave current party.'
                self._wait(self.leave_poll_ms)
                return

        if self._phase == 'validate':
            if not Map.IsOutpost():
                self._finish(False, 'Load skipped: current map is not an outpost.')
                return
            if not GLOBAL_CACHE.Party.IsPartyLeader():
                self._finish(False, 'Load skipped: current character is not party leader.')
                return

            capacity = _current_hero_slot_capacity()
            if capacity <= 0:
                self._finish(False, 'Load skipped: there is no available hero slot in this party.')
                return
            self.plan = build_load_plan(
                self.team,
                self.templates,
                max_heroes=capacity,
                hero_names=self.hero_names,
            )
            if not self.plan.slots:
                self._finish(False, 'Load skipped: selected team has no non-empty hero slots.')
                return

            if self.clear_existing:
                GLOBAL_CACHE.Party.Heroes.KickAllHeroes()
                self.message = 'Clearing current heroes.'
                self._phase = 'add'
                self._wait(self.post_kick_wait_ms)
                return

            self._phase = 'add'
            self.message = 'Adding heroes.'

        if self._phase == 'add':
            if self._add_index >= len(self.plan.slots):
                self._phase = 'wait_after_add'
                self.message = 'Waiting for heroes to join.'
                self._wait(self.post_add_wait_ms)
                return
            slot = self.plan.slots[self._add_index]
            GLOBAL_CACHE.Party.Heroes.AddHero(int(slot.hero_id))
            self.added_hero_ids.append(int(slot.hero_id))
            self._add_index += 1
            self.message = f'Adding {slot.hero_name}.'
            self._wait(self.add_delay_ms)
            return

        if self._phase == 'wait_after_add':
            existing = current_hero_ids(party_api=GLOBAL_CACHE.Party)
            self.missing_hero_ids = [slot.hero_id for slot in self.plan.slots if slot.hero_id not in existing]
            self._phase = 'behavior'
            self.message = 'Applying hero behavior.'

        if self._phase == 'behavior':
            while self._behavior_index < len(self.plan.slots):
                slot = self.plan.slots[self._behavior_index]
                self._behavior_index += 1
                if slot.behavior == HERO_BEHAVIOR_DONT_CHANGE:
                    continue
                position = hero_party_index_one_based(slot.hero_id, party_api=GLOBAL_CACHE.Party)
                if position <= 0:
                    if slot.hero_id not in self.missing_hero_ids:
                        self.missing_hero_ids.append(slot.hero_id)
                    continue
                hero_agent_id = GLOBAL_CACHE.Party.Heroes.GetHeroAgentIDByPartyPosition(position)
                if int(hero_agent_id or 0) <= 0:
                    if slot.hero_id not in self.missing_hero_ids:
                        self.missing_hero_ids.append(slot.hero_id)
                    continue
                GLOBAL_CACHE.Party.Heroes.SetHeroBehavior(int(hero_agent_id), int(slot.behavior))
                self.applied_behavior_hero_ids.append(int(slot.hero_id))
                self.message = f'Applying behavior to {slot.hero_name}.'
                self._wait(100)
                return

            self._phase = 'templates'
            self.message = 'Applying templates.'

        if self._phase == 'templates':
            while self._template_index < len(self.plan.slots):
                slot = self.plan.slots[self._template_index]
                self._template_index += 1
                if not slot.template_code and not slot.clear_skillbar:
                    continue
                position = hero_party_index_one_based(slot.hero_id, party_api=GLOBAL_CACHE.Party)
                if position <= 0:
                    if slot.hero_id not in self.missing_hero_ids:
                        self.missing_hero_ids.append(slot.hero_id)
                    continue
                template_code = slot.template_code
                if slot.clear_skillbar:
                    template_code = _empty_skillbar_template_for_hero_position(position, party_api=GLOBAL_CACHE.Party)
                    if not template_code:
                        self.failed_template_slots.append(slot)
                        continue
                try:
                    GLOBAL_CACHE.SkillBar.LoadHeroSkillTemplate(position, template_code)
                except Exception:
                    self.failed_template_slots.append(slot)
                    continue
                if slot.clear_skillbar:
                    self.cleared_skillbar_hero_ids.append(int(slot.hero_id))
                    self.message = f'Clearing skill bar for {slot.hero_name}.'
                else:
                    self.applied_template_hero_ids.append(int(slot.hero_id))
                    self.message = f'Applying template to {slot.hero_name}.'
                self._wait(self.template_delay_ms)
                return

            self._finish(True, self._final_status())


def create_apply_operation(
    config: HeroTeamConfig,
    team_id: str | None = None,
    *,
    leave_party_first: bool = False,
    clear_existing: bool = True,
) -> HeroTeamApplyOperation:
    team = get_team(config, team_id)
    if team is None:
        raise ValueError('No team selected.')
    return HeroTeamApplyOperation(
        team,
        config.templates,
        hero_names=config.hero_names,
        leave_party_first=leave_party_first,
        clear_existing=clear_existing,
    )
