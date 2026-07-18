import PyImGui
import PyUIManager

MODULE_NAME = "Frame Viewer (Basic)"

frame_ids = []
selected_frame_id = 0
auto_refresh = True
max_rows = 50
status_text = "Ready"


def refresh_frames():
    global frame_ids, selected_frame_id, status_text
    try:
        frame_ids = list(PyUIManager.UIManager.get_frame_array())
        frame_ids.sort()
        if selected_frame_id not in frame_ids:
            selected_frame_id = frame_ids[0] if frame_ids else 0
        status_text = f"Loaded {len(frame_ids)} frames"
    except Exception as exc:
        status_text = f"Refresh error: {exc}"


def get_selected_frame():
    if not selected_frame_id:
        return None
    try:
        return PyUIManager.UIFrame(selected_frame_id)
    except Exception:
        return None


def draw_frame_list():
    global selected_frame_id

    PyImGui.text(f"Showing first {min(len(frame_ids), max_rows)} frame IDs")
    PyImGui.separator()

    for fid in frame_ids[:max_rows]:
        is_selected = (fid == selected_frame_id)
        label = f"[*] {fid}" if is_selected else f"[ ] {fid}"
        if PyImGui.button(f"Select##{fid}"):
            selected_frame_id = fid
        PyImGui.same_line(0, -1)
        PyImGui.text(label)


def draw_selected_frame_info():
    frame = get_selected_frame()
    PyImGui.separator()
    PyImGui.text("Selected Frame")

    if frame is None:
        PyImGui.text("No valid frame selected")
        return

    PyImGui.text(f"frame_id: {int(getattr(frame, 'frame_id', 0) or 0)}")
    PyImGui.text(f"parent_id: {int(getattr(frame, 'parent_id', 0) or 0)}")
    PyImGui.text(f"child_offset_id: {int(getattr(frame, 'child_offset_id', 0) or 0)}")
    PyImGui.text(f"frame_hash: {int(getattr(frame, 'frame_hash', 0) or 0)}")
    PyImGui.text(f"is_created: {bool(getattr(frame, 'is_created', False))}")
    PyImGui.text(f"is_visible: {bool(getattr(frame, 'is_visible', False))}")


# Minimal starting point: refresh + select + inspect one frame.
def main():
    global auto_refresh, max_rows

    if auto_refresh and not frame_ids:
        refresh_frames()

    if PyImGui.begin(MODULE_NAME):
        if PyImGui.button("Refresh"):
            refresh_frames()
        PyImGui.same_line(0, -1)
        auto_refresh = PyImGui.checkbox("Auto refresh on empty", auto_refresh)

        PyImGui.text(status_text)
        max_rows = PyImGui.input_int("Max rows", max_rows)
        if max_rows < 1:
            max_rows = 1

        draw_frame_list()
        draw_selected_frame_info()

    PyImGui.end()


if __name__ == "__main__":
    main()
