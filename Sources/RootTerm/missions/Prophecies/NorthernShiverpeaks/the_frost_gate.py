"""The Frost Gate behavior tree."""

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
        name='The Frost Gate',
        children=[
            H.enter_mission('Frost Gate', confirm_extra=True),
            H.mission_consumables(),
            BT.AddModelToLootWhitelist(2616),
            BT.AddModelToLootWhitelist(501),
            _route(
                'Frost Gate Initial Route',
                [
                    (2507.99, 29158.33), (-152.11, 28437.97), (-1654.80, 28635.02),
                    (-2137.06, 25800.37), (-1198.94, 24615.30), (1738.81, 23509.20),
                    (536.48, 22119.72), (-287.70, 19060.61), (199.26, 17452.38),
                    (-1951.98, 16475.35), (739.03, 17550.27),
                ],
            ),
            _route(
                'Frost Gate Intervening Area',
                [
                    (2043.23, 15597.37), (-350.04, 13663.32), (418.23, 11908.01),
                    (4282.15, 12366.36), (5372.98, 10522.22), (5447.11, 8617.04),
                    (5008.80, 6977.54), (2746.78, 7269.25), (382.87, 5971.37),
                    (-1691.30, 4935.02), (-2369.01, 5506.73), (-1691.30, 4935.02),
                    (382.87, 5971.37), (2746.78, 7269.25), (5008.80, 6977.54),
                ],
            ),
            _route(
                'Frost Gate Approach Rornak Area',
                [
                    (7208.69, 5958.27), (8492.77, 3105.90), (6521.24, 1920.56),
                    (5379.68, 680.08), (7214.17, -630.60), (4917.39, 953.94),
                    (2409.27, 81.56), (1124.04, -547.04), (-1198.28, -942.42),
                    (-1664.25, -3216.48), (-3601.54, -3046.37), (-3987.79, -5933.19),
                    (-4567.96, -6441.74), (-5405.08, -7206.77), (-6126.15, -7809.15),
                    (-5851.21, -8582.82),
                ],
            ),
            _route(
                'Frost Gate Return to Rornak',
                [
                    (-4975.49, -6885.06), (-3890.84, -6078.48), (-3670.62, -3058.09),
                    (-1384.40, -1813.89), (1095.38, -439.24), (4087.63, 614.65),
                    (5588.14, 581.83), (7818.17, -993.52), (6995.70, -3512.74),
                    (9337.66, -3977.09),
                ],
            ),
            H.interact_player_number(1562, 'Frost Gate Start Rornak Escort', aftercast_ms=25000),
            _route(
                'Frost Gate Escort Rornak',
                [
                    (6995.70, -3512.74), (7818.17, -993.52), (5588.14, 581.83),
                    (4087.63, 614.65), (1095.38, -439.24), (-1384.40, -1813.89),
                    (-3670.62, -3058.09), (-3890.84, -6078.48), (-4975.49, -6885.06),
                    (-6227.38, -8218.10), (-3616.09, -8286.43),
                ],
            ),
            H.interact_gadget_id(2196, (-3754.75, -8454.17), 'Frost Gate Fire Ballista'),
            BT.Wait(3000),
            _route(
                'Frost Gate Reach Plans',
                [
                    (-6227.38, -8218.10), (-4975.49, -6885.06), (-3890.84, -6078.48),
                    (-3670.62, -3058.09), (-2695.26, -2905.09), (-614.44, -5215.14),
                    (-24.25, -6733.45), (1867.43, -6622.83), (3812.82, -6753.74),
                    (5791.86, -6222.31), (6840.31, -7862.78), (7096.01, -8070.80),
                ],
            ),
            H.interact_gadget_id(3440, (7096.01, -8070.80), 'Frost Gate Plans Chest'),
            BT.Wait(3000),
            BT.LootItems(distance=2000.0, timeout_ms=20000),
            _route(
                'Frost Gate Return Plans',
                [
                    (5791.86, -6222.31), (3812.82, -6753.74), (1867.43, -6622.83),
                    (-24.25, -6733.45), (-614.44, -5215.14), (-2695.26, -2905.09),
                    (-3670.62, -3058.09), (-3890.84, -6078.48), (-4975.49, -6885.06),
                    (-6227.38, -8218.10), (-3754.75, -8454.17),
                ],
            ),
            H.interact_player_number(1562, 'Frost Gate Deliver Plans to Rornak', aftercast_ms=3000),
            _route(
                'Frost Gate Resume Mission',
                [
                    (-6227.38, -8218.10), (-4975.49, -6885.06), (-3890.84, -6078.48),
                    (-3670.62, -3058.09), (-2695.26, -2905.09), (-614.44, -5215.14),
                    (-24.25, -6733.45), (828.95, -10925),
                ],
            ),
            H.skip_cinematic('Frost Gate Mid Cinematic', wait_ms=3000),
            _route(
                'Frost Gate First Gear',
                [(4244.74, -11344.28), (5391.77, -13726.42), (6422.43, -15717.68)],
            ),
            BT.Move((5148.44, -14684.46), pause_on_combat=False),
            BT.LootItems(distance=2000.0, timeout_ms=20000),
            H.interact_gadget_id(2210, (4863.68, -14838.41), 'Frost Gate Mechanism 1'),
            BT.Wait(8000),
            BT.LootItems(distance=2000.0, timeout_ms=20000),
            BT.MoveDirect(
                [(3411.47, -16422.07), (2438.48, -17341.37)],
                pause_on_combat=False,
                tolerance=300.0,
                timeout_ms=90000,
            ),
            _route(
                'Frost Gate Second Gear Route',
                [(2438.48, -17341.37), (595.38, -19435.06), (805.47, -21312.29)],
            ),
            BT.Move([(-417.23, -20717.56), (-1805.66, -19801.91)], pause_on_combat=False),
            H.interact_gadget_id(2212, (-2151.03, -20136.41), 'Frost Gate Mechanism 2'),
            BT.Wait(8000),
            BT.LootItems(distance=2000.0, timeout_ms=20000),
            _route(
                'Frost Gate Lever Room',
                [
                    (-1014.94, -20648.45), (1186.51, -20973.51), (546.31, -19474.91),
                    (2254.27, -21103.08), (1300.64, -21198.41),
                ],
            ),
            BT.Move(
                [(1079, -21502), (732, -21667), (397, -21826)],
                pause_on_combat=False,
            ),
            H.interact_gadget_id(2211, (397, -21826), 'Frost Gate Mechanism 3'),
            BT.Wait(8000),
            BT.LootItems(distance=2000.0, timeout_ms=20000),
            BT.Move(
                [(902.21, -21415.46), (629, -19434), (190, -19672), (-60, -19837)],
                pause_on_combat=False,
            ),
            H.interact_gadget_id(2213, (-60, -19837), 'Frost Gate Mechanism 4'),
            BT.Wait(8000),
            _route('Frost Gate Finish', [(1013.51, -18230.04)]),
            H.skip_cinematic('Frost Gate End Cinematic', wait_ms=3000),
            BT.WaitForMapLoad(map_id=cfg.completion_map, timeout_ms=120000),
        ],
    )
