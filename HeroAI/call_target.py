from Py4GWCoreLib import ActionQueueManager, Agent, Key, Keystroke, Player


def CallTarget(agent_id: int, interact: bool = False) -> bool:
    if agent_id == 0 or not Agent.IsValid(agent_id):
        return False

    Player.ChangeTarget(agent_id)
    if interact:
        Player.Interact(agent_id, True)
    ActionQueueManager().AddAction("ACTION", Keystroke.PressAndReleaseCombo, [Key.Ctrl.value, Key.Space.value])
    return True
