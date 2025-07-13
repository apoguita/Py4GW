import Py4GW
from Py4GWCoreLib import *
import webbrowser
from fractions import Fraction

MODULE_NAME = "tester for fonts"
TEXTURE_FOLDER = "Textures\\Game UI\\Skill Description\\"

import re
from typing import Any
def resolve_skill_description(skill_id: int, raw_desc: str, attribute_level: int = 0) -> str:
    """
    Replace all [! ... !] progression tags in a skill description using the correct progression values.
    If attribute_level is given, resolve using that rank.
    If not, resolve as a min–max range from level 0 to 15.
    """

    # Get all progression fields (now supports multiple)
    progressions = Skill.GetProgressionData(skill_id)
    if not progressions:
        return raw_desc

    # Wrap all progressions into known_fields format
    known_fields: list[dict[str, Any]] = [{
        "attribute": attr,
        "field": field_name,
        "values": values_dict
    } for attr, field_name, values_dict in progressions]

    def format_value(v: float) -> str:
        """Format numbers like 20.0 → 20, 17.50 → 17.5"""
        return f"{v:.2f}".rstrip('0').rstrip('.') if '.' in f"{v:.2f}" else str(int(v))

    def match_score(tag_values: list[float], values: dict[int, float]) -> float:
        """Compare tag values to progression data at levels 0, 12, 15"""
        v0 = values.get(0, 0.0)
        v12 = values.get(12, v0)
        v15 = values.get(15, v0)
        if len(tag_values) == 1:
            return abs(tag_values[0] - v15)
        elif len(tag_values) == 2:
            return abs(tag_values[0] - v0) + abs(tag_values[1] - v15)
        elif len(tag_values) == 3:
            return abs(tag_values[0] - v0) + abs(tag_values[1] - v12) + abs(tag_values[2] - v15)
        return float('inf')

    def find_best_field(tag_values: list[float]) -> dict[str, Any]:
        """Find the best matching field based on tag values"""
        best_field = known_fields[0]
        best_score = match_score(tag_values, best_field["values"])

        for field in known_fields[1:]:
            score = match_score(tag_values, field["values"])
            if score < best_score:
                best_score = score
                best_field = field

        return best_field

    def replace_tag(match: re.Match) -> str:
        tag_values = [float(g) for g in match.groups() if g is not None]

        best_field = find_best_field(tag_values)
        values = best_field["values"]

        if attribute_level and attribute_level > 0:
            level = max(0, min(attribute_level, max(values.keys())))
            resolved_value = values.get(level)
            if resolved_value is None:
                available_levels = sorted(k for k in values if k <= level)
                resolved_value = values[available_levels[-1]] if available_levels else 0.0
            return format_value(resolved_value)
        else:
            # If attribute_level is not set, preserve the tag range
            if len(tag_values) == 1:
                return format_value(tag_values[0])
            elif len(tag_values) == 2:
                return f"{format_value(tag_values[0])}...{format_value(tag_values[1])}"
            else:
                return f"{format_value(tag_values[0])}...{format_value(tag_values[1])}...{format_value(tag_values[2])}"


    # Regex pattern for [!x!], [!x...y!], [!x...y...z!]
    pattern = r'\[\!(\d+(?:\.\d+)?)(?:\.\.\.(\d+(?:\.\d+)?))?(?:\.\.\.(\d+(?:\.\d+)?))?\!\]'
    return re.sub(pattern, replace_tag, raw_desc)



selected_skill = 2235
compare_skills = False

table_start = (0.0, 0.0)
table_end = (0.0, 0.0)

hovered_skill = 0
askill_a = 0
askill_b = 0



def DrawSkillCard(skill_id:int):
    global table_start, table_end
    
    def is_mantained(skill_id):
        """
        Check if a skill is maintained.
        """
        is_enchantment = GLOBAL_CACHE.Skill.Flags.IsEnchantment(skill_id)
        if not is_enchantment:
            return False
        duration_0, duration_15 = GLOBAL_CACHE.Skill.Attribute.GetDuration(skill_id)
        return duration_0 > 10_000 and duration_15 > 10_000

    def is_sacrifice(skill_id):
        """
        Check if a skill is sacrificed.
        """
        health_cost = GLOBAL_CACHE.Skill.Data.GetHealthCost(skill_id)
        if health_cost > 0:
            return True
        return False

    def is_overcast(skill_id):
        """
        Check if a skill is overcast.
        """
        overcast = GLOBAL_CACHE.Skill.Data.GetOvercast(skill_id)
        return overcast > 0
        
    def is_adrenaline(skill_id):
        """
        Check if a skill uses adrenaline.
        """
        adrenaline = GLOBAL_CACHE.Skill.Data.GetAdrenaline(skill_id)
        return adrenaline > 0

    def is_energy(skill_id):
        """
        Check if a skill uses energy.
        """
        energy_cost = GLOBAL_CACHE.Skill.Data.GetEnergyCost(skill_id)
        return energy_cost > 0

    def is_activation_time(skill_id):
        """
        Check if a skill has an activation time.
        """
        activation = GLOBAL_CACHE.Skill.Data.GetActivation(skill_id)
        return activation > 0.0

    def is_recharge(skill_id):
        """
        Check if a skill has a recharge time.
        """
        recharge = GLOBAL_CACHE.Skill.Data.GetRecharge(skill_id)
        return recharge > 0

    def strip_skill_type(desc: str) -> str:
        if not desc:
            return ""
        parts = desc.split(".", 1)
        return parts[1].strip() if len(parts) > 1 else ""


    def GetProfessionColor(skill_id:int) -> Tuple[Color, Color]:
        profession = GLOBAL_CACHE.Skill.GetProfession(skill_id)[1]    
        color = ColorPalette.GetColor("Gray")         
        if profession == "Warrior":
            color = ColorPalette.GetColor("GW_Warrior")
        elif profession == "Ranger":
            color = ColorPalette.GetColor("GW_Ranger")
        elif profession == "Monk":
            color = ColorPalette.GetColor("GW_Monk")
        elif profession == "Necromancer":   
            color = ColorPalette.GetColor("GW_Necromancer")
        elif profession == "Mesmer":
            color = ColorPalette.GetColor("GW_Mesmer")
        elif profession == "Elementalist":
            color = ColorPalette.GetColor("GW_Elementalist")
        elif profession == "Assassin":  
            color = ColorPalette.GetColor("GW_Assassin")
        elif profession == "Ritualist":
            color = ColorPalette.GetColor("GW_Ritualist")
        elif profession == "Paragon":
            color = ColorPalette.GetColor("GW_Paragon")
        elif profession == "Dervish":
            color = ColorPalette.GetColor("GW_Dervish")
            
        faded_color = Color(color.r, color.g, color.b, 25)
        return color, faded_color

    def draw_background_frame():
        color, faded_color = GetProfessionColor(skill_id)
        #Draw Background Frame
        #Outline
        PyImGui.draw_list_add_rect(
                table_start[0]-2, table_start[1]-2,
                table_end[0]+2, table_end[1]+2,
                color.to_color(),  # Golden yellow outline
                0.0,  # Corner rounding
                PyImGui.DrawFlags._NoFlag,
                2.0   # Line thickness
            )
        #Background
        PyImGui.draw_list_add_rect_filled(
                table_start[0], table_start[1],
                table_end[0], table_end[1],
                faded_color.to_color(),
                0.0,
                PyImGui.DrawFlags._NoFlag
            )
    
    def IsElite(skill_id: int) -> bool:
        """
        Check if a skill is elite.
        """
        return GLOBAL_CACHE.Skill.Flags.IsElite(skill_id)
    
    def draw_title(skill_id: int):
        PyImGui.begin_group()
        ImGui.push_font("Bold", 22)
        if IsElite(skill_id):
            text_color = ColorPalette.GetColor("GW_Gold").to_tuple_normalized()
        else:
            text_color = ColorPalette.GetColor("GW_White").to_tuple_normalized()
            
        name_from_wiki = GLOBAL_CACHE.Skill.GetNameFromWiki(skill_id)
        PyImGui.text_colored(f"{name_from_wiki}", text_color)
        ImGui.pop_font()
        PyImGui.end_group()
        
        if PyImGui.is_item_hovered():
            if PyImGui.begin_tooltip():
                PyImGui.text(f"Name: {name_from_wiki}")
                PyImGui.text(f"Dictionary Name: {GLOBAL_CACHE.Skill.GetName(skill_id)}")
                PyImGui.end_tooltip()
    
    def draw_skill_icon(skill_id: int):
        # Texture column
        PyImGui.begin_group()
        texture_path = GLOBAL_CACHE.Skill.ExtraData.GetTexturePath(skill_id)
        ImGui.DrawTexture(texture_path, 96, 96)
        if IsElite(skill_id):
            text_color = ColorPalette.GetColor("GW_Gold").to_tuple_normalized()
            PyImGui.text_colored("Elite Skill", text_color)
        else:
            text_color = ColorPalette.GetColor("GW_White").to_tuple_normalized()
            
        attribute = GLOBAL_CACHE.Skill.Attribute.GetAttribute(skill_id)   
        att_desc = attribute.GetName() if attribute.GetName() != "Unknown" else "No Attribute"
        if GLOBAL_CACHE.Skill.Flags.IsPvE(skill_id):
            att_desc = "PvE"
        
        campaign = GLOBAL_CACHE.Skill.GetCampaign(skill_id)[1]
        PyImGui.text_wrapped(f"{att_desc}")
        PyImGui.text_wrapped(f"{campaign}")
        PyImGui.text(f"ID: {skill_id}")

        PyImGui.end_group()
        if PyImGui.is_item_hovered():
            if PyImGui.begin_tooltip():
                profession = GLOBAL_CACHE.Skill.GetProfession(skill_id)[1]
                PyImGui.text(f"ID: {skill_id}")
                PyImGui.text(f"Texture: {texture_path}")
                PyImGui.text(f"Attribute: {att_desc}")
                PyImGui.text(f"Profession: {profession}")
                PyImGui.text(f"Campaign: {campaign}")
                PyImGui.text(f"Elite: {'Yes' if IsElite(skill_id) else 'No'}")
                PyImGui.end_tooltip()
    
    def draw_upkeep(skill_id: int):
        if is_mantained(skill_id):
            PyImGui.begin_group()
            ImGui.push_font("Bold", 20)
            PyImGui.text("-1")
            ImGui.pop_font()
            PyImGui.same_line(0,5)
            ImGui.DrawTexture(TEXTURE_FOLDER + "upkeep.png", 22, 22)
            PyImGui.end_group()
            if PyImGui.is_item_hovered():
                if PyImGui.begin_tooltip():
                    energy_pips = GLOBAL_CACHE.Agent.GetEnergyPips(GLOBAL_CACHE.Player.GetAgentID())
                    PyImGui.text(f"Skill is maintained")
                    PyImGui.text(f"You can upkeep {energy_pips}x this skill")
                    PyImGui.end_tooltip()
                    
    def draw_sacrifice(skill_id: int):
        if is_sacrifice(skill_id):
            PyImGui.begin_group()
            health_cost = GLOBAL_CACHE.Skill.Data.GetHealthCost(skill_id)
            ImGui.push_font("Bold", 20)
            PyImGui.text(f"{health_cost}%")
            ImGui.pop_font()
            PyImGui.same_line(0,5)
            ImGui.DrawTexture(TEXTURE_FOLDER + "sacrifice.png", 22, 22)
            PyImGui.end_group()
            if PyImGui.is_item_hovered():
                if PyImGui.begin_tooltip():
                    max_health = GLOBAL_CACHE.Agent.GetMaxHealth(GLOBAL_CACHE.Player.GetAgentID())
                    PyImGui.text(f"Health Cost: {health_cost}%")
                    PyImGui.text(f"HP Cost: {math.ceil(max_health * (health_cost / 100))}")
                    PyImGui.end_tooltip()
                    
    def draw_overcast(skill_id: int):
        if is_overcast(skill_id):
            PyImGui.begin_group()
            overcast = GLOBAL_CACHE.Skill.Data.GetOvercast(skill_id)
            ImGui.push_font("Bold", 20)
            PyImGui.text(f"{overcast}")
            ImGui.pop_font()
            PyImGui.same_line(0,5)
            ImGui.DrawTexture(TEXTURE_FOLDER + "overcast.png", 22, 22)
            PyImGui.end_group()
            if PyImGui.is_item_hovered():
                if PyImGui.begin_tooltip():
                    PyImGui.text(f"Overcast: {overcast}")
                    PyImGui.end_tooltip()
          
    def draw_adrenaline(skill_id: int):
        if is_adrenaline(skill_id):
            PyImGui.begin_group()
            adrenaline = GLOBAL_CACHE.Skill.Data.GetAdrenaline(skill_id)
            ImGui.push_font("Bold", 20)
            PyImGui.text(f"{math.ceil(adrenaline / 25)}")
            ImGui.pop_font()
            PyImGui.same_line(0,5)
            ImGui.DrawTexture(TEXTURE_FOLDER + "adrenaline.png", 22, 22)
            PyImGui.end_group()
            if PyImGui.is_item_hovered():
                if PyImGui.begin_tooltip():
                    PyImGui.text(f"Adrenaline hits: {math.ceil(adrenaline / 25)}")
                    PyImGui.text(f"Adrenaline points: {adrenaline}")
                    PyImGui.end_tooltip()          
                    
    def draw_energy(skill_id: int):
        if is_energy(skill_id):
            PyImGui.begin_group()
            energy_cost = GLOBAL_CACHE.Skill.Data.GetEnergyCost(skill_id)
            ImGui.push_font("Bold", 20)
            PyImGui.text(f"{energy_cost}")
            ImGui.pop_font()
            PyImGui.same_line(0,5)
            ImGui.DrawTexture(TEXTURE_FOLDER + "energy.png", 22, 22)
            PyImGui.end_group()
            if PyImGui.is_item_hovered():
                if PyImGui.begin_tooltip():
                    PyImGui.text(f"Energy Cost: {energy_cost}")
                    energy_pips = GLOBAL_CACHE.Agent.GetEnergyPips(GLOBAL_CACHE.Player.GetAgentID())
                    PyImGui.text(f"Energy Pips: {energy_pips}")
                    max_energy = GLOBAL_CACHE.Agent.GetMaxEnergy(GLOBAL_CACHE.Player.GetAgentID())
                    PyImGui.text(f"Energy: {max_energy}")

                    if energy_pips > 0:
                        recoup_time = round(energy_cost / (energy_pips * 0.33), 2)
                        PyImGui.text(f"Time to Recoup Cost: {recoup_time} seconds")
                    else:
                        PyImGui.text("No regeneration (0 pips)")
                    
                    PyImGui.end_tooltip()
                    
    def draw_activation_time(skill_id: int):
        if is_activation_time(skill_id):
            PyImGui.begin_group()
            activation_time = GLOBAL_CACHE.Skill.Data.GetActivation(skill_id)
            fraction = Fraction(activation_time).limit_denominator(10)  # limit to reasonable fractions like 1/4, 1/2
            ImGui.push_font("Bold", 20)
            PyImGui.text(f"{fraction}")
            ImGui.pop_font()
            PyImGui.same_line(0,5)
            ImGui.DrawTexture(TEXTURE_FOLDER + "activation.png", 22, 22)
            PyImGui.end_group()
            if PyImGui.is_item_hovered():
                if PyImGui.begin_tooltip():
                    PyImGui.text(f"Activation Time: {activation_time} seconds")
                    aftercast = GLOBAL_CACHE.Skill.Data.GetAftercast(skill_id)
                    PyImGui.text(f"Aftercast: {aftercast}")
                    PyImGui.end_tooltip()
    
    def draw_recharge(skill_id: int):
        if is_recharge(skill_id):
            PyImGui.begin_group()
            recharge = GLOBAL_CACHE.Skill.Data.GetRecharge(skill_id)
            ImGui.push_font("Bold", 20)
            PyImGui.text(f"{recharge}")
            ImGui.pop_font()
            PyImGui.same_line(0,5)
            ImGui.DrawTexture(TEXTURE_FOLDER + "recharge.png", 22, 22)
            PyImGui.end_group()
            if PyImGui.is_item_hovered():
                if PyImGui.begin_tooltip():
                    PyImGui.text(f"Recharge Time: {recharge} seconds")
                    PyImGui.end_tooltip()
                    
    def draw_description(skill_id: int):
        PyImGui.begin_group()
        if IsElite(skill_id):
            elite_status = "Elite "
        else:
            elite_status = ""
        
        skill_type, skill_type_description = GLOBAL_CACHE.Skill.GetType(skill_id)

        if SkillType(skill_type) != SkillType.Attack:
            formatted_type = (f"{skill_type_description}. ")
        else:
            weapon_req = GLOBAL_CACHE.Skill.Data.GetWeaponReq(skill_id)
            
            if weapon_req in WeaporReq._value2member_map_:
                weapon_enum = WeaporReq(weapon_req)
                weapon_req_desc = weapon_enum.name + " " + skill_type_description
            else:
                weapon_enum = WeaporReq.None_
                weapon_req_desc = skill_type_description
            formatted_type = f"{weapon_req_desc}. "
            
        trimmed_desc = strip_skill_type(GLOBAL_CACHE.Skill.GetDescription(skill_id))  
        parsed_desc = resolve_skill_description(skill_id, trimmed_desc,0)
        description = f"{elite_status}{formatted_type}{parsed_desc}"
        PyImGui.text_wrapped(f"{description}")
        PyImGui.end_group()
        if PyImGui.is_item_hovered():
            if PyImGui.begin_tooltip():
                PyImGui.push_text_wrap_pos(400)
                concise = GLOBAL_CACHE.Skill.GetConciseDescription(skill_id)
                concise = resolve_skill_description(skill_id, concise, 0)
                PyImGui.text_wrapped(f"{concise}")
                PyImGui.pop_text_wrap_pos()
                PyImGui.end_tooltip()
                    
    # Begin drawing the skill card
    PyImGui.begin_group()
    table_start = PyImGui.get_cursor_screen_pos()
    draw_background_frame()
    
    if PyImGui.begin_table(f"Skill Table##{skill_id}", 2, PyImGui.TableFlags.NoFlag):
        PyImGui.table_setup_column("Texture", init_width_or_weight=100.0, flags=PyImGui.TableColumnFlags.WidthFixed)
        PyImGui.table_setup_column("Skill Name", init_width_or_weight=100.0, flags=PyImGui.TableColumnFlags.WidthStretch)
        PyImGui.table_next_row()
        PyImGui.table_next_column()
        
        draw_skill_icon(skill_id)

        PyImGui.table_next_column()
        draw_title(skill_id)
        PyImGui.new_line()
        draw_upkeep(skill_id)
        PyImGui.same_line(0,-1)
        draw_sacrifice(skill_id)
        PyImGui.same_line(0,-1)
        draw_overcast(skill_id)
        PyImGui.same_line(0,-1)
        draw_adrenaline(skill_id)
        PyImGui.same_line(0,-1) 
        draw_energy(skill_id)
        PyImGui.same_line(0,-1) 
        draw_activation_time(skill_id)
        PyImGui.same_line(0,-1) 
        draw_recharge(skill_id)
        PyImGui.same_line(0,-1)
        PyImGui.new_line()
        draw_description(skill_id)

        PyImGui.end_table()
    PyImGui.end_group()
    table_end = PyImGui.get_item_rect_max()

def main():
    global selected_skill, compare_skills, table_start, table_end
    
    if not Routines.Checks.Map.MapValid():
        return
    
    try:
        window_flags = PyImGui.WindowFlags.AlwaysAutoResize
        if PyImGui.begin("move", window_flags):
            hovered_skill = GLOBAL_CACHE.SkillBar.GetHoveredSkillID()
            PyImGui.text(f"Hovered Skill ID: {hovered_skill}")
            if hovered_skill != 0:
                selected_skill = hovered_skill

            selected_skill = PyImGui.input_int("Selected Skill ID", selected_skill)

            compare_skills = ImGui.toggle_button("Compare Skills", compare_skills)
            if compare_skills:
                DrawCompareSkills()

            if selected_skill != 0:
                DrawSkillCard(selected_skill)

                
                
                
        PyImGui.end()
    except Exception as e:
        Py4GW.Console.Log(MODULE_NAME, f"Error: {str(e)}", Py4GW.Console.MessageType.Error)
        raise


def DrawCompareSkills():
    def compare_text(display_name, val_a, val_b):
        PyImGui.table_next_row()
        
        # Color by equality
        color = ColorPalette.GetColor("Green") if val_a == val_b else ColorPalette.GetColor("Red")
        normalized = color.to_tuple_normalized()

        # Skill A Column
        PyImGui.table_next_column()
        PyImGui.text_colored(f"{display_name}: {val_a}", normalized)

        # Skill B Column
        PyImGui.table_next_column()
        PyImGui.text_colored(f"{display_name}: {val_b}", normalized)

    global hovered_skill, askill_a, askill_b
    window_flags = PyImGui.WindowFlags.AlwaysAutoResize
    if PyImGui.begin("compare", window_flags):
        hs = GLOBAL_CACHE.SkillBar.GetHoveredSkillID()
        if hs != 0:
            hovered_skill = hs

        PyImGui.text(f"Hovered Skill ID: {hovered_skill}")
        askill_a = PyImGui.input_int("Skill A", askill_a)
        askill_b = PyImGui.input_int("Skill B", askill_b)

        if askill_a != 0 and askill_b != 0:
            if PyImGui.begin_table("Skills Comparison Table", 2, PyImGui.TableFlags.Borders | PyImGui.TableFlags.RowBg):
                PyImGui.table_setup_column("Skill A")
                PyImGui.table_setup_column("Skill B")
                PyImGui.table_headers_row()

                skill_a = PySkill.Skill(askill_a)
                skill_b = PySkill.Skill(askill_b)

                # Texture + Name
                PyImGui.table_next_row()
                PyImGui.table_next_column()
                ImGui.DrawTexture(GLOBAL_CACHE.Skill.ExtraData.GetTexturePath(askill_a), 96, 96)
                PyImGui.text(f"ID: {askill_a}")
                PyImGui.text(f"Name: {GLOBAL_CACHE.Skill.GetNameFromWiki(askill_a)}")

                PyImGui.table_next_column()
                ImGui.DrawTexture(GLOBAL_CACHE.Skill.ExtraData.GetTexturePath(askill_b), 96, 96)
                PyImGui.text(f"ID: {askill_b}")
                PyImGui.text(f"Name: {GLOBAL_CACHE.Skill.GetNameFromWiki(askill_b)}")

                # Field comparisons
                compare_text("special", skill_a.special, skill_b.special)
                compare_text("combo_req", skill_a.combo_req, skill_b.combo_req)
                compare_text("effect1", skill_a.effect1, skill_b.effect1)
                compare_text("condition", skill_a.condition, skill_b.condition)
                compare_text("effect2", skill_a.effect2, skill_b.effect2)
                compare_text("weapon_req", skill_a.weapon_req, skill_b.weapon_req)
                compare_text("title", skill_a.title, skill_b.title)
                compare_text("id_pvp", skill_a.id_pvp, skill_b.id_pvp)
                compare_text("combo", skill_a.combo, skill_b.combo)
                compare_text("target", skill_a.target, skill_b.target)
                compare_text("skill_equip_type", skill_a.skill_equip_type, skill_b.skill_equip_type)
                compare_text("overcast", skill_a.overcast, skill_b.overcast)
                compare_text("energy_cost", skill_a.energy_cost, skill_b.energy_cost)
                compare_text("health_cost", skill_a.health_cost, skill_b.health_cost)
                compare_text("adrenaline", skill_a.adrenaline, skill_b.adrenaline)
                compare_text("activation", skill_a.activation, skill_b.activation)
                compare_text("aftercast", skill_a.aftercast, skill_b.aftercast)
                compare_text("duration_0pts", skill_a.duration_0pts, skill_b.duration_0pts)
                compare_text("duration_15pts", skill_a.duration_15pts, skill_b.duration_15pts)
                compare_text("recharge", skill_a.recharge, skill_b.recharge)
                compare_text("skill_arguments", skill_a.skill_arguments, skill_b.skill_arguments)
                compare_text("scale_0pts", skill_a.scale_0pts, skill_b.scale_0pts)
                compare_text("scale_15pts", skill_a.scale_15pts, skill_b.scale_15pts)
                compare_text("bonus_scale_0pts", skill_a.bonus_scale_0pts, skill_b.bonus_scale_0pts)
                compare_text("bonus_scale_15pts", skill_a.bonus_scale_15pts, skill_b.bonus_scale_15pts)
                compare_text("aoe_range", skill_a.aoe_range, skill_b.aoe_range)
                compare_text("const_effect", skill_a.const_effect, skill_b.const_effect)
                compare_text("caster_overhead_animation_id", skill_a.caster_overhead_animation_id, skill_b.caster_overhead_animation_id)
                compare_text("caster_body_animation_id", skill_a.caster_body_animation_id, skill_b.caster_body_animation_id)
                compare_text("target_body_animation_id", skill_a.target_body_animation_id, skill_b.target_body_animation_id)
                compare_text("target_overhead_animation_id", skill_a.target_overhead_animation_id, skill_b.target_overhead_animation_id)
                compare_text("h0004", skill_a.h0004, skill_b.h0004)
                compare_text("h0032", skill_a.h0032, skill_b.h0032)
                compare_text("h0037", skill_a.h0037, skill_b.h0037)

                PyImGui.end_table()

    PyImGui.end()

    
if __name__ == "__main__":
    main()
    
