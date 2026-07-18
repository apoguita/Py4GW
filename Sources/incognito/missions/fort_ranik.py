"""Fort Ranik (quest 937)."""

from __future__ import annotations

from Py4GWCoreLib import Botting
from Py4GWCoreLib import ConsoleLog

from Sources.incognito import helpers as H
from Sources.incognito.config import MissionConfig
from Sources.incognito.consumables import apply_mission_consumables
from Sources.incognito.consumables import reset_mission_consumables

ARMIN_ID = 2156
DEETER_ID = 2153
WRECKED_CATAPULT_ID = 1782
FIRING_LEVER_1 = 1790
FIRING_LEVER_2 = 1791


def build(bot: Botting, cfg: MissionConfig) -> None:
    bot.States.AddHeader('Fort Ranik')
    ConsoleLog('RMA', "Let's do Fort Ranik")

    bot.Map.EnterChallenge(confirm_extra=True)
    bot.Wait.UntilOnExplorable()
    bot.Wait.ForTime(2000)

    def _consets():
        reset_mission_consumables()
        yield from apply_mission_consumables()

    bot.States.AddCustomState(_consets, 'Ranik Consumables')
    H.configure_aggressive(bot)
    H.set_title(bot, H.TITLE_VANGUARD)

    H.aggro_path(
        bot,
        [
            (-4085.27, -25360.53),
            (-3305.90, -22416.73),
            (-4303.10, -18862.53),
            (-5375.19, -17085.84),
            (-5085.76, -15222.84),
            (-3487.05, -15786.19),
            (-2896.46, -12852.84),
            (-645.55, -10355.51),
        ],
        'Ranik Rescue Armin',
    )
    bot.Move.XY(-645.55, -10355.51)
    bot.Wait.ForTime(5000)

    def _talk_armin():
        ok = yield from H.interact_model_player_number_coro(ARMIN_ID, 3500.0)
        if not ok:
            ConsoleLog('RMA', 'Armin Saberlin not found — resigning.')
            from Py4GWCoreLib import Routines

            yield from Routines.Yield.Player.Resign()
            yield from Routines.Yield.wait(3000)

    bot.States.AddCustomState(_talk_armin, 'Ranik Talk Armin')

    H.aggro_path(
        bot,
        [
            (-802.04, -9461.71),
            (1340.05, -7948.62),
            (2202.21, -6534.67),
            (4290.54, -6987.38),
            (6718.88, -6680.20),
            (5561.86, -5450.06),
            (3494.28, -5974.65),
            (2994.56, -4465.93),
            (1493.77, -4579.09),
            (-572.39, -3249.40),
            (-1915.42, -872.89),
            (-431.53, 207.12),
            (1795.47, 157.74),
            (4325.37, -873.38),
            (4964.59, 1340.16),
            (5516.31, 3558.88),
        ],
        'Ranik Main Push',
    )

    H.aggro_path(
        bot,
        [
            (6672.28, 963.97),
            (6713.31, -1865.82),
        ],
        'Ranik Rescue Deeter',
    )
    bot.Wait.ForTime(3000)

    def _talk_deeter():
        yield from H.interact_model_player_number_coro(DEETER_ID, 3500.0)
        from Py4GWCoreLib import Routines

        yield from Routines.Yield.wait(20000)

    bot.States.AddCustomState(_talk_deeter, 'Ranik Talk Deeter')

    H.aggro_path(
        bot,
        [
            (6653.85, 1333.62),
            (6209.44, 3460.94),
            (3856.41, 3872.16),
            (2413.68, 5399.23),
            (1239.86, 6279.21),
            (540.20, 5586.04),
            (-601.05, 7358.60),
            (-709.04, 9076.27),
            (-2674.93, 10870.26),
            (-1958.52, 12653.42),
            (-1047.74, 13054.06),
            (2885.89, 12599.21),
            (4265.15, 15133.35),
            (2294.68, 18257.12),
            (1902.22, 15646.46),
            (774.40, 15044.29),
        ],
        'Ranik To Siegemaster',
    )
    bot.Move.XY(2045.92, 15675.97)
    H.interact_npc_xy(bot, 2045.92, 15675.97, 'Ranik Siegemaster')
    bot.Wait.ForTime(2000)
    H.add_skip_cinematic(bot, 'Ranik Cine Intro', timeout_ms=10000)
    bot.Wait.ForTime(2000)

    # Catapult parts x3
    H.aggro_path(bot, [(3893.15, 17958.28)], 'Ranik Catapult 1')
    bot.Move.XY(3893.15, 17958.28)
    H.interact_gadget_id(bot, WRECKED_CATAPULT_ID, 'Ranik Wreck 1')
    bot.Wait.ForTime(3000)
    H.add_pickup_loot(bot, 'Ranik Loot 1')
    bot.Move.XY(2045.92, 15675.97)
    H.interact_npc_xy(bot, 2045.92, 15675.97, 'Ranik Deliver 1')
    bot.Wait.ForTime(2000)

    H.aggro_path(bot, [(3012.42, 16734.00), (4401.21, 15034.08)], 'Ranik Catapult 2')
    bot.Move.XY(4401.21, 15034.08)
    H.interact_gadget_id(bot, WRECKED_CATAPULT_ID, 'Ranik Wreck 2')
    bot.Wait.ForTime(3000)
    H.add_pickup_loot(bot, 'Ranik Loot 2')
    bot.Move.XY(3360.78, 16707.18)
    bot.Move.XY(2045.92, 15675.97)
    H.interact_npc_xy(bot, 2045.92, 15675.97, 'Ranik Deliver 2')
    bot.Wait.ForTime(2000)

    H.aggro_path(bot, [(896.01, 15469.90), (1845.81, 13211.87)], 'Ranik Catapult 3')
    bot.Move.XY(2614.77, 12903.68)
    H.interact_gadget_id(bot, WRECKED_CATAPULT_ID, 'Ranik Wreck 3')
    bot.Wait.ForTime(3000)
    H.add_pickup_loot(bot, 'Ranik Loot 3')
    bot.Move.XY(761.94, 14985.39)
    bot.Move.XY(2045.92, 15675.97)
    H.interact_npc_xy(bot, 2045.92, 15675.97, 'Ranik Deliver 3')
    bot.Wait.ForTime(5000)

    bot.Move.XY(2190.47, 15324.97)
    H.interact_gadget_id(bot, FIRING_LEVER_1, 'Ranik Fire 1a')
    bot.Wait.ForTime(10000)
    H.interact_gadget_id(bot, FIRING_LEVER_1, 'Ranik Fire 1b')
    bot.Wait.ForTime(3000)

    H.aggro_path(
        bot,
        [
            (191.39, 16767.38),
            (983.85, 18899.32),
            (224.87, 20678.48),
            (-1927.14, 20366.62),
            (-2300.75, 19093.90),
        ],
        'Ranik Advance',
    )
    bot.Move.XY(-2300.75, 19093.90)
    H.interact_gadget_id(bot, FIRING_LEVER_2, 'Ranik Fire 2a')
    bot.Wait.ForTime(1000)
    H.aggro_path(bot, [(-2601.83, 17813.50)], 'Ranik Fire 2 clear')
    bot.Move.XY(-4462.94, 16802.87)
    bot.Move.XY(-2601.83, 17813.50)
    bot.Move.XY(-2300.75, 19093.90)
    H.interact_gadget_id(bot, FIRING_LEVER_2, 'Ranik Fire 2b')
    bot.Wait.ForTime(1000)

    H.aggro_path(
        bot,
        [
            (-2601.83, 17813.50),
            (-5286.51, 16186.65),
            (-6766.75, 16504.26),
            (-7945.24, 17005.83),
            (-5119.87, 20380.83),
        ],
        'Ranik Finish',
    )
    H.add_skip_cinematic(bot, 'Ranik End Cinematic', timeout_ms=30000)
    bot.Wait.ForTime(3000)
    bot.Wait.ForMapToChange(target_map_id=cfg.completion_map)
