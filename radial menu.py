import PyImGui
import math

from Py4GWCoreLib.py4gwcorelib_src.Color import Color, ColorPalette
from dataclasses import dataclass
from abc import ABC, abstractmethod

class Shape(ABC):
    def __init__(self, color: int = 0xFFFFFFFF):
        self.color = color
        self.hovered_color = 0xFFFFFFFF
        self.is_visible = True
        self.is_hovered = False

    @abstractmethod
    def draw(self):
        """Each shape must implement its own ImGui drawing logic."""
        pass

    @abstractmethod
    def update_hover(self, mouse_x: float, mouse_y: float):
        """Each shape must implement its own mathematical hitbox."""
        pass
    
    def is_clicked(self, button: int = 0) -> bool:
        """
        Concrete method inherited by all shapes.
        Returns True if the shape is hovered and the specific mouse button is clicked.
        0: Left, 1: Right, 2: Middle
        """
        if self.is_visible and self.is_hovered:
            return PyImGui.is_mouse_clicked(button)
        return False

class RingSector(Shape):
    def __init__(self, x, y, inner_r, outer_r, start_deg, end_deg, color, hovered_color=0xFFFFFFFF, outline_col=0xFF000000):
        super().__init__(color)
        self.hovered_color = hovered_color
        self.center = [x, y]
        self.inner_r = inner_r
        self.outer_r = outer_r
        self.start_deg = start_deg
        self.end_deg = end_deg
        self.outline_col = outline_col
        self.border_thickness = 2.0

    def update_hover(self, mouse_x, mouse_y):
        dx, dy = mouse_x - self.center[0], mouse_y - self.center[1]
        dist_sq = dx*dx + dy*dy
        
        # Distance check
        if not (self.inner_r**2 <= dist_sq <= self.outer_r**2):
            self.is_hovered = False
            return
            
        # Angle check
        angle = math.degrees(math.atan2(dy, dx)) % 360
        if self.start_deg < self.end_deg:
            self.is_hovered = self.start_deg <= angle <= self.end_deg
        else:
            self.is_hovered = angle >= self.start_deg or angle <= self.end_deg

    def draw(self):
        if not self.is_visible: return
        
        if self.is_hovered:
            draw_col = self.hovered_color
        else:
            draw_col = self.color
            
        s_rad, e_rad = math.radians(self.start_deg), math.radians(self.end_deg)
        
        # Fill
        thickness = self.outer_r - self.inner_r
        mid_r = self.inner_r + (thickness / 2)
        PyImGui.path_clear()
        PyImGui.path_arc_to(self.center[0], self.center[1], mid_r, s_rad, e_rad, 64)
        PyImGui.path_stroke(draw_col, False, thickness)
        
        # Borders (Curved)
        PyImGui.path_clear()
        PyImGui.path_arc_to(self.center[0], self.center[1], self.outer_r, s_rad, e_rad, 64)
        PyImGui.path_stroke(self.outline_col, False, self.border_thickness)
        
        PyImGui.path_clear()
        PyImGui.path_arc_to(self.center[0], self.center[1], self.inner_r, s_rad, e_rad, 64)
        PyImGui.path_stroke(self.outline_col, False, self.border_thickness)

        # Side Lines
        if abs(self.end_deg - self.start_deg) < 360.0:
            for rad in [s_rad, e_rad]:
                PyImGui.path_clear()
                PyImGui.path_line_to(self.center[0] + math.cos(rad) * self.inner_r, 
                                     self.center[1] + math.sin(rad) * self.inner_r)
                PyImGui.path_line_to(self.center[0] + math.cos(rad) * self.outer_r, 
                                     self.center[1] + math.sin(rad) * self.outer_r)
                PyImGui.path_stroke(self.outline_col, False, self.border_thickness)
                
class Circle(Shape):
    def __init__(self, x, y, radius, color, hovered_color,outline_col=0xFF000000):
        super().__init__(color)
        self.center = [float(x), float(y)]
        self.radius = float(radius)
        self.outline_col = outline_col
        self.border_thickness = 2.0
        self.segments = 64
        self.hovered_color = hovered_color

    def update_hover(self, mouse_x: float, mouse_y: float):
        dx, dy = mouse_x - self.center[0], mouse_y - self.center[1]
        self.is_hovered = (dx**2 + dy**2) <= (self.radius**2)

    def draw(self):
        if not self.is_visible: return
        
        if self.is_hovered:
            draw_col = self.hovered_color
        else:
            draw_col = self.color
        
        # Draw filled circle primitive
        PyImGui.draw_list_add_circle_filled(
            self.center[0], self.center[1], 
            self.radius, draw_col, self.segments
        )
        
        # Draw outline primitive
        if self.border_thickness > 0:
            PyImGui.draw_list_add_circle(
                self.center[0], self.center[1], 
                self.radius, self.outline_col, 
                self.segments, self.border_thickness
            )
    
class Rectangle(Shape):
    def __init__(self, x, y, width, height, color, hovered_color,outline_col=0xFF000000, rounding=0.0):
        super().__init__(color)
        self.pos = [float(x), float(y)]
        self.size = [float(width), float(height)]
        self.outline_col = outline_col
        self.rounding = rounding
        self.border_thickness = 2.0
        self.hovered_color = hovered_color

    def update_hover(self, mouse_x: float, mouse_y: float):
        # AABB (Axis-Aligned Bounding Box) detection
        self.is_hovered = (self.pos[0] <= mouse_x <= self.pos[0] + self.size[0] and 
                          self.pos[1] <= mouse_y <= self.pos[1] + self.size[1])

    def draw(self):
        if not self.is_visible: return
        
        if self.is_hovered:
            draw_col = self.hovered_color
        else:
            draw_col = self.color
            
        x2, y2 = self.pos[0] + self.size[0], self.pos[1] + self.size[1]
        
        # Draw filled rect
        PyImGui.draw_list_add_rect_filled(
            self.pos[0], self.pos[1], x2, y2, 
            draw_col, self.rounding, 15 # 15 = all corners
        )
        
        # Draw outline
        PyImGui.draw_list_add_rect(
            self.pos[0], self.pos[1], x2, y2, 
            self.outline_col, self.rounding, 15, self.border_thickness
        )    
        
class Triangle(Shape):
    def __init__(self, p1, p2, p3, color, hovered_color, outline_col=0xFF000000):
        super().__init__(color)
        self.points = [p1, p2, p3] # Each point is [x, y]
        self.outline_col = outline_col
        self.border_thickness = 2.0
        self.hovered_color = hovered_color
        
    def update_hover(self, mouse_x: float, mouse_y: float):
        # Point-in-triangle test (Sign method)
        def sign(p1, p2, p3):
            return (p1[0] - p3[0]) * (p2[1] - p3[1]) - (p2[0] - p3[0]) * (p1[1] - p3[1])

        d1 = sign([mouse_x, mouse_y], self.points[0], self.points[1])
        d2 = sign([mouse_x, mouse_y], self.points[1], self.points[2])
        d3 = sign([mouse_x, mouse_y], self.points[2], self.points[0])

        has_neg = (d1 < 0) or (d2 < 0) or (d3 < 0)
        has_pos = (d1 > 0) or (d2 > 0) or (d3 > 0)
        self.is_hovered = not (has_neg and has_pos)

    def draw(self):
        if not self.is_visible: return
        
        draw_col = 0xFFFFFFFF if self.is_hovered else self.color
        p = self.points
        
        PyImGui.draw_list_add_triangle_filled(
            p[0][0], p[0][1], p[1][0], p[1][1], p[2][0], p[2][1], draw_col
        )
        PyImGui.draw_list_add_triangle(
            p[0][0], p[0][1], p[1][0], p[1][1], p[2][0], p[2][1], 
            self.outline_col, self.border_thickness
        )


#region old ring
color_pick = ColorPalette.GetColor("Green")

def draw_radial_interaction_layer():
    global color_pick
        
    center_x, center_y = 400,300
    degree_start, degree_end = 2.0, 88.0
    inner_radius, outer_radius = 50, 100
    color = color_pick.to_color()
    hovered_color = ColorPalette.GetColor("LightBlue").to_color()
    
    margin = 20.0 
    diameter = (outer_radius * 2) + margin
    
    x_left = center_x - outer_radius - (margin / 2)
    y_top = center_y - outer_radius - (margin / 2)

    PyImGui.set_next_window_pos(x_left, y_top)
    PyImGui.set_next_window_size(diameter, diameter)
    
    flags = (PyImGui.WindowFlags.NoTitleBar | 
             PyImGui.WindowFlags.NoResize | 
             PyImGui.WindowFlags.NoMove | 
             PyImGui.WindowFlags.NoBackground |
             PyImGui.WindowFlags.NoScrollbar)
    
    if PyImGui.begin("##RadialInteractionLayer", flags):
        io = PyImGui.get_io()
        mouse_x, mouse_y = io.mouse_pos_x, io.mouse_pos_y
        
        circle = Circle(center_x, center_y, inner_radius -4, color, hovered_color)
        circle.update_hover(mouse_x, mouse_y)
        circle.draw()

        sector = RingSector(center_x,center_y,float(inner_radius), float(outer_radius),degree_start,degree_end,color, hovered_color)
        sector.update_hover(mouse_x, mouse_y)
        sector.draw()
        
        degree_start, degree_end = 92.0, 178.0
        
        sector2 = RingSector(center_x,center_y,float(inner_radius),float(outer_radius),degree_start,degree_end,color, hovered_color)
        sector2.update_hover(mouse_x, mouse_y)
        sector2.draw()
        
        degree_start, degree_end = 182.0, 268.0
        sector3 = RingSector(center_x,center_y,float(inner_radius),float(outer_radius),degree_start,degree_end,color, hovered_color)
        sector3.update_hover(mouse_x, mouse_y)
        sector3.draw()
        
        degree_start, degree_end = 272.0, 358.0
        sector4 = RingSector(center_x,center_y,float(inner_radius),float(outer_radius),degree_start,degree_end,color, hovered_color)
        sector4.update_hover(mouse_x, mouse_y)
        sector4.draw()
        
    PyImGui.end()
    
def draw_rectangle_layer():
    global color_pick
    
    # 1. Configuration (Matching your style)
    color = color_pick.to_color()
    hovered_color = ColorPalette.GetColor("LightBlue").to_color()
    
    left = 500
    top = 250
    width = 100
    height = 100
    margin = 10.0 # Small margin to ensure borders aren't clipped
    
    # 2. Setup the window specifically for this rectangle
    # This prevents the "narrow" clipping issue by making the window wide enough
    PyImGui.set_next_window_pos(left - (margin / 2), top - (margin / 2))
    PyImGui.set_next_window_size(width + margin, height + margin)
    
    flags = (PyImGui.WindowFlags.NoTitleBar | 
             PyImGui.WindowFlags.NoResize | 
             PyImGui.WindowFlags.NoMove | 
             PyImGui.WindowFlags.NoBackground |
             PyImGui.WindowFlags.NoScrollbar)
    
    if PyImGui.begin("##RectangleInteractionLayer", flags):
        io = PyImGui.get_io()
        mouse_x, mouse_y = io.mouse_pos_x, io.mouse_pos_y
        
        # 3. Create and process the rectangle
        rect = Rectangle(left, top, width, height, color, hovered_color)
        rect.update_hover(mouse_x, mouse_y)
        
        if rect.is_clicked(0):
            print(f"Rectangle clicked at {left}, {top}")
            
        rect.draw()
        
    PyImGui.end()
    
def draw_triangle_layer():
    global color_pick
    
    color = color_pick.to_color()
    hovered_color = ColorPalette.GetColor("LightBlue").to_color()

    # Define 3 points for the triangle
    p1 = [550, 140]
    p2 = [500, 240]
    p3 = [600, 240]
    
    # Calculate bounding box for the window
    xs = [p1[0], p2[0], p3[0]]
    ys = [p1[1], p2[1], p3[1]]
    left, top = min(xs), min(ys)
    width, height = max(xs) - left, max(ys) - top
    
    margin = 10.0
    PyImGui.set_next_window_pos(left - (margin / 2), top - (margin / 2))
    PyImGui.set_next_window_size(width + margin, height + margin)
    
    flags = (PyImGui.WindowFlags.NoTitleBar | 
             PyImGui.WindowFlags.NoResize | 
             PyImGui.WindowFlags.NoMove | 
             PyImGui.WindowFlags.NoBackground |
             PyImGui.WindowFlags.NoScrollbar)
    
    if PyImGui.begin("##TriangleInteractionLayer", flags):
        io = PyImGui.get_io()
        mouse_x, mouse_y = io.mouse_pos_x, io.mouse_pos_y
        
        tri = Triangle(p1, p2, p3, color, hovered_color)
        tri.update_hover(mouse_x, mouse_y)
        
        if tri.is_clicked(0):
            print("Triangle clicked!")
            
        tri.draw()
        
    PyImGui.end()

def draw_window():
    global color_pick
    if PyImGui.begin("Radial Menu Example"):

        
        current_color_normalized = color_pick.color_tuple 
        new_color_tuple = PyImGui.color_edit4("Color", current_color_normalized)
        if new_color_tuple != current_color_normalized:
            color_pick = Color.from_tuple_normalized(new_color_tuple)
        
    PyImGui.end()

    draw_radial_interaction_layer()
    draw_rectangle_layer() 
    draw_triangle_layer()
    
    
def main():
    draw_window()

if __name__ == "__main__":
    main()
