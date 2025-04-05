from Py4GWCoreLib import *
import math

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
        self.width = self.right - self.left
        self.height = self.bottom - self.top
        self.scale_x, self.scale_y = Map.MissionMap.GetScale()
        self.zoom = Map.MissionMap.GetZoom()
        self.center_x , self.center_y = Map.MissionMap.GetCenter()
        self.center_screen_x, self.center_screen_y = Overlay.WorldMapToScreen(self.center_x, self.center_y)
        
        self.true_center_x = self.left + (self.width / 2)
        self.true_center_y = self.top + (self.height / 2)
        self.mouse_move_x, self.mouse_move_y = Overlay().GetMouseCoords()
        self.last_click_x, self.last_click_y = Map.MissionMap.GetLastClickCoords()
        self.click_screen_x, self.click_screen_y = Overlay.NormalizedScreenToScreen(self.last_click_x, self.last_click_y)
        self.pan_offset_x, self.pan_offset_y = Map.MissionMap.GetPanOffset()
        self.mission_map_screen_center_x, self.mission_map_screen_center_y = Map.MissionMap.GetMapScreenCenter()
        
        self.player_x, self.player_y = Player.GetXY()
        self.player_screen_x, self.player_screen_y = Overlay.GamePosToScreen(self.player_x, self.player_y)
        
mission_map = MissionMap()

draw_frame = False
draw_color = Utils.RGBToColor(255, 255, 255, 125)

def DrawFrame():
    global mission_map,triangle_size
    def _draw_circle(x, y, radius, color):
        Overlay().DrawPoly(x, y, radius, color, 12, 3)
    
    def _draw_point(x, y,color):
        Overlay().DrawPoly(x, y, 4, color, 8, 4)
        
    import math

    def _draw_triangle(agent_id, x, y, color, size=10.0):
        global angle  # assumes this is defined globally

        # Add user-controlled offset to facing angle
        facing_angle = Agent.GetRotationAngle(agent_id) + Utils.DegToRad(angle)

        shape = [
            (0, -size),     # tip
            (size * -0.55, size * 0.55),  # bottom left
            (size * 0.55, size * 0.55),   # bottom right
        ]

        def rotate_point(px, py, angle):
            cos_a = math.cos(angle)
            sin_a = math.sin(angle)
            return (
                px * cos_a - py * sin_a,
                px * sin_a + py * cos_a
            )

        transformed = [
            (x + dx, y + dy)
            for dx, dy in (rotate_point(px, py, facing_angle) for px, py in shape)
        ]

        Overlay().DrawTriangleFilled(
            transformed[0][0], transformed[0][1],
            transformed[1][0], transformed[1][1],
            transformed[2][0], transformed[2][1],
            color
        )

        
    def _draw_circle_3d(x, y, radius, color):
        Overlay().DrawPoly3D(x, y, Overlay.FindZ(x, y), radius, color, 12, 3)
 

    #mission map oeverlay
    Overlay().BeginDraw("MissionMapOverlay", mission_map.left, mission_map.top, mission_map.width, mission_map.height)
    #_draw_circle(mission_map.true_center_x, mission_map.true_center_y, 20, Utils.RGBToColor(217, 255, 0, 255))
    #_draw_point(mission_map.center_screen_x, mission_map.center_screen_y, Utils.RGBToColor(255, 0, 217, 125))
    agent_array = AgentArray.GetNPCMinipetArray()
    for agent_id in agent_array:
        agent_x, agent_y = Agent.GetXY(agent_id)
        agent_screen_x, agent_screen_y = Overlay.GamePosToScreen(agent_x, agent_y)
        _draw_triangle(agent_id,agent_screen_x, agent_screen_y, Utils.RGBToColor(0, 255, 255, 255),triangle_size)
        
    agent_array = AgentArray.GetEnemyArray()
    for agent_id in agent_array:
        agent_x, agent_y = Agent.GetXY(agent_id)
        agent_screen_x, agent_screen_y = Overlay.GamePosToScreen(agent_x, agent_y)
        _draw_triangle(agent_id,agent_screen_x, agent_screen_y, Utils.RGBToColor(255, 75, 0, 255),triangle_size)
        
    Overlay().EndDraw()
    
    """
    #world overlay
    Overlay().BeginDraw()    
    _draw_circle_3d(mission_map.player_x, mission_map.player_y, 20, Utils.RGBToColor(255, 0, 0, 125))
    Overlay().EndDraw()
    """
angle = -180
triangle_size = 10
def DrawWindow():
    global draw_frame
    global mission_map, draw_color, angle, triangle_size
    global MODULE_NAME
    
    if PyImGui.begin(MODULE_NAME):
        # Global
        angle = PyImGui.slider_float("angle", angle, -360.0,360.0)
        triangle_size = PyImGui.slider_int("triangle_size", triangle_size, 0,30)

        
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
