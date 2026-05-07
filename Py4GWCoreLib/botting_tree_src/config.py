from collections.abc import Mapping
from collections.abc import Sequence
from typing import Any
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
        looting: Optional[bool] = None,
        pause_on_combat: Optional[bool] = None,
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
        account_isolation: bool = True,
        reset_hero_ai: bool = True,
        pause_on_danger: Optional[bool] = None,
        auto_loot: Optional[bool] = None,
        name: str = 'ConfigurePacifistEnv',
    ) -> BehaviorTree:
        return self._request_template_state(
            name=name,
            hero_ai=False,
            isolation=account_isolation,
            reset_hero_ai=reset_hero_ai,
            pause_on_combat=pause_on_danger,
            looting=auto_loot,
        )

    def PacifistForceHeroAITree(
        self,
        *,
        pause_on_danger: Optional[bool] = None,
        auto_loot: Optional[bool] = None,
        reset_hero_ai: bool = True,
        name: str = 'ConfigurePacifistForceHeroAIEnv',
    ) -> BehaviorTree:
        return self.PacifistTree(
            pause_on_danger=pause_on_danger,
            auto_loot=auto_loot,
            account_isolation=False,
            reset_hero_ai=reset_hero_ai,
            name=name,
        )

    def AggressiveTree(
        self,
        *,
        pause_on_danger: Optional[bool] = None,
        account_isolation: bool = True,
        auto_loot: Optional[bool] = None,
        reset_hero_ai: bool = True,
        name: str = 'ConfigureAggressiveEnv',
    ) -> BehaviorTree:
        return self._request_template_state(
            name=name,
            hero_ai=True,
            isolation=account_isolation,
            looting=auto_loot,
            pause_on_combat=pause_on_danger,
            reset_hero_ai=reset_hero_ai,
        )

    def AggressiveForceHeroAITree(
        self,
        *,
        pause_on_danger: Optional[bool] = None,
        auto_loot: Optional[bool] = None,
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
        auto_loot: Optional[bool] = None,
        reset_hero_ai: bool = True,
        pause_on_danger: Optional[bool] = None,
        name: str = 'ConfigureMultiboxAggressiveEnv',
    ) -> BehaviorTree:
        return self.AggressiveTree(
            pause_on_danger=pause_on_danger,
            account_isolation=False,
            auto_loot=auto_loot,
            reset_hero_ai=reset_hero_ai,
            name=name,
        )

    def Pacifist(
        self,
        *,
        account_isolation: bool = True,
        reset_hero_ai: bool = True,
        pause_on_danger: bool = False,
        auto_loot: Optional[bool] = None,
    ) -> BehaviorTree:
        return self.PacifistTree(
            account_isolation=account_isolation,
            reset_hero_ai=reset_hero_ai,
            pause_on_danger=pause_on_danger,
            auto_loot=auto_loot,
        )

    def PacifistForceHeroAI(
        self,
        *,
        reset_hero_ai: bool = True,
        pause_on_danger: Optional[bool] = None,
        auto_loot: Optional[bool] = None,
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
        account_isolation: bool = True,
        auto_loot: Optional[bool] = None,
        reset_hero_ai: bool = True,
    ) -> BehaviorTree:
        return self.AggressiveTree(
            pause_on_danger=pause_on_danger,
            account_isolation=account_isolation,
            auto_loot=auto_loot,
            reset_hero_ai=reset_hero_ai,
        )

    def AggressiveForceHeroAI(
        self,
        *,
        pause_on_danger: Optional[bool] = None,
        auto_loot: Optional[bool] = None,
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
        auto_loot: Optional[bool] = None,
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
    def _consumable_upkeep_steps(spec: str | Mapping[str, Any]) -> list[tuple[str, object]]:
        if isinstance(spec, str):
            return [
                (
                    f'ConsumableService:{spec}',
                    lambda spec=spec: RoutinesBT.Upkeepers.ConsumableService(spec),
                )
            ]

        raw_model_id = spec.get('key', spec.get('model_id', spec.get('modelID_or_encStr')))
        if raw_model_id is None:
            raise ValueError('Consumable upkeep spec requires model_id.')
        model_id = raw_model_id if isinstance(raw_model_id, str) else int(raw_model_id)

        effect_name = str(spec.get('effect_name', '') or '')
        name = str(spec.get('name', '') or f'ConsumableService:{model_id}')
        target_morale = spec.get('target_morale')
        target_alcohol_level = spec.get('target_alcohol_level')
        raw_effect_ids = spec.get('effect_ids', [])
        effect_ids = (
            [int(value) for value in raw_effect_ids]
            if isinstance(raw_effect_ids, Sequence) and not isinstance(raw_effect_ids, (str, bytes))
            else []
        )

        def _build_tree() -> BehaviorTree:
            return RoutinesBT.Upkeepers.ConsumableService(
                model_id,
                effect_name,
                effect_id=int(spec.get('effect_id', 0) or 0),
                effect_ids=effect_ids,
                require_effect_id=bool(spec.get('require_effect_id', False)),
                use_where=str(spec.get('use_where', 'explorable') or 'explorable'),
                target_morale=int(target_morale) if target_morale is not None else None,
                party_wide_morale=bool(spec.get('party_wide_morale', False)),
                target_alcohol_level=int(target_alcohol_level) if target_alcohol_level is not None else None,
                blocked_effect_id=int(spec.get('blocked_effect_id', 0) or 0),
                fallback_duration_ms=int(spec.get('fallback_duration_ms', 0) or 0),
                check_interval_ms=int(spec.get('check_interval_ms', 1000) or 1000),
                aftercast_ms=int(spec.get('aftercast_ms', 500) or 500),
            )

        return [(name, _build_tree)]

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
        consumable_upkeeps: Sequence[str | Mapping[str, Any]] | None = None,
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
        consumable_upkeeps: Sequence[str | Mapping[str, Any]] | None = None,
        enable_party_wipe_recovery: bool = True,
        party_wipe_default_step_name: str | None = None,
        party_wipe_return_interval_ms: float = 1000.0,
        heroai_state_logging: bool = True,
        heroai_state_log_interval_ms: int = 5000,
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
