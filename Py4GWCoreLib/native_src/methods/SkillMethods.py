from ...Scanner import ScannerSection
from ..internals.native_function import NativeFunction
from ..internals.prototypes import Prototypes


_ORDER_INTERACT_SET_HOTKEY_PATTERN = (
    b"\x55\x8b\xec\x83\xec\x08"
    b"\x8b\x45\x08\x89\x45\xfc"
    b"\x8d\x45\xf8\x50\x6a\x08"
    b"\xc7\x45\xf8\x3c\x00\x00\x00"
)


OrderInteractSetHotKey_Func = NativeFunction(
    name="OrderInteractSetHotKey_Func",
    pattern=_ORDER_INTERACT_SET_HOTKEY_PATTERN,
    mask="x" * len(_ORDER_INTERACT_SET_HOTKEY_PATTERN),
    offset=0,
    section=ScannerSection.TEXT,
    prototype=Prototypes["Void_U32"],
    use_near_call=False,
)


class SkillMethods:
    @staticmethod
    def IsOrderInteractSetHotKeyAvailable() -> bool:
        return bool(OrderInteractSetHotKey_Func.is_valid())

    @staticmethod
    def GetOrderInteractSetHotKeyAddress() -> int:
        if not SkillMethods.IsOrderInteractSetHotKeyAvailable():
            return 0
        return int(OrderInteractSetHotKey_Func.get_address() or 0)

    @staticmethod
    def OrderInteractSetHotKey(hotkey: int) -> bool:
        hotkey = int(hotkey)
        if hotkey < 0 or hotkey > 7:
            return False
        if not SkillMethods.IsOrderInteractSetHotKeyAvailable():
            return False

        OrderInteractSetHotKey_Func.directCall(hotkey)
        return True
