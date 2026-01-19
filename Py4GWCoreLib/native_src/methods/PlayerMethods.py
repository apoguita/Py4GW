from ...Scanner import ScannerSection
from ..internals.prototypes import Prototypes
from ..internals.native_function import NativeFunction

from ...enums_src.UI_enums import UIMessage
from ...Scanner import Scanner
import ctypes
from typing import List
from Py4GW import Game

class WorldActionId:
    InteractEnemy = 0
    InteractPlayerOrOther = 1
    InteractNPC = 2
    InteractItem = 3
    InteractTrade = 4
    InteractGadget = 5
 
# ------------------------------
# MoveTo
# ------------------------------

MoveTo_Func = NativeFunction(
    name="MoveTo_Func", #GWCA name
    pattern=b"\x83\xc4\x0c\x85\xff\x74\x0b\x56\x6a\x03",
    mask="xxxxxxxxxx",
    offset=-0x5,
    section=ScannerSection.TEXT,
    prototype=Prototypes["Void_FloatPtr"],
    use_near_call=True,
)

# ------------------------------
# DepositFaction
# ------------------------------

DepositFaction_Func = NativeFunction(
    name="DepositFaction_Func",
    pattern=b"\x68\x88\x13\x00\x00\xff\x76\x0c\x6a\x00",
    mask="xxxxxxxxxx",
    offset=0xA,
    section=ScannerSection.TEXT,
    prototype=Prototypes["Void_U32_U32_U32"],
)

# ------------------------------
# SetActiveTitle
# ------------------------------
sat_assertion = Scanner.FindAssertion("AttribTitles.cpp","!*hdr.param",0,0,)
sat_function_start = Scanner.ToFunctionStart(sat_assertion) 
sat_find_in_range = Scanner.FindInRange(b"\xff\x76\x08\xe8","xxxx",3,
                                        sat_function_start,sat_function_start+ 0x3ff,)
SetActiveTitle_Func_ptr = Scanner.FunctionFromNearCall(sat_find_in_range)

SetActiveTitle_Func = NativeFunction.from_address(
    name="SetActiveTitle_Func",
    address=SetActiveTitle_Func_ptr,
    prototype=Prototypes["Void_U32"],
)

# ------------------------------
# RemoveActiveTitle
# ------------------------------
RemoveActiveTitle_Func_ptr = Scanner.FindInRange(b"\x55\x8b\xec\x51","xxxx",0,
                                        SetActiveTitle_Func_ptr + 0x10,SetActiveTitle_Func_ptr + 0xff)

RemoveActiveTitle_Func = NativeFunction.from_address(
    name="RemoveActiveTitle_Func",
    address=RemoveActiveTitle_Func_ptr,
    prototype=Prototypes["Void_NoArgs"],
)
    
            
class PlayerMethods:
    @staticmethod
    def ChangeTarget(agent_id: int) -> None:
        def _action():
            from ...Agent import Agent
            from ...UIManager import UIManager
            if (target := Agent.GetAgentByID(agent_id)) is None:
                return 
            UIManager.SendUIMessage(UIMessage.kSendChangeTarget,[target.agent_id])
        
        Game.enqueue(_action)
        
    @staticmethod
    def InteractAgent(agent_id: int, call_target: bool = False) -> None:
        def _action():
            from ...Agent import Agent
            from ...UIManager import UIManager
            
            if (agent := Agent.GetAgentByID(agent_id)) is None:
                return 

            # Default packet values
            action_id = WorldActionId.InteractEnemy

            if agent.is_item_type:
                action_id = WorldActionId.InteractItem

            elif agent.is_gadget_type:
                action_id = WorldActionId.InteractGadget

            else:
                if (living := agent.GetAsAgentLiving()) is None:
                    return
                
                """ 1: "ally",
                2: "neutral",
                3: "enemy",
                4: "spirit_pet",
                5: "minion",
                6: "npc_minipet","""

                if living.allegiance == 3:  # Enemy
                    action_id = WorldActionId.InteractEnemy
                elif living.allegiance == 6:  # Npc_Minipet
                    action_id = WorldActionId.InteractNPC
                else:
                    action_id = WorldActionId.InteractPlayerOrOther

            UIManager.SendUIMessage(
                UIMessage.kSendWorldAction,
                [action_id, agent_id, call_target]
            )

        Game.enqueue(_action)
        
    @staticmethod
    def Move(x: float, y: float, zPlane: int = 0) -> None:
        def _action():
            if not MoveTo_Func.is_valid():
                return

            args = (ctypes.c_float * 4)()
            args[0] = x
            args[1] = y
            args[2] = float(zPlane)
            args[3] = 0.0  # unknown, but required

            MoveTo_Func.directCall(args)
        
        Game.enqueue(_action)   
        
    @staticmethod
    def DepositFaction(allegiance: int) -> None:
        def _action():
            if not DepositFaction_Func.is_valid():
                return
            DepositFaction_Func.directCall(0, allegiance, 5000)
        
        Game.enqueue(_action)
        
    @staticmethod
    def SetActiveTitle(title_id: int) -> None:
        def _action():
            if not SetActiveTitle_Func.is_valid():
                return
            SetActiveTitle_Func.directCall(title_id)
        
        Game.enqueue(_action)
        
    @staticmethod
    def RemoveActiveTitle() -> None:
        def _action():
            if not RemoveActiveTitle_Func.is_valid():
                return
            RemoveActiveTitle_Func.directCall()
        
        Game.enqueue(_action)
        
    @staticmethod
    def SendChat(channel: int | str, message: str) -> bool:
        """
        1:1 parity with:
        bool Chat::SendChat(char channel, const char* msg)
        -> bool Chat::SendChat(char channel, const wchar_t* msg)
        -> SendChat_Func(buffer, 0)  (hook turns into UIMessage)
        """
        if not message:
            return False

        if isinstance(channel, str):
            if len(channel) != 1:
                return False
            ch = channel
        elif isinstance(channel, int):
            if not (0 <= channel <= 0xFF):
                return False
            ch = chr(channel)
        else:
            return False

        # Match GetChannel(channel) != CHANNEL_UNKNOW
        if ch not in ('!', '@', '#', '$', '%', '"','/'):
            return False

        # Mimic char* -> wchar_t* overload path
        try:
            msg_w = message.encode("utf-8").decode("mbcs", errors="replace")
        except Exception:
            return False

        if not msg_w or len(msg_w) >= 140:
            return False

        # Clamp to in-game limit
        msg_w = msg_w[:120]

        # ---------- ASYNC EXECUTION ----------

        def _do_action():
            Buffer140 = ctypes.c_wchar * 140
            buf = Buffer140()

            buf[0] = ch
            for i, c in enumerate(msg_w):
                buf[i + 1] = c
            buf[len(msg_w) + 1] = "\0"

            class SendChatPacket(ctypes.Structure):
                _fields_ = [
                    ("message", ctypes.c_wchar_p),
                    ("agent_id", ctypes.c_uint32),
                ]

            packet = SendChatPacket(
                message=ctypes.cast(buf, ctypes.c_wchar_p),
                agent_id=0,
            )

            from ...UIManager import UIManager
            UIManager.SendUIMessageRaw(
                UIMessage.kSendChatMessage,
                ctypes.addressof(packet),
                False,
            )

        Game.enqueue(_do_action)

        return True
    
    @staticmethod
    def SendWhisper(name: str, message: str) -> bool:
        """
        bool Chat::SendChat(const char* from, const char* msg)
        -> swprintf(L"\"%S,%S", from, msg)
        -> SendChat_Func(buffer, 0)
        """
        if not name or not message:
            return False

        # ---- Mimic char* -> wchar_t* via %S (ACP / mbcs) ----
        try:
            from_w = name.encode("utf-8").decode("mbcs", errors="replace")
            msg_w  = message.encode("utf-8").decode("mbcs", errors="replace")
        except Exception:
            return False

        if not from_w or not msg_w:
            return False

        # ---- swprintf(L"\"%S,%S", from, msg) ----
        formatted = f"\"{from_w},{msg_w}"

        if not (0 < len(formatted) < 140):
            return False

        # ---------- ASYNC EXECUTION ----------
        def _do_action():
            Buffer140 = ctypes.c_wchar * 140
            buf = Buffer140()

            for i, c in enumerate(formatted):
                buf[i] = c
            buf[len(formatted)] = "\0"

            class SendChatPacket(ctypes.Structure):
                _fields_ = [
                    ("message", ctypes.c_wchar_p),
                    ("agent_id", ctypes.c_uint32),
                ]

            packet = SendChatPacket(
                message=ctypes.cast(buf, ctypes.c_wchar_p),
                agent_id=0,
            )

            from ...UIManager import UIManager
            UIManager.SendUIMessageRaw(
                UIMessage.kSendChatMessage,
                ctypes.addressof(packet),
                False,
            )

        Game.enqueue(_do_action)
        return True

    @staticmethod
    def SendChatCommand(message: str) -> bool:
        """
        void PyPlayer::SendChatCommand(std::string msg)
        -> Chat::SendChat('/', msg.c_str())
        """
        return PlayerMethods.SendChat('/', message)

    @staticmethod
    def SendFakeChat(channel: int, message: str) -> None:
        """
        1:1 parity with:
        PyPlayer::SendFakeChat
        -> Chat::SendFakeChat
        -> WriteChat
        -> WriteChatEnc
        """

        # -----------------------------
        # C++: std::wstring(message.begin(), message.end())
        # widen each UTF-8 byte to wchar
        # -----------------------------
        msg_bytes = message.encode("utf-8")
        wmessage = "".join(chr(b) for b in msg_bytes)

        def _do_action():
            # -----------------------------
            # WriteChat
            # swprintf(L"\x108\x107%s\x1", message)
            # -----------------------------
            message_encoded = f"\u0108\u0107{wmessage}\u0001"

            sender_encoded = None  # SendFakeChat never supplies sender
            final_message = message_encoded

            # -----------------------------
            # WriteChatEnc
            # -----------------------------
            if sender_encoded is not None:
                has_link = "<a=1>" in message_encoded
                has_markup = has_link or "<c=" in message_encoded

                if has_markup:
                    if has_link:
                        fmt = (
                            "\u0108\u0107<a=2>\u0001\u0002%s\u0002"
                            "\u0108\u0107</a>\u0001\u0002"
                            "\u0108\u0107: \u0001\u0002%s"
                        )
                    else:
                        fmt = (
                            "\u0108\u0107<a=1>\u0001\u0002%s\u0002"
                            "\u0108\u0107</a>\u0001\u0002"
                            "\u0108\u0107: \u0001\u0002%s"
                        )
                else:
                    fmt = "\u076b\u010a%s\u0001\u010b%s\u0001"

                final_message = fmt % (sender_encoded, message_encoded)

            # -----------------------------
            # UIChatMessage
            # -----------------------------
            class UIChatMessage(ctypes.Structure):
                _fields_ = [
                    ("channel", ctypes.c_uint32),
                    ("message", ctypes.c_wchar_p),
                    ("channel2", ctypes.c_uint32),
                ]


            param = UIChatMessage(
                channel=channel,
                message=final_message,
                channel2=channel,
            )

            from ...UIManager import UIManager
            UIManager.SendUIMessageRaw(
                UIMessage.kWriteToChatLog,
                ctypes.addressof(param),
                False,
            )

        Game.enqueue(_do_action)

