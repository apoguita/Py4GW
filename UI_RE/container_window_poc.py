import Py4GW
import PyImGui
import PyUIManager

from Py4GWCoreLib import GWContext, UIManager
from Py4GWCoreLib.GWUI import GWUI
from Py4GWCoreLib.Scanner import Scanner, ScannerSection


MODULE_NAME = "Titled ContainerWindow POC"
SCRIPT_REVISION = "2026-05-31-diagnose-scanner"
WINDOW_OPEN = True
INITIALIZED = False

FRAME_LABEL = "Py4GW"
TARGET_X = 200.0
TARGET_Y = 200.0
TARGET_WIDTH = 400.0
TARGET_HEIGHT = 300.0
# NOTE: 0x20 enables frame-level title bar — may interact with SUBCLASS_FLAGS title bar (bit 0x01)
TARGET_FRAME_FLAGS = 0x20
SUBCLASS_FLAGS = 0x59  # 0x01 title + 0x08/0x10 resize + 0x40 chrome
ANCHOR_FLAGS = 0x6
LAST_PROC_ADDR = 0
LAST_FRAME_ID = 0
LAST_STATUS = "idle"


def _log(message: str) -> None:
    print(f"[{MODULE_NAME}] {message}")


def _viewport_height() -> float:
    root_frame_id = int(UIManager.GetRootFrameID() or 0)
    _, viewport_height = UIManager.GetViewportDimensions(root_frame_id)
    return float(viewport_height)


def _engine_y_from_top(y_from_top: float, height: float) -> float:
    return _viewport_height() - float(y_from_top) - float(height)


def _frame_exists(frame_id: int) -> bool:
    if frame_id <= 0:
        return False
    try:
        return int(frame_id) in set(int(fid) for fid in UIManager.GetFrameArray())
    except Exception:
        return False


def _frame_summary(frame_id: int) -> str:
    frame_id = int(frame_id or 0)
    if frame_id <= 0:
        return "frame_id=0"
    try:
        frame = UIManager.GetFrameByID(frame_id)
        left, top, right, bottom = UIManager.GetFrameCoords(frame_id)
        return (
            f"id={frame_id} "
            f"parent={int(frame.parent_id)} "
            f"child_offset={int(frame.child_offset_id)} "
            f"created={bool(frame.is_created)} "
            f"visible={bool(frame.is_visible)} "
            f"state=0x{int(frame.frame_state):X} "
            f"rect=({left:.0f},{top:.0f})-({right:.0f},{bottom:.0f})"
        )
    except Exception as exc:
        return f"frame_id={frame_id} error={exc}"


def _resolve_window_id() -> int:
    return int(UIManager.GetFrameIDByLabel(FRAME_LABEL) or 0)


def _resolve_proc() -> None:
    global LAST_PROC_ADDR
    global LAST_STATUS

    def _invoke() -> None:
        global LAST_PROC_ADDR
        LAST_PROC_ADDR = int(PyUIManager.UIManager.resolve_container_frame_proc() or 0)
        _log(f"resolve proc complete addr=0x{LAST_PROC_ADDR:X}")

    LAST_STATUS = "resolve proc enqueued"
    Py4GW.Game.enqueue(_invoke)


def _create_window() -> None:
    global LAST_FRAME_ID
    global LAST_STATUS

    def _do_create() -> None:
        global LAST_FRAME_ID

        if GWContext.Char.GetContext() is None:
            _log("create aborted: char context unavailable")
            return

        engine_y = _engine_y_from_top(TARGET_Y, TARGET_HEIGHT)

        frame_id = int(
            PyUIManager.UIManager.create_titled_container_window(
                TARGET_X,
                engine_y,
                TARGET_WIDTH,
                TARGET_HEIGHT,
                title=FRAME_LABEL,
                parent_frame_id=9,
                child_index=0,
                frame_flags=TARGET_FRAME_FLAGS,
                anchor_flags=ANCHOR_FLAGS,
                subclass_flags=SUBCLASS_FLAGS,
            )
            or 0
        )

        if frame_id == 0:
            # Try to determine WHY it failed
            if PyUIManager.UIManager.resolve_composite_root_control_proc() == 0:
                _log("create failed: CRProc resolution failed")
            elif PyUIManager.UIManager.resolve_container_frame_proc() == 0:
                _log("create failed: ContainerFrameProc resolution failed")
            else:
                _log("create failed: CreateTitledContainerWindow returned 0 (unknown reason)")
            return

        LAST_FRAME_ID = frame_id
        _log(f"titled container created: {_frame_summary(frame_id)}")

    existing = _resolve_window_id()
    if existing > 0 and _frame_exists(existing):
        _log(f"found orphaned window frame_id={existing} ({_frame_summary(existing)}), destroying first")
        GWUI.DestroyUIComponentByFrameId(existing)
        # Schedule create for next game tick (separate from destroy tick)
        LAST_STATUS = "create window enqueued (after orphan destroy)"
        Py4GW.Game.enqueue(_do_create)
        return

    LAST_STATUS = "create window enqueued"
    Py4GW.Game.enqueue(_do_create)


def _destroy_window() -> None:
    global LAST_FRAME_ID
    global LAST_STATUS

    def _invoke() -> None:
        global LAST_FRAME_ID
        window_id = _resolve_window_id()
        if window_id <= 0 or not _frame_exists(window_id):
            window_id = int(LAST_FRAME_ID or 0)
            if window_id <= 0 or not _frame_exists(window_id):
                _log("destroy skipped: no window found")
                return
        GWUI.DestroyUIComponentByFrameId(window_id)
        _log(f"destroy complete frame_id={window_id} surviving={_frame_exists(window_id)}")
        LAST_FRAME_ID = 0

    LAST_STATUS = "destroy window enqueued"
    Py4GW.Game.enqueue(_invoke)


def _snapshot() -> None:
    window_id = _resolve_window_id()
    _log(
        f"snapshot window=({_frame_summary(window_id)}) "
        f"proc=0x{LAST_PROC_ADDR:X} "
        f"last_frame_id={LAST_FRAME_ID}"
    )


def _diagnose_crproc() -> None:
    """Resolve CRProc + create window entirely in Python. No C++ rebuild."""
    def _run():
        from Py4GWCoreLib.native_src.internals.native_function import NativeFunction
        from Py4GWCoreLib.native_src.internals.prototypes import NativeFunctionPrototype
        import ctypes

        _log("=== Python-Only Window Creation ===")

        if GWContext.Char.GetContext() is None:
            _log("  FAILED: no char context")
            return

        # --- Resolve CRProc ---
        assertion_addr = Scanner.FindAssertion("UiCtlDlg.cpp", "!s_imgList", 0, 0)
        crproc_addr = Scanner.ToFunctionStart(assertion_addr, 0x110) if assertion_addr else 0
        _log(f"  CRProc = 0x{crproc_addr:08X}")
        if not crproc_addr:
            _log("  FAILED: CRProc resolution")
            return

        # --- Resolve FrameNewSubclass ---
        subclass_addr = PyUIManager.UIManager.resolve_frame_new_subclass()
        _log(f"  FrameNewSubclass = 0x{subclass_addr:08X}")
        if not subclass_addr:
            _log("  FAILED: FrameNewSubclass")
            return

        # --- Resolve FrameMouseEnable ---
        mouse_addr = PyUIManager.UIManager.resolve_frame_mouse_enable()
        _log(f"  FrameMouseEnable = 0x{mouse_addr:08X}")
        if not mouse_addr:
            _log("  FAILED: FrameMouseEnable")
            return

        # --- Destroy orphan ---
        existing = _resolve_window_id()
        if existing > 0 and _frame_exists(existing):
            _log(f"  Destroying orphan frame_id={existing}")
            GWUI.DestroyUIComponentByFrameId(existing)

        # --- Create bare container ---
        engine_y = _engine_y_from_top(TARGET_Y, TARGET_HEIGHT)
        frame_id = int(
            PyUIManager.UIManager.create_container_window(
                TARGET_X, engine_y, TARGET_WIDTH, TARGET_HEIGHT,
                FRAME_LABEL, 9, 0, TARGET_FRAME_FLAGS, 0, ANCHOR_FLAGS,
            ) or 0
        )
        _log(f"  Container frame_id={frame_id}")
        if not frame_id:
            _log("  FAILED: CreateContainerWindow")
            return

        global LAST_FRAME_ID
        LAST_FRAME_ID = frame_id

        # --- Build NativeFunctions ---
        subclass_proto = NativeFunctionPrototype(None, ctypes.c_uint32, ctypes.c_void_p, ctypes.c_void_p)
        Subclass = NativeFunction.from_address("FrameNewSubclass", subclass_addr, subclass_proto)

        mouse_proto = NativeFunctionPrototype(None, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_uint32)
        MouseEnable = NativeFunction.from_address("FrameMouseEnable", mouse_addr, mouse_proto)

        # --- Install chrome (enqueued on game thread) ---
        fid = frame_id
        crproc = crproc_addr

        def _install_chrome():
            Subclass.directCall(fid, crproc, SUBCLASS_FLAGS)
            MouseEnable.directCall(fid, 0xFFFFFFFF, 0)
            UIManager.ShowFrame(fid, True)
            UIManager.TriggerFrameRedrawByFrameId(fid)
            _log(f"  Chrome installed on frame_id={fid}")

        Py4GW.Game.enqueue(_install_chrome)
        _log(f"  Window frame_id={frame_id} — chrome enqueued")
        _log("=== Complete ===")

    Py4GW.Game.enqueue(_run)


def _draw_window() -> None:
    global WINDOW_OPEN
    global TARGET_X
    global TARGET_Y
    global TARGET_WIDTH
    global TARGET_HEIGHT
    global TARGET_FRAME_FLAGS

    if not PyImGui.begin(f"{MODULE_NAME}##{SCRIPT_REVISION}", WINDOW_OPEN):
        PyImGui.end()
        return

    TARGET_X = float(PyImGui.input_float("X", TARGET_X))
    TARGET_Y = float(PyImGui.input_float("Y From Top", TARGET_Y))
    TARGET_WIDTH = float(PyImGui.input_float("Width", TARGET_WIDTH))
    TARGET_HEIGHT = float(PyImGui.input_float("Height", TARGET_HEIGHT))
    TARGET_FRAME_FLAGS = int(PyImGui.input_int("Frame Flags (hex)", TARGET_FRAME_FLAGS)) & 0xFFFFFFFF

    global SUBCLASS_FLAGS
    SUBCLASS_FLAGS = int(PyImGui.input_int("Subclass Flags (hex)", SUBCLASS_FLAGS)) & 0xFFFFFFFF

    if PyImGui.button("Resolve Proc"):
        _resolve_proc()

    PyImGui.same_line(0.0, 8.0)
    if PyImGui.button("Resolve Composite Proc"):
        Py4GW.Game.enqueue(lambda: _log(
            f"composite proc resolve FAILED"
            if not PyUIManager.UIManager.resolve_composite_root_control_proc()
            else f"composite proc addr=0x{PyUIManager.UIManager.resolve_composite_root_control_proc():X}"
        ))

    PyImGui.same_line(0.0, 8.0)
    if PyImGui.button("Resolve FrameNewSubclass"):
        Py4GW.Game.enqueue(lambda: _log(
            f"frame_new_subclass addr=0x{PyUIManager.UIManager.resolve_frame_new_subclass():X}"
        ))

    PyImGui.same_line(0.0, 8.0)
    if PyImGui.button("Resolve FrameMouseEnable"):
        Py4GW.Game.enqueue(lambda: _log(
            f"frame_mouse_enable addr=0x{PyUIManager.UIManager.resolve_frame_mouse_enable():X}"
            if PyUIManager.UIManager.resolve_frame_mouse_enable()
            else "frame_mouse_enable FAILED"
        ))

    PyImGui.same_line(0.0, 8.0)
    if PyImGui.button("Diagnose CRProc"):
        _diagnose_crproc()

    if PyImGui.button("Create Py4GW Window"):
        _create_window()

    PyImGui.same_line(0.0, 8.0)
    if PyImGui.button("Set Title"):
        def _set_title():
            window_id = _resolve_window_id()
            if window_id <= 0 or not _frame_exists(window_id):
                _log("set title: no window")
                return
            ok = PyUIManager.UIManager.set_frame_title_by_frame_id(window_id, FRAME_LABEL)
            _log(f"set title frame_id={window_id} ok={ok}")
            if not ok:
                return
            def _delayed_redraw():
                PyUIManager.UIManager.trigger_frame_redraw_by_frame_id(window_id)
            Py4GW.Game.enqueue(_delayed_redraw)
        Py4GW.Game.enqueue(_set_title)

    if PyImGui.button("Create DevText Clone"):
        def _clone():
            engine_y = _engine_y_from_top(TARGET_Y, TARGET_HEIGHT)
            fid = int(GWUI.CreateWindow(
                TARGET_X + 20, engine_y + 20, TARGET_WIDTH, TARGET_HEIGHT,
                frame_label="DevTextClone",
                ensure_devtext_source=True,
            ) or 0)
            _log(f"devtext clone frame_id={fid}")
        Py4GW.Game.enqueue(_clone)

    PyImGui.same_line(0.0, 8.0)
    if PyImGui.button("Clone + Custom Title"):
        def _clone_titled():
            PyUIManager.UIManager.set_next_created_window_title(FRAME_LABEL)
            engine_y = _engine_y_from_top(TARGET_Y, TARGET_HEIGHT)
            fid = int(GWUI.CreateWindow(
                TARGET_X + 20, engine_y + 20, TARGET_WIDTH, TARGET_HEIGHT,
                frame_label="TitledClone",
                ensure_devtext_source=True,
            ) or 0)
            _log(f"titled clone frame_id={fid}")
            # Clear contents to get empty window
            if fid:
                GWUI.ClearWindowContentsByFrameId(fid)
        Py4GW.Game.enqueue(_clone_titled)

    PyImGui.same_line(0.0, 8.0)
    if PyImGui.button("Set Clone Title"):
        def _set_clone():
            clone_id = int(UIManager.GetFrameIDByLabel("DevTextClone") or 0)
            if clone_id <= 0:
                _log("clone not found")
                return
            ok = PyUIManager.UIManager.set_frame_title_by_frame_id(clone_id, "CHANGED")
            _log(f"clone title set frame_id={clone_id} ok={ok}")
            if ok:
                PyUIManager.UIManager.trigger_frame_redraw_by_frame_id(clone_id)
        Py4GW.Game.enqueue(_set_clone)

    PyImGui.same_line(0.0, 8.0)
    if PyImGui.button("GWUI.SetTitle"):
        def _gwui_set():
            window_id = _resolve_window_id()
            if window_id <= 0:
                _log("gwui: no window")
                return
            ok = GWUI.SetWindowTitle(window_id, "Py4GW GWUI")
            _log(f"gwui set title frame_id={window_id} ok={ok}")
        Py4GW.Game.enqueue(_gwui_set)

    PyImGui.same_line(0.0, 8.0)
    if PyImGui.button("Send Msg 0x46"):
        def _send_46():
            window_id = _resolve_window_id()
            if window_id <= 0:
                _log("msg46: no window")
                return
            UIManager.SendUIMessageRaw(window_id, 0x46, 0, 0)
            _log(f"msg 0x46 sent to frame_id={window_id}")
        Py4GW.Game.enqueue(_send_46)

    PyImGui.same_line(0.0, 8.0)
    if PyImGui.button("TriggerFrameRedraw"):
        def _tr_redraw():
            window_id = _resolve_window_id()
            if window_id <= 0:
                return
            UIManager.TriggerFrameRedrawByFrameId(window_id)
            _log(f"trigger_frame_redraw frame_id={window_id}")
        Py4GW.Game.enqueue(_tr_redraw)

    PyImGui.same_line(0.0, 8.0)
    if PyImGui.button("Destroy Window"):
        _destroy_window()

    PyImGui.same_line(0.0, 8.0)
    if PyImGui.button("Snapshot"):
        Py4GW.Game.enqueue(_snapshot)

    PyImGui.separator()
    PyImGui.text(f"revision: {SCRIPT_REVISION}")
    PyImGui.text("Creates a titled container window with native chrome (title bar, resize, close).")
    PyImGui.text("Uses CreateContainerWindow + FrameNewSubclass + FrameMouseEnable + Ui_CompositeRootControlProc.")
    PyImGui.separator()

    current_window_id = _resolve_window_id()
    PyImGui.text(f"proc_addr       = 0x{LAST_PROC_ADDR:X}")
    PyImGui.text(f"current_window  = {current_window_id}")
    PyImGui.text(f"window_exists   = {_frame_exists(current_window_id)}")
    PyImGui.text(f"last_frame_id   = {LAST_FRAME_ID}")
    PyImGui.text(f"last_status     = {LAST_STATUS}")
    PyImGui.separator()
    PyImGui.text(f"container = {_frame_summary(current_window_id)}")

    PyImGui.end()


def main() -> None:
    global INITIALIZED
    global WINDOW_OPEN

    if not INITIALIZED:
        INITIALIZED = True
        _log(f"script revision={SCRIPT_REVISION}")
        _log("creates titled container window with native chrome via CreateTitledContainerWindow")

    if not WINDOW_OPEN:
        def _cleanup() -> None:
            window_id = _resolve_window_id()
            if window_id > 0 and _frame_exists(window_id):
                GWUI.DestroyUIComponentByFrameId(window_id)
                _log(f"widget close cleanup destroyed frame_id={window_id}")
        Py4GW.Game.enqueue(_cleanup)
        return

    _draw_window()


if __name__ == "__main__":
    main()
