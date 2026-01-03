from Py4GWCoreLib import *
from OutpostRunner.runner_singleton import runner_fsm
from OutpostRunner.map_loader import get_regions, get_runs
from OutpostRunner.StatsManager import RunInfo
from Py4GWCoreLib import IconsFontAwesome5
from OutpostRunner.Build_Manager_Addon import BodyBlockDetection
from OutpostRunner import Build_Manager
from Bots.aC_Scripts.Consumable import ConsumablesSelector
import os
import math
import time

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
    "Eye Of The North - Full Tour": {
        "_1_Eotn_To_Gunnars": "1 - Eotn -> Gunnars",
        "_2_Gunnars_To_Longeyes": "2 - Gunnars -> Longeyes",
        "_3_Longeyes_To_Doomlore": "3 - Longeyes -> Doomlore",
        "_4_Gunnars_To_Sifhalla": "4 - Gunnars -> Sifhalla",
        "_5_Sifhalla_To_Olafstead": "5 - Sifhalla -> Olafstead",
        "_6_Olafstead_To_UmbralGrotto": "6 - Olafstead -> UmbralGrotto",
        "_7_Umbral_Grotto_To_Vlox": "7 - Umbral Grotto -> Vlox",
        "_8_Vlox_To_Gadds": "8 - Vlox -> Gadds",
        "_9_Vlox_To_Tarnished": "9 - Vlox -> Tarnished",
        "_10_Tarnished_To_Rata": "10 - Tarnished -> Rata",
    },
    "Tyria - Lion's Arch To Ascalon": {
        "_1_LionsArch_To_GatesOfKryta": "1 - Lions Arch -> Gates Of Kryta",
        "_2_GatesOfKryta_To_BeaconsPerch": "2 - Gates Of Kryta -> Beacons Perch",
        "_3_BeaconsPerch_To_IceToothCave": "3 - Beacon's Perch -> Ice Tooth Cave",
        "_4_IceToothCave_To_YaksBend": "4 - Ice Tooth's Cave -> Yak's Bend",
        "_5_YaksBend_To_GrendichCourthouse": "5 - Yak's Bend -> Grendich Courthouse",
        "_6_GrendichCourthouse_To_NolaniAcademy": "6 - Grendich Courthouse -> Nolani Academy",
        "_7_GrendichCourthouse_To_PikenSquare": "7 - Grendich Courthouse -> Piken Square",
        "_8_PikenSquare_To_AscalonCity": "8 - Piken Square -> Ascalon City",
    },
    "Tyria - Ascalon to Lion's Arch": {
        "_1_AscalonCity_To_PikenSquare": "1 - Ascalon City -> Piken Square",
        "_2_PikenSquare_To_GrendichCourthouse": "2 - Piken Square -> Grendich Court House",
        "_3_GrendichCourthouse_To_YaksBend": "3 - Grendich Court House -> Yak's Bend",
        "_4_YaksBend_To_BorlisPass": "4 - Yak's Bend -> Borlis Pass",
        "_5_YaksBend_To_IceToothCave": "5 - Yak's Bend -> Ice Tooth Cave",
        "_6_IceToothCave_To_BeaconsPerch": "6 - IceTooth Cave -> Beacon's Perch",
        "_7_BeaconsPerch_To_GatesOfKryta": "7 - Beacons Perch -> Gates Of Kryta",
        "_8_GatesOfKryta_To_LionsArch": "8 - Gates Of Kryta -> Lion's Arch",
    },
    "Tyria - Beacon's Perch To Droknars Forge": {
        "_1_BeaconsPerch_To_CampRankor": "1 - Beacons Perch -> Camp Rankor",
        "_2_CampRankor_To_DroknarsForge": "2 - Camp Rankor -> Droknars Forge",

    },
    "Tyria - Ascalon - East Outposts": {
        "_1_AscalonCity_To_Sardelac": "1 - Ascalon City -> Sardelac",
        "_2_Sardelac_To_FortRanik": "2 - Sardelac -> Fort Ranik",
        "_3_FortRanik_To_SerenityTemple": "3 - Fort Ranik -> Serenity Temple",
        "_4_SerenityTemple_To_FrontierGate": "4 - Serenity Temple -> Frontier Gate",
        "_5_FrontierGate_To_RuinsOfSurmia": "5 - Frontier Gate -> Ruins Of Surmia",
    },
    "Tyria - Kryta - West Outposts": {
        "_1_LionsArch_To_DAlessioSeaboard": "1 - Lion's Arch -> D'Alessio Seabord",
        "_2_DAlessioSeaboard_To_BergenHotsprings": "2 - D'Alessio Seaboard -> Bergen Hot Springs",
        "_3_BergenHotSprings_To_BeetleTun": "3 - Bergen Hot Springs -> Beetletun",
        "_4_Beetletun_To_DivinityCoast": "4 - Beetletun -> Divinity Coast",
        "_5_BergenHotSprings_To_TempleOfTheAges": "5 - Bergen Hot Springs -> Temple Of The Ages",
        "_6_TempleOfTheAges_To_FishermensHaven": "6 - Temple Of The Ages -> Fishermen's Haven",
        "_7_FishermensHaven_To_SanctumCay": "7 - Fishermen's Haven -> Sanctum Cay",
        "_8_FishermensHaven_To_RiversideProvince": "8 - Fishermen's Haven -> Riverside Province",
    },
    "Tyria - Maguuma Outposts": {
        "_1_templeoftheages_to_thewilds": "1 - Temple Of The Ages -> The Wilds",
        "_2_thewildsoutpost_to_druidsoverlook": "2 - The Wilds Outpost -> Druid's Overlook",
        "_3_druidsoverlook_to_quarrelfalls": "3 - Druid's Overlook -> Quarrel Falls",
        "_4_quarrelfalls_to_bloodstonefenoutpost": "4 - Quarrel Falls -> Bloodstone Fen",
        "_5_quarrelfalls_to_ventarisrefuge": "5 - Quarrel Falls -> Ventari's Refuge",
        "_6_ventarisrefuge_to_auroragladeoutpost": "6 - Ventari's Refuge -> Aurora Glade",
        "_7_auroragladeoutpost_to_maguumastade": "7 - Aurora Glade -> Maguuma Stade",
        "_8_maguumastade_to_hengeofdenravi": "8 - Maguuma Stade -> Henge of Denravi",
    },
    "Tyria - Desert Outposts": {
        "_1_auguryrock_to_destinysgorge": "1 - Augury Rock -> Destiny's Gorge",
        "_2_destinysgorge_to_thirstyriver": "2 - Destiny's Gorge -> Thirsty River",
        "_3_destinysgorge_to_elonareach": "3 - Destiny's Gorge -> Elona Reach",
        "_4_elonareach_to_seekerspassage": "4 - Elona Reach -> Seeker's Passage",
        "_5_auguryrock_to_heroesaudience": "5 - Augury Rock -> Heroes Audience",
        "_6_heroesaudience_to_dunesofdespair": "6 - Heroes Audience -> Dunes of Despair",
    },
    "NF - Istan island": {
        "_1_kamadanjewelofistan_to_sunspeargreathall": "1 - Kamadan -> Sunspear Greathall",
        "_2_sunspeargreathall_to_theastralarium": "2 - Sunspear Greathall -> The Astralarium",
        "_3_sunspeargreathall_to_championsdawn": "3 - Sunspear Greathall -> Champions Dawn",
        "_4_championsdawn_to_beknurharbor": "4 - Champions Dawn -> Beknur Harbor",
        "_5_beknurharbor_to_kodlonuhamlet": "5 - Beknur Harbor -> Kodlonu Hamlet",
        "_6_championsdawn_to_jokanurdiggingsoutpost": "6 - Champions Dawn -> Jokanur Diggings",
        "_7_jokanurdiggingsoutpost_to_blacktidedenoutpost": "7 - Jokanur Diggings -> Blacktide Den",

    },
    "NF - Vabbi Tour": {
        "_1_basaltgrotto_to_jennurshordeoutpost": "1 - Basalt Grotto -> Jennur's Horde Outpost",
    },
    "Wayfarers Reverie - Tyria": {
        "_1_serenitytemple_to_pockmarkflats": "1 - Visit the Searing crystal near Serenity Temple",
        "_2_grendichcourthouse_to_flametemplecorridor": "2 - Visit the Flame Temple",
        "_3_templeoftheages_to_kessexpeak": "3 - Visit the Wizard's Tower",
        "_4_templeoftheages_to_majestysrest": "4 - Visit the Mausoleum in Majesty's Rest.",
        "_5_icetoothcave_to_anvilrock": "5 - Visit Anvil Rock",
        "_6_ventarisrefuge_to_thefalls": "6 - Visit the Falls in the Maguuma Jungle.",
        "_7_thegranitecitadel_to_mineralsprings": "7 - Visit the ancient temple of Lyssa in Mineral Springs",
        "_8_auguryrockoutpost_to_thearidsea": "8 - Visit the ruined statues of the Arid Sea",

    },
    "Wayfarers Reverie - Elona": {
        "_1_blacktideden_to_fahranurthefirstcity": "1 - Visit Fahranur, the First City",
        "_2_kodlonuhamlet_to_mehtanikeys": "2 - Visit the Cyclone Palace in Mehtani Keys",
        "_3_camphojanu_to_barbarousshore": "3 - Visit the secret corsair docks on the Barbarous Shore",
        "_4_sunspearsanctuary_to_jahaibluffs": "4 - Visit the impregnable Fortress of Jahai",
        "_5_mihanutownship_to_holdingsofchokhin": "5 - Visit the vast libraries of the Halls of Chokhin",
        "_7_lairoftheforgotten_to_poisonedoutcrops": "7 - Visit the Hallowed Point in the Poisoned Outcrops",
        "_8_themouthoftorment_to_crystaloverlook": "8 - Visit the Crystal Overlook teleporter", 
    },
    "Wayfarers Reverie - Cantha": {
        "_1_ministerchosestateoutpost_to_sunquavale": "1 - Visit the Shrine of Maat",
        "_2_zendaijunoutpost_to_haijulagoon": "2 - Visit the Haiju Lagoon",
        "_3_zinkucorridor_to_tahnnakaitemple": "3 - Visit the Tahnnakai Temple",
        "_4_senjiscorner_to_nahpuiquarter": "4 - Visit the Nahpui Quarter",
        "_5_altrummruinsoutpost_to_arborstone": "5 - Visit Arborstone's Central Chamber",
        "_6_theauriosminesoutpost_to_rheascrater": "6 - Visit the entombed leviathan in Rhea's Crater",
        "_7_harvesttemple_to_unwakingwaters": "7 - Visit the whirlpool's edge",
        "_8_imperialsanctumoutpost_to_raisupalace": "8 - Visit Raisu Palace",
    },
    "Wayfarers Reverie - The Far North": {
        "_1_eyeofthenorthoutpost_to_icecliffchasms": "1 - Visit Gwen's Garden",
        "_2_sifhalla_to_drakkarlake": "2 - Visit Drakkar Lake",
        "_3_longeyesledge_to_bjoramarches": "3 - Visit the Shrine of the Bear Spirit",
        "_4_doomloreshrine_to_daladauplands": "4 - Visit the strange ridge in Dalada Uplands",
        "_5_doomloreshrine_to_sacnothvalley": "5 - Visit the burning forest in Sacnoth Valley",
        "_6_ratasum_to_rivenearth": "6 - Visit the G.O.L.E.M site",
        "_8_vloxsfalls_to_arborbay": "8 - Visit Ventari's sanctuary.",
    },
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

class ConsumablesHelper:
    def __init__(self):
        self.started = False

    def run(self):
        while True:
            if not self.started:
                yield from Routines.Yield.wait(500)
                continue

            # basic guards (same style as TitleHelper loop) :contentReference[oaicite:3]{index=3}
            if not Routines.Checks.Map.MapValid():
                yield from Routines.Yield.wait(1000)
                continue
            if Agent.IsDead(GLOBAL_CACHE.Player.GetAgentID()):
                yield from Routines.Yield.wait(1000)
                continue

            s = ConsumablesSelector.consumable_state

            if s.get("Cupcake", False):
                yield from Routines.Yield.Upkeepers.Upkeep_BirthdayCupcake()
            if s.get("Alcohol", False):
                yield from Routines.Yield.Upkeepers.Upkeep_Alcohol(target_alc_level=1 , disable_drunk_effects=True)
            if s.get("Morale", False):
                yield from Routines.Yield.Upkeepers.Upkeep_Morale(110)
            if s.get("CitySpeed", False):
                yield from Routines.Yield.Upkeepers.Upkeep_City_Speed()

            # small idle between passes
            yield from Routines.Yield.wait(500)

def draw_ui():
    global selected_region, selected_run, selected_chain, local_freestyle, OutpostRunnerDA

    if PyImGui.begin("OutpostRunner - by: aC", PyImGui.WindowFlags.AlwaysAutoResize):
        fsm_active = bool(runner_fsm.map_chain and (runner_fsm.skill_coroutine or runner_fsm.overwatch._active))

        # --- Consumable helper ---
        helper = consumables_helper  
        was_running = helper.started
        label = "Cons: ON" if was_running else "Cons: OFF"

        if was_running:
            PyImGui.push_style_color(PyImGui.ImGuiCol.Text, (0.20, 0.90, 0.20, 1.0))

        clicked = PyImGui.button(label)

        if was_running:
            PyImGui.pop_style_color(1)

        if clicked:
            helper.started = not was_running
            if helper.started:
                ConsoleLog("FSM", "Starting consumable upkeep...", Console.MessageType.Debug)
            else:
                ConsoleLog("FSM", "Consumable upkeep stopped.", Console.MessageType.Debug)

        PyImGui.same_line(0, 10)
        PyImGui.push_style_color(PyImGui.ImGuiCol.Text, (1.0, 1.0, 0.3, 1.0))
        if PyImGui.button("Options"):
            ConsumablesSelector.show_consumables_selector = True
        PyImGui.pop_style_color(1)
        PyImGui.same_line(0, 5)
        PyImGui.text(f"Drunk Level: {Effects.GetAlcoholLevel()}")

        if ConsumablesSelector.show_consumables_selector:
            ConsumablesSelector.draw_consumables_selector_window()

        PyImGui.separator()

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

                PyImGui.same_line(0, 5)
                if selected_chain:
                    if PyImGui.button("Clear"):
                        selected_chain.clear()
                        runner_fsm.map_chain = []
                        ConsoleLog("OutpostRunner", "Cleared runs chain", Console.MessageType.Debug)

            PyImGui.separator()

            if selected_chain:
                PyImGui.text("Current Chain:")
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
        return ""
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
                Py4GW.Console.Log("BuildViewer", f"Missing texture for skill {skill_id} -> {full_texture_path}", Py4GW.Console.MessageType.Warning)

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
            SkillBar.LoadSkillTemplate("Ogej4NfMLTjbHY3l0k6M4OHQ8IA")
            ConsoleLog("GUI", "Skillbar loaded successfully!", Console.MessageType.Info)

            runner_build = Build_Manager.OutpostRunnerDA()
            runner_build.refresh_current_skills()

            global show_intro
            show_intro = False

    PyImGui.end()

# Constants
SCRIPT_DIR = os.getcwd()
OUTPOST_PATH_DIR = "Wayfarer's_Reverie_maps/"

state = {
    "active": False,
    "outpost": None,
    "segments": [],
    "final_outpost": None,
    "current_path": [],
    "last_pos": None,
    "last_map_id": None,
    "mode": None,
    "waiting_for_new_map": False
}

if not os.path.exists(OUTPOST_PATH_DIR):
    os.makedirs(OUTPOST_PATH_DIR)

def get_map_name():
    return Map.GetMapName()

def get_map_id():
    return Map.GetMapID()

def reset_state():
    state["active"] = False
    state["outpost"] = None
    state["segments"] = []
    state["final_outpost"] = None
    state["current_path"] = []
    state["last_pos"] = None
    state["last_map_id"] = None
    state["mode"] = None
    state["waiting_for_new_map"] = False

def render_path_ui():
    PyImGui.begin("OutpostRunner Logger", PyImGui.WindowFlags.AlwaysAutoResize)

    if not state["active"]:
        if PyImGui.button("Start Logging Run"):
            state["active"] = True
            name = get_map_name().replace(" ", "")
            state["outpost"] = {
                "name": name,
                "id": get_map_id(),
                "path": [],
            }
            state["last_map_id"] = get_map_id()
            state["mode"] = "outpost"
            state["last_pos"] = None
            ConsoleLog("Logger", f"Started run from outpost: {name}", Console.MessageType.Info)
    else:
        PyImGui.text(f"Logging: YES")
        PyImGui.text(f"Outpost: {state['outpost']['name']} (ID: {state['outpost']['id']})")
        PyImGui.text(f"Segments recorded: {len(state['segments'])}")
        PyImGui.text(f"Current map: {get_map_name()}")

        if PyImGui.button("Finish"):
            if state["current_path"]:
                state["segments"].append({
                    "name": state["current_segment_name"],
                    "id": state["current_segment_id"],
                    "path": state["current_path"][:],
                })

            final_name = get_map_name().replace(" ", "")
            final_id = get_map_id()
            state["final_outpost"] = {"name": final_name, "id": final_id}

            base_var = f"_1_{state['outpost']['name'].lower()}_to_{final_name.lower()}"
            filename = os.path.join(OUTPOST_PATH_DIR, f"{base_var}.py")

            try:
                with open(filename, "w") as f:
                    f.write("from Py4GWCoreLib.enums import outpost_name_to_id, explorable_name_to_id\n\n")

                    f.write("# 1) IDs\n")
                    f.write(f"{base_var}_ids = {{\n")
                    f.write(f'    "outpost_id": {state["outpost"]["id"]},\n')
                    f.write("}\n\n")

                    f.write("# 2) Outpost exit path\n")
                    f.write(f"{base_var}_outpost_path = [\n")
                    for x, y in state["outpost"]["path"]:
                        f.write(f"    ({round(x)}, {round(y)}),\n")
                    f.write("]\n\n")

                    f.write("# 3) Segments\n")
                    f.write(f"{base_var}_segments = [\n")
                    for seg in state["segments"]:
                        f.write("    {\n")
                        f.write(f'        "map_id": {seg["id"]},\n')
                        f.write('        "path": [\n')
                        for x, y in seg["path"]:
                            f.write(f"            ({round(x)}, {round(y)}),\n")
                        f.write("        ],\n")
                        f.write("    },\n")
                    f.write("    {\n")
                    f.write(f'        "map_id": {final_id},\n')
                    f.write('        "path": [],  # no further walking once you arrive\n')
                    f.write("    },\n")
                    f.write("]\n")

                ConsoleLog("Logger", f"Path saved to {filename}", Console.MessageType.Success)
            except Exception as e:
                ConsoleLog("Logger", f"Failed to save path: {str(e)}", Console.MessageType.Error)

            reset_state()

    x, y = GLOBAL_CACHE.Player.GetXY()
    PyImGui.text(f"Player Pos: ({int(x)}, {int(y)})")
    if PyImGui.button("Copy position"):
        PyImGui.set_clipboard_text(f"({int(x)}, {int(y)}),")

    # Facing vector from heading
    heading = Agent.GetRotationAngle(Player.GetAgentID())
    facing_vec = (math.cos(heading), math.sin(heading))

    # Projected point 1000 units forward
    projected_x = int(x + facing_vec[0] * 500)
    projected_y = int(y + facing_vec[1] * 500)

    PyImGui.text(f"Facing Point (+500): ({projected_x}, {projected_y})")
    if PyImGui.button("Copy Portal point"):
        PyImGui.set_clipboard_text(f"({projected_x}, {projected_y}),")

    
    PyImGui.end()

def log_path():
    if not state["active"]:
        return

    x, y = GLOBAL_CACHE.Player.GetXY()
    current_map_id = get_map_id()

    if (x, y) == (0, 0):
        if not state["waiting_for_new_map"]:
            if state["last_pos"] is not None and state.get("prev_last_pos") is not None:
                x1, y1 = state["prev_last_pos"]
                x2, y2 = state["last_pos"]
                dx, dy = x2 - x1, y2 - y1
                length = (dx ** 2 + dy ** 2) ** 0.5
                if length != 0:
                    scale = 1000 / length
                    extra_point = (round(x2 + dx * scale), round(y2 + dy * scale))
                    state["current_path"].append(extra_point)
                    ConsoleLog("Logger", f"Added portal push step at {extra_point}", Console.MessageType.Info)
            state["waiting_for_new_map"] = True
        return  

    if Map.IsMapLoading():
        return

    if current_map_id != state["last_map_id"]:
        new_name = get_map_name().replace(" ", "")
        if not new_name or current_map_id == 0 or (x == 0 and y == 0):

            ConsoleLog("Logger", f"Detected map change: {state['last_map_id']} -> {current_map_id}", Console.MessageType.Info)

        if state["mode"] == "outpost":
            state["outpost"]["path"] = state["current_path"][:]
        elif state["mode"] == "explorable":
            state["segments"].append({
                "name": state["current_segment_name"],
                "id": state["current_segment_id"],
                "path": state["current_path"][:],
            })

        state["current_path"] = []
        state["last_pos"] = None
        state["last_map_id"] = current_map_id
        state["mode"] = "explorable"
        state["current_segment_name"] = new_name
        state["current_segment_id"] = current_map_id
        state["waiting_for_new_map"] = False
        ConsoleLog("Logger", f"Started new segment in: {state['current_segment_name']}", Console.MessageType.Info)
        return

    threshold = 100  # record more frequent points (denser sampling for better path fidelity)
    if (x, y) != (0, 0):
        if state["last_pos"] is None or Utils.Distance((x, y), state["last_pos"]) >= threshold:
            state["prev_last_pos"] = state.get("last_pos")
            state["last_pos"] = (x, y)
            state["current_path"].append((x, y))

# Globals for testing
path = []
result_path = []
x, y = 6698, 16095

start_process_time = time.time()
elapsed_time = 0.0
pathing_object = AutoPathing()
path_requested = False

# Config options
smooth_by_los = True
smooth_by_chaikin = False
margin = 100.0
step_dist = 500.0
chaikin_iterations = 1

# === Instantiate & wire into your app loop (same as TitleHelper) ===
consumables_helper = ConsumablesHelper()
consumables_runner = consumables_helper.run()

def main():
    global show_intro
    if show_intro:
        draw_build_window()
    else:
        draw_ui()
        runner_fsm.fsm.update()
    try:
        next(consumables_runner)
    except StopIteration:
        pass
    if  Build_Manager.FREESTYLE_MODE:
        render_path_ui()
        log_path()
        def draw_path(points, rgba):
            if points and len(points) >= 2:
                color = Color(*rgba).to_dx_color()
                for i in range(len(points) - 1):
                    x1, y1, z1 = points[i]
                    x2, y2, z2 = points[i + 1]
                    z1 = DXOverlay.FindZ(x1, y1) - 125
                    z2 = DXOverlay.FindZ(x2, y2) - 125
                    DXOverlay().DrawLine3D(x1, y1, z1, x2, y2, z2, color, False)

        global result_path, x, y, start_process_time, pathing_object, path_requested, elapsed_time
        global smooth_by_los, smooth_by_chaikin, margin, step_dist, chaikin_iterations


        if PyImGui.begin("Pathing Test", PyImGui.WindowFlags.AlwaysAutoResize):

            player_pos = GLOBAL_CACHE.Player.GetXY()
            player_z = Agent.GetZPlane(GLOBAL_CACHE.Player.GetAgentID())
            map_id = PyMap.PyMap().map_id.ToInt()
            x = PyImGui.input_int("Target X", x)
            y = PyImGui.input_int("Target Y", y)

            if PyImGui.button("Capture Start Position"):
                player_pos = GLOBAL_CACHE.Player.GetXY()
                x = int(player_pos[0])
                y = int(player_pos[1])
                print(f"Captured start position: ({x}, {y})")
                
            PyImGui.separator()
            smooth_by_los = PyImGui.checkbox("Smooth by LOS", smooth_by_los)
            margin = PyImGui.input_float("LOS Margin", margin)
            step_dist = PyImGui.input_float("LOS Step Dist", step_dist)
            smooth_by_chaikin = PyImGui.checkbox("Smooth by Chaikin", smooth_by_chaikin)
            chaikin_iterations = PyImGui.input_int("Chaikin Iterations", chaikin_iterations)

            if PyImGui.button("Search Path"):
                start_process_time = time.time()
                path_requested = True
                def search_path_coroutine():
                    global result_path, path_requested, elapsed_time
                    zplane = Agent.GetZPlane(GLOBAL_CACHE.Player.GetAgentID())
                    result_path = yield from pathing_object.get_path(
                        (player_pos[0], player_pos[1], zplane),
                        (x, y, zplane),
                        smooth_by_los=smooth_by_los,
                        margin=margin,
                        step_dist=step_dist,
                        smooth_by_chaikin=smooth_by_chaikin,
                        chaikin_iterations=chaikin_iterations
                    )
                    path_requested = False
                    yield
                    elapsed_time = time.time() - start_process_time
                    

                GLOBAL_CACHE.Coroutines.append(search_path_coroutine())

            PyImGui.separator()
            PyImGui.text(f"Map ID: {map_id}")
            PyImGui.text(f"Player: ({player_pos[0]:.1f}, {player_pos[1]:.1f}, {player_z})")
            PyImGui.text(f"Target: ({x}, {y}, {player_z})")
            PyImGui.text(f"Distance to target: {math.hypot(player_pos[0] - x, player_pos[1] - y):.1f} units")

            navmesh = pathing_object.get_navmesh()
            if navmesh:
                start_trap = navmesh.find_trapezoid_id_by_coord(player_pos)
                goal_trap = navmesh.find_trapezoid_id_by_coord((x, y))
                PyImGui.text(f"Start Trapezoid ID: {start_trap}")
                PyImGui.text(f"Goal Trapezoid ID: {goal_trap}")

                if start_trap and goal_trap:
                    los = navmesh.has_line_of_sight(player_pos, (x, y))
                    PyImGui.text(f"Line of Sight: {'YES' if los else 'NO'}")

            else:
                PyImGui.text("NavMesh not loaded.")

            PyImGui.separator()
            if path_requested:
                PyImGui.text("Searching for path...")
            else:
                if result_path:
                    PyImGui.text(f"Path found with {len(result_path)} points")
                    PyImGui.text(f"NavMesh load time: {elapsed_time:.2f} seconds")
                    
                    if PyImGui.button("Follow Path") and result_path:
                        def follow_path_coroutine():
                            path2d = [(x, y) for (x, y, _) in result_path]
                            yield from Routines.Yield.Movement.FollowPath(path2d)
                            yield
                        GLOBAL_CACHE.Coroutines.append(follow_path_coroutine())


                    if PyImGui.collapsing_header("Path Points", PyImGui.TreeNodeFlags.DefaultOpen):
                        for i, point in enumerate(result_path):
                            PyImGui.text(f"Point {i}: ({point[0]:.1f}, {point[1]:.1f}, {point[2]:.1f})")
                else:
                    PyImGui.text("No path found or search not initiated.")

            PyImGui.end()

        draw_path(result_path, (255, 255, 0, 255))  # Yellow
