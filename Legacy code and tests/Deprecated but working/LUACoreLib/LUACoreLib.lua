local CoreLib = Py4GW.CoreLib
local pingHandler = Py4GW.PingHandler()

-- Name-related functions
function GetCharName()
    return CoreLib.Player.GetName()
end

function DisplayAllies(aDisplay)
    local allies = {}
    for _, agent in pairs(CoreLib.Agent.GetAgents()) do
        if agent.isAlly then
            table.insert(allies, agent.name)
        end
    end
    return allies
end

function DisplayEnemies(aDisplay)
    return {}
end

function GetPlayerName(aAgent)
    if aAgent == -2 then
        return CoreLib.Player.GetName()
    else
        return CoreLib.Agent.GetName(aAgent)
    end
end

function GetPartyPlayerNames()
    local partyPlayers = {}
    for _, agent in pairs(CoreLib.Agent.GetAgents()) do
        if agent.isPartyMember then
            table.insert(partyPlayers, agent.name)
        end
    end
    return partyPlayers
end

function GetPartyLeaderName()
    local partyLeader = CoreLib.Agent.GetPartyLeader()
    if partyLeader then
        return partyLeader.name
    else
        return nil
    end
end

function GetAgentName(aAgent)
    return CoreLib.Agent.GetName(aAgent)
end

-- Map-related functions
function GetInstanceUpTime()
    return CoreLib.Map.GetInstanceUptime()
end

function GetMapID()
    return CoreLib.Map.GetMapID()
end

function GetMapLoading()
    return CoreLib.Map.IsMapLoading()
end

function GetMapIsLoaded()
    return CoreLib.Map.IsMapReady()
end

function GetDistrict()
    return CoreLib.Map.GetDistrict()
end

function GetRegion()
    return CoreLib.Map.GetRegion()
end

function WaitMapLoading(aMapID, aDeadlock, skipCinematic)
    local startTime = os.time()
    while true do
        if CoreLib.Map.GetMapID() == aMapID and CoreLib.Map.IsMapReady() then
            break
        elseif os.time() - startTime > aDeadlock / 1000 then
            break
        end
        if skipCinematic and CoreLib.Map.IsInCinematic() then
            CoreLib.Map.SkipCinematic()
        end
        os.sleep(0.1)
    end
end

function GetInstanceTimestamp()
    return os.time()
end

function WaitForLoad()
    while not CoreLib.Map.IsMapReady() do
        os.sleep(0.1)
    end
end

function GetAreaVanquished()
    return CoreLib.Map.IsVanquishable()
end

function GetFoesKilled()
    return CoreLib.Map.GetFoesKilled()
end

function GetFoesToKill()
    return CoreLib.Map.GetFoesToKill()
end

-- Ping-related functions
function GetPing()
    return pingHandler:GetCurrentPing()
end

-- Chat Functions
function WriteChat(aMessage, aSender)
    CoreLib.Player.SendChat('chat', aMessage)
end

function SendWhisper(aReceiver, aMessage)
    CoreLib.Player.SendWhisper(aReceiver, aMessage)
end

-- Agent Functions
function GetAgentByID(aAgentID)
    return CoreLib.Agent.GetAgentByID(aAgentID)
end

function GetID(aAgent)
    return CoreLib.Agent.GetIDFromAgent(aAgent)
end

function GetX(aAgent)
    local xy = CoreLib.Agent.GetXY(aAgent)
    return xy.x
end

function GetY(aAgent)
    local xy = CoreLib.Agent.GetXY(aAgent)
    return xy.y
end

function GetXY(aAgent)
    return CoreLib.Agent.GetXY(aAgent)
end

function GetMoveX(aAgent)
    local velocity = CoreLib.Agent.GetVelocityXY(aAgent)
    return velocity.x
end

function GetMoveY(aAgent)
    local velocity = CoreLib.Agent.GetVelocityXY(aAgent)
    return velocity.y
end

-- Target Functions
function GetTarget(aAgent)
    return CoreLib.Player.GetTargetID()
end

function ChangeTarget(aAgent)
    CoreLib.Player.ChangeTarget(aAgent)
end

-- Best Target Functions
function GetBestTarget(aRange, aCastingOnly, aNoHexOnly, aEnchantedOnly)
    return CoreLib.Player.GetBestTarget(aRange, aCastingOnly, aNoHexOnly, aEnchantedOnly)
end

function GetBestMeleeTarget(aRange, aCastingOnly, aNoHexOnly, aEnchantedOnly)
    return CoreLib.Player.GetBestMeleeTarget(aRange, aCastingOnly, aNoHexOnly, aEnchantedOnly)
end

-- Nearest Functions
function GetNearestAllyToAgent(aAgent, aArea)
    return CoreLib.Agent.GetNearestAllyToAgent(aAgent, aArea)
end

function GetNearestMinionAllyToAgent(aAgent, aArea)
    return CoreLib.Agent.GetNearestMinionToAgent(aAgent, aArea)
end

function GetNearestNPCPtrToAgent(aAgent, aArea)
    return CoreLib.Agent.GetNearestNPCMinipetToAgent(aAgent, aArea)
end

function GetNearestItemToAgent(aAgent, aArea, aCanPickUp)
    return CoreLib.Agent.GetNearestItemToAgent(aAgent, aArea)
end

function GetNearestSignpostToAgent(aAgent, aArea)
    return CoreLib.Agent.GetNearestGadgetToAgent(aAgent, aArea)
end

function GetNearestNPCToAgent(aAgent, aArea)
    return CoreLib.Agent.GetNearestNPCMinipetToAgent(aAgent, aArea)
end

function GetNearestEnemyToAgent(aAgent, aArea)
    return CoreLib.Agent.GetNearestEnemyToAgent(aAgent, aArea)
end

function GetClosestInRangeOfAgent(aAgent, aRange, aAllegiance, aType)
    -- Note: This function is not directly equivalent to the GwA2 function,
    -- as Py4GW does not provide a direct equivalent. You may need to modify
    -- this function to suit your needs or use a different approach.
    return nil
end

-- Nearest Agent Functions
function GetNearestAgentToAgent(aAgent, area)
    local agents = {
        CoreLib.Agent.GetNearestAllyToAgent(aAgent, area),
        CoreLib.Agent.GetNearestNeutralToAgent(aAgent, area),
        CoreLib.Agent.GetNearestEnemyToAgent(aAgent, area),
        CoreLib.Agent.GetNearestSpiritPetToAgent(aAgent, area),
        CoreLib.Agent.GetNearestMinionToAgent(aAgent, area),
        CoreLib.Agent.GetNearestNPCMinipetToAgent(aAgent, area),
        CoreLib.Agent.GetNearestItemToAgent(aAgent, area),
        CoreLib.Agent.GetNearestGadgetToAgent(aAgent, area)
    }

    local nearestAgent = nil
    local minDistance = math.huge

    for _, agent in ipairs(agents) do
        if agent then
            local distance = CoreLib.Utils.Distance(aAgent, agent)
            if distance < minDistance then
                minDistance = distance
                nearestAgent = agent
            end
        end
    end

    return nearestAgent
end

function GetNearestAgentToCoords(x, y, area)
    local agents = {
        CoreLib.Agent.GetNearestAllyXY(x, y, area),
        CoreLib.Agent.GetNearestNeutralXY(x, y, area),
        CoreLib.Agent.GetNearestEnemyXY(x, y, area),
        CoreLib.Agent.GetNearestSpiritPetXY(x, y, area),
        CoreLib.Agent.GetNearestMinionXY(x, y, area),
        CoreLib.Agent.GetNearestNPCMinipetXY(x, y, area),
        CoreLib.Agent.GetNearestItemXY(x, y, area),
        CoreLib.Agent.GetNearestGadgetXY(x, y, area)
    }

    local nearestAgent = nil
    local minDistance = math.huge

    for _, agent in ipairs(agents) do
        if agent then
            local distance = CoreLib.Utils.Distance({x=x, y=y}, agent)
            if distance < minDistance then
                minDistance = distance
                nearestAgent = agent
            end
        end
    end

    return nearestAgent
end

function GetNumberOfEnemiesNearXY(x, y, aRange)
    local enemies = CoreLib.Agent.GetEnemiesInArea(x, y, aRange)
    return #enemies
end

-- Agent By Player Number Functions
function GetAgentByPlayerNumber(aPlayerNumber, aRange)
    local partyPlayers = CoreLib.Party.GetPlayers()
    for _, player in ipairs(partyPlayers) do
        if player.playerId == aPlayerNumber then
            return CoreLib.Party.GetAgentIDByPlayerID(aPlayerNumber)
        end
    end
    return nil
end

function GetAgentDistanceByPlayerNumber(aPlayerNumber)
    -- Note: This function is not directly equivalent to the GwA2 function,
    -- as Py4GW does not provide a direct equivalent. You may need to modify
    -- this function to suit your needs or use a different approach.
    local agentId = GetAgentByPlayerNumber(aPlayerNumber)
    if agentId then
        local agent = CoreLib.Agent.GetAgentByID(agentId)
        return CoreLib.Utils.Distance(agent.x, agent.y, agent.z)
    else
        return nil
    end
end

-- Party Functions
function GetParty(aAgentArray)
    -- Note: This function is not directly equivalent to the GwA2 function,
    -- as Py4GW does not provide a direct equivalent. You may need to modify
    -- this function to suit your needs or use a different approach.
    local partyPlayers = CoreLib.Party.GetPlayers()
    local partyAgents = {}
    for _, player in ipairs(partyPlayers) do
        table.insert(partyAgents, CoreLib.Party.GetAgentIDByPlayerID(player.playerId))
    end
    return partyAgents
end

function GetMaxPartySize(aMapID)
    return CoreLib.Map.GetMaxPartySize()
end

-- Agent Array Functions
function GetAgentArray(aType)
    if aType == 0 then
        return CoreLib.Player.GetAgentArray()
    elseif aType == 1 then
        return CoreLib.Player.GetAllyArray()
    elseif aType == 2 then
        return CoreLib.Player.GetNeutralArray()
    elseif aType == 3 then
        return CoreLib.Player.GetEnemyArray()
    elseif aType == 4 then
        return CoreLib.Player.GetSpiritPetArray()
    elseif aType == 5 then
        return CoreLib.Player.GetMinionArray()
    elseif aType == 6 then
        return CoreLib.Player.GetNPCMinipetArray()
    elseif aType == 7 then
        return CoreLib.Player.GetItemArray()
    elseif aType == 8 then
        return CoreLib.Player.GetGadgetArray()
    else
        return nil
    end
end

-- Danger Functions
function GetPartyDanger(aAgentArray, aParty)
    -- Note: This function is not directly equivalent to the GwA2 function,
    -- as Py4GW does not provide a direct equivalent. You may need to modify
    -- this function to suit your needs or use a different approach.
    return nil
end

function GetAgentDanger(aAgent, aAgentArray)
    -- Note: This function is not directly equivalent to the GwA2 function,
    -- as Py4GW does not provide a direct equivalent. You may need to modify
    -- this function to suit your needs or use a different approach.
    return nil
end

-- Living, Movable, Static Functions
function GetIsLiving(aAgent)
    return CoreLib.Agent.IsLiving(aAgent)
end

function GetIsMovable(aAgent)
    -- Note: This function is not directly equivalent to the GwA2 function,
    -- as Py4GW does not provide a direct equivalent. You may need to modify
    -- this function to suit your needs or use a different approach.
    return not CoreLib.Agent.IsItem(aAgent) and not CoreLib.Agent.IsGadget(aAgent)
end

function GetIsStatic(aAgent)
    -- Note: This function is not directly equivalent to the GwA2 function,
    -- as Py4GW does not provide a direct equivalent. You may need to modify
    -- this function to suit your needs or use a different approach.
    return CoreLib.Agent.IsItem(aAgent) or CoreLib.Agent.IsGadget(aAgent)
end

-- Get Primary Profession
function GetPrimaryProfession(agentId)
    local professions = CoreLib.Agent.GetProfessions(agentId or -2)
    return professions[1]
end

-- Get Secondary Profession
function GetSecondaryProfession(agentId)
    local professions = CoreLib.Agent.GetProfessions(agentId or -2)
    return professions[2]
end

-- Get Hero Profession
function GetHeroProfession(heroNumber, secondary)
    local heroes = CoreLib.Party.GetHeroes()
    local hero = heroes[heroNumber]
    if not hero then return nil end
    
    local professions = CoreLib.Agent.GetProfessions(hero.agentId)
    return professions and professions[secondary and 2 or 1]
end

-- Get Level
function GetLevel(agentId)
    return CoreLib.Agent.GetLevel(agentId or -2)
end

-- Get Team
function GetTeam(agentId)
    -- Note: This function is not directly equivalent to the GwA2 function,
    -- as Py4GW does not provide a direct equivalent. You may need to modify
    -- this function to suit your needs or use a different approach.
    return nil
end

-- Get Energy Pips
function GetEnergyPips(agentId)
    local energy = CoreLib.Agent.GetEnergy(agentId or -2)
    local maxEnergy = CoreLib.Agent.GetMaxEnergy(agentId or -2)
    return math.floor(energy / maxEnergy * 10)
end

-- Get Energy
function GetEnergy(agentId)
    return CoreLib.Agent.GetEnergy(agentId or -2)
end

-- Get Energy Requirement
function GetEnergyRequirement(skillId)
    return CoreLib.Skill.GetEnergyCost(skillId)
end

-- Get Health
function GetHealth(agentId)
    return CoreLib.Agent.GetHealth(agentId or -2)
end

-- Get HP
function GetHP(agentId)
    return CoreLib.Agent.GetHealth(agentId or -2)
end

-- Get Party Health
function GetPartyHealth()
    -- Note: This function is not directly equivalent to the GwA2 function,
    -- as Py4GW does not provide a direct equivalent. You may need to modify
    -- this function to suit your needs or use a different approach.
    return nil
end

-- Get Is Rubberbanding
function GetIsRubberbanding(agentId, time, ptr)
    -- Note: This function is not directly equivalent to the GwA2 function,
    -- as Py4GW does not provide a direct equivalent. You may need to modify
    -- this function to suit your needs or use a different approach.
    return nil
end

-- Get Moving
function GetMoving(agentId)
    return CoreLib.Agent.IsMoving(agentId)
end

-- Get Is Moving
function GetIsMoving(agentId)
    return CoreLib.Agent.IsMoving(agentId or -2)
end

-- Get Is Knocked
function GetIsKnocked(agentId)
    return CoreLib.Agent.IsNockedDown(agentId or -2)
end

-- Get Is Attacking
function GetIsAttacking(agentId)
    return CoreLib.Agent.IsAttacking(agentId)
end

-- Get Is Casting
function GetIsCasting(agentId)
    return CoreLib.Agent.IsCasting(agentId)
end

-- Get Is Bleeding
function GetIsBleeding(agentId)
    return CoreLib.Agent.IsBleeding(agentId)
end

-- Get Has Condition
function GetHasCondition(agentId)
    return CoreLib.Agent.IsConditioned(agentId)
end

-- Get Is Dead
function GetIsDead(agentId)
    return CoreLib.Agent.IsDead(agentId or -2)
end

-- Get Is Crippled
function GetIsCrippled(heroNumber)
    if heroNumber == 0 then
        return CoreLib.Agent.IsCrippled(-2)
    end
    local heroes = CoreLib.Party.GetHeroes()
    return heroes[heroNumber] and CoreLib.Agent.IsCrippled(heroes[heroNumber].agentId)
end

-- Get Has Deep Wound
function GetHasDeepWound(agentId)
    return CoreLib.Agent.IsDeepWounded(agentId)
end

-- Get Is Poisoned
function GetIsPoisoned(agentId)
    return CoreLib.Agent.IsPoisoned(agentId)
end

-- Get Is Enchanted
function GetIsEnchanted(agentId)
    return CoreLib.Agent.IsEnchanted(agentId)
end

-- Get Has Degen Hex
function GetHasDegenHex(agentId)
    return CoreLib.Agent.IsDegenHexed(agentId)
end

-- Get Has Hex
function GetHasHex(agentId)
    return CoreLib.Agent.IsHexed(agentId)
end

-- Get Has Weapon Spell
function GetHasWeaponSpell(agentId)
    return CoreLib.Agent.IsWeaponSpelled(agentId)
end

-- Get Is Boss
function GetIsBoss(agentId)
    return CoreLib.Agent.HasBossGlow(agentId)
end

-- Get Agent Model ID
function GetAgentModelId(agentId)
    return CoreLib.Agent.GetModelID(agentId)
end

-- Get Is Burning
function GetIsBurning(heroNumber)
    -- Note: This function is not directly equivalent to the GwA2 function,
    -- as Py4GW does not provide a direct equivalent. You may need to modify
    -- this function to suit your needs or use a different approach.
    return nil
end

-- Get Weapon Type
function GetWeaponType(agentId)
    return CoreLib.Agent.GetWeaponType(agentId or -2)
end

-- Get Wields Martial Weapon
function GetWieldsMartialWeapon(agentId)
    return CoreLib.Agent.IsMartial(agentId or -2)
end

-- Get Offhand Item ID
function GetOffhandItemId(agentId)
    local extraData = CoreLib.Agent.GetWeaponExtraData(agentId)
    return extraData and extraData.offhandItemId
end

-- Get Skill ID
function GetSkillId(agentId)
    return CoreLib.Agent.GetCastingSkill(agentId)
end

-- Get Party Leader
function GetPartyLeader()
    return CoreLib.Party.GetPartyLeaderID()
end

-- Get My ID
function GetMyId()
    return CoreLib.Player.GetPlayerID()
end

-- Get Can Pick Up
function GetCanPickUp(agentId)
    -- Note: This function is not directly equivalent to the GwA2 function,
    -- as Py4GW does not provide a direct equivalent. You may need to modify
    -- this function to suit your needs or use a different approach.
    return nil
end

-- Get Assigned To Me
function GetAssignedToMe(agentId)
    return CoreLib.Player.GetOwnerID() == agentId
end

-- Get Max Agents
function GetMaxAgents()
    -- Note: This function is not directly equivalent to the GwA2 function,
    -- as Py4GW does not provide a direct equivalent. You may need to modify
    -- this function to suit your needs or use a different approach.
    return nil
end

-- Get Number Of Allies
function GetNumberOfAllies(range)
    local allies = CoreLib.Player.GetAllyArray()
    local count = 0
    for _, ally in ipairs(allies) do
        if CoreLib.Utils.Distance(ally.x, ally.y, ally.z) <= (range or 5000) then
            count = count + 1
        end
    end
    return count
end

-- Get Current Target
function GetCurrentTarget()
    return CoreLib.Player.GetTargetID()
end

-- Get Current Target ID
function GetCurrentTargetId()
    return CoreLib.Player.GetTargetID()
end

-- Get Number Of Foes In Range Of Agent
function GetNumberOfFoesInRangeOfAgent(agentId, range, playerNumber)
    local enemies = CoreLib.Player.GetEnemyArray()
    local count = 0
    for _, enemy in ipairs(enemies) do
        if CoreLib.Utils.Distance(agentId.x, agentId.y, agentId.z, enemy.x, enemy.y, enemy.z) <= (range or 1250) then
            count = count + 1
        end
    end
    return count
end

-- Get Count In Range Of Agent
function GetCountInRangeOfAgent(agentId, range, allegiance, type)
    local agents = CoreLib.Player.GetAgentArray()
    local count = 0
    for _, agent in ipairs(agents) do
        if CoreLib.Utils.Distance(agentId.x, agentId.y, agentId.z, agent.x, agent.y, agent.z) <= (range or 5000) then
            if allegiance == 3 and agent.isEnemy then
                count = count + 1
            elseif allegiance == 1 and agent.isAlly then
                count = count + 1
            elseif allegiance == 2 and agent.isNeutral then
                count = count + 1
            end
        end
    end
    return count
end

-- Get Number Of Enemies
function GetNumberOfEnemies(range)
    local enemies = CoreLib.Player.GetEnemyArray()
    local count = 0
    for _, enemy in ipairs(enemies) do
        if CoreLib.Utils.Distance(enemy.x, enemy.y, enemy.z) <= (range or 3000) then
            count = count + 1
        end
    end
    return count
end

-- Get Number Of Enemies Near Agent
function GetNumberOfEnemiesNearAgent(range, agentId)
    local enemies = CoreLib.Player.GetEnemyArray()
    local count = 0
    for _, enemy in ipairs(enemies) do
        if CoreLib.Utils.Distance(agentId.x, agentId.y, agentId.z, enemy.x, enemy.y, enemy.z) <= (range or 3000) then
            count = count + 1
        end
    end
    return count
end

-- Get Number Of Allies Near XY
function GetNumberOfAlliesNearXY(x, y, range, allegiance)
    local allies = CoreLib.Player.GetAllyArray()
    local count = 0
    for _, ally in ipairs(allies) do
        if CoreLib.Utils.Distance(x, y, ally.x, ally.y) <= (range or 3000) then
            if allegiance == 1 and ally.isAlly then
                count = count + 1
            end
        end
    end
    return count
end

-- Get Number Of Moving Enemies
function GetNumberOfMovingEnemies(agentId, range)
    local enemies = CoreLib.Player.GetEnemyArray()
    local count = 0
    for _, enemy in ipairs(enemies) do
        if CoreLib.Utils.Distance(agentId.x, agentId.y, agentId.z, enemy.x, enemy.y, enemy.z) <= (range or 3000) then
            if CoreLib.Agent.IsMoving(enemy.agentId) then
                count = count + 1
            end
        end
    end
    return count
end

-- Get Number Of Moving Enemies Near XY
function GetNumberOfMovingEnemiesNearXY(x, y, range)
    local enemies = CoreLib.Player.GetEnemyArray()
    local count = 0
    for _, enemy in ipairs(enemies) do
        if CoreLib.Utils.Distance(x, y, enemy.x, enemy.y) <= (range or 3000) then
            if CoreLib.Agent.IsMoving(enemy.agentId) then
                count = count + 1
            end
        end
    end
    return count
end

-- Get Number Of Dead Allies
function GetNumberOfDeadAllies(range)
    local allies = CoreLib.Player.GetAllyArray()
    local count = 0
    for _, ally in ipairs(allies) do
        if CoreLib.Utils.Distance(ally.x, ally.y, ally.z) <= (range or 5000) then
            if CoreLib.Agent.IsDead(ally.agentId) then
                count = count + 1
            end
        end
    end
    return count
end

-- Get Number Of Conditioned Allies
function GetNumberOfConditionedAllies(range)
    local allies = CoreLib.Player.GetAllyArray()
    local count = 0
    for _, ally in ipairs(allies) do
        if CoreLib.Utils.Distance(ally.x, ally.y, ally.z) <= (range or 5000) then
            if CoreLib.Agent.IsConditioned(ally.agentId) then
                count = count + 1
            end
        end
    end
    return count
end

-- Get Number Of Bleeding Allies
function GetNumberOfBleedingAllies(range)
    local allies = CoreLib.Player.GetAllyArray()
    local count = 0
    for _, ally in ipairs(allies) do
        if CoreLib.Utils.Distance(ally.x, ally.y, ally.z) <= (range or 5000) then
            if CoreLib.Agent.IsBleeding(ally.agentId) then
                count = count + 1
            end
        end
    end
    return count
end

-- Get Number Of Poisoned Allies
function GetNumberOfPoisonedAllies(range)
    local allies = CoreLib.Player.GetAllyArray()
    local count = 0
    for _, ally in ipairs(allies) do
        if CoreLib.Utils.Distance(ally.x, ally.y, ally.z) <= (range or 5000) then
            if CoreLib.Agent.IsPoisoned(ally.agentId) then
                count = count + 1
            end
        end
    end
    return count
end

-- Get Number Of Deep Wounded Allies
function GetNumberOfDeepWoundedAllies(range)
    local allies = CoreLib.Player.GetAllyArray()
    local count = 0
    for _, ally in ipairs(allies) do
        if CoreLib.Utils.Distance(ally.x, ally.y, ally.z) <= (range or 5000) then
            if CoreLib.Agent.IsDeepWounded(ally.agentId) then
                count = count + 1
            end
        end
    end
    return count
end

-- Get Number Of Crippled Heroes
function GetNumberOfCrippledHeroes(range)
    local heroes = CoreLib.Party.GetHeroes()
    local count = 0
    for _, hero in ipairs(heroes) do
        if CoreLib.Utils.Distance(hero.x, hero.y, hero.z) <= (range or 5000) then
            if CoreLib.Agent.IsCrippled(hero.agentId) then
                count = count + 1
            end
        end
    end
    return count
end

-- Get Number Of Burning Heroes
function GetNumberOfBurningHeroes(range)
    -- Note: This function is not directly equivalent to the GwA2 function,
    -- as Py4GW does not provide a direct equivalent. You may need to modify
    -- this function to suit your needs or use a different approach.
    return nil
end

-- Get Number Of Minion Allies
function GetNumberOfMinionAllies(range)
    local minions = CoreLib.Player.GetMinionArray()
    local count = 0
    for _, minion in ipairs(minions) do
        if CoreLib.Utils.Distance(minion.x, minion.y, minion.z) <= (range or 5000) then
            count = count + 1
        end
    end
    return count
end

-- Get My Minion Count
function GetMyMinionCount(range)
    local minions = CoreLib.Player.GetMinionArray()
    local count = 0
    for _, minion in ipairs(minions) do
        if CoreLib.Utils.Distance(minion.x, minion.y, minion.z) <= (range or 5000) then
            if CoreLib.Player.GetOwnerID() == minion.ownerId then
                count = count + 1
            end
        end
    end
    return count
end

-- Get Number Of Spirit Allies
function GetNumberOfSpiritAllies(range)
    local spirits = CoreLib.Player.GetSpiritPetArray()
    local count = 0
    for _, spirit in ipairs(spirits) do
        if CoreLib.Utils.Distance(spirit.x, spirit.y, spirit.z) <= (range or 5000) then
            count = count + 1
        end
    end
    return count
end

-- Get My Spirit Count
function GetMySpiritCount()
    local spirits = CoreLib.Player.GetSpiritPetArray()
    local count = 0
    for _, spirit in ipairs(spirits) do
        if CoreLib.Player.GetOwnerID() == spirit.ownerId then
            count = count + 1
        end
    end
    return count
end

-- Get My Spirit Count with Range
function GetMySpiritCountWithRange(range)
    local spirits = CoreLib.Player.GetSpiritPetArray()
    local count = 0
    for _, spirit in ipairs(spirits) do
        if CoreLib.Utils.Distance(spirit.x, spirit.y, spirit.z) <= (range or 5000) then
            if CoreLib.Player.GetOwnerID() == spirit.ownerId then
                count = count + 1
            end
        end
    end
    return count
end

-- Get Number Of Spirits
function GetNumberOfSpirits(range, offensive, defensive)
    local spirits = CoreLib.Player.GetSpiritPetArray()
    local count = 0
    for _, spirit in ipairs(spirits) do
        if CoreLib.Utils.Distance(spirit.x, spirit.y, spirit.z) <= (range or 5000) then
            if (offensive and spirit.isOffensive) or (defensive and spirit.isDefensive) then
                count = count + 1
            end
        end
    end
    return count
end

-- Get Number Of Bosses
function GetNumberOfBosses(range)
    local agents = CoreLib.Player.GetAgentArray()
    local count = 0
    for _, agent in ipairs(agents) do
        if CoreLib.Utils.Distance(agent.x, agent.y, agent.z) <= (range or 3000) then
            if CoreLib.Agent.HasBossGlow(agent.agentId) then
                count = count + 1
            end
        end
    end
    return count
end

-- Get Number Of Dead Bosses
function GetNumberOfDeadBosses(range)
    local agents = CoreLib.Player.GetAgentArray()
    local count = 0
    for _, agent in ipairs(agents) do
        if CoreLib.Utils.Distance(agent.x, agent.y, agent.z) <= (range or 3000) then
            if CoreLib.Agent.HasBossGlow(agent.agentId) and CoreLib.Agent.IsDead(agent.agentId) then
                count = count + 1
            end
        end
    end
    return count
end

-- Get Is Spirit Agent
function GetIsSpiritAgent(agentId)
    return CoreLib.Agent.IsSpirit(agentId)
end

-- Get Is Minion Agent
function GetIsMinionAgent(agentId)
    return CoreLib.Agent.IsMinion(agentId)
end

-- Add Hero
function AddHero(heroId)
    CoreLib.Party.AddHero(heroId)
end

-- Kick Hero
function KickHero(heroId)
    CoreLib.Party.KickHero(heroId)
end

-- Kick All Heroes
function KickAllHeroes()
    CoreLib.Party.KickAllHeroes()
end

-- Add Npc
function AddNpc(npcId)
    CoreLib.Party.AddHenchman(npcId)
end

-- Kick Npc
function KickNpc(npcId)
    CoreLib.Party.KickHenchman(npcId)
end

-- Invite Player
function InvitePlayer(playerName)
    CoreLib.Party.InvitePlayer(playerName)
end

-- Leave Group
function LeaveGroup(kickHeroes)
    CoreLib.Party.LeaveParty()
end

-- CancelHero
function CancelHero(heroNumber, x, y, aggression)
    CoreLib.Party.UnflagAllHeroes()
    CoreLib.Party.ClearPartyCommands()
    CoreLib.Party.FlagHero(heroNumber, x, y)
    CoreLib.Party.FlagAllHeroes(x, y)
    CoreLib.Party.SetHeroBehavior(heroNumber, aggression)
end

-- SwitchMode
function SwitchMode(mode)
    if mode == "hard" then
        CoreLib.Party.SetHardMode()
    elseif mode == "normal" then
        CoreLib.Party.SetNormalMode()
    end
end

-- Resign
function Resign(mapID, language, region)
    CoreLib.Player.SendChatCommand("resign")
    CoreLib.Player.ReturnToOutpost()
end

-- SkipCinematic
function SkipCinematic()
    if CoreLib.Map.IsInCinematic() then
        CoreLib.Map.SkipCinematic()
    end
end

-- GetPartySize
function GetPartySize()
    return CoreLib.Party.PartySize()
end

-- Move
function Move(x, y, random)
    CoreLib.Player.Move(x, y)
end

-- OpenChestByExtraType
function OpenChestByExtraType(extraType)
    CoreLib.Player.OpenLockedChest(use_key=False)
end

-- MoveTo
function MoveTo(x, y, random)
    CoreLib.Player.Routines.Movement.FollowXY.Move(x, y, tolerance=100)
end

-- GoPlayer
function GoPlayer(agent)
    CoreLib.Player.Interact(agent_id, call_target=False)
end

-- MoveIfHurt
function MoveIfHurt(me, threshold)
    CoreLib.Player.Routines.Movement.MoveIfHurt(threshold=threshold, FollowXY_Instance=None)
end

-- ComputeDistance
function ComputeDistance(x1, y1, x2, y2)
    return CoreLib.Utils.Distance({x=x1, y=y1}, {x=x2, y=y2})
end

-- UseSkill
function UseSkill(skillSlot, target, callTarget)
    CoreLib.Skillbar.UseSkill(skill_slot, target_agent_id=target)
end

-- LoadSkillBar
function LoadSkillBar(skill1, skill2, skill3, skill4, skill5, skill6, skill7, skill8, heroNumber)
    local skills = {skill1, skill2, skill3, skill4, skill5, skill6, skill7, skill8}
    for i, skill in ipairs(skills) do
        if skill ~= 0 then
            CoreLib.Skillbar.LoadSkillTemplate(skill, heroNumber)
        end
    end
end

-- LoadSkillTemplate
function LoadSkillTemplate(template, heroNumber)
    CoreLib.Skillbar.LoadSkillTemplate(template, heroNumber)
end

-- GetSkillByID
function GetSkillByID(skillID)
    return CoreLib.Skillbar.GetSkillData(skillID)
end

-- DropBuff
function DropBuff(skillID, agentID, heroNumber)
    CoreLib.Buffs.DropBuff(skillID)
end

-- HasEffect
function HasEffect(effectSkillID, heroNumber, heroId)
    return CoreLib.Buffs.BuffExists(heroId, effectSkillID)
end

-- GetBuffCount
function GetBuffCount(heroNumber)
    return CoreLib.Buffs.GetBuffCount(heroNumber)
end

-- GetIsTargetBuffed
function GetIsTargetBuffed(skillID, agentID, heroNumber)
    return CoreLib.Buffs.BuffExists(agentID, skillID)
end

-- TravelTo
function TravelTo(mapID, language, region)
    CoreLib.Map.Travel(mapID)
end

-- ReturnToOutpost
function ReturnToOutpost()
    CoreLib.Party.ReturnToOutpost()
end

-- EnterChallenge
function EnterChallenge()
    CoreLib.Map.EnterChallenge()
end

-- AcceptQuest
function AcceptQuest(questID)
    CoreLib.Player.SendChatCommand("dialog take")
end

-- EquipItem
function EquipItem(item)
    CoreLib.Inventory.EquipItem(item)
end

-- UseItem
function UseItem(item)
    CoreLib.Inventory.UseItem(item)
end

-- PickUpItem
function PickUpItem(item)
    CoreLib.Inventory.PickUpItem(item)
end

-- DropItem
function DropItem(item, amount)
    CoreLib.Inventory.DropItem(item, amount)
end

-- MoveItem
function MoveItem(item, bag, slot, quantity)
    CoreLib.Inventory.MoveItem(item, bag, slot, quantity)
end

-- DropGold
function DropGold(amount)
    CoreLib.Inventory.DropGold(amount)
end

-- DepositGold
function DepositGold(amount)
    CoreLib.Inventory.DepositGold(amount)
end

-- WithdrawGold
function WithdrawGold(amount)
    CoreLib.Inventory.WithdrawGold(amount)
end

-- DestroyItem
function DestroyItem(item, amount)
    CoreLib.Inventory.DestroyItem(item, amount)
end

-- GetItemIDfromModelID
function GetItemIDfromModelID(modelID)
    return CoreLib.Inventory.GetItemIdFromModelID(modelID)
end

-- GetBagNumberByItemID
function GetBagNumberByItemID(itemID)
    return CoreLib.Inventory.GetBagNumberByItemID(itemID)
end

-- GetRarity
function GetRarity(item)
    return CoreLib.Inventory.Item.GetRarity(item)
end

-- GetItemValue
function GetItemValue(item)
    return CoreLib.Inventory.Item.GetValue(item)
end

-- GetQuantity
function GetQuantity(item)
    return CoreLib.Inventory.Item.GetQuantity(item)
end

return {
    GetCharname = GetCharname,
    DisplayAllies = DisplayAllies,
    DisplayEnemies = DisplayEnemies,
    GetPlayerName = GetPlayerName,
    GetPartyPlayerNames = GetPartyPlayerNames,
    GetPartyLeaderName = GetPartyLeaderName,
    GetAgentName = GetAgentName,
    GetInstanceUpTime = GetInstanceUpTime,
    GetMapID = GetMapID,
    GetMapLoading = GetMapLoading,
    GetMapIsLoaded = GetMapIsLoaded,
    GetDistrict = GetDistrict,
    GetRegion = GetRegion,
    WaitMapLoading = WaitMapLoading,
    GetInstanceTimestamp = GetInstanceTimestamp,
    WaitForLoad = WaitForLoad,
    GetAreaVanquished = GetAreaVanquished,
    GetFoesKilled = GetFoesKilled,
    GetFoesToKill = GetFoesToKill,
    GetPing = GetPing,
    WriteChat = WriteChat,
    SendWhisper = SendWhisper,
    GetAgentByID = GetAgentByID,
    GetID = GetID,
    GetX = GetX,
    GetY = GetY,
    GetXY = GetXY,
    GetMoveX = GetMoveX,
    GetMoveY = GetMoveY,
    GetTarget = GetTarget,
    ChangeTarget = ChangeTarget,
    GetBestTarget = GetBestTarget,
    GetBestMeleeTarget = GetBestMeleeTarget,
    GetNearestAllyToAgent = GetNearestAllyToAgent,
    GetNearestMinionAllyToAgent = GetNearestMinionAllyToAgent,
    GetNearestNPCPtrToAgent = GetNearestNPCPtrToAgent,
    GetNearestItemToAgent = GetNearestItemToAgent,
    GetNearestSignpostToAgent = GetNearestSignpostToAgent,
    GetNearestNPCToAgent = GetNearestNPCToAgent,
    GetNearestEnemyToAgent = GetNearestEnemyToAgent,
    GetClosestInRangeOfAgent = GetClosestInRangeOfAgent,
    GetNearestAgentToAgent = GetNearestAgentToAgent,
    GetNearestAgentToCoords = GetNearestAgentToCoords,
    GetNumberOfEnemiesNearXY = GetNumberOfEnemiesNearXY,
    GetAgentByPlayerNumber = GetAgentByPlayerNumber,
    GetAgentDistanceByPlayerNumber = GetAgentDistanceByPlayerNumber,
    GetParty = GetParty,
    GetMaxPartySize = GetMaxPartySize,
    GetAgentArray = GetAgentArray,
    GetPartyDanger = GetPartyDanger,
    GetAgentDanger = GetAgentDanger,
    GetIsLiving = GetIsLiving,
    GetIsMovable = GetIsMovable,
    GetIsStatic = GetIsStatic,
    GetPrimaryProfession = GetPrimaryProfession,
    GetSecondaryProfession = GetSecondaryProfession,
    GetHeroProfession = GetHeroProfession,
    GetLevel = GetLevel,
    GetTeam = GetTeam,
    GetEnergyPips = GetEnergyPips,
    GetEnergy = GetEnergy,
    GetEnergyRequirement = GetEnergyRequirement,
    GetHealth = GetHealth,
    GetHP = GetHP,
    GetPartyHealth = GetPartyHealth,
    GetIsRubberbanding = GetIsRubberbanding,
    GetMoving = GetMoving,
    GetIsMoving = GetIsMoving,
    GetIsKnocked = GetIsKnocked,
    GetIsAttacking = GetIsAttacking,
    GetIsCasting = GetIsCasting,
    GetIsBleeding = GetIsBleeding,
    GetHasCondition = GetHasCondition,
    GetIsDead = GetIsDead,
    GetIsCrippled = GetIsCrippled,
    GetHasDeepWound = GetHasDeepWound,
    GetIsPoisoned = GetIsPoisoned,
    GetIsEnchanted = GetIsEnchanted,
    GetHasDegenHex = GetHasDegenHex,
    GetHasHex = GetHasHex,
    GetHasWeaponSpell = GetHasWeaponSpell,
    GetIsBoss = GetIsBoss,
    GetAgentModelId = GetAgentModelId,
    GetIsBurning = GetIsBurning,
    GetWeaponType = GetWeaponType,
    GetWieldsMartialWeapon = GetWieldsMartialWeapon,
    GetOffhandItemId = GetOffhandItemId,
    GetSkillId = GetSkillId,
    GetPartyLeader = GetPartyLeader,
    GetMyId = GetMyId,
    GetCanPickUp = GetCanPickUp,
    GetAssignedToMe = GetAssignedToMe,
    GetMaxAgents = GetMaxAgents,
    GetNumberOfAllies = GetNumberOfAllies,
    GetCurrentTarget = GetCurrentTarget,
    GetCurrentTargetId = GetCurrentTargetId,
    GetNumberOfFoesInRangeOfAgent = GetNumberOfFoesInRangeOfAgent,
    GetCountInRangeOfAgent = GetCountInRangeOfAgent,
    GetNumberOfEnemies = GetNumberOfEnemies,
    GetNumberOfEnemiesNearAgent = GetNumberOfEnemiesNearAgent,
    GetNumberOfAlliesNearXY = GetNumberOfAlliesNearXY,
    GetNumberOfMovingEnemies = GetNumberOfMovingEnemies,
    GetNumberOfMovingEnemiesNearXY = GetNumberOfMovingEnemiesNearXY,
    GetNumberOfDeadAllies = GetNumberOfDeadAllies,
    GetNumberOfConditionedAllies = GetNumberOfConditionedAllies,
    GetNumberOfBleedingAllies = GetNumberOfBleedingAllies,
    GetNumberOfPoisonedAllies = GetNumberOfPoisonedAllies,
    GetNumberOfDeepWoundedAllies = GetNumberOfDeepWoundedAllies,
    GetNumberOfCrippledHeroes = GetNumberOfCrippledHeroes,
    GetNumberOfBurningHeroes = GetNumberOfBurningHeroes,
    GetNumberOfMinionAllies = GetNumberOfMinionAllies,
    GetMyMinionCount = GetMyMinionCount,
    GetNumberOfSpiritAllies = GetNumberOfSpiritAllies,
    GetMySpiritCount = GetMySpiritCount,
    GetMySpiritCountWithRange = GetMySpiritCountWithRange,
    GetNumberOfSpirits = GetNumberOfSpirits,
    GetNumberOfBosses = GetNumberOfBosses,
    GetNumberOfDeadBosses = GetNumberOfDeadBosses,
    GetIsSpiritAgent = GetIsSpiritAgent,
    GetIsMinionAgent = GetIsMinionAgent,
    AddHero = AddHero,
    KickHero = KickHero,
    KickAllHeroes = KickAllHeroes,
    AddNpc = AddNpc,
    KickNpc = KickNpc,
    InvitePlayer = InvitePlayer,
    LeaveGroup = LeaveGroup,
    CancelHero = CancelHero,
    SwitchMode = SwitchMode,
    Resign = Resign,
    SkipCinematic = SkipCinematic,
    GetPartySize = GetPartySize,
    Move = Move,
    OpenChestByExtraType = OpenChestByExtraType,
    MoveTo = MoveTo,
    GoPlayer = GoPlayer,
    MoveIfHurt = MoveIfHurt,
    ComputeDistance = ComputeDistance,
    UseSkill = UseSkill,
    LoadSkillBar = LoadSkillBar,
    LoadSkillTemplate = LoadSkillTemplate,
    GetSkillByID = GetSkillByID,
    DropBuff = DropBuff,
    GetBuffCount = GetBuffCount,
    GetIsTargetBuffed = GetIsTargetBuffed,
    TravelTo = TravelTo,
    ReturnToOutpost = ReturnToOutpost,
    EnterChallenge = EnterChallenge,
    AcceptQuest = AcceptQuest,
    EquipItem = EquipItem,
    UseItem = UseItem,
    PickUpItem = PickUpItem,
    DropItem = DropItem,
    MoveItem = MoveItem,
    DropGold = DropGold,
    DepositGold = DepositGold,
    WithdrawGold = WithdrawGold,
    DestroyItem = DestroyItem,
    GetItemIDfromModelID = GetItemIDfromModelID,
    GetBagNumberByItemID = GetBagNumberByItemID,
    GetRarity = GetRarity,
    GetItemValue = GetItemValue,
    GetQuantity = GetQuantity,
}
