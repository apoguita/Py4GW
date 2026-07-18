"""The Great Northern Wall (quest 936)."""

from __future__ import annotations

from Py4GWCoreLib import Botting
from Py4GWCoreLib import ConsoleLog

from Sources.incognito import helpers as H
from Sources.incognito.config import MissionConfig
from Sources.incognito.consumables import apply_mission_consumables
from Sources.incognito.consumables import reset_mission_consumables

LEVER_ID = 1768
WRECKAGE_ID = 1784


def build(bot: Botting, cfg: MissionConfig) -> None:
    bot.States.AddHeader('Great Northern Wall')
    ConsoleLog('RMA', "Let's do The Great Northern Wall")

    bot.Map.EnterChallenge(confirm_extra=True)
    bot.Wait.UntilOnExplorable()
    bot.Wait.ForTime(2000)

    def _consets():
        reset_mission_consumables()
        yield from apply_mission_consumables()

    bot.States.AddCustomState(_consets, 'GNW Consumables')
    H.configure_aggressive(bot)
    H.set_title(bot, H.TITLE_VANGUARD)

    H.aggro_path(bot, [(5061.98, -12074.61)], 'GNW Meet NPC')
    bot.Move.XY(5061.98, -12074.61)
    H.interact_npc_xy(bot, 5061.98, -12074.61, 'GNW Start NPC')

    H.aggro_path(
        bot,
        [
            (5706.61, -9130.08),
            (3926.99, -6229.57),
            (2110.15, -4915.36),
            (-297.06, -4610.27),
            (-3143.54, -3676.85),
            (-3979.60, -370.88),
            (-2571.80, 2060.01),
            (-3317.33, 3956.84),
        ],
        'GNW To Lever',
    )
    bot.Move.XY(-3376.63, 4053.19)
    H.interact_gadget_id(bot, LEVER_ID, 'GNW Lever')
    bot.Wait.ForTime(3000)

    H.aggro_path(
        bot,
        [
            (-4599.38, 4887.53),
            (-9002.87, 4171.10),
            (-11270.41, 6707.42),
        ],
        'GNW Wreckage 1',
    )
    bot.Move.XY(-11270.41, 6707.42)
    H.interact_gadget_id(bot, WRECKAGE_ID, 'GNW Wreck 1')
    bot.Wait.ForTime(3000)
    H.add_pickup_loot(bot, 'GNW Loot 1')

    H.aggro_path(
        bot,
        [
            (-10584.39, 7644.04),
            (-8881.86, 9336.33),
            (-8132.30, 11149.50),
            (-5693.52, 11047.60),
            (-4279.90, 10616.38),
            (-5530.60, 8322.41),
            (-5275.93, 7788.11),
        ],
        'GNW Wreckage 2',
    )
    bot.Move.XY(-5275.93, 7788.11)
    H.interact_gadget_id(bot, WRECKAGE_ID, 'GNW Wreck 2')
    bot.Wait.ForTime(3000)
    H.add_pickup_loot(bot, 'GNW Loot 2')

    H.aggro_path(
        bot,
        [
            (-4415.05, 10625.60),
            (-3778.84, 12346.56),
            (-5942.57, 14587.48),
            (-5264.41, 16620.17),
            (-6996.61, 17547.64),
            (-7578.35, 15391.69),
            (-8011.11, 14160.15),
        ],
        'GNW Wreckage 3',
    )
    bot.Move.XY(-8011.11, 14160.15)
    H.interact_gadget_id(bot, WRECKAGE_ID, 'GNW Wreck 3')
    bot.Wait.ForTime(3000)
    H.add_pickup_loot(bot, 'GNW Loot 3')

    H.aggro_path(
        bot,
        [
            (-8125.60, 14659.57),
            (-7438.48, 17060.49),
            (-5125.26, 18650.97),
            (-3164.49, 18145.61),
            (-2332.38, 19051.15),
        ],
        'GNW Wreckage 4',
    )
    bot.Move.XY(-2332.38, 19051.15)
    H.interact_gadget_id(bot, WRECKAGE_ID, 'GNW Wreck 4')
    bot.Wait.ForTime(3000)
    H.add_pickup_loot(bot, 'GNW Loot 4')

    H.aggro_path(
        bot,
        [
            (-759.99, 19157.01),
            (1266.90, 17447.13),
            (-558.52, 15004.71),
        ],
        'GNW Deliver Bonus',
    )
    bot.Move.XY(-236.11, 14266.26)
    H.interact_npc_xy(bot, -236.11, 14266.26, 'GNW Bonus NPC')
    bot.Wait.ForTime(3000)
    H.interact_npc_xy(bot, -236.11, 14266.26, 'GNW Bonus NPC 2')
    bot.Wait.ForTime(3000)

    H.aggro_path(
        bot,
        [
            (-558.52, 15004.71),
            (1266.90, 17447.13),
            (-759.99, 19157.01),
            (-2332.38, 19051.15),
            (-3164.49, 18145.61),
            (-5125.26, 18650.97),
            (-7438.48, 17060.49),
            (-8125.60, 14659.57),
            (-10153.27, 13511.82),
            (-12336.72, 12080.03),
            (-15270.91, 11737.08),
            (-16858.69, 12916.42),
            (-16848.09, 15751.31),
        ],
        'GNW Finish Push',
    )
    bot.Move.XY(-14399.37, 14535.39)
    bot.Wait.ForTime(8000)
    H.add_skip_cinematic(bot, 'GNW Cinematic 1', timeout_ms=8000)

    H.move_path(
        bot,
        [
            (-14589.88, 10237.07),
            (-14779.09, 5310.65),
            (-14822.62, 4327.29),
            (-12062.61, 2330.61),
            (-8474.64, -79.85),
            (-7461.70, -2453.69),
            (-5852.72, -3949.84),
            (-2425.33, -5882.44),
            (982.79, -7060.25),
            (3183.83, -7874.11),
            (5745.67, -9608.02),
            (5061.98, -12074.61),
        ],
        'GNW Run Back',
    )
    H.interact_npc_xy(bot, 5061.98, -12074.61, 'GNW End NPC')
    bot.Wait.ForTime(1000)
    H.add_skip_cinematic(bot, 'GNW Cinematic 2', timeout_ms=30000)
    bot.Wait.ForTime(3000)
    bot.Wait.ForMapToChange(target_map_id=cfg.completion_map)
