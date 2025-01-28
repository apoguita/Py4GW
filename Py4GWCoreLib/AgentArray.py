import Py4GW
import PyPlayer
import PyAgent

from .Agent import *
from .Player import *

from .Py4GWcorelib import Utils

class AgentArray:
    @staticmethod
    def GetAgentArray():
        """Purpose: Get the unfiltered full agent array."""
        return [item for item in Player.player_instance().GetAgentArray()  if item != 0]    

    @staticmethod
    def GetAllyArray():
        """Purpose: Retrieve the agent array pre filtered by  allies."""
        return [item for item in Player.player_instance().GetAllyArray() if item != 0]

    @staticmethod
    def GetNeutralArray():
        """Purpose: Retrieve the agent array pre filtered by neutrals."""
        return [item for item in Player.player_instance().GetNeutralArray() if item != 0]

    @staticmethod
    def GetEnemyArray():
        """Purpose: Retrieve the agent array pre filtered by enemies."""
        return [item for item in Player.player_instance().GetEnemyArray() if item != 0]

    @staticmethod
    def GetSpiritPetArray():
        """Purpose: Retrieve the agent array pre filtered by spirit & pets."""
        return [item for item in Player.player_instance().GetSpiritPetArray() if item != 0]

    @staticmethod
    def GetMinionArray():
        """Purpose: Retrieve the agent array pre filtered by minions."""
        return [item for item in Player.player_instance().GetMinionArray() if item != 0]

    @staticmethod
    def GetNPCMinipetArray():
        """Purpose: Retrieve the agent array pre filtered by NPC & minipets."""
        return [item for item in Player.player_instance().GetNPCMinipetArray() if item != 0]

    @staticmethod
    def GetItemArray():
        """Purpose: Retrieve the agent array pre-filtered by items."""
        return Player.player_instance().GetItemArray()


    @staticmethod
    def GetGadgetArray():
        """Purpose: Retrieve the agent array pre filtered by gadgets."""
        return [item for item in Player.player_instance().GetGadgetArray() if item != 0]

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

    class Sort:
        @staticmethod
        def ByAttribute(agent_array, attribute, descending=False):
            """
            Sorts agents by a specific attribute (e.g., health, distance, etc.).
            sorted_agents_by_health = Sort.ByAttribute(agent_array, 'GetHealth', descending=True)
            """
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
            return sorted(agent_array, key=condition_func, reverse=reverse)


        @staticmethod
        def ByDistance(agent_array, pos, descending=False):
            """
            Sorts agents by their distance to a given (x, y) position.
            sorted_agents_by_distance = Sort.ByDistance(agent_array, (100, 200))
            """
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
            """
            Sorts agents by their health (HP).
            sorted_agents_by_health_desc = Sort.ByHealth(agent_array, descending=True)
            """
            return AgentArray.Sort.ByCondition(
                agent_array,
                condition_func=lambda agent_id: Agent.GetHealth(agent_id),
                reverse=descending
            )

    class Filter:
        @staticmethod
        def ByAttribute(agent_array, attribute, condition_func=None, negate=False):
            """
            Filters agents by an attribute, with support for negation.
            moving_agents = AgentArray.Filter.ByAttribute(agent_array, 'IsMoving')
            """
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
            return list(filter(filter_func, agent_array))


        @staticmethod
        def ByDistance(agent_array, pos, max_distance, negate=False):
            """
            Filters agents based on their distance from a given position.
            agents_within_range = AgentArray.Filter.ByDistance(agent_array, (100, 200), 500)
            """
            def distance_filter(agent_id):
                agent_x, agent_y = Agent.GetXY(agent_id)
                distance = Utils.Distance((agent_x, agent_y), (pos[0], pos[1]))
                return (distance > max_distance) if negate else (distance <= max_distance)

            return AgentArray.Filter.ByCondition(agent_array, distance_filter)


    class Routines:
        @staticmethod
        def DetectLargestAgentCluster(agent_array, cluster_radius):
            """
            Detects the largest cluster of agents based on proximity and returns the center of mass (XY) of the cluster
            and the closest agent ID to the center of mass.

            Args:
                agent_array (list[int]): List of agent IDs.
                cluster_radius (float): The maximum distance between agents to consider them in the same cluster.

            Returns:
                tuple: (center_of_mass (tuple), closest_agent_id (int))
                    - center_of_mass: (x, y) coordinates of the cluster's center of mass.
                    - closest_agent_id: The ID of the agent closest to the center of mass.

            Example:
                center_xy, closest_agent_id = Filters.DetectLargestAgentCluster(agent_array, cluster_radius=100)
            """
            clusters = []
            ungrouped_agents = set(agent_array)

            def is_in_radius(agent1, agent2):
                x1, y1 = Agent.GetXY(agent1)
                x2, y2 = Agent.GetXY(agent2)
                distance_sq = (x1 - x2) ** 2 + (y1 - y2) ** 2
                return distance_sq <= cluster_radius ** 2

            # Create clusters by grouping nearby agents
            while ungrouped_agents:
                current_agent = ungrouped_agents.pop()
                cluster = [current_agent]

                # Find agents in the same cluster
                for agent in list(ungrouped_agents):
                    if any(is_in_radius(current_agent, other) for other in cluster):
                        cluster.append(agent)
                        ungrouped_agents.remove(agent)

                clusters.append(cluster)

            # Find the largest cluster
            largest_cluster = max(clusters, key=len)

            # Compute the center of mass (average position) of the largest cluster
            total_x = total_y = 0
            for agent_id in largest_cluster:
                agent_x, agent_y = Agent.GetXY(agent_id)
                total_x += agent_x
                total_y += agent_y

            center_of_mass_x = total_x / len(largest_cluster)
            center_of_mass_y = total_y / len(largest_cluster)
            center_of_mass = (center_of_mass_x, center_of_mass_y)

            # Find the agent closest to the center of mass
            def distance_to_center(agent_id):
                agent_x, agent_y = Agent.GetXY(agent_id)
                #return (agent_x - center_of_mass_x) ** 2 + (agent_y - center_of_mass_y) ** 2  # Squared distance
                return Utils.Distance((agent_x, agent_y), center_of_mass)

            closest_agent_id = min(largest_cluster, key=distance_to_center)

            return center_of_mass, closest_agent_id

