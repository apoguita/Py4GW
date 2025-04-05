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

        Overlay().DrawTriangleFilled(
            points[0][0], points[0][1],
            points[1][0], points[1][1],
            points[2][0], points[2][1],
            self.color.value()
        )
        # Draw the triangle outline     
        Overlay().DrawTriangle(
            points[0][0], points[0][1],
            points[1][0], points[1][1],
            points[2][0], points[2][1],
            self.accent_color.value(),
            thickness=1.0
        )
 
class Circle(Shape):
    def __init__(self, x: float, y: float, color: Color, size: float = 5.0, segments: int = 32):
        self.segments: int = segments
        self.accent_color: Color = Color(1, 1, 1, 255)
        super().__init__("Circle", color, x, y, size)

    def draw(self) -> None:
        Overlay().DrawPolyFilled(
            self.x,
            self.y,
            radius=self.size,
            color=self.color.value(),
            numsegments=32
        )
        Overlay().DrawPoly(
            self.x,
            self.y,
            radius=self.size,
            color=self.accent_color.value(),
            numsegments=32,
            thickness=1.0
        )
        
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
        overlay.DrawQuadFilled(x1, y1, x2, y2, x3, y3, x4, y4, color=self.color.value())
        overlay.DrawQuad(x1, y1, x2, y2, x3, y3, x4, y4, color=self.accent_color.value(), thickness=1.0)

        
        
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
        x, y = Overlay.GamePosToScreen(x, y)
        super().__init__(shape_type=shape_type, color=color, x=x, y=y, size=size, **kwargs)


        
class MissionMap:
    def __init__(self):
        self.left = 0
        self.top = 0
        self.right = 0
        self.bottom = 0
        self.width = 0
        self.height = 0

        self.player_screen_x, self.player_screen_y = 0, 0
        self.update()
        
    def update(self):
        coords = Map.MissionMap.GetWindowCoords()
        self.left, self.top, self.right, self.bottom = int(coords[0]-5), int(coords[1]-1), int(coords[2]+5), int(coords[3]+2)
        self.width = self.right - self.left
        self.height = self.bottom - self.top

        player_x, player_y = Player.GetXY()
        self.player_screen_x, self.player_screen_y = Overlay.GamePosToScreen(player_x, player_y)
        
mission_map = MissionMap()

draw_frame = False
draw_color = Utils.RGBToColor(255, 255, 255, 125)

def DrawFrame():
    global mission_map
    Overlay().BeginDraw("MissionMapOverlay", mission_map.left, mission_map.top, mission_map.width, mission_map.height)
    #Aggro Bubble
    Overlay().DrawPoly      (mission_map.player_screen_x, mission_map.player_screen_y, radius=Utils.GwinchToPixels(Range.Earshot.value)-2, color=Utils.RGBToColor(255, 255, 255, 40),numsegments=32,thickness=4.0)
    Overlay().DrawPolyFilled(mission_map.player_screen_x, mission_map.player_screen_y, radius=Utils.GwinchToPixels(Range.Earshot.value), color=Utils.RGBToColor(255, 255, 255, 40),numsegments=32)
    #Compass Range
    Overlay().DrawPoly      (mission_map.player_screen_x, mission_map.player_screen_y, radius=Utils.GwinchToPixels(Range.Compass.value), color=Utils.RGBToColor(0, 0, 0, 255),numsegments=360,thickness=1.0)
    Overlay().DrawPoly      (mission_map.player_screen_x, mission_map.player_screen_y, radius=Utils.GwinchToPixels(Range.Compass.value)-10, color=Utils.RGBToColor(255, 255, 255, 40),numsegments=360,thickness=20.0)
    
    agent_array = AgentArray.GetNPCMinipetArray()
    for agent_id in agent_array:
        AgentMarker("Triangle", agent_id, Color(170,255,0,255), size=6.0).draw()
        
    enemy_array = AgentArray.GetEnemyArray()
    for agent_id in enemy_array:
        AgentMarker("Square", agent_id, Color(255,0,0,255), size=6.0).draw()

    Overlay().EndDraw()
    

def DrawWindow():
    global MODULE_NAME
    
    if PyImGui.begin(MODULE_NAME):
        # Global
        pass   
    PyImGui.end()
        
def main():   
    if not Routines.Checks.Map.MapValid(): 
        return
    
    mission_map.update()
    if Map.MissionMap.IsWindowOpen():
        DrawFrame()
           
    #DrawWindow()

if __name__ == "__main__":
    main()
