import math
from typing import Callable

from Py4GWCoreLib.GlobalCache import GLOBAL_CACHE
from Py4GWCoreLib.GlobalCache.SharedMemory import AccountData
from Py4GWCoreLib.ImGui_src.IconsFontAwesome5 import IconsFontAwesome5
from Py4GWCoreLib.Player import Player
from Py4GWCoreLib.Map import Map
from Py4GWCoreLib.enums_src.Multiboxing_enums import SharedCommandType
from Py4GWCoreLib.py4gwcorelib_src.Console import ConsoleLog

class Command:
    '''
    Represents a command that can be executed and assigned to the HeroAI command system
    Attributes:
        name (str): The name of the command.
        icon (str): The icon associated with the command.
        command_function (Callable[[list[AccountData]], None] | None): The function to execute the command.
        tooltip (str): The tooltip text for the command.
        description (str): A detailed description of the command.
        map_types (list[str]): The types of maps where the command is applicable.
        
    Methods:
        is_separator() -> bool: Checks if the command is empty.
        __call__(accounts: list[AccountData]): Executes the command function with the provided accounts.
    '''
    def __init__(self, name: str, icon: str, command_function : Callable[[list[AccountData]], None] | None, tooltip : str = "", description: str = "", map_types: list[str] = ["Explorable", "Outpost"]) -> None:
        self.name = name
        self.icon = icon
        self.command_function = command_function
        self.tooltip = tooltip if tooltip else name
        self.description = description if description else self.tooltip
        self.map_types = map_types
        
    
    @property
    def is_separator(self) -> bool:
        return self.name == "Empty" and self.command_function is None
    
    def __call__(self, accounts: list[AccountData]):
        if self.command_function:
            self.command_function(accounts)

class HeroAICommands:
    '''
    Singleton class that manages HeroAI commands.
    Attributes:
        Commands (dict[str, Command]): A dictionary of command names to Command objects.
        Various predefined Command instances for different actions.
        
    Methods:
        add_command(command: Command) -> bool: Adds a new command to the system.
        remove_command(command: Command) -> bool: Removes a command from the system.
    '''
    __instance = None
    __initialized = False

    def __new__(cls, *args, **kwargs):
        if not cls.__instance:
            cls.__instance = super().__new__(cls)
        return cls.__instance
    
    def __init__(self):
        if self.__initialized:
            return
        
        self.__initialized = True

        self.Empty = Command("Empty", "", None)
        self.PixelStack = Command("Pixel Stack", IconsFontAwesome5.ICON_COMPRESS_ARROWS_ALT, self.__pixel_stack_command, "Pixel Stack Team")
        self.InteractWithTarget = Command("Interact With Target", IconsFontAwesome5.ICON_HAND_POINT_RIGHT, self.__interact_with_target_command, "Interact with current target")
        self.UnlockChest = Command("Unlock Chest", IconsFontAwesome5.ICON_KEY, self.__unlock_chest_command, "Unlock chest with current target")
        self.TakeDialogWithTarget = Command("Dialog With Target", IconsFontAwesome5.ICON_COMMENT_DOTS, self.__talk_and_dialog_with_target_command, "Take dialog with current target")
        self.OpenConsumables = Command("Open Consumables", IconsFontAwesome5.ICON_CANDY_CANE, self.__open_consumables_commands, "Open/Close Consumables Configuration Window")
        self.FlagHeroes = Command("Flag Heroes", IconsFontAwesome5.ICON_FLAG, self.__flag_heroes_command, "Flag all heroes", map_types=["Explorable"])
        self.UnflagHeroes = Command("Unflag Heroes", IconsFontAwesome5.ICON_CIRCLE_XMARK, self.__unflag_heroes_command, "Unflag all heroes", map_types=["Explorable"])
        self.Resign = Command("Resign", IconsFontAwesome5.ICON_SKULL, self.__resign_command, "Resign all accounts", map_types=["Explorable"])
        self.DonateFaction = Command("Donate Faction", IconsFontAwesome5.ICON_DONATE, self.__donate_faction_command, "Donate faction to guild")
        self.PickUpLoot = Command("Pick up loot", IconsFontAwesome5.ICON_COINS, self.__pick_up_loot_command, "Pick up loot from ground")
        self.CombatPrep = Command("Prepare for Combat", IconsFontAwesome5.ICON_SHIELD_ALT, self.__combat_prep_command, "Use Combat Preparations", map_types=["Explorable"])
        self.DisbandParty = Command("Disband Party", IconsFontAwesome5.ICON_SIGN_OUT_ALT, self.__leave_party_command, "Make all heroes leave party", map_types=["Outpost"])
        self.FormParty = Command("Form Party", IconsFontAwesome5.ICON_USERS, self.__invite_all_command, "Invite all heroes to party", map_types=["Outpost"])
        self.LeavePartyAndTravelGH = Command("Leave & Travel to GH", IconsFontAwesome5.ICON_HOME, self.__leave_party_and_travel_gh_command, "Leave party and travel to Guild Hall")
        
        self.__commands = [
            self.Empty,
            self.PixelStack,
            self.UnlockChest,
            self.InteractWithTarget,
            self.TakeDialogWithTarget,
            self.OpenConsumables,
            self.FlagHeroes,
            self.UnflagHeroes,
            self.Resign,
            self.DonateFaction,
            self.PickUpLoot,
            self.CombatPrep,
            self.DisbandParty,
            self.FormParty,
            self.LeavePartyAndTravelGH,
        ]
    
    @property
    def Commands(self) -> dict[str, Command]:   
        '''Returns a dictionary of command names to Command objects.'''   
        return {cmd.name: cmd for cmd in self.__commands}

    def add_command(self, command: Command):
        '''
        Adds a new command to the system.
        Args:
            command (Command): The command to add.
        '''
        if command not in self.__commands:
            self.__commands.append(command)
            return True
        
        return False
    
    def remove_command(self, command: Command):
        '''
        Removes a command from the system.
        Args:
            command (Command): The command to remove.
        '''
        if command in self.__commands:
            self.__commands.remove(command)
            return True
        
        return False
    
    def send_dialog(self, accounts: list[AccountData], dialog_option: int):
        sender_email = GLOBAL_CACHE.Player.GetAccountEmail()
        own_map_id = Map.GetMapID()
        own_region = Map.GetRegion()[0]
        own_district = Map.GetDistrict()
        own_language = Map.GetLanguage()[0]
        
        for account in accounts:
            same_map = own_map_id == account.MapID and own_region == account.MapRegion and own_district == account.MapDistrict and own_language == account.MapLanguage
            
            if same_map:
                GLOBAL_CACHE.ShMem.SendMessage(sender_email, account.AccountEmail, SharedCommandType.SendDialog, (dialog_option, 0, 0, 0))
                
    def __leave_party_command(self, accounts: list[AccountData]):
        sender_email = GLOBAL_CACHE.Player.GetAccountEmail()        
        
        for account in accounts:
            GLOBAL_CACHE.ShMem.SendMessage(sender_email, account.AccountEmail, SharedCommandType.LeaveParty, (0, 0, 0, 0))
    
    def __leave_party_and_travel_gh_command(self, accounts: list[AccountData]):
        sender_email = GLOBAL_CACHE.Player.GetAccountEmail()        
        
        for account in accounts:
            GLOBAL_CACHE.ShMem.SendMessage(sender_email, account.AccountEmail, SharedCommandType.LeaveParty, (0, 0, 0, 0))
            GLOBAL_CACHE.ShMem.SendMessage(sender_email, account.AccountEmail, SharedCommandType.TravelToGuildHall, (0, 0, 0, 0))

    def __combat_prep_command(self, accounts: list[AccountData]):
        sender_email = GLOBAL_CACHE.Player.GetAccountEmail()        
        
        for account in accounts:
            GLOBAL_CACHE.ShMem.SendMessage(sender_email, account.AccountEmail, SharedCommandType.UseSkillCombatPrep, (0, 0, 0, 0))
    
    def __pick_up_loot_command(self, accounts: list[AccountData]):
        sender_email = GLOBAL_CACHE.Player.GetAccountEmail()        
        
        for account in accounts:
            GLOBAL_CACHE.ShMem.SendMessage(sender_email, account.AccountEmail, SharedCommandType.PickUpLoot, (0, 0, 0, 0))
        
    def __donate_faction_command(self, accounts: list[AccountData]):
        sender_email = GLOBAL_CACHE.Player.GetAccountEmail()
        
        for account in accounts:
            GLOBAL_CACHE.ShMem.SendMessage(sender_email, account.AccountEmail, SharedCommandType.DonateToGuild, (0, 0, 0, 0))
    
    def __invite_all_command(self, accounts: list[AccountData]):
        sender_email = GLOBAL_CACHE.Player.GetAccountEmail()
        sender_id = GLOBAL_CACHE.Player.GetAgentID()
        
        def SetWaitingActions(delay_ms: int):
            delays = math.ceil(delay_ms // 50)
            for _ in range(delays):
                GLOBAL_CACHE._ActionQueueManager.AddAction("ACTION", lambda: None)  # Adding a no-op to ensure spacing between invites
        
        party_members = GLOBAL_CACHE.Party.GetPlayers()
        
        for account in accounts:
            if account.AccountEmail == sender_email:
                continue
            
            same_map = Map.GetMapID() == account.MapID and Map.GetRegion()[0] == account.MapRegion and Map.GetDistrict() == account.MapDistrict and Map.GetLanguage()[0] == account.MapLanguage
            
            if same_map and not GLOBAL_CACHE.Party.IsPartyMember(account.PlayerID):        
                char_name = account.CharacterName
                def send_invite(name = char_name):
                    ConsoleLog("HeroAI", f"Inviting {name} to party.")
                    Player.SendChatCommand("invite " + name)
                    
                GLOBAL_CACHE._ActionQueueManager.AddAction("ACTION", send_invite)
                SetWaitingActions(250)              
                
            GLOBAL_CACHE.ShMem.SendMessage(
                sender_email,
                account.AccountEmail,
                SharedCommandType.InviteToParty if same_map else SharedCommandType.TravelToMap,
                (sender_id, 0, 0, 0) if same_map else (
                    Map.GetMapID(),
                    Map.GetRegion()[0],
                    Map.GetDistrict(),
                    Map.GetLanguage()[0],
                )
            ) 
            
    def __resign_command(self, accounts: list[AccountData]):
        sender_email = GLOBAL_CACHE.Player.GetAccountEmail()
        
        for account in accounts:
            GLOBAL_CACHE.ShMem.SendMessage(sender_email, account.AccountEmail, SharedCommandType.Resign, (0, 0, 0, 0))
        
    def __pixel_stack_command(self, accounts: list[AccountData]):
        player_x, player_y = GLOBAL_CACHE.Player.GetXY()
        sender_email = GLOBAL_CACHE.Player.GetAccountEmail()
        
        for account in accounts:
            if account.AccountEmail == sender_email:
                continue
            
            GLOBAL_CACHE.ShMem.SendMessage(sender_email, account.AccountEmail, SharedCommandType.PixelStack, (player_x, player_y, 0, 0))
            
    def __unlock_chest_command(self, accounts: list[AccountData]):
        sender_email = GLOBAL_CACHE.Player.GetAccountEmail()        
        target_id = GLOBAL_CACHE.Player.GetTargetID()
        
        account_data = GLOBAL_CACHE.ShMem.GetAccountDataFromEmail(sender_email) 
        if account_data is None:
            return 
        
        party_id = account_data.PartyID
        map_id = account_data.MapID
        map_region = account_data.MapRegion
        map_district = account_data.MapDistrict
        map_language = account_data.MapLanguage

        def on_same_map_and_party(account : AccountData) -> bool:                    
            return (account.PartyID == party_id and
                    account.MapID == map_id and
                    account.MapRegion == map_region and
                    account.MapDistrict == map_district and
                    account.MapLanguage == map_language)
            
        all_accounts = [account for account in GLOBAL_CACHE.ShMem.GetAllAccountData() if on_same_map_and_party(account)]
        lowest_party_index_account = min(all_accounts, key=lambda account: account.PartyPosition, default=None)
        if lowest_party_index_account is None:
            return
        
        GLOBAL_CACHE.ShMem.SendMessage(sender_email, lowest_party_index_account.AccountEmail, SharedCommandType.OpenChest, (target_id, 1, 0, 0))
            
    def __interact_with_target_command(self, accounts: list[AccountData]):
        sender_email = GLOBAL_CACHE.Player.GetAccountEmail()        
        target_id = GLOBAL_CACHE.Player.GetTargetID()
        
        for account in accounts:
            GLOBAL_CACHE.ShMem.SendMessage(sender_email, account.AccountEmail, SharedCommandType.InteractWithTarget, (target_id, 0, 0, 0))
    
    def __talk_and_dialog_with_target_command(self, accounts: list[AccountData]):
        sender_email = GLOBAL_CACHE.Player.GetAccountEmail()        
        target_id = GLOBAL_CACHE.Player.GetTargetID()
        
        for account in accounts:
            GLOBAL_CACHE.ShMem.SendMessage(sender_email, account.AccountEmail, SharedCommandType.TakeDialogWithTarget, (target_id, 1, 0, 0))

    def __open_consumables_commands(self, accounts: list[AccountData]):
        from HeroAI import ui
        ui.show_configure_consumables_window()

    def __flag_heroes_command(self, accounts: list[AccountData]):
        from HeroAI import ui, windows
        windows.capture_flag_all = True
        windows.capture_hero_flag = True
        windows.capture_hero_index = 0
        windows.one_time_set_flag = False      
    
    def __unflag_heroes_command(self, accounts: list[AccountData]):
        from HeroAI import ui, windows
        pass
        #ClearFlags does not exists!?
        #windows.ClearFlags = True