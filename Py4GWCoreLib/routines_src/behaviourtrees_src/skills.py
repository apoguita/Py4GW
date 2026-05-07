"""
BT routines file notes
======================

This file is both:
- part of the public BT grouped routine surface
- a discovery source for higher-level tooling

Authoring and discovery conventions
-----------------------------------
- Keep existing class names as the system-level grouping surface.
- Use `PascalCase` for public/front-facing routine methods.
- Use `snake_case` for helper/internal methods.
- Use `_snake_case` for explicitly private helpers.
- Keep helper/internal methods out of the public discovery surface.

Routine docstring template
--------------------------
Each user-facing routine method should use:
- a free human-readable description first
- a structured `Meta:` block after it

Template:

    \"\"\"
    One or more human-readable paragraphs explaining what the routine builds.

    Meta:
      Expose: true
      Audience: beginner
      Display: Cast Skill ID
      Purpose: Build a tree that performs a skill-related routine.
      UserDescription: Use this when you want to cast or validate skills from a tree.
      Notes: Keep metadata single-line. Structural truth should stay in code.
    \"\"\"

Docstring parsing rules
-----------------------
- Only the `Meta:` section is intended for machine parsing.
- Keep metadata lines single-line and in `Key: Value` form.
- Unknown keys should be safe for tooling to ignore.
- Prefer adding presentation/help metadata in docstrings instead of duplicating
  structural metadata that already exists in code.
"""

from __future__ import annotations

import importlib
from collections.abc import Mapping
from collections.abc import Sequence

from ...Agent import Agent
from ...GlobalCache import GLOBAL_CACHE
from ...Player import Player
from ...Py4GWcorelib import ConsoleLog, Console
from ...py4gwcorelib_src.BehaviorTree import BehaviorTree
from ..Checks import Checks


def _log(source: str, message: str, *, log: bool = False, message_type=Console.MessageType.Info) -> None:
    ConsoleLog(source, message, message_type, log=log)


def _fail_log(source: str, message: str, message_type=Console.MessageType.Warning) -> None:
    ConsoleLog(source, message, message_type, log=True)


class _RProxy:
    """
    Internal proxy that resolves the `Routines` root package lazily for BT skill helpers.

    Meta:
      Expose: false
      Audience: advanced
      Display: Internal Routines Proxy
      Purpose: Provide lazy access to the root routines package from the BT skills module.
      UserDescription: Internal support helper class.
      Notes: This proxy is wiring support only and is not part of the public BT helper catalog.
    """
    def __getattr__(self, name: str):
        """
        Resolve a routine attribute from the root package on demand.

        Meta:
          Expose: false
          Audience: advanced
          Display: Internal Routines Proxy Get Attribute
          Purpose: Lazily fetch a named routine attribute from the root package.
          UserDescription: Internal support routine.
          Notes: This keeps BT skill helpers loosely coupled to the root package and should not be discovered directly.
        """
        root_pkg = importlib.import_module("Py4GWCoreLib")
        return getattr(root_pkg.Routines, name)


Routines = _RProxy()


class BTSkills:
    """
    Public BT helper group for skillbar loading, casting, and skill usability checks.

    Meta:
      Expose: true
      Audience: advanced
      Display: Skills
      Purpose: Group public BT routines related to loading skillbars, casting skills, and validating skill usage.
      UserDescription: Built-in BT helper group for skillbar and skill-use routines.
      Notes: Public `PascalCase` methods in this class are discovery candidates when marked exposed.
    """
    @staticmethod
    def LoadSkillbar(template:str, log:bool=False):
        """
        Build a tree that loads a player skillbar template.

        Meta:
          Expose: true
          Audience: beginner
          Display: Load Skillbar
          Purpose: Load a player skillbar from a template string.
          UserDescription: Use this when you want to swap the player skillbar to a known template.
          Notes: Calls the global skillbar loader and completes after a short aftercast delay.
        """
        def _load_skillbar(template:str):
            """
            Issue the low-level skillbar load request.

            Meta:
              Expose: false
              Audience: advanced
              Display: Internal Load Skillbar Helper
              Purpose: Trigger the global skillbar loader for the provided template string.
              UserDescription: Internal support routine.
              Notes: Returns success immediately after dispatching the load request.
            """
            GLOBAL_CACHE.SkillBar.LoadSkillTemplate(template)
            if not template:
                _fail_log("LoadSkillbar", "Failed to load skillbar: template is empty.")
                return BehaviorTree.NodeState.FAILURE
            _log("LoadSkillbar", "Loaded skillbar template.", log=log)
            return BehaviorTree.NodeState.SUCCESS
        
        tree = BehaviorTree.ActionNode(name="LoadSkillbar", action_fn=lambda: _load_skillbar(template), aftercast_ms=250)
        return BehaviorTree(tree)

    @staticmethod
    def LoadSkillbarFromMap(
        profession_level_skillbars: Mapping[str, Sequence[tuple[int | None, str]]],
        default_template: str = "",
        log: bool = False,
    ):
        """
        Build a tree that resolves a skillbar template from profession/level rules and loads it.

        Meta:
          Expose: true
          Audience: intermediate
          Display: Load Skillbar From Map
          Purpose: Select a player skillbar template automatically from a profession and level mapping.
          UserDescription: Use this when different professions or level bands should load different templates without local selection code.
          Notes: Each profession maps to ordered `(max_level_inclusive, template)` pairs. The first entry whose level is greater than or equal to the player's current level is selected. Use `None` for the final fallback pair. A `"default"` mapping key or `default_template` is used when no profession-specific entry matches.
        """
        state = {
            "template": "",
        }

        def _select_template() -> str:
            primary_profession, _ = Agent.GetProfessionNames(Player.GetAgentID())
            current_level = int(Agent.GetLevel(Player.GetAgentID()) or 0)

            candidates = profession_level_skillbars.get(primary_profession)
            if not candidates:
                candidates = profession_level_skillbars.get("default")
            if not candidates:
                return str(default_template or "")

            fallback_template = str(default_template or "")
            for max_level_inclusive, template in candidates:
                if max_level_inclusive is None:
                    fallback_template = str(template)
                    continue
                if current_level <= int(max_level_inclusive):
                    return str(template)

            return fallback_template

        def _resolve_template() -> BehaviorTree.NodeState:
            state["template"] = _select_template()
            return BehaviorTree.NodeState.SUCCESS if state["template"] else BehaviorTree.NodeState.FAILURE

        return BehaviorTree(
            BehaviorTree.SequenceNode(
                name="LoadSkillbarFromMap",
                children=[
                    BehaviorTree.ActionNode(
                        name="ResolveSkillbarTemplate",
                        action_fn=_resolve_template,
                        aftercast_ms=0,
                    ),
                    BehaviorTree.SubtreeNode(
                        name="LoadResolvedSkillbar",
                        subtree_fn=lambda _node: BTSkills.LoadSkillbar(state["template"], log=log),
                    ),
                ],
            )
        )
    
    @staticmethod
    def LoadHeroSkillbar(hero_index:int, template:str, log:bool=False):
        """
        Build a tree that loads a skillbar template for a hero slot.

        Meta:
          Expose: true
          Audience: beginner
          Display: Load Hero Skillbar
          Purpose: Load a hero skillbar from a template string.
          UserDescription: Use this when you want a specific hero to switch to a known skillbar template.
          Notes: Uses the provided hero index directly and completes after a short aftercast delay.
        """
        def _load_hero_skillbar(hero_index:int, template:str):
            """
            Issue the low-level hero skillbar load request.

            Meta:
              Expose: false
              Audience: advanced
              Display: Internal Load Hero Skillbar Helper
              Purpose: Trigger the global hero skillbar loader for the provided hero slot and template.
              UserDescription: Internal support routine.
              Notes: Returns success immediately after dispatching the load request.
            """
            GLOBAL_CACHE.SkillBar.LoadHeroSkillTemplate(hero_index, template)
            if hero_index < 0:
                _fail_log("LoadHeroSkillbar", f"Failed to load hero skillbar: invalid hero index {hero_index}.")
                return BehaviorTree.NodeState.FAILURE
            if not template:
                _fail_log("LoadHeroSkillbar", f"Failed to load hero {hero_index} skillbar: template is empty.")
                return BehaviorTree.NodeState.FAILURE
            _log("LoadHeroSkillbar", f"Loaded hero {hero_index} skillbar template.", log=log)
            return BehaviorTree.NodeState.SUCCESS
        
        tree = BehaviorTree.ActionNode(name="LoadHeroSkillbar", action_fn=lambda: _load_hero_skillbar(hero_index, template), aftercast_ms=250)
        return BehaviorTree(tree)
    
    @staticmethod
    def CastSkillID (skill_id:int,target_agent_id:int =0, extra_condition=True, aftercast_delay=0,  log=False):
        """
        Build a tree that casts a skill by skill id after checking common skill requirements.

        Meta:
          Expose: true
          Audience: intermediate
          Display: Cast Skill ID
          Purpose: Cast a skill by skill id when energy, readiness, and slot checks pass.
          UserDescription: Use this when you want to cast a specific skill from its skill id instead of a slot number.
          Notes: Requires explorable mode, enough energy, readiness, and a valid slot mapping before casting.
        """
        def _use_skill(slot:int,target_agent_id:int, aftercast_delay:int, log:bool):
            """
            Dispatch the actual skill cast for the resolved slot.

            Meta:
              Expose: false
              Audience: advanced
              Display: Internal Cast Skill ID Helper
              Purpose: Issue the low-level skill-use request for a slot resolved from a skill id.
              UserDescription: Internal support routine.
              Notes: Logs the cast using the original skill id after the request is sent.
            """
            GLOBAL_CACHE.SkillBar.UseSkill(slot, target_agent_id=target_agent_id, aftercast_delay=aftercast_delay)
            resolved_slot = GLOBAL_CACHE.SkillBar.GetSlotBySkillID(skill_id)
            if not 1 <= resolved_slot <= 8:
                _fail_log("CastSkillID", f"Failed to cast skill {skill_id}: no valid slot was resolved.")
                return BehaviorTree.NodeState.FAILURE
            _log(
                "CastSkillID",
                f"Cast {GLOBAL_CACHE.Skill.GetName(skill_id)}, slot: {resolved_slot}",
                log=log,
            )
            return BehaviorTree.NodeState.SUCCESS
        
        tree = BehaviorTree.SequenceNode(children=[
                    BehaviorTree.ConditionNode(name="InExplorable", condition_fn=lambda:Checks.Map.IsExplorable()),
                    BehaviorTree.ConditionNode(name="EnoughEnergy", condition_fn=lambda:Checks.Skills.HasEnoughEnergy(Player.GetAgentID(),skill_id)),
                    BehaviorTree.ConditionNode(name="IsSkillIDReady", condition_fn=lambda:Checks.Skills.IsSkillIDReady(skill_id)),
                    BehaviorTree.ConditionNode(name="IsSkillInSlot", condition_fn=lambda:1 <= GLOBAL_CACHE.SkillBar.GetSlotBySkillID(skill_id) <= 8),
                    BehaviorTree.ConditionNode(name="ExtraCustomCondition", condition_fn=lambda: extra_condition),
                    BehaviorTree.ActionNode(name="CastSkillID", action_fn=lambda:_use_skill(GLOBAL_CACHE.SkillBar.GetSlotBySkillID(skill_id), target_agent_id, aftercast_delay, log), aftercast_ms=aftercast_delay),
                ])
        bt = BehaviorTree(root=tree)
        return bt
    
    @staticmethod
    def CastSkillSlot(slot:int,target_agent_id: int =0,extra_condition=True, aftercast_delay=0, log=False):
        """
        Build a tree that casts a skill from a specific skillbar slot after validation checks.

        Meta:
          Expose: true
          Audience: intermediate
          Display: Cast Skill Slot
          Purpose: Cast a skill from a specific slot when the slot is valid and ready.
          UserDescription: Use this when you want to cast from a known slot number rather than a skill id.
          Notes: Requires explorable mode, a valid slot, enough energy, readiness, and any extra custom condition.
        """
        def _use_skill(slot:int,target_agent_id:int, aftercast_delay:int, log:bool):
            """
            Dispatch the actual skill cast for the requested slot.

            Meta:
              Expose: false
              Audience: advanced
              Display: Internal Cast Skill Slot Helper
              Purpose: Issue the low-level skill-use request for a known skillbar slot.
              UserDescription: Internal support routine.
              Notes: Logs the cast using the slot's current skill id after the request is sent.
            """
            GLOBAL_CACHE.SkillBar.UseSkill(slot, target_agent_id=target_agent_id, aftercast_delay=aftercast_delay)
            if not 1 <= slot <= 8:
                _fail_log("CastSkillSlot", f"Failed to cast skill slot: invalid slot {slot}.")
                return BehaviorTree.NodeState.FAILURE
            _log(
                "CastSkillSlot",
                f"Cast {GLOBAL_CACHE.Skill.GetName(GLOBAL_CACHE.SkillBar.GetSkillIDBySlot(slot))}, slot: {slot}",
                log=log,
            )
            return BehaviorTree.NodeState.SUCCESS
        
        tree = BehaviorTree.SequenceNode(children=[
                    BehaviorTree.ConditionNode(name="InExplorable", condition_fn=lambda:Routines.Checks.Map.IsExplorable()),
                    BehaviorTree.ConditionNode(name="ValidSkillSlot", condition_fn=lambda:1 <= slot <= 8),
                    BehaviorTree.ConditionNode(name="EnoughEnergy", condition_fn=lambda:Routines.Checks.Skills.HasEnoughEnergy(Player.GetAgentID(), GLOBAL_CACHE.SkillBar.GetSkillIDBySlot(slot))),
                    BehaviorTree.ConditionNode(name="IsSkillSlotReady", condition_fn=lambda:Routines.Checks.Skills.IsSkillSlotReady(slot)),
                    BehaviorTree.ConditionNode(name="ExtraCustomCondition", condition_fn=lambda: extra_condition),
                    BehaviorTree.ActionNode(name="CastSkillSlot", action_fn=lambda:_use_skill(slot, target_agent_id, aftercast_delay, log), aftercast_ms=aftercast_delay),
                ])
        bt = BehaviorTree(root=tree)
        return bt
    
    @staticmethod
    def IsSkillIDUsable(skill_id: int):
        """
        Build a tree that checks whether a skill id is currently usable.

        Meta:
          Expose: true
          Audience: intermediate
          Display: Is Skill ID Usable
          Purpose: Check whether a skill id can currently be used.
          UserDescription: Use this when you want a reusable condition tree for a skill identified by skill id.
          Notes: Checks explorable state, energy, readiness, and valid slot mapping.
        """
        tree = BehaviorTree.SequenceNode(children=[
            BehaviorTree.ConditionNode(name="InExplorable", condition_fn=lambda:Checks.Map.IsExplorable()),
            BehaviorTree.ConditionNode(name="EnoughEnergy", condition_fn=lambda:Checks.Skills.HasEnoughEnergy(Player.GetAgentID(),skill_id)),
            BehaviorTree.ConditionNode(name="IsSkillIDReady", condition_fn=lambda:Checks.Skills.IsSkillIDReady(skill_id)),
            BehaviorTree.ConditionNode(name="IsSkillInSlot", condition_fn=lambda:1 <= GLOBAL_CACHE.SkillBar.GetSlotBySkillID(skill_id) <= 8),
        ])
        bt = BehaviorTree(root=tree)
        return bt
    
    @staticmethod
    def IsSkillSlotUsable(skill_slot: int):
        """
        Build a tree that checks whether a skillbar slot is currently usable.

        Meta:
          Expose: true
          Audience: intermediate
          Display: Is Skill Slot Usable
          Purpose: Check whether a specific skill slot can currently be used.
          UserDescription: Use this when you want a reusable condition tree for a known skillbar slot.
          Notes: Checks explorable state, slot validity, energy, and readiness.
        """
        def _get_skill_id_from_slot(slot:int):
            """
            Resolve the skill id currently assigned to a slot.

            Meta:
              Expose: false
              Audience: advanced
              Display: Internal Get Skill ID From Slot Helper
              Purpose: Look up the current skill id for a provided skillbar slot.
              UserDescription: Internal support routine.
              Notes: Used to keep slot-based usability checks aligned with current skillbar state.
            """
            return GLOBAL_CACHE.SkillBar.GetSkillIDBySlot(slot)
        
        tree = BehaviorTree.SequenceNode(children=[
            BehaviorTree.ConditionNode(name="InExplorable", condition_fn=lambda:Checks.Map.IsExplorable()),
            BehaviorTree.ConditionNode(name="ValidSkillSlot", condition_fn=lambda:1 <= skill_slot <= 8),
            BehaviorTree.ConditionNode(name="EnoughEnergy", condition_fn=lambda:Checks.Skills.HasEnoughEnergy(Player.GetAgentID(), _get_skill_id_from_slot(skill_slot))),
            BehaviorTree.ConditionNode(name="IsSkillIDReady", condition_fn=lambda:Checks.Skills.IsSkillSlotReady(skill_slot)),
        ])
        bt = BehaviorTree(root=tree)
        return bt
