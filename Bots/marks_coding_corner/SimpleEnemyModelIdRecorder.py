import json
from collections import OrderedDict
from Py4GWCoreLib import *

AGENT_FILE = "recorded_agents.json"
recorded_agents = OrderedDict()


def save_agents():
    """Save recorded agent data to disk (sorted by name)."""
    with open(AGENT_FILE, "w") as f:
        json.dump(recorded_agents, f, indent=4)


def load_agents():
    """Load saved agents from disk."""
    try:
        with open(AGENT_FILE, "r") as f:
            data = json.load(f)
            # Sort alphabetically by name
            return OrderedDict(sorted(data.items()))
    except (FileNotFoundError, json.JSONDecodeError):
        return OrderedDict()


def record_current_enemies():
    """Scan nearby enemies and record their names + model IDs."""
    global recorded_agents

    player_x, player_y = GLOBAL_CACHE.Player.GetXY()
    enemy_agent_ids = Routines.Agents.GetFilteredEnemyArray(
        player_x, player_y, Range.SafeCompass.value
    )

    added = 0
    for agent_id in enemy_agent_ids:
        agent = GLOBAL_CACHE.Agent.GetAgentByID(agent_id)
        if not agent or agent.agent_id == 0:
            continue

        name = GLOBAL_CACHE.Agent.GetName(agent.agent_id)
        model_id = GLOBAL_CACHE.Agent.GetModelID(agent.agent_id)
        if not name:
            continue

        # Only record if name not already present
        if name not in recorded_agents:
            recorded_agents[name] = {
                "model_id": model_id,
                "agent_id": agent.agent_id
            }
            added += 1

    if added:
        # Keep alphabetical order
        recorded_agents = OrderedDict(sorted(recorded_agents.items()))
        save_agents()
        ConsoleLog("Agent Recorder", f"Added {added} new agent(s).")
    else:
        ConsoleLog("Agent Recorder", "No new agents found.")


def main():
    global recorded_agents

    if not recorded_agents:
        recorded_agents = load_agents()

    if PyImGui.begin("Agent Recorder"):
        PyImGui.text("Enemy Agent Name Recorder")
        PyImGui.separator()

        if PyImGui.button("SCAN & RECORD"):
            record_current_enemies()

        if PyImGui.button("CLEAR ALL"):
            recorded_agents.clear()
            save_agents()
            ConsoleLog("Agent Recorder", "Cleared all recorded agents.")

        PyImGui.separator()

        if PyImGui.begin_table("Recorded Agents", 3):
            PyImGui.table_setup_column("Model ID")
            PyImGui.table_setup_column("Name")
            PyImGui.table_setup_column("")  # remove button
            PyImGui.table_headers_row()

            remove_key = None
            for name, info in recorded_agents.items():
                PyImGui.table_next_row()
                PyImGui.table_next_column()
                PyImGui.text(str(info["model_id"]))
                PyImGui.table_next_column()
                PyImGui.text(name)
                PyImGui.table_next_column()
                if PyImGui.button(f"Remove##{name}"):
                    remove_key = name

            PyImGui.end_table()

            if remove_key:
                recorded_agents.pop(remove_key, None)
                save_agents()
                ConsoleLog("Agent Recorder", f"Removed: {remove_key}")

        PyImGui.end()


if __name__ == "__main__":
    main()
