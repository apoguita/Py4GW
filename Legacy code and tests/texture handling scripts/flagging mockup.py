from Py4GWCoreLib import *

MODULE_NAME = "flagging mockup"

# --- Formations (relative offsets to mouse)
formations = {
    "1,2 - Double Backline Wide": [
        (250, -250), (-250, -250), (0, 200), (-350, 500), (350, 500), (-450, 300), (450, 300)
    ],
    "1,2 - Double Backline Narrow": [
        (200, -200), (-200, -200), (0, 200), (-300, 500), (300, 500), (-400, 300), (400, 300)
    ],
    "1 - Single Backline Wide": [
        (0, -250), (-150, 200), (150, 200), (-350, 500), (350, 500), (-450, 300), (450, 300)
    ],
    "1 - Single Backline Narrow": [
        (0, -250), (-100, 200), (100, 200), (-300, 500), (300, 500), (-350, 300), (350, 300)
    ],
    "1,2 - Double Backline Triple Row Wide": [
        (250, -250), (-250, -250), (-250, 0), (250, 0), (-250, 300), (0, 300), (250, 300)
    ],
    "1,2 - Double Backline Triple Row Narrow": [
        (-200, -200), (200, -200), (-200, 0), (200, 0), (-200, 300), (0, 300), (200, 300)
    ],
}

# --- State
formation_names = ["Select Formation..."] + list(formations.keys())
formation_index = 0
selected_formation = None

capturing_flag = False
finished = False
safe_time_threshold = ThrottledTimer(500)

mouse_x, mouse_y = 0, 0
final_x, final_y = 0, 0


# --- Draws a hero flag at world pos
def DrawHeroFlag(pos_x, pos_y):
    pos_z = Overlay().FindZ(pos_x, pos_y)

    Overlay().BeginDraw()
    Overlay().DrawLine3D(pos_x, pos_y, pos_z, pos_x, pos_y, pos_z - 150, Utils.RGBToColor(0, 255, 0, 255), 3)
    Overlay().DrawTriangleFilled3D(
        pos_x + 25, pos_y, pos_z - 150,          # Right base
        pos_x - 25, pos_y, pos_z - 150,          # Left base
        pos_x, pos_y, pos_z - 100,               # 50 units up
        Utils.RGBToColor(0, 255, 0, 255)
    )
    Overlay().EndDraw()
    
def DrawFlagFormation(center_x: float, center_y: float, formation_name: str):
    """
    Draws all hero flags in a given formation at world position (center_x, center_y).

    Args:
        center_x (float): X world coordinate for the center of the formation.
        center_y (float): Y world coordinate for the center of the formation.
        formation_name (str): Name of the formation to draw (must exist in `formations` dict).
    """
    if formation_name not in formations:
        Py4GW.Console.Log(MODULE_NAME, f"Formation '{formation_name}' not found.", Py4GW.Console.MessageType.Warning)
        return

    Overlay().BeginDraw()
    for offset_x, offset_y in formations[formation_name]:
        DrawHeroFlag(center_x + offset_x, center_y + offset_y)
    Overlay().EndDraw()



# --- UI + Drawing
def main():
    global capturing_flag, finished, selected_formation
    global formation_index, final_x, final_y
    global mouse_x, mouse_y, safe_time_threshold

    mouse_x, mouse_y, _ = Overlay().GetMouseWorldPos()

    # --- GUI Window ---
    if PyImGui.begin("Flagging Mockup", PyImGui.WindowFlags.AlwaysAutoResize):
        formation_index = PyImGui.combo("Formation", formation_index, formation_names)
        selected_formation = formation_names[formation_index] if formation_index > 0 else None

        if PyImGui.button("Start Capturing") and selected_formation:
            capturing_flag = True
            finished = False
            safe_time_threshold.Reset()

        PyImGui.text(f"Capturing Flag: {capturing_flag}")
        PyImGui.text(f"Finished: {finished}")
        PyImGui.text(f"Selected Formation: {selected_formation or 'None'}")
        PyImGui.text(f"Mouse Position: ({mouse_x:.2f}, {mouse_y:.2f})")
    PyImGui.end()

    if selected_formation is None:
        return

    if capturing_flag:
        DrawFlagFormation(mouse_x, mouse_y, selected_formation)

    if safe_time_threshold.IsExpired() and PyImGui.is_mouse_clicked(0):
        final_x, final_y, _ = Overlay().GetMouseWorldPos()
        capturing_flag = False
        finished = True

    if finished:
        DrawFlagFormation(final_x, final_y, selected_formation)


        
        

        

# --- Entrypoint ---
if __name__ == "__main__":
    main()
