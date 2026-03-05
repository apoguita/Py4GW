from __future__ import annotations

import Py4GW
import PyImGui
from Py4GWCoreLib import Player
from Py4GWCoreLib.native_src.ShMem.SysShaMem import SystemShaMemMgr, SharedMemoryHeader, AgentArraySHMemStruct, AgentArraySHMemWrapper


def _draw_counts(payload:AgentArraySHMemStruct, wrapper:AgentArraySHMemWrapper) -> None:
    all_agents = wrapper.to_int_list()
    living_agents = wrapper.get_living_array()
    ally_agents = wrapper.get_ally_array()
    neutral_agents = wrapper.get_neutral_array()
    enemy_agents = wrapper.get_enemy_array()
    spirit_pet_agents = wrapper.get_spirit_pet_array()
    minion_agents = wrapper.get_minion_array()
    npc_minipet_agents = wrapper.get_npc_minipet_array()
    item_agents = wrapper.get_item_array()
    owned_item_agents = wrapper.get_owned_item_array()
    gadget_agents = wrapper.get_gadget_array()
    dead_ally_agents = wrapper.get_dead_ally_array()
    dead_enemy_agents = wrapper.get_dead_enemy_array()

    PyImGui.text(f"AgentArrayCount: {len(all_agents)}/{payload.max_size}")
    PyImGui.text(f"All: {len(all_agents)}")
    PyImGui.text(f"Living: {len(living_agents)}")
    PyImGui.text(f"Ally: {len(ally_agents)}")
    PyImGui.text(f"Neutral: {len(neutral_agents)}")
    PyImGui.text(f"Enemy: {len(enemy_agents)}")
    PyImGui.text(f"Spirit/Pet: {len(spirit_pet_agents)}")
    PyImGui.text(f"Minion: {len(minion_agents)}")
    PyImGui.text(f"NPC/Minipet: {len(npc_minipet_agents)}")
    PyImGui.text(f"Item: {len(item_agents)}")
    PyImGui.text(f"Owned Item: {len(owned_item_agents)}")
    PyImGui.text(f"Gadget: {len(gadget_agents)}")
    PyImGui.text(f"Dead Ally: {len(dead_ally_agents)}")
    PyImGui.text(f"Dead Enemy: {len(dead_enemy_agents)}")


def _draw_agent_preview(wrapper:AgentArraySHMemWrapper) -> None:
    agent_id = Player.GetAgentID()
    agent = wrapper.get_agent_by_id(agent_id) if wrapper is not None else None

    PyImGui.separator()
    PyImGui.text(f"Player Agent ID: {agent_id}")

    if agent is None:
        PyImGui.text("Player Agent: <not found in shared memory>")
        return

    PyImGui.text("Player Agent")
    PyImGui.text(f"Agent agent_id: {agent.agent_id}")
    PyImGui.text(f"Agent type: {agent.agent_type}")
    PyImGui.text(f"Level: {agent.level}")
    PyImGui.text(f"Allegiance: {agent.allegiance}")
    PyImGui.text(f"HP: {agent.HPValues[0]:.3f} / {agent.HPValues[1]:.3f} / {agent.HPValues[2]:.3f}")
    PyImGui.text(
        f"Energy: {agent.EnergyValues[0]:.3f} / {agent.EnergyValues[1]:.3f} / {agent.EnergyValues[2]:.3f}"
    )
    PyImGui.text(
        f"Pos: ({agent.Position.x:.1f}, {agent.Position.y:.1f}, zplane={agent.Position.zplane})"
    )
    PyImGui.text(f"Z: {agent.z:.1f}")
    ptr_value = int(agent.ptr) if agent.ptr else 0
    PyImGui.text(f"Ptr: 0x{ptr_value:X}")

    enemy_agents = wrapper.get_enemy_array()
    if not enemy_agents:
        return


    enemy_agent_id = enemy_agents[0]
    enemy_agent = wrapper.get_agent_by_id(enemy_agent_id) if wrapper is not None else None
    if enemy_agent is None:
        return
    PyImGui.separator()
    PyImGui.text("First Enemy")
    PyImGui.text(
        f"Agent: id={enemy_agent.agent_id} level={enemy_agent.level} hp={enemy_agent.HPValues[0]:.3f}"
    )


def draw_window() -> None:
    header:SharedMemoryHeader| None = SystemShaMemMgr.header_struct
    payload:AgentArraySHMemStruct | None = SystemShaMemMgr.agent_array_struct
    wrapper:AgentArraySHMemWrapper | None = SystemShaMemMgr.get_agent_array_wrapper()

    if PyImGui.begin("Shared Memory Agent Array Test"):
        PyImGui.text(f"Ready: {Py4GW.Game.is_shared_memory_ready()}")
        PyImGui.text(f"Name: {Py4GW.Game.get_shared_memory_name()}")
        PyImGui.text(f"Size: {Py4GW.Game.get_shared_memory_size()}")
        PyImGui.text(f"Sequence (API): {Py4GW.Game.get_shared_memory_sequence()}")

        if SystemShaMemMgr.shm is None:
            PyImGui.separator()
            PyImGui.text("SystemShaMemMgr: <shared memory not connected>")
        elif header is None or payload is None:
            PyImGui.separator()
            PyImGui.text("SystemShaMemMgr: <waiting for first payload update>")
        else:
            PyImGui.separator()
            PyImGui.text(f"Version: {header.version}")
            PyImGui.text(f"PID: {header.process_id}")
            PyImGui.text(f"HWND: 0x{int(header.window_handle):X}")
            PyImGui.text(f"Region Size: {header.total_size}")
            PyImGui.text(f"Sequence (read): {header.sequence}")

            PyImGui.separator()
            if wrapper is None:
                PyImGui.text("Agent Array Wrapper: <not initialized>")
            else:
                _draw_counts(payload, wrapper)
                _draw_agent_preview(wrapper)

        PyImGui.end()


def main() -> None:
    draw_window()


if __name__ == "__main__":
    main()
