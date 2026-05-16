
from enum import Enum

import PyImGui
import PyUIManager
import time
from typing import Dict, List, Optional
import json
import PyOverlay
from collections import deque, defaultdict

from Py4GWCoreLib.py4gwcorelib_src.FrameCache import frame_cache
from .Py4GWcorelib import ConsoleLog, Console
from .enums_src.Item_enums import INVENTORY_BAGS, INVENTORY_WITH_EQUIPMENT_BAGS, STORAGE_BAGS, Bags, SalvageMode
from .enums_src.UI_enums import WindowID
from dataclasses import dataclass, field
from .native_src.internals.types import Vec2f
from typing import Any, TypedDict
from .Scanner import Scanner

# —— Constants ——————————————————
NPC_DIALOG_HASH    = 3856160816
DEFAULT_OFFSET     = [2, 0, 0, 1]
DIALOG_CHILD_OFFSET = list(DEFAULT_OFFSET)

# —— Globals —————————————————


class UIManager:  
    _overlay = PyOverlay.Overlay()
    _devtext_dialog_proc_cache: int = 0
    
    class IOEvent(TypedDict):
        timestamp: int
        event_type: str
        mouse_pos: tuple[float, float]
        details: Dict[str, Any]
     
    frame_id_callbacks: list[int] = []
    frame_id_io_events: Dict[int, List[IOEvent]] = defaultdict(list)
    
    @staticmethod
    def RegisterFrameIOEventCallback(frame_id: int):
        """
        Register a frame ID to track IO events.

        :param frame_id: The frame ID to register.
        """
        if frame_id not in UIManager.frame_id_callbacks:
            UIManager.frame_id_callbacks.append(frame_id)
            
    @staticmethod
    def UnregisterFrameIOEventCallback(frame_id: int):
        """
        Unregister a frame ID from tracking IO events.

        :param frame_id: The frame ID to unregister.
        """
        if frame_id in UIManager.frame_id_callbacks:
            UIManager.frame_id_callbacks.remove(frame_id)
            if frame_id in UIManager.frame_id_io_events:
                del UIManager.frame_id_io_events[frame_id]
                
    @staticmethod
    def IsMouseOver(frame_id: int) -> bool:
        """
        Check if the mouse is over a specific frame.

        :param frame_id: The ID of the frame.
        :return: bool: True if the mouse is over the frame, False otherwise.
        """
        import PyImGui
        from Py4GWCoreLib.ImGui import ImGui
        
        io = PyImGui.get_io()
        
        left, top, right, bottom = UIManager.GetFrameCoords(frame_id)
        width = right - left
        height = bottom - top
        
        return ImGui.is_mouse_in_rect((left, top, width, height),(io.mouse_pos_x, io.mouse_pos_y))
    
    @staticmethod
    def _UpdateFrameIOEvents():
        """
        Update IO events for registered frame IDs.
        """
        import PyImGui
        from Py4GW import Game
        from .enums_src.IO_enums import MouseButton

        io = PyImGui.get_io()
        mouse_pos = (io.mouse_pos_x, io.mouse_pos_y)
        timestamp = Game.get_tick_count64()
        
        for frame_id in UIManager.frame_id_callbacks:
            if not UIManager.FrameExists(frame_id):
                continue
            
            if not UIManager.IsMouseOver(frame_id):
                continue
            
            is_left_mouse_clicked = PyImGui.is_mouse_clicked(MouseButton.Left.value)
            is_right_mouse_clicked = PyImGui.is_mouse_clicked(MouseButton.Right.value)
            is_middle_mouse_clicked = PyImGui.is_mouse_clicked(MouseButton.Middle.value)
            is_double_clicked = PyImGui.is_mouse_double_clicked(MouseButton.Left.value)
            scroll_y_delta = io.mouse_wheel
            scroll_x_delta = io.mouse_wheel_h
            
            def _add_event(event_type: str, details: Dict[str, Any] = {}):
                event: UIManager.IOEvent = {
                    "timestamp": timestamp,
                    "event_type": event_type,
                    "mouse_pos": mouse_pos,
                    "details": details
                }

                # ensure list exists for this frame
                if frame_id not in UIManager.frame_id_io_events:
                    UIManager.frame_id_io_events[frame_id] = []

                # search for existing event and update instead of adding a duplicate
                for i, existing in enumerate(UIManager.frame_id_io_events[frame_id]):
                    if existing.get("event_type") == event_type:
                        UIManager.frame_id_io_events[frame_id][i] = event
                        break
                else:
                    # not found -> append new
                    UIManager.frame_id_io_events[frame_id].append(event)
                
            if is_left_mouse_clicked:
                _add_event("left_mouse_clicked")
            
            if is_right_mouse_clicked:
                _add_event("right_mouse_clicked")
                
            if is_middle_mouse_clicked:
                _add_event("middle_mouse_clicked")
                
            if is_double_clicked:
                _add_event("double_clicked")
                
            if scroll_y_delta != 0.0:
                _add_event("mouse_wheel_scrolled", {"scroll_y_delta": scroll_y_delta})
                
            if scroll_x_delta != 0.0:
                _add_event("mouse_wheel_scrolled_horizontal", {"scroll_x_delta": scroll_x_delta})
                
    @staticmethod
    def GetIOEventsForFrame(frame_id: int) -> List[IOEvent]:
        """
        Get the list of IO events for a specific frame ID.

        :param frame_id: The frame ID to retrieve events for.
        :return: List[IOEvent]: List of IO events for the frame.
        """
        #lazy load the list if it doesn't exist
        if frame_id not in UIManager.frame_id_callbacks:
            UIManager.frame_id_callbacks.append(frame_id)
        
        return UIManager.frame_id_io_events.get(frame_id, [])
    
    @staticmethod
    def RegisterFrameIOCallbacks():
        """
        Register the frame IO event update callback.
        """
        import PyCallback
        PyCallback.PyCallback.Register(
            "UIManager.UpdateFrameIOEvents",
            PyCallback.Phase.Data,
            UIManager._UpdateFrameIOEvents,
            priority=2,
            context=PyCallback.Context.Draw
        )
   
    @staticmethod
    def ConstructFramePath(frame_id: int) -> str:
        """
        Constructs the full path for an offset-based frame by traversing up the parent chain.

        :param frame_id: The frame ID to construct the path for.
        :return: A string path in the format "hashed_parent,offset1,offset2,...", or None if no valid hashed parent is found.
        """
        if frame_id == 0:
            return ""
        try:
            current_frame = PyUIManager.UIFrame(frame_id)
        except Exception as e:
            print(f"[ERROR] Failed to create UIFrame with frame_id={frame_id}: {e}")
            return ""  # Return empty string on error
        
        # If the frame itself has a hash, return it immediately
        if current_frame.frame_hash != 0:
            return str(current_frame.frame_hash)

        path = []
        parent_hash = None

        # Traverse up the parent hierarchy until we find a hashed parent
        while current_frame.frame_id != 0:
            parent_frame = PyUIManager.UIFrame(current_frame.parent_id)

            # Store child offset
            path.append(str(current_frame.child_offset_id))

            # If we found a parent with a hash, stop and use it as the root
            if parent_frame.frame_hash:
                parent_hash = parent_frame.frame_hash
                break

            current_frame = parent_frame  # Move up to the parent

        # If no hashed parent was found, return None (invalid case)
        if parent_hash == 0:
            return ""

        # Construct and return the full path
        return str(parent_hash) + "," + ",".join(reversed(path))
    
    @staticmethod
    def SaveEntryToJSON(filename: str, frame_id: int, alias: str):
        """Writes or updates an entry in a JSON file."""
        try:
            with open(filename, "r", encoding="utf-8") as file:
                data: Dict[str, str] = json.load(file)  # Load existing data
        except (FileNotFoundError, json.JSONDecodeError):
            data = {}  # Start fresh if file doesn't exist or is invalid

        frame_path = UIManager.ConstructFramePath(frame_id)

        if frame_path:  # Ensure the path is valid before saving
            data[frame_path] = alias

        with open(filename, "w", encoding="utf-8") as file:
            json.dump(data, file, indent=4)  # Save back to file

    @staticmethod
    def GetEntryFromJSON(filename: str, frame_id: int) -> str:
        """
        Reads an entry from a JSON file by constructing the frame's path.

        :param filename: The JSON file to read from.
        :param frame_id: The frame ID to locate.
        :return: The alias if found, otherwise None.
        """
        try:
            with open(filename, "r", encoding="utf-8") as file:
                data = json.load(file)  # Load JSON data
        except (FileNotFoundError, json.JSONDecodeError):
            return "" # Return empty string if file doesn't exist or is invalid

        frame_path = UIManager.ConstructFramePath(frame_id)
        
        return data.get(frame_path) or ""  # Return the alias if found, otherwise an empty string

    @staticmethod
    def GetFrameIDByCustomLabel(filename: str = ".\\Py4GWCoreLib\\frame_aliases.json", frame_label: str = "Game") -> int:
        """
        Finds the frame_id of a UIFrame by matching its constructed path with a stored alias in the JSON file.

        :param filename: The JSON file containing frame mappings.
        :param frame_label: The label corresponding to a hashed frame path.
        :return: The frame_id if found, otherwise 0.
        """
        try:
            with open(filename, "r", encoding="utf-8") as file:
                data = json.load(file)  # Load JSON data
        except (FileNotFoundError, json.JSONDecodeError):
            return 0  # Return 0 if the file is missing or invalid

        # Find the frame path corresponding to the given label
        target_path = next((path for path, alias in data.items() if alias == frame_label), None)
        if not target_path:
            return 0  # Label not found in JSON

        # Get all frame IDs
        frame_array = UIManager.GetFrameArray()

        # Search through frames
        for frame_id in frame_array:
            frame = PyUIManager.UIFrame(frame_id)  # Create UIFrame object
            frame_path = UIManager.ConstructFramePath(frame.frame_id)  # Get full path

            if frame_path == target_path:
                return frame.frame_id  # Found the correct frame_id

        return 0  # No matching frame found


    @staticmethod
    def GetFrameLogs() -> List[tuple[int, int, str]]:
        """
        Get the frame logs.

        :return: list of tuples: Each tuple contains (timestamp, frame_id, frame_label).
        """
        return PyUIManager.UIManager.get_frame_logs()
    
    @staticmethod
    def ClearFrameLogs() -> None:
        """
        Clear the frame logs.
        """
        PyUIManager.UIManager.clear_frame_logs()
    
    @staticmethod
    def GetUIMessageLogs() -> List[tuple[int, int, bool, bool, int, list[int], list[int]]]:
        """
        Get the UI message logs.

        :return: list of tuples: Each tuple contains (timestamp, msgid, incoming, is_frame_message, frame_id, wparam_bytes, lparam_bytes).
        """
        return PyUIManager.UIManager.get_ui_message_logs()
    
    @staticmethod
    def ClearUIMessageLogs() -> None:
        """
        Clear the UI message logs.
        """
        PyUIManager.UIManager.clear_ui_message_logs()
        
    @staticmethod
    def GetFrameByID(frame_id) -> PyUIManager.UIFrame:
        """
        Get the frame by its ID.

        :param frame_id: The ID of the frame.
        :return: PyUIManager.UIFrame: The UIFrame object.
        """
        return PyUIManager.UIFrame(frame_id)
    
    @staticmethod
    def GetFrameIDByLabel(label):
        """
        Get the frame ID by its label.

        :param label: The label of the frame.
        :return: int: The frame ID, or -1 if not found.
        """
        return PyUIManager.UIManager.get_frame_id_by_label(label)
    
    @staticmethod
    def GetFrameIDByHash(hash):
        """
        Get the frame ID by its hash value.

        :param hash: The hash value of the frame.
        :return: int: The frame ID, or -1 if not found.
        """
        return PyUIManager.UIManager.get_frame_id_by_hash(hash)

    @staticmethod
    def GetTextLanguage() -> int:
        return PyUIManager.UIManager.get_text_language()

    @staticmethod
    def GetChildFrameByFrameId(parent_frame_id: int, child_offset: int) -> int:
        return PyUIManager.UIManager.get_child_frame_by_frame_id(parent_frame_id, child_offset)

    @staticmethod
    def GetChildFramePathByFrameId(parent_frame_id: int, child_offsets: list[int]) -> int:
        return PyUIManager.UIManager.get_child_frame_path_by_frame_id(parent_frame_id, child_offsets)

    @staticmethod
    def GetParentFrameID(frame_id: int) -> int:
        return PyUIManager.UIManager.get_parent_frame_id(frame_id)

    @staticmethod
    def GetFrameContext(frame_id: int) -> int:
        return int(PyUIManager.UIManager.get_frame_context(frame_id) or 0)

    @staticmethod
    def GetFirstChildFrameID(parent_frame_id: int) -> int:
        return int(PyUIManager.UIManager.get_first_child_frame_id(parent_frame_id) or 0)

    @staticmethod
    def GetLastChildFrameID(parent_frame_id: int) -> int:
        return int(PyUIManager.UIManager.get_last_child_frame_id(parent_frame_id) or 0)

    @staticmethod
    def GetNextChildFrameID(frame_id: int) -> int:
        return int(PyUIManager.UIManager.get_next_child_frame_id(frame_id) or 0)

    @staticmethod
    def GetPrevChildFrameID(frame_id: int) -> int:
        return int(PyUIManager.UIManager.get_prev_child_frame_id(frame_id) or 0)

    @staticmethod
    def GetItemFrameID(parent_frame_id: int, index: int) -> int:
        return int(PyUIManager.UIManager.get_item_frame_id(parent_frame_id, index) or 0)

    @staticmethod
    def GetTabFrameID(parent_frame_id: int, index: int) -> int:
        return int(PyUIManager.UIManager.get_tab_frame_id(parent_frame_id, index) or 0)
    
    @staticmethod
    def GetHashByLabel(label):
        """
        Get the hash value of a frame by its label.

        :param label: The label of the frame.
        :return: int: The hash value of the frame, or -1 if not found.
        """
        return PyUIManager.UIManager.get_hash_by_label(label)
    
    @staticmethod
    def GetFrameHierarchy():
        """
        Get the frame hierarchy as a dictionary.

        :return: dict: The frame hierarchy.
        """
        return PyUIManager.UIManager.get_frame_hierarchy()
    
    @staticmethod
    def GetFrameCoordsByHash(hash):
        """
        Get the coordinates of a frame by its hash value.

        :param hash: The hash value of the frame.
        :return: tuple: The (x, y),(x1,y1) coordinates of the frame, or None if not found.
        """
        return PyUIManager.UIManager.get_frame_coords_by_hash(hash)
    
    @staticmethod
    def GetFrameArray():
        """
        Get the frame array.

        :return: list: The frame array.
        """
        return PyUIManager.UIManager.get_frame_array()
    
    @staticmethod
    def SendUIMessage(msgid: int, values: list[int],skip_hooks: bool = False ) -> bool:
        return PyUIManager.UIManager.SendUIMessage(msgid, values, skip_hooks)
    
    @staticmethod
    def SendUIMessageRaw(msgid: int, wparam: int, lparam: int, skip_hooks: bool = False ) -> bool:
        return PyUIManager.UIManager.SendUIMessageRaw(msgid, wparam, lparam, skip_hooks)

    @staticmethod
    def SendFrameUIMessage(frame_id: int, message_id: int, wparam: int, lparam: int = 0) -> bool:
        return PyUIManager.UIManager.SendFrameUIMessage(frame_id, message_id, wparam, lparam)

    @staticmethod
    def SendFrameUIMessageWString(frame_id: int, message_id: int, text: str) -> bool:
        return PyUIManager.UIManager.SendFrameUIMessageWString(frame_id, message_id, text)

    @staticmethod
    def DrawOnCompass(session_id: int, points: list[tuple[int, int]]) -> bool:
        return PyUIManager.UIManager.draw_on_compass(session_id, points)

    @staticmethod
    def LoadSettings(data: list[int]) -> None:
        PyUIManager.UIManager.load_settings(data)

    @staticmethod
    def GetSettings() -> list[int]:
        return PyUIManager.UIManager.get_settings()

    @staticmethod
    def GetCurrentTooltipAddress() -> int:
        return PyUIManager.UIManager.get_current_tooltip_address()

    # CreateUIComponent callback binding is intentionally disabled for now.
    # The runtime path was destabilizing validation runs and should only be
    # restored when callback-specific work is resumed.
    #
    # @staticmethod
    # def RegisterCreateUIComponentCallback(callback, altitude: int = -0x8000) -> int:
    #     return int(PyUIManager.UIManager.register_create_ui_component_callback(callback, altitude) or 0)
    #
    # @staticmethod
    # def RemoveCreateUIComponentCallback(handle: int) -> bool:
    #     return bool(PyUIManager.UIManager.remove_create_ui_component_callback(handle))
    
    @staticmethod
    def GetRootFrameID():
        """
        Get the root frame ID.

        :return: int: The root frame ID.
        """
        return PyUIManager.UIManager.get_root_frame_id()
    
    @staticmethod
    def GetChildFrameID (parent_hash: int, child_offsets: List[int]):
        """
        Get the child frame ID.

        :param parent_hash: The parent hash value.
        :param child_offsets: The list of child offsets.
        :return: int: The child frame ID.
        """
        return PyUIManager.UIManager.get_child_frame_id(parent_hash, child_offsets)
    
    @staticmethod
    def GetAllChildFrameIDs(parent_hash: int, child_offsets: List[int]):
        """
        Finds all frame IDs that match the given offset path from the parent hash.
        Unlike GetChildFrameID, this returns *all* frames that match the offset chain.

        :param parent_hash: The root hash of the UI dialog
        :param child_offsets: List of offsets to follow
        :return: List of matching frame IDs
        """
        frame_array = UIManager.GetFrameArray()
        root_frame_id = UIManager.GetFrameIDByHash(parent_hash)

        matching_ids = []

        for fid in frame_array:
            current = PyUIManager.UIFrame(fid)
            offsets = []
            trace = current

            for _ in range(len(child_offsets)):
                offsets.insert(0, trace.child_offset_id)
                if trace.parent_id == 0:
                    break
                trace = PyUIManager.UIFrame(trace.parent_id)

            if trace.frame_id == root_frame_id and offsets == child_offsets:
                matching_ids.append(current.frame_id)

        return matching_ids
    
    @staticmethod
    def SortFramesByVerticalPosition(frame_ids: List[int]):
        positions = []
        for fid in frame_ids:
            frame = PyUIManager.UIFrame(fid)
            y = frame.position.top_on_screen
            positions.append((fid, y))
        return sorted(positions, key=lambda x: x[1])  # Lower Y = higher on screen
    
    @staticmethod
    def ColorFrames(parent_hash: int, child_offsets: List[int], debug: bool = False):
        def RGBToColor(r, g, b, a) -> int:
            return (a << 24) | (b << 16) | (g << 8) | r

        option_offsets = child_offsets
        all_ids = UIManager.GetAllChildFrameIDs(parent_hash, option_offsets)
        
        sorted_frames = UIManager.SortFramesByVerticalPosition(all_ids)

        if debug:
            print(f"All matching frame IDs: {all_ids}")
            for fid, top_y in sorted_frames:
                print(f"Frame ID: {fid}, Top Y: {top_y}")
            
        colors = [
        RGBToColor(0, 255, 0, 200),     # green
        RGBToColor(255, 0, 0, 200),     # red
        RGBToColor(0, 128, 255, 200),   # blue
        RGBToColor(255, 255, 0, 200),   # yellow
        RGBToColor(128, 0, 255, 200),   # purple
        RGBToColor(255, 128, 0, 200),   # orange
        RGBToColor(0, 255, 255, 200),   # cyan
        ]
        for i, (frame_id, _) in enumerate(sorted_frames):
            if i >= len(colors):
                break
            UIManager().DrawFrame(frame_id, colors[i])
            
    @staticmethod
    def FrameClick(frame_id: int) -> None:
        from Py4GWCoreLib import UIManager

        if not UIManager.FrameExists(frame_id):
            return
        
        PyUIManager.UIManager.button_click(frame_id)    
        
    @staticmethod
    def TestMouseAction(
        frame_id: int,
        current_state: int,
        wparam_value: int,
        lparam_value: int = 0,
    ) -> None:
        from Py4GWCoreLib import UIManager

        if not UIManager.FrameExists(frame_id):
            return
        PyUIManager.UIManager.test_mouse_action(frame_id, current_state, wparam_value, lparam_value)

    @staticmethod
    def TestMouseClickAction(
        frame_id: int,
        current_state: int,
        wparam_value: int,
        lparam_value: int = 0,
    ) -> None:
        from Py4GWCoreLib import UIManager

        if not UIManager.FrameExists(frame_id):
            return
        PyUIManager.UIManager.test_mouse_click_action(frame_id, current_state, wparam_value, lparam_value)

            
    @staticmethod
    def IsWorldMapShowing():
        """
        Check if the world map is showing.

        :return: bool: True if the world map is showing, False otherwise.
        """
        return PyUIManager.UIManager.is_world_map_showing()

    @staticmethod
    def IsUIDrawn() -> bool:
        return PyUIManager.UIManager.is_ui_drawn()

    @staticmethod
    def AsyncDecodeStr(enc_str: str) -> str:
        return PyUIManager.UIManager.async_decode_str(enc_str)

    @staticmethod
    def IsValidEncStr(enc_str: str) -> bool:
        return PyUIManager.UIManager.is_valid_enc_str(enc_str)

    @staticmethod
    def IsValidEncBytes(enc_bytes: bytes) -> bool:
        return bool(PyUIManager.UIManager.is_valid_enc_bytes(bytes(enc_bytes or b"")))

    @staticmethod
    def UInt32ToEncStr(value: int) -> str:
        return PyUIManager.UIManager.uint32_to_enc_str(value)

    @staticmethod
    def EncStrToUInt32(enc_str: str) -> int:
        return PyUIManager.UIManager.enc_str_to_uint32(enc_str)

    @staticmethod
    def SetOpenLinks(toggle: bool) -> None:
        PyUIManager.UIManager.set_open_links(toggle)
    
    @staticmethod
    def IsShiftScreenshot():
        """
        Check if the shift screenshot is enabled.

        :return: bool: True if shift screenshot is enabled, False otherwise.
        """
        return PyUIManager.UIManager.is_shift_screenshot()
            
    @staticmethod
    def GetFPSLimit():
        """
        Get the frame limit.

        :return: int: The frame limit.
        """
        return PyUIManager.UIManager.get_frame_limit()
    
    @staticmethod
    def SetFPSLimit(limit):
        """
        Set the frame limit.

        :param limit: The frame limit.
        """
        PyUIManager.UIManager.set_frame_limit(limit)
        
    @staticmethod
    def IsFrameCreated(frame_id):
        """
        Check if a frame is created.

        :param frame_id: The ID of the frame.
        :return: bool: True if the frame is created, False otherwise.
        """
        return PyUIManager.UIFrame(frame_id).is_created
    
    @staticmethod
    def IsVisible(frame_id):
        """
        Check if a frame is visible.

        :param frame_id: The ID of the frame.
        :return: bool: True if the frame is visible, False otherwise.
        """
        return PyUIManager.UIFrame(frame_id).is_visible
    
    @staticmethod
    def FrameExists(frame_id):
        """
        Check if a frame exists.

        :param frame_id: The ID of the frame.
        :return: bool: True if the frame exists, False otherwise.
        """
        frame_aray = UIManager.GetFrameArray()
        if frame_id not in frame_aray:
            return False
        return UIManager.IsFrameCreated(frame_id) and UIManager.IsVisible(frame_id)
    
    @staticmethod
    def GetParentID(frame_id):
        """
        Get the parent ID of a frame.

        :param frame_id: The ID of the frame.
        :return: int: The parent ID of the frame. 
        """
        return PyUIManager.UIFrame(frame_id).parent_id
    
    @staticmethod
    def GetViewPortScale(frame_id) -> tuple[float, float]:
        """
        Get the viewport scale of a frame.

        :param frame_id: The ID of the frame.
        :return: float: The viewport scale of the frame.
        """
        frame = PyUIManager.UIFrame(frame_id)
        return frame.position.viewport_scale_x, frame.position.viewport_scale_y
    
    @staticmethod
    def GetViewportDimensions(frame_id) -> tuple[float, float]:
        """
        Get the viewport dimensions of a frame.

        :param frame_id: The ID of the frame.
        :return: float: The viewport dimensions of the frame.
        """
        frame = PyUIManager.UIFrame(frame_id)
        return frame.position.viewport_width, frame.position.viewport_height
    
    
    @staticmethod
    def GetFrameCoords(frame_id) -> tuple[int, int, int, int]:
        """
        Get the coordinates of a frame.

        :param frame_id: The ID of the frame.
        :return: top, left, bottom, right coordinates of the frame.
        """
        frame = PyUIManager.UIFrame(frame_id)
        top = frame.position.top_on_screen
        left = frame.position.left_on_screen
        bottom = frame.position.bottom_on_screen
        right = frame.position.right_on_screen
        return left,top, right, bottom
    
    
    @staticmethod
    def GetContentFrameCoords(frame_id) -> tuple[int, int, int, int]:
        """
        Return (left, top, right, bottom) screen coords for the *content area*
        of a mission map frame, with Y correctly flipped into screen space.
        """
        frame = PyUIManager.UIFrame(frame_id)
        viewport_scale = Vec2f(*UIManager.GetViewPortScale(frame_id))
        root_frame_id = UIManager.GetRootFrameID()
        viewport_dims  = Vec2f(*UIManager.GetViewportDimensions(root_frame_id))
        _,height = viewport_dims.to_tuple()

        # Raw content coords (frame-local)
        left   = frame.position.content_left   * viewport_scale.x
        top    = (height - frame.position.content_top)   * viewport_scale.y
        right  = frame.position.content_right  * viewport_scale.x
        bottom = (height - frame.position.content_bottom) * viewport_scale.y


        return int(left), int(top), int(right), int(bottom)
        
    def DrawFrame(self,frame_id:int, draw_color:int):
        """
        Draw a frame on the UI.

        :param frame_id: The ID of the frame.
        """
        if not UIManager.FrameExists(frame_id):
            return
        
        left, top, right, bottom = UIManager.GetFrameCoords(frame_id)
        p1 = PyOverlay.Point2D(left, top)
        p2 = PyOverlay.Point2D(right, top)
        p3 = PyOverlay.Point2D(right, bottom)
        p4 = PyOverlay.Point2D(left, bottom)
        UIManager._overlay.BeginDraw()
        UIManager._overlay.DrawQuadFilled(p1,p2,p3,p4, draw_color)
        UIManager._overlay.EndDraw()
    
        
    def DrawFrameOutline(self,frame_id, draw_color:int, thickness: float = 1.0):
        """
        Draw an outline of a frame on the UI.

        :param frame_id: The ID of the frame.
        """
        if not UIManager.FrameExists(frame_id):
            return
        
        left, top, right, bottom = UIManager.GetFrameCoords(frame_id)
        p1 = PyOverlay.Point2D(left, top)
        p2 = PyOverlay.Point2D(right, top)
        p3 = PyOverlay.Point2D(right, bottom)
        p4 = PyOverlay.Point2D(left, bottom)
        UIManager._overlay.BeginDraw()
        UIManager._overlay.DrawQuad(p1,p2,p3,p4, draw_color, thickness)
        UIManager._overlay.EndDraw()

    @staticmethod
    def GetPreferenceOptions(pref:int) -> List[int]:
        return PyUIManager.UIManager.get_preference_options(pref)
    
    @staticmethod
    def GetEnumPreference(pref:int) -> int:
        return PyUIManager.UIManager.get_enum_preference(pref)
    
    @staticmethod
    def GetIntPreference(pref:int) -> int:
        return PyUIManager.UIManager.get_int_preference(pref)
    
    @staticmethod
    def GetStringPreference(pref:int) -> str:
        return PyUIManager.UIManager.get_string_preference(pref)
    
    @staticmethod
    def GetBoolPreference(pref:int) -> bool:
        return PyUIManager.UIManager.get_bool_preference(pref)
    
    @staticmethod
    def SetEnumPreference(pref:int, value:int) -> None:
        PyUIManager.UIManager.set_enum_preference(pref, value)
    
    @staticmethod
    def SetIntPreference(pref:int, value:int) -> None:
        PyUIManager.UIManager.set_int_preference(pref, value)
        
    @staticmethod
    def SetStringPreference(pref:int, value:str) -> None:
        PyUIManager.UIManager.set_string_preference(pref, value)
        
    @staticmethod
    def SetBoolPreference(pref:int, value:bool) -> None:
        PyUIManager.UIManager.set_bool_preference(pref, value)
        
    @staticmethod
    def GetKeyMappings() -> List[int]:
        return PyUIManager.UIManager.get_key_mappings()
    
    @staticmethod
    def SetKeyMappings(mappings: List[int]) -> None:
        PyUIManager.UIManager.set_key_mappings(mappings)
        
    @staticmethod
    def Keydown(key:int, frame_id:int) -> None:
        PyUIManager.UIManager.key_down(key,frame_id)
        
    @staticmethod
    def Keyup(key:int, frame_id:int) -> None:
        PyUIManager.UIManager.key_up(key,frame_id)
        
    @staticmethod
    def Keypress(key:int, frame_id:int) -> None:
        PyUIManager.UIManager.key_press(key,frame_id)
        
    @staticmethod
    def GetWindoPosition(window_id: int) -> list[int]:
        """
        Get the window position.

        :return: x,y,x1,y1 coordinates of the window.
        """
        return PyUIManager.UIManager.get_window_position(window_id)
    
    @staticmethod
    def IsWindowVisible(window_id: int) -> bool:
        """
        Check if a window is visible.

        :return: True if the window is visible, False otherwise.
        """
        return PyUIManager.UIManager.is_window_visible(window_id)
    
    @staticmethod
    def SetWindowVisible(window_id: int, visible: bool) -> None:
        """
        Set the visibility of a window.

        :param window_id: The ID of the window.
        :param visible: True to show the window, False to hide it.
        """
        PyUIManager.UIManager.set_window_visible(window_id, visible)
        
    @staticmethod
    def SetWindowPosition(window_id: int, position: list[int]) -> None:
        """
        Set the position of a window.

        :param window_id: The ID of the window.
        :param x: The x-coordinate.
        :param y: The y-coordinate.
        """
        PyUIManager.UIManager.set_window_position(window_id, position)
    
    @staticmethod
    def IsLockedChestWindowVisible() -> bool:
        """
        Check if the chest window is visible.

        :return: True if the chest window is visible, False otherwise.
        """
        
        fid = UIManager.GetChildFrameID(3856160816, [1])
        return fid != 0 and UIManager.FrameExists(fid)
    
    @staticmethod
    def IsNPCDialogVisible() -> bool:
        """
        Check if the NPC dialog is visible.

        :return: True if the NPC dialog is visible, False otherwise.
        """
        fid = UIManager.GetFrameIDByHash(NPC_DIALOG_HASH)
        return fid != 0 and UIManager.FrameExists(fid)

    @staticmethod
    def FindDialogOffset() -> None:
        """Auto-detects DIALOG_CHILD_OFFSET for the option-container."""
        global DIALOG_CHILD_OFFSET
        root = UIManager.GetFrameIDByHash(NPC_DIALOG_HASH)
        if root == 0 or not UIManager.IsVisible(root):
            return

        # build parent->children map
        frame_array = UIManager.GetFrameArray()
        children_map = defaultdict(list)
        for fid in frame_array:
            try:
                pid = PyUIManager.UIFrame(fid).parent_id
                children_map[pid].append(fid)
            except:
                pass

        # BFS: pick the container with the most template_type==1 children
        queue = deque([root])
        best = None
        best_count = 0
        while queue:
            cur = queue.popleft()
            kids = children_map.get(cur, [])
            count = sum(
                1 for c in kids
                if UIManager.IsVisible(c)
                and getattr(PyUIManager.UIFrame(c), "template_type", None) == 1
            )
            if count > best_count and count >= 2:
                best_count, best = count, cur
            for c in kids:
                queue.append(c)

        if not best:
            return

        # build index-path from root → best
        path = []
        cur = best
        while cur != root:
            parent = PyUIManager.UIFrame(cur).parent_id
            siblings = children_map[parent]
            path.insert(0, siblings.index(cur))
            cur = parent

        DIALOG_CHILD_OFFSET = path
    
    @staticmethod
    def GetDialogButtonIDs(debug: bool = False) -> list[int]:
        """
        Returns the list of visible, template_type==1 button frame-IDs,
        sorted top→bottom. Pass debug=True to log offset detection.
        """
        # detect offset once
        if DIALOG_CHILD_OFFSET == DEFAULT_OFFSET:
            UIManager.FindDialogOffset()

        # try the offset first
        ids = UIManager.GetAllChildFrameIDs(NPC_DIALOG_HASH, DIALOG_CHILD_OFFSET)
        valid = [
            fid for fid in ids
            if UIManager.IsVisible(fid)
            and getattr(PyUIManager.UIFrame(fid), "template_type", None) == 1
        ]
        if valid:
            sorted_ids = [fid for fid, _ in UIManager.SortFramesByVerticalPosition(valid)]
            if debug:
                ConsoleLog("DialogHelper", f"Offset IDs → {sorted_ids}", Console.MessageType.Info)
            return sorted_ids

        # fallback BFS over entire tree
        if debug:
            ConsoleLog("DialogHelper", "Falling back to BFS for dialog buttons", Console.MessageType.Info)

        root = UIManager.GetFrameIDByHash(NPC_DIALOG_HASH)
        frame_array = UIManager.GetFrameArray()
        children_map = defaultdict(list)
        for fid in frame_array:
            try:
                pid = PyUIManager.UIFrame(fid).parent_id
                children_map[pid].append(fid)
            except:
                pass

        descendants = []
        queue = deque([root])
        while queue:
            cur = queue.popleft()
            for c in children_map.get(cur, []):
                descendants.append(c)
                queue.append(c)

        valid = [
            fid for fid in descendants
            if UIManager.IsVisible(fid)
            and getattr(PyUIManager.UIFrame(fid), "template_type", None) == 1
        ]
        sorted_ids = [fid for fid, _ in UIManager.SortFramesByVerticalPosition(valid)]
        if debug:
            ConsoleLog("DialogHelper", f"BFS IDs -> {sorted_ids}", Console.MessageType.Info)
        return sorted_ids
    
    @staticmethod
    def ClickDialogButton(choice: int, debug: bool = False) -> bool:
        """
        Click the Nth dialog option (1-based). Returns True if dispatched.
        """
        ids = UIManager.GetDialogButtonIDs(debug)
        idx = choice - 1
        if idx < 0 or idx >= len(ids):
            if debug:
                ConsoleLog("DialogHelper", f"Choice #{choice} out of range", Console.MessageType.Warning)
            return False

        target = ids[idx]
        if debug:
            ConsoleLog(
                "DialogHelper",
                f"Clicking dialog choice #{choice} -> frame {target}",
                Console.MessageType.Info
            )
        UIManager.FrameClick(target)
        return True
    
    @staticmethod
    def GetDialogButtonCount(debug: bool = False) -> int:
        """
        Return the number of visible dialog‐button frames (template_type == 1),
        and log the count if debug=True.
        Log Example: [DialogHelper|Info] Dialog button count 3
        """
        ids = UIManager.GetDialogButtonIDs(debug)
        count = len(ids)

        if debug:
            # Log the count to the console as an info message
            ConsoleLog(
                "DialogHelper",
                f"Dialog button count {count}",
                Console.MessageType.Info
            )

        return count
        
    @staticmethod
    def GetDialogButtonFrames(debug: bool = False) -> list[tuple[int, tuple[int, int, int, int]]]:
        '''
        Returns a list of tuples containing the frame ID and its coordinates
        for all visible dialog button frames (template_type == 1), sorted by their vertical position.
        Each tuple is in the format: (frame_id, (left, top, right, bottom))
        '''
        
        if DIALOG_CHILD_OFFSET == DEFAULT_OFFSET:
            UIManager.FindDialogOffset()

        # --- Attempt offset lookup first ---
        ids_from_offset = UIManager.GetAllChildFrameIDs(NPC_DIALOG_HASH, DIALOG_CHILD_OFFSET)

        valid_frames = []
        for fid in ids_from_offset:
            if fid < 0:
                continue
            
            fr = PyUIManager.UIFrame(fid)
            
            if not fr:
                continue
            
            if not fr.is_visible:
                continue
            
            if fr.template_type != 1:
                continue

            valid_frames.append(
                (
                    fr.frame_id,
                    (
                        fr.position.left_on_screen,
                        fr.position.top_on_screen,
                        fr.position.right_on_screen,
                        fr.position.bottom_on_screen
                    )
                )
            )

        if debug:
            ConsoleLog(
                "DialogHelper",
                f"Dialog button frames with offset {DIALOG_CHILD_OFFSET}: {[fid for fid, _ in valid_frames]}",
                Console.MessageType.Info
            )

        # --- Sort by top_on_screen using cached tuples ---
        valid_frames.sort(key=lambda x: x[1][0])

        if debug:
            ConsoleLog(
                "DialogHelper",
                f"Detected dialog button frames: {valid_frames}",
                Console.MessageType.Info
            )

        # If we found frames, return immediately (no fallback needed)
        if valid_frames:
            return valid_frames

        # --- BFS fallback (heavy, so optimized hard) ---
        if debug:
            ConsoleLog("DialogHelper", "Falling back to BFS for dialog buttons", Console.MessageType.Info)

        # --- Preload the entire frame array + cache UIFrame objects once ---
        frame_ids_all = UIManager.GetFrameArray()
        
        frame_cache : dict[int, PyUIManager.UIFrame] = {}
        for fid in frame_ids_all:
            try:
                frame_cache[fid] = PyUIManager.UIFrame(fid)
            except:
                pass
            
        root = UIManager.GetFrameIDByHash(NPC_DIALOG_HASH)

        # Build children map only once
        children_map = defaultdict(list)
        for fid, fr in frame_cache.items():
            pid = fr.parent_id
            if pid is not None:
                children_map[pid].append(fid)

        # BFS
        descendants = []
        dq = deque([root])
        append_desc = descendants.append
        extend_dq = dq.extend

        while dq:
            current = dq.popleft()
            children = children_map.get(current)
            if children:
                extend_dq(children)
                for c in children:
                    append_desc(c)

        # Filter valid dialog buttons
        bfs_valid = []
        for fid in descendants:
            if fid < 0:
                continue
            
            fr = frame_cache.get(fid)
            if not fr:
                continue
            
            if not fr.is_visible:
                continue
            
            if fr.template_type != 1:
                continue
            bfs_valid.append(fid)

        # Build final dictionary for BFS mode
        result = []
        for fid in bfs_valid:
            fr = frame_cache[fid]
            result.append((
                fid,
                (
                    fr.position.left_on_screen,
                    fr.position.top_on_screen,
                    fr.position.right_on_screen,
                    fr.position.bottom_on_screen
                )
            ))
        
        # Sort by top_on_screen
        result.sort(key=lambda x: x[1][0])

        return result
    
    @staticmethod
    def ConfirmMaxAmountDialog():
        '''
        Confirm the max amount dialog such as those from Trading and Dropping items by clicking the relevant buttons.
        '''
        max_amount = UIManager.GetFrameIDByHash(4008686776)
        drop_offer_confirm = UIManager.GetFrameIDByHash(4014954629)
        
        if UIManager.FrameExists(max_amount):
            UIManager.FrameClick(max_amount)
            
        if UIManager.FrameExists(drop_offer_confirm):
            UIManager.FrameClick(drop_offer_confirm)
    
#region frameInfo
@dataclass
class FrameInfo:
    WindowID: int = 0
    WindowName: str = ""
    WindowLabel: str = ""
    FrameHash: int = 0
    ParentFrameHash: int = 0
    ChildOffsets: list = field(default_factory=list)
    FrameID_source: int = 0
    FrameID: int = 0
    BlackBoard : dict = field(default_factory=dict)
    
    def update_frame_id(self):
        if self.FrameID_source != 0:
            self.FrameID = self.FrameID_source
            return
        
        if self.WindowLabel:
            _hash = UIManager.GetHashByLabel(self.WindowLabel)
            self.FrameID = UIManager.GetFrameIDByHash(_hash)
            #self.FrameID = UIManager.GetFrameIDByLabel(self.WindowLabel)
            return

        if self.FrameHash != 0:
            self.FrameID = UIManager.GetFrameIDByHash(self.FrameHash)
        else:
            self.FrameID = UIManager.GetChildFrameID(self.ParentFrameHash, self.ChildOffsets)
            
    def GetFrameID(self):
        self.update_frame_id()
        return self.FrameID
            
    def FrameExists(self):
        self.update_frame_id()
        return UIManager.FrameExists(self.FrameID)
    
    def DrawFrame(self, color:int):
        if self.FrameExists():
            UIManager().DrawFrame(self.FrameID, color)
            
    def DrawFrameOutline(self, color:int , thickness: float = 1.0):
        if self.FrameExists():
            UIManager().DrawFrameOutline(self.FrameID, color, thickness)
            
    def FrameClick(self, current_state: Optional[int] = None, wparam_value: Optional[int] = None, lparam_value: Optional[int] = None):
        if self.FrameExists():
            UIManager.FrameClick(self.FrameID)
    
            if current_state is not None:
                UIManager.TestMouseAction(self.FrameID, current_state, wparam_value or 0, lparam_value or 0)
            
    def GetCoords(self):
        if self.FrameExists():
            return UIManager.GetFrameCoords(self.FrameID)
        return (0,0,0,0)
    
    def GetContentCoords(self):
        if self.FrameExists():
            return UIManager.GetContentFrameCoords(self.FrameID)
        return (0,0,0,0)
    
    def GetViewPortScale(self):
        if self.FrameExists():
            return UIManager.GetViewPortScale(self.FrameID)
        return (1.0,1.0)
    
    def GetViewportDimensions(self):
        if self.FrameExists():
            return UIManager.GetViewportDimensions(self.FrameID)
        return (0,0)
    
    def IsMouseOver(self):
        if self.FrameExists():
            return UIManager.IsMouseOver(self.FrameID)
        return False
    
    def GetIOEvents(self) -> list[UIManager.IOEvent]:
        if self.FrameExists():
            return UIManager.GetIOEventsForFrame(self.FrameID)
        return []
            
#region WindowFrames

WindowFrames:dict[str, FrameInfo] = {}

class WindowFrame():
    CloseWindowButtonFrame = FrameInfo(
        FrameHash=3738633661,
        WindowLabel="Close Window button"
    )
    
    #region Character Creation
    CharacterDeleteButtonFrame = FrameInfo(
        WindowName="DeleteCharacterButton",
        FrameHash=3379687503
    )

    CharacterFinalDeleteButtonFrame = FrameInfo(
        WindowName="FinalDeleteCharacterButton",
        ParentFrameHash=140452905,
        ChildOffsets=[5,1,15,2]
    )

    CreateCharacterButtonFrame1 = FrameInfo(
        WindowName="CreateCharacterButton1",
        FrameHash=3372446797
    )

    CreateCharacterButtonFrame2 = FrameInfo(
        WindowName="CreateCharacterButton2",
        FrameHash=3973689736,
    )

    CreateCharacterTypeNextButtonFrame = FrameInfo(
        WindowName="CreateCharacterTypeNextButton",
        FrameHash=3110341991
    )

    CreateCharacterNextButtonGenericFrame = FrameInfo(
        WindowName="CreateCharacterNextButtonGeneric",
        FrameHash=1102119410
    )

    FinalCreateCharacterButtonFrame = FrameInfo(
        WindowName="FinalCreateCharacterButton",
        FrameHash=3856299307
    )    
    #endregion Character Creation
       
    MiniMapFrame = FrameInfo(
                    WindowName="MiniMap",
                    WindowLabel="compass",
    )

    PartyWindowFrame = FrameInfo(
        WindowName="PartyWindow",
        FrameHash=3332025202,
        ChildOffsets=[1]
    )

    CancelEnterMissionButton = FrameInfo(
        WindowName="CancelEnterMissionButton",
        ParentFrameHash=2209443298,
        ChildOffsets=[0,1,1]
    )

    ConfirmEnterMissionButton = FrameInfo(
        WindowName="ConfirmEnterMissionButton",
        ParentFrameHash=3617868957,
        ChildOffsets=[2, 6, 100, 2, 6]
    )

    #region Inventory
    InventoryIdentifyAllButton = FrameInfo(
        WindowName = "Inventory",
        FrameHash = 3316689063
    )
    
    InventoryBags = FrameInfo(
        WindowID = WindowID.WindowID_InventoryBags,
        WindowName = "Inventory Bags",
        FrameHash = 291586130
    )
    
    InventoryBackpack = FrameInfo(
        WindowID = WindowID.WindowID_Inventory,
        WindowName = "Inventory Bags",
        ParentFrameHash = 2874675009,
        ChildOffsets = [0]
    )
    
    #endregion Inventory
    
    #region Xunlai Storage
    Xunlai_Window = FrameInfo(
        WindowName = "Xunlai Storage",
        FrameHash = 2315448754
    )
    
    Xunlai_Storage = FrameInfo(
        WindowName = "Xunlai Storage",
        ParentFrameHash = 2315448754,
        ChildOffsets = [0]
    )
    
    Xunlai_FundsFrame = FrameInfo(
        ParentFrameHash = 2315448754,
        ChildOffsets = [2]
    )
    
    Xunlai_DepositFundsButton = FrameInfo(
        ParentFrameHash = 2315448754,
        ChildOffsets = [3]
    )
    
    Xunlai_WithdrawFundsButton = FrameInfo(
        ParentFrameHash = 2315448754,
        ChildOffsets = [4]
    )
    
    # "2315448754,5": "Xunlai Window.Deposit All Materials",
    Xunlai_DepositAllMaterialsButton = FrameInfo(
        ParentFrameHash = 2315448754,
        ChildOffsets = [5]
    )
    
    Xunlai_GoldValue = FrameInfo(
        ParentFrameHash = 2315448754,
        ChildOffsets = [2, 2]
    )
    
    Xunlai_PlatinumValue = FrameInfo(
        ParentFrameHash = 2315448754,
        ChildOffsets = [2, 3]
    )
    
    Xunlai_GoldIcon = FrameInfo(
        ParentFrameHash = 2315448754,
        ChildOffsets = [2, 0]
    )
    
    Xunlai_PlatinumIcon = FrameInfo(
        ParentFrameHash = 2315448754,
        ChildOffsets = [2, 1]
    )
    
    Xunlai_Tab1 = FrameInfo(
        ParentFrameHash = 2315448754,
        ChildOffsets = [0, 4294967295]
    )
    
    Xunlai_Tab1_Content = FrameInfo(
        ParentFrameHash = 2315448754,
        ChildOffsets = [0, 0]
    )
    
    #endregion Xunlai Storage
    
    #region Salvage
    SalvageOptionsFrame = FrameInfo(
        WindowName="SalvageOptionsFrame",
        FrameHash=684387150
    )
    
    SalvageOptionCancelButton = FrameInfo(
        WindowName="CancelSalvageOptionsButton",
        ParentFrameHash=684387150,
        ChildOffsets=[1]
    )
    
    SalvageOptionConfirmButton = FrameInfo(
        WindowName="ConfirmSalvageOptionsButton",
        ParentFrameHash=684387150,
        ChildOffsets=[2]
    )
    
    OptionsSalvageOptionsFrame = FrameInfo(
        WindowName="OptionsSalvageOptionsFrame",
        ParentFrameHash=684387150,
        ChildOffsets=[5]
    )

    SalvageOptionPrefixButton = FrameInfo(
        WindowName="SalvageOptionPrefixButton",
        ParentFrameHash=684387150,
        ChildOffsets=[5, 0]
    )

    SalvageOptionSuffixButton = FrameInfo(
        WindowName="SalvageOptionSuffixButton",
        ParentFrameHash=684387150,
        ChildOffsets=[5, 1]
    )

    SalvageOptionInscriptionButton = FrameInfo(
        WindowName="SalvageOptionInscriptionButton",
        ParentFrameHash=684387150,
        ChildOffsets=[5, 2]
    )

    SalvageOptionMaterialsButton = FrameInfo(
        WindowName="SalvageOptionMaterialsButton",
        ParentFrameHash=684387150,
        ChildOffsets=[5, 3]
    )

    MaterialOptionConfirmationFrame = FrameInfo(
        WindowName="MaterialOptionConfirmationFrame",
        ParentFrameHash=684387150,
        ChildOffsets=[0]
    )

    MaterialOptionConfirmationCancelButton = FrameInfo(
        WindowName="MaterialOptionConfirmationCancelButton",
        ParentFrameHash=684387150,
        ChildOffsets=[0, 4]
    )

    MaterialOptionConfirmationConfirmButton = FrameInfo(
        WindowName="MaterialOptionConfirmationConfirmButton",
        ParentFrameHash=684387150,
        ChildOffsets=[0, 6]
    )

    LesserSalvageFrame = FrameInfo(
        WindowName="LesserSalvageFrame",
        ParentFrameHash=140452905,
        ChildOffsets=[6, 111]
    )

    LesserSalvageCancelButton = FrameInfo(
        WindowName="LesserSalvageCancelButton",
        ParentFrameHash=140452905,
        ChildOffsets=[6, 111, 4]
    )

    LesserSalvageConfirmButton = FrameInfo(
        WindowName="LesserSalvageConfirmButton",
        ParentFrameHash=140452905,
        ChildOffsets=[6, 111, 6]
    )

    ExpertSalvageUnidentifiedFrame = FrameInfo(
        WindowName="ExpertSalvageUnidentifiedFrame",
        ParentFrameHash=140452905,
        ChildOffsets=[6, 112]
    )

    ExpertSalvageUnidentifiedCancelButton = FrameInfo(
        WindowName="ExpertSalvageUnidentifiedCancelButton",
        ParentFrameHash=140452905,
        ChildOffsets=[6, 112, 4]
    )

    ExpertSalvageUnidentifiedConfirmButton = FrameInfo(
        WindowName="ExpertSalvageUnidentifiedConfirmButton",
        ParentFrameHash=140452905,
        ChildOffsets=[6, 112, 6]
    )

    #endregion Salvage
    
    #region Upgrade
    UpgradeWindowFrame = FrameInfo(
        WindowName="UpgradeWindowFrame",
        FrameHash=2612519688
    )

    UpgradeWindowCancelButton = FrameInfo(
        WindowName="UpgradeWindowCancelButton",
        ParentFrameHash=2612519688,
        ChildOffsets=[0]
    )

    UpgradeWindowConfirmButton = FrameInfo(
        WindowName="UpgradeWindowConfirmButton",
        ParentFrameHash=2612519688,
        ChildOffsets=[1]
    )

    #endregion Upgrade
    
    MerchantWindowFrame = FrameInfo(
        WindowName="MerchantWindowFrame",
        FrameHash=3613855137
    )
    
    MerchantWindowCloseButton = FrameInfo(
        WindowName="CrafterWindow Close Button",
        ParentFrameHash=MerchantWindowFrame.FrameHash,
        ChildOffsets=[0, 0, 1]
    )

    CollectorWindowFrame = FrameInfo(
        WindowName="CollectorWindowFrame",
        ParentFrameHash=3613855137,
        ChildOffsets=[0, 0, 6]
    )

    SkillTrainerWindowFrame = FrameInfo(
        WindowName="SkillTrainerWindowFrame",
        ParentFrameHash=1746895597,
        ChildOffsets=[3]
    )

    CrafterWindowFrame = FrameInfo(
        WindowName="CrafterWindowFrame",
        FrameHash=1517397806
    )
    
    


   
WindowFrames["Inventory Bags"] = WindowFrame.InventoryBags
WindowFrames["MiniMap"] = WindowFrame.MiniMapFrame
WindowFrames["PartyWindow"] = WindowFrame.PartyWindowFrame
WindowFrames["CancelEnterMissionButton"] = WindowFrame.CancelEnterMissionButton
WindowFrames["ConfirmEnterMissionButton"] = WindowFrame.ConfirmEnterMissionButton
WindowFrames["DeleteCharacterButton"] = WindowFrame.CharacterDeleteButtonFrame
WindowFrames["FinalDeleteCharacterButton"] = WindowFrame.CharacterFinalDeleteButtonFrame
WindowFrames["CreateCharacterButton1"] = WindowFrame.CreateCharacterButtonFrame1
WindowFrames["CreateCharacterButton2"] = WindowFrame.CreateCharacterButtonFrame2
WindowFrames["CreateCharacterTypeNextButton"] = WindowFrame.CreateCharacterTypeNextButtonFrame
WindowFrames["CreateCharacterNextButtonGeneric"] = WindowFrame.CreateCharacterNextButtonGenericFrame
WindowFrames["FinalCreateCharacterButton"] = WindowFrame.FinalCreateCharacterButtonFrame


#region Callbacks
#autiomatic IO events was deactivated due to instability over long sessions
#use this feature on demand
#UIManager.RegisterFrameIOCallbacks()
    
class InventoryBagWindow:
    @staticmethod
    def _get_bag_offset(bag: Bags) -> int:
        return bag.value - Bags.Backpack.value
    
    @staticmethod
    @frame_cache(category="InventoryBagWindow", source_lib="IsOpen")
    def IsOpen(bag : Bags) -> bool:
        bag_frame = InventoryBagWindow.GetBagFrame(bag)
        return bag_frame.FrameExists() if bag_frame else False
    
    @staticmethod
    @frame_cache(category="InventoryBagWindow", source_lib="GetBagFrame")
    def GetBagFrame(bag : Bags) -> Optional[FrameInfo]:
        if not bag in INVENTORY_WITH_EQUIPMENT_BAGS:
            return None
        
        offset = InventoryBagWindow._get_bag_offset(bag)
        if offset < 0:
            return None
        
        return FrameInfo(
            WindowName=f"{bag.name} Frame",
            ParentFrameHash=WindowFrame.InventoryBackpack.FrameHash,
            ChildOffsets=[offset]
        )
        
    @staticmethod
    @frame_cache(category="InventoryBagWindow", source_lib="GetBagSlotFrames")
    def GetBagSlotFrames(bag : Bags, bag_size: Optional[int] = None) -> list[FrameInfo]:
        if not bag in INVENTORY_WITH_EQUIPMENT_BAGS:
            return []
        
        offset = InventoryBagWindow._get_bag_offset(bag)
        if offset < 0:
            return []
                
        if bag_size is None:
            from PyInventory import Bag
            bag_instance = Bag(bag.value, bag.name)
            bag_size = bag_instance.GetSize()
            
        frames = []
        for slot in range(bag_size):
            frames.append(FrameInfo(
                WindowName=f"{bag.name} Slot {slot}",
                ParentFrameHash=WindowFrame.InventoryBackpack.FrameHash,
                ChildOffsets=[offset, 2 + slot]
            ))
        
        return frames
    
class InventoryBagsWindow:
    @staticmethod
    def _get_bag_offset(bag: Bags) -> int:
        return bag.value - Bags.Backpack.value
    
    @staticmethod
    @frame_cache(category="InventoryBagsWindow", source_lib="IsOpen")
    def IsOpen() -> bool:
        return WindowFrame.InventoryBags.FrameExists()
    
    @staticmethod
    @frame_cache(category="InventoryBagsWindow", source_lib="GetBagFrame")
    def GetBagSlotFrames(bag : Bags, bag_size: Optional[int] = None) -> list[FrameInfo]:
        if not bag in INVENTORY_BAGS:
            return []
                        
        if bag_size is None:
            from PyInventory import Bag
            bag_instance = Bag(bag.value, bag.name)
            bag_size = bag_instance.GetSize()
            
        frames = []
        for slot in range(bag_size):
            frames.append(FrameInfo(
                WindowName=f"{bag.name} Slot {slot}",
                ParentFrameHash=WindowFrame.InventoryBags.FrameHash,
                ChildOffsets=[0, 0, 0, InventoryBagsWindow._get_bag_offset(bag), 2 + slot]
            ))
                
        return frames
    
    @staticmethod
    @frame_cache(category="InventoryBagsWindow", source_lib="GetAllInventorySlotFrames")
    def GetInventorySlotFrames() -> list[FrameInfo]:
        frames = []
        
        for bag in INVENTORY_BAGS:
            frames.extend(InventoryBagsWindow.GetBagSlotFrames(bag))
            
        return frames

class XunlaiStorageWindow:
    from .enums_src.Model_enums import ModelID
    MATERIAL_FRAME_OFFSETS : dict[ModelID, int] = {
        ModelID.Bone: 8,
        ModelID.Iron_Ingot: 1,
        ModelID.Tanned_Hide_Square: 3,
        
        ModelID.Scale: 6,
        ModelID.Chitin_Fragment: 7,
        ModelID.Bolt_Of_Cloth: 2,
        
        ModelID.Wood_Plank: 4,
        ModelID.Granite_Slab: 9,
        ModelID.Pile_Of_Glittering_Dust: 5,
        
        ModelID.Plant_Fiber: 10,
        ModelID.Feather: 11,
        ModelID.Fur_Square: 12,
        
        ModelID.Bolt_Of_Linen: 13,
        ModelID.Bolt_Of_Damask: 14,
        ModelID.Bolt_Of_Silk: 15,  
        
        ModelID.Glob_Of_Ectoplasm: 16,
        ModelID.Steel_Ingot: 17,
        ModelID.Deldrimor_Steel_Ingot: 18,
        
        ModelID.Monstrous_Claw: 19,
        ModelID.Monstrous_Eye: 20,
        ModelID.Monstrous_Fang: 21,
        
        ModelID.Ruby: 23,
        ModelID.Sapphire: 24,
        ModelID.Diamond: 22,
        
        ModelID.Onyx_Gemstone: 36,
        ModelID.Lump_Of_Charcoal: 28,
        ModelID.Obsidian_Shard: 25,
        
        ModelID.Tempered_Glass_Vial: 29,
        ModelID.Leather_Square: 30,
        ModelID.Elonian_Leather_Square: 31,
        
        ModelID.Vial_Of_Ink: 32,
        ModelID.Roll_Of_Parchment: 33,
        ModelID.Roll_Of_Vellum: 34,
        
        ModelID.Spiritwood_Plank: 35,
        ModelID.Amber_Chunk: 26,
        ModelID.Jadeite_Shard: 27,
    }
    
    MAX_TABS = 14
    @staticmethod
    def _get_bag_offset(bag: Bags) -> int:
        if bag == Bags.MaterialStorage:
            return XunlaiStorageWindow.MAX_TABS
        
        return bag.value - Bags.Storage1.value
    
    @staticmethod
    @frame_cache(category="XunlaiStorageWindow", source_lib="IsOpen")
    def IsOpen() -> bool:
        return WindowFrame.Xunlai_Window.FrameExists()
        
    @staticmethod
    @frame_cache(category="XunlaiStorageWindow", source_lib="GetTabContentFrame")
    def GetTabFrame(bag: Bags) -> Optional[FrameInfo]:
        if not bag in STORAGE_BAGS and bag != Bags.MaterialStorage:
            return None
        
        def get_offset_for_bag(bag: Bags) -> int:
            base_offset = WindowFrame.Xunlai_Tab1.ChildOffsets[1]
            return base_offset - XunlaiStorageWindow._get_bag_offset(bag)             
        
        return FrameInfo(
            WindowName=f"{bag.name} Tab",
            ParentFrameHash=WindowFrame.Xunlai_Window.FrameHash,
            ChildOffsets=[0, get_offset_for_bag(bag)]
        )
        
    @staticmethod
    @frame_cache(category="XunlaiStorageWindow", source_lib="GetTabContentFrame")
    def GetTabContentFrame(bag: Bags) -> Optional[FrameInfo]:
        if not bag in STORAGE_BAGS and bag != Bags.MaterialStorage:
            return None
        
        def get_offset_for_bag(bag: Bags) -> int:
            base_offset = WindowFrame.Xunlai_Tab1_Content.ChildOffsets[1]            
            return base_offset + XunlaiStorageWindow._get_bag_offset(bag)             
        
        return FrameInfo(
            WindowName=f"{bag.name} Tab Content",
            ParentFrameHash=WindowFrame.Xunlai_Window.FrameHash,
            ChildOffsets=[0, get_offset_for_bag(bag)]
        )
    
    @staticmethod
    @frame_cache(category="XunlaiStorageWindow", source_lib="GetActiveTabFrame")
    def GetActiveTabFrame() -> Optional[FrameInfo]:
        for bag in STORAGE_BAGS:
            tab_frame = XunlaiStorageWindow.GetTabContentFrame(bag)
            if tab_frame and tab_frame.FrameExists():
                return tab_frame
        
        material_tab_frame = XunlaiStorageWindow.GetTabContentFrame(Bags.MaterialStorage)
        if material_tab_frame and material_tab_frame.FrameExists():
            return material_tab_frame
        
        return None
    
    @staticmethod
    @frame_cache(category="XunlaiStorageWindow", source_lib="GetActiveTabBag")
    def GetActiveTabBag() -> Optional[Bags]:
        for bag in [*STORAGE_BAGS, Bags.MaterialStorage]:
            tab_frame = XunlaiStorageWindow.GetTabContentFrame(bag)
            if tab_frame and tab_frame.FrameExists():
                return bag
        
        return None
    
    @staticmethod
    @frame_cache(category="XunlaiStorageWindow", source_lib="GetActiveTabSlotFrames")
    def GetActiveTabSlotFrames() -> list[FrameInfo]:
        active_tab = XunlaiStorageWindow.GetActiveTabBag()
        if not active_tab:
            return []
        
        if active_tab == Bags.MaterialStorage:
            return XunlaiStorageWindow.GetMaterialSlotFrames()
        
        return XunlaiStorageWindow.GetTabSlotFrames(active_tab)
    
    @staticmethod
    @frame_cache(category="XunlaiStorageWindow", source_lib="GetTabSlotFrames")
    def GetTabSlotFrames(bag : Bags, bag_size: Optional[int] = 25) -> list[FrameInfo]:
        if not bag in STORAGE_BAGS:
            return []
                
        if bag_size is None:
            from PyInventory import Bag
            bag_instance = Bag(bag.value, bag.name)
            bag_size = bag_instance.GetSize()
        
        frames = []
        for slot in range(bag_size):
            frames.append(FrameInfo(
                WindowName=f"{bag.name} Slot {slot}",
                ParentFrameHash=WindowFrame.Xunlai_Window.FrameHash,
                ChildOffsets=[0, XunlaiStorageWindow._get_bag_offset(bag), 2 + slot]
            ))
                
        return frames
    
    @staticmethod
    def GetMaterialFrame(material: ModelID) -> Optional[FrameInfo]:
        slot = XunlaiStorageWindow.MATERIAL_FRAME_OFFSETS.get(material)
        if slot is None:
            return None
        
        return FrameInfo(
            WindowName=f"Xunlai Window.Tab Material Storage.{material.name} Slot",
            ParentFrameHash=WindowFrame.Xunlai_Window.FrameHash,
            ChildOffsets=[0, XunlaiStorageWindow.MAX_TABS, 2 + slot]
        )

    @staticmethod
    @frame_cache(category="XunlaiStorageWindow", source_lib="GetMaterialSlotFrames")
    def GetMaterialSlotFrames() -> list[FrameInfo]:       
        
        frames = []
        for material, slot in XunlaiStorageWindow.MATERIAL_FRAME_OFFSETS.items():
            frames.append(FrameInfo(
                WindowName=f"Xunlai Window.Tab Material Storage.{material.name}",
                ParentFrameHash=WindowFrame.Xunlai_Window.FrameHash,
                ChildOffsets=[0, XunlaiStorageWindow.MAX_TABS, slot]
            ))
                
        return frames
    
    @staticmethod
    @frame_cache(category="XunlaiStorageWindow", source_lib="GetAllStorageSlotFrames")
    def GetStorageSlotFrames() -> list[FrameInfo]:
        frames = []
        
        for bag in STORAGE_BAGS:
            frames.extend(XunlaiStorageWindow.GetTabSlotFrames(bag))
            
        frames.extend(XunlaiStorageWindow.GetMaterialSlotFrames())
        return frames

    @staticmethod
    def ClickDepositAllMaterials() -> bool:
        if not XunlaiStorageWindow.IsOpen():
            return False
        
        frame = WindowFrame.Xunlai_DepositAllMaterialsButton
        if not frame.FrameExists():
            return False
                
        frame.FrameClick(current_state=7)
        return True

class SkillTrainerWindow:
    @staticmethod
    @frame_cache(category="SkillTrainerWindow", source_lib="IsOpen")
    def IsOpen() -> bool:
        return WindowFrame.SkillTrainerWindowFrame.FrameExists()

    @staticmethod
    def Close() -> bool:
        if not SkillTrainerWindow.IsOpen():
            return False
        
        frame = WindowFrame.MerchantWindowCloseButton  
        if not frame.FrameExists():
            return False
              
        frame.FrameClick()
        return True

class MerchantWindow:
    @staticmethod
    @frame_cache(category="MerchantWindow", source_lib="IsOpen")
    def IsOpen() -> bool:
        return WindowFrame.MerchantWindowFrame.FrameExists()
    
    @staticmethod
    def Close() -> bool:
        if not MerchantWindow.IsOpen():
            return False
        
        frame = WindowFrame.MerchantWindowCloseButton
        if not frame.FrameExists():
            return False
                
        frame.FrameClick()
        return True
    
class CollectorWindow:
    @staticmethod
    @frame_cache(category="CollectorWindow", source_lib="IsOpen")
    def IsOpen() -> bool:
        return WindowFrame.CollectorWindowFrame.FrameExists()
    
    @staticmethod
    def Close() -> bool:
        if not CollectorWindow.IsOpen():
            return False
        
        frame = WindowFrame.MerchantWindowCloseButton
        if not frame.FrameExists():
            return False
                
        frame.FrameClick()
        return True
    
class CrafterWindow:
    @staticmethod
    @frame_cache(category="CrafterWindow", source_lib="IsOpen")
    def IsOpen() -> bool:
        return WindowFrame.CrafterWindowFrame.FrameExists()

    @staticmethod
    def Close() -> bool:
        if not CrafterWindow.IsOpen():
            return False
        
        frame = WindowFrame.MerchantWindowCloseButton
        if not frame.FrameExists():
            return False
                
        frame.FrameClick()
        return True

class UpgradeWindow:
    '''
    Utility class to check for and interact with the Upgrade Window that appears when using an upgrade extract on items with multiple upgrade options.
    '''
    
    @staticmethod
    @frame_cache(category="UpgradeWindow", source_lib="IsOpen")
    def IsOpen() -> bool:
        '''Return True if the Upgrade Window is open.'''
        return WindowFrame.UpgradeWindowFrame.FrameExists()
    
    @staticmethod
    def Cancel() -> bool:
        '''Cancel the Upgrade Window by clicking the relevant button. Returns True if the button was found and clicked, False otherwise.'''
        if not UpgradeWindow.IsOpen():
            return False
        
        frame = WindowFrame.UpgradeWindowCancelButton
        frame.FrameClick()
        return True
    
    @staticmethod
    def Confirm() -> bool:
        '''Confirm the currently selected Upgrade Option by clicking the relevant button. Returns True if the button was found and clicked, False otherwise.'''
        if not UpgradeWindow.IsOpen():
            return False
        
        frame = WindowFrame.UpgradeWindowConfirmButton
        frame.FrameClick()
        return True

class SalvageOptionsWindow:
    '''
    Utility class to check for and interact with the Salvage Options Window that appears when using an expert salvage kit on items with multiple salvage options.
    '''    
    @staticmethod
    @frame_cache(category="SalvageOptionsWindow", source_lib="IsOpen")
    def IsOpen() -> bool:
        '''Return True if the Salvage Options Window is open.'''
        
        return WindowFrame.SalvageOptionsFrame.FrameExists()
    
    @staticmethod
    def Cancel() -> bool:
        '''Cancel the Salvage Options Window by clicking the relevant button. Returns True if the button was found and clicked, False otherwise.'''
        if not SalvageOptionsWindow.IsOpen():
            return False

        frame = WindowFrame.SalvageOptionCancelButton
        frame.FrameClick()
        return True
    
    @staticmethod
    def Confirm() -> bool:
        '''Confirm the currently selected Salvage Option by clicking the relevant button. Returns True if the button was found and clicked, False otherwise.'''
        if not SalvageOptionsWindow.IsOpen():
            return False

        frame = WindowFrame.SalvageOptionConfirmButton
        frame.FrameClick()
        return True
    
    @staticmethod
    def GetSalvageOptionFrame(mode: SalvageMode) -> Optional[FrameInfo]:
        '''Return the frame corresponding to the given salvage mode.'''
        if not SalvageOptionsWindow.IsOpen():
            return None
        
        match mode:
            case SalvageMode.Prefix:
                return WindowFrame.SalvageOptionPrefixButton
            
            case SalvageMode.Suffix:
                return WindowFrame.SalvageOptionSuffixButton
            
            case SalvageMode.Inscription:
                return WindowFrame.SalvageOptionInscriptionButton
            
            case SalvageMode.RareCraftingMaterials | SalvageMode.LesserCraftingMaterials:
                return WindowFrame.SalvageOptionMaterialsButton
            
            case _:
                return None
    
    @staticmethod
    @frame_cache(category="SalvageOptionsWindow", source_lib="IsOptionVisible")
    def IsOptionVisible(mode: SalvageMode) -> bool:
        '''Return True if the given salvage option is visible.'''
        option_frame = SalvageOptionsWindow.GetSalvageOptionFrame(mode)
        if option_frame is None:
            return False
        
        return option_frame.FrameExists()
    
    @staticmethod
    def SelectOption(mode: SalvageMode) -> bool:
        '''Select the given salvage option by clicking the relevant button. Returns True if the button was found and clicked, False otherwise.'''
        if not SalvageOptionsWindow.IsOptionVisible(mode):
            return False
        
        option_frame = SalvageOptionsWindow.GetSalvageOptionFrame(mode)
        if option_frame is None:
            return False
        
        option_frame.FrameClick(current_state=8)
        return True
    
    @staticmethod
    def SelectAndConfirmOption(mode: SalvageMode) -> bool:
        '''Select and confirm the given salvage option by clicking the relevant buttons. Returns True if the buttons were found and clicked, False otherwise.'''
        if not SalvageOptionsWindow.SelectOption(mode):
            return False
        
        if not SalvageOptionsWindow.Confirm():
            return False
        
        return True

class SalvageConfirmationPopup:
    '''
    Utility class to check for and interact with the confirmation pop up for salvaging with a salvage kit.
    '''
    
    @staticmethod
    @frame_cache(category="SalvageConfirmationPopup", source_lib="IsOpen")
    def IsOpen() -> bool:
        '''
        Return True if the confirmation pop up for salvaging with a salvage kit is open.
        '''
        return WindowFrame.MaterialOptionConfirmationFrame.FrameExists()
    
    @staticmethod
    def Cancel() -> bool:
        '''
        Cancel the confirmation pop up for salvaging with a salvage kit by clicking the relevant button. Returns True if the button was found and clicked, False otherwise.
        '''
        if not SalvageConfirmationPopup.IsOpen():
            return False
        
        frame = WindowFrame.MaterialOptionConfirmationCancelButton
        frame.FrameClick()
        return True
    
    @staticmethod
    def Confirm() -> bool:
        '''
        Confirm the confirmation pop up for salvaging with a salvage kit by clicking the relevant button. Returns True if the button was found and clicked, False otherwise.
        '''
        if not SalvageConfirmationPopup.IsOpen():
            return False
        
        frame = WindowFrame.MaterialOptionConfirmationConfirmButton
        frame.FrameClick()
        return True

class LesserSalvageWindow:
    '''
    Utility class to check for and interact with the confirmation pop up for salvaging with a normal salvage kit.
    '''
    @staticmethod
    @frame_cache(category="LesserSalvageWindow", source_lib="IsOpen")
    def IsOpen() -> bool:
        '''
        Return True if the confirmation pop up for salvaging with a normal salvage kit is open.
        '''
        return WindowFrame.LesserSalvageFrame.FrameExists()
    
    @staticmethod
    def Cancel() -> bool:
        '''
        Cancel the confirmation pop up for salvaging with a normal salvage kit by clicking the relevant button. Returns True if the button was found and clicked, False otherwise.
        '''
        if not LesserSalvageWindow.IsOpen():
            return False
        
        frame = WindowFrame.LesserSalvageCancelButton
        frame.FrameClick()
        return True
    
    @staticmethod
    def Confirm() -> bool:
        '''
        Confirm the confirmation pop up for salvaging with a normal salvage kit by clicking the relevant button. Returns True if the button was found and clicked, False otherwise.
        '''
        if not LesserSalvageWindow.IsOpen():
            return False
        
        frame = WindowFrame.LesserSalvageConfirmButton
        frame.FrameClick()
        return True

class ExpertSalvageUnidentifiedWindow:
    '''
    Utility class to check for and interact with the Salvage Window from using Expert Salvage Kits on Unidentified Items.
    '''
    
    @staticmethod
    @frame_cache(category="ExpertSalvageUnidentifiedWindow", source_lib="IsOpen")
    def IsOpen() -> bool:
        '''
        Return True if the Expert Salvage Unidentified Window is open.
        '''
                
        return WindowFrame.ExpertSalvageUnidentifiedFrame.FrameExists()
    
    @staticmethod
    def Cancel() -> bool:
        '''
        Cancel the Expert Salvage Unidentified Window by clicking the relevant button. Returns True if the button was found and clicked, False otherwise.
        '''
        if not ExpertSalvageUnidentifiedWindow.IsOpen():
            return False
        
        frame = WindowFrame.ExpertSalvageUnidentifiedCancelButton
        frame.FrameClick()
        return True
    
    @staticmethod
    def Confirm() -> bool:
        '''
        Confirm the Expert Salvage Unidentified Window by clicking the relevant button. Returns True if the button was found and clicked, False otherwise.
        '''        
        if not ExpertSalvageUnidentifiedWindow.IsOpen():
            return False
        
        frame = WindowFrame.ExpertSalvageUnidentifiedConfirmButton
        frame.FrameClick()
        return True

class AnySalvageWindow:
    '''
    Utility class to check for and interact with any salvage-related window, including SalvageOptionsWindow, SalvageConfirmationPopup, LesserSalvageWindow, and ExpertSalvageUnidentifiedWindow.
    '''
    
    @staticmethod
    @frame_cache(category="AnySalvageWindow", source_lib="AnySalvageWindowOpen")
    def IsOpen() -> bool:
        '''
        Return True if any salvage-related window is open, including SalvageOptionsWindow, SalvageConfirmationPopup, LesserSalvageWindow, or ExpertSalvageUnidentifiedWindow.
        '''
        
        return (
            SalvageConfirmationPopup.IsOpen()
            or SalvageOptionsWindow.IsOpen()
            or LesserSalvageWindow.IsOpen()
            or ExpertSalvageUnidentifiedWindow.IsOpen()
        )

    @staticmethod
    def Cancel() -> bool:
        '''
        Cancel any open salvage-related window, including SalvageOptionsWindow, SalvageConfirmationPopup, LesserSalvageWindow, or ExpertSalvageUnidentifiedWindow. Returns True if a salvage-related window was found and cancelled, False otherwise.
        '''
        
        if SalvageOptionsWindow.IsOpen():
            return SalvageOptionsWindow.Cancel()

        if LesserSalvageWindow.IsOpen():
            return LesserSalvageWindow.Cancel()

        if ExpertSalvageUnidentifiedWindow.IsOpen():
            return ExpertSalvageUnidentifiedWindow.Cancel()

        if SalvageConfirmationPopup.IsOpen():
            return SalvageConfirmationPopup.Cancel()

        return False


    @staticmethod
    def Confirm() -> bool:
        '''
        WARNING: This will irreversibly confirm salvage actions. Use the more specific Confirm methods if possible to avoid unintended consequences.\n
        Confirm any open salvage-related window, including SalvageOptionsWindow, SalvageConfirmationPopup, LesserSalvageWindow, or ExpertSalvageUnidentifiedWindow.
        Returns True if a salvage-related window was found and confirmed, False otherwise.
        '''
        if SalvageConfirmationPopup.IsOpen():
            return SalvageConfirmationPopup.Confirm()

        if SalvageOptionsWindow.IsOpen():
            return SalvageOptionsWindow.Confirm()

        if LesserSalvageWindow.IsOpen():
            return LesserSalvageWindow.Confirm()

        if ExpertSalvageUnidentifiedWindow.IsOpen():
            return ExpertSalvageUnidentifiedWindow.Confirm()

        return False