"""Tahnnakai Temple behavior tree."""

from Py4GWCoreLib.py4gwcorelib_src.BehaviorTree import BehaviorTree
from Sources.ApoSource.ApoBottingLib import wrappers as BT
from Sources.RootTerm import bt_helpers as H
from Sources.RootTerm.config import MissionConfig


def _route(name: str, steps: list[tuple[float, float]]) -> BehaviorTree:
    return BT.VanquishNode(
        name=name, steps=steps, clear_area_radius=1100.0, pause_on_combat=True, timeout_ms=90000
    )


def build(cfg: MissionConfig) -> BehaviorTree:
    return BT.Sequence(
        name='Tahnnakai Temple',
        children=[
            BT.SetHardMode(False),
            H.enter_mission('Tahnnakai'),
            H.mission_consumables(),
            _route(
                'Tahnnakai Meet Togo and Mhenlo',
                [(-7552.74, -3802.72), (-7257.90, -3179.21)],
            ),
            BT.Wait(3000),
            _route(
                'Tahnnakai Mesmer Boss',
                [
                    (-6582.40, -2309.14), (-5473.43, -2324.90), (-4737.73, -2317.84),
                    (-3692.54, -3428.76), (-2993.74, -4111.87),
                ],
            ),
            _route(
                'Tahnnakai Necromancer Boss',
                [
                    (-2514.95, -4344.53), (-1452.02, -5229.99), (-2040.47, -4385.58),
                    (-836.13, -4222.35), (448.65, -5348.65), (1272.83, -4604.76),
                ],
            ),
            _route(
                'Tahnnakai Elementalist Boss',
                [
                    (1754.84, -4021.96), (1588.61, -2322.38), (2257.54, -1591.97),
                    (3755.85, -2009.67), (4641.73, -2008.39),
                ],
            ),
            _route(
                'Tahnnakai Monk Boss',
                [
                    (5500.98, -1915.93), (6707.37, -1757.58), (7470.89, -860.25),
                    (7650.52, -2060.67), (6514.40, -3457.31), (6108.34, -4310.78),
                ],
            ),
            _route(
                'Tahnnakai Warrior Boss',
                [
                    (5355.68, -5492.60), (6438.47, -6679.26), (8689.74, -5023),
                    (10220.34, -4706.25), (11586.02, -4350.35), (11386.02, -4550.35),
                    (9921.30, -6293.08), (9873.84, -7403.92),
                ],
            ),
            _route(
                'Tahnnakai Ranger Boss',
                [
                    (9895.44, -7795.68), (9963.68, -8751.26), (10486.18, -9924.60),
                    (10586.18, -10024.60), (10696, -11376.88), (10517.38, -12108.80),
                ],
            ),
            _route(
                'Tahnnakai Ritualist Boss',
                [
                    (9731.49, -13309.13), (9495.46, -13729.53), (8970.58, -14508.96),
                    (8212.85, -15578.94), (7700.28, -14623.17), (7097.23, -13788.63),
                ],
            ),
            _route(
                'Tahnnakai Assassin Boss',
                [
                    (6180.67, -12973.51), (4432.93, -12125.86), (3177.59, -12160.53),
                    (2072.65, -12146.22), (2630.82, -11934.08), (2926.35, -10897.88),
                    (2965.44, -9770.59),
                ],
            ),
            H.skip_cinematic('Tahnnakai End Cinematic', wait_ms=3000),
            BT.WaitForMapLoad(map_id=cfg.completion_map, timeout_ms=120000),
        ],
    )
