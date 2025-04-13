from Py4GWCoreLib import *
from typing import Optional, Union
import math

MODULE_NAME = "Mission Map"

class Shape:
    def __init__(self, name: str, color: Color, x: float, y: float, size: float = 5.0):
        self.name: str = name
        self.color: Color = color
        self.accent_color:Color = self.color
        self.x: float = x
        self.y: float = y
        self.size: float = size

    def draw(self) -> None:
        print(f"Drawing {self.name} at ({self.x}, {self.y}) with size {self.size} and color {self.color}")

    def __repr__(self) -> str:
        return f"Shape(name={self.name}, color={self.color}, x={self.x}, y={self.y}, size={self.size})"

class Triangle(Shape):
    def __init__(self, x: float, y: float, color: Color, size: float = 5.0, offset_angle: float = 0.0):
        super().__init__("Triangle", color, x, y, size)
        self.accent_color: Color = Color(0, 0, 0, 150)
        self.offset_angle: float = offset_angle

    def draw(self) -> None:
        base_angle = (-math.pi / 2) # + Utils.DegToRad(self.offset_angle)
        # Generate 3 points spaced 120° apart
        points = []
        for i in range(3):
            angle = base_angle + i * (2 * math.pi / 3)  # 0°, 120°, 240°
            x = self.x + math.cos(angle) * self.size
            y = self.y + math.sin(angle) * self.size
            points.append((x, y))

        DXOverlay().DrawTriangleFilled(
            points[0][0], points[0][1],
            points[1][0], points[1][1],
            points[2][0], points[2][1],
            self.color.to_color()
        )
        # Draw the triangle outline     
        DXOverlay().DrawTriangle(
            points[0][0], points[0][1],
            points[1][0], points[1][1],
            points[2][0], points[2][1],
            self.accent_color.to_color(),
            thickness=1.0
        )
 
class Circle(Shape):
    def __init__(self, x: float, y: float, color: Color, size: float = 5.0, segments: int = 32):
        self.segments: int = segments
        super().__init__("Circle", color, x, y, size)
        self.accent_color: Color = Color(0, 0, 0, 255)

    def draw(self) -> None:
        Overlay().DrawPolyFilled(self.x, self.y, radius=self.size, color=self.color.to_color(), numsegments=self.segments)
        Overlay().DrawPoly(self.x, self.y, radius=self.size, color=self.accent_color.to_color(), numsegments=self.segments, thickness=1.0)
        
class Square(Shape):
    def __init__(self, x: float, y: float, color: Color, size: float = 5.0):
        super().__init__("Square", color, x, y, size)
        self.accent_color: Color = Color(0, 0, 0, 255)

    def draw(self) -> None:
        # Inscribed square inside a circle of radius = self.size
        half_side = (self.size * math.sqrt(2)) / 2

        # Corner coordinates
        x1, y1 = self.x - half_side, self.y - half_side  # top-left
        x2, y2 = self.x + half_side, self.y - half_side  # top-right
        x3, y3 = self.x + half_side, self.y + half_side  # bottom-right
        x4, y4 = self.x - half_side, self.y + half_side  # bottom-left

        overlay = Overlay()
        overlay.DrawQuadFilled(x1, y1, x2, y2, x3, y3, x4, y4, color=self.color.to_color())
        overlay.DrawQuad(x1, y1, x2, y2, x3, y3, x4, y4, color=self.accent_color.to_color(), thickness=1.0)

        
        
shapes: dict[str, type[Shape]] = {
    "Triangle": Triangle,
    "Circle": Circle,
    "Square": Square,
}
       
class Marker:
    def __init__(
        self,
        shape_type: Union[str, Shape],
        color: Color = Color(255, 255, 255, 255),
        x:float = 0.0,
        y:float = 0.0,
        size: float = 5.0,
        **kwargs
    ):
        self.color: Color = color
        self.x = x
        self.y = y
        self.size = size

        # Build the shape
        if isinstance(shape_type, Shape):
            self.shape: Shape = shape_type
            self.shape.x = x
            self.shape.y = y
        else:
            shape_cls = shapes.get(shape_type)
            if shape_cls is None:
                raise ValueError(f"Unknown shape type: {shape_type}")
            self.shape = shape_cls(x=x, y=y, color=color, size=size, **kwargs)

    def draw(self) -> None:
        self.shape.draw()
        
class AgentMarker(Marker):
    def __init__(
        self,
        shape_type: Union[str, Shape],
        agent_id: int,
        color: Color = Color(255, 255, 255, 255),
        size: float = 5.0,
        **kwargs 
    ):
        self.agent_id = agent_id
        x, y = Agent.GetXY(agent_id)
        x, y = Map.MissionMap.MapProjection.GamePosToScreen(x, y)
        super().__init__(shape_type=shape_type, color=color, x=x, y=y, size=size, **kwargs)

class MapBoundaries:
    def __init__(self, x_min, x_max, y_min, y_max, unk):
        self.x_min = x_min
        self.x_max = x_max
        self.y_min = y_min
        self.y_max = y_max
        self.unk = unk



class MissionMap:
    def __init__(self):
        self.left = 0
        self.top = 0
        self.right = 0
        self.bottom = 0
        self.width = 0
        self.height = 0

        self.player_screen_x, self.player_screen_y = 0, 0
        self.precomputed_geometry = {}
        self.pathing_map = []
        self.map_boundaries: MapBoundaries
        self.map_boundaries_vector : List[float] = []
        self.thread_manager = MultiThreading(log_actions=True)
        
        self.last_click_x = 0
        self.last_click_y = 0
        self.geometry = []
        self.renderer = DXOverlay()
        self.map_origin = Map.MissionMap.MapProjection.GameMapToScreen(0.0,0.0)

        self.update()
                   

    def update(self):
        coords = Map.MissionMap.GetWindowCoords()
        self.left, self.top, self.right, self.bottom = int(coords[0]), int(coords[1]), int(coords[2]), int(coords[3])
        self.width = self.right - self.left
        self.height = self.bottom - self.top
        
        self.left_world, self.top_world = Map.MissionMap.MapProjection.ScreenToGamePos(self.left, self.top)
        self.right_world, self.bottom_world = Map.MissionMap.MapProjection.ScreenToGamePos(self.right, self.bottom)

        self.player_x, self.player_y = Player.GetXY()
        self.player_screen_x, self.player_screen_y = Map.MissionMap.MapProjection.GamePosToScreen(self.player_x, self.player_y)
        
        click_x, click_y = Map.MissionMap.GetLastClickCoords()

        self.last_click_x, self.last_click_y = Map.MissionMap.MapProjection.ScreenToGamePos(click_x, click_y)
        
        if not self.geometry:
            self.geometry = Map.Pathing.GetComputedGeometry()
            
            #self.geometry = [[PyOverlay.Point2D(100,100),PyOverlay.Point2D(200,100),PyOverlay.Point2D(100,200),PyOverlay.Point2D(200,200)],]
            self.renderer.set_primitives(self.geometry, Color(255, 255, 255, 125).to_color())
            self.renderer.world_space.set_zoom(0.03)
            self.map_origin = Map.MissionMap.MapProjection.GameMapToScreen(0.0,0.0)
            #self.renderer.world_space.set_pan(self.map_origin[0], self.map_origin[1])
        self.renderer.world_space.set_world_space(True)
        self.renderer.mask.set_rectangle_mask(True)
        self.renderer.mask.set_rectangle_mask_bounds(self.left, self.top, self.width, self.height)
        self.renderer.world_space.set_pan(self.map_origin[0], self.map_origin[1])
        zoom = Map.MissionMap.GetAdjustedZoom()
        self.renderer.world_space.set_zoom(zoom/100.0)
        
      

            


mission_map = MissionMap()


def DrawFrame():
    global mission_map
    Overlay().BeginDraw("MissionMapOverlay", mission_map.left, mission_map.top, mission_map.width, mission_map.height)
    #terrain 
    mission_map.map_origin = Map.MissionMap.MapProjection.GameMapToScreen(0.0,0.0)
    #Overlay().DrawPolyFilled(mission_map.map_origin[0], mission_map.map_origin[1], radius=100, color=Utils.RGBToColor(0, 255, 0, 255), numsegments=32)
    mission_map.renderer.render()
    #Aggro Bubble
    Overlay().DrawPoly      (mission_map.player_screen_x, mission_map.player_screen_y, radius=Utils.GwinchToPixels(Range.Earshot.value)-2, color=Utils.RGBToColor(255, 255, 255, 40),numsegments=32,thickness=4.0)
    Overlay().DrawPolyFilled(mission_map.player_screen_x, mission_map.player_screen_y, radius=Utils.GwinchToPixels(Range.Earshot.value), color=Utils.RGBToColor(255, 255, 255, 40),numsegments=32)
    #Compass Range
    Overlay().DrawPoly      (mission_map.player_screen_x, mission_map.player_screen_y, radius=Utils.GwinchToPixels(Range.Compass.value), color=Utils.RGBToColor(0, 0, 0, 255),numsegments=360,thickness=1.0)
    Overlay().DrawPoly      (mission_map.player_screen_x, mission_map.player_screen_y, radius=Utils.GwinchToPixels(Range.Compass.value)-(2.85*Map.MissionMap.GetZoom()), color=Utils.RGBToColor(255, 255, 255, 40),numsegments=360,thickness=(5.7*Map.MissionMap.GetZoom()))
        
    agent_array = AgentArray.GetNPCMinipetArray()
    for agent_id in agent_array:
        AgentMarker("Triangle", agent_id, Color(170,255,0,255), size=6.0).draw()
        
    enemy_array = AgentArray.GetEnemyArray()
    for agent_id in enemy_array:
        #AgentMarker("Square", agent_id, Color(255,0,0,255), size=6.0).draw()
        AgentMarker("Circle", agent_id, Color(255,0,0,255), size=4.0, segments=16).draw()

    Overlay().EndDraw()

    
    """
    Overlay().BeginDraw()
    player_x, player_y = Player.GetXY()
    z_coords = Overlay.FindZ(player_x, player_y)
    Overlay().DrawPolyFilled3D(player_x, player_y, z_coords, color=Color(0, 255, 0, 255).value(), radius=100)
   
    Overlay().EndDraw()
    """





zoom = 35
zoom_offset = 0.0
pan_x = 800.0
pan_y = 800.0

screen_offset_x = 0.0
screen_offset_y = 0.0
angle = 0.0



def DrawWindow():
    global MODULE_NAME, mission_map, pan_x, pan_y, zoom, screen_offset_x, screen_offset_y, angle, zoom_offset
    
    if PyImGui.begin(MODULE_NAME):
        
        mouse_x, mouse_y = Overlay().GetMouseCoords()
        world_mouse_x, world_mouse_y = Map.MissionMap.MapProjection.ScreenToGamePos(mouse_x, mouse_y)
        PyImGui.text(f"Mouse Coords: {mouse_x:.2f}, {mouse_y:.2f}")
        PyImGui.text(f"World Mouse Coords: {world_mouse_x:.2f}, {world_mouse_y:.2f}")
        PyImGui.text(f"Mission Map: {mission_map.left:.2f}, {mission_map.top:.2f}, {mission_map.right:.2f}, {mission_map.bottom:.2f}")
        PyImGui.text(f"World Coords: {mission_map.left_world:.2f}, {mission_map.top_world:.2f}, {mission_map.right_world:.2f}, {mission_map.bottom_world:.2f}")
        
        PyImGui.separator()
        player_x, player_y = Player.GetXY()
        player_screen_x, player_screen_y = Map.MissionMap.MapProjection.GamePosToScreen(player_x, player_y)
        PyImGui.text(f"Player Screen Coords: {player_screen_x:.2f}, {player_screen_y:.2f}")
        PyImGui.text(f"Player Coords: {player_x:.2f}, {player_y:.2f}")
        
        PyImGui.separator()
        PyImGui.text(f"Mission Map Zoom: {Map.MissionMap.GetZoom()}")
        
        
    PyImGui.end()
        
def main():   
    if not Routines.Checks.Map.MapValid(): 
        return
    
    if not Map.MissionMap.IsWindowOpen():
        return
    
    mission_map.update()
    DrawFrame()       
    DrawWindow()

if __name__ == "__main__":
    main()
