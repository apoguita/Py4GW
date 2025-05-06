from Py4GWCoreLib import *
import traceback
import os
import configparser

from .constants import (
    MAX_NUM_PLAYERS,
    PRIORITY_TARGET_MODULE_NAME,
    Range,
)

class PriorityTargets:
    _instance = None  # Singleton instance
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(PriorityTargets, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self.character_targets = {}  # Dictionary to store targets by character name
            self.character_enabled = {}  # Dictionary to store enabled state by character
            self.config_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "Config")
            self.config_file = os.path.join(self.config_dir, "priority_targets.ini")
            
            # Create the directory if it doesn't exist
            if not os.path.exists(self.config_dir):
                os.makedirs(self.config_dir)
                
            # Load the configuration
            self._load_from_file()
            self._initialized = True
    
    def get_character_name(self):
        """Get the current character's name"""
        player_id = Player.GetAgentID()
        login_number = Agent.GetLoginNumber(player_id)
        return Party.Players.GetPlayerNameByLoginNumber(login_number)
    
    def _load_from_file(self):
        """Load the priority targets from file"""
        try:
            if not os.path.exists(self.config_file):
                # Create a new configuration file
                self._save_to_file()
                return

            config = configparser.ConfigParser()
            config.read(self.config_file)
            
            # Clear dictionaries and rebuild them
            self.character_targets = {}
            self.character_enabled = {}
            
            for section in config.sections():
                # This is a character section
                character_name = section
                self.character_targets[character_name] = []
                
                # Get the enabled state for this character (default to True)
                self.character_enabled[character_name] = config.getboolean(section, 'Enabled', fallback=True)
                
                for key, value in config[section].items():
                    if key.startswith('id_'):
                        try:
                            model_id = int(value)
                            if model_id not in self.character_targets[character_name]:
                                self.character_targets[character_name].append(model_id)
                        except ValueError:
                            Py4GW.Console.Log(PRIORITY_TARGET_MODULE_NAME, f"Invalid model ID in config file for {character_name}: {value}", Py4GW.Console.MessageType.Warning)
        
        except Exception as e:
            Py4GW.Console.Log(PRIORITY_TARGET_MODULE_NAME, f"Error loading priority targets from file: {str(e)}", Py4GW.Console.MessageType.Error)
            Py4GW.Console.Log(PRIORITY_TARGET_MODULE_NAME, f"Stack trace: {traceback.format_exc()}", Py4GW.Console.MessageType.Error)
    
    def _save_to_file(self):
        """Save the priority targets to file"""
        try:
            config = configparser.ConfigParser()
            
            # Add a section for each character
            for character_name in set(list(self.character_targets.keys()) + list(self.character_enabled.keys())):
                if not config.has_section(character_name):
                    config.add_section(character_name)
                
                # Add the enabled state for this character
                config[character_name]['Enabled'] = str(self.character_enabled.get(character_name, True))
                
                # Add the model IDs for this character
                for i, model_id in enumerate(self.character_targets.get(character_name, [])):
                    config[character_name][f'id_{i}'] = str(model_id)
            
            # Write to file
            with open(self.config_file, 'w') as f:
                config.write(f)
            
            Py4GW.Console.Log(PRIORITY_TARGET_MODULE_NAME, "Priority targets saved to file.", Py4GW.Console.MessageType.Info)
        
        except Exception as e:
            Py4GW.Console.Log(PRIORITY_TARGET_MODULE_NAME, f"Error saving priority targets to file: {str(e)}", Py4GW.Console.MessageType.Error)
            Py4GW.Console.Log(PRIORITY_TARGET_MODULE_NAME, f"Stack trace: {traceback.format_exc()}", Py4GW.Console.MessageType.Error)
    
    def add_model_id(self, model_id, character_name=None):
        """Add a model ID to the priority targets list for a specific character"""
        if character_name is None:
            character_name = self.get_character_name()
            
        # Ensure the character exists in our dictionaries
        if character_name not in self.character_targets:
            self.character_targets[character_name] = []
        
        if character_name not in self.character_enabled:
            self.character_enabled[character_name] = True
            
        try:
            # Convert to integer to ensure we have a valid model ID
            model_id = int(model_id)
            if model_id not in self.character_targets[character_name]:
                self.character_targets[character_name].append(model_id)
                self._save_to_file()
                return True
            return False
        except ValueError:
            Py4GW.Console.Log(PRIORITY_TARGET_MODULE_NAME, f"Invalid model ID: {model_id}", Py4GW.Console.MessageType.Error)
            return False
    
    def remove_model_id(self, model_id, character_name=None):
        """Remove a model ID from the priority targets list for a specific character"""
        if character_name is None:
            character_name = self.get_character_name()
            
        # Ensure the character exists in our dictionaries
        if character_name not in self.character_targets:
            self.character_targets[character_name] = []
            
        try:
            model_id = int(model_id)
            if model_id in self.character_targets[character_name]:
                self.character_targets[character_name].remove(model_id)
                self._save_to_file()
                return True
            return False
        except ValueError:
            Py4GW.Console.Log(PRIORITY_TARGET_MODULE_NAME, f"Invalid model ID: {model_id}", Py4GW.Console.MessageType.Error)
            return False
    
    def clear_model_ids(self, character_name=None):
        """Clear the priority targets list for a specific character"""
        if character_name is None:
            character_name = self.get_character_name()
            
        # Ensure the character exists in our dictionaries
        if character_name not in self.character_targets:
            self.character_targets[character_name] = []
        else:
            self.character_targets[character_name] = []
            
        self._save_to_file()
    
    def get_model_ids(self, character_name=None):
        """Get the priority targets list for a specific character"""
        if character_name is None:
            character_name = self.get_character_name()
            
        # Ensure the character exists in our dictionaries
        if character_name not in self.character_targets:
            self.character_targets[character_name] = []
            
        return self.character_targets.get(character_name, [])
    
    def is_enabled(self, character_name=None):
        """Check if priority targeting is enabled for a specific character"""
        if character_name is None:
            character_name = self.get_character_name()
            
        # Ensure the character exists in our dictionary
        if character_name not in self.character_enabled:
            self.character_enabled[character_name] = True
            
        return self.character_enabled.get(character_name, True)
    
    def set_enabled(self, enabled, character_name=None):
        """Enable or disable priority targeting for a specific character."""
        if character_name is None:
            character_name = self.get_character_name()
            
        # Ensure the character exists in our dictionaries
        if character_name not in self.character_enabled:
            self.character_enabled[character_name] = True
            
        self.character_enabled[character_name] = bool(enabled)
        self._save_to_file()
    
    def is_priority_target(self, agent_id):
        """Check if an agent is a priority target for the current character."""
        character_name = self.get_character_name()
        
        # Check if priority targeting is enabled for this character
        if not self.is_enabled(character_name) or not agent_id:
            return False
        
        # Ensure the character exists in our dictionary
        if character_name not in self.character_targets:
            self.character_targets[character_name] = []
        
        try:
            agent_instance = Agent.agent_instance(agent_id)
            model_id = agent_instance.living_agent.player_number
            return model_id in self.character_targets.get(character_name, [])
        except Exception as e:
            Py4GW.Console.Log(PRIORITY_TARGET_MODULE_NAME, f"Error checking priority target: {str(e)}", Py4GW.Console.MessageType.Error)
            return False
    
    def find_nearest_priority_target(self, distance=Range.Earshot.value):
        """Find the nearest priority target within the given distance for the current character."""
        try:
            character_name = self.get_character_name()
            
            # Check if priority targeting is enabled for this character
            if not self.is_enabled(character_name):
                return 0
            
            # Ensure the character exists in our dictionary
            if character_name not in self.character_targets:
                self.character_targets[character_name] = []
                
            # If no priority targets for this character, return 0
            if not self.character_targets.get(character_name, []):
                return 0
            
            enemy_array = AgentArray.GetEnemyArray()
            enemy_array = AgentArray.Filter.ByDistance(enemy_array, Player.GetXY(), distance)
            enemy_array = AgentArray.Filter.ByCondition(enemy_array, lambda agent_id: Agent.IsAlive(agent_id))
            
            for agent_id in enemy_array:
                if self.is_priority_target(agent_id):
                    return agent_id
            
            return 0
        except Exception as e:
            Py4GW.Console.Log(PRIORITY_TARGET_MODULE_NAME, f"Error finding priority target: {str(e)}", Py4GW.Console.MessageType.Error)
            Py4GW.Console.Log(PRIORITY_TARGET_MODULE_NAME, f"Stack trace: {traceback.format_exc()}", Py4GW.Console.MessageType.Error)
            return 0