from Py4GWCoreLib import ImGui, Color
import PyImGui, Py4GW
import os

MODULE_NAME = "Weapons Farm"


def scan_weapon_farm_scripts(base_path: str) -> dict[str, dict[str, list[str]]]:
    """
    Walk category -> weapon_type -> scripts.
    Returns { category: { weapon_type: [scripts] } }

    Expected structure:
      Bots/Weapons Farm/
        Cool Skins/<WeaponType>/*.py
        Green_Unique/<WeaponType>/*.py
        Textures/   (ignored)
    """
    categories: dict[str, dict[str, list[str]]] = {}

    if not os.path.isdir(base_path):
        return categories

    for category_name in sorted(os.listdir(base_path)):
        category_path = os.path.join(base_path, category_name)
        if not os.path.isdir(category_path):
            continue

        # Skip texture assets folder completely (no tab)
        if category_name.strip().lower() == "textures":
            continue

        weapon_map: dict[str, list[str]] = {}

        for weapon_type_name in sorted(os.listdir(category_path)):
            weapon_type_path = os.path.join(category_path, weapon_type_name)
            if not os.path.isdir(weapon_type_path):
                continue

            scripts = sorted([
                f for f in os.listdir(weapon_type_path)
                if f.endswith(".py")
            ])

            if scripts:
                weapon_map[weapon_type_name] = scripts

        # Only include categories that actually have scripts (avoids empty tabs)
        if weapon_map:
            categories[category_name] = weapon_map

    return categories


def tooltip():
    PyImGui.begin_tooltip()

    # Title
    title_color = Color(255, 200, 100, 255)
    ImGui.push_font("Regular", 20)
    PyImGui.text_colored("Weapons Farm Dashboard", title_color.to_tuple_normalized())
    ImGui.pop_font()
    PyImGui.spacing()
    PyImGui.separator()

    # Description
    PyImGui.text("A central management hub for automated weapon farming.")
    PyImGui.text("It categorizes your collection of farming scripts into tabs")
    PyImGui.text("based on skin rarity and weapon type for quick deployment.")
    PyImGui.spacing()

    # Features
    PyImGui.text_colored("Features:", title_color.to_tuple_normalized())
    PyImGui.bullet_text("Auto-Discovery: Scans your directory for 'Cool Skins' and 'Green Unique' scripts")
    PyImGui.bullet_text("Hierarchical Navigation: Organized by Category > Weapon Type > Map/Boss")
    PyImGui.bullet_text("Dynamic Loading: Launch any farming routine instantly with a 500ms safety delay")
    PyImGui.bullet_text("Clean UI: Uses a tree-node system to manage high volumes of farming scripts")
    PyImGui.bullet_text("Stat Tracking: Displays a count of available scripts per category in real-time")

    PyImGui.spacing()
    PyImGui.separator()
    PyImGui.spacing()

    # Credits
    PyImGui.text_colored("Credits:", title_color.to_tuple_normalized())
    PyImGui.bullet_text("Developed by Icefox")

    PyImGui.end_tooltip()

def _try_draw_texture(texture_path: str, width: int, height: int):
    """Draw WeaponsFarm.png if present; otherwise show 'No image found'."""
    try:
        if os.path.isfile(texture_path):
            ImGui.DrawTexture(texture_path=texture_path, width=width, height=height)
        else:
            PyImGui.text("No image found.")
            PyImGui.text_wrapped("Optional: add this file:")
            PyImGui.text_wrapped("Bots/Weapons Farm/Textures/WeaponsFarm.png")
    except Exception as e:
        PyImGui.text("Texture error:")
        PyImGui.text_wrapped(str(e))


def Draw_Window():
    base_path = os.path.join(Py4GW.Console.get_projects_path(), "Bots", "Weapons Farm")
    preview_image = os.path.join(base_path, "Textures", "WeaponsFarm.png")

    categories = scan_weapon_farm_scripts(base_path)

    if PyImGui.begin(MODULE_NAME, PyImGui.WindowFlags.AlwaysAutoResize):
        if PyImGui.begin_table("##MainTable", 2, PyImGui.TableFlags.NoFlag):
            # --- LEFT COLUMN: Preview Art ---
            PyImGui.table_next_column()
            if PyImGui.begin_child("##TextureChild", (280, 370), True, flags=PyImGui.WindowFlags.NoFlag):
                _try_draw_texture(preview_image, width=275, height=350)
            PyImGui.end_child()

            # --- RIGHT COLUMN: Tabs + Tree View ---
            PyImGui.table_next_column()
            if PyImGui.begin_child("##TreeChild", (300, 370), True, flags=PyImGui.WindowFlags.NoFlag):

                if not os.path.isdir(base_path):
                    PyImGui.text("Weapons Farm folder not found:")
                    PyImGui.text_wrapped(base_path)
                elif not categories:
                    PyImGui.text("No scripts found under:")
                    PyImGui.text_wrapped(base_path)
                else:
                    if PyImGui.begin_tab_bar("##WeaponsFarmTabBar"):
                        for category_name, weapon_types in categories.items():
                            if PyImGui.begin_tab_item(category_name):
                                total_scripts = sum(len(s) for s in weapon_types.values())
                                PyImGui.text(f"{category_name} scripts: {total_scripts}")

                                for weapon_type_name, scripts in weapon_types.items():
                                    weapon_label = f"{weapon_type_name} ({len(scripts)})"
                                    if PyImGui.tree_node(weapon_label):
                                        for script_file in scripts:
                                            display_name = os.path.splitext(script_file)[0]
                                            if PyImGui.button(display_name):
                                                full_path = os.path.join(
                                                    base_path,
                                                    category_name,
                                                    weapon_type_name,
                                                    script_file
                                                )
                                                Py4GW.Console.defer_stop_load_and_run(full_path, delay_ms=500)
                                        PyImGui.tree_pop()

                                PyImGui.end_tab_item()

                        PyImGui.end_tab_bar()

                PyImGui.end_child()

            PyImGui.end_table()
    PyImGui.end()


def main():
    Draw_Window()


if __name__ == "__main__":
    main()
