from imgui_bundle import hello_imgui, imgui
import json
import tkinter as tk
from tkinter import filedialog


import ctypes
import ctypes.wintypes
from ctypes import wintypes
user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32
from typing import Optional


import threading
import time
import shutil
import socket
import subprocess
from pathlib import Path
import win32gui
import win32process
import psutil
import sys
import configparser
import os
import math
import re
import copy
import base64
import hashlib
import hmac
import secrets
import struct
import mmap

class IniHandler:
    def __init__(self, filename: str):
        self.filename = filename
        self.last_modified = 0
        self.config = configparser.ConfigParser()


    def reload(self) -> configparser.ConfigParser:
        current_mtime = os.path.getmtime(self.filename)
        if current_mtime != self.last_modified:
            self.last_modified = current_mtime
            self.config.read(self.filename)
        return self.config

    def save(self, config: configparser.ConfigParser) -> None:
        with open(self.filename, 'w') as configfile:
            config.write(configfile)


    def read_key(self, section: str, key: str, default_value: str = "") -> str:
        config = self.reload()
        try:
            return config.get(section, key)
        except (configparser.NoOptionError, configparser.NoSectionError):
            return default_value

    def read_int(self, section: str, key: str, default_value: int = 0) -> int:
        config = self.reload()
        try:
            return config.getint(section, key)
        except (ValueError, configparser.NoOptionError, configparser.NoSectionError):
            return default_value

    def read_float(self, section: str, key: str, default_value: float = 0.0) -> float:
        config = self.reload()
        try:
            return config.getfloat(section, key)
        except (ValueError, configparser.NoOptionError, configparser.NoSectionError):
            return default_value

    def read_bool(self, section: str, key: str, default_value: bool = False) -> bool:
        config = self.reload()
        try:
            return config.getboolean(section, key)
        except (ValueError, configparser.NoOptionError, configparser.NoSectionError):
            return default_value


    def write_key(self, section: str, key: str, value: str) -> None:
        config = self.reload()
        if not config.has_section(section):
            config.add_section(section)
        config.set(section, key, str(value))
        self.save(config)


    def delete_key(self, section: str, key: str) -> None:
        config = self.reload()
        if config.has_section(section) and config.has_option(section, key):
            config.remove_option(section, key)
            self.save(config)

    def delete_section(self, section: str) -> None:
        config = self.reload()
        if config.has_section(section):
            config.remove_section(section)
            self.save(config)


    def list_sections(self) -> list:
        config = self.reload()
        return config.sections()

    def list_keys(self, section: str) -> dict:
        config = self.reload()
        if config.has_section(section):
            return dict(config.items(section))
        return {}

    def has_key(self, section: str, key: str) -> bool:
        config = self.reload()
        return config.has_section(section) and config.has_option(section, key)

    def clone_section(self, source_section: str, target_section: str) -> None:
        config = self.reload()
        if config.has_section(source_section):
            if not config.has_section(target_section):
                config.add_section(target_section)
            for key, value in config.items(source_section):
                config.set(target_section, key, value)
            self.save(config)


current_directory = os.getcwd()
ini_file = "Py4GW.ini"
ini_handler = IniHandler(ini_file)
mods_directory = os.path.join(current_directory, "Addons", "mods")
os.makedirs(mods_directory, exist_ok=True)

config_file = ini_handler.read_key("settings","account_config_file","accounts.json")
py4gw_dll_name = ini_handler.read_key("settings","py4gw_dll_name","Py4GW.dll")
gwtoolbox_dll_name = ini_handler.read_key("settings", "gwtoolbox_dll_name", "GWToolbox.dll")
gmod_dll_name = ini_handler.read_key("settings", "gmod_dll_name", "gMod.dll")
py4gw_gwtoolbox_delay_seconds = ini_handler.read_float("settings", "py4gw_gwtoolbox_delay_seconds", 0.0)

class TimestampedLogHistory(list):
    def _has_timestamp(self, value):
        try:
            text_value = str(value)
            return (
                len(text_value) >= 11
                and text_value[0] == "["
                and text_value[3] == ":"
                and text_value[6] == ":"
                and text_value[9] == "]"
                and text_value[10] == " "
            )
        except Exception:
            return False

    def _stamp(self, value):
        text_value = str(value)
        if self._has_timestamp(text_value):
            return text_value
        return f"[{time.strftime('%H:%M:%S')}] {text_value}"

    def append(self, value):
        super().append(self._stamp(value))

    def extend(self, values):
        super().extend(self._stamp(value) for value in values)

    def insert(self, index, value):
        super().insert(index, self._stamp(value))

    def __setitem__(self, key, value):
        if isinstance(key, slice):
            super().__setitem__(key, [self._stamp(item) for item in value])
        else:
            super().__setitem__(key, self._stamp(value))

log_history = TimestampedLogHistory()
log_history.append("Welcome To Py4GW!")

APP_VERSION = "1.0.1"


THEME_DARK = "dark"
THEME_LIGHT = "light"


def normalize_launcher_theme_mode(value: str) -> str:
    value = str(value or "").strip().lower()
    if value in ("light", "white", "normal", "normal mode", "white mode"):
        return THEME_LIGHT
    return THEME_DARK


def read_launcher_theme_mode(default_value: str = THEME_DARK) -> str:
    try:
        return normalize_launcher_theme_mode(
            ini_handler.read_key("Py4GW_Launcher", "theme_mode", default_value)
        )
    except Exception:
        return normalize_launcher_theme_mode(default_value)


def write_launcher_theme_mode(theme_mode: str) -> None:
    try:
        ini_handler.write_key("Py4GW_Launcher", "theme_mode", normalize_launcher_theme_mode(theme_mode))
    except Exception as e:
        log_history.append(f"Theme - Failed to save theme mode: {str(e)}")


def get_launcher_theme_label(theme_mode: str = None) -> str:
    mode = normalize_launcher_theme_mode(theme_mode if theme_mode is not None else ui_theme_mode)
    return "White Mode" if mode == THEME_LIGHT else "Dark Mode"


def _sanitize_team_settings_key(team_name: str) -> str:
    safe = "".join(ch if ch.isalnum() else "_" for ch in str(team_name).strip()).strip("_").lower()
    return safe or "team"


def read_team_launch_delay(team_name: str, default_value: int = 15) -> int:
    try:
        value = ini_handler.read_int("team_launch_delays", _sanitize_team_settings_key(team_name), default_value)
        return max(0, int(value))
    except Exception:
        return default_value


def write_team_launch_delay(team_name: str, seconds: int) -> None:
    try:
        ini_handler.write_key("team_launch_delays", _sanitize_team_settings_key(team_name), str(max(0, int(seconds))))
    except Exception as e:
        log_history.append(f"Team Settings - Failed to save launch delay for '{team_name}': {str(e)}")


def delete_team_launch_delay(team_name: str) -> None:
    try:
        ini_handler.delete_key("team_launch_delays", _sanitize_team_settings_key(team_name))
    except Exception as e:
        log_history.append(f"Team Settings - Failed to delete launch delay for '{team_name}': {str(e)}")

def check_and_handle_version_mismatch(ini_filename: str):
    global ini_handler, log_history, ui_theme_mode, applied_ui_theme_mode, modern_style_applied

    stored_version = ini_handler.read_key("Py4GW_Launcher", "APP_VERSION", "0.0.0")

    if stored_version != APP_VERSION:
        log_history.append(f"Version mismatch detected: Stored={stored_version}, Current={APP_VERSION}")
        ini_handler.write_key("Py4GW_Launcher", "APP_VERSION", APP_VERSION)
        log_history.append(f"Updated stored version to {APP_VERSION}")


        try:
            if not ini_handler.has_key("Py4GW_Launcher", "theme_mode"):
                ui_theme_mode = THEME_DARK
                applied_ui_theme_mode = None
                modern_style_applied = False
                log_history.append("Theme - Using built-in Dark Mode default.")
        except Exception as e:
            log_history.append(f"Theme - Default check failed: {str(e)}")
    else:
        log_history.append(f"Version check passed: {APP_VERSION}")

PROCESS_ALL_ACCESS = 0x1F0FFF
VIRTUAL_MEM = 0x1000 | 0x2000
PAGE_READWRITE = 0x04
MEM_RELEASE = 0x8000

PROCESS_VM_OPERATION = 0x0008
PROCESS_VM_READ = 0x0010
PROCESS_VM_WRITE = 0x0020
PROCESS_QUERY_INFORMATION = 0x0400
MAX_PATH = 260
TH32CS_SNAPPROCESS = 0x00000002
TH32CS_SNAPMODULE = 0x00000008
TH32CS_SNAPMODULE32 = 0x00000010
INVALID_HANDLE_VALUE = ctypes.c_void_p(-1).value


SWP_NOZORDER = 0x0004
SWP_NOACTIVATE = 0x0010
HWND_TOP = 0
WM_SETTEXT = 0x000C


WNDENUMPROC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)


user32.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
user32.GetWindowThreadProcessId.restype = wintypes.DWORD

user32.EnumWindows.argtypes = [WNDENUMPROC, wintypes.LPARAM]
user32.EnumWindows.restype = wintypes.BOOL

user32.IsWindowVisible.argtypes = [wintypes.HWND]
user32.IsWindowVisible.restype = wintypes.BOOL

user32.SetWindowTextW.argtypes = [wintypes.HWND, wintypes.LPCWSTR]
user32.SetWindowTextW.restype = wintypes.BOOL

user32.MoveWindow.argtypes = [
    wintypes.HWND,
    ctypes.c_int,
    ctypes.c_int,
    ctypes.c_int,
    ctypes.c_int,
    wintypes.BOOL,
]
user32.MoveWindow.restype = wintypes.BOOL


class PROCESS_BASIC_INFORMATION(ctypes.Structure):
    _fields_ = [("Reserved1", ctypes.c_void_p),
                ("PebBaseAddress", ctypes.c_void_p),
                ("Reserved2", ctypes.c_void_p * 2),
                ("UniqueProcessId", ctypes.c_ulong),
                ("Reserved3", ctypes.c_void_p)]

class PEB(ctypes.Structure):
    _fields_ = [("InheritedAddressSpace", ctypes.c_ubyte),
                ("ReadImageFileExecOptions", ctypes.c_ubyte),
                ("BeingDebugged", ctypes.c_ubyte),
                ("BitField", ctypes.c_ubyte),
                ("Mutant", ctypes.c_void_p),
                ("ImageBaseAddress", ctypes.c_void_p)]

class PROCESSENTRY32(ctypes.Structure):
    _fields_ = [("dwSize", ctypes.c_ulong),
                ("cntUsage", ctypes.c_ulong),
                ("th32ProcessID", ctypes.c_ulong),
                ("th32DefaultHeapID", ctypes.POINTER(ctypes.c_ulong)),
                ("th32ModuleID", ctypes.c_ulong),
                ("cntThreads", ctypes.c_ulong),
                ("th32ParentProcessID", ctypes.c_ulong),
                ("pcPriClassBase", ctypes.c_long),
                ("dwFlags", ctypes.c_ulong),
                ("szExeFile", ctypes.c_char * MAX_PATH)]

class MODULEENTRY32(ctypes.Structure):
    _fields_ = [("dwSize", wintypes.DWORD),
                ("th32ModuleID", wintypes.DWORD),
                ("th32ProcessID", wintypes.DWORD),
                ("GlblcntUsage", wintypes.DWORD),
                ("ProccntUsage", wintypes.DWORD),
                ("modBaseAddr", ctypes.POINTER(ctypes.c_byte)),
                ("modBaseSize", wintypes.DWORD),
                ("hModule", wintypes.HMODULE),
                ("szModule", wintypes.WCHAR * 256),
                ("szExePath", wintypes.WCHAR * MAX_PATH)]

CREATE_SUSPENDED = 0x00000004

class STARTUPINFO(ctypes.Structure):
    _fields_ = [("cb", ctypes.c_ulong),
                ("lpReserved", ctypes.c_wchar_p),
                ("lpDesktop", ctypes.c_wchar_p),
                ("lpTitle", ctypes.c_wchar_p),
                ("dwX", ctypes.c_ulong),
                ("dwY", ctypes.c_ulong),
                ("dwXSize", ctypes.c_ulong),
                ("dwYSize", ctypes.c_ulong),
                ("dwXCountChars", ctypes.c_ulong),
                ("dwYCountChars", ctypes.c_ulong),
                ("dwFillAttribute", ctypes.c_ulong),
                ("dwFlags", ctypes.c_ulong),
                ("wShowWindow", ctypes.c_ushort),
                ("cbReserved2", ctypes.c_ushort),
                ("lpReserved2", ctypes.c_void_p),
                ("hStdInput", ctypes.c_void_p),
                ("hStdOutput", ctypes.c_void_p),
                ("hStdError", ctypes.c_void_p)]

class PROCESS_INFORMATION(ctypes.Structure):
    _fields_ = [("hProcess", ctypes.c_void_p),
                ("hThread", ctypes.c_void_p),
                ("dwProcessId", ctypes.c_ulong),
                ("dwThreadId", ctypes.c_ulong)]

kernel32 = ctypes.windll.kernel32
ntdll = ctypes.windll.ntdll

try:
    kernel32.CreateToolhelp32Snapshot.argtypes = [wintypes.DWORD, wintypes.DWORD]
    kernel32.CreateToolhelp32Snapshot.restype = wintypes.HANDLE
    kernel32.Module32FirstW.argtypes = [wintypes.HANDLE, ctypes.POINTER(MODULEENTRY32)]
    kernel32.Module32FirstW.restype = wintypes.BOOL
    kernel32.Module32NextW.argtypes = [wintypes.HANDLE, ctypes.POINTER(MODULEENTRY32)]
    kernel32.Module32NextW.restype = wintypes.BOOL
    kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
    kernel32.CloseHandle.restype = wintypes.BOOL
except Exception:
    pass

class Account:
    def __init__(self, character_name, email, password, gw_client_name, gw_path, extra_args, run_as_admin,
                 inject_py4gw, inject_gwtoolbox, script_path="", enable_client_rename=False, use_character_name=False,
                 custom_client_name="", last_launch_time=None, total_runtime=0.0, current_session_time=0.0,
                 average_runtime=0.0, min_runtime=0.0, max_runtime=0.0, top_left=(0, 0), width=800, height=600,
                 preview_area=False, resize_client=False, inject_gmod=False, gmod_mods=None,
                 gwtoolbox_path="", launch_selected=False, launcher_account_uid=None):
        self.character_name = character_name
        self.email = email
        self.password = password
        self.gw_client_name = gw_client_name
        self.gw_path = gw_path
        self.extra_args = extra_args
        self.run_as_admin = run_as_admin
        self.inject_py4gw = inject_py4gw
        self.inject_gwtoolbox = inject_gwtoolbox
        self.inject_gmod = inject_gmod
        self.gmod_mods = gmod_mods if gmod_mods is not None else []
        self.gwtoolbox_path = str(gwtoolbox_path or "")
        self.script_path = script_path
        self.enable_client_rename = enable_client_rename
        self.use_character_name = use_character_name
        self.custom_client_name = custom_client_name
        self.last_launch_time = last_launch_time
        self.total_runtime = total_runtime
        self.current_session_time = current_session_time
        self.average_runtime = average_runtime
        self.min_runtime = min_runtime
        self.max_runtime = max_runtime
        self.top_left = top_left
        self.width = width
        self.height = height
        self.preview_area = preview_area
        self.resize_client = resize_client
        self.launch_selected = bool(launch_selected)
        self.launcher_account_uid = str(launcher_account_uid or secrets.token_hex(16))

    def to_dict(self):
        return {
            "character_name": self.character_name,
            "email": self.email,
            "password": self.password,
            "gw_client_name": self.gw_client_name,
            "gw_path": self.gw_path,
            "extra_args": self.extra_args,
            "run_as_admin": self.run_as_admin,
            "inject_py4gw": self.inject_py4gw,
            "inject_gwtoolbox": self.inject_gwtoolbox,
            "inject_gmod": self.inject_gmod,
            "gmod_mods": list(self.gmod_mods or []),
            "gwtoolbox_path": self.gwtoolbox_path,
            "script_path": self.script_path,
            "enable_client_rename": self.enable_client_rename,
            "use_character_name": self.use_character_name,
            "custom_client_name": self.custom_client_name,
            "last_launch_time": self.last_launch_time,
            "total_runtime": self.total_runtime,
            "current_session_time": self.current_session_time,
            "average_runtime": self.average_runtime,
            "min_runtime": self.min_runtime,
            "max_runtime": self.max_runtime,
            "top_left": self.top_left,
            "width": self.width,
            "height": self.height,
            "preview_area": self.preview_area,
            "resize_client": self.resize_client,
            "launch_selected": self.launch_selected,
            "launcher_account_uid": self.launcher_account_uid,
        }

    @staticmethod
    def from_dict(data):
        return Account(
            character_name=data["character_name"],
            email=data["email"],
            password=data["password"],
            gw_client_name=data["gw_client_name"],
            gw_path=data["gw_path"],
            extra_args=data["extra_args"],
            run_as_admin=data["run_as_admin"],
            inject_py4gw=data["inject_py4gw"],
            inject_gwtoolbox=data.get("inject_gwtoolbox", False),
            inject_gmod=data.get("inject_gmod", False),
            gmod_mods=list(data.get("gmod_mods", []) or []),
            gwtoolbox_path=data.get("gwtoolbox_path", ""),
            script_path=data.get("script_path", ""),
            enable_client_rename=data.get("enable_client_rename", False),
            use_character_name=data.get("use_character_name", False),
            custom_client_name=data.get("custom_client_name", ""),
            last_launch_time=data.get("last_launch_time", None),
            total_runtime=data.get("total_runtime", 0.0),
            current_session_time=data.get("current_session_time", 0.0),
            average_runtime=data.get("average_runtime", 0.0),
            min_runtime=data.get("min_runtime", 0.0),
            max_runtime=data.get("max_runtime", 0.0),
            top_left=tuple(data.get("top_left", (0, 0))),
            width=data.get("width", 800),
            height=data.get("height", 600),
            preview_area=data.get("preview_area", False),
            resize_client=data.get("resize_client", False),
            launch_selected=data.get("launch_selected", False),
            launcher_account_uid=data.get("launcher_account_uid"),
        )

def clone_account(account: Account, reset_launch_selected: bool = False) -> Account:
    try:
        cloned_data = copy.deepcopy(account.to_dict())
        cloned_account = Account.from_dict(cloned_data)
    except Exception:

        cloned_account = Account.from_dict(dict(account.to_dict()))

    cloned_account.launcher_account_uid = secrets.token_hex(16)

    if reset_launch_selected:
        cloned_account.launch_selected = False

    return cloned_account


def get_account_client_title(account) -> str:
    try:
        rename_value = str(getattr(account, "gw_client_name", "") or "").strip()
        if rename_value:
            return rename_value

        character_name = str(getattr(account, "character_name", "") or "").strip()
        if character_name:
            return character_name
    except Exception:
        pass

    return "Guild Wars"


def get_account_display_name(account) -> str:
    try:
        client_title = get_account_client_title(account).strip()
        if client_title and client_title != "Guild Wars":
            return client_title

        custom_name = str(getattr(account, "custom_client_name", "") or "").strip()
        if custom_name:
            return custom_name

        character_name = str(getattr(account, "character_name", "") or "").strip()
        if character_name:
            return character_name
    except Exception:
        pass

    return "<Unnamed Account>"


class Team:
    def __init__(self, name, launch_delay_seconds=None):
        self.name = str(name).strip()
        self.accounts = []
        self.launch_delay_seconds = (
            read_team_launch_delay(self.name)
            if launch_delay_seconds is None
            else max(0, int(launch_delay_seconds))
        )

    def add_account(self, account):
        self.accounts.append(account)

    def to_dict(self):
        try:
            return [account_to_storage_dict(account) for account in self.accounts]
        except NameError:


            return [account.to_dict() for account in self.accounts]

    @staticmethod
    def from_dict(name, accounts_data):
        team = Team(name)


        if isinstance(accounts_data, list):
            account_list = accounts_data
        elif isinstance(accounts_data, dict):

            account_list = accounts_data.get("accounts", [])
            if "launch_delay_seconds" in accounts_data:
                team.launch_delay_seconds = max(0, int(accounts_data.get("launch_delay_seconds", 15)))
                write_team_launch_delay(team.name, team.launch_delay_seconds)
        else:
            account_list = []

        for account_data in account_list:
            try:
                team.add_account(Account.from_dict(account_data))
            except Exception as e:
                log_history.append(f"Team Load - Skipped invalid account in team '{name}': {str(e)}")
        return team


class TeamManager:
    global log_history
    def __init__(self):
        self.teams = {}

    def add_team(self, team):
        self.teams[team.name] = team

    def team_exists(self, team_name: str) -> bool:
        clean_name = str(team_name).strip()
        return clean_name in self.teams

    def get_unique_team_name(self, base_name: str) -> str:
        clean_base = str(base_name).strip() or "New Team"
        if clean_base not in self.teams:
            return clean_base

        counter = 2
        while True:
            candidate = f"{clean_base} {counter}"
            if candidate not in self.teams:
                return candidate
            counter += 1

    def rename_team(self, old_name: str, new_name: str) -> bool:
        old_name = str(old_name).strip()
        new_name = str(new_name).strip()

        if not old_name or old_name not in self.teams:
            log_history.append(f"Team Rename - Source team not found: {old_name}")
            return False
        if not new_name:
            log_history.append("Team Rename - New team name is empty.")
            return False
        if new_name in self.teams and new_name != old_name:
            log_history.append(f"Team Rename - Team already exists: {new_name}")
            return False

        team = self.teams[old_name]
        old_delay = getattr(team, "launch_delay_seconds", read_team_launch_delay(old_name))
        team.name = new_name
        team.launch_delay_seconds = old_delay

        renamed = {}
        for name, existing_team in self.teams.items():
            if name == old_name:
                renamed[new_name] = team
            else:
                renamed[name] = existing_team
        self.teams = renamed

        delete_team_launch_delay(old_name)
        write_team_launch_delay(new_name, old_delay)
        log_history.append(f"Team Rename - Renamed '{old_name}' to '{new_name}'.")
        return True

    def duplicate_team(self, source_name: str, new_name: str) -> Optional[Team]:
        source_name = str(source_name).strip()
        new_name = self.get_unique_team_name(new_name)

        source_team = self.teams.get(source_name)
        if not source_team:
            log_history.append(f"Team Duplicate - Source team not found: {source_name}")
            return None

        duplicate = Team(new_name, launch_delay_seconds=getattr(source_team, "launch_delay_seconds", 15))
        duplicate.accounts = [clone_account(account) for account in source_team.accounts]
        self.add_team(duplicate)
        write_team_launch_delay(duplicate.name, duplicate.launch_delay_seconds)
        log_history.append(
            f"Team Duplicate - Duplicated '{source_name}' to '{duplicate.name}' with {len(duplicate.accounts)} accounts."
        )
        return duplicate

    def delete_team(self, team_name: str) -> bool:
        team_name = str(team_name).strip()
        if not team_name or team_name not in self.teams:
            log_history.append(f"Team Delete - Team not found: {team_name}")
            return False

        del self.teams[team_name]
        delete_team_launch_delay(team_name)
        log_history.append(f"Team Delete - Deleted team: {team_name}")
        return True

    def save_to_json(self, file_path):
        data = {team_name: team.to_dict() for team_name, team in self.teams.items()}
        try:
            if credentials_protection_enabled:
                if credential_encrypt_complete_json:
                    plain_json = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
                    data = {
                        CREDENTIAL_JSON_ENC_MARKER: True,
                        "version": 1,
                        "payload": encrypt_credential_value(plain_json),
                    }
                else:
                    data[CREDENTIAL_META_KEY] = get_credentials_metadata_for_storage()
        except NameError:
            pass

        with open(file_path, "w", encoding="utf-8") as file:
            json.dump(data, file, indent=4, ensure_ascii=False)

    def load_plain_data(self, data):
        if not isinstance(data, dict):
            self.teams = {}
            return

        try:
            apply_credentials_metadata_from_data(data)
        except NameError:
            pass

        team_items = {
            team_name: accounts
            for team_name, accounts in data.items()
            if team_name != CREDENTIAL_META_KEY
        }
        self.teams = {team_name: Team.from_dict(team_name, accounts) for team_name, accounts in team_items.items()}

    def load_from_json(self, file_path):
        try:
            with open(file_path, "r", encoding="utf-8") as file:
                data = json.load(file)

            try:
                if is_encrypted_json_wrapper(data):
                    apply_complete_json_locked_state()
                    self.teams = {}
                    log_history.append("Credential Security - Complete JSON file is encrypted. Unlock required before loading teams.")
                    return
            except NameError:
                pass

            self.load_plain_data(data)
        except FileNotFoundError:

            with open(file_path, "w", encoding="utf-8") as file:
                json.dump({}, file)
            log_history.append(f"File {file_path} not found. Created an empty file.")
            self.teams = {}
        except json.JSONDecodeError as e:
            log_history.append(f"Error parsing JSON from {file_path}: {e}")
            self.teams = {}

    def get_team(self, team_name):
        return self.teams.get(team_name)

    def get_first_team(self):
        if self.teams:
            return next(iter(self.teams.values()))
        return None

    def filter_accounts(self, team_name=None, character_name=None):
        results = []
        for team in self.teams.values():
            if team_name and team.name != team_name:
                continue
            for account in team.accounts:
                if character_name and account.character_name != character_name:
                    continue
                results.append(account)
        return results

class Patcher:
    global log_history

    def __init__(self):
        pass

    def get_process_module_base(self, process_handle: int) -> Optional[int]:
        pbi = PROCESS_BASIC_INFORMATION()
        return_length = ctypes.c_ulong(0)

        if ntdll.NtQueryInformationProcess(process_handle, 0, ctypes.byref(pbi), ctypes.sizeof(pbi), ctypes.byref(return_length)) != 0:
            return None

        peb_address = pbi.PebBaseAddress
        buffer = ctypes.create_string_buffer(ctypes.sizeof(PEB))

        bytes_read = ctypes.c_size_t()
        if not kernel32.ReadProcessMemory(process_handle, peb_address, buffer, ctypes.sizeof(PEB), ctypes.byref(bytes_read)):
            return None

        peb = PEB.from_buffer(buffer)
        return peb.ImageBaseAddress

    def search_bytes(self, haystack: bytes, needle: bytes) -> int:
        try:
            return haystack.index(needle)
        except ValueError:
            return -1

    def patch(self, pid: int) -> bool:

        process_handle = kernel32.OpenProcess(
            PROCESS_VM_OPERATION | PROCESS_VM_READ | PROCESS_VM_WRITE | PROCESS_QUERY_INFORMATION,
            False,
            pid
        )

        if process_handle is None:
            log_history.append(f"Patcher - Could not open process with PID {pid}: {ctypes.GetLastError()}")
            return False

        sig_patch = bytes([0x56, 0x57, 0x68, 0x00, 0x01, 0x00, 0x00, 0x89, 0x85, 0xF4, 0xFE, 0xFF, 0xFF, 0xC7, 0x00, 0x00, 0x00, 0x00, 0x00])
        module_base = self.get_process_module_base(process_handle)
        if module_base is None:
            log_history.append("Patcher - Failed to get module base")
            kernel32.CloseHandle(process_handle)
            return False
        gwdata = ctypes.create_string_buffer(0x48D000)

        bytes_read = ctypes.c_size_t()
        if not kernel32.ReadProcessMemory(process_handle, module_base, gwdata, 0x48D000, ctypes.byref(bytes_read)):
            log_history.append(f"Patcher - Failed to read process memory: {ctypes.GetLastError()}")
            kernel32.CloseHandle(process_handle)
            return False

        idx = self.search_bytes(gwdata.raw, sig_patch)
        if idx == -1:
            log_history.append("Patcher - Failed to find signature")
            kernel32.CloseHandle(process_handle)
            return False

        mcpatch_address = module_base + idx - 0x1A
        payload = bytes([0x31, 0xC0, 0x90, 0xC3])

        bytes_written = ctypes.c_size_t()
        if not kernel32.WriteProcessMemory(process_handle, mcpatch_address, payload, len(payload), ctypes.byref(bytes_written)):
            log_history.append(f"Patcher - Failed to write process memory: {ctypes.GetLastError()}")
            kernel32.CloseHandle(process_handle)
            return False

        log_history.append(f"Patcher - Patched at address: {hex(mcpatch_address)}")
        kernel32.CloseHandle(process_handle)
        return True

    def get_hwnd_by_pid(self, pid: int) -> wintypes.HWND:
        hwnd = wintypes.HWND(0)


        def callback(handle, extra):
            nonlocal hwnd
            window_pid = wintypes.DWORD()
            user32.GetWindowThreadProcessId(handle, ctypes.byref(window_pid))
            if window_pid.value == pid and user32.IsWindowVisible(handle):
                hwnd = handle
                return False
            return True


        user32.EnumWindows(WNDENUMPROC(callback), 0)
        return hwnd


    def launch_and_patch(self, gw_exe_path: str, account: str, password: str, character: str, extra_args: str, elevated: bool) -> Optional[int]:
        command_line = f'"{gw_exe_path}" -email "{account}" -password "{password}"'
        if character:
            command_line += f' -character "{character}"'
        command_line += f" {extra_args}"

        startup_info = STARTUPINFO()
        startup_info.cb = ctypes.sizeof(startup_info)
        process_info = PROCESS_INFORMATION()

        success = kernel32.CreateProcessW(
            None,
            command_line,
            None,
            None,
            False,
            CREATE_SUSPENDED,
            None,
            None,
            ctypes.byref(startup_info),
            ctypes.byref(process_info)
        )

        if not success:
            log_history.append(f"Patcher - Failed to create process: {ctypes.GetLastError()}")
            return None

        pid = process_info.dwProcessId

        if self.patch(pid):
            log_history.append("Patcher - Multiclient patch applied successfully.")
        else:
            log_history.append("Patcher - Failed to apply multiclient patch.")
            kernel32.TerminateProcess(process_info.hProcess, 0)
            kernel32.CloseHandle(process_info.hProcess)
            kernel32.CloseHandle(process_info.hThread)
            return None

        if kernel32.ResumeThread(process_info.hThread) == -1:
            log_history.append(f"Python - Failed to resume thread: {ctypes.GetLastError()}")
            kernel32.TerminateProcess(process_info.hProcess, 0)
            kernel32.CloseHandle(process_info.hProcess)
            kernel32.CloseHandle(process_info.hThread)
            return None

        log_history.append("Patcher - Process resumed.")

        kernel32.CloseHandle(process_info.hProcess)
        kernel32.CloseHandle(process_info.hThread)

        return pid

class GWLauncher:
    global log_history, current_directory, py4gw_dll_name, gwtoolbox_dll_name, ini_handler

    def __init__(self):
        self.active_pids = []
        self.gmod_injection_delay = 0.5
        self.py4gw_gwtoolbox_delay_seconds = max(0.0, float(py4gw_gwtoolbox_delay_seconds))

    def wait_for_gw_window(self, pid, timeout=30):
        log_history.append(f"Waiting for GW window (PID: {pid})")
        start_time = time.time()
        found_windows = []

        def enum_windows_callback(hwnd, _):
            if win32gui.IsWindowVisible(hwnd):
                try:
                    _, window_pid = win32process.GetWindowThreadProcessId(hwnd)
                    if window_pid == pid:
                        title = win32gui.GetWindowText(hwnd)
                        log_history.append(f"Wait for GW Window - Found window with title: '{title}' for PID: {pid}")

                        found_windows.append(hwnd)
                except Exception as e:
                    log_history.append(f"Wait for GW Window - Error in callback: {str(e)}")
            return True

        while time.time() - start_time < timeout:
            try:
                process = psutil.Process(pid)
                if process.status() != psutil.STATUS_RUNNING:
                    log_history.append(f"Wait for GW Window - Process {pid} is not running")
                    return False


                found_windows.clear()
                win32gui.EnumWindows(enum_windows_callback, None)

                if found_windows:
                    log_history.append(f"Wait for GW Window - Found {len(found_windows)} windows for process {pid}")

                    return True

            except psutil.NoSuchProcess:
                log_history.append(f"Wait for GW Window - Process {pid} no longer exists")
                return False
            except Exception as e:
                log_history.append(f"Wait for GW Window - Error while waiting for GW window: {str(e)}")
                return False

            time.sleep(0.5)


            elapsed = time.time() - start_time
            if elapsed % 5 < 0.5:
                log_history.append(f"Wait for GW Window - Still waiting... ({int(elapsed)}s)")

                try:
                    process = psutil.Process(pid)
                    log_history.append(f"Wait for GW Window - Process status: {process.status()}")
                    log_history.append(f"Wait for GW Window - Process command line: {process.cmdline()}")
                except Exception as e:
                    log_history.append(f"Wait for GW Window - Error getting process info: {str(e)}")

        log_history.append(f"Wait for GW Window - Timeout waiting for window of process {pid}")
        return False

    def get_visible_windows_for_pid(self, pid):
        windows = []

        def enum_windows_callback(hwnd, _):
            try:
                if not win32gui.IsWindowVisible(hwnd):
                    return True

                _, window_pid = win32process.GetWindowThreadProcessId(hwnd)
                if window_pid != pid:
                    return True

                title = win32gui.GetWindowText(hwnd)
                class_name = ""
                try:
                    class_name = win32gui.GetClassName(hwnd)
                except Exception:
                    class_name = ""

                try:
                    rect = win32gui.GetWindowRect(hwnd)
                    area = max(0, rect[2] - rect[0]) * max(0, rect[3] - rect[1])
                except Exception:
                    rect = (0, 0, 0, 0)
                    area = 0

                windows.append({
                    "hwnd": hwnd,
                    "title": title,
                    "class_name": class_name,
                    "rect": rect,
                    "area": area,
                })
            except Exception as e:
                log_history.append(f"Window Config - EnumWindows callback error: {str(e)}")
            return True

        try:
            win32gui.EnumWindows(enum_windows_callback, None)
        except Exception as e:
            log_history.append(f"Window Config - EnumWindows failed: {str(e)}")

        return windows

    def get_main_window_handle(self, pid, timeout=30):
        start_time = time.time()

        while time.time() - start_time < timeout:
            windows = self.get_visible_windows_for_pid(pid)
            if windows:
                windows.sort(key=lambda item: item.get("area", 0), reverse=True)
                return windows[0]["hwnd"]

            try:
                if not self.is_process_running(pid):
                    log_history.append(f"Window Config - Process no longer running. PID={pid}")
                    return None
            except Exception:
                return None

            time.sleep(0.25)

        log_history.append(f"Window Config - Timeout waiting for window handle. PID={pid}")
        return None

    def get_dwm_extended_frame_bounds(self, hwnd):
        try:
            rect = ctypes.wintypes.RECT()
            dwmapi = ctypes.windll.dwmapi
            DWMWA_EXTENDED_FRAME_BOUNDS = 9
            result = dwmapi.DwmGetWindowAttribute(
                ctypes.wintypes.HWND(hwnd),
                ctypes.c_uint(DWMWA_EXTENDED_FRAME_BOUNDS),
                ctypes.byref(rect),
                ctypes.sizeof(rect),
            )
            if int(result) == 0:
                return (int(rect.left), int(rect.top), int(rect.right), int(rect.bottom))
        except Exception:
            pass
        return None

    def compute_outer_rect_for_visible_grid_bounds(self, hwnd, target_x: int, target_y: int, target_w: int, target_h: int):
        try:
            outer = win32gui.GetWindowRect(hwnd)
            visible = self.get_dwm_extended_frame_bounds(hwnd)
            if not outer or not visible:
                return int(target_x), int(target_y), int(target_w), int(target_h)

            left_invisible = int(visible[0] - outer[0])
            top_invisible = int(visible[1] - outer[1])
            right_invisible = int(outer[2] - visible[2])
            bottom_invisible = int(outer[3] - visible[3])


            invisible_values = (left_invisible, top_invisible, right_invisible, bottom_invisible)
            if any(value < -32 or value > 64 for value in invisible_values):
                return int(target_x), int(target_y), int(target_w), int(target_h)

            move_x = int(target_x - left_invisible)
            move_y = int(target_y - top_invisible)
            move_w = int(target_w + left_invisible + right_invisible)
            move_h = int(target_h + top_invisible + bottom_invisible)

            return move_x, move_y, max(1, move_w), max(1, move_h)
        except Exception:
            return int(target_x), int(target_y), int(target_w), int(target_h)

    def apply_window_config_async(self, pid, account: Account, window_rect=None):
        def worker():
            client_name = get_account_client_title(account)
            desired_title = client_name

            try:
                grid_pixel_exact_mode = window_rect is not None
                if window_rect is not None:
                    pos_x = int(window_rect["x"])
                    pos_y = int(window_rect["y"])
                    width = max(1, int(window_rect["width"]))
                    height = max(1, int(window_rect["height"]))
                    resize_enabled = True
                else:
                    top_left = account.top_left or (0, 0)
                    pos_x = int(top_left[0])
                    pos_y = int(top_left[1])
                    width = max(320, int(account.width))
                    height = max(240, int(account.height))
                    resize_enabled = bool(account.resize_client)
            except Exception as e:
                log_history.append(f"Window Config - Invalid position/size values: {str(e)}")
                pos_x, pos_y, width, height = 0, 0, 800, 600
                grid_pixel_exact_mode = False
                resize_enabled = False


            duration_seconds = 5
            interval_seconds = 1.0
            attempts = int(duration_seconds / interval_seconds)
            last_hwnd = None
            last_snapshot = None

            log_history.append(
                f"Window Config - Enforcer started. PID={pid}, Character='{client_name}', "
                f"resize_client={resize_enabled}, grid_pixel_exact={grid_pixel_exact_mode}, "
                f"visible_target=X={pos_x}, Y={pos_y}, W={width}, H={height}, "
                f"duration={duration_seconds}s"
            )

            for attempt in range(1, attempts + 1):
                try:
                    if not self.is_process_running(pid):
                        log_history.append(f"Window Config - Enforcer stopped, process ended. PID={pid}")
                        return

                    windows = self.get_visible_windows_for_pid(pid)
                    if not windows:
                        if attempt in (1, 5, 10, 30, 60) or attempt % 60 == 0:
                            log_history.append(
                                f"Window Config - No visible window yet. PID={pid}, attempt={attempt}/{attempts}"
                            )
                        time.sleep(interval_seconds)
                        continue

                    windows.sort(key=lambda item: item.get("area", 0), reverse=True)
                    hwnd = windows[0]["hwnd"]

                    if hwnd != last_hwnd:
                        last_hwnd = hwnd
                        window_list = "; ".join(
                            f"HWND={w['hwnd']}, class='{w['class_name']}', title='{w['title']}', rect={w['rect']}"
                            for w in windows[:5]
                        )
                        log_history.append(
                            f"Window Config - Main window selected/changed. PID={pid}, {window_list}"
                        )


                    try:
                        win32gui.SetWindowText(hwnd, desired_title)
                    except Exception as e:
                        log_history.append(f"Window Config - SetWindowText failed: {str(e)}")


                    if resize_enabled:
                        try:
                            win32gui.ShowWindow(hwnd, 1)

                            if grid_pixel_exact_mode:
                                move_x, move_y, move_w, move_h = self.compute_outer_rect_for_visible_grid_bounds(
                                    hwnd,
                                    pos_x,
                                    pos_y,
                                    width,
                                    height,
                                )
                            else:
                                move_x, move_y, move_w, move_h = pos_x, pos_y, width, height


                            try:
                                user32.SetWindowPos(
                                    hwnd,
                                    HWND_TOP,
                                    int(move_x),
                                    int(move_y),
                                    int(move_w),
                                    int(move_h),
                                    SWP_NOZORDER | SWP_NOACTIVATE | 0x0040
                                )
                            except Exception:
                                pass
                            win32gui.MoveWindow(hwnd, int(move_x), int(move_y), int(move_w), int(move_h), True)
                        except Exception as e:
                            log_history.append(f"Window Config - Move/resize failed: {str(e)}")

                    try:
                        title_now = win32gui.GetWindowText(hwnd)
                        rect_now = win32gui.GetWindowRect(hwnd)
                    except Exception:
                        title_now = "<read failed>"
                        rect_now = (0, 0, 0, 0)

                    snapshot = (hwnd, title_now, rect_now)
                    should_log = False
                    if snapshot != last_snapshot:
                        should_log = True
                        last_snapshot = snapshot
                    if attempt in (1, 2, 5, 10, 30, 60, 120, 180, 240, 300):
                        should_log = True

                    if should_log:
                        log_history.append(
                            f"Window Config - Enforced {attempt}/{attempts}. "
                            f"HWND={hwnd}, title='{title_now}', rect={rect_now}"
                        )

                except Exception as e:
                    log_history.append(f"Window Config - Enforcer attempt {attempt}/{attempts} failed: {str(e)}")

                time.sleep(interval_seconds)

            log_history.append(f"Window Config - Enforcer finished for '{client_name}'.")

        threading.Thread(target=worker, daemon=True).start()

    def inject_dll(self, pid, dll_path):
        if not dll_path or not os.path.exists(dll_path):
            log_history.append("Inject DLL - Invalid DLL path")
            return False

        log_history.append(f"Inject DLL - Starting DLL injection for PID: {pid}")
        kernel32 = ctypes.windll.kernel32
        process_handle = None
        allocated_memory = None
        thread_handle = None

        try:

            process_handle = kernel32.OpenProcess(PROCESS_ALL_ACCESS, False, pid)
            if not process_handle:
                log_history.append(f"Inject DLL - Failed to open process. Error: {ctypes.get_last_error()}")
                return False


            loadlib_addr = kernel32.GetProcAddress(
                kernel32._handle,
                b"LoadLibraryA"
            )
            if not loadlib_addr:
                log_history.append("Inject DLL - Failed to get LoadLibraryA address")
                return False


            dll_path_bytes = dll_path.encode('ascii') + b'\0'
            path_size = len(dll_path_bytes)


            allocated_memory = kernel32.VirtualAllocEx(
                process_handle,
                0,
                path_size,
                VIRTUAL_MEM,
                PAGE_READWRITE
            )
            if not allocated_memory:
                log_history.append("Inject DLL - Failed to allocate memory")
                return False


            written = ctypes.c_size_t(0)
            write_success = kernel32.WriteProcessMemory(
                process_handle,
                allocated_memory,
                dll_path_bytes,
                path_size,
                ctypes.byref(written)
            )
            if not write_success or written.value != path_size:
                log_history.append("Inject DLL - Failed to write to process memory")
                return False


            thread_handle = kernel32.CreateRemoteThread(
                process_handle,
                None,
                0,
                loadlib_addr,
                allocated_memory,
                0,
                None
            )
            if not thread_handle:
                log_history.append("Inject DLL - Failed to create remote thread")
                return False


            kernel32.WaitForSingleObject(thread_handle, 5000)


            exit_code = ctypes.c_ulong(0)
            if kernel32.GetExitCodeThread(thread_handle, ctypes.byref(exit_code)):
                log_history.append(f"Inject DLL - Injection completed with exit code: {exit_code.value}")
                return exit_code.value != 0
            return False

        except Exception as e:
            log_history.append(f"Inject DLL - DLL injection failed with error: {str(e)}")
            return False

        finally:

            if thread_handle:
                kernel32.CloseHandle(thread_handle)
            if allocated_memory and process_handle:
                kernel32.VirtualFreeEx(process_handle, allocated_memory, 0, MEM_RELEASE)
            if process_handle:
                kernel32.CloseHandle(process_handle)

    def inject_gwtoolbox(self, pid, dll_path):
        dll_path = str(dll_path or "").strip()
        if not dll_path or not os.path.exists(dll_path):
            log_history.append("GWToolbox DLL path not valid")
            return False

        log_history.append(f"Injecting GWToolbox from: {dll_path}")
        result = self.inject_dll(pid, dll_path)
        log_history.append("GWToolbox injection " + ("successful" if result else "failed"))
        return result

    def inject_gmod(self, pid):
        gmod_path = os.path.join(current_directory, "Addons", gmod_dll_name)
        if not os.path.exists(gmod_path):
            log_history.append("gMod DLL path not valid")
            return False

        log_history.append(f"Injecting gMod from: {gmod_path}")
        result = self.inject_dll(pid, gmod_path)
        log_history.append("gMod injection " + ("successful" if result else "failed"))
        return result

    def is_process_running(self, pid):
        try:
            process = psutil.Process(pid)
            return process.status() == psutil.STATUS_RUNNING
        except psutil.NoSuchProcess:
            return False

    def attempt_dll_injection(self, pid, delay=0, dll_type="Py4GW", dll_path=""):

        if delay > 0:
            log_history.append(f"Waiting {delay} seconds before injecting {dll_type} DLL...")
            time.sleep(delay)

        if not self.is_process_running(pid):
            log_history.append(f"Process no longer running, skipping {dll_type} DLL injection")
            return False


        if dll_type == "Py4GW":
            log_history.append("Attempting Py4GW DLL injection...")
            dll_dir = os.path.join(current_directory, py4gw_dll_name)
            return self.inject_dll(pid,dll_dir)
        elif dll_type == "GWToolbox":
            log_history.append("Attempting GWToolbox DLL injection...")
            return self.inject_gwtoolbox(pid, dll_path)
        elif dll_type == "gMod":
            log_history.append("Attempting gMod DLL injection...")
            return self.inject_gmod(pid)

        log_history.append(f"Skipping {dll_type} DLL injection (not enabled).")
        return False

    def start_injection_thread(self, pid, account: Account):
        def injection_thread():
            try:
                if self.wait_for_gw_window(pid):
                    log_history.append("Injection - GW window found, waiting for initialization...")
                    time.sleep(5)

                    log_history.append(f"Injection - Starting Py4GW -> GWToolbox injection sequence for PID {pid}.")
                    py4gw_injected = False

                    if account.inject_py4gw:
                        ini_handler.write_key("settings", "autoexec_script", account.script_path)
                        py4gw_injected = self.attempt_dll_injection(pid, delay=0, dll_type="Py4GW")
                        set_account_dll_loaded_cache(account, pid, "Py4GW", py4gw_injected)
                        if py4gw_injected:
                            log_history.append("Py4GW DLL injection successful")
                        else:
                            log_history.append("Py4GW DLL injection failed")

                    if account.inject_gwtoolbox:
                        if account.inject_py4gw and not py4gw_injected:
                            log_history.append("GWToolbox DLL injection skipped because Py4GW injection failed.")
                        else:
                            if py4gw_injected:
                                delay_seconds = max(0.0, float(getattr(self, "py4gw_gwtoolbox_delay_seconds", 0.0)))
                                if delay_seconds > 0:
                                    log_history.append(f"Injection - Waiting {delay_seconds:g} seconds after Py4GW before GWToolbox.")
                                    time.sleep(delay_seconds)

                            gwtoolbox_path = str(getattr(account, "gwtoolbox_path", "") or "")
                            gwtoolbox_injected = self.attempt_dll_injection(pid, delay=0, dll_type="GWToolbox", dll_path=gwtoolbox_path)
                            set_account_dll_loaded_cache(account, pid, "GWToolbox", gwtoolbox_injected)
                            if gwtoolbox_injected:
                                log_history.append("GWToolbox DLL injection successful")
                            else:
                                log_history.append("GWToolbox DLL injection failed")

                    log_history.append(f"Injection - Finished Py4GW -> GWToolbox injection sequence for PID {pid}.")
                else:
                    log_history.append("Failed to detect GW window")
            except Exception as e:
                log_history.append(f"Error in injection thread: {str(e)}")

        threading.Thread(target=injection_thread, daemon=True).start()

    def create_modlist_for_gmod(self, account: Account):
        if not account.gw_path:
            log_history.append("Cannot create modlist.txt: gw_path not specified")
            return


        gw_dir = os.path.dirname(account.gw_path)
        modlist_path = os.path.join(gw_dir, "modlist.txt")


        mod_paths = account.gmod_mods


        try:
            with open(modlist_path, "w") as f:
                for mod_path in mod_paths:
                    f.write(f"{mod_path}\n")
            log_history.append(f"Updated modlist.txt with {len(mod_paths)} mods at {modlist_path}")
        except Exception as e:
            log_history.append(f"Error updating modlist.txt at {modlist_path}: {str(e)}")

    def start_team_launch_thread(self, team):
        def team_launch_thread():
            log_history.append(f"Launching team: {team.name}")
            for account in team.accounts:
                self.launch_gw(account)


                idle_time = max(0, int(getattr(team, "launch_delay_seconds", 15)))
                if idle_time > 0:
                    log_history.append(f"Team Launch - Waiting {idle_time}s before next account...")
                    for remaining in range(idle_time, 0, -1):
                        log_history[-1] = f"Idling... {remaining}s remaining to prevent log-in throttle"
                        time.sleep(1)
                    log_history.append("Idle complete, continuing...")

            log_history.append(f"Finished launching team: {team.name}")


        threading.Thread(target=team_launch_thread, daemon=True).start()

    def start_selected_accounts_thread(self, team, selected_accounts):
        def selected_launch_thread():
            if not selected_accounts:
                log_history.append(f"Launch Selected - No accounts selected for team: {team.name}")
                return

            log_history.append(f"Launch Selected - Launching {len(selected_accounts)} selected account(s) for team: {team.name}")
            for account in selected_accounts:
                invalidate_account_running_status(account)
                self.launch_gw(account)

                idle_time = max(0, int(getattr(team, "launch_delay_seconds", 15)))
                if idle_time > 0:
                    log_history.append(f"Launch Selected - Waiting {idle_time}s before next account...")
                    for remaining in range(idle_time, 0, -1):
                        log_history[-1] = f"Idling... {remaining}s remaining to prevent log-in throttle"
                        time.sleep(1)
                    log_history.append("Idle complete, continuing...")

            log_history.append(f"Launch Selected - Finished launching selected accounts for team: {team.name}")

        threading.Thread(target=selected_launch_thread, daemon=True).start()

    def start_missing_accounts_thread(self, team, missing_accounts):
        def missing_launch_thread():
            if not missing_accounts:
                log_history.append(f"Restart Missing - No missing selected accounts for team: {team.name}")
                return

            log_history.append(f"Restart Missing - Restarting {len(missing_accounts)} missing account(s) for team: {team.name}")
            for index, account in enumerate(missing_accounts):
                invalidate_account_running_status(account)
                self.launch_gw(account)

                idle_time = max(0, int(getattr(team, "launch_delay_seconds", 15)))
                if idle_time > 0 and index < len(missing_accounts) - 1:
                    log_history.append(f"Restart Missing - Waiting {idle_time}s before next account...")
                    for remaining in range(idle_time, 0, -1):
                        log_history[-1] = f"Restart Missing - Idling... {remaining}s remaining"
                        time.sleep(1)
                    log_history.append("Restart Missing - Idle complete, continuing...")

            log_history.append(f"Restart Missing - Finished restarting missing accounts for team: {team.name}")

        threading.Thread(target=missing_launch_thread, daemon=True).start()

    def start_selected_accounts_grid_thread(self, team, selected_accounts, monitor, rows, cols, slot_indices=None):
        def grid_launch_thread():
            if not selected_accounts:
                log_history.append(f"Grid Launch - No accounts selected for team: {team.name}")
                return

            rows_safe = max(1, int(rows))
            cols_safe = max(1, int(cols))
            capacity = rows_safe * cols_safe

            if capacity < len(selected_accounts):
                log_history.append(
                    f"Grid Launch - Layout {rows_safe}x{cols_safe} is too small for {len(selected_accounts)} accounts."
                )
                return

            launch_slot_indices = list(slot_indices or range(len(selected_accounts)))
            if len(launch_slot_indices) != len(selected_accounts):
                launch_slot_indices = list(range(len(selected_accounts)))

            rects = compute_grid_window_rects(monitor, rows_safe, cols_safe, capacity, monitor_index)
            monitor_label = monitor.get("label", "Monitor")
            log_history.append(
                f"Grid Launch - Launching {len(selected_accounts)} account(s) on {monitor_label} "
                f"with layout {rows_safe}x{cols_safe}."
            )

            for index, account in enumerate(selected_accounts):
                slot_index = max(0, min(capacity - 1, int(launch_slot_indices[index])))
                window_rect = rects[slot_index]
                log_history.append(
                    f"Grid Launch - {index + 1}/{len(selected_accounts)} {account.character_name}: "
                    f"Slot={slot_index + 1} X={window_rect['x']} Y={window_rect['y']} "
                    f"W={window_rect['width']} H={window_rect['height']}"
                )
                invalidate_account_running_status(account)
                self.launch_gw(account, window_rect=window_rect)

                idle_time = max(0, int(getattr(team, "launch_delay_seconds", 15)))
                if idle_time > 0 and index < len(selected_accounts) - 1:
                    log_history.append(f"Grid Launch - Waiting {idle_time}s before next account...")
                    for remaining in range(idle_time, 0, -1):
                        log_history[-1] = f"Grid Launch - Idling... {remaining}s remaining"
                        time.sleep(1)
                    log_history.append("Grid Launch - Idle complete, continuing...")

            log_history.append(f"Grid Launch - Finished launching selected accounts for team: {team.name}")

        threading.Thread(target=grid_launch_thread, daemon=True).start()

    def start_multi_monitor_grid_thread(self, team, launch_plan):
        def multi_grid_launch_thread():
            if not launch_plan:
                log_history.append(f"Grid Launch - No accounts selected for team: {team.name}")
                return

            rect_cache = {}
            log_history.append(
                f"Grid Launch - Launching {len(launch_plan)} account(s) across "
                f"{len(set(item.get('monitor_index') for item in launch_plan))} monitor(s)."
            )

            for index, item in enumerate(launch_plan):
                account = item.get("account")
                monitor = item.get("monitor") or {}
                monitor_index = int(item.get("monitor_index", 0))
                rows_safe = max(1, int(item.get("rows", 1)))
                cols_safe = max(1, int(item.get("cols", 1)))
                capacity = rows_safe * cols_safe
                slot_index = max(0, min(capacity - 1, int(item.get("slot_index", index))))

                cache_key = (monitor_index, rows_safe, cols_safe)
                if cache_key not in rect_cache:
                    rect_cache[cache_key] = compute_grid_window_rects(monitor, rows_safe, cols_safe, capacity, monitor_index)

                rects = rect_cache[cache_key]
                window_rect = rects[slot_index]
                monitor_label = monitor.get("label", f"Monitor {monitor_index + 1}")

                log_history.append(
                    f"Grid Launch - {index + 1}/{len(launch_plan)} {account.character_name}: "
                    f"{monitor_label} Slot={slot_index + 1} "
                    f"X={window_rect['x']} Y={window_rect['y']} "
                    f"W={window_rect['width']} H={window_rect['height']}"
                )

                invalidate_account_running_status(account)
                self.launch_gw(account, window_rect=window_rect)

                idle_time = max(0, int(getattr(team, "launch_delay_seconds", 15)))
                if idle_time > 0 and index < len(launch_plan) - 1:
                    log_history.append(f"Grid Launch - Waiting {idle_time}s before next account...")
                    for remaining in range(idle_time, 0, -1):
                        log_history[-1] = f"Grid Launch - Idling... {remaining}s remaining"
                        time.sleep(1)
                    log_history.append("Grid Launch - Idle complete, continuing...")

            log_history.append(f"Grid Launch - Finished multi-monitor launch for team: {team.name}")

        threading.Thread(target=multi_grid_launch_thread, daemon=True).start()

    def launch_gw(self, account: Account, window_rect=None):
        if not ensure_credentials_unlocked_for_action(f"Launch '{account.character_name}'"):
            return

        patcher = Patcher()
        try:
            pid = patcher.launch_and_patch(
                account.gw_path,
                account.email,
                account.password,
                account.character_name,
                account.extra_args,
                account.run_as_admin
            )

            if pid is None:
                log_history.append("Launch GW - Failed to launch or patch Guild Wars.")
                return

            log_history.append(f"Launch GW - Launched and patched GW with PID: {pid}")
            self.active_pids.append((account, pid))
            register_launcher_managed_client(account, pid)
            account_running_status_cache[id(account)] = {
                "checked_at": time.time(),
                "running": True,
                "pid": pid,
            }


            self.apply_window_config_async(pid, account, window_rect=window_rect)


            if account.inject_gmod:
                self.create_modlist_for_gmod(account)
                if self.attempt_dll_injection(pid, dll_type="gMod"):
                    log_history.append("gMod DLL injection successful")
                    time.sleep(3)
                else:
                    log_history.append("gMod DLL injection failed")

            if account.inject_py4gw or account.inject_gwtoolbox:
                self.start_injection_thread(pid, account)


        except Exception as e:
            log_history.append(f"Error launching GW: {str(e)}")


def ui_color(name: str):
    if normalize_launcher_theme_mode(ui_theme_mode) == THEME_LIGHT:
        colors = {

            "app_bg": (0.965, 0.972, 0.982, 1.00),
            "surface": (1.000, 1.000, 1.000, 1.00),
            "surface_alt": (0.940, 0.952, 0.968, 1.00),
            "surface_row": (0.930, 0.944, 0.964, 1.00),
            "surface_mint": (0.925, 0.965, 0.945, 1.00),


            "team_row_bg": (0.930, 0.944, 0.964, 1.00),
            "team_row_hover": (0.890, 0.918, 0.958, 1.00),
            "team_label": (0.090, 0.120, 0.170, 1.00),
            "team_count_badge": (0.245, 0.370, 0.735, 1.00),


            "input_bg": (0.930, 0.944, 0.964, 1.00),
            "input_hover": (0.890, 0.918, 0.958, 1.00),
            "input_active": (0.850, 0.895, 0.960, 1.00),


            "accent": (0.245, 0.370, 0.735, 1.00),
            "accent_ocean": (0.245, 0.370, 0.735, 1.00),
            "accent_2": (0.245, 0.370, 0.735, 1.00),
            "accent_sage": (0.125, 0.520, 0.350, 1.00),
            "accent_terracotta": (0.820, 0.180, 0.180, 1.00),


            "text": (0.095, 0.120, 0.160, 1.00),
            "muted": (0.000, 0.000, 0.000, 1.00),
            "disabled": (0.000, 0.000, 0.000, 1.00),
            "border": (0.760, 0.805, 0.860, 1.00),
            "border_strong": (0.630, 0.685, 0.755, 1.00),

            "info_label": (0.000, 0.000, 0.000, 1.00),
            "badge": (0.000, 0.000, 0.000, 1.00),
            "card_bg": (1.000, 1.000, 1.000, 1.00),
            "console_bg": (0.940, 0.952, 0.968, 1.00),


            "success": (0.125, 0.520, 0.350, 1.00),
            "warning": (0.750, 0.470, 0.120, 1.00),
            "danger": (0.820, 0.180, 0.180, 1.00),


            "primary_button": (0.245, 0.370, 0.735, 1.00),
            "primary_button_hovered": (0.210, 0.320, 0.650, 1.00),
            "primary_button_active": (0.170, 0.265, 0.545, 1.00),
            "success_button": (0.125, 0.520, 0.350, 1.00),
            "success_button_hovered": (0.095, 0.440, 0.290, 1.00),
            "success_button_active": (0.070, 0.360, 0.235, 1.00),
            "secondary_button": (0.245, 0.370, 0.735, 1.00),
            "secondary_button_hovered": (0.210, 0.320, 0.650, 1.00),
            "secondary_button_active": (0.170, 0.265, 0.545, 1.00),
            "danger_button": (0.820, 0.180, 0.180, 1.00),
            "danger_button_hovered": (0.700, 0.130, 0.130, 1.00),
            "danger_button_active": (0.570, 0.095, 0.095, 1.00),
            "button_text_light": (1.000, 1.000, 1.000, 1.00),
            "button_text_dark": (0.095, 0.120, 0.160, 1.00),

            "theme_button": (0.245, 0.370, 0.735, 1.00),
            "theme_button_hovered": (0.210, 0.320, 0.650, 1.00),
            "theme_button_active": (0.170, 0.265, 0.545, 1.00),
            "theme_button_text": (1.000, 1.000, 1.000, 1.00),
        }
    else:
        colors = {

            "app_bg": (0.055, 0.065, 0.085, 1.00),
            "surface": (0.085, 0.100, 0.130, 1.00),
            "surface_alt": (0.105, 0.122, 0.158, 1.00),
            "surface_row": (0.120, 0.138, 0.178, 1.00),
            "surface_mint": (0.075, 0.145, 0.120, 1.00),


            "team_row_bg": (0.105, 0.122, 0.158, 1.00),
            "team_row_hover": (0.140, 0.168, 0.220, 1.00),
            "team_label": (0.925, 0.950, 0.985, 1.00),
            "team_count_badge": (0.470, 0.650, 1.000, 1.00),


            "input_bg": (0.120, 0.138, 0.178, 1.00),
            "input_hover": (0.150, 0.175, 0.230, 1.00),
            "input_active": (0.180, 0.220, 0.300, 1.00),


            "accent": (0.470, 0.650, 1.000, 1.00),
            "accent_ocean": (0.470, 0.650, 1.000, 1.00),
            "accent_2": (0.470, 0.650, 1.000, 1.00),
            "accent_sage": (0.320, 0.820, 0.560, 1.00),
            "accent_terracotta": (1.000, 0.335, 0.335, 1.00),


            "text": (0.925, 0.950, 0.985, 1.00),
            "muted": (0.925, 0.950, 0.985, 1.00),
            "disabled": (0.925, 0.950, 0.985, 1.00),
            "border": (0.210, 0.240, 0.300, 1.00),
            "border_strong": (0.300, 0.345, 0.430, 1.00),

            "info_label": (0.925, 0.950, 0.985, 1.00),
            "badge": (0.925, 0.950, 0.985, 1.00),
            "card_bg": (0.085, 0.100, 0.130, 0.94),
            "console_bg": (0.055, 0.065, 0.085, 0.96),


            "success": (0.320, 0.820, 0.560, 1.00),
            "warning": (1.000, 0.700, 0.250, 1.00),
            "danger": (1.000, 0.335, 0.335, 1.00),


            "primary_button": (0.260, 0.410, 0.780, 1.00),
            "primary_button_hovered": (0.310, 0.480, 0.900, 1.00),
            "primary_button_active": (0.205, 0.335, 0.650, 1.00),
            "success_button": (0.160, 0.520, 0.300, 1.00),
            "success_button_hovered": (0.210, 0.640, 0.370, 1.00),
            "success_button_active": (0.105, 0.400, 0.230, 1.00),
            "secondary_button": (0.260, 0.410, 0.780, 1.00),
            "secondary_button_hovered": (0.310, 0.480, 0.900, 1.00),
            "secondary_button_active": (0.205, 0.335, 0.650, 1.00),
            "danger_button": (0.700, 0.150, 0.150, 1.00),
            "danger_button_hovered": (0.850, 0.205, 0.205, 1.00),
            "danger_button_active": (0.560, 0.100, 0.100, 1.00),
            "button_text_light": (0.985, 0.992, 1.000, 1.00),
            "button_text_dark": (0.925, 0.950, 0.985, 1.00),

            "theme_button": (0.260, 0.410, 0.780, 1.00),
            "theme_button_hovered": (0.310, 0.480, 0.900, 1.00),
            "theme_button_active": (0.205, 0.335, 0.650, 1.00),
            "theme_button_text": (0.985, 0.992, 1.000, 1.00),
        }
    return colors.get(name, colors["muted"])

def set_launcher_theme_mode(theme_mode: str):
    global ui_theme_mode, applied_ui_theme_mode, modern_style_applied

    theme_mode = normalize_launcher_theme_mode(theme_mode)
    if normalize_launcher_theme_mode(ui_theme_mode) == theme_mode:
        return

    ui_theme_mode = theme_mode
    write_launcher_theme_mode(ui_theme_mode)
    applied_ui_theme_mode = None
    modern_style_applied = False
    log_history.append(f"Theme - Changed to {get_launcher_theme_label(ui_theme_mode)}.")


def render_theme_selector_inline():
    is_light = normalize_launcher_theme_mode(ui_theme_mode) == THEME_LIGHT
    current_label = "White Mode" if is_light else "Dark Mode"
    next_mode = THEME_DARK if is_light else THEME_LIGHT

    pushed = 0
    try:
        pushed += _push_style_color_safe("button", ui_color("theme_button"))
        pushed += _push_style_color_safe("button_hovered", ui_color("theme_button_hovered"))
        pushed += _push_style_color_safe("button_active", ui_color("theme_button_active"))
        pushed += _push_style_color_safe("text", ui_color("theme_button_text"))
    except Exception:
        pushed = 0

    pressed = False
    try:
        pressed = imgui.button(f"{current_label}##theme_toggle_button", imgui.ImVec2(112, 0))
    except TypeError:
        pressed = imgui.button(f"{current_label}##theme_toggle_button")

    if pushed:
        try:
            imgui.pop_style_color(pushed)
        except Exception:
            pass

    if pressed:
        set_launcher_theme_mode(next_mode)


def ui_section_header(title: str, subtitle: str = ""):
    imgui.push_style_color(imgui.Col_.text, ui_color("accent"))
    imgui.text(title)
    imgui.pop_style_color()
    if subtitle:
        imgui.same_line()
        imgui.push_style_color(imgui.Col_.text, ui_color("muted"))
        imgui.text(subtitle)
        imgui.pop_style_color()
    imgui.separator()


def ui_info_line(label: str, value: str):
    imgui.push_style_color(imgui.Col_.text, ui_color("info_label"))
    imgui.text(f"{label}:")
    imgui.pop_style_color()
    imgui.same_line()
    imgui.text(str(value))


def _imgui_enum_int(enum_value) -> int:
    try:
        return int(enum_value.value)
    except Exception:
        try:
            return int(enum_value)
        except Exception:
            return 0


def ui_begin_card(card_id: str, height: float = 90.0, no_scrollbar: bool = False):
    imgui.push_style_color(imgui.Col_.child_bg, ui_color("card_bg"))

    window_flags = 0
    if no_scrollbar:
        try:
            window_flags |= _imgui_enum_int(imgui.WindowFlags_.no_scrollbar)
            window_flags |= _imgui_enum_int(imgui.WindowFlags_.no_scroll_with_mouse)
        except Exception:
            window_flags = 0

    imgui.begin_child(
        str_id=card_id,
        size=imgui.ImVec2(0, height),
        child_flags=int(imgui.ChildFlags_.borders.value),
        window_flags=window_flags,
    )


def ui_end_card():
    imgui.end_child()
    imgui.pop_style_color()


def ui_form_label(label: str):
    imgui.push_style_color(imgui.Col_.text, ui_color("info_label"))
    imgui.text(str(label))
    imgui.pop_style_color()


def ui_responsive_input_width(max_width: float = 300.0, min_width: float = 130.0, reserve_width: float = 130.0) -> float:
    try:
        avail = imgui.get_content_region_avail()
        avail_x = float(avail.x if hasattr(avail, "x") else avail[0])
        return max(min_width, min(max_width, avail_x - reserve_width))
    except Exception:
        return max_width


def ui_hint_text(text_value: str):
    imgui.push_style_color(imgui.Col_.text, ui_color("muted"))
    imgui.text_wrapped(str(text_value))
    imgui.pop_style_color()


def ui_subsection_title(title: str, subtitle: str = ""):
    imgui.push_style_color(imgui.Col_.text, ui_color("accent"))
    imgui.text(str(title))
    imgui.pop_style_color()
    if subtitle:
        imgui.same_line()
        imgui.push_style_color(imgui.Col_.text, ui_color("muted"))
        imgui.text(str(subtitle))
        imgui.pop_style_color()


def ui_text_muted(text_value: str):
    imgui.push_style_color(imgui.Col_.text, ui_color("muted"))
    imgui.text(str(text_value))
    imgui.pop_style_color()


def ui_text_warning(text_value: str):
    imgui.push_style_color(imgui.Col_.text, ui_color("warning"))
    imgui.text(str(text_value))
    imgui.pop_style_color()


def ui_text_accent(text_value: str):
    imgui.push_style_color(imgui.Col_.text, ui_color("accent"))
    imgui.text(str(text_value))
    imgui.pop_style_color()


def ui_small_badge(text_value: str):
    imgui.same_line()
    imgui.push_style_color(imgui.Col_.text, ui_color("badge"))
    imgui.text(f"[{text_value}]")
    imgui.pop_style_color()


def _push_style_color_safe(color_name: str, color_value) -> int:
    try:
        color_enum = getattr(imgui.Col_, color_name)
        imgui.push_style_color(color_enum, color_value)
        return 1
    except Exception:
        return 0


def push_button_style(kind: str = "secondary") -> int:
    kind = (kind or "secondary").lower()
    pushed = 0

    if kind in ("primary", "launch", "create", "save"):
        pushed += _push_style_color_safe("button", ui_color("primary_button"))
        pushed += _push_style_color_safe("button_hovered", ui_color("primary_button_hovered"))
        pushed += _push_style_color_safe("button_active", ui_color("primary_button_active"))
        pushed += _push_style_color_safe("text", ui_color("button_text_light"))
    elif kind in ("success", "selected", "active", "active_monitor"):
        pushed += _push_style_color_safe("button", ui_color("success_button"))
        pushed += _push_style_color_safe("button_hovered", ui_color("success_button_hovered"))
        pushed += _push_style_color_safe("button_active", ui_color("success_button_active"))
        pushed += _push_style_color_safe("text", ui_color("button_text_light"))
    elif kind in ("danger", "delete", "destructive"):
        pushed += _push_style_color_safe("button", ui_color("danger_button"))
        pushed += _push_style_color_safe("button_hovered", ui_color("danger_button_hovered"))
        pushed += _push_style_color_safe("button_active", ui_color("danger_button_active"))
        pushed += _push_style_color_safe("text", ui_color("button_text_light"))
    else:
        pushed += _push_style_color_safe("button", ui_color("secondary_button"))
        pushed += _push_style_color_safe("button_hovered", ui_color("secondary_button_hovered"))
        pushed += _push_style_color_safe("button_active", ui_color("secondary_button_active"))
        pushed += _push_style_color_safe("text", ui_color("button_text_light"))

    return pushed


def pop_button_style(pushed_count: int):
    if pushed_count:
        try:
            imgui.pop_style_color(pushed_count)
        except Exception:
            pass


def themed_button(label: str, kind: str = "secondary", size=None) -> bool:
    pushed = push_button_style(kind)
    try:
        if size is not None:
            try:
                return imgui.button(label, size)
            except TypeError:
                return imgui.button(label)
        return imgui.button(label)
    finally:
        pop_button_style(pushed)


def push_launcher_theme_colors() -> int:
    pushed = 0
    is_light = normalize_launcher_theme_mode(ui_theme_mode) == THEME_LIGHT

    if is_light:
        theme_colors = {
            "text": ui_color("text"),
            "text_disabled": ui_color("disabled"),
            "window_bg": ui_color("app_bg"),
            "child_bg": ui_color("card_bg"),
            "popup_bg": ui_color("surface"),
            "border": ui_color("border"),
            "border_shadow": (0.000, 0.000, 0.000, 0.00),

            "frame_bg": ui_color("input_bg"),
            "frame_bg_hovered": ui_color("input_hover"),
            "frame_bg_active": ui_color("input_active"),

            "button": ui_color("secondary_button"),
            "button_hovered": ui_color("secondary_button_hovered"),
            "button_active": ui_color("secondary_button_active"),

            "header": ui_color("surface_row"),
            "header_hovered": ui_color("team_row_hover"),
            "header_active": (0.820, 0.855, 0.905, 1.00),

            "separator": ui_color("border"),
            "separator_hovered": ui_color("accent"),
            "separator_active": ui_color("accent"),

            "tab": ui_color("surface_alt"),
            "tab_hovered": ui_color("team_row_hover"),
            "tab_active": ui_color("surface"),
            "tab_unfocused": ui_color("surface_alt"),
            "tab_unfocused_active": ui_color("surface"),

            "title_bg": ui_color("surface_alt"),
            "title_bg_active": (0.890, 0.918, 0.958, 1.00),
            "title_bg_collapsed": ui_color("surface_alt"),

            "menu_bar_bg": ui_color("surface_alt"),

            "scrollbar_bg": ui_color("surface_alt"),
            "scrollbar_grab": (0.760, 0.805, 0.860, 1.00),
            "scrollbar_grab_hovered": (0.630, 0.685, 0.755, 1.00),
            "scrollbar_grab_active": (0.500, 0.560, 0.640, 1.00),

            "check_mark": ui_color("success"),
            "slider_grab": ui_color("accent"),
            "slider_grab_active": ui_color("primary_button_hovered"),

            "resize_grip": (0.245, 0.370, 0.735, 0.18),
            "resize_grip_hovered": (0.245, 0.370, 0.735, 0.38),
            "resize_grip_active": (0.245, 0.370, 0.735, 0.65),

            "text_selected_bg": (0.245, 0.370, 0.735, 0.25),
            "nav_highlight": (0.245, 0.370, 0.735, 0.38),
            "docking_preview": (0.245, 0.370, 0.735, 0.32),
        }
    else:
        theme_colors = {
            "text": ui_color("text"),
            "text_disabled": ui_color("disabled"),
            "window_bg": ui_color("app_bg"),
            "child_bg": ui_color("card_bg"),
            "popup_bg": ui_color("surface"),
            "border": ui_color("border"),
            "border_shadow": (0.000, 0.000, 0.000, 0.00),

            "frame_bg": ui_color("input_bg"),
            "frame_bg_hovered": ui_color("input_hover"),
            "frame_bg_active": ui_color("input_active"),

            "button": ui_color("secondary_button"),
            "button_hovered": ui_color("secondary_button_hovered"),
            "button_active": ui_color("secondary_button_active"),

            "header": ui_color("surface_row"),
            "header_hovered": ui_color("team_row_hover"),
            "header_active": (0.180, 0.220, 0.300, 1.00),

            "separator": ui_color("border"),
            "separator_hovered": ui_color("accent"),
            "separator_active": ui_color("accent"),

            "tab": ui_color("surface_alt"),
            "tab_hovered": ui_color("team_row_hover"),
            "tab_active": ui_color("surface"),
            "tab_unfocused": ui_color("surface_alt"),
            "tab_unfocused_active": ui_color("surface"),

            "title_bg": ui_color("surface_alt"),
            "title_bg_active": (0.120, 0.138, 0.178, 1.00),
            "title_bg_collapsed": ui_color("surface_alt"),

            "menu_bar_bg": ui_color("surface_alt"),

            "scrollbar_bg": ui_color("app_bg"),
            "scrollbar_grab": (0.210, 0.240, 0.300, 1.00),
            "scrollbar_grab_hovered": (0.300, 0.345, 0.430, 1.00),
            "scrollbar_grab_active": (0.400, 0.465, 0.580, 1.00),

            "check_mark": ui_color("success"),
            "slider_grab": ui_color("accent"),
            "slider_grab_active": ui_color("primary_button_hovered"),

            "resize_grip": (0.470, 0.650, 1.000, 0.16),
            "resize_grip_hovered": (0.470, 0.650, 1.000, 0.35),
            "resize_grip_active": (0.470, 0.650, 1.000, 0.60),

            "text_selected_bg": (0.470, 0.650, 1.000, 0.22),
            "nav_highlight": (0.470, 0.650, 1.000, 0.34),
            "docking_preview": (0.470, 0.650, 1.000, 0.28),
        }

    for color_name, color_value in theme_colors.items():
        pushed += _push_style_color_safe(color_name, color_value)

    return pushed

def pop_launcher_theme_colors(pushed_count: int):
    if pushed_count:
        try:
            imgui.pop_style_color(pushed_count)
        except Exception:
            pass


def render_with_launcher_theme(gui_function):
    pushed_count = push_launcher_theme_colors()
    try:
        gui_function()
    finally:
        pop_launcher_theme_colors(pushed_count)


def show_team_view_themed():
    render_with_launcher_theme(show_team_view)


def show_configuration_content_themed():
    render_with_launcher_theme(show_configuration_content)


def show_account_content_themed():
    render_with_launcher_theme(show_account_content)


def show_log_console_themed():
    render_with_launcher_theme(show_log_console)


def apply_launcher_imgui_style(theme_mode: str = None):
    mode = normalize_launcher_theme_mode(theme_mode if theme_mode is not None else ui_theme_mode)
    try:
        try:
            if mode == THEME_LIGHT:
                imgui.style_colors_light()
            else:
                imgui.style_colors_dark()
        except Exception as palette_error:
            log_history.append(f"Style - Built-in palette skipped: {str(palette_error)}")

        style = imgui.get_style()


        for attr, value in [
            ("window_rounding", 5.0),
            ("child_rounding", 4.0),
            ("frame_rounding", 4.0),
            ("grab_rounding", 4.0),
            ("popup_rounding", 5.0),
            ("scrollbar_rounding", 5.0),
            ("tab_rounding", 4.0),
            ("window_border_size", 1.0),
            ("child_border_size", 1.0),
            ("frame_border_size", 1.0),
            ("indent_spacing", 12.0),
            ("scrollbar_size", 12.0),
        ]:
            try:
                setattr(style, attr, value)
            except Exception:
                pass

        try:
            style.item_spacing = imgui.ImVec2(6, 4)
        except Exception:
            pass

        try:
            style.frame_padding = imgui.ImVec2(6, 3)
        except Exception:
            pass

        try:
            style.window_padding = imgui.ImVec2(8, 6)
        except Exception:
            pass

        try:
            style.cell_padding = imgui.ImVec2(4, 2)
        except Exception:
            pass

        try:
            io = imgui.get_io()
            io.font_global_scale = 0.84
        except Exception:
            pass

        log_history.append(f"Style - {get_launcher_theme_label(mode)} applied.")
    except Exception as e:
        log_history.append(f"Style - Failed to apply {get_launcher_theme_label(mode)}: {str(e)}")


def apply_modern_imgui_style():
    apply_launcher_imgui_style(ui_theme_mode)


DEFAULT_ADVANCED_WINDOW_WIDTH = 980.0
DEFAULT_ADVANCED_WINDOW_HEIGHT = 660.0
DEFAULT_ADVANCED_LEFT_PANEL_WIDTH = 360.0
DEFAULT_ADVANCED_CONSOLE_HEIGHT = 160.0
DEFAULT_ADVANCED_LEFT_PANEL_RATIO = DEFAULT_ADVANCED_LEFT_PANEL_WIDTH / DEFAULT_ADVANCED_WINDOW_WIDTH
DEFAULT_ADVANCED_CONSOLE_HEIGHT_RATIO = DEFAULT_ADVANCED_CONSOLE_HEIGHT / DEFAULT_ADVANCED_WINDOW_HEIGHT
DEFAULT_ADVANCED_CONFIG_TAB = "account"
LAYOUT_CONFIG_SECTION = "Py4GW_Launcher"


log_hide_clear_names = str(
    ini_handler.read_key(LAYOUT_CONFIG_SECTION, "log_hide_clear_names", "true")
).strip().lower() not in ("0", "false", "no", "off")


def write_launcher_layout_value_if_changed(key: str, value) -> None:
    try:
        new_value = str(value)
        current_value = ini_handler.read_key(LAYOUT_CONFIG_SECTION, key, "")
        if current_value != new_value:
            ini_handler.write_key(LAYOUT_CONFIG_SECTION, key, new_value)
    except Exception as e:
        log_history.append(f"Layout - Failed to save {key}: {str(e)}")


def write_existing_launcher_layout_value_if_changed(key: str, value) -> None:
    try:
        if not ini_handler.has_key(LAYOUT_CONFIG_SECTION, key):
            return
        write_launcher_layout_value_if_changed(key, value)
    except Exception as e:
        log_history.append(f"Layout - Failed to update existing {key}: {str(e)}")


launcher_left_panel_width = ini_handler.read_float(
    LAYOUT_CONFIG_SECTION,
    "advanced_left_panel_width",
    DEFAULT_ADVANCED_LEFT_PANEL_WIDTH,
)
launcher_console_height = ini_handler.read_float(
    LAYOUT_CONFIG_SECTION,
    "advanced_console_height",
    DEFAULT_ADVANCED_CONSOLE_HEIGHT,
)


launcher_left_panel_ratio = ini_handler.read_float(
    LAYOUT_CONFIG_SECTION,
    "advanced_left_panel_ratio",
    launcher_left_panel_width / DEFAULT_ADVANCED_WINDOW_WIDTH,
)
launcher_console_height_ratio = ini_handler.read_float(
    LAYOUT_CONFIG_SECTION,
    "advanced_console_height_ratio",
    launcher_console_height / DEFAULT_ADVANCED_WINDOW_HEIGHT,
)

launcher_left_panel_ratio = max(0.12, min(0.82, float(launcher_left_panel_ratio)))
launcher_console_height_ratio = max(0.10, min(0.60, float(launcher_console_height_ratio)))

launcher_config_tab = ini_handler.read_key(
    LAYOUT_CONFIG_SECTION,
    "advanced_config_tab",
    DEFAULT_ADVANCED_CONFIG_TAB,
)
pending_reset_layout_confirm = False


grid_account_order_keys = []
grid_monitor_slot_keys = {}
grid_monitor_slot_keys_loaded = False
grid_preview_drag_source_index = None
grid_preview_drag_source_location = None
grid_preview_drag_source_key = None
grid_preview_drag_had_motion = False
grid_click_swap_source_location = None
grid_click_swap_source_key = None
grid_monitor_custom_merge_rects = {}
grid_monitor_custom_merge_rects_loaded = False
grid_custom_merge_active_indices = set()
grid_custom_merge_drag_start = None
grid_custom_merge_drag_current = None
grid_saved_layouts = {}
grid_saved_layouts_loaded = False
grid_saved_layout_selected = ""
grid_saved_layout_name = ""
grid_saved_layout_rename_name = ""
grid_saved_layout_source_monitor_index = 0
grid_saved_layout_target_monitor_index = 0
grid_saved_layout_delete_confirm_name = ""
grid_saved_layout_delete_confirm_requested_at = 0.0
grid_custom_capacity_warning_message = ""
gw_exe_update_enabled = ini_handler.read_bool(LAYOUT_CONFIG_SECTION, "gw_exe_update_enabled", False)
gw_exe_update_status_by_path = {}
gw_exe_update_latest_version_id = None
gw_exe_update_check_thread = None
gw_exe_update_thread = None
gw_exe_update_lock = threading.Lock()
gw_exe_update_confirm_path = ""
gw_exe_update_confirm_requested_at = 0.0
gw_exe_update_last_auto_check = 0.0
gw_exe_update_locked_delay_last_log = 0.0
gw_exe_cached_version_selected = ini_handler.read_int(LAYOUT_CONFIG_SECTION, "gw_exe_cached_version_selected", 0)
gw_exe_cached_install_target_index = max(0, ini_handler.read_int(LAYOUT_CONFIG_SECTION, "gw_exe_cached_install_target_index", 0))
gw_exe_install_cached_confirm_version = 0
gw_exe_install_cached_confirm_requested_at = 0.0
gw_exe_install_cached_confirm_paths = []
gw_exe_redownload_folder = ini_handler.read_key(LAYOUT_CONFIG_SECTION, "gw_exe_redownload_folder", "")
gw_exe_redownload_run_image = ini_handler.read_bool(LAYOUT_CONFIG_SECTION, "gw_exe_redownload_run_image", True)
gw_exe_redownload_confirm_requested_at = 0.0
gw_exe_redownload_status = ""
gw_exe_cache_verify_results = {}
gw_exe_cache_verify_thread = None
gw_exe_cache_redownload_latest_confirm_requested_at = 0.0
gw_exe_cache_redownload_latest_status = ""
perf_debug_enabled = ini_handler.read_bool(LAYOUT_CONFIG_SECTION, "perf_debug_enabled", False)
perf_debug_metrics = {}
perf_debug_lock = threading.Lock()


def _parse_int_csv(value: str, default_values=None):
    result = []
    try:
        for part in str(value or "").split(","):
            part = part.strip()
            if not part:
                continue
            result.append(int(part))
    except Exception:
        result = []

    if not result and default_values is not None:
        return list(default_values)
    return result


def _format_int_csv(values) -> str:
    return ",".join(str(int(value)) for value in values)


def perf_debug_record_elapsed(name, start_time, detail=""):
    if not perf_debug_enabled:
        return
    try:
        elapsed_ms = (time.perf_counter() - float(start_time)) * 1000.0
        key = str(name or "unknown")
        with perf_debug_lock:
            current = dict(perf_debug_metrics.get(key, {}))
            count = int(current.get("count", 0)) + 1
            total_ms = float(current.get("total_ms", 0.0)) + elapsed_ms
            max_ms = max(float(current.get("max_ms", 0.0)), elapsed_ms)
            current["count"] = count
            current["total_ms"] = total_ms
            current["avg_ms"] = total_ms / max(1, count)
            current["last_ms"] = elapsed_ms
            current["max_ms"] = max_ms
            current["last_at"] = time.time()
            current["detail"] = str(detail or "")[:160]
            perf_debug_metrics[key] = current
    except Exception:
        pass


def perf_debug_call(name, func, *args, **kwargs):
    if not perf_debug_enabled:
        return func(*args, **kwargs)
    start_time = time.perf_counter()
    try:
        return func(*args, **kwargs)
    finally:
        perf_debug_record_elapsed(name, start_time)


def perf_debug_reset_metrics():
    try:
        with perf_debug_lock:
            perf_debug_metrics.clear()
    except Exception:
        pass


def perf_debug_get_rows():
    try:
        with perf_debug_lock:
            rows = [(name, dict(values)) for name, values in perf_debug_metrics.items()]
        rows.sort(key=lambda item: float(item[1].get("total_ms", 0.0)), reverse=True)
        return rows
    except Exception:
        return []


grid_selected_monitor_index = max(0, ini_handler.read_int(LAYOUT_CONFIG_SECTION, "grid_monitor_index", 0))
grid_selected_monitor_indices = _parse_int_csv(
    ini_handler.read_key(LAYOUT_CONFIG_SECTION, "grid_monitor_indices", ""),
    [grid_selected_monitor_index],
)


grid_layout_mode = ini_handler.read_key(LAYOUT_CONFIG_SECTION, "grid_layout_mode", "auto")
grid_rows = max(1, ini_handler.read_int(LAYOUT_CONFIG_SECTION, "grid_rows", 1))
grid_cols = max(1, ini_handler.read_int(LAYOUT_CONFIG_SECTION, "grid_cols", 1))
grid_monitor_layouts = {}


def _imgui_avail_size(default_x: float = 900.0, default_y: float = 600.0):
    try:
        avail = imgui.get_content_region_avail()
        x = float(avail.x if hasattr(avail, "x") else avail[0])
        y = float(avail.y if hasattr(avail, "y") else avail[1])
        return x, y
    except Exception:
        return float(default_x), float(default_y)


def _clamp_float(value: float, min_value: float, max_value: float) -> float:
    if max_value < min_value:
        return min_value
    return max(min_value, min(max_value, float(value)))


def _begin_bordered_child(name: str, width: float, height: float, no_scrollbar: bool = False):
    flags = 0
    if no_scrollbar:
        try:
            flags |= _imgui_enum_int(imgui.WindowFlags_.no_scrollbar)
            flags |= _imgui_enum_int(imgui.WindowFlags_.no_scroll_with_mouse)
        except Exception:
            flags = 0

    imgui.push_style_color(imgui.Col_.child_bg, ui_color("card_bg"))
    imgui.begin_child(
        str_id=name,
        size=imgui.ImVec2(width, height),
        child_flags=int(imgui.ChildFlags_.borders.value),
        window_flags=flags,
    )


def _end_bordered_child():
    imgui.end_child()
    imgui.pop_style_color()


def render_advanced_splitter(splitter_height: float, rendered_left_width: float, min_left: float, max_left: float, total_width: float):
    global launcher_left_panel_width, launcher_left_panel_ratio

    splitter_width = 6.0
    pushed = 0
    try:
        pushed += _push_style_color_safe("button", ui_color("border_strong"))
        pushed += _push_style_color_safe("button_hovered", ui_color("accent"))
        pushed += _push_style_color_safe("button_active", ui_color("accent"))
        pushed += _push_style_color_safe("text", ui_color("border_strong"))
    except Exception:
        pushed = 0

    try:
        imgui.button("##advanced_vertical_splitter", imgui.ImVec2(splitter_width, max(1.0, splitter_height)))
    except TypeError:
        imgui.button("##advanced_vertical_splitter")

    if pushed:
        try:
            imgui.pop_style_color(pushed)
        except Exception:
            pass

    try:
        if imgui.is_item_active():
            io = imgui.get_io()
            delta_x = float(io.mouse_delta.x if hasattr(io.mouse_delta, "x") else io.mouse_delta[0])
            if abs(delta_x) > 0.01:
                launcher_left_panel_width = _clamp_float(rendered_left_width + delta_x, min_left, max_left)
                launcher_left_panel_ratio = _clamp_float(launcher_left_panel_width / max(1.0, total_width), 0.12, 0.82)
                write_launcher_layout_value_if_changed("advanced_left_panel_ratio", f"{launcher_left_panel_ratio:.4f}")
    except Exception:
        pass


def render_console_splitter(splitter_width: float, rendered_console_height: float, min_console: float, max_console: float, total_height: float):
    global launcher_console_height, launcher_console_height_ratio

    splitter_height = 6.0
    pushed = 0
    try:
        pushed += _push_style_color_safe("button", ui_color("border_strong"))
        pushed += _push_style_color_safe("button_hovered", ui_color("accent"))
        pushed += _push_style_color_safe("button_active", ui_color("accent"))
        pushed += _push_style_color_safe("text", ui_color("border_strong"))
    except Exception:
        pushed = 0

    try:
        imgui.button("##advanced_console_splitter", imgui.ImVec2(max(1.0, splitter_width), splitter_height))
    except TypeError:
        imgui.button("##advanced_console_splitter")

    if pushed:
        try:
            imgui.pop_style_color(pushed)
        except Exception:
            pass

    try:
        if imgui.is_item_active():
            io = imgui.get_io()
            delta_y = float(io.mouse_delta.y if hasattr(io.mouse_delta, "y") else io.mouse_delta[1])
            if abs(delta_y) > 0.01:


                launcher_console_height = _clamp_float(rendered_console_height - delta_y, min_console, max_console)
                launcher_console_height_ratio = _clamp_float(launcher_console_height / max(1.0, total_height), 0.10, 0.60)
                write_launcher_layout_value_if_changed("advanced_console_height_ratio", f"{launcher_console_height_ratio:.4f}")
    except Exception:
        pass


def get_selected_launch_accounts(team=None):
    try:
        active_team = team if team is not None else selected_team
        if not active_team:
            return []
        return [
            account for account in active_team.accounts
            if getattr(account, "launch_selected", False)
        ]
    except Exception:
        return []


def get_all_selected_launch_accounts():
    try:
        accounts = []
        for team in team_manager.teams.values():
            for account in team.accounts:
                if getattr(account, "launch_selected", False):
                    accounts.append(account)
        return accounts
    except Exception:
        return []


def get_all_selected_launch_team_count():
    try:
        return sum(
            1 for team in team_manager.teams.values()
            if any(getattr(account, "launch_selected", False) for account in team.accounts)
        )
    except Exception:
        return 0


class GridLaunchContext:
    def __init__(self, name="All Teams", launch_delay_seconds=15):
        self.name = str(name)
        self.launch_delay_seconds = max(0, int(launch_delay_seconds))


def get_grid_launch_context_team():
    try:
        delay_source = selected_team if selected_team is not None else team_manager.get_first_team()
        delay = int(getattr(delay_source, "launch_delay_seconds", 15))
    except Exception:
        delay = 15

    selected_team_count = get_all_selected_launch_team_count()
    if selected_team_count > 1:
        name = f"All Teams ({selected_team_count})"
    elif selected_team_count == 1:
        name = "Selected Team"
    else:
        name = "All Teams"

    return GridLaunchContext(name, delay)


def get_grid_account_key(account) -> str:
    try:
        return "|".join([
            str(getattr(account, "character_name", "")),
            str(getattr(account, "gw_path", "")),
        ])
    except Exception:
        return str(id(account))


GRID_SLOT_STATE_INI_KEY = "grid_monitor_slot_keys"
GRID_CUSTOM_MERGE_STATE_INI_KEY = "grid_monitor_custom_merge_rects"
GRID_SAVED_LAYOUTS_INI_KEY = "grid_saved_layouts"


def load_grid_slot_state_from_ini():
    try:
        raw_value = ini_handler.read_key(LAYOUT_CONFIG_SECTION, GRID_SLOT_STATE_INI_KEY, "")
        if not str(raw_value or "").strip():
            return {}

        parsed = json.loads(raw_value)
        if not isinstance(parsed, dict):
            return {}

        state = {}
        for monitor_key, slot_values in parsed.items():
            try:
                monitor_index = int(monitor_key)
            except Exception:
                continue

            if not isinstance(slot_values, list):
                continue

            cleaned_slots = []
            for value in slot_values:
                if value is None or value == "":
                    cleaned_slots.append(None)
                else:
                    cleaned_slots.append(str(value))

            state[monitor_index] = cleaned_slots

        return state
    except Exception as e:
        log_history.append(f"Grid Launch - Failed to load saved grid order: {str(e)}")
        return {}


def ensure_grid_slot_state_loaded():
    global grid_monitor_slot_keys, grid_monitor_slot_keys_loaded

    if grid_monitor_slot_keys_loaded:
        return

    grid_monitor_slot_keys = load_grid_slot_state_from_ini()
    grid_monitor_slot_keys_loaded = True


def load_grid_custom_merge_state_from_ini():
    try:
        raw_value = ini_handler.read_key(LAYOUT_CONFIG_SECTION, GRID_CUSTOM_MERGE_STATE_INI_KEY, "")
        if not raw_value:
            return {}

        data = json.loads(raw_value)
        if not isinstance(data, dict):
            return {}

        result = {}
        for monitor_key, rects in data.items():
            try:
                monitor_index = int(monitor_key)
            except Exception:
                continue

            if not isinstance(rects, list):
                continue

            normalized = []
            for rect in rects:
                if not isinstance(rect, dict):
                    continue

                row = int(rect.get("row", 0))
                col = int(rect.get("col", 0))
                row_span = max(1, int(rect.get("row_span", 1)))
                col_span = max(1, int(rect.get("col_span", 1)))

                if row_span <= 1 and col_span <= 1:
                    continue

                normalized.append({
                    "row": max(0, row),
                    "col": max(0, col),
                    "row_span": row_span,
                    "col_span": col_span,
                })

            if normalized:
                result[monitor_index] = normalized

        return result
    except Exception as e:
        log_history.append(f"Grid Custom - Failed to load merged areas: {str(e)}")
        return {}


def persist_grid_custom_merge_state():
    try:
        serializable = {}
        for monitor_index, rects in sorted(grid_monitor_custom_merge_rects.items(), key=lambda item: int(item[0])):
            serializable[str(int(monitor_index))] = [
                {
                    "row": int(rect.get("row", 0)),
                    "col": int(rect.get("col", 0)),
                    "row_span": max(1, int(rect.get("row_span", 1))),
                    "col_span": max(1, int(rect.get("col_span", 1))),
                }
                for rect in list(rects or [])
                if max(1, int(rect.get("row_span", 1))) > 1 or max(1, int(rect.get("col_span", 1))) > 1
            ]

        raw_value = json.dumps(serializable, ensure_ascii=False, separators=(",", ":"))
        write_launcher_layout_value_if_changed(GRID_CUSTOM_MERGE_STATE_INI_KEY, raw_value)
    except Exception as e:
        log_history.append(f"Grid Custom - Failed to save merged areas: {str(e)}")


def ensure_grid_custom_merge_state_loaded():
    global grid_monitor_custom_merge_rects, grid_monitor_custom_merge_rects_loaded

    if grid_monitor_custom_merge_rects_loaded:
        return

    grid_monitor_custom_merge_rects = load_grid_custom_merge_state_from_ini()
    grid_monitor_custom_merge_rects_loaded = True


def normalize_grid_custom_merges_for_monitor(monitor_index: int, rows: int, cols: int):
    ensure_grid_custom_merge_state_loaded()

    monitor_index = int(monitor_index)
    rows = max(1, int(rows))
    cols = max(1, int(cols))
    occupied = set()
    normalized = []

    for rect in list(grid_monitor_custom_merge_rects.get(monitor_index, []) or []):
        row = max(0, min(rows - 1, int(rect.get("row", 0))))
        col = max(0, min(cols - 1, int(rect.get("col", 0))))
        row_span = max(1, min(rows - row, int(rect.get("row_span", 1))))
        col_span = max(1, min(cols - col, int(rect.get("col_span", 1))))

        if row_span <= 1 and col_span <= 1:
            continue

        cells = {(r, c) for r in range(row, row + row_span) for c in range(col, col + col_span)}
        if occupied.intersection(cells):
            continue

        occupied.update(cells)
        normalized.append({
            "row": row,
            "col": col,
            "row_span": row_span,
            "col_span": col_span,
        })

    grid_monitor_custom_merge_rects[monitor_index] = normalized
    return normalized


def get_grid_custom_merge_maps(monitor_index: int, rows: int, cols: int):
    rects = normalize_grid_custom_merges_for_monitor(monitor_index, rows, cols)
    by_start = {}
    covered = set()

    for rect in rects:
        row = int(rect.get("row", 0))
        col = int(rect.get("col", 0))
        row_span = max(1, int(rect.get("row_span", 1)))
        col_span = max(1, int(rect.get("col_span", 1)))
        start_slot = row * max(1, int(cols)) + col
        by_start[start_slot] = rect

        for r in range(row, row + row_span):
            for c in range(col, col + col_span):
                slot_index = r * max(1, int(cols)) + c
                if slot_index != start_slot:
                    covered.add(slot_index)

    return by_start, covered


def clear_grid_custom_merges_for_monitor(monitor_index: int):
    ensure_grid_custom_merge_state_loaded()
    monitor_index = int(monitor_index)
    if grid_monitor_custom_merge_rects.get(monitor_index):
        grid_monitor_custom_merge_rects[monitor_index] = []
        persist_grid_custom_merge_state()
        layout = get_grid_monitor_layout(monitor_index)
        refill_missing_grid_accounts_for_monitor(
            get_all_selected_launch_accounts(),
            monitor_index,
            max(1, int(layout.get("rows", 1))),
            max(1, int(layout.get("cols", 1))),
        )
        log_history.append(f"Grid Custom - Cleared merged areas for Monitor {monitor_index + 1}.")


def remove_grid_custom_merge_at_slot(monitor_index: int, slot_index: int, rows: int, cols: int):
    ensure_grid_custom_merge_state_loaded()

    monitor_index = int(monitor_index)
    slot_index = int(slot_index)
    rows = max(1, int(rows))
    cols = max(1, int(cols))
    slot_row, slot_col = divmod(max(0, min(rows * cols - 1, slot_index)), cols)

    existing = normalize_grid_custom_merges_for_monitor(monitor_index, rows, cols)
    kept = []
    removed = None

    for rect in existing:
        row = int(rect.get("row", 0))
        col = int(rect.get("col", 0))
        row_span = max(1, int(rect.get("row_span", 1)))
        col_span = max(1, int(rect.get("col_span", 1)))
        if row <= slot_row < row + row_span and col <= slot_col < col + col_span:
            removed = rect
        else:
            kept.append(rect)

    if removed is None:
        return False

    grid_monitor_custom_merge_rects[monitor_index] = kept
    persist_grid_custom_merge_state()
    refill_missing_grid_accounts_for_monitor(get_all_selected_launch_accounts(), monitor_index, rows, cols)
    log_history.append(f"Grid Custom - Unmerged Monitor {monitor_index + 1} area at slot {slot_index + 1}.")
    return True


def compact_grid_slots_for_custom_merges(monitor_index: int, rows: int, cols: int):
    global grid_monitor_slot_keys

    ensure_grid_slot_state_loaded()

    monitor_index = int(monitor_index)
    rows = max(1, int(rows))
    cols = max(1, int(cols))
    capacity = rows * cols
    slots = list(grid_monitor_slot_keys.get(monitor_index, []))
    if len(slots) < capacity:
        slots = slots + [None] * (capacity - len(slots))
    slots = slots[:capacity]

    _merge_by_start, covered_slots = get_grid_custom_merge_maps(monitor_index, rows, cols)
    overflow = []

    for covered_slot in sorted(covered_slots):
        if 0 <= covered_slot < len(slots) and slots[covered_slot] is not None:
            overflow.append(slots[covered_slot])
            slots[covered_slot] = None

    visible_free_slots = [slot_index for slot_index in range(capacity) if slot_index not in covered_slots and slots[slot_index] is None]

    for item in list(overflow):
        if visible_free_slots:
            slot_index = visible_free_slots.pop(0)
            slots[slot_index] = item

    grid_monitor_slot_keys[monitor_index] = slots
    persist_grid_slot_state()


def refill_missing_grid_accounts_for_monitor(selected_accounts, monitor_index: int, rows: int, cols: int):
    global grid_monitor_slot_keys, grid_custom_capacity_warning_message

    ensure_grid_slot_state_loaded()

    selected_accounts = list(selected_accounts or [])
    selected_keys = [get_grid_account_key(account) for account in selected_accounts]
    selected_key_set = set(selected_keys)

    monitor_index = int(monitor_index)
    rows = max(1, int(rows))
    cols = max(1, int(cols))
    capacity = rows * cols
    slots = list(grid_monitor_slot_keys.get(monitor_index, []))
    if len(slots) < capacity:
        slots = slots + [None] * (capacity - len(slots))
    slots = slots[:capacity]

    _merge_by_start, covered_slots = get_grid_custom_merge_maps(monitor_index, rows, cols)

    present_keys = set()
    for monitor_slots in grid_monitor_slot_keys.values():
        for key in list(monitor_slots or []):
            if key in selected_key_set:
                present_keys.add(key)

    missing_keys = [key for key in selected_keys if key not in present_keys]
    if not missing_keys:
        grid_custom_capacity_warning_message = ""
        return 0

    filled = 0
    for key in missing_keys:
        placed = False
        for slot_index in range(capacity):
            if slot_index in covered_slots:
                continue
            if slots[slot_index] is None:
                slots[slot_index] = key
                filled += 1
                placed = True
                break
        if not placed:
            break

    grid_monitor_slot_keys[monitor_index] = slots
    persist_grid_slot_state()

    if filled < len(missing_keys):
        grid_custom_capacity_warning_message = (
            f"Grid capacity too small after refill on Monitor {monitor_index + 1}: "
            f"{get_grid_effective_area_count(monitor_index, rows, cols)} visible areas. "
            f"Missing accounts remaining: {len(missing_keys) - filled}."
        )
        log_history.append(grid_custom_capacity_warning_message)
    else:
        grid_custom_capacity_warning_message = ""
        log_history.append(f"Grid Custom - Refilled {filled} missing selected account(s) on Monitor {monitor_index + 1}.")

    return filled


def add_grid_custom_merge_rect(monitor_index: int, start_slot: int, end_slot: int, rows: int, cols: int):
    global grid_monitor_slot_keys

    ensure_grid_custom_merge_state_loaded()
    ensure_grid_slot_state_loaded()

    monitor_index = int(monitor_index)
    rows = max(1, int(rows))
    cols = max(1, int(cols))
    start_slot = max(0, min(rows * cols - 1, int(start_slot)))
    end_slot = max(0, min(rows * cols - 1, int(end_slot)))

    start_row, start_col = divmod(start_slot, cols)
    end_row, end_col = divmod(end_slot, cols)

    row_min = min(start_row, end_row)
    row_max = max(start_row, end_row)
    col_min = min(start_col, end_col)
    col_max = max(start_col, end_col)

    row_span = row_max - row_min + 1
    col_span = col_max - col_min + 1

    if row_span <= 1 and col_span <= 1:
        return False

    new_cells = {(r, c) for r in range(row_min, row_max + 1) for c in range(col_min, col_max + 1)}
    existing = normalize_grid_custom_merges_for_monitor(monitor_index, rows, cols)
    kept = []

    for rect in existing:
        rect_cells = {
            (r, c)
            for r in range(int(rect.get("row", 0)), int(rect.get("row", 0)) + int(rect.get("row_span", 1)))
            for c in range(int(rect.get("col", 0)), int(rect.get("col", 0)) + int(rect.get("col_span", 1)))
        }
        if rect_cells.isdisjoint(new_cells):
            kept.append(rect)

    kept.append({
        "row": row_min,
        "col": col_min,
        "row_span": row_span,
        "col_span": col_span,
    })
    grid_monitor_custom_merge_rects[monitor_index] = kept

    compact_grid_slots_for_custom_merges(monitor_index, rows, cols)
    refill_missing_grid_accounts_for_monitor(get_all_selected_launch_accounts(), monitor_index, rows, cols)
    persist_grid_custom_merge_state()
    log_history.append(
        f"Grid Custom - Merged Monitor {monitor_index + 1} cells R{row_min + 1}:C{col_min + 1} to R{row_max + 1}:C{col_max + 1}."
    )
    return True


def persist_grid_slot_state():
    try:
        serializable = {}
        for monitor_index, slots in sorted(grid_monitor_slot_keys.items(), key=lambda item: int(item[0])):
            serializable[str(int(monitor_index))] = [
                None if slot_key is None else str(slot_key)
                for slot_key in list(slots or [])
            ]

        raw_value = json.dumps(serializable, ensure_ascii=False, separators=(",", ":"))
        write_launcher_layout_value_if_changed(GRID_SLOT_STATE_INI_KEY, raw_value)
    except Exception as e:
        log_history.append(f"Grid Launch - Failed to save grid order: {str(e)}")


def get_selected_grid_monitor_indices(monitors):
    global grid_selected_monitor_indices, grid_selected_monitor_index

    monitor_count = len(monitors or [])
    valid = []
    for index in list(grid_selected_monitor_indices or []):
        try:
            index = int(index)
        except Exception:
            continue
        if 0 <= index < monitor_count and index not in valid:
            valid.append(index)

    if not valid:
        fallback = max(0, min(monitor_count - 1, int(grid_selected_monitor_index or 0))) if monitor_count else 0
        valid = [fallback]
        grid_selected_monitor_indices = list(valid)

    return valid


def save_grid_monitor_indices(indices):
    global grid_selected_monitor_indices, grid_selected_monitor_index

    unique = []
    for index in indices or []:
        try:
            index = int(index)
        except Exception:
            continue
        if index not in unique:
            unique.append(index)

    if not unique:
        unique = [0]

    grid_selected_monitor_indices = unique
    grid_selected_monitor_index = unique[0]
    write_launcher_layout_value_if_changed("grid_monitor_indices", _format_int_csv(unique))
    write_launcher_layout_value_if_changed("grid_monitor_index", grid_selected_monitor_index)


def toggle_grid_monitor_selection(index: int, monitors):
    current = get_selected_grid_monitor_indices(monitors)
    index = int(index)

    if index in current:
        if len(current) <= 1:
            log_history.append("Grid Launch - At least one monitor must stay selected.")
            return
        current.remove(index)
    else:
        current.append(index)
        current.sort()

    save_grid_monitor_indices(current)
    sync_multi_monitor_grid_slots(get_all_selected_launch_accounts(), current, {})


def _monitor_layout_ini_key(monitor_index: int, key: str) -> str:
    return f"grid_monitor_{int(monitor_index)}_{key}"


def get_grid_monitor_layout(monitor_index: int):
    monitor_index = int(monitor_index)

    if monitor_index not in grid_monitor_layouts:
        mode = ini_handler.read_key(
            LAYOUT_CONFIG_SECTION,
            _monitor_layout_ini_key(monitor_index, "layout_mode"),
            grid_layout_mode,
        )
        rows = max(1, ini_handler.read_int(
            LAYOUT_CONFIG_SECTION,
            _monitor_layout_ini_key(monitor_index, "rows"),
            grid_rows,
        ))
        cols = max(1, ini_handler.read_int(
            LAYOUT_CONFIG_SECTION,
            _monitor_layout_ini_key(monitor_index, "cols"),
            grid_cols,
        ))
        grid_monitor_layouts[monitor_index] = {
            "mode": str(mode or "auto"),
            "rows": rows,
            "cols": cols,
        }

    return grid_monitor_layouts[monitor_index]


def save_grid_monitor_layout(monitor_index: int, rows: int, cols: int, mode: str = "custom"):
    monitor_index = int(monitor_index)
    layout = get_grid_monitor_layout(monitor_index)
    old_rows = max(1, int(layout.get("rows", 1)))
    old_cols = max(1, int(layout.get("cols", 1)))
    old_mode = str(layout.get("mode", "auto") or "auto")
    layout["rows"] = max(1, int(rows))
    layout["cols"] = max(1, int(cols))
    layout["mode"] = str(mode or "custom")

    write_launcher_layout_value_if_changed(_monitor_layout_ini_key(monitor_index, "rows"), layout["rows"])
    write_launcher_layout_value_if_changed(_monitor_layout_ini_key(monitor_index, "cols"), layout["cols"])
    write_launcher_layout_value_if_changed(_monitor_layout_ini_key(monitor_index, "layout_mode"), layout["mode"])

    if old_rows != layout["rows"] or old_cols != layout["cols"] or old_mode != layout["mode"]:
        refill_missing_grid_accounts_for_monitor(
            get_all_selected_launch_accounts(),
            monitor_index,
            layout["rows"],
            layout["cols"],
        )


def get_monitor_share_count(total_count: int, monitor_position: int, selected_monitor_count: int) -> int:
    total_count = max(1, int(total_count))
    selected_monitor_count = max(1, int(selected_monitor_count))
    monitor_position = max(0, int(monitor_position))

    base = total_count // selected_monitor_count
    remainder = total_count % selected_monitor_count
    return max(1, base + (1 if monitor_position < remainder else 0))


def get_effective_grid_dimensions_for_monitor(monitor_index: int, monitor: dict, selected_count: int, monitor_position: int, selected_monitor_count: int):
    layout = get_grid_monitor_layout(monitor_index)
    mode = str(layout.get("mode", "auto")).lower()

    if mode == "auto":
        share_count = get_monitor_share_count(selected_count, monitor_position, selected_monitor_count)
        return compute_auto_grid(share_count, monitor)

    return max(1, int(layout.get("rows", 1))), max(1, int(layout.get("cols", 1)))


def get_grid_account_key(account) -> str:
    try:
        return "|".join([
            str(getattr(account, "character_name", "")),
            str(getattr(account, "email", "")),
            str(getattr(account, "gw_path", "")),
        ])
    except Exception:
        return str(id(account))


def get_covered_slots_for_current_monitor_layout(monitor_index: int, capacity: int):
    try:
        layout = get_grid_monitor_layout(monitor_index)
        rows = max(1, int(layout.get("rows", 1)))
        cols = max(1, int(layout.get("cols", 1)))
        if rows * cols != max(1, int(capacity)):
            return set()
        _merge_by_start, covered_slots = get_grid_custom_merge_maps(monitor_index, rows, cols)
        return set(covered_slots)
    except Exception:
        return set()


def sync_multi_monitor_grid_slots(selected_accounts, selected_monitor_indices, monitor_capacities):
    global grid_monitor_slot_keys, grid_account_order_keys, grid_custom_capacity_warning_message

    ensure_grid_slot_state_loaded()

    selected_accounts = list(selected_accounts or [])
    selected_keys_raw = [get_grid_account_key(account) for account in selected_accounts]
    selected_keys = []
    selected_key_set = set()
    for key in selected_keys_raw:
        if key in selected_key_set:
            continue
        selected_keys.append(key)
        selected_key_set.add(key)

    selected_monitor_indices = list(selected_monitor_indices or [0])

    new_state = {}
    used = set()
    visible_slots = []
    any_existing_assignment = False

    for monitor_index in selected_monitor_indices:
        capacity = max(1, int(monitor_capacities.get(monitor_index, len(selected_keys) or 1)))
        covered_slots = get_covered_slots_for_current_monitor_layout(monitor_index, capacity)
        old_slots = list(grid_monitor_slot_keys.get(monitor_index, []))

        if not old_slots and monitor_index == selected_monitor_indices[0] and grid_account_order_keys:
            old_slots = list(grid_account_order_keys)

        if len(old_slots) < capacity:
            old_slots = old_slots + [None] * (capacity - len(old_slots))

        slots = [None] * capacity

        for slot_index in range(capacity):
            if slot_index in covered_slots:
                continue

            visible_slots.append((monitor_index, slot_index))
            key = old_slots[slot_index] if slot_index < len(old_slots) else None

            if key in selected_key_set and key not in used:
                slots[slot_index] = key
                used.add(key)
                any_existing_assignment = True

        new_state[monitor_index] = slots

    if not any_existing_assignment:
        for key, location in zip(selected_keys, visible_slots):
            monitor_index, slot_index = location
            new_state[monitor_index][slot_index] = key
            used.add(key)

    total_visible_capacity = len(visible_slots)
    if len(selected_keys) > total_visible_capacity:
        missing_count = len(selected_keys) - total_visible_capacity
        grid_custom_capacity_warning_message = (
            f"Grid capacity too small across selected monitors: {total_visible_capacity} visible areas "
            f"for {len(selected_keys)} selected accounts. Missing accounts remaining: {missing_count}."
        )
    else:
        grid_custom_capacity_warning_message = ""

    grid_monitor_slot_keys = new_state

    if selected_monitor_indices:
        grid_account_order_keys = list(new_state.get(selected_monitor_indices[0], []))

    persist_grid_slot_state()
    return grid_monitor_slot_keys


def get_grid_slots_for_monitor(selected_accounts, monitor_index: int, capacity: int):
    ensure_grid_slot_state_loaded()
    selected_accounts = list(selected_accounts or [])
    by_key = {get_grid_account_key(account): account for account in selected_accounts}
    slots = grid_monitor_slot_keys.get(int(monitor_index), [])
    if len(slots) < capacity:
        slots = slots + [None] * (capacity - len(slots))
    return [by_key.get(key) if key is not None else None for key in slots[:capacity]]


def get_grid_slots(selected_accounts, capacity: int):
    sync_multi_monitor_grid_slots(selected_accounts, [0], {0: capacity})
    return get_grid_slots_for_monitor(selected_accounts, 0, capacity)


def get_ordered_grid_accounts(selected_accounts):
    capacity = max(1, len(selected_accounts or []))
    return [account for account in get_grid_slots(selected_accounts, capacity) if account is not None]


def get_grid_launch_plan(selected_accounts, capacity: int):
    slots = get_grid_slots(selected_accounts, capacity)
    launch_accounts = []
    slot_indices = []

    for slot_index, account in enumerate(slots):
        if account is None:
            continue
        launch_accounts.append(account)
        slot_indices.append(slot_index)

    return launch_accounts, slot_indices


def get_multi_monitor_grid_launch_plan(selected_accounts, monitors, selected_monitor_indices, monitor_layouts):
    launch_plan = []
    for monitor_index in selected_monitor_indices:
        layout = monitor_layouts.get(monitor_index)
        if not layout:
            continue

        capacity = int(layout["rows"]) * int(layout["cols"])
        slots = get_grid_slots_for_monitor(selected_accounts, monitor_index, capacity)
        monitor = monitors[monitor_index]
        _merge_by_start, covered_slots = get_grid_custom_merge_maps(monitor_index, int(layout["rows"]), int(layout["cols"]))

        for slot_index, account in enumerate(slots):
            if slot_index in covered_slots:
                continue
            if account is None:
                continue
            launch_plan.append({
                "account": account,
                "monitor": monitor,
                "monitor_index": monitor_index,
                "rows": int(layout["rows"]),
                "cols": int(layout["cols"]),
                "slot_index": slot_index,
            })

    return launch_plan


def get_grid_account_name_by_key(account_key) -> str:
    try:
        if account_key is None:
            return "Leer"

        for account in get_all_selected_launch_accounts():
            if get_grid_account_key(account) == account_key:
                return str(getattr(account, "character_name", "") or "Account").strip() or "Account"


        first_part = str(account_key).split("|", 1)[0].strip()
        return first_part or "Account"
    except Exception:
        return "Account"


def get_grid_merge_rect_for_start_slot(monitor_index: int, slot_index: int):
    try:
        layout = get_grid_monitor_layout(int(monitor_index))
        rows = max(1, int(layout.get("rows", 1)))
        cols = max(1, int(layout.get("cols", 1)))
        merge_by_start, _covered_slots = get_grid_custom_merge_maps(int(monitor_index), rows, cols)
        rect = merge_by_start.get(int(slot_index))
        if not rect:
            return None, rows, cols

        return {
            "row": int(rect.get("row", 0)),
            "col": int(rect.get("col", 0)),
            "row_span": max(1, int(rect.get("row_span", 1))),
            "col_span": max(1, int(rect.get("col_span", 1))),
        }, rows, cols
    except Exception:
        return None, 1, 1


def get_grid_rect_cells(rect):
    row = int(rect.get("row", 0))
    col = int(rect.get("col", 0))
    row_span = max(1, int(rect.get("row_span", 1)))
    col_span = max(1, int(rect.get("col_span", 1)))
    return {(r, c) for r in range(row, row + row_span) for c in range(col, col + col_span)}


def grid_rect_fits(rect, rows: int, cols: int):
    row = int(rect.get("row", 0))
    col = int(rect.get("col", 0))
    row_span = max(1, int(rect.get("row_span", 1)))
    col_span = max(1, int(rect.get("col_span", 1)))
    return row >= 0 and col >= 0 and row + row_span <= max(1, int(rows)) and col + col_span <= max(1, int(cols))


def grid_rects_are_valid(rects, rows: int, cols: int):
    occupied = set()
    for rect in list(rects or []):
        if not grid_rect_fits(rect, rows, cols):
            return False
        cells = get_grid_rect_cells(rect)
        if occupied.intersection(cells):
            return False
        occupied.update(cells)
    return True


def move_grid_merged_block_between_monitors(source_monitor_index: int, source_slot_index: int, target_monitor_index: int, target_slot_index: int):
    global grid_monitor_slot_keys, grid_account_order_keys, grid_custom_capacity_warning_message

    try:
        source_monitor_index = int(source_monitor_index)
        target_monitor_index = int(target_monitor_index)
        source_slot_index = int(source_slot_index)
        target_slot_index = int(target_slot_index)

        source_rect, rows, cols = get_grid_merge_rect_for_start_slot(source_monitor_index, source_slot_index)
        if not source_rect:
            return False

        if source_monitor_index != target_monitor_index:
            log_history.append("Grid Custom - Moving merged blocks across monitors is not supported yet.")
            return True

        if source_slot_index == target_slot_index:
            return True

        capacity = rows * cols
        target_slot_index = max(0, min(capacity - 1, target_slot_index))
        target_row, target_col = divmod(target_slot_index, cols)

        target_rect, _target_rows, _target_cols = get_grid_merge_rect_for_start_slot(target_monitor_index, target_slot_index)

        existing = normalize_grid_custom_merges_for_monitor(source_monitor_index, rows, cols)
        source_cells = get_grid_rect_cells(source_rect)
        target_cells = get_grid_rect_cells(target_rect) if target_rect else set()

        kept = []
        for rect in existing:
            cells = get_grid_rect_cells(rect)
            if cells == source_cells:
                continue
            if target_rect and cells == target_cells:
                continue
            kept.append(rect)

        moved_source_rect = {
            "row": target_row,
            "col": target_col,
            "row_span": max(1, int(source_rect.get("row_span", 1))),
            "col_span": max(1, int(source_rect.get("col_span", 1))),
        }

        candidate_rects = list(kept) + [moved_source_rect]

        if target_rect:
            source_row = int(source_rect.get("row", 0))
            source_col = int(source_rect.get("col", 0))
            moved_target_rect = {
                "row": source_row,
                "col": source_col,
                "row_span": max(1, int(target_rect.get("row_span", 1))),
                "col_span": max(1, int(target_rect.get("col_span", 1))),
            }
            candidate_rects.append(moved_target_rect)

        if not grid_rects_are_valid(candidate_rects, rows, cols):
            log_history.append("Grid Custom - Merged block move failed: target area does not fit or overlaps another merged area.")
            return True

        slots = list(grid_monitor_slot_keys.get(source_monitor_index, []))
        if len(slots) < capacity:
            slots = slots + [None] * (capacity - len(slots))
        slots = slots[:capacity]

        source_item = slots[source_slot_index] if 0 <= source_slot_index < len(slots) else None
        if source_item is None:
            return True

        source_name = get_grid_account_name_by_key(source_item)
        target_name = get_grid_account_name_by_key(slots[target_slot_index] if target_slot_index < len(slots) else None)

        displaced = []
        if 0 <= source_slot_index < len(slots):
            slots[source_slot_index] = None

        for r, c in get_grid_rect_cells(moved_source_rect):
            check_slot = r * cols + c
            if 0 <= check_slot < len(slots):
                item = slots[check_slot]
                if item is not None and item != source_item:
                    displaced.append(item)
                slots[check_slot] = None

        slots[target_slot_index] = source_item

        final_covered = set()
        for rect in candidate_rects:
            start_slot = int(rect.get("row", 0)) * cols + int(rect.get("col", 0))
            for r, c in get_grid_rect_cells(rect):
                slot_index = r * cols + c
                if slot_index != start_slot:
                    final_covered.add(slot_index)

        for slot_index in sorted(final_covered):
            if 0 <= slot_index < len(slots) and slots[slot_index] is not None:
                item = slots[slot_index]
                if item != source_item:
                    displaced.append(item)
                slots[slot_index] = None

        current_items = {item for item in slots if item is not None}
        displaced_unique = []
        for item in displaced:
            if item is None or item in current_items or item in displaced_unique:
                continue
            displaced_unique.append(item)

        free_slots = [
            slot_index
            for slot_index in range(capacity)
            if slot_index not in final_covered and slots[slot_index] is None
        ]

        if len(free_slots) < len(displaced_unique):
            grid_custom_capacity_warning_message = (
                f"Grid capacity too small after merged block move on Monitor {source_monitor_index + 1}: "
                f"{get_grid_effective_area_count(source_monitor_index, rows, cols)} visible areas. "
                f"Missing accounts remaining: {len(displaced_unique) - len(free_slots)}."
            )
            log_history.append(grid_custom_capacity_warning_message)
            return True

        for item, slot_index in zip(displaced_unique, free_slots):
            slots[slot_index] = item

        grid_custom_capacity_warning_message = ""
        grid_monitor_custom_merge_rects[source_monitor_index] = candidate_rects
        grid_monitor_slot_keys[source_monitor_index] = slots
        grid_account_order_keys = list(grid_monitor_slot_keys.get(source_monitor_index, []))
        persist_grid_custom_merge_state()
        persist_grid_slot_state()

        if target_rect:
            log_history.append(
                f"Grid Custom - Swapped merged block '{source_name}' slot {source_slot_index + 1} with '{target_name}' slot {target_slot_index + 1}."
            )
        else:
            log_history.append(
                f"Grid Custom - Moved merged block '{source_name}' from slot {source_slot_index + 1} to slot {target_slot_index + 1}."
            )

        return True
    except Exception as e:
        log_history.append(f"Grid Custom - Merged block move failed: {str(e)}")
        return True


def handle_grid_click_account_swap(source_monitor_index: int, source_slot_index: int, target_monitor_index: int, target_slot_index: int):
    global grid_click_swap_source_location, grid_click_swap_source_key

    try:
        source_monitor_index = int(source_monitor_index)
        source_slot_index = int(source_slot_index)
        target_monitor_index = int(target_monitor_index)
        target_slot_index = int(target_slot_index)

        if source_monitor_index == target_monitor_index and source_slot_index == target_slot_index:
            grid_click_swap_source_location = None
            grid_click_swap_source_key = None
            return False

        move_grid_account_between_monitors(source_monitor_index, source_slot_index, target_monitor_index, target_slot_index)
        grid_click_swap_source_location = None
        grid_click_swap_source_key = None
        return True
    except Exception as e:
        log_history.append(f"Grid Launch - Click swap failed: {str(e)}")
        grid_click_swap_source_location = None
        grid_click_swap_source_key = None
        return False


def move_grid_account_between_monitors(source_monitor_index: int, source_slot_index: int, target_monitor_index: int, target_slot_index: int):
    global grid_monitor_slot_keys, grid_preview_drag_source_location, grid_preview_drag_source_index, grid_preview_drag_source_key, grid_account_order_keys

    try:
        source_monitor_index = int(source_monitor_index)
        source_slot_index = int(source_slot_index)
        target_monitor_index = int(target_monitor_index)
        target_slot_index = int(target_slot_index)

        source_slots = grid_monitor_slot_keys.get(source_monitor_index, [])
        target_slots = grid_monitor_slot_keys.get(target_monitor_index, [])

        if source_slot_index < 0 or source_slot_index >= len(source_slots):
            return
        if target_slot_index < 0 or target_slot_index >= len(target_slots):
            return

        source_item = source_slots[source_slot_index]
        target_item = target_slots[target_slot_index]


        if grid_preview_drag_source_key is not None:
            source_item = grid_preview_drag_source_key

        if source_item is None:
            return

        if source_monitor_index == target_monitor_index and source_slot_index == target_slot_index:
            return

        source_name = get_grid_account_name_by_key(source_item)
        target_name = get_grid_account_name_by_key(target_item)

        if target_item is None:
            target_slots[target_slot_index] = source_item
            source_slots[source_slot_index] = None
            log_history.append(
                f"Grid Launch - Moved '{source_name}' from Monitor {source_monitor_index + 1} "
                f"slot {source_slot_index + 1} to Monitor {target_monitor_index + 1} "
                f"slot {target_slot_index + 1}."
            )
        else:
            source_slots[source_slot_index], target_slots[target_slot_index] = target_item, source_item
            log_history.append(
                f"Grid Launch - Swapped '{source_name}' at Monitor {source_monitor_index + 1} "
                f"slot {source_slot_index + 1} with '{target_name}' at Monitor {target_monitor_index + 1} "
                f"slot {target_slot_index + 1}."
            )

        grid_preview_drag_source_location = None
        grid_preview_drag_source_index = None
        grid_preview_drag_source_key = None
        grid_account_order_keys = list(grid_monitor_slot_keys.get(source_monitor_index, []))
        persist_grid_slot_state()
    except Exception as e:
        log_history.append(f"Grid Launch - Preview reorder failed: {str(e)}")


def move_grid_account(source_index: int, target_index: int):
    move_grid_account_between_monitors(0, source_index, 0, target_index)


def reset_grid_order(selected_accounts=None):
    global grid_account_order_keys, grid_monitor_slot_keys, grid_preview_drag_source_index, grid_preview_drag_source_location, grid_preview_drag_source_key, grid_preview_drag_had_motion
    global grid_monitor_custom_merge_rects, grid_custom_merge_drag_start, grid_custom_merge_drag_current, grid_custom_capacity_warning_message
    global grid_click_swap_source_location, grid_click_swap_source_key

    grid_preview_drag_source_index = None
    grid_preview_drag_source_location = None
    grid_preview_drag_source_key = None
    grid_preview_drag_had_motion = False
    grid_click_swap_source_location = None
    grid_click_swap_source_key = None
    grid_custom_merge_drag_start = None
    grid_custom_merge_drag_current = None
    grid_custom_capacity_warning_message = ""

    if selected_accounts:
        grid_account_order_keys = [get_grid_account_key(account) for account in selected_accounts]
    else:
        grid_account_order_keys = []

    grid_monitor_slot_keys = {}
    grid_monitor_custom_merge_rects = {}
    persist_grid_slot_state()
    persist_grid_custom_merge_state()
    log_history.append("Grid Launch - Grid order and custom merged areas reset to default selected-account order.")


def get_grid_drag_label():
    try:
        source_key = None

        if grid_preview_drag_source_location is not None:
            monitor_index, slot_index = grid_preview_drag_source_location
            slots = grid_monitor_slot_keys.get(int(monitor_index), [])
            if 0 <= int(slot_index) < len(slots):
                source_key = slots[int(slot_index)]
        elif grid_preview_drag_source_index is not None and 0 <= grid_preview_drag_source_index < len(grid_account_order_keys):
            source_key = grid_account_order_keys[grid_preview_drag_source_index]

        if source_key is None:
            return ""

        active_accounts = get_all_selected_launch_accounts()
        for account in active_accounts:
            if get_grid_account_key(account) == source_key:
                return account.character_name.strip() or "Account"

        return "Account"
    except Exception:
        return "Account"


class MONITORINFOEXW(ctypes.Structure):
    _fields_ = [
        ("cbSize", wintypes.DWORD),
        ("rcMonitor", wintypes.RECT),
        ("rcWork", wintypes.RECT),
        ("dwFlags", wintypes.DWORD),
        ("szDevice", wintypes.WCHAR * 32),
    ]


def _rect_to_dict(rect):
    left = int(rect.left)
    top = int(rect.top)
    right = int(rect.right)
    bottom = int(rect.bottom)
    return {
        "left": left,
        "top": top,
        "right": right,
        "bottom": bottom,
        "width": max(0, right - left),
        "height": max(0, bottom - top),
    }


def detect_display_monitors():
    monitors = []

    try:
        MonitorEnumProc = ctypes.WINFUNCTYPE(
            ctypes.c_bool,
            wintypes.HANDLE,
            wintypes.HDC,
            ctypes.POINTER(wintypes.RECT),
            wintypes.LPARAM,
        )

        def callback(hmonitor, hdc, lprect, lparam):
            info = MONITORINFOEXW()
            info.cbSize = ctypes.sizeof(MONITORINFOEXW)

            if user32.GetMonitorInfoW(hmonitor, ctypes.byref(info)):
                monitor_rect = _rect_to_dict(info.rcMonitor)
                work_rect = _rect_to_dict(info.rcWork)
                index = len(monitors) + 1
                is_primary = bool(info.dwFlags & 1)
                monitors.append({
                    "index": index,
                    "label": f"Monitor {index}" + (" (Primary)" if is_primary else ""),
                    "device": str(info.szDevice),
                    "primary": is_primary,
                    "monitor": monitor_rect,
                    "work": work_rect,
                    "width": monitor_rect["width"],
                    "height": monitor_rect["height"],
                    "work_width": work_rect["width"],
                    "work_height": work_rect["height"],
                })
            return True

        user32.EnumDisplayMonitors(None, None, MonitorEnumProc(callback), 0)
    except Exception as e:
        log_history.append(f"Grid Launch - Monitor detection failed: {str(e)}")

    if not monitors:
        try:
            width = int(user32.GetSystemMetrics(0))
            height = int(user32.GetSystemMetrics(1))
        except Exception:
            width, height = 1920, 1080

        monitors.append({
            "index": 1,
            "label": "Monitor 1 (Fallback)",
            "device": "",
            "primary": True,
            "monitor": {"left": 0, "top": 0, "right": width, "bottom": height, "width": width, "height": height},
            "work": {"left": 0, "top": 0, "right": width, "bottom": height, "width": width, "height": height},
            "width": width,
            "height": height,
            "work_width": width,
            "work_height": height,
        })

    return monitors


def monitor_display_label(monitor):
    suffix = " Primary" if monitor.get("primary") else ""
    return (
        f"{monitor.get('label', 'Monitor')}{suffix} - "
        f"{monitor.get('work_width', monitor.get('width', 0))}x"
        f"{monitor.get('work_height', monitor.get('height', 0))}"
    )


def compute_auto_grid(selected_count: int, monitor: dict):
    count = max(1, int(selected_count))
    work_w = max(1, int(monitor.get("work_width", monitor.get("width", 1920))))
    work_h = max(1, int(monitor.get("work_height", monitor.get("height", 1080))))
    monitor_aspect = work_w / work_h

    best = None
    for rows in range(1, count + 1):
        cols = int(math.ceil(count / rows))
        capacity = rows * cols
        cell_aspect = (work_w / max(1, cols)) / (work_h / max(1, rows))
        score = (
            abs(math.log(max(0.01, cell_aspect) / max(0.01, monitor_aspect)))
            + (capacity - count) * 0.18
            + abs(rows - cols) * 0.035
        )
        if best is None or score < best[0]:
            best = (score, rows, cols)

    if best:
        return best[1], best[2]
    return 1, count


def get_dynamic_grid_presets(selected_count: int):
    count = max(1, int(selected_count))
    max_axis = min(max(1, count), 8)
    max_capacity = max(count, min(count + 4, count * 2))
    presets = []

    for rows in range(1, max_axis + 1):
        for cols in range(1, max_axis + 1):
            capacity = rows * cols
            if capacity < count:
                continue
            if capacity > max_capacity and capacity != count:
                continue
            presets.append((capacity, abs(rows - cols), rows, cols))

    presets.sort(key=lambda item: (item[0] != count, item[0], item[1], item[2], item[3]))

    result = []
    seen = set()
    for _, _, rows, cols in presets:
        key = (rows, cols)
        if key not in seen:
            seen.add(key)
            result.append(key)

    return result[:16]


def get_effective_grid_dimensions(selected_count: int, monitor: dict):
    global grid_rows, grid_cols

    count = max(1, int(selected_count))
    if grid_layout_mode == "auto":
        return compute_auto_grid(count, monitor)

    rows = max(1, int(grid_rows))
    cols = max(1, int(grid_cols))
    if rows * cols < count:
        cols = max(cols, int(math.ceil(count / rows)))
    return rows, cols


def compute_grid_window_rects(monitor: dict, rows: int, cols: int, count: int, monitor_index=None):
    work = monitor.get("work") or monitor.get("monitor") or {}
    left = int(work.get("left", 0))
    top = int(work.get("top", 0))
    width = max(1, int(work.get("width", monitor.get("work_width", monitor.get("width", 1920)))))
    height = max(1, int(work.get("height", monitor.get("work_height", monitor.get("height", 1080)))))

    rows = max(1, int(rows))
    cols = max(1, int(cols))
    count = max(0, int(count))

    merge_by_start = {}
    covered_slots = set()
    if monitor_index is not None:
        merge_by_start, covered_slots = get_grid_custom_merge_maps(int(monitor_index), rows, cols)

    rects = []
    for index in range(count):
        row = index // cols
        col = index % cols
        rect = merge_by_start.get(index)
        if rect and index not in covered_slots:
            row_span = max(1, int(rect.get("row_span", 1)))
            col_span = max(1, int(rect.get("col_span", 1)))
        else:
            row_span = 1
            col_span = 1

        x1 = left + int((width * col) / cols)
        x2 = left + int((width * min(cols, col + col_span)) / cols)
        y1 = top + int((height * row) / rows)
        y2 = top + int((height * min(rows, row + row_span)) / rows)

        rects.append({
            "x": int(x1),
            "y": int(y1),
            "width": max(1, int(x2 - x1)),
            "height": max(1, int(y2 - y1)),
        })

    return rects


def save_grid_monitor_index(index: int):
    global grid_selected_monitor_index
    grid_selected_monitor_index = max(0, int(index))
    save_grid_monitor_indices([grid_selected_monitor_index])


def save_grid_layout(rows: int, cols: int, mode: str = "custom"):
    global grid_rows, grid_cols, grid_layout_mode
    grid_rows = max(1, int(rows))
    grid_cols = max(1, int(cols))
    grid_layout_mode = str(mode or "custom")
    write_launcher_layout_value_if_changed("grid_rows", grid_rows)
    write_launcher_layout_value_if_changed("grid_cols", grid_cols)
    write_launcher_layout_value_if_changed("grid_layout_mode", grid_layout_mode)


def open_grid_start_tab():
    global launcher_config_tab, is_compact_view, last_is_compact_view

    launcher_config_tab = "grid"
    write_launcher_layout_value_if_changed("advanced_config_tab", launcher_config_tab)

    if is_compact_view:
        is_compact_view = False
        ini_handler.write_key("Py4GW_Launcher", "is_compact_view", str(is_compact_view))
        try:
            hello_imgui.change_window_size((980, 660))
        except Exception:
            pass
        last_is_compact_view = is_compact_view

    log_history.append("Grid Launch - Grid Start view opened.")


def render_grid_monitor_cards(monitors, selected_indices):
    if not monitors:
        ui_text_muted("No monitors detected.")
        return

    selected_indices = set(int(index) for index in (selected_indices or []))
    avail_w, _ = _imgui_avail_size(520.0, 200.0)
    used_w = 0.0
    button_w = 165.0

    for index, monitor in enumerate(monitors):
        if index > 0 and used_w + button_w + 8.0 < avail_w:
            imgui.same_line()
            used_w += button_w + 8.0
        else:
            used_w = button_w

        is_selected = index in selected_indices
        label = f"{monitor.get('label', 'Monitor')}##grid_monitor_card_{index}"
        kind = "active_monitor" if is_selected else "secondary"
        if themed_button(label, kind, imgui.ImVec2(button_w, 0)):
            toggle_grid_monitor_selection(index, monitors)

        try:
            if imgui.is_item_hovered():
                imgui.set_tooltip(monitor_display_label(monitor))
        except Exception:
            pass


def render_grid_layout_controls_for_monitor(monitor_index: int, monitor: dict, selected_count: int, monitor_position: int, selected_monitor_count: int):
    layout = get_grid_monitor_layout(monitor_index)
    layout_mode = str(layout.get("mode", "auto")).lower()

    rows_effective, cols_effective = get_effective_grid_dimensions_for_monitor(
        monitor_index,
        monitor,
        selected_count,
        monitor_position,
        selected_monitor_count,
    )
    rows_base = max(1, int(rows_effective))
    cols_base = max(1, int(cols_effective))
    share_count = get_monitor_share_count(selected_count, monitor_position, selected_monitor_count)

    ui_section_header(
        f"{monitor.get('label', f'Monitor {monitor_index + 1}')}",
        f"Target approx. {share_count} Account(s) - Layout {rows_base}x{cols_base}"
    )

    if themed_button(
        f"Auto##grid_layout_auto_monitor_{monitor_index}",
        "primary" if layout_mode == "auto" else "secondary",
    ):


        save_grid_monitor_layout(monitor_index, rows_base, cols_base, "auto")

    presets = get_dynamic_grid_presets(share_count)
    line_width, _ = _imgui_avail_size(520.0, 200.0)
    used_width = 70.0

    for rows, cols in presets:
        button_width = 64.0
        if used_width + button_width + 8.0 < line_width:
            imgui.same_line()
            used_width += button_width + 8.0
        else:
            used_width = button_width

        is_active = (
            layout_mode != "auto"
            and rows_base == rows
            and cols_base == cols
        )
        if themed_button(
            f"{rows}x{cols}##grid_preset_monitor_{monitor_index}_{rows}_{cols}",
            "primary" if is_active else "secondary",
            imgui.ImVec2(button_width, 0),
        ):
            save_grid_monitor_layout(monitor_index, rows, cols, "custom")

    imgui.spacing()

    if themed_button(f"-##grid_rows_minus_monitor_{monitor_index}", "secondary", imgui.ImVec2(28, 0)):
        save_grid_monitor_layout(monitor_index, max(1, rows_base - 1), cols_base, "custom")
    imgui.same_line()
    imgui.text(f"Rows: {rows_base}")
    imgui.same_line()
    if themed_button(f"+##grid_rows_plus_monitor_{monitor_index}", "secondary", imgui.ImVec2(28, 0)):
        save_grid_monitor_layout(monitor_index, rows_base + 1, cols_base, "custom")

    imgui.same_line()
    imgui.text("   ")

    imgui.same_line()
    if themed_button(f"-##grid_cols_minus_monitor_{monitor_index}", "secondary", imgui.ImVec2(28, 0)):
        save_grid_monitor_layout(monitor_index, rows_base, max(1, cols_base - 1), "custom")
    imgui.same_line()
    imgui.text(f"Columns: {cols_base}")
    imgui.same_line()
    if themed_button(f"+##grid_cols_plus_monitor_{monitor_index}", "secondary", imgui.ImVec2(28, 0)):
        save_grid_monitor_layout(monitor_index, rows_base, cols_base + 1, "custom")

    imgui.spacing()
    custom_active = int(monitor_index) in grid_custom_merge_active_indices
    if themed_button(
        f"Custom Merge##grid_custom_merge_monitor_{monitor_index}",
        "primary" if custom_active else "secondary",
    ):
        if custom_active:
            grid_custom_merge_active_indices.discard(int(monitor_index))
            log_history.append(f"Grid Custom - Merge editing disabled for Monitor {monitor_index + 1}.")
        else:
            grid_custom_merge_active_indices.add(int(monitor_index))
            log_history.append(f"Grid Custom - Merge editing enabled for Monitor {monitor_index + 1}. Right-click and drag over cells.")
    imgui.same_line()
    if themed_button(f"Clear Custom##grid_custom_clear_monitor_{monitor_index}", "secondary"):
        clear_grid_custom_merges_for_monitor(monitor_index)
    if custom_active:
        ui_text_muted("Right-click, drag over cells, release to merge them into one visible grid area.")


def _imgui_vec2_xy(value):
    try:
        return float(value.x), float(value.y)
    except Exception:
        try:
            return float(value[0]), float(value[1])
        except Exception:
            return 0.0, 0.0


def _point_in_rect(px: float, py: float, left: float, top: float, right: float, bottom: float) -> bool:
    return left <= px <= right and top <= py <= bottom


def _is_left_mouse_down() -> bool:
    try:
        return bool(imgui.is_mouse_down(0))
    except Exception:
        try:
            io = imgui.get_io()
            return bool(io.mouse_down[0])
        except Exception:
            return False


def _is_left_mouse_dragging(threshold: float = 4.0) -> bool:
    try:
        return bool(imgui.is_mouse_dragging(0, float(threshold)))
    except TypeError:
        try:
            return bool(imgui.is_mouse_dragging(0))
        except Exception:
            return False
    except Exception:
        return False


def _is_right_mouse_down() -> bool:
    try:
        return bool(imgui.is_mouse_down(1))
    except Exception:
        try:
            io = imgui.get_io()
            return bool(io.mouse_down[1])
        except Exception:
            return False


def _imgui_color_u32_from_rgba(color_value):
    try:
        rgba = tuple(color_value)
        if len(rgba) < 4:
            rgba = (rgba[0], rgba[1], rgba[2], 1.0)

        try:
            return imgui.get_color_u32_vec4(imgui.ImVec4(float(rgba[0]), float(rgba[1]), float(rgba[2]), float(rgba[3])))
        except Exception:
            pass

        try:
            return imgui.get_color_u32(imgui.ImVec4(float(rgba[0]), float(rgba[1]), float(rgba[2]), float(rgba[3])))
        except Exception:
            pass

        r = max(0, min(255, int(float(rgba[0]) * 255)))
        g = max(0, min(255, int(float(rgba[1]) * 255)))
        b = max(0, min(255, int(float(rgba[2]) * 255)))
        a = max(0, min(255, int(float(rgba[3]) * 255)))
        return (a << 24) | (b << 16) | (g << 8) | r
    except Exception:
        return 0xFFFFFFFF


def _imgui_window_flag_value(name: str) -> int:
    try:
        value = getattr(imgui.WindowFlags_, name)
        return int(value.value if hasattr(value, "value") else value)
    except Exception:
        return 0


def _push_style_var_safe(var_name: str, value) -> int:
    try:
        var_enum = getattr(imgui.StyleVar_, var_name)
        imgui.push_style_var(var_enum, value)
        return 1
    except Exception:
        return 0


def render_grid_drag_mouse_ghost():
    try:
        drag_label = get_grid_drag_label()
        if not drag_label:
            return

        mouse_pos = imgui.get_mouse_pos()
        mouse_x, mouse_y = _imgui_vec2_xy(mouse_pos)
        label = f"Dragging: {drag_label}"

        try:
            imgui.set_next_window_pos(imgui.ImVec2(mouse_x + 18.0, mouse_y + 18.0))
        except Exception:
            pass

        flags = 0
        for flag_name in (
            "no_title_bar",
            "no_resize",
            "no_move",
            "no_scrollbar",
            "no_scroll_with_mouse",
            "no_saved_settings",
            "no_inputs",
            "no_focus_on_appearing",
            "no_nav",
            "always_auto_resize",
        ):
            flags |= _imgui_window_flag_value(flag_name)

        pushed_colors = 0
        pushed_vars = 0
        try:
            pushed_colors += _push_style_color_safe("window_bg", ui_color("surface"))
            pushed_colors += _push_style_color_safe("border", ui_color("accent"))
            pushed_colors += _push_style_color_safe("text", ui_color("text"))
            pushed_vars += _push_style_var_safe("window_padding", imgui.ImVec2(10.0, 7.0))
            pushed_vars += _push_style_var_safe("window_rounding", 6.0)
            pushed_vars += _push_style_var_safe("window_border_size", 1.0)
        except Exception:
            pass

        opened = False
        try:
            result = imgui.begin("Grid Drag Preview##grid_drag_mouse_ghost", None, flags)
            opened = bool(result[0]) if isinstance(result, tuple) else bool(result)
        except TypeError:
            try:
                opened = bool(imgui.begin("Grid Drag Preview##grid_drag_mouse_ghost", flags))
            except Exception:
                opened = False
        except Exception:
            opened = False

        if opened:
            try:
                imgui.push_style_color(imgui.Col_.text, ui_color("accent"))
                imgui.text("DRAG")
                imgui.pop_style_color()
                imgui.same_line()
                imgui.text(str(drag_label))
            except Exception:
                try:
                    imgui.text(label)
                except Exception:
                    pass

        try:
            imgui.end()
        except Exception:
            pass

        if pushed_vars:
            try:
                imgui.pop_style_var(pushed_vars)
            except Exception:
                pass

        if pushed_colors:
            try:
                imgui.pop_style_color(pushed_colors)
            except Exception:
                pass


        if not opened:
            try:
                imgui.set_tooltip(label)
            except Exception:
                pass
    except Exception:
        pass


def _auto_scroll_current_child_while_dragging(mouse_x: float, mouse_y: float, left: float, top: float, right: float, bottom: float):
    try:
        if grid_preview_drag_source_location is None:
            return
        if not _is_left_mouse_down():
            return
        if not _point_in_rect(mouse_x, mouse_y, left, top, right, bottom):
            return

        edge = 22.0
        step_x = 6.0
        step_y = 5.0

        try:
            scroll_x = float(imgui.get_scroll_x())
        except Exception:
            scroll_x = 0.0

        try:
            scroll_y = float(imgui.get_scroll_y())
        except Exception:
            scroll_y = 0.0

        if mouse_x > right - edge:
            try:
                imgui.set_scroll_x(scroll_x + step_x)
            except Exception:
                pass
        elif mouse_x < left + edge:
            try:
                imgui.set_scroll_x(max(0.0, scroll_x - step_x))
            except Exception:
                pass

        if mouse_y > bottom - edge:
            try:
                imgui.set_scroll_y(scroll_y + step_y)
            except Exception:
                pass
        elif mouse_y < top + edge:
            try:
                imgui.set_scroll_y(max(0.0, scroll_y - step_y))
            except Exception:
                pass
    except Exception:
        pass


def _begin_grid_preview_tile(tile_id: str, width: float, height: float, is_drag_source: bool = False):
    pushed_colors = 0
    pushed_vars = 0

    try:
        bg = ui_color("surface_alt") if is_drag_source else ui_color("surface_row")
        pushed_colors += _push_style_color_safe("child_bg", bg)
        pushed_colors += _push_style_color_safe("border", ui_color("accent") if is_drag_source else ui_color("border"))
    except Exception:
        pushed_colors = 0


    try:
        imgui.push_style_var(imgui.StyleVar_.window_padding, imgui.ImVec2(3, 2))
        pushed_vars += 1
    except Exception:
        pass

    imgui.begin_child(
        str_id=tile_id,
        size=imgui.ImVec2(width, height),
        child_flags=int(imgui.ChildFlags_.borders.value),
        window_flags=int(imgui.WindowFlags_.no_scrollbar.value) | int(imgui.WindowFlags_.no_scroll_with_mouse.value),
    )
    return pushed_colors, pushed_vars


def _end_grid_preview_tile(pushed):
    pushed_colors = 0
    pushed_vars = 0

    try:
        if isinstance(pushed, tuple):
            pushed_colors, pushed_vars = pushed
        else:
            pushed_colors = int(pushed or 0)
    except Exception:
        pushed_colors = 0
        pushed_vars = 0

    imgui.end_child()

    if pushed_vars:
        try:
            imgui.pop_style_var(pushed_vars)
        except Exception:
            pass

    if pushed_colors:
        try:
            imgui.pop_style_color(pushed_colors)
        except Exception:
            pass


def render_grid_preview_for_monitor(selected_accounts, monitor_index: int, monitor: dict, rows: int, cols: int):
    global grid_preview_drag_source_location, grid_preview_drag_source_index, grid_preview_drag_source_key, grid_preview_drag_had_motion
    global grid_custom_merge_drag_start, grid_custom_merge_drag_current
    global grid_click_swap_source_location, grid_click_swap_source_key

    selected_accounts = list(selected_accounts or [])
    count = len(selected_accounts)
    if count <= 0:
        ui_text_muted("No accounts selected.")
        return False

    rows = max(1, int(rows))
    cols = max(1, int(cols))
    capacity = rows * cols
    slots = get_grid_slots_for_monitor(selected_accounts, monitor_index, capacity)
    merge_by_start, covered_slots = get_grid_custom_merge_maps(monitor_index, rows, cols)
    custom_active = int(monitor_index) in grid_custom_merge_active_indices

    imgui.text_wrapped(
        f"{monitor.get('label', f'Monitor {monitor_index + 1}')} - "
        f"Layout: {rows}x{cols} - "
        f"{monitor.get('work_width', monitor.get('width', 0))}x"
        f"{monitor.get('work_height', monitor.get('height', 0))}"
    )

    min_cell_w = 104.0
    min_cell_h = 44.0
    gap = 3.0
    padding_x = 6.0
    padding_y = 6.0

    available_preview_width, _ = _imgui_avail_size(520.0, 240.0)
    viewport_width = max(260.0, min(740.0, available_preview_width - 12.0))
    viewport_height = max(170.0, min(300.0, viewport_width * 0.46))

    inner_viewport_width = max(1.0, viewport_width - 4.0)
    inner_viewport_height = max(1.0, viewport_height - 4.0)

    distributed_cell_w = (
        inner_viewport_width
        - (padding_x * 2.0)
        - gap * max(0, cols - 1)
    ) / max(1, cols)
    cell_w = max(min_cell_w, distributed_cell_w)
    cell_h = min_cell_h

    content_width = (padding_x * 2.0) + cols * cell_w + gap * max(0, cols - 1)
    content_height = (padding_y * 2.0) + rows * cell_h + gap * max(0, rows - 1)

    overflow_x = content_width > inner_viewport_width + 1.0
    overflow_y = content_height > inner_viewport_height + 1.0

    mouse_pos = imgui.get_mouse_pos()
    mouse_x, mouse_y = _imgui_vec2_xy(mouse_pos)

    try:
        mouse_clicked = bool(imgui.is_mouse_clicked(0))
    except Exception:
        mouse_clicked = False

    try:
        mouse_released = bool(imgui.is_mouse_released(0))
    except Exception:
        mouse_released = False

    left_dragging = _is_left_mouse_dragging()
    if grid_preview_drag_source_location is not None and left_dragging:
        grid_preview_drag_had_motion = True

    try:
        right_clicked = bool(imgui.is_mouse_clicked(1))
    except Exception:
        right_clicked = False

    try:
        right_released = bool(imgui.is_mouse_released(1))
    except Exception:
        right_released = False

    right_down = _is_right_mouse_down()

    try:
        right_double_clicked = bool(imgui.is_mouse_double_clicked(1))
    except Exception:
        right_double_clicked = False

    drop_target_location = None
    click_target_location = None
    drop_handled = False
    hover_slot_index = None

    pushed_monitor = 0
    try:
        pushed_monitor += _push_style_color_safe("child_bg", ui_color("card_bg"))
        pushed_monitor += _push_style_color_safe("border", ui_color("border_strong"))
    except Exception:
        pushed_monitor = 0

    if overflow_x or overflow_y:
        ui_text_muted("Preview scrolls only when the grid is larger than the preview window.")

    child_screen_pos = imgui.get_cursor_screen_pos()
    child_left, child_top = _imgui_vec2_xy(child_screen_pos)
    child_right = child_left + viewport_width
    child_bottom = child_top + viewport_height

    monitor_flags = 0
    if overflow_x:
        monitor_flags |= int(imgui.WindowFlags_.horizontal_scrollbar.value)
    try:
        imgui.begin_child(
            str_id=f"GridPreviewMonitor_{monitor_index}",
            size=imgui.ImVec2(viewport_width, viewport_height),
            child_flags=int(imgui.ChildFlags_.borders.value),
            window_flags=monitor_flags,
        )
    except TypeError:
        imgui.begin_child(f"GridPreviewMonitor_{monitor_index}", imgui.ImVec2(viewport_width, viewport_height), True)

    _auto_scroll_current_child_while_dragging(mouse_x, mouse_y, child_left, child_top, child_right, child_bottom)

    if (
        custom_active
        and grid_custom_merge_drag_start is not None
        and grid_custom_merge_drag_start[0] == int(monitor_index)
        and grid_custom_merge_drag_current is not None
    ):
        start_slot = int(grid_custom_merge_drag_start[1])
        current_slot = int(grid_custom_merge_drag_current)
        start_row, start_col = divmod(start_slot, cols)
        current_row, current_col = divmod(current_slot, cols)
        selection_rows = range(min(start_row, current_row), max(start_row, current_row) + 1)
        selection_cols = range(min(start_col, current_col), max(start_col, current_col) + 1)
        selection_slots = {r * cols + c for r in selection_rows for c in selection_cols}
    else:
        selection_slots = set()

    for row in range(rows):
        for col in range(cols):
            slot_index = row * cols + col
            if slot_index in covered_slots:
                continue

            merge_rect = merge_by_start.get(slot_index)
            if merge_rect:
                row_span = max(1, int(merge_rect.get("row_span", 1)))
                col_span = max(1, int(merge_rect.get("col_span", 1)))
            else:
                row_span = 1
                col_span = 1

            try:
                tile_x = padding_x + col * (cell_w + gap)
                tile_y = padding_y + row * (cell_h + gap)
                imgui.set_cursor_pos(imgui.ImVec2(tile_x, tile_y))
            except Exception:
                pass

            tile_w = cell_w * col_span + gap * max(0, col_span - 1)
            tile_h = cell_h * row_span + gap * max(0, row_span - 1)

            account = slots[slot_index] if slot_index < len(slots) else None
            running = False
            display_name = ""

            if account is not None:
                display_name = get_account_display_name(account) or f"Account {slot_index + 1}"
                running, _pid = get_account_running_status(account)

            rect_min = imgui.get_cursor_screen_pos()
            left, top = _imgui_vec2_xy(rect_min)
            right = left + tile_w
            bottom = top + tile_h
            is_mouse_inside = _point_in_rect(mouse_x, mouse_y, left, top, right, bottom)

            if is_mouse_inside:
                hover_slot_index = slot_index

            if (
                account is not None
                and mouse_clicked
                and is_mouse_inside
                and grid_preview_drag_source_location is None
            ):
                grid_preview_drag_source_location = (monitor_index, slot_index)
                grid_preview_drag_source_index = slot_index
                try:
                    source_slots = grid_monitor_slot_keys.get(int(monitor_index), [])
                    grid_preview_drag_source_key = source_slots[int(slot_index)]
                except Exception:
                    grid_preview_drag_source_key = get_grid_account_key(account)
                grid_preview_drag_had_motion = False

            if mouse_released and is_mouse_inside:
                click_target_location = (monitor_index, slot_index)

            if grid_preview_drag_source_location is not None and mouse_released and is_mouse_inside:
                drop_target_location = (monitor_index, slot_index)

            if merge_rect and right_double_clicked and is_mouse_inside:
                remove_grid_custom_merge_at_slot(monitor_index, slot_index, rows, cols)
                merge_by_start, covered_slots = get_grid_custom_merge_maps(monitor_index, rows, cols)
                drop_handled = True

            if custom_active and right_clicked and is_mouse_inside:
                grid_custom_merge_drag_start = (int(monitor_index), int(slot_index))
                grid_custom_merge_drag_current = int(slot_index)

            if custom_active and grid_custom_merge_drag_start is not None and grid_custom_merge_drag_start[0] == int(monitor_index) and is_mouse_inside:
                grid_custom_merge_drag_current = int(slot_index)

            is_drag_source = grid_preview_drag_source_location == (monitor_index, slot_index)
            is_merge_selection = slot_index in selection_slots
            pushed = _begin_grid_preview_tile(f"GridPreviewTile_{monitor_index}_{row}_{col}", tile_w, tile_h, is_drag_source)

            if is_merge_selection:
                imgui.push_style_color(imgui.Col_.text, ui_color("warning"))
                imgui.text("MERGE")
                imgui.pop_style_color()
                if account is not None:
                    imgui.same_line()

            if account is None:
                imgui.push_style_color(imgui.Col_.text, ui_color("muted"))
                imgui.text(f"{slot_index + 1}")
                imgui.pop_style_color()
                imgui.same_line()
                ui_text_muted("Empty")
            else:
                name_chars = max(8, int(tile_w / 7.0) - 2)
                short_name = display_name
                if len(short_name) > name_chars:
                    short_name = short_name[:max(1, name_chars - 3)] + "..."

                imgui.push_style_color(imgui.Col_.text, ui_color("accent"))
                imgui.text(str(slot_index + 1))
                imgui.pop_style_color()

                imgui.same_line()
                imgui.text(short_name)

                status_text = "Running" if running else "Stopped"
                status_color = ui_color("success") if running else ui_color("danger")
                imgui.push_style_color(imgui.Col_.text, status_color)
                imgui.text(status_text)
                imgui.pop_style_color()

            if merge_rect:
                imgui.push_style_color(imgui.Col_.text, ui_color("warning"))
                imgui.text(f"Merged {row_span}x{col_span}")
                imgui.pop_style_color()

            _end_grid_preview_tile(pushed)

    if custom_active and grid_custom_merge_drag_start is not None and grid_custom_merge_drag_start[0] == int(monitor_index):
        should_finish_merge = bool(right_released or not right_down)
        if should_finish_merge:
            try:
                start_slot = int(grid_custom_merge_drag_start[1])
                end_slot_value = grid_custom_merge_drag_current if grid_custom_merge_drag_current is not None else hover_slot_index
                if end_slot_value is not None:
                    add_grid_custom_merge_rect(monitor_index, start_slot, int(end_slot_value), rows, cols)
            except Exception as e:
                log_history.append(f"Grid Custom - Merge failed: {str(e)}")
            grid_custom_merge_drag_start = None
            grid_custom_merge_drag_current = None

    if overflow_x or overflow_y:
        try:
            target_x = max(0.0, content_width - 1.0) if overflow_x else 0.0
            target_y = max(0.0, content_height - 1.0) if overflow_y else 0.0
            imgui.set_cursor_pos(imgui.ImVec2(target_x, target_y))
            try:
                imgui.dummy(imgui.ImVec2(1.0, 1.0))
            except Exception:
                pass
        except Exception:
            pass

    imgui.end_child()
    if pushed_monitor:
        try:
            imgui.pop_style_color(pushed_monitor)
        except Exception:
            pass

    if mouse_released and grid_preview_drag_source_location is not None and drop_target_location is not None:
        source_monitor, source_slot = grid_preview_drag_source_location
        target_monitor, target_slot = drop_target_location

        if grid_preview_drag_had_motion:
            source_merge_rect, _source_rows, _source_cols = get_grid_merge_rect_for_start_slot(source_monitor, source_slot)
            if source_merge_rect:
                move_grid_merged_block_between_monitors(source_monitor, source_slot, target_monitor, target_slot)
            else:
                move_grid_account_between_monitors(source_monitor, source_slot, target_monitor, target_slot)
            grid_click_swap_source_location = None
            grid_click_swap_source_key = None
        else:
            if grid_click_swap_source_location is not None:
                click_source_monitor, click_source_slot = grid_click_swap_source_location
                handle_grid_click_account_swap(click_source_monitor, click_source_slot, target_monitor, target_slot)
                drop_handled = True
            else:
                grid_click_swap_source_location = (source_monitor, source_slot)
                grid_click_swap_source_key = grid_preview_drag_source_key

        grid_preview_drag_source_location = None
        grid_preview_drag_source_index = None
        grid_preview_drag_source_key = None
        grid_preview_drag_had_motion = False
        drop_handled = True

    elif mouse_released and grid_preview_drag_source_location is None and grid_click_swap_source_location is not None and click_target_location is not None:
        target_monitor, target_slot = click_target_location
        click_source_monitor, click_source_slot = grid_click_swap_source_location
        handle_grid_click_account_swap(click_source_monitor, click_source_slot, target_monitor, target_slot)
        drop_handled = True

    return drop_handled


def render_multi_monitor_grid_preview(selected_accounts, monitors, selected_monitor_indices, monitor_layouts):
    global grid_preview_drag_source_location, grid_preview_drag_source_index, grid_preview_drag_source_key, grid_preview_drag_had_motion

    render_grid_drag_mouse_ghost()

    any_drop_handled = False
    for order_index, monitor_index in enumerate(selected_monitor_indices):
        if order_index > 0:
            imgui.spacing()
            imgui.separator()
            imgui.spacing()

        layout = monitor_layouts.get(monitor_index)
        if not layout:
            continue

        if render_grid_preview_for_monitor(
            selected_accounts,
            monitor_index,
            monitors[monitor_index],
            layout["rows"],
            layout["cols"],
        ):
            any_drop_handled = True

    try:
        mouse_released = bool(imgui.is_mouse_released(0))
    except Exception:
        mouse_released = False

    if mouse_released and not any_drop_handled:
        grid_preview_drag_source_location = None
        grid_preview_drag_source_index = None
        grid_preview_drag_source_key = None
        grid_preview_drag_had_motion = False


def render_grid_preview(selected_accounts, monitor, rows: int, cols: int):
    monitor_index = 0
    sync_multi_monitor_grid_slots(selected_accounts, [monitor_index], {monitor_index: max(1, int(rows)) * max(1, int(cols))})
    monitor_layouts = {monitor_index: {"rows": max(1, int(rows)), "cols": max(1, int(cols))}}
    render_multi_monitor_grid_preview(selected_accounts, [monitor], [monitor_index], monitor_layouts)

def load_grid_saved_layouts_from_ini():
    try:
        raw_value = ini_handler.read_key(LAYOUT_CONFIG_SECTION, GRID_SAVED_LAYOUTS_INI_KEY, "")
        if not raw_value:
            return {}

        data = json.loads(raw_value)
        if not isinstance(data, dict):
            return {}

        result = {}
        for name, layout in data.items():
            clean_name = str(name or "").strip()
            if not clean_name or not isinstance(layout, dict):
                continue

            if isinstance(layout.get("monitor_layout"), dict):
                monitor_layout = layout.get("monitor_layout", {})
                merge_rects = layout.get("merge_rects", [])
            else:
                monitor_layouts_raw = layout.get("monitor_layouts", {})
                merge_rects_raw = layout.get("merge_rects", {})
                monitor_layout = {}
                merge_rects = []
                if isinstance(monitor_layouts_raw, dict) and monitor_layouts_raw:
                    first_key = sorted(
                        monitor_layouts_raw.keys(),
                        key=lambda value: int(value) if str(value).isdigit() else 999999,
                    )[0]
                    monitor_layout = monitor_layouts_raw.get(first_key, {})
                    if isinstance(merge_rects_raw, dict):
                        merge_rects = merge_rects_raw.get(first_key, [])

            if not isinstance(monitor_layout, dict):
                continue

            clean_rects = []
            if isinstance(merge_rects, list):
                for rect in merge_rects:
                    if not isinstance(rect, dict):
                        continue
                    row = max(0, int(rect.get("row", 0)))
                    col = max(0, int(rect.get("col", 0)))
                    row_span = max(1, int(rect.get("row_span", 1)))
                    col_span = max(1, int(rect.get("col_span", 1)))
                    if row_span <= 1 and col_span <= 1:
                        continue
                    clean_rects.append({
                        "row": row,
                        "col": col,
                        "row_span": row_span,
                        "col_span": col_span,
                    })

            result[clean_name] = {
                "monitor_layout": {
                    "mode": str(monitor_layout.get("mode", "custom") or "custom"),
                    "rows": max(1, int(monitor_layout.get("rows", 1))),
                    "cols": max(1, int(monitor_layout.get("cols", 1))),
                },
                "merge_rects": clean_rects,
            }

        return result
    except Exception as e:
        log_history.append(f"Grid Layouts - Failed to load saved layouts: {str(e)}")
        return {}


def persist_grid_saved_layouts():
    try:
        raw_value = json.dumps(grid_saved_layouts, ensure_ascii=False, separators=(",", ":"))
        write_launcher_layout_value_if_changed(GRID_SAVED_LAYOUTS_INI_KEY, raw_value)
    except Exception as e:
        log_history.append(f"Grid Layouts - Failed to save saved layouts: {str(e)}")


def ensure_grid_saved_layouts_loaded():
    global grid_saved_layouts, grid_saved_layouts_loaded

    if grid_saved_layouts_loaded:
        return

    grid_saved_layouts = load_grid_saved_layouts_from_ini()
    grid_saved_layouts_loaded = True


def capture_current_grid_named_layout(source_monitor_index: int):
    ensure_grid_custom_merge_state_loaded()

    source_monitor_index = int(source_monitor_index)
    layout = get_grid_monitor_layout(source_monitor_index)
    rects = list(grid_monitor_custom_merge_rects.get(source_monitor_index, []) or [])

    return {
        "monitor_layout": {
            "mode": str(layout.get("mode", "custom") or "custom"),
            "rows": max(1, int(layout.get("rows", 1))),
            "cols": max(1, int(layout.get("cols", 1))),
        },
        "merge_rects": [
            {
                "row": int(rect.get("row", 0)),
                "col": int(rect.get("col", 0)),
                "row_span": max(1, int(rect.get("row_span", 1))),
                "col_span": max(1, int(rect.get("col_span", 1))),
            }
            for rect in rects
        ],
    }


def save_grid_named_layout(layout_name: str, source_monitor_index: int):
    ensure_grid_saved_layouts_loaded()

    clean_name = str(layout_name or "").strip()
    if not clean_name:
        log_history.append("Grid Layouts - Save failed: layout name is empty.")
        return False

    grid_saved_layouts[clean_name] = capture_current_grid_named_layout(source_monitor_index)
    persist_grid_saved_layouts()
    log_history.append(f"Grid Layouts - Saved monitor layout '{clean_name}' from Monitor {int(source_monitor_index) + 1}.")
    return True


def apply_grid_named_layout(layout_name: str, target_monitor_indices):
    global grid_saved_layout_selected
    global grid_monitor_custom_merge_rects

    ensure_grid_saved_layouts_loaded()
    ensure_grid_custom_merge_state_loaded()

    clean_name = str(layout_name or "").strip()
    layout = grid_saved_layouts.get(clean_name)
    if not isinstance(layout, dict):
        log_history.append(f"Grid Layouts - Load failed, layout not found: {clean_name}")
        return False

    monitor_layout = layout.get("monitor_layout", {})
    merge_rects = list(layout.get("merge_rects", []) or [])
    if not isinstance(monitor_layout, dict):
        log_history.append(f"Grid Layouts - Load failed, invalid layout: {clean_name}")
        return False

    targets = []
    for value in list(target_monitor_indices or []):
        try:
            monitor_index = int(value)
        except Exception:
            continue
        if monitor_index not in targets:
            targets.append(monitor_index)

    if not targets:
        log_history.append("Grid Layouts - Load failed: no target monitor selected.")
        return False

    for monitor_index in targets:
        save_grid_monitor_layout(
            monitor_index,
            max(1, int(monitor_layout.get("rows", 1))),
            max(1, int(monitor_layout.get("cols", 1))),
            str(monitor_layout.get("mode", "custom") or "custom"),
        )
        grid_monitor_custom_merge_rects[monitor_index] = [
            {
                "row": max(0, int(rect.get("row", 0))),
                "col": max(0, int(rect.get("col", 0))),
                "row_span": max(1, int(rect.get("row_span", 1))),
                "col_span": max(1, int(rect.get("col_span", 1))),
            }
            for rect in merge_rects
            if isinstance(rect, dict)
        ]

    persist_grid_custom_merge_state()
    for monitor_index in targets:
        target_layout = get_grid_monitor_layout(monitor_index)
        target_rows = max(1, int(target_layout.get("rows", 1)))
        target_cols = max(1, int(target_layout.get("cols", 1)))
        compact_grid_slots_for_custom_merges(
            monitor_index,
            target_rows,
            target_cols,
        )
        refill_missing_grid_accounts_for_monitor(
            get_all_selected_launch_accounts(),
            monitor_index,
            target_rows,
            target_cols,
        )
    grid_saved_layout_selected = clean_name
    log_history.append(f"Grid Layouts - Loaded layout '{clean_name}' to {len(targets)} monitor(s).")
    return True


def rename_grid_named_layout(old_name: str, new_name: str):
    global grid_saved_layout_selected

    ensure_grid_saved_layouts_loaded()
    old_clean = str(old_name or "").strip()
    new_clean = str(new_name or "").strip()

    if not old_clean or old_clean not in grid_saved_layouts:
        log_history.append("Grid Layouts - Rename failed: select an existing layout.")
        return False

    if not new_clean:
        log_history.append("Grid Layouts - Rename failed: new name is empty.")
        return False

    if new_clean != old_clean and new_clean in grid_saved_layouts:
        log_history.append(f"Grid Layouts - Rename failed, name already exists: {new_clean}")
        return False

    grid_saved_layouts[new_clean] = grid_saved_layouts.pop(old_clean)
    grid_saved_layout_selected = new_clean
    persist_grid_saved_layouts()
    log_history.append(f"Grid Layouts - Renamed layout from '{old_clean}' to '{new_clean}'.")
    return True


def delete_grid_named_layout(layout_name: str):
    global grid_saved_layout_selected, grid_saved_layout_delete_confirm_name, grid_saved_layout_delete_confirm_requested_at

    ensure_grid_saved_layouts_loaded()
    clean_name = str(layout_name or "").strip()
    if clean_name not in grid_saved_layouts:
        log_history.append("Grid Layouts - Delete failed: select an existing layout.")
        return False

    del grid_saved_layouts[clean_name]
    if grid_saved_layout_selected == clean_name:
        grid_saved_layout_selected = ""
    grid_saved_layout_delete_confirm_name = ""
    grid_saved_layout_delete_confirm_requested_at = 0.0
    persist_grid_saved_layouts()
    log_history.append(f"Grid Layouts - Deleted layout: {clean_name}")
    return True


def get_grid_effective_area_count(monitor_index: int, rows: int, cols: int):
    rows = max(1, int(rows))
    cols = max(1, int(cols))
    _merge_by_start, covered_slots = get_grid_custom_merge_maps(monitor_index, rows, cols)
    return max(0, rows * cols - len(covered_slots))



def grid_input_text_hint(input_id: str, value: str, hint: str, width: float, max_length: int = 128):
    imgui.set_next_item_width(width)
    try:
        return imgui.input_text_with_hint(input_id, hint, value, max_length)
    except Exception:
        try:
            return imgui.input_text_with_hint(
                label=input_id,
                hint=hint,
                str=value,
            )
        except Exception:
            return imgui.input_text(input_id, value, max_length)


def render_grid_saved_layout_controls(selected_monitor_indices):
    global grid_saved_layout_selected, grid_saved_layout_name, grid_saved_layout_rename_name
    global grid_saved_layout_source_monitor_index, grid_saved_layout_target_monitor_index
    global grid_saved_layout_delete_confirm_name, grid_saved_layout_delete_confirm_requested_at

    ensure_grid_saved_layouts_loaded()

    selected_monitor_indices = [int(index) for index in list(selected_monitor_indices or [])]
    if not selected_monitor_indices:
        ui_text_muted("No active monitor selected for layout save/load.")
        return

    saved_names = sorted(grid_saved_layouts.keys())
    if grid_saved_layout_selected not in saved_names:
        grid_saved_layout_selected = saved_names[0] if saved_names else ""

    ui_section_header("Saved custom layouts", "Save, load, rename, or delete monitor layout templates.")

    panel_width, _ = _imgui_avail_size(640.0, 180.0)
    input_width = max(150.0, min(240.0, panel_width - 430.0))
    button_width = 96.0
    monitor_labels = [f"Monitor {index + 1}" for index in selected_monitor_indices]

    if grid_saved_layout_source_monitor_index not in selected_monitor_indices:
        grid_saved_layout_source_monitor_index = selected_monitor_indices[0]
    if grid_saved_layout_target_monitor_index not in selected_monitor_indices and grid_saved_layout_target_monitor_index >= 0:
        grid_saved_layout_target_monitor_index = selected_monitor_indices[0]

    source_index = selected_monitor_indices.index(grid_saved_layout_source_monitor_index)
    target_index = selected_monitor_indices.index(grid_saved_layout_target_monitor_index) if grid_saved_layout_target_monitor_index in selected_monitor_indices else 0

    _changed_name, grid_saved_layout_name = grid_input_text_hint(
        "##grid_saved_layout_name",
        grid_saved_layout_name,
        "Layout Name",
        input_width,
    )
    imgui.same_line()
    imgui.set_next_item_width(128)
    changed_source, source_index = imgui.combo("##grid_saved_layout_source_monitor", source_index, monitor_labels)
    if changed_source and 0 <= source_index < len(selected_monitor_indices):
        grid_saved_layout_source_monitor_index = selected_monitor_indices[source_index]
    imgui.same_line()
    if themed_button("Save Layout##grid_saved_layout_save", "primary", imgui.ImVec2(button_width, 0)):
        saved_name = str(grid_saved_layout_name or "").strip()
        if save_grid_named_layout(saved_name, grid_saved_layout_source_monitor_index):
            grid_saved_layout_selected = saved_name
            grid_saved_layout_name = ""

    if saved_names:
        selected_index = saved_names.index(grid_saved_layout_selected) if grid_saved_layout_selected in saved_names else 0
        imgui.set_next_item_width(input_width)
        changed_layout, selected_index = imgui.combo("##grid_saved_layout_select", selected_index, saved_names)
        if changed_layout and 0 <= selected_index < len(saved_names):
            grid_saved_layout_selected = saved_names[selected_index]
            grid_saved_layout_delete_confirm_name = ""
            grid_saved_layout_delete_confirm_requested_at = 0.0

        imgui.same_line()
        target_options = ["All"] + monitor_labels
        target_index_ui = 0 if grid_saved_layout_target_monitor_index < 0 else target_index + 1
        imgui.set_next_item_width(128)
        changed_target, target_index_ui = imgui.combo("##grid_saved_layout_target_monitor", target_index_ui, target_options)
        if changed_target:
            if target_index_ui == 0:
                grid_saved_layout_target_monitor_index = -1
            else:
                monitor_option_index = target_index_ui - 1
                if 0 <= monitor_option_index < len(selected_monitor_indices):
                    grid_saved_layout_target_monitor_index = selected_monitor_indices[monitor_option_index]

        imgui.same_line()
        target_monitors = selected_monitor_indices if grid_saved_layout_target_monitor_index < 0 else [grid_saved_layout_target_monitor_index]
        if themed_button("Load##grid_saved_layout_load", "secondary", imgui.ImVec2(66, 0)):
            apply_grid_named_layout(grid_saved_layout_selected, target_monitors)
        imgui.same_line()
        if themed_button("Delete##grid_saved_layout_delete", "danger", imgui.ImVec2(66, 0)):
            grid_saved_layout_delete_confirm_name = str(grid_saved_layout_selected or "")
            grid_saved_layout_delete_confirm_requested_at = time.time()

        if grid_saved_layout_delete_confirm_name:
            imgui.same_line()
            ui_text_warning(f"Delete '{grid_saved_layout_delete_confirm_name}'?")
            imgui.same_line()
            if themed_button("Cancel##grid_saved_layout_delete_cancel", "secondary", imgui.ImVec2(66, 0)):
                grid_saved_layout_delete_confirm_name = ""
                grid_saved_layout_delete_confirm_requested_at = 0.0
            imgui.same_line()
            if themed_button("Confirm Delete##grid_saved_layout_delete_confirm", "danger", imgui.ImVec2(132, 0)):
                if time.time() - float(grid_saved_layout_delete_confirm_requested_at or 0.0) >= 0.35:
                    delete_grid_named_layout(grid_saved_layout_delete_confirm_name)

        _changed_rename, grid_saved_layout_rename_name = grid_input_text_hint(
            "##grid_saved_layout_rename",
            grid_saved_layout_rename_name,
            "Rename To",
            input_width,
        )
        imgui.same_line()
        if themed_button("Rename##grid_saved_layout_rename_button", "secondary", imgui.ImVec2(button_width, 0)):
            rename_grid_named_layout(grid_saved_layout_selected, grid_saved_layout_rename_name)
    else:
        ui_text_muted("No saved grid layouts yet.")



def show_grid_start_content():
    global grid_selected_monitor_index, grid_rows, grid_cols, grid_layout_mode
    global grid_preview_drag_source_location, grid_preview_drag_source_index, grid_preview_drag_source_key

    ensure_team_data_loaded()

    ui_section_header(
        "Grid-Start",
        "Distribute selected accounts from all teams."
    )

    selected_accounts = get_all_selected_launch_accounts()
    selected_count = len(selected_accounts)
    selected_team_count = get_all_selected_launch_team_count()
    total_team_count = len(team_manager.teams)

    if total_team_count <= 0:
        ui_text_muted("No teams loaded.")
        return

    ui_info_line("Teams", f"{selected_team_count} of {total_team_count} with selected accounts")
    ui_info_line("Selected total", str(selected_count))

    if selected_count <= 0:
        imgui.spacing()
        imgui.push_style_color(imgui.Col_.text, ui_color("warning"))
        imgui.text_wrapped("Select accounts on the left using the Launch Selected checkboxes. Grid Start uses the selection from all teams.")
        imgui.pop_style_color()
        return

    monitors = detect_display_monitors()
    selected_monitor_indices = get_selected_grid_monitor_indices(monitors)

    imgui.spacing()
    ui_section_header("Select monitors", f"{len(monitors)} monitor(s) detected")
    ui_text_muted("You can select one or more monitors, for example Monitor 1 and 3.")
    render_grid_monitor_cards(monitors, selected_monitor_indices)


    selected_monitor_indices = get_selected_grid_monitor_indices(monitors)


    monitor_layouts = {}
    monitor_capacities = {}
    for monitor_position, monitor_index in enumerate(selected_monitor_indices):
        monitor = monitors[monitor_index]
        rows_effective, cols_effective = get_effective_grid_dimensions_for_monitor(
            monitor_index,
            monitor,
            selected_count,
            monitor_position,
            len(selected_monitor_indices),
        )
        monitor_layouts[monitor_index] = {
            "rows": rows_effective,
            "cols": cols_effective,
            "monitor": monitor,
        }
        monitor_capacities[monitor_index] = rows_effective * cols_effective

    sync_multi_monitor_grid_slots(selected_accounts, selected_monitor_indices, monitor_capacities)

    imgui.spacing()
    render_grid_saved_layout_controls(selected_monitor_indices)

    imgui.spacing()
    ui_section_header(
        "Layouts and preview per monitor",
        "Layout selection is directly above each monitor preview."
    )

    any_drop_handled = False

    for monitor_position, monitor_index in enumerate(selected_monitor_indices):
        monitor = monitors[monitor_index]

        if monitor_position > 0:
            imgui.spacing()
            imgui.separator()
            imgui.spacing()

        render_grid_layout_controls_for_monitor(
            monitor_index,
            monitor,
            selected_count,
            monitor_position,
            len(selected_monitor_indices),
        )

        rows_effective, cols_effective = get_effective_grid_dimensions_for_monitor(
            monitor_index,
            monitor,
            selected_count,
            monitor_position,
            len(selected_monitor_indices),
        )
        monitor_layouts[monitor_index] = {
            "rows": rows_effective,
            "cols": cols_effective,
            "monitor": monitor,
        }
        monitor_capacities[monitor_index] = rows_effective * cols_effective


        sync_multi_monitor_grid_slots(selected_accounts, selected_monitor_indices, monitor_capacities)

        imgui.spacing()
        ui_text_accent("Preview")
        ui_text_muted("Drag & drop also works across monitors.")

        if render_grid_preview_for_monitor(
            selected_accounts,
            monitor_index,
            monitor,
            rows_effective,
            cols_effective,
        ):
            any_drop_handled = True


    render_grid_drag_mouse_ghost()

    try:
        mouse_released = bool(imgui.is_mouse_released(0))
    except Exception:
        mouse_released = False

    if mouse_released and not any_drop_handled:
        grid_preview_drag_source_location = None
        grid_preview_drag_source_index = None
        grid_preview_drag_source_key = None

    total_capacity = sum(
        get_grid_effective_area_count(
            monitor_index,
            monitor_layouts[monitor_index]["rows"],
            monitor_layouts[monitor_index]["cols"],
        )
        for monitor_index in selected_monitor_indices
        if monitor_index in monitor_layouts
    )
    if total_capacity < selected_count:
        imgui.spacing()
        imgui.push_style_color(imgui.Col_.text, ui_color("warning"))
        imgui.text_wrapped(
            f"Grid capacity too small: {total_capacity} slots for {selected_count} selected accounts. "
            f"Increase rows/columns on one of the selected monitors."
        )
        imgui.pop_style_color()

    if grid_custom_capacity_warning_message:
        imgui.spacing()
        imgui.push_style_color(imgui.Col_.text, ui_color("warning"))
        imgui.text_wrapped(grid_custom_capacity_warning_message)
        imgui.pop_style_color()

    imgui.spacing()
    if themed_button("Reset Grid##grid_preview_reset", "secondary"):
        reset_grid_order(selected_accounts)
        sync_multi_monitor_grid_slots(selected_accounts, selected_monitor_indices, monitor_capacities)

    imgui.same_line()

    running_accounts, missing_accounts = get_selected_running_missing_state(selected_accounts)
    has_grid_restart_missing = (
        selected_count >= 2
        and len(running_accounts) > 0
        and len(missing_accounts) > 0
    )

    grid_launch_button_label = (
        f"Restart Missing ({len(missing_accounts)})##grid_restart_missing"
        if has_grid_restart_missing
        else "Start Grid Launch##grid_launch_start"
    )

    def build_current_grid_launch_plan():
        if total_capacity < selected_count:
            log_history.append("Grid Launch - Cannot build plan: total grid capacity is too small.")
            return []
        launch_plan = get_multi_monitor_grid_launch_plan(
            selected_accounts,
            monitors,
            selected_monitor_indices,
            monitor_layouts,
        )
        if len(launch_plan) < selected_count:
            log_history.append(
                f"Grid Launch - Cannot build plan: only {len(launch_plan)} of {selected_count} accounts have grid slots."
            )
            return []
        return launch_plan

    if themed_button(grid_launch_button_label, "primary"):
        launch_plan = build_current_grid_launch_plan()
        if launch_plan:
            if has_grid_restart_missing:
                missing_ids = {id(account) for account in missing_accounts}
                restart_plan = [
                    item for item in launch_plan
                    if id(item.get("account")) in missing_ids
                ]

                if not restart_plan:
                    log_history.append("Grid Restart Missing - No missing selected accounts have grid slots.")
                else:
                    log_history.append(
                        f"Grid Restart Missing - Restarting {len(restart_plan)} missing account(s) "
                        f"in their existing grid slot(s)."
                    )
                    launch_gw.start_multi_monitor_grid_thread(get_grid_launch_context_team(), restart_plan)
            else:
                launch_gw.start_multi_monitor_grid_thread(get_grid_launch_context_team(), launch_plan)

    imgui.same_line()
    if themed_button("Apply to Running##grid_apply_running", "secondary"):
        launch_plan = build_current_grid_launch_plan()
        if launch_plan:
            apply_grid_layout_to_running_clients(launch_plan)


def apply_grid_layout_to_running_clients(launch_plan):
    def apply_worker():
        try:
            if not launch_plan:
                log_history.append("Grid Apply - No grid plan available.")
                return

            rect_cache = {}
            applied = 0
            skipped = 0

            for item in list(launch_plan or []):
                account = item.get("account")
                if account is None:
                    skipped += 1
                    continue

                running, pid = get_account_running_status(account)
                if not running or not pid:
                    skipped += 1
                    continue

                monitor = item.get("monitor") or {}
                monitor_index = int(item.get("monitor_index", 0))
                rows_safe = max(1, int(item.get("rows", 1)))
                cols_safe = max(1, int(item.get("cols", 1)))
                capacity = rows_safe * cols_safe
                slot_index = max(0, min(capacity - 1, int(item.get("slot_index", 0))))

                cache_key = (monitor_index, rows_safe, cols_safe)
                if cache_key not in rect_cache:
                    rect_cache[cache_key] = compute_grid_window_rects(monitor, rows_safe, cols_safe, capacity, monitor_index)

                window_rect = rect_cache[cache_key][slot_index]
                launch_gw.apply_window_config_async(pid, account, window_rect=window_rect)
                applied += 1

            log_history.append(f"Grid Apply - Applied current grid layout to {applied} running launcher-managed client(s). Skipped={skipped}.")
        except Exception as e:
            log_history.append(f"Grid Apply - Failed: {str(e)}")

    threading.Thread(target=apply_worker, daemon=True).start()


def set_gw_exe_update_enabled(enabled: bool):
    global gw_exe_update_enabled, gw_exe_update_last_auto_check, gw_exe_update_status_by_path

    gw_exe_update_enabled = bool(enabled)
    write_launcher_layout_value_if_changed("gw_exe_update_enabled", "true" if gw_exe_update_enabled else "false")
    if gw_exe_update_enabled:
        gw_exe_update_last_auto_check = 0.0
        log_history.append("GW.exe Update - Version check enabled. Startup check uses cache and slow background scans.")
        start_gw_exe_update_status_check(force=False)
    else:
        with gw_exe_update_lock:
            gw_exe_update_status_by_path = {}
        gw_exe_update_last_auto_check = 0.0
        log_history.append("GW.exe Update - Version check disabled.")


def render_performance_debug_panel():
    global perf_debug_enabled

    ui_section_header("Performance Debug", "local timing profiler")
    changed_perf, enabled_perf = imgui.checkbox(
        "Enable performance debug##perf_debug_enabled",
        bool(perf_debug_enabled),
    )
    if changed_perf:
        perf_debug_enabled = bool(enabled_perf)
        write_launcher_layout_value_if_changed("perf_debug_enabled", "true" if perf_debug_enabled else "false")
        if not perf_debug_enabled:
            perf_debug_reset_metrics()

    imgui.same_line()
    if themed_button("Reset Metrics##perf_debug_reset", "secondary", imgui.ImVec2(112, 0)):
        perf_debug_reset_metrics()

    ui_text_muted("Running/Stopped account status rescan is back at 1 second; heavy full process scans stay out of the render path.")
    ui_text_muted("Update/cache validation now uses fast mmap pattern search and yields between files in background workers.")
    ui_text_muted("Cache-hit metrics are sampled to avoid the profiler itself creating measurable overhead.")

    if not perf_debug_enabled:
        ui_text_muted("Enable this, reproduce the lag for 20-30 seconds, then check Total/Max columns.")
        return

    rows = perf_debug_get_rows()
    if not rows:
        ui_text_muted("No timing data yet.")
        return

    try:
        imgui.columns(6, "perf_debug_columns", True)
        imgui.text("Query")
        imgui.next_column()
        imgui.text("Count")
        imgui.next_column()
        imgui.text("Last ms")
        imgui.next_column()
        imgui.text("Avg ms")
        imgui.next_column()
        imgui.text("Max ms")
        imgui.next_column()
        imgui.text("Detail")
        imgui.next_column()
        imgui.separator()

        for name, values in rows[:28]:
            max_ms = float(values.get("max_ms", 0.0))
            color = "danger" if max_ms >= 50.0 else "warning" if max_ms >= 15.0 else "success"
            imgui.text(str(name))
            imgui.next_column()
            imgui.text(str(int(values.get("count", 0))))
            imgui.next_column()
            imgui.text(f"{float(values.get('last_ms', 0.0)):.2f}")
            imgui.next_column()
            imgui.text(f"{float(values.get('avg_ms', 0.0)):.2f}")
            imgui.next_column()
            render_colored_text(f"{max_ms:.2f}", color)
            imgui.next_column()
            ui_text_muted(str(values.get("detail", "")))
            imgui.next_column()

        imgui.columns(1)
    except Exception:
        for name, values in rows[:28]:
            imgui.text(f"{name}: count={int(values.get('count', 0))}, last={float(values.get('last_ms', 0.0)):.2f} ms, avg={float(values.get('avg_ms', 0.0)):.2f} ms, max={float(values.get('max_ms', 0.0)):.2f} ms")


def show_launcher_settings_content():
    global gw_exe_update_enabled

    ensure_team_data_loaded()

    ui_section_header("Launcher Settings", "Experimental options")
    render_performance_debug_panel()
    imgui.spacing()
    ui_section_header("GW.exe Update", "version check and local cache")

    changed_update, enabled_update = imgui.checkbox(
        "Enable GW.exe update check##gw_exe_update_enabled",
        bool(gw_exe_update_enabled),
    )
    if changed_update:
        set_gw_exe_update_enabled(bool(enabled_update))

    ui_text_muted("Default is off. Enable this only if you want to test the integrated Gw.exe version check and updater.")
    ui_text_muted("Startup check uses cached file versions and scans changed files slowly in the background.")
    ui_text_muted("Use Check Now for a forced refresh.")

    if not gw_exe_update_enabled:
        imgui.spacing()
        render_colored_text("GW.exe update check is disabled.", "warning")
    else:
        imgui.spacing()
        render_gw_exe_update_panel()


def render_launcher_config_tabs():
    global launcher_config_tab

    if launcher_config_tab not in ("account", "launch", "grid", "settings"):
        launcher_config_tab = "account"

    if credentials_are_locked():
        render_credential_security_panel()
        return

    if themed_button(
        "Account Configuration##advanced_account_tab",
        "primary" if launcher_config_tab == "account" else "secondary",
    ):
        launcher_config_tab = "account"
        write_launcher_layout_value_if_changed("advanced_config_tab", launcher_config_tab)

    imgui.same_line()
    if themed_button(
        "Launch Configuration##advanced_launch_tab",
        "primary" if launcher_config_tab == "launch" else "secondary",
    ):
        launcher_config_tab = "launch"
        write_launcher_layout_value_if_changed("advanced_config_tab", launcher_config_tab)

    imgui.same_line()
    if themed_button(
        "Grid Start##advanced_grid_tab",
        "primary" if launcher_config_tab == "grid" else "secondary",
    ):
        launcher_config_tab = "grid"
        write_launcher_layout_value_if_changed("advanced_config_tab", launcher_config_tab)

    imgui.same_line()
    if themed_button(
        "Launcher Settings##advanced_launcher_settings_tab",
        "primary" if launcher_config_tab == "settings" else "secondary",
    ):
        launcher_config_tab = "settings"
        write_launcher_layout_value_if_changed("advanced_config_tab", launcher_config_tab)

    imgui.separator()

    if launcher_config_tab == "launch":
        show_account_content()
    elif launcher_config_tab == "grid":
        show_grid_start_content()
    elif launcher_config_tab == "settings":
        show_launcher_settings_content()
    else:
        show_configuration_content()


def show_launcher_layout():
    global launcher_left_panel_width, launcher_console_height, launcher_left_panel_ratio, launcher_console_height_ratio

    if is_compact_view:
        show_team_view()
        return

    total_width, total_height = _imgui_avail_size(980.0, 660.0)
    if total_width < 1 or total_height < 1:
        return


    console_splitter_height = 6.0
    min_console = 95.0
    min_top = 220.0
    max_console = max(min_console, total_height - min_top - console_splitter_height - 12.0)

    desired_console_height = total_height * launcher_console_height_ratio
    rendered_console_height = _clamp_float(desired_console_height, min_console, max_console)
    launcher_console_height = rendered_console_height
    if total_height < (min_top + min_console + console_splitter_height + 12.0):
        rendered_console_height = max(70.0, total_height * launcher_console_height_ratio)

    top_height = max(120.0, total_height - rendered_console_height - console_splitter_height - 12.0)

    splitter_width = 6.0
    min_left = 170.0
    min_right = 360.0
    max_left = max(min_left, total_width - min_right - splitter_width - 12.0)

    desired_left_width = total_width * launcher_left_panel_ratio
    rendered_left_width = _clamp_float(desired_left_width, min_left, max_left)
    launcher_left_panel_width = rendered_left_width
    if total_width < (min_left + min_right + splitter_width + 12.0):

        rendered_left_width = max(120.0, total_width * launcher_left_panel_ratio)


    _begin_bordered_child("LauncherTeamsPane", rendered_left_width, top_height)
    show_team_view()
    _end_bordered_child()

    imgui.same_line()
    render_advanced_splitter(top_height, rendered_left_width, min_left, max_left, total_width)

    imgui.same_line()
    right_width = max(120.0, total_width - rendered_left_width - splitter_width - 18.0)
    _begin_bordered_child("LauncherConfigPane", right_width, top_height)
    render_launcher_config_tabs()
    _end_bordered_child()


    render_console_splitter(total_width, rendered_console_height, min_console, max_console, total_height)


    _begin_bordered_child("LauncherConsolePane", 0, rendered_console_height)
    show_log_console()
    _end_bordered_child()


def show_launcher_layout_themed():
    render_with_launcher_theme(show_launcher_layout)


def create_docking_splits() -> list[hello_imgui.DockingSplit]:
    global is_compact_view, visible_windows
    visible_windows["MainDockSpace"] = True
    visible_windows["AdvDockSpace"] = False
    visible_windows["ConsoleDockSpace"] = False
    return []


def create_dockable_windows() -> list[hello_imgui.DockableWindow]:
    global visible_windows

    if is_compact_view:
        visible_windows["MainDockSpace"] = True
        visible_windows["AdvDockSpace"] = False
        visible_windows["ConsoleDockSpace"] = False
        return [
            hello_imgui.DockableWindow(
                label_="Teams",
                dock_space_name_="MainDockSpace",
                gui_function_=show_team_view_themed,
                can_be_closed_=False,
                is_visible_=True
            )
        ]

    visible_windows["MainDockSpace"] = True
    visible_windows["AdvDockSpace"] = False
    visible_windows["ConsoleDockSpace"] = False
    return [
        hello_imgui.DockableWindow(
            label_="Py4GW Launcher",
            dock_space_name_="MainDockSpace",
            gui_function_=show_launcher_layout_themed,
            can_be_closed_=False,
            is_visible_=True
        )
    ]


def set_log_hide_clear_names(enabled: bool):
    global log_hide_clear_names

    log_hide_clear_names = bool(enabled)
    write_launcher_layout_value_if_changed("log_hide_clear_names", "true" if log_hide_clear_names else "false")

    if log_hide_clear_names:
        log_history.append("Console - Log now Clear Name Hiding. Copy/Save will mask account names.")
    else:
        log_history.append("Console - Log now Clear Name Visible. Copy/Save will include account names.")


def get_account_names_for_console_redaction():
    try:
        names = set()

        for team in team_manager.teams.values():
            for account in team.accounts:
                for attr_name in ("character_name", "custom_client_name", "gw_client_name"):
                    value = str(getattr(account, attr_name, "") or "").strip()
                    if len(value) >= 2:
                        names.add(value)


        try:
            for tracked_account, _tracked_pid in list(launch_gw.active_pids):
                for attr_name in ("character_name", "custom_client_name", "gw_client_name"):
                    value = str(getattr(tracked_account, attr_name, "") or "").strip()
                    if len(value) >= 2:
                        names.add(value)
        except Exception:
            pass

        return sorted(names, key=len, reverse=True)
    except Exception:
        return []


def redact_console_account_names(text_value: str) -> str:
    try:
        redacted = str(text_value)
        for account_name in get_account_names_for_console_redaction():
            try:
                pattern = re.compile(re.escape(account_name), re.IGNORECASE)
                redacted = pattern.sub("*****", redacted)
            except Exception:
                redacted = redacted.replace(account_name, "*****")
        return redacted
    except Exception:
        return str(text_value)


def get_console_text(redact_account_names: bool = False):
    text_value = "\n".join(str(line) for line in log_history)
    if redact_account_names:
        return redact_console_account_names(text_value)
    return text_value


def copy_text_to_clipboard(text: str) -> bool:
    try:
        root = tk.Tk()
        root.withdraw()
        root.clipboard_clear()
        root.clipboard_append(text)
        root.update()
        root.destroy()
        return True
    except Exception as e:
        log_history.append(f"Console - Clipboard copy failed: {str(e)}")
        return False


def save_console_to_file(redact_account_names: bool = False) -> str:
    log_path = os.path.join(current_directory, "Py4GW_Launcher_console.log")
    with open(log_path, "w", encoding="utf-8") as f:
        f.write(get_console_text(redact_account_names=redact_account_names))
    return log_path


def reset_launcher_layout():
    global launcher_left_panel_width, launcher_console_height, launcher_left_panel_ratio, launcher_console_height_ratio, launcher_config_tab

    try:
        launcher_left_panel_width = DEFAULT_ADVANCED_LEFT_PANEL_WIDTH
        launcher_console_height = DEFAULT_ADVANCED_CONSOLE_HEIGHT
        launcher_left_panel_ratio = DEFAULT_ADVANCED_LEFT_PANEL_RATIO
        launcher_console_height_ratio = DEFAULT_ADVANCED_CONSOLE_HEIGHT_RATIO
        launcher_config_tab = DEFAULT_ADVANCED_CONFIG_TAB

        write_existing_launcher_layout_value_if_changed(
            "advanced_left_panel_width",
            int(DEFAULT_ADVANCED_LEFT_PANEL_WIDTH),
        )
        write_existing_launcher_layout_value_if_changed(
            "advanced_console_height",
            int(DEFAULT_ADVANCED_CONSOLE_HEIGHT),
        )
        write_existing_launcher_layout_value_if_changed(
            "advanced_left_panel_ratio",
            f"{DEFAULT_ADVANCED_LEFT_PANEL_RATIO:.4f}",
        )
        write_existing_launcher_layout_value_if_changed(
            "advanced_console_height_ratio",
            f"{DEFAULT_ADVANCED_CONSOLE_HEIGHT_RATIO:.4f}",
        )
        write_existing_launcher_layout_value_if_changed(
            "advanced_config_tab",
            DEFAULT_ADVANCED_CONFIG_TAB,
        )

        log_history.append("Layout - Reset to launcher.py defaults. No files were deleted.")
    except Exception as e:
        log_history.append(f"Layout - Reset failed: {str(e)}")

def show_log_console():
    global pending_reset_layout_confirm, log_hide_clear_names

    ui_section_header("Console", f"{len(log_history)} lines")

    if themed_button("Copy Console##copy_console", "secondary"):
        text = get_console_text(redact_account_names=log_hide_clear_names)
        if copy_text_to_clipboard(text):
            if log_hide_clear_names:
                log_history.append(f"Console - Copied {len(log_history)} lines to clipboard with account names redacted.")
            else:
                log_history.append(f"Console - Copied {len(log_history)} lines to clipboard with clear account names.")

    imgui.same_line()
    if themed_button("Save Console Log##save_console", "secondary"):
        try:
            log_path = save_console_to_file(redact_account_names=log_hide_clear_names)
            if log_hide_clear_names:
                log_history.append(f"Console - Saved redacted log to: {log_path}")
            else:
                log_history.append(f"Console - Saved clear-name log to: {log_path}")
        except Exception as e:
            log_history.append(f"Console - Save failed: {str(e)}")

    imgui.same_line()
    if themed_button("Clear Console##clear_console", "secondary"):
        log_history.clear()
        log_history.append("Console cleared.")

    imgui.same_line()
    if themed_button("Reset Layout##reset_layout", "secondary"):
        pending_reset_layout_confirm = True
        log_history.append("Layout - Reset confirmation requested.")

    imgui.same_line()
    log_name_button_label = (
        "Log now Clear Name Hiding##toggle_log_name_hide"
        if log_hide_clear_names
        else "Log now Clear Name Visible##toggle_log_name_hide"
    )
    log_name_button_kind = "success" if log_hide_clear_names else "danger"
    if themed_button(log_name_button_label, log_name_button_kind):
        set_log_hide_clear_names(not log_hide_clear_names)

    if pending_reset_layout_confirm:
        imgui.spacing()
        imgui.separator()
        imgui.push_style_color(imgui.Col_.text, ui_color("warning"))
        imgui.text_wrapped("Really reset layout? The layout view will be reset to the default values from launcher.py. No files will be deleted.")
        imgui.pop_style_color()

        if themed_button("Yes, reset layout##confirm_reset_layout", "danger"):
            pending_reset_layout_confirm = False
            reset_launcher_layout()

        imgui.same_line()
        if themed_button("Cancel##cancel_reset_layout", "secondary"):
            pending_reset_layout_confirm = False
            log_history.append("Layout - Reset cancelled.")

    imgui.spacing()
    imgui.push_style_color(imgui.Col_.child_bg, ui_color("console_bg"))
    imgui.begin_child(
        str_id="ConsoleDockSpaceWindow",
        size=imgui.ImVec2(0, 0),
        child_flags=int(imgui.ChildFlags_.borders.value),
        window_flags=int(imgui.WindowFlags_.horizontal_scrollbar.value)
    )

    scroll_y = imgui.get_scroll_y()
    scroll_max_y = imgui.get_scroll_max_y()
    is_scrolled_to_bottom = (scroll_y >= scroll_max_y)

    for i in range(len(log_history)):
        display_line = log_history[i]
        if credentials_are_locked():
            display_line = redact_console_account_names(display_line)
        imgui.text(display_line)

    if is_scrolled_to_bottom:
        imgui.set_scroll_here_y(1.0)

    imgui.end_child()
    imgui.pop_style_color()


launch_gw = GWLauncher()


def is_pid_alive(pid) -> bool:
    try:
        if pid is None:
            return False
        if not psutil.pid_exists(pid):
            return False

        process = psutil.Process(pid)
        if not process.is_running():
            return False

        status = process.status()
        dead_statuses = [getattr(psutil, "STATUS_ZOMBIE", None), getattr(psutil, "STATUS_DEAD", None)]
        return status not in dead_statuses
    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
        return False
    except Exception:
        return False


MANAGED_CLIENTS_STATE_FILE = os.path.join(current_directory, "Py4GW_Launcher_managed_clients.json")
launcher_managed_clients = {}
guildwars_process_scan_cache = {
    "checked_at": 0.0,
    "processes": [],
}
guildwars_window_scan_cache = {
    "checked_at": 0.0,
    "windows": {},
}
guildwars_process_path_cache = {}
GUILDWARS_PROCESS_SCAN_REFRESH_SECONDS = 10.0
GUILDWARS_WINDOW_SCAN_REFRESH_SECONDS = 1.0
GUILDWARS_PROCESS_PATH_CACHE_SECONDS = 30.0
RUNNING_STATUS_CACHE_HIT_SAMPLE_RATE = 100


def ensure_launcher_account_uid(account):
    try:
        uid = str(getattr(account, "launcher_account_uid", "") or "").strip()
        if not uid:
            uid = secrets.token_hex(16)
            account.launcher_account_uid = uid
            try:
                team_manager.save_to_json(config_file)
            except Exception as e:
                log_history.append(f"Managed Clients - Failed to persist account id: {str(e)}")
        return uid
    except Exception:
        return str(id(account))


def load_launcher_managed_clients():
    try:
        if not os.path.exists(MANAGED_CLIENTS_STATE_FILE):
            return {}
        with open(MANAGED_CLIENTS_STATE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict):
            return {}
        cleaned = {}
        for key, entry in data.items():
            if not isinstance(entry, dict):
                continue
            try:
                pid = int(entry.get("pid", 0))
            except Exception:
                continue
            if pid <= 0:
                continue
            cleaned[str(key)] = {
                "pid": pid,
                "title": str(entry.get("title", "") or ""),
                "character_name": str(entry.get("character_name", "") or ""),
                "gw_path": str(entry.get("gw_path", "") or ""),
                "launched_at": float(entry.get("launched_at", 0.0) or 0.0),
            }
        return cleaned
    except Exception as e:
        log_history.append(f"Managed Clients - Load failed: {str(e)}")
        return {}


def save_launcher_managed_clients():
    try:
        with open(MANAGED_CLIENTS_STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(launcher_managed_clients, f, indent=2)
    except Exception as e:
        log_history.append(f"Managed Clients - Save failed: {str(e)}")


def register_launcher_managed_client(account, pid):
    try:
        uid = ensure_launcher_account_uid(account)
        launcher_managed_clients[uid] = {
            "pid": int(pid),
            "title": get_account_client_title(account),
            "character_name": str(getattr(account, "character_name", "") or ""),
            "gw_path": str(getattr(account, "gw_path", "") or ""),
            "launched_at": time.time(),
        }
        save_launcher_managed_clients()
    except Exception as e:
        log_history.append(f"Managed Clients - Register failed: {str(e)}")


def remove_launcher_managed_client(account=None, pid=None):
    changed = False
    try:
        if account is not None:
            uid = ensure_launcher_account_uid(account)
            if uid in launcher_managed_clients:
                del launcher_managed_clients[uid]
                changed = True
        if pid is not None:
            pid_int = int(pid)
            for key, entry in list(launcher_managed_clients.items()):
                if int(entry.get("pid", 0)) == pid_int:
                    del launcher_managed_clients[key]
                    changed = True
        if changed:
            save_launcher_managed_clients()
    except Exception:
        pass


def normalize_executable_path_for_compare(path):
    try:
        clean_path = str(path or "").strip().strip('"')
        if not clean_path:
            return ""
        if os.path.isdir(clean_path):
            clean_path = os.path.join(clean_path, "Gw.exe")
        return os.path.normcase(os.path.abspath(clean_path))
    except Exception:
        return os.path.normcase(str(path or "").strip().strip('"'))


def get_process_executable_path(process):
    try:
        exe_path = str(process.exe() or "").strip()
        if exe_path:
            return exe_path
    except Exception:
        pass

    try:
        cmdline = process.cmdline()
        if cmdline:
            first_arg = str(cmdline[0] or "").strip().strip('"')
            if first_arg:
                return first_arg
    except Exception:
        pass

    return ""


def get_process_executable_path_for_pid(pid, force=False):
    start_time = time.perf_counter() if perf_debug_enabled else 0.0
    try:
        pid = int(pid)
        now = time.time()
        if not force:
            cached = guildwars_process_path_cache.get(pid)
            if cached and (now - float(cached.get("checked_at", 0.0) or 0.0)) < GUILDWARS_PROCESS_PATH_CACHE_SECONDS:
                perf_debug_record_elapsed("process_path.cache_hit", start_time, f"PID={pid}")
                return str(cached.get("path", "") or "")

        path = normalize_executable_path_for_compare(get_process_executable_path(psutil.Process(pid)))
        guildwars_process_path_cache[pid] = {
            "checked_at": now,
            "path": path,
        }
        perf_debug_record_elapsed("process_path.read", start_time, f"PID={pid}")
        return path
    except Exception:
        perf_debug_record_elapsed("process_path.failed", start_time, f"PID={pid}")
        return ""


def get_visible_arena_net_windows(force=False):
    start_time = time.perf_counter() if perf_debug_enabled else 0.0
    now = time.time()
    try:
        if not force and (now - float(guildwars_window_scan_cache.get("checked_at", 0.0) or 0.0)) < GUILDWARS_WINDOW_SCAN_REFRESH_SECONDS:
            result = dict(guildwars_window_scan_cache.get("windows", {}) or {})
            perf_debug_record_elapsed("window_scan.cache_hit", start_time, f"{len(result)} pid(s)")
            return result
    except Exception:
        pass

    windows = {}

    def enum_windows_callback(hwnd, _):
        try:
            if not win32gui.IsWindowVisible(hwnd):
                return True
            class_name = win32gui.GetClassName(hwnd)
            if "ArenaNet" not in class_name:
                return True
            _, window_pid = win32process.GetWindowThreadProcessId(hwnd)
            pid = int(window_pid)
            title = win32gui.GetWindowText(hwnd).strip()
            entry = {
                "hwnd": hwnd,
                "title": title,
                "class_name": class_name,
            }
            windows.setdefault(pid, []).append(entry)
        except Exception:
            pass
        return True

    try:
        win32gui.EnumWindows(enum_windows_callback, None)
    except Exception as e:
        log_history.append(f"Guild Wars Window Scan - Failed: {str(e)}")

    guildwars_window_scan_cache["checked_at"] = now
    guildwars_window_scan_cache["windows"] = dict(windows)
    result = dict(windows)
    perf_debug_record_elapsed("window_scan.full", start_time, f"{len(result)} pid(s)")
    return result


def process_info_is_guildwars(process_info):
    try:
        name = str(process_info.get("name", "") or "").lower()
        exe_path = str(process_info.get("exe", "") or "")
        exe_name = os.path.basename(exe_path).lower()
        return name == "gw.exe" or exe_name == "gw.exe"
    except Exception:
        return False


def get_live_guildwars_processes(force=False):
    start_time = time.perf_counter() if perf_debug_enabled else 0.0
    now = time.time()
    try:
        if not force and (now - float(guildwars_process_scan_cache.get("checked_at", 0.0) or 0.0)) < GUILDWARS_PROCESS_SCAN_REFRESH_SECONDS:
            result = list(guildwars_process_scan_cache.get("processes", []) or [])
            perf_debug_record_elapsed("process_scan.cache_hit", start_time, f"{len(result)} gw.exe")
            return result
    except Exception:
        pass

    windows_by_pid = get_visible_arena_net_windows(force=force)
    processes = []
    scanned_count = 0
    try:
        for process in psutil.process_iter(["pid", "name", "status"]):
            scanned_count += 1
            try:
                pid = int(process.info.get("pid") or process.pid)
                status = process.info.get("status")
                if status in (getattr(psutil, "STATUS_ZOMBIE", None), getattr(psutil, "STATUS_DEAD", None)):
                    continue
                name = str(process.info.get("name", "") or "")
                if name.lower() != "gw.exe":
                    continue
                if not is_pid_alive(pid):
                    continue
                exe_path = get_process_executable_path_for_pid(pid)
                info = {
                    "pid": pid,
                    "name": name,
                    "exe": normalize_executable_path_for_compare(exe_path),
                }
                window_entries = list(windows_by_pid.get(pid, []) or [])
                if window_entries:
                    info["windows"] = window_entries
                    info["window_title"] = str(window_entries[0].get("title", "") or "")
                    info["window_hwnd"] = window_entries[0].get("hwnd")
                processes.append(info)
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
            except Exception:
                continue
    except Exception as e:
        log_history.append(f"Guild Wars Process Scan - Failed: {str(e)}")

    guildwars_process_scan_cache["checked_at"] = now
    guildwars_process_scan_cache["processes"] = list(processes)
    perf_debug_record_elapsed("process_scan.full", start_time, f"{len(processes)} gw.exe / {scanned_count} process(es)")
    return processes


def guildwars_process_matches_account(process_info, account):
    try:
        expected_path = normalize_executable_path_for_compare(str(getattr(account, "gw_path", "") or ""))
        process_path = normalize_executable_path_for_compare(str(process_info.get("exe", "") or ""))
        if expected_path and process_path and expected_path != process_path:
            return False
        return True
    except Exception:
        return False


def get_arena_net_window_info_for_pid(pid):
    try:
        pid = int(pid)
        windows_by_pid = get_visible_arena_net_windows()
        entries = list(windows_by_pid.get(pid, []) or [])
        if entries:
            return dict(entries[0])
    except Exception:
        pass

    hwnd = find_visible_gw_window_for_pid(pid)
    if not hwnd:
        return None
    try:
        return {
            "hwnd": hwnd,
            "title": win32gui.GetWindowText(hwnd).strip(),
            "class_name": win32gui.GetClassName(hwnd),
        }
    except Exception:
        return {
            "hwnd": hwnd,
            "title": "",
            "class_name": "",
        }


def find_external_guildwars_process_for_account(account):
    start_time = time.perf_counter() if perf_debug_enabled else 0.0
    target_title = get_account_client_title(account).strip()
    expected_path = normalize_executable_path_for_compare(str(getattr(account, "gw_path", "") or ""))
    candidates = []

    try:
        windows_by_pid = get_visible_arena_net_windows()
        for pid, windows in dict(windows_by_pid or {}).items():
            pid = int(pid)
            if not is_pid_alive(pid):
                continue
            for window_info in list(windows or []):
                title = str(window_info.get("title", "") or "").strip()
                if target_title and target_title != "Guild Wars" and title == target_title:
                    perf_debug_record_elapsed("external_attach.window_title", start_time, target_title)
                    return pid
                candidates.append((pid, title))

        if expected_path:
            path_candidates = []
            for pid, title in candidates:
                process_path = get_process_executable_path_for_pid(pid)
                if process_path and process_path == expected_path:
                    path_candidates.append((pid, title))

            if len(path_candidates) == 1:
                perf_debug_record_elapsed("external_attach.path_unique", start_time, expected_path)
                return int(path_candidates[0][0])

        perf_debug_record_elapsed("external_attach.not_found", start_time, target_title)
        return None
    except Exception:
        perf_debug_record_elapsed("external_attach.failed", start_time, target_title)
        return None


def find_visible_gw_window_for_pid(pid, expected_title=None):
    try:
        pid = int(pid)
    except Exception:
        return None

    found_hwnd = None

    def enum_windows_callback(hwnd, _):
        nonlocal found_hwnd
        if found_hwnd is not None:
            return False
        try:
            if not win32gui.IsWindowVisible(hwnd):
                return True
            _, window_pid = win32process.GetWindowThreadProcessId(hwnd)
            if int(window_pid) != pid:
                return True
            class_name = win32gui.GetClassName(hwnd)
            if "ArenaNet" not in class_name:
                return True
            found_hwnd = hwnd
            return False
        except Exception:
            pass
        return True

    try:
        win32gui.EnumWindows(enum_windows_callback, None)
    except Exception:
        return None

    return found_hwnd


def pid_matches_account_path(pid, account):
    try:
        expected_path = os.path.normcase(os.path.abspath(str(getattr(account, "gw_path", "") or "")))
        if not expected_path:
            return True
        process_path = os.path.normcase(os.path.abspath(psutil.Process(int(pid)).exe()))
        return process_path == expected_path
    except Exception:
        return True


def get_launcher_managed_pid_for_account(account):
    try:
        uid = ensure_launcher_account_uid(account)
        entry = launcher_managed_clients.get(uid)
        if not entry:
            return None
        return int(entry.get("pid", 0))
    except Exception:
        return None


def validate_launcher_managed_account_pid(account, pid):
    try:
        if not pid or not is_pid_alive(pid):
            remove_launcher_managed_client(account=account, pid=pid)
            return False, None

        if not pid_matches_account_path(pid, account):
            remove_launcher_managed_client(account=account, pid=pid)
            return False, None

        uid = ensure_launcher_account_uid(account)
        entry = launcher_managed_clients.get(uid)
        if isinstance(entry, dict):
            entry["pid"] = int(pid)
            entry["title"] = get_account_client_title(account)
            entry["character_name"] = str(getattr(account, "character_name", "") or "")
            entry["gw_path"] = str(getattr(account, "gw_path", "") or "")

        return True, int(pid)
    except Exception:
        return False, None


def close_launcher_managed_clients(team=None):
    def resolve_close_pid(account):
        managed_pid = get_launcher_managed_pid_for_account(account)
        if managed_pid:
            running, validated_pid = validate_launcher_managed_account_pid(account, managed_pid)
            if running and validated_pid:
                return int(validated_pid), "managed"

        running, detected_pid = find_gw_window_for_account(account)
        if running and detected_pid and is_pid_alive(detected_pid):
            return int(detected_pid), "detected"

        return None, ""

    def close_worker():
        try:
            if team is None:
                accounts = [account for current_team in team_manager.teams.values() for account in current_team.accounts]
                scope = "all teams"
            else:
                accounts = list(getattr(team, "accounts", []) or [])
                scope = f"team: {getattr(team, 'name', '')}"

            closed = 0
            skipped = 0
            seen_pids = set()
            close_targets = []

            for account in accounts:
                pid, pid_source = resolve_close_pid(account)
                if not pid:
                    skipped += 1
                    continue

                pid = int(pid)
                if pid in seen_pids:
                    skipped += 1
                    continue
                seen_pids.add(pid)

                hwnd = find_visible_gw_window_for_pid(pid)
                if hwnd is None:
                    invalidate_account_running_status(account)
                    skipped += 1
                    continue

                close_targets.append((account, pid, pid_source, hwnd))

            for account, pid, pid_source, hwnd in close_targets:
                try:
                    win32gui.PostMessage(hwnd, 0x0010, 0, 0)
                    closed += 1
                    log_history.append(
                        f"Close Clients - Sent close request to {getattr(account, 'character_name', '')} PID={pid} source={pid_source}."
                    )
                except Exception as e:
                    skipped += 1
                    log_history.append(f"Close Clients - Failed for {getattr(account, 'character_name', '')}: {str(e)}")

            for account, pid, _pid_source, _hwnd in close_targets:
                remove_launcher_managed_client(account=account, pid=pid)
                invalidate_account_running_status(account)

            try:
                closed_pids = {int(pid) for _account, pid, _pid_source, _hwnd in close_targets}
                launch_gw.active_pids = [
                    (tracked_account, tracked_pid)
                    for tracked_account, tracked_pid in list(launch_gw.active_pids)
                    if int(tracked_pid) not in closed_pids
                ]
            except Exception:
                pass

            save_launcher_managed_clients()
            log_history.append(f"Close Clients - Requested close for {closed} active team client(s) in {scope}. Skipped={skipped}.")
        except Exception as e:
            log_history.append(f"Close Clients - Failed: {str(e)}")

    threading.Thread(target=close_worker, daemon=True).start()


launcher_managed_clients = load_launcher_managed_clients()


def find_gw_window_for_account(account):
    try:
        for tracked_account, tracked_pid in list(launch_gw.active_pids):
            if tracked_account is account:
                if is_pid_alive(tracked_pid):
                    return True, tracked_pid
                try:
                    launch_gw.active_pids.remove((tracked_account, tracked_pid))
                except ValueError:
                    pass
    except Exception:
        pass

    managed_pid = get_launcher_managed_pid_for_account(account)
    if managed_pid:
        running, validated_pid = validate_launcher_managed_account_pid(account, managed_pid)
        if running:
            try:
                if not any(tracked_account is account and int(tracked_pid) == int(validated_pid) for tracked_account, tracked_pid in list(launch_gw.active_pids)):
                    launch_gw.active_pids.append((account, validated_pid))
            except Exception:
                pass
            return True, validated_pid

    target_title = get_account_client_title(account).strip()

    external_pid = find_external_guildwars_process_for_account(account)
    if external_pid:
        try:
            if not any(tracked_account is account and int(tracked_pid) == int(external_pid) for tracked_account, tracked_pid in list(launch_gw.active_pids)):
                launch_gw.active_pids.append((account, int(external_pid)))
            register_launcher_managed_client(account, int(external_pid))
        except Exception:
            pass
        return True, int(external_pid)

    if not target_title or target_title == "Guild Wars":
        return False, None

    found_pid = None

    def enum_windows_callback(hwnd, _):
        nonlocal found_pid
        if found_pid is not None:
            return False

        try:
            if not win32gui.IsWindowVisible(hwnd):
                return True

            title = win32gui.GetWindowText(hwnd).strip()
            if title != target_title:
                return True

            class_name = win32gui.GetClassName(hwnd)
            if "ArenaNet" not in class_name:
                return True

            _, window_pid = win32process.GetWindowThreadProcessId(hwnd)
            if is_pid_alive(window_pid):
                found_pid = window_pid
                return False
        except Exception:
            pass

        return True

    try:
        win32gui.EnumWindows(enum_windows_callback, None)
    except Exception:
        return False, None

    return found_pid is not None, found_pid

def get_account_running_status(account):
    start_time = time.perf_counter() if perf_debug_enabled else 0.0
    cache_key = id(account)
    now = time.time()
    cached = account_running_status_cache.get(cache_key)

    if cached and (now - cached.get("checked_at", 0.0)) < ACCOUNT_STATUS_REFRESH_SECONDS:
        if perf_debug_enabled:
            try:
                hit_count = int(cached.get("perf_cache_hits", 0)) + 1
                cached["perf_cache_hits"] = hit_count
                if hit_count == 1 or hit_count % RUNNING_STATUS_CACHE_HIT_SAMPLE_RATE == 0:
                    perf_debug_record_elapsed("running_status.cache_hit_sampled", start_time, get_account_display_name(account))
            except Exception:
                pass
        return cached.get("running", False), cached.get("pid")

    running, pid = perf_debug_call("find_gw_window_for_account", find_gw_window_for_account, account)
    account_running_status_cache[cache_key] = {
        "checked_at": now,
        "running": running,
        "pid": pid,
        "perf_cache_hits": 0,
    }
    perf_debug_record_elapsed("running_status.rescan", start_time, get_account_display_name(account))
    return running, pid


def set_account_dll_loaded_cache(account, pid, dll_kind, loaded, unknown=False, message=""):
    try:
        cache = account_py4gw_status_cache if str(dll_kind).lower() == "py4gw" else account_toolbox_status_cache
        cache[id(account)] = {
            "checked_at": time.time(),
            "pid": int(pid) if pid else None,
            "loaded": None if unknown else bool(loaded),
            "unknown": bool(unknown),
            "message": str(message or ""),
        }
    except Exception:
        pass


def invalidate_account_running_status(account=None):
    try:
        if account is None:
            account_running_status_cache.clear()
            account_toolbox_status_cache.clear()
            account_py4gw_status_cache.clear()
        else:
            account_running_status_cache.pop(id(account), None)
            account_toolbox_status_cache.pop(id(account), None)
            account_py4gw_status_cache.pop(id(account), None)
    except Exception:
        pass


def is_invalid_snapshot_handle(snapshot):
    try:
        value = int(snapshot)
    except Exception:
        try:
            value = int(snapshot.value)
        except Exception:
            return True
    return value == 0 or value == -1 or value == int(INVALID_HANDLE_VALUE)


def enumerate_loaded_modules_for_pid(pid):
    pid = int(pid)
    snapshot = kernel32.CreateToolhelp32Snapshot(TH32CS_SNAPMODULE | TH32CS_SNAPMODULE32, wintypes.DWORD(pid))
    if is_invalid_snapshot_handle(snapshot):
        raise ctypes.WinError()

    modules = []
    try:
        entry = MODULEENTRY32()
        entry.dwSize = ctypes.sizeof(MODULEENTRY32)
        if not kernel32.Module32FirstW(snapshot, ctypes.byref(entry)):
            raise ctypes.WinError()

        while True:
            modules.append({
                "name": str(entry.szModule or ""),
                "path": str(entry.szExePath or ""),
            })
            if not kernel32.Module32NextW(snapshot, ctypes.byref(entry)):
                break
    finally:
        try:
            if not is_invalid_snapshot_handle(snapshot):
                kernel32.CloseHandle(snapshot)
        except Exception:
            pass

    return modules


def check_module_loaded_for_pid(pid, module_path: str):
    start_time = time.perf_counter() if perf_debug_enabled else 0.0
    module_name = os.path.basename(str(module_path or "")) or "unknown"
    try:
        if not pid or not psutil.pid_exists(int(pid)):
            return False

        module_path = str(module_path or "").strip()
        module_name = os.path.basename(module_path).lower()
        module_abs = os.path.normcase(os.path.abspath(module_path)) if module_path else ""

        if not module_name:
            return False

        for module in perf_debug_call("dll_module_enumerate", enumerate_loaded_modules_for_pid, pid):
            loaded_path = str(module.get("path", "") or "")
            loaded_name = os.path.basename(str(module.get("name", "") or loaded_path)).lower()
            loaded_abs = os.path.normcase(os.path.abspath(loaded_path)) if loaded_path else ""

            if module_abs and loaded_abs == module_abs:
                return True
            if loaded_name == module_name:
                return True

        return False
    except Exception as e:
        try:
            winerror = int(getattr(e, "winerror", 0) or 0)
        except Exception:
            winerror = 0

        if winerror == 5:
            return None

        try:
            now = time.time()
            key = (int(pid) if pid else 0, module_name, str(type(e).__name__), str(winerror))
            last_logged = float(dll_status_error_log_cache.get(key, 0.0) or 0.0)
            if (now - last_logged) >= DLL_STATUS_ERROR_LOG_SECONDS:
                dll_status_error_log_cache[key] = now
                log_history.append(f"DLL Status - Module check failed for PID={pid}, DLL={module_name}: {str(e)}")
        except Exception:
            pass
        return None
    finally:
        perf_debug_record_elapsed("dll_module_check", start_time, f"PID={pid}, DLL={module_name}")


def check_py4gw_loaded_for_pid(pid) -> bool:
    return check_module_loaded_for_pid(pid, os.path.join(current_directory, py4gw_dll_name))


def check_gwtoolbox_loaded_for_pid(pid, account) -> bool:
    configured_path = str(getattr(account, "gwtoolbox_path", "") or "").strip()
    return check_module_loaded_for_pid(pid, configured_path)


def get_account_py4gw_loaded_status(account, running=None, pid=None):
    if running is None or pid is None:
        running, pid = get_account_running_status(account)

    if not running or not pid:
        return False

    cache_key = id(account)
    now = time.time()
    cached = account_py4gw_status_cache.get(cache_key)
    if (
        cached
        and cached.get("pid") == pid
        and (now - cached.get("checked_at", 0.0)) < PY4GW_STATUS_REFRESH_SECONDS
    ):
        return cached.get("loaded", False)

    loaded = check_py4gw_loaded_for_pid(pid)
    if loaded is None:
        if cached and cached.get("pid") == pid:
            return cached.get("loaded", None)
        set_account_dll_loaded_cache(account, pid, "Py4GW", False, unknown=True, message="Access denied while checking loaded modules")
        return None

    set_account_dll_loaded_cache(account, pid, "Py4GW", bool(loaded))
    return bool(loaded)


def get_account_toolbox_loaded_status(account, running=None, pid=None):
    if running is None or pid is None:
        running, pid = get_account_running_status(account)

    if not running or not pid:
        return False

    cache_key = id(account)
    now = time.time()
    cached = account_toolbox_status_cache.get(cache_key)
    if (
        cached
        and cached.get("pid") == pid
        and (now - cached.get("checked_at", 0.0)) < TOOLBOX_STATUS_REFRESH_SECONDS
    ):
        return cached.get("loaded", False)

    loaded = check_gwtoolbox_loaded_for_pid(pid, account)
    if loaded is None:
        if cached and cached.get("pid") == pid:
            return cached.get("loaded", None)
        set_account_dll_loaded_cache(account, pid, "GWToolbox", False, unknown=True, message="Access denied while checking loaded modules")
        return None

    set_account_dll_loaded_cache(account, pid, "GWToolbox", bool(loaded))
    return bool(loaded)


def render_status_badge(label: str, kind: str, id_suffix: str = ""):
    kind = str(kind or "secondary").lower()

    if kind in ("success", "selected", "active", "active_monitor"):
        badge_color = ui_color("success")
    elif kind in ("warning", "outdated"):
        badge_color = ui_color("warning")
    elif kind in ("danger", "delete", "destructive"):
        badge_color = ui_color("danger")
    else:
        badge_color = (0.540, 0.600, 0.680, 1.00)

    badge_bg = (0.0, 0.0, 0.0, 0.0)
    badge_bg_hovered = (0.0, 0.0, 0.0, 0.0)
    badge_bg_active = (0.0, 0.0, 0.0, 0.0)

    pushed_colors = 0
    pushed_vars = 0
    try:
        pushed_colors += _push_style_color_safe("button", badge_bg)
        pushed_colors += _push_style_color_safe("button_hovered", badge_bg_hovered)
        pushed_colors += _push_style_color_safe("button_active", badge_bg_active)
        pushed_colors += _push_style_color_safe("text", badge_color)
        pushed_colors += _push_style_color_safe("border", badge_color)

        pushed_vars += _push_style_var_safe("frame_rounding", 3.0)
        pushed_vars += _push_style_var_safe("frame_border_size", 1.0)
        pushed_vars += _push_style_var_safe("frame_padding", imgui.ImVec2(4.0, 1.0))
        pushed_vars += _push_style_var_safe("item_spacing", imgui.ImVec2(4.0, 4.0))

        badge_width = max(30.0, 14.0 + (len(str(label or "")) * 8.0))
        try:
            imgui.button(f"{label}##status_badge_{id_suffix}", imgui.ImVec2(badge_width, 19.0))
        except TypeError:
            imgui.button(f"{label}##status_badge_{id_suffix}")
    finally:
        if pushed_vars:
            try:
                imgui.pop_style_var(pushed_vars)
            except Exception:
                pass
        if pushed_colors:
            try:
                imgui.pop_style_color(pushed_colors)
            except Exception:
                pass



GW_HUFFMAN_TABLE1 = [(2684354560, 2), (1610612736, 6), (1073741824, 10), (536870912, 18), (301989888, 25), (201326592, 31), (117440512, 41), (50331648, 57), (23068672, 70), (15728640, 77), (12582912, 83), (11534336, 87), (10485760, 95), (0, 255)]
GW_HUFFMAN_TABLE2 = [8, 9, 10, 0, 7, 11, 12, 6, 41, 42, 224, 4, 5, 32, 40, 43, 44, 64, 74, 3, 13, 37, 38, 39, 72, 73, 36, 71, 75, 76, 105, 106, 35, 70, 96, 99, 103, 104, 136, 137, 160, 232, 1, 2, 45, 67, 68, 69, 101, 102, 128, 135, 138, 168, 169, 192, 201, 233, 14, 77, 100, 107, 108, 132, 133, 139, 164, 165, 170, 200, 229, 131, 134, 166, 167, 199, 202, 231, 34, 46, 140, 196, 228, 230, 78, 109, 198, 236, 15, 16, 17, 141, 171, 172, 204, 234, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 33, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 65, 66, 79, 80, 81, 82, 83, 84, 85, 86, 87, 88, 89, 90, 91, 92, 93, 94, 95, 97, 98, 110, 111, 112, 113, 114, 115, 116, 117, 118, 119, 120, 121, 122, 123, 124, 125, 126, 127, 129, 130, 142, 143, 144, 145, 146, 147, 148, 149, 150, 151, 152, 153, 154, 155, 156, 157, 158, 159, 161, 162, 163, 173, 174, 175, 176, 177, 178, 179, 180, 181, 182, 183, 184, 185, 186, 187, 188, 189, 190, 191, 193, 194, 195, 197, 203, 205, 206, 207, 208, 209, 210, 211, 212, 213, 214, 215, 216, 217, 218, 219, 220, 221, 222, 223, 225, 226, 227, 235, 237, 238, 239, 240, 241, 242, 243, 244, 245, 246, 247, 248, 249, 250, 251, 252, 253, 254, 255]
GW_HUFFMAN_TABLE3 = [0, 1, 2, 3, 4, 5, 6, 7, 8, 10, 12, 14, 16, 20, 24, 28, 32, 40, 48, 56, 64, 80, 96, 112, 128, 160, 192, 224, 255, 0, 0, 0]
GW_HUFFMAN_EXTRA_BITS_LENGTH = [0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 2, 2, 2, 2, 3, 3, 3, 3, 4, 4, 4, 4, 5, 5, 5, 5, 0]
GW_HUFFMAN_EXTRA_BITS_DISTANCE = [0, 0, 0, 0, 1, 1, 2, 2, 3, 3, 4, 4, 5, 5, 6, 6, 7, 7, 8, 8, 9, 9, 10, 10, 11, 11, 12, 12, 13, 13, 14, 14]
GW_HUFFMAN_BACKTRACK_TABLE = [0, 1, 2, 3, 4, 6, 8, 12, 16, 24, 32, 48, 64, 96, 128, 192, 256, 384, 512, 768, 1024, 1536, 2048, 3072, 4096, 6144, 8192, 12288, 16384, 24576, 256, 770, 1284, 1798, 2568, 3596, 5136, 7192, 10272, 14384, 20544, 28768, 41088, 57536, 255, 0]


class GWBitStream:
    def __init__(self, data):
        self.data = bytes(data or b"")
        if len(self.data) < 8:
            raise ValueError("Input length must be at least 8")
        self.buf1 = int.from_bytes(self.data[0:4], "little")
        self.buf2 = int.from_bytes(self.data[4:8], "little")
        self.idx = 8
        self.avail = 32

    def peek(self, count):
        count = int(count)
        if count <= 0:
            return 0
        if count > 32:
            raise ValueError("Count must be less than or equal to 32")
        return (self.buf1 >> (32 - count)) & 0xFFFFFFFF

    def read(self, count):
        result = self.peek(count)
        self.consume(count)
        return result

    def consume(self, count):
        count = int(count)
        if count <= 0:
            return
        self.buf1 = ((self.buf2 >> (32 - count)) | ((self.buf1 << count) & 0xFFFFFFFF)) & 0xFFFFFFFF
        if self.avail < count:
            if self.idx >= len(self.data):
                self.avail = 0
                self.buf2 = 0
            else:
                block = self.data[self.idx:self.idx + 4]
                if len(block) < 4:
                    block = block + b"\x00" * (4 - len(block))
                self.buf2 = int.from_bytes(block, "little")
                self.idx += 4
                new_avail = self.avail + 32 - count
                self.buf1 = (self.buf1 + (self.buf2 >> new_avail)) & 0xFFFFFFFF
                self.buf2 = (self.buf2 << (count - self.avail)) & 0xFFFFFFFF
                self.avail = new_avail
        else:
            self.avail -= count
            self.buf2 = (self.buf2 << count) & 0xFFFFFFFF


class GWHuffmanTable:
    def __init__(self, nodes, large_symbol_count):
        self.nodes = list(nodes)
        self.large_symbol_translation = [(0, 0, 0) for _ in range(24)]
        self.large_symbol_values = []

    def get_next_code(self, stream):
        bits = stream.peek(8)
        enc_len, enc_val = self.nodes[bits]
        if enc_len == 0xFFFFFFFF:
            buf1 = stream.peek(32)
            selected = None
            for item in self.large_symbol_translation:
                if item[0] <= buf1:
                    selected = item
                    break
            if selected is None:
                raise RuntimeError("Failed to get next Huffman code")
            first_encoding, last_index, enc_length = selected
            enc_len = int(enc_length)
            group_index = (buf1 - first_encoding) >> (32 - enc_length)
            large_enc_index = last_index - int(group_index)
            if large_enc_index < 0 or large_enc_index >= len(self.large_symbol_values):
                raise RuntimeError("Failed to get next Huffman code")
            enc_val = self.large_symbol_values[large_enc_index]
        stream.consume(int(enc_len))
        return int(enc_val)

    @staticmethod
    def build(stream):
        symbol_follow_table_root = [0xFFFFFFFF for _ in range(32)]
        symbol_count = int(stream.read(16))
        symbol_follow_table = [0 for _ in range(symbol_count)]
        total_symbol_count = 0
        symbol_idx = symbol_count - 1
        while symbol_idx != -1:
            buf1 = stream.peek(32)
            idx = 0
            while idx < len(GW_HUFFMAN_TABLE1):
                if GW_HUFFMAN_TABLE1[idx][0] <= buf1:
                    break
                idx += 1
            if idx == len(GW_HUFFMAN_TABLE1):
                raise RuntimeError("Failed to build Huffman table")
            bit_count = idx + 3
            offset = int((buf1 - GW_HUFFMAN_TABLE1[idx][0]) >> (32 - bit_count))
            stream.consume(bit_count)
            temp = GW_HUFFMAN_TABLE2[GW_HUFFMAN_TABLE1[idx][1] - offset]
            number_of_symbol = temp >> 5
            symbol_len = temp & 0x1F
            if symbol_len != 0 or symbol_count < 2:
                number_of_symbol += 1
                total_symbol_count += int(number_of_symbol)
                for _i in range(int(number_of_symbol)):
                    symbol_follow_table[symbol_idx] = int(symbol_follow_table_root[symbol_len])
                    symbol_follow_table_root[symbol_len] = int(symbol_idx)
                    symbol_idx -= 1
            else:
                symbol_idx -= int(number_of_symbol + 1)

        if total_symbol_count == 0:
            symbol_follow_table[symbol_count - 1] = int(symbol_follow_table_root[0])
            symbol_follow_table_root[0] = int(symbol_count - 1)
            total_symbol_count = 1

        next_bits_encoding = 1
        symbol_in_huffman_table = 0
        nodes = [(0, 0) for _ in range(256)]

        for enc_len in range(1, 9):
            current_symbol = symbol_follow_table_root[enc_len]
            while current_symbol != 0xFFFFFFFF:
                if current_symbol >= symbol_count:
                    raise RuntimeError("Failed to build Huffman table")
                if next_bits_encoding >= (1 << enc_len):
                    raise RuntimeError("Failed to build Huffman table")
                first_symbol = next_bits_encoding << (8 - enc_len)
                iter_count = 1 << (8 - enc_len)
                for idx in range(first_symbol, first_symbol + iter_count):
                    nodes[idx] = (int(enc_len), int(current_symbol))
                current_symbol = symbol_follow_table[int(current_symbol)]
                symbol_in_huffman_table += 1
                next_bits_encoding -= 1
            next_bits_encoding = (next_bits_encoding << 1) + 1

        large_symbol_count = total_symbol_count - symbol_in_huffman_table
        huffman = GWHuffmanTable(nodes, large_symbol_count)
        if symbol_in_huffman_table == total_symbol_count:
            return huffman

        for enc_len in range(9, 32):
            current_symbol = symbol_follow_table_root[enc_len]
            while current_symbol != 0xFFFFFFFF:
                if current_symbol >= symbol_count:
                    raise RuntimeError("Failed to build Huffman table")
                if next_bits_encoding >= (1 << enc_len):
                    raise RuntimeError("Failed to build Huffman table")
                partial_encoding = next_bits_encoding >> (enc_len - 8)
                huffman.nodes[partial_encoding] = (0xFFFFFFFF, 0)
                huffman.large_symbol_values.append(int(current_symbol))
                current_symbol = symbol_follow_table[int(current_symbol)]
                next_bits_encoding -= 1
            first_encoding = ((next_bits_encoding + 1) << (32 - enc_len)) & 0xFFFFFFFF
            last_index = len(huffman.large_symbol_values) - 1
            huffman.large_symbol_translation[enc_len - 9] = (first_encoding, last_index, enc_len)
            next_bits_encoding = (next_bits_encoding << 1) + 1

        return huffman


def gw_u32(value):
    return int(value) & 0xFFFFFFFF


def read_exact_socket(sock, size):
    chunks = []
    remaining = int(size)
    while remaining > 0:
        chunk = sock.recv(remaining)
        if not chunk:
            raise RuntimeError("Socket closed while receiving data")
        chunks.append(chunk)
        remaining -= len(chunk)
    return b"".join(chunks)


def connect_guildwars_file_server():
    last_error = None
    for server_index in range(1, 13):
        host = f"file{server_index}.arenanetworks.com"
        sock = None
        try:
            sock = socket.create_connection((host, 6112), timeout=5.0)
            sock.settimeout(5.0)
            sock.sendall(struct.pack("<BIHHIII", 1, 0, 0xF1, 0x10, 1, 0, 0))
            manifest_bytes = read_exact_socket(sock, 32)
            manifest = struct.unpack("<hhiiiiiii", manifest_bytes)
            return sock, {
                "host": host,
                "manifest": manifest[3],
                "backup_exe": manifest[4],
                "latest_exe": manifest[8],
            }
        except Exception as e:
            last_error = e
            try:
                if sock:
                    sock.close()
            except Exception:
                pass
    raise RuntimeError(f"Failed to connect to ArenaNet file servers: {last_error}")


def get_latest_guildwars_exe_version():
    sock = None
    try:
        sock, manifest = connect_guildwars_file_server()
        return int(manifest.get("latest_exe", 0) or 0)
    finally:
        try:
            if sock:
                sock.close()
        except Exception:
            pass


def pe_read_sections(data):
    if len(data) < 0x40 or data[:2] != b"MZ":
        raise RuntimeError("Invalid PE file")
    pe_offset = struct.unpack_from("<I", data, 0x3C)[0]
    if data[pe_offset:pe_offset + 4] != b"PE\x00\x00":
        raise RuntimeError("Invalid PE signature")
    section_count = struct.unpack_from("<H", data, pe_offset + 6)[0]
    optional_header_size = struct.unpack_from("<H", data, pe_offset + 20)[0]
    section_offset = pe_offset + 24 + optional_header_size
    sections = []
    for index in range(section_count):
        offset = section_offset + index * 40
        name = data[offset:offset + 8].split(b"\x00", 1)[0].decode("ascii", errors="ignore")
        virtual_size, virtual_address, raw_size, raw_pointer = struct.unpack_from("<IIII", data, offset + 8)
        sections.append({
            "name": name,
            "virtual_size": int(virtual_size),
            "virtual_address": int(virtual_address),
            "raw_size": int(raw_size),
            "raw_pointer": int(raw_pointer),
        })
    return sections


def pe_rva_to_offset(sections, rva):
    rva = int(rva)
    for section in sections:
        start = int(section.get("virtual_address", 0))
        size = max(int(section.get("virtual_size", 0)), int(section.get("raw_size", 0)))
        end = start + size
        if start <= rva < end:
            return int(section.get("raw_pointer", 0)) + (rva - start)
    raise RuntimeError("Could not map RVA to file offset")


def find_pattern_with_wildcards(buffer, pattern):
    length = len(pattern)
    fixed_runs = []
    run_start = None
    run_bytes = []
    for index, value in enumerate(pattern):
        if value is None:
            if run_start is not None and run_bytes:
                fixed_runs.append((run_start, bytes(run_bytes)))
            run_start = None
            run_bytes = []
            continue
        if run_start is None:
            run_start = index
            run_bytes = []
        run_bytes.append(int(value))
    if run_start is not None and run_bytes:
        fixed_runs.append((run_start, bytes(run_bytes)))

    if fixed_runs:
        anchor_start, anchor = max(fixed_runs, key=lambda item: len(item[1]))
        search_from = 0
        while True:
            anchor_offset = buffer.find(anchor, search_from)
            if anchor_offset < 0:
                break
            candidate = anchor_offset - anchor_start
            if candidate >= 0 and candidate + length <= len(buffer):
                matched = True
                for index, value in enumerate(pattern):
                    if value is not None and buffer[candidate + index] != value:
                        matched = False
                        break
                if matched:
                    return candidate
            search_from = anchor_offset + 1

    for offset in range(0, len(buffer) - length + 1):
        matched = True
        for index, value in enumerate(pattern):
            if value is not None and buffer[offset + index] != value:
                matched = False
                break
        if matched:
            return offset
    raise RuntimeError("Pattern not found")


def find_pattern_with_wildcards_in_file_range(data, pattern, start, end):
    length = len(pattern)
    fixed_runs = []
    run_start = None
    run_bytes = []
    for index, value in enumerate(pattern):
        if value is None:
            if run_start is not None and run_bytes:
                fixed_runs.append((run_start, bytes(run_bytes)))
            run_start = None
            run_bytes = []
            continue
        if run_start is None:
            run_start = index
            run_bytes = []
        run_bytes.append(int(value))
    if run_start is not None and run_bytes:
        fixed_runs.append((run_start, bytes(run_bytes)))

    if not fixed_runs:
        relative = find_pattern_with_wildcards(data[start:end], pattern)
        return int(start) + int(relative)

    anchor_start, anchor = max(fixed_runs, key=lambda item: len(item[1]))
    search_from = int(start)
    search_end = max(int(start), int(end) - len(anchor) + 1)
    while search_from < search_end:
        anchor_offset = data.find(anchor, search_from, int(end))
        if anchor_offset < 0:
            break
        candidate = anchor_offset - anchor_start
        if candidate >= start and candidate + length <= end:
            matched = True
            for index, value in enumerate(pattern):
                if value is not None and data[candidate + index] != value:
                    matched = False
                    break
            if matched:
                return candidate - int(start)
        search_from = anchor_offset + 1

    raise RuntimeError("Pattern not found")


def follow_pe_call(data, sections, call_rva):
    file_offset = pe_rva_to_offset(sections, call_rva)
    op = data[file_offset]
    if op not in (0xE8, 0xE9):
        raise RuntimeError("Unsupported call opcode")
    rel = struct.unpack_from("<i", data, file_offset + 1)[0]
    return int(call_rva) + rel + 5


def read_pe_u32(data, sections, rva):
    file_offset = pe_rva_to_offset(sections, rva)
    return struct.unpack_from("<I", data, file_offset)[0]


def get_guildwars_exe_version_id(executable_path):
    start_time = time.perf_counter() if perf_debug_enabled else 0.0
    try:
        with open(executable_path, "rb") as file:
            with mmap.mmap(file.fileno(), 0, access=mmap.ACCESS_READ) as data:
                sections = pe_read_sections(data)
                text_section = None
                for section in sections:
                    if section.get("name") == ".text":
                        text_section = section
                        break
                if not text_section:
                    raise RuntimeError("PE .text section not found")

                raw_start = int(text_section.get("raw_pointer", 0))
                raw_size = int(text_section.get("raw_size", 0))
                raw_end = raw_start + raw_size
                text_rva = int(text_section.get("virtual_address", 0))

                try:
                    file_id_pattern = [0x55, 0x8B, 0xEC, 0x83, 0xEC, None, 0xE8, None, None, None, None, 0x83, 0x3D, None, None, None, None, 0x00]
                    pattern_offset = find_pattern_with_wildcards_in_file_range(data, file_id_pattern, raw_start, raw_end)
                    function_rva = text_rva + pattern_offset
                    for scan_offset in range(0, 0x80):
                        rva = function_rva + scan_offset
                        file_offset = pe_rva_to_offset(sections, rva)
                        if data[file_offset] != 0xE8:
                            continue
                        target_rva = rva + struct.unpack_from("<i", data, file_offset + 1)[0] + 5
                        target_offset = pe_rva_to_offset(sections, target_rva)
                        if data[target_offset] == 0xB8 and data[target_offset + 5] == 0xC3:
                            return int(read_pe_u32(data, sections, target_rva + 1))
                except Exception:
                    pass

                legacy_pattern = bytes([0x8B, 0xC8, 0x33, 0xDB, 0x39, 0x8D, 0xC0, 0xFD, 0xFF, 0xFF, 0x0F, 0x95, 0xC3])
                legacy_offset = data.find(legacy_pattern, raw_start, raw_end)
                if legacy_offset < 0:
                    raise RuntimeError("Guild Wars executable version pattern not found")
                legacy_offset -= raw_start
                legacy_rva = text_rva + legacy_offset
                function_rva = follow_pe_call(data, sections, legacy_rva - 5)
                return int(read_pe_u32(data, sections, function_rva + 1))
    except Exception as e:
        raise RuntimeError(f"Failed to read Gw.exe version: {str(e)}")
    finally:
        perf_debug_record_elapsed("gw_exe_version_read", start_time, os.path.basename(str(executable_path or "")))


def download_compressed_guildwars_exe(file_id, progress_callback=None):
    sock = None
    try:
        sock, manifest = connect_guildwars_file_server()
        sock.sendall(struct.pack("<HHii", 0x3F2, 0xC, int(file_id), 0))
        metadata = struct.unpack("<HH", read_exact_socket(sock, 4))
        if metadata[0] == 0x4F2:
            raise RuntimeError("ArenaNet file server could not find the requested executable")
        if metadata[0] != 0x5F2:
            raise RuntimeError(f"Unexpected file metadata response: 0x{metadata[0]:X}")
        file_response = struct.unpack("<iiii", read_exact_socket(sock, 16))
        response_file_id, size_decompressed, size_compressed, crc = file_response
        if int(response_file_id) != int(file_id):
            log_history.append(f"GW.exe Update - ArenaNet file server returned executable id {response_file_id} for requested id {file_id}. Continuing with final version verification.")

        result = bytearray()
        chunk_size = 0
        while len(result) < int(size_compressed):
            if chunk_size > 0:
                sock.sendall(struct.pack("<HHI", 0x7F3, 0x8, int(chunk_size)))
            header = struct.unpack("<HH", read_exact_socket(sock, 4))
            if header[0] not in (0x6F2, 0x6F3):
                raise RuntimeError(f"Unexpected download chunk header: 0x{header[0]:X}")
            chunk_size = int(header[1]) - 4
            if chunk_size <= 0:
                raise RuntimeError("Invalid download chunk size")
            chunk = read_exact_socket(sock, chunk_size)
            result.extend(chunk)
            if progress_callback:
                progress_callback("download", min(1.0, len(result) / max(1, int(size_compressed))))

        return bytes(result), int(size_decompressed), int(size_compressed), int(crc)
    finally:
        try:
            if sock:
                sock.close()
        except Exception:
            pass


def decompress_guildwars_exe(compressed_data, expected_final_size, progress_callback=None):
    stream = GWBitStream(compressed_data)
    stream.consume(4)
    first4_bits = int(stream.read(4))
    output = bytearray()
    expected_final_size = int(expected_final_size)

    while len(output) < expected_final_size:
        if progress_callback:
            progress_callback("unpack", min(1.0, len(output) / max(1, expected_final_size)))
        lit_huffman = GWHuffmanTable.build(stream)
        dist_huffman = GWHuffmanTable.build(stream)
        block_size = (int(stream.read(4)) + 1) * 4096
        for _i in range(block_size):
            if len(output) == expected_final_size:
                break
            code = int(lit_huffman.get_next_code(stream))
            if code < 0x100:
                output.append(code & 0xFF)
            else:
                blen = GW_HUFFMAN_EXTRA_BITS_LENGTH[code - 256]
                code_value = GW_HUFFMAN_TABLE3[code - 256]
                if blen > 0:
                    code_value |= int(stream.read(int(blen)))
                backtrack_count = first4_bits + int(code_value) + 1
                dist_code = int(dist_huffman.get_next_code(stream))
                dist_blen = GW_HUFFMAN_EXTRA_BITS_DISTANCE[dist_code]
                backtrack = GW_HUFFMAN_BACKTRACK_TABLE[dist_code]
                if dist_blen > 0:
                    backtrack |= int(stream.read(int(dist_blen)))
                if backtrack >= len(output):
                    raise RuntimeError("Failed to decompress executable")
                src = len(output) - (int(backtrack) + 1)
                for j in range(src, src + int(backtrack_count)):
                    output.append(output[j])
                    if len(output) == expected_final_size:
                        break

    if progress_callback:
        progress_callback("unpack", 1.0)
    return bytes(output)


def get_gw_exe_cache_dir():
    cache_dir = os.path.join(current_directory, "GuildWarsCache")
    os.makedirs(cache_dir, exist_ok=True)
    return cache_dir


def get_cached_gw_exe_path(version):
    return os.path.join(get_gw_exe_cache_dir(), f"Gw.{int(version)}.exe")


def get_file_sha256(path):
    start_time = time.perf_counter() if perf_debug_enabled else 0.0
    try:
        h = hashlib.sha256()
        with open(path, "rb") as file:
            while True:
                chunk = file.read(1024 * 1024)
                if not chunk:
                    break
                h.update(chunk)
        return h.hexdigest()
    finally:
        perf_debug_record_elapsed("sha256_file", start_time, os.path.basename(str(path or "")))


def get_cached_gw_exe_sha_key(version):
    return f"gw_exe_sha256_{int(version)}"


def get_cached_gw_exe_sha_signature_key(version):
    return f"gw_exe_sha256_signature_{int(version)}"


def read_cached_gw_exe_sha(version):
    return str(ini_handler.read_key(LAYOUT_CONFIG_SECTION, get_cached_gw_exe_sha_key(version), "") or "").strip().lower()


def read_cached_gw_exe_sha_signature(version):
    return str(ini_handler.read_key(LAYOUT_CONFIG_SECTION, get_cached_gw_exe_sha_signature_key(version), "") or "").strip()


def write_cached_gw_exe_sha(version, sha256_value):
    write_launcher_layout_value_if_changed(get_cached_gw_exe_sha_key(version), str(sha256_value or "").strip().lower())


def write_cached_gw_exe_sha_signature(version, signature):
    write_launcher_layout_value_if_changed(get_cached_gw_exe_sha_signature_key(version), str(signature or "").strip())


def verify_cached_gw_exe_file(version, path=None, force_full=False):
    start_time = time.perf_counter() if perf_debug_enabled else 0.0
    version = int(version)
    cache_path = path or get_cached_gw_exe_path(version)
    if not os.path.exists(cache_path):
        raise RuntimeError(f"Cached Gw.exe version not found: {version}")

    signature = get_gw_exe_file_signature(cache_path)
    stored_sha = read_cached_gw_exe_sha(version)
    stored_signature = read_cached_gw_exe_sha_signature(version)

    if stored_sha and stored_signature and stored_signature == signature and not force_full:
        perf_debug_record_elapsed("cached_exe_verify.fast_signature", start_time, str(version))
        return stored_sha

    parsed_version = get_guildwars_exe_version_id(cache_path)
    if int(parsed_version) != version:
        raise RuntimeError(f"Cached Gw.exe version mismatch: {parsed_version} != {version}")
    current_sha = get_file_sha256(cache_path)
    if stored_sha and stored_sha != current_sha:
        raise RuntimeError(f"Cached Gw.exe SHA256 mismatch for version {version}")
    write_cached_gw_exe_sha(version, current_sha)
    write_cached_gw_exe_sha_signature(version, signature)
    perf_debug_record_elapsed("cached_exe_verify.full", start_time, str(version))
    return current_sha


def set_gw_exe_cache_verify_result(version, state, message="", sha256_value=""):
    global gw_exe_cache_verify_results
    with gw_exe_update_lock:
        gw_exe_cache_verify_results[int(version)] = {
            "state": str(state or "unknown"),
            "message": str(message or ""),
            "sha256": str(sha256_value or ""),
            "checked_at": time.time(),
        }


def get_gw_exe_cache_verify_result(version):
    with gw_exe_update_lock:
        return dict(gw_exe_cache_verify_results.get(int(version), {}))


def get_gw_exe_cache_version_state_label(version):
    result = get_gw_exe_cache_verify_result(version)
    state = str(result.get("state", "unchecked"))
    if state == "ok":
        return f"{int(version)} - OK"
    if state == "corrupt":
        return f"{int(version)} - CORRUPT"
    if state == "checking":
        return f"{int(version)} - CHECKING"
    return f"{int(version)} - UNCHECKED"


def verify_cached_gw_exe_versions_worker():
    versions = get_cached_gw_exe_versions()
    if not versions:
        log_history.append("GW.exe Cache Verify - No cached versions found.")
        return
    for version in versions:
        try:
            set_gw_exe_cache_verify_result(version, "checking", "Checking cached Gw.exe version...")
            sha256_value = verify_cached_gw_exe_file(version, force_full=True)
            set_gw_exe_cache_verify_result(version, "ok", f"Version {version} OK", sha256_value)
            time.sleep(0.03)
        except Exception as e:
            set_gw_exe_cache_verify_result(version, "corrupt", str(e), "")
            log_history.append(f"GW.exe Cache Verify - Version {version} corrupt: {str(e)}")
    log_history.append(f"GW.exe Cache Verify - Finished checking {len(versions)} cached version(s).")


def start_verify_cached_gw_exe_versions():
    global gw_exe_cache_verify_thread
    try:
        if gw_exe_cache_verify_thread and gw_exe_cache_verify_thread.is_alive():
            log_history.append("GW.exe Cache Verify - Verification is already running.")
            return
    except Exception:
        pass
    gw_exe_cache_verify_thread = threading.Thread(target=verify_cached_gw_exe_versions_worker, daemon=True)
    gw_exe_cache_verify_thread.start()


def redownload_latest_gw_exe_cache_worker():
    global gw_exe_cache_redownload_latest_status
    try:
        def progress_callback(stage, value):
            global gw_exe_cache_redownload_latest_status
            label = "Downloading latest Gw.exe to local cache..." if str(stage) == "download" else "Unpacking latest Gw.exe to local cache..."
            gw_exe_cache_redownload_latest_status = f"{label} {int(float(value) * 100)}%"

        gw_exe_cache_redownload_latest_status = "Redownloading latest Gw.exe cache..."
        cache_path, latest_version = fetch_latest_guildwars_exe(progress_callback, force=True)
        sha256_value = verify_cached_gw_exe_file(latest_version, cache_path, force_full=True)
        set_gw_exe_cache_verify_result(latest_version, "ok", f"Latest version {latest_version} redownloaded and verified", sha256_value)
        gw_exe_cache_redownload_latest_status = f"Latest cache redownloaded and verified. Version {latest_version}"
        log_history.append(f"GW.exe Cache - Redownloaded latest cache version {latest_version}: {cache_path}")
    except Exception as e:
        gw_exe_cache_redownload_latest_status = f"Redownload latest cache failed: {str(e)}"
        log_history.append(f"GW.exe Cache - Redownload latest failed: {str(e)}")


def start_redownload_latest_gw_exe_cache():
    global gw_exe_update_thread
    try:
        if gw_exe_update_thread and gw_exe_update_thread.is_alive():
            log_history.append("GW.exe Cache - Another update/install is already running.")
            return
    except Exception:
        pass
    gw_exe_update_thread = threading.Thread(target=redownload_latest_gw_exe_cache_worker, daemon=True)
    gw_exe_update_thread.start()


def get_cached_gw_exe_versions():
    versions = []
    try:
        cache_dir = get_gw_exe_cache_dir()
        for entry in os.listdir(cache_dir):
            match = re.fullmatch(r"Gw\.(\d+)\.exe", str(entry or ""))
            if not match:
                continue
            path = os.path.join(cache_dir, entry)
            if os.path.isfile(path):
                versions.append(int(match.group(1)))
    except Exception:
        pass
    return sorted(set(versions), reverse=True)


def ensure_selected_cached_gw_exe_version():
    global gw_exe_cached_version_selected
    versions = get_cached_gw_exe_versions()
    if not versions:
        gw_exe_cached_version_selected = 0
        return 0, []
    if gw_exe_cached_version_selected not in versions:
        gw_exe_cached_version_selected = versions[0]
        write_launcher_layout_value_if_changed("gw_exe_cached_version_selected", str(gw_exe_cached_version_selected))
    return gw_exe_cached_version_selected, versions


def cache_existing_guildwars_executable(path, version=None):
    path = normalize_gw_exe_path(path)
    if not os.path.exists(path):
        raise RuntimeError("Gw.exe not found")
    current_version = int(version if version is not None else get_guildwars_exe_version_id(path))
    cache_path = get_cached_gw_exe_path(current_version)
    if os.path.exists(cache_path):
        try:
            verify_cached_gw_exe_file(current_version, cache_path)
            return cache_path, current_version
        except Exception as e:
            log_history.append(f"GW.exe Cache - Existing cached version {current_version} failed validation and will be replaced: {str(e)}")
            try:
                os.remove(cache_path)
            except Exception:
                pass
    temp_path = os.path.join(get_gw_exe_cache_dir(), f"Gw.{current_version}.cache_tmp")
    shutil.copy2(path, temp_path)
    parsed_version = get_guildwars_exe_version_id(temp_path)
    if parsed_version != current_version:
        try:
            os.remove(temp_path)
        except Exception:
            pass
        raise RuntimeError(f"Cached original Gw.exe version mismatch: {parsed_version} != {current_version}")
    os.replace(temp_path, cache_path)
    write_cached_gw_exe_sha(current_version, get_file_sha256(cache_path))
    write_cached_gw_exe_sha_signature(current_version, get_gw_exe_file_signature(cache_path))
    log_history.append(f"GW.exe Cache - Stored local version {current_version}: {cache_path}")
    return cache_path, current_version


def fetch_latest_guildwars_exe(progress_callback=None, force=False):
    latest_version = get_latest_guildwars_exe_version()
    if latest_version <= 0:
        raise RuntimeError("Latest Guild Wars executable version is invalid")
    cache_path = os.path.join(get_gw_exe_cache_dir(), f"Gw.{latest_version}.exe")
    if os.path.exists(cache_path) and not force:
        try:
            verify_cached_gw_exe_file(latest_version, cache_path)
            return cache_path, latest_version
        except Exception as e:
            set_gw_exe_cache_verify_result(latest_version, "corrupt", str(e), "")
            log_history.append(f"GW.exe Cache - Existing downloaded version {latest_version} failed validation and will be replaced: {str(e)}")
            try:
                os.remove(cache_path)
            except Exception:
                pass
    elif os.path.exists(cache_path) and force:
        try:
            os.remove(cache_path)
        except Exception:
            pass
    compressed_data, expected_size, _compressed_size, _crc = download_compressed_guildwars_exe(latest_version, progress_callback)
    executable_data = decompress_guildwars_exe(compressed_data, expected_size, progress_callback)
    temp_path = os.path.join(get_gw_exe_cache_dir(), f"Gw.{latest_version}.download")
    Path(temp_path).write_bytes(executable_data)
    parsed_version = get_guildwars_exe_version_id(temp_path)
    if parsed_version != latest_version:
        try:
            os.remove(temp_path)
        except Exception:
            pass
        raise RuntimeError(f"Downloaded Gw.exe version mismatch: {parsed_version} != {latest_version}")
    os.replace(temp_path, cache_path)
    sha256_value = get_file_sha256(cache_path)
    write_cached_gw_exe_sha(latest_version, sha256_value)
    write_cached_gw_exe_sha_signature(latest_version, get_gw_exe_file_signature(cache_path))
    set_gw_exe_cache_verify_result(latest_version, "ok", f"Version {latest_version} OK", sha256_value)
    return cache_path, latest_version


def normalize_gw_exe_path(path):
    clean_path = str(path or "").strip().strip('"')
    if not clean_path:
        return ""
    if os.path.isdir(clean_path):
        clean_path = os.path.join(clean_path, "Gw.exe")
    return os.path.abspath(clean_path)


def get_all_configured_gw_exe_paths():
    paths = []
    try:
        for team in list(team_manager.teams.values()):
            for account in list(getattr(team, "accounts", []) or []):
                path = normalize_gw_exe_path(getattr(account, "gw_path", ""))
                if path and path not in paths:
                    paths.append(path)
    except Exception:
        pass
    return paths


def get_gw_exe_file_signature(path):
    try:
        stat_value = os.stat(path)
        mtime_ns = getattr(stat_value, "st_mtime_ns", int(float(stat_value.st_mtime) * 1000000000))
        return f"{int(stat_value.st_size)}|{int(mtime_ns)}"
    except Exception:
        return ""


def get_gw_exe_cache_key(path):
    clean_path = normalize_gw_exe_path(path).lower()
    digest = hashlib.sha256(clean_path.encode("utf-8", errors="ignore")).hexdigest()[:24]
    return f"gw_exe_version_cache_{digest}"


def read_cached_gw_exe_version(path):
    signature = get_gw_exe_file_signature(path)
    if not signature:
        return None
    value = ini_handler.read_key(LAYOUT_CONFIG_SECTION, get_gw_exe_cache_key(path), "")
    parts = str(value or "").split("|")
    if len(parts) != 3:
        return None
    if f"{parts[0]}|{parts[1]}" != signature:
        return None
    try:
        return int(parts[2])
    except Exception:
        return None


def write_cached_gw_exe_version(path, version):
    signature = get_gw_exe_file_signature(path)
    if not signature:
        return
    write_launcher_layout_value_if_changed(get_gw_exe_cache_key(path), f"{signature}|{int(version)}")


def get_known_or_read_gw_exe_version(path):
    cached = read_cached_gw_exe_version(path)
    if cached is not None:
        return int(cached)

    try:
        status = get_gw_exe_update_status(path)
        current_version = status.get("current_version", None)
        if current_version is not None:
            return int(current_version)
    except Exception:
        pass

    return int(get_guildwars_exe_version_id(path))


def apply_gw_exe_version_status(path, current, latest, prefix=""):
    if int(current) == int(latest):
        set_gw_exe_update_status(path, "current", f"{prefix}Gw.exe is up to date. Version {current}", current, latest)
    else:
        set_gw_exe_update_status(path, "outdated", f"{prefix}Gw.exe update available. Current {current}, latest {latest}", current, latest)


def set_gw_exe_update_status(path, state, message="", current_version=None, latest_version=None, progress=None):
    global gw_exe_update_status_by_path
    path = normalize_gw_exe_path(path)
    with gw_exe_update_lock:
        current = dict(gw_exe_update_status_by_path.get(path, {}))
        current["state"] = str(state or "unknown")
        current["message"] = str(message or "")
        if current_version is not None:
            current["current_version"] = current_version
        if latest_version is not None:
            current["latest_version"] = latest_version
        if progress is not None:
            current["progress"] = float(progress)
        current["checked_at"] = time.time()
        gw_exe_update_status_by_path[path] = current


def get_gw_exe_update_status(path):
    path = normalize_gw_exe_path(path)
    with gw_exe_update_lock:
        return dict(gw_exe_update_status_by_path.get(path, {"state": "pending", "message": "Pending check"}))


def get_running_guildwars_exe_paths(force=False):
    start_time = time.perf_counter() if perf_debug_enabled else 0.0
    paths = set()
    try:
        windows_by_pid = get_visible_arena_net_windows(force=force)
        for pid in dict(windows_by_pid or {}).keys():
            try:
                exe_path = normalize_gw_exe_path(get_process_executable_path_for_pid(int(pid), force=False))
                if exe_path and os.path.basename(exe_path).lower() == "gw.exe":
                    paths.add(os.path.normcase(os.path.abspath(exe_path)))
            except Exception:
                continue
    except Exception:
        pass
    perf_debug_record_elapsed("running_paths.window_only", start_time, f"{len(paths)} path(s)")
    return paths


def is_gw_exe_path_running(path, force=False):
    clean_path = normalize_gw_exe_path(path)
    if not clean_path:
        return False
    try:
        return os.path.normcase(os.path.abspath(clean_path)) in get_running_guildwars_exe_paths(force=force)
    except Exception:
        return False


def any_guildwars_clients_running():
    try:
        return len(get_running_guildwars_exe_paths(force=True)) > 0
    except Exception:
        try:
            for team in list(team_manager.teams.values()):
                for account in list(getattr(team, "accounts", []) or []):
                    running, _pid = get_account_running_status(account)
                    if running:
                        return True
        except Exception:
            pass
    return False


def gw_exe_status_check_worker(paths, use_cache=True, stagger_delay=0.75):
    global gw_exe_update_latest_version_id
    scanned_count = 0
    try:
        for path in list(paths or []):
            set_gw_exe_update_status(path, "checking", "Checking ArenaNet latest version...")
        latest = get_latest_guildwars_exe_version()
        gw_exe_update_latest_version_id = latest
        for path in list(paths or []):
            if not os.path.exists(path):
                set_gw_exe_update_status(path, "error", "Gw.exe not found", latest_version=latest)
                continue

            cached = read_cached_gw_exe_version(path) if use_cache else None
            if cached is not None:
                apply_gw_exe_version_status(path, cached, latest, "Cached: ")
                continue

            try:
                set_gw_exe_update_status(path, "checking", "Reading local Gw.exe version...")
                current = get_guildwars_exe_version_id(path)
                write_cached_gw_exe_version(path, current)
                apply_gw_exe_version_status(path, current, latest)
                scanned_count += 1
                time.sleep(0.03)
                if stagger_delay and scanned_count > 0:
                    time.sleep(float(stagger_delay))
            except Exception as e:
                set_gw_exe_update_status(path, "error", str(e), latest_version=latest)
        problem_count = 0
        try:
            for path in list(paths or []):
                state = str(get_gw_exe_update_status(path).get("state", "") or "")
                if state in ("outdated", "error"):
                    problem_count += 1
        except Exception:
            pass
        if not use_cache or problem_count > 0:
            log_history.append(f"GW.exe Update - Version check finished. Cached check: {bool(use_cache)}. Problems: {problem_count}.")
    except Exception as e:
        for path in list(paths or []):
            set_gw_exe_update_status(path, "error", f"Update check failed: {str(e)}")
        log_history.append(f"GW.exe Update - Version check failed: {str(e)}")


def start_gw_exe_update_status_check(force=False):
    global gw_exe_update_check_thread, gw_exe_update_last_auto_check, gw_exe_update_locked_delay_last_log
    if not gw_exe_update_enabled:
        return
    if credentials_are_locked():
        now = time.time()
        if force or not gw_exe_update_locked_delay_last_log or (now - gw_exe_update_locked_delay_last_log) >= 60:
            gw_exe_update_locked_delay_last_log = now
            log_history.append("GW.exe Update - Version check delayed until credentials are unlocked.")
        return
    paths = get_all_configured_gw_exe_paths()
    if not paths:
        return
    now = time.time()
    if not force and gw_exe_update_last_auto_check and (now - gw_exe_update_last_auto_check) < 600:
        return
    try:
        if gw_exe_update_check_thread and gw_exe_update_check_thread.is_alive():
            return
    except Exception:
        pass
    gw_exe_update_last_auto_check = now
    use_cache = not bool(force)
    stagger_delay = 0.75 if use_cache else 0.25
    gw_exe_update_check_thread = threading.Thread(target=gw_exe_status_check_worker, args=(paths, use_cache, stagger_delay), daemon=True)
    gw_exe_update_check_thread.start()


def replace_guildwars_executable_from_cache(path, cache_path, latest_version):
    path = normalize_gw_exe_path(path)
    if not os.path.exists(path):
        set_gw_exe_update_status(path, "error", "Gw.exe not found", progress=0.0)
        return False
    set_gw_exe_update_status(path, "updating", "Saving current Gw.exe version to local cache...", latest_version=latest_version, progress=1.0)
    old_version = get_known_or_read_gw_exe_version(path)
    cache_existing_guildwars_executable(path, old_version)
    set_gw_exe_update_status(path, "updating", "Replacing Gw.exe from local cache...", latest_version=latest_version, progress=1.0)
    shutil.copy2(cache_path, path)
    current = int(latest_version)
    write_cached_gw_exe_version(path, current)
    set_gw_exe_update_status(path, "current", f"Gw.exe updated successfully from local cache. Version {current}", current, latest_version, 1.0)
    log_history.append(f"GW.exe Update - Updated {path} from local cache. Previous version {old_version} was stored centrally.")
    return True


def get_gw_exe_update_all_targets():
    targets = []
    try:
        for path in get_all_configured_gw_exe_paths():
            status = get_gw_exe_update_status(path)
            state = str(status.get("state", "pending"))
            message = str(status.get("message", ""))
            current_version = status.get("current_version", None)
            latest_version = status.get("latest_version", None)
            is_failed_update = state == "error" and message.startswith("Update failed") and current_version is not None and latest_version is not None and current_version != latest_version
            if state == "outdated" or is_failed_update:
                targets.append(path)
    except Exception:
        pass
    return targets


def gw_exe_update_worker(path):
    try:
        path = normalize_gw_exe_path(path)
        set_gw_exe_update_status(path, "updating", "Preparing update...", progress=0.0)
        if is_gw_exe_path_running(path, force=True):
            set_gw_exe_update_status(path, "outdated", "Update blocked. Close Guild Wars Client first.", progress=0.0)
            return

        def progress_callback(stage, value):
            label = "Downloading Gw.exe to local cache..." if str(stage) == "download" else "Unpacking Gw.exe to local cache..."
            set_gw_exe_update_status(path, "updating", f"{label} {int(float(value) * 100)}%", progress=float(value))

        cache_path, latest_version = fetch_latest_guildwars_exe(progress_callback)
        set_gw_exe_update_status(path, "updating", f"Using local cache: {cache_path}", latest_version=latest_version, progress=1.0)
        replace_guildwars_executable_from_cache(path, cache_path, latest_version)
    except Exception as e:
        set_gw_exe_update_status(path, "error", f"Update failed: {str(e)}")
        log_history.append(f"GW.exe Update - Failed for {path}: {str(e)}")


def gw_exe_update_all_worker(paths):
    paths = [normalize_gw_exe_path(path) for path in list(paths or []) if normalize_gw_exe_path(path)]
    try:
        if not paths:
            log_history.append("GW.exe Update All - No outdated Gw.exe paths selected.")
            return

        running_paths = get_running_guildwars_exe_paths(force=True)
        update_paths = []
        for path in paths:
            path_key = os.path.normcase(os.path.abspath(normalize_gw_exe_path(path)))
            if path_key in running_paths:
                set_gw_exe_update_status(path, "outdated", "Update skipped. Close Guild Wars Client first.", progress=0.0)
            else:
                update_paths.append(path)

        if not update_paths:
            log_history.append("GW.exe Update All - All selected Gw.exe files are currently running. Close the shown Guild Wars Client(s) first.")
            return

        for path in update_paths:
            set_gw_exe_update_status(path, "updating", "Preparing Update All...", progress=0.0)

        def progress_callback(stage, value):
            label = "Downloading Gw.exe once to local cache..." if str(stage) == "download" else "Unpacking Gw.exe once to local cache..."
            for path in update_paths:
                set_gw_exe_update_status(path, "updating", f"{label} {int(float(value) * 100)}%", progress=float(value))

        cache_path, latest_version = fetch_latest_guildwars_exe(progress_callback)
        log_history.append(f"GW.exe Update All - Using local cached Gw.exe: {cache_path}")

        success_count = 0
        for index, path in enumerate(update_paths, start=1):
            try:
                set_gw_exe_update_status(path, "updating", f"Updating {index}/{len(update_paths)} from local cache...", latest_version=latest_version, progress=1.0)
                if replace_guildwars_executable_from_cache(path, cache_path, latest_version):
                    success_count += 1
            except Exception as e:
                set_gw_exe_update_status(path, "error", f"Update failed: {str(e)}")
                log_history.append(f"GW.exe Update All - Failed for {path}: {str(e)}")
        log_history.append(f"GW.exe Update All - Finished. Updated {success_count}/{len(update_paths)} eligible Gw.exe files. Skipped {len(paths) - len(update_paths)} running file(s).")
    except Exception as e:
        for path in paths:
            set_gw_exe_update_status(path, "error", f"Update failed: {str(e)}")
        log_history.append(f"GW.exe Update All - Failed: {str(e)}")


def start_gw_exe_update(path):
    global gw_exe_update_thread
    try:
        if gw_exe_update_thread and gw_exe_update_thread.is_alive():
            log_history.append("GW.exe Update - Another update is already running.")
            return
    except Exception:
        pass
    gw_exe_update_thread = threading.Thread(target=gw_exe_update_worker, args=(normalize_gw_exe_path(path),), daemon=True)
    gw_exe_update_thread.start()


def start_gw_exe_update_all(paths=None):
    global gw_exe_update_thread
    try:
        if gw_exe_update_thread and gw_exe_update_thread.is_alive():
            log_history.append("GW.exe Update All - Another update is already running.")
            return
    except Exception:
        pass
    selected_paths = list(paths or get_gw_exe_update_all_targets())
    gw_exe_update_thread = threading.Thread(target=gw_exe_update_all_worker, args=(selected_paths,), daemon=True)
    gw_exe_update_thread.start()



def install_cached_gw_exe_version_worker(version, paths):
    version = int(version)
    paths = [normalize_gw_exe_path(path) for path in list(paths or []) if normalize_gw_exe_path(path)]
    try:
        if not paths:
            log_history.append("GW.exe Cache Install - No configured Gw.exe paths found.")
            return

        running_paths = get_running_guildwars_exe_paths(force=True)
        install_paths = []
        for path in paths:
            path_key = os.path.normcase(os.path.abspath(normalize_gw_exe_path(path)))
            if path_key in running_paths:
                set_gw_exe_update_status(path, "error", "Install cached version skipped. Close Guild Wars Client first.")
            else:
                install_paths.append(path)

        if not install_paths:
            log_history.append("GW.exe Cache Install - All selected Gw.exe files are currently running. Close the shown Guild Wars Client(s) first.")
            return

        cache_path = get_cached_gw_exe_path(version)
        sha256_value = verify_cached_gw_exe_file(version, cache_path)
        set_gw_exe_cache_verify_result(version, "ok", f"Version {version} OK", sha256_value)
        try:
            latest_version = int(gw_exe_update_latest_version_id or get_latest_guildwars_exe_version())
        except Exception:
            latest_version = version

        success_count = 0
        for index, path in enumerate(install_paths, start=1):
            try:
                set_gw_exe_update_status(path, "updating", f"Installing cached version {version} {index}/{len(install_paths)}...", latest_version=latest_version, progress=1.0)
                if not os.path.exists(path):
                    set_gw_exe_update_status(path, "error", "Gw.exe not found")
                    continue
                old_version = get_known_or_read_gw_exe_version(path)
                cache_existing_guildwars_executable(path, old_version)
                shutil.copy2(cache_path, path)
                current = int(version)
                write_cached_gw_exe_version(path, current)
                if current == latest_version:
                    set_gw_exe_update_status(path, "current", f"Cached version installed. Version {current}", current, latest_version, 1.0)
                else:
                    set_gw_exe_update_status(path, "outdated", f"Cached version installed. Current {current}, latest {latest_version}", current, latest_version, 1.0)
                success_count += 1
            except Exception as e:
                set_gw_exe_update_status(path, "error", f"Install cached version failed: {str(e)}")
                log_history.append(f"GW.exe Cache Install - Failed for {path}: {str(e)}")
        log_history.append(f"GW.exe Cache Install - Installed version {version} on {success_count}/{len(install_paths)} eligible Gw.exe files. Skipped {len(paths) - len(install_paths)} running file(s).")
    except Exception as e:
        for path in paths:
            set_gw_exe_update_status(path, "error", f"Install cached version failed: {str(e)}")
        log_history.append(f"GW.exe Cache Install - Failed: {str(e)}")


def start_install_cached_gw_exe_version(version, paths=None):
    global gw_exe_update_thread
    try:
        if gw_exe_update_thread and gw_exe_update_thread.is_alive():
            log_history.append("GW.exe Cache Install - Another update/install is already running.")
            return
    except Exception:
        pass
    selected_paths = list(paths or get_all_configured_gw_exe_paths())
    gw_exe_update_thread = threading.Thread(target=install_cached_gw_exe_version_worker, args=(int(version), selected_paths), daemon=True)
    gw_exe_update_thread.start()


def render_gw_exe_cached_versions_panel(paths):
    global gw_exe_cached_version_selected, gw_exe_cached_install_target_index
    global gw_exe_install_cached_confirm_version, gw_exe_install_cached_confirm_requested_at, gw_exe_install_cached_confirm_paths
    global gw_exe_cache_redownload_latest_confirm_requested_at

    selected_version, versions = ensure_selected_cached_gw_exe_version()
    ui_section_header("Cached Gw.exe Versions", "local version store")
    ui_text_muted(f"Cache folder: {get_gw_exe_cache_dir()}")

    if themed_button("Verify Cached Versions##gw_exe_verify_cached_versions", "secondary", imgui.ImVec2(158, 0)):
        start_verify_cached_gw_exe_versions()

    imgui.same_line()
    if themed_button("Redownload Latest Cache##gw_exe_redownload_latest_cache", "danger", imgui.ImVec2(184, 0)):
        gw_exe_cache_redownload_latest_confirm_requested_at = time.time()

    if gw_exe_cache_redownload_latest_confirm_requested_at:
        render_colored_text("This will redownload the latest Gw.exe into the local cache and replace the cached latest file.", "warning")
        if themed_button("Cancel##gw_exe_redownload_latest_cancel", "secondary", imgui.ImVec2(72, 0)):
            gw_exe_cache_redownload_latest_confirm_requested_at = 0.0
        imgui.same_line()
        if themed_button("Confirm Redownload Latest##gw_exe_redownload_latest_confirm", "danger", imgui.ImVec2(206, 0)):
            if time.time() - float(gw_exe_cache_redownload_latest_confirm_requested_at or 0.0) >= 0.35:
                gw_exe_cache_redownload_latest_confirm_requested_at = 0.0
                start_redownload_latest_gw_exe_cache()

    if gw_exe_cache_redownload_latest_status:
        ui_text_muted(gw_exe_cache_redownload_latest_status)

    if not versions:
        ui_text_muted("No cached Gw.exe versions yet. Updating once will store the downloaded version and the replaced old version here.")
        return

    labels = [get_gw_exe_cache_version_state_label(version) for version in versions]
    selected_index = versions.index(selected_version) if selected_version in versions else 0
    imgui.set_next_item_width(190)
    changed_version, selected_index = imgui.combo("##gw_exe_cached_version_select", selected_index, labels)
    if changed_version and 0 <= selected_index < len(versions):
        gw_exe_cached_version_selected = versions[selected_index]
        write_launcher_layout_value_if_changed("gw_exe_cached_version_selected", str(gw_exe_cached_version_selected))
        gw_exe_install_cached_confirm_version = 0
        gw_exe_install_cached_confirm_requested_at = 0.0
        gw_exe_install_cached_confirm_paths = []

    selected_result = get_gw_exe_cache_verify_result(gw_exe_cached_version_selected)
    selected_state = str(selected_result.get("state", "unchecked"))
    selected_message = str(selected_result.get("message", ""))
    if selected_state == "ok":
        render_colored_text(f"Selected cached version {gw_exe_cached_version_selected}: OK", "success")
    elif selected_state == "corrupt":
        render_colored_text(f"Selected cached version {gw_exe_cached_version_selected}: CORRUPT", "danger")
        ui_text_muted(selected_message or "Local cached file is corrupt and cannot be restored automatically unless it is the latest version and can be redownloaded.")
    elif selected_state == "checking":
        ui_text_muted(f"Selected cached version {gw_exe_cached_version_selected}: checking...")
    else:
        ui_text_muted(f"Selected cached version {gw_exe_cached_version_selected}: unchecked")

    target_options = ["All"] + [normalize_gw_exe_path(path) for path in list(paths or [])]
    if gw_exe_cached_install_target_index >= len(target_options):
        gw_exe_cached_install_target_index = 0
    imgui.same_line()
    imgui.set_next_item_width(260)
    changed_target, gw_exe_cached_install_target_index = imgui.combo("##gw_exe_cached_install_target", gw_exe_cached_install_target_index, target_options)
    if changed_target:
        write_launcher_layout_value_if_changed("gw_exe_cached_install_target_index", str(gw_exe_cached_install_target_index))
        gw_exe_install_cached_confirm_version = 0
        gw_exe_install_cached_confirm_requested_at = 0.0
        gw_exe_install_cached_confirm_paths = []

    selected_paths = list(paths or []) if gw_exe_cached_install_target_index == 0 else [target_options[gw_exe_cached_install_target_index]]
    button_label = f"Install Version All##gw_exe_install_cached_all_{gw_exe_cached_version_selected}" if gw_exe_cached_install_target_index == 0 else f"Install Version Target##gw_exe_install_cached_target_{gw_exe_cached_version_selected}"
    imgui.same_line()
    if selected_state == "corrupt":
        ui_text_muted("Install blocked for corrupt cached file.")
    elif themed_button(button_label, "danger", imgui.ImVec2(156, 0)):
        gw_exe_install_cached_confirm_version = int(gw_exe_cached_version_selected)
        gw_exe_install_cached_confirm_requested_at = time.time()
        gw_exe_install_cached_confirm_paths = list(selected_paths)

    if gw_exe_install_cached_confirm_version:
        target_text = "all configured Guild Wars folders" if len(gw_exe_install_cached_confirm_paths) != 1 else gw_exe_install_cached_confirm_paths[0]
        render_colored_text(f"Install cached Gw.exe version {gw_exe_install_cached_confirm_version} to {target_text}?", "warning")
        ui_text_muted("Close the affected Guild Wars Client first. Inactive clients can still be updated.")
        if themed_button("Cancel##gw_exe_install_cached_cancel", "secondary", imgui.ImVec2(72, 0)):
            gw_exe_install_cached_confirm_version = 0
            gw_exe_install_cached_confirm_requested_at = 0.0
            gw_exe_install_cached_confirm_paths = []
        imgui.same_line()
        if themed_button(f"Confirm Install Version {gw_exe_install_cached_confirm_version}##gw_exe_install_cached_confirm", "danger", imgui.ImVec2(210, 0)):
            if time.time() - float(gw_exe_install_cached_confirm_requested_at or 0.0) >= 0.35:
                version_to_install = int(gw_exe_install_cached_confirm_version)
                paths_to_install = list(gw_exe_install_cached_confirm_paths or selected_paths)
                gw_exe_install_cached_confirm_version = 0
                gw_exe_install_cached_confirm_requested_at = 0.0
                gw_exe_install_cached_confirm_paths = []
                start_install_cached_gw_exe_version(version_to_install, paths_to_install)


def redownload_guildwars_client_worker(destination_folder, run_image):
    global gw_exe_redownload_status, gw_exe_redownload_folder
    try:
        destination_folder = os.path.abspath(str(destination_folder or "").strip().strip('"'))
        if not destination_folder:
            gw_exe_redownload_status = "Destination folder is empty."
            return
        os.makedirs(destination_folder, exist_ok=True)
        target_exe = os.path.join(destination_folder, "Gw.exe")
        if is_gw_exe_path_running(target_exe, force=True):
            gw_exe_redownload_status = "Blocked. Close Guild Wars Client first."
            return

        def progress_callback(stage, value):
            global gw_exe_redownload_status
            label = "Downloading latest Gw.exe to local cache..." if str(stage) == "download" else "Unpacking latest Gw.exe to local cache..."
            gw_exe_redownload_status = f"{label} {int(float(value) * 100)}%"

        gw_exe_redownload_status = "Fetching latest Gw.exe..."
        cache_path, latest_version = fetch_latest_guildwars_exe(progress_callback)
        verify_cached_gw_exe_file(latest_version, cache_path)

        if os.path.exists(target_exe):
            gw_exe_redownload_status = "Saving existing Gw.exe version to local cache..."
            cache_existing_guildwars_executable(target_exe)

        shutil.copy2(cache_path, target_exe)
        current = get_guildwars_exe_version_id(target_exe)
        if current != latest_version:
            raise RuntimeError(f"Installed Gw.exe version mismatch: {current} != {latest_version}")

        write_cached_gw_exe_version(target_exe, current)
        gw_exe_redownload_folder = destination_folder
        write_launcher_layout_value_if_changed("gw_exe_redownload_folder", gw_exe_redownload_folder)
        gw_exe_redownload_status = f"Latest Gw.exe installed. Version {current}"

        if run_image:
            gw_exe_redownload_status = f"Starting Gw.exe -image for full client redownload. Version {current}"
            subprocess.Popen([target_exe, "-image"], cwd=destination_folder)
        log_history.append(f"GW.exe Client Redownload - Installed latest Gw.exe to {target_exe}. Run image: {bool(run_image)}")
    except Exception as e:
        gw_exe_redownload_status = f"Client redownload failed: {str(e)}"
        log_history.append(f"GW.exe Client Redownload - Failed: {str(e)}")


def start_redownload_guildwars_client(destination_folder, run_image):
    global gw_exe_update_thread
    try:
        if gw_exe_update_thread and gw_exe_update_thread.is_alive():
            log_history.append("GW.exe Client Redownload - Another update/install is already running.")
            return
    except Exception:
        pass
    gw_exe_update_thread = threading.Thread(target=redownload_guildwars_client_worker, args=(destination_folder, bool(run_image)), daemon=True)
    gw_exe_update_thread.start()


def render_gw_exe_redownload_panel():
    global gw_exe_redownload_folder, gw_exe_redownload_run_image, gw_exe_redownload_confirm_requested_at

    ui_section_header("Client Redownload", "fresh Gw.exe and optional -image")
    ui_text_muted("Downloads the latest Gw.exe into the local cache, copies it to the selected folder, and can start Gw.exe -image to redownload the client data.")

    input_width = ui_responsive_input_width(max_width=460.0, min_width=180.0, reserve_width=190.0)
    imgui.set_next_item_width(input_width)
    changed_folder, gw_exe_redownload_folder = imgui.input_text("##gw_exe_redownload_folder", gw_exe_redownload_folder, 512)
    if changed_folder:
        write_launcher_layout_value_if_changed("gw_exe_redownload_folder", gw_exe_redownload_folder)

    imgui.same_line()
    if themed_button("Browse##gw_exe_redownload_browse", "secondary", imgui.ImVec2(76, 0)):
        selected_folder = filedialog.askdirectory()
        if selected_folder:
            gw_exe_redownload_folder = selected_folder
            write_launcher_layout_value_if_changed("gw_exe_redownload_folder", gw_exe_redownload_folder)

    changed_image, gw_exe_redownload_run_image = imgui.checkbox("Run Gw.exe -image after install##gw_exe_redownload_run_image", bool(gw_exe_redownload_run_image))
    if changed_image:
        write_launcher_layout_value_if_changed("gw_exe_redownload_run_image", "true" if gw_exe_redownload_run_image else "false")

    if themed_button("Redownload Client##gw_exe_redownload_client", "danger", imgui.ImVec2(138, 0)):
        gw_exe_redownload_confirm_requested_at = time.time()

    if gw_exe_redownload_confirm_requested_at:
        render_colored_text("This will copy the latest Gw.exe into the selected folder. Existing Gw.exe is stored centrally first.", "warning")
        if gw_exe_redownload_run_image:
            ui_text_muted("After that, Gw.exe -image will be started. This can download the full client data and may take a long time.")
        if themed_button("Cancel##gw_exe_redownload_cancel", "secondary", imgui.ImVec2(72, 0)):
            gw_exe_redownload_confirm_requested_at = 0.0
        imgui.same_line()
        if themed_button("Confirm Redownload##gw_exe_redownload_confirm", "danger", imgui.ImVec2(156, 0)):
            if time.time() - float(gw_exe_redownload_confirm_requested_at or 0.0) >= 0.35:
                gw_exe_redownload_confirm_requested_at = 0.0
                start_redownload_guildwars_client(gw_exe_redownload_folder, gw_exe_redownload_run_image)

    if gw_exe_redownload_status:
        ui_text_muted(gw_exe_redownload_status)


def render_colored_text(text_value, color_name):
    imgui.push_style_color(imgui.Col_.text, ui_color(color_name))
    imgui.text(str(text_value))
    imgui.pop_style_color()


def render_gw_exe_update_panel():
    global gw_exe_update_confirm_path, gw_exe_update_confirm_requested_at

    if credentials_are_locked():
        return

    paths = get_all_configured_gw_exe_paths()
    if not paths:
        ui_text_muted("No configured Gw.exe paths found.")
        return

    ui_section_header("Guild Wars Executable", "Version check")
    if themed_button("Check Now##gw_exe_update_refresh", "secondary", imgui.ImVec2(96, 0)):
        start_gw_exe_update_status_check(force=True)
    update_all_targets = get_gw_exe_update_all_targets()
    if update_all_targets:
        imgui.same_line()
        if themed_button(f"Update All ({len(update_all_targets)})##gw_exe_update_all", "danger", imgui.ImVec2(112, 0)):
            gw_exe_update_confirm_path = "__all__"
            gw_exe_update_confirm_requested_at = time.time()
    imgui.same_line()
    ui_text_muted("Automatic startup check is lightweight; Check Now forces a full local scan.")

    if gw_exe_update_confirm_path == "__all__":
        render_colored_text("Close affected Guild Wars Client(s) before updating them.", "warning")
        ui_text_muted("The latest Gw.exe is downloaded once into the local Py4GW cache and then copied to each selected Guild Wars folder.")
        if themed_button("Cancel##gw_exe_update_all_cancel", "secondary", imgui.ImVec2(72, 0)):
            gw_exe_update_confirm_path = ""
            gw_exe_update_confirm_requested_at = 0.0
        imgui.same_line()
        if themed_button(f"Confirm Update All ({len(update_all_targets)})##gw_exe_update_all_confirm", "danger", imgui.ImVec2(168, 0)):
            if time.time() - float(gw_exe_update_confirm_requested_at or 0.0) >= 0.35:
                targets = list(update_all_targets)
                gw_exe_update_confirm_path = ""
                gw_exe_update_confirm_requested_at = 0.0
                start_gw_exe_update_all(targets)

    imgui.spacing()
    render_gw_exe_cached_versions_panel(paths)

    imgui.spacing()
    render_gw_exe_redownload_panel()

    for path in paths:
        status = get_gw_exe_update_status(path)
        state = str(status.get("state", "pending"))
        message = str(status.get("message", ""))

        imgui.spacing()
        if state == "current":
            render_colored_text(message or "Gw.exe is up to date.", "success")
        elif state == "outdated":
            render_colored_text(message or "Gw.exe update available.", "warning")
            imgui.same_line()
            if themed_button(f"Update##gw_exe_update_{path}", "danger", imgui.ImVec2(72, 0)):
                gw_exe_update_confirm_path = path
                gw_exe_update_confirm_requested_at = time.time()
        elif state == "updating":
            render_colored_text(message or "Updating Gw.exe...", "warning")
        elif state == "checking" or state == "pending":
            ui_text_muted(message or "Checking Gw.exe version...")
        else:
            render_colored_text(message or "Gw.exe update check failed.", "danger")
            if str(message or "").startswith("Update failed"):
                imgui.same_line()
                if themed_button(f"Restart Update##gw_exe_update_restart_{path}", "danger", imgui.ImVec2(122, 0)):
                    start_gw_exe_update(path)

        ui_text_muted(path)

        if gw_exe_update_confirm_path == path:
            render_colored_text("Close Guild Wars Client before updating this Gw.exe.", "warning")
            if themed_button(f"Cancel##gw_exe_update_cancel_{path}", "secondary", imgui.ImVec2(72, 0)):
                gw_exe_update_confirm_path = ""
                gw_exe_update_confirm_requested_at = 0.0
            imgui.same_line()
            if themed_button(f"Confirm Update##gw_exe_update_confirm_{path}", "danger", imgui.ImVec2(132, 0)):
                if time.time() - float(gw_exe_update_confirm_requested_at or 0.0) >= 0.35:
                    gw_exe_update_confirm_path = ""
                    gw_exe_update_confirm_requested_at = 0.0
                    start_gw_exe_update(path)

def render_gw_exe_version_badge(account):
    if not gw_exe_update_enabled:
        return

    imgui.same_line()
    path = normalize_gw_exe_path(str(getattr(account, "gw_path", "") or ""))
    if not path:
        render_status_badge("GW", "secondary", f"{id(account)}_gw_no_path")
        return

    status = get_gw_exe_update_status(path)
    state = str(status.get("state", "pending") or "pending").lower()
    if state == "current":
        render_status_badge("GW", "success", f"{id(account)}_gw_current")
    elif state == "outdated":
        render_status_badge("GW", "warning", f"{id(account)}_gw_outdated")
    elif state == "error":
        render_status_badge("GW", "danger", f"{id(account)}_gw_error")
    else:
        render_status_badge("GW", "secondary", f"{id(account)}_gw_pending")


def render_py4gw_badge(account, running, pid):
    if not getattr(account, "inject_py4gw", False):
        return

    loaded = get_account_py4gw_loaded_status(account, running=running, pid=pid)

    imgui.same_line()
    if not running:
        render_status_badge("PY", "secondary", f"{id(account)}_py_stopped")
        return

    if loaded is None:
        render_status_badge("PY?", "secondary", f"{id(account)}_py_unknown")
        return

    render_status_badge("PY", "success" if loaded else "danger", f"{id(account)}_py_{'loaded' if loaded else 'missing'}")

    if not loaded:
        imgui.same_line()
        if themed_button(f"Inject PY##inject_py4gw_{id(account)}", "primary"):
            ini_handler.write_key("settings", "autoexec_script", account.script_path)
            if launch_gw.attempt_dll_injection(pid, delay=0, dll_type="Py4GW"):
                set_account_dll_loaded_cache(account, pid, "Py4GW", True)
                log_history.append(f"Py4GW - Re-injected for: {account.character_name}")
            else:
                set_account_dll_loaded_cache(account, pid, "Py4GW", False)
                log_history.append(f"Py4GW - Re-injection failed for: {account.character_name}")


def render_toolbox_badge(account, running, pid):
    if not getattr(account, "inject_gwtoolbox", False):
        return

    loaded = get_account_toolbox_loaded_status(account, running=running, pid=pid)

    imgui.same_line()
    if not running:
        render_status_badge("TB", "secondary", f"{id(account)}_stopped")
        return

    if loaded is None:
        render_status_badge("TB?", "secondary", f"{id(account)}_toolbox_unknown")
        return

    render_status_badge("TB", "success" if loaded else "danger", f"{id(account)}_{'loaded' if loaded else 'missing'}")

    if not loaded:
        imgui.same_line()
        if themed_button(f"Inject TB##inject_toolbox_{id(account)}", "primary"):
            toolbox_path = str(getattr(account, "gwtoolbox_path", "") or "")
            if not toolbox_path or not os.path.exists(toolbox_path):
                log_history.append(f"GWToolbox - DLL path missing for: {account.character_name}")
            elif launch_gw.attempt_dll_injection(pid, delay=0, dll_type="GWToolbox", dll_path=toolbox_path):
                set_account_dll_loaded_cache(account, pid, "GWToolbox", True)
                log_history.append(f"GWToolbox - Re-injected for: {account.character_name}")
            else:
                set_account_dll_loaded_cache(account, pid, "GWToolbox", False)
                log_history.append(f"GWToolbox - Re-injection failed for: {account.character_name}")


def get_missing_selected_accounts(selected_accounts):
    missing = []
    for account in selected_accounts:
        running, _pid = get_account_running_status(account)
        if not running:
            missing.append(account)
    return missing


def get_selected_running_missing_state(selected_accounts):
    running_accounts = []
    missing_accounts = []

    for account in list(selected_accounts or []):
        running, _pid = get_account_running_status(account)
        if running:
            running_accounts.append(account)
        else:
            missing_accounts.append(account)

    return running_accounts, missing_accounts


def render_account_running_status(account):
    running, _pid = get_account_running_status(account)

    imgui.same_line()
    if running:
        imgui.push_style_color(imgui.Col_.text, ui_color("success"))
        imgui.text("Running")
        imgui.pop_style_color()
    else:
        imgui.push_style_color(imgui.Col_.text, ui_color("danger"))
        imgui.text("Stopped")
        imgui.pop_style_color()


def reset_team_launch_selected(team):
    changed = False
    for account in team.accounts:
        if getattr(account, "launch_selected", False):
            account.launch_selected = False
            changed = True

    if changed:
        team_manager.save_to_json(config_file)
        log_history.append(f"Launch Selected - Reset selected accounts for team: {team.name}")
    else:
        log_history.append(f"Launch Selected - No selected accounts to reset for team: {team.name}")


def select_all_team_launch_selected(team):
    changed = False
    selected = 0
    for account in team.accounts:
        selected += 1
        if not getattr(account, "launch_selected", False):
            account.launch_selected = True
            changed = True

    if changed:
        team_manager.save_to_json(config_file)
    log_history.append(f"Launch Selected - Selected all {selected} account(s) for team: {team.name}")


def render_teams_top_bar(team_count: int):
    imgui.spacing()

    try:
        imgui.align_text_to_frame_padding()
    except Exception:
        pass

    imgui.push_style_color(imgui.Col_.text, ui_color("accent"))
    imgui.text("Teams")
    imgui.pop_style_color()

    imgui.same_line()
    imgui.push_style_color(imgui.Col_.text, ui_color("muted"))
    imgui.text(f"{team_count} teams")
    imgui.pop_style_color()

    try:
        button_width = 112.0
        avail = imgui.get_content_region_avail()
        avail_x = float(avail.x if hasattr(avail, "x") else avail[0])
        current_x = float(imgui.get_cursor_pos_x())
        right_x = current_x + max(8.0, avail_x - button_width)
        imgui.same_line()
        imgui.set_cursor_pos_x(right_x)
    except Exception:
        imgui.same_line()

    render_theme_selector_inline()

    imgui.separator()


def render_locked_team_contents_panel(show_unlock_controls: bool = False):
    imgui.push_style_color(imgui.Col_.text, ui_color("accent"))
    imgui.text("Teams")
    imgui.pop_style_color()

    try:
        button_width = 112.0
        avail = imgui.get_content_region_avail()
        avail_x = float(avail.x if hasattr(avail, "x") else avail[0])
        current_x = float(imgui.get_cursor_pos_x())
        right_x = current_x + max(8.0, avail_x - button_width)
        imgui.same_line()
        imgui.set_cursor_pos_x(right_x)
    except Exception:
        imgui.same_line()

    render_theme_selector_inline()
    imgui.separator()

    ui_text_muted("Team and account contents are hidden while Credential Security is locked.")
    ui_text_muted("Unlock credentials to view teams, character names, paths and launch settings.")

    if show_unlock_controls:
        imgui.spacing()
        render_credential_security_panel()


def show_team_view():
    global team_manager, launch_gw, visible_windows, is_compact_view, last_is_compact_view, launcher_config_tab

    ensure_team_data_loaded()

    if credentials_are_locked():
        render_locked_team_contents_panel(show_unlock_controls=bool(is_compact_view))
        return

    render_teams_top_bar(len(team_manager.teams))

    total_accounts = sum(len(team.accounts) for team in team_manager.teams.values())
    ui_info_line("View", "Compact" if is_compact_view else "Advanced")
    ui_info_line("Accounts", str(total_accounts))

    toggle_label = "Switch to Advanced View" if is_compact_view else "Switch to Compact View"
    if themed_button(f"{toggle_label}##visibility_toggle", "secondary"):
        is_compact_view = not is_compact_view
        ini_handler.write_key("Py4GW_Launcher", "is_compact_view", str(is_compact_view))
        log_history.append(f"Saved is_compact_view to [Py4GW_Launcher]: {is_compact_view}")

    if imgui.is_item_hovered():
        if is_compact_view:
            imgui.set_tooltip("Switch to Advanced View to show Console and Configuration panels")
        else:
            imgui.set_tooltip("Switch to Compact View to hide Console and Configuration panels")

    imgui.spacing()
    if themed_button("Close Launcher Clients##close_launcher_clients_all", "danger"):
        close_launcher_managed_clients()

    imgui.spacing()

    if is_compact_view != last_is_compact_view:
        if is_compact_view:
            hello_imgui.change_window_size((400, 520))
            visible_windows["AdvDockSpace"] = False
            visible_windows["ConsoleDockSpace"] = False
            visible_windows["MainDockSpace"] = True
        else:
            hello_imgui.change_window_size((980, 660))
            visible_windows["AdvDockSpace"] = True
            visible_windows["ConsoleDockSpace"] = True
            visible_windows["MainDockSpace"] = True

        log_history.append(
            f"Visibility toggled: AdvDockSpace={visible_windows['AdvDockSpace']}, "
            f"ConsoleDockSpace={visible_windows['ConsoleDockSpace']}, "
            f"MainDockSpace={visible_windows['MainDockSpace']}"
        )
        last_is_compact_view = is_compact_view

    if not team_manager.teams:
        ui_text_muted("No teams available yet. Create a team in Account Configuration.")
        return

    imgui.separator()

    for team_name, team in team_manager.teams.items():
        team_label = f"{team_name}###team_node_{id(team)}"
        is_open = imgui.tree_node(team_label)


        imgui.indent()
        if normalize_launcher_theme_mode(ui_theme_mode) == THEME_LIGHT:
            team_info_color = (0.00, 0.00, 0.00, 1.00)
        else:
            team_info_color = ui_color("text")
        imgui.push_style_color(imgui.Col_.text, team_info_color)
        imgui.text(f"Team: {team_name}")
        imgui.text(f"Accounts: {len(team.accounts)}")
        imgui.pop_style_color()
        imgui.unindent()

        if is_open:
            imgui.indent()

            selected_accounts = [
                account for account in team.accounts
                if getattr(account, "launch_selected", False)
            ]

            missing_selected_accounts = get_missing_selected_accounts(selected_accounts)
            has_restart_missing = (
                len(selected_accounts) > 0
                and len(missing_selected_accounts) > 0
                and len(missing_selected_accounts) < len(selected_accounts)
            )


            if themed_button(f"Launch Team##launch_team_{id(team)}", "primary"):
                log_history.append(f"Launching all accounts for team: {team_name}")
                launch_gw.start_team_launch_thread(team)

            imgui.same_line()
            if themed_button(f"Grid Config##launch_grid_setup_{id(team)}", "primary"):
                open_grid_start_tab()

            imgui.same_line()
            if themed_button(f"Close Team Clients##close_team_clients_{id(team)}", "danger"):
                close_launcher_managed_clients(team)

            if has_restart_missing:
                selected_button_label = f"Restart Missing ({len(missing_selected_accounts)})##restart_missing_{id(team)}"
            else:
                selected_button_label = f"Launch Selected ({len(selected_accounts)})##launch_selected_{id(team)}"

            if themed_button(selected_button_label, "primary"):
                if has_restart_missing:
                    launch_gw.start_missing_accounts_thread(team, missing_selected_accounts)
                else:
                    launch_gw.start_selected_accounts_thread(team, selected_accounts)

            imgui.same_line()
            if themed_button(f"Select All##select_all_{id(team)}", "secondary"):
                select_all_team_launch_selected(team)

            imgui.same_line()
            if themed_button(f"Reset Selected##reset_selected_{id(team)}", "secondary"):
                reset_team_launch_selected(team)

            imgui.spacing()
            imgui.separator()

            for account in team.accounts:
                account_id = id(account)
                account_display_name = get_account_display_name(account)

                selected_state = bool(getattr(account, "launch_selected", False))
                changed_selected, selected_state = imgui.checkbox(f"##select_account_{account_id}", selected_state)
                if changed_selected:
                    account.launch_selected = bool(selected_state)
                    team_manager.save_to_json(config_file)
                    log_history.append(
                        f"Launch Selected - {'Selected' if account.launch_selected else 'Unselected'} account: {account.character_name}"
                    )

                imgui.same_line()
                if themed_button(f"Launch##launch_account_{account_id}", "primary"):
                    log_history.append(f"Launching account: {account.character_name}")
                    invalidate_account_running_status(account)
                    launch_gw.launch_gw(account)

                running, pid = get_account_running_status(account)
                render_gw_exe_version_badge(account)
                imgui.same_line()
                imgui.push_style_color(imgui.Col_.text, ui_color("success") if running else ui_color("danger"))
                imgui.text(account_display_name)
                imgui.pop_style_color()

                render_py4gw_badge(account, running, pid)
                render_toolbox_badge(account, running, pid)

            imgui.unindent()
            imgui.tree_pop()

        imgui.spacing()
        imgui.separator()

def show_account_content():
    global selected_team, team_manager, config_file, launch_gw


    team_names = [team.name for team in team_manager.teams.values()]


    selected_index = -1
    if selected_team:
        selected_index = team_names.index(selected_team.name) if selected_team.name in team_names else -1


    imgui.set_next_item_width(ui_responsive_input_width())
    changed, selected_index = imgui.combo(
        "Select Team", selected_index, team_names
    )


    if changed and selected_index != -1:
        selected_team = team_manager.get_team(team_names[selected_index])
        if selected_team:
            log_history.append(f"Selected team: {selected_team.name}")
    imgui.same_line()

    if not selected_team:
        imgui.text("No team selected. Please select a team from the dropdown.")
        return

    imgui.separator()
    imgui.text(f"Managing Team: {selected_team.name}")
    imgui.separator()


    for account_index, account in enumerate(selected_team.accounts):
        account_display_name = get_account_display_name(account)
        if imgui.collapsing_header(f"{account_display_name}###launch_config_account_{id(account)}"):
            imgui.spacing()


            if themed_button(f"Launch Account##{id(account)}", "primary"):
                launch_gw.launch_gw(account)
                log_history.append(f"Launching account: {account.character_name}")


            imgui.text("Run python script at launch")
            imgui.set_next_item_width(ui_responsive_input_width())
            _, account.script_path = imgui.input_text(f"##{id(account)}", account.script_path, 256)
            imgui.same_line()
            if themed_button(f"Select Script##{id(account)}", "secondary"):
                selected_script = select_python_script()
                if selected_script:
                    account.script_path = selected_script
                    team_manager.save_to_json(config_file)


            team_manager.save_to_json(config_file)


def apply_pending_rename_client_edits(log_changes: bool = True):
    changed_count = 0
    try:
        valid_keys = set()
        for current_team in team_manager.teams.values():
            for account in current_team.accounts:
                account_key = id(account)
                valid_keys.add(account_key)
                if account_key not in pending_rename_client_names:
                    continue

                pending_name = str(pending_rename_client_names.get(account_key, "") or "")
                current_name = str(getattr(account, "gw_client_name", "") or "")
                if pending_name == current_name:
                    continue

                old_display_name = get_account_display_name(account)
                account.gw_client_name = pending_name
                invalidate_account_running_status(account)
                new_display_name = get_account_display_name(account)
                changed_count += 1

                if log_changes and new_display_name != old_display_name:
                    log_history.append(f"Account Display - Team name changed from '{old_display_name}' to '{new_display_name}'.")

        for account_key in list(pending_rename_client_names.keys()):
            if account_key not in valid_keys:
                pending_rename_client_names.pop(account_key, None)
    except Exception as e:
        log_history.append(f"Account Display - Pending rename apply failed: {str(e)}")

    return changed_count


def save_teams_to_json(name):
    global config_file
    imgui.separator()
    if themed_button("Save##" + str(name), "primary"):
        try:
            apply_pending_rename_client_edits()
            team_manager.save_to_json(config_file)
            log_history.append("Config saved!")
        except Exception as e:
            log_history.append(f"Error saving teams: {e}")

def select_folder():
    root = tk.Tk()
    root.withdraw()
    folder_path = filedialog.askdirectory(title="Select Guild Wars Path")
    root.destroy()
    return folder_path

def select_gw_exe():
    root = tk.Tk()
    root.withdraw()
    file_path = filedialog.askopenfilename(
        title="Select Guild Wars Executable",
        filetypes=[("Executable Files", "*.exe")],
        initialfile="Gw.exe"
    )
    root.destroy()
    return file_path

def select_dll(name):
    root = tk.Tk()
    root.withdraw()
    file_path = filedialog.askopenfilename(
        title="Select DLL",
        filetypes=[("dynamic Libraries", "*.dll")],
        initialfile=name
    )
    root.destroy()
    return file_path

def select_python_script():
    root = tk.Tk()
    root.withdraw()
    file_path = filedialog.askopenfilename(
        title="Select Python script",
        filetypes=[("Python Scripts", "*.py")]
    )
    root.destroy()
    return file_path


def select_mod_file():
    root = tk.Tk()
    root.withdraw()
    file_path = filedialog.askopenfilename(
        title="Select Mod File",
        filetypes=[("Mod Files", "*.tpf")]
    )
    root.destroy()
    if file_path:

        log_history.append(f"Selected mod file: {file_path}")
        return file_path
    return None


def select_gwtoolbox_dll():
    root = tk.Tk()
    root.withdraw()
    file_path = filedialog.askopenfilename(
        title="Select GWToolbox DLL",
        filetypes=[("DLL Files", "*.dll"), ("All Files", "*.*")]
    )
    root.destroy()
    if file_path:
        log_history.append(f"Selected GWToolbox DLL: {file_path}")
        return file_path
    return None

team_manager = TeamManager()
selected_team = None
entered_team_name = ""
team_create_name = ""
team_rename_name = ""
team_duplicate_name = ""
last_selected_team_name = ""
pending_delete_team_name = None
pending_delete_account_id = None
account_copy_target_names = {}
pending_account_copy_create = None
account_running_status_cache = {}
account_toolbox_status_cache = {}
account_py4gw_status_cache = {}
dll_status_error_log_cache = {}
pending_rename_client_names = {}
ACCOUNT_STATUS_REFRESH_SECONDS = 1.0
TOOLBOX_STATUS_REFRESH_SECONDS = 12.0
PY4GW_STATUS_REFRESH_SECONDS = 12.0
DLL_STATUS_ERROR_LOG_SECONDS = 60.0
data_loaded = False
account_password_visibility = {}
new_account_show_password = False


CREDENTIAL_ENC_PREFIX = "enc:v1:"
CREDENTIAL_KDF_ITERATIONS = 75000
CREDENTIAL_META_KEY = "__py4gw_credentials_meta__"
CREDENTIAL_JSON_ENC_MARKER = "__py4gw_encrypted_json__"
CREDENTIAL_VERIFY_VALUE = "py4gw-credential-verify-v1"
credentials_protection_enabled = False
credentials_unlocked = False
credential_encrypt_email = True
credential_encrypt_password = True
credential_encrypt_character_name = False
credential_encrypt_complete_json = False
credential_active_salt = None
credential_active_iterations = CREDENTIAL_KDF_ITERATIONS
credential_active_enc_key = None
credential_active_mac_key = None
credential_security_password = ""
credential_security_password_confirm = ""
credential_security_old_password = ""
credential_security_new_password = ""
credential_security_new_password_confirm = ""
credential_remove_encryption_password = ""
credential_change_password_active = False
credential_enable_setup_active = False
credential_remove_encryption_confirm_active = False

new_account_data = {
    "character_name": "",
    "email": "",
    "password": "",
    "gw_client_name": "",
    "gw_path": "",
    "extra_args": "",
    "run_as_admin": False,
    "inject_py4gw": True,
    "inject_gwtoolbox": False,
    "gwtoolbox_path": "",
    "inject_gmod": False,
    "gmod_mods": [],
    "resize_client": False,
    "top_left": (0, 0),
    "width": 800,
    "height": 600
}


is_compact_view = ini_handler.read_bool("Py4GW_Launcher", "is_compact_view", False)
last_is_compact_view = is_compact_view
visible_windows = {
    "AdvDockSpace": True,
    "MainDockSpace": True,
    "ConsoleDockSpace": True,
}
ui_theme_mode = read_launcher_theme_mode(THEME_DARK)
applied_ui_theme_mode = None
modern_style_applied = False
log_history.append(f"Loaded is_compact_view from [Py4GW_Launcher]: {is_compact_view}")
log_history.append(f"Loaded theme_mode from [Py4GW_Launcher]: {get_launcher_theme_label(ui_theme_mode)}")


def _b64e(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def _b64d(value: str) -> bytes:
    value = str(value or "")
    padding = "=" * ((4 - len(value) % 4) % 4)
    return base64.urlsafe_b64decode((value + padding).encode("ascii"))


def is_encrypted_credential_value(value) -> bool:
    return isinstance(value, str) and value.startswith(CREDENTIAL_ENC_PREFIX)


def get_credentials_scope_dict() -> dict:
    if credential_encrypt_complete_json:
        return {
            "email": False,
            "password": False,
            "character_name": False,
            "complete_json": True,
        }

    return {
        "email": bool(credential_encrypt_email),
        "password": bool(credential_encrypt_password),
        "character_name": bool(credential_encrypt_character_name),
        "complete_json": False,
    }


def set_credentials_scope_from_dict(scope):
    global credential_encrypt_email, credential_encrypt_password, credential_encrypt_character_name, credential_encrypt_complete_json

    scope = scope if isinstance(scope, dict) else {}
    credential_encrypt_complete_json = bool(scope.get("complete_json", False))
    if credential_encrypt_complete_json:
        credential_encrypt_email = False
        credential_encrypt_password = False
        credential_encrypt_character_name = False
    else:
        credential_encrypt_email = bool(scope.get("email", True))
        credential_encrypt_password = bool(scope.get("password", True))
        credential_encrypt_character_name = bool(scope.get("character_name", False))


def get_credentials_field_names():
    fields = []
    if credential_encrypt_email:
        fields.append("email")
    if credential_encrypt_password:
        fields.append("password")
    if credential_encrypt_character_name:
        fields.append("character_name")
    return fields


def get_all_encryptable_field_names():
    return ("email", "password", "character_name")


def get_credentials_scope_label() -> str:
    if credential_encrypt_complete_json:
        return "Complete JSON File"

    labels = []
    if credential_encrypt_email:
        labels.append("Email")
    if credential_encrypt_password:
        labels.append("Password")
    if credential_encrypt_character_name:
        labels.append("Charname")
    return ", ".join(labels) if labels else "None"


def get_credentials_metadata_for_storage() -> dict:
    return {
        "version": 1,
        "scope": get_credentials_scope_dict(),
        "verification": encrypt_credential_value(CREDENTIAL_VERIFY_VALUE),
    }


def is_encrypted_json_wrapper(data) -> bool:
    return (
        isinstance(data, dict)
        and bool(data.get(CREDENTIAL_JSON_ENC_MARKER))
        and is_encrypted_credential_value(data.get("payload"))
    )


def read_encrypted_json_wrapper(file_path=None):
    path = file_path or config_file
    try:
        if not path or not os.path.exists(path):
            return None
        with open(path, "r", encoding="utf-8") as file:
            data = json.load(file)
        if is_encrypted_json_wrapper(data):
            return data
    except Exception:
        return None
    return None


def get_encrypted_json_payload(file_path=None):
    wrapper = read_encrypted_json_wrapper(file_path)
    if not wrapper:
        return None
    return wrapper.get("payload")


def apply_complete_json_locked_state():
    global credentials_protection_enabled, credentials_unlocked
    global credential_encrypt_email, credential_encrypt_password, credential_encrypt_character_name, credential_encrypt_complete_json

    credentials_protection_enabled = True
    credentials_unlocked = False
    credential_encrypt_email = False
    credential_encrypt_password = False
    credential_encrypt_character_name = False
    credential_encrypt_complete_json = True


def apply_credentials_metadata_from_data(data):
    if not isinstance(data, dict):
        return

    metadata = data.get(CREDENTIAL_META_KEY)
    if isinstance(metadata, dict):
        scope = metadata.get("scope", {})
        if isinstance(scope, dict):
            set_credentials_scope_from_dict(scope)



def _rotl32(value: int, shift: int) -> int:
    return ((value << shift) & 0xFFFFFFFF) | (value >> (32 - shift))


def _chacha20_quarter_round(state, a, b, c, d):
    state[a] = (state[a] + state[b]) & 0xFFFFFFFF
    state[d] ^= state[a]
    state[d] = _rotl32(state[d], 16)
    state[c] = (state[c] + state[d]) & 0xFFFFFFFF
    state[b] ^= state[c]
    state[b] = _rotl32(state[b], 12)
    state[a] = (state[a] + state[b]) & 0xFFFFFFFF
    state[d] ^= state[a]
    state[d] = _rotl32(state[d], 8)
    state[c] = (state[c] + state[d]) & 0xFFFFFFFF
    state[b] ^= state[c]
    state[b] = _rotl32(state[b], 7)


def _chacha20_block(key: bytes, nonce: bytes, counter: int) -> bytes:
    state = list(struct.unpack("<4I", b"expand 32-byte k"))
    state.extend(struct.unpack("<8I", key))
    state.append(counter & 0xFFFFFFFF)
    state.extend(struct.unpack("<3I", nonce))
    working = state[:]
    for _ in range(10):
        _chacha20_quarter_round(working, 0, 4, 8, 12)
        _chacha20_quarter_round(working, 1, 5, 9, 13)
        _chacha20_quarter_round(working, 2, 6, 10, 14)
        _chacha20_quarter_round(working, 3, 7, 11, 15)
        _chacha20_quarter_round(working, 0, 5, 10, 15)
        _chacha20_quarter_round(working, 1, 6, 11, 12)
        _chacha20_quarter_round(working, 2, 7, 8, 13)
        _chacha20_quarter_round(working, 3, 4, 9, 14)
    return struct.pack("<16I", *[((working[i] + state[i]) & 0xFFFFFFFF) for i in range(16)])


def _chacha20_xor(key: bytes, nonce: bytes, data: bytes) -> bytes:
    output = bytearray()
    counter = 1
    offset = 0
    while offset < len(data):
        key_stream = _chacha20_block(key, nonce, counter)
        chunk = data[offset:offset + 64]
        output.extend(bytes(a ^ b for a, b in zip(chunk, key_stream)))
        offset += len(chunk)
        counter = (counter + 1) & 0xFFFFFFFF
    return bytes(output)


def derive_credential_keys(master_password: str, salt: bytes, iterations: int):
    master_password = str(master_password or "")
    if not master_password:
        raise ValueError("master password is empty")
    iterations = max(25000, int(iterations or CREDENTIAL_KDF_ITERATIONS))
    key_material = hashlib.pbkdf2_hmac(
        "sha256",
        master_password.encode("utf-8"),
        salt,
        iterations,
        dklen=64,
    )
    return key_material[:32], key_material[32:]


def _credential_mac(mac_key: bytes, salt: bytes, iterations: int, nonce: bytes, ciphertext: bytes) -> bytes:
    mac = hmac.new(mac_key, digestmod=hashlib.sha256)
    mac.update(b"Py4GW-Credential-v1")
    mac.update(salt)
    mac.update(struct.pack("<I", int(iterations)))
    mac.update(nonce)
    mac.update(ciphertext)
    return mac.digest()


def _parse_encrypted_credential_token(value: str) -> dict:
    if not is_encrypted_credential_value(value):
        raise ValueError("value is not encrypted")
    raw = _b64d(value[len(CREDENTIAL_ENC_PREFIX):])
    data = json.loads(raw.decode("utf-8"))
    return {
        "iterations": int(data.get("i", CREDENTIAL_KDF_ITERATIONS)),
        "salt": _b64d(data["s"]),
        "nonce": _b64d(data["n"]),
        "ciphertext": _b64d(data["c"]),
        "tag": _b64d(data["t"]),
    }


def encrypt_credential_value(plain_value) -> str:
    global credential_active_salt, credential_active_iterations

    plain_value = str(plain_value or "")
    if is_encrypted_credential_value(plain_value):
        return plain_value
    if not credentials_protection_enabled:
        return plain_value
    if not credentials_unlocked or credential_active_enc_key is None or credential_active_mac_key is None:
        raise RuntimeError("credential encryption is locked")
    if credential_active_salt is None:
        credential_active_salt = secrets.token_bytes(16)

    nonce = secrets.token_bytes(12)
    ciphertext = _chacha20_xor(credential_active_enc_key, nonce, plain_value.encode("utf-8"))
    tag = _credential_mac(
        credential_active_mac_key,
        credential_active_salt,
        credential_active_iterations,
        nonce,
        ciphertext,
    )
    payload = {
        "i": int(credential_active_iterations),
        "s": _b64e(credential_active_salt),
        "n": _b64e(nonce),
        "c": _b64e(ciphertext),
        "t": _b64e(tag),
    }
    return CREDENTIAL_ENC_PREFIX + _b64e(json.dumps(payload, separators=(",", ":")).encode("utf-8"))


def decrypt_credential_value(encrypted_value: str, master_password: str = None, key_cache: dict = None) -> str:
    if not is_encrypted_credential_value(encrypted_value):
        return str(encrypted_value or "")

    token = _parse_encrypted_credential_token(encrypted_value)
    cache_key = (_b64e(token["salt"]), int(token["iterations"]))

    if (
        credential_active_enc_key is not None
        and credential_active_mac_key is not None
        and credential_active_salt == token["salt"]
        and int(credential_active_iterations) == int(token["iterations"])
    ):
        enc_key = credential_active_enc_key
        mac_key = credential_active_mac_key
    elif key_cache is not None and cache_key in key_cache:
        enc_key, mac_key = key_cache[cache_key]
    else:
        enc_key, mac_key = derive_credential_keys(master_password, token["salt"], token["iterations"])
        if key_cache is not None:
            key_cache[cache_key] = (enc_key, mac_key)

    expected_tag = _credential_mac(
        mac_key,
        token["salt"],
        token["iterations"],
        token["nonce"],
        token["ciphertext"],
    )
    if not hmac.compare_digest(expected_tag, token["tag"]):
        raise ValueError("wrong master password or damaged credential data")

    return _chacha20_xor(enc_key, token["nonce"], token["ciphertext"]).decode("utf-8")


def iter_all_accounts():
    try:
        for team in team_manager.teams.values():
            for account in team.accounts:
                yield account
    except Exception:
        return


def find_first_encrypted_credential_value():
    full_payload = get_encrypted_json_payload()
    if full_payload:
        return full_payload

    try:
        with open(config_file, "r", encoding="utf-8") as file:
            data = json.load(file)
        metadata = data.get(CREDENTIAL_META_KEY) if isinstance(data, dict) else None
        if isinstance(metadata, dict):
            verification = metadata.get("verification", "")
            if is_encrypted_credential_value(verification):
                return verification
    except Exception:
        pass

    for account in iter_all_accounts():
        for attr_name in get_all_encryptable_field_names():
            value = getattr(account, attr_name, "")
            if is_encrypted_credential_value(value):
                return value
    return None


def any_encrypted_credentials() -> bool:
    return find_first_encrypted_credential_value() is not None


def refresh_credentials_security_state():
    global credentials_protection_enabled, credential_encrypt_complete_json
    if get_encrypted_json_payload():
        if not credentials_unlocked:
            apply_complete_json_locked_state()
        else:
            credentials_protection_enabled = True
            credential_encrypt_complete_json = True
        return

    if any_encrypted_credentials():
        credentials_protection_enabled = True


def credentials_are_locked() -> bool:
    return bool(credentials_protection_enabled and not credentials_unlocked)


def ensure_credentials_unlocked_for_action(action_name: str = "Action") -> bool:
    if credentials_are_locked():
        log_history.append(
            f"Credential Security - {action_name} blocked. Unlock credentials with the master password first."
        )
        return False
    return True


def account_to_storage_dict(account: Account) -> dict:
    data = account.to_dict()
    if not credentials_protection_enabled or credential_encrypt_complete_json:
        return data

    for field_name in get_credentials_field_names():
        value = str(data.get(field_name, "") or "")
        if not value or is_encrypted_credential_value(value):
            data[field_name] = value
        else:
            data[field_name] = encrypt_credential_value(value)
    return data


def unlock_credentials_with_master_password(master_password: str) -> bool:
    global credentials_unlocked, credentials_protection_enabled
    global credential_active_salt, credential_active_iterations, credential_active_enc_key, credential_active_mac_key
    global selected_team, entered_team_name

    first_token = find_first_encrypted_credential_value()
    if first_token is None:
        credentials_protection_enabled = False
        credentials_unlocked = False
        log_history.append("Credential Security - No encrypted credentials found.")
        return False

    key_cache = {}
    updates = []
    try:
        first_meta = _parse_encrypted_credential_token(first_token)
        active_enc_key, active_mac_key = derive_credential_keys(
            master_password,
            first_meta["salt"],
            first_meta["iterations"],
        )
        key_cache[(_b64e(first_meta["salt"]), int(first_meta["iterations"]))] = (active_enc_key, active_mac_key)

        credential_active_salt = first_meta["salt"]
        credential_active_iterations = int(first_meta["iterations"])
        credential_active_enc_key = active_enc_key
        credential_active_mac_key = active_mac_key

        if credential_encrypt_complete_json or get_encrypted_json_payload():
            encrypted_payload = get_encrypted_json_payload()
            if not encrypted_payload:
                raise ValueError("encrypted JSON payload missing")
            plain_json = decrypt_credential_value(encrypted_payload, master_password, key_cache)
            data = json.loads(plain_json)
            team_manager.load_plain_data(data)
        else:
            try:
                with open(config_file, "r", encoding="utf-8") as file:
                    raw_data = json.load(file)
                apply_credentials_metadata_from_data(raw_data)
                metadata = raw_data.get(CREDENTIAL_META_KEY) if isinstance(raw_data, dict) else None
                verification = metadata.get("verification", "") if isinstance(metadata, dict) else ""
                if is_encrypted_credential_value(verification):
                    if decrypt_credential_value(verification, master_password, key_cache) != CREDENTIAL_VERIFY_VALUE:
                        raise ValueError("wrong master password or damaged verification token")
            except FileNotFoundError:
                pass

            for account in iter_all_accounts():
                for attr_name in get_all_encryptable_field_names():
                    value = getattr(account, attr_name, "")
                    if is_encrypted_credential_value(value):
                        updates.append((account, attr_name, decrypt_credential_value(value, master_password, key_cache)))

            for account, attr_name, plain_value in updates:
                setattr(account, attr_name, plain_value)

        credentials_protection_enabled = True
        credentials_unlocked = True
        if selected_team is None:
            first_team = team_manager.get_first_team()
            if first_team:
                selected_team = first_team
                entered_team_name = first_team.name
                sync_team_editor_fields(force=True)
        log_history.append("Credential Security - Credentials unlocked.")
        if gw_exe_update_enabled:
            start_gw_exe_update_status_check(force=False)
        return True
    except Exception as e:
        credentials_unlocked = False
        credential_active_salt = None
        credential_active_enc_key = None
        credential_active_mac_key = None
        log_history.append(f"Credential Security - Unlock failed: {str(e)}")
        return False


def enable_credentials_encryption(master_password: str, scope: dict = None) -> bool:
    global credentials_protection_enabled, credentials_unlocked
    global credential_active_salt, credential_active_iterations, credential_active_enc_key, credential_active_mac_key

    try:
        if not str(master_password or ""):
            log_history.append("Credential Security - Master password is empty.")
            return False

        if scope is not None:
            set_credentials_scope_from_dict(scope)

        if not credential_encrypt_complete_json and not get_credentials_field_names():
            log_history.append("Credential Security - Select at least one encryption target.")
            return False

        credential_active_salt = secrets.token_bytes(16)
        credential_active_iterations = CREDENTIAL_KDF_ITERATIONS
        credential_active_enc_key, credential_active_mac_key = derive_credential_keys(
            master_password,
            credential_active_salt,
            credential_active_iterations,
        )
        credentials_protection_enabled = True
        credentials_unlocked = True
        team_manager.save_to_json(config_file)
        log_history.append(
            f"Credential Security - Encryption enabled for {get_credentials_scope_label()}. KDF iterations={credential_active_iterations}."
        )
        return True
    except Exception as e:
        credentials_protection_enabled = False
        credentials_unlocked = False
        credential_active_salt = None
        credential_active_enc_key = None
        credential_active_mac_key = None
        log_history.append(f"Credential Security - Enable failed: {str(e)}")
        return False


def verify_current_master_password(master_password: str) -> bool:
    if not credentials_protection_enabled or credentials_are_locked():
        return False

    if not str(master_password or ""):
        return False

    if credential_active_salt is None or credential_active_enc_key is None or credential_active_mac_key is None:
        return False

    try:
        check_enc_key, check_mac_key = derive_credential_keys(
            master_password,
            credential_active_salt,
            credential_active_iterations,
        )
        return (
            hmac.compare_digest(check_enc_key, credential_active_enc_key)
            and hmac.compare_digest(check_mac_key, credential_active_mac_key)
        )
    except Exception:
        return False


def change_credentials_master_password(old_master_password: str, new_master_password: str) -> bool:
    global credential_active_salt, credential_active_iterations, credential_active_enc_key, credential_active_mac_key
    global credentials_protection_enabled, credentials_unlocked

    if not credentials_protection_enabled:
        log_history.append("Credential Security - Encryption is not enabled.")
        return False

    if credentials_are_locked():
        log_history.append("Credential Security - Unlock credentials before changing the master password.")
        return False

    if not verify_current_master_password(old_master_password):
        log_history.append("Credential Security - Current master password is wrong.")
        return False

    if not str(new_master_password or ""):
        log_history.append("Credential Security - New master password is empty.")
        return False

    try:
        new_salt = secrets.token_bytes(16)
        new_iterations = CREDENTIAL_KDF_ITERATIONS
        new_enc_key, new_mac_key = derive_credential_keys(
            new_master_password,
            new_salt,
            new_iterations,
        )

        credential_active_salt = new_salt
        credential_active_iterations = new_iterations
        credential_active_enc_key = new_enc_key
        credential_active_mac_key = new_mac_key
        credentials_protection_enabled = True
        credentials_unlocked = True


        team_manager.save_to_json(config_file)
        log_history.append(
            f"Credential Security - Master password changed. KDF iterations={credential_active_iterations}."
        )
        return True
    except Exception as e:
        log_history.append(f"Credential Security - Change master password failed: {str(e)}")
        return False

def lock_credentials() -> bool:
    global credentials_unlocked, credential_active_salt, credential_active_enc_key, credential_active_mac_key

    if not credentials_protection_enabled:
        log_history.append("Credential Security - Encryption is not enabled.")
        return False

    if not credentials_unlocked:
        log_history.append("Credential Security - Credentials are already locked.")
        return True

    try:
        for account in iter_all_accounts():
            storage = account_to_storage_dict(account)
            for field_name in get_all_encryptable_field_names():
                if field_name in storage:
                    setattr(account, field_name, storage.get(field_name, ""))

        team_manager.save_to_json(config_file)
        credentials_unlocked = False
        credential_active_salt = None
        credential_active_enc_key = None
        credential_active_mac_key = None
        account_password_visibility.clear()
        log_history.append("Credential Security - Credentials locked.")
        return True
    except Exception as e:
        log_history.append(f"Credential Security - Lock failed: {str(e)}")
        return False


def remove_credentials_encryption() -> bool:
    global credentials_protection_enabled, credentials_unlocked
    global credential_active_salt, credential_active_enc_key, credential_active_mac_key

    if credentials_are_locked():
        log_history.append("Credential Security - Unlock credentials before removing encryption.")
        return False

    try:
        credentials_protection_enabled = False
        team_manager.save_to_json(config_file)
        credentials_unlocked = False
        credential_active_salt = None
        credential_active_enc_key = None
        credential_active_mac_key = None
        account_password_visibility.clear()
        set_credentials_scope_from_dict({"email": True, "password": True, "character_name": False, "complete_json": False})
        log_history.append("Credential Security - Encryption removed. JSON saved as clear text.")
        return True
    except Exception as e:
        log_history.append(f"Credential Security - Remove failed: {str(e)}")
        return False


def render_credential_security_status(status: str):
    imgui.push_style_color(imgui.Col_.text, ui_color("accent"))
    imgui.text("Credential Security")
    imgui.pop_style_color()
    imgui.same_line()
    imgui.push_style_color(imgui.Col_.text, ui_color("muted"))
    imgui.text("Status:")
    imgui.pop_style_color()
    imgui.same_line()

    if status == "Unlocked":
        status_color = ui_color("success")
    elif status == "Locked":
        status_color = ui_color("danger")
    else:
        status_color = ui_color("warning")

    imgui.push_style_color(imgui.Col_.text, status_color)
    imgui.text(status)
    imgui.pop_style_color()
    imgui.separator()


def clear_credential_remove_encryption_fields():
    global credential_remove_encryption_password, credential_remove_encryption_confirm_active
    credential_remove_encryption_password = ""
    credential_remove_encryption_confirm_active = False


def render_credential_security_panel():
    global credential_security_password, credential_security_password_confirm
    global credential_security_old_password, credential_security_new_password, credential_security_new_password_confirm
    global credential_remove_encryption_password
    global credential_change_password_active, credential_enable_setup_active, credential_remove_encryption_confirm_active
    global credential_encrypt_email, credential_encrypt_password, credential_encrypt_character_name, credential_encrypt_complete_json

    refresh_credentials_security_state()

    if credentials_protection_enabled:
        status = "Unlocked" if credentials_unlocked else "Locked"
    else:
        status = "Plain"

    render_credential_security_status(status)
    if credentials_protection_enabled:
        ui_text_muted(f"Encrypted target: {get_credentials_scope_label()}")
    ui_text_muted(
        "Master password encryption protects the selected JSON data on disk. "
        "The launcher hides team and account contents while locked."
    )

    password_flags = imgui.InputTextFlags_.password.value
    password_enter_flags = password_flags
    try:
        password_enter_flags |= imgui.InputTextFlags_.enter_returns_true.value
    except Exception:
        pass

    if not credentials_protection_enabled:
        credential_change_password_active = False
        clear_credential_remove_encryption_fields()
        credential_security_old_password = ""
        credential_security_new_password = ""
        credential_security_new_password_confirm = ""

        if not credential_enable_setup_active:
            if themed_button("Enable Encryption##credential_enable_setup", "primary"):
                credential_enable_setup_active = True
                credential_security_password = ""
                credential_security_password_confirm = ""
                log_history.append("Credential Security - Enable encryption form opened.")
            ui_text_muted("Plain mode. Email/password are currently saved as clear text.")
        else:
            imgui.text("Encryption Targets")

            field_email = bool(credential_encrypt_email and not credential_encrypt_complete_json)
            field_password = bool(credential_encrypt_password and not credential_encrypt_complete_json)
            field_character_name = bool(credential_encrypt_character_name and not credential_encrypt_complete_json)

            changed_email_scope, field_email = imgui.checkbox("Email##credential_scope_email", field_email)
            if changed_email_scope and field_email:
                credential_encrypt_complete_json = False
            credential_encrypt_email = bool(field_email)

            imgui.same_line()
            changed_password_scope, field_password = imgui.checkbox("Password##credential_scope_password", field_password)
            if changed_password_scope and field_password:
                credential_encrypt_complete_json = False
            credential_encrypt_password = bool(field_password)

            imgui.same_line()
            changed_character_scope, field_character_name = imgui.checkbox("Charname##credential_scope_charname", field_character_name)
            if changed_character_scope and field_character_name:
                credential_encrypt_complete_json = False
            credential_encrypt_character_name = bool(field_character_name)

            changed_complete_json_scope, credential_encrypt_complete_json = imgui.checkbox(
                "Complete Json File##credential_scope_complete_json",
                credential_encrypt_complete_json
            )
            if changed_complete_json_scope and credential_encrypt_complete_json:
                credential_encrypt_email = False
                credential_encrypt_password = False
                credential_encrypt_character_name = False

            if credential_encrypt_complete_json:
                ui_text_muted("Complete Json File encrypts the whole accounts.json. Field selections are cleared and ignored.")
            elif not get_credentials_field_names():
                ui_text_muted("Select at least one field or Complete Json File.")

            imgui.set_next_item_width(ui_responsive_input_width())
            enter_master_password, credential_security_password = imgui.input_text(
                label="Master Password##credential_security_password",
                str=credential_security_password,
                flags=password_enter_flags,
            )

            imgui.set_next_item_width(ui_responsive_input_width())
            enter_master_password_confirm, credential_security_password_confirm = imgui.input_text(
                label="Confirm Master Password##credential_security_confirm",
                str=credential_security_password_confirm,
                flags=password_enter_flags,
            )

            submit_set_master_password = bool(enter_master_password or enter_master_password_confirm)

            if themed_button("Set Master Password##credential_set_master", "primary") or submit_set_master_password:
                if not credential_security_password:
                    log_history.append("Credential Security - Master password is empty.")
                elif credential_security_password != credential_security_password_confirm:
                    log_history.append("Credential Security - Master password confirmation does not match.")
                elif enable_credentials_encryption(credential_security_password, get_credentials_scope_dict()):
                    credential_security_password = ""
                    credential_security_password_confirm = ""
                    credential_security_old_password = ""
                    credential_security_new_password = ""
                    credential_security_new_password_confirm = ""
                    clear_credential_remove_encryption_fields()
                    credential_change_password_active = False
                    credential_enable_setup_active = False

            imgui.same_line()
            if themed_button("Cancel##credential_enable_cancel", "secondary"):
                credential_security_password = ""
                credential_security_password_confirm = ""
                credential_enable_setup_active = False
                log_history.append("Credential Security - Enable encryption cancelled.")

    elif credentials_unlocked:
        credential_enable_setup_active = False

        if credential_remove_encryption_confirm_active:
            credential_change_password_active = False
            imgui.push_style_color(imgui.Col_.text, ui_color("warning"))
            imgui.text_wrapped("Remove Encryption will save Email and Password as clear text. Confirm with the current master password.")
            imgui.pop_style_color()

            imgui.set_next_item_width(ui_responsive_input_width())
            enter_remove_encryption_password, credential_remove_encryption_password = imgui.input_text(
                label="Current Master Password##credential_remove_encryption_password",
                str=credential_remove_encryption_password,
                flags=password_enter_flags,
            )

            if themed_button("Confirm Remove Encryption##credential_confirm_remove", "danger") or enter_remove_encryption_password:
                if not credential_remove_encryption_password:
                    log_history.append("Credential Security - Current master password is empty.")
                elif not verify_current_master_password(credential_remove_encryption_password):
                    log_history.append("Credential Security - Current master password is wrong. Encryption was not removed.")
                elif remove_credentials_encryption():
                    credential_security_password = ""
                    credential_security_password_confirm = ""
                    credential_security_old_password = ""
                    credential_security_new_password = ""
                    credential_security_new_password_confirm = ""
                    clear_credential_remove_encryption_fields()
                    credential_change_password_active = False
                    credential_enable_setup_active = False

            imgui.same_line()
            if themed_button("Cancel##credential_cancel_remove_encryption", "secondary"):
                clear_credential_remove_encryption_fields()
                log_history.append("Credential Security - Remove encryption cancelled.")

        elif not credential_change_password_active:
            if themed_button("Change Master Password##credential_open_change_master", "primary"):
                credential_change_password_active = True
                clear_credential_remove_encryption_fields()
                credential_security_old_password = ""
                credential_security_new_password = ""
                credential_security_new_password_confirm = ""
                log_history.append("Credential Security - Change master password form opened.")

            imgui.same_line()
            if themed_button("Lock Credentials##credential_lock", "secondary"):
                lock_credentials()
                credential_security_password = ""
                credential_security_password_confirm = ""
                credential_security_old_password = ""
                credential_security_new_password = ""
                credential_security_new_password_confirm = ""
                clear_credential_remove_encryption_fields()
                credential_change_password_active = False
                credential_enable_setup_active = False

            imgui.same_line()
            if themed_button("Remove Encryption##credential_remove", "danger"):
                credential_remove_encryption_confirm_active = True
                credential_remove_encryption_password = ""
                credential_change_password_active = False
                log_history.append("Credential Security - Remove encryption confirmation requested.")

            ui_text_muted("Unlocked for this launcher session. The key is kept only in RAM.")

        else:
            clear_credential_remove_encryption_fields()
            ui_text_muted("Change Master Password is active. Confirm the current password, then enter the new password.")

            imgui.set_next_item_width(ui_responsive_input_width())
            enter_change_old_password, credential_security_old_password = imgui.input_text(
                label="Current Master Password##credential_security_old_password",
                str=credential_security_old_password,
                flags=password_enter_flags,
            )

            imgui.set_next_item_width(ui_responsive_input_width())
            enter_change_new_password, credential_security_new_password = imgui.input_text(
                label="New Master Password##credential_security_new_password",
                str=credential_security_new_password,
                flags=password_enter_flags,
            )

            imgui.set_next_item_width(ui_responsive_input_width())
            enter_change_new_password_confirm, credential_security_new_password_confirm = imgui.input_text(
                label="Confirm New Master Password##credential_security_new_confirm",
                str=credential_security_new_password_confirm,
                flags=password_enter_flags,
            )

            submit_change_master_password = bool(
                enter_change_old_password
                or enter_change_new_password
                or enter_change_new_password_confirm
            )

            if themed_button("Apply New Master Password##credential_apply_change_master", "primary") or submit_change_master_password:
                if not credential_security_old_password:
                    log_history.append("Credential Security - Current master password is empty.")
                elif not credential_security_new_password:
                    log_history.append("Credential Security - New master password is empty.")
                elif credential_security_new_password != credential_security_new_password_confirm:
                    log_history.append("Credential Security - New master password confirmation does not match.")
                elif change_credentials_master_password(credential_security_old_password, credential_security_new_password):
                    credential_security_password = ""
                    credential_security_password_confirm = ""
                    credential_security_old_password = ""
                    credential_security_new_password = ""
                    credential_security_new_password_confirm = ""
                    clear_credential_remove_encryption_fields()
                    credential_change_password_active = False

            imgui.same_line()
            if themed_button("Cancel##credential_cancel_change_master", "secondary"):
                credential_security_old_password = ""
                credential_security_new_password = ""
                credential_security_new_password_confirm = ""
                credential_change_password_active = False
                log_history.append("Credential Security - Change master password cancelled.")

    else:
        credential_change_password_active = False
        credential_enable_setup_active = False
        clear_credential_remove_encryption_fields()
        credential_security_old_password = ""
        credential_security_new_password = ""
        credential_security_new_password_confirm = ""

        imgui.set_next_item_width(ui_responsive_input_width())
        enter_unlock_password, credential_security_password = imgui.input_text(
            label="Master Password##credential_security_unlock_password",
            str=credential_security_password,
            flags=password_enter_flags,
        )

        if themed_button("Unlock Credentials##credential_unlock", "primary") or enter_unlock_password:
            if unlock_credentials_with_master_password(credential_security_password):
                credential_security_password = ""
                credential_security_password_confirm = ""
                credential_security_old_password = ""
                credential_security_new_password = ""
                credential_security_new_password_confirm = ""
                clear_credential_remove_encryption_fields()
                credential_change_password_active = False
                credential_enable_setup_active = False

        ui_text_muted("Locked. Launching or editing Email/Password requires unlock first.")

    imgui.separator()

def show_window_configuration(account: Account, save_callback=None):
    imgui.separator()
    imgui.text("Window")

    title_preview = get_account_display_name(account)
    imgui.text(f"Window title after launch: {title_preview}")

    changed_resize, account.resize_client = imgui.checkbox(
        f"Set Window Position / Size##resize_client_{id(account)}",
        account.resize_client
    )
    if changed_resize and save_callback:
        save_callback()

    if account.resize_client:
        top_left = account.top_left or (0, 0)
        pos_x = int(top_left[0])
        pos_y = int(top_left[1])

        imgui.set_next_item_width(100)
        changed_x, pos_x = imgui.input_int(f"X##window_x_{id(account)}", pos_x)
        imgui.same_line()
        imgui.set_next_item_width(100)
        changed_y, pos_y = imgui.input_int(f"Y##window_y_{id(account)}", pos_y)

        if changed_x or changed_y:
            account.top_left = (pos_x, pos_y)
            if save_callback:
                save_callback()

        imgui.set_next_item_width(100)
        changed_width, width = imgui.input_int(f"Width##window_width_{id(account)}", int(account.width))
        imgui.same_line()
        imgui.set_next_item_width(100)
        changed_height, height = imgui.input_int(f"Height##window_height_{id(account)}", int(account.height))

        if changed_width or changed_height:
            account.width = max(320, int(width))
            account.height = max(240, int(height))
            if save_callback:
                save_callback()

def show_new_account_window_configuration():
    imgui.separator()
    imgui.text("Window")

    title_preview = new_account_data.get("character_name", "").strip() or "<Character Name>"
    imgui.text(f"Window title after launch: {title_preview}")

    _, new_account_data["resize_client"] = imgui.checkbox(
        "Set Window Position / Size##resize_client_new_item",
        new_account_data.get("resize_client", False)
    )

    if new_account_data.get("resize_client", False):
        top_left = new_account_data.get("top_left", (0, 0)) or (0, 0)
        pos_x = int(top_left[0])
        pos_y = int(top_left[1])

        imgui.set_next_item_width(100)
        changed_x, pos_x = imgui.input_int("X##window_x_new_item", pos_x)
        imgui.same_line()
        imgui.set_next_item_width(100)
        changed_y, pos_y = imgui.input_int("Y##window_y_new_item", pos_y)

        if changed_x or changed_y:
            new_account_data["top_left"] = (pos_x, pos_y)

        imgui.set_next_item_width(100)
        changed_width, width = imgui.input_int(
            "Width##window_width_new_item",
            int(new_account_data.get("width", 800))
        )
        imgui.same_line()
        imgui.set_next_item_width(100)
        changed_height, height = imgui.input_int(
            "Height##window_height_new_item",
            int(new_account_data.get("height", 600))
        )

        if changed_width or changed_height:
            new_account_data["width"] = max(320, int(width))
            new_account_data["height"] = max(240, int(height))

def reset_new_account_form():
    for key in new_account_data.keys():
        if key == "gmod_mods":
            new_account_data[key] = []
        elif key == "top_left":
            new_account_data[key] = (0, 0)
        elif key == "width":
            new_account_data[key] = 800
        elif key == "height":
            new_account_data[key] = 600
        elif key == "inject_py4gw":
            new_account_data[key] = True
        elif isinstance(new_account_data[key], str):
            new_account_data[key] = ""
        else:
            new_account_data[key] = False


def sync_team_editor_fields(force=False):
    global team_rename_name, team_duplicate_name, last_selected_team_name

    current_name = selected_team.name if selected_team else ""
    if force or current_name != last_selected_team_name:
        team_rename_name = ""
        team_duplicate_name = ""
        last_selected_team_name = current_name


def select_team_by_name(team_name: str):
    global selected_team, entered_team_name

    selected_team = team_manager.get_team(team_name)
    if selected_team:
        entered_team_name = selected_team.name
        sync_team_editor_fields(force=True)
        log_history.append(f"Team Management - Selected team: {selected_team.name}")


def render_team_management_panel() -> bool:
    global selected_team, entered_team_name, team_create_name, team_rename_name, team_duplicate_name
    global pending_delete_team_name

    def _avail_x(default_value: float = 520.0) -> float:
        try:
            avail = imgui.get_content_region_avail()
            return float(avail.x if hasattr(avail, "x") else avail[0])
        except Exception:
            return float(default_value)

    def _clamp(value: float, min_value: float, max_value: float) -> float:
        return max(min_value, min(max_value, value))

    def _button_size(width: float = 112.0):
        return imgui.ImVec2(float(width), 22.0)

    def _row_input_width(avail_x: float, button_width: float = 112.0) -> float:
        return _clamp(avail_x - button_width - 14.0, 150.0, 420.0)

    def _input_text_hint(input_id: str, value: str, hint: str, width: float, max_length: int = 128):
        imgui.set_next_item_width(width)
        try:
            return imgui.input_text_with_hint(
                label=input_id,
                hint=hint,
                str=value,
            )
        except Exception:
            try:
                return imgui.input_text_with_hint(input_id, hint, value, max_length)
            except Exception:
                return imgui.input_text(input_id, value, max_length)

    team_names = list(team_manager.teams.keys())
    selected_index = -1
    if selected_team and selected_team.name in team_names:
        selected_index = team_names.index(selected_team.name)

    panel_width = _avail_x()
    narrow = panel_width < 500.0
    action_button_width = 112.0

    ui_section_header("Team Management", "Fast controls")

    select_width = _clamp(panel_width - 330.0, 150.0, 220.0) if not narrow else _clamp(panel_width - 110.0, 150.0, 240.0)
    imgui.set_next_item_width(select_width)
    changed, selected_index = imgui.combo("##team_select", selected_index, team_names)
    if changed and selected_index != -1:
        select_team_by_name(team_names[selected_index])
        pending_delete_team_name = None

    imgui.same_line()
    ui_form_label("Team")
    imgui.same_line()
    if themed_button("Save All##team_save_all", "primary", _button_size(action_button_width)):
        try:
            apply_pending_rename_client_edits()
            team_manager.save_to_json(config_file)
            if selected_team:
                write_team_launch_delay(selected_team.name, selected_team.launch_delay_seconds)
            log_history.append("Team Management - Saved all teams.")
        except Exception as e:
            log_history.append(f"Team Management - Save failed: {str(e)}")

    if not narrow:
        imgui.same_line()
        imgui.push_style_color(imgui.Col_.text, ui_color("muted"))
        if selected_team:
            imgui.text(f"Teams: {len(team_names)}  Selected: {selected_team.name}  Accounts: {len(selected_team.accounts)}")
        else:
            imgui.text(f"Teams: {len(team_names)}")
        imgui.pop_style_color()
    else:
        imgui.push_style_color(imgui.Col_.text, ui_color("muted"))
        if selected_team:
            imgui.text(f"Teams: {len(team_names)}  Selected: {selected_team.name}  Accounts: {len(selected_team.accounts)}")
        else:
            imgui.text(f"Teams: {len(team_names)}")
        imgui.pop_style_color()

    imgui.separator()

    editor_height = 158 if narrow else 140
    ui_begin_card("TeamEditorCard", editor_height, no_scrollbar=True)

    card_width = _avail_x(panel_width)
    input_width = _row_input_width(card_width, action_button_width)

    ui_subsection_title("Create")

    _, team_create_name = _input_text_hint("##team_create_name", team_create_name, "New Name", input_width)
    imgui.same_line()
    create_pressed = themed_button("Create##team_create", "primary", _button_size(action_button_width))

    if create_pressed:
        clean_name = team_create_name.strip()
        if not clean_name:
            log_history.append("Team Create - Team name is empty.")
        elif team_manager.team_exists(clean_name):
            log_history.append(f"Team Create - Team already exists: {clean_name}")
            select_team_by_name(clean_name)
        else:
            new_team = Team(clean_name)
            team_manager.add_team(new_team)
            selected_team = new_team
            entered_team_name = clean_name
            team_create_name = ""
            write_team_launch_delay(new_team.name, new_team.launch_delay_seconds)
            team_manager.save_to_json(config_file)
            sync_team_editor_fields(force=True)
            log_history.append(f"Team Create - Created and saved team: {clean_name}")

    if not selected_team:
        imgui.separator()
        ui_subsection_title("Edit")
        imgui.same_line()
        imgui.push_style_color(imgui.Col_.text, ui_color("muted"))
        imgui.text("Select a team first.")
        imgui.pop_style_color()
        ui_end_card()

        ui_begin_card("TeamSettingsCard", 54, no_scrollbar=True)
        ui_subsection_title("Team Settings")
        imgui.same_line()
        imgui.push_style_color(imgui.Col_.text, ui_color("muted"))
        imgui.text("Select a team first.")
        imgui.pop_style_color()
        ui_end_card()
        return False

    sync_team_editor_fields()

    imgui.separator()

    ui_subsection_title("Edit", selected_team.name)
    imgui.same_line()

    if pending_delete_team_name == selected_team.name:
        if themed_button("Cancel##team_delete_cancel", "secondary", _button_size(action_button_width)):
            pending_delete_team_name = None
            log_history.append("Team Delete - Cancelled.")
        imgui.same_line()
        if themed_button("Confirm##team_delete_confirm", "danger", _button_size(action_button_width)):
            deleted_name = selected_team.name
            if team_manager.delete_team(deleted_name):
                team_manager.save_to_json(config_file)
                selected_team = team_manager.get_first_team()
                entered_team_name = selected_team.name if selected_team else ""
                sync_team_editor_fields(force=True)
                pending_delete_team_name = None
    else:
        if themed_button("Delete Team##team_delete_arm", "danger", _button_size(action_button_width)):
            pending_delete_team_name = selected_team.name
            log_history.append(f"Team Delete - Confirmation required for team: {selected_team.name}")

    card_width = _avail_x(panel_width)
    input_width = _row_input_width(card_width, action_button_width)

    _, team_rename_name = _input_text_hint("##team_rename_name", team_rename_name, "Rename To", input_width)
    imgui.same_line()
    rename_pressed = themed_button("Rename##team_rename", "primary", _button_size(action_button_width))

    if rename_pressed:
        old_name = selected_team.name
        new_name = team_rename_name.strip()
        if team_manager.rename_team(old_name, new_name):
            selected_team = team_manager.get_team(new_name)
            entered_team_name = new_name
            team_manager.save_to_json(config_file)
            sync_team_editor_fields(force=True)
            pending_delete_team_name = None

    _, team_duplicate_name = _input_text_hint("##team_duplicate_name", team_duplicate_name, "Duplicate", input_width)
    imgui.same_line()
    duplicate_pressed = themed_button("Duplicate##team_duplicate", "primary", _button_size(action_button_width))

    if duplicate_pressed:
        duplicate = team_manager.duplicate_team(selected_team.name, team_duplicate_name.strip())
        if duplicate:
            selected_team = duplicate
            entered_team_name = duplicate.name
            team_manager.save_to_json(config_file)
            sync_team_editor_fields(force=True)
            pending_delete_team_name = None

    ui_end_card()

    settings_height = 58 if narrow else 54
    ui_begin_card("TeamSettingsCard", settings_height, no_scrollbar=True)
    ui_subsection_title("Team Settings")

    settings_width = _avail_x(panel_width)
    delay_input_width = _clamp(88.0, 76.0, max(76.0, settings_width - 260.0))

    imgui.set_next_item_width(delay_input_width)
    changed_delay, delay_value = imgui.input_int(
        f"##team_launch_delay_{id(selected_team)}",
        int(getattr(selected_team, "launch_delay_seconds", 15))
    )
    imgui.same_line()
    ui_form_label("Launch Delay")
    imgui.same_line()
    imgui.push_style_color(imgui.Col_.text, ui_color("muted"))
    imgui.text("seconds between team launches")
    imgui.pop_style_color()

    if changed_delay:
        selected_team.launch_delay_seconds = max(0, int(delay_value))
        write_team_launch_delay(selected_team.name, selected_team.launch_delay_seconds)
        log_history.append(
            f"Team Settings - Launch delay for '{selected_team.name}' set to {selected_team.launch_delay_seconds}s."
        )

    ui_end_card()

    return selected_team is not None

def copy_account_to_team(account: Account, target_team_name: str, create_missing: bool = False) -> bool:
    global selected_team, entered_team_name

    clean_name = str(target_team_name).strip()
    if not clean_name:
        log_history.append("Account Copy - Target team name is empty.")
        return False

    target_team = team_manager.get_team(clean_name)
    if target_team is None:
        if not create_missing:
            log_history.append(f"Account Copy - Target team does not exist: {clean_name}")
            return False

        target_team = Team(clean_name)
        team_manager.add_team(target_team)
        write_team_launch_delay(target_team.name, target_team.launch_delay_seconds)
        log_history.append(f"Account Copy - Created target team: {clean_name}")

    copied_account = clone_account(account, reset_launch_selected=True)
    target_team.add_account(copied_account)
    team_manager.save_to_json(config_file)
    log_history.append(
        f"Account Copy - Copied '{account.character_name}' from team "
        f"'{selected_team.name if selected_team else '<none>'}' to team '{target_team.name}'."
    )
    return True


def render_account_copy_to_team_panel(account: Account):
    global pending_account_copy_create

    account_id = id(account)
    if account_id not in account_copy_target_names:
        account_copy_target_names[account_id] = ""

    if themed_button(f"Copy Acc in new Team##account_copy_to_team_{account_id}", "secondary"):
        account_copy_target_names[account_id] = ""
        pending_account_copy_create = None
        log_history.append(f"Account Copy - Enter target team for: {account.character_name}")


    prompt_active = account_copy_target_names.get(account_id, "") != "" or (
        isinstance(pending_account_copy_create, dict)
        and pending_account_copy_create.get("account_id") == account_id
    )


    if not prompt_active and pending_account_copy_create is None:
        pass


    active_key = f"__active_{account_id}"
    if imgui.is_item_clicked():
        account_copy_target_names[active_key] = "1"

    if account_copy_target_names.get(active_key) == "1":
        imgui.spacing()
        imgui.text("Copy account to team:")
        imgui.set_next_item_width(260)
        changed_target, target_name = imgui.input_text(
            f"Target Team Name##account_copy_target_{account_id}",
            account_copy_target_names.get(account_id, ""),
            128
        )
        if changed_target:
            account_copy_target_names[account_id] = target_name
            pending_account_copy_create = None

        imgui.same_line()
        if themed_button(f"Copy##account_copy_execute_{account_id}", "primary"):
            clean_target = account_copy_target_names.get(account_id, "").strip()
            if not clean_target:
                log_history.append("Account Copy - Target team name is empty.")
            elif team_manager.team_exists(clean_target):
                if copy_account_to_team(account, clean_target, create_missing=False):
                    account_copy_target_names[account_id] = ""
                    account_copy_target_names[active_key] = "0"
                    pending_account_copy_create = None
            else:
                pending_account_copy_create = {
                    "account_id": account_id,
                    "team_name": clean_target,
                }
                log_history.append(
                    f"Account Copy - Team '{clean_target}' does not exist. Confirmation required."
                )

        imgui.same_line()
        if themed_button(f"Cancel##account_copy_cancel_{account_id}", "secondary"):
            account_copy_target_names[account_id] = ""
            account_copy_target_names[active_key] = "0"
            pending_account_copy_create = None
            log_history.append("Account Copy - Cancelled.")

        if (
            isinstance(pending_account_copy_create, dict)
            and pending_account_copy_create.get("account_id") == account_id
        ):
            missing_team_name = pending_account_copy_create.get("team_name", "").strip()
            imgui.text(f"Team '{missing_team_name}' does not exist. Create it and copy this account?")
            if themed_button(f"Create Team and Copy##account_copy_create_confirm_{account_id}", "primary"):
                if copy_account_to_team(account, missing_team_name, create_missing=True):
                    account_copy_target_names[account_id] = ""
                    account_copy_target_names[active_key] = "0"
                    pending_account_copy_create = None
            imgui.same_line()
            if themed_button(f"No##account_copy_create_cancel_{account_id}", "secondary"):
                pending_account_copy_create = None
                log_history.append("Account Copy - Create missing team cancelled.")


def ensure_team_data_loaded():
    global data_loaded, selected_team, entered_team_name

    if data_loaded:
        return

    try:
        team_manager.load_from_json(config_file)
        log_history.append(f"Teams loaded from {config_file}")

        refresh_credentials_security_state()
        if credentials_are_locked():
            selected_team = None
            entered_team_name = ""
            log_history.append("Credential Security - Encrypted credentials detected. Team contents hidden until unlock.")
        else:
            first_team = team_manager.get_first_team()
            if first_team:
                selected_team = first_team
                entered_team_name = first_team.name
                sync_team_editor_fields(force=True)
                log_history.append(f"Team Configuration: Auto-selected first team: {first_team.name}")
            else:
                log_history.append("No teams found. Please create one.")
    except Exception as e:
        log_history.append(f"Error loading teams: {e}")

    data_loaded = True


def show_configuration_content():
    global config_file, team_manager, selected_team, entered_team_name, data_loaded, new_account_data
    global account_copy_target_names, pending_account_copy_create, pending_delete_account_id
    global account_password_visibility, new_account_show_password

    ensure_team_data_loaded()

    if credentials_are_locked():
        render_credential_security_panel()
        return

    if not render_team_management_panel():
        return

    render_credential_security_panel()

    ui_section_header("Accounts in Selected Team", f"{len(selected_team.accounts)} accounts")


    for account_index, account in enumerate(list(selected_team.accounts)):
        account_display_name = get_account_display_name(account)


        if imgui.collapsing_header(f"{account_display_name}###account_config_{id(account)}"):
            imgui.spacing()
            imgui.text(f"Account Order: {account_index + 1} / {len(selected_team.accounts)}")

            if themed_button(f"Move Up##account_up_{id(account)}", "secondary"):
                if account_index > 0:
                    selected_team.accounts[account_index - 1], selected_team.accounts[account_index] = selected_team.accounts[account_index], selected_team.accounts[account_index - 1]
                    team_manager.save_to_json(config_file)
                    log_history.append(f"Account Order - Moved up: {account.character_name}")
            imgui.same_line()
            if themed_button(f"Move Down##account_down_{id(account)}", "secondary"):
                if account_index < len(selected_team.accounts) - 1:
                    selected_team.accounts[account_index + 1], selected_team.accounts[account_index] = selected_team.accounts[account_index], selected_team.accounts[account_index + 1]
                    team_manager.save_to_json(config_file)
                    log_history.append(f"Account Order - Moved down: {account.character_name}")
            imgui.same_line()
            if themed_button(f"Duplicate Account##account_duplicate_{id(account)}", "secondary"):
                duplicate = clone_account(account)
                duplicate.character_name = f"{duplicate.character_name} Copy"
                duplicate.launch_selected = False
                selected_team.accounts.insert(account_index + 1, duplicate)
                team_manager.save_to_json(config_file)
                log_history.append(f"Account Duplicate - Duplicated account as independent copy: {account.character_name}")

            imgui.same_line()
            render_account_copy_to_team_panel(account)

            imgui.spacing()
            imgui.set_next_item_width(ui_responsive_input_width())
            changed_character_name, account.character_name = imgui.input_text(f"Character Name##{id(account)}", account.character_name, 128)
            if changed_character_name:
                team_manager.save_to_json(config_file)
            imgui.spacing()
            account_id = id(account)

            if credentials_are_locked():
                imgui.text("Email: <locked - unlock credentials>")
                imgui.text("Password: ********")
                ui_text_muted("Email/Password are encrypted. Unlock Credential Security to edit or launch.")
            else:
                imgui.set_next_item_width(ui_responsive_input_width())
                changed_email, account.email = imgui.input_text(f"Email##{account_id}", account.email, 128)
                if changed_email:
                    team_manager.save_to_json(config_file)
                imgui.spacing()

                password_visible = bool(account_password_visibility.get(account_id, False))
                password_flags = 0 if password_visible else imgui.InputTextFlags_.password.value
                imgui.set_next_item_width(ui_responsive_input_width())

                changed_password, account.password = imgui.input_text(
                    label=f"Password##{account_id}",
                    str=account.password,
                    flags=password_flags
                )
                if changed_password:
                    team_manager.save_to_json(config_file)

                imgui.same_line()

                changed_password_visible, password_visible = imgui.checkbox(
                    f"Show Password##{account_id}",
                    password_visible
                )
                if changed_password_visible:
                    account_password_visibility[account_id] = bool(password_visible)


            imgui.spacing()
            account_key = id(account)
            if account_key not in pending_rename_client_names:
                pending_rename_client_names[account_key] = str(getattr(account, "gw_client_name", "") or "")

            imgui.set_next_item_width(ui_responsive_input_width())
            _changed_gw_client_name, pending_rename_client_names[account_key] = imgui.input_text(
                f"Rename GW Client##{id(account)}",
                pending_rename_client_names.get(account_key, ""),
                128,
            )
            imgui.set_next_item_width(ui_responsive_input_width())
            old_gw_path = account.gw_path
            _, account.gw_path = imgui.input_text(f"GW Path##{id(account)}", account.gw_path, 128)

            imgui.same_line()
            if themed_button(f"Select Gw.exe##{id(account)}", "secondary"):
                selected_exe = select_gw_exe()
                if selected_exe:
                    account.gw_path = selected_exe
                    if account.inject_gmod:
                        launch_gw.create_modlist_for_gmod(account)

            if account.gw_path:
                normalized_path = os.path.normpath(account.gw_path).lower()
                protected_dirs = [
                    os.path.normpath("C:/Program Files (x86)").lower(),
                    os.path.normpath("C:/Program Files").lower()
                ]
                is_protected = any(normalized_path.startswith(protected_dir) for protected_dir in protected_dirs)
                if is_protected:
                    imgui.push_style_color(imgui.Col_.text, (1.0, 0.0, 0.0, 1.0))
                    imgui.text_wrapped(
                            "Warning: GW Path is in a protected directory (C:/Program Files (x86) or C:/Program Files). "
                            "The launcher requires admin privileges to create/modify files (e.g., modlist.txt) in this location. "
                            "Use an unprotected directory such as 'C:/Games/Guild Wars', or run the launcher with elevated privileges (as administrator)."
                        )
                    imgui.pop_style_color()

            if old_gw_path != account.gw_path and account.inject_gmod:
                launch_gw.create_modlist_for_gmod(account)
            imgui.set_next_item_width(ui_responsive_input_width())
            _, account.extra_args = imgui.input_text(f"Extra Args##{id(account)}", account.extra_args, 128)

            show_window_configuration(
                account,
                save_callback=lambda: team_manager.save_to_json(config_file)
            )

            _, account.run_as_admin = imgui.checkbox(f"Run as Admin##{id(account)}", account.run_as_admin)
            _, account.inject_py4gw = imgui.checkbox(f"Inject Py4GW##{id(account)}", account.inject_py4gw)
            _, account.inject_gwtoolbox = imgui.checkbox(f"Inject GWToolbox##{id(account)}", account.inject_gwtoolbox)

            if account.inject_gwtoolbox:
                if getattr(account, "gwtoolbox_path", ""):
                    remove_toolbox = themed_button(f"Remove##gwtoolbox_{id(account)}", "danger")
                    imgui.same_line()
                    imgui.text_wrapped(f"- {account.gwtoolbox_path}")
                    if remove_toolbox:
                        account.gwtoolbox_path = ""
                        team_manager.save_to_json(config_file)
                        log_history.append(f"GWToolbox - Removed DLL path for: {account.character_name}")
                if themed_button(f"Select GWToolbox DLL##{id(account)}", "secondary"):
                    selected_dll = select_gwtoolbox_dll()
                    if selected_dll:
                        account.gwtoolbox_path = selected_dll
                        team_manager.save_to_json(config_file)

            old_inject_gmod = account.inject_gmod
            _, account.inject_gmod = imgui.checkbox(f"Inject gMod##{id(account)}", account.inject_gmod)
            if old_inject_gmod != account.inject_gmod:
                if account.inject_gmod:
                    launch_gw.create_modlist_for_gmod(account)
                else:
                    gw_dir = os.path.dirname(account.gw_path)
                    modlist_path = os.path.join(gw_dir, "modlist.txt")
                    if os.path.exists(modlist_path):
                        try:
                            os.remove(modlist_path)
                            log_history.append(f"Removed modlist.txt at {modlist_path} as gMod injection was disabled")
                        except Exception as e:
                            log_history.append(f"Error removing modlist.txt at {modlist_path}: {str(e)}")

            if account.inject_gmod:
                imgui.text("gMod Mods:")
                for i, mod in enumerate(list(account.gmod_mods)):
                    remove_mod = themed_button(f"Remove##{i}_{id(account)}", "danger")
                    imgui.same_line()
                    imgui.text_wrapped(f"- {mod}")
                    if remove_mod:
                        account.gmod_mods.pop(i)
                        team_manager.save_to_json(config_file)
                        launch_gw.create_modlist_for_gmod(account)
                        break
                if themed_button(f"Add Mod##{id(account)}", "secondary"):
                    mod_file = select_mod_file()
                    if mod_file and mod_file not in account.gmod_mods:
                        account.gmod_mods.append(mod_file)
                        team_manager.save_to_json(config_file)
                        launch_gw.create_modlist_for_gmod(account)

            save_teams_to_json(id(account))
            imgui.same_line()

            if pending_delete_account_id == id(account):
                imgui.push_style_color(imgui.Col_.text, ui_color("danger"))
                imgui.text(f"Delete account '{account_display_name}'?")
                imgui.pop_style_color()

                imgui.same_line()
                if themed_button(f"Confirm Delete##confirm_delete_account_{id(account)}", "danger"):
                    deleted_name = account.character_name.strip() or account_display_name
                    selected_team.accounts.remove(account)
                    account_password_visibility.pop(id(account), None)
                    team_manager.save_to_json(config_file)
                    pending_delete_account_id = None
                    log_history.append(f"Deleted account: {deleted_name}")

                    gw_dir = os.path.dirname(account.gw_path)
                    modlist_path = os.path.join(gw_dir, "modlist.txt")
                    if os.path.exists(modlist_path):
                        try:
                            os.remove(modlist_path)
                            log_history.append(f"Removed modlist.txt at {modlist_path} as account was deleted")
                        except Exception as e:
                            log_history.append(f"Error removing modlist.txt at {modlist_path}: {str(e)}")

                imgui.same_line()
                if themed_button(f"Cancel##cancel_delete_account_{id(account)}", "secondary"):
                    pending_delete_account_id = None
                    log_history.append(f"Account Delete - Cancelled for account: {account_display_name}")
            else:
                if themed_button(f"Delete Account##{id(account)}", "danger"):
                    pending_delete_account_id = id(account)
                    log_history.append(f"Account Delete - Confirmation required for account: {account_display_name}")


    if imgui.collapsing_header("Add New Account", imgui.TreeNodeFlags_.default_open.value):
        imgui.spacing()
        if credentials_are_locked():
            ui_text_muted("Credential Security is locked. Unlock before adding a new account.")

        for key in new_account_data.keys():
            if key == "password":
                password_flags = 0 if new_account_show_password else imgui.InputTextFlags_.password.value
                imgui.set_next_item_width(ui_responsive_input_width())


                _, new_account_data[key] = imgui.input_text(
                label=f"Password##new_item",
                str=new_account_data[key],
                flags=password_flags
                )


                imgui.same_line()
                _, new_account_show_password = imgui.checkbox(
                    "Show Password##new_item",
                    new_account_show_password
                )
            elif key == "gw_path":
                imgui.set_next_item_width(ui_responsive_input_width())


                _, new_account_data[key] = imgui.input_text(
                    key.replace("_", " ").title() + "##new_item",
                    new_account_data[key],
                    128
                )


                imgui.same_line()
                if themed_button(f"Select Gw.exe##new_item", "secondary"):
                    selected_exe = select_gw_exe()
                    if selected_exe:
                        new_account_data[key] = selected_exe

                if new_account_data[key]:
                    normalized_path = os.path.normpath(new_account_data[key]).lower()
                    protected_dirs = [
                        os.path.normpath("C:/Program Files (x86)").lower(),
                        os.path.normpath("C:/Program Files").lower()
                    ]
                    is_protected = any(normalized_path.startswith(protected_dir) for protected_dir in protected_dirs)
                    if is_protected:
                        imgui.push_style_color(imgui.Col_.text, (1.0, 0.0, 0.0, 1.0))
                        imgui.text_wrapped(
                            "Warning: GW Path is in a protected directory (C:/Program Files (x86) or C:/Program Files). "
                            "The launcher requires admin privileges to create/modify files (e.g., modlist.txt) in this location. "
                            "Use an unprotected directory such as 'C:/Games/Guild Wars', or run the launcher with elevated privileges (as administrator)."
                        )
                        imgui.pop_style_color()
            elif key == "gwtoolbox_path":
                _, new_account_data["inject_gwtoolbox"] = imgui.checkbox("Inject GWToolbox##new_item", new_account_data["inject_gwtoolbox"])
                if new_account_data["inject_gwtoolbox"]:
                    if new_account_data["gwtoolbox_path"]:
                        remove_toolbox = themed_button("Remove##gwtoolbox_new", "danger")
                        imgui.same_line()
                        imgui.text_wrapped(f"- {new_account_data['gwtoolbox_path']}")
                        if remove_toolbox:
                            new_account_data["gwtoolbox_path"] = ""
                    if themed_button("Select GWToolbox DLL##new", "secondary"):
                        selected_dll = select_gwtoolbox_dll()
                        if selected_dll:
                            new_account_data["gwtoolbox_path"] = selected_dll
            elif key == "gmod_mods":
                _, new_account_data["inject_gmod"] = imgui.checkbox("Inject gMod##new_item", new_account_data["inject_gmod"])
                if new_account_data["inject_gmod"]:
                    imgui.text("gMod Mods:")
                    for i, mod in enumerate(list(new_account_data["gmod_mods"])):
                        remove_mod = themed_button(f"Remove##{i}_new", "danger")
                        imgui.same_line()
                        imgui.text_wrapped(f"- {mod}")
                        if remove_mod:
                            new_account_data["gmod_mods"].pop(i)
                            break
                    if themed_button("Add Mod##new", "secondary"):
                        mod_file = select_mod_file()
                        if mod_file and mod_file not in new_account_data["gmod_mods"]:
                            new_account_data["gmod_mods"].append(mod_file)
            elif key in ("inject_gmod", "inject_gwtoolbox", "resize_client", "top_left", "width", "height"):
                continue
            elif isinstance(new_account_data[key], bool):
                _, new_account_data[key] = imgui.checkbox(key.replace("_", " ").title() + "##new_item", new_account_data[key])
            elif isinstance(new_account_data[key], str):
                imgui.set_next_item_width(ui_responsive_input_width())
                _, new_account_data[key] = imgui.input_text(key.replace("_", " ").title() + "##new_item", new_account_data[key], 128)

        show_new_account_window_configuration()

        if themed_button("Add Account", "primary"):
            if credentials_are_locked():
                log_history.append("Credential Security - Unlock credentials before adding accounts.")
            else:
                new_account = Account(**new_account_data)
                selected_team.add_account(new_account)
                log_history.append(f"Added account: {new_account.character_name} to team: {selected_team.name}")
                team_manager.save_to_json(config_file)
                if new_account.inject_gmod:
                    launch_gw.create_modlist_for_gmod(new_account)
                reset_new_account_form()
        imgui.same_line()
        if themed_button("Clear Form", "secondary"):
            reset_new_account_form()

launcher_icon_applied = False
launcher_icon_attempts = 0
launcher_icon_handles = []


def get_resource_path(filename: str) -> str:
    search_dirs = []

    try:
        if getattr(sys, "frozen", False):
            search_dirs.append(os.path.dirname(sys.executable))
    except Exception:
        pass

    try:
        search_dirs.append(getattr(sys, "_MEIPASS", ""))
    except Exception:
        pass

    try:
        search_dirs.append(current_directory)
    except Exception:
        pass

    try:
        search_dirs.append(os.path.dirname(os.path.abspath(__file__)))
    except Exception:
        pass

    for base_dir in search_dirs:
        if not base_dir:
            continue
        candidate = os.path.abspath(os.path.join(base_dir, filename))
        if os.path.exists(candidate):
            return candidate

    return os.path.abspath(os.path.join(current_directory, filename))


def find_launcher_icon_source() -> str:
    for icon_name in ["python_icon.ico", "python_icon.jpg", "python_icon.jpeg", "python_icon.png"]:
        icon_path = get_resource_path(icon_name)
        if os.path.exists(icon_path):
            return icon_path
    return ""


def ensure_launcher_ico() -> str:
    source_path = find_launcher_icon_source()
    if not source_path:
        return ""

    ext = os.path.splitext(source_path)[1].lower()
    if ext == ".ico":
        return source_path

    ico_output = os.path.abspath(os.path.join(current_directory, "python_icon_runtime.ico"))
    try:
        from PIL import Image
        image = Image.open(source_path).convert("RGBA")
        image.save(
            ico_output,
            format="ICO",
            sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)],
        )
        return ico_output
    except Exception as e:
        return ""


def configure_hello_imgui_icon_path(runner_params, icon_path: str) -> bool:
    if not icon_path:
        return False

    app_window_params = getattr(runner_params, "app_window_params", None)
    if app_window_params is None:
        return False

    for attr_name in [
        "window_icon_path",
        "icon_path",
        "app_icon_path",
        "icon_filename",
        "window_icon_file",
    ]:
        try:
            if hasattr(app_window_params, attr_name):
                setattr(app_window_params, attr_name, icon_path)
                return True
        except Exception:
            pass

    return False


def find_launcher_window_hwnds():
    current_pid = os.getpid()
    found_hwnds = []

    def is_candidate_window(hwnd) -> bool:
        try:
            if not win32gui.IsWindowVisible(hwnd):
                return False
            _thread_id, pid = win32process.GetWindowThreadProcessId(hwnd)
            if int(pid) != int(current_pid):
                return False
            title = win32gui.GetWindowText(hwnd).strip()
            if not title:
                return False
            return True
        except Exception:
            return False

    def enum_callback(hwnd, _extra):
        if is_candidate_window(hwnd):
            found_hwnds.append(hwnd)

    try:
        win32gui.EnumWindows(enum_callback, None)
    except Exception:
        pass


    if not found_hwnds:
        def title_callback(hwnd, _extra):
            try:
                if not win32gui.IsWindowVisible(hwnd):
                    return
                title = win32gui.GetWindowText(hwnd).strip()
                if title == "Py4GW Launcher":
                    found_hwnds.append(hwnd)
            except Exception:
                pass

        try:
            win32gui.EnumWindows(title_callback, None)
        except Exception:
            pass

    return list(dict.fromkeys(found_hwnds))


def load_icon_handle(icon_path: str, size: int):
    IMAGE_ICON = 1
    LR_LOADFROMFILE = 0x00000010
    LR_DEFAULTCOLOR = 0x00000000

    handle = ctypes.windll.user32.LoadImageW(
        None,
        os.path.abspath(icon_path),
        IMAGE_ICON,
        int(size),
        int(size),
        LR_LOADFROMFILE | LR_DEFAULTCOLOR,
    )
    if handle:
        launcher_icon_handles.append(handle)
    return handle


def load_embedded_exe_icon_handles():
    try:
        exe_path = sys.executable if getattr(sys, "frozen", False) else ""
        if not exe_path or not os.path.exists(exe_path):
            return None, None, ""

        large_icons = (ctypes.wintypes.HICON * 1)()
        small_icons = (ctypes.wintypes.HICON * 1)()

        extracted = ctypes.windll.shell32.ExtractIconExW(
            os.path.abspath(exe_path),
            0,
            large_icons,
            small_icons,
            1,
        )

        if extracted <= 0:
            return None, None, ""

        big_icon = large_icons[0]
        small_icon = small_icons[0]

        if big_icon:
            launcher_icon_handles.append(big_icon)
        if small_icon:
            launcher_icon_handles.append(small_icon)

        return small_icon, big_icon, "EXE resource"
    except Exception as e:
        return None, None, ""


def _set_class_icon(hwnd, index: int, icon_handle) -> bool:
    if not icon_handle:
        return False

    try:
        icon_value = int(icon_handle)

        if ctypes.sizeof(ctypes.c_void_p) == 8:
            func = ctypes.windll.user32.SetClassLongPtrW
            func.argtypes = [ctypes.wintypes.HWND, ctypes.c_int, ctypes.c_void_p]
            func.restype = ctypes.c_void_p
            func(hwnd, index, ctypes.c_void_p(icon_value))
        else:
            func = ctypes.windll.user32.SetClassLongW
            func.argtypes = [ctypes.wintypes.HWND, ctypes.c_int, ctypes.c_long]
            func.restype = ctypes.c_long
            func(hwnd, index, ctypes.c_long(icon_value))

        return True
    except Exception:
        try:

            win32gui.SetClassLong(hwnd, index, int(icon_handle))
            return True
        except Exception:
            return False


def set_window_class_icon(hwnd, small_icon, big_icon):
    try:
        WM_SETICON = 0x0080
        ICON_SMALL = 0
        ICON_BIG = 1
        ICON_SMALL2 = 2
        GCLP_HICON = -14
        GCLP_HICONSM = -34

        if small_icon:
            ctypes.windll.user32.SendMessageW(hwnd, WM_SETICON, ICON_SMALL, small_icon)
            ctypes.windll.user32.SendMessageW(hwnd, WM_SETICON, ICON_SMALL2, small_icon)
            try:
                win32gui.SendMessage(hwnd, WM_SETICON, ICON_SMALL, int(small_icon))
                win32gui.SendMessage(hwnd, WM_SETICON, ICON_SMALL2, int(small_icon))
            except Exception:
                pass

        if big_icon:
            ctypes.windll.user32.SendMessageW(hwnd, WM_SETICON, ICON_BIG, big_icon)
            try:
                win32gui.SendMessage(hwnd, WM_SETICON, ICON_BIG, int(big_icon))
            except Exception:
                pass

        _set_class_icon(hwnd, GCLP_HICON, big_icon)
        _set_class_icon(hwnd, GCLP_HICONSM, small_icon)


        SWP_NOSIZE = 0x0001
        SWP_NOMOVE = 0x0002
        SWP_NOZORDER = 0x0004
        SWP_NOACTIVATE = 0x0010
        SWP_FRAMECHANGED = 0x0020

        RDW_INVALIDATE = 0x0001
        RDW_UPDATENOW = 0x0100
        RDW_FRAME = 0x0400
        RDW_ALLCHILDREN = 0x0080

        ctypes.windll.user32.SetWindowPos(
            hwnd,
            None,
            0,
            0,
            0,
            0,
            SWP_NOMOVE | SWP_NOSIZE | SWP_NOZORDER | SWP_NOACTIVATE | SWP_FRAMECHANGED,
        )
        ctypes.windll.user32.DrawMenuBar(hwnd)
        ctypes.windll.user32.RedrawWindow(
            hwnd,
            None,
            None,
            RDW_INVALIDATE | RDW_UPDATENOW | RDW_FRAME | RDW_ALLCHILDREN,
        )
        ctypes.windll.user32.UpdateWindow(hwnd)
        return True
    except Exception as e:
        return False


def apply_launcher_window_icon() -> bool:
    try:
        try:
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("py4gw.launcher.manager")
        except Exception:
            pass

        hwnds = find_launcher_window_hwnds()
        if not hwnds:
            return False


        small_icon, big_icon, icon_source_label = load_embedded_exe_icon_handles()


        if not small_icon and not big_icon:
            icon_path = ensure_launcher_ico()
            if not icon_path:
                return False

            try:
                small_size = int(ctypes.windll.user32.GetSystemMetrics(49)) or 16
                big_size = int(ctypes.windll.user32.GetSystemMetrics(11)) or 32
            except Exception:
                small_size = 16
                big_size = 32

            small_icon = load_icon_handle(icon_path, small_size)
            big_icon = load_icon_handle(icon_path, big_size)

            if not small_icon:
                small_icon = load_icon_handle(icon_path, 16)
            if not big_icon:
                big_icon = load_icon_handle(icon_path, 32)

            icon_source_label = os.path.basename(icon_path)

        if not small_icon and not big_icon:
            return False

        applied_count = 0
        for hwnd in hwnds:
            if set_window_class_icon(hwnd, small_icon, big_icon):
                applied_count += 1

        if applied_count > 0:
            return True

        return False
    except Exception as e:
        return False

def write_startup_error_log(context: str):
    try:
        import traceback
        error_path = os.path.join(current_directory, "Py4GW_Launcher_startup_error.log")
        with open(error_path, "w", encoding="utf-8") as f:
            f.write(str(context) + "\n\n")
            f.write(traceback.format_exc())
    except Exception:
        pass


def main() -> None:
    try:
        runner_params = hello_imgui.RunnerParams()
        runner_params.app_window_params.window_title = "Py4GW Launcher"
        runner_params.app_window_params.window_geometry.size = (400, 520) if is_compact_view else (980, 660)
        runner_params.imgui_window_params.default_imgui_window_type = hello_imgui.DefaultImGuiWindowType.provide_full_screen_dock_space


        runner_params.docking_params.docking_splits = create_docking_splits()


        configure_hello_imgui_icon_path(runner_params, "")


        runner_params.ini_filename = "Py4GW_Launcher.ini"
        log_history.append(f"Using Hello ImGui ini_filename: {runner_params.ini_filename}")


        check_and_handle_version_mismatch(runner_params.ini_filename)


        ensure_team_data_loaded()
        if gw_exe_update_enabled:
            start_gw_exe_update_status_check(force=False)

        def update_gui():
            global visible_windows, modern_style_applied, applied_ui_theme_mode
            global launcher_icon_applied, launcher_icon_attempts

            try:
                if applied_ui_theme_mode != ui_theme_mode:
                    apply_launcher_imgui_style(ui_theme_mode)
                    applied_ui_theme_mode = ui_theme_mode
                    modern_style_applied = True


                if launcher_icon_attempts < 180:
                    launcher_icon_attempts += 1
                    if apply_launcher_window_icon():
                        launcher_icon_applied = True

                if gw_exe_update_enabled:
                    start_gw_exe_update_status_check(force=False)

                runner_params.docking_params.dockable_windows = create_dockable_windows()
            except Exception as e:
                log_history.append(f"GUI render error: {str(e)}")
                write_startup_error_log("GUI render error")
                raise

        runner_params.callbacks.show_gui = update_gui

        hello_imgui.run(runner_params)
    except Exception as e:
        log_history.append(f"Application error: {str(e)}")
        write_startup_error_log("Application error")

if __name__ == "__main__":
    main()
