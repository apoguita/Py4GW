


import importlib, typing

class _RProxy:
    def __getattr__(self, name: str):
        root_pkg = importlib.import_module("Py4GWCoreLib")
        return getattr(root_pkg.Routines, name)

Routines = _RProxy()


#region Targetting
class Targeting:
    @staticmethod
    def InteractTarget():
        from ..GlobalCache import GLOBAL_CACHE
        """Interact with the target"""
        GLOBAL_CACHE.Player.Interact(GLOBAL_CACHE.Player.GetTargetID(), False)
        
    @staticmethod
    def HasArrivedToTarget():
        """Check if the player has arrived at the target."""
        from ..GlobalCache import GLOBAL_CACHE
        from ..Py4GWcorelib import Utils
        player_x, player_y = GLOBAL_CACHE.Player.GetXY()
        target_id = GLOBAL_CACHE.Player.GetTargetID()
        target_x, target_y = GLOBAL_CACHE.Agent.GetXY(target_id)
        return Utils.Distance((player_x, player_y), (target_x, target_y)) < 100
#endregion