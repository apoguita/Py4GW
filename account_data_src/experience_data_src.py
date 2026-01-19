import PyImGui
from Py4GWCoreLib import Utils, ColorPalette, Player

class ExperienceData:
    def __init__(self):
        self.level = 0
        self.experience = 0
        self.progress_pct = 0
        self.current_skill_points = 0
        self.total_earned_skill_points = 0

    def update(self):
        self.level = Player.GetLevel()
        self.experience = Player.GetExperience()
        self.progress_pct = Utils.GetExperienceProgression(self.experience)
        skill_data = Player.GetSkillPointData()
        self.current_skill_points = skill_data[0]
        self.total_earned_skill_points = skill_data[1]

    def draw_content(self):
        # Outer table: 1 column, 2 rows
        if PyImGui.begin_table("ExperienceOuter", 1, PyImGui.TableFlags.SizingStretchProp):

            # Row 1 → nested 3-column table
            PyImGui.table_next_row()
            PyImGui.table_next_column()

            if PyImGui.begin_table(
                "ExperienceHeader", 3,
                PyImGui.TableFlags.SizingStretchProp
            ):
                # Column setup: left/right auto, middle stretch
                PyImGui.table_setup_column("LevelCol",  PyImGui.TableColumnFlags.WidthFixed, 0)
                PyImGui.table_setup_column("SpacerCol", PyImGui.TableColumnFlags.WidthStretch, 1)
                PyImGui.table_setup_column("SkillCol",  PyImGui.TableColumnFlags.WidthFixed, 0)

                PyImGui.table_next_row()

                # Col 1: Level (sticks left)
                PyImGui.table_next_column()
                PyImGui.text(f"Level: {self.level}")

                # Col 2: Spacer (auto stretches, left empty)
                PyImGui.table_next_column()

                # Col 3: Skill points (sticks right)
                PyImGui.table_next_column()
                PyImGui.text(f"Skill Points: {self.current_skill_points}/{self.total_earned_skill_points}")

                PyImGui.end_table()
            

            # Row 2 → progress bar
            PyImGui.table_next_row()
            PyImGui.table_next_column()
            avail_width = PyImGui.get_content_region_avail()[0]
            PyImGui.push_style_color(PyImGui.ImGuiCol.PlotHistogram, ColorPalette.GetColor("dark_green").to_tuple_normalized())
            PyImGui.progress_bar(self.progress_pct / 100.0, avail_width, f"{self.experience:,} xp")
            PyImGui.pop_style_color(1)
            
            PyImGui.end_table()     