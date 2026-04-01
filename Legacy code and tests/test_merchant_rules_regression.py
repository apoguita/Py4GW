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
    python "Legacy code and tests/test_merchant_rules_regression.py"
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


def _ensure_package(name: str) -> types.ModuleType:
    module = sys.modules.get(name)
    if module is None:
        module = types.ModuleType(name)
        module.__path__ = []
        sys.modules[name] = module
    return module


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

    class DummyModelValue:
        def __init__(self, value: int):
            self.value = value

    class DummyModelID:
        Glob_Of_Ectoplasm = DummyModelValue(930)
        Salvage_Kit = DummyModelValue(2992)

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
    core.ModelID = DummyModelID
    core.Player = types.SimpleNamespace(
        GetAccountEmail=lambda: "merchant.rules@example.com",
        GetName=lambda: "Merchant Rules Tester",
        GetXY=lambda: (0.0, 0.0),
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
    sys.modules["Py4GWCoreLib"] = core

    _ensure_package("Py4GWCoreLib.enums_src")
    item_enums = types.ModuleType("Py4GWCoreLib.enums_src.Item_enums")
    item_enums.ItemType = ItemType
    sys.modules["Py4GWCoreLib.enums_src.Item_enums"] = item_enums

    _ensure_package("Py4GWCoreLib.py4gwcorelib_src")
    widget_manager = types.ModuleType("Py4GWCoreLib.py4gwcorelib_src.WidgetManager")
    widget_manager.get_widget_handler = lambda: types.SimpleNamespace(
        get_widget_info=lambda _name: None,
        is_widget_enabled=lambda _name: False,
    )
    sys.modules["Py4GWCoreLib.py4gwcorelib_src.WidgetManager"] = widget_manager

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


def _prime_initialized_widget(module, widget):
    widget.catalog_loaded = True
    widget.initialized = True
    widget.account_key = widget._get_account_key()
    widget.map_snapshot = int(module.Map.GetMapID() or 0)
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
    rune_identifiers: list[str] | None = None,
    weapon_mod_identifiers: list[str] | None = None,
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
        standalone_kind=standalone_kind,
        rune_identifiers=list(rune_identifiers or []),
        weapon_mod_identifiers=list(weapon_mod_identifiers or []),
    )


def _rarity_flags(*enabled: str) -> dict[str, bool]:
    enabled_keys = {str(key or "").strip().lower() for key in enabled}
    return {
        "white": "white" in enabled_keys,
        "blue": "blue" in enabled_keys,
        "purple": "purple" in enabled_keys,
        "gold": "gold" in enabled_keys,
        "green": "green" in enabled_keys,
    }


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
    _expect(sell_rule.protected_weapon_requirement_rules == [], "Bad requirement-rule data should normalize to an empty list.")
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
                    module.WeaponRequirementRule(model_id=111, max_requirement=8),
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
                    module.WeaponRequirementRule(model_id=111, max_requirement=9),
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
            "Protected by requirement rule:",
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
                    module.WeaponRequirementRule(model_id=111, max_requirement=9),
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
                    module.WeaponRequirementRule(model_id=111, max_requirement=8),
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
    travel_widget = _prime_initialized_widget(module, _make_widget(module))
    travel_widget.preview_plan = module.PlanResult(
        supported_map=False,
        supported_reason="Travel to the selected outpost before merchant handling.",
        travel_to_outpost_id=2,
        travel_to_outpost_name="Regression Harbor",
    )
    travel_result = travel_widget.build_remote_preview_result()
    _expect(travel_result["status_label"] == "Travel", "Travel previews should report the dedicated Travel status.")
    _expect(travel_result["summary"] == "Travel first: Regression Harbor", "Travel previews should name the required outpost in the summary.")
    _expect(
        travel_result["detail"] == "Travel to the selected outpost before merchant handling.",
        "Travel previews should preserve the travel detail text for followers.",
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
        conditional_result["summary"] == "1 actionable, 1 blocked, 1 conditional.",
        "Conditional-only previews should include actionable, blocked, and conditional counts.",
    )
    _expect(
        conditional_result["detail"] == "Conditional actions need live merchant or trader confirmation at runtime.",
        "Conditional-only previews should explain why follower actions remain conditional.",
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
        ready_result["summary"] == "2 actionable, 1 blocked, 1 conditional.",
        "Ready previews should include actionable, blocked, and conditional counts when merchant stock checks remain.",
    )
    _expect(
        ready_result["detail"] == "Conditional actions need live merchant or trader confirmation at runtime.",
        "Ready previews should still explain runtime conditionality when present.",
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
        return types.SimpleNamespace(
            runes=[types.SimpleNamespace(rune=types.SimpleNamespace(identifier="rune.alpha"))],
            weapon_mods=[types.SimpleNamespace(weapon_mod=types.SimpleNamespace(identifier="mod.beta"))],
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

    widget.inventory_modifier_cache[2002] = module.InventoryModifierCacheEntry(signature=(222,), parsed=module.ParsedInventoryModifiers())
    widget._prune_inventory_modifier_cache({1001})
    _expect(1001 in widget.inventory_modifier_cache, "Active inventory items should remain in the modifier cache after pruning.")
    _expect(2002 not in widget.inventory_modifier_cache, "Items that leave inventory should be pruned from the modifier cache.")


def _test_supported_context_cache_partial_and_negative_entries_refresh_correctly(module) -> None:
    original_time = module.time.time
    original_get_map_id = module.Map.GetMapID
    original_is_map_ready = module.Map.IsMapReady
    original_is_outpost = module.Map.IsOutpost
    original_get_map_name = module.Map.GetMapName
    original_default_selectors = dict(module.DEFAULT_NPC_SELECTORS)
    original_resolve_agent_xy = module.resolve_agent_xy_from_step

    try:
        module.Map.GetMapID = lambda: 100
        module.Map.IsMapReady = lambda: True
        module.Map.IsOutpost = lambda: True
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
            selector = step["npc"]
            resolve_calls.append((resolution_phase["value"], selector))
            if resolution_phase["value"] == 0:
                return {
                    "merchant_selector": (1.0, 1.0),
                    "materials_selector": None,
                    "rare_selector": (3.0, 3.0),
                }[selector]
            return {
                "merchant_selector": (11.0, 11.0),
                "materials_selector": (22.0, 22.0),
                "rare_selector": (33.0, 33.0),
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
            len(resolve_calls) == 3,
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
            (
                "legacy_nonsalvageable_gold_sell_rule_is_removed_safely",
                lambda: _test_legacy_nonsalvageable_gold_sell_rule_is_removed_safely(module, temp_root),
            ),
            ("build_plan_captures_inventory_and_marks_conditional_stock_buy", lambda: _test_build_plan_captures_inventory_and_marks_conditional_stock_buy(module)),
            ("lower_weapon_protection_hard_overrides_higher_explicit_sell", lambda: _test_lower_weapon_protection_hard_overrides_higher_explicit_sell(module)),
            ("protection_only_rules_hard_claim_before_later_sell_rules", lambda: _test_protection_only_rules_hard_claim_before_later_sell_rules(module)),
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
            ("build_plan_deposits_material_keep_remainder_to_storage", lambda: _test_build_plan_deposits_material_keep_remainder_to_storage(module)),
            ("execute_storage_transfers_tracks_partial_moves", lambda: _test_execute_storage_transfers_tracks_partial_moves(module)),
            ("execute_now_runs_storage_deposits_as_final_phase", lambda: _test_execute_now_runs_storage_deposits_as_final_phase(module)),
            ("rule_custom_names_persist_and_fallback_cleanly", lambda: _test_rule_custom_names_persist_and_fallback_cleanly(module, temp_root)),
            ("request_execute_now_queues_only_when_preview_matches", lambda: _test_request_execute_now_queues_only_when_preview_matches(module)),
            ("compare_inventory_detects_preview_drift", lambda: _test_compare_inventory_detects_preview_drift(module)),
            ("merchant_sell_verification_confirms_changes_and_reports_timeouts", lambda: _test_merchant_sell_verification_confirms_changes_and_reports_timeouts(module)),
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
