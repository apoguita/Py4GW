import PyImGui
import Py4GW
from Py4GWCoreLib import UIManager
from Py4GWCoreLib.Context import GWContext


MODULE_NAME = "FrameLogDump"
WINDOW_NAME = "Frame Log Dump"
dump_count = 0
selected_action = 0x24
PLAYER_FLAG_DEBUG_UI = 0x8
KNOWN_ACTIONS = [
    ("0x21 Props Box?", 0x21),
    ("0x24 Sound Check", 0x24),
    ("0x27 Toggle Debug A", 0x27),
    ("0x28 Toggle Cloth?", 0x28),
    ("0x46 Unlock Camera", 0x46),
    ("0x4B Chunks?", 0x4B),
    ("0x4F Terrain Toggle", 0x4F),
    ("0x50 Walkable Outline", 0x50),
    ("0x56 Visible Blocks", 0x56),
]


def _print_frame_logs() -> int:
    logs = list(UIManager.GetFrameLogs())
    print(f"[{MODULE_NAME}] BEGIN frame logs count={len(logs)}")
    for index, (tick, frame_id, label) in enumerate(logs):
        safe_label = "" if label is None else str(label)
        print(f"[{MODULE_NAME}] {index:04d} tick={tick} frame_id={frame_id} label={safe_label}")
    print(f"[{MODULE_NAME}] END frame logs count={len(logs)}")
    return len(logs)


def _trigger_hidden_action(action_value: int) -> None:
    def _action():
        char_ctx = GWContext.Char.GetContext()
        if char_ctx is None:
            print(f"[{MODULE_NAME}] CharContext unavailable; could not trigger action 0x{action_value:02X}")
            return

        original_flags = int(char_ctx.player_flags)
        try:
            char_ctx.player_flags = original_flags | PLAYER_FLAG_DEBUG_UI
            UIManager.Keypress(action_value, 0)
            print(f"[{MODULE_NAME}] Enqueued hidden action 0x{action_value:02X}")
        finally:
            char_ctx.player_flags = original_flags

    Py4GW.Game.enqueue(_action)


def main():
    global dump_count, selected_action

    if PyImGui.begin(WINDOW_NAME):
        current_count = len(UIManager.GetFrameLogs())
        PyImGui.text(f"Captured logs: {current_count}")
        PyImGui.text(f"Dumps this session: {dump_count}")
        PyImGui.text(f"Selected action: 0x{selected_action:02X} ({selected_action})")

        if PyImGui.button("Dump Logs To Console"):
            _print_frame_logs()
            dump_count += 1

        if PyImGui.button("Trigger Selected Action"):
            _trigger_hidden_action(selected_action)

        if PyImGui.button("Previous Value"):
            selected_action = max(0, selected_action - 1)

        if PyImGui.button("Next Value"):
            selected_action = min(0xFFFF, selected_action + 1)

        for label, value in KNOWN_ACTIONS:
            if PyImGui.button(label):
                selected_action = value
                _trigger_hidden_action(selected_action)

        if PyImGui.button("Dump And Clear"):
            _print_frame_logs()
            UIManager.ClearFrameLogs()
            dump_count += 1

        if PyImGui.button("Clear Logs"):
            UIManager.ClearFrameLogs()

    PyImGui.end()


if __name__ == "__main__":
    main()
