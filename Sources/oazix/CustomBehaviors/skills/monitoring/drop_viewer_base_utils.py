import datetime
import os
import re
import sys
from typing import Any

from Sources.oazix.CustomBehaviors.PathLocator import PathLocator

EXPECTED_RUNTIME_ERRORS = (TypeError, ValueError, RuntimeError, AttributeError, IndexError, KeyError, OSError)


def _runtime_module(viewer):
    try:
        return sys.modules.get(viewer.__class__.__module__)
    except EXPECTED_RUNTIME_ERRORS:
        return None


def _runtime_attr(viewer, name: str, default=None):
    module = _runtime_module(viewer)
    if module is not None and hasattr(module, name):
        return getattr(module, name)
    return default


def safe_int(_viewer, value, default=0):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def ensure_text(_viewer, value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        try:
            return value.decode("utf-8", errors="ignore")
        except EXPECTED_RUNTIME_ERRORS:
            return ""
    return str(value)


def normalize_name_for_compare(viewer, value: Any) -> str:
    return " ".join(ensure_text(viewer, value).strip().lower().split())


def trace_auto_buy_kits(viewer, message: Any):
    ts = datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]
    text = ensure_text(viewer, message).strip()
    if not text:
        return
    line = f"{ts} {text}"
    trace = list(getattr(viewer, "auto_buy_kits_debug_trace", []) or [])
    trace.append(line)
    viewer.auto_buy_kits_debug_trace = trace[-120:]


def should_abort_auto_buy_kits(viewer) -> bool:
    return bool(getattr(viewer, "auto_buy_kits_abort_requested", False))


def is_auto_buy_kits_allowed_outpost(viewer) -> bool:
    map_api = _runtime_attr(viewer, "Map")
    try:
        if not bool(map_api.IsOutpost()):
            return False
        map_id = max(0, safe_int(viewer, map_api.GetMapID(), 0))
    except EXPECTED_RUNTIME_ERRORS:
        return False
    if map_id <= 0:
        return False
    hints = getattr(viewer, "auto_buy_kits_map_model_hints", None)
    if not isinstance(hints, dict):
        return False
    map_key = str(int(map_id))
    map_models = [safe_int(viewer, value, 0) for value in list(hints.get(map_key, []) or [])]
    return any(model_id > 0 for model_id in map_models)


def default_auto_buy_kits_map_model_hints(_viewer) -> dict[str, list[int]]:
    return {
        "55": [2043],
        "156": [2161],
    }


def sanitize_map_model_hints(viewer, value: Any) -> dict[str, list[int]]:
    result: dict[str, list[int]] = {}
    if not isinstance(value, dict):
        return result
    for raw_map_id, raw_models in value.items():
        map_key = ensure_text(viewer, raw_map_id).strip()
        if not map_key:
            continue
        models: list[int] = []
        if isinstance(raw_models, (list, tuple, set)):
            for raw_mid in raw_models:
                try:
                    mid = int(raw_mid)
                except EXPECTED_RUNTIME_ERRORS:
                    continue
                if mid > 0 and mid not in models:
                    models.append(mid)
        if models:
            result[map_key] = models[:16]
    return result


def get_known_merchant_model_ids(viewer) -> set[int]:
    if bool(getattr(viewer, "auto_buy_kits_merchant_model_ids_loaded", False)):
        return set(getattr(viewer, "auto_buy_kits_merchant_model_ids", set()) or set())

    model_data = _runtime_attr(viewer, "ModelData")
    tokens = ("merchant", "trader", "outfitter")
    model_ids: set[int] = set()

    try:
        if isinstance(model_data, dict):
            for raw_mid, row in model_data.items():
                try:
                    mid = int(raw_mid)
                except EXPECTED_RUNTIME_ERRORS:
                    continue
                if mid <= 0 or not isinstance(row, dict):
                    continue
                name_text = normalize_name_for_compare(viewer, row.get("name", ""))
                if any(tok in name_text for tok in tokens):
                    model_ids.add(mid)
    except EXPECTED_RUNTIME_ERRORS:
        pass

    try:
        converter_path = os.path.join(
            PathLocator.get_project_root_directory(),
            "Py4GWCoreLib",
            "model_id_converter.py",
        )
        if os.path.exists(converter_path):
            pat = re.compile(r'Ids\s*=\s*new\s*int\[\]\s*\{(?P<ids>[^}]*)\}.*?Name\s*=\s*"(?P<name>[^"]+)"')
            with open(converter_path, mode="r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    if "Ids" not in line or "Name" not in line:
                        continue
                    match = pat.search(line)
                    if not match:
                        continue
                    name_text = normalize_name_for_compare(viewer, match.group("name"))
                    if not any(tok in name_text for tok in tokens):
                        continue
                    for raw_num in re.findall(r"-?\d+", ensure_text(viewer, match.group("ids"))):
                        try:
                            mid = int(raw_num)
                        except EXPECTED_RUNTIME_ERRORS:
                            continue
                        if mid > 0:
                            model_ids.add(mid)
    except EXPECTED_RUNTIME_ERRORS:
        pass

    viewer.auto_buy_kits_merchant_model_ids = set(model_ids)
    viewer.auto_buy_kits_merchant_model_ids_loaded = True
    return set(model_ids)


def record_successful_kit_merchant_model(viewer, agent_id: int):
    agent_api = _runtime_attr(viewer, "Agent")
    map_api = _runtime_attr(viewer, "Map")
    aid = max(0, safe_int(viewer, agent_id, 0))
    if aid <= 0:
        return
    try:
        map_id = max(0, safe_int(viewer, map_api.GetMapID(), 0))
    except EXPECTED_RUNTIME_ERRORS:
        map_id = 0
    if map_id <= 0:
        return
    try:
        model_id = max(0, safe_int(viewer, agent_api.GetModelID(aid), 0))
    except EXPECTED_RUNTIME_ERRORS:
        model_id = 0
    if model_id <= 0:
        return
    map_key = str(int(map_id))
    hints = viewer.auto_buy_kits_map_model_hints if isinstance(getattr(viewer, "auto_buy_kits_map_model_hints", None), dict) else {}
    current = [int(v) for v in list(hints.get(map_key, []) or []) if safe_int(viewer, v, 0) > 0]
    if model_id in current:
        current = [model_id] + [v for v in current if v != model_id]
    else:
        current = [model_id] + current
    hints[map_key] = current[:16]
    viewer.auto_buy_kits_map_model_hints = hints
    viewer.runtime_config_dirty = True


def strip_tags(viewer, text: Any) -> str:
    return re.sub(r"<[^>]+>", "", ensure_text(viewer, text))


def clean_item_name(viewer, name: Any) -> str:
    cleaned = strip_tags(viewer, name).strip()
    cleaned = re.sub(r"^[\d,]+\s+", "", cleaned)
    if re.match(r"(?i)^item#\d+$", cleaned):
        return "Unknown Item"
    return cleaned


def display_player_name(viewer, player_name: Any, sender_email: Any = "") -> str:
    player_txt = ensure_text(viewer, player_name).strip()
    sender_key = ensure_text(viewer, sender_email).strip().lower()
    if sender_key:
        resolve_fn = getattr(viewer, "_resolve_sender_name_from_email", None)
        if callable(resolve_fn):
            try:
                resolved = ensure_text(viewer, resolve_fn(sender_key)).strip()
            except EXPECTED_RUNTIME_ERRORS:
                resolved = ""
            if resolved:
                return resolved
    if player_txt and player_txt.lower() not in {"follower", "unknown"}:
        return player_txt
    if sender_key:
        sender_label = sender_key.split("@", 1)[0].strip() or sender_key
        return f"{player_txt or 'Follower'} [{sender_label}]"
    return player_txt or "Unknown"


def is_unknown_item_label(viewer, name: Any) -> bool:
    txt = clean_item_name(viewer, name).strip()
    if not txt:
        return True
    txt_lc = txt.lower()
    if txt_lc in {"unknown", "unknown item"}:
        return True
    if re.match(r"(?i)^unknown item\s*\(model\s*\d+\)$", txt):
        return True
    return False


def remember_model_name(viewer, model_id: Any, item_name: Any):
    mid = max(0, safe_int(viewer, model_id, 0))
    if mid <= 0:
        return
    clean = clean_item_name(viewer, item_name).strip()
    if not clean or is_unknown_item_label(viewer, clean):
        return
    viewer.model_name_by_id[mid] = clean


def resolve_unknown_name_from_model(viewer, item_name: Any, model_id: Any) -> str:
    clean = clean_item_name(viewer, item_name).strip()
    if clean and (not is_unknown_item_label(viewer, clean)):
        return clean
    mid = max(0, safe_int(viewer, model_id, 0))
    if mid > 0:
        remembered = clean_item_name(viewer, viewer.model_name_by_id.get(mid, "")).strip()
        if remembered and (not is_unknown_item_label(viewer, remembered)):
            return remembered
        return f"Unknown Item (model {mid})"
    return "Unknown Item"
