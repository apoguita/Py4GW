import os
import traceback

import Py4GW  # type: ignore
from HeroAI.cache_data import CacheData
from Py4GWCoreLib import IniHandler
from Py4GWCoreLib import PyImGui
from Py4GWCoreLib import Routines
from Py4GWCoreLib import Timer
import Py4GWCoreLib as GW
import time

"""Module by Dharmanatrix for autocasting spells for ease of play."""

script_directory = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(script_directory, os.pardir))

first_run = True

BASE_DIR = os.path.join(project_root, "Widgets/Config")
INI_WIDGET_WINDOW_PATH = os.path.join(BASE_DIR, "ezcast_settings.ini")
os.makedirs(BASE_DIR, exist_ok=True)

cached_data = CacheData()

# ——— Window Persistence Setup ———
ini_window = IniHandler(INI_WIDGET_WINDOW_PATH)
save_window_timer = Timer()
save_window_timer.Start()

# String consts
MODULE_NAME = "EZ Cast"  # Change this Module name
COLLAPSED = "collapsed"
X_POS = "x"
Y_POS = "y"

# load last‐saved window state (fallback to 100,100 / un-collapsed)
window_x = ini_window.read_int(MODULE_NAME, X_POS, 100)
window_y = ini_window.read_int(MODULE_NAME, Y_POS, 100)
window_collapsed = ini_window.read_bool(MODULE_NAME, COLLAPSED, False)

class Cache():
    def __init__(self):
        self.busy_timer = 0
        self.previous_time = 0
        self.ping_buffer = 0.05 #delay added after a cast should complete to avoid actions queueing when not ready
        self.ezcast_cast_minimum_timer = 0.1 #minimum delay between cast attempts, used for instant speed skills
        self.dev_mode = False
        #Generic
        self.generic_skill_use_checkbox = False
        self.reset_generic_skill_on_mapload = False
        self.generic_energy_buffer = 5
        self.drop_skill = [False] * 8
        self.maintain_skill = [False] * 8
        self.spam_skill = [False] * 8
        self.combat_skill = [False] * 8
        self.combat_ranges = [144, 166, 240, 322, 1000, 1248, 1498, 2000]
        self.combat_range_index = 0
        self.combat_range_names = ["Melee", "Adjacent", "Nearby", "Area", "Earshot", "Cast", "Longbow", "Prep"]
        self.combat_ranges_checkboxes = [False] * len(self.combat_ranges)
        self.combat_range_slider = 1000
        self.skill_array = [self.drop_skill, self.maintain_skill, self.spam_skill, self.combat_skill]

        self.generic_skill_use_buffer = 0.25
        self.combat = False
        #Refrainer
        self.refrainer_use_checkbox = False
        self.refrain_buffer = 1.25
        self.refrain_delay = 0.2
        #Aota
        self.aota_checkbox = False
        self.aota_threshold = 20
        #Quick attack
        self.qa_checkbox = False
        self.qa_attack_time = 1
        self.qa_percent_cancel = 0.5
        self.qa_attack_detect = False
cache = Cache()

def DrawGenericSkills():
    generic_skill_collapse = PyImGui.collapsing_header("GenericSkillUse", 4)
    PyImGui.same_line(PyImGui.get_content_region_avail()[0] - 20, -1)
    cache.generic_skill_use_checkbox = PyImGui.checkbox("##GenericSkillUseCheckbox", cache.generic_skill_use_checkbox)
    if PyImGui.is_item_hovered():
        PyImGui.set_tooltip("Disable" if cache.generic_skill_use_checkbox else "Enable")

    if generic_skill_collapse:
        cache.reset_generic_skill_on_mapload = PyImGui.checkbox("Reset on map load",
                                                                cache.reset_generic_skill_on_mapload)
        PyImGui.push_item_width(PyImGui.get_window_width() / 6)
        cache.generic_energy_buffer = PyImGui.slider_int("##genericenergybuffer", cache.generic_energy_buffer, 0, 50)
        PyImGui.pop_item_width()
        PyImGui.same_line(0, -1)
        PyImGui.text("Minimum energy left after a skill is used")

        box_spacing = 6
        PyImGui.push_style_color(PyImGui.ImGuiCol.CheckMark, (1, 1, 0.2, 1))
        for n in range(0, 4):
            hovertip = "Nulltip"
            label_text = "NullLabel"
            match n:
                case 0:
                    label_text = " Drop Skills"
                    hovertip = "Use these skills immediately after their effect ends"
                case 1:
                    label_text = " Maintain Skills"
                    hovertip = "Attempt to maintain these skills without allowing the effect to end"
                case 2:
                    label_text = " Spam Skills"
                    hovertip = "Use these skills whenever possible"
                case 3:
                    label_text = " Combat Toggle"
                    hovertip = "The skill use options will only trigger when near foes"

            for i in range(0, 8):
                curser_pos = PyImGui.get_cursor_pos()
                color_flip = False
                if cache.skill_array[n][i]:
                    color_flip = True
                    PyImGui.push_style_color(PyImGui.ImGuiCol.FrameBg, (0.1, 0.1, 0.8, 0.8))
                cache.skill_array[n][i] = PyImGui.checkbox(f"##genericskillusebox{n}_{i}", cache.skill_array[n][i])
                if color_flip:
                    PyImGui.pop_style_color(1)
                PyImGui.set_cursor_pos(curser_pos[0], curser_pos[1])
                PyImGui.text(f" {i + 1} ")
                PyImGui.same_line(0, -1)
            else:
                PyImGui.text(label_text)
                if PyImGui.is_item_hovered():
                    PyImGui.set_tooltip(hovertip)
            PyImGui.set_cursor_pos(PyImGui.get_cursor_pos_x(), PyImGui.get_cursor_pos_y() + box_spacing)
        PyImGui.pop_style_color(2)
        for i in range(0, len(cache.combat_ranges)):
            if cache.combat_range_slider < cache.combat_ranges[i]:
                cache.combat_ranges_checkboxes[i] = False
            elif cache.combat_range_slider >= cache.combat_ranges[i]:
                cache.combat_ranges_checkboxes[i] = True
            temp = cache.combat_ranges_checkboxes[i]
            cache.combat_ranges_checkboxes[i] = PyImGui.checkbox(f"##combatrange{i}", cache.combat_ranges_checkboxes[i])
            if temp != cache.combat_ranges_checkboxes[i]:
                if temp:  # Checkbox turned off
                    for j in range(i, len(cache.combat_ranges_checkboxes)):
                        cache.combat_ranges_checkboxes[j] = False
                    cache.combat_range_slider = cache.combat_ranges[i]
                    cache.combat_range_index = i
                else:  # checkbox turned on
                    for j in range(0, i):
                        cache.combat_ranges_checkboxes[j] = True
                    cache.combat_range_slider = cache.combat_ranges[i]
            PyImGui.same_line(0, -1)
            PyImGui.text(f"{cache.combat_range_names[i]}")
            if i != 3:
                PyImGui.same_line(0, -1)
        else:
            PyImGui.text("")
            PyImGui.text(" Combat Ranges")
            if PyImGui.is_item_hovered():
                PyImGui.set_tooltip("Dictates how close foes must be to trigger combat skills")
            PyImGui.same_line(0, -1)
            if cache.combat:
                PyImGui.push_style_color(PyImGui.ImGuiCol.SliderGrab, (
                1, 0.5, 0.5, 1))  # ImGui::PushStyleColor(ImGuiCol_Text, sf::Color(255, 255, 255, 255));)
            else :
                PyImGui.push_style_color(PyImGui.ImGuiCol.SliderGrab, (
                    0, 0.5, 0.5, 1))  # ImGui::PushStyleColor(ImGuiCol_Text, sf::Color(255, 255, 255, 255));)
            cache.combat_range_slider = PyImGui.slider_int("##combatsliderRange", cache.combat_range_slider, 0,
                                                           cache.combat_ranges[len(cache.combat_ranges) - 1])
            PyImGui.pop_style_color(1)

def DrawRefrainMaintainer():
    section_header = PyImGui.collapsing_header("Refrain Maintainer", 4)
    PyImGui.same_line(PyImGui.get_content_region_avail()[0] - 20, -1)
    cache.refrainer_use_checkbox = PyImGui.checkbox("##RefrainerCheckbox", cache.refrainer_use_checkbox)
    if PyImGui.is_item_hovered():
        PyImGui.set_tooltip("Disable" if cache.refrainer_use_checkbox else "Enable")

    if section_header:
        # PyImGui.set_next_item_width(PyImGui.get_content_region_avail()[0])
        PyImGui.text_wrapped("""This function will use "Help Me!" to maintain refrains intelligently. It will alternatively use "Dont Trip!" and "I am Unstoppable!" if both are present. If only "Don't Trip!" is available, it will require a recharge reduction such as an Essence of Celerity to work.""")
        PyImGui.slider_float("Grace buffer", cache.refrain_buffer, 0, 10)
        if PyImGui.is_item_hovered():
            PyImGui.set_tooltip("The time in seconds that a refrain should have remaining when the shout ends.\nValues lower than ping will result in dropped refrains.")

def DrawAuraOfTheAssassin():
    section_header = PyImGui.collapsing_header("Aura of the Assassin", 4)
    PyImGui.same_line(PyImGui.get_content_region_avail()[0] - 20, -1)
    cache.aota_checkbox = PyImGui.checkbox("##AotaCheckbox", cache.aota_checkbox)
    if PyImGui.is_item_hovered():
        PyImGui.set_tooltip("Disable" if cache.aota_checkbox else "Enable")

    if section_header:
        PyImGui.text("NOT COMPLETE: IN DEV") #todo get rid of this
        PyImGui.text_wrapped(
            """This function will use Assassin's Promise and "Finish Him!" at the set health threshold to instantly kill any target within earshot that drops to low enough health.""")
        PyImGui.slider_int("Health Percent", cache.aota_threshold, 0, 100)
        if PyImGui.is_item_hovered():
            PyImGui.set_tooltip(
                "The health percent that Aota will scan for enemies to reach before casting AP.")


def DrawQuickAttack():
    section_header = PyImGui.collapsing_header("Quick Attack", 4)
    PyImGui.same_line(PyImGui.get_content_region_avail()[0] - 20, -1)
    cache.qa_checkbox = PyImGui.checkbox("##QACheckbox", cache.qa_checkbox)
    if PyImGui.is_item_hovered():
        PyImGui.set_tooltip("Disable" if cache.qa_checkbox else "Enable")

    if section_header:
        PyImGui.text("NOT COMPLETE: IN DEV") #todo get rid of this
        PyImGui.text_wrapped(
            """This function will cancel attacks as soon as they complete the damage phase and queue follow up attack skills to increase effective attack speed.""")



def draw_widget(cached_data):
    global window_x, window_y, window_collapsed, first_run

    if first_run:
        PyImGui.set_next_window_pos(window_x, window_y)
        PyImGui.set_next_window_collapsed(window_collapsed, 0) #setting flag to 0 to avoid the resize grabber being disabled, bit power 1 (2) represents this flag
        first_run = False

    is_window_opened = PyImGui.begin(MODULE_NAME, 0)
    new_collapsed = PyImGui.is_window_collapsed()
    end_pos = PyImGui.get_window_pos()

    if is_window_opened:
        global cache

        # Styles for the Headers
        PyImGui.push_style_color(PyImGui.ImGuiCol.Header, (
        1, 0.1, 0.1, 0.5))  # ImGui::PushStyleColor(ImGuiCol_Header, sf::Color(0, 0, 0, 0));
        PyImGui.push_style_color(PyImGui.ImGuiCol.Border, (
        0.1, 0.1, 0.2, 1))  # ImGui::PushStyleColor(ImGuiCol_Border, sf::Color(255, 255, 255, 255));
        PyImGui.push_style_color(PyImGui.ImGuiCol.Text, (
        1, 1, 1, 1))  # ImGui::PushStyleColor(ImGuiCol_Text, sf::Color(255, 255, 255, 255));
        # ImGui::PushStyleVar(ImGuiStyleVar_FrameBorderSize, 1);
        DrawGenericSkills()
        DrawRefrainMaintainer()
        if cache.dev_mode:
            DrawAuraOfTheAssassin()
            DrawQuickAttack()
        PyImGui.pop_style_color(3)  # ImGui::PopStyleColor(3);
        # PyImGui.pop_style_var() # ImGui::PopStyleVar();

    PyImGui.end()
    if save_window_timer.HasElapsed(1000):
        # Position changed?
        if (end_pos[0], end_pos[1]) != (window_x, window_y):
            window_x, window_y = int(end_pos[0]), int(end_pos[1])
            ini_window.write_key(MODULE_NAME, X_POS, str(window_x))
            ini_window.write_key(MODULE_NAME, Y_POS, str(window_y))
        # Collapsed state changed?
        if new_collapsed != window_collapsed:
            window_collapsed = new_collapsed
            ini_window.write_key(MODULE_NAME, COLLAPSED, str(window_collapsed))
        save_window_timer.Reset()


def configure():
    pass

def UseGenericSkills(energy, player_id, player_ag : GW.PyAgent.PyAgent, now):
    global cache
    nearest_foe_id = GW.Routines.Agents.GetNearestEnemy()
    nearest_foe : GW.PyAgent.PyAgent = GW.Agent.GetAgentByID(nearest_foe_id)
    nearest_distance = 5000 * 5000
    square_dis = cache.combat_range_slider * cache.combat_range_slider
    if nearest_foe is not None:
        nearest_distance = (player_ag.x - nearest_foe.x) ** 2 + (player_ag.y - nearest_foe.y) ** 2
    cache.combat = (nearest_distance < square_dis)
    # GW.Console.Log("",f"{cache.combat} cache result")
    for n in range(0,3):
        for i in range(1,9):
            if not cache.skill_array[n][i - 1]: continue
            if cache.combat_skill[i - 1] and not cache.combat: continue
            if not GW.Routines.Checks.Skills.IsSkillSlotReady(i): continue
            skill_id = GW.SkillBar.GetSkillData(i).id.id
            skill_instance : GW.PySkill.Skill = GW.PySkill.Skill(skill_id)
            if GW.Skill.Data.GetEnergyCost(skill_id) + cache.generic_energy_buffer > energy: continue
            if skill_instance.adrenaline_a != skill_instance.adrenaline != 0: continue
            effect = GW.Effects.GetEffectTimeRemaining(player_id, skill_id)
            effect_valid = False
            if n == 0 and effect == 0: effect_valid = True
            if n == 1 and effect / 1000.0 < skill_instance.activation + cache.generic_skill_use_buffer: effect_valid = True
            if n == 2: effect_valid = True
            if effect_valid:
                cast_delay = skill_instance.activation + skill_instance.aftercast
                if cast_delay > 0:
                    cache.busy_timer = cast_delay + cache.ping_buffer
                else:
                    cache.busy_timer = cache.ezcast_cast_minimum_timer
                GW.SkillBar.UseSkill(i, GW.Player.GetTargetID())
                return True
    return False

def MaintainRefrains(player_id, player_ag : GW.PyAgent, now):
    effects = GW.Effects.GetEffects(player_id)
    effect : GW.PyEffects.EffectType
    rit_lord = next((effect for effect in effects if effect.skill_id == GW.Skill.GetID("Ritual_Lord")), None)

    global cache
    help_me_skill = GW.PySkill.Skill(GW.Skill.GetID("Help_Me"))
    heroic: GW.PyEffects.EffectType = None
    bladeturn: GW.PyEffects.EffectType = None
    aggressive: GW.PyEffects.EffectType = None
    burning: GW.PyEffects.EffectType = None
    hasty: GW.PyEffects.EffectType = None
    mending: GW.PyEffects.EffectType = None
    help_me: GW.PyEffects.EffectType = None
    dont_trip: GW.PyEffects.EffectType = None
    iau: GW.PyEffects.EffectType = None
    for effect in effects:
        if effect.skill_id == GW.Skill.GetID("Heroic_Refrain"):
            heroic = effect
            continue
        if effect.skill_id == GW.Skill.GetID("Bladeturn_Refrain"):
            bladeturn = effect
            continue
        if effect.skill_id == GW.Skill.GetID("Aggressive_Refrain"):
            aggressive = effect
            continue
        if effect.skill_id == GW.Skill.GetID("Burning_Refrain"):
            burning = effect
            continue
        if effect.skill_id == GW.Skill.GetID("Hasty_Refrain"):
            hasty = effect
            continue
        if effect.skill_id == GW.Skill.GetID("Mending_Refrain"):
            mending = effect
            continue
        if effect.skill_id == help_me_skill.id.id:
            help_me = effect
            continue
        if effect.skill_id == GW.Skill.GetID("Dont_Trip"):
            dont_trip = effect
            continue
        if effect.skill_id == GW.Skill.GetID("I_Am_Unstoppable"):
            iau = effect
            continue
    refrains = [heroic, bladeturn, aggressive, burning, hasty, mending]
    refrains = [x for x in refrains if x is not None]
    help_me_slot = GW.SkillBar.GetSlotBySkillID(help_me_skill.id.id)
    n : GW.PyAgent.AttributeClass
    command : GW.PyAgent.AttributeClass = next((n for n in player_ag.attributes if n.attribute_id == GW.PyAgent.SafeAttribute.Command), None)
    if command is None:
        help_me_duration = help_me_skill.duration_0pts
    else:
        help_me_duration = help_me_skill.duration_0pts + ((help_me_skill.duration_15pts - help_me_skill.duration_0pts)/15) * command.level
    help_me_duration = round(help_me_duration)
    dont_trip_slot = GW.SkillBar.GetSlotBySkillID(GW.Skill.GetID("Dont_Trip"))
    iau_slot = GW.SkillBar.GetSlotBySkillID(GW.Skill.GetID("I_Am_Unstoppable"))
    deld : GW.PyPlayer.PyTitle = GW.Player.GetTitle(GW.TitleID.Deldrimor)
    dont_trip_dur = 0
    match deld.current_title_tier_index:
        case 0: dont_trip_dur = 3
        case 1: dont_trip_dur = 3
        case 2: dont_trip_dur = 4
        case 3: dont_trip_dur = 4
        case _: dont_trip_dur = 5
    norn : GW.PyPlayer.PyTitle = GW.Player.GetTitle(GW.TitleID.Norn)
    iau_dur = 0
    match norn.current_title_tier_index:
        case 0: iau_dur = 16
        case 1: iau_dur = 17
        case 2: iau_dur = 18
        case 3: iau_dur = 18
        case 4: iau_dur = 19
        case _: iau_dur = 20
    if len(refrains) < 1: return False
    lowest_dur :GW.PyEffects.EffectType = sorted(refrains, key= lambda effect: effect.time_remaining)[0]
    lowest_dur = lowest_dur.time_remaining / 1000
    base_durations = [effect.duration for effect in refrains]
    base_durations = sorted(base_durations)
    if help_me_slot != 0:
        if help_me is None and GW.Routines.Checks.Skills.IsSkillSlotReady(help_me_slot):
            if lowest_dur > help_me_duration > lowest_dur - cache.refrain_buffer:
                cache.busy_timer = cache.ezcast_cast_minimum_timer
                GW.SkillBar.UseSkill(help_me_slot, 0)
                return True
    if dont_trip_slot != 0:
        if dont_trip is None and GW.Routines.Checks.Skills.IsSkillSlotReady(dont_trip_slot):
            if lowest_dur > dont_trip_dur > lowest_dur - cache.refrain_buffer:
                cache.busy_timer = cache.ezcast_cast_minimum_timer
                GW.SkillBar.UseSkill(dont_trip_slot, 0)
                return True
        if iau_slot != 0:
            if iau is None and GW.Routines.Checks.Skills.IsSkillSlotReady(iau_slot):
                if dont_trip is not None and base_durations[0] + dont_trip.time_remaining/1000 > iau_dur > base_durations[0] + dont_trip.time_remaining/1000 - cache.refrain_buffer:
                    cache.busy_timer = cache.ezcast_cast_minimum_timer
                    GW.SkillBar.UseSkill(iau_slot, 0)
                    return True
    return False

def AuraOfTheAssassin(energy, player_id, player_ag : GW.PyAgent, now):
    foes = GW.Routines.Agents.GetFilteredEnemyArray(player_ag.x, player_ag.y, 1000)
    agent : GW.PyAgent.PyAgent
    found = False
    for agent in foes:
        if agent.living_agent.hp < cache.aota_threshold / 100.0:
            found = True
            break
    if found:
        ap_slot = GW.SkillBar.GetSlotBySkillID(GW.Skill.GetID("Assassins_Promise"))
        fh_slot = GW.SkillBar.GetSlotBySkillID(GW.Skill.GetID("Finish_Him"))
        if ap_slot != 0 and fh_slot != 0 and energy > 15:
            # GW.SkillBar.UseSkill(, agent.id)
            #TODO finish this
            GW.Console.Log("","Found a target to finish. This function is incomplete")
            cache.busy_timer = 1
            return True
    return False

def QuickAttack(energy, played_id, player_ag : GW.PyAgent, now, delta):
    global cache
    player : GW.PyAgent.PyLivingAgent = player_ag.living_agent
    if player.is_attacking:
        if not cache.qa_attack_detect:
            cache.qa_attack_detect = True
            cache.qa_attack_time = player.weapon_attack_speed * player.attack_speed_modifier * cache.qa_percent_cancel
        else:
            cache.qa_attack_time -= delta
            if cache.qa_attack_time < 0:
                cache.qa_attack_detect = False
                GW.Keystroke.PressAndRelease(27)
                GW.Keystroke.PressAndRelease(83)
                # GW.YieldRoutines.Keybinds.CancelAction()
                GW.Console.Log("",f"Tried to cancel {cache.qa_attack_time}")

def Update():
    global cache
    now = time.time()
    delta = now - cache.previous_time
    cache.previous_time = now
    cache.busy_timer -= delta
    if cache.busy_timer > 0:
        return
    player_id = GW.Player.GetAgentID()
    player_ag: GW.PyAgent = GW.Player.GetAgent()
    energy = GW.Agent.GetEnergy(player_id) * GW.Agent.GetMaxEnergy(player_id)
    if cache.generic_skill_use_checkbox:
        if UseGenericSkills(energy, player_id, player_ag, now): return
    # TODO autoritlord
    if cache.qa_checkbox:
        if QuickAttack(energy, player_id, player_ag, now, delta): return
    if cache.refrainer_use_checkbox:
        if MaintainRefrains(player_id, player_ag, now): return
    if cache.aota_checkbox:
        if AuraOfTheAssassin(energy, player_id, player_ag, now): return
    # TODO AutoFinishHim


def main():
    global cached_data
    try:
        if not Routines.Checks.Map.MapValid():
            return

        cached_data.Update()
        if Routines.Checks.Map.IsMapReady() and Routines.Checks.Party.IsPartyLoaded():
            draw_widget(cached_data)
            Update()

    except ImportError as e:
        Py4GW.Console.Log(MODULE_NAME, f"ImportError encountered: {str(e)}", Py4GW.Console.MessageType.Error)
        Py4GW.Console.Log(MODULE_NAME, f"Stack trace: {traceback.format_exc()}", Py4GW.Console.MessageType.Error)
    except ValueError as e:
        Py4GW.Console.Log(MODULE_NAME, f"ValueError encountered: {str(e)}", Py4GW.Console.MessageType.Error)
        Py4GW.Console.Log(MODULE_NAME, f"Stack trace: {traceback.format_exc()}", Py4GW.Console.MessageType.Error)
    except TypeError as e:
        Py4GW.Console.Log(MODULE_NAME, f"TypeError encountered: {str(e)}", Py4GW.Console.MessageType.Error)
        Py4GW.Console.Log(MODULE_NAME, f"Stack trace: {traceback.format_exc()}", Py4GW.Console.MessageType.Error)
    except Exception as e:
        # Catch-all for any other unexpected exceptions
        Py4GW.Console.Log(MODULE_NAME, f"Unexpected error encountered: {str(e)}", Py4GW.Console.MessageType.Error)
        Py4GW.Console.Log(MODULE_NAME, f"Stack trace: {traceback.format_exc()}", Py4GW.Console.MessageType.Error)
    finally:
        pass


if __name__ == "__main__":
    main()
