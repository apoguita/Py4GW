
from .Context import GWContext
from .native_src.methods.MapMethods import MapMethods
from .enums_src.Region_enums import (ServerRegionName, ServerLanguageName, RegionTypeName, 
                                     ContinentName, CampaignName,)

from .enums_src.Map_enums import (InstanceTypeName)
from .native_src.internals.types import Vec2f
from Py4GWCoreLib.py4gwcorelib_src.ActionQueue import ActionQueueManager
from Py4GWCoreLib.enums import outposts


import PyPathing
import PyOverlay

from .enums import FlagPreference
from typing import List
from .UIManager import UIManager,WindowFrames, FrameInfo
from .Overlay import *
import math

"""Map-related functionalities and utilities.

classes:
    Map: A class providing static methods to interact with and retrieve information about the game map.
    |_ MissionMap: A nested class within Map that offers methods specific to mission map operations.
    |_ MiniMap: A nested class within Map that offers methods specific to mini map operations.
    |_ Pathing: A nested class within Map that offers methods specific to pathing map operations.

"""

class Map:
    #region Instance_Type
    @staticmethod
    def GetInstanceType() -> int:
        """Retrieve the instance type of the current map."""
        if not (instance_info := GWContext.InstanceInfo.GetContext()):
            return 2  # Loading
        return instance_info.instance_type
    
    @staticmethod
    def GetInstanceTypeName() -> str:
        """Retrieve the instance type name of the current map."""
        type = Map.GetInstanceType()
        return InstanceTypeName.get(type, "Loading")

    @staticmethod
    def IsOutpost() -> bool:
        """Check if the map instance is an outpost."""
        return Map.GetInstanceTypeName() == "Outpost"

    @staticmethod
    def IsExplorable() -> bool:
        """Check if the map instance is explorable."""
        return Map.GetInstanceTypeName() == "Explorable"

    @staticmethod
    def IsMapLoading() -> bool:
        """Check if the map instance is loading."""
        return Map.GetInstanceTypeName() == "Loading"
    
    @staticmethod
    def IsMapDataLoaded() -> bool:
        """Check if the map data is loaded."""
        if not (GWContext.Map.IsValid()): return False
        return True
    
    @staticmethod
    def IsObservingMatch() -> bool:
        """Check if the character is observing a match."""
        if not (char_context := GWContext.Char.GetContext()): return False
        return char_context.current_map_id != char_context.observe_map_id
    
    @staticmethod
    def IsMapReady() -> bool:
        """Check if the map is ready to be handled."""  
        map_data_loaded = Map.IsMapDataLoaded()
        is_observing = Map.IsObservingMatch()
        is_map_loading = Map.IsMapLoading()
        return map_data_loaded and not is_observing and not is_map_loading
    
    #region Data
    @staticmethod
    def GetMapID() -> int:
        """Retrieve the ID of the current map."""
        if not (char_context :=  GWContext.Char.GetContext()): return 0
        return char_context.current_map_id
    
    @staticmethod
    def GetOutpostIDs():
        """Retrieve the outpost IDs."""
        global outposts
        return list(outposts.keys())
    
    @staticmethod
    def GetOutpostNames():
        """Retrieve the outpost names."""
        global outposts
        return list(outposts.values())
    
    
    @staticmethod
    def GetMapName(mapid=None) -> str:
        """
        Retrieve the name of a map by its ID.
        Args:
            mapid (int, optional): The ID of the map to retrieve. Defaults to the current map.
        Returns: str
        """
        from .enums_src.Map_enums import outposts, explorables

        if mapid is None:
            map_id = Map.GetMapID()
        else:
            map_id = mapid

        if map_id in outposts:
            return outposts[map_id]
        if map_id in explorables:
            return explorables[map_id]

        return "Unknown Map ID"
    
    @staticmethod
    def GetMapIDByName(name: str) -> int:
        """
        Retrieve the ID of a map (outpost or explorable) by its name.
        Case-insensitive. Returns 0 if not found.
        """
        from .enums_src.Map_enums import outposts, explorables

        # Normalize lookup key
        key = name.lower()

        catalog: dict[str, int] = {}

        # build lowercase-name -> id dictionary
        for id, nm in outposts.items():
            catalog[nm.lower()] = id

        for id, nm in explorables.items():
            catalog[nm.lower()] = id

        return int(catalog.get(key, 0))
    
    @staticmethod
    def GetInstanceUptime() -> int:
        """Retrieve the uptime of the current instance."""
        if not (agent_context := GWContext.AccAgent.GetContext()):
            return 0
        return agent_context.instance_timer
    
    @staticmethod
    def GetRegion() -> tuple[int, str]:
        """Retrieve the region ID and name of the current server region.
        Returns:
            tuple[int, str]: A tuple containing the region ID and its corresponding name.
        """
        if not (region_ctx := GWContext.ServerRegion.GetContext()):
            return 255, ServerRegionName[255]
        
        return region_ctx.region_id, ServerRegionName[region_ctx.region_id]

    
    @staticmethod
    def GetRegionType() -> tuple[int, str]:
        """
        Retrieve the region type of the current map.
        Args: None
        Returns: tuple (int, str)
        """
        _unknown_region_type = 20  # Unknown
        current_map_info = GWContext.InstanceInfo().GetMapInfo()
        if current_map_info is None:
            return _unknown_region_type, RegionTypeName[_unknown_region_type]  # Unknown
        
        return current_map_info.type, RegionTypeName[current_map_info.type]
    
    @staticmethod
    def GetDistrict() -> int:
        """Retrieve the district of the current map."""
        if not (char_context :=  GWContext.Char.GetContext()): return -1
        return char_context.district_number
    
    @staticmethod
    def GetLanguage() -> tuple[int, str]:
        """
        Retrieve the language of the current map.
        Args: None
        Returns: tuple (int, str)
        """
        unknown_language = 255  # Unknown
        lang_dict = ServerLanguageName
        
        if not (char_context := GWContext.Char.GetContext()):
            return unknown_language, lang_dict[unknown_language]

        language = char_context.language

        # validate the value
        if language not in lang_dict:
            language = unknown_language

        # now return the validated language
        return language, lang_dict[language]
    

    @staticmethod
    def GetAmountOfPlayersInInstance():
        """Retrieve the amount of players in the current instance."""
        if not (world_ctx := GWContext.World.GetContext()):
            return 0
        players = world_ctx.players
        if not players:
            return 0
        return len(players) -1
    
    @staticmethod
    def GetMaxPartySize() -> int:
        """ Retrieve the maximum party size of the current map."""
        current_map_info = GWContext.InstanceInfo().GetMapInfo()
        if current_map_info is None:
            return 0
        
        return current_map_info.max_party_size
    
    @staticmethod
    def GetMinPartySize() -> int:
        """ Retrieve the minimum party size of the current map."""
        current_map_info = GWContext.InstanceInfo().GetMapInfo()
        if current_map_info is None:
            return 0
        
        return current_map_info.min_party_size
    
    @staticmethod
    def GetMinPlayerSize() -> int:
        """Retrieve the minimum player size of the current map."""
        current_map_info = GWContext.InstanceInfo().GetMapInfo()
        if current_map_info is None:
            return 0
        return current_map_info.min_player_size
    
    @staticmethod
    def GetMaxPlayerSize() -> int:
        """Retrieve the maximum player size of the current map."""
        current_map_info = GWContext.InstanceInfo().GetMapInfo()
        if current_map_info is None:
            return 0
        return current_map_info.max_player_size
    
    @staticmethod
    def GetFoesKilled() -> int:
        """
        Retrieve the number of foes killed in the current map.
        Args: None
        Returns: int
        """
        if not (world_ctx := GWContext.World.GetContext()):
            return 0
        return world_ctx.foes_killed

    @staticmethod
    def GetFoesToKill() -> int:
        """
        Retrieve the number of foes to kill in the current map.
        Args: None
        Returns: int
        """
        if not (world_ctx := GWContext.World.GetContext()):
            return 0
        return world_ctx.foes_to_kill
    
    @staticmethod
    def IsVanquishCompleted() -> bool:
        """Check if the vanquish is completed."""
        if Map.IsVanquishable():
            return Map.GetFoesToKill() == 0
        return False
    
    @staticmethod
    def IsInCinematic() -> bool:
        """Check if the map is in a cinematic."""
        if not (cinematic_ctx := GWContext.Cinematic.GetContext()):
            return False
        return cinematic_ctx.h0004 != 0
    
    @staticmethod
    def GetCampaign() -> tuple[int, str]:
        """
        Retrieve the campaign of the current map.
        Args: None
        Returns: tuple (int, str)
        """
        not_valid = 255
        current_map_info = GWContext.InstanceInfo().GetMapInfo()
        if current_map_info is None:
            return not_valid, CampaignName[not_valid]

        return current_map_info.campaign, CampaignName[current_map_info.campaign]

    @staticmethod
    def GetContinent() -> tuple[int, str]:
        """
        Retrieve the continent of the current map.
        Args: None
        Returns: tuple (int, str)
        """
        not_valid = 255
        current_map_info = GWContext.InstanceInfo().GetMapInfo()
        if current_map_info is None:
            return not_valid,ContinentName[not_valid]
        return current_map_info.continent, ContinentName[current_map_info.continent]

    @staticmethod
    def HasEnterChallengeButton() -> bool:
        """Check if the map has an enter challenge button."""
        current_map_info = GWContext.InstanceInfo().GetMapInfo()
        if current_map_info is None:
            return False
        return current_map_info.has_enter_button

    @staticmethod
    def IsOnWorldMap():
        """Check if the map is on the world map."""
        current_map_info = GWContext.InstanceInfo().GetMapInfo()
        if current_map_info is None:
            return False
        return current_map_info.is_on_world_map
    
    @staticmethod
    def IsPVP():
        """Check if the map is a PvP map."""
        current_map_info = GWContext.InstanceInfo().GetMapInfo()
        if current_map_info is None:
            return False
        return current_map_info.is_pvp
    
    @staticmethod
    def IsGuildHall():
        """Check if the map is a Guild Hall."""
        current_map_info = GWContext.InstanceInfo().GetMapInfo()
        if current_map_info is None:
            return False
        return current_map_info.is_guild_hall
    
    @staticmethod
    def IsVanquishable():
        """Check if the map is vanquishable."""
        current_map_info = GWContext.InstanceInfo().GetMapInfo()
        if current_map_info is None:
            return False
        return current_map_info.is_vanquishable_area
    
    @staticmethod
    def IsVanquishComplete() -> bool:
        """Check if the vanquish is complete."""
        if Map.IsVanquishable():
            return Map.GetFoesToKill() == 0
        return False
    
    @staticmethod
    def IsMapUnlocked(mapid: int | None = None) -> bool:
        """Check if the map is unlocked."""
        # Step 1: determine map_id
        map_id = Map.GetMapID() if mapid is None else mapid
        # Step 2: retrieve context
        world_ctx = GWContext.World.GetContext()
        if not world_ctx:
            return False
        # Step 3: fetch the underlying array
        unlocked_maps = world_ctx.unlocked_maps
        if not unlocked_maps or len(unlocked_maps) == 0:
            return False
        # Step 4: compute index (element in array)
        real_index = map_id // 32
        if real_index >= len(unlocked_maps):
            return False
        # Step 5: compute bit shift
        shift = map_id % 32
        # Step 6: compute bit flag
        flag = 1 << shift
        # Step 7: access array element and test
        # world_ctx.unlocked_maps is expected to behave like Array<uint32_t>
        value = unlocked_maps[real_index]  # becomes uint32_t automatically
        return (value & flag) != 0
    
    #region Additional Fields
    @staticmethod
    def GetFlags() -> int:
        """Retrieve the flags of the current map."""
        current_map_info = GWContext.InstanceInfo().GetMapInfo()
        if current_map_info is None:
            return 0
        return current_map_info.flags

    @staticmethod
    def GetMinLevel() -> int:
        """Retrieve the minimum level of the current map."""
        current_map_info = GWContext.InstanceInfo().GetMapInfo()
        if current_map_info is None:
            return 0
        return current_map_info.min_level
    
    @staticmethod
    def GetMaxLevel() -> int:
        """Retrieve the maximum level of the current map."""
        current_map_info = GWContext.InstanceInfo().GetMapInfo()
        if current_map_info is None:
            return 0
        return current_map_info.max_level
    
    @staticmethod
    def GetThumbnailID() -> int:
        """Retrieve the thumbnail ID of the current map."""
        current_map_info = GWContext.InstanceInfo().GetMapInfo()
        if current_map_info is None:
            return 0
        return current_map_info.thumbnail_id
    
    @staticmethod
    def GetControlledOutpostID() -> int:
        """Retrieve the controlled outpost ID of the current map."""
        current_map_info = GWContext.InstanceInfo().GetMapInfo()
        if current_map_info is None:
            return 0
        return current_map_info.controlled_outpost_id
    
    @staticmethod
    def GetFractionMission() -> int:
        """Retrieve the fraction mission of the current map."""
        current_map_info = GWContext.InstanceInfo().GetMapInfo()
        if current_map_info is None:
            return 0
        return current_map_info.fraction_mission
    
    @staticmethod
    def GetNeededPQ() -> int:
        """Retrieve the needed PQ of the current map."""
        current_map_info = GWContext.InstanceInfo().GetMapInfo()
        if current_map_info is None:
            return 0
        return current_map_info.needed_pq
    
    @staticmethod
    def HasMissionMapsTo() -> bool:
        """Check if the current map has mission maps to."""
        current_map_info = GWContext.InstanceInfo().GetMapInfo()
        if current_map_info is None:
            return False
        return current_map_info.mission_maps_to != 0
    
    @staticmethod
    def GetMissionMapsTo() -> int:
        """Retrieve the mission maps to of the current map."""
        current_map_info = GWContext.InstanceInfo().GetMapInfo()
        if current_map_info is None:
            return 0
        return current_map_info.mission_maps_to
    
    @staticmethod
    def GetIconPosition() -> tuple[int, int]:
        """Retrieve the icon position of the current map."""
        current_map_info = GWContext.InstanceInfo().GetMapInfo()
        if current_map_info is None:
            return 0, 0
        return current_map_info.x, current_map_info.y
    
    @staticmethod
    def GetIconStartPosition() -> tuple[int, int]:
        """Retrieve the icon start position of the current map."""
        current_map_info = GWContext.InstanceInfo().GetMapInfo()
        if current_map_info is None:
            return 0, 0
        return current_map_info.icon_start_x, current_map_info.icon_start_y
    
    @staticmethod
    def GetIconStartDupePosition() -> tuple[int, int]:
        """Retrieve the icon start dupe position of the current map."""
        current_map_info = GWContext.InstanceInfo().GetMapInfo()
        if current_map_info is None:
            return 0, 0
        return current_map_info.icon_start_x_dupe, current_map_info.icon_start_y_dupe
    
    @staticmethod
    def GetIconEndPosition() -> tuple[int, int]:
        """Retrieve the icon end position of the current map."""
        current_map_info = GWContext.InstanceInfo().GetMapInfo()
        if current_map_info is None:
            return 0, 0
        return current_map_info.icon_end_x, current_map_info.icon_end_y
    
    @staticmethod
    def GetIconEndDupePosition() -> tuple[int, int]:
        """Retrieve the icon end dupe position of the current map."""
        current_map_info = GWContext.InstanceInfo().GetMapInfo()
        if current_map_info is None:
            return 0, 0
        return current_map_info.icon_end_x_dupe, current_map_info.icon_end_y_dupe
    
    @staticmethod
    def GetFileID() -> int:
        """Retrieve the file ID of the current map."""
        current_map_info = GWContext.InstanceInfo().GetMapInfo()
        if current_map_info is None:
            return 0
        return current_map_info.file_id
    
    @staticmethod
    def GetMissionChronology() -> int:
        """Retrieve the mission chronology of the current map."""
        current_map_info = GWContext.InstanceInfo().GetMapInfo()
        if current_map_info is None:
            return 0
        return current_map_info.mission_chronology
    
    @staticmethod
    def GetHAChronology() -> int:
        """Retrieve the HA chronology of the current map."""
        current_map_info = GWContext.InstanceInfo().GetMapInfo()
        if current_map_info is None:
            return 0
        return current_map_info.ha_map_chronology
    
    @staticmethod
    def GetNameID() -> int:
        """Retrieve the name ID of the current map."""
        current_map_info = GWContext.InstanceInfo().GetMapInfo()
        if current_map_info is None:
            return 0
        return current_map_info.name_id
    
    @staticmethod
    def GetDescriptionID() -> int:
        """Retrieve the description ID of the current map."""
        current_map_info = GWContext.InstanceInfo().GetMapInfo()
        if current_map_info is None:
            return 0
        return current_map_info.description_id
    
    @staticmethod
    def GetFileID1() -> int:
        """Retrieve the file ID 1 of the current map."""
        current_map_info = GWContext.InstanceInfo().GetMapInfo()
        if current_map_info is None:
            return 0
        return current_map_info.file_id1
    
    @staticmethod
    def GetFileID2() -> int:
        """Retrieve the file ID 2 of the current map."""
        current_map_info = GWContext.InstanceInfo().GetMapInfo()
        if current_map_info is None:
            return 0
        return current_map_info.file_id2
    
    @staticmethod
    def IsUnlockable() -> bool:
        """Check if the current map is unlockable."""
        current_map_info = GWContext.InstanceInfo().GetMapInfo()
        if current_map_info is None:
            return False
        return current_map_info.is_unlockable
    
    @staticmethod
    def IsEnteringChallenge() -> bool:
        """Check if the character is entering a challenge."""
        from .UIManager import WindowFrames
        CancelEnterMissionButton = WindowFrames.get("CancelEnterMissionButton", None)
        if CancelEnterMissionButton is None:
            return False
        if not CancelEnterMissionButton.FrameExists():
            return False
        return True
    
    @staticmethod
    def GetMapWorldMapBounds() -> tuple[float, float, float, float]:
        icon_start: Vec2f = Vec2f(*Map.GetIconStartPosition())
        icon_end: Vec2f = Vec2f(*Map.GetIconEndPosition())
        icon_start_dupe: Vec2f = Vec2f(*Map.GetIconStartDupePosition())
        icon_end_dupe: Vec2f = Vec2f(*Map.GetIconEndDupePosition())

        if icon_start.x == 0 and icon_start.y == 0 and icon_end.x == 0 and icon_end.y == 0:
            left   = float(icon_start_dupe.x)
            top    = float(icon_start_dupe.y)
            right  = float(icon_end_dupe.x)
            bottom = float(icon_end_dupe.y)
        else:
            left   = float(icon_start.x)
            top    = float(icon_start.y)
            right  = float(icon_end.x)
            bottom = float(icon_end.y)

        return left, top, right, bottom   
    
    @staticmethod
    def GetMapBoundaries() -> tuple[float, float, float, float]:
        """Retrieve the map boundaries of the current map."""
        if not (map_ctx := GWContext.Map.GetContext()):
            return 0.0, 0.0, 0.0, 0.0
        
        boundaries = map_ctx.map_boundaries
        
        if len(boundaries) < 5:
            return 0.0, 0.0, 0.0, 0.0  # Optional: fallback for safety

        min_x = boundaries[1]
        min_y = boundaries[2]
        max_x = boundaries[3]
        max_y = boundaries[4]

        return min_x, min_y, max_x, max_y
        
    #region Functions
    @staticmethod
    def SkipCinematic():
        """ Skip the cinematic."""
        def _skip_cinematic() -> bool:
            return MapMethods.SkipCinematic()
        ActionQueueManager().AddAction("ACTION", _skip_cinematic)

        
    @staticmethod
    def Travel(map_id):
        """Travel to a map by its ID."""
        def _travel() -> bool:
            return MapMethods.Travel(map_id)
        ActionQueueManager().AddAction("ACTION", _travel)


    @staticmethod
    def TravelToDistrict(map_id, district=0, district_number=0):
        """
        Travel to a map by its ID and district.
        Args:
            map_id (int): The ID of the map to travel to.
            district (int): The district to travel to. (region)
            district_number (int): The number of the district to travel to.
        Returns: None
        """
        def _region_from_district(district: int) -> int:
            from .enums_src.Region_enums import District, ServerRegion
            
            if district == District.International.value:
                return ServerRegion.International.value
            if district == District.American.value:
                return ServerRegion.America.value
            if district in [District.EuropeEnglish.value,
                            District.EuropeFrench.value,
                            District.EuropeGerman.value,
                            District.EuropeItalian.value,
                            District.EuropeSpanish.value,
                            District.EuropePolish.value,
                            District.EuropeRussian.value]:
                return ServerRegion.Europe.value
            if district == District.AsiaKorean.value:
                return ServerRegion.Korea.value
            if district == District.AsiaChinese.value:
                return ServerRegion.China.value
            if district == District.AsiaJapanese.value:
                return ServerRegion.Japan.value
            
            return Map.GetRegion()[0]
        
        def _language_from_district(district: int) -> int:
            from .enums_src.Region_enums import District, ServerLanguage
            
            if district == District.EuropeFrench.value:
                return ServerLanguage.French.value
            if district == District.EuropeGerman.value:
                return ServerLanguage.German.value
            if district == District.EuropeItalian.value:
                return ServerLanguage.Italian.value
            if district == District.EuropeSpanish.value:
                return ServerLanguage.Spanish.value
            if district == District.EuropePolish.value:
                return ServerLanguage.Polish.value
            if district == District.EuropeRussian.value:
                return ServerLanguage.Russian.value
            if district in [District.EuropeEnglish.value,
                            District.AsiaKorean.value,
                            District.AsiaChinese.value,
                            District.AsiaJapanese.value,
                            District.International.value,
                            District.American.value]:
                return ServerLanguage.English.value
            return Map.GetLanguage()[0]

        def _travel_to_district() -> bool:
            return MapMethods.Travel(map_id, _region_from_district(district), district_number, _language_from_district(district))
        ActionQueueManager().AddAction("ACTION", _travel_to_district)

            
        #bool Travel(int map_id, int server_region, int district_number, int language);
    @staticmethod
    def TravelToRegion(map_id, server_region, district_number, language=0):
        """
        Travel to a map by its ID and region.
        Args:
            map_id (int): The ID of the map to travel to.
            server_region (int): The region to travel to.
            district_number (int): The number of the district to travel to.
            language (int): The language to travel to.
        Returns: None
        """
        def _travel_to_region() -> bool:
            return MapMethods.Travel(map_id, server_region, district_number, language)
        ActionQueueManager().AddAction("ACTION", _travel_to_region)

        
    @staticmethod
    def TravelGH():
        """Travel to the Guild Hall."""
        def _travel_gh() -> bool:
            return MapMethods.TravelGH()
        ActionQueueManager().AddAction("ACTION", _travel_gh)

        
    @staticmethod
    def LeaveGH():
        """Leave the Guild Hall."""
        def _leave_gh() -> bool:
            return MapMethods.LeaveGH()
        ActionQueueManager().AddAction("ACTION", _leave_gh)
        
    @staticmethod
    def EnterChallenge():
        """Enter the challenge."""
        def _enter_challenge() -> bool:   
            return MapMethods.EnterChallenge()
        ActionQueueManager().AddAction("ACTION", _enter_challenge)
        
    @staticmethod
    def CancelEnterChallenge():
        """Cancel entering the challenge."""
        def _cancel_enter_challenge() -> bool:
            CancelEnterMissionButton = WindowFrames.get("CancelEnterMissionButton", None)
            if CancelEnterMissionButton is None:
                return False
            if not CancelEnterMissionButton.FrameExists():
                return False
            CancelEnterMissionButton.FrameClick()
            return True
        ActionQueueManager().AddAction("ACTION", _cancel_enter_challenge)

        
    
    #region MissionMap
    class MissionMap:
        last_right_clicked_coords: tuple[float, float] = (0.0, 0.0)
        last_right_clicked_timestamp: int = 0
        last_left_clicked_coords: tuple[float, float] = (0.0, 0.0)
        last_left_clicked_timestamp: int = 0
        #--------- Mission Map Info Methods ---------
        @staticmethod
        def GetFrameID() -> int:
            """Get the frame ID of the mission map."""
            if not (misison_map_ctx := GWContext.MissionMap.GetContext()):
                return 0
            return misison_map_ctx.frame_id
        
        @staticmethod
        def GetFrameInfo() -> FrameInfo | None:
            """Get the frame info of the mission map."""
            if not (frame_id := Map.MissionMap.GetFrameID()):
                return None
            return FrameInfo(FrameID_source=frame_id)
        
        @staticmethod
        def IsWindowOpen() -> bool:
            """Check if the mission map window is open."""
            if not (frame_info := Map.MissionMap.GetFrameInfo()):
                return False
            return frame_info.FrameExists()
        
        @staticmethod
        def OpenWindow():
            """Open the mission map window."""
            from Py4GWCoreLib import GLOBAL_CACHE, Routines
            if Map.MissionMap.IsWindowOpen():
                return
            GLOBAL_CACHE.Coroutines.append(Routines.Yield.Keybinds.OpenMissionMap())
            
        @staticmethod
        def CloseWindow():
            """Close the mission map window."""
            from Py4GWCoreLib import GLOBAL_CACHE, Routines
            if not (frame_info := Map.MissionMap.GetFrameInfo()):
                return
            GLOBAL_CACHE.Coroutines.append(Routines.Yield.Keybinds.OpenMissionMap())
        
        @staticmethod
        def IsMouseOver() -> bool:
            """Check if the mouse is hovering over the mission map."""
            if not (frame_info := Map.MissionMap.GetFrameInfo()):
                return False

            return frame_info.IsMouseOver()
        
        @staticmethod
        def GetLastClickCoords() -> tuple[float, float]:
            """Get the last left click coordinates on the mission map."""
            if not (frame_info := Map.MissionMap.GetFrameInfo()):
                return 0.0, 0.0
            
            io_events: list[UIManager.IOEvent] = frame_info.GetIOEvents()
            if len(io_events) == 0:
                return Map.MissionMap.last_left_clicked_coords
            
            for event in io_events:
                if event is None:
                    return Map.MissionMap.last_left_clicked_coords
                
                if event["event_type"] != "left_mouse_clicked":
                    continue
                
                if event["timestamp"] != Map.MissionMap.last_left_clicked_timestamp:
                    if not (misison_map_ctx := GWContext.MissionMap.GetContext()):
                        Map.MissionMap.last_left_clicked_coords = 0.0, 0.0
                        return Map.MissionMap.last_left_clicked_coords
                    
                    Map.MissionMap.last_left_clicked_coords = misison_map_ctx.last_mouse_location.to_tuple()
                    Map.MissionMap.last_left_clicked_timestamp = event["timestamp"]
                    return Map.MissionMap.last_left_clicked_coords
            
            return Map.MissionMap.last_left_clicked_coords
        
        @staticmethod
        def GetLastRightClickCoords() -> tuple[float, float]:
            """Get the last right click coordinates on the mission map."""
            if not (frame_info := Map.MissionMap.GetFrameInfo()):
                return 0.0, 0.0
            
            io_events: list[UIManager.IOEvent] = frame_info.GetIOEvents()
            if len(io_events) == 0:
                return Map.MissionMap.last_right_clicked_coords
            
            for event in io_events:
                if event is None:
                    return Map.MissionMap.last_right_clicked_coords
                
                if event["event_type"] != "right_mouse_clicked":
                    continue
                
                if event["timestamp"] != Map.MissionMap.last_right_clicked_timestamp:
                    if not (misison_map_ctx := GWContext.MissionMap.GetContext()):
                        Map.MissionMap.last_right_clicked_coords = 0.0, 0.0
                        return Map.MissionMap.last_right_clicked_coords
                    
                    Map.MissionMap.last_right_clicked_coords = misison_map_ctx.last_mouse_location.to_tuple()
                    Map.MissionMap.last_right_clicked_timestamp = event["timestamp"]
                    return Map.MissionMap.last_right_clicked_coords
            
            return Map.MissionMap.last_right_clicked_coords
        
            
        @staticmethod
        def GetMissionMapWindowCoords() -> tuple[float, float, float, float]:
            """Get the window coordinates of the mission map."""
            if not (frame_info := Map.MissionMap.GetFrameInfo()):
                return 0.0, 0.0, 0.0, 0.0
            return frame_info.GetCoords()
        
        @staticmethod
        def GetMissionMapContentsCoords() -> tuple[float, float, float, float]:
            """Get the contents coordinates of the mission map."""
            if not (frame_info := Map.MissionMap.GetFrameInfo()):
                return 0.0, 0.0, 0.0, 0.0
            return frame_info.GetContentCoords()
        
        @staticmethod
        def GetScale() -> tuple[float, float]:
            """Get the scale of the mission map."""
            if not (frame_info := Map.MissionMap.GetFrameInfo()):
                return 0.0, 0.0
            return frame_info.GetViewPortScale()
        
        @staticmethod
        def GetZoom() -> float:
            """Get the zoom level of the mission map."""
            if not (gameplay_ctx := GWContext.Gameplay.GetContext()):
                return 1.0
            return gameplay_ctx.mission_map_zoom
        
        @staticmethod
        def GetAdjustedZoom(_zoom, zoom_offset=0.0):
            """Adjust the zoom level of the mission map."""
            zoom = _zoom + zoom_offset
            if zoom == 1.0:
                return zoom + 0.0
            
            if 1.0 < zoom <= 1.5:
                return zoom + 0.0449
            
            if zoom > 1.5:
                step = 0.5
                # Snap to step count safely
                times = int((zoom - 1.5 + 1e-6) // step)  # avoids float precision issues
                return zoom + (0.0449 + (0.02449 * times))
            
            return zoom + 0.0
        
        @staticmethod
        def GetCenter() -> tuple[float, float]:
            """Get the player position coordinates of the mission map."""
            if not (misison_map_ctx := GWContext.MissionMap.GetContext()):
                return 0.0, 0.0
            return misison_map_ctx.player_mission_map_pos.to_tuple()
        
        
        
        @staticmethod
        def GetPanOffset() -> tuple[float, float]:
            """Get the pan offset of the mission map."""
            if not (misison_map_ctx := GWContext.MissionMap.GetContext()):
                return 0.0, 0.0
            subcontext = misison_map_ctx.subcontext2
            if subcontext is None:
                return 0.0, 0.0
            return subcontext.mission_map_pan_offset.to_tuple()
        
        @staticmethod
        def GetMapScreenCenter() -> tuple[float, float]:
            """Get the map screen center coordinates."""
            coords = Map.MissionMap.GetMissionMapContentsCoords()
            top_left: Vec2f = Vec2f(coords[0], coords[1])
            bottom_right: Vec2f = Vec2f(coords[2], coords[3])
            r_x  = top_left.x + (bottom_right.x - top_left.x) / 2.0
            r_y  = top_left.y + (bottom_right.y - top_left.y) / 2.0
            return r_x, r_y

        class MapProjection:
            @staticmethod
            def GamePosToWorldMap(x: float, y: float) -> tuple[float, float]:
                """Convert game-space coordinates (gwinches) to world map coordinates (screen space).

                Args:
                    x (float): The x-coordinate in game-space (gwinches).
                    y (float): The y-coordinate in game-space (gwinches).

                Returns:
                    tuple[float, float]: The corresponding coordinates on the world map (screen space).
                """
                gwinches = 96.0

                # Step 1: Get map bounds in UI space
                left, top, right, bottom = Map.GetMapWorldMapBounds()

                # Step 2: Get game-space boundaries from map context
                boundaries = Map.GetMapBoundaries()
                if len(boundaries) < 4:
                    return 0.0, 0.0  # fail-safe

                min_x = boundaries[0]
                max_y = boundaries[3]

                # Step 3: Compute origin on the world map based on boundary distances
                origin_x = left + abs(min_x) / gwinches
                origin_y = top + abs(max_y) / gwinches

                # Step 4: Convert game-space (gwinches) to world map space (screen)
                screen_x = (x / gwinches) + origin_x
                screen_y = (-y / gwinches) + origin_y  # Inverted Y

                return screen_x, screen_y
            
            @staticmethod
            def WorldMapToGamePos(x: float, y: float) -> tuple[float, float]:
                """Convert world map coordinates (screen space) to game-space coordinates (gwinches).
                Args:
                    x (float): The x-coordinate on the world map (screen space).
                    y (float): The y-coordinate on the world map (screen space).
                    Returns:
                        tuple[float, float]: The corresponding coordinates in game-space (gwinches).
                """
                gwinches = 96.0

                # Step 1: Get the world map bounds in screen-space
                left, top, right, bottom = Map.GetMapWorldMapBounds()

                # Step 2: Check if input point is within the map bounds
                #if not (left <= x <= right and top <= y <= bottom):
                #    return 0.0, 0.0  # Equivalent to ImRect.Contains check

                # Step 3: Get game-space boundaries (min_x, ..., max_y)
                bounds = Map.GetMapBoundaries()
                if len(bounds) < 4:
                    return 0.0, 0.0

                min_x = bounds[0]
                max_y = bounds[3]

                # Step 4: Compute the world map anchor point (same logic as forward)
                origin_x = left + abs(min_x) / gwinches
                origin_y = top + abs(max_y) / gwinches

                # Step 5: Convert world map coords to game-space
                game_x = (x - origin_x) * gwinches
                game_y = (y - origin_y) * gwinches * -1.0  # Inverted Y

                return game_x, game_y
    
            @staticmethod
            def WorldMapToScreen(x: float, y: float, zoom_offset=0.0) -> tuple[float, float]:
                """Convert world map coordinates (screen space) to screen coordinates.

                Args:
                    x (float): The x-coordinate on the world map (screen space).
                    y (float): The y-coordinate on the world map (screen space).
                    zoom_offset (float, optional): Additional zoom offset. Defaults to 0.0.

                Returns:
                    tuple[float, float]: The corresponding screen coordinates.
                """
                # World map coordinates (x, y) to screen space
                pan_offset_x, pan_offset_y = Map.MissionMap.GetPanOffset()
                offset_x = x - pan_offset_x
                offset_y = y - pan_offset_y
                
                offset_y = -offset_y

                scale_x, scale_y = Map.MissionMap.GetScale()
                scaled_x = offset_x * scale_x
                scaled_y = offset_y * scale_y

                zoom = Map.MissionMap.GetZoom() + zoom_offset
                mission_map_screen_center_x, mission_map_screen_center_y = Map.MissionMap.GetMapScreenCenter()
                screen_x = scaled_x * zoom + mission_map_screen_center_x
                screen_y = scaled_y * zoom + mission_map_screen_center_y

                return screen_x, screen_y

            @staticmethod
            def ScreenToWorldMap(screen_x: float, screen_y: float, zoom_offset=0.0) -> tuple[float, float]:
                """Convert screen coordinates to world map coordinates (screen space).
                Args:
                    screen_x (float): The x-coordinate on the screen.
                    screen_y (float): The y-coordinate on the screen.
                    zoom_offset (float, optional): Additional zoom offset. Defaults to 0.0.
                Returns:
                    tuple[float, float]: The corresponding coordinates on the world map (screen space).
                """
                 # Screen coordinates to world map coordinates (x, y)
                if not Map.MissionMap.IsWindowOpen():
                    return 0.0, 0.0

                zoom = Map.MissionMap.GetZoom() + zoom_offset
                scale_x, scale_y = Map.MissionMap.GetScale()
                center_x, center_y = Map.MissionMap.GetMapScreenCenter()
                pan_offset_x, pan_offset_y = Map.MissionMap.GetPanOffset()

                # Invert transform from screen space back to world space
                scaled_x = (screen_x - center_x) / zoom
                scaled_y = (screen_y - center_y) / zoom

                world_x = (scaled_x / scale_x) + pan_offset_x
                world_y = (scaled_y / scale_y) + pan_offset_y

                return world_x, world_y
    
            @staticmethod
            def GameMapToScreen(x, y, zoom_offset=0.0) -> tuple[float, float]:
                """Convert game-space coordinates (gwinches) to screen coordinates.
                
                Args:
                    x (float): The x-coordinate in game-space (gwinches).
                    y (float): The y-coordinate in game-space (gwinches).
                    zoom_offset (float, optional): Additional zoom offset. Defaults to 0.0.

                Returns:
                    tuple[float, float]: The corresponding screen coordinates.
                """
                
                world_x, world_y = Map.MissionMap.MapProjection.GamePosToWorldMap(x, y)
                return Map.MissionMap.MapProjection.WorldMapToScreen(world_x, world_y, zoom_offset)
            
            @staticmethod
            def ScreenToGameMap(x, y, zoom_offset=0.0) -> tuple[float, float]:
                """Convert screen coordinates to game-space coordinates (gwinches).
                Args:
                    x (float): The x-coordinate on the screen.
                    y (float): The y-coordinate on the screen.
                    zoom_offset (float, optional): Additional zoom offset. Defaults to 0.0.
                Returns:
                    tuple[float, float]: The corresponding coordinates in game-space (gwinches).
                """
                world_x, world_y = Map.MissionMap.MapProjection.ScreenToWorldMap(x, y, zoom_offset)
                return Map.MissionMap.MapProjection.WorldMapToGamePos(world_x, world_y)
            
            @staticmethod
            def NormalizedScreenToScreen(x, y) -> tuple[float, float]:
                """Convert normalized screen coordinates [-1, 1] to screen coordinates.
                Args:   
                    x (float): The normalized x-coordinate in [-1, 1].
                    y (float): The normalized y-coordinate in [-1, 1].
                Returns:
                    tuple[float, float]: The corresponding screen coordinates.
                """
                # Convert normalized [-1,1] → [0,1]
                adjusted_x = (x + 1.0) * 0.5
                adjusted_y = (1.0 - y) * 0.5

                # Use *exact* mission-map window bounds
                left, top, right, bottom = Map.MissionMap.GetMissionMapContentsCoords()

                width  = right  - left
                height = bottom - top

                screen_x = left + adjusted_x * width
                screen_y = top  + adjusted_y * height

                return screen_x, screen_y
            
            @staticmethod
            def ScreenToNormalizedScreen(screen_x: float, screen_y: float) -> tuple[float, float]:
                """Convert screen coordinates to normalized screen coordinates [-1, 1].
                Args:
                    screen_x (float): The x-coordinate on the screen.
                    screen_y (float): The y-coordinate on the screen.
                Returns:
                    tuple[float, float]: The corresponding normalized coordinates in [-1, 1].
                """
                # Compute width and height of the map frame
                coords = Map.MissionMap.GetMissionMapWindowCoords()
                left, top, right, bottom = int(coords[0]-5), int(coords[1]-1), int(coords[2]+5), int(coords[3]+2)
                width = right - left
                height = bottom - top

                # Relative position in [0, 1] range
                rel_x = (screen_x - left) / width
                rel_y = (screen_y - top) / height

                # Convert to normalized [-1, 1], Y is inverted
                norm_x = rel_x * 2.0 - 1.0
                norm_y = (1.0 - rel_y) * 2.0 - 1.0

                return norm_x, norm_y
            
            @staticmethod
            def NormalizedScreenToWorldMap(x, y, zoom_offset=0.0) -> tuple[float, float]:
                """Convert normalized screen coordinates [-1, 1] to world map coordinates.
                Args:
                    x (float): The normalized x-coordinate in [-1, 1].
                    y (float): The normalized y-coordinate in [-1, 1].
                    zoom_offset (float, optional): The zoom offset. Defaults to 0.0.
                Returns:
                    tuple[float, float]: The corresponding world map coordinates.
                """
                screen_x, screen_y = Map.MissionMap.MapProjection.NormalizedScreenToScreen(x, y)
                return Map.MissionMap.MapProjection.ScreenToWorldMap(screen_x, screen_y, zoom_offset)
            
            @staticmethod
            def NormalizedScreenToGamePos(x, y) -> tuple[float, float]:
                """Convert normalized screen coordinates [-1, 1] to game-space coordinates (gwinches).
                Args:
                    x (float): The normalized x-coordinate in [-1, 1].
                    y (float): The normalized y-coordinate in [-1, 1].
                Returns:
                    tuple[float, float]: The corresponding coordinates in game-space (gwinches).
                """
                #game_map_pos = PyOverlay.Overlay().NormalizedScreenToGameMap(x, y)
                #return game_map_pos.x, game_map_pos.y
                world_x, world_y = Map.MissionMap.MapProjection.NormalizedScreenToScreen(x, y)
                return Map.MissionMap.MapProjection.ScreenToGamePos(world_x, world_y)
             
            @staticmethod
            def GamePosToNormalizedScreen(x, y) -> tuple[float, float]:
                """Convert game-space coordinates (gwinches) to normalized screen coordinates [-1, 1].
                Args:
                    x (float): The x-coordinate in game-space (gwinches).
                    y (float): The y-coordinate in game-space (gwinches).
                Returns:
                    tuple[float, float]: The corresponding normalized screen coordinates in [-1, 1].
                """
                screen_x, screen_y = Map.MissionMap.MapProjection.GameMapToScreen(x, y)
                return Map.MissionMap.MapProjection.ScreenToNormalizedScreen(screen_x, screen_y)
            
            @staticmethod
            def GamePosToScreen(x, y, zoom_offset=0.0) -> tuple[float, float]:
                """Convert game-space coordinates (gwinches) to screen coordinates.
                Args:
                    x (float): The x-coordinate in game-space (gwinches).
                    y (float): The y-coordinate in game-space (gwinches).
                    zoom_offset (float, optional): Additional zoom offset. Defaults to 0.0.
                Returns:
                    tuple[float, float]: The corresponding screen coordinates.
                """
                
                world_x, world_y = Map.MissionMap.MapProjection.GamePosToWorldMap(x, y)
                return Map.MissionMap.MapProjection.WorldMapToScreen(world_x, world_y, zoom_offset)
            
            @staticmethod
            def ScreenToGamePos(x, y, zoom_offset=0.0) -> tuple[float, float]:
                """Convert screen coordinates to game-space coordinates (gwinches).
                Args:
                    x (float): The x-coordinate on the screen.
                    y (float): The y-coordinate on the screen.
                    zoom_offset (float, optional): Additional zoom offset. Defaults to 0.0.
                Returns:
                    tuple[float, float]: The corresponding coordinates in game-space (gwinches).
                """
                world_x, world_y = Map.MissionMap.MapProjection.ScreenToWorldMap(x, y, zoom_offset)
                return Map.MissionMap.MapProjection.WorldMapToGamePos(world_x, world_y)
    
            
            @staticmethod
            def WorldPosToMissionMapScreen(x: float, y: float, zoom_offset=0.0) -> tuple[float, float]:
                """Convert world position coordinates to mission map screen coordinates.
                
                Args:
                    x (float): The x-coordinate in world position.
                    y (float): The y-coordinate in world position.
                    zoom_offset (float, optional): Additional zoom offset. Defaults to 0.0.
                Returns:
                    tuple[float, float]: The corresponding screen coordinates on the mission map.
                """
                
                # 1. Convert game position (gwinches) to world map coordinates
                world_x, world_y = Map.MissionMap.MapProjection.GamePosToWorldMap(x, y)

                # 2. Project onto the mission map screen space
                screen_x, screen_y = Map.MissionMap.MapProjection.WorldMapToScreen(world_x, world_y, zoom_offset)

                return screen_x, screen_y
            
            @staticmethod
            def ScreenToWorldPos(screen_x: float, screen_y: float, zoom_offset=0.0) -> tuple[float, float]:
                """Convert mission map screen coordinates to world position coordinates.
                Args:
                    screen_x (float): The x-coordinate on the mission map screen.
                    screen_y (float): The y-coordinate on the mission map screen.
                    zoom_offset (float, optional): Additional zoom offset. Defaults to 0.0.
                Returns:
                    tuple[float, float]: The corresponding world position coordinates.
                """
                # Step 1: Convert from screen-space to world map coordinates
                world_x, world_y = Map.MissionMap.MapProjection.ScreenToWorldMap(screen_x, screen_y, zoom_offset)

                # Step 2: Convert from world map coordinates to in-game game coordinates (gwinches)
                game_x, game_y = Map.MissionMap.MapProjection.WorldMapToGamePos(world_x, world_y)

                return game_x, game_y
            
    #region MiniMap
    class MiniMap:
        last_right_clicked_coords: tuple[float, float] = (0.0, 0.0)
        last_right_clicked_timestamp: int = 0
        last_left_clicked_coords: tuple[float, float] = (0.0, 0.0)
        last_left_clicked_timestamp: int = 0
        @staticmethod
        def GetFrameInfo() -> FrameInfo | None:
            """Get the frame info of the mission map."""
            return WindowFrames["MiniMap"]
        
        @staticmethod
        def GetFrameID():
            """Get the frame ID of the mini map."""
            if not (mini_map_frame := Map.MiniMap.GetFrameInfo()):
                return 0
            
            return mini_map_frame.GetFrameID()

        @staticmethod
        def IsWindowOpen():
            """Check if the mini map window is open."""
            if not (mini_map_frame := Map.MiniMap.GetFrameInfo()):
                return False
            return mini_map_frame.FrameExists()
        
        @staticmethod
        def OpenWindow():
            """Open the mini map window."""
            from Py4GWCoreLib.enums_src.UI_enums import WindowID
            if Map.MiniMap.IsWindowOpen():
                return
            UIManager.SetWindowVisible(WindowID.WindowID_Compass, True)
            
        @staticmethod
        def CloseWindow():
            """Close the mini map window."""
            from Py4GWCoreLib.enums_src.UI_enums import WindowID
            if not Map.MiniMap.IsWindowOpen():
                return
            UIManager.SetWindowVisible(WindowID.WindowID_Compass, False)
            
        @staticmethod
        def IsMouseOver():
            """Check if the mouse is hovering over the mini map."""
            if not (mini_map_frame := Map.MiniMap.GetFrameInfo()):
                return False
            return mini_map_frame.IsMouseOver()
        
        @staticmethod
        def GetLastClickCoords() -> tuple[float, float]:
            """Get the last left click coordinates on the mission map."""
            if not (frame_info := Map.MiniMap.GetFrameInfo()):
                return 0.0, 0.0
            
            io_events: list[UIManager.IOEvent] = frame_info.GetIOEvents()
            if len(io_events) == 0:
                return Map.MiniMap.last_left_clicked_coords
            
            for event in io_events:
                if event is None:
                    return Map.MiniMap.last_left_clicked_coords
                
                if event["event_type"] != "left_mouse_clicked":
                    continue
                
                if event["timestamp"] != Map.MiniMap.last_left_clicked_timestamp:
                    Map.MiniMap.last_left_clicked_coords = event["mouse_pos"]
                    Map.MiniMap.last_left_clicked_timestamp = event["timestamp"]
                    return Map.MiniMap.last_left_clicked_coords
            
            #return Map.MiniMap.last_left_clicked_coords
            return Map.MiniMap.MapProjection.ScreenToNormalizedScreen(*Map.MiniMap.last_left_clicked_coords)
        
        @staticmethod
        def GetLastRightClickCoords() -> tuple[float, float]:
            """Get the last right click coordinates on the mission map."""
            if not (frame_info := Map.MiniMap.GetFrameInfo()):
                return 0.0, 0.0
            
            io_events: list[UIManager.IOEvent] = frame_info.GetIOEvents()
            if len(io_events) == 0:
                return Map.MiniMap.last_right_clicked_coords
            
            for event in io_events:
                if event is None:
                    return Map.MiniMap.last_right_clicked_coords
                
                if event["event_type"] != "right_mouse_clicked":
                    continue
                
                if event["timestamp"] != Map.MiniMap.last_right_clicked_timestamp:       
                    Map.MiniMap.last_right_clicked_coords = event["mouse_pos"]
                    Map.MiniMap.last_right_clicked_timestamp = event["timestamp"]
                    return Map.MiniMap.last_right_clicked_coords
            
            #return Map.MiniMap.last_right_clicked_coords
            return Map.MiniMap.MapProjection.ScreenToNormalizedScreen(*Map.MiniMap.last_right_clicked_coords)
        
        @staticmethod
        def GetWindowCoords():
            """Get the coordinates of the mini map."""
            if not (mini_map_frame := Map.MiniMap.GetFrameInfo()):
                return 0.0, 0.0, 0.0, 0.0
            return mini_map_frame.GetCoords()
        
        @staticmethod
        def IsLocked():
            """Check if the mini map is locked."""
            return UIManager.GetBoolPreference(FlagPreference.LockCompassRotation)
        
        @staticmethod
        def GetPanOffset():
            """Get the pan offset of the mini map."""
            return [0.0,0.0]
        
        @staticmethod
        def GetScale(coords = None):
            """Get the scale of the mini map."""
            if not coords:
                left,top,right,bottom = Map.MiniMap.GetWindowCoords()
            else:
                left,top,right,bottom = coords

            height = bottom - top
            diff = height - (height/1.05)
            left   += diff
            right  -= diff

            scale = (right-left)/2.0

            return scale
        
        @staticmethod
        def GetRotation():
            """Get the rotation of the mini map."""
            from .Camera import Camera

            if Map.MiniMap.IsLocked():
                return 0
            else:
                return Camera.GetCurrentYaw() - math.pi/2
        
        @staticmethod
        def GetZoom():
            """Get the zoom level of the mini map."""
            return 1.0
        
        
        
        @staticmethod
        def GetMapScreenCenter(coords = None):
            """Get the map screen center coordinates."""
            if not coords:
                left,top,right,bottom = Map.MiniMap.GetWindowCoords()
            else:
                left,top,right,bottom = coords
            height = bottom - top
            diff = height - (height/1.05)

            top    += diff
            left   += diff
            right  -= diff

            center_x = (left + right)/2.0
            center_y = top + (right - left)/2.0

            return center_x, center_y
        
        #region projection methods
        class MapProjection:
            @staticmethod
            def GamePosToWorldMap(x: float, y: float):
                gwinches = 96.0

                # Step 1: Get map bounds in UI space
                left, top, right, bottom = Map.GetMapWorldMapBounds()

                # Step 2: Get game-space boundaries from map context
                boundaries = Map.GetMapBoundaries()
                if len(boundaries) < 4:
                    return 0.0, 0.0  # fail-safe

                min_x = boundaries[0]
                max_y = boundaries[3]
                # Step 3: Compute origin on the world map based on boundary distances
                origin_x = left + abs(min_x) / gwinches
                origin_y = top + abs(max_y) / gwinches

                # Step 4: Convert game-space (gwinches) to world map space (screen)
                screen_x = (x / gwinches) + origin_x
                screen_y = (-y / gwinches) + origin_y  # Inverted Y

                return screen_x, screen_y
            
            @staticmethod
            def WorldMapToGamePos(x: float, y: float):
                gwinches = 96.0
                left, top, right, bottom = Map.GetMapWorldMapBounds()
                bounds = Map.GetMapBoundaries()
                if len(bounds) < 4:
                    return 0.0, 0.0

                min_x = bounds[0]
                max_y = bounds[3]

                # Step 4: Compute the world map anchor point (same logic as forward)
                origin_x = left + abs(min_x) / gwinches
                origin_y = top + abs(max_y) / gwinches

                # Step 5: Convert world map coords to game-space
                game_x = (x - origin_x) * gwinches
                game_y = (y - origin_y) * gwinches * -1.0  # Inverted Y

                return game_x, game_y
            
            @staticmethod
            def WorldMapToScreen(x: float, y: float):
                # World map coordinates (x, y) to screen space
                pan_offset_x, pan_offset_y = Map.MiniMap.GetPanOffset()
                offset_x = x - pan_offset_x
                offset_y = y - pan_offset_y

                scale = Map.MiniMap.GetScale()
                scaled_x = offset_x * scale
                scaled_y = offset_y * scale

                zoom = Map.MiniMap.GetZoom()
                mission_map_screen_center_x, mission_map_screen_center_y = Map.MiniMap.GetMapScreenCenter()
                screen_x = scaled_x * zoom + mission_map_screen_center_x
                screen_y = scaled_y * zoom + mission_map_screen_center_y

                return screen_x, screen_y

            @staticmethod
            def ScreenToWorldMap(screen_x: float, screen_y: float):

                zoom = Map.MiniMap.GetZoom()
                scale = Map.MiniMap.GetScale()
                center_x, center_y = Map.MiniMap.GetMapScreenCenter()
                pan_offset_x, pan_offset_y = Map.MiniMap.GetPanOffset()

                # Invert transform from screen space back to world space
                scaled_x = (screen_x - center_x) / zoom
                scaled_y = (screen_y - center_y) / zoom

                world_x = (scaled_x / scale) + pan_offset_x
                world_y = (scaled_y / scale) + pan_offset_y

                return world_x, world_y
            
            @staticmethod
            def GameMapToScreen(x, y):
                world_x, world_y = Map.MiniMap.MapProjection.GamePosToWorldMap(x, y)
                return Map.MiniMap.MapProjection.WorldMapToScreen(world_x, world_y)
            
            @staticmethod
            def ScreenToGameMap(x, y):
                world_x, world_y = Map.MiniMap.MapProjection.ScreenToWorldMap(x, y)
                return Map.MiniMap.MapProjection.WorldMapToGamePos(world_x, world_y)
            
            @staticmethod
            def NormalizedScreenToScreen(x, y):
                # Convert from [-1, 1] to [0, 1] with Y-inversion
                norm_x, norm_y = x,y
                adjusted_x = (norm_x + 1.0) * 0.5
                adjusted_y = (1.0 - norm_y) * 0.5

                # Compute width and height of the map frame
                coords = Map.MiniMap.GetWindowCoords()
                left, top, right, bottom = int(coords[0]), int(coords[1]), int(coords[2]), int(coords[3])
                width = right - left
                height = bottom - top

                screen_x = left + adjusted_x * width
                screen_y = top + adjusted_y * height

                return screen_x, screen_y
            
            @staticmethod
            def ScreenToNormalizedScreen(screen_x: float, screen_y: float):
                # Compute width and height of the map frame
                coords = Map.MiniMap.GetWindowCoords()
                left, top, right, bottom = int(coords[0]), int(coords[1]), int(coords[2]), int(coords[3])
                width = right - left
                height = bottom - top

                # Relative position in [0, 1] range
                rel_x = (screen_x - left) / width
                rel_y = (screen_y - top) / height

                # Convert to normalized [-1, 1], Y is inverted
                norm_x = rel_x * 2.0 - 1.0
                norm_y = (1.0 - rel_y) * 2.0 - 1.0

                return norm_x, norm_y
            
            @staticmethod
            def NormalizedScreenToWorldMap(x, y):
                screen_x, screen_y = Map.MiniMap.MapProjection.NormalizedScreenToScreen(x, y)
                return Map.MiniMap.MapProjection.ScreenToWorldMap(screen_x, screen_y)
            
            @staticmethod
            def NormalizedScreenToGamePos(x, y):
                world_x, world_y = Map.MiniMap.MapProjection.NormalizedScreenToScreen(x, y)
                return Map.MiniMap.MapProjection.ScreenToGamePos(world_x, world_y)
             
            @staticmethod
            def GamePosToNormalizedScreen(x, y):
                screen_x, screen_y = Map.MiniMap.MapProjection.GameMapToScreen(x, y)
                return Map.MiniMap.MapProjection.ScreenToNormalizedScreen(screen_x, screen_y)
    
            @staticmethod
            def GamePosToScreen(game_x, game_y,
                                player_x = None, player_y = None,
                                center_x = None, center_y = None,
                                scale = None, rotation = None):
                """ Convert a game position to a position on the screen relative to the compass."""

                from .Player import Player
                
                if player_x == None or player_y == None:
                    player_x, player_y = Player.GetXY()
                if center_x == None or center_y == None:
                    center_x, center_y = Map.MiniMap.GetMapScreenCenter()
                if scale == None:
                    scale = Map.MiniMap.GetScale()
                if rotation == None:
                    rotation = Map.MiniMap.GetRotation()

                x = center_x - (player_x - game_x)*scale/5000
                y = center_y + (player_y - game_y)*scale/5000

                screen_x = center_x + math.cos(rotation)*(x - center_x) - math.sin(rotation)*(y - center_y)
                screen_y = center_y + math.sin(rotation)*(x - center_x) + math.cos(rotation)*(y - center_y)

                return screen_x, screen_y
            
            @staticmethod
            def ScreenToGamePos(screen_x, screen_y,
                                player_x = None, player_y = None,
                                center_x = None, center_y = None,
                                scale = None, rotation = None):
                """ Convert a screen position relative to the compass to a position in the game."""

                from .Player import Player

                if player_x == None or player_y == None:
                    player_x, player_y = Player.GetXY()
                if center_x == None or center_y == None:
                    center_x, center_y = Map.MiniMap.GetMapScreenCenter()
                if scale == None:
                    scale = Map.MiniMap.GetScale()
                if rotation == None:
                    rotation = Map.MiniMap.GetRotation()

                x = center_x + math.cos(-rotation)*(screen_x - center_x) - math.sin(-rotation)*(screen_y - center_y)
                y = center_y + math.sin(-rotation)*(screen_x - center_x) + math.cos(-rotation)*(screen_y - center_y)

                game_x = player_x + (x - center_x)*5000/scale
                game_y = player_y - (y - center_y)*5000/scale

                return game_x, game_y
            
            @staticmethod
            def WorldPosToMiniMapScreen(x: float, y: float):
                # 1. Convert game position (gwinches) to world map coordinates
                world_x, world_y = Map.MiniMap.MapProjection.GamePosToWorldMap(x, y)

                # 2. Project onto the mission map screen space
                screen_x, screen_y = Map.MiniMap.MapProjection.WorldMapToScreen(world_x, world_y)

                return screen_x, screen_y
            
            @staticmethod
            def ScreenToWorldPos(screen_x: float, screen_y: float):
                # Step 1: Convert from screen-space to world map coordinates
                world_x, world_y = Map.MiniMap.MapProjection.ScreenToWorldMap(screen_x, screen_y)

                # Step 2: Convert from world map coordinates to in-game game coordinates (gwinches)
                game_x, game_y = Map.MiniMap.MapProjection.WorldMapToGamePos(world_x, world_y)

                return game_x, game_y
            
            @staticmethod
            def ComputedPathingGeometryToScreen(map_bounds = None,
                                                   player_x = None, player_y = None,
                                                   center_x = None, center_y = None,
                                                   scale = None, rotation = None):
                """ Convert a screen position of pathing geometry to a screen position relative to the compass."""
                from .Player import Player
                
                # Step 1: Get map bounds
                if not map_bounds:
                    map_bounds = Map.GetMapBoundaries()
                
                map_min_x = map_bounds[0]
                map_min_y = map_bounds[1]
                map_max_x = map_bounds[2]
                map_max_y = map_bounds[3]
                map_mid_x = (map_min_x + map_max_x)/2
                map_mid_y = (map_min_y + map_max_y)/2

                # Step 2: Get compass position/scale/rotation
                if center_x == None or center_y == None:
                    center_x, center_y = Map.MiniMap.GetMapScreenCenter()
                if scale == None:
                    scale = Map.MiniMap.GetScale()
                if rotation == None:
                    rotation = Map.MiniMap.GetRotation()

                # Step 3: Get Player position
                if player_x == None or player_y == None:
                    player_x, player_y = Player.GetXY()

                # Step 4: Get geometry zoom
                zoom = scale/5000

                # Step 5: Get Player position geometry offset
                x_pos_offset = map_mid_x - player_x
                y_pos_offset = map_mid_y - player_y

                # Step 6: Get rotation offset
                player_x_rotated = player_x*math.cos(-rotation) - player_y*math.sin(-rotation)
                player_y_rotated = player_x*math.sin(-rotation) + player_y*math.cos(-rotation)

                x_rot_offset = player_x - player_x_rotated
                y_rot_offset = player_y - player_y_rotated

                # Step 7: Get final offset
                x_offset = zoom*(x_pos_offset + x_rot_offset - (map_max_x + map_min_x)/2)
                y_offset = zoom*(y_pos_offset + y_rot_offset - (map_max_y + map_min_y)/2)

                return x_offset, y_offset, zoom
  
#region WorldMap
    class WorldMap:
        last_right_clicked_coords: tuple[float, float] = (0.0, 0.0)
        last_right_clicked_timestamp: int = 0
        last_left_clicked_coords: tuple[float, float] = (0.0, 0.0)
        last_left_clicked_timestamp: int = 0
        @staticmethod
        def GetFrameID():
            """Get the frame ID of the mini map."""
            if not (world_map_ctx := GWContext.WorldMap.GetContext()):
                return 0
            return world_map_ctx.frame_id
        
        @staticmethod
        def GetFrameInfo() -> FrameInfo | None:
            """Get the frame info of the mission map."""
            if not (frame_id := Map.WorldMap.GetFrameID()):
                return None
            return FrameInfo(FrameID_source=frame_id)
        
        @staticmethod
        def IsWindowOpen() -> bool:
            """Check if the mission map window is open."""
            if not (frame_info := Map.WorldMap.GetFrameInfo()):
                return False
            return frame_info.FrameExists()
        
        @staticmethod
        def OpenWindow():
            """Open the mission map window."""
            from Py4GWCoreLib import GLOBAL_CACHE, Routines
            if Map.WorldMap.IsWindowOpen():
                return
            GLOBAL_CACHE.Coroutines.append(Routines.Yield.Keybinds.OpenWorldMap())
            
        @staticmethod
        def CloseWindow():
            """Close the mission map window."""
            from Py4GWCoreLib import GLOBAL_CACHE, Routines
            if not (frame_info := Map.WorldMap.GetFrameInfo()):
                return
            GLOBAL_CACHE.Coroutines.append(Routines.Yield.Keybinds.OpenWorldMap())
            
        @staticmethod
        def IsMouseOver() -> bool:
            """Check if the mouse is hovering over the mission map."""
            if not (frame_info := Map.WorldMap.GetFrameInfo()):
                return False
            return frame_info.IsMouseOver()
        
        @staticmethod
        def GetLastClickCoords() -> tuple[float, float]:
            """Get the last left click coordinates on the mission map."""
            if not (frame_info := Map.WorldMap.GetFrameInfo()):
                return 0.0, 0.0
            
            io_events: list[UIManager.IOEvent] = frame_info.GetIOEvents()
            if len(io_events) == 0:
                return Map.WorldMap.last_left_clicked_coords
            
            for event in io_events:
                if event is None:
                    return Map.WorldMap.last_left_clicked_coords
                
                if event["event_type"] != "left_mouse_clicked":
                    continue
                
                if event["timestamp"] != Map.WorldMap.last_left_clicked_timestamp:
                    Map.WorldMap.last_left_clicked_coords = event["mouse_pos"]
                    Map.WorldMap.last_left_clicked_timestamp = event["timestamp"]
                    return Map.WorldMap.last_left_clicked_coords
            
            return Map.WorldMap.last_left_clicked_coords

        @staticmethod
        def GetLastRightClickCoords() -> tuple[float, float]:
            """Get the last right click coordinates on the mission map."""
            if not (frame_info := Map.WorldMap.GetFrameInfo()):
                return 0.0, 0.0
            
            io_events: list[UIManager.IOEvent] = frame_info.GetIOEvents()
            if len(io_events) == 0:
                return Map.WorldMap.last_right_clicked_coords
            
            for event in io_events:
                if event is None:
                    return Map.WorldMap.last_right_clicked_coords
                
                if event["event_type"] != "right_mouse_clicked":
                    continue
                
                if event["timestamp"] != Map.WorldMap.last_right_clicked_timestamp:       
                    Map.WorldMap.last_right_clicked_coords = event["mouse_pos"]
                    Map.WorldMap.last_right_clicked_timestamp = event["timestamp"]
                    return Map.WorldMap.last_right_clicked_coords
            
            return Map.WorldMap.last_right_clicked_coords
        
        @staticmethod
        def GetWindowCoords():
            """Get the coordinates of the mini map."""
            if not (world_map_ctx := GWContext.WorldMap.GetContext()):
                return 0.0, 0.0, 0.0, 0.0
            
            top_left = world_map_ctx.top_left
            bottom_right = world_map_ctx.bottom_right
            
            return top_left.x, top_left.y, bottom_right.x, bottom_right.y
        
        @staticmethod
        def GetZoom():
            """Get the zoom level of the world map."""
            if not (world_map_ctx := GWContext.WorldMap.GetContext()):
                return 1.0
            return world_map_ctx.zoom
        
        @staticmethod
        def GetParams() -> list[int] | None:
            """Get the parameters of the world map."""
            if not (world_map_ctx := GWContext.WorldMap.GetContext()):
                return None
            return world_map_ctx.params
        
        @staticmethod
        def GetExtraData() -> dict | None:
            import ctypes
            """Dump all misc fields (hXXXX + params) from WorldMapContext."""
            ctx = GWContext.WorldMap.GetContext()
            if not ctx:
                return None

            base_addr = ctypes.addressof(ctx)  # <-- raw starting address of the struct
            result = {}

            # ---- misc values at fixed offsets ----
            misc_layout = [
                (0x0004, "h0004", ctypes.c_uint32),
                (0x0008, "h0008", ctypes.c_uint32),
                (0x000C, "h000c", ctypes.c_float),
                (0x0010, "h0010", ctypes.c_float),
                (0x0014, "h0014", ctypes.c_uint32),
                (0x0018, "h0018", ctypes.c_float),
                (0x001C, "h001c", ctypes.c_float),
                (0x0020, "h0020", ctypes.c_float),
                (0x0024, "h0024", ctypes.c_float),
                (0x0028, "h0028", ctypes.c_float),
                (0x002C, "h002c", ctypes.c_float),
                (0x0030, "h0030", ctypes.c_float),
                (0x0034, "h0034", ctypes.c_float),
                (0x0068, "h0068", ctypes.c_float),
                (0x006C, "h006c", ctypes.c_float),
            ]

            for offset, name, ctype in misc_layout:
                addr = base_addr + offset
                raw_ptr = ctypes.cast(addr, ctypes.POINTER(ctype))
                result[name] = raw_ptr.contents.value
                
            # ---- array h004c ----
            h004c_offset = 0x004C
            h004c_count  = 7
            h004c        = []

            for i in range(h004c_count):
                addr = base_addr + h004c_offset + (i * ctypes.sizeof(ctypes.c_uint32))
                raw_ptr = ctypes.cast(addr, ctypes.POINTER(ctypes.c_uint32))
                h004c.append(raw_ptr.contents.value)

            result["h004c"] = h004c

            return result
        
#region Pregame
    class Pregame:
        from .native_src.context.PreGameContext import PreGameContextStruct, LoginCharacter
        
        last_right_clicked_coords: tuple[float, float] = (0.0, 0.0)
        last_right_clicked_timestamp: int = 0
        last_left_clicked_coords: tuple[float, float] = (0.0, 0.0)
        last_left_clicked_timestamp: int = 0
        
        @staticmethod
        def GetFrameID():
            """Get the frame ID of the mini map."""
            if not (world_map_ctx := GWContext.PreGame.GetContext()):
                return 0
            return world_map_ctx.frame_id
        
        @staticmethod
        def GetFrameInfo() -> FrameInfo | None:
            """Get the frame info of the mission map."""
            if not (frame_id := Map.Pregame.GetFrameID()):
                return None
            return FrameInfo(FrameID_source=frame_id)
        
        @staticmethod
        def IsWindowOpen() -> bool:
            """Check if the mission map window is open."""
            if not (frame_info := Map.Pregame.GetFrameInfo()):
                return False
            return frame_info.FrameExists()
            
        @staticmethod
        def LogOutToCharachterSelect():
            """Log out to character selection from pregame map."""
            from Py4GWCoreLib import GLOBAL_CACHE
            GLOBAL_CACHE.Player.LogoutToCharacterSelect()
        
        @staticmethod
        def GetChosenCharacterIndex() -> int:
            """Get the chosen character index from pregame map."""
            if not (pre_game_ctx := GWContext.PreGame.GetContext()):
                return -1
            return pre_game_ctx.chosen_character_index
        
        @staticmethod
        def GetContextStruct() -> PreGameContextStruct | None:
            """Get the pregame map context structure."""
            return GWContext.PreGame.GetContext()
        
        @staticmethod
        def GetCharList() -> List[LoginCharacter]:
            """Get the character list from pregame map."""
            if not (pre_game_ctx := GWContext.PreGame.GetContext()):
                return []
            return pre_game_ctx.chars_list
            
#region not_processed
    #region Pathing
    class Pathing:
        @staticmethod
        def GetPathingMaps() -> List[PyPathing.PathingMap]:
            return PyPathing.get_pathing_maps()

        @staticmethod
        def WorldToScreen(x, y, z=0.0):
            if z == 0.0:
                z = Overlay.FindZ(x, y)

            screen_pos = PyOverlay.Overlay().WorldToScreen(x, y, z)
            return screen_pos.x, screen_pos.y

        class Quad:
            def __init__(self, trapezoid: PyPathing.PathingTrapezoid):
                self.trapezoid = trapezoid

                self.top_left: PyOverlay.Point2D = PyOverlay.Point2D(int(trapezoid.XTL), int(trapezoid.YT))
                self.top_right: PyOverlay.Point2D = PyOverlay.Point2D(int(trapezoid.XTR), int(trapezoid.YT))
                self.bottom_left: PyOverlay.Point2D = PyOverlay.Point2D(int(trapezoid.XBL), int(trapezoid.YB))
                self.bottom_right: PyOverlay.Point2D = PyOverlay.Point2D(int(trapezoid.XBR), int(trapezoid.YB))

                screen_TL = Map.MissionMap.MapProjection.GameMapToScreen(self.top_left.x, self.top_left.y)
                screen_TR = Map.MissionMap.MapProjection.GameMapToScreen(self.top_right.x, self.top_right.y)
                screen_BL = Map.MissionMap.MapProjection.GameMapToScreen(self.bottom_left.x, self.bottom_left.y)
                screen_BR = Map.MissionMap.MapProjection.GameMapToScreen(self.bottom_right.x, self.bottom_right.y)

                self.screen_top_left: PyOverlay.Point2D = PyOverlay.Point2D(int(screen_TL[0]), int(screen_TL[1]))
                self.screen_top_right: PyOverlay.Point2D = PyOverlay.Point2D(int(screen_TR[0]), int(screen_TR[1]))
                self.screen_bottom_left: PyOverlay.Point2D = PyOverlay.Point2D(int(screen_BL[0]), int(screen_BL[1]))
                self.screen_bottom_right: PyOverlay.Point2D = PyOverlay.Point2D(int(screen_BR[0]), int(screen_BR[1]))

            def GetPoints(self) -> List[PyOverlay.Point2D]:
                return [self.top_left, self.top_right, self.bottom_left, self.bottom_right]

            def GetScreenPoints(self) -> List[PyOverlay.Point2D]:
                return [self.screen_top_left, self.screen_top_right, self.screen_bottom_left, self.screen_bottom_right]

            def GetShiftedPoints(self, origin_x: float, origin_y: float) -> List[PyOverlay.Point2D]:
                return [
                    PyOverlay.Point2D(int(self.top_left.x - origin_x), int(self.top_left.y - origin_y)),
                    PyOverlay.Point2D(int(self.top_right.x - origin_x), int(self.top_right.y - origin_y)),
                    PyOverlay.Point2D(int(self.bottom_left.x - origin_x), int(self.bottom_left.y - origin_y)),
                    PyOverlay.Point2D(int(self.bottom_right.x - origin_x), int(self.bottom_right.y - origin_y)),
                ]

            def GetShiftedScreenPoints(self, origin_x: float, origin_y: float) -> List[PyOverlay.Point2D]:
                shifted = self.GetShiftedPoints(origin_x, origin_y)
                shifted_tl = Map.MissionMap.MapProjection.GameMapToScreen(shifted[0].x, shifted[0].y)
                shifted_tr = Map.MissionMap.MapProjection.GameMapToScreen(shifted[1].x, shifted[1].y)
                shifted_bl = Map.MissionMap.MapProjection.GameMapToScreen(shifted[2].x, shifted[2].y)
                shifted_br = Map.MissionMap.MapProjection.GameMapToScreen(shifted[3].x, shifted[3].y)
                return [
                    PyOverlay.Point2D(int(shifted_tl[0]), int(shifted_tl[1])),
                    PyOverlay.Point2D(int(shifted_tr[0]), int(shifted_tr[1])),
                    PyOverlay.Point2D(int(shifted_bl[0]), int(shifted_bl[1])),
                    PyOverlay.Point2D(int(shifted_br[0]), int(shifted_br[1])),
                ]

        @staticmethod
        def GetComputedGeometry() -> List[List[PyOverlay.Point2D]]:
            pathing_maps = Map.Pathing.GetPathingMaps()
            geometry = []
            for layer in pathing_maps:
                for trapezoid in layer.trapezoids:
                    geometry.append(Map.Pathing.Quad(trapezoid).GetPoints())
            return geometry

        @staticmethod
        def GetScreenComputedGeometry() -> List[List[PyOverlay.Point2D]]:
            pathing_maps = Map.Pathing.GetPathingMaps()
            geometry = []
            for layer in pathing_maps:
                for trapezoid in layer.trapezoids:
                    geometry.append(Map.Pathing.Quad(trapezoid).GetScreenPoints())
            return geometry

        @staticmethod
        def GetShiftedComputedGeometry(origin_x: float, origin_y: float) -> List[List[PyOverlay.Point2D]]:
            pathing_maps = Map.Pathing.GetPathingMaps()
            geometry = []
            for layer in pathing_maps:
                for trapezoid in layer.trapezoids:
                    quad = Map.Pathing.Quad(trapezoid)
                    geometry.append(quad.GetShiftedPoints(origin_x, origin_y))
            return geometry

        @staticmethod
        def GetshiftedScreenComputedGeometry(origin_x: float, origin_y: float) -> List[List[PyOverlay.Point2D]]:
            pathing_maps = Map.Pathing.GetPathingMaps()
            geometry = []
            for layer in pathing_maps:
                for trapezoid in layer.trapezoids:
                    quad = Map.Pathing.Quad(trapezoid)
                    geometry.append(quad.GetShiftedScreenPoints(origin_x, origin_y))
            return geometry

        @staticmethod
        def _point_in_quad(px: float, py: float, quad: 'Map.Pathing.Quad') -> bool:
            '''Check if a given x,y-point is inside a quadrilateral.'''
            p = [quad.top_left, quad.top_right, quad.bottom_right, quad.bottom_left]

            def sign(x1, y1, x2, y2, x3, y3):
                return (x1 - x3) * (y2 - y3) - (x2 - x3) * (y1 - y3)

            b1 = sign(px, py, p[0].x, p[0].y, p[1].x, p[1].y) < 0.0
            b2 = sign(px, py, p[1].x, p[1].y, p[2].x, p[2].y) < 0.0
            b3 = sign(px, py, p[2].x, p[2].y, p[3].x, p[3].y) < 0.0
            b4 = sign(px, py, p[3].x, p[3].y, p[0].x, p[0].y) < 0.0

            return (b1 == b2 == b3 == b4)

        @staticmethod
        def GetMapQuads():
            '''Retrieve all pathing quads in the current map.'''
            pathing_maps = Map.Pathing.GetPathingMaps()
            quads = []
            
            for layer in pathing_maps:
                for trapezoid in layer.trapezoids:
                    quad = Map.Pathing.Quad(trapezoid)
                    quads.append(quad)

            return quads

        @staticmethod
        def IsPointInPathing(px: float, py: float) -> bool:
            '''Check if a given x,y-point is inside any pathing area.'''
            pathing_maps = Map.Pathing.GetPathingMaps()

            for layer in pathing_maps:
                for trapezoid in layer.trapezoids:
                    quad = Map.Pathing.Quad(trapezoid)
                    if Map.Pathing._point_in_quad(px, py, quad):
                        return True

            return False

        @staticmethod
        def IsScreenPointInPathing(screen_x: float, screen_y: float) -> bool:
            '''Check if a given screen x,y-point is inside any pathing area.'''
            pathing_maps = Map.Pathing.GetPathingMaps()

            for layer in pathing_maps:
                for trapezoid in layer.trapezoids:
                    quad = Map.Pathing.Quad(trapezoid)
                    pts = quad.GetScreenPoints()

                    def sign(x1, y1, x2, y2, x3, y3):
                        return (x1 - x3) * (y2 - y3) - (x2 - x3) * (y1 - y3)

                    b1 = sign(screen_x, screen_y, pts[0].x, pts[0].y, pts[1].x, pts[1].y) < 0.0
                    b2 = sign(screen_x, screen_y, pts[1].x, pts[1].y, pts[2].x, pts[2].y) < 0.0
                    b3 = sign(screen_x, screen_y, pts[2].x, pts[2].y, pts[3].x, pts[3].y) < 0.0
                    b4 = sign(screen_x, screen_y, pts[3].x, pts[3].y, pts[0].x, pts[0].y) < 0.0

                    if b1 == b2 == b3 == b4:
                        return True

            return False

    
    

