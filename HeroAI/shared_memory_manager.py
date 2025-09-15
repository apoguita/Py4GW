import Py4GW
from Py4GWCoreLib import GLOBAL_CACHE

from multiprocessing import shared_memory, Lock
from ctypes import sizeof
import time

from .constants import (
    SMM_MODULE_NAME,
    MAX_NUM_PLAYERS,
    NUMBER_OF_SKILLS,
    SHARED_MEMORY_FILE_NAME,
    LOCK_MUTEX_TIMEOUT,
    SUBSCRIBE_TIMEOUT_SECONDS,
    MAX_NUMBER_OF_BUFFS,
)

from .types import (
    GameStruct,
)

def get_base_timestamp():
    return int((time.time() % 3600) * 1000)



class SharedMemoryManager:
    global SMM_MODULE_NAME, MAX_NUM_PLAYERS, SHARED_MEMORY_FILE_NAME,LOCK_MUTEX_TIMEOUT, SUBSCRIBE_TIMEOUT_SECONDS    
    
    _instance = None  # Singleton instance
    def __new__(cls, name=SHARED_MEMORY_FILE_NAME, num_players=MAX_NUM_PLAYERS):
        if cls._instance is None:
            cls._instance = super(SharedMemoryManager, cls).__new__(cls)
            cls._instance._initialized = False  # Ensure __init__ runs only once
        return cls._instance
          
    def __init__(self, name=SHARED_MEMORY_FILE_NAME, num_players=MAX_NUM_PLAYERS):
        if not self._initialized:
            self.shm_name = name
            self.num_players = num_players
            self.size = sizeof(GameStruct)

            # Create or attach shared memory
            try:
                self.shm = shared_memory.SharedMemory(name=self.shm_name)
                Py4GW.Console.Log(SMM_MODULE_NAME, "Attached to existing shared memory.", Py4GW.Console.MessageType.Info)
            except FileNotFoundError:
                self.shm = shared_memory.SharedMemory(name=self.shm_name, create=True, size=self.size)
                Py4GW.Console.Log(SMM_MODULE_NAME, "Shared memory area created.", Py4GW.Console.MessageType.Info)

            # Attach the shared memory structure
            self.game_struct = GameStruct.from_buffer(self.shm.buf)

            # Initialize default values
            for i in range(self.num_players):
                self.reset_candidate(i)
                self.reset_player(i)
                self.reset_game_option(i)
            self.reset_party_buffs()
            
            self._initialized = True

    # ---------------------
    # Candidate Management
    # ---------------------
    def reset_candidate(self, index):
        """Reset candidate data."""
        candidate = self.game_struct.Candidates[index]
        candidate.PlayerID = 0
        candidate.MapID = 0
        candidate.MapRegion = 0
        candidate.MapDistrict = 0
        candidate.InvitedBy = 0
        candidate.SummonedBy = 0
        candidate.LastUpdated = 0

    def set_candidate(self, index, candidate_data):
        """Set a candidate structure."""
        try:
            if index < 0 or index >= self.num_players:
                raise IndexError("Invalid candidate index.")

            candidate = self.game_struct.Candidates[index]
            candidate.PlayerID = candidate_data.PlayerID
            candidate.MapID = candidate_data.MapID
            candidate.MapRegion = candidate_data.MapRegion
            candidate.MapDistrict = candidate_data.MapDistrict
            candidate.InvitedBy = candidate_data.InvitedBy
            candidate.SummonedBy = candidate_data.SummonedBy
            candidate.LastUpdated = get_base_timestamp()

        except Exception as e:
            Py4GW.Console.Log(SMM_MODULE_NAME, f"Failed to set candidate {index}: {e}", Py4GW.Console.MessageType.Error)

    def get_candidate(self, index):
        """Get a candidate structure and timeout check."""
        try:
            if index < 0 or index >= self.num_players:
                raise IndexError("Invalid candidate index.")

            candidate = self.game_struct.Candidates[index]
            # Timeout check
            current_offset = get_base_timestamp()
            if (current_offset - candidate.LastUpdated) > SUBSCRIBE_TIMEOUT_SECONDS:
                self.reset_candidate(index)

            # Return candidate data
            return {
                "PlayerID": candidate.PlayerID,
                "MapID": candidate.MapID,
                "MapRegion": candidate.MapRegion,
                "MapDistrict": candidate.MapDistrict,
                "InvitedBy": candidate.InvitedBy,
                "SummonedBy": candidate.SummonedBy,
                "LastUpdated": candidate.LastUpdated,
            }

        except Exception as e:
            Py4GW.Console.Log(SMM_MODULE_NAME, f"Failed to get candidate {index}: {e}", Py4GW.Console.MessageType.Error)
            return None

    def register_candidate(self, candidate_data):
        """Register a candidate in the first available slot."""
        for i in range(self.num_players):
            existing_candidate = self.get_candidate(i)
            if (existing_candidate and
                existing_candidate["PlayerID"] == candidate_data.PlayerID and 
                existing_candidate["MapID"] == candidate_data.MapID and
                existing_candidate["MapRegion"] == candidate_data.MapRegion and
                existing_candidate["MapDistrict"] == candidate_data.MapDistrict):
                candidate_data.InvitedBy = existing_candidate["InvitedBy"]
                candidate_data.SummonedBy = existing_candidate["SummonedBy"]
                candidate_data.LastUpdated = get_base_timestamp()
                self.set_candidate(i, candidate_data)
                return True

        for i in range(self.num_players):
            candidate = self.get_candidate(i)
            if candidate and candidate.get("PlayerID") == 0:
                self.set_candidate(i, candidate_data)
                return True
        return False

    # ---------------------
    # Player Management
    # ---------------------
    def reset_player(self, index):
        """Reset player data."""
        player = self.game_struct.Players[index]
        player.PlayerID = 0
        player.Energy_Regen = 0.0
        player.Energy = 0.0
        player.IsActive = False
        player.IsHero = False
        player.IsFlagged = False
        player.FlagPosX = 0.0
        player.FlagPosY = 0.0
        player.FollowAngle = -1.0
        player.LastUpdated = 0


    def set_player(self, index, player_data):
        """Write player data."""
        try:
            if index < 0 or index >= self.num_players:
                raise IndexError("Invalid player index.")

            player = self.game_struct.Players[index]
            player.PlayerID = player_data.PlayerID
            player.Energy_Regen = player_data.Energy_Regen
            player.Energy = player_data.Energy
            player.IsActive = player_data.IsActive
            player.IsHero = player_data.IsHero
            player.IsFlagged = player_data.IsFlagged
            player.FlagPosX = player_data.FlagPosX
            player.FlagPosY = player_data.FlagPosY
            player.FollowAngle = player_data.FollowAngle
            player.LastUpdated = get_base_timestamp()


        except Exception as e:
            Py4GW.Console.Log(SMM_MODULE_NAME, f"Write failed for player {index}: {e}", Py4GW.Console.MessageType.Error)

    def set_player_property(self, player_index, property_name, value):
        """Write a single property of a player."""
        try:
            # Validate index
            if player_index < 0 or player_index >= self.num_players:
                raise IndexError("Invalid player index.")


            player = self.game_struct.Players[player_index]

            # Handle core properties
            if property_name == "PlayerID":
                player.PlayerID = value
            elif property_name == "Energy_Regen":
                player.Energy_Regen = value
            elif property_name == "Energy":
                player.Energy = value
            elif property_name == "IsActive":
                player.IsActive = value
            elif property_name == "IsHero":
                player.IsHero = value
            elif property_name == "IsFlagged":
                player.IsFlagged = value
            elif property_name == "FlagPosX":
                player.FlagPosX = value
            elif property_name == "FlagPosY":
                player.FlagPosY = value
            elif property_name == "FollowAngle":
                player.FollowAngle = value
            elif property_name == "LastUpdated":
                player.LastUpdated = value
            else:
                raise KeyError(f"Invalid property name: {property_name}")

            # Update timestamp after modification
            player.LastUpdated = get_base_timestamp()

        except Exception as e:
            Py4GW.Console.Log(SMM_MODULE_NAME, f"Write failed for property {property_name} at index {player_index}: {e}", Py4GW.Console.MessageType.Error)

    def get_player(self, index):
        """Read player data and timeout check."""
        try:

            player = self.game_struct.Players[index]
                
            # Timeout check
            current_offset = get_base_timestamp()
            if (current_offset - player.LastUpdated) > SUBSCRIBE_TIMEOUT_SECONDS:
                self.reset_player(index)

            data = {
                "PlayerID": player.PlayerID,
                "Energy_Regen": player.Energy_Regen,
                "Energy": player.Energy,
                "IsActive": player.IsActive,
                "IsHero": player.IsHero,
                "IsFlagged": player.IsFlagged,
                "FlagPosX": player.FlagPosX,
                "FlagPosY": player.FlagPosY,
                "FollowAngle": player.FollowAngle,
                "LastUpdated": player.LastUpdated,
            }

            return data
        except Exception as e:
            Py4GW.Console.Log(SMM_MODULE_NAME, f"Read failed for player {index}: {e}", Py4GW.Console.MessageType.Error)
            return None


    # ---------------------
    # Game Option Management
    # ---------------------

    def reset_game_option(self, index):
        """Reset game options for a specific player."""
        game_option = self.game_struct.GameOptions[index]
        game_option.Following = True
        game_option.Avoidance = True
        game_option.Looting = True
        game_option.Targeting = True
        game_option.Combat = True
        game_option.WindowVisible = True

        for i in range(NUMBER_OF_SKILLS):
            game_option.Skills[i].Active = True


    def set_game_option(self, index, game_option_data):
        """Write game option data."""
        try:
            if index < 0 or index >= self.num_players:
                raise IndexError("Invalid game option index.")

            game_option = self.game_struct.GameOptions[index]
            game_option.Following = game_option_data.Following
            game_option.Avoidance = game_option_data.Avoidance
            game_option.Looting = game_option_data.Looting
            game_option.Targeting = game_option_data.Targeting
            game_option.Combat = game_option_data.Combat
            game_option.WindowVisible = game_option_data.WindowVisible

            for i in range(NUMBER_OF_SKILLS):
                game_option.Skills[i].Active = game_option_data.Skills[i].Active


        except Exception as e:
            Py4GW.Console.Log(SMM_MODULE_NAME, f"Write failed for game option {index}: {e}", Py4GW.Console.MessageType.Error)


    def get_game_option(self, index):
        """Read game option data and timeout check."""
        try:
            if index < 0 or index >= self.num_players:
                raise IndexError("Invalid game option index.")

            game_option = self.game_struct.GameOptions[index]
            # Collect data
            data = {
                "Following": game_option.Following,
                "Avoidance": game_option.Avoidance,
                "Looting": game_option.Looting,
                "Targeting": game_option.Targeting,
                "Combat": game_option.Combat,
                "WindowVisible": game_option.WindowVisible,
                "Skills": [skill.Active for skill in game_option.Skills],
            }

            return data

        except Exception as e:
            Py4GW.Console.Log(SMM_MODULE_NAME, f"Read failed for game option {index}: {e}", Py4GW.Console.MessageType.Error)
            return None

    def set_game_option_property(self, index, property_name, value):
        """Write a single property of the game option without locks."""
        try:
            if index < 0 or index >= self.num_players:
                raise IndexError("Invalid game option index.")

            # Access the game option
            game_option = self.game_struct.GameOptions[index]

            # Handle skill-specific properties
            if property_name.startswith("Skill_"):
                # Parse the skill index from the property name
                skill_index = int(property_name.split("_")[1]) - 1
                if not (0 <= skill_index < NUMBER_OF_SKILLS):
                    raise IndexError(f"Invalid skill index: {skill_index}")
                game_option.Skills[skill_index].Active = value
            # Handle generic properties
            elif hasattr(game_option, property_name):
                setattr(game_option, property_name, value)
            else:
                raise KeyError(f"Invalid property name: {property_name}")

        except Exception as e:
            Py4GW.Console.Log(SMM_MODULE_NAME, f"Write failed for property {property_name} at index {index}: {e}", Py4GW.Console.MessageType.Error)


    # ---------------------
    # Party Buffs Management
    # ---------------------
    def reset_party_buffs(self):
        """Reset all buffs for a specific player."""
        buff_index = 0
        try:
            for buff_index in range(MAX_NUMBER_OF_BUFFS):
                self.reset_buff(buff_index)

        except Exception as e:
            Py4GW.Console.Log(SMM_MODULE_NAME, f"Failed to reset buffs for player {buff_index}: {e}", Py4GW.Console.MessageType.Error)

    def reset_buff(self, index):
        """Reset a specific party buff."""
        try:

            buff = self.game_struct.PlayerBuffs[index]
            buff.PlayerID = 0
            buff.Buff_id = 0
            buff.LastUpdated = 0

        except Exception as e:
            Py4GW.Console.Log(SMM_MODULE_NAME, f"Failed to reset buff {index}: {e}", Py4GW.Console.MessageType.Error)

    def get_buff(self,agent_id, skill_id):
        """Retrieve a specific buff with timeout checks."""
        buff_index = 0
        try:

            for buff_index, buff in enumerate(self.game_struct.PlayerBuffs):
                if buff.PlayerID == agent_id and buff.Buff_id == skill_id:
                    current_offset = get_base_timestamp()
                    if current_offset - buff.LastUpdated > SUBSCRIBE_TIMEOUT_SECONDS:
                        self.reset_buff(buff_index)
                        return None
                    return {
                        "PlayerID": buff.PlayerID,
                        "Buff_id": buff.Buff_id,
                        "LastUpdated": buff.LastUpdated,
                    }

            return None

        except Exception as e:
            Py4GW.Console.Log(SMM_MODULE_NAME, f"Failed to retrieve buff {buff_index}: {e}", Py4GW.Console.MessageType.Error)
            return None
  
    def get_agent_buffs(self, agent_id):
        """Retrieve all buffs for a specific agent."""
        try:
            buff_list = []
            for buff_index, buff in enumerate(self.game_struct.PlayerBuffs):
                if buff.PlayerID == agent_id:
                    current_offset = get_base_timestamp()
                    if (current_offset - buff.LastUpdated) > SUBSCRIBE_TIMEOUT_SECONDS:
                        self.reset_buff(buff_index)
                    else:
                        buff_list.append(buff.Buff_id)
            return buff_list
        except Exception as e:
            Py4GW.Console.Log(
                SMM_MODULE_NAME, f"Failed to retrieve buffs for agent {agent_id}: {e}", Py4GW.Console.MessageType.Error)
            return []

    def set_buff(self, buff_data):
        """Set or update a party buff."""
        try:

            # Check for an existing buff with the same Buff_id and PlayerID
            for buff_index, buff in enumerate(self.game_struct.PlayerBuffs):
                if buff.Buff_id == buff_data["Buff_id"] and buff.PlayerID == buff_data["PlayerID"]:
                    buff.LastUpdated = buff_data["LastUpdated"]
                    return True

            # Reset expired buffs
            for buff_index, buff in enumerate(self.game_struct.PlayerBuffs):
                current_offset = get_base_timestamp()
                if current_offset - buff.LastUpdated > SUBSCRIBE_TIMEOUT_SECONDS:
                    self.reset_buff(buff_index)
                    # Use the reset slot for the new buff
                    buff.PlayerID = buff_data["PlayerID"]
                    buff.Buff_id = buff_data["Buff_id"]
                    buff.LastUpdated = buff_data["LastUpdated"]
                    return True

            # Find an empty slot for the new buff
            for buff_index, buff in enumerate(self.game_struct.PlayerBuffs):
                if buff.Buff_id == 0:
                    buff.PlayerID = buff_data["PlayerID"]
                    buff.Buff_id = buff_data["Buff_id"]
                    buff.LastUpdated = buff_data["LastUpdated"]
                    return True

            # No available slots
            Py4GW.Console.Log(SMM_MODULE_NAME, "No available slots for registering buff.", Py4GW.Console.MessageType.Warning)
            return False

        except Exception as e:
            Py4GW.Console.Log(SMM_MODULE_NAME, f"Failed to set buff: {e}", Py4GW.Console.MessageType.Error)
            return False

        
    def register_buffs(self, agent_id):
        """Register new buffs or update existing ones for the agent."""
        try:
            # Process buffs
            buff_list = GLOBAL_CACHE.Effects.GetBuffs(agent_id)
            for buff in buff_list:
                buff_data = {
                    "PlayerID": agent_id,
                    "Buff_id": buff.skill_id,  # Adjust according to the property name in the Buff object
                    "LastUpdated": get_base_timestamp(),
                    # Add other common properties if needed
                }
                self.set_buff(buff_data)

            # Process effects
            effect_list = GLOBAL_CACHE.Effects.GetEffects(agent_id)
            for effect in effect_list:
                buff_data = {
                    "PlayerID": agent_id,
                    "Buff_id": effect.skill_id,  # Adjust according to the property name in the Effect object
                    "LastUpdated": get_base_timestamp(),
                    # Add other common properties if needed
                }
                self.set_buff(buff_data)

        except Exception as e:
            Py4GW.Console.Log(
                SMM_MODULE_NAME, f"Failed to register buffs for agent {agent_id}: {e}", Py4GW.Console.MessageType.Error
            )

    def buff_exists(self, agent_id, skill_id):
        """Check if a specific buff exists for the agent."""
        try:
            buff = self.get_buff(agent_id,skill_id)
            if buff is not None and buff["PlayerID"] == agent_id:
                return True
            return False
        except Exception as e:
            Py4GW.Console.Log(
                SMM_MODULE_NAME, f"Failed to check buff existence: {e}", Py4GW.Console.MessageType.Error)
            return False
        
    def close(self):
        """Close this process's reference to shared memory."""
        self.shm.close()  

