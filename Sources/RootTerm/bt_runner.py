"""Hot-reload-safe behavior-tree mission queue assembly."""

from __future__ import annotations

import importlib
from collections.abc import Callable
from typing import TYPE_CHECKING

from Py4GWCoreLib.py4gwcorelib_src.BehaviorTree import BehaviorTree
from Sources.ApoSource.ApoBottingLib import wrappers as BT
from Sources.RootTerm import bt_helpers
from Sources.RootTerm.catalog import get_name
from Sources.RootTerm.config import get_config
from Sources.RootTerm.config import is_playable
from Sources.RootTerm.missions.EOTN.CentralStorylines import against_the_charr
from Sources.RootTerm.missions.EOTN.CentralStorylines import curse_of_the_nornbear
from Sources.RootTerm.missions.EOTN.FinalEncounters import a_time_for_heroes
from Sources.RootTerm.missions.EOTN.TheShiverpeaks import a_gate_too_far
from Sources.RootTerm.missions.EOTN.TheShiverpeaks import blood_washes_blood
from Sources.RootTerm.missions.Factions.KainengCity import nahpui_quarter
from Sources.RootTerm.missions.Factions.KainengCity import sunjiang_district
from Sources.RootTerm.missions.Factions.KainengCity import tahnnakai_temple
from Sources.RootTerm.missions.Factions.KainengCity import vizunah_square
from Sources.RootTerm.missions.Factions.ShingJeaIsland import minister_chos_estate
from Sources.RootTerm.missions.Factions.ShingJeaIsland import zen_daijun
from Sources.RootTerm.missions.Nightfall.Istan import chahbek_village
from Sources.RootTerm.missions.Prophecies.Ascalon import fort_ranik
from Sources.RootTerm.missions.Prophecies.Ascalon import great_northern_wall
from Sources.RootTerm.missions.Prophecies.Ascalon import nolani_academy
from Sources.RootTerm.missions.Prophecies.Ascalon import ruins_of_surmia
from Sources.RootTerm.missions.Prophecies.NorthernShiverpeaks import borlis_pass
from Sources.RootTerm.missions.Prophecies.NorthernShiverpeaks import the_frost_gate
from Sources.RootTerm.options import OPTIONS

if TYPE_CHECKING:
    from Py4GWCoreLib.BottingTree import BottingTree

# Py4GW keeps imported package modules alive when the selected script reloads.
# Refresh mission implementations so iterative edits are reflected in-client.
importlib.reload(bt_helpers)
importlib.reload(against_the_charr)
importlib.reload(curse_of_the_nornbear)
importlib.reload(blood_washes_blood)
importlib.reload(a_gate_too_far)
importlib.reload(a_time_for_heroes)
importlib.reload(vizunah_square)
importlib.reload(nahpui_quarter)
importlib.reload(sunjiang_district)
importlib.reload(tahnnakai_temple)
importlib.reload(minister_chos_estate)
importlib.reload(zen_daijun)
importlib.reload(chahbek_village)
importlib.reload(fort_ranik)
importlib.reload(great_northern_wall)
importlib.reload(nolani_academy)
importlib.reload(ruins_of_surmia)
importlib.reload(borlis_pass)
importlib.reload(the_frost_gate)

MissionBuilder = Callable[[object], BehaviorTree]
NamedStep = tuple[str, Callable[[], BehaviorTree]]

DISPATCH: dict[int, MissionBuilder] = {
    936: great_northern_wall.build,
    937: fort_ranik.build,
    938: ruins_of_surmia.build,
    939: nolani_academy.build,
    940: borlis_pass.build,
    941: the_frost_gate.build,
    961: zen_daijun.build,
    962: vizunah_square.build,
    963: nahpui_quarter.build,
    964: tahnnakai_temple.build,
    967: sunjiang_district.build,
    978: chahbek_village.build,
    1003: against_the_charr.build,
    1006: curse_of_the_nornbear.build,
    1007: blood_washes_blood.build,
    1008: a_gate_too_far.build,
    1010: a_time_for_heroes.build,
    1119: minister_chos_estate.build,
}


def _build_mission(quest_id: int) -> BehaviorTree:
    cfg = get_config(quest_id)
    builder = DISPATCH.get(quest_id)
    if cfg is None or builder is None:
        return BT.LogMessage(f'Unsupported mission {quest_id}.', module_name='RMA')

    name = get_name(quest_id)
    OPTIONS.status_message = f'Running {name}'
    return BT.Sequence(
        name=f'Run {name}',
        map_id_or_name=cfg.town_map,
        random_travel=False,
        hard_mode=OPTIONS.hard_mode,
        children=[builder(cfg)],
    )


def build_execution_steps(tree: BottingTree) -> list[NamedStep]:
    steps: list[NamedStep] = [
        (
            'Initialize',
            lambda: tree.Config.Aggressive(
                multi_account=False,
                auto_loot=True,
                resurrection_scroll=False,
            ),
        ),
    ]

    selected = [qid for qid in OPTIONS.get_selected_quest_ids() if is_playable(qid)]
    if not selected:
        steps.append(
            (
                'No Missions Selected',
                lambda: BT.LogMessage(
                    'Select at least one playable mission in the Missions tab.',
                    module_name='RMA',
                ),
            )
        )
        return steps

    for quest_id in selected:
        name = get_name(quest_id)
        steps.append((name, lambda quest_id=quest_id: _build_mission(quest_id)))
    return steps
