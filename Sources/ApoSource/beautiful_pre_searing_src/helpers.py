from typing import Callable, TypeAlias
from Sources.ApoSource.beautiful_pre_searing_src.globals import *
from Py4GWCoreLib.BottingTree import BottingTree
from Py4GWCoreLib.Agent import Agent
from Py4GWCoreLib.Player import Player

def subtree_step(name: str, tree_builder: Callable[[], BehaviorTree]) -> BehaviorTree.Node:
    return BehaviorTree.SubtreeNode(
        name=name,
        subtree_fn=lambda node: tree_builder(),
    )

def named_planner_steps_to_sequence(
    name: str,
    steps: list[tuple[str, Callable[[], BehaviorTree]]],
) -> BehaviorTree:
    return BehaviorTree(
        BehaviorTree.SequenceNode(
            name=name,
            children=[
                subtree_step(step_name, step_builder)
                for step_name, step_builder in steps
            ],
        )
    )

def start_tree_with_heroai_enabled(botting_tree: BottingTree, tree: BehaviorTree | None) -> None:
    botting_tree.EnableHeadlessHeroAI()
    botting_tree.SetCurrentTree(tree, auto_start=True)


def start_named_steps_with_heroai_enabled(
    botting_tree: BottingTree,
    steps,
    name: str,
) -> None:
    botting_tree.EnableHeadlessHeroAI()
    botting_tree.SetCurrentNamedPlannerSteps(
        steps,
        name=name,
        auto_start=True,
    )

def LogMessage(message: str) -> BehaviorTree:
    return BT.LogMessage(
        message=message,
        module_name=MODULE_NAME,
        print_to_console=PRINT_TO_CONSOLE,
        print_to_blackboard=PRINT_TO_BLACKBOARD,
    )


def get_merchant_coords_from_map_id() -> Vec2f | None:
    from Py4GWCoreLib.Map import Map

    current_map_id = Map.GetMapID()
    if current_map_id == ASCALON_CITY_MAP_ID:
        return Vec2f(8470.88, 4882.44)
    if current_map_id == ASHFORD_ABBEY_MAP_ID:
        return Vec2f(-11477.68, -6431.78)
    if current_map_id == FOIBLES_FAIR_MAP_ID:
        return Vec2f(-906.54, 10786.26)
    if current_map_id == BARRADIN_STATE_MAP_ID:
        return Vec2f(-6509.08, 1246.19)
    if current_map_id == FORT_RANIK_MAP_ID:
        return Vec2f(24507.09, 10367.38)
    return None


def get_exit_map_coords_from_map_id(alternate_exit:str | None = None) -> tuple[list[Vec2f], int] | None:
    from Py4GWCoreLib.Map import Map

    current_map_id = Map.GetMapID()
    if current_map_id == ASCALON_CITY_MAP_ID:
        return [EXIT_ASCALON_CITY_COORDS], LAKESIDE_COUNTY_MAP_ID
    if current_map_id == ASHFORD_ABBEY_MAP_ID:
        if alternate_exit == "The Catacombs":
            return EXIT_TO_CATACOMBS_COORDS, CATACOMBS_MAP_ID
        return EXIT_TO_LAKESIDE_COUNTY_COORDS, LAKESIDE_COUNTY_MAP_ID
    if current_map_id == FOIBLES_FAIR_MAP_ID:
        return FOIBLES_FAIR_EXIT_COORDS, WIZARDS_FOLLY_MAP_ID
    if current_map_id == FORT_RANIK_MAP_ID:
        return EXIT_TO_REGENT_VALLEY_COORDS, REGENT_VALLEY_MAP_ID
    return None

def get_build_for_level() -> str:
    primary, secondary = Agent.GetProfessionNames(Player.GetAgentID())
    
    level = Player.GetLevel()
    
    if primary == "Warrior": 
        if level < 5:
            return "OQISglcFaNA023bGAAAA"
        else:
            return "OQITED5VjAqKFAAQrBw30GA"
        
    if primary == "Ranger":
        if secondary == "Warrior":
            return "OgEUUDbglcFKGAAA2aNA+m2A"
        else:
            return "OgASglcFK230ezAAAAAA"

    if primary == "Monk":
        if level < 5:
            return "OwISglcFgkf023bGAAAA"
        else:
            return "OwIU4iXglcFokfAA2rEk+m2A"

    if primary == "Necromancer":
        if level < 5:
            return "OAJSglcFZKN023bGAAAA"
        else:
            return "OAJUQCbglcFZKNtBAAA2+m2A"

    if primary == "Mesmer":
        if level < 5:
            return "OQJSglcFaAF023bGAAAA"
        else:
            return "OQJTICsktQDbAAAA2ow30GA"

    if primary == "Elementalist":
        if level < 5:
            return "OgJSglcFCjW023bGAAAA"
        else:
            return "OgJSglcFCjW023bGAAAA"

    return "AAAAAAAAAAAAAAAAAAAA"


def equip_build_for_level() -> BehaviorTree:
    def _build(node: BehaviorTree.Node) -> BehaviorTree:
        build_template = get_build_for_level()
        return BehaviorTree(
            BehaviorTree.SequenceNode(
                name="EquipBuildForLevel",
                children=[
                    LogMessage("Equipping skillbar for current level"),
                    BT.LoadSkillbar(build_template),
                ],
            )
        )

    return BehaviorTree(
        BehaviorTree.SubtreeNode(
            name="RuntimeEquipBuildForLevel",
            subtree_fn=_build,
        )
    )


def _move_path(path: list[Vec2f], name: str) -> BehaviorTree:
    if not path:
        return BehaviorTree(
            BehaviorTree.SucceederNode(
                name=f"{name}EmptyPath",
            )
        )

    return BehaviorTree(
        BehaviorTree.SequenceNode(
            name=name,
            children=[BT.Move(point) for point in path],
        )
    )


def exit_current_map(alternate_exit: str | None = None) -> BehaviorTree:
    def _build(node: BehaviorTree.Node) -> BehaviorTree:
        exit_data = get_exit_map_coords_from_map_id(alternate_exit=alternate_exit)
        if exit_data is None:
            return BehaviorTree(
                BehaviorTree.FailerNode(
                    name="MissingExitDataForCurrentMap",
                )
            )

        exit_coords, target_map_id = exit_data
        return BehaviorTree(
            BehaviorTree.SequenceNode(
                name="ExitCurrentMap",
                children=[
                    LogMessage("Exiting current map"),
                    _move_path(exit_coords, "MoveToExit"),
                    BT.WaitForMapLoad(target_map_id),
                ],
            )
        )

    return BehaviorTree(
        BehaviorTree.SubtreeNode(
            name="RuntimeExitCurrentMap",
            subtree_fn=_build,
        )
    )


def MoveInteractAndSellItems(
    merchant_coords: Vec2f,
    exclude_models: list[int] | None = None,
    log: bool = False,
    target_distance: float = Range.Area.value,
    destroy_zero_value_items: bool = False,
) -> BehaviorTree:
    merchant_frame_hash = 3613855137

    def _is_merchant_window_open() -> bool:
        from Py4GWCoreLib.UIManager import UIManager

        merchant_frame_id = UIManager.GetFrameIDByHash(merchant_frame_hash)
        return merchant_frame_id != 0 and UIManager.FrameExists(merchant_frame_id)

    def _debug_cleanup_state(node: BehaviorTree.Node) -> BehaviorTree.NodeState:
        from Py4GWCoreLib import GLOBAL_CACHE
        exclude_list = list(exclude_models or [])
        excluded_models = set(exclude_list)
        sellable_item_ids: list[int] = []
        zero_value_item_ids: list[int] = []
        excluded_item_count = 0

        for item_id in GLOBAL_CACHE.Inventory.GetAllInventoryItemIds():
            if item_id == 0:
                continue

            model_id = GLOBAL_CACHE.Item.GetModelID(item_id)
            if model_id in excluded_models:
                excluded_item_count += 1
                continue

            item_value = int(GLOBAL_CACHE.Item.Properties.GetValue(item_id) or 0)
            if item_value > 0:
                sellable_item_ids.append(item_id)
            else:
                zero_value_item_ids.append(item_id)

        LogMessage(
            "DEBUG Merchant cleanup: "
            f"sellable_count={len(sellable_item_ids)} "
            f"zero_value_count={len(zero_value_item_ids)} "
            f"excluded_item_count={excluded_item_count} "
            f"excluded_models={exclude_list}"
        ).root.tick()
        return BehaviorTree.NodeState.SUCCESS

    return BehaviorTree(
        BehaviorTree.SelectorNode(
            name="MoveInteractAndSellItems",
            children=[
                BehaviorTree.SequenceNode(
                    name="MerchantCleanupRequired",
                    children=[
                        BehaviorTree.ActionNode(
                            name="DebugMerchantCleanupState",
                            action_fn=_debug_cleanup_state,
                            aftercast_ms=0,
                        ),
                        BT.NeedsInventoryCleanup(exclude_models=exclude_models),
                        LogMessage("Inventory cleanup needed, visiting merchant"),
                        BT.MoveAndInteract(merchant_coords, target_distance=target_distance),
                        BehaviorTree.ConditionNode(
                            name="MerchantWindowOpen",
                            condition_fn=_is_merchant_window_open,
                        ),
                        BT.SellInventoryItems(exclude_models=exclude_models, log=log),
                        BehaviorTree.SelectorNode(
                            name="OptionalDestroyZeroValueItems",
                            children=[
                                BehaviorTree.SequenceNode(
                                    name="DestroyZeroValueItemsWhenEnabled",
                                    children=[
                                        BehaviorTree.ConditionNode(
                                            name="DestroyZeroValueItemsEnabled",
                                            condition_fn=lambda: destroy_zero_value_items,
                                        ),
                                        BT.DestroyZeroValueItems(exclude_models=exclude_models, log=log),
                                    ],
                                ),
                                BehaviorTree.SucceederNode(
                                    name="SkipDestroyZeroValueItems",
                                ),
                            ],
                        ),
                    ],
                ),
                BehaviorTree.SequenceNode(
                    name="NoMerchantCleanupRequired",
                    children=[
                        BehaviorTree.ActionNode(
                            name="DebugMerchantCleanupStateNoCleanup",
                            action_fn=_debug_cleanup_state,
                            aftercast_ms=0,
                        ),
                        LogMessage("No merchant cleanup needed"),
                    ],
                ),
            ],
        )
    )


def merchant_cleanup(
    exclude_models: list[int] | None = None,
    destroy_zero_value_items: bool = True,
    target_distance: float = Range.Area.value,
) -> BehaviorTree:
    def _build(node: BehaviorTree.Node) -> BehaviorTree:
        merchant_coords = get_merchant_coords_from_map_id()
        if merchant_coords is None:
            return BehaviorTree(
                BehaviorTree.SucceederNode(
                    name="SkipMerchantCleanup",
                )
            )

        return MoveInteractAndSellItems(
            merchant_coords=merchant_coords,
            exclude_models=exclude_models,
            destroy_zero_value_items=destroy_zero_value_items,
            target_distance=target_distance,
            log=False,
        )

    return BehaviorTree(
        BehaviorTree.SubtreeNode(
            name="RuntimeMerchantCleanup",
            subtree_fn=_build,
        )
    )


def customize_weapon() -> BehaviorTree:
    def _click_customize_weapon_button(node: BehaviorTree.Node) -> BehaviorTree.NodeState:
        from Py4GWCoreLib.UIManager import UIManager

        frame_id = UIManager.GetFrameIDByCustomLabel(frame_label="Merchant.CustomizeWeaponButton")
        if frame_id == 0 or not UIManager.FrameExists(frame_id):
            return BehaviorTree.NodeState.FAILURE

        UIManager.FrameClick(frame_id)
        return BehaviorTree.NodeState.SUCCESS

    return BehaviorTree(
        BehaviorTree.SequenceNode(
            name="CustomizeWeapon",
            children=[
                LogMessage("Clicking customize weapon button"),
                BehaviorTree.ActionNode(
                    name="ClickCustomizeWeaponButton",
                    action_fn=_click_customize_weapon_button,
                    aftercast_ms=500,
                ),
            ],
        )
    )
