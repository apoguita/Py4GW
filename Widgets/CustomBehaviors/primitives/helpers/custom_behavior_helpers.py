import time
from collections.abc import Generator
from dataclasses import dataclass
from functools import reduce
from typing import Any, Callable, Optional, Tuple

from Py4GWCoreLib.GlobalCache.SharedMemory import AccountData
from Py4GWCoreLib.enums_src.Model_enums import GadgetModelID
from Py4GWCoreLib.py4gwcorelib_src.Timer import Timer
from Widgets.CustomBehaviors.primitives.helpers import custom_behavior_helpers_tests
from Widgets.CustomBehaviors.primitives.helpers.behavior_result import BehaviorResult
from Widgets.CustomBehaviors.primitives.helpers.targeting_order import TargetingOrder
from Widgets.CustomBehaviors.primitives.skills.custom_skill import CustomSkill

from Py4GWCoreLib import GLOBAL_CACHE, Overlay, SkillBar, ActionQueueManager, Routines, Range, Utils, SPIRIT_BUFF_MAP, SpiritModelID, AgentArray
from Widgets.CustomBehaviors.primitives import constants

MODULE_NAME = "Custom Combat Behavior Helpers"

@dataclass
class SortableAgentData:
    agent_id: int
    distance_from_player: float
    hp: float
    is_caster: bool
    is_melee: bool
    is_martial: bool
    enemy_quantity_within_range: int
    agent_quantity_within_range: int
    energy: float

@dataclass
class SpiritAgentData:
    agent_id: int
    distance_from_player: float
    hp: float

@dataclass
class GravityCenter:
    coordinates: tuple[float, float]
    agent_covered_count: int
    distance_from_player: float

class Helpers:

    @staticmethod
    def interleave_generators(*generators):
        """
        Alternate between generators in a round-robin manner.
        """
        iterators = [iter(gen) for gen in generators]
        while iterators:
            for it in iterators[:]:
                try:
                    yield next(it)
                except StopIteration:
                    iterators.remove(it)

    @staticmethod
    def wait_for(milliseconds) -> Generator[Any, Any, Any]:
        start_time = time.time()

        while (time.time() - start_time) < milliseconds / 1000:
            yield 'wait'  # Pause and allow resumption while waiting
        return

    @staticmethod
    def delay_aftercast(skill_casted: CustomSkill) -> Generator[Any, Any, Any]:

        activation_time = GLOBAL_CACHE.Skill.Data.GetActivation(skill_casted.skill_id) * 1000
        aftercast = GLOBAL_CACHE.Skill.Data.GetAftercast(skill_casted.skill_id) * 1000
        delay = activation_time if activation_time > aftercast else aftercast
        if constants.DEBUG: print(f"{skill_casted.skill_name} let's wait for aftercast :{delay}ms | activation_time:{activation_time} | aftercast:{aftercast}")

        yield from Helpers.wait_for(delay + 200)  # 200ms more to really avoid double-cast

    @staticmethod
    def wait_for_or_until_completion(milliseconds: int, action: Callable[[], Generator[Any, Any, BehaviorResult]]) -> Generator[Any, Any, BehaviorResult]:
        start_time = time.time()

        while (time.time() - start_time) < milliseconds / 1000:
            action_result: BehaviorResult = yield from action()
            if action_result == BehaviorResult.ACTION_PERFORMED:
                if constants.DEBUG: print(f"wait_for_or_until_completion has reached completion : {milliseconds}ms")
                return BehaviorResult.ACTION_PERFORMED
            yield 'wait'  # Pause and allow resumption while waiting
        return BehaviorResult.ACTION_SKIPPED

    @staticmethod
    def wait_for_condition_before_execution(
        milliseconds: int, 
        action: Callable[[], Generator[Any, Any, BehaviorResult]], 
        condition_check: Callable[[], bool]) -> Generator[Any, Any, BehaviorResult]:
        '''
        wait for a condition to be met before executing an action
        '''
        
        start_time = time.time()

        while (time.time() - start_time) < milliseconds / 1000:
            is_condition_met: bool = condition_check()

            if is_condition_met == False:
                return BehaviorResult.ACTION_SKIPPED
            
            yield from Helpers.wait_for(100)

        if constants.DEBUG: print(f"wait_for_condition_before_execution has reached completion : {milliseconds}ms")
        action_result: BehaviorResult = yield from action()
        return action_result

class Resources:

    @staticmethod
    def get_nearest_dungeon_chest(max_distance: int) -> int | None:
        
        valid_chest_ids = [
            GadgetModelID.CHEST_DUNGEON_SECRET_LAIR_OF_THE_SNOWMAN.value,
            GadgetModelID.CHEST_DUNGEON_BOGROOT_GROWTHS.value,
            GadgetModelID.CHEST_DUNGEON_SLAVERS_EXILE_JUSTICIAR_THOMMIS_ROOM.value,

            GadgetModelID.BURIED_TREASURE_THE_MIRROR_OF_LYSS.value,
        ]

        gadget_array = AgentArray.GetGadgetArray()
        gadget_array = AgentArray.Filter.ByDistance(gadget_array, GLOBAL_CACHE.Player.GetXY(), max_distance)
        gadget_array = AgentArray.Sort.ByDistance(gadget_array, GLOBAL_CACHE.Player.GetXY())

        for agent_id in gadget_array:
            gadget_id = GLOBAL_CACHE.Agent.GetGadgetID(agent_id)
            if gadget_id in valid_chest_ids:
                return agent_id

        return None
    
    @staticmethod
    def get_nearest_locked_chest(max_distance: int) -> int | None:
        
        valid_chest_ids = [
            GadgetModelID.CHEST_HIDDEN_STASH.value,
            GadgetModelID.CHEST_ASCALONIAN.value,
            GadgetModelID.CHEST_SHING_JEA.value,
            GadgetModelID.CHEST_GENERIC.value,
        ]

        gadget_array = AgentArray.GetGadgetArray()
        gadget_array = AgentArray.Filter.ByDistance(gadget_array, GLOBAL_CACHE.Player.GetXY(), max_distance)
        gadget_array = AgentArray.Sort.ByDistance(gadget_array, GLOBAL_CACHE.Player.GetXY())

        for agent_id in gadget_array:
            gadget_id = GLOBAL_CACHE.Agent.GetGadgetID(agent_id)
            if gadget_id in valid_chest_ids:
                return agent_id

        return None


    @staticmethod
    def is_player_holding_an_item() -> bool:
        weapon_type, _ = GLOBAL_CACHE.Agent.GetWeaponType(GLOBAL_CACHE.Player.GetAgentID())
        if weapon_type == 0:
            return True
        return False
    
    @staticmethod
    def is_party_dead() -> bool:
        players = GLOBAL_CACHE.Party.GetPlayers()
        for player in players:
            agent_id = GLOBAL_CACHE.Party.Players.GetAgentIDByLoginNumber(player.login_number)
            if GLOBAL_CACHE.Agent.IsDead(agent_id) == False:
                return False
        return True

    @staticmethod
    def has_enough_resources(skill_casted: CustomSkill):
        player_agent_id = GLOBAL_CACHE.Player.GetAgentID()

        adrenaline_required = GLOBAL_CACHE.Skill.Data.GetAdrenaline(skill_casted.skill_id)
        adrenaline_a = GLOBAL_CACHE.SkillBar.GetSkillData(skill_casted.skill_slot).adrenaline_a
        has_enough_adrenaline = True
        if adrenaline_required > 0 and adrenaline_a < adrenaline_required:
            has_enough_adrenaline = False

        player_life = Resources.get_player_absolute_health()
        skill_life = GLOBAL_CACHE.Skill.Data.GetHealthCost(skill_casted.skill_id)
        has_enough_life = True if player_life * 0.95 >= skill_life else False

        energy_cost_with_effect = Resources.__get_true_cost(skill_casted)
        player_energy = Resources.get_player_absolute_energy()
        has_enough_energy = True if player_energy >= energy_cost_with_effect else False

        return has_enough_adrenaline and has_enough_life and has_enough_energy

    @staticmethod
    def __get_true_cost(skill: CustomSkill) -> float:
        '''
        should be part of core libs (fix GetEnergyCostWithEffects)
        '''

        player_agent_id = GLOBAL_CACHE.Player.GetAgentID()

        def get_attribute_level(attribute_name):
            attributes = GLOBAL_CACHE.Agent.GetAttributes(player_agent_id)
            for attr in attributes:
                if attr.GetName() == attribute_name:
                    return attr.level
            return 0

        energy_cost = Routines.Checks.Skills.GetEnergyCostWithEffects(skill.skill_id, player_agent_id)
        profession = GLOBAL_CACHE.Agent.GetProfessionNames(player_agent_id)[0]
        skill_type = GLOBAL_CACHE.Skill.GetType(skill.skill_id)[1]

        if profession == "Dervish" and skill_type == "Enchantment":
            mysticism_level = get_attribute_level("Mysticism")
            energy_cost = round((1 - (mysticism_level * 0.04)) * energy_cost)
            return energy_cost

        if profession == "Ranger":
            energy_cost = Routines.Checks.Skills.apply_expertise_reduction(energy_cost, get_attribute_level("Expertise"), skill.skill_id)

        return energy_cost

    @staticmethod
    def get_energy_percent_in_party(agent_id):

        accounts:list[AccountData] = GLOBAL_CACHE.ShMem.GetAllAccountData()
        for account in accounts:
            if agent_id == account.PlayerID:
                return account.PlayerEnergy
        return 1.0  # default return full energy to prevent issues

    @staticmethod
    def get_player_absolute_health() -> float:
        player_agent_id = GLOBAL_CACHE.Player.GetAgentID()
        current_heath_percent = GLOBAL_CACHE.Agent.GetHealth(player_agent_id)
        heath_max = GLOBAL_CACHE.Agent.GetMaxHealth(player_agent_id)
        return current_heath_percent * heath_max

    @staticmethod
    def get_player_absolute_energy() -> float:
        player_agent_id = GLOBAL_CACHE.Player.GetAgentID()
        current_energy_percent = GLOBAL_CACHE.Agent.GetEnergy(player_agent_id)
        energy_max = GLOBAL_CACHE.Agent.GetMaxEnergy(player_agent_id)
        return current_energy_percent * energy_max

    @staticmethod
    def player_can_sacrifice_health(
        percentage_to_sacrifice: int,
        min_health_percent_left = 0.3,
        min_health_absolute_left = 175,
    ) -> bool:
        player_max_health = GLOBAL_CACHE.Agent.GetMaxHealth(GLOBAL_CACHE.Player.GetAgentID())
        amount_we_will_sacrifice = player_max_health * percentage_to_sacrifice / 100
        player_current_health = Resources.get_player_absolute_health()
        health_after_sacrifice = player_current_health - amount_we_will_sacrifice

        return (health_after_sacrifice > min_health_absolute_left
                and health_after_sacrifice / player_max_health > min_health_percent_left)

    @staticmethod
    def is_spirit_exist(
            within_range: Range,
            associated_to_skill: Optional[CustomSkill] = None,
            condition: Optional[Callable[[int], bool]] = None) -> bool:

        spirit_array = GLOBAL_CACHE.AgentArray.GetSpiritPetArray()
        spirit_array = AgentArray.Filter.ByDistance(spirit_array, GLOBAL_CACHE.Player.GetXY(), within_range.value)
        spirit_array = AgentArray.Filter.ByCondition(spirit_array, lambda agent_id: GLOBAL_CACHE.Agent.IsAlive(agent_id))
        spirit_array = AgentArray.Filter.ByCondition(spirit_array, lambda agent_id: GLOBAL_CACHE.Agent.IsSpawned(agent_id))
        
        if condition is not None:
            spirit_array = AgentArray.Filter.ByCondition(spirit_array, condition)

        if associated_to_skill is not None:
            for spirit_id in spirit_array:
                model_value = GLOBAL_CACHE.Agent.GetPlayerNumber(spirit_id)

                # Check if model_value is valid for SpiritModelID Enum
                if model_value in SpiritModelID._value2member_map_:
                    spirit_model_id = SpiritModelID(model_value)
                    if SPIRIT_BUFF_MAP.get(spirit_model_id) == associated_to_skill.skill_id:
                        return True
            return False

        return len(spirit_array) > 0
    
    @staticmethod
    def is_ally_under_specific_effect(agent_id: int, skill_id: int) -> bool:
        if agent_id == GLOBAL_CACHE.Player.GetAgentID() :
            # if target is the player, check if the player has the effect
            has_buff: bool = Routines.Checks.Effects.HasBuff(GLOBAL_CACHE.Player.GetAgentID(), skill_id)
            return has_buff
        else:
            # else check if the party target has the effect
            # we should also deep dive inside player.pet

            accounts:list[AccountData] = GLOBAL_CACHE.ShMem.GetAllAccountData()
            for account in accounts:
                if account.PlayerID == agent_id:

                    for buff in account.PlayerBuffs:
                        if buff.SkillId == skill_id:
                            return True

        return False

class Actions:

    @staticmethod
    def player_drop_item_if_possible() -> Generator[Any, Any, BehaviorResult]:
        if not Resources.is_player_holding_an_item():
            yield
            return BehaviorResult.ACTION_SKIPPED

        from Py4GWCoreLib import UIManager
        all_ids = UIManager.GetAllChildFrameIDs(5040781, [0, 0])
        exist = UIManager.FrameExists(all_ids[0])
        if exist:
            UIManager.FrameClick(all_ids[0])
            yield from Helpers.wait_for(100)
            return BehaviorResult.ACTION_PERFORMED

        return BehaviorResult.ACTION_SKIPPED

    @staticmethod
    def auto_attack(target_id: Optional[int] = None) -> Generator[Any, Any, Any]:

        if GLOBAL_CACHE.Agent.IsAttacking(GLOBAL_CACHE.Player.GetAgentID()):
            yield
            return BehaviorResult.ACTION_SKIPPED

        if target_id is None:
            target_id = Targets.get_nearest_or_default_from_enemy_ordered_by_priority(Range.Spellcast.value)

        if not GLOBAL_CACHE.Agent.IsValid(target_id):
            return None

        GLOBAL_CACHE.Player.ChangeTarget(target_id)
        yield from Helpers.wait_for(100) 
        GLOBAL_CACHE.Player.Interact(target_id, False)
        yield from Helpers.wait_for(100)
        return BehaviorResult.ACTION_PERFORMED

    @staticmethod
    def cast_skill_to_lambda(skill: CustomSkill, select_target: Optional[Callable[[], int]]) -> Generator[Any, Any, BehaviorResult]:

        if not Routines.Checks.Skills.IsSkillSlotReady(skill.skill_slot):
            yield
            return BehaviorResult.ACTION_SKIPPED

        if not Resources.has_enough_resources(skill):
            yield
            return BehaviorResult.ACTION_SKIPPED

        target_agent_id: int | None = None

        if select_target is not None:
            selected_target = select_target()
            if selected_target is None:
                yield
                return BehaviorResult.ACTION_SKIPPED
            target_agent_id = selected_target

        if target_agent_id is not None: 
            GLOBAL_CACHE.Player.ChangeTarget(target_agent_id)
            yield from Helpers.wait_for(50)
            
        Routines.Sequential.Skills.CastSkillSlot(skill.skill_slot)
        if constants.DEBUG: print(f"cast_skill_to_target {skill.skill_name} to {target_agent_id}")
        yield from Helpers.delay_aftercast(skill)
        return BehaviorResult.ACTION_PERFORMED

    @staticmethod
    def cast_skill_to_target(skill: CustomSkill, target_agent_id: int) -> Generator[Any, Any, BehaviorResult]:
        return (yield from Actions.cast_skill_to_lambda(skill, select_target=lambda: target_agent_id))

    @staticmethod
    def cast_skill(skill: CustomSkill) -> Generator[Any, Any, BehaviorResult]:
        return (yield from Actions.cast_skill_to_lambda(skill, select_target=None))

    @staticmethod
    def cast_skill_generic_heroai(skill: CustomSkill) -> Generator[Any, Any, BehaviorResult]:
        from HeroAI.cache_data import CacheData
        cached_data = CacheData()
        if cached_data.combat_handler is None: print("combat_handler is None")
        if cached_data.combat_handler.skills is None:
            try:
                cached_data.combat_handler.PrioritizeSkills()
                print(f"PrioritizeSkills")
            except Exception as e:
                print(f"echec {e}")
        if cached_data.combat_handler.skills is None:
            print("combat_handler.skills is None")
            yield
            return BehaviorResult.ACTION_SKIPPED

        def find_order():
            for index, generic_skill in enumerate(cached_data.combat_handler.skills):
                if generic_skill.skill_id == skill.skill_id:
                    return index  # Returning order (1-based index)
            return -1  # Return -1 if skill_id not found

        order = find_order()
        is_ready_to_cast, target_agent_id = cached_data.combat_handler.IsReadyToCast(order)
        

        if not is_ready_to_cast:
            yield
            return BehaviorResult.ACTION_SKIPPED

        # option1
        if target_agent_id is not None: 
            GLOBAL_CACHE.Player.ChangeTarget(target_agent_id)
            yield from Helpers.wait_for(50)


        Routines.Sequential.Skills.CastSkillID(skill.skill_id)
        # option2
        # ActionQueueManager().AddAction("ACTION", SkillBar.UseSkill, skill_slot, target_agent_id)
        if constants.DEBUG: print(f"cast_skill_to_target {skill.skill_name} to {target_agent_id}")
        yield from Helpers.delay_aftercast(skill)
        return BehaviorResult.ACTION_PERFORMED

    @staticmethod
    def cast_effect_before_expiration(skill: CustomSkill, time_before_expire: int) -> Generator[Any, Any, BehaviorResult]:
        if not Routines.Checks.Skills.IsSkillSlotReady(skill.skill_slot):
            yield
            return BehaviorResult.ACTION_SKIPPED

        if not Resources.has_enough_resources(skill):
            yield
            return BehaviorResult.ACTION_SKIPPED

        has_buff = Routines.Checks.Effects.HasBuff(GLOBAL_CACHE.Player.GetAgentID(), skill.skill_id)
        buff_time_remaining = GLOBAL_CACHE.Effects.GetEffectTimeRemaining(GLOBAL_CACHE.Player.GetAgentID(), skill.skill_id) if has_buff else 0
        if not has_buff or buff_time_remaining <= time_before_expire:
            ActionQueueManager().AddAction("ACTION", SkillBar.UseSkill, skill.skill_slot, 0)
            if constants.DEBUG: print(f"cast_effect_before_expiration {skill.skill_name}")
            yield from Helpers.delay_aftercast(skill)
            return BehaviorResult.ACTION_PERFORMED

        yield
        return BehaviorResult.ACTION_SKIPPED

class Targets:
    
    @staticmethod
    def find_optimal_gravity_center(range_to_cover: Range, agent_ids: list[int]) -> GravityCenter | None:
        '''
        find position that will cover max allies within range
        '''
        OVERLAY_DEBUG = constants.DEBUG
        player_x, player_y, player_z = GLOBAL_CACHE.Agent.GetXYZ(GLOBAL_CACHE.Player.GetAgentID()) #cached_data.data.player_xyz # needs to be live
        if OVERLAY_DEBUG: Overlay().BeginDraw()
        
        player_position: tuple[float, float] = GLOBAL_CACHE.Player.GetXY()
        other_party_member_positions = [GLOBAL_CACHE.Agent.GetXY(agent_id) for agent_id in agent_ids]
        # other_party_member_positions: list[tuple[float, float]] = [GLOBAL_CACHE.Agent.GetXY(agent_id) for agent_id in GLOBAL_CACHE.AgentArray.GetAllyArray() if agent_id != GLOBAL_CACHE.Player.GetAgentID()]
        # other_party_member_positions: list[tuple[float, float]] = [GLOBAL_CACHE.Agent.GetXY(agent_id) for agent_id in GLOBAL_CACHE.AgentArray.GetAllyArray()]
        seek_range: float = range_to_cover.value - 50
        
        if OVERLAY_DEBUG: Overlay().DrawPoly3D(player_x, player_y, player_z, seek_range, Utils.RGBToColor(255, 128, 0 , 128), numsegments=32, thickness=5.0)
        # print(f"other_party_member_positions: {other_party_member_positions}")

        for pos in other_party_member_positions:
            # Overlay().DrawPoly3D(pos[0], pos[1], player_z, range_to_cover.value, Utils.RGBToColor(128, 255, 0 , 128), numsegments=32, thickness=2.0)
            if OVERLAY_DEBUG: Overlay().DrawPolyFilled3D(pos[0], pos[1], player_z, 30, Utils.RGBToColor(255, 0, 0 , 50), numsegments=32)
        
        if not other_party_member_positions: return None
        if len(other_party_member_positions) == 0: return None
        # if len(other_party_member_positions) == 1: return other_party_member_positions[0]
        
        # print("\n=== Recherche par centres intelligents ===")
        opt_pos, opt_count, opt_distance = custom_behavior_helpers_tests.find_optimal_position_weighted(player_position, other_party_member_positions, seek_range)
        # print(f"Position optimale: {opt_pos}")
        # print(f"Allié couverts: {opt_count}")
    
        if opt_pos is not None:
            if OVERLAY_DEBUG: Overlay().DrawPolyFilled3D(opt_pos[0], opt_pos[1], player_z, seek_range, Utils.RGBToColor(255, 255, 0 , 50), numsegments=32)
            if OVERLAY_DEBUG: Overlay().DrawPolyFilled3D(opt_pos[0], opt_pos[1], player_z, 50, Utils.RGBToColor(0, 255, 255 , 150), numsegments=32)
            # Overlay().DrawPoly3D(pos_smart[0], pos_smart[1], player_z, seek_range / 2, Utils.RGBToColor(128, 255, 0 , 128), numsegments=32, thickness=2.0)

        # fallback if no circle found (e.g. all points far apart)
        # if best_center is None and other_party_member_positions:
        #     # return average position
        #     sx = sum(p[0] for p in other_party_member_positions)
        #     sy = sum(p[1] for p in other_party_member_positions)
        #     return (sx / len(other_party_member_positions), sy / len(other_party_member_positions))
                
        # Overlay().DrawPolyFilled3D()
        if OVERLAY_DEBUG: Overlay().EndDraw()
        return GravityCenter(coordinates=opt_pos, agent_covered_count=opt_count, distance_from_player=opt_distance)

    @staticmethod
    def is_player_close_to_combat() -> bool:

        enemy_id = Targets.get_nearest_or_default_from_enemy_ordered_by_priority(
            within_range = Range.Spellcast.value + 350,
            condition = lambda agent_id: not GLOBAL_CACHE.Agent.IsAggressive(agent_id),
        )
        if enemy_id is not None and enemy_id > 0 and GLOBAL_CACHE.Agent.IsValid(enemy_id): return True
        return False


    @staticmethod
    def is_player_in_aggro() -> bool:
        
        enemy_aggressive_id = Targets.get_nearest_or_default_from_enemy_ordered_by_priority(
            within_range = Range.Spellcast.value + 400,
            condition = lambda agent_id: GLOBAL_CACHE.Agent.IsAggressive(agent_id))
        if enemy_aggressive_id is not None and enemy_aggressive_id > 0 and GLOBAL_CACHE.Agent.IsValid(enemy_aggressive_id): return True

        enemy_id = Targets.get_nearest_or_default_from_enemy_ordered_by_priority(
            within_range = Range.Spellcast.value,
            condition = lambda agent_id: not GLOBAL_CACHE.Agent.IsAggressive(agent_id))
        if enemy_id is not None and enemy_id > 0 and GLOBAL_CACHE.Agent.IsValid(enemy_id): return True

        return False

    @staticmethod
    def is_party_member_in_aggro(agent_id:int) -> bool:
        
        agent_pos:tuple[float, float] = GLOBAL_CACHE.Agent.GetXY(agent_id)

        enemy_aggressive_id = Targets.get_nearest_or_default_from_enemy_ordered_by_priority_custom_source(
            source_agent_pos=agent_pos,
            within_range = Range.Spellcast.value + 400,
            condition = lambda agent_id: GLOBAL_CACHE.Agent.IsAggressive(agent_id))
        if enemy_aggressive_id is not None and enemy_aggressive_id > 0 and GLOBAL_CACHE.Agent.IsValid(enemy_aggressive_id): return True

        enemy_id = Targets.get_nearest_or_default_from_enemy_ordered_by_priority_custom_source(
            source_agent_pos=agent_pos,
            within_range = Range.Spellcast.value,
            condition = lambda agent_id: not GLOBAL_CACHE.Agent.IsAggressive(agent_id))
        if enemy_id is not None and enemy_id > 0 and GLOBAL_CACHE.Agent.IsValid(enemy_id): return True

        return False

    @staticmethod
    def is_party_leader_in_aggro() -> bool:
        
        party_leader_id:int = GLOBAL_CACHE.Party.GetPartyLeaderID()
        if Targets.is_party_member_in_aggro(party_leader_id): return True
        return False

    @staticmethod
    def is_party_in_aggro() -> bool:
        
        # doing such thing for whole party is too costly
        #return False

        players = GLOBAL_CACHE.Party.GetPlayers()
        for player in players:
            agent_id = GLOBAL_CACHE.Party.Players.GetAgentIDByLoginNumber(player.login_number)
            if Targets.is_party_member_in_aggro(agent_id):
                return agent_id

        # todo to implement
        return False

    @staticmethod
    def get_all_spirits_raw(
            within_range: Range,
            spirit_model_ids: list[SpiritModelID] | None = None,
            condition: Optional[Callable[[int], bool]] = None) -> list[SpiritAgentData]:
        spirit_agent_ids = GLOBAL_CACHE.AgentArray.GetSpiritPetArray()
        spirit_agent_ids = AgentArray.Filter.ByDistance(spirit_agent_ids, GLOBAL_CACHE.Player.GetXY(), within_range.value)
        spirit_agent_ids = AgentArray.Filter.ByCondition(spirit_agent_ids, lambda agent_id: GLOBAL_CACHE.Agent.IsAlive(agent_id))
        if condition is not None:
            spirit_agent_ids = AgentArray.Filter.ByCondition(spirit_agent_ids, condition)

        if spirit_model_ids is not None:
            spirit_agent_ids = AgentArray.Filter.ByCondition(spirit_agent_ids, lambda agent_id: GLOBAL_CACHE.Agent.GetPlayerNumber(agent_id) in spirit_model_ids)

        spirit_data: list[SpiritAgentData] = []
        for spirit_agent_id in spirit_agent_ids:
            spirit_data.append(SpiritAgentData(
                agent_id=spirit_agent_id,
                distance_from_player=Utils.Distance(GLOBAL_CACHE.Agent.GetXY(spirit_agent_id), GLOBAL_CACHE.Player.GetXY()),
                hp=GLOBAL_CACHE.Agent.GetHealth(spirit_agent_id)
            ))

        return spirit_data

    @staticmethod
    def get_first_or_default_from_spirits_raw(
            within_range: Range,
            spirit_model_ids: list[SpiritModelID] | None = None,
            condition: Optional[Callable[[int], bool]] = None) -> SpiritAgentData | None:
        spirits = Targets.get_all_spirits_raw(within_range, spirit_model_ids, condition)
        if len(spirits) == 0: return None
        return spirits[0]

    @staticmethod
    def get_all_possible_allies_ordered_by_priority_raw(
            within_range: Range,
            condition: Callable[[int], bool] | None = None,
            sort_key: tuple[TargetingOrder, ...] | None = None,
            range_to_count_enemies: float | None = None,
            range_to_count_allies: float | None = None) -> list[SortableAgentData]:

        player_pos: tuple[float, float] = GLOBAL_CACHE.Player.GetXY()
        agent_ids: list[int] = GLOBAL_CACHE.AgentArray.GetAllyArray()
        all_enemies_ids: list[int] = GLOBAL_CACHE.AgentArray.GetEnemyArray()

        agent_ids = AgentArray.Filter.ByCondition(agent_ids, lambda agent_id: GLOBAL_CACHE.Agent.IsAlive(agent_id))
        agent_ids = AgentArray.Filter.ByDistance(agent_ids, player_pos, within_range.value)
        if condition is not None: agent_ids = AgentArray.Filter.ByCondition(agent_ids, condition)

        def build_sortable_array(agent_id):
            agent_pos = GLOBAL_CACHE.Agent.GetXY(agent_id)

            # scan enemies within range
            enemies_ids = AgentArray.Filter.ByCondition(all_enemies_ids, lambda agent_id: GLOBAL_CACHE.Agent.IsAlive(agent_id))
            enemies_ids = AgentArray.Filter.ByDistance(enemies_ids, player_pos, within_range.value)
            enemies_quantity_within_range = 0

            if range_to_count_enemies is not None:
                for enemy_id in enemies_ids:
                    if Utils.Distance(GLOBAL_CACHE.Agent.GetXY(enemy_id), agent_pos) <= range_to_count_enemies:
                        enemies_quantity_within_range += 1

            # scan agents within aoe range
            allies_quantity_within_range = 0

            if range_to_count_allies is not None:
                for other_agent_id in agent_ids:
                    if other_agent_id != agent_id and Utils.Distance(GLOBAL_CACHE.Agent.GetXY(other_agent_id), agent_pos) <= range_to_count_allies:
                        allies_quantity_within_range += 1

            return SortableAgentData(
                agent_id=agent_id,
                distance_from_player=Utils.Distance(agent_pos, player_pos),
                hp=GLOBAL_CACHE.Agent.GetHealth(agent_id),
                is_caster=GLOBAL_CACHE.Agent.IsCaster(agent_id),
                is_melee=GLOBAL_CACHE.Agent.IsMelee(agent_id),
                is_martial=GLOBAL_CACHE.Agent.IsMartial(agent_id),
                enemy_quantity_within_range=enemies_quantity_within_range,
                agent_quantity_within_range=allies_quantity_within_range,
                energy=Resources.get_energy_percent_in_party(agent_id)
            )

        data_to_sort = list(map(lambda agent_id: build_sortable_array(agent_id), agent_ids))

        if not sort_key:  # If no sort_key is provided
            return data_to_sort

        # Iterate over sort_key in reverse order (apply less important sort criteria first)
        for criterion in reversed(sort_key):
            if criterion == TargetingOrder.DISTANCE_ASC:
                data_to_sort = sorted(data_to_sort, key=lambda x: x.distance_from_player)
            elif criterion == TargetingOrder.DISTANCE_DESC:
                data_to_sort = sorted(data_to_sort, key=lambda x: -x.distance_from_player)
            elif criterion == TargetingOrder.HP_ASC:
                data_to_sort = sorted(data_to_sort, key=lambda x: x.hp)
            elif criterion == TargetingOrder.HP_DESC:
                data_to_sort = sorted(data_to_sort, key=lambda x: -x.hp)
            elif criterion == TargetingOrder.ENERGY_ASC:
                data_to_sort = sorted(data_to_sort, key=lambda x: x.energy)
            elif criterion == TargetingOrder.ENERGY_DESC:
                data_to_sort = sorted(data_to_sort, key=lambda x: -x.energy)
            elif criterion == TargetingOrder.AGENT_QUANTITY_WITHIN_RANGE_DESC:
                data_to_sort = sorted(data_to_sort, key=lambda x: -x.agent_quantity_within_range)
            elif criterion == TargetingOrder.AGENT_QUANTITY_WITHIN_RANGE_ASC:
                data_to_sort = sorted(data_to_sort, key=lambda x: x.agent_quantity_within_range)
            elif criterion == TargetingOrder.ENEMIES_QUANTITY_WITHIN_RANGE_DESC:
                data_to_sort = sorted(data_to_sort, key=lambda x: -x.enemy_quantity_within_range)
            elif criterion == TargetingOrder.CASTER_THEN_MELEE:
                data_to_sort = sorted(data_to_sort, key=lambda x: x.is_caster)
            elif criterion == TargetingOrder.MELEE_THEN_CASTER:
                data_to_sort = sorted(data_to_sort, key=lambda x: x.is_melee)
            else:
                raise ValueError(f"Invalid sorting criterion: {criterion}")

        return data_to_sort

    @staticmethod
    def get_all_possible_allies_ordered_by_priority(
            within_range: Range,
            condition: Callable[[int], bool] | None = None,
            sort_key: tuple[TargetingOrder, ...] | None = None,
            range_to_count_enemies: float | None = None,
            range_to_count_allies: float | None = None) -> tuple[int, ...]:

        data = Targets.get_all_possible_allies_ordered_by_priority_raw(
            within_range=within_range,
            condition=condition,
            sort_key=sort_key,
            range_to_count_enemies=range_to_count_enemies,
            range_to_count_allies=range_to_count_allies
        )
        return tuple(entry.agent_id for entry in data)

    @staticmethod
    def get_first_or_default_from_allies_ordered_by_priority(
            within_range: Range,
            condition: Callable[[int], bool] | None = None,
            sort_key: tuple[TargetingOrder, ...] | None = None,
            range_to_count_enemies: float | None = None,
            range_to_count_allies: float | None = None) -> int | None:

        allies = Targets.get_all_possible_allies_ordered_by_priority(within_range=within_range, condition=condition, sort_key=sort_key, range_to_count_enemies=range_to_count_enemies, range_to_count_allies=range_to_count_allies)
        if len(allies) == 0: return None
        return allies[0]

    # enemy 

    @staticmethod
    def get_nearest_or_default_from_enemy_ordered_by_priority_custom_source(
            source_agent_pos: tuple[float, float],
            within_range: float,
            condition: Optional[Callable[[int], bool]] = None) -> Optional[int]:
        
        enemies = Targets._get_all_possible_enemies_ordered_by_priority_raw(
            source_agent_pos=source_agent_pos, 
            within_range=within_range,
            condition=condition,
            sort_key=(TargetingOrder.DISTANCE_ASC, TargetingOrder.HP_ASC))
            
        if len(enemies) == 0: return None
        return enemies[0].agent_id

    @staticmethod
    def get_nearest_or_default_from_enemy_ordered_by_priority(
            within_range: float,
            condition: Optional[Callable[[int], bool]] = None) -> Optional[int]:
        
        enemies = Targets._get_all_possible_enemies_ordered_by_priority_raw(
            source_agent_pos=GLOBAL_CACHE.Player.GetXY(), 
            within_range=within_range,
            condition=condition,
            sort_key=(TargetingOrder.DISTANCE_ASC, TargetingOrder.HP_ASC))

        if len(enemies) == 0: return None
        return enemies[0].agent_id

    @staticmethod
    def get_first_or_default_from_enemy_ordered_by_priority(
            within_range: Range,
            condition: Optional[Callable[[int], bool]] = None,
            sort_key: Optional[Tuple[TargetingOrder, ...]] = None,
            range_to_count_enemies: Optional[float] = None) -> Optional[int]:
        """
        Determines and retrieves a tuple of all possible enemy agents within a specified range,
        filtered by conditions, and ordered by priority based on given sorting keys.
        Ordering handles multiple criteria like distance from the player, health points, and the number of enemies within the area-of-effect (AoE) range.

        :param within_range: The maximum distance from the player to consider agents as valid targets.
        :param condition: An optional callable, taking an agent's identifier as input, that must
            return a boolean indicating whether the agent meets additional filtering criteria.
        :param sort_key: An optional tuple specifying the priority order for sorting the filtered
            enemies. Each criterion defines a sorting strategy applied sequentially.
        :param clustered_foes_within_range: A range representing the area-of-effect radius, which is used to determine
            how densely packed enemies are in the proximity of each other.

        :return: Optionally returns the identifier of the first enemy that satisfies the
        specified criteria, ordered by priority. Returns None if no enemies satisfy the criteria.
        """

        enemies = Targets.get_all_possible_enemies_ordered_by_priority(within_range, condition, sort_key, range_to_count_enemies)
        if len(enemies) == 0: return None
        return enemies[0]

    @staticmethod
    def _get_all_possible_enemies_ordered_by_priority_raw(
            source_agent_pos: tuple[float, float],
            within_range: float,
            condition: Callable[[int], bool] | None = None,
            sort_key: tuple[TargetingOrder, ...] | None = None,
            range_to_count_enemies: float | None = None) -> list[SortableAgentData]:
        
        agent_ids: list[int] = GLOBAL_CACHE.AgentArray.GetEnemyArray()
        agent_ids = AgentArray.Filter.ByDistance(agent_ids, source_agent_pos, within_range)
        agent_ids = AgentArray.Filter.ByCondition(agent_ids, lambda agent_id: GLOBAL_CACHE.Agent.IsAlive(agent_id))
        if condition is not None: agent_ids = AgentArray.Filter.ByCondition(agent_ids, condition)

        def build_sortable_array(agent_id):
            agent_pos = GLOBAL_CACHE.Agent.GetXY(agent_id)
            enemy_quantity_within_range = 0

            if range_to_count_enemies is not None:
                for other_agent_id in agent_ids:  # complexity O(n^2) !
                    if other_agent_id != agent_id and Utils.Distance(GLOBAL_CACHE.Agent.GetXY(other_agent_id), agent_pos) <= range_to_count_enemies:
                        enemy_quantity_within_range += 1

            return SortableAgentData(
                agent_id=agent_id,
                distance_from_player=Utils.Distance(agent_pos, source_agent_pos),
                hp=GLOBAL_CACHE.Agent.GetHealth(agent_id),
                is_caster=GLOBAL_CACHE.Agent.IsCaster(agent_id),
                is_melee=GLOBAL_CACHE.Agent.IsMelee(agent_id),
                is_martial=GLOBAL_CACHE.Agent.IsMartial(agent_id),
                enemy_quantity_within_range=enemy_quantity_within_range,
                agent_quantity_within_range=0,  # Not used for enemies
                energy=0.0  # Not used for enemies
            )

        data_to_sort = list(map(lambda agent_id: build_sortable_array(agent_id), agent_ids))

        if not sort_key:  # If no sort_key is provided
            return data_to_sort

        # Iterate over sort_key in reverse order (apply less important sort criteria first)
        for criterion in reversed(sort_key):
            if criterion == TargetingOrder.DISTANCE_ASC:
                data_to_sort = sorted(data_to_sort, key=lambda x: x.distance_from_player)
            elif criterion == TargetingOrder.DISTANCE_DESC:
                data_to_sort = sorted(data_to_sort, key=lambda x: -x.distance_from_player)
            elif criterion == TargetingOrder.HP_ASC:
                data_to_sort = sorted(data_to_sort, key=lambda x: x.hp)
            elif criterion == TargetingOrder.HP_DESC:
                data_to_sort = sorted(data_to_sort, key=lambda x: -x.hp)
            elif criterion == TargetingOrder.AGENT_QUANTITY_WITHIN_RANGE_DESC:
                data_to_sort = sorted(data_to_sort, key=lambda x: -x.enemy_quantity_within_range)
            elif criterion == TargetingOrder.AGENT_QUANTITY_WITHIN_RANGE_ASC:
                data_to_sort = sorted(data_to_sort, key=lambda x: x.enemy_quantity_within_range)
            elif criterion == TargetingOrder.CASTER_THEN_MELEE:
                data_to_sort = sorted(data_to_sort, key=lambda x: x.is_caster)
            elif criterion == TargetingOrder.MELEE_THEN_CASTER:
                data_to_sort = sorted(data_to_sort, key=lambda x: x.is_melee)
            else:
                raise ValueError(f"Invalid sorting criterion: {criterion}")

        return data_to_sort

    @staticmethod
    def get_all_possible_enemies_ordered_by_priority_raw(
            within_range: Range,
            condition: Callable[[int], bool] | None = None,
            sort_key: tuple[TargetingOrder, ...] | None = None,
            range_to_count_enemies: float | None = None) -> list[SortableAgentData]:

        return Targets._get_all_possible_enemies_ordered_by_priority_raw(
            source_agent_pos=GLOBAL_CACHE.Player.GetXY(),
            within_range=within_range.value,
            condition=condition,
            sort_key=sort_key,
            range_to_count_enemies=range_to_count_enemies
        )
        
    @staticmethod
    def get_all_possible_enemies_ordered_by_priority(
            within_range: Range,
            condition: Optional[Callable[[int], bool]] = None,
            sort_key: Optional[Tuple[TargetingOrder, ...]] = None,
            range_to_count_enemies: Optional[float] = None) -> Tuple[int, ...]:
        """
        Determines and retrieves a tuple of all possible enemy agents within a specified range,
        filtered by conditions, and ordered by priority based on given sorting keys.
        Ordering handles multiple criteria like distance from the player, health points, and the number of enemies within the area-of-effect (AoE) range.

        :param within_range: The maximum distance from the player to consider agents as valid targets.
        :param condition: An optional callable, taking an agent's identifier as input, that must
            return a boolean indicating whether the agent meets additional filtering criteria.
        :param sort_key: An optional tuple specifying the priority order for sorting the filtered
            enemies. Each criterion defines a sorting strategy applied sequentially.
        :param range_to_count_enemies: A range representing the area-of-effect radius, which is used to determine
            how densely packed enemies are in the proximity of each other.

        :return: A tuple containing the identifiers of enemy agents, ordered by the specified
            priority logic and constrained by the input conditions and ranges.
        """
        data = Targets.get_all_possible_enemies_ordered_by_priority_raw(
            within_range=within_range,
            condition=condition,
            sort_key=sort_key,
            range_to_count_enemies=range_to_count_enemies
        )
        return tuple(entry.agent_id for entry in data)

class Heals:


    @staticmethod
    def is_party_damaged(within_range:Range, min_allies_count:int, less_health_than_percent:float) -> bool:

        allies = Targets.get_all_possible_allies_ordered_by_priority(
            within_range=within_range,
            condition= lambda agent_id: GLOBAL_CACHE.Agent.GetHealth(agent_id) < less_health_than_percent,
            sort_key= (TargetingOrder.HP_ASC, TargetingOrder.DISTANCE_ASC),
            range_to_count_enemies=None,
            range_to_count_allies=None)

        if len(allies) < min_allies_count: return False
        return True

    @staticmethod
    def party_average_health(within_range:Range) -> float:
        allies = Targets.get_all_possible_allies_ordered_by_priority(
            within_range=within_range,
            condition= lambda agent_id: True,
            sort_key= (TargetingOrder.HP_ASC, TargetingOrder.DISTANCE_ASC),
        )
        return reduce(lambda acc, ally: acc + GLOBAL_CACHE.Agent.GetHealth(ally), allies, 0) / len(allies)

    @staticmethod
    def get_first_member_damaged(within_range: Range, less_health_than_percent: float, exclude_player:bool, condition: Optional[Callable[[int], bool]] = None) -> int | None:

        allies = Targets.get_all_possible_allies_ordered_by_priority(
            within_range=within_range,
            condition=lambda agent_id: GLOBAL_CACHE.Agent.GetHealth(agent_id) < less_health_than_percent,
            sort_key=(TargetingOrder.HP_ASC, TargetingOrder.DISTANCE_ASC),
            range_to_count_enemies=None,
            range_to_count_allies=None)

        if exclude_player:
            allies = AgentArray.Filter.ByCondition(allies, lambda agent_id: agent_id != GLOBAL_CACHE.Player.GetAgentID())

        if condition is not None:
            allies = AgentArray.Filter.ByCondition(allies, condition)

        if len(allies) == 0: return None
        return allies[0]
