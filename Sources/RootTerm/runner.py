"""Behavior-tree mission queue assembly."""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING

from Py4GWCoreLib.py4gwcorelib_src.BehaviorTree import BehaviorTree
from Sources.ApoSource.ApoBottingLib import wrappers as BT
from Sources.RootTerm.catalog import get_name
from Sources.RootTerm.config import get_config
from Sources.RootTerm.config import is_playable
from Sources.RootTerm.missions import DISPATCH
from Sources.RootTerm.options import OPTIONS

if TYPE_CHECKING:
    from Py4GWCoreLib.BottingTree import BottingTree

NamedStep = tuple[str, Callable[[], BehaviorTree]]


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
        children=[
            builder(cfg),
        ],
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
        steps.extend(
            [
                (
                    'No Missions Selected',
                    lambda: BT.LogMessage(
                        'Select at least one playable mission in the Missions tab.',
                        module_name='RMA',
                    ),
                ),
            ]
        )
        return steps

    for quest_id in selected:
        name = get_name(quest_id)
        steps.append((name, lambda quest_id=quest_id: _build_mission(quest_id)))
    return steps
