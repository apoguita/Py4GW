from dataclasses import dataclass, field
from typing import Any

import PyImGui

from ..ImGui import ImGui
from ..IniManager import IniManager


@dataclass
class WindowVarSpec:
    kind: str
    key: str
    section: str
    name: str
    default: Any


@dataclass
class ManagedWindowSpec:
    identifier: str
    filename: str
    title: str
    flags: int = PyImGui.WindowFlags.NoFlag
    vars: list[WindowVarSpec] = field(default_factory=list)
    open_var_name: str | None = None
    open_default: bool = False
    ini_key: str = ""


class WindowFactory:
    def __init__(self, ini_path: str) -> None:
        self.ini_path = ini_path
        self._windows: dict[str, ManagedWindowSpec] = {}

    def register_window(self, spec: ManagedWindowSpec) -> None:
        self._windows[spec.identifier] = spec

    def ensure_ini(self) -> bool:
        for spec in self._windows.values():
            spec.ini_key = IniManager().ensure_key(self.ini_path, spec.filename)
            if not spec.ini_key:
                return False

        for spec in self._windows.values():
            IniManager().add_bool(spec.ini_key, "init", "Window config", "init", default=True)

            if spec.open_var_name is not None:
                IniManager().add_bool(
                    spec.ini_key,
                    spec.open_var_name,
                    "Configuration",
                    spec.open_var_name,
                    default=spec.open_default,
                )

            for var in spec.vars:
                match var.kind:
                    case "bool":
                        IniManager().add_bool(spec.ini_key, var.key, var.section, var.name, default=bool(var.default))
                    case "float":
                        IniManager().add_float(spec.ini_key, var.key, var.section, var.name, float(var.default))
                    case "int":
                        IniManager().add_int(spec.ini_key, var.key, var.section, var.name, int(var.default))
                    case "str":
                        IniManager().add_str(spec.ini_key, var.key, var.section, var.name, str(var.default))

            IniManager().load_once(spec.ini_key)
            IniManager().set(spec.ini_key, "init", True)
            IniManager().save_vars(spec.ini_key)

        return True

    def key(self, identifier: str) -> str:
        return self._windows[identifier].ini_key

    def begin(self, identifier: str, p_open=None) -> tuple[bool, bool]:
        spec = self._windows[identifier]
        return ImGui.BeginWithClose(
            ini_key=spec.ini_key,
            name=spec.title,
            p_open=p_open,
            flags=spec.flags,
        )

    def is_open(self, identifier: str) -> bool:
        spec = self._windows[identifier]
        if spec.open_var_name is None:
            return False
        return IniManager().getBool(spec.ini_key, spec.open_var_name, spec.open_default, section="Configuration")

    def set_open(self, identifier: str, value: bool) -> None:
        spec = self._windows[identifier]
        if spec.open_var_name is None:
            return
        IniManager().set(spec.ini_key, spec.open_var_name, bool(value), section="Configuration")
        IniManager().save_vars(spec.ini_key)
