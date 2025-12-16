import math
from typing import Callable

from Py4GWCoreLib.GlobalCache import GLOBAL_CACHE
from Py4GWCoreLib.GlobalCache.SharedMemory import AccountData
from Py4GWCoreLib.ImGui_src.IconsFontAwesome5 import IconsFontAwesome5
from Py4GWCoreLib.Player import Player
from Py4GWCoreLib.enums_src.Multiboxing_enums import SharedCommandType
from Py4GWCoreLib.py4gwcorelib_src.Console import ConsoleLog

class Command:
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
    
    ## make this class executable like a function
    def __call__(self, accounts: list[AccountData]):
        if self.command_function:
            self.command_function(accounts)

class HeroAICommands:
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
        self.PixelStack = Command("Pixel Stack", IconsFontAwesome5.ICON_COMPRESS_ARROWS_ALT, self.pixel_stack_command, "Pixel Stack Team")
        self.InteractWithTarget = Command("Interact With Target", IconsFontAwesome5.ICON_HAND_POINT_RIGHT, self.interact_with_target_command, "Interact with current target")
        self.UnlockChest = Command("Unlock Chest", IconsFontAwesome5.ICON_KEY, self.unlock_chest_command, "Unlock chest with current target")
        self.TakeDialogWithTarget = Command("Dialog With Target", IconsFontAwesome5.ICON_COMMENT_DOTS, self.talk_and_dialog_with_target_command, "Take dialog with current target")
        self.OpenConsumables = Command("Open Consumables", IconsFontAwesome5.ICON_CANDY_CANE, self.open_consumables_commands, "Open/Close Consumables Configuration Window")
        self.FlagHeroes = Command("Flag Heroes", IconsFontAwesome5.ICON_FLAG, self.flag_heroes_command, "Flag all heroes", map_types=["Explorable"])
        self.UnflagHeroes = Command("Unflag Heroes", IconsFontAwesome5.ICON_CIRCLE_XMARK, self.unflag_heroes_command, "Unflag all heroes", map_types=["Explorable"])
        self.Resign = Command("Resign", IconsFontAwesome5.ICON_SKULL, self.resign_command, "Resign all accounts", map_types=["Explorable"])
        self.DonateFaction = Command("Donate Faction", IconsFontAwesome5.ICON_DONATE, self.donate_faction_command, "Donate faction to guild")
        self.GetStuck = Command("Get Stuck", IconsFontAwesome5.ICON_BUG, self.get_stuck_command, "Get stuck at a specific location")
        # self.GetBlessing = Command("Get Blessing", IconsFontAwesome5.ICON_PRAYING_HANDS, self.get_blessing_command, "Get Blessing from nearby shrine")
        self.PickUpLoot = Command("Pick up loot", IconsFontAwesome5.ICON_COINS, self.pick_up_loot_command, "Pick up loot from ground")
        self.CombatPrep = Command("Prepare for Combat", IconsFontAwesome5.ICON_SHIELD_ALT, self.combat_prep_command, "Use Combat Preparations", map_types=["Explorable"])
        self.DisbandParty = Command("Disband Party", IconsFontAwesome5.ICON_SIGN_OUT_ALT, self.leave_party_command, "Make all heroes leave party", map_types=["Outpost"])
        self.FormParty = Command("Form Party", IconsFontAwesome5.ICON_USERS, self.invite_all_command, "Invite all heroes to party", map_types=["Outpost"])
        
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
            # self.GetStuck,
            
            # self.GetBlessing,
            self.PickUpLoot,
            self.CombatPrep,
            self.DisbandParty,
            self.FormParty,
        ]
    
    @property
    def Commands(self) -> dict[str, Command]:      
        return {cmd.name: cmd for cmd in self.__commands}

    def add_command(self, command: Command):
        if command not in self.__commands:
            self.__commands.append(command)
            return True
        
        return False
    
    def remove_command(self, command: Command):
        if command in self.__commands:
            self.__commands.remove(command)
            return True
        
        return False
    
    def get_stuck_command(self, accounts: list[AccountData]):
        x,y = 8730, 7402
        GLOBAL_CACHE.ShMem.SendMessage(
            GLOBAL_CACHE.Player.GetAccountEmail(),
            GLOBAL_CACHE.Player.GetAccountEmail(),
            SharedCommandType.PixelStack,
            (x, y, 0, 0)
        )
        
        x,y = -1062, 1021
        GLOBAL_CACHE.ShMem.SendMessage(
            GLOBAL_CACHE.Player.GetAccountEmail(),
            GLOBAL_CACHE.Player.GetAccountEmail(),
            SharedCommandType.PixelStack,
            (x, y, 0, 0)
        )
    
    def leave_party_command(self, accounts: list[AccountData]):
        sender_email = GLOBAL_CACHE.Player.GetAccountEmail()        
        
        for account in accounts:
            GLOBAL_CACHE.ShMem.SendMessage(sender_email, account.AccountEmail, SharedCommandType.LeaveParty, (0, 0, 0, 0))
    
    def combat_prep_command(self, accounts: list[AccountData]):
        sender_email = GLOBAL_CACHE.Player.GetAccountEmail()        
        
        for account in accounts:
            GLOBAL_CACHE.ShMem.SendMessage(sender_email, account.AccountEmail, SharedCommandType.UseSkillCombatPrep, (0, 0, 0, 0))
    
    def pick_up_loot_command(self, accounts: list[AccountData]):
        sender_email = GLOBAL_CACHE.Player.GetAccountEmail()        
        
        for account in accounts:
            GLOBAL_CACHE.ShMem.SendMessage(sender_email, account.AccountEmail, SharedCommandType.PickUpLoot, (0, 0, 0, 0))
    
    def get_blessing_command(self, accounts: list[AccountData]):
        sender_email = GLOBAL_CACHE.Player.GetAccountEmail()        
        
        for account in accounts:
            GLOBAL_CACHE.ShMem.SendMessage(sender_email, account.AccountEmail, SharedCommandType.GetBlessing, (0, 0, 0, 0))
    
    def donate_faction_command(self, accounts: list[AccountData]):
        sender_email = GLOBAL_CACHE.Player.GetAccountEmail()
        
        for account in accounts:
            GLOBAL_CACHE.ShMem.SendMessage(sender_email, account.AccountEmail, SharedCommandType.DonateToGuild, (0, 0, 0, 0))
    
    def invite_all_command(self, accounts: list[AccountData]):
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
            
            same_map = GLOBAL_CACHE.Map.GetMapID() == account.MapID and GLOBAL_CACHE.Map.GetRegion()[0] == account.MapRegion and GLOBAL_CACHE.Map.GetDistrict() == account.MapDistrict and GLOBAL_CACHE.Map.GetLanguage()[0] == account.MapLanguage
            
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
                    GLOBAL_CACHE.Map.GetMapID(),
                    GLOBAL_CACHE.Map.GetRegion()[0],
                    GLOBAL_CACHE.Map.GetDistrict(),
                    GLOBAL_CACHE.Map.GetLanguage()[0],
                )
            ) 
        
    
    def resign_command(self, accounts: list[AccountData]):
        sender_email = GLOBAL_CACHE.Player.GetAccountEmail()
        
        for account in accounts:
            GLOBAL_CACHE.ShMem.SendMessage(sender_email, account.AccountEmail, SharedCommandType.Resign, (0, 0, 0, 0))
        
    def pixel_stack_command(self, accounts: list[AccountData]):
        player_x, player_y = GLOBAL_CACHE.Player.GetXY()
        sender_email = GLOBAL_CACHE.Player.GetAccountEmail()
        
        for account in accounts:
            if account.AccountEmail == sender_email:
                continue
            
            GLOBAL_CACHE.ShMem.SendMessage(sender_email, account.AccountEmail, SharedCommandType.PixelStack, (player_x, player_y, 0, 0))
            
    def unlock_chest_command(self, accounts: list[AccountData]):
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
            
    def interact_with_target_command(self, accounts: list[AccountData]):
        sender_email = GLOBAL_CACHE.Player.GetAccountEmail()        
        target_id = GLOBAL_CACHE.Player.GetTargetID()
        
        for account in accounts:
            GLOBAL_CACHE.ShMem.SendMessage(sender_email, account.AccountEmail, SharedCommandType.InteractWithTarget, (target_id, 0, 0, 0))
    
    def talk_and_dialog_with_target_command(self, accounts: list[AccountData]):
        sender_email = GLOBAL_CACHE.Player.GetAccountEmail()        
        target_id = GLOBAL_CACHE.Player.GetTargetID()
        
        for account in accounts:
            GLOBAL_CACHE.ShMem.SendMessage(sender_email, account.AccountEmail, SharedCommandType.TakeDialogWithTarget, (target_id, 1, 0, 0))

    def send_dialog(self, accounts: list[AccountData], dialog_option: int):
        sender_email = GLOBAL_CACHE.Player.GetAccountEmail()
        own_map_id = GLOBAL_CACHE.Map.GetMapID()
        own_region = GLOBAL_CACHE.Map.GetRegion()[0]
        own_district = GLOBAL_CACHE.Map.GetDistrict()
        own_language = GLOBAL_CACHE.Map.GetLanguage()[0]
        
        for account in accounts:
            same_map = own_map_id == account.MapID and own_region == account.MapRegion and own_district == account.MapDistrict and own_language == account.MapLanguage
            
            if same_map:
                GLOBAL_CACHE.ShMem.SendMessage(sender_email, account.AccountEmail, SharedCommandType.SendDialog, (dialog_option, 0, 0, 0))

    def open_consumables_commands(self, accounts: list[AccountData]):
        from HeroAI import ui
        ui.show_configure_consumables_window()

    def flag_heroes_command(self, accounts: list[AccountData]):
        from HeroAI import ui, windows
        windows.capture_flag_all = True
        windows.capture_hero_flag = True
        windows.capture_hero_index = 0
        windows.one_time_set_flag = False      
    
    def unflag_heroes_command(self, accounts: list[AccountData]):
        from HeroAI import ui, windows
        windows.ClearFlags = True