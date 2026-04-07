import Py4GW
import PyImGui

from Py4GWCoreLib import Agent, GLOBAL_CACHE, Player, Routines, Utils
from Py4GWCoreLib.BottingTree import BottingTree
from Py4GWCoreLib.Map import Map
from Py4GWCoreLib.enums_src.Model_enums import ModelID


def build_tree_diagnostic_dump(botting_tree: BottingTree, selected_debug_tree_name: str) -> str:
    bb = botting_tree.blackboard
    move_data = botting_tree.GetMoveData()
    headless_tree = botting_tree.headless_heroai
    cached_data = headless_tree.cached_data
    options = getattr(cached_data, "account_options", None)
    leader_id = int(GLOBAL_CACHE.Party.GetPartyLeaderID() or 0)
    player_id = int(Player.GetAgentID() or 0)
    player_target_id = int(Player.GetTargetID() or 0)
    party_target_id = int(getattr(headless_tree.heroai_build._get_cached_data().combat_handler, "GetPartyTarget", lambda: 0)() or 0)
    build_contract = headless_tree.heroai_build.GetBuildContract()
    follow_threshold = float(getattr(options, "FollowMoveThreshold", -1.0)) if options is not None else -1.0
    follow_threshold_combat = float(getattr(options, "FollowMoveThresholdCombat", -1.0)) if options is not None else -1.0
    combat_enabled = bool(getattr(options, "Combat", False)) if options is not None else None
    looting_enabled = bool(getattr(options, "Looting", False)) if options is not None else None
    targeting_enabled = bool(getattr(options, "Targeting", False)) if options is not None else None
    follow_pos = None
    if options is not None:
        follow_pos = (
            float(getattr(options.FollowPos, "x", 0.0)),
            float(getattr(options.FollowPos, "y", 0.0)),
            int(float(getattr(options.FollowPos, "z", 0.0))),
        )
    distance_to_leader = Utils.Distance(Agent.GetXY(leader_id), Player.GetXY()) if leader_id else None
    combat_handler = cached_data.combat_handler
    root_children = headless_tree.tree.get_children() if hasattr(headless_tree.tree, "get_children") else []
    global_guard = root_children[0] if len(root_children) > 0 else None
    casting_block = root_children[1] if len(root_children) > 1 else None
    status_selector = root_children[2] if len(root_children) > 2 else None
    selector_children = status_selector.get_children() if status_selector is not None and hasattr(status_selector, "get_children") else []
    looting_node = selector_children[0] if len(selector_children) > 0 else None
    ooc_node = selector_children[1] if len(selector_children) > 1 else None
    follow_node = selector_children[2] if len(selector_children) > 2 else None
    combat_node = selector_children[3] if len(selector_children) > 3 else None
    imp_model_id = ModelID.Igneous_Summoning_Stone.value
    imp_item_id = int(GLOBAL_CACHE.Inventory.GetFirstModelID(imp_model_id) or 0)
    imp_model_count = int(GLOBAL_CACHE.Inventory.GetModelCount(imp_model_id) or 0)
    summoning_sickness_effect_id = 2886
    summon_creature_model_ids = {513, 1726}
    alive_imp_agent_ids = [
        int(other)
        for other in GLOBAL_CACHE.Party.GetOthers()
        if Agent.GetModelID(other) in summon_creature_model_ids and not Agent.IsDead(other)
    ]
    service_tree_names = {name: tree for name, tree in getattr(botting_tree, "_service_trees", [])}
    outpost_imp_tree = service_tree_names.get("OutpostImpService")
    explorable_imp_tree = service_tree_names.get("ExplorableImpService")

    lines: list[str] = []
    lines.append("=== Beautiful Pre-Searing Tree Diagnostics ===")
    lines.append(f"selected_debug_tree_name={selected_debug_tree_name}")
    lines.append(f"started={botting_tree.IsStarted()} paused={botting_tree.IsPaused()}")
    lines.append(f"headless_heroai_enabled={botting_tree.IsHeadlessHeroAIEnabled()}")
    lines.append(f"looting_enabled={botting_tree.IsLootingEnabled()}")
    lines.append(f"_last_heroai_state={getattr(botting_tree, '_last_heroai_state', None)}")
    lines.append(f"_last_planner_gate_state={getattr(botting_tree, '_last_planner_gate_state', None)}")
    lines.append("")
    lines.append("[Blackboard]")
    for key in (
        "HEROAI_STATUS",
        "HEROAI_SUCCESS",
        "COMBAT_ACTIVE",
        "LOOTING_ACTIVE",
        "USER_INTERRUPT_ACTIVE",
        "PAUSE_MOVEMENT",
        "PLANNER_STATUS",
        "PLANNER_OWNER",
        "account_isolation_enabled",
        "headless_heroai_enabled",
        "looting_enabled",
        "move_state",
        "move_reason",
        "move_current_waypoint_index",
        "move_path_index",
        "move_path_count",
        "move_resume_recovery_active",
    ):
        lines.append(f"{key}={repr(bb.get(key))}")
    lines.append("")
    lines.append("[MoveData]")
    lines.append(repr(move_data))
    lines.append("")
    lines.append("[HeadlessCache]")
    lines.append(f"account_email={getattr(cached_data, 'account_email', None)}")
    lines.append(f"in_aggro={getattr(cached_data.data, 'in_aggro', None)}")
    lines.append(f"in_looting_routine={getattr(cached_data, 'in_looting_routine', None)}")
    lines.append(f"looting_node_running={headless_tree.IsLootingNodeRunning()}")
    lines.append(f"looting_active={headless_tree.IsLootingActive()}")
    lines.append(f"user_interrupting={headless_tree.IsUserInterrupting()}")
    lines.append("")
    lines.append("[HeroAI Init]")
    lines.append(f"map_valid={Routines.Checks.Map.MapValid()}")
    lines.append(f"party_loaded={GLOBAL_CACHE.Party.IsPartyLoaded()}")
    lines.append(f"map_is_explorable={Map.IsExplorable()}")
    lines.append(f"map_in_cinematic={Map.IsInCinematic()}")
    lines.append(f"player_alive={Agent.IsAlive(player_id)}")
    lines.append(f"player_knocked_down={Agent.IsKnockedDown(player_id)}")
    lines.append(f"player_casting={Agent.IsCasting(player_id)}")
    lines.append(f"in_casting_routine={cached_data.combat_handler.InCastingRoutine()}")
    lines.append(f"distance_to_destination={headless_tree._distance_to_destination()}")
    lines.append(f"build_contract_class={type(build_contract).__name__ if build_contract is not None else None}")
    lines.append(f"build_tick_state={getattr(headless_tree.heroai_build, 'tick_state', None)}")
    lines.append(f"did_tick_succeed={headless_tree.heroai_build.DidTickSucceed()}")
    lines.append("")
    lines.append("[HeroAI Context]")
    lines.append(f"player_id={player_id}")
    lines.append(f"leader_id={leader_id}")
    lines.append(f"player_target_id={player_target_id}")
    lines.append(f"party_target_id={party_target_id}")
    lines.append(f"player_is_leader={player_id == leader_id}")
    lines.append(f"distance_to_leader={distance_to_leader}")
    lines.append(f"following_enabled={bool(getattr(options, 'Following', False)) if options is not None else None}")
    lines.append(f"combat_enabled={combat_enabled}")
    lines.append(f"looting_option_enabled={looting_enabled}")
    lines.append(f"targeting_enabled={targeting_enabled}")
    lines.append(f"follow_timer_expired={cached_data.follow_throttle_timer.IsExpired()}")
    lines.append(f"follow_threshold={follow_threshold}")
    lines.append(f"follow_threshold_combat={follow_threshold_combat}")
    lines.append(f"follow_pos={follow_pos}")
    lines.append(f"player_is_melee={Agent.IsMelee(player_id)}")
    lines.append("")
    lines.append("[HeroAI Bootstrap]")
    lines.append(f"headless_root_last_state={getattr(headless_tree.tree, 'last_state', None)}")
    lines.append(f"global_guard_last_state={getattr(global_guard, 'last_state', None)}")
    lines.append(f"casting_block_last_state={getattr(casting_block, 'last_state', None)}")
    lines.append(f"status_selector_last_state={getattr(headless_tree._status_selector, 'last_state', None)}")
    lines.append(f"looting_node_last_state={getattr(looting_node, 'last_state', None)}")
    lines.append(f"ooc_node_last_state={getattr(ooc_node, 'last_state', None)}")
    lines.append(f"follow_node_last_state={getattr(follow_node, 'last_state', None)}")
    lines.append(f"combat_node_last_state={getattr(combat_node, 'last_state', None)}")
    lines.append("")
    lines.append("[Combat Handler]")
    lines.append(f"combat_handler_in_aggro={getattr(combat_handler, 'in_aggro', None)}")
    lines.append(f"combat_handler_targeting_enabled={getattr(combat_handler, 'is_targeting_enabled', None)}")
    lines.append(f"combat_handler_combat_enabled={getattr(combat_handler, 'is_combat_enabled', None)}")
    lines.append(f"combat_handler_in_casting_routine={getattr(combat_handler, 'in_casting_routine', None)}")
    lines.append(f"combat_handler_skill_pointer={getattr(combat_handler, 'skill_pointer', None)}")
    lines.append(f"combat_handler_nearest_enemy={getattr(combat_handler, 'nearest_enemy', None)}")
    lines.append(f"combat_handler_nearest_npc={getattr(combat_handler, 'nearest_npc', None)}")
    lines.append(f"combat_handler_nearest_spirit={getattr(combat_handler, 'nearest_spirit', None)}")
    lines.append(f"combat_handler_lowest_ally={getattr(combat_handler, 'lowest_ally', None)}")
    lines.append(f"combat_handler_lowest_ally_energy={getattr(combat_handler, 'lowest_ally_energy', None)}")
    lines.append(f"combat_handler_auto_attack_time={getattr(cached_data, 'auto_attack_time', None)}")
    lines.append("")
    lines.append("[Imp Service]")
    lines.append(f"outpost_imp_service_last_state={getattr(outpost_imp_tree, 'last_state', None)}")
    lines.append(f"explorable_imp_service_last_state={getattr(explorable_imp_tree, 'last_state', None)}")
    lines.append(f"map_is_outpost={Map.IsOutpost()}")
    lines.append(f"map_is_explorable={Map.IsExplorable()}")
    lines.append(f"player_level={Player.GetLevel()}")
    lines.append(f"imp_model_id={imp_model_id}")
    lines.append(f"imp_item_id={imp_item_id}")
    lines.append(f"imp_model_count={imp_model_count}")
    lines.append(f"has_summoning_sickness={GLOBAL_CACHE.Effects.HasEffect(Player.GetAgentID(), summoning_sickness_effect_id)}")
    lines.append(f"alive_imp_agent_ids={alive_imp_agent_ids}")
    lines.append("")
    lines.append("[Planner Gate]")
    lines.append(f"pause_on_combat={botting_tree.pause_on_combat}")
    lines.append(f"planner_gate_state={getattr(botting_tree, '_last_planner_gate_state', None)}")
    lines.append(f"planner_tree_last_state={getattr(botting_tree.planner_tree, 'last_state', None)}")
    lines.append(f"planner_root_last_state={getattr(botting_tree.planner_tree.root, 'last_state', None)}")
    return "\n".join(lines)


def dump_tree_diagnostics(botting_tree: BottingTree, selected_debug_tree_name: str) -> None:
    payload = build_tree_diagnostic_dump(botting_tree, selected_debug_tree_name)
    print(payload)
    PyImGui.set_clipboard_text(payload)
    Py4GW.Console.Log(
        "Beautiful Pre-Searing",
        "Tree diagnostics dumped to stdout and copied to clipboard.",
        Py4GW.Console.MessageType.Info,
    )
