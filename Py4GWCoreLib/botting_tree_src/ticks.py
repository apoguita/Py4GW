import Py4GW

from ..GlobalCache import GLOBAL_CACHE
from ..Routines import Routines
from ..py4gwcorelib_src.BehaviorTree import BehaviorTree
from .enums import HeroAIStatus, PlannerStatus


class BottingTreeTicksMixin:
    def _tick_heroai(self, node: BehaviorTree.Node) -> BehaviorTree.NodeState:
        bb = node.blackboard
        requested_isolation = bb.pop('account_isolation_enabled_request', None)
        if isinstance(requested_isolation, bool):
            self.SetIsolationEnabled(requested_isolation)
        bb['account_isolation_enabled'] = self.IsIsolationEnabled()

        requested_enabled = bb.pop('headless_heroai_enabled_request', None)
        requested_reset_runtime = bool(bb.pop('headless_heroai_reset_runtime_request', True))
        if isinstance(requested_enabled, bool):
            self.SetHeadlessHeroAIEnabled(requested_enabled, reset_runtime=requested_reset_runtime)
        bb['headless_heroai_enabled'] = self.IsHeadlessHeroAIEnabled()

        requested_looting_enabled = bb.pop('looting_enabled_request', None)
        if isinstance(requested_looting_enabled, bool):
            self.SetLootingEnabled(requested_looting_enabled)
        bb['looting_enabled'] = self.IsLootingEnabled()

        requested_pause_on_combat = bb.pop('pause_on_combat_request', None)
        if isinstance(requested_pause_on_combat, bool):
            self.pause_on_combat = requested_pause_on_combat
        bb['pause_on_combat'] = self.pause_on_combat

        if not self.started or self.paused:
            bb['COMBAT_ACTIVE'] = False
            bb['LOOTING_ACTIVE'] = False
            bb['PAUSE_MOVEMENT'] = False
            bb['HEROAI_SUCCESS'] = False
            return BehaviorTree.NodeState.RUNNING

        if not self.IsHeadlessHeroAIEnabled():
            if self._should_log_heroai_state('disabled'):
                Py4GW.Console.Log('BottingTree', 'Headless HeroAI is disabled.', Py4GW.Console.MessageType.Info)
            self._last_heroai_state = 'disabled'
            bb['COMBAT_ACTIVE'] = False
            bb['LOOTING_ACTIVE'] = False
            bb['PAUSE_MOVEMENT'] = False
            bb['HEROAI_STATUS'] = HeroAIStatus.DISABLED.value
            bb['HEROAI_SUCCESS'] = False
            self.headless_heroai.reset()
            return BehaviorTree.NodeState.RUNNING

        self._disable_heroai_widget_for_headless()
        self.EnsureHeroAIOptionsEnabled()

        if Routines.Checks.Map.IsLoading() or not Routines.Checks.Map.IsExplorable():
            if self._should_log_heroai_state('waiting_map'):
                Py4GW.Console.Log('BottingTree', 'HeroAI waiting for combat-ready map.', Py4GW.Console.MessageType.Info)
            self._last_heroai_state = 'waiting_map'
            bb['COMBAT_ACTIVE'] = False
            bb['LOOTING_ACTIVE'] = False
            bb['PAUSE_MOVEMENT'] = False
            bb['HEROAI_STATUS'] = HeroAIStatus.WAITING_MAP.value
            bb['HEROAI_SUCCESS'] = False
            self.headless_heroai.reset()
            return BehaviorTree.NodeState.RUNNING

        if Routines.Checks.Player.IsDead():
            if self._should_log_heroai_state('player_dead'):
                Py4GW.Console.Log('BottingTree', 'HeroAI paused because player is dead.', Py4GW.Console.MessageType.Warning)
            self._last_heroai_state = 'player_dead'
            bb['COMBAT_ACTIVE'] = False
            bb['LOOTING_ACTIVE'] = False
            bb['PAUSE_MOVEMENT'] = False
            bb['HEROAI_STATUS'] = HeroAIStatus.PLAYER_DEAD.value
            bb['HEROAI_SUCCESS'] = False
            return BehaviorTree.NodeState.RUNNING

        if Routines.Checks.Player.IsKnockedDown():
            if self._should_log_heroai_state('knocked_down'):
                Py4GW.Console.Log('BottingTree', 'HeroAI paused because player is knocked down.', Py4GW.Console.MessageType.Warning)
            self._last_heroai_state = 'knocked_down'
            bb['COMBAT_ACTIVE'] = bool(self.headless_heroai.cached_data.data.in_aggro)
            bb['LOOTING_ACTIVE'] = False
            bb['PAUSE_MOVEMENT'] = False
            bb['HEROAI_STATUS'] = HeroAIStatus.PLAYER_KNOCKED_DOWN.value
            bb['HEROAI_SUCCESS'] = False
            return BehaviorTree.NodeState.RUNNING

        self.headless_heroai.tick()
        bb['USER_INTERRUPT_ACTIVE'] = self.headless_heroai.IsUserInterrupting()
        bb['LOOTING_ACTIVE'] = self.headless_heroai.IsLootingActive()
        bb['PAUSE_MOVEMENT'] = bool(bb['LOOTING_ACTIVE'] or bb['USER_INTERRUPT_ACTIVE'])

        if self.headless_heroai.cached_data.data.in_aggro:
            if self._last_heroai_state != 'combat':
                self._last_heroai_state = 'combat'
            bb['COMBAT_ACTIVE'] = True
            bb['HEROAI_STATUS'] = HeroAIStatus.COMBAT_TICK.value
        else:
            if self._last_heroai_state != 'ooc':
                self._last_heroai_state = 'ooc'
            bb['COMBAT_ACTIVE'] = False
            bb['HEROAI_STATUS'] = HeroAIStatus.OOC_TICK.value

        bb['HEROAI_SUCCESS'] = bool(self.headless_heroai.heroai_build.DidTickSucceed())
        return BehaviorTree.NodeState.RUNNING

    def _tick_planner(self, node: BehaviorTree.Node) -> BehaviorTree.NodeState:
        bb = node.blackboard

        if not self.started or self.paused:
            bb['PLANNER_STATUS'] = PlannerStatus.IDLE.value
            bb['PLANNER_OWNER'] = PlannerStatus.OWNER_PLANNER.value
            return BehaviorTree.NodeState.RUNNING

        if Routines.Checks.Party.IsPartyWiped() or GLOBAL_CACHE.Party.IsPartyDefeated():
            bb['PLANNER_STATUS'] = 'PAUSED: Party wipe recovery'
            bb['PLANNER_OWNER'] = PlannerStatus.OWNER_PLANNER.value
            return BehaviorTree.NodeState.RUNNING

        if bb.get('COMBAT_ACTIVE', False) and self.pause_on_combat:
            if self._last_planner_gate_state != 'paused_on_combat':
                self._last_planner_gate_state = 'paused_on_combat'
            bb['PLANNER_STATUS'] = PlannerStatus.PAUSED_ON_COMBAT.value
            bb['PLANNER_OWNER'] = PlannerStatus.OWNER_HEROAI.value
        elif bb.get('LOOTING_ACTIVE', False):
            if self._last_planner_gate_state != 'paused_on_looting':
                self._last_planner_gate_state = 'paused_on_looting'
            bb['PLANNER_STATUS'] = PlannerStatus.PAUSED_ON_LOOTING.value
            bb['PLANNER_OWNER'] = PlannerStatus.OWNER_HEROAI.value

        if self.planner_tree is None:
            if self._last_planner_gate_state != 'idle_no_planner':
                Py4GW.Console.Log('BottingTree', 'Planner tree is not set; planner idling.', Py4GW.Console.MessageType.Warning)
                self._last_planner_gate_state = 'idle_no_planner'
            bb['PLANNER_STATUS'] = PlannerStatus.IDLE.value
            bb['PLANNER_OWNER'] = PlannerStatus.OWNER_PLANNER.value
            return BehaviorTree.NodeState.RUNNING

        self._last_planner_gate_state = 'planner_tick'
        bb['PLANNER_STATUS'] = PlannerStatus.TICK.value
        bb['PLANNER_OWNER'] = PlannerStatus.OWNER_PLANNER.value
        self.planner_tree.blackboard = bb
        planner_result = BehaviorTree.Node._normalize_state(self.planner_tree.tick())
        if planner_result is None:
            raise TypeError('Planner tree returned a non-NodeState result.')
        if planner_result == BehaviorTree.NodeState.SUCCESS:
            Py4GW.Console.Log('BottingTree', 'Planner tree completed.', Py4GW.Console.MessageType.Success)
            bb['PLANNER_STATUS'] = 'PLANNER: Completed'
            bb['PLANNER_OWNER'] = PlannerStatus.OWNER_PLANNER.value
            self.started = False
            self.paused = False
            self.RestoreAccountIsolation()
        elif planner_result == BehaviorTree.NodeState.FAILURE:
            Py4GW.Console.Log('BottingTree', 'Planner tree failed.', Py4GW.Console.MessageType.Warning)
            bb['PLANNER_STATUS'] = 'PLANNER: Failed'
            bb['PLANNER_OWNER'] = PlannerStatus.OWNER_PLANNER.value
            self.started = False
            self.paused = False
            self.RestoreAccountIsolation()
        return BehaviorTree.NodeState.RUNNING

    def _tick_service_tree(self, node: BehaviorTree.Node, service_tree: BehaviorTree, service_name: str) -> BehaviorTree.NodeState:
        if not self.started or self.paused:
            return BehaviorTree.NodeState.RUNNING

        service_tree.blackboard = node.blackboard
        service_result = BehaviorTree.Node._normalize_state(service_tree.tick())
        if service_result is None:
            raise TypeError(f"Service tree '{service_name}' returned a non-NodeState result.")
        if service_result in (BehaviorTree.NodeState.SUCCESS, BehaviorTree.NodeState.FAILURE):
            Py4GW.Console.Log(
                'BottingTree',
                f"Upkeep tree '{service_name}' returned {service_result.name}.",
                Py4GW.Console.MessageType.Info if service_result == BehaviorTree.NodeState.SUCCESS else Py4GW.Console.MessageType.Warning,
            )
        if service_result in (BehaviorTree.NodeState.SUCCESS, BehaviorTree.NodeState.FAILURE):
            service_tree.reset()
        return BehaviorTree.NodeState.RUNNING
