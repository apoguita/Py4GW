from __future__ import annotations

from typing import TYPE_CHECKING

from Py4GWCoreLib.BuildMgr import BuildCoroutine
from Py4GWCoreLib import Range, Routines
from Py4GWCoreLib.Agent import Agent
from Py4GWCoreLib.Player import Player

if TYPE_CHECKING:
    from Py4GWCoreLib.BuildMgr import BuildMgr

__all__ = ["NoAttribute"]


class NoAttribute:
    def __init__(self, build: BuildMgr) -> None:
        self.build: BuildMgr = build

    #region D
    def Drop_Held_Bundle(
        self,
        *,
        min_party_damaged_count: int = 4,
        health_threshold: float = 0.65,
        within_range: float = Range.Spirit.value,
    ) -> BuildCoroutine:
        """Drop the currently-held bundle (item-spell ashes) when at least
        `min_party_damaged_count` allies within `within_range` are below
        `health_threshold` HP (0.0-1.0). Returns False when not holding a
        bundle or the threshold isn't met.

        Bundle item-spells (Protective Was Kaolai, Vital Was Soothing,
        Generous Was Tsungrai, ...) heal/buff the party on drop. Sequence
        this check BEFORE the cast in any rotation that holds an item spell
        so we release the heal before recasting."""
        from Py4GWCoreLib import AgentArray, UIManager

        player_id: int = Player.GetAgentID()

        if not Agent.IsHoldingItem(player_id):
            return False

        # Inline party-damage scan via Routines.Checks.Agents.* so remote
        # heroes' HP is read from the shared-memory broadcast (correct in
        # multibox) instead of this client's stale local view.
        ally_ids = AgentArray.GetAllyArray()
        ally_ids = AgentArray.Filter.ByDistance(ally_ids, Player.GetXY(), within_range)
        ally_ids = AgentArray.Filter.ByCondition(ally_ids, lambda aid: Routines.Checks.Agents.IsAlive(aid))

        damaged_count = 0
        for aid in ally_ids:
            if Routines.Checks.Agents.GetHealth(aid) < health_threshold:
                damaged_count += 1
                if damaged_count >= min_party_damaged_count:
                    break
        if damaged_count < min_party_damaged_count:
            return False

        # Frame 5040781 is the in-game "Drop Bundle Button" (see
        # Py4GWCoreLib/frame_aliases.json). Clicking it directly is more
        # reliable than ControlAction_DropItem - the keybind silently no-ops if
        # the player hasn't bound a drop-item key in GW's controls.
        drop_button_ids = UIManager.GetAllChildFrameIDs(5040781, [0, 0])
        if not drop_button_ids or not UIManager.FrameExists(drop_button_ids[0]):
            return False

        UIManager.FrameClick(drop_button_ids[0])
        # FrameClick isn't a CastSkillID-style cast, so BuildMgr's per-tick
        # aftercast timer isn't stamped automatically. Mark it manually so the
        # next tick doesn't fire another action while the engine is still
        # processing the drop. Stamp BEFORE yielding so the outer loop sees
        # the timer set on its very next pass.
        self.build._mark_local_cast_pending(250)
        yield  # Keep this a generator under BuildCoroutine; gives the engine
        # one tick to register the drop before the rotation continues.
        return True
    #endregion
