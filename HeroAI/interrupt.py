"""Interrupt feasibility helper for HeroAI.

Owns the per-frame cast sampler, the interrupt classifier (driven by
``SkillNature.Interrupt`` tags in ``HeroAI/custom_skill_src/``), the
``is_interrupt_feasible`` decision helper, and post-fire outcome logging.

Consumed by two evaluators:
* ``HeroAI/combat.py`` ``AreCastConditionsMet`` — data-driven (unmatched bar).
* ``Py4GWCoreLib/BuildMgr.py`` ``CastSkillID`` — matched-build choke point.
"""

from __future__ import annotations

from typing import Iterable

import Py4GW
from Py4GWCoreLib import (
    GLOBAL_CACHE,
    Agent,
    AgentArray,
    Effects,
    Player,
    Range,
    Routines,
    Utils,
)

from .types import SkillNature


# Logs every decision to the console while True. Flip off when validated.
INTERRUPT_DEBUG: bool = False

# Safety multiplier on measured ping.
_PING_SAFETY = 1.2

# Reaction margin on top of cast + ping buffer.
_DEFAULT_REACTION_MARGIN_MS = 50

# Sampler entry age-out. Exceeds the longest in-game activation time.
_OBSERVATION_MAX_AGE_MS = 10_000

# Grace past nominal activation before declaring FAIL — covers aftercast.
_OUTCOME_FAIL_GRACE_MS = 500

# ---------------------------------------------------------------------------
# Non-Fast-Casting cast-time modifiers.
#
# Applied on top of apply_fast_casting() as a multiplier. FC itself is exempt
# from the -25%/+150% caps — these tables only cover the non-FC side
# (consumables, self-buffs, spirit auras, slowing hexes), and the raw product
# of active modifiers gets clamped to [_NON_FC_MIN_MULT, _NON_FC_MAX_MULT].
# ---------------------------------------------------------------------------

# Consumables — stack MULTIPLICATIVELY with each other per user guidance.
# (skill_id_name, multiplier)
_CONSUMABLE_CAST_MODS: list[tuple[str, float]] = [
    ("Blue_Rock_Candy_Rush", 0.80),    # 20% faster
    ("Green_Rock_Candy_Rush", 0.85),   # 15% faster
    ("Red_Rock_Candy_Rush", 0.75),     # 25% faster
    ("Essence_of_Celerity_item_effect", 0.80),  # 20% faster
    ("Pie_Induced_Ecstasy", 0.85),     # Slice of Pumpkin Pie buff — 15% faster
]

# Self-enchantments that only affect SPELLS (not signets, not attack skills).
# Gated on GLOBAL_CACHE.Skill.Flags.IsSpell(our_skill_id).
_SPELL_ONLY_SPEEDUPS: list[tuple[str, float]] = [
    ("Mindbender", 0.80),              # 20% faster, PvE-only
]

# Slowing hexes that affect ALL skill types. Take MAX (they don't stack).
_SLOWING_HEXES_ALL: list[tuple[str, float]] = [
    ("Migraine", 2.0),
    ("Snaring_Web", 2.0),
]

# Slowing hexes that only affect SPELLS. Take MAX across spell+all hexes.
_SLOWING_HEXES_SPELLS: list[tuple[str, float]] = [
    ("Frustration", 2.0),
    ("Confusing_Images", 2.0),
    ("Arcane_Conundrum", 2.0),
    ("Enchanters_Conundrum", 2.0),
    ("Stolen_Speed", 2.0),
    ("Shared_Burden", 1.5),
    ("Sum_of_All_Fears", 1.33),
]

# Caps on the non-FC multiplier: -25% floor, +150% ceiling of original.
_NON_FC_MIN_MULT: float = 0.75
_NON_FC_MAX_MULT: float = 2.5

# --- Attack-skill interrupt parameters (ranger bow + warrior/sin melee) ---
# Attack skills use the attack-speed mechanic, not activation-time. The
# spell-side modifier tables don't apply — only AttackSpeedModifier and
# projectile flight time.

# Projectile flight ms per gw of distance. Py4GW doesn't expose bow subtype
# (Recurve/Longbow/Shortbow/Hornbow/Flatbow), so every bow is treated as
# Recurve — the most common subtype on hero bars.
_BOW_FLIGHT_MS_PER_GW: float = 0.42

# Touch range for melee swings. Bow attacks use Range.Spellcast (1248gw).
_MELEE_TOUCH_RANGE_GW: int = 144

# Lazy cache — populated on first use so we don't hit the game API at import.
_SKILL_ID_CACHE: dict[str, int] = {}

_LOG_PREFIX = "HeroAI.interrupt"


def _now_ms() -> int:
    return int(Py4GW.Game.get_tick_count64())


def _log(message: str, level: str = "Debug") -> None:
    # Master switch: all interrupt-module output is gated on INTERRUPT_DEBUG.
    if not INTERRUPT_DEBUG:
        return
    msg_type = {
        "Debug": Py4GW.Console.MessageType.Debug,
        "Info": Py4GW.Console.MessageType.Info,
        "Warning": Py4GW.Console.MessageType.Warning,
    }.get(level, Py4GW.Console.MessageType.Debug)
    try:
        Py4GW.Console.Log(_LOG_PREFIX, message, msg_type)
    except Exception:
        # Console may not be available during very early import; swallow.
        pass


# --- Classifier ---
# Reuses HeroAI/custom_skill_src/ Nature tags as source of truth.

_INTERRUPT_SKILL_IDS: set[int] | None = None


def _ensure_registry() -> set[int]:
    """Build the classified-interrupt set once, lazily.

    Deferred to first call so ``HeroAI.combat`` has finished importing.
    """
    global _INTERRUPT_SKILL_IDS
    if _INTERRUPT_SKILL_IDS is not None:
        return _INTERRUPT_SKILL_IDS

    try:
        from .combat import custom_skill_data_handler  # lazy to avoid cycles
    except Exception as exc:
        _log(f"registry bootstrap failed: {exc}", "Warning")
        _INTERRUPT_SKILL_IDS = set()
        return _INTERRUPT_SKILL_IDS

    # skill_data is a pre-sized list; the index IS the skill_id.
    ids: set[int] = set()
    try:
        for skill_id, cs in enumerate(custom_skill_data_handler.skill_data):
            if cs.Nature == SkillNature.Interrupt.value:
                ids.add(skill_id)
    except Exception as exc:
        _log(f"registry scan failed: {exc}", "Warning")

    _INTERRUPT_SKILL_IDS = ids
    _log(f"registry populated: {len(ids)} interrupt skills classified", "Info")
    return _INTERRUPT_SKILL_IDS


def is_classified_as_interrupt(skill_id: int) -> bool:
    """True if ``skill_id`` is tagged ``SkillNature.Interrupt``."""
    if not skill_id:
        return False
    return skill_id in _ensure_registry()


def register_interrupt_skills(skill_ids: Iterable[int]) -> None:
    """Manual registry override — for tests/whitelisting. Production picks
    up ``custom_skill_src/`` tags automatically."""
    _ensure_registry().update(int(s) for s in skill_ids if s)


# --- CastObserver: per-frame sampler ---


class CastObserver:
    """Tracks every observed enemy cast within compass radius every frame.

    Key: ``(agent_id, casting_skill_id)`` → value: first_seen_ms.
    ``elapsed_ms`` returns ``now - first_seen`` or ``None`` when unknown.
    """

    def __init__(self) -> None:
        self._observations: dict[tuple[int, int], int] = {}
        self._pending_outcomes: list[tuple[int, int, int, int, int]] = []
        # (target_id, enemy_skill_id, our_skill_id, fired_at_ms, enemy_total_ms)

    # --- Public queries -----------------------------------------------------

    def elapsed_ms(self, agent_id: int, skill_id: int) -> int | None:
        ts = self._observations.get((agent_id, skill_id))
        if ts is None:
            return None
        return _now_ms() - ts

    # --- Per-frame tick -----------------------------------------------------

    def tick(self) -> None:
        try:
            self._sweep_observations()
            self._sweep_pending_outcomes()
        except Exception as exc:
            _log(f"tick error: {exc}", "Warning")

    def _sweep_observations(self) -> None:
        now = _now_ms()

        try:
            player_pos = Player.GetXY()
            enemies = AgentArray.Filter.ByDistance(
                AgentArray.GetEnemyArray(),
                player_pos,
                Range.SafeCompass.value,
            )
        except Exception:
            enemies = []

        live_keys: set[tuple[int, int]] = set()

        for agent_id in enemies:
            try:
                if not Agent.IsCasting(agent_id):
                    self._drop_agent(agent_id)
                    continue
                sid = Agent.GetCastingSkillID(agent_id)
            except Exception:
                continue

            if not sid:
                self._drop_agent(agent_id)
                continue

            key = (agent_id, sid)
            if key not in self._observations:
                self._drop_agent(agent_id)
                self._observations[key] = now
            live_keys.add(key)

        stale_cutoff = now - _OBSERVATION_MAX_AGE_MS
        to_remove = [
            key for key, ts in self._observations.items()
            if key not in live_keys and ts < stale_cutoff
        ]
        for key in to_remove:
            self._observations.pop(key, None)

    def _drop_agent(self, agent_id: int) -> None:
        keys = [k for k in self._observations if k[0] == agent_id]
        for k in keys:
            self._observations.pop(k, None)

    # --- Outcome logging ----------------------------------------------------

    def queue_outcome(
        self,
        target_id: int,
        enemy_skill_id: int,
        our_skill_id: int,
        enemy_total_ms: int,
    ) -> None:
        if not target_id or not enemy_skill_id or not our_skill_id:
            return
        self._pending_outcomes.append(
            (target_id, enemy_skill_id, our_skill_id, _now_ms(), enemy_total_ms)
        )

    def _sweep_pending_outcomes(self) -> None:
        if not self._pending_outcomes:
            return

        now = _now_ms()
        keep: list[tuple[int, int, int, int, int]] = []

        for record in self._pending_outcomes:
            target, enemy_skill, our_skill, fired_at, enemy_total = record

            # SUCCESS: target no longer casting that skill in the sampler.
            if self.elapsed_ms(target, enemy_skill) is None:
                self._log_outcome("SUCCESS", target, enemy_skill, our_skill, now - fired_at)
                continue

            # SUCCESS: target is still casting, but a different skill now.
            try:
                current_sid = (
                    Agent.GetCastingSkillID(target) if Agent.IsCasting(target) else 0
                )
            except Exception:
                current_sid = 0
            if current_sid and current_sid != enemy_skill:
                self._log_outcome("SUCCESS", target, enemy_skill, our_skill, now - fired_at)
                continue

            # FAIL: the enemy cast has had time to complete past its activation.
            if now - fired_at > enemy_total + _OUTCOME_FAIL_GRACE_MS:
                self._log_outcome("FAIL", target, enemy_skill, our_skill, now - fired_at)
                continue

            keep.append(record)

        self._pending_outcomes = keep

    def _log_outcome(
        self,
        verdict: str,
        target_id: int,
        enemy_skill_id: int,
        our_skill_id: int,
        elapsed_ms: int,
    ) -> None:
        our_name = _safe_skill_name(our_skill_id)
        target_name = _safe_agent_name(target_id)
        enemy_skill_name = _safe_skill_name(enemy_skill_id)
        _log(
            f"[outcome] {verdict} our={our_name}({our_skill_id}) "
            f"target={target_name}({target_id}) enemy_skill="
            f"{enemy_skill_name}({enemy_skill_id}) elapsed={elapsed_ms}ms",
            "Info",
        )


cast_observer = CastObserver()


# --- Shared helpers ---


_PING_HANDLER = Py4GW.PingHandler()


def _get_player_fast_casting_level() -> int:
    """Read the player's Fast Casting attribute level, 0 if absent."""
    try:
        player_id = Player.GetAgentID()
        for attribute in Agent.GetAttributes(player_id):
            if attribute.GetName() == "Fast Casting":
                return int(attribute.level)
    except Exception:
        pass
    return 0


def _safe_skill_name(skill_id: int) -> str:
    try:
        return str(GLOBAL_CACHE.Skill.GetName(skill_id) or "").strip() or "?"
    except Exception:
        return "?"


def _safe_agent_name(agent_id: int) -> str:
    try:
        return str(Agent.GetNameByID(agent_id) or "").strip() or "?"
    except Exception:
        return "?"


def _resolve_skill_id(name: str) -> int:
    """Cached skill_id lookup by name. Returns 0 when unknown.

    Logs a one-shot warning on unresolved names so typos in modifier
    tables surface without console spam.
    """
    if name in _SKILL_ID_CACHE:
        return _SKILL_ID_CACHE[name]
    sid = 0
    try:
        sid = int(GLOBAL_CACHE.Skill.GetID(name) or 0)
    except Exception:
        sid = 0
    _SKILL_ID_CACHE[name] = sid
    if sid == 0:
        _log(f"unresolved modifier skill_id: '{name}'", "Warning")
    return sid


def _compute_modifier_multiplier(
    our_skill_id: int,
) -> tuple[float, float, list[str]]:
    """Stacked non-FC cast-time multiplier.

    Returns ``(raw, capped, applied)`` — caller multiplies the
    FC-reduced activation by ``capped``. FC is exempt from the cap;
    only the non-FC product is clamped to ``[_NON_FC_MIN_MULT,
    _NON_FC_MAX_MULT]``. ``applied`` is a list of display strings
    for logging.
    """
    try:
        player_id = Player.GetAgentID()
    except Exception:
        return 1.0, 1.0, []

    try:
        is_our_spell = bool(GLOBAL_CACHE.Skill.Flags.IsSpell(our_skill_id))
    except Exception:
        is_our_spell = False

    applied: list[str] = []
    raw = 1.0

    # Consumables — stack multiplicatively.
    for name, mult in _CONSUMABLE_CAST_MODS:
        sid = _resolve_skill_id(name)
        if not sid:
            continue
        try:
            present = Effects.HasEffect(player_id, sid)
        except Exception:
            present = False
        if present:
            raw *= mult
            applied.append(f"{name} (x{mult:.2f})")

    # Self-enchantments that only affect spells.
    if is_our_spell:
        for name, mult in _SPELL_ONLY_SPEEDUPS:
            sid = _resolve_skill_id(name)
            if not sid:
                continue
            try:
                present = Effects.HasEffect(player_id, sid)
            except Exception:
                present = False
            if present:
                raw *= mult
                applied.append(f"{name} (x{mult:.2f})")

    # Slowing hexes — take MAX across all-skill + spell-only (hexes don't stack).
    hex_candidates: list[tuple[str, float]] = list(_SLOWING_HEXES_ALL)
    if is_our_spell:
        hex_candidates.extend(_SLOWING_HEXES_SPELLS)

    strongest_hex_mult = 1.0
    strongest_hex_name = ""
    for name, mult in hex_candidates:
        sid = _resolve_skill_id(name)
        if not sid:
            continue
        try:
            present = Effects.HasEffect(player_id, sid)
        except Exception:
            present = False
        if present and mult > strongest_hex_mult:
            strongest_hex_mult = mult
            strongest_hex_name = name
    if strongest_hex_mult > 1.0:
        raw *= strongest_hex_mult
        applied.append(f"{strongest_hex_name} (x{strongest_hex_mult:.2f})")

    capped = max(_NON_FC_MIN_MULT, min(_NON_FC_MAX_MULT, raw))
    return raw, capped, applied


def _is_attack_skill(skill_id: int) -> bool:
    """True if classified as Attack — bypasses FC and the spell modifier
    table; uses the attack-speed mechanic instead."""
    if not skill_id:
        return False
    try:
        return bool(GLOBAL_CACHE.Skill.Flags.IsAttack(skill_id))
    except Exception:
        return False


def _max_interrupt_range_gw(our_skill_id: int) -> tuple[int, str]:
    """Return (max_range_gw, label) for the range gate.

    - Spell / signet:    spellcast (1248gw)
    - Attack + bow:      spellcast (1248gw)
    - Attack + melee:    touch (144gw)

    Melee swings can't connect past 144gw regardless of timing budget.
    """
    if not _is_attack_skill(our_skill_id):
        return int(Range.Spellcast.value), "spellcast"

    try:
        player_id = Player.GetAgentID()
        weapon_type, _ = Agent.GetWeaponType(player_id)
    except Exception:
        weapon_type = 0

    if weapon_type == 1:  # Weapon.Bow
        return int(Range.Spellcast.value), "spellcast"
    return _MELEE_TOUCH_RANGE_GW, "melee touch"


def _calc_attack_skill_activation_ms(
    our_skill_id: int,
    distance_gw: int,
    player_id: int,
) -> tuple[int, int, int, float, list[str]]:
    """Compute time-to-impact for an attack-skill interrupt.

    Returns ``(total_ms, release_ms, flight_ms, ias_modifier, breakdown)``.

    Half-interval rule: attack skills release/connect at *half* the stated
    activation time (the remaining half is the return-to-neutral tail —
    irrelevant for interrupt feasibility). So ``release_ms = stated/2``.

    Ranged adds ``flight_ms`` for projectile travel; ``total_ms = release +
    flight``. IAS scales the interval (Frenzy = 0.66, etc).
    """
    # Stated activation; fall back to weapon interval when the skill has
    # no explicit time (uses first half of the next attack interval).
    try:
        stated_s = GLOBAL_CACHE.Skill.Data.GetActivation(our_skill_id) or 0.0
    except Exception:
        stated_s = 0.0
    if stated_s <= 0:
        try:
            stated_s = float(Agent.GetWeaponAttackSpeed(player_id) or 0.0)
        except Exception:
            stated_s = 0.0

    stated_ms = int(stated_s * 1000)
    half_interval_ms = stated_ms // 2

    # IAS modifier scales the interval. Defaults to 1.0 if the API misbehaves.
    try:
        ias_modifier = float(Agent.GetAttackSpeedModifier(player_id) or 1.0)
    except Exception:
        ias_modifier = 1.0
    if ias_modifier <= 0:
        ias_modifier = 1.0

    release_ms = int(half_interval_ms * ias_modifier)

    # Flight time only for bows. Bow subtype isn't exposed by Py4GW —
    # every bow is treated as Recurve (0.42 ms/gw).
    flight_ms = 0
    weapon_kind = "non-bow"
    try:
        weapon_type, _ = Agent.GetWeaponType(player_id)
    except Exception:
        weapon_type = 0
    if weapon_type == 1:  # Weapon.Bow
        flight_ms = int(distance_gw * _BOW_FLIGHT_MS_PER_GW)
        weapon_kind = "bow (recurve assumed)"

    total_ms = release_ms + flight_ms

    breakdown = [
        f"half_interval={half_interval_ms}ms",
        f"IAS=x{ias_modifier:.2f}",
        f"release={release_ms}ms",
    ]
    if flight_ms > 0:
        breakdown.append(f"flight={flight_ms}ms ({weapon_kind})")
        breakdown.append(f"impact={total_ms}ms")

    return total_ms, release_ms, flight_ms, ias_modifier, breakdown


def _queue_outcome(target_id: int, enemy_skill_id: int, our_skill_id: int) -> None:
    """Convenience wrapper used by call-sites after a feasibility check wins."""
    try:
        enemy_total_s = GLOBAL_CACHE.Skill.Data.GetActivation(enemy_skill_id) or 0.0
    except Exception:
        enemy_total_s = 0.0
    cast_observer.queue_outcome(
        target_id, enemy_skill_id, our_skill_id, int(enemy_total_s * 1000)
    )


# --- is_interrupt_feasible: the decision helper ---


def is_interrupt_feasible(
    target_agent_id: int,
    our_skill_id: int,
    fast_casting_level: int,
    ping_ms: int,
    *,
    reaction_margin_ms: int = _DEFAULT_REACTION_MARGIN_MS,
    debug: bool | None = None,
) -> bool:
    """True if our interrupt can land before the target's cast completes."""
    if debug is None:
        debug = INTERRUPT_DEBUG

    # Early-exit cases fire frequently (per-enemy scans). Skip-logging
    # is reserved for actionable cases (range, instant, etc).
    our_name = _safe_skill_name(our_skill_id)

    if not target_agent_id:
        return False

    try:
        if not Agent.IsCasting(target_agent_id):
            return False
    except Exception:
        return False

    # --- Range gate ---
    try:
        player_pos = Player.GetXY()
        target_pos = Agent.GetXY(target_agent_id)
        distance = int(Utils.Distance(player_pos, target_pos))
    except Exception:
        distance = 0

    target_name = _safe_agent_name(target_agent_id)

    # Cap depends on skill type + wielded weapon (melee=144gw, else=spellcast).
    max_range_gw, range_label = _max_interrupt_range_gw(our_skill_id)

    if distance > max_range_gw:
        if debug:
            _log(
                f"[rupt] Our '{our_name}', {target_name} → SKIP: out of {range_label} range "
                f"(distance={distance}gw, max={max_range_gw}gw)"
            )
        return False

    # --- Target skill info ---
    try:
        enemy_skill_id = Agent.GetCastingSkillID(target_agent_id)
    except Exception:
        return False

    if not enemy_skill_id:
        return False

    try:
        enemy_total_s = GLOBAL_CACHE.Skill.Data.GetActivation(enemy_skill_id) or 0.0
    except Exception:
        enemy_total_s = 0.0

    enemy_skill_name = _safe_skill_name(enemy_skill_id)

    if enemy_total_s <= 0:
        if debug:
            _log(
                f"[rupt] Our '{our_name}', {target_name} is casting '{enemy_skill_name}' "
                f"→ SKIP: target skill is instant (nothing to interrupt)"
            )
        return False

    # --- Elapsed / remaining (from sampler) ---
    elapsed_ms = cast_observer.elapsed_ms(target_agent_id, enemy_skill_id) or 0
    enemy_total_ms = int(enemy_total_s * 1000)
    remaining_ms = max(0, enemy_total_ms - elapsed_ms)

    # --- Our activation: branch on skill type ---
    # Attack skills use attack-speed mechanics (IAS + half-interval +
    # flight), not FC + spell-side modifiers.
    is_attack_path = _is_attack_skill(our_skill_id)

    # Defaults (kept stable across both branches for debug log).
    our_activation_ms_after_fc: int = 0
    raw_mult: float = 1.0
    capped_mult: float = 1.0
    applied_modifiers: list[str] = []
    attack_breakdown: list[str] = []
    attack_release_ms: int = 0
    attack_flight_ms: int = 0
    attack_ias_modifier: float = 1.0

    if is_attack_path:
        try:
            player_id = Player.GetAgentID()
        except Exception:
            player_id = 0
        (
            our_activation_ms,
            attack_release_ms,
            attack_flight_ms,
            attack_ias_modifier,
            attack_breakdown,
        ) = _calc_attack_skill_activation_ms(our_skill_id, distance, player_id)
    else:
        try:
            our_activation_s, _ = Routines.Checks.Skills.apply_fast_casting(
                our_skill_id, fast_casting_level
            )
        except Exception:
            try:
                our_activation_s = GLOBAL_CACHE.Skill.Data.GetActivation(our_skill_id) or 0.0
            except Exception:
                our_activation_s = 0.0
        our_activation_ms_after_fc = int(our_activation_s * 1000)

        # Capped non-FC multiplier (consumables, spirits, hexes). FC is
        # exempt from the cap; only the non-FC product is clamped.
        raw_mult, capped_mult, applied_modifiers = _compute_modifier_multiplier(our_skill_id)
        our_activation_ms = int(our_activation_ms_after_fc * capped_mult)

    ping_buffer_ms = int(ping_ms * _PING_SAFETY)
    budget_ms = our_activation_ms + ping_buffer_ms + reaction_margin_ms
    feasible = remaining_ms >= budget_ms

    if debug:
        verdict = "FEASIBLE" if feasible else "SKIP: cast too far along"
        _log(
            f"[rupt] Our '{our_name}', {target_name} is casting '{enemy_skill_name}' "
            f"→ {verdict}"
        )
        _log(
            f"       distance={distance}gw ({range_label} max {max_range_gw}gw)"
        )
        if is_attack_path:
            _log(
                f"       attack: {', '.join(attack_breakdown)}"
            )
            _log(
                f"       target_remaining={remaining_ms}ms vs our_budget={budget_ms}ms  "
                f"[cast={our_activation_ms}ms "
                f"(release={attack_release_ms}+flight={attack_flight_ms}, "
                f"IAS x{attack_ias_modifier:.2f}) "
                f"+ ping={ping_ms}ms*1.2={ping_buffer_ms}ms + margin={reaction_margin_ms}ms]"
            )
        else:
            if applied_modifiers:
                if abs(raw_mult - capped_mult) > 1e-4:
                    mods_summary = f"raw x{raw_mult:.2f}, capped x{capped_mult:.2f}"
                else:
                    mods_summary = f"x{capped_mult:.2f}"
                _log(
                    f"       modifiers: {', '.join(applied_modifiers)} -> {mods_summary}"
                )
            _log(
                f"       target_remaining={remaining_ms}ms vs our_budget={budget_ms}ms  "
                f"[cast={our_activation_ms}ms (FC {fast_casting_level}, mods x{capped_mult:.2f}) "
                f"+ ping={ping_ms}ms*1.2={ping_buffer_ms}ms + margin={reaction_margin_ms}ms]"
            )

    return feasible


# --- Per-frame tick registration ---
# Sampler runs independent of either evaluator path.

_CALLBACK_NAME = "HeroAI.Interrupt.Tick"


def _register_tick_callback() -> None:
    try:
        import PyCallback

        PyCallback.PyCallback.Register(
            _CALLBACK_NAME,
            PyCallback.Phase.Data,
            cast_observer.tick,
            priority=7,
            context=PyCallback.Context.Draw,
        )
        _log("sampler tick registered", "Info")
    except Exception as exc:
        _log(f"sampler tick registration failed: {exc}", "Warning")


_register_tick_callback()
