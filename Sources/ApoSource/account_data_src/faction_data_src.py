import Py4GW
import PyImGui
from typing import Callable
from Py4GWCoreLib import ImGui, ColorPalette, Player
#region FactionData
BASE_PATH = Py4GW.Console.get_projects_path()
TEXTURE_BASE_PATH = BASE_PATH + "\\Textures\\Faction_Icons\\"

class FactionNode:
    TEXTURE_PATHS = {
        "Balthazar": TEXTURE_BASE_PATH + "Faction_(Balthazar).jpg",
        "Kurzick":   TEXTURE_BASE_PATH + "Faction_(Kurzick).jpg",
        "Luxon":     TEXTURE_BASE_PATH + "Faction_(Luxon).jpg",
        "Imperial":  TEXTURE_BASE_PATH + "Faction_(Imperial).jpg",
    }

    def __init__(self, name: str, data_fn: Callable):
        self.name = name
        self.data_fn = data_fn
        self.current = 0
        self.total_earned = 0
        self.max = 0
        self.texture_path = self.TEXTURE_PATHS[name]

    def update(self):
        """Fetch fresh data for this faction."""
        self.current, self.total_earned, self.max = self.data_fn()

        
    def draw_content(self):
        """Draw the faction entry (icon + stats + bar)."""
        square_side = 45
        texture_size = (square_side, square_side)
        progress = 0.0 if self.max <= 0 else self.current / self.max

        if PyImGui.begin_table(f"FactionOuter_{self.name}", 2, PyImGui.TableFlags.SizingStretchProp):
            PyImGui.table_setup_column("TextureCol", PyImGui.TableColumnFlags.WidthFixed, texture_size[0] + 5)
            PyImGui.table_setup_column("ContentCol", PyImGui.TableColumnFlags.WidthStretch, 1)
            PyImGui.table_next_row()

            # --- Column 1: Texture ---
            PyImGui.table_next_column()
            ImGui.DrawTexture(self.texture_path, *texture_size)

            # --- Column 2: Text + Bar ---
            PyImGui.table_next_column()
            if PyImGui.begin_table(f"FactionInner_{self.name}", 1, PyImGui.TableFlags.SizingStretchProp):
                PyImGui.table_next_row()
                PyImGui.table_next_column()
                PyImGui.text(f"{self.name} (Current: {self.current}, Total: {self.total_earned}, Max: {self.max})")

                PyImGui.table_next_row()
                PyImGui.table_next_column()
                avail_width = PyImGui.get_content_region_avail()[0]
                PyImGui.push_style_color(
                    PyImGui.ImGuiCol.PlotHistogram,
                    ColorPalette.GetColor("midnight_violet").to_tuple_normalized(),
                )
                PyImGui.progress_bar(progress, avail_width, f"{self.current:,}/{self.max:,}")
                PyImGui.pop_style_color(1)
                PyImGui.end_table()

            PyImGui.end_table()
            
class FactionData:
    """Container for all faction nodes."""
    def __init__(self):
        self.nodes = [
            FactionNode("Balthazar", Player.GetBalthazarData),
            FactionNode("Kurzick",   Player.GetKurzickData),
            FactionNode("Luxon",     Player.GetLuxonData),
            FactionNode("Imperial",  Player.GetImperialData),
        ]
        self.update()

    def update(self):
        for node in self.nodes:
            node.update()

    def draw_content(self):
        PyImGui.text("Faction Data:")
        for node in self.nodes:
            node.draw_content()