local Party = {}

function Party.party_instance()
    return PyParty.PyParty()
end

function Party.GetPartyID()
    return Party.party_instance().party_id
end

function Party.GetPartyLeaderID()
    local players = Party.GetPlayers()
    local leader = players[1]
    return Party.Players.GetAgentIDByLoginNumber(leader.login_number)
end

function Party.GetOwnPartyNumber()
    for i = 1, #Party.GetPlayers() do
        local player_id = Party.Players.GetAgentIDByLoginNumber(Party.GetPlayers()[i].login_number)
        if player_id == Player.GetAgentID() then
            return i - 1
        end
    end
    return -1
end

function Party.GetPlayers()
    return Party.party_instance().players
end

function Party.GetHeroes()
    return Party.party_instance().heroes
end

function Party.GetHenchmen()
    return Party.party_instance().henchmen
end

function Party.IsHardModeUnlocked()
    return Party.party_instance().is_hard_mode_unlocked
end

function Party.IsHardMode()
    return Party.party_instance().is_in_hard_mode
end

function Party.IsNormalMode()
    return not Party.IsHardMode()
end

function Party.GetPartySize()
    return Party.party_instance().party_size
end

function Party.GetPlayerCount()
    return Party.party_instance().party_player_count
end

function Party.GetHeroCount()
    return Party.party_instance().party_hero_count
end

function Party.GetHenchmanCount()
    return Party.party_instance().party_henchman_count
end

function Party.IsPartyDefeated()
    return Party.party_instance().is_party_defeated
end

function Party.IsPartyLoaded()
    return Party.party_instance().is_party_loaded
end

function Party.IsPartyLeader()
    return Party.party_instance().is_party_leader
end

function Party.SetTickasToggle(enable)
    Party.party_instance().tick:SetTickToggle(enable)
end

function Party.IsAllTicked()
    return Party.party_instance().tick:IsTicked()
end

function Party.IsPlayerTicked(login_number)
    return Party.party_instance():GetIsPlayerTicked(login_number)
end

function Party.SetTicked(ticked)
    Party.party_instance().tick:SetTicked(ticked)
end

function Party.ToggleTicked()
    local login_number = Party.Players.GetLoginNumberByAgentID(Player.GetAgentID())
    local party_number = Party.Players.GetPartyNumberFromLoginNumber(login_number)

    if Party.IsPlayerTicked(party_number) then
        Party.SetTicked(false)
    else
        Party.SetTicked(true)
    end
end

function Party.SetHardMode()
    if Party.IsHardModeUnlocked() and Party.IsNormalMode() then
        Party.party_instance().SetHardMode(true)
    end
end

function Party.SetNormalMode()
    if Party.IsHardMode() then
        Party.party_instance().SetHardMode(false)
    end
end

function Party.SearchParty(search_type, advertisement)
    return Party.party_instance().SearchParty(search_type, advertisement)
end

function Party.SearchPartyCancel()
    Party.party_instance().SearchPartyCancel()
end

function Party.SearchPartyReply(accept)
    return Party.party_instance().SearchPartyReply(accept)
end

function Party.RespondToPartyRequest(party_id, accept)
    return Party.party_instance().RespondToPartyRequest(party_id, accept)
end

function Party.ReturnToOutpost()
    Party.party_instance().ReturnToOutpost()
end

function Party.LeaveParty()
    Party.party_instance().LeaveParty()
end

Party.Players = {}
function Party.Players.GetAgentIDByLoginNumber(login_number)
    return Party.party_instance().GetAgentIDByLoginNumber(login_number)
end

function Party.Players.GetPlayerNameByLoginNumber(login_number)
    return Party.party_instance().GetPlayerNameByLoginNumber(login_number)
end

function Party.Players.GetPartyNumberFromLoginNumber(login_number)
    local players = Party.GetPlayers()
    for index, player in ipairs(players) do
        if player.login_number == login_number then
            return index - 1
        end
    end
    return -1
end

function Party.Players.GetLoginNumberByAgentID(agent_id)
    local players = Party.GetPlayers()
    for _, player in ipairs(players) do
        local player_id = Party.Players.GetAgentIDByLoginNumber(player.login_number)
        if agent_id == player_id then
            return player.login_number
        end
    end
    return 0
end

function Party.Players.InvitePlayer(agent_id_or_name)
    if type(agent_id_or_name) == "number" then
        Party.party_instance().InvitePlayer(agent_id_or_name)
    elseif type(agent_id_or_name) == "string" then
        Player.SendChatCommand("invite " .. agent_id_or_name)
    else
        error("Invalid argument type. Must be number (ID) or string (name).")
    end
end

function Party.Players.KickPlayer(login_number)
    Party.party_instance().KickPlayer(login_number)
end

Party.Heroes = {}
function Party.Heroes.GetHeroAgentIDByPartyPosition(hero_position)
    return Party.party_instance().GetHeroAgentID(hero_position)
end

function Party.Heroes.GetHeroIDByAgentID(agent_id)
    local heroes = Party.GetHeroes()
    for _, hero in ipairs(heroes) do
        if hero.agent_id == agent_id then
            return hero.hero_id:GetID()
        end
    end
end

function Party.Heroes.GetHeroIDByPartyPosition(hero_position)
    local heroes = Party.GetHeroes()
    for index, hero in ipairs(heroes) do
        if index - 1 == hero_position then
            return hero.hero_id:GetID()
        end
    end
end

function Party.Heroes.GetHeroIdByName(hero_name)
    local hero = PyParty.Hero(hero_name)
    return hero:GetId()
end

function Party.Heroes.GetHeroNameById(hero_id)
    local hero = PyParty.Hero(hero_id)
    return hero:GetName()
end

function Party.Heroes.GetNameByAgentID(agent_id)
    local heroes = Party.GetHeroes()
    for _, hero in ipairs(heroes) do
        if hero.agent_id == agent_id then
            return hero.hero_id:GetName()
        end
    end
end

function Party.Heroes.AddHero(hero_id)
    Party.party_instance().AddHero(hero_id)
end

function Party.Heroes.AddHeroByName(hero_name)
    local hero = PyParty.Hero(hero_name)
    Party.party_instance().AddHero(hero:GetID())
end

function Party.Heroes.KickHero(hero_id)
    Party.party_instance().KickHero(hero_id)
end

function Party.Heroes.KickHeroByName(hero_name)
    local hero = PyParty.Hero(hero_name)
    Party.party_instance().KickHero(hero:GetID())
end

function Party.Heroes.KickAllHeroes()
    Party.party_instance().KickAllHeroes()
end

function Party.Heroes.FlagHero(hero_id, x, y)
    Party.party_instance().FlagHero(hero_id, x, y)
end

function Party.Heroes.FlagAllHeroes(x, y)
    Party.party_instance().FlagAllHeroes(x, y)
end

function Party.Heroes.UnflagHero(hero_id)
    Party.party_instance().UnflagHero(hero_id)
end

function Party.Heroes.UnflagAllHeroes()
    Party.party_instance().UnflagAllHeroes()
end

function Party.Heroes.IsHeroFlagged(hero_party_number)
    return Party.party_instance().IsHeroFlagged(hero_party_number)
end

function Party.Heroes.IsAllFlagged()
    return Party.party_instance().IsAllFlagged()
end

function Party.Heroes.GetAllFlag()
    return Party.party_instance().GetAllFlagX(), Party.party_instance().GetAllFlagY()
end

function Party.Heroes.SetHeroBehavior(hero_agent_id, behavior)
    Party.party_instance().SetHeroBehavior(hero_agent_id, behavior)
end

Party.Henchmen = {}
function Party.Henchmen.AddHenchman(henchman_id)
    Party.party_instance().AddHenchman(henchman_id)
end

function Party.Henchmen.KickHenchman(henchman_id)
    Party.party_instance().KickHenchman(henchman_id)
end

Party.Pets = {}
function Party.Pets.SetPetBehavior(behavior, lock_target_id)
    Party.party_instance().SetPetBehavior(behavior, lock_target_id)
end

function Party.Pets.GetPetInfo(owner_id)
    return Party.party_instance().GetPetInfo(owner_id)
end

return Party
