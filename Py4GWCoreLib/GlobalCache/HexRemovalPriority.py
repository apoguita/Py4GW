from __future__ import annotations

from dataclasses import dataclass, field
from enum import IntEnum
from functools import lru_cache

from Py4GWCoreLib.enums_src.GameData_enums import Profession

from ..py4gwcorelib_src.FrameCache import frame_cache


class HexRemovalPriority(IntEnum):
    NONE = 0
    LOW = 1
    MEDIUM = 2
    HIGH = 3


class TargetRole(IntEnum):
    MELEE = 1
    RANGED_MARTIAL = 2
    CASTER = 3


PROFESSION_ROLE: dict[int, TargetRole] = {
    int(Profession.Warrior): TargetRole.MELEE,
    int(Profession.Assassin): TargetRole.MELEE,
    int(Profession.Dervish): TargetRole.MELEE,
    int(Profession.Ranger): TargetRole.RANGED_MARTIAL,
    int(Profession.Paragon): TargetRole.RANGED_MARTIAL,
    int(Profession.Mesmer): TargetRole.CASTER,
    int(Profession.Necromancer): TargetRole.CASTER,
    int(Profession.Elementalist): TargetRole.CASTER,
    int(Profession.Monk): TargetRole.CASTER,
    int(Profession.Ritualist): TargetRole.CASTER,
}


DEFAULT_HEX_REMOVAL_PRIORITY: HexRemovalPriority = HexRemovalPriority.MEDIUM

# Below this remaining-ms threshold, hexes are skipped unless they are HIGH.
MIN_HEX_REMAINING_MS_TO_REMOVE: int = 2500

# Toggle for [HexRemoval] console logs.
HEX_REMOVAL_DEBUG: bool = True

# Per-(agent, hex) detection log throttle in ms (0 disables).
HEX_REMOVAL_DETECTION_THROTTLE_MS: int = 2000

_LAST_DETECTION_LOG: dict[tuple[int, int], int] = {}

# Per-zone role cache. GW1 reuses agent IDs across zones, so any cached
# (role, profession) is only valid within the map it was resolved on.
# Cleared lazily on the first call after Map.GetMapID() changes.
_role_cache: dict[int, tuple["TargetRole", int]] = {}
_role_cache_map_id: int = 0


@dataclass(frozen=True)
class HexRemovalEntry:
    """Per-role removal priority for one hex, with per-profession overrides."""

    caster: HexRemovalPriority
    ranged_martial: HexRemovalPriority
    melee: HexRemovalPriority
    by_profession: dict[int, HexRemovalPriority] = field(default_factory=dict)

    def for_target(self, role: TargetRole, profession_id: int) -> HexRemovalPriority:
        if profession_id in self.by_profession:
            return self.by_profession[profession_id]
        if role == TargetRole.MELEE:
            return self.melee
        if role == TargetRole.RANGED_MARTIAL:
            return self.ranged_martial
        return self.caster


# Compact aliases for _HEX_DEFAULTS_TABLE entries.
NONE = HexRemovalPriority.NONE
LOW  = HexRemovalPriority.LOW
MED  = HexRemovalPriority.MEDIUM
HIGH = HexRemovalPriority.HIGH

War    = int(Profession.Warrior)
Ranger = int(Profession.Ranger)
Monk   = int(Profession.Monk)
Necro  = int(Profession.Necromancer)
Mes    = int(Profession.Mesmer)
Ele    = int(Profession.Elementalist)
Asn    = int(Profession.Assassin)
Rit    = int(Profession.Ritualist)
Para   = int(Profession.Paragon)
Derv   = int(Profession.Dervish)

_HEX_DEFAULTS_TABLE: list[tuple] = [
    # Each row sets one hex's removal priority against three target roles:
    #   caster — Mes, Necro, Ele, Monk, Rit
    #   ranged — Ranger, Para
    #   melee  — War, Asn, Derv
    # Priorities: NONE = ignore / never remove on this role,
    #             LOW / MED / HIGH = increasing urgency to remove.
    # by_profession overrides the role priority for specific primary
    # professions (e.g. {Para: HIGH} → Paragons treat this hex as HIGH
    # regardless of their ranged role default). Use None when no profession
    # needs to deviate from the role priorities above.
    #
    # name                 caster, ranged, melee, by_profession (or None)
    # ─── Mesmer ──────────────────────────────────────────────────────
    ("Air_of_Disenchantment",  HIGH, NONE, NONE, None),
    ("Arcane_Conundrum",       HIGH, NONE, NONE, None),
    ("Arcane_Languor",         HIGH, MED,  LOW,  None),
    ("Backfire",               HIGH, NONE, NONE, None),
    ("Calculated_Risk",        NONE, NONE, NONE, None),
    ("Clumsiness",             NONE, LOW,  MED,  None),
    ("Confusing_Images",       HIGH, NONE, NONE, None),
    ("Conjure_Nightmare",      MED,  MED,  MED,  None),
    ("Conjure_Phantasm",       LOW,  LOW,  LOW,  None),
    ("Crippling_Anguish",      LOW,  MED,  HIGH, None),
    ("Diversion",              HIGH, MED,  MED,  None),
    ("Empathy",                NONE, HIGH, HIGH, None),
    ("Enchanter's_Conundrum",  HIGH, NONE, NONE, None),
    ("Ether_Lord",             MED,  MED,  MED,  None),
    ("Ether_Phantom",          MED,  LOW,  LOW,  None),
    ("Ethereal_Burden",        LOW,  LOW,  HIGH, None),
    ("Fevered_Dreams",         HIGH, HIGH, HIGH, None),
    ("Fragility",              LOW,  LOW,  LOW,  None),
    ("Frustration",            HIGH, LOW,  LOW,  None),
    ("Guilt",                  MED,  LOW,  LOW,  None),
    ("Ignorance",              HIGH, HIGH, HIGH, None),
    ("Illusion_of_Pain",       MED,  MED,  MED,  None),
    ("Images_of_Remorse",      LOW,  MED,  MED,  None),
    ("Imagined_Burden",        LOW,  MED,  HIGH, None),
    ("Ineptitude",             NONE, MED,  HIGH, {Para: HIGH}),
    ("Kitah's_Burden",         LOW,  MED,  HIGH, None),
    ("Migraine",               HIGH, MED,  LOW,  None),
    ("Mind_Wrack",             MED,  NONE, NONE, None),
    ("Mistrust",               MED,  NONE, NONE, None),
    ("Overload",               LOW,  LOW,  LOW,  None),
    ("Panic",                  HIGH, MED,  MED,  None),
    ("Phantom_Pain",           LOW,  LOW,  LOW,  None),
    ("Power_Flux",             MED,  LOW,  NONE, {Ranger: LOW, Para: MED, Monk: HIGH, Rit: HIGH, Necro: HIGH}),
    ("Power_Leech",            LOW,  NONE, NONE, None),
    ("Price_of_Pride",         MED,  MED,  MED,  None),
    ("Recurring_Insecurity",   LOW,  LOW,  LOW,  None),
    ("Shame",                  HIGH, NONE, NONE, {Derv: MED}),
    ("Shared_Burden",          MED,  MED,  HIGH, {Monk: HIGH, Rit: HIGH, Necro: HIGH}),
    ("Shrinking_Armor",        LOW,  LOW,  LOW,  None),
    ("Soothing_Images",        NONE, MED,  HIGH, {Para: HIGH, Asn: LOW}),
    ("Spirit_of_Failure",      NONE, MED,  HIGH, None),
    ("Spirit_Shackles",        NONE, HIGH, HIGH, None),
    ("Stolen_Speed",           HIGH, NONE, NONE, {Derv: MED}),
    ("Sum_of_All_Fears",       MED,  MED,  HIGH, None),
    ("Visions_of_Regret",      HIGH, HIGH, HIGH, None),
    ("Wandering_Eye",          LOW,  MED,  MED,  None),
    ("Wastrel's_Demise",       NONE, NONE, NONE, None),
    ("Wastrel's_Worry",        NONE, NONE, NONE, None),
    ("Web_of_Disruption",      MED,  NONE, NONE, None),

    # ─── Necromancer ─────────────────────────────────────────────────
    ("Atrophy",                MED,  MED,  MED,  {Monk: HIGH, Rit: HIGH, Necro: HIGH}),
    ("Barbs",                  LOW,  LOW,  LOW,  None),
    ("Blood_Bond",             NONE, NONE, NONE, None),
    ("Cacophony",              NONE, NONE, NONE, {War: MED, Para: HIGH}),
    ("Corrupt_Enchantment",    LOW,  LOW,  LOW,  None),
    ("Defile_Defenses",        NONE, LOW,  LOW,  {Ranger: MED, War: MED}),
    ("Defile_Flesh",           MED,  MED,  MED,  None),
    ("Depravity",              MED,  NONE, NONE, {Derv: MED}),
    ("Faintheartedness",       LOW,  HIGH, HIGH, None),
    ("Icy_Veins",              NONE, NONE, NONE, None),
    ("Insidious_Parasite",     NONE, MED,  HIGH, None),
    ("Life_Siphon",            NONE, NONE, NONE, None),
    ("Life_Transfer",          MED,  MED,  MED,  None),
    ("Lingering_Curse",        MED,  MED,  MED,  None),
    ("Malaise",                LOW,  LOW,  LOW,  {Monk: MED, Rit: MED, Necro: MED}),
    ("Malign_Intervention",    LOW,  LOW,  LOW,  None),
    ("Mark_of_Fury",           LOW,  LOW,  LOW,  None),
    ("Mark_of_Pain",           LOW,  LOW,  LOW,  None),
    ("Mark_of_Subversion",     MED,  NONE, NONE, None),
    ("Meekness",               NONE, MED,  HIGH, None),
    ("Parasitic_Bond",         NONE, NONE, NONE, None),
    ("Price_of_Failure",       NONE, MED,  HIGH, {Para: HIGH}),
    ("Putrid_Bile",            NONE, NONE, NONE, None),
    ("Reaper's_Mark",          NONE, NONE, NONE, None),
    ("Reckless_Haste",         NONE, MED,  MED,  {Para: HIGH, War: HIGH, Asn: HIGH}),
    ("Rigor_Mortis",           NONE, NONE, NONE, None),
    ("Rising_Bile",            LOW,  LOW,  LOW,  None),
    ("Shadow_of_Fear",         NONE, MED,  MED,  {Para: HIGH, War: HIGH}),
    ("Shivers_of_Dread",       MED,  LOW,  LOW,  None),
    ("Soul_Barbs",             LOW,  LOW,  LOW,  None),
    ("Soul_Bind",              MED,  MED,  MED,  None),
    ("Soul_Leech",             MED,  NONE, NONE, None),
    ("Spinal_Shivers",         MED,  LOW,  LOW,  None),
    ("Spiteful_Spirit",        LOW,  LOW,  MED,  {Ranger: MED}),
    ("Spoil_Victor",           LOW,  LOW,  LOW,  None),
    ("Suffering",              LOW,  LOW,  LOW,  None),
    ("Ulcerous_Lungs",         NONE, NONE, NONE, {Para: LOW, War: LOW}),
    ("Vile_Miasma",            LOW,  LOW,  LOW,  None),
    ("Vocal_Minority",         LOW,  HIGH, LOW,  {War: MED}),
    ("Wail_of_Doom",           LOW,  LOW,  LOW,  {Monk: MED, Necro: MED, Rit: MED}),
    ("Weaken_Knees",           LOW,  LOW,  LOW,  None),
    ("Wither",                 LOW,  LOW,  LOW,  {Monk: MED, Rit: MED, Necro: MED}),

    # ─── Elementalist ────────────────────────────────────────────────
    ("Ash_Blast",              NONE, NONE, NONE, None),
    ("Blurred_Vision",         NONE, HIGH, HIGH, None),
    ("Chilling_Winds",         NONE, NONE, NONE, None),
    ("Deep_Freeze",            LOW,  MED,  HIGH, None),
    ("Earthen_Shackles",       NONE, NONE, LOW,  None),
    ("Freezing_Gust",          NONE, NONE, LOW,  None),
    ("Frozen_Burst",           LOW,  LOW,  HIGH, None),
    ("Glimmering_Mark",        NONE, HIGH, HIGH, None),
    ("Grasping_Earth",         LOW,  LOW,  HIGH, None),
    ("Ice_Prison",             NONE, MED,  HIGH, None),
    ("Ice_Spikes",             LOW,  LOW,  HIGH, None),
    ("Icy_Shackles",           MED,  MED,  HIGH, None),
    ("Incendiary_Bonds",       LOW,  LOW,  LOW,  None),
    ("Lightning_Strike",       NONE, NONE, NONE, None),
    ("Lightning_Surge",        MED,  MED,  HIGH, None),
    ("Mark_of_Rodgort",        LOW,  LOW,  LOW,  None),
    ("Mind_Freeze",            MED,  MED,  HIGH, None),
    ("Mirror_of_Ice",          LOW,  LOW,  HIGH, None),
    ("Rust",                   LOW,  LOW,  LOW,  {Mes: MED}),
    ("Shard_Storm",            LOW,  LOW,  HIGH, None),
    ("Shatterstone",           NONE, NONE, NONE, None),
    ("Smoldering_Embers",      NONE, NONE, NONE, None),
    ("Teinai's_Prison",        LOW,  LOW,  HIGH, None),
    ("Winter's_Embrace",       LOW,  LOW,  HIGH, None),

    # ─── Monk ────────────────────────────────────────────────────────
    ("Amity",                  NONE, HIGH, HIGH, None),
    ("Defender's_Zeal",        NONE, LOW,  LOW,  None),
    ("Pacifism",               NONE, MED,  HIGH, {Para: HIGH}),
    ("Scourge_Enchantment",    LOW,  LOW,  LOW,  None),
    ("Scourge_Healing",        LOW,  LOW,  LOW,  None),
    ("Scourge_Sacrifice",      NONE, NONE, NONE, {Necro: HIGH}),

    # ─── Assassin ────────────────────────────────────────────────────
    ("Assassin's_Promise",     NONE, NONE, NONE, None),
    ("Augury_of_Death",        NONE, NONE, NONE, None),
    ("Dark_Prison",            NONE, NONE, MED,  None),
    ("Enduring_Toxin",         LOW,  LOW,  LOW,  None),
    ("Expose_Defenses",        LOW,  LOW,  LOW,  None),
    ("Hidden_Caltrops",        LOW,  LOW,  MED,  None),
    ("Mark_of_Death",          LOW,  LOW,  LOW,  None),
    ("Mark_of_Insecurity",     LOW,  LOW,  LOW,  None),
    ("Mark_of_Instability",    NONE, NONE, NONE, None),
    ("Mirrored_Stance",        NONE, NONE, NONE, None),
    ("Scorpion_Wire",          NONE, NONE, NONE, None),
    ("Seeping_Wound",          LOW,  LOW,  MED,  None),
    ("Shadow_Fang",            NONE, NONE, NONE, None),
    ("Shadow_Prison",          LOW,  LOW,  HIGH, None),
    ("Shadow_Shroud",          LOW,  LOW,  LOW,  None),
    ("Shadowy_Burden",         LOW,  LOW,  MED,  None),
    ("Shameful_Fear",          NONE, NONE, NONE, None),
    ("Shroud_of_Silence",      HIGH, LOW,  LOW,  {Derv: MED}),
    ("Siphon_Speed",           LOW,  LOW,  MED,  None),
    ("Siphon_Strength",        NONE, NONE, NONE, None),

    # ─── Ritualist ───────────────────────────────────────────────────
    ("Binding_Chains",         NONE, NONE, NONE, None),
    ("Dulled_Weapon",          NONE, LOW,  LOW,  None),
    ("Lamentation",            NONE, NONE, NONE, None),
    ("Painful_Bond",           LOW,  LOW,  LOW,  None),
    ("Renewing_Surge",         LOW,  LOW,  LOW,  None),
]

_HEX_DEFAULTS: dict[str, HexRemovalEntry] = {
    name: HexRemovalEntry(c, r, m, by_profession=bp or {})
    for name, c, r, m, bp in _HEX_DEFAULTS_TABLE
}


HEX_REMOVAL_PRIORITY: dict[int, HexRemovalEntry] = {}
# Reverse map for the GUI: skill_id → original table name (save-key consistency).
_NAME_BY_SKILL_ID: dict[int, str] = {}
_HEX_REMOVAL_PRIORITY_BUILT: bool = False


def _build_hex_removal_priority() -> None:
    """Resolve _HEX_DEFAULTS + user overrides into HEX_REMOVAL_PRIORITY.

    Lazy first call so module import doesn't require the GW skill database.
    Names that fail to resolve are skipped. User overrides come from the
    per-account JSONC config; if loading fails, falls back to defaults.
    """
    global _HEX_REMOVAL_PRIORITY_BUILT
    if _HEX_REMOVAL_PRIORITY_BUILT:
        return
    try:
        from Py4GWCoreLib import GLOBAL_CACHE
    except Exception:
        return

    # Lazy import to avoid CoreLib → HeroAI hard dep at module load time.
    overrides: dict[str, HexRemovalEntry] = {}
    try:
        from HeroAI.hex_removal_src.hex_removal_config import load_active_overrides
        overrides = load_active_overrides()
    except Exception:
        pass

    merged = {**_HEX_DEFAULTS, **overrides}
    for name, entry in merged.items():
        sid = GLOBAL_CACHE.Skill.GetID(name)
        if sid > 0:
            HEX_REMOVAL_PRIORITY[sid] = entry
            _NAME_BY_SKILL_ID[sid] = name
    _HEX_REMOVAL_PRIORITY_BUILT = True


def invalidate_hex_removal_priority() -> None:
    """Clear the resolved priority cache; next selector tick rebuilds.

    Called by HeroAI.hex_removal_config after the user edits via the GUI
    or imports a new config — picks up the change without a restart.
    """
    global _HEX_REMOVAL_PRIORITY_BUILT
    HEX_REMOVAL_PRIORITY.clear()
    _NAME_BY_SKILL_ID.clear()
    _HEX_REMOVAL_PRIORITY_BUILT = False


def get_skill_id_to_name() -> dict[int, str]:
    """skill_id → original hex name. Used by the GUI for save-key lookup."""
    if not _HEX_REMOVAL_PRIORITY_BUILT:
        _build_hex_removal_priority()
    return dict(_NAME_BY_SKILL_ID)


def get_target_role(agent_id: int) -> tuple[TargetRole, int]:
    """Return (role, primary_profession_id) for the given agent.

    Per-zone cached (see _role_cache). Unknown profession → CASTER.
    """
    global _role_cache_map_id
    try:
        from ..Map import Map
        current_map_id = int(Map.GetMapID() or 0)
    except Exception:
        current_map_id = 0
    if current_map_id != _role_cache_map_id:
        _role_cache.clear()
        _role_cache_map_id = current_map_id

    aid = int(agent_id)
    cached = _role_cache.get(aid)
    if cached is not None:
        return cached

    try:
        from ..Agent import Agent
        primary, _secondary = Agent.GetProfessions(aid)
        primary_int = int(primary or 0)
    except Exception:
        primary_int = 0
    role = PROFESSION_ROLE.get(primary_int, TargetRole.CASTER)
    result = (role, primary_int)
    _role_cache[aid] = result
    return result


def classify_hex_with_role(
    hex_skill_id: int,
    role: TargetRole,
    profession_id: int,
) -> HexRemovalPriority:
    """Removal priority for hex_skill_id against an already-resolved target.

    Lets callers resolve role once per agent and reuse it across many hexes,
    avoiding redundant Agent.GetProfessions calls. Unknown hexes → DEFAULT.
    """
    if not _HEX_REMOVAL_PRIORITY_BUILT:
        _build_hex_removal_priority()
    entry = HEX_REMOVAL_PRIORITY.get(int(hex_skill_id))
    if entry is None:
        return DEFAULT_HEX_REMOVAL_PRIORITY
    return entry.for_target(role, profession_id)


def classify_hex_for_removal(hex_skill_id: int, target_agent_id: int) -> HexRemovalPriority:
    """Return the removal priority of `hex_skill_id` against `target_agent_id`.

    Unknown hexes resolve to DEFAULT_HEX_REMOVAL_PRIORITY.
    """
    role, profession_id = get_target_role(int(target_agent_id))
    return classify_hex_with_role(hex_skill_id, role, profession_id)


def get_hex_skill_ids_on_agent(agent_id: int) -> list[int]:
    """Return hex skill IDs on agent_id (SHMEM, with local Effects fallback)."""
    try:
        from Py4GWCoreLib import GLOBAL_CACHE, Routines
    except Exception:
        return []

    skill_ids: list[int] = []
    try:
        shared_buffs = Routines.Checks.Agents.GetBuffs(int(agent_id))
        if shared_buffs:
            skill_ids = [int(b.SkillId) for b in shared_buffs]
        else:
            effects = list(GLOBAL_CACHE.Effects.GetBuffs(int(agent_id))) + list(
                GLOBAL_CACHE.Effects.GetEffects(int(agent_id))
            )
            skill_ids = [int(getattr(e, "skill_id", 0) or 0) for e in effects]
            skill_ids = [s for s in skill_ids if s > 0]
    except Exception:
        return []

    hexes: list[int] = []
    for sid in skill_ids:
        try:
            if GLOBAL_CACHE.Skill.Flags.IsHex(sid):
                hexes.append(sid)
        except Exception:
            continue
    return hexes


@frame_cache(category="HexRemoval", source_lib="ScoredHexedAllies")
def _get_scored_hexed_allies(max_distance: float = 4500.0) -> list[tuple[int, int]]:
    """Single hexed-ally scan, frame-cached on max_distance.

    Returns (agent_id, worst_priority) sorted by (priority desc,
    distance asc). HIGH/MED/LOW callers share this one scan per frame.
    """
    from Py4GWCoreLib import GLOBAL_CACHE, Routines
    from ..AgentArray import AgentArray
    from ..Agent import Agent
    from ..Player import Player

    player_pos = Player.GetXY()
    ally_array = AgentArray.GetAllyArray()
    ally_array = AgentArray.Filter.ByDistance(ally_array, player_pos, max_distance)
    ally_array = AgentArray.Filter.ByCondition(ally_array, lambda agent_id: Agent.IsAlive(agent_id))
    ally_array = AgentArray.Filter.ByCondition(ally_array, Routines.Party.IsPartyMember)

    scored: list[tuple[int, int, float]] = []
    for agent_id in ally_array:
        # Resolve role once per ally to avoid repeating the
        # Agent.GetProfessions C-call inside the per-hex loop.
        role, prof_id = get_target_role(agent_id)

        hex_iter: list[tuple[int, float | None]] = []
        try:
            shared_buffs = Routines.Checks.Agents.GetBuffs(agent_id)
            if shared_buffs:
                for buff in shared_buffs:
                    sid = int(buff.SkillId)
                    if sid <= 0:
                        continue
                    # Type==2 → EffectType (hex/effect with remaining_ms);
                    # Type==1 → BuffType (upkeep, no remaining time).
                    rem = float(buff.Remaining) if int(buff.Type) == 2 else None
                    hex_iter.append((sid, rem))
            else:
                local_effects = (
                    GLOBAL_CACHE.Effects.GetBuffs(agent_id)
                    + GLOBAL_CACHE.Effects.GetEffects(agent_id)
                )
                for effect in local_effects:
                    sid = int(getattr(effect, "skill_id", 0) or 0)
                    if sid <= 0:
                        continue
                    rem = getattr(effect, "time_remaining", None)
                    hex_iter.append((sid, float(rem) if rem is not None else None))
        except Exception:
            continue
        worst = 0
        # Lazy per-ally descriptor: only resolved when a log line actually fires
        # (debug on AND throttle/near-expiry passes), and at most once per ally
        # per frame instead of once per hex per log site.
        ally_descriptor: str | None = None
        for skill_id, time_remaining_ms in hex_iter:
            if skill_id <= 0:
                continue
            try:
                if not GLOBAL_CACHE.Skill.Flags.IsHex(skill_id):
                    continue
            except Exception:
                continue
            priority = int(classify_hex_with_role(skill_id, role, prof_id))

            if HEX_REMOVAL_DEBUG and should_log_detection(agent_id, skill_id):
                rem_str = (
                    f"remaining={int(time_remaining_ms)}ms"
                    if time_remaining_ms is not None
                    else "remaining=?"
                )
                if ally_descriptor is None:
                    ally_descriptor = agent_descriptor(agent_id)
                _log_hex(
                    f"detected: {_skill_name(skill_id)} on "
                    f"{ally_descriptor} "
                    f"priority={HexRemovalPriority(priority).name} {rem_str}"
                )

            # Skip near-expired hexes (BuffType upkeep has no remaining time → keep).
            if time_remaining_ms is not None and 0 < int(time_remaining_ms) <= MIN_HEX_REMAINING_MS_TO_REMOVE:
                # Don't log NONE-priority skips — they'd flood without signal.
                if HEX_REMOVAL_DEBUG and priority > 0:
                    if ally_descriptor is None:
                        ally_descriptor = agent_descriptor(agent_id)
                    _log_hex(
                        f"skipped near-expiry: {_skill_name(skill_id)} on "
                        f"{ally_descriptor} "
                        f"({int(time_remaining_ms)}ms remaining)"
                    )
                continue
            if priority > worst:
                worst = priority
        if worst <= 0:
            continue
        try:
            ax, ay = Agent.GetXY(agent_id)
            dx = ax - player_pos[0]
            dy = ay - player_pos[1]
            distance_sq = dx * dx + dy * dy
        except Exception:
            distance_sq = 0.0
        scored.append((int(agent_id), worst, float(distance_sq)))

    scored.sort(key=lambda item: (-item[1], item[2]))
    return [(aid, pri) for aid, pri, _dist in scored]


def get_hexed_ally_array(max_distance: float = 4500.0, min_priority: int = 1):
    """Return party members hexed with at least one hex of min_priority or higher.

    Sorted by (priority desc, distance asc). Frame-cached scan shared
    by HIGH/MED/LOW callers.
    """
    scored = _get_scored_hexed_allies(max_distance)
    threshold = int(min_priority)
    return [aid for aid, pri in scored if pri >= threshold]


def get_hexed_ally_for_removal(
    max_distance: float = 4500.0,
    reserve: bool = False,
    skill_id: int = 0,
    aftercast_delay: int = 250,
    min_priority: int = 1,
):
    """Pick a hexed ally for removal, honouring cross-hero hex-removal locks.

    `min_priority` is a `HexRemovalPriority` int (default `HexRemovalPriority.LOW = 1`).
    """
    from Py4GWCoreLib import Routines
    from ..Py4GWcorelib import Utils
    from ..Player import Player

    # Precondition gate: don't pick a target unless the removal skill
    # is castable, otherwise we'd POST a phantom lock that blocks other
    # clients while no cast fires.
    if reserve and skill_id:
        try:
            if not Routines.Checks.Skills.IsSkillIDReady(int(skill_id)):
                return 0
            if not Routines.Checks.Skills.HasEnoughEnergy(Player.GetAgentID(), int(skill_id)):
                return 0
        except Exception:
            # If the check itself raises, fall through to the selector.
            pass

    hexed_array = get_hexed_ally_array(max_distance, min_priority=min_priority)
    pre_lock_count = len(hexed_array)
    try:
        from .WhiteboardLocks import filter_unlocked_hex_targets
        hexed_array = filter_unlocked_hex_targets(hexed_array)
    except Exception:
        pass
    post_lock_count = len(hexed_array)
    selected = Utils.GetFirstFromArray(hexed_array)

    if HEX_REMOVAL_DEBUG:
        try:
            pri_name = HexRemovalPriority(int(min_priority)).name
        except Exception:
            pri_name = str(min_priority)
        skill_label = _skill_name(skill_id) if skill_id else "?"
        if selected:
            blocked = pre_lock_count - post_lock_count
            blocked_note = f" ({blocked} blocked by other clients)" if blocked > 0 else ""
            _log_hex(
                f"picked: {agent_descriptor(selected)} for {skill_label} "
                f"min_priority={pri_name}{blocked_note}"
            )
        else:
            if pre_lock_count > 0 and post_lock_count == 0:
                _log_hex(
                    f"no_target: {pre_lock_count} hexed ally/allies above min_priority={pri_name} "
                    f"all blocked by other clients (skill={skill_label})"
                )
            elif pre_lock_count == 0:
                # No qualifying hexed allies — stay silent.
                pass

    if selected and reserve:
        try:
            from .WhiteboardLocks import post_hex_removal_lock
            post_hex_removal_lock(selected, skill_id=skill_id, aftercast_delay=aftercast_delay)
        except Exception:
            pass
    return selected


def cast_hex_removal_and_track(
    build,
    skill_id: int,
    target_agent_id: int,
    aftercast_delay: int = 250,
):
    """Cast a hex-removal skill; on success, release the cross-hero lock early.

    Wraps build.CastSkillIDAndRestoreTarget with pre/post hex-count tracking.
    Early release lets another client step in for the next hex on this
    teammate without waiting for the natural lock expiry.
    """
    pre_hex_ids = get_hex_skill_ids_on_agent(target_agent_id)
    pre_count = len(pre_hex_ids)

    # Each name lookup wrapped individually so a single failure can't squash
    # the casting log — that line is the primary cast/reject signal.
    target_name = f"agent#{int(target_agent_id)}"
    try:
        from ..Agent import Agent
        resolved = (Agent.GetNameByID(int(target_agent_id)) or "").strip()
        if resolved:
            target_name = resolved
    except Exception as exc:
        _log_hex(f"name_lookup_error agent#{int(target_agent_id)}: {exc!r}")

    skill_name = f"skill#{int(skill_id)}"
    try:
        from Py4GWCoreLib import GLOBAL_CACHE
        resolved_skill = (GLOBAL_CACHE.Skill.GetName(int(skill_id)) or "").strip()
        if resolved_skill:
            skill_name = resolved_skill
    except Exception as exc:
        _log_hex(f"skill_name_lookup_error skill#{int(skill_id)}: {exc!r}")

    try:
        from Py4GWCoreLib import GLOBAL_CACHE
        hex_names = ", ".join(
            (GLOBAL_CACHE.Skill.GetName(int(hid)) or f"#{int(hid)}").strip()
            for hid in pre_hex_ids
        )
    except Exception:
        hex_names = ", ".join(f"#{int(hid)}" for hid in pre_hex_ids)

    _log_hex(
        f"casting {skill_name} on {target_name}(#{int(target_agent_id)}) "
        f"hexes=[{hex_names}]"
    )

    cast_result = yield from build.CastSkillIDAndRestoreTarget(
        skill_id=int(skill_id),
        target_agent_id=int(target_agent_id),
        log=False,
        aftercast_delay=int(aftercast_delay),
    )

    if cast_result:
        post_hex_ids = get_hex_skill_ids_on_agent(target_agent_id)
        if len(post_hex_ids) < pre_count:
            try:
                from .WhiteboardLocks import clear_hex_removal_lock
                clear_hex_removal_lock(int(target_agent_id))
            except Exception as exc:
                _log_hex(
                    f"lock_release_error agent#{int(target_agent_id)}: {exc!r}"
                )
            removed_ids = [hid for hid in pre_hex_ids if hid not in set(post_hex_ids)]
            try:
                from Py4GWCoreLib import GLOBAL_CACHE
                removed_names = ", ".join(
                    (GLOBAL_CACHE.Skill.GetName(int(hid)) or f"#{int(hid)}").strip()
                    for hid in removed_ids
                )
            except Exception:
                removed_names = ", ".join(f"#{int(hid)}" for hid in removed_ids)
            _log_hex(
                f"removed [{removed_names}] from {target_name}; lock released"
            )

    return cast_result


# ----- Debug logging helpers -----------------------------------------------


def _log_hex(msg: str) -> None:
    """Emit a [HexRemoval] console line gated by HEX_REMOVAL_DEBUG."""
    if not HEX_REMOVAL_DEBUG:
        return
    try:
        from Py4GWCoreLib import ConsoleLog
        import Py4GW
        ConsoleLog("HexRemoval", msg, Py4GW.Console.MessageType.Info)
    except Exception:
        pass


def _role_name(role: TargetRole) -> str:
    if role == TargetRole.MELEE:
        return "melee"
    if role == TargetRole.RANGED_MARTIAL:
        return "ranged"
    if role == TargetRole.CASTER:
        return "caster"
    return "?"


def _profession_name(profession_id: int) -> str:
    try:
        from ..enums_src.GameData_enums import Profession, Profession_Names
        prof = Profession(int(profession_id))
        return Profession_Names.get(prof, "?")
    except Exception:
        return "?"


@lru_cache(maxsize=512)
def _skill_name(skill_id: int) -> str:
    try:
        from Py4GWCoreLib import GLOBAL_CACHE
        return (GLOBAL_CACHE.Skill.GetName(int(skill_id)) or f"skill#{int(skill_id)}").strip()
    except Exception:
        return f"skill#{int(skill_id)}"


def _agent_name(agent_id: int) -> str:
    try:
        from ..Agent import Agent
        resolved = (Agent.GetName(int(agent_id)) or "").strip()
        if resolved:
            return resolved
    except Exception:
        pass
    return f"agent#{int(agent_id)}"


def agent_descriptor(agent_id: int) -> str:
    """Return 'Name(Profession, role)' descriptor for logs."""
    name = _agent_name(agent_id)
    role, prof_id = get_target_role(agent_id)
    return f"{name}({_profession_name(prof_id)}, {_role_name(role)})"


def should_log_detection(agent_id: int, hex_skill_id: int) -> bool:
    """True when (agent, hex) hasn't logged within HEX_REMOVAL_DETECTION_THROTTLE_MS."""
    if not HEX_REMOVAL_DEBUG:
        return False
    if HEX_REMOVAL_DETECTION_THROTTLE_MS <= 0:
        return True
    try:
        import Py4GW
        now = int(Py4GW.Game.get_tick_count64())
    except Exception:
        return False
    key = (int(agent_id), int(hex_skill_id))
    last = _LAST_DETECTION_LOG.get(key, 0)
    if now - last < HEX_REMOVAL_DETECTION_THROTTLE_MS:
        return False
    _LAST_DETECTION_LOG[key] = now
    return True
