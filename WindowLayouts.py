from cProfile import label
from Py4GWCoreLib import IconsFontAwesome5, Color, ColorPalette, GLOBAL_CACHE, SharedCommandType, ConsoleLog
import PyImGui
import Py4GW
import PyOverlay
import os

MODULE_NAME = "Window Manipulator"

screen_overlay = PyOverlay.ScreenOverlay()
screen_overlay.create_overlay(ms=100, destroy=False)

io = PyImGui.get_io()
screen_width, screen_height = screen_overlay.get_desktop_size()

import ctypes as ct

def _pack_wchars(value: str, WCharArrayType):
    """Pack a Python str into a fixed-size ctypes wide-char array (null-terminated)."""
    arr = WCharArrayType()
    if value:
        maxlen = getattr(WCharArrayType, "_length_", 0) - 1  # leave room for terminator
        s = value[:maxlen] if maxlen > 0 else ""
        for i, ch in enumerate(s):
            arr[i] = ch
    return arr

def _pack_extra_data_for_sendmessage(extra_tuple):
    """
    Return a 4-tuple of ctypes wide-char arrays matching SendMessage's argtypes.
    Falls back to (c_wchar * 4) if argtypes aren't available.
    """
    # Try to infer the expected array types from the function signature
    arr_types = None
    fn = getattr(GLOBAL_CACHE.ShMem, "SendMessage", None)
    if fn is not None:
        argtypes = getattr(fn, "argtypes", None)
        if argtypes:
            # Most bindings put the 4 wchar arrays as the last 4 parameters
            last4 = argtypes[-4:]
            if (
                len(last4) == 4
                and all(isinstance(t, type) for t in last4)
                and all(hasattr(t, "_length_") for t in last4)
                and all(getattr(t, "_type_", None) is ct.c_wchar for t in last4)
            ):
                arr_types = last4

    if arr_types is None:
        # Fallback based on your error: expected c_wchar_Array_4
        arr_types = [ct.c_wchar * 4] * 4

    # Build packed tuple
    out = []
    for i in range(4):
        val = extra_tuple[i] if i < len(extra_tuple) else ""
        typ = arr_types[i]
        if isinstance(val, typ):
            out.append(val)
        else:
            out.append(_pack_wchars(str(val), typ))
    return tuple(out)


def _send_message_to(command: SharedCommandType, receiver_email: str, params=(0.0, 0.0, 0.0, 0.0), ExtraData=("", "", "", "")):
    sender_email = GLOBAL_CACHE.Player.GetAccountEmail()
    accounts = GLOBAL_CACHE.ShMem.GetAllAccountData()
    if not any(acc.AccountEmail == receiver_email for acc in accounts):
        ConsoleLog("Messaging", f"Account with email {receiver_email} not found. Message not sent.", log=True)
        return

    packed = _pack_extra_data_for_sendmessage(ExtraData)

    # Some bindings want the 4 arrays as separate args; others accept a single tuple.
    try:
        GLOBAL_CACHE.ShMem.SendMessage(sender_email, receiver_email, command, params, *packed)
    except TypeError:
        GLOBAL_CACHE.ShMem.SendMessage(sender_email, receiver_email, command, params, packed)

    
    
def slider_input_int(label: str, value: int, min_value: int, max_value: int) -> int:
    """Draw a slider + input int combo on one line, clamped to [min_value, max_value]."""
    v = int(value)

    # Use hidden IDs so the visible label can be separate/clean
    slider_id = f"##{label}_slider"
    input_id  = f"##{label}_input"

    # Optional visible label
    start_x = PyImGui.get_cursor_pos_x()
    PyImGui.text(label)
    PyImGui.same_line(start_x + 50, -1)
    #PyImGui.same_line(0, -1)  # 50px gap after the label

    PyImGui.push_item_width(150)
    v_slider = PyImGui.slider_int(slider_id, v, int(min_value), int(max_value))
    if v_slider != v:
        v = v_slider

    PyImGui.same_line(0, -1)
    v_input = PyImGui.input_int(input_id, v)
    if v_input != v:
        # clamp manual input
        if v_input < min_value: v_input = min_value
        if v_input > max_value: v_input = max_value
        v = v_input

    PyImGui.pop_item_width()
    return v


class ClientConfig:
    def __init__(self, email="", alias="", x=0.0, y=0.0, width=0.0, height=0.0, borderless=False, rename_window=False, window_title=""):
        self.email = email
        self.alias = alias
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.borderless = borderless
        self.rename_window = rename_window
        self.window_title = window_title
        self.color:Color =  ColorPalette.GetColor("white")
        self.show_overlay: bool = True 
        self.always_on_top: bool = False
        self.opacity: int = 255  # 0-255
        
    def to_dict(self):
        return {
            "email": self.email,
            "alias": self.alias,
            "x": self.x,
            "y": self.y,
            "width": self.width,
            "height": self.height,
            "borderless": self.borderless,
            "rename_window": self.rename_window,
            "window_title": self.window_title,
            "color": self.color.to_tuple(),
            "show_overlay": self.show_overlay,
            "always_on_top": self.always_on_top,
            "opacity": self.opacity
        }
        
    def from_dict(self, data):
        self.email = data.get("email", "")
        self.alias = data.get("alias", "")
        self.x = data.get("x", 0.0)
        self.y = data.get("y", 0.0)
        self.width = data.get("width", 0.0)
        self.height = data.get("height", 0.0)
        self.borderless = data.get("borderless", False)
        self.rename_window = data.get("rename_window", False)
        self.window_title = data.get("window_title", "")
        color_tuple = data.get("color", (255, 255, 255, 255))
        if isinstance(color_tuple, (list, tuple)) and len(color_tuple) == 4:
            self.color = Color(*color_tuple)
        self.show_overlay = data.get("show_overlay", False)
        self.always_on_top = data.get("always_on_top", False)
        self.opacity = data.get("opacity", 255)

class LayoutConfig:
    def __init__(self, layout_name: str = "", is_template: bool = False):
        self.layout_name = layout_name
        self.is_template = is_template  # <-- NEW: mark as client-less template when True
        self.clients: list[ClientConfig] = []

    def to_dict(self):
        return {
            "layout_name": self.layout_name,
            "is_template": self.is_template,  # <-- NEW
            "clients": [client.to_dict() for client in self.clients]
        }

    def from_dict(self, data):
        self.layout_name = data.get("layout_name", "")
        self.is_template = data.get("is_template", False)  # <-- NEW (defaults to False)
        self.clients = []
        for client_data in data.get("clients", []):
            client = ClientConfig()
            client.from_dict(client_data)
            self.clients.append(client)

    def get_client_by_email(self, email: str) -> ClientConfig | None:
        for client in self.clients:
            if client.email == email:
                return client
        return None

    def get_client_by_alias(self, alias: str) -> ClientConfig | None:
        for client in self.clients:
            if client.alias == alias:
                return client
        return None

    def add_client(self, client: ClientConfig):
        self.clients.append(client)

    def remove_client(self, client: ClientConfig):
        self.clients.remove(client)

    def update_client(self, email: str, new_client: ClientConfig):
        for i, client in enumerate(self.clients):
            if client.email == email:
                self.clients[i] = new_client
                return

    def get_all_clients(self) -> list[ClientConfig]:
        return self.clients

    
class WindowLayouts:
    def __init__(self):
        self.layouts: list[LayoutConfig] = []
        self.all_accounts: list[ClientConfig] = []
        self.accounts_file = "accounts.json"
        self.projects_path = Py4GW.Console.get_projects_path()
        
        # existing UI state...
        self._lcw_selected_layout_idx = -1
        self._lcw_selected_client_idx = -1
        self._lcw_account_picker_idx = 0
        
        self._edit_layout_name = ""
        self._new_layout_name = ""
        # NEW: per-client editor windows state
        self._client_editor_windows: list[dict] = []  # each: {"layout_idx": int, "client_idx": int, "open": bool}
        self.load_layouts()
        self.get_all_accounts_from_json()

    def load_layouts(self):
        config_path = os.path.join(self.projects_path, "window_layouts.json")
        if os.path.exists(config_path):
            import json
            with open(config_path, "r") as f:
                data = json.load(f)
                self.layouts = []
                for layout_data in data.get("layouts", []):
                    layout = LayoutConfig()
                    layout.from_dict(layout_data)
                    self.layouts.append(layout)

    def save_layouts(self):
        config_path = os.path.join(self.projects_path, "window_layouts.json")
        import json
        with open(config_path, "w") as f:
            data = {
                "layouts": [layout.to_dict() for layout in self.layouts]
            }
            json.dump(data, f, indent=4)

    def get_layout_by_name(self, name: str) -> LayoutConfig | None:
        for layout in self.layouts:
            if layout.layout_name == name:
                return layout
        return None

    def add_layout(self, layout: LayoutConfig):
        self.layouts.append(layout)
        self.save_layouts()

    def remove_layout(self, layout: LayoutConfig):
        self.layouts.remove(layout)
        self.save_layouts()

    def update_layout(self, name: str, new_layout: LayoutConfig):
        for i, layout in enumerate(self.layouts):
            if layout.layout_name == name:
                self.layouts[i] = new_layout
                self.save_layouts()
                return

    def get_all_layouts(self) -> list[LayoutConfig]:
        return self.layouts    

    def get_all_accounts_from_json (self):
        import json
        with open(self.accounts_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        seen = set()
        unique_accounts: list[ClientConfig] = []

        for group_name, accounts in data.items():
            for acc in accounts:
                email = acc.get("email")
                if not email or email in seen:
                    continue
                seen.add(email)

                # Create a ClientConfig using relevant fields
                client = ClientConfig(
                    email=email,
                    alias=acc.get("character_name", email),
                    x=acc.get("top_left", [0, 0])[0],
                    y=acc.get("top_left", [0, 0])[1],
                    width=acc.get("width", 800),
                    height=acc.get("height", 600),
                    borderless=acc.get("resize_client", False),
                    rename_window=acc.get("enable_client_rename", False),
                    window_title=acc.get("custom_client_name", "")
                )
                unique_accounts.append(client)

        # Save into layouts
        self.all_accounts = unique_accounts
        self.save_layouts()
        print(f"Extracted {len(unique_accounts)} unique accounts.")
        
    def draw_window(self):
        if PyImGui.begin("Layout Management", PyImGui.WindowFlags.AlwaysAutoResize):
            PyImGui.text("Window Layouts:")

            for i, layout in enumerate(self.get_all_layouts()):
                if PyImGui.selectable(
                    layout.layout_name,
                    self._lcw_selected_layout_idx == i,
                    PyImGui.SelectableFlags.NoFlag,
                    (0.0, 0.0),
                ):
                    self._lcw_selected_layout_idx = i
                    self._edit_layout_name = layout.layout_name

            PyImGui.separator()

            if 0 <= self._lcw_selected_layout_idx < len(self.get_all_layouts()):
                layout = self.get_all_layouts()[self._lcw_selected_layout_idx]
                PyImGui.text(f"Editing Layout: {layout.layout_name}")
                self._edit_layout_name = PyImGui.input_text("Layout Name", self._edit_layout_name, 0)

                if PyImGui.button("Save Changes"):
                    layout.layout_name = self._edit_layout_name
                    self.save_layouts()

                PyImGui.same_line(0, -1)
                if PyImGui.button("Delete Layout"):
                    self.remove_layout(layout)
                    self._lcw_selected_layout_idx = -1
                    self._edit_layout_name = ""

            PyImGui.separator()
            self._new_layout_name = PyImGui.input_text("New Layout Name", self._new_layout_name, 0)
            if PyImGui.button("Add Layout") and self._new_layout_name.strip():
                new_layout = LayoutConfig(layout_name=self._new_layout_name.strip())
                self.add_layout(new_layout)
                self._new_layout_name = ""
        PyImGui.end()
        
    # --- add this method inside class WindowLayouts ---
    def open_client_editor(self, layout_idx: int, client_idx: int):
        # avoid duplicates
        for win in self._client_editor_windows:
            if win["layout_idx"] == layout_idx and win["client_idx"] == client_idx and win["open"]:
                return
        self._client_editor_windows.append({"layout_idx": layout_idx, "client_idx": client_idx, "open": True})
        
    def draw_client_editors(self):
        # draw each open editor; collect those to close after drawing
        to_close = []
        for idx, win in enumerate(self._client_editor_windows):
            if not win["open"]:
                to_close.append(idx)
                continue

            lidx = win["layout_idx"]
            cidx = win["client_idx"]

            # validate indices
            if not (0 <= lidx < len(self.layouts)) or not (0 <= cidx < len(self.layouts[lidx].clients)):
                to_close.append(idx)
                continue

            layout = self.layouts[lidx]
            client = layout.clients[cidx]

            # unique window title/id (ImGui uses text before ## as visible, after ## as unique id)
            title = f"Edit Client: {client.email}##{lidx}:{cidx}"
            if PyImGui.begin(title, True, PyImGui.WindowFlags.AlwaysAutoResize):

                PyImGui.text(f"Layout: {layout.layout_name}")
                PyImGui.separator()
                
                start_x = PyImGui.get_cursor_pos_x()
                PyImGui.text("Alias:")
                PyImGui.same_line(start_x + 50, -1)
                PyImGui.push_item_width(200)
                client.alias = PyImGui.input_text(f"##{client.email}_alias", client.alias, 0)
                start_x = PyImGui.get_cursor_pos_x()
                PyImGui.text("Email:")
                PyImGui.same_line(start_x + 50, -1)
                client.email = PyImGui.input_text(f"##{client.email}_email", client.email, 0)
                PyImGui.pop_item_width()
                PyImGui.push_item_width(100)
                PyImGui.text("Window Title:")
                PyImGui.same_line(0, -1)
                client.window_title = PyImGui.input_text(f"##{client.email}_window_title", client.window_title, 0)
                PyImGui.same_line(0, -1)
                client.rename_window = PyImGui.checkbox("Rename", client.rename_window)
                PyImGui.pop_item_width()
                
                PyImGui.separator()
                PyImGui.text("Position and Size (px):")
                
                client.x = slider_input_int("X", int(client.x), -100, int(screen_width))
                client.y = slider_input_int("Y", int(client.y), -100, int(screen_height))

                client.width  = slider_input_int("Width",  int(client.width),  0, int(screen_width))
                client.height = slider_input_int("Height", int(client.height), 0, int(screen_height))
                
                client.show_overlay = PyImGui.checkbox("Preview Position", getattr(client, "show_overlay", False))
                color = PyImGui.color_edit4("Color", client.color.to_tuple_normalized())
                client.color = Color.from_tuple(color)
                
                PyImGui.separator()

                client.borderless = PyImGui.checkbox("Borderless", client.borderless)
                PyImGui.show_tooltip("this action is non reversable from the client side; the client must be restarted to restore borders")
                PyImGui.same_line(0, -1)
                client.always_on_top = PyImGui.checkbox("Always on Top", getattr(client, "always_on_top", False))
                client.opacity = PyImGui.slider_int("Opacity", getattr(client, "opacity", 255), 0, 255)

                if PyImGui.button("Save"):
                    self.save_layouts()

                PyImGui.same_line(0, -1)
                """if PyImGui.button("Remove From Layout"):
                    layout.remove_client(client)
                    self.save_layouts()
                    to_close.append(idx)  # close this editor; client is gone"""
            
                accounts = GLOBAL_CACHE.ShMem.GetAllAccountData()
                if any(acc.AccountEmail == client.email for acc in accounts):
                    if PyImGui.button("Apply to Client Now"):
                        # send messages to that client
                        if client.rename_window:
                            _send_message_to(SharedCommandType.SetWindowTitle, client.email, ExtraData=(client.window_title, "", "", ""))
                        _send_message_to(SharedCommandType.SetWindowGeometry, client.email, params=(int(client.x), int(client.y), int(client.width), int(client.height)))
                        _send_message_to(SharedCommandType.SetBorderless, client.email, params=(float(client.borderless), 0.0, 0.0, 0.0))
                        _send_message_to(SharedCommandType.SetAlwaysOnTop, client.email, params=(float(client.always_on_top), 0.0, 0.0, 0.0))
                        _send_message_to(SharedCommandType.SetOpacity, client.email, params=(float(client.opacity), 0.0, 0.0, 0.0))
                
                PyImGui.same_line(0, -1)
                if PyImGui.button("Close"):
                    to_close.append(idx)

            PyImGui.end()

        # remove closed windows (from the end to keep indices valid)
        for i in reversed(to_close):
            if 0 <= i < len(self._client_editor_windows):
                self._client_editor_windows.pop(i)




window_manager = WindowLayouts()
layout_manager_window_open = False

draw_screen_rect = False

def DrawMainWindow():
    global layout_manager_window_open, draw_screen_rect
    icon = IconsFontAwesome5.ICON_GRIP_HORIZONTAL

    if PyImGui.begin(f"{icon} {MODULE_NAME}", True,
                     PyImGui.WindowFlags.AlwaysAutoResize | PyImGui.WindowFlags.MenuBar):

        if PyImGui.begin_menu_bar():
            if PyImGui.begin_menu("Edit Layouts"):
                # Visible toggle inside the menu
                layout_manager_window_open = PyImGui.checkbox("Layout Manager", layout_manager_window_open)
                PyImGui.end_menu()
            PyImGui.end_menu_bar()
        
        PyImGui.text("Manage and apply window layouts to clients.")
        layouts = window_manager.get_all_layouts()
        layout_names = [l.layout_name for l in layouts]
        if not layout_names:
            layout_names = ["<no layouts>"]

        # clamp index
        if not (0 <= window_manager._lcw_selected_layout_idx < len(layout_names)):
            window_manager._lcw_selected_layout_idx = 0 if layouts else -1

        prev_idx = window_manager._lcw_selected_layout_idx
        window_manager._lcw_selected_layout_idx = PyImGui.combo("Layout", window_manager._lcw_selected_layout_idx, layout_names)

        # reset client selection if layout changed
        if window_manager._lcw_selected_layout_idx != prev_idx:
            window_manager._lcw_selected_client_idx = -1

        PyImGui.separator()
        PyImGui.text("Clients")
        
        if 0 <= window_manager._lcw_selected_layout_idx < len(layouts):
            layout = layouts[window_manager._lcw_selected_layout_idx]
            if not layout.clients:
                PyImGui.text("<no clients>")
            else:
                for i, c in enumerate(layout.clients):
                    PyImGui.text(f"{c.alias} ({c.email})")
                    PyImGui.same_line(0, -1)
                    if PyImGui.button(f"Edit##{i}"):
                        window_manager.open_client_editor(window_manager._lcw_selected_layout_idx, i)
                
    PyImGui.end()



def main():
    global layout_manager_window_open, draw_screen_rect

    DrawMainWindow()
    if layout_manager_window_open:
        window_manager.draw_window()
    
    window_manager.draw_client_editors()

    for layout in window_manager.layouts:
        for c in layout.clients:
            if getattr(c, "show_overlay", False):
                argb = c.color.to_argb()
                white = ColorPalette.GetColor("white").to_argb()
                faded_argb = c.color.copy()
                faded_argb.set_a(100)  # low alpha for filled rect
                screen_overlay.show(True)
                screen_overlay.begin()

                screen_overlay.draw_rect_filled(int(c.x), int(c.y), int(c.width), int(c.height), faded_argb.to_argb())
                screen_overlay.draw_rect(int(c.x), int(c.y), int(c.width), int(c.height), argb, 2.0)
                screen_overlay.draw_text_box(int(c.x), int(c.y), int(c.width), int(c.height), "Sample Text Box", white, px_size=48.0, hcenter=True, vcenter=True)
                screen_overlay.end()

if __name__ == "__main__":
    main()
