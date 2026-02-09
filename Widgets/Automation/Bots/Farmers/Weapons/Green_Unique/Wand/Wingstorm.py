import os
from Py4GWCoreLib import Botting

# QUEST TO INCREASE SPAWNS
BOT_NAME = "Wingstorm Farm"
MODULE_ICON = "Textures\\Module_Icons\\Wingstorm.png"
OUTPOST_TO_TRAVEL = 222  # The Eternal Grove
COORD_TO_EXIT_MAP = (-6268.25, 14450.51)  # The Eternal Grove exit to Drazach Thicket
EXPLORABLE_TO_TRAVEL = 195  # Drazach Thicket

KILLING_PATH = [
    (-8809.31, -15449.91),
    (-7470.48, -12735.28),
    (-6612.19, -11486.74),
    (-5383.67, -10481.91),
    (-5094.75, -8604.45),
    (-6231.31, -9035.03),
    (-7788.61, -9345.19),
]

bot = Botting(BOT_NAME)

def bot_routine(bot: Botting) -> None:
    bot.States.AddHeader(BOT_NAME)
    bot.Templates.Multibox_Aggressive()
    bot.Templates.Routines.PrepareForFarm(map_id_to_travel=OUTPOST_TO_TRAVEL)
    bot.States.AddHeader(f"{BOT_NAME}_loop")
    bot.Party.SetHardMode(False)
    bot.Move.XYAndExitMap(*COORD_TO_EXIT_MAP, target_map_id=EXPLORABLE_TO_TRAVEL)
    bot.Wait.ForTime(1000)
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
    Finds a shared textures folder at:
      <some parent>\\Bots\\Weapons Farm\\Textures
    (or 'textures'), starting from the current working directory (Py4GW-safe).
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

def main():
    bot.Update()

    texture_folder = _find_shared_textures_folder()
    texture_path = os.path.join(texture_folder, f"{BOT_NAME}.png") if texture_folder else ""

    # If a matching PNG exists, use it; otherwise show the window without an icon.
    if texture_path and os.path.exists(texture_path):
        bot.UI.draw_window(icon_path=texture_path)
    else:
        bot.UI.draw_window()
        
def tooltip():
    import PyImGui
    from Py4GWCoreLib import ImGui, Color
    PyImGui.begin_tooltip()

    # Title
    title_color = Color(255, 200, 100, 255)
    ImGui.push_font("Regular", 20)
    PyImGui.text_colored("Wingstorm Farmer bot", title_color.to_tuple_normalized())
    ImGui.pop_font()
    PyImGui.spacing()
    PyImGui.separator()
    # Description
    PyImGui.text("multi-account bot to farm Wingstorm weapon")
    PyImGui.spacing()
    PyImGui.bullet_text("Requirements:")
    PyImGui.bullet_text("- 6-8 well-geared accounts")
    PyImGui.bullet_text("- Hero AI widget enabled on all accounts")
    PyImGui.bullet_text("- Launch the script on the party leader only")
    PyImGui.bullet_text("Designed for Normal Mode (NM) for faster and easy run, but can be change editing True or False in the code.")
    
    # Credits
    PyImGui.text_colored("Credits:", title_color.to_tuple_normalized())
    PyImGui.bullet_text("Developed by Icefox")
    PyImGui.end_tooltip()

if __name__ == "__main__":
    main()
