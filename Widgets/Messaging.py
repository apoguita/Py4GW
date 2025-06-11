
from Py4GWCoreLib import GLOBAL_CACHE, PyImGui, SharedCommandType, Routines, ConsoleLog, Console, UIManager
from Py4GWCoreLib import LootConfig, Range, ActionQueueManager
from datetime import datetime, timezone
import time


MODULE_NAME = "Messaging"

width, height = 0,0

class HeroAIoptions:
    def __init__(self):
        self.Following = False
        self.Avoidance = False
        self.Looting = False
        self.Targeting = False
        self.Combat = False
        self.Skills: list[bool] = [False] * 8
        
hero_ai_snapshot = HeroAIoptions()

#region ImGui
def configure():
    DrawWindow()

def DrawWindow():
    if PyImGui.begin(MODULE_NAME):
        account_email = GLOBAL_CACHE.Player.GetAccountEmail()
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
            
            command:SharedCommandType = message.Command
            params:tuple[float] = message.Params
            active = message.Active
            running = message.Running
            timestamp = message.Timestamp
            PyImGui.text(f"Message {index}:")
            PyImGui.text(f"Sender: {sender}")
            PyImGui.text(f"Receiver: {receiver}")
            PyImGui.text(f"Command: {SharedCommandType(command).name}")
            PyImGui.text(f"Params: {', '.join(map(str, params))}")
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
                
                
                command:SharedCommandType = message.Command
                params:tuple[float] = message.Params
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
    
#endregion
#region HeroAI Snapshot
def SnapshotHeroAIOptions(acocunt_email):
    global hero_ai_snapshot
    hero_ai_options = GLOBAL_CACHE.ShMem.GetHeroAIOptions(acocunt_email)
    if hero_ai_options is None:
        return
    
    hero_ai_snapshot.Following = hero_ai_options.Following
    hero_ai_snapshot.Avoidance = hero_ai_options.Avoidance
    hero_ai_snapshot.Looting = hero_ai_options.Looting
    hero_ai_snapshot.Targeting = hero_ai_options.Targeting
    hero_ai_snapshot.Combat = hero_ai_options.Combat
    yield
    
def RestoreHeroAISnapshot(acocunt_email):
    global hero_ai_snapshot
    hero_ai_options = GLOBAL_CACHE.ShMem.GetHeroAIOptions(acocunt_email)
    if hero_ai_options is None:
        return
    
    hero_ai_options.Following = hero_ai_snapshot.Following
    hero_ai_options.Avoidance = hero_ai_snapshot.Avoidance
    hero_ai_options.Looting = hero_ai_snapshot.Looting
    hero_ai_options.Targeting = hero_ai_snapshot.Targeting
    hero_ai_options.Combat = hero_ai_snapshot.Combat
    yield


def DisableHeroAIOptions(acocunt_email):
    hero_ai_options = GLOBAL_CACHE.ShMem.GetHeroAIOptions(acocunt_email)
    if hero_ai_options is None:
        return
    
    hero_ai_options.Following = False
    hero_ai_options.Avoidance = False
    hero_ai_options.Looting = False
    hero_ai_options.Targeting = False
    hero_ai_options.Combat = False
    yield

#endregion

#region InviteToParty

def InviteToParty(index, message):
    #ConsoleLog(MODULE_NAME, f"Processing InviteToParty message: {message}", Console.MessageType.Info)
    GLOBAL_CACHE.ShMem.MarkMessageAsRunning(message.ReceiverEmail, index)
    sender_data = GLOBAL_CACHE.ShMem.GetAccountDataFromEmail(message.SenderEmail)
    if sender_data is None:
        GLOBAL_CACHE.ShMem.MarkMessageAsFinished(message.ReceiverEmail, index)
        return
    yield from Routines.Yield.wait(100)
    GLOBAL_CACHE.Party.Players.InvitePlayer(sender_data.CharacterName)
    yield from Routines.Yield.wait(100)
    GLOBAL_CACHE.ShMem.MarkMessageAsFinished(message.ReceiverEmail, index)
    ConsoleLog(MODULE_NAME, f"InviteToParty message processed and finished.", Console.MessageType.Info)
    
#endregion
#region TravelToMap
    
def TravelToMap(index, message):
    #ConsoleLog(MODULE_NAME, f"Processing TravelToMap message: {message}", Console.MessageType.Info)
    GLOBAL_CACHE.ShMem.MarkMessageAsRunning(message.ReceiverEmail, index)
    sender_data = GLOBAL_CACHE.ShMem.GetAccountDataFromEmail(message.SenderEmail)
    if sender_data is None:
        GLOBAL_CACHE.ShMem.MarkMessageAsFinished(message.ReceiverEmail, index)
        return
    map_id = sender_data.MapID
    map_region = sender_data.MapRegion
    map_district = sender_data.MapDistrict

    yield from Routines.Yield.Map.TravelToRegion(map_id, map_region, map_district, language=0, log=True)
    yield from Routines.Yield.wait(100)
    GLOBAL_CACHE.ShMem.MarkMessageAsFinished(message.ReceiverEmail, index)
    ConsoleLog(MODULE_NAME, f"TravelToMap message processed and finished.", Console.MessageType.Info)
    
#endregion
#region Resign
    
def Resign(index, message):
    #ConsoleLog(MODULE_NAME, f"Processing Resign message: {message}", Console.MessageType.Info)
    GLOBAL_CACHE.ShMem.MarkMessageAsRunning(message.ReceiverEmail, index)
    GLOBAL_CACHE.Player.SendChatCommand("resign")
    yield from Routines.Yield.wait(100)
    GLOBAL_CACHE.ShMem.MarkMessageAsFinished(message.ReceiverEmail, index)
    ConsoleLog(MODULE_NAME, f"Resign message processed and finished.", Console.MessageType.Info)
    
#endregion
#region PixelStack
def PixelStack(index, message):
    ConsoleLog(MODULE_NAME, f"Processing PixelStack message: {message}", Console.MessageType.Info)
    GLOBAL_CACHE.ShMem.MarkMessageAsRunning(message.ReceiverEmail, index)
    sender_data = GLOBAL_CACHE.ShMem.GetAccountDataFromEmail(message.SenderEmail)
    if sender_data is None:
        GLOBAL_CACHE.ShMem.MarkMessageAsFinished(message.ReceiverEmail, index)
        return
    yield from SnapshotHeroAIOptions(message.ReceiverEmail)
    yield from DisableHeroAIOptions(message.ReceiverEmail)
    yield from Routines.Yield.wait(100)
    yield from Routines.Yield.Movement.FollowPath([(message.Params[0], message.Params[1])], tolerance=10)
    yield from Routines.Yield.wait(100)
    yield from RestoreHeroAISnapshot(message.ReceiverEmail)
    GLOBAL_CACHE.ShMem.MarkMessageAsFinished(message.ReceiverEmail, index)
    ConsoleLog(MODULE_NAME, f"PixelStack message processed and finished.", Console.MessageType.Info)
    
#endregion

#region InteractWithTarget
    
def InteractWithTarget(index, message):
    ConsoleLog(MODULE_NAME, f"Processing InteractWithTarget message: {message}", Console.MessageType.Info)
    GLOBAL_CACHE.ShMem.MarkMessageAsRunning(message.ReceiverEmail, index)
    sender_data = GLOBAL_CACHE.ShMem.GetAccountDataFromEmail(message.SenderEmail)
    if sender_data is None:
        return
    target = int(message.Params[0])
    if target==0:
        ConsoleLog(MODULE_NAME, "Invalid target ID.", Console.MessageType.Warning)
        GLOBAL_CACHE.ShMem.MarkMessageAsFinished(message.ReceiverEmail, index)
        return
    
    yield from SnapshotHeroAIOptions(message.ReceiverEmail)
    yield from DisableHeroAIOptions(message.ReceiverEmail)
    yield from Routines.Yield.wait(100)
    x,y = GLOBAL_CACHE.Agent.GetXY(target)
    yield from Routines.Yield.Movement.FollowPath([(x, y)])
    yield from Routines.Yield.wait(100)
    yield from Routines.Yield.Player.InteractAgent(target)
    yield from RestoreHeroAISnapshot(message.ReceiverEmail)
    GLOBAL_CACHE.ShMem.MarkMessageAsFinished(message.ReceiverEmail, index)
    ConsoleLog(MODULE_NAME, f"InteractWithTarget message processed and finished.", Console.MessageType.Info)
    
#endregion
#region TakeDialogWithTarget
    
def TakeDialogWithTarget(index, message):
    ConsoleLog(MODULE_NAME, f"Processing TakeDialogWithTarget message: {message}", Console.MessageType.Info)
    GLOBAL_CACHE.ShMem.MarkMessageAsRunning(message.ReceiverEmail, index)
    sender_data = GLOBAL_CACHE.ShMem.GetAccountDataFromEmail(message.SenderEmail)
    if sender_data is None:
        return
    target = int(message.Params[0])
    if target==0:
        ConsoleLog(MODULE_NAME, "Invalid target ID.", Console.MessageType.Warning)
        GLOBAL_CACHE.ShMem.MarkMessageAsFinished(message.ReceiverEmail, index)
        return
    
    yield from SnapshotHeroAIOptions(message.ReceiverEmail)
    yield from DisableHeroAIOptions(message.ReceiverEmail)
    yield from Routines.Yield.wait(100)
    x,y = GLOBAL_CACHE.Agent.GetXY(target)
    yield from Routines.Yield.Movement.FollowPath([(x, y)])
    yield from Routines.Yield.wait(100)
    yield from Routines.Yield.Player.InteractAgent(target)
    yield from Routines.Yield.wait(500)
    if UIManager.IsNPCDialogVisible():
        UIManager.ClickDialogButton(message.Params[1])
        yield from Routines.Yield.wait(200)
    yield from RestoreHeroAISnapshot(message.ReceiverEmail)
    GLOBAL_CACHE.ShMem.MarkMessageAsFinished(message.ReceiverEmail, index)
    ConsoleLog(MODULE_NAME, f"TakeDialogWithTarget message processed and finished.", Console.MessageType.Info)
    
def GetBlessing(index, message):
    GLOBAL_CACHE.ShMem.MarkMessageAsRunning(message.ReceiverEmail, index)
    sender_data = GLOBAL_CACHE.ShMem.GetAccountDataFromEmail(message.SenderEmail)
    if sender_data is None:
        return
    target = int(message.Params[0])
    if target==0:
        ConsoleLog(MODULE_NAME, "Invalid target ID.", Console.MessageType.Warning)
        GLOBAL_CACHE.ShMem.MarkMessageAsFinished(message.ReceiverEmail, index)
        return
    
    yield from SnapshotHeroAIOptions(message.ReceiverEmail)
    yield from DisableHeroAIOptions(message.ReceiverEmail)
    yield from Routines.Yield.wait(100)
    x,y = GLOBAL_CACHE.Agent.GetXY(target)
    yield from Routines.Yield.Movement.FollowPath([(x, y)])
    yield from Routines.Yield.wait(100)
    yield from Routines.Yield.Player.InteractAgent(target)
    yield from Routines.Yield.wait(500)
    if UIManager.IsNPCDialogVisible():
        UIManager.ClickDialogButton(message.Params[1])
        yield from Routines.Yield.wait(200)
    yield from RestoreHeroAISnapshot(message.ReceiverEmail)
    GLOBAL_CACHE.ShMem.MarkMessageAsFinished(message.ReceiverEmail, index)
    ConsoleLog(MODULE_NAME, f"GetBlessing message processed and finished.", Console.MessageType.Info)
     
    
#endregion
#region UsePcon
  
def UsePcon(index, message):
    ConsoleLog(MODULE_NAME, f"Processing UsePcon message: {message}", Console.MessageType.Info)
    GLOBAL_CACHE.ShMem.MarkMessageAsRunning(message.ReceiverEmail, index)

    pcon_model_id = int(message.Params[0])
    pcon_skill_id = int(message.Params[1])
    pcon_model_id2 = int(message.Params[2])
    pcon_skill_id2 = int(message.Params[3])

    # Halt if any of the effects is already active
    if GLOBAL_CACHE.ShMem.HasEffect(message.ReceiverEmail, pcon_skill_id) or \
       GLOBAL_CACHE.ShMem.HasEffect(message.ReceiverEmail, pcon_skill_id2):
        #ConsoleLog(MODULE_NAME, "Player already has the effect of one of the PCon skills.", Console.MessageType.Warning)
        GLOBAL_CACHE.ShMem.MarkMessageAsFinished(message.ReceiverEmail, index)
        return

    # Check inventory to determine which PCon to use
    if GLOBAL_CACHE.Inventory.GetModelCount(pcon_model_id) > 0:
        pcon_model_to_use = pcon_model_id
    elif GLOBAL_CACHE.Inventory.GetModelCount(pcon_model_id2) > 0:
        pcon_model_to_use = pcon_model_id2
    else:
        #ConsoleLog(MODULE_NAME, "Player does not have any of the required PCons in inventory.", Console.MessageType.Warning)
        GLOBAL_CACHE.ShMem.MarkMessageAsFinished(message.ReceiverEmail, index)
        return

    item_id = GLOBAL_CACHE.Item.GetItemIdFromModelID(pcon_model_to_use)
    if item_id == 0:
        #ConsoleLog(MODULE_NAME, f"Could not find item ID for PCon model {pcon_model_to_use}.", Console.MessageType.Error)
        GLOBAL_CACHE.ShMem.MarkMessageAsFinished(message.ReceiverEmail, index)
        return

    GLOBAL_CACHE.Inventory.UseItem(item_id)
    ConsoleLog(MODULE_NAME, f"Using PCon model {pcon_model_to_use} with item_id {item_id}.", Console.MessageType.Info)
    yield from Routines.Yield.wait(100)
    GLOBAL_CACHE.ShMem.MarkMessageAsFinished(message.ReceiverEmail, index)
    #ConsoleLog(MODULE_NAME, "UsePcon message processed and finished.", Console.MessageType.Info)
#endregion

#region PickUpLoot
def PickUpLoot(index, message):
    def _exit_if_not_map_valid():
        if not Routines.Checks.Map.MapValid():
            yield from RestoreHeroAISnapshot(message.ReceiverEmail)
            GLOBAL_CACHE.ShMem.MarkMessageAsFinished(message.ReceiverEmail, index)
            ActionQueueManager().ResetAllQueues()
            return True  # Signal that we must exit
        
        if GLOBAL_CACHE.Inventory.GetFreeSlotCount() < 1:
            ConsoleLog(MODULE_NAME, "No free slots in inventory, halting.", Console.MessageType.Error)
            yield from RestoreHeroAISnapshot(message.ReceiverEmail)
            GLOBAL_CACHE.ShMem.MarkMessageAsFinished(message.ReceiverEmail, index)
            ActionQueueManager().ResetAllQueues()
            return True
        
        return False
    
    def _GetBaseTimestamp():
        SHMEM_ZERO_EPOCH = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0).timestamp()
        return int((time.time() - SHMEM_ZERO_EPOCH) * 1000)

    
    
    GLOBAL_CACHE.ShMem.MarkMessageAsRunning(message.ReceiverEmail, index)
    
    loot_array = LootConfig().GetfilteredLootArray(Range.Earshot.value, multibox_loot= True)
    if len(loot_array) == 0:
        GLOBAL_CACHE.ShMem.MarkMessageAsFinished(message.ReceiverEmail, index)
        return
    
    ConsoleLog(MODULE_NAME, f"Starting PickUpLoot routine", Console.MessageType.Info)

    yield from SnapshotHeroAIOptions(message.ReceiverEmail)
    yield from DisableHeroAIOptions(message.ReceiverEmail)
    yield from Routines.Yield.wait(100)
    while True:
        loot_array = LootConfig().GetfilteredLootArray(Range.Earshot.value, multibox_loot= True)
        if len(loot_array) == 0:
            break 
        item_id = loot_array.pop(0)
        if item_id is None or item_id == 0:
            continue
        
        if (yield from _exit_if_not_map_valid()):
            LootConfig().AddItemIDToBlacklist(item_id)
            ConsoleLog("PickUp Loot", "Map is not valid, halting.", Console.MessageType.Warning)
            yield from RestoreHeroAISnapshot(message.ReceiverEmail)
            GLOBAL_CACHE.ShMem.MarkMessageAsFinished(message.ReceiverEmail, index)
            ActionQueueManager().ResetAllQueues()
            return
        
        if not GLOBAL_CACHE.Agent.IsValid(item_id):
            yield from Routines.Yield.wait(100)
            continue
        
        pos = GLOBAL_CACHE.Agent.GetXY(item_id)
        follow_success = yield from Routines.Yield.Movement.FollowPath([pos])
        if not follow_success:
            LootConfig().AddItemIDToBlacklist(item_id)
            ConsoleLog("PickUp Loot", "Failed to follow path to loot item, halting.", Console.MessageType.Warning)
            yield from RestoreHeroAISnapshot(message.ReceiverEmail)
            GLOBAL_CACHE.ShMem.MarkMessageAsFinished(message.ReceiverEmail, index)
            ActionQueueManager().ResetAllQueues()
            return

        
        yield from Routines.Yield.wait(100)
        if (yield from _exit_if_not_map_valid()):
            return
        yield from Routines.Yield.Player.InteractAgent(item_id)
        yield from Routines.Yield.wait(100)
        start_time =  _GetBaseTimestamp()
        timeout = 3000
        while True:
            current_time = _GetBaseTimestamp()
            
            delta = current_time - start_time
            if delta > timeout:
                LootConfig().AddItemIDToBlacklist(item_id)
                ConsoleLog("PickUp Loot", "Timeout reached while picking up loot, halting.", Console.MessageType.Warning)
                yield from RestoreHeroAISnapshot(message.ReceiverEmail)
                GLOBAL_CACHE.ShMem.MarkMessageAsFinished(message.ReceiverEmail, index)
                ActionQueueManager().ResetAllQueues()
                return
            
            if (yield from _exit_if_not_map_valid()):
                LootConfig().AddItemIDToBlacklist(item_id)
                ConsoleLog("PickUp Loot", "Map is not valid, halting.", Console.MessageType.Warning)
                yield from RestoreHeroAISnapshot(message.ReceiverEmail)
                GLOBAL_CACHE.ShMem.MarkMessageAsFinished(message.ReceiverEmail, index)
                ActionQueueManager().ResetAllQueues()
                return
            
            loot_array = LootConfig().GetfilteredLootArray(Range.Earshot.value, multibox_loot=True)
            if item_id not in loot_array or len(loot_array) == 0:
                yield from Routines.Yield.wait(100)
                break
            yield from Routines.Yield.wait(100)


    yield from RestoreHeroAISnapshot(message.ReceiverEmail)
    GLOBAL_CACHE.ShMem.MarkMessageAsFinished(message.ReceiverEmail, index)
    ConsoleLog(MODULE_NAME, "PickUpLoot routine finished.", Console.MessageType.Info)


#region ProcessMessages
    
def ProcessMessages():
    account_email = GLOBAL_CACHE.Player.GetAccountEmail()
    index, message = GLOBAL_CACHE.ShMem.GetNextMessage(account_email)
    
    if index == -1 or message is None:
        return
    
    match message.Command:
        case SharedCommandType.TravelToMap:
            GLOBAL_CACHE.Coroutines.append(TravelToMap(index, message))
        case SharedCommandType.InviteToParty:
            GLOBAL_CACHE.Coroutines.append(InviteToParty(index, message))
        case SharedCommandType.InteractWithTarget:
            GLOBAL_CACHE.Coroutines.append(InteractWithTarget(index, message))
        case SharedCommandType.TakeDialogWithTarget:
            GLOBAL_CACHE.Coroutines.append(TakeDialogWithTarget(index, message))
        case SharedCommandType.GetBlessing:
            pass
        case SharedCommandType.OpenChest:
            pass
        case SharedCommandType.PickUpLoot:
            GLOBAL_CACHE.Coroutines.append(PickUpLoot(index, message))
        case SharedCommandType.UseSkill:
            pass
        case SharedCommandType.Resign:
            GLOBAL_CACHE.Coroutines.append(Resign(index, message))
        case SharedCommandType.PixelStack:
            GLOBAL_CACHE.Coroutines.append(PixelStack(index, message))
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
        case SharedCommandType.LootEx:
            #privately Handled Command, by Frenkey
            pass
        case _:
            GLOBAL_CACHE.ShMem.MarkMessageAsFinished(account_email, index)
            pass
#endregion       
    
def main():
    ProcessMessages()
    
    
    
if __name__ == "__main__":
    main()
