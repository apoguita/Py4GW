from __future__ import annotations

import ast
import re
import sys
from collections import defaultdict
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
RECIPES_DIR = REPO_ROOT / "Sources" / "modular_bot" / "recipes"
DOCS_DIR = REPO_ROOT / "Sources" / "modular_bot" / "Docs"
ACTIONS_DOCS_DIR = DOCS_DIR / "actions"

MODULES = {
    "movement": RECIPES_DIR / "actions_movement.py",
    "targeting": RECIPES_DIR / "actions_targeting.py",
    "interaction": RECIPES_DIR / "actions_interaction.py",
    "party": RECIPES_DIR / "actions_party.py",
    "inventory": RECIPES_DIR / "actions_inventory.py",
}

ACTION_DOC_FILES = {
    "movement": ACTIONS_DOCS_DIR / "movement.md",
    "interaction": ACTIONS_DOCS_DIR / "interaction.md",
    "targeting": ACTIONS_DOCS_DIR / "targeting.md",
    "party": ACTIONS_DOCS_DIR / "party.md",
    "inventory": ACTIONS_DOCS_DIR / "inventory.md",
}

INDEX_PATH = ACTIONS_DOCS_DIR / "index.md"
ANCHOR_RE = re.compile(r"<a\s+id=\"action-([a-z0-9_]+)\"\s*></a>")
INDEX_ROW_RE = re.compile(
    r"\|\s*`([a-z0-9_]+)`\s*\|\s*`([a-z0-9_]+)`\s*\|\s*`([A-Za-z0-9_]+)`\s*\|\s*\[([a-z0-9_]+)\]\(([^)]+)\)\s*\|"
)


def parse_registry_actions() -> tuple[dict[str, str], dict[str, str]]:
    action_to_subsystem: dict[str, str] = {}
    action_to_handler: dict[str, str] = {}

    for subsystem, path in MODULES.items():
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in tree.body:
            handlers_dict = None
            if (
                isinstance(node, ast.AnnAssign)
                and isinstance(node.target, ast.Name)
                and node.target.id == "HANDLERS"
                and isinstance(node.value, ast.Dict)
            ):
                handlers_dict = node.value
            elif (
                isinstance(node, ast.Assign)
                and any(isinstance(t, ast.Name) and t.id == "HANDLERS" for t in node.targets)
                and isinstance(node.value, ast.Dict)
            ):
                handlers_dict = node.value

            if handlers_dict is None:
                continue

            for key_node, value_node in zip(handlers_dict.keys, handlers_dict.values):
                if not (isinstance(key_node, ast.Constant) and isinstance(key_node.value, str)):
                    continue
                if not isinstance(value_node, ast.Name):
                    continue
                action = key_node.value
                action_to_subsystem[action] = subsystem
                action_to_handler[action] = value_node.id

    return action_to_subsystem, action_to_handler


def parse_doc_actions() -> tuple[dict[str, str], dict[str, list[str]]]:
    doc_action_to_subsystem: dict[str, str] = {}
    duplicates_by_subsystem: dict[str, list[str]] = defaultdict(list)

    for subsystem, path in ACTION_DOC_FILES.items():
        text = path.read_text(encoding="utf-8")
        found = ANCHOR_RE.findall(text)
        seen: set[str] = set()
        for action in found:
            if action in seen:
                duplicates_by_subsystem[subsystem].append(action)
            seen.add(action)
            if action in doc_action_to_subsystem:
                duplicates_by_subsystem[subsystem].append(action)
            doc_action_to_subsystem[action] = subsystem

    return doc_action_to_subsystem, duplicates_by_subsystem


def parse_index_rows() -> list[dict[str, str]]:
    text = INDEX_PATH.read_text(encoding="utf-8")
    rows: list[dict[str, str]] = []
    for m in INDEX_ROW_RE.finditer(text):
        rows.append(
            {
                "action": m.group(1),
                "subsystem": m.group(2),
                "handler": m.group(3),
                "link_label": m.group(4),
                "link": m.group(5),
            }
        )
    return rows


def validate_links(index_rows: list[dict[str, str]], doc_actions: set[str]) -> list[str]:
    errors: list[str] = []

    file_to_anchors: dict[str, set[str]] = {}
    for _, path in ACTION_DOC_FILES.items():
        anchors = {f"action-{a}" for a in ANCHOR_RE.findall(path.read_text(encoding="utf-8"))}
        file_to_anchors[path.name] = anchors

    for row in index_rows:
        link = row["link"]
        if "#" not in link:
            errors.append(f"Index link missing anchor for action {row['action']!r}: {link}")
            continue
        filename, anchor = link.split("#", 1)
        file_path = ACTIONS_DOCS_DIR / filename
        if not file_path.exists():
            errors.append(f"Index link points to missing file for action {row['action']!r}: {filename}")
            continue
        if anchor not in file_to_anchors.get(file_path.name, set()):
            errors.append(f"Index link points to missing anchor for action {row['action']!r}: {link}")
        if row["link_label"] != row["action"]:
            errors.append(
                f"Index link label mismatch for action {row['action']!r}: label={row['link_label']!r}"
            )
        if row["action"] not in doc_actions:
            errors.append(f"Index includes undocumented action {row['action']!r}")

    return errors


def main() -> int:
    action_to_subsystem, action_to_handler = parse_registry_actions()
    registry_actions = set(action_to_subsystem.keys())

    doc_action_to_subsystem, duplicates_by_subsystem = parse_doc_actions()
    doc_actions = set(doc_action_to_subsystem.keys())

    index_rows = parse_index_rows()
    index_actions = [row["action"] for row in index_rows]
    index_action_set = set(index_actions)

    errors: list[str] = []

    for subsystem, duplicates in duplicates_by_subsystem.items():
        if duplicates:
            errors.append(f"Duplicate action anchors in {subsystem}: {sorted(set(duplicates))}")

    if len(index_actions) != len(index_action_set):
        dupes = sorted({a for a in index_actions if index_actions.count(a) > 1})
        errors.append(f"Duplicate actions in index: {dupes}")

    missing_in_docs = sorted(registry_actions - doc_actions)
    extra_in_docs = sorted(doc_actions - registry_actions)
    if missing_in_docs:
        errors.append(f"Missing documented actions: {missing_in_docs}")
    if extra_in_docs:
        errors.append(f"Extra actions in docs not in registry: {extra_in_docs}")

    missing_in_index = sorted(registry_actions - index_action_set)
    extra_in_index = sorted(index_action_set - registry_actions)
    if missing_in_index:
        errors.append(f"Missing index actions: {missing_in_index}")
    if extra_in_index:
        errors.append(f"Extra index actions not in registry: {extra_in_index}")

    errors.extend(validate_links(index_rows, doc_actions))

    for row in index_rows:
        action = row["action"]
        if action not in action_to_subsystem:
            continue
        if row["subsystem"] != action_to_subsystem[action]:
            errors.append(
                f"Index subsystem mismatch for {action!r}: expected {action_to_subsystem[action]!r}, got {row['subsystem']!r}"
            )
        if row["handler"] != action_to_handler[action]:
            errors.append(
                f"Index handler mismatch for {action!r}: expected {action_to_handler[action]!r}, got {row['handler']!r}"
            )

    print("ModularBot Docs Coverage Report")
    print("=" * 32)
    print(f"Registered actions: {len(registry_actions)}")
    print(f"Documented actions: {len(doc_actions)}")
    print(f"Indexed actions: {len(index_action_set)}")
    print("")

    for subsystem in ("movement", "interaction", "targeting", "party", "inventory"):
        reg = sorted(a for a, s in action_to_subsystem.items() if s == subsystem)
        doc = sorted(a for a, s in doc_action_to_subsystem.items() if s == subsystem)
        missing = sorted(set(reg) - set(doc))
        pct = (len(doc) / len(reg) * 100.0) if reg else 100.0
        print(f"- {subsystem}: {len(doc)}/{len(reg)} ({pct:.1f}%)")
        if missing:
            print(f"  missing: {missing}")

    if errors:
        print("\nValidation FAILED:")
        for err in errors:
            print(f"- {err}")
        return 1

    print("\nValidation PASSED: documented_actions == registered_actions, no duplicates, index links resolved.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
