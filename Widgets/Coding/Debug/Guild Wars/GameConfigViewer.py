from Py4GWCoreLib import *
import PyImGui
from typing import Any

MODULE_NAME = "Gw config Manager"

# 1) index (scan code) -> VK code map (start identity, override mismatches)
INDEX_TO_VK = {i: 0 for i in range(256)}
# override as you discover them:
INDEX_TO_VK[0] = Key.LAlt.value
INDEX_TO_VK[1] = Key.LCtrl.value
INDEX_TO_VK[2] = Key.Shift.value
INDEX_TO_VK[3] = Key.Grave.value
INDEX_TO_VK[4] = Key.Backslash.value
INDEX_TO_VK[5] = Key.CapsLock.value
INDEX_TO_VK[6] = Key.Comma.value
INDEX_TO_VK[7] = Key.Minus.value
INDEX_TO_VK[8] = Key.Equal.value
INDEX_TO_VK[9] = Key.Escape.value
INDEX_TO_VK[10] = Key.LeftBrace.value
INDEX_TO_VK[11] = Key.Unmappable.value
INDEX_TO_VK[12] = Key.Period.value
INDEX_TO_VK[13] = Key.RightBrace.value
INDEX_TO_VK[14] = Key.Semicolon.value
INDEX_TO_VK[15] = Key.Slash.value
INDEX_TO_VK[16] = Key.PrintScreen.value
INDEX_TO_VK[17] = Key.Apostrophe.value
INDEX_TO_VK[18] = Key.Backspace.value
INDEX_TO_VK[19] = Key.Delete.value
INDEX_TO_VK[20] = Key.Enter.value
INDEX_TO_VK[21] = Key.Space.value
INDEX_TO_VK[22] = Key.Tab.value
INDEX_TO_VK[23] = Key.End.value
INDEX_TO_VK[24] = Key.Home.value
INDEX_TO_VK[25] = Key.Insert.value
INDEX_TO_VK[26] = Key.PageDown.value
INDEX_TO_VK[27] = Key.PageUp.value
INDEX_TO_VK[28] = Key.DownArrow.value
INDEX_TO_VK[29] = Key.LeftArrow.value
INDEX_TO_VK[30] = Key.RightArrow.value
INDEX_TO_VK[31] = Key.UpArrow.value
INDEX_TO_VK[32] = Key.F1.value
INDEX_TO_VK[33] = Key.F2.value
INDEX_TO_VK[34] = Key.F3.value
INDEX_TO_VK[35] = Key.F4.value
INDEX_TO_VK[36] = Key.F5.value
INDEX_TO_VK[37] = Key.F6.value
INDEX_TO_VK[38] = Key.F7.value
INDEX_TO_VK[39] = Key.F8.value
INDEX_TO_VK[40] = Key.F9.value
INDEX_TO_VK[41] = Key.F10.value
INDEX_TO_VK[42] = Key.F11.value
INDEX_TO_VK[43] = Key.F12.value





INDEX_TO_VK[48] = Key.Zero.value
INDEX_TO_VK[49] = Key.One.value
INDEX_TO_VK[50] = Key.Two.value
INDEX_TO_VK[51] = Key.Three.value
INDEX_TO_VK[52] = Key.Four.value
INDEX_TO_VK[53] = Key.Five.value
INDEX_TO_VK[54] = Key.Six.value
INDEX_TO_VK[55] = Key.Seven.value
INDEX_TO_VK[56] = Key.Eight.value
INDEX_TO_VK[57] = Key.Nine.value








INDEX_TO_VK[65] = Key.A.value
INDEX_TO_VK[66] = Key.B.value
INDEX_TO_VK[67] = Key.C.value
INDEX_TO_VK[68] = Key.D.value
INDEX_TO_VK[69] = Key.E.value
INDEX_TO_VK[70] = Key.F.value
INDEX_TO_VK[71] = Key.G.value
INDEX_TO_VK[72] = Key.H.value
INDEX_TO_VK[73] = Key.I.value
INDEX_TO_VK[74] = Key.J.value
INDEX_TO_VK[75] = Key.K.value
INDEX_TO_VK[76] = Key.L.value
INDEX_TO_VK[77] = Key.M.value
INDEX_TO_VK[78] = Key.N.value
INDEX_TO_VK[79] = Key.O.value
INDEX_TO_VK[80] = Key.P.value
INDEX_TO_VK[81] = Key.Q.value
INDEX_TO_VK[82] = Key.R.value
INDEX_TO_VK[83] = Key.S.value
INDEX_TO_VK[84] = Key.T.value
INDEX_TO_VK[85] = Key.U.value
INDEX_TO_VK[86] = Key.V.value
INDEX_TO_VK[87] = Key.W.value
INDEX_TO_VK[88] = Key.X.value
INDEX_TO_VK[89] = Key.Y.value
INDEX_TO_VK[90] = Key.Z.value




INDEX_TO_VK[95] = Key.Numpad0.value
INDEX_TO_VK[96] = Key.Numpad1.value
INDEX_TO_VK[97] = Key.Numpad2.value
INDEX_TO_VK[98] = Key.Numpad3.value
INDEX_TO_VK[99] = Key.Numpad4.value
INDEX_TO_VK[100] = Key.Numpad5.value
INDEX_TO_VK[101] = Key.Numpad6.value
INDEX_TO_VK[102] = Key.Numpad7.value
INDEX_TO_VK[103] = Key.Numpad8.value
INDEX_TO_VK[104] = Key.Numpad9.value
INDEX_TO_VK[106] = Key.NumpadSubtract.value
INDEX_TO_VK[114] = Key.RAlt.value
INDEX_TO_VK[115] = Key.RCtrl.value

CONTROL_MAP = {
    128: "Action: Attack/Interact (Do It)",
    129: "Inventory: Activate Weapon Set 1",
    130: "Inventory: Activate Weapon Set 2",
    131: "Inventory: Activate Weapon Set 3",
    132: "Inventory: Activate Weapon Set 4",
    133: "Panel: Close All Panels",
    134: "Inventory: Cycle Equipment",
    135: "Miscelaneous: Log Out",
    136: "Chat: Open Chat",
    137: "Targeting: Show Others",
    138: "Panel: Open Hero",
    139: "Inventory: Open Inventory",
    140: "Panel: Open World Map",
    141: "Panel: Open Options",
    142: "Panel: Open Quest",
    143: "Panel: Open Skills and Attributes",
    144: "Camera: Reverse Camera",
    145: "Movement: Strafe Left",
    146: "Movement: Strafe Right",
    147: "Targeting: Foe - Nearest",
    148: "Targeting: Show Targets",
    149: "Targeting: Foe - Next",
    150: "Targeting: Party Member - 1",
    151: "Targeting: Party Member - 2",
    152: "Targeting: Party Member - 3",
    153: "Targeting: Party Member - 4",
    154: "Targeting: Party Member - 5",
    155: "Targeting: Party Member - 6",
    156: "Targeting: Party Member - 7",
    157: "Targeting: Party Member - 8",
    158: "Targeting: Foe - Previous",
    159: "Targeting: Priority Target",
    160: "Targeting: Self",
    161: "Chat: Toggle Chat",
    162: "Movement: Turn Left",
    163: "Movement: Turn Right",
    164: "Action: Use Skill 1",
    165: "Action: Use Skill 2",
    166: "Action: Use Skill 3",
    167: "Action: Use Skill 4",
    168: "Action: Use Skill 5",
    169: "Action: Use Skill 6",
    170: "Action: Use Skill 7",
    171: "Action: Use Skill 8",
    172: "Movement: Move Backward",
    173: "Movement: Move Forward",
    174: "Miscelaneous: Screenshot",
    175: "Action: Cancel Action",
    176: "Camera: Free Camera",
    177: "Movement: Reverse Direction",
    178: "Inventory: Open Backpack",
    179: "Inventory: Open Belt Pouch",
    180: "Inventory: Open Bag 1",
    181: "Inventory: Open Bag 2",
    182: "Panel: Open Mission Map",
    183: "Movement: Automatic Run",
    184: "Inventory: Toggle All Bags",
    185: "Panel: Open Friends",
    186: "Panel: Open Guild",
    187: "Miscelaneous: Language Quick Toggle",
    188: "Targeting: Ally - Nearest",
    189: "Panel: Open Score Chart",
    190: "Chat: Reply",
    191: "Panel: Open Party",
    192: "Chat: Start Chat Command",
    193: "Panel: Open Customize Layout",
    194: "Panel: Open Observe",
    195: "Targeting: Item - Nearest",
    196: "Targeting: Item - Next",
    197: "Targeting: Item - Previous",
    198: "Targeting: Party Member - 9",
    199: "Targeting: Party Member - 10",
    200: "Targeting: Party Member - 11",
    201: "Targeting: Party Member - 12",
    202: "Targeting: Party Member - Next",
    203: "Targeting: Party Member - Previous",
    204: "Action: Follow",
    205: "Action: Drop Item",
    206: "Camera: Zoom In",
    207: "Camera: Zoom Out",
    208: "Action: Suppress Action",
    209: "Panel: Open Load from Equipment Template",
    210: "Panel: Open Load from Skills Template",
    211: "Panel: Open Templates Manager",
    219: "Action: Clear Party Commands",
    220: "Panel: Open Hero Commander 1",
    221: "Panel: Open Hero Commander 2",
    222: "Panel: Open Hero Commander 3",
    223: "Panel: Open Pet Commander",
    212: "Panel: Open Save to Equipment Template",
    213: "Panel: Open Save to Skills Template",
    214: "Action: Command Party",
    215: "Action: Command Hero 1",
    216: "Action: Command Hero 2",
    217: "Action: Command Hero 3",
    218: "Panel: Open PvP Equipment",
    224: "Panel: OpenHero 1 Pet Commander",
    225: "Panel: OpenHero 2 Pet Commander",
    226: "Panel: OpenHero 3 Pet Commander",
    227: "Targeting: Clear Target",
    228: "Panel: Open Help",
    229: "Action: Order Hero 1 to Use Skill 1",
    230: "Action: Order Hero 1 to Use Skill 2",
    231: "Action: Order Hero 1 to Use Skill 3",
    232: "Action: Order Hero 1 to Use Skill 4",
    233: "Action: Order Hero 1 to Use Skill 5",
    234: "Action: Order Hero 1 to Use Skill 6",
    235: "Action: Order Hero 1 to Use Skill 7",
    236: "Action: Order Hero 1 to Use Skill 8",
    237: "Action: Order Hero 2 to Use Skill 1",
    238: "Action: Order Hero 2 to Use Skill 2",
    239: "Action: Order Hero 2 to Use Skill 3",
    240: "Action: Order Hero 2 to Use Skill 4",
    241: "Action: Order Hero 2 to Use Skill 5",
    242: "Action: Order Hero 2 to Use Skill 6",
    243: "Action: Order Hero 2 to Use Skill 7",
    244: "Action: Order Hero 2 to Use Skill 8",
    245: "Action: Order Hero 3 to Use Skill 1",
    246: "Action: Order Hero 3 to Use Skill 2",
    247: "Action: Order Hero 3 to Use Skill 3",
    248: "Action: Order Hero 3 to Use Skill 4",
    249: "Action: Order Hero 3 to Use Skill 5",
    250: "Action: Order Hero 3 to Use Skill 6",
    251: "Action: Order Hero 3 to Use Skill 7",
    252: "Action: Order Hero 3 to Use Skill 8",
    253: "Panel: Open Minion List",
    254: "Panel: OpenHero 4 Pet Commander",
    255: "Panel: OpenHero 5 Pet Commander",
    256: "Panel: OpenHero 6 Pet Commander",
    257: "Panel: OpenHero 7 Pet Commander",
    258: "Action: Command Hero 4",
    259: "Action: Command Hero 5",
    260: "Action: Command Hero 6",
    261: "Action: Command Hero 7",
    262: "Action: Order Hero 4 to Use Skill 1",
    263: "Action: Order Hero 4 to Use Skill 2",
    264: "Action: Order Hero 4 to Use Skill 3",
    265: "Action: Order Hero 4 to Use Skill 4",
    266: "Action: Order Hero 4 to Use Skill 5",
    267: "Action: Order Hero 4 to Use Skill 6",
    268: "Action: Order Hero 4 to Use Skill 7",
    269: "Action: Order Hero 4 to Use Skill 8",
    270: "Action: Order Hero 5 to Use Skill 1",
    271: "Action: Order Hero 5 to Use Skill 2",
    272: "Action: Order Hero 5 to Use Skill 3",
    273: "Action: Order Hero 5 to Use Skill 4",
    274: "Action: Order Hero 5 to Use Skill 5",
    275: "Action: Order Hero 5 to Use Skill 6",
    276: "Action: Order Hero 5 to Use Skill 7",
    277: "Action: Order Hero 5 to Use Skill 8",
    278: "Action: Order Hero 6 to Use Skill 1",
    279: "Action: Order Hero 6 to Use Skill 2",
    280: "Action: Order Hero 6 to Use Skill 3",
    281: "Action: Order Hero 6 to Use Skill 4",
    282: "Action: Order Hero 6 to Use Skill 5",
    283: "Action: Order Hero 6 to Use Skill 6",
    284: "Action: Order Hero 6 to Use Skill 7",
    285: "Action: Order Hero 6 to Use Skill 8",
    286: "Action: Order Hero 7 to Use Skill 1",
    287: "Action: Order Hero 7 to Use Skill 2",
    288: "Action: Order Hero 7 to Use Skill 3",
    289: "Action: Order Hero 7 to Use Skill 4",
    290: "Action: Order Hero 7 to Use Skill 5",
    291: "Action: Order Hero 7 to Use Skill 6",
    292: "Action: Order Hero 7 to Use Skill 7",
    293: "Action: Order Hero 7 to Use Skill 8",
    294: "Panel: Open Hero Commander 4",
    295: "Panel: Open Hero Commander 5",
    296: "Panel: Open Hero Commander 6",
    297: "Panel: Open Hero Commander 7",

}

class PrefType:
    INT = "int"
    BOOL = "bool"
    STRING = "string"
    ENUM = "enum"

class Preferences:
    # preference mapping: name -> (type, preference_enum, enum_cls, flipped)
    _PREF_MAP = {
        "TextLanguage":   (PrefType.INT,    NumberPreference.TextLanguage,   ServerLanguage, False),
        "AudioLanguage":  (PrefType.INT,    NumberPreference.AudioLanguage,  ServerLanguage, False),
        "ChatFilterLevel":(PrefType.INT,    NumberPreference.ChatFilterLevel,None, False),
        "InGameClock":    (PrefType.INT,    NumberPreference.ClockMode,      InGameClockMode, False),
        "DamageTextSize": (PrefType.INT,    NumberPreference.DamageTextSize, None, False),
        "FieldOfView":    (PrefType.INT,    NumberPreference.FieldOfView,    None, False),
        "CameraRotationSpeed": (PrefType.INT, NumberPreference.CameraRotationSpeed, None, False),
        "LockCompassRotation": (PrefType.BOOL, FlagPreference.LockCompassRotation, None, False),
        "DisableMouseWalking": (PrefType.BOOL, FlagPreference.DisableMouseWalking, None, True),
        "InvertMouseControlOfCamera": (PrefType.BOOL, FlagPreference.InvertMouseControlOfCamera, None, False),
        "DoubleTapForwardToRunBackwardsToFlip": (PrefType.BOOL, FlagPreference.DoubleTapForwardToRunBackwardsToFlip, None, False),
        "DoubleClickToInteract": (PrefType.BOOL, FlagPreference.DoubleClickToInteract, None, True),
        "AlwaysShowNearbyNamesPvP": (PrefType.BOOL, FlagPreference.AlwaysShowNearbyNamesPvP, None, False),
        "DoNotCloseWindowsOnEscape": (PrefType.BOOL, FlagPreference.DoNotCloseWindowsOnEscape, None, False),
        "DoNotShowSkillTipsOnSkillBars": (PrefType.BOOL, FlagPreference.DoNotShowSkillTipsOnSkillBars, None, False),
        "DoNotShowSkillTipsOnEffectMonitor": (PrefType.BOOL, FlagPreference.DoNotShowSkillTipsOnEffectMonitor, None, False),
        "ShowTextInSkillFloaters": (PrefType.BOOL, FlagPreference.ShowTextInSkillFloaters, None, False),
        "AutoTargetFoes": (PrefType.BOOL, FlagPreference.AutoTargetFoes, None, False),
        "AutoTargetNPCs": (PrefType.BOOL, FlagPreference.AutoTargetNPCs, None, False),
        "FadeDistantNameTags": (PrefType.BOOL, FlagPreference.FadeDistantNameTags, None, True),
        "ConciseSkillDescriptions": (PrefType.BOOL, FlagPreference.ConciseSkillDescriptions, None, False),
        "WhispersFromFriendsEtcOnly": (PrefType.BOOL, FlagPreference.WhispersFromFriendsEtcOnly, None, False),
        "ShowChatTimestamps": (PrefType.BOOL, FlagPreference.ShowChatTimestamps, None, False),
        "ShowCollapsedBags": (PrefType.BOOL, FlagPreference.ShowCollapsedBags, None, False),
        "ItemRarityBorder": (PrefType.BOOL, FlagPreference.ItemRarityBorder, None, False),
        "AlwaysShowAllyNames": (PrefType.BOOL, FlagPreference.AlwaysShowAllyNames, None, False),
        "AlwaysShowFoeNames": (PrefType.BOOL, FlagPreference.AlwaysShowFoeNames, None, False),
        "WindowSizeX": (PrefType.INT, NumberPreference.WindowSizeX, None, False),
        "WindowSizeY": (PrefType.INT, NumberPreference.WindowSizeY, None, False),
        "RefreshRate": (PrefType.INT, NumberPreference.RefreshRate, None, False),
        "InterfaceSize": (PrefType.ENUM, EnumPreference.InterfaceSize, InterfaceSize, False),
        "AntiAliasing": (PrefType.ENUM, EnumPreference.AntiAliasing, AntiAliasing, False),
        "TerrainQuality": (PrefType.ENUM, EnumPreference.TerrainQuality, TerrainQuality, False),
        "Reflections": (PrefType.ENUM, EnumPreference.Reflections, Reflections, False),
        "TextureQuality": (PrefType.INT, NumberPreference.TextureQuality, TextureQuality, False),
        "ShadowQuality": (PrefType.ENUM, EnumPreference.ShadowQuality, ShadowQuality, False),
        "ShaderQuality": (PrefType.ENUM, EnumPreference.ShaderQuality, ShaderQuality, False),
        "FrameLimiter": (PrefType.ENUM, EnumPreference.FrameLimiter, FrameLimiter, False),
        "FullscreenGamma": (PrefType.INT, NumberPreference.FullscreenGamma, None, False),
        "WaitForVSync": (PrefType.BOOL, FlagPreference.WaitForVSync, None, False),
        "UseBestTextureFiltering": (PrefType.INT, NumberPreference.UseBestTextureFiltering, BoolPreference, False),
        "EnhancedDrawDistance": (PrefType.BOOL, FlagPreference.EnhancedDrawDistance, None, False),
        "UseHighResolutionTexturesInOutposts": (PrefType.BOOL, FlagPreference.UseHighResolutionTexturesInOutposts, None, False),
        "MasterVolume": (PrefType.INT, NumberPreference.MasterVolume, None, False),
        "MusicVolume": (PrefType.INT, NumberPreference.MusicVolume, None, False),
        "BackgroundVolume": (PrefType.INT, NumberPreference.BackgroundVolume, None, False),
        "EffectsVolume": (PrefType.INT, NumberPreference.EffectsVolume, None, False),
        "DialogVolume": (PrefType.INT, NumberPreference.DialogVolume, None, False),
        "UIVolume": (PrefType.INT, NumberPreference.UIVolume, None, False),
        "MuteWhenGuildWarsIsInBackground": (PrefType.BOOL, FlagPreference.MuteWhenGuildWarsIsInBackground, None, True),
        "SoundQuality": (PrefType.INT, NumberPreference.SoundQuality, None, False),
        "OptimizeForStereo": (PrefType.BOOL, FlagPreference.OptimizeForStereo, None, False),
        "ScreenBorderless": (PrefType.INT, NumberPreference.ScreenBorderless, None, False),

    }

    def __init__(self):
        self._values: dict[str, object] = {}

    def Load(self):
        """Fetch all preferences from UIManager based on type."""
        for name, (ptype, pref_enum, _, flipped) in self._PREF_MAP.items():
            if ptype == PrefType.INT:
                self._values[name] = UIManager.GetIntPreference(pref_enum.value)
            elif ptype == PrefType.BOOL:
                raw = UIManager.GetBoolPreference(pref_enum.value)
                self._values[name] = not raw if flipped else raw
            elif ptype == PrefType.STRING:
                self._values[name] = UIManager.GetStringPreference(pref_enum.value)
            elif ptype == PrefType.ENUM:
                self._values[name] = UIManager.GetEnumPreference(pref_enum.value)


    def Get(self, name: str) -> object:
        """Get raw value (int, bool, or string)."""
        return self._values[name]

    def GetWithEnum(self, name: str) -> tuple[object, str]:
        """Get value and enum name (if enum is configured)."""
        value = self._values[name]
        enum_cls = self._PREF_MAP[name][2]
        if enum_cls:
            try:
                return value, enum_cls(value).name
            except ValueError:
                return value, "Unknown"
        return value, str(value)

    def Set(self, name: str, value: Any):
        """Set logical value and push to UIManager with flip-handling."""
        ptype, pref_enum, _, flipped = self._PREF_MAP[name]
        self._values[name] = value
        if ptype == PrefType.INT:
            UIManager.SetIntPreference(pref_enum.value, int(value))
        elif ptype == PrefType.BOOL:
            raw = not value if flipped else bool(value)
            UIManager.SetBoolPreference(pref_enum.value, raw)
        elif ptype == PrefType.STRING:
            UIManager.SetStringPreference(pref_enum.value, str(value))
            
    def GetKeyMappings(self) -> list[int]:
        """Get current key mappings."""
        return UIManager.GetKeyMappings()
    
    def SetKeyMappings(self, mappings: list[int]):
        """Set key mappings."""
        UIManager.SetKeyMappings(mappings)



GwPreferences = Preferences()

test_value = 13

_last_probe_results: dict[int, bool | None] | None = None
_last_int_probe_results: dict[int, int | None] | None = None
_last_enum_probe_results: dict[int, int | None] | None = None

def _safe_get_bool_pref(pref_id: int) -> bool | None:
    try:
        return UIManager.GetBoolPreference(pref_id)
    except Exception:
        return None  # invalid/unknown IDs
    
def _safe_get_int_pref(pref_id: int) -> int | None:
    try:
        return UIManager.GetIntPreference(pref_id)
    except Exception:
        return None  # invalid/unknown IDs

def _safe_get_enum_pref(pref_id: int) -> int | None:
    try:
        return UIManager.GetEnumPreference(pref_id)
    except Exception:
        return None  # invalid/unknown IDs

def probe_bool_preferences(start: int = 0, end: int = 300, compare: bool = False) -> dict[int, bool | None]:
    """
    Probes boolean preferences in [start, end]. If compare=True, prints diffs vs last stored probe.
    Always stores the current probe as the new 'last' at the end.
    """
    global _last_probe_results

    current: dict[int, bool | None] = {i: _safe_get_bool_pref(i) for i in range(start, end + 1)}

    if compare and _last_probe_results is not None:
        print("=== Preference changes since last probe ===")
        any_change = False
        for i in range(start, end + 1):
            prev = _last_probe_results.get(i)
            now = current.get(i)
            if prev != now:
                any_change = True
                print(f"ID {i}: {prev} -> {now}")
        if not any_change:
            print("No changes detected in the specified range.")
    elif compare and _last_probe_results is None:
        print("No previous probe stored; nothing to compare against. Storing this run as the reference.")

    # Store current as the new reference
    _last_probe_results = current
    return current
    
def probe_int_preferences(start: int = 0, end: int = 300, compare: bool = False) -> dict[int, int | None]:
    """
    Probes integer preferences in [start, end]. If compare=True, prints diffs vs last stored probe.
    Always stores the current probe as the new 'last' at the end.
    """
    global _last_int_probe_results

    current: dict[int, int | None] = {i: _safe_get_int_pref(i) for i in range(start, end + 1)}

    if compare and _last_int_probe_results is not None:
        print("=== Preference changes since last probe ===")
        any_change = False
        for i in range(start, end + 1):
            prev = _last_int_probe_results.get(i)
            now = current.get(i)
            if prev != now:
                any_change = True
                print(f"ID {i}: {prev} -> {now}")
        if not any_change:
            print("No changes detected in the specified range.")
    elif compare and _last_int_probe_results is None:
        print("No previous probe stored; nothing to compare against. Storing this run as the reference.")

    # Store current as the new reference
    _last_int_probe_results = current
    return current    

def probe_enum_preferences(start: int = 0, end: int = 300, compare: bool = False) -> dict[int, int | None]:
    """
    Probes enum preferences in [start, end]. If compare=True, prints diffs vs last stored probe.
    Always stores the current probe as the new 'last' at the end.
    """
    global _last_enum_probe_results

    current: dict[int, int | None] = {i: _safe_get_enum_pref(i) for i in range(start, end + 1)}

    if compare and _last_enum_probe_results is not None:
        print("=== Preference changes since last probe ===")
        any_change = False
        for i in range(start, end + 1):
            prev = _last_enum_probe_results.get(i)
            now = current.get(i)
            if prev != now:
                any_change = True
                print(f"ID {i}: {prev} -> {now}")
        if not any_change:
            print("No changes detected in the specified range.")
    elif compare and _last_enum_probe_results is None:
        print("No previous probe stored; nothing to compare against. Storing this run as the reference.")

    # Store current as the new reference
    _last_enum_probe_results = current
    return current
    
    
key_mappings: list[int] = []
snapshot: list[int] = []


# 2) helper to prefer alias (non-VK_ name) if available
def get_key_display_name(vk_code: int) -> str:
    try:
        member = Key(vk_code)
    except ValueError:
        return f"Unknown(0x{vk_code:02X})"

    # gather all names (canonical + aliases) that point to this member
    names = [n for n, m in Key.__members__.items() if m is member]
    # prefer a friendly alias (non-VK_) if present
    for n in names:
        if not n.startswith("VK_"):
            return n
    return member.name  # fallback to VK_* canonical

index_to_test = 0

# Global dict to track which debug windows are open
if "debug_windows" not in globals():
    globals()["debug_windows"] = {}

def toggle_debug_window(win_id):
    """Toggle visibility of a debug window for a given WindowID."""
    globals()["debug_windows"][win_id] = not globals()["debug_windows"].get(win_id, False)

def draw_debug_window(win_id):
    """Draw the debug window if its flag is set."""
    if not globals()["debug_windows"].get(win_id, False):
        return  # nothing to draw

    title = f"Window Debug: {win_id.name}"
    if PyImGui.begin(title, True):  # `True` makes it closable
        coords = UIManager.GetWindoPosition(win_id.value)
        visible = UIManager.IsWindowVisible(win_id.value)

        if coords:
            x1, y1, x2, y2 = coords
            PyImGui.text(f"Coords: {coords}")
            PyImGui.text(f"Visible: {visible}")

            # Editable coords
            x1 = PyImGui.input_int("Left", x1)
            y1 = PyImGui.input_int("Top", y1)
            x2 = PyImGui.input_int("Right", x2)
            y2 = PyImGui.input_int("Bottom", y2)

            if PyImGui.button("Set Position"):
                UIManager.SetWindowPosition(win_id.value, [x1, y1, x2, y2])

            if PyImGui.button("Get Position"):
                coords = UIManager.GetWindoPosition(win_id.value)
                print(f"[DEBUG] {win_id.name} → {coords}")

            # Visibility toggle
            new_vis = PyImGui.checkbox("Visible", visible)
            if new_vis != visible:
                UIManager.SetWindowVisible(win_id.value, new_vis)

            # Overlay checkbox
            key = f"draw_{win_id.value}"
            if key not in globals():
                globals()[key] = False
            globals()[key] = PyImGui.checkbox("Draw Overlay", globals()[key])

            if globals()[key]:
                # Fall back: manual draw using window position
                left, top, right, bottom = coords
                p1 = PyOverlay.Point2D(left, top)
                p2 = PyOverlay.Point2D(right, top)
                p3 = PyOverlay.Point2D(right, bottom)
                p4 = PyOverlay.Point2D(left, bottom)
                _overlay = PyOverlay.Overlay()
                _overlay.BeginDraw()
                _overlay.DrawQuad(p1, p2, p3, p4, Color(0,255,0,255).to_color(), thickness=3)
                _overlay.EndDraw()

        else:
            PyImGui.text("No coords available")

    else:
        # If closed via [X], unset flag
        globals()["debug_windows"][win_id] = False
    PyImGui.end()


def Draw_Window():
    global test_value, key_mappings, snapshot, index_to_test
    GwPreferences.Load()
    if PyImGui.begin(MODULE_NAME, PyImGui.WindowFlags.AlwaysAutoResize):
        if PyImGui.begin_tab_bar("##tabs"):
            if PyImGui.begin_tab_item("General"):
                PyImGui.text(f"Text Language: {GwPreferences.GetWithEnum('TextLanguage')[1]}")
                if PyImGui.button("set Italian"):
                    GwPreferences.Set("TextLanguage", ServerLanguage.Italian.value)
                PyImGui.text(f"Audio Language: {GwPreferences.GetWithEnum('AudioLanguage')[1]}")
                PyImGui.text(f"Chat Filter Level: {GwPreferences.GetWithEnum('ChatFilterLevel')[1]} (not working)")
                PyImGui.text(f"In-Game Clock: {GwPreferences.GetWithEnum('InGameClock')[1]}")
                PyImGui.text(f"Damage Text Size: {GwPreferences.GetWithEnum('DamageTextSize')[1]}")
                PyImGui.text(f"Field of View: {GwPreferences.GetWithEnum('FieldOfView')[1]}")
                PyImGui.text(f"Camera Rotation Speed: {GwPreferences.GetWithEnum('CameraRotationSpeed')[1]}")
                PyImGui.text(f"Lock Compass Rotation:"); PyImGui.same_line(0,-1)
                PyImGui.text_colored(f"{GwPreferences.GetWithEnum('LockCompassRotation')[1]}", Utils.TrueFalseColor(GwPreferences.Get('LockCompassRotation')))
                PyImGui.text(f"Disable Mouse Walking:"); PyImGui.same_line(0,-1)
                PyImGui.text_colored(f"{GwPreferences.GetWithEnum('DisableMouseWalking')[1]}", Utils.TrueFalseColor(GwPreferences.Get('DisableMouseWalking')))
                if PyImGui.button("Toggle Disable Mouse Walking"):
                    current = GwPreferences.Get('DisableMouseWalking')
                    GwPreferences.Set('DisableMouseWalking', not current)
                PyImGui.text(f"Invert Mouse Control of Camera:"); PyImGui.same_line(0,-1)
                PyImGui.text_colored(f"{GwPreferences.GetWithEnum('InvertMouseControlOfCamera')[1]}", Utils.TrueFalseColor(GwPreferences.Get('InvertMouseControlOfCamera')))
                PyImGui.text(f"Double Tap Forward to Run Backwards to Flip:"); PyImGui.same_line(0,-1)
                PyImGui.text_colored(f"{GwPreferences.GetWithEnum('DoubleTapForwardToRunBackwardsToFlip')[1]}", Utils.TrueFalseColor(GwPreferences.Get('DoubleTapForwardToRunBackwardsToFlip')))
                PyImGui.text(f"Double Click to Interact:"); PyImGui.same_line(0,-1)
                PyImGui.text_colored(f"{GwPreferences.GetWithEnum('DoubleClickToInteract')[1]}", Utils.TrueFalseColor(GwPreferences.Get('DoubleClickToInteract')))
                PyImGui.text(f"Always Show Nearby Names in PvP:"); PyImGui.same_line(0,-1)
                PyImGui.text_colored(f"{GwPreferences.GetWithEnum('AlwaysShowNearbyNamesPvP')[1]}", Utils.TrueFalseColor(GwPreferences.Get('AlwaysShowNearbyNamesPvP')))
                PyImGui.text(f"Do Not Close Windows on Escape:"); PyImGui.same_line(0,-1)
                PyImGui.text_colored(f"{GwPreferences.GetWithEnum('DoNotCloseWindowsOnEscape')[1]}", Utils.TrueFalseColor(GwPreferences.Get('DoNotCloseWindowsOnEscape')))
                PyImGui.text(f"Do Not Show Skill Tips on Skill Bars:"); PyImGui.same_line(0,-1)
                PyImGui.text_colored(f"{GwPreferences.GetWithEnum('DoNotShowSkillTipsOnSkillBars')[1]}", Utils.TrueFalseColor(GwPreferences.Get('DoNotShowSkillTipsOnSkillBars')))
                PyImGui.text(f"Do Not Show Skill Tips on Effect Monitor:"); PyImGui.same_line(0,-1)
                PyImGui.text_colored(f"{GwPreferences.GetWithEnum('DoNotShowSkillTipsOnEffectMonitor')[1]}", Utils.TrueFalseColor(GwPreferences.Get('DoNotShowSkillTipsOnEffectMonitor')))
                PyImGui.text(f"Show Text in Skill Floaters:"); PyImGui.same_line(0,-1)
                PyImGui.text_colored(f"{GwPreferences.GetWithEnum('ShowTextInSkillFloaters')[1]}", Utils.TrueFalseColor(GwPreferences.Get('ShowTextInSkillFloaters')))
                PyImGui.text(f"Auto Target Foes:"); PyImGui.same_line(0,-1)
                PyImGui.text_colored(f"{GwPreferences.GetWithEnum('AutoTargetFoes')[1]}", Utils.TrueFalseColor(GwPreferences.Get('AutoTargetFoes')))
                PyImGui.text(f"Auto Target NPCs:"); PyImGui.same_line(0,-1)
                PyImGui.text_colored(f"{GwPreferences.GetWithEnum('AutoTargetNPCs')[1]}", Utils.TrueFalseColor(GwPreferences.Get('AutoTargetNPCs')))
                PyImGui.text(f"Fade Distant Name Tags:"); PyImGui.same_line(0,-1)
                PyImGui.text_colored(f"{GwPreferences.GetWithEnum('FadeDistantNameTags')[1]}", Utils.TrueFalseColor(GwPreferences.Get('FadeDistantNameTags')))
                PyImGui.text(f"Concise Skill Descriptions:"); PyImGui.same_line(0,-1)
                PyImGui.text_colored(f"{GwPreferences.GetWithEnum('ConciseSkillDescriptions')[1]}", Utils.TrueFalseColor(GwPreferences.Get('ConciseSkillDescriptions')))
                PyImGui.text(f"Whispers From Friends Etc Only:"); PyImGui.same_line(0,-1)
                PyImGui.text_colored(f"{GwPreferences.GetWithEnum('WhispersFromFriendsEtcOnly')[1]}", Utils.TrueFalseColor(GwPreferences.Get('WhispersFromFriendsEtcOnly')))
                PyImGui.text(f"Show Chat Timestamps:"); PyImGui.same_line(0,-1)
                PyImGui.text_colored(f"{GwPreferences.GetWithEnum('ShowChatTimestamps')[1]}", Utils.TrueFalseColor(GwPreferences.Get('ShowChatTimestamps')))
                PyImGui.text(f"Show Collapsed Bags:"); PyImGui.same_line(0,-1)
                PyImGui.text_colored(f"{GwPreferences.GetWithEnum('ShowCollapsedBags')[1]}", Utils.TrueFalseColor(GwPreferences.Get('ShowCollapsedBags')))
                PyImGui.text(f"Item Rarity Border:"); PyImGui.same_line(0,-1)
                PyImGui.text_colored(f"{GwPreferences.GetWithEnum('ItemRarityBorder')[1]}", Utils.TrueFalseColor(GwPreferences.Get('ItemRarityBorder')))
                PyImGui.text(f"Always Show Ally Names:"); PyImGui.same_line(0,-1)
                PyImGui.text_colored(f"{GwPreferences.GetWithEnum('AlwaysShowAllyNames')[1]}", Utils.TrueFalseColor(GwPreferences.Get('AlwaysShowAllyNames')))
                PyImGui.text(f"Always Show Foe Names:"); PyImGui.same_line(0,-1)
                PyImGui.text_colored(f"{GwPreferences.GetWithEnum('AlwaysShowFoeNames')[1]}", Utils.TrueFalseColor(GwPreferences.Get('AlwaysShowFoeNames')))

                PyImGui.end_tab_item()
            if PyImGui.begin_tab_item("Graphics"):
                PyImGui.text("Resolution:"); PyImGui.same_line(0,-1)
                PyImGui.text(f"{GwPreferences.GetWithEnum('WindowSizeX')[1]} x {GwPreferences.GetWithEnum('WindowSizeY')[1]}")
                PyImGui.same_line(0,-1)
                PyImGui.text(f"Refresh Rate: {GwPreferences.GetWithEnum('RefreshRate')[1]} Hz")
                PyImGui.text(f"Interface Size: {GwPreferences.GetWithEnum('InterfaceSize')[1]}")
                PyImGui.same_line(0,-1)
                PyImGui.text(f"Anti-Aliasing: {GwPreferences.GetWithEnum('AntiAliasing')[1]}")
                PyImGui.separator()
                PyImGui.text(f"Terrain Quality: {GwPreferences.GetWithEnum('TerrainQuality')[1]}")
                PyImGui.text(f"Reflections: {GwPreferences.GetWithEnum('Reflections')[1]}")
                PyImGui.text(f"Texture Quality: {GwPreferences.GetWithEnum('TextureQuality')[1]}")
                PyImGui.text(f"Shadow Quality: {GwPreferences.GetWithEnum('ShadowQuality')[1]}")
                PyImGui.text(f"Shader Quality: {GwPreferences.GetWithEnum('ShaderQuality')[1]}")
                PyImGui.text(f"Frame Limiter: {GwPreferences.GetWithEnum('FrameLimiter')[1]}")
                PyImGui.text(f"Fullscreen Gamma: {GwPreferences.GetWithEnum('FullscreenGamma')[1]} (weird number but ok)")
                PyImGui.text(f"Wait For V-Sync:"); PyImGui.same_line(0,-1)
                PyImGui.text_colored(f"{GwPreferences.GetWithEnum('WaitForVSync')[1]}", Utils.TrueFalseColor(GwPreferences.Get('WaitForVSync')))
                PyImGui.text(f"Enable Post-Processing: (not accessible)")
                PyImGui.text(f"Use Best Texture Filtering: {GwPreferences.GetWithEnum('UseBestTextureFiltering')[1]}")
                PyImGui.text(f"Enhanced Draw Distance:"); PyImGui.same_line(0,-1)
                PyImGui.text_colored(f"{GwPreferences.GetWithEnum('EnhancedDrawDistance')[1]}", Utils.TrueFalseColor(GwPreferences.Get('EnhancedDrawDistance')))
                PyImGui.text(f"Use High Resolution Textures in Outposts:"); PyImGui.same_line(0,-1)
                PyImGui.text_colored(f"{GwPreferences.GetWithEnum('UseHighResolutionTexturesInOutposts')[1]}", Utils.TrueFalseColor(GwPreferences.Get('UseHighResolutionTexturesInOutposts')))

                PyImGui.end_tab_item()
            if PyImGui.begin_tab_item("Sound"):
                PyImGui.text(f"Master Volume: {GwPreferences.GetWithEnum('MasterVolume')[1]}")
                PyImGui.text(f"Music Volume: {GwPreferences.GetWithEnum('MusicVolume')[1]}")
                PyImGui.text(f"Background Volume: {GwPreferences.GetWithEnum('BackgroundVolume')[1]}")
                PyImGui.text(f"Effects Volume: {GwPreferences.GetWithEnum('EffectsVolume')[1]}")
                PyImGui.text(f"Dialog Volume: {GwPreferences.GetWithEnum('DialogVolume')[1]}")
                PyImGui.text(f"UI Volume: {GwPreferences.GetWithEnum('UIVolume')[1]}")
                PyImGui.text(f"Mute When Guild Wars Is In Background:"); PyImGui.same_line(0,-1)
                PyImGui.text_colored(f"{GwPreferences.GetWithEnum('MuteWhenGuildWarsIsInBackground')[1]}", Utils.TrueFalseColor(GwPreferences.Get('MuteWhenGuildWarsIsInBackground')))
                PyImGui.text(f"Sound Quality: {GwPreferences.GetWithEnum('SoundQuality')[1]}")
                PyImGui.text(f"Use 3D Audio Hardware: (unable to test)")
                PyImGui.text(f"Use EAX: (unable to test)")
                PyImGui.text(f"Optimize For Stereo:"); PyImGui.same_line(0,-1)
                PyImGui.text_colored(f"{GwPreferences.GetWithEnum('OptimizeForStereo')[1]}", Utils.TrueFalseColor(GwPreferences.Get('OptimizeForStereo')))
                
                PyImGui.separator()
                test_value = PyImGui.input_int("Test Int Input", test_value)
                if test_value is not None:
                    value = UIManager.GetBoolPreference(test_value)
                    PyImGui.text(f"Value of enum {test_value}: {value}")
                    
                if PyImGui.button("Probe Bool (store)"):
                    probe_bool_preferences()  # just record

                if PyImGui.button("Probe Bool + Compare"):
                    probe_bool_preferences(compare=True)  # compare vs last
                    
                PyImGui.separator()
                if PyImGui.button("Probe Int (store)"):
                    probe_int_preferences()  # just record

                if PyImGui.button("Probe Int + Compare"):
                    probe_int_preferences(compare=True)  # compare vs last
                    
                PyImGui.separator()
                
                if PyImGui.button("Probe Enum (store)"):
                    probe_enum_preferences()  # just record

                if PyImGui.button("Probe Enum + Compare"):
                    probe_enum_preferences(compare=True)  # compare vs last
                    
                
                    
                    
                PyImGui.end_tab_item()
            if PyImGui.begin_tab_item("Control"):
                if PyImGui.button("Take Snapshot"):
                    snapshot = UIManager.GetKeyMappings()
                    print("Snapshot taken.")

                # Compare snapshot with current
                if PyImGui.button("Compare Snapshot"):
                    current = UIManager.GetKeyMappings()
                    for i, (snap_val, curr_val) in enumerate(zip(snapshot, current)):
                        if snap_val != curr_val:
                            # get friendly key name
                            if i in Key._value2member_map_:
                                key_enum = Key(i)
                                aliases = [name for name, member in Key.__members__.items() if member is key_enum]
                                key_name = next((a for a in aliases if not a.startswith("VK_")), key_enum.name)
                            else:
                                key_name = f"Unknown({i})"

                            print(f"{i}: {key_name} changed {snap_val} -> {curr_val}")


                key_mappings = UIManager.GetKeyMappings()
                
                index_to_test = PyImGui.input_int("Index to Test", index_to_test)
                if index_to_test is not None:
                    if PyImGui.button("Set Mapping for Index"):
                            key_mappings2 = key_mappings.copy()
                            key_mappings2[index_to_test] = 128
                            UIManager.SetKeyMappings(key_mappings2)

                if key_mappings:
                    for idx, mapping in enumerate(key_mappings):
                        vk_code = INDEX_TO_VK.get(idx, 0)  # translate scan-code index -> VK
                        if vk_code == 0:  # means no override
                            vk_code = idx
                        key_name = get_key_display_name(vk_code)

                        if idx == mapping:
                            mapping_name = "Unmapped"
                        else:
                            mapping_name = CONTROL_MAP.get(mapping, f"{mapping}")

                        # --- color priority ---
                        if idx == mapping:
                            color = ColorPalette.GetColor("Gray").to_tuple_normalized()
                        elif idx in INDEX_TO_VK and INDEX_TO_VK[idx] != 0:
                            color = ColorPalette.GetColor("Yellow").to_tuple_normalized()
                        elif mapping in CONTROL_MAP:
                            color = ColorPalette.GetColor("Cyan").to_tuple_normalized()
                        else:
                            color = ColorPalette.GetColor("White").to_tuple_normalized()

                        PyImGui.text_colored(f"{idx}: {key_name} -> {mapping_name}", color)

                PyImGui.end_tab_item()
            if PyImGui.begin_tab_item("Interface"):
                for win_id in WindowID:
                    if win_id == WindowID.WindowID_Count:
                        continue
                    if PyImGui.button(f"{win_id.name}##btn{win_id.value}"):
                        toggle_debug_window(win_id)
                PyImGui.end_tab_item()

            # Draw all active debug windows
            for win_id in list(globals()["debug_windows"].keys()):
                draw_debug_window(win_id)
    
            PyImGui.end_tab_bar()
    PyImGui.end()

def tooltip():
    PyImGui.begin_tooltip()

    # Title
    title_color = Color(255, 200, 100, 255)
    ImGui.push_font("Regular", 20)
    PyImGui.text_colored("Gw Config Manager", title_color.to_tuple_normalized())
    ImGui.pop_font()
    PyImGui.spacing()
    PyImGui.separator()

    # Description
    PyImGui.text("A powerful low-level utility for inspecting and debugging")
    PyImGui.text("the internal game engine configuration, key mappings,")
    PyImGui.text("and UI window states.")
    PyImGui.spacing()

    # Features
    PyImGui.text_colored("Features:", title_color.to_tuple_normalized())
    PyImGui.bullet_text("Input Mapping: Visualizes scan code to VK code translations for keybinds")
    PyImGui.bullet_text("Control Map Audit: Identifies cyan-colored overrides in the game's control system")
    PyImGui.bullet_text("Interface Debugger: Direct access to toggle and inspect internal game windows")
    PyImGui.bullet_text("Window ID Tracking: Monitors visibility and state of every engine-level window")
    PyImGui.bullet_text("Color-Coded Status: Differentiates between standard, identity, and custom mappings")

    PyImGui.spacing()
    PyImGui.separator()
    PyImGui.spacing()

    # Credits
    PyImGui.text_colored("Credits:", title_color.to_tuple_normalized())
    PyImGui.bullet_text("Developed by Apo")

    PyImGui.end_tooltip()
    
def main():
    Draw_Window()


if __name__ == "__main__":
    main()
