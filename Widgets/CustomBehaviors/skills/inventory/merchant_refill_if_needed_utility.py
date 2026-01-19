from enum import Enum
import random
from re import DEBUG
from typing import Any, Generator, override

import PyImGui

from Py4GWCoreLib import GLOBAL_CACHE, AgentArray, ItemArray, Routines, Range, Map, Agent, Player
from Py4GWCoreLib.Pathing import AutoPathing
from Py4GWCoreLib.Py4GWcorelib import Utils
from Widgets.CustomBehaviors.primitives import constants
from Widgets.CustomBehaviors.primitives.behavior_state import BehaviorState
from Widgets.CustomBehaviors.primitives.bus.event_message import EventMessage
from Widgets.CustomBehaviors.primitives.bus.event_type import EventType
from Widgets.CustomBehaviors.primitives.helpers import custom_behavior_helpers
from Widgets.CustomBehaviors.primitives.helpers.behavior_result import BehaviorResult
from Widgets.CustomBehaviors.primitives.scores.comon_score import CommonScore
from Widgets.CustomBehaviors.primitives.scores.score_static_definition import ScoreStaticDefinition
from Widgets.CustomBehaviors.primitives.skills.custom_skill import CustomSkill
from Widgets.CustomBehaviors.primitives.skills.custom_skill_utility_base import CustomSkillUtilityBase
from Widgets.CustomBehaviors.primitives.skills.utility_skill_execution_strategy import UtilitySkillExecutionStrategy
from Widgets.CustomBehaviors.primitives.skills.utility_skill_typology import UtilitySkillTypology
from Widgets.CustomBehaviors.primitives.bus.event_bus import EventBus

class MerchantType(Enum):
    MERCHANT = 1
    RUNE_TRADER = 2
    RARE_MATERIAL_TRADER = 3
    CRAFTING_MATERIAL_TRADER = 4

class MerchantRefillIfNeededUtility(CustomSkillUtilityBase):
    def __init__(self,
    event_bus: EventBus,
    current_build: list[CustomSkill],
    ) -> None:

        super().__init__(
            event_bus=event_bus,
            skill=CustomSkill("merchant_refill_if_needed_utility"),
            in_game_build=current_build,
            score_definition=ScoreStaticDefinition(CommonScore.INVENTORY.value),
            allowed_states=[BehaviorState.IDLE],
            utility_skill_typology=UtilitySkillTypology.INVENTORY,
            execution_strategy=UtilitySkillExecutionStrategy.EXECUTE_THROUGH_THE_END) # or stuck detection will make us reset each 5s...

        self.score_definition: ScoreStaticDefinition = ScoreStaticDefinition(CommonScore.INVENTORY.value)
        self.should_visit_merchant:bool = False
        self.should_visit_rune_trader:bool = False
        self.should_visit_rare_material_trader:bool = False
        self.should_visit_crafting_material_trader:bool = False

        self.should_visit_npc_config:dict[MerchantType, bool] = {
            MerchantType.MERCHANT: True,
            MerchantType.RUNE_TRADER: True,
            MerchantType.RARE_MATERIAL_TRADER: True,
            MerchantType.CRAFTING_MATERIAL_TRADER: True,
        }

        self.visit_duration_in_seconds_config:dict[MerchantType, int] = {
            MerchantType.MERCHANT: 5,
            MerchantType.RUNE_TRADER: 5,
            MerchantType.RARE_MATERIAL_TRADER: 10,
            MerchantType.CRAFTING_MATERIAL_TRADER: 3,
        }

        self.npc_visited:dict[MerchantType, bool] = {
            MerchantType.MERCHANT: False,
            MerchantType.RUNE_TRADER: False,
            MerchantType.RARE_MATERIAL_TRADER: False,
            MerchantType.CRAFTING_MATERIAL_TRADER: False,
        }

        self.event_bus.subscribe(EventType.MAP_CHANGED, self.map_changed, subscriber_name=self.custom_skill.skill_name)
    
    def map_changed(self, message: EventMessage) -> Generator[Any, Any, Any]:
        self.npc_visited[MerchantType.MERCHANT] = False
        self.npc_visited[MerchantType.RUNE_TRADER] = False
        self.npc_visited[MerchantType.RARE_MATERIAL_TRADER] = False
        self.npc_visited[MerchantType.CRAFTING_MATERIAL_TRADER] = False
        yield

    @override
    def are_common_pre_checks_valid(self, current_state: BehaviorState) -> bool:
        if self.allowed_states is not None and current_state not in self.allowed_states: return False
        if not Map.IsOutpost(): return False
        if not Map.IsGuildHall(): return False # be discret...
        return True

    def _is_merchant_agent(self, agent_id: int) -> bool:
        """Check if the agent is a merchant by checking for merchant tags in multiple languages."""
        merchant_tags = ['Merchant', 'Marchand', 'Kauffrau']
        agent_name = Agent.GetNameByID(agent_id)
        return any(merchant_tag in agent_name for merchant_tag in merchant_tags)
    
    def _is_rune_trader_agent(self, agent_id: int) -> bool:
        merchant_tags = ['Rune Trader']
        agent_name = Agent.GetNameByID(agent_id)
        return any(merchant_tag in agent_name for merchant_tag in merchant_tags)
    
    def _is_rare_material_trader_agent(self, agent_id: int) -> bool:
        merchant_tags = ['Rare Material Trader']
        agent_name = Agent.GetNameByID(agent_id)
        return any(merchant_tag in agent_name for merchant_tag in merchant_tags)
    
    def _is_crafter_material_trader_agent(self, agent_id: int) -> bool:
        merchant_tags = ['Crafting Material Trader']
        agent_name = Agent.GetNameByID(agent_id)
        return any(merchant_tag in agent_name for merchant_tag in merchant_tags)

    def _get_target(self, merchant_type: MerchantType) -> int | None:
        agent_ids = AgentArray.GetNPCMinipetArray()
        agent_ids = AgentArray.Filter.ByDistance(agent_ids, Player.GetXY(), Range.Compass.value)
        agent_ids = AgentArray.Filter.ByCondition(agent_ids, lambda agent_id: Agent.IsAlive(agent_id) and Agent.IsValid(agent_id))

        if merchant_type == MerchantType.MERCHANT:
            agent_ids = AgentArray.Filter.ByCondition(agent_ids, self._is_merchant_agent)
        if merchant_type == MerchantType.RUNE_TRADER:
            agent_ids = AgentArray.Filter.ByCondition(agent_ids, self._is_rune_trader_agent)
        if merchant_type == MerchantType.RARE_MATERIAL_TRADER:
            agent_ids = AgentArray.Filter.ByCondition(agent_ids, self._is_rare_material_trader_agent)
        if merchant_type == MerchantType.CRAFTING_MATERIAL_TRADER:
            agent_ids = AgentArray.Filter.ByCondition(agent_ids, self._is_crafter_material_trader_agent)

        if len(agent_ids) == 0: return None
        return agent_ids[0]
        
    @override
    def _evaluate(self, current_state: BehaviorState, previously_attempted_skills: list[CustomSkill]) -> float | None:
        if self.should_visit_npc_config[MerchantType.MERCHANT] and not self.npc_visited[MerchantType.MERCHANT]: return self.score_definition.get_score()
        if self.should_visit_npc_config[MerchantType.RUNE_TRADER] and not self.npc_visited[MerchantType.RUNE_TRADER]: return self.score_definition.get_score()
        if self.should_visit_npc_config[MerchantType.RARE_MATERIAL_TRADER] and not self.npc_visited[MerchantType.RARE_MATERIAL_TRADER]: return self.score_definition.get_score()
        if self.should_visit_npc_config[MerchantType.CRAFTING_MATERIAL_TRADER] and not self.npc_visited[MerchantType.CRAFTING_MATERIAL_TRADER]: return self.score_definition.get_score()
        return None

    def _visit(self, merchant_type: MerchantType) -> Generator[Any, None, None]:

        if not self.should_visit_npc_config[merchant_type]: return
        if self.npc_visited[merchant_type]: return

        target_agent_id = self._get_target(merchant_type)
        if target_agent_id is None: return

        print(f"Visiting {merchant_type.name}...")
        target_position : tuple[float, float] = Agent.GetXY(target_agent_id)
        if Utils.Distance(target_position, Player.GetXY()) > 150:
            path3d = yield from AutoPathing().get_path_to(target_position[0], target_position[1], smooth_by_los=True, margin=100.0, step_dist=300.0)
            path2d:list[tuple[float, float]]  = [(x, y) for (x, y, *_ ) in path3d]

            yield from Routines.Yield.Movement.FollowPath(
                    path_points= path2d,
                    custom_exit_condition=lambda: Agent.IsDead(Player.GetAgentID()),
                    tolerance=150,
                    log=constants.DEBUG,
                    timeout=10_000,
                    progress_callback=lambda progress: print(f"FollowPath merchant_refill_if_needed_utility: progress: {progress}") if constants.DEBUG else None,
                    custom_pause_fn=lambda: False)

        print(f"Merchant reached.")
        Player.Interact(target_agent_id, call_target=True)
        visit_duration_in_seconds = self.visit_duration_in_seconds_config[merchant_type]
        yield from custom_behavior_helpers.Helpers.wait_for(visit_duration_in_seconds * 1000)
        self.npc_visited[merchant_type] = True

    @override
    def _execute(self, state: BehaviorState) -> Generator[Any, None, BehaviorResult]:
        
        if not self.npc_visited[MerchantType.MERCHANT]:
            yield from self._visit(MerchantType.MERCHANT)
            return BehaviorResult.ACTION_PERFORMED
        if not self.npc_visited[MerchantType.RUNE_TRADER]:
            yield from self._visit(MerchantType.RUNE_TRADER)
            return BehaviorResult.ACTION_PERFORMED
        if not self.npc_visited[MerchantType.RARE_MATERIAL_TRADER]:
            yield from self._visit(MerchantType.RARE_MATERIAL_TRADER)
            return BehaviorResult.ACTION_PERFORMED
        if not self.npc_visited[MerchantType.CRAFTING_MATERIAL_TRADER]:
            yield from self._visit(MerchantType.CRAFTING_MATERIAL_TRADER)
            return BehaviorResult.ACTION_PERFORMED

        return BehaviorResult.ACTION_SKIPPED

    @override
    def customized_debug_ui(self, current_state: BehaviorState) -> None:
        """Display debug UI for merchant refill utility"""

        if PyImGui.collapsing_header("Merchant Refill Status", PyImGui.TreeNodeFlags.DefaultOpen):

            # Configuration section
            PyImGui.text_colored("Configuration:", (1.0, 1.0, 0.0, 1.0))  # Yellow
            PyImGui.separator()

            if PyImGui.begin_table("merchant_config", 3, int(PyImGui.TableFlags.Borders | PyImGui.TableFlags.RowBg)):
                PyImGui.table_setup_column("Merchant Type")
                PyImGui.table_setup_column("Should Visit")
                PyImGui.table_setup_column("Visit Duration (s)")
                PyImGui.table_headers_row()

                for merchant_type in MerchantType:
                    PyImGui.table_next_row()
                    PyImGui.table_next_column()
                    PyImGui.text(merchant_type.name.replace('_', ' ').title())

                    PyImGui.table_next_column()
                    should_visit = self.should_visit_npc_config[merchant_type]
                    new_value = PyImGui.checkbox(f"##should_visit_{merchant_type.name}", should_visit)
                    if new_value != should_visit:
                        self.should_visit_npc_config[merchant_type] = new_value

                    PyImGui.table_next_column()
                    PyImGui.text(str(self.visit_duration_in_seconds_config[merchant_type]))

                PyImGui.end_table()

            PyImGui.spacing()

            # Status section
            PyImGui.text_colored("Visit Status:", (1.0, 1.0, 0.0, 1.0))  # Yellow
            PyImGui.separator()

            if PyImGui.begin_table("merchant_status", 2, int(PyImGui.TableFlags.Borders | PyImGui.TableFlags.RowBg)):
                PyImGui.table_setup_column("Merchant Type")
                PyImGui.table_setup_column("Visited")
                PyImGui.table_headers_row()

                for merchant_type in MerchantType:
                    PyImGui.table_next_row()
                    PyImGui.table_next_column()
                    PyImGui.text(merchant_type.name.replace('_', ' ').title())

                    PyImGui.table_next_column()
                    visited = self.npc_visited[merchant_type]
                    if visited:
                        PyImGui.text_colored("✓ Visited", (0.0, 1.0, 0.0, 1.0))  # Green
                    else:
                        PyImGui.text_colored("✗ Not Visited", (1.0, 0.5, 0.0, 1.0))  # Orange

                PyImGui.end_table()

            PyImGui.spacing()

            # Additional debug info
            PyImGui.text_colored("Debug Info:", (1.0, 1.0, 0.0, 1.0))  # Yellow
            PyImGui.separator()
            PyImGui.bullet_text(f"Is Outpost: {Map.IsOutpost()}")
            PyImGui.bullet_text(f"Is Guild Hall: {Map.IsGuildHall()}")

            # Show nearby merchants
            PyImGui.spacing()
            PyImGui.text_colored("Nearby Merchants:", (1.0, 1.0, 0.0, 1.0))  # Yellow
            PyImGui.separator()

            for merchant_type in MerchantType:
                agent_id = self._get_target(merchant_type)
                if agent_id is not None:
                    target_pos = Agent.GetXY(agent_id)
                    player_pos = Player.GetXY()
                    distance = Utils.Distance(target_pos, player_pos)
                    PyImGui.bullet_text(f"{merchant_type.name}: (ID: {agent_id}, dist: {distance:.0f})")
                else:
                    PyImGui.bullet_text(f"{merchant_type.name}: Not found")
