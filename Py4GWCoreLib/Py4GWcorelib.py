import traceback
import math
from enum import Enum
import time
from time import sleep
from collections import namedtuple, deque
from typing import Optional
import ctypes

import Py4GW
import PyAgent
import PyKeystroke

from .Agent import *
from abc import ABC, abstractmethod
from .enums import *


import threading
import socket
import configparser
import os
from datetime import datetime, timezone

#region IniHandler
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
        """Reload the INI file only if it has changed.
        
        If the file doesn't exist, create an empty file.
        """
        if not os.path.exists(self.filename):
            # Create an empty file if it doesn't exist.
            with open(self.filename, 'w') as f:
                f.write("")
            # Update last_modified since a new file was created.
            self.last_modified = os.path.getmtime(self.filename)
            return self.config

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

#endregion

@staticmethod
def ConsoleLog(sender, message, message_type:int=0 , log: bool = True):
    """Logs a message with an optional message type."""
    if log:
        if message_type == 0:
            Py4GW.Console.Log(sender, message, Py4GW.Console.MessageType.Info)
        elif message_type == 1:
            Py4GW.Console.Log(sender, message, Py4GW.Console.MessageType.Warning)
        elif message_type == 2:
            Py4GW.Console.Log(sender, message, Py4GW.Console.MessageType.Error)
        elif message_type == 3:
            Py4GW.Console.Log(sender, message, Py4GW.Console.MessageType.Debug)
        elif message_type == 4:
            Py4GW.Console.Log(sender, message, Py4GW.Console.MessageType.Success)
        elif message_type == 5:
            Py4GW.Console.Log(sender, message, Py4GW.Console.MessageType.Performance)
        elif message_type == 6:
            Py4GW.Console.Log(sender, message, Py4GW.Console.MessageType.Notice)
        else:
            Py4GW.Console.Log(sender, message, Py4GW.Console.MessageType.Info)


#region Utils
# Utils
class Utils:
    from typing import Tuple
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
        """return a normalized RGBA tuple from 0-255 values"""
        return r / 255.0, g / 255.0, b / 255.0, a / 255.0
    
    @staticmethod
    def NormalToColor(color: Tuple[float, float, float, float]) -> "Color":
        """Convert a normalized RGBA float tuple (0.0–1.0) to 0–255 integer values."""
        r = int(color[0] * 255)
        g = int(color[1] * 255)
        b = int(color[2] * 255)
        a = int(color[3] * 255)
        return Color(r, g, b, a)

    
    @staticmethod
    def RGBToDXColor(r, g, b, a) -> int:
        return (a << 24) | (r << 16) | (g << 8) | b
    
    @staticmethod
    def RGBToColor(r, g, b, a) -> int:
        return (a << 24) | (b << 16) | (g << 8) | r
    
    @staticmethod
    def ColorToTuple(color: int) -> Tuple[float, float, float, float]:
        """Convert a 32-bit integer color (ABGR) to a normalized (0.0 - 1.0) RGBA tuple."""
        a = (color >> 24) & 0xFF  # Extract Alpha (highest 8 bits)
        b = (color >> 16) & 0xFF  # Extract Blue  (next 8 bits)
        g = (color >> 8) & 0xFF   # Extract Green (next 8 bits)
        r = color & 0xFF          # Extract Red   (lowest 8 bits)
        return r / 255.0, g / 255.0, b / 255.0, a / 255.0  # Convert to RGBA float

    @staticmethod
    def TupleToColor(color_tuple: Tuple[float, float, float, float]) -> int:
        """Convert a normalized (0.0 - 1.0) RGBA tuple back to a 32-bit integer color (ABGR)."""
        r = int(color_tuple[0] * 255)  # Convert R back to 0-255
        g = int(color_tuple[1] * 255)  # Convert G back to 0-255
        b = int(color_tuple[2] * 255)  # Convert B back to 0-255
        a = int(color_tuple[3] * 255)  # Convert A back to 0-255
        return Utils.RGBToColor(r, g, b, a)  # Encode back as ABGR
    
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
        
    @staticmethod
    def GetFirstFromArray(array):
        if array is None:
            return 0
        
        if len(array) > 0:
            return array[0]
        return 0
    
    @staticmethod
    def GwinchToPixels(gwinch_value: float, zoom_offset=0.0) -> float:
        from .Map import Map

        gwinches = 96.0  # hardcoded GW unit scale
        zoom = Map.MissionMap.GetZoom() + zoom_offset
        scale_x, _ = Map.MissionMap.GetScale()

        pixels_per_gwinch = (scale_x * zoom) / gwinches
        return gwinch_value * pixels_per_gwinch

        
    @staticmethod
    def PixelsToGwinch(pixel_value: float, zoom_offset=0.0) -> float:
        from .Map import Map

        gwinches = 96.0
        zoom = Map.MissionMap.GetZoom() + zoom_offset
        scale_x, _ = Map.MissionMap.GetScale()

        pixels_per_gwinch = (scale_x * zoom) / gwinches
        return pixel_value / pixels_per_gwinch

    @staticmethod
    def SafeInt(value, fallback=0):
        try:
            if not math.isfinite(value):
                return fallback
            return int(value)
        except (ValueError, TypeError, OverflowError):
            return fallback
        
    @staticmethod
    def SafeFloat(value, fallback=0.0):
        try:
            if not math.isfinite(value):
                return fallback
            return float(value)
        except (ValueError, TypeError, OverflowError):
            return fallback

    @staticmethod
    def GetBaseTimestamp():
        SHMEM_ZERO_EPOCH = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0).timestamp()
        return int((time.time() - SHMEM_ZERO_EPOCH) * 1000)

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

#endregion
#region Color
class Color:
    def __init__(self, r: int = 255, g: int = 255, b: int = 255, a: int = 255):
        self.name: str = "Color"
        self.r: int = r
        self.g: int = g
        self.b: int = b
        self.a: int = a
        
    def set_r(self, r: int) -> None:
        self.r = r
    
    def set_g(self, g: int) -> None:
        self.g = g
        
    def set_b(self, b: int) -> None:
        self.b = b
        
    def set_a(self, a: int) -> None:
        self.a = a
        
    def set_rgba(self, r: int, g: int, b: int, a: int) -> None:
        self.r = r
        self.g = g
        self.b = b
        self.a = a

    def get_r (self) -> int:
        return self.r
    
    def get_g (self) -> int:
        return self.g
    
    def get_b (self) -> int:
        return self.b
    
    def get_a (self) -> int: 
        return self.a
    
    def get_rgba (self) -> tuple:
        return (self.r, self.g, self.b, self.a)


    def to_color(self) -> int:
        return Utils.RGBToColor(self.r, self.g, self.b, self.a)
    
    def to_dx_color(self) -> int:
        return Utils.RGBToDXColor(self.r, self.g, self.b, self.a)
    
    def to_tuple(self) -> tuple:
        return (self.r, self.g, self.b, self.a)
    
    def to_tuple_normalized(self) -> tuple:
        return (self.r / 255, self.g / 255, self.b / 255, self.a / 255)

    def __repr__(self) -> str:
        return f"{self.name} (RGBA: {self.r}, {self.g}, {self.b}, {self.a})"
    
    def desaturate(self, amount: float = 1.0) -> "Color":
        """
        Returns a new Color instance, desaturated toward gray by the given amount [0..1].
        0.0 = no change, 1.0 = fully grayscale.
        """
        amount = max(0.0, min(amount, 1.0))  # Clamp between 0 and 1
        gray = int(0.4 * self.r + 0.4 * self.g + 0.4 * self.b)

        new_r = int(self.r * (1 - amount) + gray * amount)
        new_g = int(self.g * (1 - amount) + gray * amount)
        new_b = int(self.b * (1 - amount) + gray * amount)

        return Color(r=new_r, g=new_g, b=new_b, a=self.a)
    
    def shift(self, target: "Color", amount: float) -> "Color":
        """
        Returns a new Color instance shifted toward the target Color by the given amount [0..1].
        0.0 = no change, 1.0 = fully target color.
        """
        amount = max(0.0, min(amount, 1.0))  # Clamp between 0 and 1

        new_r = int(self.r + (target.r - self.r) * amount)
        new_g = int(self.g + (target.g - self.g) * amount)
        new_b = int(self.b + (target.b - self.b) * amount)
        new_a = int(self.a + (target.a - self.a) * amount)

        return Color(new_r, new_g, new_b, new_a)



#endregion
#region Timer
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
        return f"<Timer running={self.IsRunning()}>"

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
#endregion
#region ThrottledTimer

class ThrottledTimer:
    def __init__(self, throttle_time=1000):
        self.throttle_time = throttle_time
        self.timer = Timer()
        self.timer.Start()
        
    def IsExpired(self):
        return self.timer.HasElapsed(self.throttle_time)
    
    def Reset(self):
        self.timer.Reset()
        
    def Start(self):
        self.timer.Start()
        
    def Stop(self):
        self.timer.Stop()
    
    def IsStopped(self):
        return self.timer.IsStopped()
    
    
    def SetThrottleTime(self, throttle_time):
        self.throttle_time = throttle_time
        
    def GetTimeElapsed(self):
        return self.timer.GetElapsedTime()
    
    def GetTimeRemaining(self):
        if self.timer.IsStopped():
            return 0
        return max(0, self.throttle_time - self.timer.GetElapsedTime())

#endregion
#region KeyHandler

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
    def PressCombo(modifiers: list[int]):
        """
        Purpose: Simulate a key press event for multiple keys using scan codes.
        Args:
            modifiers (list of Key): The list of keys to press.
        Returns: None
        """
        Keystroke.keystroke_instance().PressKeyCombo(modifiers)

    @staticmethod
    def ReleaseCombo(modifiers: list[int]):
        """
        Purpose: Simulate a key release event for multiple keys using scan codes.
        Args:
            modifiers (list of Key): The list of keys to release.
        Returns: None
        """
        Keystroke.keystroke_instance().ReleaseKeyCombo(modifiers)

    @staticmethod
    def PressAndReleaseCombo(modifiers: list[int]):
        """
        Purpose: Simulate a key press and release event for multiple keys using scan codes.
        Args:
            modifiers (list of Key): The list of keys to press and release.
        Returns: None
        """
        Keystroke.keystroke_instance().PushKeyCombo(modifiers)

#endregion

    
#region ActionQueue

class ActionQueue:
    def __init__(self):
        """Initialize the action queue."""
        self.queue = deque() # Use deque for efficient FIFO operations
        self.history = deque(maxlen=100)  # Store recent action history with a cap
        self._step_ids = deque()          # Step ID queue (internal use)
        self._step_counter = 0            # Unique step ID tracker
        self._last_step_id = None         # Last executed step ID


    def add_action(self, action, *args, **kwargs):
        """
        Add an action to the queue.

        :param action: Function to execute.
        :param args: Positional arguments for the function.
        :param kwargs: Keyword arguments for the function.
        """
        self.queue.append((action, args, kwargs))
        self._step_ids.append(self._step_counter)  # Track step ID
        self._step_counter += 1
        
    def execute_next(self):
        if self.queue:
            action, args, kwargs = self.queue.popleft()
            self._last_step_id = self._step_ids.popleft()  # Extract step ID
            action(*args, **kwargs)
            self.history.append((datetime.now(), action, args, kwargs))
            return True
        return False

    def get_last_step_id(self):
        """Return the step ID of the last executed action"""
        return self._last_step_id

    def get_next_step_id(self):
        """Peek the step ID of the next action (non-invasive)"""
        return self._step_ids[0] if self._step_ids else None
            
    def is_empty(self):
        """Check if the action queue is empty."""
        return not bool(self.queue)
    
    def clear(self):
        """Clear all actions from the queue."""
        self.queue.clear()
        self._step_ids.clear()
        
    def clear_history(self):
        """Clear the action history."""
        self.history.clear()
        
    def get_next_action_name(self):
        """
        Get the name of the next action function in the queue, or None if empty.
        :return: String with function name or None.
        """
        if self.queue:
            action, args, kwargs = self.queue[0]
            parts = [action.__name__]
            parts.extend(str(arg) for arg in args)
            parts.extend(f"{k}={v}" for k, v in kwargs.items())
            return ','.join(parts)
        return None
    
    def get_all_action_names(self):
        """
        Get a list of all action names with arguments concatenated.
        :return: List of concatenated action strings.
        """
        action_strings = []
        for action, args, kwargs in self.queue:
            parts = [action.__name__]
            parts.extend(str(arg) for arg in args)
            parts.extend(f"{k}={v}" for k, v in kwargs.items())
            action_strings.append(','.join(parts))
        return action_strings
    
    def get_history(self):
        """
        Return the raw history queue: list of (datetime, function, args, kwargs).
        """
        return list(self.history)

    def get_history_names(self):
        formatted = []
        for i, entry in enumerate(self.history):
            if not isinstance(entry, tuple) or len(entry) != 4:
                formatted.append(f"[INVALID ENTRY #{i}]: {repr(entry)}")
                continue
            ts, func, args, kwargs = entry
            try:
                parts = [f"{ts.strftime('%H:%M:%S')} - {func.__name__}"]
                parts.extend(str(arg) for arg in args)
                parts.extend(f"{k}={v}" for k, v in kwargs.items())
                formatted.append(', '.join(parts))
            except Exception as e:
                formatted.append(f"[ERROR formatting entry #{i}]: {e}")
        return formatted


        
class ActionQueueNode:
    def __init__(self,throttle_time=250):
        self.action_queue = ActionQueue()
        self.action_queue_timer = Timer()
        self.action_queue_timer.Start()
        self.action_queue_time = throttle_time
        self._aftercast_delays = deque()
        

    def execute_next(self):
        delay = self._aftercast_delays[0] if self._aftercast_delays else 0
        if self.action_queue_timer.HasElapsed(self.action_queue_time + delay):      
            result = self.action_queue.execute_next()
            self.action_queue_timer.Reset()
            if self._aftercast_delays:
                self._aftercast_delays.popleft()
            return result
        return False
    
    def AftercastDelay(self):
        """Dummy action used to enforce a delay step in the queue."""
        pass
                
    def add_action(self, action, *args, **kwargs):
        self.action_queue.add_action(action, *args, **kwargs)
        self._aftercast_delays.append(0)
        
    def add_action_with_delay(self, delay, action, *args, **kwargs):
        self.action_queue.add_action(action, *args, **kwargs)
        self._aftercast_delays.append(0)  # Real action runs immediately

        self.action_queue.add_action(self.AftercastDelay)
        self._aftercast_delays.append(delay)  # Delay applies to this no-op step
        
    def is_empty(self):
        return self.action_queue.is_empty()
    
    def clear(self):
        self.action_queue.clear()
        self._aftercast_delays.clear()
        
    def clear_history(self):
        self.action_queue.clear_history()
        
    def IsExpired(self):
        delay = self._aftercast_delays[0] if self._aftercast_delays else 0
        return self.action_queue_timer.HasElapsed(self.action_queue_time + delay)
    
    def ProcessQueue(self):
        if self.IsExpired():
            return self.execute_next()
        return False
    
    def GetNextActionName(self):
        return self.action_queue.get_next_action_name()
    
    def GetAllActionNames(self):
        return self.action_queue.get_all_action_names()
    
    def GetHistory(self):
        return self.action_queue.get_history()
    
    def GetHistoryNames(self):
        return self.action_queue.get_history_names()


class QueueTypes(Enum):
    Action = "ACTION"
    Loot = "LOOT"
    Merchant = "MERCHANT"
    Salvage = "SALVAGE"
    Identify = "IDENTIFY"

    @classmethod
    def list(cls):
        return [member.value for member in cls]


class ActionQueueManager:
    _instance = None  # Singleton instance

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ActionQueueManager, cls).__new__(cls)
            cls._instance._initialize_queues()
        return cls._instance

    def _initialize_queues(self):
        self.queues = {
            "ACTION": ActionQueueNode(50),
            "LOOT": ActionQueueNode(1250),
            "MERCHANT": ActionQueueNode(750),
            "SALVAGE": ActionQueueNode(325),
            "IDENTIFY": ActionQueueNode(150)
            # Add more queues here if needed
        }
        
    def AddAction(self, queue_name, action, *args, **kwargs):
        """Add an action to a specific queue by name."""
        if queue_name in self.queues:
            self.queues[queue_name].add_action(action, *args, **kwargs)
        else:
            raise ValueError(f"Queue '{queue_name}' does not exist.")
        
    def AddActionWithDelay(self, queue_name, delay, action, *args, **kwargs):
        """Add an action with a delay to a specific queue by name."""
        if queue_name in self.queues:
            self.queues[queue_name].add_action_with_delay(delay, action, *args, **kwargs)
        else:
            raise ValueError(f"Queue '{queue_name}' does not exist.")

    # Reset specific queue
    def ResetQueue(self, queue_name):
        if queue_name in self.queues:
            self.queues[queue_name].clear()

    # Reset all queues
    def ResetAllQueues(self):
        for queue in self.queues.values():
            queue.clear()

    # Process specific queue
    def ProcessQueue(self, queue_name):
        if queue_name in self.queues:
            return self.queues[queue_name].ProcessQueue()
        return False

    # Process all queues
    def ProcessAll(self):
        for queue in self.queues.values():
            queue.ProcessQueue()

    # Getters (optional if you prefer direct dict access)
    def GetQueue(self, queue_name) -> ActionQueueNode:
        queue = self.queues.get(queue_name)
        if queue is None:
            raise ValueError(f"Queue '{queue_name}' does not exist.")
        return queue
    
    def IsEmpty(self, queue_name) -> bool:
        queue = self.GetQueue(queue_name)
        return queue.is_empty()
    
    def GetNextActionName(self, queue_name) -> str:
        queue = self.GetQueue(queue_name)
        return queue.GetNextActionName() or ""
    
    def GetAllActionNames(self, queue_name) -> list:
        queue = self.GetQueue(queue_name)
        return queue.GetAllActionNames()
    
    def GetHistory(self, queue_name) -> list:
        queue = self.GetQueue(queue_name)
        return queue.GetHistory()
    
    def GetHistoryNames(self, queue_name) -> list:
        queue = self.GetQueue(queue_name)
        return queue.GetHistoryNames()

    def ClearHistory(self, queue_name) -> None:
        queue = self.GetQueue(queue_name)
        queue.clear_history()

           
            
#endregion



#region BehaviorTree
class BehaviorTree:
    class NodeState(Enum):
        RUNNING = 0
        SUCCESS = 1
        FAILURE = 2
 
    class Node(ABC):
        def __init__(self):
            self.state: "BehaviorTree.NodeState" = BehaviorTree.NodeState.RUNNING  # Default state

        @abstractmethod
        def tick(self) -> "BehaviorTree.NodeState":
            """This method should be implemented in subclasses to define behavior."""
            pass

        def run(self) -> "BehaviorTree.NodeState":
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
#endregion

#region FSM

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
        self.paused = False
        self.on_transition = None
        self.on_complete = None

    class State:
        def __init__(self, id, name=None, execute_fn=None, exit_condition=None, transition_delay_ms=0, run_once=True, on_enter=None, on_exit=None):
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
            self.on_enter = on_enter or (lambda: None)
            self.on_exit = on_exit or (lambda: None)
            self.next_state = None
            self.event_transitions = {}

        def enter(self):
            self.on_enter()

        def exit(self):
            self.on_exit()

        def reset_transition_timer(self):
            self.transition_timer.Reset()

        def execute(self):
            """Run the state's block of code. If `run_once` is True, run it only once."""
            if not self.run_once or not self.executed:
                self.execute_fn()
                if not self.executed:  # Only reset timer on first execution
                    self.reset_transition_timer()
                self.executed = True

        def can_exit(self):
            """
            Check if the exit condition is met and if the transition delay has passed.
            """
            if not self.transition_timer.HasElapsed(self.transition_delay_ms):
                return False
            
            return self.exit_condition()
            
        def reset(self):
            """Reset the state so it can be re-entered, if needed."""
            self.executed = False
            self.transition_timer.Stop()  # Reset timer when resetting the state

        def set_next_state(self, next_state):
            """Set the next state for transitions."""
            self.next_state = next_state
        
        def add_event_transition(self, event_name: str, target_state_name: str):
            """
            Define a transition triggered by a specific event.

            :param event_name: The name of the event that triggers this transition.
            :param target_state_name: The name of the state to transition to.
            """
            if not isinstance(event_name, str) or not isinstance(target_state_name, str):
                raise TypeError("Event name and target state name must be strings.")
            self.event_transitions[event_name] = target_state_name
            
    class ConditionState(State):
        def __init__(self, id, name=None, condition_fn=None, sub_fsm=None,
                 on_enter=None, on_exit=None, log_actions=False):
            """
            A state that evaluates a condition and decides whether to continue or run a sub-FSM.

            :param condition_fn: Function that returns True/False. If True,
                                 it runs the sub_fsm and waits for it to finish before transitioning.
            :param sub_fsm: An optional sub-FSM that will be run if condition_fn returns False.
            """
            super().__init__(id, name, on_enter=on_enter, on_exit=on_exit)
            self.condition_fn = condition_fn or (lambda: True)  # Default to True if no condition provided
            self.sub_fsm = sub_fsm
            self.sub_fsm_active = False
            self.log_actions = log_actions

        def execute(self):
            """
            Execute the condition function. If it returns False, mark the state as completed.
            If it returns True, start the subroutine FSM (if provided).
            """
            if self.sub_fsm_active:
                # If the sub-FSM is running, update it and check if it is finished
                if self.sub_fsm and not self.sub_fsm.is_finished():
                    self.sub_fsm.update()
                    return
                self.sub_fsm_active = False  # Sub-FSM finished, can continue execution
                self.executed = True
                self.reset_transition_timer()  # Fix missing timer reset
                return

                # Evaluate the condition
            if not self.condition_fn():
                self.executed = True  # Condition not met, continue to the next state
                self.reset_transition_timer()  # Fix missing timer reset
                return
            
            if self.sub_fsm and not self.sub_fsm_active:
                # Condition met, start the sub-FSM
                if self.log_actions:
                    ConsoleLog("FSM", f"Starting FSM Subroutine", Py4GW.Console.MessageType.Success)
                self.sub_fsm.reset()
                self.sub_fsm.start()
                self.sub_fsm_active = True
            else:
                self.executed = True  # Ensure exit is possible if no sub_fsm
                self.reset_transition_timer()  # Fix missing timer reset
            
        def can_exit(self):
            """
            The node can exit only if the condition is met or the sub-FSM has finished running.
            """
            return self.executed and not self.sub_fsm_active
        
        def reset(self):
            super().reset()
            self.sub_fsm_active = False
            if self.sub_fsm:
                self.sub_fsm.reset()
        
    def SetLogBehavior(self, log_actions=False):
        """
        Set whether to log state transitions and actions.
        :param log_actions: Whether to log state transitions and actions (default: False).
        """
        self.log_actions = log_actions

    def GetLogBehavior(self):
        """Get the current logging behavior setting."""
        return self.log_actions

    def AddState(self, name=None, execute_fn=None, exit_condition=None, transition_delay_ms=0, run_once=True, on_enter=None, on_exit=None):
        """Add a state with an optional name, execution function, and exit condition."""
        state = FSM.State(
            id=self.state_counter,
            name=name,
            execute_fn=execute_fn,
            exit_condition=exit_condition,
            run_once=run_once,
            transition_delay_ms=transition_delay_ms,
            on_enter=on_enter,
            on_exit=on_exit
        )
        
        if self.states:
            self.states[-1].set_next_state(state)
        
        self.states.append(state)
        self.state_counter += 1

    def AddSubroutine(self, name=None, condition_fn=None, sub_fsm=None,
                  on_enter=None, on_exit=None):
        """Add a condition node that evaluates a condition and can run a subroutine FSM."""
        condition_node = FSM.ConditionState(
            id=self.state_counter,
            name=name,
            condition_fn=condition_fn,
            sub_fsm=sub_fsm,
            on_enter=on_enter,
            on_exit=on_exit,
            log_actions=self.log_actions
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

    def get_state_names(self):
        return [s.name for s in self.states]

    def terminate(self):
        if self.log_actions:
            Py4GW.Console.Log("FSM", f"{self.name}: Terminated forcefully.", Py4GW.Console.MessageType.Warning)
        self.current_state = None
        self.finished = True

    def run_until(self, condition_fn):
        while not self.finished and not condition_fn():
            self.update()
    
    def set_completion_callback(self, callback_fn):
        self.on_complete = callback_fn
    
    def get_current_state_index(self):
        if not self.current_state or self.current_state not in self.states:
            return -1
        return self.states.index(self.current_state)

    def get_next_state_index(self):
        if not self.current_state:
            return -1
        next_state = getattr(self.current_state, 'next_state', None)
        if not next_state or next_state not in self.states:
            return -1
        return self.states.index(next_state)

    def interrupt(self, fn):
        if not self.current_state:
            return
        original_exit = self.current_state.exit

        def wrapped_exit():
            original_exit()
            fn()

        self.current_state.exit = wrapped_exit
    
    def pause(self):
        self.paused = True

    def resume(self):
        self.paused = False

    def is_paused(self):
        return self.paused

    def set_transition_callback(self, callback_fn):
        self.on_transition = callback_fn

    def has_state(self, name):
        return any(s.name == name for s in self.states)

    def restart(self):
        self.reset()
        self.start()

    def AddWaitState(self, name, condition_fn, timeout_ms=10000, on_timeout=None, on_enter=None, on_exit=None):
        timer = Timer()
        def exit_fn():
            if condition_fn():
                return True
            if timer.HasElapsed(timeout_ms):
                if on_timeout:
                    try:
                        on_timeout()
                    except Exception as e:
                        if self.log_actions:
                            ConsoleLog("FSM", f"Error in on_timeout for state '{name}': {e}", Py4GW.Console.MessageType.Error)
                return True
            return False

        wait_state = FSM.State(
            id=self.state_counter,
            name=name,
            execute_fn=lambda: None,
            exit_condition=exit_fn,
            run_once=True,
            on_enter=on_enter,      # <-- PASS on_enter
            on_exit=on_exit 
        )
        wait_state.transition_timer = timer
        if self.states:
            self.states[-1].set_next_state(wait_state)

        self.states.append(wait_state)
        self.state_counter += 1

    def trigger_event(self, event_name: str) -> bool:
        """
        Triggers an event, potentially causing an immediate state transition
        if the current state is configured to handle it.

        :param event_name: The name of the event to trigger.
        :return: True if the event caused a transition, False otherwise.
        """
        if self.paused or self.finished or not self.current_state:
            return False # Cannot transition if paused, finished, or not started

        target_state_name = self.current_state.event_transitions.get(event_name)

        if target_state_name:
            target_state = self._get_state_by_name(target_state_name)
            if target_state:
                if self.log_actions:
                    ConsoleLog("FSM", f"{self.name}: Event '{event_name}' triggered transition from '{self.current_state.name}' to '{target_state.name}'", Py4GW.Console.MessageType.Info)

                # --- Perform Transition ---
                original_state_name = self.current_state.name
                self.current_state.exit()

                if self.on_transition:
                    try:
                        self.on_transition(original_state_name, target_state.name)
                    except Exception as e:
                         ConsoleLog("FSM", f"Error in on_transition callback during event '{event_name}': {e}", Py4GW.Console.MessageType.Error)


                self.current_state = target_state
                self.current_state.reset() # Reset the new state
                self.current_state.enter()
                # --- End Transition ---

                return True
            else:
                # Log error: target state name defined but not found
                ConsoleLog("FSM", f"{self.name}: Event '{event_name}' defined transition to unknown state '{target_state_name}' from state '{self.current_state.name}'", Py4GW.Console.MessageType.Error)
                return False
        else:
            # Event not handled by the current state
            if self.log_actions:
                 ConsoleLog("FSM", f"{self.name}: Event '{event_name}' triggered but not handled by current state '{self.current_state.name}'", Py4GW.Console.MessageType.Debug)
            return False

    def update(self):
        if self.paused:
            if self.log_actions:
                ConsoleLog("FSM", f"{self.name}: FSM is paused.", Py4GW.Console.MessageType.Warning)
            return
        
        if self.finished:
            if self.log_actions:
                ConsoleLog("FSM", f"{self.name}: FSM has finished.", Py4GW.Console.MessageType.Warning)
            return
        
        if not self.current_state:
            if self.log_actions:
                ConsoleLog("FSM", f"{self.name}: FSM has not been started.", Py4GW.Console.MessageType.Warning)
            return

        if self.log_actions:
            ConsoleLog("FSM", f"{self.name}: Executing state: {self.current_state.name}", Py4GW.Console.MessageType.Info)
        self.current_state.execute()

        if not self.current_state.can_exit():
            return

        self.current_state.exit()
        next_state_polling = getattr(self.current_state, 'next_state', None) # Get the *original* next_state
        
        if next_state_polling:
            original_state_name = self.current_state.name # Store name before changing
            if self.on_transition:
                 try:
                     self.on_transition(original_state_name, next_state_polling.name)
                 except Exception as e:
                     ConsoleLog("FSM", f"Error in on_transition callback during polling transition: {e}", Py4GW.Console.MessageType.Error)
            
            self.current_state = next_state_polling
            self.current_state.reset()
            self.current_state.enter()

            if self.log_actions:
                ConsoleLog("FSM", f"{self.name}: Transitioning to state: {self.current_state.name}", Py4GW.Console.MessageType.Info)
            return

        final_state_name = self.current_state.name
        self.current_state = None
        self.finished = True

        if self.log_actions:
            ConsoleLog("FSM", f"{self.name}: Reached the final state: {final_state_name}. FSM has completed.", Py4GW.Console.MessageType.Success)
        
        if self.on_complete:
            try:
                self.on_complete()
            except Exception as e:
                ConsoleLog("FSM", f"Error in on_complete callback: {e}", Py4GW.Console.MessageType.Error)

    def is_started(self):
        """Check whether the FSM has been started."""
        return self.current_state is not None and not self.finished
                
    def is_finished(self):
        """Check whether the FSM has finished executing all states."""
        return self.finished

    def jump_to_state_by_name(self, state_name):
        """Jump to a specific state by its name."""
        for state in self.states:
            if state.name == state_name:
                self.current_state = state
                self.current_state.reset() # Reset the state upon jumping to it
                self.current_state.enter()
                if self.log_actions:
                    Py4GW.Console.Log("FSM", f"{self.name}: Jumped to state: {self.current_state.name}", Py4GW.Console.MessageType.Info)
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
    
    def _get_state_by_name(self, state_name: str) -> Optional[State]:
        """Finds a state object by its name."""
        for state in self.states:
            if state.name == state_name:
                return state
        return None
    
#endregion

#region MultiThreading

class MultiThreading:
    def __init__(self, timeout=1.0, log_actions=False):
        """Initialize thread manager."""
        self.threads = {}
        self.log_actions = log_actions
        self.lock = threading.Lock()
        self.timeout = timeout
        self.watchdog_thread = None
        self.watchdog_active = False

    def add_thread(self, name, execute_fn, *args, **kwargs):
        """Add and immediately start a thread."""
        with self.lock:
            if name in self.threads:
                Py4GW.Console.Log("MultiThreading", f"Thread '{name}' already exists.", Py4GW.Console.MessageType.Warning)
                return

            # Prepare thread entry
            last_keepalive = time.time()
            self.threads[name] = {
                "thread": None,
                "target_fn": execute_fn,
                "args": args,
                "kwargs": kwargs,
                "last_keepalive": last_keepalive
            }

        # Start thread immediately
        self.start_thread(name)

    def start_thread(self, name):
        """Start the thread."""
        with self.lock:
            if name not in self.threads:
                Py4GW.Console.Log("MultiThreading", f"Thread '{name}' does not exist.", Py4GW.Console.MessageType.Warning)
                return

            thread_info = self.threads[name]
            thread = thread_info.get("thread")
            if thread and thread.is_alive():
                Py4GW.Console.Log("MultiThreading", f"Thread '{name}' already running.", Py4GW.Console.MessageType.Warning)
                return

            # Create a NEW thread object every time we start
            execute_fn = thread_info["target_fn"]
            args = thread_info["args"]
            kwargs = thread_info["kwargs"]

            def wrapped_target(*args, **kwargs):
                if self.log_actions:
                    Py4GW.Console.Log("MultiThreading", f"Thread '{name}' running.", Py4GW.Console.MessageType.Info)
                try:
                    execute_fn(*args, **kwargs)
                except SystemExit:
                    if self.log_actions:
                        Py4GW.Console.Log("MultiThreading", f"Thread '{name}' forcefully exited.", Py4GW.Console.MessageType.Info)
                except Exception as e:
                    Py4GW.Console.Log("MultiThreading", f"Thread '{name}' exception: {str(e)}", Py4GW.Console.MessageType.Error)
                finally:
                    if self.log_actions:
                        Py4GW.Console.Log("MultiThreading", f"Thread '{name}' exited.", Py4GW.Console.MessageType.Info)

            new_thread = threading.Thread(target=wrapped_target, args=args, kwargs=kwargs, daemon=True)
            self.threads[name]["thread"] = new_thread
            self.threads[name]["last_keepalive"] = time.time()
            new_thread.start()

            if self.log_actions:
                Py4GW.Console.Log("MultiThreading", f"Thread '{name}' started.", Py4GW.Console.MessageType.Success)

    def update_keepalive(self, name):
        """Update keepalive timestamp."""
        with self.lock:
            if name in self.threads:
                self.threads[name]["last_keepalive"] = time.time()
                
    def update_all_keepalives(self):
        """Update keepalive timestamp for all threads except the watchdog."""
        current_time = time.time()
        with self.lock:
            for name, info in self.threads.items():
                if name == "watchdog":  # Optional: skip watchdog
                    continue
                self.threads[name]["last_keepalive"] = current_time


    def stop_thread(self, name):
        with self.lock:
            if name not in self.threads:
                if self.log_actions:
                    Py4GW.Console.Log("MultiThreading", f"Thread '{name}' does not exist.", Py4GW.Console.MessageType.Warning)
                return

            thread_info = self.threads[name]
            thread = thread_info.get("thread")
            if thread and thread.is_alive():
                if self.log_actions:
                    Py4GW.Console.Log("MultiThreading", f"Force stopping thread '{name}'.", Py4GW.Console.MessageType.Warning)
                ctypes.pythonapi.PyThreadState_SetAsyncExc(ctypes.c_long(thread.ident), ctypes.py_object(SystemExit))
                time.sleep(0.1)

            del self.threads[name]
        if self.log_actions:
            Py4GW.Console.Log("MultiThreading", f"Thread '{name}' stopped and removed.", Py4GW.Console.MessageType.Info)

    def stop_all_threads(self):
        with self.lock:
            thread_names = list(self.threads.keys())

        for name in thread_names:
            self.stop_thread(name)




    def check_timeouts(self):
        """Watchdog force-stops expired threads."""
        current_time = time.time()
        expired = []
        with self.lock:
            for name, info in self.threads.items():
                if current_time - info["last_keepalive"] > self.timeout:
                    expired.append(name)

        for name in expired:
            Py4GW.Console.Log("MultiThreading", f"Thread '{name}' keepalive expired, force stopping.", Py4GW.Console.MessageType.Warning)
            self.stop_thread(name)


    def start_watchdog(self, main_thread_name):
        if self.watchdog_thread and self.watchdog_thread.is_alive():
            Py4GW.Console.Log("MultiThreading", "Watchdog already running.", Py4GW.Console.MessageType.Warning)
            return

        self.watchdog_active = True

        def watchdog_fn():
            from .Map import Map
            if self.log_actions:
                Py4GW.Console.Log("Watchdog", "Watchdog started.", Py4GW.Console.MessageType.Info)
            while self.watchdog_active:
                current_time = time.time()
                expired_threads = []

                if Map.IsMapLoading():
                    time.sleep(3)
                    continue
                else:
                    with self.lock:
                        for name, info in self.threads.items():
                            if name == "watchdog":
                                continue

                            last_keepalive = info["last_keepalive"]
                            if current_time - last_keepalive > self.timeout:
                                expired_threads.append(name)

                # Expire threads
                for name in expired_threads:
                    if name != main_thread_name:
                        ConsoleLog("Watchdog", f"Thread '{name}' timed out. Stopping it.", Console.MessageType.Warning, log=True)
                        self.stop_thread(name)

                # MAIN_THREAD_NAME expired → stop all
                if main_thread_name in expired_threads:
                    ConsoleLog("Watchdog", f"Main thread '{main_thread_name}' timed out! Stopping all threads.", Console.MessageType.Error, log=True)
                    self.stop_all_threads()
                    break

                # Check if only watchdog remains
                with self.lock:
                    active_threads = [name for name in self.threads.keys() if name != "watchdog"]

                if not active_threads:
                    ConsoleLog("Watchdog", "No active threads left. Stopping watchdog.", Console.MessageType.Notice, log=True)
                    self.watchdog_active = False
                    break

                time.sleep(0.3)

            # Final cleanup
            with self.lock:
                if "watchdog" in self.threads:
                    del self.threads["watchdog"]
            Py4GW.Console.Log("Watchdog", "Watchdog stopped & cleaned.", Py4GW.Console.MessageType.Info)

        # Register watchdog in threads registry
        with self.lock:
            self.threads["watchdog"] = {
                "thread": None,
                "target_fn": None,
                "args": (),
                "kwargs": {},
                "last_keepalive": time.time()
            }

        # Start watchdog thread
        watchdog_thread = threading.Thread(target=watchdog_fn, daemon=True)
        self.watchdog_thread = watchdog_thread
        self.threads["watchdog"]["thread"] = watchdog_thread
        watchdog_thread.start()
        if self.log_actions:
            Py4GW.Console.Log("MultiThreading", "Watchdog thread started.", Py4GW.Console.MessageType.Success)

    def stop_watchdog(self):
        """Manually stop watchdog if needed."""
        self.watchdog_active = False

#endregion


#region ConfigCalsses
class LootConfig:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(LootConfig, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self.reset()
        self._initialized = True

    def reset(self):
        self.loot_gold_coins = False
        self.loot_whites = False
        self.loot_blues = False
        self.loot_purples = False
        self.loot_golds = False
        self.loot_greens = False
        self.whitelist = set()  # Avoid duplicates
        self.blacklist = set()
        self.item_id_blacklist = set()  # For items that are blacklisted by ID
        self.item_id_whitelist = set()  # For items that are whitelisted by ID

    def SetProperties(self, loot_whites=False, loot_blues=False, loot_purples=False, loot_golds=False, loot_greens=False, loot_gold_coins=False):
        self.loot_gold_coins = loot_gold_coins
        self.loot_whites = loot_whites
        self.loot_blues = loot_blues
        self.loot_purples = loot_purples
        self.loot_golds = loot_golds
        self.loot_greens = loot_greens

    def AddToWhitelist(self, model_id: int):
        self.whitelist.add(model_id)

    def AddToBlacklist(self, model_id: int):
        self.blacklist.add(model_id)
        
    def AddItemIDToWhitelist(self, item_id: int):
        """
        Add an item ID to the whitelist.
        This is used for items that should be picked up regardless of their model ID.
        """
        self.item_id_whitelist.add(item_id)
        
    def AddItemIDToBlacklist(self, item_id: int):
        """
        Add an item ID to the blacklist.
        This is used for items that should not be picked up regardless of their model ID.
        """
        self.item_id_blacklist.add(item_id)

    def RemoveFromWhitelist(self, model_id: int):
        self.whitelist.discard(model_id)
        
    def RemoveItemIDFromWhitelist(self, item_id: int):
        """
        Remove an item ID from the whitelist.
        This is used for items that were previously whitelisted.
        """
        self.item_id_whitelist.discard(item_id)

    def RemoveFromBlacklist(self, model_id: int):
        self.blacklist.discard(model_id)
        
    def RemoveItemIDFromBlacklist(self, item_id: int):
        """
        Remove an item ID from the blacklist.
        This is used for items that were previously blacklisted.
        """
        self.item_id_blacklist.discard(item_id)
        
    def ClearWhitelist(self):
        self.whitelist.clear()
        
    def ClearItemIDWhitelist(self):
        """
        Clear the item ID whitelist.
        This is used to remove all item IDs that were whitelisted.
        """
        self.item_id_whitelist.clear()
        
    def ClearBlacklist(self):
        self.blacklist.clear()
        
    def ClearItemIDBlacklist(self):
        """
        Clear the item ID blacklist.
        This is used to remove all item IDs that were blacklisted.
        """
        self.item_id_blacklist.clear()

    def IsWhitelisted(self, model_id: int):
        return model_id in self.whitelist

    def IsBlacklisted(self, model_id: int):
        return model_id in self.blacklist
    
    def IsItemIDWhitelisted(self, item_id: int):
        """
        Check if an item ID is whitelisted.
        This is used to determine if an item should be picked up based on its ID.
        """
        return item_id in self.item_id_whitelist
    
    def IsItemIDBlacklisted(self, item_id: int):
        """
        Check if an item ID is blacklisted.
        This is used to determine if an item should be ignored based on its ID.
        """
        return item_id in self.item_id_blacklist

    def GetWhitelist(self):
        return list(self.whitelist)

    def GetBlacklist(self):
        return list(self.blacklist)
    
    def GetItemIDBlacklist(self):
        """
        Get the list of blacklisted item IDs.
        This is used to retrieve all item IDs that should not be picked up.
        """
        return list(self.item_id_blacklist)

    def GetfilteredLootArray(self, distance: float = Range.SafeCompass.value, multibox_loot: bool = False, allow_unasigned_loot=False) -> list[int]:
        from .AgentArray import AgentArray
        from .GlobalCache import GLOBAL_CACHE
        from .Routines import Routines
        from .Agent import Agent
        from .Item import Item
        if not Routines.Checks.Map.MapValid():
            return []
        
        def IsValidItem(item_id):
            if not Routines.Checks.Map.MapValid():
                return False
            
            if not Agent.IsValid(item_id):
                return False    
            player_agent_id = GLOBAL_CACHE.Player.GetAgentID()
            owner_id = Agent.GetItemAgentOwnerID(item_id)
            return ((owner_id == player_agent_id) or (owner_id == 0))

        def IsValidFollowerItem(item_id):
            if not Routines.Checks.Map.MapValid():
                return False
            if not Agent.IsValid(item_id):
                return False 
            party_leader_id = GLOBAL_CACHE.Party.GetPartyLeaderID()
            player_agent_id = GLOBAL_CACHE.Player.GetAgentID()
            owner_id = Agent.GetItemAgentOwnerID(item_id)
            
            if party_leader_id == player_agent_id:
                # If the player is the party leader, gold coins are valid
                agent = Agent.agent_instance(item_id)
                item_agent_id = agent.item_agent.item_id
                model_id = Item.GetModelID(item_agent_id)
                if model_id == ModelID.Gold_Coins.value:
                    is_gold_coin = True
                else:
                    is_gold_coin = allow_unasigned_loot

                return ((owner_id == player_agent_id) or (is_gold_coin))
            else:
                # If the player is a follower, only items owned by the player are valid
                return (owner_id == player_agent_id)
            
        
        if not Routines.Checks.Map.MapValid():
            return []
            
        loot_array = GLOBAL_CACHE.AgentArray.GetItemArray()
        loot_array = AgentArray.Filter.ByDistance(loot_array, GLOBAL_CACHE.Player.GetXY(), distance)

        if multibox_loot:
            loot_array = AgentArray.Filter.ByCondition(loot_array, lambda item_id: IsValidFollowerItem(item_id))
        else:
            loot_array = AgentArray.Filter.ByCondition(loot_array, lambda item_id: IsValidItem(item_id))


        for agent_id in loot_array[:]:  # Iterate over a copy to avoid modifying while iterating
            item_data = GLOBAL_CACHE.Agent.GetItemAgent(agent_id)
            item_id = item_data.item_id
            model_id = GLOBAL_CACHE.Item.GetModelID(item_id)

            if self.IsWhitelisted(model_id):
                continue
            
            if self.IsItemIDWhitelisted(item_id):
                continue

            if self.IsBlacklisted(model_id):
                loot_array.remove(agent_id)
                continue
            
            if self.IsItemIDBlacklisted(item_id):
                loot_array.remove(agent_id)
                continue

            if not self.loot_whites and GLOBAL_CACHE.Item.Rarity.IsWhite(item_id):
                loot_array.remove(agent_id)
                continue
            if not self.loot_blues and GLOBAL_CACHE.Item.Rarity.IsBlue(item_id):
                loot_array.remove(agent_id)
                continue
            if not self.loot_purples and GLOBAL_CACHE.Item.Rarity.IsPurple(item_id):
                loot_array.remove(agent_id)
                continue
            if not self.loot_golds and GLOBAL_CACHE.Item.Rarity.IsGold(item_id):
                loot_array.remove(agent_id)
                continue
            if not self.loot_greens and GLOBAL_CACHE.Item.Rarity.IsGreen(item_id):
                loot_array.remove(agent_id)
                continue

        loot_array = AgentArray.Sort.ByDistance(loot_array, GLOBAL_CACHE.Player.GetXY())

        return loot_array
#endregion


import Py4GW


#region AutoInventory
class AutoInventoryHandler():
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AutoInventoryHandler, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        from Py4GWCoreLib import ThrottledTimer, IniHandler
        if self._initialized:
            return
        self._LOOKUP_TIME:int = 15000
        self.lookup_throttle = ThrottledTimer(self._LOOKUP_TIME)
        self.ini = IniHandler("AutoLoot.ini")
        self.initialized = False
        self.status = "Idle"
        self.outpost_handled = False
        self.module_active = False
        self.module_name = "AutoInventoryHandler"
        
        self.id_whites = False
        self.id_blues = True
        self.id_purples = True
        self.id_golds = False
        self.id_greens = False
        
        self.salvage_whites = True
        self.salvage_rare_materials = False
        self.salvage_blues = True
        self.salvage_purples = True
        self.salvage_golds = False
        self.salvage_blacklist = []  # Items that should not be salvaged, even if they match the salvage criteria
        self.blacklisted_model_id = 0
        self.model_id_search = ""
        self.model_id_search_mode = 0  # 0 = Contains, 1 = Starts With
        self.show_dialog_popup = False 
        
        self.deposit_trophies = True
        self.deposit_materials = True
        self.deposit_blues = True
        self.deposit_purples = True
        self.deposit_golds = True
        self.deposit_greens = True
        self.keep_gold = 5000
        
        self.load_from_ini(self.ini, "AutoLootOptions")
        self._initialized = True
           
    def save_to_ini(self, section: str = "AutoLootOptions"):
        self.ini.write_key(section, "module_active", str(self.module_active))
        self.ini.write_key(section, "lookup_time", str(self._LOOKUP_TIME))
        self.ini.write_key(section, "id_whites", str(self.id_whites))
        self.ini.write_key(section, "id_blues", str(self.id_blues))
        self.ini.write_key(section, "id_purples", str(self.id_purples))
        self.ini.write_key(section, "id_golds", str(self.id_golds))
        self.ini.write_key(section, "id_greens", str(self.id_greens))

        self.ini.write_key(section, "salvage_whites", str(self.salvage_whites))
        self.ini.write_key(section, "salvage_rare_materials", str(self.salvage_rare_materials))
        self.ini.write_key(section, "salvage_blues", str(self.salvage_blues))
        self.ini.write_key(section, "salvage_purples", str(self.salvage_purples))
        self.ini.write_key(section, "salvage_golds", str(self.salvage_golds))

        self.ini.write_key(section, "salvage_blacklist", ",".join(str(i) for i in sorted(set(self.salvage_blacklist))))

        self.ini.write_key(section, "deposit_trophies", str(self.deposit_trophies))
        self.ini.write_key(section, "deposit_materials", str(self.deposit_materials))
        self.ini.write_key(section, "deposit_blues", str(self.deposit_blues))
        self.ini.write_key(section, "deposit_purples", str(self.deposit_purples))
        self.ini.write_key(section, "deposit_golds", str(self.deposit_golds))
        self.ini.write_key(section, "deposit_greens", str(self.deposit_greens))
        self.ini.write_key(section, "keep_gold", str(self.keep_gold))


    def load_from_ini(self, ini, section: str = "AutoLootOptions"):
        from Py4GWCoreLib import ThrottledTimer

        self._LOOKUP_TIME = ini.read_int(section, "lookup_time", self._LOOKUP_TIME)
        self.lookup_throttle = ThrottledTimer(self._LOOKUP_TIME)

        self.module_active = ini.read_bool(section, "module_active", self.module_active)
        self.id_whites = ini.read_bool(section, "id_whites", self.id_whites)
        self.id_blues = ini.read_bool(section, "id_blues", self.id_blues)
        self.id_purples = ini.read_bool(section, "id_purples", self.id_purples)
        self.id_golds = ini.read_bool(section, "id_golds", self.id_golds)
        self.id_greens = ini.read_bool(section, "id_greens", self.id_greens)

        self.salvage_whites = ini.read_bool(section, "salvage_whites", self.salvage_whites)
        self.salvage_rare_materials = ini.read_bool(section, "salvage_rare_materials", self.salvage_rare_materials)
        self.salvage_blues = ini.read_bool(section, "salvage_blues", self.salvage_blues)
        self.salvage_purples = ini.read_bool(section, "salvage_purples", self.salvage_purples)
        self.salvage_golds = ini.read_bool(section, "salvage_golds", self.salvage_golds)

        blacklist_str = ini.read_key(section, "salvage_blacklist", "")
        self.salvage_blacklist = [int(x) for x in blacklist_str.split(",") if x.strip().isdigit()]


        self.deposit_trophies = ini.read_bool(section, "deposit_trophies", self.deposit_trophies)
        self.deposit_materials = ini.read_bool(section, "deposit_materials", self.deposit_materials)
        self.deposit_blues = ini.read_bool(section, "deposit_blues", self.deposit_blues)
        self.deposit_purples = ini.read_bool(section, "deposit_purples", self.deposit_purples)
        self.deposit_golds = ini.read_bool(section, "deposit_golds", self.deposit_golds)
        self.deposit_greens = ini.read_bool(section, "deposit_greens", self.deposit_greens)

        self.keep_gold = ini.read_int(section, "keep_gold", self.keep_gold)
        
    def AutoID(self, item_id):
        from Py4GWCoreLib import Inventory, ConsoleLog
        first_id_kit = Inventory.GetFirstIDKit()
        if first_id_kit == 0:
            ConsoleLog(self.module_name, "No ID Kit found in inventory", Py4GW.Console.MessageType.Warning)
        else:
            Inventory.IdentifyItem(item_id, first_id_kit)
            
    def AutoSalvage(self, item_id):
        from Py4GWCoreLib import Inventory, ConsoleLog
        first_salv_kit = Inventory.GetFirstSalvageKit(use_lesser=True)
        if first_salv_kit == 0:
            ConsoleLog(self.module_name, "No Salvage Kit found in inventory", Py4GW.Console.MessageType.Warning)
        else:
            Inventory.SalvageItem(item_id, first_salv_kit)
            
    def IdentifyItems(self):
        from Py4GWCoreLib import GLOBAL_CACHE, Item, Routines, Bags, ActionQueueManager, ConsoleLog
        def _get_total_id_uses():
            total_uses = 0
            for bag_id in range(Bags.Backpack, Bags.Bag2 + 1):
                bag_items = GLOBAL_CACHE.ItemArray.GetItemArray(GLOBAL_CACHE.ItemArray.CreateBagList(bag_id))
                for item_id in bag_items:
                    if Item.Usage.IsIDKit(item_id):
                        total_uses += Item.Usage.GetUses(item_id)

            return total_uses
        
        total_uses = _get_total_id_uses()
        current_uses = 0
        for bag_id in range(Bags.Backpack, Bags.Bag2+1):
            bag_to_check = GLOBAL_CACHE.ItemArray.CreateBagList(bag_id)
            item_array = GLOBAL_CACHE.ItemArray.GetItemArray(bag_to_check)
            
            for item_id in item_array:
                if total_uses == 0:
                    ConsoleLog(self.module_name, f"Identified {current_uses} items, no more ID Kits left in inventory", Py4GW.Console.MessageType.Warning)
                    yield
                    return
                
                is_identified = GLOBAL_CACHE.Item.Usage.IsIdentified(item_id)
                
                if is_identified:
                    yield
                    continue
                
                _,rarity = GLOBAL_CACHE.Item.Rarity.GetRarity(item_id)
                if ((rarity == "White" and self.id_whites) or
                    (rarity == "Blue" and self.id_blues) or
                    (rarity == "Green" and self.id_greens) or
                    (rarity == "Purple" and self.id_purples) or
                    (rarity == "Gold" and self.id_golds)):
                    ActionQueueManager().AddAction("IDENTIFY", self.AutoID, item_id)
                    current_uses += 1
                    total_uses -= 1
                    yield
                    
        while not ActionQueueManager().IsEmpty("IDENTIFY"):
            yield from Routines.Yield.wait(100)
                    
        if current_uses > 0:
            ConsoleLog(self.module_name, f"Identified {current_uses} items", Py4GW.Console.MessageType.Success)
            
    def SalvageItems(self):
        from Py4GWCoreLib import GLOBAL_CACHE, Item, Routines, Bags, ActionQueueManager, ConsoleLog, Inventory
        def _get_total_salv_uses():
            total_uses = 0
            for bag_id in range(Bags.Backpack, Bags.Bag2 + 1):
                bag_items = GLOBAL_CACHE.ItemArray.GetItemArray(GLOBAL_CACHE.ItemArray.CreateBagList(bag_id))
                for item_id in bag_items:
                    if Item.Usage.IsLesserKit(item_id):
                        total_uses += Item.Usage.GetUses(item_id)

            return total_uses
        
        total_uses = _get_total_salv_uses()
        current_uses = 0
        for bag_id in range(Bags.Backpack, Bags.Bag2+1):
            bag_to_check = GLOBAL_CACHE.ItemArray.CreateBagList(bag_id)
            item_array = GLOBAL_CACHE.ItemArray.GetItemArray(bag_to_check)
            
            for item_id in item_array:
                if total_uses == 0:
                    ConsoleLog(self.module_name, f"Salvaged {current_uses} items, no more Salvage Kits left in inventory", Py4GW.Console.MessageType.Warning)
                    yield
                    return
                
                quantity = GLOBAL_CACHE.Item.Properties.GetQuantity(item_id)
                _,rarity = GLOBAL_CACHE.Item.Rarity.GetRarity(item_id)
                is_white =  rarity == "White"
                is_blue = rarity == "Blue"
                is_green = rarity == "Green"
                is_purple = rarity == "Purple"
                is_gold = rarity == "Gold"
                is_material = GLOBAL_CACHE.Item.Type.IsMaterial(item_id)
                is_material_salvageable = GLOBAL_CACHE.Item.Usage.IsMaterialSalvageable(item_id)
                is_identified = GLOBAL_CACHE.Item.Usage.IsIdentified(item_id)
                is_salvageable = GLOBAL_CACHE.Item.Usage.IsSalvageable(item_id)
                is_salvage_kit = GLOBAL_CACHE.Item.Usage.IsLesserKit(item_id)
                model_id = GLOBAL_CACHE.Item.GetModelID(item_id)
                
                if not ((is_white and is_salvageable) or (is_identified and is_salvageable)):
                    yield
                    continue
                
                if model_id in self.salvage_blacklist:
                    yield
                    continue
                
                if is_white and is_material and is_material_salvageable and not self.salvage_rare_materials:
                    yield
                    continue
                
                if is_white and not is_material and not self.salvage_whites:
                    yield
                    continue
                
                if is_blue and not self.salvage_blues:
                    yield
                    continue
                
                if is_purple and not self.salvage_purples:
                    yield
                    continue
                
                if is_gold and not self.salvage_golds:
                    yield
                    continue
                

                for _ in range(quantity):
                    ActionQueueManager().AddAction("SALVAGE", self.AutoSalvage, item_id)
                    
                    if (is_purple or is_gold):
                        ActionQueueManager().AddAction("SALVAGE", Inventory.AcceptSalvageMaterialsWindow)
                    
                    current_uses += 1
                    total_uses -= 1
                    
                    while not ActionQueueManager().IsEmpty("SALVAGE"):
                        yield from Routines.Yield.wait(50)
                    
                    if total_uses == 0:
                        ConsoleLog(self.module_name, f"Salvaged {current_uses} items, no more Salvage Kits left in inventory", Py4GW.Console.MessageType.Warning)
                        yield
                        return

                    yield
                    
                    
        if current_uses > 0:
            ConsoleLog(self.module_name, f"Salvaged {current_uses} items", Py4GW.Console.MessageType.Success)
            
    def DepositItemsAuto(self):
        from Py4GWCoreLib import GLOBAL_CACHE, Routines, Bags
        for bag_id in range(Bags.Backpack, Bags.Bag2+1):
            bag_to_check = GLOBAL_CACHE.ItemArray.CreateBagList(bag_id)
            item_array = GLOBAL_CACHE.ItemArray.GetItemArray(bag_to_check)
            
            for item_id in item_array:
                # Check if the item is a trophy or material
                is_trophy = GLOBAL_CACHE.Item.Type.IsTrophy(item_id)
                is_tome = GLOBAL_CACHE.Item.Type.IsTome(item_id)
                _, item_type = GLOBAL_CACHE.Item.GetItemType(item_id)
                is_usable = (item_type == "Usable")
                
                is_material = GLOBAL_CACHE.Item.Type.IsMaterial(item_id)
                _, rarity = GLOBAL_CACHE.Item.Rarity.GetRarity(item_id)
                is_white =  rarity == "White"
                is_blue = rarity == "Blue"
                is_green = rarity == "Green"
                is_purple = rarity == "Purple"
                is_gold = rarity == "Gold"
                
                if is_tome:
                    GLOBAL_CACHE.Inventory.DepositItemToStorage(item_id)
                    yield from Routines.Yield.wait(350)
                
                if is_trophy and self.deposit_trophies and is_white:
                    GLOBAL_CACHE.Inventory.DepositItemToStorage(item_id)
                    yield from Routines.Yield.wait(350)
                
                if is_material and self.deposit_materials:
                    GLOBAL_CACHE.Inventory.DepositItemToStorage(item_id)
                    yield from Routines.Yield.wait(350)
                
                if is_blue and self.deposit_blues:
                    GLOBAL_CACHE.Inventory.DepositItemToStorage(item_id)
                    yield from Routines.Yield.wait(350)
                
                if is_purple and self.deposit_purples:
                    GLOBAL_CACHE.Inventory.DepositItemToStorage(item_id)
                    yield from Routines.Yield.wait(350)
                
                if is_gold and self.deposit_golds and not is_usable and not is_trophy:
                    GLOBAL_CACHE.Inventory.DepositItemToStorage(item_id)
                    yield from Routines.Yield.wait(350)
                
                if is_green and self.deposit_greens:
                    GLOBAL_CACHE.Inventory.DepositItemToStorage(item_id)
                    yield from Routines.Yield.wait(350)
            
            
    def IDAndSalvageItems(self):
        self.status = "Identifying"
        yield from self.IdentifyItems()
        self.status = "Salvaging"
        yield from self.SalvageItems()
        self.status = "Idle"
        yield
        
    def IDSalvageDepositItems(self):
        from Py4GWCoreLib import Routines, ConsoleLog
        ConsoleLog("AutoInventoryHandler", "Starting ID, Salvage and Deposit routine", Py4GW.Console.MessageType.Info)
        self.status = "Identifying"
        yield from self.IdentifyItems()
        
        self.status = "Salvaging"
        yield from self.SalvageItems()
        
        self.status = "Depositing"
        yield from self.DepositItemsAuto()
        
        self.status = "Depositing Gold"
        
        yield from Routines.Yield.Items.DepositGold(self.keep_gold, log =False)
        
        self.status = "Idle"
        ConsoleLog("AutoInventoryHandler", "ID, Salvage and Deposit routine completed", Py4GW.Console.MessageType.Success)


#endregion
