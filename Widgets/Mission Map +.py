from Py4GWCoreLib import *
from typing import ClassVar, Union
import math

from dataclasses import dataclass

#region CONSTANTS
MODULE_NAME = "Mission Map"
MATH_PI = math.pi
BASE_ANGLE = (-MATH_PI / 2)
SQRT_2 = math.sqrt(2)
GWINCHES = 96.0
POLY_SEGMENTS = 16

#end region

#region ENUMS
class SpiritBuff:
    def __init__ (self, spirit_name:str, model_id: int, skill_id: int, color: Color = Color(96, 128, 0, 255)):
        self.spirit_name = spirit_name
        self.model_id = model_id
        self.skill_id = skill_id
        self.color = color
        
    def __repr__(self):
        return f"SpiritBuff(model_id={self.model_id}, skill_id={self.skill_id}, color={self.color})"

RANGER_SPIRIT_COLOR = Color(r=204, g=255, b=153, a=255)
RITUALIST_SPIRIT_COLOR = Color(r=187, g=255, b=255, a=255)
EBON_VANGUARD_COLOR = Color(r=66, g=3, b=1, a=255)
SPIRIT_BUFFS = [
    SpiritBuff("Frozen Soil", 2882, Skill.GetID("Frozen_Soil"), RANGER_SPIRIT_COLOR),
    SpiritBuff("Life", 4218, Skill.GetID("Life"), RITUALIST_SPIRIT_COLOR),
    SpiritBuff("Bloodsong", 4227, Skill.GetID("Bloodsong"), RITUALIST_SPIRIT_COLOR),
    SpiritBuff("Anger", 4229, Skill.GetID("Signet_of_Spirits"), RITUALIST_SPIRIT_COLOR),
    SpiritBuff("Hate", 4230, Skill.GetID("Signet_of_Spirits"), RITUALIST_SPIRIT_COLOR),
    SpiritBuff("Suffering", 4231, Skill.GetID("Signet_of_Spirits"), RITUALIST_SPIRIT_COLOR),
    SpiritBuff("Anguish", 5720, Skill.GetID("Anguish"), RITUALIST_SPIRIT_COLOR),
    SpiritBuff("Disenchantment", 4225, Skill.GetID("Disenchantment"), RITUALIST_SPIRIT_COLOR),
    SpiritBuff("Dissonance", 4221, Skill.GetID("Dissonance"), RITUALIST_SPIRIT_COLOR),
    SpiritBuff("Pain", 4214, Skill.GetID("Pain"), RITUALIST_SPIRIT_COLOR),
    SpiritBuff("Shadowsong", 4213, Skill.GetID("Shadowsong"), RITUALIST_SPIRIT_COLOR),
    SpiritBuff("Wanderlust", 4228, Skill.GetID("Wanderlust"), RITUALIST_SPIRIT_COLOR),
    SpiritBuff("Vampirism", 5723, Skill.GetID("Vampirism"), EBON_VANGUARD_COLOR),
    SpiritBuff("Agony", 5854, Skill.GetID("Agony"), RITUALIST_SPIRIT_COLOR),
    SpiritBuff("Displacement", 4217, Skill.GetID("Displacement"), RITUALIST_SPIRIT_COLOR),
    SpiritBuff("Earthbind", 4222, Skill.GetID("Earthbind"), RITUALIST_SPIRIT_COLOR),
    SpiritBuff("Empowerment", 5721, Skill.GetID("Empowerment"), RITUALIST_SPIRIT_COLOR),
    SpiritBuff("Preservation", 4219, Skill.GetID("Preservation"), RITUALIST_SPIRIT_COLOR),
    SpiritBuff("Recovery", 5719, Skill.GetID("Recovery"), RITUALIST_SPIRIT_COLOR),
    SpiritBuff("Recuperation", 4220, Skill.GetID("Recuperation"), RITUALIST_SPIRIT_COLOR),
    SpiritBuff("Rejuvenation", 5853, Skill.GetID("Rejuvenation"), RITUALIST_SPIRIT_COLOR),
    SpiritBuff("Shelter", 4223, Skill.GetID("Shelter"), RITUALIST_SPIRIT_COLOR),
    SpiritBuff("Soothing", 4216, Skill.GetID("Soothing"), RITUALIST_SPIRIT_COLOR),
    SpiritBuff("Union", 4224, Skill.GetID("Union"), RITUALIST_SPIRIT_COLOR),
    SpiritBuff("Destruction", 4215, Skill.GetID("Destruction"), RITUALIST_SPIRIT_COLOR),
    SpiritBuff("Restoration", 4226, Skill.GetID("Restoration"), RITUALIST_SPIRIT_COLOR),
    SpiritBuff("Winds", 2884, Skill.GetID("Winds"),EBON_VANGUARD_COLOR),
    SpiritBuff("Brambles", 4239, Skill.GetID("Brambles"), RANGER_SPIRIT_COLOR),
    SpiritBuff("Conflagration", 4237, Skill.GetID("Conflagration"), RANGER_SPIRIT_COLOR),
    SpiritBuff("Energizing Wind", 2885, Skill.GetID("Energizing_Wind"), RANGER_SPIRIT_COLOR),
    SpiritBuff("Equinox", 4236, Skill.GetID("Equinox"), RANGER_SPIRIT_COLOR),
    SpiritBuff("Edge of Extinction", 2876, Skill.GetID("Edge_of_Extinction"), RANGER_SPIRIT_COLOR),
    SpiritBuff("Famine", 4238, Skill.GetID("Famine"), RANGER_SPIRIT_COLOR),
    SpiritBuff("Favorable Winds", 2883, Skill.GetID("Favorable_Winds"), RANGER_SPIRIT_COLOR),
    SpiritBuff("Fertile Season", 2878, Skill.GetID("Fertile_Season"), RANGER_SPIRIT_COLOR),
    SpiritBuff("Greater Conflagration", 2877, Skill.GetID("Greater_Conflagration"), RANGER_SPIRIT_COLOR),
    SpiritBuff("Infuriating Heat", 5715, Skill.GetID("Infuriating_Heat"), RANGER_SPIRIT_COLOR),
    SpiritBuff("Lacerate", 4232, Skill.GetID("Lacerate"), RANGER_SPIRIT_COLOR),
    SpiritBuff("Muddy Terrain", 2888, Skill.GetID("Muddy_Terrain"), RANGER_SPIRIT_COLOR),
    SpiritBuff("Nature's Renewal", 2887, Skill.GetID("Natures_Renewal"), RANGER_SPIRIT_COLOR),
    SpiritBuff("Pestilence", 4234, Skill.GetID("Pestilence"), RANGER_SPIRIT_COLOR),
    SpiritBuff("Predatory Season", 2881, Skill.GetID("Predatory_Season"), RANGER_SPIRIT_COLOR),
    SpiritBuff("Primal Echoes", 2880, Skill.GetID("Primal_Echoes"), RANGER_SPIRIT_COLOR),
    SpiritBuff("Quickening Zephyr", 2886, Skill.GetID("Quickening_Zephyr"), RANGER_SPIRIT_COLOR),
    SpiritBuff("Quicksand", 5718, Skill.GetID("Quicksand"), RANGER_SPIRIT_COLOR),
    SpiritBuff("Roaring Winds", 5717, Skill.GetID("Roaring_Winds"), RANGER_SPIRIT_COLOR),
    SpiritBuff("Symbiosis", 2879, Skill.GetID("Symbiosis"), RANGER_SPIRIT_COLOR),
    SpiritBuff("Toxicity", 5716, Skill.GetID("Toxicity"), RANGER_SPIRIT_COLOR),
    SpiritBuff("Tranquility", 4235, Skill.GetID("Tranquility"), RANGER_SPIRIT_COLOR),
    SpiritBuff("Winter", 2874, Skill.GetID("Winter"), RANGER_SPIRIT_COLOR),
    SpiritBuff("Winnowing", 2875, Skill.GetID("Winnowing"), RANGER_SPIRIT_COLOR),
]

def get_spirit_name(model_id: int) -> str:
    for buff in SPIRIT_BUFFS:
        if buff.model_id == model_id:
            return buff.spirit_name
    return "Unknown"

def get_spirit_buff_color(model_id: int) -> Color:
    for buff in SPIRIT_BUFFS:
        if buff.model_id == model_id:
            return buff.color
    return Color(0, 0, 0, 255) #default color is a minipet

#endregion

#region HELPERS

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

def RawGamePosToScreen(x:float, y:float, zoom:float, zoom_offset:float, left_bound:float, top_bound:float, boundaries:list[float],
                       pan_offset_x:float, pan_offset_y:float, scale_x:float, scale_y:float,
                       mission_map_screen_center_x:float, mission_map_screen_center_y:float) -> tuple[float, float]:

    global GWINCHES

    if len(boundaries) < 5:
        return 0.0, 0.0  # fail-safe

    min_x = boundaries[1]
    max_y = boundaries[4]

    # Step 3: Compute origin on the world map based on boundary distances
    origin_x = left_bound + abs(min_x) / GWINCHES
    origin_y = top_bound + abs(max_y) / GWINCHES

    # Step 4: Convert game-space (gwinches) to world map space (screen)
    screen_x = (x / GWINCHES) + origin_x
    screen_y = (-y / GWINCHES) + origin_y  # Inverted Y

    offset_x = screen_x - pan_offset_x
    offset_y = screen_y - pan_offset_y

    scaled_x = offset_x * scale_x
    scaled_y = offset_y * scale_y

    zoom_total = zoom + zoom_offset

    screen_x = scaled_x * zoom_total + mission_map_screen_center_x
    screen_y = scaled_y * zoom_total + mission_map_screen_center_y

    return screen_x, screen_y

def RawGwinchToPixels(gwinch_value: float, zoom:float, zoom_offset:float, scale_x) -> float:
    global GWINCHES
    pixels_per_gwinch = (scale_x * (zoom + zoom_offset)) / GWINCHES
    return gwinch_value * pixels_per_gwinch

#endregion
#region MARKERS
class Shape:
    def __init__(self, name: str, color: Color,accent_color: Color, x: float, y: float, size: float = 5.0, offset_angle: float = 0.0):
        self.name: str = name
        self.color: Color = color
        self.accent_color:Color = accent_color
        self.x: float = x
        self.y: float = y
        self.size: float = size
        self.base_angle: float = 0.0
        self.offset_angle: float = offset_angle
        

    def draw(self) -> None:
        print(f"Drawing {self.name} at ({self.x}, {self.y}) with size {self.size} and color {self.color}")

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(x={self.x}, y={self.y}, size={self.size}, color={self.color})"

class Triangle(Shape):
    global BASE_ANGLE
    def __init__(self, color: Color, accent_color:Color,x: float, y:float, size: float = 5.0, offset_angle: float = 0.0):
        super().__init__("Triangle", color, accent_color, x, y, size)
        self.accent_color: Color = accent_color
        self.offset_angle: float = offset_angle
        self.base_angle:float = 0.0 # + Utils.DegToRad(self.offset_angle)

    def draw(self) -> None:
        
        # Generate 3 points spaced 120° apart
        points = []
        for i in range(3):
            angle = (self.base_angle + self.offset_angle) + i * (2 * MATH_PI / 3)  # 0°, 120°, 240°
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
            thickness=2.0
        )
 
class Circle(Shape):
    def __init__(self, color: Color,accent_color:Color, x: float, y: float, size: float, segments: int = 16, offset_angle= 0.0):
        self.segments: int = segments
        super().__init__("Circle", color, accent_color, x, y, size, offset_angle)
        self.accent_color: Color = accent_color

    def draw(self) -> None:
        Overlay().DrawPolyFilled(self.x, self.y, radius=self.size, color=self.color.to_color(),numsegments=self.segments)
        Overlay().DrawPoly(self.x, self.y, radius=self.size, color=self.accent_color.to_color(), numsegments=self.segments, thickness=2)
        
class Teardrop(Shape):
    def __init__(self, color: Color,accent_color:Color, x: float, y: float, size: float, offset_angle: float = 0.0, segments: int = 16):
        self.segments: int = segments
        super().__init__("Teardrop", color, accent_color, x, y, size)
        self.accent_color: Color = accent_color
        self.base_angle: float = BASE_ANGLE
        self.offset_angle: float = offset_angle

    def draw(self) -> None:
        # 1. Draw unrotated circle
        Overlay().DrawPolyFilled(self.x, self.y, radius=self.size, color=self.color.to_color(), numsegments=self.segments)
        Overlay().DrawPoly(self.x, self.y, radius=self.size, color=self.accent_color.to_color(), numsegments=self.segments, thickness=2)

        # 2. Build arrow points (relative to center)
        half_side = (self.size * SQRT_2) / 2
        local_points = [
            (0          , -half_side * 2),     # p1 - arrow tip
            (-half_side , -half_side),# p2 - left base
            (half_side  , -half_side), # p4 - right base
        ]

        # 3. Calculate rotation angle (negated for in-game rotation match)
        angle = -(self.base_angle + self.offset_angle)
        cos_a = math.cos(angle)
        sin_a = math.sin(angle)

        # 4. Rotate + translate points
        def rotate(px, py):
            rx = px * cos_a - py * sin_a + self.x
            ry = px * sin_a + py * cos_a + self.y
            return (rx, ry)

        p1 = rotate(*local_points[0])
        p2 = rotate(*local_points[1])
        p4 = rotate(*local_points[2])
        
        # 5. Draw the arrow
        Overlay().DrawTriangleFilled(p1[0], p1[1], p2[0], p2[1], p4[0], p4[1], color=self.color.to_color())
        Overlay().DrawLine(p1[0], p1[1], p2[0], p2[1], color=self.accent_color.to_color(), thickness=2.0)
        Overlay().DrawLine(p1[0], p1[1], p4[0], p4[1], color=self.accent_color.to_color(), thickness=2.0)
     
class Penta(Shape):
    def __init__(self, color: Color,accent_color:Color, x: float, y: float, size: float):
        self.segments: int = 5
        super().__init__("Penta", color, accent_color, x, y, size)
        self.accent_color: Color = accent_color

    def draw(self) -> None:
        Overlay().DrawPolyFilled(self.x, self.y, radius=self.size, color=self.color.to_color(),numsegments=self.segments)
        Overlay().DrawPoly(self.x, self.y, radius=self.size, color=self.accent_color.to_color(), numsegments=self.segments, thickness=2)
        
class Square(Shape):
    def __init__(self, color: Color, accent_color:Color, x: float, y: float, size: float = 5.0):
        super().__init__("Square", color, accent_color, x, y, size)
        self.accent_color: Color = accent_color

    def draw(self) -> None:
        # Inscribed square inside a circle of radius = self.size
        half_side = (self.size * SQRT_2) / 2

        # Corner coordinates
        x1, y1 = self.x - half_side, self.y - half_side  # top-left
        x2, y2 = self.x + half_side, self.y - half_side  # top-right
        x3, y3 = self.x + half_side, self.y + half_side  # bottom-right
        x4, y4 = self.x - half_side, self.y + half_side  # bottom-left

        Overlay().DrawQuadFilled(x1, y1, x2, y2, x3, y3, x4, y4, color=self.color.to_color())
        Overlay().DrawQuad(x1, y1, x2, y2, x3, y3, x4, y4, color=self.accent_color.to_color(), thickness=2.0)

class Tear(Shape):
    def __init__(self, color: Color, accent_color:Color, x: float, y: float, size: float = 8.0, offset_angle: float = 0.0):
        super().__init__("Tear", color, accent_color, x, y, size)
        self.base_angle: float = BASE_ANGLE
        self.offset_angle: float = offset_angle

    def draw(self) -> None:
        # Compute total rotation angle
        angle = -(self.base_angle + self.offset_angle)
        cos_a = math.cos(angle)
        sin_a = math.sin(angle)

        # Geometry setup
        half_side = (self.size * SQRT_2) / 2

        # Define original points relative to center (self.x, self.y)
        points = [
            (0          , -half_side * 2),  # top
            (half_side  , 0),       # right
            (0          , half_side),       # bottom
            (-half_side , 0)       # left
        ]

        # Rotate and translate points
        rotated = []
        for px, py in points:
            rx = px * cos_a - py * sin_a + self.x
            ry = px * sin_a + py * cos_a + self.y
            rotated.append((rx, ry))

        # Unpack rotated points
        (x1, y1), (x2, y2), (x3, y3), (x4, y4) = rotated

        # Draw filled and outlined quad
        Overlay().DrawQuadFilled(x1, y1, x2, y2, x3, y3, x4, y4, color=self.color.to_color())
        Overlay().DrawQuad(x1, y1, x2, y2, x3, y3, x4, y4, color=self.accent_color.to_color(), thickness=2.0)
               
shapes: dict[str, type[Shape]] = {
    "Triangle": Triangle,
    "Circle": Circle,
    "Teardrop": Teardrop,
    "Square": Square,
    "Penta": Penta,
    "Tear": Tear,
}
       
class Marker:
    def __init__(
        self,
        shape_type: Union[str, Shape],
        color: Color,
        accent_color: Color,
        x:float = 0.0,
        y:float = 0.0,
        size: float = 5.0,
        **kwargs
    ):
        self.color: Color = color
        self.accent_color: Color = accent_color
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
            self.shape = shape_cls(x=x, y=y, color=color, accent_color=accent_color, size=size, **kwargs)


    def draw(self) -> None:
        self.shape.draw()
        
class AgentMarker(Marker):
    def __init__(
        self,
        shape_type: Union[str, Shape],
        agent_id: int,
        color: Color,
        size: float = 5.0,
        zoom_offset: float = 0.0,
        **kwargs 
    ):
        self.agent_id = agent_id
        x, y = Agent.GetXY(agent_id)
        x, y = Map.MissionMap.MapProjection.GamePosToScreen(x, y, zoom_offset)
        super().__init__(shape_type=shape_type, color=color, x=x, y=y, size=size, **kwargs)

#endregion

#Marker("Tear", Color(255,128,0,255), accent_color, x,y, size=10.0 + size_offset, offset_angle=agent.rotation_angle).draw()
#region CONFIGS
class ConfigItem:
    def __init__(self, name: str, marker_name: str, color: Color, alternate_color: Color, marker_size :float, visible: bool = True):
        self.Name:str = name
        self.Marker:str = marker_name
        self.Color:Color = color
        self.AlternateColor:Color = alternate_color
        self.size :float = marker_size
        self.visible: bool = visible
        
    def __repr__(self) -> str:
        return f"ConfigItem(Name={self.Name}, Marker={self.Marker}, Color={self.Color}, AlternateColor={self.AlternateColor}, size={self.size})"
       
class Config:
    def __init__(self, name: str):
        self.Name: str = name
        self.ConfigItems: list[ConfigItem] = []
        
    def add(self, config_item: ConfigItem) -> None:
        self.ConfigItems.append(config_item)
        
    def get(self, name: str) -> ConfigItem:
        for item in self.ConfigItems:
            if item.Name == name:
                return item
        return ConfigItem(name, "Circle", Color(0, 0, 0, 255), Color(0, 0, 0, 255), 5.0)
    
    def remove(self, name: str) -> None:
        for item in self.ConfigItems:
            if item.Name == name:
                self.ConfigItems.remove(item)
                break
            
    def update(self, name: str, new_config_item: ConfigItem) -> None:
        for index, item in enumerate(self.ConfigItems):
            if item.Name == name:
                self.ConfigItems[index] = new_config_item
                break
        
    def __repr__(self) -> str:
        return f"Config(Name={self.Name}, ConfigItems={self.ConfigItems})"
    

GLOBAL_CONFIGS: Config = Config("Global")
player_color = Color(255, 128, 0, 255)
object_player = ConfigItem("Player", marker_name="Tear", color=player_color, alternate_color=player_color.desaturate(0.5), marker_size=10.0)
GLOBAL_CONFIGS.add(object_player)
ally_color = Color(0,179,0,255)
object_ally = ConfigItem("Ally", marker_name="Tear", color=ally_color, alternate_color=ally_color.desaturate(0.5), marker_size=8.0)
GLOBAL_CONFIGS.add(object_ally)
players_color = Color(100,100,255,255)
object_players = ConfigItem("Players", marker_name="Tear", color=players_color, alternate_color=players_color.desaturate(0.5), marker_size=8.0)
GLOBAL_CONFIGS.add(object_players)
neutral_color = Color(0,0,220,255)
object_neutral = ConfigItem("Neutral", marker_name="Circle", color=neutral_color, alternate_color=neutral_color.desaturate(0.5), marker_size=4.0)
GLOBAL_CONFIGS.add(object_neutral)
enemy_color = Color(255,0,0,255)
object_enemy = ConfigItem("Enemy", marker_name="Tear", color=enemy_color, alternate_color=enemy_color.desaturate(0.5), marker_size=8.0)
GLOBAL_CONFIGS.add(object_enemy)

for spirit_buff in SPIRIT_BUFFS:
    buff_color = spirit_buff.color
    r,g,b,a = buff_color.get_rgba()
    aura_color = Color(r, g, b, int(a * 0.17))
    object_buff = ConfigItem(f"{spirit_buff.spirit_name}", marker_name="Circle", color=buff_color, alternate_color=aura_color, marker_size=4.0)
    GLOBAL_CONFIGS.add(object_buff)

pet_color = Color(0,179,0,255)
object_pet = ConfigItem("Pet", marker_name="Circle", color=pet_color, alternate_color=pet_color.desaturate(0.5), marker_size=4.0)
GLOBAL_CONFIGS.add(object_pet)
minion_color = Color(0,128,93,255)
object_minion = ConfigItem("Minion", marker_name="Circle", color=minion_color, alternate_color=minion_color.desaturate(0.5), marker_size=4.0)
GLOBAL_CONFIGS.add(object_minion)
npc_color = Color(153,255,153,255)
object_npc = ConfigItem("NPC", marker_name="Triangle", color=npc_color, alternate_color=npc_color.desaturate(0.5), marker_size=8.0)
GLOBAL_CONFIGS.add(object_npc)
minipet_color =  Color(100,100,255,255)
object_minipet = ConfigItem("Minipet", marker_name="Circle", color=minipet_color, alternate_color=minipet_color.desaturate(0.5), marker_size=2.0)
GLOBAL_CONFIGS.add(object_minipet)
default_color = Color(70,70,70,255)
object_default = ConfigItem("Default", marker_name="Circle", color=default_color, alternate_color=default_color.desaturate(0.5), marker_size=4.0)
GLOBAL_CONFIGS.add(object_default)
gadget_color = Color(120,120,120,255)
object_gadget = ConfigItem("Gadget", marker_name="Circle", color=gadget_color, alternate_color=gadget_color.desaturate(0.5), marker_size=6.0)
GLOBAL_CONFIGS.add(object_gadget)
item_color = Color(255,255,0,255)
object_item = ConfigItem("Item", marker_name="Circle", color=item_color, alternate_color=item_color.desaturate(0.5), marker_size=6.0)
GLOBAL_CONFIGS.add(object_item)


#region MISSION MAP
class MissionMap:
    def __init__(self):
        self.left = 0
        self.top = 0
        self.right = 0
        self.bottom = 0
        self.width = 0
        self.height = 0

        self.player_screen_x, self.player_screen_y = 0, 0
        self.player_agent_id = 0
        self.player_target_id = 0
        
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
        self.scale_x, self.scale_y = 1.0, 1.0
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
        
        self.player_target_id = Player.GetTargetID()
        self.player_agent_id = Player.GetAgentID()
        
        click_x, click_y = Map.MissionMap.GetLastClickCoords()

        self.last_click_x, self.last_click_y = Map.MissionMap.MapProjection.ScreenToGamePos(click_x, click_y, self.mega_zoom)
        
        if not self.geometry:
            self.boundaries = Map.map_instance().map_boundaries
            self.left_bound, self.top_bound, self.right_bound, self.bottom_bound = Map.GetMapWorldMapBounds()
            
            self.geometry = Map.Pathing.GetComputedGeometry()
            self.renderer.set_primitives(self.geometry, Color(255, 255, 255, 80).to_dx_color())
            self.mega_zoom_renderer.set_primitives(self.geometry, Color(255, 255, 255, 100).to_dx_color())

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
        self.renderer.world_space.set_scale(self.scale_x)
        self.map_origin = Map.MissionMap.MapProjection.GameMapToScreen(0.0,0.0,self.mega_zoom)
        
        
mission_map = MissionMap()

#endregion

#region DRAWING
def DrawFrame():
    global mission_map
    def _draw_aggro_bubble():
        Overlay().DrawPoly      (mission_map.player_screen_x, mission_map.player_screen_y, radius=RawGwinchToPixels(Range.Earshot.value,mission_map.zoom, mission_map.mega_zoom, mission_map.scale_x)-2, color=Utils.RGBToColor(255, 255, 255, 40),numsegments=64,thickness=4.0)
        Overlay().DrawPolyFilled(mission_map.player_screen_x, mission_map.player_screen_y, radius=RawGwinchToPixels(Range.Earshot.value,mission_map.zoom, mission_map.mega_zoom, mission_map.scale_x), color=Utils.RGBToColor(255, 255, 255, 40),numsegments=64)
        
    Overlay().BeginDraw("MissionMapOverlay", mission_map.left, mission_map.top, mission_map.width, mission_map.height)
    #terrain 
    
    zoom = mission_map.zoom + mission_map.mega_zoom
    
    if zoom >3.5:
        mission_map.mega_zoom_renderer.DrawQuadFilled(mission_map.left,mission_map.top, mission_map.right,mission_map.top, mission_map.right,mission_map.bottom, mission_map.left,mission_map.bottom, color=Utils.RGBToColor(75,75,75,200))
        
        mission_map.mega_zoom_renderer.render()
    else:
        mission_map.renderer.render()
        
    _draw_aggro_bubble()
    #Compass Range
    Overlay().DrawPoly      (mission_map.player_screen_x, mission_map.player_screen_y, radius=RawGwinchToPixels(Range.Compass.value,mission_map.zoom, mission_map.mega_zoom, mission_map.scale_x), color=Utils.RGBToColor(0, 0, 0, 255),numsegments=360,thickness=1.0)
    zoom = mission_map.zoom + mission_map.mega_zoom
    Overlay().DrawPoly      (mission_map.player_screen_x, mission_map.player_screen_y, radius=RawGwinchToPixels(Range.Compass.value,mission_map.zoom, mission_map.mega_zoom, mission_map.scale_x)-(2.85*zoom), color=Utils.RGBToColor(255, 255, 255, 40),numsegments=360,thickness=(5.7*zoom))
    
    agent_array = AgentArray.GetRawAgentArray()
    for agent in agent_array:
        alliegance = agent.living_agent.allegiance.ToInt()
        x,y = RawGamePosToScreen(agent.x, agent.y, 
                                 mission_map.zoom, mission_map.mega_zoom,
                                 mission_map.left_bound, mission_map.top_bound,
                                 mission_map.boundaries, 
                                 mission_map.pan_offset_x, mission_map.pan_offset_y,
                                 mission_map.scale_x, mission_map.scale_y,
                                 mission_map.mission_map_screen_center_x, mission_map.mission_map_screen_center_y)
    
        accent_color = Color(0, 0, 0, 150)
        size_offset = 0.0
        if agent.id == mission_map.player_target_id:
            accent_color = Color(235, 235, 50, 255)
            size_offset =2.0
                
        size_offset += mission_map.mega_zoom *( 1/5)
        
        marker = GLOBAL_CONFIGS.get("Default")
        color = marker.Color
        accent_color = marker.AlternateColor
        alive = True
        rotation_angle = 0.0
        is_spawned = False
        
        if agent.is_living:
            alive = agent.living_agent.is_alive
            rotation_angle = agent.rotation_angle
            has_boss_glow = agent.living_agent.has_boss_glow
            is_spawned = agent.living_agent.is_spawned
            
            if has_boss_glow:
                accent_color = Color(0, 200, 45, 255)
            
            if agent.id == mission_map.player_agent_id:
                marker = GLOBAL_CONFIGS.get("Player")   
            elif alliegance == Allegiance.Ally:
                if agent.living_agent.is_npc:
                    marker = GLOBAL_CONFIGS.get("Ally")
                else:
                    marker = GLOBAL_CONFIGS.get("Players")
            elif alliegance == Allegiance.Neutral:
                marker = GLOBAL_CONFIGS.get("Neutral")
            elif alliegance == Allegiance.Enemy:
                if is_spawned:
                    model_id = agent.living_agent.player_number
                    spirit_name = get_spirit_name(model_id)
                    if spirit_name != "Unknown" and alive:
                        marker = GLOBAL_CONFIGS.get(spirit_name)
                        enemy_marker = GLOBAL_CONFIGS.get("Enemy")
                        shifted_color = marker.Color.shift(enemy_marker.Color, 0.5)
                        shifted_color.set_a(int(shifted_color.get_a() * 0.333))
                        #spirit range area
                        Overlay().DrawPoly      (x, y, radius=RawGwinchToPixels(Range.Spirit.value,mission_map.zoom, mission_map.mega_zoom, mission_map.scale_x)-2, color=shifted_color.to_color(),numsegments=64,thickness=1.0)
                        Overlay().DrawPolyFilled(x, y, radius=RawGwinchToPixels(Range.Spirit.value,mission_map.zoom, mission_map.mega_zoom, mission_map.scale_x), color=shifted_color.to_color(),numsegments=64)
                else:  
                    marker = GLOBAL_CONFIGS.get("Enemy")
            elif alliegance == Allegiance.SpiritPet:     
                model_id = agent.living_agent.player_number
                spirit_name = get_spirit_name(model_id)
                if spirit_name != "Unknown" and alive:
                    marker = GLOBAL_CONFIGS.get(spirit_name)
                    #spirit range area
                    Overlay().DrawPoly      (x, y, radius=RawGwinchToPixels(Range.Spirit.value,mission_map.zoom, mission_map.mega_zoom, mission_map.scale_x)-2, color=marker.AlternateColor.to_color(),numsegments=64,thickness=1.0)
                    Overlay().DrawPolyFilled(x, y, radius=RawGwinchToPixels(Range.Spirit.value,mission_map.zoom, mission_map.mega_zoom, mission_map.scale_x), color=marker.AlternateColor.to_color(),numsegments=64)
                else:
                    if not is_spawned:
                        marker = GLOBAL_CONFIGS.get("Pet")
            elif alliegance == Allegiance.Minion:
                marker = GLOBAL_CONFIGS.get("Minion")
            elif alliegance == Allegiance.NpcMinipet:
                level = agent.living_agent.level
                if level > 1:
                    marker = GLOBAL_CONFIGS.get("NPC")   
                else: 
                    marker = GLOBAL_CONFIGS.get("Minipet")     
            else:
                marker = GLOBAL_CONFIGS.get("Default")
        elif agent.is_gadget:
            marker = GLOBAL_CONFIGS.get("Gadget")
        elif agent.is_item:
            marker = GLOBAL_CONFIGS.get("Item")
         
        color = marker.Color if alive else marker.AlternateColor   
        Marker(marker.Marker, color, accent_color, x,y, marker.size + size_offset, offset_angle=rotation_angle).draw()

    Overlay().EndDraw() 
    

def DrawWindow():
    global mission_map
    if PyImGui.begin("Mission Map"):
        pass
    PyImGui.end()
    
def configure():
    pass

def main():  
    if not Routines.Checks.Map.MapValid():
        mission_map.geometry = [] 
        return
    
    if not Map.MissionMap.IsWindowOpen():
        return
    
    mission_map.update()
    #DrawWindow()
    DrawFrame()       
    
    if mission_map.zoom >= 3.5:
            mission_map.mega_zoom = FloatingSlider("Mega Zoom", mission_map.mega_zoom, mission_map.left, mission_map.bottom-27, 0.0, 15.0, Color(255, 255, 255, 255))
    else:
        mission_map.mega_zoom = 0.0 
    
    
if __name__ == "__main__":
    main()
