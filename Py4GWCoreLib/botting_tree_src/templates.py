from typing import TYPE_CHECKING

from ..py4gwcorelib_src.BehaviorTree import BehaviorTree

if TYPE_CHECKING:
    from ..BottingTree import BottingTree


class _BottingTreeTemplates:
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

    @staticmethod
    def PacifistTree(
        *,
        account_isolation: bool = True,
        reset_hero_ai: bool = True,
        name: str = 'ConfigurePacifistEnv',
    ) -> BehaviorTree:
        return _BottingTreeTemplates._request_template_state(
            name=name,
            hero_ai=False,
            looting=False,
            isolation=account_isolation,
            pause_on_combat=False,
            reset_hero_ai=reset_hero_ai,
        )

    @staticmethod
    def PacifistForceHeroAITree(
        *,
        reset_hero_ai: bool = True,
        name: str = 'ConfigurePacifistForceHeroAIEnv',
    ) -> BehaviorTree:
        return _BottingTreeTemplates.PacifistTree(
            account_isolation=False,
            reset_hero_ai=reset_hero_ai,
            name=name,
        )

    @staticmethod
    def AggressiveTree(
        *,
        pause_on_danger: bool = True,
        account_isolation: bool = True,
        auto_loot: bool = True,
        reset_hero_ai: bool = True,
        name: str = 'ConfigureAggressiveEnv',
    ) -> BehaviorTree:
        return _BottingTreeTemplates._request_template_state(
            name=name,
            hero_ai=True,
            looting=auto_loot,
            isolation=account_isolation,
            pause_on_combat=pause_on_danger,
            reset_hero_ai=reset_hero_ai,
        )

    @staticmethod
    def AggressiveForceHeroAITree(
        *,
        pause_on_danger: bool = True,
        auto_loot: bool = True,
        reset_hero_ai: bool = True,
        name: str = 'ConfigureAggressiveForceHeroAIEnv',
    ) -> BehaviorTree:
        return _BottingTreeTemplates.AggressiveTree(
            pause_on_danger=pause_on_danger,
            account_isolation=False,
            auto_loot=auto_loot,
            reset_hero_ai=reset_hero_ai,
            name=name,
        )

    @staticmethod
    def MultiboxAggressiveTree(
        *,
        auto_loot: bool = True,
        reset_hero_ai: bool = True,
        name: str = 'ConfigureMultiboxAggressiveEnv',
    ) -> BehaviorTree:
        return _BottingTreeTemplates.AggressiveTree(
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


BottingTreeTemplates = _BottingTreeTemplates
