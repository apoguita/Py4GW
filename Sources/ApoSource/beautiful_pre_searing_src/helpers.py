from Sources.ApoSource.beautiful_pre_searing_src.globals import *


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
    return None


def get_exit_map_coords_from_map_id() -> tuple[list[Vec2f], int] | None:
    from Py4GWCoreLib.Map import Map

    current_map_id = Map.GetMapID()
    if current_map_id == ASCALON_CITY_MAP_ID:
        return [EXIT_ASCALON_CITY_COORDS], LAKESIDE_COUNTY_MAP_ID
    if current_map_id == ASHFORD_ABBEY_MAP_ID:
        return EXIT_TO_LAKESIDE_COUNTY_COORDS, LAKESIDE_COUNTY_MAP_ID
    if current_map_id == FOIBLES_FAIR_MAP_ID:
        return GO_TO_WIZARDS_FOLLY_EXIT_COORDS, WIZARDS_FOLLY_MAP_ID
    return None


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


def exit_current_map() -> BehaviorTree:
    def _build(node: BehaviorTree.Node) -> BehaviorTree:
        exit_data = get_exit_map_coords_from_map_id()
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

    return BehaviorTree(
        BehaviorTree.SelectorNode(
            name="MoveInteractAndSellItems",
            children=[
                BehaviorTree.SequenceNode(
                    name="MerchantCleanupRequired",
                    children=[
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
                LogMessage("No merchant cleanup needed"),
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
