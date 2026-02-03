
from enum import IntEnum
from typing import Optional

import PyImGui

from Py4GWCoreLib.ImGui_src.ImGuisrc import ImGui
from Py4GWCoreLib.py4gwcorelib_src.Color import Color


class Region:
    class ResizeDirection(IntEnum):
        NONE = 0
        TOP = 1
        BOTTOM = 2
        LEFT = 4
        RIGHT = 8
        TOP_LEFT = TOP | LEFT
        TOP_RIGHT = TOP | RIGHT
        BOTTOM_LEFT = BOTTOM | LEFT
        BOTTOM_RIGHT = BOTTOM | RIGHT

    def __init__(self, x: int = 0, y: int = 0, w: int = 300, h: int = 200, name: str = "Region", account: str = "", main: bool = False, color: Optional[Color] = None):
        self.x, self.y, self.w, self.h = x, y, w, h
        self.color = color if color else Color.random()

        self.selected = False
        self.dragging = False
        self.resizing = False
        self.resize_grab_size = 12
        self.resize_direction = Region.ResizeDirection.NONE

        self.name: str = name
        self.account: str = account
        self.main: bool = main

    def to_dict(self) -> dict:
        return {
            "x": self.x,
            "y": self.y,
            "w": self.w,
            "h": self.h,
            "name": self.name,
            "account": self.account,
            "main": self.main,
            "color": {
                "r": self.color.r,
                "g": self.color.g,
                "b": self.color.b,
                "a": self.color.a,
            }
        }

    @staticmethod
    def from_dict(data: dict, number: int = 0) -> "Region":
        color_data = data.get("color", {})
        color = Color(
            r=color_data.get("r", 255),
            g=color_data.get("g", 255),
            b=color_data.get("b", 255),
            a=color_data.get("a", 255)
        )

        return Region(
            x=data.get("x", 0),
            y=data.get("y", 0),
            w=data.get("w", 300),
            h=data.get("h", 200),
            name=data.get("name", f"Region{(number if number > 0 else '')}"),
            account=data.get("account", ""),
            main=data.get("main", False),
            color=color
        )

    def rect(self, scale: float = 1.0) -> tuple[float, float, float, float]:
        return (self.x * scale, self.y * scale, (self.x + self.w) * scale, (self.y + self.h) * scale)

    def contains(self, mx, my, scale: float = 1.0):
        x1, y1, x2, y2 = self.rect(scale)
        return x1 <= mx <= x2 and y1 <= my <= y2

    def on_resize_zone(self, mx, my, scale: float = 1.0) -> "Region.ResizeDirection":
        x1, y1, x2, y2 = self.rect(scale)
        grab = self.resize_grab_size

        if x1 <= mx <= x1 + grab and y1 <= my <= y1 + grab:
            return Region.ResizeDirection.TOP_LEFT

        if x2 - grab <= mx <= x2 and y1 <= my <= y1 + grab:
            return Region.ResizeDirection.TOP_RIGHT

        if x1 <= mx <= x1 + grab and y2 - grab <= my <= y2:
            return Region.ResizeDirection.BOTTOM_LEFT

        if x2 - grab <= mx <= x2 and y2 - grab <= my <= y2:
            return Region.ResizeDirection.BOTTOM_RIGHT

        if x1 <= mx <= x1 + grab:
            return Region.ResizeDirection.LEFT

        elif x2 - grab <= mx <= x2:
            return Region.ResizeDirection.RIGHT

        elif y1 <= my <= y1 + grab:
            return Region.ResizeDirection.TOP

        elif y2 - grab <= my <= y2:
            return Region.ResizeDirection.BOTTOM

        return Region.ResizeDirection.NONE

    def draw(self, origin_x: float, origin_y: float, scale: float = 1.0):
        text_display = f"{self.name if not self.account else self.account}"

        # Compute rectangle coordinates and size
        x1, y1, x2, y2 = self.rect(scale)
        width = x2 - x1
        height = y2 - y1

        # Apply origin offset
        x1 += origin_x
        y1 += origin_y
        x2 += origin_x
        y2 += origin_y

        # Background + border
        PyImGui.draw_list_add_rect_filled(
            x1, y1, x2, y2, self.color.opacify(0.15).color_int, 0, 0
        )
        PyImGui.draw_list_add_rect(
            x1, y1, x2, y2, self.color.color_int, 0, 0, 1
        )

        # Resize handles
        # Top-left
        PyImGui.draw_list_add_triangle_filled(
            x1, y1 + self.resize_grab_size,
            x1, y1,
            x1 + self.resize_grab_size, y1,
            self.color.opacify(0.5).color_int
        )

        # Top-right
        PyImGui.draw_list_add_triangle_filled(
            x2 - 1 - self.resize_grab_size, y1,
            x2 - 1, y1,
            x2 - 1, y1 + self.resize_grab_size,
            self.color.opacify(0.5).color_int
        )

        # Bottom-left
        PyImGui.draw_list_add_triangle_filled(
            x1, y2 - 1 - self.resize_grab_size,
            x1, y2 - 1,
            x1 + self.resize_grab_size, y2 - 1,
            self.color.opacify(0.5).color_int
        )

        # Bottom-right
        PyImGui.draw_list_add_triangle_filled(
            x2 - 1 - self.resize_grab_size, y2 - 1,
            x2 - 1, y2 - 1,
            x2 - 1, y2 - 1 - self.resize_grab_size,
            self.color.opacify(0.5).color_int
        )

        # --- Improved font scaling ---
        # Base font size (e.g. 13–16 depending on current ImGui font)
        start_font_size = PyImGui.get_text_line_height()

        # Measure text at base font size
        base_text_size = PyImGui.calc_text_size(text_display)
        base_width, base_height = base_text_size

        # Determine scaling factors for width and height constraints
        # (How much we can grow before exceeding available box)
        # Add a 4px vertical padding margin
        available_width = width - 6
        available_height = height - 4

        # Avoid division by zero
        if base_width <= 0 or base_height <= 0:
            return

        scale_x = available_width / base_width
        scale_y = available_height / base_height

        # Choose smallest scale factor to fit both width & height
        scale_factor = min(scale_x, scale_y)

        # Compute new font size relative to start font size
        font_size = start_font_size * scale_factor

        # Clamp the final font size to a reasonable range
        font_size = max(10, min(32, font_size))

        # Apply and render text
        ImGui.push_font("Regular", int(font_size))
        text_size = PyImGui.calc_text_size(text_display)

        PyImGui.push_clip_rect(x1, y1, width, height, True)
        PyImGui.draw_list_add_text(
            x1 + ((width - text_size[0]) / 2),
            y1 + ((height - text_size[1]) / 2),
            self.color.opacify(1).color_int,
            text_display,
        )
        ImGui.pop_font()

        details_text = f"{self.w}x{self.h} @ {self.x},{self.y}"
        details_size = PyImGui.calc_text_size(details_text)
        PyImGui.draw_list_add_text(
            x1 + ((width - details_size[0]) / 2),
            y1 + height - details_size[1] - 2,
            self.color.opacify(1).color_int,
            details_text,
        )
        PyImGui.pop_clip_rect()
