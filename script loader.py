from Py4GWCoreLib import ImGui, GLOBAL_CACHE, TitleID
import PyImGui, Py4GW
import os

MODULE_NAME = "Vanquisher"
TEXTURE = "" #Py4GW.Console.get_projects_path() + "//Vanquisher.png"


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


def Draw_Window():
    base_path = os.path.join(Py4GW.Console.get_projects_path(), "Bots\\Vanquish\\")
    campaigns = scan_scripts(base_path)
    CURRENT_FACTION, TOTAL_EARNED, MAX_POINTS = GLOBAL_CACHE.Player.GetKurzickData()
    
    if PyImGui.begin(MODULE_NAME, PyImGui.WindowFlags.AlwaysAutoResize):
        PyImGui.text(f"Current Faction: {CURRENT_FACTION}")
        PyImGui.text(f"Total Earned: {TOTAL_EARNED}")
        PyImGui.text(f"Max Points: {MAX_POINTS}")
        kur_title = GLOBAL_CACHE.Player.GetTitle(TitleID.Kurzick)
        max_title_rank = kur_title.max_title_rank
        max_title_tier_index = kur_title.max_title_tier_index
        current_points = kur_title.current_points
        current_title_tier_index = kur_title.current_title_tier_index
        points_needed_current_rank = kur_title.points_needed_current_rank
        next_title_tier_index = kur_title.next_title_tier_index
        points_needed_next_rank = kur_title.points_needed_next_rank
        is_percentage_based = kur_title.is_percentage_based
        has_tiers = kur_title.has_tiers
        
        PyImGui.text(f"Title ID: {kur_title.title_id}")
        PyImGui.text(f"Current Points: {current_points}")
        PyImGui.text(f"Current Title Tier Index: {current_title_tier_index}")
        PyImGui.text(f"Points Needed Current Rank: {points_needed_current_rank}")
        PyImGui.text(f"Next Title Tier Index: {next_title_tier_index}")
        PyImGui.text(f"Points Needed Next Rank: {points_needed_next_rank}")
        PyImGui.text(f"Is Percentage Based: {is_percentage_based}")
        PyImGui.text(f"Has Tiers: {has_tiers}")
        PyImGui.text(f"Max Title Rank: {max_title_rank}")
        PyImGui.text(f"Max Title Tier Index: {max_title_tier_index}")

    
        if PyImGui.begin_table("##MainTable", 2, PyImGui.TableFlags.BordersInnerV):
            # --- LEFT COLUMN: Texture Art ---
            PyImGui.table_next_column()
            if PyImGui.begin_child("##TextureChild",  (250, 350), True, flags=PyImGui.WindowFlags.NoFlag):
                ImGui.DrawTexture(texture_path=TEXTURE, width=220, height=320)
            PyImGui.end_child()

            # --- RIGHT COLUMN: Tree View ---
            PyImGui.table_next_column()
            if PyImGui.begin_child("##TreeChild", (400, 350), True, flags=PyImGui.WindowFlags.NoFlag):
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
                                        Py4GW.Console.Log(
                                            MODULE_NAME,
                                            f"Clicked script {script_file} at {full_path}",
                                            Py4GW.Console.MessageType.Info,
                                        )
                                        # Optional: load/execute here
                                        # Py4GW.Console.defer_stop_load_and_run(full_path)
                                PyImGui.tree_pop()
                        PyImGui.tree_pop()
            PyImGui.end_child()

            PyImGui.end_table()
    PyImGui.end()


def main():
    Draw_Window()


if __name__ == "__main__":
    main()
