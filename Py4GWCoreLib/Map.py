import Py4GW
import PyMap
import PyMissionMap
import PyPathing
import PyOverlay
from .enums import explorables, explorable_name_to_id, FlagPreference
from .UIManager import *
from .Overlay import *
from collections import deque
import time

class Map:
    @staticmethod
    def map_instance():
        """Return the PyMap instance. """
        return PyMap.PyMap() 

    @staticmethod
    def IsMapReady():
        """Check if the map is ready to be handled."""
        return Map.map_instance().is_map_ready

    @staticmethod
    def IsOutpost():
        """Check if the map instance is an outpost."""
        return Map.map_instance().instance_type.GetName() == "Outpost"

    @staticmethod
    def IsExplorable():
        """Check if the map instance is explorable."""
        return Map.map_instance().instance_type.GetName() == "Explorable"

    @staticmethod
    def IsMapLoading():
        """Check if the map instance is loading."""
        return Map.map_instance().instance_type.GetName() == "Loading"

    @staticmethod
    def GetMapName(mapid=None):
        """
        Retrieve the name of a map by its ID.
        Args:
            mapid (int, optional): The ID of the map to retrieve. Defaults to the current map.
        Returns: str
        """
        global explorables
        if mapid is None:
            map_id = Map.GetMapID()
        else:
            map_id = mapid

        if map_id in explorables:
            return explorables[map_id]

        map_id_instance = PyMap.MapID(map_id)
        return map_id_instance.GetName()

    @staticmethod
    def GetMapID():
        """Retrieve the ID of the current map."""
        return Map.map_instance().map_id.ToInt()

    @staticmethod
    def GetOutpostIDs():
        """Retrieve the outpost IDs."""
        map_id_instance = PyMap.MapID(Map.GetMapID())
        return map_id_instance.GetOutpostIDs()

    @staticmethod
    def GetOutpostNames():
        """Retrieve the outpost names."""
        map_id_instance = PyMap.MapID(Map.GetMapID())
        return map_id_instance.GetOutpostNames()
    
    @staticmethod
    def GetMapIDByName(name):
        global explorable_name_to_id
        """Retrieve the ID of a map by its name."""
        map_id = explorable_name_to_id.get(name)
        if map_id is not None:
            return map_id

        # Get outpost IDs and names, and build a reverse lookup map
        outpost_ids = Map.GetOutpostIDs()
        outpost_names = Map.GetOutpostNames()
        outpost_name_to_id = {name: id for id, name in zip(outpost_names, outpost_ids)}

        # Check if the name exists in outposts
        return outpost_name_to_id.get(name, 0)

    @staticmethod
    def GetExplorableIDs():
        """
        Retrieve all explorable map IDs.
        Returns: list[int]
        """
        global explorables
        return list(explorables.keys())

    @staticmethod
    def GetExplorableNames():
        """
        Retrieve all explorable map names.
        Returns: list[str]
        """
        global explorables
        return list(explorables.values())
        

    @staticmethod
    def Travel(map_id):
        """Travel to a map by its ID."""
        Map.map_instance().Travel(map_id)

    @staticmethod
    def TravelToDistrict(map_id, district=0, district_number=0):
        """
        Travel to a map by its ID and district.
        Args:
            map_id (int): The ID of the map to travel to.
            district (int): The district to travel to.
            district_number (int): The number of the district to travel to.
        Returns: None
        """
        Map.map_instance().Travel(map_id, district, district_number)
        
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
        Map.map_instance().Travel(map_id, server_region, district_number, language)
    
    @staticmethod
    def TravelGH():
        """Travel to the Guild Hall."""
        Map.map_instance().TravelGH()
        
    @staticmethod
    def LeaveGH():
        """Leave the Guild Hall."""
        Map.map_instance().LeaveGH()

    @staticmethod
    def SetFog(state):
        """
        Set the fog state of the map.
        Args:
            state (bool): The state of the fog.
        Returns: None
        """
        Py4GW.Game.SetFog(state)

    @staticmethod
    def GetInstanceUptime():
        """Retrieve the uptime of the current instance."""
        return Map.map_instance().instance_time

    @staticmethod
    def GetMaxPartySize():
        """ Retrieve the maximum party size of the current map."""
        return Map.map_instance().max_party_size
    
    @staticmethod
    def GetMinPartySize():
        """ Retrieve the minimum party size of the current map."""
        return Map.map_instance().min_party_size

    @staticmethod
    def IsInCinematic():
        """Check if the map is in a cinematic."""
        return Map.map_instance().is_in_cinematic

    @staticmethod
    def SkipCinematic():
        """ Skip the cinematic."""
        Map.map_instance().SkipCinematic()

    @staticmethod
    def HasEnterChallengeButton():
        """Check if the map has an enter challenge button."""
        return Map.map_instance().has_enter_button

    @staticmethod
    def EnterChallenge():
        """Enter the challenge."""
        Map.map_instance().EnterChallenge()

    @staticmethod
    def CancelEnterChallenge():
        """Cancel entering the challenge."""
        Map.map_instance().CancelEnterChallenge()

    @staticmethod
    def IsVanquishable():
        """Check if the map is vanquishable."""
        return Map.map_instance().is_vanquishable_area

    @staticmethod
    def GetFoesKilled():
        """
        Retrieve the number of foes killed in the current map.
        Args: None
        Returns: int
        """
        return Map.map_instance().foes_killed

    @staticmethod
    def GetFoesToKill():
        """
        Retrieve the number of foes to kill in the current map.
        Args: None
        Returns: int
        """
        return Map.map_instance().foes_to_kill

    @staticmethod
    def GetCampaign():
        """
        Retrieve the campaign of the current map.
        Args: None
        Returns: tuple (int, str)
        """
        campaign = Map.map_instance().campaign
        return campaign.ToInt(), campaign.GetName()

    @staticmethod
    def GetContinent():
        """
        Retrieve the continent of the current map.
        Args: None
        Returns: tuple (int, str)
        """
        continent = Map.map_instance().continent
        return continent.ToInt(), continent.GetName()

    @staticmethod
    def GetRegionType():
        """
        Retrieve the region type of the current map.
        Args: None
        Returns: tuple (int, str)
        """
        region_type = Map.map_instance().region_type
        return region_type.ToInt(), region_type.GetName()

    @staticmethod
    def GetDistrict():
        """Retrieve the district of the current map."""
        return Map.map_instance().district

    @staticmethod
    def GetRegion():
        """Retrieve the region of the current map."""
        region = Map.map_instance().server_region
        return region.ToInt(), region.GetName()

    @staticmethod
    def GetLanguage():
        """
        Retrieve the language of the current map.
        Args: None
        Returns: tuple (int, str)
        """
        language = Map.map_instance().language
        return language.ToInt(), language.GetName()

    @staticmethod
    def RegionFromDistrict(district):
        """
        Retrieve the region from a district.
        Args:
            district (int): The district to retrieve the region from.
        Returns: tuple (int, str)
        """
        region = Map.map_instance().RegionFromDistrict(district)
        return region.ToInt(), region.GetName()

    @staticmethod
    def LanguageFromDistrict(district):
        """
        Retrieve the language from a district.
        Args:
            district (int): The district to retrieve the language from.
        Returns: tuple (int, str)
        """
        language = Map.map_instance().LanguageFromDistrict(district)
        return language.ToInt(), language.GetName()

    @staticmethod
    def GetIsMapUnlocked(mapid=None):
        """Check if the map is unlocked."""
        if mapid is None:
            map_id = Map.GetMapID()
        else:
            map_id = mapid
        return Map.map_instance().GetIsMapUnlocked(map_id)

    @staticmethod
    def GetAmountOfPlayersInInstance():
        """Retrieve the amount of players in the current instance."""
        return Map.map_instance().amount_of_players_in_instance
    
    @staticmethod
    def GetFlags():
        """Retrieve the flags of the current map."""
        return Map.map_instance().flags
    
    @staticmethod
    def GetThumbnailID():
        """Retrieve the thumbnail ID of the current map."""
        return Map.map_instance().thumbnail_id
    
    @staticmethod
    def GetMinPlayerSize():
        """Retrieve the minimum player size of the current map."""
        return Map.map_instance().min_player_size
    
    @staticmethod
    def GetMaxPlayerSize():
        """Retrieve the maximum player size of the current map."""
        return Map.map_instance().max_player_size
    
    @staticmethod
    def GetControlledOutpostID():
        """Retrieve the controlled outpost ID of the current map."""
        return Map.map_instance().controlled_outpost_id
    
    @staticmethod
    def GetFractionMission():
        """Retrieve the fraction mission of the current map."""
        return Map.map_instance().fraction_mission
    
    @staticmethod
    def GetMinLevel():
        """Retrieve the minimum level of the current map."""
        return Map.map_instance().min_level
    
    @staticmethod
    def GetMaxLevel():
        """Retrieve the maximum level of the current map."""
        return Map.map_instance().max_level
    
    @staticmethod
    def GetNeededPQ():
        """Retrieve the needed PQ of the current map."""
        return Map.map_instance().needed_pq
    
    @staticmethod
    def GetMissionMapsTo():
        """Retrieve the mission maps to of the current map."""
        return Map.map_instance().mission_maps_to
    
    @staticmethod
    def GetIconPosition():
        """Retrieve the icon position of the current map."""
        return Map.map_instance().icon_position_x, Map.map_instance().icon_position_y
    
    @staticmethod
    def GetIconStartPosition():
        """Retrieve the icon start position of the current map."""
        return Map.map_instance().icon_start_x, Map.map_instance().icon_start_y
    
    @staticmethod
    def GetIconEndPosition():
        """Retrieve the icon end position of the current map."""
        return Map.map_instance().icon_end_x, Map.map_instance().icon_end_y
    
    @staticmethod
    def GetIconStartPositionDupe():
        """Retrieve the icon start position dupe of the current map."""
        return Map.map_instance().icon_start_x_dupe, Map.map_instance().icon_start_y_dupe
    
    @staticmethod
    def GetIconEndPositionDupe():
        """Retrieve the icon end position dupe of the current map."""
        return Map.map_instance().icon_end_x_dupe, Map.map_instance().icon_end_y_dupe

    @staticmethod
    def GetFileID():
        """Retrieve the file ID of the current map."""
        return Map.map_instance().file_id
    
    @staticmethod
    def GetMissionChronology():
        """Retrieve the mission chronology of the current map."""
        return Map.map_instance().mission_chronology
    
    @staticmethod
    def GetHAChronology():
        """Retrieve the HA chronology of the current map."""
        return Map.map_instance().ha_map_chronology
    
    @staticmethod
    def GetNameID():
        """Retrieve the name ID of the current map."""
        return Map.map_instance().name_id
    
    @staticmethod
    def GetDescriptionID():
        """Retrieve the description ID of the current map."""
        return Map.map_instance().description_id
    
    @staticmethod
    def GetMapWorldMapBounds():
        map_info = Map.map_instance()

        if map_info.icon_start_x == 0 and map_info.icon_start_y == 0 and map_info.icon_end_x == 0 and map_info.icon_end_y == 0:
            left   = float(map_info.icon_start_x_dupe)
            top    = float(map_info.icon_start_y_dupe)
            right  = float(map_info.icon_end_x_dupe)
            bottom = float(map_info.icon_end_y_dupe)
        else:
            left   = float(map_info.icon_start_x)
            top    = float(map_info.icon_start_y)
            right  = float(map_info.icon_end_x)
            bottom = float(map_info.icon_end_y)

        return left, top, right, bottom
    
    @staticmethod
    def GetMapBoundaries():
        """Retrieve the map boundaries of the current map."""
        boundaries = Map.map_instance().map_boundaries
        if len(boundaries) < 5:
            return 0.0, 0.0, 0.0, 0.0  # Optional: fallback for safety

        min_x = boundaries[1]
        min_y = boundaries[2]
        max_x = boundaries[3]
        max_y = boundaries[4]

        return min_x, min_y, max_x, max_y

    class Pathing:
        @staticmethod
        def GetPathingMaps() -> List[PyPathing.PathingMap]:
            return PyPathing.get_pathing_maps()

        class Quad:
            def __init__(self, trapezoid : PyPathing.PathingTrapezoid):
                self.trapezoid = trapezoid
                
                self.top_left:PyOverlay.Point2D = PyOverlay.Point2D(int(trapezoid.XTL), int(trapezoid.YT))
                self.top_right:PyOverlay.Point2D = PyOverlay.Point2D(int(trapezoid.XTR), int(trapezoid.YT))
                self.bottom_left:PyOverlay.Point2D = PyOverlay.Point2D(int(trapezoid.XBL), int(trapezoid.YB))
                self.bottom_right:PyOverlay.Point2D = PyOverlay.Point2D(int(trapezoid.XBR), int(trapezoid.YB))
                
            
                screen_TL = Overlay.GameMapToScreen(self.top_left.x, self.top_left.y)
                screen_TR = Overlay.GameMapToScreen(self.top_right.x, self.top_right.y)
                screen_BL = Overlay.GameMapToScreen(self.bottom_left.x, self.bottom_left.y)
                screen_BR = Overlay.GameMapToScreen(self.bottom_right.x, self.bottom_right.y)
                
                self.screen_top_left:PyOverlay.Point2D = PyOverlay.Point2D(int(screen_TL[0]), int(screen_TL[1]))
                self.screen_top_right:PyOverlay.Point2D = PyOverlay.Point2D(int(screen_TR[0]), int(screen_TR[1]))
                self.screen_bottom_left:PyOverlay.Point2D = PyOverlay.Point2D(int(screen_BL[0]), int(screen_BL[1]))
                self.screen_bottom_right:PyOverlay.Point2D = PyOverlay.Point2D(int(screen_BR[0]), int(screen_BR[1]))
                
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
                shifted_tl = Overlay.GameMapToScreen(shifted[0].x, shifted[0].y)
                shifted_tr = Overlay.GameMapToScreen(shifted[1].x, shifted[1].y)
                shifted_bl = Overlay.GameMapToScreen(shifted[2].x, shifted[2].y)
                shifted_br = Overlay.GameMapToScreen(shifted[3].x, shifted[3].y)
                return [
                    PyOverlay.Point2D(int(shifted_tl[0]), int(shifted_tl[1])),
                    PyOverlay.Point2D(int(shifted_tr[0]), int(shifted_tr[1])),
                    PyOverlay.Point2D(int(shifted_bl[0]), int(shifted_bl[1])),
                    PyOverlay.Point2D(int(shifted_br[0]), int(shifted_br[1])),
                ]
                
        @staticmethod
        def GetComputedGeometry() -> List[List[PyOverlay.Point2D]]:
            pathintg_maps = Map.Pathing.GetPathingMaps()
            geometry = []
            for layer in pathintg_maps:
                for trapezoid in layer.trapezoids:
                    geometry.append(Map.Pathing.Quad(trapezoid).GetPoints())
            return geometry
                    
                
        @staticmethod
        def GetScreenComputedGeometry() -> List[List[PyOverlay.Point2D]]:
            pathintg_maps = Map.Pathing.GetPathingMaps()
            geometry = []
            for layer in pathintg_maps:
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

                     
   

    class MiniMap:
        @staticmethod
        def GetFrameID():
            """Get the frame ID of the mini map."""
            hash = UIManager.GetHashByLabel("compass") #3268554015
            return UIManager.GetFrameIDByHash(hash)
            
        @staticmethod
        def FrameExists():
            """Check if the mini map frame is visible."""
            return UIManager.FrameExists(Map.MiniMap.GetFrameID())
        
        @staticmethod
        def GetCoords():
            """Get the coordinates of the mini map."""
            return UIManager.GetFrameCoords(Map.MiniMap.GetFrameID())
        
        @staticmethod
        def IsLocked():
            """Check if the mini map is locked."""
            return UIManager.GetBoolPreference(FlagPreference.LockCompassRotation)

    class MissionMap:
        @staticmethod
        def _mission_map_instance():
            """Return the PyMapMissionMap instance. """
            return PyMissionMap.PyMissionMap()
        
        @staticmethod
        def GetContext():
            """Get the context of the mission map."""
            return Map.MissionMap._mission_map_instance().GetContext()
        
        @staticmethod
        def IsWindowOpen():
            """Check if the mission map window is open."""
            return Map.MissionMap._mission_map_instance().window_open
        
        @staticmethod
        def GetFrameID():
            """Get the frame ID of the mission map."""
            return Map.MissionMap._mission_map_instance().frame_id
        
        @staticmethod
        def GetWindowCoords():
            """Get the window coordinates of the mission map."""
            return Map.MissionMap._mission_map_instance().left, Map.MissionMap._mission_map_instance().top, Map.MissionMap._mission_map_instance().right, Map.MissionMap._mission_map_instance().bottom
        
        @staticmethod
        def GetScale():
            """Get the scale of the mission map."""
            return Map.MissionMap._mission_map_instance().scale_x, Map.MissionMap._mission_map_instance().scale_y
        
        @staticmethod
        def GetZoom():
            """Get the zoom level of the mission map."""
            return Map.MissionMap._mission_map_instance().zoom
        
        @staticmethod
        def GetCenter():
            """Get the center coordinates of the mission map."""
            return Map.MissionMap._mission_map_instance().center_x, Map.MissionMap._mission_map_instance().center_y
        
        @staticmethod
        def GetLastClickCoords():
            """Get the last click coordinates on the mission map."""
            return Map.MissionMap._mission_map_instance().last_click_x, Map.MissionMap._mission_map_instance().last_click_y
        
        @staticmethod
        def GetPanOffset():
            """Get the pan offset of the mission map."""
            return Map.MissionMap._mission_map_instance().pan_offset_x, Map.MissionMap._mission_map_instance().pan_offset_y
        
        @staticmethod
        def GetMapScreenCenter():
            """Get the map screen center coordinates."""
            return Map.MissionMap._mission_map_instance().mission_map_screen_center_x, Map.MissionMap._mission_map_instance().mission_map_screen_center_y