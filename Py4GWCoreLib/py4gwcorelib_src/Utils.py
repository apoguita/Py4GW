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
    
    @staticmethod  
    def base64_to_bin64(char : str) -> str:
        """Convert base64 character to 6-bit binary string (Guild Wars LSB-first order)"""
        match char:
            case 'A': return '000000'
            case 'B': return '100000'
            case 'C': return '010000'
            case 'D': return '110000'
            case 'E': return '001000'
            case 'F': return '101000'
            case 'G': return '011000'
            case 'H': return '111000'
            case 'I': return '000100'
            case 'J': return '100100'
            case 'K': return '010100'
            case 'L': return '110100'
            case 'M': return '001100'
            case 'N': return '101100'
            case 'O': return '011100'
            case 'P': return '111100'
            case 'Q': return '000010'
            case 'R': return '100010'
            case 'S': return '010010'
            case 'T': return '110010'
            case 'U': return '001010'
            case 'V': return '101010'
            case 'W': return '011010'
            case 'X': return '111010'
            case 'Y': return '000110'
            case 'Z': return '100110'
            case 'a': return '010110'
            case 'b': return '110110'
            case 'c': return '001110'
            case 'd': return '101110'
            case 'e': return '011110'
            case 'f': return '111110'
            case 'g': return '000001'
            case 'h': return '100001'
            case 'i': return '010001'
            case 'j': return '110001'
            case 'k': return '001001'
            case 'l': return '101001'
            case 'm': return '011001'
            case 'n': return '111001'
            case 'o': return '000101'
            case 'p': return '100101'
            case 'q': return '010101'
            case 'r': return '110101'
            case 's': return '001101'
            case 't': return '101101'
            case 'u': return '011101'
            case 'v': return '111101'
            case 'w': return '000011'
            case 'x': return '100011'
            case 'y': return '010011'
            case 'z': return '110011'
            case '0': return '001011'
            case '1': return '101011'
            case '2': return '011011'
            case '3': return '111011'
            case '4': return '000111'
            case '5': return '100111'
            case '6': return '010111'
            case '7': return '110111'
            case '8': return '001111'
            case '9': return '101111'
            case '+': return '011111'
            case '/': return '111111'
        return '000000'  # Default to 'A' if character is not found

    @staticmethod
    def dec_to_bin64(decimal : int, bits : int) -> str:
        """Convert decimal to binary string with specified number of bits (LSB first order)"""
        binary = bin(decimal)[2:]  # Remove '0b' prefix
        binary = binary.zfill(bits)  # Pad with zeros to reach desired length
        return binary[::-1]  # Reverse to match LSB-first order used in Guild Wars

    @staticmethod
    def bin64_to_base64(binary : str) -> str:
        """Convert binary string to base64 character using Guild Wars specific mapping"""
        # Pad binary to multiple of 6 bits
        while len(binary) % 6 != 0:
            binary += '0'

        # Create reverse mapping from the existing base64_to_bin64 function
        bin_to_char = {}
        chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/'
        for char in chars:
            bin_pattern = Utils.base64_to_bin64(char)
            bin_to_char[bin_pattern] = char

        result = ''
        for i in range(0, len(binary), 6):
            chunk = binary[i:i+6]
            if chunk in bin_to_char:
                result += bin_to_char[chunk]
            else:
                # Fallback - this shouldn't happen if encoding is correct
                result += 'A'

        return result

    @staticmethod
    def bin64_to_dec(binary):
        """Convert binary string to decimal (LSB-first order)"""
        decimal = 0
        for i in range(0, len(binary)):
            if binary[i] == '1':
                decimal += 2**(i)
        return decimal

#endregion