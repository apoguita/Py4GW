from __future__ import annotations

import time
from typing import Any, Dict, List

# import PyImGui
from Py4GWCoreLib import Agent, AgentArray, Botting, Color, Dialog, GLOBAL_CACHE, ImGui, Map, Player, Py4GW, PyImGui, Routines, UIManager

MODULE_NAME = "Zaishen Quest Taker"
MODULE_ICON = "Textures\\Module_Icons\\Quest Auto Runner.png"
EMBARK_BEACH = 857
QUEST_TARGET_COUNT = 3
QUEST_TYPE_SEQUENCE = [
    "Zaishen Mission",
    "Zaishen Bounty",
    "Zaishen Vanquish",
]
QUEST_LOG_REFRESH_TIMEOUT_MS = 800
QUEST_VERIFY_TIMEOUT_SECONDS = 2.0
POST_DIALOG_SEND_WAIT_MS = 200
CLUSTER_NAME_BY_ORDINAL = {
    1: "Northwest",
    2: "Northeast",
    3: "Southeast",
    4: "Southwest",
}
ZAISHEN_QUEST_LIMIT_MESSAGES = {
    "The Zaishen only allow 3 missions to be undertaken at one time.",
    "Zaishen bounties are limited to 3 at one time.",
    "Zaishen battle assignments are limited to 3 at one time.",
}
ZAISHEN_NO_MORE_QUESTS_MESSAGES = {
    "There are no more quests available here today, but other signs may have more postings from the Zaishen.",
}
ZAISHEN_PENDING_OBJECTIVE_MESSAGES = {
    "There are still threats that remain. Return when you have slain all of the foes that await you at your destination."
}
ZAISHEN_DECLINE_MESSAGES = {
    "No, I'm way too busy today.",
    "No, I am way too busy today.",
}

RECORDED_ZAISHEN_ROUTE = [
    {'index': 1, 'kind': 'step', 'label': 'Step 1', 'map_id': 857, 'map_name': 'Embark Beach', 'player_agent_id': 1, 'player_x': -3410.77, 'player_y': 416.35, 'player_z': -412.13},
    {'index': 2, 'kind': 'npc', 'label': 'NPC 2', 'map_id': 857, 'map_name': 'Embark Beach', 'player_agent_id': 1, 'player_x': -3410.77, 'player_y': 416.35, 'player_z': -412.13, 'target_id': 13, 'target_name': 'Zaishen Mission', 'target_model_id': 1197, 'target_is_npc': True, 'target_allegiance': 'NPC/Minipet', 'target_x': -3512.0, 'target_y': 460.0, 'target_z': -411.22},
    {'index': 3, 'kind': 'step', 'label': 'Step 3', 'map_id': 857, 'map_name': 'Embark Beach', 'player_agent_id': 1, 'player_x': -3292.84, 'player_y': 573.26, 'player_z': -411.65},
    {'index': 4, 'kind': 'npc', 'label': 'NPC 4', 'map_id': 857, 'map_name': 'Embark Beach', 'player_agent_id': 1, 'player_x': -3292.84, 'player_y': 573.26, 'player_z': -411.65, 'target_id': 14, 'target_name': 'Zaishen Bounty', 'target_model_id': 1198, 'target_is_npc': True, 'target_allegiance': 'NPC/Minipet', 'target_x': -3379.0, 'target_y': 636.0, 'target_z': -411.78},
    {'index': 5, 'kind': 'step', 'label': 'Step 5', 'map_id': 857, 'map_name': 'Embark Beach', 'player_agent_id': 1, 'player_x': -3204.26, 'player_y': 737.57, 'player_z': -412.44},
    {'index': 6, 'kind': 'npc', 'label': 'NPC 6', 'map_id': 857, 'map_name': 'Embark Beach', 'player_agent_id': 1, 'player_x': -3204.26, 'player_y': 737.57, 'player_z': -412.44, 'target_id': 15, 'target_name': 'Zaishen Vanquish', 'target_model_id': 1200, 'target_is_npc': True, 'target_allegiance': 'NPC/Minipet', 'target_x': -3284.0, 'target_y': 793.0, 'target_z': -412.76},
    {'index': 7, 'kind': 'step', 'label': 'Step 7', 'map_id': 857, 'map_name': 'Embark Beach', 'player_agent_id': 1, 'player_x': -2960.45, 'player_y': 905.27, 'player_z': -412.0},
    {'index': 8, 'kind': 'step', 'label': 'Step 8', 'map_id': 857, 'map_name': 'Embark Beach', 'player_agent_id': 1, 'player_x': -2056.49, 'player_y': 535.82, 'player_z': -412.24},
    {'index': 9, 'kind': 'step', 'label': 'Step 9', 'map_id': 857, 'map_name': 'Embark Beach', 'player_agent_id': 1, 'player_x': -562.97, 'player_y': 154.79, 'player_z': -320.54},
    {'index': 10, 'kind': 'step', 'label': 'Step 10', 'map_id': 857, 'map_name': 'Embark Beach', 'player_agent_id': 1, 'player_x': 1422.99, 'player_y': 172.28, 'player_z': -562.93},
    {'index': 11, 'kind': 'step', 'label': 'Step 11', 'map_id': 857, 'map_name': 'Embark Beach', 'player_agent_id': 1, 'player_x': 2271.03, 'player_y': 477.33, 'player_z': -560.87},
    {'index': 12, 'kind': 'step', 'label': 'Step 12', 'map_id': 857, 'map_name': 'Embark Beach', 'player_agent_id': 1, 'player_x': 2372.89, 'player_y': 2358.08, 'player_z': -993.67},
    {'index': 13, 'kind': 'step', 'label': 'Step 13', 'map_id': 857, 'map_name': 'Embark Beach', 'player_agent_id': 1, 'player_x': 2801.81, 'player_y': 3058.28, 'player_z': -971.8},
    {'index': 14, 'kind': 'step', 'label': 'Step 14', 'map_id': 857, 'map_name': 'Embark Beach', 'player_agent_id': 42, 'player_x': 2617.1, 'player_y': 3333.74, 'player_z': -886.97},
    {'index': 15, 'kind': 'npc', 'label': 'NPC 15', 'map_id': 857, 'map_name': 'Embark Beach', 'player_agent_id': 42, 'player_x': 2617.1, 'player_y': 3333.74, 'player_z': -886.97, 'target_id': 6, 'target_name': 'Zaishen Mission', 'target_model_id': 1197, 'target_is_npc': True, 'target_allegiance': 'NPC/Minipet', 'target_x': 2700.0, 'target_y': 3278.0, 'target_z': -909.84},
    {'index': 16, 'kind': 'step', 'label': 'Step 16', 'map_id': 857, 'map_name': 'Embark Beach', 'player_agent_id': 42, 'player_x': 2452.44, 'player_y': 3090.11, 'player_z': -889.91},
    {'index': 17, 'kind': 'npc', 'label': 'NPC 17', 'map_id': 857, 'map_name': 'Embark Beach', 'player_agent_id': 42, 'player_x': 2452.44, 'player_y': 3090.11, 'player_z': -889.91, 'target_id': 7, 'target_name': 'Zaishen Bounty', 'target_model_id': 1198, 'target_is_npc': True, 'target_allegiance': 'NPC/Minipet', 'target_x': 2533.0, 'target_y': 3025.0, 'target_z': -908.36},
    {'index': 18, 'kind': 'step', 'label': 'Step 18', 'map_id': 857, 'map_name': 'Embark Beach', 'player_agent_id': 42, 'player_x': 2235.34, 'player_y': 2830.28, 'player_z': -877.92},
    {'index': 19, 'kind': 'npc', 'label': 'NPC 19', 'map_id': 857, 'map_name': 'Embark Beach', 'player_agent_id': 42, 'player_x': 2235.34, 'player_y': 2830.28, 'player_z': -877.92, 'target_id': 8, 'target_name': 'Zaishen Vanquish', 'target_model_id': 1200, 'target_is_npc': True, 'target_allegiance': 'NPC/Minipet', 'target_x': 2331.0, 'target_y': 2778.0, 'target_z': -904.63},
    {'index': 20, 'kind': 'step', 'label': 'Step 20', 'map_id': 857, 'map_name': 'Embark Beach', 'player_agent_id': 1, 'player_x': 2341.21, 'player_y': 2009.28, 'player_z': -1014.04},
    {'index': 21, 'kind': 'step', 'label': 'Step 21', 'map_id': 857, 'map_name': 'Embark Beach', 'player_agent_id': 1, 'player_x': 2267.43, 'player_y': -265.09, 'player_z': -440.24},
    {'index': 22, 'kind': 'step', 'label': 'Step 22', 'map_id': 857, 'map_name': 'Embark Beach', 'player_agent_id': 1, 'player_x': 2410.09, 'player_y': -1816.31, 'player_z': -79.93},
    {'index': 23, 'kind': 'step', 'label': 'Step 23', 'map_id': 857, 'map_name': 'Embark Beach', 'player_agent_id': 1, 'player_x': 2660.43, 'player_y': -2313.34, 'player_z': -84.99},
    {'index': 24, 'kind': 'npc', 'label': 'NPC 24', 'map_id': 857, 'map_name': 'Embark Beach', 'player_agent_id': 1, 'player_x': 2660.43, 'player_y': -2313.34, 'player_z': -84.99, 'target_id': 58, 'target_name': 'Zaishen Mission', 'target_model_id': 1197, 'target_is_npc': True, 'target_allegiance': 'NPC/Minipet', 'target_x': 2702.0, 'target_y': -2411.0, 'target_z': -85.0},
    {'index': 25, 'kind': 'step', 'label': 'Step 25', 'map_id': 857, 'map_name': 'Embark Beach', 'player_agent_id': 1, 'player_x': 2535.92, 'player_y': -2416.33, 'player_z': -85.08},
    {'index': 26, 'kind': 'npc', 'label': 'NPC 26', 'map_id': 857, 'map_name': 'Embark Beach', 'player_agent_id': 1, 'player_x': 2535.92, 'player_y': -2416.33, 'player_z': -85.08, 'target_id': 56, 'target_name': 'Zaishen Bounty', 'target_model_id': 1198, 'target_is_npc': True, 'target_allegiance': 'NPC/Minipet', 'target_x': 2603.0, 'target_y': -2500.0, 'target_z': -85.0},
    {'index': 27, 'kind': 'step', 'label': 'Step 27', 'map_id': 857, 'map_name': 'Embark Beach', 'player_agent_id': 1, 'player_x': 2426.98, 'player_y': -2537.65, 'player_z': -83.49},
    {'index': 28, 'kind': 'npc', 'label': 'NPC 28', 'map_id': 857, 'map_name': 'Embark Beach', 'player_agent_id': 1, 'player_x': 2426.98, 'player_y': -2537.65, 'player_z': -83.49, 'target_id': 57, 'target_name': 'Zaishen Vanquish', 'target_model_id': 1200, 'target_is_npc': True, 'target_allegiance': 'NPC/Minipet', 'target_x': 2505.0, 'target_y': -2610.0, 'target_z': -85.41},
    {'index': 29, 'kind': 'step', 'label': 'Step 29', 'map_id': 857, 'map_name': 'Embark Beach', 'player_agent_id': 1, 'player_x': 1761.28, 'player_y': -2500.37, 'player_z': -107.32},
    {'index': 30, 'kind': 'step', 'label': 'Step 30', 'map_id': 857, 'map_name': 'Embark Beach', 'player_agent_id': 1, 'player_x': 870.37, 'player_y': -2776.29, 'player_z': -56.57},
    {'index': 31, 'kind': 'step', 'label': 'Step 31', 'map_id': 857, 'map_name': 'Embark Beach', 'player_agent_id': 1, 'player_x': -195.43, 'player_y': -3501.85, 'player_z': -98.08},
    {'index': 32, 'kind': 'npc', 'label': 'NPC 32', 'map_id': 857, 'map_name': 'Embark Beach', 'player_agent_id': 1, 'player_x': -195.43, 'player_y': -3501.85, 'player_z': -98.08, 'target_id': 7, 'target_name': 'Zaishen Mission', 'target_model_id': 1197, 'target_is_npc': True, 'target_allegiance': 'NPC/Minipet', 'target_x': -277.0, 'target_y': -3561.0, 'target_z': -101.44},
    {'index': 33, 'kind': 'step', 'label': 'Step 33', 'map_id': 857, 'map_name': 'Embark Beach', 'player_agent_id': 1, 'player_x': -345.17, 'player_y': -3373.6, 'player_z': -96.07},
    {'index': 34, 'kind': 'npc', 'label': 'NPC 34', 'map_id': 857, 'map_name': 'Embark Beach', 'player_agent_id': 1, 'player_x': -345.17, 'player_y': -3373.6, 'player_z': -96.07, 'target_id': 9, 'target_name': 'Zaishen Vanquish', 'target_model_id': 1200, 'target_is_npc': True, 'target_allegiance': 'NPC/Minipet', 'target_x': -428.0, 'target_y': -3439.0, 'target_z': -99.12},
    {'index': 35, 'kind': 'step', 'label': 'Step 35', 'map_id': 857, 'map_name': 'Embark Beach', 'player_agent_id': 1, 'player_x': -491.14, 'player_y': -3260.51, 'player_z': -94.82},
    {'index': 36, 'kind': 'npc', 'label': 'NPC 36', 'map_id': 857, 'map_name': 'Embark Beach', 'player_agent_id': 1, 'player_x': -491.14, 'player_y': -3260.51, 'player_z': -94.82, 'target_id': 8, 'target_name': 'Zaishen Bounty', 'target_model_id': 1198, 'target_is_npc': True, 'target_allegiance': 'NPC/Minipet', 'target_x': -557.0, 'target_y': -3333.0, 'target_z': -94.42},
]


def _route_point_from_record(record: Dict[str, Any]) -> tuple[float, float]:
    return (
        float(record.get("player_x", 0.0) or 0.0),
        float(record.get("player_y", 0.0) or 0.0),
    )


def _distance_xy(point_a: tuple[float, float], point_b: tuple[float, float]) -> float:
    dx = float(point_a[0]) - float(point_b[0])
    dy = float(point_a[1]) - float(point_b[1])
    return (dx * dx + dy * dy) ** 0.5


def _build_cluster_catalog_from_recorded_route() -> List[Dict[str, Any]]:
    clusters: Dict[int, Dict[str, Any]] = {}
    name_counts: Dict[str, int] = {}

    for record in RECORDED_ZAISHEN_ROUTE:
        if int(record.get("map_id", 0) or 0) != EMBARK_BEACH:
            continue
        if str(record.get("kind", "") or "").strip().lower() != "npc":
            continue

        npc_name = str(record.get("target_name", "") or "").strip()
        if not npc_name:
            continue

        ordinal = int(name_counts.get(npc_name, 0)) + 1
        name_counts[npc_name] = ordinal
        cluster = clusters.setdefault(
            ordinal,
            {
                "cluster_index": ordinal,
                "cluster_name": CLUSTER_NAME_BY_ORDINAL.get(ordinal, f"Cluster {ordinal}"),
                "targets": [],
            },
        )

        approach_xy = _route_point_from_record(record)
        npc_xy = (
            float(record.get("target_x", 0.0) or 0.0),
            float(record.get("target_y", 0.0) or 0.0),
        )
        cluster["targets"].append(
            {
                "label": f"{npc_name} ({cluster['cluster_name']})",
                "npc_name": npc_name,
                "cluster_index": ordinal,
                "cluster_name": cluster["cluster_name"],
                "model_id": int(record.get("target_model_id", 0) or 0),
                "route_points": [approach_xy],
                "approach_xy": approach_xy,
                "npc_xy": npc_xy,
            }
        )

    ordered_clusters: List[Dict[str, Any]] = []
    for ordinal in sorted(clusters):
        cluster = clusters[ordinal]
        targets = list(cluster.get("targets", []) or [])
        if targets:
            center_x = sum(float(target["npc_xy"][0]) for target in targets) / len(targets)
            center_y = sum(float(target["npc_xy"][1]) for target in targets) / len(targets)
            cluster["center_xy"] = (center_x, center_y)
        else:
            cluster["center_xy"] = (0.0, 0.0)
        ordered_clusters.append(cluster)
    return ordered_clusters


def _select_cluster_for_spawn(player_xy: tuple[float, float]) -> Dict[str, Any] | None:
    if not ZAISHEN_CLUSTERS:
        return None
    return min(
        ZAISHEN_CLUSTERS,
        key=lambda cluster: min(
            _distance_xy(player_xy, tuple(target.get("approach_xy", cluster.get("center_xy", (0.0, 0.0)))))
            for target in (cluster.get("targets", []) or [])
        ),
    )


def _build_targets_for_cluster(cluster: Dict[str, Any], start_xy: tuple[float, float]) -> List[Dict[str, Any]]:
    _ = start_xy
    raw_targets = [dict(target) for target in (cluster.get("targets", []) or [])]
    target_by_name = {
        str(target.get("npc_name", "") or "").strip(): target
        for target in raw_targets
    }
    ordered_targets: List[Dict[str, Any]] = []
    for quest_name in QUEST_TYPE_SEQUENCE:
        target = target_by_name.get(quest_name)
        if target is None:
            return []
        ordered_targets.append(target)
    for index, target in enumerate(ordered_targets, start=1):
        target["run_order"] = index
    return ordered_targets


ZAISHEN_CLUSTERS = _build_cluster_catalog_from_recorded_route()

bot = Botting(MODULE_NAME, config_movement_timeout=20000)


class ZaishenBountyState:
    def __init__(self) -> None:
        self.confirmation_text = "I can do that!"
        self.move_timeout_ms = 20000
        self.dialog_timeout_ms = 7000
        self.quest_targets: List[Dict[str, Any]] = []
        self.selected_cluster_name = ""
        self.spawn_xy = (0.0, 0.0)
        self.current_npc_name = ""
        self.current_npc_ordinal = 0
        self.current_target_model_id = 0
        self.current_cluster_name = ""
        self.current_route_points: List[tuple[float, float]] = []
        self.first_offer_dialog_id = 0
        self.offered_quest_name = ""
        self.confirmation_dialog_id = 0
        self.offer_is_confirmation_step = False
        self.npc_agent_id = 0
        self.npc_xy = (0.0, 0.0)
        self.skip_current_npc = False
        self.last_status = "Idle"
        self.last_choices: List[str] = []
        self.last_quest_log_names: List[str] = []
        self.completed_results: List[str] = []
        self.current_pass_label = "initial"
        self.successful_quest_names: List[str] = []
        self.retryable_failed_quest_names: List[str] = []
        self.final_retry_targets: List[str] = []
        self.last_error = ""
        self.stop_requested = False

    def reset_run_state(self) -> None:
        self.quest_targets = []
        self.selected_cluster_name = ""
        self.spawn_xy = (0.0, 0.0)
        self.current_npc_name = ""
        self.current_npc_ordinal = 0
        self.current_target_model_id = 0
        self.current_cluster_name = ""
        self.current_route_points = []
        self.first_offer_dialog_id = 0
        self.offered_quest_name = ""
        self.confirmation_dialog_id = 0
        self.offer_is_confirmation_step = False
        self.npc_agent_id = 0
        self.npc_xy = (0.0, 0.0)
        self.skip_current_npc = False
        self.last_choices = []
        self.last_quest_log_names = []
        self.completed_results = []
        self.current_pass_label = "initial"
        self.successful_quest_names = []
        self.retryable_failed_quest_names = []
        self.final_retry_targets = []
        self.last_error = ""
        self.stop_requested = False

    def config_error(self) -> str:
        if not ZAISHEN_CLUSTERS:
            return "Recorded Zaishen cluster data is empty."
        for cluster in ZAISHEN_CLUSTERS:
            cluster_names = {
                str(target.get("npc_name", "") or "").strip()
                for target in (cluster.get("targets", []) or [])
            }
            if any(required_name not in cluster_names for required_name in QUEST_TYPE_SEQUENCE):
                return "Recorded Zaishen cluster data is incomplete."
        return ""

    def quest_log_ids(self) -> List[int]:
        try:
            return [int(qid) for qid in (GLOBAL_CACHE.Quest.GetQuestLogIds() or [])]
        except Exception:
            return []

    def set_status(self, message: str, *, error: bool = False) -> None:
        self.last_status = message
        if error:
            self.last_error = message
            Py4GW.Console.Log(MODULE_NAME, message, Py4GW.Console.MessageType.Error)
        else:
            Py4GW.Console.Log(MODULE_NAME, message, Py4GW.Console.MessageType.Info)

    def begin_npc(self, target: dict, *, pass_label: str = "initial") -> None:
        self.current_npc_name = str(target.get("npc_name", "") or "")
        self.current_npc_ordinal = int(target.get("run_order", 0) or 0)
        self.current_target_model_id = int(target.get("model_id", 0) or 0)
        self.current_cluster_name = str(target.get("cluster_name", "") or "")
        self.current_route_points = [
            (float(point[0]), float(point[1]))
            for point in (target.get("route_points", []) or [])
            if isinstance(point, (list, tuple)) and len(point) >= 2
        ]
        self.first_offer_dialog_id = 0
        self.offered_quest_name = ""
        self.confirmation_dialog_id = 0
        self.offer_is_confirmation_step = False
        self.npc_agent_id = 0
        npc_xy = target.get("npc_xy", (0.0, 0.0))
        self.npc_xy = (float(npc_xy[0]), float(npc_xy[1])) if isinstance(npc_xy, (list, tuple)) and len(npc_xy) >= 2 else (0.0, 0.0)
        self.skip_current_npc = False
        self.last_choices = []
        self.current_pass_label = str(pass_label or "initial")

    def append_result(self, message: str) -> None:
        self.completed_results.append(message)

    def record_quest_failure(self, *, retryable: bool = True) -> None:
        quest_name = str(self.current_npc_name or "").strip()
        if not quest_name:
            return
        if self.current_pass_label == "final retry":
            return
        if retryable and quest_name not in self.retryable_failed_quest_names and quest_name not in self.successful_quest_names:
            self.retryable_failed_quest_names.append(quest_name)

    def record_quest_success(self) -> None:
        quest_name = str(self.current_npc_name or "").strip()
        if not quest_name:
            return
        if quest_name not in self.successful_quest_names:
            self.successful_quest_names.append(quest_name)
        self.retryable_failed_quest_names = [
            name for name in self.retryable_failed_quest_names if name != quest_name
        ]
        self.final_retry_targets = [
            name for name in self.final_retry_targets if name != quest_name
        ]


state = ZaishenBountyState()


def _normalize_dialog_label(value: str) -> str:
    return " ".join(str(value or "").strip().lower().split())


def _normalize_quest_name(value: str) -> str:
    return " ".join(str(value or "").strip().lower().split())


def _button_text(button) -> str:
    return str(getattr(button, "message_decoded", "") or getattr(button, "message", "") or "").strip()


def _dialog_text_from_catalog(dialog_id: int) -> str:
    if int(dialog_id) == 0:
        return ""
    try:
        dialog_info = Dialog.get_dialog_info(int(dialog_id))
        content = str(getattr(dialog_info, "content", "") or "").strip() if dialog_info is not None else ""
        if content:
            return content
    except Exception:
        pass
    try:
        decoded = str(Dialog.get_dialog_text_decoded(int(dialog_id)) or "").strip()
        if decoded:
            return decoded
    except Exception:
        pass
    return ""


def _current_target_label() -> str:
    if state.current_npc_name and state.current_cluster_name:
        return f"{state.current_npc_name} ({state.current_cluster_name})"
    return state.current_npc_name or "Current NPC"


def _current_attempt_label() -> str:
    label = _current_target_label()
    if state.current_pass_label == "final retry":
        return f"{label} [final retry]"
    return label


def _get_selected_target_by_name(quest_name: str) -> Dict[str, Any] | None:
    normalized = str(quest_name or "").strip()
    for target in state.quest_targets:
        if str(target.get("npc_name", "") or "").strip() == normalized:
            return target
    return None


def _active_dialog_message() -> str:
    active_dialog = Dialog.get_active_dialog()
    if active_dialog is None:
        return ""
    return str(getattr(active_dialog, "message", "") or "").strip()


def _is_zaishen_quest_limit_message(message: str) -> bool:
    normalized = _normalize_dialog_label(message)
    return any(normalized == _normalize_dialog_label(candidate) for candidate in ZAISHEN_QUEST_LIMIT_MESSAGES)


def _classify_zaishen_dialog_rejection(message: str) -> tuple[str, bool, bool] | None:
    normalized = _normalize_dialog_label(message)
    if not normalized:
        return None
    if any(normalized == _normalize_dialog_label(candidate) for candidate in ZAISHEN_QUEST_LIMIT_MESSAGES):
        return ("quest limit reached", False, False)
    if any(normalized == _normalize_dialog_label(candidate) for candidate in ZAISHEN_NO_MORE_QUESTS_MESSAGES):
        return ("no more Zaishen quests are available from this sign today", False, False)
    if any(normalized == _normalize_dialog_label(candidate) for candidate in ZAISHEN_PENDING_OBJECTIVE_MESSAGES):
        return ("current Zaishen objective is still active and must be finished first", False, False)
    return None


def _is_confirmation_button_text(value: str) -> bool:
    return _normalize_dialog_label(value) == _normalize_dialog_label(state.confirmation_text)


def _is_decline_button_text(value: str) -> bool:
    normalized = _normalize_dialog_label(value)
    return any(normalized == _normalize_dialog_label(candidate) for candidate in ZAISHEN_DECLINE_MESSAGES)


def _dialog_is_open() -> bool:
    return bool(UIManager.IsNPCDialogVisible() or Dialog.is_dialog_active())


def _active_dialog_agent_id() -> int:
    try:
        active_dialog = Dialog.get_active_dialog()
        return int(getattr(active_dialog, "agent_id", 0) or 0) if active_dialog is not None else 0
    except Exception:
        return 0


def _dialog_belongs_to_current_npc() -> bool:
    if state.npc_agent_id == 0:
        return False
    agent_id = _active_dialog_agent_id()
    return int(agent_id) != 0 and int(agent_id) == int(state.npc_agent_id)


def _current_npc_dialog_is_ready() -> bool:
    return _dialog_is_open() and _dialog_belongs_to_current_npc()


def _distance_to_current_npc() -> float:
    if state.npc_agent_id == 0:
        return float("inf")
    try:
        player_x, player_y = Player.GetXY()
        npc_x, npc_y = Agent.GetXY(state.npc_agent_id)
    except Exception:
        return float("inf")
    dx = float(player_x) - float(npc_x)
    dy = float(player_y) - float(npc_y)
    return (dx * dx + dy * dy) ** 0.5


def _resolve_offered_quest_name(button) -> str:
    button_text = _button_text(button)
    if button_text and not _is_confirmation_button_text(button_text):
        return button_text

    catalog_text = _dialog_text_from_catalog(int(getattr(button, "dialog_id", 0) or 0))
    if catalog_text and not _is_confirmation_button_text(catalog_text):
        return catalog_text

    active_message = _active_dialog_message() if _current_npc_dialog_is_ready() else ""
    if active_message and not _is_confirmation_button_text(active_message) and not _is_zaishen_quest_limit_message(active_message):
        return active_message

    return ""


def _yield_stop_with_status(message: str, *, error: bool = False):
    state.set_status(message, error=error)
    state.stop_requested = True
    yield


def _yield_skip_current_npc(
    message: str,
    *,
    error: bool = False,
    retryable: bool = True,
    counts_as_failure: bool = True,
):
    result = f"{_current_attempt_label()}: {message}"
    state.skip_current_npc = True
    if counts_as_failure:
        state.record_quest_failure(retryable=retryable)
    state.append_result(result)
    state.set_status(result, error=error)
    yield from Routines.Yield.wait(100)


def _refresh_quest_log_names(timeout_ms: int = QUEST_LOG_REFRESH_TIMEOUT_MS):
    state.last_quest_log_names = []
    quest_ids = state.quest_log_ids()
    if not quest_ids:
        yield
        return

    for quest_id in quest_ids:
        try:
            GLOBAL_CACHE.Quest.RequestQuestName(quest_id)
        except Exception:
            pass

    pending = set(int(quest_id) for quest_id in quest_ids)
    collected: List[str] = []
    deadline = time.monotonic() + (max(250, int(timeout_ms)) / 1000.0)

    while pending and time.monotonic() < deadline:
        ready_now: List[int] = []
        for quest_id in list(pending):
            try:
                if GLOBAL_CACHE.Quest.IsQuestNameReady(quest_id):
                    quest_name = str(GLOBAL_CACHE.Quest.GetQuestName(quest_id) or "").strip()
                    if quest_name:
                        collected.append(quest_name)
                    ready_now.append(quest_id)
            except Exception:
                ready_now.append(quest_id)
        for quest_id in ready_now:
            pending.discard(quest_id)
        if pending:
            yield from Routines.Yield.wait(75)

    for quest_id in list(pending):
        try:
            if GLOBAL_CACHE.Quest.IsQuestNameReady(quest_id):
                quest_name = str(GLOBAL_CACHE.Quest.GetQuestName(quest_id) or "").strip()
                if quest_name:
                    collected.append(quest_name)
        except Exception:
            pass

    state.last_quest_log_names = collected
    yield


def _initialize_run():
    state.reset_run_state()
    config_error = state.config_error()
    if config_error:
        yield from _yield_stop_with_status(config_error, error=True)
        return

    state.set_status("Run initialized. Traveling to Embark Beach and selecting the nearest Zaishen trio.")
    yield from Routines.Yield.wait(100)


def _select_targets_for_current_spawn():
    config_error = state.config_error()
    if config_error:
        yield from _yield_stop_with_status(config_error, error=True)
        return

    deadline = time.monotonic() + 8.0
    while time.monotonic() < deadline:
        if int(Map.GetMapID() or 0) == EMBARK_BEACH and Routines.Checks.Map.IsMapReady():
            break
        yield from Routines.Yield.wait(200)
    else:
        yield from _yield_stop_with_status("Failed to arrive in Embark Beach before selecting Zaishen targets.", error=True)
        return

    try:
        player_x, player_y = Player.GetXY()
    except Exception:
        yield from _yield_stop_with_status("Could not resolve the player spawn position in Embark Beach.", error=True)
        return

    state.spawn_xy = (float(player_x), float(player_y))
    cluster = _select_cluster_for_spawn(state.spawn_xy)
    if cluster is None:
        yield from _yield_stop_with_status("Could not select a Zaishen cluster for the current Embark Beach spawn.", error=True)
        return

    state.selected_cluster_name = str(cluster.get("cluster_name", "") or "")
    state.quest_targets = _build_targets_for_cluster(cluster, state.spawn_xy)
    if len(state.quest_targets) < QUEST_TARGET_COUNT:
        yield from _yield_stop_with_status("Nearest Zaishen cluster did not produce all three target NPCs.", error=True)
        return

    ordered_names = " -> ".join(str(target.get("npc_name", "") or "NPC") for target in state.quest_targets)
    state.set_status(
        f"Spawn at ({state.spawn_xy[0]:.0f}, {state.spawn_xy[1]:.0f}); selected {state.selected_cluster_name} trio. Fixed order: {ordered_names}."
    )
    yield from _refresh_quest_log_names(timeout_ms=QUEST_LOG_REFRESH_TIMEOUT_MS)
    yield from Routines.Yield.wait(100)


def _find_recorded_npc_match() -> tuple[int, float, float] | None:
    normalized_target = _normalize_quest_name(state.current_npc_name)
    matches: List[tuple[float, int, float, float]] = []
    for agent_id in AgentArray.GetNPCMinipetArray():
        try:
            resolved_name = Agent.GetNameByID(agent_id)
            if _normalize_quest_name(resolved_name) != normalized_target:
                continue
            if state.current_target_model_id and int(Agent.GetModelID(agent_id) or 0) != int(state.current_target_model_id):
                continue
            x, y = Agent.GetXY(agent_id)
            distance = ((float(x) - float(state.npc_xy[0])) ** 2 + (float(y) - float(state.npc_xy[1])) ** 2) ** 0.5
            matches.append((distance, int(agent_id), float(x), float(y)))
        except Exception:
            continue
    if not matches:
        return None
    matches.sort(key=lambda item: (item[0], item[1]))
    _, agent_id, x, y = matches[0]
    return agent_id, x, y


def _make_prepare_npc(quest_name: str):
    def _prepare():
        target = _get_selected_target_by_name(quest_name)
        if target is None:
            yield from _yield_stop_with_status(
                f"Selected Zaishen route is missing '{quest_name}'.",
                error=True,
            )
            return
        state.begin_npc(target, pass_label="initial")
        state.set_status(f"Preparing {_current_target_label()} in forced order.")
        yield from Routines.Yield.wait(100)
    return _prepare


def _make_prepare_retry_npc(quest_name: str):
    def _prepare():
        target = _get_selected_target_by_name(quest_name)
        if target is None:
            yield from _yield_stop_with_status(
                f"Selected Zaishen route is missing '{quest_name}' during the final retry pass.",
                error=True,
            )
            return
        state.begin_npc(target, pass_label="final retry")
        if quest_name not in state.final_retry_targets:
            state.skip_current_npc = True
            yield
            return
        state.set_status(f"Final retry pass: re-attempting {_current_target_label()} after another Zaishen quest succeeded.")
        yield from Routines.Yield.wait(100)
    return _prepare


def _resolve_current_npc():
    if not state.current_npc_name:
        yield from _yield_skip_current_npc("no target NPC selected", error=True)
        return

    deadline = time.monotonic() + 5.0
    while time.monotonic() < deadline:
        match = _find_recorded_npc_match()
        if match is not None:
            agent_id, x, y = match
            state.npc_agent_id = int(agent_id)
            state.npc_xy = (x, y)
            state.set_status(
                f"Resolved {_current_target_label()} at ({state.npc_xy[0]:.0f}, {state.npc_xy[1]:.0f})."
            )
            yield from Routines.Yield.wait(100)
            return
        yield from Routines.Yield.wait(200)

    yield from _yield_skip_current_npc(
        f"could not find {_current_target_label()} in the current outpost",
        error=True,
    )


def _move_to_current_npc():
    if state.skip_current_npc:
        yield
        return
    if state.npc_agent_id == 0:
        yield from _yield_skip_current_npc("NPC was not resolved before movement", error=True)
        return

    approach_xy = state.current_route_points[0] if state.current_route_points else state.npc_xy
    approach_tolerance = 180.0
    npc_tolerance = 240.0
    state.set_status(f"Approaching {_current_target_label()} via the recorded stop.")

    deadline = time.monotonic() + (max(1000, int(state.move_timeout_ms)) / 1000.0)
    previous_approach_distance = float("inf")
    stagnant_ticks = 0
    while time.monotonic() < deadline:
        if _current_npc_dialog_is_ready():
            yield from Routines.Yield.wait(150)
            return

        try:
            player_xy = tuple(float(value) for value in Player.GetXY())
        except Exception:
            player_xy = (0.0, 0.0)

        approach_distance = _distance_xy(player_xy, approach_xy)
        npc_distance = _distance_to_current_npc()
        if approach_distance <= approach_tolerance or npc_distance <= npc_tolerance:
            yield from Routines.Yield.wait(150)
            return

        if approach_distance >= previous_approach_distance - 20.0:
            stagnant_ticks += 1
        else:
            stagnant_ticks = 0
        previous_approach_distance = approach_distance

        if stagnant_ticks < 4:
            Player.Move(float(approach_xy[0]), float(approach_xy[1]))
            yield from Routines.Yield.wait(250)
            continue

        yield from Routines.Yield.Player.ChangeTarget(state.npc_agent_id)
        yield from Routines.Yield.wait(100)
        yield from Routines.Yield.Player.InteractAgent(state.npc_agent_id)
        yield from Routines.Yield.wait(350)
        stagnant_ticks = 0

    yield from _yield_skip_current_npc(
        f"failed to approach '{_current_target_label()}'",
        error=True,
    )


def _interact_with_current_npc():
    if state.skip_current_npc:
        yield
        return
    if state.npc_agent_id == 0:
        yield from _yield_skip_current_npc("NPC target is missing before interact", error=True)
        return

    if _current_npc_dialog_is_ready():
        yield from Routines.Yield.wait(250)
        return

    state.set_status(f"Interacting with {_current_target_label()}.")
    deadline = time.monotonic() + 5.0
    interaction_attempts = 0
    while time.monotonic() < deadline:
        interaction_attempts += 1
        yield from Routines.Yield.Player.ChangeTarget(state.npc_agent_id)
        yield from Routines.Yield.wait(100)
        yield from Routines.Yield.Player.InteractAgent(state.npc_agent_id)
        settle_deadline = time.monotonic() + 1.2
        while time.monotonic() < settle_deadline:
            if _current_npc_dialog_is_ready():
                yield from Routines.Yield.wait(250)
                return
            yield from Routines.Yield.wait(100)

        if _dialog_is_open():
            state.set_status(
                f"{_current_target_label()}: stale dialog remained open after interact attempt {interaction_attempts}; retrying."
            )
        else:
            state.set_status(f"{_current_target_label()}: interact attempt {interaction_attempts} did not open dialog; retrying.")
        yield from Routines.Yield.wait(250)

    yield from _yield_skip_current_npc(f"dialog did not open for '{_current_target_label()}'", error=True)


def _resolve_first_offer_dialog():
    if state.skip_current_npc:
        yield
        return
    deadline = time.monotonic() + (max(1000, int(state.dialog_timeout_ms)) / 1000.0)
    confirmation_label = _normalize_dialog_label(state.confirmation_text)

    while time.monotonic() < deadline:
        if not _current_npc_dialog_is_ready():
            yield from Routines.Yield.wait(150)
            continue

        active_message = _active_dialog_message()
        rejection = _classify_zaishen_dialog_rejection(active_message)
        if rejection is not None:
            rejection_reason, retryable, counts_as_failure = rejection
            yield from _yield_skip_current_npc(
                f"{rejection_reason}; dialog says '{active_message}'",
                retryable=retryable,
                counts_as_failure=counts_as_failure,
            )
            return
        buttons = Dialog.get_active_dialog_buttons()
        state.last_choices = [
            f"{_button_text(button) or '<empty>'} [0x{button.dialog_id:X}]"
            for button in buttons
        ]
        visible_buttons = [
            button
            for button in buttons
            if int(getattr(button, "dialog_id", 0) or 0) != 0
            and not _is_decline_button_text(_button_text(button))
        ]
        non_confirmation_buttons = [
            button
            for button in visible_buttons
            if _normalize_dialog_label(_button_text(button)) != confirmation_label
        ]

        selected_button = None
        if non_confirmation_buttons:
            selected_button = non_confirmation_buttons[0]
            state.offer_is_confirmation_step = False
        elif visible_buttons:
            selected_button = visible_buttons[0]
            state.offer_is_confirmation_step = True

        if selected_button is not None:
            dialog_id = int(selected_button.dialog_id)
            state.first_offer_dialog_id = dialog_id
            state.offered_quest_name = _resolve_offered_quest_name(selected_button)
            if state.offer_is_confirmation_step:
                state.confirmation_dialog_id = dialog_id
                if state.offered_quest_name:
                    state.set_status(
                        f"Dialog opened directly at confirmation 0x{dialog_id:X}; inferred quest '{state.offered_quest_name}'."
                    )
                else:
                    state.set_status(f"Dialog opened directly at confirmation 0x{dialog_id:X}; quest name unavailable.")
            else:
                if state.offered_quest_name:
                    state.set_status(
                        f"Resolved first offered dialog 0x{state.first_offer_dialog_id:X} for '{state.offered_quest_name}'."
                    )
                else:
                    state.set_status(f"Resolved first offered dialog 0x{state.first_offer_dialog_id:X}.")
            yield from Routines.Yield.wait(250)
            return

        yield from Routines.Yield.wait(150)

    available = ", ".join(state.last_choices) if state.last_choices else "<none>"
    yield from _yield_skip_current_npc(
        f"could not resolve the first quest dialog offered by '{_current_target_label()}'. Available choices: {available}",
        error=True,
    )


def _skip_if_offered_quest_already_present():
    if state.skip_current_npc:
        yield
        return
    if not state.offered_quest_name:
        state.set_status(f"{_current_target_label()}: first offered dialog did not expose a quest name; duplicate guard is unavailable.")
        yield
        return

    target_name = _normalize_quest_name(state.offered_quest_name)
    if any(_normalize_quest_name(name) == target_name for name in state.last_quest_log_names):
        yield from _yield_skip_current_npc(
            f"quest '{state.offered_quest_name}' is already in the quest log",
            retryable=False,
            counts_as_failure=False,
        )
        return

    state.set_status(f"{_current_target_label()}: quest '{state.offered_quest_name}' is not in the quest log. Proceeding to accept it.")
    yield


def _send_first_offer_dialog():
    if state.skip_current_npc:
        yield
        return
    if state.offer_is_confirmation_step:
        state.set_status(f"{_current_target_label()}: dialog is already at confirmation; skipping the initial send.")
        yield
        return
    if state.first_offer_dialog_id == 0:
        yield from _yield_skip_current_npc("first offered dialog ID was not resolved", error=True)
        return

    state.set_status(f"Sending first offered dialog 0x{state.first_offer_dialog_id:X}.")
    Player.SendDialog(state.first_offer_dialog_id)
    yield from Routines.Yield.wait(POST_DIALOG_SEND_WAIT_MS)


def _resolve_confirmation_dialog():
    if state.skip_current_npc:
        yield
        return
    if state.offer_is_confirmation_step and state.confirmation_dialog_id != 0:
        state.set_status(f"Resolved confirmation dialog 0x{state.confirmation_dialog_id:X}.")
        yield
        return
    target_label = _normalize_dialog_label(state.confirmation_text)
    deadline = time.monotonic() + (max(1000, int(state.dialog_timeout_ms)) / 1000.0)

    while time.monotonic() < deadline:
        if not _current_npc_dialog_is_ready():
            yield from Routines.Yield.wait(150)
            continue

        active_message = _active_dialog_message()
        rejection = _classify_zaishen_dialog_rejection(active_message)
        if rejection is not None:
            rejection_reason, retryable, counts_as_failure = rejection
            yield from _yield_skip_current_npc(
                f"{rejection_reason}; dialog says '{active_message}'",
                retryable=retryable,
                counts_as_failure=counts_as_failure,
            )
            return
        buttons = Dialog.get_active_dialog_buttons()
        state.last_choices = [
            f"{_button_text(button) or '<empty>'} [0x{button.dialog_id:X}]"
            for button in buttons
        ]
        for button in buttons:
            if _normalize_dialog_label(_button_text(button)) == target_label and int(button.dialog_id) != 0:
                state.confirmation_dialog_id = int(button.dialog_id)
                state.set_status(f"Resolved confirmation dialog 0x{state.confirmation_dialog_id:X}.")
                yield
                return
        yield from Routines.Yield.wait(150)

    available = ", ".join(state.last_choices) if state.last_choices else "<none>"
    yield from _yield_skip_current_npc(
        f"could not find confirmation text '{state.confirmation_text}'. Available choices: {available}",
        error=True,
    )


def _send_confirmation_dialog():
    if state.skip_current_npc:
        yield
        return
    if state.confirmation_dialog_id == 0:
        yield from _yield_skip_current_npc("confirmation dialog ID was not resolved", error=True)
        return

    state.set_status(f"Sending confirmation dialog 0x{state.confirmation_dialog_id:X}.")
    Player.SendDialog(state.confirmation_dialog_id)
    yield from Routines.Yield.wait(POST_DIALOG_SEND_WAIT_MS)


def _verify_quest_added():
    if state.skip_current_npc:
        yield
        return
    target_name = _normalize_quest_name(state.offered_quest_name)
    if not target_name:
        state.record_quest_success()
        state.append_result(f"{_current_attempt_label()}: accepted quest flow but NPC did not expose a readable quest name for verification")
        state.set_status(f"{_current_attempt_label()}: accepted quest flow but verification name was unavailable.")
        yield
        return
    if not any(_normalize_quest_name(name) == target_name for name in state.last_quest_log_names):
        state.last_quest_log_names.append(state.offered_quest_name)
    state.record_quest_success()
    result = f"{_current_attempt_label()}: sent acceptance for '{state.offered_quest_name}'"
    state.append_result(result)
    state.set_status(result)
    yield


def _plan_final_retry_pass():
    state.current_pass_label = "initial"
    state.final_retry_targets = []

    if not state.retryable_failed_quest_names:
        state.set_status("Initial Zaishen pass finished with no retryable failures.")
        yield
        return

    if not state.successful_quest_names:
        state.set_status("Initial Zaishen pass had failures but no successful quest takes; skipping the final retry pass.")
        yield
        return

    state.final_retry_targets = [
        quest_name
        for quest_name in QUEST_TYPE_SEQUENCE
        if quest_name in state.retryable_failed_quest_names
    ]
    if not state.final_retry_targets:
        state.set_status("Initial Zaishen pass did not leave any failed quest types pending for the final retry pass.")
        yield
        return

    retry_labels = ", ".join(state.final_retry_targets)
    state.set_status(f"Initial Zaishen pass finished. Final retry pass scheduled for: {retry_labels}.")
    yield from Routines.Yield.wait(100)


def _finish_run():
    summary = ", ".join(state.completed_results) if state.completed_results else "No quest actions were recorded."
    yield from _yield_stop_with_status(f"Embark Beach Zaishen trio finished. {summary}")


def _create_bot_routine(bot_instance: Botting) -> None:
    bot_instance.States.AddHeader("Initialize")
    bot_instance.States.AddCustomState(_initialize_run, "Initialize run state")

    bot_instance.States.AddHeader("Travel to Embark Beach")
    bot_instance.Map.Travel(target_map_id=EMBARK_BEACH)
    bot_instance.Wait.ForTime(500)
    bot_instance.States.AddCustomState(_select_targets_for_current_spawn, "Select nearest Zaishen trio")

    for quest_name in QUEST_TYPE_SEQUENCE:
        bot_instance.States.AddHeader(f"Handle {quest_name}")
        bot_instance.States.AddCustomState(_make_prepare_npc(quest_name), f"Prepare {quest_name}")
        bot_instance.States.AddCustomState(_resolve_current_npc, f"Resolve {quest_name}")
        bot_instance.States.AddCustomState(_move_to_current_npc, f"Move to {quest_name}")
        bot_instance.States.AddCustomState(_interact_with_current_npc, f"Interact with {quest_name}")
        bot_instance.States.AddCustomState(_resolve_first_offer_dialog, f"Resolve first offered dialog for {quest_name}")
        bot_instance.States.AddCustomState(_skip_if_offered_quest_already_present, f"Skip {quest_name} if offered quest already exists")
        bot_instance.States.AddCustomState(_send_first_offer_dialog, f"Send first offered dialog for {quest_name}")
        bot_instance.States.AddCustomState(_resolve_confirmation_dialog, f"Resolve 'I can do that!' for {quest_name}")
        bot_instance.States.AddCustomState(_send_confirmation_dialog, f"Send confirmation for {quest_name}")
        bot_instance.States.AddCustomState(_verify_quest_added, f"Verify quest added for {quest_name}")

    bot_instance.States.AddHeader("Plan Final Retry Pass")
    bot_instance.States.AddCustomState(_plan_final_retry_pass, "Plan final retry pass")

    for quest_name in QUEST_TYPE_SEQUENCE:
        bot_instance.States.AddHeader(f"Retry {quest_name}")
        bot_instance.States.AddCustomState(_make_prepare_retry_npc(quest_name), f"Prepare retry {quest_name}")
        bot_instance.States.AddCustomState(_resolve_current_npc, f"Resolve retry {quest_name}")
        bot_instance.States.AddCustomState(_move_to_current_npc, f"Move retry {quest_name}")
        bot_instance.States.AddCustomState(_interact_with_current_npc, f"Interact retry {quest_name}")
        bot_instance.States.AddCustomState(_resolve_first_offer_dialog, f"Resolve retry first offered dialog for {quest_name}")
        bot_instance.States.AddCustomState(_skip_if_offered_quest_already_present, f"Skip retry {quest_name} if offered quest already exists")
        bot_instance.States.AddCustomState(_send_first_offer_dialog, f"Send retry first offered dialog for {quest_name}")
        bot_instance.States.AddCustomState(_resolve_confirmation_dialog, f"Resolve retry 'I can do that!' for {quest_name}")
        bot_instance.States.AddCustomState(_send_confirmation_dialog, f"Send retry confirmation for {quest_name}")
        bot_instance.States.AddCustomState(_verify_quest_added, f"Verify retry quest added for {quest_name}")

    bot_instance.States.AddHeader("Finish")
    bot_instance.States.AddCustomState(_finish_run, "Finish Zaishen trio")


def _draw_main_status() -> None:
    active_quests = state.last_quest_log_names
    config_error = state.config_error()

    PyImGui.text(f"Target map: {Map.GetMapName(EMBARK_BEACH)} ({EMBARK_BEACH})")
    if state.selected_cluster_name:
        PyImGui.text(f"Selected cluster: {state.selected_cluster_name}")
    else:
        PyImGui.text("Selected cluster: <pending>")
    if state.spawn_xy != (0.0, 0.0):
        PyImGui.text(f"Spawn position: ({state.spawn_xy[0]:.0f}, {state.spawn_xy[1]:.0f})")
    else:
        PyImGui.text("Spawn position: <pending>")
    PyImGui.text(f"Current NPC: {_current_target_label() if state.current_npc_name else '<pending>'}")
    if state.quest_targets:
        planned_order = " -> ".join(str(target.get("npc_name", "") or "NPC") for target in state.quest_targets)
        PyImGui.text_wrapped(f"Planned trio order: {planned_order}")
    else:
        PyImGui.text("Planned trio order: <pending>")
    PyImGui.text(f"Offered quest name: {state.offered_quest_name or '<pending>'}")
    PyImGui.separator()
    PyImGui.text_wrapped(f"Status: {state.last_status}")

    if state.first_offer_dialog_id:
        PyImGui.text(f"First offered dialog: 0x{state.first_offer_dialog_id:X}")
    else:
        PyImGui.text("First offered dialog: <none>")

    if state.confirmation_dialog_id:
        PyImGui.text(f"Resolved confirmation dialog: 0x{state.confirmation_dialog_id:X}")
    else:
        PyImGui.text("Resolved confirmation dialog: <none>")

    if config_error:
        PyImGui.separator()
        PyImGui.text_colored(f"Config issue: {config_error}", Color(255, 120, 120, 255).to_tuple_normalized())

    PyImGui.separator()
    PyImGui.text_wrapped(
        "The widget travels to Embark Beach, reads your actual spawn position, picks the nearest recorded Zaishen trio cluster, then handles that local trio in fixed order: "
        "Mission -> Bounty -> Vanquish. Each stop resolves the nearest matching live NPC by recorded name/model/position, reads the offered quest "
        "from the live dialog, compares that NPC-provided quest name against the current quest log, and only sends live dialog IDs when the quest is not already present. "
        "If one quest take fails while another one succeeds, the widget schedules one final retry pass for the failed quest types at the end."
    )
    if active_quests:
        preview = ", ".join(active_quests[:6])
        suffix = " ..." if len(active_quests) > 8 else ""
        PyImGui.text_wrapped(f"Quest log names: {preview}{suffix}")
    else:
        PyImGui.text("Quest log names: <none resolved yet>")

    if state.last_choices:
        PyImGui.separator()
        PyImGui.text("Last visible dialog choices:")
        for choice_label in state.last_choices[:6]:
            PyImGui.bullet_text(choice_label)

    if state.completed_results:
        PyImGui.separator()
        PyImGui.text("Completed results:")
        for result in state.completed_results[-6:]:
            PyImGui.bullet_text(result)


def _draw_settings() -> None:
    state.confirmation_text = PyImGui.input_text("Confirmation text", state.confirmation_text, 128)
    state.move_timeout_ms = PyImGui.input_int("Move timeout (ms)", state.move_timeout_ms)
    state.dialog_timeout_ms = PyImGui.input_int("Dialog timeout (ms)", state.dialog_timeout_ms)
    state.move_timeout_ms = max(1000, int(state.move_timeout_ms))
    state.dialog_timeout_ms = max(1000, int(state.dialog_timeout_ms))

    PyImGui.separator()
    PyImGui.text_wrapped("Examples")
    PyImGui.bullet_text("The widget does not require a quest ID, offer dialog ID, or quest name.")
    PyImGui.bullet_text("It always travels to Embark Beach, selects the nearest recorded Zaishen trio for the current spawn, and handles the trio in fixed order: Mission -> Bounty -> Vanquish.")
    PyImGui.bullet_text("The duplicate guard uses the label or catalog text of each NPC's first live offered dialog choice.")
    PyImGui.bullet_text("If at least one quest take succeeds, any failed quest types get one final retry pass at the end.")


def _draw_help() -> None:
    PyImGui.text_wrapped(
        "Start the widget in any outpost or explorable area. It will travel to Embark Beach, detect which recorded Zaishen trio is nearest to the actual zone-in spawn, "
        "then move through that local trio in fixed order: Mission -> Bounty -> Vanquish. It interacts, sends the first live dialog ID offered by each NPC, then resolves and sends the live choice whose text matches the confirmation text."
    )
    PyImGui.separator()
    PyImGui.text_wrapped(
        "The duplicate guard reads the offered quest name from the live button text first, then falls back to dialog catalog/body text when the NPC opens "
        "directly on the confirmation choice. If that quest name is already present in the quest log, that NPC is skipped and the widget continues to the next NPC in the selected local trio."
    )
    PyImGui.separator()
    PyImGui.text_wrapped(
        "When one quest take fails but at least one other quest take succeeds during the same run, the widget adds one final retry pass at the end for the failed quest types."
    )


bot.SetMainRoutine(_create_bot_routine)
bot.UI.override_draw_config(_draw_settings)
bot.UI.override_draw_help(_draw_help)


def tooltip():
    PyImGui.begin_tooltip()
    title_color = Color(255, 200, 100, 255)
    ImGui.push_font("Regular", 20)
    PyImGui.text_colored(MODULE_NAME, title_color.to_tuple_normalized())
    ImGui.pop_font()
    PyImGui.spacing()
    PyImGui.separator()
    PyImGui.text("Travels to Embark Beach, picks the nearest recorded")
    PyImGui.text("Zaishen trio for the current spawn, and uses the live")
    PyImGui.text("dialog flow to confirm each quest with 'I can do that!'.")
    PyImGui.end_tooltip()


def main():
    try:
        if not Routines.Checks.Map.MapValid():
            return

        if Routines.Checks.Map.IsMapReady() and Routines.Checks.Party.IsPartyLoaded():
            bot.Update()
            if state.stop_requested:
                bot.Stop()
                state.stop_requested = False
            bot.UI.draw_window(icon_path=MODULE_ICON, additional_ui=_draw_main_status)
    except Exception as exc:
        Py4GW.Console.Log(
            MODULE_NAME,
            f"Unexpected error: {exc}",
            Py4GW.Console.MessageType.Error,
        )


if __name__ == "__main__":
    main()
