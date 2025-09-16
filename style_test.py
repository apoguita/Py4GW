import PyImGui
from Py4GWCoreLib.ImGui import Themes

MODULE_NAME = "Style Manager"

# Start with the first theme (ImGui = 0)
selected_index = 0
theme_names = [t.name for t in Themes.StyleTheme]


def main():
    global selected_index

    if PyImGui.begin(MODULE_NAME, PyImGui.WindowFlags.AlwaysAutoResize):
        PyImGui.text("Select Theme:")

        # Correct usage: pass index, returns new index
        selected_index = PyImGui.combo("##theme_selector", selected_index, theme_names)

        # Map index back to enum
        theme_enum = list(Themes.StyleTheme)[selected_index]

        # --- Temporary Preview ---
        preview_theme = Themes(theme_enum.name)
        preview_theme.preview()
        PyImGui.text(f"Previewing theme: {theme_enum.name}")

        # Example widget
        if PyImGui.button("Example Button"):
            print("clicked!")

        PyImGui.separator()

        # --- Control buttons ---
        if PyImGui.button("Apply Theme Permanently"):
            applied_theme = Themes(theme_enum.name)
            applied_theme.apply()
            PyImGui.text(f"Applied permanently: {theme_enum.name}")

        if PyImGui.button("Reset to Default"):
            default_theme = Themes("Default")
            default_theme.revert()

    PyImGui.end()


if __name__ == "__main__":
    main()
