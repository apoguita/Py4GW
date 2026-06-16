from enum import Enum
#region Color
class Color:
    def __init__(self, r: int = 255, g: int = 255, b: int = 255, a: int = 255):
        self.name: str = "Color"
        self.r: int = r
        self.g: int = g
        self.b: int = b
        self.a: int = a
        
    # --------------- internal helpers ---------------
    @staticmethod
    def _clamp8(v: int) -> int:
        return 0 if v < 0 else 255 if v > 255 else int(v)

    @staticmethod
    def _pack_abgr(r: int, g: int, b: int, a: int) -> int:
        # ABGR = A BBBBBBBB GGGGGGGG RRRRRRRR
        return ((a & 0xFF) << 24) | ((b & 0xFF) << 16) | ((g & 0xFF) << 8) | (r & 0xFF)

    @staticmethod
    def _pack_argb(r: int, g: int, b: int, a: int) -> int:
        # ARGB = A R G B (DirectX D3DCOLOR)
        return ((a & 0xFF) << 24) | ((r & 0xFF) << 16) | ((g & 0xFF) << 8) | (b & 0xFF)

    @staticmethod
    def _pack_rgba(r: int, g: int, b: int, a: int) -> int:
        # RGBA in memory (rarely used as a single int), still useful symmetry
        return ((r & 0xFF) << 24) | ((g & 0xFF) << 16) | ((b & 0xFF) << 8) | (a & 0xFF)

    @staticmethod
    def _pack_bgra(r: int, g: int, b: int, a: int) -> int:
        return ((b & 0xFF) << 24) | ((g & 0xFF) << 16) | ((r & 0xFF) << 8) | (a & 0xFF)

    @staticmethod
    def _unpack_abgr(v: int) -> tuple[int, int, int, int]:
        a = (v >> 24) & 0xFF
        b = (v >> 16) & 0xFF
        g = (v >> 8) & 0xFF
        r = v & 0xFF
        return r, g, b, a

    @staticmethod
    def _unpack_argb(v: int) -> tuple[int, int, int, int]:
        a = (v >> 24) & 0xFF
        r = (v >> 16) & 0xFF
        g = (v >> 8) & 0xFF
        b = v & 0xFF
        return r, g, b, a
    
    # --------------- existing API (routed) ---------------     
    def set_r(self, r: int) -> None: self.r = r
    def set_g(self, g: int) -> None: self.g = g
    def set_b(self, b: int) -> None: self.b = b
    def set_a(self, a: int) -> None: self.a = a
    def set_rgba(self, r: int, g: int, b: int, a: int) -> None:
        self.r, self.g, self.b, self.a = map(self._clamp8, (r, g, b, a))

    def get_r(self) -> int: return self.r
    def get_g(self) -> int: return self.g
    def get_b(self) -> int: return self.b
    def get_a(self) -> int: return self.a
    
    def get_rgba(self) -> tuple: return (self.r, self.g, self.b, self.a)
    def to_rgba(self) -> tuple: return (self.r, self.g, self.b, self.a)

    def to_color(self) -> int:
        # “ABGR”
        return self._pack_abgr(self.r, self.g, self.b, self.a)
    
    def from_color(self, color: int) -> None:
        #"ABGR"
        r, g, b, a = self._unpack_abgr(color)
        self.set_rgba(r, g, b, a)
    
    def to_dx_color(self) -> int:
        # DirectX D3DCOLOR (ARGB)
        return self._pack_argb(self.r, self.g, self.b, self.a)
    
    def from_dx_color(self, color: int) -> None:
        # DirectX D3DCOLOR (ARGB)
        r, g, b, a = self._unpack_argb(color)
        self.set_rgba(r, g, b, a)
    
    def to_tuple(self) -> tuple: return (self.r, self.g, self.b, self.a)  
    
    @classmethod
    def from_float_tuple(cls, color: tuple[float, float, float, float]) -> "Color":
        if any(c > 255.0 for c in color):
            raise ValueError("Color components must be in the range 0.0 to 255.0")
        r, g, b, a = (int(c) for c in color)
        return cls(r, g, b, a)

    
    @classmethod
    def from_tuple(cls, color: tuple[float, float, float, float]) -> "Color":
        # Your original method: normalized floats 0..1
        if color[0] > 1.0 or color[1] > 1.0 or color[2] > 1.0 or color[3] > 1.0:
            raise ValueError("Color components must be in the range 0.0 to 1.0")
        
        r, g, b, a = [int(c * 255) for c in color]
        return cls(r, g, b, a)
    
    def to_tuple_normalized(self) -> tuple:
        return (self.r / 255, self.g / 255, self.b / 255, self.a / 255)

    @classmethod
    def from_tuple_normalized(cls, color: tuple[float, float, float, float]) -> "Color":
        if any(c > 1.0 or c < 0.0 for c in color):
            raise ValueError("Color components must be in the range 0.0 to 1.0")

        r, g, b, a = (int(c * 255) for c in color)
        return cls(r, g, b, a)

        
    def copy(self) -> "Color":
        return Color(self.r, self.g, self.b, self.a)

    @property
    def rgb_tuple(self) -> tuple[int, int, int, int]:
        """Return integer RGBA tuple (0–255)."""
        return self.to_tuple()

    @property
    def color_tuple(self) -> tuple[float, float, float, float]:
        """Return normalized RGBA tuple (0.0–1.0)."""
        return self.to_tuple_normalized()

    @property
    def color_int(self) -> int:
        """Return packed ABGR int color."""
        return self.to_color()
    
    def to_hex(self, include_alpha: bool = True) -> str:
        """Return color as hex string '#RRGGBBAA' or '#RRGGBB'."""
        if include_alpha:
            return f"#{self.r:02X}{self.g:02X}{self.b:02X}{self.a:02X}"
        else:
            return f"#{self.r:02X}{self.g:02X}{self.b:02X}"
    
    def to_rgba_string(self) -> str:
        """Return color as string 'R, G, B, A'."""
        return f"{self.r}, {self.g}, {self.b}, {self.a}"
    
    def to_abgr(self) -> int:
        return self._pack_abgr(self.r, self.g, self.b, self.a)
    
    def from_abgr(self, color: int) -> None:
        r, g, b, a = self._unpack_abgr(color)
        self.set_rgba(r, g, b, a)

    def to_argb(self) -> int:
        return self._pack_argb(self.r, self.g, self.b, self.a)
    
    def from_argb(self, color: int) -> None:
        r, g, b, a = self._unpack_argb(color)
        self.set_rgba(r, g, b, a)

    def __eq__(self, other) -> bool:
        return isinstance(other, Color) and self.to_tuple() == other.to_tuple()

    def __ne__(self, other) -> bool:
        return not self.__eq__(other)

    def __hash__(self) -> int:
        return hash(self.to_tuple())

    def __repr__(self) -> str:
        return f"{self.name} (RGBA: {self.r}, {self.g}, {self.b}, {self.a})"
    
    
    def desaturate(self, amount: float = 1.0) -> "Color":
        """
        Returns a new Color instance, desaturated toward gray by the given amount [0..1].
        0.0 = no change, 1.0 = fully grayscale.
        """
        amount = max(0.0, min(amount, 1.0))  # Clamp between 0 and 1
        gray = int(0.4 * self.r + 0.4 * self.g + 0.4 * self.b)

        new_r = int(self.r * (1 - amount) + gray * amount)
        new_g = int(self.g * (1 - amount) + gray * amount)
        new_b = int(self.b * (1 - amount) + gray * amount)

        return Color(r=new_r, g=new_g, b=new_b, a=self.a)
    
    def saturate(self, amount: float = 1.0) -> "Color":
        """
        Returns a new Color instance with increased saturation by the given amount [0..1].
        0.0 = no change, 1.0 = full saturation boost.
        """
        amount = max(0.0, min(amount, 1.0))  # Clamp between 0 and 1

        # Convert to grayscale as baseline
        gray = int(0.4 * self.r + 0.4 * self.g + 0.4 * self.b)

        # Boost color by pushing channels away from gray
        new_r = int(self.r + (self.r - gray) * amount)
        new_g = int(self.g + (self.g - gray) * amount)
        new_b = int(self.b + (self.b - gray) * amount)

        # Clamp to valid RGB range
        new_r = max(0, min(255, new_r))
        new_g = max(0, min(255, new_g))
        new_b = max(0, min(255, new_b))

        return Color(r=new_r, g=new_g, b=new_b, a=self.a)

    def opacity(self, amount: float) -> "Color":
        """
        0.0 = fully transparent, 1.0 = fully solid.
        """
        return Color(self.r, self.g, self.b, int(255 * amount))
    
    def shift(self, target: "Color", amount: float) -> "Color":
        """
        Returns a new Color instance shifted toward the target Color by the given amount [0..1].
        0.0 = no change, 1.0 = fully target color.
        """
        amount = max(0.0, min(amount, 1.0))  # Clamp between 0 and 1

        new_r = int(self.r + (target.r - self.r) * amount)
        new_g = int(self.g + (target.g - self.g) * amount)
        new_b = int(self.b + (target.b - self.b) * amount)
        new_a = int(self.a + (target.a - self.a) * amount)

        return Color(new_r, new_g, new_b, new_a)
    
    def Negate(self) -> "Color":
        """Returns a new Color instance that is the negative of this color."""
        return Color(255 - self.r, 255 - self.g, 255 - self.b, self.a)
    
    @classmethod
    def _make(cls, r: int, g: int, b: int, a: int = 255) -> "Color":
        return cls(r, g, b, a)
    
    def to_json(self) -> dict[str, int]:
        """Serialize color to a JSON-friendly dict."""
        return {"r": self.r, "g": self.g, "b": self.b, "a": self.a}

    @classmethod
    def from_json(cls, data: dict[str, int]) -> "Color":
        """Deserialize from a JSON dict into a Color instance."""
        return cls(
            data.get("r", 255),
            data.get("g", 255),
            data.get("b", 255),
            data.get("a", 255)
        )

    @classmethod
    def from_hex(cls, hex_str: str) -> "Color":
        """Create a Color from a hex string like '#RRGGBBAA' or '#RRGGBB'."""
        hex_str = hex_str.lstrip('#')
        if len(hex_str) == 6:
            r, g, b = int(hex_str[0:2], 16), int(hex_str[2:4], 16), int(hex_str[4:6], 16)
            return cls(r, g, b)
        elif len(hex_str) == 8:
            r, g, b, a = int(hex_str[0:2], 16), int(hex_str[2:4], 16), int(hex_str[4:6], 16), int(hex_str[6:8], 16)
            return cls(r, g, b, a)
        else:
            raise ValueError("Hex string must be in format '#RRGGBB' or '#RRGGBBAA'")
        
        return cls(r, g, b, a if 'a' in locals() else 255)
    
    @classmethod
    def from_rgba_string(cls, rgba_str: str) -> "Color":
        """Create a Color from a string like 'R, G, B, A' or 'R, G, B'."""
        parts = rgba_str.split(',')
        if len(parts) not in (3, 4):
            raise ValueError("RGBA string must be in format 'R, G, B' or 'R, G, B, A'")
        
        r = int(parts[0].strip())
        g = int(parts[1].strip())
        b = int(parts[2].strip())
        a = int(parts[3].strip()) if len(parts) == 4 else 255
        
        return cls(r, g, b, a)

    @classmethod
    def random(cls, a: int = 255) -> "Color":
        """Generate a random color with optional alpha."""
        import random
        return cls(
            r=random.randint(0, 255),
            g=random.randint(0, 255),
            b=random.randint(0, 255),
            a=a
        )

   
class ColorPalette(Enum):
    Markdown_White = Color(255, 255, 255, 255)
    Markdown_Blue = Color(153, 238, 255, 255)
    Markdown_Green = Color(0, 255, 0, 255)
    Markdown_Purple = Color(187, 136, 238, 255)
    Markdown_Gold = Color(255, 204, 85, 255)
    Markdown_Red = Color(255, 0, 0, 255)
    Markdown_Dull = Color(120, 120, 120, 255)
    
    Aqua = Color(0, 255, 255)
    Azure = Color(240, 255, 255)
    Beige = Color(245, 245, 220)
    Black = Color(0, 0, 0)
    Blue = Color(0, 0, 255)
    BrightGreen = Color(0, 255, 0)
    Brown = Color(165, 42, 42)
    Chocolate = Color(210, 105, 30)
    Coral = Color(255, 127, 80)
    Creme = Color(255, 238, 187)
    Crimson = Color(220, 20, 60)
    Cyan = Color(0, 255, 255)
    DarkBlue = Color(0, 0, 139)
    DarkCyan = Color(0, 139, 139)
    DarkGray = Color(169, 169, 169)
    DarkGreen = Color(0, 100, 0)
    DarkMagenta = Color(139, 0, 139)
    DarkOrange = Color(255, 140, 0)
    DarkRed = Color(139, 0, 0)
    DarkViolet = Color(148, 0, 211)
    DeepPink = Color(255, 20, 147)
    DodgerBlue = Color(30, 144, 255)
    Firebrick = Color(178, 34, 34)
    Fuchsia = Color(255, 0, 255)
    Gold = Color(255, 215, 0)
    Gray = Color(128, 128, 128)
    Green = Color(0, 128, 0)
    GwBlue = Color(0, 170, 255, 255)
    GwDisabled = Color(26, 26, 26, 255)
    GwGold = Color(225, 150, 0, 255)
    GwGreen = Color(25, 200, 0, 255)
    GwPurple = Color(110, 65, 200, 255)
    GwWhite = Color(255, 255, 255, 255)
    GwWarrior = Color(222, 185, 104, 255)
    GwRanger = Color(147, 194, 74, 255)
    GwMonk = Color(171, 215, 229, 255)
    GwNecromancer = Color(87, 174, 112, 255)
    GwMesmer = Color(161, 84, 146, 255)
    GwElementalist = Color(197, 75, 75, 255)
    GwAssassin = Color(234, 18, 125, 255)
    GwRitualist = Color(39, 234, 204, 255)
    GwParagon = Color(208, 122, 14, 255)
    GwDervish = Color(97, 115, 163, 255)
    Indigo = Color(75, 0, 130)
    Ivory = Color(255, 255, 240)
    Khaki = Color(240, 230, 140)
    Lavender = Color(230, 230, 250)
    LightBlue = Color(173, 216, 230)
    LightCoral = Color(240, 128, 128)
    LightCyan = Color(224, 255, 255)
    LightGray = Color(211, 211, 211)
    LightGold = Color(255, 233, 123, 255)
    LightGreen = Color(144, 238, 144)
    LightPink = Color(255, 182, 193)
    LightYellow = Color(255, 255, 224)
    Lime = Color(0, 255, 0)
    Magenta = Color(255, 0, 255)
    Maroon = Color(128, 0, 0)
    MidnightViolet = Color(75, 0, 130)
    Navy = Color(0, 0, 128)
    Olive = Color(128, 128, 0)
    Orange = Color(255, 165, 0)
    Orchid = Color(218, 112, 214)
    Peru = Color(205, 133, 63)
    Pink = Color(255, 192, 203)
    Plum = Color(221, 160, 221)
    Purple = Color(128, 0, 128)
    Red = Color(255, 0, 0)
    RosyBrown = Color(188, 143, 143)
    Salmon = Color(250, 128, 114)
    Sienna = Color(160, 82, 45)
    Silver = Color(192, 192, 192)
    SkyBlue = Color(135, 206, 235)
    SlateBlue = Color(106, 90, 205)
    SlateGray = Color(112, 128, 144)
    Tan = Color(210, 180, 140)
    Teal = Color(0, 128, 128)
    Thistle = Color(216, 191, 216)
    Tomato = Color(255, 99, 71)
    Turquoise = Color(64, 224, 208)
    Violet = Color(238, 130, 238)
    Wheat = Color(245, 222, 179)
    White = Color(255, 255, 255)
    Yellow = Color(200, 155, 0, 255)

    @property
    def color(self) -> Color:
        return self.value

    @classmethod
    def _normalize_name(cls, name: str) -> str:
        return ''.join(ch for ch in str(name or '').strip().lower() if ch.isalnum())

    @classmethod
    def _member_map_lower(cls) -> dict[str, 'ColorPalette']:
        # Use __members__ so aliased enum names like "Red" remain addressable.
        return {
            cls._normalize_name(member_name): member
            for member_name, member in cls.__members__.items()
        }

    @staticmethod
    def GetColor(name: str) -> Color:
        member = ColorPalette._member_map_lower().get(ColorPalette._normalize_name(name))
        return member.color if member else Color()

    @staticmethod
    def ListColors() -> list[str]:
        return list(ColorPalette.__members__.keys())

    @staticmethod
    def HasColor(name: str) -> bool:
        return ColorPalette._normalize_name(name) in ColorPalette._member_map_lower()

#endregion
