from operator import index
from Py4GWCoreLib import *
from .constants import *
from .types import *
from .globals import *
from .utils import *
from .candidates import SendPartyCommand
from .targetting import *
from HeroAI import game_option
from .combat import CombatClass


def DrawBuffWindow():
    if not Map.IsExplorable():
        return

    for index in range(MAX_NUM_PLAYERS):
        player_struct = HeroAI_vars.all_player_struct[index]
        if player_struct.IsActive:
            if Agent.IsPlayer(player_struct.PlayerID):
                player_name = Agent.GetName(player_struct.PlayerID)
            else:
                player_name = Party.Heroes.GetNameByAgentID(player_struct.PlayerID)

            if PyImGui.tree_node(f"{player_name}##DebugBuffsPlayer{index}"):
                # Retrieve buffs for the player
                player_buffs = HeroAI_vars.shared_memory_handler.get_agent_buffs(player_struct.PlayerID)
                headers = ["Skill ID", "Skill Name"]
                data = [(skill_id, Skill.GetName(skill_id)) for skill_id in player_buffs]
                ImGui.table(f"{player_name} Buffs", headers, data)
                PyImGui.tree_pop()


def TrueFalseColor(condition):
    if condition:
        return RGBToNormal(0, 255, 0, 255)
    else:
        return RGBToNormal(255, 0, 0, 255)

skill_slot = 0
def DrawPrioritizedSkills(combat_handler: CombatClass):
    global skill_slot
    from .constants import NUMBER_OF_SKILLS
    from .combat import CombatClass

    # combat_handler.PrioritizeSkills()

    in_casting_routine = combat_handler.InCastingRoutine()
    PyImGui.text_colored(f"InCastingRoutine: {in_casting_routine}",TrueFalseColor(not in_casting_routine))
    PyImGui.text(f"aftercast_timer: {combat_handler.aftercast_timer.GetElapsedTime()}")
    ordered_skills = combat_handler.GetOrderedSkills()
    if ordered_skills is not None:
        txt = "Sorted Utility Evaluations [{0:.0f}:{1:.2f}, {2:.0f}:{3:.2f}, {4:.0f}:{5:.2f}, {6:.0f}:{7:.2f}, {8:.0f}:{9:.2f}, {10:.0f}:{11:.2f}, {12:.0f}:{13:.2f}, {14:.0f}:{15:.2f}]"
        txt2 = "Indexed Utility Evaluations [{0:.0f}:{1:.2f}, {2:.0f}:{3:.2f}, {4:.0f}:{5:.2f}, {6:.0f}:{7:.2f}, {8:.0f}:{9:.2f}, {10:.0f}:{11:.2f}, {12:.0f}:{13:.2f}, {14:.0f}:{15:.2f}]"
        PyImGui.text(txt.format(ordered_skills[0][0]+1, ordered_skills[0][1], ordered_skills[1][0]+1, ordered_skills[1][1], ordered_skills[2][0]+1, ordered_skills[2][1], ordered_skills[3][0]+1, ordered_skills[3][1], ordered_skills[4][0]+1, ordered_skills[4][1], ordered_skills[5][0]+1, ordered_skills[5][1], ordered_skills[6][0]+1, ordered_skills[6][1], ordered_skills[7][0]+1, ordered_skills[7][1]))
        ordered_skills = combat_handler.GetUnorderedSkillUtility()
        if ordered_skills is not None:
            PyImGui.text(txt2.format(ordered_skills[0][0]+1, ordered_skills[0][1], ordered_skills[1][0]+1, ordered_skills[1][1], ordered_skills[2][0]+1, ordered_skills[2][1], ordered_skills[3][0]+1, ordered_skills[3][1], ordered_skills[4][0]+1, ordered_skills[4][1], ordered_skills[5][0]+1, ordered_skills[5][1], ordered_skills[6][0]+1, ordered_skills[6][1], ordered_skills[7][0]+1, ordered_skills[7][1]))
    if PyImGui.begin_tab_bar("OrderedSkills"):
        skills = combat_handler.GetSkills()
        for i in range(len(skills)):
            slot = i
            skill = skills[i]
            if PyImGui.begin_tab_item(Skill.GetName(skill.skill_id)):
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

                    is_skill_ready = combat_handler.IsSkillReady(slot)
                    is_ooc_skill = combat_handler.IsOOCSkill(slot)
                    is_ready_to_cast, v_target = combat_handler.IsReadyToCast(skill_slot)

                    self_id = Player.GetAgentID()
                    nearest_enemy = TargetNearestEnemy()
                    nearest_ally = TargetLowestAlly()
                    nearest_npc = TargetNearestNpc()
                    nearest_item = TargetNearestItem()
                    nearest_spirit = TargetNearestSpirit()
                    nearest_minion = TargetLowestMinion()
                    nearest_corpse = TargetNearestCorpse()
                    pet_id = TargetPet(self_id)

                    headers = ["Self", "Nearest Enemy", "Nearest Ally", "Nearest NPC", "Nearest Item", "Nearest Spirit", "Nearest Minion", "Nearest Corpse", "Pet"]

                    data = [
                        (self_id, nearest_enemy, nearest_ally, nearest_npc, nearest_item,
                         nearest_spirit, nearest_minion, nearest_corpse, pet_id)
                    ]

                    ImGui.table("Target Debug Table", headers, data)

                    PyImGui.text(f"Target to Cast: {v_target}")

                    PyImGui.separator()

                    PyImGui.text_colored(f"IsSkillReady: {is_skill_ready}",TrueFalseColor(is_skill_ready))

                    PyImGui.text_colored(f"IsReadyToCast: {is_ready_to_cast}", TrueFalseColor(is_ready_to_cast))
                    if PyImGui.tree_node(f"IsReadyToCast: {is_ready_to_cast}"):
                        is_casting = Agent.IsCasting(Player.GetAgentID())
                        casting_skill = Agent.GetCastingSkill(Player.GetAgentID())
                        skillbar_casting = SkillBar.GetCasting()
                        skillbar_recharge = combat_handler.skills[skill_slot].skillbar_data.recharge
                        current_energy = Agent.GetEnergy(Player.GetAgentID()) * Agent.GetMaxEnergy(Player.GetAgentID())
                        energy_cost = Skill.Data.GetEnergyCost(combat_handler.GetOrderedSkill(skill_slot).skill_id)
                        current_hp = Agent.GetHealth(Player.GetAgentID())
                        target_hp = combat_handler.GetOrderedSkill(skill_slot).custom_skill_data.Conditions.SacrificeHealth
                        health_cost = Skill.Data.GetHealthCost(combat_handler.GetOrderedSkill(skill_slot).skill_id)

                        adrenaline_required = Skill.Data.GetAdrenaline(combat_handler.GetOrderedSkill(skill_slot).skill_id)
                        adrenaline_a = combat_handler.GetOrderedSkill(skill_slot).skillbar_data.adrenaline_a

                        current_overcast = Agent.GetOvercast(Player.GetAgentID())
                        overcast_target = combat_handler.GetOrderedSkill(skill_slot).custom_skill_data.Conditions.Overcast
                        skill_overcast = Skill.Data.GetOvercast(combat_handler.GetOrderedSkill(skill_slot).skill_id)

                        are_cast_conditions_met = combat_handler.AreCastConditionsMet(skill_slot,v_target)
                        spirit_buff_exists = combat_handler.SpiritBuffExists(combat_handler.GetOrderedSkill(skill_slot).skill_id)
                        has_effect = combat_handler.HasEffect(v_target, combat_handler.GetOrderedSkill(skill_slot).skill_id)

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


HeroFlags: bool = [False, False, False, False, False, False, False, False, False]
AllFlag = False
CLearFlags = False
one_time_set_flag = False
def DrawFlags():
    global HeroAI_vars,capture_flag_all, capture_hero_flag, capture_hero_index, overlay
    global one_time_set_flag, CLearFlags

    if capture_hero_flag:
        x, y, _ = overlay.GetMouseWorldPos()
        if capture_flag_all:
            DrawFlagAll(x, y)
            pass
        else:
            DrawHeroFlag(x, y)
            
        if PyImGui.is_mouse_clicked(0) and one_time_set_flag:
            one_time_set_flag = False
            return

        if PyImGui.is_mouse_clicked(0) and not one_time_set_flag:
            if capture_hero_index > 0 and capture_hero_index <= Party.GetHeroCount():
                if not capture_flag_all:   
                    agent_id = Party.Heroes.GetHeroAgentIDByPartyPosition(capture_hero_index)
                    Party.Heroes.FlagHero(agent_id, x, y)
                    one_time_set_flag = True
            else:
                if capture_hero_index == 0:
                    hero_ai_index = 0
                    Party.Heroes.FlagAllHeroes(x, y)
                else:
                    hero_ai_index = capture_hero_index - Party.GetHeroCount()
                HeroAI_vars.shared_memory_handler.set_player_property(hero_ai_index, "IsFlagged", True)
                HeroAI_vars.shared_memory_handler.set_player_property(hero_ai_index, "FlagPosX", x)
                HeroAI_vars.shared_memory_handler.set_player_property(hero_ai_index, "FlagPosY", y)
                HeroAI_vars.shared_memory_handler.set_player_property(hero_ai_index, "FollowAngle", Agent.GetRotationAngle(Player.GetAgentID()))
                
                one_time_set_flag = True

            capture_flag_all = False
            capture_hero_flag = False
            one_time_set_flag = False
            capture_mouse_timer.Stop()

    #All flag is handled by the game even with no heroes
    if HeroAI_vars.all_player_struct[0].IsFlagged:
        DrawFlagAll(HeroAI_vars.all_player_struct[0].FlagPosX, HeroAI_vars.all_player_struct[0].FlagPosY)
        
    for i in range(1, MAX_NUM_PLAYERS):
        if HeroAI_vars.all_player_struct[i].IsFlagged and HeroAI_vars.all_player_struct[i].IsActive and not HeroAI_vars.all_player_struct[i].IsHero:
            DrawHeroFlag(HeroAI_vars.all_player_struct[i].FlagPosX,HeroAI_vars.all_player_struct[i].FlagPosY)

    if CLearFlags:
        for i in range(MAX_NUM_PLAYERS):
            HeroAI_vars.shared_memory_handler.set_player_property(i, "IsFlagged", False)
            HeroAI_vars.shared_memory_handler.set_player_property(i, "FlagPosX", 0.0)
            HeroAI_vars.shared_memory_handler.set_player_property(i, "FlagPosY", 0.0)
            HeroAI_vars.shared_memory_handler.set_player_property(i, "FollowAngle", 0.0)
            Party.Heroes.UnflagHero(i)
        Party.Heroes.UnflagAllHeroes()
        CLearFlags = False
            
        

def DrawFlaggingWindow():
    global HeroFlags, AllFlag, capture_flag_all, capture_hero_flag, capture_hero_index, one_time_set_flag
    global CLearFlags
    party_size = Party.GetPartySize()
    if party_size == 1:
        PyImGui.text("No Follower or Heroes to Flag.")
        return

    if PyImGui.begin_table("Flags",3):
        PyImGui.table_next_row()
        PyImGui.table_next_column()
        if party_size >= 2:
            HeroFlags[0] = ImGui.toggle_button("1", IsHeroFlagged(1), 30, 30)
        PyImGui.table_next_column()
        if party_size >= 3:
            HeroFlags[1] = ImGui.toggle_button("2", IsHeroFlagged(2),30,30)
        PyImGui.table_next_column()
        if party_size >= 4:
            HeroFlags[2] = ImGui.toggle_button("3", IsHeroFlagged(3),30,30)
        PyImGui.table_next_row()
        PyImGui.table_next_column()
        if party_size >= 5:
            HeroFlags[3] = ImGui.toggle_button("4", IsHeroFlagged(4),30,30)
        PyImGui.table_next_column()
        AllFlag = ImGui.toggle_button("All", IsHeroFlagged(0), 30, 30)
        PyImGui.table_next_column()
        if party_size >= 6:
            HeroFlags[4] = ImGui.toggle_button("5", IsHeroFlagged(5),30,30)
        PyImGui.table_next_row()
        PyImGui.table_next_column()
        if party_size >= 7:
            HeroFlags[5] = ImGui.toggle_button("6", IsHeroFlagged(6),30,30)
        PyImGui.table_next_column()
        if party_size >= 8:
            HeroFlags[6] = ImGui.toggle_button("7", IsHeroFlagged(7), 30, 30)
        PyImGui.table_next_column()
        CLearFlags = ImGui.toggle_button("X", HeroFlags[7],30,30)
        PyImGui.end_table()

    if AllFlag != IsHeroFlagged(0):
        capture_hero_flag = True
        capture_flag_all = True
        capture_hero_index = 0
        one_time_set_flag = False
        capture_mouse_timer.Start()

    for i in range(1, party_size):
        if HeroFlags[i-1] != IsHeroFlagged(i):
            capture_hero_flag = True
            capture_flag_all = False
            capture_hero_index = i
            one_time_set_flag = False
            capture_mouse_timer.Start()
        

def DrawCandidateWindow():
    global HeroAI_vars, HeroAI_windows
    global party_config_first_run

    candidate_count = 0

    table_flags = PyImGui.TableFlags.Sortable | PyImGui.TableFlags.Borders | PyImGui.TableFlags.RowBg
    if PyImGui.begin_table("CandidateTable", 2, table_flags):
        # Setup columns
        PyImGui.table_setup_column("Invite", PyImGui.TableColumnFlags.NoSort)
        PyImGui.table_setup_column("Candidate", PyImGui.TableColumnFlags.NoFlag)
        PyImGui.table_headers_row()

        sort_specs = PyImGui.table_get_sort_specs()

        column_index = 1  # Default to Candidate column
        sort_direction = 1  # Default to Ascending

        if sort_specs and sort_specs.SpecsCount > 0:
            spec = sort_specs.Specs
            column_index = spec.ColumnIndex
            sort_direction = spec.SortDirection

        sorted_candidates = HeroAI_vars.all_candidate_struct[:]
        if column_index == 1:  # Sort by Candidate Name
            sorted_candidates.sort(
                key=lambda x: Agent.GetName(x.PlayerID),
                reverse=(sort_direction == 2)  # 2 = Descending
            )

        for index in range(MAX_NUM_PLAYERS):
            candidate = HeroAI_vars.all_candidate_struct[index]
            if (candidate.PlayerID and
                candidate.PlayerID != Player.GetAgentID() and
                candidate.MapID == Map.GetMapID() and
                candidate.MapRegion == Map.GetRegion()[0] and
                candidate.MapDistrict == Map.GetDistrict()):

                candidate_count += 1

                PyImGui.table_next_row()

                PyImGui.table_set_column_index(0)
                if PyImGui.button(f"Invite##invite_{candidate.PlayerID}"):
                    SendPartyCommand(index, "Invite")

                PyImGui.table_set_column_index(1)
                PyImGui.text(Agent.GetName(candidate.PlayerID))     

        PyImGui.end_table()

        if candidate_count == 0:
            PyImGui.text("No candidates found.")

    PyImGui.separator()

    for index in range(MAX_NUM_PLAYERS):
        candidate = HeroAI_vars.all_candidate_struct[index]
        if ((candidate.PlayerID and candidate.PlayerID != Player.GetAgentID()) and
            (candidate.MapID != Map.GetMapID() or
            candidate.MapRegion != Map.GetRegion()[0] or
            candidate.MapDistrict != Map.GetDistrict())):

            if PyImGui.button(f"Summon from map {Map.GetMapName(candidate.MapID)}##summon_{candidate.PlayerID}"):
                SendPartyCommand(index, "Summon")  


def DrawCandidatesDebug():
    global MAX_NUM_PLAYERS, Debug_window_vars

    candidate_count = 0     
    headers = ["Slot","MapID", "MapRegion", "MapDistrict","PlayerID", "InvitedBy", "SummonedBy", "LastUpdated"]

    data = []
    for i in range(MAX_NUM_PLAYERS):
        candidate = HeroAI_vars.all_candidate_struct[i]
        data.append((
            i,  # Slot index
            candidate.MapID,
            candidate.MapRegion,
            candidate.MapDistrict,
            candidate.PlayerID,
            candidate.InvitedBy,
            candidate.SummonedBy,
            candidate.LastUpdated
        ))

    ImGui.table("Candidate Debug Table", headers, data)

slot_to_write = 0
def DrawPlayersDebug():
    global MAX_NUM_PLAYERS, Debug_window_vars   , slot_to_write, HeroAI_vars

    own_party_number = Party.GetOwnPartyNumber()
    PyImGui.text(f"Own Party Number: {own_party_number}")
    slot_to_write = PyImGui.input_int("Slot to write", slot_to_write)

    if PyImGui.button("Submit"):
        self_id = Player.GetAgentID()

        HeroAI_vars.shared_memory_handler.set_player_property(slot_to_write, "PlayerID", self_id)
        HeroAI_vars.shared_memory_handler.set_player_property(slot_to_write, "Energy_Regen", Agent.GetEnergyRegen(self_id))
        HeroAI_vars.shared_memory_handler.set_player_property(slot_to_write, "Energy", Agent.GetEnergy(self_id))
        HeroAI_vars.shared_memory_handler.set_player_property(slot_to_write, "IsActive", True)
        HeroAI_vars.shared_memory_handler.set_player_property(slot_to_write, "IsHero", False)
        HeroAI_vars.shared_memory_handler.set_player_property(slot_to_write, "IsFlagged", False)
        HeroAI_vars.shared_memory_handler.set_player_property(slot_to_write, "FlagPosX", 0.0)
        HeroAI_vars.shared_memory_handler.set_player_property(slot_to_write, "FlagPosY", 0.0)


    headers = ["Slot","PlayerID", "EnergyRegen", "Energy","IsActive", "IsHero", "IsFlagged", "FlagPosX", "FlagPosY", "LastUpdated"]

    data = []
    for i in range(MAX_NUM_PLAYERS):
        player = HeroAI_vars.all_player_struct[i]
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


def DrawHeroesDebug(): 
    global MAX_NUM_PLAYERS, Debug_window_vars
    headers = ["Slot", "agent_id", "owner_player_id", "hero_id", "hero_name"]
    data = []

    heroes = Party.GetHeroes() 
    for index, hero in enumerate(heroes):
        data.append((
            index,  # Slot index
            hero.agent_id,
            hero.owner_player_id,
            hero.hero_id.GetID(),
            hero.hero_id.GetName(),
        ))
    ImGui.table("Heroes Debug Table", headers, data)


def DrawGameOptionsDebug():
    global MAX_NUM_PLAYERS, HeroAI_vars

    data = []
    PyImGui.text("Remote Control Variables")
    headers = ["Control", "Following", "Avoidance", "Looting", "Targetting", "Combat"]
    headers += [f"Skill {j + 1}" for j in range(NUMBER_OF_SKILLS)]
    row = [
        "Remote",  
        HeroAI_vars.global_control_game_struct.Following,
        HeroAI_vars.global_control_game_struct.Avoidance,
        HeroAI_vars.global_control_game_struct.Looting,
        HeroAI_vars.global_control_game_struct.Targetting,
        HeroAI_vars.global_control_game_struct.Combat,
        HeroAI_vars.global_control_game_struct.WindowVisible
    ]

    row += [
        HeroAI_vars.global_control_game_struct.Skills[j].Active for j in range(NUMBER_OF_SKILLS)
    ]
    data.append(tuple(row))
    ImGui.table("Control Debug Table", headers, data)

    headers = ["Slot", "Following", "Avoidance", "Looting", "Targetting", "Combat", "WindowVisible"]
    headers += [f"Skill {j + 1}" for j in range(NUMBER_OF_SKILLS)] 

    data = []
    for i in range(MAX_NUM_PLAYERS):
        row = [
            i,  
            HeroAI_vars.all_game_option_struct[i].Following,
            HeroAI_vars.all_game_option_struct[i].Avoidance,
            HeroAI_vars.all_game_option_struct[i].Looting,
            HeroAI_vars.all_game_option_struct[i].Targetting,
            HeroAI_vars.all_game_option_struct[i].Combat,
            HeroAI_vars.all_game_option_struct[i].WindowVisible
        ]

        row += [
            HeroAI_vars.all_game_option_struct[i].Skills[j].Active for j in range(NUMBER_OF_SKILLS)
        ]

        data.append(tuple(row))

    ImGui.table("Game Options Debug Table", headers, data)

draw_fake_flag = True
def DrawFlagDebug():
    global capture_flag_all, capture_hero_flag,draw_fake_flag, overlay
    PyImGui.text("Flag Debug")
    PyImGui.text(f"capture_flag_all: {capture_flag_all}")
    PyImGui.text(f"capture_hero_flag: {capture_hero_flag}")
    if PyImGui.button("Toggle Flags"):
        capture_flag_all = not capture_flag_all
        capture_hero_flag = not capture_hero_flag

    PyImGui.separator()

    x, y, z = overlay.GetMouseWorldPos()

    PyImGui.text(f"Mouse Position: {x:.2f}, {y:.2f}, {z:.2f}")
    PyImGui.text_colored("Having GetMouseWorldPos active will crash your client on map change",(1, 0.5, 0.05, 1))
    mouse_x, mouse_y = overlay.GetMouseCoords()
    PyImGui.text(f"Mouse Coords: {mouse_x}, {mouse_y}")
    PyImGui.text(f"Player Position: {Agent.GetXYZ(Player.GetAgentID())}")
    draw_fake_flag = PyImGui.checkbox("Draw Fake Flag", draw_fake_flag)

    if draw_fake_flag:
        DrawFlagAll(x, y)

    PyImGui.separator()

    PyImGui.text(f"AllFlag: {AllFlag}")
    PyImGui.text(f"capture_hero_index: {capture_hero_index}")

    for i in range(MAX_NUM_PLAYERS):
        if HeroFlags[i]:
            PyImGui.text(f"Hero {i + 1} is flagged")

def DrawFollowDebug(combat_handler: CombatClass):
    global show_area_rings, show_hero_follow_grid, show_distance_on_followers, overlay
    global Angle_changed


    if PyImGui.button("reset overlay"):
        overlay.RefreshDrawList()
    show_area_rings = PyImGui.checkbox("Show Area Rings", show_area_rings)
    show_hero_follow_grid = PyImGui.checkbox("Show Hero Follow Grid", show_hero_follow_grid)
    show_distance_on_followers = PyImGui.checkbox("Show Distance on Followers", show_distance_on_followers)
    PyImGui.separator()
    PyImGui.text(f"InAggro: {InAggro()}")
    PyImGui.text(f"IsMelee: {Agent.IsMelee(Player.GetAgentID())}")
    PyImGui.text(f"Nearest Enemy: {TargetNearestEnemy()}")
    PyImGui.text(f"stay_alert_timer: {combat_handler.GetStayAlertTimer()}")
    PyImGui.text(f"Leader Rotation Angle: {Agent.GetRotationAngle(Party.GetPartyLeaderID())}")
    PyImGui.text(f"Angle_changed: {Angle_changed}")

    segments = 32
    overlay.BeginDraw()
    if show_area_rings:
        player_x, player_y, player_z = Agent.GetXYZ(Player.GetAgentID())

        overlay.DrawPoly3D(player_x, player_y, player_z, radius=Range.Touch.value / 2, color=RGBToColor(255, 255, 0 , 128),numsegments=segments,thickness=2.0)
        overlay.DrawPoly3D(player_x, player_y, player_z, radius=Range.Touch.value    , color=RGBToColor(255, 200, 0 , 128),numsegments=segments,thickness=2.0)
        overlay.DrawPoly3D(player_x, player_y, player_z, radius=Range.Adjacent.value , color=RGBToColor(255, 150, 0 , 128), numsegments=segments, thickness=2.0)
        overlay.DrawPoly3D(player_x, player_y, player_z, radius=Range.Nearby.value   , color=RGBToColor(255, 100, 0 , 128), numsegments=segments, thickness=2.0)
        overlay.DrawPoly3D(player_x, player_y, player_z, radius=Range.Area.value     , color=RGBToColor(255, 50 , 0 , 128), numsegments=segments, thickness=2.0)
        overlay.DrawPoly3D(player_x, player_y, player_z, radius=Range.Earshot.value  , color=RGBToColor(255, 25 , 0 , 128), numsegments=segments, thickness=2.0)
        overlay.DrawPoly3D(player_x, player_y, player_z, radius=Range.Spellcast.value, color=RGBToColor(255, 12 , 0 , 128), numsegments=segments, thickness=2.0)

    if show_hero_follow_grid:
        leader_x, leader_y, leader_z = Agent.GetXYZ(Party.GetPartyLeaderID())

        for index, angle in enumerate(hero_formation):
            if index == 0:
                continue
            angle_on_hero_grid = Agent.GetRotationAngle(Party.GetPartyLeaderID()) + DegToRad(angle)
            hero_x = Range.Touch.value * math.cos(angle_on_hero_grid) + leader_x
            hero_y = Range.Touch.value * math.sin(angle_on_hero_grid) + leader_y
            
            overlay.DrawPoly3D(hero_x, hero_y, leader_z, radius=Range.Touch.value /2, color=RGBToColor(255, 0, 255, 128), numsegments=segments, thickness=2.0)
 
    if show_distance_on_followers:
        for i in range(MAX_NUM_PLAYERS):
            if HeroAI_vars.all_player_struct[i].IsActive:
                overlay.BeginDraw()
                player_id = HeroAI_vars.all_player_struct[i].PlayerID
                if player_id == Player.GetAgentID():
                    continue
                target_x, target_y, target_z = Agent.GetXYZ(player_id)
                overlay.DrawPoly3D(target_x, target_y, target_z, radius=72, color=RGBToColor(255, 255, 255, 128),numsegments=segments,thickness=2.0)
                z_coord = overlay.FindZ(target_x, target_y, 0)
                overlay.DrawText3D(target_x, target_y, z_coord-130, f"{DistanceFromWaypoint(target_x, target_y):.1f}",color=RGBToColor(255, 255, 255, 128), autoZ=False, centered=True, scale=2.0)
    
    overlay.EndDraw()
    



def DrawDebugWindow(combat_handler: CombatClass):
    global MAX_NUM_PLAYERS, HeroAI_vars, Debug_window_vars

    if PyImGui.collapsing_header("Candidates Debug"):
        DrawCandidatesDebug()
    if PyImGui.collapsing_header("Players Debug"):
        DrawPlayersDebug()
    if PyImGui.collapsing_header("Game Options Debug"):
        DrawGameOptionsDebug()

    if PyImGui.collapsing_header("Heroes Debug"):
        DrawHeroesDebug()

    if Map.IsExplorable():
        if PyImGui.collapsing_header("Follow Debug"):
            DrawFollowDebug()
        if PyImGui.collapsing_header("Flag Debug"):
            DrawFlagDebug()
        if PyImGui.collapsing_header("Prioritized Skills"):
            DrawPrioritizedSkills(combat_handler)
        if PyImGui.collapsing_header("Buff Debug"):
            DrawBuffWindow()



def DrawMultiboxTools(combat_handler: CombatClass):
    global MAX_NUM_PLAYERS, HeroAI_vars, HeroAI_windows

    HeroAI_windows.tools_window.initialize()

    if HeroAI_windows.tools_window.begin():
        if Map.IsOutpost() and Player.GetAgentID() == Party.GetPartyLeaderID():
            if PyImGui.collapsing_header("Party Setup",PyImGui.TreeNodeFlags.DefaultOpen):
                DrawCandidateWindow()
        if Map.IsExplorable() and Player.GetAgentID() == Party.GetPartyLeaderID():
            if PyImGui.collapsing_header("Flagging"):
                DrawFlaggingWindow()
        if PyImGui.collapsing_header("Debug Options"):
            DrawDebugWindow(combat_handler)

    
    HeroAI_windows.tools_window.process_window()
    HeroAI_windows.tools_window.end()


def CompareAndSubmitGameOptions(game_option: GameOptionStruct):
    global HeroAI_vars

    # Core Options
    if game_option.Following != HeroAI_vars.global_control_game_struct.Following:
        HeroAI_vars.global_control_game_struct.Following = game_option.Following
        for i in range(MAX_NUM_PLAYERS):
            HeroAI_vars.shared_memory_handler.set_game_option_property(i, "Following", game_option.Following)

    if game_option.Avoidance != HeroAI_vars.global_control_game_struct.Avoidance:
        HeroAI_vars.global_control_game_struct.Avoidance = game_option.Avoidance
        for i in range(MAX_NUM_PLAYERS):
            HeroAI_vars.shared_memory_handler.set_game_option_property(i, "Avoidance", game_option.Avoidance)

    if game_option.Looting != HeroAI_vars.global_control_game_struct.Looting:
        HeroAI_vars.global_control_game_struct.Looting = game_option.Looting
        for i in range(MAX_NUM_PLAYERS):
            HeroAI_vars.shared_memory_handler.set_game_option_property(i, "Looting", game_option.Looting)

    if game_option.Targetting != HeroAI_vars.global_control_game_struct.Targetting:
        HeroAI_vars.global_control_game_struct.Targetting = game_option.Targetting
        for i in range(MAX_NUM_PLAYERS):
            HeroAI_vars.shared_memory_handler.set_game_option_property(i, "Targetting", game_option.Targetting)

    if game_option.Combat != HeroAI_vars.global_control_game_struct.Combat:
        HeroAI_vars.global_control_game_struct.Combat = game_option.Combat
        for i in range(MAX_NUM_PLAYERS):
            HeroAI_vars.shared_memory_handler.set_game_option_property(i, "Combat", game_option.Combat)

    # Skills
    for skill_index in range(NUMBER_OF_SKILLS):
        if game_option.Skills[skill_index].Active != HeroAI_vars.global_control_game_struct.Skills[skill_index].Active:
            HeroAI_vars.global_control_game_struct.Skills[skill_index].Active = game_option.Skills[skill_index].Active
            for i in range(MAX_NUM_PLAYERS):
                HeroAI_vars.shared_memory_handler.set_game_option_property(
                    i, f"Skill_{skill_index + 1}", game_option.Skills[skill_index].Active
                )


def SubmitGameOptions(index,game_option,original_game_option):
    # Core Options
    if game_option.Following != original_game_option.Following:
        HeroAI_vars.shared_memory_handler.set_game_option_property(index, "Following", game_option.Following)

    if game_option.Avoidance != original_game_option.Avoidance:
        HeroAI_vars.shared_memory_handler.set_game_option_property(index, "Avoidance", game_option.Avoidance)

    if game_option.Looting != original_game_option.Looting:
        HeroAI_vars.shared_memory_handler.set_game_option_property(index, "Looting", game_option.Looting)

    if game_option.Targetting != original_game_option.Targetting:
        HeroAI_vars.shared_memory_handler.set_game_option_property(index, "Targetting", game_option.Targetting)

    if game_option.Combat != original_game_option.Combat:
        HeroAI_vars.shared_memory_handler.set_game_option_property(index, "Combat", game_option.Combat)

    # Skills
    for i in range(NUMBER_OF_SKILLS):
        if game_option.Skills[i].Active != original_game_option.Skills[i].Active:
            HeroAI_vars.shared_memory_handler.set_game_option_property(index, f"Skill_{i + 1}", game_option.Skills[i].Active)

def DrawPanelButtons(source_game_option):
    global HeroAI_vars
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
        game_option.Targetting = ImGui.toggle_button(IconsFontAwesome5.ICON_BULLSEYE + "##Targetting", source_game_option.Targetting,40,40)
        ImGui.show_tooltip("Targetting")
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

def DrawMainWindow():
    global HeroAI_vars, HeroAI_windows

    own_party_number = Party.GetOwnPartyNumber()

    game_option = GameOptionStruct()
    original_game_option = HeroAI_vars.all_game_option_struct[own_party_number]
        
    if not original_game_option.WindowVisible:
        return

    if own_party_number == 0:
        return

    HeroAI_windows.main_window.initialize()
    if HeroAI_windows.main_window.begin():
        game_option = DrawPanelButtons(original_game_option) 
        SubmitGameOptions(own_party_number,game_option,original_game_option)

        HeroAI_windows.main_window.process_window()
        HeroAI_windows.main_window.end()


def DrawControlPanelWindow():
    global HeroAI_vars, HeroAI_windows

    own_party_number = Party.GetOwnPartyNumber()
    game_option = GameOptionStruct()     
    if own_party_number != 0:
        return

    HeroAI_windows.control_window.initialize()
    if HeroAI_windows.control_window.begin():   
        game_option = DrawPanelButtons(HeroAI_vars.global_control_game_struct) 
        CompareAndSubmitGameOptions(game_option)

        if PyImGui.collapsing_header("Player Control"):
            for index in range(MAX_NUM_PLAYERS):
                if HeroAI_vars.all_player_struct[index].IsActive and not HeroAI_vars.all_player_struct[index].IsHero:
                    original_game_option = HeroAI_vars.all_game_option_struct[index]
                    player_name = Agent.GetName(HeroAI_vars.all_player_struct[index].PlayerID)
                    if PyImGui.tree_node(f"{player_name}##ControlPlayer{index}"):
                        game_option = DrawPanelButtons(original_game_option)
                        SubmitGameOptions(index, game_option, original_game_option)
                        PyImGui.tree_pop()

        HeroAI_windows.control_window.process_window()
    HeroAI_windows.control_window.end()
   

