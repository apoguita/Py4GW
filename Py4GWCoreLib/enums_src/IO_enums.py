from enum import Enum
from enum import IntEnum

# region mouse
class MouseButton(IntEnum):
    Left = 0
    Right = 1
    Middle = 2
    
    
# region Key
class Key(Enum):
    # Letters
    A = 0x41
    B = 0x42
    C = 0x43
    D = 0x44
    E = 0x45
    F = 0x46
    G = 0x47
    H = 0x48
    I = 0x49  # noqa
    J = 0x4A
    K = 0x4B
    L = 0x4C
    M = 0x4D
    N = 0x4E
    O = 0x4F  # noqa
    P = 0x50
    Q = 0x51
    R = 0x52
    S = 0x53
    T = 0x54
    U = 0x55
    V = 0x56
    W = 0x57
    X = 0x58
    Y = 0x59
    Z = 0x5A

    # Numbers (Top row, not numpad)
    Zero = 0x30
    One = 0x31
    Two = 0x32
    Three = 0x33
    Four = 0x34
    Five = 0x35
    Six = 0x36
    Seven = 0x37
    Eight = 0x38
    Nine = 0x39

    # Function keys
    F1 = 0x70
    F2 = 0x71
    F3 = 0x72
    F4 = 0x73
    F5 = 0x74
    F6 = 0x75
    F7 = 0x76
    F8 = 0x77
    F9 = 0x78
    F10 = 0x79
    F11 = 0x7A
    F12 = 0x7B

    # Control keys
    Shift = 0x10
    Ctrl = 0x11
    Alt = 0x12
    Enter = 0x0D
    Escape = 0x1B
    Space = 0x20
    Tab = 0x09
    Backspace = 0x08
    Delete = 0x2E
    Insert = 0x2D
    Home = 0x24
    End = 0x23
    PageUp = 0x21
    PageDown = 0x22

    # Arrow keys
    LeftArrow = 0x25
    UpArrow = 0x26
    RightArrow = 0x27
    DownArrow = 0x28

    # Numpad keys
    Numpad0 = 0x60
    Numpad1 = 0x61
    Numpad2 = 0x62
    Numpad3 = 0x63
    Numpad4 = 0x64
    Numpad5 = 0x65
    Numpad6 = 0x66
    Numpad7 = 0x67
    Numpad8 = 0x68
    Numpad9 = 0x69
    NumpadMultiply = 0x6A
    NumpadAdd = 0x6B
    NumpadSubtract = 0x6D
    NumpadDecimal = 0x6E
    NumpadDivide = 0x6F

    # Miscellaneous
    CapsLock = 0x14
    PrintScreen = 0x2C
    ScrollLock = 0x91
    Pause = 0x13

    # Special characters (US standard keyboard) (Danish standard keyboard) (English standard keyboard)
    Semicolon = 0xBA     # ;                   # æ                        # ;
    Equal = 0xBB         # =                   # ´                        # =
    Comma = 0xBC         # ,                   # ,                        # ,
    Minus = 0xBD         # -                   # +                        # -
    Period = 0xBE        # .                   # .                        # .
    Slash = 0xBF         # /                   # -                        # /
    Backtick = 0xC0      # `                   # ½                        # `
    LeftBracket = 0xDB   # [                   # å                        # [
    Backslash = 0xDC     # \                   # '                        # #
    RightBracket = 0xDD  # ]                   # ¨                        # ]
    Apostrophe = 0xDE    # '                   # ø                        # '

