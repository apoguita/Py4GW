"""Ruins of Surmia behavior tree."""

from __future__ import annotations

from Py4GWCoreLib import TitleID
from Py4GWCoreLib.py4gwcorelib_src.BehaviorTree import BehaviorTree
from Sources.ApoSource.ApoBottingLib import wrappers as BT
from Sources.RootTerm import bt_helpers as H
from Sources.RootTerm.config import MissionConfig

AGGRO_RANGE = 1100.0
MOVE_TIMEOUT_MS = 90000


def _combat_route(name: str, steps: list[tuple[float, float]]) -> BehaviorTree:
    return BT.VanquishNode(
        name=name,
        steps=steps,
        clear_area_radius=AGGRO_RANGE,
        pause_on_combat=True,
        timeout_ms=MOVE_TIMEOUT_MS,
    )


def build(cfg: MissionConfig) -> BehaviorTree:
    return BT.Sequence(
        name='Ruins of Surmia',
        children=[
            BT.LogMessage("Let's do Ruins of Surmia", module_name='RMA'),
            H.enter_mission('Surmia', confirm_extra=True),
            H.mission_consumables(),
            H.set_title(int(TitleID.Ebon_Vanguard)),
            _combat_route(
                'Surmia Escort Rurik',
                [
                    (-2990.50, -12068.34), (-1451.28, -10454.99), (-1140.83, -8481.46),
                    (-2442.26, -7291.99), (-4219.68, -7364.55), (-4131.06, -5608.16),
                    (-5711.31, -3834.03), (-4512.70, -3514.72), (-3440.72, -3341.73),
                    (-3187.80, -862.84), (-1094.83, -1395.68), (1618.36, -2337.94),
                    (2179.95, -3822.68), (1331.02, -5888.40), (2823.68, -6186.49),
                    (5095.79, -4959.29), (4178.48, -4874.52), (4154.47, -3954.20),
                    (4281.71, -4691.90), (6539.01, -2518.72),
                ],
            ),
            _combat_route(
                'Surmia Charr Area',
                [
                    (7464.21, -1628.94), (9550.87, -842.07), (8551.27, 1186.45),
                    (5603.75, 2546.10), (4640.82, 4523.10), (4512.21, 6395.20),
                    (6418.05, 9086.19), (3785.58, 9683), (2161.52, 8613.75),
                    (756.14, 8762.98), (-560.16, 10277.36), (-2322.63, 9445.97),
                    (-2104.17, 7361.81),
                ],
            ),
            _combat_route(
                'Surmia Free Prisoners',
                [
                    (-2330.80, 4997.18), (-3774.54, 4117.49), (-6472.18, 4775.07),
                    (-6289.30, 3832.68), (-5741.73, 6774.71), (-6034.60, 9442.67),
                    (-7660.10, 8896.11), (-6091.54, 9506.05), (-5660.81, 12139.55),
                    (-3437.10, 13486.78), (-1861.80, 14872.14),
                ],
            ),
            H.skip_cinematic('Surmia Prisoner Cinematic', wait_ms=3000),
            _combat_route(
                'Surmia Escort to Gate',
                [
                    (-1884.69, 17015.66), (-3891.78, 18144.49), (-3062.98, 19501.18),
                    (-1886.46, 20655.14), (-5269.70, 21291.35), (-1808.12, 20432.33),
                    (1929.84, 20018.25), (3144.54, 20681.38),
                ],
            ),
            _combat_route(
                'Surmia Reach Breena',
                [
                    (547.34, 20185.90), (1466.57, 18791.85), (4934.14, 17822.26),
                    (6059.02, 17504.67), (7908.88, 18600.33), (7978.23, 20093.47),
                ],
            ),
            BT.Move((7735.03, 20278.41), pause_on_combat=False, tolerance=150.0),
            H.interact_player_number(5995, 'Surmia Accept Breena Bonus', aftercast_ms=10000),
            BT.Move((8333.32, 19411.73), pause_on_combat=False),
            BT.Wait(5000),
            _combat_route(
                'Surmia Flame Keepers',
                [
                    (-6709.59, 22334.74), (-9016.87, 23108.93), (-9386.34, 20466.06),
                    (-8554.34, 17794.26), (-9092.66, 16485.51), (-10490.22, 16681.80),
                    (-10642.01, 15408.21), (-9515.96, 14596.67), (-8678.47, 16700.46),
                    (-9083.40, 19411.51), (-9151.24, 21353.85), (-7037.06, 22183.75),
                    (-6551.15, 22380.39),
                ],
            ),
            _combat_route(
                'Surmia Northern Circuit',
                [
                    (-4107.67, 21226.69), (-1795.46, 20413.27), (1530.28, 18922.37),
                    (4208.92, 18451.53), (4436.83, 20443.10), (1921.97, 22007.27),
                    (-333.66, 22899.93), (-1514.22, 25271.61), (-1175.65, 26703.38),
                    (2217.70, 26881.32), (2154.38, 24633.04), (4732.77, 23131.84),
                    (5801.08, 22354.30), (8364.18, 23146.95), (9712.70, 24683.93),
                    (9815.25, 26650.03), (10228.03, 28056.41), (9451.02, 30423.26),
                    (8497.07, 32790.30), (6306.06, 33257.16), (6099.82, 31305.29),
                    (5458.33, 32180.61),
                ],
            ),
            _combat_route(
                'Surmia Local Clear',
                [
                    (4644.99, 31751.85), (6179.79, 33234.52), (4565.98, 34653.65),
                    (3117.18, 34591.87), (3207.44, 33816.13), (3162.60, 32734.46),
                    (1542.32, 33954.33), (59.32, 32855.61), (2434.11, 31231.17),
                    (4730.04, 31830.23),
                ],
            ),
            _combat_route(
                'Surmia Return to Lever',
                [
                    (7218.03, 33030.79), (9098.33, 31701.45), (10398.20, 28859.41),
                    (9702.42, 25986.14), (9872.45, 23457.95), (7251.82, 22828.14),
                    (4640.39, 22446.67),
                ],
            ),
            H.interact_gadget_id(1707, (4640.39, 22446.67), 'Surmia Bridge Lever'),
            BT.Wait(5000),
            _combat_route(
                'Surmia Final Escort',
                [
                    (5402.62, 22677), (7251.82, 22828.14), (9872.45, 23457.95),
                    (9702.42, 25986.14), (8071.53, 27711.64), (9420.88, 30278.94),
                    (8810.73, 32506.16), (5982.33, 33660.01), (4565.98, 34653.65),
                    (3117.18, 34591.87), (3207.44, 33816.13), (3162.60, 32734.46),
                ],
            ),
            H.skip_cinematic('Surmia End Cinematic', wait_ms=3000),
            BT.WaitForMapLoad(map_id=cfg.completion_map, timeout_ms=120000),
        ],
    )
