"""
[FARM] Sunspear Title (BottingTree version)
Farms sunspear title points in Arkjok Ward using BottingTree with CustomBehavior integration.
"""

from Py4GWCoreLib import *
from Py4GWCoreLib.BottingTree import BottingTree
from Py4GWCoreLib.IniManager import IniManager
from Py4GWCoreLib.routines_src.BehaviourTrees import BT as RoutinesBT
from Sources.oazix.CustomBehaviors.gui.flag_panel.flag_backward_grid_placement import FlagBackwardGridPlacement
from Sources.oazix.CustomBehaviors.primitives.following_behavior_priority import FollowingBehaviorPriority
from Sources.oazix.CustomBehaviors.primitives.botting.botting_manager import BottingManager
from Sources.oazix.CustomBehaviors.primitives.parties.custom_behavior_party import CustomBehaviorParty
from Sources.oazix.CustomBehaviors.primitives.parties.party_flagging_manager import PartyFlaggingManager
from Sources.oazix.CustomBehaviors.primitives.parties.party_following_manager import PartyFollowingManager
from Sources.oazix.CustomBehaviors.skills.botting.move_to_enemy_if_close_enough import MoveToEnemyIfCloseEnoughUtility
from Sources.oazix.CustomBehaviors.skills.botting.move_to_party_member_if_dead import MoveToPartyMemberIfDeadUtility
from Sources.oazix.CustomBehaviors.skills.botting.move_to_party_member_if_in_aggro import MoveToPartyMemberIfInAggroUtility
from Sources.oazix.CustomBehaviors.skills.botting.wait_if_in_aggro import WaitIfInAggroUtility
from Sources.oazix.CustomBehaviors.skills.botting.wait_if_lock_taken import WaitIfLockTakenUtility
from Sources.oazix.CustomBehaviors.skills.botting.wait_if_party_member_mana_too_low import WaitIfPartyMemberManaTooLowUtility
from Sources.oazix.CustomBehaviors.skills.botting.wait_if_party_member_needs_to_loot import WaitIfPartyMemberNeedsToLootUtility
from Sources.oazix.CustomBehaviors.skills.botting.wait_if_party_member_too_far import WaitIfPartyMemberTooFarUtility

# Global settings
INI_KEY = ""
INI_PATH = "Widgets/BottingTree"
INI_FILENAME = "SunspearTitleBT.ini"
initialized = False
botting_tree: BottingTree | None = None

# Map IDs
YOHLON_HAVEN_OUTPOST = 381
ARKJOK_WARD_EXPLORABLE = 380

# Farm coordinates in Arkjok Ward
FARM_COORDINATES = [
    (-18872, -14304),
    (-17545, -12840),
    (-18249, -11494),
    (-18251, -9614),
    (-18255, -14646),
    (-18393, -15739),
    (-17499, -16418),
    (-16845, -17140),
    (-16535, -17567),
    (-17916, -16217),
    (-18763, -14359)
]

# NPC coordinates for bounty
BOUNTY_NPC_COORDS = Vec2f(-17223.0, -12543.0)
BOUNTY_DIALOG_ID = 0x85


def _configure_custom_behaviors() -> None:
    """Configure custom behavior settings for this farm."""
    CustomBehaviorParty().set_party_is_blessing_enabled(True)
    CustomBehaviorParty().set_party_is_combat_enabled(True)
    CustomBehaviorParty().set_party_is_looting_enabled(True)
    PartyFollowingManager().set_party_following_behavior_state(FollowingBehaviorPriority.LOW_PRIORITY)
    
    # Configure aggressive skills
    BottingManager().configure_aggressive_skill(MoveToEnemyIfCloseEnoughUtility.Name, enabled=True)
    BottingManager().configure_aggressive_skill(MoveToPartyMemberIfInAggroUtility.Name, enabled=True)
    BottingManager().configure_aggressive_skill(WaitIfLockTakenUtility.Name, enabled=True)
    BottingManager().configure_aggressive_skill(WaitIfPartyMemberTooFarUtility.Name, enabled=True)
    BottingManager().configure_aggressive_skill(MoveToPartyMemberIfDeadUtility.Name, enabled=True)
    BottingManager().configure_aggressive_skill(WaitIfPartyMemberManaTooLowUtility.Name, enabled=True)
    BottingManager().configure_aggressive_skill(WaitIfPartyMemberNeedsToLootUtility.Name, enabled=True)
    BottingManager().configure_aggressive_skill(WaitIfInAggroUtility.Name, enabled=True)
    
    # Set flag placement
    FlagBackwardGridPlacement.apply_backward_grid_to_flag_manager()
    PartyFlaggingManager().clear_all_flags()


def InitializeCustomBehaviors() -> BehaviorTree:
    """Initialize custom behaviors configuration."""
    def _init(node: BehaviorTree.Node) -> BehaviorTree.NodeState:
        _configure_custom_behaviors()
        return BehaviorTree.NodeState.SUCCESS
    
    return BehaviorTree(
        BehaviorTree.ActionNode(
            name="InitializeCustomBehaviors",
            action_fn=_init,
            aftercast_ms=1000
        )
    )


def TravelToYohlonHaven() -> BehaviorTree:
    """Travel to Yohlon Haven outpost."""
    return BehaviorTree(
        BehaviorTree.SequenceNode(
            name="TravelToYohlonHaven",
            children=[
                RoutinesBT.Travel.ToMap(YOHLON_HAVEN_OUTPOST),
                RoutinesBT.Party.SetHardMode(False),
            ]
        )
    )


def ExitToArkjokWard() -> BehaviorTree:
    """Exit from Yohlon Haven to Arkjok Ward."""
    return BehaviorTree(
        BehaviorTree.SequenceNode(
            name="ExitToArkjokWard",
            children=[
                RoutinesBT.Player.Move(5987, 1241, log=False),
                RoutinesBT.Map.WaitForMapLoad(ARKJOK_WARD_EXPLORABLE),
            ]
        )
    )


def GetBounty() -> BehaviorTree:
    """Get bounty from the Wandering Priest NPC."""
    return BehaviorTree(
        BehaviorTree.SequenceNode(
            name="GetBounty",
            children=[
                RoutinesBT.Player.Move(BOUNTY_NPC_COORDS.x, BOUNTY_NPC_COORDS.y, log=False),
                RoutinesBT.NPC.Dialog(BOUNTY_DIALOG_ID),
            ]
        )
    )


def FarmRoute() -> BehaviorTree:
    """Farm along the route killing enemies."""
    farm_moves = [
        RoutinesBT.Player.Move(x, y, log=False, pause_on_combat=False)
        for x, y in FARM_COORDINATES
    ]

    return BehaviorTree(
        BehaviorTree.SequenceNode(
            name="FarmRoute",
            children=farm_moves
        )
    )


def ReturnToOutpost() -> BehaviorTree:
    """Return to Yohlon Haven outpost."""
    return BehaviorTree(
        BehaviorTree.SequenceNode(
            name="ReturnToOutpost",
            children=[
                RoutinesBT.Player.Move(-21789, -14798, log=False),
                RoutinesBT.Map.WaitForMapLoad(YOHLON_HAVEN_OUTPOST),
            ]
        )
    )


def ResignParty() -> BehaviorTree:
    """Resign the party to reset the instance."""
    return BehaviorTree(
        BehaviorTree.SequenceNode(
            name="ResignParty",
            children=[
                RoutinesBT.Party.Resign(timeout_ms=50000),
            ]
        )
    )


def _get_sequence_builders():
    """Define the farming sequence."""
    return [
        ("Initialize", InitializeCustomBehaviors),
        ("Travel", TravelToYohlonHaven),
        ("ExitOutpost", ExitToArkjokWard),
        ("GetBounty", GetBounty),
        ("Farm", FarmRoute),
        ("Return", ReturnToOutpost),
        ("Resign", ResignParty),
    ]


def _add_config_vars():
    """Add configuration variables to INI file."""
    global INI_KEY
    IniManager().add_bool(INI_KEY, "pause_on_combat", "Behavior", "PauseOnCombat", default=False)
    IniManager().add_bool(INI_KEY, "enable_isolation", "Behavior", "EnableIsolation", default=True)
    IniManager().add_bool(INI_KEY, "enable_looting", "Behavior", "EnableLooting", default=True)


def ensure_botting_tree() -> BottingTree:
    """Ensure botting tree is initialized."""
    global botting_tree
    if botting_tree is None:
        # Create BottingTree with custom_behaviors enabled
        botting_tree = BottingTree(
            pause_on_combat=False,  # Don't pause on combat - let custom behaviors handle it
            isolation_enabled=True,
            use_custom_behaviors=True  # Enable custom behavior integration
        )
    return botting_tree


def main():
    global INI_KEY, initialized, botting_tree

    if not initialized:
        if not INI_KEY:
            INI_KEY = IniManager().ensure_key(INI_PATH, INI_FILENAME)
            if not INI_KEY:
                return
            _add_config_vars()
            IniManager().load_once(INI_KEY)

        botting_tree = ensure_botting_tree()
        botting_tree.SetCurrentNamedPlannerSteps(
            _get_sequence_builders(),
            start_from="Initialize",
            name="SunspearTitleFarm",
            auto_start=False,
        )
        initialized = True

    if botting_tree is not None:
        botting_tree.tick()
        botting_tree.Draw()

if __name__ == "__main__":
    main()
