
import PyUIManager
from typing import Dict, List, Tuple, Optional
import json
import PyOverlay
from collections import deque, defaultdict
from .Py4GWcorelib import ConsoleLog, Console

# —— Constants ——————————————————
NPC_DIALOG_HASH    = 3856160816
DEFAULT_OFFSET     = [2, 0, 0, 1]
DIALOG_CHILD_OFFSET = list(DEFAULT_OFFSET)

# —— Globals —————————————————
_overlay = PyOverlay.Overlay()

class UIManager:  
    global overlay
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
    def FrameClick(frame_id):
        """
        Click a frame on the UI.

        :param frame_id: The ID of the frame.
        """
        if not UIManager.FrameExists(frame_id):
            return
        PyUIManager.UIManager.button_click(frame_id)
    
    @staticmethod
    def TestMouseAction(frame_id, current_state, wparam_value, lparam_value=0):
        """
        Test mouse action on a frame.

        :param frame_id: The ID of the frame.
        :param current_state: The current state of the mouse.
        :param wparam_value: The wparam value.
        """
        if not UIManager.FrameExists(frame_id):
            return
        PyUIManager.UIManager.test_mouse_action(frame_id, current_state, wparam_value, lparam_value)
    
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
        from .Py4GWcorelib import Utils
        option_offsets = child_offsets
        all_ids = UIManager.GetAllChildFrameIDs(parent_hash, option_offsets)
        
        sorted_frames = UIManager.SortFramesByVerticalPosition(all_ids)

        if debug:
            print(f"All matching frame IDs: {all_ids}")
            for fid, top_y in sorted_frames:
                print(f"Frame ID: {fid}, Top Y: {top_y}")
            
        colors = [
        Utils.RGBToColor(0, 255, 0, 200),     # green
        Utils.RGBToColor(255, 0, 0, 200),     # red
        Utils.RGBToColor(0, 128, 255, 200),   # blue
        Utils.RGBToColor(255, 255, 0, 200),   # yellow
        Utils.RGBToColor(128, 0, 255, 200),   # purple
        Utils.RGBToColor(255, 128, 0, 200),   # orange
        Utils.RGBToColor(0, 255, 255, 200),   # cyan
        ]
        for i, (frame_id, _) in enumerate(sorted_frames):
            if i >= len(colors):
                break
            UIManager().DrawFrame(frame_id, colors[i])
            
    @staticmethod
    def IsWorldMapShowing():
        """
        Check if the world map is showing.

        :return: bool: True if the world map is showing, False otherwise.
        """
        return PyUIManager.UIManager.is_world_map_showing()
    
    @staticmethod
    def IsShiftScreebshot():
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
    def GetFrameCoords(frame_id):
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
    
        
    def DrawFrame(self,frame_id, draw_color):
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
        _overlay.BeginDraw()
        _overlay.DrawQuadFilled(p1,p2,p3,p4, draw_color)
        _overlay.EndDraw()
    
        
    def DrawFrameOutline(self,frame_id, draw_color):
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
        _overlay.BeginDraw()
        _overlay.DrawQuad(p1,p2,p3,p4, draw_color)
        _overlay.EndDraw()

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
            ConsoleLog("DialogHelper", f"BFS IDs → {sorted_ids}", Console.MessageType.Info)
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
                f"Clicking dialog choice #{choice} → frame {target}",
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