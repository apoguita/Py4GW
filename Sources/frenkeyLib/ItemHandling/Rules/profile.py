from __future__ import annotations

import json
import os
from typing import Any, Iterator, Optional

from Py4GW import Console
from Sources.frenkeyLib.ItemHandling.Rules.base_rule import BaseRule
from Sources.frenkeyLib.ItemHandling.Rules.types import ItemAction

class RuleProfile:
    def __init__(self, name: str, rules: Optional[list[BaseRule]] = None):
        self.name = name
        self.rule_groups: dict[str, list[BaseRule]] = {}
        self.group_order: list[str] = []
        self._cache_dirty: bool = True
        self._evaluation_rules: tuple[BaseRule, ...] = ()
        self._all_rules: tuple[BaseRule, ...] = ()

        if rules:
            for rule in rules:
                self.add_rule(rule)

    def invalidate_cache(self) -> None:
        self._cache_dirty = True

    def _rebuild_cache_if_needed(self) -> None:
        if not self._cache_dirty:
            return

        all_rules: list[BaseRule] = []
        evaluation_rules: list[BaseRule] = []

        for rule_type in self.group_order:
            group = self.rule_groups.get(rule_type, [])
            if not group:
                continue

            all_rules.extend(group)
            for rule in group:
                if rule.is_valid():
                    evaluation_rules.append(rule)

        self._all_rules = tuple(all_rules)
        self._evaluation_rules = tuple(evaluation_rules)
        self._cache_dirty = False

    @staticmethod
    def get_profiles_directory() -> str:
        project_path = Console.get_projects_path()
        profile_dir = os.path.join(project_path, "Widgets", "Config", "ItemHandling", "Profiles")
        os.makedirs(profile_dir, exist_ok=True)
        return profile_dir

    @property
    def default_path(self) -> str:
        return os.path.join(self.get_profiles_directory(), f"{self.name}.json")

    def add_rule(self, rule: BaseRule, rule_type: Optional[str] = None, index: Optional[int] = None) -> None:
        rule_type_name = rule_type or type(rule).__name__
        if rule_type_name not in self.rule_groups:
            self.rule_groups[rule_type_name] = []
            self.group_order.append(rule_type_name)

        group = self.rule_groups[rule_type_name]
        if index is None or index < 0 or index >= len(group):
            group.append(rule)
        else:
            group.insert(index, rule)

        self._cache_dirty = True

    def remove_rule(self, rule: BaseRule) -> None:
        for rule_type_name in list(self.group_order):
            group = self.rule_groups.get(rule_type_name, [])
            if rule in group:
                group.remove(rule)
                if len(group) == 0:
                    self.rule_groups.pop(rule_type_name, None)
                    self.group_order.remove(rule_type_name)
                self._cache_dirty = True
                return

    def move_rule(self, rule_type: str, from_index: int, to_index: int) -> bool:
        group = self.rule_groups.get(rule_type, None)
        if not group:
            return False

        if from_index < 0 or from_index >= len(group):
            return False

        to_index = max(0, min(to_index, len(group) - 1))
        if from_index == to_index:
            return True

        rule = group.pop(from_index)
        group.insert(to_index, rule)
        self._cache_dirty = True
        return True

    def move_group(self, from_index: int, to_index: int) -> bool:
        if from_index < 0 or from_index >= len(self.group_order):
            return False

        to_index = max(0, min(to_index, len(self.group_order) - 1))
        if from_index == to_index:
            return True

        group_name = self.group_order.pop(from_index)
        self.group_order.insert(to_index, group_name)
        self._cache_dirty = True
        return True

    def iter_rules(self, rule_type: Optional[str] = None) -> Iterator[BaseRule]:
        if rule_type is not None:
            for rule in self.rule_groups.get(rule_type, []):
                yield rule
            return

        for group_name in self.group_order:
            for rule in self.rule_groups.get(group_name, []):
                yield rule

    def get_rules_of_type(self, rule_type: str) -> list[BaseRule]:
        return self.rule_groups.get(rule_type, [])

    def get_evaluation_rules(self) -> tuple[BaseRule, ...]:
        self._rebuild_cache_if_needed()
        return self._evaluation_rules

    def get_matching_rule(self, item_id: int) -> Optional[BaseRule]:
        evaluation_rules = self.get_evaluation_rules()
        for rule in evaluation_rules:
            if rule.applies(item_id):
                return rule
        return None

    def get_action_for_item(self, item_id: int) -> ItemAction:
        rule = self.get_matching_rule(item_id)
        return rule.action if rule else ItemAction.NONE

    def to_dict(self) -> dict[str, Any]:
        grouped_rules: dict[str, list[dict[str, Any]]] = {}
        for rule_type in self.group_order:
            group = self.rule_groups.get(rule_type, [])
            if not group:
                continue
            grouped_rules[rule_type] = [rule.to_dict() for rule in group]

        return {
            "format": "itemhandling-rule-profile",
            "version": 2,
            "name": self.name,
            "group_order": list(self.group_order),
            "rule_groups": grouped_rules,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "RuleProfile":
        name = str(payload.get("name", "Default"))
        profile = cls(name=name)

        # New grouped format (v2+)
        groups = payload.get("rule_groups", None)
        group_order = payload.get("group_order", None)
        if isinstance(groups, dict):
            ordered_group_names: list[str] = []
            if isinstance(group_order, list):
                ordered_group_names = [
                    str(group_name) for group_name in group_order
                    if isinstance(group_name, str) and group_name in groups
                ]
            for key in groups.keys():
                if key not in ordered_group_names:
                    ordered_group_names.append(str(key))

            for group_name in ordered_group_names:
                rows = groups.get(group_name, [])
                if not isinstance(rows, list):
                    continue
                for row in rows:
                    if not isinstance(row, dict):
                        continue
                    rule = BaseRule.from_dict(row)
                    if rule is not None:
                        profile.add_rule(rule, rule_type=group_name)
            profile._rebuild_cache_if_needed()
            return profile

        profile._rebuild_cache_if_needed()
        return profile

    def to_json(self, indent: int = 4) -> str:
        return json.dumps(self.to_dict(), indent=indent)

    @classmethod
    def from_json(cls, json_payload: str) -> "RuleProfile":
        return cls.from_dict(json.loads(json_payload))

    def save(self, path: Optional[str] = None) -> str:
        target_path = path or self.default_path
        target_directory = os.path.dirname(target_path)
        if target_directory:
            os.makedirs(target_directory, exist_ok=True)

        with open(target_path, "w", encoding="utf-8") as file:
            json.dump(self.to_dict(), file, indent=4)

        return target_path

    @classmethod
    def load(cls, path: str) -> "RuleProfile":
        try:
            with open(path, "r", encoding="utf-8") as file:
                payload = json.load(file)
        
        except (FileNotFoundError, json.JSONDecodeError):
            return cls.from_dict({})
        
        return cls.from_dict(payload)

    @classmethod
    def load_by_name(cls, name: str) -> "RuleProfile":
        path = os.path.join(cls.get_profiles_directory(), f"{name}.json")
        return cls.load(path)
