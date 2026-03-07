"""
Route recipe - run outpost-to-outpost/transit routes from structured JSON files.

Route files:
    Sources/modular_bot/routes/<route_name>.json
"""

from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from Py4GWCoreLib import Botting

from ..phase import Phase
from ..hero_setup import get_team_for_size
from .modular_actions import register_step as _register_shared_step
from .runner_common import count_expanded_steps, register_recipe_context, register_repeated_steps


def _get_routes_dir() -> str:
    return os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "routes"))


def _load_route_data(route_name: str) -> Dict[str, Any]:
    routes_dir = _get_routes_dir()
    filepath = os.path.join(routes_dir, f"{route_name}.json")
    if not os.path.isfile(filepath):
        available = []
        if os.path.isdir(routes_dir):
            available = [f[:-5] for f in os.listdir(routes_dir) if f.endswith(".json")]
        raise FileNotFoundError(
            f"Route data not found: {filepath}\n"
            f"Available routes: {available}"
        )
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def list_available_routes() -> List[str]:
    routes_dir = _get_routes_dir()
    if not os.path.isdir(routes_dir):
        return []
    names: List[str] = []
    for filename in os.listdir(routes_dir):
        if filename.endswith(".json"):
            names.append(filename[:-5])
    return sorted(names)


def _register_step(bot: "Botting", step: Dict[str, Any], step_idx: int) -> None:
    _register_shared_step(bot, step, step_idx, recipe_name="Route")


def route_run(bot: "Botting", route_name: str) -> None:
    from Py4GWCoreLib import ConsoleLog, Party

    data = _load_route_data(route_name)
    display_name = data.get("name", route_name)
    outpost_id = data.get("outpost_id")
    max_heroes = data.get("max_heroes", 0)
    hero_team = str(data.get("hero_team", "") or "")
    steps = data.get("steps", [])
    register_recipe_context(bot, str(display_name), total_steps=count_expanded_steps(steps))

    if outpost_id:
        bot.Party.LeaveParty()
        bot.Map.Travel(target_map_id=outpost_id)

    if max_heroes > 0:
        hero_ids = get_team_for_size(max_heroes, hero_team)
        if hero_ids:
            bot.Party.AddHeroList(hero_ids)
            bot.Wait.UntilCondition(
                lambda _expected=len(hero_ids): Party.IsPartyLoaded() and Party.GetHeroCount() >= _expected,
                duration=250,
            )
            bot.Wait.ForTime(500)

    total_registered_steps = register_repeated_steps(
        bot,
        recipe_name="Route",
        steps=steps,
        register_step=_register_step,
    )

    ConsoleLog(
        "Recipe:Route",
        f"Registered route: {display_name} ({total_registered_steps} expanded steps from {len(steps)} source steps, outpost {outpost_id})",
    )


def Route(
    route_name: str,
    name: Optional[str] = None,
    anchor: bool = False,
) -> Phase:
    if name is None:
        try:
            data = _load_route_data(route_name)
            name = str(data.get("name", route_name))
        except FileNotFoundError:
            name = f"Route: {route_name}"

    return Phase(name, lambda bot: route_run(bot, route_name), anchor=anchor)
