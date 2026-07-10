# OpenCode Workflow Redesign Proposal

> Proposed on 2026-07-05.
> This proposal is intentionally research-first and does not treat the current local `.opencode` flow as the architecture to preserve.

## 1. Design Objective

Build an OpenCode workflow system that:

- slows the model down before irreversible action
- improves intake quality before planning
- treats intake approval as the hard gate for every long workflow
- uses parallel research when ambiguity is real
- introduces meaningful opposition instead of fake self-agreement
- routes cheaper and stronger models intentionally
- keeps reusable knowledge separate from task state
- supports implementation, documentation, and testing without forcing every task through the full pipeline

This should be a workflow kit, not one giant fixed graph.

## 2. Core Principles

### 2.1 The orchestrator should coordinate, not think for everyone

The orchestrator should:

- classify task type
- decide which workflow to launch
- decide when to escalate
- collect structured outputs
- ask the user for approval at phase boundaries

It should not:

- do the deep research itself
- accumulate giant raw transcripts
- keep rereading the whole world

### 2.2 State must be structured, current, and disposable

Do not use an append-only pool as the main system memory.

Use a per-task state file with sections like:

- request
- intake draft
- approved intake
- constraints
- evidence
- open questions
- options
- chosen plan
- implementation notes
- verification status
- doc status

Keep raw transcripts optional and archival, not always loaded.

Important rule:

- later phases consume the approved intake, not a fresh reinterpretation of the request
- if later phases discover missing assumptions, the workflow must return to intake instead of silently patching the contract

### 2.3 Use agents for incentives and permissions, not for theater

Create an agent only if at least one is true:

- it needs a different model
- it needs a different tool surface
- it needs different success criteria
- it needs a different communication style

If none are true, use a command or a skill instead.

### 2.4 Opposition must be asymmetric

The critic should not just "review politely."
It should be instructed to:

- attack unstated assumptions
- identify ambiguity
- find missing experiments
- challenge model routing
- propose a cheaper or safer alternative

### 2.5 Verification is mandatory for action-heavy tasks

Implementation and validation must be separate roles or separate phases.

### 2.6 Intake is the king artifact

For long workflows, intake is the authoritative contract.

That means:

- only the user can approve intake completion
- planning is forbidden until intake is approved
- if later phases uncover broken assumptions, the workflow reopens intake
- downstream agents inherit the approved intake as the source of truth

## 3. Proposed Building Blocks

## 3.1 Always-On Rules

Keep in:

- `AGENTS.md`
- small referenced instruction files

Keep only:

- repo rules
- editing constraints
- language/runtime constraints
- safety constraints
- high-level architectural facts

Do not keep workflow transcripts here.

## 3.2 Skills

Recommended skill categories:

- `py4gw-core`: repo architecture and high-value gotchas
- `re-methodology`: WASM-first RE procedure
- `verification-playbook`: how to validate Python, C++, launcher, bridge, and widget changes
- `doc-authoring`: doc expectations and file placement
- `workflow-patterns`: how your preferred intake, research, consensus, and verification loops work
- `deepseek-routing`: when to prefer Flash vs Pro

Recommended rule for skills:

- one skill = one reusable capability or one cohesive knowledge area
- target 500 to 2,500 words for most skills
- split anything that becomes a mini-book

## 3.3 Commands

Use commands as workflow entrypoints.

Recommended commands:

- `/intake`
- `/intake-feature`
- `/intake-bug`
- `/intake-research`
- `/intake-reverse-engineering`
- `/intake-refactor`
- `/research`
- `/plan`
- `/implement`
- `/verify`
- `/document`
- `/consensus`
- `/task-status`

This is cleaner than encoding every workflow as a different "primary" agent.

## 3.4 Agents

Recommended initial agent roster:

1. `workflow-orchestrator`
2. `intake-analyst`
3. `intake-opponent`
4. `research-scout`
5. `planner`
6. `opponent`
7. `implementer`
8. `verifier`
9. `docs-writer`

Optional later:

10. `test-author`
11. `consensus-synthesizer`
12. `re-analyst`

That is enough. Start there.

## 4. Proposed Workflow Library

## 4.1 Workflow A: Intake Polish

Use when:

- the request is ambiguous
- the user is exploring
- the cost of misplanning is high

Flow:

1. `intake-analyst` questions the user while inspecting relevant repo context to enrich the conversation.
2. `intake-analyst` produces a polished intake draft with explicit unknowns, assumptions, and proposed constraints.
3. `intake-opponent` attacks the draft: what is still underspecified, what project rules may be forgotten, and what assumptions about implementation are still unproven?
4. `workflow-orchestrator` presents the revised intake back to the user as the current contract.
5. If the user does not approve, the workflow loops back to step 1.
6. Only explicit user approval completes intake.

Output artifact:

- `task_state.md` with an `Approved Intake` section explicitly approved by the user

Model routing:

- intake on Flash by default for speed
- intake-opponent on Flash for fast challenge passes, or Pro if ambiguity is subtle and architectural
- final synthesis on Pro

Why this matters:

- you explicitly said models are too eager
- this workflow forces hesitation before planning
- it treats user approval, not agent confidence, as the completion condition

### 4.1.1 Intake completion rule

Intake is complete only when both are true:

1. the required intake fields are sufficiently populated
2. the user explicitly approves the current intake draft

If either is false, planning is blocked.

### 4.1.2 Recommended intake artifact

Before planning is allowed, the intake artifact should contain at least:

- Objective
- Desired Outcome
- In-Scope Work
- Out-of-Scope Work
- Relevant Repo Areas
- Constraints and Project Rules
- Assumptions Requiring Confirmation
- Unknown Implementation Details
- Acceptance Criteria
- Risks / Failure Modes
- Open Questions
- User Approval Status

This structure matches the real pain point:

- the end goal is usually known
- the "how" is usually underspecified
- project rules and assumptions get lost later unless they are surfaced now

### 4.1.3 Intake behavior standard

The intake phase should feel like a collaborative spec editor.

That means:

- the agent does not just interrogate the user
- it proposes a concrete spec draft after each round
- it highlights what changed, what is still unknown, and what is blocking approval
- it uses repo evidence to ask better questions
- it keeps rewriting the spec until the user says it is correct

## 4.2 Workflow B: Research Swarm

Use when:

- the question is broad
- external research matters
- there are multiple plausible directions

Flow:

1. Launch 2-4 `research-scout` runs with different search angles.
2. Each scout returns:
   - key facts
   - source list
   - confidence
   - contradictions
   - recommended follow-up
3. `consensus-synthesizer` or `planner` merges them into a research brief.
4. `opponent` attacks the brief for missing perspectives.

Suggested scout angles:

- official docs
- community practice
- academic/pattern view
- platform comparison

Model routing:

- scouts on Flash
- synthesis on Pro
- final opposition on Pro for high-stakes research

Guardrail:

- do not let scouts plan implementation

## 4.3 Workflow C: Plan With Opposition

Use when:

- a nontrivial code or architecture change is coming

Flow:

1. `planner` creates plan v1.
2. `opponent` critiques plan v1 aggressively.
3. `planner` creates plan v2 with explicit responses to each criticism.
4. `workflow-orchestrator` checks the plan against the approved intake.
5. `workflow-orchestrator` either approves or asks user checkpoint questions.

Hard gate:

- the planner is not allowed to compensate for a weak intake
- if the approved intake still leaves critical implementation constraints unresolved, the task returns to intake

Required plan structure:

- scope
- impacted files or systems
- assumptions
- alternatives rejected
- implementation steps
- validation steps
- rollback or containment plan

Model routing:

- planner on Pro
- opponent on Pro

This is one of the highest-value places to spend stronger-model budget.

## 4.4 Workflow D: Implement With Verification

Use when:

- the plan is approved

Flow:

1. `implementer` executes the approved plan.
2. `verifier` checks:
   - syntax/build
   - targeted runtime checks
   - plan adherence
   - unexpected side effects
3. `opponent` optionally reviews if the change is risky.
4. `implementer` fixes only verified issues.

Important rule:

- the implementer is allowed to stop and report plan gaps
- it is not allowed to silently improvise architecture

Model routing:

- implementer on Pro for complex code, Flash for simple localized edits
- verifier on Flash for mechanical checks, Pro when interpretation matters

## 4.5 Workflow E: Document and Test

Use when:

- the code change is stable enough to explain

Flow:

1. `test-author` or `verifier` adds or runs targeted checks.
2. `docs-writer` updates the right docs.
3. `workflow-orchestrator` confirms the shipped artifact list.

This phase should not be fused into implementation by default.

## 5. Recommended DeepSeek Routing Matrix

## 5.1 Flash-first tasks

Route to `deepseek-v4-flash`:

- iterative intake questioning and redrafting
- repo scouting
- code search
- documentation discovery
- first-pass web search
- evidence extraction
- classification
- structured note conversion
- simple command execution plans
- quick validation passes

Use thinking mode when the task is still analysis-heavy but not decision-critical.

## 5.2 Pro-first tasks

Route to `deepseek-v4-pro`:

- difficult intake lock-in and final contract synthesis
- architecture planning
- option comparison
- consensus formation
- adversarial critique
- risky implementation
- verification of surprising or ambiguous outcomes
- final user-facing synthesis

## 5.3 Flash -> Pro chain

Best default pattern:

1. Flash questions, scouts, and drafts
2. Pro resolves subtle ambiguity and locks the contract
3. Flash verifies mechanics
4. Pro resolves conflicts and final judgments

This gives you speed without letting the fast model own the final judgment.

Important correction:

- the primary reason to use Flash is speed
- the primary reason to use Pro is depth and judgment
- lower cost is useful but secondary

## 6. Filesystem Proposal

Recommended new structure:

```text
.opencode/
  agents/
    workflow-orchestrator.md
    intake-analyst.md
    intake-opponent.md
    research-scout.md
    planner.md
    opponent.md
    implementer.md
    verifier.md
    docs-writer.md
  commands/
    intake.md
    research.md
    plan.md
    implement.md
    verify.md
    consensus.md
    task-status.md
  skills/
    workflow-patterns/SKILL.md
    deepseek-routing/SKILL.md
    verification-playbook/SKILL.md
    py4gw-core/SKILL.md
    re-methodology/SKILL.md
  tasks/
    active/
      <task-id>/
        state.md
        intake.md
        research.md
        plan.md
        verification.md
        docs.md
    archive/
```

Key difference from the current style:

- task state is per-task
- state is structured by artifact type
- the orchestrator does not need one giant global pool

## 7. Suggested Artifact Schemas

## 7.1 `state.md`

Use headings:

- Original Request
- Intake Status
- Objective
- Desired Outcome
- In-Scope Work
- Out-of-Scope Work
- Relevant Repo Areas
- Constraints
- Project Rules To Preserve
- Confirmed Assumptions
- Unconfirmed Assumptions
- Known Facts
- Unknowns
- Open Questions
- Acceptance Criteria
- Risk Level
- Selected Workflow
- Current Phase
- Model Routing
- Approval Status

## 7.2 `research.md`

- Question
- Search Angles
- Findings
- Contradictions
- Source Links
- Confidence
- Open Gaps

## 7.3 `plan.md`

- Plan Version
- Scope
- Assumptions
- Steps
- Validation
- Critique Responses
- Approval

## 7.4 `verification.md`

- Checks Run
- Results
- Failures
- Fixes Applied
- Residual Risk

## 8. Anti-Patterns To Explicitly Ban

Ban these in the redesign:

- giant append-only shared memory loaded by everyone
- duplicated policy text across every agent
- agents that both decide and verify their own work by default
- using skills as temporary scratchpads
- letting research workers make implementation decisions
- letting planning start before explicit user intake approval
- allowing agents to silently fill in "how" details that should have been clarified in intake
- routing everything to the strongest model
- routing planning to a cheap model just to save tokens
- permanent swarm behavior for ordinary edits

## 9. Implementation Roadmap

### Phase 1

- define the new workflow philosophy
- create the small initial agent set
- create command entrypoints
- add `deepseek-routing` and `workflow-patterns` skills
- introduce per-task state files
- implement the intake gate and approval loop first

### Phase 2

- add research swarm support
- add consensus synthesis
- separate verifier from reviewer if both are needed
- refine model variants for Flash and Pro

### Phase 3

- add optional task archives
- add metrics: latency, token cost, approval count, failure cause
- prune agents and commands that are not producing value

## 10. Recommended Starting Configuration

If you want the first version to be disciplined, start with:

- 1 primary orchestrator
- 7-8 subagents
- intake archetype commands first
- 4-6 focused skills
- 1 task-state format
- Flash for fast questioning and scouting, Pro for lock-in and decisions

Do not start with:

- many specialist micro-agents
- always-on swarm mode
- giant context pools
- complex auto-cataloging

## 11. Immediate Next Step

The next practical move should be:

1. agree on the workflow library and agent roster
2. agree on the intake artifact and approval loop
3. agree on the state-file format
4. agree on the Flash vs Pro routing rules
5. only then rewrite `.opencode`

If we skip that order, the new configuration will just be another prompt pile.
