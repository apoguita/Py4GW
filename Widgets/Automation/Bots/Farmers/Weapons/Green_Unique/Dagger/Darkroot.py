import os
from Py4GWCoreLib import Botting

BOT_NAME = "Darkroot´s Dagger Farm"
OUTPOST_TO_TRAVEL = 230
COORD_TO_EXIT_MAP = (-4494.75, 4760.00)
EXPLORABLE_TO_TRAVEL = 209

KILLING_PATH = [
    (-19123.88, -6413.41),
    (-20367.02, -3802.24)
]

bot = Botting(BOT_NAME)

def bot_routine(bot: Botting) -> None:
    bot.States.AddHeader(BOT_NAME)
    bot.Templates.Multibox_Aggressive()
    bot.Templates.Routines.PrepareForFarm(map_id_to_travel=OUTPOST_TO_TRAVEL)
    bot.States.AddHeader(f"{BOT_NAME}_loop")
    bot.Party.SetHardMode(False)
    bot.Move.XYAndExitMap(*COORD_TO_EXIT_MAP, target_map_id=EXPLORABLE_TO_TRAVEL)
    bot.Move.FollowAutoPath(KILLING_PATH)
    bot.Wait.UntilOutOfCombat()
    bot.Multibox.ResignParty()
    bot.Wait.ForTime(1000)
    bot.Wait.UntilOnOutpost()
    bot.States.JumpToStepName(f"[H]{BOT_NAME}_loop_3")

bot.SetMainRoutine(bot_routine)

def _iter_parents(start_dir: str):
    d = os.path.abspath(start_dir)
    while True:
        yield d
        parent = os.path.dirname(d)
        if parent == d:
            break
        d = parent

def _find_shared_textures_folder() -> str:
    """
    Looks for a shared textures folder at:
      <some parent>\\Bots\\Weapons Farm\\Textures
    (or 'textures'), starting from cwd (Py4GW-safe).
    """
    weapons = "Weapons Farm"
    for base in _iter_parents(os.getcwd()):
        candidates = [
            os.path.join(base, "Bots", weapons, "Textures"),
            os.path.join(base, "Bots", weapons, "textures"),
            os.path.join(base, weapons, "Textures"),
            os.path.join(base, weapons, "textures"),
        ]
        for c in candidates:
            if os.path.isdir(c):
                return c
    return ""

def tooltip():
    import PyImGui
    from Py4GWCoreLib import ImGui, Color
    PyImGui.begin_tooltip()

    # Title
    title_color = Color(255, 200, 100, 255)
    ImGui.push_font("Regular", 20)
    PyImGui.text_colored(BOT_NAME + " bot", title_color.to_tuple_normalized())
    ImGui.pop_font()
    PyImGui.spacing()
    PyImGui.separator()
    # Description
    PyImGui.text("Multi-account bot to " + BOT_NAME)
    PyImGui.spacing()
    PyImGui.bullet_text("Requirements:")
    PyImGui.bullet_text("- Amatz Basin outpost.")
    PyImGui.bullet_text("- Trading Blows quest disabled.")

    # Credits
    PyImGui.text_colored("Credits:", title_color.to_tuple_normalized())
    PyImGui.bullet_text("Developed by Aura")
    PyImGui.bullet_text("Contributors: Wick-Divinus, XLeek")
    PyImGui.end_tooltip()

def main():
    bot.Update()

    texture_folder = _find_shared_textures_folder()
    texture_path = os.path.join(texture_folder, f"{BOT_NAME}.png") if texture_folder else ""

    if texture_path and os.path.exists(texture_path):
        bot.UI.draw_window(icon_path=texture_path)
    else:
        bot.UI.draw_window()  # No fallback icon

if __name__ == "__main__":
    main()
