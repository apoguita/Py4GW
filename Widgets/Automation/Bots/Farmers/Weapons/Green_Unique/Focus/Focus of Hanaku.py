import os
from Py4GWCoreLib import Botting

# QUEST TO INCREASE SPAWNS 
BOT_NAME = "Focus of Hanaku Farm"
OUTPOST_TO_TRAVEL = 289
COORD_TO_EXIT_MAP = (-11133.13, -18248.88)
EXPLORABLE_TO_TRAVEL = 202

KILLING_PATH = [
    (-7080.29, -21352.27),
    (-6318.91, -20829.62)
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
    PyImGui.text_colored("Focus of Hanaku Farmer bot", title_color.to_tuple_normalized())
    ImGui.pop_font()
    PyImGui.spacing()
    PyImGui.separator()
    # Description
    PyImGui.text("Multi-account bot to farm Focus of Hanaku")
    PyImGui.spacing()
    PyImGui.bullet_text("Requirements:")
    PyImGui.bullet_text("- Seafarer's Rest outpost.")
    PyImGui.bullet_text("- Does not spawn post-Winds of Change cleansing.")
    # Credits
    PyImGui.text_colored("Credits:", title_color.to_tuple_normalized())
    PyImGui.bullet_text("Developed by Wick-Divinus")
    PyImGui.bullet_text("Contributors: Kendor")
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
