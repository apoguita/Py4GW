from functools import wraps
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from Py4GWCoreLib.botting_src.helpers import BottingHelpers
    
from .decorators import _yield_step, _fsm_step
from typing import Any, Generator, TYPE_CHECKING, Tuple, List, Optional, Callable
from Py4GWCoreLib.enums import SharedCommandType 

from Py4GWCoreLib import ConsoleLog, Console
from Py4GWCoreLib.Player import Player
from Py4GWCoreLib.Map import Map
from Py4GWCoreLib.GlobalCache.SharedMemory import (
    AccountStruct,
)

#region Multibox
class _Multibox:
    def __init__(self, parent: "BottingHelpers"):
        from ...GlobalCache import GLOBAL_CACHE
        self.parent = parent.parent
        self._config = parent._config
        self._Events = parent.Events   
        

    class _AccountData:
        def __init__(self, account_data:AccountStruct):
            self.SlotNumber = account_data.SlotNumber
            self.IsSlotActive = account_data.IsSlotActive
            self.AccountEmail = account_data.AccountEmail
            self.AccountName = account_data.AccountName
            self.CharacterName = account_data.AgentData.CharacterName
            self.IsAccount = account_data.IsAccount
            self.IsHero = account_data.IsHero
            self.IsPet = account_data.IsPet
            self.IsNPC = account_data.IsNPC
            self.OwnerPlayerID = account_data.AgentData.OwnerAgentID
            self.HeroID = account_data.AgentData.HeroID
            self.MapID = account_data.AgentData.Map.MapID
            self.MapRegion = account_data.AgentData.Map.Region
            self.MapDistrict = account_data.AgentData.Map.District
            self.PlayerID = account_data.AgentData.AgentID
            self.PlayerHP = account_data.AgentData.Health.Current
            self.PlayerMaxHP = account_data.AgentData.Health.Max
            self.PlayerHealthRegen = account_data.AgentData.Health.Regen
            self.PlayerEnergy = account_data.AgentData.Energy.Current
            self.PlayerMaxEnergy = account_data.AgentData.Energy.Max
            self.PlayerEnergyRegen = account_data.AgentData.Energy.Regen
            self.PlayerPosX = account_data.AgentData.Pos.x
            self.PlayerPosY = account_data.AgentData.Pos.y
            self.PlayerPosZ = account_data.AgentData.Pos.z
            self.PlayerFacingAngle = account_data.AgentData.RotationAngle
            self.PlayerTargetID = account_data.AgentData.TargetID
            self.PlayerLoginNumber = account_data.AgentData.LoginNumber
            self.PlayerIsTicked = account_data.AgentPartyData.IsTicked
            self.PartyID = account_data.AgentPartyData.PartyID
            self.PartyPosition = account_data.AgentPartyData.PartyPosition
            self.PlayerIsPartyLeader = account_data.AgentPartyData.IsPartyLeader            
            self.PlayerBuffs = account_data.AgentData.Buffs.Buffs
            self.LastUpdated = account_data.LastUpdated

        
    class _HeroAI:
        class HeroAIOptions:
            def __init__(self, email: str):
                from ...GlobalCache import GLOBAL_CACHE
                hero_ai_options = GLOBAL_CACHE.ShMem.GetHeroAIOptions(email)

                self.email = hero_ai_options.Email if hero_ai_options else email
                self.Following = hero_ai_options.Following if hero_ai_options else False
                self.Avoidance = hero_ai_options.Avoidance if hero_ai_options else False
                self.Looting = hero_ai_options.Looting if hero_ai_options else False
                self.Targeting = hero_ai_options.Targeting if hero_ai_options else False
                self.Combat = hero_ai_options.Combat if hero_ai_options else False
                self.Skills = list(hero_ai_options.Skills) if hero_ai_options else []
                self.IsFlagged = hero_ai_options.IsFlagged if hero_ai_options else False
                self.FlagPosX = hero_ai_options.FlagPosX if hero_ai_options else 0.0
                self.FlagPosY = hero_ai_options.FlagPosY if hero_ai_options else 0.0
                self.FlagFacingAngle = hero_ai_options.FlagFacingAngle if hero_ai_options else 0.0

            
        def __init__(self, parent: "_Multibox"):
            self.parent = parent.parent
            self._config = parent._config
            self._Events = parent._Events 

            
        def _get_hero_ai_options_by_email(self, email: str):
            from ...GlobalCache import GLOBAL_CACHE
            hero_ai_options = self.HeroAIOptions(email)
            return hero_ai_options

        def _set_hero_ai_options_by_email(self, email: str, option: str, value: Any, skill_index:int =0):
            from ...GlobalCache import GLOBAL_CACHE
            current_options = GLOBAL_CACHE.ShMem.GetHeroAIOptions(email)
            if not current_options:
                return

            current_options.Email = email
            current_options.Following = value if option == "Following" else current_options.Following
            current_options.Avoidance = value if option == "Avoidance" else current_options.Avoidance
            current_options.Looting = value if option == "Looting" else current_options.Looting
            current_options.Targeting = value if option == "Targeting" else current_options.Targeting
            current_options.Combat = value if option == "Combat" else current_options.Combat
            current_options.Skills
            current_options.Skills[skill_index] = bool(value if ((option == "Skills") and (skill_index >=1) and (skill_index < 8)) else current_options.Skills[skill_index])
            current_options.IsFlagged = value if option == "IsFlagged" else current_options.IsFlagged
            current_options.FlagPosX = value if option == "FlagPosX" else current_options.FlagPosX
            current_options.FlagPosY = value if option == "FlagPosY" else current_options.FlagPosY
            current_options.FlagFacingAngle = value if option == "FlagFacingAngle" else current_options.FlagFacingAngle

            result = GLOBAL_CACHE.ShMem.SetHeroAIOptions(email, current_options)
            return result
        
    def _get_all_account_data(self) -> List[_AccountData]:
        from ...GlobalCache import GLOBAL_CACHE
        accounts = GLOBAL_CACHE.ShMem.GetAllAccountData()
        account_list = []
        for account in accounts:
            account_list.append(self._AccountData(account))
        return account_list
    
    def _get_all_account_emails(self) -> List[str]:
        from ...GlobalCache import GLOBAL_CACHE
        accounts = GLOBAL_CACHE.ShMem.GetAllAccountData()
        account_list = []
        for account in accounts:
            account_list.append(account.AccountEmail)
        return account_list
    
    def _get_account_data_from_email(self, email: str) -> Optional[_AccountData]:
        from ...GlobalCache import GLOBAL_CACHE
        account = GLOBAL_CACHE.ShMem.GetAccountDataFromEmail(email)
        if account is None:
            return None
        return self._AccountData(account)
    
    def _get_player_data(self):
        from ...GlobalCache import GLOBAL_CACHE
        player_email = Player.GetAccountEmail()
        return self._get_account_data_from_email(player_email)

    def _summon_all_accounts(self):
        from ...GlobalCache import GLOBAL_CACHE
        from ...Routines import Routines
        player_data = self._get_player_data()
        all_accounts = self._get_all_account_data()
        
        if not player_data:
            return
        
        for account in all_accounts:
            if (player_data.MapID == account.MapID and
                player_data.MapRegion == account.MapRegion and
                player_data.MapDistrict == account.MapDistrict):
                continue

            GLOBAL_CACHE.ShMem.SendMessage(player_data.AccountEmail, account.AccountEmail, SharedCommandType.TravelToMap, (player_data.MapID, player_data.MapRegion, player_data.MapDistrict, 0))
            yield from Routines.Yield.wait(500)
        yield

    def _summon_account_by_email(self, email: str):
        from ...GlobalCache import GLOBAL_CACHE
        from ...Routines import Routines
        player_data = self._get_player_data()
        account = self._get_account_data_from_email(email)
        
        if not player_data or not account:
            return
        
        if (player_data.MapID == account.MapID and
            player_data.MapRegion == account.MapRegion and
            player_data.MapDistrict == account.MapDistrict):
            return

        GLOBAL_CACHE.ShMem.SendMessage(player_data.AccountEmail, account.AccountEmail, SharedCommandType.TravelToMap, (player_data.MapID, player_data.MapRegion, player_data.MapDistrict, 0))
        yield from  Routines.Yield.wait(500)
        
    def _invite_all_accounts(self):
        from ...GlobalCache import GLOBAL_CACHE
        from ...Routines import Routines
        player_data = self._get_player_data()
        all_accounts = self._get_all_account_data()
        
        if not player_data:
            return
        
        for account in all_accounts:
            if (player_data.MapID == account.MapID and
                player_data.MapRegion == account.MapRegion and
                player_data.MapDistrict == account.MapDistrict and
                player_data.PartyID != account.PartyID):
                GLOBAL_CACHE.Party.Players.InvitePlayer(account.CharacterName)
                GLOBAL_CACHE.ShMem.SendMessage(player_data.AccountEmail, account.AccountEmail, SharedCommandType.InviteToParty, (0,0,0,0))
                yield from Routines.Yield.wait(500)
        yield
        
    def _invite_account_by_email(self, email: str):
        from ...GlobalCache import GLOBAL_CACHE
        from ...Routines import Routines
        player_data = self._get_player_data()
        account = self._get_account_data_from_email(email)
        
        if not player_data or not account:
            return
        
        if (player_data.MapID == account.MapID and
            player_data.MapRegion == account.MapRegion and
            player_data.MapDistrict == account.MapDistrict and
            player_data.PartyID != account.PartyID):
            GLOBAL_CACHE.Party.Players.InvitePlayer(account.CharacterName)
            GLOBAL_CACHE.ShMem.SendMessage(player_data.AccountEmail, account.AccountEmail, SharedCommandType.InviteToParty, (0,0,0,0))
            yield from Routines.Yield.wait(500)
        yield
        
    def _kick_account_by_email(self, email: str):
        from ...GlobalCache import GLOBAL_CACHE
        from ...Routines import Routines
        player_data = self._get_player_data()
        account = self._get_account_data_from_email(email)
        
        if not player_data or not account:
            return
        
        if player_data.PartyID == account.PartyID and player_data.AccountEmail != account.AccountEmail:
            GLOBAL_CACHE.Party.Players.KickPlayer(account.CharacterName)
            yield from Routines.Yield.wait(500)
        yield
        
    def _kick_all_accounts(self):
        from ...GlobalCache import GLOBAL_CACHE
        from ...Routines import Routines
        player_data = self._get_player_data()
        all_accounts = self._get_all_account_data()
        
        if not player_data:
            return
        
        for account in all_accounts:
            if player_data.PartyID == account.PartyID and player_data.AccountEmail != account.AccountEmail:
                GLOBAL_CACHE.Party.Players.KickPlayer(account.CharacterName)
                yield from Routines.Yield.wait(500)
        
    def _resignParty(self):
        from ...GlobalCache import GLOBAL_CACHE
        from ...Routines import Routines
        accounts = GLOBAL_CACHE.ShMem.GetAllAccountData()
        sender_email = Player.GetAccountEmail()
        for account in accounts:
            ConsoleLog("Messaging", "Resigning account: " + account.AccountEmail, log=False)
            GLOBAL_CACHE.ShMem.SendMessage(sender_email, account.AccountEmail, SharedCommandType.Resign, (0,0,0,0))
        yield from Routines.Yield.wait(500)
        
    def _pixel_stack(self):
        from ...GlobalCache import GLOBAL_CACHE
        from ...Agent import Agent
        from ...import Range
        sender_email = Player.GetAccountEmail()
        x, y = Player.GetXY()

        players = GLOBAL_CACHE.Party.GetPlayers()
        current_map = Map.GetMapID()
        player_names = []

        for player in players:
            agent_name = GLOBAL_CACHE.Party.Players.GetPlayerNameByLoginNumber(player.login_number)
            agent_id = GLOBAL_CACHE.Party.Players.GetAgentIDByLoginNumber(player.login_number)
            agent = Agent.GetAgentByID(agent_id)
            if not agent:
                continue
            dx, dy = x - agent.pos.x, y - agent.pos.y
            players_dist_sq = dx * dx + dy * dy
            max_dist_sq = Range.Earshot.value ** 2

            if agent_name != "" and players_dist_sq > max_dist_sq:
                player_names.append(agent_name)
        
        accounts = GLOBAL_CACHE.ShMem.GetAllAccountData()
        sender_email = sender_email
        for account in accounts:
            if sender_email == account.AccountEmail:
                continue
            
            if not current_map == account.AgentData.Map.MapID:
                continue
            
            account_name = account.AgentData.CharacterName
            if account_name not in player_names:
                continue 
            
            ConsoleLog("Messaging", "Pixelstacking account: " + account.AccountEmail, log= False)
            GLOBAL_CACHE.ShMem.SendMessage(sender_email, account.AccountEmail, SharedCommandType.PixelStack, (x,y,0,0))
        yield
        
    def _brute_force_unstuck(self):
        from ...GlobalCache import GLOBAL_CACHE

        sender_email = Player.GetAccountEmail()
        x, y = Player.GetXY()

        players = GLOBAL_CACHE.Party.GetPlayers()
        current_map = Map.GetMapID()
        player_names = []

        for player in players:
            agent_name = GLOBAL_CACHE.Party.Players.GetPlayerNameByLoginNumber(player.login_number)
            if agent_name != "":
                player_names.append(agent_name)

        accounts = GLOBAL_CACHE.ShMem.GetAllAccountData()
        for account in accounts:
            if sender_email == account.AccountEmail:
                continue

            if not current_map == account.AgentData.Map.MapID:
                continue

            account_name = account.AgentData.CharacterName
            if account_name not in player_names:
                continue

            ConsoleLog("Messaging", "BruteForcing account: " + account.AccountEmail, log=False)
            # send same-shaped payload as pixel stack (x, y, 0, 0) — adjust if your handler expects different
            GLOBAL_CACHE.ShMem.SendMessage(sender_email, account.AccountEmail, SharedCommandType.BruteForceUnstuck, (x, y, 0, 0))

        yield

        
    def _interact_with_target(self):
        from ...GlobalCache import GLOBAL_CACHE
        target = Player.GetTargetID()
        if target == 0:
            ConsoleLog("Messaging", "No target to interact with.")
            return
        sender_email = Player.GetAccountEmail()
        accounts = GLOBAL_CACHE.ShMem.GetAllAccountData()

        for account in accounts:
            if sender_email == account.AccountEmail:
                continue
            ConsoleLog("Messaging", f"Ordering {account.AccountEmail} to interact with target: {target}", log=False)
            GLOBAL_CACHE.ShMem.SendMessage(sender_email, account.AccountEmail, SharedCommandType.InteractWithTarget, (target,0,0,0))
        yield
        
    def _take_dialog_with_target(self):
        from ...GlobalCache import GLOBAL_CACHE
        from ...UIManager import UIManager
        target = Player.GetTargetID()
        if target == 0:
            ConsoleLog("Messaging", "No target to interact with.")
            return
        if not UIManager.IsNPCDialogVisible():
            ConsoleLog("Messaging", "No dialog is open.")
            return
        
        # i need to display a modal dialog here to confirm options
        options = UIManager.GetDialogButtonCount()
        sender_email = Player.GetAccountEmail()

        self_account = GLOBAL_CACHE.ShMem.GetAccountDataFromEmail(sender_email)
        if not self_account:
            return
        accounts = GLOBAL_CACHE.ShMem.GetAllAccountData()
        for account in accounts:
            if self_account.AccountEmail == account.AccountEmail:
                continue
            ConsoleLog("Messaging", f"Ordering {account.AccountEmail} to interact with target: {target}", log=False)
            GLOBAL_CACHE.ShMem.SendMessage(sender_email, account.AccountEmail, SharedCommandType.TakeDialogWithTarget, (target,1,0,0))
        yield
        
    def _use_consumable_message(self, params):
        from ...GlobalCache import GLOBAL_CACHE
        from ...Routines import Routines
        account_email = sender_email = Player.GetAccountEmail()

        accounts = GLOBAL_CACHE.ShMem.GetAllAccountData()
        sender_email = account_email
        for account in accounts:
            ConsoleLog("Messaging", f"Sending Consumable Message to  {account.AccountEmail}", log= False)
            
            GLOBAL_CACHE.ShMem.SendMessage(sender_email, account.AccountEmail, SharedCommandType.PCon, params)
        yield from Routines.Yield.wait(500)
        
    def _donate_faction(self):
        from ...GlobalCache import GLOBAL_CACHE
        accounts = GLOBAL_CACHE.ShMem.GetAllAccountData()
        sender_email = Player.GetAccountEmail()
        for account in accounts:
            ConsoleLog("Messaging", "Donating to guild from account: " + account.AccountEmail, log= False)
            GLOBAL_CACHE.ShMem.SendMessage(sender_email, account.AccountEmail, SharedCommandType.DonateToGuild, (0,0,0,0))
        yield
        
    def _send_dialog_with_target(self, dialog_id: int, wait_time: int=3000):
        from ...GlobalCache import GLOBAL_CACHE
        from ...Routines import Routines
        target = Player.GetTargetID()
        if target == 0:
            ConsoleLog("Messaging", "No target to interact with.")
            return
        sender_email = Player.GetAccountEmail()
        accounts = GLOBAL_CACHE.ShMem.GetAllAccountData()

        for account in accounts:
            ConsoleLog("Messaging", f"Ordering {account.AccountEmail} to send dialog {dialog_id} to target: {target}", log=False)
            GLOBAL_CACHE.ShMem.SendMessage(sender_email, account.AccountEmail, SharedCommandType.SendDialogToTarget, (target, dialog_id,0,0))
        yield from Routines.Yield.wait(wait_time)
        
    @_yield_step(label="ResignParty", counter_key="RESIGN_PARTY")
    def resign_party(self):
        yield from self._resignParty()
        
    @_yield_step(label="DonateFaction", counter_key="DONATE_FACTION")
    def donate_faction(self):
        yield from self._donate_faction()

    @_yield_step(label="SendDialogToTarget", counter_key="SEND_DIALOG_TO_TARGET")
    def send_dialog_to_target(self, dialog_id: int):
        yield from self._send_dialog_with_target(dialog_id)

    @_yield_step(label="PixelStack", counter_key="PIXEL_STACK")
    def pixel_stack(self):
        yield from self._pixel_stack()
        
    @_yield_step(label="InteractWithTarget", counter_key="INTERACT_WITH_TARGET")
    def interact_with_target(self):
        yield from self._interact_with_target()

    @_yield_step(label="TakeDialogWithTarget", counter_key="TAKE_DIALOG_WITH_TARGET")
    def take_dialog_with_target(self):
        yield from self._take_dialog_with_target()
        
    @_yield_step(label="UseConsumable", counter_key="USE_CONSUMABLE")
    def use_consumable(self, params):
        yield from self._use_consumable_message(params)
        
    @_yield_step(label="SummonAllAccounts", counter_key="SUMMON_ALL_ACCOUNTS")
    def summon_all_accounts(self):
        yield from self._summon_all_accounts()
        
    @_yield_step(label="SummonAccountByEmail", counter_key="SUMMON_ACCOUNT_BY_EMAIL")
    def summon_account_by_email(self, email: str):
        yield from self._summon_account_by_email(email)
        
    @_yield_step(label="InviteAllAccounts", counter_key="INVITE_ALL_ACCOUNTS")
    def invite_all_accounts(self):
        yield from self._invite_all_accounts()
        
    @_yield_step(label="InviteAccountByEmail", counter_key="INVITE_ACCOUNT_BY_EMAIL")
    def invite_account_by_email(self, email: str):
        yield from self._invite_account_by_email(email)
        
    @_yield_step(label="KickAllAccounts", counter_key="KICK_ALL_ACCOUNTS")
    def kick_all_accounts(self):
        yield from self._kick_all_accounts()
        
    @_yield_step(label="KickAccountByEmail", counter_key="KICK_ACCOUNT_BY_EMAIL")
    def kick_account_by_email(self, email: str):
        yield from self._kick_account_by_email(email)
        
    def get_all_account_data(self) -> List[_AccountData]:
        return self._get_all_account_data()

    def get_all_account_emails(self) -> List[str]:
        return self._get_all_account_emails()
    
    def get_account_data_from_email(self, email: str) -> Optional[_AccountData]:
        return self._get_account_data_from_email(email)
    
    def get_player_data(self) -> Optional[_AccountData]:
        return self._get_player_data()