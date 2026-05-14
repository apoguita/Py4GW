
from typing import Tuple

import importlib

class _RProxy:
    def __getattr__(self, name: str):
        root_pkg = importlib.import_module("Py4GWCoreLib")
        return getattr(root_pkg.Routines, name)

Routines = _RProxy()
from ..Player import Player
from ..py4gwcorelib_src.FrameCache import frame_cache

class Checks:
#region Player
    class Player:
        @staticmethod
        def CanAct():
            if not Checks.Map.MapValid():
                return False
            if Checks.Player.IsDead():
                return False
            if Checks.Player.IsKnockedDown():
                return False
            if Checks.Player.IsCasting():
                return False
            
            #from ..Agent import Agent
            #return Agent.CanAct(Player.GetAgentID())
        
            return True 
        
        
        @staticmethod
        def IsDead():
            from ..GlobalCache import GLOBAL_CACHE
            from ..Agent import Agent
            return Agent.IsDead(Player.GetAgentID())
        
        @staticmethod
        def IsCasting():
            from ..GlobalCache import GLOBAL_CACHE
            from ..Agent import Agent
            return Agent.IsCasting(Player.GetAgentID())
        
        @staticmethod
        def IsKnockedDown():
            from ..GlobalCache import GLOBAL_CACHE
            from ..Agent import Agent
            return Agent.IsKnockedDown(Player.GetAgentID())

#region Party
    class Party:
        @staticmethod
        def GetPartyMemberInDangerID(aggro_area=None, aggressive_only: bool = False):
            from ..GlobalCache import GLOBAL_CACHE
            from ..AgentArray import AgentArray
            from ..Agent import Agent
            from ..Map import Map
            from ..Party import Party
            from ..enums_src.GameData_enums import Range

            if not Checks.Map.MapValid():
                return 0

            if aggro_area is None:
                aggro_area = Range.Earshot

            enemy_array = AgentArray.GetEnemyArray()
            if not enemy_array:
                return 0

            radius = aggro_area.value if hasattr(aggro_area, "value") else float(aggro_area)
            radius_sq = radius * radius
            self_agent_id = Player.GetAgentID()
            shared_in_aggro_by_agent: dict[int, bool] = {}

            # Shared-memory fallback for multiboxed party members:
            # local enemy arrays can miss fights happening away from the leader.
            try:
                own_map_id = int(Map.GetMapID() or 0)
                own_region = int(Map.GetRegion()[0] or 0)
                own_district = int(Map.GetDistrict() or 0)
                own_language = int(Map.GetLanguage()[0] or 0)
                own_party_id = int(Party.GetPartyID() or 0)

                for account in GLOBAL_CACHE.ShMem.GetAllAccountData():
                    agent_id = int(getattr(account.AgentData, "AgentID", 0) or 0)
                    if agent_id <= 0:
                        continue
                    if own_party_id > 0 and int(getattr(account.AgentPartyData, "PartyID", 0) or 0) != own_party_id:
                        continue

                    same_map = (
                        int(getattr(account.AgentData.Map, "MapID", 0) or 0) == own_map_id
                        and int(getattr(account.AgentData.Map, "Region", 0) or 0) == own_region
                        and int(getattr(account.AgentData.Map, "District", 0) or 0) == own_district
                        and int(getattr(account.AgentData.Map, "Language", 0) or 0) == own_language
                    )
                    if not same_map:
                        continue

                    shared_in_aggro_by_agent[agent_id] = bool(getattr(account, "InAggro", False))
            except Exception:
                shared_in_aggro_by_agent = {}

            def _member_in_danger(agent_id: int) -> bool:
                if not Agent.IsValid(agent_id) or Agent.IsDead(agent_id):
                    return False
                if agent_id == self_agent_id:
                    return False
                if bool(shared_in_aggro_by_agent.get(int(agent_id), False)):
                    return True

                member_pos = Agent.GetXY(agent_id)
                if not member_pos:
                    return False

                mx, my = member_pos
                for enemy_id in enemy_array:
                    if enemy_id == agent_id:
                        continue
                    if not Agent.IsAlive(enemy_id):
                        continue
                    if aggressive_only and not Agent.IsAggressive(enemy_id):
                        continue

                    enemy_pos = Agent.GetXY(enemy_id)
                    if not enemy_pos:
                        continue

                    dx = mx - enemy_pos[0]
                    dy = my - enemy_pos[1]
                    if (dx * dx + dy * dy) <= radius_sq:
                        return True
                return False

            players = GLOBAL_CACHE.Party.GetPlayers()
            henchmen = GLOBAL_CACHE.Party.GetHenchmen()
            heroes = GLOBAL_CACHE.Party.GetHeroes()

            for player in players:
                agent_id = GLOBAL_CACHE.Party.Players.GetAgentIDByLoginNumber(player.login_number)
                if _member_in_danger(agent_id):
                    return agent_id

            for henchman in henchmen:
                if _member_in_danger(henchman.agent_id):
                    return henchman.agent_id

            for hero in heroes:
                if _member_in_danger(hero.agent_id):
                    return hero.agent_id

            return 0

        @staticmethod
        def IsPartyMemberInDanger(aggro_area=None, aggressive_only: bool = False):
            return Checks.Party.GetPartyMemberInDangerID(aggro_area=aggro_area, aggressive_only=aggressive_only) != 0

        @staticmethod
        def IsPartyMemberDead():
            from ..GlobalCache import GLOBAL_CACHE
            from ..Agent import Agent
            if not Checks.Map.MapValid():
                return False
            is_someone_dead = False
            players = GLOBAL_CACHE.Party.GetPlayers()
            henchmen = GLOBAL_CACHE.Party.GetHenchmen()
            heroes = GLOBAL_CACHE.Party.GetHeroes()

            for player in players:
                agent_id = GLOBAL_CACHE.Party.Players.GetAgentIDByLoginNumber(player.login_number)
                if Agent.IsValid(agent_id) and Agent.IsDead(agent_id):
                    is_someone_dead = True
                    break
            for henchman in henchmen:
                if Agent.IsValid(henchman.agent_id) and Agent.IsDead(henchman.agent_id):
                    is_someone_dead = True
                    break

            for hero in heroes:
                if Agent.IsValid(hero.agent_id) and Agent.IsDead(hero.agent_id):
                    is_someone_dead = True
                    break

            return is_someone_dead
        
        @staticmethod
        def IsPartyMemberBehind(range_value: int = 3500): #spirit
            from ..GlobalCache import GLOBAL_CACHE
            from ..Py4GWcorelib import Utils
            from ..Agent import Agent
            if not Checks.Map.MapValid():
                return False

            players = GLOBAL_CACHE.Party.GetPlayers()
            henchmen = GLOBAL_CACHE.Party.GetHenchmen()
            heroes = GLOBAL_CACHE.Party.GetHeroes()
            player_pos = Player.GetXY()

            for player in players:
                agent_id = GLOBAL_CACHE.Party.Players.GetAgentIDByLoginNumber(player.login_number)
                if Agent.IsValid(agent_id) and not Agent.IsDead(agent_id):
                    agent_pos = Agent.GetXY(agent_id)
                    if Utils.Distance(player_pos, agent_pos) > range_value:
                        return True

            for henchman in henchmen:
                if Agent.IsValid(henchman.agent_id) and not Agent.IsDead(henchman.agent_id):
                    agent_pos = Agent.GetXY(henchman.agent_id)
                    if Utils.Distance(player_pos, agent_pos) > range_value:
                        return True

            for hero in heroes:
                if Agent.IsValid(hero.agent_id) and not Agent.IsDead(hero.agent_id):
                    agent_pos = Agent.GetXY(hero.agent_id)
                    if Utils.Distance(player_pos, agent_pos) > range_value:
                        return True

            return False
        
        @staticmethod
        def IsDeadPartyMemberBehind():
            from ..GlobalCache import GLOBAL_CACHE
            from ..Py4GWcorelib import Utils
            from ..enums_src.GameData_enums import Range
            from ..Routines import Checks
            from ..Agent import Agent

            if not Checks.Map.MapValid():
                return False

            players = GLOBAL_CACHE.Party.GetPlayers()
            henchmen = GLOBAL_CACHE.Party.GetHenchmen()
            heroes = GLOBAL_CACHE.Party.GetHeroes()
            player_pos = Player.GetXY()

            for player in players:
                agent_id = GLOBAL_CACHE.Party.Players.GetAgentIDByLoginNumber(player.login_number)
                if Agent.IsValid(agent_id) and Agent.IsDead(agent_id):
                    agent_pos = Agent.GetXY(agent_id)
                    if Utils.Distance(player_pos, agent_pos) > Range.Earshot.value:
                        return True

            for henchman in henchmen:
                if Agent.IsValid(henchman.agent_id) and Agent.IsDead(henchman.agent_id):
                    agent_pos = Agent.GetXY(henchman.agent_id)
                    if Utils.Distance(player_pos, agent_pos) > Range.Earshot.value:
                        return True

            for hero in heroes:
                if Agent.IsValid(hero.agent_id) and Agent.IsDead(hero.agent_id):
                    agent_pos = Agent.GetXY(hero.agent_id)
                    if Utils.Distance(player_pos, agent_pos) > Range.Earshot.value:
                        return True

            return False

        
        @staticmethod
        def IsPartyWiped():
            from ..GlobalCache import GLOBAL_CACHE
            from ..Agent import Agent
            if not Checks.Map.MapValid():
                return False

            if not Checks.Party.IsPartyLoaded():
                return False

            players = GLOBAL_CACHE.Party.GetPlayers()
            henchmen = GLOBAL_CACHE.Party.GetHenchmen()
            heroes = GLOBAL_CACHE.Party.GetHeroes()
            found_valid_member = False

            for player in players:
                agent_id = GLOBAL_CACHE.Party.Players.GetAgentIDByLoginNumber(player.login_number)
                if not Agent.IsValid(agent_id):
                    continue
                found_valid_member = True
                if not Agent.IsDead(agent_id):
                    return False

            for henchman in henchmen:
                if not Agent.IsValid(henchman.agent_id):
                    continue
                found_valid_member = True
                if not Agent.IsDead(henchman.agent_id):
                    return False

            for hero in heroes:
                if not Agent.IsValid(hero.agent_id):
                    continue
                found_valid_member = True
                if not Agent.IsDead(hero.agent_id):
                    return False

            return found_valid_member
        
        @staticmethod
        def IsPartyLoaded():
            from ..GlobalCache import GLOBAL_CACHE
            from ..Agent import Agent
            if not Checks.Map.MapValid():
                return False
            return GLOBAL_CACHE.Party.IsPartyLoaded()
        
        @staticmethod
        def IsAllPartyMembersInRange(range_value):
            from ..GlobalCache import GLOBAL_CACHE
            from ..Py4GWcorelib import Utils
            from ..Agent import Agent
            if not Checks.Map.MapValid():
                return False

            all_in_range = True
            players = GLOBAL_CACHE.Party.GetPlayers()
            henchmen = GLOBAL_CACHE.Party.GetHenchmen()
            heroes = GLOBAL_CACHE.Party.GetHeroes()
            player_pos = Player.GetXY()

            for player in players:
                agent_id = GLOBAL_CACHE.Party.Players.GetAgentIDByLoginNumber(player.login_number)
                if Agent.IsValid(agent_id) and not Agent.IsDead(agent_id):
                    agent_pos = Agent.GetXY(agent_id)
                    if Utils.Distance(player_pos, agent_pos) > range_value:
                        all_in_range = False
                        break

            for henchman in henchmen:
                if Agent.IsValid(henchman.agent_id) and not Agent.IsDead(henchman.agent_id):
                    agent_pos = Agent.GetXY(henchman.agent_id)
                    if Utils.Distance(player_pos, agent_pos) > range_value:
                        all_in_range = False
                        break

            for hero in heroes:
                if Agent.IsValid(hero.agent_id) and not Agent.IsDead(hero.agent_id):
                    agent_pos = Agent.GetXY(hero.agent_id)
                    if Utils.Distance(player_pos, agent_pos) > range_value:
                        all_in_range = False
                        break

            return all_in_range
        
        

#region Map
    class Map:
        @staticmethod
        def MapValid():
            from ..Map import Map
            from ..Party import Party

            if not Map.IsMapReady():
                return False
            
            if Map.IsInCinematic():
                return False
            
            if not Party.IsPartyLoaded():
                return False
            
            return True
        
        @staticmethod
        def IsExplorable():
            from ..Map import Map
            if not Checks.Map.MapValid():
                return False
            return Map.IsExplorable()
        
        @staticmethod
        def IsOutpost():
            from ..Map import Map
            if not Checks.Map.MapValid():
                return False
            return Map.IsOutpost()
        
        @staticmethod
        def IsLoading():
            from ..Map import Map
            if not Checks.Map.MapValid():
                return True
            
            return Map.IsMapLoading()
        
        @staticmethod
        def IsMapReady():
            from ..Map import Map
            return Map.IsMapReady()

        
        @staticmethod
        def IsInCinematic():
            from ..Map import Map
            if not Checks.Map.MapValid():
                return False
            return Map.IsInCinematic()
        
        @staticmethod
        def IsCombatReady():
            from ..Map import Map
            if not Checks.Map.MapValid():
                return False
            return Map.IsExplorable()
        
#region Inventory
    class Inventory:
        @staticmethod
        def InventoryAndLockpickCheck():
            from ..GlobalCache import GLOBAL_CACHE
            return GLOBAL_CACHE.Inventory.GetFreeSlotCount() > 0 and GLOBAL_CACHE.Inventory.GetModelCount(22751) > 0 
        
        @staticmethod
        def IsModelInInventory(model_id: int):
            from ..GlobalCache import GLOBAL_CACHE
            return GLOBAL_CACHE.Inventory.GetModelCount(model_id) > 0
        
        @staticmethod
        def IsItemInInventory(item_id: int):
            from ..GlobalCache import GLOBAL_CACHE
            return GLOBAL_CACHE.Inventory.GetItemCount(item_id) > 0
        
        @staticmethod
        def IsModelEquipped(model_id: int):
            from ..GlobalCache import GLOBAL_CACHE
            return GLOBAL_CACHE.Inventory.GetModelCountInEquipped(model_id) > 0
        
        @staticmethod
        def IsModelInBank(model_id: int):
            from ..GlobalCache import GLOBAL_CACHE
            return GLOBAL_CACHE.Inventory.GetModelCountInStorage(model_id) > 0
        
        @staticmethod
        def IsModelInInventoryOrBank(model_id: int):
            from ..GlobalCache import GLOBAL_CACHE
            return (GLOBAL_CACHE.Inventory.GetModelCount(model_id) + GLOBAL_CACHE.Inventory.GetModelCountInStorage(model_id)) > 0
        
        @staticmethod
        def IsModelInInventoryOrEquipped(model_id: int):
            from ..GlobalCache import GLOBAL_CACHE
            return (GLOBAL_CACHE.Inventory.GetModelCount(model_id) + GLOBAL_CACHE.Inventory.GetModelCountInEquipped(model_id)) > 0
    
    class Items:
        @staticmethod
        def IsSalvageable(item_id: int):
            from ..GlobalCache import GLOBAL_CACHE
            from ..Item import Item
            item_instance = Item.item_instance(item_id)
            return item_instance.is_salvageable  
        
        
#region Effects
    class Effects:
        @staticmethod
        def HasBuff(agent_id, skill_id):
            from ..GlobalCache import GLOBAL_CACHE
            if GLOBAL_CACHE.Effects.HasEffect(agent_id, skill_id):
                return True
            return False
        
        @staticmethod
        def HasEffect(agent_id, skill_id, exact_weapon_spell=False):
            return Checks.Agents.HasEffect(agent_id, skill_id, exact_weapon_spell)
        
#region Agents
    class Agents:
        from ..enums_src.GameData_enums import Range

        @staticmethod
        @frame_cache(category="Checks.Agents", source_lib="_get_same_party_shared_agent_data")
        def _get_same_party_shared_agent_data(agent_id: int):
            from ..GlobalCache import GLOBAL_CACHE
            from ..Map import Map
            from ..Party import Party

            if not agent_id or not Map.IsMapReady():
                return None

            own_map_id = Map.GetMapID()
            own_region = Map.GetRegion()[0]
            own_district = Map.GetDistrict()
            own_language = Map.GetLanguage()[0]
            own_party_id = Party.GetPartyID()
            party_members = {
                int(Party.Players.GetAgentIDByLoginNumber(party_member.login_number) or 0)
                for party_member in (Party.GetPlayers() or [])
            }

            for acc in GLOBAL_CACHE.ShMem.GetAllAccountData():
                if not acc.IsSlotActive or acc.AgentData.AgentID != agent_id:
                    continue

                same_map = (
                    own_map_id == acc.AgentData.Map.MapID
                    and own_region == acc.AgentData.Map.Region
                    and own_district == acc.AgentData.Map.District
                    and own_language == acc.AgentData.Map.Language
                )
                same_party = agent_id in party_members and acc.AgentPartyData.PartyID == own_party_id
                if same_map and same_party:
                    return acc.AgentData

            return None

        @staticmethod
        @frame_cache(category="Checks.Agents", source_lib="_shared_agent_has_skill_equipped")
        def _shared_agent_has_skill_equipped(agent_id: int, skill_id: int) -> bool:
            if not agent_id or not skill_id:
                return False

            shared_agent_data = Checks.Agents._get_same_party_shared_agent_data(agent_id)
            if shared_agent_data is None:
                return False

            return any(int(skill.Id) == skill_id for skill in shared_agent_data.Skillbar.Skills)

        @staticmethod
        @frame_cache(category="Checks.Agents", source_lib="_get_shared_weapon_name")
        def _get_shared_weapon_name(agent_id: int) -> tuple[int, str]:
            from ..Agent import Agent
            from ..enums_src.GameData_enums import Weapon, Weapon_Names

            shared_agent_data = Checks.Agents._get_same_party_shared_agent_data(agent_id)
            if shared_agent_data is None:
                return Agent.GetWeaponType(agent_id)

            weapon_type = int(shared_agent_data.WeaponType)
            if weapon_type == 0:
                return 0, "Unknown"

            try:
                weapon_type_enum = Weapon(weapon_type)
            except ValueError:
                return weapon_type, "Unknown"

            return weapon_type, Weapon_Names.get(weapon_type_enum, "Unknown")

        @staticmethod
        @frame_cache(category="Checks.Agents", source_lib="IsDead")
        def IsDead(agent_id: int) -> bool:
            from ..Agent import Agent

            shared_agent_data = Checks.Agents._get_same_party_shared_agent_data(agent_id)
            if shared_agent_data is not None:
                return bool(
                    shared_agent_data.Is_Dead
                    or shared_agent_data.Is_DeadByTypeMap
                    or float(shared_agent_data.Health.Current) <= Agent.DEAD_HEALTH_EPSILON
                )
            return bool(Agent.IsDead(agent_id) or Agent.GetHealth(agent_id) <= Agent.DEAD_HEALTH_EPSILON)

        @staticmethod
        @frame_cache(category="Checks.Agents", source_lib="IsAlive")
        def IsAlive(agent_id: int) -> bool:
            from ..Agent import Agent

            shared_agent_data = Checks.Agents._get_same_party_shared_agent_data(agent_id)
            if shared_agent_data is not None:
                return (
                    (not shared_agent_data.Is_Dead)
                    and (not shared_agent_data.Is_DeadByTypeMap)
                    and float(shared_agent_data.Health.Current) > Agent.DEAD_HEALTH_EPSILON
                )
            return (not Agent.IsDead(agent_id)) and Agent.GetHealth(agent_id) > Agent.DEAD_HEALTH_EPSILON

        @staticmethod
        @frame_cache(category="Checks.Agents", source_lib="GetHealth")
        def GetHealth(agent_id: int) -> float:
            from ..Agent import Agent

            shared_agent_data = Checks.Agents._get_same_party_shared_agent_data(agent_id)
            if shared_agent_data is not None:
                return float(shared_agent_data.Health.Current)
            return float(Agent.GetHealth(agent_id))

        @staticmethod
        @frame_cache(category="Checks.Agents", source_lib="IsHexed")
        def IsHexed(agent_id: int) -> bool:
            from ..Agent import Agent

            shared_agent_data = Checks.Agents._get_same_party_shared_agent_data(agent_id)
            if shared_agent_data is not None:
                return bool(shared_agent_data.Is_Hexed)
            return Agent.IsHexed(agent_id)

        @staticmethod
        @frame_cache(category="Checks.Agents", source_lib="IsEnchanted")
        def IsEnchanted(agent_id: int) -> bool:
            from ..Agent import Agent

            shared_agent_data = Checks.Agents._get_same_party_shared_agent_data(agent_id)
            if shared_agent_data is not None:
                return bool(shared_agent_data.Is_Enchanted)
            return Agent.IsEnchanted(agent_id)

        @staticmethod
        @frame_cache(category="Checks.Agents", source_lib="IsConditioned")
        def IsConditioned(agent_id: int) -> bool:
            from ..Agent import Agent

            shared_agent_data = Checks.Agents._get_same_party_shared_agent_data(agent_id)
            if shared_agent_data is not None:
                return bool(shared_agent_data.Is_Conditioned)
            return Agent.IsConditioned(agent_id)

        @staticmethod
        @frame_cache(category="Checks.Agents", source_lib="IsAttacking")
        def IsAttacking(agent_id: int) -> bool:
            from ..Agent import Agent

            shared_agent_data = Checks.Agents._get_same_party_shared_agent_data(agent_id)
            if shared_agent_data is not None:
                return int(shared_agent_data.AnimationCode) == 2
            return Agent.IsAttacking(agent_id)

        @staticmethod
        @frame_cache(category="Checks.Agents", source_lib="IsKnockedDown")
        def IsKnockedDown(agent_id: int) -> bool:
            from ..Agent import Agent

            shared_agent_data = Checks.Agents._get_same_party_shared_agent_data(agent_id)
            if shared_agent_data is not None:
                return bool(shared_agent_data.ModelState & 0x400)
            return Agent.IsKnockedDown(agent_id)

        @staticmethod
        @frame_cache(category="Checks.Agents", source_lib="IsWeaponSpelled")
        def IsWeaponSpelled(agent_id: int) -> bool:
            from ..Agent import Agent

            shared_agent_data = Checks.Agents._get_same_party_shared_agent_data(agent_id)
            if shared_agent_data is not None:
                return bool(shared_agent_data.Is_WeaponSpelled)
            return Agent.IsWeaponSpelled(agent_id)

        @staticmethod
        @frame_cache(category="Checks.Agents", source_lib="HasIllusionaryWeaponry")
        def HasIllusionaryWeaponry(agent_id: int) -> bool:
            from ..Skill import Skill

            iw_skill_ids = (
                Skill.GetID("Illusionary_Weaponry"),
                Skill.GetID("Illusionary_Weaponry_(PVP)"),
            )
            for skill_id in iw_skill_ids:
                if not skill_id:
                    continue
                if (
                    Checks.Agents.HasEffect(agent_id, skill_id)
                    or Checks.Agents._shared_agent_has_skill_equipped(agent_id, skill_id)
                ):
                    return True
            return False

        @staticmethod
        @frame_cache(category="Checks.Agents", source_lib="IsMartial")
        def IsMartial(agent_id: int) -> bool:
            from ..Agent import Agent

            if Agent.IsPet(agent_id):
                return True

            if Checks.Agents.HasIllusionaryWeaponry(agent_id):
                return False

            weapon_type, weapon_name = Checks.Agents._get_shared_weapon_name(agent_id)
            if weapon_type == 0:
                return False

            return weapon_name in {"Bow", "Axe", "Hammer", "Daggers", "Scythe", "Spear", "Sword"}

        @staticmethod
        @frame_cache(category="Checks.Agents", source_lib="IsCaster")
        def IsCaster(agent_id: int) -> bool:
            from ..Agent import Agent

            if Agent.IsPet(agent_id):
                return False

            caster_weapon_types = {"Wand", "Staff", "Staff1", "Staff2", "Staff3", "Scepter", "Scepter2"}
            weapon_type, weapon_name = Checks.Agents._get_shared_weapon_name(agent_id)
            if weapon_type == 0 or weapon_name == "Unknown":
                return False

            return weapon_name in caster_weapon_types

        @staticmethod
        @frame_cache(category="Checks.Agents", source_lib="IsMelee")
        def IsMelee(agent_id: int) -> bool:
            from ..Agent import Agent

            if Agent.IsPet(agent_id):
                return True

            if Checks.Agents.HasIllusionaryWeaponry(agent_id):
                return False

            weapon_type, weapon_name = Checks.Agents._get_shared_weapon_name(agent_id)
            if weapon_type == 0:
                return False

            return weapon_name in {"Axe", "Hammer", "Daggers", "Scythe", "Sword"}

        @staticmethod
        @frame_cache(category="Checks.Agents", source_lib="IsRanged")
        def IsRanged(agent_id: int) -> bool:
            from ..Agent import Agent

            if Agent.IsPet(agent_id):
                return False

            weapon_type, weapon_name = Checks.Agents._get_shared_weapon_name(agent_id)
            if weapon_type == 0:
                return False

            return weapon_name in {"Bow", "Spear"}

        @staticmethod
        @frame_cache(category="Checks.Agents", source_lib="InDanger")
        def InDanger(aggro_area=Range.Earshot, aggressive_only = False):
            from ..AgentArray import AgentArray
            from ..Agent import Agent
            from ..EnemyBlacklist import EnemyBlacklist
            if not Checks.Map.MapValid():
                return False

            enemy_array = AgentArray.GetEnemyArray()
            if not enemy_array:
                return False

            player_id = Player.GetAgentID()
            player_pos = Player.GetXY()
            if not player_pos:
                return False

            radius = aggro_area.value if hasattr(aggro_area, "value") else float(aggro_area)
            radius_sq = radius * radius
            px, py = player_pos

            # Local bindings reduce attribute lookup overhead in this hot loop.
            get_xy = Agent.GetXY
            is_alive = Agent.IsAlive
            is_aggressive = Agent.IsAggressive

            bl = EnemyBlacklist()
            bl_empty = bl.is_empty()

            for agent_id in enemy_array:
                if agent_id == player_id:
                    continue
                if not is_alive(agent_id):
                    continue
                if aggressive_only and not is_aggressive(agent_id):
                    continue
                if not bl_empty and bl.is_blacklisted(agent_id):
                    continue

                enemy_pos = get_xy(agent_id)
                if not enemy_pos:
                    continue

                dx = px - enemy_pos[0]
                dy = py - enemy_pos[1]
                if (dx * dx + dy * dy) <= radius_sq:
                    return True

            return False

        @staticmethod
        @frame_cache(category="Checks.Agents", source_lib="InAggro")
        def InAggro(aggro_area=Range.Earshot.value, aggressive_only = False):
            from ..AgentArray import AgentArray
            from ..Agent import Agent
            if not Checks.Map.MapValid():
                return False

            enemy_array = AgentArray.GetEnemyArray()
            if not enemy_array:
                return False

            player_id = Player.GetAgentID()
            player_pos = Player.GetXY()
            if not player_pos:
                return False

            radius_sq = aggro_area * aggro_area
            px, py = player_pos

            get_xy = Agent.GetXY
            is_alive = Agent.IsAlive
            is_aggressive = Agent.IsAggressive

            for agent_id in enemy_array:
                if agent_id == player_id:
                    continue
                if not is_alive(agent_id):
                    continue
                if aggressive_only and not is_aggressive(agent_id):
                    continue

                enemy_pos = get_xy(agent_id)
                if not enemy_pos:
                    continue

                dx = px - enemy_pos[0]
                dy = py - enemy_pos[1]
                if (dx * dx + dy * dy) <= radius_sq:
                    return True

            return False

        @staticmethod
        @frame_cache(category="Checks.Agents", source_lib="IsCloseToAggro")
        def IsCloseToAggro() -> bool:
            """
            Returns True when combat is imminent but the player is not yet
            engaged. True when either:
              - the party leader has an aggressive enemy within Spellcast+400
                or any enemy within Spellcast, OR
              - a non-aggressive enemy is within Spellcast+350 of the player.
            Use this to gate upkeep and pre-engagement casts so they fire
            before aggro lands.
            """
            from ..AgentArray import AgentArray
            from ..Agent import Agent
            from ..Party import Party
            from ..enums_src.GameData_enums import Range

            if not Checks.Map.MapValid():
                return False
            enemy_array = AgentArray.GetEnemyArray()
            if not enemy_array:
                return False

            player_pos = Player.GetXY()
            if not player_pos:
                return False
            px, py = player_pos

            leader_id = Party.GetPartyLeaderID()
            leader_pos = Agent.GetXY(leader_id) if leader_id and Agent.IsValid(leader_id) else None

            spellcast = Range.Spellcast.value
            r_leader_aggressive_sq = (spellcast + 400) * (spellcast + 400)
            r_leader_any_sq = spellcast * spellcast
            r_player_close_sq = (spellcast + 350) * (spellcast + 350)

            for enemy_id in enemy_array:
                if not Agent.IsAlive(enemy_id):
                    continue
                enemy_pos = Agent.GetXY(enemy_id)
                if not enemy_pos:
                    continue
                ex, ey = enemy_pos
                is_aggressive = Agent.IsAggressive(enemy_id)

                if not is_aggressive:
                    dx = px - ex
                    dy = py - ey
                    if (dx * dx + dy * dy) <= r_player_close_sq:
                        return True

                if leader_pos is not None:
                    ldx = leader_pos[0] - ex
                    ldy = leader_pos[1] - ey
                    leader_dist_sq = ldx * ldx + ldy * ldy
                    if is_aggressive and leader_dist_sq <= r_leader_aggressive_sq:
                        return True
                    if leader_dist_sq <= r_leader_any_sq:
                        return True

            return False


        @staticmethod
        @frame_cache(category="Checks.Agents", source_lib="IsEnemyBehind")
        def IsEnemyBehind (agent_id):
            from ..GlobalCache import GLOBAL_CACHE
            from ..Agent import Agent
            import math
            player_agent_id = Player.GetAgentID()
            target = Player.GetTargetID()
            player_x, player_y = Agent.GetXY(player_agent_id)
            player_angle = Agent.GetRotationAngle(player_agent_id)  # Player's facing direction
            nearest_enemy = agent_id
            if target == 0:
                Player.ChangeTarget(nearest_enemy)
                target = nearest_enemy
            nearest_enemy_x, nearest_enemy_y = Agent.GetXY(nearest_enemy)
                        

            # Calculate the angle between the player and the enemy
            dx = nearest_enemy_x - player_x
            dy = nearest_enemy_y - player_y
            angle_to_enemy = math.atan2(dy, dx)  # Angle in radians
            angle_to_enemy = math.degrees(angle_to_enemy)  # Convert to degrees
            angle_to_enemy = (angle_to_enemy + 360) % 360  # Normalize to [0, 360]

            # Calculate the relative angle to the enemy
            angle_diff = (angle_to_enemy - player_angle + 360) % 360

            if angle_diff < 90 or angle_diff > 270:
                return True
            return False
        
        @staticmethod
        @frame_cache(category="Checks.Agents", source_lib="IsValidItem")
        def IsValidItem(item_id):
            from ..GlobalCache import GLOBAL_CACHE
            from ..Agent import Agent
            owner = Agent.GetItemAgentOwnerID(item_id)
            return (owner == Player.GetAgentID()) or (owner == 0)
        
        @staticmethod
        @frame_cache(category="Checks.Agents", source_lib="GetBuffs")
        def GetBuffs(agent_id: int):
            shared_agent_data = Checks.Agents._get_same_party_shared_agent_data(agent_id)
            if shared_agent_data is None:
                return []
            return [b for b in shared_agent_data.Buffs.Buffs if int(b.SkillId) > 0]

        @staticmethod
        @frame_cache(category="Checks.Agents", source_lib="HasEffect")
        def HasEffect(agent_id, skill_id, exact_weapon_spell=False):
            from ..GlobalCache import GLOBAL_CACHE
            from ..Skill import Skill
            from ..Agent import Agent

            if not agent_id or not skill_id:
                return False

            result = False

            shared_agent_data = Checks.Agents._get_same_party_shared_agent_data(agent_id)
            if shared_agent_data is not None:
                result = any(buff.SkillId == skill_id for buff in shared_agent_data.Buffs.Buffs)

            if not result:
                result = GLOBAL_CACHE.Effects.HasEffect(agent_id, skill_id)

            if not result and not exact_weapon_spell:
                skilltype, _ = Skill.GetType(skill_id)
                if skilltype == 25: #SkillType.WeaponSpell.value:
                    result = Checks.Agents.IsWeaponSpelled(agent_id)

            return result

#region Skills
    class Skills:
        @staticmethod
        def HasEnoughEnergy(agent_id, skill_id):
            """
            Purpose: Check if the player has enough energy to use the skill.
            Args:
                agent_id (int): The agent ID of the player.
                skill_id (int): The skill ID to check.
            Returns: bool
            """
            from ..Agent import Agent
            player_energy = Agent.GetEnergy(agent_id) * Agent.GetMaxEnergy(agent_id)
            skill_energy = Checks.Skills.GetEnergyCostWithEffects(skill_id, agent_id)
            return player_energy >= skill_energy
        
        @staticmethod
        def HasEnoughLife(agent_id, skill_id):
            """
            Purpose: Check if the player has enough life to use the skill.
            Args:
                agent_id (int): The agent ID of the player.
                skill_id (int): The skill ID to check.
            Returns: bool
            """
            from ..GlobalCache import GLOBAL_CACHE
            from ..Agent import Agent
            player_life = Agent.GetHealth(agent_id)
            skill_life = GLOBAL_CACHE.Skill.Data.GetHealthCost(skill_id)
            return player_life > skill_life

        @staticmethod
        def HasEnoughAdrenalineBySlot(skill_slot):
            """
            Purpose: Check if the equipped skill in the given slot has enough adrenaline.
            Args:
                skill_slot (int): The 1-based skill slot to check.
            Returns: bool
            """
            from ..GlobalCache import GLOBAL_CACHE

            if not (1 <= skill_slot <= 8):
                return False

            skill_id = int(GLOBAL_CACHE.SkillBar.GetSkillIDBySlot(skill_slot) or 0)
            if skill_id == 0:
                return False

            skill_adrenaline = int(GLOBAL_CACHE.Skill.Data.GetAdrenaline(skill_id) or 0)
            if skill_adrenaline == 0:
                return True

            skillbar_data = GLOBAL_CACHE.SkillBar.GetSkillData(skill_slot)
            if skillbar_data is None:
                return False

            current_adrenaline = int(getattr(skillbar_data, "adrenaline_a", 0) or 0)
            return current_adrenaline >= skill_adrenaline

        @staticmethod
        def HasEnoughAdrenaline(agent_id, skill_id):
            """
            Purpose: Check if the player has enough adrenaline to use the skill.
            Args:
                agent_id (int): The agent ID of the player.
                skill_id (int): The skill ID to check.
            Returns: bool
            """
            from ..Skillbar import SkillBar

            slot = SkillBar.GetSlotBySkillID(skill_id)
            if not (1 <= slot <= 8):
                return False

            return Checks.Skills.HasEnoughAdrenalineBySlot(slot)

        @staticmethod
        def DaggerStatusPass(agent_id, skill_id):
            """
            Purpose: Check if the player attack dagger status match tha skill requirement.
            Args:
                agent_id (int): The agent ID of the player.
                skill_id (int): The skill ID to check.
            Returns: bool
            """
            from ..GlobalCache import GLOBAL_CACHE
            from ..Agent import Agent
            dagger_status = Agent.GetDaggerStatus(agent_id)
            skill_combo = GLOBAL_CACHE.Skill.Data.GetCombo(skill_id)

            if skill_combo == 1 and (dagger_status != 0 and dagger_status != 3):
                return False

            if skill_combo == 2 and dagger_status != 1:
                return False

            if skill_combo == 3 and dagger_status != 2:
                return False

            return True
        
        @staticmethod
        def IsSkillIDReady(skill_id):
            from ..GlobalCache import GLOBAL_CACHE
            slot = GLOBAL_CACHE.SkillBar.GetSlotBySkillID(skill_id)
            return Checks.Skills.IsSkillSlotReady(slot)


        @staticmethod
        def IsSkillSlotReady(skill_slot):
            from ..GlobalCache import GLOBAL_CACHE
            if skill_slot <= 0 or skill_slot > 8:
                return False
            skill = GLOBAL_CACHE.SkillBar.GetSkillData(skill_slot)
            return skill.recharge == 0
        
        @staticmethod    
        def CanCast():
            if not Checks.Map.MapValid():
                return False
            
            from ..GlobalCache import GLOBAL_CACHE
            player_agent_id = Player.GetAgentID()

            if (
                Checks.Player.IsCasting() or
                Checks.Player.IsDead() or
                Checks.Player.IsKnockedDown() or
                GLOBAL_CACHE.SkillBar.GetCasting() != 0
            ):
                return False
            return True
        
        @staticmethod
        def InCastingProcess():
            from ..GlobalCache import GLOBAL_CACHE
            from ..Agent import Agent
            player_agent_id = Player.GetAgentID()
            if Agent.IsCasting(player_agent_id) or GLOBAL_CACHE.SkillBar.GetCasting() != 0:
                return True
            return False
        
        @staticmethod
        def apply_fast_casting(skill_id: int, fast_casting_level =0) -> Tuple[float, float]:
            """
            Applies Fast Casting effects for cast time and recharge time, following exact in-game mechanics.

            :param agent_id: ID of the agent using the skill.
            :param skill_id: ID of the skill being evaluated.
            :return: (adjusted_cast_time, adjusted_recharge_time)
            """
            from ..GlobalCache import GLOBAL_CACHE
            activation_time = GLOBAL_CACHE.Skill.Data.GetActivation(skill_id)
            recharge_time = GLOBAL_CACHE.Skill.Data.GetRecharge(skill_id)
            
            #return activation_time, recharge_time

            if fast_casting_level <= 0:
                return activation_time, recharge_time

            # Get skill type and professions
            is_spell = GLOBAL_CACHE.Skill.Flags.IsSpell(skill_id)
            is_signet = GLOBAL_CACHE.Skill.Flags.IsSignet(skill_id)
            _, skill_profession = GLOBAL_CACHE.Skill.GetProfession(skill_id)

            # --- CAST TIME REDUCTION ---
            if is_spell or is_signet:
                # Mesmer spells/signets → always affected
                if skill_profession == "Mesmer":
                    activation_time *= 0.955 ** fast_casting_level
                    activation_time = round(activation_time, 3)
                # Non-Mesmer spells/signets → only affected if cast time >= 2s
                elif activation_time >= 2.0:
                    activation_time *= 0.955 ** fast_casting_level
                    activation_time = round(activation_time, 3)

            # --- RECHARGE TIME REDUCTION ---
            if skill_profession == "Mesmer" and is_spell:
                recharge_time *= (1.0 - 0.03 * fast_casting_level)
                recharge_time = round(recharge_time)

            return activation_time, recharge_time


        
        @staticmethod
        def apply_expertise_reduction(base_cost: int, expertise_level: int, skill_id) -> int:
            """
            Applies the Guild Wars expertise cost reduction correctly.
            
            :param base_cost: The original energy cost of the skill.
            :param expertise_level: The level of Expertise (0-20).
            :return: The reduced cost, rounded down to an integer.
            """
            from ..GlobalCache import GLOBAL_CACHE
            from ..Agent import Agent
            from ..enums_src.GameData_enums import Profession_Names

            player_id = Player.GetAgentID()
            primary_profession, _ = Agent.GetProfessionNames(player_id)

            if (primary_profession != "Ranger"):
                return base_cost

            skill_type, _ = GLOBAL_CACHE.Skill.GetType(skill_id)
            _, skill_profession = GLOBAL_CACHE.Skill.GetProfession(skill_id)
            if (skill_type == 14 or #attack skills
                GLOBAL_CACHE.Skill.Flags.IsRitual(skill_id) or
                GLOBAL_CACHE.Skill.Flags.IsTouchRange(skill_id) or
                skill_profession == "Ranger"):

                EXPERTISE_REDUCTION = [
                    1.00, 0.96, 0.92, 0.88, 0.84, 0.80, 0.76, 0.72, 0.68, 0.64, 0.60,
                    0.56, 0.52, 0.48, 0.44, 0.40, 0.36, 0.32, 0.28, 0.24, 0.20
                ]
                if expertise_level < 0 or expertise_level > 20:
                    expertise_level = max(0, min(expertise_level, 20))  # clamp
                reduction_factor = EXPERTISE_REDUCTION[expertise_level]
                return max(0, int(base_cost * reduction_factor))  # floor after applying
            
            return base_cost  # No reduction for other skills

        
        @staticmethod
        def GetEnergyCostWithEffects(skill_id, agent_id):
            """Retrieve the actual energy cost of a skill by its ID and effects.

            Args:
                skill_id (int): ID of the skill.
                agent_id (int): ID of the agent (player or hero).

            Returns:
                float: Final energy cost after applying all effects.
                    Values are rounded to integers.
                    Minimum cost is 0 unless otherwise specified by an effect.
            """
            from ..GlobalCache import GLOBAL_CACHE
            # Get base energy cost for the skill
            cost = GLOBAL_CACHE.Skill.Data.GetEnergyCost(skill_id)
            
            # Get all active effects on the agent
            player_effects = GLOBAL_CACHE.Effects.GetEffects(agent_id)

            # Process each effect in order of application
            # Effects are processed in this specific order to match game mechanics
            for effect in player_effects:
                effect_id = effect.skill_id
                attr = GLOBAL_CACHE.Effects.EffectAttributeLevel(agent_id, effect_id)

                match effect_id:
                    case 469:  # Primal Echoes - Forces Signets to cost 10 energy
                        if GLOBAL_CACHE.Skill.Flags.IsSignet(skill_id):
                            cost = 10  # Fixed cost regardless of other effects
                            continue  # Allow other effects to modify this cost

                    case 475:  # Quickening Zephyr - Increases energy cost by 30%
                        cost *= 1.30   # Using multiplication instead of addition for better precision
                        continue

                    case 1725:  # Roaring Winds - Increases Shout/Chant cost based on attribute level
                        if GLOBAL_CACHE.Skill.Flags.IsChant(skill_id) or GLOBAL_CACHE.Skill.Flags.IsShout(skill_id):
                            match attr:
                                case a if 0 < a <= 1:
                                    cost += 1
                                case a if 2 <= a <= 5:
                                    cost += 2
                                case a if 6 <= a <= 9:
                                    cost += 3
                                case a if 10 <= a <= 13:
                                    cost += 4
                                case a if 14 <= a <= 16:
                                    cost += 5
                                case a if 17 <= a <= 20:
                                    cost += 6
                            continue

                    case 1677:  # Veiled Nightmare - Increases all costs by 40%
                        cost *= 1.40
                        continue

                    case 856:  # "Kilroy Stonekin" - Reduces all costs by 50%
                        cost *= 0.50
                        continue

                    case 1115:  # Air of Enchantment
                        if GLOBAL_CACHE.Skill.Flags.IsEnchantment(skill_id):
                            cost -= 5
                        continue

                    case 1223:  # Anguished Was Lingwah
                        if GLOBAL_CACHE.Skill.Flags.IsHex(skill_id) and GLOBAL_CACHE.Skill.GetProfession(skill_id)[0] == 8:
                            match attr:
                                case a if 0 < a <= 1:
                                    cost -= 1
                                case a if 2 <= a <= 5:
                                    cost -= 2
                                case a if 6 <= a <= 9:
                                    cost -= 3
                                case a if 10 <= a <= 13:
                                    cost -= 4
                                case a if 14 <= a <= 16:
                                    cost -= 5
                                case a if 17 <= a <= 20:
                                    cost -= 6
                                case a if a > 20:
                                    cost -= 7
                            continue

                    case 1220:  # Attuned Was Songkai
                        if GLOBAL_CACHE.Skill.Flags.IsSpell(skill_id) or GLOBAL_CACHE.Skill.Flags.IsRitual(skill_id):
                            percentage = 5 + (attr * 3) if attr <= 20 else 68
                            cost -= cost * (percentage / 100)
                        continue

                    case 596:  # Chimera of Intensity
                        cost -= cost * 0.50
                        continue

                    case 806:  # Cultist's Fervor
                        if GLOBAL_CACHE.Skill.Flags.IsSpell(skill_id) and GLOBAL_CACHE.Skill.GetProfession(skill_id)[0] == 4:
                            match attr:
                                case a if 0 < a <= 1:
                                    cost -= 1
                                case a if 2 <= a <= 4:
                                    cost -= 2
                                case a if 5 <= a <= 7:
                                    cost -= 3
                                case a if 8 <= a <= 10:
                                    cost -= 4
                                case a if 11 <= a <= 13:
                                    cost -= 5
                                case a if 14 <= a <= 16:
                                    cost -= 6
                                case a if 17 <= a <= 19:
                                    cost -= 7
                                case a if a > 19:
                                    cost -= 8
                            continue

                    case 310:  # Divine Spirit
                        if GLOBAL_CACHE.Skill.Flags.IsSpell(skill_id) and GLOBAL_CACHE.Skill.GetProfession(skill_id)[0] == 3:
                            cost -= 5
                        continue

                    case 1569:  # Energizing Chorus
                        if GLOBAL_CACHE.Skill.Flags.IsChant(skill_id) or GLOBAL_CACHE.Skill.Flags.IsShout(skill_id):
                            match attr:
                                case a if 0 < a <= 1:
                                    cost -= 3
                                case a if 2 <= a <= 5:
                                    cost -= 4
                                case a if 6 <= a <= 9:
                                    cost -= 5
                                case a if 10 <= a <= 13:
                                    cost -= 6
                                case a if 14 <= a <= 16:
                                    cost -= 7
                                case a if 17 <= a <= 20:
                                    cost -= 8
                                case a if a > 20:
                                    cost -= 9
                            continue

                    case 474:  # Energizing Wind
                        if cost >= 15:
                            cost -= 15
                        else:
                            cost = 0
                        continue

                    case 2145:  # Expert Focus
                        if GLOBAL_CACHE.Skill.Flags.IsAttack(skill_id) and GLOBAL_CACHE.Skill.Data.GetWeaponReq(skill_id) == 2:
                            match attr:
                                case a if 0 < a <= 7:
                                    cost -= 1
                                case a if a > 8:
                                    cost -= 2
                                

                    case 199:  # Glyph of Energy
                        if GLOBAL_CACHE.Skill.Flags.IsSpell(skill_id):
                            if attr == 0:
                                cost -= 10
                            else:
                                cost -= (10 + attr)

                    case 200:  # Glyph of Lesser Energy
                        if GLOBAL_CACHE.Skill.Flags.IsSpell(skill_id):
                            match attr:
                                case 0:
                                    cost -= 10
                                case a if 1 <= a <= 2:
                                    cost -= 11
                                case a if 3 <= a <= 4:
                                    cost -= 12
                                case a if 5 <= a <= 6:
                                    cost -= 13
                                case a if 7 <= a <= 8:
                                    cost -= 14
                                case a if 9 <= a <= 10:
                                    cost -= 15
                                case a if 11 <= a <= 12:
                                    cost -= 16
                                case a if 13 <= a <= 14:
                                    cost -= 17
                                case 15:
                                    cost -= 18
                                case a if 16 <= a <= 16:
                                    cost -= 19
                                case a if 17 <= a <= 18:
                                    cost -= 20
                                case a if a >= 20:
                                    cost -= 21

                    case 1394:  # Healer's Covenant
                        if GLOBAL_CACHE.Skill.Flags.IsSpell(skill_id) and GLOBAL_CACHE.Skill.Attribute.GetAttribute(skill_id).attribute_id == 15:
                            match attr:
                                case a if 0 < a <= 3:
                                    cost -= 1
                                case a if 4 <= a <= 11:
                                    cost -= 2
                                case a if 12 <= a <= 18:
                                    cost -= 3
                                case a if a >= 19:
                                    cost -= 4

                    case 763:  # Jaundiced Gaze
                        if GLOBAL_CACHE.Skill.Flags.IsEnchantment(skill_id):
                            match attr:
                                case 0:
                                    cost -= 1
                                case a if 1 <= a <= 2:
                                    cost -= 2
                                case a if 3 <= a <= 4:
                                    cost -= 3
                                case 5:
                                    cost -= 4
                                case a if 6 <= a <= 7:
                                    cost -= 5
                                case a if 8 <= a <= 9:
                                    cost -= 6
                                case 10:
                                    cost -= 7
                                case a if 11 <= a <= 12:
                                    cost -= 8
                                case a if 13 <= a <= 14:
                                    cost -= 9
                                case 15:
                                    cost -= 10
                                case a if 16 <= a <= 17:
                                    cost -= 11
                                case a if 18 <= a <= 19:
                                    cost -= 12
                                case 20:
                                    cost -= 13
                                case a if a > 20:
                                    cost -= 14

                    case 1739:  # Renewing Memories
                        if GLOBAL_CACHE.Skill.Flags.IsItemSpell(skill_id) or GLOBAL_CACHE.Skill.Flags.IsWeaponSpell(skill_id):
                            percentage = 5 + (attr * 2) if attr <= 20 else 47
                            cost -= cost * (percentage / 100)

                    case 1240:  # Soul Twisting
                        if GLOBAL_CACHE.Skill.Flags.IsRitual(skill_id):
                            cost = 10  # Fixe le coût à 10

                    case 987:  # Way of the Empty Palm
                        if GLOBAL_CACHE.Skill.Data.GetCombo(skill_id) == 2 or GLOBAL_CACHE.Skill.Data.GetCombo(skill_id) == 3:  # Attaque double ou secondaire
                            cost = 0

            cost = max(0, cost)

            return cost
