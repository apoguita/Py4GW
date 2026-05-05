from __future__ import annotations

from typing import TYPE_CHECKING, Optional, Protocol

import Py4GW
from Py4GWCoreLib import Player, GLOBAL_CACHE, SpiritModelID, Timer, Agent, Routines, Range, Allegiance, AgentArray
from Py4GWCoreLib import Weapon, Effects
from Py4GWCoreLib.enums import SPIRIT_BUFF_MAP, ModelID
from Py4GWCoreLib.GlobalCache.HexRemovalPriority import get_hexed_ally_for_removal
from .custom_skill import CustomSkillClass
from .targeting import TargetLowestAlly, TargetLowestAllyEnergy, TargetClusteredEnemy, TargetLowestAllyCaster, TargetLowestAllyMartial, TargetLowestAllyMelee, TargetLowestAllyRanged, GetAllAlliesArray, TargetAllyWeaponSpell, TargetMinionOrAllyNonEnchanted, TargetMinionNonEnchanted, TargetAllyNonEnchanted, TargetAllyNonWeaponSpelled, TargetDeadPartyMember, IsResurrectablePartyMember
from .targeting import GetEnemyAttacking, GetEnemyCasting, GetEnemyCastingSpell, GetEnemyCastingSpellOrChant, GetEnemyInjured, GetEnemyConditioned, GetEnemyHealthy
from .targeting import GetEnemyHexed, GetEnemyDegenHexed, GetEnemyEnchanted, GetEnemyMoving, GetEnemyKnockedDown
from .targeting import GetEnemyBleeding, GetEnemyPoisoned, GetEnemyCrippled
from .interrupt import is_interrupt_feasible, _queue_outcome
from .types import SkillNature, Skilltarget, SkillType
from .constants import MAX_NUM_PLAYERS
from .call_target import CallTarget
from .settings import Settings

from Py4GWCoreLib.enums_src.GameData_enums import Profession

if TYPE_CHECKING:
    from .cache_data import CacheData
    from .custom_skill_src.skill_types import CustomSkill
    from Py4GWCoreLib.GlobalCache.SharedMemory import AccountStruct


MAX_SKILLS = 8
custom_skill_data_handler = CustomSkillClass()

class SkillbarDataLike(Protocol):
    @property
    def recharge(self) -> int: ...

    @property
    def adrenaline_a(self) -> int: ...

SPIRIT_BUFF_SKILL_IDS: frozenset[int] = frozenset(
    int(skill_id)
    for skill_id in SPIRIT_BUFF_MAP.values()
    if skill_id
)
VOW_SPELL_TYPES: tuple[int, ...] = (
    SkillType.Spell.value,
    SkillType.Hex.value,
    SkillType.Enchantment.value,
    SkillType.Well.value,
    SkillType.Ward.value,
    SkillType.Glyph.value,
    SkillType.Ritual.value,
    SkillType.WeaponSpell.value,
    SkillType.Form.value,
)

SKILL_LOCK_MIN_LEASE_MS = 500


# Level 3 alcohol: each drink gives +3 or more — one drink reaches target level
ALCOHOL_L3_MODEL_IDS = [
    ModelID.Aged_Dwarven_Ale.value,
    ModelID.Aged_Hunters_Ale.value,
    ModelID.Keg_Of_Aged_Hunters_Ale.value,
    ModelID.Bottle_Of_Grog.value,
    ModelID.Spiked_Eggnog.value,
    ModelID.Vial_Of_Absinthe.value,
    ModelID.Witchs_Brew.value,
]
# Level 1 alcohol: each drink gives +1 — needs multiple uses to reach target level
ALCOHOL_L1_MODEL_IDS = [
    ModelID.Dwarven_Ale.value,
    ModelID.Hunters_Ale.value,
    ModelID.Bottle_Of_Rice_Wine.value,
    ModelID.Bottle_Of_Vabbian_Wine.value,
    ModelID.Bottle_Of_Juniberry_Gin.value,
    ModelID.Shamrock_Ale.value,
    ModelID.Hard_Apple_Cider.value,
    ModelID.Eggnog.value,
]
# Combined list: L3 items preferred first for efficiency
ALCOHOL_MODEL_IDS = ALCOHOL_L3_MODEL_IDS + ALCOHOL_L1_MODEL_IDS

#region CombatClass
class CombatClass:
    global MAX_SKILLS, custom_skill_data_handler

    class SkillData:
        skill_id: int
        skillbar_data: SkillbarDataLike
        custom_skill_data: CustomSkill

        def __init__(self, slot: int) -> None:
            self.skill_id = int(GLOBAL_CACHE.SkillBar.GetSkillIDBySlot(slot) or 0)  # slot is 1 based
            self.skillbar_data = GLOBAL_CACHE.SkillBar.GetSkillData(slot)  # Fetch additional data from the skill bar
            self.custom_skill_data = custom_skill_data_handler.get_skill(self.skill_id)  # Retrieve custom skill data

    def __init__(self) -> None:
        """
        Initializes the CombatClass with an empty skill set and order.
        """
        self.cached_data: CacheData | None = None
        self.active_spirit_buff_skill_ids: set[int] | None = None
        
        self.skills: list[CombatClass.SkillData] = []
        self.skill_order: list[int] = [0] * MAX_SKILLS
        self.skill_pointer: int = 0
        self.in_casting_routine: bool = False
        self.aftercast: int = 0
        self.aftercast_timer = Timer()
        self.aftercast_timer.Start()
        self.ping_handler = Py4GW.PingHandler()
        self.oldCalledTarget: int = 0
        self.auto_call_target_id: int = 0
        self.auto_call_target_called: bool = False
        self.auto_call_target_source: str = ""

        self.in_aggro: bool = False
        self.is_targeting_enabled: bool = False
        self.is_combat_enabled: bool = False
        self.is_skill_enabled: list[bool] = []
        self.blocked_skill_ids: set[int] = set()
        self.fast_casting_exists: bool = False
        self.fast_casting_level: int = 0
        self.expertise_exists: bool = False
        self.expertise_level: int = 0
        
        self.nearest_enemy: int = Routines.Agents.GetNearestEnemy(self.get_combat_distance())
        self.lowest_ally: int = 0
        self.lowest_ally_energy: int = 0
        self.nearest_npc: int = Routines.Agents.GetNearestNPC(Range.Spellcast.value)
        self.nearest_spirit: int = Routines.Agents.GetNearestSpirit(Range.Spellcast.value)
        self.lowest_minion: int = Routines.Agents.GetLowestMinion(Range.Spellcast.value)
        self.nearest_corpse: int = Routines.Agents.GetNearestCorpse(Range.Spellcast.value)
        
        self.energy_drain = GLOBAL_CACHE.Skill.GetID("Energy_Drain") 
        self.energy_tap = GLOBAL_CACHE.Skill.GetID("Energy_Tap")
        self.ether_feast = GLOBAL_CACHE.Skill.GetID("Ether_Feast")
        self.ether_lord = GLOBAL_CACHE.Skill.GetID("Ether_Lord")
        self.essence_strike = GLOBAL_CACHE.Skill.GetID("Essence_Strike")
        self.glowing_signet = GLOBAL_CACHE.Skill.GetID("Glowing_Signet")
        self.clamor_of_souls = GLOBAL_CACHE.Skill.GetID("Clamor_of_Souls")
        self.waste_not_want_not = GLOBAL_CACHE.Skill.GetID("Waste_Not_Want_Not")
        self.mend_body_and_soul = GLOBAL_CACHE.Skill.GetID("Mend_Body_and_Soul")
        self.grenths_balance = GLOBAL_CACHE.Skill.GetID("Grenths_Balance")
        self.deaths_retreat = GLOBAL_CACHE.Skill.GetID("Deaths_Retreat")
        self.plague_sending = GLOBAL_CACHE.Skill.GetID("Plague_Sending")
        self.plague_signet = GLOBAL_CACHE.Skill.GetID("Plague_Signet")
        self.plague_touch = GLOBAL_CACHE.Skill.GetID("Plague_Touch")
        self.golden_fang_strike = GLOBAL_CACHE.Skill.GetID("Golden_Fang_Strike")
        self.golden_fox_strike = GLOBAL_CACHE.Skill.GetID("Golden_Fox_Strike")
        self.golden_lotus_strike = GLOBAL_CACHE.Skill.GetID("Golden_Lotus_Strike")
        self.golden_phoenix_strike = GLOBAL_CACHE.Skill.GetID("Golden_Phoenix_Strike")
        self.golden_skull_strike = GLOBAL_CACHE.Skill.GetID("Golden_Skull_Strike")
        self.brutal_weapon = GLOBAL_CACHE.Skill.GetID("Brutal_Weapon")
        self.signet_of_removal = GLOBAL_CACHE.Skill.GetID("Signet_of_Removal")
        self.dwaynas_kiss = GLOBAL_CACHE.Skill.GetID("Dwaynas_Kiss")
        self.unnatural_signet = GLOBAL_CACHE.Skill.GetID("Unnatural_Signet")
        self.toxic_chill = GLOBAL_CACHE.Skill.GetID("Toxic_Chill")
        self.discord = GLOBAL_CACHE.Skill.GetID("Discord")
        self.empathic_removal = GLOBAL_CACHE.Skill.GetID("Empathic_Removal")
        self.iron_palm = GLOBAL_CACHE.Skill.GetID("Iron_Palm")
        self.melandrus_resilience = GLOBAL_CACHE.Skill.GetID("Melandrus_Resilience")
        self.necrosis = GLOBAL_CACHE.Skill.GetID("Necrosis")
        self.peace_and_harmony = GLOBAL_CACHE.Skill.GetID("Peace_and_Harmony")
        self.purge_signet = GLOBAL_CACHE.Skill.GetID("Purge_Signet")
        self.resilient_weapon = GLOBAL_CACHE.Skill.GetID("Resilient_Weapon")
        self.gaze_from_beyond = GLOBAL_CACHE.Skill.GetID("Gaze_from_Beyond")
        self.spirit_burn = GLOBAL_CACHE.Skill.GetID("Spirit_Burn")
        self.signet_of_ghostly_might = GLOBAL_CACHE.Skill.GetID("Signet_of_Ghostly_Might")
        self.burning = GLOBAL_CACHE.Skill.GetID("Burning")
        self.blind = GLOBAL_CACHE.Skill.GetID("Blind")
        self.cracked_armor = GLOBAL_CACHE.Skill.GetID("Cracked_Armor")
        self.crippled = GLOBAL_CACHE.Skill.GetID("Crippled")
        self.dazed = GLOBAL_CACHE.Skill.GetID("Dazed")
        self.deep_wound = GLOBAL_CACHE.Skill.GetID("Deep_Wound")
        self.disease = GLOBAL_CACHE.Skill.GetID("Disease")
        self.poison = GLOBAL_CACHE.Skill.GetID("Poison")
        self.weakness = GLOBAL_CACHE.Skill.GetID("Weakness")
        self.comfort_animal = GLOBAL_CACHE.Skill.GetID("Comfort_Animal")
        self.heal_as_one = GLOBAL_CACHE.Skill.GetID("Heal_as_One")
        self.never_rampage_alone = GLOBAL_CACHE.Skill.GetID("Never_Rampage_Alone")
        self.whirlwind_attack = GLOBAL_CACHE.Skill.GetID("Whirlwind_Attack")
        self.heroic_refrain = GLOBAL_CACHE.Skill.GetID("Heroic_Refrain")
        self.natures_blessing = GLOBAL_CACHE.Skill.GetID("Natures_Blessing")
        self.relentless_assault = GLOBAL_CACHE.Skill.GetID("Relentless_Assault")
        self.great_dwarf_weapon = GLOBAL_CACHE.Skill.GetID("Great_Dwarf_Weapon")
        self.preparation_skill_ids = tuple(
            skill_id
            for skill_id in (
                GLOBAL_CACHE.Skill.GetID("Apply_Poison"),
                GLOBAL_CACHE.Skill.GetID("Barbed_Arrows"),
                GLOBAL_CACHE.Skill.GetID("Choking_Gas"),
                GLOBAL_CACHE.Skill.GetID("Corrupted_Breath"),
                GLOBAL_CACHE.Skill.GetID("Disrupting_Accuracy"),
                GLOBAL_CACHE.Skill.GetID("Expert_Focus"),
                GLOBAL_CACHE.Skill.GetID("Glass_Arrows"),
                GLOBAL_CACHE.Skill.GetID("Ignite_Arrows"),
                GLOBAL_CACHE.Skill.GetID("Kindle_Arrows"),
                GLOBAL_CACHE.Skill.GetID("Marksmans_Wager"),
                GLOBAL_CACHE.Skill.GetID("Melandrus_Arrows"),
                GLOBAL_CACHE.Skill.GetID("Rapid_Fire"),
                GLOBAL_CACHE.Skill.GetID("Read_the_Wind"),
                GLOBAL_CACHE.Skill.GetID("Seeking_Arrows"),
                GLOBAL_CACHE.Skill.GetID("Trappers_Focus"),
            )
            if skill_id
        )
        self.pet_attack_list = [GLOBAL_CACHE.Skill.GetID("Bestial_Mauling"),
                               GLOBAL_CACHE.Skill.GetID("Bestial_Pounce"),
                               GLOBAL_CACHE.Skill.GetID("Brutal_Strike"),
                               GLOBAL_CACHE.Skill.GetID("Disrupting_Lunge"),
                               GLOBAL_CACHE.Skill.GetID("Enraged_Lunge"),
                               GLOBAL_CACHE.Skill.GetID("Feral_Lunge"),
                               GLOBAL_CACHE.Skill.GetID("Ferocious_Strike"),
                               GLOBAL_CACHE.Skill.GetID("Maiming_Strike"),
                               GLOBAL_CACHE.Skill.GetID("Melandrus_Assault"),
                               GLOBAL_CACHE.Skill.GetID("Poisonous_Bite"),
                               GLOBAL_CACHE.Skill.GetID("Pounce"),
                               GLOBAL_CACHE.Skill.GetID("Predators_Pounce"),
                               GLOBAL_CACHE.Skill.GetID("Savage_Pounce"),
                               GLOBAL_CACHE.Skill.GetID("Scavenger_Strike")
                               ]
        
        self.alcohol_skills = [
            GLOBAL_CACHE.Skill.GetID("Drunken_Master"),
            GLOBAL_CACHE.Skill.GetID("Dwarven_Stability"),
            GLOBAL_CACHE.Skill.GetID("Feel_No_Pain")
        ]
        
        #junundu
        self.junundu_wail = GLOBAL_CACHE.Skill.GetID("Junundu_Wail")
        self.unknown_junundu_ability = GLOBAL_CACHE.Skill.GetID("Unknown_Junundu_Ability")
        self.leave_junundu = GLOBAL_CACHE.Skill.GetID("Leave_Junundu")
        self.junundu_tunnel = GLOBAL_CACHE.Skill.GetID("Junundu_Tunnel")
        
    def Update(self, cached_data: CacheData) -> None:
        self.cached_data = cached_data
        self.in_aggro = cached_data.data.in_aggro
        
        self.fast_casting_exists = cached_data.data.fast_casting_exists
        self.fast_casting_level = cached_data.data.fast_casting_level
        self.expertise_exists = cached_data.data.expertise_exists
        self.expertise_level = cached_data.data.expertise_level
        
        options = cached_data.account_options
        self.is_targeting_enabled = options.Targeting if options is not None else False
        self.is_combat_enabled = options.Combat if options is not None else False
        if options is not None:
            self.is_skill_enabled = [bool(options.Skills[i]) for i in range(MAX_SKILLS)]
        else:
            self.is_skill_enabled = [False] * MAX_SKILLS
        self.active_spirit_buff_skill_ids = None

    def ApplyBlockedSkillIDs(self, blocked_skill_ids: list[int] | None = None) -> None:
        if len(self.is_skill_enabled) != MAX_SKILLS:
            self.is_skill_enabled = [True] * MAX_SKILLS
        self.blocked_skill_ids = {
            int(skill_id) for skill_id in (blocked_skill_ids or []) if int(skill_id) != 0
        }
            
    def _get_active_spirit_buff_skill_ids(self) -> set[int]:
        spirit_array = AgentArray.GetSpiritPetArray()
        if not spirit_array:
            return set()

        player_x, player_y = Player.GetXY()
        max_distance_sq = Range.Earshot.value * Range.Earshot.value
        active_skill_ids: set[int] = set()

        for spirit_id in spirit_array:
            if not Agent.IsAlive(spirit_id) or not Agent.IsSpawned(spirit_id):
                continue

            spirit_x, spirit_y = Agent.GetXY(spirit_id)
            dx = spirit_x - player_x
            dy = spirit_y - player_y
            if (dx * dx) + (dy * dy) > max_distance_sq:
                continue

            model_value = Agent.GetPlayerNumber(spirit_id)
            if model_value in SpiritModelID._value2member_map_:
                spirit_model_id = SpiritModelID(model_value)
                buff_skill_id = SPIRIT_BUFF_MAP.get(spirit_model_id)
                if buff_skill_id:
                    active_skill_ids.add(int(buff_skill_id))

        return active_skill_ids
        

    #region PrioritizeSkills
    def PrioritizeSkills(self) -> None:
        """
        Create a priority-based skill execution order.
        """
        #initialize skillbar
        original_skills : list[CombatClass.SkillData] = []
        for i in range(MAX_SKILLS):
            original_skills.append(self.SkillData(i+1))

        # Initialize the pointer and tracking list
        ptr = 0
        ptr_chk = [False] * MAX_SKILLS
        ordered_skills  : list[CombatClass.SkillData] = []
        
        priorities = [
            SkillNature.CustomA,
            SkillNature.Interrupt,
            SkillNature.CustomB,
            SkillNature.Enchantment_Removal,
            SkillNature.CustomC,
            SkillNature.Healing,
            SkillNature.CustomD,
            SkillNature.Resurrection,
            SkillNature.CustomE,
            SkillNature.Hex_Removal,
            SkillNature.CustomF,
            SkillNature.Condi_Cleanse,
            SkillNature.CustomG,
            SkillNature.SelfTargeted,
            SkillNature.CustomH,
            SkillNature.EnergyBuff,
            SkillNature.CustomI,
            SkillNature.Buff,
            SkillNature.CustomJ,
            SkillNature.OffensiveA,
            SkillNature.CustomK,
            SkillNature.OffensiveB,
            SkillNature.CustomL,
            SkillNature.OffensiveC,
            SkillNature.CustomM,
            SkillNature.Offensive,
            SkillNature.CustomN,
        ]

        for priority in priorities:
            #for i in range(ptr,MAX_SKILLS):
            for i in range(MAX_SKILLS):
                skill = original_skills[i]
                if not ptr_chk[i] and skill.custom_skill_data.Nature == priority.value:
                    self.skill_order[ptr] = i
                    ptr_chk[i] = True
                    ptr += 1
                    ordered_skills.append(skill)
        
        skill_types = [
            SkillType.Form,
            SkillType.Enchantment,
            SkillType.EchoRefrain,
            SkillType.WeaponSpell,
            SkillType.Chant,
            SkillType.Preparation,
            SkillType.Ritual,
            SkillType.Ward,
            SkillType.Well,
            SkillType.Stance,
            SkillType.Shout,
            SkillType.Glyph,
            SkillType.Signet,
            SkillType.Hex,
            SkillType.Trap,
            SkillType.Spell,
            SkillType.Skill,
            SkillType.PetAttack,
            SkillType.Attack,
        ]

        
        for skill_type in skill_types:
            #for i in range(ptr,MAX_SKILLS):
            for i in range(MAX_SKILLS):
                skill = original_skills[i]
                if not ptr_chk[i] and skill.custom_skill_data.SkillType == skill_type.value:
                    self.skill_order[ptr] = i
                    ptr_chk[i] = True
                    ptr += 1
                    ordered_skills.append(skill)

        combos = [3, 2, 1]  # Dual attack, off-hand attack, lead attack
        for combo in combos:
            #for i in range(ptr,MAX_SKILLS):
            for i in range(MAX_SKILLS):
                skill = original_skills[i]
                if not ptr_chk[i] and GLOBAL_CACHE.Skill.Data.GetCombo(skill.skill_id) == combo:
                    self.skill_order[ptr] = i
                    ptr_chk[i] = True
                    ptr += 1
                    ordered_skills.append(skill)
        
        # Fill in remaining unprioritized skills
        for i in range(MAX_SKILLS):
            if not ptr_chk[i]:
                self.skill_order[ptr] = i
                ptr_chk[i] = True
                ptr += 1
                ordered_skills.append(original_skills[i])
        
        self.skills = ordered_skills
        
        
    def GetSkills(self) -> list[CombatClass.SkillData]:
        """
        Retrieve the prioritized skill set.
        """
        return self.skills
        

    def GetOrderedSkill(self, index: int) -> Optional[CombatClass.SkillData]:
        """
        Retrieve the skill at the given index in the prioritized order.
        """
        if 0 <= index < MAX_SKILLS:
            return self.skills[index]
        return None  # Return None if the index is out of bounds

    def AdvanceSkillPointer(self) -> None:
        self.skill_pointer += 1
        if self.skill_pointer >= MAX_SKILLS:
            self.skill_pointer = 0
            
    def ResetSkillPointer(self) -> None:
        self.skill_pointer = 0
        
    def SetSkillPointer(self, pointer: int) -> None:
        if 0 <= pointer < MAX_SKILLS:
            self.skill_pointer = pointer
        else:
            self.skill_pointer = 0
            
    def GetSkillPointer(self) -> int:
        return self.skill_pointer
            
    def GetEnergyValues(self, agent_id: int) -> float:
        from .utils import GetEnergyValues
        return GetEnergyValues(agent_id, live_cached_data=self.cached_data)

    def IsSkillReady(self, slot: int) -> bool:
        if not (0 <= slot < len(self.skills)):
            return False

        original_index = self.skill_order[slot] 
        
        if self.skills[slot].skill_id == 0:
            return False

        if self.skills[slot].skillbar_data.recharge != 0:
            return False

        if not self.is_skill_enabled[original_index]:
            return False

        return self.skills[slot].skill_id not in self.blocked_skill_ids
        
    def InCastingRoutine(self) -> bool:
        if self.aftercast_timer.HasElapsed(self.aftercast):
            self.in_casting_routine = False
            self.aftercast_timer.Reset()

        return self.in_casting_routine

    def GetPartyTargetID(self) -> int:
        if not GLOBAL_CACHE.Party.IsPartyLoaded():
            return 0

        players = GLOBAL_CACHE.Party.GetPlayers()
        target = players[0].called_target_id

        if Agent.IsLiving(target) and not Agent.IsDead(target):
            return target  
        
        return 0 

    def SafeChangeTarget(self, target_id: int) -> None:
        if Agent.IsValid(target_id):
            Player.ChangeTarget(target_id)
            
    def SafeInteract(self, target_id: int) -> None:
        if Agent.IsValid(target_id):
            Player.ChangeTarget(target_id)
            Player.Interact(target_id, False)

    def _is_valid_call_target(self, target_id: int) -> bool:
        if target_id == 0 or not Agent.IsValid(target_id) or Agent.IsDead(target_id):
            return False
        _, target_allegiance = Agent.GetAllegiance(target_id)
        return target_allegiance == "Enemy"

    def MaybeCallCombatTarget(
        self,
        target_id: int,
        cached_data: CacheData | None,
        *,
        force: bool = False,
        source: str = "auto",
    ) -> None:
        if cached_data is None or not Settings().AutoCallTargets:
            return

        if not cached_data.account_data.AgentPartyData.IsPartyLeader:
            return

        if not self._is_valid_call_target(self.auto_call_target_id):
            self.auto_call_target_id = 0
            self.auto_call_target_called = False
            self.auto_call_target_source = ""

        if (
            self.auto_call_target_id != 0
            and target_id != self.auto_call_target_id
            and not force
        ):
            return

        if target_id != self.auto_call_target_id:
            self.auto_call_target_id = target_id
            self.auto_call_target_called = False
            self.auto_call_target_source = source

        if self.auto_call_target_called:
            return

        if not self._is_valid_call_target(target_id):
            return

        from Py4GWCoreLib import Party
        if Party.GetPartyTarget() == target_id:
            self.auto_call_target_called = True
            return

        if CallTarget(target_id, interact=False):
            self.auto_call_target_called = True

    def _spike_lock_enabled(self, skill: SkillData) -> bool:
        custom_skill = getattr(skill, "custom_skill_data", None)
        return bool(getattr(custom_skill, "SpikeLock", False))

    def _post_spike_lock(self, skill: SkillData, target_id: int) -> None:
        if not self._spike_lock_enabled(skill):
            return
        if target_id == 0 or not Agent.IsValid(target_id) or Agent.IsDead(target_id):
            return
        try:
            from Py4GWCoreLib.enums_src.Whiteboard_enums import (
                WhiteboardClaimStrength,
                WhiteboardLockKind,
                WhiteboardLockMode,
                WhiteboardReentryPolicy,
            )

            email = Player.GetAccountEmail() or ""
            if not email:
                return
            group_id = GLOBAL_CACHE.ShMem.GetAccountGroupByEmail(email)
            expires_at = int(Py4GW.Game.get_tick_count64()) + 1500
            GLOBAL_CACHE.ShMem.PostLock(
                email,
                int(WhiteboardLockKind.CALL_TARGET),
                int(skill.skill_id),
                int(target_id),
                int(expires_at),
                int(group_id),
                int(WhiteboardLockMode.BARRIER),
                1,
                int(WhiteboardReentryPolicy.OWNER_REENTRANT),
                int(WhiteboardClaimStrength.HARD),
            )
        except Exception:
            pass

    def _apply_spike_lock(self, skill: SkillData, target_id: int) -> None:
        if not self._spike_lock_enabled(skill):
            return
        if target_id == 0 or not Agent.IsValid(target_id) or Agent.IsDead(target_id):
            return
        _, target_allegiance = Agent.GetAllegiance(target_id)
        if target_allegiance != "Enemy":
            return
        if CallTarget(target_id, interact=False):
            self.auto_call_target_id = target_id
            self.auto_call_target_called = True
            self.auto_call_target_source = "spike"
        self._post_spike_lock(skill, target_id)

    def GetPartyTarget(self) -> int:
        from Py4GWCoreLib import Party
        party_target = Party.GetPartyTarget()
        if self.is_targeting_enabled and party_target != 0:
            current_target = Player.GetTargetID()
            if current_target != party_target:
                if Agent.IsLiving(party_target):
                    _, alliegeance = Agent.GetAllegiance(party_target)
                    if alliegeance != 'Ally' and alliegeance != 'NPC/Minipet' and self.is_combat_enabled:
                        self.SafeChangeTarget(party_target)
                        return party_target
        return 0

    def get_combat_distance(self) -> float:
        if self.cached_data is not None:
            return self.cached_data.GetActiveScanRange()
        return Range.Spellcast.value if self.in_aggro else Range.Earshot.value



    def GetAppropiateTarget(self, slot: int) -> int:
        from .utils import HasIllusionaryWeaponry
        v_target: int = 0

        if not self.is_targeting_enabled:
            return Player.GetTargetID()

        targeting_strict = self.skills[slot].custom_skill_data.Conditions.TargetingStrict
        target_allegiance = self.skills[slot].custom_skill_data.TargetAllegiance
        conditions = self.skills[slot].custom_skill_data.Conditions

        # Lazy helpers — only call expensive scans when a branch actually needs them
        _nearest_enemy = None
        def get_nearest_enemy() -> int:
            nonlocal _nearest_enemy
            if _nearest_enemy is None:
                _nearest_enemy = Routines.Agents.GetNearestEnemy(self.get_combat_distance())
            return _nearest_enemy

        _lowest_ally = None
        def get_lowest_ally() -> int:
            nonlocal _lowest_ally
            if _lowest_ally is None:
                _lowest_ally = TargetLowestAlly(filter_skill_id=self.skills[slot].skill_id)
            return _lowest_ally

        if self.skills[slot].skill_id == self.heroic_refrain:
            if not self.HasEffect(Player.GetAgentID(), self.heroic_refrain):
                return Player.GetAgentID()

        if target_allegiance == Skilltarget.Enemy:
            v_target = self.GetPartyTarget()
            if v_target == 0:
                v_target = get_nearest_enemy()
        elif target_allegiance == Skilltarget.EnemyCaster:
            v_target = Routines.Agents.GetNearestEnemyCaster(self.get_combat_distance())
            if v_target == 0 and not targeting_strict:
                v_target = get_nearest_enemy()
        elif target_allegiance == Skilltarget.EnemyMartial:
            v_target = Routines.Agents.GetNearestEnemyMartial(self.get_combat_distance())
            if v_target == 0 and not targeting_strict:
                v_target = get_nearest_enemy()
        elif target_allegiance == Skilltarget.EnemyMartialMelee:
            v_target = Routines.Agents.GetNearestEnemyMelee(self.get_combat_distance())
            if v_target == 0 and not targeting_strict:
                v_target = get_nearest_enemy()
        elif target_allegiance == Skilltarget.EnemyClustered:
            v_target = TargetClusteredEnemy(
                self.get_combat_distance(),
                skill_id=self.skills[slot].skill_id,
                cluster_radius=Range.Earshot.value,
            )
            if v_target == 0 and not targeting_strict:
                v_target = get_nearest_enemy()
        elif target_allegiance == Skilltarget.EnemyAttacking:
            v_target = GetEnemyAttacking(self.get_combat_distance())
            if v_target == 0 and not targeting_strict:
                v_target = get_nearest_enemy()
        elif target_allegiance == Skilltarget.EnemyCasting:
            v_target = GetEnemyCasting(self.get_combat_distance())
            if v_target == 0 and not targeting_strict:
                v_target = get_nearest_enemy()
        elif target_allegiance == Skilltarget.EnemyCastingSpell:
            v_target = GetEnemyCastingSpell(self.get_combat_distance())
            if v_target == 0 and not targeting_strict:
                v_target = get_nearest_enemy()
        elif target_allegiance == Skilltarget.EnemyCastingSpellOrChant:
            v_target = GetEnemyCastingSpellOrChant(self.get_combat_distance())
            if v_target == 0 and not targeting_strict:
                v_target = get_nearest_enemy()
        elif target_allegiance == Skilltarget.AllyWeaponSpell:
            v_target = TargetAllyWeaponSpell(
                self.skills[slot].skill_id,
                self.get_combat_distance(),
                allow_overlap_weapon_spell=conditions.AllowOverlapWeaponSpell,
            )
            if v_target == 0 and not targeting_strict:
                v_target = get_lowest_ally()
        elif target_allegiance == Skilltarget.EnemyInjured:
            v_target = GetEnemyInjured(self.get_combat_distance())
            if v_target == 0 and not targeting_strict:
                v_target = get_nearest_enemy()
        elif target_allegiance == Skilltarget.EnemyConditioned:
            v_target = GetEnemyConditioned(self.get_combat_distance())
            if v_target == 0 and not targeting_strict:
                v_target = get_nearest_enemy()
        elif target_allegiance == Skilltarget.EnemyBleeding:
            v_target = GetEnemyBleeding(self.get_combat_distance())
            if v_target == 0 and not targeting_strict:
                v_target = get_nearest_enemy()
        elif target_allegiance == Skilltarget.EnemyPoisoned:
            v_target = GetEnemyPoisoned(self.get_combat_distance())
            if v_target == 0 and not targeting_strict:
                v_target = get_nearest_enemy()
        elif target_allegiance == Skilltarget.EnemyCrippled:
            v_target = GetEnemyCrippled(self.get_combat_distance())
            if v_target == 0 and not targeting_strict:
                v_target = get_nearest_enemy()
        elif target_allegiance == Skilltarget.EnemyHexed:
            v_target = GetEnemyHexed(self.get_combat_distance())
            if v_target == 0 and not targeting_strict:
                v_target = get_nearest_enemy()
        elif target_allegiance == Skilltarget.EnemyDegenHexed:
            v_target = GetEnemyDegenHexed(self.get_combat_distance())
            if v_target == 0 and not targeting_strict:
                v_target = get_nearest_enemy()
        elif target_allegiance == Skilltarget.EnemyEnchanted:
            v_target = GetEnemyEnchanted(self.get_combat_distance())
            if v_target == 0 and not targeting_strict:
                v_target = get_nearest_enemy()
        elif target_allegiance == Skilltarget.EnemyMoving:
            v_target = GetEnemyMoving(self.get_combat_distance())
            if v_target == 0 and not targeting_strict:
                v_target = get_nearest_enemy()
        elif target_allegiance == Skilltarget.EnemyKnockedDown:
            v_target = GetEnemyKnockedDown(self.get_combat_distance())
            if v_target == 0 and not targeting_strict:
                v_target = get_nearest_enemy()
        elif target_allegiance == Skilltarget.AllyMartialRanged:
            v_target = Routines.Agents.GetNearestEnemyRanged(self.get_combat_distance())
            if v_target == 0 and not targeting_strict:
                v_target = get_nearest_enemy()
        elif target_allegiance == Skilltarget.Ally:
            v_target = get_lowest_ally()
        elif target_allegiance == Skilltarget.AllyCaster:
            v_target = TargetLowestAllyCaster(filter_skill_id=self.skills[slot].skill_id)
            if v_target == 0 and not targeting_strict:
                v_target = get_lowest_ally()
        elif target_allegiance == Skilltarget.AllyMartial:
            target_other_ally = self.skills[slot].skill_id == self.great_dwarf_weapon
            v_target = TargetLowestAllyMartial(other_ally=target_other_ally, filter_skill_id=self.skills[slot].skill_id)
            if v_target != 0 and HasIllusionaryWeaponry(v_target):
                v_target = 0
            if v_target == 0 and not targeting_strict:
                v_target = get_lowest_ally()
        elif target_allegiance == Skilltarget.AllyMartialMelee:
            v_target = TargetLowestAllyMelee(filter_skill_id=self.skills[slot].skill_id)
            if v_target != 0 and HasIllusionaryWeaponry(v_target):
                v_target = 0
            if v_target == 0 and not targeting_strict:
                v_target = get_lowest_ally()
        elif target_allegiance == Skilltarget.AllyMartialRanged:
            v_target = TargetLowestAllyRanged(filter_skill_id=self.skills[slot].skill_id)
            if v_target == 0 and not targeting_strict:
                v_target = get_lowest_ally()
        elif target_allegiance == Skilltarget.OtherAlly:
            if self.skills[slot].custom_skill_data.Nature == SkillNature.EnergyBuff.value:
                v_target = TargetLowestAllyEnergy(other_ally=True, filter_skill_id=self.skills[slot].skill_id, less_energy=self.skills[slot].custom_skill_data.Conditions.LessEnergy)
                #print("Energy Buff Target: ", RawAgentArray().get_name(v_target))
            else:
                v_target = TargetLowestAlly(other_ally=True, filter_skill_id=self.skills[slot].skill_id)
        elif target_allegiance == Skilltarget.Self:
            v_target = Player.GetAgentID()
        elif target_allegiance == Skilltarget.Pet:
            v_target = GLOBAL_CACHE.Party.Pets.GetPetID(Player.GetAgentID())
        elif target_allegiance == Skilltarget.DeadAlly:
            v_target = TargetDeadPartyMember(Range.Spellcast.value)
        elif target_allegiance == Skilltarget.ResurrectionAlly:
            v_target = Routines.Agents.GetResurrectionTarget(
                Range.Spellcast.value,
                reserve=True,
                skill_id=self.skills[slot].skill_id,
            )
        elif target_allegiance == Skilltarget.HexedAlly:
            v_target = get_hexed_ally_for_removal(
                Range.Spellcast.value,
                reserve=True,
                skill_id=self.skills[slot].skill_id,
            )
        elif target_allegiance == Skilltarget.Spirit:
            v_target = Routines.Agents.GetNearestSpirit(Range.Spellcast.value)
        elif target_allegiance == Skilltarget.Minion:
            v_target = Routines.Agents.GetLowestMinion(Range.Spellcast.value)
        elif target_allegiance == Skilltarget.MinionOrAllyNonEnchanted:
            v_target = TargetMinionOrAllyNonEnchanted(filter_skill_id=self.skills[slot].skill_id)
        elif target_allegiance == Skilltarget.MinionNonEnchanted:
            v_target = TargetMinionNonEnchanted()
        elif target_allegiance == Skilltarget.AllyNonEnchanted:
            v_target = TargetAllyNonEnchanted()
        elif target_allegiance == Skilltarget.NonWeaponSpelledAlly:
            v_target = Player.GetAgentID() if TargetAllyNonWeaponSpelled() else 0
        elif target_allegiance == Skilltarget.Corpse:
            v_target = Routines.Agents.GetNearestCorpse(Range.Spellcast.value)
        elif target_allegiance == Skilltarget.ExploitableCorpse:
            v_target = Routines.Agents.GetNearestExploitableCorpse(
                Range.Spellcast.value,
                reserve=True,
                skill_id=self.skills[slot].skill_id,
            )
        elif target_allegiance == Skilltarget.AllyNPCByModel:
            model_id_filter = self.skills[slot].custom_skill_data.Conditions.ModelIDFilter
            if model_id_filter:
                npc_agent_id = Routines.Agents.GetNearestAliveAgentByModelID(model_id_filter, Range.Spellcast.value)
                if npc_agent_id and not Routines.Checks.Agents.IsWeaponSpelled(npc_agent_id):
                    v_target = npc_agent_id
            if v_target == 0 and not targeting_strict:
                # Fallback only when strict targeting is disabled.
                # Exclude self to avoid invalid self-target attempts (e.g. Great Dwarf Weapon).
                v_target = TargetLowestAllyMartial(other_ally=True, filter_skill_id=self.skills[slot].skill_id)
                # Exclude the NPC itself from the fallback — it may appear in GetAllyArray()
                # as a martial NPC, but CheckForEffect doesn't work for non-party members,
                # so it won't be filtered out even when it already has the weapon spell.
                if v_target and model_id_filter and Agent.GetModelID(v_target) == model_id_filter:
                    v_target = 0
            if v_target == Player.GetAgentID():
                v_target = 0
        else:
            v_target = self.GetPartyTarget()
            if v_target == 0:
                v_target = get_nearest_enemy()

        # Great Dwarf Weapon cannot self-target; keep an extra guard even if profile data is misconfigured.
        if self.skills[slot].skill_id == self.great_dwarf_weapon and v_target == Player.GetAgentID():
            v_target = TargetLowestAllyMartial(other_ally=True, filter_skill_id=self.skills[slot].skill_id)
        return v_target

    def IsPartyMember(self, agent_id: int) -> bool:
        from .utils import IsPartyMember
        return IsPartyMember(agent_id)

    def _get_active_effect_ids(self, agent_id: int) -> list[int] | None:
        cached_data = self.cached_data

        if cached_data is not None:
            party_acc = cached_data.party.get_by_player_id(agent_id)
            if (
                party_acc is not None
                and party_acc.IsSlotActive
                and party_acc.AgentPartyData.PartyID == cached_data.party.party_id
            ):
                return [buff.SkillId for buff in party_acc.AgentData.Buffs.Buffs]

        for acc in GLOBAL_CACHE.ShMem.GetAllActiveSlotsData() or []:
            if acc.IsSlotActive and acc.AgentData.AgentID == agent_id:
                return [buff.SkillId for buff in acc.AgentData.Buffs.Buffs]

        allegiance, allegiance_name = Agent.GetAllegiance(agent_id)
        if allegiance == Allegiance.SpiritPet.value:
            return []

        if allegiance_name in ("Ally", "NPC/Minipet"):
            return []

        return [
            effect.skill_id
            for effect in GLOBAL_CACHE.Effects.GetBuffs(agent_id) + GLOBAL_CACHE.Effects.GetEffects(agent_id)
        ]
        
    def HasEffect(self, agent_id: int, skill_id: int, exact_weapon_spell: bool = False) -> bool:
        active_effect_ids = self._get_active_effect_ids(agent_id)
        if active_effect_ids is None:
            return False
        
        custom_skill_data = custom_skill_data_handler.get_skill(skill_id)
        shared_effects = custom_skill_data.Conditions.SharedEffects if custom_skill_data else []
        
        result = skill_id in active_effect_ids or any(shared_buff in active_effect_ids for shared_buff in shared_effects)

        if not result:
            skilltype, _ = GLOBAL_CACHE.Skill.GetType(skill_id)
            if not exact_weapon_spell and skilltype == SkillType.WeaponSpell.value:
                result = Routines.Checks.Agents.IsWeaponSpelled(agent_id)
            elif skilltype == SkillType.Preparation.value:
                result = any(preparation_id in active_effect_ids for preparation_id in self.preparation_skill_ids)

        return result


    def AreCastConditionsMet(self, slot: int, vTarget: int) -> bool:
        from .utils import GetEffectAndBuffIds
        
        number_of_features = 0
        feature_count = 0

        Conditions = self.skills[slot].custom_skill_data.Conditions

        """ Check if the skill is a resurrection skill and the target is dead """
        if self.skills[slot].custom_skill_data.Nature == SkillNature.Resurrection.value:
            return bool(IsResurrectablePartyMember(vTarget) and Routines.Checks.Agents.IsDead(vTarget))


        if self.skills[slot].custom_skill_data.Conditions.UniqueProperty:
            
            """ check all UniqueProperty skills """
            if (self.skills[slot].skill_id == self.energy_drain or 
                self.skills[slot].skill_id == self.energy_tap or
                self.skills[slot].skill_id == self.ether_lord 
                ):
                return self.GetEnergyValues(Player.GetAgentID()) < Conditions.LessEnergy

            if (self.skills[slot].skill_id == self.ether_feast):
                return Agent.GetHealth(Player.GetAgentID()) < Conditions.LessLife
        
            if (self.skills[slot].skill_id == self.essence_strike):
                energy = self.GetEnergyValues(Player.GetAgentID()) < Conditions.LessEnergy
                return energy and (Routines.Agents.GetNearestSpirit(Range.Spellcast.value) != 0)

            if (self.skills[slot].skill_id == self.glowing_signet):
                energy= self.GetEnergyValues(Player.GetAgentID()) < Conditions.LessEnergy
                return energy and self.HasEffect(vTarget, self.burning)

            if (self.skills[slot].skill_id == self.clamor_of_souls):
                energy = self.GetEnergyValues(Player.GetAgentID()) < Conditions.LessEnergy
                return energy and Agent.IsHoldingItem(Player.GetAgentID())

            if (self.skills[slot].skill_id == self.waste_not_want_not):
                energy= self.GetEnergyValues(Player.GetAgentID()) < Conditions.LessEnergy
                return energy and not Agent.IsCasting(vTarget) and not Routines.Checks.Agents.IsAttacking(vTarget)

            if (self.skills[slot].skill_id == self.mend_body_and_soul):
                spirits_exist = Routines.Agents.GetNearestSpirit(Range.Earshot.value)
                life = Agent.GetHealth(Player.GetAgentID()) < Conditions.LessLife
                return life or (spirits_exist != 0 and Routines.Checks.Agents.IsConditioned(vTarget))

            if (self.skills[slot].skill_id == self.grenths_balance):
                life = Agent.GetHealth(Player.GetAgentID()) < Conditions.LessLife
                return life and Agent.GetHealth(Player.GetAgentID()) < Routines.Checks.Agents.GetHealth(vTarget)

            if (self.skills[slot].skill_id == self.deaths_retreat):
                return Agent.GetHealth(Player.GetAgentID()) < Routines.Checks.Agents.GetHealth(vTarget)

            if (self.skills[slot].skill_id == self.plague_sending or
                self.skills[slot].skill_id == self.plague_signet or
                self.skills[slot].skill_id == self.plague_touch
                ):
                return Routines.Checks.Agents.IsConditioned(Player.GetAgentID())

            if (self.skills[slot].skill_id == self.golden_fang_strike or
                self.skills[slot].skill_id == self.golden_fox_strike or
                self.skills[slot].skill_id == self.golden_lotus_strike or
                self.skills[slot].skill_id == self.golden_phoenix_strike or
                self.skills[slot].skill_id == self.golden_skull_strike
                ):
                return Routines.Checks.Agents.IsEnchanted(Player.GetAgentID())

            if (self.skills[slot].skill_id == self.brutal_weapon):
                return not Routines.Checks.Agents.IsEnchanted(Player.GetAgentID())

            if (self.skills[slot].skill_id == self.signet_of_removal):
                return (not Routines.Checks.Agents.IsEnchanted(vTarget)) and Routines.Checks.Agents.IsConditioned(vTarget)

            if (self.skills[slot].skill_id == self.dwaynas_kiss or
                self.skills[slot].skill_id == self.unnatural_signet or
                self.skills[slot].skill_id == self.toxic_chill
                ):
                return Routines.Checks.Agents.IsHexed(vTarget) or Routines.Checks.Agents.IsEnchanted(vTarget)

            if (self.skills[slot].skill_id == self.discord):
                return (Routines.Checks.Agents.IsHexed(vTarget) and Routines.Checks.Agents.IsConditioned(vTarget)) or (Routines.Checks.Agents.IsEnchanted(vTarget))

            if (self.skills[slot].skill_id == self.empathic_removal or
                self.skills[slot].skill_id == self.iron_palm or
                self.skills[slot].skill_id == self.melandrus_resilience or
                self.skills[slot].skill_id == self.necrosis or
                self.skills[slot].skill_id == self.peace_and_harmony or
                self.skills[slot].skill_id == self.purge_signet or
                self.skills[slot].skill_id == self.resilient_weapon
                ):
                return Routines.Checks.Agents.IsHexed(vTarget) or Routines.Checks.Agents.IsConditioned(vTarget)
            
            if (self.skills[slot].skill_id == self.gaze_from_beyond or
                self.skills[slot].skill_id == self.spirit_burn or
                self.skills[slot].skill_id == self.signet_of_ghostly_might
                ):
                return True if Routines.Agents.GetNearestSpirit(Range.Spellcast.value) != 0 else False
            
            if (self.skills[slot].skill_id == self.comfort_animal or
                self.skills[slot].skill_id == self.heal_as_one
                ):
                from Py4GWCoreLib.Party import Party
                pet_data = Party.Pets.GetPetInfo(Player.GetAgentID())
                if not pet_data or pet_data.agent_id == 0:
                    return False
                LessLife = Routines.Checks.Agents.GetHealth(pet_data.agent_id) < Conditions.LessLife
                dead = Routines.Checks.Agents.IsDead(pet_data.agent_id)
                return LessLife or dead

            if (self.skills[slot].skill_id == self.never_rampage_alone):
                pet_id = GLOBAL_CACHE.Party.Pets.GetPetID(Player.GetAgentID())
                return pet_id != 0 and Routines.Checks.Agents.IsAlive(pet_id)

            if (self.skills[slot].skill_id == self.whirlwind_attack):
                weapon_type, _ = Agent.GetWeaponType(Player.GetAgentID())
                return weapon_type not in (1, 6)  # Block for Bow (1) and Spear (6)

            if (self.skills[slot].skill_id == self.natures_blessing):
                player_life = Agent.GetHealth(Player.GetAgentID()) < Conditions.LessLife
                nearest_npc = Routines.Agents.GetNearestNPC(Range.Spirit.value)
                if nearest_npc == 0:
                    return player_life

                nearest_NPC_life = Routines.Checks.Agents.GetHealth(nearest_npc) < Conditions.LessLife
                return player_life or nearest_NPC_life
            
            if (self.skills[slot].skill_id == self.relentless_assault
                ):
                return Routines.Checks.Agents.IsHexed(Player.GetAgentID()) or Routines.Checks.Agents.IsConditioned(Player.GetAgentID())
            
            if (self.skills[slot].skill_id == self.junundu_wail):
                nearest_corpse = Routines.Agents.GetDeadAlly(Range.Earshot.value)
                if nearest_corpse != 0:
                    return True
                
                life = Agent.GetHealth(Player.GetAgentID()) < Conditions.LessLife
                nearest = Routines.Agents.GetNearestEnemy(self.get_combat_distance())
                if nearest == 0:
                    return life
                
                return False


            if (self.skills[slot].skill_id == self.junundu_tunnel):
                return Routines.Agents.GetNearestEnemy(self.get_combat_distance()) == 0

            if ((self.skills[slot].skill_id == self.unknown_junundu_ability) or
                (self.skills[slot].skill_id == self.leave_junundu)
                ):
                return False


            return True  # if no unique property is configured, return True for all UniqueProperty
        
        feature_count += (1 if Conditions.IsAlive else 0)
        feature_count += (1 if Conditions.HasCondition else 0)
        feature_count += (1 if Conditions.HasBleeding else 0)
        feature_count += (1 if Conditions.HasBlindness else 0)
        feature_count += (1 if Conditions.HasBurning else 0)
        feature_count += (1 if Conditions.HasCrackedArmor else 0)
        feature_count += (1 if Conditions.HasCrippled else 0)
        feature_count += (1 if Conditions.HasDazed else 0)
        feature_count += (1 if Conditions.HasDeepWound else 0)
        feature_count += (1 if Conditions.HasDisease else 0)
        feature_count += (1 if Conditions.HasPoison else 0)
        feature_count += (1 if Conditions.HasWeakness else 0)
        feature_count += (1 if Conditions.HasWeaponSpell else 0)
        feature_count += (1 if Conditions.HasEnchantment else 0)
        feature_count += (1 if Conditions.HasDervishEnchantment else 0)
        feature_count += (1 if Conditions.HasHex else 0)
        feature_count += (1 if Conditions.HasChant else 0)
        feature_count += (1 if Conditions.IsCasting else 0)
        feature_count += (1 if Conditions.IsKnockedDown else 0)
        feature_count += (1 if Conditions.IsMoving else 0)
        feature_count += (1 if Conditions.IsAttacking else 0)
        feature_count += (1 if Conditions.IsHoldingItem else 0)
        feature_count += (1 if Conditions.LessLife > 0 else 0)
        feature_count += (1 if Conditions.MoreLife > 0 else 0)
        feature_count += (1 if Conditions.LessEnergy > 0 else 0)
        feature_count += (1 if Conditions.LessSelfEnergyPercentage > 0 else 0)
        feature_count += (1 if Conditions.Overcast > 0 else 0)
        feature_count += (1 if Conditions.IsPartyWide else 0)
        feature_count += (1 if Conditions.RequiresSpiritInEarshot else 0)
        feature_count += (1 if Conditions.EnemyCount > 0 else 0)
        feature_count += (1 if Conditions.AlliesInRange > 0 else 0)
        feature_count += (1 if Conditions.SpiritsInRange > 0 else 0)
        feature_count += (1 if Conditions.MinionsInRange > 0 else 0)
        feature_count += (1 if Conditions.CloseToAggro else 0)

        if Conditions.IsAlive:
            if Routines.Checks.Agents.IsAlive(vTarget):
                number_of_features += 1

        needs_any_condition = Conditions.HasCondition
        needs_bleeding = needs_any_condition or Conditions.HasBleeding
        needs_blind = needs_any_condition or Conditions.HasBlindness
        needs_burning = needs_any_condition or Conditions.HasBurning
        needs_cracked_armor = needs_any_condition or Conditions.HasCrackedArmor
        needs_crippled = needs_any_condition or Conditions.HasCrippled
        needs_dazed = needs_any_condition or Conditions.HasDazed
        needs_deep_wound = needs_any_condition or Conditions.HasDeepWound
        needs_disease = needs_any_condition or Conditions.HasDisease
        needs_poison = needs_any_condition or Conditions.HasPoison
        needs_weakness = needs_any_condition or Conditions.HasWeakness
        buff_list: list[int] = []
        cached_data = self.cached_data
        def get_buff_list() -> list[int]:
            nonlocal buff_list
            if not buff_list:
                if cached_data is None:
                    raise ValueError("cached_data is required")
                buff_list = GetEffectAndBuffIds(vTarget, cached_data)
            return buff_list

        is_conditioned = Routines.Checks.Agents.IsConditioned(vTarget) if needs_any_condition else False
        is_bleeding = Agent.IsBleeding(vTarget) if needs_bleeding else False
        is_blind = self.HasEffect(vTarget, self.blind) if needs_blind else False
        is_burning = self.HasEffect(vTarget, self.burning) if needs_burning else False
        is_cracked_armor = self.HasEffect(vTarget, self.cracked_armor) if needs_cracked_armor else False
        is_crippled = Agent.IsCrippled(vTarget) if needs_crippled else False
        is_dazed = self.HasEffect(vTarget, self.dazed) if needs_dazed else False
        is_deep_wound = self.HasEffect(vTarget, self.deep_wound) if needs_deep_wound else False
        is_disease = self.HasEffect(vTarget, self.disease) if needs_disease else False
        is_poison = Agent.IsPoisoned(vTarget) if needs_poison else False
        is_weakness = self.HasEffect(vTarget, self.weakness) if needs_weakness else False


        if Conditions.HasBleeding:
            if is_bleeding:
                number_of_features += 1

        if Conditions.HasBlindness:
            if is_blind:
                number_of_features += 1

        if Conditions.HasBurning:
            if is_burning:
                number_of_features += 1

        if Conditions.HasCrackedArmor:
            if is_cracked_armor:
                number_of_features += 1
          
        if Conditions.HasCrippled:
            if is_crippled:
                number_of_features += 1
                
        if Conditions.HasDazed:
            if is_dazed:
                number_of_features += 1
          
        if Conditions.HasDeepWound:
            if is_deep_wound:
                number_of_features += 1
                
        if Conditions.HasDisease:
            if is_disease:
                number_of_features += 1

        if Conditions.HasPoison:
            if is_poison:
                number_of_features += 1

        if Conditions.HasWeakness:
            if is_weakness:
                number_of_features += 1
         
        if Conditions.HasWeaponSpell:
            if Routines.Checks.Agents.IsWeaponSpelled(vTarget):
                if len(Conditions.WeaponSpellList) == 0:
                    number_of_features += 1
                else:
                    for skill_id in Conditions.WeaponSpellList:
                        if self.HasEffect(vTarget, skill_id, exact_weapon_spell=True):
                            number_of_features += 1
                            break

        if Conditions.HasEnchantment:
            if Routines.Checks.Agents.IsEnchanted(vTarget):
                if len(Conditions.EnchantmentList) == 0:
                    number_of_features += 1
                else:
                    for skill_id in Conditions.EnchantmentList:
                        if self.HasEffect(vTarget, skill_id):
                            number_of_features += 1
                            break

        if Conditions.HasDervishEnchantment:
            for buff in get_buff_list():
                skill_type, _ = GLOBAL_CACHE.Skill.GetType(buff)
                if skill_type == SkillType.Enchantment.value:
                    _, profession = GLOBAL_CACHE.Skill.GetProfession(buff)
                    if profession == "Dervish":
                        number_of_features += 1
                        break

        if Conditions.HasHex:
            if Routines.Checks.Agents.IsHexed(vTarget):
                if len(Conditions.HexList) == 0:
                    number_of_features += 1
                else:
                    for skill_id in Conditions.HexList:
                        if self.HasEffect(vTarget, skill_id):
                            number_of_features += 1
                            break

        if Conditions.HasChant:
            if self.IsPartyMember(vTarget):                
                buff_list = get_buff_list()
                
                for buff in buff_list:
                    skill_type, _ = GLOBAL_CACHE.Skill.GetType(buff)
                    if skill_type == SkillType.Chant.value:
                        if len(Conditions.ChantList) == 0:
                            number_of_features += 1
                        else:
                            if buff in Conditions.ChantList:
                                number_of_features += 1
                                break
                                
        if Conditions.IsCasting:
            if Agent.IsCasting(vTarget):
                casting_skill_id = Agent.GetCastingSkillID(vTarget)
                nature = self.skills[slot].custom_skill_data.Nature
                if nature == SkillNature.Interrupt.value:
                    if is_interrupt_feasible(
                        target_agent_id=vTarget,
                        our_skill_id=self.skills[slot].skill_id,
                        fast_casting_level=self.fast_casting_level,
                        ping_ms=int(self.ping_handler.GetCurrentPing()),
                    ):
                        if (len(Conditions.CastingSkillList) == 0
                                or casting_skill_id in Conditions.CastingSkillList):
                            number_of_features += 1
                            _queue_outcome(vTarget, casting_skill_id, self.skills[slot].skill_id)
                else:
                    if GLOBAL_CACHE.Skill.Data.GetActivation(casting_skill_id) >= 0.250:
                        if len(Conditions.CastingSkillList) == 0:
                            number_of_features += 1
                        else:
                            if casting_skill_id in Conditions.CastingSkillList:
                                number_of_features += 1

        if Conditions.IsKnockedDown:
            if Routines.Checks.Agents.IsKnockedDown(vTarget):
                number_of_features += 1
                            
        if Conditions.IsMoving:
            if Agent.IsMoving(vTarget):
                number_of_features += 1
        
        if Conditions.IsAttacking:
            if Routines.Checks.Agents.IsAttacking(vTarget):
                number_of_features += 1

        if Conditions.IsHoldingItem:
            if Agent.IsHoldingItem(vTarget):
                number_of_features += 1

        if Conditions.LessLife != 0:
            if Routines.Checks.Agents.GetHealth(vTarget) < Conditions.LessLife:
                number_of_features += 1

        if Conditions.MoreLife != 0:
            if Routines.Checks.Agents.GetHealth(vTarget) > Conditions.MoreLife:
                number_of_features += 1
        
        if Conditions.LessEnergy != 0:
            from .utils import GetEnergyValues
            if self.IsPartyMember(vTarget):
                player_energy = GetEnergyValues(vTarget)
                if player_energy < Conditions.LessEnergy:
                    number_of_features += 1
            else:
                number_of_features += 1 #henchmen, allies, pets or something else thats not reporting energy

        if Conditions.LessSelfEnergyPercentage > 0:
            # Agent.GetEnergy returns a 0.0-1.0 fraction of max energy; threshold uses the same scale.
            if Agent.GetEnergy(Player.GetAgentID()) <= Conditions.LessSelfEnergyPercentage:
                number_of_features += 1

        if Conditions.Overcast != 0:
            if Player.GetAgentID() == vTarget:
                if Agent.GetOvercast(vTarget) < Conditions.Overcast:
                    number_of_features += 1
                    
        if Conditions.IsPartyWide:
            from .utils import SameMapAsAccount

            cached_data = self.cached_data
            if cached_data is None:
                return False

            area = Range.SafeCompass.value if Conditions.PartyWideArea == 0 else Conditions.PartyWideArea
            less_life = Conditions.LessLife
            player_x, player_y = Player.GetXY()
            area_sq = area * area

            total_group_life = 0.0
            total_group_members = 0

            for acc in cached_data.party:
                if not acc.IsSlotActive:
                    continue
                if acc.AgentPartyData.PartyID != cached_data.party.party_id:
                    continue
                if not SameMapAsAccount(acc):
                    continue

                max_health = float(acc.AgentData.Health.Max or 0.0)
                current_health = float(acc.AgentData.Health.Current or 0.0)
                if max_health <= 0.0 or current_health <= 0.0:
                    continue

                dx = float(acc.AgentData.Pos.x) - player_x
                dy = float(acc.AgentData.Pos.y) - player_y
                if (dx * dx) + (dy * dy) > area_sq:
                    continue

                total_group_life += current_health / max_health
                total_group_members += 1

            if total_group_members == 0:
                return False

            if (total_group_life / total_group_members) < less_life:
                number_of_features += 1
                                    
        if Conditions.RequiresSpiritInEarshot:            
            if Routines.Agents.GetNearestSpirit(Range.Earshot.value) != 0:
                number_of_features += 1
                    
        player_pet_id = 0
        def get_player_pet_id() -> int:
            nonlocal player_pet_id
            if player_pet_id == 0:
                player_pet_id = GLOBAL_CACHE.Party.Pets.GetPetID(Player.GetAgentID())
            return player_pet_id
        
        if self.skills[slot].custom_skill_data.TargetAllegiance == Skilltarget.Pet.value:
            pet_id = get_player_pet_id()
            if pet_id == 0 or Routines.Checks.Agents.IsDead(pet_id):
                return False
            
            if self.skills[slot].custom_skill_data.Nature == SkillNature.Buff.value:
                if self.HasEffect(pet_id, self.skills[slot].skill_id):
                    return False
            
        if self.skills[slot].custom_skill_data.SkillType == SkillType.PetAttack.value:
            pet_id = get_player_pet_id()
            if Routines.Checks.Agents.IsDead(pet_id):
                return False

            for skill_id in self.pet_attack_list:
                if self.skills[slot].skill_id == skill_id:
                    if self.HasEffect(pet_id,self.skills[slot].skill_id ):
                        return False
            
        if Conditions.EnemyCount != 0:
            player_pos = Player.GetXY()
            enemy_array = Routines.Agents.GetFilteredEnemyArray(player_pos[0], player_pos[1], Conditions.EnemiesInRange)
            if len(enemy_array) >= Conditions.EnemyCount:
                number_of_features += 1
            else:
                return False
                
        if Conditions.AlliesInRange != 0:
            player_pos = Player.GetXY()
            ally_array = ally_array = Routines.Agents.GetFilteredAllyArray(player_pos[0], player_pos[1], Conditions.AlliesInRangeArea,other_ally=True)
            if len(ally_array) >= Conditions.AlliesInRange:
                number_of_features += 1
            else:
                return False
                
        if Conditions.SpiritsInRange != 0:
            player_pos = Player.GetXY()
            ally_array = ally_array = Routines.Agents.GetFilteredSpiritArray(player_pos[0], player_pos[1], Conditions.SpiritsInRangeArea)
            if len(ally_array) >= Conditions.SpiritsInRange:
                number_of_features += 1
            else:
                return False
                
        if Conditions.MinionsInRange != 0:
            player_pos = Player.GetXY()
            ally_array = ally_array = Routines.Agents.GetFilteredMinionArray(player_pos[0], player_pos[1], Conditions.MinionsInRangeArea)
            if len(ally_array) >= Conditions.MinionsInRange:
                number_of_features += 1
            else:
                return False

        if Conditions.CloseToAggro:
            if Routines.Checks.Agents.InAggro(self.get_combat_distance()) or Routines.Checks.Agents.IsCloseToAggro():
                number_of_features += 1
            else:
                return False
            

        #Py4GW.Console.Log("AreCastConditionsMet", f"feature count: {feature_count}, No of features {number_of_features}", Py4GW.Console.MessageType.Info)
        
        if feature_count == number_of_features:
            return True

        return False


    def SpiritBuffExists(self, skill_id: int) -> bool:
        if skill_id not in SPIRIT_BUFF_SKILL_IDS:
            return False

        if self.active_spirit_buff_skill_ids is None:
            self.active_spirit_buff_skill_ids = self._get_active_spirit_buff_skill_ids()

        return skill_id in self.active_spirit_buff_skill_ids

    def IsReadyToCast(self, slot: int) -> tuple[bool, int]:

        #return False, 0 
        
        skill = self.skills[slot]
        skillbar_data = skill.skillbar_data
        skill_id = skill.skill_id
        conditions = skill.custom_skill_data.Conditions
        target_allegiance = skill.custom_skill_data.TargetAllegiance

        # Check if no skill is assigned to the slot
        if skill_id == 0:
            self.in_casting_routine = False
            return False, 0

        # Check if the skill is recharging
        if skillbar_data.recharge != 0:
            self.in_casting_routine = False
            return False, 0

        player_id = Player.GetAgentID()
        player_is_casting = Agent.IsCasting(player_id)

        if player_is_casting:
            self.in_casting_routine = False
            return False, 0
        
        skillbar_casting = GLOBAL_CACHE.SkillBar.GetCasting() or 0
        
        if skillbar_casting != 0:
            self.in_casting_routine = False
            return False, 0
        
        # Check if there is enough adrenaline
        adrenaline_required = GLOBAL_CACHE.Skill.Data.GetAdrenaline(skill_id)
        if adrenaline_required > 0 and skillbar_data.adrenaline_a < adrenaline_required:
            self.in_casting_routine = False
            return False, 0

        # Cannot cast spells while Vow of Silence is active
        skill_type, _ = GLOBAL_CACHE.Skill.GetType(skill_id)
        if skill_type in VOW_SPELL_TYPES and Routines.Checks.Effects.HasBuff(player_id, 1517):
            self.in_casting_routine = False
            return False, 0

        # Check if there is enough energy
        current_hp = Agent.GetHealth(Player.GetAgentID())
        current_energy = self.GetEnergyValues(Player.GetAgentID()) * Agent.GetMaxEnergy(Player.GetAgentID())

        energy_cost = Routines.Checks.Skills.GetEnergyCostWithEffects(skill_id, player_id)

        if self.expertise_exists:
            energy_cost = Routines.Checks.Skills.apply_expertise_reduction(energy_cost, self.expertise_level, skill_id)

        if current_energy < energy_cost:
            self.in_casting_routine = False
            return False, 0

        # Check if there is enough health
        target_hp = conditions.SacrificeHealth
        health_cost = GLOBAL_CACHE.Skill.Data.GetHealthCost(skill_id)
        if (current_hp < target_hp) and health_cost > 0:
            self.in_casting_routine = False
            return False, 0

        # Opt-in post-sacrifice safety floors. Only applied when the skill sets at least one floor
        # above 0. Sacrifice amount is derived from SacrificePercent (fraction of max HP).
        # Refuses to cast unless the caster's HP after sacrifice is strictly greater than BOTH
        # the percent-of-max floor AND the absolute-HP floor.
        min_after_pct = getattr(conditions, "MinHealthAfterSacrificePercent", 0.0)
        min_after_abs = getattr(conditions, "MinHealthAfterSacrificeAbsolute", 0)
        sacrifice_pct = getattr(conditions, "SacrificePercent", 0.0)
        if sacrifice_pct > 0 and (min_after_pct > 0 or min_after_abs > 0):
            max_hp = Agent.GetMaxHealth(Player.GetAgentID())
            sacrifice_amount = max_hp * sacrifice_pct
            hp_after_sacrifice = (current_hp * max_hp) - sacrifice_amount
            if min_after_abs > 0 and hp_after_sacrifice <= min_after_abs:
                self.in_casting_routine = False
                return False, 0
            if min_after_pct > 0 and max_hp > 0 and (hp_after_sacrifice / max_hp) <= min_after_pct:
                self.in_casting_routine = False
                return False, 0

        # --- Expensive target resolution (only if all cheap checks passed) ---
        v_target = self.GetAppropiateTarget(slot)

        if v_target is None or v_target == 0:
            self.in_casting_routine = False
            return False, 0

        # --- Target-dependent checks ---

        # Check combo conditions
        combo_type = GLOBAL_CACHE.Skill.Data.GetCombo(skill_id)
        dagger_status = Agent.GetDaggerStatus(v_target)
        if ((combo_type == 1 and dagger_status not in (0, 3)) or
            (combo_type == 2 and dagger_status != 1) or
            (combo_type == 3 and dagger_status != 2)):
            self.in_casting_routine = False
            return False, v_target
        
        # Check spirit buff (target-independent)
        if self.SpiritBuffExists(skill_id):
            self.in_casting_routine = False
            return False, 0

        # Check if effect already exists on target (uses shared memory for party members)
        exact_weapon_spell = (
            skill_type == SkillType.WeaponSpell.value
            and conditions.AllowOverlapWeaponSpell
        )
        if (
            target_allegiance != Skilltarget.NonWeaponSpelledAlly.value
            and self.HasEffect(v_target, skill_id, exact_weapon_spell=exact_weapon_spell)
        ):
            self.in_casting_routine = False
            return False, v_target

        # Check if the skill has the required conditions
        if not self.AreCastConditionsMet(slot, v_target):
            self.in_casting_routine = False
            return False, v_target

        return True, v_target

    def IsOOCSkill(self, slot: int) -> bool:
        if self.skills[slot].custom_skill_data.Conditions.IsOutOfCombat:
            return True

        skill_type = self.skills[slot].custom_skill_data.SkillType
        skill_nature = self.skills[slot].custom_skill_data.Nature

        if(skill_nature == SkillNature.Healing.value or
           skill_nature == SkillNature.Hex_Removal.value or
           skill_nature == SkillNature.Condi_Cleanse.value or
           skill_nature == SkillNature.EnergyBuff.value or
           skill_nature == SkillNature.Resurrection.value
        ):
            return True

        return False

    def ChooseTarget(self, interact: bool = True) -> bool:       
        if not self.is_targeting_enabled:
            return False

        if not self.in_aggro:
            return False

            
        called_target = self.GetPartyTarget()
        #if Agent.IsAlive(called_target):
        if called_target != 0:
            self.SafeInteract(called_target)
            return True
            
        nearest = Routines.Agents.GetNearestEnemy(self.get_combat_distance())
        if nearest != 0:
            self.SafeInteract(nearest)
            return True

        return False

    def HandleAutoAttack(self, cached_data: CacheData | None) -> bool:
        if cached_data is None or not self.is_combat_enabled or self.in_casting_routine:
            return False

        player_id = Player.GetAgentID()
        if Agent.IsHoldingItem(player_id):
            return False

        cached_data.auto_attack_time = cached_data.GetWeaponAttackAftercast()

        target_id = Player.GetTargetID()
        _, target_allegiance = Agent.GetAllegiance(target_id)

        if target_id == 0 or Agent.IsDead(target_id) or (target_allegiance != "Enemy"):
            if self.ChooseTarget():
                self.MaybeCallCombatTarget(Player.GetTargetID(), cached_data)
                cached_data.auto_attack_time = cached_data.GetWeaponAttackAftercast()
                cached_data.auto_attack_timer.Reset()
                return True

        if (
            cached_data.auto_attack_timer.HasElapsed(cached_data.auto_attack_time)
            and cached_data.data.weapon_type != 0
        ):
            if self.ChooseTarget():
                self.MaybeCallCombatTarget(Player.GetTargetID(), cached_data)
                cached_data.auto_attack_time = cached_data.GetWeaponAttackAftercast()
                cached_data.auto_attack_timer.Reset()
                self.ResetSkillPointer()
                return True

        return False
        
        
        
    def GetWeaponAttackAftercast(self) -> int:
        """
        Returns the attack speed of the current weapon.
        """
        weapon_type,_ = Agent.GetWeaponType(Player.GetAgentID())
        player_living = Agent.GetLivingAgentByID(Player.GetAgentID())
        if player_living is None:
            return 0
        
        attack_speed = player_living.weapon_attack_speed
        attack_speed_modifier = player_living.attack_speed_modifier if player_living.attack_speed_modifier != 0 else 1.0
        
        if attack_speed == 0:
            match weapon_type:
                case Weapon.Bow.value:
                    attack_speed = 2.475
                case Weapon.Axe.value:
                    attack_speed = 1.33
                case Weapon.Hammer.value:
                    attack_speed = 1.75
                case Weapon.Daggers.value:
                    attack_speed = 1.33
                case Weapon.Scythe.value:
                    attack_speed = 1.5
                case Weapon.Spear.value:
                    attack_speed = 1.5
                case Weapon.Sword.value:
                    attack_speed = 1.33
                case Weapon.Scepter.value:
                    attack_speed = 1.75
                case Weapon.Scepter2.value:
                    attack_speed = 1.75
                case Weapon.Wand.value:
                    attack_speed = 1.75
                case Weapon.Staff1.value:
                    attack_speed = 1.75
                case Weapon.Staff.value:
                    attack_speed = 1.75
                case Weapon.Staff2.value:
                    attack_speed = 1.75
                case Weapon.Staff3.value:
                    attack_speed = 1.75
                case _:
                    attack_speed = 1.75
                    
        return int((attack_speed / attack_speed_modifier) * 1000)

    def FindCastableSkill(self, ooc: bool = False) -> tuple[int, int]:
        """
        Scan the prioritized skill list and return the first castable skill slot
        together with its resolved target. Returns (-1, 0) if nothing is castable.
        """
        for slot in range(MAX_SKILLS):
            if not self.IsSkillReady(slot):
                continue

            if ooc and not self.IsOOCSkill(slot):
                continue

            is_ready_to_cast, target_agent_id = self.IsReadyToCast(slot)
            if not is_ready_to_cast or target_agent_id == 0:
                continue

            if not Agent.IsLiving(target_agent_id):
                continue

            return slot, target_agent_id

        return -1, 0

    def GetDrunkLevel(self) -> int:
        """
        Get current drunk level (0-5). Returns 0 if unable to determine.
        """
        try:
            level = Effects.GetAlcoholLevel()
            return max(0, min(5, int(level)))
        except Exception:
            pass
        return 0

    def UseAlcoholIfAvailable(self) -> bool:
        """
        Checks inventory for alcohol and uses the first available one.
        Level 1 is sufficient; L3 items are used first for a bigger bonus when available.
        Returns True if alcohol was used, False otherwise.
        """
        try:
            # Check if already at target drunk level (>= 1 is enough)
            drunk_level = self.GetDrunkLevel()
            Py4GW.Console.Log("HeroAI", f"Drunken Master: drunk level = {drunk_level}", Py4GW.Console.MessageType.Debug)

            if drunk_level >= 1:
                Py4GW.Console.Log("HeroAI", f"Already drunk (level {drunk_level}), skipping alcohol", Py4GW.Console.MessageType.Debug)
                return False
            
            for alcohol_model_id in ALCOHOL_MODEL_IDS:
                if GLOBAL_CACHE.Inventory.GetModelCount(alcohol_model_id) > 0:
                    item_id = GLOBAL_CACHE.Item.GetItemIdFromModelID(alcohol_model_id)
                    if item_id:
                        Py4GW.Console.Log("HeroAI", f"Using alcohol item_id {item_id}", Py4GW.Console.MessageType.Info)
                        GLOBAL_CACHE.Inventory.UseItem(item_id)
                        return True
            
            Py4GW.Console.Log("HeroAI", "No alcohol found in inventory", Py4GW.Console.MessageType.Debug)
        except Exception as e:
            Py4GW.Console.Log("HeroAI", f"Error in UseAlcoholIfAvailable: {e}", Py4GW.Console.MessageType.Warning)
        return False

    def _skill_lock_enabled(self, skill: SkillData) -> bool:
        custom_skill = getattr(skill, "custom_skill_data", None)
        return bool(getattr(custom_skill, "SkillLock", False))

    def _skill_lock_extra_ms(self, skill: SkillData) -> int:
        custom_skill = getattr(skill, "custom_skill_data", None)
        try:
            return max(0, int(getattr(custom_skill, "SkillLockAftercastMs", 0) or 0))
        except (TypeError, ValueError):
            return 0

    def _skill_lock_is_blocked(self, skill: SkillData) -> bool:
        if not self._skill_lock_enabled(skill):
            return False
        try:
            from Py4GWCoreLib.enums_src.Whiteboard_enums import (
                WhiteboardClaimStrength,
                WhiteboardLockKind,
                WhiteboardLockMode,
                WhiteboardReentryPolicy,
            )

            email = Player.GetAccountEmail() or ""
            if not email:
                return False
            group_id = GLOBAL_CACHE.ShMem.GetAccountGroupByEmail(email)
            now = Py4GW.Game.get_tick_count64()
            return GLOBAL_CACHE.ShMem.IsLockBlocked(
                int(WhiteboardLockKind.COOLDOWN),
                int(skill.skill_id),
                0,
                int(group_id),
                email,
                int(now),
                int(WhiteboardLockMode.EXCLUSIVE),
                1,
                int(WhiteboardReentryPolicy.OWNER_REENTRANT),
                int(WhiteboardClaimStrength.HARD),
            )
        except Exception:
            return False

    def _skill_lock_post(self, skill: SkillData) -> None:
        if not self._skill_lock_enabled(skill):
            return
        try:
            from Py4GWCoreLib.GlobalCache.shared_memory_src.Globals import (
                SHMEM_INTENT_DEFAULT_PING_BUDGET_MS,
            )
            from Py4GWCoreLib.enums_src.Whiteboard_enums import (
                WhiteboardClaimStrength,
                WhiteboardLockKind,
                WhiteboardLockMode,
                WhiteboardReentryPolicy,
            )

            email = Player.GetAccountEmail() or ""
            if not email:
                return
            activation_ms = int((GLOBAL_CACHE.Skill.Data.GetActivation(skill.skill_id) or 0) * 1000)
            aftercast_ms = int((GLOBAL_CACHE.Skill.Data.GetAftercast(skill.skill_id) or 0) * 1000)
            extra_ms = self._skill_lock_extra_ms(skill)
            lease_ms = (
                max(SKILL_LOCK_MIN_LEASE_MS, activation_ms + aftercast_ms)
                + extra_ms
                + int(SHMEM_INTENT_DEFAULT_PING_BUDGET_MS)
            )
            expires_at = int(Py4GW.Game.get_tick_count64()) + int(lease_ms)
            GLOBAL_CACHE.ShMem.PostLock(
                email,
                int(WhiteboardLockKind.COOLDOWN),
                int(skill.skill_id),
                0,
                int(expires_at),
                None,
                int(WhiteboardLockMode.EXCLUSIVE),
                1,
                int(WhiteboardReentryPolicy.OWNER_REENTRANT),
                int(WhiteboardClaimStrength.HARD),
            )
        except Exception:
            pass

    def HandleCombat(self, cached_data: CacheData | None = None, ooc: bool = False) -> bool:
        """
        Execute the first castable skill in the prioritized skill order.
        """
        slot, target_agent_id = self.FindCastableSkill(ooc=ooc)
        if slot < 0:
            self.ResetSkillPointer()
            return self.HandleAutoAttack(cached_data) if not ooc else False

        self.SetSkillPointer(slot)
        skill_id = self.skills[slot].skill_id
        
        # Auto-use alcohol before alcohol-dependent PVE skills for optimal effect
        if skill_id in self.alcohol_skills:
            #Py4GW.Console.Log("HeroAI", f"Detected alcohol-dependent skill, checking for alcohol...", Py4GW.Console.MessageType.Info)
            self.UseAlcoholIfAvailable()
            
        self.in_casting_routine = True
        self.aftercast = 250
        skill = self.skills[slot]
        if skill.custom_skill_data.Nature == SkillNature.Resurrection.value:
            self.aftercast = 500

        if self._skill_lock_is_blocked(skill):
            self.ResetSkillPointer()
            return False

        self.aftercast_timer.Reset()
        self._apply_spike_lock(skill, target_agent_id)
        self._skill_lock_post(skill)
        GLOBAL_CACHE.SkillBar.UseSkill(self.skill_order[slot]+1, target_agent_id, aftercast_delay=self.aftercast)
        self.ResetSkillPointer()
        return True
