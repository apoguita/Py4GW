import Py4GW
from Py4GWCoreLib import ConsoleLog, Map, Party, Player, Agent, Effects, SharedCommandType
from ctypes import Structure, c_uint, c_float, c_bool, c_wchar
from multiprocessing import shared_memory
from ctypes import sizeof
from datetime import datetime, timezone
from datetime import datetime, timezone
import time

SHMEM_MAX_EMAIL_LEN = 64
SHMEM_MAX_CHAR_LEN = 20
SHMEM_MAX_NUMBER_OF_BUFFS = 240
SHMEM_MAX_NUM_PLAYERS = 64
SMM_MODULE_NAME = "Py4GW - Shared Memory"
SHMEM_SHARED_MEMORY_FILE_NAME = "Py4GW_Shared_Mem"
SHMEM_ZERO_EPOCH = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0).timestamp()
SHMEM_SUBSCRIBE_TIMEOUT_MILISECONDS = 500 # milliseconds

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
               
        else:
            ConsoleLog(SMM_MODULE_NAME, f"Invalid player ID: {index}", Py4GW.Console.MessageType.Error)
       

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
        
    def SetPlayerData(self, account_email: str):
        """Set player data for the account with the given email."""      
        index = self.GetAccountSlot(account_email)
        if index != -1:
            player = self.GetStruct().AccountData[index]
            player.SlotNumber = index
            player.IsSlotActive = True
            player.IsAccount = True
            player.LastUpdated = self.GetBaseTimestamp()
            if Map.IsMapLoading(): 
                return
            if not Map.IsMapReady():
                return
            if not Party.IsPartyLoaded():
                return
            if Map.IsInCinematic():
                return
            
            player.AccountEmail = account_email 
            agent_id = Player.GetAgentID()
            login_number = Party.Players.GetLoginNumberByAgentID(agent_id)
            party_number = Party.Players.GetPartyNumberFromLoginNumber(login_number)
            map_region, _ = Map.GetRegion()
            playerx, playery, playerz = Agent.GetXYZ(agent_id)
            
            player.AccountName = Player.GetAccountName()
            player.CharacterName = Party.Players.GetPlayerNameByLoginNumber(login_number)
            
            player.IsHero = False
            player.IsPet = False
            player.IsNPC = False
            player.OwnerPlayerID = 0
            player.HeroID = 0
            player.MapID = Map.GetMapID()
            player.MapRegion = map_region
            player.MapDistrict = Map.GetDistrict()
            player.PlayerID = agent_id
            player.PlayerHP = Agent.GetHealth(agent_id)
            player.PlayerMaxHP = Agent.GetMaxHealth(agent_id)
            player.PlayerHealthRegen = Agent.GetHealthRegen(agent_id)
            player.PlayerEnergy = Agent.GetEnergy(agent_id)
            player.PlayerMaxEnergy = Agent.GetMaxEnergy(agent_id)
            player.PlayerEnergyRegen = Agent.GetEnergyRegen(agent_id)
            player.PlayerPosX = playerx
            player.PlayerPosY = playery
            player.PlayerPosZ = playerz
            player.PlayerFacingAngle = Agent.GetRotationAngle(agent_id)
            player.PlayerTargetID = Player.GetTargetID()
            player.PlayerLoginNumber = login_number
            player.PlayerIsTicked = Party.IsPlayerTicked(party_number)
            player.PartyID = Party.GetPartyID()
            player.PartyPosition = party_number
            player.PatyIsPartyLeader = Party.IsPartyLeader()
            buff_list = Effects.GetBuffs(agent_id)
            effect_list = Effects.GetEffects(agent_id)
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
            if Map.IsMapLoading(): 
                return
            if not Map.IsMapReady():
                return
            if not Party.IsPartyLoaded():
                return
            if Map.IsInCinematic():
                return
            
            hero.AccountEmail = Player.GetAccountEmail() 
            agent_id = hero_data.agent_id
            login_number = 0
            party_number = 0
            map_region, _ = Map.GetRegion()
            playerx, playery, playerz = Agent.GetXYZ(agent_id)
            
            hero.AccountName = Player.GetAccountName()
            hero.CharacterName = hero_data.hero_id.GetName()
            
            hero.IsHero = True
            hero.IsPet = False
            hero.IsNPC = False
            hero.OwnerPlayerID = Party.Players.GetAgentIDByLoginNumber(hero_data.owner_player_id)
            hero.HeroID = hero_data.hero_id.GetID()
            hero.MapID = Map.GetMapID()
            hero.MapRegion = map_region
            hero.MapDistrict = Map.GetDistrict()
            hero.PlayerID = agent_id
            hero.PlayerHP = Agent.GetHealth(agent_id)
            hero.PlayerMaxHP = Agent.GetMaxHealth(agent_id)
            hero.PlayerHealthRegen = Agent.GetHealthRegen(agent_id)
            hero.PlayerEnergy = Agent.GetEnergy(agent_id)
            hero.PlayerMaxEnergy = Agent.GetMaxEnergy(agent_id)
            hero.PlayerEnergyRegen = Agent.GetEnergyRegen(agent_id)
            hero.PlayerPosX = playerx
            hero.PlayerPosY = playery
            hero.PlayerPosZ = playerz
            hero.PlayerFacingAngle = Agent.GetRotationAngle(agent_id)
            hero.PlayerTargetID = 0
            hero.PlayerLoginNumber = 0
            hero.PlayerIsTicked = False
            hero.PartyID = Party.GetPartyID()
            hero.PartyPosition = 0
            hero.PatyIsPartyLeader = Party.IsPartyLeader()
            buff_list = Effects.GetBuffs(agent_id)
            effect_list = Effects.GetEffects(agent_id)
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
        pet_info = Party.Pets.GetPetInfo(Player.GetAgentID())
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
            
            if Map.IsMapLoading(): 
                return
            if not Map.IsMapReady():
                return
            if not Party.IsPartyLoaded():
                return
            if Map.IsInCinematic():
                return
            
            agent_id = pet_info.agent_id
            map_region, _ = Map.GetRegion()
            playerx, playery, playerz = Agent.GetXYZ(agent_id)
            
            pet.AccountEmail = Player.GetAccountEmail()
            pet.AccountName = Player.GetAccountName()
            pet.CharacterName = f"Agent {pet_info.owner_agent_id} Pet"
            pet.IsHero = False
            pet.IsNPC = False
            pet.MapID = Map.GetMapID()
            pet.MapRegion = map_region
            pet.MapDistrict = Map.GetDistrict()
            pet.PlayerID = agent_id
            pet.PartyID = Party.GetPartyID()
            pet.PartyPosition = 0
            pet.PatyIsPartyLeader = False  
            pet.PlayerLoginNumber = 0 
            if Map.IsOutpost():
                return
            pet.PlayerHP = Agent.GetHealth(agent_id)
            pet.PlayerMaxHP = Agent.GetMaxHealth(agent_id)
            pet.PlayerHealthRegen = Agent.GetHealthRegen(agent_id)
            pet.PlayerEnergy = Agent.GetEnergy(agent_id)
            pet.PlayerMaxEnergy = Agent.GetMaxEnergy(agent_id)
            pet.PlayerEnergyRegen = Agent.GetEnergyRegen(agent_id)
            pet.PlayerPosX = playerx
            pet.PlayerPosY = playery
            pet.PlayerPosZ = playerz
            pet.PlayerFacingAngle = Agent.GetRotationAngle(agent_id)
            pet.PlayerTargetID = pet_info.locked_target_id
            
            buff_list = Effects.GetBuffs(agent_id)
            effect_list = Effects.GetEffects(agent_id)
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
        owner_id = Player.GetAgentID()
        for hero_data in Party.GetHeroes():
            agent_from_login = Party.Players.GetAgentIDByLoginNumber(hero_data.owner_player_id)
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
    
    def PreviewNextMessage(self, account_email: str) -> tuple[int, SharedMessage | None]:
        """Preview the next message for the given account without marking it as running."""
        for index in range(self.max_num_players):
            message = self.GetStruct().SharedMessage[index]
            if message.ReceiverEmail == account_email and message.Active and not message.Running:
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

