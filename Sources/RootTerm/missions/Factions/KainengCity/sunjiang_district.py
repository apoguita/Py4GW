"""Sunjiang District behavior tree."""

from Py4GWCoreLib.py4gwcorelib_src.BehaviorTree import BehaviorTree
from Sources.ApoSource.ApoBottingLib import wrappers as BT
from Sources.RootTerm import bt_helpers as H
from Sources.RootTerm.config import MissionConfig

TOGO = 3171
MHENLO = 3172


def _route(name: str, steps: list[tuple[float, float]]) -> BehaviorTree:
    return BT.VanquishNode(
        name=name, steps=steps, clear_area_radius=1100.0, pause_on_combat=True, timeout_ms=90000
    )


def build(cfg: MissionConfig) -> BehaviorTree:
    return BT.Sequence(
        name='Sunjiang District',
        children=[
            H.enter_mission('Sunjiang'),
            H.mission_consumables(),
            _route('Sunjiang Meet Togo Mhenlo', [(-7186.22, -7033.49)]),
            H.wait_for_player_number(TOGO, 'Sunjiang Wait for Togo', max_range=2500.0, timeout_ms=60000),
            H.wait_for_player_number(MHENLO, 'Sunjiang Wait for Mhenlo', max_range=2500.0, timeout_ms=60000),
            BT.Wait(10000),
            BT.Move((-5872.91, -6989.90), pause_on_combat=False, tolerance=300.0),
            _route('Sunjiang Approach First Spirit', [(-4765.80, -6891.40)]),
            BT.Wait(2000),
            _route(
                'Sunjiang First Spirit of Portals',
                [
                    (-2807.16, -6967.21),
                    (-1759.96, -6548.59),
                    (-1824.09, -7697.15),
                    (-1257.90, -7644.81),
                    (-359.56, -7461.32),
                    (4.83, -6224.40),
                    (-47.17, -3500.56),
                ],
            ),
            _route(
                'Sunjiang Second Spirit Approach',
                [
                    (2291.94, -2511.57),
                    (2370.99, -982.48),
                    (2628.47, 42.12),
                    (2693.91, 2356.34),
                    (4482.88, 2316.88),
                ],
            ),
            BT.Wait(2000),
            _route(
                'Sunjiang Second Spirit of Portals',
                [
                    (5017.88, 45.15),
                    (6032.45, 66.60),
                    (6415.38, -304.91),
                ],
            ),
            _route(
                'Sunjiang Third Spirit Approach',
                [
                    (4948.20, 400.04),
                    (4468.52, 2517.84),
                    (3746.16, 4039.01),
                    (2046.40, 4096.18),
                ],
            ),
            _route(
                'Sunjiang Third Spirit of Portals',
                [
                    (2025.62, 7651.59),
                    (1068.59, 6107.61),
                ],
            ),
            _route(
                'Sunjiang Fourth Spirit Approach',
                [
                    (-842.38, 6629.78),
                    (-2506.68, 6619.71),
                    (-3417.18, 6856.22),
                    (-3632.37, 5204.12),
                ],
            ),
            _route('Sunjiang Fourth Spirit of Portals', [(-4634.41, 3827.36)]),
            H.skip_cinematic('Sunjiang Mid Cinematic', wait_ms=3000),
            BT.Wait(3000),
            _route(
                'Sunjiang Shiroken Constructs',
                [
                    (314.21, 1409.90),
                    (-105.44, 2130.47),
                    (-61.90, 1325.04),
                ],
            ),
            H.skip_cinematic('Sunjiang End Cinematic', wait_ms=3000),
            BT.WaitForMapLoad(map_id=cfg.completion_map, timeout_ms=120000),
        ],
    )
