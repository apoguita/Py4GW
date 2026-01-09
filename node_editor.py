import PyImGui as imgui
from dataclasses import dataclass, field
from typing import List, Tuple, Optional

# ---------------------------------
# Data Structures
# ---------------------------------

@dataclass
class Pin:
    id: int
    name: str
    is_output: bool
    pos: Tuple[float, float] = (0.0, 0.0)


@dataclass
class Node:
    id: int
    title: str
    pos: Tuple[float, float]
    inputs: List[Pin] = field(default_factory=list)
    outputs: List[Pin] = field(default_factory=list)


@dataclass
class Link:
    start_pin: Pin
    end_pin: Pin


# ---------------------------------
# Node Editor Core
# ---------------------------------

class NodeEditor:
    def __init__(self):
        self.nodes: List[Node] = []
        self.links: List[Link] = []

        self._next_id = 1
        self._dragging_pin: Optional[Pin] = None

        # View state
        self.pan = [0.0, 0.0]
        self.zoom = 1.0
        self.min_zoom = 0.2
        self.max_zoom = 2.5

        self._canvas_pos = (0, 0)
        self._canvas_size = (0, 0)

    # ---------------------------------
    # Public API
    # ---------------------------------

    def begin(self, label="NodeEditor"):
        imgui.begin_child(
            label,
            (0, 0),
            border=True,
            flags=imgui.WindowFlags.NoScrollbar | imgui.WindowFlags.NoMove
        )

        self._canvas_pos = imgui.get_cursor_screen_pos()
        self._canvas_size = imgui.get_content_region_avail()

        self._handle_pan_and_zoom()
        self._draw_background()

    def end(self):
        self._draw_links()
        self._draw_nodes()
        imgui.end_child()

    def add_node(self, title, x, y):
        node = Node(
            id=self._new_id(),
            title=title,
            pos=(x, y),
            inputs=[Pin(self._new_id(), "In", False)],
            outputs=[Pin(self._new_id(), "Out", True)],
        )
        self.nodes.append(node)
        return node

    # ---------------------------------
    # Internal Helpers
    # ---------------------------------

    def _new_id(self):
        i = self._next_id
        self._next_id += 1
        return i

    def _to_screen(self, pos):
        return (
            self._canvas_pos[0] + (pos[0] + self.pan[0]) * self.zoom,
            self._canvas_pos[1] + (pos[1] + self.pan[1]) * self.zoom,
        )

    def _handle_pan_and_zoom(self):
        io = imgui.get_io()

        # Zoom
        if imgui.is_window_hovered():
            self.zoom += io.mouse_wheel * 0.1 * self.zoom
            self.zoom = max(self.min_zoom, min(self.zoom, self.max_zoom))

        # Pan (MMB drag)
        if imgui.is_mouse_dragging(2):
            dx, dy = imgui.get_mouse_drag_delta(2)
            self.pan[0] += dx / self.zoom
            self.pan[1] += dy / self.zoom
            imgui.reset_mouse_drag_delta(2)

    def _draw_background(self):
        #draw_list = imgui.get_window_draw_list()
        draw_list = imgui.get_window_draw_list()
        x, y = self._canvas_pos
        w, h = self._canvas_size

        grid_step = 64 * self.zoom
        if grid_step < 16:
            return

        start_x = x + (self.pan[0] * self.zoom) % grid_step
        start_y = y + (self.pan[1] * self.zoom) % grid_step

        for i in range(int(w // grid_step) + 2):
            draw_list.add_line(
                start_x + i * grid_step,
                y,
                start_x + i * grid_step,
                y + h,
                imgui.get_color_u32_rgba(0.2, 0.2, 0.2, 1),
            )

        for i in range(int(h // grid_step) + 2):
            draw_list.add_line(
                x,
                start_y + i * grid_step,
                x + w,
                start_y + i * grid_step,
                imgui.get_color_u32_rgba(0.2, 0.2, 0.2, 1),
            )

    def _draw_nodes(self):
        for node in self.nodes:
            screen_pos = self._to_screen(node.pos)
            imgui.set_cursor_screen_pos(screen_pos)

            imgui.begin_group()
            imgui.begin_child(
                f"node_{node.id}",
                160 * self.zoom,
                90 * self.zoom,
                border=True,
            )

            imgui.text(node.title)

            for pin in node.inputs:
                self._draw_pin(pin)

            for pin in node.outputs:
                self._draw_pin(pin)

            imgui.end_child()
            imgui.end_group()

            # Drag node
            if imgui.is_item_active() and imgui.is_mouse_dragging(0):
                dx, dy = imgui.get_mouse_drag_delta(0)
                node.pos = (
                    node.pos[0] + dx / self.zoom,
                    node.pos[1] + dy / self.zoom,
                )
                imgui.reset_mouse_drag_delta(0)

    def _draw_pin(self, pin: Pin):
        draw_list = imgui.get_window_draw_list()
        cursor = imgui.get_cursor_screen_pos()
        radius = 5 * self.zoom

        pin.pos = (cursor[0] + radius, cursor[1] + radius)

        draw_list.add_circle_filled(
            pin.pos[0],
            pin.pos[1],
            radius,
            imgui.get_color_u32_rgba(0.9, 0.7, 0.2, 1),
        )

        imgui.invisible_button(f"pin_{pin.id}", radius * 2, radius * 2)

        if imgui.is_item_clicked():
            if self._dragging_pin is None:
                self._dragging_pin = pin
            else:
                if self._dragging_pin.is_output != pin.is_output:
                    self.links.append(
                        Link(
                            self._dragging_pin if self._dragging_pin.is_output else pin,
                            pin if self._dragging_pin.is_output else self._dragging_pin,
                        )
                    )
                self._dragging_pin = None

        imgui.same_line()
        imgui.text(pin.name)

    def _draw_links(self):
        draw_list = imgui.get_window_draw_list()

        for link in self.links:
            p1 = link.start_pin.pos
            p2 = link.end_pin.pos

            draw_list.add_bezier_curve(
                p1[0], p1[1],
                p1[0] + 50 * self.zoom, p1[1],
                p2[0] - 50 * self.zoom, p2[1],
                p2[0], p2[1],
                imgui.get_color_u32_rgba(1, 1, 1, 1),
                2.0,
            )