import Py4GW

@staticmethod
def ConsoleLog(sender, message, message_type:int=0 , log: bool = True):
    """Logs a message with an optional message type."""
    if log:
        if message_type == 0:
            Py4GW.Console.Log(sender, message, Py4GW.Console.MessageType.Info)
        elif message_type == 1:
            Py4GW.Console.Log(sender, message, Py4GW.Console.MessageType.Warning)
        elif message_type == 2:
            Py4GW.Console.Log(sender, message, Py4GW.Console.MessageType.Error)
        elif message_type == 3:
            Py4GW.Console.Log(sender, message, Py4GW.Console.MessageType.Debug)
        elif message_type == 4:
            Py4GW.Console.Log(sender, message, Py4GW.Console.MessageType.Success)
        elif message_type == 5:
            Py4GW.Console.Log(sender, message, Py4GW.Console.MessageType.Performance)
        elif message_type == 6:
            Py4GW.Console.Log(sender, message, Py4GW.Console.MessageType.Notice)
        else:
            Py4GW.Console.Log(sender, message, Py4GW.Console.MessageType.Info)

Console = Py4GW.Console