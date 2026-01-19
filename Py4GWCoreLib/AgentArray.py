import PyAgent

from .Player import *

from .Py4GWcorelib import Utils
from .enums_src.GameData_enums import Allegiance
from .Context import GWContext
from typing import Callable
from .native_src.context.AgentContext import AgentStruct


class AgentArray:
    #region Agent
    @staticmethod
    def GetAgentArray() -> list[int]:
        """Purpose: Get the unfiltered full agent array."""
        agent_array_ctx = GWContext.AgentArray.GetContext()
        if not agent_array_ctx:
            return []

        agent_array = agent_array_ctx.GetAgentArray()
        
        return agent_array
    
    #region Ally
    @staticmethod
    def GetAllyArray() -> list[int]:
        """Purpose: Get the unfiltered full agent array."""
        agent_array_ctx = GWContext.AgentArray.GetContext()
        if not agent_array_ctx:
            return []

        agent_array = agent_array_ctx.GetAllyArray()
        return agent_array
    
    #region Neutral
    @staticmethod
    def GetNeutralArray() -> list[int]:
        """Purpose: Retrieve the agent array pre filtered by neutrals."""
        agent_array_ctx = GWContext.AgentArray.GetContext()
        if not agent_array_ctx:
            return []
        agent_array = agent_array_ctx.GetNeutralArray()
        return agent_array
    
    #region Enemy
    @staticmethod
    def GetEnemyArray() -> list[int]:
        """Purpose: Retrieve the agent array pre filtered by enemies."""
        agent_array_ctx = GWContext.AgentArray.GetContext()
        if not agent_array_ctx:
            return []
        agent_array = agent_array_ctx.GetEnemyArray()
        return agent_array

    #region SpiritPet
    @staticmethod
    def GetSpiritPetArray() -> list[int]:
        """Purpose: Retrieve the agent array pre filtered by spirit & pets."""
        agent_array_ctx = GWContext.AgentArray.GetContext()
        if not agent_array_ctx:
            return []
        agent_array = agent_array_ctx.GetSpiritPetArray()
        return agent_array
    
    
    #region Minion
    @staticmethod
    def GetMinionArray() -> list[int]:
        """Purpose: Retrieve the agent array pre filtered by minions."""
        agent_array_ctx = GWContext.AgentArray.GetContext()
        if not agent_array_ctx:
            return []
        agent_array = agent_array_ctx.GetMinionArray()
        return agent_array
    
    #region NPCMinipet
    @staticmethod
    def GetNPCMinipetArray() -> list[int]:
        """Purpose: Retrieve the agent array pre filtered by NPC & minipets."""
        agent_array_ctx = GWContext.AgentArray.GetContext()
        if not agent_array_ctx:
            return []
        agent_array = agent_array_ctx.GetNPCMinipetArray()
        return agent_array
    
    #region Item
    @staticmethod
    def GetItemArray() -> list[int]:
        """Purpose: Retrieve the agent array pre-filtered by items."""
        agent_array_ctx = GWContext.AgentArray.GetContext()
        if not agent_array_ctx:
            return []
        agent_array = agent_array_ctx.GetItemAgentArray()
        return agent_array
    
    #region OwnedItem
    @staticmethod
    def GetOwnedItemArray() -> list[int]:
        """Purpose: Retrieve the agent array pre filtered by owned items."""
        agent_array_ctx = GWContext.AgentArray.GetContext()
        if not agent_array_ctx:
            return []
        agent_array = agent_array_ctx.GetOwnedItemAgentArray()
        return agent_array
    

    #region Gadget
    @staticmethod
    def GetGadgetArray() -> list[int]:
        """Purpose: Retrieve the agent array pre filtered by gadgets."""
        agent_array_ctx = GWContext.AgentArray.GetContext()
        if not agent_array_ctx:
            return []
        agent_array = agent_array_ctx.GetGadgetAgentArray()
        return agent_array
    
    
    #region DeadAlly
    @staticmethod
    def GetDeadAllyArray() -> list[int]:
        """Purpose: Retrieve the dead ally agent array."""
        agent_array_ctx = GWContext.AgentArray.GetContext()
        if not agent_array_ctx:
            return []
        agent_array = agent_array_ctx.GetDeadAllyArray()
        return agent_array
    
    
    #region DeadEnemy
    @staticmethod
    def GetDeadEnemyArray() -> list[int]:
        """Purpose: Retrieve the dead enemy agent array."""
        agent_array_ctx = GWContext.AgentArray.GetContext()
        if not agent_array_ctx:
            return []
        agent_array = agent_array_ctx.GetDeadEnemyArray()
        return agent_array
    
    @staticmethod
    def GetAgentByID(agent_id: int) -> AgentStruct | None:
        """Purpose: Get an agent by its AgentID."""
        agent_array_ctx = GWContext.AgentArray.GetContext()
        if not agent_array_ctx:
            return None
        
        agent = agent_array_ctx.GetAgentByID(agent_id)
        return agent
        
    #region
    
    #region Manipulation
    class Manipulation:
        @staticmethod
        def Merge(array1, array2):
            """
            Merges two agent arrays, removing duplicates (union).

            Args:
                array1 (list[int]): First agent array.
                array2 (list[int]): Second agent array.

            Returns:
                list[int]: A merged array with unique agent IDs.

            Example:
                merged_agents = Filters.MergeAgentArrays(array1, array2)
            """
            return list(set(array1).union(set(array2)))

        @staticmethod
        def Subtract(array1, array2):
            """
            Removes all elements in array2 from array1 and returns the resulting list.

            This function computes the set difference between the two input arrays,

            Args:
                array1 (list[int]): The base list from which elements will be removed.
                array2 (list[int]): The list of elements to remove from `array1`.

            Returns:
                list[int]: A new list containing elements of `array1` that are not in `array2`.
            """
            return list(set(array1) - set(array2))


        @staticmethod
        def Intersect(array1, array2):
            """
            Returns agents that are present in both arrays (intersection).

            Args:
                array1 (list[int]): First agent array.
                array2 (list[int]): Second agent array.

            Returns:
                list[int]: Agents present in both arrays.

            Example:
                intersected_agents = Filters.IntersectAgentArrays(array1, array2)
            """
            return list(set(array1).intersection(set(array2)))

    #region Sort
    class Sort:
        @staticmethod
        def ByAttribute(agent_array, attribute, descending=False):
            """
            Sorts agents by a specific attribute (e.g., health, distance, etc.).
            sorted_agents_by_health = Sort.ByAttribute(agent_array, 'GetHealth', descending=True)
            """
            if agent_array is None:
                return []
            return AgentArray.Sort.ByCondition(
                agent_array,
                condition_func=lambda agent_id: getattr(Agent, attribute)(agent_id),
                reverse=descending
            )

        @staticmethod
        def ByCondition(agent_array, condition_func, reverse=False):
            """
            Sorts agents based on a custom condition function.
            sorted_agents_by_custom = Sort.ByCondition(
                agent_array,
                condition_func=lambda agent_id: (Utils.Distance(Agent.GetXY(agent_id), (100, 200)), Agent.GetHealth(agent_id))
            )
            """
            if agent_array is None:
                return []
            return sorted(agent_array, key=condition_func, reverse=reverse)


        @staticmethod
        def ByDistance(agent_array, pos, descending=False):
            from .GlobalCache import GLOBAL_CACHE
            """
            Sorts agents by their distance to a given (x, y) position.
            sorted_agents_by_distance = Sort.ByDistance(agent_array, (100, 200))
            """
            if agent_array is None:
                return []
            return AgentArray.Sort.ByCondition(
                agent_array,
                condition_func=lambda agent_id: Utils.Distance(
                    Agent.GetXY(agent_id),
                    (pos[0], pos[1])
                ),
                reverse=descending
            )

        @staticmethod
        def ByHealth(agent_array, descending=False):
            from .GlobalCache import GLOBAL_CACHE
            """
            Sorts agents by their health (HP).
            sorted_agents_by_health_desc = Sort.ByHealth(agent_array, descending=True)
            """
            if agent_array is None:
                return []
            return AgentArray.Sort.ByCondition(
                agent_array,
                condition_func=lambda agent_id: Agent.GetHealth(agent_id),
                reverse=descending
            )
    #region Filter
    class Filter:
        @staticmethod
        def ByAttribute(agent_array, attribute, condition_func=None, negate=False):
            """
            Filters agents by an attribute, with support for negation.
            moving_agents = AgentArray.Filter.ByAttribute(agent_array, 'IsMoving')
            """
            if agent_array is None:
                return []
            def attribute_filter(agent_id):
                if hasattr(Agent, attribute):
                    # Fetch the attribute value dynamically
                    attr_value = getattr(Agent, attribute)(agent_id)

                    # Apply the condition function or return the attribute directly
                    result = condition_func(attr_value) if condition_func else bool(attr_value)

                    # Apply negation if required
                    return not result if negate else result

                return False if not negate else True

            return AgentArray.Filter.ByCondition(agent_array, attribute_filter)


        @staticmethod
        def ByCondition(agent_array, filter_func):
            """
            Filters the agent array using a custom filter function.\
            moving_nearby_agents = AgentArray.Filter.ByCondition(
                agent_array,
                lambda agent_id: Agent.IsMoving(agent_id) and Utils.Distance(Agent.GetXY(agent_id), (100, 200)) <= 500
            )
            """
            if agent_array is None:
                return []
            return list(filter(filter_func, agent_array))


        @staticmethod
        def ByDistance(agent_array, pos, max_distance, negate=False):
            from .GlobalCache import GLOBAL_CACHE
            """
            Filters agents based on their distance from a given position.
            agents_within_range = AgentArray.Filter.ByDistance(agent_array, (100, 200), 500)
            """
            if agent_array is None:
                return []
            def distance_filter(agent_id):
                agent_x, agent_y = Agent.GetXY(agent_id)
                distance = Utils.Distance((agent_x, agent_y), (pos[0], pos[1]))
                return (distance > max_distance) if negate else (distance <= max_distance)

            return AgentArray.Filter.ByCondition(agent_array, distance_filter)

    #region Routines
    class Routines:
            @staticmethod
            def DetectLargestAgentCluster(agent_array, cluster_radius):
                from .GlobalCache import GLOBAL_CACHE
                from .Py4GWcorelib import Utils

                """
                Detects the largest cluster of agents based on proximity and returns
                the agent ID closest to the cluster's center of mass.

                Args:
                    agent_array (list[int]): List of agent IDs.
                    cluster_radius (float): Maximum distance between agents to consider them in the same cluster.

                Returns:
                    int: The ID of the agent closest to the center of the largest cluster.
                """

                if not agent_array:
                    return 0  # no agents

                cluster_radius_sq = cluster_radius ** 2

                def is_in_radius(agent1, agent2):
                    x1, y1 = Agent.GetXY(agent1)
                    x2, y2 = Agent.GetXY(agent2)
                    dx, dy = x1 - x2, y1 - y2
                    return (dx * dx + dy * dy) <= cluster_radius_sq

                # --- Group agents into clusters ---
                unvisited = set(agent_array)
                clusters = []

                while unvisited:
                    current = unvisited.pop()
                    cluster = [current]
                    stack = [current]

                    while stack:
                        node = stack.pop()
                        neighbors = [a for a in list(unvisited) if is_in_radius(node, a)]
                        for n in neighbors:
                            unvisited.remove(n)
                            cluster.append(n)
                            stack.append(n)

                    clusters.append(cluster)

                # --- Find largest cluster ---
                largest_cluster = max(clusters, key=len)

                # --- Compute cluster center (average XY) ---
                total_x = total_y = 0
                for agent_id in largest_cluster:
                    x, y = Agent.GetXY(agent_id)
                    total_x += x
                    total_y += y
                center_x = total_x / len(largest_cluster)
                center_y = total_y / len(largest_cluster)
                center_pos = (center_x, center_y)

                # --- Find agent closest to center ---
                def dist(agent_id):
                    ax, ay = Agent.GetXY(agent_id)
                    return Utils.Distance((ax, ay), center_pos)

                closest_agent_id = min(largest_cluster, key=dist)
                return closest_agent_id

