from Py4GWCoreLib import ImGui, GLOBAL_CACHE, TitleID
import PyImGui, Py4GW
import os

MODULE_NAME = "Vanquisher"
TEXTURE =  os.path.join(Py4GW.Console.get_projects_path(), "Bots\\Vanquish\\Vanquisher.png")


def scan_scripts(base_path: str) -> dict[str, dict[str, list[str]]]:
    """
    Walk campaign -> area -> scripts.
    Returns { campaign: { area: [scripts] } }
    """
    campaigns: dict[str, dict[str, list[str]]] = {}
    for campaign_name in os.listdir(base_path):
        campaign_path = os.path.join(base_path, campaign_name)
        if not os.path.isdir(campaign_path):
            continue

        campaigns[campaign_name] = {}
        for area_name in os.listdir(campaign_path):
            area_path = os.path.join(campaign_path, area_name)
            if not os.path.isdir(area_path):
                continue

            scripts = [
                f for f in os.listdir(area_path)
                if f.endswith(".py")
            ]
            campaigns[campaign_name][area_name] = scripts
    return campaigns

def configure():
    pass

def Draw_Window():
    base_path = os.path.join(Py4GW.Console.get_projects_path(), "Bots\\Vanquish\\")
    campaigns = scan_scripts(base_path)
   
    if PyImGui.begin(MODULE_NAME, PyImGui.WindowFlags.AlwaysAutoResize):
        if PyImGui.begin_table("##MainTable", 2, PyImGui.TableFlags.NoFlag):
            # --- LEFT COLUMN: Texture Art ---
            PyImGui.table_next_column()
            if PyImGui.begin_child("##TextureChild",  (280, 370), True, flags=PyImGui.WindowFlags.NoFlag):
                ImGui.DrawTexture(texture_path=TEXTURE, width=275, height=350)
            PyImGui.end_child()

            # --- RIGHT COLUMN: Tree View ---
            PyImGui.table_next_column()
            if PyImGui.begin_child("##TreeChild", (300, 370), True, flags=PyImGui.WindowFlags.NoFlag):
                for campaign_name, areas in campaigns.items():
                    total_scripts = sum(len(scripts) for scripts in areas.values())
                    campaign_label = f"{campaign_name} ({total_scripts})"

                    if PyImGui.tree_node(campaign_label):
                        for area_name, scripts in areas.items():
                            script_count = len(scripts)
                            area_label = f"{area_name} ({script_count})"

                            if PyImGui.tree_node(area_label):
                                for script_file in scripts:
                                    display_name = os.path.splitext(script_file)[0]
                                    if PyImGui.button(display_name):
                                        full_path = os.path.join(base_path, campaign_name, area_name, script_file)
                                        Py4GW.Console.defer_stop_load_and_run(full_path,delay_ms=500)
                                PyImGui.tree_pop()
                        PyImGui.tree_pop()
            PyImGui.end_child()

            PyImGui.end_table()
    PyImGui.end()


def main():
    Draw_Window()


if __name__ == "__main__":
    main()
