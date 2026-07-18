# OpenCode Agentic Workflow Research

> Compiled 2026-07-05.
> Goal: research OpenCode, adjacent coding-agent ecosystems, modern agent workflow patterns, and DeepSeek V4 model-routing implications for a stronger OpenCode-based flow.

## 1. Executive Summary

The main conclusion is simple:

- OpenCode already has the right low-level primitives: custom agents, per-agent permissions, skills, custom commands, MCP servers, custom tools, model variants, and task delegation.
- The hard part is not feature availability. The hard part is orchestration design.
- Current best practice across coding-agent systems is converging on small, sharply-bounded workers plus a thin orchestrator, not a giant pipeline with permanent shared transcripts.
- The most common failure mode is over-orchestration: too many agents, too much duplicated prompt text, too much always-on memory, and summaries or pools that become the system instead of supporting it.
- For model routing, the high-value split is usually:
  - faster model for intake triage, repeated clarification rounds, broad research sweeps, indexing, scouting, and first-pass criticism
  - stronger model for planning, synthesis, adversarial review, implementation, and final decisions

For your target system, the right direction is not "make the current flow more elaborate." It is:

1. Make intake the hard gate, then separate research, planning, opposition, implementation, verification, and documentation into distinct phases.
2. Keep only compact structured state between phases.
3. Use parallel research and opposition deliberately, not everywhere.
4. Route work to DeepSeek V4 Flash or Pro based on task shape, not agent prestige.
5. Make the orchestrator a traffic controller, not a knowledge warehouse.

## 2. What OpenCode Actually Gives You

OpenCode's docs show that the platform already supports the building blocks needed for an advanced agent harness:

- `AGENTS.md` plus extra `instructions` files for always-on project rules.
- configurable built-in tools including `bash`, `edit`, `write`, `read`, `grep`, `glob`, `apply_patch`, `skill`, `todowrite`, `webfetch`, `websearch`, and `question`
- per-tool permissions with `allow`, `deny`, and `ask`
- per-agent configuration, including mode, model, permissions, hidden/internal agents, and task permissions
- custom commands for reusable higher-level prompts
- MCP servers for external tool surfaces
- custom tools for repo-specific capabilities
- agent skills via `SKILL.md`
- model variants and provider-specific options

Important details from the OpenCode docs:

- `websearch` is available when using the OpenCode provider or when `OPENCODE_ENABLE_EXA=1`.
- skills are loaded on-demand through the native `skill` tool from `.opencode/skills/`, `.claude/skills/`, and `.agents/skills/` compatible locations.
- subagents can be hidden and exposed only through task delegation.
- `permission.task` can explicitly control which subagents an agent is allowed to spawn.
- permissions also support external-directory scoping and command-pattern matching.
- MCP tools are powerful but token-expensive; OpenCode explicitly warns that some MCP servers can bloat context quickly.

Research implication:

- OpenCode is not missing capabilities.
- Your design problem is harness policy: what always loads, what loads on demand, what gets summarized, what gets preserved, and which model does which work.

## 3. OpenCode-Specific Architecture Guidance

From the official docs, the most relevant OpenCode design levers are:

### 3.1 Rules

`AGENTS.md` should hold durable project rules.

Use `instructions` in `opencode.json` for:

- split rulesets
- mode- or domain-specific references
- shared remote instructions if needed

Research implication:

- stable repo rules belong in `AGENTS.md` or referenced instruction files
- they do not belong inside every specialist agent prompt

### 3.2 Skills

Skills are for reusable procedural knowledge:

- domain playbooks
- operator checklists
- RE methodologies
- test procedures
- formatting and packaging conventions

They are a poor fit for:

- live project state
- mutable session memory
- giant append-only transcripts

### 3.3 Agents

OpenCode agents are best used as role-isolated workers with:

- a clear trigger description
- constrained permissions
- optionally different models
- optional hidden status for internal workers

Research implication:

- a good agent is narrow enough that you can say when it should not be used

### 3.4 Commands

Commands are the right place for "start a named workflow" behavior such as:

- `/intake`
- `/research`
- `/plan`
- `/consensus`
- `/implement`
- `/ship-docs`

This matters because some behavior is workflow initiation, not agent identity.

## 4. Cross-Platform Patterns That Matter

### 4.1 Claude Code

Claude Code's subagent docs strongly reinforce several patterns:

- subagents exist to preserve the parent context by isolating noisy work
- built-in research/planning agents are read-only
- subagents can have separate tools, permissions, hooks, skills, and memory behavior
- cheaper models are explicitly recommended for lower-risk delegated work
- agent teams, background agents, dynamic workflows, and worktree isolation are first-class concepts in the ecosystem

The important lesson is not "copy Claude Code."

The lesson is:

- exploration should not pollute implementation context
- the parent should receive only what it needs to decide the next move
- delegation is primarily a context-management strategy, not just a specialization trick

### 4.2 Roo Code

Roo Code's Boomerang Tasks docs are especially relevant because they make the orchestrator intentionally weak:

- the built-in Orchestrator mode delegates to specialized modes
- subtasks run in isolated context
- only a summary returns upward
- the orchestrator is intentionally limited so it does not drown itself in file reads

That design is directly aligned with your stated problem:

- models get eager
- they over-process
- they self-persuade too quickly

Roo's answer is not "more memory."
It is "less context in the decision-maker."

### 4.3 OpenHands

OpenHands research emphasizes:

- sandboxed execution
- composable agent SDK design
- multi-LLM routing
- secure and portable execution

The main relevance here is architectural:

- the more ambitious the workflow, the more you need lifecycle control, bounded tool surfaces, and explicit state transitions

### 4.4 Skills Standard and Configuration Research

Recent 2026 research is useful here:

- `Configuring Agentic AI Coding Tools` found that context files dominate, while skills and subagents are usually used only shallowly.
- `From Registry to Repository` found that reused skills are mostly copied once and then locally adapted, usually by adding project-specific bindings instead of rewriting the behavioral contract.

Research implication:

- keep behavioral contracts stable
- put project-specific bindings in local skills and commands
- do not let agent prompts become large mutable documents

## 5. Multi-Agent Workflow Patterns That Actually Work

Based on Anthropic workflow patterns, Roo orchestration, current coding-agent papers, and the broader tooling ecosystem, the most robust patterns are:

### 5.1 Orchestrator -> Worker

Use when:

- work can be decomposed cleanly
- specialists can return bounded outputs

Good for:

- intake to research
- research to planning
- implementation to verification

### 5.2 Evaluator -> Optimizer

Use when:

- first-pass output is likely incomplete or overconfident

Good for:

- plan -> critique -> plan refinement
- implementation -> review -> focused fix

This directly matches your desire for opposition and polishing.

### 5.3 Parallel Analysts -> Consensus

Use when:

- research space is broad
- ambiguity is high
- a single agent is likely to anchor too early

Good for:

- web research
- RE work
- architecture option generation

Do not use it for trivial edits. It adds latency and synthesis burden.

For intake specifically, a light two-agent loop is usually better than a large swarm:

- one agent enriches and drafts the spec
- one agent attacks ambiguity and forgotten assumptions

### 5.4 Read-Only Scout Before Action

Use when:

- the repo area is unfamiliar
- instructions are underspecified

This is the cheapest way to reduce "eager execution."

### 5.5 Verification Gate

Use when:

- implementation risks regressions
- tool usage has side effects
- the model is prone to declaring success early

Verification is distinct from review:

- review asks "is this a good change?"
- verification asks "did it actually work?"

### 5.6 Structured State Handoff

This is the most important pattern.

Do not pass giant transcripts between phases.
Pass a compact structured artifact:

- task statement
- constraints
- evidence
- open questions
- decision
- implementation targets
- verification checklist

This is where many agent systems fail.

## 6. Failure Modes Repeated Across the Ecosystem

### 6.1 Over-Orchestration

Symptoms:

- too many agents
- agents with overlapping jobs
- repeated prompt boilerplate
- more coordination than work

Result:

- latency
- token waste
- false rigor

### 6.2 Context Poisoning

Roo explicitly calls this out.
Once the orchestrator reads everything, it stops orchestrating and starts improvising from noisy context.

### 6.3 Shared-Memory Bloat

Append-only context pools feel safe, but they often become self-defeating:

- stale facts remain live forever
- the model cannot tell current state from historical exploration
- contradiction detection becomes harder, not easier

### 6.4 Bad Skill Boundaries

Skills become harmful when they contain:

- task-specific temporary notes
- mutable project state
- giant prose catalogs that should be split

### 6.5 Premature Consensus

If one planner and one critic are too similar, the "opposition" is fake.
The harness should force alternate perspectives:

- option generation vs option criticism
- evidence gatherer vs synthesis decider
- implementer vs verifier

### 6.6 Guessing Under Underspecification

Recent 2026 research on coding-agent action-boundary violations found that underspecified instructions often do not cause agents to stop; they cause agents to guess.

That is directly relevant to your stated concern.

Harness implication:

- intake must be explicit
- intake must be allowed to loop until the user approves it
- uncertainty must survive into planning
- agents should be rewarded for escalating ambiguity instead of smoothing it over

## 7. DeepSeek V4 Flash and Pro: What Matters for Harness Design

### 7.1 Current official facts

From DeepSeek's API docs and model card as of 2026-07-05:

- active API models are `deepseek-v4-flash` and `deepseek-v4-pro`
- both support 1M context
- both support tool calls and JSON output
- both support thinking and non-thinking modes
- `deepseek-chat` and `deepseek-reasoner` are compatibility names scheduled for deprecation on 2026-07-24 15:59 UTC
- pricing currently listed by DeepSeek API:
  - Flash: $0.14 / 1M input cache miss, $0.28 / 1M output
  - Pro: $0.435 / 1M input cache miss, $0.87 / 1M output
- DeepSeek also publishes OpenCode and Claude Code integration guides

### 7.2 Relative capability shape

From the official model card:

- Pro is the stronger knowledge and harder reasoning model
- Flash is smaller and cheaper
- Flash-Max is described by DeepSeek as approaching Pro on reasoning when given larger thinking budgets, but still slightly behind on pure knowledge tasks and the most complex agentic workflows
- both are positioned as strong coding and long-context models

### 7.3 Practical routing guidance

Use Flash for:

- iterative intake questioning
- repo scouting
- web discovery
- broad candidate generation
- first-pass extraction
- low-risk opposition
- converting raw findings into structured notes
- command/skill selection assistance

Use Pro for:

- locking a difficult intake into a final approved contract
- planning with tradeoffs
- architecture synthesis
- consensus resolution
- adversarial review of nontrivial plans
- implementation in sensitive subsystems
- verification of surprising findings
- final user-facing synthesis

Use Flash with high effort only when:

- the task is still mostly search-and-sort or clarification-heavy
- speed matters more than final-depth judgment
- correctness can be checked by a stronger verifier later

Use Pro early when:

- ambiguity is central
- the right plan is harder than the code
- the task needs strong judgment, not just strong execution

## 8. What This Means For Your New OpenCode Flow

Your stated goals imply a specific harness philosophy:

- protect against eagerness
- introduce deliberate opposition
- improve intake before planning
- require explicit user approval before intake is considered complete
- use swarming for research and ambiguity reduction
- preserve enough state to continue work across phases
- avoid hard-coding one rigid mega-pipeline

That points to a modular workflow library, not one monolithic orchestrator.

The system should offer a small set of workflow patterns:

- Intake polish
- Research swarm
- Plan with opposition
- Implement with verification
- Document and catalog

Each pattern should be callable independently.

## 9. Recommended Boundaries

Use this rule:

- `AGENTS.md` / instructions: durable repo rules
- skills: reusable domain knowledge and operating procedures
- commands: named workflow entrypoints
- agents: role-specialized workers
- state files: current task facts and decisions, not giant transcripts
- MCP/custom tools: capability extensions

If something is temporary and task-specific, it should not be a skill.
If something is reusable but not always relevant, it should usually be a skill.
If something is "start a standard workflow," it should usually be a command.
If something needs a different tool surface, model, or incentives, it should be an agent.

## 10. Design Conclusions

The strongest research-backed direction is:

- thin orchestrator
- small worker set
- explicit structured state
- read-only research isolation
- adversarial planning
- separate verification from review
- model routing by task shape
- limited, intentional swarm usage

The redesign should optimize for:

- fewer always-loaded instructions
- fewer role overlaps
- less transcript inheritance
- more explicit uncertainty handling
- more deliberate model selection

## Sources

- OpenCode Intro: https://opencode.ai/docs
- OpenCode Tools: https://opencode.ai/docs/tools/
- OpenCode Rules: https://opencode.ai/docs/rules/
- OpenCode Agents: https://opencode.ai/docs/agents/
- OpenCode Commands: https://opencode.ai/docs/commands/
- OpenCode Permissions: https://opencode.ai/docs/permissions/
- OpenCode Agent Skills: https://opencode.ai/docs/skills/
- OpenCode Models: https://opencode.ai/docs/models/
- OpenCode MCP Servers: https://opencode.ai/docs/mcp-servers/
- OpenCode Custom Tools: https://opencode.ai/docs/custom-tools/
- OpenCode Ecosystem: https://opencode.ai/docs/ecosystem/
- Claude Code subagents: https://code.claude.com/docs/en/sub-agents
- Claude Code hooks: https://code.claude.com/docs/en/hooks
- Claude Code memory: https://code.claude.com/docs/en/memory
- Roo Code custom instructions: https://roocodeinc.github.io/Roo-Code/features/custom-instructions/
- Roo Code Boomerang Tasks: https://roocodeinc.github.io/Roo-Code/features/boomerang-tasks/
- Roo Code custom modes: https://roocodeinc.github.io/Roo-Code/features/custom-modes/
- Roo Code skills: https://roocodeinc.github.io/Roo-Code/features/skills/
- Roo Code worktrees: https://roocodeinc.github.io/Roo-Code/features/worktrees/
- Roo Code MCP: https://roocodeinc.github.io/Roo-Code/features/mcp/overview/
- DeepSeek API docs: https://api-docs.deepseek.com/
- DeepSeek pricing: https://api-docs.deepseek.com/quick_start/pricing
- DeepSeek Claude Code integration: https://api-docs.deepseek.com/quick_start/agent_integrations/claude_code
- DeepSeek OpenCode integration: https://api-docs.deepseek.com/quick_start/agent_integrations/opencode
- DeepSeek V4 technical report / model card: https://arxiv.org/abs/2606.19348
- Hugging Face DeepSeek V4 Pro: https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro
- Hugging Face DeepSeek V4 Flash: https://huggingface.co/deepseek-ai/DeepSeek-V4-Flash
- Configuring Agentic AI Coding Tools (2026): https://arxiv.org/abs/2602.14690
- From Registry to Repository (2026): https://arxiv.org/abs/2607.00911
- Recursive Agent Harnesses (2026): https://arxiv.org/abs/2606.13643
- Dive into Claude Code (2026): https://arxiv.org/abs/2604.14228
- OpenHands platform paper: https://arxiv.org/abs/2407.16741
- OpenHands SDK paper: https://arxiv.org/abs/2511.03690
- Coding Agents Are Guessing (2026): https://arxiv.org/abs/2607.02294
- Swarm Skills (2026): https://arxiv.org/abs/2605.10052
