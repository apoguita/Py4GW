from Py4GWCoreLib import *
from typing import Optional
import math

MODULE_NAME = "Mission Map"

    
class Shape:
    def __init__(self, name:str, color:Color, x:float, y:float, size:float = 5.0):
        self.name = name
        self.color = color
        self.x = x
        self.y = y
        self.size = size

    def draw(self):
        print(f"Drawing {self.name} with color {self.color}")

        
class Marker:
    def __init__(self, x, y, color):
        self.name:str = "Marker"
        self.x:float = x
        self.y:float = y
        self.color:Color = color
        self.accent_color:Color = Color(255, 255, 255, 255)
        self.size:float = 10
        
    def draw(self):
        pass

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
    def _draw_triangle(agent_id, color, radius=10.0):
        agent_x, agent_y = Agent.GetXY(agent_id)  
        center_x, center_y = Overlay.GamePosToScreen(agent_x, agent_y)

        # Starting angle offset to have one tip facing upward (optional)
        base_angle = -math.pi / 2  # 90° upward

        # Generate 3 points spaced 120° apart
        points = []
        for i in range(3):
            angle = base_angle + i * (2 * math.pi / 3)  # 0°, 120°, 240°
            x = center_x + math.cos(angle) * radius
            y = center_y + math.sin(angle) * radius
            points.append((x, y))

        Overlay().DrawTriangleFilled(
            points[0][0], points[0][1],
            points[1][0], points[1][1],
            points[2][0], points[2][1],
            color
        )
        
        black = Utils.RGBToColor(0, 0, 0, 150)
        
        Overlay().DrawTriangle(
            points[0][0], points[0][1],
            points[1][0], points[1][1],
            points[2][0], points[2][1],
            black,
            thickness=1.0
        )
     

    #mission map oeverlay
    
    Overlay().BeginDraw("MissionMapOverlay", mission_map.left, mission_map.top, mission_map.width, mission_map.height)
    #Aggro Bubble
    Overlay().DrawPoly      (mission_map.player_screen_x, mission_map.player_screen_y, radius=Utils.GwinchToPixels(Range.Earshot.value), color=Utils.RGBToColor(255, 255, 255, 40),numsegments=32,thickness=4.0)
    Overlay().DrawPolyFilled(mission_map.player_screen_x, mission_map.player_screen_y, radius=Utils.GwinchToPixels(Range.Earshot.value), color=Utils.RGBToColor(255, 255, 255, 40),numsegments=32)
    #Compass Range
    Overlay().DrawPoly      (mission_map.player_screen_x, mission_map.player_screen_y, radius=Utils.GwinchToPixels(Range.Compass.value), color=Utils.RGBToColor(0, 0, 0, 255),numsegments=360,thickness=1.0)
    Overlay().DrawPoly      (mission_map.player_screen_x, mission_map.player_screen_y, radius=Utils.GwinchToPixels(Range.Compass.value)-10, color=Utils.RGBToColor(255, 255, 255, 40),numsegments=360,thickness=20.0)
    #Overlay().DrawPolyFilled(mission_map.player_screen_x, mission_map.player_screen_y, radius=Utils.GwinchToPixels(Range.Compass.value), color=Utils.RGBToColor(255, 255, 255, 40),numsegments=32)
    
    
    agent_array = AgentArray.GetNPCMinipetArray()
    for agent_id in agent_array:
        _draw_triangle(agent_id,Utils.RGBToColor(170, 255, 0, 255),triangle_size)
       
    """
    agent_array = AgentArray.GetEnemyArray()
    for agent_id in agent_array:
        agent_x, agent_y = Agent.GetXY(agent_id)
        agent_screen_x, agent_screen_y = Overlay.GamePosToScreen(agent_x, agent_y)
        _draw_triangle(agent_id,agent_screen_x, agent_screen_y, Utils.RGBToColor(255, 75, 0, 255),triangle_size)
        """
    Overlay().EndDraw()
    
    
    #world overlay
    """
    Overlay().BeginDraw()   
    player_x, player_y, player_z = Agent.GetXYZ(Player.GetAgentID()) 
    segments = 32
    #Overlay().DrawPoly3D(player_x, player_y, player_z, radius=72, color=0xFF1E90FF,numsegments=segments,thickness=5.0)
    #Overlay().DrawPoly3D(player_x, player_y, player_z, radius=Range.Touch.value, color=0xAB5A1EFF,numsegments=segments,thickness=5.0)
    #Overlay().DrawPoly3D(player_x, player_y, player_z, radius=Range.Adjacent.value, color=0x3BC154FF,numsegments=segments,thickness=5.0)
    #Overlay().DrawPoly3D(player_x, player_y, player_z, radius=Range.Nearby.value, color=0xE39626FF,numsegments=segments,thickness=5.0)
    #Overlay().DrawPoly3D(player_x, player_y, player_z, radius=Range.Area.value, color=0xE3357EFF,numsegments=segments,thickness=5.0)
    Overlay().DrawPoly3D(player_x, player_y, player_z, radius=Range.Earshot.value, color=0xE3357EFF,numsegments=segments,thickness=5.0)
                    
    Overlay().EndDraw()
    """

angle = -180
triangle_size = 5
def DrawWindow():
    global draw_frame
    global mission_map, draw_color, angle, triangle_size
    global MODULE_NAME
    
    if PyImGui.begin(MODULE_NAME):
        # Global
        angle = PyImGui.slider_float("angle", angle, -360.0,360.0)
        triangle_size = PyImGui.slider_int("triangle_size", triangle_size, 0,30)
        
        PyImGui.text(f"zoom: {mission_map.zoom}")
        PyImGui.text(f"scale_x: {mission_map.scale_x}")
        PyImGui.text(f"scale_y: {mission_map.scale_y}")

        
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
