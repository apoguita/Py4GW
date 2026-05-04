"""
Offline regression checks for Merchant Rules.

This script stubs the runtime-heavy modules that MerchantRules depends on,
loads the real widget module by path, and exercises the logic we most want
to keep stable:

- malformed profile preservation + backup snapshotting
- legacy profile normalization + safe rewrite
- plan building for current preview logic
- preview drift / execute safety gating
- merchant-sell verification outcomes
- multibox preview/execute result formatting and timeout handling
- inventory modifier/support-context cache behavior
- profile recovery and atomic profile rewrite edges

Run:
    python "Widgets/Data/test_merchant_rules_regression.py"
"""

from __future__ import annotations

import enum
import importlib.util
import json
import os
import shutil
import sys
import traceback
import types
from dataclasses import replace
from pathlib import Path


def _find_repo_root(start_path: Path) -> Path:
    current = start_path.resolve()
    if current.is_file():
        current = current.parent

    for candidate in (current, *current.parents):
        merchant_rules_path = candidate / "Widgets" / "Guild Wars" / "Items & Loot" / "MerchantRules.py"
        if merchant_rules_path.is_file():
            return candidate

    raise RuntimeError(f"Could not locate the Py4GW repo root from {start_path}.")


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = _find_repo_root(SCRIPT_DIR)
MERCHANT_RULES_PATH = REPO_ROOT / "Widgets" / "Guild Wars" / "Items & Loot" / "MerchantRules.py"


def _expect(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def _catalog_model_ids(entries: list[dict[str, object]]) -> set[int]:
    model_ids: set[int] = set()
    for entry in entries:
        try:
            model_id = int(entry.get("model_id") or 0)
        except Exception:
            model_id = 0
        if model_id > 0:
            model_ids.add(model_id)
    return model_ids


def _ensure_package(name: str) -> types.ModuleType:
    module = sys.modules.get(name)
    if module is None:
        module = types.ModuleType(name)
        module.__path__ = []
        sys.modules[name] = module
    return module


def _load_real_model_id_enum(repo_root: Path):
    if "PySkill" not in sys.modules:
        class DummySkill:
            def __init__(self, _name):
                self.id = types.SimpleNamespace(id=0)

        py_skill = types.ModuleType("PySkill")
        py_skill.Skill = DummySkill
        sys.modules["PySkill"] = py_skill

    model_enums_path = repo_root / "Py4GWCoreLib" / "enums_src" / "Model_enums.py"
    spec = importlib.util.spec_from_file_location("merchant_rules_regression_model_enums", model_enums_path)
    _expect(spec is not None and spec.loader is not None, "Failed to create import spec for Model_enums.")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module.ModelID


def _load_real_title_enums(repo_root: Path):
    title_enums_path = repo_root / "Py4GWCoreLib" / "enums_src" / "Title_enums.py"
    spec = importlib.util.spec_from_file_location("merchant_rules_regression_title_enums", title_enums_path)
    _expect(spec is not None and spec.loader is not None, "Failed to create import spec for Title_enums.")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module.TitleID, module.TITLE_TIERS


def _install_stub_modules(project_root: Path) -> None:
    class DummyTimer:
        def __init__(self, *_args, **_kwargs):
            pass

        def Reset(self) -> None:
            pass

        def Start(self) -> None:
            pass

        def IsExpired(self) -> bool:
            return True

    class DummyActionQueueManager:
        def IsEmpty(self, *_args, **_kwargs) -> bool:
            return True

    class DummyMessageType:
        Info = "info"
        Warning = "warning"
        Error = "error"
        Success = "success"
        Debug = "debug"

    class DummyConsoleModule:
        MessageType = DummyMessageType

        @staticmethod
        def get_projects_path() -> str:
            return str(project_root)

    real_model_id = _load_real_model_id_enum(REPO_ROOT)
    real_title_id, real_title_tiers = _load_real_title_enums(REPO_ROOT)

    class ItemType(enum.IntEnum):
        Unknown = 0
        Axe = 1
        Bow = 2
        Daggers = 3
        Hammer = 4
        Offhand = 5
        Scythe = 6
        Shield = 7
        Spear = 8
        Staff = 9
        Sword = 10
        Wand = 11
        Headpiece = 12
        Chestpiece = 13
        Gloves = 14
        Leggings = 15
        Boots = 16
        Salvage = 17
        Rune_Mod = 18
        Weapon = 100
        MartialWeapon = 101
        OffhandOrShield = 102
        EquippableItem = 103
        SpellcastingWeapon = 104

    class Attribute(enum.IntEnum):
        None_ = 0

    def _empty_generator(*_args, **_kwargs):
        if False:
            yield None

    py4gw = types.ModuleType("Py4GW")
    py4gw.Console = DummyConsoleModule
    sys.modules["Py4GW"] = py4gw

    imgui = types.ModuleType("PyImGui")
    imgui.WindowFlags = types.SimpleNamespace(NoFlag=0, AlwaysAutoResize=1)
    imgui.SelectableFlags = types.SimpleNamespace(NoFlag=0)
    imgui.TableFlags = types.SimpleNamespace(NoFlag=0, Borders=1, RowBg=2, BordersInnerV=4)
    imgui.TableColumnFlags = types.SimpleNamespace(WidthFixed=1, WidthStretch=2)
    imgui.TreeNodeFlags = types.SimpleNamespace(NoFlag=0, SpanFullWidth=1)
    imgui.ImGuiCol = types.SimpleNamespace(
        Button=0,
        ButtonHovered=1,
        ButtonActive=2,
        Header=3,
        HeaderHovered=4,
        HeaderActive=5,
        Text=6,
    )
    imgui.push_style_color = lambda *_args, **_kwargs: None
    imgui.pop_style_color = lambda *_args, **_kwargs: None
    imgui.checkbox = lambda _label, checked: bool(checked)
    imgui.is_item_hovered = lambda *_args, **_kwargs: False
    sys.modules["PyImGui"] = imgui

    core = types.ModuleType("Py4GWCoreLib")
    core.ActionQueueManager = DummyActionQueueManager
    core.Console = DummyConsoleModule
    core.ConsoleLog = lambda *_args, **_kwargs: None
    core.GLOBAL_CACHE = types.SimpleNamespace()
    core.Map = types.SimpleNamespace(
        GetMapID=lambda: 100,
        GetInstanceUptime=lambda: 0,
        IsMapReady=lambda: True,
        IsOutpost=lambda: True,
        IsGuildHall=lambda: False,
        GetMapName=lambda map_id=0: f"Map {int(map_id)}",
        IsMapIDMatch=lambda current, target: int(current) == int(target),
        GetOutpostIDs=lambda: [],
        GetOutpostNames=lambda: [],
        GetRegion=lambda: (0, 0),
        GetDistrict=lambda: 0,
        GetLanguage=lambda: (0, 0),
    )
    core.ModelID = real_model_id
    core.TitleID = real_title_id
    core.TITLE_TIERS = real_title_tiers
    core.Player = types.SimpleNamespace(
        GetAccountEmail=lambda: "merchant.rules@example.com",
        GetName=lambda: "Merchant Rules Tester",
        GetXY=lambda: (0.0, 0.0),
        GetSkillPointData=lambda: (100, 100),
        GetTitle=lambda _title_id: types.SimpleNamespace(current_points=999999),
    )
    core.Routines = types.SimpleNamespace(
        Yield=types.SimpleNamespace(
            wait=_empty_generator,
            Map=types.SimpleNamespace(TravelToOutpost=_empty_generator),
            Movement=types.SimpleNamespace(FollowPath=_empty_generator),
            Agents=types.SimpleNamespace(InteractWithAgentXY=_empty_generator),
            Merchant=types.SimpleNamespace(SellItems=_empty_generator),
        )
    )
    core.SharedCommandType = types.SimpleNamespace(MerchantRules=1)
    core.ThrottledTimer = DummyTimer
    core.__path__ = []
    sys.modules["Py4GWCoreLib"] = core

    _ensure_package("Py4GWCoreLib.enums_src")
    model_enums = types.ModuleType("Py4GWCoreLib.enums_src.Model_enums")
    model_enums.ModelID = real_model_id
    sys.modules["Py4GWCoreLib.enums_src.Model_enums"] = model_enums

    item_enums = types.ModuleType("Py4GWCoreLib.enums_src.Item_enums")
    item_enums.ItemType = ItemType
    sys.modules["Py4GWCoreLib.enums_src.Item_enums"] = item_enums

    title_enums = types.ModuleType("Py4GWCoreLib.enums_src.Title_enums")
    title_enums.TitleID = real_title_id
    title_enums.TITLE_TIERS = real_title_tiers
    sys.modules["Py4GWCoreLib.enums_src.Title_enums"] = title_enums

    enums_module = types.ModuleType("Py4GWCoreLib.enums")
    enums_module.Attribute = Attribute
    sys.modules["Py4GWCoreLib.enums"] = enums_module

    _ensure_package("Py4GWCoreLib.py4gwcorelib_src")
    widget_manager = types.ModuleType("Py4GWCoreLib.py4gwcorelib_src.WidgetManager")
    widget_manager.get_widget_handler = lambda: types.SimpleNamespace(
        get_widget_info=lambda _name: None,
        is_widget_enabled=lambda _name: False,
    )
    sys.modules["Py4GWCoreLib.py4gwcorelib_src.WidgetManager"] = widget_manager

    _ensure_package("Py4GWCoreLib.modular")
    modular_actions = types.ModuleType("Py4GWCoreLib.modular.actions")
    modular_actions.DEFAULT_NPC_SELECTORS = {}
    modular_actions.SUPPORTED_MAP_NPC_SELECTORS = {}
    modular_actions.resolve_agent_xy_from_step = lambda *_args, **_kwargs: None
    sys.modules["Py4GWCoreLib.modular.actions"] = modular_actions

    _ensure_package("Sources")
    _ensure_package("Sources.marks_sources")
    mods_parser = types.ModuleType("Sources.marks_sources.mods_parser")

    class DummyModDatabase:
        def __init__(self):
            self.weapon_mods = {}
            self.runes = {}

        @staticmethod
        def load(_path: str) -> "DummyModDatabase":
            return DummyModDatabase()

    mods_parser.ModDatabase = DummyModDatabase
    mods_parser.MatchedRuneInfo = type("MatchedRuneInfo", (), {})
    mods_parser.MatchedWeaponModInfo = type("MatchedWeaponModInfo", (), {})
    mods_parser.parse_modifiers = (
        lambda _raw, _item_type, _model_id, _db: types.SimpleNamespace(
            runes=[],
            weapon_mods=[],
            is_rune=False,
            requirements=0,
            attribute=types.SimpleNamespace(name="None_", value=0),
            damage=(0, 0),
            shield_armor=(0, 0),
        )
    )
    sys.modules["Sources.marks_sources.mods_parser"] = mods_parser

    _ensure_package("Sources.modular_bot")
    _ensure_package("Sources.modular_bot.recipes")
    actions_inventory = types.ModuleType("Sources.modular_bot.recipes.actions_inventory")
    actions_inventory.DEFAULT_NPC_SELECTORS = {}
    actions_inventory.SUPPORTED_MAP_NPC_SELECTORS = {}
    actions_inventory._get_nonsalvageable_gold_item_ids = lambda: []
    sys.modules["Sources.modular_bot.recipes.actions_inventory"] = actions_inventory

    step_selectors = types.ModuleType("Sources.modular_bot.recipes.step_selectors")
    step_selectors.resolve_agent_xy_from_step = lambda *_args, **_kwargs: None
    sys.modules["Sources.modular_bot.recipes.step_selectors"] = step_selectors


def _load_merchant_rules_module(project_root: Path):
    _install_stub_modules(project_root)
    module_name = "merchant_rules_regression_target"
    spec = importlib.util.spec_from_file_location(module_name, MERCHANT_RULES_PATH)
    _expect(spec is not None and spec.loader is not None, "Failed to create import spec for MerchantRules.")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def _make_widget(module):
    widget = module.MerchantRulesWidget()
    widget.outpost_entries = [
        {"id": 1, "name": "Temple of Testing"},
        {"id": 2, "name": "Regression Harbor"},
    ]
    widget.catalog_by_model_id = {
        111: {"model_id": 111, "name": "Iron Sword"},
        222: {"model_id": 222, "name": "Bone"},
        555: {"model_id": 555, "name": "Identification Kit"},
        int(module.ECTOPLASM_MODEL_ID): {"model_id": int(module.ECTOPLASM_MODEL_ID), "name": "Glob of Ectoplasm", "material_type": "rare"},
    }
    widget._debug_log = lambda *_args, **_kwargs: None
    widget._log_plan_summary = lambda *_args, **_kwargs: None
    widget._get_multibox_accounts = lambda: []
    widget._get_multibox_display_name_from_email = lambda account_email: str(account_email or "").strip()
    return widget


def _seed_display_sort_fixture(widget) -> None:
    widget.catalog_by_model_id.update(
        {
            100: {"model_id": 100, "name": "alpha"},
            200: {"model_id": 200, "name": "Bravo"},
            300: {"model_id": 300, "name": "zulu"},
            400: {"model_id": 400, "name": "alpha"},
        }
    )
    widget.weapon_mod_names = {
        "mod_z": "Zeal",
        "mod_b": "Shared",
        "mod_a": "shared",
    }
    widget.rune_names = {
        "rune_z": "Zeal Rune",
        "rune_b": "Shared Rune",
        "rune_a": "shared rune",
    }


def _prime_initialized_widget(module, widget):
    widget.catalog_loaded = True
    widget.initialized = True
    widget.account_key = widget._get_account_key()
    widget.map_snapshot = int(module.Map.GetMapID() or 0)
    return widget


def _install_sell_rule_editor_click_stubs(module, clicked_button_label: str) -> None:
    imgui = module.PyImGui
    clicked_label = str(clicked_button_label or "")
    _visible_label, separator, hidden_id = clicked_label.partition("##")
    confirm_label = f"Are you sure?##{hidden_id}" if separator else "Are you sure?"
    imgui.button = lambda label: str(label or "") in (clicked_label, confirm_label)
    imgui.small_button = lambda *_args, **_kwargs: False
    imgui.same_line = lambda *_args, **_kwargs: None
    imgui.spacing = lambda *_args, **_kwargs: None
    imgui.text = lambda *_args, **_kwargs: None
    imgui.text_wrapped = lambda *_args, **_kwargs: None
    imgui.text_colored = lambda *_args, **_kwargs: None
    imgui.input_text = lambda _label, value: value
    imgui.collapsing_header = lambda *_args, **_kwargs: False
    imgui.begin_disabled = lambda *_args, **_kwargs: None
    imgui.end_disabled = lambda *_args, **_kwargs: None
    imgui.tree_pop = lambda *_args, **_kwargs: None


def _prepare_sell_rule_editor_widget(module, clicked_button_label: str):
    _install_sell_rule_editor_click_stubs(module, clicked_button_label)
    widget = _make_widget(module)
    if clicked_button_label:
        widget.pending_destructive_button_key = widget._get_destructive_button_key(clicked_button_label)
        widget.pending_destructive_button_expires_at_ms = int(module.time.time() * 1000) + module.DESTRUCTIVE_BUTTON_CONFIRM_TIMEOUT_MS
    widget.catalog_common_material_ids = [921, 925, 946]
    widget.catalog_rare_materials = [
        {"model_id": int(module.ECTOPLASM_MODEL_ID), "name": "Glob of Ectoplasm", "material_type": "rare"},
    ]
    widget.catalog_by_model_id.update(
        {
            921: {"model_id": 921, "name": "Bone", "material_type": "common"},
            925: {"model_id": 925, "name": "Bolt of Cloth", "material_type": "common"},
            946: {"model_id": 946, "name": "Wood Plank", "material_type": "common"},
            int(module.ECTOPLASM_MODEL_ID): {
                "model_id": int(module.ECTOPLASM_MODEL_ID),
                "name": "Glob of Ectoplasm",
                "material_type": "rare",
            },
        }
    )
    widget._draw_rule_header_row = lambda *args, **_kwargs: (True, bool(args[8]), False, "", False)
    widget._draw_section_heading = lambda *_args, **_kwargs: None
    widget._draw_secondary_text = lambda *_args, **_kwargs: None
    widget._draw_rule_name_input = lambda _label, value: value
    widget._draw_whitelist_targets = lambda **kwargs: (kwargs["targets"], 0)
    widget._draw_material_search_results = lambda *_args, **_kwargs: (0, [])
    widget._draw_search_results = lambda *_args, **_kwargs: (0, [])
    widget._draw_add_all_matches_button = lambda *_args, **_kwargs: False
    return widget


def _make_item(
    module,
    *,
    item_id: int,
    model_id: int,
    name: str,
    quantity: int = 1,
    rarity: str = "Gold",
    identified: bool = True,
    is_customized: bool = False,
    is_material: bool = False,
    is_rare_material: bool = False,
    is_weapon_like: bool = False,
    is_armor_piece: bool = False,
    item_type_id: int = 0,
    item_type_name: str = "",
    salvageable: bool = False,
    standalone_kind: str = "",
    requirement: int = 0,
    requirement_attribute_id: int = 0,
    requirement_attribute_name: str = "",
    damage_min: int = 0,
    damage_max: int = 0,
    energy: int = 0,
    armor: int = 0,
    rune_identifiers: list[str] | None = None,
    weapon_mod_identifiers: list[str] | None = None,
    weapon_mod_matches: list[object] | None = None,
):
    return module.InventoryItemInfo(
        item_id=item_id,
        model_id=model_id,
        name=name,
        quantity=quantity,
        value=100,
        item_type_id=item_type_id,
        item_type_name=item_type_name,
        rarity=rarity,
        identified=identified,
        salvageable=salvageable,
        is_customized=is_customized,
        is_inscribable=False,
        is_material=is_material,
        is_rare_material=is_rare_material,
        is_weapon_like=is_weapon_like,
        is_armor_piece=is_armor_piece,
        requirement=requirement,
        requirement_attribute_id=requirement_attribute_id,
        requirement_attribute_name=requirement_attribute_name,
        damage_min=damage_min,
        damage_max=damage_max,
        energy=energy,
        armor=armor,
        standalone_kind=standalone_kind,
        rune_identifiers=list(rune_identifiers or []),
        weapon_mod_identifiers=list(weapon_mod_identifiers or []),
        weapon_mod_matches=list(weapon_mod_matches or []),
    )


def _make_weapon_mod_match(
    module,
    identifier: str,
    value: int | None,
    *,
    target_item_type: str = "",
    component_kind: str = "",
    mod_type: str = "",
) -> object:
    return module.ParsedUpgradeMatch(
        identifier=identifier,
        target_item_type=target_item_type,
        component_kind=component_kind,
        mod_type=mod_type,
        value=value,
        min_value=0,
        max_value=0,
        is_maxed=False,
    )


def _fake_weapon_mod(identifier: str, mod_type: str, item_mods: dict[object, str], *, value_min: int = 0, value_max: int = 0) -> object:
    modifiers = []
    if value_max > value_min:
        modifiers.append(
            types.SimpleNamespace(
                modifier_value_arg=types.SimpleNamespace(name="Arg2"),
                min=value_min,
                max=value_max,
            )
        )
    return types.SimpleNamespace(
        identifier=identifier,
        name=identifier,
        mod_type=types.SimpleNamespace(name=mod_type),
        item_mods=dict(item_mods),
        modifiers=modifiers,
    )


def _install_weapon_mod_catalog_fixture(module):
    original_db = module.MOD_DB
    module.MOD_DB = types.SimpleNamespace(
        weapon_mods={
            "Cruel": _fake_weapon_mod(
                "Cruel",
                "Prefix",
                {
                    module.ItemType.Axe: "AxeHaft",
                    module.ItemType.Hammer: "HammerHaft",
                    module.ItemType.Sword: "SwordHilt",
                    module.ItemType.Daggers: "DaggerTang",
                },
            ),
            "Barbed": _fake_weapon_mod(
                "Barbed",
                "Prefix",
                {
                    module.ItemType.Axe: "AxeHaft",
                    module.ItemType.Daggers: "DaggerTang",
                },
            ),
            "of Defense": _fake_weapon_mod(
                "of Defense",
                "Suffix",
                {
                    module.ItemType.Axe: "AxeGrip",
                    module.ItemType.Daggers: "DaggerHandle",
                    module.ItemType.Staff: "StaffWrapping",
                },
                value_min=1,
                value_max=5,
            ),
        },
        runes={},
    )
    return original_db


def _rarity_flags(*enabled: str) -> dict[str, bool]:
    enabled_keys = {str(key or "").strip().lower() for key in enabled}
    return {
        "white": "white" in enabled_keys,
        "blue": "blue" in enabled_keys,
        "purple": "purple" in enabled_keys,
        "gold": "gold" in enabled_keys,
        "green": "green" in enabled_keys,
    }


def _salvage_settings(
    module,
    *,
    model_ids: list[int] | None = None,
    rarities: list[str] | None = None,
    categories: list[str] | None = None,
    on_inventory_change: bool = False,
    rules: list[object] | None = None,
):
    rarity_keys = {str(value or "").strip().lower() for value in (rarities or [])}
    category_keys = {str(value or "").strip().lower() for value in (categories or [])}
    return module.SalvageSettings(
        model_ids=list(model_ids or []),
        rarities={key: key in rarity_keys for key, _label in module.RARITY_OPTION_ORDER},
        categories={key: key in category_keys for key, _label in module.SALVAGE_CATEGORY_ORDER},
        on_inventory_change=on_inventory_change,
        rules=list(rules or []),
    )


def _identify_settings(
    module,
    *,
    rarities: list[str] | None = None,
    before_execute: bool = False,
    on_inventory_change: bool = False,
):
    rarity_keys = {str(value or "").strip().lower() for value in (rarities or [])}
    return module.IdentifySettings(
        rarities={key: key in rarity_keys for key, _label in module.RARITY_OPTION_ORDER},
        before_execute=before_execute,
        on_inventory_change=on_inventory_change,
    )


def _make_weapon_item(
    module,
    *,
    item_id: int,
    model_id: int,
    name: str,
    requirement: int,
    item_type=None,
    identified: bool = True,
    requirement_attribute_id: int = 1,
    requirement_attribute_name: str = "Axe Mastery",
    damage_min: int = 0,
    damage_max: int = 0,
    energy: int = 0,
    armor: int = 0,
):
    selected_item_type = item_type if item_type is not None else module.ItemType.Axe
    return _make_item(
        module,
        item_id=item_id,
        model_id=model_id,
        name=name,
        rarity="Gold",
        identified=identified,
        is_weapon_like=True,
        requirement=requirement,
        requirement_attribute_id=requirement_attribute_id,
        requirement_attribute_name=requirement_attribute_name,
        damage_min=damage_min,
        damage_max=damage_max,
        energy=energy,
        armor=armor,
        item_type_id=int(selected_item_type),
        item_type_name=str(getattr(selected_item_type, "name", "Axe")),
    )


def _drain_generator_return(generator):
    try:
        while True:
            next(generator)
    except StopIteration as stop:
        return stop.value


def _get_multibox_status(widget, account_email: str):
    return widget.multibox_statuses.get(str(account_email or "").strip().lower())


def _test_malformed_profile_is_preserved(module, temp_root: Path) -> None:
    widget = _make_widget(module)
    config_path = temp_root / "malformed_profile.json"
    original_text = '{"version": 8, "buy_rules": [invalid json'
    config_path.write_text(original_text, encoding="utf-8")
    widget.config_path = str(config_path)

    widget._load_profile()

    _expect(config_path.read_text(encoding="utf-8") == original_text, "Malformed profile should not be rewritten on load failure.")
    recovery_dir = Path(widget._get_profile_recovery_dir(str(config_path)))
    snapshots = sorted(recovery_dir.glob(config_path.name + ".load-failed-*.bak"))
    _expect(bool(snapshots), "Malformed profile load should create a timestamped backup snapshot.")
    _expect("preserving the original file" in widget.profile_warning.lower(), "Load warning should explain that the original profile was preserved.")
    _expect(widget.active_workspace == module.WORKSPACE_RULES, "Malformed profile load should open the Rules workspace for recovery.")


def _test_legacy_profile_normalizes_and_saves(module, temp_root: Path) -> None:
    widget = _make_widget(module)
    config_path = temp_root / "legacy_profile.json"
    payload = {
        "favorite_outpost_ids": [1, "2", 2, 999],
        "buy_rules": [
            {
                "enabled": True,
                "kind": module.LEGACY_BUY_KIND_ECTO,
                "model_id": int(module.ECTOPLASM_MODEL_ID),
                "target_count": 25,
                "max_per_run": 5,
                "material_targets": "bad nested type",
            }
        ],
        "sell_rules": [
            {
                "enabled": True,
                "kind": module.LEGACY_SELL_KIND_WEAPONS_BY_RARITY,
                "blacklist_model_ids": "bad nested type",
                "protected_weapon_mod_identifiers": "bad nested type",
                "protected_weapon_requirement_rules": "bad nested type",
                "all_weapons_max_requirement": 9,
                "rarities": {"gold": True, "purple": True},
            }
        ],
    }
    config_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    widget.config_path = str(config_path)

    widget._load_profile()

    _expect(len(widget.buy_rules) == 1, "Legacy profile should normalize into one active buy rule.")
    buy_rule = widget.buy_rules[0]
    _expect(buy_rule.kind == module.BUY_KIND_MATERIAL_TARGET, "Legacy ecto buy rule should migrate to material-target logic.")
    _expect(len(buy_rule.material_targets) == 1, "Legacy material-target migration should preserve the original target row.")
    _expect(buy_rule.material_targets[0].model_id == int(module.ECTOPLASM_MODEL_ID), "Material target should keep the ectoplasm model id.")
    _expect(widget.favorite_outpost_ids == [1, 2], "Favorite outposts should be normalized, deduped, and filtered to known ids.")

    sell_rule = widget.sell_rules[0]
    _expect(sell_rule.kind == module.SELL_KIND_WEAPONS, "Legacy weapon sell rule should migrate to the modern weapon rule kind.")
    _expect(sell_rule.blacklist_model_ids == [], "Bad nested blacklist data should normalize to an empty list.")
    _expect(sell_rule.protected_weapon_mod_identifiers == [], "Bad protected-mod data should normalize to an empty list.")
    _expect(sell_rule.protected_weapon_mod_thresholds == [], "Missing protected-mod threshold data should normalize to an empty list.")
    _expect(sell_rule.protected_weapon_requirement_rules == [], "Bad requirement-rule data should normalize to an empty list.")
    _expect(sell_rule.all_weapons_min_requirement == 1, "Legacy max-only requirement thresholds should migrate to a low endpoint of 1.")
    _expect(sell_rule.all_weapons_max_requirement == 9, "Valid requirement threshold should survive legacy normalization.")

    saved_payload = json.loads(config_path.read_text(encoding="utf-8"))
    _expect(saved_payload["version"] == module.PROFILE_VERSION, "Normalized legacy profiles should be rewritten to the current version.")
    _expect(isinstance(saved_payload["buy_rules"][0]["material_targets"], list), "Normalized material targets should be saved as a list.")
    _expect(bool(widget.profile_notice), "Legacy normalization should surface a profile notice.")


def _test_legacy_whitelist_keep_count_migrates_to_per_target_rows(module, temp_root: Path) -> None:
    widget = _make_widget(module)
    config_path = temp_root / "legacy_whitelist_keep_profile.json"
    payload = {
        "version": module.PROFILE_VERSION - 1,
        "sell_rules": [
            {
                "enabled": True,
                "kind": module.SELL_KIND_COMMON_MATERIALS,
                "model_ids": [921, 925],
                "keep_count": 25,
            }
        ],
        "destroy_rules": [
            {
                "enabled": True,
                "kind": module.DESTROY_KIND_EXPLICIT_MODELS,
                "model_ids": [111, 555],
                "keep_count": 1,
            }
        ],
    }
    config_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    widget.config_path = str(config_path)

    widget._load_profile()

    sell_targets = [(target.model_id, target.keep_count) for target in widget.sell_rules[0].whitelist_targets]
    destroy_targets = [(target.model_id, target.keep_count) for target in widget.destroy_rules[0].whitelist_targets]
    _expect(
        sell_targets == [(921, 25), (925, 25)],
        "Legacy pooled sell keep_count values should migrate into one keep row per selected material model.",
    )
    _expect(
        destroy_targets == [(111, 1), (555, 1)],
        "Legacy pooled destroy keep_count values should migrate into one keep row per selected explicit model.",
    )
    _expect(widget.sell_rules[0].keep_count == 0 and widget.destroy_rules[0].keep_count == 0, "Migrated whitelist rules should stop using the pooled keep_count field in memory.")

    saved_payload = json.loads(config_path.read_text(encoding="utf-8"))
    _expect(
        saved_payload["sell_rules"][0]["whitelist_targets"] == [
            {"model_id": 921, "keep_count": 25, "deposit_to_storage": False},
            {"model_id": 925, "keep_count": 25, "deposit_to_storage": False},
        ],
        "Normalized profiles should persist sell whitelist keep rows explicitly.",
    )
    _expect(
        saved_payload["destroy_rules"][0]["whitelist_targets"] == [
            {"model_id": 111, "keep_count": 1, "deposit_to_storage": False},
            {"model_id": 555, "keep_count": 1, "deposit_to_storage": False},
        ],
        "Normalized profiles should persist destroy whitelist keep rows explicitly.",
    )
    _expect(
        not saved_payload["sell_rules"][0].get("deposit_protected_matches", False),
        "Legacy sell rules should default the new deposit-protected flag off when normalized.",
    )


def _test_sell_material_presets_survive_same_frame_table_writeback(module) -> None:
    widget = _prepare_sell_rule_editor_widget(module, "Add All Common Materials##sell_common_preset_0")
    widget.sell_rules = [
        module._normalize_sell_rule(
            module.SellRule(
                enabled=False,
                kind=module.SELL_KIND_COMMON_MATERIALS,
                whitelist_targets=[module.WhitelistTarget(model_id=946, keep_count=0)],
            )
        )
    ]

    changed = widget._draw_sell_rule_editor(0, widget.sell_rules[0])

    _expect(changed, "Sell material preset button should report a changed rule.")
    _expect(
        widget.sell_rules[0].model_ids == [946, 921, 925],
        "Sell material preset clicks should not be undone by the selected-materials table in the same draw pass.",
    )
    _expect(
        [target.model_id for target in widget.sell_rules[0].whitelist_targets] == [946, 921, 925],
        "Sell material preset clicks should persist the expanded whitelist target rows.",
    )


def _test_sell_clear_list_survives_same_frame_table_writeback(module) -> None:
    widget = _prepare_sell_rule_editor_widget(module, "Clear List##sell_clear_0")
    widget.sell_rules = [
        module._normalize_sell_rule(
            module.SellRule(
                enabled=False,
                kind=module.SELL_KIND_EXPLICIT_MODELS,
                whitelist_targets=[
                    module.WhitelistTarget(model_id=111, keep_count=1),
                    module.WhitelistTarget(model_id=555, keep_count=0),
                ],
            )
        )
    ]

    changed = widget._draw_sell_rule_editor(0, widget.sell_rules[0])

    _expect(changed, "Sell Clear List should report a changed rule.")
    _expect(widget.sell_rules[0].model_ids == [], "Sell Clear List should clear model IDs.")
    _expect(widget.sell_rules[0].whitelist_targets == [], "Sell Clear List should clear whitelist target rows.")


def _test_legacy_nonsalvageable_gold_sell_rule_is_removed_safely(module, temp_root: Path) -> None:
    widget = _make_widget(module)
    config_path = temp_root / "legacy_gold_rule_profile.json"
    payload = {
        "version": module.PROFILE_VERSION - 1,
        "sell_rules": [
            {
                "enabled": True,
                "kind": module.LEGACY_SELL_KIND_NONSALVAGEABLE_GOLDS,
                "keep_count": 2,
            },
            {
                "enabled": True,
                "kind": module.SELL_KIND_EXPLICIT_MODELS,
                "model_ids": [1234],
                "keep_count": 1,
            },
        ],
    }
    config_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    widget.config_path = str(config_path)

    widget._load_profile()

    _expect(
        len(widget.sell_rules) == 1,
        "Legacy non-salvageable gold sell rules should be removed during profile normalization.",
    )
    _expect(
        widget.sell_rules[0].kind == module.SELL_KIND_EXPLICIT_MODELS,
        "Supported sell rules should remain after legacy gold-rule removal.",
    )
    _expect(
        module.LEGACY_SELL_KIND_NONSALVAGEABLE_GOLDS not in module.SELL_RULE_KINDS,
        "The retired gold sell rule kind should not remain in the active sell rule kinds.",
    )
    _expect(
        module.LEGACY_SELL_KIND_NONSALVAGEABLE_GOLDS not in module.SELL_RULE_WORKSPACE_ORDER,
        "The retired gold sell rule kind should not remain in the sell workspace order.",
    )
    _expect(
        "Golds" not in module.SELL_RULE_WORKSPACE_LABELS.values(),
        "The sell workspace should no longer expose a Golds tab label.",
    )

    saved_payload = json.loads(config_path.read_text(encoding="utf-8"))
    _expect(
        all(entry.get("kind") != module.LEGACY_SELL_KIND_NONSALVAGEABLE_GOLDS for entry in saved_payload["sell_rules"]),
        "Normalized profiles should not write the retired gold sell rule back to disk.",
    )


def _test_salvage_profile_defaults_are_off(module, temp_root: Path) -> None:
    widget = _make_widget(module)
    config_path = temp_root / "salvage_defaults_profile.json"
    config_path.write_text(json.dumps({"version": module.PROFILE_VERSION - 1}, indent=2), encoding="utf-8")
    widget.config_path = str(config_path)

    widget._load_profile()

    _expect(not widget.salvage_settings.model_ids, "Legacy profiles should load with no explicit salvage models.")
    _expect(not any(widget.salvage_settings.rarities.values()), "All salvage rarity selectors should default off.")
    _expect(not any(widget.salvage_settings.categories.values()), "All salvage category selectors should default off.")
    _expect(not widget.salvage_settings.on_inventory_change, "On-pickup/inventory-change salvage should default off.")
    _expect(not any(widget.identify_settings.rarities.values()), "All identify rarity selectors should default off.")
    _expect(not widget.identify_settings.before_execute, "Identify before Execute should default off.")
    _expect(not widget.identify_settings.on_inventory_change, "On-pickup/inventory-change identify should default off.")
    saved_payload = json.loads(config_path.read_text(encoding="utf-8"))
    _expect("salvage_settings" in saved_payload, "Normalized profiles should persist the salvage settings object.")
    _expect("identify_settings" in saved_payload, "Normalized profiles should persist the identify settings object.")
    _expect(not any(saved_payload["salvage_settings"]["rarities"].values()), "Saved salvage rarity selectors should remain off by default.")
    _expect(not any(saved_payload["identify_settings"]["rarities"].values()), "Saved identify rarity selectors should remain off by default.")
    _expect(not saved_payload["identify_settings"]["before_execute"], "Saved Identify before Execute should remain off by default.")
    _expect(not saved_payload["identify_settings"]["on_inventory_change"], "Saved on-pickup/inventory-change identify should remain off by default.")


def _test_manual_vendor_profile_defaults_and_roundtrip(module, temp_root: Path) -> None:
    setting_names = [
        "auto_sell_on_manual_vendor_interaction",
        "auto_buy_on_manual_vendor_interaction",
        "auto_sell_to_any_merchant",
        "auto_sell_any_merchant_normal_items",
        "auto_sell_any_merchant_materials",
        "auto_sell_any_merchant_runes",
    ]

    widget = _make_widget(module)
    normalized = widget._normalize_profile_payload({"version": module.PROFILE_VERSION - 1})
    for setting_name in setting_names:
        _expect(not normalized[setting_name], f"{setting_name} should default off for legacy profiles.")
        _expect(not getattr(widget, setting_name), f"{setting_name} should default off on new widgets.")

    config_path = temp_root / "manual_vendor_settings_profile.json"
    widget.config_path = str(config_path)
    for setting_name in setting_names:
        setattr(widget, setting_name, True)

    _expect(widget._save_profile(), "Manual vendor settings profile should save.")
    saved_payload = json.loads(config_path.read_text(encoding="utf-8"))
    for setting_name in setting_names:
        _expect(saved_payload[setting_name] is True, f"{setting_name} should save as enabled.")

    reloaded_widget = _make_widget(module)
    reloaded_widget.config_path = str(config_path)
    reloaded_widget._load_profile()
    for setting_name in setting_names:
        _expect(getattr(reloaded_widget, setting_name) is True, f"{setting_name} should reload as enabled.")


def _test_manual_vendor_runtime_queues_once_per_signature(module) -> None:
    widget = _make_widget(module)
    widget.auto_sell_on_manual_vendor_interaction = True
    widget._is_merchant_window_open = lambda: True

    queued_coroutines: list[object] = []
    original_coroutines = getattr(module.GLOBAL_CACHE, "Coroutines", None)
    had_coroutines = hasattr(module.GLOBAL_CACHE, "Coroutines")
    try:
        module.GLOBAL_CACHE.Coroutines = queued_coroutines
        context_a = module.ManualVendorContext(
            signature="vendor-a",
            merchant_types={module.MERCHANT_TYPE_MERCHANT},
        )
        context_b = module.ManualVendorContext(
            signature="vendor-b",
            merchant_types={module.MERCHANT_TYPE_MERCHANT},
        )

        widget._get_current_manual_vendor_context = lambda: context_a
        widget._update_manual_vendor_runtime()
        _expect(len(queued_coroutines) == 1, "Manual vendor runtime should queue once for a new vendor signature.")
        _expect(widget.manual_vendor_running, "Manual vendor runtime should mark itself running before queueing.")

        widget.manual_vendor_running = False
        widget._update_manual_vendor_runtime()
        _expect(len(queued_coroutines) == 1, "Manual vendor runtime should not queue twice for the same vendor signature.")

        widget._get_current_manual_vendor_context = lambda: context_b
        widget._update_manual_vendor_runtime()
        _expect(len(queued_coroutines) == 2, "Manual vendor runtime should re-arm when the vendor signature changes.")

        widget.manual_vendor_running = False
        widget._is_merchant_window_open = lambda: False
        widget._update_manual_vendor_runtime()
        _expect(widget.manual_vendor_handled_signature == "", "Manual vendor runtime should re-arm after the merchant window closes.")
    finally:
        if had_coroutines:
            module.GLOBAL_CACHE.Coroutines = original_coroutines
        elif hasattr(module.GLOBAL_CACHE, "Coroutines"):
            delattr(module.GLOBAL_CACHE, "Coroutines")


def _test_manual_vendor_matching_sell_uses_current_merchant_only(module) -> None:
    widget = _make_widget(module)
    widget.auto_sell_on_manual_vendor_interaction = True
    widget.preview_ready = True
    context = module.ManualVendorContext(
        signature="normal-merchant",
        merchant_types={module.MERCHANT_TYPE_MERCHANT},
    )
    plan = module.PlanResult(
        supported_map=True,
        merchant_sell_item_ids=[10, 20],
        material_sales=[
            module.PlannedMaterialSale(
                merchant_type=module.MERCHANT_TYPE_MATERIALS,
                item_id=20,
                model_id=946,
                label="Wood Plank",
                batches_to_sell=1,
                quantity_to_sell=10,
            )
        ],
        rune_trader_sales=[
            module.PlannedTraderSale(item_id=30, model_id=5551, label="Superior Vigor"),
        ],
        has_actions=True,
    )
    captured_sales: list[tuple[int, int]] = []

    def _capture_open_merchant_sales(manual_sales, *, phase_label="Merchant sells"):
        captured_sales.extend((int(sale.item_id), int(sale.quantity_to_sell)) for sale in manual_sales)
        if False:
            yield None
        return module.ExecutionPhaseOutcome(
            label=phase_label,
            measure_label="items",
            attempted=len(manual_sales),
            completed=len(manual_sales),
        )

    widget._is_merchant_window_open = lambda: True
    widget._get_current_manual_vendor_context = lambda: context
    widget._build_plan = lambda **_kwargs: plan
    widget._execute_open_merchant_sell_phase = _capture_open_merchant_sales
    widget._get_manual_merchant_sale_for_item_id = (
        lambda item_id, quantity_to_sell=0, *, model_id=0, label="": module.PlannedManualMerchantSale(
            item_id=int(item_id),
            model_id=int(model_id or 111),
            label=label or f"Item {item_id}",
            quantity_to_sell=max(1, int(quantity_to_sell or 1)),
        )
    )

    _drain_generator_return(widget._run_manual_vendor_pass(context))

    _expect(captured_sales == [(10, 1)], "Matching auto-sell at a normal merchant should not include trader-targeted sales.")
    _expect(not widget.preview_ready, "Successful manual vendor sales should mark Preview dirty.")


def _test_manual_vendor_any_merchant_material_fallback(module) -> None:
    widget = _make_widget(module)
    widget.auto_sell_to_any_merchant = True
    widget.auto_sell_any_merchant_materials = True
    context = module.ManualVendorContext(
        signature="normal-merchant",
        merchant_types={module.MERCHANT_TYPE_MERCHANT},
    )
    plan = module.PlanResult(
        supported_map=True,
        merchant_sell_item_ids=[20],
        material_sales=[
            module.PlannedMaterialSale(
                merchant_type=module.MERCHANT_TYPE_MATERIALS,
                item_id=20,
                model_id=946,
                label="Wood Plank",
                batches_to_sell=1,
                quantity_to_sell=10,
            )
        ],
        rune_trader_sales=[
            module.PlannedTraderSale(item_id=30, model_id=5551, label="Superior Vigor"),
        ],
        has_actions=True,
    )
    captured_sales: list[tuple[int, int]] = []

    def _capture_open_merchant_sales(manual_sales, *, phase_label="Merchant sells"):
        captured_sales.extend((int(sale.item_id), int(sale.quantity_to_sell)) for sale in manual_sales)
        if False:
            yield None
        return module.ExecutionPhaseOutcome(
            label=phase_label,
            measure_label="items",
            attempted=len(manual_sales),
            completed=len(manual_sales),
        )

    widget._is_merchant_window_open = lambda: True
    widget._get_current_manual_vendor_context = lambda: context
    widget._build_plan = lambda **_kwargs: plan
    widget._execute_open_merchant_sell_phase = _capture_open_merchant_sales
    widget._get_manual_material_fallback_merchant_sell_item_ids = lambda _plan: {20}
    widget._get_manual_merchant_sale_for_item_id = (
        lambda item_id, quantity_to_sell=0, *, model_id=0, label="": module.PlannedManualMerchantSale(
            item_id=int(item_id),
            model_id=int(model_id or 111),
            label=label or f"Item {item_id}",
            quantity_to_sell=int(quantity_to_sell),
        )
    )

    _drain_generator_return(widget._run_manual_vendor_pass(context))

    _expect(captured_sales == [(20, 0)], "Any-merchant material fallback should allow the full configured material stack.")


def _test_manual_vendor_auto_buy_uses_current_offers(module) -> None:
    widget = _make_widget(module)
    widget.auto_buy_on_manual_vendor_interaction = True
    widget.preview_ready = True
    context = module.ManualVendorContext(
        signature="normal-merchant",
        merchant_types={module.MERCHANT_TYPE_MERCHANT},
        merchant_item_ids=[501],
    )
    plan = module.PlanResult(
        supported_map=True,
        merchant_stock_buys=[
            module.PlannedMerchantBuy(model_id=555, quantity=2, label="Identification Kit"),
        ],
        has_actions=True,
    )
    captured_buys: list[tuple[int, int, list[int]]] = []

    def _capture_buy(model_id, quantity, *, offered_items=None):
        captured_buys.append((int(model_id), int(quantity), list(offered_items or [])))
        if False:
            yield None
        return True

    widget._is_merchant_window_open = lambda: True
    widget._get_current_manual_vendor_context = lambda: context
    widget._build_plan = lambda **_kwargs: plan
    widget._buy_merchant_model = _capture_buy

    _drain_generator_return(widget._run_manual_vendor_pass(context))

    _expect(captured_buys == [(555, 2, [501])], "Manual auto-buy should use only the currently opened merchant's offers.")
    _expect(not widget.preview_ready, "Successful manual vendor buys should mark Preview dirty.")


def _test_exact_rune_sell_rule_profile_roundtrip(module, temp_root: Path) -> None:
    widget = _make_widget(module)
    config_path = temp_root / "exact_rune_sell_profile.json"
    payload = {
        "version": module.PROFILE_VERSION - 1,
        "sell_rules": [
            {
                "enabled": True,
                "kind": module.SELL_KIND_RUNE_TRADER_TARGET,
                "rune_sell_targets": [
                    {"identifier": "rune_attunement", "keep_count": 1},
                ],
            },
        ],
    }
    config_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    widget.config_path = str(config_path)

    widget._load_profile()

    _expect(
        module.SELL_KIND_RUNE_TRADER_TARGET in module.SELL_RULE_KINDS,
        "Exact rune sell rules should be a supported sell rule kind.",
    )
    _expect(
        module.SELL_KIND_RUNE_TRADER_TARGET in module.SELL_RULE_WORKSPACE_ORDER,
        "Exact rune sell rules should be available from the Sell workspace.",
    )
    _expect(len(widget.sell_rules) == 1, "Exact rune sell profiles should load one rule.")
    rule = widget.sell_rules[0]
    _expect(rule.kind == module.SELL_KIND_RUNE_TRADER_TARGET, "Exact rune sell rule kind should round-trip.")
    _expect(rule.merchant_type == module.MERCHANT_TYPE_RUNE_TRADER, "Exact rune sell rules should route to the Rune Trader.")
    _expect(len(rule.rune_sell_targets) == 1, "Exact rune sell target list should load.")
    _expect(rule.rune_sell_targets[0].identifier == "rune_attunement", "Exact rune sell target identifier should round-trip.")
    _expect(rule.rune_sell_targets[0].keep_count == 1, "Exact rune sell target keep count should round-trip.")

    saved_payload = json.loads(config_path.read_text(encoding="utf-8"))
    saved_rule = saved_payload["sell_rules"][0]
    _expect(
        saved_rule["rune_sell_targets"] == [{"identifier": "rune_attunement", "keep_count": 1}],
        "Exact rune sell targets should save with plain keep-count rows.",
    )


def _test_exact_rune_sell_rule_plans_matching_standalone_runes(module) -> None:
    widget = _make_widget(module)
    widget.rune_names = {
        "rune_attunement": "Rune of Attunement",
        "rune_vigor": "Rune of Vigor",
    }
    widget.sell_rules = [
        module._normalize_sell_rule(
            module.SellRule(
                enabled=True,
                kind=module.SELL_KIND_RUNE_TRADER_TARGET,
                rune_sell_targets=[
                    module.RuneSellTarget(identifier="rune_attunement", keep_count=1),
                ],
            )
        )
    ]
    widget._get_supported_context = lambda: (
        True,
        "Ready",
        {
            module.MERCHANT_TYPE_RUNE_TRADER: (0.0, 0.0),
            module.MERCHANT_TYPE_MERCHANT: (0.0, 0.0),
        },
    )
    widget._collect_inventory_items = lambda: [
        _make_item(
            module,
            item_id=101,
            model_id=9001,
            name="Rune of Attunement",
            rarity="Blue",
            standalone_kind=module.RUNE_STANDALONE_KIND,
            rune_identifiers=["rune_attunement"],
        ),
        _make_item(
            module,
            item_id=102,
            model_id=9001,
            name="Rune of Attunement",
            rarity="Blue",
            standalone_kind=module.RUNE_STANDALONE_KIND,
            rune_identifiers=["rune_attunement"],
        ),
        _make_item(
            module,
            item_id=103,
            model_id=9002,
            name="Rune of Vigor",
            rarity="Blue",
            standalone_kind=module.RUNE_STANDALONE_KIND,
            rune_identifiers=["rune_vigor"],
        ),
    ]

    plan = widget._build_plan()

    sold_ids = {sale.item_id for sale in plan.rune_trader_sales}
    _expect(len(sold_ids) == 1, "Exact rune sell rules should sell only excess matching standalone runes.")
    _expect(sold_ids <= {101, 102}, "Exact rune sell rules should not sell non-target rune names.")
    _expect(103 not in sold_ids, "Exact rune sell rules should leave other standalone rune names alone.")
    _expect(
        any("reserved to satisfy keep count 1" in entry.reason for entry in plan.entries),
        "Exact rune sell rules should show when a matching rune is kept.",
    )


def _test_exact_rune_sell_rule_reserves_names_from_broad_armor_rule(module) -> None:
    widget = _make_widget(module)
    widget.sell_rules = [
        module._normalize_sell_rule(
            module.SellRule(
                enabled=True,
                kind=module.SELL_KIND_ARMOR,
                rarities=_rarity_flags("blue"),
                include_standalone_runes=True,
            )
        ),
        module._normalize_sell_rule(
            module.SellRule(
                enabled=True,
                kind=module.SELL_KIND_RUNE_TRADER_TARGET,
                rune_sell_targets=[
                    module.RuneSellTarget(identifier="rune_attunement", keep_count=1),
                ],
            )
        ),
    ]
    widget._get_supported_context = lambda: (
        True,
        "Ready",
        {
            module.MERCHANT_TYPE_RUNE_TRADER: (0.0, 0.0),
            module.MERCHANT_TYPE_MERCHANT: (0.0, 0.0),
        },
    )
    widget._collect_inventory_items = lambda: [
        _make_item(
            module,
            item_id=101,
            model_id=9001,
            name="Rune of Attunement",
            rarity="Blue",
            standalone_kind=module.RUNE_STANDALONE_KIND,
            rune_identifiers=["rune_attunement"],
        ),
        _make_item(
            module,
            item_id=102,
            model_id=9001,
            name="Rune of Attunement",
            rarity="Blue",
            standalone_kind=module.RUNE_STANDALONE_KIND,
            rune_identifiers=["rune_attunement"],
        ),
        _make_item(
            module,
            item_id=103,
            model_id=9002,
            name="Rune of Vigor",
            rarity="Blue",
            standalone_kind=module.RUNE_STANDALONE_KIND,
            rune_identifiers=["rune_vigor"],
        ),
    ]

    plan = widget._build_plan()

    sold_ids = {sale.item_id for sale in plan.rune_trader_sales}
    _expect(103 in sold_ids, "Broad armor loose-rune rules should still sell non-reserved rune names.")
    _expect(len(sold_ids & {101, 102}) == 1, "Exact rune sell rules should control reserved rune names before broad armor rules.")
    _expect(
        any("reserved to satisfy keep count 1" in entry.reason for entry in plan.entries),
        "Exact rune keep counts should still apply when a broad armor loose-rune rule exists first.",
    )


def _test_manual_vendor_exact_rune_sell_runs_at_rune_trader(module) -> None:
    widget = _make_widget(module)
    widget.auto_sell_on_manual_vendor_interaction = True
    widget.preview_ready = True
    context = module.ManualVendorContext(
        signature="rune-trader",
        merchant_types={module.MERCHANT_TYPE_RUNE_TRADER},
    )
    plan = module.PlanResult(
        supported_map=True,
        rune_trader_sales=[
            module.PlannedTraderSale(item_id=101, model_id=9001, label="Rune of Attunement"),
        ],
        has_actions=True,
    )
    captured_sales: list[int] = []

    def _capture_rune_sales(_coords, trader_sales, *, phase_label="Rune trader sales", trader_items=None):
        captured_sales.extend(int(sale.item_id) for sale in trader_sales)
        if False:
            yield None
        return module.ExecutionPhaseOutcome(
            label=phase_label,
            measure_label="items",
            attempted=len(trader_sales),
            completed=len(trader_sales),
        )

    widget._is_merchant_window_open = lambda: True
    widget._get_current_manual_vendor_context = lambda: context
    widget._build_plan = lambda **_kwargs: plan
    widget._sell_planned_trader_items = _capture_rune_sales

    _drain_generator_return(widget._run_manual_vendor_pass(context))

    _expect(captured_sales == [101], "Manual auto-sell should run exact rune trader sales at a Rune Trader.")
    _expect(not widget.preview_ready, "Successful manual rune sales should mark Preview dirty.")


def _test_salvage_candidate_evaluation_precedence(module) -> None:
    widget = _make_widget(module)
    widget.salvage_settings = _salvage_settings(module, model_ids=[100])
    enabled_sell_rules = []
    selected_item = _make_item(
        module,
        item_id=1,
        model_id=100,
        name="Selected Gold",
        rarity="Gold",
        identified=True,
        salvageable=True,
    )

    protected_rule = module._normalize_sell_rule(
        module.SellRule(
            enabled=True,
            kind=module.SELL_KIND_WEAPONS,
            rarities=_rarity_flags("gold"),
            blacklist_model_ids=[100],
        )
    )
    protected_item = _make_item(
        module,
        item_id=2,
        model_id=100,
        name="Protected Gold",
        rarity="Gold",
        identified=True,
        salvageable=True,
        is_weapon_like=True,
    )
    protected_reason = widget._get_salvage_candidate_block_reason(
        protected_item,
        [(0, protected_rule)],
        require_salvage_kit=True,
        salvage_kit_id=1,
    )
    _expect(protected_reason.startswith("protected:"), "Protection should be the first salvage block reason.")

    unsalvageable_reason = widget._get_salvage_candidate_block_reason(
        replace(selected_item, salvageable=False),
        enabled_sell_rules,
        require_salvage_kit=True,
        salvage_kit_id=1,
    )
    _expect(unsalvageable_reason.startswith("unsalvageable:"), "Runtime IsSalvageable should block salvage.")

    customized_reason = widget._get_salvage_candidate_block_reason(
        replace(selected_item, is_customized=True),
        enabled_sell_rules,
        require_salvage_kit=True,
        salvage_kit_id=1,
    )
    _expect(customized_reason.startswith("customized:"), "Customized items should block salvage.")

    unidentified_reason = widget._get_salvage_candidate_block_reason(
        replace(selected_item, identified=False),
        enabled_sell_rules,
        require_salvage_kit=True,
        salvage_kit_id=1,
    )
    _expect(unidentified_reason.startswith("unidentified non-white:"), "Unidentified non-white items should block salvage.")

    not_selected_reason = widget._get_salvage_candidate_block_reason(
        replace(selected_item, model_id=101),
        enabled_sell_rules,
        require_salvage_kit=True,
        salvage_kit_id=1,
    )
    _expect(not_selected_reason == "not selected by salvage settings", "Unselected items should not be salvage candidates.")

    no_kit_reason = widget._get_salvage_candidate_block_reason(
        selected_item,
        enabled_sell_rules,
        require_salvage_kit=True,
        salvage_kit_id=0,
    )
    _expect(no_kit_reason == "no normal salvage kit", "Missing normal salvage kits should block salvage.")

    ok_reason = widget._get_salvage_candidate_block_reason(
        selected_item,
        enabled_sell_rules,
        require_salvage_kit=True,
        salvage_kit_id=1,
    )
    _expect(ok_reason == "", "Selected safe items with a normal kit should be salvage candidates.")


def _test_salvage_broad_rarity_selection(module) -> None:
    widget = _make_widget(module)
    widget.salvage_settings = _salvage_settings(module, rarities=["gold"])
    gold_item = _make_item(module, item_id=10, model_id=1000, name="Gold Drop", rarity="Gold", identified=True, salvageable=True)
    purple_item = _make_item(module, item_id=11, model_id=1001, name="Purple Drop", rarity="Purple", identified=True, salvageable=True)

    _expect(
        widget._get_salvage_candidate_block_reason(gold_item, [], require_salvage_kit=True, salvage_kit_id=1) == "",
        "Enabled rarity selectors should select matching salvageable items.",
    )
    _expect(
        widget._get_salvage_candidate_block_reason(purple_item, [], require_salvage_kit=True, salvage_kit_id=1)
        == "not selected by salvage settings",
        "Disabled rarity selectors should not select other rarities.",
    )


def _test_salvage_category_selection(module) -> None:
    widget = _make_widget(module)
    widget.salvage_settings = _salvage_settings(module, categories=[module.SALVAGE_CATEGORY_WEAPONS])
    weapon_item = _make_item(
        module,
        item_id=20,
        model_id=2000,
        name="Weapon Drop",
        rarity="Blue",
        identified=True,
        salvageable=True,
        is_weapon_like=True,
    )
    armor_item = _make_item(
        module,
        item_id=21,
        model_id=2001,
        name="Armor Drop",
        rarity="Blue",
        identified=True,
        salvageable=True,
        is_armor_piece=True,
    )

    _expect(
        widget._get_salvage_candidate_block_reason(weapon_item, [], require_salvage_kit=True, salvage_kit_id=1) == "",
        "Enabled category selectors should select matching salvageable items.",
    )
    _expect(
        widget._get_salvage_candidate_block_reason(armor_item, [], require_salvage_kit=True, salvage_kit_id=1)
        == "not selected by salvage settings",
        "Disabled category selectors should not select other categories.",
    )


def _test_salvage_rarity_and_category_filters_combine(module) -> None:
    widget = _make_widget(
        module,
    )
    widget.salvage_settings = _salvage_settings(
        module,
        rarities=["gold"],
        categories=[module.SALVAGE_CATEGORY_WEAPONS, module.SALVAGE_CATEGORY_ARMOR],
    )
    gold_weapon = _make_item(
        module,
        item_id=22,
        model_id=2002,
        name="Gold Weapon",
        rarity="Gold",
        identified=True,
        salvageable=True,
        is_weapon_like=True,
    )
    gold_armor = _make_item(
        module,
        item_id=23,
        model_id=2003,
        name="Gold Armor",
        rarity="Gold",
        identified=True,
        salvageable=True,
        is_armor_piece=True,
    )
    white_weapon = _make_item(
        module,
        item_id=24,
        model_id=2004,
        name="White Weapon",
        rarity="White",
        identified=True,
        salvageable=True,
        is_weapon_like=True,
    )
    blue_weapon = _make_item(
        module,
        item_id=25,
        model_id=2005,
        name="Blue Weapon",
        rarity="Blue",
        identified=True,
        salvageable=True,
        is_weapon_like=True,
    )
    gold_material = _make_item(
        module,
        item_id=26,
        model_id=2006,
        name="Gold Material",
        rarity="Gold",
        identified=True,
        salvageable=True,
        is_material=True,
    )

    _expect(
        widget._get_salvage_candidate_block_reason(gold_weapon, [], require_salvage_kit=True, salvage_kit_id=1) == "",
        "Gold weapons should match combined rarity/category salvage filters.",
    )
    _expect(
        widget._get_salvage_candidate_block_reason(gold_armor, [], require_salvage_kit=True, salvage_kit_id=1) == "",
        "Gold armor should match combined rarity/category salvage filters.",
    )
    _expect(
        widget._get_salvage_candidate_block_reason(white_weapon, [], require_salvage_kit=True, salvage_kit_id=1)
        == "not selected by salvage settings",
        "White weapons should not match Gold + Weapons salvage filters.",
    )
    _expect(
        widget._get_salvage_candidate_block_reason(blue_weapon, [], require_salvage_kit=True, salvage_kit_id=1)
        == "not selected by salvage settings",
        "Blue weapons should not match Gold + Weapons salvage filters.",
    )
    _expect(
        widget._get_salvage_candidate_block_reason(gold_material, [], require_salvage_kit=True, salvage_kit_id=1)
        == "not selected by salvage settings",
        "Gold non-selected categories should not match Gold + Weapons/Armor salvage filters.",
    )


def _test_salvage_filter_summary_describes_combined_filters(module) -> None:
    widget = _make_widget(module)
    widget.salvage_settings = _salvage_settings(
        module,
        rarities=["gold"],
        categories=[module.SALVAGE_CATEGORY_WEAPONS, module.SALVAGE_CATEGORY_ARMOR],
    )

    summary = widget._format_salvage_filter_summary(widget.salvage_settings)
    _expect(
        "1 active rule(s)" in summary and "Default (legacy behavior)" in summary,
        "Salvage filter summary should show the active rule count and salvage option label.",
    )


def _test_salvage_selected_items_block_destroy(module) -> None:
    widget = _make_widget(module)
    widget.salvage_settings = _salvage_settings(module, rarities=["gold"])
    widget.destroy_rules = [
        module._normalize_destroy_rule(
            module.DestroyRule(
                enabled=True,
                kind=module.DESTROY_KIND_WEAPONS,
                rarities=_rarity_flags("gold"),
            )
        )
    ]
    widget._collect_inventory_items = lambda: [
        _make_item(
            module,
            item_id=30,
            model_id=3000,
            name="Gold Weapon",
            rarity="Gold",
            identified=True,
            salvageable=True,
            is_weapon_like=True,
        )
    ]

    plan = widget._build_plan()

    _expect(not plan.destroy_actions, "Salvage-selected eligible items should not be planned for destroy.")
    _expect(
        any("salvage wins over destroy" in entry.reason for entry in plan.entries if entry.action_type == "destroy"),
        "Destroy planning should explain when MR Salvage claims a matching item first.",
    )


def _make_specific_suffix_salvage_rule(module, salvage_option: str):
    return module._normalize_salvage_rule(
        module.SalvageRule(
            enabled=True,
            salvage_option=salvage_option,
            target_weapon_mod_variant_thresholds=[
                module.WeaponModVariantThresholdRule(
                    identifier="of Defense",
                    target_item_type="Daggers",
                    component_kind="DaggerHandle",
                    min_value=5,
                )
            ],
        )
    )


def _make_specific_suffix_item(module, *, item_id: int = 40):
    return _make_item(
        module,
        item_id=item_id,
        model_id=4000 + item_id,
        name="Dagger Handle of Defense",
        rarity="Gold",
        identified=True,
        salvageable=True,
        is_weapon_like=True,
        item_type_id=int(module.ItemType.Daggers),
        item_type_name="Daggers",
        weapon_mod_identifiers=["of Defense"],
        weapon_mod_matches=[
            _make_weapon_mod_match(
                module,
                "of Defense",
                5,
                target_item_type="Daggers",
                component_kind="DaggerHandle",
                mod_type="Suffix",
            )
        ],
    )


class _FakeExactUpgradeSalvageBridge:
    def __init__(
        self,
        module,
        *,
        available: bool = True,
        result=None,
        unavailable_reason: str = "fake backend unavailable",
    ):
        self.module = module
        self.available = bool(available)
        self.result = (
            result
            if result is not None
            else module._ExactUpgradeSalvageBridgeResult(True, "processed", "")
        )
        self.unavailable_reason = unavailable_reason
        self.availability_checks = 0
        self.calls: list[dict[str, object]] = []

    def is_available(self):
        self.availability_checks += 1
        return self.available, "" if self.available else self.unavailable_reason

    def salvage_exact_upgrade(
        self,
        item_id: int,
        option: object,
        *,
        preferred_kit_id: int = 0,
        timeout_ms: int = 0,
        debug_enabled: bool = False,
    ):
        self.calls.append(
            {
                "item_id": int(item_id),
                "option": option,
                "preferred_kit_id": int(preferred_kit_id),
                "timeout_ms": int(timeout_ms),
                "debug_enabled": bool(debug_enabled),
            }
        )
        if False:
            yield None
        return self.result


def _install_fake_exact_salvage_bridge(widget, fake_bridge: _FakeExactUpgradeSalvageBridge) -> None:
    widget._exact_upgrade_salvage_bridge = fake_bridge
    widget._salvage_upgrade_session_support_cache = None


def _make_salvage_candidate(module, item, rule, *, reason: str = "specific upgrade target"):
    return module.SalvageCandidate(
        item=item,
        rule_index=0,
        rule=rule,
        reason=reason,
    )


def _test_specific_upgrade_salvage_target_accepts_compatible_option(module) -> None:
    original_db = _install_weapon_mod_catalog_fixture(module)
    try:
        widget = _make_widget(module)
        fake_bridge = _FakeExactUpgradeSalvageBridge(module, available=True)
        _install_fake_exact_salvage_bridge(widget, fake_bridge)
        widget.salvage_settings = _salvage_settings(
            module,
            rules=[_make_specific_suffix_salvage_rule(module, module.SALVAGE_OPTION_SUFFIX)],
        )
        item = _make_specific_suffix_item(module)

        reason = widget._get_salvage_candidate_block_reason(
            item,
            [],
            require_salvage_kit=True,
            salvage_kit_id=1,
        )

        _expect(reason == "", "Specific suffix target should be executable with the suffix salvage option.")
        _expect(fake_bridge.calls == [], "Candidate evaluation should not execute the salvage bridge.")
        _expect(
            "specific upgrade target" in widget._get_salvage_selection_reason(item),
            "Specific upgrade target should produce a salvage selection reason.",
        )
    finally:
        module.MOD_DB = original_db


def _test_specific_upgrade_salvage_backend_unavailable_blocks(module) -> None:
    original_db = _install_weapon_mod_catalog_fixture(module)
    try:
        widget = _make_widget(module)
        fake_bridge = _FakeExactUpgradeSalvageBridge(module, available=False)
        _install_fake_exact_salvage_bridge(widget, fake_bridge)
        widget.salvage_settings = _salvage_settings(
            module,
            rules=[_make_specific_suffix_salvage_rule(module, module.SALVAGE_OPTION_SUFFIX)],
        )
        item = _make_specific_suffix_item(module)

        reason = widget._get_salvage_candidate_block_reason(
            item,
            [],
            require_salvage_kit=True,
            salvage_kit_id=1,
        )

        _expect(
            reason == module.SALVAGE_UPGRADE_BACKEND_UNAVAILABLE_REASON,
            "Unavailable exact-upgrade salvage backend should block specific-upgrade salvage.",
        )
        _expect(fake_bridge.calls == [], "Backend availability checks should not execute salvage.")
    finally:
        module.MOD_DB = original_db


def _test_specific_upgrade_salvage_current_bridge_disabled_by_default(module) -> None:
    original_db = _install_weapon_mod_catalog_fixture(module)
    try:
        widget = _make_widget(module)
        widget.salvage_settings = _salvage_settings(
            module,
            rules=[_make_specific_suffix_salvage_rule(module, module.SALVAGE_OPTION_SUFFIX)],
        )
        item = _make_specific_suffix_item(module)

        reason = widget._get_salvage_candidate_block_reason(
            item,
            [],
            require_salvage_kit=True,
            salvage_kit_id=1,
        )
        bridge = widget._get_exact_upgrade_salvage_bridge()

        _expect(
            reason == module.SALVAGE_UPGRADE_BACKEND_UNAVAILABLE_REASON,
            "The current Frenkey/BT bridge should fail closed for exact-upgrade salvage.",
        )
        _expect(
            getattr(bridge, "_load_attempted", False),
            "Current bridge availability should be checked before exact-upgrade salvage is allowed.",
        )
        _expect(
            not getattr(bridge, "_loaded", True),
            "Current bridge should not load the destructive BT salvage path without deterministic slot targeting.",
        )
        _expect(
            getattr(bridge, "_BTNodes", None) is None,
            "Current bridge should not bind BTNodes while exact-upgrade targeting is disabled.",
        )
    finally:
        module.MOD_DB = original_db


def _test_specific_upgrade_salvage_current_bridge_blocks_execute_before_node(module) -> None:
    original_db = _install_weapon_mod_catalog_fixture(module)
    try:
        widget = _make_widget(module)
        item = _make_specific_suffix_item(module)
        rule = _make_specific_suffix_salvage_rule(module, module.SALVAGE_OPTION_SUFFIX)
        widget.salvage_settings = _salvage_settings(module, rules=[rule])
        widget._build_inventory_item_info = lambda item_id: item if int(item_id) == int(item.item_id) else None
        widget._get_salvage_kit_id_for_option = lambda _option: 777

        status = _drain_generator_return(
            widget._salvage_one_item_with_rule(
                _make_salvage_candidate(module, item, rule),
                [],
            )
        )
        bridge = widget._get_exact_upgrade_salvage_bridge()

        _expect(status == "blocked", "Current exact-upgrade bridge should block execution before any salvage node runs.")
        _expect(
            getattr(bridge, "_BTNodes", None) is None,
            "Blocked current bridge execution should not construct or call Frenkey BTNodes.",
        )
        _expect(
            getattr(bridge, "_load_reason", "") == module.SALVAGE_UPGRADE_BACKEND_UNAVAILABLE_REASON,
            "Blocked current bridge execution should expose the deterministic-targeting safety reason.",
        )
    finally:
        module.MOD_DB = original_db


def _test_specific_upgrade_salvage_protection_blocks_before_bridge(module) -> None:
    original_db = _install_weapon_mod_catalog_fixture(module)
    try:
        widget = _make_widget(module)
        fake_bridge = _FakeExactUpgradeSalvageBridge(module, available=True)
        _install_fake_exact_salvage_bridge(widget, fake_bridge)
        widget.salvage_settings = _salvage_settings(
            module,
            rules=[_make_specific_suffix_salvage_rule(module, module.SALVAGE_OPTION_SUFFIX)],
        )
        item = _make_specific_suffix_item(module)
        protected_rule = module._normalize_sell_rule(
            module.SellRule(
                enabled=True,
                kind=module.SELL_KIND_WEAPONS,
                rarities=_rarity_flags("gold"),
                blacklist_model_ids=[int(item.model_id)],
            )
        )

        reason = widget._get_salvage_candidate_block_reason(
            item,
            [(0, protected_rule)],
            require_salvage_kit=True,
            salvage_kit_id=1,
        )

        _expect(
            reason.startswith("protected:"),
            "Protected specific-upgrade targets should block before backend checks.",
        )
        _expect(fake_bridge.availability_checks == 0, "Protected items should not check backend availability.")
        _expect(fake_bridge.calls == [], "Protected items should not execute the salvage bridge.")
    finally:
        module.MOD_DB = original_db


def _test_specific_upgrade_salvage_target_blocks_mismatched_option(module) -> None:
    original_db = _install_weapon_mod_catalog_fixture(module)
    try:
        widget = _make_widget(module)
        fake_bridge = _FakeExactUpgradeSalvageBridge(module, available=True)
        _install_fake_exact_salvage_bridge(widget, fake_bridge)
        widget.salvage_settings = _salvage_settings(
            module,
            rules=[_make_specific_suffix_salvage_rule(module, module.SALVAGE_OPTION_PREFIX)],
        )
        item = _make_specific_suffix_item(module)

        reason = widget._get_salvage_candidate_block_reason(
            item,
            [],
            require_salvage_kit=True,
            salvage_kit_id=1,
        )

        _expect(
            reason.startswith("specific upgrade target requires Salvage suffix"),
            "Specific suffix target should not execute through prefix salvage.",
        )
        _expect(
            "configured for Salvage prefix" in reason,
            "Mismatched specific-upgrade block should name the configured broad option.",
        )
        _expect(
            fake_bridge.availability_checks == 0,
            "Mismatched specific-upgrade options should block before backend checks.",
        )
        _expect(fake_bridge.calls == [], "Mismatched specific-upgrade options should not execute the bridge.")
    finally:
        module.MOD_DB = original_db


def _test_specific_upgrade_salvage_bridge_success_returns_processed(module) -> None:
    original_db = _install_weapon_mod_catalog_fixture(module)
    try:
        widget = _make_widget(module)
        item = _make_specific_suffix_item(module)
        rule = _make_specific_suffix_salvage_rule(module, module.SALVAGE_OPTION_SUFFIX)
        fake_bridge = _FakeExactUpgradeSalvageBridge(
            module,
            available=True,
            result=module._ExactUpgradeSalvageBridgeResult(True, "processed", ""),
        )
        _install_fake_exact_salvage_bridge(widget, fake_bridge)
        widget.salvage_settings = _salvage_settings(module, rules=[rule])
        widget._build_inventory_item_info = lambda item_id: item if int(item_id) == int(item.item_id) else None
        widget._get_salvage_kit_id_for_option = lambda _option: 777

        status = _drain_generator_return(
            widget._salvage_one_item_with_rule(
                _make_salvage_candidate(module, item, rule),
                [],
            )
        )

        _expect(status == "processed", "Verified exact-upgrade bridge success should return processed.")
        _expect(len(fake_bridge.calls) == 1, "Matching exact-upgrade salvage should execute the bridge once.")
        _expect(
            fake_bridge.calls[0]["option"] == module.SALVAGE_OPTION_SUFFIX,
            "Suffix targets should use suffix salvage.",
        )
        _expect(
            fake_bridge.calls[0]["preferred_kit_id"] == 777,
            "The selected upgrade salvage kit should be passed through.",
        )
    finally:
        module.MOD_DB = original_db


def _test_specific_upgrade_salvage_wrong_slot_completion_returns_failed(module) -> None:
    original_db = _install_weapon_mod_catalog_fixture(module)
    try:
        widget = _make_widget(module)
        item = _make_specific_suffix_item(module)
        rule = _make_specific_suffix_salvage_rule(module, module.SALVAGE_OPTION_SUFFIX)
        fake_bridge = _FakeExactUpgradeSalvageBridge(
            module,
            available=True,
            result=module._ExactUpgradeSalvageBridgeResult(
                False,
                "failed",
                "backend salvage completed but targeted slot remains and another upgrade was removed",
            ),
        )
        _install_fake_exact_salvage_bridge(widget, fake_bridge)
        widget.salvage_settings = _salvage_settings(module, rules=[rule])
        widget._build_inventory_item_info = lambda item_id: item if int(item_id) == int(item.item_id) else None
        widget._get_salvage_kit_id_for_option = lambda _option: 777

        status = _drain_generator_return(
            widget._salvage_one_item_with_rule(
                _make_salvage_candidate(module, item, rule),
                [],
            )
        )

        _expect(status == "failed", "Wrong-slot exact-upgrade completion should fail closed.")
        _expect(
            len(fake_bridge.calls) == 1,
            "Only a deliberately injected deterministic fake bridge should reach post-salvage verification.",
        )
    finally:
        module.MOD_DB = original_db


def _test_specific_upgrade_salvage_bridge_not_called_for_protected_execute(module) -> None:
    original_db = _install_weapon_mod_catalog_fixture(module)
    try:
        widget = _make_widget(module)
        item = _make_specific_suffix_item(module)
        rule = _make_specific_suffix_salvage_rule(module, module.SALVAGE_OPTION_SUFFIX)
        fake_bridge = _FakeExactUpgradeSalvageBridge(module, available=True)
        _install_fake_exact_salvage_bridge(widget, fake_bridge)
        widget.salvage_settings = _salvage_settings(module, rules=[rule])
        widget._build_inventory_item_info = lambda item_id: item if int(item_id) == int(item.item_id) else None
        widget._get_salvage_kit_id_for_option = lambda _option: 777
        protected_rule = module._normalize_sell_rule(
            module.SellRule(
                enabled=True,
                kind=module.SELL_KIND_WEAPONS,
                rarities=_rarity_flags("gold"),
                blacklist_model_ids=[int(item.model_id)],
            )
        )

        status = _drain_generator_return(
            widget._salvage_one_item_with_rule(
                _make_salvage_candidate(module, item, rule),
                [(0, protected_rule)],
            )
        )

        _expect(status == "blocked", "Protected exact-upgrade execution should block before bridge execution.")
        _expect(fake_bridge.availability_checks == 0, "Protected execution should not check backend availability.")
        _expect(fake_bridge.calls == [], "Protected execution should not call the bridge.")
    finally:
        module.MOD_DB = original_db


def _test_specific_upgrade_salvage_target_mismatch_still_blocks_destroy(module) -> None:
    original_db = _install_weapon_mod_catalog_fixture(module)
    try:
        widget = _make_widget(module)
        widget.salvage_settings = _salvage_settings(
            module,
            rules=[_make_specific_suffix_salvage_rule(module, module.SALVAGE_OPTION_PREFIX)],
        )
        widget.destroy_rules = [
            module._normalize_destroy_rule(
                module.DestroyRule(
                    enabled=True,
                    kind=module.DESTROY_KIND_WEAPONS,
                    rarities=_rarity_flags("gold"),
                )
            )
        ]
        widget._collect_inventory_items = lambda: [_make_specific_suffix_item(module)]

        plan = widget._build_plan()

        _expect(
            not plan.destroy_actions,
            "Mismatched specific-upgrade salvage targets should still reserve matching items from destroy.",
        )
        _expect(
            any(
                "salvage wins over destroy" in entry.reason
                for entry in plan.entries
                if entry.action_type == "destroy"
            ),
            "Destroy preview should still explain that the specific-upgrade salvage rule claimed the item.",
        )
    finally:
        module.MOD_DB = original_db


def _test_specific_upgrade_salvage_target_blocks_default_and_material_options(module) -> None:
    original_db = _install_weapon_mod_catalog_fixture(module)
    try:
        item = _make_specific_suffix_item(module)
        for salvage_option in (module.SALVAGE_OPTION_DEFAULT, module.SALVAGE_OPTION_MATERIALS):
            widget = _make_widget(module)
            fake_bridge = _FakeExactUpgradeSalvageBridge(module, available=True)
            _install_fake_exact_salvage_bridge(widget, fake_bridge)
            widget.salvage_settings = _salvage_settings(
                module,
                rules=[_make_specific_suffix_salvage_rule(module, salvage_option)],
            )

            reason = widget._get_salvage_candidate_block_reason(
                item,
                [],
                require_salvage_kit=True,
                salvage_kit_id=1,
            )

            _expect(
                reason == "specific upgrade target requires prefix, suffix, or inscription salvage option",
                "Specific-upgrade targets should not execute through default/material salvage.",
            )
            _expect(
                fake_bridge.availability_checks == 0,
                "Default/material options should block before backend checks.",
            )
            _expect(fake_bridge.calls == [], "Default/material options should not call the bridge.")
    finally:
        module.MOD_DB = original_db


def _test_identify_exact_rarity_claims_before_destroy_and_cleanup(module) -> None:
    widget = _make_widget(module)
    widget.identify_settings = _identify_settings(module, rarities=["blue"], before_execute=True)
    widget._get_id_kit_id = lambda: 900
    widget.cleanup_targets = [module.CleanupTarget(model_id=200, keep_on_character=0)]
    widget.destroy_rules = [
        module._normalize_destroy_rule(
            module.DestroyRule(
                enabled=True,
                kind=module.DESTROY_KIND_EXPLICIT_MODELS,
                whitelist_targets=[
                    module.WhitelistTarget(model_id=200, keep_count=0),
                    module.WhitelistTarget(model_id=300, keep_count=0),
                ],
            )
        )
    ]
    widget._get_supported_context = lambda: (
        True,
        "Ready",
        {
            module.MERCHANT_TYPE_MERCHANT: (1.0, 1.0),
            module.MERCHANT_TYPE_MATERIALS: (2.0, 2.0),
            module.MERCHANT_TYPE_RUNE_TRADER: (3.0, 3.0),
            module.MERCHANT_TYPE_RARE_MATERIALS: (4.0, 4.0),
        },
    )
    widget._collect_inventory_items = lambda: [
        _make_item(module, item_id=1, model_id=200, name="Blue Sword", rarity="Blue", identified=False),
        _make_item(module, item_id=2, model_id=300, name="Purple Sword", rarity="Purple", identified=False),
    ]

    plan = widget._build_plan()

    _expect(plan.identify_item_ids == [1], "Identify planning should select only exact blue unidentified items.")
    _expect(plan.identify_claimed_item_ids == [1], "Identify planning should claim selected items before later actions.")
    _expect(1 not in [action.item_id for action in plan.destroy_actions], "Identify-selected items should not also be planned for destroy.")
    _expect(2 in [action.item_id for action in plan.destroy_actions], "Unselected purple items should remain eligible for later destroy rules.")
    _expect(1 not in [transfer.item_id for transfer in plan.cleanup_transfers], "Identify-selected items should not also be planned for cleanup.")


def _test_identify_no_kit_still_claims_selected_items(module) -> None:
    widget = _make_widget(module)
    widget.identify_settings = _identify_settings(module, rarities=["blue"], before_execute=True)
    widget._get_id_kit_id = lambda: 0
    widget.cleanup_targets = [module.CleanupTarget(model_id=200, keep_on_character=0)]
    widget.sell_rules = [
        module._normalize_sell_rule(
            module.SellRule(
                enabled=True,
                kind=module.SELL_KIND_EXPLICIT_MODELS,
                whitelist_targets=[module.WhitelistTarget(model_id=200, keep_count=0)],
            )
        )
    ]
    widget.destroy_rules = [
        module._normalize_destroy_rule(
            module.DestroyRule(
                enabled=True,
                kind=module.DESTROY_KIND_EXPLICIT_MODELS,
                whitelist_targets=[module.WhitelistTarget(model_id=200, keep_count=0)],
            )
        )
    ]
    widget._get_supported_context = lambda: (
        True,
        "Ready",
        {
            module.MERCHANT_TYPE_MERCHANT: (1.0, 1.0),
            module.MERCHANT_TYPE_MATERIALS: (2.0, 2.0),
            module.MERCHANT_TYPE_RUNE_TRADER: (3.0, 3.0),
            module.MERCHANT_TYPE_RARE_MATERIALS: (4.0, 4.0),
        },
    )
    widget._collect_inventory_items = lambda: [
        _make_item(module, item_id=1, model_id=200, name="Blue Sword", rarity="Blue", identified=False),
    ]

    plan = widget._build_plan()

    _expect(not plan.identify_item_ids, "No ID kit should leave identify with no runnable item IDs.")
    _expect(plan.identify_claimed_item_ids == [1], "No-kit identify candidates should still be claimed in the preview.")
    _expect(not plan.destroy_actions and not plan.destroy_item_ids, "No-kit identify candidates should not fall through to destroy.")
    _expect(not plan.merchant_sell_item_ids, "No-kit identify candidates should not fall through to sell.")
    _expect(not plan.cleanup_transfers, "No-kit identify candidates should not fall through to cleanup.")
    _expect(
        any(entry.action_type == "identify" and entry.state == module.PLAN_STATE_SKIPPED and "No ID kit" in entry.reason for entry in plan.entries),
        "Preview should surface a no-ID-kit identify warning.",
    )


def _test_identify_on_inventory_change_queues_auto_pass(module) -> None:
    widget = _make_widget(module)
    widget.identify_settings = _identify_settings(module, rarities=["blue"], on_inventory_change=True)
    widget.identify_last_signature = ((1, 1),)
    widget._get_inventory_signature = lambda items=None: ((1, 1), (2, 1))
    queued: list[bool] = []
    widget._queue_identify_now = lambda *, auto_triggered=False: queued.append(bool(auto_triggered))

    widget._update_identify_runtime()

    _expect(queued == [True], "Inventory-change identify should queue an auto identify pass when inventory changes.")
    _expect(not widget.identify_rescan_requested, "Auto identify queueing should consume the pending rescan flag.")


def _test_protected_salvage_destroy_overlap_blocks_both(module) -> None:
    widget = _make_widget(module)
    widget.salvage_settings = _salvage_settings(module, rarities=["gold"])
    widget.sell_rules = [
        module._normalize_sell_rule(
            module.SellRule(
                enabled=True,
                kind=module.SELL_KIND_WEAPONS,
                rarities=_rarity_flags("gold"),
                blacklist_model_ids=[4000],
            )
        )
    ]
    widget.destroy_rules = [
        module._normalize_destroy_rule(
            module.DestroyRule(
                enabled=True,
                kind=module.DESTROY_KIND_WEAPONS,
                rarities=_rarity_flags("gold"),
            )
        )
    ]
    widget._collect_inventory_items = lambda: [
        _make_item(
            module,
            item_id=40,
            model_id=4000,
            name="Protected Gold Weapon",
            rarity="Gold",
            identified=True,
            salvageable=True,
            is_weapon_like=True,
        )
    ]

    plan = widget._build_plan()

    _expect(not plan.destroy_actions, "Protected items should not be planned for destroy when they also match salvage.")
    _expect(
        any("Hard-protected" in entry.reason for entry in plan.entries if entry.action_type == "destroy"),
        "Protection should be the displayed block reason when protection and salvage overlap.",
    )
    candidate_reason = widget._get_salvage_candidate_block_reason(
        widget._collect_inventory_items()[0],
        widget._collect_enabled_sell_rules(),
        require_salvage_kit=True,
        salvage_kit_id=1,
    )
    _expect(candidate_reason.startswith("protected:"), "Protected items should also block salvage candidate evaluation.")


def _test_build_plan_captures_inventory_and_marks_conditional_stock_buy(module) -> None:
    widget = _make_widget(module)
    widget.buy_rules = [
        module._normalize_buy_rule(
            module.BuyRule(
                enabled=True,
                kind=module.BUY_KIND_MERCHANT_STOCK,
                model_id=555,
                target_count=3,
                max_per_run=2,
            )
        )
    ]
    widget.sell_rules = [
        module._normalize_sell_rule(
            module.SellRule(
                enabled=True,
                kind=module.SELL_KIND_EXPLICIT_MODELS,
                model_ids=[111],
                keep_count=0,
            )
        )
    ]
    widget._get_supported_context = lambda: (
        True,
        "Ready",
        {
            module.MERCHANT_TYPE_MERCHANT: (1.0, 1.0),
            module.MERCHANT_TYPE_MATERIALS: (2.0, 2.0),
            module.MERCHANT_TYPE_RUNE_TRADER: (3.0, 3.0),
            module.MERCHANT_TYPE_RARE_MATERIALS: (4.0, 4.0),
        },
    )
    widget._collect_inventory_items = lambda: [
        _make_item(module, item_id=1, model_id=111, name="Iron Sword", quantity=1),
    ]

    plan = widget._build_plan()

    _expect(plan.inventory_snapshot_captured, "Plan build should record that an inventory snapshot was captured.")
    _expect(plan.inventory_model_counts == {111: 1}, "Plan build should persist model counts from the preview snapshot.")
    _expect(plan.inventory_item_count == 1, "Plan build should record the number of inventory stacks it saw.")
    _expect(len(plan.merchant_stock_buys) == 1, "Merchant stock target should produce one conditional buy action.")
    _expect(plan.merchant_stock_buys[0].quantity == 2, "Merchant stock target should respect Max Per Run when building the plan.")
    _expect(any(entry.state == module.PLAN_STATE_CONDITIONAL for entry in plan.entries), "Merchant stock preview entries should remain conditional.")
    _expect(plan.merchant_sell_item_ids == [1], "Explicit sell rules should still allocate matching inventory items.")
    _expect(plan.has_actions, "Plan should be actionable when either buy or sell work was found.")


def _test_consumable_crafter_plan_title_gate_blocks_low_rank(module) -> None:
    widget = _make_widget(module)
    essence_model_id = int(module.ModelID.Essence_Of_Celerity.value)
    widget.buy_rules = [
        module._normalize_buy_rule(
            module.BuyRule(
                enabled=True,
                kind=module.BUY_KIND_CONSUMABLE_CRAFTER_TARGET,
                merchant_stock_targets=[
                    module.MerchantStockTarget(model_id=essence_model_id, target_count=1, max_per_run=1),
                ],
            )
        )
    ]
    widget._get_supported_context = lambda: (
        True,
        "Ready",
        {
            module.MERCHANT_TYPE_CONSUMABLE_CRAFTER: (3592.99, 78.78),
        },
    )
    widget._collect_inventory_items = lambda: []
    original_inventory = getattr(module.GLOBAL_CACHE, "Inventory", None)
    original_player = module.Player
    try:
        module.GLOBAL_CACHE.Inventory = types.SimpleNamespace(IsStorageOpen=lambda: False)
        module.Player = types.SimpleNamespace(
            GetSkillPointData=lambda: (100, 100),
            GetTitle=lambda _title_id: types.SimpleNamespace(current_points=0),
        )

        plan = widget._build_plan()

        _expect(not plan.consumable_crafter_buys, "Low title rank should block consumable crafter buys before execution.")
        _expect(
            any(
                entry.merchant_type == module.MERCHANT_TYPE_CONSUMABLE_CRAFTER
                and entry.state == module.PLAN_STATE_SKIPPED
                and "requires rank 3" in entry.reason
                for entry in plan.entries
            ),
            "Preview should explain the consumable crafter title-rank gate.",
        )
    finally:
        module.GLOBAL_CACHE.Inventory = original_inventory
        module.Player = original_player


def _test_consumable_crafter_plan_caps_by_skill_gold_and_material_storage(module) -> None:
    widget = _make_widget(module)
    essence_model_id = int(module.ModelID.Essence_Of_Celerity.value)
    feather_model_id = int(module.ModelID.Feather.value)
    dust_model_id = int(module.ModelID.Pile_Of_Glittering_Dust.value)
    widget.buy_rules = [
        module._normalize_buy_rule(
            module.BuyRule(
                enabled=True,
                kind=module.BUY_KIND_CONSUMABLE_CRAFTER_TARGET,
                merchant_stock_targets=[
                    module.MerchantStockTarget(model_id=essence_model_id, target_count=5, max_per_run=5),
                ],
            )
        )
    ]
    widget._get_supported_context = lambda: (
        True,
        "Ready",
        {
            module.MERCHANT_TYPE_CONSUMABLE_CRAFTER: (3592.99, 78.78),
        },
    )
    widget._collect_inventory_items = lambda: [
        _make_item(module, item_id=1, model_id=feather_model_id, name="Feather", quantity=250, is_material=True),
    ]
    widget._collect_storage_items = lambda: []
    widget._get_material_storage_quantity_and_slot = (
        lambda model_id: (100, 3, 250) if int(model_id) == dust_model_id else (0, 0, 250)
    )
    original_inventory = getattr(module.GLOBAL_CACHE, "Inventory", None)
    original_player = module.Player
    try:
        module.GLOBAL_CACHE.Inventory = types.SimpleNamespace(
            IsStorageOpen=lambda: True,
            GetGoldOnCharacter=lambda: 250,
            GetGoldInStorage=lambda: 250,
        )
        module.Player = types.SimpleNamespace(
            GetSkillPointData=lambda: (2, 100),
            GetTitle=lambda _title_id: types.SimpleNamespace(current_points=999999),
        )

        plan = widget._build_plan()

        _expect(plan.storage_exact, "Open storage should make consumable crafter planning use exact storage/material counts.")
        _expect(len(plan.consumable_crafter_buys) == 1, "Supported consumable crafter target should plan one craft action.")
        _expect(
            plan.consumable_crafter_buys[0].quantity == 2,
            "Consumable crafter planning should cap by skill points, combined gold, and material storage availability.",
        )
        _expect(
            any(
                entry.merchant_type == module.MERCHANT_TYPE_CONSUMABLE_CRAFTER
                and entry.quantity == 2
                and entry.state == module.PLAN_STATE_CONDITIONAL
                and "Capped by available skill points, gold, or materials." in entry.reason
                for entry in plan.entries
            ),
            "Preview should show the exact capped consumable crafter quantity.",
        )
    finally:
        module.GLOBAL_CACHE.Inventory = original_inventory
        module.Player = original_player


def _test_consumable_crafter_craft_amount_mode_ignores_existing_xunlai_output(module) -> None:
    widget = _make_widget(module)
    essence_model_id = int(module.ModelID.Essence_Of_Celerity.value)
    feather_model_id = int(module.ModelID.Feather.value)
    dust_model_id = int(module.ModelID.Pile_Of_Glittering_Dust.value)
    widget.buy_rules = [
        module._normalize_buy_rule(
            module.BuyRule(
                enabled=True,
                kind=module.BUY_KIND_CONSUMABLE_CRAFTER_TARGET,
                merchant_stock_targets=[
                    module.MerchantStockTarget(model_id=essence_model_id, target_count=5, max_per_run=5),
                ],
                consumable_crafter_count_mode=module.CONSUMABLE_CRAFTER_COUNT_MODE_CRAFT_AMOUNT,
            )
        )
    ]
    widget._get_supported_context = lambda: (
        True,
        "Ready",
        {
            module.MERCHANT_TYPE_CONSUMABLE_CRAFTER: (3592.99, 78.78),
        },
    )
    widget._collect_inventory_items = lambda: [
        _make_item(module, item_id=1, model_id=feather_model_id, name="Feather", quantity=250, is_material=True),
        _make_item(module, item_id=2, model_id=dust_model_id, name="Pile of Glittering Dust", quantity=250, is_material=True),
    ]
    widget._collect_storage_items = lambda: [
        _make_item(module, item_id=3, model_id=essence_model_id, name="Essence of Celerity", quantity=1),
    ]
    original_inventory = getattr(module.GLOBAL_CACHE, "Inventory", None)
    original_player = module.Player
    try:
        module.GLOBAL_CACHE.Inventory = types.SimpleNamespace(
            IsStorageOpen=lambda: True,
            GetGoldOnCharacter=lambda: 1250,
            GetGoldInStorage=lambda: 0,
        )
        module.Player = types.SimpleNamespace(
            GetSkillPointData=lambda: (5, 100),
            GetTitle=lambda _title_id: types.SimpleNamespace(current_points=999999),
        )

        plan = widget._build_plan()

        _expect(len(plan.consumable_crafter_buys) == 1, "Craft amount mode should plan the selected consumable craft.")
        _expect(
            plan.consumable_crafter_buys[0].quantity == 5,
            "Craft amount mode should ignore matching consumables already in Xunlai storage.",
        )
    finally:
        module.GLOBAL_CACHE.Inventory = original_inventory
        module.Player = original_player


def _test_consumable_crafter_maintain_mode_counts_existing_xunlai_output(module) -> None:
    widget = _make_widget(module)
    essence_model_id = int(module.ModelID.Essence_Of_Celerity.value)
    feather_model_id = int(module.ModelID.Feather.value)
    dust_model_id = int(module.ModelID.Pile_Of_Glittering_Dust.value)
    widget.buy_rules = [
        module._normalize_buy_rule(
            module.BuyRule(
                enabled=True,
                kind=module.BUY_KIND_CONSUMABLE_CRAFTER_TARGET,
                merchant_stock_targets=[
                    module.MerchantStockTarget(model_id=essence_model_id, target_count=5, max_per_run=5),
                ],
                consumable_crafter_count_mode=module.CONSUMABLE_CRAFTER_COUNT_MODE_MAINTAIN_STOCK,
            )
        )
    ]
    widget._get_supported_context = lambda: (
        True,
        "Ready",
        {
            module.MERCHANT_TYPE_CONSUMABLE_CRAFTER: (3592.99, 78.78),
        },
    )
    widget._collect_inventory_items = lambda: [
        _make_item(module, item_id=1, model_id=feather_model_id, name="Feather", quantity=250, is_material=True),
        _make_item(module, item_id=2, model_id=dust_model_id, name="Pile of Glittering Dust", quantity=250, is_material=True),
    ]
    widget._collect_storage_items = lambda: [
        _make_item(module, item_id=3, model_id=essence_model_id, name="Essence of Celerity", quantity=1),
    ]
    original_inventory = getattr(module.GLOBAL_CACHE, "Inventory", None)
    original_player = module.Player
    try:
        module.GLOBAL_CACHE.Inventory = types.SimpleNamespace(
            IsStorageOpen=lambda: True,
            GetGoldOnCharacter=lambda: 1250,
            GetGoldInStorage=lambda: 0,
        )
        module.Player = types.SimpleNamespace(
            GetSkillPointData=lambda: (5, 100),
            GetTitle=lambda _title_id: types.SimpleNamespace(current_points=999999),
        )

        plan = widget._build_plan()

        _expect(len(plan.consumable_crafter_buys) == 1, "Maintain mode should plan the selected consumable craft.")
        _expect(
            plan.consumable_crafter_buys[0].quantity == 4,
            "Maintain mode should count matching consumables already in Xunlai storage before crafting the shortage.",
        )
    finally:
        module.GLOBAL_CACHE.Inventory = original_inventory
        module.Player = original_player


def _test_consumable_crafter_plan_reserves_shared_material_storage_across_targets(module) -> None:
    widget = _make_widget(module)
    essence_model_id = int(module.ModelID.Essence_Of_Celerity.value)
    grail_model_id = int(module.ModelID.Grail_Of_Might.value)
    feather_model_id = int(module.ModelID.Feather.value)
    iron_model_id = int(module.ModelID.Iron_Ingot.value)
    dust_model_id = int(module.ModelID.Pile_Of_Glittering_Dust.value)
    widget.buy_rules = [
        module._normalize_buy_rule(
            module.BuyRule(
                enabled=True,
                kind=module.BUY_KIND_CONSUMABLE_CRAFTER_TARGET,
                merchant_stock_targets=[
                    module.MerchantStockTarget(model_id=essence_model_id, target_count=3, max_per_run=3),
                    module.MerchantStockTarget(model_id=grail_model_id, target_count=3, max_per_run=3),
                ],
                consumable_crafter_count_mode=module.CONSUMABLE_CRAFTER_COUNT_MODE_CRAFT_AMOUNT,
            )
        )
    ]
    widget._get_supported_context = lambda: (
        True,
        "Ready",
        {
            module.MERCHANT_TYPE_CONSUMABLE_CRAFTER: (3592.99, 78.78),
        },
    )
    widget._collect_inventory_items = lambda: [
        _make_item(module, item_id=1, model_id=feather_model_id, name="Feather", quantity=150, is_material=True),
        _make_item(module, item_id=2, model_id=iron_model_id, name="Iron Ingot", quantity=150, is_material=True),
    ]
    widget._collect_storage_items = lambda: []
    widget._get_material_storage_quantity_and_slot = (
        lambda model_id: (158, 9, 250) if int(model_id) == dust_model_id else (0, 0, 250)
    )
    original_inventory = getattr(module.GLOBAL_CACHE, "Inventory", None)
    original_player = module.Player
    try:
        module.GLOBAL_CACHE.Inventory = types.SimpleNamespace(
            IsStorageOpen=lambda: True,
            GetGoldOnCharacter=lambda: 1500,
            GetGoldInStorage=lambda: 0,
        )
        module.Player = types.SimpleNamespace(
            GetSkillPointData=lambda: (6, 100),
            GetTitle=lambda _title_id: types.SimpleNamespace(current_points=999999),
        )

        plan = widget._build_plan()

        quantities_by_model = {craft.model_id: craft.quantity for craft in plan.consumable_crafter_buys}
        _expect(
            quantities_by_model.get(essence_model_id, 0) == 3,
            "First consumable crafter target should reserve the shared Glittering Dust it needs.",
        )
        _expect(
            quantities_by_model.get(grail_model_id, 0) == 0,
            "Later consumable crafter targets should not reuse Glittering Dust already reserved by earlier targets.",
        )
        _expect(
            sum(int(craft.quantity) for craft in plan.consumable_crafter_buys) == 3,
            "Consumable crafter preview should cap total crafts by shared material storage availability.",
        )
        _expect(
            any(
                entry.merchant_type == module.MERCHANT_TYPE_CONSUMABLE_CRAFTER
                and entry.state == module.PLAN_STATE_SKIPPED
                and "need 150" in entry.reason.lower()
                and str(dust_model_id) in entry.reason
                and "found 8" in entry.reason
                for entry in plan.entries
            ),
            "Blocked consumable crafter preview rows should report the full requested material need and the remaining quantity found.",
        )
    finally:
        module.GLOBAL_CACHE.Inventory = original_inventory
        module.Player = original_player


def _test_consumable_crafter_partial_cap_reports_remaining_material_shortage(module) -> None:
    widget = _make_widget(module)
    essence_model_id = int(module.ModelID.Essence_Of_Celerity.value)
    grail_model_id = int(module.ModelID.Grail_Of_Might.value)
    feather_model_id = int(module.ModelID.Feather.value)
    iron_model_id = int(module.ModelID.Iron_Ingot.value)
    dust_model_id = int(module.ModelID.Pile_Of_Glittering_Dust.value)
    widget.buy_rules = [
        module._normalize_buy_rule(
            module.BuyRule(
                enabled=True,
                kind=module.BUY_KIND_CONSUMABLE_CRAFTER_TARGET,
                merchant_stock_targets=[
                    module.MerchantStockTarget(model_id=essence_model_id, target_count=2, max_per_run=2),
                    module.MerchantStockTarget(model_id=grail_model_id, target_count=3, max_per_run=3),
                ],
                consumable_crafter_count_mode=module.CONSUMABLE_CRAFTER_COUNT_MODE_CRAFT_AMOUNT,
            )
        )
    ]
    widget._get_supported_context = lambda: (
        True,
        "Ready",
        {
            module.MERCHANT_TYPE_CONSUMABLE_CRAFTER: (3592.99, 78.78),
        },
    )
    widget._collect_inventory_items = lambda: [
        _make_item(module, item_id=1, model_id=feather_model_id, name="Feather", quantity=100, is_material=True),
        _make_item(module, item_id=2, model_id=iron_model_id, name="Iron Ingot", quantity=150, is_material=True),
    ]
    widget._collect_storage_items = lambda: []
    widget._get_material_storage_quantity_and_slot = (
        lambda model_id: (158, 9, 250) if int(model_id) == dust_model_id else (0, 0, 250)
    )
    original_inventory = getattr(module.GLOBAL_CACHE, "Inventory", None)
    original_player = module.Player
    try:
        module.GLOBAL_CACHE.Inventory = types.SimpleNamespace(
            IsStorageOpen=lambda: True,
            GetGoldOnCharacter=lambda: 1250,
            GetGoldInStorage=lambda: 0,
        )
        module.Player = types.SimpleNamespace(
            GetSkillPointData=lambda: (5, 100),
            GetTitle=lambda _title_id: types.SimpleNamespace(current_points=999999),
        )

        plan = widget._build_plan()

        quantities_by_model = {craft.model_id: craft.quantity for craft in plan.consumable_crafter_buys}
        _expect(
            quantities_by_model.get(essence_model_id, 0) == 2,
            "First target should reserve enough Glittering Dust for two Essence crafts.",
        )
        _expect(
            quantities_by_model.get(grail_model_id, 0) == 1,
            "Second target should partially craft one Grail with the remaining shared Glittering Dust.",
        )
        _expect(
            any(
                entry.merchant_type == module.MERCHANT_TYPE_CONSUMABLE_CRAFTER
                and entry.model_id == 0
                and entry.label.startswith("Model")
                and entry.quantity == 1
                and entry.state == module.PLAN_STATE_CONDITIONAL
                and "remaining request" in entry.reason.lower()
                and "need 100" in entry.reason.lower()
                and str(dust_model_id) in entry.reason
                and "found 8" in entry.reason
                for entry in plan.entries
            ),
            "Partially capped consumable crafter preview rows should explain the unfulfilled remaining material need.",
        )
    finally:
        module.GLOBAL_CACHE.Inventory = original_inventory
        module.Player = original_player


def _test_consumable_crafter_resource_priority_follows_target_order(module) -> None:
    widget = _make_widget(module)
    essence_model_id = int(module.ModelID.Essence_Of_Celerity.value)
    grail_model_id = int(module.ModelID.Grail_Of_Might.value)
    feather_model_id = int(module.ModelID.Feather.value)
    iron_model_id = int(module.ModelID.Iron_Ingot.value)
    dust_model_id = int(module.ModelID.Pile_Of_Glittering_Dust.value)
    widget.buy_rules = [
        module._normalize_buy_rule(
            module.BuyRule(
                enabled=True,
                kind=module.BUY_KIND_CONSUMABLE_CRAFTER_TARGET,
                merchant_stock_targets=[
                    module.MerchantStockTarget(model_id=grail_model_id, target_count=3, max_per_run=3),
                    module.MerchantStockTarget(model_id=essence_model_id, target_count=3, max_per_run=3),
                ],
                consumable_crafter_count_mode=module.CONSUMABLE_CRAFTER_COUNT_MODE_CRAFT_AMOUNT,
            )
        )
    ]
    widget._get_supported_context = lambda: (
        True,
        "Ready",
        {
            module.MERCHANT_TYPE_CONSUMABLE_CRAFTER: (3673.02, -131.27),
        },
    )
    widget._collect_inventory_items = lambda: [
        _make_item(module, item_id=1, model_id=feather_model_id, name="Feather", quantity=150, is_material=True),
        _make_item(module, item_id=2, model_id=iron_model_id, name="Iron Ingot", quantity=150, is_material=True),
    ]
    widget._collect_storage_items = lambda: []
    widget._get_material_storage_quantity_and_slot = (
        lambda model_id: (150, 9, 250) if int(model_id) == dust_model_id else (0, 0, 250)
    )
    original_inventory = getattr(module.GLOBAL_CACHE, "Inventory", None)
    original_player = module.Player
    try:
        module.GLOBAL_CACHE.Inventory = types.SimpleNamespace(
            IsStorageOpen=lambda: True,
            GetGoldOnCharacter=lambda: 1500,
            GetGoldInStorage=lambda: 0,
        )
        module.Player = types.SimpleNamespace(
            GetSkillPointData=lambda: (6, 100),
            GetTitle=lambda _title_id: types.SimpleNamespace(current_points=999999),
        )

        plan = widget._build_plan()

        quantities_by_model = {craft.model_id: craft.quantity for craft in plan.consumable_crafter_buys}
        _expect(
            quantities_by_model.get(grail_model_id, 0) == 3,
            "First selected consumable target should reserve scarce shared materials first.",
        )
        _expect(
            quantities_by_model.get(essence_model_id, 0) == 0,
            "Later selected consumable targets should not preempt resources reserved by earlier rows.",
        )
    finally:
        module.GLOBAL_CACHE.Inventory = original_inventory
        module.Player = original_player


def _test_consumable_crafter_preview_warns_when_free_inventory_slots_are_low(module) -> None:
    widget = _make_widget(module)
    essence_model_id = int(module.ModelID.Essence_Of_Celerity.value)
    feather_model_id = int(module.ModelID.Feather.value)
    dust_model_id = int(module.ModelID.Pile_Of_Glittering_Dust.value)
    widget.buy_rules = [
        module._normalize_buy_rule(
            module.BuyRule(
                enabled=True,
                kind=module.BUY_KIND_CONSUMABLE_CRAFTER_TARGET,
                merchant_stock_targets=[
                    module.MerchantStockTarget(model_id=essence_model_id, target_count=1, max_per_run=1),
                ],
                consumable_crafter_count_mode=module.CONSUMABLE_CRAFTER_COUNT_MODE_CRAFT_AMOUNT,
            )
        )
    ]
    widget._get_supported_context = lambda: (
        True,
        "Ready",
        {
            module.MERCHANT_TYPE_CONSUMABLE_CRAFTER: (3592.99, 78.78),
        },
    )
    widget._collect_inventory_items = lambda: []
    widget._collect_storage_items = lambda: [
        _make_item(module, item_id=1, model_id=feather_model_id, name="Feather", quantity=50, is_material=True),
        _make_item(module, item_id=2, model_id=dust_model_id, name="Pile of Glittering Dust", quantity=50, is_material=True),
    ]
    original_inventory = getattr(module.GLOBAL_CACHE, "Inventory", None)
    original_player = module.Player
    try:
        module.GLOBAL_CACHE.Inventory = types.SimpleNamespace(
            IsStorageOpen=lambda: True,
            GetGoldOnCharacter=lambda: 250,
            GetGoldInStorage=lambda: 0,
            GetFreeSlotCount=lambda: 1,
        )
        module.Player = types.SimpleNamespace(
            GetSkillPointData=lambda: (1, 100),
            GetTitle=lambda _title_id: types.SimpleNamespace(current_points=999999),
        )

        plan = widget._build_plan()

        _expect(len(plan.consumable_crafter_buys) == 1, "Low inventory-space warning should not block consumable crafter planning.")
        _expect(
            any(
                entry.merchant_type == module.MERCHANT_TYPE_CONSUMABLE_CRAFTER
                and entry.label == "Inventory space"
                and entry.state == module.PLAN_STATE_SKIPPED
                and "may need up to 3 free slot" in entry.reason
                and "found 1" in entry.reason
                for entry in plan.entries
            ),
            "Consumable crafter preview should warn when planned material withdrawals and output may exceed free inventory slots.",
        )
    finally:
        module.GLOBAL_CACHE.Inventory = original_inventory
        module.Player = original_player


def _test_consumable_crafter_execution_prepares_materials_before_opening_crafter(module) -> None:
    widget = _make_widget(module)
    essence_model_id = int(module.ModelID.Essence_Of_Celerity.value)
    offered_item_id = 9001
    calls: list[str] = []
    original_player = module.Player
    original_inventory = getattr(module.GLOBAL_CACHE, "Inventory", None)
    original_item = getattr(module.GLOBAL_CACHE, "Item", None)
    original_trading = getattr(module.GLOBAL_CACHE, "Trading", None)
    original_merchant_yield = getattr(module.Routines.Yield, "Merchant", None)
    try:
        def _prepare(_crafts, *, vendor_name: str):
            calls.append(f"prepare:{vendor_name}")
            if False:
                yield None
            return True

        def _open(_coords, vendor_name: str):
            calls.append(f"open:{vendor_name}")
            if False:
                yield None
            return [offered_item_id]

        def _wait_for_transaction(*_args, **_kwargs):
            calls.append("wait_transaction")
            if False:
                yield None
            return True

        def _craft_item(*_args, **_kwargs) -> None:
            calls.append("craft")

        widget._prepare_consumable_crafting_materials = _prepare
        widget._open_consumable_crafter = _open
        widget._collect_crafting_ingredients_from_inventory = lambda _recipe: ([101, 102], [50, 50], [])
        module.Player = types.SimpleNamespace(
            GetSkillPointData=lambda: (5, 100),
            GetTitle=lambda _title_id: types.SimpleNamespace(current_points=999999),
        )
        module.GLOBAL_CACHE.Inventory = types.SimpleNamespace(
            IsStorageOpen=lambda: True,
            GetGoldOnCharacter=lambda: 1000,
            GetModelCount=lambda _model_id: 0,
        )
        module.GLOBAL_CACHE.Item = types.SimpleNamespace(GetModelID=lambda item_id: essence_model_id if int(item_id) == offered_item_id else 0)
        module.GLOBAL_CACHE.Trading = types.SimpleNamespace(
            Crafter=types.SimpleNamespace(CraftItem=_craft_item),
        )
        module.Routines.Yield.Merchant = types.SimpleNamespace(_wait_for_transaction=_wait_for_transaction)

        outcome = _drain_generator_return(
            widget._craft_planned_consumables(
                [
                    module.PlannedConsumableCraft(
                        model_id=essence_model_id,
                        quantity=1,
                        label="Essence of Celerity",
                        vendor_key="kwat",
                        vendor_name="Kwat",
                        coords=(3592.99, 78.78),
                    )
                ]
            )
        )

        _expect(outcome.completed == 1, "Consumable crafter execution should complete when prep, offer lookup, and transaction succeed.")
        _expect(
            calls[:2] == ["prepare:Kwat", "open:Kwat"],
            "Consumable crafter execution must withdraw materials before opening the crafter window.",
        )
        _expect("craft" in calls, "Consumable crafter execution should send the craft request after opening the crafter.")
    finally:
        module.Player = original_player
        module.GLOBAL_CACHE.Inventory = original_inventory
        module.GLOBAL_CACHE.Item = original_item
        module.GLOBAL_CACHE.Trading = original_trading
        module.Routines.Yield.Merchant = original_merchant_yield


def _test_lower_weapon_protection_hard_overrides_higher_explicit_sell(module) -> None:
    widget = _make_widget(module)
    widget.sell_rules = [
        module._normalize_sell_rule(
            module.SellRule(
                enabled=True,
                kind=module.SELL_KIND_EXPLICIT_MODELS,
                model_ids=[111],
                keep_count=0,
            )
        ),
        module._normalize_sell_rule(
            module.SellRule(
                enabled=True,
                kind=module.SELL_KIND_WEAPONS,
                protected_weapon_requirement_rules=[
                    module.WeaponRequirementRule(model_id=111, min_requirement=1, max_requirement=8),
                ],
            )
        ),
    ]
    widget._get_supported_context = lambda: (
        True,
        "Ready",
        {
            module.MERCHANT_TYPE_MERCHANT: (1.0, 1.0),
            module.MERCHANT_TYPE_MATERIALS: (2.0, 2.0),
            module.MERCHANT_TYPE_RUNE_TRADER: (3.0, 3.0),
            module.MERCHANT_TYPE_RARE_MATERIALS: (4.0, 4.0),
        },
    )
    widget._collect_inventory_items = lambda: [
        _make_item(
            module,
            item_id=1,
            model_id=111,
            name="Chaos Axe",
            is_weapon_like=True,
            requirement=8,
            item_type_id=int(module.ItemType.Axe),
            item_type_name="Axe",
        ),
    ]

    plan = widget._build_plan()

    _expect(not plan.merchant_sell_item_ids, "A lower weapon protection rule should hard-protect the item before a higher explicit sell rule can claim it.")
    _expect(not plan.has_actions, "Hard-protected sell targets should leave the plan non-actionable when no other work remains.")
    _expect(
        any("Hard-protected by Rule 2" in entry.reason for entry in plan.entries if entry.state == module.PLAN_STATE_SKIPPED),
        "Preview entries should explain that the lower protection rule claimed the item during the hard-protection pass.",
    )


def _test_protection_only_rules_hard_claim_before_later_sell_rules(module) -> None:
    shared_coords = {
        module.MERCHANT_TYPE_MERCHANT: (1.0, 1.0),
        module.MERCHANT_TYPE_MATERIALS: (2.0, 2.0),
        module.MERCHANT_TYPE_RUNE_TRADER: (3.0, 3.0),
        module.MERCHANT_TYPE_RARE_MATERIALS: (4.0, 4.0),
    }
    cases = [
        (
            "weapon model protection",
            module.SellRule(
                enabled=True,
                kind=module.SELL_KIND_WEAPONS,
                rarities=_rarity_flags(),
                blacklist_model_ids=[111],
            ),
            module.SellRule(
                enabled=True,
                kind=module.SELL_KIND_WEAPONS,
                rarities=_rarity_flags("gold"),
            ),
            _make_item(
                module,
                item_id=1,
                model_id=111,
                name="Chaos Axe",
                rarity="Gold",
                is_weapon_like=True,
                requirement=9,
                item_type_id=int(module.ItemType.Axe),
                item_type_name="Axe",
            ),
            "Blacklisted model.",
        ),
        (
            "weapon requirement protection",
            module.SellRule(
                enabled=True,
                kind=module.SELL_KIND_WEAPONS,
                rarities=_rarity_flags(),
                protected_weapon_requirement_rules=[
                    module.WeaponRequirementRule(model_id=111, min_requirement=1, max_requirement=9),
                ],
            ),
            module.SellRule(
                enabled=True,
                kind=module.SELL_KIND_WEAPONS,
                rarities=_rarity_flags("gold"),
            ),
            _make_item(
                module,
                item_id=1,
                model_id=111,
                name="Chaos Axe",
                rarity="Gold",
                is_weapon_like=True,
                requirement=9,
                item_type_id=int(module.ItemType.Axe),
                item_type_name="Axe",
            ),
            "Protected by requirement range:",
        ),
        (
            "weapon type protection",
            module.SellRule(
                enabled=True,
                kind=module.SELL_KIND_WEAPONS,
                rarities=_rarity_flags(),
                blacklist_item_type_ids=[int(module.ItemType.Axe)],
            ),
            module.SellRule(
                enabled=True,
                kind=module.SELL_KIND_WEAPONS,
                rarities=_rarity_flags("gold"),
            ),
            _make_item(
                module,
                item_id=1,
                model_id=111,
                name="Chaos Axe",
                rarity="Gold",
                is_weapon_like=True,
                requirement=9,
                item_type_id=int(module.ItemType.Axe),
                item_type_name="Axe",
            ),
            "Blacklisted weapon type: Axe.",
        ),
        (
            "weapon mod protection",
            module.SellRule(
                enabled=True,
                kind=module.SELL_KIND_WEAPONS,
                rarities=_rarity_flags(),
                protected_weapon_mod_identifiers=["sundering"],
            ),
            module.SellRule(
                enabled=True,
                kind=module.SELL_KIND_WEAPONS,
                rarities=_rarity_flags("gold"),
            ),
            _make_item(
                module,
                item_id=1,
                model_id=111,
                name="Chaos Axe",
                rarity="Gold",
                is_weapon_like=True,
                requirement=9,
                item_type_id=int(module.ItemType.Axe),
                item_type_name="Axe",
                weapon_mod_identifiers=["sundering"],
            ),
            "Contains protected weapon mod: sundering.",
        ),
        (
            "armor rune protection",
            module.SellRule(
                enabled=True,
                kind=module.SELL_KIND_ARMOR,
                rarities=_rarity_flags(),
                protected_rune_identifiers=["superior_vigor"],
            ),
            module.SellRule(
                enabled=True,
                kind=module.SELL_KIND_ARMOR,
                rarities=_rarity_flags("gold"),
            ),
            _make_item(
                module,
                item_id=2,
                model_id=222,
                name="Ascalon Chestpiece",
                rarity="Gold",
                is_armor_piece=True,
                rune_identifiers=["superior_vigor"],
            ),
            "Contains protected rune/insignia: superior_vigor.",
        ),
    ]

    for label, protection_rule, sell_rule, item, expected_reason_fragment in cases:
        widget = _make_widget(module)
        widget.sell_rules = [
            module._normalize_sell_rule(protection_rule),
            module._normalize_sell_rule(sell_rule),
        ]
        widget._get_supported_context = lambda coords=shared_coords: (True, "Ready", coords)
        widget._collect_inventory_items = lambda item=item: [item]

        plan = widget._build_plan()

        _expect(
            not plan.merchant_sell_item_ids and not plan.rune_trader_sales,
            f"{label} should hard-protect the item before the later sell rule can claim it.",
        )
        _expect(
            not plan.has_actions,
            f"{label} should leave the plan non-actionable when the protected item is the only candidate.",
        )
        _expect(
            any(
                "Hard-protected by Rule 1" in entry.reason and expected_reason_fragment in entry.reason
                for entry in plan.entries
                if entry.state == module.PLAN_STATE_SKIPPED
            ),
            f"{label} should surface the hard-protection reason in preview output.",
        )


def _test_weapon_mod_identifier_protection_still_matches_all_rolls(module) -> None:
    widget = _make_widget(module)
    identifier = "Forget Me Not"
    rule = module._normalize_sell_rule(
        module.SellRule(
            enabled=True,
            kind=module.SELL_KIND_WEAPONS,
            protected_weapon_mod_identifiers=[identifier],
        )
    )

    for value in (18, 19, 20):
        item = _make_item(
            module,
            item_id=value,
            model_id=111,
            name=f"Insightful Staff +{value}",
            is_weapon_like=True,
            item_type_id=int(module.ItemType.Staff),
            item_type_name="Staff",
            weapon_mod_identifiers=[identifier],
            weapon_mod_matches=[_make_weapon_mod_match(module, identifier, value)],
        )
        protection = widget._get_equippable_hard_protection_reason(item, rule)
        _expect(
            protection is not None and "Contains protected weapon mod:" in protection[1],
            f"Legacy identifier-only protection should protect {identifier} +{value}.",
        )


def _test_weapon_mod_threshold_protection_uses_inclusive_minimum_rolls(module) -> None:
    widget = _make_widget(module)
    identifier = "Forget Me Not"

    def _protects(min_value: int, roll_value: int) -> bool:
        rule = module._normalize_sell_rule(
            module.SellRule(
                enabled=True,
                kind=module.SELL_KIND_WEAPONS,
                protected_weapon_mod_thresholds=[
                    module.WeaponModThresholdRule(identifier=identifier, min_value=min_value),
                ],
            )
        )
        item = _make_item(
            module,
            item_id=roll_value,
            model_id=111,
            name=f"Insightful Staff +{roll_value}",
            is_weapon_like=True,
            item_type_id=int(module.ItemType.Staff),
            item_type_name="Staff",
            weapon_mod_identifiers=[identifier],
            weapon_mod_matches=[_make_weapon_mod_match(module, identifier, roll_value)],
        )
        return widget._get_equippable_hard_protection_reason(item, rule) is not None

    _expect(_protects(20, 20), "A Forget Me Not +20 threshold should protect +20.")
    _expect(not _protects(20, 19), "A Forget Me Not +20 threshold should not protect +19.")
    _expect(_protects(19, 19), "A Forget Me Not +19 threshold should protect +19.")
    _expect(_protects(19, 20), "A Forget Me Not +19 threshold should protect +20.")
    _expect(not _protects(19, 18), "A Forget Me Not +19 threshold should not protect +18.")


def _test_weapon_mod_threshold_protection_handles_small_ranges(module) -> None:
    widget = _make_widget(module)
    identifier = "of the Necromancer"
    rule = module._normalize_sell_rule(
        module.SellRule(
            enabled=True,
            kind=module.SELL_KIND_WEAPONS,
            protected_weapon_mod_thresholds=[
                module.WeaponModThresholdRule(identifier=identifier, min_value=5),
            ],
        )
    )

    def _protection_for(roll_value: int):
        item = _make_item(
            module,
            item_id=roll_value,
            model_id=222,
            name=f"Focus {roll_value}",
            is_weapon_like=True,
            item_type_id=int(module.ItemType.Offhand),
            item_type_name="Offhand",
            weapon_mod_identifiers=[identifier],
            weapon_mod_matches=[_make_weapon_mod_match(module, identifier, roll_value)],
        )
        return widget._get_equippable_hard_protection_reason(item, rule)

    _expect(_protection_for(5) is not None, "An of the Necromancer +5 threshold should protect +5.")
    _expect(_protection_for(4) is None, "An of the Necromancer +5 threshold should not protect +4.")


def _test_weapon_mod_threshold_requires_parsed_roll_value(module) -> None:
    widget = _make_widget(module)
    identifier = "Forget Me Not"
    rule = module._normalize_sell_rule(
        module.SellRule(
            enabled=True,
            kind=module.SELL_KIND_WEAPONS,
            protected_weapon_mod_thresholds=[
                module.WeaponModThresholdRule(identifier=identifier, min_value=19),
            ],
        )
    )
    item = _make_item(
        module,
        item_id=1,
        model_id=111,
        name="Unparsed Staff",
        is_weapon_like=True,
        item_type_id=int(module.ItemType.Staff),
        item_type_name="Staff",
        weapon_mod_identifiers=[identifier],
        weapon_mod_matches=[_make_weapon_mod_match(module, identifier, None)],
    )

    _expect(
        widget._get_equippable_hard_protection_reason(item, rule) is None,
        "Threshold protection should not match when the parsed upgrade value is missing.",
    )


def _test_weapon_mod_legacy_identifier_wins_over_threshold(module) -> None:
    widget = _make_widget(module)
    identifier = "Forget Me Not"
    rule = module._normalize_sell_rule(
        module.SellRule(
            enabled=True,
            kind=module.SELL_KIND_WEAPONS,
            protected_weapon_mod_identifiers=[identifier],
            protected_weapon_mod_thresholds=[
                module.WeaponModThresholdRule(identifier=identifier, min_value=20),
            ],
        )
    )
    item = _make_item(
        module,
        item_id=1,
        model_id=111,
        name="Insightful Staff +18",
        is_weapon_like=True,
        item_type_id=int(module.ItemType.Staff),
        item_type_name="Staff",
        weapon_mod_identifiers=[identifier],
        weapon_mod_matches=[_make_weapon_mod_match(module, identifier, 18)],
    )

    protection = widget._get_equippable_hard_protection_reason(item, rule)
    _expect(
        protection is not None and "Contains protected weapon mod:" in protection[1],
        "Legacy identifier-only protection should win over a threshold rule for the same upgrade.",
    )
    _expect(
        protection is not None and "threshold" not in protection[1].lower(),
        "Mixed legacy and threshold protection should report the legacy all-roll reason.",
    )


def _test_old_weapon_mod_identifier_profile_loads_without_thresholds(module, temp_root: Path) -> None:
    widget = _make_widget(module)
    config_path = temp_root / "old_weapon_mod_identifier_profile.json"
    payload = {
        "version": module.PROFILE_VERSION - 1,
        "sell_rules": [
            {
                "enabled": True,
                "kind": module.SELL_KIND_WEAPONS,
                "protected_weapon_mod_identifiers": ["Forget Me Not"],
            }
        ],
    }
    config_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    widget.config_path = str(config_path)

    widget._load_profile()

    _expect(
        widget.sell_rules[0].protected_weapon_mod_identifiers == ["Forget Me Not"],
        "Old profiles with only protected_weapon_mod_identifiers should preserve the legacy all-roll entries.",
    )
    _expect(
        widget.sell_rules[0].protected_weapon_mod_thresholds == [],
        "Old profiles without threshold rows should load with no threshold protections.",
    )


def _test_weapon_mod_threshold_profile_round_trips(module, temp_root: Path) -> None:
    widget = _make_widget(module)
    config_path = temp_root / "weapon_mod_threshold_profile.json"
    payload = {
        "version": module.PROFILE_VERSION,
        "sell_rules": [
            {
                "enabled": True,
                "kind": module.SELL_KIND_WEAPONS,
                "protected_weapon_mod_thresholds": [
                    {"identifier": "Forget Me Not", "min_value": 19},
                    {"identifier": "of the Necromancer", "min_value": 5},
                ],
            }
        ],
    }
    config_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    widget.config_path = str(config_path)

    widget._load_profile()

    _expect(
        widget.sell_rules[0].protected_weapon_mod_thresholds == [
            module.WeaponModThresholdRule(identifier="Forget Me Not", min_value=19),
            module.WeaponModThresholdRule(identifier="of the Necromancer", min_value=5),
        ],
        "Threshold weapon-mod protections should load as structured threshold rules.",
    )

    saved_payload = json.loads(config_path.read_text(encoding="utf-8"))
    _expect(
        saved_payload["sell_rules"][0]["protected_weapon_mod_thresholds"] == [
            {"identifier": "Forget Me Not", "min_value": 19},
            {"identifier": "of the Necromancer", "min_value": 5},
        ],
        "Threshold weapon-mod protections should save without renaming existing protected-mod keys.",
    )


def _test_weapon_mod_variant_catalog_expands_prefix_suffix_components(module) -> None:
    original_db = _install_weapon_mod_catalog_fixture(module)
    try:
        widget = _make_widget(module)
        widget._load_modifier_catalogs()
    finally:
        module.MOD_DB = original_db

    labels = {str(entry.get("name", "")) for entry in widget.weapon_mod_entries}
    _expect("Cruel (all supported weapons)" in labels, "Weapon-mod catalog should keep broad generic choices.")
    _expect("Cruel Hammer Haft" in labels, "Weapon-mod catalog should include exact prefix component variants.")
    _expect("Barbed Axe Haft" in labels, "Weapon-mod catalog should include valid Barbed axe prefix variant.")
    _expect("Barbed Dagger Tang" in labels, "Weapon-mod catalog should include valid Barbed dagger prefix variant.")
    _expect("Dagger Handle of Defense" in labels, "Weapon-mod catalog should include exact suffix component variants.")
    _expect("Staff Wrapping of Defense" in labels, "Weapon-mod catalog should include staff suffix variants.")
    _expect("Barbed Hammer Haft" not in labels, "Weapon-mod catalog must not invent unsupported component variants.")

    barbed_results = widget._search_identifier_catalog("barbed", widget.weapon_mod_entries)
    barbed_labels = [str(entry.get("name", "")) for entry in barbed_results]
    _expect("Barbed (all supported weapons)" in barbed_labels, "Searching a base modifier should show the broad entry.")
    _expect("Barbed Axe Haft" in barbed_labels, "Searching a base modifier should show valid exact variants.")

    barbed_axe_results = widget._search_identifier_catalog("barbed axe", widget.weapon_mod_entries)
    _expect(
        barbed_axe_results and str(barbed_axe_results[0].get("name", "")) == "Barbed Axe Haft",
        "Specific component searches should rank the exact variant first.",
    )
    _expect(
        all(str(entry.get("name", "")) != "Barbed Hammer Haft" for entry in barbed_axe_results),
        "Specific searches must still exclude invalid generated variants.",
    )


def _test_old_weapon_mod_identifier_protects_all_exact_variants(module) -> None:
    widget = _make_widget(module)
    rule = module._normalize_sell_rule(
        module.SellRule(
            enabled=True,
            kind=module.SELL_KIND_WEAPONS,
            protected_weapon_mod_identifiers=["Cruel"],
        )
    )

    for item_type, component_kind in ((module.ItemType.Hammer, "HammerHaft"), (module.ItemType.Axe, "AxeHaft")):
        item = _make_item(
            module,
            item_id=int(item_type),
            model_id=111,
            name=f"Cruel {item_type.name}",
            is_weapon_like=True,
            item_type_id=int(item_type),
            item_type_name=item_type.name,
            weapon_mod_identifiers=["Cruel"],
            weapon_mod_matches=[
                _make_weapon_mod_match(
                    module,
                    "Cruel",
                    None,
                    target_item_type=item_type.name,
                    component_kind=component_kind,
                    mod_type="Prefix",
                )
            ],
        )
        protection = widget._get_equippable_hard_protection_reason(item, rule)
        _expect(
            protection is not None and "Contains protected weapon mod:" in protection[1],
            f"Legacy Cruel protection should still protect {item_type.name} variants.",
        )


def _test_exact_weapon_mod_variant_protects_only_matching_component(module) -> None:
    widget = _make_widget(module)
    widget.weapon_mod_names["Cruel"] = "Cruel"
    rule = module._normalize_sell_rule(
        module.SellRule(
            enabled=True,
            kind=module.SELL_KIND_WEAPONS,
            protected_weapon_mod_variants=[
                module.WeaponModVariantRule(
                    identifier="Cruel",
                    target_item_type="Hammer",
                    component_kind="HammerHaft",
                )
            ],
        )
    )

    hammer = _make_item(
        module,
        item_id=1,
        model_id=111,
        name="Cruel Hammer",
        is_weapon_like=True,
        item_type_id=int(module.ItemType.Hammer),
        item_type_name="Hammer",
        weapon_mod_identifiers=["Cruel"],
        weapon_mod_matches=[
            _make_weapon_mod_match(
                module,
                "Cruel",
                None,
                target_item_type="Hammer",
                component_kind="HammerHaft",
                mod_type="Prefix",
            )
        ],
    )
    axe = _make_item(
        module,
        item_id=2,
        model_id=111,
        name="Cruel Axe",
        is_weapon_like=True,
        item_type_id=int(module.ItemType.Axe),
        item_type_name="Axe",
        weapon_mod_identifiers=["Cruel"],
        weapon_mod_matches=[
            _make_weapon_mod_match(
                module,
                "Cruel",
                None,
                target_item_type="Axe",
                component_kind="AxeHaft",
                mod_type="Prefix",
            )
        ],
    )
    standalone_hammer_haft = _make_item(
        module,
        item_id=3,
        model_id=111,
        name="Cruel Hammer Haft",
        is_weapon_like=False,
        item_type_id=int(module.ItemType.Rune_Mod),
        item_type_name="Rune_Mod",
        standalone_kind=module.WEAPON_MOD_STANDALONE_KIND,
        weapon_mod_identifiers=["Cruel"],
        weapon_mod_matches=[
            _make_weapon_mod_match(
                module,
                "Cruel",
                None,
                target_item_type="Hammer",
                component_kind="HammerHaft",
                mod_type="Prefix",
            )
        ],
    )

    _expect(widget._get_equippable_hard_protection_reason(hammer, rule) is not None, "Exact Cruel Hammer Haft should protect hammers.")
    _expect(
        widget._get_equippable_hard_protection_reason(standalone_hammer_haft, rule) is not None,
        "Exact Cruel Hammer Haft should protect standalone upgrade components with the matching TargetItemType.",
    )
    _expect(widget._get_equippable_hard_protection_reason(axe, rule) is None, "Exact Cruel Hammer Haft should not protect axes.")


def _test_weapon_mod_variant_threshold_requires_exact_variant_and_roll(module) -> None:
    widget = _make_widget(module)
    widget.weapon_mod_names["of Defense"] = "of Defense"
    rule = module._normalize_sell_rule(
        module.SellRule(
            enabled=True,
            kind=module.SELL_KIND_WEAPONS,
            protected_weapon_mod_variant_thresholds=[
                module.WeaponModVariantThresholdRule(
                    identifier="of Defense",
                    target_item_type="Daggers",
                    component_kind="DaggerHandle",
                    min_value=5,
                )
            ],
        )
    )

    dagger_max = _make_item(
        module,
        item_id=1,
        model_id=111,
        name="Dagger Handle of Defense",
        is_weapon_like=True,
        item_type_id=int(module.ItemType.Daggers),
        item_type_name="Daggers",
        weapon_mod_identifiers=["of Defense"],
        weapon_mod_matches=[
            _make_weapon_mod_match(
                module,
                "of Defense",
                5,
                target_item_type="Daggers",
                component_kind="DaggerHandle",
                mod_type="Suffix",
            )
        ],
    )
    dagger_low = _make_item(
        module,
        item_id=2,
        model_id=111,
        name="Low Dagger Handle of Defense",
        is_weapon_like=True,
        item_type_id=int(module.ItemType.Daggers),
        item_type_name="Daggers",
        weapon_mod_identifiers=["of Defense"],
        weapon_mod_matches=[
            _make_weapon_mod_match(
                module,
                "of Defense",
                4,
                target_item_type="Daggers",
                component_kind="DaggerHandle",
                mod_type="Suffix",
            )
        ],
    )
    staff_max = _make_item(
        module,
        item_id=3,
        model_id=111,
        name="Staff Wrapping of Defense",
        is_weapon_like=True,
        item_type_id=int(module.ItemType.Staff),
        item_type_name="Staff",
        weapon_mod_identifiers=["of Defense"],
        weapon_mod_matches=[
            _make_weapon_mod_match(
                module,
                "of Defense",
                5,
                target_item_type="Staff",
                component_kind="StaffWrapping",
                mod_type="Suffix",
            )
        ],
    )

    _expect(widget._get_equippable_hard_protection_reason(dagger_max, rule) is not None, "Variant threshold should protect matching max dagger suffix.")
    _expect(widget._get_equippable_hard_protection_reason(dagger_low, rule) is None, "Variant threshold should require the configured roll.")
    _expect(widget._get_equippable_hard_protection_reason(staff_max, rule) is None, "Variant threshold should require the exact component variant.")


def _test_weapon_mod_variant_profile_round_trips(module, temp_root: Path) -> None:
    widget = _make_widget(module)
    config_path = temp_root / "weapon_mod_variant_profile.json"
    payload = {
        "version": module.PROFILE_VERSION,
        "sell_rules": [
            {
                "enabled": True,
                "kind": module.SELL_KIND_WEAPONS,
                "protected_weapon_mod_variants": [
                    {"identifier": "Cruel", "target_item_type": "Hammer", "component_kind": "HammerHaft"},
                ],
                "protected_weapon_mod_variant_thresholds": [
                    {
                        "identifier": "of Defense",
                        "target_item_type": "Daggers",
                        "component_kind": "DaggerHandle",
                        "min_value": 5,
                    },
                ],
            }
        ],
    }
    config_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    widget.config_path = str(config_path)

    widget._load_profile()

    _expect(
        widget.sell_rules[0].protected_weapon_mod_variants == [
            module.WeaponModVariantRule(identifier="Cruel", target_item_type="Hammer", component_kind="HammerHaft")
        ],
        "Exact weapon-mod variants should load as structured variant rules.",
    )
    _expect(
        widget.sell_rules[0].protected_weapon_mod_variant_thresholds == [
            module.WeaponModVariantThresholdRule(
                identifier="of Defense",
                target_item_type="Daggers",
                component_kind="DaggerHandle",
                min_value=5,
            )
        ],
        "Exact weapon-mod variant thresholds should load as structured threshold rules.",
    )

    saved_payload = json.loads(config_path.read_text(encoding="utf-8"))
    _expect(
        saved_payload["sell_rules"][0]["protected_weapon_mod_variants"] == [
            {"identifier": "Cruel", "target_item_type": "Hammer", "component_kind": "HammerHaft"}
        ],
        "Exact weapon-mod variants should save using readable profile fields.",
    )
    _expect(
        saved_payload["sell_rules"][0]["protected_weapon_mod_variant_thresholds"] == [
            {
                "identifier": "of Defense",
                "target_item_type": "Daggers",
                "component_kind": "DaggerHandle",
                "min_value": 5,
            }
        ],
        "Exact weapon-mod variant thresholds should save using readable profile fields.",
    )


def _test_merchant_rules_reconstructs_standalone_weapon_mod_variant_context(module) -> None:
    widget = _make_widget(module)
    weapon_mod = _fake_weapon_mod(
        "Cruel",
        "Prefix",
        {
            module.ItemType.Axe: "AxeHaft",
            module.ItemType.Hammer: "HammerHaft",
        },
    )
    original_parse_modifiers = module.parse_modifiers

    def _fake_parse_modifiers(_raw_modifiers, _parse_item_type, _model_id, _db):
        return types.SimpleNamespace(
            runes=[],
            weapon_mods=[
                types.SimpleNamespace(
                    weapon_mod=weapon_mod,
                    value=0,
                    is_maxed=True,
                )
            ],
            is_rune=False,
            requirements=0,
        )

    widget._get_item_modifier_values = lambda _item_id: (
        (module.WEAPON_MOD_TARGET_ITEM_TYPE_MODIFIER_ID, int(module.ItemType.Hammer), 0),
        (9320, 1, 226),
    )
    module.parse_modifiers = _fake_parse_modifiers
    try:
        parsed = widget._get_cached_inventory_modifiers(
            1001,
            111,
            module.ItemType.Rune_Mod,
            module.ItemType.Rune_Mod,
            is_weapon_like=False,
            is_armor_piece=False,
        )
    finally:
        module.parse_modifiers = original_parse_modifiers

    _expect(parsed.standalone_kind == module.WEAPON_MOD_STANDALONE_KIND, "Standalone weapon upgrade components should keep their routing kind.")
    _expect(len(parsed.weapon_mod_matches) == 1, "Standalone weapon upgrade component should keep a parsed weapon-mod match.")
    match = parsed.weapon_mod_matches[0]
    _expect(match.target_item_type == "Hammer", "Merchant Rules should reconstruct standalone TargetItemType from raw modifiers.")
    _expect(match.component_kind == "HammerHaft", "Merchant Rules should reconstruct standalone component kind from item_mods.")
    _expect(match.mod_type == "Prefix", "Merchant Rules should carry the matched weapon-mod type from the parsed match.")


def _test_merchant_rules_reconstructs_equipped_weapon_mod_variant_context(module) -> None:
    widget = _make_widget(module)
    weapon_mod = _fake_weapon_mod(
        "Cruel",
        "Prefix",
        {
            module.ItemType.Axe: "AxeHaft",
            module.ItemType.Hammer: "HammerHaft",
        },
    )
    original_parse_modifiers = module.parse_modifiers

    def _fake_parse_modifiers(_raw_modifiers, _parse_item_type, _model_id, _db):
        return types.SimpleNamespace(
            runes=[],
            weapon_mods=[
                types.SimpleNamespace(
                    weapon_mod=weapon_mod,
                    value=0,
                    is_maxed=True,
                )
            ],
            is_rune=False,
            requirements=0,
        )

    widget._get_item_modifier_values = lambda _item_id: ((9320, 1, 226),)
    module.parse_modifiers = _fake_parse_modifiers
    try:
        parsed = widget._get_cached_inventory_modifiers(
            1001,
            111,
            module.ItemType.Hammer,
            module.ItemType.Hammer,
            is_weapon_like=True,
            is_armor_piece=False,
        )
    finally:
        module.parse_modifiers = original_parse_modifiers

    _expect(len(parsed.weapon_mod_matches) == 1, "Equipped weapon should keep a parsed weapon-mod match.")
    match = parsed.weapon_mod_matches[0]
    _expect(match.target_item_type == "Hammer", "Merchant Rules should reconstruct equipped weapon item type from parse_item_type.")
    _expect(match.component_kind == "HammerHaft", "Merchant Rules should reconstruct equipped component kind from item_mods.")
    _expect(match.mod_type == "Prefix", "Merchant Rules should carry the matched weapon-mod type from the parsed match.")


def _test_global_weapon_requirement_range_is_inclusive_and_excludes_unknown(module) -> None:
    widget = _make_widget(module)
    rule = module._normalize_sell_rule(
        module.SellRule(
            enabled=True,
            kind=module.SELL_KIND_WEAPONS,
            all_weapons_min_requirement=7,
            all_weapons_max_requirement=9,
        )
    )

    for req in (7, 8, 9):
        reason = widget._get_weapon_requirement_hit_reason(
            _make_weapon_item(module, item_id=100 + req, model_id=111, name="Chaos Axe", requirement=req),
            rule,
        )
        _expect(
            "Protected by all-weapons requirement range:" in reason,
            f"Global requirement range 7-9 should protect req {req}.",
        )

    for req in (6, 10, 0):
        reason = widget._get_weapon_requirement_hit_reason(
            _make_weapon_item(module, item_id=200 + req, model_id=111, name="Chaos Axe", requirement=req),
            rule,
        )
        _expect(reason == "", f"Global requirement range 7-9 should not protect req {req}.")


def _test_model_specific_weapon_requirement_range_is_inclusive(module) -> None:
    widget = _make_widget(module)
    rule = module._normalize_sell_rule(
        module.SellRule(
            enabled=True,
            kind=module.SELL_KIND_WEAPONS,
            protected_weapon_requirement_rules=[
                module.WeaponRequirementRule(model_id=111, min_requirement=8, max_requirement=10),
            ],
        )
    )

    for req in (8, 9, 10):
        reason = widget._get_weapon_requirement_hit_reason(
            _make_weapon_item(module, item_id=300 + req, model_id=111, name="Chaos Axe", requirement=req),
            rule,
        )
        _expect(
            "Protected by requirement range:" in reason,
            f"Chaos Axe model-specific range 8-10 should protect req {req}.",
        )

    for req in (7, 11):
        reason = widget._get_weapon_requirement_hit_reason(
            _make_weapon_item(module, item_id=400 + req, model_id=111, name="Chaos Axe", requirement=req),
            rule,
        )
        _expect(reason == "", f"Chaos Axe model-specific range 8-10 should not protect req {req}.")


def _test_model_specific_requirement_range_overrides_global_range(module) -> None:
    widget = _make_widget(module)
    rule = module._normalize_sell_rule(
        module.SellRule(
            enabled=True,
            kind=module.SELL_KIND_WEAPONS,
            all_weapons_min_requirement=7,
            all_weapons_max_requirement=9,
            protected_weapon_requirement_rules=[
                module.WeaponRequirementRule(model_id=111, min_requirement=8, max_requirement=10),
            ],
        )
    )

    chaos_req_7 = widget._get_weapon_requirement_hit_reason(
        _make_weapon_item(module, item_id=501, model_id=111, name="Chaos Axe", requirement=7),
        rule,
    )
    _expect(
        chaos_req_7 == "",
        "A valid Chaos Axe model-specific range should prevent the global range from protecting Chaos Axe req 7.",
    )

    chaos_req_9 = widget._get_weapon_requirement_hit_reason(
        _make_weapon_item(module, item_id=502, model_id=111, name="Chaos Axe", requirement=9),
        rule,
    )
    _expect(
        "Protected by requirement range:" in chaos_req_9,
        "Chaos Axe req 9 should be protected by its model-specific range.",
    )

    fellblade_req_8 = widget._get_weapon_requirement_hit_reason(
        _make_weapon_item(module, item_id=503, model_id=222, name="Fellblade", requirement=8, item_type=module.ItemType.Sword),
        rule,
    )
    _expect(
        "Protected by all-weapons requirement range:" in fellblade_req_8,
        "A different model req 8 should still be protected by the global range.",
    )


def _test_unconditional_protected_model_still_protects_all_requirements(module) -> None:
    widget = _make_widget(module)
    rule = module._normalize_sell_rule(
        module.SellRule(
            enabled=True,
            kind=module.SELL_KIND_WEAPONS,
            blacklist_model_ids=[111],
            all_weapons_min_requirement=7,
            all_weapons_max_requirement=9,
            protected_weapon_requirement_rules=[
                module.WeaponRequirementRule(model_id=111, min_requirement=8, max_requirement=10),
            ],
        )
    )

    for req in (0, 7, 13):
        protection = widget._get_equippable_hard_protection_reason(
            _make_weapon_item(module, item_id=600 + req, model_id=111, name="Chaos Axe", requirement=req),
            rule,
        )
        _expect(
            protection is not None and protection[1] == "Blacklisted model.",
            f"Unconditional protected models should still protect req {req}.",
        )


def _test_perfect_base_raw_modifier_snapshot_extracts_stats(module) -> None:
    raw_modifiers = (
        (module.MODIFIER_IDENTIFIER_ATTRIBUTE_REQUIREMENT << 4, 20, 8),
        (module.MODIFIER_IDENTIFIER_DAMAGE << 4, 22, 15),
        (module.MODIFIER_IDENTIFIER_ENERGY << 4, 10, 0),
        (module.MODIFIER_IDENTIFIER_ARMOR1 << 4, 16, 0),
    )

    extracted = module._extract_base_stats_from_raw_modifiers(raw_modifiers)

    _expect(
        extracted == (8, 20, "", 15, 22, 10, 16),
        "Raw modifier snapshots should expose requirement, damage, energy, and armor for perfect-base matching.",
    )


def _test_all_weapons_perfect_only_requirement_range(module) -> None:
    widget = _make_widget(module)
    rule = module._normalize_sell_rule(
        module.SellRule(
            enabled=True,
            kind=module.SELL_KIND_WEAPONS,
            all_weapons_min_requirement=8,
            all_weapons_max_requirement=9,
            all_weapons_perfect_stats_only=True,
        )
    )

    perfect_q8 = widget._get_weapon_requirement_hit_reason(
        _make_weapon_item(
            module,
            item_id=650,
            model_id=111,
            name="Iron Sword",
            requirement=8,
            item_type=module.ItemType.Sword,
            requirement_attribute_name="Swordsmanship",
            damage_min=15,
            damage_max=22,
        ),
        rule,
    )
    _expect(
        perfect_q8 == "Protected by all-weapons perfect-base range: Sword 15-22, req 8 Swordsmanship.",
        "All-weapons perfect-only range should protect a q8 perfect sword.",
    )

    nonperfect_q8 = widget._get_weapon_requirement_hit_reason(
        _make_weapon_item(
            module,
            item_id=651,
            model_id=111,
            name="Iron Sword",
            requirement=8,
            item_type=module.ItemType.Sword,
            requirement_attribute_name="Swordsmanship",
            damage_min=14,
            damage_max=22,
        ),
        rule,
    )
    _expect(nonperfect_q8 == "", "All-weapons perfect-only range should reject a q8 non-perfect sword.")

    perfect_q10 = widget._get_weapon_requirement_hit_reason(
        _make_weapon_item(
            module,
            item_id=652,
            model_id=111,
            name="Iron Sword",
            requirement=10,
            item_type=module.ItemType.Sword,
            requirement_attribute_name="Swordsmanship",
            damage_min=15,
            damage_max=22,
        ),
        rule,
    )
    _expect(perfect_q10 == "", "All-weapons perfect-only range should reject a q10 perfect sword when range is 8-9.")


def _test_model_specific_perfect_only_requirement_range(module) -> None:
    widget = _make_widget(module)
    rule = module._normalize_sell_rule(
        module.SellRule(
            enabled=True,
            kind=module.SELL_KIND_WEAPONS,
            all_weapons_min_requirement=8,
            all_weapons_max_requirement=9,
            all_weapons_perfect_stats_only=True,
            protected_weapon_requirement_rules=[
                module.WeaponRequirementRule(model_id=333, min_requirement=8, max_requirement=12, perfect_stats_only=True),
            ],
        )
    )

    model_perfect_q10 = widget._get_weapon_requirement_hit_reason(
        _make_weapon_item(
            module,
            item_id=660,
            model_id=333,
            name="Storm Bow",
            requirement=10,
            item_type=module.ItemType.Bow,
            requirement_attribute_name="Marksmanship",
            damage_min=15,
            damage_max=28,
        ),
        rule,
    )
    _expect(
        model_perfect_q10 == "Protected by model perfect-base range: Storm Bow 15-28, req 10 Marksmanship.",
        "Model-specific perfect-only range should protect a selected model in its broader range.",
    )

    other_model_q10 = widget._get_weapon_requirement_hit_reason(
        _make_weapon_item(
            module,
            item_id=661,
            model_id=444,
            name="Shadow Bow",
            requirement=10,
            item_type=module.ItemType.Bow,
            requirement_attribute_name="Marksmanship",
            damage_min=15,
            damage_max=28,
        ),
        rule,
    )
    _expect(other_model_q10 == "", "A different q10 model should not be protected by the narrower all-weapons range.")

    model_nonperfect_q10 = widget._get_weapon_requirement_hit_reason(
        _make_weapon_item(
            module,
            item_id=662,
            model_id=333,
            name="Storm Bow",
            requirement=10,
            item_type=module.ItemType.Bow,
            requirement_attribute_name="Marksmanship",
            damage_min=14,
            damage_max=28,
        ),
        rule,
    )
    _expect(model_nonperfect_q10 == "", "Model-specific perfect-only range should reject the selected model when stats are low.")


def _test_perfect_base_requires_staff_focus_and_shield_stats(module) -> None:
    widget = _make_widget(module)
    rule = module._normalize_sell_rule(
        module.SellRule(
            enabled=True,
            kind=module.SELL_KIND_WEAPONS,
            all_weapons_min_requirement=8,
            all_weapons_max_requirement=9,
            all_weapons_perfect_stats_only=True,
        )
    )

    staff_perfect = widget._get_weapon_requirement_hit_reason(
        _make_weapon_item(
            module,
            item_id=670,
            model_id=6700,
            name="Divine Staff",
            requirement=9,
            item_type=module.ItemType.Staff,
            requirement_attribute_name="Divine Favor",
            damage_min=11,
            damage_max=22,
            energy=10,
        ),
        rule,
    )
    _expect(
        staff_perfect == "Protected by all-weapons perfect-base range: Staff 11-22, Energy +10, req 9 Divine Favor.",
        "Perfect staff protection should require both 11-22 damage and Energy +10.",
    )

    staff_missing_energy = widget._get_weapon_requirement_hit_reason(
        _make_weapon_item(
            module,
            item_id=671,
            model_id=6701,
            name="Divine Staff",
            requirement=9,
            item_type=module.ItemType.Staff,
            requirement_attribute_name="Divine Favor",
            damage_min=11,
            damage_max=22,
            energy=9,
        ),
        rule,
    )
    _expect(staff_missing_energy == "", "Perfect staff protection should reject 11-22 staves without Energy +10.")

    focus_perfect = widget._get_weapon_requirement_hit_reason(
        _make_weapon_item(
            module,
            item_id=672,
            model_id=6702,
            name="Jeweled Focus",
            requirement=9,
            item_type=module.ItemType.Offhand,
            requirement_attribute_name="Domination Magic",
            energy=12,
        ),
        rule,
    )
    _expect(
        focus_perfect == "Protected by all-weapons perfect-base range: Focus Energy +12, req 9 Domination Magic.",
        "Perfect focus protection should require Energy +12.",
    )

    focus_low_energy = widget._get_weapon_requirement_hit_reason(
        _make_weapon_item(
            module,
            item_id=673,
            model_id=6703,
            name="Jeweled Focus",
            requirement=9,
            item_type=module.ItemType.Offhand,
            requirement_attribute_name="Domination Magic",
            energy=11,
        ),
        rule,
    )
    _expect(focus_low_energy == "", "Perfect focus protection should reject Energy +11.")

    shield_perfect = widget._get_weapon_requirement_hit_reason(
        _make_weapon_item(
            module,
            item_id=674,
            model_id=6704,
            name="Tower Shield",
            requirement=9,
            item_type=module.ItemType.Shield,
            requirement_attribute_name="Tactics",
            armor=16,
        ),
        rule,
    )
    _expect(
        shield_perfect == "Protected by all-weapons perfect-base range: Shield Armor 16, req 9 Tactics.",
        "Perfect shield protection should require Armor 16.",
    )

    shield_low_armor = widget._get_weapon_requirement_hit_reason(
        _make_weapon_item(
            module,
            item_id=675,
            model_id=6705,
            name="Tower Shield",
            requirement=9,
            item_type=module.ItemType.Shield,
            requirement_attribute_name="Tactics",
            armor=15,
        ),
        rule,
    )
    _expect(shield_low_armor == "", "Perfect shield protection should reject Armor 15.")


def _test_perfect_only_unidentified_missing_stats_fail_closed(module) -> None:
    widget = _make_widget(module)
    perfect_rule = module._normalize_sell_rule(
        module.SellRule(
            enabled=True,
            kind=module.SELL_KIND_WEAPONS,
            all_weapons_min_requirement=8,
            all_weapons_max_requirement=9,
            all_weapons_perfect_stats_only=True,
            skip_unidentified=False,
        )
    )
    normal_rule = module._normalize_sell_rule(
        module.SellRule(
            enabled=True,
            kind=module.SELL_KIND_WEAPONS,
            all_weapons_min_requirement=8,
            all_weapons_max_requirement=9,
            skip_unidentified=False,
        )
    )

    unidentified_unknown = _make_weapon_item(
        module,
        item_id=680,
        model_id=6800,
        name="Unidentified Sword",
        requirement=0,
        item_type=module.ItemType.Sword,
        identified=False,
        requirement_attribute_id=0,
        requirement_attribute_name="",
        damage_min=0,
        damage_max=0,
    )
    reason = widget._get_weapon_requirement_hit_reason(unidentified_unknown, perfect_rule)
    _expect(
        reason == "Protected until identified: perfect-base stats unavailable.",
        "Perfect-only rules should fail closed for unidentified items when req/base stats are unavailable.",
    )
    protection = widget._get_equippable_hard_protection_reason(unidentified_unknown, perfect_rule)
    _expect(
        protection is not None and protection[1] == "Protected until identified: perfect-base stats unavailable.",
        "Perfect-only unidentified fail-closed protection should flow through hard protection.",
    )

    normal_reason = widget._get_weapon_requirement_hit_reason(unidentified_unknown, normal_rule)
    _expect(normal_reason == "", "Normal requirement protection should keep unknown req behavior unchanged.")

    unidentified_q10_unknown_stats = _make_weapon_item(
        module,
        item_id=681,
        model_id=6801,
        name="Unidentified Sword",
        requirement=10,
        item_type=module.ItemType.Sword,
        identified=False,
        requirement_attribute_name="Swordsmanship",
        damage_min=0,
        damage_max=0,
    )
    q10_reason = widget._get_weapon_requirement_hit_reason(unidentified_q10_unknown_stats, perfect_rule)
    _expect(q10_reason == "", "A known req outside the configured range should not fail closed just because stats are unavailable.")


def _test_weapon_requirement_ranges_normalize_swapped_and_zero_endpoints(module, temp_root: Path) -> None:
    widget = _make_widget(module)
    config_path = temp_root / "requirement_range_normalization_profile.json"
    widget.config_path = str(config_path)
    widget.sell_rules = [
        module._normalize_sell_rule(
            module.SellRule(
                enabled=True,
                kind=module.SELL_KIND_WEAPONS,
                all_weapons_min_requirement=10,
                all_weapons_max_requirement=8,
                protected_weapon_requirement_rules=[
                    module.WeaponRequirementRule(model_id=111, min_requirement=10, max_requirement=8),
                    module.WeaponRequirementRule(model_id=222, min_requirement=8, max_requirement=0),
                ],
            )
        )
    ]

    rule = widget.sell_rules[0]
    _expect(
        (rule.all_weapons_min_requirement, rule.all_weapons_max_requirement) == (8, 10),
        "Global requirement ranges should auto-swap low/high endpoints.",
    )
    _expect(
        (rule.protected_weapon_requirement_rules[0].min_requirement, rule.protected_weapon_requirement_rules[0].max_requirement) == (8, 10),
        "Model-specific requirement ranges should auto-swap low/high endpoints.",
    )
    _expect(
        (rule.protected_weapon_requirement_rules[1].min_requirement, rule.protected_weapon_requirement_rules[1].max_requirement) == (8, 0),
        "A zero endpoint should remain disabled without being swapped into a nonzero range.",
    )

    global_seven_five = module._normalize_sell_rule(
        module.SellRule(
            enabled=True,
            kind=module.SELL_KIND_WEAPONS,
            all_weapons_min_requirement=7,
            all_weapons_max_requirement=5,
        )
    )
    _expect(
        (global_seven_five.all_weapons_min_requirement, global_seven_five.all_weapons_max_requirement) == (5, 7),
        "Global range low=7 high=5 should normalize to low=5 high=7.",
    )
    _expect(
        (global_seven_five.all_weapons_min_requirement, global_seven_five.all_weapons_max_requirement) != (5, 5),
        "Global swapped ranges must not collapse both endpoints to the edited high value.",
    )
    _expect(
        (rule.protected_weapon_requirement_rules[0].min_requirement, rule.protected_weapon_requirement_rules[0].max_requirement) != (10, 10),
        "Model-specific swapped ranges must not collapse both endpoints to the edited low value.",
    )
    _expect(
        module._normalize_weapon_requirement_range(8, 0) == (8, 0),
        "Endpoint 0 should disable the range without swapping endpoint order.",
    )
    _expect(
        module._should_defer_weapon_requirement_range_commit(7, 5, input_active=True),
        "Reversed nonzero ranges should defer UI commits while an endpoint input is active.",
    )
    _expect(
        not module._should_defer_weapon_requirement_range_commit(7, 5, input_active=False),
        "Reversed nonzero ranges should commit once endpoint editing is no longer active.",
    )
    _expect(
        not module._should_defer_weapon_requirement_range_commit(8, 0, input_active=True),
        "Endpoint 0 should not be treated as an active reversed range in the UI commit path.",
    )

    disabled_model_reason = widget._get_weapon_requirement_hit_reason(
        _make_weapon_item(module, item_id=701, model_id=222, name="Fellblade", requirement=8, item_type=module.ItemType.Sword),
        rule,
    )
    _expect(
        "Protected by all-weapons requirement range:" in disabled_model_reason,
        "Inactive model-specific ranges should not block the global range for that model.",
    )

    endpoint_zero_rule = module._normalize_sell_rule(
        module.SellRule(
            enabled=True,
            kind=module.SELL_KIND_WEAPONS,
            all_weapons_min_requirement=0,
            all_weapons_max_requirement=9,
            protected_weapon_requirement_rules=[
                module.WeaponRequirementRule(model_id=111, min_requirement=0, max_requirement=10),
            ],
        )
    )
    _expect(
        widget._get_weapon_requirement_hit_reason(
            _make_weapon_item(module, item_id=702, model_id=111, name="Chaos Axe", requirement=8),
            endpoint_zero_rule,
        )
        == "",
        "Endpoint 0 should disable global and model-specific requirement ranges.",
    )

    _expect(widget._save_profile(), "Saving swapped requirement ranges should succeed.")
    saved_payload = json.loads(config_path.read_text(encoding="utf-8"))
    saved_rule = saved_payload["sell_rules"][0]
    _expect(
        (saved_rule["all_weapons_min_requirement"], saved_rule["all_weapons_max_requirement"]) == (8, 10),
        "Saved global requirement ranges should persist corrected endpoint order.",
    )
    _expect(
        (
            saved_rule["protected_weapon_requirement_rules"][0]["min_requirement"],
            saved_rule["protected_weapon_requirement_rules"][0]["max_requirement"],
        )
        == (8, 10),
        "Saved model-specific requirement ranges should persist corrected endpoint order.",
    )


def _test_legacy_requirement_thresholds_migrate_to_ranges(module, temp_root: Path) -> None:
    widget = _make_widget(module)
    config_path = temp_root / "legacy_requirement_threshold_profile.json"
    payload = {
        "version": module.PROFILE_VERSION - 1,
        "sell_rules": [
            {
                "enabled": True,
                "kind": module.SELL_KIND_WEAPONS,
                "all_weapons_max_requirement": 8,
                "protected_weapon_requirement_rules": [
                    {"model_id": 111, "max_requirement": 10},
                ],
            }
        ],
    }
    config_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    widget.config_path = str(config_path)

    widget._load_profile()

    rule = widget.sell_rules[0]
    _expect(
        (rule.all_weapons_min_requirement, rule.all_weapons_max_requirement) == (1, 8),
        "Old global max-only configs should load as range 1-old max.",
    )
    _expect(
        (
            rule.protected_weapon_requirement_rules[0].min_requirement,
            rule.protected_weapon_requirement_rules[0].max_requirement,
        )
        == (1, 10),
        "Old model-specific max-only configs should load as range 1-old max.",
    )

    saved_payload = json.loads(config_path.read_text(encoding="utf-8"))
    saved_rule = saved_payload["sell_rules"][0]
    _expect(
        (saved_rule["all_weapons_min_requirement"], saved_rule["all_weapons_max_requirement"]) == (1, 8),
        "Migrated global requirement ranges should save the new low endpoint.",
    )
    _expect(
        (
            saved_rule["protected_weapon_requirement_rules"][0]["min_requirement"],
            saved_rule["protected_weapon_requirement_rules"][0]["max_requirement"],
        )
        == (1, 10),
        "Migrated model-specific requirement ranges should save the new low endpoint.",
    )


def _test_keep_count_claims_items_before_later_sell_rules(module) -> None:
    widget = _make_widget(module)
    widget.sell_rules = [
        module._normalize_sell_rule(
            module.SellRule(
                enabled=True,
                kind=module.SELL_KIND_EXPLICIT_MODELS,
                model_ids=[111],
                keep_count=1,
            )
        ),
        module._normalize_sell_rule(
            module.SellRule(
                enabled=True,
                kind=module.SELL_KIND_WEAPONS,
            )
        ),
    ]
    widget._get_supported_context = lambda: (
        True,
        "Ready",
        {
            module.MERCHANT_TYPE_MERCHANT: (1.0, 1.0),
            module.MERCHANT_TYPE_MATERIALS: (2.0, 2.0),
            module.MERCHANT_TYPE_RUNE_TRADER: (3.0, 3.0),
            module.MERCHANT_TYPE_RARE_MATERIALS: (4.0, 4.0),
        },
    )
    widget._collect_inventory_items = lambda: [
        _make_item(
            module,
            item_id=1,
            model_id=111,
            name="Iron Sword",
            is_weapon_like=True,
            item_type_id=int(module.ItemType.Sword),
            item_type_name="Sword",
        ),
    ]

    plan = widget._build_plan()

    _expect(not plan.merchant_sell_item_ids, "Items kept by a higher-priority explicit rule should no longer fall through to later sell rules.")
    _expect(not plan.has_actions, "A keep-only match should not leave behind later actionable sells for the same claimed item.")
    _expect(
        any("Kept by Rule 1" in entry.reason for entry in plan.entries if entry.state == module.PLAN_STATE_SKIPPED),
        "Preview entries should identify when a higher rule claimed an item to satisfy keep count.",
    )


def _test_common_material_rule_claims_stack_before_later_explicit_sell(module) -> None:
    widget = _make_widget(module)
    widget.sell_rules = [
        module._normalize_sell_rule(
            module.SellRule(
                enabled=True,
                kind=module.SELL_KIND_COMMON_MATERIALS,
                model_ids=[222],
                keep_count=0,
            )
        ),
        module._normalize_sell_rule(
            module.SellRule(
                enabled=True,
                kind=module.SELL_KIND_EXPLICIT_MODELS,
                model_ids=[222],
                keep_count=0,
            )
        ),
    ]
    widget._get_supported_context = lambda: (
        True,
        "Ready",
        {
            module.MERCHANT_TYPE_MERCHANT: (1.0, 1.0),
            module.MERCHANT_TYPE_MATERIALS: (2.0, 2.0),
            module.MERCHANT_TYPE_RUNE_TRADER: (3.0, 3.0),
            module.MERCHANT_TYPE_RARE_MATERIALS: (4.0, 4.0),
        },
    )
    widget._collect_inventory_items = lambda: [
        _make_item(
            module,
            item_id=2,
            model_id=222,
            name="Bone",
            quantity=50,
            is_material=True,
        ),
    ]

    plan = widget._build_plan()

    _expect(len(plan.material_sales) == 1, "The first matching material rule should still schedule trader sales for the stack it claims.")
    _expect(plan.material_sales[0].quantity_to_sell == 50, "The material rule should keep its full-batch sell quantity once it claims the stack.")
    _expect(not plan.merchant_sell_item_ids, "Later explicit-item rules should not also schedule the same claimed material stack for merchant sale.")
    _expect(plan.has_actions, "Claimed material sales should remain actionable merchant work.")


def _test_sell_material_targets_keep_counts_apply_per_model(module) -> None:
    widget = _make_widget(module)
    widget.catalog_by_model_id[921] = {"model_id": 921, "name": "Wood Plank", "material_type": "common"}
    widget.catalog_by_model_id[925] = {"model_id": 925, "name": "Iron Ingot", "material_type": "common"}
    widget.sell_rules = [
        module._normalize_sell_rule(
            module.SellRule(
                enabled=True,
                kind=module.SELL_KIND_COMMON_MATERIALS,
                whitelist_targets=[
                    module.WhitelistTarget(model_id=921, keep_count=25),
                    module.WhitelistTarget(model_id=925, keep_count=250),
                ],
            )
        )
    ]
    widget._get_supported_context = lambda: (
        True,
        "Ready",
        {
            module.MERCHANT_TYPE_MERCHANT: (1.0, 1.0),
            module.MERCHANT_TYPE_MATERIALS: (2.0, 2.0),
            module.MERCHANT_TYPE_RUNE_TRADER: (3.0, 3.0),
            module.MERCHANT_TYPE_RARE_MATERIALS: (4.0, 4.0),
        },
    )
    widget._collect_inventory_items = lambda: [
        _make_item(module, item_id=60, model_id=921, name="Wood Plank", quantity=40, is_material=True),
        _make_item(module, item_id=61, model_id=925, name="Iron Ingot", quantity=300, is_material=True),
    ]

    plan = widget._build_plan()

    sales_by_model = {
        sale.model_id: sale.quantity_to_sell
        for sale in plan.material_sales
    }
    _expect(sales_by_model == {921: 10, 925: 50}, "Per-target material keep counts should be planned independently inside one sell rule.")
    _expect(
        any(entry.state == module.PLAN_STATE_SKIPPED and entry.label == "Wood Plank" and entry.quantity == 30 for entry in plan.entries),
        "Preview should keep the per-target remaining quantity for the first material model.",
    )
    _expect(
        any(entry.state == module.PLAN_STATE_SKIPPED and entry.label == "Iron Ingot" and entry.quantity == 250 for entry in plan.entries),
        "Preview should keep the per-target remaining quantity for the second material model.",
    )


def _test_sell_material_keep_zero_routes_common_leftovers_to_merchant(module) -> None:
    widget = _make_widget(module)
    widget.catalog_by_model_id[921] = {"model_id": 921, "name": "Wood Plank", "material_type": "common"}
    widget.sell_rules = [
        module._normalize_sell_rule(
            module.SellRule(
                enabled=True,
                kind=module.SELL_KIND_COMMON_MATERIALS,
                whitelist_targets=[
                    module.WhitelistTarget(model_id=921, keep_count=0),
                ],
            )
        )
    ]
    widget._get_supported_context = lambda: (
        True,
        "Ready",
        {
            module.MERCHANT_TYPE_MERCHANT: (1.0, 1.0),
            module.MERCHANT_TYPE_MATERIALS: (2.0, 2.0),
            module.MERCHANT_TYPE_RUNE_TRADER: (3.0, 3.0),
            module.MERCHANT_TYPE_RARE_MATERIALS: (4.0, 4.0),
        },
    )
    widget._collect_inventory_items = lambda: [
        _make_item(module, item_id=62, model_id=921, name="Wood Plank", quantity=11, is_material=True),
    ]

    plan = widget._build_plan()

    _expect(len(plan.material_sales) == 1, "Common-material keep_count=0 should still sell the full trader batch first.")
    _expect(plan.material_sales[0].item_id == 62 and plan.material_sales[0].quantity_to_sell == 10, "The planner should send 10 Wood to the Material Trader first.")
    _expect(plan.merchant_sell_item_ids == [62], "The leftover common-material stack should then be queued for Merchant sale when keep_count is zero.")
    _expect(
        any(
            entry.state == module.PLAN_STATE_WILL_EXECUTE
            and entry.merchant_type == module.MERCHANT_TYPE_MATERIALS
            and entry.label == "Wood Plank"
            and entry.quantity == 10
            for entry in plan.entries
        ),
        "Preview should show the trader batch sale for the common material.",
    )
    _expect(
        any(
            entry.state == module.PLAN_STATE_WILL_EXECUTE
            and entry.merchant_type == module.MERCHANT_TYPE_MERCHANT
            and entry.label == "Wood Plank"
            and entry.quantity == 1
            for entry in plan.entries
        ),
        "Preview should show the leftover common-material quantity going to the Merchant when keep_count is zero.",
    )
    _expect(
        not any(
            entry.state == module.PLAN_STATE_SKIPPED
            and entry.label == "Wood Plank"
            and entry.quantity == 1
            and "remain after selling full trader batches" in entry.reason
            for entry in plan.entries
        ),
        "The keep-zero leftover should no longer be previewed as a kept remainder.",
    )


def _test_execute_now_reuses_common_material_keep_zero_leftover_plan(module) -> None:
    widget = _make_widget(module)
    widget.catalog_by_model_id[921] = {"model_id": 921, "name": "Wood Plank", "material_type": "common"}
    widget.sell_rules = [
        module._normalize_sell_rule(
            module.SellRule(
                enabled=True,
                kind=module.SELL_KIND_COMMON_MATERIALS,
                whitelist_targets=[
                    module.WhitelistTarget(model_id=921, keep_count=0),
                ],
            )
        )
    ]
    widget._get_supported_context = lambda: (
        True,
        "Ready",
        {
            module.MERCHANT_TYPE_MERCHANT: (1.0, 1.0),
            module.MERCHANT_TYPE_MATERIALS: (2.0, 2.0),
            module.MERCHANT_TYPE_RUNE_TRADER: (3.0, 3.0),
            module.MERCHANT_TYPE_RARE_MATERIALS: (4.0, 4.0),
        },
    )
    widget._collect_inventory_items = lambda: [
        _make_item(module, item_id=62, model_id=921, name="Wood Plank", quantity=11, is_material=True),
    ]

    preview_plan = widget._build_plan()
    preview_material_sales = [
        (sale.item_id, sale.model_id, sale.quantity_to_sell, sale.batch_size, sale.merchant_type)
        for sale in preview_plan.material_sales
    ]
    preview_sell_ids = list(preview_plan.merchant_sell_item_ids)

    captured_material_sales: list[tuple[int, int, int, int, str]] = []
    captured_merchant_sell_ids: list[int] = []

    def _capture_material_sales(_coords, sales, *, phase_label="Material sales"):
        captured_material_sales.extend(
            (
                sale.item_id,
                sale.model_id,
                sale.quantity_to_sell,
                sale.batch_size,
                sale.merchant_type,
            )
            for sale in sales
        )
        if False:
            yield None
        return module.ExecutionPhaseOutcome(
            label=phase_label,
            measure_label="trades",
            attempted=sum(max(0, int(sale.batches_to_sell)) for sale in sales),
            completed=sum(max(0, int(sale.batches_to_sell)) for sale in sales),
        )

    def _capture_merchant_sell(_coords, item_ids):
        captured_merchant_sell_ids.extend(int(item_id) for item_id in item_ids)
        if False:
            yield None
        return module.ExecutionPhaseOutcome(label="Merchant sells", measure_label="items", attempted=len(item_ids), completed=len(item_ids))

    widget._sell_planned_materials = _capture_material_sales
    widget._execute_merchant_sell_phase = _capture_merchant_sell

    _drain_generator_return(widget._execute_now())

    _expect(captured_material_sales == preview_material_sales, "Execute should rebuild and reuse the same material-trader batch plan that preview produced.")
    _expect(captured_merchant_sell_ids == preview_sell_ids, "Execute should rebuild and reuse the same Merchant leftover plan that preview produced.")


def _test_sell_explicit_targets_keep_counts_apply_per_model(module) -> None:
    widget = _make_widget(module)
    widget.catalog_by_model_id[555] = {"model_id": 555, "name": "Identification Kit"}
    widget.sell_rules = [
        module._normalize_sell_rule(
            module.SellRule(
                enabled=True,
                kind=module.SELL_KIND_EXPLICIT_MODELS,
                whitelist_targets=[
                    module.WhitelistTarget(model_id=111, keep_count=1),
                    module.WhitelistTarget(model_id=555, keep_count=0),
                ],
            )
        )
    ]
    widget._get_supported_context = lambda: (
        True,
        "Ready",
        {
            module.MERCHANT_TYPE_MERCHANT: (1.0, 1.0),
            module.MERCHANT_TYPE_MATERIALS: (2.0, 2.0),
            module.MERCHANT_TYPE_RUNE_TRADER: (3.0, 3.0),
            module.MERCHANT_TYPE_RARE_MATERIALS: (4.0, 4.0),
        },
    )
    widget._collect_inventory_items = lambda: [
        _make_item(module, item_id=70, model_id=111, name="Iron Sword", quantity=1),
        _make_item(module, item_id=71, model_id=111, name="Iron Sword", quantity=1),
        _make_item(module, item_id=72, model_id=555, name="Identification Kit", quantity=1),
    ]

    plan = widget._build_plan()
    sell_item_ids = set(plan.merchant_sell_item_ids)

    _expect(72 in sell_item_ids, "Per-target explicit sell keep counts should still sell models with a zero keep value.")
    _expect(len(sell_item_ids & {70, 71}) == 1, "Per-target explicit sell keep counts should keep one matching item for only the targeted model.")
    _expect(
        any(entry.state == module.PLAN_STATE_SKIPPED and entry.label == "Iron Sword" and "keep count 1" in entry.reason.lower() for entry in plan.entries),
        "Preview should explain which explicit-model item was kept for its own target row.",
    )


def _test_destroy_material_keep_count_plans_partial_stack(module) -> None:
    widget = _make_widget(module)
    widget.catalog_by_model_id[333] = {"model_id": 333, "name": "Wood"}
    widget.destroy_rules = [
        module._normalize_destroy_rule(
            module.DestroyRule(
                enabled=True,
                kind=module.DESTROY_KIND_MATERIALS,
                model_ids=[333],
                keep_count=4,
            )
        )
    ]
    widget._get_supported_context = lambda: (
        True,
        "Ready",
        {
            module.MERCHANT_TYPE_MERCHANT: (1.0, 1.0),
            module.MERCHANT_TYPE_MATERIALS: (2.0, 2.0),
            module.MERCHANT_TYPE_RUNE_TRADER: (3.0, 3.0),
            module.MERCHANT_TYPE_RARE_MATERIALS: (4.0, 4.0),
        },
    )
    widget._collect_inventory_items = lambda: [
        _make_item(
            module,
            item_id=30,
            model_id=333,
            name="Wood",
            quantity=20,
            is_material=True,
        ),
    ]
    original_inventory = getattr(module.GLOBAL_CACHE, "Inventory", None)
    try:
        module.GLOBAL_CACHE.Inventory = types.SimpleNamespace(
            FindItemBagAndSlot=lambda item_id: (1, 0) if int(item_id) == 30 else (None, None),
            GetBagSize=lambda bag_id: 2 if int(bag_id) == 1 else 0,
        )

        plan = widget._build_plan()

        _expect(len(plan.destroy_actions) == 1, "Stackable destroy rules should produce one planned destroy action for the matched stack.")
        action = plan.destroy_actions[0]
        _expect(action.item_id == 30, "The planned destroy action should target the matched material stack.")
        _expect(action.quantity_to_destroy == 16, "Destroy keep_count should reserve only the requested quantity from a stackable material stack.")
        _expect(action.keep_quantity == 4, "Destroy keep_count should keep the requested quantity on the source stack before destroying the remainder.")
        _expect(action.requires_split, "Partial stack destroys should mark that a stack split is required.")
        _expect(plan.has_actions, "A partial stack destroy should remain actionable when a safe split slot exists.")
        _expect(
            any(entry.state == module.PLAN_STATE_WILL_EXECUTE and entry.label == "Wood" and entry.quantity == 16 for entry in plan.entries),
            "Preview should show the destroy quantity for stackable partial destroys.",
        )
        _expect(
            any(entry.state == module.PLAN_STATE_SKIPPED and entry.label == "Wood" and entry.quantity == 4 for entry in plan.entries),
            "Preview should show the kept remainder for stackable partial destroys.",
        )
    finally:
        module.GLOBAL_CACHE.Inventory = original_inventory


def _test_destroy_material_keep_count_blocks_without_split_slot(module) -> None:
    widget = _make_widget(module)
    widget.catalog_by_model_id[333] = {"model_id": 333, "name": "Wood"}
    widget.destroy_rules = [
        module._normalize_destroy_rule(
            module.DestroyRule(
                enabled=True,
                kind=module.DESTROY_KIND_MATERIALS,
                model_ids=[333],
                keep_count=4,
            )
        )
    ]
    widget._get_supported_context = lambda: (
        True,
        "Ready",
        {
            module.MERCHANT_TYPE_MERCHANT: (1.0, 1.0),
            module.MERCHANT_TYPE_MATERIALS: (2.0, 2.0),
            module.MERCHANT_TYPE_RUNE_TRADER: (3.0, 3.0),
            module.MERCHANT_TYPE_RARE_MATERIALS: (4.0, 4.0),
        },
    )
    widget._collect_inventory_items = lambda: [
        _make_item(
            module,
            item_id=31,
            model_id=333,
            name="Wood",
            quantity=20,
            is_material=True,
        ),
    ]
    original_inventory = getattr(module.GLOBAL_CACHE, "Inventory", None)
    try:
        module.GLOBAL_CACHE.Inventory = types.SimpleNamespace(
            FindItemBagAndSlot=lambda item_id: (1, 0) if int(item_id) == 31 else (None, None),
            GetBagSize=lambda bag_id: 1 if int(bag_id) == 1 else 0,
        )

        plan = widget._build_plan()

        _expect(not plan.destroy_actions, "Destroy planning should not fake a partial stack destroy when no safe split slot exists.")
        _expect(not plan.has_actions, "A blocked partial stack destroy should leave the plan non-actionable.")
        _expect(
            any(
                entry.state == module.PLAN_STATE_SKIPPED
                and "splitting a stack" in entry.reason.lower()
                and "empty inventory slot" in entry.reason.lower()
                for entry in plan.entries
            ),
            "Preview should explain that the partial destroy is blocked because no safe split slot exists.",
        )
    finally:
        module.GLOBAL_CACHE.Inventory = original_inventory


def _test_nonstackable_destroy_keep_count_stays_whole_item(module) -> None:
    widget = _make_widget(module)
    widget.destroy_rules = [
        module._normalize_destroy_rule(
            module.DestroyRule(
                enabled=True,
                kind=module.DESTROY_KIND_EXPLICIT_MODELS,
                model_ids=[111],
                keep_count=1,
            )
        )
    ]
    widget._get_supported_context = lambda: (
        True,
        "Ready",
        {
            module.MERCHANT_TYPE_MERCHANT: (1.0, 1.0),
            module.MERCHANT_TYPE_MATERIALS: (2.0, 2.0),
            module.MERCHANT_TYPE_RUNE_TRADER: (3.0, 3.0),
            module.MERCHANT_TYPE_RARE_MATERIALS: (4.0, 4.0),
        },
    )
    widget._collect_inventory_items = lambda: [
        _make_item(
            module,
            item_id=40,
            model_id=111,
            name="Iron Sword",
            is_weapon_like=True,
            item_type_id=int(module.ItemType.Sword),
            item_type_name="Sword",
        ),
        _make_item(
            module,
            item_id=41,
            model_id=111,
            name="Iron Sword",
            is_weapon_like=True,
            item_type_id=int(module.ItemType.Sword),
            item_type_name="Sword",
        ),
    ]

    plan = widget._build_plan()

    _expect(len(plan.destroy_actions) == 1, "Non-stackable destroy rules should still plan whole-item destroys.")
    action = plan.destroy_actions[0]
    _expect(action.quantity_to_destroy == 1, "Non-stackable destroy planning should still destroy one whole item at a time.")
    _expect(not action.requires_split, "Non-stackable destroy actions should not require stack splitting.")
    _expect(
        any(entry.state == module.PLAN_STATE_SKIPPED and entry.quantity == 1 and "keep count 1" in entry.reason.lower() for entry in plan.entries),
        "Non-stackable destroy planning should keep a whole item to satisfy keep_count.",
    )


def _test_destroy_material_targets_keep_counts_apply_per_model(module) -> None:
    widget = _make_widget(module)
    widget.catalog_by_model_id[333] = {"model_id": 333, "name": "Wood"}
    widget.catalog_by_model_id[444] = {"model_id": 444, "name": "Iron"}
    widget.destroy_rules = [
        module._normalize_destroy_rule(
            module.DestroyRule(
                enabled=True,
                kind=module.DESTROY_KIND_MATERIALS,
                whitelist_targets=[
                    module.WhitelistTarget(model_id=333, keep_count=4),
                    module.WhitelistTarget(model_id=444, keep_count=100),
                ],
            )
        )
    ]
    widget._get_supported_context = lambda: (
        True,
        "Ready",
        {
            module.MERCHANT_TYPE_MERCHANT: (1.0, 1.0),
            module.MERCHANT_TYPE_MATERIALS: (2.0, 2.0),
            module.MERCHANT_TYPE_RUNE_TRADER: (3.0, 3.0),
            module.MERCHANT_TYPE_RARE_MATERIALS: (4.0, 4.0),
        },
    )
    widget._collect_inventory_items = lambda: [
        _make_item(module, item_id=80, model_id=333, name="Wood", quantity=20, is_material=True),
        _make_item(module, item_id=81, model_id=444, name="Iron", quantity=120, is_material=True),
    ]
    original_inventory = getattr(module.GLOBAL_CACHE, "Inventory", None)
    try:
        module.GLOBAL_CACHE.Inventory = types.SimpleNamespace(
            FindItemBagAndSlot=lambda item_id: (1, 0) if int(item_id) == 80 else (1, 1),
            GetBagSize=lambda bag_id: 3 if int(bag_id) == 1 else 0,
        )

        plan = widget._build_plan()

        action_by_model = {
            action.model_id: action
            for action in plan.destroy_actions
        }
        _expect(action_by_model[333].quantity_to_destroy == 16 and action_by_model[333].keep_quantity == 4, "Per-target material destroy keep counts should preserve the first material independently.")
        _expect(action_by_model[444].quantity_to_destroy == 20 and action_by_model[444].keep_quantity == 100, "Per-target material destroy keep counts should preserve the second material independently.")
    finally:
        module.GLOBAL_CACHE.Inventory = original_inventory


def _test_destroy_explicit_targets_keep_counts_apply_per_model(module) -> None:
    widget = _make_widget(module)
    widget.catalog_by_model_id[555] = {"model_id": 555, "name": "Identification Kit"}
    widget.destroy_rules = [
        module._normalize_destroy_rule(
            module.DestroyRule(
                enabled=True,
                kind=module.DESTROY_KIND_EXPLICIT_MODELS,
                whitelist_targets=[
                    module.WhitelistTarget(model_id=111, keep_count=1),
                    module.WhitelistTarget(model_id=555, keep_count=0),
                ],
            )
        )
    ]
    widget._get_supported_context = lambda: (
        True,
        "Ready",
        {
            module.MERCHANT_TYPE_MERCHANT: (1.0, 1.0),
            module.MERCHANT_TYPE_MATERIALS: (2.0, 2.0),
            module.MERCHANT_TYPE_RUNE_TRADER: (3.0, 3.0),
            module.MERCHANT_TYPE_RARE_MATERIALS: (4.0, 4.0),
        },
    )
    widget._collect_inventory_items = lambda: [
        _make_item(module, item_id=90, model_id=111, name="Iron Sword", quantity=1),
        _make_item(module, item_id=91, model_id=111, name="Iron Sword", quantity=1),
        _make_item(module, item_id=92, model_id=555, name="Identification Kit", quantity=1),
    ]

    plan = widget._build_plan()
    destroyed_item_ids = {action.item_id for action in plan.destroy_actions}

    _expect(92 in destroyed_item_ids, "Per-target explicit destroy keep counts should still destroy models with a zero keep value.")
    _expect(len(destroyed_item_ids & {90, 91}) == 1, "Per-target explicit destroy keep counts should keep one matching item only for that targeted model.")
    _expect(
        any(entry.state == module.PLAN_STATE_SKIPPED and entry.label == "Iron Sword" and "keep count 1" in entry.reason.lower() for entry in plan.entries),
        "Preview should explain which explicit destroy item was kept for its own target row.",
    )


def _test_execute_partial_destroy_moves_keep_quantity_before_destroy(module) -> None:
    widget = _make_widget(module)
    quantities = {50: 20}
    move_calls: list[tuple[int, int, int, int]] = []
    destroy_calls: list[int] = []
    original_item = getattr(module.GLOBAL_CACHE, "Item", None)
    original_inventory = getattr(module.GLOBAL_CACHE, "Inventory", None)
    try:
        module.GLOBAL_CACHE.Item = types.SimpleNamespace(
            Properties=types.SimpleNamespace(
                GetQuantity=lambda item_id: int(quantities.get(int(item_id), 0)),
            )
        )

        def _move_item(item_id: int, bag_id: int, slot: int, quantity: int) -> None:
            move_calls.append((int(item_id), int(bag_id), int(slot), int(quantity)))
            quantities[int(item_id)] = max(0, int(quantities.get(int(item_id), 0)) - int(quantity))

        def _destroy_item(item_id: int) -> None:
            destroy_calls.append(int(item_id))
            quantities.pop(int(item_id), None)

        module.GLOBAL_CACHE.Inventory = types.SimpleNamespace(
            MoveItem=_move_item,
            DestroyItem=_destroy_item,
        )
        widget._get_inventory_stack_quantities = lambda item_ids: {
            int(item_id): int(quantities.get(int(item_id), 0))
            for item_id in item_ids
            if int(quantities.get(int(item_id), 0)) > 0
        }
        widget._find_inventory_empty_slot = lambda _items=None: module.DestroySplitDestination(bag_id=1, slot=1)

        def _confirm_destroy(previous_quantities, **_kwargs):
            if False:
                yield None
            return set(int(item_id) for item_id in previous_quantities.keys()), set()

        widget._wait_for_merchant_sell_confirmation = _confirm_destroy

        outcome = _drain_generator_return(
            widget._execute_destroy_phase(
                [
                    module.PlannedDestroyAction(
                        item_id=50,
                        model_id=333,
                        label="Wood",
                        quantity_to_destroy=16,
                        source_quantity=20,
                        keep_quantity=4,
                        requires_split=True,
                    )
                ]
            )
        )

        _expect(move_calls == [(50, 1, 1, 4)], "Partial destroy execution should move the kept quantity into a free slot before destroying the source stack.")
        _expect(destroy_calls == [50], "Partial destroy execution should destroy the original stack after the keep quantity is moved out.")
        _expect(outcome.completed == 1 and outcome.timeout_failures == 0, "Partial destroy execution should complete successfully when the split and destroy both verify.")
        _expect(50 not in quantities, "The source stack should be gone after a successful partial destroy.")
    finally:
        module.GLOBAL_CACHE.Item = original_item
        module.GLOBAL_CACHE.Inventory = original_inventory


def _test_execute_now_matches_preview_for_protection_only_rules(module) -> None:
    widget = _make_widget(module)
    widget.sell_rules = [
        module._normalize_sell_rule(
            module.SellRule(
                enabled=True,
                kind=module.SELL_KIND_WEAPONS,
                rarities=_rarity_flags(),
                protected_weapon_requirement_rules=[
                    module.WeaponRequirementRule(model_id=111, min_requirement=1, max_requirement=9),
                ],
            )
        ),
        module._normalize_sell_rule(
            module.SellRule(
                enabled=True,
                kind=module.SELL_KIND_WEAPONS,
                rarities=_rarity_flags("gold"),
            )
        ),
    ]
    widget._get_supported_context = lambda: (
        True,
        "Ready",
        {
            module.MERCHANT_TYPE_MERCHANT: (1.0, 1.0),
            module.MERCHANT_TYPE_MATERIALS: (2.0, 2.0),
            module.MERCHANT_TYPE_RUNE_TRADER: (3.0, 3.0),
            module.MERCHANT_TYPE_RARE_MATERIALS: (4.0, 4.0),
        },
    )
    widget._collect_inventory_items = lambda: [
        _make_item(
            module,
            item_id=1,
            model_id=111,
            name="Chaos Axe",
            rarity="Gold",
            is_weapon_like=True,
            requirement=9,
            item_type_id=int(module.ItemType.Axe),
            item_type_name="Axe",
        ),
    ]

    preview_plan = widget._build_plan()
    _expect(not preview_plan.has_actions, "Preview should keep protection-only hits out of the sell queue.")

    _drain_generator_return(widget._execute_now())

    _expect(
        widget.status_message == "Nothing to execute for the current rules and inventory state.",
        "Execute should rebuild the same protected plan and skip selling when preview had only hard-protected matches.",
    )
    _expect(not widget.preview_plan.has_actions, "Execute should leave the rebuilt preview plan in the same protected non-actionable state.")


def _test_execute_now_respects_per_target_whitelist_keep_counts(module) -> None:
    widget = _make_widget(module)
    widget.catalog_by_model_id[555] = {"model_id": 555, "name": "Identification Kit"}
    widget.catalog_by_model_id[666] = {"model_id": 666, "name": "Destroy Me"}
    widget.catalog_by_model_id[777] = {"model_id": 777, "name": "Destroy Me Too"}
    widget.sell_rules = [
        module._normalize_sell_rule(
            module.SellRule(
                enabled=True,
                kind=module.SELL_KIND_EXPLICIT_MODELS,
                whitelist_targets=[
                    module.WhitelistTarget(model_id=111, keep_count=1),
                    module.WhitelistTarget(model_id=555, keep_count=0),
                ],
            )
        )
    ]
    widget.destroy_rules = [
        module._normalize_destroy_rule(
            module.DestroyRule(
                enabled=True,
                kind=module.DESTROY_KIND_EXPLICIT_MODELS,
                whitelist_targets=[
                    module.WhitelistTarget(model_id=666, keep_count=1),
                    module.WhitelistTarget(model_id=777, keep_count=0),
                ],
            )
        )
    ]
    widget._get_supported_context = lambda: (
        True,
        "Ready",
        {
            module.MERCHANT_TYPE_MERCHANT: (1.0, 1.0),
            module.MERCHANT_TYPE_MATERIALS: (2.0, 2.0),
            module.MERCHANT_TYPE_RUNE_TRADER: (3.0, 3.0),
            module.MERCHANT_TYPE_RARE_MATERIALS: (4.0, 4.0),
        },
    )
    widget._collect_inventory_items = lambda: [
        _make_item(module, item_id=101, model_id=111, name="Iron Sword", quantity=1),
        _make_item(module, item_id=102, model_id=111, name="Iron Sword", quantity=1),
        _make_item(module, item_id=103, model_id=555, name="Identification Kit", quantity=1),
        _make_item(module, item_id=201, model_id=666, name="Destroy Me", quantity=1),
        _make_item(module, item_id=202, model_id=666, name="Destroy Me", quantity=1),
        _make_item(module, item_id=203, model_id=777, name="Destroy Me Too", quantity=1),
    ]

    preview_plan = widget._build_plan()
    preview_sell_ids = list(preview_plan.merchant_sell_item_ids)
    preview_destroy_actions = [
        (action.item_id, action.model_id, action.quantity_to_destroy, action.keep_quantity, action.requires_split)
        for action in preview_plan.destroy_actions
    ]
    _expect(preview_sell_ids, "Preview should schedule explicit sell work for per-target whitelist rules.")
    _expect(preview_destroy_actions, "Preview should schedule explicit destroy work for per-target whitelist rules.")

    captured_sell_ids: list[int] = []
    captured_destroy_actions: list[tuple[int, int, int, int, bool]] = []

    def _capture_destroy(actions):
        captured_destroy_actions.extend(
            (
                action.item_id,
                action.model_id,
                action.quantity_to_destroy,
                action.keep_quantity,
                action.requires_split,
            )
            for action in actions
        )
        if False:
            yield None
        return module.ExecutionPhaseOutcome(label="Destroy", measure_label="items", attempted=len(actions), completed=len(actions))

    def _capture_merchant_sell(_coords, item_ids):
        captured_sell_ids.extend(int(item_id) for item_id in item_ids)
        if False:
            yield None
        return module.ExecutionPhaseOutcome(label="Merchant sells", measure_label="items", attempted=len(item_ids), completed=len(item_ids))

    widget._execute_destroy_phase = _capture_destroy
    widget._execute_merchant_sell_phase = _capture_merchant_sell

    _drain_generator_return(widget._execute_now())

    _expect(captured_sell_ids == preview_sell_ids, "Execute should rebuild and use the same per-target sell plan that preview produced.")
    _expect(captured_destroy_actions == preview_destroy_actions, "Execute should rebuild and use the same per-target destroy plan that preview produced.")


def _test_build_plan_deposits_protected_weapon_matches_conditionally(module) -> None:
    widget = _make_widget(module)
    widget.sell_rules = [
        module._normalize_sell_rule(
            module.SellRule(
                enabled=True,
                kind=module.SELL_KIND_WEAPONS,
                deposit_protected_matches=True,
                protected_weapon_requirement_rules=[
                    module.WeaponRequirementRule(model_id=111, min_requirement=1, max_requirement=8),
                ],
            )
        )
    ]
    widget._get_supported_context = lambda: (
        True,
        "Ready",
        {
            module.MERCHANT_TYPE_MERCHANT: (1.0, 1.0),
            module.MERCHANT_TYPE_MATERIALS: (2.0, 2.0),
            module.MERCHANT_TYPE_RUNE_TRADER: (3.0, 3.0),
            module.MERCHANT_TYPE_RARE_MATERIALS: (4.0, 4.0),
        },
    )
    original_inventory = getattr(module.GLOBAL_CACHE, "Inventory", None)
    try:
        module.GLOBAL_CACHE.Inventory = types.SimpleNamespace(IsStorageOpen=lambda: False)
        widget._collect_inventory_items = lambda: [
            _make_item(
                module,
                item_id=301,
                model_id=111,
                name="Chaos Axe",
                rarity="Gold",
                is_weapon_like=True,
                requirement=8,
                item_type_id=int(module.ItemType.Axe),
                item_type_name="Axe",
            ),
        ]

        plan = widget._build_plan()

        deposit_transfers = [transfer for transfer in plan.storage_transfers if transfer.direction == module.STORAGE_TRANSFER_DEPOSIT]
        _expect(len(deposit_transfers) == 1, "Protected weapon matches should create one planned Xunlai deposit transfer when enabled.")
        _expect(
            deposit_transfers[0].item_id == 301 and deposit_transfers[0].quantity == 1,
            "Protected weapon deposits should target the matched stack and quantity.",
        )
        _expect(
            any(
                entry.action_type == "deposit"
                and entry.merchant_type == module.MERCHANT_TYPE_STORAGE
                and entry.label == "Chaos Axe"
                and entry.state == module.PLAN_STATE_CONDITIONAL
                for entry in plan.entries
            ),
            "Preview should show protected weapon deposits as conditional when Xunlai is closed.",
        )
        _expect(plan.has_actions, "A planned Xunlai deposit should keep the preview actionable.")
    finally:
        module.GLOBAL_CACHE.Inventory = original_inventory


def _test_build_plan_does_not_deposit_customized_or_unidentified_only_skips(module) -> None:
    widget = _make_widget(module)
    widget.sell_rules = [
        module._normalize_sell_rule(
            module.SellRule(
                enabled=True,
                kind=module.SELL_KIND_WEAPONS,
                rarities=_rarity_flags("gold"),
                skip_customized=True,
                deposit_protected_matches=True,
            )
        )
    ]
    widget._get_supported_context = lambda: (
        True,
        "Ready",
        {
            module.MERCHANT_TYPE_MERCHANT: (1.0, 1.0),
            module.MERCHANT_TYPE_MATERIALS: (2.0, 2.0),
            module.MERCHANT_TYPE_RUNE_TRADER: (3.0, 3.0),
            module.MERCHANT_TYPE_RARE_MATERIALS: (4.0, 4.0),
        },
    )
    original_inventory = getattr(module.GLOBAL_CACHE, "Inventory", None)
    try:
        module.GLOBAL_CACHE.Inventory = types.SimpleNamespace(IsStorageOpen=lambda: False)
        widget._collect_inventory_items = lambda: [
            _make_item(
                module,
                item_id=302,
                model_id=111,
                name="Customized Axe",
                rarity="Gold",
                is_customized=True,
                is_weapon_like=True,
                item_type_id=int(module.ItemType.Axe),
                item_type_name="Axe",
            ),
        ]

        plan = widget._build_plan()

        _expect(
            not any(transfer.direction == module.STORAGE_TRANSFER_DEPOSIT for transfer in plan.storage_transfers),
            "Customized-only protection skips should not be turned into Xunlai deposits in v1.",
        )
        _expect(
            any("Customized item." in entry.reason for entry in plan.entries if entry.state == module.PLAN_STATE_SKIPPED),
            "Preview should still surface the existing customized-item skip reason.",
        )
    finally:
        module.GLOBAL_CACHE.Inventory = original_inventory


def _test_build_plan_deposits_explicit_keep_targets_on_storage_only_preview(module) -> None:
    widget = _prime_initialized_widget(module, _make_widget(module))
    widget.sell_rules = [
        module._normalize_sell_rule(
            module.SellRule(
                enabled=True,
                kind=module.SELL_KIND_EXPLICIT_MODELS,
                whitelist_targets=[
                    module.WhitelistTarget(model_id=111, keep_count=1, deposit_to_storage=True),
                ],
            )
        )
    ]
    widget._get_supported_context = lambda: (
        False,
        "Outpost ready, but merchant selectors were not resolved.",
        {
            module.MERCHANT_TYPE_MERCHANT: None,
            module.MERCHANT_TYPE_MATERIALS: None,
            module.MERCHANT_TYPE_RUNE_TRADER: None,
            module.MERCHANT_TYPE_RARE_MATERIALS: None,
        },
    )
    original_inventory = getattr(module.GLOBAL_CACHE, "Inventory", None)
    try:
        module.GLOBAL_CACHE.Inventory = types.SimpleNamespace(IsStorageOpen=lambda: False)
        widget._collect_inventory_items = lambda: [
            _make_item(module, item_id=310, model_id=111, name="Iron Sword", quantity=1),
        ]

        plan = widget._build_plan()
        widget.preview_plan = plan

        _expect(
            any(
                entry.action_type == "deposit"
                and entry.label == "Iron Sword"
                and entry.state == module.PLAN_STATE_CONDITIONAL
                for entry in plan.entries
            ),
            "Storage-only previews should still show conditional Xunlai deposits for explicit keep targets.",
        )
        _expect(plan.has_actions, "Storage-only deposit previews should remain actionable even when merchant support is unavailable.")

        preview_result = widget.build_remote_preview_result()
        _expect(preview_result["status_label"] == "Conditional", "Storage-only previews with conditional deposits should report Conditional status.")
        _expect(
            "Xunlai cleanup" in preview_result["detail"],
            "Storage-only preview detail should explain that Xunlai cleanup can still run.",
        )
    finally:
        module.GLOBAL_CACHE.Inventory = original_inventory


def _test_projected_preview_builds_post_travel_plan_without_travel_entry(module) -> None:
    widget = _prime_initialized_widget(module, _make_widget(module))
    widget.auto_travel_enabled = True
    widget.target_outpost_id = 2
    widget.sell_rules = [
        module._normalize_sell_rule(
            module.SellRule(
                enabled=True,
                kind=module.SELL_KIND_EXPLICIT_MODELS,
                model_ids=[111],
                keep_count=0,
            )
        )
    ]
    widget._collect_inventory_items = lambda: [
        _make_item(module, item_id=410, model_id=111, name="Iron Sword", quantity=1),
    ]

    plan = widget._build_plan(projected_preview=True)

    _expect(plan.travel_to_outpost_id == 0, "Projected previews should no longer use runtime travel state in the plan result.")
    _expect(not any(entry.action_type == "travel" for entry in plan.entries), "Projected previews should not collapse into a synthetic travel row.")
    _expect(
        any(
            entry.action_type == "sell"
            and entry.label == "Iron Sword"
            and entry.state == module.PLAN_STATE_CONDITIONAL
            for entry in plan.entries
        ),
        "Projected previews should still show the post-travel merchant action, marked conditional until arrival context is confirmed.",
    )
    _expect(plan.has_actions, "Projected previews should remain actionable when post-travel merchant work is expected.")


def _test_projected_preview_keeps_cleanup_visible_from_unsupported_current_map(module) -> None:
    widget = _prime_initialized_widget(module, _make_widget(module))
    widget.auto_travel_enabled = True
    widget.target_outpost_id = 2
    widget.cleanup_targets = [module.CleanupTarget(model_id=111, keep_on_character=0)]
    widget._collect_inventory_items = lambda: [
        _make_item(module, item_id=420, model_id=111, name="Iron Sword", quantity=1),
    ]

    original_is_outpost = module.Map.IsOutpost
    original_is_guild_hall = module.Map.IsGuildHall
    try:
        module.Map.IsOutpost = lambda: False
        module.Map.IsGuildHall = lambda: False

        plan = widget._build_plan(projected_preview=True)

        _expect(
            any(
                entry.action_type == "deposit"
                and entry.label == "Iron Sword"
                and entry.state == module.PLAN_STATE_CONDITIONAL
                for entry in plan.entries
            ),
            "Projected previews should still surface planned cleanup / Xunlai deposits even when the current map is unsupported.",
        )
        _expect(plan.has_actions, "Projected cleanup should keep the preview actionable from unsupported current maps.")
    finally:
        module.Map.IsOutpost = original_is_outpost
        module.Map.IsGuildHall = original_is_guild_hall


def _configure_consumable_multistop_fixture(
    module,
    *,
    include_material_buy: bool = True,
    destination_id: int = 2,
    destination_name: str = "Regression Harbor",
):
    widget = _prime_initialized_widget(module, _make_widget(module))
    widget.outpost_entries = [
        entry
        for entry in widget.outpost_entries
        if int(entry.get("id", 0)) not in {int(module.EMBARK_BEACH_MAP_ID), int(destination_id)}
    ]
    widget.outpost_entries.append({"id": int(destination_id), "name": str(destination_name)})
    widget.outpost_entries.append({"id": int(module.EMBARK_BEACH_MAP_ID), "name": "Embark Beach"})
    widget.auto_travel_enabled = True
    widget.target_outpost_id = int(destination_id)

    armor_model_id = int(module.ModelID.Armor_Of_Salvation.value)
    wood_model_id = int(module.ModelID.Wood_Plank.value)
    bone_model_id = int(module.ModelID.Bone.value)
    iron_model_id = int(module.ModelID.Iron_Ingot.value)
    widget.catalog_by_model_id.update(
        {
            armor_model_id: {"model_id": armor_model_id, "name": "Armor of Salvation"},
            wood_model_id: {"model_id": wood_model_id, "name": "Wood Plank", "material_type": "common"},
            bone_model_id: {"model_id": bone_model_id, "name": "Bone", "material_type": "common"},
            iron_model_id: {"model_id": iron_model_id, "name": "Iron Ingot", "material_type": "common"},
        }
    )
    buy_rules = [
        module._normalize_buy_rule(
            module.BuyRule(
                enabled=True,
                kind=module.BUY_KIND_CONSUMABLE_CRAFTER_TARGET,
                merchant_stock_targets=[
                    module.MerchantStockTarget(model_id=armor_model_id, target_count=1, max_per_run=1),
                ],
                consumable_crafter_count_mode=module.CONSUMABLE_CRAFTER_COUNT_MODE_CRAFT_AMOUNT,
            )
        )
    ]
    if include_material_buy:
        buy_rules.append(
            module._normalize_buy_rule(
                module.BuyRule(
                    enabled=True,
                    kind=module.BUY_KIND_MATERIAL_TARGET,
                    material_targets=[
                        module.MaterialTarget(model_id=wood_model_id, target_count=1, max_per_run=10),
                    ],
                )
            )
        )
    widget.buy_rules = buy_rules
    widget._collect_inventory_items = lambda: [
        _make_item(
            module,
            item_id=11,
            model_id=iron_model_id,
            name="Iron Ingot",
            quantity=50,
            is_material=True,
        ),
        _make_item(
            module,
            item_id=12,
            model_id=bone_model_id,
            name="Bone",
            quantity=50,
            is_material=True,
        )
    ]
    widget._collect_storage_items = lambda: []
    widget._get_material_storage_quantity_and_slot = lambda _model_id: (0, 0, 250)
    return widget


def _test_consumable_multistop_preview_routes_embark_before_destination(module) -> None:
    widget = _configure_consumable_multistop_fixture(module, include_material_buy=True)
    original_inventory = getattr(module.GLOBAL_CACHE, "Inventory", None)
    original_player = module.Player
    try:
        module.GLOBAL_CACHE.Inventory = types.SimpleNamespace(
            IsStorageOpen=lambda: True,
            GetGoldOnCharacter=lambda: 1000,
            GetGoldInStorage=lambda: 0,
            GetFreeSlotCount=lambda: 10,
        )
        module.Player = types.SimpleNamespace(
            GetSkillPointData=lambda: (5, 100),
            GetTitle=lambda _title_id: types.SimpleNamespace(current_points=999999),
        )

        plan = widget._build_plan(projected_preview=True)

        travel_labels = [entry.label for entry in plan.entries if entry.action_type == "travel"]
        _expect(plan.multi_stop_route, "Projected preview should mark the Embark Beach consumable route as multi-stop.")
        _expect(
            travel_labels == ["Embark Beach", "Regression Harbor"],
            "Projected preview should show travel to Embark Beach before the selected destination.",
        )
        _expect(
            any(
                entry.merchant_type == module.MERCHANT_TYPE_CONSUMABLE_CRAFTER
                and entry.label.startswith("Armor of Salvation")
                and entry.quantity == 1
                and entry.state == module.PLAN_STATE_CONDITIONAL
                for entry in plan.entries
            ),
            "Projected destination previews should keep Embark Beach consumable crafting visible.",
        )
        _expect(
            any(
                entry.merchant_type == module.MERCHANT_TYPE_MATERIALS
                and entry.label.startswith("Wood Plank")
                and entry.quantity == 10
                and entry.state == module.PLAN_STATE_CONDITIONAL
                for entry in plan.entries
            ),
            "Projected multi-stop previews should keep remaining destination material buys visible.",
        )
        _expect(
            not any(
                entry.merchant_type == module.MERCHANT_TYPE_CONSUMABLE_CRAFTER
                and "Embark Beach only" in entry.reason
                for entry in plan.entries
            ),
            "Projected multi-stop previews should not hide consumable work behind the selected non-Embark destination.",
        )
    finally:
        module.GLOBAL_CACHE.Inventory = original_inventory
        module.Player = original_player


def _test_consumable_multistop_execute_crafts_then_runs_destination_work(module) -> None:
    guild_hall_id = 179
    widget = _configure_consumable_multistop_fixture(
        module,
        include_material_buy=True,
        destination_id=guild_hall_id,
        destination_name="Guild Hall - Isle of the Dead",
    )
    current_map = {"id": 100, "guild_hall": False}
    events: list[str] = []
    debug_logs: list[str] = []
    destination_plan_counts: list[tuple[int, int]] = []
    original_map_methods = {
        "GetMapID": module.Map.GetMapID,
        "IsMapReady": module.Map.IsMapReady,
        "IsOutpost": module.Map.IsOutpost,
        "IsGuildHall": module.Map.IsGuildHall,
        "IsMapIDMatch": module.Map.IsMapIDMatch,
    }
    original_inventory = getattr(module.GLOBAL_CACHE, "Inventory", None)
    original_player = module.Player
    try:
        module.Map.GetMapID = lambda: int(current_map["id"])
        module.Map.IsMapReady = lambda: True
        module.Map.IsOutpost = lambda: True
        module.Map.IsGuildHall = lambda: bool(current_map["guild_hall"])
        module.Map.IsMapIDMatch = lambda current, target: int(current) == int(target)
        module.GLOBAL_CACHE.Inventory = types.SimpleNamespace(
            IsStorageOpen=lambda: True,
            GetGoldOnCharacter=lambda: 1000,
            GetGoldInStorage=lambda: 0,
            GetFreeSlotCount=lambda: 10,
        )
        module.Player = types.SimpleNamespace(
            GetSkillPointData=lambda: (5, 100),
            GetTitle=lambda _title_id: types.SimpleNamespace(current_points=999999),
        )

        def _context(*_args, **_kwargs):
            if int(current_map["id"]) == int(module.EMBARK_BEACH_MAP_ID):
                return True, "Embark ready", {
                    module.MERCHANT_TYPE_MERCHANT: None,
                    module.MERCHANT_TYPE_MATERIALS: None,
                    module.MERCHANT_TYPE_RUNE_TRADER: None,
                    module.MERCHANT_TYPE_SCROLL_TRADER: None,
                    module.MERCHANT_TYPE_RARE_MATERIALS: None,
                    module.MERCHANT_TYPE_CONSUMABLE_CRAFTER: (3349.48, 596.78),
                }
            if bool(current_map["guild_hall"]):
                return True, "Guild Hall ready", {
                    module.MERCHANT_TYPE_MERCHANT: None,
                    module.MERCHANT_TYPE_MATERIALS: (20.0, 20.0),
                    module.MERCHANT_TYPE_RUNE_TRADER: None,
                    module.MERCHANT_TYPE_SCROLL_TRADER: None,
                    module.MERCHANT_TYPE_RARE_MATERIALS: None,
                    module.MERCHANT_TYPE_CONSUMABLE_CRAFTER: None,
                }
            return False, "Unsupported", {
                module.MERCHANT_TYPE_MERCHANT: None,
                module.MERCHANT_TYPE_MATERIALS: None,
                module.MERCHANT_TYPE_RUNE_TRADER: None,
                module.MERCHANT_TYPE_SCROLL_TRADER: None,
                module.MERCHANT_TYPE_RARE_MATERIALS: None,
                module.MERCHANT_TYPE_CONSUMABLE_CRAFTER: None,
            }

        def _travel(outpost_id: int):
            events.append(f"travel:{int(outpost_id)}")
            current_map["id"] = int(outpost_id)
            current_map["guild_hall"] = int(outpost_id) == guild_hall_id
            if False:
                yield None
            return True

        def _craft(crafts, *, phase_label="Consumable crafters"):
            events.extend(f"craft:{craft.label}" for craft in crafts)
            if False:
                yield None
            total = sum(max(0, int(craft.quantity)) for craft in crafts)
            return module.ExecutionPhaseOutcome(label=phase_label, measure_label="crafts", attempted=total, completed=total)

        def _buy_materials(_coords, buys, *, phase_label="Material buys"):
            destination_plan_counts.append(
                (
                    len(widget.preview_plan.material_buys),
                    len(widget.preview_plan.consumable_crafter_buys),
                )
            )
            events.extend(f"material:{buy.label}" for buy in buys)
            if False:
                yield None
            return module.ExecutionPhaseOutcome(label=phase_label, measure_label="trades", attempted=len(buys), completed=len(buys))

        widget._debug_log = lambda message: debug_logs.append(str(message))
        widget._get_supported_context = _context
        widget._travel_to_target_outpost = _travel
        widget._craft_planned_consumables = _craft
        widget._buy_planned_materials = _buy_materials

        _drain_generator_return(widget._execute_now())

        _expect(
            events == [
                f"travel:{int(module.EMBARK_BEACH_MAP_ID)}",
                "craft:Armor of Salvation (24860)",
                f"travel:{guild_hall_id}",
                "material:Wood Plank (946)",
            ],
            "Travel + Execute should craft Embark consumables before traveling to the selected destination for remaining work.",
        )
        _expect(
            events.count(f"travel:{int(module.EMBARK_BEACH_MAP_ID)}") == 1,
            "Travel + Execute should only travel to Embark Beach once per multi-stop run.",
        )
        _expect(
            sum(1 for event in events if event.startswith("craft:Armor of Salvation")) == 1,
            "Craft requested amount mode should not execute the same consumable craft twice in one multi-stop run.",
        )
        _expect(
            destination_plan_counts == [(1, 0)],
            "Destination execution should run a non-consumable plan with material_buys=1 and consumable_crafts=0.",
        )
        _expect(
            sum("Multi-stop execution travel: target=Embark Beach" in row for row in debug_logs) == 1,
            "Nested destination execution must not re-enter the Embark Beach multi-stop route after Guild Hall arrival.",
        )
    finally:
        module.Map.GetMapID = original_map_methods["GetMapID"]
        module.Map.IsMapReady = original_map_methods["IsMapReady"]
        module.Map.IsOutpost = original_map_methods["IsOutpost"]
        module.Map.IsGuildHall = original_map_methods["IsGuildHall"]
        module.Map.IsMapIDMatch = original_map_methods["IsMapIDMatch"]
        module.GLOBAL_CACHE.Inventory = original_inventory
        module.Player = original_player


def _test_consumable_multistop_execute_stops_at_embark_when_only_consumables(module) -> None:
    widget = _configure_consumable_multistop_fixture(module, include_material_buy=False)
    current_map = {"id": 100}
    events: list[str] = []
    original_map_methods = {
        "GetMapID": module.Map.GetMapID,
        "IsMapReady": module.Map.IsMapReady,
        "IsOutpost": module.Map.IsOutpost,
        "IsGuildHall": module.Map.IsGuildHall,
        "IsMapIDMatch": module.Map.IsMapIDMatch,
    }
    original_inventory = getattr(module.GLOBAL_CACHE, "Inventory", None)
    original_player = module.Player
    try:
        module.Map.GetMapID = lambda: int(current_map["id"])
        module.Map.IsMapReady = lambda: True
        module.Map.IsOutpost = lambda: True
        module.Map.IsGuildHall = lambda: False
        module.Map.IsMapIDMatch = lambda current, target: int(current) == int(target)
        module.GLOBAL_CACHE.Inventory = types.SimpleNamespace(
            IsStorageOpen=lambda: True,
            GetGoldOnCharacter=lambda: 1000,
            GetGoldInStorage=lambda: 0,
            GetFreeSlotCount=lambda: 10,
        )
        module.Player = types.SimpleNamespace(
            GetSkillPointData=lambda: (5, 100),
            GetTitle=lambda _title_id: types.SimpleNamespace(current_points=999999),
        )
        widget._get_supported_context = lambda *_args, **_kwargs: (
            int(current_map["id"]) == int(module.EMBARK_BEACH_MAP_ID),
            "Ready" if int(current_map["id"]) == int(module.EMBARK_BEACH_MAP_ID) else "Unsupported",
            {
                module.MERCHANT_TYPE_MERCHANT: None,
                module.MERCHANT_TYPE_MATERIALS: None,
                module.MERCHANT_TYPE_RUNE_TRADER: None,
                module.MERCHANT_TYPE_SCROLL_TRADER: None,
                module.MERCHANT_TYPE_RARE_MATERIALS: None,
                module.MERCHANT_TYPE_CONSUMABLE_CRAFTER: (3349.48, 596.78)
                if int(current_map["id"]) == int(module.EMBARK_BEACH_MAP_ID)
                else None,
            },
        )

        def _travel(outpost_id: int):
            events.append(f"travel:{int(outpost_id)}")
            current_map["id"] = int(outpost_id)
            if False:
                yield None
            return True

        def _craft(crafts, *, phase_label="Consumable crafters"):
            events.extend(f"craft:{craft.label}" for craft in crafts)
            if False:
                yield None
            total = sum(max(0, int(craft.quantity)) for craft in crafts)
            return module.ExecutionPhaseOutcome(label=phase_label, measure_label="crafts", attempted=total, completed=total)

        widget._travel_to_target_outpost = _travel
        widget._craft_planned_consumables = _craft

        _drain_generator_return(widget._execute_now())

        _expect(
            events == [f"travel:{int(module.EMBARK_BEACH_MAP_ID)}", "craft:Armor of Salvation (24860)"],
            "Travel + Execute should stop at Embark Beach when no non-consumable destination work remains.",
        )
    finally:
        module.Map.GetMapID = original_map_methods["GetMapID"]
        module.Map.IsMapReady = original_map_methods["IsMapReady"]
        module.Map.IsOutpost = original_map_methods["IsOutpost"]
        module.Map.IsGuildHall = original_map_methods["IsGuildHall"]
        module.Map.IsMapIDMatch = original_map_methods["IsMapIDMatch"]
        module.GLOBAL_CACHE.Inventory = original_inventory
        module.Player = original_player


def _test_consumable_multistop_execute_here_stays_local(module) -> None:
    widget = _configure_consumable_multistop_fixture(module, include_material_buy=True)
    current_map = {"id": 2}
    events: list[str] = []
    original_map_methods = {
        "GetMapID": module.Map.GetMapID,
        "IsMapReady": module.Map.IsMapReady,
        "IsOutpost": module.Map.IsOutpost,
        "IsGuildHall": module.Map.IsGuildHall,
        "IsMapIDMatch": module.Map.IsMapIDMatch,
    }
    original_inventory = getattr(module.GLOBAL_CACHE, "Inventory", None)
    original_player = module.Player
    try:
        module.Map.GetMapID = lambda: int(current_map["id"])
        module.Map.IsMapReady = lambda: True
        module.Map.IsOutpost = lambda: True
        module.Map.IsGuildHall = lambda: False
        module.Map.IsMapIDMatch = lambda current, target: int(current) == int(target)
        module.GLOBAL_CACHE.Inventory = types.SimpleNamespace(
            IsStorageOpen=lambda: True,
            GetGoldOnCharacter=lambda: 1000,
            GetGoldInStorage=lambda: 0,
            GetFreeSlotCount=lambda: 10,
        )
        module.Player = types.SimpleNamespace(
            GetSkillPointData=lambda: (5, 100),
            GetTitle=lambda _title_id: types.SimpleNamespace(current_points=999999),
        )
        widget._get_supported_context = lambda *_args, **_kwargs: (
            True,
            "Destination ready",
            {
                module.MERCHANT_TYPE_MERCHANT: None,
                module.MERCHANT_TYPE_MATERIALS: (20.0, 20.0),
                module.MERCHANT_TYPE_RUNE_TRADER: None,
                module.MERCHANT_TYPE_SCROLL_TRADER: None,
                module.MERCHANT_TYPE_RARE_MATERIALS: None,
                module.MERCHANT_TYPE_CONSUMABLE_CRAFTER: None,
            },
        )

        def _travel(outpost_id: int):
            events.append(f"travel:{int(outpost_id)}")
            if False:
                yield None
            return True

        def _craft(crafts, *, phase_label="Consumable crafters"):
            events.extend(f"craft:{craft.label}" for craft in crafts)
            if False:
                yield None
            return module.ExecutionPhaseOutcome(label=phase_label, measure_label="crafts", attempted=0, completed=0)

        def _buy_materials(_coords, buys, *, phase_label="Material buys"):
            events.extend(f"material:{buy.label}" for buy in buys)
            if False:
                yield None
            return module.ExecutionPhaseOutcome(label=phase_label, measure_label="trades", attempted=len(buys), completed=len(buys))

        widget._travel_to_target_outpost = _travel
        widget._craft_planned_consumables = _craft
        widget._buy_planned_materials = _buy_materials

        _drain_generator_return(widget._execute_now(local_only=True))

        _expect(
            events == ["material:Wood Plank (946)"],
            "Execute Here should stay local with consumable rules enabled and must not route through Embark Beach.",
        )
    finally:
        module.Map.GetMapID = original_map_methods["GetMapID"]
        module.Map.IsMapReady = original_map_methods["IsMapReady"]
        module.Map.IsOutpost = original_map_methods["IsOutpost"]
        module.Map.IsGuildHall = original_map_methods["IsGuildHall"]
        module.Map.IsMapIDMatch = original_map_methods["IsMapIDMatch"]
        module.GLOBAL_CACHE.Inventory = original_inventory
        module.Player = original_player


def _test_preview_reason_display_hides_projected_suffix_without_mutating_plan(module) -> None:
    widget = _prime_initialized_widget(module, _make_widget(module))
    widget.preview_ready = True
    widget.preview_requires_execute_travel = True
    widget.preview_execute_travel_target_outpost_id = 2
    widget.preview_execute_travel_target_outpost_name = "Regression Harbor"
    projected_reason = (
        "1 individual trade(s). "
        "Projected after travel to Regression Harbor. "
        "Execute will confirm live Merchant access on arrival."
    )
    entry = module.ExecutionPlanEntry(
        action_type="sell",
        merchant_type=module.MERCHANT_TYPE_MERCHANT,
        label="Iron Sword",
        quantity=1,
        state=module.PLAN_STATE_CONDITIONAL,
        reason=projected_reason,
    )

    displayed_reason = widget._get_preview_reason_for_display(entry)

    _expect(
        displayed_reason == "1 individual trade(s).",
        "Preview row rendering should hide the projected-travel suffix while preserving the row-specific reason.",
    )
    _expect(
        entry.reason == projected_reason,
        "Preview row rendering should stay UI-only and must not mutate the stored plan reason.",
    )


def _test_preview_reason_display_normalizes_nested_protection_wording(module) -> None:
    widget = _prime_initialized_widget(module, _make_widget(module))
    direct_linked = module.ExecutionPlanEntry(
        action_type="deposit",
        merchant_type=module.MERCHANT_TYPE_STORAGE,
        label="Tower Shield",
        quantity=1,
        state=module.PLAN_STATE_WILL_EXECUTE,
        reason="Protected by Weapons Protections (#1): Protected by all-weapons perfect-base range: Shield Armor 16, req 9 Strength.",
    )
    blocked_destroy = module.ExecutionPlanEntry(
        action_type="destroy",
        merchant_type=module.MERCHANT_TYPE_INVENTORY,
        label="Chaos Axe",
        quantity=1,
        state=module.PLAN_STATE_SKIPPED,
        reason="Blocked by Destroy Weapons rule #2: Hard-protected by Weapons Protections (#1): Protected by model perfect-base range: Chaos Axe 6-28, req 9 Axe Mastery.",
    )

    _expect(
        widget._get_preview_reason_for_display(direct_linked)
        == "Protected by Weapons Protections (#1): all-weapons perfect-base range, Shield Armor 16, req 9 Strength.",
        "Preview display should collapse nested direct protection wording without mutating the stored reason.",
    )
    _expect(
        direct_linked.reason
        == "Protected by Weapons Protections (#1): Protected by all-weapons perfect-base range: Shield Armor 16, req 9 Strength.",
        "Preview reason wording polish should be display-only.",
    )
    _expect(
        widget._get_preview_reason_for_display(blocked_destroy)
        == "Blocked by Destroy Weapons rule #2: protected by Weapons Protections (#1), model perfect-base range, Chaos Axe 6-28, req 9 Axe Mastery.",
        "Preview display should make blocked nested protection wording scannable.",
    )


def _test_detailed_preview_controls_direct_storage_deposit_reasons(module) -> None:
    widget = _prime_initialized_widget(module, _make_widget(module))

    direct_perfect = module.ExecutionPlanEntry(
        action_type="deposit",
        merchant_type=module.MERCHANT_TYPE_STORAGE,
        label="Tower Shield",
        quantity=1,
        state=module.PLAN_STATE_WILL_EXECUTE,
        reason="Protected by all-weapons perfect-base range: Shield Armor 16, req 9 Strength.",
    )
    ordinary_cleanup = module.ExecutionPlanEntry(
        action_type="deposit",
        merchant_type=module.MERCHANT_TYPE_STORAGE,
        label="Bone",
        quantity=10,
        state=module.PLAN_STATE_WILL_EXECUTE,
        reason="Cleanup target keeps 0 on character.",
    )
    skipped_protection = module.ExecutionPlanEntry(
        action_type="deposit",
        merchant_type=module.MERCHANT_TYPE_STORAGE,
        label="Tower Shield",
        quantity=0,
        state=module.PLAN_STATE_SKIPPED,
        reason="Blocked by Rule 1 (Weapons): Hard-protected by Rule 1 (Weapons): Blacklisted model.",
    )

    _expect(
        not widget._should_show_preview_reason(
            direct_perfect,
            widget._get_preview_reason_for_display(direct_perfect),
        ),
        "Compact preview should hide direct Xunlai deposit protection reasons.",
    )
    _expect(
        not widget._should_show_preview_reason(
            ordinary_cleanup,
            widget._get_preview_reason_for_display(ordinary_cleanup),
        ),
        "Compact preview should hide ordinary direct Xunlai deposit reasons.",
    )
    widget.detailed_preview = True
    _expect(
        widget._should_show_preview_reason(
            direct_perfect,
            widget._get_preview_reason_for_display(direct_perfect),
        ),
        "Detailed Preview should show direct Xunlai deposit protection reasons.",
    )
    widget.detailed_preview = False
    _expect(
        widget._should_show_preview_reason(
            skipped_protection,
            widget._get_preview_reason_for_display(skipped_protection),
            show_reasons=True,
        ),
        "Skipped protection reasons should continue to show through the skipped/blocked table.",
    )


def _test_detailed_preview_shows_all_direct_reasons(module) -> None:
    widget = _prime_initialized_widget(module, _make_widget(module))
    direct_destroy = module.ExecutionPlanEntry(
        action_type="destroy",
        merchant_type=module.MERCHANT_TYPE_INVENTORY,
        label="Purple Sword",
        quantity=1,
        state=module.PLAN_STATE_WILL_EXECUTE,
        reason="Matched by Destroy Weapons rule #2: rarity Purple.",
    )
    direct_sell = module.ExecutionPlanEntry(
        action_type="sell",
        merchant_type=module.MERCHANT_TYPE_MERCHANT,
        label="Iron Sword",
        quantity=1,
        state=module.PLAN_STATE_WILL_EXECUTE,
        reason="1 individual trade(s).",
    )
    conditional_buy = module.ExecutionPlanEntry(
        action_type="buy",
        merchant_type=module.MERCHANT_TYPE_MATERIALS,
        label="Iron Ingot",
        quantity=10,
        state=module.PLAN_STATE_CONDITIONAL,
        reason="Will attempt this buy only if the currently opened merchant offers the item.",
    )
    skipped_destroy = module.ExecutionPlanEntry(
        action_type="destroy",
        merchant_type=module.MERCHANT_TYPE_INVENTORY,
        label="Chaos Axe",
        quantity=0,
        state=module.PLAN_STATE_SKIPPED,
        reason="Blocked by Destroy Weapons rule #2: protected by Weapons Protections (#1), model perfect-base range.",
    )

    _expect(
        not widget._should_show_preview_reason(
            direct_destroy,
            widget._get_preview_reason_for_display(direct_destroy),
        ),
        "Compact preview should keep ordinary direct destroy reasons hidden.",
    )
    widget.detailed_preview = True
    _expect(
        widget._should_show_preview_reason(
            direct_destroy,
            widget._get_preview_reason_for_display(direct_destroy),
        ),
        "Detailed Preview should show direct destroy reasons.",
    )
    _expect(
        widget._should_show_preview_reason(
            direct_sell,
            widget._get_preview_reason_for_display(direct_sell),
        ),
        "Detailed Preview should show direct sell reasons.",
    )
    _expect(
        widget._should_show_preview_reason(
            conditional_buy,
            widget._get_preview_reason_for_display(conditional_buy),
            is_conditional=True,
        ),
        "Conditional reasons should remain visible in detailed preview.",
    )
    _expect(
        widget._should_show_preview_reason(
            skipped_destroy,
            widget._get_preview_reason_for_display(skipped_destroy),
            show_reasons=True,
        ),
        "Skipped / blocked reasons should remain visible through the existing skipped table path.",
    )


def _test_projected_preview_here_availability_tracks_local_services_and_storage(module) -> None:
    widget = _prime_initialized_widget(module, _make_widget(module))
    widget.preview_ready = True
    widget.preview_requires_execute_travel = True
    widget.preview_execute_travel_target_outpost_id = 2
    widget.preview_execute_travel_target_outpost_name = "Regression Harbor"
    widget.preview_plan = module.PlanResult(
        supported_map=True,
        supported_reason="Projected preview",
        entries=[
            module.ExecutionPlanEntry(
                action_type="sell",
                merchant_type=module.MERCHANT_TYPE_MERCHANT,
                label="Iron Sword",
                quantity=1,
                state=module.PLAN_STATE_CONDITIONAL,
                reason="Projected merchant work.",
            ),
            module.ExecutionPlanEntry(
                action_type="buy",
                merchant_type=module.MERCHANT_TYPE_MATERIALS,
                label="Iron Ingot",
                quantity=10,
                state=module.PLAN_STATE_CONDITIONAL,
                reason="Projected material work.",
            ),
            module.ExecutionPlanEntry(
                action_type="buy",
                merchant_type=module.MERCHANT_TYPE_RUNE_TRADER,
                label="Superior Vigor Rune",
                quantity=1,
                state=module.PLAN_STATE_CONDITIONAL,
                reason="Projected rune trader work.",
            ),
            module.ExecutionPlanEntry(
                action_type="deposit",
                merchant_type=module.MERCHANT_TYPE_STORAGE,
                label="Bone",
                quantity=1,
                state=module.PLAN_STATE_CONDITIONAL,
                reason="Projected storage work.",
            ),
        ],
        storage_plan_state=module.STORAGE_PLAN_STATE_NEEDS_EXACT_SCAN,
    )
    widget._get_supported_context = lambda: (
        True,
        "Ready",
        {
            module.MERCHANT_TYPE_MERCHANT: (1.0, 1.0),
            module.MERCHANT_TYPE_MATERIALS: None,
            module.MERCHANT_TYPE_RUNE_TRADER: (3.0, 3.0),
            module.MERCHANT_TYPE_RARE_MATERIALS: None,
        },
    )
    widget._has_local_storage_access = lambda: False

    availability_here = widget._get_preview_here_availability()
    merchant_entry, material_entry, rune_entry, storage_entry = widget.preview_plan.entries

    _expect(
        widget._is_preview_entry_available_here(
            merchant_entry,
            availability_here=availability_here,
            plan=widget.preview_plan,
        ),
        "Projected merchant rows should show as locally available when the current map resolves a merchant.",
    )
    _expect(
        not widget._is_preview_entry_available_here(
            material_entry,
            availability_here=availability_here,
            plan=widget.preview_plan,
        ),
        "Projected material rows should stay unavailable-here when the current map does not resolve that trader.",
    )
    _expect(
        not widget._is_preview_entry_available_here(
            storage_entry,
            availability_here=availability_here,
            plan=widget.preview_plan,
        ),
        "Projected storage rows should stay unavailable-here when local Xunlai access cannot be resolved passively.",
    )
    _expect(
        not widget._is_preview_entry_available_here(
            rune_entry,
            availability_here=availability_here,
            plan=widget.preview_plan,
        ),
        "Rune trader buys that still need an exact storage scan should stay unavailable-here until passive local Xunlai access is found.",
    )
    _expect(
        widget._get_preview_unavailable_here_reason(
            material_entry,
            availability_here=availability_here,
            plan=widget.preview_plan,
        ) == "Material Trader not available here.",
        "Unavailable projected trader rows should explain which local service is missing.",
    )
    _expect(
        widget._get_preview_unavailable_here_reason(
            rune_entry,
            availability_here=availability_here,
            plan=widget.preview_plan,
        ) == "Xunlai Storage not available here.",
        "Projected rune rows that only lack passive local storage access should explain that Xunlai is the missing local dependency.",
    )

    widget._has_local_storage_access = lambda: True
    availability_here = widget._get_preview_here_availability()

    _expect(
        widget._is_preview_entry_available_here(
            storage_entry,
            availability_here=availability_here,
            plan=widget.preview_plan,
        ),
        "Projected storage rows should turn available-here once passive local Xunlai access is resolved.",
    )
    _expect(
        widget._is_preview_entry_available_here(
            rune_entry,
            availability_here=availability_here,
            plan=widget.preview_plan,
        ),
        "Rune trader buys should turn available-here once both the trader and passive local Xunlai access are available.",
    )
    _expect(
        widget._get_preview_unavailable_here_reason(
            merchant_entry,
            availability_here=availability_here,
            plan=widget.preview_plan,
        ) == "",
        "Rows that are available here should not show an extra unavailable-here explanation.",
    )


def _test_supported_context_generic_services_fall_back_to_name_queries(module) -> None:
    original_get_map_id = module.Map.GetMapID
    original_is_map_ready = module.Map.IsMapReady
    original_is_outpost = module.Map.IsOutpost
    original_is_guild_hall = module.Map.IsGuildHall
    original_get_map_name = module.Map.GetMapName
    original_default_selectors = dict(module.DEFAULT_NPC_SELECTORS)
    original_resolve_agent_xy = module.resolve_agent_xy_from_step

    try:
        module.Map.GetMapID = lambda: 55
        module.Map.IsMapReady = lambda: True
        module.Map.IsOutpost = lambda: True
        module.Map.IsGuildHall = lambda: False
        module.Map.GetMapName = lambda map_id=0: f"Map {int(map_id)}"
        module.DEFAULT_NPC_SELECTORS.clear()
        module.DEFAULT_NPC_SELECTORS.update({
            "merchant": "merchant_selector",
            "materials": "materials_selector",
            "rare_materials": "rare_selector",
        })

        widget = _make_widget(module)
        widget._resolve_rune_trader_coords = lambda _map_id, **_kwargs: None
        resolve_calls: list[tuple[object, object, object]] = []

        def _fake_resolve(step, **kwargs):
            resolve_calls.append((step.get("npc"), step.get("target"), kwargs.get("default_max_dist")))
            if step.get("npc") in {"merchant_selector", "materials_selector", "rare_selector"}:
                return None
            return {
                module.MERCHANT_NAME_QUERY: (10.0, 10.0),
                module.MATERIAL_TRADER_NAME_QUERY: (20.0, 20.0),
                module.RARE_MATERIAL_TRADER_NAME_QUERY: (30.0, 30.0),
            }.get(step.get("target"))

        module.resolve_agent_xy_from_step = _fake_resolve
        supported, reason, coords = widget._get_supported_context()

        _expect(supported, "Name-query fallback should keep the map supported when current services are available.")
        _expect(coords[module.MERCHANT_TYPE_MERCHANT] == (10.0, 10.0), "Merchant fallback should resolve the local merchant tag.")
        _expect(coords[module.MERCHANT_TYPE_MATERIALS] == (20.0, 20.0), "Material-trader fallback should resolve the local trader tag.")
        _expect(coords[module.MERCHANT_TYPE_RARE_MATERIALS] == (30.0, 30.0), "Rare-trader fallback should resolve the local trader tag.")
        _expect(
            all(call[2] == module.OUTPOST_SERVICE_SEARCH_MAX_DIST for call in resolve_calls),
            "Current-map service resolution should search the full outpost range when checking local availability.",
        )
        _expect(
            any(call[1] == module.MERCHANT_NAME_QUERY for call in resolve_calls),
            "Merchant fallback should try the local merchant tag when the generic selector misses.",
        )
        _expect(
            any(call[1] == module.MATERIAL_TRADER_NAME_QUERY for call in resolve_calls),
            "Material-trader fallback should try the local material-trader tag when the generic selector misses.",
        )
        _expect(
            any(call[1] == module.RARE_MATERIAL_TRADER_NAME_QUERY for call in resolve_calls),
            "Rare-trader fallback should try the local rare-trader tag when the generic selector misses.",
        )
        _expect(
            "Partial merchant/trader resolution succeeded." in reason,
            "Fallback-supported maps should still explain when some services, like Rune Trader, remain unresolved.",
        )
    finally:
        module.Map.GetMapID = original_get_map_id
        module.Map.IsMapReady = original_is_map_ready
        module.Map.IsOutpost = original_is_outpost
        module.Map.IsGuildHall = original_is_guild_hall
        module.Map.GetMapName = original_get_map_name
        module.DEFAULT_NPC_SELECTORS.clear()
        module.DEFAULT_NPC_SELECTORS.update(original_default_selectors)
        module.resolve_agent_xy_from_step = original_resolve_agent_xy


def _test_execute_here_ignores_travel_and_reports_local_summary(module) -> None:
    widget = _make_widget(module)
    widget.auto_travel_enabled = True
    widget.target_outpost_id = 2
    widget.sell_rules = [
        module._normalize_sell_rule(
            module.SellRule(
                enabled=True,
                kind=module.SELL_KIND_EXPLICIT_MODELS,
                whitelist_targets=[module.WhitelistTarget(model_id=111, keep_count=0)],
            )
        )
    ]
    widget.cleanup_targets = [module.CleanupTarget(model_id=222, keep_on_character=0)]
    widget._get_supported_context = lambda: (
        True,
        "Ready",
        {
            module.MERCHANT_TYPE_MERCHANT: (1.0, 1.0),
            module.MERCHANT_TYPE_MATERIALS: None,
            module.MERCHANT_TYPE_RUNE_TRADER: None,
            module.MERCHANT_TYPE_RARE_MATERIALS: None,
        },
    )
    widget._collect_inventory_items = lambda: [
        _make_item(module, item_id=410, model_id=111, name="Iron Sword", quantity=1),
        _make_item(module, item_id=420, model_id=222, name="Bone", quantity=1),
    ]

    travel_calls: list[int] = []
    merchant_sell_ids: list[int] = []
    storage_phase_calls: list[str] = []
    widget._has_local_storage_access = lambda: False

    def _capture_travel(outpost_id: int):
        travel_calls.append(int(outpost_id))
        if False:
            yield None
        return True

    def _capture_merchant_sell(_coords, item_ids):
        merchant_sell_ids.extend(int(item_id) for item_id in item_ids)
        if False:
            yield None
        return module.ExecutionPhaseOutcome(label="Merchant sells", measure_label="items", attempted=len(item_ids), completed=len(item_ids))

    def _capture_storage_transfers(_transfers, *, phase_label="Storage transfers"):
        storage_phase_calls.append(phase_label)
        if False:
            yield None
        return module.ExecutionPhaseOutcome(label=phase_label, measure_label="items", attempted=0, completed=0)

    widget._travel_to_target_outpost = _capture_travel
    widget._execute_merchant_sell_phase = _capture_merchant_sell
    widget._execute_storage_transfers = _capture_storage_transfers

    _drain_generator_return(widget._execute_now(local_only=True))

    _expect(not travel_calls, "Execute Here should rebuild a fresh local plan without traveling to the configured target outpost.")
    _expect(merchant_sell_ids == [410], "Execute Here should still run the locally available merchant work.")
    _expect(not storage_phase_calls, "Execute Here should skip local Xunlai work when no local storage source is available.")
    _expect(
        "Execute Here: 1 local action(s) | 1 skipped / unavailable." in widget.last_execution_summary,
        "Execute Here should report how many local actions ran versus how many projected or unavailable steps were skipped.",
    )
    _expect(
        widget.status_message == "Execute Here finished. Preview again to refresh the post-run state.",
        "Execute Here should finish with the dedicated local-execution status message.",
    )


def _test_build_plan_deposits_material_keep_remainder_to_storage(module) -> None:
    widget = _make_widget(module)
    widget.catalog_by_model_id[921] = {"model_id": 921, "name": "Wood Plank", "material_type": "common"}
    widget.sell_rules = [
        module._normalize_sell_rule(
            module.SellRule(
                enabled=True,
                kind=module.SELL_KIND_COMMON_MATERIALS,
                whitelist_targets=[
                    module.WhitelistTarget(model_id=921, keep_count=25, deposit_to_storage=True),
                ],
            )
        )
    ]
    widget._get_supported_context = lambda: (
        True,
        "Ready",
        {
            module.MERCHANT_TYPE_MERCHANT: (1.0, 1.0),
            module.MERCHANT_TYPE_MATERIALS: (2.0, 2.0),
            module.MERCHANT_TYPE_RUNE_TRADER: (3.0, 3.0),
            module.MERCHANT_TYPE_RARE_MATERIALS: (4.0, 4.0),
        },
    )
    original_inventory = getattr(module.GLOBAL_CACHE, "Inventory", None)
    try:
        module.GLOBAL_CACHE.Inventory = types.SimpleNamespace(IsStorageOpen=lambda: False)
        widget._collect_inventory_items = lambda: [
            _make_item(module, item_id=320, model_id=921, name="Wood Plank", quantity=40, is_material=True),
        ]

        plan = widget._build_plan()

        _expect(len(plan.material_sales) == 1 and plan.material_sales[0].quantity_to_sell == 10, "Material keep targets should still preserve the existing trader sale quantity.")
        deposit_transfers = [transfer for transfer in plan.storage_transfers if transfer.direction == module.STORAGE_TRANSFER_DEPOSIT]
        _expect(
            len(deposit_transfers) == 1 and deposit_transfers[0].item_id == 320 and deposit_transfers[0].quantity == 30,
            "Material keep targets should deposit only the kept remainder quantity to regular Xunlai storage.",
        )
        _expect(
            any(entry.state == module.PLAN_STATE_SKIPPED and entry.label == "Wood Plank" and entry.quantity == 30 for entry in plan.entries),
            "Preview should still show the kept material remainder before it is deposited.",
        )
    finally:
        module.GLOBAL_CACHE.Inventory = original_inventory


def _test_execute_storage_transfers_tracks_partial_moves(module) -> None:
    widget = _make_widget(module)
    quantities = {330: 30}
    original_item = getattr(module.GLOBAL_CACHE, "Item", None)
    original_inventory = getattr(module.GLOBAL_CACHE, "Inventory", None)
    try:
        module.GLOBAL_CACHE.Item = types.SimpleNamespace(
            Properties=types.SimpleNamespace(
                GetQuantity=lambda item_id: int(quantities.get(int(item_id), 0)),
            )
        )

        def _partial_deposit(item_id: int, **_kwargs) -> bool:
            quantities[int(item_id)] = 10
            return True

        module.GLOBAL_CACHE.Inventory = types.SimpleNamespace(
            DepositItemToStorage=_partial_deposit,
            WithdrawItemFromStorage=lambda *_args, **_kwargs: False,
        )

        def _wait_for_queue(*_args, **_kwargs):
            if False:
                yield None
            return True

        widget._wait_for_action_queue_empty = _wait_for_queue

        def _wait_for_target(item_id: int, _expected_quantity: int, **_kwargs):
            if False:
                yield None
            return int(quantities.get(int(item_id), 0))

        widget._wait_for_stack_quantity_target = _wait_for_target

        outcome = _drain_generator_return(
            widget._execute_storage_transfers(
                [
                    module.PlannedStorageTransfer(
                        direction=module.STORAGE_TRANSFER_DEPOSIT,
                        key="item:330",
                        label="Wood Plank",
                        item_id=330,
                        quantity=25,
                    )
                ],
                phase_label="Storage deposits",
            )
        )

        _expect(
            outcome.completed == 20 and outcome.timeout_failures == 5,
            "Storage transfer execution should count only the quantity that actually moved and report the shortfall separately.",
        )
    finally:
        module.GLOBAL_CACHE.Item = original_item
        module.GLOBAL_CACHE.Inventory = original_inventory


def _install_material_storage_execution_stubs(
    module,
    widget,
    *,
    source_item_id: int = 330,
    model_id: int = 921,
    source_quantity: int = 40,
    storage_quantity: int | None = None,
    storage_slot: int = 0,
    is_material: bool = True,
    is_rare_material: bool = False,
    verify_material_move: bool = True,
):
    quantities = {int(source_item_id): int(source_quantity)}
    storage_item_id = 9330
    if storage_quantity is not None:
        quantities[storage_item_id] = int(storage_quantity)
    calls: dict[str, list[tuple[int, int, int, int] | tuple[int, int]]] = {
        "material_moves": [],
        "regular_deposits": [],
    }
    original_item = getattr(module.GLOBAL_CACHE, "Item", None)
    original_item_array = getattr(module.GLOBAL_CACHE, "ItemArray", None)
    original_inventory = getattr(module.GLOBAL_CACHE, "Inventory", None)

    def _get_model_id(item_id: int) -> int:
        safe_item_id = int(item_id)
        if safe_item_id in (int(source_item_id), storage_item_id):
            return int(model_id)
        return 0

    def _get_quantity(item_id: int) -> int:
        return max(0, int(quantities.get(int(item_id), 0)))

    def _move_item(item_id: int, bag_id: int, slot: int, quantity: int = 1) -> bool:
        safe_quantity = max(0, int(quantity))
        calls["material_moves"].append((int(item_id), int(bag_id), int(slot), safe_quantity))
        if verify_material_move:
            quantities[int(item_id)] = max(0, int(quantities.get(int(item_id), 0)) - safe_quantity)
        return True

    def _deposit_item_to_storage(item_id: int, **kwargs) -> bool:
        requested = max(0, int(kwargs.get("ammount", kwargs.get("amount", -1))))
        current = max(0, int(quantities.get(int(item_id), 0)))
        if requested < 0:
            requested = current
        moved = min(current, requested)
        calls["regular_deposits"].append((int(item_id), moved))
        quantities[int(item_id)] = max(0, current - moved)
        return moved > 0

    module.GLOBAL_CACHE.Item = types.SimpleNamespace(
        GetModelID=_get_model_id,
        GetSlot=lambda item_id: int(storage_slot) if int(item_id) == storage_item_id else 0,
        Properties=types.SimpleNamespace(GetQuantity=_get_quantity),
        Type=types.SimpleNamespace(
            IsMaterial=lambda item_id: bool(is_material),
            IsRareMaterial=lambda item_id: bool(is_rare_material),
        ),
    )
    module.GLOBAL_CACHE.ItemArray = types.SimpleNamespace(
        CreateBagList=lambda *bag_ids: list(bag_ids),
        GetItemArray=lambda _bags: [storage_item_id] if storage_quantity is not None else [],
    )
    module.GLOBAL_CACHE.Inventory = types.SimpleNamespace(
        MoveItem=_move_item,
        DepositItemToStorage=_deposit_item_to_storage,
        WithdrawItemFromStorage=lambda *_args, **_kwargs: False,
    )

    widget._get_inventory_stack_quantities = lambda item_ids: {
        int(item_id): max(0, int(quantities.get(int(item_id), 0)))
        for item_id in item_ids
        if int(item_id) == int(source_item_id) and max(0, int(quantities.get(int(item_id), 0))) > 0
    }

    def _wait_for_queue(*_args, **_kwargs):
        if False:
            yield None
        return True

    def _wait_for_target(item_id: int, _expected_quantity: int, **_kwargs):
        if False:
            yield None
        return max(0, int(quantities.get(int(item_id), 0)))

    widget._wait_for_action_queue_empty = _wait_for_queue
    widget._wait_for_stack_quantity_target = _wait_for_target
    widget._wait_for_inventory_source_stack_quantity_target = _wait_for_target

    def _restore() -> None:
        module.GLOBAL_CACHE.Item = original_item
        module.GLOBAL_CACHE.ItemArray = original_item_array
        module.GLOBAL_CACHE.Inventory = original_inventory

    return quantities, calls, _restore


def _execute_single_deposit_transfer(module, widget, *, item_id: int = 330, quantity: int = 25, model_id: int = 921):
    return _drain_generator_return(
        widget._execute_storage_transfers(
            [
                module.PlannedStorageTransfer(
                    direction=module.STORAGE_TRANSFER_DEPOSIT,
                    key=f"item:{int(item_id)}",
                    label="Bone",
                    item_id=int(item_id),
                    quantity=int(quantity),
                    model_id=int(model_id),
                )
            ],
            phase_label="Storage deposits",
        )
    )


def _test_execute_storage_transfers_deposits_material_storage_first_when_space_exists(module) -> None:
    widget = _make_widget(module)
    _quantities, calls, restore = _install_material_storage_execution_stubs(module, widget)
    try:
        outcome = _execute_single_deposit_transfer(module, widget)

        _expect(outcome.completed == 25 and outcome.timeout_failures == 0, "Material Storage should complete the whole requested material deposit when space exists.")
        _expect(calls["material_moves"] == [(330, module.MATERIAL_STORAGE_BAG_ID, 0, 25)], "Material cleanup should move to Material Storage first.")
        _expect(calls["regular_deposits"] == [], "Regular Xunlai item-pane deposit should not run when Material Storage accepts the full amount.")
    finally:
        restore()


def _test_execute_storage_transfers_uses_live_material_storage_scan_over_stale_cache(module) -> None:
    widget = _make_widget(module)
    _quantities, calls, restore = _install_material_storage_execution_stubs(
        module,
        widget,
        model_id=929,
        storage_quantity=module.MATERIAL_STORAGE_MAX_STACK_SIZE,
        storage_slot=9,
    )
    original_pyinventory = sys.modules.get("PyInventory")

    class _LiveMaterialBag:
        def __init__(self, _bag_id, _bag_name):
            pass

        def GetItems(self):
            return []

        def GetSize(self):
            return 38

    sys.modules["PyInventory"] = types.SimpleNamespace(Bag=_LiveMaterialBag)
    try:
        outcome = _execute_single_deposit_transfer(module, widget, model_id=929)

        _expect(outcome.completed == 25 and outcome.timeout_failures == 0, "Live Material Storage scan should override stale cache data that incorrectly looks full.")
        _expect(calls["material_moves"] == [(330, module.MATERIAL_STORAGE_BAG_ID, 9, 25)], "Glittering Dust should move to its Material Storage slot when live storage has room.")
        _expect(calls["regular_deposits"] == [], "Stale full cache data must not force regular item-pane fallback when live Material Storage has room.")
    finally:
        if original_pyinventory is None:
            sys.modules.pop("PyInventory", None)
        else:
            sys.modules["PyInventory"] = original_pyinventory
        restore()


def _test_execute_storage_transfers_probes_material_storage_when_quantity_reports_full(module) -> None:
    widget = _make_widget(module)
    _quantities, calls, restore = _install_material_storage_execution_stubs(
        module,
        widget,
        storage_quantity=module.MATERIAL_STORAGE_MAX_STACK_SIZE,
    )
    try:
        outcome = _execute_single_deposit_transfer(module, widget)

        _expect(outcome.completed == 25 and outcome.timeout_failures == 0, "A reported-full Material Storage quantity should still probe the known material slot before fallback.")
        _expect(calls["material_moves"] == [(330, module.MATERIAL_STORAGE_BAG_ID, 0, 25)], "Known material slots should be probed even when the quantity scan reports full.")
        _expect(calls["regular_deposits"] == [], "Reported-full Material Storage scans must not cause immediate regular item-pane fallback.")
    finally:
        restore()


def _test_execute_storage_transfers_partially_fills_material_storage_then_falls_back(module) -> None:
    widget = _make_widget(module)
    _quantities, calls, restore = _install_material_storage_execution_stubs(
        module,
        widget,
        storage_quantity=240,
    )
    try:
        outcome = _execute_single_deposit_transfer(module, widget)

        _expect(outcome.completed == 25 and outcome.timeout_failures == 0, "Partial Material Storage capacity plus regular fallback should complete the requested deposit.")
        _expect(calls["material_moves"] == [(330, module.MATERIAL_STORAGE_BAG_ID, 0, 10)], "Material Storage should receive only its available capacity first.")
        _expect(calls["regular_deposits"] == [(330, 15)], "Only the verified remainder should fall back to regular storage panes.")
    finally:
        restore()


def _test_execute_storage_transfers_non_material_uses_regular_storage_only(module) -> None:
    widget = _make_widget(module)
    _quantities, calls, restore = _install_material_storage_execution_stubs(
        module,
        widget,
        model_id=111,
        is_material=False,
    )
    try:
        outcome = _execute_single_deposit_transfer(module, widget, model_id=111)

        _expect(outcome.completed == 25 and outcome.timeout_failures == 0, "Non-material cleanup should keep using regular storage panes.")
        _expect(calls["material_moves"] == [], "Non-material deposits should not attempt Material Storage.")
        _expect(calls["regular_deposits"] == [(330, 25)], "Non-material deposits should call the existing regular storage helper.")
    finally:
        restore()


def _test_execute_storage_transfers_unverified_material_move_skips_regular_fallback(module) -> None:
    widget = _make_widget(module)
    _quantities, calls, restore = _install_material_storage_execution_stubs(
        module,
        widget,
        verify_material_move=False,
    )
    try:
        outcome = _execute_single_deposit_transfer(module, widget)

        _expect(outcome.completed == 0 and outcome.timeout_failures == 25, "Unverified Material Storage moves should report the requested deposit as unresolved.")
        _expect(calls["material_moves"] == [(330, module.MATERIAL_STORAGE_BAG_ID, 0, 25)], "The Material Storage move should be attempted first.")
        _expect(calls["regular_deposits"] == [], "Regular storage fallback must be skipped when the Material Storage move cannot be verified.")
    finally:
        restore()


def _test_execute_now_runs_storage_deposits_as_final_phase(module) -> None:
    widget = _make_widget(module)
    widget.sell_rules = [
        module._normalize_sell_rule(
            module.SellRule(
                enabled=True,
                kind=module.SELL_KIND_EXPLICIT_MODELS,
                whitelist_targets=[
                    module.WhitelistTarget(model_id=111, keep_count=1, deposit_to_storage=True),
                ],
            )
        )
    ]
    widget._get_supported_context = lambda: (
        True,
        "Ready",
        {
            module.MERCHANT_TYPE_MERCHANT: (1.0, 1.0),
            module.MERCHANT_TYPE_MATERIALS: (2.0, 2.0),
            module.MERCHANT_TYPE_RUNE_TRADER: (3.0, 3.0),
            module.MERCHANT_TYPE_RARE_MATERIALS: (4.0, 4.0),
        },
    )
    widget._collect_inventory_items = lambda: [
        _make_item(module, item_id=340, model_id=111, name="Iron Sword", quantity=1),
    ]
    open_state = {"open": False}
    open_calls: list[str] = []
    phase_calls: list[str] = []
    original_inventory = getattr(module.GLOBAL_CACHE, "Inventory", None)
    try:
        def _open_xunlai() -> None:
            open_calls.append("open")
            open_state["open"] = True

        module.GLOBAL_CACHE.Inventory = types.SimpleNamespace(
            IsStorageOpen=lambda: bool(open_state["open"]),
            OpenXunlaiWindow=_open_xunlai,
        )

        def _capture_storage_transfers(transfers, *, phase_label="Storage transfers"):
            phase_calls.append(phase_label)
            if False:
                yield None
            return module.ExecutionPhaseOutcome(
                label=phase_label,
                measure_label="items",
                attempted=sum(int(transfer.quantity) for transfer in transfers),
                completed=sum(int(transfer.quantity) for transfer in transfers),
            )

        widget._execute_storage_transfers = _capture_storage_transfers

        _drain_generator_return(widget._execute_now())

        _expect(phase_calls == ["Storage deposits"], "Execute should run deposit cleanup in the dedicated final storage-deposit phase.")
        _expect(open_calls == ["open"], "Execute should open Xunlai once when planned deposits need storage access.")
    finally:
        module.GLOBAL_CACHE.Inventory = original_inventory


def _test_rule_custom_names_persist_and_fallback_cleanly(module, temp_root: Path) -> None:
    widget = _make_widget(module)
    config_path = temp_root / "named_rules_profile.json"
    widget.config_path = str(config_path)
    widget.buy_rules = [
        module._normalize_buy_rule(
            module.BuyRule(
                enabled=True,
                kind=module.BUY_KIND_MERCHANT_STOCK,
                model_id=555,
                target_count=2,
                max_per_run=1,
                name="Cleanup Stock",
            )
        ),
        module._normalize_buy_rule(
            module.BuyRule(
                enabled=True,
                kind=module.BUY_KIND_MATERIAL_TARGET,
            )
        ),
    ]
    widget.sell_rules = [
        module._normalize_sell_rule(
            module.SellRule(
                enabled=True,
                kind=module.SELL_KIND_WEAPONS,
                name="Low Req Keep",
            )
        ),
        module._normalize_sell_rule(
            module.SellRule(
                enabled=True,
                kind=module.SELL_KIND_EXPLICIT_MODELS,
                model_ids=[111],
                name="",
            )
        ),
    ]

    _expect(widget._save_profile(), "Saving a profile with custom rule names should succeed.")
    saved_payload = json.loads(config_path.read_text(encoding="utf-8"))
    _expect(saved_payload["buy_rules"][0]["name"] == "Cleanup Stock", "Saved profiles should persist custom buy-rule names.")
    _expect(saved_payload["sell_rules"][0]["name"] == "Low Req Keep", "Saved profiles should persist custom sell-rule names.")
    _expect(saved_payload["sell_rules"][1]["name"] == "", "Unnamed rules should still serialize with an empty custom-name field for stable round-tripping.")

    reloaded_widget = _make_widget(module)
    reloaded_widget.config_path = str(config_path)
    reloaded_widget._load_profile()

    _expect(reloaded_widget.buy_rules[0].name == "Cleanup Stock", "Reload should restore custom buy-rule names from disk.")
    _expect(reloaded_widget.sell_rules[0].name == "Low Req Keep", "Reload should restore custom sell-rule names from disk.")
    _expect(reloaded_widget.sell_rules[1].name == "", "Reload should keep unnamed rules blank instead of inventing labels.")
    _expect(
        reloaded_widget._get_rule_display_label(reloaded_widget.buy_rules[0], module.BUY_KIND_LABELS[module.BUY_KIND_MERCHANT_STOCK]) == "Cleanup Stock",
        "Named rules should use their custom label in the shared rule-header display path.",
    )
    _expect(
        reloaded_widget._get_rule_display_label(reloaded_widget.sell_rules[1], module.SELL_KIND_LABELS[module.SELL_KIND_EXPLICIT_MODELS]) == module.SELL_KIND_LABELS[module.SELL_KIND_EXPLICIT_MODELS],
        "Blank custom names should fall back to the existing generated rule label.",
    )
    _expect(
        reloaded_widget._format_sell_rule_reference(0, reloaded_widget.sell_rules[0]) == "Low Req Keep (#1)",
        "Named rule references should prefer only the custom label plus the stable rule number.",
    )


def _test_item_handling_catalog_migration_loads_primary_catalog_and_modelid_fallback(module) -> None:
    original_paths = {
        "CATALOG_PATH": module.CATALOG_PATH,
        "ITEMS_CATALOG_PATH": module.ITEMS_CATALOG_PATH,
        "DROP_DATA_PATH": module.DROP_DATA_PATH,
        "ITEM_HANDLING_ITEMS_CATALOG_PATH": module.ITEM_HANDLING_ITEMS_CATALOG_PATH,
        "RUNES_CATALOG_PATH": module.RUNES_CATALOG_PATH,
    }
    try:
        module.CATALOG_PATH = str(REPO_ROOT / "Widgets" / "Data" / "merchant_rules_catalog.json")
        module.ITEMS_CATALOG_PATH = str(REPO_ROOT / "Widgets" / "Data" / "merchant_rules_items_catalog.json")
        module.DROP_DATA_PATH = str(REPO_ROOT / "Widgets" / "Data" / "modelid_drop_data.json")
        module.ITEM_HANDLING_ITEMS_CATALOG_PATH = str(REPO_ROOT / "Sources" / "frenkeyLib" / "ItemHandling" / "Items" / "items.json")
        module.RUNES_CATALOG_PATH = str(REPO_ROOT / "Sources" / "marks_sources" / "mods_data" / "runes.json")

        item_handling_catalog = json.loads(Path(module.ITEM_HANDLING_ITEMS_CATALOG_PATH).read_text(encoding="utf-8"))
        item_handling_entries = module._iter_item_handling_catalog_entries(item_handling_catalog)
        item_handling_model_ids = _catalog_model_ids(item_handling_entries)

        _expect(
            len(item_handling_model_ids) > 3600,
            "ItemHandling items.json should provide the broad searchable item catalog without requiring the old Merchant Rules mirror.",
        )
        _expect(
            {400, 2989, int(module.ECTOPLASM_MODEL_ID)}.issubset(item_handling_model_ids),
            "ItemHandling items.json should cover known searchable catalog items and curated override ids.",
        )
        _expect(
            399 not in item_handling_model_ids,
            "Crystalline Sword should remain a ModelID-fallback case until richer catalog metadata is added.",
        )

        legacy_catalog_path = Path(module.ITEMS_CATALOG_PATH)
        if legacy_catalog_path.exists():
            legacy_catalog = json.loads(legacy_catalog_path.read_text(encoding="utf-8"))
            legacy_model_ids = _catalog_model_ids(list(legacy_catalog.get("items", [])))
            _expect(
                len(item_handling_model_ids) > len(legacy_model_ids),
                "ItemHandling items.json should contribute more unique model ids than the deprecated Merchant Rules item mirror.",
            )
            _expect(
                legacy_model_ids.issubset(item_handling_model_ids),
                "The deprecated Merchant Rules item mirror should remain covered by ItemHandling items.json while it exists.",
            )

        widget = _make_widget(module)
        widget._load_catalog()

        _expect(widget.catalog_stats.get("item_handling_present") is True, "Merchant Rules should detect the ItemHandling catalog file.")
        _expect(
            int(widget.catalog_stats.get("item_handling_items", 0)) > 3600,
            "Merchant Rules should load the broader ItemHandling catalog as the primary searchable catalog.",
        )
        _expect(
            int(widget.catalog_stats.get("mirrored_items", 0)) == 0,
            "Merchant Rules should not load the deprecated mirror during normal catalog loading.",
        )
        _expect(
            widget.catalog_stats.get("mirrored_deprecated_fallback_used") is False,
            "The deprecated mirror fallback should remain idle when items.json loads successfully.",
        )

        fellblade_entry = widget.catalog_by_model_id.get(400, {})
        _expect(fellblade_entry.get("source") == "item_handling_items_catalog", "ItemHandling entries should win over the legacy mirror for shared model ids.")
        _expect(fellblade_entry.get("name") == "Fellblade", "ItemHandling entries should preserve display names.")
        _expect(fellblade_entry.get("item_type") == "Sword", "ItemHandling entries should preserve item types.")
        _expect(fellblade_entry.get("skin") == "Fellblade.png", "ItemHandling entries should preserve skin names for search aliases.")
        _expect(fellblade_entry.get("wiki_url") == "https://wiki.guildwars.com/wiki/Fellblade", "ItemHandling entries should preserve wiki urls.")
        _expect(fellblade_entry.get("attributes") == ["Swordsmanship"], "ItemHandling entries should preserve attributes without using name_encoded.")
        _expect("name_encoded" not in fellblade_entry, "Merchant Rules should ignore name_encoded in ItemHandling entries.")

        trophy_entry = widget.catalog_by_model_id.get(852, {})
        _expect(trophy_entry.get("category") == "Trophy", "ItemHandling category metadata should be preserved when present.")

        _expect(
            widget.catalog_by_model_id.get(int(module.ECTOPLASM_MODEL_ID), {}).get("source") == "merchant_rules_catalog.rare",
            "Curated Merchant Rules material entries should still override broad catalog entries.",
        )
        _expect(
            widget.catalog_by_model_id.get(2989, {}).get("source") == "merchant_rules_catalog.essentials",
            "Curated Merchant Rules merchant entries should still override broad catalog entries.",
        )

        crystalline_entry = widget.catalog_by_model_id.get(399, {})
        _expect(crystalline_entry.get("source") == "modelid_enum_fallback", "Missing rich catalog items should be added from ModelID fallback.")
        _expect(crystalline_entry.get("name") == "Crystalline Sword", "CamelCase ModelID fallback names should be humanized for display/search.")
        _expect(crystalline_entry.get("item_type") == "Sword", "ModelID fallback should infer obvious weapon item types from enum names.")

        for query in ("Crystalline Sword", "CrystallineSword", "Crystalline_Sword", "399"):
            matches = widget._search_catalog(query, limit=max(1, len(widget.catalog_by_model_id)))
            _expect(
                399 in {int(entry.get("model_id", 0)) for entry in matches},
                f"Catalog search should find Crystalline Sword fallback entries by {query!r}.",
            )

        for query in ("Fellblade", "Fellblade.png", "400", "Sword"):
            matches = widget._search_catalog(query, limit=max(1, len(widget.catalog_by_model_id)))
            _expect(
                400 in {int(entry.get("model_id", 0)) for entry in matches},
                f"Catalog search should find ItemHandling entries by {query!r}.",
            )
    finally:
        for name, value in original_paths.items():
            setattr(module, name, value)


def _test_catalog_loads_without_deprecated_mirrored_item_catalog(module, temp_root: Path) -> None:
    original_paths = {
        "CATALOG_PATH": module.CATALOG_PATH,
        "ITEMS_CATALOG_PATH": module.ITEMS_CATALOG_PATH,
        "DROP_DATA_PATH": module.DROP_DATA_PATH,
        "ITEM_HANDLING_ITEMS_CATALOG_PATH": module.ITEM_HANDLING_ITEMS_CATALOG_PATH,
        "RUNES_CATALOG_PATH": module.RUNES_CATALOG_PATH,
    }
    try:
        module.CATALOG_PATH = str(REPO_ROOT / "Widgets" / "Data" / "merchant_rules_catalog.json")
        module.ITEMS_CATALOG_PATH = str(temp_root / "missing" / "merchant_rules_items_catalog.json")
        module.DROP_DATA_PATH = str(REPO_ROOT / "Widgets" / "Data" / "modelid_drop_data.json")
        module.ITEM_HANDLING_ITEMS_CATALOG_PATH = str(REPO_ROOT / "Sources" / "frenkeyLib" / "ItemHandling" / "Items" / "items.json")
        module.RUNES_CATALOG_PATH = str(REPO_ROOT / "Sources" / "marks_sources" / "mods_data" / "runes.json")

        _expect(not Path(module.ITEMS_CATALOG_PATH).exists(), "The deprecated mirror path should be missing for this regression check.")

        widget = _make_widget(module)
        widget._load_catalog()

        _expect(widget.catalog_stats.get("item_handling_present") is True, "items.json should still be present for the missing-mirror test.")
        _expect(widget.catalog_stats.get("mirrored_present") is False, "The deprecated mirror should be reported missing when the file is absent.")
        _expect(int(widget.catalog_stats.get("mirrored_items", 0)) == 0, "A missing deprecated mirror should not add catalog entries.")
        _expect(
            widget.catalog_stats.get("mirrored_deprecated_fallback_used") is False,
            "A missing deprecated mirror should not be treated as a used fallback when items.json loads.",
        )
        _expect(
            all(entry.get("source") != "merchant_rules_items_catalog" for entry in widget.catalog_by_model_id.values()),
            "Catalog contents should not depend on the deprecated Merchant Rules mirror.",
        )

        for query, expected_model_id in (
            ("Fellblade", 400),
            ("Fellblade.png", 400),
            ("Sword", 400),
            ("Identification Kit", 2989),
            ("Glob of Ectoplasm", int(module.ECTOPLASM_MODEL_ID)),
            ("Crystalline Sword", 399),
            ("CrystallineSword", 399),
            ("399", 399),
        ):
            matches = widget._search_catalog(query, limit=max(1, len(widget.catalog_by_model_id)))
            _expect(
                expected_model_id in {int(entry.get("model_id", 0)) for entry in matches},
                f"Catalog search should find model {expected_model_id} by {query!r} without the deprecated mirror.",
            )

        _expect(
            widget.catalog_by_model_id.get(399, {}).get("source") == "modelid_enum_fallback",
            "ModelID fallback should provide Crystalline Sword when richer catalogs do not.",
        )
        _expect(
            widget.catalog_by_model_id.get(400, {}).get("source") == "item_handling_items_catalog",
            "items.json should provide Fellblade without the deprecated mirror.",
        )
    finally:
        for name, value in original_paths.items():
            setattr(module, name, value)


def _test_scroll_of_heros_insight_wins_duplicate_model_id_and_searches(module) -> None:
    original_paths = {
        "CATALOG_PATH": module.CATALOG_PATH,
        "ITEMS_CATALOG_PATH": module.ITEMS_CATALOG_PATH,
        "DROP_DATA_PATH": module.DROP_DATA_PATH,
        "ITEM_HANDLING_ITEMS_CATALOG_PATH": module.ITEM_HANDLING_ITEMS_CATALOG_PATH,
        "RUNES_CATALOG_PATH": module.RUNES_CATALOG_PATH,
    }
    try:
        module.CATALOG_PATH = str(REPO_ROOT / "Widgets" / "Data" / "merchant_rules_catalog.json")
        module.ITEMS_CATALOG_PATH = str(REPO_ROOT / "Widgets" / "Data" / "merchant_rules_items_catalog.json")
        module.DROP_DATA_PATH = str(REPO_ROOT / "Widgets" / "Data" / "modelid_drop_data.json")
        module.ITEM_HANDLING_ITEMS_CATALOG_PATH = str(REPO_ROOT / "Sources" / "frenkeyLib" / "ItemHandling" / "Items" / "items.json")
        module.RUNES_CATALOG_PATH = str(REPO_ROOT / "Sources" / "marks_sources" / "mods_data" / "runes.json")

        scroll_model_id = int(module.ModelID.Scroll_Of_Heros_Insight.value)
        item_handling_catalog = json.loads(Path(module.ITEM_HANDLING_ITEMS_CATALOG_PATH).read_text(encoding="utf-8"))
        duplicate_rows = [
            entry
            for entry in module._iter_item_handling_catalog_entries(item_handling_catalog)
            if int(entry.get("model_id", 0) or 0) == scroll_model_id
        ]
        _expect(
            {str(entry.get("name", "")) for entry in duplicate_rows} >= {"Salvage Kit", "Scroll of Hero's Insight"},
            "The regression fixture should include both duplicate 5594 rows from items.json.",
        )

        widget = _make_widget(module)
        widget._load_catalog()

        entry = widget.catalog_by_model_id.get(scroll_model_id, {})
        _expect(entry.get("source") == "item_handling_items_catalog", "Scroll of Hero's Insight should come from items.json.")
        _expect(entry.get("name") == "Scroll of Hero's Insight", "Scroll duplicate metadata should win over the bogus Salvage Kit row.")
        _expect(entry.get("item_type") == "Scroll", "Scroll duplicate metadata should preserve the Scroll item type.")
        _expect(entry.get("category") == "Scroll", "Scroll duplicate metadata should preserve the Scroll category.")
        _expect(entry.get("sub_category") == "RareXPScroll", "Scroll duplicate metadata should preserve the rare XP scroll sub-category.")
        _expect(entry.get("skin") == "Scroll of Hero's Insight.png", "Scroll duplicate metadata should preserve the skin alias source.")
        _expect(
            entry.get("wiki_url") == "https://wiki.guildwars.com/wiki/Scroll_of_Hero%27s_Insight",
            "Scroll duplicate metadata should preserve the wiki alias source.",
        )

        alias_labels = entry.get("alias_labels", {})
        _expect(isinstance(alias_labels, dict), "Catalog aliases should be rebuilt for the selected scroll entry.")
        _expect(
            "scroll of hero's insight" in alias_labels,
            "Scroll aliases should include the display/skin/wiki stem with apostrophe intact.",
        )
        _expect("salvage kit" not in alias_labels, "The skipped bogus duplicate should not leave a Salvage Kit alias on model 5594.")

        for query in ("Scroll of Hero", "Hero's Insight", "Scroll of Hero's Insight", "5594"):
            matches = widget._search_catalog(query)
            _expect(
                scroll_model_id in {int(match.get("model_id", 0)) for match in matches},
                f"Generic item catalog search should find Scroll of Hero's Insight by {query!r}.",
            )

        for query in ("Scroll of Hero", "Hero's Insight", "Scroll of Hero's Insight", "5594", "Scroll"):
            matches = widget._search_scroll_trader_stock_catalog(query)
            _expect(
                scroll_model_id in {int(match.get("model_id", 0)) for match in matches},
                f"Scroll trader stock search should find Scroll of Hero's Insight by {query!r}.",
            )
    finally:
        for name, value in original_paths.items():
            setattr(module, name, value)


def _test_display_sorting_helpers_and_summaries_are_case_insensitive(module) -> None:
    widget = _make_widget(module)
    _seed_display_sort_fixture(widget)

    _expect(
        widget._sort_model_ids_for_display([300, 100, 200, 400]) == [100, 400, 200, 300],
        "Display sorting for selected model-id lists should be alphabetical by displayed label with a stable fallback.",
    )
    _expect(
        [
            entry.model_id
            for entry in widget._sort_targets_by_model_label_for_display(
                [
                    module.WeaponRequirementRule(model_id=300, min_requirement=1, max_requirement=8),
                    module.WeaponRequirementRule(model_id=100, min_requirement=1, max_requirement=8),
                    module.WeaponRequirementRule(model_id=200, min_requirement=1, max_requirement=8),
                ]
            )
        ]
        == [100, 200, 300],
        "Display sorting for protected requirement rows should be alphabetical by model label without changing the stored rule order.",
    )
    _expect(
        widget._sort_identifiers_for_display(["mod_z", "mod_b", "mod_a"], widget._get_weapon_mod_label) == ["mod_a", "mod_b", "mod_z"],
        "Display sorting for protected identifiers should be case-insensitive and use the identifier as a stable fallback when names tie.",
    )
    _expect(
        [
            target.identifier
            for target in widget._sort_targets_by_identifier_label_for_display(
                [
                    module.RuneTraderTarget(identifier="rune_z", target_count=0, max_per_run=0),
                    module.RuneTraderTarget(identifier="rune_b", target_count=0, max_per_run=0),
                    module.RuneTraderTarget(identifier="rune_a", target_count=0, max_per_run=0),
                ],
                widget._get_rune_label,
            )
        ]
        == ["rune_a", "rune_b", "rune_z"],
        "Display sorting for rune-target tables should be case-insensitive and stable when labels tie.",
    )

    buy_stock_rule = module._normalize_buy_rule(
        module.BuyRule(
            enabled=True,
            kind=module.BUY_KIND_MERCHANT_STOCK,
            merchant_stock_targets=[
                module.MerchantStockTarget(model_id=300, target_count=0, max_per_run=0),
                module.MerchantStockTarget(model_id=100, target_count=0, max_per_run=0),
                module.MerchantStockTarget(model_id=200, target_count=0, max_per_run=0),
            ],
        )
    )
    buy_material_rule = module._normalize_buy_rule(
        module.BuyRule(
            enabled=True,
            kind=module.BUY_KIND_MATERIAL_TARGET,
            material_targets=[
                module.MaterialTarget(model_id=300, target_count=0, max_per_run=0),
                module.MaterialTarget(model_id=100, target_count=0, max_per_run=0),
                module.MaterialTarget(model_id=200, target_count=0, max_per_run=0),
            ],
        )
    )
    buy_rune_rule = module._normalize_buy_rule(
        module.BuyRule(
            enabled=True,
            kind=module.BUY_KIND_RUNE_TRADER_TARGET,
            rune_targets=[
                module.RuneTraderTarget(identifier="rune_z", target_count=0, max_per_run=0),
                module.RuneTraderTarget(identifier="rune_b", target_count=0, max_per_run=0),
                module.RuneTraderTarget(identifier="rune_a", target_count=0, max_per_run=0),
            ],
        )
    )
    sell_material_rule = module._normalize_sell_rule(
        module.SellRule(
            enabled=True,
            kind=module.SELL_KIND_COMMON_MATERIALS,
            whitelist_targets=[
                module.WhitelistTarget(model_id=300, keep_count=3),
                module.WhitelistTarget(model_id=100, keep_count=1),
                module.WhitelistTarget(model_id=200, keep_count=2),
            ],
        )
    )
    sell_item_rule = module._normalize_sell_rule(
        module.SellRule(
            enabled=True,
            kind=module.SELL_KIND_EXPLICIT_MODELS,
            whitelist_targets=[
                module.WhitelistTarget(model_id=300, keep_count=3),
                module.WhitelistTarget(model_id=100, keep_count=1),
                module.WhitelistTarget(model_id=200, keep_count=2),
            ],
        )
    )
    destroy_material_rule = module._normalize_destroy_rule(
        module.DestroyRule(
            enabled=True,
            kind=module.DESTROY_KIND_MATERIALS,
            whitelist_targets=[
                module.WhitelistTarget(model_id=300, keep_count=3),
                module.WhitelistTarget(model_id=100, keep_count=1),
                module.WhitelistTarget(model_id=200, keep_count=2),
            ],
        )
    )
    destroy_item_rule = module._normalize_destroy_rule(
        module.DestroyRule(
            enabled=True,
            kind=module.DESTROY_KIND_EXPLICIT_MODELS,
            whitelist_targets=[
                module.WhitelistTarget(model_id=300, keep_count=3),
                module.WhitelistTarget(model_id=100, keep_count=1),
                module.WhitelistTarget(model_id=200, keep_count=2),
            ],
        )
    )

    buy_stock_summary, buy_stock_ready = widget._get_buy_rule_summary(buy_stock_rule)
    buy_material_summary, buy_material_ready = widget._get_buy_rule_summary(buy_material_rule)
    buy_rune_summary, buy_rune_ready = widget._get_buy_rule_summary(buy_rune_rule)
    sell_material_summary, sell_material_ready = widget._get_sell_rule_summary(sell_material_rule)
    sell_item_summary, sell_item_ready = widget._get_sell_rule_summary(sell_item_rule)
    destroy_material_summary, destroy_material_ready = widget._get_destroy_rule_summary(destroy_material_rule)
    destroy_item_summary, destroy_item_ready = widget._get_destroy_rule_summary(destroy_item_rule)

    _expect(
        buy_stock_ready and buy_stock_summary == "3 stock target(s) | alpha, Bravo +1 more",
        "Collapsed buy stock summaries should use the same alphabetical display order as the expanded target table.",
    )
    _expect(
        buy_material_ready and buy_material_summary == "3 material target(s) | alpha, Bravo +1 more",
        "Collapsed buy material summaries should use the same alphabetical display order as the expanded target table.",
    )
    _expect(
        buy_rune_ready and buy_rune_summary == "3 target(s) | shared rune, Shared Rune +1 more",
        "Collapsed buy rune summaries should use the same alphabetical display order as the expanded target table.",
    )
    _expect(
        sell_material_ready and sell_material_summary == "3 material target(s) | alpha keep 1, Bravo keep 2 +1 more",
        "Collapsed sell material summaries should match the alphabetical order used by the expanded selected-materials table.",
    )
    _expect(
        sell_item_ready and sell_item_summary == "3 selected target(s) | alpha keep 1, Bravo keep 2 +1 more",
        "Collapsed sell explicit-item summaries should match the alphabetical order used by the expanded selected-items table.",
    )
    _expect(
        destroy_material_ready and destroy_material_summary == "3 material target(s) | alpha keep 1, Bravo keep 2 +1 more",
        "Collapsed destroy material summaries should match the alphabetical order used by the expanded selected-materials table.",
    )
    _expect(
        destroy_item_ready and destroy_item_summary == "3 selected target(s) | alpha keep 1, Bravo keep 2 +1 more",
        "Collapsed destroy explicit-item summaries should match the alphabetical order used by the expanded selected-items table.",
    )
    _expect(
        [target.model_id for target in buy_stock_rule.merchant_stock_targets] == [300, 100, 200],
        "Display-only summary sorting should not mutate the stored merchant-stock target order.",
    )
    _expect(
        [target.identifier for target in buy_rune_rule.rune_targets] == ["rune_z", "rune_b", "rune_a"],
        "Display-only summary sorting should not mutate the stored rune-target order.",
    )


def _test_display_sort_reads_preserve_saved_child_entry_order(module, temp_root: Path) -> None:
    widget = _make_widget(module)
    _seed_display_sort_fixture(widget)
    config_path = temp_root / "display_sort_preserves_saved_order.json"
    widget.config_path = str(config_path)

    widget.buy_rules = [
        module._normalize_buy_rule(
            module.BuyRule(
                enabled=True,
                kind=module.BUY_KIND_MERCHANT_STOCK,
                merchant_stock_targets=[
                    module.MerchantStockTarget(model_id=300, target_count=0, max_per_run=0),
                    module.MerchantStockTarget(model_id=100, target_count=0, max_per_run=0),
                    module.MerchantStockTarget(model_id=200, target_count=0, max_per_run=0),
                ],
            )
        ),
        module._normalize_buy_rule(
            module.BuyRule(
                enabled=True,
                kind=module.BUY_KIND_MATERIAL_TARGET,
                material_targets=[
                    module.MaterialTarget(model_id=300, target_count=0, max_per_run=0),
                    module.MaterialTarget(model_id=100, target_count=0, max_per_run=0),
                    module.MaterialTarget(model_id=200, target_count=0, max_per_run=0),
                ],
            )
        ),
        module._normalize_buy_rule(
            module.BuyRule(
                enabled=True,
                kind=module.BUY_KIND_RUNE_TRADER_TARGET,
                rune_targets=[
                    module.RuneTraderTarget(identifier="rune_z", target_count=0, max_per_run=0),
                    module.RuneTraderTarget(identifier="rune_b", target_count=0, max_per_run=0),
                    module.RuneTraderTarget(identifier="rune_a", target_count=0, max_per_run=0),
                ],
            )
        ),
    ]
    widget.sell_rules = [
        module._normalize_sell_rule(
            module.SellRule(
                enabled=True,
                kind=module.SELL_KIND_WEAPONS,
                blacklist_model_ids=[300, 100, 200],
                protected_weapon_requirement_rules=[
                    module.WeaponRequirementRule(model_id=300, min_requirement=1, max_requirement=8),
                    module.WeaponRequirementRule(model_id=100, min_requirement=1, max_requirement=9),
                    module.WeaponRequirementRule(model_id=200, min_requirement=1, max_requirement=10),
                ],
                protected_weapon_mod_identifiers=["mod_z", "mod_b", "mod_a"],
                rule_id="weapon_rule",
            )
        ),
        module._normalize_sell_rule(
            module.SellRule(
                enabled=True,
                kind=module.SELL_KIND_ARMOR,
                protected_rune_identifiers=["rune_z", "rune_b", "rune_a"],
                rule_id="armor_rule",
            )
        ),
        module._normalize_sell_rule(
            module.SellRule(
                enabled=True,
                kind=module.SELL_KIND_EXPLICIT_MODELS,
                whitelist_targets=[
                    module.WhitelistTarget(model_id=300, keep_count=3),
                    module.WhitelistTarget(model_id=100, keep_count=1),
                    module.WhitelistTarget(model_id=200, keep_count=2),
                ],
            )
        ),
    ]
    widget.destroy_rules = [
        module._normalize_destroy_rule(
            module.DestroyRule(
                enabled=True,
                kind=module.DESTROY_KIND_EXPLICIT_MODELS,
                whitelist_targets=[
                    module.WhitelistTarget(model_id=300, keep_count=3),
                    module.WhitelistTarget(model_id=100, keep_count=1),
                    module.WhitelistTarget(model_id=200, keep_count=2),
                ],
            )
        )
    ]
    widget.cleanup_targets = [
        module.CleanupTarget(model_id=300, keep_on_character=3),
        module.CleanupTarget(model_id=100, keep_on_character=1),
        module.CleanupTarget(model_id=200, keep_on_character=2),
    ]

    for buy_rule in widget.buy_rules:
        widget._get_buy_rule_summary(buy_rule)
    for sell_rule in widget.sell_rules:
        widget._get_sell_rule_summary(sell_rule)
    for destroy_rule in widget.destroy_rules:
        widget._get_destroy_rule_summary(destroy_rule)
    widget._sort_model_ids_for_display(widget.sell_rules[0].blacklist_model_ids)
    widget._sort_identifiers_for_display(widget.sell_rules[0].protected_weapon_mod_identifiers, widget._get_weapon_mod_label)

    _expect(widget._save_profile(), "Saving a profile after display-only sorting reads should still succeed.")
    saved_payload = json.loads(config_path.read_text(encoding="utf-8"))

    _expect(
        [entry["model_id"] for entry in saved_payload["buy_rules"][0]["merchant_stock_targets"]] == [300, 100, 200],
        "Display-only sorting must not change persisted merchant-stock target order.",
    )
    _expect(
        [entry["model_id"] for entry in saved_payload["buy_rules"][1]["material_targets"]] == [300, 100, 200],
        "Display-only sorting must not change persisted material-target order.",
    )
    _expect(
        [entry["identifier"] for entry in saved_payload["buy_rules"][2]["rune_targets"]] == ["rune_z", "rune_b", "rune_a"],
        "Display-only sorting must not change persisted rune-target order.",
    )
    _expect(
        saved_payload["sell_rules"][0]["blacklist_model_ids"] == [300, 100, 200],
        "Display-only sorting must not change persisted protected-model order.",
    )
    _expect(
        [entry["model_id"] for entry in saved_payload["sell_rules"][0]["protected_weapon_requirement_rules"]] == [300, 100, 200],
        "Display-only sorting must not change persisted protected-requirement order.",
    )
    _expect(
        saved_payload["sell_rules"][0]["protected_weapon_mod_identifiers"] == ["mod_z", "mod_b", "mod_a"],
        "Display-only sorting must not change persisted protected-weapon-mod order.",
    )
    _expect(
        saved_payload["sell_rules"][1]["protected_rune_identifiers"] == ["rune_z", "rune_b", "rune_a"],
        "Display-only sorting must not change persisted protected-rune order.",
    )
    _expect(
        [entry["model_id"] for entry in saved_payload["sell_rules"][2]["whitelist_targets"]] == [300, 100, 200],
        "Display-only sorting must not change persisted sell whitelist order.",
    )
    _expect(
        [entry["model_id"] for entry in saved_payload["destroy_rules"][0]["whitelist_targets"]] == [300, 100, 200],
        "Display-only sorting must not change persisted destroy whitelist order.",
    )
    _expect(
        [entry["model_id"] for entry in saved_payload["cleanup_targets"]] == [300, 100, 200],
        "Display-only sorting must not change persisted cleanup-target order.",
    )


def _test_rune_description_templates_resolve_for_tooltips(module) -> None:
    description = "+{arg2[8680]} {arg1[8680]} (Non-stacking)\n-{arg2[8408]} Health"
    modifiers = [
        {"Identifier": 8680, "Arg1": 35, "Arg2": 2, "Arg": 8962},
        {"Identifier": 8408, "Arg1": 0, "Arg2": 35, "Arg": 35},
    ]
    resolved = module._resolve_rune_description_template(description, modifiers)
    _expect(
        resolved == "+2 Critical Strikes (Non-stacking)\n-35 Health",
        "Rune tooltip descriptions should resolve attribute and health placeholders while preserving non-stacking text.",
    )


def _test_default_protection_jump_targets_still_use_first_stored_entry(module) -> None:
    widget = _make_widget(module)
    _seed_display_sort_fixture(widget)

    blacklist_rule = module._normalize_sell_rule(
        module.SellRule(
            kind=module.SELL_KIND_WEAPONS,
            blacklist_model_ids=[300, 100, 200],
        )
    )
    requirement_rule = module._normalize_sell_rule(
        module.SellRule(
            kind=module.SELL_KIND_WEAPONS,
            protected_weapon_requirement_rules=[
                module.WeaponRequirementRule(model_id=300, min_requirement=1, max_requirement=8),
                module.WeaponRequirementRule(model_id=100, min_requirement=1, max_requirement=8),
            ],
        )
    )
    weapon_mod_rule = module._normalize_sell_rule(
        module.SellRule(
            kind=module.SELL_KIND_WEAPONS,
            protected_weapon_mod_identifiers=["mod_z", "mod_a"],
        )
    )
    armor_rune_rule = module._normalize_sell_rule(
        module.SellRule(
            kind=module.SELL_KIND_ARMOR,
            protected_rune_identifiers=["rune_z", "rune_a"],
        )
    )

    _expect(
        widget._get_default_sell_rule_protection_jump_target(blacklist_rule) == (module.SELL_PROTECTION_ANCHOR_MODELS, "model:300"),
        "Default protection jumps should still follow the first stored protected-model entry, not the alphabetical display order.",
    )
    _expect(
        widget._get_default_sell_rule_protection_jump_target(requirement_rule) == (module.SELL_PROTECTION_ANCHOR_REQUIREMENTS, "requirement_model:300"),
        "Default protection jumps should still follow the first stored requirement rule, not the alphabetical display order.",
    )
    _expect(
        widget._get_default_sell_rule_protection_jump_target(weapon_mod_rule) == (module.SELL_PROTECTION_ANCHOR_WEAPON_MODS, "identifier:mod_z"),
        "Default protection jumps should still follow the first stored weapon-mod entry, not the alphabetical display order.",
    )
    _expect(
        widget._get_default_sell_rule_protection_jump_target(armor_rune_rule) == (module.SELL_PROTECTION_ANCHOR_RUNES, "identifier:rune_z"),
        "Default protection jumps should still follow the first stored rune entry, not the alphabetical display order.",
    )


def _test_request_execute_now_queues_only_when_preview_matches(module) -> None:
    widget = _make_widget(module)
    widget.preview_ready = True
    widget.preview_plan = module.PlanResult(
        inventory_snapshot_captured=True,
        inventory_model_counts={111: 1},
        inventory_item_count=1,
        supported_map=True,
        has_actions=True,
    )
    widget._collect_inventory_items = lambda: [
        _make_item(module, item_id=1, model_id=111, name="Iron Sword", quantity=1),
    ]

    queued: list[str] = []
    widget._queue_execute_now = lambda: queued.append("queued")

    widget._request_execute_now()

    _expect(queued == ["queued"], "Execute request should continue immediately when the preview snapshot still matches inventory.")
    _expect(not widget.execute_drift_requires_confirmation, "Matching inventory should not require an execute confirmation.")


def _test_compare_inventory_detects_preview_drift(module) -> None:
    widget = _make_widget(module)
    widget.preview_ready = True
    widget.preview_plan = module.PlanResult(
        inventory_snapshot_captured=True,
        inventory_model_counts={111: 1},
        inventory_item_count=1,
    )
    widget._collect_inventory_items = lambda: [
        _make_item(module, item_id=1, model_id=111, name="Iron Sword", quantity=2),
        _make_item(module, item_id=2, model_id=222, name="Bone", quantity=1),
    ]

    compared = widget._compare_current_inventory_against_preview()

    _expect(compared, "Preview drift compare should complete when a preview snapshot exists.")
    _expect(widget.execute_drift_requires_confirmation, "Inventory drift should force an explicit execute confirmation.")
    _expect("2 model(s)" in widget.preview_inventory_diff_summary, "Drift summary should report how many model counts changed.")
    _expect(any("Iron Sword" in row for row in widget.preview_inventory_diff_rows), "Drift rows should mention changed existing models.")
    _expect(any("Bone" in row for row in widget.preview_inventory_diff_rows), "Drift rows should mention newly introduced models.")


def _test_compare_inventory_detects_preview_drift_for_projected_preview(module) -> None:
    widget = _make_widget(module)
    widget.preview_ready = True
    widget.preview_requires_execute_travel = True
    widget.preview_execute_travel_target_outpost_id = 2
    widget.preview_execute_travel_target_outpost_name = "Regression Harbor"
    widget.preview_plan = module.PlanResult(
        inventory_snapshot_captured=True,
        inventory_model_counts={111: 1},
        inventory_item_count=1,
    )
    widget._collect_inventory_items = lambda: [
        _make_item(module, item_id=1, model_id=111, name="Iron Sword", quantity=2),
        _make_item(module, item_id=2, model_id=222, name="Bone", quantity=1),
    ]

    compared = widget._compare_current_inventory_against_preview()

    _expect(compared, "Projected previews should still support inventory drift comparison.")
    _expect(widget.execute_drift_requires_confirmation, "Projected preview drift should still force an explicit execute confirmation.")
    _expect("2 model(s)" in widget.preview_inventory_diff_summary, "Projected preview drift should report changed model counts.")
    _expect(any("Iron Sword" in row for row in widget.preview_inventory_diff_rows), "Projected preview drift rows should mention changed existing models.")
    _expect(any("Bone" in row for row in widget.preview_inventory_diff_rows), "Projected preview drift rows should mention newly introduced models.")


def _test_merchant_sell_verification_confirms_changes_and_reports_timeouts(module) -> None:
    widget = _make_widget(module)
    remaining_quantity_snapshots = iter([
        {101: 1},
    ])
    widget._get_inventory_stack_quantities = lambda _item_ids: next(remaining_quantity_snapshots, {})

    confirmed_ids, pending_ids = _drain_generator_return(
        widget._wait_for_merchant_sell_confirmation(
            {
                101: 2,
                202: 1,
            },
            timeout_ms=0,
            step_ms=1,
        )
    )

    _expect(confirmed_ids == {101, 202}, "Merchant sell verification should confirm both decreased stacks and disappeared items.")
    _expect(not pending_ids, "Merchant sell verification should not leave pending items when every tracked item changed.")

    timeout_widget = _make_widget(module)
    timeout_widget._get_inventory_stack_quantities = lambda _item_ids: {303: 4}
    confirmed_ids, pending_ids = _drain_generator_return(
        timeout_widget._wait_for_merchant_sell_confirmation(
            {
                303: 4,
            },
            timeout_ms=0,
            step_ms=1,
        )
    )

    _expect(not confirmed_ids, "Merchant sell verification should not report success when the tracked quantity never changes.")
    _expect(pending_ids == {303}, "Merchant sell verification should leave unchanged items pending so the caller can report a timeout.")

    timeout_summary = timeout_widget._format_execution_phase_summary(
        module.ExecutionPhaseOutcome(
            label="Merchant sells",
            measure_label="items",
            attempted=1,
            completed=len(confirmed_ids),
            timeout_failures=len(pending_ids),
        )
    )
    _expect("0/1 items" in timeout_summary, "Merchant sell timeout summaries should keep the attempted item count visible.")
    _expect("1 timeout(s)" in timeout_summary, "Merchant sell timeout summaries should report the unresolved item count.")


def _test_build_remote_preview_result_formats_multibox_states(module) -> None:
    projected_widget = _prime_initialized_widget(module, _make_widget(module))
    projected_widget.preview_ready = True
    projected_widget.preview_requires_execute_travel = True
    projected_widget.preview_execute_travel_target_outpost_id = 2
    projected_widget.preview_execute_travel_target_outpost_name = "Regression Harbor"
    projected_widget.preview_plan = module.PlanResult(
        supported_map=True,
        entries=[
            module.ExecutionPlanEntry(
                action_type="sell",
                merchant_type=module.MERCHANT_TYPE_MERCHANT,
                label="Iron Sword",
                quantity=1,
                state=module.PLAN_STATE_CONDITIONAL,
            ),
        ],
        has_actions=True,
    )
    projected_result = projected_widget.build_remote_preview_result()
    _expect(projected_result["status_label"] == "Projected", "Projected previews should report the dedicated Projected status.")
    _expect(projected_result["summary"] == "1 can run, 0 blocked, 1 need live checks.", "Projected previews should still report runnable and live-check counts.")
    _expect(
        "Regression Harbor" in projected_result["detail"],
        "Projected previews should name the auto-travel target in the remote detail text.",
    )
    _expect(
        "auto-travel" in projected_result["detail"].lower(),
        "Projected previews should explain that Execute still owns the real travel and rebuild flow.",
    )

    unsupported_widget = _prime_initialized_widget(module, _make_widget(module))
    unsupported_widget.preview_plan = module.PlanResult(
        supported_map=False,
        supported_reason="Current map is not supported.",
    )
    unsupported_result = unsupported_widget.build_remote_preview_result()
    _expect(unsupported_result["status_label"] == "Unsupported", "Unsupported previews should report the Unsupported status.")
    _expect(
        unsupported_result["summary"] == "Current map is not supported.",
        "Unsupported previews should reuse the supported-reason text in the summary.",
    )

    conditional_widget = _prime_initialized_widget(module, _make_widget(module))
    conditional_widget.preview_plan = module.PlanResult(
        supported_map=True,
        entries=[
            module.ExecutionPlanEntry(
                action_type="buy",
                merchant_type=module.MERCHANT_TYPE_MERCHANT,
                label="Identification Kit",
                quantity=1,
                state=module.PLAN_STATE_CONDITIONAL,
            ),
            module.ExecutionPlanEntry(
                action_type="sell",
                merchant_type=module.MERCHANT_TYPE_MERCHANT,
                label="Skipped Test Item",
                quantity=1,
                state=module.PLAN_STATE_SKIPPED,
                reason="Protected by rules.",
            ),
        ],
        has_actions=True,
    )
    conditional_result = conditional_widget.build_remote_preview_result()
    _expect(conditional_result["status_label"] == "Conditional", "Conditional-only previews should use the Conditional status.")
    _expect(
        conditional_result["summary"] == "1 can run, 1 blocked, 1 need live checks.",
        "Conditional-only previews should include runnable, blocked, and live-check counts.",
    )
    _expect(
        conditional_result["detail"] == "Some actions need a live merchant, trader, crafter, or Xunlai check before MR can confirm them.",
        "Conditional-only previews should explain why follower actions still need live checks.",
    )
    _expect(conditional_result["primary_count"] == 1, "Conditional previews should report actionable counts to the leader.")
    _expect(conditional_result["secondary_count"] == 1, "Conditional previews should report blocked counts to the leader.")

    ready_widget = _prime_initialized_widget(module, _make_widget(module))
    ready_widget.preview_plan = module.PlanResult(
        supported_map=True,
        entries=[
            module.ExecutionPlanEntry(
                action_type="sell",
                merchant_type=module.MERCHANT_TYPE_MERCHANT,
                label="Iron Sword",
                quantity=1,
                state=module.PLAN_STATE_WILL_EXECUTE,
            ),
            module.ExecutionPlanEntry(
                action_type="buy",
                merchant_type=module.MERCHANT_TYPE_MERCHANT,
                label="Identification Kit",
                quantity=1,
                state=module.PLAN_STATE_CONDITIONAL,
            ),
            module.ExecutionPlanEntry(
                action_type="sell",
                merchant_type=module.MERCHANT_TYPE_MERCHANT,
                label="Protected Item",
                quantity=1,
                state=module.PLAN_STATE_SKIPPED,
                reason="Protected by rules.",
            ),
        ],
        has_actions=True,
    )
    ready_result = ready_widget.build_remote_preview_result()
    _expect(ready_result["status_label"] == "Ready", "Mixed direct and conditional previews should stay in the Ready state.")
    _expect(
        ready_result["summary"] == "2 can run, 1 blocked, 1 need live checks.",
        "Ready previews should include runnable, blocked, and live-check counts when merchant stock checks remain.",
    )
    _expect(
        ready_result["detail"] == "Some actions need a live merchant, trader, crafter, or Xunlai check before MR can confirm them.",
        "Ready previews should still explain when live checks are needed.",
    )

    empty_widget = _prime_initialized_widget(module, _make_widget(module))
    empty_widget.preview_plan = module.PlanResult(
        supported_map=True,
        entries=[],
        has_actions=False,
    )
    empty_result = empty_widget.build_remote_preview_result()
    _expect(empty_result["status_label"] == "No Actions", "Empty previews should report the No Actions status.")
    _expect(
        empty_result["summary"] == "No actionable merchant work found.",
        "Empty previews should use the compact no-actions summary.",
    )


def _test_build_remote_execute_result_formats_multibox_states(module) -> None:
    executed_widget = _prime_initialized_widget(module, _make_widget(module))
    executed_widget.preview_plan = module.PlanResult(
        supported_map=True,
        entries=[
            module.ExecutionPlanEntry(
                action_type="sell",
                merchant_type=module.MERCHANT_TYPE_MERCHANT,
                label="Iron Sword",
                quantity=1,
                state=module.PLAN_STATE_WILL_EXECUTE,
            ),
            module.ExecutionPlanEntry(
                action_type="buy",
                merchant_type=module.MERCHANT_TYPE_MERCHANT,
                label="Identification Kit",
                quantity=1,
                state=module.PLAN_STATE_CONDITIONAL,
            ),
            module.ExecutionPlanEntry(
                action_type="sell",
                merchant_type=module.MERCHANT_TYPE_MERCHANT,
                label="Blocked Item",
                quantity=1,
                state=module.PLAN_STATE_SKIPPED,
                reason="Protected by rules.",
            ),
        ],
        has_actions=True,
    )
    executed_widget.last_execution_summary = "Merchant stock: 1/1 targets queued. Merchant sells: 1/1 items."
    executed_widget.status_message = "Execution finished. Preview again to refresh the post-run state."

    executed_result = executed_widget.build_remote_execute_result()

    _expect(executed_result["status_label"] == "Executed", "Execute results with actionable entries should report Executed.")
    _expect(executed_result["primary_count"] == 2, "Execute results should count direct and conditional actions as actionable.")
    _expect(executed_result["secondary_count"] == 1, "Execute results should report blocked entries separately.")
    _expect(
        executed_result["summary"] == executed_widget.last_execution_summary,
        "Execute results should reuse the richer execution summary when one is available.",
    )
    _expect(
        executed_result["detail"] == executed_widget.status_message,
        "Execute results should preserve the final status message for multibox followers.",
    )

    empty_widget = _prime_initialized_widget(module, _make_widget(module))
    empty_widget.preview_plan = module.PlanResult(supported_map=True, entries=[], has_actions=False)
    empty_widget.status_message = "Nothing to execute for the current rules and inventory state."
    empty_result = empty_widget.build_remote_execute_result()

    _expect(empty_result["status_label"] == "No Actions", "Execute results without actionable entries should report No Actions.")
    _expect(
        empty_result["summary"] == empty_widget.status_message,
        "Empty execute results should surface the current status message when nothing ran.",
    )


def _test_handle_multibox_result_updates_status_and_ignores_stale_requests(module) -> None:
    widget = _make_widget(module)
    widget.multibox_active_request_id = "execute-req-1"
    widget.multibox_running_email = "follower@example.com"
    widget.multibox_running_started_at_ms = 12345
    widget.multibox_running_accounts = {"follower@example.com": 12000}

    ignored = widget.handle_multibox_result(
        "Follower@example.com",
        request_id="stale-request",
        opcode=module.MERCHANT_RULES_OPCODE_EXECUTE_RESULT,
        primary_count=2,
        secondary_count=1,
        success_flag=True,
        status_label="Executed",
        summary="Should be ignored.",
        detail="Stale request result.",
    )

    _expect(not ignored, "Mismatched request ids should be ignored so older follower results do not overwrite current state.")
    _expect(widget.multibox_running_email == "follower@example.com", "Ignoring a stale result should leave the running follower untouched.")
    _expect("follower@example.com" in widget.multibox_running_accounts, "Ignoring a stale result should not clear running-account tracking.")

    accepted = widget.handle_multibox_result(
        "Follower@example.com",
        request_id="execute-req-1",
        opcode=module.MERCHANT_RULES_OPCODE_EXECUTE_RESULT,
        primary_count=2,
        secondary_count=1,
        success_flag=True,
        status_label="Executed",
        summary="2 actions finished.",
        detail="Execution finished cleanly.",
    )

    _expect(accepted, "Matching execute results should be accepted.")
    status = _get_multibox_status(widget, "follower@example.com")
    _expect(status is not None, "Accepted multibox results should create or update follower status rows.")
    _expect(status.state == "execute_result", "Execute result opcodes should map to the execute_result state.")
    _expect(status.success, "Successful execute results should stay marked successful.")
    _expect(status.primary_count == 2 and status.secondary_count == 1, "Accepted execute results should preserve the reported action counts.")
    _expect(widget.multibox_running_email == "", "Accepted execute results should clear the currently running follower.")
    _expect(widget.multibox_running_started_at_ms == 0, "Accepted execute results should clear the running-start timestamp.")
    _expect("follower@example.com" not in widget.multibox_running_accounts, "Accepted execute results should remove the follower from preview tracking as well.")

    error_widget = _make_widget(module)
    error_widget.multibox_active_request_id = "execute-req-2"
    error_widget.multibox_running_accounts = {"error@example.com": 1}
    accepted_error = error_widget.handle_multibox_result(
        "error@example.com",
        request_id="execute-req-2",
        opcode=module.MERCHANT_RULES_OPCODE_ERROR_RESULT,
        primary_count=0,
        secondary_count=1,
        success_flag=True,
        status_label="Execute Failed",
        summary="Execution failed.",
        detail="Merchant window never opened.",
    )

    _expect(accepted_error, "Error results with the active request id should still be accepted.")
    error_status = _get_multibox_status(error_widget, "error@example.com")
    _expect(error_status.state == "error", "Error result opcodes should map to the error state.")
    _expect(not error_status.success, "Error result opcodes should never remain successful even if the remote flag was truthy.")


def _test_advance_multibox_batch_handles_preview_and_execute_timeouts(module) -> None:
    preview_widget = _make_widget(module)
    preview_widget.multibox_active_action = "preview"
    preview_widget.multibox_active_request_id = "preview-req-1"
    preview_widget.multibox_running_accounts = {
        "preview-timeout@example.com": 0,
        "preview-ok@example.com": module.MULTIBOX_REMOTE_TIMEOUT_MS,
    }
    original_time = module.time.time
    module.time.time = lambda: (module.MULTIBOX_REMOTE_TIMEOUT_MS + 10) / 1000.0
    try:
        preview_widget._advance_multibox_batch()
    finally:
        module.time.time = original_time

    timeout_status = _get_multibox_status(preview_widget, "preview-timeout@example.com")
    _expect(timeout_status is not None and timeout_status.state == "error", "Preview followers should flip to an error status when they time out.")
    _expect(timeout_status.status_label == "Timed Out", "Preview timeouts should use the dedicated Timed Out label.")
    _expect(
        timeout_status.detail == "The follower did not answer the Merchant Rules preview request in time.",
        "Preview timeouts should keep the preview-specific timeout detail.",
    )
    _expect(
        "preview-ok@example.com" in preview_widget.multibox_running_accounts,
        "Preview followers still inside the timeout window should stay tracked as running.",
    )

    execute_widget = _make_widget(module)
    execute_widget.multibox_active_action = "execute"
    execute_widget.multibox_active_request_id = "execute-req-3"
    execute_widget.multibox_running_email = "running@example.com"
    execute_widget.multibox_running_started_at_ms = 0
    execute_widget.multibox_pending_accounts = [
        "missing@example.com",
        "sendfail@example.com",
        "queued@example.com",
    ]
    execute_widget._get_multibox_active_email_map = lambda: {
        "sendfail@example.com": "sendfail@example.com",
        "queued@example.com": "queued@example.com",
    }
    send_calls: list[tuple[str, int, str, str]] = []

    def _fake_send(receiver_email: str, opcode: int, request_id: str, status_label: str, *_extra) -> bool:
        send_calls.append((receiver_email, opcode, request_id, status_label))
        return receiver_email == "queued@example.com"

    execute_widget._send_multibox_command = _fake_send
    original_time = module.time.time
    module.time.time = lambda: (module.MULTIBOX_REMOTE_TIMEOUT_MS + 25) / 1000.0
    try:
        execute_widget._advance_multibox_batch()
    finally:
        module.time.time = original_time

    running_timeout_status = _get_multibox_status(execute_widget, "running@example.com")
    _expect(running_timeout_status is not None and running_timeout_status.state == "error", "The active execute follower should time out into an error status.")
    _expect(
        running_timeout_status.detail == "The follower did not answer the Merchant Rules request in time.",
        "Execute timeouts should keep the execute-specific timeout detail.",
    )
    missing_status = _get_multibox_status(execute_widget, "missing@example.com")
    _expect(missing_status is not None and missing_status.status_label == "Unavailable", "Unavailable execute followers should be reported before queueing later followers.")
    sendfail_status = _get_multibox_status(execute_widget, "sendfail@example.com")
    _expect(sendfail_status is not None and sendfail_status.status_label == "Request Not Queued", "Send failures should surface the request-not-queued state.")
    queued_status = _get_multibox_status(execute_widget, "queued@example.com")
    _expect(queued_status is not None and queued_status.state == "running", "The next sendable execute follower should move into the running state.")
    _expect(execute_widget.multibox_running_email == "queued@example.com", "Execute batching should advance to the next sendable follower after earlier failures.")
    _expect(execute_widget.multibox_running_started_at_ms > 0, "Execute batching should stamp a fresh start time for the newly running follower.")
    _expect(
        send_calls == [
            ("sendfail@example.com", module.MERCHANT_RULES_OPCODE_EXECUTE, "execute-req-3", "Execute"),
            ("queued@example.com", module.MERCHANT_RULES_OPCODE_EXECUTE, "execute-req-3", "Execute"),
        ],
        "Execute batching should retry pending followers in order until one request is queued.",
    )


def _test_multibox_sync_preserves_follower_window_geometry_on_disk(module, temp_root: Path) -> None:
    widget = _make_widget(module)
    follower_email = "follower@example.com"
    follower_config_path = Path(widget._get_config_path_for_account(follower_email))
    follower_config_path.parent.mkdir(parents=True, exist_ok=True)
    follower_payload = {
        "version": module.PROFILE_VERSION,
        "auto_travel_enabled": False,
        "target_outpost_id": 1,
        "favorite_outpost_ids": [1],
        "debug_logging": False,
        "window_x": 15,
        "window_y": 25,
        "window_width": 350,
        "window_height": 450,
        "window_collapsed": True,
        "buy_rules": [],
        "sell_rules": [],
    }
    follower_config_path.write_text(json.dumps(follower_payload, indent=2), encoding="utf-8")

    widget.auto_travel_enabled = True
    widget.target_outpost_id = 2
    widget.favorite_outpost_ids = [1, 2]
    widget.debug_logging = True
    widget.window_x = 900
    widget.window_y = 901
    widget.window_width = 902
    widget.window_height = 903
    widget.window_collapsed = False
    widget.buy_rules = [
        module._normalize_buy_rule(
            module.BuyRule(
                enabled=True,
                kind=module.BUY_KIND_MATERIAL_TARGET,
                material_targets=[
                    module.MaterialTarget(
                        model_id=int(module.ECTOPLASM_MODEL_ID),
                        target_count=25,
                        max_per_run=5,
                    )
                ],
            )
        )
    ]
    widget.sell_rules = [
        module._normalize_sell_rule(
            module.SellRule(
                enabled=True,
                kind=module.SELL_KIND_EXPLICIT_MODELS,
                model_ids=[111],
                keep_count=0,
            )
        )
    ]
    widget._get_multibox_accounts = lambda: [types.SimpleNamespace(AccountEmail=follower_email, IsActive=True, IsHero=False)]
    widget.multibox_selected_accounts = {follower_email: True}
    send_calls: list[tuple[str, int, str, str]] = []
    widget._send_multibox_command = lambda receiver_email, opcode, request_id, status_label: send_calls.append(
        (receiver_email, opcode, request_id, status_label)
    ) or True

    widget._start_multibox_sync()

    saved_payload = json.loads(follower_config_path.read_text(encoding="utf-8"))
    _expect(saved_payload["auto_travel_enabled"], "Multibox sync should still push leader Merchant Rules settings to the follower profile.")
    _expect(saved_payload["target_outpost_id"] == 2, "Multibox sync should keep the leader target outpost in the follower profile.")
    _expect(saved_payload["favorite_outpost_ids"] == [1, 2], "Multibox sync should keep synced favorite outposts intact.")
    _expect(saved_payload["debug_logging"], "Multibox sync should keep synced debug settings intact.")
    _expect(len(saved_payload["buy_rules"]) == 1 and len(saved_payload["sell_rules"]) == 1, "Multibox sync should still write synced buy and sell rules.")
    _expect(saved_payload["window_x"] == 15 and saved_payload["window_y"] == 25, "Follower sync should preserve the follower window position on disk.")
    _expect(saved_payload["window_width"] == 350 and saved_payload["window_height"] == 450, "Follower sync should preserve the follower window size on disk.")
    _expect(saved_payload["window_collapsed"], "Follower sync should preserve the follower collapsed state on disk.")
    _expect(
        send_calls == [(follower_email, module.MERCHANT_RULES_OPCODE_RELOAD_PROFILE, widget.multibox_active_request_id, "Sync")],
        "Multibox sync should still queue the follower reload request after writing the synced profile.",
    )


def _test_reload_profile_from_disk_preserves_live_window_geometry(module, temp_root: Path) -> None:
    widget = _prime_initialized_widget(module, _make_widget(module))
    config_path = temp_root / "reload_preserve_window_geometry.json"
    widget.config_path = str(config_path)

    collapsed_disk_payload = {
        "version": module.PROFILE_VERSION,
        "auto_travel_enabled": True,
        "target_outpost_id": 2,
        "favorite_outpost_ids": [2],
        "debug_logging": True,
        "window_x": 700,
        "window_y": 701,
        "window_width": 702,
        "window_height": 703,
        "window_collapsed": False,
        "buy_rules": [
            {
                "enabled": True,
                "kind": module.BUY_KIND_MERCHANT_STOCK,
                "merchant_type": module.MERCHANT_TYPE_MERCHANT,
                "model_id": 555,
                "target_count": 3,
                "max_per_run": 2,
                "material_targets": [],
            }
        ],
        "sell_rules": [],
    }
    config_path.write_text(json.dumps(collapsed_disk_payload, indent=2), encoding="utf-8")

    widget.window_x = 11
    widget.window_y = 22
    widget.window_width = 333
    widget.window_height = 444
    widget.window_collapsed = True
    widget.window_geometry_dirty = False

    widget.reload_profile_from_disk(
        status_message="Merchant Rules profile reloaded by multibox sync.",
        preserve_window_geometry=True,
    )

    _expect(widget.auto_travel_enabled, "Reload should still apply synced Merchant Rules settings from disk.")
    _expect(widget.target_outpost_id == 2 and widget.favorite_outpost_ids == [2], "Reload should still apply synced outpost settings from disk.")
    _expect(widget.debug_logging, "Reload should still apply synced debug settings from disk.")
    _expect(len(widget.buy_rules) == 1, "Reload should still apply synced buy rules from disk.")
    _expect(widget.window_x == 11 and widget.window_y == 22, "Collapsed follower reload should preserve the live window position.")
    _expect(widget.window_width == 333 and widget.window_height == 444, "Collapsed follower reload should preserve the live window size.")
    _expect(widget.window_collapsed, "Collapsed follower reload should preserve the live collapsed state.")
    _expect(widget.window_geometry_needs_apply, "Reloaded follower window geometry should be re-applied on the next draw.")
    _expect(widget.window_geometry_dirty, "Reloaded follower window geometry should be marked dirty when it overrides synced UI state.")

    open_disk_payload = dict(collapsed_disk_payload)
    open_disk_payload["window_x"] = 810
    open_disk_payload["window_y"] = 811
    open_disk_payload["window_width"] = 812
    open_disk_payload["window_height"] = 813
    open_disk_payload["window_collapsed"] = True
    config_path.write_text(json.dumps(open_disk_payload, indent=2), encoding="utf-8")

    widget.window_x = 101
    widget.window_y = 202
    widget.window_width = 303
    widget.window_height = 404
    widget.window_collapsed = False
    widget.window_geometry_dirty = False

    widget.reload_profile_from_disk(
        status_message="Merchant Rules profile reloaded by multibox sync.",
        preserve_window_geometry=True,
    )

    _expect(widget.window_x == 101 and widget.window_y == 202, "Open follower reload should preserve the live window position.")
    _expect(widget.window_width == 303 and widget.window_height == 404, "Open follower reload should preserve the live window size.")
    _expect(not widget.window_collapsed, "Open follower reload should preserve the live expanded state.")
    _expect(widget.window_geometry_dirty, "Open follower reload should also mark restored UI state dirty when it overrides synced geometry.")


def _test_reload_profile_multibox_message_preserves_window_geometry(module) -> None:
    widget = _make_widget(module)
    reload_calls: list[tuple[str, bool]] = []

    def _fake_reload_profile_from_disk(*, status_message: str = "", preserve_window_geometry: bool = False):
        reload_calls.append((status_message, preserve_window_geometry))
        return True

    widget.reload_profile_from_disk = _fake_reload_profile_from_disk
    message = types.SimpleNamespace(
        SenderEmail="leader@example.com",
        ReceiverEmail="follower@example.com",
        Params=(float(module.MERCHANT_RULES_OPCODE_RELOAD_PROFILE), 0.0, 0.0, 0.0),
        ExtraData=("", "", "", ""),
    )

    _drain_generator_return(widget.handle_shared_multibox_message(message))

    _expect(
        reload_calls == [("Merchant Rules live config reloaded by multibox sync.", True)],
        "The Merchant Rules reload opcode should preserve follower window geometry during multibox-triggered reloads.",
    )


def _test_modifier_parse_cache_reuses_hits_and_prunes_stale_entries(module) -> None:
    widget = _make_widget(module)
    parse_calls: list[tuple[tuple[tuple[int, int, int], ...], int, int]] = []
    original_parse_modifiers = module.parse_modifiers

    def _fake_parse_modifiers(raw_modifiers, parse_item_type, model_id, _db):
        parse_calls.append((tuple(raw_modifiers), int(getattr(parse_item_type, "value", 0)), int(model_id)))
        weapon_mod = types.SimpleNamespace(
            identifier="mod.beta",
            modifiers=[
                types.SimpleNamespace(
                    modifier_value_arg=types.SimpleNamespace(name="Arg1"),
                    min=10,
                    max=20,
                )
            ],
        )
        return types.SimpleNamespace(
            runes=[types.SimpleNamespace(rune=types.SimpleNamespace(identifier="rune.alpha"))],
            weapon_mods=[types.SimpleNamespace(weapon_mod=weapon_mod, value=19, is_maxed=False)],
            is_rune=False,
            requirements=9,
        )

    widget._get_item_modifier_values = lambda _item_id: ((101, 1, 2),)
    module.parse_modifiers = _fake_parse_modifiers
    try:
        first = widget._get_cached_inventory_modifiers(
            1001,
            111,
            module.ItemType.Sword,
            module.ItemType.Sword,
            is_weapon_like=True,
            is_armor_piece=False,
        )
        second = widget._get_cached_inventory_modifiers(
            1001,
            111,
            module.ItemType.Sword,
            module.ItemType.Sword,
            is_weapon_like=True,
            is_armor_piece=False,
        )
    finally:
        module.parse_modifiers = original_parse_modifiers

    _expect(len(parse_calls) == 1, "Matching modifier signatures should reuse the cached parse result instead of reparsing.")
    _expect(widget.inventory_modifier_cache_misses == 1, "The first modifier lookup should count as a cache miss.")
    _expect(widget.inventory_modifier_cache_hits == 1, "A repeated modifier lookup with the same signature should count as a cache hit.")
    _expect(first == second, "Cache hits should return the same parsed modifier payload for the unchanged item signature.")
    _expect(
        first.weapon_mod_matches == (
            module.ParsedUpgradeMatch(identifier="mod.beta", value=19, min_value=10, max_value=20, is_maxed=False),
        ),
        "Modifier cache entries should retain parsed weapon-mod roll value and range metadata for threshold protection.",
    )

    widget.inventory_modifier_cache[2002] = module.InventoryModifierCacheEntry(signature=(222,), parsed=module.ParsedInventoryModifiers())
    widget._prune_inventory_modifier_cache({1001})
    _expect(1001 in widget.inventory_modifier_cache, "Active inventory items should remain in the modifier cache after pruning.")
    _expect(2002 not in widget.inventory_modifier_cache, "Items that leave inventory should be pruned from the modifier cache.")


def _test_supported_context_cache_partial_and_negative_entries_refresh_correctly(module) -> None:
    original_time = module.time.time
    original_get_map_id = module.Map.GetMapID
    original_is_map_ready = module.Map.IsMapReady
    original_is_outpost = module.Map.IsOutpost
    original_is_guild_hall = module.Map.IsGuildHall
    original_get_map_name = module.Map.GetMapName
    original_default_selectors = dict(module.DEFAULT_NPC_SELECTORS)
    original_resolve_agent_xy = module.resolve_agent_xy_from_step

    try:
        module.Map.GetMapID = lambda: 100
        module.Map.IsMapReady = lambda: True
        module.Map.IsOutpost = lambda: True
        module.Map.IsGuildHall = lambda: False
        module.Map.GetMapName = lambda map_id=0: f"Map {int(map_id)}"
        module.DEFAULT_NPC_SELECTORS.clear()
        module.DEFAULT_NPC_SELECTORS.update({
            "merchant": "merchant_selector",
            "materials": "materials_selector",
            "rare_materials": "rare_selector",
        })

        partial_widget = _make_widget(module)
        partial_widget._resolve_rune_trader_coords = lambda _map_id, **_kwargs: None
        resolution_phase = {"value": 0}
        resolve_calls: list[tuple[int, str]] = []

        def _fake_resolve(step, **_kwargs):
            selector = step.get("npc") or step.get("target")
            resolve_calls.append((resolution_phase["value"], selector))
            if resolution_phase["value"] == 0:
                return {
                    "merchant_selector": (1.0, 1.0),
                    "materials_selector": None,
                    module.MATERIAL_TRADER_NAME_QUERY: None,
                    "rare_selector": (3.0, 3.0),
                    module.RARE_SCROLL_TRADER_NAME_QUERY: None,
                }[selector]
            return {
                "merchant_selector": (11.0, 11.0),
                "materials_selector": (22.0, 22.0),
                module.MATERIAL_TRADER_NAME_QUERY: (22.5, 22.5),
                "rare_selector": (33.0, 33.0),
                module.RARE_SCROLL_TRADER_NAME_QUERY: (44.0, 44.0),
            }[selector]

        module.resolve_agent_xy_from_step = _fake_resolve
        module.time.time = lambda: 100.0
        first_supported, first_reason, first_coords = partial_widget._get_supported_context()
        module.time.time = lambda: 100.5
        cached_supported, cached_reason, cached_coords = partial_widget._get_supported_context()
        resolution_phase["value"] = 1
        module.time.time = lambda: 102.0
        refreshed_supported, refreshed_reason, refreshed_coords = partial_widget._get_supported_context()

        _expect(first_supported, "Partial selector resolution should still mark the map supported when at least one merchant resolves.")
        _expect(first_coords[module.MERCHANT_TYPE_MATERIALS] is None, "The initial partial cache should preserve unresolved merchant types.")
        _expect(
            len(resolve_calls) == 5,
            "Supported-context lookups should reuse cached partial selector results for the same map until the cache is invalidated.",
        )
        _expect(cached_supported == first_supported and cached_reason == first_reason and cached_coords == first_coords, "Partial supported-context results should be reused inside the retry window.")
        _expect(refreshed_supported == first_supported, "Cached partial supported-context results should remain stable until the cache is invalidated.")
        _expect(refreshed_coords == first_coords, "Cached partial supported-context results should not silently refresh mid-map.")
        _expect("Partial merchant/trader resolution succeeded." in first_reason, "Partial supported-context messages should explain that only some selectors resolved.")

        negative_widget = _make_widget(module)
        negative_widget._resolve_rune_trader_coords = lambda _map_id, **_kwargs: None
        negative_calls: list[str] = []

        def _fake_negative_resolve(step, **_kwargs):
            selector = step["npc"]
            negative_calls.append(selector)
            return (9.0, 9.0)

        module.resolve_agent_xy_from_step = _fake_negative_resolve
        module.Map.IsMapReady = lambda: False
        module.time.time = lambda: 200.0
        unsupported, reason, coords = negative_widget._get_supported_context()
        module.Map.IsMapReady = lambda: True
        module.time.time = lambda: 200.1
        refreshed_supported, refreshed_reason, refreshed_coords = negative_widget._get_supported_context()

        _expect(not unsupported and reason == "Map is not ready.", "Negative supported-context cache entries should still return the immediate readiness failure.")
        _expect(all(value is None for value in coords.values()), "Negative supported-context cache entries should not fabricate selector coordinates.")
        _expect(
            not negative_calls,
            "Negative readiness cache entries should stay cached for the current map until the cache is invalidated.",
        )
        _expect(not refreshed_supported and refreshed_reason == reason, "A second supported-context lookup should reuse the cached readiness failure for the current map.")
        _expect(refreshed_coords == coords, "Cached readiness failures should preserve their unresolved coordinate snapshot.")
    finally:
        module.time.time = original_time
        module.Map.GetMapID = original_get_map_id
        module.Map.IsMapReady = original_is_map_ready
        module.Map.IsOutpost = original_is_outpost
        module.Map.IsGuildHall = original_is_guild_hall
        module.Map.GetMapName = original_get_map_name
        module.DEFAULT_NPC_SELECTORS.clear()
        module.DEFAULT_NPC_SELECTORS.update(original_default_selectors)
        module.resolve_agent_xy_from_step = original_resolve_agent_xy


def _test_profile_restore_and_atomic_write_rotation(module, temp_root: Path) -> None:
    widget = _make_widget(module)
    config_path = temp_root / "restore_profile.json"
    backup_path = Path(widget._get_profile_backup_path(str(config_path)))
    backup_path.parent.mkdir(parents=True, exist_ok=True)

    current_payload = {
        "version": module.PROFILE_VERSION,
        "buy_rules": [],
        "sell_rules": [],
        "favorite_outpost_ids": [],
    }
    backup_payload = {
        "version": 0,
        "favorite_outpost_ids": [2],
        "buy_rules": [
            {
                "enabled": True,
                "kind": module.LEGACY_BUY_KIND_ECTO,
                "model_id": int(module.ECTOPLASM_MODEL_ID),
                "target_count": 15,
                "max_per_run": 4,
            }
        ],
        "sell_rules": [],
    }
    config_path.write_text(json.dumps(current_payload, indent=2), encoding="utf-8")
    backup_path.write_text(json.dumps(backup_payload, indent=2), encoding="utf-8")
    widget.config_path = str(config_path)
    widget.preview_ready = True
    widget.preview_plan = module.PlanResult(has_actions=True)
    widget.last_error = "previous error"
    widget.last_execution_summary = "previous execution"

    restored = widget._restore_profile_from_backup()

    _expect(restored, "Restore should succeed when a readable Merchant Rules backup exists.")
    _expect(widget.favorite_outpost_ids == [2], "Restore should reload normalized data from the backup payload.")
    _expect(len(widget.buy_rules) == 1, "Restore should repopulate buy rules from the backup payload.")
    _expect(widget.buy_rules[0].kind == module.BUY_KIND_MATERIAL_TARGET, "Restore should normalize legacy backup payloads before writing them back.")
    _expect(not widget.preview_ready and not widget.preview_plan.has_actions, "Restore should reset preview runtime state after reloading the profile.")
    _expect(widget.last_error == "" and widget.last_execution_summary == "", "Restore should clear stale runtime errors and execution summaries.")
    _expect(widget.status_message == "Merchant Rules live config restored from the last backup.", "Restore should publish the dedicated restored status message.")
    _expect(widget.profile_notice == f"Restored live config from {backup_path.name}.", "Restore should report which backup file was used.")
    saved_payload = json.loads(config_path.read_text(encoding="utf-8"))
    rotated_backup_payload = json.loads(backup_path.read_text(encoding="utf-8"))
    _expect(saved_payload["version"] == module.PROFILE_VERSION, "Restore should rewrite the active profile at the current schema version.")
    _expect(
        rotated_backup_payload["version"] == current_payload["version"],
        "Restoring from backup should rotate the pre-restore active profile into the backup slot before replacing the live file.",
    )

    legacy_restore_widget = _make_widget(module)
    legacy_restore_config = temp_root / "restore_profile_legacy_fallback.json"
    legacy_restore_backup = Path(str(legacy_restore_config) + ".bak")
    legacy_restore_config.write_text(json.dumps(current_payload, indent=2), encoding="utf-8")
    legacy_restore_backup.write_text(json.dumps(backup_payload, indent=2), encoding="utf-8")
    legacy_restore_widget.config_path = str(legacy_restore_config)

    legacy_restored = legacy_restore_widget._restore_profile_from_backup()

    _expect(legacy_restored, "Restore should still fall back to the legacy adjacent backup when needed.")
    _expect(
        legacy_restore_widget.favorite_outpost_ids == [2],
        "Legacy adjacent backups should still restore normalized data.",
    )

    rotation_widget = _make_widget(module)
    rotation_config = temp_root / "atomic_rotation.json"
    rotation_backup = Path(rotation_widget._get_profile_backup_path(str(rotation_config)))
    rotation_backup.parent.mkdir(parents=True, exist_ok=True)
    old_payload = {"version": module.PROFILE_VERSION, "buy_rules": [], "sell_rules": [], "favorite_outpost_ids": [1]}
    older_backup_payload = {"version": module.PROFILE_VERSION, "buy_rules": [], "sell_rules": [], "favorite_outpost_ids": [2]}
    new_payload = {"version": module.PROFILE_VERSION, "buy_rules": [], "sell_rules": [], "favorite_outpost_ids": [1, 2]}
    rotation_config.write_text(json.dumps(old_payload, indent=2), encoding="utf-8")
    rotation_backup.write_text(json.dumps(older_backup_payload, indent=2), encoding="utf-8")

    rotation_widget._write_profile_payload_to_path(
        str(rotation_config),
        new_payload,
        backup_mode="recovery",
    )

    _expect(
        json.loads(rotation_config.read_text(encoding="utf-8"))["favorite_outpost_ids"] == [1, 2],
        "Atomic profile writes should replace the active config with the new payload.",
    )
    _expect(
        json.loads(rotation_backup.read_text(encoding="utf-8"))["favorite_outpost_ids"] == [1],
        "Atomic profile writes should rotate the previous active config into the backup slot.",
    )

    failure_widget = _make_widget(module)
    failure_config = temp_root / "atomic_replace_failure.json"
    failure_backup = Path(failure_widget._get_profile_backup_path(str(failure_config)))
    failure_backup.parent.mkdir(parents=True, exist_ok=True)
    failure_old_payload = {"version": module.PROFILE_VERSION, "buy_rules": [], "sell_rules": [], "favorite_outpost_ids": [7]}
    failure_new_payload = {"version": module.PROFILE_VERSION, "buy_rules": [], "sell_rules": [], "favorite_outpost_ids": [8]}
    failure_config.write_text(json.dumps(failure_old_payload, indent=2), encoding="utf-8")
    original_replace = module.os.replace
    temp_files_before = set(temp_root.glob("atomic_replace_failure.json.tmp-*"))

    def _failing_replace(_src: str, _dst: str):
        raise OSError("simulated replace failure")

    module.os.replace = _failing_replace
    try:
        try:
            failure_widget._write_profile_payload_to_path(
                str(failure_config),
                failure_new_payload,
                backup_mode="recovery",
            )
        except OSError as exc:
            _expect("simulated replace failure" in str(exc), "Atomic-write failure test should surface the simulated replace error.")
        else:
            raise AssertionError("Atomic-write failure test should raise when os.replace fails.")
    finally:
        module.os.replace = original_replace

    temp_files_after = set(temp_root.glob("atomic_replace_failure.json.tmp-*"))
    _expect(
        json.loads(failure_config.read_text(encoding="utf-8"))["favorite_outpost_ids"] == [7],
        "Failed atomic profile writes should leave the original active config untouched.",
    )
    _expect(
        json.loads(failure_backup.read_text(encoding="utf-8"))["favorite_outpost_ids"] == [7],
        "Failed atomic profile writes should still refresh the backup with the last good active config.",
    )
    _expect(temp_files_after == temp_files_before, "Failed atomic profile writes should clean up their temporary files.")


def _test_failed_profile_snapshots_use_recovery_retention(module, temp_root: Path) -> None:
    widget = _make_widget(module)
    config_path = temp_root / "malformed_profile_retention.json"
    config_path.write_text('{"version": 8, "sell_rules": [broken json', encoding="utf-8")
    recovery_dir = Path(widget._get_profile_recovery_dir(str(config_path)))

    original_strftime = module.time.strftime
    original_time = module.time.time
    try:
        formatted_times = iter(
            [
                "20260101-000000",
                "20260101-000001",
                "20260101-000002",
                "20260101-000003",
            ]
        )
        unix_times = iter([1000.001, 1001.002, 1002.003, 1003.004])
        module.time.strftime = lambda _fmt: next(formatted_times)
        module.time.time = lambda: next(unix_times)

        for _ in range(4):
            widget._snapshot_failed_profile(str(config_path))
    finally:
        module.time.strftime = original_strftime
        module.time.time = original_time

    snapshots = sorted(recovery_dir.glob(config_path.name + ".load-failed-*.bak"))
    snapshot_names = [path.name for path in snapshots]
    _expect(
        len(snapshots) == module.FAILED_PROFILE_SNAPSHOT_LIMIT,
        "Failed profile recovery snapshots should be capped per live config.",
    )
    _expect(
        all(path.parent == recovery_dir for path in snapshots),
        "Failed profile recovery snapshots should be written into the Recovery folder.",
    )
    _expect(
        not any("20260101-000000" in name for name in snapshot_names),
        "Snapshot retention should prune the oldest failed-load recovery file first.",
    )


def _test_failed_profile_load_preserves_original_when_snapshot_creation_fails(module, temp_root: Path) -> None:
    widget = _make_widget(module)
    config_path = temp_root / "malformed_profile_without_snapshot.json"
    original_text = '{"version": 8, "sell_rules": [broken json'
    config_path.write_text(original_text, encoding="utf-8")
    widget.config_path = str(config_path)
    recovery_dir = Path(widget._get_profile_recovery_dir(str(config_path)))

    def _raise_snapshot_failure(_config_path: str) -> str:
        raise OSError("disk full")

    widget._snapshot_failed_profile = _raise_snapshot_failure
    widget._load_profile()

    _expect(
        config_path.read_text(encoding="utf-8") == original_text,
        "Profile load failures should still preserve the unreadable profile even when snapshot creation also fails.",
    )
    _expect(
        "no recovery backup was created" in widget.profile_warning.lower(),
        "Load warnings should explain when snapshot creation also failed so recovery options are clear.",
    )
    _expect(
        not list(recovery_dir.glob(config_path.name + ".load-failed-*.bak")),
        "Snapshot-creation failures should not leave behind partial recovery files.",
    )


def main() -> int:
    temp_root = SCRIPT_DIR / "_merchant_rules_regression_tmp"
    shutil.rmtree(temp_root, ignore_errors=True)
    temp_root.mkdir(parents=True, exist_ok=True)
    try:
        module = _load_merchant_rules_module(temp_root)

        tests = [
            ("malformed_profile_is_preserved", lambda: _test_malformed_profile_is_preserved(module, temp_root)),
            ("legacy_profile_normalizes_and_saves", lambda: _test_legacy_profile_normalizes_and_saves(module, temp_root)),
            ("legacy_whitelist_keep_count_migrates_to_per_target_rows", lambda: _test_legacy_whitelist_keep_count_migrates_to_per_target_rows(module, temp_root)),
            ("sell_material_presets_survive_same_frame_table_writeback", lambda: _test_sell_material_presets_survive_same_frame_table_writeback(module)),
            ("sell_clear_list_survives_same_frame_table_writeback", lambda: _test_sell_clear_list_survives_same_frame_table_writeback(module)),
            (
                "legacy_nonsalvageable_gold_sell_rule_is_removed_safely",
                lambda: _test_legacy_nonsalvageable_gold_sell_rule_is_removed_safely(module, temp_root),
            ),
            ("salvage_profile_defaults_are_off", lambda: _test_salvage_profile_defaults_are_off(module, temp_root)),
            ("manual_vendor_profile_defaults_and_roundtrip", lambda: _test_manual_vendor_profile_defaults_and_roundtrip(module, temp_root)),
            ("manual_vendor_runtime_queues_once_per_signature", lambda: _test_manual_vendor_runtime_queues_once_per_signature(module)),
            ("manual_vendor_matching_sell_uses_current_merchant_only", lambda: _test_manual_vendor_matching_sell_uses_current_merchant_only(module)),
            ("manual_vendor_any_merchant_material_fallback", lambda: _test_manual_vendor_any_merchant_material_fallback(module)),
            ("manual_vendor_auto_buy_uses_current_offers", lambda: _test_manual_vendor_auto_buy_uses_current_offers(module)),
            ("exact_rune_sell_rule_profile_roundtrip", lambda: _test_exact_rune_sell_rule_profile_roundtrip(module, temp_root)),
            ("exact_rune_sell_rule_plans_matching_standalone_runes", lambda: _test_exact_rune_sell_rule_plans_matching_standalone_runes(module)),
            ("exact_rune_sell_rule_reserves_names_from_broad_armor_rule", lambda: _test_exact_rune_sell_rule_reserves_names_from_broad_armor_rule(module)),
            ("manual_vendor_exact_rune_sell_runs_at_rune_trader", lambda: _test_manual_vendor_exact_rune_sell_runs_at_rune_trader(module)),
            ("salvage_candidate_evaluation_precedence", lambda: _test_salvage_candidate_evaluation_precedence(module)),
            ("salvage_broad_rarity_selection", lambda: _test_salvage_broad_rarity_selection(module)),
            ("salvage_category_selection", lambda: _test_salvage_category_selection(module)),
            ("salvage_rarity_and_category_filters_combine", lambda: _test_salvage_rarity_and_category_filters_combine(module)),
            ("salvage_filter_summary_describes_combined_filters", lambda: _test_salvage_filter_summary_describes_combined_filters(module)),
            ("salvage_selected_items_block_destroy", lambda: _test_salvage_selected_items_block_destroy(module)),
            (
                "specific_upgrade_salvage_target_accepts_compatible_option",
                lambda: _test_specific_upgrade_salvage_target_accepts_compatible_option(module),
            ),
            (
                "specific_upgrade_salvage_backend_unavailable_blocks",
                lambda: _test_specific_upgrade_salvage_backend_unavailable_blocks(module),
            ),
            (
                "specific_upgrade_salvage_current_bridge_disabled_by_default",
                lambda: _test_specific_upgrade_salvage_current_bridge_disabled_by_default(module),
            ),
            (
                "specific_upgrade_salvage_current_bridge_blocks_execute_before_node",
                lambda: _test_specific_upgrade_salvage_current_bridge_blocks_execute_before_node(module),
            ),
            (
                "specific_upgrade_salvage_protection_blocks_before_bridge",
                lambda: _test_specific_upgrade_salvage_protection_blocks_before_bridge(module),
            ),
            (
                "specific_upgrade_salvage_target_blocks_mismatched_option",
                lambda: _test_specific_upgrade_salvage_target_blocks_mismatched_option(module),
            ),
            (
                "specific_upgrade_salvage_bridge_success_returns_processed",
                lambda: _test_specific_upgrade_salvage_bridge_success_returns_processed(module),
            ),
            (
                "specific_upgrade_salvage_wrong_slot_completion_returns_failed",
                lambda: _test_specific_upgrade_salvage_wrong_slot_completion_returns_failed(module),
            ),
            (
                "specific_upgrade_salvage_bridge_not_called_for_protected_execute",
                lambda: _test_specific_upgrade_salvage_bridge_not_called_for_protected_execute(module),
            ),
            (
                "specific_upgrade_salvage_target_mismatch_still_blocks_destroy",
                lambda: _test_specific_upgrade_salvage_target_mismatch_still_blocks_destroy(module),
            ),
            (
                "specific_upgrade_salvage_target_blocks_default_and_material_options",
                lambda: _test_specific_upgrade_salvage_target_blocks_default_and_material_options(module),
            ),
            ("identify_exact_rarity_claims_before_destroy_and_cleanup", lambda: _test_identify_exact_rarity_claims_before_destroy_and_cleanup(module)),
            ("identify_no_kit_still_claims_selected_items", lambda: _test_identify_no_kit_still_claims_selected_items(module)),
            ("identify_on_inventory_change_queues_auto_pass", lambda: _test_identify_on_inventory_change_queues_auto_pass(module)),
            ("protected_salvage_destroy_overlap_blocks_both", lambda: _test_protected_salvage_destroy_overlap_blocks_both(module)),
            ("build_plan_captures_inventory_and_marks_conditional_stock_buy", lambda: _test_build_plan_captures_inventory_and_marks_conditional_stock_buy(module)),
            ("consumable_crafter_plan_title_gate_blocks_low_rank", lambda: _test_consumable_crafter_plan_title_gate_blocks_low_rank(module)),
            (
                "consumable_crafter_plan_caps_by_skill_gold_and_material_storage",
                lambda: _test_consumable_crafter_plan_caps_by_skill_gold_and_material_storage(module),
            ),
            (
                "consumable_crafter_craft_amount_mode_ignores_existing_xunlai_output",
                lambda: _test_consumable_crafter_craft_amount_mode_ignores_existing_xunlai_output(module),
            ),
            (
                "consumable_crafter_maintain_mode_counts_existing_xunlai_output",
                lambda: _test_consumable_crafter_maintain_mode_counts_existing_xunlai_output(module),
            ),
            (
                "consumable_crafter_plan_reserves_shared_material_storage_across_targets",
                lambda: _test_consumable_crafter_plan_reserves_shared_material_storage_across_targets(module),
            ),
            (
                "consumable_crafter_partial_cap_reports_remaining_material_shortage",
                lambda: _test_consumable_crafter_partial_cap_reports_remaining_material_shortage(module),
            ),
            (
                "consumable_crafter_resource_priority_follows_target_order",
                lambda: _test_consumable_crafter_resource_priority_follows_target_order(module),
            ),
            (
                "consumable_crafter_preview_warns_when_free_inventory_slots_are_low",
                lambda: _test_consumable_crafter_preview_warns_when_free_inventory_slots_are_low(module),
            ),
            (
                "consumable_crafter_execution_prepares_materials_before_opening_crafter",
                lambda: _test_consumable_crafter_execution_prepares_materials_before_opening_crafter(module),
            ),
            ("lower_weapon_protection_hard_overrides_higher_explicit_sell", lambda: _test_lower_weapon_protection_hard_overrides_higher_explicit_sell(module)),
            ("protection_only_rules_hard_claim_before_later_sell_rules", lambda: _test_protection_only_rules_hard_claim_before_later_sell_rules(module)),
            ("weapon_mod_identifier_protection_still_matches_all_rolls", lambda: _test_weapon_mod_identifier_protection_still_matches_all_rolls(module)),
            ("weapon_mod_threshold_protection_uses_inclusive_minimum_rolls", lambda: _test_weapon_mod_threshold_protection_uses_inclusive_minimum_rolls(module)),
            ("weapon_mod_threshold_protection_handles_small_ranges", lambda: _test_weapon_mod_threshold_protection_handles_small_ranges(module)),
            ("weapon_mod_threshold_requires_parsed_roll_value", lambda: _test_weapon_mod_threshold_requires_parsed_roll_value(module)),
            ("weapon_mod_legacy_identifier_wins_over_threshold", lambda: _test_weapon_mod_legacy_identifier_wins_over_threshold(module)),
            ("old_weapon_mod_identifier_profile_loads_without_thresholds", lambda: _test_old_weapon_mod_identifier_profile_loads_without_thresholds(module, temp_root)),
            ("weapon_mod_threshold_profile_round_trips", lambda: _test_weapon_mod_threshold_profile_round_trips(module, temp_root)),
            ("weapon_mod_variant_catalog_expands_prefix_suffix_components", lambda: _test_weapon_mod_variant_catalog_expands_prefix_suffix_components(module)),
            ("old_weapon_mod_identifier_protects_all_exact_variants", lambda: _test_old_weapon_mod_identifier_protects_all_exact_variants(module)),
            ("exact_weapon_mod_variant_protects_only_matching_component", lambda: _test_exact_weapon_mod_variant_protects_only_matching_component(module)),
            ("weapon_mod_variant_threshold_requires_exact_variant_and_roll", lambda: _test_weapon_mod_variant_threshold_requires_exact_variant_and_roll(module)),
            ("weapon_mod_variant_profile_round_trips", lambda: _test_weapon_mod_variant_profile_round_trips(module, temp_root)),
            ("merchant_rules_reconstructs_standalone_weapon_mod_variant_context", lambda: _test_merchant_rules_reconstructs_standalone_weapon_mod_variant_context(module)),
            ("merchant_rules_reconstructs_equipped_weapon_mod_variant_context", lambda: _test_merchant_rules_reconstructs_equipped_weapon_mod_variant_context(module)),
            ("global_weapon_requirement_range_is_inclusive_and_excludes_unknown", lambda: _test_global_weapon_requirement_range_is_inclusive_and_excludes_unknown(module)),
            ("model_specific_weapon_requirement_range_is_inclusive", lambda: _test_model_specific_weapon_requirement_range_is_inclusive(module)),
            ("model_specific_requirement_range_overrides_global_range", lambda: _test_model_specific_requirement_range_overrides_global_range(module)),
            ("unconditional_protected_model_still_protects_all_requirements", lambda: _test_unconditional_protected_model_still_protects_all_requirements(module)),
            ("perfect_base_raw_modifier_snapshot_extracts_stats", lambda: _test_perfect_base_raw_modifier_snapshot_extracts_stats(module)),
            ("all_weapons_perfect_only_requirement_range", lambda: _test_all_weapons_perfect_only_requirement_range(module)),
            ("model_specific_perfect_only_requirement_range", lambda: _test_model_specific_perfect_only_requirement_range(module)),
            ("perfect_base_requires_staff_focus_and_shield_stats", lambda: _test_perfect_base_requires_staff_focus_and_shield_stats(module)),
            ("perfect_only_unidentified_missing_stats_fail_closed", lambda: _test_perfect_only_unidentified_missing_stats_fail_closed(module)),
            ("weapon_requirement_ranges_normalize_swapped_and_zero_endpoints", lambda: _test_weapon_requirement_ranges_normalize_swapped_and_zero_endpoints(module, temp_root)),
            ("legacy_requirement_thresholds_migrate_to_ranges", lambda: _test_legacy_requirement_thresholds_migrate_to_ranges(module, temp_root)),
            ("keep_count_claims_items_before_later_sell_rules", lambda: _test_keep_count_claims_items_before_later_sell_rules(module)),
            ("common_material_rule_claims_stack_before_later_explicit_sell", lambda: _test_common_material_rule_claims_stack_before_later_explicit_sell(module)),
            ("sell_material_targets_keep_counts_apply_per_model", lambda: _test_sell_material_targets_keep_counts_apply_per_model(module)),
            ("sell_material_keep_zero_routes_common_leftovers_to_merchant", lambda: _test_sell_material_keep_zero_routes_common_leftovers_to_merchant(module)),
            ("execute_now_reuses_common_material_keep_zero_leftover_plan", lambda: _test_execute_now_reuses_common_material_keep_zero_leftover_plan(module)),
            ("sell_explicit_targets_keep_counts_apply_per_model", lambda: _test_sell_explicit_targets_keep_counts_apply_per_model(module)),
            ("destroy_material_keep_count_plans_partial_stack", lambda: _test_destroy_material_keep_count_plans_partial_stack(module)),
            ("destroy_material_keep_count_blocks_without_split_slot", lambda: _test_destroy_material_keep_count_blocks_without_split_slot(module)),
            ("nonstackable_destroy_keep_count_stays_whole_item", lambda: _test_nonstackable_destroy_keep_count_stays_whole_item(module)),
            ("destroy_material_targets_keep_counts_apply_per_model", lambda: _test_destroy_material_targets_keep_counts_apply_per_model(module)),
            ("destroy_explicit_targets_keep_counts_apply_per_model", lambda: _test_destroy_explicit_targets_keep_counts_apply_per_model(module)),
            ("execute_partial_destroy_moves_keep_quantity_before_destroy", lambda: _test_execute_partial_destroy_moves_keep_quantity_before_destroy(module)),
            ("execute_now_matches_preview_for_protection_only_rules", lambda: _test_execute_now_matches_preview_for_protection_only_rules(module)),
            ("execute_now_respects_per_target_whitelist_keep_counts", lambda: _test_execute_now_respects_per_target_whitelist_keep_counts(module)),
            ("build_plan_deposits_protected_weapon_matches_conditionally", lambda: _test_build_plan_deposits_protected_weapon_matches_conditionally(module)),
            ("build_plan_does_not_deposit_customized_or_unidentified_only_skips", lambda: _test_build_plan_does_not_deposit_customized_or_unidentified_only_skips(module)),
            ("build_plan_deposits_explicit_keep_targets_on_storage_only_preview", lambda: _test_build_plan_deposits_explicit_keep_targets_on_storage_only_preview(module)),
            ("projected_preview_builds_post_travel_plan_without_travel_entry", lambda: _test_projected_preview_builds_post_travel_plan_without_travel_entry(module)),
            ("projected_preview_keeps_cleanup_visible_from_unsupported_current_map", lambda: _test_projected_preview_keeps_cleanup_visible_from_unsupported_current_map(module)),
            (
                "consumable_multistop_preview_routes_embark_before_destination",
                lambda: _test_consumable_multistop_preview_routes_embark_before_destination(module),
            ),
            (
                "consumable_multistop_execute_crafts_then_runs_destination_work",
                lambda: _test_consumable_multistop_execute_crafts_then_runs_destination_work(module),
            ),
            (
                "consumable_multistop_execute_stops_at_embark_when_only_consumables",
                lambda: _test_consumable_multistop_execute_stops_at_embark_when_only_consumables(module),
            ),
            (
                "consumable_multistop_execute_here_stays_local",
                lambda: _test_consumable_multistop_execute_here_stays_local(module),
            ),
            ("preview_reason_display_hides_projected_suffix_without_mutating_plan", lambda: _test_preview_reason_display_hides_projected_suffix_without_mutating_plan(module)),
            ("preview_reason_display_normalizes_nested_protection_wording", lambda: _test_preview_reason_display_normalizes_nested_protection_wording(module)),
            ("detailed_preview_shows_all_direct_reasons", lambda: _test_detailed_preview_shows_all_direct_reasons(module)),
            (
                "projected_preview_here_availability_tracks_local_services_and_storage",
                lambda: _test_projected_preview_here_availability_tracks_local_services_and_storage(module),
            ),
            (
                "supported_context_generic_services_fall_back_to_name_queries",
                lambda: _test_supported_context_generic_services_fall_back_to_name_queries(module),
            ),
            ("build_plan_deposits_material_keep_remainder_to_storage", lambda: _test_build_plan_deposits_material_keep_remainder_to_storage(module)),
            ("execute_storage_transfers_tracks_partial_moves", lambda: _test_execute_storage_transfers_tracks_partial_moves(module)),
            (
                "execute_storage_transfers_deposits_material_storage_first_when_space_exists",
                lambda: _test_execute_storage_transfers_deposits_material_storage_first_when_space_exists(module),
            ),
            (
                "execute_storage_transfers_uses_live_material_storage_scan_over_stale_cache",
                lambda: _test_execute_storage_transfers_uses_live_material_storage_scan_over_stale_cache(module),
            ),
            (
                "execute_storage_transfers_probes_material_storage_when_quantity_reports_full",
                lambda: _test_execute_storage_transfers_probes_material_storage_when_quantity_reports_full(module),
            ),
            (
                "execute_storage_transfers_partially_fills_material_storage_then_falls_back",
                lambda: _test_execute_storage_transfers_partially_fills_material_storage_then_falls_back(module),
            ),
            (
                "execute_storage_transfers_non_material_uses_regular_storage_only",
                lambda: _test_execute_storage_transfers_non_material_uses_regular_storage_only(module),
            ),
            (
                "execute_storage_transfers_unverified_material_move_skips_regular_fallback",
                lambda: _test_execute_storage_transfers_unverified_material_move_skips_regular_fallback(module),
            ),
            ("execute_now_runs_storage_deposits_as_final_phase", lambda: _test_execute_now_runs_storage_deposits_as_final_phase(module)),
            (
                "execute_here_ignores_travel_and_reports_local_summary",
                lambda: _test_execute_here_ignores_travel_and_reports_local_summary(module),
            ),
            ("rule_custom_names_persist_and_fallback_cleanly", lambda: _test_rule_custom_names_persist_and_fallback_cleanly(module, temp_root)),
            (
                "item_handling_catalog_migration_loads_primary_catalog_and_modelid_fallback",
                lambda: _test_item_handling_catalog_migration_loads_primary_catalog_and_modelid_fallback(module),
            ),
            (
                "catalog_loads_without_deprecated_mirrored_item_catalog",
                lambda: _test_catalog_loads_without_deprecated_mirrored_item_catalog(module, temp_root),
            ),
            (
                "scroll_of_heros_insight_wins_duplicate_model_id_and_searches",
                lambda: _test_scroll_of_heros_insight_wins_duplicate_model_id_and_searches(module),
            ),
            ("display_sorting_helpers_and_summaries_are_case_insensitive", lambda: _test_display_sorting_helpers_and_summaries_are_case_insensitive(module)),
            ("display_sort_reads_preserve_saved_child_entry_order", lambda: _test_display_sort_reads_preserve_saved_child_entry_order(module, temp_root)),
            ("rune_description_templates_resolve_for_tooltips", lambda: _test_rune_description_templates_resolve_for_tooltips(module)),
            ("default_protection_jump_targets_still_use_first_stored_entry", lambda: _test_default_protection_jump_targets_still_use_first_stored_entry(module)),
            ("request_execute_now_queues_only_when_preview_matches", lambda: _test_request_execute_now_queues_only_when_preview_matches(module)),
            ("compare_inventory_detects_preview_drift", lambda: _test_compare_inventory_detects_preview_drift(module)),
            ("compare_inventory_detects_preview_drift_for_projected_preview", lambda: _test_compare_inventory_detects_preview_drift_for_projected_preview(module)),
            ("merchant_sell_verification_confirms_changes_and_reports_timeouts", lambda: _test_merchant_sell_verification_confirms_changes_and_reports_timeouts(module)),
            ("detailed_preview_controls_direct_storage_deposit_reasons", lambda: _test_detailed_preview_controls_direct_storage_deposit_reasons(module)),
            ("build_remote_preview_result_formats_multibox_states", lambda: _test_build_remote_preview_result_formats_multibox_states(module)),
            ("build_remote_execute_result_formats_multibox_states", lambda: _test_build_remote_execute_result_formats_multibox_states(module)),
            ("handle_multibox_result_updates_status_and_ignores_stale_requests", lambda: _test_handle_multibox_result_updates_status_and_ignores_stale_requests(module)),
            ("advance_multibox_batch_handles_preview_and_execute_timeouts", lambda: _test_advance_multibox_batch_handles_preview_and_execute_timeouts(module)),
            ("multibox_sync_preserves_follower_window_geometry_on_disk", lambda: _test_multibox_sync_preserves_follower_window_geometry_on_disk(module, temp_root)),
            ("reload_profile_from_disk_preserves_live_window_geometry", lambda: _test_reload_profile_from_disk_preserves_live_window_geometry(module, temp_root)),
            ("reload_profile_multibox_message_preserves_window_geometry", lambda: _test_reload_profile_multibox_message_preserves_window_geometry(module)),
            ("modifier_parse_cache_reuses_hits_and_prunes_stale_entries", lambda: _test_modifier_parse_cache_reuses_hits_and_prunes_stale_entries(module)),
            ("supported_context_cache_partial_and_negative_entries_refresh_correctly", lambda: _test_supported_context_cache_partial_and_negative_entries_refresh_correctly(module)),
            ("profile_restore_and_atomic_write_rotation", lambda: _test_profile_restore_and_atomic_write_rotation(module, temp_root)),
            ("failed_profile_snapshots_use_recovery_retention", lambda: _test_failed_profile_snapshots_use_recovery_retention(module, temp_root)),
            ("failed_profile_load_preserves_original_when_snapshot_creation_fails", lambda: _test_failed_profile_load_preserves_original_when_snapshot_creation_fails(module, temp_root)),
        ]

        failures: list[tuple[str, str]] = []
        for name, test_fn in tests:
            try:
                test_fn()
            except Exception:
                failures.append((name, traceback.format_exc()))
                print(f"FAIL: {name}")
            else:
                print(f"PASS: {name}")

        if failures:
            print("")
            print(f"{len(failures)} regression test(s) failed:")
            for name, details in failures:
                print(f"- {name}")
                print(details.rstrip())
                print("")
            return 1

        print("")
        print(f"PASS: {len(tests)} Merchant Rules regression checks passed.")
        return 0
    finally:
        shutil.rmtree(temp_root, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
