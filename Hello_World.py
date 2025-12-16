from Py4GWCoreLib import (UIManager, GLOBAL_CACHE, Console, ConsoleLog, Routines, ThrottledTimer,
                          Keystroke, Key, FrameInfo, CHAR_MAP
                          )
import PyImGui
import Py4GW

from datetime import datetime, timedelta
BOOT_TIME = datetime.now() - timedelta(milliseconds=Py4GW.Game.get_tick_count64())

def decode_frame_timestamp(tick_value: int) -> str:
    event_dt = BOOT_TIME + timedelta(milliseconds=tick_value)
    return event_dt.strftime("%H:%M:%S.%f")[:-3]  # HH:MM:SS.mmm

def draw_window():
    if PyImGui.begin("Address tester"):
        
        if PyImGui.button("add routine"):
            GLOBAL_CACHE.Coroutines.append(Routines.Yield.RerollCharacter.DeleteAndCreateCharacter(
                character_name_to_delete="Dialgoeur Main",
                new_character_name="Dialoguer Main",
                campaign_name="Nightfall",
                profession_name="Dervish",
                timeout_ms=60000,
                log=True
            ))

        frame_logs = UIManager.GetFrameLogs()
        frame_logs = list(reversed(frame_logs))

        if PyImGui.button("Print Logs"):
            for ts, parent_frame_id, label in UIManager.GetFrameLogs():
                frame_id =  UIManager.GetFrameIDByLabel(label)
                print(f"[{decode_frame_timestamp(ts)}] Frame {frame_id}: {label}")


        for ts, parent_frame_id, label in frame_logs:
            frame_id =  UIManager.GetFrameIDByLabel(label)
            t = decode_frame_timestamp(ts)
            PyImGui.text(f"[{t}] Frame ID: {frame_id}, Label: {label}")

    PyImGui.end()



def main():
    draw_window()
    target = GLOBAL_CACHE.Player.GetTargetID()
    model = GLOBAL_CACHE.Agent.GetModelID(target)


if __name__ == "__main__":
    main()
