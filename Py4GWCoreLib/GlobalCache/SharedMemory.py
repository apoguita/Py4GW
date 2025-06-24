import Py4GW
from Py4GWCoreLib import ConsoleLog, Map, Party, Player, Agent, Effects, SharedCommandType, ThrottledTimer
from ctypes import Structure, c_uint, c_float, c_bool, c_wchar
from multiprocessing import shared_memory
from ctypes import sizeof
from datetime import datetime, timezone
import time

SHMEM_MAX_EMAIL_LEN = 64
SHMEM_MAX_CHAR_LEN = 20
SHMEM_MAX_NUMBER_OF_BUFFS = 240
SHMEM_MAX_NUM_PLAYERS = 64
SMM_MODULE_NAME = "Py4GW - Shared Memory"
SHMEM_SHARED_MEMORY_FILE_NAME = "Py4GW_Shared_Mem"
SHMEM_ZERO_EPOCH = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0).timestamp()
SHMEM_SUBSCRIBE_TIMEOUT_MILISECONDS = 5000 # milliseconds

SHMEM_NUMBER_OF_SKILLS = 8

    
class AccountData(Structure):
    _pack_ = 1
    _fields_ = [
        ("SlotNumber", c_uint),  # Slot number for the player
        ("IsSlotActive", c_bool),
        ("AccountEmail", c_wchar*SHMEM_MAX_EMAIL_LEN),
        ("AccountName", c_wchar*SHMEM_MAX_CHAR_LEN),
        ("CharacterName", c_wchar*SHMEM_MAX_CHAR_LEN),
        ("IsAccount", c_bool),
        ("IsHero", c_bool),
        ("IsPet", c_bool),
        ("IsNPC", c_bool),
        ("OwnerPlayerID", c_uint),
        ("HeroID", c_uint),
        ("MapID", c_uint),
        ("MapRegion", c_uint),
        ("MapDistrict", c_uint),
        ("PlayerID", c_uint),
        ("PlayerHP", c_float),
        ("PlayerMaxHP", c_float),
        ("PlayerHealthRegen", c_float),
        ("PlayerEnergy", c_float),
        ("PlayerMaxEnergy", c_float),
        ("PlayerEnergyRegen", c_float),
        ("PlayerPosX", c_float),
        ("PlayerPosY", c_float),
        ("PlayerPosZ", c_float),
        ("PlayerFacingAngle", c_float),
        ("PlayerTargetID", c_uint),
        ("PlayerLoginNumber", c_uint),
        ("PlayerIsTicked", c_bool),
        ("PartyID", c_uint),
        ("PartyPosition", c_uint),
        ("PatyIsPartyLeader", c_bool),
        ("PlayerBuffs", c_uint * SHMEM_MAX_NUMBER_OF_BUFFS),  # Buff IDs
        ("LastUpdated", c_uint),
    ]
    
class SharedMessage(Structure):
    _pack_ = 1
    _fields_ = [
        ("SenderEmail", c_wchar * SHMEM_MAX_EMAIL_LEN),
        ("ReceiverEmail", c_wchar * SHMEM_MAX_EMAIL_LEN),
        ("Command", c_uint),
        ("Params", c_float * 4),
        ("Active", c_bool), 
        ("Running", c_bool),
        ("Timestamp", c_uint), 
    ]
    
class HeroAIOptionStruct(Structure):
    _pack_ = 1
    _fields_ = [
        ("Following", c_bool),
        ("Avoidance", c_bool), 
        ("Looting", c_bool), 
        ("Targeting", c_bool),
        ("Combat", c_bool),
        ("Skills", c_bool * SHMEM_NUMBER_OF_SKILLS),
        ("IsFlagged", c_bool),
        ("FlagPosX", c_float),
        ("FlagPosY", c_float),
        ("FlagFacingAngle", c_float),
    ] 
    
class AllAccounts(Structure):
    _pack_ = 1
    _fields_ = [
        ("AccountData", AccountData * SHMEM_MAX_NUM_PLAYERS),
        ("SharedMessage", SharedMessage * SHMEM_MAX_NUM_PLAYERS),  # Messages for each player
        ("HeroAIOptions", HeroAIOptionStruct * SHMEM_MAX_NUM_PLAYERS),  # Game options for HeroAI
    ]
        
class Py4GWSharedMemoryManager:
    _instance = None  # Singleton instance
    def __new__(cls, name=SHMEM_SHARED_MEMORY_FILE_NAME, num_players=SHMEM_MAX_NUM_PLAYERS):
        if cls._instance is None:
            cls._instance = super(Py4GWSharedMemoryManager, cls).__new__(cls)
            cls._instance._initialized = False  # Ensure __init__ runs only once
        return cls._instance
    
    def __init__(self, name=SHMEM_SHARED_MEMORY_FILE_NAME, max_num_players=SHMEM_MAX_NUM_PLAYERS):
        if not self._initialized:
            self.shm_name = name
            self.max_num_players = max_num_players
            self.size = sizeof(AllAccounts)
            self.map_instance = Map.map_instance()
            self.party_instance = None #Party.party_instance()
            self.player_instance = None #Player.player_instance()
            self.throttle_timer_150 = ThrottledTimer(150)
            self.throttle_timer_63 = ThrottledTimer(63) # 4 frames at 15 FPS
        
        # Create or attach shared memory
        try:
            self.shm = shared_memory.SharedMemory(name=self.shm_name)
            ConsoleLog(SMM_MODULE_NAME, "Attached to existing shared memory.", Py4GW.Console.MessageType.Info)
        except FileNotFoundError:
            self.shm = shared_memory.SharedMemory(name=self.shm_name, create=True, size=self.size)
            ConsoleLog(SMM_MODULE_NAME, "Shared memory area created.", Py4GW.Console.MessageType.Success)

        # Attach the shared memory structure
        #self.game_struct = AllAccounts.from_buffer(self.shm.buf)
        self.ResetAllData()  # Initialize all player data
        
        self._initialized = True
    
    def GetStruct(self) -> AllAccounts:
        return AllAccounts.from_buffer(self.shm.buf)
        
    def GetBaseTimestamp(self):
        # Return milliseconds since ZERO_EPOCH
        return int((time.time() - SHMEM_ZERO_EPOCH) * 1000)

        
    def ResetAllData(self):
        """Reset all player data in shared memory."""
        for i in range(self.max_num_players):
            self.ResetPlayerData(i)
            self.ResetHeroAIData(i)
        
    def ResetPlayerData(self, index):
        """Reset data for a specific player."""
        if 0 <= index < self.max_num_players:
            player = self.GetStruct().AccountData[index]
            player.IsSlotActive = False
            player.AccountEmail = ""
            player.AccountName = ""
            player.CharacterName = ""
            player.IsAccount = False
            player.IsHero = False
            player.IsPet = False
            player.IsNPC = False
            player.OwnerPlayerID = 0
            player.HeroID = 0
            player.MapID = 0
            player.MapRegion = 0
            player.MapDistrict = 0
            player.PlayerID = 0
            player.PlayerHP = 0.0
            player.PlayerMaxHP = 0.0
            player.PlayerHealthRegen = 0.0
            player.PlayerEnergy = 0.0
            player.PlayerMaxEnergy = 0.0
            player.PlayerEnergyRegen = 0.0  
            player.PlayerPosX = 0.0
            player.PlayerPosY = 0.0
            player.PlayerPosZ = 0.0
            player.PlayerFacingAngle = 0.0
            player.PlayerTargetID = 0
            player.PlayerLoginNumber = 0
            player.PlayerIsTicked = False
            player.PartyID = 0
            player.PartyPosition = 0
            player.PatyIsPartyLeader = False
            for j in range(SHMEM_MAX_NUMBER_OF_BUFFS):
                player.PlayerBuffs[j] = 0
            player.LastUpdated = self.GetBaseTimestamp()
            
    def ResetHeroAIData(self, index): 
            option = self.GetStruct().HeroAIOptions[index]
            option.Following = True
            option.Avoidance = True
            option.Looting = True
            option.Targeting = True
            option.Combat = True
            for i in range(SHMEM_NUMBER_OF_SKILLS):
                option.Skills[i] = True 
            option.IsFlaged = False
            option.FlagPosX = 0.0
            option.FlagPosY = 0.0
            option.FlagFacingAngle = 0.0
               

    def FindAccount(self, account_email: str) -> int:
        """Find the index of the account with the given email."""
        for i in range(self.max_num_players):
            player = self.GetStruct().AccountData[i]
            if not player.IsSlotActive:
                continue
            if self.GetStruct().AccountData[i].AccountEmail == account_email and player.IsAccount:
                return i
        return -1
    
    def FindHero(self, hero_data) -> int:
        """Find the index of the hero with the given ID."""
        for i in range(self.max_num_players):
            player = self.GetStruct().AccountData[i]
            if not player.IsSlotActive:
                continue
            if player.IsHero and player.HeroID == hero_data.hero_id.GetID() and player.OwnerPlayerID == Party.Players.GetAgentIDByLoginNumber(hero_data.owner_player_id):
                return i
        return -1
    
    def FindPet(self, pet_data) -> int:
        """Find the index of the pet with the given ID."""
        for i in range(self.max_num_players):
            player = self.GetStruct().AccountData[i]
            if not player.IsSlotActive:
                continue
            if player.IsPet and player.PlayerID == pet_data.agent_id and player.OwnerPlayerID == pet_data.owner_agent_id:
                return i
        return -1

    def FindEmptySlot(self) -> int:
        """Find the first empty slot in shared memory."""
        for i in range(self.max_num_players):
            if not self.GetStruct().AccountData[i].IsSlotActive:
                return i
        return -1
    
    def GetAccountSlot(self, account_email: str) -> int:
        """Get the slot index for the account with the given email."""
        index = self.FindAccount(account_email)
        if index == -1:
            index = self.FindEmptySlot()
            player = self.GetStruct().AccountData[index]
            player.IsSlotActive = True
            player.AccountEmail = account_email
            player.LastUpdated = self.GetBaseTimestamp()
        return index
    
    def GetHeroSlot(self, hero_data) -> int:
        """Get the slot index for the hero with the given owner ID and hero ID."""
        index = self.FindHero(hero_data)
        if index == -1:
            index = self.FindEmptySlot()
            hero = self.GetStruct().AccountData[index]
            hero.IsSlotActive = True
            hero.IsHero = True
            hero.OwnerPlayerID = Party.Players.GetAgentIDByLoginNumber(hero_data.owner_player_id)
            hero.HeroID = hero_data.hero_id.GetID()
            hero.LastUpdated = self.GetBaseTimestamp()
        return index
    
    def GetPetSlot(self, pet_data) -> int:
        """Get the slot index for the pet with the given owner ID and agent ID."""
        index = self.FindPet(pet_data)
        if index == -1:
            index = self.FindEmptySlot()
            pet = self.GetStruct().AccountData[index]
            pet.IsSlotActive = True
            pet.IsPet = True
            pet.OwnerPlayerID = pet_data.owner_agent_id
            pet.PlayerID = pet_data.agent_id
            pet.LastUpdated = self.GetBaseTimestamp()
        return index
    
    def _updatechache(self):
        """Update the shared memory cache."""
        self.map_instance.GetContext()
        if (self.map_instance.instance_type.GetName() == "Loading" or 
            self.map_instance.is_in_cinematic):
            if self.party_instance is not None:
                self.party_instance.GetContext()
            if self.player_instance is not None:
                self.player_instance.GetContext()
            
            return
            
        if self.party_instance is None:
            self.party_instance = Party.party_instance()
        if self.player_instance is None:
            self.player_instance = Player.player_instance()
            
        if self.throttle_timer_150.IsExpired():   
            self.throttle_timer_150.Reset()
            self.party_instance.GetContext()
            self.player_instance.GetContext()
        
        if self.throttle_timer_63.IsExpired():
            self.throttle_timer_63.Reset()
            self.player_instance.agent.GetContext()
        
     
    def GetLoginNumber(self):
        players = self.party_instance.players if self.party_instance else []
        agent_id = self.player_instance.id if self.player_instance else 0
        if len(players) > 0:
            for player in players:
                Pagent_id = self.party_instance.GetAgentIDByLoginNumber(player.login_number) if self.party_instance else 0
                if agent_id == Pagent_id:
                    return player.login_number
        return 0   

    def GetPartyNumber(self):
        login_number = self.GetLoginNumber()
        players = self.party_instance.players if self.party_instance else []

        for index, player in enumerate(players):
            if player.login_number == login_number:
                return index

        return -1
        
    def SetPlayerData(self, account_email: str):
        """Set player data for the account with the given email."""      
        index = self.GetAccountSlot(account_email)
        if index != -1:
            self._updatechache()
            player = self.GetStruct().AccountData[index]
            player.SlotNumber = index
            player.IsSlotActive = True
            player.IsAccount = True
            player.AccountEmail = account_email
            player.LastUpdated = self.GetBaseTimestamp()
            
            if self.map_instance.instance_type.GetName() == "Loading":
                return
            
            if (self.party_instance is None or 
                self.player_instance is None):
                return
            
            if not self.map_instance.is_map_ready:
                return
            if not self.party_instance.is_party_loaded:
                return
            if self.map_instance.is_in_cinematic:
                return
            
             
            agent_id = self.player_instance.id
            login_number = self.GetLoginNumber()
            party_number = self.GetPartyNumber()
            map_region = self.map_instance.server_region.ToInt()
            playerx, playery, playerz = self.player_instance.agent.x, self.player_instance.agent.y, self.player_instance.agent.z

            player.AccountName =self.player_instance.account_name
            player.CharacterName =self.party_instance.GetPlayerNameByLoginNumber(login_number)
            
            player.IsHero = False
            player.IsPet = False
            player.IsNPC = False
            player.OwnerPlayerID = 0
            player.HeroID = 0
            player.MapID = self.map_instance.map_id.ToInt()
            player.MapRegion = map_region
            player.MapDistrict = self.map_instance.district
            player.PlayerID = agent_id
            player.PlayerHP = self.player_instance.agent.living_agent.hp
            player.PlayerMaxHP = self.player_instance.agent.living_agent.max_hp
            player.PlayerHealthRegen = self.player_instance.agent.living_agent.hp_regen
            player.PlayerEnergy = self.player_instance.agent.living_agent.energy
            player.PlayerMaxEnergy = self.player_instance.agent.living_agent.max_energy
            player.PlayerEnergyRegen = self.player_instance.agent.living_agent.energy_regen
            player.PlayerPosX = playerx
            player.PlayerPosY = playery
            player.PlayerPosZ = playerz
            player.PlayerFacingAngle = self.player_instance.agent.rotation_angle
            player.PlayerTargetID = self.player_instance.target_id
            player.PlayerLoginNumber = login_number
            player.PlayerIsTicked = self.party_instance.GetIsPlayerTicked(party_number)
            player.PartyID = self.party_instance.party_id
            player.PartyPosition = party_number
            player.PatyIsPartyLeader = self.party_instance.is_party_leader
            effects_instance = Effects.get_instance(self.player_instance.id)
            buff_list = effects_instance.GetBuffs()
            effect_list = effects_instance.GetEffects()
            for j in range(SHMEM_MAX_NUMBER_OF_BUFFS):
                player.PlayerBuffs[j] = 0
                
            index = 0

            for buff in buff_list:
                if index >= SHMEM_MAX_NUMBER_OF_BUFFS:
                    break
                player.PlayerBuffs[index] = buff.skill_id
                index += 1

            for effect in effect_list:
                if index >= SHMEM_MAX_NUMBER_OF_BUFFS:
                    break
                player.PlayerBuffs[index] = effect.skill_id
                index += 1
            
        else:
            ConsoleLog(SMM_MODULE_NAME, "No empty slot available for new player data.", Py4GW.Console.MessageType.Error)
            
    def SetHeroData(self,hero_data):
        """Set player data for the account with the given email."""      
        index = self.GetHeroSlot(hero_data)
        if index != -1:
            hero = self.GetStruct().AccountData[index]
            hero.SlotNumber = index
            hero.IsSlotActive = True
            hero.IsAccount = False
            hero.LastUpdated = self.GetBaseTimestamp()
            
            if self.map_instance.instance_type.GetName() == "Loading":
                return
            
            if (self.party_instance is None or 
                self.player_instance is None):
                return
            
            if not self.map_instance.is_map_ready:
                return
            if not self.party_instance.is_party_loaded:
                return
            if self.map_instance.is_in_cinematic:
                return
            
            hero.AccountEmail = self.player_instance.account_email
            agent_id = hero_data.agent_id
            map_region = self.map_instance.region_type.ToInt()
            
            hero_agent_instance = Agent.agent_instance(agent_id)
            
            playerx, playery, playerz = hero_agent_instance.x, hero_agent_instance.y, hero_agent_instance.z
            
            hero.AccountName = self.player_instance.account_name
            hero.CharacterName = hero_data.hero_id.GetName()
            
            hero.IsHero = True
            hero.IsPet = False
            hero.IsNPC = False
            hero.OwnerPlayerID = self.party_instance.GetAgentIDByLoginNumber(hero_data.owner_player_id)
            hero.HeroID = hero_data.hero_id.GetID()
            hero.MapID = self.map_instance.map_id.ToInt()
            hero.MapRegion = map_region
            hero.MapDistrict = self.map_instance.district
            hero.PlayerID = agent_id
            hero.PlayerHP = hero_agent_instance.living_agent.hp
            hero.PlayerMaxHP = hero_agent_instance.living_agent.max_hp
            hero.PlayerHealthRegen = hero_agent_instance.living_agent.hp_regen
            hero.PlayerEnergy = hero_agent_instance.living_agent.energy
            hero.PlayerMaxEnergy = hero_agent_instance.living_agent.max_energy
            hero.PlayerEnergyRegen = hero_agent_instance.living_agent.energy_regen
            hero.PlayerPosX = playerx
            hero.PlayerPosY = playery
            hero.PlayerPosZ = playerz
            hero.PlayerFacingAngle = hero_agent_instance.rotation_angle
            hero.PlayerTargetID = 0
            hero.PlayerLoginNumber = 0
            hero.PlayerIsTicked = False
            hero.PartyID = self.party_instance.party_id
            hero.PartyPosition = 0
            hero.PatyIsPartyLeader = False
            effects_instance = Effects.get_instance(agent_id)
            buff_list = effects_instance.GetBuffs()
            effect_list = effects_instance.GetEffects()
            for j in range(SHMEM_MAX_NUMBER_OF_BUFFS):
                hero.PlayerBuffs[j] = 0
                
            index = 0

            for buff in buff_list:
                if index >= SHMEM_MAX_NUMBER_OF_BUFFS:
                    break
                hero.PlayerBuffs[index] = buff.skill_id
                index += 1

            for effect in effect_list:
                if index >= SHMEM_MAX_NUMBER_OF_BUFFS:
                    break
                hero.PlayerBuffs[index] = effect.skill_id
                index += 1
            
        else:
            ConsoleLog(SMM_MODULE_NAME, "No empty slot available for new hero data.", Py4GW.Console.MessageType.Error)
            
    def SetPetData(self):
        owner_agent_id = self.player_instance.id if self.player_instance else 0
        
        pet_info = self.party_instance.GetPetInfo(owner_agent_id) if self.party_instance else None
        if not pet_info:
            return
        
        index = self.GetPetSlot(pet_info)
        if index != -1:
            pet = self.GetStruct().AccountData[index]
            pet.SlotNumber = index
            pet.IsSlotActive = True
            pet.IsPet = True
            pet.OwnerPlayerID = pet_info.owner_agent_id
            pet.HeroID = 0
            pet.IsAccount = False
            pet.LastUpdated = self.GetBaseTimestamp()
            
            if self.map_instance.instance_type.GetName() == "Loading":
                return
            
            if (self.party_instance is None or 
                self.player_instance is None):
                return
            
            if not self.map_instance.is_map_ready:
                return
            if not self.party_instance.is_party_loaded:
                return
            if self.map_instance.is_in_cinematic:
                return
            
            agent_id = pet_info.agent_id
            agent_instance = Agent.agent_instance(agent_id)
            map_region = self.map_instance.region_type.ToInt()
            playerx, playery, playerz = agent_instance.x, agent_instance.y, agent_instance.z
            
            pet.AccountEmail = self.player_instance.account_email
            pet.AccountName = self.player_instance.account_name
            pet.CharacterName = f"Agent {pet_info.owner_agent_id} Pet"
            pet.IsHero = False
            pet.IsNPC = False
            pet.MapID = self.map_instance.map_id.ToInt()
            pet.MapRegion = map_region
            pet.MapDistrict = self.map_instance.district
            pet.PlayerID = agent_id
            pet.PartyID = self.party_instance.party_id
            pet.PartyPosition = 0
            pet.PatyIsPartyLeader = False  
            pet.PlayerLoginNumber = 0 
            if self.map_instance.instance_type.GetName() == "Outpost":
                return
            pet.PlayerHP = agent_instance.living_agent.hp
            pet.PlayerMaxHP = agent_instance.living_agent.max_hp
            pet.PlayerHealthRegen = agent_instance.living_agent.hp_regen
            pet.PlayerEnergy = agent_instance.living_agent.energy
            pet.PlayerMaxEnergy = agent_instance.living_agent.max_energy
            pet.PlayerEnergyRegen = agent_instance.living_agent.energy_regen
            pet.PlayerPosX = playerx
            pet.PlayerPosY = playery
            pet.PlayerPosZ = playerz
            pet.PlayerFacingAngle = agent_instance.rotation_angle
            pet.PlayerTargetID = pet_info.locked_target_id
            
            effects_instance = Effects.get_instance(self.player_instance.id)
            buff_list = effects_instance.GetBuffs()
            effect_list = effects_instance.GetEffects()
            for j in range(SHMEM_MAX_NUMBER_OF_BUFFS):
                pet.PlayerBuffs[j] = 0
                
            index = 0

            for buff in buff_list:
                if index >= SHMEM_MAX_NUMBER_OF_BUFFS:
                    break
                pet.PlayerBuffs[index] = buff.skill_id
                index += 1

            for effect in effect_list:
                if index >= SHMEM_MAX_NUMBER_OF_BUFFS:
                    break
                pet.PlayerBuffs[index] = effect.skill_id
                index += 1
            
        else:
            ConsoleLog(SMM_MODULE_NAME, "No empty slot available for new Pet data.", Py4GW.Console.MessageType.Error)
        
        
    def SetHeroesData(self):
        """Set data for all heroes in the given list."""
        owner_id = self.player_instance.id if self.player_instance else 0
        for hero_data in self.party_instance.heroes if self.party_instance else []:
            agent_from_login = self.party_instance.GetAgentIDByLoginNumber(hero_data.owner_player_id) if self.party_instance else 0
            if agent_from_login != owner_id:
                continue
            self.SetHeroData(hero_data)
            
    def GetAllActivePlayers(self) -> list[AccountData]:
        """Get all active players in shared memory."""
        players = []
        for i in range(self.max_num_players):
            player = self.GetStruct().AccountData[i]
            if player.IsSlotActive:
                players.append(player)
        return players
        
    def GetAllAccountData(self) -> list[AccountData]:
        """Get all player data, ordered by PartyID, PartyPosition, PlayerLoginNumber, CharacterName."""
        players = []
        for i in range(self.max_num_players):
            player = self.GetStruct().AccountData[i]
            if player.IsSlotActive and player.IsAccount:
                players.append(player)

        # Sort by PartyID, then PartyPosition, then PlayerLoginNumber, then CharacterName
        players.sort(key=lambda p: (
            p.MapID,
            p.MapRegion,
            p.MapDistrict,
            p.PartyID,
            p.PartyPosition,
            p.PlayerLoginNumber,
            p.CharacterName
        ))

        return players
    
    def GetAccountDataFromEmail(self, account_email: str) -> AccountData | None:
        """Get player data for the account with the given email."""
        index = self.FindAccount(account_email)
        if index != -1:
            return self.GetStruct().AccountData[index]
        else:
            ConsoleLog(SMM_MODULE_NAME, f"Account {account_email} not found.", Py4GW.Console.MessageType.Error)
            return None
     
    def GetAccountDataFromPartyNumber(self, party_number: int) -> AccountData | None:
        """Get player data for the account with the given party number."""
        for i in range(self.max_num_players):
            player = self.GetStruct().AccountData[i]
            if player.IsSlotActive and player.PartyPosition == party_number:
                return player
        ConsoleLog(SMM_MODULE_NAME, f"Party number {party_number} not found.", Py4GW.Console.MessageType.Error)
        return None
    
    def HasEffect(self, account_email: str, effect_id: int) -> bool:
        """Check if the account with the given email has the specified effect."""
        if effect_id == 0:
            return False
        
        player = self.GetAccountDataFromEmail(account_email)
        if player:
            for buff in player.PlayerBuffs:
                if buff == effect_id:
                    return True
        return False
        
    def GetHeroAIOptions(self, account_email: str) -> HeroAIOptionStruct | None:
        """Get HeroAI options for the account with the given email."""
        index = self.FindAccount(account_email)
        if index != -1:
            return self.GetStruct().HeroAIOptions[index]
        else:
            ConsoleLog(SMM_MODULE_NAME, f"Account {account_email} not found.", Py4GW.Console.MessageType.Error)
            return None
        
    def GetGerHeroAIOptionsByPartyNumber(self, party_number: int) -> HeroAIOptionStruct | None:
        """Get HeroAI options for the account with the given party number."""
        for i in range(self.max_num_players):
            player = self.GetStruct().AccountData[i]
            if player.IsSlotActive and player.PartyPosition == party_number:
                return self.GetStruct().HeroAIOptions[i]
        return None    
        
        
    def SetHeroAIOptions(self, account_email: str, options: HeroAIOptionStruct):
        """Set HeroAI options for the account with the given email."""
        index = self.FindAccount(account_email)
        if index != -1:
            self.GetStruct().HeroAIOptions[index] = options
        else:
            ConsoleLog(SMM_MODULE_NAME, f"Account {account_email} not found.", Py4GW.Console.MessageType.Error)
    
    def SetHeroAIProperty(self, account_email: str, property_name: str, value):
        """Set a specific HeroAI property for the account with the given email."""
        index = self.FindAccount(account_email)
        if index != -1:
            options = self.GetStruct().HeroAIOptions[index]
            
            if property_name.startswith("Skill_"):
                skill_index = int(property_name.split("_")[1])
                if 0 <= skill_index < SHMEM_NUMBER_OF_SKILLS:
                    options.Skills[skill_index] = value
                else:
                    ConsoleLog(SMM_MODULE_NAME, f"Invalid skill index: {skill_index}.", Py4GW.Console.MessageType.Error)
                return
            
            if hasattr(options, property_name):
                setattr(options, property_name, value)
            else:
                ConsoleLog(SMM_MODULE_NAME, f"Property {property_name} does not exist in HeroAIOptions.", Py4GW.Console.MessageType.Error)
        else:
            ConsoleLog(SMM_MODULE_NAME, f"Account {account_email} not found.", Py4GW.Console.MessageType.Error)
    
    def GetMapsFromPlayers(self):
        """Get a list of unique maps from all active players."""
        maps = set()
        for i in range(self.max_num_players):
            player = self.GetStruct().AccountData[i]
            if player.IsSlotActive and player.IsAccount:
                maps.add((player.MapID, player.MapRegion, player.MapDistrict))
        return list(maps)
    
    def GetPartiesFromMaps(self, map_id: int, map_region: int, map_district: int):
        """
        Get a list of unique PartyIDs for players in the specified map/region/district.
        """
        parties = set()
        for i in range(self.max_num_players):
            player = self.GetStruct().AccountData[i]
            if (player.IsSlotActive and player.IsAccount and
                player.MapID == map_id and
                player.MapRegion == map_region and
                player.MapDistrict == map_district):
                parties.add(player.PartyID)
        return list(parties)

    
    def GetPlayersFromParty(self, party_id: int, map_id: int, map_region: int, map_district: int):
        """Get a list of players in a specific party on a specific map."""
        players = []
        for i in range(self.max_num_players):
            player = self.GetStruct().AccountData[i]
            if (player.IsSlotActive and player.IsAccount and
                player.MapID == map_id and
                player.MapRegion == map_region and
                player.MapDistrict == map_district and
                player.PartyID == party_id):
                players.append(player)
        return players
    
    def GetHeroesFromPlayers(self, owner_player_id: int):
        """Get a list of heroes owned by the specified player."""
        heroes = []
        for i in range(self.max_num_players):
            player = self.GetStruct().AccountData[i]
            if (player.IsSlotActive and player.IsHero and
                player.OwnerPlayerID == owner_player_id):
                heroes.append(player)
        return heroes
    
    def GetPetsFromPlayers(self, owner_agent_id: int):
        """Get a list of pets owned by the specified player."""
        pets = []
        for i in range(self.max_num_players):
            player = self.GetStruct().AccountData[i]
            if (player.IsSlotActive and player.IsPet and
                player.OwnerPlayerID == owner_agent_id):
                pets.append(player)
        return pets
    
    def UpdateTimeouts(self):
        current_time = self.GetBaseTimestamp()

        for index in range(self.max_num_players):
            player = self.GetStruct().AccountData[index]

            if player.IsSlotActive:
                delta = current_time - player.LastUpdated
                if delta > SHMEM_SUBSCRIBE_TIMEOUT_MILISECONDS:
                    #ConsoleLog(SMM_MODULE_NAME, f"Player {player.AccountEmail} has timed out after {delta} ms.", Py4GW.Console.MessageType.Warning)
                    self.ResetPlayerData(index)
                    
    def SendMessage(self, sender_email: str, receiver_email: str, command: SharedCommandType, params: tuple = (0.0, 0.0, 0.0, 0.0)):
        """Send a message to another player."""
        index = self.FindAccount(receiver_email)
        if index == -1:
            ConsoleLog(SMM_MODULE_NAME, f"Receiver account {receiver_email} not found.", Py4GW.Console.MessageType.Error)
            return
        
        for i in range(self.max_num_players):
            message = self.GetStruct().SharedMessage[i]
            if message.Active:
                continue  # Find the first unfinished message slot
            
            message.SenderEmail = sender_email
            message.ReceiverEmail = receiver_email
            message.Command = command.value
            message.Params = (c_float * 4)(*params)
            message.Active = True
            message.Running = False
            message.Timestamp = self.GetBaseTimestamp()
            return
     
    def GetNextMessage(self, account_email: str) -> tuple[int, SharedMessage | None]:
        """Read the next message for the given account."""
        for index in range(self.max_num_players):
            message = self.GetStruct().SharedMessage[index]
            if message.ReceiverEmail == account_email and message.Active and not message.Running:
                return index, message
        return -1, None  # Return an empty message if no messages are found
    
    def PreviewNextMessage(self, account_email: str, include_running: bool = True) -> tuple[int, SharedMessage | None]:
        """Preview the next message for the given account.
        If include_running is True, will also return a running message."""
        for index in range(self.max_num_players):
            message = self.GetStruct().SharedMessage[index]
            if message.ReceiverEmail != account_email or not message.Active:
                continue
            if not message.Running or include_running:
                return index, message
        return -1, None

    
    def MarkMessageAsRunning(self, account_email: str, message_index: int):
        """Mark a specific message as running."""
        if 0 <= message_index < self.max_num_players:
            message = self.GetStruct().SharedMessage[message_index]
            if message.ReceiverEmail == account_email:
                message.Running = True
                message.Active = True
                message.Timestamp = self.GetBaseTimestamp()
            else:
                ConsoleLog(SMM_MODULE_NAME, f"Message at index {message_index} does not belong to {account_email}.", Py4GW.Console.MessageType.Error)
        else:
            ConsoleLog(SMM_MODULE_NAME, f"Invalid message index: {message_index}.", Py4GW.Console.MessageType.Error)
            
    def MarkMessageAsFinished(self, account_email: str, message_index: int):
        """Mark a specific message as finished."""
        if 0 <= message_index < self.max_num_players:
            message = self.GetStruct().SharedMessage[message_index]
            if message.ReceiverEmail == account_email:
                message.SenderEmail = ""
                message.ReceiverEmail = ""
                message.Command = SharedCommandType.NoCommand
                message.Params = (c_float * 4)(0.0, 0.0, 0.0, 0.0)
                message.Timestamp = self.GetBaseTimestamp()
                message.Running = False
                message.Active = False
            else:
                ConsoleLog(SMM_MODULE_NAME, f"Message at index {message_index} does not belong to {account_email}.", Py4GW.Console.MessageType.Error)
        else:
            ConsoleLog(SMM_MODULE_NAME, f"Invalid message index: {message_index}.", Py4GW.Console.MessageType.Error)
            
    def GetAllMessages(self) -> list[tuple[int, SharedMessage]]:
        """Get all messages in shared memory with their index."""
        messages = []
        for index in range(self.max_num_players):
            message = self.GetStruct().SharedMessage[index]
            if message.Active:
                messages.append((index, message))  # Add index and message
        return messages

