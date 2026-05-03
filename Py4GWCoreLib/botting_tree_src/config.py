from typing import TYPE_CHECKING

from ..py4gwcorelib_src.BehaviorTree import BehaviorTree
from ..routines_src.BehaviourTrees import BT as RoutinesBT

if TYPE_CHECKING:
    from ..BottingTree import BottingTree


class _BottingTreeConfig:
    def __init__(self, parent: 'BottingTree'):
        self.parent = parent

    @staticmethod
    def _request_template_state(
        *,
        name: str,
        hero_ai: bool,
        looting: bool,
        isolation: bool,
        pause_on_combat: bool,
        reset_hero_ai: bool = True,
    ) -> BehaviorTree:
        state = {'requested': False}
        request_keys = (
            'headless_heroai_enabled_request',
            'headless_heroai_reset_runtime_request',
            'looting_enabled_request',
            'account_isolation_enabled_request',
            'pause_on_combat_request',
        )

        def _apply_template(node: BehaviorTree.Node) -> BehaviorTree.NodeState:
            if state['requested']:
                if any(key in node.blackboard for key in request_keys):
                    return BehaviorTree.NodeState.RUNNING
                state['requested'] = False
                return BehaviorTree.NodeState.SUCCESS

            node.blackboard['headless_heroai_enabled_request'] = bool(hero_ai)
            node.blackboard['headless_heroai_reset_runtime_request'] = bool(reset_hero_ai)
            node.blackboard['looting_enabled_request'] = bool(looting)
            node.blackboard['account_isolation_enabled_request'] = bool(isolation)
            node.blackboard['pause_on_combat_request'] = bool(pause_on_combat)
            node.blackboard['botting_tree_template'] = name
            state['requested'] = True
            return BehaviorTree.NodeState.RUNNING

        return BehaviorTree(
            BehaviorTree.ActionNode(
                name=name,
                action_fn=_apply_template,
                aftercast_ms=0,
            )
        )

    def PacifistTree(
        self,
        *,
        account_isolation: bool = True,
        reset_hero_ai: bool = True,
        name: str = 'ConfigurePacifistEnv',
    ) -> BehaviorTree:
        return self._request_template_state(
            name=name,
            hero_ai=False,
            looting=False,
            isolation=account_isolation,
            pause_on_combat=False,
            reset_hero_ai=reset_hero_ai,
        )

    def PacifistForceHeroAITree(
        self,
        *,
        reset_hero_ai: bool = True,
        name: str = 'ConfigurePacifistForceHeroAIEnv',
    ) -> BehaviorTree:
        return self.PacifistTree(
            account_isolation=False,
            reset_hero_ai=reset_hero_ai,
            name=name,
        )

    def AggressiveTree(
        self,
        *,
        pause_on_danger: bool = True,
        account_isolation: bool = True,
        auto_loot: bool = True,
        reset_hero_ai: bool = True,
        name: str = 'ConfigureAggressiveEnv',
    ) -> BehaviorTree:
        return self._request_template_state(
            name=name,
            hero_ai=True,
            looting=auto_loot,
            isolation=account_isolation,
            pause_on_combat=pause_on_danger,
            reset_hero_ai=reset_hero_ai,
        )

    def AggressiveForceHeroAITree(
        self,
        *,
        pause_on_danger: bool = True,
        auto_loot: bool = True,
        reset_hero_ai: bool = True,
        name: str = 'ConfigureAggressiveForceHeroAIEnv',
    ) -> BehaviorTree:
        return self.AggressiveTree(
            pause_on_danger=pause_on_danger,
            account_isolation=False,
            auto_loot=auto_loot,
            reset_hero_ai=reset_hero_ai,
            name=name,
        )

    def MultiboxAggressiveTree(
        self,
        *,
        auto_loot: bool = True,
        reset_hero_ai: bool = True,
        name: str = 'ConfigureMultiboxAggressiveEnv',
    ) -> BehaviorTree:
        return self.AggressiveTree(
            pause_on_danger=True,
            account_isolation=False,
            auto_loot=auto_loot,
            reset_hero_ai=reset_hero_ai,
            name=name,
        )

    def Pacifist(self, **kwargs) -> BehaviorTree:
        return self.PacifistTree(**kwargs)

    def PacifistForceHeroAI(self, **kwargs) -> BehaviorTree:
        return self.PacifistForceHeroAITree(**kwargs)

    def Aggressive(self, **kwargs) -> BehaviorTree:
        return self.AggressiveTree(**kwargs)

    def AggressiveForceHeroAI(self, **kwargs) -> BehaviorTree:
        return self.AggressiveForceHeroAITree(**kwargs)

    def Multibox_Aggressive(self, **kwargs) -> BehaviorTree:
        return self.MultiboxAggressiveTree(**kwargs)

    ConfigurePacifistEnv = Pacifist
    ConfigureAggressiveEnv = Aggressive

    def ConfigureUpkeepTrees(
        self,
        *,
        disable_looting: bool = True,
        restore_isolation_on_stop: bool = True,
        enable_outpost_imp_service: bool = True,
        enable_explorable_imp_service: bool = True,
        imp_target_bag: int = 1,
        imp_slot: int = 0,
        imp_log: bool = False,
        enable_party_wipe_recovery: bool = True,
        party_wipe_default_step_name: str | None = None,
        party_wipe_return_interval_ms: float = 1000.0,
    ) -> 'BottingTree':
        upkeep_steps: list[tuple[str, object]] = []

        if disable_looting:
            self.parent.DisableLooting()
        else:
            self.parent.EnableLooting()

        self.parent.SetRestoreIsolationOnStop(restore_isolation_on_stop)

        if enable_outpost_imp_service:
            upkeep_steps.append(
                (
                    'OutpostImpService',
                    lambda: RoutinesBT.Upkeepers.OutpostImpService(
                        target_bag=imp_target_bag,
                        slot=imp_slot,
                        log=imp_log,
                    ),
                )
            )

        if enable_explorable_imp_service:
            upkeep_steps.append(
                (
                    'ExplorableImpService',
                    lambda: RoutinesBT.Upkeepers.ExplorableImpService(
                        log=imp_log,
                    ),
                )
            )

        self.parent.SetUpkeepTrees(upkeep_steps)

        if enable_party_wipe_recovery:
            default_step_name = party_wipe_default_step_name
            if default_step_name is None:
                planner_steps = self.parent.GetNamedPlannerStepNames()
                default_step_name = planner_steps[0] if planner_steps else None
            self.parent.AddPartyWipeRecoveryService(
                default_step_name=default_step_name,
                return_interval_ms=party_wipe_return_interval_ms,
            )

        return self.parent

    def ConfigureUpkeepTreesTree(
        self,
        *,
        disable_looting: bool = True,
        restore_isolation_on_stop: bool = True,
        enable_outpost_imp_service: bool = True,
        enable_explorable_imp_service: bool = True,
        imp_target_bag: int = 1,
        imp_slot: int = 0,
        imp_log: bool = False,
        enable_party_wipe_recovery: bool = True,
        party_wipe_default_step_name: str | None = None,
        party_wipe_return_interval_ms: float = 1000.0,
        name: str = 'ConfigureUpkeepTrees',
    ) -> BehaviorTree:
        def _configure(_node: BehaviorTree.Node) -> BehaviorTree.NodeState:
            self.ConfigureUpkeepTrees(
                disable_looting=disable_looting,
                restore_isolation_on_stop=restore_isolation_on_stop,
                enable_outpost_imp_service=enable_outpost_imp_service,
                enable_explorable_imp_service=enable_explorable_imp_service,
                imp_target_bag=imp_target_bag,
                imp_slot=imp_slot,
                imp_log=imp_log,
                enable_party_wipe_recovery=enable_party_wipe_recovery,
                party_wipe_default_step_name=party_wipe_default_step_name,
                party_wipe_return_interval_ms=party_wipe_return_interval_ms,
            )
            return BehaviorTree.NodeState.SUCCESS

        return BehaviorTree(
            BehaviorTree.ActionNode(
                name=name,
                action_fn=_configure,
                aftercast_ms=0,
            )
        )
