from Py4GWCoreLib import *
from Py4GWCoreLib import Player

module_name = "Faction Deposit UI"

# Faction enum values (adjust if yours differ)
LUXON_ENUM   = 1
KURZICK_ENUM = 2
CHUNK         = 5000

def get_luxon_unspent():
    return Player.GetLuxonData()[0]

def get_kurzick_unspent():
    return Player.GetKurzickData()[0]

def _do_deposit(faction_enum, chunks):
    for _ in range(chunks):
        Player.DepositFaction(faction_enum)

def deposit_5000_luxon():
    unspent = get_luxon_unspent()
    if unspent < CHUNK:
        Py4GW.Console.Log(module_name,
            "Not enough Luxon points to make a deposit.",
            Py4GW.Console.MessageType.Warning)
        return

    _do_deposit(LUXON_ENUM, 1)
    Py4GW.Console.Log(module_name,
        f"Deposited {CHUNK} Luxon points.",
        Py4GW.Console.MessageType.Info)

def deposit_all_luxon():
    unspent = get_luxon_unspent()
    chunks  = unspent // CHUNK
    if chunks == 0:
        Py4GW.Console.Log(module_name,
            "Not enough Luxon points to make a deposit.",
            Py4GW.Console.MessageType.Warning)
        return

    total = chunks * CHUNK
    _do_deposit(LUXON_ENUM, chunks)
    Py4GW.Console.Log(module_name,
        f"Deposited {total} Luxon points.",
        Py4GW.Console.MessageType.Info)

def deposit_5000_kurzick():
    unspent = get_kurzick_unspent()
    if unspent < CHUNK:
        Py4GW.Console.Log(module_name,
            "Not enough Kurzick points to make a deposit.",
            Py4GW.Console.MessageType.Warning)
        return

    _do_deposit(KURZICK_ENUM, 1)
    Py4GW.Console.Log(module_name,
        f"Deposited {CHUNK} Kurzick points.",
        Py4GW.Console.MessageType.Info)

def deposit_all_kurzick():
    unspent = get_kurzick_unspent()
    chunks  = unspent // CHUNK
    if chunks == 0:
        Py4GW.Console.Log(module_name,
            "Not enough Kurzick points to make a deposit.",
            Py4GW.Console.MessageType.Warning)
        return

    total = chunks * CHUNK
    _do_deposit(KURZICK_ENUM, chunks)
    Py4GW.Console.Log(module_name,
        f"Deposited {total} Kurzick points.",
        Py4GW.Console.MessageType.Info)

# per-tick flag to defer actions into logic_tick
_request = None

def logic_tick():
    global _request
    if _request:
        _request()
        _request = None

def on_imgui_render():
    global _request
    PyImGui.begin("Faction Deposit Control", PyImGui.WindowFlags.AlwaysAutoResize)

    PyImGui.text("Quick deposit to guild:")
    PyImGui.separator()

    if PyImGui.button("Deposit 5000 Luxon"):
        _request = deposit_5000_luxon
    if PyImGui.button("Deposit All Luxon"):
        _request = deposit_all_luxon

    PyImGui.separator()

    if PyImGui.button("Deposit 5000 Kurzick"):
        _request = deposit_5000_kurzick
    if PyImGui.button("Deposit All Kurzick"):
        _request = deposit_all_kurzick

    PyImGui.end()

def main():
    if not Routines.Checks.Map.MapValid():
        return
    logic_tick()
    on_imgui_render()

def setup(): pass
def configure(): setup()

if __name__ == "__main__":
    main()
