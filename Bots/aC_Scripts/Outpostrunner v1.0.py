from Py4GWCoreLib import *
from OutpostRunner.runner_singleton import runner_fsm
from OutpostRunner.map_loader import get_regions, get_runs
from OutpostRunner.StatsManager import RunInfo
from Py4GWCoreLib import IconsFontAwesome5
from OutpostRunner.Build_Manager_Addon import BodyBlockDetection
from OutpostRunner import Build_Manager
import os
show_intro = True
# UI state
selected_region = None
selected_run    = None
selected_chain  = [] 
last_valid_next_point = None
local_freestyle = False
# Cache
_cached_regions = None
_cached_runs_by_region = {} 

# === STATIC FRIENDLY NAME MAP ===
RUN_NAME_MAP = {
    "Eye Of The North": {
        "_1_Eotn_To_Gunnars": "1 - Eotn To Gunnars",
        "_2_Gunnars_To_Longeyes": "2 - Gunnars To Longeyes",
        "_3_Longeyes_To_Doomlore": "3 - Longeyes To Doomlore",
        "_4_Gunnars_To_Sifhalla": "4 - Gunnars To Sifhalla",
        "_5_Sifhalla_To_Olafstead": "5 - Sifhalla To Olafstead",
        "_6_Olafstead_To_UmbralGrotto": "6 - Olafstead To UmbralGrotto",
        "_7_Umbral_Grotto_To_Vlox": "7 - Umbral Grotto To Vlox",
        "_8_Vlox_To_Gadds": "8 - Vlox To Gadds",
        "_9_Vlox_To_Tarnished": "9 - Vlox To Tarnished",
        "_10_Tarnished_To_Rata": "10 - Tarnished To Rata",
    }
}

# 7) Neutral button colors (light gray → slightly brighter on hover → slightly darker on active)
neutral_button        = Color(33, 51, 58, 255).to_tuple_normalized()  # default button
neutral_button_hover  = Color(140, 140, 140, 255).to_tuple_normalized()  # hovered
neutral_button_active = Color( 90,  90,  90, 255).to_tuple_normalized()  # pressed
# Freestyle active button colors (green theme)
freestyle_button         = Color(0, 180, 0, 255).to_tuple_normalized()   # base green
freestyle_button_hover   = Color(0, 220, 0, 255).to_tuple_normalized()   # brighter on hover
freestyle_button_active  = Color(0, 140, 0, 255).to_tuple_normalized()   # darker on press

def get_cached_regions():
    global _cached_regions
    if _cached_regions is None:
        _cached_regions = get_regions()
    return _cached_regions

def get_cached_runs_for_region(region: str):
    """Direct lookup from static map (no normalization/parsing)."""
    region_map = RUN_NAME_MAP.get(region, {})
    raw_runs = list(region_map.keys())        # filenames
    display_runs = list(region_map.values())  # friendly names
    return raw_runs, display_runs

def format_time(seconds: float) -> str:
    minutes = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{minutes:02}:{secs:02}"

def parse_run_filename(region, run_filename):
    name = run_filename.lstrip("_")
    parts = name.split("_")
    order = int(parts[0]) if parts[0].isdigit() else 0
    origin = parts[1]
    destination = parts[-1]
    run_id = f"{region}__{run_filename}"
    return RunInfo(order, run_id, origin, destination, region, run_filename)

def draw_ui():
    global selected_region, selected_run, selected_chain, local_freestyle, OutpostRunnerDA

    if PyImGui.begin("OutpostRunner - by: aC", PyImGui.WindowFlags.AlwaysAutoResize):
        fsm_active = bool(runner_fsm.map_chain and (runner_fsm.skill_coroutine or runner_fsm.overwatch._active))

        # --- Start/Stop buttons always visible ---
        if not Build_Manager.FREESTYLE_MODE: 
            if PyImGui.button("Start OutpostRunner"):
                if selected_chain:
                    runner_fsm.set_map_chain(sorted(selected_chain, key=lambda r: r.order))
                    runner_fsm.start()
                else:
                    ConsoleLog("OutpostRunner", "No runs in chain!")
        PyImGui.same_line(0, 5)

        if not Build_Manager.FREESTYLE_MODE:
            if PyImGui.button("Stop"):
                runner_fsm.reset()
                runner_fsm.map_chain = []
        PyImGui.same_line(0, 10)
        # Change button color if freestyle is active
        # --- Decide which color set based on current state ---
        if  Build_Manager.FREESTYLE_MODE:
            # Green when active
            PyImGui.push_style_color(PyImGui.ImGuiCol.Button,         freestyle_button)
            PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonHovered,  freestyle_button_hover)
            PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonActive,   freestyle_button_active)
        else:
            # Neutral when inactive
            PyImGui.push_style_color(PyImGui.ImGuiCol.Button,         neutral_button)
            PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonHovered,  neutral_button_hover)
            PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonActive,   neutral_button_active)

        # --- Render the button ---
        
        if not fsm_active:
            if PyImGui.button("Freestyle"):

                if not Build_Manager.FREESTYLE_MODE:
                    Build_Manager.FREESTYLE_MODE = True
                    runner_build = Build_Manager.OutpostRunnerDA()
                    Build_Manager.FREESTYLE_COROUTINE = runner_build.ProcessSkillCasting(None)
                    GLOBAL_CACHE.Coroutines.append(Build_Manager.FREESTYLE_COROUTINE)
                    ConsoleLog("OutpostRunner", "Freestyle mode started.")
                else:
                    Build_Manager.FREESTYLE_MODE = False
                    if Build_Manager.FREESTYLE_COROUTINE in GLOBAL_CACHE.Coroutines:
                        GLOBAL_CACHE.Coroutines.remove(Build_Manager.FREESTYLE_COROUTINE)
                    Build_Manager.FREESTYLE_COROUTINE = None
                    ConsoleLog("OutpostRunner", "Freestyle mode stopped.")

            PyImGui.pop_style_color(3)

        if not Build_Manager.FREESTYLE_MODE and not fsm_active:
            # --- Region Dropdown ---
            regions = list(RUN_NAME_MAP.keys())
            if not selected_region:
                selected_region = regions[0] 

            r_idx = regions.index(selected_region)
            new_r_idx = PyImGui.combo("Region", r_idx, regions)
            if new_r_idx != r_idx:
                selected_region = regions[new_r_idx]
                selected_run = None

            # --- Run Dropdown ---
            runs_raw, runs_display = get_cached_runs_for_region(selected_region)

            if not runs_raw:
                PyImGui.text("⚠ No runs found in this region!")
            else:
                if selected_run not in runs_raw:
                    selected_run = runs_raw[0]

                sel_idx = runs_raw.index(selected_run)
                new_idx = PyImGui.combo("Run", sel_idx, runs_display)
                if new_idx != sel_idx:
                    selected_run = runs_raw[new_idx]

                # --- Add Single Run ---
                if PyImGui.button("Add run to Chain"):
                    friendly_name = RUN_NAME_MAP[selected_region][selected_run]
                    try:
                        order = int(selected_run.split("_")[1])
                    except (IndexError, ValueError):
                        order = 0

                    run_info = RunInfo(
                        order=order,
                        id=f"{selected_region}__{selected_run}",
                        origin=selected_region,
                        destination=friendly_name,
                        region=selected_region,
                        run_name=selected_run
                    )
                    run_info.display = friendly_name

                    if not any(r.id == run_info.id for r in selected_chain):
                        selected_chain.append(run_info)

                PyImGui.same_line(0, 5)

                # --- Add All in Region ---
                if PyImGui.button("Add All in Region"):
                    for run_file in runs_raw:
                        friendly_name = RUN_NAME_MAP[selected_region][run_file]
                        try:
                            order = int(run_file.split("_")[1])
                        except (IndexError, ValueError):
                            order = 0

                        run_info = RunInfo(
                            order=order,
                            id=f"{selected_region}__{run_file}",
                            origin=selected_region,
                            destination=friendly_name,
                            region=selected_region,
                            run_name=run_file
                        )
                        run_info.display = friendly_name

                        if not any(r.id == run_info.id for r in selected_chain):
                            selected_chain.append(run_info)

                    ConsoleLog("OutpostRunner",f"Added all runs from region {selected_region}",Console.MessageType.Debug)

            PyImGui.separator()

            PyImGui.text("Current Chain:")
            if selected_chain:
                for idx, run in enumerate(sorted(selected_chain, key=lambda r: r.order)):
                    PyImGui.text(run.display)
                    PyImGui.same_line(0, 0)
                    if not fsm_active:
                        if PyImGui.small_button(f"Remove##{idx}"):
                            selected_chain.pop(idx)
            else:
                PyImGui.text("No runs in chain.")

        green_color = (0.0, 1.0, 0.0, 1.0)
        red_color = (1.0, 0.0, 0.0, 1.0)
        if not Build_Manager.FREESTYLE_MODE:
            stats = getattr(runner_fsm, "chain_stats", None)
            if stats is not None and stats.runs:
                #PyImGui.separator()
                PyImGui.text(f"Total time: {format_time(stats.total_chain_time())}")
                PyImGui.separator()
                for r in stats.runs:
                    if r.finished:
                        PyImGui.text(f"{r.order}: {r.display}")
                        PyImGui.same_line(0, 5)
                        PyImGui.text_colored(f"Done: {format_time(r.duration)} {IconsFontAwesome5.ICON_CHECK}", green_color)
                        if r.failures >= 1:
                            PyImGui.same_line(0, 5)
                            PyImGui.text_colored(f"fails:{r.failures}", red_color)
                    elif r.started:
                        PyImGui.text(f"{r.order}: {r.display}")
                        PyImGui.same_line(0, 5)
                        PyImGui.text_colored(f"{IconsFontAwesome5.ICON_RUNNING} in progress", green_color)
                    else:
                        PyImGui.text(f"{r.order}: {r.display} {IconsFontAwesome5.ICON_ELLIPSIS_H} not started")

        # Skillcasting status
        skill_active = bool(runner_fsm.skill_coroutine)
        overwatch_active = runner_fsm.overwatch._active
        PyImGui.separator()
        # --- Skillcasting ---
        PyImGui.text("Build Manager:")
        PyImGui.same_line(0, 5)
        if skill_active or Build_Manager.FREESTYLE_MODE:
            PyImGui.text_colored("Running", green_color)
        else:
            PyImGui.text_colored("Stopped", red_color)

        # --- Overwatch ---
        PyImGui.text("Overwatch:")
        PyImGui.same_line(0 ,5)
        if overwatch_active:
            PyImGui.text_colored("Running", green_color)
        else:
            PyImGui.text_colored("Stopped", red_color)

        # --- Stuck Detection Status ---
        is_stuck = BodyBlockDetection(seconds=2.0)
        if is_stuck:
            PyImGui.text("Bodyblock:")
            PyImGui.same_line(0, 5)
            PyImGui.text_colored("Blocked! -> Shadowstep", red_color)
        else:
            PyImGui.text("Bodyblock:")
            PyImGui.same_line(0, 5)
            PyImGui.text_colored("Not blocked", green_color)

            PyImGui.end()

        # --- Show Next Path Point (Debug) ---
        global last_valid_next_point
        next_point = runner_fsm.helpers.get_next_path_point()
        if next_point:
            x, y = next_point
            last_valid_next_point = next_point 
            #PyImGui.text(f"Next Path Point: X={x:.2f}, Y={y:.2f}")
        #else:
            #PyImGui.text("Next Path Point: None (no current map data)")

# Example skill IDs for the build
BUILD_SKILLS = [1763, 1543, 2423, 2356, 826, 952, 1031, 572]  # replace with actual IDs
ATTRIBUTES = [
    ("Deadly Arts", 3),
    ("Shadow Arts", 12),
    ("Mysticism", 12)
]

# Cache Py4GW root
PY4GW_ROOT = os.path.abspath(os.path.join(os.getcwd(), "..", ".."))

def get_full_texture_path(skill_id: int) -> str:
    """Resolve a skill ID to a full absolute texture path."""
    relative_path = GLOBAL_CACHE.Skill.ExtraData.GetTexturePath(skill_id)
    if not relative_path:
        return None
    texture_path = os.path.join(PY4GW_ROOT, relative_path)
    return os.path.normpath(texture_path)

def draw_build_window():
    if PyImGui.begin("Welcome To OutpostRunner - by: aC", True, PyImGui.WindowFlags.AlwaysAutoResize):

        # --- Title ---
        dervish = os.path.join(PY4GW_ROOT, "Textures/Profession_Icons/[10] - Dervish.png")
        assasin = os.path.join(PY4GW_ROOT, "Textures/Profession_Icons/[7] - Assassin.png")
        ImGui.DrawTexture(dervish, 30, 30)
        PyImGui.same_line(0, 6)
        ImGui.DrawTexture(assasin, 30, 30)
        PyImGui.same_line(0, 6)
        PyImGui.text_colored("Dervish / Assassin", (1.0, 0.75, 0.0, 1.0))
        PyImGui.separator()

        # --- Skills Section ---
        PyImGui.text("Build Skills:")
        PyImGui.separator()

        for skill_id in BUILD_SKILLS:
            full_texture_path = get_full_texture_path(skill_id)

            if full_texture_path and os.path.exists(full_texture_path):
                ImGui.DrawTexture(full_texture_path, 48, 48)
            else:
                Py4GW.Console.Log("BuildViewer", f"❌ Missing texture for skill {skill_id} -> {full_texture_path}", Py4GW.Console.MessageType.Warning)

            PyImGui.same_line(0, 6)

        PyImGui.new_line()
        PyImGui.separator()

        # --- Attributes ---
        PyImGui.text_colored("Attributes:", (0.6, 0.9, 1.0, 1.0))
        for attr_name, attr_value in ATTRIBUTES:
            PyImGui.bullet_text(f"{attr_name}: {attr_value}")
        PyImGui.separator()

        # Equipment section
        PyImGui.text_colored("Equipment", (0.6, 0.9, 1.0, 1.0))
        PyImGui.bullet_text("Full Radiant/Survivor/Sentry (Depending which is more necessary for an area).")
        PyImGui.bullet_text("Full Attunement/Vitae (Depending on which is more necessary for an area).")
        PyImGui.bullet_text("Defensive Set")

        PyImGui.separator()

        # Defensive Set
        PyImGui.text_colored("Defensive Set", (0.8, 0.8, 1.0, 1.0)) 
        PyImGui.bullet_text("Any martial weapon")
        PyImGui.bullet_text("\"I Have the Power!\" Inscription.")
        PyImGui.bullet_text("20% longer Enchantments.")
        PyImGui.bullet_text("16 Armor Shield.")
        PyImGui.bullet_text("-2 (while enchanted).")
        PyImGui.bullet_text("+45hp (while enchanted).")

        PyImGui.separator()

        # High Energy Set
        PyImGui.text_colored("High Energy Set", (0.8, 1.0, 0.8, 1.0))
        PyImGui.bullet_text("Any staff with +10 energy and 20% halves skill recharge of spells.")
        PyImGui.bullet_text("Defensive, Hale, Swift, or Insightful Staff Head.")
        PyImGui.bullet_text("\"Don't think twice\", \"Hale and Hearty\" or \"Seize the Day\" Inscription.")
        PyImGui.bullet_text("Staff Wrapping of Enchanting (+20% useful for lengthening Shadow Form).")

        PyImGui.separator()

        # High Energy Set
        PyImGui.text_colored("When you load the bot. you MUST! have all skills equipped", (1.0, 0.0, 0.0, 1.0))
        PyImGui.text_colored("The bot will take a snapshot of your widgets and disable them all", (1.0, 0.0, 0.0, 1.0))
        PyImGui.text_colored("When you press start!. when the run finishes it will restore your", (1.0, 0.0, 0.0, 1.0))
        PyImGui.text_colored("previously enabled widgets to their intial state.", (1.0, 0.0, 0.0, 1.0))
        PyImGui.text_colored("Do your self a favor and abandon quest: Lost Souls.", (1.0, 0.75, 0.0, 1.0))
        PyImGui.text_colored("Enjoy the running, when ready pres continue", (1.0, 0.0, 0.0, 1.0))

        if PyImGui.button("Load Skilltemplate - And load the bot"):
            # 1) Load the build
            SkillBar.LoadSkillTemplate("Ogej4NfMLTjbHY3l0k6M4OHQ8IA")
            ConsoleLog("GUI", "✅ Skillbar loaded successfully!", Console.MessageType.Info)

            # 2) Refresh Build_Manager snapshot
            runner_build = Build_Manager.OutpostRunnerDA()
            runner_build.refresh_current_skills()

            # 3) Switch GUI state → hide intro, show main bot UI
            global show_intro
            show_intro = False  # this tells main() to stop drawing build window and go straight to draw_ui()

    PyImGui.end()

def main():
    global show_intro
    if show_intro:
        draw_build_window()
    else:
        draw_ui()
        runner_fsm.fsm.update()