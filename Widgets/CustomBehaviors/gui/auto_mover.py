from typing import Any, Callable, Generator
from Py4GWCoreLib import IconsFontAwesome5, PyImGui, Routines
from Py4GWCoreLib.GlobalCache import GLOBAL_CACHE
from Py4GWCoreLib.Pathing import AutoPathing
from Widgets.CustomBehaviors.primitives import constants
from Widgets.CustomBehaviors.primitives.custom_behavior_loader import CustomBehaviorLoader, MatchResult
from Widgets.CustomBehaviors.primitives.parties.custom_behavior_shared_memory import CustomBehaviorWidgetMemoryManager
from Widgets.CustomBehaviors.primitives.skillbars.custom_behavior_base_utility import CustomBehaviorBaseUtility
from Widgets.CustomBehaviors.skills.botting.move_if_stuck import MoveIfStuckUtility
from Widgets.CustomBehaviors.skills.botting.move_to_distant_chest_if_path_exists import MoveToDistantChestIfPathExistsUtility
from Widgets.CustomBehaviors.skills.botting.move_to_enemy_if_close_enough import MoveToEnemyIfCloseEnoughUtility
from Widgets.CustomBehaviors.skills.botting.move_to_party_member_if_dead import MoveToPartyMemberIfDeadUtility
from Widgets.CustomBehaviors.skills.botting.move_to_party_member_if_in_aggro import MoveToPartyMemberIfInAggroUtility
from Widgets.CustomBehaviors.skills.botting.resign_if_needed import ResignIfNeededUtility
from Widgets.CustomBehaviors.skills.botting.wait_if_in_aggro import WaitIfInAggroUtility
from Widgets.CustomBehaviors.skills.botting.wait_if_party_member_mana_too_low import WaitIfPartyMemberManaTooLowUtility
from Widgets.CustomBehaviors.skills.botting.wait_if_party_member_needs_to_loot import WaitIfPartyMemberNeedsToLootUtility
from Widgets.CustomBehaviors.skills.botting.wait_if_party_member_too_far import WaitIfPartyMemberTooFarUtility

shared_data = CustomBehaviorWidgetMemoryManager().GetCustomBehaviorWidgetData()
generator:Generator[Any, None, Any] | None = None
coords_input_buffer = ["0, 0"]  # Mutable object to persist between frames
movement_progress:float = 0

@staticmethod
def render():
    global generator, coords_input_buffer  # Tell Python we're referring to the global one

    PyImGui.text(f"auto-moving from map coords [U] - copy paste coordinate from [MissionMap+ - Widget]")
    PyImGui.separator()

    if not GLOBAL_CACHE.Party.IsPartyLeader():
        PyImGui.text(f"feature restricted to party leader.")
        return

    # Render editable text box for coords
    coords_input_buffer[0] = PyImGui.input_text("coords", coords_input_buffer[0])

    instance:CustomBehaviorBaseUtility = CustomBehaviorLoader().custom_combat_behavior
    if instance is None: return

    if generator is None:
        if PyImGui.button("PLAY"):

            target_position: tuple[float, float] | None = None

            # Try to parse the coordinates input
            try:
                # Attempt to split and map the input to two floats
                coords = coords_input_buffer[0].split(",")
                if len(coords) != 2:
                    raise ValueError("Expected two coordinates separated by a comma.")

                # Try to convert each part of the split input into floats
                target_position = tuple(map(float, coords))
                
            except ValueError as e:
                print(f"Invalid coordinates format! Error: {e}")
                target_position = None  # If there's any error, set to None

            if target_position == None:
                return

            generator = move_to(target_position)

            # instance.inject_additionnal_utility_skills(ResignIfNeededUtility(instance.in_game_build))
            # instance.inject_additionnal_utility_skills(MoveToDistantChestIfPathExistsUtility(instance.in_game_build))

            instance.inject_additionnal_utility_skills(MoveIfStuckUtility(instance.in_game_build))
            instance.inject_additionnal_utility_skills(MoveToPartyMemberIfInAggroUtility(instance.in_game_build))
            instance.inject_additionnal_utility_skills(MoveToEnemyIfCloseEnoughUtility(instance.in_game_build))
            instance.inject_additionnal_utility_skills(MoveToPartyMemberIfDeadUtility(instance.in_game_build))
            instance.inject_additionnal_utility_skills(WaitIfPartyMemberManaTooLowUtility(instance.in_game_build))
            instance.inject_additionnal_utility_skills(WaitIfPartyMemberTooFarUtility(instance.in_game_build))
            instance.inject_additionnal_utility_skills(WaitIfPartyMemberNeedsToLootUtility(instance.in_game_build))
            instance.inject_additionnal_utility_skills(WaitIfInAggroUtility(instance.in_game_build))

            pass

    if generator is not None:
        PyImGui.text(f"Running {movement_progress}%")
        if PyImGui.button("STOP"):
            generator = None

    # Run one step of the generator
    if generator is not None:
        try:
            next(generator)
        except StopIteration:
            generator = None
    
    PyImGui.separator()
    PyImGui.text(f"such feature will inject additionnal utility skills,")
    PyImGui.text(f"so the leader account will be able to act as a bot - fully autonomous")

def move_to(target_position: tuple[float, float]) -> Generator[Any, None, Any]:

    global movement_progress

    instance:CustomBehaviorBaseUtility = CustomBehaviorLoader().custom_combat_behavior
    path3d = yield from AutoPathing().get_path_to(target_position[0], target_position[1], smooth_by_los=True, margin=100.0, step_dist=300.0)
    path2d:list[tuple[float, float]]  = [(x, y) for (x, y, *_ ) in path3d]

    custom_pause_fn: Callable[[], bool] | None = lambda: instance.is_executing_utility_skills() == True # meaning we pause moving across coords, if we have any action that is higher priority

    move_generator = Routines.Yield.Movement.FollowPath(
            path_points= path2d, 
            custom_exit_condition=lambda: GLOBAL_CACHE.Agent.IsDead(GLOBAL_CACHE.Player.GetAgentID()), # todo change to party is dead.
            tolerance=150, 
            log=constants.DEBUG, 
            timeout=-1, 
            progress_callback=on_progress,
            custom_pause_fn=custom_pause_fn)

    yield from move_generator

def on_progress(progress: float) -> None:
    global movement_progress
    movement_progress = round(progress * 100, 1)