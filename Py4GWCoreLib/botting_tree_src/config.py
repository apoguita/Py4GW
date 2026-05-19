from typing import Callable
from typing import Optional
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
        isolation: bool,
        multi_account: Optional[bool] = None,
        looting: Optional[bool] = None,
        pause_on_combat: Optional[bool] = None,
        reset_hero_ai: bool = True,
    ) -> BehaviorTree:
        state = {'requested': False}
        request_keys = (
            'multi_account_request',
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

            if multi_account is not None:
                node.blackboard['multi_account_request'] = bool(multi_account)
            node.blackboard['headless_heroai_enabled_request'] = bool(hero_ai)
            node.blackboard['headless_heroai_reset_runtime_request'] = bool(reset_hero_ai)
            if looting is not None:
                node.blackboard['looting_enabled_request'] = bool(looting)
            node.blackboard['account_isolation_enabled_request'] = bool(isolation)
            if pause_on_combat is not None:
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
        account_isolation: Optional[bool] = None,
        multi_account: Optional[bool] = None,
        reset_hero_ai: bool = True,
        pause_on_danger: Optional[bool] = None,
        auto_loot: bool = True,
        name: str = 'ConfigurePacifistEnv',
    ) -> BehaviorTree:
        resolved_isolation = bool(account_isolation) if account_isolation is not None else not bool(multi_account)
        return self._request_template_state(
            name=name,
            hero_ai=False,
            isolation=resolved_isolation,
            multi_account=multi_account,
            reset_hero_ai=reset_hero_ai,
            pause_on_combat=pause_on_danger,
            looting=auto_loot,
        )

    def PacifistForceHeroAITree(
        self,
        *,
        pause_on_danger: Optional[bool] = None,
        auto_loot: bool = True,
        reset_hero_ai: bool = True,
        name: str = 'ConfigurePacifistForceHeroAIEnv',
    ) -> BehaviorTree:
        return self._request_template_state(
            name=name,
            hero_ai=True,
            isolation=False,
            looting=auto_loot,
            pause_on_combat=pause_on_danger,
            reset_hero_ai=reset_hero_ai,
        )

    def AggressiveTree(
        self,
        *,
        pause_on_danger: Optional[bool] = None,
        account_isolation: Optional[bool] = None,
        multi_account: Optional[bool] = None,
        auto_loot: Optional[bool] = None,
        reset_hero_ai: bool = True,
        name: str = 'ConfigureAggressiveEnv',
    ) -> BehaviorTree:
        resolved_isolation = bool(account_isolation) if account_isolation is not None else not bool(multi_account)
        return self._request_template_state(
            name=name,
            hero_ai=True,
            isolation=resolved_isolation,
            multi_account=multi_account,
            looting=auto_loot,
            pause_on_combat=pause_on_danger,
            reset_hero_ai=reset_hero_ai,
        )

    def AggressiveForceHeroAITree(
        self,
        *,
        pause_on_danger: Optional[bool] = None,
        auto_loot: bool = True,
        reset_hero_ai: bool = True,
        name: str = 'ConfigureAggressiveForceHeroAIEnv',
    ) -> BehaviorTree:
        return self._request_template_state(
            name=name,
            hero_ai=True,
            isolation=False,
            looting=auto_loot,
            pause_on_combat=pause_on_danger,
            reset_hero_ai=reset_hero_ai,
        )

    def MultiboxAggressiveTree(
        self,
        *,
        auto_loot: bool = True,
        reset_hero_ai: bool = True,
        pause_on_danger: Optional[bool] = None,
        name: str = 'ConfigureMultiboxAggressiveEnv',
    ) -> BehaviorTree:
        return self._request_template_state(
            name=name,
            hero_ai=True,
            isolation=False,
            multi_account=True,
            looting=auto_loot,
            pause_on_combat=pause_on_danger,
            reset_hero_ai=reset_hero_ai,
        )

    def Pacifist(
        self,
        *,
        account_isolation: Optional[bool] = None,
        multi_account: Optional[bool] = None,
        reset_hero_ai: bool = True,
        pause_on_danger: bool = False,
        auto_loot: bool = True,
    ) -> BehaviorTree:
        return self.PacifistTree(
            account_isolation=account_isolation,
            multi_account=multi_account,
            reset_hero_ai=reset_hero_ai,
            pause_on_danger=pause_on_danger,
            auto_loot=auto_loot,
        )

    def PacifistForceHeroAI(
        self,
        *,
        reset_hero_ai: bool = True,
        pause_on_danger: Optional[bool] = None,
        auto_loot: bool = True,
    ) -> BehaviorTree:
        return self.PacifistForceHeroAITree(
            reset_hero_ai=reset_hero_ai,
            pause_on_danger=pause_on_danger,
            auto_loot=auto_loot,
        )

    def Aggressive(
        self,
        *,
        pause_on_danger: bool = True,
        account_isolation: Optional[bool] = None,
        multi_account: Optional[bool] = None,
        auto_loot: bool = True,
        reset_hero_ai: bool = True,
    ) -> BehaviorTree:
        return self.AggressiveTree(
            pause_on_danger=pause_on_danger,
            account_isolation=account_isolation,
            multi_account=multi_account,
            auto_loot=auto_loot,
            reset_hero_ai=reset_hero_ai,
        )

    def AggressiveForceHeroAI(
        self,
        *,
        pause_on_danger: Optional[bool] = None,
        auto_loot: bool = True,
        reset_hero_ai: bool = True,
    ) -> BehaviorTree:
        return self.AggressiveForceHeroAITree(
            pause_on_danger=pause_on_danger,
            auto_loot=auto_loot,
            reset_hero_ai=reset_hero_ai,
        )

    def Multibox_Aggressive(
        self,
        *,
        pause_on_danger: Optional[bool] = None,
        auto_loot: bool = True,
        reset_hero_ai: bool = True,
    ) -> BehaviorTree:
        return self.MultiboxAggressiveTree(
            pause_on_danger=pause_on_danger,
            auto_loot=auto_loot,
            reset_hero_ai=reset_hero_ai,
        )

    ConfigurePacifistEnv = Pacifist
    ConfigureAggressiveEnv = Aggressive

    @staticmethod
    def _consumable_upkeep_steps(model_id: int) -> list[tuple[str, object]]:
        model_id = int(model_id)
        return [
            (
                f'ConsumableService:{model_id}',
                lambda model_id=model_id: RoutinesBT.Upkeepers.ConsumableService(model_id),
            )
        ]

    def ConfigureUpkeep(
        self,
        *,
        disable_looting: bool = False,
        restore_isolation_on_stop: bool = True,
        enable_outpost_imp_service: bool = False,
        enable_explorable_imp_service: bool = False,
        imp_target_bag: int = 1,
        imp_slot: int = 0,
        imp_log: bool = False,
        consumable_upkeeps: list[int] | tuple[int, ...] | None = None,
        enable_party_wipe_recovery: bool = True,
        party_wipe_default_step_name: str | None = None,
        party_wipe_return_interval_ms: float = 1000.0,
        heroai_state_logging: bool = True,
        heroai_state_log_interval_ms: int = 5000,
    ) -> 'BottingTree':
        upkeep_steps: list[tuple[str, object]] = []

        if disable_looting:
            self.parent.DisableLooting()
        else:
            self.parent.EnableLooting()

        self.parent.SetRestoreIsolationOnStop(restore_isolation_on_stop)
        self.parent.SetHeroAIStateLogging(
            enabled=heroai_state_logging,
            interval_ms=heroai_state_log_interval_ms,
        )

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

        for consumable_spec in consumable_upkeeps or ():
            upkeep_steps.extend(self._consumable_upkeep_steps(consumable_spec))

        self.parent.SetUpkeepTrees(upkeep_steps)

        if enable_party_wipe_recovery:
            default_step_name: str | Callable[[], str | None] | None = party_wipe_default_step_name
            if default_step_name is None:
                default_step_name = lambda: (self.parent.GetNamedPlannerStepNames() or [None])[0]
            self.parent.EnsurePartyWipeRecoveryService(
                default_step_name=default_step_name,
                return_interval_ms=party_wipe_return_interval_ms,
            )

        return self.parent

    def ConfigureUpkeepNode(
        self,
        *,
        disable_looting: bool = True,
        restore_isolation_on_stop: bool = True,
        enable_outpost_imp_service: bool = True,
        enable_explorable_imp_service: bool = True,
        imp_target_bag: int = 1,
        imp_slot: int = 0,
        imp_log: bool = False,
        consumable_upkeeps: list[int] | tuple[int, ...] | None = None,
        enable_party_wipe_recovery: bool = True,
        party_wipe_default_step_name: str | None = None,
        party_wipe_return_interval_ms: float = 1000.0,
        heroai_state_logging: bool = True,
        heroai_state_log_interval_ms: int = 5000,
        name: str = 'ConfigureUpkeep',
    ) -> BehaviorTree:
        def _configure(_node: BehaviorTree.Node) -> BehaviorTree.NodeState:
            self.ConfigureUpkeep(
                disable_looting=disable_looting,
                restore_isolation_on_stop=restore_isolation_on_stop,
                enable_outpost_imp_service=enable_outpost_imp_service,
                enable_explorable_imp_service=enable_explorable_imp_service,
                imp_target_bag=imp_target_bag,
                imp_slot=imp_slot,
                imp_log=imp_log,
                consumable_upkeeps=consumable_upkeeps,
                enable_party_wipe_recovery=enable_party_wipe_recovery,
                party_wipe_default_step_name=party_wipe_default_step_name,
                party_wipe_return_interval_ms=party_wipe_return_interval_ms,
                heroai_state_logging=heroai_state_logging,
                heroai_state_log_interval_ms=heroai_state_log_interval_ms,
            )
            return BehaviorTree.NodeState.SUCCESS

        return BehaviorTree(
            BehaviorTree.ActionNode(
                name=name,
                action_fn=_configure,
                aftercast_ms=0,
            )
        )
