#region STATES
from typing import TYPE_CHECKING, Any, Dict, Iterable

if TYPE_CHECKING:
    from Py4GWCoreLib.botting_src.helpers import BottingClass

#region PROPERTIES
class _PROPERTIES:
    def __init__(self, parent: "BottingClass"):
        self.parent = parent
        self._config = parent.config
        self._helpers = parent.helpers

    def Get(self, name: str, field: str = "active") -> Any:
        return self._resolve(name).get(field)

    def Set(self, name: str, value: Any, field: str = "value") -> None:
        self._resolve(name).set(field, value)

    def IsActive(self, name: str) -> bool:
        return self._resolve(name).is_active()

    def Enable(self, name: str) -> None:
        self._resolve(name).enable()

    def Disable(self, name: str) -> None:
        self._resolve(name).disable()

    def SetActive(self, name: str, active: bool) -> None:
        self._resolve(name).set_active(active)

    def ResetTodefault(self, name: str, field: str = "active") -> None:
        self._resolve(name).reset(field)

    def ResetAll(self, name: str) -> None:
        self._resolve(name).reset_all()

    def ApplyNow(self, name: str, field: str, value: Any) -> None:
        """
        Immediate, no-FSM write.
        Directly calls Property._apply(field, value).
        Use with care: this bypasses FSM AddState.
        """
        self._resolve(name)._apply(field, value)

    # --- Internal resolver ---
    def _resolve(self, name: str):
        # Check config_properties first
        if hasattr(self._config.config_properties, name):
            return getattr(self._config.config_properties, name)
        # Then upkeep
        if hasattr(self._config.upkeep, name):
            return getattr(self._config.upkeep, name)
        raise AttributeError(f"No property named {name!r}")

    def exists(self, name: str) -> bool:
        try:
            self._resolve(name)
            return True
        except AttributeError:
            return False

    # Introspection (useful for tooling/validation)
    def fields(self, name: str) -> Iterable[str]:
        prop = self._resolve(name)
        return list(prop._values.keys())  # read-only exposure

    def values(self, name: str) -> Dict[str, Any]:
        prop = self._resolve(name)
        return dict(prop._values)  # snapshot

    def defaults(self, name: str) -> Dict[str, Any]:
        prop = self._resolve(name)
        return dict(prop._defaults)  # snapshot
    
    def SetActiveSkills(self, active: bool) -> None:
        self._config.build_handler
