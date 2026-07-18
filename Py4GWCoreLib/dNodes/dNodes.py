import PyImGui
from enum import Enum
from typing import List, Dict

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


class PinType(Enum):
    pass


class Pin:
    def __init__(self, _is_in: bool, _type: PinType, parent_id):
        self.id = IDFactory().get_id()
        self.link_ids: List[int] = list()
        self.location = (1, 1)
        self.type = _type
        self.radius = 8
        self.exists = True
        self.is_in = _is_in
        self.parent = parent_id
        self.is_hovered = False
        self.is_pressed = False
        self.is_dragged = False
        self.value = False

    def _pre_draw(self):
        PyImGui.push_id(f"{self.id}pin")

    def draw_override(self):
        """This is the function to override in child classes that wish to draw a different looking pin."""
        PyImGui.draw_list_add_circle(self.location[0] + self.radius, self.location[1] + self.radius, self.radius, PACKED_GREY, 4, 3)

    def _post_draw(self):
        self.is_pressed = PyImGui.invisible_button("pin_button", self.radius * 2, self.radius * 2)
        self.is_hovered = PyImGui.is_item_hovered()
        self.is_dragged = PyImGui.is_item_active() and PyImGui.is_mouse_dragging(0, -1.0)
        PyImGui.set_cursor_screen_pos(self.location[0], self.location[1] + self.radius * 2)
        PyImGui.pop_id()

    def _draw(self):
        self._pre_draw()
        self.draw_override()
        self._post_draw()


class Link:
    def __init__(self, pin_in: Pin, pin_out: Pin):
        self.pin_in: Pin = pin_in
        self.pin_out: Pin = pin_out
        self.exists = True
        self.id = IDFactory().get_id()


class Node:
    def __init__(self, x=100, y=100):
        self.id = IDFactory().get_id()
        self.type = "None"
        self.delete_me = False
        self.del_width = 30
        self.header_color = (0.20, 0.15, 0.7, 1.0)
        self.height = 20
        self.width = 60
        self.pins: List[Pin] = list()
        self.header_height = 20
        self.side_padding = 20
        self.x = x
        self.y = y
        self.hovered = False
        self.tooltip = "No tooltip for this node"

    def draw_header(self):
        PyImGui.text("?")
        if PyImGui.is_item_hovered():
            PyImGui.set_tooltip(self.tooltip)
        PyImGui.same_line(0.0, -1.0)
        PyImGui.push_item_width(PyImGui.get_content_region_avail()[0])
        PyImGui.text(f"{self.type}")
        PyImGui.pop_item_width()
        PyImGui.same_line(PyImGui.get_content_region_avail()[0] - self.del_width, -1)
        if PyImGui.small_button("del"):
            self.delete_me = True
            p: Pin
            for p in self.pins:
                p.exists = False

    def draw_body(self):
        pass

    def inform_update(self, pin: Pin):
        pass

    def pre_execute(self):
        pass

    def execute(self):
        return False


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
        self.half_line = round(self.LINE_THICKNESS / 2)
        self.pin_drag_start: Pin = None
        self.drag_buffered = False
        self.pins: List[Pin] = list()
        self.links: Dict[int, Link] = dict()
        self.nodes: Dict[int, Node] = dict()
        self.global_transform = (0, 0)
        self.width = 1000
        self.height = 1000
        self.new_node_class: type(Node) = Node
        self.first_order_nodes: List[Node] = list()
        self.block_propagation = False

    def add_node(self, node: Node):
        self.nodes[node.id] = node
        self.pins.extend(node.pins)
        pin: Pin
        first_order = True
        for pin in node.pins:
            if pin.is_in:
                first_order = False
                break
        if first_order:
            self.first_order_nodes.append(node)

    def delete_node(self, node: Node):
        self.nodes.pop(node.id)
        if self.first_order_nodes.__contains__(node):
            self.first_order_nodes.remove(node)

    def _create_link(self, in_pin: Pin, out_pin: Pin):
        new_link: Link = Link(in_pin, out_pin)
        out_pin.link_ids.append(new_link.id)
        in_pin.link_ids.append(new_link.id)
        self.links[new_link.id] = new_link

    def _delete_link(self, link: Link):
        link.pin_in.link_ids.remove(link.id)
        link.pin_out.link_ids.remove(link.id)
        self.links.pop(link.id)

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

        PyImGui.draw_list_add_line(in_pos[0], in_pos[1], in_pos[0], center_y, PACKED_GREY, self.LINE_THICKNESS)
        p1 = False
        if center_y > in_pos[1]:
            PyImGui.set_cursor_screen_pos(in_pos[0] - self.half_line, in_pos[1])
            p1 = PyImGui.invisible_button("p2b", self.LINE_THICKNESS, center_y - in_pos[1])
        else:
            PyImGui.set_cursor_screen_pos(in_pos[0] - self.half_line, center_y)
            p1 = PyImGui.invisible_button("p1b", self.LINE_THICKNESS, in_pos[1] - center_y)
        PyImGui.draw_list_add_line(out_pos[0], out_pos[1], out_pos[0], center_y, PACKED_GREY, self.LINE_THICKNESS)
        p2 = False
        if center_y > out_pos[1]:
            PyImGui.set_cursor_screen_pos(out_pos[0] - self.half_line, out_pos[1])
            p2 = PyImGui.invisible_button("p2b", self.LINE_THICKNESS, center_y - out_pos[1])
        else:
            PyImGui.set_cursor_screen_pos(out_pos[0] - self.half_line, center_y)
            p2 = PyImGui.invisible_button("p1b", self.LINE_THICKNESS, out_pos[1] - center_y)
        PyImGui.draw_list_add_line(in_pos[0], center_y, out_pos[0], center_y, PACKED_GREY, self.LINE_THICKNESS)
        p3 = False
        if in_pos[0] > out_pos[0]:
            PyImGui.set_cursor_screen_pos(out_pos[0], center_y - self.half_line)
            p3 = PyImGui.invisible_button("p3b", in_pos[0] - out_pos[0], self.LINE_THICKNESS)
        else:
            PyImGui.set_cursor_screen_pos(in_pos[0], center_y - self.half_line)
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
                pin._draw()
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
            pin._draw()
            PyImGui.set_cursor_screen_pos(pos[0], pos[1] + pin.radius * 2)
        PyImGui.end_child()
        PyImGui.pop_style_color(1)
        PyImGui.pop_id()

    def _handle_space_edges(self):
        node: Node
        tran_x = 0
        tran_y = 0
        for node in self.nodes.values():
            if node.delete_me:
                self.delete_node(node)
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
                for node in self.nodes.values():
                    node.x -= tran_x
                    node.y -= tran_y
                break

    def _draw_links(self):
        node_dict = dict()
        node: Node
        for node in self.nodes.values():
            node_dict[node] = [0, 0]
        link: Link
        for link in self.links.values():
            if not link.exists:
                self._delete_link(link)
                break
            self.draw_link(link, node_dict[self.nodes[link.pin_in.parent]][0], node_dict[self.nodes[link.pin_out.parent]][1])
            node_dict[self.nodes[link.pin_in.parent]][0] += 1
            node_dict[self.nodes[link.pin_out.parent]][1] += 1

    def _handle_drag_and_link(self, mouse_x, mouse_y):
        pin_hovered: Pin = None
        for pin in self.pins:
            if pin.is_dragged:
                self.pin_drag_start = pin
            if pin.is_hovered:
                pin_hovered = pin
        # PyImGui.text(f"""Pin hovered {pin_hovered.id if pin_hovered is not None else "none"}, pin_drag_start {(self.pin_drag_start.id, self.pin_drag_start.is_dragged) if self.pin_drag_start is not None else "none"}""")
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
                        self._create_link(in_pin, out_pin)
                        self.pin_drag_start = None
                        self.drag_buffered = False
                        return
                if not self.drag_buffered:
                    self.drag_buffered = True
                else:
                    self.pin_drag_start = None
                    self.drag_buffered = False

    def _handle_creating_new_nodes(self, screen_x, screen_y, mouse_x, mouse_y, screen_pos):
        if PyImGui.is_mouse_clicked(1):
            mouse_relx = mouse_x - screen_pos[0]
            mouse_rely = mouse_y - screen_pos[1]
            if 0 < mouse_relx < screen_x and 0 < mouse_rely < screen_y:
                n = self.new_node_class(mouse_relx, mouse_rely)
                self.add_node(n)

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

    def _get_nodes_connected_to_pin(self, pin: Pin) -> List[Node]:
        nodes: List[Node] = list()
        link: Link
        if pin.is_in:
            for i in pin.link_ids:
                nodes.append(self.nodes[self.links[i].pin_out.parent])
        else:
            for i in pin.link_ids:
                nodes.append(self.nodes[self.links[i].pin_in.parent])
        return nodes

    def propagate_pin(self, pin: Pin):
        if self.block_propagation:
            return
        if pin.is_in:
            return
        for i in pin.link_ids:
            p: Pin = self.links[i].pin_in
            p.value = pin.value
            if self.nodes[p.parent].delete_me: continue
            self.nodes[p.parent].inform_update(p)

    def execute_graph(self):
        self.block_propagation = False
        node: Node
        for node in self.nodes.values():
            node.pre_execute()

        for node in self.first_order_nodes:
            node.execute()
            p: Pin
            for p in node.pins:
                if p.is_in: continue
                self.propagate_pin(p)
