from typing import cast
from Py4GWCoreLib import AgentArray, Agent, Range, Utils
from Widgets.CustomBehaviors.primitives.helpers.sortable_agent_data import SortableAgentData
from Widgets.CustomBehaviors.primitives.parties.memory_cache_manager import MemoryCacheManager

class CustomTargeting:

    _instance = None  # Singleton instance

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(CustomTargeting, cls).__new__(cls)
        return cls._instance

    # ----------------------------- Cache Key Builder -----------------------------

    @staticmethod
    def __round_pos(pos: tuple[float, float]) -> tuple[int, int]:
        """Round position to reduce cache key variations (positions within ~10 units share cache)."""
        return (int(pos[0] / 10) * 10, int(pos[1] / 10) * 10)

    @classmethod
    def __build_combined_enemy_targets_key(
        cls,
        source_pos: tuple[float, float],
        within_range: float,
        leader_agent_id: int | None,
        include_aggressive_further: bool,
        is_alive: bool | None
    ) -> str:
        rounded = cls.__round_pos(source_pos)
        leader_part = f"leader:{leader_agent_id}" if leader_agent_id is not None else "leader:none"
        aggressive_part = f"aggr:{include_aggressive_further}"
        alive_part = f"alive:{is_alive}"
        return f"combined|pos:{rounded[0]},{rounded[1]}|range:{within_range:.0f}|{leader_part}|{aggressive_part}|{alive_part}"

    # ----------------------------- Agent Data Builder -----------------------------

    @staticmethod
    def __build_sortable_agent_data(agent_id: int, source_pos: tuple[float, float]) -> SortableAgentData:
        """Build a SortableAgentData object for the given agent."""
        agent_pos = Agent.GetXY(agent_id)
        return SortableAgentData(
            agent_id=agent_id,
            distance_from_player=Utils.Distance(agent_pos, source_pos),
            hp=Agent.GetHealth(agent_id),
            is_caster=Agent.IsCaster(agent_id),
            is_melee=Agent.IsMelee(agent_id),
            is_martial=Agent.IsMartial(agent_id),
            enemy_quantity_within_range=0,  # Computed separately if needed
            agent_quantity_within_range=0,  # Computed separately if needed
            energy=0.0  # Computed separately if needed
        )

    def refresh(self):
        """Clear all cached data. Call this at the start of each frame/tick."""
        MemoryCacheManager().refresh()

    # ----------------------------- Private Helper Methods -----------------------------

    def __get_leader_targets(self, leader_agent_id: int, within_range: float) -> list[SortableAgentData]:
        """
        Get enemies within range of the party leader.

        :param leader_agent_id: The agent ID of the party leader
        :param within_range: Maximum distance from leader
        :return: List of SortableAgentData for enemies within range of leader
        """
        leader_pos = Agent.GetXY(leader_agent_id)
        all_enemies = AgentArray.GetEnemyArray()
        leader_target_ids = AgentArray.Filter.ByDistance(all_enemies, leader_pos, within_range)
        return [
            self.__build_sortable_agent_data(agent_id, leader_pos)
            for agent_id in leader_target_ids
        ]

    def __get_aggressive_enemies_further(
            self,
            source_pos: tuple[float, float],
            extended_range: float | None = None
    ) -> list[SortableAgentData]:
        """
        Get aggressive enemies that are a bit further away.
        Default range is Range.Spellcast.value * 1.5

        :param source_pos: Source position to measure distance from
        :param extended_range: Optional custom range (defaults to Spellcast * 1.5)
        :return: List of SortableAgentData for aggressive enemies
        """
        if extended_range is None:
            extended_range = Range.Spellcast.value * 1.5

        all_enemies = AgentArray.GetEnemyArray()
        further_agent_ids = AgentArray.Filter.ByDistance(all_enemies, source_pos, extended_range)
        aggressive_agent_ids = AgentArray.Filter.ByCondition(further_agent_ids, lambda agent_id: Agent.IsAggressive(agent_id))
        
        return [self.__build_sortable_agent_data(agent_id, source_pos) for agent_id in aggressive_agent_ids]

    def __get_enemies_by_distance(
            self,
            source_pos: tuple[float, float],
            within_range: float
    ) -> list[SortableAgentData]:
        """
        Get enemies within range of a position.

        :param source_pos: Source position to measure distance from
        :param within_range: Maximum distance
        :return: List of SortableAgentData for enemies within range
        """
        all_enemies = AgentArray.GetEnemyArray()
        enemy_ids_in_range = AgentArray.Filter.ByDistance(all_enemies, source_pos, within_range)
        return [self.__build_sortable_agent_data(agent_id, source_pos) for agent_id in enemy_ids_in_range]

    # ----------------------------- Combined Helpers -----------------------------

    def get_combined_enemy_targets(
            self,
            source_pos: tuple[float, float],
            within_range: float,
            leader_agent_id: int | None = None,
            include_aggressive_further: bool = True,
            is_alive: bool | None = None
    ) -> list[SortableAgentData]:
        """
        Get combined list of enemies from multiple sources (cached).
        This combines:
        - Enemies within range of source position
        - Enemies within range of party leader (if provided and different from player)
        - Aggressive enemies a bit further away (if enabled)

        :param source_pos: Source position (usually player position)
        :param within_range: Base range to search for enemies
        :param leader_agent_id: Optional party leader agent ID
        :param include_aggressive_further: Whether to include aggressive enemies further away
        :param is_alive: Whether to filter for alive agents only (default: True)
        :return: Deduplicated list of SortableAgentData
        """
        cache_key = self.__build_combined_enemy_targets_key(
            source_pos, within_range, leader_agent_id, include_aggressive_further, is_alive
        )

        # Check cache first
        cached = MemoryCacheManager().get(cache_key)
        if cached is not None:
            return cast(list[SortableAgentData], cached)

        # Compute the result
        agents: list[SortableAgentData] = list(self.__get_enemies_by_distance(source_pos, within_range))

        # Add leader targets if provided
        if leader_agent_id is not None:
            leader_targets = self.__get_leader_targets(leader_agent_id, within_range)
            agents.extend(leader_targets)

        # Add aggressive enemies further away
        if include_aggressive_further:
            aggressive_further = self.__get_aggressive_enemies_further(source_pos)
            agents.extend(aggressive_further)

        # Deduplicate by agent_id
        seen_ids: set[int] = set()
        unique_agents: list[SortableAgentData] = []
        for agent in agents:
            if agent.agent_id not in seen_ids:
                seen_ids.add(agent.agent_id)
                unique_agents.append(agent)

        # Filter alive if requested
        if is_alive:
            unique_agents = [agent for agent in unique_agents if Agent.IsAlive(agent.agent_id)]

        # Store in cache
        MemoryCacheManager().set(cache_key, unique_agents)

        return unique_agents


