import time
from datetime import datetime
from datetime import timezone

import Py4GW
import PyUIManager

from HeroAI.cache_data import CacheData
from Py4GWCoreLib import GLOBAL_CACHE, Player, Map, Agent, Effects
from Py4GWCoreLib import ActionQueueManager
from Py4GWCoreLib import CombatPrepSkillsType
from Py4GWCoreLib import Console
from Py4GWCoreLib import ConsoleLog
from Py4GWCoreLib import LootConfig
import PyImGui
from Py4GWCoreLib import Range, TitleID
from Py4GWCoreLib import Routines
from Py4GWCoreLib import Utils, ImGui, Color, ColorPalette
from Py4GWCoreLib import SharedCommandType
from Py4GWCoreLib import UIManager
from Py4GWCoreLib import AutoPathing
from Py4GWCoreLib import IniHandler
from Py4GWCoreLib.GlobalCache.SharedMemory import AccountStruct
from Py4GWCoreLib.Py4GWcorelib import Keystroke
from Py4GWCoreLib.enums_src.Model_enums import ModelID
from Py4GWCoreLib.py4gwcorelib_src.WidgetManager import get_widget_handler

cached_data = CacheData()


MODULE_NAME = "Messaging"
OPTIONAL = False

SUMMON_SPIRITS_LUXON = "Summon_Spirits_luxon"
SUMMON_SPIRITS_KURZICK = "Summon_Spirits_kurzick"
ARMOR_OF_UNFEELING = "Armor_of_Unfeeling"

width, height = 0, 0


class HeroAIoptions:
    def __init__(self):
        self.Following = False
        self.Avoidance = False
        self.Looting = False
        self.Targeting = False
        self.Combat = False
        self.Skills: list[bool] = [False] * 8


hero_ai_snapshots: list[HeroAIoptions] = []

combat_prep_first_skills_check = True
hero_ai_has_ritualist_skills = False
hero_ai_has_paragon_skills = False


# region ImGui
def configure():
    DrawWindow()
    
def tooltip():
    PyImGui.begin_tooltip()

    # Title
    title_color = Color(255, 200, 100, 255)
    ImGui.push_font("Regular", 20)
    PyImGui.text_colored("Messaging", title_color.to_tuple_normalized())
    ImGui.pop_font()
    red = ColorPalette.GetColor("red")
    PyImGui.text_colored("This is a system Widget, deactivating it will cause issues.", red.to_tuple_normalized())
    PyImGui.separator()

    # Description
    #ellaborate a better description 
    PyImGui.text("This widget provides a comprehensive interface")
    PyImGui.text("for monitoring and managing messages exchanged")
    PyImGui.text("between accounts on your system using the shared")
    PyImGui.text("memory messaging system.")
    
    PyImGui.spacing()

    # Features
    PyImGui.text_colored("Features:", title_color.to_tuple_normalized())
    PyImGui.bullet_text("View incoming messages")
    PyImGui.bullet_text("Mark messages as finished")
    PyImGui.bullet_text("Supports various message commands")

    PyImGui.spacing()
    PyImGui.separator()
    PyImGui.spacing()

    # Credits
    PyImGui.text_colored("Credits:", title_color.to_tuple_normalized())
    PyImGui.bullet_text("Developed by Apo")
    PyImGui.bullet_text("Contributors: Mark, frenkey, aC")

    PyImGui.end_tooltip()


def DrawWindow():
    if PyImGui.begin(MODULE_NAME):
        account_email = Player.GetAccountEmail()
        PyImGui.text(f"Account Email: {account_email}")
        PyImGui.separator()
        PyImGui.text("Messages for you:")
        index, message = GLOBAL_CACHE.ShMem.PreviewNextMessage(account_email)

        if index == -1 or message is None:
            PyImGui.text("No new messages.")
        else:
            sender = message.SenderEmail
            receiver = message.ReceiverEmail
            if sender is None or receiver is None:
                PyImGui.text("Invalid message data.")
                PyImGui.end()
                return

            command: SharedCommandType = SharedCommandType(message.Command)
            params: tuple[float, ...] = tuple(message.Params)
            extra_data: tuple[str, ...] = tuple(message.ExtraData)
            active = message.Active
            running = message.Running
            timestamp = message.Timestamp
            PyImGui.text(f"Message {index}:")
            PyImGui.text(f"Sender: {sender}")
            PyImGui.text(f"Receiver: {receiver}")
            PyImGui.text(f"Command: {SharedCommandType(command).name}")
            PyImGui.text(f"Params: {', '.join(map(str, params))}")
            PyImGui.text(f"ExtraData: {', '.join(map(str, extra_data))}")
            PyImGui.text(f"Active: {active}")
            PyImGui.text(f"Running: {running}")
            PyImGui.text(f"Timestamp: {timestamp}")
            if PyImGui.button(f"finish_{index}"):
                GLOBAL_CACHE.ShMem.MarkMessageAsFinished(receiver, index)
        PyImGui.separator()

        PyImGui.text("All messages:")

        messages = GLOBAL_CACHE.ShMem.GetAllMessages()
        if len(messages) == 0:
            PyImGui.text("No messages available.")
        else:
            for msg in messages:
                index, message = msg
                if message is None:
                    continue

                sender = message.SenderEmail
                receiver = message.ReceiverEmail
                if sender is None or receiver is None:
                    continue

                command: SharedCommandType = SharedCommandType(message.Command)
                params: tuple[float, ...] = tuple(message.Params)
                running = message.Running
                timestamp = message.Timestamp

                PyImGui.text(f"Message {index}:")
                PyImGui.text(f"Sender: {sender}")
                PyImGui.text(f"Receiver: {receiver}")
                PyImGui.text(f"Command: {SharedCommandType(command).name}")
                PyImGui.text(f"Params: {', '.join(map(str, params))}")
                PyImGui.text(f"Running: {running}")
                PyImGui.text(f"Timestamp: {timestamp}")
                if PyImGui.button(f"finish_{index}"):
                    GLOBAL_CACHE.ShMem.MarkMessageAsFinished(receiver, index)
                PyImGui.separator()

    PyImGui.end()


# endregion
# region HeroAI Snapshot
def SnapshotHeroAIOptions(account_email):
    global hero_ai_snapshots
    hero_ai_options = GLOBAL_CACHE.ShMem.GetHeroAIOptions(account_email)
    if hero_ai_options is None:
        return
    
    data: HeroAIoptions = HeroAIoptions()
    data.Following = hero_ai_options.Following
    data.Avoidance = hero_ai_options.Avoidance
    data.Looting = hero_ai_options.Looting
    data.Targeting = hero_ai_options.Targeting
    data.Combat = hero_ai_options.Combat

    hero_ai_snapshots.append(data)



def RestoreHeroAISnapshot(account_email):
    global hero_ai_snapshots
    
    if not hero_ai_snapshots:
        EnableHeroAIOptions(account_email)  # If no snapshot, just enable everything to be safe
        ConsoleLog(MODULE_NAME, "No Hero AI snapshot found, enabling all options as fallback.", Console.MessageType.Warning, True)
        return
    
    hero_ai_options = GLOBAL_CACHE.ShMem.GetHeroAIOptions(account_email)
    if hero_ai_options is None:
        return
    
    last_state = hero_ai_snapshots.pop()

    hero_ai_options.Following = last_state.Following
    hero_ai_options.Avoidance = last_state.Avoidance
    hero_ai_options.Looting = last_state.Looting
    hero_ai_options.Targeting = last_state.Targeting
    hero_ai_options.Combat = last_state.Combat



def DisableHeroAIOptions(account_email):
    hero_ai_options = GLOBAL_CACHE.ShMem.GetHeroAIOptions(account_email)
    if hero_ai_options is None:
        return

    hero_ai_options.Following = False
    hero_ai_options.Avoidance = False
    hero_ai_options.Looting = False
    hero_ai_options.Targeting = False
    hero_ai_options.Combat = False



def EnableHeroAIOptions(account_email):
    hero_ai_options = GLOBAL_CACHE.ShMem.GetHeroAIOptions(account_email)
    if hero_ai_options is None:
        return

    hero_ai_options.Following = True
    hero_ai_options.Avoidance = True
    hero_ai_options.Looting = True
    hero_ai_options.Targeting = True
    hero_ai_options.Combat = True



# endregion

# region InviteToParty


def InviteToParty(index, message):
    # ConsoleLog(MODULE_NAME, f"Processing InviteToParty message: {message}", Console.MessageType.Info)
    GLOBAL_CACHE.ShMem.MarkMessageAsRunning(message.ReceiverEmail, index)
    sender_data = GLOBAL_CACHE.ShMem.GetAccountDataFromEmail(message.SenderEmail)
    if sender_data is None:
        GLOBAL_CACHE.ShMem.MarkMessageAsFinished(message.ReceiverEmail, index)
        return
    yield from Routines.Yield.wait(100)
    GLOBAL_CACHE.Party.Players.InvitePlayer(sender_data.CharacterName)
    yield from Routines.Yield.wait(100)
    GLOBAL_CACHE.ShMem.MarkMessageAsFinished(message.ReceiverEmail, index)
    ConsoleLog(MODULE_NAME, "InviteToParty message processed and finished.", Console.MessageType.Info, False)


# endregion


# region LeaveParty
def LeaveParty(index, message):
    # ConsoleLog(MODULE_NAME, f"Processing LeaveParty message: {message}", Console.MessageType.Info)
    GLOBAL_CACHE.ShMem.MarkMessageAsRunning(message.ReceiverEmail, index)
    sender_data = GLOBAL_CACHE.ShMem.GetAccountDataFromEmail(message.SenderEmail)
    if sender_data is None:
        GLOBAL_CACHE.ShMem.MarkMessageAsFinished(message.ReceiverEmail, index)
        return
    GLOBAL_CACHE.Party.LeaveParty()
    yield from Routines.Yield.wait(100)
    GLOBAL_CACHE.ShMem.MarkMessageAsFinished(message.ReceiverEmail, index)
    ConsoleLog(MODULE_NAME, "LeaveParty message processed and finished.", Console.MessageType.Info, False)


# endregion

# region TravelToMap


def TravelToMap(index, message):
    # ConsoleLog(MODULE_NAME, f"Processing TravelToMap message: {message}", Console.MessageType.Info)
    GLOBAL_CACHE.ShMem.MarkMessageAsRunning(message.ReceiverEmail, index)
    sender_data = GLOBAL_CACHE.ShMem.GetAccountDataFromEmail(message.SenderEmail)
    if sender_data is None:
        GLOBAL_CACHE.ShMem.MarkMessageAsFinished(message.ReceiverEmail, index)
        return

    map_id = int(message.Params[0])
    map_region = int(message.Params[1])
    map_district = int(message.Params[2])
    language = int(message.Params[3])

    yield from Routines.Yield.Map.TravelToRegion(map_id, map_region, map_district, language=language, log=True)
    yield from Routines.Yield.wait(100)
    GLOBAL_CACHE.ShMem.MarkMessageAsFinished(message.ReceiverEmail, index)
    ConsoleLog(MODULE_NAME, "TravelToMap message processed and finished.", Console.MessageType.Info, False)


# endregion

# region Resign
def Resign(index, message):
    if not Routines.Checks.Map.MapValid():
        ConsoleLog(MODULE_NAME, "Map is not valid, cannot process resign message.", Console.MessageType.Warning)
        GLOBAL_CACHE.ShMem.MarkMessageAsFinished(message.ReceiverEmail, index)
        return

    # ConsoleLog(MODULE_NAME, f"Processing Resign message: {message}", Console.MessageType.Info)
    GLOBAL_CACHE.ShMem.MarkMessageAsRunning(message.ReceiverEmail, index)
    for i in range(2):
        Player.SendChatCommand("resign")
        yield from Routines.Yield.wait(100)
    GLOBAL_CACHE.ShMem.MarkMessageAsFinished(message.ReceiverEmail, index)
    ConsoleLog(MODULE_NAME, "Resign message processed and finished.", Console.MessageType.Info, False)
# endregion

# region PixelStack
def PixelStack(index, message):
    ConsoleLog(MODULE_NAME, f"Processing PixelStack message: {message}", Console.MessageType.Info)
    GLOBAL_CACHE.ShMem.MarkMessageAsRunning(message.ReceiverEmail, index)
    sender_data = GLOBAL_CACHE.ShMem.GetAccountDataFromEmail(message.SenderEmail)
    if sender_data is None:
        GLOBAL_CACHE.ShMem.MarkMessageAsFinished(message.ReceiverEmail, index)
        return

    SnapshotHeroAIOptions(message.ReceiverEmail)
    try:
        DisableHeroAIOptions(message.ReceiverEmail)
        yield from Routines.Yield.wait(100)
        Player.SendChatCommand("stuck")
        yield from Routines.Yield.wait(250)
        result = (yield from Routines.Yield.Movement.FollowPath(
            [(message.Params[0], message.Params[1])],
            tolerance=10,
            timeout=10000,
        ))
        yield from Routines.Yield.wait(100)

        if not result:
            ConsoleLog(MODULE_NAME, "PixelStack movement failed or timed out.", Console.MessageType.Warning, log=True)

            # --- Recovery sequence ---
            start_x, start_y = Player.GetXY()
            Player.SendChatCommand("stuck")
            # Step 1: Always walk backwards
            ConsoleLog(MODULE_NAME, "Recovery: walking backwards.", Console.MessageType.Info)
            yield from Routines.Yield.Movement.WalkBackwards(1500)
            # Step 2: strafe left
            ConsoleLog(MODULE_NAME, "Recovery: strafing left.", Console.MessageType.Info)
            yield from Routines.Yield.Movement.StrafeLeft(1500)
            # Step 3: If no movement after strafing left, strafe right
            left_x, left_y = Player.GetXY()
            if Utils.Distance((start_x, start_y), (left_x, left_y)) < 50:
                ConsoleLog(MODULE_NAME, "No movement detected, strafing right.", Console.MessageType.Info)
                yield from Routines.Yield.Movement.StrafeRight(3500)  # we need to get away from that wall

        else:
            ConsoleLog(MODULE_NAME, "PixelStack movement succeeded.", Console.MessageType.Info, log=False)
    finally:
        EnableHeroAIOptions(message.ReceiverEmail)
        GLOBAL_CACHE.ShMem.MarkMessageAsFinished(message.ReceiverEmail, index)


# endregion


# region BruteForceUnstuck
def BruteForceUnstuck(index, message):
    ConsoleLog(MODULE_NAME, f"Processing BruteForceUnstuck message: {message}", Console.MessageType.Info)
    GLOBAL_CACHE.ShMem.MarkMessageAsRunning(message.ReceiverEmail, index)
    sender_data = GLOBAL_CACHE.ShMem.GetAccountDataFromEmail(message.SenderEmail)
    if sender_data is None:
        GLOBAL_CACHE.ShMem.MarkMessageAsFinished(message.ReceiverEmail, index)
        return

    SnapshotHeroAIOptions(message.ReceiverEmail)
    try:
        DisableHeroAIOptions(message.ReceiverEmail)
        yield from Routines.Yield.wait(100)

        # Initial stuck command
        Player.SendChatCommand("stuck")
        yield from Routines.Yield.wait(250)

        # --- Recovery sequence attempts ---
        start_x, start_y = Player.GetXY()

        # --- define wiggle helpers ---
        def wiggle_back_left():
            for _ in range(3):
                yield from Routines.Yield.Movement.WalkBackwards(250)
                yield from Routines.Yield.Movement.StrafeLeft(250)

        def wiggle_back_right():
            for _ in range(3):
                yield from Routines.Yield.Movement.WalkBackwards(250)
                yield from Routines.Yield.Movement.StrafeRight(250)

        # --- attempts dictionary ---
        attempts = [
            {"name": "backwards", "action": lambda: Routines.Yield.Movement.WalkBackwards(1000)},
            {"name": "strafe_left", "action": lambda: Routines.Yield.Movement.StrafeLeft(1000)},
            {"name": "strafe_right", "action": lambda: Routines.Yield.Movement.StrafeRight(2000)},
            {"name": "wiggle_back_left", "action": wiggle_back_left},
            {"name": "wiggle_back_right", "action": wiggle_back_right},
        ]

        for attempt in attempts:
            ConsoleLog(MODULE_NAME, f"Recovery: {attempt['name']}.", Console.MessageType.Info)
            yield from attempt["action"]()

            # Check movement
            cur_x, cur_y = Player.GetXY()
            if Utils.Distance((start_x, start_y), (cur_x, cur_y)) > 50:
                ConsoleLog(MODULE_NAME, f"Unstuck successful with {attempt['name']}.", Console.MessageType.Info)
                break
        else:
            ConsoleLog(MODULE_NAME, "All unstuck attempts failed.", Console.MessageType.Warning)

    finally:
        EnableHeroAIOptions(message.ReceiverEmail)
        GLOBAL_CACHE.ShMem.MarkMessageAsFinished(message.ReceiverEmail, index)
# endregion

# region InteractWithTarget


def InteractWithTarget(index, message):
    ConsoleLog(MODULE_NAME, f"Processing InteractWithTarget message: {message}", Console.MessageType.Info, False)
    GLOBAL_CACHE.ShMem.MarkMessageAsRunning(message.ReceiverEmail, index)
    sender_data = GLOBAL_CACHE.ShMem.GetAccountDataFromEmail(message.SenderEmail)
    if sender_data is None:
        GLOBAL_CACHE.ShMem.MarkMessageAsFinished(message.ReceiverEmail, index)
        return

    target = int(message.Params[0])
    if target == 0:
        ConsoleLog(MODULE_NAME, "Invalid target ID.", Console.MessageType.Warning)
        GLOBAL_CACHE.ShMem.MarkMessageAsFinished(message.ReceiverEmail, index)
        return

    SnapshotHeroAIOptions(message.ReceiverEmail)
    try:
        DisableHeroAIOptions(message.ReceiverEmail)
        yield from Routines.Yield.wait(100)
        x, y = Agent.GetXY(target)
        yield from Routines.Yield.Movement.FollowPath([(x, y)])
        yield from Routines.Yield.wait(100)
        yield from Routines.Yield.Player.InteractAgent(target)

        ConsoleLog(MODULE_NAME, "InteractWithTarget message processed and finished.", Console.MessageType.Info, False)
    finally:
        RestoreHeroAISnapshot(message.ReceiverEmail)
        GLOBAL_CACHE.ShMem.MarkMessageAsFinished(message.ReceiverEmail, index)


# endregion
# region TakeDialogWithTarget
def TakeDialogWithTarget(index, message):
    ConsoleLog(MODULE_NAME, f"Processing TakeDialogWithTarget message: {message}", Console.MessageType.Info, False)
    GLOBAL_CACHE.ShMem.MarkMessageAsRunning(message.ReceiverEmail, index)
    sender_data = GLOBAL_CACHE.ShMem.GetAccountDataFromEmail(message.SenderEmail)
    if sender_data is None:
        GLOBAL_CACHE.ShMem.MarkMessageAsFinished(message.ReceiverEmail, index)
        return

    target = int(message.Params[0])
    if target == 0:
        ConsoleLog(MODULE_NAME, "Invalid target ID.", Console.MessageType.Warning)
        GLOBAL_CACHE.ShMem.MarkMessageAsFinished(message.ReceiverEmail, index)
        return

    SnapshotHeroAIOptions(message.ReceiverEmail)
    try:
        DisableHeroAIOptions(message.ReceiverEmail)
        yield from Routines.Yield.wait(100)
        x, y = Agent.GetXY(target)
        yield from Routines.Yield.Movement.FollowPath([(x, y)])
        yield from Routines.Yield.wait(100)
        yield from Routines.Yield.Player.InteractAgent(target)
        yield from Routines.Yield.wait(500)
        if UIManager.IsNPCDialogVisible():
            UIManager.ClickDialogButton(int(message.Params[1]))
            yield from Routines.Yield.wait(200)

        ConsoleLog(MODULE_NAME, "TakeDialogWithTarget message processed and finished.", Console.MessageType.Info, False)
    finally:
        RestoreHeroAISnapshot(message.ReceiverEmail)
        GLOBAL_CACHE.ShMem.MarkMessageAsFinished(message.ReceiverEmail, index)
# endregion

# region SendDialogToTarget
def SendDialogToTarget(index, message):
    ConsoleLog(MODULE_NAME, f"Processing SendDialogToTarget message: {message}", Console.MessageType.Info, False)
    GLOBAL_CACHE.ShMem.MarkMessageAsRunning(message.ReceiverEmail, index)
    sender_data = GLOBAL_CACHE.ShMem.GetAccountDataFromEmail(message.SenderEmail)
    if sender_data is None:
        GLOBAL_CACHE.ShMem.MarkMessageAsFinished(message.ReceiverEmail, index)
        return

    target = int(message.Params[0])
    if target == 0:
        ConsoleLog(MODULE_NAME, "Invalid target ID.", Console.MessageType.Warning)
        GLOBAL_CACHE.ShMem.MarkMessageAsFinished(message.ReceiverEmail, index)
        return

    dialog = int(message.Params[1])

    SnapshotHeroAIOptions(message.ReceiverEmail)
    try:
        DisableHeroAIOptions(message.ReceiverEmail)
        yield from Routines.Yield.wait(100)
        x, y = Agent.GetXY(target)
        yield from Routines.Yield.Movement.FollowPath([(x, y)])
        yield from Routines.Yield.wait(100)
        yield from Routines.Yield.Player.InteractAgent(target)
        yield from Routines.Yield.wait(500)
        Player.SendDialog(dialog)
        yield from Routines.Yield.wait(500)

        ConsoleLog(MODULE_NAME, "SendDialogToTarget message processed and finished.", Console.MessageType.Info, False)
    finally:
        RestoreHeroAISnapshot(message.ReceiverEmail)
        GLOBAL_CACHE.ShMem.MarkMessageAsFinished(message.ReceiverEmail, index)
# endregion

# region SendDialog
def SendDialog(index, message):
    ConsoleLog(MODULE_NAME, f"Processing SendDialog message: {message}", Console.MessageType.Info, False)
    GLOBAL_CACHE.ShMem.MarkMessageAsRunning(message.ReceiverEmail, index)
    sender_data = GLOBAL_CACHE.ShMem.GetAccountDataFromEmail(message.SenderEmail)
    if sender_data is None:
        GLOBAL_CACHE.ShMem.MarkMessageAsFinished(message.ReceiverEmail, index)
        return

    if UIManager.IsNPCDialogVisible():
        UIManager.ClickDialogButton(int(message.Params[0]))
        
    yield from Routines.Yield.wait(500)
    GLOBAL_CACHE.ShMem.MarkMessageAsFinished(message.ReceiverEmail, index)
# endregion

# region GetBlessing
def GetBlessing(index, message):
    GLOBAL_CACHE.ShMem.MarkMessageAsRunning(message.ReceiverEmail, index)
    sender_data = GLOBAL_CACHE.ShMem.GetAccountDataFromEmail(message.SenderEmail)
    if sender_data is None:
        GLOBAL_CACHE.ShMem.MarkMessageAsFinished(message.ReceiverEmail, index)
        return

    target = int(message.Params[0])
    if target == 0:
        ConsoleLog(MODULE_NAME, "Invalid target ID.", Console.MessageType.Warning)
        GLOBAL_CACHE.ShMem.MarkMessageAsFinished(message.ReceiverEmail, index)
        return

    SnapshotHeroAIOptions(message.ReceiverEmail)
    try:
        DisableHeroAIOptions(message.ReceiverEmail)
        yield from Routines.Yield.wait(100)
        x, y = Agent.GetXY(target)
        yield from Routines.Yield.Movement.FollowPath([(x, y)])
        yield from Routines.Yield.wait(100)
        yield from Routines.Yield.Player.InteractAgent(target)
        yield from Routines.Yield.wait(500)
        if UIManager.IsNPCDialogVisible():
            UIManager.ClickDialogButton(message.Params[1])
            yield from Routines.Yield.wait(200)

        ConsoleLog(MODULE_NAME, "GetBlessing message processed and finished.", Console.MessageType.Info, False)
    finally:
        RestoreHeroAISnapshot(message.ReceiverEmail)
        GLOBAL_CACHE.ShMem.MarkMessageAsFinished(message.ReceiverEmail, index)


# endregion
# region UsePcon


def UsePcon(index, message):
    ConsoleLog(MODULE_NAME, f"Processing UsePcon message: {message}", Console.MessageType.Info, False)
    GLOBAL_CACHE.ShMem.MarkMessageAsRunning(message.ReceiverEmail, index)

    pcon_model_id = int(message.Params[0])
    pcon_skill_id = int(message.Params[1])
    pcon_model_id2 = int(message.Params[2])
    pcon_skill_id2 = int(message.Params[3])

    # Halt if any of the effects is already active
    if GLOBAL_CACHE.ShMem.HasEffect(message.ReceiverEmail, pcon_skill_id) or GLOBAL_CACHE.ShMem.HasEffect(
        message.ReceiverEmail, pcon_skill_id2
    ):
        # ConsoleLog(MODULE_NAME, "Player already has the effect of one of the PCon skills.", Console.MessageType.Warning)
        GLOBAL_CACHE.ShMem.MarkMessageAsFinished(message.ReceiverEmail, index)
        return

    # Check inventory to determine which PCon to use
    if GLOBAL_CACHE.Inventory.GetModelCount(pcon_model_id) > 0:
        pcon_model_to_use = pcon_model_id
    elif GLOBAL_CACHE.Inventory.GetModelCount(pcon_model_id2) > 0:
        pcon_model_to_use = pcon_model_id2
    else:
        # ConsoleLog(MODULE_NAME, "Player does not have any of the required PCons in inventory.", Console.MessageType.Warning)
        GLOBAL_CACHE.ShMem.MarkMessageAsFinished(message.ReceiverEmail, index)
        return

    item_id = GLOBAL_CACHE.Item.GetItemIdFromModelID(pcon_model_to_use)
    if item_id == 0:
        # ConsoleLog(MODULE_NAME, f"Could not find item ID for PCon model {pcon_model_to_use}.", Console.MessageType.Error)
        GLOBAL_CACHE.ShMem.MarkMessageAsFinished(message.ReceiverEmail, index)
        return

    GLOBAL_CACHE.Inventory.UseItem(item_id)
    ConsoleLog(
        MODULE_NAME, f"Using PCon model {pcon_model_to_use} with item_id {item_id}.", Console.MessageType.Info, False
    )
    yield from Routines.Yield.wait(100)
    GLOBAL_CACHE.ShMem.MarkMessageAsFinished(message.ReceiverEmail, index)
    # ConsoleLog(MODULE_NAME, "UsePcon message processed and finished.", Console.MessageType.Info)


# endregion


# region PressKey
def PressKey(index, message):
    ConsoleLog(MODULE_NAME, f"Processing PressKey message: {message}", Console.MessageType.Info, False)
    GLOBAL_CACHE.ShMem.MarkMessageAsRunning(message.ReceiverEmail, index)

    key_id = int(message.Params[0])
    repetition = int(message.Params[1]) if len(message.Params) > 1 else 1

    if key_id:
        for _ in range(repetition):
            Keystroke.PressAndRelease(key_id)
            yield from Routines.Yield.wait(100)

    GLOBAL_CACHE.ShMem.MarkMessageAsFinished(message.ReceiverEmail, index)
    ConsoleLog(MODULE_NAME, "PressKey message processed and finished.", Console.MessageType.Info, False)


# endregion
# region DonateToGuild
def DonateToGuild(index, message):
    MODULE = "DonateFaction"
    CHUNK = 5000

    GLOBAL_CACHE.ShMem.MarkMessageAsRunning(message.ReceiverEmail, index)

    # --- Guards ---
    if not Routines.Checks.Map.MapValid():
        ConsoleLog(MODULE, "Invalid map, cannot donate.", Console.MessageType.Warning)
        GLOBAL_CACHE.ShMem.MarkMessageAsFinished(message.ReceiverEmail, index)
        return

    map_id = Map.GetMapID()
    TITLE_CAP = 10_000_000
    TOTAL_CUMULATIVE = 0
    if map_id == 77:  # House zu Heltzer
        faction = 0  # Kurzick
        npc_pos = (5408, 1494)
        CURRENT_FACTION = Player.GetKurzickData()[0]
        title = Player.GetTitle(TitleID.Kurzick)
        TOTAL_CUMULATIVE = title.current_points if title else 0
    elif map_id == 193:  # Cavalon
        faction = 1  # Luxon
        npc_pos = (9074, -1124)
        CURRENT_FACTION = Player.GetLuxonData()[0]
        title = Player.GetTitle(TitleID.Luxon)
        TOTAL_CUMULATIVE = title.current_points if title else 0
    else:
        ConsoleLog(MODULE, "Not in a valid outpost for donation.", Console.MessageType.Warning)
        GLOBAL_CACHE.ShMem.MarkMessageAsFinished(message.ReceiverEmail, index)
        return

    # --- Move to NPC ---
    px, py = Player.GetXY()
    z = Agent.GetZPlane(Player.GetAgentID())
    try:
        path3d = yield from AutoPathing().get_path(
            (px, py, z), (npc_pos[0], npc_pos[1], z), smooth_by_los=True, margin=100.0, step_dist=500.0
        )
    except Exception:
        path3d = []

    path2d = [(x, y) for (x, y, *_) in path3d] if path3d else [npc_pos]
    yield from Routines.Yield.Movement.FollowPath(path2d)

    # --- Interact with NPC ---
    yield from Routines.Yield.wait(400)
    yield from Routines.Yield.Agents.InteractWithAgentXY(*npc_pos)
    yield from Routines.Yield.wait(400)

    if TOTAL_CUMULATIVE <= TITLE_CAP:  # donate faction points if title is not maxed
        # --- Donation loop ---
        chunks = CURRENT_FACTION // CHUNK
        for _ in range(chunks):
            if not UIManager.IsNPCDialogVisible():
                yield from Routines.Yield.Player.InteractTarget()
                yield from Routines.Yield.wait(300)
                if not UIManager.IsNPCDialogVisible():
                    break
            Player.DepositFaction(faction)
            yield from Routines.Yield.wait(300)
    else:  # swap faction points for mats if title is maxed
        swapped = 0
        chunks = CURRENT_FACTION // CHUNK
        while swapped < chunks:
            if not UIManager.IsNPCDialogVisible():
                yield from Routines.Yield.Player.InteractTarget()
                yield from Routines.Yield.wait(250)
                if not UIManager.IsNPCDialogVisible():
                    break
            UIManager.ClickDialogButton(1)  # exchange
            yield from Routines.Yield.wait(250)
            UIManager.ClickDialogButton(2)  # confirm
            yield from Routines.Yield.wait(300)
            swapped += 1

    GLOBAL_CACHE.ShMem.MarkMessageAsFinished(message.ReceiverEmail, index)
# endregion

#region Open Chest
def OpenChest(index, message):
    start_time = time.time()
    
    cascade = int(message.Params[1]) == 1
    chest_id = int(message.Params[0])
    
    email_owner = message.ReceiverEmail or Player.GetAccountEmail()
    
    GLOBAL_CACHE.ShMem.MarkMessageAsRunning(email_owner, index)
    SnapshotHeroAIOptions(email_owner)
    
    def unlock_chest():
        has_lockpick = GLOBAL_CACHE.Inventory.GetModelCount(ModelID.Lockpick) > 0
        
        if not has_lockpick:
            ConsoleLog(MODULE_NAME, "No lockpicks available, halting.", Console.MessageType.Warning)
            return
            
        if not Agent.IsValid(chest_id):
            return
                
        DisableHeroAIOptions(email_owner)
        yield from Routines.Yield.wait(100)
        x, y = Agent.GetXY(chest_id)
        ConsoleLog(MODULE_NAME, f"Moving to chest at ({x}, {y})", Console.MessageType.Info)
        yield from Routines.Yield.Movement.FollowPath([(x, y)])
        yield from Routines.Yield.wait(100)
        
        ConsoleLog(MODULE_NAME, f"Interacting with chest ID {chest_id}", Console.MessageType.Info)
        yield from Routines.Yield.Player.InteractAgent(chest_id)
        yield from Routines.Yield.wait(150)

        ConsoleLog(MODULE_NAME, "Checking for locked chest window...", Console.MessageType.Info)
        if UIManager.IsLockedChestWindowVisible():
            while True:
                if time.time() - start_time > 30:
                    ConsoleLog(MODULE_NAME, "Timeout reached while opening chest, halting.", Console.MessageType.Warning)
                    return
            
                Player.SendDialog(2)
                yield from Routines.Yield.wait(1500)    
            
                if not UIManager.IsLockedChestWindowVisible():
                    ConsoleLog(MODULE_NAME, "Chest successfully unlocked.", Console.MessageType.Info)
                    return
        else:
            ConsoleLog(MODULE_NAME, "Chest is not locked or already opened.", Console.MessageType.Info)
                
    try:
        yield from unlock_chest()  
          
    finally:
        RestoreHeroAISnapshot(email_owner)      
        GLOBAL_CACHE.ShMem.MarkMessageAsFinished(email_owner, index)
          
        #Get Party Index and cascade to the next party index
        if cascade:
            ConsoleLog(MODULE_NAME, "Cascading OpenChest to next party member.", Console.MessageType.Info)
            account_data = GLOBAL_CACHE.ShMem.GetAccountDataFromEmail(email_owner)     
                   
            if account_data is not None:
                ConsoleLog(MODULE_NAME, f"Current account party position: {account_data.PartyPosition}", Console.MessageType.Info)
                
                party_id = account_data.PartyID
                map_id = Map.GetMapID()
                map_region = Map.GetRegion()[0]
                map_district = Map.GetDistrict()
                map_language = Map.GetLanguage()[0]

                def on_same_map_and_party(account : AccountStruct) -> bool:                    
                    return (account.PartyID == party_id and
                            account.MapID == map_id and
                            account.MapRegion == map_region and
                            account.MapDistrict == map_district and
                            account.MapLanguage == map_language)
                
                all_accounts = [account for account in GLOBAL_CACHE.ShMem.GetAllAccountData() if on_same_map_and_party(account) and account.PartyPosition > account_data.PartyPosition]
                chest_pos = Agent.GetXY(chest_id)
                                
                sorted_by_party_index = sorted(
                    [acc for acc in all_accounts if Utils.Distance((acc.PlayerPosX, acc.PlayerPosY), chest_pos) < 2500.0], 
                key=lambda acc: acc.PartyPosition ) if all_accounts else []
                
                if sorted_by_party_index:
                    next_account = sorted_by_party_index[0]
                    ConsoleLog(MODULE_NAME, f"Cascading OpenChest to next party member: {next_account.CharacterName} ({next_account.AccountEmail})", Console.MessageType.Info)
                    GLOBAL_CACHE.ShMem.SendMessage(
                        sender_email=email_owner,
                        receiver_email=next_account.AccountEmail,
                        command=SharedCommandType.OpenChest,
                        params=(chest_id, 1 if cascade else 0, 0, 0),
                    )
            else:
                ConsoleLog(MODULE_NAME, f"Account data of {email_owner} not found for cascading.", Console.MessageType.Warning)
                    
        else:
            ConsoleLog(MODULE_NAME, "OpenChest routine finished without cascading.", Console.MessageType.Info)
    

# region PickUpLoot
def PickUpLoot(index, message):
    def _exit_if_not_map_valid():
        if not Routines.Checks.Map.MapValid():
            RestoreHeroAISnapshot(message.ReceiverEmail)
            GLOBAL_CACHE.ShMem.MarkMessageAsFinished(message.ReceiverEmail, index)
            ActionQueueManager().ResetAllQueues()
            return True  # Signal that we must exit

        if GLOBAL_CACHE.Inventory.GetFreeSlotCount() < 1:
            ConsoleLog(
                MODULE_NAME,
                "No free slots in inventory, halting.",
                Console.MessageType.Error,
            )
            RestoreHeroAISnapshot(message.ReceiverEmail)
            GLOBAL_CACHE.ShMem.MarkMessageAsFinished(message.ReceiverEmail, index)
            ActionQueueManager().ResetAllQueues()
            return True

        return False

    def _GetBaseTimestamp():
        SHMEM_ZERO_EPOCH = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0).timestamp()
        return int((time.time() - SHMEM_ZERO_EPOCH) * 1000)

    GLOBAL_CACHE.ShMem.MarkMessageAsRunning(message.ReceiverEmail, index)

    loot_array = LootConfig().GetfilteredLootArray(Range.Earshot.value, multibox_loot=True)
    if len(loot_array) == 0:
        RestoreHeroAISnapshot(message.ReceiverEmail)  # <-- missing before
        GLOBAL_CACHE.ShMem.MarkMessageAsFinished(message.ReceiverEmail, index)
        return

    ConsoleLog(MODULE_NAME, "Starting PickUpLoot routine", Console.MessageType.Info, False)

    SnapshotHeroAIOptions(message.ReceiverEmail)
    try:
        DisableHeroAIOptions(message.ReceiverEmail)
        yield from Routines.Yield.wait(100)
        while True:
            loot_array = LootConfig().GetfilteredLootArray(Range.Earshot.value, multibox_loot=True)
            if len(loot_array) == 0:
                break
            item_id = loot_array.pop(0)
            if item_id is None or item_id == 0:
                continue

            if ( _exit_if_not_map_valid()):
                LootConfig().AddItemIDToBlacklist(item_id)
                ConsoleLog("PickUp Loot", "Map is not valid, halting.", Console.MessageType.Warning)
                ActionQueueManager().ResetAllQueues()
                return

            if not Agent.IsValid(item_id):
                yield from Routines.Yield.wait(100)
                continue

            pos = Agent.GetXY(item_id)
            follow_success = yield from Routines.Yield.Movement.FollowPath([pos], timeout=10000)
            if not follow_success:
                LootConfig().AddItemIDToBlacklist(item_id)
                ConsoleLog(
                    "PickUp Loot",
                    "Failed to follow path to loot item, halting.",
                    Console.MessageType.Warning,
                )
                ActionQueueManager().ResetAllQueues()
                return

            yield from Routines.Yield.wait(100)
            if (_exit_if_not_map_valid()):
                RestoreHeroAISnapshot(message.ReceiverEmail)
                return
            yield from Routines.Yield.Player.InteractAgent(item_id)
            yield from Routines.Yield.wait(100)
            start_time = _GetBaseTimestamp()
            timeout = 3000
            while True:
                current_time = _GetBaseTimestamp()

                delta = current_time - start_time
                if delta > timeout:
                    LootConfig().AddItemIDToBlacklist(item_id)
                    ConsoleLog(
                        "PickUp Loot",
                        "Timeout reached while picking up loot, halting.",
                        Console.MessageType.Warning,
                    )
                    ActionQueueManager().ResetAllQueues()
                    return

                if (_exit_if_not_map_valid()):
                    LootConfig().AddItemIDToBlacklist(item_id)
                    ConsoleLog(
                        "PickUp Loot",
                        "Map is not valid, halting.",
                        Console.MessageType.Warning,
                    )
                    ActionQueueManager().ResetAllQueues()
                    return

                loot_array = LootConfig().GetfilteredLootArray(Range.Earshot.value, multibox_loot=True)
                if item_id not in loot_array or len(loot_array) == 0:
                    yield from Routines.Yield.wait(100)
                    break
                yield from Routines.Yield.wait(100)

        ConsoleLog(MODULE_NAME, "PickUpLoot routine finished.", Console.MessageType.Info, False)
    finally:
        RestoreHeroAISnapshot(message.ReceiverEmail)
        GLOBAL_CACHE.ShMem.MarkMessageAsFinished(message.ReceiverEmail, index)
#endregion

# region DisableHeroAI / EnableHeroAI
def MessageDisableHeroAI(index, message):
    ConsoleLog(MODULE_NAME, f"Processing DisableHeroAI message: {message}", Console.MessageType.Info, False)
    GLOBAL_CACHE.ShMem.MarkMessageAsRunning(message.ReceiverEmail, index)
    account_email = message.ReceiverEmail
    SnapshotHeroAIOptions(account_email)
    DisableHeroAIOptions(account_email)
    GLOBAL_CACHE.ShMem.MarkMessageAsFinished(account_email, index)
    ConsoleLog(MODULE_NAME, "DisableHeroAI message processed and finished.", Console.MessageType.Info, False)
    yield


def MessageEnableHeroAI(index, message):
    ConsoleLog(MODULE_NAME, f"Processing EnableHeroAI message: {message}", Console.MessageType.Info, False)
    GLOBAL_CACHE.ShMem.MarkMessageAsRunning(message.ReceiverEmail, index)
    account_email = message.ReceiverEmail
    if message.Params[0]:
        EnableHeroAIOptions(account_email)
    else:
        RestoreHeroAISnapshot(account_email)
    GLOBAL_CACHE.ShMem.MarkMessageAsFinished(account_email, index)
    ConsoleLog(MODULE_NAME, "EnableHeroAI message processed and finished.", Console.MessageType.Info, False)
    yield
    
# endregion

# region SetWindowGeometry
def SetWindowGeometry(index, message):
    GLOBAL_CACHE.ShMem.MarkMessageAsRunning(message.ReceiverEmail, index)
    sender_data = GLOBAL_CACHE.ShMem.GetAccountDataFromEmail(message.SenderEmail)
    if sender_data is None:
        GLOBAL_CACHE.ShMem.MarkMessageAsFinished(message.ReceiverEmail, index)
        return
    Py4GW.Console.set_window_geometry(int(message.Params[0]), int(message.Params[1]), int(message.Params[2]), int(message.Params[3]))
    yield from Routines.Yield.wait(1500)
    GLOBAL_CACHE.ShMem.MarkMessageAsFinished(message.ReceiverEmail, index)
    ConsoleLog(MODULE_NAME, "SetWindowGeometry message processed and finished.", Console.MessageType.Info, False)
# endregion
#region SetWindowActive
def SetWindowActive(index, message):
    GLOBAL_CACHE.ShMem.MarkMessageAsRunning(message.ReceiverEmail, index)
    sender_data = GLOBAL_CACHE.ShMem.GetAccountDataFromEmail(message.SenderEmail)
    if sender_data is None:
        GLOBAL_CACHE.ShMem.MarkMessageAsFinished(message.ReceiverEmail, index)
        return
    
    Py4GW.Console.set_window_active()
    
    yield from Routines.Yield.wait(100)
    GLOBAL_CACHE.ShMem.MarkMessageAsFinished(message.ReceiverEmail, index)
    ConsoleLog(MODULE_NAME, "SetWindowActive message processed and finished.", Console.MessageType.Info, False)
# endregion
#region SetWindowTitle
def SetWindowTitle(index, message):
    GLOBAL_CACHE.ShMem.MarkMessageAsRunning(message.ReceiverEmail, index)

    sender_data = GLOBAL_CACHE.ShMem.GetAccountDataFromEmail(message.SenderEmail)
    if sender_data is None:
        GLOBAL_CACHE.ShMem.MarkMessageAsFinished(message.ReceiverEmail, index)
        return

    extra = tuple(GLOBAL_CACHE.ShMem._c_wchar_array_to_str(arr) for arr in message.ExtraData)
    title = extra[0] if extra else ""

    Py4GW.Console.set_window_title(title)

    yield from Routines.Yield.wait(100)
    GLOBAL_CACHE.ShMem.MarkMessageAsFinished(message.ReceiverEmail, index)
    ConsoleLog(MODULE_NAME, "SetWindowTitle message processed and finished.",
               Console.MessageType.Info, False)

# endregion
#region SetBorderless
def SetBorderless(index, message):
    GLOBAL_CACHE.ShMem.MarkMessageAsRunning(message.ReceiverEmail, index)
    sender_data = GLOBAL_CACHE.ShMem.GetAccountDataFromEmail(message.SenderEmail)
    if sender_data is None:
        GLOBAL_CACHE.ShMem.MarkMessageAsFinished(message.ReceiverEmail, index)
        return
    Py4GW.Console.set_borderless(bool(message.Params[0]))
    yield from Routines.Yield.wait(1000)
    GLOBAL_CACHE.ShMem.MarkMessageAsFinished(message.ReceiverEmail, index)
    ConsoleLog(MODULE_NAME, "SetBorderless message processed and finished.", Console.MessageType.Info, False)
# endregion
#region SetAlwaysOnTop
def SetAlwaysOnTop(index, message):
    GLOBAL_CACHE.ShMem.MarkMessageAsRunning(message.ReceiverEmail, index)
    sender_data = GLOBAL_CACHE.ShMem.GetAccountDataFromEmail(message.SenderEmail)
    if sender_data is None:
        GLOBAL_CACHE.ShMem.MarkMessageAsFinished(message.ReceiverEmail, index)
        return
    Py4GW.Console.set_always_on_top(bool(message.Params[0]))
    yield from Routines.Yield.wait(100)
    GLOBAL_CACHE.ShMem.MarkMessageAsFinished(message.ReceiverEmail, index)
    ConsoleLog(MODULE_NAME, "SetAlwaysOnTop message processed and finished.", Console.MessageType.Info, False)
# endregion
#region FlashWindow
def FlashWindow(index, message):
    GLOBAL_CACHE.ShMem.MarkMessageAsRunning(message.ReceiverEmail, index)
    sender_data = GLOBAL_CACHE.ShMem.GetAccountDataFromEmail(message.SenderEmail)
    if sender_data is None:
        GLOBAL_CACHE.ShMem.MarkMessageAsFinished(message.ReceiverEmail, index)
        return
    Py4GW.Console.flash_window()
    yield from Routines.Yield.wait(100)
    GLOBAL_CACHE.ShMem.MarkMessageAsFinished(message.ReceiverEmail, index)
    ConsoleLog(MODULE_NAME, "FlashWindow message processed and finished.", Console.MessageType.Info, False)
# endregion
#region RequestAttention
def RequestAttention(index, message):
    GLOBAL_CACHE.ShMem.MarkMessageAsRunning(message.ReceiverEmail, index)
    sender_data = GLOBAL_CACHE.ShMem.GetAccountDataFromEmail(message.SenderEmail)
    if sender_data is None:
        GLOBAL_CACHE.ShMem.MarkMessageAsFinished(message.ReceiverEmail, index)
        return
    Py4GW.Console.request_attention()
    yield from Routines.Yield.wait(100)
    GLOBAL_CACHE.ShMem.MarkMessageAsFinished(message.ReceiverEmail, index)
    ConsoleLog(MODULE_NAME, "RequestAttention message processed and finished.", Console.MessageType.Info, False)
# endregion
# region SetTransparentClickThrough
def SetTransparentClickThrough(index, message):
    GLOBAL_CACHE.ShMem.MarkMessageAsRunning(message.ReceiverEmail, index)
    sender_data = GLOBAL_CACHE.ShMem.GetAccountDataFromEmail(message.SenderEmail)
    if sender_data is None:
        GLOBAL_CACHE.ShMem.MarkMessageAsFinished(message.ReceiverEmail, index)
        return
    Py4GW.Console.transparent_click_through(bool(message.Params[0]))
    yield from Routines.Yield.wait(100)
    GLOBAL_CACHE.ShMem.MarkMessageAsFinished(message.ReceiverEmail, index)
    ConsoleLog(MODULE_NAME, "SetTransparentClickThrough message processed and finished.", Console.MessageType.Info, False)
# endregion
# region SetTransparency
def SetOpacity(index, message):
    GLOBAL_CACHE.ShMem.MarkMessageAsRunning(message.ReceiverEmail, index)
    sender_data = GLOBAL_CACHE.ShMem.GetAccountDataFromEmail(message.SenderEmail)
    if sender_data is None:
        GLOBAL_CACHE.ShMem.MarkMessageAsFinished(message.ReceiverEmail, index)
        return
    Py4GW.Console.adjust_window_opacity(int(message.Params[0]))
    yield from Routines.Yield.wait(100)
    GLOBAL_CACHE.ShMem.MarkMessageAsFinished(message.ReceiverEmail, index)
    ConsoleLog(MODULE_NAME, "SetOpacity message processed and finished.", Console.MessageType.Info, False)
#endregion

#region UseSkill
def UseSkill(index, message):
    ConsoleLog(MODULE_NAME, f"Processing UseSkill message: {message}", Console.MessageType.Info, False)
    GLOBAL_CACHE.ShMem.MarkMessageAsRunning(message.ReceiverEmail, index)
    sender_data = GLOBAL_CACHE.ShMem.GetAccountDataFromEmail(message.SenderEmail)
    if sender_data is None:
        GLOBAL_CACHE.ShMem.MarkMessageAsFinished(message.ReceiverEmail, index)
        return

    target = int(message.Params[0])
    if target == 0:
        ConsoleLog(MODULE_NAME, "Invalid target ID.", Console.MessageType.Warning)
        GLOBAL_CACHE.ShMem.MarkMessageAsFinished(message.ReceiverEmail, index)
        return
    yield from Routines.Yield.Agents.ChangeTarget(target)
    skill_id = int(message.Params[1])
    skill_slot = GLOBAL_CACHE.SkillBar.GetSlotBySkillID(skill_id)
    

    if skill_slot < 1 or skill_slot > 8:
        ConsoleLog(MODULE_NAME, "Invalid skill slot.", Console.MessageType.Warning)
        GLOBAL_CACHE.ShMem.MarkMessageAsFinished(message.ReceiverEmail, index)
        return

    SnapshotHeroAIOptions(message.ReceiverEmail)
    try:
        ConsoleLog(MODULE_NAME, f"Disable HERO AI.", Console.MessageType.Info)
        DisableHeroAIOptions(message.ReceiverEmail)
        ConsoleLog(MODULE_NAME, f"Changing target to {target}.", Console.MessageType.Info)
        yield from Routines.Yield.Agents.ChangeTarget(target)
        ConsoleLog(MODULE_NAME, f"Casting skill in slot {skill_slot}.", Console.MessageType.Info)
        yield from Routines.Yield.Skills.CastSkillSlot(slot=skill_slot, aftercast_delay=0, log=True)

        ConsoleLog(MODULE_NAME, "UseSkill message processed and finished.", Console.MessageType.Info, False)
    finally:
        RestoreHeroAISnapshot(message.ReceiverEmail)
        GLOBAL_CACHE.ShMem.MarkMessageAsFinished(message.ReceiverEmail, index)

# region UseItem (generic)
def _local_has_effect(effect_id: int) -> bool:
    if effect_id <= 0:
        return False
    try:
        pid = int(Player.GetAgentID())
        return bool(Effects.EffectExists(pid, int(effect_id)) or Effects.BuffExists(pid, int(effect_id)))
    except Exception:
        return False

def _player_is_dead() -> bool:
    try:
        fn = getattr(Player, "IsDead", None)
        if callable(fn):
            return bool(fn())
    except Exception:
        pass
    return False

def _map_is_loading() -> bool:
    try:
        for nm in ("IsLoading", "IsMapLoading", "IsLoadingMap", "IsInLoadingScreen"):
            fn = getattr(Map, nm, None)
            if callable(fn) and bool(fn()):
                return True
    except Exception:
        pass
    return False

def _inventory_ready() -> bool:
    try:
        inv = getattr(GLOBAL_CACHE, "Inventory", None)
        if inv is not None:
            fn = getattr(inv, "IsReady", None)
            if callable(fn):
                return bool(fn())
    except Exception:
        return False
    return True

def _should_block_item_use() -> bool:
    if not Routines.Checks.Map.MapValid():
        return True
    if _player_is_dead():
        return True
    if _map_is_loading():
        return True
    if not _inventory_ready():
        return True
    return False

def UseItem(index, message):
    ConsoleLog(MODULE_NAME, f"Processing UseItem message: {message}", Console.MessageType.Info, False)
    GLOBAL_CACHE.ShMem.MarkMessageAsRunning(message.ReceiverEmail, index)

    # Check if the user has opted in to team broadcasts (Pycons setting)
    # Use Player.GetAccountEmail() to match the hash used by Pycons.py
    try:
        # Get the current account's email (must match how Pycons computes the hash)
        account_email = Player.GetAccountEmail()
        # Create account-specific INI path by using email hash to avoid special chars
        import hashlib
        email_hash = hashlib.md5(account_email.encode()).hexdigest()[:8]
        ini_path = f"Widgets/Config/Pycons_{email_hash}.ini"
        
        ConsoleLog(MODULE_NAME, f"UseItem: Reading opt-in from {ini_path} (account: {account_email})", Console.MessageType.Info)
        
        ini_handler = IniHandler(ini_path)
        opt_in = ini_handler.read_bool("Pycons", "team_consume_opt_in", False)
        ConsoleLog(MODULE_NAME, f"UseItem: team_consume_opt_in setting read as: {opt_in}", Console.MessageType.Info)
        if not opt_in:
            ConsoleLog(MODULE_NAME, "UseItem: team_consume_opt_in is disabled, ignoring broadcast.", Console.MessageType.Info)
            GLOBAL_CACHE.ShMem.MarkMessageAsFinished(message.ReceiverEmail, index)
            return
    except Exception as e:
        ConsoleLog(MODULE_NAME, f"UseItem: failed to read team_consume_opt_in setting: {e}", Console.MessageType.Warning)
        GLOBAL_CACHE.ShMem.MarkMessageAsFinished(message.ReceiverEmail, index)
        return

    if _should_block_item_use():
        ConsoleLog(MODULE_NAME, "UseItem: blocked by safety checks (dead/loading/inventory not ready/map invalid).", Console.MessageType.Info, False)
        GLOBAL_CACHE.ShMem.MarkMessageAsFinished(message.ReceiverEmail, index)
        return

    if len(message.Params) < 1:
        ConsoleLog(MODULE_NAME, "UseItem: missing model_id param.", Console.MessageType.Warning)
        GLOBAL_CACHE.ShMem.MarkMessageAsFinished(message.ReceiverEmail, index)
        return

    try:
        model_id = int(message.Params[0])
    except Exception:
        ConsoleLog(MODULE_NAME, "UseItem: invalid model_id.", Console.MessageType.Warning)
        GLOBAL_CACHE.ShMem.MarkMessageAsFinished(message.ReceiverEmail, index)
        return

    repeat = 1
    if len(message.Params) > 1:
        try:
            repeat = max(1, int(message.Params[1]))
        except Exception:
            repeat = 1
    effect_id = 0
    if len(message.Params) > 2:
        try:
            effect_id = int(message.Params[2])
        except Exception:
            effect_id = 0

    count = GLOBAL_CACHE.Inventory.GetModelCount(model_id)
    if count < 1:
        ConsoleLog(MODULE_NAME, f"UseItem: no items with model_id {model_id} in inventory.", Console.MessageType.Warning)
        GLOBAL_CACHE.ShMem.MarkMessageAsFinished(message.ReceiverEmail, index)
        return
    if effect_id > 0 and _local_has_effect(effect_id):
        ConsoleLog(MODULE_NAME, f"UseItem: effect {effect_id} already active, skipping.", Console.MessageType.Info, False)
        GLOBAL_CACHE.ShMem.MarkMessageAsFinished(message.ReceiverEmail, index)
        return

    used = 0
    for _ in range(repeat):
        if effect_id > 0 and _local_has_effect(effect_id):
            ConsoleLog(MODULE_NAME, f"UseItem: effect {effect_id} active mid-loop, stopping.", Console.MessageType.Info, False)
            break
        if GLOBAL_CACHE.Inventory.GetModelCount(model_id) < 1:
            ConsoleLog(MODULE_NAME, "UseItem: out of items mid-loop, stopping.", Console.MessageType.Info)
            break

        item_id = GLOBAL_CACHE.Item.GetItemIdFromModelID(model_id)
        if not item_id:
            ConsoleLog(MODULE_NAME, f"UseItem: could not resolve item_id for model_id {model_id}.", Console.MessageType.Warning)
            break

        GLOBAL_CACHE.Inventory.UseItem(item_id)
        used += 1
        ConsoleLog(MODULE_NAME, f"UseItem: used item_id {item_id} (model {model_id}).", Console.MessageType.Info, False)

        yield from Routines.Yield.wait(150)

    ConsoleLog(MODULE_NAME, f"UseItem: finished. Requested {repeat}, actually used {used}.", Console.MessageType.Info)
    GLOBAL_CACHE.ShMem.MarkMessageAsFinished(message.ReceiverEmail, index)
# endregion

# region UseSkillFromMessage
def UseSkillCombatPrep(index, message):
    global combat_prep_first_skills_check
    global hero_ai_has_paragon_skills
    global hero_ai_has_ritualist_skills

    account_email = message.ReceiverEmail
    GLOBAL_CACHE.ShMem.MarkMessageAsRunning(account_email, index)

    # --- Paragon Shouts ---
    paragon_skills = [
        "Theres_Nothing_to_Fear",
        "Stand_Your_Ground",
    ]

    # --- Ritualist Spirits ---
    skills_to_precast = [
        SUMMON_SPIRITS_LUXON,
        SUMMON_SPIRITS_KURZICK,
    ]
    spirit_skills_to_prep = [
        "Shelter",
        "Union",
        "Earthbind",
        "Displacement",
        "Signet_of_Spirits",
        "Bloodsong",
        "Vampirism",
        "Rejuvenation",
        "Recuperation",
    ]
    skills_to_postcast = [
        ARMOR_OF_UNFEELING,
    ]
    full_ritualist_skills = skills_to_precast + spirit_skills_to_prep + skills_to_postcast

    def curr_agent_has_ritualist_skills():
        for skill in full_ritualist_skills:
            skill_id = GLOBAL_CACHE.Skill.GetID(skill)
            slot_number = GLOBAL_CACHE.SkillBar.GetSlotBySkillID(skill_id)

            if slot_number:
                return True
        return False

    def curr_agent_has_paragon_skills():
        for skill in paragon_skills:
            skill_id = GLOBAL_CACHE.Skill.GetID(skill)
            slot_number = GLOBAL_CACHE.SkillBar.GetSlotBySkillID(skill_id)

            if slot_number:
                return True
        return False

    def cast_paragon_shouts():
        global cached_data

        ConsoleLog(MODULE_NAME, "Paragon shout skills initialized", Console.MessageType.Info)

        SnapshotHeroAIOptions(account_email)
        DisableHeroAIOptions(account_email)

        # --- Cast Paragon Shouts ---
        try:
            for skill in paragon_skills:
                skill_id = GLOBAL_CACHE.Skill.GetID(skill)
                slot_number = GLOBAL_CACHE.SkillBar.GetSlotBySkillID(skill_id)

                if not skill_id or not slot_number:
                    continue

                if not cached_data.combat_handler.IsReadyToCast(slot_number):
                    continue

                yield from Routines.Yield.Skills.CastSkillID(skill_id, aftercast_delay=100)

        except Exception as e:
            ConsoleLog(MODULE_NAME, f"Error during shout casting loop: {e}", Console.MessageType.Error)
            yield from Routines.Yield.wait(500)  # optional backoff

        # --- Re-enable Hero AI ---
        RestoreHeroAISnapshot(account_email)
        yield from Routines.Yield.wait(100)

    def cast_rit_spirits():
        global cached_data

        ConsoleLog(MODULE_NAME, "Ritualist skills initialized", Console.MessageType.Info)

        # --- Disable Hero AI ---
        SnapshotHeroAIOptions(account_email)
        DisableHeroAIOptions(account_email)

        # --- Cast Ritualist Skills ---
        try:
            for skill in full_ritualist_skills:
                skill_id = GLOBAL_CACHE.Skill.GetID(skill)
                slot_number = GLOBAL_CACHE.SkillBar.GetSlotBySkillID(skill_id)

                if not skill_id or not slot_number:
                    continue

                if skill in spirit_skills_to_prep and cached_data.combat_handler.SpiritBuffExists(skill_id):
                    continue

                if not cached_data.combat_handler.IsReadyToCast(slot_number):
                    continue

                if skill in spirit_skills_to_prep or skill == SUMMON_SPIRITS_LUXON or skill == SUMMON_SPIRITS_KURZICK:
                    yield from Routines.Yield.Skills.CastSkillID(skill_id, aftercast_delay=1250)

                if skill == ARMOR_OF_UNFEELING:
                    has_any_spirits_in_range = any(
                        cached_data.combat_handler.SpiritBuffExists(GLOBAL_CACHE.Skill.GetID(spirit_skill))
                        for spirit_skill in spirit_skills_to_prep
                    )
                    if has_any_spirits_in_range:
                        yield from Routines.Yield.Skills.CastSkillID(skill_id, aftercast_delay=1250)

        except Exception as e:
            ConsoleLog(MODULE_NAME, f"Error during spirit casting loop: {e}", Console.MessageType.Error)
            yield from Routines.Yield.wait(500)  # optional backoff

        # --- Re-enable Hero AI ---
        RestoreHeroAISnapshot(account_email)
        yield from Routines.Yield.wait(100)

    cast_params = message.Params[0]

    if combat_prep_first_skills_check:
        hero_ai_has_ritualist_skills = curr_agent_has_ritualist_skills()
        hero_ai_has_paragon_skills = curr_agent_has_paragon_skills()
        combat_prep_first_skills_check = False

    if cast_params == CombatPrepSkillsType.SpiritsPrep and hero_ai_has_ritualist_skills:
        yield from cast_rit_spirits()
    elif cast_params == CombatPrepSkillsType.ShoutsPrep and hero_ai_has_paragon_skills:
        yield from cast_paragon_shouts()

    yield from Routines.Yield.wait(100)
    GLOBAL_CACHE.ShMem.MarkMessageAsFinished(message.ReceiverEmail, index)
#endregion

# region Widget handling
def PauseWidgets(index, message):
    GLOBAL_CACHE.ShMem.MarkMessageAsRunning(message.ReceiverEmail, index)
    sender_data = GLOBAL_CACHE.ShMem.GetAccountDataFromEmail(message.SenderEmail)
    if sender_data is None:
        GLOBAL_CACHE.ShMem.MarkMessageAsFinished(message.ReceiverEmail, index)
        return
    
    widget_handler = get_widget_handler()
    widget_handler.pause_widgets()
    yield from Routines.Yield.wait(100)
    GLOBAL_CACHE.ShMem.MarkMessageAsFinished(message.ReceiverEmail, index)
    ConsoleLog(MODULE_NAME, "PauseWidgets message processed and finished.", Console.MessageType.Info, False)

def ResumeWidgets(index, message):
    GLOBAL_CACHE.ShMem.MarkMessageAsRunning(message.ReceiverEmail, index)
    sender_data = GLOBAL_CACHE.ShMem.GetAccountDataFromEmail(message.SenderEmail)
    if sender_data is None:
        GLOBAL_CACHE.ShMem.MarkMessageAsFinished(message.ReceiverEmail, index)
        return
    
    widget_handler = get_widget_handler()
    yield from Routines.Yield.wait(100)
    GLOBAL_CACHE.ShMem.MarkMessageAsFinished(message.ReceiverEmail, index)
    ConsoleLog(MODULE_NAME, "ResumeWidgets message processed and finished.", Console.MessageType.Info, False)
# endregion

#region SwitchCharacter
def SwitchCharacter(index, message):
    GLOBAL_CACHE.ShMem.MarkMessageAsRunning(message.ReceiverEmail, index)
    sender_data = GLOBAL_CACHE.ShMem.GetAccountDataFromEmail(message.SenderEmail)
    if sender_data is None:
        GLOBAL_CACHE.ShMem.MarkMessageAsFinished(message.ReceiverEmail, index)
        return
    

    extra = tuple(GLOBAL_CACHE.ShMem._c_wchar_array_to_str(arr) for arr in message.ExtraData)
    character_name = extra[0] if extra else ""
    
    if character_name and character_name != Player.GetName():
        yield from Routines.Yield.RerollCharacter.Reroll(character_name)  
    
    GLOBAL_CACHE.ShMem.MarkMessageAsFinished(message.ReceiverEmail, index)
    ConsoleLog(MODULE_NAME, "SwitchCharacter message processed and finished.", Console.MessageType.Info, False)    
# endregion

#region LoadSkillTemplate
def LoadSkillTemplate(index, message):
    GLOBAL_CACHE.ShMem.MarkMessageAsRunning(message.ReceiverEmail, index)
    sender_data = GLOBAL_CACHE.ShMem.GetAccountDataFromEmail(message.SenderEmail)
    
    if sender_data is None:
        GLOBAL_CACHE.ShMem.MarkMessageAsFinished(message.ReceiverEmail, index)
        return
    
    if Map.IsOutpost():
        extra = tuple(GLOBAL_CACHE.ShMem._c_wchar_array_to_str(arr) for arr in message.ExtraData)
        template = extra[0] if extra else ""
            
        if template:
            GLOBAL_CACHE.SkillBar.LoadSkillTemplate(template)
            yield from Routines.Yield.wait(100)
    
    GLOBAL_CACHE.ShMem.MarkMessageAsFinished(message.ReceiverEmail, index)
    ConsoleLog(MODULE_NAME, "LoadSkillTemplate message processed and finished.", Console.MessageType.Info, False)
# endregion

#region SkipCutscene
def SkipCutscene(index, message):
    GLOBAL_CACHE.ShMem.MarkMessageAsRunning(message.ReceiverEmail, index)
    sender_data = GLOBAL_CACHE.ShMem.GetAccountDataFromEmail(message.SenderEmail)
    
    if sender_data is None:
        GLOBAL_CACHE.ShMem.MarkMessageAsFinished(message.ReceiverEmail, index)
        return
    
    if Map.IsInCinematic():
        Map.SkipCinematic()
        yield from Routines.Yield.wait(100)
    
    GLOBAL_CACHE.ShMem.MarkMessageAsFinished(message.ReceiverEmail, index)
    ConsoleLog(MODULE_NAME, "SkipCutscene message processed and finished.", Console.MessageType.Info, False)
# endregion

#region TravelToGuildHall
def TravelToGuildHall(index, message):
    GLOBAL_CACHE.ShMem.MarkMessageAsRunning(message.ReceiverEmail, index)
    sender_data = GLOBAL_CACHE.ShMem.GetAccountDataFromEmail(message.SenderEmail)
    if sender_data is None:
        GLOBAL_CACHE.ShMem.MarkMessageAsFinished(message.ReceiverEmail, index)
        return
    
    if Map.IsGuildHall():
        GLOBAL_CACHE.ShMem.MarkMessageAsFinished(message.ReceiverEmail, index)
        return
    
    Map.TravelGH()
    yield from Routines.Yield.wait(100)
    GLOBAL_CACHE.ShMem.MarkMessageAsFinished(message.ReceiverEmail, index)
    ConsoleLog(MODULE_NAME, "TravelToGuildHall message processed and finished.", Console.MessageType.Info, False)
# endregion

# region ProcessMessages
def ProcessMessages():
    account_email = Player.GetAccountEmail()
    index, message = GLOBAL_CACHE.ShMem.GetNextMessage(account_email)

    if index == -1 or message is None:
        return

    match message.Command:
        case SharedCommandType.TravelToMap:
            GLOBAL_CACHE.Coroutines.append(TravelToMap(index, message))
        case SharedCommandType.InviteToParty:
            GLOBAL_CACHE.Coroutines.append(InviteToParty(index, message))
        case SharedCommandType.LeaveParty:
            GLOBAL_CACHE.Coroutines.append(LeaveParty(index, message))
        case SharedCommandType.InteractWithTarget:
            GLOBAL_CACHE.Coroutines.append(InteractWithTarget(index, message))
        case SharedCommandType.TakeDialogWithTarget:
            GLOBAL_CACHE.Coroutines.append(TakeDialogWithTarget(index, message))
        case SharedCommandType.SendDialogToTarget:
            GLOBAL_CACHE.Coroutines.append(SendDialogToTarget(index, message))
        case SharedCommandType.SendDialog:
            GLOBAL_CACHE.Coroutines.append(SendDialog(index, message))
        case SharedCommandType.GetBlessing:
            pass
        case SharedCommandType.OpenChest:
            GLOBAL_CACHE.Coroutines.append(OpenChest(index, message))
            pass
        case SharedCommandType.PickUpLoot:
            GLOBAL_CACHE.Coroutines.append(PickUpLoot(index, message))
        case SharedCommandType.UseSkill:
            GLOBAL_CACHE.Coroutines.append(UseSkill(index, message))
        case SharedCommandType.Resign:
            GLOBAL_CACHE.Coroutines.append(Resign(index, message))
        case SharedCommandType.PixelStack:
            GLOBAL_CACHE.Coroutines.append(PixelStack(index, message))
        case SharedCommandType.BruteForceUnstuck:
            GLOBAL_CACHE.Coroutines.append(BruteForceUnstuck(index, message))
        case SharedCommandType.PCon:
            GLOBAL_CACHE.Coroutines.append(UsePcon(index, message))
        case SharedCommandType.IdentifyItems:
            pass
        case SharedCommandType.SalvageItems:
            pass
        case SharedCommandType.MerchantItems:
            pass
        case SharedCommandType.MerchantMaterials:
            pass
        case SharedCommandType.DisableHeroAI:
            GLOBAL_CACHE.Coroutines.append(MessageDisableHeroAI(index, message))
        case SharedCommandType.EnableHeroAI:
            GLOBAL_CACHE.Coroutines.append(MessageEnableHeroAI(index, message))
        case SharedCommandType.PressKey:
            GLOBAL_CACHE.Coroutines.append(PressKey(index, message))
        case SharedCommandType.DonateToGuild:
            GLOBAL_CACHE.Coroutines.append(DonateToGuild(index, message))
        case SharedCommandType.SetWindowGeometry:
            GLOBAL_CACHE.Coroutines.append(SetWindowGeometry(index, message))
        case SharedCommandType.SetWindowActive:
            GLOBAL_CACHE.Coroutines.append(SetWindowActive(index, message))
        case SharedCommandType.SetWindowTitle:
            GLOBAL_CACHE.Coroutines.append(SetWindowTitle(index, message))
        case SharedCommandType.SetBorderless:
            GLOBAL_CACHE.Coroutines.append(SetBorderless(index, message))
        case SharedCommandType.SetAlwaysOnTop:
            GLOBAL_CACHE.Coroutines.append(SetAlwaysOnTop(index, message))
        case SharedCommandType.UseItem:
            GLOBAL_CACHE.Coroutines.append(UseItem(index, message))
        case SharedCommandType.FlashWindow:
            GLOBAL_CACHE.Coroutines.append(FlashWindow(index, message))
        case SharedCommandType.RequestAttention:
            GLOBAL_CACHE.Coroutines.append(RequestAttention(index, message))
        case SharedCommandType.SetTransparentClickThrough:
            GLOBAL_CACHE.Coroutines.append(SetTransparentClickThrough(index, message))
        case SharedCommandType.SetOpacity:
            GLOBAL_CACHE.Coroutines.append(SetOpacity(index, message))
        case SharedCommandType.PauseWidgets:
            GLOBAL_CACHE.Coroutines.append(PauseWidgets(index, message))
        case SharedCommandType.ResumeWidgets:
            GLOBAL_CACHE.Coroutines.append(ResumeWidgets(index, message))
        case SharedCommandType.SwitchCharacter:
            GLOBAL_CACHE.Coroutines.append(SwitchCharacter(index, message))
        case SharedCommandType.LoadSkillTemplate:
            GLOBAL_CACHE.Coroutines.append(LoadSkillTemplate(index, message))
        case SharedCommandType.SkipCutscene:
            GLOBAL_CACHE.Coroutines.append(SkipCutscene(index, message))
        case SharedCommandType.TravelToGuildHall:
            GLOBAL_CACHE.Coroutines.append(TravelToGuildHall(index, message))
        case SharedCommandType.UseSkillCombatPrep:
            GLOBAL_CACHE.Coroutines.append(UseSkillCombatPrep(index, message))
        case SharedCommandType.LootEx:
            # privately Handled Command, by frenkey
            pass
        case SharedCommandType.CustomBehaviors:
            # privately Handled Command, used in CustomBehaviors widget
            pass
        case _:
            GLOBAL_CACHE.ShMem.MarkMessageAsFinished(account_email, index)
            pass


# endregion


def main():
    ProcessMessages()


if __name__ == "__main__":
    main()
