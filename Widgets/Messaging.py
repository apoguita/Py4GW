
from Py4GWCoreLib import GLOBAL_CACHE, PyImGui, SharedCommandType, Routines, ConsoleLog, Console

MODULE_NAME = "Messaging"

width, height = 0,0

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
            pass
        case SharedCommandType.TakeDialogWithTarget:
            pass
        case SharedCommandType.GetBlessing:
            pass
        case SharedCommandType.OpenChest:
            pass
        case SharedCommandType.PickUpLoot:
            pass
        case SharedCommandType.UseSkill:
            pass
        case _:
            GLOBAL_CACHE.ShMem.MarkMessageAsFinished(account_email, index)
            pass
    
def main():
    ProcessMessages()
    
    
    
if __name__ == "__main__":
    main()
