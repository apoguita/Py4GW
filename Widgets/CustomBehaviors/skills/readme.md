# `sequence_utility`
- is basically a sequence of casting of 2 skills
- both `skills.evaluate` must be > 0 for the sequence to be evaluated.
- skills must be declared as stub. and fully managed of the `sequence_utility`.
- example :
    - `intensity` > `invoke_lightning` (`invoke_lightning` can't be casted without `intensity`.)
    - `deadly_paradox` > `shadow_form` (`shadow_form` can't be casted without `deadly_paradox`.)
- we try to limit such usage as much as possible as it's complexify logic.

# `preparation_utility`
- simpler version than sequence, the preparation is made to verify a skill can be casted based on the fact another one is ready to be executed.
- example :
   - `intensity` > `shell_shock` or `chain_lightning`, but `shell_shock` and `chain_lightning` remain castable on their own.
   - `symbolic_celerity` > `keystone_signet`, but `keystone_signet` can be casted on its own (for a refresh for instance.)

# simply priority
- sometimes we might want to enforce a condition that another skill has prepared. such as `deep_wound`.
- When there is no way to target it (we add an external tracker.) such as `cracked_armor` or `glimmering_mark`.
- example :
    - `shell_shock` > `shock_arrow`
- should be prioritized as much as possible
- other examples : 
    - `symbolic_posture` > `keystone_signet` (it is not a sequence or a preparation. as symbolic posture is a buff we can easily check it from `keystone_signet`).

# `arcane_echo_utility`
- is not done through a sequence, but rather it's own utility skill.
- basically you put `original_skill_to_copy` & `new_copied_instance` and `arcane_echo` will manage to orchestrate everything.
- it looks like a sequence but it's not. as we are not orchestrating the `original_skill_to_copy`. we are just using it when `arcane_echo` is ready.



# events
- sometimes we want to be open to multiple skills. so we can react to an event.
- example :
    - cast a spirit triggers `SPIRIT_CREATED` that can be consumed by any other skills.
    - when we run multiple ritualists in the group, we can rely on `Agent.GetXx` ;
    - `Summon_Spirit`, `Spirit_Transfer`, `Armor_of_unfeeling`, etc... would be interested to know what are the spirits we own.
- main usage is for daemon events rather than combat skills

# shared locks
- when we want to coordinate skills between multiple accounts. we use `shared_locking`.
- example :
    - interrupt, resurrection, hexes, conditions, condition cleanse, etc... benefit from a shared lock.
- we basically lock on a key that is `[OPERATION_NAME]_[AGENT_ID]` with a method `_get_lock_key(self, agent_id: int)`
    - `ByUralsHammer`
    - `GenericResurrection_{agent_id}`
    - `ShellShock_{agent_id}`
    - `EbonVanguardAssassinSupport_{agent_id}` (to avoid spamming the same target)
    - `Shatter_Hex_{agent_id}`
    - `Interrupt_{agent_id}`
- it is useless for skills that are simply doing damages

