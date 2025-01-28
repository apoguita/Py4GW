from Py4GWCoreLib import *
checkbox_state = True
def DrawWindow():
    global checkbox_state

    if PyImGui.begin("Called Target list"):
        PyImGui.text(f"List of called targets")
        players = Party.GetPlayers()

        for player in players:
            if player.called_target_id != 0:
                PyImGui.text(f"{player.login_number} is targeting {player.called_target_id}")
    PyImGui.end()


def main():
        DrawWindow()

if __name__ == "__main__":
    main()

