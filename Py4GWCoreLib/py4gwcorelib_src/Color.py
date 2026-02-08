
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

    def opacify(self, amount: float) -> "Color":
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
    def random(cls, a: int = 255) -> "Color":
        """Generate a random color with optional alpha."""
        import random
        return cls(
            r=random.randint(0, 255),
            g=random.randint(0, 255),
            b=random.randint(0, 255),
            a=a
        )
    
class ColorPalette:
    _colors: dict[str, Color] = {
        "aqua": Color(0, 255, 255),
        "azure": Color(240, 255, 255),
        "beige": Color(245, 245, 220),
        "black": Color(0, 0, 0),
        "blue": Color(0, 0, 255),
        "bright_green": Color(0, 255, 0),
        "brown": Color(165, 42, 42),
        "chocolate": Color(210, 105, 30),
        "coral": Color(255, 127, 80),
        "creme": Color(255, 238, 187),
        "crimson": Color(220, 20, 60),
        "cyan": Color(0, 255, 255),
        "dark_blue": Color(0, 0, 139),
        "dark_cyan": Color(0, 139, 139),
        "dark_gray": Color(169, 169, 169),
        "dark_green": Color(0, 100, 0),
        "dark_magenta": Color(139, 0, 139),
        "dark_orange": Color(255, 140, 0),
        "dark_red": Color(139, 0, 0),
        "dark_violet": Color(148, 0, 211),
        "deep_pink": Color(255, 20, 147),
        "dodger_blue": Color(30, 144, 255),
        "firebrick": Color(178, 34, 34),
        "fuchsia": Color(255, 0, 255),
        "gold": Color(255, 215, 0),
        "gray": Color(128, 128, 128),
        "green": Color(0, 128, 0),
        "gw_blue": Color(0, 170, 255, 255),
        "gw_disabled":  Color(26, 26, 26, 255),
        "gw_gold": Color(225, 150, 0, 255),
        "gw_green": Color(25, 200, 0, 255),
        "gw_purple": Color(110, 65, 200, 255),
        "gw_white": Color(255, 255, 255, 255),
        "gw_warrior": Color(222, 185, 104, 255), 
        "gw_ranger": Color(147, 194, 74, 255),
        "gw_monk": Color(171, 215, 229, 255),
        "gw_necromancer": Color(87, 174, 112, 255),
        "gw_mesmer": Color(161, 84, 146, 255),
        "gw_elementalist": Color(197, 75, 75, 255),
        "gw_assassin": Color(234, 18, 125, 255),
        "gw_ritualist": Color(39, 234, 204, 255),
        "gw_paragon": Color(208, 122, 14, 255),
        "gw_dervish": Color(97, 115, 163, 255),
        "indigo": Color(75, 0, 130),
        "ivory": Color(255, 255, 240),
        "khaki": Color(240, 230, 140),
        "lavender": Color(230, 230, 250),
        "light_blue": Color(173, 216, 230),
        "light_coral": Color(240, 128, 128),
        "light_cyan": Color(224, 255, 255),
        "light_gray": Color(211, 211, 211),
        "light_gold": Color(255, 233, 123, 255),
        "light_green": Color(144, 238, 144),
        "light_pink": Color(255, 182, 193),
        "light_yellow": Color(255, 255, 224),
        "lime": Color(0, 255, 0),
        "magenta": Color(255, 0, 255),
        "maroon": Color(128, 0, 0),
        "midnight_violet": Color(75, 0, 130), 
        "navy": Color(0, 0, 128),
        "olive": Color(128, 128, 0),
        "orange": Color(255, 165, 0),
        "orchid": Color(218, 112, 214),
        "peru": Color(205, 133, 63),
        "pink": Color(255, 192, 203),
        "plum": Color(221, 160, 221),
        "purple": Color(128, 0, 128),
        "red": Color(255, 0, 0),
        "rosy_brown": Color(188, 143, 143),
        "salmon": Color(250, 128, 114),
        "sienna": Color(160, 82, 45),
        "silver": Color(192, 192, 192),
        "sky_blue": Color(135, 206, 235),
        "slate_blue": Color(106, 90, 205),
        "slate_gray": Color(112, 128, 144),
        "tan": Color(210, 180, 140),
        "teal": Color(0, 128, 128),
        "thistle": Color(216, 191, 216),
        "tomato": Color(255, 99, 71),
        "turquoise": Color(64, 224, 208),
        "violet": Color(238, 130, 238),
        "wheat": Color(245, 222, 179),
        "white": Color(255, 255, 255),
        "yellow": Color(200, 155, 0, 255)
    }

    @staticmethod
    def GetColor(name: str) -> Color:
        return ColorPalette._colors.get(name.lower(), Color())

    @staticmethod
    def ListColors() -> list[str]:
        return list(ColorPalette._colors.keys())

    @staticmethod
    def HasColor(name: str) -> bool:
        return name.lower() in ColorPalette._colors

#endregion