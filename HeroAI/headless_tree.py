from Py4GWCoreLib.Agent import Agent
from Py4GWCoreLib.GlobalCache import GLOBAL_CACHE
from Py4GWCoreLib.Map import Map
from Py4GWCoreLib.Player import Player
from Py4GWCoreLib.Routines import Routines
from Py4GWCoreLib.Builds.Any.HeroAI import HeroAI_Build
from Py4GWCoreLib.routines_src.BehaviourTrees import BehaviorTree
from Py4GWCoreLib import ActionQueueManager, LootConfig, Range, SharedCommandType, ThrottledTimer, Utils

from .cache_data import CacheData
from .follow.follower_runtime import (
    FollowExecutionState,
    execute_follower_follow,
    get_follow_destination_distance,
    is_follow_recovery_active,
)
from .settings import Settings
from .utils import DrawSharedMemoryFlags


class HeroAIHeadlessTree:
    """
    Headless HeroAI upkeep/combat tree.

    This keeps the non-UI parts of the HeroAI widget tree available to scripts
    without requiring the widget itself to be enabled.
    """

    def __init__(self, cached_data: CacheData | None = None, heroai_build: HeroAI_Build | None = None):
        self.cached_data = cached_data or CacheData()
        self.heroai_build = heroai_build or HeroAI_Build(self.cached_data)
        Settings().AutoCallTargets = True
        self._build_contract_map_signature: tuple[int, int, int, int] | None = None
        self._loot_throttle_check = ThrottledTimer(250)
        self._looting_node: BehaviorTree.ActionNode | None = None
        self._status_selector: BehaviorTree.SelectorNode | None = None
        self._follow_state = FollowExecutionState()
        self._headless_looting_enabled = True
        self.tree = self._build_tree()

    def _has_active_pick_up_loot_message(self) -> bool:
        account_email = Player.GetAccountEmail()
        index, message = GLOBAL_CACHE.ShMem.PreviewNextMessage(account_email)
        return bool(index != -1 and message and message.Command == SharedCommandType.PickUpLoot)

    def _consume_headless_looting_control_messages(self) -> None:
        account_email = str(Player.GetAccountEmail() or '').strip()
        if not account_email:
            return

        latest_enabled: bool | None = None
        for message_index, message in GLOBAL_CACHE.ShMem.GetAllMessages():
            if message is None:
                continue
            if not getattr(message, 'Active', False):
                continue
            if str(getattr(message, 'ReceiverEmail', '') or '').strip() != account_email:
                continue
            if int(getattr(message, 'Command', SharedCommandType.NoCommand)) != int(SharedCommandType.SetHeadlessLooting):
                continue
            latest_enabled = bool(int(getattr(message, 'Params', (1, 0, 0, 0))[0] or 0))
            GLOBAL_CACHE.ShMem.MarkMessageAsFinished(account_email, message_index)

        if latest_enabled is not None:
            self._headless_looting_enabled = latest_enabled

    def _is_looting_routine_active(self) -> bool:
        if not self._headless_looting_enabled:
            return False

        if self.cached_data.IsHeadlessCombatPauseActive():
            return False

        if not self._has_active_pick_up_loot_message():
            return False

        if self._loot_throttle_check.IsExpired():
            return False

        return True

    def _handle_looting(self) -> BehaviorTree.NodeState:
        if not self._headless_looting_enabled:
            self.cached_data.in_looting_routine = False
            return BehaviorTree.NodeState.FAILURE

        if is_follow_recovery_active(self.cached_data, self._follow_state):
            self.cached_data.in_looting_routine = False
            return BehaviorTree.NodeState.FAILURE

        if self.cached_data.IsHeadlessCombatPauseActive():
            self.cached_data.in_looting_routine = False
            return BehaviorTree.NodeState.FAILURE

        if self._has_active_pick_up_loot_message():
            self.cached_data.in_looting_routine = True
            if not Routines.Checks.Map.MapValid() or not Map.IsExplorable():
                self.cached_data.in_looting_routine = False
                return BehaviorTree.NodeState.FAILURE
            if GLOBAL_CACHE.Inventory.GetFreeSlotCount() <= 1:
                self.cached_data.in_looting_routine = False
                return BehaviorTree.NodeState.FAILURE
            if self._loot_throttle_check.IsExpired():
                self.cached_data.in_looting_routine = False
                return BehaviorTree.NodeState.FAILURE
            return BehaviorTree.NodeState.RUNNING

        if not Routines.Checks.Map.MapValid() or not Map.IsExplorable():
            self.cached_data.in_looting_routine = False
            return BehaviorTree.NodeState.FAILURE

        if GLOBAL_CACHE.Inventory.GetFreeSlotCount() <= 1:
            self.cached_data.in_looting_routine = False
            return BehaviorTree.NodeState.FAILURE

        loot_array = LootConfig().GetfilteredLootArray(
            Range.Earshot.value,
            multibox_loot=True,
            allow_unasigned_loot=False,
        )
        if len(loot_array) == 0:
            self.cached_data.in_looting_routine = False
            return BehaviorTree.NodeState.FAILURE

        account_email = Player.GetAccountEmail()
        self_account = GLOBAL_CACHE.ShMem.GetAccountDataFromEmail(account_email)
        if self_account:
            GLOBAL_CACHE.ShMem.SendMessage(
                self_account.AccountEmail,
                self_account.AccountEmail,
                SharedCommandType.PickUpLoot,
                (0, 0, 0, 0),
            )
            self._loot_throttle_check.Reset()
            self.cached_data.in_looting_routine = True
            return BehaviorTree.NodeState.RUNNING

        self.cached_data.in_looting_routine = False
        return BehaviorTree.NodeState.FAILURE

    def _handle_out_of_combat(self) -> bool:
        options = self.cached_data.account_options
        if not options or not options.Combat:
            return False

        if self.cached_data.IsHeadlessCombatPauseActive():
            return False

        if is_follow_recovery_active(self.cached_data, self._follow_state):
            return False

        player_agent_id = Player.GetAgentID()
        if self.cached_data.combat_handler.InCastingRoutine() or Agent.IsCasting(player_agent_id):
            return False

        self.heroai_build.set_cached_data(self.cached_data)
        next(self.heroai_build.ProcessOOC(), None)
        return self.heroai_build.DidTickSucceed()

    def _handle_combat(self) -> bool:
        options = self.cached_data.account_options
        if not options or not options.Combat:
            return False

        if is_follow_recovery_active(self.cached_data, self._follow_state):
            return False

        if not self.cached_data.IsHeadlessCombatPauseActive():
            return False

        self.heroai_build.set_cached_data(self.cached_data)
        next(self.heroai_build.ProcessCombat(), None)
        return self.heroai_build.DidTickSucceed()

    def _distance_to_destination(self) -> float:
        return get_follow_destination_distance(self.cached_data)

    def _is_user_interrupting(self) -> bool:
        return False

    def IsUserInterrupting(self) -> bool:
        return self._is_user_interrupting()

    def _follow(self) -> BehaviorTree.NodeState:
        return execute_follower_follow(self.cached_data, self._follow_state)

    def IsLootingActive(self) -> bool:
        return bool(self._headless_looting_enabled) and self._is_looting_routine_active()

    def IsLootingNodeRunning(self) -> bool:
        if self._looting_node is None:
            return False
        return self._looting_node.last_state == BehaviorTree.NodeState.RUNNING

    def SetLootingEnabled(self, enabled: bool) -> None:
        self._headless_looting_enabled = bool(enabled)

    def IsLootingEnabled(self) -> bool:
        return bool(self._headless_looting_enabled)

    def GetBuildContract(self):
        return self.heroai_build.GetBuildContract()

    def GetBuildContractName(self) -> str:
        contract_build = self.GetBuildContract()
        if contract_build is None:
            return ""
        return str(getattr(contract_build, "build_name", "") or contract_build.__class__.__name__)

    def initialize(self) -> bool:
        if not Routines.Checks.Map.MapValid():
            self.heroai_build.ClearBuildContract()
            self._build_contract_map_signature = None
            return False

        if not GLOBAL_CACHE.Party.IsPartyLoaded():
            return False

        if not Map.IsExplorable():
            self.heroai_build.ClearBuildContract()
            self._build_contract_map_signature = None
            return False

        if Map.IsInCinematic():
            return False

        self.heroai_build.set_cached_data(self.cached_data)
        map_signature = (
            int(Map.GetMapID()),
            int(Map.GetRegion()[0]),
            int(Map.GetDistrict()),
            int(Map.GetLanguage()[0]),
        )
        if self._build_contract_map_signature != map_signature:
            self.heroai_build.EnsureBuildContract(self.cached_data)
            self._build_contract_map_signature = map_signature

        self.cached_data.UpdateCombat()
        return True

    def update(self) -> None:
        self._consume_headless_looting_control_messages()
        self.cached_data.Update()

    def tick(self):
        self.update()
        try:
            DrawSharedMemoryFlags()
        except Exception:
            pass
        if self.initialize():
            return self.tree.tick()

        self.tree.reset()
        return BehaviorTree.NodeState.RUNNING

    def reset(self) -> None:
        self.tree.reset()
        self.heroai_build.ClearBuildContract()
        self._build_contract_map_signature = None
        self._follow_state = FollowExecutionState()

    def _build_tree(self):
        self._looting_node = BehaviorTree.ActionNode(
            name="LootingRoutine",
            action_fn=lambda: self._handle_looting() if self._headless_looting_enabled else BehaviorTree.NodeState.FAILURE,
        )
        self._status_selector = BehaviorTree.SelectorNode(
            name="HeadlessHeroAI_UpdateStatusSelector",
            children=[
                self._looting_node,
                BehaviorTree.ActionNode(
                    name="HandleOutOfCombat",
                    action_fn=lambda: (
                        BehaviorTree.NodeState.SUCCESS
                        if self._handle_out_of_combat()
                        else BehaviorTree.NodeState.FAILURE
                    ),
                ),
                BehaviorTree.ActionNode(
                    name="Follow",
                    action_fn=lambda: self._follow(),
                ),
                BehaviorTree.ActionNode(
                    name="HandleCombat",
                    action_fn=lambda: (
                        self.cached_data.auto_attack_timer.Reset()
                        or BehaviorTree.NodeState.SUCCESS
                        if self._handle_combat()
                        else BehaviorTree.NodeState.FAILURE
                    ),
                ),
            ],
        )

        global_guard = BehaviorTree.SequenceNode(
            name="HeadlessHeroAI_GlobalGuard",
            children=[
                BehaviorTree.ConditionNode(
                    name="IsAlive",
                    condition_fn=lambda: Agent.IsAlive(Player.GetAgentID()),
                ),
                BehaviorTree.ConditionNode(
                    name="DistanceSafe",
                    condition_fn=lambda: (
                        self._distance_to_destination() < Range.SafeCompass.value
                        or is_follow_recovery_active(self.cached_data, self._follow_state)
                    ),
                ),
                BehaviorTree.ConditionNode(
                    name="NotKnockedDown",
                    condition_fn=lambda: not Agent.IsKnockedDown(Player.GetAgentID()),
                ),
            ],
        )

        casting_block = BehaviorTree.ConditionNode(
            name="IsCasting",
            condition_fn=lambda: (
                BehaviorTree.NodeState.RUNNING
                if (
                    (
                        self.cached_data.combat_handler.InCastingRoutine()
                        and not is_follow_recovery_active(self.cached_data, self._follow_state)
                    )
                    or Agent.IsCasting(Player.GetAgentID())
                )
                else BehaviorTree.NodeState.SUCCESS
            ),
        )

        return BehaviorTree.SequenceNode(
            name="HeadlessHeroAI_Main_BT",
            children=[
                global_guard,
                casting_block,
                self._status_selector,
            ],
        )
