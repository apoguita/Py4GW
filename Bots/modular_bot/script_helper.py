"""
Script Helper

Displays:
- Player coordinates as [x, y]
- Player map (id + name)
- Target coordinates as [x, y]
"""

import PyImGui

from Py4GWCoreLib import Agent, Map, Player


def _fmt_xy(x: float, y: float) -> str:
    return f"[{int(x)}, {int(y)}]"


def main():
    if PyImGui.begin("Script Helper"):
        player_x, player_y = Player.GetXY()
        map_id = Map.GetMapID()
        map_name = Map.GetMapName(map_id)
        target_id = Player.GetTargetID()

        player_coords = _fmt_xy(player_x, player_y)
        PyImGui.text(f"Player coordinates: {player_coords}")
        if PyImGui.button("Copy Player Coordinates"):
            PyImGui.set_clipboard_text(player_coords)

        PyImGui.text(f"Player map: [{map_id}] {map_name}")
        if PyImGui.button("Copy Player Map ID"):
            PyImGui.set_clipboard_text(str(map_id))

        if target_id and Agent.IsValid(target_id):
            target_x, target_y = Agent.GetXY(target_id)
            target_coords = _fmt_xy(target_x, target_y)
            PyImGui.text(f"Target coordinates: {target_coords}")
            if PyImGui.button("Copy Target Coordinates"):
                PyImGui.set_clipboard_text(target_coords)
        else:
            PyImGui.text("Target coordinates: []")

    PyImGui.end()

