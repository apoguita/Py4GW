
from Py4GWCoreLib import GLOBAL_CACHE, PyImGui, SharedCommandType, Routines, ConsoleLog, Console, UIManager

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


def InviteToParty(index, message):
    ConsoleLog(MODULE_NAME, f"Processing InviteToParty message: {message}", Console.MessageType.Info)
    GLOBAL_CACHE.ShMem.MarkMessageAsRunning(message.ReceiverEmail, index)
    sender_data = GLOBAL_CACHE.ShMem.GetAccountDataFromEmail(message.SenderEmail)
    if sender_data is None:
        return
    yield from Routines.Yield.wait(100)
    GLOBAL_CACHE.Party.Players.InvitePlayer(sender_data.CharacterName)
    yield from Routines.Yield.wait(100)
    GLOBAL_CACHE.ShMem.MarkMessageAsFinished(message.ReceiverEmail, index)
    ConsoleLog(MODULE_NAME, f"InviteToParty message processed and finished.", Console.MessageType.Info)
    
def TravelToMap(index, message):
    ConsoleLog(MODULE_NAME, f"Processing TravelToMap message: {message}", Console.MessageType.Info)
    GLOBAL_CACHE.ShMem.MarkMessageAsRunning(message.ReceiverEmail, index)
    sender_data = GLOBAL_CACHE.ShMem.GetAccountDataFromEmail(message.SenderEmail)
    if sender_data is None:
        return
    map_id = sender_data.MapID
    map_region = sender_data.MapRegion
    map_district = sender_data.MapDistrict

    yield from Routines.Yield.Map.TravelToRegion(map_id, map_region, map_district, laguage=0, log=True)
    yield from Routines.Yield.wait(100)
    GLOBAL_CACHE.ShMem.MarkMessageAsFinished(message.ReceiverEmail, index)
    ConsoleLog(MODULE_NAME, f"TravelToMap message processed and finished.", Console.MessageType.Info)
    
def Resign(index, message):
    ConsoleLog(MODULE_NAME, f"Processing Resign message: {message}", Console.MessageType.Info)
    GLOBAL_CACHE.ShMem.MarkMessageAsRunning(message.ReceiverEmail, index)
    GLOBAL_CACHE.Player.SendChatCommand("resign")
    yield from Routines.Yield.wait(100)
    GLOBAL_CACHE.ShMem.MarkMessageAsFinished(message.ReceiverEmail, index)
    ConsoleLog(MODULE_NAME, f"Resign message processed and finished.", Console.MessageType.Info)
    
def PixelStack(index, message):
    ConsoleLog(MODULE_NAME, f"Processing PixelStack message: {message}", Console.MessageType.Info)
    GLOBAL_CACHE.ShMem.MarkMessageAsRunning(message.ReceiverEmail, index)
    sender_data = GLOBAL_CACHE.ShMem.GetAccountDataFromEmail(message.SenderEmail)
    if sender_data is None:
        return
    yield from SnapshotHeroAIOptions(message.ReceiverEmail)
    yield from DisableHeroAIOptions(message.ReceiverEmail)
    yield from Routines.Yield.wait(100)
    yield from Routines.Yield.Movement.FollowPath([(message.Params[0], message.Params[1])], tolerance=10)
    yield from Routines.Yield.wait(100)
    yield from RestoreHeroAISnapshot(message.ReceiverEmail)
    GLOBAL_CACHE.ShMem.MarkMessageAsFinished(message.ReceiverEmail, index)
    ConsoleLog(MODULE_NAME, f"PixelStack message processed and finished.", Console.MessageType.Info)
    
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
    
def TakeDialogWithTarget(index, message):
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
    yield from Routines.Yield.wait(500)
    if UIManager.IsNPCDialogVisible():
        UIManager.ClickDialogButton(message.Params[1])
        yield from Routines.Yield.wait(200)
    yield from RestoreHeroAISnapshot(message.ReceiverEmail)
    GLOBAL_CACHE.ShMem.MarkMessageAsFinished(message.ReceiverEmail, index)
    ConsoleLog(MODULE_NAME, f"InteractWithTarget message processed and finished.", Console.MessageType.Info)
    
    
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
            pass
        case SharedCommandType.UseSkill:
            pass
        case SharedCommandType.Resign:
            GLOBAL_CACHE.Coroutines.append(Resign(index, message))
        case SharedCommandType.PixelStack:
            GLOBAL_CACHE.Coroutines.append(PixelStack(index, message))
        case SharedCommandType.PCon:
            pass
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
        
    
def main():
    ProcessMessages()
    
    
    
if __name__ == "__main__":
    main()
