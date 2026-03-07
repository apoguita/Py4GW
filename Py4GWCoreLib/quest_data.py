"""Backward-compatible quest data exports.

Use `Py4GWCoreLib.enums` or `Py4GWCoreLib.enums_src.Quest_enums` for new imports.
"""

from .enums_src.Quest_enums import QUEST_DATA, QUEST_NAMES, get_quest_id, get_quest_ids, get_quest_name

__all__ = [
    "QUEST_DATA",
    "QUEST_NAMES",
    "get_quest_id",
    "get_quest_ids",
    "get_quest_name",
]
