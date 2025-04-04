from Py4GWCoreLib import *

MODULE_NAME = "Mission Map"

class MissionMap:
    def __init__(self):
        self.window_open = False
        self.frame_id = 0

        self.left = 0
        self.top = 0
        self.right = 0
        self.bottom = 0

        self.scale_x = 1.0
        self.scale_y = 1.0
        self.zoom = 1.0

        self.center_x = 0.0
        self.center_y = 0.0

        self.last_click_x = 0.0
        self.last_click_y = 0.0

        self.pan_offset_x = 0.0
        self.pan_offset_y = 0.0

        self.mission_map_screen_center_x = 0.0
        self.mission_map_screen_center_y = 0.0
        self.update()
        
    def update(self):
        self.window_open = Map.MissionMap.IsWindowOpen()
        self.frame_id = Map.MissionMap.GetFrameID()
        coords = Map.MissionMap.GetWindowCoords()
        self.left, self.top, self.right, self.bottom = int(coords[0]-5), int(coords[1]-1), int(coords[2]+5), int(coords[3]+2)
        self.scale_x, self.scale_y = Map.MissionMap.GetScale()
        self.zoom = Map.MissionMap.GetZoom()
        self.center_x , self.center_y = Map.MissionMap.GetCenter()
        self.last_click_x, self.last_click_y = Map.MissionMap.GetLastClickCoords()
        self.pan_offset_x, self.pan_offset_y = Map.MissionMap.GetPanOffset()
        self.mission_map_screen_center_x, self.mission_map_screen_center_y = Map.MissionMap.GetMapScreenCenter()
        
mission_map = MissionMap()

draw_frame = False
draw_color = Utils.RGBToColor(255, 255, 255, 125)

def DrawFrame():
    global mission_map

    width = mission_map.right - mission_map.left
    height = mission_map.bottom - mission_map.top
        
    Overlay().BeginDraw("MissionMapOverlay", mission_map.left, mission_map.top, width, height)
    #Overlay().DrawQuadFilled(mission_map.left, mission_map.top, mission_map.right, mission_map.top, mission_map.right, mission_map.bottom, mission_map.left, mission_map.bottom, draw_color)
    click_x, click_y = Overlay.NormalizedScreenToScreen(mission_map.last_click_x, mission_map.last_click_y)
    Overlay().DrawPoly(click_x, click_y, 100, Utils.RGBToColor(255, 100, 0, 255), 32, 10)
    Overlay().DrawPoly(mission_map.mission_map_screen_center_x, mission_map.mission_map_screen_center_y, 100, Utils.RGBToColor(255, 100, 255, 125), 32, 10)
    Overlay().EndDraw()
        
def DrawWindow():
    global draw_frame
    global mission_map, draw_color
    global MODULE_NAME
    
    if PyImGui.begin(MODULE_NAME):
        PyImGui.text(f"Window Open: {mission_map.window_open}")
        PyImGui.text(f"Frame ID: {mission_map.frame_id}")
        PyImGui.text(f"Window Coords: {mission_map.left}, {mission_map.top}, {mission_map.right}, {mission_map.bottom}")
        PyImGui.text(f"Scale: {mission_map.scale_x}, {mission_map.scale_y}")
        PyImGui.text(f"Zoom: {mission_map.zoom}")
        PyImGui.text(f"Center: {mission_map.center_x}, {mission_map.center_y}")
        PyImGui.text(f"Map Screen Center: {mission_map.mission_map_screen_center_x}, {mission_map.mission_map_screen_center_y}")
        PyImGui.text(f"Last Click: {mission_map.last_click_x}, {mission_map.last_click_y}")
        click_x, click_y = Overlay.NormalizedScreenToScreen(mission_map.last_click_x, mission_map.last_click_y)
        PyImGui.text(f"Last Click Game: {click_x}, {click_y}")
        PyImGui.text(f"Pan Offset: {mission_map.pan_offset_x}, {mission_map.pan_offset_y}")
        
    PyImGui.end()
        
def main():   
    if not Routines.Checks.Map.MapValid(): 
        return
    
    mission_map.update()
    if mission_map.window_open:
        DrawFrame()
           
    DrawWindow()

if __name__ == "__main__":
    main()
