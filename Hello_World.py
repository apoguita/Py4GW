from Py4GWCoreLib import *
import re
import sys

MODULE_NAME = "Frame Tester"

from collections import defaultdict

def build_frame_tree(frame_hierarchy):
    """Builds a tree where each parent_frame_id maps to a list of (frame_id, frame_hash) pairs."""
    frame_tree = defaultdict(list)

    for parent_hash, frame_hash, parent_frame_id, frame_id in frame_hierarchy:
        frame_tree[parent_frame_id].append({"frame_id": frame_id, "frame_hash": frame_hash})  

    return frame_tree

def render_frame_tree(parent_frame_id=0, depth=0):
    """ Recursively renders the frame hierarchy using PyImGui. """
    if parent_frame_id not in frame_tree:
        return

    if PyImGui.tree_node(f"Frame {parent_frame_id}##{parent_frame_id}"):
        for child in frame_tree[parent_frame_id]:
            frame_id = child["frame_id"]
            frame_hash = child["frame_hash"]
            if PyImGui.tree_node(f"Frame {frame_id} (Hash: {frame_hash})##{frame_id}"):
                render_frame_tree(frame_id, depth + 1)  # Recursively render children
                PyImGui.tree_pop()  # Close the child node
        PyImGui.tree_pop()  # Close the parent node



frame_hash = 0
frame_id_by_hash = 0
frame_id_by_label = 0
frame_coords: list[tuple[int, int]] = []
frame_hierarchy: list[tuple[int, int, int, int]] = []
frame_tree = {}
frame = None

overlay = Overlay()

def DrawWindow():
    global frame_hash, frame_id_by_hash, frame_id_by_label, frame_coords, overlay, frame_hierarchy, frame_tree
    global frame
    try:
        if PyImGui.begin("Frame Tester"):
            
            if PyImGui.button("populate hash from 'skillbar' frame"):
                frame_hash = UIManager.GetHashByLabel("skillbar")
                frame_id_by_label = UIManager.GetFrameIDByLabel("skillbar")
                frame = PyUIManager.UIFrame(frame_id_by_label)
                frame_coords = UIManager.GetFrameCoordsByHash(frame_hash)
                            
            PyImGui.text(f"frame hash: {frame_hash}")
            PyImGui.text(f"frame id by label: {frame_id_by_label}")
            
            PyImGui.separator()
            
            PyImGui.text("Frame Data:")
            if frame:
                PyImGui.text(f"frame_id: {frame.frame_id}")
                PyImGui.text(f"parent_id: {frame.parent_id}")
                PyImGui.text(f"frame_hash: {frame.frame_hash}")
                PyImGui.text(f"visibility_flags: {frame.visibility_flags}")
                PyImGui.text(f"type: {frame.type}")
                PyImGui.text(f"template_type: {frame.template_type}")
                PyImGui.text(f"position: [{frame.position.top_on_screen}, {frame.position.left_on_screen}, {frame.position.bottom_on_screen}, {frame.position.right_on_screen}]")
                PyImGui.text(f"frame coords: {frame_coords}")
                PyImGui.text(f"frame_callbacks: ")
                for i, callback in enumerate(frame.frame_callbacks):
                    PyImGui.text(f"Callback {i}: {callback.get_address()}")
                PyImGui.text(f"frame_layout: {frame.frame_layout}")

            if PyImGui.button("Populate Frame Hierarchy"):
                frame_hierarchy = UIManager.GetFrameHierarchy()  # Fetch hierarchy
                frame_tree = build_frame_tree(frame_hierarchy)  # Construct hierarchy
                
            if frame_tree:
                render_frame_tree()

            
                
            """
                
            if PyImGui.button("populate frame id by hash"):
                frame_id_by_hash = UI.GetFrameIDByHash(frame_hash)
                
            if PyImGui.button("populate frame id by label"):
                frame_id_by_label = UI.GetFrameIDByLabel("skillbar")
                
            if PyImGui.button("populate frame coords"):
                frame_coords = UI.GetFrameCoordsByHash(frame_hash)
                
            PyImGui.text(f"frame hash: {frame_hash}")
            PyImGui.text(f"frame id by hash: {frame_id_by_hash}")
            PyImGui.text(f"frame id by label: {frame_id_by_label}")
            PyImGui.text(f"frame coords: {frame_coords}")
            PyImGui.text(f"mouse coords: {overlay.GetMouseCoords()}")
            
            if frame_coords:
                top_left = frame_coords[0]
                bottom_right = frame_coords[1]
                top = top_left[0]
                left = top_left[1]
                bottom = bottom_right[0]
                right = bottom_right[1]
                                
                overlay.BeginDraw()
                overlay.DrawQuad(top, left, top,right, bottom, right, bottom, left, Utils.RGBToColor(0, 255, 0, 255), 5)
                overlay.EndDraw()
            
            """
        PyImGui.end()

    except Exception as e:
        Py4GW.Console.Log("tester", f"Unexpected Error: {str(e)}", Py4GW.Console.MessageType.Error)






def main():
    DrawWindow()


if __name__ == "__main__":
    main()
