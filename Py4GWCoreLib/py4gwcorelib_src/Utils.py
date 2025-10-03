#region Utils
# Utils
import math
import time
from .Color import Color
from datetime import datetime, timezone
class Utils:
    from typing import Tuple
    @staticmethod
    def HasFlag(flags: int, flag: int) -> bool:
        return (int(flags) & int(flag)) == int(flag)

    @staticmethod
    def Distance(pos1, pos2):
        """
        Purpose: Calculate the distance between two positions.
        Args:
            pos1 (tuple): The first position (x, y).
            pos2 (tuple): The second position (x, y).
        Returns: float
        """
        return math.sqrt((pos1[0] - pos2[0]) ** 2 + (pos1[1] - pos2[1]) ** 2)
    
    @staticmethod
    def RGBToNormal(r, g, b, a):
        """return a normalized RGBA tuple from 0-255 values"""
        return r / 255.0, g / 255.0, b / 255.0, a / 255.0
    
    @staticmethod
    def NormalToColor(color: Tuple[float, float, float, float]) -> "Color":
        """Convert a normalized RGBA float tuple (0.0–1.0) to 0–255 integer values."""
        r = int(color[0] * 255)
        g = int(color[1] * 255)
        b = int(color[2] * 255)
        a = int(color[3] * 255)
        return Color(r, g, b, a)

    
    @staticmethod
    def RGBToDXColor(r, g, b, a) -> int:
        return (a << 24) | (r << 16) | (g << 8) | b
    
    @staticmethod
    def RGBToColor(r, g, b, a) -> int:
        return (a << 24) | (b << 16) | (g << 8) | r
    
    @staticmethod
    def ColorToTuple(color: int) -> Tuple[float, float, float, float]:
        """Convert a 32-bit integer color (ABGR) to a normalized (0.0 - 1.0) RGBA tuple."""
        a = (color >> 24) & 0xFF  # Extract Alpha (highest 8 bits)
        b = (color >> 16) & 0xFF  # Extract Blue  (next 8 bits)
        g = (color >> 8) & 0xFF   # Extract Green (next 8 bits)
        r = color & 0xFF          # Extract Red   (lowest 8 bits)
        return r / 255.0, g / 255.0, b / 255.0, a / 255.0  # Convert to RGBA float

    @staticmethod
    def TupleToColor(color_tuple: Tuple[float, float, float, float]) -> int:
        """Convert a normalized (0.0 - 1.0) RGBA tuple back to a 32-bit integer color (ABGR)."""
        r = int(color_tuple[0] * 255)  # Convert R back to 0-255
        g = int(color_tuple[1] * 255)  # Convert G back to 0-255
        b = int(color_tuple[2] * 255)  # Convert B back to 0-255
        a = int(color_tuple[3] * 255)  # Convert A back to 0-255
        return Utils.RGBToColor(r, g, b, a)  # Encode back as ABGR
    
    @staticmethod
    def DegToRad(degrees):
        return degrees * (math.pi / 180)

    @staticmethod
    def RadToDeg(radians):
        return radians * (180 / math.pi)
    
    @staticmethod
    def TrueFalseColor(condition):
        if condition:
            return Utils.RGBToNormal(0, 255, 0, 255)
        else:
            return Utils.RGBToNormal(255, 0, 0, 255)
        
    @staticmethod
    def GetFirstFromArray(array):
        if array is None:
            return 0
        
        if len(array) > 0:
            return array[0]
        return 0
    
    @staticmethod
    def GwinchToPixels(gwinch_value: float, zoom_offset=0.0) -> float:
        from ..Map import Map

        gwinches = 96.0  # hardcoded GW unit scale
        zoom = Map.MissionMap.GetZoom() + zoom_offset
        scale_x, _ = Map.MissionMap.GetScale()

        pixels_per_gwinch = (scale_x * zoom) / gwinches
        return gwinch_value * pixels_per_gwinch

        
    @staticmethod
    def PixelsToGwinch(pixel_value: float, zoom_offset=0.0) -> float:
        from ..Map import Map

        gwinches = 96.0
        zoom = Map.MissionMap.GetZoom() + zoom_offset
        scale_x, _ = Map.MissionMap.GetScale()

        pixels_per_gwinch = (scale_x * zoom) / gwinches
        return pixel_value / pixels_per_gwinch
    
    @staticmethod
    def PixelsToUV(x: int, y: int, w: int, h: int, texture_width: int, texture_height: int) -> tuple[tuple[float, float], tuple[float, float]]:
        uv0 = (x / texture_width, y / texture_height)
        uv1 = ((x + w) / texture_width, (y + h) / texture_height)
        return uv0, uv1

    @staticmethod
    def SafeInt(value, fallback=0):
        try:
            if not math.isfinite(value):
                return fallback
            return int(value)
        except (ValueError, TypeError, OverflowError):
            return fallback
        
    @staticmethod
    def SafeFloat(value, fallback=0.0):
        try:
            if not math.isfinite(value):
                return fallback
            return float(value)
        except (ValueError, TypeError, OverflowError):
            return fallback

    @staticmethod
    def GetBaseTimestamp():
        SHMEM_ZERO_EPOCH = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0).timestamp()
        return int((time.time() - SHMEM_ZERO_EPOCH) * 1000)

    @staticmethod
    def split_uppercase(s: str) -> str:
        import re
        return re.sub(r'(?<!^)(?=[A-Z])', ' ', s)

#endregion