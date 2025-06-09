from operator import index
from Py4GWCoreLib import GLOBAL_CACHE, IconsFontAwesome5, PyImGui, ImGui, Utils, Overlay, Range, SharedCommandType, ConsoleLog, Color
from Py4GWCoreLib import UIManager, ModelID, GLOBAL_CACHE

from .constants import MAX_NUM_PLAYERS, NUMBER_OF_SKILLS
from .types import SkillType, SkillNature, Skilltarget, GameOptionStruct
from .globals import capture_mouse_timer, show_area_rings, show_hero_follow_grid, show_distance_on_followers, hero_formation, capture_hero_flag, capture_flag_all, capture_hero_index
from .utils import IsHeroFlagged, DrawFlagAll, DrawHeroFlag, DistanceFromWaypoint

from .cache_data import CacheData

import math


def DrawBuffWindow(cached_data:CacheData):
    global MAX_NUM_PLAYERS
    if not cached_data.data.is_explorable:
        return

    for index in range(MAX_NUM_PLAYERS):
        player_struct = cached_data.HeroAI_vars.all_player_struct[index]
        if player_struct.IsActive:
            if GLOBAL_CACHE.Agent.IsPlayer(player_struct.PlayerID):
                player_name = GLOBAL_CACHE.Agent.GetName(player_struct.PlayerID)
            else:
                player_name = GLOBAL_CACHE.Party.Heroes.GetNameByAgentID(player_struct.PlayerID)

            if PyImGui.tree_node(f"{player_name}##DebugBuffsPlayer{index}"):
                # Retrieve buffs for the player
                player_buffs = cached_data.HeroAI_vars.shared_memory_handler.get_agent_buffs(player_struct.PlayerID)
                headers = ["Skill ID", "Skill Name"]
                data = [(skill_id, GLOBAL_CACHE.Skill.GetName(skill_id)) for skill_id in player_buffs]
                ImGui.table(f"{player_name} Buffs", headers, data)
                PyImGui.tree_pop()


def TrueFalseColor(condition):
    if condition:
        return Utils.RGBToNormal(0, 255, 0, 255)
    else:
        return Utils.RGBToNormal(255, 0, 0, 255)

skill_slot = 0
def DrawPrioritizedSkills(cached_data:CacheData):
    global skill_slot
    from .constants import NUMBER_OF_SKILLS
 
    PyImGui.text(f"skill pointer: : {cached_data.combat_handler.skill_pointer}")
    in_casting_routine = cached_data.combat_handler.InCastingRoutine()
    PyImGui.text_colored(f"InCastingRoutine: {in_casting_routine}",TrueFalseColor(not in_casting_routine))
    PyImGui.text(f"aftercast_timer: {cached_data.combat_handler.aftercast_timer.GetElapsedTime()}")

    if PyImGui.begin_tab_bar("OrderedSkills"):
        skills = cached_data.combat_handler.GetSkills()
        for i in range(len(skills)):
            slot = i
            skill = skills[i]
        
            if PyImGui.begin_tab_item(GLOBAL_CACHE.Skill.GetName(skill.skill_id)):
                if PyImGui.tree_node(f"Custom Properties"):
                    # Display skill properties
                    PyImGui.text(f"Skill ID: {skill.skill_id}")
                    PyImGui.text(f"Skill Type: {SkillType(skill.custom_skill_data.SkillType).name}")
                    PyImGui.text(f"Skill Nature: {SkillNature(skill.custom_skill_data.Nature).name}")
                    PyImGui.text(f"Skill Target: {Skilltarget(skill.custom_skill_data.TargetAllegiance).name}")

                    PyImGui.separator()
                    PyImGui.text("Cast Conditions:")

                    # Dynamically display attributes of CastConditions
                    conditions = skill.custom_skill_data.Conditions
                    for attr_name, attr_value in vars(conditions).items():
                        # Check if the attribute is a non-empty list or True for non-list attributes
                        if isinstance(attr_value, list) and attr_value:  # Non-empty list
                            PyImGui.text(f"{attr_name}: {', '.join(map(str, attr_value))}")
                        elif isinstance(attr_value, bool) and attr_value:  # True boolean
                            PyImGui.text(f"{attr_name}: True")
                        elif isinstance(attr_value, (int, float)) and attr_value != 0:  # Non-zero numbers
                            PyImGui.text(f"{attr_name}: {attr_value}")
                    PyImGui.tree_pop()

                
                if PyImGui.tree_node(f"Combat debug"):
                
                    is_skill_ready = cached_data.combat_handler.IsSkillReady(slot)
                    is_ooc_skill = cached_data.combat_handler.IsOOCSkill(slot)  
                    is_ready_to_cast, v_target = cached_data.combat_handler.IsReadyToCast(skill_slot)

                    self_id = GLOBAL_CACHE.Player.GetAgentID()
                    nearest_enemy = cached_data.data.nearest_enemy
                    nearest_ally = cached_data.data.lowest_ally
                    nearest_spirit = cached_data.data.nearest_spirit
                    nearest_minion = cached_data.data.lowest_minion
                    nearest_corpse = cached_data.data.nearest_corpse
                    pet_id = cached_data.data.pet_id

                    headers = ["Self", "Nearest Enemy", "Nearest Ally", "Nearest Item", "Nearest Spirit", "Nearest Minion", "Nearest Corpse", "Pet"]

                    data = [
                        (self_id, nearest_enemy, nearest_ally,
                         nearest_spirit, nearest_minion, nearest_corpse, pet_id)
                    ]

                    ImGui.table("Target Debug Table", headers, data)

                    PyImGui.text(f"Target to Cast: {v_target}")

                    PyImGui.separator()
                    
                    PyImGui.text(f"InAggro: {cached_data.data.in_aggro}")
                    PyImGui.text(f"stayt_alert_timer: {cached_data.stay_alert_timer.GetElapsedTime()}")
                    
                    PyImGui.separator()

                    PyImGui.text_colored(f"IsSkillReady: {is_skill_ready}",TrueFalseColor(is_skill_ready))
                    
                    PyImGui.text_colored(f"IsReadyToCast: {is_ready_to_cast}", TrueFalseColor(is_ready_to_cast))
                    if PyImGui.tree_node(f"IsReadyToCast: {is_ready_to_cast}"): 
                        is_casting = cached_data.data.player_is_casting
                        casting_skill = cached_data.data.player_casting_skill
                        skillbar_casting = cached_data.data.player_skillbar_casting
                        skillbar_recharge = cached_data.combat_handler.skills[skill_slot].skillbar_data.recharge
                        current_energy = cached_data.data.energy * cached_data.data.max_energy
                        ordered_skill = cached_data.combat_handler.GetOrderedSkill(skill_slot)
                        if ordered_skill:                        
                            energy_cost = GLOBAL_CACHE.Skill.Data.GetEnergyCost(ordered_skill.skill_id)
                            current_hp = cached_data.data.player_hp
                            target_hp = ordered_skill.custom_skill_data.Conditions.SacrificeHealth
                            health_cost = GLOBAL_CACHE.Skill.Data.GetHealthCost(ordered_skill.skill_id)

                            adrenaline_required = GLOBAL_CACHE.Skill.Data.GetAdrenaline(ordered_skill.skill_id)
                            adrenaline_a = ordered_skill.skillbar_data.adrenaline_a
                        
                            current_overcast = cached_data.data.player_overcast
                            overcast_target = ordered_skill.custom_skill_data.Conditions.Overcast
                            skill_overcast = GLOBAL_CACHE.Skill.Data.GetOvercast(ordered_skill.skill_id)

                            are_cast_conditions_met = cached_data.combat_handler.AreCastConditionsMet(skill_slot,v_target)
                            spirit_buff_exists = cached_data.combat_handler.SpiritBuffExists(ordered_skill.skill_id)
                            has_effect = cached_data.combat_handler.HasEffect(v_target, ordered_skill.skill_id)

                            PyImGui.text_colored(f"IsCasting: {is_casting}", TrueFalseColor(not is_casting))
                            PyImGui.text_colored(f"CastingSkill: {casting_skill}", TrueFalseColor(not casting_skill != 0))
                            PyImGui.text_colored(f"SkillBar Casting: {skillbar_casting}", TrueFalseColor(not skillbar_casting != 0))
                            PyImGui.text_colored(f"SkillBar recharge: {skillbar_recharge}", TrueFalseColor(skillbar_recharge == 0))  
                            PyImGui.text_colored(f"Energy: {current_energy} / Cost {energy_cost}", TrueFalseColor(current_energy >= energy_cost))

                            PyImGui.text_colored(f"Current HP: {current_hp} / Target HP: {target_hp} / Health Cost: {health_cost}", TrueFalseColor(health_cost == 0 or current_hp >= health_cost))
                            PyImGui.text_colored(f"Adrenaline Required: {adrenaline_required}", TrueFalseColor(adrenaline_required == 0 or (adrenaline_a >= adrenaline_required)))
                            PyImGui.text_colored(f"Current Overcast: {current_overcast} / Overcast Target: {overcast_target} / Skill Overcast: {skill_overcast}", TrueFalseColor(current_overcast >= overcast_target or skill_overcast == 0))
                        
                            PyImGui.text_colored(f"AreCastConditionsMet: {are_cast_conditions_met}", TrueFalseColor(are_cast_conditions_met))
                            PyImGui.text_colored(f"SpiritBuffExists: {spirit_buff_exists}", TrueFalseColor(not spirit_buff_exists))
                            PyImGui.text_colored(f"HasEffect: {has_effect}", TrueFalseColor(not has_effect))

                        PyImGui.tree_pop()

                    PyImGui.tree_pop()

                    PyImGui.text_colored(f"IsOOCSkill: {is_ooc_skill}",TrueFalseColor(is_ooc_skill))
                
                PyImGui.end_tab_item()
        PyImGui.end_tab_bar()


HeroFlags: list[bool] = [False, False, False, False, False, False, False, False, False]
AllFlag = False
CLearFlags = False
one_time_set_flag = False
def DrawFlags(cached_data:CacheData):
    global capture_flag_all, capture_hero_flag, capture_hero_index
    global one_time_set_flag, CLearFlags

    if capture_hero_flag:
        x, y, _ = Overlay().GetMouseWorldPos()
        if capture_flag_all:
            DrawFlagAll(x, y)
            pass
        else:
            DrawHeroFlag(x, y)
            
        if PyImGui.is_mouse_clicked(0) and one_time_set_flag:
            one_time_set_flag = False
            return

        if PyImGui.is_mouse_clicked(0) and not one_time_set_flag:
            if capture_hero_index > 0 and capture_hero_index <= cached_data.data.party_hero_count:
                if not capture_flag_all:   
                    agent_id = GLOBAL_CACHE.Party.Heroes.GetHeroAgentIDByPartyPosition(capture_hero_index)
                    GLOBAL_CACHE.Party.Heroes.FlagHero(agent_id, x, y)
                    one_time_set_flag = True
            else:
                if capture_hero_index == 0:
                    hero_ai_index = 0
                    GLOBAL_CACHE.Party.Heroes.FlagAllHeroes(x, y)
                else:
                    hero_ai_index = capture_hero_index - cached_data.data.party_hero_count
                cached_data.HeroAI_vars.shared_memory_handler.set_player_property(hero_ai_index, "IsFlagged", True)
                cached_data.HeroAI_vars.shared_memory_handler.set_player_property(hero_ai_index, "FlagPosX", x)
                cached_data.HeroAI_vars.shared_memory_handler.set_player_property(hero_ai_index, "FlagPosY", y)
                cached_data.HeroAI_vars.shared_memory_handler.set_player_property(hero_ai_index, "FollowAngle", cached_data.data.party_leader_rotation_angle)
                
                one_time_set_flag = True

            capture_flag_all = False
            capture_hero_flag = False
            one_time_set_flag = False
            capture_mouse_timer.Stop()

    #All flag is handled by the game even with no heroes
    if cached_data.HeroAI_vars.all_player_struct[0].IsFlagged:
        DrawFlagAll(cached_data.HeroAI_vars.all_player_struct[0].FlagPosX, cached_data.HeroAI_vars.all_player_struct[0].FlagPosY)
        
    for i in range(1, MAX_NUM_PLAYERS):
        if cached_data.HeroAI_vars.all_player_struct[i].IsFlagged and cached_data.HeroAI_vars.all_player_struct[i].IsActive and not cached_data.HeroAI_vars.all_player_struct[i].IsHero:
            DrawHeroFlag(cached_data.HeroAI_vars.all_player_struct[i].FlagPosX,cached_data.HeroAI_vars.all_player_struct[i].FlagPosY)

    if CLearFlags:
        for i in range(MAX_NUM_PLAYERS):
            cached_data.HeroAI_vars.shared_memory_handler.set_player_property(i, "IsFlagged", False)
            cached_data.HeroAI_vars.shared_memory_handler.set_player_property(i, "FlagPosX", 0.0)
            cached_data.HeroAI_vars.shared_memory_handler.set_player_property(i, "FlagPosY", 0.0)
            cached_data.HeroAI_vars.shared_memory_handler.set_player_property(i, "FollowAngle", 0.0)
            GLOBAL_CACHE.Party.Heroes.UnflagHero(i)
        GLOBAL_CACHE.Party.Heroes.UnflagAllHeroes()
        CLearFlags = False
            
        

def DrawFlaggingWindow(cached_data:CacheData):
    global HeroFlags, AllFlag, capture_flag_all, capture_hero_flag, capture_hero_index, one_time_set_flag
    global CLearFlags
    party_size = cached_data.data.party_size
    if party_size == 1:
        PyImGui.text("No Follower or Heroes to Flag.")
        return

    if PyImGui.collapsing_header("Flagging"):
        if PyImGui.begin_table("Flags",3):
            PyImGui.table_next_row()
            PyImGui.table_next_column()
            if party_size >= 2:
                HeroFlags[0] = ImGui.toggle_button("1", IsHeroFlagged(cached_data,1), 30, 30)
            PyImGui.table_next_column()
            if party_size >= 3:
                HeroFlags[1] = ImGui.toggle_button("2", IsHeroFlagged(cached_data,2),30,30)
            PyImGui.table_next_column()
            if party_size >= 4:
                HeroFlags[2] = ImGui.toggle_button("3", IsHeroFlagged(cached_data,3),30,30)
            PyImGui.table_next_row()
            PyImGui.table_next_column()
            if party_size >= 5:
                HeroFlags[3] = ImGui.toggle_button("4", IsHeroFlagged(cached_data,4),30,30)
            PyImGui.table_next_column()
            AllFlag = ImGui.toggle_button("All", IsHeroFlagged(cached_data,0), 30, 30)
            PyImGui.table_next_column()
            if party_size >= 6:
                HeroFlags[4] = ImGui.toggle_button("5", IsHeroFlagged(cached_data,5),30,30)
            PyImGui.table_next_row()
            PyImGui.table_next_column()
            if party_size >= 7:
                HeroFlags[5] = ImGui.toggle_button("6", IsHeroFlagged(cached_data,6),30,30)
            PyImGui.table_next_column()
            if party_size >= 8:
                HeroFlags[6] = ImGui.toggle_button("7", IsHeroFlagged(cached_data,7), 30, 30)
            PyImGui.table_next_column()
            CLearFlags = ImGui.toggle_button("X", HeroFlags[7],30,30)
            PyImGui.end_table()
    
    if PyImGui.collapsing_header("Formation Flagger - Backline(1,2)"):
        set_formations_relative_to_leader = []
        final_text_to_announce = ''
        
        formations  = {
            "1,2 - Double Backline Wide": [
                (250, -250), (-250, -250), (0, 200), (-350, 500), (350, 500), (-450, 300), (450, 300)
            ],
            "1,2 - Double Backline Narrow": [
                (200, -200), (-200, -200), (0, 200), (-300, 500), (300, 500), (-400, 300), (400, 300)
            ],
            "1 - Single Backline Wide": [
                (0, -250), (-150, 200), (150, 200), (-350, 500), (350, 500), (-450, 300), (450, 300)
            ],
            "1 - Single Backline Narrow": [
                (0, -250), (-100, 200), (100, 200), (-300, 500), (300, 500), (-350, 300), (350, 300)
            ],
            "1,2 - Double Backline Triple Row Wide": [
                (250, -250), (-250, -250), (-250, 0), (250, 0), (-250, 300), (0, 300), (250, 300)
            ],
            "1,2 - Double Backline Triple Row Narrow": [
                (-200, -200), (200, -200), (-200, 0), (200, 0), (-200, 300), (0, 300), (200, 300)
            ],
        }
        
        for formation_text, formation_coordinates in formations.items():
            should_set_formation = PyImGui.button(formation_text)
            if should_set_formation:
                final_text_to_announce = formation_text
                set_formations_relative_to_leader = formation_coordinates
        
        if len(set_formations_relative_to_leader):
            print(f'[INFO] Setting Formation: {final_text_to_announce}')
            leader_follow_angle = cached_data.data.party_leader_rotation_angle  # in radians
            leader_x, leader_y, _ = GLOBAL_CACHE.Agent.GetXYZ(GLOBAL_CACHE.Party.GetPartyLeaderID())
            angle_rad = leader_follow_angle - math.pi / 2  # adjust for coordinate system

            cos_a = math.cos(angle_rad)
            sin_a = math.sin(angle_rad)

            for hero_ai_index in range(1, party_size):
                offset_x, offset_y = set_formations_relative_to_leader[hero_ai_index - 1]
                
                # Rotate offset
                rotated_x = offset_x * cos_a - offset_y * sin_a
                rotated_y = offset_x * sin_a + offset_y * cos_a

                # Apply rotated offset to leader's position
                final_x = leader_x + rotated_x
                final_y = leader_y + rotated_y

                cached_data.HeroAI_vars.shared_memory_handler.set_player_property(hero_ai_index, "IsFlagged", True)
                cached_data.HeroAI_vars.shared_memory_handler.set_player_property(hero_ai_index, "FlagPosX", final_x)
                cached_data.HeroAI_vars.shared_memory_handler.set_player_property(hero_ai_index, "FlagPosY", final_y)
                cached_data.HeroAI_vars.shared_memory_handler.set_player_property(hero_ai_index, "FollowAngle", leader_follow_angle)
                
                
    if AllFlag != IsHeroFlagged(cached_data,0):
        capture_hero_flag = True
        capture_flag_all = True
        capture_hero_index = 0
        one_time_set_flag = False
        capture_mouse_timer.Start()

    for i in range(1, party_size):
        if HeroFlags[i-1] != IsHeroFlagged(cached_data,i):
            capture_hero_flag = True
            capture_flag_all = False
            capture_hero_index = i
            one_time_set_flag = False
            capture_mouse_timer.Start()
        

def DrawCandidateWindow(cached_data:CacheData):
    def _OnSameMap(self_account, candidate):
        if (candidate.MapID == self_account.MapID and
            candidate.MapRegion == self_account.MapRegion and
            candidate.MapDistrict == self_account.MapDistrict):
            return True
        return False
    
    def _OnSameParty(self_account, candidate):
        if self_account.PartyID == candidate.PartyID:
            return True
        return False
        
    table_flags = PyImGui.TableFlags.Sortable | PyImGui.TableFlags.Borders | PyImGui.TableFlags.RowBg
    if PyImGui.begin_table("CandidateTable", 2, table_flags):
        # Setup columns
        PyImGui.table_setup_column("Command", PyImGui.TableColumnFlags.NoSort)
        PyImGui.table_setup_column("Candidate", PyImGui.TableColumnFlags.NoFlag)
        PyImGui.table_headers_row()

        account_email = GLOBAL_CACHE.Player.GetAccountEmail()
        self_account = GLOBAL_CACHE.ShMem.GetAccountDataFromEmail(account_email)
        if not self_account:
            PyImGui.text("No account data found.")
            PyImGui.end_table()
            return
        accounts = GLOBAL_CACHE.ShMem.GetAllAccountData()
        
        for account in accounts:
            if account.AccountEmail == account_email:
                continue
            
            if _OnSameMap(self_account, account) and not _OnSameParty(self_account, account):
                PyImGui.table_next_row()
                PyImGui.table_next_column()
                if PyImGui.button(f"Invite##invite_{account.PlayerID}"):
                    GLOBAL_CACHE.Party.Players.InvitePlayer(account.CharacterName)
                    GLOBAL_CACHE.ShMem.SendMessage(account_email, account.AccountEmail,SharedCommandType.InviteToParty, (self_account.PlayerID,0,0,0))
                PyImGui.table_next_column()
                PyImGui.text(f"{account.CharacterName}")
            else:
                if not _OnSameMap(self_account, account):
                    PyImGui.table_next_row()
                    PyImGui.table_next_column()
                    if PyImGui.button(f"Summon##summon_{account.PlayerID}"):
                        GLOBAL_CACHE.ShMem.SendMessage(account_email, account.AccountEmail,SharedCommandType.TravelToMap, (self_account.MapID,self_account.MapRegion,self_account.MapDistrict,0))
                    PyImGui.table_next_column()
                    PyImGui.text(f"{account.CharacterName}")
        PyImGui.end_table()



slot_to_write = 0
def DrawPlayersDebug(cached_data:CacheData):
    global MAX_NUM_PLAYERS, slot_to_write

    own_party_number = cached_data.data.own_party_number
    PyImGui.text(f"Own Party Number: {own_party_number}")
    slot_to_write = PyImGui.input_int("Slot to write", slot_to_write)

    if PyImGui.button("Submit"):
        self_id = cached_data.data.player_agent_id

        cached_data.HeroAI_vars.shared_memory_handler.set_player_property(slot_to_write, "PlayerID", self_id)
        cached_data.HeroAI_vars.shared_memory_handler.set_player_property(slot_to_write, "Energy_Regen", cached_data.data.energy_regen)
        cached_data.HeroAI_vars.shared_memory_handler.set_player_property(slot_to_write, "Energy", cached_data.data.energy)
        cached_data.HeroAI_vars.shared_memory_handler.set_player_property(slot_to_write, "IsActive", True)
        cached_data.HeroAI_vars.shared_memory_handler.set_player_property(slot_to_write, "IsHero", False)
        cached_data.HeroAI_vars.shared_memory_handler.set_player_property(slot_to_write, "IsFlagged", False)
        cached_data.HeroAI_vars.shared_memory_handler.set_player_property(slot_to_write, "FlagPosX", 0.0)
        cached_data.HeroAI_vars.shared_memory_handler.set_player_property(slot_to_write, "FlagPosY", 0.0)


    headers = ["Slot","PlayerID", "EnergyRegen", "Energy","IsActive", "IsHero", "IsFlagged", "FlagPosX", "FlagPosY", "LastUpdated"]

    data = []
    for i in range(MAX_NUM_PLAYERS):
        player = cached_data.HeroAI_vars.all_player_struct[i]
        data.append((
            i,  # Slot index
            player.PlayerID,
            f"{player.Energy_Regen:.4f}", 
            f"{player.Energy:.4f}",       
            player.IsActive,
            player.IsHero,
            player.IsFlagged,
            f"{player.FlagPosX:.4f}",     
            f"{player.FlagPosY:.4f}",     
            player.LastUpdated
        ))

    ImGui.table("Players Debug Table", headers, data)


def DrawHeroesDebug(cached_data:CacheData): 
    global MAX_NUM_PLAYERS
    headers = ["Slot", "agent_id", "owner_player_id", "hero_id", "hero_name"]
    data = []

    heroes = cached_data.data.heroes
    for index, hero in enumerate(heroes):
        data.append((
            index,  # Slot index
            hero.agent_id,
            hero.owner_player_id,
            hero.hero_id.GetID(),
            hero.hero_id.GetName(),
        ))
    ImGui.table("Heroes Debug Table", headers, data)


def DrawGameOptionsDebug(cached_data:CacheData):
    global MAX_NUM_PLAYERS

    data = []
    PyImGui.text("Remote Control Variables")
    PyImGui.text(f"own_party_number: {cached_data.data.own_party_number}")
    headers = ["Control", "Following", "Avoidance", "Looting", "Targeting", "Combat"]
    headers += [f"Skill {j + 1}" for j in range(NUMBER_OF_SKILLS)]
    row = [
        "Remote",  
        cached_data.HeroAI_vars.global_control_game_struct.Following,
        cached_data.HeroAI_vars.global_control_game_struct.Avoidance,
        cached_data.HeroAI_vars.global_control_game_struct.Looting,
        cached_data.HeroAI_vars.global_control_game_struct.Targeting,
        cached_data.HeroAI_vars.global_control_game_struct.Combat,
        cached_data.HeroAI_vars.global_control_game_struct.WindowVisible
    ]

    row += [
        cached_data.HeroAI_vars.global_control_game_struct.Skills[j].Active for j in range(NUMBER_OF_SKILLS)
    ]
    data.append(tuple(row))
    ImGui.table("Control Debug Table", headers, data)

    headers = ["Slot", "Following", "Avoidance", "Looting", "Targeting", "Combat", "WindowVisible"]
    headers += [f"Skill {j + 1}" for j in range(NUMBER_OF_SKILLS)] 

    data = []
    for i in range(MAX_NUM_PLAYERS):
        row = [
            i,  
            cached_data.HeroAI_vars.all_game_option_struct[i].Following,
            cached_data.HeroAI_vars.all_game_option_struct[i].Avoidance,
            cached_data.HeroAI_vars.all_game_option_struct[i].Looting,
            cached_data.HeroAI_vars.all_game_option_struct[i].Targeting,
            cached_data.HeroAI_vars.all_game_option_struct[i].Combat,
            cached_data.HeroAI_vars.all_game_option_struct[i].WindowVisible
        ]

        row += [
            cached_data.HeroAI_vars.all_game_option_struct[i].Skills[j].Active for j in range(NUMBER_OF_SKILLS)
        ]

        data.append(tuple(row))

    ImGui.table("Game Options Debug Table", headers, data)

draw_fake_flag = True
def DrawFlagDebug(cached_data:CacheData):
    global capture_flag_all, capture_hero_flag,draw_fake_flag
    global MAX_NUM_PLAYERS
    
    PyImGui.text("Flag Debug")
    PyImGui.text(f"capture_flag_all: {capture_flag_all}")
    PyImGui.text(f"capture_hero_flag: {capture_hero_flag}")
    if PyImGui.button("Toggle Flags"):
        capture_flag_all = not capture_flag_all
        capture_hero_flag = not capture_hero_flag

    PyImGui.separator()

    x, y, z = Overlay().GetMouseWorldPos()

    PyImGui.text(f"Mouse Position: {x:.2f}, {y:.2f}, {z:.2f}")
    PyImGui.text_colored("Having GetMouseWorldPos active will crash your client on map change",(1, 0.5, 0.05, 1))
    mouse_x, mouse_y = Overlay().GetMouseCoords()
    PyImGui.text(f"Mouse Coords: {mouse_x}, {mouse_y}")
    PyImGui.text(f"Player Position: {cached_data.data.player_xyz}")
    draw_fake_flag = PyImGui.checkbox("Draw Fake Flag", draw_fake_flag)

    if draw_fake_flag:
        DrawFlagAll(x, y)

    PyImGui.separator()

    PyImGui.text(f"AllFlag: {AllFlag}")
    PyImGui.text(f"capture_hero_index: {capture_hero_index}")

    for i in range(MAX_NUM_PLAYERS):
        if HeroFlags[i]:
            PyImGui.text(f"Hero {i + 1} is flagged")

def DrawFollowDebug(cached_data:CacheData):
    global show_area_rings, show_hero_follow_grid, show_distance_on_followers
    global MAX_NUM_PLAYERS


    if PyImGui.button("reset overlay"):
        Overlay().RefreshDrawList()
    show_area_rings = PyImGui.checkbox("Show Area Rings", show_area_rings)
    show_hero_follow_grid = PyImGui.checkbox("Show Hero Follow Grid", show_hero_follow_grid)
    show_distance_on_followers = PyImGui.checkbox("Show Distance on Followers", show_distance_on_followers)
    PyImGui.separator()
    PyImGui.text(f"InAggro: {cached_data.data.in_aggro}")
    PyImGui.text(f"IsMelee: {GLOBAL_CACHE.Agent.IsMelee(cached_data.data.player_agent_id)}")
    PyImGui.text(f"Nearest Enemy: {cached_data.data.nearest_enemy}")
    PyImGui.text(f"stay_alert_timer: {cached_data.stay_alert_timer.GetElapsedTime()}")
    PyImGui.text(f"Leader Rotation Angle: {cached_data.data.party_leader_rotation_angle}")
    PyImGui.text(f"old_leader_rotation_angle: {cached_data.data.old_angle}")
    PyImGui.text(f"Angle_changed: {cached_data.data.angle_changed}")

    segments = 32
    Overlay().BeginDraw()
    if show_area_rings:
        player_x, player_y, player_z = GLOBAL_CACHE.Agent.GetXYZ(GLOBAL_CACHE.Player.GetAgentID()) #cached_data.data.player_xyz # needs to be live

        Overlay().DrawPoly3D(player_x, player_y, player_z, Range.Touch.value / 2, Utils.RGBToColor(255, 255, 0 , 128), numsegments=segments, thickness=2.0)
        Overlay().DrawPoly3D(player_x, player_y, player_z, Range.Touch.value    , Utils.RGBToColor(255, 200, 0 , 128), numsegments=segments, thickness=2.0)
        Overlay().DrawPoly3D(player_x, player_y, player_z, Range.Adjacent.value , Utils.RGBToColor(255, 150, 0 , 128), numsegments=segments, thickness=2.0)
        Overlay().DrawPoly3D(player_x, player_y, player_z, Range.Nearby.value   , Utils.RGBToColor(255, 100, 0 , 128), numsegments=segments, thickness=2.0)
        Overlay().DrawPoly3D(player_x, player_y, player_z, Range.Area.value     , Utils.RGBToColor(255, 50 , 0 , 128), numsegments=segments, thickness=2.0)
        Overlay().DrawPoly3D(player_x, player_y, player_z, Range.Earshot.value  , Utils.RGBToColor(255, 25 , 0 , 128), numsegments=segments, thickness=2.0)
        Overlay().DrawPoly3D(player_x, player_y, player_z, Range.Spellcast.value, Utils.RGBToColor(255, 12 , 0 , 128), numsegments=segments, thickness=2.0)

    if show_hero_follow_grid:
        leader_x, leader_y, leader_z = GLOBAL_CACHE.Agent.GetXYZ(GLOBAL_CACHE.Party.GetPartyLeaderID()) #cached_data.data.party_leader_xyz #needs to be live 

        for index, angle in enumerate(hero_formation):
            if index == 0:
                continue
            angle_on_hero_grid = GLOBAL_CACHE.Agent.GetRotationAngle(GLOBAL_CACHE.Party.GetPartyLeaderID()) + Utils.DegToRad(angle)
            hero_x = Range.Touch.value * math.cos(angle_on_hero_grid) + leader_x
            hero_y = Range.Touch.value * math.sin(angle_on_hero_grid) + leader_y
            
            Overlay().DrawPoly3D(hero_x, hero_y, leader_z, radius=Range.Touch.value /2, color=Utils.RGBToColor(255, 0, 255, 128), numsegments=segments, thickness=2.0)
 
    if show_distance_on_followers:
        for i in range(MAX_NUM_PLAYERS):
            if cached_data.HeroAI_vars.all_player_struct[i].IsActive:
                Overlay().BeginDraw()
                player_id = cached_data.HeroAI_vars.all_player_struct[i].PlayerID
                if player_id == cached_data.data.player_agent_id:
                    continue
                target_x, target_y, target_z = GLOBAL_CACHE.Agent.GetXYZ(player_id)
                Overlay().DrawPoly3D(target_x, target_y, target_z, radius=72, color=Utils.RGBToColor(255, 255, 255, 128),numsegments=segments,thickness=2.0)
                z_coord = Overlay().FindZ(target_x, target_y, 0)
                Overlay().DrawText3D(target_x, target_y, z_coord-130, f"{DistanceFromWaypoint(target_x, target_y):.1f}",color=Utils.RGBToColor(255, 255, 255, 128), autoZ=False, centered=True, scale=2.0)
    
    Overlay().EndDraw()
    
def DrawOptions(cached_data:CacheData):
    cached_data.ui_state_data.show_classic_controls = PyImGui.checkbox("Show Classic Controls", cached_data.ui_state_data.show_classic_controls)
    #TODO Select combat engine options


class ButtonColor:
    def __init__(self, button_color:Color, hovered_color:Color, active_color:Color):
        self.button_color = button_color
        self.hovered_color = hovered_color
        self.active_color = active_color
      

ButtonColors = {
    "Resign": ButtonColor(button_color=Color(90,0,10,255), hovered_color=Color(160,0,15,255), active_color=Color(210,0,20,255)),  
    "PixelStack": ButtonColor(button_color=Color(90,0,10,255), hovered_color=Color(160,0,15,255), active_color=Color(190,0,20,255)),
    "Flag": ButtonColor(button_color=Color(90,0,10,255), hovered_color=Color(160,0,15,255), active_color=Color(190,0,20,255)),
    "ClearFlags": ButtonColor(button_color=Color(90,0,10,255), hovered_color=Color(160,0,15,255), active_color=Color(190,0,20,255)),
    "Celerity": ButtonColor(button_color = Color(129, 33, 188, 255), hovered_color = Color(165, 100, 200, 255), active_color = Color(135, 225, 230, 255)),  
    "GrailOfMight": ButtonColor(button_color=Color(70,0,10,255), hovered_color=Color(160,0,15,255), active_color=Color(252,225,115,255)),
    "ArmorOfSalvation": ButtonColor(button_color = Color(96, 60, 15, 255),hovered_color = Color(187, 149, 38, 255),active_color = Color(225, 150, 0, 255)),
    "CandyCane": ButtonColor(button_color = Color(63, 91, 54, 255),hovered_color = Color(149, 72, 34, 255),active_color = Color(96, 172, 28, 255)),
    "BirthdayCupcake": ButtonColor(button_color = Color(138, 54, 80, 255),hovered_color = Color(255, 186, 198, 255),active_color = Color(205, 94, 215, 255)),
    "GoldenEgg": ButtonColor(button_color = Color(245, 227, 143, 255),hovered_color = Color(253, 248, 234, 255),active_color = Color(129, 82, 35, 255)),
    "CandyCorn": ButtonColor(button_color = Color(239, 174, 33, 255),hovered_color = Color(206, 178, 148, 255),active_color = Color(239, 77, 16, 255)),
    "CandyApple": ButtonColor(button_color = Color(75, 26, 28, 255),hovered_color = Color(202, 60, 88, 255),active_color = Color(179, 0, 39, 255)),
    "PumpkinPie": ButtonColor(button_color = Color(224, 176, 126, 255),hovered_color = Color(226, 209, 210, 255),active_color = Color(129, 87, 54, 255)),
    "DrakeKabob": ButtonColor(button_color = Color(28, 28, 28, 255),hovered_color = Color(190, 187, 184, 255),active_color = Color(94, 26, 13, 255)),
    "SkalefinSoup": ButtonColor(button_color = Color(68, 85, 142, 255),hovered_color = Color(255, 255, 107, 255),active_color = Color(106, 139, 51, 255)),
    "PahnaiSalad": ButtonColor(button_color = Color(113, 43, 25, 255),hovered_color = Color(185, 157, 90, 255),active_color = Color(137, 175, 10, 255)),
    "WarSupplies": ButtonColor(button_color = Color(51, 26, 13, 255),hovered_color = Color(113, 43, 25, 255),active_color = Color(202, 115, 77, 255)),
    "Alcohol": ButtonColor(button_color = Color(58, 41, 50, 255),hovered_color = Color(169, 145, 111, 255),active_color = Color(173, 173, 156, 255)),
    "Blank": ButtonColor(button_color= Color(0, 0, 0, 0), hovered_color=Color(0, 0, 0, 0), active_color=Color(0, 0, 0, 0)),
}

show_confirm_dialog = False
dialog_options = []
target_id = 0



def DrawMessagingOptions(cached_data:CacheData):
    def _post_pcon_message(params):
        self_account = GLOBAL_CACHE.ShMem.GetAccountDataFromEmail(cached_data.account_email)
        if not self_account:
            return
        accounts = GLOBAL_CACHE.ShMem.GetAllAccountData()
        sender_email = cached_data.account_email
        for account in accounts:
            ConsoleLog("Messaging", f"Sending Pcon Message to  {account.AccountEmail}")
            
            GLOBAL_CACHE.ShMem.SendMessage(sender_email, account.AccountEmail, SharedCommandType.PCon, params)

    if ImGui.colored_button(f"{IconsFontAwesome5.ICON_TIMES}##commands_resign", ButtonColors["Resign"].button_color, ButtonColors["Resign"].hovered_color, ButtonColors["Resign"].active_color):
    #if PyImGui.button(f"{IconsFontAwesome5.ICON_TIMES}##commands_resign"):
        accounts = GLOBAL_CACHE.ShMem.GetAllAccountData()
        sender_email = cached_data.account_email
        for account in accounts:
            ConsoleLog("Messaging", "Resigning account: " + account.AccountEmail)
            GLOBAL_CACHE.ShMem.SendMessage(sender_email, account.AccountEmail, SharedCommandType.Resign, (0,0,0,0))
    ImGui.show_tooltip("Resign Party")
    
    PyImGui.same_line(0,-1)
    PyImGui.text("|")
    PyImGui.same_line(0,-1)

    if PyImGui.button(f"{IconsFontAwesome5.ICON_COMPRESS_ARROWS_ALT}##commands_pixelstack"):
        self_account = GLOBAL_CACHE.ShMem.GetAccountDataFromEmail(cached_data.account_email)
        if not self_account:
            return
        accounts = GLOBAL_CACHE.ShMem.GetAllAccountData()
        sender_email = cached_data.account_email
        for account in accounts:
            if self_account.AccountEmail == account.AccountEmail:
                continue
            ConsoleLog("Messaging", "Pixelstacking account: " + account.AccountEmail)
            GLOBAL_CACHE.ShMem.SendMessage(sender_email, account.AccountEmail, SharedCommandType.PixelStack, (self_account.PlayerPosX,self_account.PlayerPosY,0,0))
    ImGui.show_tooltip("Pixel Stack (Carto Helper)")
    
    PyImGui.same_line(0,-1)

    if PyImGui.button(f"{IconsFontAwesome5.ICON_HAND_POINT_RIGHT}##commands_InteractTarget"):
        target = GLOBAL_CACHE.Player.GetTargetID()
        if target == 0:
            ConsoleLog("Messaging", "No target to interact with.")
            return
        self_account = GLOBAL_CACHE.ShMem.GetAccountDataFromEmail(cached_data.account_email)
        if not self_account:
            return
        accounts = GLOBAL_CACHE.ShMem.GetAllAccountData()
        sender_email = cached_data.account_email
        for account in accounts:
            if self_account.AccountEmail == account.AccountEmail:
                continue
            ConsoleLog("Messaging", f"Ordering {account.AccountEmail} to interact with target: {target}")
            GLOBAL_CACHE.ShMem.SendMessage(sender_email, account.AccountEmail, SharedCommandType.InteractWithTarget, (target,0,0,0))
    ImGui.show_tooltip("Interact with Target")
    PyImGui.same_line(0,-1)

    if PyImGui.button(f"{IconsFontAwesome5.ICON_COMMENT_DOTS}##commands_takedialog"):
        target = GLOBAL_CACHE.Player.GetTargetID()
        if target == 0:
            ConsoleLog("Messaging", "No target to interact with.")
            return
        if not UIManager.IsNPCDialogVisible():
            ConsoleLog("Messaging", "No dialog is open.")
            return
        
        # i need to display a modal dialog here to confirm options
        options = UIManager.GetDialogButtonCount()
        
        self_account = GLOBAL_CACHE.ShMem.GetAccountDataFromEmail(cached_data.account_email)
        if not self_account:
            return
        accounts = GLOBAL_CACHE.ShMem.GetAllAccountData()
        sender_email = cached_data.account_email
        for account in accounts:
            if self_account.AccountEmail == account.AccountEmail:
                continue
            ConsoleLog("Messaging", f"Ordering {account.AccountEmail} to interact with target: {target}")
            GLOBAL_CACHE.ShMem.SendMessage(sender_email, account.AccountEmail, SharedCommandType.InteractWithTarget, (target,1,0,0))
    ImGui.show_tooltip("Get Dialog")
    PyImGui.separator()
    if PyImGui.collapsing_header("PCons"):
        PyImGui.push_style_color(PyImGui.ImGuiCol.Text, ButtonColors["Celerity"].active_color.to_tuple_normalized())
        if ImGui.colored_button(f"{IconsFontAwesome5.ICON_GLOBE_ASIA}##commands_pcon_celerity", 
                                ButtonColors["Celerity"].button_color, 
                                ButtonColors["Celerity"].hovered_color, 
                                ButtonColors["Celerity"].active_color, 
                                width=30, height=30):
            _post_pcon_message((ModelID.Essence_Of_Celerity.value, GLOBAL_CACHE.Skill.GetID("Essence_of_Celerity_item_effect"), 0, 0))
        PyImGui.pop_style_color(1)
        ImGui.show_tooltip("Esence of Celerity")
        
        PyImGui.same_line(0,-1)
        PyImGui.push_style_color(PyImGui.ImGuiCol.Text, ButtonColors["GrailOfMight"].active_color.to_tuple_normalized())
        if ImGui.colored_button(f"{IconsFontAwesome5.ICON_WINE_GLASS}##commands_pcon_grail_of_might", 
                                ButtonColors["GrailOfMight"].button_color, 
                                ButtonColors["GrailOfMight"].hovered_color, 
                                ButtonColors["GrailOfMight"].active_color, 
                                width=30, height=30):
            _post_pcon_message((ModelID.Grail_Of_Might.value, GLOBAL_CACHE.Skill.GetID("Grail_of_Might_item_effect"), 0, 0))
        PyImGui.pop_style_color(1)
        ImGui.show_tooltip("Grail of Might")
        
        PyImGui.same_line(0,-1)
        PyImGui.push_style_color(PyImGui.ImGuiCol.Text, ButtonColors["ArmorOfSalvation"].active_color.to_tuple_normalized())
        if ImGui.colored_button(f"{IconsFontAwesome5.ICON_SPLOTCH}##commands_pcon_ArmorOfSalvation", 
                                ButtonColors["ArmorOfSalvation"].button_color, 
                                ButtonColors["ArmorOfSalvation"].hovered_color, 
                                ButtonColors["ArmorOfSalvation"].active_color, 
                                width=30, height=30):
            _post_pcon_message((ModelID.Armor_Of_Salvation.value, GLOBAL_CACHE.Skill.GetID("Armor_of_Salvation_item_effect"), 0, 0))
        PyImGui.pop_style_color(1)
        ImGui.show_tooltip("Armor of Salvation")
        
        PyImGui.same_line(0,-1)
        PyImGui.text("|")
        PyImGui.same_line(0,-1)
        
        PyImGui.push_style_color(PyImGui.ImGuiCol.Text, ButtonColors["CandyCane"].active_color.to_tuple_normalized())
        if ImGui.colored_button(f"{IconsFontAwesome5.ICON_CANDY_CANE}##commands_pcon_CandyCane", 
                                ButtonColors["CandyCane"].button_color, 
                                ButtonColors["CandyCane"].hovered_color, 
                                ButtonColors["CandyCane"].active_color, 
                                width=30, height=30):
            _post_pcon_message((ModelID.Rainbow_Cc.value, 0, ModelID.Honeycomb.value, 0))
        PyImGui.pop_style_color(1)
        ImGui.show_tooltip("Rainbow Candy Cane / Honeycomb")
        PyImGui.separator()
        

        PyImGui.push_style_color(PyImGui.ImGuiCol.Text, ButtonColors["BirthdayCupcake"].active_color.to_tuple_normalized())
        if ImGui.colored_button(f"{IconsFontAwesome5.ICON_BIRTHDAY_CAKE}##commands_pcon_BirthdayCupcake", 
                                ButtonColors["BirthdayCupcake"].button_color, 
                                ButtonColors["BirthdayCupcake"].hovered_color, 
                                ButtonColors["BirthdayCupcake"].active_color, 
                                width=30, height=30):
            _post_pcon_message((ModelID.Birthday_Cupcake.value, GLOBAL_CACHE.Skill.GetID("Birthday_Cupcake_skill"), 0, 0))
        PyImGui.pop_style_color(1)
        ImGui.show_tooltip("Birthday Cupcake")
        
        PyImGui.same_line(0,-1)
        PyImGui.push_style_color(PyImGui.ImGuiCol.Text, ButtonColors["GoldenEgg"].active_color.to_tuple_normalized())
        if ImGui.colored_button(f"{IconsFontAwesome5.ICON_EGG}##commands_pcon_GoldenEgg", 
                                ButtonColors["GoldenEgg"].button_color, 
                                ButtonColors["GoldenEgg"].hovered_color, 
                                ButtonColors["GoldenEgg"].active_color, 
                                width=30, height=30):
            _post_pcon_message((ModelID.Golden_Egg.value, GLOBAL_CACHE.Skill.GetID("Golden_Egg_skill"), 0, 0))
        PyImGui.pop_style_color(1)
        ImGui.show_tooltip("Golden Egg")
        
        PyImGui.same_line(0,-1)
        PyImGui.push_style_color(PyImGui.ImGuiCol.Text, ButtonColors["CandyCorn"].active_color.to_tuple_normalized())
        if ImGui.colored_button(f"{IconsFontAwesome5.ICON_CARROT}##commands_pcon_CandyCorn", 
                                ButtonColors["CandyCorn"].button_color, 
                                ButtonColors["CandyCorn"].hovered_color, 
                                ButtonColors["CandyCorn"].active_color, 
                                width=30, height=30):
            _post_pcon_message((ModelID.Candy_Corn.value, GLOBAL_CACHE.Skill.GetID("Candy_Corn_skill"), 0, 0))
        PyImGui.pop_style_color(1)
        ImGui.show_tooltip("Candy Corn")
        
        PyImGui.same_line(0,-1)
        PyImGui.text("|")
        PyImGui.same_line(0,-1)
        
        PyImGui.push_style_color(PyImGui.ImGuiCol.Text, ButtonColors["Alcohol"].active_color.to_tuple_normalized())
        if ImGui.colored_button(f"{IconsFontAwesome5.ICON_WINE_BOTTLE}##commands_pcon_Alcohol", 
                                ButtonColors["Alcohol"].button_color, 
                                ButtonColors["Alcohol"].hovered_color, 
                                ButtonColors["Alcohol"].active_color, 
                                width=30, height=30):
            pass
        PyImGui.pop_style_color(1)
        ImGui.show_tooltip("Alcohol")
        PyImGui.separator()
        
        PyImGui.push_style_color(PyImGui.ImGuiCol.Text, ButtonColors["CandyApple"].active_color.to_tuple_normalized())
        if ImGui.colored_button(f"{IconsFontAwesome5.ICON_APPLE_ALT}##commands_pcon_CandyApple", 
                                ButtonColors["CandyApple"].button_color, 
                                ButtonColors["CandyApple"].hovered_color, 
                                ButtonColors["CandyApple"].active_color, 
                                width=30, height=30):
            _post_pcon_message((ModelID.Candy_Apple.value, GLOBAL_CACHE.Skill.GetID("Candy_Apple_skill"), 0, 0))
        PyImGui.pop_style_color(1)
        ImGui.show_tooltip("Candy Apple")
        
        PyImGui.same_line(0,-1)
        PyImGui.push_style_color(PyImGui.ImGuiCol.Text, ButtonColors["PumpkinPie"].active_color.to_tuple_normalized())
        if ImGui.colored_button(f"{IconsFontAwesome5.ICON_CHEESE}##commands_pcon_PumpkinPie", 
                                ButtonColors["PumpkinPie"].button_color, 
                                ButtonColors["PumpkinPie"].hovered_color, 
                                ButtonColors["PumpkinPie"].active_color, 
                                width=30, height=30):
            _post_pcon_message((ModelID.Slice_Of_Pumpkin_Pie.value, GLOBAL_CACHE.Skill.GetID("Pie_Induced_Ecstasy"), 0, 0))
        PyImGui.pop_style_color(1)
        ImGui.show_tooltip("Slice of Pumpkin Pie")
        
        PyImGui.same_line(0,-1)
        PyImGui.push_style_color(PyImGui.ImGuiCol.Text, ButtonColors["DrakeKabob"].active_color.to_tuple_normalized())
        if ImGui.colored_button(f"{IconsFontAwesome5.ICON_SLASH}##commands_pcon_DrakeKabob", 
                                ButtonColors["DrakeKabob"].button_color, 
                                ButtonColors["DrakeKabob"].hovered_color, 
                                ButtonColors["DrakeKabob"].active_color, 
                                width=30, height=30):
            _post_pcon_message((ModelID.Drake_Kabob.value, GLOBAL_CACHE.Skill.GetID("Drake_Skin"), 0, 0))
        PyImGui.pop_style_color(1)
        ImGui.show_tooltip("Drake Kabob")

        PyImGui.separator()
        
        PyImGui.push_style_color(PyImGui.ImGuiCol.Text, ButtonColors["SkalefinSoup"].active_color.to_tuple_normalized())
        if ImGui.colored_button(f"{IconsFontAwesome5.ICON_MORTAR_PESTLE}##commands_pcon_SkalefinSoup", 
                                ButtonColors["SkalefinSoup"].button_color, 
                                ButtonColors["SkalefinSoup"].hovered_color, 
                                ButtonColors["SkalefinSoup"].active_color, 
                                width=30, height=30):
            _post_pcon_message((ModelID.Bowl_Of_Skalefin_Soup.value, GLOBAL_CACHE.Skill.GetID("Skale_Vigor"), 0, 0))
        PyImGui.pop_style_color(1)
        ImGui.show_tooltip("Skalefin Soup")
        
        PyImGui.same_line(0,-1)
        PyImGui.push_style_color(PyImGui.ImGuiCol.Text, ButtonColors["PahnaiSalad"].active_color.to_tuple_normalized())
        if ImGui.colored_button(f"{IconsFontAwesome5.ICON_RING}##commands_pcon_PahnaiSalad", 
                                ButtonColors["PahnaiSalad"].button_color, 
                                ButtonColors["PahnaiSalad"].hovered_color, 
                                ButtonColors["PahnaiSalad"].active_color, 
                                width=30, height=30):
            _post_pcon_message((ModelID.Pahnai_Salad.value, GLOBAL_CACHE.Skill.GetID("Pahnai_Salad_item_effect"), 0, 0))
        PyImGui.pop_style_color(1)
        ImGui.show_tooltip("Pahnai Salad")
        
        PyImGui.same_line(0,-1)
        PyImGui.push_style_color(PyImGui.ImGuiCol.Text, ButtonColors["WarSupplies"].active_color.to_tuple_normalized())
        if ImGui.colored_button(f"{IconsFontAwesome5.ICON_TOOLBOX}##commands_pcon_WarSupplies", 
                                ButtonColors["WarSupplies"].button_color, 
                                ButtonColors["WarSupplies"].hovered_color, 
                                ButtonColors["WarSupplies"].active_color, 
                                width=30, height=30):
            _post_pcon_message((ModelID.War_Supplies.value, GLOBAL_CACHE.Skill.GetID("Well_Supplied"), 0, 0))
        PyImGui.pop_style_color(1)
        ImGui.show_tooltip("War Supplies")
    
    

def DrawDebugWindow(cached_data:CacheData):
    global MAX_NUM_PLAYERS

    if PyImGui.collapsing_header("Players Debug"):
        DrawPlayersDebug(cached_data)
    if PyImGui.collapsing_header("Game Options Debug"):
        DrawGameOptionsDebug(cached_data)

    if PyImGui.collapsing_header("Heroes Debug"):
        DrawHeroesDebug(cached_data)

    if cached_data.data.is_explorable:
        if PyImGui.collapsing_header("Follow Debug"):
            DrawFollowDebug(cached_data)
        if PyImGui.collapsing_header("Flag Debug"):
            DrawFlagDebug(cached_data)
        if PyImGui.collapsing_header("Prioritized Skills"):
            DrawPrioritizedSkills(cached_data)
        if PyImGui.collapsing_header("Buff Debug"):
            DrawBuffWindow(cached_data)
        



def DrawMultiboxTools(cached_data:CacheData):
    global MAX_NUM_PLAYERS
    cached_data.HeroAI_windows.tools_window.initialize()

    if cached_data.HeroAI_windows.tools_window.begin():
        if cached_data.data.is_outpost and cached_data.data.player_agent_id == cached_data.data.party_leader_id:
            if PyImGui.collapsing_header("Party Setup",PyImGui.TreeNodeFlags.DefaultOpen):
                DrawCandidateWindow(cached_data)
        if cached_data.data.is_explorable and cached_data.data.player_agent_id == cached_data.data.party_leader_id:
            if PyImGui.collapsing_header("Flagging"):
                DrawFlaggingWindow(cached_data)

        if PyImGui.collapsing_header("Debug Options"):
            DrawDebugWindow(cached_data)
   
    cached_data.HeroAI_windows.tools_window.process_window()
    cached_data.HeroAI_windows.tools_window.end()



def CompareAndSubmitGameOptions(cached_data:CacheData, game_option: GameOptionStruct):   
    global MAX_NUM_PLAYERS
    # Core Options
    accounts = GLOBAL_CACHE.ShMem.GetAllAccountData()
    if not accounts:
        ConsoleLog("HeroAI", "No accounts found in shared memory.")
        return
    
    if game_option.Following != cached_data.HeroAI_vars.global_control_game_struct.Following:
        cached_data.HeroAI_vars.global_control_game_struct.Following = game_option.Following
        for account in accounts:
            account_email = account.AccountEmail
            hero_ai_data = GLOBAL_CACHE.ShMem.GetHeroAIOptions(account_email)
            if hero_ai_data is None:
                ConsoleLog("HeroAI", f"Failed to get HeroAI options for {account_email} from shared memory.")
                continue
            
            hero_ai_data.Following = game_option.Following


    if game_option.Avoidance != cached_data.HeroAI_vars.global_control_game_struct.Avoidance:
        cached_data.HeroAI_vars.global_control_game_struct.Avoidance = game_option.Avoidance
        for account in accounts:
            account_email = account.AccountEmail
            hero_ai_data = GLOBAL_CACHE.ShMem.GetHeroAIOptions(account_email)
            if hero_ai_data is None:
                ConsoleLog("HeroAI", f"Failed to get HeroAI options for {account_email} from shared memory.")
                continue
            
            hero_ai_data.Avoidance = game_option.Avoidance

    if game_option.Looting != cached_data.HeroAI_vars.global_control_game_struct.Looting:
        cached_data.HeroAI_vars.global_control_game_struct.Looting = game_option.Looting
        for account in accounts:
            account_email = account.AccountEmail
            hero_ai_data = GLOBAL_CACHE.ShMem.GetHeroAIOptions(account_email)
            if hero_ai_data is None:
                ConsoleLog("HeroAI", f"Failed to get HeroAI options for {account_email} from shared memory.")
                continue
            
            hero_ai_data.Looting = game_option.Looting

    if game_option.Targeting != cached_data.HeroAI_vars.global_control_game_struct.Targeting:
        cached_data.HeroAI_vars.global_control_game_struct.Targeting = game_option.Targeting
        for account in accounts:
            account_email = account.AccountEmail
            hero_ai_data = GLOBAL_CACHE.ShMem.GetHeroAIOptions(account_email)
            if hero_ai_data is None:
                ConsoleLog("HeroAI", f"Failed to get HeroAI options for {account_email} from shared memory.")
                continue
            
            hero_ai_data.Targeting = game_option.Targeting

    if game_option.Combat != cached_data.HeroAI_vars.global_control_game_struct.Combat:
        cached_data.HeroAI_vars.global_control_game_struct.Combat = game_option.Combat
        for account in accounts:
            account_email = account.AccountEmail
            hero_ai_data = GLOBAL_CACHE.ShMem.GetHeroAIOptions(account_email)
            if hero_ai_data is None:
                ConsoleLog("HeroAI", f"Failed to get HeroAI options for {account_email} from shared memory.")
                continue
            
            hero_ai_data.Combat = game_option.Combat

    # Skills
    for skill_index in range(NUMBER_OF_SKILLS):
        if game_option.Skills[skill_index].Active != cached_data.HeroAI_vars.global_control_game_struct.Skills[skill_index].Active:
            cached_data.HeroAI_vars.global_control_game_struct.Skills[skill_index].Active = game_option.Skills[skill_index].Active
            for account in accounts:
                account_email = account.AccountEmail
                hero_ai_data = GLOBAL_CACHE.ShMem.GetHeroAIOptions(account_email)
                if hero_ai_data is None:
                    ConsoleLog("HeroAI", f"Failed to get HeroAI options for {account_email} from shared memory.")
                    continue
                
                hero_ai_data.Skills[skill_index] = game_option.Skills[skill_index].Active


def SubmitGameOptions(cached_data:CacheData,party_pos,game_option,original_game_option):
    # Core Options
    hero_ai_data = GLOBAL_CACHE.ShMem.GetGerHeroAIOptionsByPartyNumber(party_pos)
    if hero_ai_data is None:
        ConsoleLog("HeroAI", "Failed to get HeroAI options from shared memory.")
        return
    if game_option.Following != original_game_option.Following:
        hero_ai_data.Following = game_option.Following
        ConsoleLog("HeroAI", f"Following set to {game_option.Following} for party {party_pos}")
        #cached_data.HeroAI_vars.shared_memory_handler.set_game_option_property(index, "Following", game_option.Following)

    if game_option.Avoidance != original_game_option.Avoidance:
        hero_ai_data.Avoidance = game_option.Avoidance
        ConsoleLog("HeroAI", f"Avoidance set to {game_option.Avoidance} for party {party_pos}")
        #cached_data.HeroAI_vars.shared_memory_handler.set_game_option_property(index, "Avoidance", game_option.Avoidance)

    if game_option.Looting != original_game_option.Looting:
        hero_ai_data.Looting = game_option.Looting
        ConsoleLog("HeroAI", f"Looting set to {game_option.Looting} for party {party_pos}")
        #cached_data.HeroAI_vars.shared_memory_handler.set_game_option_property(index, "Looting", game_option.Looting)

    if game_option.Targeting != original_game_option.Targeting:
        hero_ai_data.Targeting = game_option.Targeting
        ConsoleLog("HeroAI", f"Targeting set to {game_option.Targeting} for party {party_pos}")
        #cached_data.HeroAI_vars.shared_memory_handler.set_game_option_property(index, "Targeting", game_option.Targeting)

    if game_option.Combat != original_game_option.Combat:
        hero_ai_data.Combat = game_option.Combat
        ConsoleLog("HeroAI", f"Combat set to {game_option.Combat} for party {party_pos}")
        #cached_data.HeroAI_vars.shared_memory_handler.set_game_option_property(index, "Combat", game_option.Combat)

    # Skills
    for i in range(NUMBER_OF_SKILLS):
        if game_option.Skills[i].Active != original_game_option.Skills[i].Active:
            hero_ai_data.Skills[i] = game_option.Skills[i].Active
            ConsoleLog("HeroAI", f"Skill {i + 1} set to {game_option.Skills[i].Active} for party {party_pos}")
            #cached_data.HeroAI_vars.shared_memory_handler.set_game_option_property(index, f"Skill_{i + 1}", game_option.Skills[i].Active)

def DrawPanelButtons(source_game_option):
    game_option = GameOptionStruct()
    if PyImGui.begin_table("GameOptionTable", 5):
        PyImGui.table_next_row()
        PyImGui.table_next_column()
        game_option.Following = ImGui.toggle_button(IconsFontAwesome5.ICON_RUNNING + "##Following", source_game_option.Following,40,40)
        ImGui.show_tooltip("Following")
        PyImGui.table_next_column()
        game_option.Avoidance = ImGui.toggle_button(IconsFontAwesome5.ICON_PODCAST + "##Avoidance", source_game_option.Avoidance,40,40)
        ImGui.show_tooltip("Avoidance")
        PyImGui.table_next_column()
        game_option.Looting = ImGui.toggle_button(IconsFontAwesome5.ICON_COINS + "##Looting", source_game_option.Looting,40,40)
        ImGui.show_tooltip("Looting")
        PyImGui.table_next_column()
        game_option.Targeting = ImGui.toggle_button(IconsFontAwesome5.ICON_BULLSEYE + "##Targeting", source_game_option.Targeting,40,40)
        ImGui.show_tooltip("Targeting")
        PyImGui.table_next_column()
        game_option.Combat = ImGui.toggle_button(IconsFontAwesome5.ICON_SKULL_CROSSBONES + "##Combat", source_game_option.Combat,40,40)
        ImGui.show_tooltip("Combat")
        PyImGui.end_table()

    if PyImGui.begin_table("SkillsTable", NUMBER_OF_SKILLS + 1):
        PyImGui.table_next_row()
        for i in range(NUMBER_OF_SKILLS):
            PyImGui.table_next_column()
            game_option.Skills[i].Active = ImGui.toggle_button(f"{i + 1}##Skill{i}", source_game_option.Skills[i].Active,22,22)
            ImGui.show_tooltip(f"Skill {i + 1}")
        PyImGui.end_table()

    return game_option

def DrawMainWindow(cached_data:CacheData):
    own_party_number = cached_data.data.own_party_number
    game_option = GameOptionStruct()
    original_game_option = cached_data.HeroAI_vars.all_game_option_struct[own_party_number]
     
    if not original_game_option.WindowVisible:
        return

    if own_party_number <= 0:
        return

    cached_data.HeroAI_windows.main_window.initialize()
    if cached_data.HeroAI_windows.main_window.begin():
        game_option = DrawPanelButtons(original_game_option) 
        SubmitGameOptions(cached_data,own_party_number,game_option,original_game_option)

        cached_data.HeroAI_windows.main_window.process_window()
        cached_data.HeroAI_windows.main_window.end()


def DrawControlPanelWindow(cached_data:CacheData):
    global MAX_NUM_PLAYERS
    own_party_number = cached_data.data.own_party_number
    game_option = GameOptionStruct()     
    if own_party_number != 0:
        return

    cached_data.HeroAI_windows.control_window.initialize()
    if cached_data.HeroAI_windows.control_window.begin():   
        game_option = DrawPanelButtons(cached_data.HeroAI_vars.global_control_game_struct) 
        CompareAndSubmitGameOptions(cached_data,game_option)

        if PyImGui.collapsing_header("Player Control"):
            for index in range(MAX_NUM_PLAYERS):
                if cached_data.HeroAI_vars.all_player_struct[index].IsActive and not cached_data.HeroAI_vars.all_player_struct[index].IsHero:
                    original_game_option = cached_data.HeroAI_vars.all_game_option_struct[index]
                    login_number = GLOBAL_CACHE.Party.Players.GetLoginNumberByAgentID(cached_data.HeroAI_vars.all_player_struct[index].PlayerID)
                    player_name = GLOBAL_CACHE.Party.Players.GetPlayerNameByLoginNumber(login_number)
                    if PyImGui.tree_node(f"{player_name}##ControlPlayer{index}"):
                        game_option2 = DrawPanelButtons(original_game_option)
                        ConsoleLog("HeroAI", f"Submitting game options for player {player_name} at index {index}")
                        SubmitGameOptions(cached_data, index, game_option2, original_game_option)
                        PyImGui.tree_pop()

        cached_data.HeroAI_windows.control_window.process_window()
    cached_data.HeroAI_windows.control_window.end()
   

