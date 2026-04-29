"""
source_loader module

This module is part of the modular runtime surface.
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any

from ..paths import modular_data_root


_BLOCK_DIRS: dict[str, str] = {
    "missions": "missions",
    "quests": "quests",
    "routes": "routes",
    "farms": "farms",
    "dungeons": "dungeons",
    "vanquishes": "vanquishes",
    "bounties": "bounties",
}


def _modular_root_dir() -> str:
    return os.path.abspath(os.path.normpath(modular_data_root()))


def _normalize_block_name(block_name: str) -> str:
    name = str(block_name or "").strip().replace("\\", "/")
    if name.endswith(".json"):
        name = name[:-5]
    return name.strip("/")


def _validate_block_name(block_name: str) -> str:
    normalized = _normalize_block_name(block_name)
    if not normalized:
        raise FileNotFoundError("Empty modular block name.")
    if os.path.isabs(normalized):
        raise FileNotFoundError("Modular block paths must be relative to Sources/modular_data.")
    parts = [part for part in normalized.split("/") if part]
    if any(part == ".." for part in parts):
        raise FileNotFoundError("Modular block paths cannot escape Sources/modular_data.")
    return normalized


def _path_inside_root(path: str, root: str) -> bool:
    try:
        return os.path.commonpath([root, os.path.abspath(os.path.normpath(path))]) == root
    except ValueError:
        return False


def _list_json_files(base_dir: str) -> list[str]:
    if not os.path.isdir(base_dir):
        return []
    names: list[str] = []
    for root, _, files in os.walk(base_dir):
        for filename in files:
            if not filename.endswith(".json"):
                continue
            rel = os.path.relpath(os.path.join(root, filename), base_dir).replace("\\", "/")
            names.append(rel[:-5])
    return sorted(names)


@dataclass(frozen=True)
class BlockSource:
    """
    B lo ck So ur ce class.
    
    Meta:
      Expose: true
      Audience: advanced
      Display: Block Source
      Purpose: Provide explicit modular runtime behavior and metadata.
      UserDescription: Internal class used by modular orchestration and step execution.
      Notes: Keep behavior explicit and side effects contained.
    """
    kind: str
    key: str
    path: str
    data: dict[str, Any]


class BlockSourceLoader:
    """
    B lo ck So ur ce Lo ad er class.
    
    Meta:
      Expose: true
      Audience: advanced
      Display: Block Source Loader
      Purpose: Provide explicit modular runtime behavior and metadata.
      UserDescription: Internal class used by modular orchestration and step execution.
      Notes: Keep behavior explicit and side effects contained.
    """
    @staticmethod
    def resolve_path(block_name: str, *, kind: str | None = None) -> str:
        normalized = _validate_block_name(block_name)
        root = _modular_root_dir()
        candidates: list[str] = []
        candidates.append(os.path.join(root, f"{normalized}.json"))

        search_kinds: list[str]
        if kind is None:
            search_kinds = list(_BLOCK_DIRS.keys())
        else:
            kind_norm = str(kind).strip().lower()
            if kind_norm not in _BLOCK_DIRS:
                raise FileNotFoundError(f"Unknown block kind: {kind!r}")
            search_kinds = [kind_norm]

        for kind_name in search_kinds:
            base_dir = os.path.join(root, _BLOCK_DIRS[kind_name])
            rel_name = (
                normalized[len(_BLOCK_DIRS[kind_name]) + 1 :]
                if normalized.startswith(f"{_BLOCK_DIRS[kind_name]}/")
                else normalized
            )
            candidates.append(os.path.join(base_dir, f"{rel_name}.json"))

        for candidate in candidates:
            candidate_norm = os.path.abspath(os.path.normpath(candidate))
            if not _path_inside_root(candidate_norm, root):
                continue
            if os.path.isfile(candidate_norm):
                return candidate_norm

        raise FileNotFoundError(
            f"Modular block not found: {block_name!r}\nChecked: {candidates}"
        )

    @staticmethod
    def load(block_name: str, *, kind: str | None = None) -> BlockSource:
        path = BlockSourceLoader.resolve_path(block_name, kind=kind)
        with open(path, "r", encoding="utf-8-sig") as handle:
            data = json.load(handle)

        key = _normalize_block_name(block_name)
        if kind:
            key = key[len(str(kind).strip().lower()) + 1 :] if key.startswith(f"{str(kind).strip().lower()}/") else key
        resolved_kind = str(kind or "").strip().lower()
        if not resolved_kind:
            relative = os.path.relpath(path, _modular_root_dir()).replace("\\", "/")
            for kind_name in _BLOCK_DIRS:
                prefix = f"{kind_name}/"
                if relative.startswith(prefix):
                    resolved_kind = kind_name
                    break

        return BlockSource(
            kind=resolved_kind,
            key=key,
            path=path,
            data=dict(data) if isinstance(data, dict) else {},
        )

    @staticmethod
    def list_available(*, kind: str | None = None) -> list[str]:
        root = _modular_root_dir()
        if kind:
            kind_norm = str(kind).strip().lower()
            if kind_norm not in _BLOCK_DIRS:
                return []
            return _list_json_files(os.path.join(root, _BLOCK_DIRS[kind_norm]))

        merged: list[str] = []
        for kind_name, dirname in _BLOCK_DIRS.items():
            for rel in _list_json_files(os.path.join(root, dirname)):
                merged.append(f"{kind_name}/{rel}")
        return sorted(merged)
