"""Chahbek Village (quest 978)."""

from __future__ import annotations

from Py4GWCoreLib import Botting
from Py4GWCoreLib import ConsoleLog

from Sources.incognito import helpers as H
from Sources.incognito.config import MissionConfig
from Sources.incognito.consumables import apply_mission_consumables
from Sources.incognito.consumables import reset_mission_consumables

FIRE_OIL_ID = 6373
NORTH_CATAPULT_ID = 6388
SOUTH_CATAPULT_ID = 6389
NPC_XY = (3542.21, -5201.80)


def build(bot: Botting, cfg: MissionConfig) -> None:
    bot.States.AddHeader('Chahbek Village')
    ConsoleLog('RMA', "Let's do Chahbek Village")

    bot.Move.XY(*NPC_XY)
    bot.Dialogs.AtXY(NPC_XY[0], NPC_XY[1], 0x81)
    bot.Wait.ForTime(1000)
    bot.Dialogs.AtXY(NPC_XY[0], NPC_XY[1], 0x84)
    bot.Wait.UntilOnExplorable()
    bot.Wait.ForTime(2000)

    def _consets():
        reset_mission_consumables()
        yield from apply_mission_consumables()

    bot.States.AddCustomState(_consets, 'Chahbek Consumables')
    H.configure_aggressive(bot)
    H.set_title(bot, H.TITLE_LIGHTBRINGER)

    bot.Move.XY(3246.24, -3531.79)
    H.aggro_path(
        bot,
        [
            (1814.75, -3718.83),
            (226.88, -5757.88),
            (-683.73, -4043.84),
            (-2000.08, -3392.83),
            (-4320.19, -2137.18),
        ],
        'Chahbek Clear Corsairs',
    )

    bot.Move.XY(-4715.77, -1836.36)
    H.interact_gadget_id(bot, FIRE_OIL_ID, 'Chahbek Oil 1')
    bot.Wait.ForTime(1000)
    bot.Move.XY(-1696.50, -2564.60)
    H.interact_gadget_id(bot, NORTH_CATAPULT_ID, 'Chahbek North Load')
    bot.Wait.ForTime(4000)
    H.interact_gadget_id(bot, NORTH_CATAPULT_ID, 'Chahbek North Fire')
    bot.Wait.ForTime(1000)

    bot.Move.XY(-4715.77, -1836.36)
    H.interact_gadget_id(bot, FIRE_OIL_ID, 'Chahbek Oil 2')
    bot.Wait.ForTime(1000)
    bot.Move.XY(-1818.94, -3599.51)
    bot.Move.XY(-1725.04, -4104.62)
    H.interact_gadget_id(bot, SOUTH_CATAPULT_ID, 'Chahbek South Load')
    bot.Wait.ForTime(4000)
    H.interact_gadget_id(bot, SOUTH_CATAPULT_ID, 'Chahbek South Fire')
    bot.Wait.ForTime(1000)

    bot.Move.XY(-2672.59, -3801.81)
    H.aggro_path(
        bot,
        [
            (-2398.64, -6207.63),
            (-4223.66, -6597.19),
            (-3909.37, -4700.47),
            (-3068.31, -2816.32),
            (-2160.76, -424.09),
            (-1698.78, 1248.06),
            (-29.31, -1009.32),
        ],
        'Chahbek Boss Finish',
    )

    H.add_skip_cinematic(bot, 'Chahbek End Cinematic', timeout_ms=30000)
    bot.Wait.ForTime(3000)
    bot.Wait.ForMapToChange(target_map_id=cfg.completion_map)
