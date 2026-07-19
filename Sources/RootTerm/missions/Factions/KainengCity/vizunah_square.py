"""Vizunah Square behavior tree (Local Quarter)."""

from Py4GWCoreLib.py4gwcorelib_src.BehaviorTree import BehaviorTree
from Sources.ApoSource.ApoBottingLib import wrappers as BT
from Sources.RootTerm import bt_helpers as H
from Sources.RootTerm.config import MissionConfig


def _route(name: str, steps: list[tuple[float, float]], radius: float = 1100.0) -> BehaviorTree:
    return BT.VanquishNode(
        name=name, steps=steps, clear_area_radius=radius, pause_on_combat=True, timeout_ms=90000
    )


def build(cfg: MissionConfig) -> BehaviorTree:
    first_arena = [
        (-4503.40, -6457.54), (-4779.42, -6910.51), (-4515.56, -7437.63),
        (-3774.39, -7841.55), (-3559.83, -5997.38),
    ]
    return BT.Sequence(
        name='Vizunah Square',
        children=[
            H.enter_mission('Vizunah'),
            H.mission_consumables(),
            BT.MoveDirect(
                [(-3560.39, -11459.60), (-3447.72, -10115.67)],
                pause_on_combat=False,
                tolerance=200.0,
                timeout_ms=90000,
            ),
            _route('Vizunah Approach Togo', [(-4039.46, -6466.64)]),
            _route('Vizunah Protect Togo', first_arena),
            H.wait_for_player_number(3172, 'Vizunah Wait for Mhenlo', max_range=2500.0, timeout_ms=360000),
            _route('Vizunah First Arena', first_arena),
            H.skip_cinematic('Vizunah First Cinematic', wait_ms=3000),
            BT.MoveDirect(
                [(-3267.91, -5625.54), (-2302.01, -4765.11)],
                pause_on_combat=False,
                tolerance=300.0,
                timeout_ms=90000,
            ),
            _route(
                'Vizunah Am Fah Route',
                [
                    (-1092.62, -4370.43), (-1729.95, -4623.46), (-1092.62, -4370.43),
                    (504.92, -4289.29), (-1092.62, -4370.43), (-1729.95, -4623.46),
                    (-2938.19, -5261.71), (-1729.95, -4623.46), (-1092.62, -4370.43),
                    (-1729.95, -4623.46), (-2938.19, -5261.71), (-1729.95, -4623.46),
                    (-1092.62, -4370.43), (504.92, -4289.29), (2856.97, -3851.57),
                    (4221.64, -3588.84), (5821.38, -4664.98), (6714.32, -6275.54),
                    (5821.38, -4664.98), (4221.64, -3588.84), (5821.38, -4664.98),
                    (6714.32, -6275.54), (7809.96, -6119.93), (7754.93, -3336.64),
                ],
            ),
            _route('Vizunah Second Arena Approach', [(7334.10, -172.34)]),
            H.wait_for_player_number(3171, 'Vizunah Wait for Togo 2', max_range=2000.0),
            H.wait_for_player_number(3172, 'Vizunah Wait for Mhenlo 2', max_range=2000.0),
            _route(
                'Vizunah Second Arena',
                [(7484.55, -112.69), (6874.22, 570.88), (6823.22, -839.56)],
            ),
            BT.MoveDirect(
                [(7397.83, 1688.80), (7907.08, 2831.84)],
                pause_on_combat=False,
                tolerance=300.0,
                timeout_ms=90000,
            ),
            _route(
                'Vizunah Middle Route',
                [
                    (10583.03, 2735.83), (10793.47, 547.85), (10541.12, 2051.24),
                    (10792.44, -1769.94), (10541.12, 2051.24), (10792.44, -1769.94),
                    (11033.45, -3371.88), (12149.98, -5516.47), (11245.04, -6998.10),
                    (12149.98, -5516.47), (11245.04, -6998.10),
                ],
            ),
            _route('Vizunah Third Arena Approach', [(11168.40, -8951.57), (9589.75, -10964.62)]),
            H.wait_for_player_number(3171, 'Vizunah Wait for Togo 3', max_range=2000.0),
            H.wait_for_player_number(3172, 'Vizunah Wait for Mhenlo 3', max_range=2000.0),
            _route(
                'Vizunah Third Arena',
                [
                    (9372.23, -10916.75), (10722.49, -12723.07), (10378.17, -10523.64),
                    (9303.62, -9522.29), (7666.43, -9682.02),
                ],
            ),
            _route(
                'Vizunah Final Am Fah',
                [(10828.44, -11674.54), (10389.75, -13355.83), (9695.34, -13685.31),
                 (8839.76, -13980.17), (8793.88, -15752.57)],
            ),
            _route(
                'Vizunah Finish',
                [
                    (8538.26, -17793.22), (6878.73, -18410.26), (4503.33, -16767.55),
                    (2759.80, -17012.39), (1789.08, -18973.98), (926.32, -19256.02),
                    (350.62, -19073.80), (628.84, -17507.08),
                ],
            ),
            H.skip_cinematic('Vizunah End Cinematic', wait_ms=3000),
            BT.WaitForMapLoad(map_id=cfg.completion_map, timeout_ms=120000),
        ],
    )
