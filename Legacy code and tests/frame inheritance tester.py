from Py4GWCoreLib import UIManager, FrameInfo
import PyImGui
import PyOverlay
import PyUIManager

CancelEnterMissionButton = FrameInfo(
    WindowName="CancelEnterMissionButton",
    ParentFrameHash=2209443298,
    ChildOffsets=[0,1,1]
)

orig_frames = []                 # [frame_id]
post_frames = []                 # [frame_id]
new_frames_with_coords = []      # [(frame_id, (l,t,r,b))]
visible_flags = []               # [(frame_id, bool)]
frame_data_cache:list[PyUIManager.UIFrame] = []         # [(frame_id, UIFrame)]
parent_frame_data_cache:list[PyUIManager.UIFrame] = []  # [(parent_frame_id, UIFrame)]
grandparent_frame_data_cache:list[PyUIManager.UIFrame] = []  # [(grandparent_frame_id, UIFrame)]

_overlay = PyOverlay.Overlay()

def DrawFrameCached(left: float,
                    top: float,
                    right: float,
                    bottom: float,
                    draw_color: int,
                    batch: bool = False):

    p1 = PyOverlay.Point2D(int(left),  int(top))
    p2 = PyOverlay.Point2D(int(right), int(top))
    p3 = PyOverlay.Point2D(int(right), int(bottom))
    p4 = PyOverlay.Point2D(int(left),  int(bottom))

    if not batch:
        _overlay.BeginDraw()

    _overlay.DrawQuadFilled(p1, p2, p3, p4, draw_color)

    if not batch:
        _overlay.EndDraw()


def draw_window():
    global orig_frames, post_frames, new_frames_with_coords, visible_flags, frame_data_cache
    global parent_frame_data_cache, grandparent_frame_data_cache
    global CancelEnterMissionButton

    if PyImGui.begin("Address tester"):
        if CancelEnterMissionButton.FrameExists():
            PyImGui.text("Entering mission")
            CancelEnterMissionButton.DrawFrameOutline(0xFF0000FF)
            if PyImGui.button("Cancel Enter Mission"):
                CancelEnterMissionButton.FrameClick()
        else:
            PyImGui.text("Idle")

        # ---- SNAPSHOT 1 ----
        if PyImGui.button("Get Frame_tree"):
            frame_tree = UIManager.GetFrameArray()
            orig_frames = [fid for fid in frame_tree if UIManager.FrameExists(fid)]
            post_frames = []
            new_frames_with_coords = []
            visible_flags = []
            frame_data_cache = []
            parent_frame_data_cache = []
            grandparent_frame_data_cache = []

        # ---- SNAPSHOT 2 ----
        if PyImGui.button("Get post sample Frame_tree"):
            frame_tree = UIManager.GetFrameArray()
            post_frames = [fid for fid in frame_tree if UIManager.FrameExists(fid)]

            for fid in post_frames:
                if fid not in orig_frames:
                    coords = UIManager.GetFrameCoords(fid)
                    new_frames_with_coords.append((fid, coords))
                    visible_flags.append(True) 
                    frame = PyUIManager.UIFrame(fid)
                    frame_data_cache.append(frame)
                    parent = PyUIManager.UIFrame(frame.parent_id)
                    parent_frame_data_cache.append(parent)
                    grandparent = PyUIManager.UIFrame(parent.parent_id)
                    grandparent_frame_data_cache.append(grandparent)
                    print(f"New Frame ID: {fid}, Coords: {coords}")

        PyImGui.separator()

        # ---- DRAW CACHED FRAMES ----
        for i, (frame_id, (l, t, r, b)) in enumerate(new_frames_with_coords):
            # checkbox toggles current stored state
            visible_flags[i] = PyImGui.checkbox(f"Frame ID: {frame_id}", visible_flags[i])
            if not visible_flags[i]:
                continue
            PyImGui.text("frame_id: " + str(frame_data_cache[i].frame_id))
            PyImGui.text("parent_id: " + str(frame_data_cache[i].parent_id))
            PyImGui.text("frame_hash: " + str(frame_data_cache[i].frame_hash))
            PyImGui.text("child_offset_id: " + str(frame_data_cache[i].child_offset_id))
            PyImGui.separator()
            if PyImGui.collapsing_header("Parent Frame Data##" + str(frame_data_cache[i].parent_id)):
                PyImGui.text("parent frame_id: " + str(parent_frame_data_cache[i].frame_id))
                PyImGui.text("parent parent_id: " + str(parent_frame_data_cache[i].parent_id))
                PyImGui.text("parent frame_hash: " + str(parent_frame_data_cache[i].frame_hash))
                PyImGui.text("parent child_offset_id: " + str(parent_frame_data_cache[i].child_offset_id))
                PyImGui.separator()
            if PyImGui.collapsing_header("Grandparent Frame Data##" + str(parent_frame_data_cache[i].parent_id)):
                PyImGui.text("grandparent frame_id: " + str(grandparent_frame_data_cache[i].frame_id))
                PyImGui.text("grandparent parent_id: " + str(grandparent_frame_data_cache[i].parent_id))
                PyImGui.text("grandparent frame_hash: " + str(grandparent_frame_data_cache[i].frame_hash))
                PyImGui.text("grandparent child_offset_id: " + str(grandparent_frame_data_cache[i].child_offset_id))
                PyImGui.separator()
            
            

        # draw only those enabled
        if any(visible_flags):
            _overlay.BeginDraw()
            for i, (frame_id, (l, t, r, b)) in enumerate(new_frames_with_coords):
                if visible_flags[i]:
                    DrawFrameCached(l, t, r, b, 0x80FF00FF, batch=True)
            _overlay.EndDraw()

    PyImGui.end()

def main():
    draw_window()

if __name__ == "__main__":
    main()
