"""
Public Behavior Tree routines related to quest-state conditions.
"""

from __future__ import annotations

from ...Py4GWcorelib import Console, ConsoleLog
from ...Quest import Quest
from ...py4gwcorelib_src.BehaviorTree import BehaviorTree


def _log(
    source: str,
    message: str,
    *,
    log: bool = False,
    message_type=Console.MessageType.Info,
) -> None:
    ConsoleLog(
        source,
        message,
        message_type,
        log=log,
    )


class BTQuest:
    """
    Public BT helper group for quest-state conditions.

    Meta:
      Expose: true
      Audience: advanced
      Display: Quest
      Purpose: Group public BT routines related to quest state and quest-log conditions.
      UserDescription: Built-in BT helper group for checking quest state.
      Notes: Public PascalCase methods marked exposed are discovery candidates.
    """

    
    

