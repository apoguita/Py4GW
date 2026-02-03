from Py4GWCoreLib import ImGui, Color, ColorPalette
from Py4GW_widget_manager import get_widget_handler
import PyImGui, Py4GW
import os

MODULE_NAME = "Leveling"
LEVELING_SCRIPTS_PATH = os.path.join(Py4GW.Console.get_projects_path(), "Bots", "Leveling")
PROPHECIES_TEXTURE =  os.path.join(LEVELING_SCRIPTS_PATH, "Prophecies-art.png")
FACTIONS_TEXTURE =  os.path.join(LEVELING_SCRIPTS_PATH, "Factions-art.png")
NIGHTFALL_TEXTURE =  os.path.join(LEVELING_SCRIPTS_PATH, "Nightfall-art.png")
KILLROY_TEXTURE = os.path.join(LEVELING_SCRIPTS_PATH, "Kilroy Stonekins Punch-Out Extravaganza-art.png")

PROPHECIES_SCRIPTS_PATH = os.path.join(LEVELING_SCRIPTS_PATH, "Prophecies","Py4GW - LDoA.py")
FACTIONS_SCRIPTS_PATH = os.path.join(LEVELING_SCRIPTS_PATH, "Factions","Factions Character Leveler.py")
NIGHTFALL_SCRIPTS_PATH = os.path.join(LEVELING_SCRIPTS_PATH, "Nightfall","Nightfall_leveler.py")
KILLROY_SCRIPTS_PATH = os.path.join(LEVELING_SCRIPTS_PATH, "KillroyStoneskin", "Kilroy Stonekins Punch-Out Extravaganza.py")

def tooltip():
    PyImGui.begin_tooltip()

    # Title
    title_color = Color(255, 200, 100, 255)
    ImGui.push_font("Regular", 20)
    PyImGui.text_colored("Leveling Dashboard", title_color.to_tuple_normalized())
    ImGui.pop_font()
    PyImGui.spacing()
    PyImGui.separator()

    # Description
    PyImGui.text("An automated progression portal designed to handle character")
    PyImGui.text("leveling across all campaigns. It provides a visual interface")
    PyImGui.text("to launch campaign-specific leveling bots and mini-games.")
    PyImGui.spacing()

    # Features
    PyImGui.text_colored("Features:", title_color.to_tuple_normalized())
    PyImGui.bullet_text("Campaign Selector: Integrated support for Prophecies, Factions, and Nightfall")
    PyImGui.bullet_text("LDoA Support: Quick-launch for the 'Legendary Defender of Ascalon' routine")
    PyImGui.bullet_text("Killroy Extravaganza: Dedicated automation for the Kilroy Stonekin punch-out game")
    PyImGui.bullet_text("Visual HUD: High-quality campaign art and custom-themed action buttons")
    PyImGui.bullet_text("One-Click Execution: Defer-loads and runs specialized scripts with safety delays")
    PyImGui.bullet_text("Auto-Close: Automatically manages the widget state when a leveling path is started")

    PyImGui.spacing()
    PyImGui.separator()
    PyImGui.spacing()

    # Credits
    PyImGui.text_colored("Credits:", title_color.to_tuple_normalized())
    PyImGui.bullet_text("Developed by Apo")

    PyImGui.end_tooltip()

def RunAndClose(script_path: str, delay_ms: int = 500):
    Py4GW.Console.defer_stop_load_and_run(script_path, delay_ms=delay_ms)
    handler = get_widget_handler()
    handler.disable_widget("Leveling")
    
def Draw_Window():
    def image_with_caption(
        label: str,
        texture_path: str,
        caption: str,
        size: tuple[int, int] = (200, 200),
        caption_offset: tuple[int, int] = (12, 150),
        text_color=(1.0, 1.0, 1.0, 1.0),
        shadow_color=(0.0, 0.0, 0.0, 0.7),
        shadow_offset: tuple[int, int] = (2, 2),
        font_size: int = 24,
        font_style: str = "Bold"
    ):
        """
        Draws an image button with a caption that has a drop shadow.

        Args:
            label (str): Button ID/label
            texture_path (str): Path to the texture
            caption (str): Text to render under/over the image
            size (tuple[int,int]): Width, height of the image
            caption_offset (tuple[int,int]): Offset for text relative to top-left of image
            text_color (tuple): RGBA main text color
            shadow_color (tuple): RGBA shadow text color
            shadow_offset (tuple[int,int]): Offset of shadow relative to main text
            font_size (int): Caption font size
            font_style (str): Caption font style
        """
        cursor_x, cursor_y = PyImGui.get_cursor_screen_pos()

        # Draw the image button
        result = ImGui.ImageButton(label, texture_path=texture_path, width=size[0], height=size[1])
            

        # Position for main caption
        text_x = cursor_x + caption_offset[0]
        text_y = cursor_y + caption_offset[1]

        # Shadow first
        PyImGui.set_cursor_screen_pos(text_x + shadow_offset[0], text_y + shadow_offset[1])
        ImGui.text_colored(caption, color=shadow_color, font_size=font_size, font_style=font_style)

        # Main text
        PyImGui.set_cursor_screen_pos(text_x, text_y)
        ImGui.text_colored(caption, color=text_color, font_size=font_size, font_style=font_style)

        # Restore cursor below image
        PyImGui.set_cursor_screen_pos(cursor_x, cursor_y + size[1])
        return result


    if PyImGui.begin(MODULE_NAME, PyImGui.WindowFlags.AlwaysAutoResize):
        if PyImGui.begin_table("##MainTable", 3, PyImGui.TableFlags.NoFlag):
            # --- LEFT COLUMN: Texture Art ---
            PyImGui.table_next_column()
            if image_with_caption(
                label="Pre-Searing Bible (Prophecies)",
                texture_path=PROPHECIES_TEXTURE,
                caption="Pre-Searing\nBible",
                size=(200, 200),
                caption_offset=(12, 150),
                text_color=ColorPalette.GetColor("violet").to_tuple_normalized(),
                shadow_color=ColorPalette.GetColor("black").to_tuple_normalized(),
                shadow_offset=(2, 2),
                font_size=24,
                font_style="Bold"
            ):
                RunAndClose(PROPHECIES_SCRIPTS_PATH, delay_ms=250)
            PyImGui.table_next_column()
            if image_with_caption(
                label="Factions (Quick Leveler)",
                texture_path=FACTIONS_TEXTURE,
                caption="Factions\nQuick Leveler",
                size=(200, 200),
                caption_offset=(12, 150),
                text_color=ColorPalette.GetColor("gw_monk").to_tuple_normalized(),
                shadow_color=ColorPalette.GetColor("black").to_tuple_normalized(),
                shadow_offset=(2, 2),
                font_size=24,
                font_style="Bold"
            ):
                RunAndClose(FACTIONS_SCRIPTS_PATH, delay_ms=250)
            PyImGui.table_next_column()
            if image_with_caption(
                label="Nightfall Leveler",
                texture_path=NIGHTFALL_TEXTURE,
                caption="Nightfall\nLeveler",
                size=(200, 200),
                caption_offset=(12, 150),
                text_color=ColorPalette.GetColor("white").to_tuple_normalized(),
                shadow_color=ColorPalette.GetColor("black").to_tuple_normalized(),
                shadow_offset=(2, 2),
                font_size=24,
                font_style="Bold"
            ):
                RunAndClose(NIGHTFALL_SCRIPTS_PATH, delay_ms=250)
            PyImGui.end_table()
        if PyImGui.begin_table("##killroyTable", 1, PyImGui.TableFlags.NoFlag):
            PyImGui.table_next_column()
            if image_with_caption(
                label="Kilroy Stonekin's Punch-Out Extravaganza!",
                texture_path=KILLROY_TEXTURE,
                caption="Kilroy Stonekin's Punch-Out Extravaganza!",
                size=(640, 100),
                caption_offset=(12, 80),
                text_color=ColorPalette.GetColor("white").to_tuple_normalized(),
                shadow_color=ColorPalette.GetColor("black").to_tuple_normalized(),
                shadow_offset=(2, 2),
                font_size=24,
                font_style="Bold"
            ):
                RunAndClose(KILLROY_SCRIPTS_PATH, delay_ms=250)
            PyImGui.end_table()
    PyImGui.end()



def main():
    Draw_Window()


if __name__ == "__main__":
    main()
