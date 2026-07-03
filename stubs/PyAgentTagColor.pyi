"""Type stub for the embedded PyAgentTagColor module.

Agent name-tag color override. The DLL owns a detour on the native color
resolver (AvCharGetConsiderColor / FUN_007d9cf0); Python controls enable/disable
and the color rule store. Colors are ARGB 0xAARRGGBB (opaque red = 0xFFFF0000).
Allegiance ids: 1=Ally, 2=Neutral, 3=Enemy, 4=SpiritPet, 5=Minion, 6=NpcMinipet.
See docs/RE/name_tag_color_reverse_engineering.md.
"""

def enable() -> None:
    """Enable color overriding (the resolver detour applies matching rules)."""
    ...

def disable() -> None:
    """Disable color overriding (game default colors return)."""
    ...

def is_enabled() -> bool: ...

def is_hook_installed() -> bool:
    """True if the resolver detour was resolved and installed at DLL init."""
    ...

def set_agent_color(agent_id: int, argb: int) -> None:
    """Override one agent's name-tag color (ARGB). Highest precedence."""
    ...

def remove_agent_color(agent_id: int) -> bool: ...

def set_allegiance_color(allegiance: int, argb: int) -> None:
    """Override a whole allegiance category (1..6). Per-agent rules win."""
    ...

def remove_allegiance_color(allegiance: int) -> bool: ...

def clear_rules() -> None:
    """Drop all overrides (agents revert to game defaults)."""
    ...

def get_agent_rules() -> dict[int, int]:
    """Map agent_id -> ARGB for the current per-agent overrides."""
    ...

def get_allegiance_rules() -> dict[int, int]:
    """Map allegiance -> ARGB for the current per-allegiance overrides."""
    ...

def read_consider_color(agent_id: int) -> int:
    """The color the game currently computes for an agent (ARGB), read via the
    original resolver. Unaffected by overrides. 0 if unavailable."""
    ...

def get_diagnostics() -> dict[str, object]:
    """Counters: initialized, hook_installed, enabled, resolver_calls_seen,
    agent_rule_hits, allegiance_rule_hits, last_agent_id, last_color."""
    ...

def reset_diagnostics() -> None: ...
