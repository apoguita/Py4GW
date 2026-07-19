"""Curse of the Nornbear behavior tree."""

from Py4GWCoreLib import TitleID
from Py4GWCoreLib.py4gwcorelib_src.BehaviorTree import BehaviorTree
from Sources.ApoSource.ApoBottingLib import wrappers as BT
from Sources.RootTerm import bt_helpers as H
from Sources.RootTerm.config import MissionConfig


def build(cfg: MissionConfig) -> BehaviorTree:
    return BT.Sequence(
        name='Curse of the Nornbear',
        children=[
            H.mission_consumables(),
            H.set_title(int(TitleID.Norn)),
            BT.MoveAndDialog((14317.10, 23935.31), 0x81, pause_on_combat=False),
            BT.SendDialog(0x86),
            BT.WaitForMapLoad(map_id=cfg.mission_map, timeout_ms=120000),
            H.skip_cinematic('Nornbear Intro'),
            BT.VanquishNode(
                name='Track the Nornbear',
                steps=[
                    (7007.33, 23572.58), (5631.19, 23079.56), (3347.98, 22400.52),
                    (2373.94, 22399.62), (2649.74, 19133.76), (2482.09, 18261.76),
                    (2780.76, 16096.74), (856.75, 15720.97), (-2457.16, 15856.53),
                    (-6127.03, 16051.32), (-3499.28, 15930.70), (418.25, 15692.95),
                    (3313.89, 16087.55), (6072.77, 15384.90), (8085.13, 14053.51),
                    (5138.29, 15600.64), (4740.89, 14637.12), (5707.74, 13561.38),
                    (4800.86, 11590.40), (2716.40, 11708.33), (32.45, 10625.76),
                    (843.83, 9463.73), (2196, 8220.27), (2384.14, 6401.20),
                    (3950.96, 5561.40), (4857.82, 6909.11),
                ],
                pause_on_combat=True,
                timeout_ms=90000,
            ),
            BT.LootItems(distance=1500, timeout_ms=30000),
            H.skip_cinematic('Nornbear End'),
            BT.WaitForMapLoad(map_id=cfg.completion_map, timeout_ms=120000),
        ],
    )
