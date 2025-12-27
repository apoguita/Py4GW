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
    @staticmethod
    def SkipCinematic() -> bool:
        """Skip the current map cinematic."""
        if not SkipCinematic_Func.is_valid():
            return False
        
        SkipCinematic_Func()
        return True

    @staticmethod
    def Travel(map_id: int, region: int =0, district_number: int =0, language: int =0) -> bool:
        return UIManager.SendUIMessage(
            UIMessage.kTravel,
            [map_id, region, language, district_number],
            False
        )

    @staticmethod
    def TravelGH(key: GHKey | None = None) -> bool:
        """Travel to a Guild Hall using the specified GHKey."""
        if key is None:
            guild_ctx = GuildContext.get_context()
            if guild_ctx is None:
                return False
            key = guild_ctx.player_gh_key
                    
        return UIManager.SendUIMessageRaw(
            UIMessage.kGuildHall,
            ctypes.addressof(key),
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
        
