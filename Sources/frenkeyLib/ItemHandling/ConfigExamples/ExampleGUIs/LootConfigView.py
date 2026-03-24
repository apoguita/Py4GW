from __future__ import annotations

import inspect
from enum import Enum, EnumMeta
from typing import Optional

import PyImGui

from Py4GWCoreLib.ImGui_src.IconsFontAwesome5 import IconsFontAwesome5
from Py4GWCoreLib.ImGui_src.ImGuisrc import ImGui
from Py4GWCoreLib.Item import Bag
from Py4GWCoreLib.enums_src.GameData_enums import DyeColor
from Py4GWCoreLib.enums_src.Item_enums import ItemType, Rarity
from Py4GWCoreLib.enums_src.Model_enums import ModelID
from Py4GWCoreLib.py4gwcorelib_src.Utils import Utils
from Sources.frenkeyLib.ItemHandling.ConfigExamples.LootConfig import LootConfig
from Sources.frenkeyLib.ItemHandling.Items.ItemCache import ITEM_CACHE
from Sources.frenkeyLib.ItemHandling.Items.ItemData import ITEM_DATA
from Sources.frenkeyLib.ItemHandling.Items.item_snapshot import ItemSnapshot
from Sources.frenkeyLib.ItemHandling.Mods import properties as properties_module
from Sources.frenkeyLib.ItemHandling.Mods import upgrades as upgrades_module
from Sources.frenkeyLib.ItemHandling.Mods.properties import ItemProperty
from Sources.frenkeyLib.ItemHandling.Mods.upgrades import Upgrade
from Sources.frenkeyLib.ItemHandling.Rules.base_rule import (
    BaseRule,
    DyesRule,
    ItemSkinRule,
    ItemTypeAndRarityRule,
    ItemTypesRule,
    ModelIdRule,
    PropertyFilter,
    RaritiesRule,
    SalvagesToMaterialRule,
    WeaponSkinRule,
    WeaponTypeRule,
    UpgradeRule,
)
from Sources.frenkeyLib.ItemHandling.Rules.rule_descriptions import RULE_DESCRIPTIONS
from Sources.frenkeyLib.ItemHandling.Rules.types import ItemAction
from Sources.frenkeyLib.ItemHandling.encoded_strings import GWStringEncoded
from Sources.frenkeyLib.ItemHandling.utility import IsWeaponType


def _enum_members(enum_cls: EnumMeta) -> list[Enum]:
    return list(enum_cls) # type: ignore #ignore


def _enum_labels(enum_cls: EnumMeta) -> list[str]:
    return [member.name for member in _enum_members(enum_cls)]


def _normalize_rule_name(rule_type: str) -> str:
    return rule_type.replace("Rule", "").replace("_", " ")


def _decode_item_name(item: Optional[ItemSnapshot]) -> str:
    if item is None:
        return "Empty Slot"

    for encoded in (item.complete_name_enc, item.singular_name, item.name_enc):
        if encoded:
            try:
                decoded = GWStringEncoded(encoded, "").plain
                if decoded:
                    return decoded
            except Exception:
                pass

    if item.data and item.data.name:
        return item.data.name

    return f"{item.item_type.name} ({item.model_id})"


def _safe_combo(label: str, current_index: int, options: list[str]) -> int:
    if not options:
        PyImGui.text(f"{label}: no options")
        return 0

    current_index = max(0, min(current_index, len(options) - 1))
    return PyImGui.combo(label, current_index, options)


class LootConfigView:
    def __init__(self):
        self.config = LootConfig()
        self.selected_rule_index: int = 0
        self.new_rule_type_index: int = 0
        self.property_index: int = 0
        self.rule_search: str = ""
        self.preview_search: str = ""
        self.status_message: str = ""
        self.preview_only_matches: bool = False
        self.inventory_refresh_version: int = 0

        self.rule_type_names = self._build_rule_type_names()
        self.item_type_values = _enum_members(ItemType)
        self.item_type_labels = _enum_labels(ItemType)
        self.rarity_values = _enum_members(Rarity)
        self.rarity_labels = _enum_labels(Rarity)
        self.dye_values = _enum_members(DyeColor)
        self.dye_labels = _enum_labels(DyeColor)
        self.model_id_values = _enum_members(ModelID)
        self.model_id_labels = [f"{member.name} ({member.value})" for member in self.model_id_values]
        self.item_action_values = _enum_members(ItemAction)
        self.item_action_labels = _enum_labels(ItemAction)
        self.upgrade_classes = self._discover_upgrade_classes()
        self.upgrade_labels = [cls.__name__ for cls in self.upgrade_classes]
        self.property_classes = self._discover_property_classes()
        self.property_labels = [cls.__name__ for cls in self.property_classes]
        
        item_skins : list[str] = [item.skin for _, items in ITEM_DATA.data.items() for item in items.values() if item.skin] # filter out empty skins
        self.item_skins = sorted(set(item_skins))
        
        weapon_skins : list[str] = [item.skin for _, items in ITEM_DATA.data.items() for item in items.values() if item.skin and IsWeaponType(item.item_type)] # filter out empty skins and only include weapon skins
        self.weapon_skins = sorted(set(weapon_skins))
        
        self.item_skin_index : int = 0
        self.weapon_skin_index : int = 0

    def _build_rule_type_names(self) -> list[str]:
        rule_classes = [
            rule_cls
            for name, rule_cls in BaseRule._registry.items()
            if name != "BaseRule"
        ]
        rule_classes.sort(
            key=lambda cls: (-int(getattr(getattr(cls, "priority", 0), "value", 0)), cls.__name__)
        )
        return [rule_cls.__name__ for rule_cls in rule_classes]

    def _discover_upgrade_classes(self) -> list[type[Upgrade]]:
        classes: list[type[Upgrade]] = []
        for _, obj in inspect.getmembers(upgrades_module, inspect.isclass):
            if obj.__module__ != upgrades_module.__name__:
                continue
            if obj is Upgrade:
                continue
            mro = getattr(obj, "__mro__", ())
            if any(base.__name__ == "Upgrade" for base in mro):
                classes.append(obj)
        classes.sort(key=lambda cls: cls.__name__)
        return classes

    def _discover_property_classes(self) -> list[type[ItemProperty]]:
        classes: list[type[ItemProperty]] = []
        for _, obj in inspect.getmembers(properties_module, inspect.isclass):
            if obj.__module__ != properties_module.__name__:
                continue
            if obj is ItemProperty:
                continue
            mro = getattr(obj, "__mro__", ())
            if any(base.__name__ == "ItemProperty" for base in mro):
                classes.append(obj)
        classes.sort(key=lambda cls: cls.__name__)
        return classes

    def draw(self) -> None:
        PyImGui.set_next_window_size((900, 600), PyImGui.ImGuiCond.Appearing)
        PyImGui.begin("Loot Config Editor", PyImGui.WindowFlags.NoFlag)
        self._clamp_selection()

        PyImGui.text("Loot Config Editor")
        PyImGui.separator()

        if PyImGui.button("Save"):
            self.config.save()
            self.status_message = f"Saved to {self.config.default_path}"
        PyImGui.same_line(0, -1)
        if PyImGui.button("Reload"):
            self.config.load()
            self.status_message = f"Reloaded from {self.config.default_path}"
            self._clamp_selection()
        PyImGui.same_line(0, -1)
        if PyImGui.button("Refresh Inventory"):
            ITEM_CACHE.reset()
            self.inventory_refresh_version += 1
            self.status_message = "Inventory cache refreshed."

        if self.status_message:
            PyImGui.same_line(0, 5)
            PyImGui.text(self.status_message)

        table_flags = (
            PyImGui.TableFlags.BordersInnerV
            | PyImGui.TableFlags.Resizable
            | PyImGui.TableFlags.SizingStretchProp
        )
        if PyImGui.begin_table("LootConfigViewLayout", 3, table_flags):
            PyImGui.table_setup_column("Rules", PyImGui.TableColumnFlags.WidthStretch, 0.32)
            PyImGui.table_setup_column("Settings", PyImGui.TableColumnFlags.WidthStretch, 0.33)
            PyImGui.table_setup_column("Preview", PyImGui.TableColumnFlags.WidthStretch, 0.35)
            PyImGui.table_next_row()

            PyImGui.table_next_column()
            self._draw_rule_selection_panel()

            PyImGui.table_next_column()
            self._draw_rule_settings_panel()

            PyImGui.table_next_column()
            self._draw_preview_panel()

            PyImGui.end_table()

        PyImGui.end()
        
    def _clamp_selection(self) -> None:
        if not self.config.rules:
            self.selected_rule_index = 0
            return
        self.selected_rule_index = max(0, min(self.selected_rule_index, len(self.config.rules) - 1))

    def _selected_rule(self) -> Optional[BaseRule]:
        if not self.config.rules:
            return None
        self._clamp_selection()
        return self.config.rules[self.selected_rule_index]

    def _draw_rule_selection_panel(self) -> None:
        if PyImGui.begin_child("RuleSelectionPane", (0, 0), True, PyImGui.WindowFlags.NoFlag):
            PyImGui.text("1. Rule Selection")
            PyImGui.separator()

            self.rule_search = PyImGui.input_text("Filter##RuleFilter", self.rule_search)
            if PyImGui.begin_combo("Rule Type##NewRuleType", Utils.humanize_string(self.rule_type_names[self.new_rule_type_index] if self.rule_type_names else "No Rule Types"), PyImGui.ImGuiComboFlags.NoFlag):
                for index, rule_type_name in enumerate(self.rule_type_names):
                    # PyImGui.text(rule_type_name)
                    
                    if PyImGui.selectable(Utils.humanize_string(rule_type_name), index == self.new_rule_type_index, PyImGui.SelectableFlags.NoFlag, (0.0, 0.0)):
                        self.new_rule_type_index = index
                            
                    rule_description = RULE_DESCRIPTIONS.get(BaseRule._registry.get(rule_type_name), "No description available for this rule.")
                    self.show_rule_tooltip(rule_type_name, rule_description) 
                            
                PyImGui.end_combo()
                        
            rule_description = RULE_DESCRIPTIONS.get(BaseRule._registry.get(self.rule_type_names[self.new_rule_type_index]), "No description available for this rule.")
            if rule_description:
                self.show_rule_tooltip(self.rule_type_names[self.new_rule_type_index], rule_description)    
            
            if PyImGui.button("Add Empty Rule") and self.rule_type_names:
                self._add_empty_rule(self.rule_type_names[self.new_rule_type_index])

            PyImGui.separator()

            selected_rule = self._selected_rule()
            if selected_rule is not None:
                if PyImGui.button("Move Up") and self.selected_rule_index > 0:
                    index = self.selected_rule_index
                    self.config.rules[index - 1], self.config.rules[index] = self.config.rules[index], self.config.rules[index - 1]
                    self.selected_rule_index -= 1
                PyImGui.same_line(0, -1)
                if PyImGui.button("Move Down") and self.selected_rule_index < len(self.config.rules) - 1:
                    index = self.selected_rule_index
                    self.config.rules[index + 1], self.config.rules[index] = self.config.rules[index], self.config.rules[index + 1]
                    self.selected_rule_index += 1
                PyImGui.same_line(0, -1)
                if PyImGui.button("Delete Rule"):
                    del self.config.rules[self.selected_rule_index]
                    self._clamp_selection()

            PyImGui.separator()

            search = self.rule_search.strip().lower()
            for index, rule in enumerate(self.config.rules):
                label = f"{index + 1}. {rule.name or _normalize_rule_name(type(rule).__name__)} [{type(rule).__name__}]"
                if search and search not in label.lower():
                    continue

                selected = index == self.selected_rule_index
                if PyImGui.selectable(label, selected, PyImGui.SelectableFlags.NoFlag, (0.0, 0.0)):
                    self.selected_rule_index = index

                PyImGui.same_line(0, 10)
                validity_text = "valid" if rule.is_valid() else "incomplete"
                PyImGui.text(f"({validity_text})")

            if not self.config.rules:
                PyImGui.text("No rules yet.")

        PyImGui.end_child()

    def show_rule_tooltip(self, rule_type_name, rule_description):
        if rule_description:
            if PyImGui.is_item_hovered():
                PyImGui.set_next_window_size((400, 0), PyImGui.ImGuiCond.Always)
                PyImGui.begin_tooltip()
                ImGui.text_colored(Utils.humanize_string(rule_type_name), (255, 100, 0, 255), 15, "Bold")
                ImGui.text_wrapped(rule_description)
                PyImGui.end_tooltip()

    def _add_empty_rule(self, rule_type_name: str) -> None:
        rule_cls = BaseRule._registry.get(rule_type_name)
        if rule_cls is None:
            return

        pretty_name = _normalize_rule_name(rule_type_name)
        rule = rule_cls(f"New {pretty_name}")
        if hasattr(rule, "action"):
            rule.action = ItemAction.PickUp

        if isinstance(rule, (WeaponSkinRule, WeaponTypeRule)):
            rule.requirement_max = 13

        self.config.rules.append(rule)
        self.selected_rule_index = len(self.config.rules) - 1

    def _draw_rule_settings_panel(self) -> None:
        if PyImGui.begin_child("RuleSettingsPane", (0, 0), True, PyImGui.WindowFlags.NoFlag):
            PyImGui.text("2. Rule Settings")
            PyImGui.separator()

            rule = self._selected_rule()
            if rule is None:
                PyImGui.text("Select a rule to edit it.")
            else:
                rule.name = PyImGui.input_text("Name", rule.name)

                # current_action = self.item_action_values.index(rule.action) if rule.action in self.item_action_values else 0
                # action_index = _safe_combo("Action", current_action, self.item_action_labels)
                # rule.action = ItemAction(self.item_action_values[action_index].value)

                PyImGui.text(f"Type: {type(rule).__name__}")
                PyImGui.text(f"Valid: {'yes' if rule.is_valid() else 'no'}")
                PyImGui.separator()

                if isinstance(rule, ModelIdRule):
                    self._draw_model_id_rule(rule)
                elif isinstance(rule, ItemTypesRule):
                    self._draw_multi_enum_rule("Item Types", rule.item_types, self.item_type_values)
                elif isinstance(rule, RaritiesRule):
                    self._draw_multi_enum_rule("Rarities", rule.rarities, self.rarity_values)
                elif isinstance(rule, DyesRule):
                    self._draw_multi_enum_rule("Dye Colors", rule.dye_colors, self.dye_values)
                elif isinstance(rule, ItemSkinRule):
                    self.item_skin_index = self._draw_string_list_editor("Item Skins", rule.item_skins, "Skin", self.item_skins, self.item_skin_index)
                elif isinstance(rule, ItemTypeAndRarityRule):
                    self._draw_multi_enum_rule("Item Types", rule.item_types, self.item_type_values)
                    PyImGui.separator()
                    self._draw_multi_enum_rule("Rarities", rule.rarities, self.rarity_values)
                elif isinstance(rule, WeaponSkinRule):
                    self.weapon_skin_index = self._draw_string_list_editor("Weapon Skins", rule.weapon_skins, "Weapon Skin", self.weapon_skins, self.weapon_skin_index)
                    PyImGui.separator()
                    self._draw_requirement_editor(rule)
                    PyImGui.separator()
                    self._draw_property_filters_editor(rule.properties)
                elif isinstance(rule, WeaponTypeRule):
                    self._draw_single_enum_selector("Weapon Type", rule, "item_type", self.item_type_values)
                    self._draw_requirement_editor(rule)
                    PyImGui.separator()
                    self._draw_property_filters_editor(rule.properties)
                elif isinstance(rule, UpgradeRule):
                    self._draw_upgrade_rule(rule)
                elif isinstance(rule, SalvagesToMaterialRule):
                    materials = [
                        ModelID.Iron_Ingot,
                        ModelID.Bone,
                        ModelID.Feather,
                        ModelID.Pile_Of_Glittering_Dust,
                        ModelID.Plant_Fiber,
                    ]
                    self._draw_multi_enum_rule("Materials", rule.materials, materials, label_builder=lambda m: f"{m.name} ({m.value})")
                else:
                    PyImGui.text("No custom editor implemented for this rule.")

        PyImGui.end_child()

    def _draw_preview_panel(self) -> None:
        if PyImGui.begin_child("RulePreviewPane", (0, 0), True, PyImGui.WindowFlags.NoFlag):
            PyImGui.text("3. Inventory Preview")
            PyImGui.separator()

            self.preview_search = PyImGui.input_text("Filter Items##PreviewFilter", self.preview_search)
            self.preview_only_matches = PyImGui.checkbox("Only show selected rule matches", self.preview_only_matches)

            PyImGui.separator()

            selected_rule = self._selected_rule()
            items = self._flatten_inventory_snapshot()
            filtered_items = [row for row in items if self._matches_preview_filter(row[2], selected_rule)]

            PyImGui.text(f"Visible items: {len(filtered_items)}")
            PyImGui.text(f"Cache version: {self.inventory_refresh_version}")
            PyImGui.separator()

            table_flags = (
                PyImGui.TableFlags.Borders
                | PyImGui.TableFlags.RowBg
                | PyImGui.TableFlags.ScrollY
                | PyImGui.TableFlags.SizingStretchProp
            )
            if PyImGui.begin_table("LootPreviewTable", 5, table_flags):
                PyImGui.table_setup_column("Bag", PyImGui.TableColumnFlags.WidthFixed, 65)
                PyImGui.table_setup_column("Slot", PyImGui.TableColumnFlags.WidthFixed, 45)
                PyImGui.table_setup_column("Item", PyImGui.TableColumnFlags.WidthStretch, 180)
                PyImGui.table_setup_column("Type", PyImGui.TableColumnFlags.WidthFixed, 90)
                PyImGui.table_setup_column("Selected Rule", PyImGui.TableColumnFlags.WidthFixed, 100)
                PyImGui.table_headers_row()

                for bag_name, slot, item in filtered_items:
                    item_id = item.id if item else 0
                    selected_match = selected_rule.applies(item_id) if selected_rule and item else False
                    final_action = self._action_for_item(item_id)

                    PyImGui.table_next_row()
                    PyImGui.table_next_column()
                    PyImGui.text(bag_name)
                    PyImGui.table_next_column()
                    PyImGui.text(str(slot))
                    PyImGui.table_next_column()
                    PyImGui.text(_decode_item_name(item))
                    PyImGui.table_next_column()
                    PyImGui.text(item.item_type.name if item else "-")
                    PyImGui.table_next_column()
                    PyImGui.text_colored(IconsFontAwesome5.ICON_CHECK if selected_match else IconsFontAwesome5.ICON_TIMES,
                                         (0, 1, 0, 1) if selected_match else (1, 0, 0, 1))

                PyImGui.end_table()

            if not filtered_items:
                PyImGui.text("No inventory items match the current preview filters.")

        PyImGui.end_child()

    def _flatten_inventory_snapshot(self) -> list[tuple[str, int, Optional[ItemSnapshot]]]:
        snapshot = ITEM_CACHE.get_inventory_snapshot(Bag.Backpack, Bag.Max)
        rows: list[tuple[str, int, Optional[ItemSnapshot]]] = []
        for bag, bag_snapshot in snapshot.items():
            for slot, item in bag_snapshot.items():
                rows.append((bag.name, slot, item))
        return rows

    def _matches_preview_filter(self, item: Optional[ItemSnapshot], selected_rule: Optional[BaseRule]) -> bool:
        if item is None:
            return False

        search = self.preview_search.strip().lower()
        if search:
            haystack = " ".join(
                [
                    _decode_item_name(item),
                    item.item_type.name,
                    item.rarity.name,
                    str(item.model_id),
                ]
            ).lower()
            if search not in haystack:
                return False

        if self.preview_only_matches and selected_rule is not None:
            return selected_rule.applies(item.id)

        return True

    def _action_for_item(self, item_id: int) -> ItemAction:
        for rule in self.config.rules:
            if rule.applies(item_id):
                return rule.action
        return ItemAction.NONE

    def _draw_single_enum_selector(self, label: str, obj: object, attribute: str, values: list) -> None:
        current_value = getattr(obj, attribute, None)
        labels = [value.name for value in values]
        index = values.index(current_value) if current_value in values else 0
        index = _safe_combo(label, index, labels)
        setattr(obj, attribute, values[index] if values else None)

    def _draw_multi_enum_rule(self, label: str, selected_values: list, values: list, label_builder=None) -> None:
        label_builder = label_builder or (lambda value: value.name)
        PyImGui.text(label)
        if PyImGui.begin_child(f"{label}Child", (0, 180), True, PyImGui.WindowFlags.NoFlag):
            for value in values:
                is_selected = value in selected_values
                new_selected = PyImGui.checkbox(f"{label_builder(value)}##{label}_{value}", is_selected)
                if new_selected != is_selected:
                    if new_selected:
                        selected_values.append(value)
                    else:
                        selected_values.remove(value)
        PyImGui.end_child()

    def _draw_string_list_editor(self, label: str, values: list[str], item_label: str, available_values: list[str] = [], selected_index: int = 0) -> int:
        PyImGui.text(label + (f" ({len(available_values)})"))
        remove_index = -1
        
        selected_index = PyImGui.combo(f"##{label}Available", selected_index, available_values)  # Show available values in a combo box for reference
        PyImGui.same_line(0, -1)
        if PyImGui.button(f"Add {item_label}##{label}_AddAvailable") and available_values:
            if selected_index >= 0 and selected_index < len(available_values):
                if available_values[selected_index] not in values:
                    values.append(available_values[selected_index])
        
        if PyImGui.begin_child(f"{label}List", (0, 150), True, PyImGui.WindowFlags.NoFlag):
            for index, value in enumerate(values):
                PyImGui.text(f"{value}")
                PyImGui.same_line(0, -1)
                if PyImGui.button(f"X##{label}_Delete_{index}"):
                    remove_index = index
        PyImGui.end_child()

        if remove_index >= 0:
            del values[remove_index]
            
        return selected_index

    def _draw_model_id_rule(self, rule: ModelIdRule) -> None:
        model_index = self.model_id_values.index(rule.model_id) if rule.model_id in self.model_id_values else 0
        model_index = _safe_combo("Model ID", model_index, self.model_id_labels)
        rule.model_id = ModelID(self.model_id_values[model_index]) if self.model_id_values else None

    def _draw_requirement_editor(self, rule: WeaponSkinRule | WeaponTypeRule) -> None:
        rule.requirement_min = max(0, PyImGui.input_int("Requirement Min", rule.requirement_min))
        rule.requirement_max = max(rule.requirement_min, PyImGui.input_int("Requirement Max", rule.requirement_max))
        rule.only_max_damage = PyImGui.checkbox("Only Max Damage", rule.only_max_damage)

    def _draw_upgrade_rule(self, rule: UpgradeRule) -> None:
        if not self.upgrade_labels:
            PyImGui.text("No upgrade classes found.")
            return

        current_class = type(rule.upgrade) if rule.upgrade is not None else None
        PyImGui.text(f"Current Upgrade: {current_class.__name__ if current_class else 'None'}")
        
        current_index = self.upgrade_labels.index(current_class.__name__) if current_class and current_class.__name__ in self.upgrade_labels else 0
        selected_index = _safe_combo("Upgrade", current_index, self.upgrade_labels)
        selected_class = self.upgrade_classes[selected_index]
        if current_class and current_class.__name__ != selected_class.__name__:
            try:
                rule.upgrade = selected_class()
            except Exception:
                pass

    def _draw_property_filters_editor(self, properties: list[PropertyFilter]) -> None:
        PyImGui.text("Property Filters")
        remove_index = -1
        if PyImGui.begin_child("PropertyFilterList", (0, 180), True, PyImGui.WindowFlags.NoFlag):
            
            prop = self.property_classes[self.property_index] if self.property_classes else None
            
            if PyImGui.begin_combo("Rule Type##NewRuleType", Utils.humanize_string(prop.__name__) if prop else "", PyImGui.ImGuiComboFlags.NoFlag):
                for index, p in enumerate(self.property_classes):
                    # PyImGui.text(rule_type_name)
                    
                    if PyImGui.selectable(Utils.humanize_string(p.__name__), index == self.property_index, PyImGui.SelectableFlags.NoFlag, (0.0, 0.0)):
                        self.property_index = index
                                                        
                PyImGui.end_combo()
            
            PyImGui.same_line(0, -1)
            if PyImGui.button("Add Property") and self.property_classes:
                selected_class = self.property_classes[self.property_index] if self.property_classes and self.property_index < len(self.property_classes) else None
                
                try:
                    if selected_class:
                        properties.append({"property_type": selected_class.__name__, "modifier_arg": 0})
                except Exception:
                    pass
            
            PyImGui.separator()
                                
            for index, prop in enumerate(properties):
                property_type_name = str(prop.get("property_type", "")) if isinstance(prop, dict) else type(prop).__name__
                modifier_arg = int(prop.get("modifier_arg", -1)) if isinstance(prop, dict) else int(prop.modifier.arg)
                PyImGui.text(f"{Utils.humanize_string(property_type_name)}")

                PyImGui.same_line(0, -1)
                if PyImGui.button(f"X##PropertyDelete_{index}"):
                    remove_index = index
        PyImGui.end_child()

        if remove_index >= 0:
            del properties[remove_index]

        if PyImGui.button("Add Property Filter") and self.property_labels:
            properties.append({"property_type": self.property_labels[0], "modifier_arg": 0})


_LOOT_CONFIG_VIEW: Optional[LootConfigView] = None


def draw_loot_config_view() -> None:
    global _LOOT_CONFIG_VIEW
    if _LOOT_CONFIG_VIEW is None:
        _LOOT_CONFIG_VIEW = LootConfigView()
    _LOOT_CONFIG_VIEW.draw()
