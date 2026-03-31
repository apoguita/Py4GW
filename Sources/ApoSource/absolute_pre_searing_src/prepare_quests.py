from typing import Callable

from Py4GWCoreLib.Agent import Agent
from Py4GWCoreLib.enums import Range
from Py4GWCoreLib.py4gwcorelib_src.BehaviorTree import BehaviorTree
from Py4GWCoreLib.routines_src.BehaviourTrees import BT as RoutinesBT

from .data import GENESIS_DATA


def Sequence_001_Common(module_name: str, print_to_console: bool | Callable[[], bool] = False) -> BehaviorTree:
    sequence_001_common_data = GENESIS_DATA.sequence_001_common_data

    tree = BehaviorTree.SequenceNode(
        name="Starting common sequence",
        children=[
            RoutinesBT.Player.LogMessage(source=module_name, to_console=print_to_console, to_blackboard=True, message="Starting Absolute Pre-Searing"),
            RoutinesBT.Player.LogMessage(source=module_name, to_console=print_to_console, to_blackboard=True, message=sequence_001_common_data.town_cryer_message),
            RoutinesBT.Agents.MoveTargetInteractAndAutomaticDialog(
                x=sequence_001_common_data.town_cryer_coords[0],
                y=sequence_001_common_data.town_cryer_coords[1],
                button_number=0,
                log=False,
            ),
            RoutinesBT.Player.LogMessage(source=module_name, to_console=print_to_console, to_blackboard=True, message=sequence_001_common_data.sir_tydius_message),
            RoutinesBT.Agents.MoveTargetInteractAndAutomaticDialog(
                x=sequence_001_common_data.sir_tydius_coords[0],
                y=sequence_001_common_data.sir_tydius_coords[1],
                button_number=0,
                log=False,
            ),
            RoutinesBT.Player.SendAutomaticDialog(button_number=0, log=False),
            RoutinesBT.Player.LogMessage(source=module_name, to_console=print_to_console, to_blackboard=True, message=sequence_001_common_data.exit_map_message),
            RoutinesBT.Player.Move(x=sequence_001_common_data.exit_map_coords[0], y=sequence_001_common_data.exit_map_coords[1], log=False),
            RoutinesBT.Map.WaitforMapLoad(map_id=sequence_001_common_data.lakeside_county_map_id, log=False),
        ],
    )
    return BehaviorTree(tree)


def Warrior_001_Sequence(module_name: str, print_to_console: bool | Callable[[], bool] = False) -> BehaviorTree:
    quest_001_warrior_data = GENESIS_DATA.quest_001_warrior_data

    tree = BehaviorTree.SequenceNode(
        name="Warrior 001 sequence",
        children=[
            RoutinesBT.Player.LogMessage(source=module_name, to_console=print_to_console, to_blackboard=True, message=quest_001_warrior_data.van_the_warrior_message),
            RoutinesBT.Agents.MoveTargetInteractAndAutomaticDialog(
                x=quest_001_warrior_data.van_the_warrior_coords[0],
                y=quest_001_warrior_data.van_the_warrior_coords[1],
                button_number=0,
                log=False,
            ),
            RoutinesBT.Player.SendAutomaticDialog(button_number=0, log=False),
            RoutinesBT.Player.LogMessage(source=module_name, to_console=print_to_console, to_blackboard=True, message=GENESIS_DATA.quest_001_common_data.skale_kill_spot_message),
            RoutinesBT.Player.Move(x=quest_001_warrior_data.skale_coords[0], y=quest_001_warrior_data.skale_coords[1], log=False),
            RoutinesBT.Player.LogMessage(source=module_name, to_console=print_to_console, to_blackboard=True, message=GENESIS_DATA.quest_001_common_data.skale_kill_spot_arrival_message),
            RoutinesBT.Agents.ClearEnemiesInArea(
                x=quest_001_warrior_data.skale_coords[0],
                y=quest_001_warrior_data.skale_coords[1],
                radius=GENESIS_DATA.quest_001_common_data.clear_area_radius,
                log=False,
            ),
            RoutinesBT.Player.LogMessage(source=module_name, to_console=print_to_console, to_blackboard=True, message=quest_001_warrior_data.return_message),
            RoutinesBT.Agents.MoveTargetInteractAndAutomaticDialog(
                x=quest_001_warrior_data.van_the_warrior_coords[0],
                y=quest_001_warrior_data.van_the_warrior_coords[1],
                button_number=0,
                log=False,
            ),
        ],
    )
    return BehaviorTree(tree)


def Ranger_001_Sequence(module_name: str, print_to_console: bool | Callable[[], bool] = False) -> BehaviorTree:
    quest_001_ranger_data = GENESIS_DATA.quest_001_ranger_data

    tree = BehaviorTree.SequenceNode(
        name="Ranger 001 sequence",
        children=[
            RoutinesBT.Player.LogMessage(source=module_name, to_console=print_to_console, to_blackboard=True, message=quest_001_ranger_data.artemis_the_ranger_message),
            RoutinesBT.Agents.MoveTargetInteractAndAutomaticDialog(
                x=quest_001_ranger_data.artemis_the_ranger_coords[0],
                y=quest_001_ranger_data.artemis_the_ranger_coords[1],
                button_number=0,
                log=False,
            ),
            RoutinesBT.Player.SendAutomaticDialog(button_number=0, log=False),
            RoutinesBT.Player.LogMessage(source=module_name, to_console=print_to_console, to_blackboard=True, message=GENESIS_DATA.quest_001_common_data.skale_kill_spot_message),
            RoutinesBT.Player.Move(x=quest_001_ranger_data.skale_coords[0], y=quest_001_ranger_data.skale_coords[1], log=False),
            RoutinesBT.Player.LogMessage(source=module_name, to_console=print_to_console, to_blackboard=True, message=GENESIS_DATA.quest_001_common_data.skale_kill_spot_arrival_message),
            RoutinesBT.Agents.ClearEnemiesInArea(
                x=quest_001_ranger_data.skale_coords[0],
                y=quest_001_ranger_data.skale_coords[1],
                radius=GENESIS_DATA.quest_001_common_data.clear_area_radius,
                log=False,
            ),
            RoutinesBT.Player.LogMessage(source=module_name, to_console=print_to_console, to_blackboard=True, message=quest_001_ranger_data.return_message),
            RoutinesBT.Agents.MoveTargetInteractAndAutomaticDialog(
                x=quest_001_ranger_data.artemis_the_ranger_coords[0],
                y=quest_001_ranger_data.artemis_the_ranger_coords[1],
                button_number=0,
                log=False,
            ),
        ],
    )
    return BehaviorTree(tree)


def Monk_001_Sequence(module_name: str, print_to_console: bool | Callable[[], bool] = False) -> BehaviorTree:
    quest_001_monk_data = GENESIS_DATA.quest_001_monk_data

    tree = BehaviorTree.SequenceNode(
        name="Monk 001 sequence",
        children=[
            RoutinesBT.Player.LogMessage(source=module_name, to_console=print_to_console, to_blackboard=True, message=quest_001_monk_data.cigio_the_monk_message),
            RoutinesBT.Agents.MoveTargetInteractAndAutomaticDialog(
                x=quest_001_monk_data.cigio_the_monk_coords[0],
                y=quest_001_monk_data.cigio_the_monk_coords[1],
                button_number=0,
                log=False,
            ),
            RoutinesBT.Player.SendAutomaticDialog(button_number=0, log=False),
            RoutinesBT.Player.LogMessage(source=module_name, to_console=print_to_console, to_blackboard=True, message=GENESIS_DATA.quest_001_common_data.skale_kill_spot_message),
            RoutinesBT.Player.Move(x=quest_001_monk_data.skale_coords[0], y=quest_001_monk_data.skale_coords[1], log=False),
            RoutinesBT.Player.LogMessage(source=module_name, to_console=print_to_console, to_blackboard=True, message=GENESIS_DATA.quest_001_common_data.skale_kill_spot_arrival_message),
            RoutinesBT.Agents.ClearEnemiesInArea(
                x=quest_001_monk_data.skale_coords[0],
                y=quest_001_monk_data.skale_coords[1],
                radius=GENESIS_DATA.quest_001_common_data.clear_area_radius,
                log=False,
            ),
            RoutinesBT.Player.LogMessage(source=module_name, to_console=print_to_console, to_blackboard=True, message=quest_001_monk_data.gwen_message),
            RoutinesBT.Agents.MoveTargetAndInteract(
                x=quest_001_monk_data.gwen_coords[0],
                y=quest_001_monk_data.gwen_coords[1],
                target_distance=Range.Area.value,
                log=False,
            ),
            RoutinesBT.Player.LogMessage(source=module_name, to_console=print_to_console, to_blackboard=True, message=quest_001_monk_data.return_message),
            RoutinesBT.Agents.MoveTargetInteractAndAutomaticDialog(
                x=quest_001_monk_data.cigio_the_monk_coords[0],
                y=quest_001_monk_data.cigio_the_monk_coords[1],
                button_number=0,
                log=False,
            ),
        ],
    )
    return BehaviorTree(tree)


def Necromancer_001_Sequence(module_name: str, print_to_console: bool | Callable[[], bool] = False) -> BehaviorTree:
    quest_001_necromancer_data = GENESIS_DATA.quest_001_necromancer_data

    tree = BehaviorTree.SequenceNode(
        name="Necromancer 001 sequence",
        children=[
            RoutinesBT.Player.LogMessage(source=module_name, to_console=print_to_console, to_blackboard=True, message=quest_001_necromancer_data.verata_the_necromancer_message),
            RoutinesBT.Agents.MoveTargetInteractAndAutomaticDialog(
                x=quest_001_necromancer_data.verata_the_necromancer_coords[0],
                y=quest_001_necromancer_data.verata_the_necromancer_coords[1],
                button_number=0,
                log=False,
            ),
            RoutinesBT.Player.SendAutomaticDialog(button_number=0, log=False),
            RoutinesBT.Player.LogMessage(source=module_name, to_console=print_to_console, to_blackboard=True, message=GENESIS_DATA.quest_001_common_data.skale_kill_spot_message),
            RoutinesBT.Player.Move(x=quest_001_necromancer_data.skale_coords[0], y=quest_001_necromancer_data.skale_coords[1], log=False),
            RoutinesBT.Player.LogMessage(source=module_name, to_console=print_to_console, to_blackboard=True, message=GENESIS_DATA.quest_001_common_data.skale_kill_spot_arrival_message),
            RoutinesBT.Agents.ClearEnemiesInArea(
                x=quest_001_necromancer_data.skale_coords[0],
                y=quest_001_necromancer_data.skale_coords[1],
                radius=GENESIS_DATA.quest_001_common_data.clear_area_radius,
                log=False,
            ),
            RoutinesBT.Agents.MoveTargetInteractAndAutomaticDialogByModelID(
                model_id=Agent.GetModelIDByEncString(
                    quest_001_necromancer_data.verata_the_necromancer_enc_string
                ),
                button_number=0,
                log=False,
            ),
        ],
    )
    return BehaviorTree(tree)


def Mesmer_001_Sequence(module_name: str, print_to_console: bool | Callable[[], bool] = False) -> BehaviorTree:
    quest_001_mesmer_data = GENESIS_DATA.quest_001_mesmer_data

    tree = BehaviorTree.SequenceNode(
        name="Mesmer 001 sequence",
        children=[
            RoutinesBT.Player.LogMessage(source=module_name, to_console=print_to_console, to_blackboard=True, message=quest_001_mesmer_data.sebedoh_the_mesmer_message),
            RoutinesBT.Agents.MoveTargetInteractAndAutomaticDialog(
                x=quest_001_mesmer_data.sebedoh_the_mesmer_coords[0],
                y=quest_001_mesmer_data.sebedoh_the_mesmer_coords[1],
                button_number=0,
                log=False,
            ),
            RoutinesBT.Player.SendAutomaticDialog(button_number=0, log=False),
            RoutinesBT.Player.LogMessage(source=module_name, to_console=print_to_console, to_blackboard=True, message=GENESIS_DATA.quest_001_common_data.skale_kill_spot_message),
            RoutinesBT.Player.Move(x=quest_001_mesmer_data.skale_coords[0], y=quest_001_mesmer_data.skale_coords[1], log=False),
            RoutinesBT.Player.LogMessage(source=module_name, to_console=print_to_console, to_blackboard=True, message=GENESIS_DATA.quest_001_common_data.skale_kill_spot_arrival_message),
            RoutinesBT.Agents.ClearEnemiesInArea(
                x=quest_001_mesmer_data.skale_coords[0],
                y=quest_001_mesmer_data.skale_coords[1],
                radius=GENESIS_DATA.quest_001_common_data.clear_area_radius,
                log=False,
            ),
            RoutinesBT.Player.LogMessage(source=module_name, to_console=print_to_console, to_blackboard=True, message=quest_001_mesmer_data.return_message),
            RoutinesBT.Agents.MoveTargetInteractAndAutomaticDialog(
                x=quest_001_mesmer_data.sebedoh_the_mesmer_coords[0],
                y=quest_001_mesmer_data.sebedoh_the_mesmer_coords[1],
                button_number=0,
                log=False,
            ),
        ],
    )
    return BehaviorTree(tree)


def Elementalist_001_Sequence(module_name: str, print_to_console: bool | Callable[[], bool] = False) -> BehaviorTree:
    quest_001_elementalist_data = GENESIS_DATA.quest_001_elementalist_data

    tree = BehaviorTree.SequenceNode(
        name="Elementalist 001 sequence",
        children=[
            RoutinesBT.Player.LogMessage(source=module_name, to_console=print_to_console, to_blackboard=True, message=quest_001_elementalist_data.quest_giver_message),
            RoutinesBT.Agents.MoveTargetInteractAndAutomaticDialog(
                x=quest_001_elementalist_data.quest_giver_coords[0],
                y=quest_001_elementalist_data.quest_giver_coords[1],
                button_number=0,
                log=False,
            ),
            RoutinesBT.Player.SendAutomaticDialog(button_number=0, log=False),
            RoutinesBT.Player.LogMessage(source=module_name, to_console=print_to_console, to_blackboard=True, message=GENESIS_DATA.quest_001_common_data.skale_kill_spot_message),
            RoutinesBT.Player.Move(x=quest_001_elementalist_data.skale_coords[0], y=quest_001_elementalist_data.skale_coords[1], log=False),
            RoutinesBT.Player.LogMessage(source=module_name, to_console=print_to_console, to_blackboard=True, message=GENESIS_DATA.quest_001_common_data.skale_kill_spot_arrival_message),
            RoutinesBT.Agents.ClearEnemiesInArea(
                x=quest_001_elementalist_data.skale_coords[0],
                y=quest_001_elementalist_data.skale_coords[1],
                radius=GENESIS_DATA.quest_001_common_data.clear_area_radius,
                log=False,
            ),
            RoutinesBT.Player.LogMessage(source=module_name, to_console=print_to_console, to_blackboard=True, message=quest_001_elementalist_data.return_message),
            RoutinesBT.Agents.MoveTargetInteractAndAutomaticDialog(
                x=quest_001_elementalist_data.quest_giver_coords[0],
                y=quest_001_elementalist_data.quest_giver_coords[1],
                button_number=0,
                log=False,
            ),
            RoutinesBT.Player.LogMessage(source=module_name, to_console=print_to_console, to_blackboard=True, message=quest_001_elementalist_data.cleanup_message),
            RoutinesBT.Items.DestroyItems(
                model_ids=list(quest_001_elementalist_data.cleanup_model_ids),
                log=False,
                aftercast_ms=100,
            ),
        ],
    )
    return BehaviorTree(tree)


def Profession_Specific_Quest_001_Sequence(module_name: str, print_to_console: bool | Callable[[], bool] = False) -> BehaviorTree:
    tree = BehaviorTree.SequenceNode(
        name="Profession specific quest 001 sequence",
        children=[
            RoutinesBT.Player.StorePrimaryProfessionName(
                blackboard_key="player_primary_profession_name",
                log=False,
            ),
            BehaviorTree.SwitchNode(
                selector_fn=lambda node: node.blackboard.get("player_primary_profession_name", ""),
                cases=[
                    ("Warrior", lambda: Warrior_001_Sequence(module_name, print_to_console)),
                    ("Ranger", lambda: Ranger_001_Sequence(module_name, print_to_console)),
                    ("Monk", lambda: Monk_001_Sequence(module_name, print_to_console)),
                    ("Necromancer", lambda: Necromancer_001_Sequence(module_name, print_to_console)),
                    ("Mesmer", lambda: Mesmer_001_Sequence(module_name, print_to_console)),
                    ("Elementalist", lambda: Elementalist_001_Sequence(module_name, print_to_console)),
                ],
                name="RunProfessionSequence",
            ),
        ],
    )
    return BehaviorTree(tree)


def Sequence_002_Common(module_name: str, print_to_console: bool | Callable[[], bool] = False) -> BehaviorTree:
    quest_001_common_data = GENESIS_DATA.quest_001_common_data
    sequence_002_common_data = GENESIS_DATA.sequence_002_common_data

    tree = BehaviorTree.SequenceNode(
        name="Starting common sequence",
        children=[
            RoutinesBT.Player.LogMessage(source=module_name, to_console=print_to_console, to_blackboard=True, message="Waiting for Haversdan to arrive"),
            RoutinesBT.Player.Move(x=quest_001_common_data.wait_for_haversdan_coords[0], y=quest_001_common_data.wait_for_haversdan_coords[1], log=False),
            RoutinesBT.Player.Wait(duration_ms=quest_001_common_data.haversdan_wait_ms, log=True),
            RoutinesBT.Player.LogMessage(source=module_name, to_console=print_to_console, to_blackboard=True, message="Moving to Haversdan"),
            RoutinesBT.Agents.MoveTargetInteractAndAutomaticDialog(
                x=quest_001_common_data.haversdan_coords[0],
                y=quest_001_common_data.haversdan_coords[1],
                target_distance=Range.Area.value,
                button_number=0,
                log=False,
            ),
            RoutinesBT.Player.LogMessage(source=module_name, to_console=print_to_console, to_blackboard=True, message="Moving to Pitney"),
            RoutinesBT.Agents.MoveTargetInteractAndAutomaticDialog(
                x=quest_001_common_data.pitney_coords[0],
                y=quest_001_common_data.pitney_coords[1],
                target_distance=Range.Area.value,
                button_number=0,
                log=False,
            ),
            RoutinesBT.Player.LogMessage(source=module_name, to_console=print_to_console, to_blackboard=True, message="Moving to Ashford Devona"),
            RoutinesBT.Agents.MoveTargetInteractAndAutomaticDialog(
                x=quest_001_common_data.devona_coords[0],
                y=quest_001_common_data.devona_coords[1],
                button_number=0,
                log=False,
            ),
            RoutinesBT.Player.SendAutomaticDialog(button_number=0, log=False),
            RoutinesBT.Player.LogMessage(source=module_name, to_console=print_to_console, to_blackboard=True, message="Moving to Ashford Abbey"),
            RoutinesBT.Player.Move(x=quest_001_common_data.ashford_abbey_move_coords[0], y=quest_001_common_data.ashford_abbey_move_coords[1], log=False),
            RoutinesBT.Map.WaitforMapLoad(map_id=quest_001_common_data.ashford_abbey_map_id, log=False),
            RoutinesBT.Player.LogMessage(source=module_name, to_console=print_to_console, to_blackboard=True, message="Moving to Meerak"),
            RoutinesBT.Agents.MoveTargetInteractAndAutomaticDialog(
                x=quest_001_common_data.meerak_coords[0],
                y=quest_001_common_data.meerak_coords[1],
                button_number=0,
                log=False,
            ),
            RoutinesBT.Player.LogMessage(source=module_name, to_console=print_to_console, to_blackboard=True, message=sequence_002_common_data.Travel_to_ascalon_city_message),
            RoutinesBT.Map.TravelToOutpost(outpost_id=sequence_002_common_data.ascalon_city_map_id),
            RoutinesBT.Player.LogMessage(source=module_name, to_console=print_to_console, to_blackboard=True, message=sequence_002_common_data.amin_saberlin_message),
            RoutinesBT.Player.Move(x=sequence_002_common_data.amin_saberlin_001_coords[0], y=sequence_002_common_data.amin_saberlin_001_coords[1], log=False),
            RoutinesBT.Agents.MoveTargetInteractAndAutomaticDialog(
                x=sequence_002_common_data.amin_saberlin_coords[0],
                y=sequence_002_common_data.amin_saberlin_coords[1],
                button_number=0,
                log=False,
            ),
            RoutinesBT.Player.SendAutomaticDialog(button_number=0, log=False),
            RoutinesBT.Player.LogMessage(source=module_name, to_console=print_to_console, to_blackboard=True, message="sequence completed!"),
        ],
    )
    return BehaviorTree(tree)


def get_sequence_builders(module_name: str, print_to_console: bool | Callable[[], bool] = False) -> list[tuple[str, Callable[[], BehaviorTree]]]:
    return [
        ("Sequence_001_Common", lambda: Sequence_001_Common(module_name, print_to_console)),
        ("Profession_Specific_Quest_001_Sequence", lambda: Profession_Specific_Quest_001_Sequence(module_name, print_to_console)),
        ("Sequence_002_Common", lambda: Sequence_002_Common(module_name, print_to_console)),
    ]
