from ctypes import string_at
from http.client import UNAUTHORIZED
import inspect
import os
import stat
from statistics import StatisticsError
from tkinter.filedialog import dialogstates
from turtle import st
import Py4GW
import ImGui_Py

import PyAgent
import PyPlayer
import PyParty
import PyItem
import PyInventory
import PySkill
import PySkillbar
import PyMerchant
import PyEffects
import PyKeystroke

import math
from enum import Enum

#This is the base Python Library for Py4GW
#It is intended to be used as am inlcude the Py4GW API
#It is not intended to be run as a standalone script
#it contains the core functions and classes for Py4GW
#aswell as advanced Routines and implementations

#utility Functions not especific of any process
# Utils
class Utils:
    @staticmethod
    def Distance(pos1, pos2):
        """
        Purpose: Calculate the distance between two positions.
        Args:
            pos1 (tuple): The first position (x, y).
            pos2 (tuple): The second position (x, y).
        Returns: float
        """
        return math.sqrt((pos1[0] - pos2[0]) ** 2 + (pos1[1] - pos2[1]) ** 2)

    class Filters:
        @staticmethod
        def FilterSelfFromAgentArray(agent_array):
            """
            Purpose: Filter the player from an agent array.
            Args:
                agent_array (list): The list of agent IDs.
            Returns: list
            """
            player_instance = PyPlayer.PyPlayer()
            return [agent_id for agent_id in agent_array if agent_id != player_instance.id]

        @staticmethod
        def FilterAgentArrayByRange(agent_pos,agent_array, area=5000):
            """
            Purpose: Filter an agent array by range.
            Args:
                agent_array (list): The list of agent IDs.
                area (int, optional): The area to search for the nearest agent. Default is 5000.
            Returns: list
            """
            x, y = Player.GetPlayerXY()

            filtered_agent_array = []
            for agent_id in agent_array:
                agent_instance = PyAgent.PyAgent(agent_id)
                if Utils.Distance(agent_pos, (agent_instance.x, agent_instance.y)) <= area:
                    filtered_agent_array.append(agent_id)
            return filtered_agent_array

        @staticmethod
        def FilterAgentArrayByMoving(agent_pos, agent_array, area=5000):
            """
            Purpose: Filter an agent array by moving.
            Args:
                agent_array (list): The list of agent IDs.
                area (int, optional): The area to search for the nearest agent. Default is 5000.
            Returns: list
            """
            range_array = Utils.Filters.FilterAgentArrayByRange(agent_pos, agent_array, area)
            filtered_agent_array = []
            for agent_id in range_array:
                if Agent.IsMoving(agent_id):
                    filtered_agent_array.append(agent_id)
            return filtered_agent_array

        @staticmethod
        def FilterAgentArrayByDead(agent_pos, agent_array, area=5000):
            """
            Purpose: Filter an agent array by dead.
            Args:
                agent_array (list): The list of agent IDs.
                area (int, optional): The area to search for the nearest agent. Default is 5000.
            Returns: list
            """
            range_array = Utils.Filters.FilterAgentArrayByRange(agent_pos, agent_array, area)
            filtered_agent_array = []
            for agent_id in range_array:
                if Agent.IsDead(agent_id):
                    filtered_agent_array.append(agent_id)
            return filtered_agent_array

        @staticmethod
        def FilterAgentArrayByAlive(agent_pos, agent_array, area=5000):
            """
            Purpose: Filter an agent array by alive.
            Args:
                agent_array (list): The list of agent IDs.
                area (int, optional): The area to search for the nearest agent. Default is 5000.
            Returns: list
            """
            range_array = Utils.Filters.FilterAgentArrayByRange(agent_pos, agent_array, area)
            filtered_agent_array = []
            for agent_id in range_array:
                if Agent.IsAlive(agent_id):
                    filtered_agent_array.append(agent_id)
            return filtered_agent_array

        @staticmethod
        def FilterAgentArrayByIsConditioned(agent_pos, agent_array, area=5000):
            """
            Purpose: Filter an agent array by conditioned.
            Args:
                agent_array (list): The list of agent IDs.
                area (int, optional): The area to search for the nearest agent. Default is 5000.
            Returns: list
            """
            range_array = Utils.Filters.FilterAgentArrayByRange(agent_pos, agent_array, area)
            filtered_agent_array = []
            for agent_id in range_array:
                if Agent.IsConditioned(agent_id):
                    filtered_agent_array.append(agent_id)
            return filtered_agent_array

        @staticmethod
        def FilterAgentArrayByIsBleeding(agent_pos, agent_array, area=5000):
            """
            Purpose: Filter an agent array by bleeding.
            Args:
                agent_array (list): The list of agent IDs.
                area (int, optional): The area to search for the nearest agent. Default is 5000.
            Returns: list
            """
            range_array = Utils.Filters.FilterAgentArrayByRange(agent_pos, agent_array, area)
            filtered_agent_array = []
            for agent_id in range_array:
                if Agent.IsBleeding(agent_id):
                    filtered_agent_array.append(agent_id)
            return filtered_agent_array

        @staticmethod
        def FilterAgentArrayByIsPoisoned(agent_pos, agent_array, area=5000):
            """
            Purpose: Filter an agent array by poisoned.
            Args:
                agent_array (list): The list of agent IDs.
                area (int, optional): The area to search for the nearest agent. Default is 5000.
            Returns: list
            """
            range_array = Utils.Filters.FilterAgentArrayByRange(agent_pos, agent_array, area)
            filtered_agent_array = []
            for agent_id in range_array:
                if Agent.IsPoisoned(agent_id):
                    filtered_agent_array.append(agent_id)
            return filtered_agent_array

        @staticmethod
        def FilterAgentByIsDeepWounded(agent_pos, agent_array, area=5000):
            """
            Purpose: Filter an agent array by deep wounded.
            Args:
                agent_array (list): The list of agent IDs.
                area (int, optional): The area to search for the nearest agent. Default is 5000.
            Returns: list
            """
            range_array = Utils.Filters.FilterAgentArrayByRange(agent_pos, agent_array, area)
            filtered_agent_array = []
            for agent_id in range_array:
                if Agent.IsDeepWounded(agent_id):
                    filtered_agent_array.append(agent_id)
            return filtered_agent_array

        @staticmethod
        def FilterAgentArrayByIsCrippled(agent_pos, agent_array, area=5000):
            """
            Purpose: Filter an agent array by crippled.
            Args:
                agent_array (list): The list of agent IDs.
                area (int, optional): The area to search for the nearest agent. Default is 5000.
            Returns: list
            """
            range_array = Utils.Filters.FilterAgentArrayByRange(agent_pos, agent_array, area)
            filtered_agent_array = []
            for agent_id in range_array:
                if Agent.IsCrippled(agent_id):
                    filtered_agent_array.append(agent_id)
            return filtered_agent_array

        @staticmethod
        def FilterArrayByOwnerID(agent_pos, agent_array, owner_id, area=5000):
            """
            Purpose: Filter an agent array by owner ID.
            Args:
                agent_array (list): The list of agent IDs.
                owner_id (int): The ID of the owner.
                area (int, optional): The area to search for the nearest agent. Default is 5000.
            Returns: list
            """
            range_array = Utils.Filters.FilterAgentArrayByRange(agent_pos, agent_array, area)
            filtered_agent_array = []
            for agent_id in range_array:
                if Agent.GetOwnerID(agent_id) == owner_id:
                    filtered_agent_array.append(agent_id)
            return filtered_agent_array

        @staticmethod
        def FilterArrayByNotOwnerID(agent_pos, agent_array, owner_id, area=5000):
            """
            Purpose: Filter an agent array by not owner ID.
            Args:
                agent_array (list): The list of agent IDs.
                owner_id (int): The ID of the owner.
                area (int, optional): The area to search for the nearest agent. Default is 5000.
            Returns: list
            """
            range_array = Utils.Filters.FilterAgentArrayByRange(agent_pos, agent_array, area)
            filtered_agent_array = []
            for agent_id in range_array:
                if Agent.GetOwnerID(agent_id) != owner_id:
                    filtered_agent_array.append(agent_id)
            return filtered_agent_array

        @staticmethod
        def FilterArrayByHasBossGlow(agent_pos, agent_array, area=5000):
            """
            Purpose: Filter an agent array by boss glow.
            Args:
                agent_array (list): The list of agent IDs.
                area (int, optional): The area to search for the nearest agent. Default is 5000.
            Returns: list
            """
            range_array = Utils.Filters.FilterAgentArrayByRange(agent_pos, agent_array, area)
            filtered_agent_array = []
            for agent_id in range_array:
                if Agent.HasBossGlow(agent_id):
                    filtered_agent_array.append(agent_id)
            return filtered_agent_array

        @staticmethod
        def FilterArrayByHasEnchantment(agent_pos, agent_array, area=5000):
            """
            Purpose: Filter an agent array by enchantment.
            Args:
                agent_array (list): The list of agent IDs.
                area (int, optional): The area to search for the nearest agent. Default is 5000.
            Returns: list
            """
            range_array = Utils.Filters.FilterAgentArrayByRange(agent_pos, agent_array, area)
            filtered_agent_array = []
            for agent_id in range_array:
                if Agent.IsEnchanted(agent_id):
                    filtered_agent_array.append(agent_id)
            return filtered_agent_array

        @staticmethod
        def FilterArrayByNotHasEnchantment(agent_pos, agent_array, area=5000):
            """
            Purpose: Filter an agent array by not having an enchantment.
            Args:
                agent_array (list): The list of agent IDs.
                area (int, optional): The area to search for the nearest agent. Default is 5000.
            Returns: list
            """
            range_array = Utils.Filters.FilterAgentArrayByRange(agent_pos, agent_array, area)
            filtered_agent_array = []
            for agent_id in range_array:
                if not Agent.IsEnchanted(agent_id):
                    filtered_agent_array.append(agent_id)
            return filtered_agent_array

        @staticmethod
        def FilterArrayByHasHex(agent_pos, agent_array, area=5000):
            """
            Purpose: Filter an agent array by hex.
            Args:
                agent_array (list): The list of agent IDs.
                area (int, optional): The area to search for the nearest agent. Default is 5000.
            Returns: list
            """
            range_array = Utils.Filters.FilterAgentArrayByRange(agent_pos, agent_array, area)
            filtered_agent_array = []
            for agent_id in range_array:
                if Agent.IsHexed(agent_id):
                    filtered_agent_array.append(agent_id)
            return filtered_agent_array

        @staticmethod
        def FilterArrayByNotHasHex(agent_pos, agent_array, area=5000):
            """
            Purpose: Filter an agent array by not having a hex.
            Args:
                agent_array (list): The list of agent IDs.
                area (int, optional): The area to search for the nearest agent. Default is 5000.
            Returns: list
            """
            range_array = Utils.Filters.FilterAgentArrayByRange(agent_pos, agent_array, area)
            filtered_agent_array = []
            for agent_id in range_array:
                if not Agent.IsHexed(agent_id):
                    filtered_agent_array.append(agent_id)
            return filtered_agent_array

        @staticmethod
        def FilterArrayByIsCasting(agent_pos, agent_array, area=5000):
            """
            Purpose: Filter an agent array by casting.
            Args:
                agent_array (list): The list of agent IDs.
                area (int, optional): The area to search for the nearest agent. Default is 5000.
            Returns: list
            """
            range_array = Utils.Filters.FilterAgentArrayByRange(agent_pos, agent_array, area)
            filtered_agent_array = []
            for agent_id in range_array:
                if Agent.IsCasting(agent_id):
                    filtered_agent_array.append(agent_id)
            return filtered_agent_array

        @staticmethod
        def FilterArrayByNotCasting(agent_pos, agent_array, area=5000):
            """
            Purpose: Filter an agent array by not casting.
            Args:
                agent_array (list): The list of agent IDs.
                area (int, optional): The area to search for the nearest agent. Default is 5000.
            Returns: list
            """
            range_array = Utils.Filters.FilterAgentArrayByRange(agent_pos, agent_array, area)
            filtered_agent_array = []
            for agent_id in range_array:
                if not Agent.IsCasting(agent_id):
                    filtered_agent_array.append(agent_id)
            return filtered_agent_array

        @staticmethod
        def FilterAgentArrayByIsMartial(agent_pos, agent_array, area=5000):
            """
            Purpose: Filter an agent array by martial.
            Args:
                agent_array (list): The list of agent IDs.
                area (int, optional): The area to search for the nearest agent. Default is 5000.
            Returns: list
            """
            range_array = Utils.Filters.FilterAgentArrayByRange(agent_pos, agent_array, area)
            filtered_agent_array = []
            for agent_id in range_array:
                if Agent.IsMartial(agent_id):
                    filtered_agent_array.append(agent_id)
            return filtered_agent_array

        @staticmethod
        def FilterAgentArrayByIsCaster(agent_pos, agent_array, area=5000):
            """
            Purpose: Filter an agent array by caster.
            Args:
                agent_array (list): The list of agent IDs.
                area (int, optional): The area to search for the nearest agent. Default is 5000.
            Returns: list
            """
            range_array = Utils.Filters.FilterAgentArrayByRange(agent_pos, agent_array, area)
            filtered_agent_array = []
            for agent_id in range_array:
                if Agent.IsCaster(agent_id):
                    filtered_agent_array.append(agent_id)
            return filtered_agent_array

        @staticmethod
        def FilterAgentArrayByIsRanged(agent_pos, agent_array, area=5000):
            """
            Purpose: Filter an agent array by ranged.
            Args:
                agent_array (list): The list of agent IDs.
                area (int, optional): The area to search for the nearest agent. Default is 5000.
            Returns: list
            """
            range_array = Utils.Filters.FilterAgentArrayByRange(agent_pos, agent_array, area)
            filtered_agent_array = []
            for agent_id in range_array:
                if Agent.IsRanged(agent_id):
                    filtered_agent_array.append(agent_id)
            return filtered_agent_array

        @staticmethod
        def FilterAgentArrayByIsMelee(agent_pos, agent_array, area=5000):
            """
            Purpose: Filter an agent array by melee.
            Args:
                agent_array (list): The list of agent IDs.
                area (int, optional): The area to search for the nearest agent. Default is 5000.
            Returns: list
            """
            range_array = Utils.Filters.FilterAgentArrayByRange(agent_pos, agent_array, area)
            filtered_agent_array = []
            for agent_id in range_array:
                if Agent.IsMelee(agent_id):
                    filtered_agent_array.append(agent_id)
            return filtered_agent_array

    class VectorFields:
        """
        The VectorFields class simulates movement using repulsion and attraction forces based on agent arrays and custom positions.
        Additionally, custom repulsion and attraction positions can be provided.
        """

        def __init__(self, probe_position, custom_repulsion_radius=100, custom_attraction_radius=100):
            """
            Initialize the VectorFields object with player position and default settings.
            Args:
                probe_position (tuple): The player's current position (x, y).
            """
            self.probe_position = probe_position

            # Store settings for agent arrays and custom positions
            self.agent_arrays_settings = {}

            # Custom repulsion and attraction lists
            self.custom_repulsion_positions = []
            self.custom_attraction_positions = []

            # Radius for custom positions
            self.custom_repulsion_radius = custom_repulsion_radius
            self.custom_attraction_radius = custom_attraction_radius

        def add_agent_array(self, array_name, agent_array, radius, is_dangerous=True):
            """
            Add an agent array to be processed with the vector fields.
            Args:
                array_name (str): Name of the agent array (e.g., 'enemies', 'allies').
                agent_array (list): List of agent IDs to process.
                radius (int): Radius of effect for this array.
                is_dangerous (bool): Whether the array represents a dangerous (repulsion) or safe (attraction) set. Default is True.
            """
            self.agent_arrays_settings[array_name] = {
                'agent_array': agent_array,
                'radius': radius,
                'is_dangerous': is_dangerous
            }

        def add_custom_repulsion_position(self, position):
            """
            Add a custom repulsion position.
            Args:
                position (tuple): The position (x, y) to add to the repulsion list.
            """
            self.custom_repulsion_positions.append(position)

        def add_custom_attraction_position(self, position):
            """
            Add a custom attraction position.
            Args:
                position (tuple): The position (x, y) to add to the attraction list.
            """
            self.custom_attraction_positions.append(position)

        def clear_custom_positions(self):
            """
            Clear all custom repulsion and attraction positions.
            """
            self.custom_repulsion_positions.clear()
            self.custom_attraction_positions.clear()

        def calculate_unit_vector(self, target_position):
            """
            Calculate the unit vector between the player and a target position.
            Args:
                target_position (tuple): The target's position (x, y).
            Returns:
                tuple: The unit vector (dx, dy) pointing from the player to the target.
            """
            pos_a = self.probe_position
            pos_b = target_position

            #fix for agent spawning on top of player 
            pos_a[0] += 1
            pos_a[1] += 1

            pos_b[0] += -1
            pos_b[1] += -1
            
            distance = Utils.Distance(pos_a,pos_b)
            if distance == 0:
                return (0, 0)  # Avoid division by zero
            return ((pos_b[0] - pos_a[0]) / distance,
                    (pos_b[1] - pos_a[1]) / distance)

        def process_agent_array(self, agent_array, radius, is_dangerous):
            """
            Process a given agent array and calculate its total vector (either repulsion or attraction).
            Args:
                agent_array (list): List of agent IDs.
                radius (int): Radius of effect for the agents.
                is_dangerous (bool): Whether the agents are repulsive (True) or attractive (False).
            Returns:
                tuple: The combined vector (dx, dy) from this agent array.
            """
            combined_vector = [0, 0]
            if radius == 0:
                return (0, 0)  # Ignore if radius is 0

            for agent_id in agent_array:
                agent_instance = PyAgent.PyAgent(agent_id)
                target_position = (agent_instance.x, agent_instance.y)
                distance = Utils.Distance(self.probe_position, target_position)

                if distance <= radius:
                    unit_vector = self.calculate_unit_vector(target_position)
                    if is_dangerous:
                        # Repulsion: Subtract the vector
                        combined_vector[0] -= unit_vector[0]
                        combined_vector[1] -= unit_vector[1]
                    else:
                        # Attraction: Add the vector
                        combined_vector[0] += unit_vector[0]
                        combined_vector[1] += unit_vector[1]

            return tuple(combined_vector)

        def process_custom_positions(self, positions, radius, is_dangerous):
            """
            Process custom repulsion or attraction positions and calculate their total vector.
            Args:
                positions (list): List of custom positions [(x, y), ...].
                radius (int): Radius of effect for these positions.
                is_dangerous (bool): Whether the positions are repulsive (True) or attractive (False).
            Returns:
                tuple: The combined vector (dx, dy) from the custom positions.
            """
            combined_vector = [0, 0]
            for position in positions:
                distance = Utils.Distance(self.probe_position, position)

                if distance <= radius:
                    unit_vector = self.calculate_unit_vector(position)
                    if is_dangerous:
                        # Repulsion: Subtract the vector
                        combined_vector[0] -= unit_vector[0]
                        combined_vector[1] -= unit_vector[1]
                    else:
                        # Attraction: Add the vector
                        combined_vector[0] += unit_vector[0]
                        combined_vector[1] += unit_vector[1]

            return tuple(combined_vector)

        def compute_combined_vector(self):
            """
            Compute the overall vector for all agent arrays and custom positions.
            Returns:
                tuple: The final combined vector (dx, dy).
            """
            final_vector = [0, 0]

            # Process all agent arrays
            for array_name, settings in self.agent_arrays_settings.items():
                agent_vector = self.process_agent_array(
                    settings['agent_array'], settings['radius'], settings['is_dangerous'])
                final_vector[0] += agent_vector[0]
                final_vector[1] += agent_vector[1]

            # Process custom repulsion positions
            repulsion_vector = self.process_custom_positions(self.custom_repulsion_positions, self.custom_repulsion_radius, True)
            final_vector[0] += repulsion_vector[0]
            final_vector[1] += repulsion_vector[1]

            # Process custom attraction positions
            attraction_vector = self.process_custom_positions(self.custom_attraction_positions, self.custom_attraction_radius, False)
            final_vector[0] += attraction_vector[0]
            final_vector[1] += attraction_vector[1]

            return tuple(final_vector)

        def generate_escape_vector(self, agent_arrays, custom_repulsion_positions=None, custom_attraction_positions=None):
            """
            Purpose: Generate an escape vector based on the input agent arrays and custom repulsion/attraction settings.
            Args:
                agent_arrays (list): A list of dictionaries representing different agent arrays and their parameters.
                                        Each dictionary should contain:
                                        - 'name' (str): Name of the agent array (e.g., 'enemies', 'allies').
                                        - 'array' (list): The agent IDs in the array.
                                        - 'radius' (int): The radius of effect for this array (0 to ignore).
                                        - 'is_dangerous' (bool): Whether this array represents repulsion (True) or attraction (False).
                custom_repulsion_positions (list, optional): A list of custom positions (x, y) to act as repulsion sources. Default is None.
                custom_attraction_positions (list, optional): A list of custom positions (x, y) to act as attraction sources. Default is None.
            Returns:
                tuple: The final combined vector (dx, dy) based on all agent arrays and custom settings.
            """
            # Loop through the provided agent arrays and add them to the vector fields
            for agent_array in agent_arrays:
                name = agent_array['name']
                array = agent_array['array']
                radius = agent_array['radius']
                is_dangerous = agent_array['is_dangerous']

                # Add each agent array to the vector field with its properties
                self.add_agent_array(name, array, radius, is_dangerous)

            # Add custom repulsion positions if provided
            if custom_repulsion_positions:
                for position in custom_repulsion_positions:
                    self.add_custom_repulsion_position(position)

            # Add custom attraction positions if provided
            if custom_attraction_positions:
                for position in custom_attraction_positions:
                    self.add_custom_attraction_position(position)

            # Compute the final escape vector by combining all repulsion/attraction vectors
            escape_vector = self.compute_combined_vector()

            return escape_vector



# Maps
class Map:
    @staticmethod
    def IsMapReady():
        """
        Purpose: Check if the map is ready to be handled.
        Args: None
        Returns: bool
        """
        return Map.IsMapReady()

    @staticmethod
    def IsOutpost():
        """
        Purpose: Check if the map instance is an outpost.
        Args: None
        Returns: bool
        """
        return Map.IsOutpost()

    @staticmethod
    def IsExplorable():
        """
        Purpose: Check if the map instance is explorable.
        Args: None
        Returns: bool
        """
        return Map.IsExplorable()

    @staticmethod
    def IsMapLoading():
        """
        Purpose: Check if the map instance is loading.
        Args: None
        Returns: bool
        """
        return Map.IsMapLoading()

    @staticmethod
    def GetMapName(mapid=None):
        """
        Purpose: Retrieve the name of a map by its ID.
        Args:
            mapid (int, optional): The ID of the map to retrieve. Defaults to the current map.
        Returns: str
        """
        return Map.GetMapName(mapid)

    @staticmethod
    def GetMapID():
        """
        Purpose: Retrieve the ID of the current map.
        Args: None
        Returns: int
        """
        return Map.GetMapID()

    @staticmethod
    def Travel(map_id):
        """
        Purpose: Travel to a map by its ID.
        Args:
            map_id (int): The ID of the map to travel to.
        Returns: None
        """
        Map.Travel(map_id)

    @staticmethod
    def GetInstanceUptime():
        """
        Purpose: Retrieve the uptime of the current instance.
        Args: None
        Returns: int (ms)
        """
        return Map.GetInstanceUptime()

    @staticmethod
    def GetMaxPartySize():
        """
        Purpose: Retrieve the maximum party size of the current map.
        Args: None
        Returns: int
        """
        return Map.GetMaxPartySize()

    @staticmethod
    def IsInCinematic():
        """
        Purpose: Check if the map is in a cinematic.
        Args: None
        Returns: bool
        """
        return Map.IsInCinematic()

    @staticmethod
    def SkipCinematic():
        """
        Purpose: Skip the cinematic.
        Args: None
        Returns: None
        """
        return Map.SkipCinematic()

    @staticmethod
    def HasEnterChallengeButton():
        """
        Purpose: Check if the map has an enter button.
        Args: None
        Returns: bool
        """
        return Map.HasEnterChallengeButton()

    @staticmethod
    def EnterChallenge():
        """
        Purpose: Enter the challenge.
        Args: None
        Returns: None
        """
        return Map.EnterChallenge()

    @staticmethod
    def CancelEnterChallenge():
        """
        Purpose: Cancel entering the challenge.
        Args: None
        Returns: None
        """
        return Map.CancelEnterChallenge()

    @staticmethod
    def IsVanquishable():
        """
        Purpose: Check if the map is vanquisheable.
        Args: None
        Returns: bool
        """
        return Map.IsVanquishable()

    @staticmethod
    def GetFoesKilled():
        """
        Purpose: Retrieve the number of foes killed in the current map.
        Args: None
        Returns: int
        """
        return Map.GetFoesKilled()

    @staticmethod
    def GetFoesToKill():
        """
        Purpose: Retrieve the number of foes to kill in the current map.
        Args: None
        Returns: int
        """
        return Map.GetFoesToKill()

    @staticmethod
    def GetDistrict():
        """
        Purpose: Retrieve the district of the current map.
        Args: None
        Returns: str
        """
        return Map.GetDistrict()

    @staticmethod
    def GetRegion():
        """
        Purpose: Retrieve the region of the current map.
        Args: None
        Returns: str
        """
        return Map.GetRegion()[0]

    @staticmethod
    def GetLanguage():
        """
        Purpose: Retrieve the language of the current map.
        Args: None
        Returns: str
        """
        return Map.GetLanguage()

# Agents
class Agent:
    @staticmethod
    def GetIdFromAgent(agent_instance):
        """
        Purpose: Retrieve the ID of an agent.
        Args:
            agent_instance (PyAgent): The agent instance.
        Returns: int
        """
        return agent_instance.agent_id
    
    @staticmethod
    def GetAgentByID(agent_id):
        """
        Purpose: Retrieve an agent by its ID.
        Args:
            agent_id (int): The ID of the agent to retrieve.
        Returns: PyAgent
        """
        return PyAgent.PyAgent(agent_id)

    @staticmethod
    def GetModelID(agent_id):
        """
        Purpose: Retrieve the model of an agent.
        Args:
            agent_id (int): The ID of the agent.
        Returns: str
        """
        Agent.GetModelID(agent_id)

    @staticmethod
    def IsLiving(agent_id):
        """
        Purpose: Check if the agent is living.
        Args: None
        Returns: bool
        """
        agent_instance = PyAgent.PyAgent(agent_id)
        return agent_instance.is_living

    @staticmethod
    def IsItem(agent_id):
        """
        Purpose: Check if the agent is an item.
        Args: None
        Returns: bool
        """
        agent_instance = PyAgent.PyAgent(agent_id)
        return agent_instance.is_item

    @staticmethod
    def IsGadget(agent_id):
        """
        Purpose: Check if the agent is a gadget.
        Args: None
        Returns: bool
        """
        agent_instance = PyAgent.PyAgent(agent_id)
        return agent_instance.is_gadget

    @staticmethod
    def IsSpirit(agent_id):
        """
        Purpose: Check if the agent is a spirit.
        Args: None
        Returns: bool
        """
        agent_instance = PyAgent.PyAgent(agent_id)
        return agent_instance.living_agent.allegiance.GetName() == "Spirit/Pet"

    @staticmethod
    def IsMinion(agent_id):
        """
        Purpose: Check if the agent is a minion.
        Args: None
        Returns: bool
        """
        agent_instance = PyAgent.PyAgent(agent_id)
        return agent_instance.living_agent.allegiance.GetName() == "Minion"

    @staticmethod
    def GetOwnerID(agent_id):
        """
        Purpose: Retrieve the owner ID of an agent.
        Args:
            agent_id (int): The ID of the agent.
        Returns: int
        """
        agent_instance = PyAgent.PyAgent(agent_id)
        return agent_instance.living_agent.owner_id

    @staticmethod
    def GetAgentArrayByType(agent_type, player_instance=None):
        """
        Purpose: Retrieve the agent array by the specified type.
        Args:
            agent_type (str): The type of agent array to fetch ('Ally', 'Neutral', etc.).
            player_instance (optional): The player instance to use.
        Returns: list
        """
        if player_instance is None:
            player_instance = PyPlayer.PyPlayer()
        agent_array_methods = {
            "Ally": player_instance.GetAllyArray,
            "Neutral": player_instance.GetNeutralArray,
            "Enemy": player_instance.GetEnemyArray,
            "SpiritPet": player_instance.GetSpiritPetArray,
            "Minion": player_instance.GetMinionArray,
            "NPCMinipet": player_instance.GetNPCMinipetArray,
            "Item": player_instance.GetItemArray,
            "Gadget": player_instance.GetGadgetArray
        }
        return agent_array_methods[agent_type]()

    @staticmethod
    def GetXY(agent_id):
        """
        Purpose: Retrieve the X and Y coordinates of an agent.
        Args:
            agent_id (int): The ID of the agent.
        Returns: tuple
        """
        agent_instance = PyAgent.PyAgent(agent_id)
        return agent_instance.x, agent_instance.y

    @staticmethod
    def GetVelocityXY(agent_id):
        """
        Purpose: Retrieve the X and Y velocity of an agent.
        Args:
            agent_id (int): The ID of the agent.
        Returns: tuple
        """
        agent_instance = PyAgent.PyAgent(agent_id)
        return agent_instance.velocity_x, agent_instance.velocity_y

    @staticmethod
    def GetNearestAgentXY(agent_array, x, y, area=5000,filter_dead= True):
        """
        Purpose: Get the nearest agent from an agent array based on coordinates.
        Args:
            agent_array (list): The list of agent IDs.
            x (float): X coordinate.
            y (float): Y coordinate.
            area (int, optional): The area to search for the nearest agent. Default is 5000.
        Returns: PyAgent
        """
        if not agent_array:
            return None
        nearest_agent = None
        min_distance_sq = float('inf')
        player_agent_id = PyPlayer.PyPlayer().id
        for agent_id in agent_array:
            agent_instance = PyAgent.PyAgent(agent_id)
            if player_agent_id == agent_instance.id:
                continue
            if filter_dead and Agent.IsDead(agent_id):
                continue

            if hasattr(agent_instance, 'x') and hasattr(agent_instance, 'y'):
                distance_sq = (agent_instance.x - x) ** 2 + (agent_instance.y - y) ** 2
                if (distance_sq < min_distance_sq) and (distance_sq < area ** 2):
                    min_distance_sq = distance_sq
                    nearest_agent = agent_instance
        return nearest_agent

    @staticmethod
    def GetNearestAgentOfTypeXY(agent_type, x, y, area=5000, player_instance=None,filter_dead= True):
        """
        Purpose: Get the nearest agent of a specified type based on coordinates.
        Args:
            agent_type (str): The type of agent to find ('Ally', 'Neutral', etc.).
            x (float): X coordinate.
            y (float): Y coordinate.
            area (int, optional): The area to search for the nearest agent. Default is 5000.
            player_instance (optional): The player instance to use.
        Returns: PyAgent
        """
        agent_array = Agent.GetAgentArrayByType(agent_type, player_instance)
        return Agent.GetNearestAgentXY(agent_array, x, y, area,filter_dead)

    @staticmethod
    def GetNearestAllyXY(x, y, area=5000, player_instance=None,filter_dead= True):
        """
        Purpose: Get the nearest ally based on coordinates.
        Args:
            x (float): X coordinate.
            y (float): Y coordinate.
            area (int, optional): The area to search for the nearest ally. Default is 5000.
            player_instance (optional): The player instance to use.
        Returns: PyAgent
        """
        return Agent.GetNearestAgentOfTypeXY("Ally", x, y, area, player_instance,filter_dead)

    @staticmethod
    def GetNearestNeutralXY(x, y, area=5000, player_instance=None,filter_dead= True):
        """
        Purpose: Get the nearest neutral agent based on coordinates.
        Args:
            x (float): X coordinate.
            y (float): Y coordinate.
            area (int, optional): The area to search for the nearest neutral agent. Default is 5000.
            player_instance (optional): The player instance to use.
        Returns: PyAgent
        """
        return Agent.GetNearestAgentOfTypeXY("Neutral", x, y, area, player_instance,filter_dead)

    @staticmethod
    def GetNearestEnemyXY(x, y, area=5000, player_instance=None,filter_dead= True):
        """
        Purpose: Get the nearest enemy based on coordinates.
        Args:
            x (float): X coordinate.
            y (float): Y coordinate.
            area (int, optional): The area to search for the nearest enemy. Default is 5000.
            player_instance (optional): The player instance to use.
        Returns: PyAgent
        """
        return Agent.GetNearestAgentOfTypeXY("Enemy", x, y, area, player_instance,filter_dead)

    @staticmethod
    def GetNearestSpiritPetXY(x, y, area=5000, player_instance=None,filter_dead= True):
        """
        Purpose: Get the nearest spirit pet based on coordinates.
        Args:
            x (float): X coordinate.
            y (float): Y coordinate.
            area (int, optional): The area to search for the nearest spirit pet. Default is 5000.
            player_instance (optional): The player instance to use.
        Returns: PyAgent
        """
        return Agent.GetNearestAgentOfTypeXY("SpiritPet", x, y, area, player_instance,filter_dead)

    @staticmethod
    def GetNearestMinionXY(x, y, area=5000, player_instance=None,filter_dead= True):
        """
        Purpose: Get the nearest minion based on coordinates.
        Args:
            x (float): X coordinate.
            y (float): Y coordinate.
            area (int, optional): The area to search for the nearest minion. Default is 5000.
            player_instance (optional): The player instance to use.
        Returns: PyAgent
        """
        return Agent.GetNearestAgentOfTypeXY("Minion", x, y, area, player_instance,filter_dead)

    @staticmethod
    def GetNearestNPCMinipetXY(x, y, area=5000, player_instance=None,filter_dead= True):
        """
        Purpose: Get the nearest NPC or minipet based on coordinates.
        Args:
            x (float): X coordinate.
            y (float): Y coordinate.
            area (int, optional): The area to search for the nearest NPC minipet. Default is 5000.
            player_instance (optional): The player instance to use.
        Returns: PyAgent
        """
        return Agent.GetNearestAgentOfTypeXY("NPCMinipet", x, y, area, player_instance,filter_dead)

    @staticmethod
    def GetNearestItemXY(x, y, area=5000, player_instance=None,filter_dead= True):
        """
        Purpose: Get the nearest item based on coordinates.
        Args:
            x (float): X coordinate.
            y (float): Y coordinate.
            area (int, optional): The area to search for the nearest item. Default is 5000.
            player_instance (optional): The player instance to use.
        Returns: PyAgent
        """
        return Agent.GetNearestAgentOfTypeXY("Item", x, y, area, player_instance,filter_dead)

    @staticmethod
    def GetNearestGadgetXY(x, y, area=5000, player_instance=None,filter_dead= True):
        """
        Purpose: Get the nearest gadget based on coordinates.
        Args:
            x (float): X coordinate.
            y (float): Y coordinate.
            area (int, optional): The area to search for the nearest gadget. Default is 5000.
            player_instance (optional): The player instance to use.
        Returns: PyAgent
        """
        return Agent.GetNearestAgentOfTypeXY("Gadget", x, y, area, player_instance,filter_dead)

    @staticmethod
    def GetNearestAllyToAgent(agent_id, area=5000,filter_dead= True):
        """
        Purpose: Get the nearest ally to an agent based on its ID.
        Args:
            agent_id (int): The ID of the agent.
            area (int, optional): The area to search for the nearest ally. Default is 5000.
        Returns: PyAgent
        """
        agent_instance = PyAgent.PyAgent(agent_id)
        return Agent.GetNearestAgentOfTypeXY("Ally", agent_instance.x, agent_instance.y, area,filter_dead)

    @staticmethod
    def GetNearestNeutralToAgent(agent_id, area=5000,filter_dead= True):
        """
        Purpose: Get the nearest neutral agent to an agent based on its ID.
        Args:
            agent_id (int): The ID of the agent.
            area (int, optional): The area to search for the nearest neutral agent. Default is 5000.
        Returns: PyAgent
        """
        agent_instance = PyAgent.PyAgent(agent_id)
        return Agent.GetNearestAgentOfTypeXY("Neutral", agent_instance.x, agent_instance.y, area,filter_dead)

    @staticmethod
    def GetNearestEnemyToAgent(agent_id, area=5000,filter_dead= True):
        """
        Purpose: Get the nearest enemy to an agent based on its ID.
        Args:
            agent_id (int): The ID of the agent.
            area (int, optional): The area to search for the nearest enemy. Default is 5000.
        Returns: PyAgent
        """
        agent_instance = PyAgent.PyAgent(agent_id)
        return Agent.GetNearestAgentOfTypeXY("Enemy", agent_instance.x, agent_instance.y, area,filter_dead)

    @staticmethod
    def GetNearestSpiritPetToAgent(agent_id, area=5000,filter_dead= True):
        """
        Purpose: Get the nearest spirit pet to an agent based on its ID.
        Args:
            agent_id (int): The ID of the agent.
            area (int, optional): The area to search for the nearest spirit pet. Default is 5000.
        Returns: PyAgent
        """
        agent_instance = PyAgent.PyAgent(agent_id)
        return Agent.GetNearestAgentOfTypeXY("SpiritPet", agent_instance.x, agent_instance.y, area,filter_dead)

    @staticmethod
    def GetNearestMinionToAgent(agent_id, area=5000,filter_dead= True):
        """
        Purpose: Get the nearest minion to an agent based on its ID.
        Args:
            agent_id (int): The ID of the agent.
            area (int, optional): The area to search for the nearest minion. Default is 5000.
        Returns: PyAgent
        """
        agent_instance = PyAgent.PyAgent(agent_id)
        return Agent.GetNearestAgentOfTypeXY("Minion", agent_instance.x, agent_instance.y, area,filter_dead)

    @staticmethod
    def GetNearestNPCMinipetToAgent(agent_id, area=5000,filter_dead= True):
        """
        Purpose: Get the nearest NPC minipet to an agent based on its ID.
        Args:
            agent_id (int): The ID of the agent.
            area (int, optional): The area to search for the nearest NPC minipet. Default is 5000.
        Returns: PyAgent
        """
        agent_instance = PyAgent.PyAgent(agent_id)
        return Agent.GetNearestAgentOfTypeXY("NPCMinipet", agent_instance.x, agent_instance.y, area,filter_dead)

    @staticmethod
    def GetNearestItemToAgent(agent_id, area=5000,filter_dead= True):
        """
        Purpose: Get the nearest item to an agent based on its ID.
        Args:
            agent_id (int): The ID of the agent.
            area (int, optional): The area to search for the nearest item. Default is 5000.
        Returns: PyAgent
        """
        agent_instance = PyAgent.PyAgent(agent_id)
        return Agent.GetNearestAgentOfTypeXY("Item", agent_instance.x, agent_instance.y, area,filter_dead)

    @staticmethod
    def GetNearestGadgetToAgent(agent_id, area=5000,filter_dead= True):
        """
        Purpose: Get the nearest gadget to an agent based on its ID.
        Args:
            agent_id (int): The ID of the agent.
            area (int, optional): The area to search for the nearest gadget. Default is 5000.
        Returns: PyAgent
        """
        agent_instance = PyAgent.PyAgent(agent_id)
        return Agent.GetNearestAgentOfTypeXY("Gadget", agent_instance.x, agent_instance.y,area,filter_dead)

    @staticmethod
    def GetNearestAlly(area=5000,filter_dead= True):
        """
        Purpose: Get the nearest ally based on the player's coordinates.
        Args:
            area (int, optional): The area to search for the nearest ally. Default is 5000.
        Returns: PyAgent
        """
        x, y = Player.GetPlayerXY()
        return Agent.GetNearestAgentOfTypeXY("Ally", x, y, area,filter_dead)

    @staticmethod
    def GetNearestNeutral(area=5000,filter_dead= True):
        """
        Purpose: Get the nearest neutral agent based on the player's coordinates.
        Args:
            area (int, optional): The area to search for the nearest neutral agent. Default is 5000.
        Returns: PyAgent
        """
        x, y = Player.GetPlayerXY()
        return Agent.GetNearestAgentOfTypeXY("Neutral", x, y, area,filter_dead)

    @staticmethod
    def GetNearestEnemy(area=5000,filter_dead= True):
        """
        Purpose: Get the nearest enemy based on the player's coordinates.
        Args:
            area (int, optional): The area to search for the nearest enemy. Default is 5000.
        Returns: PyAgent
        """
        x, y = Player.GetPlayerXY()
        return Agent.GetNearestAgentOfTypeXY("Enemy", x, y, area,filter_dead)

    @staticmethod
    def GetNearestSpiritPet(area=5000,filter_dead= True):
        """
        Purpose: Get the nearest spirit pet based on the player's coordinates.
        Args:
            area (int, optional): The area to search for the nearest spirit pet. Default is 5000.
        Returns: PyAgent
        """
        x, y = Player.GetPlayerXY()
        return Agent.GetNearestAgentOfTypeXY("SpiritPet", x, y, area,filter_dead)

    @staticmethod
    def GetNearestMinion(area=5000,filter_dead= True):
        """
        Purpose: Get the nearest minion based on the player's coordinates.
        Args:
            area (int, optional): The area to search for the nearest minion. Default is 5000.
        Returns: PyAgent
        """
        x, y = Player.GetPlayerXY()
        return Agent.GetNearestAgentOfTypeXY("Minion", x, y, area,filter_dead)

    @staticmethod
    def GetNearestNPCMinipet(area=5000, filter_dead= True):
        """
        Purpose: Get the nearest NPC minipet based on the player's coordinates.
        Args:
            area (int, optional): The area to search for the nearest NPC minipet. Default is 5000.
        Returns: PyAgent
        """
        x, y = Player.GetPlayerXY()
        return Agent.GetNearestAgentOfTypeXY("NPCMinipet", x, y, area,filter_dead)

    @staticmethod
    def GetNearestItem(area=5000, filter_dead=True):
        """
        Purpose: Get the nearest item based on the player's coordinates.
        Args:
            area (int, optional): The area to search for the nearest item. Default is 5000.
        Returns: PyAgent
        """
        x, y = Player.GetPlayerXY()
        return Agent.GetNearestAgentOfTypeXY("Item", x, y, area,filter_dead)

    @staticmethod
    def GetNearestGadget(area=5000, filter_dead=True):
        """
        Purpose: Get the nearest gadget based on the player's coordinates.
        Args:
            area (int, optional): The area to search for the nearest gadget. Default is 5000.
        Returns: PyAgent
        """
        x, y = Player.GetPlayerXY()
        return Agent.GetNearestAgentOfTypeXY("Gadget", x, y, area,filter_dead)

    @staticmethod
    def GetName(agent_id):
        """
        Purpose: Get the name of an agent by its ID.
        Args:
            agent_id (int): The ID of the agent.
        Returns: str
        """
        agent_instance = PyAgent.PyAgent(agent_id)
        return agent_instance.living_agent.name

    @staticmethod
    def GetProfessions(agent_id):
        """
        Purpose: Retrieve the player's primary and secondary professions.
        Args: agent_id
        Returns: tuple
        """
        agent_instance = PyAgent.PyAgent(agent_id)

        return agent_instance.living_agent.profession, agent_instance.living_agent.secondary_profession

    @staticmethod
    def GetProfessionNames(agent_id):
        """
        Purpose: Retrieve the names of the player's primary and secondary professions.
        Args: agent_id
        Returns: tuple
        """
        agent_instance = PyAgent.PyAgent(agent_id)
        return agent_instance.living_agent.profession.GetName(), agent_instance.living_agent.secondary_profession.GetName()

    @staticmethod
    def GetProfessionShortNames(agent_id):
        """
        Purpose: Retrieve the short names of the player's primary and secondary professions.
        Args: agent_id
        Returns: tuple
        """
        agent_instance = PyAgent.PyAgent(agent_id)
        return agent_instance.living_agent.profession.GetShortName(), agent_instance.living_agent.secondary_profession.GetShortName()

    @staticmethod
    def GetProfessionIDs(agent_id):
        """
        Purpose: Retrieve the IDs of the player's primary and secondary professions.
        Args: agent_id
        Returns: tuple
        """
        player = PyPlayer.PyPlayer()
        agent_instance = PyAgent.PyAgent(agent_id)
        return agent_instance.living_agent.profession.ToInt(), agent_instance.living_agent.secondary_profession.ToInt()

    @staticmethod
    def GetLevel(agent_id):
        """
        Purpose: Retrieve the level of the player.
        Args: agent_id
        Returns: int
        """
        agent_instance = PyAgent.PyAgent(agent_id)
        return agent_instance.living_agent.level

    @staticmethod
    def GetEnergy(agent_id):
        """
        Purpose: Retrieve the energy of the agent, only workd for players their heroes
        Args: agent_id
        Returns: int
        """
        agent_instance = PyAgent.PyAgent(agent_id)
        return agent_instance.living_agent.energy

    @staticmethod
    def GetMaxEnergy(agent_id):
        """
        Purpose: Retrieve the maximum energy of the agent, only works for players and heroes.
        Args: agent_id
        Returns: int
        """
        agent_instance = PyAgent.PyAgent(agent_id)
        return agent_instance.living_agent.max_energy

    @staticmethod
    def GetEnergyRegen(agent_id):
        """
        Purpose: Retrieve the energy regeneration of the agent, only works for players and heroes.
        Args: agent_id
        Returns: int
        """
        agent_instance = PyAgent.PyAgent(agent_id)
        return agent_instance.living_agent.energy_regen

    @staticmethod
    def GetHealth(agent_id):
        """
        Purpose: Retrieve the health of the agent.
        Args: agent_id
        Returns: int
        """
        agent_instance = PyAgent.PyAgent(agent_id)
        return agent_instance.living_agent.hp

    @staticmethod
    def GetMaxHealth(agent_id):
        """
        Purpose: Retrieve the maximum health of the agent.
        Args: agent_id
        Returns: int
        """
        agent_instance = PyAgent.PyAgent(agent_id)
        return agent_instance.living_agent.max_hp

    @staticmethod
    def GetHealthRegen(agent_id):
        """
        Purpose: Retrieve the health regeneration of the agent.
        Args: agent_id
        Returns: int
        """
        agent_instance = PyAgent.PyAgent(agent_id)
        return agent_instance.living_agent.hp_regen

    @staticmethod
    def IsMoving(agent_id):
        """
        Purpose: Check if the agent is moving.
        Args: agent_id
        Returns: bool
        """
        agent_instance = PyAgent.PyAgent(agent_id)
        return agent_instance.living_agent.is_moving

    @staticmethod
    def GetVelocityVector(agent_id):
        """
        Purpose: Retrieve the velocity vector of the agent.
        Args: agent_id
        Returns: tuple
        """
        agent_instance = PyAgent.PyAgent(agent_id)
        return agent_instance.velocity_x, agent_instance.velocity_y

    @staticmethod
    def IsNockedDown(agent_id):
        """
        Purpose: Check if the agent is knocked down.
        Args: agent_id
        Returns: bool
        """
        agent_instance = PyAgent.PyAgent(agent_id)
        return agent_instance.living_agent.is_knocked_down

    @staticmethod
    def IsBleeding(agent_id):
        """
        Purpose: Check if the agent is bleeding.
        Args: agent_id
        Returns: bool
        """
        agent_instance = PyAgent.PyAgent(agent_id)
        return agent_instance.living_agent.is_bleeding

    @staticmethod
    def IsCrippled(agent_id):
        """
        Purpose: Check if the agent is crippled.
        Args: agent_id
        Returns: bool
        """
        agent_instance = PyAgent.PyAgent(agent_id)
        return agent_instance.living_agent.is_crippled

    @staticmethod
    def IsDeepWounded(agent_id):
        """
        Purpose: Check if the agent is deep wounded.
        Args: agent_id
        Returns: bool
        """
        agent_instance = PyAgent.PyAgent(agent_id)
        return agent_instance.living_agent.is_deep_wounded

    @staticmethod
    def IsPoisoned(agent_id):
        """
        Purpose: Check if the agent is poisoned.
        Args: agent_id
        Returns: bool
        """
        agent_instance = PyAgent.PyAgent(agent_id)
        return agent_instance.living_agent.is_poisoned

    @staticmethod
    def IsConditioned(agent_id):
        """
        Purpose: Check if the agent is conditioned.
        Args: agent_id
        Returns: bool
        """
        agent_instance = PyAgent.PyAgent(agent_id)
        return agent_instance.living_agent.is_conditioned

    @staticmethod
    def IsEnchanted(agent_id):
        """
        Purpose: Check if the agent is enchanted.
        Args: agent_id
        Returns: bool
        """
        agent_instance = PyAgent.PyAgent(agent_id)
        return agent_instance.living_agent.is_enchanted

    @staticmethod
    def IsHexed(agent_id):
        """
        Purpose: Check if the agent is hexed.
        Args: agent_id
        Returns: bool
        """
        agent_instance = PyAgent.PyAgent(agent_id)
        return agent_instance.living_agent.is_hexed

    @staticmethod
    def IsDegenHexed(agent_id):
        """
        Purpose: Check if the agent is degen hexed.
        Args: agent_id
        Returns: bool
        """
        agent_instance = PyAgent.PyAgent(agent_id)
        return agent_instance.living_agent.is_degen_hexed
     
    @staticmethod
    def IsDead(agent_id):
        """
        Purpose: Check if the agent is dead.
        Args: agent_id
        Returns: bool
        """
        agent_instance = PyAgent.PyAgent(agent_id)
        return agent_instance.living_agent.is_dead

    @staticmethod
    def IsAlive(agent_id):
        """
        Purpose: Check if the agent is alive.
        Args: agent_id
        Returns: bool
        """
        agent_instance = PyAgent.PyAgent(agent_id)
        return agent_instance.living_agent.is_alive

    @staticmethod
    def IsWeaponSpelled(agent_id):
        """
        Purpose: Check if the agent's weapon is spelled.
        Args: agent_id
        Returns: bool
        """
        agent_instance = PyAgent.PyAgent(agent_id)
        return agent_instance.living_agent.is_weapon_spelled
    
    @staticmethod
    def IsInCombatStance(agent_id):
        """
        Purpose: Check if the agent is in combat stance.
        Args: agent_id
        Returns: bool
        """
        return Agent.IsInCombatStance(agent_id)
    
    @staticmethod
    def IsAttacking(agent_id):
        """
        Purpose: Check if the agent is attacking.
        Args: agent_id
        Returns: bool
        """
        agent_instance = PyAgent.PyAgent(agent_id)
        return agent_instance.living_agent.is_attacking

    @staticmethod
    def IsCasting(agent_id):
        """
        Purpose: Check if the agent is casting.
        Args: agent_id
        Returns: bool
        """
        agent_instance = PyAgent.PyAgent(agent_id)
        return agent_instance.living_agent.is_casting

    @staticmethod
    def IsIdle(agent_id):
        """
        Purpose: Check if the agent is idle.
        Args: agent_id
        Returns: bool
        """
        agent_instance = PyAgent.PyAgent(agent_id)
        return agent_instance.living_agent.is_idle
    
    @staticmethod
    def HasBossGlow(agent_id):
        """
        Purpose: Check if the agent has a boss glow.
        Args: agent_id
        Returns: bool
        """
        agent_instance = PyAgent.PyAgent(agent_id)
        return agent_instance.living_agent.has_boss_glow

    @staticmethod
    def GetWeaponType(agent_id):
        """
        Purpose: Retrieve the weapon type of the agent.
        Args: agent_id
        Returns: str
        """
        agent_instance = PyAgent.PyAgent(agent_id)
        return agent_instance.living_agent.weapon_type.GetName()

    @staticmethod
    def GetWeaponExtraData(agent_id):
        """
        Purpose: Retrieve the weapon extra data of the agent.
        Args: agent_id
        Returns: tuple
        """
        agent_instance = PyAgent.PyAgent(agent_id)
        return agent_instance.living_agent.weapon_item_type, agent_instance.living_agent.offhand_item_type, agent_instance.living_agent.weapon_item_id, agent_instance.living_agent.offhand_item_id

    @staticmethod
    def IsMartial(agent_id):
        """
        Purpose: Check if the agent is martial.
        Args: agent_id
        Returns: bool
        """

        martial_weapon_types = [ 
        "Bow","Axe","Hammer","Daggers",
        "Scythe","Spear", "Sword"
        ]
        agent_instance = PyAgent.PyAgent(agent_id)
        
        return agent_instance.living_agent.weapon_type.GetName() in martial_weapon_types

    @staticmethod
    def IsCaster(agent_id):
        """
        Purpose: Check if the agent is a caster.
        Args: None
        Returns: bool
        """
        return not Agent.IsMartial(agent_id)

    @staticmethod
    def IsMelee(agent_id):
        """
        Purpose: Check if the agent is melee.
        Args: None
        Returns: bool
        """
        melee_weapon_types = [
            "Axe","Hammer","Daggers","Schythe","Sword"
        ]
        agent_instance = PyAgent.PyAgent(agent_id)
        return agent_instance.living_agent.weapon_type.GetName() in melee_weapon_types

    @staticmethod
    def IsRanged(agent_id):
        """
        Purpose: Check if the agent is ranged.
        Args: None
        Returns: bool
        """
        return not Agent.IsMelee(agent_id)

    @staticmethod
    def GetCastingSkill(agent_id):
        """
        Purpose: Retrieve the casting skill of the agent.
        Args: None
        Returns: int
        """
        agent_instance = PyAgent.PyAgent(agent_id)
        return agent_instance.living_agent.casting_skill_id
# Player
class Player:
    @staticmethod
    def SendDialog(dialog_id):
        """
        Purpose: Send a dialog response.
        Args:
            dialog_id (int): The ID of the dialog.
        Returns: None
        """
        player = PyPlayer.PyPlayer()
        player.SendDialog(dialog_id)

    @staticmethod
    def SendChatCommand(command):
        """
        Purpose: Send a '/' chat command.
        Args:
            command (str): The command to send.
        Returns: None
        """
        player = PyPlayer.PyPlayer()
        player.SendChatCommand(command)

    @staticmethod
    def SendChat(channel, message):
        """
        Purpose: Send a chat message to a channel.
        Args:
            channel (char): The channel to send the message to.
            message (str): The message to send.
        Returns: None
        """
        player = PyPlayer.PyPlayer()
        player.SendChat(channel, message)

    @staticmethod
    def SendWhisper(target_name, message):
        """
        Purpose: Send a whisper to a target player.
        Args:
            target_name (str): The name of the target player.
            message (str): The message to send.
        Returns: None
        """
        player = PyPlayer.PyPlayer()
        player.SendWhisper(target_name, message)

    @staticmethod
    def GetTargetID():
        """
        Purpose: Retrieve the ID of the player's target.
        Args: None
        Returns: int
        """
        player = PyPlayer.PyPlayer()
        return player.target_id

    @staticmethod
    def ChangeTarget (agent_id):
        """
        Purpose: Change the player's target.
        Args:
            agent_id (int): The ID of the agent to target.
        Returns: None
        """
        player = PyPlayer.PyPlayer()
        player.ChangeTarget(agent_id)
        
        
    @staticmethod
    def Interact(agent_id, call_target=False):
        """
        Purpose: Interact with an agent.
        Args:
            agent_id (int): The ID of the agent to interact with.
            call_target (bool, optional): Whether to call the agent as a target.
        Returns: None
        """
        player = PyPlayer.PyPlayer()
        player.InteractAgent(agent_id, call_target)

    @staticmethod
    def OpenLockedChest(use_key=False):
        """
        Purpose: Open a locked chest.
        Args:
            use_key (bool): Whether to use a key to open the chest.
        Returns: None
        """
        player = PyPlayer.PyPlayer()
        player.OpenLockedChest(use_key)

    @staticmethod
    def GetAgentID():
        """
        Purpose: Retrieve the agent ID of the player.
        Args: None
        Returns: int
        """
        player = PyPlayer.PyPlayer()
        agent = Agent.GetAgentByID(player.id)
        return agent.id

    @staticmethod
    def GetName():
        """
        Purpose: Retrieve the player's name.
        Args: None
        Returns: str
        """
        player = PyPlayer.PyPlayer()
        return Agent.GetName(player.id)

    @staticmethod
    def GetPlayerXY():
        """
        Purpose: Retrieve the player's current X and Y coordinates.
        Args: None
        Returns: tuple (x, y)
        """
        player = PyPlayer.PyPlayer()
        agent = Agent.GetAgentByID(player.id)
        return agent.x, agent.y

    @staticmethod
    def Move(x, y):
        """
        Purpose: Move the player to specified X and Y coordinates.
        Args:
            x (float): X coordinate.
            y (float): Y coordinate.
        Returns: None
        """
        player = PyPlayer.PyPlayer()
        player.Move(x, y)

    @staticmethod
    def CancelMove(self):
        """
        Purpose: Cancel the player's current move action.
        Args: None
        Returns: None
        """
        player_instance = PyPlayer.PyPlayer()
        player_agent = PyAgent.PyAgent(self.player_instance.id)
        if Map.IsMapReady():
            self.player_instance.Move(player_agent.x, player_agent.y)

    @staticmethod
    def GetAgentArray():
        """
        Purpose: Retrieve the player's agent array.
        Args: None
        Returns: list
        """
        player = PyPlayer.PyPlayer()
        return player.GetAgentArray()

    @staticmethod
    def GetAllyArray():
        """
        Purpose: Retrieve the player's ally array.
        Args: None
        Returns: list
        """
        player = PyPlayer.PyPlayer()
        return player.GetAllyArray()

    @staticmethod
    def GetNeutralArray():
        """
        Purpose: Retrieve the player's neutral array.
        Args: None
        Returns: list
        """
        player = PyPlayer.PyPlayer()
        return player.GetNeutralArray()

    @staticmethod
    def GetEnemyArray():
        """
        Purpose: Retrieve the player's enemy array.
        Args: None
        Returns: list
        """
        player = PyPlayer.PyPlayer()
        return player.GetEnemyArray()

    @staticmethod
    def GetSpiritPetArray():
        """
        Purpose: Retrieve the player's spirit pet array.
        Args: None
        Returns: list
        """
        player = PyPlayer.PyPlayer()
        return player.GetSpiritPetArray()

    @staticmethod
    def GetMinionArray():
        """
        Purpose: Retrieve the player's minion array.
        Args: None
        Returns: list
        """
        player = PyPlayer.PyPlayer()
        return player.GetMinionArray()

    @staticmethod
    def GetNPCMinipetArray():
        """
        Purpose: Retrieve the player's NPC minipet array.
        Args: None
        Returns: list
        """
        player = PyPlayer.PyPlayer()
        return player.GetNPCMinipetArray()

    @staticmethod
    def GetItemArray():
        """
        Purpose: Retrieve the player's item array.
        Args: None
        Returns: list
        """
        player = PyPlayer.PyPlayer()
        return player.GetItemArray()

    @staticmethod
    def GetGadgetArray():
        """
        Purpose: Retrieve the player's gadget array.
        Args: None
        Returns: list
        """
        player = PyPlayer.PyPlayer()
        return player.GetGadgetArray()

    class Routines:
        class Movement:
            class FollowXY:
                def __init__(self):
                    """
                    Purpose: Initialize the FollowXY object and set default values.
                    Routine for following a waypoint.
                    Returns: None
                    """
                    self.waypoint = (0, 0)
                    self.tolerance = 100
                    self.player_instance = PyPlayer.PyPlayer()
                    self.following = False
                    self.arrived = False
                    self.timer = Timer()
                    self.timer.start()
                    self.timer.stop()

                def calculate_distance(self, pos1, pos2):
                    """
                    Purpose: Calculate the Euclidean distance between two points.
                    Args:
                        pos1 (tuple): First position (x, y).
                        pos2 (tuple): Second position (x, y).
                    Returns: float
                    """
                    return math.sqrt((pos1[0] - pos2[0]) ** 2 + (pos1[1] - pos2[1]) ** 2)

                def Move(self, x, y, tolerance=100):
                    """
                    Purpose: Move the player to the specified coordinates.
                    Args:
                        x (float): X coordinate.
                        y (float): Y coordinate.
                        tolerance (int, optional): The tolerance distance to consider arrival. Default is 100.
                    Returns: None
                    """
                    if not self.following:
                        self.Reset()
                        self.waypoint = (x, y)
                        self.tolerance = tolerance
                        self.following = True
                        self.arrived = False
                        self.player_instance.Move(x, y)

                def Reset(self):
                    """
                    Purpose: Cancel the current move command and reset the waypoint following state.
                    Args: None
                    Returns: None
                    """
                    self.following = False
                    self.arrived = False
                    self.timer.reset()

                def Update(self):
                    """
                    Purpose: Update the FollowXY object's state, check if the player has reached the waypoint,
                    and issue new move commands if necessary.
                    Args: None
                    Returns: None
                    """
                    if self.following:
                        current_position = Player.GetPlayerXY()
                        if self.calculate_distance(self.waypoint, current_position) <= self.tolerance:
                            self.arrived = True
                            self.following = False

                    if self.following and not self.arrived:
                        agent_instance = PyAgent.PyAgent(self.player_instance.id)
                        if not agent_instance.living_agent.is_moving:
                            self.player_instance.Move(self.waypoint[0], self.waypoint[1])

                def GetElapsedTime(self):
                    """
                    Purpose: Get the elapsed time since the player started moving.
                    Args: None
                    Returns: float
                    """
                    return self.timer.get_elapsed_time()

                def SetWaypoint(self, x, y):
                    """
                    Purpose: Set the waypoint coordinates for the player to follow.
                    Args:
                        x (float): X coordinate.
                        y (float): Y coordinate.
                    Returns: None
                    """
                    self.waypoint = (x, y)
                    self.player_instance.Move(x, y)

                def GetWaypoint(self):
                    """
                    Purpose: Retrieve the coordinates of the current waypoint.
                    Args: None
                    Returns: tuple (x, y)
                    """
                    return self.waypoint

                def GetDistanceToWaypoint(self):
                    """
                    Purpose: Get the distance between the player and the current waypoint.
                    Args: None
                    Returns: float
                    """
                    current_position = Player.GetPlayerXY()
                    return self.calculate_distance(self.waypoint, current_position)

                def GetIsFollowing(self):
                    """
                    Purpose: Check if the player is currently following a waypoint.
                    Args: None
                    Returns: bool
                    """
                    return self.following

                def GetHasArrived(self):
                    """
                    Purpose: Check if the player has arrived at the current waypoint.
                    Args: None
                    Returns: bool
                    """
                    return self.arrived

            class PathHandler:
                def __init__(self, coordinates):
                    """
                    Purpose: Initialize the PathHandler with a list of coordinates.
                    Args:
                        coordinates (list): A list of tuples representing the points (x, y).
                    Returns: None
                    """
                    self.coordinates = coordinates
                    self.index = 0
                    self.reverse_direction_flag = False
                    self.finished = False

                def get_current_point(self):
                    """
                    Purpose: Get the current point in the list of coordinates.
                    Args: None
                    Returns: tuple or None
                    """
                    if self.coordinates:
                        return self.coordinates[self.index]
                    return None

                def get_next_point(self):
                    """
                    Purpose: Get the next point without advancing, or None if traversal is finished.
                    Args: None
                    Returns: tuple or None
                    """
                    if self.finished:
                        return None
                    if self.reverse_direction_flag:
                        if self.index > 0:
                            return self.coordinates[self.index - 1]
                    else:
                        if self.index < len(self.coordinates) - 1:
                            return self.coordinates[self.index + 1]
                    return None

                def get_current_point_and_advance(self):
                    """
                    Purpose: Get the current point and advance the pointer to the next point.
                    Args: None
                    Returns: tuple or None
                    """
                    if self.finished:
                        return None
                    current_point = self.get_current_point()
                    if self.reverse_direction_flag:
                        if self.index > 0:
                            self.index -= 1
                        else:
                            self.finished = True
                    else:
                        if self.index < len(self.coordinates) - 1:
                            self.index += 1
                        else:
                            self.finished = True
                    return current_point

                def reverse_direction(self):
                    """
                    Purpose: Reverse the direction of the traversal.
                    Args: None
                    Returns: None
                    """
                    self.reverse_direction_flag = not self.reverse_direction_flag
                    self.finished = False

                def reset_path(self):
                    """
                    Purpose: Reset the path traversal to the start or end, depending on the direction.
                    Args: None
                    Returns: None
                    """
                    self.index = 0 if not self.reverse_direction_flag else len(self.coordinates) - 1
                    self.finished = False

                def is_finished(self):
                    """
                    Purpose: Check if the traversal has finished.
                    Args: None
                    Returns: bool
                    """
                    return self.finished

                def set_position(self, index):
                    """
                    Purpose: Set the current index in the list of coordinates.
                    Args:
                        index (int): The index to set the position to.
                    Returns: None
                    """
                    if 0 <= index < len(self.coordinates):
                        self.index = index
                        self.finished = False
                    else:
                        raise IndexError(f"Index {index} out of bounds for coordinates list")

                def get_position(self):
                    """
                    Purpose: Get the current index in the list of coordinates.
                    Args: None
                    Returns: int
                    """
                    return self.index

                def advance_position(self, steps=1):
                    """
                    Purpose: Advance the pointer by a specified number of steps.
                    Args:
                        steps (int, optional): The number of steps to advance. Default is 1.
                    Returns: tuple or None
                    """
                    if self.reverse_direction_flag:
                        new_index = max(0, self.index - steps)
                    else:
                        new_index = min(len(self.coordinates) - 1, self.index + steps)
                    self.index = new_index
                    if (not self.reverse_direction_flag and self.index == len(self.coordinates) - 1) or \
                       (self.reverse_direction_flag and self.index == 0):
                        self.finished = True
                    else:
                        self.finished = False
                    return self.get_current_point()

                def retreat_position(self, steps=1):
                    """
                    Purpose: Move the pointer backward by a specified number of steps.
                    Args:
                        steps (int, optional): The number of steps to retreat. Default is 1.
                    Returns: tuple or None
                    """
                    return self.advance_position(-steps)


            def MoveIfHurt(threshold=0.7, FollowXY_Instance=None):
                """
                Purpose: Move the player away from danger if health is below the given threshold (default 70%).
                Args:
                    threshold (float): The health threshold below which the player will attempt to escape.
                    FollowXY_Instance your Global instance of FollowXY
                Returns:
                    bool: True if the player initiates movement, False if no movement is needed.
                """
    
                player_health = Agent.GetHealth(Player.GetAgentID())

                if player_health >= threshold:
                    return False

                player_position = Player.GetPlayerXY()

                # Initialize VectorFields for calculating escape direction
                vector_fields = Utils.VectorFields(player_position)

                # Get the array of enemies and filter only alive enemies within a range and add the array to the vector fields
                enemy_array = Player.GetEnemyArray()
                filtered_enemy_array = Utils.Filters.FilterAgentArrayByAlive(player_position, enemy_array, area=1350)
                vector_fields.add_agent_array('enemies', filtered_enemy_array, radius=1350, is_dangerous=True)

                # Compute the overall escape vector
                escape_vector = vector_fields.compute_combined_vector()

                # If the escape vector is non-zero, initiate movement
                if escape_vector != (0, 0):
                    new_x = player_position[0] + escape_vector[0] * 50  # Move by 50 units in the escape direction
                    new_y = player_position[1] + escape_vector[1] * 50

                    # Use the provided FollowXY instance or create a new one
                    if FollowXY_Instance is None:
                        FollowXY_Instance = Player.Routines.Movement.FollowXY()

                    # Move the player using the FollowXY instance
                    FollowXY_Instance.Move(new_x, new_y)
                    return True, FollowXY_Instance

                return False, FollowXY_Instance

        
        class Targeting:
            def GetBestTarget(a_range=1320, casting_only=False, no_hex_only=False, enchanted_only=False):
                """
                Purpose: Returns the best target within the specified range based on criteria like whether the agent is casting, enchanted, or hexed.
                Args:
                    a_range (int): The maximum distance for selecting targets.
                    casting_only (bool): If True, only select agents that are casting.
                    no_hex_only (bool): If True, only select agents that are not hexed.
                    enchanted_only (bool): If True, only select agents that are enchanted.
                Returns: PyAgent.PyAgent: The best target agent object, or None if no target matches.
                """
                best_target = None
                lowest_sum = float('inf')
                nearest_enemy = None
                nearest_distance = float('inf')
                lowest_hp_target = None
                lowest_hp = float('inf')

                player = PyPlayer.PyPlayer()
                player_pos = Player.GetPlayerXY()
                agents = player.GetEnemyArray()
                agents = Utils.Filters.FilterAgentArrayByAlive(player_pos, agents, a_range) #filter out Dead and Far agents

                if enchanted_only:
                    agents = Utils.Filters.FilterArrayByHasEnchantment(agents)

                if no_hex_only:
                    agents = Utils.Filters.FilterArrayByHasHex(agents)

                if casting_only:
                    agents = Utils.Filters.FilterArrayByIsCasting(agents)

                for agent_id in agents:
                    agent = PyAgent.PyAgent(agent_id)

                    distance_to_self = Utils.Distance(Player.GetPlayerXY(), (agent.x, agent.y))

                    # Track the nearest enemy
                    if distance_to_self < nearest_distance:
                        nearest_enemy = agent
                        nearest_distance = distance_to_self

                    # Track the agent with the lowest HP
                    agent_hp = agent.living_agent.hp
                    if agent_hp < lowest_hp:
                        lowest_hp = agent_hp
                        lowest_hp_target = agent

                    # Calculate the sum of distances between this agent and other agents within range
                    sum_distances = 0
                    for other_agent_id in agents:
                        other_agent = PyAgent.PyAgent(other_agent_id)
                        #no need to filter any agent since the array is filtered already
                        sum_distances += Utils.Distance((agent.x, agent.y), (other_agent.x, other_agent.y))

                    # Track the best target based on the sum of distances
                    if sum_distances < lowest_sum:
                        lowest_sum = sum_distances
                        best_target = agent

                return best_target

            def GetBestMeleeTarget(a_range=1320, casting_only=False, no_hex_only=False, enchanted_only=False):
                """
                Purpose: Returns the best melee most baslled up target within the specified range based on criteria like whether the agent is casting, enchanted, or hexed.
                Args:
                    a_range (int): The maximum distance for selecting targets.
                    casting_only (bool): If True, only select agents that are casting.
                    no_hex_only (bool): If True, only select agents that are not hexed.
                    enchanted_only (bool): If True, only select agents that are enchanted.
                Returns: PyAgent.PyAgent: The best melee target agent object, or None if no target matches.
                """
                best_target = None
                lowest_sum = float('inf')
                nearest_enemy = None
                nearest_distance = float('inf')
                lowest_hp_target = None
                lowest_hp = float('inf')

                player = PyPlayer.PyPlayer()
                player_pos = Player.GetPlayerXY()
                agents = player.GetEnemyArray()

                # Filter out dead, distant, and non-melee agents
                agents = Utils.Filters.FilterAgentArrayByAlive(player_pos, agents, a_range)
                agents = Utils.Filters.FilterAgentArrayByIsMelee(player_pos, agents, a_range)

                if enchanted_only:
                    agents = Utils.Filters.FilterArrayByHasEnchantment(agents)

                if no_hex_only:
                    agents = Utils.Filters.FilterArrayByHasHex(agents)

                if casting_only:
                    agents = Utils.Filters.FilterArrayByIsCasting(agents)

                for agent_id in agents:
                    agent = PyAgent.PyAgent(agent_id)

                    distance_to_self = Utils.Distance(Player.GetPlayerXY(), (agent.x, agent.y))

                    # Track the nearest melee enemy
                    if distance_to_self < nearest_distance:
                        nearest_enemy = agent
                        nearest_distance = distance_to_self

                    # Track the agent with the lowest HP
                    agent_hp = agent.living_agent.hp
                    if agent_hp < lowest_hp:
                        lowest_hp = agent_hp
                        lowest_hp_target = agent

                    # Calculate the sum of distances between this agent and other agents within range
                    sum_distances = 0
                    for other_agent_id in agents:
                        other_agent = PyAgent.PyAgent(other_agent_id)
                        sum_distances += Utils.Distance((agent.x, agent.y), (other_agent.x, other_agent.y))

                    # Track the best melee target based on the sum of distances
                    if sum_distances < lowest_sum:
                        lowest_sum = sum_distances
                        best_target = agent

                return best_target

class Skill:
    @staticmethod
    def GetName(skill_id):
        """
        Purpose: Retrieve the name of a skill by its ID.
        Args:
            skill_id (int): The ID of the skill to retrieve.
        Returns: str
        """
        skill_instance = PySkill.Skill(skill_id)
        return skill_instance.id.GetName()

    @staticmethod
    def GetTypeName(skill_id):
        """
        Purpose: Retrieve the type of a skill by its ID.
        Args:
            skill_id (int): The ID of the skill to retrieve.
        Returns: str
        """
        skill_instance = PySkill.Skill(skill_id)
        return skill_instance.type.GetName()


    @staticmethod
    def GetEnergyCost(skill_id):
        """
        Purpose: Retrieve the energy cost of a skill by its ID.
        Args:
            skill_id (int): The ID of the skill to retrieve.
        Returns: int
        """
        skill_instance = PySkill.Skill(skill_id)
        return skill_instance.energy_cost

class SkillBar:
    @staticmethod
    def LoadSkillTemplate(skill_template):
        """
        Purpose: Load a skill template by name.
        Args:
            template_name (str): The name of the skill template to load.
        Returns: None
        """
        skillbar_instance = PySkillbar.PySkillbar()
        skillbar_instance.LoadSkillTemplate(skill_template)
        
    @staticmethod
    def UseSkill(skill_slot, target_agent_id=0):
        """
        Purpose: Use a skill from the skill bar.
        Args:
            skill_slot (int): The slot number of the skill to use (1-8).
            target_agent_id (int, optional): The ID of the target agent. Default is 0.
        Returns: None
        """
        skillbar_instance = PySkillbar.PySkillbar()
        skillbar_instance.UseSkill(skill_slot, target_agent_id)

    @staticmethod
    def GetSkillIDBySlot(skill_slot):
        """
        Purpose: Retrieve the data of a skill by its slot number.
        Args:
            skill_slot (int): The slot number of the skill to retrieve (1-8).
        Returns: dict: A dictionary containing skill details retrieved by slot.
        """
        skillbar_instance = PySkillbar.PySkillbar()
        skill_id = skillbar_instance.GetSkillID(skill_slot)
        return skill_id

    @staticmethod
    def GetSkillSlot(skill_id):
        """
        Purpose: Retrieve the slot number of a skill by its ID.
        Args:
            skill_id (int): The ID of the skill to retrieve.
        Returns: int: The slot number where the skill is located.
        """
        skillbar_instance = PySkillbar.PySkillbar()
        return skillbar_instance.GetSkillSlot(skill_id)
    
    @staticmethod
    def GetSkilbarSkillData(skill_id):
        """
        Purpose: Retrieve the data of a skill by its ID.
        Args:
            skill_id (int): The ID of the skill to retrieve.
        Returns: dict: A dictionary containing skill details like ID, adrenaline, recharge, and event data.
        """
        skill_instance = PySkill.Skill(skill_id)
        return {
            "id": skill_instance.id.id,
            "adrenaline_a": skill_instance.adrenaline_a,
            "adrenaline_b": skill_instance.adrenaline_b,
            "recharge": skill_instance.recharge,
            "event": skill_instance.event
        }

    class Skill:
        @staticmethod
        def GetName(skill_id):
            """
            Purpose: Retrieve the name of a skill by its ID.
            Args:
                skill_id (int): The ID of the skill to retrieve.
            Returns: str
            """
            skill_instance = PySkill.Skill(skill_id)
            return skill_instance.id.GetName()

        @staticmethod
        def GetType(skill_id):
            """
            Purpose: Retrieve the type of a skill by its ID.
            Args:
                skill_id (int): The ID of the skill to retrieve.
            Returns: str
            """
            skill_instance = PySkill.Skill(skill_id)
            return skill_instance.type.GetName()

        def GetCampaign(skill_id):
            """
            Purpose: Retrieve the campaign of a skill by its ID.
            Args:
                skill_id (int): The ID of the skill to retrieve.
            Returns: str
            """
            skill_instance = PySkill.Skill(skill_id)
            return skill_instance.campaign.GetName()

        @staticmethod
        def GetSpecial(skill_id):
            """
            Purpose: Retrieve the special field.
            Args:
                skill_id (int): The ID of the skill to retrieve.
            Returns: str
            """
            skill_instance = PySkill.Skill(skill_id)
            return skill_instance.special

        @staticmethod
        def GetComboReq(skill_id):
            """
            Purpose: Retrieve the combo requirement of a skill by its ID.
            Args:
                skill_id (int): The ID of the skill to retrieve.
            Returns: str
            """
            skill_instance = PySkill.Skill(skill_id)
            return skill_instance.combo_req

        @staticmethod
        def GerEffect1(skill_id):
            """
            Purpose: Retrieve the first effect of a skill by its ID.
            Args:
                skill_id (int): The ID of the skill to retrieve.
            Returns: str
            """
            skill_instance = PySkill.Skill(skill_id)
            return skill_instance.effect1

        @staticmethod
        def GetEffect2(skill_id):
            """
            Purpose: Retrieve the second effect of a skill by its ID.
            Args:
                skill_id (int): The ID of the skill to retrieve.
            Returns: str
            """
            skill_instance = PySkill.Skill(skill_id)
            return skill_instance.effect2
        
        @staticmethod
        def GetCondition(skill_id):
            """
            Purpose: Retrieve the condition of a skill by its ID.
            Args:
                skill_id (int): The ID of the skill to retrieve.
            Returns: str
            """
            skill_instance = PySkill.Skill(skill_id)
            return skill_instance.condition

        @staticmethod
        def GetWeaponReq(skill_id):
            """
            Purpose: Retrieve the weapon requirement of a skill by its ID.
            Args:
                skill_id (int): The ID of the skill to retrieve.
            Returns: str
            """
            skill_instance = PySkill.Skill(skill_id)
            return skill_instance.weapon_req

        @staticmethod
        def GetProfession(skill_id):
            """
            Purpose: Retrieve the profession of a skill by its ID.
            Args:
                skill_id (int): The ID of the skill to retrieve.
            Returns: str
            """
            skill_instance = PySkill.Skill(skill_id)
            return skill_instance.profession.ToInt()

        @staticmethod
        def GetAttribute(skill_id):
            """
            Purpose: Retrieve the attribute of a skill by its ID.
            Args:
                skill_id (int): The ID of the skill to retrieve.
            Returns: str
            """
            skill_instance = PySkill.Skill(skill_id)
            return skill_instance.attribute.ToInt()

        @staticmethod
        def GetTitle(skill_id):
            """
            Purpose: Retrieve the title of a skill by its ID.
            Args:
                skill_id (int): The ID of the skill to retrieve.
            Returns: str
            """
            skill_instance = PySkill.Skill(skill_id)
            return skill_instance.title

        @staticmethod
        def GetIDPVP(skill_id):
            """
            Purpose: Retrieve the PvP ID of a skill by its ID.
            Args:
                skill_id (int): The ID of the skill to retrieve.
            Returns: int
            """
            skill_instance = PySkill.Skill(skill_id)
            return skill_instance.id_pvp

        @staticmethod
        def GetCombo(skill_id):
            """
            Purpose: Retrieve the combo of a skill by its ID.
            Args:
                skill_id (int): The ID of the skill to retrieve.
            Returns: str
            """
            skill_instance = PySkill.Skill(skill_id)
            return skill_instance.combo

        @staticmethod
        def GetTarget(skill_id):
            """
            Purpose: Retrieve the target of a skill by its ID.
            Args:
                skill_id (int): The ID of the skill to retrieve.
            Returns: str
            """
            skill_instance = PySkill.Skill(skill_id)
            return skill_instance.target

        @staticmethod
        def GetSkillEquipType(skill_id):
            """
            Purpose: Retrieve the skill equip type of a skill by its ID.
            Args:
                skill_id (int): The ID of the skill to retrieve.
            Returns: str
            """
            skill_instance = PySkill.Skill(skill_id)
            return skill_instance.skill_equip_type
            
        @staticmethod
        def GetOvercast(skill_id):
            """
            Purpose: Retrieve the overcast of a skill by its ID.
            Args:
                skill_id (int): The ID of the skill to retrieve.
            Returns: int
            """
            skill_instance = PySkill.Skill(skill_id)
            return skill_instance.overcast
   
        @staticmethod
        def GetEnergyCost(skill_id):
            """
            Purpose: Retrieve the energy cost of a skill by its ID.
            Args:
                skill_id (int): The ID of the skill to retrieve.
            Returns: int
            """
            skill_instance = PySkill.Skill(skill_id)
            return skill_instance.energy_cost

        @staticmethod
        def GetHealthCost(skill_id):
            """
            Purpose: Retrieve the health cost of a skill by its ID.
            Args:
                skill_id (int): The ID of the skill to retrieve.
            Returns: int
            """
            skill_instance = PySkill.Skill(skill_id)
            return skill_instance.health_cost

        @staticmethod
        def GetAdrenaline(skill_id):
            """
            Purpose: Retrieve the adrenaline cost of a skill by its ID.
            Args:
                skill_id (int): The ID of the skill to retrieve.
            Returns: int
            """
            skill_instance = PySkill.Skill(skill_id)
            return skill_instance.adrenaline

        @staticmethod
        def GetActivation(skill_id):
            """
            Purpose: Retrieve the activation time of a skill by its ID.
            Args:
                skill_id (int): The ID of the skill to retrieve.
            Returns: int
            """
            skill_instance = PySkill.Skill(skill_id)
            return skill_instance.activation

        
        @staticmethod
        def GetAftercast(skill_id):
            """
            Purpose: Retrieve the aftercast of a skill by its ID.
            Args:
                skill_id (int): The ID of the skill to retrieve.
            Returns: int
            """
            skill_instance = PySkill.Skill(skill_id)
            return skill_instance.aftercast
        
        @staticmethod
        def GetDuration0(skill_id):
            """
            Purpose: Retrieve the duration of a skill at 0 points by its ID.
            Args:
                skill_id (int): The ID of the skill to retrieve.
            Returns: int
            """
            skill_instance = PySkill.Skill(skill_id)
            return skill_instance.duration_0pts

        @staticmethod
        def GetDuration15(skill_id):
            """
            Purpose: Retrieve the duration of a skill at 15 points by its ID.
            Args:
                skill_id (int): The ID of the skill to retrieve.
            Returns: int
            """
            skill_instance = PySkill.Skill(skill_id)
            return skill_instance.duration_15pts

        @staticmethod
        def GetRecharge(skill_id):
            """
            Purpose: Retrieve the recharge time of a skill by its ID.
            Args:
                skill_id (int): The ID of the skill to retrieve.
            Returns: int
            """
            skill_instance = PySkill.Skill(skill_id)
            return skill_instance.recharge

        @staticmethod
        def GetSkillArguments(skill_id):
            """
            Purpose: Retrieve the skill arguments of a skill by its ID.
            Args:
                skill_id (int): The ID of the skill to retrieve.
            Returns: str
            """
            skill_instance = PySkill.Skill(skill_id)
            return skill_instance.skill_arguments

        @staticmethod
        def GetScale0(skill_id):
            """
            Purpose: Retrieve the scale of a skill at 0 points by its ID.
            Args:
                skill_id (int): The ID of the skill to retrieve.
            Returns: float
            """
            skill_instance = PySkill.Skill(skill_id)
            return skill_instance.scale_0pts

        @staticmethod
        def GetScale15(skill_id):
            """
            Purpose: Retrieve the scale of a skill at 15 points by its ID.
            Args:
                skill_id (int): The ID of the skill to retrieve.
            Returns: float
            """
            skill_instance = PySkill.Skill(skill_id)
            return skill_instance.scale_15pts

        @staticmethod
        def GetBonusScale0(skill_id):
            """
            Purpose: Retrieve the bonus scale of a skill at 0 points by its ID.
            Args:
                skill_id (int): The ID of the skill to retrieve.
            Returns: float
            """
            skill_instance = PySkill.Skill(skill_id)
            return skill_instance.bonus_scale_0pts

        @staticmethod
        def GetBonusScale15(skill_id):
            """
            Purpose: Retrieve the bonus scale of a skill at 15 points by its ID.
            Args:
                skill_id (int): The ID of the skill to retrieve.
            Returns: float
            """
            skill_instance = PySkill.Skill(skill_id)
            return skill_instance.bonus_scale_15pts

        @staticmethod
        def GetAoERange(skill_id):
            """
            Purpose: Retrieve the AoE range of a skill by its ID.
            Args:
                skill_id (int): The ID of the skill to retrieve.
            Returns: int
            """
            skill_instance = PySkill.Skill(skill_id)
            return skill_instance.aoe_range

        @staticmethod
        def GetConstEffect(skill_id):
            """
            Purpose: Retrieve the constant effect of a skill by its ID.
            Args:
                skill_id (int): The ID of the skill to retrieve.
            Returns: str
            """
            skill_instance = PySkill.Skill(skill_id)
            return skill_instance.const_effect

        @staticmethod
        def GetCasterOverheadAnimationID(skill_id):
            """
            Purpose: Retrieve the caster overhead animation ID of a skill by its ID.
            Args:
                skill_id (int): The ID of the skill to retrieve.
            Returns: int
            """
            skill_instance = PySkill.Skill(skill_id)
            return skill_instance.caster_overhead_animation_id

        @staticmethod
        def GetCasterBodyAnimationID(skill_id):
            """
            Purpose: Retrieve the caster body animation ID of a skill by its ID.
            Args:
                skill_id (int): The ID of the skill to retrieve.
            Returns: int
            """
            skill_instance = PySkill.Skill(skill_id)
            return skill_instance.caster_body_animation_id

        @staticmethod
        def GetTargetBodyAnimationID(skill_id):
            """
            Purpose: Retrieve the target body animation ID of a skill by its ID.
            Args:
                skill_id (int): The ID of the skill to retrieve.
            Returns: int
            """
            skill_instance = PySkill.Skill(skill_id)
            return skill_instance.target_body_animation_id

        @staticmethod
        def GetTargetOverheadAnimationID(skill_id):
            """
            Purpose: Retrieve the target overhead animation ID of a skill by its ID.
            Args:
                skill_id (int): The ID of the skill to retrieve.
            Returns: int
            """
            skill_instance = PySkill.Skill(skill_id)
            return skill_instance.target_overhead_animation_id

        @staticmethod
        def GetProjectileAnimation1ID(skill_id):
            """
            Purpose: Retrieve the first projectile animation ID of a skill by its ID.
            Args:
                skill_id (int): The ID of the skill to retrieve.
            Returns: int
            """
            skill_instance = PySkill.Skill(skill_id)
            return skill_instance.projectile_animation1_id

        @staticmethod
        def GetProjectileAnimation2ID(skill_id):
            """
            Purpose: Retrieve the second projectile animation ID of a skill by its ID.
            Args:
                skill_id (int): The ID of the skill to retrieve.
            Returns: int
            """
            skill_instance = PySkill.Skill(skill_id)
            return skill_instance.projectile_animation2_id

        @staticmethod
        def GetIconFileID(skill_id):
            """
            Purpose: Retrieve the icon file ID of a skill by its ID.
            Args:
                skill_id (int): The ID of the skill to retrieve.
            Returns: int
            """
            skill_instance = PySkill.Skill(skill_id)
            return skill_instance.icon_file_id

        @staticmethod
        def GetIconFileID2(skill_id):
            """
            Purpose: Retrieve the second icon file ID of a skill by its ID.
            Args:
                skill_id (int): The ID of the skill to retrieve.
            Returns: int
            """
            skill_instance = PySkill.Skill(skill_id)
            return skill_instance.icon_file2_id

        @staticmethod
        def GetNameID(skill_id):
            """
            Purpose: Retrieve the name ID of a skill by its ID.
            Args:
                skill_id (int): The ID of the skill to retrieve.
            Returns: int
            """
            skill_instance = PySkill.Skill(skill_id)
            return skill_instance.name_id

        @staticmethod
        def GetConcise(skill_id):
            """
            Purpose: Retrieve the concise description of a skill by its ID.
            Args:
                skill_id (int): The ID of the skill to retrieve.
            Returns: str
            """
            skill_instance = PySkill.Skill(skill_id)
            return skill_instance.concise

        @staticmethod
        def GetDescriptionID(skill_id):
            """
            Purpose: Retrieve the description ID of a skill by its ID.
            Args:
                skill_id (int): The ID of the skill to retrieve.
            Returns: int
            """
            skill_instance = PySkill.Skill(skill_id)
            return skill_instance.description_id

        @staticmethod
        def IsTouchRange(skill_id):
            """
            Purpose: Check if a skill has touch range.
            Args:
                skill_id (int): The ID of the skill to check.
            Returns: bool
            """
            skill_instance = PySkill.Skill(skill_id)
            return skill_instance.is_touch_range

        @staticmethod
        def IsElite(skill_id):
            """
            Purpose: Check if a skill is elite.
            Args:
                skill_id (int): The ID of the skill to check.
            Returns: bool
            """
            skill_instance = PySkill.Skill(skill_id)
            return skill_instance.is_elite

        @staticmethod
        def IsHalfRange(skill_id):
            """
            Purpose: Check if a skill has half range.
            Args:
                skill_id (int): The ID of the skill to check.
            Returns: bool
            """
            skill_instance = PySkill.Skill(skill_id)
            return skill_instance.is_half_range

        @staticmethod
        def IsPvP(skill_id):
            """
            Purpose: Check if a skill is PvP.
            Args:
                skill_id (int): The ID of the skill to check.
            Returns: bool
            """
            skill_instance = PySkill.Skill(skill_id)
            return skill_instance.is_pvp

        @staticmethod
        def IsPvE(skill_id):
            """
            Purpose: Check if a skill is PvE.
            Args:
                skill_id (int): The ID of the skill to check.
            Returns: bool
            """
            skill_instance = PySkill.Skill(skill_id)
            return skill_instance.is_pve

        @staticmethod

        def IsPlayable(skill_id):
            """
            Purpose: Check if a skill is playable.
            Args:
            skill_id (int): The ID of the skill to check.
            Returns: bool
            """
            skill_instance = PySkill.Skill(skill_id)
            return skill_instance.is_playable

        @staticmethod
        def IsStacking(skill_id):
            """
            Purpose: Check if a skill is stacking.
            Args:
            skill_id (int): The ID of the skill to check.
            Returns: bool
            """
            skill_instance = PySkill.Skill(skill_id)
            return skill_instance.is_stacking
        
        @staticmethod
        def IsNonStacking(skill_id):
            """
            Purpose: Check if a skill is non-stacking.
            Args:
            skill_id (int): The ID of the skill to check.
            Returns: bool
            """
            skill_instance = PySkill.Skill(skill_id)
            return skill_instance.is_non_stacking

        @staticmethod
        def IsUnused(skill_id):
            """
            Purpose: Check if a skill is unused.
            Args:
            skill_id (int): The ID of the skill to check.
            Returns: bool
            """
            skill_instance = PySkill.Skill(skill_id)
            return skill_instance.is_unused

        @staticmethod
        def GetAdrenalineA(skill_id):
            """
            Purpose: Retrieve the adrenaline A value of a skill by its ID.
            Args:
            skill_id (int): The ID of the skill to retrieve.
            Returns: int
            """
            skill_instance = PySkill.Skill(skill_id)
            return skill_instance.adrenaline_a

        @staticmethod
        def GetAdrenalineB(skill_id):
            """
            Purpose: Retrieve the adrenaline B value of a skill by its ID.
            Args:
            skill_id (int): The ID of the skill to retrieve.
            Returns: int
            """
            skill_instance = PySkill.Skill(skill_id)
            return skill_instance.adrenaline_b


class Bag(Enum):
    NoBag = 0
    Backpack = 1
    Belt_Pouch = 2
    Bag_1 = 3
    Bag_2 = 4
    Equipment_Pack = 5
    Material_Storage = 6
    Unclaimed_Items = 7
    Storage_1 = 8
    Storage_2 = 9
    Storage_3 = 10
    Storage_4 = 11
    Storage_5 = 12
    Storage_6 = 13
    Storage_7 = 14
    Storage_8 = 15
    Storage_9 = 16
    Storage_10 = 17
    Storage_11 = 18
    Storage_12 = 19
    Storage_13 = 20
    Storage_14 = 21
    Equipped_Items = 22
    Max = 23

class Inventory:
    @staticmethod
    def GetInventorySpace():
        """
        Purpose: Calculate and return the total number of items and the combined capacity of bags 1, 2, 3, and 4.
        Args: None
        Returns: tuple: (total_items, total_capacity)
            - total_items: The sum of items in the four bags.
            - total_capacity: The combined capacity (size) of the four bags.
        """
        bags_to_check = [Bag.Backpack, Bag.Belt_Pouch, Bag.Bag_1, Bag.Bag_2]
    
        total_items = 0
        total_capacity = 0
    
        for bag_enum in bags_to_check:
            bag_instance = PyInventory.Bag(bag_enum.value, bag_enum.name)
            total_capacity += bag_instance.GetSize()
            total_items += bag_instance.items_count

        return total_items, total_capacity

    @staticmethod
    def GetFreeSlotCount():
        """
        Purpose: Calculate and return the number of free slots in bags 1, 2, 3, and 4.
        Args: None
        Returns: int: The number of free slots available across the four bags.
        """
        total_items, total_capacity = Inventory.GetInventorySpace()
        free_slots = total_capacity - total_items
        return max(free_slots, 0)

    @staticmethod
    def GetItemCount(item_id):
        """
        Purpose: Count the number of items with the specified item_id in bags 1, 2, 3, and 4.
        Args:
            item_id (int): The ID of the item to count.
        Returns: int: The total number of items matching the item_id in bags 1, 2, 3, and 4.
        """
        bags_to_check = [Bag.Backpack, Bag.Belt_Pouch, Bag.Bag_1, Bag.Bag_2]
    
        total_item_count = 0
    
        for bag_enum in bags_to_check:
            bag_instance = PyInventory.Bag(bag_enum.value, bag_enum.name)
        
            for item in bag_instance.GetItems():
                if item.item_id == item_id:
                    total_item_count += item.quantity
    
        return total_item_count

    @staticmethod
    def GetModelCount(model_id):
        """
        Purpose: Count the number of items with the specified model_id in bags 1, 2, 3, and 4.
        Args:
            model_id (int): The model ID of the item to count.
        Returns: int: The total number of items matching the model_id in bags 1, 2, 3, and 4.
        """
        bags_to_check = [Bag.Backpack, Bag.Belt_Pouch, Bag.Bag_1, Bag.Bag_2]
    
        total_model_count = 0
    
        for bag_enum in bags_to_check:
            bag_instance = PyInventory.Bag(bag_enum.value, bag_enum.name)
        
            for item in bag_instance.GetItems():
                pyitem_instance = PyItem.Item(item.item_id)
            
                if pyitem_instance.model_id == model_id:
                    total_model_count += pyitem_instance.quantity
    
        return total_model_count

    @staticmethod
    def GetFirstIDKit():
        """
        Purpose: Find the first Identification Kit (ID Kit) in bags 1, 2, 3, and 4.
        Returns:
            int: The Item ID of the first ID Kit found, or 0 if no ID Kit is found.
        """
        bags_to_check = [Bag.Backpack, Bag.Belt_Pouch, Bag.Bag_1, Bag.Bag_2]
    
        for bag_enum in bags_to_check:
            bag_instance = PyInventory.Bag(bag_enum.value, bag_enum.name)
            for item in bag_instance.GetItems():
                pyitem_instance = PyItem.Item(item.item_id)
                if pyitem_instance.is_id_kit:
                    return pyitem_instance.item_id  # Return the ID of the first ID Kit found
    
        return 0  # Return 0 if no ID Kit is found

    @staticmethod
    def GetFirstUnidentifiedItem():
        """
        Purpose: Find the first unidentified item in bags 1, 2, 3, and 4.
        Returns:
            int: The Item ID of the first unidentified item found, or 0 if no unidentified item is found.
        """
        bags_to_check = [Bag.Backpack, Bag.Belt_Pouch, Bag.Bag_1, Bag.Bag_2]
    
        for bag_enum in bags_to_check:
            bag_instance = PyInventory.Bag(bag_enum.value, bag_enum.name)
            for item in bag_instance.GetItems():
                pyitem_instance = PyItem.Item(item.item_id)
                if not pyitem_instance.is_identified:  # Check if the item is not identified
                    return pyitem_instance.item_id  # Return the ID of the first unidentified item found
    
        return 0  # Return 0 if no unidentified item is found




    @staticmethod
    def GetFirstSalvageKit():
        """
        Purpose: Find the first available salvage kit in bags 1, 2, 3, and 4.
        Returns:
            int: The Item ID of the first salvage kit found, or 0 if no salvage kit is found.
        """
        bags_to_check = [Bag.Backpack, Bag.Belt_Pouch, Bag.Bag_1, Bag.Bag_2]
    
        for bag_enum in bags_to_check:
            bag_instance = PyInventory.Bag(bag_enum.value, bag_enum.name)
            for item in bag_instance.GetItems():
                pyitem_instance = PyItem.Item(item.item_id)
                if pyitem_instance.is_salvage_kit:
                    return pyitem_instance.item_id  # Return the ID of the first salvage kit found
    
        return 0  # Return 0 if no salvage kit is found

    
    @staticmethod
    def GetFirstSalvageableItem():
        """
        Purpose: Find the first salvageable item in bags 1, 2, 3, and 4.
        Returns:
            int: The Item ID of the first salvageable item found, or 0 if no salvageable item is found.
        """
        bags_to_check = [Bag.Backpack, Bag.Belt_Pouch, Bag.Bag_1, Bag.Bag_2]
    
        for bag_enum in bags_to_check:
            bag_instance = PyInventory.Bag(bag_enum.value, bag_enum.name)
            for item in bag_instance.GetItems():
                pyitem_instance = PyItem.Item(item.item_id)
                if pyitem_instance.is_salvageable:
                    return pyitem_instance.item_id  # Return the ID of the first salvageable item found
    
        return 0  # Return 0 if no salvageable item is found



    @staticmethod
    def IdentifyFirst():
        """
        Purpose: Identify the first unidentified item found in bags 1, 2, 3, and 4 using the first available ID kit.
                 Items are filtered by the given list of exact rarities (e.g., ["White", "Purple", "Gold"]).
        Args:
            rarities (list of str, optional): The rarity filter for identification.
        Returns:
            bool: True if an item was identified, False if no unidentified item or ID kit was found.
        """
        # Get the first ID Kit
        id_kit_id = Inventory.GetFirstIDKit()
        if id_kit_id == 0:
            Py4GW.Console.Log("IdentifyFirst", "No ID Kit found.")
            return False

        # Find the first unidentified item based on the rarity filter
        unid_item_id = Inventory.GetFirstUnidentifiedItem()
        if unid_item_id == 0:
            Py4GW.Console.Log("IdentifyFirst", "No unidentified item found.")
            return False

        # Use the ID Kit to identify the item
        inventory = PyInventory.Inventory()
        inventory.IdentifyItem(id_kit_id, unid_item_id)
        Py4GW.Console.Log("IdentifyFirst", f"Identified item with Item ID: {unid_item_id} using ID Kit ID: {id_kit_id}")
        return True


    @staticmethod
    def SalvageFirst():
        """
        Purpose: Salvage the first salvageable item found in bags 1, 2, 3, and 4 using the first available salvage kit.
                 Items are filtered by the given list of exact rarities (e.g., ["White", "Purple", "Gold"]).
        Args:
            rarities (list of str, optional): The rarity filter for salvage.
        Returns:
            bool: True if an item was salvaged, False if no salvageable item or salvage kit was found.
        """
        # Get the first available Salvage Kit
        salvage_kit_id = Inventory.GetFirstSalvageKit()
        if salvage_kit_id == 0:
            Py4GW.Console.Log("SalvageFirst", "No salvage kit found.")
            return False

        # Find the first salvageable item based on the rarity filter
        salvage_item_id = Inventory.GetFirstSalvageableItem()
        if salvage_item_id == 0:
            Py4GW.Console.Log("SalvageFirst", "No salvageable item found.")
            return False

        # Use the Salvage Kit to salvage the item
        inventory = PyInventory.Inventory()
        inventory.StartSalvage(salvage_kit_id, salvage_item_id)
        Py4GW.Console.Log("SalvageFirst", f"Started salvaging item with Item ID: {salvage_item_id} using Salvage Kit ID: {salvage_kit_id}")
        
        if inventory.IsSalvaging() and inventory.IsSalvageTransactionDone():
            inventory.FinishSalvage()
            Py4GW.Console.Log("SalvageFirst", f"Finished salvaging item with Item ID: {salvage_item_id}.")
            return True

        return False

    @staticmethod
    def IsInSalvageSession():
        """
        Purpose: Check if the player is currently salvaging.
        Returns: bool: True if the player is salvaging, False if not.
        """
        inventory = PyInventory.Inventory()
        return inventory.IsSalvaging()

    @staticmethod
    def IsSalvageSessionDone():
        """
        Purpose: Check if the salvage transaction is completed.
        Returns: bool: True if the salvage transaction is done, False if not.
        """
        inventory = PyInventory.Inventory()
        return inventory.IsSalvageTransactionDone()

    @staticmethod
    def FinishSalvage():
        """
        Purpose: Finish the salvage process.
        Returns: bool: True if the salvage process is finished, False if not.
        """
        inventory = PyInventory.Inventory()
        if inventory.IsSalvaging() and inventory.IsSalvageTransactionDone():
            inventory.FinishSalvage()
            Py4GW.Console.Log("FinishSalvage", "Finished the salvage process.")
            return True

        return False

    @staticmethod
    def OpenXunlaiWindow():
        """
        Purpose: Open the Xunlai Storage window.
        Returns: bool: True if the Xunlai Storage window is opened, False if not.
        """
        inventory = PyInventory.Inventory()
        inventory.OpenXunlaiWindow()
        return inventory.GetIsStorageOpen()

    @staticmethod
    def IsStorageOpen():
        """
        Purpose: Check if the Xunlai Storage window is open.
        Returns: bool: True if the Xunlai Storage window is open, False if not.
        """
        inventory = PyInventory.Inventory()
        return inventory.GetIsStorageOpen()

    @staticmethod
    def PickUpItem(item_id, call_target=False):
        """
        Purpose: Pick up an item from the ground.
        Args:
            item_id (int): The ID of the item to pick up. (not agent_id)
            call_target (bool, optional): True to call the target, False to pick up the item directly.
        Returns: None
        """
        inventory = PyInventory.Inventory()
        inventory.PickUpItem(item_id, call_target)

    @staticmethod
    def DropItem(item_id, quantity=1):
        """
        Purpose: Drop an item from the inventory.
        Args:
            item_id (int): The ID of the item to drop.
            quantity (int, optional): The quantity of the item to drop.
        Returns: None
        """
        inventory = PyInventory.Inventory()
        inventory.DropItem(item_id, quantity)

    @staticmethod
    def EquipItem(item_id, agent_id):
        """
        Purpose: Equip an item from the inventory.
        Args:
            item_id (int): The ID of the item to equip.
            agent_id (int): The agent ID of the player to equip the item.
        Returns: None
        """
        inventory = PyInventory.Inventory()
        inventory.EquipItem(item_id, agent_id)

    @staticmethod
    def UseItem(item_id):
        """ 
        Purpose: Use an item from the inventory.
        Args:
            item_id (int): The ID of the item to use.
        Returns: None
        """
        inventory = PyInventory.Inventory()
        inventory.UseItem(item_id)

    @staticmethod
    def DestroyItem(item_id):
        """
        Purpose: Destroy an item from the inventory.
        Args:
            item_id (int): The ID of the item to destroy.
        Returns: None
        """
        inventory = PyInventory.Inventory()
        inventory.DestroyItem(item_id)

    @staticmethod
    def GetHoveredItemId(item_id):
        """
        Purpose: Get the hovered item ID.
        Args: None
        Returns: int: The hovered item ID.
        """
        inventory = PyInventory.Inventory()
        return inventory.GetHoveredItemId(item_id)

    @staticmethod
    def GetGoldOnCharacter():
        """         
        Purpose: Retrieve the amount of gold on the character.
        Args: None
        Returns: int: The amount of gold on the character.
        """
        inventory = PyInventory.Inventory()
        return inventory.GetGoldAmount()

    @staticmethod
    def GetGoldInStorage():
        """
        Purpose: Retrieve the amount of gold in storage.
        Args: None
        Returns: int: The amount of gold in storage.
        """
        inventory = PyInventory.Inventory()
        return inventory.GetGoldAmountInStorage()

    @staticmethod
    def DepositGold(amount):
        """
        Purpose: Deposit gold into storage.
        Args:
            amount (int): The amount of gold to deposit.
        Returns: None
        """
        inventory = PyInventory.Inventory()
        inventory.DepositGold(amount)

    @staticmethod
    def WithdrawGold(amount):
        """
        Purpose: Withdraw gold from storage.
        Args:
            amount (int): The amount of gold to withdraw.
        Returns: None
        """
        inventory = PyInventory.Inventory()
        inventory.WithdrawGold(amount)

    @staticmethod
    def DropGold(amount):
        """
        Purpose: Drop a certain amount of gold.
        Args:
            amount (int): The amount of gold to drop.
        Returns: None
        """
        inventory = PyInventory.Inventory()
        inventory.DropGold(amount)
           
    @staticmethod
    def MoveItem(item_id, bag_id, slot, quantity=1):
        """ 
        Purpose: Move an item within a bag.
        Args:
            item_id (int): The ID of the item to move.
            bag_id (int): The ID of the bag to move the item to.
            slot (int): The slot to move the item to.
            quantity (int, optional): The quantity of the item to move.
        Returns: None
        """
        inventory = PyInventory.Inventory()
        inventory.MoveItem(item_id, bag_id, slot, quantity)

    class Item:

        @staticmethod
        def GetItemIdFromModelID(model_id):
            """
            Purpose: Retrieve the item ID from the model ID.
            Args:
                model_id (int): The model ID of the item.
            Returns: int: The item ID corresponding to the model ID, or 0 if no item is found.
            """
            # Bags to check (as defined in previous logic)
            bags_to_check = [Bag.Backpack, Bag.Belt_Pouch, Bag.Bag_1, Bag.Bag_2]

            # Iterate through each bag and its items
            for bag_enum in bags_to_check:
                bag_instance = PyInventory.Bag(bag_enum.value, bag_enum.name)
                for item in bag_instance.GetItems():
                    pyitem_instance = PyItem.Item(item.item_id)
            
                    # Check if the item's model ID matches the given model ID
                    if pyitem_instance.model_id == model_id:
                        return pyitem_instance.item_id  # Return the item ID if a match is found

            return 0  # Return 0 if no matching item is found

        @staticmethod
        def GetBagNumberByItemID(item_id):
            """
            Purpose: Returns the bag number that has an item id contained inside.
            Args:
                item_id (int): The item ID to search for.
            Returns:
                int: The bag number that contains the item, or 0 if not found.
            """
            # List of bags to check (Bag enum values were provided in earlier context)
            bags_to_check = [Bag.Backpack, Bag.Belt_Pouch, Bag.Bag_1, Bag.Bag_2]

            # Iterate over the bags, keeping track of the bag number (1-based index)
            for bag_number, bag_enum in enumerate(bags_to_check, start=1):
                bag_instance = PyInventory.Bag(bag_enum.value, bag_enum.name)

                # Check each item in the bag
                for item in bag_instance.GetItems():
                    if item.item_id == item_id:
                        return bag_number  # Return the 1-based bag number if item is found

            return 0  # Return 0 if the item was not found in any bag

        @staticmethod
        def GetModelID(item_id):
            """
            Purpose: Retrieve the model ID of an item by its ID.
            Args:
                item_id (int): The ID of the item to retrieve.
            Returns: int: The model ID of the item.
            """
            item =  PyItem.Item(item_id)
            return item.model_id

        @staticmethod
        def GetRarity(item_id):
            """
            Purpose: Retrieve the rarity of an item by its ID.
            Args:
                item_id (int): The ID of the item to retrieve.
            Returns: str: The rarity of the item.
            """
            item =  PyItem.Item(item_id)
            return item.rarity.name

        @staticmethod
        def GetAgentId(item_id):
            """
            Purpose: Retrieve the agent ID of an item by its ID.
            Args:
                item_id (int): The ID of the item to retrieve.
            Returns: int: The agent ID of the item.
            """
            item =  PyItem.Item(item_id)
            return item.agent_id

        @staticmethod
        def GetItemByAgentId(agent_id):
            """
            Purpose: Retrieve the item associated with a given agent ID.
            Args:
                agent_id (int): The agent ID to search for.
            Returns:
                PyItem.Item: The item object corresponding to the agent ID, or None if no item is found.
            """
            # Bags to check (Backpack, Belt Pouch, Bag 1, Bag 2, etc.)
            bags_to_check = [Bag.Backpack, Bag.Belt_Pouch, Bag.Bag_1, Bag.Bag_2]

            # Iterate over the bags
            for bag_enum in bags_to_check:
                bag_instance = PyInventory.Bag(bag_enum.value, bag_enum.name)

                # Iterate over the items in the bag
                for item in bag_instance.GetItems():
                    pyitem_instance = PyItem.Item(item.item_id)

                    # Check if the item's agent ID matches the given agent ID
                    if pyitem_instance.agent_id == agent_id:
                        return pyitem_instance  # Return the item if a match is found

            return None  # Return None if no matching item is found

        @staticmethod
        def GetModifiersCount(item_id):
            """
            Purpose: Retrieve the number of modifiers of an item by its ID.
            Args:
                item_id (int): The ID of the item to retrieve.
            Returns: int: The number of modifiers of the item.
            """
            item =  PyItem.Item(item_id)
            return len(item.modifiers)

        @staticmethod
        def GetModifiers(item_id):
            """
            Purpose: Retrieve the modifiers of an item by its ID.
            Args:
                item_id (int): The ID of the item to retrieve.
            Returns: list: The modifiers of the item.
            """
            item =  PyItem.Item(item_id)
            return item.modifiers

        @staticmethod
        def IsCustomized(item_id):
            """
            Purpose: Check if an item is customized by its ID.
            Args:
                item_id (int): The ID of the item to check.
            Returns: bool: True if the item is customized, False if not.
            """
            item =  PyItem.Item(item_id)
            return item.is_customized

        @staticmethod
        def GetItemType(item_id):
            """
            Purpose: Retrieve the item type of an item by its ID.
            Args:
                item_id (int): The ID of the item to retrieve.
            Returns: str: The item type of the item.
            """
            item =  PyItem.Item(item_id)
            return item.item_type.GetName()

        @staticmethod
        def GetDyeInfo(item_id):
            """
            Purpose: Retrieve the dye information of an item by its ID.
            Args:
                item_id (int): The ID of the item to retrieve.
            Returns: str: The dye information of the item.
            """
            item =  PyItem.Item(item_id)
            return item.dye_info.ToString()

        @staticmethod
        def GetValue(item_id):
            """
            Purpose: Retrieve the value of an item by its ID.
            Args:
                item_id (int): The ID of the item to retrieve.
            Returns: int: The value of the item.
            """
            item =  PyItem.Item(item_id)
            return item.value

        @staticmethod
        def GetInteraction(item_id):
            """
            Purpose: Retrieve the interaction of an item by its ID.
            Args:
                item_id (int): The ID of the item to retrieve.
            Returns: int: The interaction of the item.
            """
            item =  PyItem.Item(item_id)
            return item.interaction

        @staticmethod
        def GetItemFormula(item_id):
            """
            Purpose: Retrieve the item formula of an item by its ID.
            Args:
                item_id (int): The ID of the item to retrieve.
            Returns: int: The item formula of the item.
            """
            item =  PyItem.Item(item_id)
            return item.item_formula

        @staticmethod
        def IsMaterialSalvageable(item_id):
            """
            Purpose: Check if an item is material salvageable by its ID.
            Args:
                item_id (int): The ID of the item to check.
            Returns: bool: True if the item is material salvageable, False if not.
            """
            item =  PyItem.Item(item_id)
            return item.is_material_salvageable

        @staticmethod
        def GetQuantity(item_id):
            """
            Purpose: Retrieve the quantity of an item by its ID.
            Args:
                item_id (int): The ID of the item to retrieve.
            Returns: int: The quantity of the item.
            """
            item =  PyItem.Item(item_id)
            return item.quantity

        @staticmethod
        def IsEquipped(item_id):
            """
            Purpose: Check if an item is equipped by its ID.
            Args:
                item_id (int): The ID of the item to check.
            Returns: bool: True if the item is equipped, False if not.
            """
            item =  PyItem.Item(item_id)
            return item.equipped

        @staticmethod
        def GetProfession(item_id):
            """
            Purpose: Retrieve the profession of an item by its ID.
            Args:
                item_id (int): The ID of the item to retrieve.
            Returns: str: The profession of the item.
            """
            item =  PyItem.Item(item_id)
            return item.profession

        @staticmethod
        def GetSlot(item_id):
            """
            Purpose: Retrieve the slot of an item by its ID.
            Args:
                item_id (int): The ID of the item to retrieve.
            Returns: str: The slot of the item.
            """
            item =  PyItem.Item(item_id)
            return item.slot

        @staticmethod
        def IsStackable(item_id):
            """
            Purpose: Check if an item is stackable by its ID.
            Args:
                item_id (int): The ID of the item to check.
            Returns: bool: True if the item is stackable, False if not.
            """
            item =  PyItem.Item(item_id)
            return item.is_stackable

        @staticmethod
        def IsInscribable(item_id):
            """
            Purpose: Check if an item is inscribable by its ID.
            Args:
                item_id (int): The ID of the item to check.
            Returns: bool: True if the item is inscribable, False if not.
            """
            item =  PyItem.Item(item_id)
            return item.is_inscribable

        @staticmethod
        def IsMaterial(item_id):
            """
            Purpose: Check if an item is a material by its ID.
            Args:
                item_id (int): The ID of the item to check.
            Returns: bool: True if the item is a material, False if not.
            """
            item =  PyItem.Item(item_id)
            return item.is_material

        @staticmethod
        def IsZCoin(item_id):
            """
            Purpose: Check if an item is a ZCoin by its ID.
            Args:
                item_id (int): The ID of the item to check.
            Returns: bool: True if the item is a ZCoin, False if not.
            """
            item =  PyItem.Item(item_id)
            return item.is_zcoin

        @staticmethod
        def GetUses(item_id):
            """
            Purpose: Retrieve the uses of an item by its ID.
            Args:
                item_id (int): The ID of the item to retrieve.
            Returns: int: The uses of the item.
            """
            item =  PyItem.Item(item_id)
            return item.uses

        @staticmethod
        def IsIDKit(item_id):
            """
            Purpose: Check if an item is an ID Kit by its ID.
            Args:
                item_id (int): The ID of the item to check.
            Returns: bool: True if the item is an ID Kit, False if not.
            """
            item =  PyItem.Item(item_id)
            return item.is_id_kit

        @staticmethod
        def IsSalvageKit(item_id):
            """
            Purpose: Check if an item is a salvage kit by its ID.
            Args:
                item_id (int): The ID of the item to check.
            Returns: bool: True if the item is a salvage kit, False if not.
            """
            item =  PyItem.Item(item_id)
            return item.is_salvage_kit

        @staticmethod
        def IsTome(item_id):
            """
            Purpose: Check if an item is a tome by its ID.
            Args:
                item_id (int): The ID of the item to check.
            Returns: bool: True if the item is a tome, False if not.
            """
            item =  PyItem.Item(item_id)
            return item.is_tome

        @staticmethod
        def IsLesserKit(item_id):
            """
            Purpose: Check if an item is a lesser kit by its ID.
            Args:
                item_id (int): The ID of the item to check.
            Returns: bool: True if the item is a lesser kit, False if not.
            """
            item =  PyItem.Item(item_id)
            return item.is_lesser_kit

        @staticmethod
        def IsExpertSalvageKit(item_id):
            """
            Purpose: Check if an item is an expert salvage kit by its ID.
            Args:
                item_id (int): The ID of the item to check.
            Returns: bool: True if the item is an expert salvage kit, False if not.
            """
            item =  PyItem.Item(item_id)
            return item.is_expert_salvage_kit

        @staticmethod
        def IsPerfectSalvageKit(item_id):
            """
            Purpose: Check if an item is a perfect salvage kit by its ID.
            Args:
                item_id (int): The ID of the item to check.
            Returns: bool: True if the item is a perfect salvage kit, False if not.
            """
            item =  PyItem.Item(item_id)
            return item.is_perfect_salvage_kit

        @staticmethod
        def IsWeapon(item_id):
            """
            Purpose: Check if an item is a weapon by its ID.
            Args:
                item_id (int): The ID of the item to check.
            Returns: bool: True if the item is a weapon, False if not.
            """
            item =  PyItem.Item(item_id)
            return item.is_weapon

        @staticmethod
        def IsArmor(item_id):
            """
            Purpose: Check if an item is armor by its ID.
            Args:
                item_id (int): The ID of the item to check.
            Returns: bool: True if the item is armor, False if not.
            """
            item =  PyItem.Item(item_id)
            return item.is_armor

        @staticmethod
        def IsSalvageable(item_id):
            """
            Purpose: Check if an item is salvageable by its ID.
            Args:
                item_id (int): The ID of the item to check.
            Returns: bool: True if the item is salvageable, False if not.
            """
            item =  PyItem.Item(item_id)
            return item.is_salvageable

        @staticmethod
        def IsInventoryItem(item_id):
            """
            Purpose: Check if an item is an inventory item by its ID.
            Args:
                item_id (int): The ID of the item to check.
            Returns: bool: True if the item is an inventory item, False if not.
            """
            item =  PyItem.Item(item_id)
            return item.is_inventory_item

        @staticmethod
        def IsStorageItem(item_id):
            """
            Purpose: Check if an item is a storage item by its ID.
            Args:
                item_id (int): The ID of the item to check.
            Returns: bool: True if the item is a storage item, False if not.
            """
            item =  PyItem.Item(item_id)
            return item.is_storage_item

        @staticmethod
        def IsRareMaterial(item_id):
            """
            Purpose: Check if an item is a rare material by its ID.
            Args:
                item_id (int): The ID of the item to check.
            Returns: bool: True if the item is a rare material, False if not.
            """
            item =  PyItem.Item(item_id)
            return item.is_rare_material

        @staticmethod
        def IsOfferedInTrade(item_id):
            """
            Purpose: Check if an item is offered in trade by its ID.
            Args:
                item_id (int): The ID of the item to check.
            Returns: bool: True if the item is offered in trade, False if not.
            """
            item =  PyItem.Item(item_id)
            return item.is_offered_in_trade

        @staticmethod
        def IsSparkly(item_id):
            """
            Purpose: Check if an item is sparkly by its ID.
            Args:
                item_id (int): The ID of the item to check.
            Returns: bool: True if the item is sparkly, False if not.
            """
            item =  PyItem.Item(item_id)
            return item.is_sparkly

        @staticmethod
        def IsIdentified(item_id):
            """
            Purpose: Check if an item is identified by its ID.
            Args:
                item_id (int): The ID of the item to check.
            Returns: bool: True if the item is identified, False if not.
            """
            item =  PyItem.Item(item_id)
            return item.is_identified

        @staticmethod
        def IsPrefixUpgradable(item_id):
            """
            Purpose: Check if an item is prefix upgradable by its ID.
            Args:
                item_id (int): The ID of the item to check.
            Returns: bool: True if the item is prefix upgradable, False if not.
            """
            item =  PyItem.Item(item_id)
            return item.is_prefix_upgradable

        @staticmethod
        def IsSuffixUpgradable(item_id):
            """
            Purpose: Check if an item is suffix upgradable by its ID.
            Args:
                item_id (int): The ID of the item to check.
            Returns: bool: True if the item is suffix upgradable, False if not.
            """
            item =  PyItem.Item(item_id)
            return item.is_suffix_upgradable

        @staticmethod
        def IsStackable(item_id):
            """
            Purpose: Check if an item is stackable by its ID.
            Args:
                item_id (int): The ID of the item to check.
            Returns: bool: True if the item is stackable, False if not.
            """
            item =  PyItem.Item(item_id)
            return item.is_stackable

        @staticmethod
        def IsUsable(item_id):
            """
            Purpose: Check if an item is usable by its ID.
            Args:
                item_id (int): The ID of the item to check.
            Returns: bool: True if the item is usable, False if not.
            """
            item =  PyItem.Item(item_id)
            return item.is_usable

        @staticmethod
        def IsTradable(item_id):
            """
            Purpose: Check if an item is tradable by its ID.
            Args:
                item_id (int): The ID of the item to check.
            Returns: bool: True if the item is tradable, False if not.
            """
            item =  PyItem.Item(item_id)
            return item.is_tradable

        @staticmethod
        def IsInscription(item_id):
            """
            Purpose: Check if an item is an inscription by its ID.
            Args:
                item_id (int): The ID of the item to check.
            Returns: bool: True if the item is an inscription, False if not.
            """
            item =  PyItem.Item(item_id)
            return item.is_inscription

        @staticmethod
        def IsRarityBlue(item_id):
            """
            Purpose: Check if an item is blue rarity by its ID.
            Args:
                item_id (int): The ID of the item to check.
            Returns: bool: True if the item is blue rarity, False if not.
            """
            item =  PyItem.Item(item_id)
            return item.is_rarity_blue

        @staticmethod
        def IsRarityPurple(item_id):
            """
            Purpose: Check if an item is purple rarity by its ID.
            Args:
                item_id (int): The ID of the item to check.
            Returns: bool: True if the item is purple rarity, False if not.
            """
            item =  PyItem.Item(item_id)
            return item.is_rarity_purple

        @staticmethod
        def IsRarityGreen(item_id):
            """
            Purpose: Check if an item is green rarity by its ID.
            Args:
                item_id (int): The ID of the item to check.
            Returns: bool: True if the item is green rarity, False if not.
            """
            item =  PyItem.Item(item_id)
            return item.is_rarity_green

        @staticmethod
        def IsRarityGold(item_id):
            """
            Purpose: Check if an item is gold rarity by its ID.
            Args:
                item_id (int): The ID of the item to check.
            Returns: bool: True if the item is gold rarity, False if not.
            """
            item =  PyItem.Item(item_id)
            return item.is_rarity_gold

      
 


class Party:
    #tick is an option to check if party member is ready
    @staticmethod
    def IsTicked():
        """
        Purpose: Check if the party member is ready.
        Args: None
        Returns: bool
        """
        party_instance = PyParty.PyParty()
        return party_instance.tick.IsTicked()

    @staticmethod
    def SetTickasToggle(enable):
        """
        Purpose: Set the tick as a toggle.
        Args: Bool
        Returns: None
        """
        party_instance = PyParty.PyParty()
        party_instance.tick.SetTickToggle(enable)

    @staticmethod
    def SetTicked(ticked):
        """
        Purpose: Set the party member as ready.
        Args: None
        Returns: None
        """
        party_instance = PyParty.PyParty()
        party_instance.tick.SetTicked(ticked)

    @staticmethod
    def ToggleTicked():
        """
        Purpose: Toggle the party member's ready status.
        Args: None
        Returns: None
        """
        party_instance = PyParty.PyParty()
        party_instance.tick.ToggleTicked()

    @staticmethod
    def IsPartyDefeated():
        """
        Purpose: Check if the party has been defeated.
        Args: None
        Returns: bool
        """
        party_instance = PyParty.PyParty()
        return party_instance.is_party_defeated

    @staticmethod
    def IsPartyLoaded():
        """
        Purpose: Check if the party is loaded.
        Args: None
        Returns: bool
        """
        party_instance = PyParty.PyParty()
        return party_instance.is_party_loaded

    @staticmethod
    def IsPartyLeader():
        """
        Purpose: Check if the player is the party leader.
        Args: None
        Returns: bool
        """
        party_instance = PyParty.PyParty()
        return party_instance.is_party_leader
    
    @staticmethod
    def PartySize():
        """
        Purpose: Retrieve the size of the party.
        Args: None
        Returns: int
        """
        party_instance = PyParty.PyParty()
        return party_instance.party_size

    @staticmethod
    def PlayerCount():
        """
        Purpose: Retrieve the number of players in the party.
        Args: None
        Returns: int
        """
        party_instance = PyParty.PyParty()
        return party_instance.party_player_count

    @staticmethod
    def HeroCount():
        """
        Purpose: Retrieve the number of heroes in the party.
        Args: None
        Returns: int
        """
        party_instance = PyParty.PyParty()
        return party_instance.party_hero_count

    @staticmethod
    def HenchmanCount():
        """
        Purpose: Retrieve the number of henchmen in the party.
        Args: None
        Returns: int
        """
        party_instance = PyParty.PyParty()
        return party_instance.party_henchman_count

    @staticmethod
    def SearchParty(search_type, advertisement):
        """
        Search for a party.
        Args:
            search_type (int): The search type.
            advertisement (str): The advertisement.
        Returns: bool
        """
        party_instance = PyParty.PyParty()
        return party_instance.SearchParty(search_type, advertisement)

    @staticmethod
    def SearchPartyCancel():
        """
        Cancel the party search.
        Args: None
        Returns: None
        """
        party_instance = PyParty.PyParty()
        party_instance.SearchPartyCancel()

    @staticmethod
    def SearchPartyReply(accept):
        """
        Reply to a party search.
        Args:
            accept (bool): Whether to accept the party search.
        Returns: bool
        """
        party_instance = PyParty.PyParty()
        return party_instance.SearchPartyReply(accept)

    @staticmethod
    def RespondToPartyRequest(party_id, accept):
        """
        Respond to a party request.
        Args:
            party_id (int): The party ID.
            accept (bool): Whether to accept the party request.
        Returns: bool
        """
        party_instance = PyParty.PyParty()
        return party_instance.RespondToPartyRequest(party_id, accept)

    @staticmethod
    def GetAgentIDByLoginNumber(login_number):
        """
        Retrieve the agent ID by login number.
        Args:
            login_number (int): The login number.
        Returns: int
        """
        party_instance = PyParty.PyParty()
        return party_instance.GetAgentIDByLoginNumber(login_number)

    @staticmethod
    def GetHeroAgentID(hero_index):
        """
        Retrieve the agent ID of a hero by index.
        Args:
            hero_index (int): The hero index.
        Returns: int
        """
        party_instance = PyParty.PyParty()
        return party_instance.GetHeroAgentID(hero_index)

    @staticmethod
    def GetAgentHeroID(agent_id):
        """
        Retrieve the hero ID of an agent.
        Args:
            agent_id (int): The agent ID.
        Returns: int
        """
        party_instance = PyParty.PyParty()
        return party_instance.GetAgentHeroID(agent_id)

    @staticmethod
    def InvitePlayer(player_id_or_name):
        """
        Invite a player by ID (int) or name (str).
        Args: 
            player (int or str): The player ID or player name.
        """
        party_instance = PyParty.PyParty()

        if isinstance(player_id_or_name, int):
            party_instance.InvitePlayer(player_id_or_name)
        elif isinstance(player_id_or_name, str):
            Player.SendChatCommand("invite " + player_id_or_name)

        else:
            raise TypeError("Invalid argument type. Must be int (ID) or str (name).")

    @staticmethod
    def KickPlayer(player_id):
        """
        Kick a player from the party by ID.
        Args: 
            player_id (int): The player ID.
        """
        party_instance = PyParty.PyParty()
        party_instance.KickPlayer(player_id)

    @staticmethod
    def LeaveParty():
        """
        Leave the party.
        Args: None
        """
        party_instance = PyParty.PyParty()
        party_instance.LeaveParty()

    @staticmethod
    def SetHardMode():
        """
        Set the party to hard mode.
        Args: None
        """
        party_instance = PyParty.PyParty()
        if party_instance.is_hard_mode_unlocked and not party_instance.is_in_hard_mode:
            party_instance.SetHardMode(True)

    @staticmethod
    def SetNormalMode():
        """
        Set the party to normal mode.
        Args: None
        """
        party_instance = PyParty.PyParty()
        if party_instance.is_in_hard_mode:
            party_instance.SetHardMode(False)

    @staticmethod
    def IsHardMode():
        """
        Check if the party is in hard mode.
        Args: None
        Returns: bool
        """
        party_instance = PyParty.PyParty()
        return party_instance.is_in_hard_mode

    @staticmethod
    def IsNormalMode():
        """
        Check if the party is in normal mode.
        Args: None
        Returns: bool
        """
        return not Party.IsHardMode()

    @staticmethod
    def ReturnToOutpost():
        """
        Return to the outpost.
        Args: None
        """
        party_instance = PyParty.PyParty()
        party_instance.ReturnToOutpost()

    @staticmethod
    def AddHero(hero_id):
        """
        Add a hero to the party by ID.
        Args: 
            hero_id (int): The hero ID.
        """
        party_instance = PyParty.PyParty()
        party_instance.AddHero(hero_id)

    @staticmethod
    def KickHero(hero_id):
        """
        Kick a hero from the party by ID.
        Args: 
            hero_id (int): The hero ID.
        """
        party_instance = PyParty.PyParty()
        party_instance.KickHero(hero_id)

    @staticmethod
    def KickAllHeroes():
        """
        Kick all heroes from the party.
        Args: None
        """
        party_instance = PyParty.PyParty()
        party_instance.KickAllHeroes()

    @staticmethod
    def AddHenchman(henchman_id):
        """
        Add a henchman to the party by ID.
        Args: 
            henchman_id (int): The henchman ID.
        """
        party_instance = PyParty.PyParty()
        party_instance.AddHenchman(henchman_id)

    @staticmethod
    def KickHenchman(henchman_id):
        """
        Kick a henchman from the party by ID.
        Args: 
            henchman_id (int): The henchman ID.
        """
        party_instance = PyParty.PyParty()
        party_instance.KickHenchman(henchman_id)


    @staticmethod
    def FlagHero (hero_id, x, y):
        """
        Flag a hero to a specific location.
        Args:
            hero_id (int): The hero ID.
            x (float): The X coordinate.
            y (float): The Y coordinate.
        """
        party_instance = PyParty.PyParty()
        party_instance.FlagHero(hero_id, x, y)
        
    @staticmethod
    def FlagAllHeroes(x, y):
        """
        Flag all heroes to a specific location.
        Args:
            x (float): The X coordinate.
            y (float): The Y coordinate.
        """
        party_instance = PyParty.PyParty()
        party_instance.FlagAllHeroes(x, y)

    @staticmethod
    def UnflagHero(hero_id):
        """
        Unflag a hero.
        Args:
            hero_id (int): The hero ID.
        """
        party_instance = PyParty.PyParty()
        party_instance.UnflagHero(hero_id)
        
    @staticmethod
    def UnflagAllHeroes():
        """
        Unflag all heroes.
        Args: None
        """
        party_instance = PyParty.PyParty()
        party_instance.UnflagAllHeroes()

    @staticmethod
    def SetHeroBehavior (hero_agent_id, behavior):
        """
        Set the behavior of a hero.
        Args:
            hero_id (int): The hero agent ID.
            behavior (int): 0=Fight, 1=Guard, 2=Avoid
        """
        party_instance = PyParty.PyParty()
        party_instance.SetHeroBehavior(hero_agent_id, behavior)

    @staticmethod
    def SetPetBehavior(behavior, lock_target_id):
        """
        Set the behavior of a pet.
        Args:
            pet_id (int): The pet agent ID.
            behavior (int): 0=Fight, 1=Guard, 2=Avoid
        """
        party_instance = PyParty.PyParty()
        party_instance.SetPetBehavior(behavior, lock_target_id)

    @staticmethod
    def HeroUseSkill(target_agent_id, skill_number, hero_number):
        """
        Have a hero use a skill.
        Args:
            target_agent_id (int): The target agent ID.
            skill_number (int): The skill number (1-8)
            hero_number (int): The hero number (1-7)
        """
        party_instance = PyParty.PyParty()
        party_instance.HeroUseSkill(target_agent_id, skill_number, hero_number)

    @staticmethod
    def GetAgentIDByPlayerID(player_id):
        """
        Purpose: Get the agent ID of a party member by their player ID.
        Args:
            player_id (int): The player ID of the party member.
        Returns: int: The agent ID of the party member.
        """
        party_instance = PyParty.PyParty()
        agent_id = party_instance.GetAgentByPlayerID(player_id)
        
        return agent_id

    @staticmethod
    def GetPartyLeaderID():
        """
        Purpose: Get the agent ID of the party leader.
        Args: None
        Returns: int: The agent ID of the party leader.
        """
        players = Party.GetPlayers()
        leader = players[0]
        agent_id = Party.GetAgentIDByPlayerID(leader.player_id)
        return agent_id
  

    @staticmethod
    def GetPlayers():
        """
        Purpose: Get the list of player IDs in the party.
        Args: None
        Returns: list: A list of player IDs in the party.
        """
        party_instance = PyParty.PyParty()
        return party_instance.players
    
    @staticmethod
    def GetHeroes():
        """
        Purpose: Get the list of hero IDs in the party.
        Args: None
        Returns: list: A list of hero IDs in the party.
        """
        party_instance = PyParty.PyParty()
        return party_instance.heroes

    @staticmethod
    def GetHenchmen():
        """
        Purpose: Get the list of henchmen IDs in the party.
        Args: None
        Returns: list: A list of henchmen IDs in the party.
        """
        party_instance = PyParty.PyParty()
        return party_instance.henchmen
        
class ImGui:
    
    def toggle_button(label: str, v: bool) -> bool:
        """
        Purpose: Create a toggle button that changes its state and color based on the current state.
        Args:
            label (str): The label of the button.
            v (bool): The current toggle state (True for on, False for off).
        Returns: bool: The new state of the button after being clicked.
        """
        clicked = False

        if v:
            ImGui_Py.push_style_color(ImGui_Py.ImGuiCol.Button, (0.153, 0.318, 0.929, 1.0))  # On color
            ImGui_Py.push_style_color(ImGui_Py.ImGuiCol.ButtonHovered, (0.6, 0.6, 0.9, 1.0))  # Hover color
            ImGui_Py.push_style_color(ImGui_Py.ImGuiCol.ButtonActive, (0.6, 0.6, 0.6, 1.0))
            clicked = ImGui_Py.button(label)
            ImGui_Py.pop_style_color(3)
        else:
            clicked = ImGui_Py.button(label)
        if clicked:
            v = not v

        return v

    def table(title, headers, data):
        """
        Purpose: Display a table using ImGui_Py.
        Args:
            title (str): The title of the table.
            headers (list of str): The header names for the table columns.
            data (list of values or tuples): The data to display in the table. 
                - If it's a list of single values, display them in one column.
                - If it's a list of tuples, display them across multiple columns.
        Returns: None
        """
        if len(data) == 0:
            return  # No data to display

        first_row = data[0]
        if isinstance(first_row, tuple):
            num_columns = len(first_row)
        else:
            num_columns = 1  # Single values will be displayed in one column

        # Start the table with dynamic number of columns
        if ImGui_Py.begin_table(title, num_columns, ImGui_Py.TableFlags.Borders):
            for i, header in enumerate(headers):
                ImGui_Py.table_setup_column(header)
            ImGui_Py.table_headers_row()

            for row in data:
                ImGui_Py.table_next_row()
                if isinstance(row, tuple):
                    for i, cell in enumerate(row):
                        ImGui_Py.table_set_column_index(i)
                        ImGui_Py.text(str(cell))
                else:
                    ImGui_Py.table_set_column_index(0)
                    ImGui_Py.text(str(row))

            ImGui_Py.end_table()

class Buffs:

    @staticmethod
    def DropBuff(buff_id):
        """
        Purpose: Drop a specific buff by Buff Id.
        Args:
            skill_id (int): The skill ID of the buff to drop.
        Returns: None
        """
        agent_effects = PyEffects.PyEffects(Player.GetAgentID())
        agent_effects.DropBuff(buff_id)
    
    @staticmethod
    def GetBuffs(agent_id: int):
        """
        Purpose: Get the list of active buffs for a specific agent.
        Args:
            agent_id (int): The agent ID of the party member.
        Returns: list: A list of BuffType objects for the specified agent.
        """
        agent_effects = PyEffects.PyEffects(agent_id)
        buff_list = agent_effects.GetBuffs()
        return buff_list

    @staticmethod
    def GetEffects(agent_id: int):
        """
        Purpose: Get the list of active effects for a specific agent.
        Args:
            agent_id (int): The agent ID of the party member.
        Returns: list: A list of EffectType objects for the specified agent.
        """
        agent_effects = PyEffects.PyEffects(agent_id)
        effects_list = agent_effects.GetEffects()
        return effects_list

    @staticmethod
    def GetBuffCount(agent_id: int):
        """
        Purpose: Get the count of active buffs for a specific agent.
        Args:
            agent_id (int): The agent ID of the party member.
        Returns: int: The number of buffs applied to the agent.
        """
        agent_effects = PyEffects.PyEffects(agent_id)
        buff_count = agent_effects.GetBuffCount()
        return buff_count

    @staticmethod
    def GetEffectCount(agent_id: int):
        """
        Purpose: Get the count of active effects for a specific agent.
        Args:
            agent_id (int): The agent ID of the party member.
        Returns: int: The number of effects applied to the agent.
        """
        agent_effects = PyEffects.PyEffects(agent_id)
        effect_count = agent_effects.GetEffectCount()
        return effect_count

    @staticmethod
    def BuffExists(agent_id: int, skill_id: int):
        """
        Purpose: Check if a specific buff exists for a given agent and skill ID.
        Args:
            agent_id (int): The agent ID of the party member.
            skill_id (int): The skill ID of the buff.
        Returns: bool: True if the buff exists, False otherwise.
        """
        agent_effects = PyEffects.PyEffects(agent_id)
        buff_exists = agent_effects.BuffExists(skill_id)
        return buff_exists

    @staticmethod
    def EffectExists(agent_id: int, skill_id: int):
        """
        Purpose: Check if a specific effect exists for a given agent and skill ID.
        Args:
            agent_id (int): The agent ID of the party member.
            skill_id (int): The skill ID of the effect.
        Returns: bool: True if the effect exists, False otherwise.
        """
        agent_effects = PyEffects.PyEffects(agent_id)
        effect_exists = agent_effects.EffectExists(skill_id)
        return effect_exists

    @staticmethod
    def GetBuffsAndEffects(agent_id: int):
        """
        Purpose: Get the list of all active buffs and effects for a specific agent.
        Args:
            agent_id (int): The agent ID of the party member.
        Returns: dict: A dictionary containing 'buffs' and 'effects'.
                      - 'buffs' is a list of BuffType objects.
                      - 'effects' is a list of EffectType objects.
        """
        agent_effects = PyEffects.PyEffects(agent_id)
        buffs = agent_effects.GetBuffs()
        effects = agent_effects.GetEffects()
        return {
            'buffs': buffs,
            'effects': effects
        }


class Key(Enum):
    # Letters
    A = 0x41
    B = 0x42
    C = 0x43
    D = 0x44
    E = 0x45
    F = 0x46
    G = 0x47
    H = 0x48
    I = 0x49
    J = 0x4A
    K = 0x4B
    L = 0x4C
    M = 0x4D
    N = 0x4E
    O = 0x4F
    P = 0x50
    Q = 0x51
    R = 0x52
    S = 0x53
    T = 0x54
    U = 0x55
    V = 0x56
    W = 0x57
    X = 0x58
    Y = 0x59
    Z = 0x5A

    # Numbers (Top row, not numpad)
    Zero = 0x30
    One = 0x31
    Two = 0x32
    Three = 0x33
    Four = 0x34
    Five = 0x35
    Six = 0x36
    Seven = 0x37
    Eight = 0x38
    Nine = 0x39

    # Function keys
    F1 = 0x70
    F2 = 0x71
    F3 = 0x72
    F4 = 0x73
    F5 = 0x74
    F6 = 0x75
    F7 = 0x76
    F8 = 0x77
    F9 = 0x78
    F10 = 0x79
    F11 = 0x7A
    F12 = 0x7B

    # Control keys
    Shift = 0x10
    Ctrl = 0x11
    Alt = 0x12
    Enter = 0x0D
    Escape = 0x1B
    Space = 0x20
    Tab = 0x09
    Backspace = 0x08
    Delete = 0x2E
    Insert = 0x2D
    Home = 0x24
    End = 0x23
    PageUp = 0x21
    PageDown = 0x22

    # Arrow keys
    LeftArrow = 0x25
    UpArrow = 0x26
    RightArrow = 0x27
    DownArrow = 0x28

    # Numpad keys
    Numpad0 = 0x60
    Numpad1 = 0x61
    Numpad2 = 0x62
    Numpad3 = 0x63
    Numpad4 = 0x64
    Numpad5 = 0x65
    Numpad6 = 0x66
    Numpad7 = 0x67
    Numpad8 = 0x68
    Numpad9 = 0x69
    NumpadMultiply = 0x6A
    NumpadAdd = 0x6B
    NumpadSubtract = 0x6D
    NumpadDecimal = 0x6E
    NumpadDivide = 0x6F

    # Miscellaneous
    CapsLock = 0x14
    PrintScreen = 0x2C
    ScrollLock = 0x91
    Pause = 0x13

class Keystroke:
    key_sender = PyKeystroke.PyScanCodeKeystroke()

    @staticmethod
    def Press(key):
        """
        Purpose: Simulate a key press event using scan codes.
        Args:
            key (Key): The key to press.
        Returns: None
        """
        Keystroke.key_sender.PressKey(key.value)

    @staticmethod
    def Release(key):
        """
        Purpose: Simulate a key release event using scan codes.
        Args:
            key (Key): The key to release.
        Returns: None
        """
        Keystroke.key_sender.ReleaseKey(key.value)

    @staticmethod
    def PressAndRelease(key):
        """
        Purpose: Simulate a key press and release event using scan codes.
        Args:
            key (Key): The key to press and release.
        Returns: None
        """
        Keystroke.key_sender.PushKey(key.value)

    @staticmethod
    def PressCombo(modifiers):
        """
        Purpose: Simulate a key press event for multiple keys using scan codes.
        Args:
            modifiers (list of Key): The list of keys to press.
        Returns: None
        """
        keys = [key.value for key in modifiers]
        Keystroke.key_sender.PressKeyCombo(keys)

    @staticmethod
    def ReleaseCombo(modifiers):
        """
        Purpose: Simulate a key release event for multiple keys using scan codes.
        Args:
            modifiers (list of Key): The list of keys to release.
        Returns: None
        """
        keys = [key.value for key in modifiers]
        Keystroke.key_sender.ReleaseKeyCombo(keys)

    @staticmethod
    def PressAndReleaseCombo(modifiers):
        """
        Purpose: Simulate a key press and release event for multiple keys using scan codes.
        Args:
            modifiers (list of Key): The list of keys to press and release.
        Returns: None
        """
        keys = [key.value for key in modifiers]
        Keystroke.key_sender.PushKeyCombo(keys)
