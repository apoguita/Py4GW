"""Underworld Dhuum-phase domain helpers.

Everything that is shared across multiple skill utilities but is *not*
skill-cast logic:

  - UW Chest detection          — fight-over sentinel used by all utilities
  - Skill name resolution       — locale-tolerant CustomSkill factory
  - Same-party-and-map check    — filters shared-memory accounts to the
                                   current instance
  - Spirit Form multibox query  — counts / lists soul-split accounts
  - Morale / death-penalty data — reads morale from shared memory
"""

from Py4GWCoreLib import Agent, AgentArray, GLOBAL_CACHE, Player, Utils
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill import CustomSkill


# ── Spirit Form ────────────────────────────────────────────────────────────────

SPIRIT_FORM_SKILL_ID: int = 3134


# ── UW Chest ──────────────────────────────────────────────────────────────────

_UW_CHEST_POS = (-13987, 17291)
_UW_CHEST_RADIUS = 3000.0
_UW_CHEST_NAME_FRAGMENT = "underworld chest"


def is_uw_chest_present() -> bool:
    """Return True if the Underworld Chest has spawned near the Dhuum altar.

    The chest only appears after Dhuum is defeated. All skill utilities call
    this to suppress casts once the encounter is finished.
    """
    for agent_id in AgentArray.GetAgentArray():
        if not Agent.IsValid(agent_id):
            continue
        if not Agent.IsGadget(agent_id):
            continue
        name = (Agent.GetNameByID(agent_id) or "").strip().lower()
        if _UW_CHEST_NAME_FRAGMENT not in name:
            continue
        if Utils.Distance(_UW_CHEST_POS, Agent.GetXY(agent_id)) <= _UW_CHEST_RADIUS:
            return True
    return False


# ── Skill resolution ───────────────────────────────────────────────────────────

def resolve_skill_id(*names: str) -> int:
    """Return the first resolvable numeric skill ID from the given name candidates.

    Returns 0 when none of the names resolve (e.g. the skill is absent from the
    current locale's game data or GLOBAL_CACHE is not yet populated).
    """
    for name in names:
        try:
            skill_id = int(GLOBAL_CACHE.Skill.GetID(name))
        except Exception:
            skill_id = 0
        if skill_id > 0:
            return skill_id
    return 0


def resolve_first_known_skill(*names: str) -> CustomSkill:
    """Return a CustomSkill for the first name that resolves to a valid skill ID.

    Falls back to names[0] when no name resolves, so callers always receive a
    non-None object and never need to guard against None.
    """
    for name in names:
        if resolve_skill_id(name) > 0:
            return CustomSkill(name)
    return CustomSkill(names[0])


# ── Party / account helpers ────────────────────────────────────────────────────

def same_party_and_map(self_account, other_account) -> bool:
    """Return True when both accounts share the same party, map, region, district, and language.

    All five fields must match to ensure only accounts that are truly in the
    same in-game instance are considered.
    """
    return (
        int(self_account.AgentPartyData.PartyID) == int(other_account.AgentPartyData.PartyID)
        and int(self_account.AgentData.Map.MapID) == int(other_account.AgentData.Map.MapID)
        and int(self_account.AgentData.Map.Region) == int(other_account.AgentData.Map.Region)
        and int(self_account.AgentData.Map.District) == int(other_account.AgentData.Map.District)
        and int(self_account.AgentData.Map.Language) == int(other_account.AgentData.Map.Language)
    )


def count_spirit_form_accounts() -> int:
    """Count how many active same-party accounts currently have Spirit Form (buff 3134)."""
    self_email = Player.GetAccountEmail()
    self_account = GLOBAL_CACHE.ShMem.GetAccountDataFromEmail(self_email)
    if self_account is None:
        return 0
    count = 0
    for account in (GLOBAL_CACHE.ShMem.GetAllAccountData() or []):
        if not account.IsSlotActive or account.IsIsolated:
            continue
        if not same_party_and_map(self_account, account):
            continue
        try:
            if any(
                b.SkillId == SPIRIT_FORM_SKILL_ID
                for b in account.AgentData.Buffs.Buffs
                if b.SkillId != 0
            ):
                count += 1
        except Exception:
            pass
    return count


def get_spirit_form_agent_ids() -> set[int]:
    """Return the agent IDs of same-party accounts that currently have Spirit Form."""
    result: set[int] = set()
    self_email = Player.GetAccountEmail()
    self_account = GLOBAL_CACHE.ShMem.GetAccountDataFromEmail(self_email)
    if self_account is None:
        return result
    for account in (GLOBAL_CACHE.ShMem.GetAllAccountData() or []):
        if not account.IsSlotActive or account.IsIsolated:
            continue
        if not same_party_and_map(self_account, account):
            continue
        try:
            if any(
                b.SkillId == SPIRIT_FORM_SKILL_ID
                for b in account.AgentData.Buffs.Buffs
                if b.SkillId != 0
            ):
                agent_id = int(account.AgentData.AgentID or 0)
                if agent_id > 0:
                    result.add(agent_id)
        except Exception:
            pass
    return result


def get_morale_by_agent_id() -> dict[int, int]:
    """Return a mapping of {agent_id: morale_value} for all same-party accounts.

    Morale range: 0–100.  death_penalty = 100 − morale.
    Accounts that are inactive, isolated, or in a different instance are excluded.
    """
    morale_by_agent: dict[int, int] = {}
    self_email = Player.GetAccountEmail()
    self_account = GLOBAL_CACHE.ShMem.GetAccountDataFromEmail(self_email)
    if self_account is None:
        return morale_by_agent
    for account in GLOBAL_CACHE.ShMem.GetAllAccountData():
        if not account.IsSlotActive or account.IsIsolated:
            continue
        if not same_party_and_map(self_account, account):
            continue
        agent_id = int(account.AgentData.AgentID or 0)
        if agent_id <= 0:
            continue
        morale_by_agent[agent_id] = int(account.AgentData.Morale)
    return morale_by_agent
