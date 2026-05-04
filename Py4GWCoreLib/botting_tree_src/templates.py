import warnings
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..BottingTree import BottingTree


class _BottingTreeTemplates:
    """Deprecated compatibility layer. Use `bot.Config` instead."""

    def __init__(self, parent: 'BottingTree'):
        self.parent = parent

    def _warn(self) -> None:
        warnings.warn(
            'BottingTree.Templates is deprecated; use BottingTree.Config instead.',
            DeprecationWarning,
            stacklevel=2,
        )

    def PacifistTree(
        self,
        *,
        account_isolation: bool = True,
        reset_hero_ai: bool = True,
        name: str = 'ConfigurePacifistEnv',
    ):
        self._warn()
        return self.parent.Config.PacifistTree(
            account_isolation=account_isolation,
            reset_hero_ai=reset_hero_ai,
            name=name,
        )

    def PacifistForceHeroAITree(
        self,
        *,
        reset_hero_ai: bool = True,
        name: str = 'ConfigurePacifistForceHeroAIEnv',
    ):
        self._warn()
        return self.parent.Config.PacifistForceHeroAITree(
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
    ):
        self._warn()
        return self.parent.Config.AggressiveTree(
            pause_on_danger=pause_on_danger,
            account_isolation=account_isolation,
            auto_loot=auto_loot,
            reset_hero_ai=reset_hero_ai,
            name=name,
        )

    def AggressiveForceHeroAITree(
        self,
        *,
        pause_on_danger: bool = True,
        auto_loot: bool = True,
        reset_hero_ai: bool = True,
        name: str = 'ConfigureAggressiveForceHeroAIEnv',
    ):
        self._warn()
        return self.parent.Config.AggressiveForceHeroAITree(
            pause_on_danger=pause_on_danger,
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
    ):
        self._warn()
        return self.parent.Config.MultiboxAggressiveTree(
            auto_loot=auto_loot,
            reset_hero_ai=reset_hero_ai,
            name=name,
        )

    def Pacifist(
        self,
        *,
        account_isolation: bool = True,
        reset_hero_ai: bool = True,
    ):
        self._warn()
        return self.parent.Config.Pacifist(
            account_isolation=account_isolation,
            reset_hero_ai=reset_hero_ai,
        )

    def PacifistForceHeroAI(
        self,
        *,
        reset_hero_ai: bool = True,
    ):
        self._warn()
        return self.parent.Config.PacifistForceHeroAI(
            reset_hero_ai=reset_hero_ai,
        )

    def Aggressive(
        self,
        *,
        pause_on_danger: bool = True,
        account_isolation: bool = True,
        auto_loot: bool = True,
        reset_hero_ai: bool = True,
    ):
        self._warn()
        return self.parent.Config.Aggressive(
            pause_on_danger=pause_on_danger,
            account_isolation=account_isolation,
            auto_loot=auto_loot,
            reset_hero_ai=reset_hero_ai,
        )

    def AggressiveForceHeroAI(
        self,
        *,
        pause_on_danger: bool = True,
        auto_loot: bool = True,
        reset_hero_ai: bool = True,
    ):
        self._warn()
        return self.parent.Config.AggressiveForceHeroAI(
            pause_on_danger=pause_on_danger,
            auto_loot=auto_loot,
            reset_hero_ai=reset_hero_ai,
        )

    def Multibox_Aggressive(
        self,
        *,
        auto_loot: bool = True,
        reset_hero_ai: bool = True,
    ):
        self._warn()
        return self.parent.Config.Multibox_Aggressive(
            auto_loot=auto_loot,
            reset_hero_ai=reset_hero_ai,
        )

    ConfigurePacifistEnv = Pacifist
    ConfigureAggressiveEnv = Aggressive


BottingTreeTemplates = _BottingTreeTemplates
