# Agent Skills & Agentic Flows — Research Compendium

> Compiled 2026-05-31 from OpenCode, OpenAI Codex, Claude/Anthropic, agentskills.io, and Reddit.

---

## 1. The SKILL.md Standard (agentskills.io)

### Format

An open standard adopted by **30+ products** (OpenCode, Claude Code, OpenAI Codex, Gemini CLI, Cursor, GitHub Copilot, VS Code, JetBrains Junie, OpenHands, Mux, Amp, Letta, Goose, Roo Code, Mistral Vibe, Spring AI, and more).

A skill is a directory containing a `SKILL.md` file:

```
my-skill/
├── SKILL.md          # Required: YAML frontmatter + Markdown body
├── scripts/          # Optional: executable code
├── references/       # Optional: documentation
├── assets/           # Optional: templates, resources
└── agents/           # Optional: platform-specific metadata (openai.yaml, etc.)
```

**YAML frontmatter** (required fields):
```yaml
---
name: skill-name           # 1-64 chars, lowercase-hyphenated, regex: ^[a-z0-9]+(-[a-z0-9]+)*$
description: What it does  # 1-1024 chars, specific enough for agents to match correctly
license: MIT               # Optional
compatibility: opencode    # Optional
metadata:                  # Optional string-to-string map
  audience: maintainers
---
```

**Markdown body**: Instructions, workflows, code examples, file references — anything the agent needs to perform the task.

### Progressive Disclosure (the key innovation)

All three major platforms use the same 3-level loading model:

| Level | What loads | Token cost | When |
|-------|-----------|------------|------|
| **Level 1: Metadata** | `name` + `description` from YAML frontmatter | ~100 tokens per skill | Always (at startup) |
| **Level 2: Instructions** | Full `SKILL.md` body | ~1,000–5,000 tokens | When task matches description |
| **Level 3: Resources** | Bundled scripts, references, templates | Near zero (code never enters context; only output) | As referenced by instructions |

This means you can install **dozens of skills** with almost zero context penalty. Only the one being used loads fully.

### Skill Discovery Locations

Skills are discovered from multiple locations in priority order:

| Scope | Path | Used By |
|-------|------|---------|
| Project | `.opencode/skills/<name>/SKILL.md` | OpenCode |
| Global | `~/.config/opencode/skills/<name>/SKILL.md` | OpenCode |
| Claude-compatible (project) | `.claude/skills/<name>/SKILL.md` | OpenCode, Claude Code |
| Claude-compatible (global) | `~/.claude/skills/<name>/SKILL.md` | OpenCode, Claude Code |
| Agent-compatible (project) | `.agents/skills/<name>/SKILL.md` | OpenCode, Codex |
| Agent-compatible (global) | `~/.agents/skills/<name>/SKILL.md` | OpenCode, Codex |
| Repository root | `$REPO_ROOT/.agents/skills/` | Codex |
| User | `$HOME/.agents/skills/` | Codex |
| Admin | `/etc/codex/skills/` | Codex |
| System | Bundled with the agent | Codex, Claude |

OpenCode walks up from the current working directory to the git worktree root, loading any matching `skills/*/SKILL.md` along the way.

### Skill Tool Invocation

Agents load skills by calling the `skill` tool:

```
skill({ name: "skill-name" })
```

Skills can be invoked:
- **Explicitly**: User mentions the skill (`$skill-name` in Codex, `@skill-name` in OpenCode)
- **Implicitly**: Agent matches task description against skill descriptions and loads automatically
- **Programmatically**: Orchestrator instructs subagents which skills to load

### Permissions

Skills are gated by permission keys with glob patterns:

```json
{
  "permission": {
    "skill": {
      "*": "allow",
      "internal-*": "deny",
      "experimental-*": "ask"
    }
  }
}
```

- `allow` — Loads immediately
- `deny` — Hidden from agent entirely
- `ask` — User prompted for approval

---

## 2. OpenCode Agent System

### Agent Types

**Primary agents**: Main assistants you interact with directly. Cycle with Tab key.

**Subagents**: Specialized assistants primary agents invoke via the Task tool or `@mention`.

### Built-in Agents

| Agent | Mode | Access | Purpose |
|-------|------|--------|---------|
| **Build** | Primary | All tools enabled | Default — full file ops + bash for development |
| **Plan** | Primary | File edits: ask, Bash: ask | Analysis and planning without making changes |
| **General** | Subagent | Full tools (except todo) | Multi-step tasks, parallel work |
| **Explore** | Subagent | Read-only | Fast codebase exploration, file search |
| **Scout** | Subagent | Read-only | External docs and dependency research |
| **Compaction** | Primary (hidden) | System | Auto-compacts long context |
| **Title** | Primary (hidden) | System | Auto-generates session titles |
| **Summary** | Primary (hidden) | System | Auto-creates session summaries |

### Agent Configuration Options

| Option | Description |
|--------|-------------|
| `description` | What the agent does and when to use it (required) |
| `temperature` | 0.0-1.0; lower = more focused, higher = more creative |
| `steps` | Max agentic iterations before forced text response |
| `disable` | Set to `true` to disable |
| `prompt` | Custom system prompt file path |
| `model` | Override model per agent (format: `provider/model-id`) |
| `permissions` | Per-agent permission overrides (14 keys with glob patterns) |
| `mode` | `primary`, `subagent`, or `all` |
| `hidden` | Hide from `@` autocomplete (subagents only) |
| `color` | Hex or theme color for UI |
| `top_p` | 0.0-1.0 for response diversity |
| Additional | Passed through to provider (e.g., `reasoningEffort`) |

### Agent Creation

**JSON** (in `opencode.json`):
```json
{
  "agent": {
    "code-reviewer": {
      "description": "Reviews code for best practices and potential issues",
      "mode": "subagent",
      "model": "anthropic/claude-sonnet-4-20250514",
      "prompt": "You are a code reviewer...",
      "permission": { "edit": "deny" }
    }
  }
}
```

**Markdown** (in `~/.config/opencode/agents/` or `.opencode/agents/`):
```markdown
---
description: Reviews code for quality and best practices
mode: subagent
model: anthropic/claude-sonnet-4-20250514
temperature: 0.1
permission:
  edit: deny
  bash: deny
---
You are in code review mode. Focus on...
```

The markdown filename becomes the agent name (`review.md` → `review` agent).

### Permission System (14 keys)

| Key | Controls |
|-----|----------|
| `read` | Reading files (matches file path) |
| `edit` | All file modifications (edit, write, patch) |
| `glob` | File globbing (matches glob pattern) |
| `grep` | Content search (matches regex) |
| `bash` | Shell commands (matches parsed commands) |
| `task` | Launching subagents (matches subagent name) |
| `skill` | Loading skills (matches skill name) |
| `lsp` | LSP queries |
| `question` | Asking user questions |
| `webfetch` | Fetching URLs (matches URL) |
| `websearch` | Web search (matches query) |
| `external_directory` | Paths outside project worktree |
| `todowrite` | Todo list management |
| `doom_loop` | Same tool call repeats 3x with identical input |

Each key accepts: `"allow"`, `"ask"`, `"deny"`, or an object with glob patterns. **Last matching rule wins.**

### Built-in Tools

| Tool | Purpose |
|------|---------|
| `bash` | Execute shell commands |
| `edit` | Exact string replacements in files |
| `write` | Create or overwrite files |
| `read` | Read file contents with line ranges |
| `grep` | Regex content search (uses ripgrep) |
| `glob` | File pattern matching |
| `lsp` | LSP code intelligence (experimental) |
| `apply_patch` | Apply patches to files |
| `skill` | Load SKILL.md content |
| `todowrite` | Manage todo lists (disabled for subagents by default) |
| `webfetch` | Fetch web content |
| `websearch` | Web search via Exa AI |
| `question` | Ask user questions during execution |

---

## 3. OpenAI Codex — Subagents & Skills

### Subagent Architecture

Codex spawns specialized agents in parallel, collects results, and consolidates. Key concepts:

- **Context pollution**: Useful info gets buried under noisy intermediate output (exploration notes, test logs, stack traces)
- **Context rot**: Performance degrades as conversation fills with less relevant details
- **Solution**: Move noisy work off the main thread — subagents return summaries, not raw output

### Built-in Agents

| Agent | Purpose |
|-------|---------|
| `default` | General-purpose fallback |
| `worker` | Execution-focused — implementation and fixes |
| `explorer` | Read-heavy codebase exploration |

### Global Subagent Settings

```toml
[agents]
max_threads = 6          # Concurrent open agent cap (default: 6)
max_depth = 1            # Nesting depth (default: 1 — child can spawn, no deeper)
job_max_runtime_seconds  # Per-worker timeout for CSV jobs
```

### Custom Agent Files (TOML)

Stored at `~/.codex/agents/` (personal) or `.codex/agents/` (project):

```toml
name = "reviewer"
description = "PR reviewer focused on correctness, security, and missing tests."
developer_instructions = """
Review code like an owner. Prioritize correctness, security, behavior regressions, and missing test coverage.
"""
model = "gpt-5.4"
model_reasoning_effort = "high"
sandbox_mode = "read-only"
nickname_candidates = ["Atlas", "Delta", "Echo"]
```

Required fields: `name`, `description`, `developer_instructions`.

### Model Selection Guidance

| Model | Use Case |
|-------|----------|
| `gpt-5.5` | Start here for demanding agents — strongest for ambiguous, multi-step work |
| `gpt-5.4` | Strong coding, reasoning, tool use, broader workflows |
| `gpt-5.4-mini` | Speed/efficiency over depth — exploration, read-heavy scans, parallel workers |
| `gpt-5.3-codex-spark` | Near-instant text-only iteration (ChatGPT Pro required) |

### Reasoning Effort

| Level | When to use |
|-------|------------|
| `high` | Complex logic, assumption checking, edge cases (reviewer, security agents) |
| `medium` | Balanced default for most agents |
| `low` | Straightforward tasks, speed matters most |

Higher = more response time and tokens, better quality for complex work.

### CSV Batch Processing (experimental)

`spawn_agents_on_csv` — reads a CSV, spawns one worker per row, exports combined results:

```
spawn_agents_on_csv with:
- csv_path: /tmp/components.csv
- id_column: path
- instruction: "Review {path} owned by {owner}. Return JSON via report_agent_job_result."
- output_csv_path: /tmp/components-review.csv
```

### Codex Skills

Same SKILL.md format. Additional features:

- **Skill creator**: `$skill-creator` (interactive)
- **Skill installer**: `$skill-installer linear` (install curated skills)
- **Enable/disable**: `[[skills.config]]` entries in `~/.codex/config.toml`
- **Distribution**: Package skills as plugins for sharing

Skills use progressive disclosure just like OpenCode and Claude. The initial skills list is capped at ~2% of context window or 8,000 characters. Codex shortens descriptions first when near the cap.

### `agents/openai.yaml` Metadata

```yaml
interface:
  display_name: "Optional user-facing name"
  short_description: "Optional user-facing description"
  icon_small: "./assets/small-logo.svg"
  icon_large: "./assets/large-logo.png"
  brand_color: "#3B82F6"
  default_prompt: "Optional surrounding prompt"

policy:
  allow_implicit_invocation: false   # When false, only explicit $skill works

dependencies:
  tools:
    - type: "mcp"
      value: "openaiDeveloperDocs"
      description: "OpenAI Docs MCP server"
      transport: "streamable_http"
      url: "https://developers.openai.com/mcp"
```

---

## 4. Claude/Anthropic — Agent Skills

### Why Skills

Skills are reusable, filesystem-based resources providing domain-specific expertise. Unlike prompts (one-off conversation instructions), skills load on-demand across multiple conversations.

Key benefits:
- **Specialize Claude**: Tailor capabilities for domain-specific tasks
- **Reduce repetition**: Create once, use automatically across sessions
- **Compose capabilities**: Combine skills for complex workflows

### Skill Types

| Type | What it is | How loaded |
|------|-----------|------------|
| **Instructions** | Procedural knowledge, workflows, best practices | Loaded into context window |
| **Code** | Executable scripts (Python, bash, etc.) | Run via bash; code NEVER enters context — only output |
| **Resources** | Reference materials, schemas, templates, docs | Loaded on demand from filesystem |

### Where Skills Work

| Surface | Pre-built Skills | Custom Skills | Sharing |
|---------|-----------------|---------------|---------|
| Claude API | PowerPoint, Excel, Word, PDF | Upload via `/v1/skills` endpoints | Workspace-wide |
| Claude Code | None | Filesystem-based directories | Personal (`~/.claude/skills/`) or project (`.claude/skills/`) |
| claude.ai | PowerPoint, Excel, Word, PDF | Upload as zip files | Individual user only |

### Pre-built Skills (from Anthropic)

- **PowerPoint (pptx)**: Create presentations, edit slides, analyze content
- **Excel (xlsx)**: Create spreadsheets, analyze data, generate reports with charts
- **Word (docx)**: Create documents, edit content, format text
- **PDF (pdf)**: Generate formatted PDF documents and reports
- **Claude API**: Up-to-date API reference material, SDK docs, best practices for 8 languages

### Runtime Constraints by Surface

| Constraint | Claude API | Claude Code | claude.ai |
|-----------|-----------|-------------|-----------|
| Network access | **None** | Full | Varies (user/admin settings) |
| Package installation | Only pre-installed | Local only (avoid global) | Varies |
| Code execution | In VM container | On user's machine | In sandbox |

### Security

Skills execute in the agent's environment with the agent's permissions. A malicious skill can:
- Invoke tools in harmful ways
- Exfiltrate data to external systems
- Execute unexpected code

**Rule**: Only use skills from trusted sources (yourself or Anthropic). Audit all files before use.

---

## 5. Building Effective Agents (Anthropic Engineering, Dec 2024)

### Core Distinction

- **Workflows**: LLMs and tools orchestrated through predefined code paths
- **Agents**: LLMs dynamically direct their own processes and tool usage

### The Principle: Start Simple

Find the simplest solution possible. Only increase complexity when needed. Many applications only need single LLM calls with retrieval + in-context examples.

### The Augmented LLM (Building Block)

LLM + retrieval + tools + memory. Models actively use these capabilities — generating their own search queries, selecting appropriate tools, determining what to retain.

### Five Workflow Patterns

#### 1. Prompt Chaining
Sequential steps where each LLM call processes the previous output. With programmatic checks (gates) on intermediates.

**When**: Tasks can be cleanly decomposed into fixed subtasks. Trade latency for accuracy.

**Examples**: Marketing copy → translate. Document outline → check criteria → write document.

#### 2. Routing
Classify input → direct to specialized followup. Separation of concerns, specialized prompts.

**When**: Complex tasks with distinct categories. Classification can be LLM or traditional model.

**Examples**: Customer service (general vs refund vs tech support). Route easy questions to cheaper/faster models.

#### 3. Parallelization
LLMs work simultaneously, outputs aggregated programmatically.

- **Sectioning**: Independent subtasks in parallel
- **Voting**: Same task multiple times for diverse outputs

**When**: Subtasks can be parallelized for speed, or multiple perspectives needed for confidence.

**Examples**: Guardrails (one screens while another responds). Vulnerability review (multiple prompts flag issues).

#### 4. Orchestrator-Workers
Central LLM dynamically breaks down tasks, delegates to workers, synthesizes results.

**When**: Complex tasks where subtasks can't be predicted (coding: number of files and nature of changes depend on the task).

**Key difference from parallelization**: Subtasks aren't pre-defined — orchestrator determines them based on input.

**Examples**: Multi-file code changes. Search tasks across multiple sources.

#### 5. Evaluator-Optimizer
One LLM generates, another evaluates and provides feedback in a loop.

**When**: Clear evaluation criteria exist, and iterative refinement provides measurable value. Two signs of fit: (1) human feedback demonstrably improves output, (2) the LLM can provide such feedback.

**Examples**: Literary translation (nuance critique). Complex search (evaluator decides if more searching needed).

### Autonomous Agents

Agents begin with a command or discussion with the user. Once the task is clear, they plan and operate independently, returning for information or judgment as needed. Crucial: gain "ground truth" from the environment at each step (tool call results, code execution) to assess progress.

**When**: Open-ended problems where steps can't be predicted, hardcoding a fixed path is impossible.

**Cost**: Higher token usage, potential for compounding errors. Extensive sandbox testing + guardrails required.

### Agent-Computer Interface (ACI) Design

Invest as much effort in tool design as in prompt engineering:

1. Give the model enough tokens to "think" before committing
2. Keep format close to what models see naturally on the internet
3. Avoid formatting overhead (line counts, string escaping)
4. Test how the model uses tools — iterate based on observed mistakes
5. **Poka-yoke**: Design tool arguments so mistakes are harder to make
6. Use absolute paths (not relative) if the agent changes directories

**SWE-bench lesson**: More time was spent optimizing tools than the overall prompt.

### Three Core Principles

1. **Simplicity** in agent design
2. **Transparency** — explicitly show the agent's planning steps
3. Carefully craft ACI through thorough **tool documentation and testing**

---

## 6. Reddit Community Insights

### r/DeepSeek (~197k members)

**Key discussions (May 2026):**
- DeepSeek-V4 Preview is live and open-sourced
- v4-Pro Model at 75% off API pricing — described as "basically free"
- Expert mode concerns: context window potentially capped at 128k
- Web chat limits: 6 edits / 6 regenerations per session
- Active community building desktop apps, persistent memory tools
- Users migrating from Claude Opus/Sonnet to DeepSeek due to pricing
- Censorship concerns with some queries

**Takeaway**: DeepSeek is extremely popular for API usage. Price is the #1 driver. Reliability and limits are common complaints.

### r/opencode

**Key discussions (May 2026):**
- "In love with DeepSeek" — common combo: OpenCode as agent harness, DeepSeek as model
- Plugin ecosystem growing: multi-account management, auto-switch on rate limits
- `opencode-raven`: search agent plugin enforcing delegation
- `aienv`: Docker-like isolated environments for agents
- Model comparisons: GLM, Kimi, DeepSeek tested for code generation
- Concerns: memory leaks, token usage accuracy, model quality fluctuations
- New users seeking recommendations for models and configurations

**Takeaway**: OpenCode + DeepSeek is the most popular pairing. Plugin ecosystem is active. Quality fluctuations are a recurring topic.

### r/opencodeCLI (~2.5k members)

**Key discussions (May 2026):**
- Very technical community — focused on agent configuration, reliability, and model testing
- "Opencode Skill to Document Codebases" — community-built skill
- "Why do models resort to simplest fix rather than proper fix and how do I stop it?" — agent behavior tuning
- "Prompt injection → credential exfiltration is a real path" — security concerns
- `opencode-raven v2.0.0`: hard MCP/tool rerouting, not just search delegation
- "DS4 Flash really dumb today?" — model quality fluctuations
- opencode x Ghostty terminal praised for workflow
- Go subscription effectiveness debate
- MCP server resource reading issues, timeout configuration

**Takeaway**: Power users want more control over agent behavior (timeouts, fix quality, delegation enforcement). Security around prompt injection is a real concern. Model reliability varies day-to-day.

---

## 7. Key Design Patterns (Cross-Platform Synthesis)

### Pattern 1: Separate System Knowledge from Task Instructions

All platforms converge on extracting project/domain knowledge into skills rather than loading it into every prompt. System prompts stay lean (~100-300 lines focused on agent behavior). Domain expertise loads on demand.

### Pattern 2: Progressive Disclosure Enables Scale

The 3-level loading model (metadata → instructions → resources) means you can maintain dozens of skills with minimal context cost. This is the single most important architectural insight across all platforms.

### Pattern 3: Permissions Are Converging on allow/ask/deny with Globs

OpenCode, Codex, and Claude all implement permission systems with the same three actions and pattern-based matching. The difference is granularity (OpenCode: 14 keys, Codex: sandbox modes, Claude: tool-level).

### Pattern 4: Subagents Prevent Context Pollution

Long-running sessions accumulate noise. Subagents isolate work into focused contexts and return summaries. Codex explicitly names "context rot" as the problem subagents solve. OpenCode's General/Explore/Scout subagents serve the same purpose.

### Pattern 5: Model Tiering by Task Complexity

Different subagents need different models. Codex recommends gpt-5.4-mini for fast scans, gpt-5.5 for complex reasoning. The pattern: cheaper/faster models for exploration and simple fixes; more capable models for planning, review, and complex implementation.

### Pattern 6: Orchestrator-Workers is the Dominant Multi-Agent Flow

Anthropic identifies it as one of 5 core patterns. Both OpenCode and Codex implement it natively. The orchestrator decomposes tasks, delegates to specialized workers, and synthesizes results. Workers are narrow and opinionated.

### Pattern 7: Evaluator-Optimizer for Quality Gates

The opponent/critique pattern (where one agent evaluates another's output) appears across platforms. Anthropic formalizes it as a workflow pattern. In practice: plan → review → refine → implement → review → fix loops.

---

## 8. SKILL.md Authoring Best Practices

### From All Three Platforms

1. **Keep each skill focused on one job.** Narrow and opinionated > broad and vague.
2. **Write descriptions with trigger keywords.** Agents match tasks to skills via description text. Front-load the key use case.
3. **Prefer instructions over scripts** unless deterministic behavior or external tooling is needed.
4. **Write imperative steps** with explicit inputs and outputs.
5. **Test prompts against skill descriptions** to confirm correct trigger behavior.
6. **Include concrete file paths, function names, and gotchas** — the skill should eliminate the need to re-research.
7. **Document boundaries** — what this skill covers vs. what adjacent skills cover.
8. **Cross-reference canonical docs** rather than duplicating them. Skills are guides, not replacements for full documentation.

### From Claude Specifically

- **Level 1 (metadata)**: Brief enough for the agent to choose correctly. ~100 tokens.
- **Level 2 (instructions)**: Under 5,000 tokens. Procedural knowledge, not reference material.
- **Level 3 (resources)**: Can be effectively unlimited. Code never enters context; only output does.
- **Date-stamp skills** so agents know freshness.
- **Include example usage** and edge cases in tool definitions.

### From Codex Specifically

- Instruction-only is the default for new skills.
- Descriptions should be concise with clear scope and boundaries.
- The initial skills list is capped — if many skills are installed, shorter descriptions are favored.
- `allow_implicit_invocation: false` when a skill should only be triggered explicitly.

---

## 9. Reference Links

| Resource | URL |
|----------|-----|
| OpenCode Docs | https://opencode.ai/docs |
| OpenCode Agents | https://opencode.ai/docs/agents/ |
| OpenCode Skills | https://opencode.ai/docs/skills/ |
| OpenCode Permissions | https://opencode.ai/docs/permissions/ |
| OpenCode Tools | https://opencode.ai/docs/tools/ |
| Codex Subagents | https://developers.openai.com/codex/subagents |
| Codex Subagent Concepts | https://developers.openai.com/codex/concepts/subagents |
| Codex Skills | https://developers.openai.com/codex/skills |
| Claude Agent Skills | https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview |
| Building Effective Agents | https://www.anthropic.com/engineering/building-effective-agents |
| Agent Skills Standard | https://agentskills.io |
| Agent Skills Spec | https://agentskills.io/specification |
| Claude Skills Cookbook | https://platform.claude.com/cookbook/skills-notebooks-01-skills-introduction |
| OpenAI Skills Repo | https://github.com/openai/skills |
| Anthropic Skills Repo | https://github.com/anthropics/skills |
| Reddit r/DeepSeek | https://www.reddit.com/r/DeepSeek/ |
| Reddit r/opencode | https://www.reddit.com/r/opencode/ |
| Reddit r/opencodeCLI | https://www.reddit.com/r/opencodeCLI/ |
