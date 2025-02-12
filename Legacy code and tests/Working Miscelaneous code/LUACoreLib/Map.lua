local Map = {}

function Map.map_instance()
    return PyMap.PyMap()
end

function Map.IsMapReady()
    return Map.map_instance().is_map_ready
end

function Map.IsOutpost()
    return Map.map_instance().instance_type:GetName() == "Outpost"
end

function Map.IsExplorable()
    return Map.map_instance().instance_type:GetName() == "Explorable"
end

function Map.IsMapLoading()
    return Map.map_instance().instance_type:GetName() == "Loading"
end

function Map.GetMapName(mapid)
    if mapid == nil then
        map_id = Map.GetMapID()
    else
        map_id = mapid
    end

    if explorables[map_id] then
        return explorables[map_id]
    end

    local map_id_instance = PyMap.MapID(map_id)
    return map_id_instance:GetName()
end

function Map.GetMapID()
    return Map.map_instance().map_id:ToInt()
end

function Map.GetOutpostIDs()
    local map_id_instance = PyMap.MapID(Map.GetMapID())
    return map_id_instance:GetOutpostIDs()
end

function Map.GetOutpostNames()
    local map_id_instance = PyMap.MapID(Map.GetMapID())
    return map_id_instance:GetOutpostNames()
end

function Map.GetMapIDByName(name)
    if explorable_name_to_id[name] then
        return explorable_name_to_id[name]
    end

    local outpost_ids = Map.GetOutpostIDs()
    local outpost_names = Map.GetOutpostNames()
    local outpost_name_to_id = {}
    for i, id in pairs(outpost_ids) do
        outpost_name_to_id[outpost_names[i]] = id
    end

    return outpost_name_to_id[name] or 0
end

function Map.GetExplorableIDs()
    local ids = {}
    for id, _ in pairs(explorables) do
        table.insert(ids, id)
    end
    return ids
end

function Map.GetExplorableNames()
    local names = {}
    for _, name in pairs(explorables) do
        table.insert(names, name)
    end
    return names
end

function Map.Travel(map_id)
    Map.map_instance():Travel(map_id)
end

function Map.TravelToDistrict(map_id, district, district_number)
    Map.map_instance():Travel(map_id, district, district_number)
end

function Map.GetInstanceUptime()
    return Map.map_instance().instance_time
end

function Map.GetMaxPartySize()
    return Map.map_instance().max_party_size
end

function Map.IsInCinematic()
    return Map.map_instance().is_in_cinematic
end

function Map.SkipCinematic()
    Map.map_instance():SkipCinematic()
end

function Map.HasEnterChallengeButton()
    return Map.map_instance().has_enter_button
end

function Map.EnterChallenge()
    Map.map_instance():EnterChallenge()
end

function Map.CancelEnterChallenge()
    Map.map_instance():CancelEnterChallenge()
end

function Map.IsVanquishable()
    return Map.map_instance().is_vanquishable_area
end

function Map.GetFoesKilled()
    return Map.map_instance().foes_killed
end

function Map.GetFoesToKill()
    return Map.map_instance().foes_to_kill
end

function Map.GetCampaign()
    local campaign = Map.map_instance().campaign
    return campaign:ToInt(), campaign:GetName()
end

function Map.GetContinent()
    local continent = Map.map_instance().continent
    return continent:ToInt(), continent:GetName()
end

function Map.GetRegionType()
    local region_type = Map.map_instance().region_type
    return region_type:ToInt(), region_type:GetName()
end

function Map.GetDistrict()
    return Map.map_instance().district
end

function Map.GetRegion()
    local region = Map.map_instance().server_region
    return region:ToInt(), region:GetName()
end

function Map.GetLanguage()
    local language = Map.map_instance().language
    return language:ToInt(), language:GetName()
end

function Map.RegionFromDistrict(district)
    local region = Map.map_instance():RegionFromDistrict(district)
    return region:ToInt(), region:GetName()
end

function Map.LanguageFromDistrict(district)
    local language = Map.map_instance():LanguageFromDistrict(district)
    return language:ToInt(), language:GetName()
end

function Map.GetIsMapUnlocked(mapid)
    if mapid == nil then
        map_id = Map.GetMapID()
    else
        map_id = mapid
    end

    local map_id_instance = PyMap.MapID(map_id)
    return map_id_instance:GetIsMapUnlocked(map_id_instance.map_id:ToInt())
end

function Map.GetAmountOfPlayersInInstance()
    return Map.map_instance().amount_of_players_in_instance
end

return Map
