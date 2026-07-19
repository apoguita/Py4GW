"""A Time for Heroes behavior tree."""

from Py4GWCoreLib import TitleID
from Py4GWCoreLib.py4gwcorelib_src.BehaviorTree import BehaviorTree
from Sources.ApoSource.ApoBottingLib import wrappers as BT
from Sources.RootTerm import bt_helpers as H
from Sources.RootTerm.config import MissionConfig


def build(cfg: MissionConfig) -> BehaviorTree:
    return BT.Sequence(
        name='A Time for Heroes',
        children=[
            H.mission_consumables(),
            H.set_title(int(TitleID.Deldrimor)),
            BT.MoveAndDialog((13.67, -829.73), 0x86, pause_on_combat=False),
            BT.SendDialog(0x84),
            BT.WaitForMapLoad(map_id=cfg.mission_map, timeout_ms=120000),
            BT.VanquishNode(
                name='Defeat the Great Destroyer',
                steps=[
                    (-16167.68, 19751.79),
                    (-14846.22, 17417.58),
                    (-14289.67, 16481.70),
                    (-14625.87, 14777.79),
                ],
                pause_on_combat=True,
                timeout_ms=90000,
            ),
            H.skip_cinematic('A Time for Heroes End'),
            BT.WaitForMapLoad(map_id=cfg.completion_map, timeout_ms=120000),
        ],
    )
