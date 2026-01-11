import PyImGui
from enum import Enum
from typing import List

"""
Author: Dharmanatrix. Dharma
2026
This script is designed to assist in the creation of node-editor spaces in Pyimgui, specifically for Py4GW 
"""

def _pack_rgba(r: int, g: int, b: int, a: int) -> int:
    # RGBA in memory (rarely used as a single int), still useful symmetry
    return ((r & 0xFF) << 24) | ((g & 0xFF) << 16) | ((b & 0xFF) << 8) | (a & 0xFF)


PACKED_GREY = _pack_rgba(100, 200, 250, 255)
PACKED_RED = _pack_rgba(255, 50, 50, 255)
PACKED_BLUE = _pack_rgba(50, 50, 255, 255)


class SingletonMeta(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            instance = super().__call__(*args, **kwargs)
            cls._instances[cls] = instance
        return cls._instances[cls]


class IDFactory(metaclass=SingletonMeta):
    def __init__(self):
        self.current = 0

    def get_id(self):
        self.current += 1
        print(f"Generated id {self.current}")
        return self.current

"""
    some data stored in cache

        self.logic_blocks = []
        self.links: List[Link] = list()
        self.pin_delay = False
        self.link_drag = 0
        
        
    Drawing was this
        global pin_hover, pin_load, pin_drag_start
    pin_hover = None

    section_header = PyImGui.collapsing_header("SmartCast", 4)
    PyImGui.same_line(PyImGui.get_content_region_avail()[0] - 20, -1)
    cache.sc_checkbox = PyImGui.checkbox("##SCCheckbox", cache.sc_checkbox)
    if PyImGui.is_item_hovered():
        PyImGui.set_tooltip("Disable" if cache.sc_checkbox else "Enable")

    if section_header:
        PyImGui.text("NOT COMPLETE: IN DEV")  # todo get rid of this
        PyImGui.begin_child("SmartCastOne", border=True, flags=PyImGui.WindowFlags.HorizontalScrollbar)
        PyImGui.begin_child("SmartCastTwo", (10000, 40000), border=True)
        if PyImGui.button("Create Logic Block"):
            cache.logic_blocks.append(LogicBlock())
        block: LogicBlock
        PyImGui.text(f"[{PyImGui.get_content_region_avail()}]")
        pos = PyImGui.get_cursor_pos()
        for block in cache.logic_blocks:
            # if avail > block.width + 10:
            #    PyImGui.same_line(0, 10)
            # avail = PyImGui.get_content_region_avail()[0]
            if block.logic.delete_me:
                cache.logic_blocks.remove(block)
                break
            else:
                block.draw()
            # PyImGui.same_line(0, 10)
            # PyImGui.text(f"[{PyImGui.get_content_region_avail()[0]}, {block.width * 4}, {avail > block.width * 4}]")
        link: Link
        for link in cache.links:
            if not link.exists:
                cache.links.remove(link)
                break
            link.Draw()
        PyImGui.set_cursor_pos(pos[0], pos[1])
        PyImGui.text(f"Hovered {pin_hover if pin_hover is None else pin_hover.id}, {cache.link_drag}")
        if pin_load is not None:
            if PyImGui.is_mouse_dragging(0, -1.0):
                # PyImGui.text("Dragon deez")
                cache.link_drag = 3
            if cache.link_drag > 0:
                if pin_drag_start is None:
                    pin_drag_start = pin_load.location
                    pin_drag_start[0] += pin_load.radius
                    pin_drag_start[1] += pin_load.radius
                dx, dy = PyImGui.get_mouse_drag_delta(0, 0.0)
                PyImGui.draw_list_add_line(pin_load.location[0] + pin_load.radius, pin_load.location[1] + pin_load.radius, pin_drag_start[0] + dx, pin_drag_start[1] + dy, PACKED_GREY, 4)
                if not PyImGui.is_mouse_dragging(0, -1):
                    if ValidatePins(pin_load, pin_hover):
                        in_pin, out_pin = (pin_load, pin_hover) if pin_load.is_in else (pin_hover, pin_load)
                        new_link: Link = Link(in_pin, out_pin)
                        cache.links.append(new_link)
                        cache.link_drag = 1
                cache.link_drag -= 1
            else:
                pin_load = None
                pin_drag_start = None

        PyImGui.end_child()
        PyImGui.end_child()
"""


class PinType(Enum):
    pass


class Pin:
    def __init__(self, _is_in: bool, _type: PinType, parent_id):
        self.id = IDFactory().get_id()
        self.location = (1, 1)
        self.type = _type
        self.radius = 8
        self.exists = True
        self.is_in = _is_in
        self.parent = parent_id
        self.is_hovered = False
        self.is_pressed = False
        self.is_dragged = False


    def pre_draw(self):
        PyImGui.push_id(f"{self.id}pin")

    def draw_override(self):
        """This is the function to override in child classes that wish to draw a different looking pin."""
        PyImGui.draw_list_add_circle(self.location[0] + self.radius, self.location[1] + self.radius, self.radius, PACKED_GREY, 4, 3)

    def post_draw(self):
        self.is_pressed = PyImGui.invisible_button("pin_button", self.radius * 2, self.radius * 2)
        self.is_hovered = PyImGui.is_item_hovered()
        self.is_dragged = PyImGui.is_item_active() and PyImGui.is_mouse_dragging(0, -1.0)
        PyImGui.pop_id()

    def draw(self):
        self.pre_draw()
        self.draw_override()
        self.post_draw()


class Link:
    def __init__(self, pin_in: Pin, pin_out: Pin):
        self.pin_in: Pin = pin_in
        self.pin_out: Pin = pin_out
        self.exists = True
        self.id = IDFactory().get_id()


class Execution:
    def execute(self):
        pass


class Node:
    def __init__(self):
        self.id = IDFactory().get_id()
        self.type = "None"
        self.delete_me = False
        self.del_width = 30
        self.header_color = (0.20, 0.15, 0.7, 1.0)
        self.height = 40
        self.width = 100
        self.pins: List[Pin] = list()
        self.header_height = 20
        self.side_padding = 20
        self.x = 100
        self.y = 100
        self.hovered = False
        self.execute: Execution


    def draw_header(self):
        PyImGui.push_item_width(PyImGui.get_content_region_avail()[0])
        PyImGui.text(self.type)
        PyImGui.pop_item_width()
        PyImGui.same_line(PyImGui.get_content_region_avail()[0] - self.del_width, -1)
        if PyImGui.small_button("del"):
            self.delete_me = True
            p: Pin
            for p in self.pins:
                p.exists = False

    def draw_body(self):
        PyImGui.text(f"({self.x, self.y})")


def validate_pins(pin_a: Pin, pin_b: Pin) -> bool:
    if pin_a is None: return False
    if pin_b is None: return False
    if pin_a == pin_b: return False
    if pin_a.is_in == pin_b.is_in: return False
    if pin_a.type != pin_b.type: return False
    if pin_a.parent == pin_b.parent: return False
    return True


class NodeSpace:
    def __init__(self, unique_id):
        self.my_id = unique_id
        self.TRIGGER_COLOR = (0.573, 0, 1, 1)
        self.FLOW_COLOR = (0.631, 0, 0, 1)
        self.LOGIC_COLOR = (0, 0.616, 1, 1)
        self.DATA_COLOR = (0, 0.529, 0.051, 1)
        self.OUTPUT_COLOR = (0.969, 0.271, 0, 1)
        self.LINE_THICKNESS = 4
        self.LEAD_LENGTH = -20
        self.SIZE_CHANGE_POP = 10
        self.SPACER = 2
        self.pin_drag_start: Pin = None
        self.drag_buffered = False
        self.pins: List[Pin] = list()
        self.links: List[Link] = list()
        self.nodes = []
        self.global_transform = (0, 0)
        self.width = 1000
        self.height = 1000
        self.new_node_class: type(Node) = Node

    def draw_link_b(self, link: Link, in_count, out_count):
        PyImGui.push_id(f"linkid{link.id}")
        if not link.pin_in.exists or not link.pin_out.exists:
            link.exists = False
            return
        in_pos = link.pin_in.location[0] + link.pin_in.radius, link.pin_in.location[1] + link.pin_in.radius
        out_pos = link.pin_out.location[0] + link.pin_out.radius, link.pin_out.location[1] + link.pin_out.radius
        # PyImGui.draw_list_add_line(link.pins[0].location[0] + link.pins[0].radius, link.pins[0].location[1] + link.pins[0].radius, link.pins[1].location[0] + link.pins[0].radius, link.pins[1].location[1] + link.pins[0].radius, Py4GWCoreLib.Color()._pack_rgba(100, 200, 250, 255), 4)
        PyImGui.draw_list_add_line(in_pos[0], in_pos[1], in_pos[0] + self.LEAD_LENGTH - in_count * 2 * self.LINE_THICKNESS, in_pos[1], PACKED_GREY, self.LINE_THICKNESS)
        PyImGui.draw_list_add_line(out_pos[0], out_pos[1], out_pos[0] - (self.LEAD_LENGTH - out_count * 2 * self.LINE_THICKNESS), out_pos[1], PACKED_GREY, self.LINE_THICKNESS)
        in_pos = in_pos[0] + self.LEAD_LENGTH - in_count * 2 * self.LINE_THICKNESS, in_pos[1]
        out_pos = out_pos[0] - (self.LEAD_LENGTH - out_count * 2 * self.LINE_THICKNESS), out_pos[1]
        center_x = (in_pos[0] + out_pos[0]) / 2
        center_y = (in_pos[1] + out_pos[1]) / 2
        PyImGui.draw_list_add_line(in_pos[0], in_pos[1], in_pos[0], center_y, PACKED_GREY, self.LINE_THICKNESS)
        PyImGui.draw_list_add_line(out_pos[0], out_pos[1], out_pos[0], center_y, PACKED_GREY, self.LINE_THICKNESS)
        PyImGui.draw_list_add_line(in_pos[0], center_y, out_pos[0], center_y, PACKED_GREY, self.LINE_THICKNESS)

        PyImGui.set_cursor_screen_pos(center_x - 5, center_y - 5)
        link.exists = not PyImGui.small_button("d")
        PyImGui.pop_id()

    def draw_link(self, link: Link, in_count, out_count):
        PyImGui.push_id(f"linkid{link.id}")
        is_pressed = False
        if not link.pin_in.exists or not link.pin_out.exists:
            link.exists = False
            return
        in_pos = link.pin_in.location[0] + link.pin_in.radius, link.pin_in.location[1] + link.pin_in.radius
        out_pos = link.pin_out.location[0] + link.pin_out.radius, link.pin_out.location[1] + link.pin_out.radius
        PyImGui.draw_list_add_line(in_pos[0], in_pos[1], in_pos[0] + self.LEAD_LENGTH - in_count * 2 * self.LINE_THICKNESS, in_pos[1], PACKED_GREY, self.LINE_THICKNESS)
        PyImGui.draw_list_add_line(out_pos[0], out_pos[1], out_pos[0] - (self.LEAD_LENGTH - out_count * 2 * self.LINE_THICKNESS), out_pos[1], PACKED_GREY, self.LINE_THICKNESS)
        in_pos = in_pos[0] + self.LEAD_LENGTH - in_count * 2 * self.LINE_THICKNESS, in_pos[1]
        out_pos = out_pos[0] - (self.LEAD_LENGTH - out_count * 2 * self.LINE_THICKNESS), out_pos[1]
        center_x = (in_pos[0] + out_pos[0]) / 2
        center_y = (in_pos[1] + out_pos[1]) / 2
        half_line = self.LINE_THICKNESS / 2
        PyImGui.draw_list_add_line(in_pos[0], in_pos[1], in_pos[0], center_y, PACKED_GREY, self.LINE_THICKNESS)
        p1 = False
        if center_y > in_pos[1]:
            PyImGui.set_cursor_screen_pos(in_pos[0] - half_line, in_pos[1])
            p1 = PyImGui.invisible_button("p2b", self.LINE_THICKNESS, center_y - in_pos[1])
        else:
            PyImGui.set_cursor_screen_pos(in_pos[0] - half_line, center_y)
            p1 = PyImGui.invisible_button("p1b", self.LINE_THICKNESS, in_pos[1] - center_y)
        PyImGui.draw_list_add_line(out_pos[0], out_pos[1], out_pos[0], center_y, PACKED_GREY, self.LINE_THICKNESS)
        p2 = False
        if center_y > out_pos[1]:
            PyImGui.set_cursor_screen_pos(out_pos[0] - half_line, out_pos[1])
            p2 = PyImGui.invisible_button("p2b", self.LINE_THICKNESS, center_y - out_pos[1])
        else:
            PyImGui.set_cursor_screen_pos(out_pos[0] - half_line, center_y)
            p2 = PyImGui.invisible_button("p1b", self.LINE_THICKNESS, out_pos[1] - center_y)
        PyImGui.draw_list_add_line(in_pos[0], center_y, out_pos[0], center_y, PACKED_GREY, self.LINE_THICKNESS)
        p3 = False
        if in_pos[0] > out_pos[0]:
            PyImGui.set_cursor_screen_pos(out_pos[0], center_y - half_line)
            p3 = PyImGui.invisible_button("p3b", in_pos[0] - out_pos[0], self.LINE_THICKNESS)
        else:
            PyImGui.set_cursor_screen_pos(in_pos[0], center_y - half_line)
            p3 = PyImGui.invisible_button("p3b", out_pos[0] - in_pos[0], self.LINE_THICKNESS)

        PyImGui.set_cursor_screen_pos(center_x - 5, center_y - 5)
        is_pressed = p1 or p2 or p3
        link.exists = not is_pressed
        PyImGui.pop_id()
        
    def draw_node(self, node: Node):
        PyImGui.push_id(f"Ldraw{node.id}")
        PyImGui.set_cursor_pos(node.x, node.y)
        if node.hovered:
            PyImGui.push_style_color(PyImGui.ImGuiCol.ChildBg, (0.30, 0.15, 0.2, 1.0))
        else:
            PyImGui.push_style_color(PyImGui.ImGuiCol.ChildBg, (0.10, 0.15, 0.2, 1.0))
        PyImGui.begin_child(f"LogicBlockFull",
                            (node.width + node.side_padding * 2, node.header_height + node.height),
                            border=False)
        PyImGui.push_style_color(PyImGui.ImGuiCol.ChildBg, node.header_color)
        PyImGui.begin_child(f"LogicHeader", (node.width + node.side_padding * 2, node.header_height), border=False)
        pos = PyImGui.get_cursor_pos()
        pressed = PyImGui.invisible_button(f"##LogicBlockButton{node.id}",
                                           node.width + node.side_padding * 2 - node.del_width,
                                           node.header_height)
        node.hovered = PyImGui.is_item_hovered()
        if PyImGui.is_item_active() and PyImGui.is_mouse_dragging(0, -1.0):
            node.hovered = True
            dx, dy = PyImGui.get_mouse_drag_delta(0, 0.0)
            node.x += dx
            node.y += dy
            PyImGui.reset_mouse_drag_delta(0)
        PyImGui.set_cursor_pos(pos[0], pos[1] + self.SPACER)
        node.draw_header()
        PyImGui.end_child()
        PyImGui.pop_style_color(1)
        PyImGui.set_cursor_pos(2, pos[1] + node.header_height + self.SPACER)
        pin: Pin
        out_pins: List[Pin] = list()
        for pin in node.pins:
            if not pin.is_in:
                out_pins.append(pin)
            else:
                pos = PyImGui.get_cursor_screen_pos()
                pin.location = pos
                pin.draw()
                PyImGui.set_cursor_screen_pos(pos[0], pos[1] + self.SPACER + pin.radius * 2)
        PyImGui.set_cursor_pos(node.side_padding, node.header_height)
        PyImGui.begin_child(f"LogicBody", (node.width, node.height), border=False)
        node.draw_body()
        PyImGui.end_child()
        PyImGui.set_cursor_pos(node.side_padding * 2 + node.width, node.header_height)
        for pin in out_pins:
            pos = PyImGui.get_cursor_screen_pos()
            PyImGui.set_cursor_screen_pos(pos[0] - pin.radius * 2 - self.SPACER, pos[1] + self.SPACER)
            pin.location = PyImGui.get_cursor_screen_pos()
            pin.draw()
            PyImGui.set_cursor_screen_pos(pos[0], pos[1] + pin.radius * 2)
        PyImGui.end_child()
        PyImGui.pop_style_color(1)
        PyImGui.pop_id()

    def _handle_creating_new_nodes(self, screen_x, screen_y, mouse_x, mouse_y, screen_pos):
        if PyImGui.is_mouse_clicked(1):
            mouse_relx = mouse_x - screen_pos[0]
            mouse_rely = mouse_y - screen_pos[1]
            if 0 < mouse_relx < screen_x and 0 < mouse_rely < screen_y:
                n = self.new_node_class()
                n.x = mouse_relx
                n.y = mouse_rely
                self.nodes.append(n)
                self.pins.extend(n.pins)

    def _handle_space_edges(self):
        node: Node
        tran_x = 0
        tran_y = 0
        for node in self.nodes:
            if node.delete_me:
                self.nodes.remove(node)
                break
            else:
                self.draw_node(node)
                if node.x + node.width > self.width:
                    self.width += node.width + self.SIZE_CHANGE_POP
                elif node.x < 0:
                    tran_x = node.x - self.SIZE_CHANGE_POP
                if node.y < 0:
                    tran_y = node.y - self.SIZE_CHANGE_POP
                elif node.y + node.height + node.header_height > self.height:
                    self.height += node.height + node.header_height + self.SIZE_CHANGE_POP
            if tran_y != 0 or tran_x != 0:
                for node in self.nodes:
                    node.x -= tran_x
                    node.y -= tran_y
                break

    def _draw_links(self):
        pin_dict = dict()
        pin: Pin
        for pin in self.pins:
            pin_dict[pin] = 0
        link: Link
        for link in self.links:
            if not link.exists:
                self.links.remove(link)
                break
            self.draw_link(link, pin_dict[link.pin_in], pin_dict[link.pin_out])
            pin_dict[link.pin_in] = pin_dict[link.pin_in] + 1
            pin_dict[link.pin_out] = pin_dict[link.pin_out] + 1

    def _handle_drag_and_link(self, mouse_x, mouse_y):
        pin_hovered: Pin = None
        for pin in self.pins:
            if pin.is_dragged:
                self.pin_drag_start = pin
            if pin.is_hovered:
                pin_hovered = pin
        PyImGui.text(f"""Pin hovered {pin_hovered.id if pin_hovered is not None else "none"}, pin_drag_start {(self.pin_drag_start.id, self.pin_drag_start.is_dragged) if self.pin_drag_start is not None else "none"}""")
        if self.pin_drag_start is not None:
            if PyImGui.is_mouse_dragging(0, -1.0):
                PyImGui.draw_list_add_line(self.pin_drag_start.location[0] + self.pin_drag_start.radius,
                                           self.pin_drag_start.location[1] + self.pin_drag_start.radius,
                                           mouse_x,
                                           mouse_y, PACKED_GREY, self.LINE_THICKNESS)
            else:
                if pin_hovered is not None:
                    if validate_pins(self.pin_drag_start, pin_hovered):
                        in_pin, out_pin = (self.pin_drag_start, pin_hovered) if self.pin_drag_start.is_in else (
                        pin_hovered, self.pin_drag_start)
                        new_link: Link = Link(in_pin, out_pin)
                        self.links.append(new_link)
                        self.pin_drag_start = None
                        self.drag_buffered = False
                        return
                if not self.drag_buffered:
                    self.drag_buffered = True
                else:
                    self.pin_drag_start = None
                    self.drag_buffered = False

    def draw_space(self):
        pin_hover: Pin = None
        PyImGui.push_id(self.my_id)
        PyImGui.begin_child("SpaceOuter", border=True, flags=PyImGui.WindowFlags.HorizontalScrollbar)
        screen_x, screen_y = PyImGui.get_content_region_avail()
        mouse_x = PyImGui.get_io().mouse_pos_x
        mouse_y = PyImGui.get_io().mouse_pos_y
        PyImGui.begin_child("SpaceInner", (self.width, self.height), border=True)
        pos = PyImGui.get_cursor_pos()
        screen_pos = PyImGui.get_cursor_screen_pos()
        self._handle_creating_new_nodes(screen_x, screen_y, mouse_x, mouse_y, screen_pos)
        self._handle_space_edges()
        self._draw_links()
        PyImGui.set_cursor_pos(pos[0], pos[1])
        self._handle_drag_and_link(mouse_x, mouse_y)
        PyImGui.end_child()
        PyImGui.end_child()
        PyImGui.pop_id()
