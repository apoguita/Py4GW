import math
import time
from pathlib import Path

import Py4GW
import PyImGui

from Py4GWCoreLib import ActionQueueManager, ConsoleLog, Map, Party, Player, Routines, ThrottledTimer, Timer
from Py4GWCoreLib.py4gwcorelib_src.IniHandler import IniHandler


BOT_NAME = "Kamadan Trade Spammer"
KAMADAN_MAP_ID = 449
TRADE_CHANNEL = "$"
TRADE_MODES = ["WTS", "WTB"]
COOLDOWN_OPTIONS_MINUTES = [1, 2, 3, 5]
MAP_LOAD_TIMEOUT_MS = 15000
PARTY_LEAVE_TIMEOUT_MS = 4000
RETURN_TO_OUTPOST_TIMEOUT_MS = 5000
INTER_MESSAGE_DELAY_MS = 1250
WAIT_STEP_MS = 100
SPAM_SPOT_COORD = (-8010.0, 14680.0)
SPAM_APPROACH_PATH = [(-8016.0, 14428.0), SPAM_SPOT_COORD]
SPAM_SPOT_REPOSITION_RADIUS = 1500.0
MOVE_TOLERANCE = 175.0
SETTINGS_SECTION = "Kamadan Trade Spammer"
SETTINGS_PATH = Path(__file__).with_suffix(".ini")


class SpammerSettings:
    def __init__(self) -> None:
        self.mode_index = 0
        self.cooldown_index = 0
        self.auto_leave_party = True
        self.auto_reposition = True
        self.messages = ["", "", ""]

    def cooldown_minutes(self) -> int:
        index = max(0, min(self.cooldown_index, len(COOLDOWN_OPTIONS_MINUTES) - 1))
        return COOLDOWN_OPTIONS_MINUTES[index]

    def cooldown_ms(self) -> int:
        return self.cooldown_minutes() * 60 * 1000


class SpammerRuntime:
    def __init__(self) -> None:
        self.running = False
        self.controller = None
        self.status = "Idle"
        self.status_lines = []
        self.cycles_sent = 0
        self.messages_sent = 0
        self.current_message_index = 0
        self.current_cycle_size = 0
        self.cooldown_timer = Timer()
        self.save_timer = ThrottledTimer(700)
        self.settings_dirty = False


settings = SpammerSettings()
runtime = SpammerRuntime()
ini_handler = IniHandler(str(SETTINGS_PATH))


def clamp(value: int, minimum: int, maximum: int) -> int:
    return max(minimum, min(value, maximum))


def load_settings() -> None:
    settings.mode_index = clamp(
        ini_handler.read_int(SETTINGS_SECTION, "mode_index", 0),
        0,
        len(TRADE_MODES) - 1,
    )
    settings.cooldown_index = clamp(
        ini_handler.read_int(SETTINGS_SECTION, "cooldown_index", 0),
        0,
        len(COOLDOWN_OPTIONS_MINUTES) - 1,
    )
    settings.auto_leave_party = ini_handler.read_bool(SETTINGS_SECTION, "auto_leave_party", True)
    settings.auto_reposition = ini_handler.read_bool(SETTINGS_SECTION, "auto_reposition", True)
    for index in range(3):
        settings.messages[index] = ini_handler.read_key(
            SETTINGS_SECTION,
            f"message_{index + 1}",
            settings.messages[index],
        )


def save_settings() -> None:
    ini_handler.write_key(SETTINGS_SECTION, "mode_index", settings.mode_index)
    ini_handler.write_key(SETTINGS_SECTION, "cooldown_index", settings.cooldown_index)
    ini_handler.write_key(SETTINGS_SECTION, "auto_leave_party", settings.auto_leave_party)
    ini_handler.write_key(SETTINGS_SECTION, "auto_reposition", settings.auto_reposition)
    for index, message in enumerate(settings.messages, start=1):
        ini_handler.write_key(SETTINGS_SECTION, f"message_{index}", message)


def mark_settings_dirty() -> None:
    runtime.settings_dirty = True
    runtime.save_timer.Reset()


def persist_settings_if_needed() -> None:
    if runtime.settings_dirty and runtime.save_timer.IsExpired():
        save_settings()
        runtime.settings_dirty = False


def push_status(message: str, message_type=Py4GW.Console.MessageType.Info) -> None:
    runtime.status = message
    timestamp = time.strftime("%H:%M:%S")
    runtime.status_lines.append(f"{timestamp} - {message}")
    runtime.status_lines = runtime.status_lines[-8:]
    ConsoleLog(BOT_NAME, message, message_type)


def distance_to(x: float, y: float) -> float:
    px, py = Player.GetXY()
    return math.hypot(px - x, py - y)


def active_messages() -> list[str]:
    built_messages = []
    for raw_message in settings.messages:
        built = build_trade_message(raw_message)
        if built:
            built_messages.append(built)
    return built_messages


def build_trade_message(raw_message: str) -> str:
    message = raw_message.strip()
    if not message:
        return ""

    upper_message = message.upper()
    if upper_message.startswith("WTB ") or upper_message.startswith("WTS "):
        return message

    prefix = TRADE_MODES[settings.mode_index]
    return f"{prefix} {message}"


def format_duration_ms(milliseconds: float) -> str:
    remaining_seconds = max(0, int(milliseconds / 1000))
    minutes = remaining_seconds // 60
    seconds = remaining_seconds % 60
    return f"{minutes:02}:{seconds:02}"


def start_spammer() -> None:
    if not active_messages():
        push_status("Add at least one trade message before starting.", Py4GW.Console.MessageType.Warning)
        return

    ActionQueueManager().ResetAllQueues()
    runtime.cooldown_timer.Stop()
    runtime.cycles_sent = 0
    runtime.messages_sent = 0
    runtime.current_message_index = 0
    runtime.current_cycle_size = 0
    runtime.running = True
    runtime.controller = spammer_loop()
    push_status("Spammer started.")
    save_settings()


def stop_spammer(reason: str = "Spammer stopped.") -> None:
    runtime.running = False
    runtime.controller = None
    runtime.current_message_index = 0
    runtime.current_cycle_size = 0
    runtime.cooldown_timer.Stop()
    ActionQueueManager().ResetAllQueues()
    push_status(reason)
    save_settings()


def wait_for_condition(predicate, timeout_ms: int, step_ms: int = WAIT_STEP_MS):
    timer = Timer()
    timer.Start()
    while runtime.running and not predicate():
        if timer.HasElapsed(timeout_ms):
            return False
        yield from Routines.Yield.wait(step_ms)
    return predicate()


def ensure_kamadan():
    if Map.IsMapLoading():
        push_status("Waiting for current map load to finish.")
        if not (
            yield from wait_for_condition(
                lambda: not Map.IsMapLoading() and Map.IsMapReady(),
                MAP_LOAD_TIMEOUT_MS,
            )
        ):
            push_status("Map load did not settle in time.", Py4GW.Console.MessageType.Warning)
            return False

    if Map.GetMapID() == KAMADAN_MAP_ID and Map.IsOutpost():
        return True

    if Map.IsExplorable():
        push_status("Returning to outpost before traveling to Kamadan.")
        Party.ReturnToOutpost()
        yield from Routines.Yield.wait(500)
        if not (
            yield from wait_for_condition(
                lambda: Map.IsMapLoading() or Map.IsOutpost(),
                RETURN_TO_OUTPOST_TIMEOUT_MS,
            )
        ):
            push_status(
                "ReturnToOutpost did not transition cleanly; waiting for an outpost to become available.",
                Py4GW.Console.MessageType.Warning,
            )
            return False

    push_status("Traveling to Kamadan.")
    travel_success = yield from Routines.Yield.Map.TravelToOutpost(
        KAMADAN_MAP_ID,
        log=False,
        timeout=MAP_LOAD_TIMEOUT_MS,
    )
    if not travel_success:
        push_status("Travel to Kamadan failed.", Py4GW.Console.MessageType.Warning)
        return False

    return Map.GetMapID() == KAMADAN_MAP_ID and Map.IsOutpost()


def leave_group_if_needed():
    if not settings.auto_leave_party:
        return True

    if Party.GetPartySize() <= 1:
        return True

    push_status("Leaving party before spamming.")
    Party.LeaveParty()
    if not (
        yield from wait_for_condition(
            lambda: Party.GetPartySize() <= 1,
            PARTY_LEAVE_TIMEOUT_MS,
        )
    ):
        push_status("Party leave did not complete in time.", Py4GW.Console.MessageType.Warning)
        return False
    return True


def move_to_spam_spot():
    if not settings.auto_reposition:
        return True

    if distance_to(*SPAM_SPOT_COORD) <= SPAM_SPOT_REPOSITION_RADIUS:
        return True

    push_status("Moving to the Kamadan spam spot.")
    follow_success = yield from Routines.Yield.Movement.FollowPath(
        SPAM_APPROACH_PATH,
        tolerance=MOVE_TOLERANCE,
        log=False,
        timeout=12000,
    )
    if not follow_success:
        push_status("Failed to reach the spam spot.", Py4GW.Console.MessageType.Warning)
        return False
    return distance_to(*SPAM_SPOT_COORD) <= SPAM_SPOT_REPOSITION_RADIUS


def send_trade_message(message: str, index: int, total: int):
    if not runtime.running:
        return False

    if Map.GetMapID() != KAMADAN_MAP_ID or not Map.IsOutpost() or Map.IsMapLoading():
        push_status("Kamadan is no longer ready; restarting preparation.", Py4GW.Console.MessageType.Warning)
        return False

    runtime.current_message_index = index
    runtime.current_cycle_size = total
    push_status(f"Sending message {index}/{total}.")
    Player.SendChat(TRADE_CHANNEL, message)
    runtime.messages_sent += 1
    yield from Routines.Yield.wait(350)
    return True


def spammer_loop():
    while runtime.running:
        messages = active_messages()
        if not messages:
            stop_spammer("All messages are empty. Spammer stopped.")
            return

        push_status("Preparing spammer.")
        if not (yield from ensure_kamadan()):
            yield from Routines.Yield.wait(1000)
            continue

        if not (yield from leave_group_if_needed()):
            yield from Routines.Yield.wait(1000)
            continue

        if not (yield from move_to_spam_spot()):
            yield from Routines.Yield.wait(1000)
            continue

        restart_cycle = False
        total_messages = len(messages)
        for index, message in enumerate(messages, start=1):
            if not runtime.running:
                return

            if settings.auto_reposition and distance_to(*SPAM_SPOT_COORD) > SPAM_SPOT_REPOSITION_RADIUS:
                push_status("Moved away from the spam spot; repositioning.", Py4GW.Console.MessageType.Warning)
                restart_cycle = True
                break

            if not (yield from send_trade_message(message, index, total_messages)):
                restart_cycle = True
                break

            if index < total_messages:
                push_status(f"Waiting before message {index + 1}/{total_messages}.")
                yield from Routines.Yield.wait(INTER_MESSAGE_DELAY_MS)

        if restart_cycle:
            runtime.current_message_index = 0
            runtime.current_cycle_size = 0
            yield from Routines.Yield.wait(500)
            continue

        runtime.cycles_sent += 1
        runtime.current_message_index = 0
        runtime.current_cycle_size = total_messages
        runtime.cooldown_timer.Reset()
        push_status("Waiting for next send cycle.")
        while runtime.running and not runtime.cooldown_timer.HasElapsed(settings.cooldown_ms()):
            if Map.GetMapID() != KAMADAN_MAP_ID or not Map.IsOutpost() or Map.IsMapLoading():
                push_status("Map changed during cooldown; re-preparing.", Py4GW.Console.MessageType.Warning)
                break
            yield from Routines.Yield.wait(250)


def advance_spammer() -> None:
    if runtime.controller is None:
        return

    try:
        next(runtime.controller)
    except StopIteration:
        runtime.controller = None
        if runtime.running:
            runtime.running = False
            runtime.cooldown_timer.Stop()
            push_status("Spammer loop finished.")
    except Exception as exc:
        runtime.controller = None
        runtime.running = False
        runtime.cooldown_timer.Stop()
        ActionQueueManager().ResetAllQueues()
        push_status(f"Spammer error: {exc}", Py4GW.Console.MessageType.Error)
        raise


def draw_ui() -> None:
    window_flags = PyImGui.WindowFlags.AlwaysAutoResize
    PyImGui.set_next_window_size(520, 0)
    if PyImGui.begin(BOT_NAME, window_flags):
        PyImGui.text("Kamadan trade chat spammer")
        PyImGui.separator()
        PyImGui.text_wrapped(
            "Prepares the current client in Kamadan, optionally leaves party, repositions near the chest area, then sends non-empty trade messages to '$' in a timed loop."
        )
        PyImGui.spacing()

        if runtime.running:
            if PyImGui.button("Stop", 120, 30):
                stop_spammer()
        else:
            if PyImGui.button("Start", 120, 30):
                start_spammer()

        PyImGui.same_line(0.0, 10.0)
        PyImGui.text(f"Status: {runtime.status}")

        mode_index = PyImGui.combo("Mode", settings.mode_index, TRADE_MODES)
        if mode_index != settings.mode_index:
            settings.mode_index = mode_index
            mark_settings_dirty()

        cooldown_labels = [f"{minutes} minute" if minutes == 1 else f"{minutes} minutes" for minutes in COOLDOWN_OPTIONS_MINUTES]
        cooldown_index = PyImGui.combo("Cycle Cooldown", settings.cooldown_index, cooldown_labels)
        if cooldown_index != settings.cooldown_index:
            settings.cooldown_index = cooldown_index
            mark_settings_dirty()

        auto_leave = PyImGui.checkbox("Leave party automatically", settings.auto_leave_party)
        if auto_leave != settings.auto_leave_party:
            settings.auto_leave_party = auto_leave
            mark_settings_dirty()

        auto_reposition = PyImGui.checkbox("Reposition near spam spot", settings.auto_reposition)
        if auto_reposition != settings.auto_reposition:
            settings.auto_reposition = auto_reposition
            mark_settings_dirty()

        PyImGui.separator()
        for index in range(3):
            updated_message = PyImGui.input_text(
                f"Message {index + 1}",
                settings.messages[index],
                180,
            )
            if updated_message != settings.messages[index]:
                settings.messages[index] = updated_message
                mark_settings_dirty()

        PyImGui.separator()
        PyImGui.text(f"Current Map: {Map.GetMapID()}")
        PyImGui.text(f"Cycles Sent: {runtime.cycles_sent}")
        PyImGui.text(f"Messages Sent: {runtime.messages_sent}")

        if runtime.running and runtime.cooldown_timer.IsRunning():
            remaining = max(0, settings.cooldown_ms() - runtime.cooldown_timer.GetElapsedTime())
            PyImGui.text(f"Next cycle in: {format_duration_ms(remaining)}")

        if runtime.current_cycle_size > 0 and runtime.current_message_index > 0:
            PyImGui.text(f"Active send: {runtime.current_message_index}/{runtime.current_cycle_size}")

        PyImGui.separator()
        PyImGui.text("Recent activity:")
        if not runtime.status_lines:
            PyImGui.text_disabled("No activity yet.")
        else:
            for line in runtime.status_lines[-6:]:
                PyImGui.text_wrapped(line)
    PyImGui.end()


def main():
    try:
        advance_spammer()
        persist_settings_if_needed()
        draw_ui()
    except Exception as exc:
        ConsoleLog(BOT_NAME, f"Unhandled error: {exc}", Py4GW.Console.MessageType.Error)
        raise

def tooltip():
    import PyImGui
    from Py4GWCoreLib import ImGui, Color

    PyImGui.begin_tooltip()

    title_color = Color(255, 200, 100, 255)

    ImGui.push_font("Regular", 20)
    PyImGui.text_colored("Kamadan Trade Spammer", title_color.to_tuple_normalized())
    ImGui.pop_font()

    PyImGui.spacing()
    PyImGui.separator()
    PyImGui.spacing()

    PyImGui.text("Tool for sending trade messages in Kamadan")
    PyImGui.text("with a configurable timed loop.")
    
    PyImGui.spacing()
    PyImGui.text_colored("Credits", title_color.to_tuple_normalized())
    PyImGui.bullet_text("Developed by XLeek")

    PyImGui.end_tooltip()


load_settings()

if __name__ == "__main__":
    main()
