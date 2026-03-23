import PyImGui

from HeroAI.cache_data import CacheData
from HeroAI.custom_skill import CustomSkillClass
from Py4GWCoreLib import Agent, GLOBAL_CACHE, Player, Py4GW, Routines


FGJ_ID = GLOBAL_CACHE.Skill.GetID("For_Great_Justice")
custom_skill_handler = CustomSkillClass()
cached_data = CacheData()
last_snapshot = "Press 'Capture FGJ Snapshot' to collect debug values."


def _find_skill_slot(skill_id: int) -> int:
    for slot in range(1, 9):
        if int(GLOBAL_CACHE.SkillBar.GetSkillIDBySlot(slot) or 0) == skill_id:
            return slot
    return 0


def _find_prioritized_index(combat, skill_id: int) -> int:
    for index, skill_data in enumerate(combat.skills):
        if int(skill_data.skill_id or 0) == skill_id:
            return index
    return -1


def _bool_text(value: bool) -> str:
    return "yes" if value else "no"


def _draw_line(label: str, value) -> None:
    PyImGui.text(f"{label}: {value}")


def _build_snapshot() -> str:
    cached_data.Update()
    cached_data.UpdateCombat()

    combat = cached_data.combat_handler
    player_id = Player.GetAgentID()
    slot_1_based = _find_skill_slot(FGJ_ID)
    raw_slot_index = slot_1_based - 1 if slot_1_based > 0 else -1
    prioritized_index = _find_prioritized_index(combat, FGJ_ID)
    fgj_custom = custom_skill_handler.get_skill(FGJ_ID)
    selected_index, selected_target = combat.FindCastableSkill(ooc=False)
    selected_skill_id = combat.skills[selected_index].skill_id if selected_index >= 0 else 0

    lines = [
        f"player_id={player_id}",
        f"fgj_id={FGJ_ID}",
        f"equipped_slot={slot_1_based if slot_1_based > 0 else 'not equipped'}",
        f"raw_slot_index={raw_slot_index}",
        f"prioritized_index={prioritized_index}",
        f"in_aggro={cached_data.data.in_aggro}",
        f"combat_enabled={combat.is_combat_enabled}",
        f"targeting_enabled={combat.is_targeting_enabled}",
        f"current_target={Player.GetTargetID()}",
        f"local_has_effect={GLOBAL_CACHE.Effects.HasEffect(player_id, FGJ_ID)}",
        f"combat_has_effect={combat.HasEffect(player_id, FGJ_ID)}",
        f"custom_target={getattr(fgj_custom, 'TargetAllegiance', 'n/a')}",
        f"custom_nature={getattr(fgj_custom, 'Nature', 'n/a')}",
        f"custom_ooc={bool(getattr(fgj_custom.Conditions, 'IsOutOfCombat', False))}",
        f"selected_castable_index={selected_index}",
        f"selected_castable_skill_id={selected_skill_id}",
        f"selected_castable_target={selected_target}",
        f"fgj_would_be_selected={selected_index == prioritized_index and prioritized_index >= 0}",
        f"can_cast_global={Routines.Checks.Skills.CanCast()}",
        f"agent_casting={Agent.IsCasting(player_id)}",
        f"skillbar_casting={GLOBAL_CACHE.SkillBar.GetCasting()}",
    ]

    if prioritized_index >= 0:
        skill_data = combat.skills[prioritized_index]
        target_agent_id = combat.GetAppropiateTarget(prioritized_index)
        is_skill_ready = combat.IsSkillReady(prioritized_index)
        is_ooc_skill = combat.IsOOCSkill(prioritized_index)
        is_ready_to_cast, ready_target = combat.IsReadyToCast(prioritized_index)
        target_living = Agent.IsLiving(target_agent_id) if target_agent_id else False
        skillbar_data = skill_data.skillbar_data

        lines.extend([
            f"ordered_skill_id={skill_data.skill_id}",
            f"skill_order_slot_index={prioritized_index}",
            f"ordered_original_slot={combat.skill_order[prioritized_index] + 1}",
            f"recharge={getattr(skillbar_data, 'recharge', 'n/a')}",
            f"adrenaline_have={getattr(skillbar_data, 'adrenaline_a', 'n/a')}",
            f"adrenaline_need={GLOBAL_CACHE.Skill.Data.GetAdrenaline(FGJ_ID)}",
            f"is_skill_ready={is_skill_ready}",
            f"is_ooc_skill={is_ooc_skill}",
            f"appropriate_target={target_agent_id}",
            f"target_living={target_living}",
            f"ready_to_cast={is_ready_to_cast}",
            f"ready_target={ready_target}",
            f"conditions_met={combat.AreCastConditionsMet(prioritized_index, player_id)}",
            f"energy_current={combat.GetEnergyValues(player_id) * Agent.GetMaxEnergy(player_id)}",
            f"energy_cost={Routines.Checks.Skills.GetEnergyCostWithEffects(FGJ_ID, player_id)}",
            f"health={Agent.GetHealth(player_id)}",
        ])
    else:
        lines.append("fgj_status=not found in prioritized combat.skills")

    return "\n".join(lines)


def main():
    global last_snapshot
    cached_data.Update()
    cached_data.UpdateCombat()

    combat = cached_data.combat_handler
    player_id = Player.GetAgentID()
    slot_1_based = _find_skill_slot(FGJ_ID)
    raw_slot_index = slot_1_based - 1 if slot_1_based > 0 else -1
    prioritized_index = _find_prioritized_index(combat, FGJ_ID)
    fgj_custom = custom_skill_handler.get_skill(FGJ_ID)
    selected_index, selected_target = combat.FindCastableSkill(ooc=False)
    selected_skill_id = combat.skills[selected_index].skill_id if selected_index >= 0 else 0

    if PyImGui.begin("FGJ Debug"):
        if PyImGui.button("Capture FGJ Snapshot"):
            last_snapshot = _build_snapshot()
            for line in last_snapshot.splitlines():
                Py4GW.Console.Log("FGJ Debug", line, Py4GW.Console.MessageType.Info)

        _draw_line("player_id", player_id)
        _draw_line("fgj_id", FGJ_ID)
        _draw_line("equipped_slot", slot_1_based if slot_1_based > 0 else "not equipped")
        _draw_line("raw_slot_index", raw_slot_index)
        _draw_line("prioritized_index", prioritized_index)
        _draw_line("in_aggro", _bool_text(cached_data.data.in_aggro))
        _draw_line("combat_enabled", _bool_text(combat.is_combat_enabled))
        _draw_line("targeting_enabled", _bool_text(combat.is_targeting_enabled))
        _draw_line("current_target", Player.GetTargetID())
        _draw_line("local_has_effect", _bool_text(GLOBAL_CACHE.Effects.HasEffect(player_id, FGJ_ID)))
        _draw_line("combat_has_effect", _bool_text(combat.HasEffect(player_id, FGJ_ID)))
        _draw_line("custom_target", getattr(fgj_custom, "TargetAllegiance", "n/a"))
        _draw_line("custom_nature", getattr(fgj_custom, "Nature", "n/a"))
        _draw_line("custom_ooc", _bool_text(bool(getattr(fgj_custom.Conditions, "IsOutOfCombat", False))))
        _draw_line("selected_castable_index", selected_index)
        _draw_line("selected_castable_skill_id", selected_skill_id)
        _draw_line("selected_castable_target", selected_target)
        _draw_line("fgj_would_be_selected", _bool_text(selected_index == prioritized_index and prioritized_index >= 0))

        if prioritized_index >= 0:
            skill_data = combat.skills[prioritized_index]
            target_agent_id = combat.GetAppropiateTarget(prioritized_index)
            is_skill_ready = combat.IsSkillReady(prioritized_index)
            is_ooc_skill = combat.IsOOCSkill(prioritized_index)
            is_ready_to_cast, ready_target = combat.IsReadyToCast(prioritized_index)
            target_living = Agent.IsLiving(target_agent_id) if target_agent_id else False
            skillbar_data = skill_data.skillbar_data

            _draw_line("ordered_skill_id", skill_data.skill_id)
            _draw_line("skill_order_slot_index", prioritized_index)
            _draw_line("ordered_original_slot", combat.skill_order[prioritized_index] + 1)
            _draw_line("recharge", getattr(skillbar_data, "recharge", "n/a"))
            _draw_line("adrenaline_have", getattr(skillbar_data, "adrenaline_a", "n/a"))
            _draw_line("adrenaline_need", GLOBAL_CACHE.Skill.Data.GetAdrenaline(FGJ_ID))
            _draw_line("is_skill_ready", _bool_text(is_skill_ready))
            _draw_line("is_ooc_skill", _bool_text(is_ooc_skill))
            _draw_line("appropriate_target", target_agent_id)
            _draw_line("target_living", _bool_text(target_living))
            _draw_line("ready_to_cast", _bool_text(is_ready_to_cast))
            _draw_line("ready_target", ready_target)
            _draw_line("conditions_met", _bool_text(combat.AreCastConditionsMet(prioritized_index, player_id)))
            _draw_line("can_cast_global", _bool_text(Routines.Checks.Skills.CanCast()))
            _draw_line("agent_casting", _bool_text(Agent.IsCasting(player_id)))
            _draw_line("skillbar_casting", GLOBAL_CACHE.SkillBar.GetCasting())
            _draw_line("energy_current", combat.GetEnergyValues(player_id) * Agent.GetMaxEnergy(player_id))
            _draw_line("energy_cost", Routines.Checks.Skills.GetEnergyCostWithEffects(FGJ_ID, player_id))
            _draw_line("health", Agent.GetHealth(player_id))
        else:
            PyImGui.text("FGJ is not present in the prioritized HeroAI skill list.")

        PyImGui.separator()
        PyImGui.text("Press the button and copy the FGJ Debug lines from the Py4GW console.")
        for line in last_snapshot.splitlines():
            PyImGui.text(line)

    PyImGui.end()


if __name__ == "__main__":
    main()
