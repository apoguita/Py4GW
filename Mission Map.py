from Py4GWCoreLib import *
from typing import Optional, Union
import math

MODULE_NAME = "Mission Map"

def FloatingSlider(caption, value,x,y,min_value, max_value, color:Color):
    width=20
    height=25
    # Set the position and size of the floating button
    PyImGui.set_next_window_pos(x, y)
    PyImGui.set_next_window_size(0, height)
    

    flags=( PyImGui.WindowFlags.NoCollapse | 
        PyImGui.WindowFlags.NoTitleBar |
        PyImGui.WindowFlags.NoScrollbar |
        PyImGui.WindowFlags.AlwaysAutoResize  ) 
    
    PyImGui.push_style_var2(ImGui.ImGuiStyleVar.WindowPadding,0.0,0.0)
    PyImGui.push_style_var(ImGui.ImGuiStyleVar.WindowRounding,0.0)
    PyImGui.push_style_color(PyImGui.ImGuiCol.Border, color.to_tuple())
       
    result = value
    if PyImGui.begin(f"##invisible_window{caption}", flags):
        PyImGui.push_style_color(PyImGui.ImGuiCol.SliderGrab, (0.7, 0.7, 0.7, 1.0))  # Slider grab color
        PyImGui.push_style_color(PyImGui.ImGuiCol.SliderGrabActive, (0.9, 0.9, 0.9, 1.0))

        result = PyImGui.slider_float(f"##floating_slider{caption}", value, min_value, max_value)
        ImGui.show_tooltip(f"Enhance the zoom level of the map.")
        PyImGui.pop_style_color(2)
    PyImGui.end()
    PyImGui.pop_style_var(2)
    PyImGui.pop_style_color(1)
    return result

class Shape:
    def __init__(self, name: str, color: Color, x: float, y: float, size: float = 5.0):
        self.name: str = name
        self.color: Color = color
        self.accent_color:Color = self.color
        self.x: float = x
        self.y: float = y
        self.size: float = size
        self.scale: float = 1.0
        self.angle: float = 0.0

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
            self.color.to_color()
        )
        # Draw the triangle outline     
        Overlay().DrawTriangle(
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
        zoom_offset: float = 0.0,
        **kwargs 
    ):
        self.agent_id = agent_id
        x, y = Agent.GetXY(agent_id)
        x, y = Map.MissionMap.MapProjection.GamePosToScreen(x, y, zoom_offset)
        super().__init__(shape_type=shape_type, color=color, x=x, y=y, size=size, **kwargs)

class MapBoundaries:
    def __init__(self, x_min, x_max, y_min, y_max, unk):
        self.x_min = x_min
        self.x_max = x_max
        self.y_min = y_min
        self.y_max = y_max
        self.unk = unk

         


def RawGamePosToScreen(x:float, y:float, zoom:float, zoom_offset:float, left_bound:float, top_bound:float, boundaries:list[float],
                       pan_offset_x:float, pan_offset_y:float, scale_x:float, scale_y:float,
                       mission_map_screen_center_x:float, mission_map_screen_center_y:float) -> tuple[float, float]:

    gwinches = 96.0

    if len(boundaries) < 5:
        return 0.0, 0.0  # fail-safe

    min_x = boundaries[1]
    max_y = boundaries[4]

    # Step 3: Compute origin on the world map based on boundary distances
    origin_x = left_bound + abs(min_x) / gwinches
    origin_y = top_bound + abs(max_y) / gwinches

    # Step 4: Convert game-space (gwinches) to world map space (screen)
    screen_x = (x / gwinches) + origin_x
    screen_y = (-y / gwinches) + origin_y  # Inverted Y

    offset_x = screen_x - pan_offset_x
    offset_y = screen_y - pan_offset_y

    scaled_x = offset_x * scale_x
    scaled_y = offset_y * scale_y

    zoom_total = zoom + zoom_offset

    screen_x = scaled_x * zoom_total + mission_map_screen_center_x
    screen_y = scaled_y * zoom_total + mission_map_screen_center_y

    return screen_x, screen_y
            


class MissionMap:
    def __init__(self):
        self.left = 0
        self.top = 0
        self.right = 0
        self.bottom = 0
        self.width = 0
        self.height = 0

        self.player_screen_x, self.player_screen_y = 0, 0
        
        self.zoom = 0.0
        
        self.last_click_x = 0
        self.last_click_y = 0
        
        self.boundaries = []
        self.geometry = []
        self.renderer = DXOverlay()
        self.mega_zoom_renderer = DXOverlay()
        self.mega_zoom = 0.0
        self.map_origin = Map.MissionMap.MapProjection.GameMapToScreen(0.0,0.0,self.mega_zoom)
        self.left_bound, self.top_bound, self.right_bound, self.bottom_bound = 0.0, 0.0, 0.0, 0.0
        
        self.pan_offset_x, self.pan_offset_y = 0.0, 0.0
        self.scale_x, self.scale_y = Map.MissionMap.GetScale()
        self.zoom =  0.0
        self.mission_map_screen_center_x, self.mission_map_screen_center_y = 0.0, 0.0
        
        

        self.update()
                   

    def update(self):
        coords = Map.MissionMap.GetWindowCoords()
        self.left, self.top, self.right, self.bottom = int(coords[0]), int(coords[1]), int(coords[2]), int(coords[3])
        self.width = self.right - self.left
        self.height = self.bottom - self.top
        
        self.pan_offset_x, self.pan_offset_y = Map.MissionMap.GetPanOffset()
        self.scale_x, self.scale_y = Map.MissionMap.GetScale()
        self.zoom = Map.MissionMap.GetZoom()
        self.mission_map_screen_center_x, self.mission_map_screen_center_y = Map.MissionMap.GetMapScreenCenter()
        
        self.left_world, self.top_world = Map.MissionMap.MapProjection.ScreenToGamePos(self.left, self.top, self.mega_zoom)
        self.right_world, self.bottom_world = Map.MissionMap.MapProjection.ScreenToGamePos(self.right, self.bottom, self.mega_zoom)

        self.player_x, self.player_y = Player.GetXY()
        self.player_screen_x, self.player_screen_y = RawGamePosToScreen(self.player_x, self.player_y, 
                                                    self.zoom, self.mega_zoom,
                                                    self.left_bound, self.top_bound, self.boundaries,
                                                    self.pan_offset_x, self.pan_offset_y, self.scale_x, self.scale_y,
                                                    self.mission_map_screen_center_x, self.mission_map_screen_center_y)
        
        click_x, click_y = Map.MissionMap.GetLastClickCoords()

        self.last_click_x, self.last_click_y = Map.MissionMap.MapProjection.ScreenToGamePos(click_x, click_y, self.mega_zoom)
        
        if not self.geometry:
            self.boundaries = Map.map_instance().map_boundaries
            self.left_bound, self.top_bound, self.right_bound, self.bottom_bound = Map.GetMapWorldMapBounds()
            
            self.geometry = Map.Pathing.GetComputedGeometry()
            self.renderer.set_primitives(self.geometry, Color(155, 155, 155, 125).to_dx_color())
            self.mega_zoom_renderer.set_primitives(self.geometry, Color(155, 155, 155, 255).to_dx_color())

        self.renderer.world_space.set_world_space(True)
        self.mega_zoom_renderer.world_space.set_world_space(True)
        self.renderer.mask.set_rectangle_mask(True)
        self.mega_zoom_renderer.mask.set_rectangle_mask(True)
        self.renderer.mask.set_rectangle_mask_bounds(self.left, self.top, self.width, self.height)
        self.mega_zoom_renderer.mask.set_rectangle_mask_bounds(self.left, self.top, self.width, self.height)
        self.renderer.world_space.set_pan(self.map_origin[0], self.map_origin[1])
        self.mega_zoom_renderer.world_space.set_pan(self.map_origin[0], self.map_origin[1])
        zoom = Map.MissionMap.GetAdjustedZoom(zoom_offset=self.mega_zoom)
        self.renderer.world_space.set_zoom(zoom/100.0)
        self.mega_zoom_renderer.world_space.set_zoom(zoom/100.0)
        self.map_origin = Map.MissionMap.MapProjection.GameMapToScreen(0.0,0.0,self.mega_zoom)
        
        
mission_map = MissionMap()

def RawGwinchToPixels(gwinch_value: float, zoom:float, zoom_offset:float, scale_x) -> float:
        gwinches = 96.0  # hardcoded GW unit scale
        pixels_per_gwinch = (scale_x * (zoom + zoom_offset)) / gwinches
        return gwinch_value * pixels_per_gwinch

def DrawFrame():
    global mission_map
    Overlay().BeginDraw("MissionMapOverlay", mission_map.left, mission_map.top, mission_map.width, mission_map.height)
    #terrain 
    zoom = mission_map.zoom + mission_map.mega_zoom
    if zoom >3.5:
        mission_map.mega_zoom_renderer.DrawQuadFilled(mission_map.left,mission_map.top, mission_map.right,mission_map.top, mission_map.right,mission_map.bottom, mission_map.left,mission_map.bottom, color=Utils.RGBToColor(75,75,75,200))
        
        mission_map.mega_zoom_renderer.render()
    else:
        mission_map.renderer.render()
    #Aggro Bubble
    Overlay().DrawPoly      (mission_map.player_screen_x, mission_map.player_screen_y, radius=RawGwinchToPixels(Range.Earshot.value,mission_map.zoom, mission_map.mega_zoom, mission_map.scale_x)-2, color=Utils.RGBToColor(255, 255, 255, 40),numsegments=32,thickness=4.0)
    Overlay().DrawPolyFilled(mission_map.player_screen_x, mission_map.player_screen_y, radius=RawGwinchToPixels(Range.Earshot.value,mission_map.zoom, mission_map.mega_zoom, mission_map.scale_x), color=Utils.RGBToColor(255, 255, 255, 40),numsegments=32)
    #Compass Range
    Overlay().DrawPoly      (mission_map.player_screen_x, mission_map.player_screen_y, radius=RawGwinchToPixels(Range.Earshot.value,mission_map.zoom, mission_map.mega_zoom, mission_map.scale_x), color=Utils.RGBToColor(0, 0, 0, 255),numsegments=360,thickness=1.0)
    zoom = mission_map.zoom + mission_map.mega_zoom
    Overlay().DrawPoly      (mission_map.player_screen_x, mission_map.player_screen_y, radius=RawGwinchToPixels(Range.Earshot.value,mission_map.zoom, mission_map.mega_zoom, mission_map.scale_x)-(2.85*zoom), color=Utils.RGBToColor(255, 255, 255, 40),numsegments=360,thickness=(5.7*zoom))
         
    agent_array = AgentArray.GetAgentArray()
    for agent_id in agent_array:
        agent = Agent.agent_instance(agent_id)
        alliegance = agent.living_agent.allegiance.ToInt()
        x,y = RawGamePosToScreen(agent.x, agent.y, 
                                 mission_map.zoom, mission_map.mega_zoom,
                                 mission_map.left_bound, mission_map.top_bound,
                                 mission_map.boundaries, 
                                 mission_map.pan_offset_x, mission_map.pan_offset_y,
                                 mission_map.scale_x, mission_map.scale_y,
                                 mission_map.mission_map_screen_center_x, mission_map.mission_map_screen_center_y)
    
        if alliegance == Allegiance.NpcMinipet:
            Marker("Triangle", Color(170,255,0,255),x,y, size=6.0).draw()
        elif alliegance == Allegiance.Enemy:
            Marker("Circle", Color(255,0,0,255),x,y, size=4.0, segments=16).draw()
        elif alliegance == Allegiance.Ally:
            Marker("Circle", Color(100,138,217,255),x,y, size=4.0, segments=16).draw()
        else:
            Marker("Circle", Color(70,70,70,255),x,y, size=4.0, segments=16).draw()
    
    Overlay().EndDraw()

 
   
def main():  
    if not Routines.Checks.Map.MapValid():
        mission_map.geometry = [] 
        return
    
    if not Map.MissionMap.IsWindowOpen():
        return
    
    mission_map.update()
    DrawFrame()       
    
    if mission_map.zoom >= 3.5:
            mission_map.mega_zoom = FloatingSlider("Mega Zoom", mission_map.mega_zoom, mission_map.left, mission_map.bottom-27, 0.0, 10.0, Color(255, 255, 255, 255))
    else:
        mission_map.mega_zoom = 0.0 
    
    
if __name__ == "__main__":
    main()
