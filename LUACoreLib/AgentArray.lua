local AgentArray = {}

function AgentArray.GetAgentArray()
    return Player.player_instance():GetAgentArray()
end

function AgentArray.GetAllyArray()
    return Player.player_instance():GetAllyArray()
end

function AgentArray.GetNeutralArray()
    return Player.player_instance():GetNeutralArray()
end

function AgentArray.GetEnemyArray()
    return Player.player_instance():GetEnemyArray()
end

function AgentArray.GetSpiritPetArray()
    return Player.player_instance():GetSpiritPetArray()
end

function AgentArray.GetMinionArray()
    return Player.player_instance():GetMinionArray()
end

function AgentArray.GetNPCMinipetArray()
    return Player.player_instance():GetNPCMinipetArray()
end

function AgentArray.GetItemArray()
    return Player.player_instance():GetItemArray()
end

function AgentArray.GetGadgetArray()
    return Player.player_instance():GetGadgetArray()
end

function AgentArray.Merge(array1, array2)
    local merged = {}
    for _, v in pairs(array1) do
        merged[v] = true
    end
    for _, v in pairs(array2) do
        merged[v] = true
    end
    local result = {}
    for k, _ in pairs(merged) do
        table.insert(result, k)
    end
    return result
end

function AgentArray.Subtract(array1, array2)
    local result = {}
    for _, v in pairs(array1) do
        if not Utils.Contains(array2, v) then
            table.insert(result, v)
        end
    end
    return result
end

function AgentArray.Intersect(array1, array2)
    local result = {}
    for _, v in pairs(array1) do
        if Utils.Contains(array2, v) then
            table.insert(result, v)
        end
    end
    return result
end

function AgentArray.Sort.ByAttribute(agent_array, attribute, descending)
    local sorted = {}
    for _, v in pairs(agent_array) do
        table.insert(sorted, v)
    end
    table.sort(sorted, function(a, b)
        local attr_a = Agent[attribute](a)
        local attr_b = Agent[attribute](b)
        if descending then
            return attr_a > attr_b
        else
            return attr_a < attr_b
        end
    end)
    return sorted
end

function AgentArray.Sort.ByCondition(agent_array, condition_func, reverse)
    local sorted = {}
    for _, v in pairs(agent_array) do
        table.insert(sorted, v)
    end
    table.sort(sorted, function(a, b)
        local cond_a = condition_func(a)
        local cond_b = condition_func(b)
        if reverse then
            return cond_a > cond_b
        else
            return cond_a < cond_b
        end
    end)
    return sorted
end

function AgentArray.Sort.ByDistance(agent_array, pos, descending)
    local sorted = {}
    for _, v in pairs(agent_array) do
        table.insert(sorted, v)
    end
    table.sort(sorted, function(a, b)
        local dist_a = Utils.Distance(Agent.GetXY(a), pos)
        local dist_b = Utils.Distance(Agent.GetXY(b), pos)
        if descending then
            return dist_a > dist_b
        else
            return dist_a < dist_b
        end
    end)
    return sorted
end

function AgentArray.Sort.ByHealth(agent_array, descending)
    local sorted = {}
    for _, v in pairs(agent_array) do
        table.insert(sorted, v)
    end
    table.sort(sorted, function(a, b)
        local health_a = Agent.GetHealth(a)
        local health_b = Agent.GetHealth(b)
        if descending then
            return health_a > health_b
        else
            return health_a < health_b
        end
    end)
    return sorted
end

function AgentArray.Filter.ByAttribute(agent_array, attribute, condition_func, negate)
    local filtered = {}
    for _, v in pairs(agent_array) do
        local attr_value = Agent[attribute](v)
        if condition_func then
            attr_value = condition_func(attr_value)
        end
        if negate then
            attr_value = not attr_value
        end
        if attr_value then
            table.insert(filtered, v)
        end
    end
    return filtered
end

function AgentArray.Filter.ByCondition(agent_array, filter_func)
    local filtered = {}
    for _, v in pairs(agent_array) do
        if filter_func(v) then
            table.insert(filtered, v)
        end
    end
    return filtered
end

function AgentArray.Filter.ByDistance(agent_array, pos, max_distance, negate)
    local filtered = {}
    for _, v in pairs(agent_array) do
        local dist = Utils.Distance(Agent.GetXY(v), pos)
        if negate then
            if dist > max_distance then
                table.insert(filtered, v)
            end
        else
            if dist <= max_distance then
                table.insert(filtered, v)
            end
        end
    end
    return filtered
end

function AgentArray.Routines.DetectLargestAgentCluster(agent_array, cluster_radius)
    local clusters = {}
    local ungrouped_agents = {}
    for _, v in pairs(agent_array) do
        ungrouped_agents[v] = true
    end

    local function is_in_radius(agent1, agent2)
        local x1, y1 = Agent.GetXY(agent1)
        local x2, y2 = Agent.GetXY(agent2)
        local distance_sq = (x1 - x2) ^ 2 + (y1 - y2) ^ 2
        return distance_sq <= cluster_radius ^ 2
    end

    while next(ungrouped_agents) do
        local current_agent = next(ungrouped_agents)
        local cluster = {current_agent}
        ungrouped_agents[current_agent] = nil

        for agent, _ in pairs(ungrouped_agents) do
            if is_in_radius(current_agent, agent) then
                table.insert(cluster, agent)
                ungrouped_agents[agent] = nil
            end
        end

        table.insert(clusters, cluster)
    end

    local largest_cluster = {}
    for _, cluster in pairs(clusters) do
        if #cluster > #largest_cluster then
            largest_cluster = cluster
        end
    end

    local total_x = 0
    local total_y = 0
    for _, agent_id in pairs(largest_cluster) do
        local x, y = Agent.GetXY(agent_id)
        total_x = total_x + x
        total_y = total_y + y
    end

    local center_of_mass_x = total_x / #largest_cluster
    local center_of_mass_y = total_y / #largest_cluster
    local center_of_mass = {center_of_mass_x, center_of_mass_y}

    local function distance_to_center(agent_id)
        local x, y = Agent.GetXY(agent_id)
        return Utils.Distance({x, y}, center_of_mass)
    end

    local closest_agent_id = nil
    local min_distance = math.huge
    for _, agent_id in pairs(largest_cluster) do
        local distance = distance_to_center(agent_id)
        if distance < min_distance then
            min_distance = distance
            closest_agent_id = agent_id
        end
    end

    return center_of_mass, closest_agent_id
end

return AgentArray
