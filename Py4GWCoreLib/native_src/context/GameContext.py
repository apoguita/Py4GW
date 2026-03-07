
from Py4GW import Game
from ctypes import Structure, c_uint32, c_float, sizeof, cast, POINTER, c_void_p
from ..internals.types import Vec2f


class GameContextStruct(Structure):
    """Top-level game context (0x5C bytes). Field names from GWCA."""
    _pack_ = 1
    _fields_ = [
        ("h0000", c_void_p),               # +0x00
        ("h0004", c_void_p),               # +0x04
        ("agent_context", c_uint32),        # +0x08  AgentContext*
        ("h000C", c_uint32),                # +0x0C
        ("h0010", c_uint32),                # +0x10
        ("map_context", c_uint32),          # +0x14  MapContext*
        ("text_parser", c_uint32),          # +0x18  TextParser*
        ("h001C", c_uint32),                # +0x1C
        ("some_number", c_uint32),          # +0x20
        ("h0024", c_uint32),                # +0x24
        ("account_context", c_uint32),      # +0x28  AccountContext*
        ("world_context", c_uint32),        # +0x2C  WorldContext*
        ("cinematic", c_uint32),            # +0x30  Cinematic*
        ("h0034", c_uint32),                # +0x34
        ("gadget_context", c_uint32),       # +0x38  GadgetContext*
        ("guild_context", c_uint32),        # +0x3C  GuildContext*
        ("item_context", c_uint32),         # +0x40  ItemContext*
        ("char_context", c_uint32),         # +0x44  CharContext*
        ("h0048", c_uint32),                # +0x48
        ("party_context", c_uint32),        # +0x4C  PartyContext*
        ("h0050", c_uint32),                # +0x50
        ("h0054", c_uint32),                # +0x54
        ("trade_context", c_uint32),        # +0x58  TradeContext*
    ]
