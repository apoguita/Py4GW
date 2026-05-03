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

    def PacifistTree(self, **kwargs):
        self._warn()
        return self.parent.Config.PacifistTree(**kwargs)

    def PacifistForceHeroAITree(self, **kwargs):
        self._warn()
        return self.parent.Config.PacifistForceHeroAITree(**kwargs)

    def AggressiveTree(self, **kwargs):
        self._warn()
        return self.parent.Config.AggressiveTree(**kwargs)

    def AggressiveForceHeroAITree(self, **kwargs):
        self._warn()
        return self.parent.Config.AggressiveForceHeroAITree(**kwargs)

    def MultiboxAggressiveTree(self, **kwargs):
        self._warn()
        return self.parent.Config.MultiboxAggressiveTree(**kwargs)

    def Pacifist(self, **kwargs):
        self._warn()
        return self.parent.Config.Pacifist(**kwargs)

    def PacifistForceHeroAI(self, **kwargs):
        self._warn()
        return self.parent.Config.PacifistForceHeroAI(**kwargs)

    def Aggressive(self, **kwargs):
        self._warn()
        return self.parent.Config.Aggressive(**kwargs)

    def AggressiveForceHeroAI(self, **kwargs):
        self._warn()
        return self.parent.Config.AggressiveForceHeroAI(**kwargs)

    def Multibox_Aggressive(self, **kwargs):
        self._warn()
        return self.parent.Config.Multibox_Aggressive(**kwargs)

    ConfigurePacifistEnv = Pacifist
    ConfigureAggressiveEnv = Aggressive


BottingTreeTemplates = _BottingTreeTemplates
