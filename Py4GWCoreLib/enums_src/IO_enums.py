from enum import Enum, IntFlag
from enum import IntEnum

# region mouse
class MouseButton(IntEnum):
    Left = 0
    Right = 1
    Middle = 2

# region ModifierKey
class ModifierKey(IntFlag):
    NoneKey = 0
    Shift = 1 << 0
    Ctrl = 1 << 1
    Alt = 1 << 2
    
# region Key
class Key(Enum):
    VK_0x00 = 0x00  # Undefined
    VK_LBUTTON = 0x01; LeftMouseButton = VK_LBUTTON
    VK_RBUTTON = 0x02; RightMouseButton = VK_RBUTTON
    VK_CANCEL = 0x03; Cancel = VK_CANCEL
    VK_MBUTTON = 0x04; MiddleMouseButton = VK_MBUTTON
    VK_XBUTTON1 = 0x05; XButton1 = VK_XBUTTON1
    VK_XBUTTON2 = 0x06; XButton2 = VK_XBUTTON2

    VK_BACK = 0x08; Backspace = VK_BACK
    VK_TAB = 0x09; Tab = VK_TAB

    VK_CLEAR = 0x0C; Clear = VK_CLEAR
    VK_RETURN = 0x0D; Enter = VK_RETURN

    VK_SHIFT = 0x10; Shift = VK_SHIFT
    VK_CONTROL = 0x11; Ctrl = VK_CONTROL
    VK_MENU = 0x12; Alt = VK_MENU
    VK_PAUSE = 0x13; Pause = VK_PAUSE
    VK_CAPITAL = 0x14; CapsLock = VK_CAPITAL
    VK_KANA = 0x15; Kana = VK_KANA
    VK_IME_ON = 0x16; IMEOn = VK_IME_ON
    VK_JUNJA = 0x17; Junja = VK_JUNJA
    VK_FINAL = 0x18; Final = VK_FINAL
    VK_HANJA = 0x19; Hanja = VK_HANJA
    VK_IME_OFF = 0x1A; IMEOff = VK_IME_OFF
    VK_ESCAPE = 0x1B; Escape = VK_ESCAPE
    VK_CONVERT = 0x1C; Convert = VK_CONVERT
    VK_NONCONVERT = 0x1D; NonConvert = VK_NONCONVERT
    VK_ACCEPT = 0x1E; Accept = VK_ACCEPT
    VK_MODECHANGE = 0x1F; ModeChange = VK_MODECHANGE

    VK_SPACE = 0x20; Space = VK_SPACE
    VK_PRIOR = 0x21; PageUp = VK_PRIOR
    VK_NEXT = 0x22; PageDown = VK_NEXT
    VK_END = 0x23; End = VK_END
    VK_HOME = 0x24; Home = VK_HOME
    VK_LEFT = 0x25; LeftArrow = VK_LEFT
    VK_UP = 0x26; UpArrow = VK_UP
    VK_RIGHT = 0x27; RightArrow = VK_RIGHT
    VK_DOWN = 0x28; DownArrow = VK_DOWN
    VK_SELECT = 0x29; Select = VK_SELECT
    VK_PRINT = 0x2A; Print = VK_PRINT
    VK_EXECUTE = 0x2B; Execute = VK_EXECUTE
    VK_SNAPSHOT = 0x2C; PrintScreen = VK_SNAPSHOT
    VK_INSERT = 0x2D; Insert = VK_INSERT
    VK_DELETE = 0x2E; Delete = VK_DELETE
    VK_HELP = 0x2F; Help = VK_HELP

    VK_0 = 0x30; Zero = VK_0
    VK_1 = 0x31; One = VK_1
    VK_2 = 0x32; Two = VK_2
    VK_3 = 0x33; Three = VK_3
    VK_4 = 0x34; Four = VK_4
    VK_5 = 0x35; Five = VK_5
    VK_6 = 0x36; Six = VK_6
    VK_7 = 0x37; Seven = VK_7
    VK_8 = 0x38; Eight = VK_8
    VK_9 = 0x39; Nine = VK_9

    VK_A = 0x41; A = VK_A
    VK_B = 0x42; B = VK_B
    VK_C = 0x43; C = VK_C
    VK_D = 0x44; D = VK_D
    VK_E = 0x45; E = VK_E
    VK_F = 0x46; F = VK_F
    VK_G = 0x47; G = VK_G
    VK_H = 0x48; H = VK_H
    VK_I = 0x49; I = VK_I
    VK_J = 0x4A; J = VK_J
    VK_K = 0x4B; K = VK_K
    VK_L = 0x4C; L = VK_L
    VK_M = 0x4D; M = VK_M
    VK_N = 0x4E; N = VK_N
    VK_O = 0x4F; O = VK_O
    VK_P = 0x50; P = VK_P
    VK_Q = 0x51; Q = VK_Q
    VK_R = 0x52; R = VK_R
    VK_S = 0x53; S = VK_S
    VK_T = 0x54; T = VK_T
    VK_U = 0x55; U = VK_U
    VK_V = 0x56; V = VK_V
    VK_W = 0x57; W = VK_W
    VK_X = 0x58; X = VK_X
    VK_Y = 0x59; Y = VK_Y
    VK_Z = 0x5A; Z = VK_Z

    VK_LWIN = 0x5B; LWin = VK_LWIN
    VK_RWIN = 0x5C; RWin = VK_RWIN
    VK_APPS = 0x5D; Apps = VK_APPS
    VK_0x5E = 0x5E  # Reserved
    VK_SLEEP = 0x5F; Sleep = VK_SLEEP

    VK_NUMPAD0 = 0x60; Numpad0 = VK_NUMPAD0
    VK_NUMPAD1 = 0x61; Numpad1 = VK_NUMPAD1
    VK_NUMPAD2 = 0x62; Numpad2 = VK_NUMPAD2
    VK_NUMPAD3 = 0x63; Numpad3 = VK_NUMPAD3
    VK_NUMPAD4 = 0x64; Numpad4 = VK_NUMPAD4
    VK_NUMPAD5 = 0x65; Numpad5 = VK_NUMPAD5
    VK_NUMPAD6 = 0x66; Numpad6 = VK_NUMPAD6
    VK_NUMPAD7 = 0x67; Numpad7 = VK_NUMPAD7
    VK_NUMPAD8 = 0x68; Numpad8 = VK_NUMPAD8
    VK_NUMPAD9 = 0x69; Numpad9 = VK_NUMPAD9
    VK_MULTIPLY = 0x6A; NumpadMultiply = VK_MULTIPLY
    VK_ADD = 0x6B; NumpadAdd = VK_ADD
    VK_SEPARATOR = 0x6C; NumpadSeparator = VK_SEPARATOR
    VK_SUBTRACT = 0x6D; NumpadSubtract = VK_SUBTRACT
    VK_DECIMAL = 0x6E; NumpadDecimal = VK_DECIMAL
    VK_DIVIDE = 0x6F; NumpadDivide = VK_DIVIDE

    VK_F1 = 0x70; F1 = VK_F1
    VK_F2 = 0x71; F2 = VK_F2
    VK_F3 = 0x72; F3 = VK_F3
    VK_F4 = 0x73; F4 = VK_F4
    VK_F5 = 0x74; F5 = VK_F5
    VK_F6 = 0x75; F6 = VK_F6
    VK_F7 = 0x76; F7 = VK_F7
    VK_F8 = 0x77; F8 = VK_F8
    VK_F9 = 0x78; F9 = VK_F9
    VK_F10 = 0x79; F10 = VK_F10
    VK_F11 = 0x7A; F11 = VK_F11
    VK_F12 = 0x7B; F12 = VK_F12
    VK_F13 = 0x7C; F13 = VK_F13
    VK_F14 = 0x7D; F14 = VK_F14
    VK_F15 = 0x7E; F15 = VK_F15
    VK_F16 = 0x7F; F16 = VK_F16
    VK_F17 = 0x80; F17 = VK_F17
    VK_F18 = 0x81; F18 = VK_F18
    VK_F19 = 0x82; F19 = VK_F19
    VK_F20 = 0x83; F20 = VK_F20
    VK_F21 = 0x84; F21 = VK_F21
    VK_F22 = 0x85; F22 = VK_F22
    VK_F23 = 0x86; F23 = VK_F23
    VK_F24 = 0x87; F24 = VK_F24

    VK_NUMLOCK = 0x90; NumLock = VK_NUMLOCK
    VK_SCROLL = 0x91; ScrollLock = VK_SCROLL

    VK_LSHIFT = 0xA0; LShift = VK_LSHIFT
    VK_RSHIFT = 0xA1; RShift = VK_RSHIFT
    VK_LCONTROL = 0xA2; LCtrl = VK_LCONTROL
    VK_RCONTROL = 0xA3; RCtrl = VK_RCONTROL
    VK_LMENU = 0xA4; LAlt = VK_LMENU
    VK_RMENU = 0xA5; RAlt = VK_RMENU

    VK_BROWSER_BACK = 0xA6; BrowserBack = VK_BROWSER_BACK
    VK_BROWSER_FORWARD = 0xA7; BrowserForward = VK_BROWSER_FORWARD
    VK_BROWSER_REFRESH = 0xA8; BrowserRefresh = VK_BROWSER_REFRESH
    VK_BROWSER_STOP = 0xA9; BrowserStop = VK_BROWSER_STOP
    VK_BROWSER_SEARCH = 0xAA; BrowserSearch = VK_BROWSER_SEARCH
    VK_BROWSER_FAVORITES = 0xAB; BrowserFavorites = VK_BROWSER_FAVORITES
    VK_BROWSER_HOME = 0xAC; BrowserHome = VK_BROWSER_HOME

    VK_VOLUME_MUTE = 0xAD; VolumeMute = VK_VOLUME_MUTE
    VK_VOLUME_DOWN = 0xAE; VolumeDown = VK_VOLUME_DOWN
    VK_VOLUME_UP = 0xAF; VolumeUp = VK_VOLUME_UP
    VK_MEDIA_NEXT_TRACK = 0xB0; MediaNextTrack = VK_MEDIA_NEXT_TRACK
    VK_MEDIA_PREV_TRACK = 0xB1; MediaPrevTrack = VK_MEDIA_PREV_TRACK
    VK_MEDIA_STOP = 0xB2; MediaStop = VK_MEDIA_STOP
    VK_MEDIA_PLAY_PAUSE = 0xB3; MediaPlayPause = VK_MEDIA_PLAY_PAUSE
    VK_LAUNCH_MAIL = 0xB4; LaunchMail = VK_LAUNCH_MAIL
    VK_LAUNCH_MEDIA_SELECT = 0xB5; LaunchMediaSelect = VK_LAUNCH_MEDIA_SELECT
    VK_LAUNCH_APP1 = 0xB6; LaunchApp1 = VK_LAUNCH_APP1
    VK_LAUNCH_APP2 = 0xB7; LaunchApp2 = VK_LAUNCH_APP2

    VK_OEM_1= 0xBA; Semicolon = 0xBA
    VK_OEM_2 = 0xBF; Slash = VK_OEM_2
    VK_OEM_3= 0xC0; Grave = VK_OEM_3
    VK_OEM_4= 0xDB; LeftBrace = VK_OEM_4
    VK_OEM_5= 0xDC; Backslash = VK_OEM_5
    VK_OEM_6= 0xDD; RightBrace = VK_OEM_6
    VK_OEM_7= 0xDE; Apostrophe = VK_OEM_7
    VK_OEM_PLUS= 0xBB; Equal = 0xBB
    VK_OEM_MINUS= 0xBD; Minus = 0xBD
    VK_OEM_PERIOD= 0xBE; Period = 0xBE
    VK_OEM_COMMA= 0xBC; Comma = 0xBC
    
    

    VK_GAMEPAD_A = 0xC3; GamepadA = VK_GAMEPAD_A
    VK_GAMEPAD_B = 0xC4; GamepadB = VK_GAMEPAD_B
    VK_GAMEPAD_X = 0xC5; GamepadX = VK_GAMEPAD_X
    VK_GAMEPAD_Y = 0xC6; GamepadY = VK_GAMEPAD_Y
    VK_GAMEPAD_RIGHT_SHOULDER = 0xC7; GamepadRB = VK_GAMEPAD_RIGHT_SHOULDER
    VK_GAMEPAD_LEFT_SHOULDER = 0xC8; GamepadLB = VK_GAMEPAD_LEFT_SHOULDER
    VK_GAMEPAD_LEFT_TRIGGER = 0xC9; GamepadLT = VK_GAMEPAD_LEFT_TRIGGER
    VK_GAMEPAD_RIGHT_TRIGGER = 0xCA; GamepadRT = VK_GAMEPAD_RIGHT_TRIGGER
    VK_GAMEPAD_DPAD_UP = 0xCB; GamepadDPadUp = VK_GAMEPAD_DPAD_UP
    VK_GAMEPAD_DPAD_DOWN = 0xCC; GamepadDPadDown = VK_GAMEPAD_DPAD_DOWN
    VK_GAMEPAD_DPAD_LEFT = 0xCD; GamepadDPadLeft = VK_GAMEPAD_DPAD_LEFT
    VK_GAMEPAD_DPAD_RIGHT = 0xCE; GamepadDPadRight = VK_GAMEPAD_DPAD_RIGHT
    VK_GAMEPAD_MENU = 0xCF; GamepadMenu = VK_GAMEPAD_MENU
    VK_GAMEPAD_VIEW = 0xD0; GamepadView = VK_GAMEPAD_VIEW
    VK_GAMEPAD_LEFT_THUMBSTICK_BUTTON = 0xD1; GamepadLThumb = VK_GAMEPAD_LEFT_THUMBSTICK_BUTTON
    VK_GAMEPAD_RIGHT_THUMBSTICK_BUTTON = 0xD2; GamepadRThumb = VK_GAMEPAD_RIGHT_THUMBSTICK_BUTTON
    VK_GAMEPAD_LEFT_THUMBSTICK_UP = 0xD3; GamepadLThumbUp = VK_GAMEPAD_LEFT_THUMBSTICK_UP
    VK_GAMEPAD_LEFT_THUMBSTICK_DOWN = 0xD4; GamepadLThumbDown = VK_GAMEPAD_LEFT_THUMBSTICK_DOWN
    VK_GAMEPAD_LEFT_THUMBSTICK_RIGHT = 0xD5; GamepadLThumbRight = VK_GAMEPAD_LEFT_THUMBSTICK_RIGHT
    VK_GAMEPAD_LEFT_THUMBSTICK_LEFT = 0xD6; GamepadLThumbLeft = VK_GAMEPAD_LEFT_THUMBSTICK_LEFT
    VK_GAMEPAD_RIGHT_THUMBSTICK_UP = 0xD7; GamepadRThumbUp = VK_GAMEPAD_RIGHT_THUMBSTICK_UP
    VK_GAMEPAD_RIGHT_THUMBSTICK_DOWN = 0xD8; GamepadRThumbDown = VK_GAMEPAD_RIGHT_THUMBSTICK_DOWN
    VK_GAMEPAD_RIGHT_THUMBSTICK_RIGHT = 0xD9; GamepadRThumbRight = VK_GAMEPAD_RIGHT_THUMBSTICK_RIGHT
    VK_GAMEPAD_RIGHT_THUMBSTICK_LEFT = 0xDA; GamepadRThumbLeft = VK_GAMEPAD_RIGHT_THUMBSTICK_LEFT
    
    Unmapped = 0xFFFF; Unused = Unmapped; Unmappable = Unmapped
    
# Maps a character to (Key, shift_required)
CHAR_MAP = {
    # lowercase letters
    **{chr(c): (getattr(Key, chr(c).upper()), False) for c in range(ord('a'), ord('z')+1)},
    # uppercase letters
    **{chr(c): (getattr(Key, chr(c)), True) for c in range(ord('A'), ord('Z')+1)},

    # digits
    "0": (Key.VK_0, False),
    "1": (Key.VK_1, False),
    "2": (Key.VK_2, False),
    "3": (Key.VK_3, False),
    "4": (Key.VK_4, False),
    "5": (Key.VK_5, False),
    "6": (Key.VK_6, False),
    "7": (Key.VK_7, False),
    "8": (Key.VK_8, False),
    "9": (Key.VK_9, False),

    # space & enter
    " ": (Key.Space, False),
    "\n": (Key.Enter, False),

    # simple punctuation
    ".": (Key.Period, False),
    ",": (Key.Comma, False),
    "-": (Key.Minus, False),
    "_": (Key.Minus, True),
    "=": (Key.Equal, False),
    "+": (Key.Equal, True),
    ";": (Key.Semicolon, False),
    ":": (Key.Semicolon, True),
    "'": (Key.Apostrophe, False),
    '"': (Key.Apostrophe, True),
    "/": (Key.Slash, False),
    "?": (Key.Slash, True),
    "\\": (Key.Backslash, False),
    "|": (Key.Backslash, True),
    "[": (Key.LeftBrace, False),
    "{": (Key.LeftBrace, True),
    "]": (Key.RightBrace, False),
    "}": (Key.RightBrace, True),
    "`": (Key.Grave, False),
    "~": (Key.Grave, True),
}
