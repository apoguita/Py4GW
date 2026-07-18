local Agent = {}

function Agent.agent_instance(agent_id)
    return PyAgent.PyAgent(agent_id)
end

function Agent.GetIdFromAgent(agent_instance)
    return agent_instance.id
end

function Agent.GetAgentByID(agent_id)
    return Agent.agent_instance(agent_id)
end

function Agent.GetAttributes(agent_id)
    local agent_instance = Agent.agent_instance(agent_id)
    return agent_instance.attributes
end

function Agent.GetNPCSkillbar(agent_id)
    local agent_instance = Agent.agent_instance(agent_id)
    return agent_instance.npc_skillbar
end

function Agent.GetModelID(agent_id)
    local agent_instance = Agent.agent_instance(agent_id)
    return agent_instance.model_id
end

function Agent.IsLiving(agent_id)
    local agent_instance = Agent.agent_instance(agent_id)
    return agent_instance.is_living
end

function Agent.IsItem(agent_id)
    local agent_instance = Agent.agent_instance(agent_id)
    return agent_instance.is_item
end

function Agent.IsGadget(agent_id)
    local agent_instance = Agent.agent_instance(agent_id)
    return agent_instance.is_gadget
end

function Agent.GetPlayerNumber(agent_id)
    local agent_instance = Agent.agent_instance(agent_id)
    return agent_instance.living_agent.player_number
end

function Agent.GetLoginNumber(agent_id)
    local agent_instance = Agent.agent_instance(agent_id)
    return agent_instance.living_agent.login_number
end

function Agent.IsSpirit(agent_id)
    local agent_instance = Agent.agent_instance(agent_id)
    return agent_instance.living_agent.allegiance.GetName() == "Spirit/Pet"
end

function Agent.IsMinion(agent_id)
    local agent_instance = Agent.agent_instance(agent_id)
    return agent_instance.living_agent.allegiance.GetName() == "Minion"
end

function Agent.GetOwnerID(agent_id)
    local agent_instance = Agent.agent_instance(agent_id)
    return agent_instance.living_agent.owner_id
end

function Agent.GetXY(agent_id)
    local agent_instance = Agent.agent_instance(agent_id)
    return agent_instance.x, agent_instance.y
end

function Agent.GetXYZ(agent_id)
    local agent_instance = Agent.agent_instance(agent_id)
    return agent_instance.x, agent_instance.y, agent_instance.z
end

function Agent.GetZPlane(agent_id)
    local agent_instance = Agent.agent_instance(agent_id)
    return agent_instance.zplane
end

function Agent.GetRotationAngle(agent_id)
    local agent_instance = Agent.agent_instance(agent_id)
    return agent_instance.rotation_angle
end

function Agent.GetRotationCos(agent_id)
    local agent_instance = Agent.agent_instance(agent_id)
    return agent_instance.rotation_cos
end

function Agent.GetRotationSin(agent_id)
    local agent_instance = Agent.agent_instance(agent_id)
    return agent_instance.rotation_sin
end

function Agent.GetVelocityXY(agent_id)
    local agent_instance = Agent.agent_instance(agent_id)
    return agent_instance.velocity_x, agent_instance.velocity_y
end

function Agent.GetName(agent_id)
    local agent_instance = Agent.agent_instance(agent_id)
    return agent_instance.living_agent.name
end

function Agent.GetProfessions(agent_id)
    local agent_instance = Agent.agent_instance(agent_id)
    return agent_instance.living_agent.profession, agent_instance.living_agent.secondary_profession
end

function Agent.GetProfessionNames(agent_id)
    local agent_instance = Agent.agent_instance(agent_id)
    return agent_instance.living_agent.profession.GetName(), agent_instance.living_agent.secondary_profession.GetName()
end

function Agent.GetProfessionShortNames(agent_id)
    local agent_instance = Agent.agent_instance(agent_id)
    return agent_instance.living_agent.profession.GetShortName(), agent_instance.living_agent.secondary_profession.GetShortName()
end

function Agent.GetProfessionIDs(agent_id)
    local agent_instance = Agent.agent_instance(agent_id)
    return agent_instance.living_agent.profession.ToInt(), agent_instance.living_agent.secondary_profession.ToInt()
end

function Agent.GetLevel(agent_id)
    local agent_instance = Agent.agent_instance(agent_id)
    return agent_instance.living_agent.level
end

function Agent.GetEnergy(agent_id)
    local agent_instance = Agent.agent_instance(agent_id)
    return agent_instance.living_agent.energy
end

function Agent.GetMaxEnergy(agent_id)
    local agent_instance = Agent.agent_instance(agent_id)
    return agent_instance.living_agent.max_energy
end

function Agent.GetEnergyRegen(agent_id)
    local agent_instance = Agent.agent_instance(agent_id)
    return agent_instance.living_agent.energy_regen
end

function Agent.GetHealth(agent_id)
    local agent_instance = Agent.agent_instance(agent_id)
    return agent_instance.living_agent.hp
end

function Agent.GetMaxHealth(agent_id)
    local agent_instance = Agent.agent_instance(agent_id)
    return agent_instance.living_agent.max_hp
end

function Agent.GetHealthRegen(agent_id)
    local agent_instance = Agent.agent_instance(agent_id)
    return agent_instance.living_agent.hp_regen
end

function Agent.IsMoving(agent_id)
    local agent_instance = Agent.agent_instance(agent_id)
    return agent_instance.living_agent.is_moving
end

function Agent.IsKnockedDown(agent_id)
    local agent_instance = Agent.agent_instance(agent_id)
    return agent_instance.living_agent.is_knocked_down
end

function Agent.IsBleeding(agent_id)
    local agent_instance = Agent.agent_instance(agent_id)
    return agent_instance.living_agent.is_bleeding
end

function Agent.IsCrippled(agent_id)
    local agent_instance = Agent.agent_instance(agent_id)
    return agent_instance.living_agent.is_crippled
end

function Agent.IsDeepWounded(agent_id)
    local agent_instance = Agent.agent_instance(agent_id)
    return agent_instance.living_agent.is_deep_wounded
end

function Agent.IsPoisoned(agent_id)
    local agent_instance = Agent.agent_instance(agent_id)
    return agent_instance.living_agent.is_poisoned
end

function Agent.IsConditioned(agent_id)
    local agent_instance = Agent.agent_instance(agent_id)
    return agent_instance.living_agent.is_conditioned
end

function Agent.IsEnchanted(agent_id)
    local agent_instance = Agent.agent_instance(agent_id)
    return agent_instance.living_agent.is_enchanted
end

function Agent.IsHexed(agent_id)
    local agent_instance = Agent.agent_instance(agent_id)
    return agent_instance.living_agent.is_hexed
end

function Agent.IsDegenHexed(agent_id)
    local agent_instance = Agent.agent_instance(agent_id)
    return agent_instance.living_agent.is_degen_hexed
end

function Agent.IsDead(agent_id)
    local agent_instance = Agent.agent_instance(agent_id)
    return agent_instance.living_agent.is_dead
end

function Agent.IsAlive(agent_id)
    local agent_instance = Agent.agent_instance(agent_id)
    return not Agent.IsDead(agent_id)
end

function Agent.IsWeaponSpelled(agent_id)
    local agent_instance = Agent.agent_instance(agent_id)
    return agent_instance.living_agent.is_weapon_spelled
end

function Agent.IsInCombatStance(agent_id)
    local agent_instance = Agent.agent_instance(agent_id)
    return agent_instance.living_agent.in_combat_stance
end

function Agent.IsAttacking(agent_id)
    local agent_instance = Agent.agent_instance(agent_id)
    return agent_instance.living_agent.is_attacking
end

function Agent.IsCasting(agent_id)
    local agent_instance = Agent.agent_instance(agent_id)
    return agent_instance.living_agent.is_casting
end

function Agent.IsIdle(agent_id)
    local agent_instance = Agent.agent_instance(agent_id)
    return agent_instance.living_agent.is_idle
end

function Agent.HasBossGlow(agent_id)
    local agent_instance = Agent.agent_instance(agent_id)
    return agent_instance.living_agent.has_boss_glow
end

function Agent.GetWeaponType(agent_id)
    local agent_instance = Agent.agent_instance(agent_id)
    return agent_instance.living_agent.weapon_type.ToInt(), agent_instance.living_agent.weapon_type.GetName()
end

function Agent.GetWeaponExtraData(agent_id)
    local agent_instance = Agent.agent_instance(agent_id)
    return agent_instance.living_agent.weapon_item_id, agent_instance.living_agent.weapon_item_type, agent_instance.living_agent.offhand_item_id, agent_instance.living_agent.offhand_item_type
end

function Agent.IsMartial(agent_id)
    local agent_instance = Agent.agent_instance(agent_id)
    local martial_weapon_types = {"Bow", "Axe", "Hammer", "Daggers", "Scythe", "Spear", "Sword"}
    return agent_instance.living_agent.weapon_type.GetName() in martial_weapon_types
end

function Agent.IsCaster(agent_id)
    local agent_instance = Agent.agent_instance(agent_id)
    return not Agent.IsMartial(agent_id)
end

function Agent.IsMelee(agent_id)
    local agent_instance = Agent.agent_instance(agent_id)
    local melee_weapon_types = {"Axe", "Hammer", "Daggers", "Scythe", "Sword"}
    return agent_instance.living_agent.weapon_type.GetName() in melee_weapon_types
end

function Agent.IsRanged(agent_id)
    local agent_instance = Agent.agent_instance(agent_id)
    return not Agent.IsMelee(agent_id)
end

function Agent.GetCastingSkill(agent_id)
    local agent_instance = Agent.agent_instance(agent_id)
    return agent_instance.living_agent.casting_skill_id
end

function Agent.GetDaggerStatus(agent_id)
    local agent_instance = Agent.agent_instance(agent_id)
    return agent_instance.living_agent.dagger_status
end

function Agent.GetAllegiance(agent_id)
    local agent_instance = Agent.agent_instance(agent_id)
    return agent_instance.living_agent.allegiance.ToInt(), agent_instance.living_agent.allegiance.GetName()
end

function Agent.IsPlayer(agent_id)
    local agent_instance = Agent.agent_instance(agent_id)
    return agent_instance.living_agent.is_player
end

function Agent.IsNPC(agent_id)
    local agent_instance = Agent.agent_instance(agent_id)
    return agent_instance.living_agent.is_npc
end

function Agent.HasQuest(agent_id)
    local agent_instance = Agent.agent_instance(agent_id)
    return agent_instance.living_agent.has_quest
end

function Agent.IsDeadByTypeMap(agent_id)
    local agent_instance = Agent.agent_instance(agent_id)
    return agent_instance.living_agent.is_dead_by_typemap
end

function Agent.IsFemale(agent_id)
    local agent_instance = Agent.agent_instance(agent_id)
    return agent_instance.living_agent.is_female
end

function Agent.IsHidingCape(agent_id)
    local agent_instance = Agent.agent_instance(agent_id)
    return agent_instance.living_agent.is_hiding_cape
end

function Agent.CanBeViewedInPartyWindow(agent_id)
    local agent_instance = Agent.agent_instance(agent_id)
    return agent_instance.living_agent.can_be_viewed_in_party_window
end

function Agent.IsSpawned(agent_id)
    local agent_instance = Agent.agent_instance(agent_id)
    return agent_instance.living_agent.is_spawned
end

function Agent.IsBeingObserved(agent_id)
    local agent_instance = Agent.agent_instance(agent_id)
    return agent_instance.living_agent.is_being_observed
end

function Agent.GetOvercast(agent_id)
    local agent_instance = Agent.agent_instance(agent_id)
    return agent_instance.living_agent.overcast
end

function Agent.GetItemAgent(agent_id)
    local agent_instance = Agent.agent_instance(agent_id)
    return agent_instance.item_agent
end

function Agent.GetGadgetAgent(agent_id)
    local agent_instance = Agent.agent_instance(agent_id)
    return agent_instance.gadget_agent
end

function Agent.GetGadgetID(agent_id)
    local gadget_agent = Agent.GetGadgetAgent(agent_id)
    return gadget_agent.gadget_id
end

return Agent
