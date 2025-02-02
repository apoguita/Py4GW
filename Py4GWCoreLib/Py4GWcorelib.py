import traceback
import math
from enum import Enum
import time
from collections import namedtuple

import Py4GW
from Py4GWCoreLib.Skillbar import SkillBar
import PyImGui
import PyMap
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

from .Agent import *
from abc import ABC, abstractmethod
from .Player import Player
from .Map import Map
from .Inventory import Inventory
from .Skill import Skill

import inspect
import threading
import socket
import configparser
import os

class IniHandler:
    def __init__(self, filename: str):
        """
        Initialize the handler with the given INI file.
        """
        self.filename = filename
        self.last_modified = 0
        self.config = configparser.ConfigParser()

    # ----------------------------
    # Core Methods
    # ----------------------------

    def reload(self) -> configparser.ConfigParser:
        """Reload the INI file only if it has changed."""
        current_mtime = os.path.getmtime(self.filename)
        if current_mtime != self.last_modified:
            self.last_modified = current_mtime
            self.config.read(self.filename)
        return self.config

    def save(self, config: configparser.ConfigParser) -> None:
        """
        Save changes to the INI file.
        """
        with open(self.filename, 'w') as configfile:
            config.write(configfile)

    # ----------------------------
    # Read Methods
    # ----------------------------

    def read_key(self, section: str, key: str, default_value: str = "") -> str:
        """
        Read a string value from the INI file.
        """
        config = self.reload()
        try:
            return config.get(section, key)
        except (configparser.NoOptionError, configparser.NoSectionError):
            return default_value

    def read_int(self, section: str, key: str, default_value: int = 0) -> int:
        """
        Read an integer value.
        """
        config = self.reload()
        try:
            return config.getint(section, key)
        except (ValueError, configparser.NoOptionError, configparser.NoSectionError):
            return default_value

    def read_float(self, section: str, key: str, default_value: float = 0.0) -> float:
        """
        Read a float value.
        """
        config = self.reload()
        try:
            return config.getfloat(section, key)
        except (ValueError, configparser.NoOptionError, configparser.NoSectionError):
            return default_value

    def read_bool(self, section: str, key: str, default_value: bool = False) -> bool:
        """
        Read a boolean value.
        """
        config = self.reload()
        try:
            return config.getboolean(section, key)
        except (ValueError, configparser.NoOptionError, configparser.NoSectionError):
            return default_value

    # ----------------------------
    # Write Methods
    # ----------------------------

    def write_key(self, section: str, key: str, value: str) -> None:
        """
        Write or update a key-value pair.
        """
        config = self.reload()
        if not config.has_section(section):
            config.add_section(section)
        config.set(section, key, str(value))
        self.save(config)

    # ----------------------------
    # Delete Methods
    # ----------------------------

    def delete_key(self, section: str, key: str) -> None:
        """
        Delete a specific key.
        """
        config = self.reload()
        if config.has_section(section) and config.has_option(section, key):
            config.remove_option(section, key)
            self.save(config)

    def delete_section(self, section: str) -> None:
        """
        Delete an entire section.
        """
        config = self.reload()
        if config.has_section(section):
            config.remove_section(section)
            self.save(config)


    # ----------------------------
    # Utility Methods
    # ----------------------------

    def list_sections(self) -> list:
        """
        List all sections in the INI file.
        """
        config = self.reload()
        return config.sections()

    def list_keys(self, section: str) -> dict:
        """
        List all keys and values in a section.
        """
        config = self.reload()
        if config.has_section(section):
            return dict(config.items(section))
        return {}

    def has_key(self, section: str, key: str) -> bool:
        """
        Check if a key exists in a section.
        """
        config = self.reload()
        return config.has_section(section) and config.has_option(section, key)

    def clone_section(self, source_section: str, target_section: str) -> None:
        """
        Clone all keys from one section to another.
        """
        config = self.reload()
        if config.has_section(source_section):
            if not config.has_section(target_section):
                config.add_section(target_section)
            for key, value in config.items(source_section):
                config.set(target_section, key, value)
            self.save(config)


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
    
    @staticmethod
    def RGBToNormal(r, g, b, a):
        return r / 255.0, g / 255.0, b / 255.0, a / 255.0
    
    @staticmethod
    def RGBToColor(r, g, b, a):
        return (a << 24) | (b << 16) | (g << 8) | r
    
    @staticmethod
    def DegToRad(degrees):
        return degrees * (math.pi / 180)

    @staticmethod
    def RadToDeg(radians):
        return radians * (180 / math.pi)
    
    @staticmethod
    def TrueFalseColor(condition):
        if condition:
            return Utils.RGBToNormal(0, 255, 0, 255)
        else:
            return Utils.RGBToNormal(255, 0, 0, 255)

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
            # Create adjusted positions as new tuples
            pos_a = (self.probe_position[0] + 1, self.probe_position[1] + 1)
            pos_b = (target_position[0] - 1, target_position[1] - 1)

            distance = Utils.Distance(pos_a, pos_b)
            if distance == 0:
                return (0, 0)  # Avoid division by zero
            return ((pos_b[0] - pos_a[0]) / distance, (pos_b[1] - pos_a[1]) / distance)



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

class Timer:
    def __init__(self):
        """Initialize the Timer object with default values."""
        self.start_time = 0.0
        self.paused_time = 0.0
        self.running = False
        self.paused = False

    def Start(self):
        """Start the timer."""
        self.Stop()
        if not self.running:
            self.start_time = time.perf_counter()  # High-precision time
            self.running = True
            self.paused = False
            self.paused_time = 0.0  # Reset paused time

    def Stop(self):
        """Stop the timer."""
        self.running = False
        self.paused = False
        
    def Reset(self):
        """Reset the timer."""
        self.Start()

    def Pause(self):
        """Pause the timer."""
        if self.running and not self.paused:
            self.paused_time = time.perf_counter() - self.start_time  # Capture elapsed time
            self.paused = True

    def Resume(self):
        """Resume the timer."""
        if self.running and self.paused:
            self.start_time = time.perf_counter() - self.paused_time  # Adjust start time
            self.paused = False

    def IsStopped(self):
        """Check if the timer is stopped."""
        return not self.running

    def IsRunning(self):
        """Check if the timer is running."""
        return self.running and not self.paused

    def IsPaused(self):
        """Check if the timer is paused."""
        return self.paused

    def GetElapsedTime(self):
        """Get the elapsed time in milliseconds."""
        if not self.running:
            return 0
        if self.paused:
            return self.paused_time * 1000  # Convert to milliseconds
        return (time.perf_counter() - self.start_time) * 1000  # Convert to milliseconds

    def HasElapsed(self, milliseconds):
        """Check if the specified time has elapsed."""
        if not self.running or self.paused:
            return False
        return self.GetElapsedTime() >= milliseconds

    def FormatElapsedTime(self, mask="hh:mm:ss:ms"):
        return FormatTime(self.GetElapsedTime(), mask)
    
    def __repr__(self):
        return f"<Timer running={self.is_running()}>"

def FormatTime(time_ms, mask="hh:mm:ss:ms"):
        """Get the formatted elapsed time string based on the mask provided."""
        ms = int(time_ms)
        seconds = ms // 1000
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        milliseconds = ms % 1000  # Directly get remaining milliseconds

        # Apply the mask
        formatted_time = mask
        if "hh" in mask:
            formatted_time = formatted_time.replace("hh", f"{hours:02}")
        if "mm" in mask:
            formatted_time = formatted_time.replace("mm", f"{minutes:02}")
        if "ss" in mask:
            formatted_time = formatted_time.replace("ss", f"{secs:02}")
        if "ms" in mask:
            formatted_time = formatted_time.replace("ms", f"{milliseconds:03}")

        return formatted_time

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
    @staticmethod
    def keystroke_instance():
        """
        Purpose: Get the PyScanCodeKeystroke instance for sending keystrokes.
        Returns: PyScanCodeKeystroke
        """
        return PyKeystroke.PyScanCodeKeystroke()


    @staticmethod
    def Press(key):
        """
        Purpose: Simulate a key press event using scan codes.
        Args:
            key (Key): The key to press.
        Returns: None
        """
        Keystroke.keystroke_instance().PressKey(key)

    @staticmethod
    def Release(key):
        """
        Purpose: Simulate a key release event using scan codes.
        Args:
            key (Key): The key to release.
        Returns: None
        """
        Keystroke.keystroke_instance().ReleaseKey(key)

    @staticmethod
    def PressAndRelease(key):
        """
        Purpose: Simulate a key press and release event using scan codes.
        Args:
            key (Key): The key to press and release.
        Returns: None
        """
        Keystroke.keystroke_instance().PushKey(key)

    @staticmethod
    def PressCombo(modifiers):
        """
        Purpose: Simulate a key press event for multiple keys using scan codes.
        Args:
            modifiers (list of Key): The list of keys to press.
        Returns: None
        """
        keys = [key.value for key in modifiers]
        Keystroke.keystroke_instance().PressKeyCombo(keys)

    @staticmethod
    def ReleaseCombo(modifiers):
        """
        Purpose: Simulate a key release event for multiple keys using scan codes.
        Args:
            modifiers (list of Key): The list of keys to release.
        Returns: None
        """
        keys = [key.value for key in modifiers]
        Keystroke.keystroke_instance().ReleaseKeyCombo(keys)

    @staticmethod
    def PressAndReleaseCombo(modifiers):
        """
        Purpose: Simulate a key press and release event for multiple keys using scan codes.
        Args:
            modifiers (list of Key): The list of keys to press and release.
        Returns: None
        """
        keys = [key.value for key in modifiers]
        Keystroke.keystroke_instance().PushKeyCombo(keys)


arrived_timer = Timer()
class Routines:
    class Checks:
        class Inventory:
            def InventoryAndLockpickCheck():
                return Inventory.GetFreeSlotCount() > 0 and Inventory.GetModelCount(22751) > 0 

        class Skills:
            def HasEnoughEnergy(agent_id, skill_id):
                """
                Purpose: Check if the player has enough energy to use the skill.
                Args:
                    agent_id (int): The agent ID of the player.
                    skill_id (int): The skill ID to check.
                Returns: bool
                """
                player_energy = Agent.GetEnergy(agent_id) * Agent.GetMaxEnergy(agent_id)
                skill_energy = Skill.Data.GetEnergyCost(skill_id)
                return player_energy >= skill_energy

            def HasEnoughLife(agent_id, skill_id):
                """
                Purpose: Check if the player has enough life to use the skill.
                Args:
                    agent_id (int): The agent ID of the player.
                    skill_id (int): The skill ID to check.
                Returns: bool
                """
                player_life = Agent.GetHealth(agent_id)
                skill_life = Skill.Data.GetHealthCost(skill_id)
                return player_life > skill_life

            def HasEnoughAdrenaline(agent_id, skill_id):
                """
                Purpose: Check if the player has enough adrenaline to use the skill.
                Args:
                    agent_id (int): The agent ID of the player.
                    skill_id (int): The skill ID to check.
                Returns: bool
                """
                skill_adrenaline = Skill.Data.GetAdrenaline(skill_id)
                skill_adrenaline_a = Skill.Data.GetAdrenalineA(skill_id)
                if skill_adrenaline == 0:
                    return True

                if skill_adrenaline_a >= skill_adrenaline:
                    return True

                return False

            def DaggerStatusPass(agent_id, skill_id):
                """
                Purpose: Check if the player attack dagger status match tha skill requirement.
                Args:
                    agent_id (int): The agent ID of the player.
                    skill_id (int): The skill ID to check.
                Returns: bool
                """
                dagger_status = Agent.GetDaggerStatus(agent_id)
                skill_combo = Skill.Data.GetCombo(skill_id)

                if skill_combo == 1 and (dagger_status != 0 and dagger_status != 3):
                    return False

                if skill_combo == 2 and dagger_status != 1:
                    return False

                if skill_combo == 3 and dagger_status != 2:
                    return False

                return True

    class Transition:
        def TravelToOutpost(outpost_id, log= True):
            """
            Purpose: Travel to the specified outpost by ID.
            Args:
                outpost_id (int): The ID of the outpost to travel to.
                log (bool) Optional: Whether to log the action. Default is True.
            Returns: None
            """
            global arrived_timer
            if Map.IsMapReady():
                if Map.GetMapID() != outpost_id and arrived_timer.IsStopped():
                    if log:
                        current_function = inspect.currentframe().f_code.co_name
                        Py4GW.Console.Log(f"{current_function}", f"Outpost Check Failed. ({Map.GetMapName(outpost_id)}), Travelling.", Py4GW.Console.MessageType.Info)
                    Map.Travel(outpost_id)
                    arrived_timer.Start()
                    return

                if log and arrived_timer.IsStopped():
                    current_function = inspect.currentframe().f_code.co_name
                    Py4GW.Console.Log(f"{current_function}", f"Outpost Check Passed. ({Map.GetMapName(outpost_id)}).", Py4GW.Console.MessageType.Info)

        @staticmethod
        def HasArrivedToOutpost(outpost_id, log= True):
            """
            Purpose: Check if the player has arrived at the specified outpost after traveling.
            Args:
                outpost_id (int): The ID of the outpost to check.
                log (bool) Optional: Whether to log the action. Default is True.
            Returns: bool
            """
            global arrived_timer

            if Map.GetMapID() == outpost_id and Routines.Transition.IsOutpostLoaded():
                if log:
                    current_function = inspect.currentframe().f_code.co_name
                    Py4GW.Console.Log(f"{current_function}", f"Outpost Arrive Passed. @{Map.GetMapName(outpost_id)}.", Py4GW.Console.MessageType.Info)
                    arrived_timer.Stop()
                    return True
                else:
                    if arrived_timer.HasElapsed(5000):
                        arrived_timer.Stop()
                        if log:
                            current_function = inspect.currentframe().f_code.co_name
                            Py4GW.Console.Log(f"{current_function}", f"Outpost Arrive Timeout. @{Map.GetMapName(outpost_id)}.", Py4GW.Console.MessageType.Info)
                        return False
            
            if log:
                current_function = inspect.currentframe().f_code.co_name
                Py4GW.Console.Log(f"{current_function}", f"Outpost Arrive Failed. @{Map.GetMapName(outpost_id)}. Retrying.", Py4GW.Console.MessageType.Info)
                
            return False

        def IsOutpostLoaded():
            """
            Purpose: Check if the outpost map is loaded.
            Args: None
            Returns: bool
            """
            from .Party import Party
            map_loaded = Map.IsMapReady() and Map.IsOutpost() and Party.IsPartyLoaded()
            if map_loaded:
                Py4GW.Console.Log("IsOutpostLoaded", f"Outpost Map Loaded.", Py4GW.Console.MessageType.Info)
            else:
                Py4GW.Console.Log("IsOutpostLoaded", f"Outpost Map Not Loaded. Retrying.", Py4GW.Console.MessageType.Info)
            
            return map_loaded

        def IsExplorableLoaded(log_actions=False):
            """
            Purpose: Check if the explorable map is loaded.
            Args: None
            Returns: bool
            """
            from .Party import Party
            map_loaded =  Map.IsMapReady() and Map.IsExplorable() and Party.IsPartyLoaded()
            if log_actions:
                if map_loaded:
                    Py4GW.Console.Log("IsExplorableLoaded", f"Explorable Map Loaded.", Py4GW.Console.MessageType.Info)
                else:
                    Py4GW.Console.Log("IsExplorableLoaded", f"Explorable Map Not Loaded. Retrying.", Py4GW.Console.MessageType.Info)
            
            return map_loaded

    class Targeting:

        def TargetMerchant():
            """Target the nearest merchant. within 5000 units"""
            Player.SendChatCommand("target [Merchant]")

        def InteractTarget():
            """Interact with the target"""
            Player.Interact(Player.GetTargetID())
       
        def HasArrivedToTarget():
            """Check if the player has arrived at the target."""
            player_x, player_y = Player.GetXY()
            target_id = Player.GetTargetID()
            target_x, target_y = Agent.GetXY(target_id)
            return Utils.Distance((player_x, player_y), (target_x, target_y)) < 100


        def GetNearestItem(max_distance=5000):
            from .AgentArray import AgentArray
            """
            Purpose: Get the nearest item within the specified range.
            Args:
                range (int): The maximum distance to search for items.
            Returns: Agent ID or None
            """
            item_array = AgentArray.GetItemArray()
            item_array = AgentArray.Filter.ByDistance(item_array, Player.GetXY(), max_distance)
            item_array = AgentArray.Sort.ByDistance(item_array,Player.GetXY())
            if len(item_array) > 0:
                return item_array[0]    

        def GetNearestChest(max_distance=5000):
            from .AgentArray import AgentArray
            """
            Purpose: Get the nearest chest within the specified range.
            Args:
                range (int): The maximum distance to search for chests.
            Returns: Agent ID or None
            """
            gadget_array = AgentArray.GetGadgetArray()
            gadget_array = AgentArray.Filter.ByDistance(gadget_array, Player.GetXY(), max_distance)
            gadget_array = AgentArray.Sort.ByDistance(gadget_array,Player.GetXY())
            for agent_id in gadget_array:
                if Agent.GetGadgetID(agent_id) == 8141: #8141 is the ID for a chest
                    return agent_id

            return 0

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

    class Movement:
        def FollowPath(path_handler,follow_handler, log_actions=False):
            """
            Purpose: Follow a path using the path handler and follow handler objects.
            Args:
                path_handler (PathHandler): The PathHandler object containing the path coordinates.
                follow_handler (FollowXY): The FollowXY object for moving to waypoints.
            Returns: None
            """
            
            follow_handler.update()

            if follow_handler.is_following():
                return


            point = path_handler.advance()
            if point is not None:
                follow_handler.move_to_waypoint(point[0], point[1])
                if log_actions:
                    Py4GW.Console.Log("FollowPath", f"Moving to {point}", Py4GW.Console.MessageType.Info)

        def IsFollowPathFinished(path_handler,follow_handler):
            return path_handler.is_finished() and follow_handler.has_arrived()


        class FollowXY:
            def __init__(self, tolerance=100):
                """
                Initialize the FollowXY object with default values.
                Routine for following a waypoint.
                """
                self.waypoint = (0, 0)
                self.tolerance = tolerance
                self.player_instance = PyPlayer.PyPlayer()
                self.following = False
                self.arrived = False
                self.timer = Timer()  # Timer to track movement start time
                self.wait_timer = Timer()  # Timer to track waiting after issuing move command
                self.wait_timer_run_once = True


            def calculate_distance(self, pos1, pos2):
                """
                Calculate the Euclidean distance between two points.
                """
                return math.sqrt((pos1[0] - pos2[0]) ** 2 + (pos1[1] - pos2[1]) ** 2)

            def move_to_waypoint(self, x, y, tolerance=None):
                """
                Move the player to the specified coordinates.
                Args:
                    x (float): X coordinate of the waypoint.
                    y (float): Y coordinate of the waypoint.
                    tolerance (int, optional): The distance threshold to consider arrival. Defaults to the initialized value.
                """
                self.reset()
                self.waypoint = (x, y)
                self.tolerance = tolerance if tolerance is not None else self.tolerance
                self.following = True
                self.arrived = False
                self.player_instance.Move(x, y)
                self.timer.Start()

            def reset(self):
                """
                Cancel the current move command and reset the waypoint following state.
                """
                self.following = False
                self.arrived = False
                self.timer.Reset()
                self.wait_timer.Reset()

            def update(self, log_actions = False):
                """
                Update the FollowXY object's state, check if the player has reached the waypoint,
                and issue new move commands if necessary.
                """
                if self.following:
                    current_position = Player.GetXY()
                    is_casting = Agent.IsCasting(Player.GetAgentID())
                    is_moving = Agent.IsMoving(Player.GetAgentID())
                    is_knocked_down = Agent.IsKnockedDown(Player.GetAgentID())
                    is_dead = Agent.IsDead(Player.GetAgentID())

                    if is_casting or is_moving or is_knocked_down or is_dead:
                        return 

                     # Check if the wait timer has elapsed and re-enable movement checks
                    if self.wait_timer.HasElapsed(1000):
                        self.wait_timer.Reset()
                        self.wait_timer_run_once = True

                    # Check if the player has arrived at the waypoint
                    if self.calculate_distance(current_position, self.waypoint) <= self.tolerance:
                        self.arrived = True
                        self.following = False
                        return

                    # Re-issue the move command if the player is not moving and not casting
                    if self.wait_timer_run_once:
                        # Use the move_to_waypoint function to reissue movement
                        Player.Move(0,0) #reset movement pointer?
                        Player.Move(self.waypoint[0], self.waypoint[1])
                        self.wait_timer_run_once  = False  # Disable immediate re-issue
                        self.wait_timer.Start()  # Start the wait timer to prevent spamming movement
                        if log_actions:
                            Py4GW.Console.Log("FollowXY", f"Stopped, R eissue move", Py4GW.Console.MessageType.Info)

                    

            def get_time_elapsed(self):
                """
                Get the elapsed time since the player started moving.
                """
                return self.timer.GetElapsedTime()

            def get_distance_to_waypoint(self):
                """
                Get the distance between the player and the current waypoint.
                """
                current_position = Player.GetXY()
                return Utils.Distance(current_position, self.waypoint)

            def is_following(self):
                """
                Check if the player is currently following a waypoint.
                """
                return self.following

            def has_arrived(self):
                """
                Check if the player has arrived at the current waypoint.
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
                self.reverse = False  # By default, move forward
                self.finished = False

            def get_current_point(self):
                """
                Purpose: Get the current point in the list of coordinates.
                Args: None
                Returns: tuple or None
                """
                if not self.coordinates or self.finished:
                    return None
                return self.coordinates[self.index]

            def advance(self):
                """
                Purpose: Advance the pointer in the list based on the current direction (forward or reverse).
                Args: None
                Returns: tuple or None (next point or None if finished)
                """
                if self.finished:
                    return None

                current_point = self.get_current_point()

                # Move forward or backward based on the direction
                if self.reverse:
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

            def toggle_direction(self):
                """
                Purpose: Manually reverse the current direction of traversal.
                Args: None
                Returns: None
                """
                self.reverse = not self.reverse

            def reset(self):
                """
                Purpose: Reset the path traversal to the start or end depending on direction.
                Args: None
                Returns: None
                """
                self.index = 0 if not self.reverse else len(self.coordinates) - 1
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

            def get_position_count(self):
                """
                Purpose: Get the total number of positions in the list.
                Args: None
                Returns: int
                """
                return len(self.coordinates)
    

class BehaviorTree:
    class NodeState(Enum):
        RUNNING = 0
        SUCCESS = 1
        FAILURE = 2

    class Node(ABC):
        def __init__(self):
            self.state = BehaviorTree.NodeState.RUNNING  # Default state

        @abstractmethod
        def tick(self):
            """This method should be implemented in subclasses to define behavior."""
            pass

        def run(self):
            """Executes the tick method and returns the node's current state."""
            self.state = self.tick()  # Calls the tick method
            return self.state

        def reset(self):
            """Resets the node's state to allow restarting the behavior tree."""
            self.state = BehaviorTree.NodeState.RUNNING

    class ActionNode(Node):
        def __init__(self, action):
            super().__init__()
            self.action = action  # The action function this node will execute

        def tick(self):
            """Executes the action and returns the result."""
            return self.action()  # Call the action function


    class ConditionNode(Node):
        def __init__(self, condition):
            super().__init__()
            self.condition = condition  # The condition function this node will evaluate

        def tick(self):
            """Checks the condition and returns the result."""
            if self.condition():  # Evaluate the condition function
                return BehaviorTree.NodeState.SUCCESS
            else:
                return BehaviorTree.NodeState.FAILURE

    class CompositeNode(Node):
        def __init__(self, children=None):
            super().__init__()
            self.children = children if children else []  # A list of child nodes

        def add_child(self, child):
            """Adds a child node to the composite node."""
            self.children.append(child)

        def reset(self):
            """Reset all child nodes' states."""
            for child in self.children:
                child.reset()
            super().reset()

    # Sequence Node - executes children in sequence
    class SequenceNode(CompositeNode):
        def tick(self):
            """Executes children in sequence."""
            for child in self.children:
                result = child.run()  # Run each child node
            
                if result == BehaviorTree.NodeState.FAILURE:
                    return BehaviorTree.NodeState.FAILURE  # Stop if any child fails
            
                if result == BehaviorTree.NodeState.RUNNING:
                    return BehaviorTree.NodeState.RUNNING  # If a child is still running, keep running
            
            return BehaviorTree.NodeState.SUCCESS  # Only return success if all children succeed


    # Selector Node - executes children in order, returns success if any succeed
    class SelectorNode(CompositeNode):
        def tick(self):
            """Executes children in order, returns success if any succeed."""
            for child in self.children:
                result = child.run()  # Run each child node
            
                if result == BehaviorTree.NodeState.SUCCESS:
                    return BehaviorTree.NodeState.SUCCESS  # Stop if any child succeeds
            
                if result == BehaviorTree.NodeState.RUNNING:
                    return BehaviorTree.NodeState.RUNNING  # If a child is still running, keep running

            return BehaviorTree.NodeState.FAILURE  # Only return failure if all children fail


    # Parallel Node - runs all children in parallel, succeeds or fails based on thresholds
    class ParallelNode(CompositeNode):
        def __init__(self, success_threshold=1, failure_threshold=1, children=None):
            super().__init__(children)
            self.success_threshold = success_threshold  # Number of successes needed for SUCCESS
            self.failure_threshold = failure_threshold  # Number of failures needed for FAILURE

        def tick(self):
            """Executes all children in parallel."""
            success_count = 0
            failure_count = 0

            for child in self.children:
                result = child.run()  # Run each child node

                if result == BehaviorTree.NodeState.SUCCESS:
                    success_count += 1
                elif result == BehaviorTree.NodeState.FAILURE:
                    failure_count += 1

                # Check if the success or failure threshold is reached
                if success_count >= self.success_threshold:
                    return BehaviorTree.NodeState.SUCCESS
                if failure_count >= self.failure_threshold:
                    return BehaviorTree.NodeState.FAILURE

            return BehaviorTree.NodeState.RUNNING  # If thresholds are not met, it's still running


    # Inverter Node - inverts the result of its child node
    class InverterNode(Node):
        def __init__(self, child):
            super().__init__()
            self.child = child  # The node to invert

        def tick(self):
            """Inverts the result of the child node."""
            result = self.child.run()  # Run the child node
        
            if result == BehaviorTree.NodeState.SUCCESS:
                return BehaviorTree.NodeState.FAILURE  # Invert SUCCESS to FAILURE
            elif result == BehaviorTree.NodeState.FAILURE:
                return BehaviorTree.NodeState.SUCCESS  # Invert FAILURE to SUCCESS
            else:
                return BehaviorTree.NodeState.RUNNING  # RUNNING remains unchanged

    # Succeeder Node - always returns success, regardless of child result
    class SucceederNode(Node):
        def __init__(self, child):
            super().__init__()
            self.child = child  # The node whose result will be modified

        def tick(self):
            """Succeeder always returns SUCCESS."""
            self.child.run()  # Run the child, but ignore its result
            return BehaviorTree.NodeState.SUCCESS  # Always return SUCCESS

    class RepeaterNode(Node):
        def __init__(self, child, repeat_interval=1000, repeat_limit=-1):
            """
            Initialize the RepeaterNode with an optional repeat limit.

            :param child: The child node to repeat.
            :param repeat_interval: Time in milliseconds between repetitions (cooldown period).
            :param repeat_limit: Maximum number of times to repeat (-1 for unlimited).
            """
            super().__init__()
            self.child = child  # The child node to repeat
            self.repeat_interval = repeat_interval  # Time in milliseconds between repetitions
            self.repeat_limit = repeat_limit  # Maximum number of repetitions (-1 for unlimited)
            self.current_repeats = 0  # Counter to track the number of repetitions
            self.timer = Timer()  # Instance of Timer class
            self.timer.Start()  # Start the timer immediately
            self.repetition_allowed = False  # Whether the child can be run again

        def tick(self):
            """Run the child node if the cooldown has passed and repeat limit is not reached."""
            # Check if the repeat limit has been reached
            if self.repeat_limit != -1 and self.current_repeats >= self.repeat_limit:
                return BehaviorTree.NodeState.SUCCESS  # Stop after reaching the repeat limit

            # If the repetition is allowed, run the child node
            if self.repetition_allowed:
                result = self.child.run()  # Run the child node

                if result in [BehaviorTree.NodeState.SUCCESS, BehaviorTree.NodeState.FAILURE]:
                    # After the child finishes, start the cooldown timer
                    self.timer.Start()
                    self.repetition_allowed = False  # Prevent running until the cooldown ends
                    self.current_repeats += 1  # Increment the repeat counter

                return result

            # Check if the cooldown has elapsed
            if self.timer.HasElapsed(self.repeat_interval):
                self.repetition_allowed = True  # Allow the next repetition
                self.timer.Stop()  # Reset the timer

            return BehaviorTree.NodeState.RUNNING  # Keep the node in the running state during cooldown

        def reset(self):
            """Reset the repeater node and the child state."""
            self.current_repeats = 0  # Reset the repeat count
            self.repetition_allowed = False  # Disallow immediate repetition
            self.timer.Start()  # Restart the timer
            self.child.reset()  # Reset the child node
            super().reset()  # Reset the node state

    class CreateBehaviorTree(SequenceNode):
        def __init__(self, nodes=None):
            # Initialize the behavior tree with a list of nodes (can be Sequence, Selector, etc.)
            super().__init__(nodes)

class FSM:

    def __init__(self, name, log_actions=False):
        """
        Initialize the FSM with a name and track its states and transitions.
        :param name: The name of the FSM (for logging and identification purposes).
        """
        self.name = name  # Store the FSM name
        self.states = []  # List to store all states in order
        self.current_state = None  # Track the current state
        self.state_counter = 0  # Internal counter for state IDs
        self.log_actions = log_actions  # Whether to log state transitions and actions
        self.finished = False  # Track whether the FSM has completed all states


    class State:
        def __init__(self, id, name=None, execute_fn=None, exit_condition=None, transition_delay_ms=0, run_once=True):
            """
            :param id: Internal ID of the state.
            :param name: Optional name of the state (for debugging purposes).
            :param execute_fn: A function representing the block of code to be executed in this state.
            :param exit_condition: A function that returns True/False to determine if it can transition to the next state.
            :param run_once: Whether the execution function should run only once (default: True).
            :param transition_delay_ms: Delay in milliseconds before checking the exit condition (default: 0).
            """
            self.id = id
            self.name = name or f"State-{id}"  # If no name is provided, use "State-ID"
            self.execute_fn = execute_fn or (lambda: None)  # Default to no action if not provided
            self.exit_condition = exit_condition or (lambda: True)  # Default to False if not provided
            self.run_once = run_once  # Flag to control whether the action runs once or repeatedly
            self.executed = False  # Track whether the state's execute function has been run
            self.transition_delay_ms = transition_delay_ms  # Delay before transitioning to the next state
            self.transition_timer = Timer()  # Timer to manage the delay

        def execute(self):
            """Run the state's block of code. If `run_once` is True, run it only once."""
            if not self.run_once or not self.executed:
                self.execute_fn()
                self.executed = True  # Mark execution as complete if run_once is True
                self.transition_timer.Reset()  # Reset the timer

        def can_exit(self):
            """
            Check if the exit condition is met and if the transition delay has passed.
            """
            if self.transition_timer.HasElapsed(self.transition_delay_ms):
                if self.exit_condition():
                    # If the exit condition is true and the delay has passed, return True
                    return True
                else:
                    # Reset the timer if the exit condition is not yet met
                    self.transition_timer.Reset()
            return False

        def reset(self):
            """Reset the state so it can be re-entered, if needed."""
            self.executed = False
            self.transition_timer.Stop()  # Reset timer when resetting the state

        def set_next_state(self, next_state):
            """Set the next state for transitions."""
            self.next_state = next_state

    class ConditionState(State):
        def __init__(self, id, name=None, condition_fn=None, sub_fsm=None):
            """
            A state that evaluates a condition and decides whether to continue or run a sub-FSM.

            :param condition_fn: Function that returns True/False. If True,
                                 it runs the sub_fsm and waits for it to finish before transitioning.
            :param sub_fsm: An optional sub-FSM that will be run if condition_fn returns False.
            """
            super().__init__(id, name)
            self.condition_fn = condition_fn or (lambda: True)  # Default to True if no condition provided
            self.sub_fsm = sub_fsm
            self.sub_fsm_active = False

        def execute(self):
            """
            Execute the condition function. If it returns False, mark the state as completed.
            If it returns True, start the subroutine FSM (if provided).
            """
            if self.sub_fsm_active:
                # If the sub-FSM is running, update it and check if it is finished
                if not self.sub_fsm.is_finished():
                    self.sub_fsm.update()
                else:
                    self.sub_fsm_active = False  # Sub-FSM finished, can continue execution
                    self.executed = True
            else:
                # Evaluate the condition
                if not self.condition_fn():
                    self.executed = True  # Condition not met, continue to the next state
                elif self.sub_fsm:
                    # Condition met, start the sub-FSM
                    Py4GW.Console.Log("FSM", f"Starting FSM Subroutine", Py4GW.Console.MessageType.Success)

                    self.sub_fsm.reset()
                    self.sub_fsm.start()
                    self.sub_fsm_active = True

        def can_exit(self):
            """
            The node can exit only if the condition is met or the sub-FSM has finished running.
            """
            return self.executed and not self.sub_fsm_active

    def SetLogBehavior(self, log_actions=False):
        """
        Set whether to log state transitions and actions.
        :param log_actions: Whether to log state transitions and actions (default: False).
        """
        self.log_actions = log_actions

    def GetLogBehavior(self):
        """Get the current logging behavior setting."""
        return self.log_actions

    def AddState(self, name=None, execute_fn=None, exit_condition=None, transition_delay_ms=0, run_once=True):
        """Add a state with an optional name, execution function, and exit condition."""
        state = FSM.State(
            id=self.state_counter,
            name=name,
            execute_fn=execute_fn,
            exit_condition=exit_condition,
            run_once=run_once,
            transition_delay_ms=transition_delay_ms
        )
        
        if self.states:
            self.states[-1].set_next_state(state)
        
        self.states.append(state)
        self.state_counter += 1


    def AddSubroutine(self, name=None, condition_fn=None, sub_fsm=None):
        """Add a condition node that evaluates a condition and can run a subroutine FSM."""
        condition_node = FSM.ConditionState(
            id=self.state_counter,
            name=name,
            condition_fn=condition_fn,
            sub_fsm=sub_fsm
        )
        if self.states:
            self.states[-1].set_next_state(condition_node)
        self.states.append(condition_node)
        self.state_counter += 1

    def start(self):
        """Start the FSM by setting the initial state."""
        if not self.states:
            raise ValueError(f"{self.name}: No states have been added to the FSM.")
        self.current_state = self.states[0]
        self.finished = False
        Py4GW.Console.Log("FSM", f"{self.name}: Starting FSM with initial state: {self.current_state.name}", Py4GW.Console.MessageType.Success)

    def stop(self):
        """Stop the FSM and mark it as finished."""
        self.current_state = None
        self.finished = True

        if self.log_actions:
            Py4GW.Console.Log("FSM", f"{self.name}: FSM has been stopped by user.", Py4GW.Console.MessageType.Info)

    def reset(self):
        """Reset the FSM to the initial state without starting it."""
        if not self.states:
            raise ValueError(f"{self.name}: No states have been added to the FSM.")
        self.current_state = self.states[0]  # Reset to the first state
        self.finished = False
        for state in self.states:
            state.reset()  # Reset all states

        if self.log_actions:
            Py4GW.Console.Log("FSM", f"{self.name}: FSM has been reset.", Py4GW.Console.MessageType.Info)


    def update(self):
        """Update the FSM: execute the current state and transition if the exit condition is met."""
        if self.current_state is None:
            # FSM has either not started or already finished
            Py4GW.Console.Log("FSM", f"{self.name}: FSM has not been started or has finished.", Py4GW.Console.MessageType.Warning)
            return

        # Execute the current state's logic (runs once or repeatedly based on the run_once flag)
        if self.log_actions:
            Py4GW.Console.Log("FSM", f"{self.name}: Executing state: {self.current_state.name}", Py4GW.Console.MessageType.Info)
        
        self.current_state.execute()

        # Check if the current state's exit condition is met
        if self.current_state.can_exit():
            if hasattr(self.current_state, 'next_state') and self.current_state.next_state is not None:
                # Transition to the next state
                if self.log_actions:
                    Py4GW.Console.Log("FSM", f"{self.name}: Transitioning from state: {self.current_state.name} to state: {self.current_state.next_state.name}", Py4GW.Console.MessageType.Info)
                self.current_state = self.current_state.next_state
                self.current_state.reset()  # Reset the next state for execution
            else:
                if self.log_actions:
                    Py4GW.Console.Log("FSM", f"{self.name}: Reached the final state: {self.current_state.name}. FSM has completed.", Py4GW.Console.MessageType.Success)
                self.current_state = None  # End of the state machine
                self.finished = True  # Set the FSM to finished
        else:
            if self.log_actions:
                Py4GW.Console.Log("FSM", f"{self.name}: Remaining in state: {self.current_state.name}", Py4GW.Console.MessageType.Info)

    def is_started(self):
        """Check whether the FSM has been started."""
        return self.current_state is not None and not self.finished
                
    def is_finished(self):
        """Check whether the FSM has finished executing all states."""
        return self.finished

    def jump_to_state(self, state_id):
        """Jump to a specific state by its ID."""
        if state_id < 0 or state_id >= len(self.states):
            raise ValueError(f"Invalid state ID: {state_id}")
        self.current_state = self.states[state_id]
        if self.log_actions:
            Py4GW.Console.Log("FSM", f"{self.name}: Jumped to state: {self.current_state.name}", Py4GW.Console.MessageType.Info)
        self.current_state.reset()  # Reset the state upon jumping to it

    def jump_to_state_by_name(self, state_name):
        """Jump to a specific state by its name."""
        for state in self.states:
            if state.name == state_name:
                self.current_state = state
                if self.log_actions:
                    Py4GW.Console.Log("FSM", f"{self.name}: Jumped to state: {self.current_state.name}", Py4GW.Console.MessageType.Info)
                self.current_state.reset()  # Reset the state upon jumping to it
                return
        raise ValueError(f"State with name '{state_name}' not found.")

    def get_current_state_number(self):
        """Get the current state number (index) in the FSM."""
        if self.current_state is None:
            return 0
        return self.states.index(self.current_state) + 1

    def get_state_count (self):
        """Get the total number of states in the FSM."""
        return len(self.states)

    def get_state_number_by_name(self, state_name):
        """Get the step number (index) by the state name."""
        for idx, state in enumerate(self.states):
            if state.name == state_name:
                return idx + 1
        return 0
    
    def get_current_step_name(self):
        """Get the name of the current step (state) in the FSM."""
        if self.current_state is None:
            return f"{self.name}: FSM not started or finished"
        return self.current_state.name


    def get_next_step_name(self):
        """Get the name of the next step (state) in the FSM."""
        if self.current_state is None:
            return f"{self.name}: FSM not started or finished"
        if hasattr(self.current_state, 'next_state') and self.current_state.next_state:
            return self.current_state.next_state.name
        return f"{self.name}: No next state (final state reached)"

    def get_previous_step_name(self):
        """Get the name of the previous step (state) in the FSM."""
        if self.current_state is None:
            return f"{self.name}: FSM not started or finished"
        current_index = self.states.index(self.current_state)
        if current_index > 0:
            return self.states[current_index - 1].name
        return f"{self.name}: No previous state (first state)"


class MultiThreading:
    def __init__(self):
        """Initialize the thread manager."""
        self.threads = {}
        self.lock = threading.Lock()

    def add_thread(self, name, execute_fn, *args, **kwargs):
        """
        Add a new thread to the manager.

        :param name: Unique name for the thread.
        :param execute_fn: Function to execute in the thread.
        :param args: Positional arguments for the target function.
        :param kwargs: Keyword arguments for the target function.
        """
        target =execute_fn
        with self.lock:
            if name in self.threads:
                Py4GW.Console.Log("MultiThreading", f"Thread '{name}' already exists.", Py4GW.Console.MessageType.Warning)
                return
            stop_event = threading.Event()

            def wrapped_target(*args, **kwargs):
                while not stop_event.is_set():
                    target(*args, **kwargs)

            thread = threading.Thread(target=wrapped_target, args=args, kwargs=kwargs, daemon=True)
            self.threads[name] = {"thread": thread, "stop_event": stop_event}
            Py4GW.Console.Log("MultiThreading", f"Thread '{name}' added.", Py4GW.Console.MessageType.Info)

    def start_thread(self, name):
        """Start the thread with the specified name."""
        with self.lock:
            if name not in self.threads:
                Py4GW.Console.Log("MultiThreading", f"Thread '{name}' does not exist.", Py4GW.Console.MessageType.Error)
                return
            thread_info = self.threads[name]
            thread = thread_info["thread"]
            if thread.is_alive():
                Py4GW.Console.Log("MultiThreading", f"Thread '{name}' is already running.", Py4GW.Console.MessageType.Warning)
                return
            thread.start()
            Py4GW.Console.Log("MultiThreading", f"Thread '{name}' started.", Py4GW.Console.MessageType.Success)

    def stop_thread(self, name):
        """Stop the thread with the specified name."""
        with self.lock:
            if name not in self.threads:
                Py4GW.Console.Log("MultiThreading", f"Thread '{name}' does not exist.", Py4GW.Console.MessageType.Error)
                return
            thread_info = self.threads[name]
            stop_event = thread_info["stop_event"]
            stop_event.set()
            thread = thread_info["thread"]
            thread.join(timeout=2)
            if thread.is_alive():
                Py4GW.Console.Log("MultiThreading", f"Failed to stop thread '{name}' gracefully.", Py4GW.Console.MessageType.Warning)
            else:
                Py4GW.Console.Log("MultiThreading", f"Thread '{name}' stopped.", Py4GW.Console.MessageType.Info)
            del self.threads[name]

    def stop_all_threads(self):
        """Stop all threads managed by this manager."""
        thread_names = []
        with self.lock:
            # Make a copy of thread names to avoid modifying the dictionary while iterating
            thread_names = list(self.threads.keys())

        # Stop threads without holding the lock
        for name in thread_names:
            self.stop_thread(name)

