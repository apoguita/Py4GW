import os
from Py4GWCoreLib import Botting, ModelID  # ModelID can also be removed if unused elsewhere

# QUEST TO INCREASE SPAWNS
BOT_NAME = "The Mindsquall Farm"
OUTPOST_TO_TRAVEL = 640  # Rata Sum
COORD_TO_EXIT_MAP = (16429.57, 13491.29)  # Rata Sum exit to Magus Stones
EXPLORABLE_TO_TRAVEL = 569  # Magus Stones

KILLING_PATH = [
    (16845.38, 11494.00),
    (15590.38, 8148.21),
    (14830.84, 8253.73),
    (13010.51, 6993.52),
    (14830.84, 8253.73),
    (13010.51, 6993.52),
    (13511.45, 7823.19),
    (15123.12, 8488.75),
    (13960.76, 10583.61),
    (12175.51, 9514.61),
    (13960.76, 10583.61),
    (12175.51, 9514.61),
    (13960.76, 10583.61),
    (12175.51, 9514.61),
    (11951.20, 7661.88),
    (9738.14, 9081.23),
    (9482.51, 8770.36),
    (9082.11, 9638.05),
    (7546.94, 12105.38),
    (7221.61, 10923.58),
    (5173.30, 10854.70),
    (3845.28, 13876.48),
    (-1146.77, 12302.44),
    (-4257.07, 12403.80),
    (-6287.15, 13025.13),
    (-8988.33, 12881.63),
]

bot = Botting(BOT_NAME)

def bot_routine(bot: Botting) -> None:
    bot.States.AddHeader(BOT_NAME)
    bot.Templates.Multibox_Aggressive()
    bot.Templates.Routines.PrepareForFarm(map_id_to_travel=OUTPOST_TO_TRAVEL)
    bot.States.AddHeader(f"{BOT_NAME}_loop")
    bot.Party.SetHardMode(False)
    bot.Move.XYAndExitMap(*COORD_TO_EXIT_MAP, target_map_id=EXPLORABLE_TO_TRAVEL)
    bot.Wait.ForTime(4000)
    bot.Move.XYAndInteractNPC(14810.47, 13164.24)
    bot.Multibox.SendDialogToTarget(0x84)
    bot.Move.FollowAutoPath(KILLING_PATH)
    bot.Wait.UntilOutOfCombat()
    bot.Multibox.ResignParty()
    bot.Wait.ForTime(1000)
    bot.Wait.UntilOnOutpost()
    bot.States.JumpToStepName(f"[H]{BOT_NAME}_loop_3")

bot.SetMainRoutine(bot_routine)

def _find_shared_textures_folder() -> str:
    weapons = "Weapons Farm"
    current = os.getcwd()

    while True:
        candidates = [
            os.path.join(current, "Bots", weapons, "Textures"),
            os.path.join(current, "Weapons Farm", "Textures"),
        ]
        for c in candidates:
            if os.path.isdir(c):
                return c

        parent = os.path.dirname(current)
        if parent == current:
            return ""
        current = parent

def main():
    bot.Update()

    texture_folder = _find_shared_textures_folder()
    texture_path = os.path.join(texture_folder, f"{BOT_NAME}.png") if texture_folder else ""

    if texture_path and os.path.exists(texture_path):
        bot.UI.draw_window(icon_path=texture_path)
    else:
        bot.UI.draw_window()  # No icon shown instead of fallback

if __name__ == "__main__":
    main()
