import PyImGui
import Py4GW

from Py4GWCoreLib.UIManager import UIManager
from Py4GWCoreLib.enums_src.UI_enums import UIMessage
from Py4GWCoreLib import ImGui, Color

from datetime import datetime, timedelta

def draw_multi_table(
    table_id: str,
    headers: list[str],
    rows: list[list[str | int | float]]
):
    """
    Generic multi-column table renderer.
    headers: ["Index", "Timestamp", "Frame ID", "Label"]
    rows:    [[0, "12:34:56", 123, "Foo"], ...]
    """

    column_count = len(headers)

    flags = (
        PyImGui.TableFlags.BordersInnerH
        | PyImGui.TableFlags.BordersInnerV
        | PyImGui.TableFlags.RowBg
        | PyImGui.TableFlags.Resizable
        | PyImGui.TableFlags.ScrollY
        | PyImGui.TableFlags.SizingStretchProp
    )

    if PyImGui.begin_table(table_id, column_count, flags):

        # column setup
        for name in headers:
            PyImGui.table_setup_column(name, PyImGui.TableColumnFlags.WidthStretch)

        PyImGui.table_headers_row()

        # rows
        for row in rows:
            PyImGui.table_next_row()
            for col_index, value in enumerate(row):
                PyImGui.table_set_column_index(col_index)
                PyImGui.text_unformatted(str(value))

        PyImGui.end_table()

# ---------------------------------------------------------
# GLOBAL ANCHOR (initialized once)
# ---------------------------------------------------------
_anchor_walltime: datetime = datetime.now()
_anchor_tick = Py4GW.Game.get_tick_count64()


# ---------------------------------------------------------
# PURE TIMESTAMP CONVERSION USING TICK DELTA ONLY
# ---------------------------------------------------------
def tick_to_timestamp(event_tick: int) -> str:
    global _anchor_walltime, _anchor_tick
    """
    Convert an event tick to an absolute wall clock timestamp (HH:MM:SS.mmm)
    using a fixed anchor. This avoids jitter because datetime.now()
    is never used after the anchor is set.
    """
    ms_delta = event_tick - _anchor_tick
    event_time = _anchor_walltime + timedelta(milliseconds=ms_delta)
    return event_time.strftime("%H:%M:%S")  # up to milliseconds


# ---------------------------------------------------------
# EXAMPLE USAGE IN YOUR WINDOW
# ---------------------------------------------------------


def draw_window():

    if PyImGui.begin("UI Listener Window", True, PyImGui.WindowFlags.AlwaysAutoResize):
        if PyImGui.begin_tab_bar("MainTabBar"):
            if PyImGui.begin_tab_item("Frame Label Listener"):
                if PyImGui.begin_child("FrameLabelChild", (1000, 800), True, 0):

                    frame_logs = UIManager.GetFrameLogs()
                    frame_logs.reverse()

                    headers = ["Index", "Timestamp", "Frame ID", "Label"]
                    rows = []

                    for i, (tick, frame_id, label) in enumerate(frame_logs):
                        ts = tick_to_timestamp(tick)
                        rows.append([i, ts, frame_id, label])

                    draw_multi_table("FrameLabelTable", headers, rows)

                PyImGui.end_child()
                PyImGui.end_tab_item()
            if PyImGui.begin_tab_item("UI Message Listener"):
                if PyImGui.begin_child("UIMessageChild", (1000, 800), True, 0):
                    if PyImGui.button("Clear UI Message Logs"):
                        UIManager.ClearUIMessageLogs()
                        

                    frame_logs = UIManager.GetUIMessageLogs()
                    frame_logs.reverse()

                    headers = ["Index", "Timestamp", "Incoming", "Is Frame Message", "Frame ID", "UI Message ID", "WParam", "LParam"]
                    rows = []

                    for i, (tick, message_id,incoming,is_frame_message, frame_id, w_bytes, lbytes) in enumerate(frame_logs):
                        ts = tick_to_timestamp(tick)
                        message_str  = UIMessage(message_id).name if message_id in UIMessage._value2member_map_ else hex(message_id)
                        rows.append([
                            i, ts, incoming, is_frame_message, frame_id, message_str,
                            w_bytes[:8],    # take only first 8 bytes
                            lbytes[:8]      # same here
                        ])

                    draw_multi_table("UIMessageTable", headers, rows)
                    
                    if PyImGui.button("print logs to console"):
                         for i, (tick, message_id,incoming,is_frame_message, frame_id, w_bytes, lbytes) in enumerate(frame_logs):
                            ts = tick_to_timestamp(tick)
                            message_str  = UIMessage(message_id).name if message_id in UIMessage._value2member_map_ else hex(message_id)
                            print(f"[{i}] {ts} | Incoming: {incoming} | IsFrameMsg: {is_frame_message} | FrameID: {frame_id} | MsgID: {message_str} | WParam: {w_bytes} | LParam: {lbytes}")

                PyImGui.end_child()
                PyImGui.end_tab_item()

            PyImGui.end_tab_bar()

    PyImGui.end()
    
def tooltip():
    PyImGui.begin_tooltip()

    # Title
    title_color = Color(255, 200, 100, 255)
    ImGui.push_font("Regular", 20)
    PyImGui.text_colored("UI Message Listener", title_color.to_tuple_normalized())
    ImGui.pop_font()
    PyImGui.spacing()
    PyImGui.separator()

    # Description
    PyImGui.text("A low-level diagnostic tool for intercepting and logging internal")
    PyImGui.text("game UI messages. Essential for reverse-engineering frame behaviors")
    PyImGui.text("and identifying specific UI triggers for automation.")
    PyImGui.spacing()

    # Features
    PyImGui.text_colored("Features:", title_color.to_tuple_normalized())
    PyImGui.bullet_text("Message Interception: Capture real-time 'WParam' and 'LParam' packet data")
    PyImGui.bullet_text("Frame Filtering: Track messages specifically linked to internal Frame IDs")
    PyImGui.bullet_text("Traffic Analysis: Separate view for Incoming vs. Outgoing UI communications")
    PyImGui.bullet_text("Data Logging: Precise millisecond timestamps for every intercepted message")
    PyImGui.bullet_text("Export Utility: Print full raw byte-logs to the console for external analysis")

    PyImGui.spacing()
    PyImGui.separator()
    PyImGui.spacing()

    # Credits
    PyImGui.text_colored("Credits:", title_color.to_tuple_normalized())
    PyImGui.bullet_text("Developed by Apo")

    PyImGui.end_tooltip()
    

def main():
    draw_window()


if __name__ == "__main__":
    main()
