local Effects = {}

function Effects.DropBuff(buff_id)
    local agent_effects = PyEffects.PyEffects(Player.GetAgentID())
    agent_effects:DropBuff(buff_id)
end

function Effects.GetBuffs(agent_id)
    local agent_effects = PyEffects.PyEffects(agent_id)
    local buff_list = agent_effects:GetBuffs()
    return buff_list
end

function Effects.GetEffects(agent_id)
    local agent_effects = PyEffects.PyEffects(agent_id)
    local effects_list = agent_effects:GetEffects()
    return effects_list
end

function Effects.GetBuffCount(agent_id)
    local agent_effects = PyEffects.PyEffects(agent_id)
    local buff_count = agent_effects:GetBuffCount()
    return buff_count
end

function Effects.GetEffectCount(agent_id)
    local agent_effects = PyEffects.PyEffects(agent_id)
    local effect_count = agent_effects:GetEffectCount()
    return effect_count
end

function Effects.BuffExists(agent_id, skill_id)
    local agent_effects = PyEffects.PyEffects(agent_id)
    local buff_exists = agent_effects:BuffExists(skill_id)
    return buff_exists
end

function Effects.EffectExists(agent_id, skill_id)
    local agent_effects = PyEffects.PyEffects(agent_id)
    local effect_exists = agent_effects:EffectExists(skill_id)
    return effect_exists
end

function Effects.EffectAttributeLevel(agent_id, skill_id)
    local agent_effects = PyEffects.PyEffects(agent_id)
    local effects_list = agent_effects:GetEffects()
    for _, effect in pairs(effects_list) do
        if effect.skill_id == skill_id then
            return effect.attribute_level
        end
    end
    return 0
end

return Effects
