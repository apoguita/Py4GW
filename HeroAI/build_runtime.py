from __future__ import annotations

import importlib
from typing import TYPE_CHECKING, cast

from Py4GWCoreLib.Map import Map

from .cache_data import CacheData

if TYPE_CHECKING:
    from Py4GWCoreLib.BuildMgr import BuildRegistry
    from Py4GWCoreLib.Builds.Any.HeroAI import HeroAI_Build


_cached_data: CacheData = CacheData()
_heroai_build: "HeroAI_Build | None" = None
_build_contract_map_signature: tuple[int, int, int, int] | None = None


def _load_heroai_build_class() -> type["HeroAI_Build"]:
    module = importlib.import_module("Py4GWCoreLib.Builds.Any.HeroAI")
    return cast(type["HeroAI_Build"], getattr(module, "HeroAI_Build"))


def get_runtime_build(cached_data: CacheData | None = None) -> "HeroAI_Build":
    global _cached_data, _heroai_build

    if cached_data is not None:
        _cached_data = cached_data

    if _heroai_build is None:
        _heroai_build = _load_heroai_build_class()(_cached_data)
    else:
        _heroai_build.set_cached_data(_cached_data)

    return _heroai_build


def get_registry(cached_data: CacheData | None = None) -> "BuildRegistry":
    registry = get_runtime_build(cached_data).GetBuildRegistry()
    if registry is None:
        raise RuntimeError("HeroAI runtime build registry is not available.")
    return registry


def clear_build_contract(cached_data: CacheData | None = None) -> None:
    global _build_contract_map_signature

    get_runtime_build(cached_data).ClearBuildContract()
    _build_contract_map_signature = None


def sync_build_contract(cached_data: CacheData | None = None) -> None:
    global _build_contract_map_signature

    build = get_runtime_build(cached_data)
    map_signature = (
        int(Map.GetMapID()),
        int(Map.GetRegion()[0]),
        int(Map.GetDistrict()),
        int(Map.GetLanguage()[0]),
    )
    if _build_contract_map_signature != map_signature:
        build.EnsureBuildContract(_cached_data)
        _build_contract_map_signature = map_signature


def refresh_builds(cached_data: CacheData | None = None) -> "HeroAI_Build":
    global _cached_data, _heroai_build, _build_contract_map_signature

    if cached_data is not None:
        _cached_data = cached_data

    registry = get_registry(_cached_data)
    registry.RefreshBuilds()

    _heroai_build = _load_heroai_build_class()(_cached_data)
    _build_contract_map_signature = None
    return _heroai_build
