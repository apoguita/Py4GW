local SkillBar = {}

function SkillBar.LoadSkillTemplate(skill_template)
    PySkillbar.Skillbar():LoadSkillTemplate(skill_template)
end

function SkillBar.LoadHeroSkillTemplate(hero_index, skill_template)
    PySkillbar.Skillbar():LoadHeroSkillTemplate(hero_index, skill_template)
end

function SkillBar.GetSkillbar()
    local skill_ids = {}
    for slot = 1, 8 do
        local skill_id = SkillBar.GetSkillIDBySlot(slot)
        if skill_id ~= 0 then
            table.insert(skill_ids, skill_id)
        end
    end
    return skill_ids
end

function SkillBar.GetHeroSkillbar(hero_index)
    return PySkillbar.Skillbar():GetHeroSkillbar(hero_index)
end

function SkillBar.UseSkill(skill_slot, target_agent_id)
    target_agent_id = target_agent_id or 0
    PySkillbar.Skillbar():UseSkill(skill_slot, target_agent_id)
end

function SkillBar.HeroUseSkill(target_agent_id, skill_number, hero_number)
    PySkillbar.Skillbar():HeroUseSkill(target_agent_id, skill_number, hero_number)
end

function SkillBar.ChangeHeroSecondary(hero_index, secondary_profession)
    PySkillbar.Skillbar():ChangeHeroSecondary(hero_index, secondary_profession)
end

function SkillBar.GetSkillIDBySlot(skill_slot)
    local skill = PySkillbar.Skillbar():GetSkill(skill_slot)
    return skill.id.id
end

function SkillBar.GetSlotBySkillID(skill_id)
    for i = 1, 8 do
        if SkillBar.GetSkillIDBySlot(i) == skill_id then
            return i
        end
    end
    return 0
end

function SkillBar.GetSkillData(slot)
    return PySkillbar.Skillbar():GetSkill(slot)
end

function SkillBar.GetHoveredSkillID()
    return PySkillbar.Skillbar():GetHoveredSkill()
end

function SkillBar.IsSkillUnlocked(skill_id)
    return PySkillbar.Skillbar():IsSkillUnlocked(skill_id)
end

function SkillBar.IsSkillLearnt(skill_id)
    return PySkillbar.Skillbar():IsSkillLearnt(skill_id)
end

function SkillBar.GetAgentID()
    return PySkillbar.Skillbar().agent_id
end

function SkillBar.GetDisabled()
    return PySkillbar.Skillbar().disabled
end

function SkillBar.GetCasting()
    return PySkillbar.Skillbar().casting
end

return SkillBar
