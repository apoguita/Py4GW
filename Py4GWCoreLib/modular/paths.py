"""
paths module

This module is part of the modular runtime surface.
"""
from __future__ import annotations

import os


def project_root() -> str:
    try:
        import Py4GW

        root = str(Py4GW.Console.get_projects_path() or "").strip()
        if root:
            return os.path.normpath(root)
    except Exception:
        pass
    return os.path.normpath(os.getcwd())


def modular_data_root() -> str:
    return os.path.join(project_root(), "Sources", "modular_data")


def modular_settings_root() -> str:
    return os.path.join(project_root(), "Settings", "ModularBot")


def modular_logs_root() -> str:
    return os.path.join(project_root(), "Logs", "modular_bot")
