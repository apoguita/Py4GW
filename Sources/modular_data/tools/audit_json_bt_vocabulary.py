"""Audit modular JSON recipes against the BT-native smart node vocabulary."""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path


CANONICAL_STEP_TYPES: frozenset[str] = frozenset(
    {
        "behavior",
        "interact",
        "inventory",
        "map",
        "party",
        "route",
        "wait",
    }
)

LEGACY_STEP_TYPES: frozenset[str] = frozenset(
    {
        "abandon_quest",
        "add_enemy_blacklist",
        "automatic_dialog",
        "auto_path",
        "auto_path_delayed",
        "auto_path_till_timeout",
        "broadcast_summoning_stone",
        "dialog",
        "dialog_multibox",
        "dialog_with_model",
        "dialogs",
        "disable_party_member_hooks",
        "drop_bundle",
        "emote",
        "enable_party_member_hooks",
        "enemy_blacklist",
        "enter_challenge",
        "exit_map",
        "flag_all_accounts",
        "flag_heroes",
        "follow_model",
        "force_hero_state",
        "interact_gadget",
        "interact_gadget_at_xy",
        "interact_item",
        "interact_nearest_npc",
        "interact_npc",
        "interact_quest_npc",
        "inventory_cleanup",
        "key_press",
        "load_party",
        "loot_chest",
        "move",
        "nudge_move",
        "party_member_hooks",
        "path",
        "path_to_target",
        "quest",
        "remove_enemy_blacklist",
        "resign",
        "set_anchor",
        "set_auto_behavior",
        "set_auto_combat",
        "set_auto_following",
        "set_auto_looting",
        "set_combat_engine",
        "skip_cutscene",
        "suppress_recovery",
        "travel",
        "unflag_all_accounts",
        "unflag_heroes",
        "use_all_consumables",
        "use_consumables",
        "wait_for_map_load",
        "wait_map_change",
        "wait_map_load",
        "wait_model_has_quest",
    }
)

COMMON_FIELDS: frozenset[str] = frozenset({"type", "name", "anchor", "repeat", "ms", "log", "debug"})

ALLOWED_FIELDS: dict[str, frozenset[str]] = {
    "behavior": COMMON_FIELDS | frozenset({"action", "mode", "enemy"}),
    "interact": COMMON_FIELDS
    | frozenset(
        {
            "action",
            "target",
            "kind",
            "point",
            "x",
            "y",
            "model_id",
            "id",
            "ids",
            "dialog_id",
            "interval_ms",
            "interact_delay_ms",
            "settle_ms",
            "dialog_delay_ms",
            "button",
            "button_number",
            "max_dist",
            "npc",
            "gadget",
            "selector",
            "nearest",
            "tolerance",
            "move_tolerance",
            "pause_on_combat",
        }
    ),
    "inventory": COMMON_FIELDS | frozenset({"action", "mode", "multibox", "leader_only", "timeout_ms"}),
    "map": COMMON_FIELDS
    | frozenset({"action", "target_map_id", "map_id", "target_map_name", "delay_ms", "timeout_ms", "timeout"}),
    "party": COMMON_FIELDS
    | frozenset(
        {
            "action",
            "required_hero",
            "max_heroes",
            "hero_ids",
            "heroes",
            "henchman_ids",
            "henchmen",
            "clear_existing",
            "point",
            "x",
            "y",
            "state",
            "behavior",
            "quest_id",
            "id",
        }
    ),
    "route": COMMON_FIELDS
    | frozenset(
        {
            "mode",
            "point",
            "points",
            "x",
            "y",
            "target_map_id",
            "map_id",
            "target_map_name",
            "tolerance",
            "move_tolerance",
            "pause_on_combat",
            "clear_area_radius",
            "range",
            "pulses",
            "pulse_ms",
            "target",
            "kind",
            "enemy",
            "model_id",
            "selector",
            "nearest",
            "max_dist",
        }
    ),
    "wait": COMMON_FIELDS | frozenset({"action", "duration_ms", "command"}),
}

ALLOWED_VALUES: dict[tuple[str, str], frozenset[str]] = {
    ("behavior", "action"): frozenset({"enemy_blacklist"}),
    ("behavior", "mode"): frozenset({"add", "remove"}),
    ("interact", "action"): frozenset({"target", "dialog", "auto_dialog", "drop_bundle"}),
    ("interact", "target"): frozenset({"npc", "gadget", "item"}),
    ("interact", "kind"): frozenset({"npc", "gadget", "item"}),
    ("inventory", "action"): frozenset({"use_consumables", "broadcast_summoning_stone"}),
    ("map", "action"): frozenset({"travel", "enter_challenge", "wait_for_map_load"}),
    ("party", "action"): frozenset({"load", "flag_heroes", "unflag_heroes", "force_hero_state", "resign", "abandon_quest"}),
    ("route", "mode"): frozenset({"move", "exit", "nudge", "kill", "target"}),
    ("wait", "action"): frozenset({"wait", "emote"}),
}


@dataclass
class AuditResult:
    files: int
    steps: int
    canonical_counts: Counter[str]
    legacy_counts: Counter[str]
    unknown_counts: Counter[str]
    semantic_counts: Counter[str]

    @property
    def has_issues(self) -> bool:
        return bool(self.legacy_counts or self.unknown_counts or self.semantic_counts)


def audit_root(root: Path) -> AuditResult:
    canonical_counts: Counter[str] = Counter()
    legacy_counts: Counter[str] = Counter()
    unknown_counts: Counter[str] = Counter()
    semantic_counts: Counter[str] = Counter()
    file_count = 0
    step_count = 0
    target_registry = _load_target_registry(root)

    for path in sorted(root.rglob("*.json")):
        file_count += 1
        recipe = json.loads(path.read_text(encoding="utf-8-sig"))
        if not isinstance(recipe, dict):
            unknown_counts["<non-object-recipe>"] += 1
            continue
        steps = recipe.get("steps", [])
        if not isinstance(steps, list):
            unknown_counts["<non-list-steps>"] += 1
            continue
        for step in steps:
            if not isinstance(step, dict):
                unknown_counts["<non-object-step>"] += 1
                continue
            step_count += 1
            step_type = str(step.get("type", "") or "").strip().lower()
            if step_type in CANONICAL_STEP_TYPES:
                canonical_counts[step_type] += 1
                _audit_step_semantics(step, step_type, semantic_counts, target_registry)
            elif step_type in LEGACY_STEP_TYPES:
                legacy_counts[step_type] += 1
            else:
                unknown_counts[step_type or "<missing>"] += 1

    return AuditResult(
        files=file_count,
        steps=step_count,
        canonical_counts=canonical_counts,
        legacy_counts=legacy_counts,
        unknown_counts=unknown_counts,
        semantic_counts=semantic_counts,
    )


def format_result(result: AuditResult) -> str:
    lines = [
        f"Files: {result.files}",
        f"Steps: {result.steps}",
        f"Canonical steps: {sum(result.canonical_counts.values())}",
        f"Legacy migration steps: {sum(result.legacy_counts.values())}",
        f"Unknown steps: {sum(result.unknown_counts.values())}",
        f"Semantic issues: {sum(result.semantic_counts.values())}",
    ]
    if result.canonical_counts:
        lines.append("")
        lines.append("Canonical types:")
        for step_type, count in result.canonical_counts.most_common():
            lines.append(f"  {step_type}: {count}")
    if result.legacy_counts:
        lines.append("")
        lines.append("Legacy types:")
        for step_type, count in result.legacy_counts.most_common():
            lines.append(f"  {step_type}: {count}")
    if result.unknown_counts:
        lines.append("")
        lines.append("Unknown types:")
        for step_type, count in result.unknown_counts.most_common():
            lines.append(f"  {step_type}: {count}")
    if result.semantic_counts:
        lines.append("")
        lines.append("Semantic issues:")
        for issue, count in result.semantic_counts.most_common():
            lines.append(f"  {issue}: {count}")
    return "\n".join(lines)


def _audit_step_semantics(
    step: dict[str, object],
    step_type: str,
    semantic_counts: Counter[str],
    target_registry: object | None,
) -> None:
    allowed_fields = ALLOWED_FIELDS[step_type]
    for key in step:
        if key not in allowed_fields:
            semantic_counts[f"{step_type}.unsupported_field.{key}"] += 1

    for key in ("action", "mode", "target", "kind"):
        allowed_values = ALLOWED_VALUES.get((step_type, key))
        if allowed_values is None or key not in step:
            continue
        value = str(step.get(key) or "").strip().lower()
        if value and value not in allowed_values:
            semantic_counts[f"{step_type}.unsupported_{key}.{value}"] += 1

    if step_type == "party" and str(step.get("action") or "").strip().lower() == "load":
        for removed_key in ("team", "team_mode", "use_priority", "minionless"):
            if removed_key in step:
                semantic_counts[f"party.load.removed_field.{removed_key}"] += 1

    if step_type == "interact":
        _audit_selector(step, step_type, semantic_counts, target_registry)
    if step_type == "route" and str(step.get("mode") or "").strip().lower() == "target":
        _audit_selector(step, step_type, semantic_counts, target_registry)


def _audit_selector(
    step: dict[str, object],
    step_type: str,
    semantic_counts: Counter[str],
    target_registry: object | None,
) -> None:
    target = str(step.get("target") or step.get("kind") or ("gadget" if "gadget" in step else "npc")).strip().lower()
    has_point = "point" in step or ("x" in step and "y" in step)
    has_model = _int(step.get("model_id"), 0) > 0
    has_nearest = _bool(step.get("nearest"), False)
    selector_pairs: list[tuple[str, str]] = []

    for kind in ("npc", "gadget", "enemy"):
        value = step.get(kind)
        if isinstance(value, str) and value.strip():
            selector_pairs.append((kind, value.strip()))

    generic = step.get("selector")
    if isinstance(generic, str) and generic.strip() and target in {"npc", "gadget", "enemy"}:
        selector_pairs.append((target, generic.strip()))
        specific = step.get(target)
        if isinstance(specific, str) and specific.strip():
            if specific.strip() == generic.strip():
                semantic_counts[f"{target}.duplicate_selector"] += 1
            else:
                semantic_counts[f"{target}.conflicting_selector"] += 1

    action = str(step.get("action") or "target").strip().lower()
    should_target_agent = (
        step_type == "interact" and action == "target"
    ) or any(key in step for key in ("npc", "gadget", "selector", "nearest"))
    if should_target_agent and target in {"npc", "gadget"} and not (has_point or has_model or has_nearest or selector_pairs):
        semantic_counts[f"{target}.missing_selector"] += 1

    if target_registry is None:
        return
    for kind, key in selector_pairs:
        if not target_registry.has_named_agent_target(kind, key):
            semantic_counts[f"{kind}.unknown_selector.{key}"] += 1


def _load_target_registry(root: Path) -> object | None:
    registry_path = root.resolve().parents[1] / "Py4GWCoreLib" / "modular" / "domain" / "target_registry.py"
    if not registry_path.exists():
        registry_path = Path(__file__).resolve().parents[3] / "Py4GWCoreLib" / "modular" / "domain" / "target_registry.py"
    if not registry_path.exists():
        return None
    spec = importlib.util.spec_from_file_location("_modular_target_registry", registry_path)
    if spec is None or spec.loader is None:
        return None
    module = importlib.util.module_from_spec(spec)
    sys.modules[str(spec.name)] = module
    spec.loader.exec_module(module)
    return module


def _int(value: object, default: int) -> int:
    try:
        if isinstance(value, str):
            return int(value, 0)
        return int(value)
    except (TypeError, ValueError):
        return default


def _bool(value: object, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"1", "true", "yes", "on"}:
            return True
        if normalized in {"0", "false", "no", "off"}:
            return False
    return default


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="Root folder containing modular JSON recipes.",
    )
    parser.add_argument(
        "--fail-on-issues",
        action="store_true",
        help="Return a non-zero exit code for legacy or unknown vocabulary.",
    )
    args = parser.parse_args(argv)

    result = audit_root(args.root)
    print(format_result(result))
    return 1 if args.fail_on_issues and result.has_issues else 0


if __name__ == "__main__":
    raise SystemExit(main())
