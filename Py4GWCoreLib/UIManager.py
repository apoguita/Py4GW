import ctypes
import PyUIManager
from typing import Dict, List, Tuple, Optional
import json
import PyOverlay



#region FrameID_Rutines

#endregion


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
    def GetRootFrameID():
        """
        Get the root frame ID.

        :return: int: The root frame ID.
        """
        return PyUIManager.UIManager.get_root_frame_id()
    
    @staticmethod
    def GetChildFrameID (parent_hash: int, child_offsets: List[int]) -> int:
        """
        Get the child frame ID.

        :param parent_hash: The parent hash value.
        :param child_offsets: The list of child offsets.
        :return: int: The child frame ID.
        """
        return PyUIManager.UIManager.get_child_frame_id(parent_hash, child_offsets)
    
    @staticmethod
    def IsWorldMapShowing():
        """
        Check if the world map is showing.

        :return: bool: True if the world map is showing, False otherwise.
        """
        return PyUIManager.UIManager.is_world_map_showing()
    
    @staticmethod
    def SetPreference(preference, value):
        """
        Set a preference value.

        :param preference: The preference to set.
        :param value: The value to set.
        """
        PyUIManager.UIManager.set_preference(preference, value)
        
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


    