#region Utils
# Utils
import math
import time
import PyImGui
import re
from .Color import Color
from datetime import datetime, timezone
from ..enums import CAP_EXPERIENCE, CAP_STEP, EXPERIENCE_PROGRESSION
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
    
<<<<<<< Updated upstream
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
=======
    @staticmethod
    def GetExperienceProgression(xp: int) -> float:
        """
        Given total XP, return (level, percent_in_level, skill_points_from_xp).
        https://wiki.guildwars.com/wiki/Experience
        """
        # Before overflow
        for lvl, base, req in EXPERIENCE_PROGRESSION:
            if xp < base + req:
                pct = (xp - base) / req * 100.0
                # skill points only after level 20
                skill_points = max(0, lvl - 20)
                return pct

        # Overflow past 182,600
        overflow = xp - CAP_EXPERIENCE
        extra_levels = overflow // CAP_STEP
        remainder = overflow % CAP_STEP
        lvl = 23 + extra_levels
        pct = remainder / CAP_STEP * 100.0

        # Skill points: from 21 onward
        # Level 21 = +1, Level 22 = +2, then +1 per 15k chunk
        skill_points = (22 - 20)  # 2 from reaching 21 & 22
        skill_points += extra_levels + (1 if remainder > 0 else 0)

        return pct

    @staticmethod
    def TokenizeMarkupText(text: str, max_width: float):
        """Return tokenized lines of markup-ready text (no rendering)."""
        # Identify atomic blocks
        style = PyImGui.StyleConfig()
        style.Pull()
        _orig_cell = style.CellPadding
        _orig_item = style.ItemSpacing
        style.CellPadding = (_orig_cell[0], 0.0)   # ↓ vertical padding inside table rows
        style.ItemSpacing = (_orig_item[0], 0.0)   # ↓ spacing between stacked rows
        style.Push()

        atomic_blocks = re.findall(r"<c=@[^>]+>.*?</c>", text, flags=re.IGNORECASE)
        tmp_placeholder = text
        block_map = {}
        for i, block in enumerate(atomic_blocks):
            key = f"@@BLOCK{i}@@"
            block_map[key] = block
            tmp_placeholder = tmp_placeholder.replace(block, key)

        tag_or_text = re.compile(r"(<[^>]+>|\{[^}]+\}|@@BLOCK\d+@@|[^\{\}<@\n\r]+|\n+|\r+)")
        parts = tag_or_text.findall(tmp_placeholder)
        lines, current_line, visible = [], [], ""
        inside_bullet = False

        def flush_line():
            nonlocal current_line, visible
            if current_line:
                lines.append("".join(current_line).rstrip())
                current_line = []
                visible = ""

        for part in parts:
            low = part.lower()
            # --- Handle newlines ---
            if part == "\n" or part == "\r" or part == "\r\n" or "\n" in part:
                flush_line()
                lines.append("")
                inside_bullet = False
                continue
            # --- Handle breaks ---
            if low in ("<brx>", "<br>", "<brx/>"):
                flush_line()
                inside_bullet = False
                continue
            if low in ("<p>", "</p>"):
                flush_line()
                lines.append("")  # paragraph break
                inside_bullet = False
                continue
            # --- Bullet start ---
            if low in ("{s}", "{sc}"):
                inside_bullet = True
                current_line.append(part)
                continue
            # --- Protected atomic color blocks ---
            if part.startswith("@@BLOCK"):
                block = block_map[part]
                inner_text = re.sub(r"^<c=@[^>]+>|</c>$", "", block, flags=re.IGNORECASE)
                visible_width = PyImGui.calc_text_size(visible + inner_text)[0]
                if visible_width > max_width and visible and not inside_bullet:
                    flush_line()
                current_line.append(block)
                visible += inner_text
                continue
            # --- Tags (non-visible markup) ---
            if part.startswith("<") or part.startswith("{"):
                current_line.append(part)
                continue
            # --- Word-based wrapping (disabled for bullets) ---
            if inside_bullet:
                # append directly without wrapping logic
                current_line.append(part)
                visible += part
                continue
            
            words = part.split(" ")
            for w in words:
                if not w:
                    #current_line.append(" ")
                    visible += ""
                    continue
                test = (visible + " " + w).strip() if visible else w
                if PyImGui.calc_text_size(test)[0] > max_width and visible:
                    flush_line()
                    current_line.append(w)
                    visible = w
                else:
                    if visible:
                        current_line.append(" ")
                    current_line.append(w)
                    visible = test

        if current_line:
            flush_line()
        
        # --- Tokenize each split line into markup tokens ---
        pattern = re.compile(r"(<[^>]+>|\{[^}]+\})")
        tokenized_lines = []
        for line in lines:
            tokens, pos = [], 0
            for match in pattern.finditer(line):
                start, end = match.span()
                if start > pos:
                    tokens.append({"type": "text", "value": line[pos:start]})
                tag = match.group(0).strip()

                if tag.lower().startswith("<c=@"):
                    tokens.append({"type": "color_start", "value": tag[3:-1].strip()})
                elif tag.lower() == "</c>":
                    tokens.append({"type": "color_end"})
                elif tag.lower() in ("<brx>", "<br>", "<brx/>"):
                    tokens.append({"type": "line_break"})
                elif tag.lower() in ("<p>", "</p>"):
                    tokens.append({"type": "paragraph"})
                elif tag.lower() == "{sc}":
                    tokens.append({"type": "bullet", "gray": True})
                elif tag.lower() == "{s}":
                    tokens.append({"type": "bullet", "gray": False})
                pos = end
            if pos < len(line):
                tokens.append({"type": "text", "value": line[pos:]})
            tokenized_lines.append(tokens)
            
        style.CellPadding = _orig_cell
        style.ItemSpacing = _orig_item
        style.Push()

        return tokenized_lines
>>>>>>> Stashed changes

#endregion