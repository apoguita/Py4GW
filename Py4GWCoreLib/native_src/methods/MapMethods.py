from ...Scanner import ScannerSection
from ..internals.prototypes import Prototypes
from ..internals.native_function import NativeFunction
from ...UIManager import UIManager
from ...enums_src.UI_enums import UIMessage
from ..context.GuildContext import Guild, GuildContext, GHKey
import ctypes
from typing import List


SkipCinematic_Func = NativeFunction(
    name="SkipCinematic_Func", #GWCA name
    pattern=b"\x8b\x40\x30\x83\x78\x04\x00",
    mask="xxxxxxx",
    offset=-0x5,
    section=ScannerSection.TEXT,
    prototype=Prototypes["Void_NoArgs"],
    use_near_call=False,
)

class MapMethods:
    _GHKEY_SCRATCH = GHKey()
    @staticmethod
    def SkipCinematic() -> bool:
        """Skip the current map cinematic."""
        if not SkipCinematic_Func.is_valid():
            return False
        
        SkipCinematic_Func()
        return True

    @staticmethod
    def Travel(map_id: int, region: int = 0, district_number: int = 0, language: int = 0) -> bool:
        class TravelStruct(ctypes.Structure):
            _fields_ = [
                ("map_id", ctypes.c_uint32),  # GW::Constants::MapID
                ("region", ctypes.c_int32),  # ServerRegion
                ("language", ctypes.c_int32),  # Language
                ("district_number", ctypes.c_int32),
            ]

        return UIManager.SendUIMessageRaw(
            UIMessage.kTravel,
            ctypes.addressof(TravelStruct(map_id=map_id, region=region, language=language, district_number=district_number)),
            False,
        )

    @staticmethod
    def TravelGH(key: GHKey | None = None) -> bool:
        """
        Travel to a Guild Hall.
        If a key is provided, its value is written into the existing
        player_gh_key before sending the UI message.
        """
        guild_ctx = GuildContext.get_context()
        if guild_ctx is None:
            return False

        gh_key = guild_ctx.player_gh_key
        if gh_key is None:
            return False

        # If a custom key was provided, stuff its value into the real GH key
        if key is not None:
            for i in range(4):
                gh_key.key_data[i] = key.key_data[i]

        # Always use the original, working pointer
        return UIManager.SendUIMessageRaw(
            UIMessage.kGuildHall,
            ctypes.addressof(gh_key),
            0,
            False
        )

    @staticmethod
    def LeaveGH() -> bool:
        """Leave the current Guild Hall."""
        return UIManager.SendUIMessage(
            UIMessage.kLeaveGuildHall,
            [0],
            False
        )
        
    @staticmethod
    def EnterChallenge() -> bool:
        """Enter the challenge mode from the Guild Hall."""
        return UIManager.SendUIMessage(
            UIMessage.kSendEnterMission,
            [0],
            False
        )
        
