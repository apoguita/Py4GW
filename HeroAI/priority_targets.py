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
            self.priority_model_ids = []
            self.is_enabled = True
            self.config_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), "Config", "priority_targets.ini")
            self._load_from_file()  # Load data from file
            self._initialized = True
    
    def _load_from_file(self):
        """Charge les ID de modèles prioritaires à partir du fichier INI."""
        try:
            if not os.path.exists(self.config_file):
                # Create the Config directory if it does not exist
                config_dir = os.path.dirname(self.config_file)
                if not os.path.exists(config_dir):
                    os.makedirs(config_dir)
                # Create an empty INI file with the basic structure
                self._save_to_file()
                return

            config = configparser.ConfigParser()
            config.read(self.config_file)
            
            if 'Settings' in config:
                self.is_enabled = config.getboolean('Settings', 'Enabled', fallback=True)
            
            if 'ModelIDs' in config:
                for key, value in config['ModelIDs'].items():
                    if key.startswith('id_'):
                        try:
                            model_id = int(value)
                            if model_id not in self.priority_model_ids:
                                self.priority_model_ids.append(model_id)
                        except ValueError:
                            Py4GW.Console.Log(PRIORITY_TARGET_MODULE_NAME, f"Invalid model ID in config file: {value}", Py4GW.Console.MessageType.Warning)
        
        except Exception as e:
            Py4GW.Console.Log(PRIORITY_TARGET_MODULE_NAME, f"Error loading priority targets from file: {str(e)}", Py4GW.Console.MessageType.Error)
            Py4GW.Console.Log(PRIORITY_TARGET_MODULE_NAME, f"Stack trace: {traceback.format_exc()}", Py4GW.Console.MessageType.Error)
    
    def _save_to_file(self):
        """Sauvegarde les ID de modèles prioritaires dans le fichier INI."""
        try:
            config = configparser.ConfigParser()
            
            # Settings section
            config['Settings'] = {
                'Enabled': str(self.is_enabled)
            }
            
            # Model IDs Section
            config['ModelIDs'] = {}
            for i, model_id in enumerate(self.priority_model_ids):
                config['ModelIDs'][f'id_{i}'] = str(model_id)
            
            # Create the directory if necessary
            config_dir = os.path.dirname(self.config_file)
            if not os.path.exists(config_dir):
                os.makedirs(config_dir)
            
            # Write to file
            with open(self.config_file, 'w') as f:
                config.write(f)
            
            Py4GW.Console.Log(PRIORITY_TARGET_MODULE_NAME, "Priority targets saved to file.", Py4GW.Console.MessageType.Info)
        
        except Exception as e:
            Py4GW.Console.Log(PRIORITY_TARGET_MODULE_NAME, f"Error saving priority targets to file: {str(e)}", Py4GW.Console.MessageType.Error)
            Py4GW.Console.Log(PRIORITY_TARGET_MODULE_NAME, f"Stack trace: {traceback.format_exc()}", Py4GW.Console.MessageType.Error)
    
    def add_model_id(self, model_id):
        """Add a model ID to the priority targets list if not already present."""
        try:
            # Convert to integer to ensure we have a valid model ID
            model_id = int(model_id)
            if model_id not in self.priority_model_ids:
                self.priority_model_ids.append(model_id)
                self._save_to_file()  # Save after modification
                return True
            return False
        except ValueError:
            Py4GW.Console.Log(PRIORITY_TARGET_MODULE_NAME, f"Invalid model ID: {model_id}", Py4GW.Console.MessageType.Error)
            return False
    
    def remove_model_id(self, model_id):
        """Remove a model ID from the priority targets list."""
        try:
            model_id = int(model_id)
            if model_id in self.priority_model_ids:
                self.priority_model_ids.remove(model_id)
                self._save_to_file()  # Save after modification
                return True
            return False
        except ValueError:
            Py4GW.Console.Log(PRIORITY_TARGET_MODULE_NAME, f"Invalid model ID: {model_id}", Py4GW.Console.MessageType.Error)
            return False
    
    def clear_model_ids(self):
        """Clear the priority targets list."""
        self.priority_model_ids = []
        self._save_to_file()  # Save after modification
    
    def get_model_ids(self):
        """Get the priority targets list."""
        return self.priority_model_ids
    
    def set_enabled(self, enabled):
        """Enable or disable priority targeting."""
        self.is_enabled = bool(enabled)
        self._save_to_file()  # Save after modification
    
    def is_priority_target(self, agent_id):
        """Check if an agent is a priority target."""
        if not self.is_enabled or not agent_id:
            return False
        
        try:
            agent_instance = Agent.agent_instance(agent_id)
            model_id = agent_instance.living_agent.player_number
            return model_id in self.priority_model_ids
        except Exception as e:
            Py4GW.Console.Log(PRIORITY_TARGET_MODULE_NAME, f"Error checking priority target: {str(e)}", Py4GW.Console.MessageType.Error)
            return False
    
    def find_nearest_priority_target(self, distance=Range.Earshot.value):
        """Find the nearest priority target within the given distance."""
        try:
            if not self.is_enabled or not self.priority_model_ids:
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