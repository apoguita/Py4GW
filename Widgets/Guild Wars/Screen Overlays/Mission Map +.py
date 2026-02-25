from Py4GWCoreLib import PetModelID, SpiritModelID
from Py4GWCoreLib import Color
from Py4GWCoreLib import GLOBAL_CACHE
import PyImGui
from Py4GWCoreLib import ImGui, Color
from Py4GWCoreLib import DXOverlay
from Py4GWCoreLib import ThrottledTimer
from Py4GWCoreLib import Timer
from Py4GWCoreLib import Utils
from Py4GWCoreLib import Range
from Py4GWCoreLib import Rarity
from Py4GWCoreLib import Routines
from Py4GWCoreLib import Map, Player
from Py4GWCoreLib import Agent, AgentArray
from Py4GWCoreLib.native_src.context.AgentContext import AgentStruct

from typing import Any, Union, cast
import math

#region CONSTANTS
MODULE_NAME = "Mission Map"
MATH_PI = math.pi
BASE_ANGLE = (-MATH_PI / 2)
SQRT_2 = math.sqrt(2)
GWINCHES = 96.0
POLY_SEGMENTS = 16
PET_MODEL_IDS = set(e.value for e in PetModelID)
AREA_SPIRIT_MODELS = [SpiritModelID.DESTRUCTION, SpiritModelID.PRESERVATION]
EARSHOT_SPIRIT_MODELS = [SpiritModelID.AGONY, SpiritModelID.REJUVENATION]
CHEST_GADGET_IDS = [9,69,4579,8141, 9523, 4582]

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
    SpiritBuff("Frozen Soil", SpiritModelID.FROZEN_SOIL, GLOBAL_CACHE.Skill.GetID("Frozen_Soil"), RANGER_SPIRIT_COLOR),
    SpiritBuff("Life", SpiritModelID.LIFE, GLOBAL_CACHE.Skill.GetID("Life"), RITUALIST_SPIRIT_COLOR),
    SpiritBuff("Bloodsong", SpiritModelID.BLOODSONG, GLOBAL_CACHE.Skill.GetID("Bloodsong"), RITUALIST_SPIRIT_COLOR),
    SpiritBuff("Anger", SpiritModelID.ANGER, GLOBAL_CACHE.Skill.GetID("Signet_of_Spirits"), RITUALIST_SPIRIT_COLOR),
    SpiritBuff("Hate", SpiritModelID.HATE, GLOBAL_CACHE.Skill.GetID("Signet_of_Spirits"), RITUALIST_SPIRIT_COLOR),
    SpiritBuff("Suffering", SpiritModelID.SUFFERING, GLOBAL_CACHE.Skill.GetID("Signet_of_Spirits"), RITUALIST_SPIRIT_COLOR),
    SpiritBuff("Anguish", SpiritModelID.ANGUISH, GLOBAL_CACHE.Skill.GetID("Anguish"), RITUALIST_SPIRIT_COLOR),
    SpiritBuff("Disenchantment", SpiritModelID.DISENCHANTMENT, GLOBAL_CACHE.Skill.GetID("Disenchantment"), RITUALIST_SPIRIT_COLOR),
    SpiritBuff("Dissonance", SpiritModelID.DISSONANCE, GLOBAL_CACHE.Skill.GetID("Dissonance"), RITUALIST_SPIRIT_COLOR),
    SpiritBuff("Pain", SpiritModelID.PAIN, GLOBAL_CACHE.Skill.GetID("Pain"), RITUALIST_SPIRIT_COLOR),
    SpiritBuff("Shadowsong", SpiritModelID.SHADOWSONG, GLOBAL_CACHE.Skill.GetID("Shadowsong"), RITUALIST_SPIRIT_COLOR),
    SpiritBuff("Wanderlust", SpiritModelID.WANDERLUST, GLOBAL_CACHE.Skill.GetID("Wanderlust"), RITUALIST_SPIRIT_COLOR),
    SpiritBuff("Vampirism", SpiritModelID.VAMPIRISM, GLOBAL_CACHE.Skill.GetID("Vampirism"), EBON_VANGUARD_COLOR),
    SpiritBuff("Agony", SpiritModelID.AGONY, GLOBAL_CACHE.Skill.GetID("Agony"), RITUALIST_SPIRIT_COLOR),
    SpiritBuff("Displacement", SpiritModelID.DISPLACEMENT, GLOBAL_CACHE.Skill.GetID("Displacement"), RITUALIST_SPIRIT_COLOR),
    SpiritBuff("Earthbind", SpiritModelID.EARTHBIND, GLOBAL_CACHE.Skill.GetID("Earthbind"), RITUALIST_SPIRIT_COLOR),
    SpiritBuff("Empowerment", SpiritModelID.EMPOWERMENT, GLOBAL_CACHE.Skill.GetID("Empowerment"), RITUALIST_SPIRIT_COLOR),
    SpiritBuff("Preservation", SpiritModelID.PRESERVATION, GLOBAL_CACHE.Skill.GetID("Preservation"), RITUALIST_SPIRIT_COLOR),
    SpiritBuff("Recovery", SpiritModelID.RECOVERY, GLOBAL_CACHE.Skill.GetID("Recovery"), RITUALIST_SPIRIT_COLOR),
    SpiritBuff("Recuperation", SpiritModelID.RECUPERATION, GLOBAL_CACHE.Skill.GetID("Recuperation"), RITUALIST_SPIRIT_COLOR),
    SpiritBuff("Rejuvenation", SpiritModelID.REJUVENATION, GLOBAL_CACHE.Skill.GetID("Rejuvenation"), RITUALIST_SPIRIT_COLOR),
    SpiritBuff("Shelter", SpiritModelID.SHELTER, GLOBAL_CACHE.Skill.GetID("Shelter"), RITUALIST_SPIRIT_COLOR),
    SpiritBuff("Soothing", SpiritModelID.SOOTHING, GLOBAL_CACHE.Skill.GetID("Soothing"), RITUALIST_SPIRIT_COLOR),
    SpiritBuff("Union", SpiritModelID.UNION, GLOBAL_CACHE.Skill.GetID("Union"), RITUALIST_SPIRIT_COLOR),
    SpiritBuff("Destruction", SpiritModelID.DESTRUCTION, GLOBAL_CACHE.Skill.GetID("Destruction"), RITUALIST_SPIRIT_COLOR),
    SpiritBuff("Restoration", SpiritModelID.RESTORATION, GLOBAL_CACHE.Skill.GetID("Restoration"), RITUALIST_SPIRIT_COLOR),
    SpiritBuff("Winds", SpiritModelID.WINDS, GLOBAL_CACHE.Skill.GetID("Winds"),EBON_VANGUARD_COLOR),
    SpiritBuff("Brambles", SpiritModelID.BRAMBLES, GLOBAL_CACHE.Skill.GetID("Brambles"), RANGER_SPIRIT_COLOR),
    SpiritBuff("Conflagration", SpiritModelID.CONFLAGRATION, GLOBAL_CACHE.Skill.GetID("Conflagration"), RANGER_SPIRIT_COLOR),
    SpiritBuff("Energizing Wind", SpiritModelID.ENERGIZING_WIND, GLOBAL_CACHE.Skill.GetID("Energizing_Wind"), RANGER_SPIRIT_COLOR),
    SpiritBuff("Equinox", SpiritModelID.EQUINOX, GLOBAL_CACHE.Skill.GetID("Equinox"), RANGER_SPIRIT_COLOR),
    SpiritBuff("Edge of Extinction", SpiritModelID.EDGE_OF_EXTINCTION, GLOBAL_CACHE.Skill.GetID("Edge_of_Extinction"), RANGER_SPIRIT_COLOR),
    SpiritBuff("Famine", SpiritModelID.FAMINE, GLOBAL_CACHE.Skill.GetID("Famine"), RANGER_SPIRIT_COLOR),
    SpiritBuff("Favorable Winds", SpiritModelID.FAVORABLE_WINDS, GLOBAL_CACHE.Skill.GetID("Favorable_Winds"), RANGER_SPIRIT_COLOR),
    SpiritBuff("Fertile Season", SpiritModelID.FERTILE_SEASON, GLOBAL_CACHE.Skill.GetID("Fertile_Season"), RANGER_SPIRIT_COLOR),
    SpiritBuff("Greater Conflagration", SpiritModelID.GREATER_CONFLAGRATION, GLOBAL_CACHE.Skill.GetID("Greater_Conflagration"), RANGER_SPIRIT_COLOR),
    SpiritBuff("Infuriating Heat", SpiritModelID.INFURIATING_HEAT, GLOBAL_CACHE.Skill.GetID("Infuriating_Heat"), RANGER_SPIRIT_COLOR),
    SpiritBuff("Lacerate", SpiritModelID.LACERATE, GLOBAL_CACHE.Skill.GetID("Lacerate"), RANGER_SPIRIT_COLOR),
    SpiritBuff("Muddy Terrain", SpiritModelID.MUDDY_TERRAIN, GLOBAL_CACHE.Skill.GetID("Muddy_Terrain"), RANGER_SPIRIT_COLOR),
    SpiritBuff("Nature's Renewal", SpiritModelID.NATURES_RENEWAL, GLOBAL_CACHE.Skill.GetID("Natures_Renewal"), RANGER_SPIRIT_COLOR),
    SpiritBuff("Pestilence", SpiritModelID.PESTILENCE, GLOBAL_CACHE.Skill.GetID("Pestilence"), RANGER_SPIRIT_COLOR),
    SpiritBuff("Predatory Season", SpiritModelID.PREDATORY_SEASON, GLOBAL_CACHE.Skill.GetID("Predatory_Season"), RANGER_SPIRIT_COLOR),
    SpiritBuff("Primal Echoes", SpiritModelID.PRIMAL_ECHOES, GLOBAL_CACHE.Skill.GetID("Primal_Echoes"), RANGER_SPIRIT_COLOR),
    SpiritBuff("Quickening Zephyr", SpiritModelID.QUICKENING_ZEPHYR, GLOBAL_CACHE.Skill.GetID("Quickening_Zephyr"), RANGER_SPIRIT_COLOR),
    SpiritBuff("Quicksand", SpiritModelID.QUICKSAND, GLOBAL_CACHE.Skill.GetID("Quicksand"), RANGER_SPIRIT_COLOR),
    SpiritBuff("Roaring Winds", SpiritModelID.ROARING_WINDS, GLOBAL_CACHE.Skill.GetID("Roaring_Winds"), RANGER_SPIRIT_COLOR),
    SpiritBuff("Symbiosis", SpiritModelID.SYMBIOSIS, GLOBAL_CACHE.Skill.GetID("Symbiosis"), RANGER_SPIRIT_COLOR),
    SpiritBuff("Toxicity", SpiritModelID.TOXICITY, GLOBAL_CACHE.Skill.GetID("Toxicity"), RANGER_SPIRIT_COLOR),
    SpiritBuff("Tranquility", SpiritModelID.TRANQUILITY, GLOBAL_CACHE.Skill.GetID("Tranquility"), RANGER_SPIRIT_COLOR),
    SpiritBuff("Winter", SpiritModelID.WINTER, GLOBAL_CACHE.Skill.GetID("Winter"), RANGER_SPIRIT_COLOR),
    SpiritBuff("Winnowing", SpiritModelID.WINNOWING, GLOBAL_CACHE.Skill.GetID("Winnowing"), RANGER_SPIRIT_COLOR),
]

def get_spirit_name(model_id: int) -> str:
    for buff in SPIRIT_BUFFS:
        if buff.model_id == model_id:
            return buff.spirit_name
    return "Unknown"


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

def RawGamePosToScreen(x:float, y:float, zoom:float, zoom_offset:float, left_bound:float, top_bound:float, boundaries:tuple[float, float, float, float],
                       pan_offset_x:float, pan_offset_y:float, scale_x:float, scale_y:float,
                       mission_map_screen_center_x:float, mission_map_screen_center_y:float) -> tuple[float, float]:

    global GWINCHES

    if len(boundaries) < 4:
        return 0.0, 0.0  # fail-safe

    min_x = boundaries[0]
    max_y = boundaries[3]

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

def RawScreenToRawGamePos(screen_x: float, screen_y: float, zoom: float, zoom_offset: float,
                       left_bound: float, top_bound: float, boundaries: tuple[float, float, float, float],
                       pan_offset_x: float, pan_offset_y: float,
                       scale_x: float, scale_y: float,
                       mission_map_screen_center_x: float, mission_map_screen_center_y: float) -> tuple[float, float]:
    global GWINCHES

    if len(boundaries) < 4:
        return 0.0, 0.0  # fail-safe

    min_x = boundaries[0]
    max_y = boundaries[3]

    # Compute origin same as before
    origin_x = left_bound + abs(min_x) / GWINCHES
    origin_y = top_bound + abs(max_y) / GWINCHES

    zoom_total = zoom + zoom_offset
    if zoom_total == 0:
        zoom_total = 1.0

    # Reverse zoom and center offset
    scaled_x = (screen_x - mission_map_screen_center_x) / zoom_total
    scaled_y = (screen_y - mission_map_screen_center_y) / zoom_total

    # Reverse scaling
    offset_x = scaled_x / (scale_x if scale_x != 0 else 1)
    offset_y = scaled_y / (scale_y if scale_y != 0 else 1)

    # Apply pan offset
    world_x = offset_x + pan_offset_x
    world_y = offset_y + pan_offset_y

    # Convert from world map space to game-space (gwinches)
    game_x = (world_x - origin_x) * GWINCHES
    game_y = -(world_y - origin_y) * GWINCHES  # Invert Y back

    return game_x, game_y


def RawGwinchToPixels(gwinch_value: float, zoom:float, zoom_offset:float, scale_x) -> float:
    global GWINCHES
    pixels_per_gwinch = (scale_x * (zoom + zoom_offset)) / GWINCHES
    return gwinch_value * pixels_per_gwinch

def FloatingCoordsStrip(x, y, last_x, last_y, color, width=None, margin=8, label="Cords"):
    # place just above the bottom edge with a small margin
    win_x = x + margin
    win_y = y + 15 - margin
    PyImGui.set_next_window_pos(win_x, win_y)
    if width is not None:
        PyImGui.set_next_window_size(width - (margin * 2), 25)

    flags = (PyImGui.WindowFlags.NoCollapse |
             PyImGui.WindowFlags.NoTitleBar |
             PyImGui.WindowFlags.NoScrollbar |
             PyImGui.WindowFlags.NoMove |
             PyImGui.WindowFlags.AlwaysAutoResize |
             PyImGui.WindowFlags.NoBackground)

    # clean, overlay look
    PyImGui.push_style_var2(ImGui.ImGuiStyleVar.WindowPadding, 4.0, 4.0)
    PyImGui.push_style_var2(ImGui.ImGuiStyleVar.FramePadding, 2.0, 2.0)
    PyImGui.push_style_var(ImGui.ImGuiStyleVar.WindowRounding, 0.0)
    PyImGui.push_style_color(PyImGui.ImGuiCol.WindowBg, (0, 0, 0, 0))
    PyImGui.push_style_color(PyImGui.ImGuiCol.Border, color.to_tuple())

    if PyImGui.begin("##mm_coords_strip", flags):
        if PyImGui.button("Copy"):
            PyImGui.set_clipboard_text(f"{int(last_x)}, {int(last_y)}")
        if PyImGui.is_item_hovered():
            ImGui.show_tooltip("Copy the last clicked coordinates.")
        PyImGui.same_line(0, 6)
        PyImGui.text(f"{label}: ({int(last_x)}, {int(last_y)})")
    PyImGui.end()

    PyImGui.pop_style_color(2)
    PyImGui.pop_style_var(3)

#endregion
#region MARKERS
def DLLine(x1, y1, x2, y2, color, thickness=1.0):
    PyImGui.draw_list_add_line(float(x1), float(y1), float(x2), float(y2), color, float(thickness))

def DLCircle(x, y, radius, color, numsegments=16, thickness=1.0):
    PyImGui.draw_list_add_circle(float(x), float(y), float(radius), color, int(numsegments), float(thickness))

def DLCircleFilled(x, y, radius, color, numsegments=16):
    PyImGui.draw_list_add_circle_filled(float(x), float(y), float(radius), color, int(numsegments))

def DLTriangle(x1, y1, x2, y2, x3, y3, color, thickness=1.0):
    PyImGui.draw_list_add_triangle(float(x1), float(y1), float(x2), float(y2), float(x3), float(y3), color, float(thickness))

def DLTriangleFilled(x1, y1, x2, y2, x3, y3, color):
    PyImGui.draw_list_add_triangle_filled(float(x1), float(y1), float(x2), float(y2), float(x3), float(y3), color)

def DLQuad(x1, y1, x2, y2, x3, y3, x4, y4, color, thickness=1.0):
    PyImGui.draw_list_add_quad(float(x1), float(y1), float(x2), float(y2), float(x3), float(y3), float(x4), float(y4), color, float(thickness))

def DLQuadFilled(x1, y1, x2, y2, x3, y3, x4, y4, color):
    PyImGui.draw_list_add_quad_filled(float(x1), float(y1), float(x2), float(y2), float(x3), float(y3), float(x4), float(y4), color)

_COLOR_INT_CACHE: dict[tuple[int, int, int, int], int] = {}
def ColorToIntCached(color: Color) -> int:
    key = color.get_rgba()
    cached = _COLOR_INT_CACHE.get(key)
    if cached is not None:
        return cached
    packed = color.to_color()
    _COLOR_INT_CACHE[key] = packed
    return packed

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
    UNIT_POINTS = tuple(
        (math.cos(i * (2 * MATH_PI / 3)), math.sin(i * (2 * MATH_PI / 3)))
        for i in range(3)
    )
    def __init__(self, color: Color, accent_color:Color,x: float, y:float, size: float = 5.0, offset_angle: float = 0.0):
        super().__init__("Triangle", color, accent_color, x, y, size)
        self.accent_color: Color = accent_color
        self.offset_angle: float = offset_angle
        self.base_angle:float = 0.0 # + Utils.DegToRad(self.offset_angle)

    def draw(self) -> None:
        angle_offset = self.base_angle + self.offset_angle
        cos_o = math.cos(angle_offset)
        sin_o = math.sin(angle_offset)
        points = []
        for ux, uy in Triangle.UNIT_POINTS:
            rx = ux * cos_o - uy * sin_o
            ry = ux * sin_o + uy * cos_o
            points.append((self.x + (rx * self.size), self.y + (ry * self.size)))


        DLTriangleFilled(
            points[0][0], points[0][1],
            points[1][0], points[1][1],
            points[2][0], points[2][1],
            ColorToIntCached(self.color)
        )
        # Draw the triangle outline     
        DLTriangle(
            points[0][0], points[0][1],
            points[1][0], points[1][1],
            points[2][0], points[2][1],
            ColorToIntCached(self.accent_color),
            thickness=2.0
        )
 
class Circle(Shape):
    def __init__(self, color: Color,accent_color:Color, x: float, y: float, size: float, segments: int = 16, offset_angle= 0.0):
        self.segments: int = segments
        super().__init__("Circle", color, accent_color, x, y, size, offset_angle)
        self.accent_color: Color = accent_color

    def draw(self) -> None:
        DLCircleFilled(self.x, self.y, radius=self.size, color=ColorToIntCached(self.color), numsegments=self.segments)
        DLCircle(self.x, self.y, radius=self.size, color=ColorToIntCached(self.accent_color), numsegments=self.segments, thickness=2)
        
class Teardrop(Shape):
    ARROW_LOCAL_POINTS_UNIT = (
        (0.0, -SQRT_2),
        (-SQRT_2 / 2, -SQRT_2 / 2),
        (SQRT_2 / 2, -SQRT_2 / 2),
    )
    def __init__(self, color: Color,accent_color:Color, x: float, y: float, size: float, offset_angle: float = 0.0, segments: int = 16):
        self.segments: int = segments
        super().__init__("Teardrop", color, accent_color, x, y, size)
        self.accent_color: Color = accent_color
        self.base_angle: float = BASE_ANGLE
        self.offset_angle: float = offset_angle

    def draw(self) -> None:
        # 1. Draw unrotated circle
        DLCircleFilled(self.x, self.y, radius=self.size, color=ColorToIntCached(self.color), numsegments=self.segments)
        DLCircle(self.x, self.y, radius=self.size, color=ColorToIntCached(self.accent_color), numsegments=self.segments, thickness=2)

        # 2. Calculate rotation angle (negated for in-game rotation match)
        angle = -(self.base_angle + self.offset_angle)
        cos_a = math.cos(angle)
        sin_a = math.sin(angle)

        # 4. Rotate + translate points
        def rotate(px, py):
            rx = px * cos_a - py * sin_a + self.x
            ry = px * sin_a + py * cos_a + self.y
            return (rx, ry)

        p1 = rotate(self.ARROW_LOCAL_POINTS_UNIT[0][0] * self.size, self.ARROW_LOCAL_POINTS_UNIT[0][1] * self.size)
        p2 = rotate(self.ARROW_LOCAL_POINTS_UNIT[1][0] * self.size, self.ARROW_LOCAL_POINTS_UNIT[1][1] * self.size)
        p4 = rotate(self.ARROW_LOCAL_POINTS_UNIT[2][0] * self.size, self.ARROW_LOCAL_POINTS_UNIT[2][1] * self.size)
        
        # 5. Draw the arrow
        DLTriangleFilled(p1[0], p1[1], p2[0], p2[1], p4[0], p4[1], color=ColorToIntCached(self.color))
        DLLine(p1[0], p1[1], p2[0], p2[1], color=ColorToIntCached(self.accent_color), thickness=2.0)
        DLLine(p1[0], p1[1], p4[0], p4[1], color=ColorToIntCached(self.accent_color), thickness=2.0)
     
class Penta(Shape):
    def __init__(self, color: Color,accent_color:Color, x: float, y: float, size: float):
        self.segments: int = 5
        super().__init__("Penta", color, accent_color, x, y, size)
        self.accent_color: Color = accent_color

    def draw(self) -> None:
        DLCircleFilled(self.x, self.y, radius=self.size, color=ColorToIntCached(self.color), numsegments=self.segments)
        DLCircle(self.x, self.y, radius=self.size, color=ColorToIntCached(self.accent_color), numsegments=self.segments, thickness=2)
        
class Square(Shape):
    def __init__(self, color: Color, accent_color:Color, x: float, y: float, size: float = 5.0, offset_angle: float = 0.0):
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

        DLQuadFilled(x1, y1, x2, y2, x3, y3, x4, y4, color=ColorToIntCached(self.color))
        DLQuad(x1, y1, x2, y2, x3, y3, x4, y4, color=ColorToIntCached(self.accent_color), thickness=2.0)
        
class Lock(Shape):
    def __init__(self, color: Color, accent_color:Color, x: float, y: float, size: float = 5.0, offset_angle: float = 0.0):
        super().__init__("Lock", color, accent_color, x, y, size)
        self.accent_color: Color = accent_color

    def draw(self) -> None:
        # Inscribed square inside a circle of radius = self.size
        half_side = (self.size * SQRT_2) / 2
        eighth_side = half_side / 4

        # Corner coordinates
        x1, y1 = self.x - half_side, self.y - half_side  # top-left
        x2, y2 = self.x + half_side, self.y - half_side  # top-right
        x3, y3 = self.x + half_side, self.y + half_side  # bottom-right
        x4, y4 = self.x - half_side, self.y + half_side  # bottom-left

        DLCircle(self.x, self.y -half_side - eighth_side, radius=self.size / 2, color=ColorToIntCached(self.accent_color), numsegments=12, thickness=3)
        DLQuadFilled(x1, y1, x2, y2, x3, y3, x4, y4, color=ColorToIntCached(self.color))
        DLQuad(x1, y1, x2, y2, x3, y3, x4, y4, color=ColorToIntCached(self.accent_color), thickness=2.0)
        DLQuadFilled(self.x- eighth_side, self.y- eighth_side, self.x+eighth_side, self.y-eighth_side, self.x+eighth_side, self.y+eighth_side, self.x-eighth_side, self.y+eighth_side, color=ColorToIntCached(self.accent_color))
        
class SignPost(Shape):
    def __init__(self, color: Color, accent_color:Color, x: float, y: float, size: float = 5.0, offset_angle: float = 0.0):
        super().__init__("SignPost", color, accent_color, x, y, size)
        self.accent_color: Color = accent_color

    def draw(self) -> None:
        def _draw_text_line (x1, y1, x2, y2, color: Color):
            DLLine(x1, y1, x2, y2, color=ColorToIntCached(color), thickness=1.0)
            DLLine(x1, y1, x2, y2, color=ColorToIntCached(color), thickness=1.0)
            
        half_side = (self.size * SQRT_2) / 2
        quarter_side = half_side / 2
        eighth_side = half_side / 4
        three_quarter_side = half_side + quarter_side

        # Corner coordinates
        x1, y1 = self.x - three_quarter_side, self.y - half_side  # top-left
        x2, y2 = self.x + three_quarter_side, self.y - half_side  # top-right
        x3, y3 = self.x + three_quarter_side, self.y + half_side  # bottom-right
        x4, y4 = self.x - three_quarter_side, self.y + half_side  # bottom-left

        DLQuadFilled(x1, y1, x2, y2, x3, y3, x4, y4, color=ColorToIntCached(self.color))
        DLQuad(x1, y1, x2, y2, x3, y3, x4, y4, color=ColorToIntCached(self.accent_color), thickness=2.0)
        
        l1_x1, l1_y1 = self.x - half_side, self.y - quarter_side  # top-left
        l1_x2, l1_y2 = self.x + half_side, self.y - quarter_side  # top-right
        
        _draw_text_line(l1_x1, l1_y1, l1_x2, l1_y2, self.accent_color)
        y = self.y
        _draw_text_line(l1_x1, y, l1_x2, y, self.accent_color)

        
    

class Tear(Shape):
    LOCAL_POINTS_UNIT = (
        (0.0, -SQRT_2),
        (SQRT_2 / 2, 0.0),
        (0.0, SQRT_2 / 2),
        (-SQRT_2 / 2, 0.0),
    )
    def __init__(self, color: Color, accent_color:Color, x: float, y: float, size: float = 8.0, offset_angle: float = 0.0):
        super().__init__("Tear", color, accent_color, x, y, size)
        self.base_angle: float = BASE_ANGLE
        self.offset_angle: float = offset_angle

    def draw(self) -> None:
        # Compute total rotation angle
        angle = -(self.base_angle + self.offset_angle)
        cos_a = math.cos(angle)
        sin_a = math.sin(angle)

        # Rotate and translate points
        rotated = []
        for ux, uy in self.LOCAL_POINTS_UNIT:
            px = ux * self.size
            py = uy * self.size
            rx = px * cos_a - py * sin_a + self.x
            ry = px * sin_a + py * cos_a + self.y
            rotated.append((rx, ry))

        # Unpack rotated points
        (x1, y1), (x2, y2), (x3, y3), (x4, y4) = rotated

        # Draw filled and outlined quad
        DLQuadFilled(x1, y1, x2, y2, x3, y3, x4, y4, color=ColorToIntCached(self.color))
        DLQuad(x1, y1, x2, y2, x3, y3, x4, y4, color=ColorToIntCached(self.accent_color), thickness=2.0)
        
class Scale(Shape):
    def __init__(self, color: Color, accent_color:Color, x: float, y: float, size: float = 8.0, offset_angle: float = 0.0):
        super().__init__("Scale", color, accent_color, x, y, size)
        self.base_angle: float = BASE_ANGLE
        self.offset_angle: float = offset_angle

    def draw(self) -> None:
        half_side = (self.size * SQRT_2) / 2
        
        x1, y1 = self.x, self.y + half_side 
        x2, y2 = self.x, self.y - half_side 
        
        DLLine(x1, y1, x2, y2, color=ColorToIntCached(self.color), thickness=2.0)
        
        x1, y1 = self.x - half_side, self.y - half_side
        x2, y2 = self.x + half_side, self.y - half_side

        DLLine(x1, y1, x2, y2, color=ColorToIntCached(self.color), thickness=2.0)
        
        

        
               
shapes: dict[str, type[Shape]] = {
    "Triangle": Triangle,
    "Circle": Circle,
    "Teardrop": Teardrop,
    "Square": Square,
    "Penta": Penta,
    "Tear": Tear,
    "SignPost": SignPost,
    "Lock": Lock,
    "Scale": Scale,
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


_SHAPE_INSTANCE_CACHE: dict[str, Shape] = {}
def DrawMarkerCached(shape_type: str, color: Color, accent_color: Color, x: float, y: float, size: float, **kwargs) -> None:
    shape = _SHAPE_INSTANCE_CACHE.get(shape_type)
    if shape is None:
        shape_cls = shapes.get(shape_type)
        if shape_cls is None:
            raise ValueError(f"Unknown shape type: {shape_type}")
        shape_ctor = cast(Any, shape_cls)
        shape = shape_ctor(x=x, y=y, color=color, accent_color=accent_color, size=size, **kwargs)
        _SHAPE_INSTANCE_CACHE[shape_type] = shape
    else:
        shape.x = x
        shape.y = y
        shape.size = size
        shape.color = color
        shape.accent_color = accent_color
        if hasattr(shape, "offset_angle") and "offset_angle" in kwargs:
            shape.offset_angle = kwargs["offset_angle"]
    shape.draw()

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
accent_color = Color(0, 0, 0, 200)
player_color = Color(5, 190, 5, 255)
object_player = ConfigItem("Player", marker_name="Tear", color=player_color, alternate_color=accent_color, marker_size=10.0)
GLOBAL_CONFIGS.add(object_player)
ally_color = Color(0,179,0,255)
object_ally = ConfigItem("Ally", marker_name="Tear", color=ally_color, alternate_color=accent_color, marker_size=8.0)
GLOBAL_CONFIGS.add(object_ally)
players_color = Color(100,100,255,255)
object_players = ConfigItem("Players", marker_name="Tear", color=players_color, alternate_color=accent_color, marker_size=8.0)
GLOBAL_CONFIGS.add(object_players)
neutral_color = Color(0,220,220,255)
object_neutral = ConfigItem("Neutral", marker_name="Circle", color=neutral_color, alternate_color=accent_color, marker_size=4.0)
GLOBAL_CONFIGS.add(object_neutral)
enemy_color = Color(255,0,0,255)
object_enemy = ConfigItem("Enemy", marker_name="Tear", color=enemy_color, alternate_color=accent_color, marker_size=8.0)
GLOBAL_CONFIGS.add(object_enemy)

for spirit_buff in SPIRIT_BUFFS:
    buff_color = spirit_buff.color
    r,g,b,a = buff_color.get_rgba()
    aura_color = Color(r, g, b, int(a * 0.17))
    object_buff = ConfigItem(f"{spirit_buff.spirit_name}", marker_name="Circle", color=buff_color, alternate_color=aura_color, marker_size=4.0)
    GLOBAL_CONFIGS.add(object_buff)

pet_color = Color(0,179,0,255)
object_pet = ConfigItem("Pet", marker_name="Circle", color=pet_color, alternate_color=accent_color, marker_size=4.0)
GLOBAL_CONFIGS.add(object_pet)
enemy_pet_color = Color(255,255,0,255)
object_enemy_pet = ConfigItem("Enemy Pet", marker_name="Circle", color=enemy_pet_color, alternate_color=accent_color, marker_size=4.0)
GLOBAL_CONFIGS.add(object_enemy_pet)
minion_color = Color(0,128,93,255)
object_minion = ConfigItem("Minion", marker_name="Circle", color=minion_color, alternate_color=accent_color, marker_size=4.0)
GLOBAL_CONFIGS.add(object_minion)
npc_color = Color(153,255,153,255)
object_npc = ConfigItem("NPC", marker_name="Triangle", color=npc_color, alternate_color=accent_color, marker_size=8.0)
GLOBAL_CONFIGS.add(object_npc)
merchant_color = Color(153,255,153,255)
object_merchant = ConfigItem("Merchant", marker_name="Scale", color=merchant_color, alternate_color=accent_color, marker_size=8.0)
GLOBAL_CONFIGS.add(object_merchant)
minipet_color =  Color(153,255,153,255)
object_minipet = ConfigItem("Minipet", marker_name="Circle", color=minipet_color, alternate_color=accent_color, marker_size=2.0)
GLOBAL_CONFIGS.add(object_minipet)
default_color = Color(70,70,70,255)
object_default = ConfigItem("Default", marker_name="Circle", color=default_color, alternate_color=accent_color, marker_size=4.0)
GLOBAL_CONFIGS.add(object_default)
gadget_color = Color(165,135,75,255)
object_gadget = ConfigItem("Gadget", marker_name="SignPost", color=gadget_color, alternate_color=accent_color, marker_size=6.0)
GLOBAL_CONFIGS.add(object_gadget)
chest_color = Color(165,135,75,255)
object_chest = ConfigItem("Chest", marker_name="Lock", color=chest_color, alternate_color=accent_color, marker_size=6.0)
GLOBAL_CONFIGS.add(object_chest)
item_color = Color(200,200,0,255)
object_item = ConfigItem("Item", marker_name="Square", color=item_color, alternate_color=accent_color, marker_size=6.0)
GLOBAL_CONFIGS.add(object_item)


#region MISSIONMAP
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
        
        self.boundaries:tuple[float, float, float, float] = (0.0, 0.0, 0.0, 0.0)
        self.geometry = []
        self.renderer = DXOverlay()
        self.mega_zoom_renderer = DXOverlay()
        self.mega_zoom = 0.0
        self.map_origin = (0.0, 0.0)
        self.left_bound, self.top_bound, self.right_bound, self.bottom_bound = 0.0, 0.0, 0.0, 0.0
        self.cached_map_id = 0
        self.map_boundaries_by_map_id: dict[int, tuple[float, float, float, float]] = {}
        self.world_bounds_by_map_id: dict[int, tuple[float, float, float, float]] = {}
        self.pathing_geometry_built_by_map_id: dict[int, bool] = {}
        self._mask_enabled = False
        self._last_mission_map_coords: tuple[int, int, int, int] | None = None
        self._last_transform_signature: tuple | None = None
        
        self.pan_offset_x, self.pan_offset_y = 0.0, 0.0
        self.scale_x, self.scale_y = 1.0, 1.0
        self.zoom =  0.0
        self.mission_map_screen_center_x, self.mission_map_screen_center_y = 0.0, 0.0
        
        self.throttle_timer = ThrottledTimer(34) # every 4 frames 1000/60 = 16.67ms * 4 = 66.67ms
        self.agent_array = []
        self.Map_load_timer = Timer()
        self.Map_load_timer.Start()
        
        self.aggro_bubble_color = Utils.RGBToColor(255, 255, 255, 40)
        self.item_rarity_white_color = Color(225, 225, 225, 255)
        self.item_rarity_blue_color = Color(0, 170, 255, 255)
        self.item_rarity_green_color = Color(25, 200, 0, 255)
        self.item_rarity_gold_color = Color(225, 150, 0, 255)
        self.item_rarity_purple_color = Color(110, 65, 200, 255)
        
        self.target_accent_color = Color(235, 235, 50, 255)
        self.boss_glow_accent_color = Color(0, 200, 45, 255)
        
        self.ally_marker = GLOBAL_CONFIGS.get("Ally")
        self.player_marker = GLOBAL_CONFIGS.get("Player")
        self.players_marker = GLOBAL_CONFIGS.get("Players")
        self.neutral_marker = GLOBAL_CONFIGS.get("Neutral")
        self.enemy_marker = GLOBAL_CONFIGS.get("Enemy")
        self.enemy_pet_marker = GLOBAL_CONFIGS.get("Enemy Pet")
        self.minion_marker = GLOBAL_CONFIGS.get("Minion")
        self.npc_marker = GLOBAL_CONFIGS.get("NPC")
        self.minipet_marker = GLOBAL_CONFIGS.get("Minipet")
        self.gadget_marker = GLOBAL_CONFIGS.get("Gadget")
        self.item_marker = GLOBAL_CONFIGS.get("Item")
        self.pet_marker = GLOBAL_CONFIGS.get("Pet")
        self.default_marker = GLOBAL_CONFIGS.get("Default")
        self.chest_marker = GLOBAL_CONFIGS.get("Chest")
        self.merchant_marker = GLOBAL_CONFIGS.get("Merchant")
        
        self.renderer.mask.set_rectangle_mask(True)
        self.mega_zoom_renderer.mask.set_rectangle_mask(True)
        self.renderer.world_space.set_world_space(True)
        self.mega_zoom_renderer.world_space.set_world_space(True)
        self._mask_enabled = True
                   

    def update(self):  

        #if not self.throttle_timer.IsExpired():
        #    return
        #self.throttle_timer.Reset()    

        
        map_id = Map.GetMapID()
        if self.cached_map_id != map_id:
            self.cached_map_id = map_id
            self.map_boundaries_by_map_id.clear()
            self.world_bounds_by_map_id.clear()
            self.pathing_geometry_built_by_map_id.clear()
            self._last_mission_map_coords = None
            self._last_transform_signature = None

        if map_id in self.map_boundaries_by_map_id:
            self.boundaries = self.map_boundaries_by_map_id[map_id]
        else:
            self.boundaries = Map.GetMapBoundaries()
            self.map_boundaries_by_map_id[map_id] = self.boundaries

        if map_id in self.world_bounds_by_map_id:
            self.left_bound, self.top_bound, self.right_bound, self.bottom_bound = self.world_bounds_by_map_id[map_id]
        else:
            self.left_bound, self.top_bound, self.right_bound, self.bottom_bound = Map.GetMapWorldMapBounds()
            self.world_bounds_by_map_id[map_id] = (self.left_bound, self.top_bound, self.right_bound, self.bottom_bound)
        
        #self.geometry = Map.Pathing.GetComputedGeometry()
        #self.renderer.set_primitives(self.geometry, Color(255, 255, 255, 80).to_dx_color())
        #self.mega_zoom_renderer.set_primitives(self.geometry, Color(255, 255, 255, 100).to_dx_color())
        if not self.pathing_geometry_built_by_map_id.get(map_id, False):
            self.renderer.build_pathing_trapezoid_geometry(Color(255, 255, 255, 80).to_dx_color())
            self.mega_zoom_renderer.build_pathing_trapezoid_geometry(Color(255, 255, 255, 100).to_dx_color())
            self.pathing_geometry_built_by_map_id[map_id] = True
        
        coords = Map.MissionMap.GetMissionMapContentsCoords()
        coords_i = (int(coords[0]), int(coords[1]), int(coords[2]), int(coords[3]))
        if self._last_mission_map_coords != coords_i:
            self._last_mission_map_coords = coords_i
            self.left, self.top, self.right, self.bottom = coords_i
            self.width = self.right - self.left
            self.height = self.bottom - self.top
            self.renderer.mask.set_rectangle_mask_bounds(self.left, self.top, self.width, self.height)
            self.mega_zoom_renderer.mask.set_rectangle_mask_bounds(self.left, self.top, self.width, self.height)
        
        self.pan_offset_x, self.pan_offset_y = Map.MissionMap.GetPanOffset()
        self.scale_x, self.scale_y = Map.MissionMap.GetScale()

        self.zoom = Map.MissionMap.GetZoom()
        self.mission_map_screen_center_x, self.mission_map_screen_center_y = Map.MissionMap.GetCenter()

        transform_signature = (
            self.left, self.top, self.right, self.bottom,
            self.zoom, self.mega_zoom,
            self.pan_offset_x, self.pan_offset_y,
            self.scale_x, self.scale_y,
            self.mission_map_screen_center_x, self.mission_map_screen_center_y,
            self.boundaries,
            self.left_bound, self.top_bound, self.right_bound, self.bottom_bound,
        )
        if self._last_transform_signature != transform_signature:
            self._last_transform_signature = transform_signature
            self.left_world, self.top_world = RawScreenToRawGamePos(self.left, self.top, 
                                                                    self.zoom, self.mega_zoom,
                                                                    self.left_bound, self.top_bound, self.boundaries,
                                                                    self.pan_offset_x, self.pan_offset_y, self.scale_x, self.scale_y,
                                                                    self.mission_map_screen_center_x, self.mission_map_screen_center_y)
            self.right_world, self.bottom_world = RawScreenToRawGamePos(self.right, self.bottom, self.zoom, self.mega_zoom,
                                                                    self.left_bound, self.top_bound, self.boundaries,
                                                                    self.pan_offset_x, self.pan_offset_y, self.scale_x, self.scale_y,
                                                                    self.mission_map_screen_center_x, self.mission_map_screen_center_y)
            self.map_origin = RawGamePosToScreen(0.0, 0.0, 
                                                self.zoom, self.mega_zoom,
                                                self.left_bound, self.top_bound, self.boundaries,
                                                self.pan_offset_x, self.pan_offset_y, self.scale_x, self.scale_y,
                                                self.mission_map_screen_center_x, self.mission_map_screen_center_y)
            self.renderer.world_space.set_pan(self.map_origin[0], self.map_origin[1])
            self.mega_zoom_renderer.world_space.set_pan(self.map_origin[0], self.map_origin[1])
            zoom = Map.MissionMap.GetAdjustedZoom(self.zoom, zoom_offset=self.mega_zoom)
            self.renderer.world_space.set_zoom(zoom/100.0)
            self.mega_zoom_renderer.world_space.set_zoom(zoom/100.0)
            self.renderer.world_space.set_scale(self.scale_x)
            self.mega_zoom_renderer.world_space.set_scale(self.scale_x)

        
        self.player_agent_id = Player.GetAgentID()
        self.player_target_id = Player.GetTargetID()
        
        
        self.player_x, self.player_y = Player.GetXY()
        self.player_screen_x, self.player_screen_y = RawGamePosToScreen(self.player_x, self.player_y, 
                                                    self.zoom, self.mega_zoom,
                                                    self.left_bound, self.top_bound, self.boundaries,
                                                    self.pan_offset_x, self.pan_offset_y, self.scale_x, self.scale_y,
                                                    self.mission_map_screen_center_x, self.mission_map_screen_center_y)
        
        # aC  ---
        io = PyImGui.get_io()
        mx, my = io.mouse_pos_x, io.mouse_pos_y   # screen coords

        LEFT = 0
        if PyImGui.is_mouse_clicked(LEFT) and not io.want_capture_mouse:
            if self.left <= mx <= self.right and self.top <= my <= self.bottom:
                gx, gy = RawScreenToRawGamePos(
                    mx, my,
                    self.zoom, self.mega_zoom,
                    self.left_bound, self.top_bound, self.boundaries,
                    self.pan_offset_x, self.pan_offset_y,
                    self.scale_x, self.scale_y,
                    self.mission_map_screen_center_x, self.mission_map_screen_center_y
                )
                self.last_click_x, self.last_click_y = gx, gy
        # aC  ---

        if not self._mask_enabled:
            self.renderer.mask.set_rectangle_mask(True)
            self.mega_zoom_renderer.mask.set_rectangle_mask(True)
            self.renderer.world_space.set_world_space(True)
            self.mega_zoom_renderer.world_space.set_world_space(True)
            self._mask_enabled = True
mission_map = MissionMap()

#endregion

#region DRAWING
def DrawFrame():
    global mission_map
    def _get_agent_xy_from_obj(agent_obj: AgentStruct):
        x,y = RawGamePosToScreen(agent_obj.pos.x, agent_obj.pos.y, 
                                 mission_map.zoom, mission_map.mega_zoom,
                                 mission_map.left_bound, mission_map.top_bound,
                                 mission_map.boundaries, 
                                 mission_map.pan_offset_x, mission_map.pan_offset_y,
                                 mission_map.scale_x, mission_map.scale_y,
                                 mission_map.mission_map_screen_center_x, mission_map.mission_map_screen_center_y)
        return x,y
    
    def _get_alternate_color(agent_id):
        if mission_map.player_target_id == agent_id:
            accent_color = mission_map.target_accent_color
            size_offset =2.0
            return accent_color, size_offset
        return mission_map.default_marker.AlternateColor, 0.0

    def _begin_imgui_draw_window() -> bool:
        PyImGui.set_next_window_pos(mission_map.left, mission_map.top)
        PyImGui.set_next_window_size(mission_map.width, mission_map.height)
        flags = (
            PyImGui.WindowFlags.NoTitleBar |
            PyImGui.WindowFlags.NoScrollbar |
            PyImGui.WindowFlags.NoMove |
            PyImGui.WindowFlags.NoSavedSettings |
            PyImGui.WindowFlags.NoBackground |
            PyImGui.WindowFlags.NoInputs
        )
        PyImGui.push_style_var2(ImGui.ImGuiStyleVar.WindowPadding, 0.0, 0.0)
        PyImGui.push_style_var2(ImGui.ImGuiStyleVar.FramePadding, 0.0, 0.0)
        return PyImGui.begin("##mission_map_imgui_drawlist", flags)

    def _end_imgui_draw_window() -> None:
        PyImGui.end()
        PyImGui.pop_style_var(2)

    def _draw_circle_stroke(x: float, y: float, radius: float, color: int, segments: int, thickness: float) -> None:
        PyImGui.draw_list_add_circle(x, y, radius, color, segments, thickness)

    def _draw_circle_fill(x: float, y: float, radius: float, color: int, segments: int) -> None:
        PyImGui.draw_list_add_circle_filled(x, y, radius, color, segments)

    def _segments_for_radius(radius: float) -> int:
        if radius < 18:
            return 12
        if radius < 35:
            return 16
        if radius < 70:
            return 24
        if radius < 130:
            return 32
        if radius < 220:
            return 48
        return 64
    
    def _draw_aggro_bubble():
        radius = aggro_radius_px
        color = aggro_bubble_color
        segments = _segments_for_radius(radius)
        _draw_circle_stroke(mission_map.player_screen_x, mission_map.player_screen_y, radius-2, color, segments, 4.0)
        _draw_circle_fill(mission_map.player_screen_x, mission_map.player_screen_y, radius, color, segments)
        
    def _draw_terrain(zoom):
        if zoom >3.5:
            mission_map.mega_zoom_renderer.DrawQuadFilled(mission_map.left,mission_map.top, mission_map.right,mission_map.top, mission_map.right,mission_map.bottom, mission_map.left,mission_map.bottom, color=Utils.RGBToColor(75,75,75,200))
            mission_map.mega_zoom_renderer.render()
        else:
            mission_map.renderer.render()
            
    def _draw_compass_range(zoom):
        radius = compass_radius_px
        color = aggro_bubble_color
        segments = _segments_for_radius(radius)
        _draw_circle_stroke(mission_map.player_screen_x, mission_map.player_screen_y, radius, compass_outline_color, segments, 1.0)
        _draw_circle_stroke(mission_map.player_screen_x, mission_map.player_screen_y, radius-(2.85*zoom), color, segments, (5.7*zoom))
    
    #terrain 
    zoom = mission_map.zoom + mission_map.mega_zoom
    aggro_bubble_color = mission_map.aggro_bubble_color
    compass_outline_color = Utils.RGBToColor(0, 0, 0, 255)
    aggro_radius_px = RawGwinchToPixels(Range.Earshot.value, mission_map.zoom, mission_map.mega_zoom, mission_map.scale_x)
    compass_radius_px = RawGwinchToPixels(Range.Compass.value, mission_map.zoom, mission_map.mega_zoom, mission_map.scale_x)
    spirit_range_radius_px = {
        Range.Spirit.value: RawGwinchToPixels(Range.Spirit.value, mission_map.zoom, mission_map.mega_zoom, mission_map.scale_x),
        Range.Area.value: RawGwinchToPixels(Range.Area.value, mission_map.zoom, mission_map.mega_zoom, mission_map.scale_x),
        Range.Earshot.value: RawGwinchToPixels(Range.Earshot.value, mission_map.zoom, mission_map.mega_zoom, mission_map.scale_x),
    }
    _draw_terrain(zoom)    
    imgui_draw_window_open = _begin_imgui_draw_window()
    if imgui_draw_window_open:
        _draw_aggro_bubble()
        _draw_compass_range(zoom)
    
      
    neutral_array = AgentArray.GetNeutralArray()
    minion_array = AgentArray.GetMinionArray()
    spirit_pet_array = AgentArray.GetSpiritPetArray()
    enemy_array = AgentArray.GetEnemyArray()
    ally_array = AgentArray.GetAllyArray()
    npc_minipet_array = AgentArray.GetNPCMinipetArray()
    for agent_id in neutral_array:
        obj = Agent.GetAgentByID(agent_id)
        if not obj: continue
        living = obj.GetAsAgentLiving()
        if not living:
            continue
        if not (living.hp > 0.0 and not (living.is_dead or living.is_dead_by_type_map)):
            continue
        x,y = _get_agent_xy_from_obj(obj)
        rotation_angle = obj.rotation_angle
        marker = mission_map.neutral_marker
        alternate_color, size = _get_alternate_color(agent_id)
        Marker(marker.Marker, marker.Color, alternate_color, x, y, marker.size + size, offset_angle=rotation_angle).draw()

    for agent_id in minion_array:
        obj = Agent.GetAgentByID(agent_id)
        if not obj: continue
        living = obj.GetAsAgentLiving()
        if not living:
            continue
        if not (living.hp > 0.0 and not (living.is_dead or living.is_dead_by_type_map)):
            continue
        x,y = _get_agent_xy_from_obj(obj)
        rotation_angle = obj.rotation_angle
        marker = mission_map.minion_marker
        alternate_color, size = _get_alternate_color(agent_id)
        Marker(marker.Marker, marker.Color, alternate_color, x, y, marker.size + size, offset_angle=rotation_angle).draw()  
            
    for agent_id in spirit_pet_array:
        obj = Agent.GetAgentByID(agent_id)
        if not obj: continue
        living = obj.GetAsAgentLiving()
        if not living:
            continue
        if not (living.hp > 0.0 and not (living.is_dead or living.is_dead_by_type_map)):
            continue
        x,y = _get_agent_xy_from_obj(obj)
        rotation_angle = obj.rotation_angle
        if not living.is_spawned:
               marker = mission_map.pet_marker
        else:
            model_id = living.player_number
            spirit_name = get_spirit_name(model_id)
            if spirit_name == "Unknown":
                marker = mission_map.neutral_marker
            else:
                marker = GLOBAL_CONFIGS.get(spirit_name)
                area = Range.Spirit.value
                if model_id in AREA_SPIRIT_MODELS:
                    area = Range.Area.value
                if model_id in EARSHOT_SPIRIT_MODELS:
                    area = Range.Earshot.value
                spirit_area = spirit_range_radius_px.get(area, spirit_range_radius_px[Range.Spirit.value])
                aura_color = ColorToIntCached(marker.AlternateColor)
                aura_segments = _segments_for_radius(spirit_area)
            
                _draw_circle_stroke(x, y, spirit_area-2, aura_color, aura_segments, 1.0)
                _draw_circle_fill(x, y, spirit_area, aura_color, aura_segments)
                
        alternate_color, size = _get_alternate_color(agent_id)
        Marker(marker.Marker, marker.Color, alternate_color, x, y, marker.size + size, offset_angle=rotation_angle).draw()
        
    for agent_id in enemy_array:
        obj = Agent.GetAgentByID(agent_id)
        if not obj: continue
        living = obj.GetAsAgentLiving()
        if not living:
            continue
        if not (living.hp > 0.0 and not (living.is_dead or living.is_dead_by_type_map)):
            continue
        x,y = _get_agent_xy_from_obj(obj)
        rotation_angle = obj.rotation_angle
        model_id = living.player_number
        if not living.is_spawned:
            if model_id in PET_MODEL_IDS:
                marker = mission_map.enemy_pet_marker
            else:
                marker = mission_map.enemy_marker
        else:
            spirit_name = get_spirit_name(model_id)
            if spirit_name == "Unknown":
                marker = mission_map.enemy_marker
            else:
                marker = GLOBAL_CONFIGS.get(spirit_name)
                area = Range.Spirit.value
                if model_id in AREA_SPIRIT_MODELS:
                    area = Range.Area.value
                if model_id in EARSHOT_SPIRIT_MODELS:
                    area = Range.Earshot.value
                    
                enemy_marker = mission_map.enemy_marker
                shifted_color = marker.Color.shift(enemy_marker.Color, 0.55)
                shifted_color.set_a(int(shifted_color.get_a() * 0.25))
                    
                spirit_area = spirit_range_radius_px.get(area, spirit_range_radius_px[Range.Spirit.value])
                shifted_color_dx = ColorToIntCached(shifted_color)
                aura_segments = _segments_for_radius(spirit_area)
            
                _draw_circle_stroke(x, y, spirit_area-2, shifted_color_dx, aura_segments, 1.0)
                _draw_circle_fill(x, y, spirit_area, shifted_color_dx, aura_segments)
                
        alternate_color, size = _get_alternate_color(agent_id)
        Marker(marker.Marker, marker.Color, alternate_color, x, y, marker.size + size, offset_angle=rotation_angle).draw()
        
      

    for agent_id in ally_array:
        obj = Agent.GetAgentByID(agent_id)
        if not obj: continue
        living = obj.GetAsAgentLiving()
        if not living:
            continue
        if not (living.hp > 0.0 and not (living.is_dead or living.is_dead_by_type_map)):
            continue
        x,y = _get_agent_xy_from_obj(obj)
        rotation_angle = obj.rotation_angle
        if living.is_npc:
            marker = mission_map.npc_marker
        else:
            marker = mission_map.players_marker  
        alternate_color, size = _get_alternate_color(agent_id)
        Marker(marker.Marker, marker.Color, alternate_color, x, y, marker.size + size, offset_angle=rotation_angle).draw() 
     
    if Player.IsPlayerLoaded():
        agent_id = Player.GetAgentID()
        obj = Agent.GetAgentByID(agent_id)
        if obj:
            living = obj.GetAsAgentLiving()
        else:
            living = None
        if living and (living.hp > 0.0 and not (living.is_dead or living.is_dead_by_type_map)):
            if obj is None:
                return
            x,y = _get_agent_xy_from_obj(obj)
            rotation_angle = obj.rotation_angle
            marker = mission_map.player_marker
            alternate_color, size = _get_alternate_color(agent_id)
            Marker(marker.Marker, marker.Color, alternate_color, x, y, marker.size + size, offset_angle=rotation_angle).draw()
     
     
        
    for agent_id in npc_minipet_array:
        obj = Agent.GetAgentByID(agent_id)
        if not obj: continue
        living = obj.GetAsAgentLiving()
        if not living:
            continue
        if not (living.hp > 0.0 and not (living.is_dead or living.is_dead_by_type_map)):
            continue
        x,y = _get_agent_xy_from_obj(obj)
        rotation_angle = obj.rotation_angle
        level = living.level
        if level > 1:
            agent_name = Agent.GetNameByID(agent_id)
            if "MERCHANT" in agent_name.upper():
                marker = mission_map.merchant_marker
            else:
                marker = mission_map.npc_marker   
        else: 
            marker = mission_map.minipet_marker     
        alternate_color, size = _get_alternate_color(agent_id)
        Marker(marker.Marker, marker.Color, alternate_color, x, y, marker.size + size, offset_angle=rotation_angle).draw()
        
    for agent_id in AgentArray.GetGadgetArray():
        obj = Agent.GetAgentByID(agent_id)
        if not obj: continue
        gadget = obj.GetAsAgentGadget()
        if not gadget:
            continue
        x,y = _get_agent_xy_from_obj(obj)
        rotation_angle = obj.rotation_angle
        gadget_id = gadget.gadget_id
        if gadget_id in CHEST_GADGET_IDS:
            marker = mission_map.chest_marker
        else:
            marker = mission_map.gadget_marker
            
        alternate_color, size = _get_alternate_color(agent_id)
        Marker(marker.Marker, marker.Color, alternate_color, x, y, marker.size + size, offset_angle=rotation_angle).draw()
    for agent_id in AgentArray.GetItemArray():
        obj = Agent.GetAgentByID(agent_id)
        if not obj: continue
        item_agent = obj.GetAsAgentItem()
        if not item_agent:
            continue
        x,y = _get_agent_xy_from_obj(obj)
        rotation_angle = obj.rotation_angle
        marker = mission_map.item_marker
        
        item_id = item_agent.item_id
        item = GLOBAL_CACHE.Item.raw_item_array.get_item_by_id(item_id)
        item_rarity = item.rarity if item is not None else 0
        if item_rarity == Rarity.Blue.value:
            marker.Color = mission_map.item_rarity_blue_color
        elif item_rarity == Rarity.Purple.value:
            marker.Color = mission_map.item_rarity_purple_color
        elif item_rarity == Rarity.Gold.value:
            marker.Color = mission_map.item_rarity_gold_color
        elif item_rarity == Rarity.Green.value:
            marker.Color = mission_map.item_rarity_green_color
        else:
            marker.Color = mission_map.item_rarity_white_color
        
        alternate_color, size = _get_alternate_color(agent_id)
        Marker(marker.Marker, marker.Color, alternate_color, x, y, marker.size + size, offset_angle=rotation_angle).draw()
        
    _end_imgui_draw_window()
               
def tooltip():
    PyImGui.begin_tooltip()

    # Title
    title_color = Color(255, 200, 100, 255)
    ImGui.push_font("Regular", 20)
    PyImGui.text_colored("Mission Map +", title_color.to_tuple_normalized())
    ImGui.pop_font()
    PyImGui.spacing()
    PyImGui.separator()

    # Description
    #ellaborate a better description 
    PyImGui.text("Misison Map + enhances the in-game mission map with additional features")
    PyImGui.text("and functionalities to improve your gameplay experience.")

    
    PyImGui.spacing()

    # Features
    PyImGui.text_colored("Features:", title_color.to_tuple_normalized())
    PyImGui.bullet_text("Enhanced Map Visualization")
    PyImGui.bullet_text("Customizable Markers")
    PyImGui.bullet_text("Zoom Functionality")
    PyImGui.bullet_text("Coordinate Display")
    PyImGui.bullet_text("Agent tracking")

    PyImGui.spacing()
    PyImGui.separator()
    PyImGui.spacing()

    # Credits
    PyImGui.text_colored("Credits:", title_color.to_tuple_normalized())
    PyImGui.bullet_text("Developed by Apo")
    PyImGui.bullet_text("Contributors: Searinox, Dharmantrix, aC")

    PyImGui.end_tooltip()

def draw():  
    try:  
        if not Routines.Checks.Map.MapValid():
            mission_map.geometry = [] 
            mission_map.Map_load_timer.Reset()
            return
        
        #if not mission_map.Map_load_timer.HasElapsed(1000):
        #    return
        
        if Map.MissionMap.IsWindowOpen():
            mission_map.update()
            DrawFrame()
            FloatingCoordsStrip(
                mission_map.left,
                mission_map.top,
                mission_map.last_click_x,
                mission_map.last_click_y,
                Color(255, 255, 255, 255),
                width=mission_map.width,
                margin=8,
                label="Coords"
            )
            if mission_map.zoom >= 3.5:
                    mission_map.mega_zoom = FloatingSlider("Mega Zoom", mission_map.mega_zoom, mission_map.left, mission_map.bottom-27, 0.0, 15.0, Color(255, 255, 255, 255))
            else:
                mission_map.mega_zoom = 0.0 
    
    except Exception as e:
        import Py4GW
        Py4GW.Console.Log("Mission Map +", str(e), Py4GW.Console.MessageType.Error)

        
    
if __name__ == "__main__":
    draw()
